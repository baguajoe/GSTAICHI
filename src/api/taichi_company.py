"""Tai Chi Company subscription app API, registered at /api/tcc."""
import os
from datetime import datetime
from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from .models import db, SiteSettings, Tier, Video, CORNER_SECTION
from .extensions import limiter
from .tcc_auth import role_required, get_current_user

tcc = Blueprint('tcc', __name__)

MIN_PASSWORD_LENGTH = 8
NEW_THIS_MONTH_LIMIT = 8
LATEST_FROM_TEACHER_LIMIT = 8


@tcc.route('/settings', methods=['GET'])
def get_settings():
    """Public branding and contact info. Every name, color, phone and address in the app comes from here."""
    return jsonify(SiteSettings.get().serialize_public())


@tcc.route('/manifest.webmanifest', methods=['GET'])
def get_manifest():
    """Home-screen app manifest, named and colored from SiteSettings. Paths are relative to the site."""
    settings = SiteSettings.get()
    manifest = {
        "name": settings.app_name,
        "short_name": settings.app_name,
        "description": f"Tai Chi Chuan video lessons{(' from ' + settings.school_name) if settings.school_name else ''}.",
        "start_url": "/tai-chi-company/",
        "scope": "/tai-chi-company/",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": settings.primary_color,
        "icons": [
            {"src": "/tcc-icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/tcc-icons/icon-512.png", "sizes": "512x512", "type": "image/png"},
            {"src": "/tcc-icons/maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        ],
    }
    response = jsonify(manifest)
    response.mimetype = "application/manifest+json"
    return response


@tcc.route('/tiers', methods=['GET'])
def get_tiers():
    """Tiers with their currently offered plans and prices (from the database, never hard-coded)."""
    tiers = Tier.query.order_by(Tier.sort_order, Tier.rank).all()
    return jsonify([t.serialize() for t in tiers])


@tcc.route('/me', methods=['GET'])
@role_required()
def get_me():
    return jsonify(get_current_user().serialize_account())


@tcc.route('/change-password', methods=['POST'])
@limiter.limit("10 per hour")
@role_required()
def change_password():
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    new_password = data.get("new_password") or ""
    if not check_password_hash(user.password, data.get("current_password") or ""):
        return jsonify({"msg": "Your current password is not correct."}), 400
    if len(new_password) < MIN_PASSWORD_LENGTH:
        return jsonify({"msg": f"Your new password must be at least {MIN_PASSWORD_LENGTH} characters."}), 400
    user.password = generate_password_hash(new_password)
    db.session.commit()
    return jsonify({"msg": "Your password has been changed."}), 200


# ----- Video library (cards and details only; protected playback comes in a later phase) -----

def _viewer():
    """The signed-in user, or None. An expired or broken token is treated as signed out."""
    try:
        user = get_current_user(optional=True)
    except Exception:
        return None
    if user is None or user.is_suspended:
        return None
    return user


def visible_videos():
    now = datetime.utcnow()
    return (Video.query
            .filter(Video.slug.isnot(None), Video.is_published.is_(True))
            .filter((Video.publish_at.is_(None)) | (Video.publish_at <= now))
            .order_by(Video.sort_order, Video.id))


def _card(video, viewer):
    data = video.serialize_card()
    rank = viewer.effective_tier_rank if viewer else 0
    data["locked"] = not video.is_free_sample and video.tier_rank > rank
    path = data.pop("thumbnail_path")
    base = os.getenv("MEDIA_BASE_URL", "").rstrip("/")
    data["thumbnail_url"] = f"{base}/{path.lstrip('/')}" if path and base else None
    return data


def _is_new_this_month(video, now):
    return bool(video.publish_at) and video.publish_at.year == now.year and video.publish_at.month == now.month


@tcc.route('/library', methods=['GET'])
@tcc.route('/videos', methods=['GET'])
@limiter.limit("60 per minute")
def get_videos():
    viewer = _viewer()
    videos = visible_videos().all()
    now = datetime.utcnow()
    newest = sorted((v for v in videos if _is_new_this_month(v, now)),
                    key=lambda v: (v.publish_at, v.id), reverse=True)[:NEW_THIS_MONTH_LIMIT]
    from_teacher = sorted((v for v in videos if v.section == CORNER_SECTION),
                          key=lambda v: (v.publish_at or v.created_at or now, v.id), reverse=True)[:LATEST_FROM_TEACHER_LIMIT]
    return jsonify({
        "videos": [_card(v, viewer) for v in videos],
        "new_this_month": [v.slug for v in newest],
        "latest_from_teacher": [v.slug for v in from_teacher],
        "viewer_tier_rank": viewer.effective_tier_rank if viewer else 0,
    })


@tcc.route('/new-this-month', methods=['GET'])
@limiter.limit("60 per minute")
def get_new_this_month():
    viewer = _viewer()
    now = datetime.utcnow()
    newest = sorted((v for v in visible_videos().all() if _is_new_this_month(v, now)),
                    key=lambda v: (v.publish_at, v.id), reverse=True)[:NEW_THIS_MONTH_LIMIT]
    return jsonify([_card(v, viewer) for v in newest])


@tcc.route('/videos/<slug>', methods=['GET'])
@limiter.limit("60 per minute")
def get_video(slug):
    viewer = _viewer()
    video = visible_videos().filter(Video.slug == slug).first()
    if video is None:
        return jsonify({"msg": "We could not find that video."}), 404
    data = _card(video, viewer)
    data["long_description"] = video.long_description or ""
    data["chapters"] = video.chapters or []
    others = visible_videos().filter(Video.section == video.section, Video.id != video.id).all()
    data["up_next"] = [_card(v, viewer) for v in others]
    return jsonify(data)


# Route modules register on the same blueprint
from . import tcc_encoding, tcc_playback  # noqa: E402,F401
