"""Members' practice videos attached to "Ask Vincent" questions: limits, who may watch, and deleting them.

The browser uploads before the question exists, so an upload is identified by a signed token holding its owner,
storage key and length. The files live in the private masters bucket under member-questions/, and are only ever
reached through short-lived presigned addresses made after checking who is asking.
"""
import os
import secrets
from datetime import datetime, timedelta
from botocore.exceptions import BotoCoreError, ClientError
from itsdangerous import URLSafeTimedSerializer, BadSignature
from . import r2
from .models import db, Question, SiteSettings

MAX_SECONDS = 3 * 60
MAX_BYTES = 500 * 1024 ** 2
KEY_PREFIX = "member-questions/"
VIDEO_TYPES = {".mp4": "video/mp4", ".mov": "video/quicktime", ".webm": "video/webm"}
KEEP_AFTER_ANSWER = timedelta(days=90)
KEEP_IF_NEVER_ANSWERED = timedelta(days=120)
# An upload token lasts a day. A file nobody attached by twice that can no longer be attached, so it can go.
TOKEN_SECONDS = 24 * 60 * 60
# Only checked when the upload starts, so a slow upload is fine. Short, because until it runs out the same
# address could replace the file after its size was checked.
UPLOAD_URL_SECONDS = 15 * 60
ABANDONED_AFTER = timedelta(days=2)

STORAGE_ERRORS = (r2.R2NotConfigured, BotoCoreError, ClientError)


def video_type(filename, content_type):
    """(extension, content type) for an allowed video, or None. A file's own extension decides, because
    phones often report no type or a vague one; the reported type is only used when there is no extension."""
    ext = os.path.splitext(filename or "")[1].lower()
    if ext:
        return (ext, VIDEO_TYPES[ext]) if ext in VIDEO_TYPES else None
    reported = (content_type or "").split(";")[0].strip().lower()
    for known_ext, known_type in VIDEO_TYPES.items():
        if reported == known_type:
            return known_ext, known_type
    return None


def new_key(ext):
    return f"{KEY_PREFIX}{secrets.token_urlsafe(32)}{ext}"


def _signer():
    return URLSafeTimedSerializer(os.environ.get("FLASK_APP_KEY", "sample key"), salt="question-video")


def make_upload_token(user, key, seconds):
    return _signer().dumps({"user": user.id, "key": key, "seconds": seconds})


def read_upload_token(token, user):
    """The upload this token stands for, or None if it is not this member's, was altered or has expired."""
    if not isinstance(token, str) or not token:
        return None
    try:
        upload = _signer().loads(token, max_age=TOKEN_SECONDS)
    except BadSignature:  # includes an expired token
        return None
    if upload.get("user") != user.id or not str(upload.get("key", "")).startswith(KEY_PREFIX):
        return None
    return upload


def is_attached(key):
    return Question.query.filter_by(member_video_key=key).first() is not None


def stored_size(key):
    """The size of an uploaded file from storage (never from the browser), or None if it did not arrive."""
    try:
        return r2.object_size(r2.masters_bucket(), key)
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") in ("404", "NoSuchKey", "NotFound"):
            return None
        raise


def delete_file(key):
    r2.delete_object(r2.masters_bucket(), key)


def _month_start(now):
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def videos_allowance(user, now=None):
    """(videos allowed a month, videos left this calendar month in UTC, when the next month starts).
    A video that has since been removed still counts for the month it was sent."""
    now = now or datetime.utcnow()
    per_month = SiteSettings.get().question_videos_per_month
    start = _month_start(now)
    used = Question.query.filter(Question.user_id == user.id, Question.member_video_uploaded_at >= start).count()
    return per_month, max(0, per_month - used), _month_start(start + timedelta(days=32))


