import os
import secrets
from datetime import datetime
from flask import request, redirect, url_for, session, render_template_string, abort, flash
from flask_admin import Admin, AdminIndexView, expose, BaseView
from flask_admin.actions import action
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import SecureForm
from markupsafe import Markup
from werkzeug.security import check_password_hash
from wtforms import SelectField
from wtforms.validators import ValidationError
from sqlalchemy import func
from .models import (db, User, Class, Book, Video, Article, SiteSettings, Tier, Plan, Question,
                     EncodingJob, PlaybackSession, SecurityEvent, WebhookEvent, CORNER_SECTION)
from .extensions import limiter
from .security import EVENT_LABELS, suspend_user, unsuspend_user
from .tcc_dashboard import dashboard_stats

# Only users with role "admin" can use /admin. They sign in with their normal
# site email and password; the login is kept in a signed Flask session cookie.

SESSION_KEY = "admin_user_id"


def current_admin():
    user_id = session.get(SESSION_KEY)
    if not user_id:
        return None
    user = db.session.get(User, user_id)
    if user is None or user.role != "admin" or user.is_suspended:
        session.pop(SESSION_KEY, None)
        return None
    return user


LOGIN_PAGE = """
<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Admin Sign In</title>
<style>
 body{font-family:system-ui,sans-serif;font-size:18px;background:#f6f3f3;margin:0;padding:40px 16px}
 form{max-width:420px;margin:auto;background:#fff;padding:32px;border-radius:8px;box-shadow:0 2px 12px rgba(0,0,0,.1)}
 h1{color:#590d0d;font-size:26px;margin-top:0}
 label{display:block;margin:16px 0 6px;font-weight:600}
 input{width:100%;box-sizing:border-box;font-size:18px;padding:12px;border:1px solid #999;border-radius:6px}
 button{margin-top:24px;width:100%;min-height:52px;font-size:18px;background:#590d0d;color:#fff;border:0;border-radius:6px;cursor:pointer}
 .error{background:#fde8e8;color:#8a1111;padding:12px;border-radius:6px;margin-bottom:8px}
</style></head><body>
<form method="post">
  <h1>Admin Sign In</h1>
  {% if error %}<div class="error">{{ error }}</div>{% endif %}
  <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
  <label for="email">Email</label>
  <input id="email" name="email" type="email" autocomplete="username" required value="{{ email or '' }}">
  <label for="password">Password</label>
  <input id="password" name="password" type="password" autocomplete="current-password" required>
  <button type="submit">Sign In</button>
</form></body></html>
"""


class SecureIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        if current_admin() is None:
            return redirect(url_for('.login', next=request.full_path))
        session.setdefault("admin_form_csrf", secrets.token_urlsafe(32))
        return self.render('admin/tcc_dashboard.html', stats=dashboard_stats(), settings=SiteSettings.get(),
                           csrf_token=session["admin_form_csrf"])

    def _checked_user(self, user_id):
        admin = current_admin()
        if admin is None:
            abort(403)
        token = session.get("admin_form_csrf")
        if not token or token != request.form.get("csrf_token"):
            abort(400)
        user = db.session.get(User, user_id)
        if user is None:
            abort(404)
        return admin, user

    @expose('/suspend/<int:user_id>', methods=['POST'])
    def suspend(self, user_id):
        admin, user = self._checked_user(user_id)
        if user.id == admin.id:
            flash("You cannot suspend your own account.", "error")
        else:
            suspend_user(user, request.form.get("reason"), admin)
            db.session.commit()
            flash(f"{user.email} is suspended. Undo this under Users (Unsuspend).")
        return redirect(url_for('.index'))

    @expose('/dismiss/<int:user_id>', methods=['POST'])
    def dismiss(self, user_id):
        _admin, user = self._checked_user(user_id)
        SecurityEvent.query.filter_by(user_id=user.id, is_reviewed=False).update({"is_reviewed": True})
        db.session.commit()
        flash(f"Marked {user.email}'s events as checked.")
        return redirect(url_for('.index'))

    @expose('/login', methods=['GET', 'POST'])
    @limiter.limit("10 per minute;50 per hour", methods=["POST"])
    def login(self):
        error = None
        email = None
        if request.method == 'POST':
            token = session.pop("admin_csrf", None)
            if not token or token != request.form.get("csrf_token"):
                error = "Your session expired. Please try again."
            else:
                email = (request.form.get("email") or "").strip().lower()
                password = request.form.get("password") or ""
                user = User.query.filter(func.lower(User.email) == email).first()
                if user and check_password_hash(user.password, password) and user.role == "admin" and not user.is_suspended:
                    session.clear()
                    session[SESSION_KEY] = user.id
                    user.last_login_at = datetime.utcnow()
                    db.session.commit()
                    next_url = request.args.get("next") or ""
                    # only allow redirects inside /admin
                    if not next_url.startswith("/admin"):
                        next_url = url_for(".index")
                    return redirect(next_url)
                error = "Wrong email or password, or this account is not an administrator."
        session["admin_csrf"] = secrets.token_urlsafe(32)
        return render_template_string(LOGIN_PAGE, error=error, email=email, csrf_token=session["admin_csrf"])

    @expose('/signout')
    def signout(self):
        session.pop(SESSION_KEY, None)
        return redirect(url_for('.login'))


