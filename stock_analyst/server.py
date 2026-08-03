"""MCP server — exposes stock analysis tools via MCP protocol."""

import json
import logging

from mcp.server import MCPServer

from stock_analyst.config import get_settings

logger = logging.getLogger(__name__)

mcp = MCPServer("stock-analyst")


def _error(code: str, message: str) -> str:
    return json.dumps({"error": {"code": code, "message": message}})


def _ok(result, **kwargs) -> str:
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def analyze_stock(symbol: str, region: str = "in") -> str:
    """Retrieve full stock analysis: fundamentals, technicals, peer comparison, DCF valuation, revenue forecast, and news.

    Args:
        symbol: Stock ticker symbol (e.g., RELIANCE for India, AAPL for US, 0700.HK for Hong Kong).
        region: Region code (us, gb, de, jp, in, etc.). Default: in (India).
    """
    try:
        import stock_analyst
        return _ok(stock_analyst.analyze(symbol, region=region))
    except Exception as e:
        logger.exception("analyze_stock failed")
        return _error("analysis_failed", str(e))


@mcp.tool()
def get_fundamentals(symbol: str) -> str:
    """Retrieve financial ratios: profitability (ROE, ROA, margins), liquidity, leverage, efficiency, and valuation (PE, PB, EV/EBITDA) with benchmark interpretations.

    Args:
        symbol: Stock ticker symbol (e.g., RELIANCE, TCS).
    """
    try:
        import stock_analyst
        return _ok(stock_analyst.get_fundamentals(symbol))
    except Exception as e:
        logger.exception("get_fundamentals failed")
        return _error("fundamentals_failed", str(e))


@mcp.tool()
def get_technicals(symbol: str, period: str = "1y") -> str:
    """Retrieve technical signals: EMA trend, RSI (overbought/oversold), MACD crossovers, Bollinger Band position, and overall signal.

    Args:
        symbol: Stock ticker symbol.
        period: Historical period — one of: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max. Default: 1y.
    """
    try:
        import stock_analyst
        return _ok(stock_analyst.get_technicals(symbol, period=period))
    except Exception as e:
        logger.exception("get_technicals failed")
        return _error("technicals_failed", str(e))


@mcp.tool()
def get_peer_comparison(symbol: str, region: str = "in") -> str:
    """Retrieve peer comparison: fundamental and technical metrics ranked among industry peers.

    Args:
        symbol: Stock ticker symbol.
        region: Region code (us, gb, de, jp, in, etc.). Default: in.
    """
    try:
        import stock_analyst
        return _ok(stock_analyst.get_peer_comparison(symbol, region=region))
    except Exception as e:
        logger.exception("get_peer_comparison failed")
        return _error("peer_comparison_failed", str(e))


@mcp.tool()
def get_dcf_valuation(symbol: str) -> str:
    """Retrieve DCF valuation: WACC (India-adjusted defaults), equity value per share via perpetuity growth and exit multiple methods, with sensitivity range.

    Args:
        symbol: Stock ticker symbol.
    """
    try:
        import stock_analyst
        return _ok(stock_analyst.get_dcf_valuation(symbol))
    except Exception as e:
        logger.exception("get_dcf_valuation failed")
        return _error("dcf_failed", str(e))


@mcp.tool()
def get_revenue_forecast(symbol: str) -> str:
    """Retrieve revenue forecast with base, bull, and bear scenarios including trend analysis and growth rates.

    Args:
        symbol: Stock ticker symbol.
    """
    try:
        import stock_analyst
        return _ok(stock_analyst.get_revenue_forecast(symbol))
    except Exception as e:
        logger.exception("get_revenue_forecast failed")
        return _error("forecast_failed", str(e))


@mcp.tool()
def get_news(symbol: str) -> str:
    """Retrieve recent news headlines with sentiment analysis (VADER), article snippets, and analyst recommendation summary.

    Args:
        symbol: Stock ticker symbol.
    """
    try:
        import stock_analyst
        return _ok(stock_analyst.get_news(symbol))
    except Exception as e:
        logger.exception("get_news failed")
        return _error("news_failed", str(e))


@mcp.tool()
def compare_stocks(symbols: str) -> str:
    """Compare multiple stocks side-by-side with full analysis for each.

    Args:
        symbols: Comma-separated stock ticker symbols (e.g., "RELIANCE,TCS,INFY").
    """
    try:
        import stock_analyst
        symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]
        if not symbol_list:
            return _error("invalid_input", "Provide at least one symbol")
        return _ok(stock_analyst.compare_stocks(symbol_list))
    except Exception as e:
        logger.exception("compare_stocks failed")
        return _error("comparison_failed", str(e))


@mcp.tool()
def get_raw_data(symbol: str, data_type: str) -> str:
    """Fetch cached raw financial data for deep dives. Triggers a data fetch if not cached.

    Args:
        symbol: Stock ticker symbol.
        data_type: Type of data — one of: info, financials, balance_sheet, cashflow, ohlcv.
    """
    valid_types = {"info", "financials", "balance_sheet", "cashflow", "ohlcv"}
    if data_type not in valid_types:
        return _error("invalid_input", f"data_type must be one of: {', '.join(sorted(valid_types))}")
    try:
        import stock_analyst
        return _ok(stock_analyst.get_raw_data(symbol, data_type))
    except Exception as e:
        logger.exception("get_raw_data failed")
        return _error("raw_data_failed", str(e))


@mcp.tool()
def get_market_mood(region: str = "in") -> str:
    """Retrieve current market mood: region-specific indices, volatility index, and market assessment.

    Args:
        region: Region code (us, gb, de, jp, in, etc.). Default: in. For India, includes MMI from tickertape.in.
    
    Returns macro market context for investment timing decisions.
    """
    try:
        import stock_analyst
        return _ok(stock_analyst.get_market_mood(region=region))
    except Exception as e:
        logger.exception("get_market_mood failed")
        return _error("market_mood_failed", str(e))


