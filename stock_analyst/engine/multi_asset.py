"""Multi-asset analysis: ETFs, indices, commodities, crypto, currencies."""

import logging
from typing import Any, Dict

import yfinance as yf

from stock_analyst.cache.base import Cache
from stock_analyst.config import Settings
from stock_analyst.engine.data_provider import DataProvider
from stock_analyst.engine.fundamentals import FundamentalAnalyzer
from stock_analyst.engine.technicals import TechnicalAnalyzer

logger = logging.getLogger(__name__)


class MultiAssetAnalyzer:
    """Analyze any asset class: stocks, ETFs, indices, commodities, crypto, currencies."""

    def __init__(self, provider: DataProvider, cache: Cache, config: Settings) -> None:
        self._provider = provider
        self._cache = cache
        self._config = config
        self._fa = FundamentalAnalyzer(provider, cache, config)
        self._ta = TechnicalAnalyzer(provider, cache, config)

    def analyze_asset(
        self,
        symbol: str,
        asset_type: str = "stock",
        include_fundamentals: bool = True,
        include_technicals: bool = True,
    ) -> Dict[str, Any]:
        """Analyze any asset: stock, etf, index, commodity, crypto, currency.
        
        Args:
            symbol: Ticker symbol (e.g., 'AAPL', 'SPY', 'GC=F', 'BTC-USD', 'EURUSD=X')
            asset_type: Type of asset (stock, etf, index, commodity, crypto, currency)
            include_fundamentals: Include fundamental ratios (not available for all assets)
            include_technicals: Include technical analysis
        
        Returns:
            Dict with available analysis
        """
        result: Dict[str, Any] = {
            "symbol": symbol,
            "asset_type": asset_type,
        }

        # Get basic info
        try:
            info = self._provider.get_info(symbol)
            result["name"] = info.get("longName") or info.get("shortName", "")
            result["currency"] = info.get("currency", "")
            result["current_price"] = info.get("currentPrice") or info.get("regularMarketPrice")
            result["market_cap"] = info.get("marketCap")
            result["sector"] = info.get("sector", "")
            result["industry"] = info.get("industry", "")
        except Exception as e:
            logger.debug("Failed to get info for %s: %s", symbol, e)

        # Fundamentals (skip for commodities, crypto, currencies if not available)
        if include_fundamentals:
            try:
                fundamentals = self._fa.fetch_all(symbol)
                if fundamentals and "ratio_input" in fundamentals:
                    from stock_analyst.fa.ratio_runner import run_ratios
                    result["fundamentals"] = run_ratios(fundamentals["ratio_input"], self._config)
            except Exception as e:
                logger.debug("Fundamentals failed for %s: %s", symbol, e)

        # Technicals (work for all assets with OHLCV data)
        if include_technicals:
            try:
                result["technicals"] = self._ta.analyze(symbol, period=self._config.default_period)
            except Exception as e:
                logger.debug("Technicals failed for %s: %s", symbol, e)

        return result

    def get_asset_info(self, symbol: str) -> Dict[str, Any]:
        """Get basic info for any asset."""
        try:
            info = self._provider.get_info(symbol)
            return {
                "symbol": symbol,
                "name": info.get("longName") or info.get("shortName", ""),
                "currency": info.get("currency", ""),
                "price": info.get("currentPrice") or info.get("regularMarketPrice"),
                "market_cap": info.get("marketCap"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "exchange": info.get("exchange"),
                "country": info.get("country"),
            }
        except Exception as e:
            logger.debug("Failed to get info for %s: %s", symbol, e)
            return {"symbol": symbol, "error": str(e)}