class AdminOnlyMixin:
    def is_accessible(self):
        return current_admin() is not None

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin.login', next=request.full_path))


class SecureModelView(AdminOnlyMixin, ModelView):
    form_base_class = SecureForm  # CSRF protection on admin forms
    page_size = 50


def tier_choices(include_none_label):
    return [("", include_none_label)] + [(str(t.rank), f"{t.name} (level {t.rank})")
                                         for t in Tier.query.order_by(Tier.rank).all()]


class OptionalIntSelect(SelectField):
    """A drop-down whose empty choice saves as None."""
    def process_formdata(self, valuelist):
        self.data = int(valuelist[0]) if valuelist and valuelist[0] not in ("", "None") else None

    def pre_validate(self, form):
        pass


class UserAdmin(SecureModelView):
    column_list = ("id", "email", "name", "role", "tier_rank", "subscription_status", "granted_tier_rank",
                   "is_founding_member", "is_suspended", "flags", "created_at", "last_login_at")
    column_labels = {"tier_rank": "Paid level", "granted_tier_rank": "Free access level",
                     "granted_until": "Free access until", "is_suspended": "Suspended", "flags": "Security"}
    column_searchable_list = ("email", "name")
    column_filters = ("is_suspended", "role", "tier_rank", "subscription_status", "is_founding_member",
                      "granted_tier_rank")
    column_default_sort = ("id", True)
    column_exclude_list = ("password",)
    form_columns = ("email", "name", "role", "granted_tier_rank", "granted_until", "is_suspended", "suspended_reason",
                    "tier_rank", "subscription_status", "paid_through", "is_founding_member")
    form_overrides = {"granted_tier_rank": OptionalIntSelect}
    form_args = {
        "granted_tier_rank": {"label": "Give free access to level",
                              "description": "Use this to give a member access without paying (a gift, a scholarship, "
                                             "or while a PayPal problem is sorted out). PayPal never changes this."},
        "granted_until": {"description": "Leave empty for no end date."},
        "tier_rank": {"label": "Paid level (set by PayPal)",
                      "description": "Normally changed only by PayPal. To give access, use 'Give free access' above."},
        "subscription_status": {"description": "Normally changed only by PayPal."},
        "suspended_reason": {"description": "Only admins see this."},
    }
    form_choices = {
        "role": [("member", "Member"), ("teacher", "Teacher"), ("admin", "Admin")],
        "subscription_status": [(s, s) for s in ("none", "active", "past_due", "cancelled", "expired")],
    }

    def _flags(view, context, model, name):
        count = SecurityEvent.query.filter_by(user_id=model.id, is_reviewed=False).count()
        if not count:
            return ""
        return Markup(f'<a href="{url_for("securityevent.index_view", search=model.email)}">'
                      f'<span class="label label-danger">{count} to check</span></a>')

    column_formatters = {"flags": _flags}

    def _set_tier_choices(self, form):
        form.granted_tier_rank.choices = tier_choices("No free access")
        return form

    def create_form(self, obj=None):
        return self._set_tier_choices(super().create_form(obj))

    def edit_form(self, obj=None):
        return self._set_tier_choices(super().edit_form(obj))

    def on_model_change(self, form, model, is_created):
        if is_created:
            raise ValidationError("Members create their own accounts on the website.")
        if "is_suspended" in form and form.is_suspended.object_data != form.is_suspended.data:
            admin = current_admin()
            if model.is_suspended:
                if admin and model.id == admin.id:
                    raise ValidationError("You cannot suspend your own account.")
                suspend_user(model, model.suspended_reason, admin)
            else:
                unsuspend_user(model, admin)

    @action("suspend", "Suspend", "Suspend the selected accounts? They are stopped from watching right away and cannot sign in.")
    def action_suspend(self, ids):
        admin = current_admin()
        users = [u for u in User.query.filter(User.id.in_(ids)).all() if u.id != admin.id]
        for user in users:
            suspend_user(user, "Suspended from the Users list", admin)
        db.session.commit()
        flash(f"{len(users)} account(s) suspended.")

    @action("unsuspend", "Unsuspend", "Allow the selected accounts to sign in and watch again?")
    def action_unsuspend(self, ids):
        admin = current_admin()
        users = User.query.filter(User.id.in_(ids), User.is_suspended.is_(True)).all()
        for user in users:
            unsuspend_user(user, admin)
        db.session.commit()
        flash(f"{len(users)} account(s) unsuspended.")


