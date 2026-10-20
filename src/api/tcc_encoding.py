"""Admin-only endpoints used by tools/encode_and_upload.py to record finished encodes."""
import os
import re
from datetime import datetime
from flask import jsonify, request
from sqlalchemy import func
from .models import db, Video, SiteSettings, Tier
from .key_vault import encrypt_key
from .tcc_auth import role_required, get_current_user
from .taichi_company import tcc

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,118}$")
HEX32_RE = re.compile(r"^[0-9a-f]{32}$")


def key_uri_base():
    """Where players fetch video keys. Baked into every playlist, so it must be the live API address."""
    base = (os.getenv("BACKEND_URL") or request.host_url).rstrip("/")
    return f"{base}/api/tcc/key/"


def _bad(msg):
    return jsonify({"msg": msg}), 400


@tcc.route('/admin/videos/status', methods=['GET'])
@role_required("admin")
def admin_videos_status():
    videos = Video.query.filter(Video.slug.isnot(None)).order_by(Video.sort_order, Video.id).all()
    return jsonify({
        "key_uri_base": key_uri_base(),
        "videos": [{"slug": v.slug, "title": v.title, "status": v.status,
                    "ready": bool(v.hls_master_path) and v.status == "ready"} for v in videos],
    })


@tcc.route('/admin/videos/import', methods=['POST'])
@role_required("admin")
def admin_videos_import():
    data = request.get_json(silent=True) or {}
    slug = (data.get("slug") or "").strip()
    if not SLUG_RE.match(slug):
        return _bad("slug must be lowercase letters, numbers and dashes.")
    key_hex = (data.get("key_hex") or "").lower()
    if not HEX32_RE.match(key_hex):
        return _bad("key_hex must be 32 hex characters.")
    if data.get("hls_master_path") != f"{slug}/master.m3u8":
        return _bad("hls_master_path must be <slug>/master.m3u8.")
    paths = [data.get("thumbnail_path"), data.get("chapters_vtt_path")]
    for option in data.get("thumbnail_options") or []:
        paths += [option.get("large"), option.get("small")]
    if any(p and not str(p).startswith(f"{slug}/") for p in paths):
        return _bad("All file paths must be inside the video's own folder.")

    settings = SiteSettings.get()
    sections = {s["key"]: s for s in settings.video_sections or []}
    video = Video.query.filter_by(slug=slug).first()
    if video is None:
        title = (data.get("title") or "").strip()
        section = data.get("section")
        if not title or section not in sections:
            return _bad(f"New video '{slug}' needs a title and a section ({', '.join(sections)}).")
        max_order = db.session.query(func.max(Video.sort_order)).scalar() or 0
        video = Video(slug=slug, title=title, section=section, is_published=True,
                      publish_at=datetime.utcnow(), sort_order=max_order + 1,
                      tier_rank=sections[section].get("tier_rank", 1),
                      uploaded_by=get_current_user().id)
        db.session.add(video)
    else:
        if data.get("title"):
            video.title = data["title"].strip()
        if data.get("section"):
            if data["section"] not in sections:
                return _bad(f"Unknown section '{data['section']}'.")
            video.section = data["section"]
    if data.get("tier_rank") not in (None, ""):
        ranks = {t.rank for t in Tier.query.all()}
        if int(data["tier_rank"]) not in ranks:
            return _bad(f"tier_rank must be one of {sorted(ranks)}.")
        video.tier_rank = int(data["tier_rank"])

    video.hls_master_path = data["hls_master_path"]
    video.thumbnail_options = data.get("thumbnail_options") or []
    video.thumbnail_path = data.get("thumbnail_path")
    video.chapters_vtt_path = data.get("chapters_vtt_path")
    video.duration_seconds = data.get("duration_seconds")
    video.width = data.get("width")
    video.height = data.get("height")
    video.renditions = data.get("renditions")
    video.encryption_key_enc = encrypt_key(bytes.fromhex(key_hex))
    video.status = "ready"
    video.failure_reason = None
    db.session.commit()
    return jsonify({"msg": f"{video.title} is ready.", "video": video.serialize_card()}), 200
