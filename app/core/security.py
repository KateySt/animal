import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

from app.core import ForbiddenError
from app.core.config import get_auth_config
from app.db import TokenType
from app.db.models import User


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(user: User, scopes: list[str] | None = None) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user.id),
        "scopes": scopes or [],
        "pv": user.permissions_version,
        "is_superuser": user.is_superuser,
        "type": TokenType.access,
        "iat": now,
        "exp": now + timedelta(minutes=get_auth_config().ACCESS_TOKEN_TIME_MINUTES),
    }
    return jwt.encode(payload, get_auth_config().ACCESS_TOKEN_SECRET, algorithm=get_auth_config().JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, get_auth_config().ACCESS_TOKEN_SECRET, algorithms=[get_auth_config().JWT_ALGORITHM])
    except jwt.PyJWTError:
        raise ForbiddenError("Invalid or expired token")


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
