"""Stock screener: yfinance EquityQuery primary, NSE CSV + screener.in fallbacks."""

import io
import logging
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
import yfinance as yf
from bs4 import BeautifulSoup
from yfinance import EquityQuery

from stock_analyst.cache.base import Cache
from stock_analyst.config import Settings

logger = logging.getLogger(__name__)

# Maps user-friendly filter keys to EquityQuery field names
_FILTER_MAP: Dict[str, str] = {
    "market_cap_min": "intradaymarketcap",
    "market_cap_max": "intradaymarketcap",
    "pe_min": "peratio.lasttwelvemonths",
    "pe_max": "peratio.lasttwelvemonths",
    "pb_min": "pricebookratio.quarterly",
    "pb_max": "pricebookratio.quarterly",
    "roe_min": "returnonequity.lasttwelvemonths",
    "roe_max": "returnonequity.lasttwelvemonths",
    "dividend_yield_min": "forward_dividend_yield",
    "dividend_yield_max": "forward_dividend_yield",
    "revenue_growth_min": "totalrevenues1yrgrowth.lasttwelvemonths",
    "revenue_growth_max": "totalrevenues1yrgrowth.lasttwelvemonths",
    "debt_to_equity_max": "totaldebtequity.lasttwelvemonths",
    "debt_to_equity_min": "totaldebtequity.lasttwelvemonths",
    "current_ratio_min": "currentratio.lasttwelvemonths",
    "current_ratio_max": "currentratio.lasttwelvemonths",
    "52w_change_min": "fiftytwowkpercentchange",
    "52w_change_max": "fiftytwowkpercentchange",
    "beta_min": "beta",
    "beta_max": "beta",
}

# Sortable fields mapping
_SORT_MAP: Dict[str, str] = {
    "market_cap": "intradaymarketcap",
    "pe": "peratio.lasttwelvemonths",
    "pb": "pricebookratio.quarterly",
    "roe": "returnonequity.lasttwelvemonths",
    "dividend_yield": "forward_dividend_yield",
    "revenue_growth": "totalrevenues1yrgrowth.lasttwelvemonths",
    "price": "intradayprice",
    "change": "percentchange",
    "volume": "dayvolume",
    "ticker": "ticker",
}


def _build_equity_query(filters: Dict[str, Any]) -> EquityQuery:
    """Build EquityQuery from user-friendly filter dict."""
    conditions: List[EquityQuery] = []

    # Always filter to India region
    conditions.append(EquityQuery("eq", ["region", "in"]))

    # Sector / industry (equality)
    if "sector" in filters:
        conditions.append(EquityQuery("eq", ["sector", filters["sector"]]))
    if "industry" in filters:
        conditions.append(EquityQuery("eq", ["industry", filters["industry"]]))

    # Numeric range filters
    for key, value in filters.items():
        if key in ("sector", "industry"):
            continue
        field = _FILTER_MAP.get(key)
        if not field:
            continue
        if key.endswith("_min"):
            conditions.append(EquityQuery("gte", [field, float(value)]))
        elif key.endswith("_max"):
            conditions.append(EquityQuery("lte", [field, float(value)]))

    if len(conditions) == 1:
        return conditions[0]
    return EquityQuery("and", conditions)


