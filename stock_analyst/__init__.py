"""Stock Analyst — Indian stock market analysis tool."""

import logging
from typing import Any

from stock_analyst.analysis.formatter import to_json as to_json
from stock_analyst.analysis.formatter import to_markdown as to_markdown
from stock_analyst.analysis.peer_comparison import build_peer_comparison
from stock_analyst.analysis.report import StockReport
from stock_analyst.cache import get_cache
from stock_analyst.config import Settings, get_settings
from stock_analyst.engine.data_provider import get_provider
from stock_analyst.engine.fundamentals import FundamentalAnalyzer
from stock_analyst.engine.market import MarketAnalyzer
from stock_analyst.engine.multi_asset import MultiAssetAnalyzer
from stock_analyst.engine.news import NewsAnalyzer
from stock_analyst.engine.peers import PeerAnalyzer
from stock_analyst.engine.screener import StockScreener
from stock_analyst.engine.search import TickerSearch
from stock_analyst.engine.technicals import TechnicalAnalyzer
from stock_analyst.fa.dcf_runner import run_dcf
from stock_analyst.fa.forecast_runner import run_forecast
from stock_analyst.fa.ratio_runner import run_ratios

logger = logging.getLogger(__name__)

_config: Settings | None = None
_cache = None
_provider = None


def _init():
    global _config, _cache, _provider
    if _config is None:
        _config = get_settings()
        _cache = get_cache(_config)
        _provider = get_provider(_config)


def _resolve_symbol(symbol: str, region: str = "in") -> str:
    """Resolve bare symbol to exchange suffix based on region.
    
    - Preserves explicit exchange suffixes (.NS, .BO, .L, .DE, .HK, etc.)
    - For India (in), appends .NS if no suffix
    - For other regions, leaves as-is (yfinance handles US/EU/Asia tickers directly)
    """
    s = symbol.upper().strip()
    explicit_suffixes = (".NS", ".BO", ".L", ".DE", ".PA", ".TO", ".AX", ".HK", ".SS", ".SZ", ".T", ".KS", ".SI", ".AS", ".MC", ".SW", ".BR", ".CO", ".HE", ".LS", ".OL", ".ST", ".VI")
    if any(s.endswith(suf) for suf in explicit_suffixes):
        return s
    if region == "in":
        return f"{s}.NS"
    return s


def analyze(symbol: str, region: str = "in", include_peers: bool = True) -> dict[str, Any]:
    """Full analysis: fundamentals + technicals + peers + DCF + forecast + news."""
    _init()
    resolved_symbol = _resolve_symbol(symbol, region)
    report = _build_report(resolved_symbol, region=region, include_peers=include_peers)
    return report.to_dict()


def get_fundamentals(symbol: str, region: str = "in") -> dict[str, Any]:
    """Financial ratios only."""
    _init()
    resolved_symbol = _resolve_symbol(symbol, region)
    fa = FundamentalAnalyzer(_provider, _cache, _config)
    data = fa.fetch_all(resolved_symbol)
    return run_ratios(data["ratio_input"], _config)


def get_technicals(symbol: str, region: str = "in", period: str = "") -> dict[str, Any]:
    """Technical signals only."""
    _init()
    resolved_symbol = _resolve_symbol(symbol, region)
    ta = TechnicalAnalyzer(_provider, _cache, _config)
    return ta.analyze(resolved_symbol, period=period)


def get_peer_comparison(symbol: str, region: str = "in") -> dict[str, Any]:
    """Peer comparison tables."""
    _init()
    resolved_symbol = _resolve_symbol(symbol, region)
    pa = PeerAnalyzer(_provider, _cache, _config)
    peers = pa.discover_peers(resolved_symbol, region=region)
    fund = pa.get_peer_fundamentals(resolved_symbol, peers, region=region)
    tech = pa.get_peer_technicals(resolved_symbol, peers, region=region)
    return build_peer_comparison(
        resolved_symbol, fund, tech,
        _config.peer_fundamental_metrics_list,
        _config.peer_technical_metrics_list,
    )


def get_dcf_valuation(symbol: str, region: str = "in") -> dict[str, Any]:
    """DCF valuation summary."""
    _init()
    resolved_symbol = _resolve_symbol(symbol, region)
    fa = FundamentalAnalyzer(_provider, _cache, _config)
    data = fa.fetch_all(resolved_symbol)
    return run_dcf(data["dcf_input"], _config)


def get_revenue_forecast(symbol: str, region: str = "in") -> dict[str, Any]:
    """Revenue forecast: base/bull/bear scenarios."""
    _init()
    resolved_symbol = _resolve_symbol(symbol, region)
    fa = FundamentalAnalyzer(_provider, _cache, _config)
    data = fa.fetch_all(resolved_symbol)
    return run_forecast(data["forecast_input"], _config)


