"""
"Upload an article" in the Teacher Studio: turns a Word, PDF, plain text or Markdown file into article HTML
for the Studio editor. Nothing is saved or published here; the teacher reviews the result in the editor.

import_document() returns {"title", "summary", "content", "notes"}. content is cleaned with
rich_text.clean_html, so only the magazine formats survive (fonts, colors, sizes and spacing are dropped).
Photos in Word and PDF files are made smaller and stored privately with save_photo(image bytes) -> path,
then placed where they were in the document. The uploaded file itself is never stored.
"""
import html
import io
import os
import re
from collections import Counter
from statistics import median

from .rich_text import clean_html

MAX_DOCUMENT_BYTES = 25 * 1024 * 1024
MAX_PDF_PAGES = 200
MAX_PHOTOS = 40
EXTENSIONS = {".docx", ".pdf", ".txt", ".md", ".markdown"}

# The same rules as the editor's Auto-format (src/front/js/component/tai-chi-company/autoFormat.js)
MAX_HEADING_LENGTH = 80
MAX_HEADING_WORDS = 12
ENDS_LIKE_A_SENTENCE = re.compile(r"[.,;:!]$")
NUMBERED = re.compile(r"^\d{1,2}[.)]\s+\S")
LETTERED = re.compile(r"^[A-Za-z][.)]\s+\S")
QUOTED = re.compile(r"^[\"“'‘][^\"“”]{8,}[\"”'’](?:\s*[—–-]+\s*[^\"“”]{1,60})?$")
# "ii. Step", "iv. Body position": sub-points like the lettered ones
ROMAN = re.compile(r"^(?:i{1,3}|iv|vi{0,3}|ix|xi{0,3})[.)]\s*[A-Za-z]", re.I)
# A bullet character; PDFs sometimes only give its glyph number, like "(cid:127)"
BULLET = re.compile(r"^(?:[•◦▪▫●○‣∙·\-–*]\s+|\(cid:\d+\)\s*)(?=\S)")

# Word paragraph styles that are not headings by name
DOCX_STYLE_MAP = """
p[style-name='Title'] => h1:fresh
p[style-name='Subtitle'] => p:fresh
p[style-name='Quote'] => blockquote:fresh
p[style-name='Intense Quote'] => blockquote:fresh
"""


class DocumentError(Exception):
    """A problem with the uploaded file, explained in plain English for the teacher."""


def short_line(text):
    return (len(text) <= MAX_HEADING_LENGTH and len(text.split()) <= MAX_HEADING_WORDS
            and not ENDS_LIKE_A_SENTENCE.search(text))


def classify_line(text):
    """Auto-format for one line, as in autoFormat.js: "heading", "subheading", "quote" or None."""
    text = (text or "").strip()
    if not text:
        return None
    if NUMBERED.match(text) and short_line(text):
        return "heading"
    if LETTERED.match(text) and short_line(text):
        return "subheading"
    if QUOTED.match(text) and len(text) <= 400:
        return "quote"
    return None


def auto_format(text):
    """The editor's Auto-format on HTML: short numbered paragraphs become headings, lettered ones subheadings,
    and paragraphs that are a whole quotation become quotes."""
    tags = {"heading": "h2", "subheading": "h3", "quote": "blockquote"}

    def change(match):
        kind = classify_line(_text_of(match.group(1)))
        return f"<{tags[kind]}>{match.group(1)}</{tags[kind]}>" if kind else match.group(0)
    return re.sub(r"<p>((?:(?!</?p>).)*?)</p>", change, text, flags=re.S)


def paragraphs_from_lines(lines, wrapped=None):
    """Lines of one block of text. Hard-wrapped lines (all but the last shorter than about 130 characters)
    are one paragraph; otherwise each line is its own paragraph. wrapped forces one or the other."""
    if wrapped is None:
        wrapped = len(lines) > 1 and all(len(l) <= 130 for l in lines[:-1])
    return [" ".join(lines)] if wrapped else lines


def _text_of(fragment):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", fragment))).strip()


def _esc(text):
    return html.escape(text, quote=False)


def _figure(path):
    return f'<figure class="tcc-photo" data-size="full"><img src="{html.escape(path, quote=True)}" alt=""></figure>'


