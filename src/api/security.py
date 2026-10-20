"""Security events shown to admins in /admin (Security Events). Unreviewed events are the ones to look at."""
from datetime import datetime, timedelta
from .models import db, SecurityEvent, PlaybackSession

# Plain-English descriptions shown in the admin and the dashboard
EVENT_LABELS = {
    "fast_download": "Video pieces downloaded much faster than anyone can watch (possible copying)",
    "key_flood": "Video key requested many times in a short time (possible copying)",
    "many_ips": "Account used from more than 3 internet addresses in 24 hours (possible account sharing)",
    "stream_limit": "Tried to watch on a third device at the same time",
    "repeated_stream_limit": "Hit the two-device limit many times in 24 hours (possible account sharing)",
    "key_denied": "Video key refused",
    "suspended": "Account suspended by an administrator",
    "unsuspended": "Account unsuspended by an administrator",
}

# Logged for the record only; these never flag an account on the dashboard
NOT_FLAGGED = ("stream_limit", "key_denied", "suspended", "unsuspended")


def log_event(user_id, event_type, details=None, dedupe_hours=None, reviewed=False):
    """Record an event. With dedupe_hours, skip it if the same event was logged for this user recently."""
    if dedupe_hours and user_id:
        since = datetime.utcnow() - timedelta(hours=dedupe_hours)
        exists = SecurityEvent.query.filter(SecurityEvent.user_id == user_id, SecurityEvent.type == event_type,
                                            SecurityEvent.created_at >= since).first()
        if exists:
            return None
    event = SecurityEvent(user_id=user_id, type=event_type, details=details or {}, is_reviewed=reviewed)
    db.session.add(event)
    return event


def count_events(user_id, event_type, hours):
    since = datetime.utcnow() - timedelta(hours=hours)
    return SecurityEvent.query.filter(SecurityEvent.user_id == user_id, SecurityEvent.type == event_type,
                                      SecurityEvent.created_at >= since).count()


def suspend_user(user, reason, admin=None):
    """Blocks the account everywhere (sign in, API, video keys) and stops anything playing now."""
    user.is_suspended = True
    user.suspended_reason = (reason or "").strip()[:300] or None
    for session in PlaybackSession.query.filter_by(user_id=user.id, is_active=True).all():
        session.end("suspended")
    log_event(user.id, "suspended", {"reason": user.suspended_reason, "by": admin.email if admin else None}, reviewed=True)
    # Everything flagged so far has now been dealt with
    SecurityEvent.query.filter_by(user_id=user.id, is_reviewed=False).update({"is_reviewed": True})


def unsuspend_user(user, admin=None):
    user.is_suspended = False
    user.suspended_reason = None
    log_event(user.id, "unsuspended", {"by": admin.email if admin else None}, reviewed=True)
