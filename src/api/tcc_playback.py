"""
Protected playback: /api/tcc/play, /key, /heartbeat, /stop and the Worker's usage reports.

How it fits together:
  1. POST /play/<slug> checks the member's plan and the 2-stream limit, creates a PlaybackSession and
     returns a signed URL for the Cloudflare Worker (media.<domain>) that serves the encrypted HLS files.
  2. The player fetches the AES key from GET /key/<slug>. The key is only given out for an active session
     that has sent a heartbeat in the last 60 seconds, to a member whose plan still allows the video.
     hls.js sends the sign-in token plus X-Playback-Session. Safari's built-in player (iPhone, iPad, Mac),
     AirPlay and Chromecast cannot add headers, so the Worker adds the signed ?t= token to the key address
     in the playlist and the same checks are made with it.
  3. The player sends POST /heartbeat/<session> every 20 seconds and POST /stop/<session> when done.
"""
import hmac
import json
import os
from datetime import datetime, timedelta
from flask import jsonify, request, Response
from .models import db, Video, PlaybackSession, SiteSettings
from .extensions import limiter
from .key_vault import decrypt_key, KeyVaultError
from .media_tokens import sign_media_token, verify_media_token, sign_report, MediaTokenError
from .security import log_event, count_events
from .tcc_auth import role_required, get_current_user
from .taichi_company import tcc, visible_videos

MAX_STREAMS = 2
HEARTBEAT_SECONDS = 20
HEARTBEAT_TIMEOUT = timedelta(seconds=60)
TOKEN_TTL_SECONDS = 6 * 60 * 60
SEGMENT_SECONDS = 6

# Anomaly thresholds (Phase 8 shows these in /admin)
FAST_DOWNLOAD_FACTOR = 3        # more than 3x real-time playback...
FAST_DOWNLOAD_ALLOWANCE = 20    # ...after the first 20 pieces (start-up buffering and quality switches)
KEY_FLOOD_COUNT = 40
KEY_FLOOD_WINDOW = timedelta(minutes=30)
MANY_IPS = 3
REPEATED_LIMIT_HITS = 5


def can_watch(user, video):
    if user is None or user.is_suspended:
        return False
    if video.is_free_sample:
        return True
    return user.effective_tier_rank >= video.tier_rank


def _client_ip():
    return request.remote_addr or ""


def _expire_stale_sessions(user_id):
    cutoff = datetime.utcnow() - HEARTBEAT_TIMEOUT
    for s in PlaybackSession.query.filter(PlaybackSession.user_id == user_id, PlaybackSession.is_active.is_(True),
                                          PlaybackSession.last_heartbeat_at < cutoff).all():
        s.end("timeout")


def _session_summary(s):
    return {"id": s.id, "device": s.device_label(), "video_title": s.video.title if s.video else "",
            "started_at": s.started_at.isoformat() if s.started_at else None}


def _check_many_ips(user):
    since = datetime.utcnow() - timedelta(hours=24)
    ips = {ip for (ip,) in db.session.query(PlaybackSession.ip)
           .filter(PlaybackSession.user_id == user.id, PlaybackSession.started_at >= since).distinct()}
    if len(ips) > MANY_IPS:
        log_event(user.id, "many_ips", {"ips": sorted(ips)}, dedupe_hours=24)


