"""CLI interface for stock_analyst."""

import argparse
import json
import logging
import sys

from stock_analyst.config import get_settings


def main():
    parser = argparse.ArgumentParser(
        prog="stock_analyst",
        description="Indian Stock Market Analysis Tool",
    )
    parser.add_argument("--symbol", "-s", help="Stock ticker symbol (e.g., RELIANCE)")
    parser.add_argument("--symbols", help="Comma-separated symbols for comparison")
    parser.add_argument(
        "--analysis", "-a",
        choices=["full", "fundamentals", "technicals", "peers", "dcf", "forecast", "news", "market-mood"],
        default="full",
        help="Analysis type (default: full)",
    )
    parser.add_argument("--format", "-f", choices=["json", "markdown"], default=None, help="Output format")
    parser.add_argument("--raw", help="Fetch raw data type: info|financials|balance_sheet|cashflow|ohlcv")
    parser.add_argument("--period", default="", help="Historical period for technicals")
    parser.add_argument("--no-cache", action="store_true", help="Disable caching")
    parser.add_argument("--env-file", help="Path to custom env file")
    parser.add_argument("--compare", action="store_true", help="Compare mode for --symbols")
    parser.add_argument("--serve", action="store_true", help="Start MCP server")

    # Screener arguments
    parser.add_argument("--screen", action="store_true", help="Screen stocks by criteria")
    parser.add_argument("--sector", help="Filter by sector")
    parser.add_argument("--industry", help="Filter by industry")
    parser.add_argument("--market-cap-min", type=float, help="Min market cap")
    parser.add_argument("--market-cap-max", type=float, help="Max market cap")
    parser.add_argument("--pe-max", type=float, help="Max P/E ratio")
    parser.add_argument("--pe-min", type=float, help="Min P/E ratio")
    parser.add_argument("--roe-min", type=float, help="Min ROE (decimal, e.g., 0.15)")
    parser.add_argument("--dividend-yield-min", type=float, help="Min dividend yield (decimal)")
    parser.add_argument("--sort-by", default="market_cap", help="Sort screener results by field")
    parser.add_argument("--limit", type=int, default=None, help="Max results for screener")

    args = parser.parse_args()

    config = get_settings()
    output_format = args.format or config.output_format
    logging.basicConfig(level=getattr(logging, config.log_level, logging.INFO))

    if args.serve:
        from stock_analyst.server import main as serve
        serve()
        return

    import stock_analyst

    if args.no_cache:
        stock_analyst._config = config
        from stock_analyst.cache.base import NullCache
        stock_analyst._cache = NullCache()
        stock_analyst._provider = stock_analyst.get_provider(config)

    result = None

    # Market mood (no symbol needed)
    if args.analysis == "market-mood":
        result = stock_analyst.get_market_mood()
    # Screener (no symbol needed)
    elif args.screen:
        filters = {}
        if args.sector:
            filters["sector"] = args.sector
        if args.industry:
            filters["industry"] = args.industry
        if args.market_cap_min is not None:
            filters["market_cap_min"] = args.market_cap_min
        if args.market_cap_max is not None:
            filters["market_cap_max"] = args.market_cap_max
        if args.pe_max is not None:
            filters["pe_max"] = args.pe_max
        if args.pe_min is not None:
            filters["pe_min"] = args.pe_min
        if args.roe_min is not None:
            filters["roe_min"] = args.roe_min
        if args.dividend_yield_min is not None:
            filters["dividend_yield_min"] = args.dividend_yield_min
        result = stock_analyst.screen_stocks(filters, sort_by=args.sort_by, limit=args.limit)
    elif args.raw and args.symbol:
        result = stock_analyst.get_raw_data(args.symbol, args.raw)
    elif args.symbols and args.compare:
        symbol_list = [s.strip() for s in args.symbols.split(",") if s.strip()]
        result = stock_analyst.compare_stocks(symbol_list)
    elif args.symbol:
        if args.analysis == "full":
            result = stock_analyst.analyze(args.symbol)
        elif args.analysis == "fundamentals":
            result = stock_analyst.get_fundamentals(args.symbol)
        elif args.analysis == "technicals":
            result = stock_analyst.get_technicals(args.symbol, period=args.period)
        elif args.analysis == "peers":
            result = stock_analyst.get_peer_comparison(args.symbol)
        elif args.analysis == "dcf":
            result = stock_analyst.get_dcf_valuation(args.symbol)
        elif args.analysis == "forecast":
            result = stock_analyst.get_revenue_forecast(args.symbol)
        elif args.analysis == "news":
            result = stock_analyst.get_news(args.symbol)
    else:
        parser.print_help()
        sys.exit(1)

    if result is None:
        parser.print_help()
        sys.exit(1)

    if output_format == "markdown" and args.analysis == "full" and args.symbol:
        from stock_analyst.analysis.formatter import to_markdown
        report = stock_analyst._build_report(args.symbol)
        print(to_markdown(report))
    else:
        indent = 2 if config.output_pretty else None
        print(json.dumps(result, indent=indent, default=str))
