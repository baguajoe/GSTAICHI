"""Tai Chi Company subscription app API, registered at /api/tcc."""
import os
from datetime import datetime
from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from .models import db, SiteSettings, Tier, Video
from .extensions import limiter
from .tcc_auth import role_required, get_current_user

tcc = Blueprint('tcc', __name__)

MIN_PASSWORD_LENGTH = 8
NEW_THIS_MONTH_LIMIT = 8


@tcc.route('/settings', methods=['GET'])
def get_settings():
    """Public branding and contact info. Every name, color, phone and address in the app comes from here."""
    return jsonify(SiteSettings.get().serialize_public())


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


def _visible_videos():
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


@tcc.route('/videos', methods=['GET'])
def get_videos():
    viewer = _viewer()
    videos = _visible_videos().all()
    now = datetime.utcnow()
    newest = sorted((v for v in videos if _is_new_this_month(v, now)),
                    key=lambda v: (v.publish_at, v.id), reverse=True)[:NEW_THIS_MONTH_LIMIT]
    return jsonify({
        "videos": [_card(v, viewer) for v in videos],
        "new_this_month": [v.slug for v in newest],
        "viewer_tier_rank": viewer.effective_tier_rank if viewer else 0,
    })


@tcc.route('/videos/<slug>', methods=['GET'])
def get_video(slug):
    viewer = _viewer()
    video = _visible_videos().filter(Video.slug == slug).first()
    if video is None:
        return jsonify({"msg": "We could not find that video."}), 404
    data = _card(video, viewer)
    data["long_description"] = video.long_description or ""
    others = _visible_videos().filter(Video.section == video.section, Video.id != video.id).all()
    data["up_next"] = [_card(v, viewer) for v in others]
    return jsonify(data)
