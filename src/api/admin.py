import os
import secrets
from datetime import datetime
from flask import request, redirect, url_for, session, render_template_string, abort
from flask_admin import Admin, AdminIndexView, expose, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import SecureForm
from werkzeug.security import check_password_hash
from sqlalchemy import func
from .models import (db, User, Class, Book, Video, Article, SiteSettings, Tier, Plan,
                     EncodingJob, PlaybackSession, SecurityEvent, WebhookEvent)
from .extensions import limiter

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
        return super().index()

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


class UserAdmin(SecureModelView):
    column_list = ("id", "email", "name", "role", "tier_rank", "subscription_status",
                   "is_founding_member", "is_suspended", "created_at", "last_login_at")
    column_searchable_list = ("email", "name")
    column_filters = ("role", "tier_rank", "subscription_status", "is_founding_member", "is_suspended")
    column_exclude_list = ("password",)
    form_excluded_columns = ("password",)
    form_choices = {
        "role": [("member", "Member"), ("teacher", "Teacher"), ("admin", "Admin")],
        "subscription_status": [(s, s) for s in ("none", "active", "past_due", "cancelled", "expired")],
    }


class VideoAdmin(SecureModelView):
    column_list = ("id", "title", "slug", "section", "tier_rank", "status", "is_published",
                   "is_free_sample", "publish_at", "sort_order")
    column_searchable_list = ("title", "slug")
    column_filters = ("section", "status", "is_published", "is_free_sample")
    column_default_sort = ("sort_order", False)
    form_excluded_columns = ("encryption_key_enc", "description", "url", "streaming_url", "duration",
                             "is_downloadable", "price", "purchases", "tags")
    column_exclude_list = ("encryption_key_enc",)
    form_choices = {
        "section": [("beginner", "Beginner"), ("intermediate", "Intermediate"),
                    ("advanced", "Advanced"), ("qigong", "Qigong")],
        "status": [(s, s) for s in ("placeholder", "uploading", "processing", "ready", "failed")],
    }


class ArticleAdmin(SecureModelView):
    column_list = ("id", "title", "author", "section", "category", "members_only", "status", "publish_at")
    column_searchable_list = ("title", "author")
    column_filters = ("members_only", "status", "category", "section")
    form_choices = {"status": [("draft", "Draft"), ("scheduled", "Scheduled"), ("published", "Published")]}


class SiteSettingsAdmin(SecureModelView):
    can_create = False
    can_delete = False
    column_list = ("app_name", "school_name", "contact_phone", "contact_email", "founding_member_end_date")


class PlanAdmin(SecureModelView):
    column_list = ("tier", "interval", "price", "paypal_plan_id", "is_active", "is_founding", "created_at")
    form_choices = {"interval": [("month", "Monthly"), ("year", "Yearly")]}


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
        index_view=SecureIndexView(),
    )

    admin.add_view(SiteSettingsAdmin(SiteSettings, db.session, name="Site Settings", category="Tai Chi Company"))
    admin.add_view(UserAdmin(User, db.session, category="Tai Chi Company"))
    admin.add_view(SecureModelView(Tier, db.session, category="Tai Chi Company"))
    admin.add_view(PlanAdmin(Plan, db.session, category="Tai Chi Company"))
    admin.add_view(VideoAdmin(Video, db.session, category="Tai Chi Company"))
    admin.add_view(SecureModelView(EncodingJob, db.session, name="Encoding Jobs", category="Tai Chi Company"))
    admin.add_view(SecureModelView(SecurityEvent, db.session, name="Security Events", category="Tai Chi Company"))
    admin.add_view(ReadOnlyAdmin(PlaybackSession, db.session, name="Playback Sessions", category="Tai Chi Company"))
    admin.add_view(ReadOnlyAdmin(WebhookEvent, db.session, name="Webhook Events", category="Tai Chi Company"))

    admin.add_view(ArticleAdmin(Article, db.session))
    admin.add_view(SecureModelView(Class, db.session))
    admin.add_view(SecureModelView(Book, db.session))

    admin.add_view(LogoutView(name='Logout', endpoint='logout'))
