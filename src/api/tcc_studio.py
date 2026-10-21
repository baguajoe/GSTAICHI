"""
Teacher Studio API (/api/tcc/studio/...), for teachers and admins only.

Uploads go straight from the browser (often a phone) to the private taichi-masters bucket with presigned
multipart URLs; the server never handles the video bytes. When an upload completes an EncodingJob is queued
and src/worker.py turns it into protected streaming files.
"""
import io
import re
import secrets
import time
from datetime import datetime
from botocore.exceptions import BotoCoreError, ClientError
from flask import jsonify, request
from sqlalchemy import func
from .models import db, Video, EncodingJob, Article, SiteSettings, Question, PlaybackSession, CORNER_SECTION
from .extensions import limiter
from . import r2
from .r2 import R2NotConfigured
from .tcc_auth import role_required, get_current_user
from .taichi_company import tcc
from .tcc_articles import media_url, reading_minutes, article_card, article_body
from .rich_text import clean_html, editor_html, plain_text, image_url, DESCRIPTION_BLOCKS
from .video_pipeline import chapters_to_vtt
from .article_import import import_document, DocumentError, MAX_DOCUMENT_BYTES

STAFF = ("teacher", "admin")
MAX_PARTS_PER_REQUEST = 50
IMAGE_TYPES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/gif": "gif"}
MAX_IMAGE_BYTES = 10 * 1024 * 1024


def _bad(msg, code=400):
    return jsonify({"msg": msg}), code


def _storage_error(e):
    print(f"R2 problem: {e}")
    message = str(e) if isinstance(e, R2NotConfigured) else "The video storage could not be reached. Please try again."
    return jsonify({"msg": message}), 503


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "")[:19])
    except ValueError:
        return None


def _slugify(title):
    base = re.sub(r"[^a-z0-9]+", "-", (title or "").lower()).strip("-")[:80] or "video"
    slug, n = base, 2
    while Video.query.filter_by(slug=slug).first():
        slug, n = f"{base}-{n}", n + 1
    return slug


def _sections():
    return {s["key"]: s for s in SiteSettings.get().video_sections or []}


def _chapters(value):
    """[{start, label}] with start in seconds; ignores empty rows."""
    chapters = []
    for c in value or []:
        label = str(c.get("label", "")).strip()[:120]
        try:
            start = max(0, int(float(c.get("start", 0))))
        except (TypeError, ValueError):
            continue
        if label:
            chapters.append({"start": start, "label": label})
    return sorted(chapters, key=lambda c: c["start"])


def studio_video(v):
    job = EncodingJob.query.filter_by(video_id=v.id).order_by(EncodingJob.id.desc()).first()
    return {
        "id": v.id, "slug": v.slug, "title": v.title, "section": v.section, "category": v.category,
        "short_description": v.short_description or "",
        "long_description": editor_html(v.long_description, blocks=DESCRIPTION_BLOCKS) if v.long_description else "",
        "show_in_library": v.show_in_library,
        "publish_at": v.publish_at.isoformat() if v.publish_at else None,
        "is_published": v.is_published, "is_free_sample": v.is_free_sample, "tier_rank": v.tier_rank,
        "chapters": v.chapters or [], "status": v.status, "studio_status": v.studio_status,
        "failure_reason": v.failure_reason, "duration_seconds": v.duration_seconds,
        "thumbnail_path": v.custom_thumbnail_path or v.thumbnail_path,
        "thumbnail_url": media_url(v.custom_thumbnail_path or v.thumbnail_path),
        "thumbnail_options": [{"percent": o.get("percent"), "path": o.get("large"), "url": media_url(o.get("small") or o.get("large"))}
                              for o in (v.thumbnail_options or [])],
        "custom_thumbnail_path": v.custom_thumbnail_path,
        "original_filename": v.original_filename, "upload_size": v.upload_size,
        "attempts": job.attempts if job else 0,
        "uploaded_by": v.uploader.name or v.uploader.email if v.uploader else None,
        "created_at": v.created_at.isoformat() if v.created_at else None,
    }


def _apply_video_fields(video, data, sections):
    if "title" in data:
        title = (data.get("title") or "").strip()
        if not title:
            return "Please give the video a title."
        video.title = title[:200]
    if "section" in data:
        if data["section"] not in sections:
            return "Please choose a section."
        video.section = data["section"]
        video.tier_rank = sections[data["section"]].get("tier_rank", 1)
    for field in ("short_description", "category"):
        if field in data:
            video.__setattr__(field, (data.get(field) or "").strip() or None)
    if "long_description" in data:
        video.long_description = clean_html(data.get("long_description"), DESCRIPTION_BLOCKS) or None
    if "show_in_library" in data:
        video.show_in_library = bool(data["show_in_library"])
    if "publish_at" in data:
        video.publish_at = _parse_date(data["publish_at"]) or datetime.utcnow()
    if "is_free_sample" in data:
        video.is_free_sample = bool(data["is_free_sample"])
    if "is_published" in data:
        video.is_published = bool(data["is_published"])
    if "chapters" in data:
        video.chapters = _chapters(data["chapters"])
    return None


