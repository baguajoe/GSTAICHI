"""Member emails: welcome, plan changes, and "new video" announcements.

Every email has a designed HTML version and a plain-text version, and is logged in EmailLog (/admin > Emails).

New-video emails go out a little at a time from a small sender loop that runs inside the API itself (no separate
worker): every minute it sends up to EMAIL_BATCH_SIZE emails, never more than EMAIL_DAILY_LIMIT in any 24 hours
(counting every email the app sent, keeping EMAIL_RESERVE free for welcome and account emails). Whatever is left
waits for the next day automatically. A database lock makes sure only one copy of the loop sends at a time.
"""
import html
import os
import threading
import time
from datetime import datetime, timedelta
from itsdangerous import URLSafeSerializer, BadSignature
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from .models import (db, User, Video, Tier, SiteSettings, EmailLog, VideoAnnouncement, AnnouncementRecipient,
                     CORNER_SECTION)
from .send_email import send_email

DAILY_LIMIT = int(os.getenv("EMAIL_DAILY_LIMIT") or 400)
RESERVE = int(os.getenv("EMAIL_RESERVE") or 50)  # kept free for welcome, payment and cancellation emails
BATCH_SIZE = int(os.getenv("EMAIL_BATCH_SIZE") or 20)
TICK_SECONDS = int(os.getenv("EMAIL_TICK_SECONDS") or 60)
PAID_WELCOME_WAIT = timedelta(hours=2)  # signed up to pay: wait this long for PayPal before the free welcome
WELCOME_GIVE_UP = timedelta(days=3)
PAYPAL_PAYMENTS_URL = "https://www.paypal.com/myaccount/autopay/"
LOCK_KEY = 7243105  # Postgres advisory lock for the sender loop
# The mirror / slow-motion tip in the paid welcome appears only once those player tools are live
PLAYER_LEARNING_TOOLS_LIVE = False

KINDS = {
    "welcome_free": "Welcome (Free plan)",
    "welcome_paid": "Welcome (paid plan)",
    "upgrade": "Thank you for joining a plan",
    "cancelled": "Subscription cancelled",
    "payment_failed": "Payment problem",
    "new_video": "New video",
}


# ----- links -----

def _frontend():
    return (os.getenv("FRONTEND_URL") or "https://gstaichi.org").rstrip("/")


def _backend():
    return (os.getenv("BACKEND_URL") or "https://api.gstaichi.org").rstrip("/")


def app_url(path=""):
    return f"{_frontend()}/tai-chi-company{path}"


def _serializer():
    return URLSafeSerializer(os.environ.get("FLASK_APP_KEY", "sample key"), salt="email-unsubscribe")


def unsubscribe_token(user):
    return _serializer().dumps({"u": user.id, "p": "new_videos"})


def user_from_unsubscribe_token(token):
    try:
        data = _serializer().loads(token or "")
    except BadSignature:
        return None
    if not isinstance(data, dict) or data.get("p") != "new_videos":
        return None
    return db.session.get(User, data.get("u"))


def unsubscribe_url(user):
    return f"{_backend()}/api/tcc/email/unsubscribe?t={unsubscribe_token(user)}"


# ----- design -----