SECTION_CHOICES = [("beginner", "Beginner"), ("intermediate", "Intermediate"), ("advanced", "Advanced"),
                   ("qigong", "Qigong"), (CORNER_SECTION, "Teacher's corner")]


class VideoAdmin(SecureModelView):
    column_list = ("id", "title", "slug", "section", "tier_rank", "status", "is_published",
                   "is_free_sample", "publish_at", "sort_order")
    column_searchable_list = ("title", "slug")
    column_filters = ("section", "status", "is_published", "is_free_sample")
    column_default_sort = ("sort_order", False)
    form_excluded_columns = ("encryption_key_enc", "description", "url", "streaming_url", "duration",
                             "is_downloadable", "price", "purchases", "tags", "upload_id", "uploader")
    column_exclude_list = ("encryption_key_enc",)
    form_choices = {
        "section": SECTION_CHOICES,
        "status": [(s, s) for s in ("placeholder", "uploading", "processing", "ready", "failed")],
    }


class ArticleAdmin(SecureModelView):
    column_list = ("id", "title", "author", "section", "category", "members_only", "status", "publish_at", "read_count")
    column_searchable_list = ("title", "author")
    column_filters = ("members_only", "status", "category", "section")
    form_choices = {"status": [("draft", "Draft"), ("scheduled", "Scheduled"), ("published", "Published")]}


class SiteSettingsAdmin(SecureModelView):
    can_create = False
    can_delete = False
    column_list = ("app_name", "school_name", "contact_phone", "contact_email", "founding_member_end_date")
    form_args = {
        "founding_member_end_date": {"description": "Members who subscribe before this date are founding members and "
                                                    "keep their price for life. Empty = the founding offer is open with no end date yet."},
        "notification_email": {"description": "Gets emails about new subscribers, cancellations and member questions. "
                                              "Never shown on the website."},
        "video_watermark": {"description": "Show the member's email and number moving over videos while they play."},
        "video_sections": {"description": 'List of {"key", "label", "tier_rank"}. Keys must not change once videos use them.'},
    }


class TierAdmin(SecureModelView):
    column_list = ("name", "rank", "description", "sort_order")
    column_default_sort = ("rank", False)
    form_excluded_columns = ("plans",)


class PlanAdmin(SecureModelView):
    column_list = ("tier", "interval", "price", "paypal_plan_id", "paypal_sandbox_plan_id", "is_active", "is_founding",
                   "created_at")
    column_default_sort = ("created_at", True)
    column_filters = ("is_active", "is_founding", "interval")
    form_choices = {"interval": [("month", "Monthly"), ("year", "Yearly")]}
    form_args = {
        "price": {"description": "A price already set up in PayPal cannot change. To change a price: untick 'Is Active' "
                                 "on the old plan, add a new plan with the new price, then run "
                                 "scripts/create_paypal_plans.py. Members on the old plan keep their price."},
        "is_active": {"description": "Offered to new members. Old plans stay for members already on them."},
        "is_founding": {"description": "The plan new members get while the founding offer is open."},
        "paypal_plan_id": {"description": "Live PayPal plan. Filled in by scripts/create_paypal_plans.py (starts with P-)."},
        "paypal_sandbox_plan_id": {"description": "PayPal sandbox (test) plan. Filled in by scripts/create_paypal_plans.py "
                                                  "while PAYPAL_MODE=sandbox."},
    }

    def on_model_change(self, form, model, is_created):
        if not is_created and (model.paypal_plan_id or model.paypal_sandbox_plan_id) and form.price.object_data is not None \
                and form.price.object_data != form.price.data:
            raise ValidationError("This price is already set up in PayPal and cannot change. Untick 'Is Active' on "
                                  "this plan and add a new plan with the new price instead.")


