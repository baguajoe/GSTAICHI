from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import uuid

db = SQLAlchemy()


# Tai Chi Company roles and subscription states
USER_ROLES = ("member", "teacher", "admin")
SUBSCRIPTION_STATUSES = ("none", "active", "past_due", "cancelled", "expired")


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    is_active = db.Column(db.Boolean(), default=True)

    # Tai Chi Company fields
    name = db.Column(db.String(120), nullable=True)
    role = db.Column(db.String(20), nullable=False, default="member", server_default="member")
    tier_rank = db.Column(db.Integer, nullable=False, default=0, server_default="0")  # 0 = free account
    subscription_status = db.Column(db.String(20), nullable=False, default="none", server_default="none")
    paypal_subscription_id = db.Column(db.String(64), nullable=True, index=True)
    current_plan_id = db.Column(db.Integer, db.ForeignKey("plan.id"), nullable=True)
    paid_through = db.Column(db.DateTime, nullable=True)  # access lasts until this date after cancelling
    next_billing_at = db.Column(db.DateTime, nullable=True)  # from PayPal, shown on the account page
    is_founding_member = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())
    is_suspended = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())
    created_at = db.Column(db.DateTime, default=datetime.utcnow, server_default=db.func.now())
    last_login_at = db.Column(db.DateTime, nullable=True)

    current_plan = db.relationship("Plan", foreign_keys=[current_plan_id])

    def __repr__(self):
        return f'<User {self.email}>'

    @property
    def is_staff(self):
        return self.role in ("teacher", "admin")

    @property
    def is_paying_member(self):
        """Any paid tier counts. Teachers and admins see everything."""
        if self.is_staff:
            return True
        return self.tier_rank >= 1 and self.has_active_access

    @property
    def has_active_access(self):
        if self.subscription_status == "active":
            return True
        if self.subscription_status == "past_due":
            # PayPal retries a failed payment for a few days; keep access for a week after the paid period
            return self.paid_through is None or self.paid_through + timedelta(days=7) > datetime.utcnow()
        # Cancelled members keep access until the end of the paid period
        if self.subscription_status == "cancelled" and self.paid_through:
            return self.paid_through > datetime.utcnow()
        return False

    @property
    def effective_tier_rank(self):
        if self.is_staff:
            return 999
        return self.tier_rank if self.has_active_access else 0

    def serialize(self):
        return {
            "id": self.id,
            "email": self.email,
        }

    def serialize_account(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "role": self.role,
            "tier_rank": self.tier_rank,
            "effective_tier_rank": self.effective_tier_rank,
            "subscription_status": self.subscription_status,
            "current_plan": self.current_plan.serialize() if self.current_plan else None,
            "paid_through": self.paid_through.isoformat() if self.paid_through else None,
            "next_billing_at": self.next_billing_at.isoformat() if self.next_billing_at else None,
            "has_paypal_subscription": bool(self.paypal_subscription_id),
            "is_founding_member": self.is_founding_member,
            "is_paying_member": self.is_paying_member,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date, nullable=False)
    location = db.Column(db.String(300), nullable=False)

    def __repr__(self):
        return f"<Class {self.name}>"

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "date": self.date.strftime('%Y-%m-%d'),
            "location": self.location,
        }

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    publication_date = db.Column(db.Date, nullable=False)
    download_url = db.Column(db.String(2083), nullable=True)
    is_pod_available = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<Book {self.title}>"

    def serialize(self):
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "description": self.description,
            "price": str(self.price),
            "publication_date": self.publication_date.strftime('%Y-%m-%d'),
            "download_url": self.download_url,
            "is_pod_available": self.is_pod_available,
        }

VIDEO_STATUSES = ("placeholder", "uploading", "processing", "ready", "failed")
CORNER_SECTION = "vincents-corner"  # section key for the teacher's short videos (label comes from SiteSettings.corner_name)


