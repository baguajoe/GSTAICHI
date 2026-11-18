"""The weekly "New this week" email. Run from the repo root with:  pipenv run python -m unittest discover -s tests -t .
Throwaway SQLite; emails are captured, nothing is sent."""
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

_workdir = tempfile.mkdtemp(prefix="tcc-digest-tests-")
os.environ.update(
    DATABASE_URL=f"sqlite:///{_workdir}/test.db", FLASK_APP_KEY="test-key", JWT_SECRET_KEY="test-jwt-key",
    BACKEND_URL="https://api.test", FRONTEND_URL="https://site.test", GMAIL="", GMAIL_PASSWORD="",
    ENV="test", FLASK_DEBUG="0", EMAIL_SENDER="off",
)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from flask_jwt_extended import create_access_token  # noqa: E402
from app import app  # noqa: E402
from api.extensions import limiter  # noqa: E402
from api.models import db, User, Tier, Video, Article, SiteSettings, ContentDigest, DigestRecipient, EmailLog  # noqa: E402
from api import admin as admin_module, member_emails  # noqa: E402
from api.article_batches import load_batch, apply_batch  # noqa: E402

assert app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite"), "tests must never run on a real database"
NOW = datetime.utcnow()


class Base(unittest.TestCase):
    def setUp(self):
        self.ctx = app.app_context()
        self.ctx.push()
        limiter.enabled = False
        db.drop_all()
        db.create_all()
        SiteSettings.get()
        db.session.add_all([Tier(name="Student", rank=1), Tier(name="Advanced", rank=2)])
        db.session.commit()
        self.sent = []
        patcher = patch("api.member_emails.send_email", side_effect=lambda **kw: self.sent.append(kw))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.free = self.member("free@test.org")
        self.paid = self.member("paid@test.org", tier_rank=1, subscription_status="active")
        self.top = self.member("top@test.org", tier_rank=2, subscription_status="active")
        self.off = self.member("off@test.org", email_new_videos=False)
        self.gone = self.member("gone@test.org", is_suspended=True)

    def tearDown(self):
        db.session.remove()
        self.ctx.pop()

    def member(self, email, **fields):
        user = User(email=email, password="x", is_active=True, **fields)
        db.session.add(user)
        db.session.commit()
        return user

    def article(self, title, **fields):
        a = Article(title=title, author="Vincent Chu", content="<p>Some words.</p>", members_only=True,
                    status=fields.pop("status", "published"), category=fields.pop("category", "Training"),
                    summary=f"About {title}.", publish_at=fields.pop("publish_at", NOW - timedelta(hours=1)), **fields)
        db.session.add(a)
        db.session.commit()
        return a

    def video(self, title, tier_rank=1, ready=True, **fields):
        slug = title.lower().replace(" ", "-")
        v = Video(title=title, slug=slug, section="beginner", tier_rank=tier_rank,
                  is_published=fields.pop("is_published", True),
                  status="ready" if ready else "placeholder", hls_master_path=f"{slug}/master.m3u8" if ready else None,
                  publish_at=fields.pop("publish_at", NOW - timedelta(hours=1)), short_description=f"{title} lesson.",
                  **fields)
        db.session.add(v)
        db.session.commit()
        return v

    def send_all(self):
        for _ in range(10):
            if not member_emails.process_queue():
                break
        return {m["recipient"]: m for m in self.sent}


class WhatGoesIn(Base):
    def test_only_new_visible_content(self):
        new = self.article("New Article")
        self.article("Draft", status="draft")
        self.article("Later", publish_at=NOW + timedelta(days=2))
        self.article("Already Emailed", digest_sent_at=NOW - timedelta(days=7))
        ready = self.video("Ready Video")
        self.video("Coming Soon", ready=False)
        self.video("Inside An Article", show_in_library=False)
        self.video("Hidden", is_published=False)
        articles, videos = member_emails.pending_content()
        self.assertEqual([a.title for a in articles], [new.title])
        self.assertEqual([v.title for v in videos], [ready.title])

    def test_skip_the_week_when_nothing_is_new(self):
        digest, reason = member_emails.queue_digest("weekly")
        self.assertIsNone(digest)
        self.assertIn("Nothing new", reason)
        self.assertEqual(ContentDigest.query.count(), 0)

    def test_a_video_that_finishes_later_goes_into_a_later_digest(self):
        v = self.video("Slow Encode", ready=False, publish_at=NOW - timedelta(days=20))
        self.article("First")
        member_emails.queue_digest("manual")
        v.status, v.hls_master_path = "ready", "slow/master.m3u8"
        db.session.commit()
        self.assertEqual([x.title for x in member_emails.pending_content()[1]], ["Slow Encode"])


