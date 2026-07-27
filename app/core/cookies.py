from datetime import UTC, datetime

from fastapi import Response

from app.core.config import get_auth_config
from app.db import TokenType
from app.services.auth_service import IssuedTokens

REFRESH_COOKIE_PATH = "/api/v1/auth"


def set_refresh_cookie(response: Response, tokens: IssuedTokens) -> None:
    max_age = int((tokens.refresh_expires_at - datetime.now(UTC)).total_seconds())
    response.set_cookie(
        key=TokenType.refresh,
        value=tokens.refresh_token,
        max_age=max_age,
        httponly=True,
        secure=get_auth_config().COOKIE_SECURE,
        samesite="strict",
        path=REFRESH_COOKIE_PATH,
        domain=get_auth_config().COOKIE_DOMAIN,
    )


def delete_refresh_cookie(response: Response) -> None:
    response.delete_cookie(TokenType.refresh, path=REFRESH_COOKIE_PATH, domain=get_auth_config().COOKIE_DOMAIN)