class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)  # legacy field, use short/long_description
    url = db.Column(db.String(2083), nullable=True)  # legacy field, never store public video URLs
    streaming_url = db.Column(db.String(2083), nullable=True)  # legacy field
    duration = db.Column(db.Interval, nullable=True)  # legacy field, use duration_seconds
    is_downloadable = db.Column(db.Boolean, default=False)
    is_streamable = db.Column(db.Boolean, default=True)
    category = db.Column(db.String(100), nullable=True)
    tags = db.Column(db.String(300), nullable=True)
    price = db.Column(db.Float, nullable=False, default=0.0)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    views = db.Column(db.Integer, default=0)
    purchases = db.Column(db.Integer, default=0)

    # Tai Chi Company fields
    slug = db.Column(db.String(120), unique=True, nullable=True, index=True)  # also the R2 folder name
    section = db.Column(db.String(40), nullable=True)  # beginner / intermediate / advanced / qigong
    tier_rank = db.Column(db.Integer, nullable=False, default=1, server_default="1")
    short_description = db.Column(db.Text, nullable=True)
    long_description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="placeholder", server_default="placeholder")
    failure_reason = db.Column(db.Text, nullable=True)
    master_r2_key = db.Column(db.String(500), nullable=True)
    hls_master_path = db.Column(db.String(500), nullable=True)
    thumbnail_options = db.Column(db.JSON, nullable=True)
    thumbnail_path = db.Column(db.String(500), nullable=True)
    custom_thumbnail_path = db.Column(db.String(500), nullable=True)
    chapters = db.Column(db.JSON, nullable=True)  # [{"start": seconds, "label": "..."}]
    chapters_vtt_path = db.Column(db.String(500), nullable=True)
    encryption_key_enc = db.Column(db.Text, nullable=True)  # AES key encrypted with KEY_ENCRYPTION_SECRET
    duration_seconds = db.Column(db.Integer, nullable=True)
    width = db.Column(db.Integer, nullable=True)  # as shown on screen; upright phone videos are taller than wide
    height = db.Column(db.Integer, nullable=True)
    renditions = db.Column(db.JSON, nullable=True)  # [{"name": "720p", "width": 1280, "height": 720, "video_kbps": 2800}]
    publish_at = db.Column(db.DateTime, nullable=True)
    is_free_sample = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())
    sort_order = db.Column(db.Integer, nullable=False, default=0, server_default="0")
    is_published = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())
    uploaded_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Video {self.title}>"

    @property
    def is_coming_soon(self):
        return not self.hls_master_path or self.status != "ready"

    def serialize(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "url": self.url,
            "streaming_url": self.streaming_url,
            "duration": str(self.duration) if self.duration else None,
            "is_downloadable": self.is_downloadable,
            "is_streamable": self.is_streamable,
            "category": self.category,
            "tags": self.tags.split(',') if self.tags else [],
            "price": self.price,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "views": self.views,
            "purchases": self.purchases,
        }

    def serialize_card(self):
        """Safe public fields for library cards. Never includes keys or stream paths."""
        return {
            "id": self.id,
            "slug": self.slug,
            "title": self.title,
            "section": self.section,
            "tier_rank": self.tier_rank,
            "category": self.category,
            "short_description": self.short_description,
            "duration_seconds": self.duration_seconds,
            "width": self.width,
            "height": self.height,
            "thumbnail_path": self.custom_thumbnail_path or self.thumbnail_path,
            "is_free_sample": self.is_free_sample,
            "coming_soon": self.is_coming_soon,
            "publish_at": self.publish_at.isoformat() if self.publish_at else None,
            "sort_order": self.sort_order,
        }


class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    section=db.Column(db.String(100), nullable=True, default="Other")
    # content = db.Column(db.Text(collation='utf8mb4_unicode_ci'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    # Example for PostgreSQL-compatible unicode collation
    # content = db.Column(db.Text().with_variant(db.Text("C.UTF-8"), 'postgresql'), nullable=False)
    author = db.Column(db.String(100), nullable=False)

    # Tai Chi Company member article fields
    members_only = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())
    summary = db.Column(db.Text, nullable=True)
    cover_image_path = db.Column(db.String(500), nullable=True)
    category = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="published", server_default="published")  # draft / scheduled / published
    publish_at = db.Column(db.DateTime, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    article_photo = db.relationship("ArticlePhoto", back_populates="article", uselist=False)
    article_photos = db.relationship("ArticlePhotos", back_populates="article")

    def __repr__(self):
        return f"<Article {self.title}>"

    def serialize(self):
        return {
            "id": self.id,
            "title": self.title,
            "section": self.section,
            "content": self.content,
            "author": self.author,
            "article_photo": self.article_photo.serialize() if self.article_photo else None,
            "article_photos": [photo.serialize() for photo in self.article_photos],
        }

class ArticlePhoto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(500), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey("article.id"), nullable=False)
    article = db.relationship("Article", back_populates="article_photo", uselist=False)

    def __init__(self, public_id, image_url, article_id):
        self.public_id = public_id
        self.image_url = image_url.strip()
        self.article_id = article_id

    def serialize(self):
        return {
            "id": self.id,
            "image_url": self.image_url
        }
    

