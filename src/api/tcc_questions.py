"""'Ask Vincent': paying members send questions; Vincent answers by email (Reply-To is the member), in /admin,
or in the Studio, often with a short corner video. Members see their questions and answers on the Account page."""
import os
import re
from datetime import datetime, timedelta
from flask import jsonify, request
from sqlalchemy.exc import IntegrityError
from . import question_videos as qv, r2
from .models import db, Question, Video, SiteSettings, CORNER_SECTION
from .extensions import limiter
from .notify import email, signature
from .clean_input import clean_text
from .tcc_auth import role_required, get_current_user
from .taichi_company import tcc, visible_videos

MAX_QUESTION_LENGTH = 2000
MIN_QUESTION_LENGTH = 10
MAX_SUBJECT_LENGTH = 150
MAX_ANSWER_LENGTH = 5000
QUESTIONS_PER_WEEK = 3
WEEK = timedelta(days=7)
VIDEO_TIME = re.compile(r"^(?:(\d{1,2}):)?(\d{1,3}):([0-5]\d)$")


def vincent_email():
    """Where member questions go. Server-side only: never sent to the browser."""
    return (os.getenv("ASK_VINCENT_EMAIL") or "chu.v@usa.com").strip()


def teacher():
    return SiteSettings.get().teacher_name or "Vincent"


def _video_time(value):
    """'12:30' or '1:02:30', tidied; '' when empty; None when it cannot be read."""
    value = (value or "").strip().replace(".", ":")
    if not value:
        return ""
    match = VIDEO_TIME.match(value)
    if not match:
        return None
    hours, minutes, seconds = match.groups()
    if hours:
        return f"{int(hours)}:{int(minutes):02d}:{seconds}"
    minutes = int(minutes)
    if minutes >= 60:
        return f"{minutes // 60}:{minutes % 60:02d}:{seconds}"
    return f"{minutes}:{seconds}"


def _allowance(user):
    """How many questions this member can still send this week, and when the next one frees up."""
    since = datetime.utcnow() - WEEK
    recent = (Question.query.filter(Question.user_id == user.id, Question.created_at >= since)
              .order_by(Question.created_at).all())
    remaining = max(0, QUESTIONS_PER_WEEK - len(recent))
    next_at = recent[0].created_at + WEEK if remaining == 0 and recent else None
    return remaining, next_at


def _friendly_date(when):
    return f"{when.strftime('%A, %B')} {when.day}"


def notify_member_answered(question):
    """Emails the member once their answer can be watched (or read). Returns True if an email went out.
    Members who turned off "Email me when Vincent answers" still see the answer under My questions."""
    if question.member_notified_at or question.user is None:
        return False
    if question.user.email_answers is False:
        return False
    video = question.answer_video
    if video is not None and video.status != "ready":
        return False  # sent later by the worker, when the video is Ready
    settings = SiteSettings.get()
    frontend = (os.getenv("FRONTEND_URL") or "").rstrip("/")
    name = teacher()
    asked = f"{question.subject}: " if question.subject else ""
    lines = [f"Hello{(' ' + question.user.name) if question.user.name else ''},", "",
             f"{name} has answered your question:", "", f"\"{asked}{question.question[:500]}\"", ""]
    if question.answer_note:
        lines += [question.answer_note, ""]
    if video is not None:
        when = ""
        if video.publish_at and video.publish_at > datetime.utcnow():
            when = f" It will be available from {video.publish_at.strftime('%B %d, %Y')}."
        lines += [f"Watch the answer: {frontend}/tai-chi-company/watch/{video.slug}{when}", ""]
    lines += [f"You can see all your questions and answers under My questions: {frontend}/tai-chi-company/account#my-questions", "",
              f"(To stop these emails, untick \"Email me when {name} answers\" on your Account page.)", ""]
    lines.append(signature())
    if email(question.user.email, f"{name} answered your question", "\n".join(lines)):
        question.member_notified_at = datetime.utcnow()
        return True
    return False


def save_answer(question, note=None, video_id=None):
    """Store an answer (a few words and/or a corner video), mark the question answered and email the member.
    Returns an error message, or None. The caller commits."""
    if video_id:
        video = db.session.get(Video, int(video_id))
        if video is None or video.section != CORNER_SECTION:
            return "Please choose one of the corner videos."
        question.answer_video_id = video.id
    if note is not None:
        question.answer_note = clean_text(note)[:MAX_ANSWER_LENGTH] or None
    if not question.answer_video_id and not question.answer_note:
        return "Please choose a video or write a short answer."
    question.status = "answered"
    question.answered_at = question.answered_at or datetime.utcnow()
    db.session.flush()
    notify_member_answered(question)
    return None


def mark_answered(question):
    """Answered outside the app (for example Vincent replied to the email). No email to the member."""
    question.status = "answered"
    question.answered_at = question.answered_at or datetime.utcnow()


def reopen(question):
    question.status, question.answered_at = "new", None


def _question_json(question, viewer, for_staff=False):
    """Every question sent to a browser goes through here, so the video is only ever described to its owner or staff."""
    return {**question.serialize(for_staff=for_staff), "member_video": qv.member_video_json(question, viewer)}


def _minutes(seconds):
    return f"{seconds // 60}:{seconds % 60:02d}"


def _email_vincent(user, question):
    lesson = question.lesson_video.title if question.lesson_video else "Not given"
    if question.lesson_video and question.video_time:
        lesson += f", at {question.video_time}"
    frontend = (os.getenv("FRONTEND_URL") or "").rstrip("/")
    backend = (os.getenv("BACKEND_URL") or "").rstrip("/")
    body = "\n".join([
        f"A member asked you a question in {SiteSettings.get().app_name}.",
        "",
        f"From:    {user.name or '(no name given)'}",
        f"Plan:    {question.member_plan}",
        f"Lesson:  {lesson}",
        f"Subject: {question.subject}",
        "",
        question.question,
        "",
        *([f"The member sent a video of their practice"
           f"{' (' + _minutes(question.member_video_seconds) + ' long)' if question.member_video_seconds else ''}. "
           f"Watch it in the Questions inbox (you will need to sign in).", ""] if question.member_video_key else []),
        "---",
        "To answer, just press Reply: your email goes straight to the member.",
        f"You can also open this question in the Questions inbox ({backend}/admin/questions/?q={question.id}) "
        f"and the answer will show under the member's My questions.",
        f"Lesson link: {frontend}/tai-chi-company/watch/{question.lesson_video.slug}" if question.lesson_video else "",
    ]).rstrip()
    return email(vincent_email(), f"Ask {teacher()}: {question.subject}", body, reply_to=user.email)


@tcc.route('/questions/allowance', methods=['GET'])
@role_required()
def question_allowance():
    """What the Ask Vincent page needs to know before showing the form."""
    user = get_current_user()
    remaining, next_at = _allowance(user)
    data = {"can_ask": user.is_paying_member, "per_week": QUESTIONS_PER_WEEK, "remaining": remaining,
            "next_at": next_at.isoformat() if next_at else None}
    if user.is_paying_member:
        per_month, videos_left, next_month = qv.videos_allowance(user)
        data.update(videos_per_month=per_month, videos_remaining=videos_left, videos_next_at=next_month.isoformat(),
                    video_max_seconds=qv.MAX_SECONDS, video_max_bytes=qv.MAX_BYTES)
    return jsonify(data)


def _free_member_refused(user):
    """Every video step checks this on the server: hiding the button is not enough."""
    if user.is_paying_member:
        return None
    return jsonify({"msg": f"Video feedback from {teacher()} is included with paid plans."}), 403


def _storage_problem(error):
    print(f"Question video storage problem: {error}")
    return jsonify({"msg": "We could not reach video storage just now. Please try again in a few minutes."}), 503


def _too_big_message():
    return f"This video is too big. Videos can be up to {qv.MAX_BYTES // 1024 ** 2} MB."


def _monthly_limit_message(per_month, next_month):
    return (f"You have sent {per_month} video{'' if per_month == 1 else 's'} this month, which is the most for one month. "
            f"You can send your next video on {_friendly_date(next_month)}. You can still send your question without a video.")


@tcc.route('/questions/video/upload-url', methods=['POST'])
@limiter.limit("20 per hour")
@role_required()
def question_video_upload_url():
    """Checks the plan and the limits, then gives the browser an address to send the file straight to private storage."""
    user = get_current_user()
    refused = _free_member_refused(user)
    if refused:
        return refused
    data = request.get_json(silent=True) or {}
    kind = qv.video_type(data.get("filename"), data.get("content_type"))
    if kind is None:
        return jsonify({"msg": "Please choose an MP4, MOV or WebM video."}), 400
    size, seconds = data.get("size"), data.get("seconds")
    if isinstance(size, bool) or not isinstance(size, int) or size <= 0:
        return jsonify({"msg": "We could not read the size of this video. Please choose it again."}), 400
    if size > qv.MAX_BYTES:
        return jsonify({"msg": _too_big_message()}), 400
    # The browser cannot read the length of every video, so an unknown length is allowed. The size limit always applies.
    if seconds is not None:
        if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or seconds <= 0:
            return jsonify({"msg": "We could not read the length of this video. Please choose it again."}), 400
        seconds = round(seconds)
        if seconds > qv.MAX_SECONDS:
            return jsonify({"msg": f"Please choose a video of {qv.MAX_SECONDS // 60} minutes or less."}), 400
    remaining, next_at = _allowance(user)
    if remaining <= 0:
        return jsonify({"msg": f"You have sent {QUESTIONS_PER_WEEK} questions this week. "
                               f"You can send your next question on {_friendly_date(next_at)}."}), 400
    per_month, videos_left, next_month = qv.videos_allowance(user)
    if videos_left <= 0:
        return jsonify({"msg": _monthly_limit_message(per_month, next_month), "video_limit": True}), 400

    ext, content_type = kind
    key = qv.new_key(ext)
    try:
        url = r2.presign_put(r2.masters_bucket(), key, content_type, seconds=qv.UPLOAD_URL_SECONDS)
    except qv.STORAGE_ERRORS as e:
        return _storage_problem(e)
    return jsonify({"upload_url": url, "content_type": content_type,
                    "upload_token": qv.make_upload_token(user, key, seconds)})


