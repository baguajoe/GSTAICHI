"""'Ask Vincent': paying members send questions; teachers answer, often with a short corner video."""
import os
from datetime import datetime
from flask import jsonify, request
from .models import db, Question, Video, SiteSettings, CORNER_SECTION
from .extensions import limiter
from .notify import email, notify_school, signature
from .tcc_auth import role_required, get_current_user
from .taichi_company import tcc

MAX_QUESTION_LENGTH = 2000


def notify_member_answered(question):
    """Emails the member once their answer can be watched (or read). Returns True if an email went out."""
    if question.member_notified_at or question.user is None:
        return False
    video = question.answer_video
    if video is not None and video.status != "ready":
        return False  # sent later by the worker, when the video is Ready
    settings = SiteSettings.get()
    frontend = (os.getenv("FRONTEND_URL") or "").rstrip("/")
    lines = [f"Hello{(' ' + question.user.name) if question.user.name else ''},", "",
             f"{settings.teacher_name} has answered your question:", "", f"\"{question.question[:500]}\"", ""]
    if question.answer_note:
        lines += [question.answer_note, ""]
    if video is not None:
        when = ""
        if video.publish_at and video.publish_at > datetime.utcnow():
            when = f" It will be available from {video.publish_at.strftime('%B %d, %Y')}."
        lines += [f"Watch the answer: {frontend}/tai-chi-company/watch/{video.slug}{when}", ""]
    else:
        lines += [f"See it in {settings.corner_name}: {frontend}/tai-chi-company/vincents-corner", ""]
    lines.append(signature())
    if email(question.user.email, f"{settings.teacher_name} answered your question", "\n".join(lines)):
        question.member_notified_at = datetime.utcnow()
        return True
    return False


@tcc.route('/questions', methods=['POST'])
@limiter.limit("5 per hour")
@role_required()
def ask_question():
    user = get_current_user()
    if not user.is_paying_member:
        return jsonify({"msg": "Asking questions is included with every plan. Please choose a plan first."}), 403
    text = ((request.get_json(silent=True) or {}).get("question") or "").strip()
    if len(text) < 10:
        return jsonify({"msg": "Please write your question (at least a few words)."}), 400
    if len(text) > MAX_QUESTION_LENGTH:
        return jsonify({"msg": f"Please keep your question under {MAX_QUESTION_LENGTH} characters."}), 400
    question = Question(user_id=user.id, question=text)
    db.session.add(question)
    db.session.commit()
    settings = SiteSettings.get()
    notify_school(f"New question for {settings.teacher_name}",
                  f"{user.name or ''} <{user.email}> asked:\n\n{text}\n\nAnswer it in the Studio: "
                  f"{(os.getenv('FRONTEND_URL') or '').rstrip('/')}/tai-chi-company/studio")
    return jsonify({"msg": f"Thank you! Your question has been sent to {settings.teacher_name}.",
                    "question": question.serialize()}), 201


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
    if data.get("video_id"):
        video = db.session.get(Video, int(data["video_id"]))
        if video is None or video.section != CORNER_SECTION:
            return jsonify({"msg": "Please choose one of the corner videos."}), 400
        question.answer_video_id = video.id
    if "answer_note" in data:
        question.answer_note = (data.get("answer_note") or "").strip()[:2000] or None
    if not question.answer_video_id and not question.answer_note:
        return jsonify({"msg": "Please choose a video or write a short answer."}), 400
    question.status = "answered"
    question.answered_at = datetime.utcnow()
    notify_member_answered(question)
    db.session.commit()
    return jsonify(question.serialize(for_staff=True))


@tcc.route('/studio/questions/<int:question_id>/reopen', methods=['POST'])
@role_required("teacher", "admin")
def reopen_question(question_id):
    question = db.session.get(Question, question_id)
    if question is None:
        return jsonify({"msg": "Question not found."}), 404
    question.status, question.answered_at = "new", None
    db.session.commit()
    return jsonify(question.serialize(for_staff=True))