class ArticlePhotos(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(500), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey("article.id"), nullable=False)
    article = db.relationship("Article", back_populates="article_photos")

    def __init__(self, public_id, image_url, article_id):
        self.public_id = public_id
        self.image_url = image_url.strip()
        self.article_id = article_id

    def serialize(self):
        return {
            "id": self.id,
            "image_url": self.image_url
        }



class SiteSettings(db.Model):
    """Single row holding all branding and contact info, so the app can be reused by other teachers."""
    __tablename__ = "site_settings"
    id = db.Column(db.Integer, primary_key=True)
    app_name = db.Column(db.String(120), nullable=False, default="Tai Chi Company")
    school_name = db.Column(db.String(200), nullable=False, default="")
    logo_url = db.Column(db.String(500), nullable=True)
    primary_color = db.Column(db.String(20), nullable=False, default="#590d0d")
    contact_phone = db.Column(db.String(50), nullable=True)
    contact_email = db.Column(db.String(120), nullable=True)
    address = db.Column(db.String(300), nullable=True)
    notification_email = db.Column(db.String(120), nullable=True)  # private, never sent to the browser
    copyright_line = db.Column(db.String(300), nullable=True)
    terms_of_service_text = db.Column(db.Text, nullable=True)
    article_categories = db.Column(db.JSON, nullable=True)  # ["Application", "Forms", ...]
    video_sections = db.Column(db.JSON, nullable=True)  # [{"key": "beginner", "label": "Beginner", "tier_rank": 1}, ...]
    teacher_name = db.Column(db.String(120), nullable=False, default="", server_default="")  # "Latest from ...", "Ask ..."
    corner_name = db.Column(db.String(120), nullable=False, default="", server_default="")  # the teacher's short-video section
    corner_categories = db.Column(db.JSON, nullable=True)  # ["Tip", "Correction", ...]
    founding_member_end_date = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get(cls):
        settings = cls.query.order_by(cls.id).first()
        if settings is None:
            settings = cls(app_name="Tai Chi Company", school_name="")
            db.session.add(settings)
            db.session.commit()
        return settings

    def serialize_public(self):
        return {
            "app_name": self.app_name,
            "school_name": self.school_name,
            "logo_url": self.logo_url,
            "primary_color": self.primary_color,
            "contact_phone": self.contact_phone,
            "contact_email": self.contact_email,
            "address": self.address,
            "copyright_line": self.copyright_line,
            "terms_of_service_text": self.terms_of_service_text,
            "article_categories": self.article_categories or [],
            "video_sections": self.video_sections or [],
            "teacher_name": self.teacher_name,
            "corner_name": self.corner_name,
            "corner_section": CORNER_SECTION,
            "corner_categories": self.corner_categories or [],
            "founding_member_end_date": self.founding_member_end_date.isoformat() if self.founding_member_end_date else None,
        }

    def __repr__(self):
        return f"<SiteSettings {self.app_name}>"


class Tier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), nullable=False)
    rank = db.Column(db.Integer, unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0, server_default="0")

    plans = db.relationship("Plan", back_populates="tier", order_by="Plan.interval")

    def __repr__(self):
        return f"<Tier {self.name}>"

    def serialize(self, include_plans=True):
        data = {
            "id": self.id,
            "name": self.name,
            "rank": self.rank,
            "description": self.description,
            "sort_order": self.sort_order,
        }
        if include_plans:
            data["plans"] = [p.serialize() for p in self.plans if p.is_active]
        return data


