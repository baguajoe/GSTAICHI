"""
"Accounts to check": the rules that flag possible copying or account sharing, in one place.

The rules only ever record events for an admin to look at. Nothing here suspends anyone: suspension is always
a manual admin choice (the Suspend buttons in /admin).

1. sustained_fast_download: video pieces fetched well above playback speed for a whole 10-minute window.
   The player's normal buffer-ahead is ignored: the first 90 seconds of a session, plus 90 seconds of video
   after every seek (seeks come from the position the player reports in its heartbeats).
2. bulk_download: one account fetched several different videos start to finish, each far faster than real time,
   within a short time.
3. shared_streams: two or more sessions playing at the same time on the same account from different devices.
   Internet addresses are not counted (phones change address between Wi-Fi and mobile data).
   Also kept from before: key_flood (video key asked for over and over) and repeated_stream_limit.

An account is listed only when one rule fired on at least MIN_DAYS different days within LOOKBACK_DAYS.
"""
import math
from collections import defaultdict
from datetime import datetime, timedelta
from .models import db, User, Video, PlaybackSession, SecurityEvent
from .security import EVENT_LABELS, log_event

SEGMENT_SECONDS = 6
SPEED_FACTOR = 3                       # "well above playback speed": more than 3x real time
WARMUP = timedelta(seconds=90)         # start-up buffering is never counted
BUFFER_PIECES = 15                     # 90 seconds of video: what the player loads ahead after each seek
RATE_WINDOW = timedelta(minutes=10)    # speed must stay high for a whole window
FULL_FETCH_SHARE = 0.9                 # "start to finish": at least 90% of the video's pieces
BULK_VIDEOS = 3                        # different videos fetched start to finish...
BULK_WINDOW = timedelta(minutes=30)    # ...within this time
SEEK_SLACK_SECONDS = 10
MAX_PLAYBACK_RATE = 2.5                # the player's fastest speed setting, with room to spare

MIN_DAYS = 2
LOOKBACK_DAYS = 30

# Rules that can put an account on the list (their events, on MIN_DAYS different days)
FLAG_RULES = ("sustained_fast_download", "bulk_download", "shared_streams", "key_flood", "repeated_stream_limit")
# Rules used before 2026-11-12 (too strict). Kept so old events still read properly; they never list an account.
OLD_RULES = ("fast_download", "many_ips")


# ----- live checks (called from tcc_playback) -----

def note_heartbeat(session, position, now):
    """Counts a seek when the reported position jumps (back, or forward faster than any playback speed)."""
    previous, last = session.position_seconds, session.last_heartbeat_at
    if previous is None or last is None:
        return
    elapsed = max(0.0, (now - last).total_seconds())
    if position < previous - 5 or position > previous + elapsed * MAX_PLAYBACK_RATE + SEEK_SLACK_SECONDS:
        session.window_seeks = (session.window_seeks or 0) + 1


def window_allowance(window_seconds, seeks):
    return SPEED_FACTOR * window_seconds / SEGMENT_SECONDS + BUFFER_PIECES * (1 + (seeks or 0))


def video_pieces(video):
    return math.ceil(video.duration_seconds / SEGMENT_SECONDS) if video and video.duration_seconds else None


def note_pieces(session, count, now, device=None):
    """The Worker served `count` more pieces for this session. Runs the download-speed rules."""
    session.segment_count = (session.segment_count or 0) + count
    since_start = now - session.started_at
    if since_start >= WARMUP:
        if session.window_started_at is None:
            session.window_started_at, session.window_pieces = now, 0
        session.window_pieces = (session.window_pieces or 0) + count
        window = now - session.window_started_at
        if window >= RATE_WINDOW:
            seconds = window.total_seconds()
            if session.window_pieces > window_allowance(seconds, session.window_seeks):
                session.fast_windows = (session.fast_windows or 0) + 1
                if session.fast_windows == 1:  # once per session is enough to show the pattern
                    log_event(session.user_id, "sustained_fast_download", {
                        "video": session.video.slug if session.video else None,
                        "video_title": session.video.title if session.video else None,
                        "session": session.id, "pieces": session.window_pieces, "seconds": int(seconds),
                        "speed": round(session.window_pieces * SEGMENT_SECONDS / seconds, 1),
                        "seeks": session.window_seeks or 0, "ip": session.ip, "device": device,
                    })
            session.window_started_at, session.window_pieces, session.window_seeks = now, 0, 0

    total = video_pieces(session.video)
    if total and session.fetched_all_at is None and session.segment_count >= total * FULL_FETCH_SHARE \
            and since_start.total_seconds() < session.video.duration_seconds / SPEED_FACTOR:
        session.fetched_all_at = now
        _check_bulk(session, now)