def render(heading, blocks, button=None, after_button=None, unsubscribe=None, preheader=""):
    """Builds (plain_text, html). blocks / after_button: ("p", text), ("ul", [texts]), ("h2", text),
    ("small", text), ("link", label, url), ("img", url, alt). button: (label, url). unsubscribe: url or None."""
    settings = SiteSettings.get()
    app_name = settings.app_name or "The Tai Chi Company"
    school = settings.school_name or "Gin Soon Tai Chi Chuan Federation"
    address = settings.address or "33 Harrison Ave, 5th Floor, Boston, MA"
    prefs = app_url("/account#emails")
    e = html.escape

    def html_blocks(items):
        out = []
        for b in items or []:
            if b[0] == "p":
                out.append(f'<p style="margin:0 0 18px;font-size:20px;line-height:1.6;color:#1a1a1a;">{e(b[1])}</p>')
            elif b[0] == "h2":
                out.append(f'<h2 style="margin:28px 0 12px;font-size:23px;line-height:1.3;color:#590d0d;">{e(b[1])}</h2>')
            elif b[0] == "small":
                out.append(f'<p style="margin:0 0 14px;font-size:17px;line-height:1.5;color:#444444;">{e(b[1])}</p>')
            elif b[0] == "ul":
                items_html = "".join(f'<li style="margin:0 0 8px;">{e(i)}</li>' for i in b[1])
                out.append(f'<ul style="margin:0 0 18px;padding-left:26px;font-size:20px;line-height:1.5;color:#1a1a1a;">{items_html}</ul>')
            elif b[0] == "link":
                out.append(f'<p style="margin:0 0 18px;font-size:20px;line-height:1.6;"><a href="{e(b[2])}" '
                           f'style="color:#590d0d;font-weight:bold;">{e(b[1])}</a></p>')
            elif b[0] == "img" and b[1]:
                out.append(f'<img src="{e(b[1])}" alt="{e(b[2])}" width="536" '
                           f'style="display:block;width:100%;max-width:536px;height:auto;border-radius:8px;margin:0 0 18px;">')
        return "".join(out)

    def text_blocks(items):
        out = []
        for b in items or []:
            if b[0] in ("p", "small"):
                out.append(b[1])
            elif b[0] == "h2":
                out.append(b[1].upper())
            elif b[0] == "ul":
                out.append("\n".join(f"  * {i}" for i in b[1]))
            elif b[0] == "link":
                out.append(f"{b[1]}: {b[2]}")
        return out

    button_html = ""
    if button:
        button_html = (
            '<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:8px 0 26px;"><tr>'
            f'<td bgcolor="#590d0d" style="border-radius:8px;"><a href="{e(button[1])}" '
            'style="display:inline-block;padding:18px 34px;font-size:22px;font-weight:bold;color:#ffffff;'
            f'text-decoration:none;border-radius:8px;font-family:Arial,Helvetica,sans-serif;">{e(button[0])}</a></td>'
            '</tr></table>')
    unsubscribe_html = (f'<br><a href="{e(unsubscribe)}" style="color:#590d0d;">Stop these emails</a> '
                        f'(new-video emails only)') if unsubscribe else ""
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(heading)}</title></head>
<body style="margin:0;padding:0;background:#f4efe9;">
<div style="display:none;max-height:0;overflow:hidden;">{e(preheader)}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#f4efe9;">
<tr><td align="center" style="padding:20px 10px;">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0"
 style="width:100%;max-width:600px;background:#ffffff;border-radius:10px;overflow:hidden;font-family:Arial,Helvetica,sans-serif;">
