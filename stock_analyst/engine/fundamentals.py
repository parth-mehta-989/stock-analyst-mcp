"""Fundamental analysis: fetches raw data, maps to FA format, caches."""

import logging
from typing import Any, Dict

from stock_analyst.cache.base import Cache
from stock_analyst.config import Settings
from stock_analyst.engine.data_provider import DataProvider
from stock_analyst.engine.mapper import map_to_dcf_input, map_to_forecast_input, map_to_ratio_input

logger = logging.getLogger(__name__)


class FundamentalAnalyzer:
    def __init__(self, provider: DataProvider, cache: Cache, config: Settings) -> None:
        self._provider = provider
        self._cache = cache
        self._config = config

    def _cache_raw(self, symbol: str, data_type: str, data: Any) -> None:
        """Cache raw data for get_raw_data access."""
        key = f"raw:{symbol}:{data_type}"
        try:
            if hasattr(data, "to_dict"):
                self._cache.set(key, data.to_dict())
            elif isinstance(data, (dict, list)):
                self._cache.set(key, data)
        except Exception as e:
            logger.debug("Cache write failed for %s: %s", key, e)

    def fetch_all(self, symbol: str) -> Dict[str, Any]:
        """Fetch all fundamental data, cache raw, return mapped data."""
        cache_key = f"fundamentals:{symbol}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        info = self._provider.get_info(symbol)
        financials = self._provider.get_financials(symbol)
        balance_sheet = self._provider.get_balance_sheet(symbol)
        cashflow = self._provider.get_cashflow(symbol)

        # Cache raw data
        self._cache_raw(symbol, "info", info)
        self._cache_raw(symbol, "financials", financials)
        self._cache_raw(symbol, "balance_sheet", balance_sheet)
        self._cache_raw(symbol, "cashflow", cashflow)

        result = {
            "ratio_input": map_to_ratio_input(info, financials, balance_sheet, cashflow),
            "dcf_input": map_to_dcf_input(info, financials, balance_sheet, self._config),
            "forecast_input": map_to_forecast_input(financials, self._config),
            "info_summary": {
                "name": info.get("longName", symbol),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "current_price": info.get("currentPrice"),
                "market_cap": info.get("marketCap"),
                "currency": info.get("currency", "INR"),
            },
        }

        self._cache.set(cache_key, result)
        return result
