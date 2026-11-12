""""Accounts to check" rules. Run from the repo root with:  pipenv run python -m unittest discover -s tests -t .
Throwaway SQLite; nothing real is reached."""
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta

_workdir = tempfile.mkdtemp(prefix="tcc-rules-tests-")
os.environ.update(
    DATABASE_URL=f"sqlite:///{_workdir}/test.db", FLASK_APP_KEY="test-key", JWT_SECRET_KEY="test-jwt-key",
    BACKEND_URL="https://api.test", FRONTEND_URL="https://site.test", GMAIL="", GMAIL_PASSWORD="",
    ENV="test", FLASK_DEBUG="0", EMAIL_SENDER="off",
)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from app import app  # noqa: E402
from api.extensions import limiter  # noqa: E402
from api.models import db, User, Video, PlaybackSession, SecurityEvent, SiteSettings  # noqa: E402
from api import admin as admin_module, playback_rules as rules  # noqa: E402

assert app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite")
IPHONE = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)"
MAC = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
T0 = datetime(2026, 11, 10, 18, 0, 0)


class Base(unittest.TestCase):
    def setUp(self):
        self.ctx = app.app_context()
        self.ctx.push()
        limiter.enabled = False
        db.drop_all()
        db.create_all()
        SiteSettings.get()
        self.member = User(email="member@test.org", password="x", tier_rank=3, subscription_status="active")
        db.session.add(self.member)
        self.videos = []
        for i in range(4):
            v = Video(title=f"Form part {i + 1}", slug=f"form-{i + 1}", duration_seconds=30 * 60)  # 300 pieces each
            db.session.add(v)
            self.videos.append(v)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        self.ctx.pop()

    def session(self, video=None, start=T0, ua=IPHONE, ip="10.0.0.1", **kw):
        s = PlaybackSession(user_id=self.member.id, video_id=(video or self.videos[0]).id, started_at=start,
                            last_heartbeat_at=start, ip=ip, user_agent=ua, **kw)
        db.session.add(s)
        db.session.commit()
        return s

    def feed(self, s, pieces_per_minute, minutes, start_offset=timedelta(0), seeks_every=None):
        """Simulate the Worker reporting pieces every 10 seconds, and heartbeats with seeks."""
        position, step = 0, 0
        t = s.started_at + start_offset
        end = t + timedelta(minutes=minutes)
        per_report = pieces_per_minute / 6
        carry = 0.0
        while t < end:
            t += timedelta(seconds=10)
            step += 1
            carry += per_report
            count, carry = int(carry), carry - int(carry)
            if count:
                rules.note_pieces(s, count, t)
            if step % 2 == 0:  # heartbeat every 20 s
                position += 20
                if seeks_every and step % seeks_every == 0:
                    position += 600  # jump ahead 10 minutes
                rules.note_heartbeat(s, position, t)
                s.position_seconds, s.last_heartbeat_at = position, t
        db.session.commit()

    def events(self, kind):
        return SecurityEvent.query.filter_by(type=kind).all()


class DownloadSpeed(Base):
    def test_normal_watching_with_startup_buffer_is_not_flagged(self):
        s = self.session()
        rules.note_pieces(s, 30, T0 + timedelta(seconds=20))  # player fills its buffer at the start
        self.feed(s, 10, 30, start_offset=timedelta(seconds=20))  # then 1x: 10 pieces a minute
        self.assertEqual(self.events("sustained_fast_download"), [])

    def test_skimming_with_many_seeks_is_not_flagged(self):
        s = self.session()
        # Skipping ahead every 40 seconds: 1x playback plus a 90-second refill after each skip (about 3.2x overall)
        self.feed(s, 32, 30, seeks_every=4)
        self.assertEqual(self.events("sustained_fast_download"), [])

    def test_the_same_rate_without_seeks_is_flagged(self):
        s = self.session()
        self.feed(s, 32, 30)
        self.assertEqual(len(self.events("sustained_fast_download")), 1)

    def test_short_burst_is_not_flagged(self):
        s = self.session()
        self.feed(s, 60, 3)  # 6x for 3 minutes, then normal
        self.feed(s, 10, 20, start_offset=timedelta(minutes=3))
        self.assertEqual(self.events("sustained_fast_download"), [])

    def test_sustained_fast_fetching_is_flagged_once(self):
        s = self.session()
        self.feed(s, 50, 25)  # 5x for 25 minutes
        found = self.events("sustained_fast_download")
        self.assertEqual(len(found), 1)
        self.assertGreater(found[0].details["speed"], 3)
        self.assertIn("Form part 1", rules.describe_event(found[0]))

    def test_several_whole_videos_in_minutes_is_flagged(self):
        for i, v in enumerate(self.videos[:3]):
            s = self.session(video=v, start=T0 + timedelta(minutes=4 * i))
            rules.note_pieces(s, 300, s.started_at + timedelta(minutes=3))
            db.session.commit()
        found = self.events("bulk_download")
        self.assertEqual(len(found), 1)
        self.assertEqual(len(found[0].details["videos"]), 3)

    def test_two_whole_videos_are_not_enough(self):
        for i, v in enumerate(self.videos[:2]):
            s = self.session(video=v, start=T0 + timedelta(minutes=4 * i))
            rules.note_pieces(s, 300, s.started_at + timedelta(minutes=3))
        self.assertEqual(self.events("bulk_download"), [])


