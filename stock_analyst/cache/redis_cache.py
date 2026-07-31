"""Redis cache implementation."""

import json
from typing import Any, Optional

import redis

from stock_analyst.cache.base import Cache


class RedisCache(Cache):
    def __init__(self, url: str, default_ttl: int = 3600) -> None:
        self._client = redis.from_url(url, decode_responses=True)
        self._default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        raw = self._client.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        ttl = ttl or self._default_ttl
        self._client.setex(key, ttl, json.dumps(value, default=str))

    def exists(self, key: str) -> bool:
        return bool(self._client.exists(key))