class SecurityEventAdmin(SecureModelView):
    can_create = False
    can_edit = False
    column_list = ("created_at", "user", "type", "details", "is_reviewed")
    column_labels = {"user": "Member", "type": "What happened", "is_reviewed": "Checked"}
    column_default_sort = ("created_at", True)
    column_searchable_list = ("user.email", "user.name")
    column_filters = ("is_reviewed", "type", "created_at")
    column_formatters = {
        "user": lambda v, c, m, n: m.user.email if m.user else "",
        "type": lambda v, c, m, n: EVENT_LABELS.get(m.type, m.type),
    }

    @action("reviewed", "Mark as checked", "Mark the selected events as checked?")
    def action_reviewed(self, ids):
        count = SecurityEvent.query.filter(SecurityEvent.id.in_(ids)).update({"is_reviewed": True}, synchronize_session=False)
        db.session.commit()
        flash(f"{count} event(s) marked as checked.")

    @action("suspend", "Suspend these members", "Suspend the members of the selected events? They are stopped from watching right away.")
    def action_suspend(self, ids):
        admin = current_admin()
        user_ids = {e.user_id for e in SecurityEvent.query.filter(SecurityEvent.id.in_(ids)).all() if e.user_id}
        users = [u for u in User.query.filter(User.id.in_(user_ids)).all() if u.id != admin.id and not u.is_suspended]
        for user in users:
            suspend_user(user, "Suspended from Security Events", admin)
        db.session.commit()
        flash(f"{len(users)} account(s) suspended.")


class QuestionAdmin(SecureModelView):
    can_create = False
    column_list = ("created_at", "user", "question", "status", "answer_video", "answer_note", "answered_at")
    column_labels = {"user": "Member", "answer_video": "Answer video"}
    column_default_sort = ("created_at", True)
    column_searchable_list = ("question", "user.email")
    column_filters = ("status", "created_at")
    column_formatters = {
        "user": lambda v, c, m, n: m.user.email if m.user else "",
        "answer_video": lambda v, c, m, n: m.answer_video.title if m.answer_video else "",
    }
    form_columns = ("status", "answer_note")
    form_choices = {"status": [("new", "New"), ("answered", "Answered")]}


class EncodingJobAdmin(SecureModelView):
    can_create = False
    column_list = ("id", "video", "status", "attempts", "error", "created_at", "started_at", "finished_at")
    column_default_sort = ("id", True)
    column_filters = ("status",)
    column_formatters = {"video": lambda v, c, m, n: m.video.title if m.video else ""}
    form_columns = ("status", "attempts")
    form_choices = {"status": [(s, s) for s in ("queued", "running", "done", "failed")]}

    @action("retry", "Try again", "Prepare the selected failed videos again?")
    def action_retry(self, ids):
        count = 0
        for job in EncodingJob.query.filter(EncodingJob.id.in_(ids), EncodingJob.status == "failed").all():
            video = job.video
            if video is None or not video.master_r2_key:
                continue
            video.status, video.failure_reason = "processing", None
            db.session.add(EncodingJob(video_id=video.id, status="queued"))
            count += 1
        db.session.commit()
        flash(f"{count} video(s) will be prepared again by the worker.")


class ReadOnlyAdmin(SecureModelView):
    can_create = False
    can_edit = False


class LogoutView(AdminOnlyMixin, BaseView):
    @expose('/')
    def index(self):
        return redirect(url_for('admin.signout'))


def setup_admin(app):
    app.secret_key = os.environ.get('FLASK_APP_KEY', 'sample key')
    app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'

    admin = Admin(
        app,
        name='Gin Soon Admin',
        template_mode='bootstrap3',
        index_view=SecureIndexView(name="Dashboard"),
    )

    tcc = "The Tai Chi Company"
    admin.add_view(SiteSettingsAdmin(SiteSettings, db.session, name="Site Settings", category=tcc))
    admin.add_view(UserAdmin(User, db.session, name="Users", category=tcc))
    admin.add_view(TierAdmin(Tier, db.session, name="Tiers", category=tcc))
    admin.add_view(PlanAdmin(Plan, db.session, name="Plans and Prices", category=tcc))
    admin.add_view(VideoAdmin(Video, db.session, name="Videos", category=tcc))
    admin.add_view(EncodingJobAdmin(EncodingJob, db.session, name="Encoding Jobs", category=tcc))
    admin.add_view(QuestionAdmin(Question, db.session, name="Ask the Teacher Questions", category=tcc))
    admin.add_view(SecurityEventAdmin(SecurityEvent, db.session, name="Security Events", category=tcc))
    admin.add_view(ReadOnlyAdmin(PlaybackSession, db.session, name="Playback Sessions", category=tcc))
    admin.add_view(ReadOnlyAdmin(WebhookEvent, db.session, name="Webhook Events", category=tcc))

    admin.add_view(ArticleAdmin(Article, db.session))
    admin.add_view(SecureModelView(Class, db.session))
    admin.add_view(SecureModelView(Book, db.session))

    admin.add_view(LogoutView(name='Logout', endpoint='logout'))
