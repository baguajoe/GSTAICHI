"""Signed playback tokens shared with the Cloudflare Worker (cloudflare-worker/src/index.js).

Token format: <expiry unix seconds>.<playback session id>.<signature>
signature = base64url(HMAC-SHA256(MEDIA_TOKEN_SECRET, "<expiry>.<session id>.<slug>")), no padding.
The slug is signed but not included, so a token only opens files inside that one video's folder.
"""
import base64
import hashlib
import hmac
import os
import time


class MediaTokenError(Exception):
    pass


def _secret():
    secret = os.getenv("MEDIA_TOKEN_SECRET", "")
    if len(secret) < 32:
        raise MediaTokenError("MEDIA_TOKEN_SECRET is missing or too short (it needs at least 32 characters).")
    return secret.encode()


def _signature(expires, session_id, slug):
    digest = hmac.new(_secret(), f"{expires}.{session_id}.{slug}".encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")


def sign_media_token(slug, session_id, ttl_seconds):
    expires = int(time.time()) + int(ttl_seconds)
    return f"{expires}.{session_id}.{_signature(expires, session_id, slug)}"


def verify_media_token(token, slug):
    """Returns the playback session id if the token is valid for this slug and not expired, else None."""
    try:
        expires_str, session_id, signature = (token or "").split(".")
        expires = int(expires_str)
    except ValueError:
        return None
    if expires < time.time():
        return None
    if not hmac.compare_digest(signature, _signature(expires, session_id, slug)):
        return None
    return session_id


def sign_report(body_bytes):
    """Signature the Worker puts on segment usage reports (header X-Report-Signature)."""
    return hmac.new(_secret(), body_bytes, hashlib.sha256).hexdigest()
