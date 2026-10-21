"""
Rich text for member articles and video "About This Form" descriptions.

The Studio editor (Quill) sends HTML. It is cleaned with nh3 before it is saved and again before it is shown,
so only these survive: paragraphs, h2/h3 headings, bold, italic, links, lists, quotes, dividers and the
three special blocks below. Scripts, styles, event handlers and every other tag or attribute are removed.

  <figure class="tcc-photo" data-size="full|medium|small-left|small-right"><img src alt><figcaption>…</figcaption></figure>
  <figure class="tcc-gallery"><img src alt><img src alt>…<figcaption>…</figcaption></figure>
  <figure class="tcc-video-block" data-video="<video slug>"><figcaption>…</figcaption></figure>

Pictures must be ones uploaded through the Studio, and are stored as paths, never as full addresses:
  article-private/<name>  photos inside articles and descriptions. The media Worker serves them only with a
                          signed link for that one picture, made here when the page is shown.
  article-images/<name>   cover pictures and pictures in older articles (public).

Older content is plain text (a blank line between paragraphs, a line like ![caption](address) for a
picture). It is converted to HTML when it is shown or opened in the editor, and saved as HTML after that.
"""
import html
import os
import re
from urllib.parse import urlparse

import nh3

from .media_tokens import sign_media_token

PRIVATE_IMAGE = re.compile(r"^article-private/[a-f0-9]{24}\.(?:jpg|png|webp|gif)$")
PUBLIC_IMAGE = re.compile(r"^article-images/[a-z0-9]+\.(?:jpg|png|webp|gif)$")
VIDEO_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,119}$")
PHOTO_SIZES = {"full", "medium", "small-left", "small-right"}
ARTICLE_BLOCKS = {"tcc-photo", "tcc-gallery", "tcc-video-block"}
DESCRIPTION_BLOCKS = {"tcc-photo"}
IMAGE_LINK_SECONDS = 6 * 60 * 60

TAGS = {"p", "br", "h2", "h3", "strong", "em", "a", "ul", "ol", "li", "blockquote", "hr", "figure", "figcaption", "img"}
ATTRIBUTES = {"a": {"href"}, "img": {"src", "alt"}, "figure": {"class", "data-size", "data-video"}}
RENAMES = [(r"h1", "h2"), (r"h[4-6]", "h3"), (r"b", "strong"), (r"i", "em")]
LEGACY_IMAGE_LINE = re.compile(r"^!\[(.*?)\]\((https?://[^\s)]+)\)$")
LOOKS_LIKE_HTML = re.compile(r"^\s*<(?:p|h[1-6]|ul|ol|blockquote|figure|hr|div|br|strong|em|b|i|a)\b", re.I)


def image_path(src):
    """The stored path for a picture address (signed or not), or None if it is not one of ours."""
    path = urlparse(html.unescape(src or "").strip()).path.lstrip("/")
    return path if PRIVATE_IMAGE.match(path) or PUBLIC_IMAGE.match(path) else None


def image_url(path, scope):
    """Address to show a stored picture: private ones get a signed link that opens only that picture."""
    base = os.getenv("MEDIA_BASE_URL", "").rstrip("/")
    if not base or not path:
        return None
    if PRIVATE_IMAGE.match(path):
        return f"{base}/{path}?t={sign_media_token(path, scope, IMAGE_LINK_SECONDS)}"
    return f"{base}/{path}"


def _filter(blocks):
    def attribute_filter(tag, attribute, value):
        if tag == "img" and attribute == "src":
            return image_path(value)
        if tag == "figure":
            if attribute == "class":
                found = [c for c in value.split() if c in blocks]
                return found[0] if found else None
            if attribute == "data-size":
                return value if value in PHOTO_SIZES else None
            if attribute == "data-video":
                return value if VIDEO_SLUG.match(value) else None
        return value
    return attribute_filter


