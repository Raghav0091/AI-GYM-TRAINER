import json
from typing import Any

import redis

from app.core.config import settings


class CacheUnavailable(RuntimeError):
    pass


def _client():
    return redis.from_url(settings.redis_url, decode_responses=True, socket_connect_timeout=2)


def set_cache(key: str, value: Any, ttl: int | None = None) -> bool:
    try:
        payload = json.dumps(value)
        _client().set(key, payload, ex=ttl)
        return True
    except redis.RedisError as exc:
        raise CacheUnavailable(f"Redis unavailable: {exc}") from exc


def get_cache(key: str) -> Any:
    try:
        value = _client().get(key)
    except redis.RedisError as exc:
        raise CacheUnavailable(f"Redis unavailable: {exc}") from exc

    return json.loads(value) if value else None


def delete_cache(key: str) -> bool:
    try:
        return bool(_client().delete(key))
    except redis.RedisError as exc:
        raise CacheUnavailable(f"Redis unavailable: {exc}") from exc