def can_watch(question, viewer):
    """Staff always can. A member can only watch their own, and only while on a paid plan."""
    if viewer is None or not question.member_video_key or question.member_video_deleted_at:
        return False
    if viewer.is_staff:
        return True
    return viewer.id == question.user_id and viewer.is_paying_member


def removed_note(question):
    days = (KEEP_AFTER_ANSWER if question.answered_at else KEEP_IF_NEVER_ANSWERED).days
    return f"Video removed after {days} days."


def member_video_json(question, viewer):
    """What this viewer may know about a question's video. None if there is no video or it is not theirs to see.
    Watch addresses are made here, after the check, and last about an hour. The storage key is never included."""
    if not question.member_video_key or viewer is None:
        return None
    if not viewer.is_staff and viewer.id != question.user_id:
        return None
    data = {"state": "ready", "seconds": question.member_video_seconds, "size": question.member_video_size,
            "watch_url": None}
    if question.member_video_deleted_at:
        data.update(state="removed", note=removed_note(question))
    elif not can_watch(question, viewer):
        data.update(state="locked", note="Your video can be watched while you are on a paid plan.")
    else:
        bucket, key = r2.masters_bucket(), question.member_video_key
        try:
            data["watch_url"] = r2.presign_get(bucket, key)
            if viewer.is_staff:
                # Some computers cannot play phone videos in the browser, so staff can also save the file
                ext = os.path.splitext(key)[1]
                data["download_url"] = r2.presign_get(bucket, key, download_name=f"member-video-{question.id}{ext}")
        except STORAGE_ERRORS as e:
            print(f"Could not make a watch address for question {question.id}: {e}")
    return data


def live_videos(user):
    return Question.query.filter(Question.user_id == user.id, Question.member_video_key.isnot(None),
                                 Question.member_video_deleted_at.is_(None)).all()


def _delete_and_mark(questions, now):
    """Marks each question only once its file is gone, so a failed delete is tried again next time."""
    removed, failed = 0, 0
    for question in questions:
        try:
            delete_file(question.member_video_key)
            question.member_video_deleted_at = now
            db.session.commit()
            removed += 1
        except STORAGE_ERRORS as e:
            db.session.rollback()
            failed += 1
            print(f"Could not delete the video of question {question.id}: {e}")
    return removed, failed


def delete_member_videos(user, now=None):
    """Removes all of one member's videos at once. Returns (removed, failed)."""
    return _delete_and_mark(live_videos(user), now or datetime.utcnow())


def _purge_abandoned(now):
    """Deletes uploads never attached to a question (the member left the page, or an account was deleted).
    Only ever touches member-questions/: Vincent's own master videos share this bucket."""
    bucket = r2.masters_bucket()
    known = {key for (key,) in db.session.query(Question.member_video_key).filter(Question.member_video_key.isnot(None))}
    db.session.commit()  # no open transaction while talking to storage (see the worker's note about migrations)
    removed = 0
    for key, modified in r2.list_objects(bucket, KEY_PREFIX):
        if key in known or modified.replace(tzinfo=None) > now - ABANDONED_AFTER:
            continue
        r2.delete_object(bucket, key)
        removed += 1
    return removed


def purge_question_videos(now=None):
    """Deletes videos 90 days after the answer, or 120 days after sending if never answered, then abandoned uploads.
    Safe to run as often as you like. Returns counts of what happened."""
    now = now or datetime.utcnow()
    answered_long_ago = db.and_(Question.answered_at.isnot(None), Question.answered_at <= now - KEEP_AFTER_ANSWER)
    never_answered = db.and_(Question.answered_at.is_(None), Question.created_at <= now - KEEP_IF_NEVER_ANSWERED)
    due = Question.query.filter(Question.member_video_key.isnot(None), Question.member_video_deleted_at.is_(None),
                                db.or_(answered_long_ago, never_answered)).all()
    removed, failed = _delete_and_mark(due, now)
    return {"removed": removed, "failed": failed, "abandoned": _purge_abandoned(now)}
