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
def analyze_stock(symbol: str) -> str:
    """Retrieve full stock analysis: fundamentals, technicals, peer comparison, DCF valuation, revenue forecast, and news for an Indian NSE/BSE stock.

    Args:
        symbol: Stock ticker symbol (e.g., RELIANCE, TCS, INFY). Automatically appends .NS for NSE.
    """
    try:
        import stock_analyst
        return _ok(stock_analyst.analyze(symbol))
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
def get_peer_comparison(symbol: str) -> str:
    """Retrieve peer comparison: fundamental and technical metrics ranked among industry peers discovered via yfinance Industry API.

    Args:
        symbol: Stock ticker symbol.
    """
    try:
        import stock_analyst
        return _ok(stock_analyst.get_peer_comparison(symbol))
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
    """Retrieve recent news headlines (latest 5) and analyst recommendation summary (buy/hold/sell counts).

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