@mcp.tool()
def screen_stocks(filters: str = "", region: str = "in", sort_by: str = "market_cap", limit: int = 50) -> str:
    """Screen stocks by fundamental, valuation, and technical criteria in any region.

    Args:
        filters: JSON string of filter criteria. Example: '{"sector": "Technology", "pe_max": 30, "roe_min": 0.15}'.
            Available filters: sector, industry, market_cap_min/max, pe_min/max, pb_min/max,
            roe_min/max, dividend_yield_min/max, revenue_growth_min/max, debt_to_equity_min/max,
            current_ratio_min/max, 52w_change_min/max, beta_min/max.
        region: Region code (us, gb, de, jp, in, etc.). Default: in.
        sort_by: Sort field — one of: market_cap, pe, pb, roe, dividend_yield, revenue_growth, price, change, volume, ticker. Default: market_cap.
        limit: Max results (1-250). Default: 50.
    """
    try:
        import stock_analyst
        filter_dict = json.loads(filters) if filters else {}
        return _ok(stock_analyst.screen_stocks(filter_dict, region=region, sort_by=sort_by, limit=limit))
    except Exception as e:
        logger.exception("screen_stocks failed")
        return _error("screen_failed", str(e))


@mcp.tool()
def get_screener_filters() -> str:
    """List available filter keys, descriptions, and sort options for the stock screener.

    Call this before screen_stocks to see what filters you can use.
    """
    try:
        import stock_analyst
        return _ok(stock_analyst.get_screener_filters())
    except Exception as e:
        logger.exception("get_screener_filters failed")
        return _error("screener_filters_failed", str(e))


@mcp.tool()
def search_tickers(query: str, instrument_type: str = "stock", region: str = "", limit: int = 10) -> str:
    """Search for tickers by name or symbol across regions.

    Args:
        query: Search term (ticker symbol or company name, e.g., 'Apple', 'AAPL', 'Tesla').
        instrument_type: Type of instrument (stock, etf, mutualfund, index, future, currency, cryptocurrency). Default: stock.
        region: Optional region filter (us, gb, de, jp, in, etc.). Leave empty for all regions.
        limit: Max results (1-50). Default: 10.
    """
    try:
        import stock_analyst
        return _ok(stock_analyst.search_tickers(query, instrument_type=instrument_type, 
                                               region=region if region else None, limit=limit))
    except Exception as e:
        logger.exception("search_tickers failed")
        return _error("search_failed", str(e))


@mcp.tool()
def analyze_asset(symbol: str, asset_type: str = "stock", include_fundamentals: bool = True, include_technicals: bool = True) -> str:
    """Analyze any asset class: stocks, ETFs, indices, commodities, crypto, currencies.

    Args:
        symbol: Ticker symbol (e.g., 'AAPL' for stock, 'SPY' for ETF, 'GC=F' for gold futures, 'BTC-USD' for Bitcoin, 'EURUSD=X' for currency pair).
        asset_type: Type of asset (stock, etf, index, commodity, crypto, currency). Default: stock.
        include_fundamentals: Include fundamental ratios (may not be available for all assets). Default: true.
        include_technicals: Include technical analysis. Default: true.
    """
    try:
        import stock_analyst
        return _ok(stock_analyst.analyze_asset(symbol, asset_type=asset_type, 
                                              include_fundamentals=include_fundamentals,
                                              include_technicals=include_technicals))
    except Exception as e:
        logger.exception("analyze_asset failed")
        return _error("asset_analysis_failed", str(e))


@mcp.tool()
def get_config() -> str:
    """Retrieve current configuration settings for all analysis tools.

    Returns current values for technical analysis periods, DCF parameters, peer comparison settings, etc.
    Use this to understand available options before calling set_config.
    """
    try:
        import stock_analyst
        config = stock_analyst.get_config()
        return _ok(config)
    except Exception as e:
        logger.exception("get_config failed")
        return _error("config_failed", str(e))


@mcp.tool()
def set_config(key: str, value: str) -> str:
    """Update a configuration setting for analysis tools.

    Args:
        key: Configuration key (e.g., 'default_period', 'ta_rsi_period', 'fa_dcf_projection_years').
        value: New value as string (will be converted to appropriate type).

    Common keys:
        - default_period: Historical period for analysis (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max). Default: 1y
        - ta_rsi_period: RSI calculation period. Default: 14
        - ta_ema_periods: Comma-separated EMA periods (e.g., '20,50,200'). Default: 20,50,200
        - fa_dcf_projection_years: DCF projection years. Default: 5
        - fa_dcf_terminal_growth: Terminal growth rate (0.025 = 2.5%). Default: 0.025
        - fa_dcf_exit_multiple: Exit multiple for DCF. Default: 12.0
        - peers_max_count: Max peers for comparison. Default: 10
        - cache_ttl: Cache TTL in seconds. Default: 3600

    Returns confirmation with new value and affected tools.
    """
    try:
        import stock_analyst
        result = stock_analyst.set_config(key, value)
        return _ok(result)
    except Exception as e:
        logger.exception("set_config failed")
        return _error("config_failed", str(e))


def main():
    config = get_settings()
    logging.basicConfig(level=getattr(logging, config.log_level, logging.INFO))
    transport = config.mcp_transport
    kwargs = {}
    if transport == "streamable-http":
        kwargs["port"] = config.mcp_port
    mcp.run(transport=transport, **kwargs)


if __name__ == "__main__":
    main()