<tr><td bgcolor="#590d0d" style="background:#590d0d;padding:24px 32px;">
<span style="font-size:28px;font-weight:bold;color:#ffffff;font-family:Georgia,'Times New Roman',serif;">{e(app_name)}</span>
</td></tr>
<tr><td style="padding:32px 32px 12px;">
<h1 style="margin:0 0 20px;font-size:30px;line-height:1.25;color:#590d0d;">{e(heading)}</h1>
{html_blocks(blocks)}
{button_html}
{html_blocks(after_button)}
</td></tr>
<tr><td style="padding:20px 32px 28px;border-top:1px solid #e6dcd5;font-size:16px;line-height:1.6;color:#555555;">
{e(school)}<br>{e(address)}<br>
<a href="{e(prefs)}" style="color:#590d0d;">Manage your email preferences</a>{unsubscribe_html}
</td></tr>
</table></td></tr></table></body></html>"""

    lines = [app_name.upper(), "", heading, ""]
    lines += [part + "\n" for part in text_blocks(blocks)]
    if button:
        lines += [f"{button[0]}: {button[1]}", ""]
    lines += [part + "\n" for part in text_blocks(after_button)]
    lines += ["--", school, address, f"Manage your email preferences: {prefs}"]
    if unsubscribe:
        lines.append(f"Stop these emails (new-video emails only): {unsubscribe}")
    return "\n".join(lines).replace("\n\n\n", "\n\n"), page


# ----- sending and the log -----

def deliver(kind, to_email, subject, content, user=None, video=None, dedupe_key=None, is_test=False, headers=None):
    """Sends one email and logs it. Returns True if sent. With dedupe_key, the same email is never sent twice
    (a failed one may be tried again). Commits the session."""
    plain, page = content
    log = EmailLog(kind=kind, to_email=to_email, user_id=user.id if user else None, video_id=video.id if video else None,
                   subject=subject[:300], status="sending", is_test=is_test, dedupe_key=dedupe_key)
    db.session.add(log)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return False  # already sent
    try:
        send_email(recipient=to_email, subject=subject, body=plain, html=page, headers=headers)
        log.status = "sent"
    except Exception as e:
        log.status, log.error = "failed", str(e)[:500]
        log.dedupe_key = None  # let a later event try again
        print(f"Email {kind} to {to_email} failed: {log.error}")
    db.session.commit()
    return log.status == "sent"


def sent_last_24h(now=None):
    since = (now or datetime.utcnow()) - timedelta(hours=24)
    return EmailLog.query.filter(EmailLog.created_at >= since, EmailLog.status.in_(("sent", "sending"))).count()


# ----- content -----

def _first_name(user):
    return (user.name or "").strip().split(" ")[0] if user and user.name else ""


def _hello(user):
    name = _first_name(user)
    return f"Hello {name}," if name else "Hello,"


def _tier_name(rank):
    tier = Tier.query.filter_by(rank=rank).first()
    return tier.name if tier else f"Level {rank}"


def _first_lesson_url():
    from .taichi_company import visible_videos
    samples = visible_videos().filter(Video.is_free_sample.is_(True)).all()
    pick = next((v for v in samples if v.slug == "fundamentals"), None) or (samples[0] if samples else None)
    return app_url(f"/watch/{pick.slug}") if pick else app_url("/library")


def _unlocked(rank):
    """What a plan at this level includes, in words."""
    settings = SiteSettings.get()
    levels = [s.get("label") for s in (settings.video_sections or [])
              if s.get("key") != CORNER_SECTION and (s.get("tier_rank") or 1) <= rank]
    items = [f"{label} videos" for label in levels if label]
    teacher = settings.teacher_name or "Vincent"
    if settings.corner_name:
        items.append(f"{settings.corner_name}: short videos from {teacher}")
    items.append(f"Ask {teacher}: send {teacher} your questions")
    items.append("All the member articles")
    return items


def _install_blocks():
    return [
        ("h2", "Put the app on your phone or tablet"),
        ("ul", ["iPhone or iPad: open the website in Safari, tap the Share button, then \"Add to Home Screen\".",
                "Android: open it in Chrome, tap the three dots, then \"Install app\".",
                "Computer: click \"Install the app\" at the top of the page."]),
        ("link", "Step-by-step help with pictures", app_url("/add-to-phone")),
    ]


def _health_line():
    return ("small", f"Before you practice, please read our short health disclaimer: {app_url('/health')}")


def _plan_info(user):
    """(plan name, level rank) for the member's current plan."""
    rank = user.effective_tier_rank if not user.is_staff else max((t.rank for t in Tier.query.all()), default=1)
    name = user.current_plan.tier.name if user.current_plan and user.current_plan.tier else _tier_name(rank)
    return name, rank


def welcome_free(user):
    teacher = SiteSettings.get().teacher_name or "Vincent"
    blocks = [
        ("p", _hello(user)),
        ("p", f"I'm {teacher} Chu, and I'm so glad you're here. Tai Chi is learned slowly, one movement at a time, "
              "so be patient with yourself and enjoy the practice."),
        ("p", "On the Free plan you can already:"),
        ("ul", ["Watch the free sample lessons", "Read all the member articles"]),
    ]
    after = _install_blocks() + [
        ("h2", "Ready for more?"),
        ("p", "Upgrade anytime to unlock all lessons."),
        ("link", "See the plans", app_url("/join")),
        _health_line(),
        ("p", "See you in class,"), ("p", f"{teacher} Chu"),
    ]
    subject = "Welcome to The Tai Chi Company!"
    return subject, render(subject, blocks, ("Watch your first lesson", _first_lesson_url()), after,
                           preheader="Your first free lesson is waiting.")


