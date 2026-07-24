from httpx_oauth.clients.google import GoogleOAuth2

from app.core import BadRequestError
from app.core.config import get_auth_config
from app.schemas.auth import IssuedTokens
from app.services import AuthService

google_oauth_client = GoogleOAuth2(
    get_auth_config().GOOGLE_CLIENT_ID,
    get_auth_config().GOOGLE_CLIENT_SECRET,
)


async def get_google_url():
    return await google_oauth_client.get_authorization_url(
        get_auth_config().GOOGLE_REDIRECT_URI,
        scope=["openid", "email", "profile"],
    )


async def get_google_token(code: str, service: AuthService) -> IssuedTokens:
    token = await google_oauth_client.get_access_token(code, get_auth_config().GOOGLE_REDIRECT_URI)
    account_id, account_email = await google_oauth_client.get_id_email(token.get("access_token"))
    if account_email is None:
        raise BadRequestError("Google account has no email")
    return await service.google_callback(
        account_id=account_id,
        account_email=account_email,
        access_token=token["access_token"],
        expires_at=token.get("expires_at"),
    )
