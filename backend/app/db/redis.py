import redis.asyncio as redis

from app.config import settings

# connection pool shared across the entire app
redis_pool: redis.Redis | None = None
redis_pool_binary: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    global redis_pool
    if redis_pool is None:
        redis_pool = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,  # redis responds in 'bytes' by default. setting this param true makes it convert those bytes to py str before returning
            max_connections=1000,  # creates a connection pool of 20 connections
        )
    return redis_pool


async def close_redis() -> None:
    global redis_pool
    if redis_pool is not None:
        await redis_pool.aclose()
        redis_pool = None


async def get_redis_binary() -> redis.Redis:
    """Redis client that does NOT decode responses. Use for binary data (Pub/Sub, Yjs)."""
    global redis_pool_binary
    if redis_pool_binary is None:
        redis_pool_binary = redis.from_url(settings.REDIS_URL)
    return redis_pool_binary


async def close_redis_binary() -> None:
    global redis_pool_binary
    if redis_pool_binary is not None:
        await redis_pool_binary.aclose()
        redis_pool_binary = None
