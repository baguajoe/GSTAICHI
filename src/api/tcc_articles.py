"""
Member articles (Article.members_only = True), separate from the public articles on the main site.

Every paying member (any tier) can read every member article. Others see the title, summary and cover
picture only: the full text is sent only from an authenticated request by a paying member. Articles marked
"Free for everyone" (Article.is_free) are sent in full to anyone, signed in or not.
The text is sanitized HTML (see rich_text.py). Videos placed in an article still need the viewer's plan.
"""
import math
import os
from datetime import datetime, timedelta
from flask import jsonify, request
from sqlalchemy import or_
from .models import db, Article, Video, SiteSettings
from .extensions import limiter
from .taichi_company import tcc, _viewer, _card, visible_videos
from .rich_text import plain_text, reader_html, video_slugs

NEW_DAYS = 14
WORDS_PER_MINUTE = 200


def media_url(path):
    """Cover and article pictures live in the streams bucket under article-images/ (served by the media Worker)."""
    if not path:
        return None
    if path.startswith(("http://", "https://")):
        return path
    base = os.getenv("MEDIA_BASE_URL", "").rstrip("/")
    return f"{base}/{path.lstrip('/')}" if base else None


def published_member_articles():
    now = datetime.utcnow()
    return (Article.query.filter(Article.members_only.is_(True), Article.status.in_(("published", "scheduled")))
            .filter(or_(Article.publish_at.is_(None), Article.publish_at <= now)))


def reading_minutes(text):
    return max(1, math.ceil(len(plain_text(text).split()) / WORDS_PER_MINUTE))


def article_card(article, can_read):
    published = article.publish_at or article.created_at
    return {
        "id": article.id,
        "title": article.title,
        "author": article.author,
        "category": article.category,
        "summary": article.summary or "",
        "cover_image_url": media_url(article.cover_image_path),
        "cover_position": article.cover_position or "50% 50%",
        "is_free": bool(article.is_free),
        "published_at": published.isoformat() if published else None,
        "reading_minutes": reading_minutes(article.content),
        "is_new": bool(published) and published >= datetime.utcnow() - timedelta(days=NEW_DAYS),
        "locked": not can_read,
    }


def _is_member(viewer):
    return viewer is not None and viewer.is_paying_member


def _can_read(viewer, article):
    return bool(article.is_free) or _is_member(viewer)


def article_videos(content, viewer):
    """What the reader needs for each video placed in the article, by slug. The player checks the plan again."""
    slugs = video_slugs(content)
    if not slugs:
        return {}
    videos = {}
    for video in visible_videos().filter(Video.slug.in_(slugs)).all():
        data = _card(video, viewer)
        data["chapters"] = video.chapters or []
        data["processing"] = video.status in ("uploading", "processing")
        videos[video.slug] = data
    return videos


def article_body(article, content, viewer):
    """The full text and what goes with it, for a reader (or the Studio preview)."""
    return {
        "content_html": reader_html(content, f"article-{article.id or 0}"),
        "videos": article_videos(content, viewer),
        "watermark_text": f"{viewer.email} · Member {viewer.id}" if viewer else (SiteSettings.get().app_name or ""),
        "licensed_to": viewer.email if viewer else None,
    }


@tcc.route('/articles', methods=['GET'])
@limiter.limit("60 per minute")
def list_member_articles():
    viewer = _viewer()
    query = published_member_articles()
    category = (request.args.get("category") or "").strip()
    if category:
        query = query.filter(Article.category == category)
    search = (request.args.get("q") or "").strip()
    if search:
        like = f"%{search}%"
        query = query.filter(or_(Article.title.ilike(like), Article.summary.ilike(like),
                                 Article.author.ilike(like), Article.content.ilike(like)))
    articles = query.order_by(Article.publish_at.desc().nullslast(), Article.id.desc()).all()
    is_member = _is_member(viewer)
    return jsonify({"articles": [article_card(a, is_member or bool(a.is_free)) for a in articles], "can_read": is_member})


@tcc.route('/articles/legacy/<int:legacy_id>', methods=['GET'])
@limiter.limit("60 per minute")
def find_legacy_article(legacy_id):
    """The member article for a link to the old public Articles page (/articles/<legacy id>)."""
    article = published_member_articles().filter(Article.legacy_id == legacy_id).first()
    if article is None:
        return jsonify({"msg": "We could not find that article."}), 404
    return jsonify({"id": article.id})


@tcc.route('/articles/<int:article_id>', methods=['GET'])
@limiter.limit("30 per minute")
def get_member_article(article_id):
    viewer = _viewer()
    article = published_member_articles().filter(Article.id == article_id).first()
    if article is None:
        return jsonify({"msg": "We could not find that article."}), 404
    can_read = _can_read(viewer, article)
    data = article_card(article, can_read)
    if can_read:
        data.update(article_body(article, article.content, viewer))
        article.read_count = (article.read_count or 0) + 1
        db.session.commit()
    return jsonify(data)
