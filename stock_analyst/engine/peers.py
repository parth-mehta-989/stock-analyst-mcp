"""Peer discovery via yfinance Industry API + screener.in fallback."""

import logging
import time
from typing import Any, Dict, List

import requests
import yfinance as yf
from bs4 import BeautifulSoup

from stock_analyst.cache.base import Cache
from stock_analyst.config import Settings
from stock_analyst.engine.data_provider import DataProvider

logger = logging.getLogger(__name__)


def _strip_exchange(symbol: str) -> str:
    """Remove .NS / .BO suffix and normalize."""
    return symbol.upper().strip().replace(".NS", "").replace(".BO", "")


class PeerAnalyzer:
    def __init__(self, provider: DataProvider, cache: Cache, config: Settings) -> None:
        self._provider = provider
        self._cache = cache
        self._config = config

    def discover_peers(self, symbol: str) -> List[str]:
        """Discover peer symbols. Tries yfinance Industry API first, screener.in second."""
        cache_key = f"peers_list:{symbol}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        peers: List[str] = self._yfinance_industry(symbol)

        if not peers and self._config.screener_enabled:
            peers = self._scrape_screener(symbol)

        # Remove the target stock from peers
        raw_sym = _strip_exchange(symbol)
        peers = [p for p in peers if _strip_exchange(p) != raw_sym][:self._config.peers_max_count]

        self._cache.set(cache_key, peers)
        return peers

    def _yfinance_industry(self, symbol: str) -> List[str]:
        """Discover peers via yfinance Industry top_companies (region=IN)."""
        try:
            info = self._provider.get_info(symbol)
            industry_key = info.get("industryKey", "")
            if not industry_key:
                logger.debug("No industryKey for %s", symbol)
                return []

            industry = yf.Industry(industry_key, region="IN")
            top = industry.top_companies
            if top is None or top.empty:
                logger.debug("No top_companies for industry %s", industry_key)
                return []

            # index is symbol (e.g. TCS.NS), extract raw ticker
            return [_strip_exchange(sym) for sym in top.index.tolist()]
        except Exception as e:
            logger.debug("yfinance Industry peer discovery failed: %s", e)
            return []

    def _scrape_screener(self, symbol: str) -> List[str]:
        """Scrape screener.in for peer list. Best-effort fallback."""
        raw_sym = _strip_exchange(symbol)
        url = f"{self._config.screener_base_url}/{raw_sym}/"
        try:
            resp = requests.get(
                url,
                headers={"User-Agent": self._config.http_user_agent},
                timeout=self._config.screener_timeout,
            )
            if resp.status_code != 200:
                logger.debug("Screener.in returned %d for %s", resp.status_code, raw_sym)
                return []

            soup = BeautifulSoup(resp.content, "html.parser")
            peer_section = soup.find("section", {"id": "peers"})
            if not peer_section:
                return []

            # Try table first (legacy DOM)
            table = peer_section.find("table", {"class": "data-table"})
            if table:
                peers = []
                for row in table.find_all("tr")[1:]:
                    link = row.find("a")
                    if link and link.get("href"):
                        parts = link["href"].strip("/").split("/")
                        if len(parts) >= 2:
                            peers.append(parts[1])
                if peers:
                    time.sleep(self._config.screener_delay)
                    return peers

            # Fallback: extract company links from peer section
            peers = []
            for link in peer_section.find_all("a", href=True):
                href = link["href"]
                if href.startswith("/company/") and not href.startswith("/company/CN") and not href.startswith("/company/1"):
                    parts = href.strip("/").split("/")
                    if len(parts) >= 2 and parts[1].isalpha():
                        peers.append(parts[1])

            time.sleep(self._config.screener_delay)
            return peers

        except Exception as e:
            logger.debug("Screener.in scraping failed: %s", e)
            return []

    def get_peer_fundamentals(self, symbol: str, peers: List[str]) -> Dict[str, Any]:
        """Fetch fundamental metrics for target + peers for comparison."""
        cache_key = f"peer_fundamentals:{symbol}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        all_symbols = [symbol] + peers
        results = {}

        for sym in all_symbols:
            try:
                info = self._provider.get_info(sym)
                results[_strip_exchange(sym)] = {
                    "pe": info.get("trailingPE"),
                    "pb": info.get("priceToBook"),
                    "roe": info.get("returnOnEquity"),
                    "debt_to_equity": info.get("debtToEquity"),
                    "dividend_yield": info.get("dividendYield"),
                    "market_cap": info.get("marketCap"),
                    "net_margin": info.get("profitMargins"),
                    "revenue_growth": info.get("revenueGrowth"),
                    "operating_margin": info.get("operatingMargins"),
                    "roa": info.get("returnOnAssets"),
                    "current_price": info.get("currentPrice"),
                    "name": info.get("longName", sym),
                }
            except Exception as e:
                logger.debug("Failed to fetch peer %s: %s", sym, e)

        self._cache.set(cache_key, results)
        return results

    def get_peer_technicals(self, symbol: str, peers: List[str]) -> Dict[str, Any]:
        """Fetch technical signals for target + peers."""
        cache_key = f"peer_technicals:{symbol}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        # Import here to avoid circular dependency
        from stock_analyst.engine.technicals import TechnicalAnalyzer

        ta_analyzer = TechnicalAnalyzer(self._provider, self._cache, self._config)
        all_symbols = [symbol] + peers
        results = {}

        for sym in all_symbols:
            try:
                tech = ta_analyzer.analyze(sym)
                clean_sym = _strip_exchange(sym)
                results[clean_sym] = {
                    k: tech.get(k)
                    for k in ["current_price", "rsi", "rsi_signal", "ema_trend",
                              "macd_signal", "overall_signal", "price_vs_52w_high_pct"]
                }
                # price vs EMA200
                results[clean_sym]["price_vs_ema200"] = None
                ema200 = tech.get("ema_200")
                cp = tech.get("current_price")
                if ema200 and cp and ema200 > 0:
                    results[clean_sym]["price_vs_ema200"] = round((cp - ema200) / ema200 * 100, 2)
            except Exception as e:
                logger.debug("Failed technical for peer %s: %s", sym, e)

        self._cache.set(cache_key, results)
        return results
