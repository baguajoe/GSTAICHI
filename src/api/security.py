"""Security events shown to admins in /admin (Security Events). Unreviewed events are the ones to look at."""
from datetime import datetime, timedelta
from .models import db, SecurityEvent

# Plain-English descriptions shown in the admin and the dashboard
EVENT_LABELS = {
    "fast_download": "Video pieces downloaded much faster than anyone can watch (possible copying)",
    "key_flood": "Video key requested many times in a short time (possible copying)",
    "many_ips": "Account used from more than 3 internet addresses in 24 hours (possible account sharing)",
    "stream_limit": "Tried to watch on a third device at the same time",
    "repeated_stream_limit": "Hit the two-device limit many times in 24 hours (possible account sharing)",
    "key_denied": "Video key refused",
}


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