class Plan(db.Model):
    """A PayPal billing plan. A price change means a new Plan row; old ones stay for existing subscribers."""
    id = db.Column(db.Integer, primary_key=True)
    tier_id = db.Column(db.Integer, db.ForeignKey("tier.id"), nullable=False)
    interval = db.Column(db.String(10), nullable=False)  # month / year
    price = db.Column(db.Numeric(10, 2), nullable=False)
    paypal_plan_id = db.Column(db.String(64), unique=True, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, server_default=db.true())  # offered to new subscribers
    is_founding = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())
    created_at = db.Column(db.DateTime, default=datetime.utcnow, server_default=db.func.now())

    tier = db.relationship("Tier", back_populates="plans")

    def __repr__(self):
        tier_name = self.tier.name if self.tier else "?"
        return f"<Plan {tier_name} {self.interval} ${self.price}>"

    def serialize(self):
        return {
            "id": self.id,
            "tier_id": self.tier_id,
            "tier_name": self.tier.name if self.tier else None,
            "tier_rank": self.tier.rank if self.tier else None,
            "interval": self.interval,
            "price": str(self.price),
            "paypal_plan_id": self.paypal_plan_id,
            "is_active": self.is_active,
            "is_founding": self.is_founding,
        }


class EncodingJob(db.Model):
    __tablename__ = "encoding_job"
    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey("video.id"), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default="queued", server_default="queued")  # queued / running / done / failed
    attempts = db.Column(db.Integer, nullable=False, default=0, server_default="0")
    error = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, server_default=db.func.now())
    started_at = db.Column(db.DateTime, nullable=True)
    finished_at = db.Column(db.DateTime, nullable=True)

    video = db.relationship("Video")

    def __repr__(self):
        return f"<EncodingJob {self.id} video={self.video_id} {self.status}>"


def _uuid_str():
    return str(uuid.uuid4())


class PlaybackSession(db.Model):
    __tablename__ = "playback_session"
    id = db.Column(db.String(36), primary_key=True, default=_uuid_str)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    video_id = db.Column(db.Integer, db.ForeignKey("video.id"), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow, server_default=db.func.now())
    last_heartbeat_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip = db.Column(db.String(64), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, server_default=db.true())
    position_seconds = db.Column(db.Integer, nullable=True)  # last position reported by the player
    key_request_count = db.Column(db.Integer, nullable=False, default=0, server_default="0")
    last_key_at = db.Column(db.DateTime, nullable=True)
    segment_count = db.Column(db.Integer, nullable=False, default=0, server_default="0")  # reported by the Worker
    flagged = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())
    ended_at = db.Column(db.DateTime, nullable=True)
    end_reason = db.Column(db.String(40), nullable=True)  # stopped / timeout / replaced / access_lost

    user = db.relationship("User")
    video = db.relationship("Video")

    def end(self, reason):
        if self.is_active:
            self.is_active = False
            self.ended_at = datetime.utcnow()
            self.end_reason = reason

    def device_label(self):
        """Plain description of the device, from the browser's user agent."""
        ua = self.user_agent or ""
        for needle, label in (("iPhone", "iPhone"), ("iPad", "iPad"), ("Android", "Android phone or tablet"),
                              ("CrKey", "Chromecast"), ("Windows", "Windows computer"),
                              ("Macintosh", "Mac computer"), ("Linux", "computer")):
            if needle in ua:
                return label
        return "another device"


class SecurityEvent(db.Model):
    __tablename__ = "security_event"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True, index=True)
    type = db.Column(db.String(60), nullable=False)
    details = db.Column(db.JSON, nullable=True)
    is_reviewed = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())
    created_at = db.Column(db.DateTime, default=datetime.utcnow, server_default=db.func.now(), index=True)

    user = db.relationship("User")

    def __repr__(self):
        return f"<SecurityEvent {self.type} user={self.user_id}>"


class WebhookEvent(db.Model):
    """PayPal webhook event IDs, so each event is processed only once."""
    __tablename__ = "webhook_event"
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.String(100), unique=True, nullable=False)
    event_type = db.Column(db.String(100), nullable=True)
    payload = db.Column(db.JSON, nullable=True)
    received_at = db.Column(db.DateTime, default=datetime.utcnow, server_default=db.func.now())
    processed_at = db.Column(db.DateTime, nullable=True)
