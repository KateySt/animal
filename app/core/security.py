import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
from jose import ExpiredSignatureError, JWTError, jwt

from app.core import UnauthorizedError
from app.core.config import auth_config
from app.db import TokenType


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(email: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": email,
        "iat": now,
        "exp": now + timedelta(minutes=auth_config.ACCESS_TOKEN_TIME_MINUTES),
        "type": TokenType.access,
    }
    return jwt.encode(payload, auth_config.JWT_SECRET, algorithm=auth_config.JWT_ALGORITHM)


def create_refresh_token(email: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": email,
        "iat": now,
        "exp": now + timedelta(minutes=auth_config.REFRESH_TOKEN_TIME_MINUTES),
        "jti": str(uuid.uuid4()),
        "type": TokenType.refresh,
    }
    return jwt.encode(payload, auth_config.JWT_SECRET, algorithm=auth_config.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, auth_config.JWT_SECRET, algorithms=[auth_config.JWT_ALGORITHM])
    except ExpiredSignatureError:
        raise UnauthorizedError("Token has expired")
    except JWTError:
        raise UnauthorizedError("Invalid token")

    return payload