def get_news(symbol: str, region: str = "in") -> dict[str, Any]:
    """News + analyst recommendations."""
    _init()
    resolved_symbol = _resolve_symbol(symbol, region)
    na = NewsAnalyzer(_provider, _cache, _config)
    return na.analyze(resolved_symbol)


def compare_stocks(symbols: list[str], region: str = "in") -> dict[str, Any]:
    """Side-by-side comparison of multiple stocks."""
    _init()
    results = {}
    for sym in symbols:
        results[sym] = analyze(sym, region=region, include_peers=False)
    return results


def get_raw_data(symbol: str, data_type: str, region: str = "in") -> dict[str, Any]:
    """Fetch cached raw data."""
    _init()
    resolved_symbol = _resolve_symbol(symbol, region)
    key = f"raw:{resolved_symbol}:{data_type}"
    data = _cache.get(key)
    if data is None:
        # Trigger a fetch to populate cache
        fa = FundamentalAnalyzer(_provider, _cache, _config)
        fa.fetch_all(resolved_symbol)
        data = _cache.get(key)
    return data or {"error": f"No cached data for {resolved_symbol}:{data_type}"}


def get_market_mood(region: str = "in") -> dict[str, Any]:
    """Market mood: region-specific indices + volatility."""
    _init()
    ma = MarketAnalyzer(_cache, _config)
    return ma.get_mood(region=region)


def screen_stocks(
    filters: dict[str, Any] | None = None,
    region: str = "in",
    sort_by: str = "market_cap",
    sort_asc: bool = False,
    limit: int | None = None,
) -> dict[str, Any]:
    """Screen stocks by criteria (market cap, PE, ROE, sector, etc.) in any region."""
    _init()
    screener = StockScreener(_cache, _config)
    return screener.screen(filters or {}, region=region, sort_by=sort_by, sort_asc=sort_asc, limit=limit)


def get_screener_filters() -> dict[str, Any]:
    """Return available screener filter keys and descriptions."""
    return StockScreener.available_filters()


