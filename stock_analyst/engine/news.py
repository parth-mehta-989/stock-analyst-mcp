"""News headlines + analyst recommendations."""

import logging
from typing import Any, Dict, List

from stock_analyst.cache.base import Cache
from stock_analyst.config import Settings
from stock_analyst.engine.data_provider import DataProvider

logger = logging.getLogger(__name__)


class NewsAnalyzer:
    def __init__(self, provider: DataProvider, cache: Cache, config: Settings) -> None:
        self._provider = provider
        self._cache = cache
        self._config = config

    def analyze(self, symbol: str) -> Dict[str, Any]:
        cache_key = f"news:{symbol}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        result: Dict[str, Any] = {
            "symbol": symbol,
            "headlines": [],
            "recommendations": {},
        }

        # Headlines (latest 5)
        news_items = self._provider.get_news(symbol)
        for item in news_items[:5]:
            if isinstance(item, dict):
                result["headlines"].append({
                    "title": item.get("title", ""),
                    "publisher": item.get("publisher", ""),
                    "link": item.get("link", ""),
                })

        # Analyst recommendations summary
        recs = self._provider.get_recommendations(symbol)
        if recs is not None and not recs.empty:
            try:
                latest = recs.iloc[-1] if len(recs) > 0 else None
                if latest is not None:
                    rec_dict = {}
                    for col in recs.columns:
                        val = latest.get(col)
                        if val is not None:
                            rec_dict[col] = int(val) if isinstance(val, (int, float)) else str(val)
                    result["recommendations"] = rec_dict
            except Exception as e:
                logger.debug("Recommendations parse failed: %s", e)

        self._cache.set(cache_key, result)
        return result
