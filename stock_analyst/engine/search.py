"""Ticker search and lookup across regions."""

import logging
from typing import Any, Dict, List

import yfinance as yf

from stock_analyst.cache.base import Cache
from stock_analyst.config import Settings

logger = logging.getLogger(__name__)


class TickerSearch:
    def __init__(self, cache: Cache, config: Settings) -> None:
        self._cache = cache
        self._config = config

    def search(
        self,
        query: str,
        instrument_type: str = "stock",
        region: str | None = None,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """Search for tickers by name or symbol.
        
        Args:
            query: Search term (ticker or company name)
            instrument_type: Type of instrument (stock, etf, mutualfund, index, future, currency, cryptocurrency)
            region: Optional region filter (e.g., 'us', 'gb', 'in')
            limit: Max results
        
        Returns:
            Dict with search results
        """
        cache_key = f"search:{query}:{instrument_type}:{region}:{limit}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        try:
            lookup = yf.Lookup(query, raise_errors=False)
            results = []

            # Get results by instrument type
            if instrument_type == "stock":
                items = lookup.get_stock(count=limit * 2)
            elif instrument_type == "etf":
                items = lookup.get_etf(count=limit * 2)
            elif instrument_type == "mutualfund":
                items = lookup.get_mutualfund(count=limit * 2)
            elif instrument_type == "index":
                items = lookup.get_index(count=limit * 2)
            elif instrument_type == "future":
                items = lookup.get_future(count=limit * 2)
            elif instrument_type == "currency":
                items = lookup.get_currency(count=limit * 2)
            elif instrument_type == "cryptocurrency":
                items = lookup.get_cryptocurrency(count=limit * 2)
            else:
                items = lookup.get_all(count=limit * 2)

            if not items:
                return {
                    "query": query,
                    "instrument_type": instrument_type,
                    "region": region,
                    "count": 0,
                    "results": [],
                }

            # Filter by region if specified
            for item in items[:limit * 2]:
                item_region = item.get("region", "").lower()
                if region and item_region != region.lower():
                    continue
                results.append({
                    "symbol": item.get("symbol", ""),
                    "name": item.get("shortName") or item.get("longName", ""),
                    "exchange": item.get("exchange", ""),
                    "region": item.get("region", ""),
                    "instrument_type": item.get("typeDisp", instrument_type),
                })
                if len(results) >= limit:
                    break

            result = {
                "query": query,
                "instrument_type": instrument_type,
                "region": region,
                "count": len(results),
                "results": results,
            }

            self._cache.set(cache_key, result)
            return result

        except Exception as e:
            logger.debug("Ticker search failed: %s", e)
            return {
                "query": query,
                "instrument_type": instrument_type,
                "region": region,
                "count": 0,
                "results": [],
                "error": str(e),
            }
