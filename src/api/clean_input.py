"""Cleaning what members type into forms (questions, names): plain text only."""
import html
import re
import nh3

CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def clean_text(value, keep_newlines=True):
    """Plain text only: drops HTML tags (and anything inside <script>/<style>), control characters and extra
    blank lines. Text is always shown as text in the app and sent as plain-text email, never as HTML."""
    text = str(value or "")
    text = nh3.clean(text, tags=set(), clean_content_tags={"script", "style"}, attributes={})
    text = html.unescape(text)
    text = text.replace("<", "").replace(">", "") if re.search(r"<\s*/?\s*[a-zA-Z!]", text) else text
    text = CONTROL_CHARS.sub("", text.replace("\r\n", "\n").replace("\r", "\n"))
    if not keep_newlines:
        return " ".join(text.split())
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    return re.sub(r"\n{3,}", "\n\n", text).strip()