class Sharing(Base):
    def test_two_devices_at_once_is_recorded_but_ip_changes_are_not(self):
        first = self.session(ua=IPHONE, ip="10.0.0.1", is_active=True)
        same_phone_new_ip = self.session(ua=IPHONE, ip="172.16.0.9", is_active=True)
        rules.check_shared_streams(self.member, same_phone_new_ip)
        self.assertEqual(self.events("shared_streams"), [])
        laptop = self.session(ua=MAC, ip="10.0.0.2", is_active=True)
        rules.check_shared_streams(self.member, laptop)
        db.session.commit()
        found = self.events("shared_streams")
        self.assertEqual(len(found), 1)
        text = rules.describe_event(found[0])
        self.assertIn("Mac computer", text)
        self.assertIn("iPhone", text)
        self.assertIsNotNone(first)


class Listing(Base):
    def add(self, kind, when, reviewed=False):
        db.session.add(SecurityEvent(user_id=self.member.id, type=kind, details={}, created_at=when, is_reviewed=reviewed))
        db.session.commit()

    def test_one_day_is_not_listed_two_days_are(self):
        now = datetime.utcnow()
        self.add("shared_streams", now - timedelta(hours=1))
        self.add("shared_streams", now - timedelta(hours=2))
        self.assertEqual(rules.flagged_accounts(now), [])
        self.add("shared_streams", now - timedelta(days=3))
        listed = rules.flagged_accounts(now)
        self.assertEqual([r["id"] for r in listed], [self.member.id])
        self.assertIn("on 2 days", listed[0]["reasons"][0])

    def test_old_rules_and_different_rules_on_different_days_do_not_list(self):
        now = datetime.utcnow()
        self.add("many_ips", now - timedelta(days=1))
        self.add("many_ips", now - timedelta(days=2))
        self.add("fast_download", now - timedelta(days=3))
        self.add("shared_streams", now - timedelta(days=1))
        self.add("key_flood", now - timedelta(days=2))
        self.assertEqual(rules.flagged_accounts(now), [])

    def test_nothing_ever_suspends(self):
        now = datetime.utcnow()
        for d in range(10):
            for kind in rules.FLAG_RULES:
                self.add(kind, now - timedelta(days=d))
        rules.flagged_accounts(now)
        rules.replay()
        db.session.refresh(self.member)
        self.assertFalse(self.member.is_suspended)


class AdminPages(Base):
    def client(self):
        admin = User(email="admin@test.org", password="x", role="admin")
        db.session.add(admin)
        db.session.commit()
        c = app.test_client()
        with c.session_transaction() as s:
            s[admin_module.SESSION_KEY] = admin.id
            s["admin_form_csrf"] = "tok"
        return c

    def test_replay_compares_and_clear_marks_checked(self):
        now = datetime.utcnow()
        # Old rule warning from a normal member
        db.session.add(SecurityEvent(user_id=self.member.id, type="many_ips", details={"ips": ["a", "b", "c", "d"]},
                                     created_at=now - timedelta(days=1)))
        # A copier on two days: 25 minutes, 5x
        copier = User(email="copier@test.org", password="x", tier_rank=3, subscription_status="active")
        db.session.add(copier)
        db.session.commit()
        for d in (1, 2):
            start = now - timedelta(days=d)
            db.session.add(PlaybackSession(user_id=copier.id, video_id=self.videos[0].id, started_at=start,
                                           last_heartbeat_at=start + timedelta(minutes=25), ip="1.1.1.1",
                                           user_agent=MAC, segment_count=1250, is_active=False))
        db.session.commit()
        report = rules.replay(now)
        by_email = {r["email"]: r for r in report["rows"]}
        self.assertEqual(by_email["member@test.org"]["new"], [])
        self.assertTrue(by_email["member@test.org"]["old"])
        self.assertTrue(by_email["copier@test.org"]["new"])

        c = self.client()
        page = c.get("/admin/rules-check")
        self.assertEqual(page.status_code, 200)
        self.assertIn("copier@test.org", page.get_data(as_text=True))
        self.assertEqual(c.post("/admin/rules-check", data={"csrf_token": "bad"}).status_code, 400)
        c.post("/admin/rules-check", data={"csrf_token": "tok"})
        self.assertEqual(SecurityEvent.query.filter_by(is_reviewed=False).count(), 0)
        db.session.refresh(copier)
        self.assertFalse(copier.is_suspended)

    def test_account_page_is_plain_english(self):
        s = self.session()
        self.feed(s, 50, 25)
        page = self.client().get(f"/admin/account/{self.member.id}")
        html = page.get_data(as_text=True)
        self.assertEqual(page.status_code, 200)
        self.assertIn("normal playing speed", html)
        self.assertIn("Form part 1", html)
        self.assertIn("internet address 10.0.0.1", html)

    def test_dashboard_links_to_account_page(self):
        now = datetime.utcnow()
        for d in (1, 2):
            db.session.add(SecurityEvent(user_id=self.member.id, type="shared_streams", details={},
                                         created_at=now - timedelta(days=d)))
        db.session.commit()
        html = self.client().get("/admin/").get_data(as_text=True)
        self.assertIn(f"/admin/account/{self.member.id}", html)


if __name__ == "__main__":
    unittest.main()