def welcome_paid(user, plan_name=None, rank=None):
    settings = SiteSettings.get()
    teacher = settings.teacher_name or "Vincent"
    if plan_name is None:
        plan_name, rank = _plan_info(user)
    blocks = [
        ("p", _hello(user)),
        ("p", f"I'm {teacher} Chu, and I'm so glad you're here. Tai Chi is learned slowly, one movement at a time, "
              "so be patient with yourself and enjoy the practice."),
        ("p", f"Your {plan_name} plan unlocks:"),
        ("ul", _unlocked(rank)),
        ("p", "The best place to begin is the Beginner level, from the first lesson."),
    ]
    after = []
    if PLAYER_LEARNING_TOOLS_LIVE:
        after += [("h2", "A tip for practicing"),
                  ("p", "Press \"Mirror\" under the video to see me like in a mirror, so you can follow along "
                        "with the same side. Press \"Speed\" and choose 0.5x to watch a movement in slow motion.")]
    after += [
        ("h2", f"Ask {teacher}"),
        ("p", f"Have a question about a movement? Choose \"Ask {teacher}\" in the app menu, write your question, "
              "and if you like, choose the lesson and the time in the video. I read every question myself."),
    ] + _install_blocks() + [_health_line(), ("p", "See you in class,"), ("p", f"{teacher} Chu")]
    subject = "Welcome to The Tai Chi Company!"
    return subject, render(subject, blocks, ("Start with Beginner", app_url("/library")), after,
                           preheader=f"Your {plan_name} plan is ready.")


def upgrade_email(user, plan_name=None, rank=None):
    if plan_name is None:
        plan_name, rank = _plan_info(user)
    subject = f"Thank you for joining {plan_name}!"
    blocks = [("p", _hello(user)), ("p", "Your plan is active. Here is what is now unlocked:"), ("ul", _unlocked(rank))]
    return subject, render(subject, blocks, ("Start watching", app_url("/library")),
                           [_health_line()], preheader="Your new lessons are ready.")


def cancelled_email(user, until=None):
    until = until or (user.paid_through.strftime("%B %d, %Y").replace(" 0", " ") if user.paid_through
                      else "the end of the period you paid for")
    subject = "Your subscription is cancelled"
    blocks = [
        ("p", _hello(user)),
        ("p", f"Your subscription is cancelled. You keep access until {until}."),
        ("p", "You will not be charged again. Thank you for practicing with us. Your free account stays open, "
              "so you can still read the articles and watch the free lessons."),
    ]
    return subject, render(subject, blocks, ("Come back anytime", app_url("/account")),
                           [("small", "Did you not mean to cancel? Just reply to this email.")],
                           preheader=f"You keep access until {until}.")


def payment_failed_email(user):
    subject = "A problem with your payment"
    blocks = [
        ("p", _hello(user)),
        ("p", "There was a problem with your payment. Please update it in PayPal so you keep your lessons."),
        ("p", "This often happens when a card expires. PayPal will try again in a few days."),
    ]
    return subject, render(subject, blocks, ("Update my payment in PayPal", PAYPAL_PAYMENTS_URL),
                           [("small", "Need help? Just reply to this email.")],
                           preheader="Please update your payment in PayPal.")


def video_plan_label(video):
    if video.is_free_sample:
        return "Free lesson: every member can watch it"
    return f"Part of the {_tier_name(video.tier_rank)} plan"


def new_video_email(user, video):
    from .tcc_articles import media_url
    from .tcc_playback import can_watch
    subject = f"New video: {video.title}"
    blocks = [
        ("p", _hello(user)),
        ("p", "A new video has been added to the library."),
        ("img", media_url(video.custom_thumbnail_path or video.thumbnail_path), video.title),
        ("h2", video.title),
    ]
    if video.short_description:
        blocks.append(("p", video.short_description))
    blocks.append(("p", video_plan_label(video)))
    watch_url = app_url(f"/watch/{video.slug}")
    if can_watch(user, video):
        button = ("Watch now", watch_url)
        after = []
    else:
        button = ("Upgrade to watch", watch_url)
        after = [("small", "This video is part of a paid plan. Open it to see the plans, or upgrade on your Account page.")]
    unsubscribe = unsubscribe_url(user)
    headers = {"List-Unsubscribe": f"<{unsubscribe}>", "List-Unsubscribe-Post": "List-Unsubscribe=One-Click"}
    return subject, render(subject, blocks, button, after, unsubscribe=unsubscribe,
                           preheader=video.short_description or video.title), headers


