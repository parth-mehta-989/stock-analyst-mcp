"""Cache factory."""

import logging

from stock_analyst.cache.base import Cache, NullCache
from stock_analyst.cache.csv_cache import CsvCache
from stock_analyst.cache.redis_cache import RedisCache
from stock_analyst.config import Settings

logger = logging.getLogger(__name__)


def get_cache(config: Settings) -> Cache:
    if config.cache_backend == "none":
        return NullCache()
    if config.cache_backend == "csv":
        return CsvCache(config.csv_cache_dir, config.cache_ttl)
    # redis with csv fallback
    try:
        cache = RedisCache(config.redis_url, config.cache_ttl)
        cache._client.ping()
        return cache
    except Exception:
        logger.warning("Redis unavailable. Start with: redis-server. Falling back to CSV cache.")
        return CsvCache(config.csv_cache_dir, config.cache_ttl)