@tcc.route('/play/<slug>', methods=['POST'])
@limiter.limit("20 per minute")
@role_required()
def play(slug):
    user = get_current_user()
    # Teachers can also play videos members cannot see yet (to check chapters in the Studio)
    videos = Video.query.filter(Video.slug.isnot(None)) if user and user.is_staff else visible_videos()
    video = videos.filter(Video.slug == slug).first()
    if video is None:
        return jsonify({"msg": "We could not find that video."}), 404
    if not can_watch(user, video):
        return jsonify({"code": "upgrade", "msg": "Your plan does not include this video yet."}), 403
    if video.is_coming_soon or not video.encryption_key_enc:
        return jsonify({"code": "coming_soon", "msg": "This video is coming soon."}), 409

    data = request.get_json(silent=True) or {}
    _expire_stale_sessions(user.id)
    # The member chose "stop it there and watch here", or the player is restarting its own session
    for key in ("end_session_id", "replace_session_id"):
        if data.get(key):
            own = PlaybackSession.query.filter_by(id=data[key], user_id=user.id).first()
            if own:
                own.end("replaced")

    active = PlaybackSession.query.filter_by(user_id=user.id, is_active=True).order_by(PlaybackSession.started_at).all()
    if len(active) >= MAX_STREAMS:
        log_event(user.id, "stream_limit", {"video": slug, "ip": _client_ip()}, reviewed=True)
        if count_events(user.id, "stream_limit", 24) + 1 >= REPEATED_LIMIT_HITS:
            log_event(user.id, "repeated_stream_limit", {"hits_in_24h": count_events(user.id, "stream_limit", 24) + 1},
                      dedupe_hours=24)
        db.session.commit()
        return jsonify({
            "code": "stream_limit",
            "msg": f"Playing on another device. Your account can play on {MAX_STREAMS} devices at the same time.",
            "sessions": [_session_summary(s) for s in active],
        }), 409

    session = PlaybackSession(user_id=user.id, video_id=video.id, ip=_client_ip(),
                              user_agent=(request.headers.get("User-Agent") or "")[:500],
                              last_heartbeat_at=datetime.utcnow())
    db.session.add(session)
    db.session.flush()
    _check_many_ips(user)
    try:
        token = sign_media_token(slug, session.id, TOKEN_TTL_SECONDS)
    except MediaTokenError as e:
        db.session.rollback()
        print(f"Playback is not configured: {e}")
        return jsonify({"msg": "Video playback is not set up yet. Please try again later."}), 503
    db.session.commit()

    media_base = os.getenv("MEDIA_BASE_URL", "").rstrip("/")
    return jsonify({
        "session_id": session.id,
        "url": f"{media_base}/{video.hls_master_path}?t={token}",
        # None turns the watermark off (Admin > Site Settings > Video watermark)
        "watermark_text": f"{user.email}  ·  Member {user.id}" if SiteSettings.get().video_watermark else None,
        "licensed_to": user.name or user.email,
        "heartbeat_seconds": HEARTBEAT_SECONDS,
        "chapters": video.chapters or [],
        # Hook for future DRM (FairPlay/Widevine through EME). None means AES-128 HLS as today.
        "drm": None,
    })


def _session_for_key_request(slug):
    """Finds the playback session from either the hls.js headers or the signed ?t= token."""
    session_id = request.headers.get("X-Playback-Session")
    if not session_id:
        # Safari's player, AirPlay and Chromecast: the Worker put the signed token on the key address
        token_session = verify_media_token(request.args.get("t"), slug)
        return PlaybackSession.query.get(token_session) if token_session else None, None
    user = get_current_user()  # hls.js: 401 if the sign-in token is missing or expired
    if user is None:
        return None, user
    session = PlaybackSession.query.get(session_id)
    if session is None or session.user_id != user.id:
        return None, user
    return session, user


