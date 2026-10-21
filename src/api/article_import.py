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
    return _flatten_tables(result.value)


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
        elif len(lines) > 1 and all(len(l) >= 55 for l in lines[:-1]):
            out.append(f"<p>{_esc(' '.join(lines))}</p>")
        else:
            out.extend(f"<p>{_esc(l)}</p>" for l in lines)
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
    # A short line that is all bold is a heading
    def bold_heading(match):
        words = _text_of(match.group(1))
        return f"<h2>{_esc(words)}</h2>" if words and short_line(words) else match.group(0)
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


def import_document(filename, data, save_photo):
    ext = os.path.splitext((filename or "").lower())[1]
    if ext == ".doc":
        raise DocumentError("This is an older Word file (.doc). In Word, choose File, Save As, and pick "
                            "\"Word Document (.docx)\", then upload that file.")
    if ext not in EXTENSIONS:
        raise DocumentError("Please choose a Word (.docx), PDF, text (.txt) or Markdown (.md) file.")
    if not data:
        raise DocumentError("This file is empty.")
    if len(data) > MAX_DOCUMENT_BYTES:
        raise DocumentError("This file is bigger than 25 MB. Please make the photos in it smaller, or split it in two.")

    photos = _Photos(save_photo)
    if ext == ".docx":
        raw = _docx_html(data, photos)
    elif ext == ".pdf":
        raw = _pdf_html(data, photos)
    elif ext == ".txt":
        raw = _text_html(_decode(data))
    else:
        raw = _markdown_html(_decode(data))

    title, body = _title_and_body(_tidy(raw), filename)
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
    if ext == ".pdf":
        notes.append("PDFs do not keep bold, italics or links. Please check the article and add them where needed.")
    return {"title": title, "summary": _summary(content), "content": content, "notes": notes}
