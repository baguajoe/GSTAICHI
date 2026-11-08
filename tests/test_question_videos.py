"""Ask Vincent member videos. Run from the repo root with:  pipenv run python -m unittest discover -s tests -t .

Runs on a throwaway SQLite file with an in-memory stand-in for storage. The settings below replace anything from
.env before the app is imported, so these tests can never reach the real database, the R2 buckets or Gmail.
"""
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

_workdir = tempfile.mkdtemp(prefix="tcc-tests-")
os.environ.update(
    DATABASE_URL=f"sqlite:///{_workdir}/test.db", FLASK_APP_KEY="test-key", JWT_SECRET_KEY="test-jwt-key",
    R2_ENDPOINT_URL="https://r2.invalid", R2_ACCESS_KEY_ID="test", R2_SECRET_ACCESS_KEY="test",
    R2_MASTERS_BUCKET="test-masters", BACKEND_URL="https://api.test", FRONTEND_URL="https://site.test",
    GMAIL="", GMAIL_PASSWORD="", ENV="test", FLASK_DEBUG="0",
)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from botocore.exceptions import ClientError  # noqa: E402
from flask_jwt_extended import create_access_token  # noqa: E402
from app import app  # noqa: E402
from api.extensions import limiter  # noqa: E402
from api.models import db, Question, SiteSettings, User  # noqa: E402
from api import admin as admin_module, question_videos as qv  # noqa: E402

MB = 1024 ** 2
assert app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite"), "tests must never run on a real database"


class FakeStorage:
    """Stands in for the boto3 client behind api.r2: objects are just {key: (size, last modified)}."""

    def __init__(self):
        self.objects = {}
        self.fail_deletes = False

    def add(self, key, size=10 * MB, age=timedelta(0)):
        self.objects[key] = (size, datetime.now(timezone.utc) - age)

    def generate_presigned_url(self, operation, ExpiresIn, Params):
        return f"https://signed.test/{operation}/{Params['Key']}?expires={ExpiresIn}&d={Params.get('ResponseContentDisposition', '')}"

    def head_object(self, Bucket, Key):
        if Key not in self.objects:
            raise ClientError({"Error": {"Code": "404"}}, "HeadObject")
        return {"ContentLength": self.objects[Key][0]}

    def delete_object(self, Bucket, Key):
        if self.fail_deletes:
            raise ClientError({"Error": {"Code": "500"}}, "DeleteObject")
        self.objects.pop(Key, None)

    def get_paginator(self, _name):
        storage = self

        class Paginator:
            def paginate(self, Bucket, Prefix):
                yield {"Contents": [{"Key": k, "LastModified": m} for k, (_s, m) in storage.objects.items() if k.startswith(Prefix)]}
        return Paginator()