# ----- what triggers them -----

def send_welcome(user, force_kind=None):
    """The welcome email, once per member: paid if they have a plan now, free otherwise."""
    if user.welcome_sent_at:
        return False
    paid = force_kind == "welcome_paid" or (force_kind is None and user.is_paying_member and not user.is_staff)
    subject, content = welcome_paid(user) if paid else welcome_free(user)
    sent = deliver("welcome_paid" if paid else "welcome_free", user.email, subject, content, user=user,
                   dedupe_key=f"welcome:{user.id}")
    if sent:
        user.welcome_sent_at, user.welcome_due_at = datetime.utcnow(), None
        db.session.commit()
    return sent


def plan_status_emails(user, before_status, before_rank, event_type=None):
    """Called after the member's subscription was updated (in the app or from a PayPal webhook). Sends at most
    one email per change; the dedupe keys stop a repeated PayPal event from sending it again. Never raises."""
    try:
        sub = user.paypal_subscription_id or "none"
        status = user.subscription_status
        if status == "active" and (before_status != "active" or (user.tier_rank or 0) > (before_rank or 0)):
            if user.welcome_sent_at is None and user.welcome_due_at is not None:
                send_welcome(user, force_kind="welcome_paid")  # a brand-new member: the paid welcome says it all
            else:
                subject, content = upgrade_email(user)
                deliver("upgrade", user.email, subject, content, user=user,
                        dedupe_key=f"upgrade:{sub}:{user.current_plan_id}")
        elif status == "cancelled" and before_status != "cancelled":
            subject, content = cancelled_email(user)
            deliver("cancelled", user.email, subject, content, user=user, dedupe_key=f"cancelled:{sub}")
        elif (status == "past_due" and before_status != "past_due") or \
                event_type in ("BILLING.SUBSCRIPTION.PAYMENT.FAILED", "BILLING.SUBSCRIPTION.SUSPENDED"):
            cycle = (user.paid_through or datetime.utcnow()).strftime("%Y-%m-%d")
            subject, content = payment_failed_email(user)
            deliver("payment_failed", user.email, subject, content, user=user,
                    dedupe_key=f"payment_failed:{sub}:{cycle}")
    except Exception as e:
        db.session.rollback()
        print(f"Plan email for user {user.id} failed: {e}")


# ----- new-video announcements -----

def announcement_for(video):
    return VideoAnnouncement.query.filter_by(video_id=video.id).first()


def announcement_summary(video):
    """For the Studio and /admin: the choice and how far the sending has got."""
    a = announcement_for(video)
    if a is None:
        return {"choice": video.announce_choice}
    c = a.counts()
    return {"choice": "yes", "status": a.status, "total": a.total, "sent": c["sent"], "failed": c["failed"],
            "waiting": c["pending"], "skipped": c["skipped"], "waiting_reason": waiting_reason(a, c)}


def recipients_query():
    return User.query.filter(User.email_new_videos.is_(True), User.is_suspended.is_(False))


def announce_video(video, starter=None):
    """"Yes": queues the email for every member with new-video emails turned on. Returns (announcement, error)."""
    if announcement_for(video):
        return None, "Members have already been emailed about this video."
    a = VideoAnnouncement(video_id=video.id, created_by=starter.id if starter else None, status="sending")
    db.session.add(a)
    db.session.flush()
    ids = [uid for (uid,) in recipients_query().with_entities(User.id).all()]
    db.session.bulk_insert_mappings(AnnouncementRecipient,
                                    [{"announcement_id": a.id, "user_id": uid, "status": "pending"} for uid in ids])
    a.total = len(ids)
    if not ids:
        a.status, a.finished_at = "done", datetime.utcnow()
    video.announce_choice = "yes"
    db.session.commit()
    kick()
    return a, None


def video_is_out(video, now=None):
    now = now or datetime.utcnow()
    return bool(video and video.slug and video.is_published and not video.is_coming_soon
                and (video.publish_at is None or video.publish_at <= now))