@tcc.route('/questions/video/confirm', methods=['POST'])
@limiter.limit("30 per hour")
@role_required()
def question_video_confirm():
    """After the upload: checks the real size in storage, and deletes the file if it is too big."""
    user = get_current_user()
    refused = _free_member_refused(user)
    if refused:
        return refused
    upload = qv.read_upload_token((request.get_json(silent=True) or {}).get("upload_token"), user)
    if upload is None:
        return jsonify({"msg": "This upload has expired. Please choose your video again."}), 400
    try:
        size = qv.stored_size(upload["key"])
        if size is None or size == 0:
            return jsonify({"msg": "Your video did not arrive. Please try again."}), 400
        if size > qv.MAX_BYTES:
            qv.delete_file(upload["key"])
            return jsonify({"msg": _too_big_message()}), 400
    except qv.STORAGE_ERRORS as e:
        return _storage_problem(e)
    return jsonify({"size": size})


@tcc.route('/questions/video/remove', methods=['POST'])
@limiter.limit("30 per hour")
@role_required()
def question_video_remove():
    """The member changed their mind before sending. A video already sent with a question cannot be removed here."""
    user = get_current_user()
    refused = _free_member_refused(user)
    if refused:
        return refused
    upload = qv.read_upload_token((request.get_json(silent=True) or {}).get("upload_token"), user)
    if upload is None:
        return jsonify({"msg": "This upload has expired."}), 400
    if qv.is_attached(upload["key"]):
        return jsonify({"msg": "This video was already sent."}), 400
    try:
        qv.delete_file(upload["key"])
    except qv.STORAGE_ERRORS as e:
        return _storage_problem(e)
    return jsonify({"msg": "Removed."})


def _attach_video(question, user, token):
    """Puts an uploaded video on a new question, checking everything again. Returns an error response, or None."""
    def problem(message, status=400, **extra):
        return jsonify({"msg": message, "video_problem": True, **extra}), status

    upload = qv.read_upload_token(token, user)
    if upload is None:
        return problem("Your video upload has expired. Please remove it and choose it again.")
    if qv.is_attached(upload["key"]):
        return problem("This video was already sent with another question. Please choose your video again.")
    per_month, videos_left, next_month = qv.videos_allowance(user)
    if videos_left <= 0:
        return problem(_monthly_limit_message(per_month, next_month), video_limit=True)
    try:
        size = qv.stored_size(upload["key"])
        if size is None or size == 0:
            return problem("Your video did not arrive. Please choose it again.")
        if size > qv.MAX_BYTES:
            qv.delete_file(upload["key"])
            return problem(_too_big_message())
    except qv.STORAGE_ERRORS as e:
        return _storage_problem(e)
    question.member_video_key = upload["key"]
    question.member_video_size = size
    question.member_video_seconds = upload.get("seconds")
    question.member_video_uploaded_at = datetime.utcnow()
    return None