class Base(unittest.TestCase):
    def setUp(self):
        self.ctx = app.app_context()
        self.ctx.push()
        limiter.enabled = False
        db.drop_all()
        db.create_all()
        SiteSettings.get()
        self.storage = FakeStorage()
        for target, value in (("api.r2.client", lambda *a, **k: self.storage),
                              ("api.tcc_questions.email", lambda *a, **k: True)):
            patcher = patch(target, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.paid = self.member("paid@test.org", tier_rank=1, subscription_status="active")
        self.other = self.member("other@test.org", tier_rank=1, subscription_status="active")
        self.free = self.member("free@test.org")
        self.teacher = self.member("teacher@test.org", role="teacher")
        self.client = app.test_client()

    def tearDown(self):
        db.session.remove()
        self.ctx.pop()

    def member(self, email, **fields):
        user = User(email=email, password="x", is_active=True, **fields)
        db.session.add(user)
        db.session.commit()
        return user

    def call(self, method, path, user, body=None):
        headers = {"Authorization": f"Bearer {create_access_token(identity=user.email)}"} if user else {}
        return getattr(self.client, method)(f"/api/tcc{path}", json=body, headers=headers)

    def upload_url(self, user, **overrides):
        body = {"filename": "IMG_0001.MOV", "content_type": "video/quicktime", "size": 10 * MB, "seconds": 60, **overrides}
        return self.call("post", "/questions/video/upload-url", user, body)

    def uploaded(self, user, size=10 * MB, **overrides):
        """A finished upload: the signed token, with the file in storage."""
        response = self.upload_url(user, **overrides)
        self.assertEqual(response.status_code, 200, response.get_json())
        data = response.get_json()
        key = data["upload_url"].split("put_object/")[1].split("?")[0]
        self.storage.add(key, size)
        return data["upload_token"], key

    def ask(self, user, token=None, text="How is my Single Whip?"):
        return self.call("post", "/questions", user, {"subject": "Single Whip", "question": text, "video_token": token})

    def question_with_video(self, user, **fields):
        key = qv.new_key(".mp4")
        self.storage.add(key)
        question = Question(user_id=user.id, subject="s", question="a question", member_video_key=key, member_video_size=10 * MB,
                            member_video_seconds=60, member_video_uploaded_at=datetime.utcnow(), **fields)
        db.session.add(question)
        db.session.commit()
        return question


class FreeMembers(Base):
    def test_refused_at_every_step(self):
        token, _key = self.uploaded(self.paid)
        question = self.question_with_video(self.free, created_at=datetime.utcnow())
        steps = [("post", "/questions/video/upload-url", {"filename": "a.mp4", "size": 1, "seconds": 1}),
                 ("post", "/questions/video/confirm", {"upload_token": token}),
                 ("post", "/questions/video/remove", {"upload_token": token}),
                 ("post", "/questions", {"subject": "s", "question": "a real question", "video_token": token}),
                 ("get", f"/questions/{question.id}/video", None)]
        for method, path, body in steps:
            with self.subTest(path=path):
                self.assertEqual(self.call(method, path, self.free, body).status_code, 403)

    def test_signed_out_refused_at_every_step(self):
        for method, path in (("post", "/questions/video/upload-url"), ("post", "/questions/video/confirm"),
                             ("post", "/questions/video/remove"), ("get", "/questions/1/video")):
            with self.subTest(path=path):
                self.assertEqual(self.call(method, path, None, {}).status_code, 401)

    def test_a_lapsed_member_can_no_longer_watch_their_own_video(self):
        question = self.question_with_video(self.free)
        self.assertEqual(self.call("get", f"/questions/{question.id}/video", self.free).status_code, 403)
        video = self.call("get", "/questions/mine", self.free).get_json()[0]["member_video"]
        self.assertEqual(video["state"], "locked")
        self.assertIsNone(video["watch_url"])

    def test_free_allowance_has_no_video_details(self):
        data = self.call("get", "/questions/allowance", self.free).get_json()
        self.assertFalse(data["can_ask"])
        self.assertNotIn("videos_remaining", data)


class Uploading(Base):
    def test_paid_member_sends_a_question_with_a_video(self):
        token, key = self.uploaded(self.paid)
        self.assertTrue(key.startswith("member-questions/") and key.endswith(".mov"))
        self.assertEqual(self.call("post", "/questions/video/confirm", self.paid, {"upload_token": token}).get_json()["size"], 10 * MB)
        response = self.ask(self.paid, token)
        self.assertEqual(response.status_code, 201, response.get_json())
        question = Question.query.one()
        self.assertEqual((question.member_video_key, question.member_video_size, question.member_video_seconds), (key, 10 * MB, 60))
        self.assertIsNotNone(question.member_video_uploaded_at)
        self.assertNotIn(key, str(Question.serialize(question)))

    def test_text_is_still_required_with_a_video(self):
        token, _key = self.uploaded(self.paid)
        self.assertEqual(self.ask(self.paid, token, text="").status_code, 400)
        self.assertEqual(Question.query.count(), 0)

    def test_a_video_is_optional(self):
        self.assertEqual(self.ask(self.paid).status_code, 201)
        self.assertIsNone(Question.query.one().member_video_key)

    def test_allowed_types(self):
        for filename, content_type in (("a.mp4", "video/mp4"), ("A.MOV", ""), ("b.webm", "video/webm"), ("no-extension", "video/quicktime")):
            with self.subTest(filename=filename):
                self.assertEqual(self.upload_url(self.paid, filename=filename, content_type=content_type).status_code, 200)

    def test_wrong_types_refused(self):
        for filename, content_type in (("a.avi", "video/x-msvideo"), ("a.exe", "video/mp4"), ("a.txt", "text/plain"), ("no-extension", "image/png"), ("", "")):
            with self.subTest(filename=filename):
                self.assertEqual(self.upload_url(self.paid, filename=filename, content_type=content_type).status_code, 400)

    def test_too_big_refused_before_upload(self):
        self.assertEqual(self.upload_url(self.paid, size=qv.MAX_BYTES).status_code, 200)
        self.assertEqual(self.upload_url(self.paid, size=qv.MAX_BYTES + 1).status_code, 400)

    def test_too_long_refused(self):
        self.assertEqual(self.upload_url(self.paid, seconds=180).status_code, 200)
        self.assertEqual(self.upload_url(self.paid, seconds=181).status_code, 400)

    def test_upload_address_is_short_lived(self):
        self.assertIn(f"expires={qv.UPLOAD_URL_SECONDS}", self.upload_url(self.paid).get_json()["upload_url"])

    def test_unreadable_length_is_allowed(self):
        self.assertEqual(self.upload_url(self.paid, seconds=None).status_code, 200)

    def test_file_bigger_than_claimed_is_deleted_at_confirm(self):
        token, key = self.uploaded(self.paid, size=qv.MAX_BYTES + 1)
        self.assertEqual(self.call("post", "/questions/video/confirm", self.paid, {"upload_token": token}).status_code, 400)
        self.assertNotIn(key, self.storage.objects)

    def test_file_bigger_than_claimed_is_deleted_when_skipping_confirm(self):
        token, key = self.uploaded(self.paid, size=qv.MAX_BYTES + 1)
        response = self.ask(self.paid, token)
        self.assertEqual(response.status_code, 400)
        self.assertTrue(response.get_json()["video_problem"])
        self.assertNotIn(key, self.storage.objects)
        self.assertEqual(Question.query.count(), 0)

    def test_upload_that_never_arrived_is_refused(self):
        token, key = self.uploaded(self.paid)
        del self.storage.objects[key]
        self.assertEqual(self.call("post", "/questions/video/confirm", self.paid, {"upload_token": token}).status_code, 400)
        self.assertEqual(self.ask(self.paid, token).status_code, 400)

    def test_remove_before_sending(self):
        token, key = self.uploaded(self.paid)
        self.assertEqual(self.call("post", "/questions/video/remove", self.paid, {"upload_token": token}).status_code, 200)
        self.assertNotIn(key, self.storage.objects)

    def test_sent_video_cannot_be_removed_or_reused(self):
        token, key = self.uploaded(self.paid)
        self.assertEqual(self.ask(self.paid, token).status_code, 201)
        self.assertEqual(self.call("post", "/questions/video/remove", self.paid, {"upload_token": token}).status_code, 400)
        self.assertIn(key, self.storage.objects)
        self.assertEqual(self.ask(self.paid, token).status_code, 400)
        self.assertEqual(Question.query.count(), 1)

    def test_another_members_or_altered_token_is_refused(self):
        token, key = self.uploaded(self.paid)
        self.assertEqual(self.ask(self.other, token).status_code, 400)
        self.assertEqual(self.ask(self.paid, token[:-3] + "abc").status_code, 400)
        self.assertEqual(self.call("post", "/questions/video/remove", self.other, {"upload_token": token}).status_code, 400)
        self.assertIn(key, self.storage.objects)

    def test_expired_token_is_refused(self):
        token, _key = self.uploaded(self.paid)
        with patch("itsdangerous.timed.TimestampSigner.get_timestamp", lambda _self: int(datetime.utcnow().timestamp()) + qv.TOKEN_SECONDS + 60):
            self.assertIsNone(qv.read_upload_token(token, self.paid))


class Limits(Base):
    def test_monthly_limit_defaults_to_two(self):
        self.assertEqual(SiteSettings.get().question_videos_per_month, 2)
        for _ in range(2):
            self.assertEqual(self.ask(self.paid, self.uploaded(self.paid)[0]).status_code, 201)
        response = self.upload_url(self.paid)
        self.assertEqual(response.status_code, 400)
        self.assertTrue(response.get_json()["video_limit"])
        self.assertEqual(self.call("get", "/questions/allowance", self.paid).get_json()["videos_remaining"], 0)

    def test_monthly_limit_is_checked_again_when_sending(self):
        tokens = [self.uploaded(self.paid)[0] for _ in range(3)]
        self.assertEqual(self.ask(self.paid, tokens[0]).status_code, 201)
        self.assertEqual(self.ask(self.paid, tokens[1]).status_code, 201)
        response = self.ask(self.paid, tokens[2])
        self.assertEqual(response.status_code, 400)
        self.assertTrue(response.get_json()["video_limit"])

    def test_text_questions_still_work_at_the_monthly_limit(self):
        for _ in range(2):
            self.ask(self.paid, self.uploaded(self.paid)[0])
        self.assertEqual(self.ask(self.paid).status_code, 201)

    def test_limit_can_be_changed_without_a_deploy(self):
        SiteSettings.get().question_videos_per_month = 0
        db.session.commit()
        self.assertEqual(self.upload_url(self.paid).status_code, 400)
        SiteSettings.get().question_videos_per_month = 1
        db.session.commit()
        self.assertEqual(self.upload_url(self.paid).status_code, 200)

    def test_last_months_videos_do_not_count(self):
        last_month = datetime.utcnow().replace(day=1) - timedelta(days=1)
        for _ in range(2):
            self.question_with_video(self.paid).member_video_uploaded_at = last_month
        db.session.commit()
        self.assertEqual(self.call("get", "/questions/allowance", self.paid).get_json()["videos_remaining"], 2)

    def test_removed_video_still_counts_for_the_month(self):
        self.question_with_video(self.paid, member_video_deleted_at=datetime.utcnow())
        self.assertEqual(self.call("get", "/questions/allowance", self.paid).get_json()["videos_remaining"], 1)

    def test_video_question_counts_toward_the_weekly_limit(self):
        SiteSettings.get().question_videos_per_month = 10
        db.session.commit()
        for _ in range(3):
            self.assertEqual(self.ask(self.paid, self.uploaded(self.paid)[0]).status_code, 201)
        self.assertEqual(self.upload_url(self.paid).status_code, 400)
        self.assertEqual(self.ask(self.paid).status_code, 400)

    def test_next_month_crosses_the_year(self):
        _per_month, _left, next_month = qv.videos_allowance(self.paid, datetime(2026, 12, 31, 23, 0))
        self.assertEqual(next_month, datetime(2027, 1, 1))


class Watching(Base):
    def test_owner_and_staff_get_a_watch_link_with_about_an_hour(self):
        question = self.question_with_video(self.paid)
        for viewer in (self.paid, self.teacher):
            with self.subTest(viewer=viewer.email):
                data = self.call("get", f"/questions/{question.id}/video", viewer).get_json()
                self.assertIn("get_object", data["watch_url"])
                self.assertIn("expires=3600", data["watch_url"])

    def test_a_different_member_gets_nothing(self):
        question = self.question_with_video(self.paid)
        response = self.call("get", f"/questions/{question.id}/video", self.other)
        self.assertEqual(response.status_code, 404)
        self.assertNotIn("signed.test", response.get_data(as_text=True))
        self.assertEqual(self.call("get", "/questions/mine", self.other).get_json(), [])
        self.assertEqual(self.call("get", "/studio/questions", self.other).status_code, 403)

    def test_watch_link_is_in_the_question_data_for_owner_and_staff(self):
        self.question_with_video(self.paid)
        self.assertIn("signed.test", self.call("get", "/questions/mine", self.paid).get_json()[0]["member_video"]["watch_url"])
        staff_video = self.call("get", "/studio/questions", self.teacher).get_json()[0]["member_video"]
        self.assertIn("signed.test", staff_video["watch_url"])
        self.assertIn("attachment", staff_video["download_url"])

    def test_storage_key_is_never_sent_to_the_browser_except_inside_a_signed_address(self):
        question = self.question_with_video(self.paid)
        data = self.call("get", "/questions/mine", self.paid).get_json()[0]
        self.assertNotIn("member_video_key", data)
        self.assertEqual(data["member_video"]["state"], "ready")
        self.assertEqual(question.member_video_seconds, data["member_video"]["seconds"])

    def test_removed_video_shows_the_note_and_no_link(self):
        question = self.question_with_video(self.paid, status="answered", answered_at=datetime.utcnow(), member_video_deleted_at=datetime.utcnow())
        video = self.call("get", "/questions/mine", self.paid).get_json()[0]["member_video"]
        self.assertEqual((video["state"], video["note"], video["watch_url"]), ("removed", "Video removed after 90 days.", None))
        self.assertEqual(self.call("get", f"/questions/{question.id}/video", self.paid).status_code, 404)

    def test_question_without_a_video_has_none(self):
        self.ask(self.paid)
        self.assertIsNone(self.call("get", "/questions/mine", self.paid).get_json()[0]["member_video"])

    def test_storage_being_down_does_not_break_my_questions(self):
        self.question_with_video(self.paid)
        with patch("api.r2.client", side_effect=qv.r2.R2NotConfigured("not set")):
            response = self.call("get", "/questions/mine", self.paid)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.get_json()[0]["member_video"]["watch_url"])


