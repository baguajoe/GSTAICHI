"""PayPal subscriptions: admin link, confirm, login restore and webhook. Run from the repo root with:
  pipenv run python -m unittest discover -s tests -t .
Throwaway SQLite; PayPal and email are mocked, nothing real is reached."""
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

_workdir = tempfile.mkdtemp(prefix="tcc-paypal-tests-")
os.environ.update(
    DATABASE_URL=f"sqlite:///{_workdir}/test.db", FLASK_APP_KEY="test-key", JWT_SECRET_KEY="test-jwt-key",
    BACKEND_URL="https://api.test", FRONTEND_URL="https://site.test", GMAIL="", GMAIL_PASSWORD="",
    ENV="test", FLASK_DEBUG="0", PAYPAL_MODE="live", PAYPAL_CLIENT_ID="x", PAYPAL_CLIENT_SECRET="y",
    EMAIL_SENDER="off",
)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from flask_jwt_extended import create_access_token  # noqa: E402
from werkzeug.security import generate_password_hash  # noqa: E402
from app import app  # noqa: E402
from api.extensions import limiter  # noqa: E402
from api.models import db, User, Tier, Plan, SiteSettings  # noqa: E402
from api import admin as admin_module, paypal  # noqa: E402
from api.paypal import PayPalError  # noqa: E402

