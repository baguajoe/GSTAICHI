"""Shared Flask extensions, created here so blueprints can import them without circular imports."""
import os
from flask import request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["500 per day", "25 per minute"],
    storage_uri=os.getenv("REDIS_URL", "memory://"),
)


@limiter.request_filter
def _skip_static_files():
    # Admin pages load many CSS/JS files; don't count those against the limit
    return request.path.startswith("/admin/static") or request.path.startswith("/static")