@tcc.route('/questions', methods=['POST'])
@limiter.limit("10 per hour")
@role_required()
def ask_question():
    user = get_current_user()
    name = teacher()
    if not user.is_paying_member:
        return jsonify({"msg": f"Upgrade to ask {name} your questions. Asking is included with every paid plan."}), 403
    data = request.get_json(silent=True) or {}
    subject = clean_text(data.get("subject"), keep_newlines=False)
    text = clean_text(data.get("question"))
    if not subject:
        return jsonify({"msg": "Please write a short subject, for example \"Single Whip\"."}), 400
    if len(subject) > MAX_SUBJECT_LENGTH:
        return jsonify({"msg": f"Please keep the subject under {MAX_SUBJECT_LENGTH} characters."}), 400
    if len(text) < MIN_QUESTION_LENGTH:
        return jsonify({"msg": "Please write your question (at least a few words)."}), 400
    if len(text) > MAX_QUESTION_LENGTH:
        return jsonify({"msg": f"Please keep your question under {MAX_QUESTION_LENGTH} characters. "
                               f"Yours is {len(text)}."}), 400
    lesson = None
    if data.get("lesson_video_id"):
        try:
            lesson = visible_videos().filter(Video.id == int(data["lesson_video_id"])).first()
        except (TypeError, ValueError):
            lesson = None
        if lesson is None:
            return jsonify({"msg": "Please choose a lesson from the list, or leave it empty."}), 400
    video_time = _video_time(data.get("video_time"))
    if video_time is None:
        return jsonify({"msg": "Please write the time like this: 12:30 (minutes and seconds), or leave it empty."}), 400

    remaining, next_at = _allowance(user)
    if remaining <= 0:
        return jsonify({"msg": f"You have sent {QUESTIONS_PER_WEEK} questions this week, which is the most for one week. "
                               f"You can send your next question on {_friendly_date(next_at)}. Thank you for your patience!",
                        "weekly_limit": True, "next_at": next_at.isoformat() if next_at else None}), 400

    question = Question(user_id=user.id, subject=subject, question=text, lesson_video_id=lesson.id if lesson else None,
                        video_time=video_time or None, member_plan=user.plan_name)
    if data.get("video_token"):
        video_error = _attach_video(question, user, data["video_token"])
        if video_error:
            return video_error
    db.session.add(question)
    try:
        db.session.commit()
    except IntegrityError:  # the same video sent twice at the same moment
        db.session.rollback()
        return jsonify({"msg": "This video was already sent with another question. Please choose your video again.",
                        "video_problem": True}), 400
    if not _email_vincent(user, question):
        print(f"Question {question.id} saved but the email to the teacher did not go out")
    return jsonify({"msg": f"Thank you! {name} will answer as soon as he can.",
                    "question": _question_json(question, user), "remaining": remaining - 1,
                    "videos_remaining": qv.videos_allowance(user)[1]}), 201


@tcc.route('/questions/mine', methods=['GET'])
@role_required()
def my_questions():
    user = get_current_user()
    questions = Question.query.filter_by(user_id=user.id).order_by(Question.created_at.desc()).all()
    return jsonify([_question_json(q, user) for q in questions])


@tcc.route('/questions/<int:question_id>/video', methods=['GET'])
@limiter.limit("120 per hour")
@role_required()
def question_video(question_id):
    """A fresh watch address, for a page left open past the hour. Only the member who sent it, or staff."""
    user = get_current_user()
    question = db.session.get(Question, question_id)
    # The same answer whether or not the question exists, so nobody can probe for other members' questions
    if question is None or (not user.is_staff and question.user_id != user.id) or not question.member_video_key:
        return jsonify({"msg": "Video not found."}), 404
    if not user.is_staff:
        refused = _free_member_refused(user)
        if refused:
            return refused
    if question.member_video_deleted_at:
        return jsonify({"msg": qv.removed_note(question)}), 404
    data = qv.member_video_json(question, user)
    if not data or not data["watch_url"]:
        return jsonify({"msg": "We could not reach video storage just now. Please try again in a few minutes."}), 503
    return jsonify(data)


@tcc.route('/studio/questions', methods=['GET'])
@role_required("teacher", "admin")
def studio_questions():
    status = request.args.get("status")
    query = Question.query
    if status in ("new", "answered"):
        query = query.filter_by(status=status)
    questions = query.order_by(Question.created_at.desc()).limit(500).all()
    viewer = get_current_user()
    return jsonify([_question_json(q, viewer, for_staff=True) for q in questions])


@tcc.route('/studio/questions/<int:question_id>/answer', methods=['POST'])
@role_required("teacher", "admin")
def answer_question(question_id):
    """Link an existing corner video and/or write a short note, and mark the question answered."""
    question = db.session.get(Question, question_id)
    if question is None:
        return jsonify({"msg": "Question not found."}), 404
    data = request.get_json(silent=True) or {}
    error = save_answer(question, data.get("answer_note") if "answer_note" in data else None, data.get("video_id"))
    if error:
        db.session.rollback()
        return jsonify({"msg": error}), 400
    db.session.commit()
    return jsonify(_question_json(question, get_current_user(), for_staff=True))


@tcc.route('/studio/questions/<int:question_id>/reopen', methods=['POST'])
@role_required("teacher", "admin")
def reopen_question(question_id):
    question = db.session.get(Question, question_id)
    if question is None:
        return jsonify({"msg": "Question not found."}), 404
    reopen(question)
    db.session.commit()
    return jsonify(_question_json(question, get_current_user(), for_staff=True))