def _check_bulk(session, now):
    recent = (PlaybackSession.query
              .filter(PlaybackSession.user_id == session.user_id, PlaybackSession.fetched_all_at >= now - BULK_WINDOW)
              .all())
    videos = {s.video_id: s for s in recent}
    videos[session.video_id] = session
    if len(videos) >= BULK_VIDEOS:
        log_event(session.user_id, "bulk_download", {
            "videos": sorted(s.video.title for s in videos.values() if s.video),
            "minutes": BULK_WINDOW.seconds // 60, "ips": sorted({s.ip for s in videos.values() if s.ip}),
            "devices": sorted({s.device_label() for s in videos.values()}),
        }, dedupe_hours=6)


def check_shared_streams(user, new_session):
    """After a new session starts: is another device playing on this account right now?"""
    others = [s for s in PlaybackSession.query.filter_by(user_id=user.id, is_active=True).all()
              if s.id != new_session.id and (s.user_agent or "") != (new_session.user_agent or "")]
    if not others:
        return
    sessions = [new_session] + others
    log_event(user.id, "shared_streams", {
        "sessions": [{"video_title": s.video.title if s.video else None, "device": s.device_label(), "ip": s.ip,
                      "started_at": s.started_at.isoformat() if s.started_at else None} for s in sessions],
    }, dedupe_hours=12)


# ----- the list on the dashboard -----

def _days_by_rule(events):
    days = defaultdict(set)
    for e in events:
        days[e.type].add(e.created_at.date())
    return days


def flagged_accounts(now=None, limit=25):
    """Accounts where one rule fired (and nobody has marked it checked) on MIN_DAYS or more different days."""
    now = now or datetime.utcnow()
    events = (SecurityEvent.query
              .filter(SecurityEvent.is_reviewed.is_(False), SecurityEvent.user_id.isnot(None),
                      SecurityEvent.type.in_(FLAG_RULES),
                      SecurityEvent.created_at >= now - timedelta(days=LOOKBACK_DAYS))
              .order_by(SecurityEvent.created_at).all())
    by_user = defaultdict(list)
    for e in events:
        by_user[e.user_id].append(e)
    result = []
    for user_id, user_events in by_user.items():
        days = _days_by_rule(user_events)
        firing = {rule: d for rule, d in days.items() if len(d) >= MIN_DAYS}
        if not firing:
            continue
        user = db.session.get(User, user_id)
        if user is None:
            continue
        result.append({"id": user.id, "email": user.email, "name": user.name, "count": len(user_events),
                       "last": user_events[-1].created_at, "is_suspended": user.is_suspended,
                       "reasons": [f"{EVENT_LABELS.get(rule, rule)}: on {len(d)} days" for rule, d in sorted(firing.items())]})
    result.sort(key=lambda r: (-r["count"], -r["last"].timestamp()))
    return result[:limit]


# ----- plain English for the "See events" page -----

def _when(dt):
    return dt.strftime("%a %b %d, %Y at %H:%M UTC") if dt else "an unknown time"


def _from(ip=None, device=None):
    parts = [p for p in (device, f"internet address {ip}" if ip else None) if p]
    return f" from {' at '.join(parts)}" if parts else ""


def _minutes(seconds):
    minutes = round((seconds or 0) / 60)
    return f"{minutes} minute{'s' if minutes != 1 else ''}"


