"""Numbers for the admin dashboard (/admin). Read-only."""
from collections import Counter
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import func
from .models import db, User, Tier, Video, Article, PlaybackSession, EncodingJob, Question, SecurityEvent
from .security import EVENT_LABELS, NOT_FLAGGED

TOP = 10


def _month_start(now):
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def subscribers_by_tier():
    """Paying members (not teachers/admins) by tier, plus members with access granted by an admin."""
    tiers = Tier.query.order_by(Tier.rank).all()
    paid, granted = Counter(), Counter()
    revenue = Decimal("0")
    members = (User.query.filter(User.role == "member")
               .filter((User.tier_rank >= 1) | (User.granted_tier_rank >= 1)).all())
    for user in members:
        if user.tier_rank >= 1 and user.has_active_access:
            paid[user.tier_rank] += 1
            # cancelled members still have access but will not pay again
            if user.subscription_status in ("active", "past_due") and user.current_plan:
                price = Decimal(str(user.current_plan.price))
                revenue += price if user.current_plan.interval == "month" else price / 12
        elif user.granted_rank >= 1:
            granted[user.granted_rank] += 1
    rows = [{"tier": t.name, "paid": paid[t.rank], "granted": granted[t.rank]} for t in tiers]
    return rows, sum(paid.values()), sum(granted.values()), revenue.quantize(Decimal("0.01"))


def most_watched(since):
    rows = (db.session.query(PlaybackSession.video_id, func.count(PlaybackSession.id),
                             func.count(func.distinct(PlaybackSession.user_id)))
            .filter(PlaybackSession.started_at >= since)
            .group_by(PlaybackSession.video_id)
            .order_by(func.count(PlaybackSession.id).desc()).limit(TOP).all())
    videos = {v.id: v for v in Video.query.filter(Video.id.in_([r[0] for r in rows])).all()} if rows else {}
    return [{"title": videos[r[0]].title if r[0] in videos else "(deleted)", "plays": r[1], "members": r[2]}
            for r in rows]


def flagged_accounts():
    """Accounts with security events nobody has reviewed yet, most events first."""
    rows = (db.session.query(SecurityEvent.user_id, func.count(SecurityEvent.id), func.max(SecurityEvent.created_at))
            .filter(SecurityEvent.is_reviewed.is_(False), SecurityEvent.user_id.isnot(None),
                    SecurityEvent.type.notin_(NOT_FLAGGED))
            .group_by(SecurityEvent.user_id)
            .order_by(func.count(SecurityEvent.id).desc()).limit(25).all())
    users = {u.id: u for u in User.query.filter(User.id.in_([r[0] for r in rows])).all()} if rows else {}
    result = []
    for user_id, count, last in rows:
        user = users.get(user_id)
        if user is None:
            continue
        types = [t for (t,) in db.session.query(SecurityEvent.type).filter(
            SecurityEvent.user_id == user_id, SecurityEvent.is_reviewed.is_(False),
            SecurityEvent.type.notin_(NOT_FLAGGED)).distinct()]
        result.append({"id": user.id, "email": user.email, "name": user.name, "count": count, "last": last,
                       "reasons": [EVENT_LABELS.get(t, t) for t in types], "is_suspended": user.is_suspended})
    return result


def dashboard_stats(now=None):
    now = now or datetime.utcnow()
    month = _month_start(now)
    tiers, paid_total, granted_total, revenue = subscribers_by_tier()
    failed_videos = Video.query.filter_by(status="failed").order_by(Video.updated_at.desc()).all()
    open_questions = Question.query.filter_by(status="new").order_by(Question.created_at).all()
    return {
        "month_name": now.strftime("%B %Y"),
        "tiers": tiers,
        "paid_total": paid_total,
        "granted_total": granted_total,
        "monthly_revenue": revenue,
        "signups": User.query.filter(User.role == "member", User.created_at >= month).count(),
        "new_subscribers": User.query.filter(User.role == "member", User.subscribed_at >= month).count(),
        "cancellations": User.query.filter(User.role == "member", User.cancelled_at >= month).count(),
        "most_watched": most_watched(now - timedelta(days=30)),
        "most_read": [{"title": a.title, "reads": a.read_count or 0} for a in
                      Article.query.filter(Article.members_only.is_(True), Article.read_count > 0)
                      .order_by(Article.read_count.desc()).limit(TOP).all()],
        "open_questions": len(open_questions),
        "oldest_questions": [{"asked": q.created_at, "member": q.user.email if q.user else "", "text": q.question[:160]}
                             for q in open_questions[:5]],
        "failed_videos": [{"id": v.id, "title": v.title, "reason": v.failure_reason} for v in failed_videos],
        "failed_jobs_30d": EncodingJob.query.filter(EncodingJob.status == "failed",
                                                    EncodingJob.created_at >= now - timedelta(days=30)).count(),
        "waiting_jobs": EncodingJob.query.filter(EncodingJob.status.in_(("queued", "running"))).count(),
        "flagged": flagged_accounts(),
        "suspended": User.query.filter_by(is_suspended=True).count(),
    }
