"""Word article conversion, the November 2026 batch of Vincent's articles, and the admin's Bulk import.
Run from the repo root with:  pipenv run python -m unittest discover -s tests -t .
Throwaway SQLite; photo storage is never reached. The fixtures are small made-up documents, not real articles."""
import io
import json
import os
import re
import sys
import tempfile
import unittest
from datetime import datetime

_workdir = tempfile.mkdtemp(prefix="tcc-article-tests-")
os.environ.update(
    DATABASE_URL=f"sqlite:///{_workdir}/test.db", FLASK_APP_KEY="test-key", JWT_SECRET_KEY="test-jwt-key",
    BACKEND_URL="https://api.test", FRONTEND_URL="https://site.test", GMAIL="", GMAIL_PASSWORD="",
    ENV="test", FLASK_DEBUG="0", EMAIL_SENDER="off",
)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from app import app  # noqa: E402
from api.extensions import limiter  # noqa: E402
from api.models import db, User, Article, SiteSettings  # noqa: E402
from api import admin as admin_module  # noqa: E402
from api.article_import import (import_document, title_from_filename, chapter_number, outline_headings,  # noqa: E402
                                drop_leading_title, docx_number_labels, _relabel_word_lists, DocumentError)
from api.article_batches import load_batch, apply_batch, import_word_files  # noqa: E402
from api.word97 import paragraphs, DocReadError  # noqa: E402

assert app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite"), "tests must never run on a real database"

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


def fixture(name):
    with open(os.path.join(FIXTURES, name), "rb") as f:
        return f.read()


def no_photos(raw):
    return None


class Titles(unittest.TestCase):
    def test_titles_from_vincents_file_names(self):
        cases = {
            "Chapter 7 Tai Chi and Tai Chi Chuan.doc": "Tai Chi and Tai Chi Chuan",
            "Chapter 10 Tai Chi Yin Yang Symbol and Tai Chi Chuan (1).doc": "Tai Chi Yin Yang Symbol and Tai Chi Chuan",
            "Chapter 9 Tai Chi Symbol and Tai Chi Yin Yang Symbol .doc": "Tai Chi Symbol and Tai Chi Yin Yang Symbol",
            "Chapter 28. Why Tai Chi Chuan is an Internal Chinese Martial Art.docx":
                "Why Tai Chi Chuan is an Internal Chinese Martial Art",
            "28 Why Practice Tai Chi Chuan Slowly.docx": "Why Practice Tai Chi Chuan Slowly",
            "Solo Form Notes.docx": "Solo Form Notes",
        }
        for name, title in cases.items():
            self.assertEqual(title_from_filename(name), title, name)

    def test_chapter_numbers(self):
        self.assertEqual(chapter_number("Chapter 13 Interpreting.doc"), 13)
        self.assertEqual(chapter_number("Chapter 28. Why.docx"), 28)
        self.assertIsNone(chapter_number("Solo Form.docx"))

    def test_leading_title_lines_are_dropped(self):
        html = "<p></p><h2>Chapter 4</h2><p><strong>Chinese Martial Arts Curriculum</strong></p><h2>I. Introduction</h2>"
        self.assertEqual(drop_leading_title(html, "Chinese Martial Arts Curriculum"), "<h2>I. Introduction</h2>")


