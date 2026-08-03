"""Market mood: region-specific indices + VIX/volatility context."""

import logging
import re
from typing import Any, Dict, Optional

import requests
import yfinance as yf
from bs4 import BeautifulSoup

from stock_analyst.cache.base import Cache
from stock_analyst.config import Settings

logger = logging.getLogger(__name__)

# Region -> (primary_index, vix_index)
_REGION_INDICES = {
    "us": ("^GSPC", "^VIX"),
    "gb": ("^FTSE", "^VIX"),
    "de": ("^GDAXI", "^VDAX"),
    "fr": ("^FCHI", "^VDAX"),
    "it": ("^FTSEMIB", "^VIX"),
    "es": ("^IBEX", "^VIX"),
    "nl": ("^AEX", "^VIX"),
    "ch": ("^SSMI", "^VIX"),
    "se": ("^OMXS30", "^VIX"),
    "jp": ("^N225", "^VIX"),
    "hk": ("^HSI", "^VIX"),
    "cn": ("^SSEC", "^VIX"),
    "sg": ("^STI", "^VIX"),
    "au": ("^AXJO", "^VIX"),
    "nz": ("^NZ50", "^VIX"),
    "in": ("^NSEI", "^INDIAVIX"),
    "br": ("^BVSP", "^VIX"),
    "mx": ("^MXX", "^VIX"),
    "ca": ("^GSPTSE", "^VIX"),
    "kr": ("^KS11", "^VIX"),
    "th": ("^SETI", "^VIX"),
    "my": ("^KLSE", "^VIX"),
}


def _mmi_label(value: float) -> str:
    """Classify MMI value into zone label."""
    if value < 30:
        return "Extreme Fear"
    if value < 50:
        return "Fear"
    if value <= 50:
        return "Neutral"
    if value <= 70:
        return "Greed"
    return "Extreme Greed"


def _fetch_index(symbol: str) -> Dict[str, Any]:
    """Fetch current price + day change for a yfinance index symbol."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        price = info.get("regularMarketPrice") or info.get("previousClose")
        prev = info.get("regularMarketPreviousClose") or info.get("previousClose")
        change = None
        change_pct = None
        if price and prev and prev > 0:
            change = round(price - prev, 2)
            change_pct = round((price - prev) / prev * 100, 2)
        return {
            "price": price,
            "previous_close": prev,
            "change": change,
            "change_pct": change_pct,
        }
    except Exception as e:
        logger.debug("Failed to fetch index %s: %s", symbol, e)
        return {"price": None, "previous_close": None, "change": None, "change_pct": None}


class MarketAnalyzer:
    def __init__(self, cache: Cache, config: Settings) -> None:
        self._cache = cache
        self._config = config

    def get_mood(self, region: str = "in") -> Dict[str, Any]:
        """Get market mood: region-specific indices + volatility."""
        cache_key = f"market_mood:{region}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        result: Dict[str, Any] = {
            "region": region,
            "primary_index": {},
            "volatility_index": {},
        }

        # Get region-specific indices
        primary_idx, vix_idx = _REGION_INDICES.get(region, ("^GSPC", "^VIX"))

        # 1. Primary index (e.g., Nifty 50 for India, S&P 500 for US)
        result["primary_index"] = _fetch_index(primary_idx)
        result["primary_index"]["symbol"] = primary_idx

        # 2. Volatility index (e.g., India VIX for India, VIX for US)
        result["volatility_index"] = _fetch_index(vix_idx)
        result["volatility_index"]["symbol"] = vix_idx

        # India-specific: try to get MMI from tickertape
        if region == "in":
            result["mmi"] = self._scrape_mmi()
        else:
            result["mmi"] = {"value": None, "label": "unknown", "source": "none"}

        # Overall assessment based on volatility
        vix_price = result["volatility_index"].get("price")
        mmi_val = result["mmi"].get("value")

        assessment = "unknown"
        if mmi_val is not None:
            if mmi_val < 30:
                assessment = "Markets oversold, potential buying opportunity"
            elif mmi_val < 50:
                assessment = "Cautious sentiment, watch for direction"
            elif mmi_val <= 70:
                assessment = "Greedy sentiment, be selective"
            else:
                assessment = "Markets overbought, avoid fresh positions"
        elif vix_price is not None:
            if vix_price > 25:
                assessment = "High volatility — fear in market"
            elif vix_price > 18:
                assessment = "Moderate volatility — cautious"
            else:
                assessment = "Low volatility — calm market"

        result["assessment"] = assessment

        self._cache.set(cache_key, result)
        return result

    def _scrape_mmi(self) -> Dict[str, Any]:
        """Scrape tickertape.in for Market Mood Index value."""
        try:
            resp = requests.get(
                self._config.market_mood_url,
                headers={"User-Agent": self._config.http_user_agent},
                timeout=self._config.http_timeout,
            )
            if resp.status_code != 200:
                logger.debug("Tickertape MMI returned %d", resp.status_code)
                return {"value": None, "label": "unknown", "source": "tickertape"}

            soup = BeautifulSoup(resp.content, "html.parser")
            text = soup.get_text(separator=" ", strip=True)

            # Look for the MMI numeric value — pattern like "73.22"
            # near "Market Mood Index" or "MMI"
            mmi_val = None

            # Strategy 1: find the value near "zone" text
            zone_match = re.search(
                r"(?:Extreme\s+(?:Fear|Greed)|Fear|Greed|Neutral)\s*(?:zone)?\s*(\d+\.?\d*)",
                text, re.IGNORECASE
            )
            if zone_match:
                mmi_val = float(zone_match.group(1))

            # Strategy 2: broader search for standalone decimal near MMI
            if mmi_val is None:
                val_match = re.search(r"MMI[^0-9]*?(\d{1,2}\.\d{1,2})", text, re.IGNORECASE)
                if val_match:
                    mmi_val = float(val_match.group(1))

            if mmi_val is not None:
                return {
                    "value": mmi_val,
                    "label": _mmi_label(mmi_val),
                    "source": "tickertape",
                }

            logger.debug("Could not parse MMI value from tickertape page")
            return {"value": None, "label": "unknown", "source": "tickertape"}

        except Exception as e:
            logger.debug("Tickertape MMI scrape failed: %s", e)
            return {"value": None, "label": "unknown", "source": "tickertape"}