def waiting_reason(a, counts=None, now=None):
    counts = counts or a.counts()
    if a.status == "done" or not counts["pending"]:
        return None
    if not video_is_out(a.video, now):
        when = a.video.publish_at.strftime("%B %d at %H:%M UTC") if a.video and a.video.publish_at else "it is ready"
        return f"Waiting until the video appears for members ({when})."
    if DAILY_LIMIT - RESERVE - sent_last_24h(now) <= 0:
        return "Today's email limit is reached. Sending continues automatically within 24 hours."
    return "Sending a few at a time (about every minute)."


def _send_announcement_batch(now):
    budget = min(BATCH_SIZE, DAILY_LIMIT - RESERVE - sent_last_24h(now))
    sent_now = 0
    for a in VideoAnnouncement.query.filter_by(status="sending").order_by(VideoAnnouncement.id).all():
        if not video_is_out(a.video, now):
            continue
        while budget > 0:
            rows = (AnnouncementRecipient.query.filter_by(announcement_id=a.id, status="pending")
                    .order_by(AnnouncementRecipient.id).limit(min(budget, BATCH_SIZE)).all())
            if not rows:
                break
            for row in rows:
                user = row.user
                if user is None or user.is_suspended or not user.email_new_videos:
                    row.status = "skipped"  # turned the emails off (or the account closed) after the Yes
                    db.session.commit()
                    continue
                subject, content, headers = new_video_email(user, a.video)
                ok = deliver("new_video", user.email, subject, content, user=user, video=a.video, headers=headers,
                             dedupe_key=f"new_video:{a.id}:{user.id}")
                row.status, row.sent_at = ("sent" if ok else "failed"), datetime.utcnow()
                db.session.commit()
                budget -= 1
                sent_now += 1
                if budget <= 0:
                    break
        if not AnnouncementRecipient.query.filter_by(announcement_id=a.id, status="pending").count():
            a.status, a.finished_at = "done", datetime.utcnow()
            db.session.commit()
        if budget <= 0:
            break
    return sent_now


def _send_due_welcomes(now):
    due = User.query.filter(User.welcome_sent_at.is_(None), User.welcome_due_at.isnot(None),
                            User.welcome_due_at <= now).limit(BATCH_SIZE).all()
    for user in due:
        if now - user.welcome_due_at > WELCOME_GIVE_UP:
            user.welcome_due_at = None  # kept failing for days: stop trying
            db.session.commit()
        elif not send_welcome(user):
            user.welcome_due_at = now + timedelta(minutes=30)  # try again later
            db.session.commit()


_local_lock = threading.Lock()


def process_queue(now=None):
    """One round of the sender loop. Safe to call from several processes at once."""
    now = now or datetime.utcnow()
    if db.engine.dialect.name != "postgresql":
        with _local_lock:
            _send_due_welcomes(now)
            return _send_announcement_batch(now)
    with db.engine.connect() as lock_conn:
        if not lock_conn.execute(text("SELECT pg_try_advisory_lock(:k)"), {"k": LOCK_KEY}).scalar():
            return 0  # another copy of the API is sending right now
        try:
            _send_due_welcomes(now)
            return _send_announcement_batch(now)
        finally:
            lock_conn.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": LOCK_KEY})
            if hasattr(lock_conn, "commit"):
                lock_conn.commit()  # SQLAlchemy 2 style connections


# ----- the sender loop inside the API -----

_wake = threading.Event()
_started_pid = None


def kick():
    """Run the sender soon (after a sign-up or a "Yes")."""
    _wake.set()


def _loop(app):
    time.sleep(5)
    while True:
        with app.app_context():
            try:
                process_queue()
            except Exception as e:
                print(f"Email sender: {type(e).__name__}: {e}")
            finally:
                db.session.remove()
        _wake.wait(TICK_SECONDS)
        _wake.clear()


def start_email_sender(app):
    """Starts the loop in each API process on its first request (not during flask commands like setup-database).
    EMAIL_SENDER=off turns it off."""
    if (os.getenv("EMAIL_SENDER") or "on").lower() == "off":
        return

    @app.before_request
    def _start_sender_once():
        global _started_pid
        if _started_pid == os.getpid():
            return
        _started_pid = os.getpid()
        threading.Thread(target=_loop, args=(app,), daemon=True, name="email-sender").start()
