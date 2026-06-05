import redis.asyncio as aioredis
from config import REDIS_URL

_redis: aioredis.Redis | None = None


async def connect_redis():
    global _redis
    _redis = await aioredis.from_url(REDIS_URL, decode_responses=True)
    await _redis.ping()
    print("[Redis] Connected")


async def close_redis():
    global _redis
    if _redis:
        await _redis.aclose()
        print("[Redis] Connection closed")


def get_redis() -> aioredis.Redis:
    if _redis is None:
        raise RuntimeError("Redis not initialized. Call connect_redis() first.")
    return _redis


async def cache_set(key: str, value: str, ttl: int = 300) -> None:
    await get_redis().set(key, value, ex=ttl)


async def cache_get(key: str) -> str | None:
    return await get_redis().get(key)


async def cache_delete(key: str) -> None:
    await get_redis().delete(key)


async def rate_limit_check(key: str, max_calls: int, window: int) -> bool:
    r = get_redis()
    current = await r.incr(key)
    if current == 1:
        await r.expire(key, window)
    return current <= max_calls


async def enqueue_job(queue_name: str, payload: str) -> None:
    await get_redis().rpush(queue_name, payload)


async def dequeue_job(queue_name: str, timeout: int = 5) -> str | None:
    result = await get_redis().blpop(queue_name, timeout=timeout)
    if result:
        return result[1]
    return None
