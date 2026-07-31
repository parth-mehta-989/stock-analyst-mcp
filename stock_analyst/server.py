"""MCP server — exposes stock analysis tools via MCP protocol."""

import json
import logging
from typing import Optional

from mcp.server import MCPServer

from stock_analyst.config import get_settings

logger = logging.getLogger(__name__)
config = get_settings()

mcp = MCPServer("stock-analyst")


@mcp.tool()
def analyze_stock(symbol: str) -> str:
    """Full stock analysis: fundamentals, technicals, peer comparison, DCF valuation, revenue forecast, and news.

    Args:
        symbol: Stock ticker symbol (e.g., RELIANCE, TCS, INFY). Automatically appends .NS for NSE.

    Returns:
        str: JSON with computed metrics — ratios, signals, peer rankings, DCF summary, forecast.
    """
    import stock_analyst
    result = stock_analyst.analyze(symbol)
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def get_fundamentals(symbol: str) -> str:
    """Financial ratios: profitability (ROE, ROA, margins), liquidity, leverage, efficiency, and valuation (PE, PB, EV/EBITDA).

    Args:
        symbol: Stock ticker symbol (e.g., RELIANCE, TCS).

    Returns:
        str: JSON with ratio values, formulas, and benchmark interpretations.
    """
    import stock_analyst
    result = stock_analyst.get_fundamentals(symbol)
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def get_technicals(symbol: str, period: str = "1y") -> str:
    """Technical signals: EMA trend, RSI (overbought/oversold), MACD crossovers, Bollinger Band position.

    Args:
        symbol: Stock ticker symbol.
        period: Historical period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max). Default: 1y.

    Returns:
        str: JSON with compact technical summary and overall signal.
    """
    import stock_analyst
    result = stock_analyst.get_technicals(symbol, period=period)
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def get_peer_comparison(symbol: str) -> str:
    """Peer comparison: fundamental + technical metrics ranked among sector peers.

    Args:
        symbol: Stock ticker symbol.

    Returns:
        str: JSON with peer fundamental/technical tables and target rankings.
    """
    import stock_analyst
    result = stock_analyst.get_peer_comparison(symbol)
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def get_dcf_valuation(symbol: str) -> str:
    """DCF valuation: WACC (India-adjusted), equity value per share, sensitivity range.

    Args:
        symbol: Stock ticker symbol.

    Returns:
        str: JSON with WACC, value per share (perpetuity + exit multiple), sensitivity min/max.
    """
    import stock_analyst
    result = stock_analyst.get_dcf_valuation(symbol)
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def get_revenue_forecast(symbol: str) -> str:
    """Revenue forecast: base/bull/bear scenarios with trend analysis.

    Args:
        symbol: Stock ticker symbol.

    Returns:
        str: JSON with trend direction, growth rate, and scenario comparison.
    """
    import stock_analyst
    result = stock_analyst.get_revenue_forecast(symbol)
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def get_news(symbol: str) -> str:
    """Recent news headlines (latest 5) and analyst recommendation summary.

    Args:
        symbol: Stock ticker symbol.

    Returns:
        str: JSON with headlines and buy/hold/sell recommendation counts.
    """
    import stock_analyst
    result = stock_analyst.get_news(symbol)
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def compare_stocks(symbols: str) -> str:
    """Side-by-side comparison of multiple stocks.

    Args:
        symbols: Comma-separated stock ticker symbols (e.g., "RELIANCE,TCS,INFY").

    Returns:
        str: JSON with full analysis for each stock.
    """
    import stock_analyst
    symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]
    result = stock_analyst.compare_stocks(symbol_list)
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def get_raw_data(symbol: str, data_type: str) -> str:
    """Fetch cached raw financial data for deep dives.

    Args:
        symbol: Stock ticker symbol.
        data_type: Type of data — one of: info, financials, balance_sheet, cashflow, ohlcv

    Returns:
        str: JSON with raw financial statement data.
    """
    import stock_analyst
    result = stock_analyst.get_raw_data(symbol, data_type)
    return json.dumps(result, indent=2, default=str)


def main():
    logging.basicConfig(level=getattr(logging, config.log_level, logging.INFO))
    transport = config.mcp_transport
    kwargs = {}
    if transport == "streamable-http":
        kwargs["port"] = config.mcp_port
    mcp.run(transport=transport, **kwargs)


if __name__ == "__main__":
    main()
