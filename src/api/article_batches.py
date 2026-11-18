"""
Adds a batch of converted articles (a JSON file in seed_data/) to the database. Called by a data migration, so it
runs once per database on deploy (render.yaml preDeployCommand: flask setup-database). Running it again changes
nothing:

- each article is added only if no article with the same title (any capitals) exists yet
- the batch's new category is added to the site's article categories only if it is missing
- the existing articles named in "move_to_training" get the new category (only the category changes); the
  migration runs once, so a later change made in the admin is not undone on the next deploy

Uses plain SQL tables, not the models, so the migration keeps working when the models change later.
"""
import json
import os
from datetime import datetime, timedelta

import sqlalchemy as sa

SEED_DIR = os.path.join(os.path.dirname(__file__), "seed_data")

article = sa.table(
    "article",
    sa.column("id", sa.Integer), sa.column("title", sa.String), sa.column("section", sa.String),
    sa.column("content", sa.Text), sa.column("author", sa.String), sa.column("members_only", sa.Boolean),
    sa.column("is_free", sa.Boolean), sa.column("summary", sa.Text), sa.column("category", sa.String),
    sa.column("status", sa.String), sa.column("publish_at", sa.DateTime), sa.column("read_count", sa.Integer),
    sa.column("created_at", sa.DateTime), sa.column("updated_at", sa.DateTime),
)
site_settings = sa.table("site_settings", sa.column("id", sa.Integer), sa.column("article_categories", sa.JSON))


def load_batch(filename):
    with open(os.path.join(SEED_DIR, filename), encoding="utf-8") as f:
        return json.load(f)


def _same_title(title):
    return sa.func.lower(sa.func.trim(article.c.title)) == title.strip().lower()


def add_category(conn, category):
    for row in conn.execute(sa.select(site_settings.c.id, site_settings.c.article_categories)).all():
        categories = list(row.article_categories or [])
        if category in categories:
            continue
        # Before "Other", which stays last
        at = categories.index("Other") if "Other" in categories else len(categories)
        categories.insert(at, category)
        conn.execute(site_settings.update().where(site_settings.c.id == row.id).values(article_categories=categories))


def apply_batch(conn, batch, now=None, log=print):
    """Returns {"added": [titles], "skipped": [titles], "moved": [titles]}."""
    now = now or datetime.utcnow()
    result = {"added": [], "skipped": [], "moved": []}
    category = batch.get("new_category")
    if category:
        add_category(conn, category)

    articles = sorted(batch["articles"], key=lambda a: a["order"])
    for a in articles:
        if conn.execute(sa.select(article.c.id).where(_same_title(a["title"]))).first():
            result["skipped"].append(a["title"])
            log(f"Article '{a['title']}' is already there; not added again.")
            continue
        # The list shows the newest first: the first in the batch gets the latest time
        publish_at = now - timedelta(minutes=a["order"] - 1)
        conn.execute(article.insert().values(
            title=a["title"], author=batch.get("author") or "Vincent Chu", content=a["content"],
            summary=a.get("summary") or None, category=a["category"], section=a["category"],
            members_only=True, is_free=False, status="published", publish_at=publish_at,
            read_count=0, created_at=now, updated_at=now,
        ))
        result["added"].append(a["title"])
        log(f"Added article '{a['title']}' ({a['category']}).")

    for title in batch.get("move_to_training") or []:
        for row in conn.execute(sa.select(article.c.id, article.c.category).where(_same_title(title))).all():
            if row.category == category:
                continue
            conn.execute(article.update().where(article.c.id == row.id)
                         .values(category=category, section=category, updated_at=now))
            result["moved"].append(title)
            log(f"Moved '{title}' (article {row.id}) from {row.category or 'no category'} to {category}.")
    return result


# ----- Admin: Bulk import -----

MAX_BULK_FILES = 30
BULK_EXTENSIONS = (".doc", ".docx")


def import_word_files(files, category, publish=True, author="Vincent Chu", save_photo=None, now=None):
    """Turns several Word files into members-only articles in one go, with the same conversion as the Studio upload.
    files: [(filename, bytes)]. The title comes from the file name ("Chapter 7 Tai Chi and Tai Chi Chuan.doc" ->
    "Tai Chi and Tai Chi Chuan"). They are listed in chapter order. A title that already exists is skipped.
    Returns [{"file", "title", "status": "added" | "skipped" | "error", "message", "id"}]."""
    from .article_import import (import_document, title_from_filename, chapter_number, drop_leading_title,
                                 DocumentError, _summary)
    from .models import db, Article
    from .rich_text import clean_html

    now = now or datetime.utcnow()
    save_photo = save_photo or (lambda raw: None)
    rows = []
    ordered = sorted(files, key=lambda f: (chapter_number(f[0]) is None, chapter_number(f[0]) or 0, f[0].lower()))
    for position, (filename, data) in enumerate(ordered):
        row = {"file": filename, "title": title_from_filename(filename), "status": "error", "message": "", "id": None}
        rows.append(row)
        if not filename.lower().endswith(BULK_EXTENSIONS):
            row["message"] = "Not a Word file (.doc or .docx)."
            continue
        if not row["title"]:
            row["message"] = "The file name has no title in it."
            continue
        existing = Article.query.filter(
            sa.func.lower(sa.func.trim(Article.title)) == row["title"].strip().lower()).first()
        if existing is not None:
            row.update(status="skipped", id=existing.id, message="An article with this title already exists.")
            continue
        try:
            result = import_document(filename, data, save_photo, allow_doc=True)
        except DocumentError as e:
            row["message"] = str(e)
            continue
        except Exception as e:
            print(f"Bulk import failed for {filename}: {type(e).__name__}: {e}")
            row["message"] = "This file could not be read. Try saving it again as .docx."
            continue
        content = clean_html(drop_leading_title(result["content"], row["title"], result["title"]))
        article = Article(
            title=row["title"], author=author, content=content, summary=_summary(content) or None,
            category=category, section=category or "Other", members_only=True, is_free=False,
            status="published" if publish else "draft",
            publish_at=now - timedelta(minutes=position) if publish else None,
        )
        db.session.add(article)
        db.session.flush()
        row.update(status="added", id=article.id, message=" ".join(result.get("notes") or []))
    db.session.commit()
    return rows