class _Photos:
    """Hands photos to save_photo, at most MAX_PHOTOS, and counts the ones that could not be used."""

    def __init__(self, save_photo):
        self.save_photo = save_photo
        self.saved = 0
        self.skipped = 0

    def add(self, raw):
        if self.saved >= MAX_PHOTOS:
            self.skipped += 1
            return None
        path = self.save_photo(raw)
        if path:
            self.saved += 1
        else:
            self.skipped += 1
        return path


# ----- Word -----

def _docx_html(data, photos):
    import mammoth

    def image(img):
        with img.open() as f:
            path = photos.add(f.read())
        return {"src": path or "", "alt": img.alt_text or ""}

    try:
        result = mammoth.convert_to_html(io.BytesIO(data), style_map=DOCX_STYLE_MAP,
                                         convert_image=mammoth.images.img_element(image))
    except Exception as e:
        if photos.saved == 0 and "zip" in str(e).lower():
            raise DocumentError("This file could not be opened as a Word document. Please save it again as .docx and try once more.") from e
        raise
    text = _flatten_tables(result.value)
    try:
        return _relabel_word_lists(text, docx_number_labels(data))
    except Exception as e:  # the numbers are a nicety: never fail an upload over them
        print(f"Word list numbers skipped: {type(e).__name__}: {e}")
        return text


# ----- Word list numbers -----
# mammoth turns Word's automatic numbering ("I.", "II.", "A.", "a.") into <ol> lists, and a list of one item
# restarts at 1. So "II. Tai Chi Philosophy" would show as "1. Tai Chi Philosophy". docx_number_labels() works
# out the number Word shows in front of each numbered paragraph, so the real labels can be put back.