class Sending(Base):
    def test_one_email_per_member_with_the_right_videos(self):
        for n in range(3):
            self.article(f"Article {n}")
        self.video("Student Form", tier_rank=1)
        self.video("Advanced Form", tier_rank=2)
        self.video("Free Lesson", tier_rank=2, is_free_sample=True)
        digest, _ = member_emails.queue_digest("weekly")
        self.assertEqual(digest.total, 3)  # not the member who turned it off, not the suspended one
        mails = self.send_all()
        self.assertEqual(sorted(mails), ["free@test.org", "paid@test.org", "top@test.org"])
        self.assertEqual(len(self.sent), 3)

        free = mails["free@test.org"]
        self.assertTrue(free["subject"].startswith("New this week: "))
        for n in range(3):
            self.assertIn(f"Article {n}", free["body"])
        watch, others = free["html"].split("New on other plans")
        self.assertIn("Free Lesson", watch)
        self.assertNotIn("Student Form", watch)
        self.assertIn("Student Form", others)
        self.assertIn("Advanced Form", others)
        self.assertIn("Upgrade to watch", others)

        paid = mails["paid@test.org"]
        watch, others = paid["html"].split("New on other plans")
        self.assertIn("Student Form", watch)
        self.assertIn("Advanced Form", others)

        top = mails["top@test.org"]
        self.assertNotIn("New on other plans", top["html"])
        self.assertNotIn("Upgrade to watch", top["html"])
        self.assertIn("Watch now", top["html"])

        for m in mails.values():
            self.assertIn("List-Unsubscribe", m["headers"])
            self.assertIn("/api/tcc/email/unsubscribe?t=", m["html"])
            self.assertIn("https://site.test/tai-chi-company/articles/", m["html"])
        self.assertEqual(ContentDigest.query.one().status, "done")
        self.assertEqual(EmailLog.query.filter_by(kind="digest", status="sent").count(), 3)

    def test_nothing_twice(self):
        self.article("Once")
        member_emails.queue_digest("manual")
        self.send_all()
        self.assertIsNone(member_emails.queue_digest("manual")[0])
        self.send_all()
        self.assertEqual(len(self.sent), 3)

    def test_turned_off_after_queueing(self):
        self.article("Something")
        member_emails.queue_digest("weekly")
        self.free.email_new_videos = False
        db.session.commit()
        self.send_all()
        self.assertNotIn("free@test.org", [m["recipient"] for m in self.sent])
        self.assertEqual(DigestRecipient.query.filter_by(status="skipped").count(), 1)

    def test_daily_limit(self):
        self.article("Something")
        member_emails.queue_digest("weekly")
        with patch.object(member_emails, "DAILY_LIMIT", member_emails.RESERVE + 2):
            self.send_all()
        self.assertEqual(len(self.sent), 2)
        self.assertEqual(ContentDigest.query.one().status, "sending")

    def test_weekly_runs_once_in_six_days(self):
        self.article("One")
        self.assertIsNotNone(member_emails.queue_digest("weekly")[0])
        self.article("Two")
        digest, reason = member_emails.queue_digest("weekly")
        self.assertIsNone(digest)
        self.assertIn("already", reason)
        later = member_emails.queue_digest("weekly", now=NOW + timedelta(days=7))[0]
        self.assertEqual(later.article_ids, [Article.query.filter_by(title="Two").one().id])

    def test_bulk_import_is_one_email_not_ten(self):
        with db.engine.begin() as conn:
            apply_batch(conn, load_batch("vincent_chu_articles_2026_11.json"), log=lambda m: None)
        digest, _ = member_emails.queue_digest("weekly")
        self.assertEqual(len(digest.article_ids), 10)
        self.send_all()
        self.assertEqual(len(self.sent), 3)
        self.assertIn("and 9 more", self.sent[0]["subject"])
        body = self.sent[0]["body"]
        self.assertLess(body.index("Chinese Martial Arts Curriculum"), body.index("Why Practice Tai Chi Chuan Slowly"))

    def test_unsubscribe_link(self):
        client = app.test_client()
        token = member_emails.unsubscribe_token(self.free)
        page = client.get(f"/api/tcc/email/unsubscribe?t={token}").get_data(as_text=True)
        self.assertIn("weekly email", page)
        db.session.expire_all()
        self.assertFalse(db.session.get(User, self.free.id).email_new_videos)
        client.post("/api/tcc/email/unsubscribe", data={"t": token, "action": "resubscribe"})
        db.session.expire_all()
        self.assertTrue(db.session.get(User, self.free.id).email_new_videos)

    def test_account_switch(self):
        r = app.test_client().put("/api/tcc/profile", json={"email_new_videos": False},
                                  headers={"Authorization": f"Bearer {create_access_token(identity=self.paid.email)}"})
        self.assertLess(r.status_code, 300, r.get_data(as_text=True))
        db.session.expire_all()
        self.assertFalse(db.session.get(User, self.paid.id).email_new_videos)


