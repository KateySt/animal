from authlib.integrations.starlette_client import OAuth

from app.core.config import get_auth_config

oauth = OAuth()
oauth.register(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_id=get_auth_config().GOOGLE_CLIENT_ID,
    client_secret=get_auth_config().GOOGLE_CLIENT_SECRET,
    client_kwargs={"scope": "openid email profile", "code_challenge_method": "S256"},
)