_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
_ROMAN = [(1000, "m"), (900, "cm"), (500, "d"), (400, "cd"), (100, "c"), (90, "xc"), (50, "l"), (40, "xl"),
          (10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")]


def _roman(n):
    out = ""
    for value, letters in _ROMAN:
        while n >= value:
            out, n = out + letters, n - value
    return out


def _format_number(n, fmt):
    if fmt in ("upperRoman", "lowerRoman"):
        r = _roman(max(n, 1))
        return r.upper() if fmt == "upperRoman" else r
    if fmt in ("upperLetter", "lowerLetter"):
        letter = chr(ord("a") + (max(n, 1) - 1) % 26) * ((max(n, 1) - 1) // 26 + 1)
        return letter.upper() if fmt == "upperLetter" else letter
    if fmt == "decimalZero":
        return f"{n:02d}"
    return str(n)


def docx_number_labels(data):
    """[(label, format, paragraph text)] for every numbered or bulleted paragraph, in document order.
    label is what Word shows, e.g. "II." or "a)"; format is Word's numFmt (upperRoman, decimal, bullet, ...)."""
    import zipfile
    import xml.etree.ElementTree as ET

    z = zipfile.ZipFile(io.BytesIO(data))
    names = set(z.namelist())
    if "word/numbering.xml" not in names:
        return []
    numbering = ET.fromstring(z.read("word/numbering.xml"))
    w = _W

    def levels_of(parent):
        found = {}
        for lvl in parent.findall(f"{w}lvl"):
            ilvl = int(lvl.get(f"{w}ilvl", "0"))
            start = lvl.find(f"{w}start")
            fmt = lvl.find(f"{w}numFmt")
            text = lvl.find(f"{w}lvlText")
            found[ilvl] = {"start": int(start.get(f"{w}val")) if start is not None else 1,
                           "fmt": fmt.get(f"{w}val") if fmt is not None else "decimal",
                           "text": text.get(f"{w}val") if text is not None else f"%{ilvl + 1}."}
        return found

    abstract = {a.get(f"{w}abstractNumId"): levels_of(a) for a in numbering.findall(f"{w}abstractNum")}
    nums = {}
    for num in numbering.findall(f"{w}num"):
        ref = num.find(f"{w}abstractNumId")
        aid = ref.get(f"{w}val") if ref is not None else None
        overrides = {}
        for o in num.findall(f"{w}lvlOverride"):
            ilvl = int(o.get(f"{w}ilvl", "0"))
            so = o.find(f"{w}startOverride")
            inner = levels_of(o)
            overrides[ilvl] = {"start": int(so.get(f"{w}val")) if so is not None else None, "lvl": inner.get(ilvl)}
        nums[num.get(f"{w}numId")] = {"abstract": aid, "overrides": overrides}

    # Paragraph styles can carry the numbering too
    style_num = {}
    if "word/styles.xml" in names:
        for style in ET.fromstring(z.read("word/styles.xml")).findall(f"{w}style"):
            numpr = style.find(f"{w}pPr/{w}numPr")
            if numpr is not None:
                nid, il = numpr.find(f"{w}numId"), numpr.find(f"{w}ilvl")
                style_num[style.get(f"{w}styleId")] = (nid.get(f"{w}val") if nid is not None else None,
                                                     int(il.get(f"{w}val")) if il is not None else 0)

    counters, started = {}, set()
    out = []
    body = ET.fromstring(z.read("word/document.xml")).find(f"{w}body")
    for p in body.iter(f"{w}p"):
        ppr = p.find(f"{w}pPr")
        num_id, ilvl = None, 0
        if ppr is not None:
            ps = ppr.find(f"{w}pStyle")
            if ps is not None and ps.get(f"{w}val") in style_num:
                num_id, ilvl = style_num[ps.get(f"{w}val")]
            numpr = ppr.find(f"{w}numPr")
            if numpr is not None:
                nid, il = numpr.find(f"{w}numId"), numpr.find(f"{w}ilvl")
                if nid is not None:
                    num_id = nid.get(f"{w}val")
                if il is not None:
                    ilvl = int(il.get(f"{w}val"))
        if not num_id or num_id == "0" or num_id not in nums:
            continue
        num = nums[num_id]
        levels = dict(abstract.get(num["abstract"], {}))
        for lv, o in num["overrides"].items():
            if o["lvl"]:
                levels[lv] = o["lvl"]
        if ilvl not in levels:
            continue
        # Word keeps counting across lists made from the same template, unless a list says to restart
        key = num["abstract"]
        count = counters.setdefault(key, {})
        override = num["overrides"].get(ilvl, {}).get("start")
        if override is not None and (num_id, ilvl) not in started:
            count[ilvl] = override
        else:
            count[ilvl] = count[ilvl] + 1 if ilvl in count else levels[ilvl]["start"]
        started.add((num_id, ilvl))
        for deeper in [l for l in count if l > ilvl]:
            del count[deeper]
        fmt = levels[ilvl]["fmt"]
        if fmt == "bullet":
            label = ""
        else:
            def fill(m):
                lv = int(m.group(1)) - 1
                lvl = levels.get(lv, {"fmt": "decimal", "start": 1})
                return _format_number(count.get(lv, lvl["start"]), lvl["fmt"])
            label = re.sub(r"%(\d)", fill, levels[ilvl]["text"]).strip()
        text = "".join(t.text or "" for t in p.iter(f"{w}t"))
        out.append((label, fmt, text))
    return out


def _norm_words(text):
    return re.sub(r"\s+", " ", text).strip().lower()


def _relabel_word_lists(text, labels):
    """Puts Word's own numbers back. A numbered list that is not simply 1, 2, 3 (Roman numerals, letters, or
    numbering that carries on from earlier in the document, or a "list" of one line) becomes paragraphs that start with the label, so
    "II." stays "II."; Auto-format then turns short ones into headings. Plain 1, 2, 3 lists and bullets stay lists."""
    labels = [l for l in labels if _text_of(_esc(l[2]))]
    position = 0

    def take(item_html):
        """The label of the numbered paragraph this list item came from, matched by its words."""
        nonlocal position
        words = _norm_words(_text_of(item_html))
        for i in range(position, min(position + 5, len(labels))):
            if _norm_words(labels[i][2]) == words:
                position = i + 1
                return labels[i]
        return None

    def one_list(match):
        tag, inner = match.group(1), match.group(2)
        items = re.findall(r"<li>(.*?)</li>", inner, re.S)
        if "<ol" in inner or "<ul" in inner or not items:
            return match.group(0)  # nested lists: leave as they are
        found = [take(i) for i in items]
        if tag == "ul" or any(f is None for f in found):
            return match.group(0)
        numbers = [f[0] for f in found]
        if len(items) > 1 and all(f[1] == "decimal" for f in found) \
                and numbers == [f"{n}." for n in range(1, len(items) + 1)]:
            return match.group(0)
        return "".join(f"<p>{label} {item.strip()}</p>" for (label, _, _), item in zip(found, items))
    return re.sub(r"<(ol|ul)>((?:(?!</?(?:ol|ul)>).)*?)</\1>", one_list, text, flags=re.S)


# ----- Outline headings -----
# Vincent's articles are laid out as "I. Introduction", "II. ...", with "A. ..." under them. Word files mark
# those in every possible way (heading styles, bold, plain text). outline_headings() makes them consistent:
# Roman numerals are sections (h2), capital letters subsections (h3). Documents numbered 1, 2, 3 at the top
# get h2 for those numbers only where the line was already a heading or bold, so numbered lists stay lists.

UPPER_ROMAN = re.compile(r"^(?=[IVX])(X{0,3})(IX|IV|V?I{0,3})\s*[.)]\s*(?=\S)")
CAPITAL = re.compile(r"^[A-Z]\s*[.)]\s+(?=\S)")
ARABIC = re.compile(r"^\d{1,2}\s*[.)]\s+(?=\S)")
SECTION_MAX_WORDS, SECTION_MAX_LENGTH = 20, 140  # "III. The Formation of the Tai Chi Yin and Yang Symbol and ..."
BLOCK = re.compile(r"<(p|h[1-4])>(.*?)</\1>", re.S)


def _fits(line, words, length):
    """A line short enough to be a heading. A trailing full stop is allowed ("I. Introduction.")."""
    t = line.rstrip(". ").strip()
    return bool(t) and len(t) <= length and len(t.split()) <= words and not re.search(r"[,;:!]$", t)


def _split_blank_lines(text):
    """A blank line inside a Word paragraph (two line breaks) starts a new paragraph."""
    def split(m):
        parts = [p.strip() for p in re.split(r"(?:<br\s*/?>\s*){2,}", m.group(1))]
        return "".join(f"<p>{p}</p>" for p in parts if _text_of(p))
    return re.sub(r"<p>((?:(?!</?p>).)*?(?:<br\s*/?>\s*){2,}(?:(?!</?p>).)*?)</p>", split, text, flags=re.S)


def outline_headings(text):
    text = _split_blank_lines(text)
    blocks = list(BLOCK.finditer(text))
    lines = [re.sub(r"\s+", " ", _text_of(m.group(2))).strip() for m in blocks]
    roman_top = any(UPPER_ROMAN.match(l) and re.match(r"^[IVX]{2,}", l) for l in lines)

    def kind(i):
        if not 0 <= i < len(lines):
            return None
        l = lines[i]
        if roman_top and UPPER_ROMAN.match(l):
            return "roman"
        if CAPITAL.match(l):
            return "capital"
        if ARABIC.match(l):
            return "arabic"
        return None

    def is_bold(i):
        tag, inner = blocks[i].group(1), blocks[i].group(2)
        return tag != "p" or bool(re.fullmatch(r"\s*(?:<(strong|b)>.*?</\1>\s*[?.:]?\s*)+", inner, re.S))

    def in_a_run(i, k):
        """Lines like "A. ...", "B. ..." straight after each other are a list of points, not headings."""
        return kind(i - 1) == k or kind(i + 1) == k

    has_capital_headings = any(kind(i) == "capital" and not in_a_run(i, "capital") for i in range(len(lines)))
    levels = []
    for i, line in enumerate(lines):
        k, level = kind(i), None
        sub = _fits(line, MAX_HEADING_WORDS, MAX_HEADING_LENGTH) and not line.endswith(".")
        if k == "roman" and _fits(line, SECTION_MAX_WORDS, SECTION_MAX_LENGTH):
            level = "h2"
        elif k == "capital" and sub and not in_a_run(i, k):
            level = "h3"
        elif k == "arabic" and not roman_top and is_bold(i) and _fits(line, SECTION_MAX_WORDS, SECTION_MAX_LENGTH):
            level = "h2"
        elif k == "arabic" and roman_top and not has_capital_headings and sub and not in_a_run(i, k):
            level = "h3"
        levels.append(level)

    out, last = [], 0
    for m, line, level in zip(blocks, lines, levels):
        out.append(text[last:m.start()])
        last = m.end()
        if level is None:
            out.append(m.group(0))
            continue
        label = re.match(r"^(\S+?)\s*([.)])\s*", line)
        clean = f"{label.group(1)}{label.group(2)} {line[label.end():]}" if label else line
        out.append(f"<{level}>{_esc(clean.rstrip('. '))}</{level}>")
    out.append(text[last:])
    return "".join(out)


def title_from_filename(filename):
    """ "Chapter 7 Tai Chi and Tai Chi Chuan.doc" -> "Tai Chi and Tai Chi Chuan";
    "28 Why Practice Tai Chi Chuan Slowly.docx" -> "Why Practice Tai Chi Chuan Slowly"."""
    name = os.path.splitext(os.path.basename(filename or ""))[0]
    name = re.sub(r"\s*\(\d+\)\s*$", "", name)  # "Name (1)": a second download of the same file
    name = re.sub(r"[_]+", " ", name)
    name = re.sub(r"^\s*(?:chapter|ch\.?)\s*\d+\s*[.:\-–]?\s*|^\s*\d{1,3}\s*[.:\-–]?\s+", "", name, flags=re.I)
    name = re.sub(r"\s+", " ", name).strip()
    return (name[:1].upper() + name[1:])[:200]


def chapter_number(filename):
    m = re.match(r"^\s*(?:chapter|ch\.?)?\s*(\d{1,3})\b", os.path.basename(filename or ""), re.I)
    return int(m.group(1)) if m else None


def drop_leading_title(content, *titles):
    """Removes paragraphs or headings at the start that only repeat the title (or are empty)."""
    wanted = {_norm_words(re.sub(r"^\s*(?:chapter\s*)?\d+\s*[.:]?\s*", "", t, flags=re.I)) for t in titles if t}
    while True:
        m = re.match(r"\s*<(p|h[1-6])>(.*?)</\1>", content, re.S)
        if not m:
            return content
        words = _norm_words(re.sub(r"^\s*(?:chapter\s*)?\d+\s*[.:]?\s*", "", _text_of(m.group(2)), flags=re.I))
        if words and words not in wanted:
            return content
        content = content[m.end():]


def _flatten_tables(text):
    """Tables do not fit the magazine layout: each row becomes a paragraph, cells separated by " · "."""
    def row(match):
        cells = [_text_of(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", match.group(0), re.S)]
        cells = [c for c in cells if c]
        return f"<p>{_esc(' · '.join(cells))}</p>" if cells else ""
    def table(match):
        return re.sub(r"<tr[^>]*>.*?</tr>", row, match.group(0), flags=re.S)
    text = re.sub(r"<table[^>]*>.*?</table>", table, text, flags=re.S)
    return re.sub(r"</?(?:table|thead|tbody|tfoot)[^>]*>", "", text)


# ----- PDF -----

def _is_bold(fontname):
    return bool(re.search(r"bold|black|heavy|semibold|demi|,b$", fontname or "", re.I))


def _pdf_lines_and_photos(pdf, photos):
    """Every text line and photo in reading order: [{page, top, ...}]"""
    items, page_count = [], len(pdf.pages)
    for number, page in enumerate(pdf.pages):
        for line in page.extract_text_lines(return_chars=True, strip=True):
            chars = [c for c in line["chars"] if c["text"].strip()]
            text = re.sub(r"\s+", " ", line["text"]).strip()
            if not chars or not text:
                continue
            items.append({
                "kind": "line", "page": number, "top": line["top"], "bottom": line["bottom"],
                "x0": line["x0"], "x1": line["x1"], "text": text,
                "size": round(median(c["size"] for c in chars), 1),
                "bold": sum(_is_bold(c.get("fontname")) for c in chars) >= 0.8 * len(chars),
                "page_height": page.height, "page_width": page.width,
            })
        for image in page.images:
            box = (max(0, image["x0"]), max(0, image["top"]), min(page.width, image["x1"]), min(page.height, image["bottom"]))
            if box[2] - box[0] < 60 or box[3] - box[1] < 60:
                continue  # icons, bullets and lines
            try:
                picture = page.crop(box).to_image(resolution=150).original
                buffer = io.BytesIO()
                picture.save(buffer, format="PNG")
                path = photos.add(buffer.getvalue())
            except Exception as e:
                print(f"PDF picture skipped: {e}")
                photos.skipped += 1
                path = None
            if path:
                items.append({"kind": "photo", "page": number, "top": box[1], "path": path})
    items.sort(key=lambda i: (i["page"], i["top"]))
    return items, page_count


def _drop_headers_and_footers(lines, page_count):
    """Lines repeated at the top or bottom of most pages (running titles, page numbers)."""
    def in_margin(line):
        return line["top"] < line["page_height"] * 0.08 or line["bottom"] > line["page_height"] * 0.92
    def key(line):
        return re.sub(r"\d+", "#", line["text"].lower())
    pages_per_key = Counter()
    for k, page in {(key(l), l["page"]) for l in lines if in_margin(l)}:
        pages_per_key[k] += 1
    repeated = {k for k, n in pages_per_key.items() if n >= max(2, page_count * 0.5)}
    page_number = re.compile(r"^(?:page\s*)?#(?:\s*(?:of|/)\s*#)?$|^[-–]\s*#\s*[-–]$", re.I)
    return [l for l in lines if not (in_margin(l) and (key(l) in repeated or page_number.match(key(l))))]


def _pdf_html(data, photos):
    import pdfplumber

    try:
        pdf = pdfplumber.open(io.BytesIO(data))
    except Exception as e:
        raise DocumentError("This file could not be opened as a PDF. It may be damaged or protected with a password.") from e
    with pdf:
        if len(pdf.pages) > MAX_PDF_PAGES:
            raise DocumentError(f"This PDF has more than {MAX_PDF_PAGES} pages. Please upload a shorter document.")
        items, page_count = _pdf_lines_and_photos(pdf, photos)

    lines = _drop_headers_and_footers([i for i in items if i["kind"] == "line"], page_count)
    if sum(len(l["text"]) for l in lines) < 40:
        raise DocumentError("No words could be read from this PDF. It is probably a scan (pictures of the pages). "
                            "Please upload the Word version instead, or type the article in.")
    kept = {id(l) for l in lines}
    items = [i for i in items if i["kind"] == "photo" or id(i) in kept]

    sizes = Counter()
    for l in lines:
        sizes[l["size"]] += len(l["text"])
    body_size = sizes.most_common(1)[0][0]
    body_bold = sum(len(l["text"]) for l in lines if l["bold"]) > 0.5 * sum(sizes.values())
    gaps = [b["top"] - a["bottom"] for a, b in zip(lines, lines[1:]) if a["page"] == b["page"] and b["top"] > a["bottom"]]
    line_gap = median(gaps) if gaps else 3
    right_edge = {}
    for l in lines:
        right_edge[l["page"]] = max(right_edge.get(l["page"], 0), l["x1"])

    def heading_level(line):
        text = line["text"]
        if not short_line(text) and not (len(text) <= MAX_HEADING_LENGTH and NUMBERED.match(text)):
            return None
        if line["size"] >= body_size * 1.12 or NUMBERED.match(text):
            return "h2"
        if LETTERED.match(text) or (line["bold"] and not body_bold):
            return "h3"
        return None

    # Group lines into blocks: headings, list items and paragraphs
    blocks, current, previous = [], None, None
    for item in items:
        if item["kind"] == "photo":
            blocks.append({"kind": "photo", "path": item["path"]})
            current, previous = None, None
            continue
        line, text = item, item["text"]
        level = heading_level(line)
        bullet = BULLET.match(text)
        new_block = (current is None or level is not None or bullet or current["kind"] not in ("p", "li"))
        if not new_block and previous is not None:
            if line["page"] != previous["page"]:
                new_block = bool(re.search(r"[.!?:\"”']$", previous["text"]))
            else:
                gap = line["top"] - previous["bottom"]
                ended = re.search(r"[.!?:\"”']$", previous["text"])
                short_previous = previous["x1"] < right_edge[previous["page"]] - 0.15 * (right_edge[previous["page"]] - previous["x0"])
                new_block = gap > line_gap * 1.6 + 2 or (ended and short_previous)
        if new_block:
            if level:
                current = {"kind": level, "text": text, "lines": 1, "gap_before": True}
            elif bullet:
                current = {"kind": "li", "text": text[bullet.end():], "lines": 1}
            else:
                gap_before = previous is None or line["page"] != previous["page"] or line["top"] - previous["bottom"] > line_gap * 1.6 + 2
                current = {"kind": "p", "text": text, "lines": 1, "gap_before": gap_before}
            blocks.append(current)
        else:
            joined = current["text"]
            if joined.endswith("-") and text[:1].islower():
                current["text"] = joined[:-1] + text
            else:
                current["text"] = f"{joined} {text}"
            current["lines"] += 1
        if level:
            current = {"kind": "closed"}  # a heading is always one line
        previous = line

    # A short line standing on its own (space above and below) is a subheading
    for i, block in enumerate(blocks):
        if block["kind"] == "p" and block["lines"] == 1 and block.get("gap_before") and len(block["text"].split()) <= 8 \
                and short_line(block["text"]) and block["text"][:1].isupper():
            following = blocks[i + 1] if i + 1 < len(blocks) else None
            if following is None or following.get("gap_before") or following["kind"] != "p":
                block["kind"] = "h3"
    # Documents with only one level of headings: make them main headings
    if not any(b["kind"] == "h2" for b in blocks):
        for block in blocks:
            if block["kind"] == "h3":
                block["kind"] = "h2"

    out, in_list = [], False
    for block in blocks:
        kind = block["kind"]
        if kind == "closed":
            continue
        if kind == "li" and not in_list:
            out.append("<ul>")
            in_list = True
        elif kind != "li" and in_list:
            out.append("</ul>")
            in_list = False
        if kind == "photo":
            out.append(_figure(block["path"]))
        else:
            out.append(f"<{kind}>{_esc(block['text'])}</{kind}>")
    if in_list:
        out.append("</ul>")
    return "".join(out)


# ----- Plain text and Markdown -----

def _decode(data):
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("latin-1")


def _text_html(text):
    """Blank lines separate paragraphs. A block of hard-wrapped lines becomes one paragraph;
    a block of short lines keeps each line; lines starting with a bullet become a list."""
    out = []
    for block in re.split(r"\n\s*\n", text.replace("\r\n", "\n").replace("\r", "\n")):
        lines = [l.strip() for l in block.split("\n") if l.strip()]
        if not lines:
            continue
        if not out and len(lines) == 1 and short_line(lines[0]) and not NUMBERED.match(lines[0]):
            out.append(f"<h1>{_esc(lines[0])}</h1>")  # a first line on its own is the title
        elif all(BULLET.match(l) for l in lines):
            out.append("<ul>" + "".join(f"<li>{_esc(BULLET.sub('', l))}</li>" for l in lines) + "</ul>")
        else:
            out.extend(f"<p>{_esc(p)}</p>" for p in paragraphs_from_lines(lines))
    return "".join(out)


def _markdown_html(text):
    import markdown
    return markdown.markdown(text, extensions=["sane_lists"], output_format="html")


# ----- Shared tidying -----

def _lift_photos(text):
    """Photos must be their own block: split paragraphs and headings around them."""
    text = re.sub(r"<a\b[^>]*>\s*(<img\b[^>]*>)\s*</a>", r"\1", text)

    def split(match):
        tag, inner = match.group(1), match.group(2)
        if "<img" not in inner:
            return match.group(0)
        out = []
        for part in re.split(r"(<img\b[^>]*>)", inner):
            if part.startswith("<img"):
                src = re.search(r'\ssrc="([^"]+)"', part)
                if src:
                    out.append(_figure(html.unescape(src.group(1))))
            elif _text_of(part):
                out.append(f"<{tag}>{part.strip()}</{tag}>")
        return "".join(out)
    return re.sub(r"<(p|h[1-6])>(.*?)</\1>", split, text, flags=re.S)


def _tidy(text):
    text = _lift_photos(text)
    text = re.sub(r'<a\s+href="#[^"]*"[^>]*>(.*?)</a>', r"\1", text, flags=re.S)  # links inside the document
    text = re.sub(r"<a\s+id=\"[^\"]*\"\s*>\s*</a>", "", text)  # Word bookmarks
    # A short line that is all bold is a heading; "a. ..." or "ii. ..." a subheading
    def bold_heading(match):
        words = _text_of(match.group(1))
        if not words or not short_line(words):
            return match.group(0)
        tag = "h3" if LETTERED.match(words) or ROMAN.match(words) else "h2"
        return f"<{tag}>{_esc(words)}</{tag}>"
    text = re.sub(r"<p>\s*<(?:strong|b)>((?:(?!</?p>).)*?)</(?:strong|b)>\s*</p>", bold_heading, text, flags=re.S)
    text = re.sub(r"[ \t ]{2,}", " ", text)
    text = re.sub(r"<(p|h[1-6]|li|blockquote)>\s+", r"<\1>", text)
    text = re.sub(r"\s+</(p|h[1-6]|li|blockquote)>", r"</\1>", text)
    return text


def _title_and_body(text, filename):
    """The first heading becomes the title when the document starts with one; otherwise the file name."""
    first = re.match(r"\s*<(h[1-3])>(.*?)</\1>", text, re.S)
    if first and _text_of(first.group(2)):
        return _text_of(first.group(2))[:200], text[first.end():]
    name = os.path.splitext(os.path.basename(filename or ""))[0]
    name = re.sub(r"[_]+|(?<=\w)-(?=\w)", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return (name[:1].upper() + name[1:])[:200] if name else "", text


def _summary(text):
    """The first real paragraph, cut to about two sentences."""
    for paragraph in re.findall(r"<p>(.*?)</p>", text, re.S):
        words = _text_of(paragraph)
        if len(words) < 40:
            continue
        sentences = re.findall(r"[^.!?]+[.!?]+[\"”']?", words)
        summary = " ".join(s.strip() for s in sentences[:2]) if sentences else words
        if len(summary) > 320:
            summary = summary[:317].rsplit(" ", 1)[0] + "…"
        return summary
    return ""


def _doc_html(data):
    """An old Word file (.doc): words and paragraphs only (see word97.py)."""
    from .word97 import paragraphs, DocReadError
    try:
        found = paragraphs(data)
    except DocReadError as e:
        raise DocumentError(str(e)) from e
    return "".join("<p>" + "<br>".join(_esc(l) for l in p.split("\n")) + "</p>" for p in found)


def import_document(filename, data, save_photo, allow_doc=False):
    """allow_doc: also read old .doc files (text and paragraphs only). The admin's Bulk import uses it."""
    ext = os.path.splitext((filename or "").lower())[1]
    if ext == ".doc" and not allow_doc:
        raise DocumentError("This is an older Word file (.doc). In Word, choose File, Save As, and pick "
                            "\"Word Document (.docx)\", then upload that file.")
    if ext not in EXTENSIONS and ext != ".doc":
        raise DocumentError("Please choose a Word (.docx), PDF, text (.txt) or Markdown (.md) file.")
    if not data:
        raise DocumentError("This file is empty.")
    if len(data) > MAX_DOCUMENT_BYTES:
        raise DocumentError("This file is bigger than 25 MB. Please make the photos in it smaller, or split it in two.")

    photos = _Photos(save_photo)
    if ext == ".docx":
        raw = _docx_html(data, photos)
    elif ext == ".doc":
        raw = _doc_html(data)
    elif ext == ".pdf":
        raw = _pdf_html(data, photos)
    elif ext == ".txt":
        raw = _text_html(_decode(data))
    else:
        raw = _markdown_html(_decode(data))

    tidy = _tidy(raw.replace("\t", " "))
    if ext in (".docx", ".doc"):
        tidy = outline_headings(tidy)
    title, body = _title_and_body(tidy, filename)
    content = clean_html(body)
    if not _text_of(content) and "<figure" not in content:
        raise DocumentError("No text was found in this file.")

    notes = []
    if photos.saved:
        notes.append(f"{photos.saved} photo{'s' if photos.saved != 1 else ''} added where "
                     + ("they were" if photos.saved != 1 else "it was") + " in the document.")
    if photos.skipped:
        notes.append(f"{photos.skipped} picture{'s' if photos.skipped != 1 else ''} could not be used"
                     + (f" (at most {MAX_PHOTOS} per article)" if photos.saved >= MAX_PHOTOS else "")
                     + ". You can add photos with the Photo button.")
    if ext == ".doc":
        notes.append("Old .doc files keep only the words and paragraphs, not italics, bold or Word's list numbers.")
    if ext == ".pdf":
        notes.append("PDFs do not keep bold, italics or links. Please check the article and add them where needed.")
    return {"title": title, "summary": _summary(content), "content": content, "notes": notes}