class Admin(Base):
    def admin_client(self):
        admin = self.member("admin@test.org", role="admin", name="Vincent Chu")
        client = app.test_client()
        with client.session_transaction() as s:
            s[admin_module.SESSION_KEY] = admin.id
            s["admin_form_csrf"] = "tok"
        return client

    def test_preview_send_now_and_log(self):
        client = self.admin_client()
        self.article("Important Article")
        self.video("New Form From Vincent", tier_rank=2)
        page = client.get("/admin/emails/").get_data(as_text=True)
        self.assertIn("Waiting for the next email", page)
        self.assertIn("New Form From Vincent", page)
        free = client.get("/admin/emails/digest/preview?plan=free").get_data(as_text=True)
        self.assertIn("Upgrade to watch", free)
        top = client.get("/admin/emails/digest/preview?plan=top").get_data(as_text=True)
        self.assertNotIn("Upgrade to watch", top)

        client.post("/admin/emails/test/digest", data={"csrf_token": "tok"})
        self.assertEqual([m["recipient"] for m in self.sent], ["admin@test.org"])
        self.assertTrue(self.sent[0]["subject"].startswith("[TEST]"))
        self.assertEqual(ContentDigest.query.count(), 0)  # a test does not use up the new content

        r = client.post("/admin/emails/digest/send", data={"csrf_token": "tok"}, follow_redirects=True)
        html = r.get_data(as_text=True)
        self.assertIn("on its way to", html)
        digest = ContentDigest.query.one()
        self.assertEqual((digest.kind, digest.total), ("manual", 4))  # the admin has the emails on too
        self.send_all()
        html = client.get("/admin/emails/").get_data(as_text=True)
        self.assertIn("4 of 4 sent", html)
        self.assertIn("Nothing new since the last email", html)

        again = client.post("/admin/emails/digest/send", data={"csrf_token": "tok"}, follow_redirects=True)
        self.assertIn("Nothing new", again.get_data(as_text=True))
        self.assertEqual(client.post("/admin/emails/digest/send", data={"csrf_token": "x"}).status_code, 400)

    def test_cron_command(self):
        runner = app.test_cli_runner()
        out = runner.invoke(args=["queue-weekly-digest"]).output
        self.assertIn("No weekly email", out)
        self.article("For The Cron")
        out = runner.invoke(args=["queue-weekly-digest"]).output
        self.assertIn("Queued", out)
        self.assertEqual(ContentDigest.query.one().kind, "weekly")

    def test_per_video_email_is_gone(self):
        v = self.video("Some Video")
        r = app.test_client().post(f"/api/tcc/studio/videos/{v.id}/announce", json={"send": True},
                                   headers={"Authorization": f"Bearer {create_access_token(identity=self.paid.email)}"})
        self.assertIn(r.status_code, (404, 405))


if __name__ == "__main__":
    unittest.main()