def describe_event(event):
    """One plain-English sentence for an admin."""
    d = event.details or {}
    when = _when(event.created_at)
    t = event.type
    if t == "sustained_fast_download":
        video_minutes = (d.get("pieces") or 0) * SEGMENT_SECONDS / 60
        seeks = d.get("seeks") or 0
        return (f"{when}: “{d.get('video_title') or d.get('video') or 'a video'}” — fetched about "
                f"{video_minutes:.0f} minutes of video in {_minutes(d.get('seconds'))}, about {d.get('speed')}× "
                f"normal playing speed{f' (with {seeks} seeks allowed for)' if seeks else ''}"
                f"{_from(d.get('ip'), d.get('device'))}.")
    if t == "bulk_download":
        videos = d.get("videos") or []
        return (f"{when}: fetched {len(videos)} whole videos within {d.get('minutes', 30)} minutes, each far faster "
                f"than it can be watched: {', '.join('“' + v + '”' for v in videos)}"
                f"{_from(', '.join(d.get('ips') or []) or None, ', '.join(d.get('devices') or []) or None)}.")
    if t == "shared_streams":
        parts = [f"“{s.get('video_title') or 'a video'}” on {s.get('device') or 'a device'}"
                 f"{' (internet address ' + s['ip'] + ')' if s.get('ip') else ''}" for s in d.get("sessions", [])]
        return f"{when}: playing on {len(parts)} devices at the same time: " + "; ".join(parts) + "."
    if t == "key_flood":
        return (f"{when}: “{d.get('video')}” — the video key was asked for {d.get('key_requests')} times within "
                f"30 minutes{_from(d.get('ip'))}.")
    if t == "repeated_stream_limit":
        return f"{when}: tried to start a third device {d.get('hits_in_24h')} times in 24 hours."
    if t == "stream_limit":
        return f"{when}: tried to play “{d.get('video')}” on a third device{_from(d.get('ip'))} (refused)."
    if t == "fast_download":
        return (f"{when}: (old rule) “{d.get('video')}” — {d.get('pieces')} pieces "
                f"{d.get('seconds_since_start')} seconds after starting{_from(d.get('ip'))}.")
    if t == "many_ips":
        return f"{when}: (old rule) used from {len(d.get('ips') or [])} internet addresses in 24 hours."
    if t in ("suspended", "unsuspended"):
        reason = f" Reason: {d['reason']}" if d.get("reason") else ""
        return f"{when}: {EVENT_LABELS.get(t, t)} by {d.get('by') or 'an administrator'}.{reason}"
    return f"{when}: {EVENT_LABELS.get(t, t)}."


def account_summary(user, now=None, days=60):
    """Everything the "See events" page shows for one member."""
    now = now or datetime.utcnow()
    since = now - timedelta(days=days)
    events = (SecurityEvent.query.filter(SecurityEvent.user_id == user.id, SecurityEvent.created_at >= since)
              .order_by(SecurityEvent.created_at.desc()).all())
    flag_events = [e for e in events if e.type in FLAG_RULES and not e.is_reviewed]
    rules = [{"label": EVENT_LABELS.get(rule, rule), "days": sorted(d, reverse=True), "listed": len(d) >= MIN_DAYS}
             for rule, d in sorted(_days_by_rule(flag_events).items())]
    sessions = (PlaybackSession.query.filter(PlaybackSession.user_id == user.id, PlaybackSession.started_at >= since)
                .order_by(PlaybackSession.started_at.desc()).limit(40).all())
    return {
        "rules": rules,
        "events": [{"text": describe_event(e), "type": e.type, "reviewed": e.is_reviewed,
                    "flag": e.type in FLAG_RULES} for e in events],
        "sessions": [session_row(s) for s in sessions],
        "days": days,
    }


def session_row(s):
    end = s.ended_at or s.last_heartbeat_at or s.started_at
    seconds = max(0, (end - s.started_at).total_seconds()) if end and s.started_at else 0
    video_minutes = (s.segment_count or 0) * SEGMENT_SECONDS / 60
    speed = round(video_minutes * 60 / seconds, 1) if seconds >= 60 else None
    return {"started": _when(s.started_at), "video": s.video.title if s.video else "(deleted video)",
            "device": s.device_label(), "ip": s.ip or "", "length": _minutes(seconds),
            "fetched": f"{video_minutes:.0f} min of video", "speed": f"{speed}×" if speed is not None else "—",
            "fast": bool(s.fast_windows) or s.fetched_all_at is not None}


# ----- replay: what the new rules would have flagged from existing logs -----

