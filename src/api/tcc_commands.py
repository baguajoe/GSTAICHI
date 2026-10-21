"""Flask CLI commands for Tai Chi Company. All are safe to run more than once."""
import os
import re
from datetime import datetime
from decimal import Decimal
import click
from sqlalchemy import func, inspect
from .models import db, User, SiteSettings, Tier, Plan, Video, Article, USER_ROLES
from .seed_data.tcc_catalog import DEFAULT_SITE_SETTINGS, TIERS, VIDEOS, SECTION_TIER_RANK
from .seed_data.video_descriptions import VIDEO_LONG_DESCRIPTIONS


def setup_tcc_commands(app):

    @app.cli.command("setup-database")
    def setup_database():
        """Run at every deploy. Brings the database up to date; on a brand-new, empty database it creates all
        tables first (the oldest migrations assume tables from the original site, so they cannot start from empty)."""
        from flask_migrate import upgrade, stamp
        tables = set(inspect(db.engine).get_table_names())
        if not tables:
            print("Empty database: creating all tables.")
            db.create_all()
            stamp()
            print("Done. Next: flask seed-tcc (or flask seed-tcc --no-videos for a new teacher).")
        elif "alembic_version" not in tables:
            raise click.ClickException("This database has tables but no migration history. "
                                       "Ask a developer before going further.")
        else:
            upgrade()
            print("Database is up to date.")

    @app.cli.command("seed-tcc")
    @click.option("--no-videos", is_flag=True, help="Skip the Gin Soon video list (for a new teacher's own site).")
    def seed_tcc(no_videos):
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
        for order, v in enumerate([] if no_videos else VIDEOS, start=1):
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
        if no_videos:
            print("No placeholder videos created (--no-videos). Upload videos in the Studio.")
        else:
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
        """Add the first member article, "Combat Tai Chi Chuan" by Vincent Chu, formatted with headings for its
        numbered sections. An existing copy still in the old plain-text format is upgraded. Safe to run again."""
        title = "Combat Tai Chi Chuan"
        with open(os.path.join(os.path.dirname(__file__), "seed_data", "combat_tai_chi_chuan.html")) as f:
            content = f.read().strip()
        summary = re.sub(r"<[^>]+>", "", content.split("</p>", 1)[0]).strip()
        article = Article.query.filter_by(title=title, members_only=True).first()
        if article is not None:
            if article.content.lstrip().startswith("<"):
                print(f"Member article '{title}' already exists.")
                return
            article.content = content
            db.session.commit()
            print(f"Member article '{title}' upgraded to the new format.")
            return
        db.session.add(Article(
            title=title, author="Vincent Chu", content=content, members_only=True, category="Application",
            section="Application", summary=summary, status="published", publish_at=datetime.utcnow(),
        ))
        db.session.commit()
        print(f"Member article '{title}' added.")

    @app.cli.command("import-public-articles")
    def import_public_articles():
        """Bring the articles from the old public Articles page (seed_data/public_articles.json) into the member
        articles, in the magazine style, members-only. An article already there (same title, or imported before)
        is not copied again; it only learns its old page number, so old links find it. Safe to run again."""
        from .legacy_articles import load_public_articles, to_magazine_html, RENAMED
        from .article_import import _summary

        for old, new in RENAMED.items():
            for article in Article.query.filter_by(title=old).all():
                article.title = new
                print(f"Renamed '{old}' to '{new}'.")

        created, linked, converted = [], [], []
        for item in load_public_articles():
            if Article.query.filter_by(legacy_id=item["legacy_id"]).first():
                continue
            title = RENAMED.get(item["title"], item["title"])
            same = Article.query.filter(func.lower(Article.title) == title.lower())
            member_copy = same.filter(Article.members_only.is_(True)).first()
            if member_copy is not None:
                member_copy.legacy_id = item["legacy_id"]
                linked.append(title)
                continue
            content = to_magazine_html(item["content"])
            article = same.filter(Article.members_only.is_(False)).first()
            if article is not None:
                converted.append(title)  # the old public copy becomes the member article
            else:
                article = Article(title=title)
                db.session.add(article)
                created.append(title)
            article.author = item["author"]
            article.category = article.section = item["category"]
            article.content = content
            article.summary = _summary(content) or None
            article.members_only = True
            article.is_free = False
            article.status = "published"
            article.publish_at = article.publish_at or datetime.utcnow()
            article.legacy_id = item["legacy_id"]
        db.session.commit()
        for title in created:
            print(f"Imported '{title}'.")
        for title in converted:
            print(f"Imported '{title}' (the old public copy was turned into the member article).")
        for title in linked:
            print(f"'{title}' is already a member article; old links now open it.")
        print(f"{len(created) + len(converted)} articles imported, {len(linked)} already there.")

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
