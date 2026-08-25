from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import jwt
from pwdlib import PasswordHash

from app.config import settings

PASSWORD_HASH = PasswordHash.recommended()
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return PASSWORD_HASH.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return PASSWORD_HASH.verify(password, password_hash)


def _encode_token(user_id: str, token_type: str, expires_delta: timedelta, jti: str | None = None) -> tuple[str, str]:
    now = datetime.now(timezone.utc)
    token_jti = jti or uuid4().hex
    payload: dict[str, Any] = {
        "sub": user_id,
        "type": token_type,
        "jti": token_jti,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM), token_jti


def create_access_token(user_id: str) -> str:
    token, _ = _encode_token(user_id, "access", timedelta(minutes=settings.access_token_minutes))
    return token


def create_refresh_token(user_id: str) -> tuple[str, str, datetime]:
    expires = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_days)
    token, jti = _encode_token(user_id, "refresh", timedelta(days=settings.refresh_token_days))
    return token, jti, expires


def decode_token(token: str, expected_type: str) -> dict[str, Any]:
    payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError("wrong token type")
    return payload


def new_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def csrf_matches(cookie_value: str | None, header_value: str | None) -> bool:
    if not cookie_value or not header_value:
        return False
    return hmac.compare_digest(cookie_value, header_value)


def fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
