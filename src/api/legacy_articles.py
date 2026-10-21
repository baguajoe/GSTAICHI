"""
The articles from the old public Articles page (src/front/js/utils/articlesData.js, copied to
seed_data/public_articles.json), turned into member articles in the magazine style.

The old texts mix several kinds of markup: proper <p> paragraphs with hard-wrapped lines, plain text with one
paragraph per line, unclosed <P> tags, <p class="section-title"> headings, bold lines used as headings, and
wrapper tags from the old React page (<Fragment>, <div>, <td>). to_magazine_html() turns all of them into
paragraphs, headings, lists and quotes, then runs the same Auto-format as uploaded documents.
"""
import json
import os
import re

from .article_import import auto_format, paragraphs_from_lines, _tidy, _text_of, _esc
from .rich_text import clean_html

DATA_FILE = os.path.join(os.path.dirname(__file__), "seed_data", "public_articles.json")
RENAMED = {"Chapter 16 Three Levels Tai Chi Chuan Practice": "Three Levels of Tai Chi Chuan Practice"}

BLOCK_TAG = re.compile(r"(</?(?:p|h[1-6]|ol|ul|li|blockquote)\b[^>]*>|<br\s*/?>)", re.I)
NUMBERED_ITEM = re.compile(r"^(\d{1,2})\.\s+(.+)$")


def load_public_articles():
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


def _prepare(raw):
    text = raw.replace("\r\n", "\n")
    text = re.sub(r"</?(?:fragment|div|td|span)\b[^>]*>", "\n", text, flags=re.I)
    # Old section headings, whatever tag they were on
    text = re.sub(r'<(p|h[1-6])\s+class(?:Name)?="section-title"\s*>(.*?)</\1>', r"<h2>\2</h2>", text, flags=re.S | re.I)
    text = re.sub(r"<(p|h[1-6])\s+class(?:Name)?=\"[^\"]*\"\s*>", r"<\1>", text, flags=re.I)
    # Links to pages of the old site do not exist any more: keep the words
    text = re.sub(r'<a\s+href="(?!https?:|mailto:)[^"]*"[^>]*>(.*?)</a>', r"\1", text, flags=re.S | re.I)
    text = re.sub(r"</a>", "", text) if "<a " not in text else text
    return text


def _wrapped(text):
    """Is the text outside <p>...</p> hard-wrapped (a newline is just a space), or one paragraph per line?"""
    loose = re.sub(r"<p\b[^>]*>.*?</p>", "", text, flags=re.S | re.I)
    lines = [l.strip() for l in re.sub(r"<[^>]+>", "", loose).split("\n") if l.strip()]
    if not lines:
        return True
    return sum(len(l) <= 130 for l in lines) >= 0.8 * len(lines)


def _blocks(text):
    """[(tag, inner html, indented)] from the prepared text."""
    wrapped = _wrapped(text)
    blocks, buffer, open_tag, in_p = [], "", None, False

    def flush(joined=None):
        nonlocal buffer
        for segment in re.split(r"\n\s*\n", buffer):
            lines = [l.strip() for l in segment.split("\n") if l.strip()]
            if not lines:
                continue
            indented = segment.strip().startswith(("&nbsp;", "\u00a0"))
            for paragraph in paragraphs_from_lines(lines, wrapped=wrapped if joined is None else joined):
                blocks.append(("p", paragraph, indented))
        buffer = ""

    for token in BLOCK_TAG.split(text):
        tag = BLOCK_TAG.fullmatch(token)
        if not tag:
            buffer += token
            continue
        name = re.match(r"</?\s*([a-z0-9]+)", token, re.I).group(1).lower()
        closing = token.startswith("</")
        if name == "p":
            # Inside a closed <p>...</p> a newline is always just a space
            flush(joined=True if closing and in_p else None)
            in_p = not closing
        elif name == "br":
            flush()
        elif name in ("ol", "ul"):
            flush()
            blocks.append((token.lower(), "", False))
        elif closing and name == open_tag:
            inner = re.sub(r"\s+", " ", buffer).strip()
            if inner:
                blocks.append((name, inner, False))
            buffer, open_tag = "", None
        elif not closing:
            flush()
            open_tag = name
    flush()
    return blocks


def _numbered_runs(blocks):
    """A long run of numbered lines (1, 2, 3, ...) is a list, like the movements of a form: an ordered list,
    with the indented lines under a number as its sub-steps."""
    out, i = [], 0
    while i < len(blocks):
        start = NUMBERED_ITEM.match(_text_of(blocks[i][1])) if blocks[i][0] == "p" else None
        if not start or start.group(1) != "1":
            out.append(blocks[i])
            i += 1
            continue
        items, expected, j = [], 1, i
        while j < len(blocks) and blocks[j][0] == "p":
            number = NUMBERED_ITEM.match(_text_of(blocks[j][1]))
            if number and int(number.group(1)) == expected:
                items.append([number.group(2), []])
                expected += 1
            elif blocks[j][2] and items:
                items[-1][1].append(_text_of(blocks[j][1]))
            else:
                break
            j += 1
        if len(items) < 8:
            out.append(blocks[i])
            i += 1
            continue
        parts = []
        for title, steps in items:
            sub = "<ul>" + "".join(f"<li>{_esc(s)}</li>" for s in steps) + "</ul>" if steps else ""
            parts.append(f"<li>{_esc(title)}{sub}</li>")
        out.append(("html", "<ol>" + "".join(parts) + "</ol>", False))
        i = j
    return out


def to_magazine_html(raw):
    blocks = _numbered_runs(_blocks(_prepare(raw)))
    out = []
    for tag, inner, _indented in blocks:
        if tag == "html":
            out.append(inner)
        elif tag.startswith("<"):
            out.append(tag)
        else:
            inner = re.sub(r"(?:&nbsp;| )+", " ", inner).strip()
            tag = {"h1": "h2", "h4": "h3", "h5": "h3", "h6": "h3"}.get(tag, tag)
            if inner:
                out.append(f"<{tag}>{inner}</{tag}>")
    text = auto_format(_tidy("".join(out)))
    # Headings are plain words: the magazine style gives them their look. The numbering style of the first
    # numbered heading ("1." or "A.") is the top level; other numbered headings, and headings without a
    # number after the first top-level one, are subheadings.
    top = None

    def heading(match):
        nonlocal top
        tag, words = match.group(1), re.sub(r"^\*\s+", "", _text_of(match.group(2)))
        style = "digit" if re.match(r"^\d{1,2}[.)]\s", words) else "upper" if re.match(r"^[A-Z][.)]\s", words) else None
        if tag == "h2":
            if style and top is None:
                top = style
            if top and style != top:
                tag = "h3"
        return f"<{tag}>{_esc(words)}</{tag}>"
    text = re.sub(r"<(h[23])>(.*?)</\1>", heading, text, flags=re.S)
    return clean_html(text)