class EmailToTeacher(Base):
    def test_email_links_to_admin_and_never_to_storage(self):
        sent = []
        with patch("api.tcc_questions.email", lambda to, subject, body, **k: sent.append(body) or True):
            token, key = self.uploaded(self.paid)
            self.ask(self.paid, token)
        question = Question.query.one()
        self.assertIn(f"https://api.test/admin/questions/?q={question.id}", sent[0])
        self.assertIn("(1:00 long)", sent[0])
        for private in (key, "signed.test", "member-questions"):
            self.assertNotIn(private, sent[0])

    def test_email_without_a_video_does_not_mention_one(self):
        sent = []
        with patch("api.tcc_questions.email", lambda to, subject, body, **k: sent.append(body) or True):
            self.ask(self.paid)
        self.assertNotIn("sent a video", sent[0])


class AdminInbox(Base):
    def signed_in(self):
        admin = self.member("admin@test.org", role="admin")
        client = app.test_client()
        with client.session_transaction() as session:
            session[admin_module.SESSION_KEY] = admin.id
        return client

    def test_player_shows_for_admin_and_the_link_opens_one_question(self):
        wanted = self.question_with_video(self.paid)
        unrelated = Question(user_id=self.other.id, subject="Unrelated subject", question="Another question here")
        db.session.add(unrelated)
        db.session.commit()
        page = self.signed_in().get(f"/admin/questions/?q={wanted.id}").get_data(as_text=True)
        self.assertIn("<video", page)
        self.assertIn("signed.test/get_object", page)
        self.assertNotIn("Unrelated subject", page)

    def test_signed_out_goes_to_login_and_keeps_the_question(self):
        question = self.question_with_video(self.paid)
        response = app.test_client().get(f"/admin/questions/?q={question.id}")
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.headers["Location"])
        self.assertIn(f"q%3D{question.id}", response.headers["Location"])
        self.assertNotIn("signed.test", response.get_data(as_text=True))

    def test_member_is_not_let_in(self):
        question = self.question_with_video(self.paid)
        client = app.test_client()
        with client.session_transaction() as session:
            session[admin_module.SESSION_KEY] = self.paid.id
        self.assertEqual(client.get(f"/admin/questions/?q={question.id}").status_code, 302)

    def test_monthly_limit_form_refuses_silly_numbers_on_the_server(self):
        view = admin_module.SiteSettingsAdmin(SiteSettings, db.session, endpoint="settings-test", url="/settings-test")
        for value, expected in (("-1", False), ("101", False), ("abc", False), ("0", True), ("5", True)):
            with self.subTest(value=value), app.test_request_context(method="POST", data={"question_videos_per_month": value}):
                form = view.edit_form(SiteSettings.get())
                self.assertEqual(form.question_videos_per_month.validate(form), expected)

    def test_deleting_an_account_deletes_its_questions_and_videos(self):
        question = self.question_with_video(self.paid)
        other = self.question_with_video(self.other)
        key, other_key = question.member_video_key, other.member_video_key
        view = admin_module.UserAdmin(User, db.session, endpoint="user-delete-test", url="/user-delete-test")
        with app.test_request_context():
            self.assertTrue(view.delete_model(self.paid))
        self.assertNotIn(key, self.storage.objects)
        self.assertIn(other_key, self.storage.objects)
        self.assertEqual(Question.query.count(), 1)