def search_tickers(
    query: str,
    instrument_type: str = "stock",
    region: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Search for tickers by name or symbol across regions."""
    _init()
    search = TickerSearch(_cache, _config)
    return search.search(query, instrument_type=instrument_type, region=region, limit=limit)


def analyze_asset(
    symbol: str,
    asset_type: str = "stock",
    region: str = "in",
    include_fundamentals: bool = True,
    include_technicals: bool = True,
) -> dict[str, Any]:
    """Analyze any asset: stock, ETF, index, commodity, crypto, currency."""
    _init()
    resolved_symbol = _resolve_symbol(symbol, region) if asset_type == "stock" else symbol
    analyzer = MultiAssetAnalyzer(_provider, _cache, _config)
    return analyzer.analyze_asset(resolved_symbol, asset_type=asset_type, 
                                  include_fundamentals=include_fundamentals,
                                  include_technicals=include_technicals)


def get_config() -> dict[str, Any]:
    """Get current configuration settings."""
    _init()
    return {
        "data_provider": _config.data_provider,
        "default_exchange": _config.default_exchange,
        "default_period": _config.default_period,
        "default_interval": _config.default_interval,
        "cache_backend": _config.cache_backend,
        "cache_ttl": _config.cache_ttl,
        "technical_analysis": {
            "ema_periods": _config.ta_ema_periods,
            "rsi_period": _config.ta_rsi_period,
            "macd_params": _config.ta_macd_params,
            "bollinger_enabled": _config.ta_bollinger_enabled,
            "bollinger_period": _config.ta_bollinger_period,
        },
        "financial_analysis": {
            "dcf_enabled": _config.fa_dcf_enabled,
            "dcf_projection_years": _config.fa_dcf_projection_years,
            "dcf_terminal_growth": _config.fa_dcf_terminal_growth,
            "dcf_exit_multiple": _config.fa_dcf_exit_multiple,
            "wacc_risk_free_rate": _config.fa_wacc_risk_free_rate,
            "wacc_equity_risk_premium": _config.fa_wacc_equity_risk_premium,
            "wacc_cost_of_debt": _config.fa_wacc_cost_of_debt,
            "wacc_tax_rate": _config.fa_wacc_tax_rate,
            "wacc_debt_weight": _config.fa_wacc_debt_weight,
            "wacc_equity_weight": _config.fa_wacc_equity_weight,
            "forecast_scenarios": _config.fa_forecast_scenarios,
        },
        "peer_comparison": {
            "max_count": _config.peers_max_count,
            "fundamental_comparison": _config.peers_fundamental_comparison,
            "technical_comparison": _config.peers_technical_comparison,
            "fundamental_metrics": _config.peers_fundamental_metrics,
            "technical_metrics": _config.peers_technical_metrics,
        },
        "output": {
            "format": _config.output_format,
            "include_raw": _config.output_include_raw,
            "pretty": _config.output_pretty,
        },
    }


def set_config(key: str, value: str) -> dict[str, Any]:
    """Update a configuration setting dynamically.
    
    Args:
        key: Config key (e.g., 'default_period', 'ta_rsi_period')
        value: New value as string
        
    Returns:
        dict with confirmation, new value, and affected tools
    """
    _init()
    
    # Type conversions
    type_map = {
        "default_period": str,
        "default_interval": str,
        "ta_rsi_period": int,
        "ta_ema_periods": str,
        "ta_macd_params": str,
        "ta_bollinger_enabled": lambda x: x.lower() in ("true", "1", "yes"),
        "ta_bollinger_period": int,
        "fa_dcf_enabled": lambda x: x.lower() in ("true", "1", "yes"),
        "fa_dcf_projection_years": int,
        "fa_dcf_terminal_growth": float,
        "fa_dcf_exit_multiple": float,
        "fa_wacc_risk_free_rate": float,
        "fa_wacc_equity_risk_premium": float,
        "fa_wacc_cost_of_debt": float,
        "fa_wacc_tax_rate": float,
        "fa_wacc_debt_weight": float,
        "fa_wacc_equity_weight": float,
        "fa_forecast_scenarios": str,
        "peers_max_count": int,
        "peers_fundamental_comparison": lambda x: x.lower() in ("true", "1", "yes"),
        "peers_technical_comparison": lambda x: x.lower() in ("true", "1", "yes"),
        "peers_fundamental_metrics": str,
        "peers_technical_metrics": str,
        "cache_ttl": int,
        "output_format": str,
        "output_include_raw": lambda x: x.lower() in ("true", "1", "yes"),
        "output_pretty": lambda x: x.lower() in ("true", "1", "yes"),
    }
    
    if key not in type_map:
        valid_keys = sorted(type_map.keys())
        return {
            "error": f"Unknown config key: {key}",
            "valid_keys": valid_keys,
        }
    
    try:
        converter = type_map[key]
        converted_value = converter(value)
        setattr(_config, key, converted_value)
        
        # Determine affected tools
        affected_tools = []
        if key.startswith("ta_"):
            affected_tools.append("get_technicals")
            affected_tools.append("analyze_stock")
        if key.startswith("fa_"):
            affected_tools.extend(["get_dcf_valuation", "get_revenue_forecast", "analyze_stock"])
        if key.startswith("peers_"):
            affected_tools.extend(["get_peer_comparison", "analyze_stock"])
        if key in ("default_period", "default_interval", "cache_ttl"):
            affected_tools.append("all_tools")
        
        return {
            "status": "success",
            "key": key,
            "old_value": getattr(_config, key),
            "new_value": converted_value,
            "affected_tools": list(set(affected_tools)),
            "message": f"Config updated: {key} = {converted_value}",
        }
    except (ValueError, TypeError) as e:
        return {
            "error": f"Failed to convert value: {e!s}",
            "key": key,
            "value": value,
            "expected_type": str(type_map[key]),
        }


def _build_report(symbol: str, region: str = "in", include_peers: bool = True) -> StockReport:
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
    except (ValueError, KeyError, RuntimeError) as e:
        logger.error("Ratio calculation failed: %s", e)

    # Technicals
    ta = TechnicalAnalyzer(_provider, _cache, _config)
    report.technicals = ta.analyze(symbol)

    # Peers
    if include_peers:
        try:
            pa = PeerAnalyzer(_provider, _cache, _config)
            peers = pa.discover_peers(symbol, region=region)
            if peers:
                fund = pa.get_peer_fundamentals(symbol, peers, region=region)
                tech = pa.get_peer_technicals(symbol, peers, region=region)
                report.peer_comparison = build_peer_comparison(
                    symbol, fund, tech,
                    _config.peer_fundamental_metrics_list,
                    _config.peer_technical_metrics_list,
                )
        except (ValueError, KeyError, RuntimeError) as e:
            logger.error("Peer comparison failed: %s", e)

    # DCF
    if _config.fa_dcf_enabled:
        try:
            report.dcf_valuation = run_dcf(data["dcf_input"], _config)
        except (ValueError, KeyError, RuntimeError) as e:
            logger.error("DCF failed: %s", e)

    # Forecast
    try:
        report.forecast = run_forecast(data["forecast_input"], _config)
    except (ValueError, KeyError, RuntimeError) as e:
        logger.error("Forecast failed: %s", e)

    # News
    na = NewsAnalyzer(_provider, _cache, _config)
    report.news = na.analyze(symbol)

    return report