def replay(now=None, days=LOOKBACK_DAYS):
    """Runs the new rules over the playback history (and the key/stream-limit events, whose rules are unchanged).
    Old sessions have no per-window or seek records, so speed is judged over each whole session (after the first
    90 seconds) with the same allowance as one seek: an approximation that errs towards flagging.
    Returns rows for every account listed by the old rules or the new ones."""
    now = now or datetime.utcnow()
    since = now - timedelta(days=days)
    hits = defaultdict(lambda: defaultdict(set))   # user_id -> rule -> {dates}
    examples = defaultdict(list)

    sessions = (PlaybackSession.query.filter(PlaybackSession.started_at >= since)
                .order_by(PlaybackSession.user_id, PlaybackSession.started_at).all())
    videos = {v.id: v for v in Video.query.filter(Video.id.in_({s.video_id for s in sessions})).all()} if sessions else {}
    by_user = defaultdict(list)
    for s in sessions:
        by_user[s.user_id].append(s)

    for user_id, user_sessions in by_user.items():
        full = []
        for s in user_sessions:
            end = s.ended_at or s.last_heartbeat_at or s.started_at
            seconds = (end - s.started_at).total_seconds() if end and s.started_at else 0
            counted = seconds - WARMUP.total_seconds()
            pieces = (s.segment_count or 0) - 2 * BUFFER_PIECES  # start-up buffer + one seek
            if counted >= RATE_WINDOW.total_seconds() and pieces > SPEED_FACTOR * counted / SEGMENT_SECONDS:
                hits[user_id]["sustained_fast_download"].add(s.started_at.date())
                examples[user_id].append(f"{_when(s.started_at)}: “{videos[s.video_id].title if s.video_id in videos else '?'}” "
                                         f"{(s.segment_count or 0) * SEGMENT_SECONDS / 60:.0f} min of video in {_minutes(seconds)}")
            video = videos.get(s.video_id)
            total = video_pieces(video)
            if total and (s.segment_count or 0) >= total * FULL_FETCH_SHARE and seconds < video.duration_seconds / SPEED_FACTOR:
                full.append((end, s.video_id))
        for i, (end, _video) in enumerate(full):
            in_window = {v for (t, v) in full[i:] if abs(t - end) <= BULK_WINDOW}
            if len(in_window) >= BULK_VIDEOS:
                hits[user_id]["bulk_download"].add(end.date())
                examples[user_id].append(f"{_when(end)}: {len(in_window)} whole videos within {_minutes(BULK_WINDOW.total_seconds())}")
        for i, a in enumerate(user_sessions):
            a_end = a.ended_at or a.last_heartbeat_at or a.started_at
            for b in user_sessions[i + 1:]:
                if b.started_at >= a_end:
                    break
                if (a.user_agent or "") != (b.user_agent or ""):
                    hits[user_id]["shared_streams"].add(b.started_at.date())
                    examples[user_id].append(f"{_when(b.started_at)}: {a.device_label()} and {b.device_label()} at the same time")

    old_listed = defaultdict(set)
    for e in SecurityEvent.query.filter(SecurityEvent.created_at >= since, SecurityEvent.user_id.isnot(None)).all():
        if e.type in ("key_flood", "repeated_stream_limit"):
            hits[e.user_id][e.type].add(e.created_at.date())
        if e.type in OLD_RULES + ("key_flood", "repeated_stream_limit"):
            old_listed[e.user_id].add(e.type)

    rows = []
    for user_id in set(hits) | set(old_listed):
        firing = {rule: d for rule, d in hits[user_id].items() if len(d) >= MIN_DAYS}
        once = {rule: d for rule, d in hits[user_id].items() if len(d) < MIN_DAYS}
        if not firing and user_id not in old_listed:
            continue
        user = db.session.get(User, user_id)
        if user is None:
            continue
        rows.append({
            "id": user.id, "email": user.email, "name": user.name, "is_suspended": user.is_suspended,
            "old": sorted(EVENT_LABELS.get(t, t) for t in old_listed.get(user_id, ())),
            "new": [f"{EVENT_LABELS.get(r, r)}: on {len(d)} days" for r, d in sorted(firing.items())],
            "below": [f"{EVENT_LABELS.get(r, r)}: on {len(d)} day" for r, d in sorted(once.items())],
            "examples": examples[user_id][:6],
        })
    rows.sort(key=lambda r: (not r["new"], r["email"]))
    return {"rows": rows, "days": days, "sessions": len(sessions),
            "would_list": sum(1 for r in rows if r["new"]), "old_listed": sum(1 for r in rows if r["old"])}


def clear_flags():
    """Marks every unchecked flag as checked (old and new rules). Returns how many."""
    count = (SecurityEvent.query.filter(SecurityEvent.is_reviewed.is_(False),
                                        SecurityEvent.type.in_(FLAG_RULES + OLD_RULES))
             .update({"is_reviewed": True}, synchronize_session=False))
    db.session.commit()
    return count