assert app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite")
NEXT = (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%dT10:00:00Z")

def sub(sid="I-LXD0MUSW6HP2", status="ACTIVE", plan="P-ADV", custom="24"):
    return {"id": sid, "status": status, "plan_id": plan, "custom_id": custom,
            "start_time": "2026-11-05T10:00:00Z", "billing_info": {"next_billing_time": NEXT}}

class Base(unittest.TestCase):
    def setUp(self):
        self.ctx = app.app_context()
        self.ctx.push()
        limiter.enabled = False
        db.drop_all()
        db.create_all()
        SiteSettings.get()
        for rank, name, pid in ((1, "Beginner", "P-BEG"), (2, "Intermediate", "P-INT"), (3, "Advanced", "P-ADV")):
            t = Tier(name=name, rank=rank)
            db.session.add(t)
            db.session.flush()
            db.session.add(Plan(tier_id=t.id, interval="month", price=9.99 + 5 * (rank - 1), paypal_plan_id=pid,
                                paypal_sandbox_plan_id=pid + "-SB"))
        self.until = datetime.utcnow() + timedelta(days=10)
        self.rudy = User(id=24, email="rudy@test.org", password=generate_password_hash("password123"),
                         granted_tier_rank=3, granted_until=self.until)
        db.session.add(self.rudy)
        db.session.commit()
        self.paypal_subs = {}
        self.cancelled = []
        for target, value in (
                ("api.paypal.get_subscription", self.fake_get),
                ("api.paypal.cancel_subscription", lambda sid, reason: self.cancelled.append(sid)),
                ("api.tcc_payments.notify_school", lambda *a, **k: None),
                ("api.tcc_payments.plan_status_emails", lambda *a, **k: None),
                ("api.paypal.verify_webhook", lambda h, e: True)):
            p = patch(target, value)
            p.start()
            self.addCleanup(p.stop)

    def tearDown(self):
        db.session.remove()
        self.ctx.pop()

    def fake_get(self, sid, timeout=30):
        if sid not in self.paypal_subs:
            raise PayPalError("PayPal said: RESOURCE_NOT_FOUND", 404, {})
        value = self.paypal_subs[sid]
        if isinstance(value, Exception):
            raise value
        return value

    def admin_client(self):
        admin = User(email="admin@test.org", password="x", role="admin")
        db.session.add(admin)
        db.session.commit()
        client = app.test_client()
        with client.session_transaction() as s:
            s[admin_module.SESSION_KEY] = admin.id
            s["admin_form_csrf"] = "tok"
        return client

    def reload(self):
        db.session.expire_all()
        return db.session.get(User, 24)

class AdminLink(Base):
    def test_links_rudy_and_keeps_free_access(self):
        self.paypal_subs["I-LXD0MUSW6HP2"] = sub()
        client = self.admin_client()
        page = client.get("/admin/user/link-paypal/24")
        self.assertEqual(page.status_code, 200, page.get_data(as_text=True)[:500])
        r = client.post("/admin/user/link-paypal/24", data={"csrf_token": "tok", "subscription_id": "I-LXD0MUSW6HP2"})
        html = r.get_data(as_text=True)
        self.assertIn("alert-success", html, html[:3000])
        u = self.reload()
        self.assertEqual((u.paypal_subscription_id, u.tier_rank, u.subscription_status), ("I-LXD0MUSW6HP2", 3, "active"))
        self.assertIsNotNone(u.paid_through)
        self.assertEqual((u.granted_tier_rank, u.granted_until), (3, self.until))
        self.assertEqual(self.cancelled, [])
        listing = client.get("/admin/user/").get_data(as_text=True)
        self.assertIn("I-LXD0MUSW6HP2", listing)
        edit = client.get("/admin/user/edit/?id=24").get_data(as_text=True)
        self.assertIn("I-LXD0MUSW6HP2", edit)
        self.assertIn("link-paypal/24", edit)

    def test_refuses_not_active_wrong_owner_unknown_plan_and_bad_csrf(self):
        client = self.admin_client()
        for s, text in ((sub(status="SUSPENDED"), "not ACTIVE"), (sub(custom="99"), "user 99"),
                        (sub(plan="P-OTHER"), "not in Plans")):
            self.paypal_subs["I-LXD0MUSW6HP2"] = s
            html = client.post("/admin/user/link-paypal/24",
                               data={"csrf_token": "tok", "subscription_id": "I-LXD0MUSW6HP2"}).get_data(as_text=True)
            self.assertIn(text, html)
            self.assertEqual(self.reload().tier_rank, 0)
        self.assertIn("no subscription", client.post(
            "/admin/user/link-paypal/24", data={"csrf_token": "tok", "subscription_id": "I-NOPE"}).get_data(as_text=True))
        self.assertEqual(client.post("/admin/user/link-paypal/24",
                                     data={"csrf_token": "bad", "subscription_id": "I-X"}).status_code, 400)

    def test_list_action_redirects(self):
        import re
        client = self.admin_client()
        listing = client.get("/admin/user/").get_data(as_text=True)
        token = re.search(r'id="action_form".*?name="csrf_token"[^>]*value="([^"]+)"', listing, re.S).group(1)
        r = client.post("/admin/user/action/", data={"action": "link_paypal", "rowid": ["24"], "csrf_token": token})
        self.assertIn(r.status_code, (302, 303))
        self.assertIn("link-paypal/24", r.headers["Location"])

class ConfirmAndLogin(Base):
    def token(self):
        return {"Authorization": f"Bearer {create_access_token(identity='rudy@test.org')}"}

    def test_pending_confirm_saves_id_then_login_restores(self):
        self.paypal_subs["I-NEW"] = sub("I-NEW", status="APPROVED")
        c = app.test_client()
        r = c.post("/api/tcc/subscription/confirm", json={"subscription_id": "I-NEW"}, headers=self.token())
        self.assertEqual(r.status_code, 202)
        self.assertEqual(self.reload().paypal_subscription_id, "I-NEW")
        self.paypal_subs["I-NEW"] = sub("I-NEW")
        r = c.post("/api/login", json={"email": "rudy@test.org", "password": "password123"})
        self.assertEqual(r.status_code, 200)
        u = self.reload()
        self.assertEqual((u.tier_rank, u.subscription_status), (3, "active"))
        self.assertEqual(u.granted_until, self.until)

    def test_login_survives_paypal_down(self):
        self.rudy.paypal_subscription_id = "I-DOWN"
        db.session.commit()
        self.paypal_subs["I-DOWN"] = PayPalError("Could not reach PayPal: Timeout")
        r = app.test_client().post("/api/login", json={"email": "rudy@test.org", "password": "password123"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.reload().tier_rank, 0)

    def test_confirm_active(self):
        self.paypal_subs["I-A"] = sub("I-A")
        r = app.test_client().post("/api/tcc/subscription/confirm", json={"subscription_id": "I-A"}, headers=self.token())
        self.assertEqual(r.status_code, 200, r.get_json())
        self.assertEqual(self.reload().tier_rank, 3)

    def test_confirm_other_users_subscription_refused(self):
        self.paypal_subs["I-B"] = sub("I-B", custom="7")
        r = app.test_client().post("/api/tcc/subscription/confirm", json={"subscription_id": "I-B"}, headers=self.token())
        self.assertEqual(r.status_code, 403)
        self.assertIsNone(self.reload().paypal_subscription_id)

class Webhook(Base):
    def post(self, sid, custom="24"):
        return app.test_client().post("/api/tcc/paypal/webhook", json={
            "id": f"WH-{sid}", "event_type": "BILLING.SUBSCRIPTION.ACTIVATED",
            "resource": {"id": sid, "custom_id": custom}})

    def test_new_subscription_replaces_non_billing_old_one(self):
        self.rudy.paypal_subscription_id, self.rudy.subscription_status = "I-OLD", "cancelled"
        db.session.commit()
        self.paypal_subs["I-NEW"] = sub("I-NEW")
        self.assertEqual(self.post("I-NEW").status_code, 200)
        u = self.reload()
        self.assertEqual((u.paypal_subscription_id, u.tier_rank, u.subscription_status), ("I-NEW", 3, "active"))

    def test_old_replaced_subscription_still_ignored(self):
        self.rudy.paypal_subscription_id, self.rudy.subscription_status, self.rudy.tier_rank = "I-CUR", "active", 2
        db.session.commit()
        self.paypal_subs["I-OLD"] = sub("I-OLD")
        self.post("I-OLD")
        u = self.reload()
        self.assertEqual((u.paypal_subscription_id, u.tier_rank), ("I-CUR", 2))

if __name__ == "__main__":
    unittest.main()
