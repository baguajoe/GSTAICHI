"""The member's private profile (Account page): name, photo, email address and email preferences.

Profiles are private. Nothing here (or anywhere in the app) lists members or shows one member to another;
every route works only on the signed-in member's own account.
"""
import io
import re
import secrets
from flask import jsonify, request
from flask_jwt_extended import create_access_token
from sqlalchemy import func
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
from .models import db, User, SiteSettings
from .extensions import limiter
from . import r2
from .notify import email, signature
from .tcc_auth import role_required, get_current_user
from .taichi_company import tcc
from .clean_input import clean_text

MAX_NAME_LENGTH = 120
MAX_PHOTO_UPLOAD_BYTES = 10 * 1024 * 1024  # what the member may send; it is stored much smaller
PHOTO_SIZE = 400  # pixels, longest side
EMAIL_PATTERN = re.compile(r"^[^@\s<>]+@[^@\s<>]+\.[^@\s<>]+$")


def _bad(msg, code=400):
    return jsonify({"msg": msg}), code


@tcc.route('/profile', methods=['PUT'])
@limiter.limit("60 per hour")
@role_required()
def update_profile():
    """Name and email preferences. Only the fields sent are changed."""
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    if "name" in data:
        name = clean_text(data.get("name"), keep_newlines=False)
        if len(name) > MAX_NAME_LENGTH:
            return _bad(f"Please keep your name under {MAX_NAME_LENGTH} characters.")
        user.name = name or None
    for field in ("email_new_videos", "email_answers"):
        if field in data:
            setattr(user, field, bool(data[field]))
    db.session.commit()
    return jsonify({"msg": "Saved.", "user": user.serialize_account()})


@tcc.route('/agree-terms', methods=['POST'])
@role_required()
def agree_terms():
    """The one-time "I agree" pop-up for members who joined before sign-up asked for it."""
    user = get_current_user()
    if user.agreed_terms_at is None:
        user.agreed_terms_at = datetime.utcnow()
        db.session.commit()
    return jsonify({"msg": "Thank you.", "user": user.serialize_account()})


@tcc.route('/change-email', methods=['POST'])
@limiter.limit("5 per hour")
@role_required()
def change_email():
    """A new email address needs the current password. The sign-in token carries the email, so a new one is
    returned; the old address gets a note in case someone else made the change."""
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    new_email = (data.get("new_email") or "").strip().lower()
    if not check_password_hash(user.password, data.get("password") or ""):
        return _bad("Your password is not correct.")
    if not EMAIL_PATTERN.match(new_email) or len(new_email) > 120:
        return _bad("Please enter a valid email address.")
    if new_email == user.email.lower():
        return _bad("That is already your email address.")
    if User.query.filter(func.lower(User.email) == new_email).first():
        return _bad("That email address is already used by another account.")
    old_email = user.email
    user.email = new_email
    db.session.commit()
    settings = SiteSettings.get()
    email(old_email, f"Your {settings.app_name} email address was changed",
          f"Hello{(' ' + user.name) if user.name else ''},\n\nThe email address for your {settings.app_name} account "
          f"was changed to {new_email}.\n\nIf you did not do this, please contact us right away.\n\n{signature()}")
    token = create_access_token(identity=user.email, expires_delta=timedelta(days=7))
    return jsonify({"msg": "Your email address has been changed. Use the new address to log in from now on.",
                    "token": token, "user": user.serialize_account()})


def _resize_photo(raw):
    """A square-ish small WebP, turned the right way up. Returns bytes, or None if it is not a picture."""
    from PIL import Image, ImageOps
    try:
        with Image.open(io.BytesIO(raw)) as img:
            img = ImageOps.exif_transpose(img)
            img = img.convert("RGB")
            # Crop to the middle square so it fits a round frame, then shrink
            side = min(img.size)
            left, top = (img.width - side) // 2, (img.height - side) // 2
            img = img.crop((left, top, left + side, top + side))
            img.thumbnail((PHOTO_SIZE, PHOTO_SIZE), Image.LANCZOS)
            out = io.BytesIO()
            img.save(out, format="WEBP", quality=82, method=4)
            return out.getvalue()
    except Exception as e:
        print(f"Profile photo could not be read: {e}")
        return None


def _delete_photo(path):
    if not path:
        return
    try:
        r2.delete_object(r2.streams_bucket(), path)
    except Exception as e:
        print(f"Old profile photo not deleted ({path}): {e}")


@tcc.route('/profile/photo', methods=['POST'])
@limiter.limit("20 per hour")
@role_required()
def upload_photo():
    """The picture is resized here and kept private: stored like article photos (members-only folder in the
    streams bucket) and shown only to its owner with a short-lived signed link."""
    user = get_current_user()
    upload = request.files.get("photo")
    if upload is None:
        return _bad("Please choose a picture.")
    raw = upload.read(MAX_PHOTO_UPLOAD_BYTES + 1)
    if len(raw) > MAX_PHOTO_UPLOAD_BYTES:
        return _bad("This picture is bigger than 10 MB. Please choose a smaller one.")
    small = _resize_photo(raw)
    if small is None:
        return _bad("We could not read that picture. Please choose a JPG or PNG photo.")
    path = f"article-private/{secrets.token_hex(12)}.webp"
    try:
        r2.put_bytes(r2.streams_bucket(), path, small, "image/webp")
    except Exception as e:
        print(f"Profile photo upload failed: {e}")
        return _bad("The picture could not be saved just now. Please try again later.", 503)
    old = user.photo_path
    user.photo_path = path
    db.session.commit()
    _delete_photo(old)
    return jsonify({"msg": "Your photo has been saved.", "user": user.serialize_account()})


@tcc.route('/profile/photo', methods=['DELETE'])
@role_required()
def delete_photo():
    user = get_current_user()
    old = user.photo_path
    user.photo_path = None
    db.session.commit()
    _delete_photo(old)
    return jsonify({"msg": "Your photo has been removed.", "user": user.serialize_account()})
