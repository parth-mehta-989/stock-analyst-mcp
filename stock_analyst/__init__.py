"""Stock Analyst — Indian stock market analysis tool."""

import logging
from typing import Any, Dict, List, Optional

from stock_analyst.analysis.formatter import to_json, to_markdown
from stock_analyst.analysis.peer_comparison import build_peer_comparison
from stock_analyst.analysis.report import StockReport
from stock_analyst.cache import get_cache
from stock_analyst.config import Settings, get_settings
from stock_analyst.engine.data_provider import get_provider
from stock_analyst.engine.fundamentals import FundamentalAnalyzer
from stock_analyst.engine.news import NewsAnalyzer
from stock_analyst.engine.peers import PeerAnalyzer
from stock_analyst.engine.technicals import TechnicalAnalyzer
from stock_analyst.fa.dcf_runner import run_dcf
from stock_analyst.fa.forecast_runner import run_forecast
from stock_analyst.fa.ratio_runner import run_ratios

logger = logging.getLogger(__name__)

_config: Optional[Settings] = None
_cache = None
_provider = None


def _init():
    global _config, _cache, _provider
    if _config is None:
        _config = get_settings()
        _cache = get_cache(_config)
        _provider = get_provider(_config)


def analyze(symbol: str, include_peers: bool = True) -> Dict[str, Any]:
    """Full analysis: fundamentals + technicals + peers + DCF + forecast + news."""
    _init()
    report = _build_report(symbol, include_peers=include_peers)
    return report.to_dict()


def get_fundamentals(symbol: str) -> Dict[str, Any]:
    """Financial ratios only."""
    _init()
    fa = FundamentalAnalyzer(_provider, _cache, _config)
    data = fa.fetch_all(symbol)
    return run_ratios(data["ratio_input"], _config)


def get_technicals(symbol: str, period: str = "") -> Dict[str, Any]:
    """Technical signals only."""
    _init()
    ta = TechnicalAnalyzer(_provider, _cache, _config)
    return ta.analyze(symbol, period=period)


def get_peer_comparison(symbol: str) -> Dict[str, Any]:
    """Peer comparison tables."""
    _init()
    pa = PeerAnalyzer(_provider, _cache, _config)
    peers = pa.discover_peers(symbol)
    fund = pa.get_peer_fundamentals(symbol, peers)
    tech = pa.get_peer_technicals(symbol, peers)
    return build_peer_comparison(
        symbol, fund, tech,
        _config.peer_fundamental_metrics_list,
        _config.peer_technical_metrics_list,
    )


def get_dcf_valuation(symbol: str) -> Dict[str, Any]:
    """DCF valuation summary."""
    _init()
    fa = FundamentalAnalyzer(_provider, _cache, _config)
    data = fa.fetch_all(symbol)
    return run_dcf(data["dcf_input"], _config)


def get_revenue_forecast(symbol: str) -> Dict[str, Any]:
    """Revenue forecast: base/bull/bear scenarios."""
    _init()
    fa = FundamentalAnalyzer(_provider, _cache, _config)
    data = fa.fetch_all(symbol)
    return run_forecast(data["forecast_input"], _config)


def get_news(symbol: str) -> Dict[str, Any]:
    """News + analyst recommendations."""
    _init()
    na = NewsAnalyzer(_provider, _cache, _config)
    return na.analyze(symbol)


def compare_stocks(symbols: List[str]) -> Dict[str, Any]:
    """Side-by-side comparison of multiple stocks."""
    _init()
    results = {}
    for sym in symbols:
        results[sym] = analyze(sym, include_peers=False)
    return results


def get_raw_data(symbol: str, data_type: str) -> Dict[str, Any]:
    """Fetch cached raw data."""
    _init()
    key = f"raw:{symbol.upper().strip()}:{data_type}"
    data = _cache.get(key)
    if data is None:
        # Trigger a fetch to populate cache
        fa = FundamentalAnalyzer(_provider, _cache, _config)
        fa.fetch_all(symbol)
        data = _cache.get(key)
    return data or {"error": f"No cached data for {symbol}:{data_type}"}


def _build_report(symbol: str, include_peers: bool = True) -> StockReport:
    fa = FundamentalAnalyzer(_provider, _cache, _config)
    data = fa.fetch_all(symbol)

    report = StockReport(
        symbol=symbol,
        name=data["info_summary"].get("name", symbol),
        sector=data["info_summary"].get("sector", ""),
        industry=data["info_summary"].get("industry", ""),
        current_price=data["info_summary"].get("current_price"),
        market_cap=data["info_summary"].get("market_cap"),
        currency=data["info_summary"].get("currency", "INR"),
    )

    # Fundamentals
    try:
        report.fundamentals = run_ratios(data["ratio_input"], _config)
    except Exception as e:
        logger.error("Ratio calculation failed: %s", e)

    # Technicals
    ta = TechnicalAnalyzer(_provider, _cache, _config)
    report.technicals = ta.analyze(symbol)

    # Peers
    if include_peers:
        try:
            pa = PeerAnalyzer(_provider, _cache, _config)
            peers = pa.discover_peers(symbol)
            if peers:
                fund = pa.get_peer_fundamentals(symbol, peers)
                tech = pa.get_peer_technicals(symbol, peers)
                report.peer_comparison = build_peer_comparison(
                    symbol, fund, tech,
                    _config.peer_fundamental_metrics_list,
                    _config.peer_technical_metrics_list,
                )
        except Exception as e:
            logger.error("Peer comparison failed: %s", e)

    # DCF
    if _config.fa_dcf_enabled:
        try:
            report.dcf_valuation = run_dcf(data["dcf_input"], _config)
        except Exception as e:
            logger.error("DCF failed: %s", e)

    # Forecast
    try:
        report.forecast = run_forecast(data["forecast_input"], _config)
    except Exception as e:
        logger.error("Forecast failed: %s", e)

    # News
    na = NewsAnalyzer(_provider, _cache, _config)
    report.news = na.analyze(symbol)

    return report