class StockScreener:
    def __init__(self, cache: Cache, config: Settings) -> None:
        self._cache = cache
        self._config = config

    def screen(
        self,
        filters: Dict[str, Any],
        sort_by: str = "market_cap",
        sort_asc: bool = False,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Screen stocks by criteria. Tries yfinance -> NSE CSV -> screener.in."""
        limit = limit or self._config.screener_max_results

        # Try yfinance EquityQuery first
        result = self._yfinance_screen(filters, sort_by, sort_asc, limit)
        if result["stocks"]:
            return result

        # Fallback: screener.in
        if self._config.screener_enabled:
            result = self._screener_in_screen(filters, limit)
            if result["stocks"]:
                return result

        return {
            "source": "none",
            "count": 0,
            "filters_applied": filters,
            "stocks": [],
            "message": "No stocks matched the given filters from any source.",
        }

    def _yfinance_screen(
        self,
        filters: Dict[str, Any],
        sort_by: str,
        sort_asc: bool,
        limit: int,
    ) -> Dict[str, Any]:
        """Screen using yfinance EquityQuery."""
        try:
            query = _build_equity_query(filters)
            sort_field = _SORT_MAP.get(sort_by, "intradaymarketcap")

            response = yf.screen(
                query,
                sortField=sort_field,
                sortAsc=sort_asc,
                _size=min(limit, 250),
            )

            if not response or "quotes" not in response:
                logger.debug("yfinance screen returned empty response")
                return {"source": "yfinance", "count": 0, "stocks": []}

            stocks = []
            for quote in response["quotes"][:limit]:
                stocks.append({
                    "symbol": quote.get("symbol", ""),
                    "name": quote.get("longName") or quote.get("shortName", ""),
                    "exchange": quote.get("exchange", ""),
                    "sector": quote.get("sector", ""),
                    "industry": quote.get("industry", ""),
                    "market_cap": quote.get("marketCap"),
                    "current_price": quote.get("regularMarketPrice"),
                    "pe": quote.get("trailingPE"),
                    "pb": quote.get("priceToBook"),
                    "dividend_yield": quote.get("dividendYield"),
                    "52w_change_pct": quote.get("fiftyTwoWeekChangePercent"),
                })

            return {
                "source": "yfinance",
                "count": len(stocks),
                "filters_applied": filters,
                "stocks": stocks,
            }
        except Exception as e:
            logger.debug("yfinance screen failed: %s", e)
            return {"source": "yfinance", "count": 0, "stocks": []}

    def _screener_in_screen(
        self,
        filters: Dict[str, Any],
        limit: int,
    ) -> Dict[str, Any]:
        """Fallback: scrape screener.in raw screen."""
        try:
            query_parts = []
            if "market_cap_min" in filters:
                query_parts.append(f"Market Capitalization >{filters['market_cap_min']}")
            if "market_cap_max" in filters:
                query_parts.append(f"Market Capitalization<{filters['market_cap_max']}")
            if "pe_max" in filters:
                query_parts.append(f"Price to Earning <{filters['pe_max']}")
            if "roe_min" in filters:
                query_parts.append(f"Return on equity >{filters['roe_min']}")

            if not query_parts:
                return {"source": "screener.in", "count": 0, "stocks": []}

            query_str = " AND\n".join(query_parts)
            params = {
                "sort": "",
                "order": "",
                "query": query_str,
                "latest": "on",
            }

            resp = requests.get(
                self._config.screener_screen_url,
                params=params,
                headers={"User-Agent": self._config.http_user_agent},
                timeout=self._config.screener_timeout,
            )
            if resp.status_code != 200:
                logger.debug("screener.in screen returned %d", resp.status_code)
                return {"source": "screener.in", "count": 0, "stocks": []}

            soup = BeautifulSoup(resp.content, "html.parser")
            table = soup.find("table", {"class": "data-table"})
            if not table:
                return {"source": "screener.in", "count": 0, "stocks": []}

            stocks = []
            for row in table.find_all("tr")[1:limit + 1]:
                cols = row.find_all("td")
                if len(cols) < 2:
                    continue
                link = cols[1].find("a") if len(cols) > 1 else cols[0].find("a")
                if not link:
                    continue
                href = link.get("href", "")
                parts = href.strip("/").split("/")
                sym = parts[1] if len(parts) >= 2 else ""
                name = link.get_text(strip=True)
                stocks.append({
                    "symbol": f"{sym}.NS" if sym and not sym[0].isdigit() else sym,
                    "name": name,
                })

            return {
                "source": "screener.in",
                "count": len(stocks),
                "filters_applied": filters,
                "stocks": stocks,
            }
        except Exception as e:
            logger.debug("screener.in screen failed: %s", e)
            return {"source": "screener.in", "count": 0, "stocks": []}

    @staticmethod
    def available_filters() -> Dict[str, Any]:
        """Return available filter keys and their descriptions."""
        return {
            "filters": {
                "sector": "Sector name (e.g., 'Technology', 'Healthcare')",
                "industry": "Industry name (e.g., 'Software—Infrastructure')",
                "market_cap_min": "Min market cap (in local currency units)",
                "market_cap_max": "Max market cap",
                "pe_min": "Min trailing P/E ratio",
                "pe_max": "Max trailing P/E ratio",
                "pb_min": "Min price-to-book ratio",
                "pb_max": "Max price-to-book ratio",
                "roe_min": "Min return on equity (decimal, e.g., 0.15 = 15%)",
                "roe_max": "Max return on equity",
                "dividend_yield_min": "Min forward dividend yield (decimal)",
                "dividend_yield_max": "Max forward dividend yield",
                "revenue_growth_min": "Min YoY revenue growth (decimal)",
                "revenue_growth_max": "Max YoY revenue growth",
                "debt_to_equity_min": "Min debt-to-equity ratio",
                "debt_to_equity_max": "Max debt-to-equity ratio",
                "current_ratio_min": "Min current ratio",
                "current_ratio_max": "Max current ratio",
                "52w_change_min": "Min 52-week price change %",
                "52w_change_max": "Max 52-week price change %",
                "beta_min": "Min beta",
                "beta_max": "Max beta",
            },
            "sort_options": list(_SORT_MAP.keys()),
        }