@tcc.route('/studio/videos', methods=['GET'])
@role_required(*STAFF)
def studio_videos():
    videos = Video.query.filter(Video.slug.isnot(None)).order_by(Video.created_at.desc(), Video.id.desc()).all()
    return jsonify([studio_video(v) for v in videos])


@tcc.route('/studio/videos', methods=['POST'])
@role_required(*STAFF)
def studio_create_video():
    data = request.get_json(silent=True) or {}
    user = get_current_user()
    # "Waiting for video" until the browser actually starts sending the file
    video = Video(slug=_slugify(data.get("title")), title="", status="placeholder", is_published=True,
                  publish_at=datetime.utcnow(), uploaded_by=user.id,
                  sort_order=(db.session.query(func.max(Video.sort_order)).scalar() or 0) + 1)
    error = _apply_video_fields(video, {"title": data.get("title"), "section": data.get("section"), **data}, _sections())
    if error:
        return _bad(error)
    if video.section == CORNER_SECTION and not video.category:
        video.category = "Other"
    db.session.add(video)
    db.session.flush()
    question_id = data.get("question_id")
    if question_id:
        question = db.session.get(Question, int(question_id))
        if question:
            question.answer_video_id = video.id
            question.status = "answered"
            question.answered_at = datetime.utcnow()
    db.session.commit()
    return jsonify(studio_video(video)), 201


@tcc.route('/studio/videos/<int:video_id>', methods=['PUT'])
@role_required(*STAFF)
def studio_update_video(video_id):
    video = db.session.get(Video, video_id)
    if video is None:
        return _bad("Video not found.", 404)
    data = request.get_json(silent=True) or {}
    error = _apply_video_fields(video, data, _sections())
    if error:
        return _bad(error)
    if "thumbnail_path" in data:
        path = data["thumbnail_path"]
        allowed = {o.get("large") for o in video.thumbnail_options or []}
        if path not in allowed:
            return _bad("Please choose one of the pictures shown.")
        video.thumbnail_path = path
        video.custom_thumbnail_path = None
    if "custom_thumbnail_path" in data:
        path = data["custom_thumbnail_path"] or None
        if path and not re.match(rf"^{re.escape(video.slug)}/thumbs/custom-[a-z0-9]+\.(jpg|png|webp)$", path):
            return _bad("That picture is not valid.")
        video.custom_thumbnail_path = path
    if "chapters" in data and video.status == "ready" and video.duration_seconds:
        # keep the chapters file in storage in step with the list (the player itself uses the list)
        try:
            if video.chapters:
                r2.put_text(r2.streams_bucket(), f"{video.slug}/chapters.vtt",
                            chapters_to_vtt(video.chapters, video.duration_seconds), "text/vtt")
                video.chapters_vtt_path = f"{video.slug}/chapters.vtt"
            else:
                video.chapters_vtt_path = None
        except Exception as e:
            print(f"Could not update chapters.vtt for {video.slug}: {e}")
    db.session.commit()
    return jsonify(studio_video(video))


@tcc.route('/studio/videos/<int:video_id>', methods=['DELETE'])
@role_required(*STAFF)
def studio_delete_video(video_id):
    video = db.session.get(Video, video_id)
    if video is None:
        return _bad("Video not found.", 404)
    try:
        if video.upload_id and video.master_r2_key and video.status == "uploading":
            r2.abort_multipart(r2.masters_bucket(), video.master_r2_key, video.upload_id)
        if video.master_r2_key:
            r2.delete_object(r2.masters_bucket(), video.master_r2_key)
        r2.delete_prefix(r2.streams_bucket(), video.slug)
    except R2NotConfigured:
        pass  # nothing can be stored yet, so nothing to delete
    except Exception as e:
        return _storage_error(e)
    Question.query.filter_by(answer_video_id=video.id).update({"answer_video_id": None})
    PlaybackSession.query.filter_by(video_id=video.id).delete()
    EncodingJob.query.filter_by(video_id=video.id).delete()
    db.session.delete(video)
    db.session.commit()
    return jsonify({"msg": "The video has been deleted."})