def _drop_broken_blocks(text):
    text = re.sub(r"<img(?![^>]*\ssrc=)[^>]*>", "", text)  # pictures that were not ours
    text = re.sub(r"<p>\s*(?:<br>\s*)*</p>", "", text)  # empty lines
    # a figure without a known kind is a photo; then drop photo and gallery blocks without a picture and
    # video blocks without a video
    text = re.sub(r"<figure(?![^>]*\sclass=)", '<figure class="tcc-photo"', text)
    text = re.sub(r'<figure class="tcc-(?:photo|gallery)"[^>]*>\s*(?:<figcaption>.*?</figcaption>)?\s*</figure>', "", text, flags=re.S)
    text = re.sub(r'<figure(?![^>]*data-video=)[^>]*class="tcc-video-block"[^>]*>.*?</figure>', "", text, flags=re.S)
    return text.strip()


def clean_html(raw, blocks=ARTICLE_BLOCKS):
    """Safe HTML to store. blocks: which special blocks are allowed (descriptions only have photos)."""
    text = (raw or "").replace("&nbsp;", " ").replace(" ", " ")
    for old, new in RENAMES:
        text = re.sub(rf"<(/?){old}(?=[\s>/])", rf"<\1{new}", text, flags=re.I)
    text = nh3.clean(text, tags=TAGS, attributes=ATTRIBUTES, attribute_filter=_filter(blocks),
                     url_schemes={"http", "https", "mailto"}, link_rel="noopener noreferrer nofollow",
                     strip_comments=True)
    return _drop_broken_blocks(text)


def legacy_to_html(text):
    """Older plain-text content: each line its own paragraph, ![caption](address) lines become photos."""
    out = []
    for line in (text or "").splitlines():
        line = line.strip()
        if not line:
            continue
        picture = LEGACY_IMAGE_LINE.match(line)
        if picture:
            caption = html.escape(picture.group(1))
            src = html.escape(picture.group(2), quote=True)
            out.append(f'<figure class="tcc-photo" data-size="full"><img src="{src}" alt="{caption}">'
                       + (f"<figcaption>{caption}</figcaption>" if caption else "") + "</figure>")
        else:
            out.append(f"<p>{html.escape(line, quote=False)}</p>")
    return "".join(out)


def to_html(content, blocks=ARTICLE_BLOCKS):
    content = content or ""
    return clean_html(content if LOOKS_LIKE_HTML.match(content) else legacy_to_html(content), blocks)


def plain_text(content):
    """Words only (reading time, search)."""
    words = nh3.clean(to_html(content).replace("<", " <"), tags=set())
    return re.sub(r"\s+", " ", html.unescape(words)).strip()


def _sign_images(text, scope):
    def sign(match):
        tag = match.group(0)
        src = re.search(r'\ssrc="([^"]*)"', tag)
        url = image_url(html.unescape(src.group(1)), scope) if src else None
        return tag.replace(src.group(0), f' src="{html.escape(url, quote=True)}"', 1) if url else ""
    text = re.sub(r"<img\s[^>]*>", sign, text)
    return _drop_broken_blocks(text)


def editor_html(content, scope="studio", blocks=ARTICLE_BLOCKS):
    """For the Studio editor: clean HTML with pictures that can be displayed."""
    return _sign_images(to_html(content, blocks), scope)


def reader_html(content, scope, blocks=ARTICLE_BLOCKS):
    """For members: like the editor, plus numbered headings ("1. Softness…", "a. Yielding…") get a styled number."""
    text = _sign_images(to_html(content, blocks), scope)
    text = re.sub(r"<h2>(\d{1,2})[.)]\s+", r'<h2><span class="tcc-num">\1</span>', text)
    text = re.sub(r"<h3>([A-Za-z])[.)]\s+", r'<h3><span class="tcc-num">\1</span>', text)
    return text


def video_slugs(content):
    return list(dict.fromkeys(re.findall(r'data-video="([a-z0-9-]+)"', to_html(content))))
