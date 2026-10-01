import socketio

from app.core import get_auth_config, get_redis_config

sio = socketio.AsyncServer(
    async_mode="asgi",
    client_manager=socketio.AsyncRedisManager(get_redis_config().redis_url),
    cors_allowed_origins=get_auth_config().CORS_ORIGINS,
)