class WordConversion(unittest.TestCase):
    def test_docx_keeps_roman_numbers_italics_and_chinese(self):
        data = fixture("sample_article.docx")
        self.assertEqual([l[0] for l in docx_number_labels(data)], ["I.", "II.", "III."])
        result = import_document("Chapter 3 Sample Practice Notes.docx", data, no_photos)
        c = result["content"]
        self.assertIn("<h2>I. Introduction</h2>", c)
        self.assertIn("<h2>II. Standing Practice</h2>", c)
        self.assertIn("<h3>A. Rooting</h3>", c)
        self.assertIn("<h2>III. Conclusion</h2>", c)
        self.assertIn("<em>italic words</em>", c)
        self.assertIn("太極拳", c)
        self.assertNotIn("<ol", c)
        self.assertNotIn("style=", c)

    def test_doc_needs_permission_and_keeps_words(self):
        data = fixture("sample_article.doc")
        with self.assertRaises(DocumentError):
            import_document("Sample.doc", data, no_photos)  # the Studio upload still asks for .docx
        found = paragraphs(data)
        self.assertIn("Breathe naturally. Chinese: 太極拳.", found)
        result = import_document("Sample.doc", data, no_photos, allow_doc=True)
        self.assertIn("<h3>A. Rooting</h3>", result["content"])
        self.assertTrue(result["notes"])

    def test_doc_reader_rejects_other_files(self):
        with self.assertRaises(DocReadError):
            paragraphs(b"not a word file at all" * 40)
        with self.assertRaises(DocReadError):
            paragraphs(fixture("sample_article.docx"))

    def test_one_line_word_list_gets_its_real_number(self):
        labels = [("II.", "upperRoman", "Tai Chi Philosophy"), ("1.", "decimal", "Soft"), ("2.", "decimal", "Slow")]
        html = "<ol><li>Tai Chi Philosophy</li></ol><p>x</p><ol><li>Soft</li><li>Slow</li></ol>"
        self.assertEqual(_relabel_word_lists(html, labels),
                         "<p>II. Tai Chi Philosophy</p><p>x</p><ol><li>Soft</li><li>Slow</li></ol>")

    def test_outline(self):
        html = ("<p>I. Introduction.</p><p>Text.</p>"
                "<p><strong>II. A section heading that is quite a bit longer than twelve words but still a heading</strong></p>"
                "<p>A. Rooting</p><p>Text.</p>"
                # a run of lettered lines is a list of points, not headings
                "<p>A. It is easier to relax</p><p>B. It is easier to breathe</p>"
                "<p>1. A numbered line under a Roman-numbered section</p>")
        out = outline_headings(html)
        self.assertIn("<h2>I. Introduction</h2>", out)
        self.assertIn("<h2>II. A section heading", out)
        self.assertIn("<h3>A. Rooting</h3>", out)
        self.assertIn("<p>A. It is easier to relax</p><p>B. It is easier to breathe</p>", out)
        self.assertIn("<p>1. A numbered line", out)

    def test_numbered_top_level_only_when_bold(self):
        out = outline_headings("<p><strong>1. Introduction</strong></p><p>Text.</p><p>2. To obtain relaxation</p>")
        self.assertIn("<h2>1. Introduction</h2>", out)
        self.assertIn("<p>2. To obtain relaxation</p>", out)


class DbCase(unittest.TestCase):
    def setUp(self):
        self.ctx = app.app_context()
        self.ctx.push()
        limiter.enabled = False
        db.drop_all()
        db.create_all()
        settings = SiteSettings.get()
        settings.article_categories = ["Application", "Forms", "Philosophy", "Technique", "Other"]
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        self.ctx.pop()

    def article(self, title, category):
        a = Article(title=title, author="Vincent Chu", content="<p>Old text.</p>", category=category,
                    section=category, members_only=True, status="published", publish_at=datetime(2026, 10, 21))
        db.session.add(a)
        db.session.commit()
        return a


class VincentBatch(DbCase):
    def test_seed_file(self):
        batch = load_batch("vincent_chu_articles_2026_11.json")
        articles = batch["articles"]
        self.assertEqual(len(articles), 10)
        by_chapter = {a["chapter"]: a for a in articles}
        self.assertEqual({c for c, a in by_chapter.items() if a["category"] == "Training"}, {4, 14, 15, None})
        self.assertEqual({c for c, a in by_chapter.items() if a["category"] == "Philosophy"}, {7, 8, 9, 10, 13, 28})
        self.assertEqual([a["chapter"] for a in sorted(articles, key=lambda a: a["order"])],
                         [4, 7, 8, 9, 10, 13, 14, 15, 28, None])
        self.assertEqual(by_chapter[None]["title"], "Why Practice Tai Chi Chuan Slowly")
        self.assertEqual(by_chapter[14]["title"], "The Three Emphases as an Internal Martial Art")
        for a in articles:
            self.assertFalse(re.match(r"(?i)chapter", a["title"]), a["title"])
            self.assertNotRegex(a["content"], r"(?i)marital art|style=|<span|<font|<h1")
            self.assertTrue(a["summary"], a["title"])
            self.assertIn("<h2>", a["content"], a["title"])
        self.assertIn("<em>", by_chapter[8]["content"])  # .doc italics survived

    def test_apply_twice(self):
        three = self.article("Three Levels of Tai Chi Chuan Practice", "Forms")
        cultivation = self.article("Cultivation and Training in Chinese Martial Art", "Technique")
        solo = self.article("Solo Form", "Forms")
        existing = self.article("tai chi and tai chi chuan", "Application")  # same title, other capitals
        batch = load_batch("vincent_chu_articles_2026_11.json")

        with db.engine.begin() as conn:
            first = apply_batch(conn, batch, log=lambda m: None)
        self.assertEqual(len(first["added"]), 9)
        self.assertEqual(first["skipped"], ["Tai Chi and Tai Chi Chuan"])
        self.assertEqual(sorted(first["moved"]), sorted([three.title, cultivation.title]))

        with db.engine.begin() as conn:
            second = apply_batch(conn, batch, log=lambda m: None)
        self.assertEqual((second["added"], second["moved"]), ([], []))

        db.session.expire_all()
        self.assertEqual(Article.query.count(), 4 + 9)
        self.assertEqual(SiteSettings.get().article_categories,
                         ["Application", "Forms", "Philosophy", "Technique", "Training", "Other"])
        self.assertEqual((db.session.get(Article, three.id).category, db.session.get(Article, three.id).section),
                         ("Training", "Training"))
        self.assertEqual(db.session.get(Article, three.id).content, "<p>Old text.</p>")  # only the category changed
        self.assertEqual(db.session.get(Article, cultivation.id).category, "Training")
        self.assertEqual(db.session.get(Article, solo.id).category, "Forms")
        self.assertEqual(db.session.get(Article, existing.id).content, "<p>Old text.</p>")
        new = Article.query.filter_by(title="Why Practice Tai Chi Chuan Slowly").one()
        self.assertEqual((new.members_only, new.is_free, new.status, new.author, new.category),
                         (True, False, "published", "Vincent Chu", "Training"))
        listed = [a.title for a in Article.query.order_by(Article.publish_at.desc()).limit(9)]
        self.assertEqual(listed[0], "Chinese Martial Arts Curriculum")
        self.assertEqual(listed[-1], "Why Practice Tai Chi Chuan Slowly")