@tcc.route('/key/<slug>', methods=['GET'])
@limiter.limit("60 per minute")
def get_key(slug):
    session, _ = _session_for_key_request(slug)
    denied = None
    if session is None:
        denied = "no_session"
    elif not session.is_active:
        denied = "session_ended"
    elif session.video is None or session.video.slug != slug:
        denied = "wrong_video"
    elif datetime.utcnow() - (session.last_heartbeat_at or session.started_at) > HEARTBEAT_TIMEOUT:
        denied = "no_heartbeat"
    elif not can_watch(session.user, session.video):
        denied = "no_access"
    if denied:
        log_event(session.user_id if session else None, "key_denied",
                  {"video": slug, "reason": denied, "ip": _client_ip()}, reviewed=True)
        db.session.commit()
        return jsonify({"msg": "This video cannot be played right now. Please press Play again."}), 403

    now = datetime.utcnow()
    session.key_request_count = (session.key_request_count or 0) + 1
    session.last_key_at = now
    if session.key_request_count > KEY_FLOOD_COUNT and now - session.started_at < KEY_FLOOD_WINDOW and not session.flagged:
        session.flagged = True
        log_event(session.user_id, "key_flood", {"video": slug, "session": session.id,
                                                 "key_requests": session.key_request_count, "ip": _client_ip()})
    try:
        key = decrypt_key(session.video.encryption_key_enc)
    except KeyVaultError as e:
        db.session.commit()
        print(f"Video key problem for {slug}: {e}")
        return jsonify({"msg": "This video cannot be played right now."}), 500
    db.session.commit()
    response = Response(key, mimetype="application/octet-stream")
    response.headers["Cache-Control"] = "no-store, private"
    return response


def _own_session(session_id):
    user = get_current_user()
    return PlaybackSession.query.filter_by(id=session_id, user_id=user.id).first(), user


@tcc.route('/heartbeat/<session_id>', methods=['POST'])
@role_required()
def heartbeat(session_id):
    session, user = _own_session(session_id)
    if session is None:
        return jsonify({"msg": "Playback session not found."}), 404
    if not session.is_active:
        message = ("This video was started on another device, so it stopped here."
                   if session.end_reason == "replaced" else "Playback stopped. Please press Play again.")
        return jsonify({"code": "ended", "msg": message}), 410
    if not can_watch(user, session.video):
        session.end("access_lost")
        db.session.commit()
        return jsonify({"code": "access_lost", "msg": "Your plan no longer includes this video."}), 403
    data = request.get_json(silent=True) or {}
    session.last_heartbeat_at = datetime.utcnow()
    if isinstance(data.get("position"), (int, float)):
        session.position_seconds = int(data["position"])
    db.session.commit()
    return jsonify({"ok": True})


@tcc.route('/stop/<session_id>', methods=['POST'])
@role_required()
def stop(session_id):
    session, _ = _own_session(session_id)
    if session is None:
        return jsonify({"msg": "Playback session not found."}), 404
    session.end("stopped")
    db.session.commit()
    return jsonify({"ok": True})


@tcc.route('/media/report', methods=['POST'])
@limiter.exempt  # comes from Cloudflare's servers for every viewer, signed with MEDIA_TOKEN_SECRET
def media_report():
    """The Worker reports each video piece it serves, so copying faster than real time can be spotted."""
    body = request.get_data()
    try:
        expected = sign_report(body)
    except MediaTokenError:
        return jsonify({"msg": "not configured"}), 503
    if not hmac.compare_digest(request.headers.get("X-Report-Signature", ""), expected):
        return jsonify({"msg": "bad signature"}), 403
    try:
        data = json.loads(body)
        session = PlaybackSession.query.get(str(data["session"]))
        count = max(1, min(int(data.get("count", 1)), 100))
    except (ValueError, KeyError, TypeError):
        return jsonify({"msg": "bad report"}), 400
    if session is None:
        return jsonify({"ok": True})
    session.segment_count = (session.segment_count or 0) + count
    elapsed = (datetime.utcnow() - session.started_at).total_seconds()
    allowed = elapsed / SEGMENT_SECONDS * FAST_DOWNLOAD_FACTOR + FAST_DOWNLOAD_ALLOWANCE
    if session.segment_count > allowed and not session.flagged:
        session.flagged = True
        log_event(session.user_id, "fast_download", {
            "video": session.video.slug if session.video else None, "session": session.id,
            "pieces": session.segment_count, "seconds_since_start": int(elapsed),
            "ip": session.ip,
        })
    db.session.commit()
    return jsonify({"ok": True})
