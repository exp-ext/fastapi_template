import redis.asyncio as aioredis
from redis.asyncio.client import Redis

from . import logger

logger = logger.getChild(__name__)


class AsyncRedisClient:
    _client: Redis = None

    @classmethod
    async def initialize(cls):
        from . import settings
        if cls._client is None:
            cls._client = await aioredis.from_url(
                f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}",
                max_connections=20,
                encoding="utf8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            logger.info("AsyncRedisClient is setting...")
        return cls._client

    @classmethod
    def get_client(cls) -> Redis:
        if cls._client is None:
            logger.error("AsyncRedisClient is not initialized.")
            raise RuntimeError("AsyncRedisClient has not been initialized. Please initialize the client before using it.")
        return cls._client


async def set_async_redis_client() -> Redis:
    client = await AsyncRedisClient.initialize()
    return client