# ----- uploads -----

@tcc.route('/studio/videos/<int:video_id>/upload/start', methods=['POST'])
@limiter.limit("30 per hour")
@role_required(*STAFF)
def studio_upload_start(video_id):
    video = db.session.get(Video, video_id)
    if video is None:
        return _bad("Video not found.", 404)
    data = request.get_json(silent=True) or {}
    filename = re.sub(r"[^\w.\- ]", "", str(data.get("filename") or "video"))[:200] or "video"
    try:
        size = int(data.get("size") or 0)
    except ValueError:
        size = 0
    if size <= 0:
        return _bad("The file is empty.")
    if size > r2.MAX_UPLOAD_BYTES:
        return _bad("This file is bigger than 10 GB. Please make it shorter or smaller and try again.")
    content_type = str(data.get("content_type") or "")
    if content_type and not content_type.startswith("video/"):
        return _bad("This does not look like a video file.")

    # Same file again: carry on with the upload that was interrupted
    if video.upload_id and video.status == "uploading" and video.original_filename == filename and video.upload_size == size:
        try:
            parts = r2.list_parts(r2.masters_bucket(), video.master_r2_key, video.upload_id)
            return jsonify({"upload_id": video.upload_id, "part_size": r2.PART_SIZE, "parts": parts, "resumed": True})
        except Exception as e:
            print(f"Could not resume upload for {video.slug}, starting again: {e}")

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "mp4"
    key = f"{video.slug}/master-{int(time.time())}.{re.sub(r'[^a-z0-9]', '', ext)[:5] or 'mp4'}"
    try:
        upload_id = r2.start_multipart(r2.masters_bucket(), key, content_type or "video/mp4")
    except Exception as e:
        return _storage_error(e)
    video.upload_id, video.master_r2_key = upload_id, key
    video.upload_size, video.original_filename = size, filename
    video.status, video.failure_reason = "uploading", None
    db.session.commit()
    return jsonify({"upload_id": upload_id, "part_size": r2.PART_SIZE, "parts": [], "resumed": False})


