"""'Ask Vincent': paying members send questions; Vincent answers by email (Reply-To is the member), in /admin,
or in the Studio, often with a short corner video. Members see their questions and answers on the Account page."""
import os
import re
from datetime import datetime, timedelta
from flask import jsonify, request
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
        "---",
        "To answer, just press Reply: your email goes straight to the member.",
        f"You can also answer in the Questions inbox ({backend}/admin/questions/) and the answer will show "
        f"under the member's My questions.",
        f"Lesson link: {frontend}/tai-chi-company/watch/{question.lesson_video.slug}" if question.lesson_video else "",
    ]).rstrip()
    return email(vincent_email(), f"Ask {teacher()}: {question.subject}", body, reply_to=user.email)


@tcc.route('/questions/allowance', methods=['GET'])
@role_required()
def question_allowance():
    """What the Ask Vincent page needs to know before showing the form."""
    user = get_current_user()
    remaining, next_at = _allowance(user)
    return jsonify({"can_ask": user.is_paying_member, "per_week": QUESTIONS_PER_WEEK, "remaining": remaining,
                    "next_at": next_at.isoformat() if next_at else None})


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
    db.session.add(question)
    db.session.commit()
    if not _email_vincent(user, question):
        print(f"Question {question.id} saved but the email to the teacher did not go out")
    return jsonify({"msg": f"Thank you! {name} will answer as soon as he can.",
                    "question": question.serialize(), "remaining": remaining - 1}), 201


@tcc.route('/questions/mine', methods=['GET'])
@role_required()
def my_questions():
    user = get_current_user()
    questions = Question.query.filter_by(user_id=user.id).order_by(Question.created_at.desc()).all()
    return jsonify([q.serialize() for q in questions])


@tcc.route('/studio/questions', methods=['GET'])
@role_required("teacher", "admin")
def studio_questions():
    status = request.args.get("status")
    query = Question.query
    if status in ("new", "answered"):
        query = query.filter_by(status=status)
    questions = query.order_by(Question.created_at.desc()).limit(500).all()
    return jsonify([q.serialize(for_staff=True) for q in questions])


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
    return jsonify(question.serialize(for_staff=True))


@tcc.route('/studio/questions/<int:question_id>/reopen', methods=['POST'])
@role_required("teacher", "admin")
def reopen_question(question_id):
    question = db.session.get(Question, question_id)
    if question is None:
        return jsonify({"msg": "Question not found."}), 404
    reopen(question)
    db.session.commit()
    return jsonify(question.serialize(for_staff=True))
