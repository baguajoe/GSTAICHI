"""Encrypts each video's AES-128 key before it is stored in the database, using KEY_ENCRYPTION_SECRET.

The keys never go to R2. If the database leaked without the secret, the keys would still be unreadable.
Changing KEY_ENCRYPTION_SECRET makes every stored key unreadable, so videos would have to be re-encoded.
"""
import base64
import hashlib
import os
from cryptography.fernet import Fernet, InvalidToken


class KeyVaultError(Exception):
    pass


def _fernet():
    secret = os.getenv("KEY_ENCRYPTION_SECRET", "")
    if len(secret) < 32:
        raise KeyVaultError("KEY_ENCRYPTION_SECRET is missing or too short (it needs at least 32 characters).")
    # Any long random string works: hash it down to the 32 bytes Fernet needs
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest()))


def encrypt_key(key_bytes):
    if len(key_bytes) != 16:
        raise KeyVaultError("A video key must be exactly 16 bytes.")
    return _fernet().encrypt(key_bytes).decode()


def decrypt_key(token):
    try:
        key = _fernet().decrypt(token.encode())
    except InvalidToken as e:
        raise KeyVaultError("A stored video key could not be decrypted. Was KEY_ENCRYPTION_SECRET changed?") from e
    if len(key) != 16:
        raise KeyVaultError("A stored video key has the wrong length.")
    return key
