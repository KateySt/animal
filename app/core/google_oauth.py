from httpx_oauth.clients.google import GoogleOAuth2

from app.core.config import auth_config

google_oauth_client = GoogleOAuth2(
    auth_config.GOOGLE_CLIENT_ID,
    auth_config.GOOGLE_CLIENT_SECRET,
)