class BulkImport(DbCase):
    def admin_client(self):
        admin = User(email="admin@test.org", password="x", role="admin")
        db.session.add(admin)
        db.session.commit()
        client = app.test_client()
        with client.session_transaction() as s:
            s[admin_module.SESSION_KEY] = admin.id
            s["admin_form_csrf"] = "tok"
        return client

    def post(self, client, files, category="Philosophy", publish="publish"):
        data = {"csrf_token": "tok", "category": category, "publish": publish,
                "files": [(io.BytesIO(content), name) for name, content in files]}
        return client.post("/admin/article_import/", data=data, content_type="multipart/form-data")

    def test_page_and_import(self):
        client = self.admin_client()
        page = client.get("/admin/article_import/")
        self.assertEqual(page.status_code, 200)
        self.assertIn("Philosophy", page.get_data(as_text=True))

        files = [("Chapter 9 Sample Notes.doc", fixture("sample_article.doc")),
                 ("Chapter 3 Sample Practice Notes.docx", fixture("sample_article.docx")),
                 ("notes.pdf", b"%PDF")]
        r = self.post(client, files)
        html = r.get_data(as_text=True)
        self.assertEqual(r.status_code, 200, html[:2000])
        self.assertIn("2 article(s) added", html)
        a = Article.query.filter_by(title="Sample Practice Notes").one()
        b = Article.query.filter_by(title="Sample Notes").one()
        self.assertEqual((a.category, a.members_only, a.status, a.author), ("Philosophy", True, "published", "Vincent Chu"))
        self.assertIn("<h2>II. Standing Practice</h2>", a.content)
        self.assertGreater(a.publish_at, b.publish_at)  # chapter 3 listed before chapter 9

        again = self.post(client, files[:1], publish="draft").get_data(as_text=True)
        self.assertIn("0 article(s) added, 1 skipped", again)
        self.assertEqual(Article.query.count(), 2)

    def test_drafts_and_checks(self):
        client = self.admin_client()
        self.assertIn("Please choose a category", self.post(client, [("a.docx", b"x")], category="Nope").get_data(as_text=True))
        self.post(client, [("Chapter 3 Sample Practice Notes.docx", fixture("sample_article.docx"))], publish="draft")
        a = Article.query.one()
        self.assertEqual((a.status, a.publish_at), ("draft", None))
        bad_csrf = client.post("/admin/article_import/", data={"csrf_token": "wrong", "category": "Philosophy"})
        self.assertEqual(bad_csrf.status_code, 400)

    def test_needs_admin(self):
        r = app.test_client().get("/admin/article_import/")
        self.assertIn(r.status_code, (302, 403))

    def test_function_skips_duplicates_in_one_upload(self):
        data = fixture("sample_article.docx")
        rows = import_word_files([("Notes.docx", data), ("notes (1).docx", data)], "Forms")
        self.assertEqual([r["status"] for r in rows], ["added", "skipped"])


if __name__ == "__main__":
    unittest.main()
