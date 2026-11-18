"""
One-time conversion of Vincent Chu's Word articles (Nov 2026 batch) into src/api/seed_data/vincent_chu_articles_2026_11.json.
The JSON is committed; migration a7b8c9d0e1f2 adds the articles to the database on the next deploy.

Run from the repo root, in a Codespace with LibreOffice (old .doc files are turned into .docx first, so they keep
their italics and list numbers):

    pipenv run python scripts/convert_vincent_articles.py "archive (1)"

The Word files themselves are not committed (archive folders are in .gitignore).
"""
import glob
import json
import os
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from api.article_import import (import_document, title_from_filename, chapter_number, drop_leading_title,  # noqa: E402
                                _summary)
from api.rich_text import clean_html  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "api", "seed_data",
                   "vincent_chu_articles_2026_11.json")

# Chapter -> category, as agreed with the school. "Why Practice Tai Chi Chuan Slowly" has no chapter: None.
CATEGORIES = {4: "Training", 14: "Training", 15: "Training", None: "Training",
              7: "Philosophy", 8: "Philosophy", 9: "Philosophy", 10: "Philosophy", 13: "Philosophy", 28: "Philosophy"}
# Typos in the file names
TITLE_FIXES = {"The Three Emphases As am Internal Martial Art": "The Three Emphases as an Internal Martial Art",
               "Three Objectives in Tai Chi Chuan Practices": "Three Objectives in Tai Chi Chuan Practice"}
# Typos in the text: (wrong, right)
TEXT_FIXES = [(r"\bMarital Art", "Martial Art"), (r"\bmarital art", "martial art")]
# Section numbers that are wrong in the Word files: Chapter 4 calls its last section "5." after I. to IV.;
# Chapter 10 has two sections numbered III.
TEXT_FIXES_BY_CHAPTER = {
    4: [(r"<(p|h3)>5\. Conclusion</\1>", "<h2>V. Conclusion</h2>")],
    10: [(r"<h2>III\. Yin and Yang Transformation", "<h2>IV. Yin and Yang Transformation"),
         (r"<h2>IV\. Conclusion</h2>", "<h2>V. Conclusion</h2>")],
}
# Files whose name starts with a number that is not a chapter number
NOT_A_CHAPTER = ("28 Why Practice Tai Chi Chuan Slowly",)


def as_docx(path, workdir):
    if path.lower().endswith(".docx"):
        return path
    subprocess.run(["soffice", "--headless", "--convert-to", "docx", "--outdir", workdir, path],
                   check=True, capture_output=True, timeout=300)
    return os.path.join(workdir, os.path.splitext(os.path.basename(path))[0] + ".docx")


def main(folder):
    files = sorted(glob.glob(os.path.join(folder, "*.doc")) + glob.glob(os.path.join(folder, "*.docx")))
    if not files:
        sys.exit(f"No .doc or .docx files in {folder}")
    articles = []
    with tempfile.TemporaryDirectory() as workdir:
        for path in files:
            name = os.path.basename(path)
            chapter = None if name.startswith(NOT_A_CHAPTER) else chapter_number(name)
            with open(as_docx(path, workdir), "rb") as f:
                result = import_document(name.replace(".doc", ".docx") if name.endswith(".doc") else name,
                                         f.read(), lambda raw: None)
            title = title_from_filename(name)
            title = TITLE_FIXES.get(title, title)
            content = drop_leading_title(result["content"], title, result["title"])
            for wrong, right in TEXT_FIXES + TEXT_FIXES_BY_CHAPTER.get(chapter, []):
                content = re.sub(wrong, right, content)
            content = clean_html(content)
            articles.append({"source_file": name, "chapter": chapter, "title": title,
                             "category": CATEGORIES[chapter], "summary": _summary(content), "content": content})
            print(f"{chapter or '-':>3}  {CATEGORIES[chapter]:<10}  {title}")
    # Chapter order; the one without a chapter number last
    articles.sort(key=lambda a: (a["chapter"] is None, a["chapter"] or 0))
    for order, a in enumerate(articles, 1):
        a["order"] = order
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"author": "Vincent Chu",
                   "move_to_training": ["Three Levels of Tai Chi Chuan Practice",
                                        "Cultivation and Training in Chinese Martial Art"],
                   "new_category": "Training",
                   "articles": articles}, f, ensure_ascii=False, indent=1)
    print(f"Wrote {len(articles)} articles to {os.path.relpath(OUT)}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "archive")
