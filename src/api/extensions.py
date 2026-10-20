"""Shared Flask extensions, created here so blueprints can import them without circular imports."""
import os
from flask import request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    # Generous default: a page load makes several API calls and the video player sends heartbeats.
    # Sensitive endpoints (login, keys, play, articles) set their own tighter limits.
    default_limits=["3000 per day", "60 per minute"],
    storage_uri=os.getenv("REDIS_URL") or "memory://",
)


@limiter.request_filter
def _skip_static_files():
    # Only the API and /admin are rate limited. The React bundle, images and admin CSS/JS
    # are served by the same app and a single page can load dozens of them.
    path = request.path
    if path.startswith("/admin/static"):
        return True
    return not (path.startswith("/api") or path.startswith("/admin"))
