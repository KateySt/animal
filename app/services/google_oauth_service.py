import httpx
from authlib.integrations.httpx_client import AsyncOAuth2Client

from app.core.config import get_auth_config

GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"


class GoogleOAuthService:
    def __init__(self) -> None:
        self._metadata: dict = {}
        self._jwks: dict = {}

    def _make_client(self) -> AsyncOAuth2Client:
        return AsyncOAuth2Client(
            client_id=get_auth_config().GOOGLE_CLIENT_ID,
            client_secret=get_auth_config().GOOGLE_CLIENT_SECRET,
            scope="openid email profile",
        )

    async def init(self) -> None:
        async with httpx.AsyncClient() as client:
            resp = await client.get(GOOGLE_DISCOVERY_URL)
            resp.raise_for_status()
            self._metadata = resp.json()

            resp = await client.get(self._metadata["jwks_uri"])
            resp.raise_for_status()
            self._jwks = resp.json()

    @property
    def metadata(self) -> dict:
        return self._metadata

    @property
    def jwks(self) -> dict:
        return self._jwks

    @property
    def client(self) -> AsyncOAuth2Client:
        return self._make_client()


google_oauth_service = GoogleOAuthService()
