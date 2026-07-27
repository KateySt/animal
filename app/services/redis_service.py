import datetime

import redis.asyncio as redis
from redis.asyncio import ConnectionPool

from app.core import get_redis_config


class RedisService:
    def __init__(self):
        self._pool = ConnectionPool(
            host=get_redis_config().REDIS_HOST,
            port=get_redis_config().REDIS_PORT,
            password=get_redis_config().REDIS_PASSWORD,
            decode_responses=False,
            max_connections=10,
        )
        self.redis = redis.Redis(connection_pool=self._pool)

    async def close(self):
        await self._pool.disconnect()

    async def set_cache(self, key: str, value: str | int, ttl: int = 60) -> None:
        await self.redis.setex(key, datetime.timedelta(seconds=ttl), value)

    async def get_cache(self, key: str) -> str | None:
        return await self.redis.get(key)

    async def delete_cache(self, key: str) -> None:
        await self.redis.delete(key)


redis_service = RedisService()