class Purging(Base):
    def test_answered_90_days_ago_is_deleted_and_marked(self):
        now = datetime.utcnow()
        old = self.question_with_video(self.paid, status="answered", answered_at=now - timedelta(days=91))
        key = old.member_video_key
        result = qv.purge_question_videos(now)
        self.assertEqual(result["removed"], 1)
        self.assertNotIn(key, self.storage.objects)
        self.assertEqual(db.session.get(Question, old.id).member_video_deleted_at, now)

    def test_answered_less_than_90_days_ago_is_kept(self):
        now = datetime.utcnow()
        recent = self.question_with_video(self.paid, status="answered", answered_at=now - timedelta(days=89), created_at=now - timedelta(days=300))
        self.assertEqual(qv.purge_question_videos(now)["removed"], 0)
        self.assertIn(recent.member_video_key, self.storage.objects)

    def test_never_answered_is_deleted_after_120_days_only(self):
        now = datetime.utcnow()
        old = self.question_with_video(self.paid, created_at=now - timedelta(days=121))
        young = self.question_with_video(self.other, created_at=now - timedelta(days=119))
        old_key, young_key = old.member_video_key, young.member_video_key
        self.assertEqual(qv.purge_question_videos(now)["removed"], 1)
        self.assertNotIn(old_key, self.storage.objects)
        self.assertIn(young_key, self.storage.objects)

    def test_never_answered_note_says_120_days(self):
        question = self.question_with_video(self.paid, member_video_deleted_at=datetime.utcnow())
        self.assertEqual(qv.removed_note(question), "Video removed after 120 days.")

    def test_a_failed_delete_is_not_marked_and_is_tried_again(self):
        now = datetime.utcnow()
        old = self.question_with_video(self.paid, created_at=now - timedelta(days=200))
        self.storage.fail_deletes = True
        self.assertEqual(qv._delete_and_mark([old], now), (0, 1))
        self.assertIsNone(db.session.get(Question, old.id).member_video_deleted_at)
        self.storage.fail_deletes = False
        self.assertEqual(qv.purge_question_videos(now)["removed"], 1)

    def test_running_it_twice_changes_nothing_more(self):
        now = datetime.utcnow()
        self.question_with_video(self.paid, created_at=now - timedelta(days=200))
        qv.purge_question_videos(now)
        self.assertEqual(qv.purge_question_videos(now), {"removed": 0, "failed": 0, "abandoned": 0})

    def test_abandoned_uploads_go_but_recent_and_attached_ones_and_other_files_stay(self):
        now = datetime.utcnow()
        attached = self.question_with_video(self.paid)
        self.storage.objects[attached.member_video_key] = (1, datetime.now(timezone.utc) - timedelta(days=30))
        self.storage.add("member-questions/abandoned.mp4", age=timedelta(days=3))
        self.storage.add("member-questions/in-progress.mp4", age=timedelta(hours=3))
        self.storage.add("single-whip/master-1.mp4", age=timedelta(days=400))
        self.assertEqual(qv.purge_question_videos(now)["abandoned"], 1)
        self.assertEqual(set(self.storage.objects), {attached.member_video_key, "member-questions/in-progress.mp4", "single-whip/master-1.mp4"})

    def test_flask_command(self):
        old = self.question_with_video(self.paid, created_at=datetime.utcnow() - timedelta(days=200))
        result = app.test_cli_runner().invoke(args=["purge-question-videos"])
        self.assertIn("Deleted 1 old video(s)", result.output)
        self.assertIsNotNone(db.session.get(Question, old.id).member_video_deleted_at)

    def test_flask_command_for_one_member(self):
        mine = self.question_with_video(self.paid)
        theirs = self.question_with_video(self.other)
        result = app.test_cli_runner().invoke(args=["purge-question-videos", "--member", "PAID@test.org"])
        self.assertIn("Deleted 1 video(s)", result.output)
        self.assertIsNotNone(db.session.get(Question, mine.id).member_video_deleted_at)
        self.assertIsNone(db.session.get(Question, theirs.id).member_video_deleted_at)


if __name__ == "__main__":
    unittest.main()