@tcc.route('/studio/videos/<int:video_id>/upload/parts', methods=['POST'])
@limiter.limit("600 per hour")
@role_required(*STAFF)
def studio_upload_part_urls(video_id):
    video = db.session.get(Video, video_id)
    if video is None or not video.upload_id:
        return _bad("This upload has not been started.", 404)
    numbers = (request.get_json(silent=True) or {}).get("part_numbers") or []
    max_part = -(-video.upload_size // r2.PART_SIZE)
    numbers = [int(n) for n in numbers[:MAX_PARTS_PER_REQUEST] if str(n).isdigit() and 1 <= int(n) <= max_part]
    try:
        urls = {n: r2.presign_part(r2.masters_bucket(), video.master_r2_key, video.upload_id, n) for n in numbers}
    except Exception as e:
        return _storage_error(e)
    return jsonify({"urls": urls})


@tcc.route('/studio/videos/<int:video_id>/upload/complete', methods=['POST'])
@role_required(*STAFF)
def studio_upload_complete(video_id):
    video = db.session.get(Video, video_id)
    if video is None or not video.upload_id:
        return _bad("This upload has not been started.", 404)
    parts = (request.get_json(silent=True) or {}).get("parts") or []
    expected = -(-video.upload_size // r2.PART_SIZE)
    if len({int(p["part_number"]) for p in parts}) != expected:
        return _bad("Some pieces of the file are missing. Please press Continue upload.")
    try:
        r2.complete_multipart(r2.masters_bucket(), video.master_r2_key, video.upload_id, parts)
        if r2.object_size(r2.masters_bucket(), video.master_r2_key) != video.upload_size:
            return _bad("The uploaded file is not complete. Please upload it again.")
    except Exception as e:
        return _storage_error(e)
    video.upload_id = None
    video.status = "processing"
    db.session.add(EncodingJob(video_id=video.id, status="queued"))
    db.session.commit()
    return jsonify(studio_video(video))


@tcc.route('/studio/videos/<int:video_id>/upload/abort', methods=['POST'])
@role_required(*STAFF)
def studio_upload_abort(video_id):
    video = db.session.get(Video, video_id)
    if video is None or not video.upload_id:
        return jsonify({"ok": True})
    try:
        r2.abort_multipart(r2.masters_bucket(), video.master_r2_key, video.upload_id)
    except Exception as e:
        print(f"Abort failed (ignored): {e}")
    video.upload_id = None
    video.status = "placeholder" if not video.hls_master_path else "ready"
    db.session.commit()
    return jsonify(studio_video(video))


@tcc.route('/studio/videos/<int:video_id>/retry', methods=['POST'])
@role_required(*STAFF)
def studio_retry(video_id):
    video = db.session.get(Video, video_id)
    if video is None:
        return _bad("Video not found.", 404)
    if video.status != "failed" or not video.master_r2_key:
        return _bad("Only a failed video with an uploaded file can be tried again.")
    video.status, video.failure_reason = "processing", None
    db.session.add(EncodingJob(video_id=video.id, status="queued"))
    db.session.commit()
    return jsonify(studio_video(video))


@tcc.route('/studio/videos/<int:video_id>/thumbnail-upload', methods=['POST'])
@role_required(*STAFF)
def studio_thumbnail_upload(video_id):
    video = db.session.get(Video, video_id)
    if video is None:
        return _bad("Video not found.", 404)
    content_type = (request.get_json(silent=True) or {}).get("content_type")
    if content_type not in ("image/jpeg", "image/png", "image/webp"):
        return _bad("Please choose a JPG or PNG picture.")
    path = f"{video.slug}/thumbs/custom-{secrets.token_hex(6)}.{IMAGE_TYPES[content_type]}"
    try:
        url = r2.presign_put(r2.streams_bucket(), path, content_type)
    except Exception as e:
        return _storage_error(e)
    return jsonify({"upload_url": url, "path": path, "url": media_url(path)})


# ----- articles -----

def studio_article(a):
    now = datetime.utcnow()
    if a.status == "draft":
        label = "Draft"
    elif a.publish_at and a.publish_at > now:
        label = "Scheduled"
    else:
        label = "Published"
    return {
        "id": a.id, "title": a.title, "author": a.author, "category": a.category, "summary": a.summary or "",
        "content": editor_html(a.content), "is_free": bool(a.is_free),
        "cover_image_path": a.cover_image_path, "cover_image_url": media_url(a.cover_image_path),
        "cover_position": a.cover_position or "50% 50%",
        "publish_at": a.publish_at.isoformat() if a.publish_at else None, "status": label,
        "reading_minutes": reading_minutes(a.content), "read_count": a.read_count or 0,
        "updated_at": a.updated_at.isoformat() if a.updated_at else None,
    }


def _article_fields(data):
    """Checks the form. Returns (error, cleaned fields)."""
    title = (data.get("title") or "").strip()
    if not title:
        return "Please give the article a title.", None
    content = clean_html(data.get("content"))
    if data.get("action", "draft") == "publish" and not plain_text(content) and "<figure" not in content:
        return "Please write the article before publishing it.", None
    cover = data.get("cover_image_path") or None
    if cover and not re.match(r"^article-images/[a-z0-9]+\.(jpg|png|webp|gif)$", cover):
        return "The cover picture is not valid.", None
    position = str(data.get("cover_position") or "")
    position = position if re.match(r"^\d{1,3}% \d{1,3}%$", position) else None
    return None, {"title": title[:200], "content": content, "cover": cover, "position": position}


def _apply_article(article, data):
    error, fields = _article_fields(data)
    if error:
        return error
    title, content, cover = fields["title"], fields["content"], fields["cover"]
    action = data.get("action", "draft")
    article.title = title[:200]
    article.author = ((data.get("author") or "").strip() or get_current_user().name or "")[:100]
    article.category = (data.get("category") or "").strip() or None
    article.section = article.category or "Other"
    article.summary = (data.get("summary") or "").strip() or None
    article.content = content
    article.cover_image_path = cover
    article.cover_position = fields["position"]
    article.is_free = bool(data.get("is_free"))
    article.members_only = True
    article.publish_at = _parse_date(data.get("publish_at")) or datetime.utcnow()
    if action == "publish":
        article.status = "scheduled" if article.publish_at > datetime.utcnow() else "published"
    else:
        article.status = "draft"
    return None


@tcc.route('/studio/articles', methods=['GET'])
@role_required(*STAFF)
def studio_articles():
    articles = Article.query.filter(Article.members_only.is_(True)).order_by(Article.updated_at.desc().nullslast(), Article.id.desc()).all()
    return jsonify([studio_article(a) for a in articles])


@tcc.route('/studio/articles', methods=['POST'])
@role_required(*STAFF)
def studio_create_article():
    article = Article(created_by=get_current_user().id, content="", author="", title="")
    error = _apply_article(article, request.get_json(silent=True) or {})
    if error:
        return _bad(error)
    db.session.add(article)
    db.session.commit()
    return jsonify(studio_article(article)), 201


@tcc.route('/studio/articles/<int:article_id>', methods=['PUT'])
@role_required(*STAFF)
def studio_update_article(article_id):
    article = Article.query.filter_by(id=article_id, members_only=True).first()
    if article is None:
        return _bad("Article not found.", 404)
    error = _apply_article(article, request.get_json(silent=True) or {})
    if error:
        return _bad(error)
    db.session.commit()
    return jsonify(studio_article(article))


@tcc.route('/studio/articles/preview', methods=['POST'])
@role_required(*STAFF)
def studio_preview_article():
    """The article exactly as the reader page shows it, from the unsaved form (nothing is saved)."""
    data = request.get_json(silent=True) or {}
    error, fields = _article_fields({**data, "action": "draft", "title": data.get("title") or "Untitled"})
    if error:
        return _bad(error)
    article = Article(id=int(data["id"]) if str(data.get("id") or "").isdigit() else None,
                      title=fields["title"], author=(data.get("author") or "").strip(), content=fields["content"],
                      category=(data.get("category") or "").strip() or None, summary=(data.get("summary") or "").strip(),
                      cover_image_path=fields["cover"], cover_position=fields["position"], is_free=bool(data.get("is_free")),
                      publish_at=_parse_date(data.get("publish_at")) or datetime.utcnow())
    return jsonify({**article_card(article, True), **article_body(article, fields["content"], get_current_user())})


@tcc.route('/studio/articles/<int:article_id>', methods=['DELETE'])
@role_required(*STAFF)
def studio_delete_article(article_id):
    article = Article.query.filter_by(id=article_id, members_only=True).first()
    if article is None:
        return _bad("Article not found.", 404)
    db.session.delete(article)
    db.session.commit()
    return jsonify({"msg": "The article has been deleted."})


@tcc.route('/studio/images', methods=['POST'])
@limiter.limit("120 per hour")
@role_required(*STAFF)
def studio_image_upload():
    """A presigned address for one picture: a cover (public), or with "private" a photo inside an article or
    a video description (members only; shown with a signed link)."""
    data = request.get_json(silent=True) or {}
    content_type = data.get("content_type")
    if content_type not in IMAGE_TYPES:
        return _bad("Please choose a JPG, PNG, WEBP or GIF picture.")
    if int(data.get("size") or 0) > MAX_IMAGE_BYTES:
        return _bad("This picture is bigger than 10 MB. Please use a smaller one.")
    folder = "article-private" if data.get("private") else "article-images"
    path = f"{folder}/{secrets.token_hex(12)}.{IMAGE_TYPES[content_type]}"
    try:
        url = r2.presign_put(r2.streams_bucket(), path, content_type)
    except Exception as e:
        return _storage_error(e)
    return jsonify({"upload_url": url, "path": path, "url": image_url(path, "studio")})


def _store_document_photo(raw):
    """A photo from an uploaded document: at most 1600 pixels on the longest side, saved as WebP in the
    private article folder. Returns the stored path, or None if it is not a picture we can read."""
    from PIL import Image, ImageOps
    try:
        with Image.open(io.BytesIO(raw)) as img:
            img = ImageOps.exif_transpose(img)
            if min(img.size) < 48:
                return None  # icons and dividers
            img = img.convert("RGBA" if img.mode in ("RGBA", "LA", "P") else "RGB")
            img.thumbnail((1600, 1600), Image.LANCZOS)
            out = io.BytesIO()
            img.save(out, format="WEBP", quality=82, method=4)
    except Exception as e:
        print(f"Document photo skipped: {e}")
        return None
    path = f"article-private/{secrets.token_hex(12)}.webp"
    r2.put_bytes(r2.streams_bucket(), path, out.getvalue(), "image/webp")
    return path


@tcc.route('/studio/articles/import', methods=['POST'])
@limiter.limit("30 per hour")
@role_required(*STAFF)
def studio_import_article():
    """Turns an uploaded Word, PDF, text or Markdown file into an unsaved article for the editor."""
    upload = request.files.get("file")
    if upload is None or not upload.filename:
        return _bad("Please choose a file to upload.")
    data = upload.read(MAX_DOCUMENT_BYTES + 1)
    try:
        result = import_document(upload.filename, data, _store_document_photo)
    except DocumentError as e:
        return _bad(str(e))
    except (R2NotConfigured, BotoCoreError, ClientError) as e:
        return _storage_error(e)
    except Exception as e:
        print(f"Article import failed for {upload.filename}: {type(e).__name__}: {e}")
        return _bad("This document could not be read. Please try saving it again as .docx or PDF, "
                    "or copy and paste the text into a new article.")
    return jsonify({**result, "content": editor_html(result["content"])})
