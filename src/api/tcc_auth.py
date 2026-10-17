"""Role checks shared by the API blueprints. The JWT identity is the user's email."""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from sqlalchemy import func
from .models import User


def get_current_user(optional=False):
    """Returns the signed-in User, or None. With optional=True a missing token is not an error."""
    verify_jwt_in_request(optional=optional)
    identity = get_jwt_identity()
    if not identity:
        return None
    return User.query.filter(func.lower(User.email) == str(identity).lower()).first()


def role_required(*roles):
    """Decorator: allow only signed-in, non-suspended users whose role is in roles."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if user is None:
                return jsonify({"msg": "Please sign in."}), 401
            if user.is_suspended:
                return jsonify({"msg": "This account has been suspended. Please contact us for help."}), 403
            if roles and user.role not in roles:
                return jsonify({"msg": "You do not have permission to do that."}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator
