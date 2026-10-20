"""Flask CLI commands for Tai Chi Company. All are safe to run more than once."""
from datetime import datetime
from decimal import Decimal
import click
from sqlalchemy import func
from .models import db, User, SiteSettings, Tier, Plan, Video, Article, USER_ROLES
from .seed_data.tcc_catalog import DEFAULT_SITE_SETTINGS, TIERS, VIDEOS, SECTION_TIER_RANK
from .seed_data.video_descriptions import VIDEO_LONG_DESCRIPTIONS


def setup_tcc_commands(app):

    @app.cli.command("seed-tcc")
    def seed_tcc():
        """Create site settings, tiers, plans and placeholder videos. Never overwrites existing rows."""
        settings = SiteSettings.query.first()
        if settings is None:
            db.session.add(SiteSettings(**DEFAULT_SITE_SETTINGS))
            print("Site settings created.")
        else:
            print("Site settings already exist, left unchanged.")

        for t in TIERS:
            tier = Tier.query.filter_by(rank=t["rank"]).first()
            if tier is None:
                tier = Tier(name=t["name"], rank=t["rank"], description=t["description"], sort_order=t["sort_order"])
                db.session.add(tier)
                db.session.flush()
                print(f"Tier {tier.name} created.")
            for interval, price in (("month", t["monthly"]), ("year", t["yearly"])):
                if Plan.query.filter_by(tier_id=tier.id, interval=interval).first() is None:
                    # The launch plans are the founding member plans; PayPal plan IDs are added in /admin
                    db.session.add(Plan(tier_id=tier.id, interval=interval, price=Decimal(price),
                                        is_active=True, is_founding=True))
                    print(f"  Plan {tier.name} / {interval} ${price} created.")

        now = datetime.utcnow()
        created = 0
        for order, v in enumerate(VIDEOS, start=1):
            if Video.query.filter_by(slug=v["slug"]).first():
                continue
            db.session.add(Video(
                slug=v["slug"],
                title=v["title"],
                section=v["section"],
                tier_rank=SECTION_TIER_RANK[v["section"]],
                category=v.get("category"),
                short_description=v.get("short_description") or None,
                is_free_sample=v.get("is_free_sample", False),
                status="placeholder",
                is_published=True,
                publish_at=now,
                sort_order=order,
            ))
            created += 1
        db.session.commit()
        print(f"{created} placeholder videos created ({len(VIDEOS) - created} already existed).")

    @app.cli.command("seed-video-descriptions")
    def seed_video_descriptions():
        """Copy long descriptions from seed_data/video_descriptions.py onto existing videos (matched by slug)."""
        updated = 0
        for slug, text in VIDEO_LONG_DESCRIPTIONS.items():
            video = Video.query.filter_by(slug=slug).first()
            if video is None:
                print(f"  Skipped '{slug}': no video with that slug (run flask seed-tcc first).")
                continue
            video.long_description = text.strip()
            updated += 1
            print(f"  Updated '{slug}'.")
        db.session.commit()
        print(f"{updated} video descriptions updated.")

    @app.cli.command("seed-tcc-articles")
    def seed_tcc_articles():
        """Add the first member article, "Combat Tai Chi Chuan" by Vincent Chu. Safe to run again."""
        from .commands import COMBAT_PART_ONE, COMBAT_PART_TWO
        title = "Combat Tai Chi Chuan"
        if Article.query.filter_by(title=title, members_only=True).first():
            print(f"Member article '{title}' already exists.")
            return
        text = COMBAT_PART_ONE.strip() + "\n\n" + COMBAT_PART_TWO.strip()
        if text.startswith(title):
            text = text[len(title):].strip()  # the title is shown separately
        first_paragraph = text.split("\n\n")[0].strip()
        db.session.add(Article(
            title=title, author="Vincent Chu", content=text, members_only=True, category="Application",
            section="Application", summary=first_paragraph, status="published", publish_at=datetime.utcnow(),
        ))
        db.session.commit()
        print(f"Member article '{title}' added.")

    @app.cli.command("set-role")
    @click.argument("email")
    @click.argument("role")
    def set_role(email, role):
        """Give a user a role: member, teacher or admin. Example: flask set-role you@example.com admin"""
        if role not in USER_ROLES:
            raise click.BadParameter(f"role must be one of {', '.join(USER_ROLES)}")
        user = User.query.filter(func.lower(User.email) == email.strip().lower()).first()
        if user is None:
            raise click.ClickException(f"No user with email {email}. Sign up on the site first.")
        user.role = role
        db.session.commit()
        print(f"{user.email} is now {role}.")
