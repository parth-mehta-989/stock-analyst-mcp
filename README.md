# stock-analyst-mcp

MCP server for global stock market analysis — fundamentals, technicals, DCF valuation, peer comparison, multi-asset support, and more. Works for 50+ regions worldwide.

<!-- mcp-name: io.github.parth-mehta-989/stock-analyst-mcp -->

## What's New in v0.5.7

**Python 3.13+ Requirement**

- **Requires Python >=3.13**: Fixes `uvx` picking stale Python 3.12 which caused pandas C extension crashes (`ModuleNotFoundError: pandas._libs.pandas_parser`)
- **`uvx stock-analyst-mcp` now works without `--python`**: uv/uvx auto-selects 3.13+

## What's New in v0.5.6

**MCP Framework Migration — FastMCP standalone**

- **Replaced `mcp` SDK with standalone `fastmcp`**: Eliminates v2.0.0 breaking changes, no more `mcp.server.fastmcp` import errors
- **Cleaner dependency**: `fastmcp>=3.4.0,<4.0.0` (Prefect-maintained, actively developed)
- **Port configuration**: Now passed as kwarg to `mcp.run(transport=..., port=...)`
- **Future-proof**: No SDK version conflicts, fastmcp handles all MCP protocol versions

## What's New in v0.5.5

**News Fix — yfinance format change**

- **Fixed empty headlines**: yfinance now nests news fields under `content`
- **Correct mapping**: title, publisher, link, pub_date extracted from `content.*`
- **Backward compatible**: still handles legacy top-level news format

## What's New in v0.5.4

**API Fix — `FastMCP.run()` compatibility**

- **Fixed TypeError**: `FastMCP.run()` doesn't accept `port` kwarg
- **Port configuration**: Set via `mcp.settings.port` before calling `run()`

## What's New in v0.5.3

**Compatibility Fix — `mcp>=1.28` support**

- **Fixed breaking import**: Replaced removed `MCPServer` with `FastMCP` from `mcp.server.fastmcp`
- **Pinned mcp dependency**: `mcp>=1.0.0,<3.0.0` to prevent future breakage
- **Added requirements.txt** for pip-based installs

## What's New in v0.5.2

**Screener Fix — `screen_stocks` works across regions**

- **Fixed yfinance EquityQuery parameter**: `_size` → `size` in `yf.screen()` call, restoring screener results for India and other regions

## What's New in v0.5.1

**Performance Overhaul — 3-19x faster peer analysis**

- **Parallel peer fundamentals**: ThreadPoolExecutor on `get_info()` calls (3.7x speedup)
- **Batch history downloads**: Single `yf.download()` for all peers (19.3x speedup)
- **Parallel snippet fetching**: News analysis now fetches article snippets concurrently
- **New `stock_analyst/utils/` module**: Reusable concurrency helpers (`parallel_map`, `parallel_map_dict`, `batch_download_history`)
- **Zero new dependencies**: Uses stdlib `concurrent.futures`

**Example**: Analyzing LOW (US) with 10 peers now takes ~2-3s instead of 8-10s.

## Install

```bash
pip install stock-analyst-mcp
```

Or run directly without installing:

```bash
uvx stock-analyst-mcp
```

## MCP Configuration

Add to your MCP client config (Claude Desktop, Devin, Cursor, etc.):

```json
{
  "mcpServers": {
    "stock-analyst": {
      "command": "uvx",
      "args": ["stock-analyst-mcp"]
    }
  }
}
```

Or if installed via pip:

```json
{
  "mcpServers": {
    "stock-analyst": {
      "command": "stock-analyst-mcp"
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `analyze_stock` | Full analysis: fundamentals + technicals + peers + DCF + forecast + news (any region) |
| `get_fundamentals` | Financial ratios: profitability, liquidity, leverage, efficiency, valuation |
| `get_technicals` | Technical signals: EMA trend, RSI, MACD, Bollinger Bands |
| `get_peer_comparison` | Peer fundamental + technical metrics with rankings (region-scoped) |
| `get_dcf_valuation` | DCF: WACC, equity value/share, sensitivity range |
| `get_revenue_forecast` | Revenue forecast: base/bull/bear scenarios |
| `get_news` | News headlines with VADER sentiment + article snippets + analyst recommendations |
| `get_market_mood` | Region-specific indices + volatility index + market assessment |
| `screen_stocks` | Screen stocks by filters (sector, PE, ROE, market cap, etc.) in any region |
| `get_screener_filters` | List available screener filter keys and sort options |
| `search_tickers` | Search for tickers by name or symbol across regions (stocks, ETFs, indices, crypto, etc.) |
| `analyze_asset` | Analyze any asset class: stocks, ETFs, indices, commodities, crypto, currencies |
| `compare_stocks` | Side-by-side comparison of multiple stocks |
| `get_raw_data` | Fetch cached raw financials for deep dives |
| `get_config` | View current configuration settings for all analysis tools |
| `set_config` | Update configuration settings dynamically |

### Configuration Tools

#### `get_config`

Retrieve all current configuration settings. Useful for understanding what parameters are available before calling `set_config`.

```python
from stock_analyst import get_config

config = get_config()
# Returns dict with sections:
# - data_provider, default_exchange, default_period, cache settings
# - technical_analysis: EMA periods, RSI period, MACD params, Bollinger settings
# - financial_analysis: DCF params, WACC settings, forecast scenarios
# - peer_comparison: max count, metrics to compare
# - output: format, pretty-print settings
```

#### `set_config`

Update configuration dynamically without restarting. Changes affect subsequent tool calls.

```python
from stock_analyst import set_config

# Change technical analysis period from 1y to 1d
result = set_config("default_period", "1d")
# Returns: {"status": "success", "key": "default_period", "new_value": "1d", "affected_tools": ["all_tools"]}

# Change RSI period from 14 to 21
result = set_config("ta_rsi_period", "21")
# Returns: {"status": "success", "key": "ta_rsi_period", "new_value": 21, "affected_tools": ["get_technicals", "analyze_stock"]}

# Change DCF projection years from 5 to 10
result = set_config("fa_dcf_projection_years", "10")
# Returns: {"status": "success", "key": "fa_dcf_projection_years", "new_value": 10, "affected_tools": ["get_dcf_valuation", "get_revenue_forecast", "analyze_stock"]}
```

**Common Configuration Keys:**

| Key | Type | Default | Description | Affects |
|-----|------|---------|-------------|---------|
| `default_period` | str | `1y` | Historical period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max | all_tools |
| `ta_rsi_period` | int | `14` | RSI calculation period | get_technicals, analyze_stock |
| `ta_ema_periods` | str | `20,50,200` | Comma-separated EMA periods | get_technicals, analyze_stock |
| `ta_macd_params` | str | `12,26,9` | MACD (fast, slow, signal) | get_technicals, analyze_stock |
| `ta_bollinger_enabled` | bool | `true` | Enable Bollinger Bands | get_technicals, analyze_stock |
| `ta_bollinger_period` | int | `20` | Bollinger Bands period | get_technicals, analyze_stock |
| `fa_dcf_enabled` | bool | `true` | Run DCF valuation | analyze_stock, get_dcf_valuation |
| `fa_dcf_projection_years` | int | `5` | DCF projection years | get_dcf_valuation, get_revenue_forecast, analyze_stock |
| `fa_dcf_terminal_growth` | float | `0.025` | Terminal growth rate (2.5%) | get_dcf_valuation, analyze_stock |
| `fa_dcf_exit_multiple` | float | `12.0` | Exit multiple for DCF | get_dcf_valuation, analyze_stock |
| `fa_wacc_risk_free_rate` | float | `0.07` | Risk-free rate (7% for India) | get_dcf_valuation, analyze_stock |
| `fa_wacc_equity_risk_premium` | float | `0.06` | Equity risk premium (6%) | get_dcf_valuation, analyze_stock |
| `fa_wacc_cost_of_debt` | float | `0.09` | Cost of debt (9% for India) | get_dcf_valuation, analyze_stock |
| `fa_wacc_tax_rate` | float | `0.25` | Tax rate (25% for India) | get_dcf_valuation, analyze_stock |
| `peers_max_count` | int | `10` | Max peers to compare | get_peer_comparison, analyze_stock |
| `cache_ttl` | int | `3600` | Cache TTL in seconds | all_tools |

**Example: Customize Technical Analysis**

```python
from stock_analyst import set_config, get_technicals

# Use 1-day data with custom RSI period
set_config("default_period", "1d")
set_config("ta_rsi_period", "21")

# Get technicals with new settings
signals = get_technicals("RELIANCE")
```

**Example: Customize DCF Valuation**

```python
from stock_analyst import set_config, get_dcf_valuation

# Use 10-year projection with different growth assumptions
set_config("fa_dcf_projection_years", "10")
set_config("fa_dcf_terminal_growth", "0.03")  # 3% terminal growth
set_config("fa_wacc_risk_free_rate", "0.065")  # 6.5% risk-free rate

# Get DCF with new assumptions
valuation = get_dcf_valuation("RELIANCE")
```

## CLI

Also works as a standalone CLI (no LLM needed):

```bash
# Full analysis
stock-analyst --symbol RELIANCE

# Specific analysis
stock-analyst --symbol TCS --analysis fundamentals
stock-analyst --symbol INFY --analysis technicals
stock-analyst --symbol RELIANCE --analysis dcf

# Compare multiple stocks
stock-analyst --symbols RELIANCE,TCS,INFY --compare

# Markdown output
stock-analyst --symbol RELIANCE --format markdown

# Raw data
stock-analyst --symbol RELIANCE --raw financials

# Market mood (no symbol needed)
stock-analyst --analysis market-mood

# Stock screener (India)
stock-analyst --screen --sector Technology --pe-max 30 --roe-min 0.15
stock-analyst --screen --market-cap-min 50000000000 --sort-by pe --limit 20

# Global stocks (any region)
stock-analyst --symbol AAPL --region us
stock-analyst --symbol 0700.HK --region hk
stock-analyst --screen --region gb --sector Technology --pe-max 25

# Market mood (global)
stock-analyst --analysis market-mood --region us
stock-analyst --analysis market-mood --region de

# Ticker search
stock-analyst --search "Apple" --search-type stock --region us
stock-analyst --search "Bitcoin" --search-type cryptocurrency

# Multi-asset analysis
stock-analyst --symbol SPY --analysis asset --asset-type etf
stock-analyst --symbol GC=F --analysis asset --asset-type commodity
stock-analyst --symbol BTC-USD --analysis asset --asset-type crypto
```

## Configuration

All settings configurable via environment variables with `SA_` prefix. Defaults work out of the box for Indian markets (NSE). Supports 50+ regions globally.

| Variable | Default | Description |
|----------|---------|-------------|
| `SA_DEFAULT_REGION` | `in` | Region code (us, gb, de, jp, in, etc.) |
| `SA_DEFAULT_EXCHANGE` | `.NS` | NSE (`.NS`) or BSE (`.BO`) — for India only |
| `SA_DEFAULT_PERIOD` | `1y` | Historical data period |
| `SA_CACHE_BACKEND` | `redis` | `redis`, `csv`, or `none` |
| `SA_REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `SA_CACHE_TTL` | `3600` | Cache TTL in seconds |
| `SA_SCREENER_ENABLED` | `true` | Use screener.in as fallback for peers |
| `SA_FA_DCF_ENABLED` | `true` | Run DCF valuation |
| `SA_FA_WACC_RISK_FREE_RATE` | `0.07` | India 10Y govt bond yield |
| `SA_PEERS_MAX_COUNT` | `10` | Max peers to compare |
| `SA_MCP_TRANSPORT` | `stdio` | `stdio` or `streamable-http` |
| `SA_MCP_PORT` | `3001` | Port for streamable-http |

See `configurations.env.example` for the full list.

## Python Library

```python
from stock_analyst import (
    analyze, get_fundamentals, get_technicals,
    get_news, get_market_mood, screen_stocks,
    search_tickers, analyze_asset,
)

# Indian stocks (default region)
result = analyze("RELIANCE")
ratios = get_fundamentals("TCS")
signals = get_technicals("INFY", period="6mo")

# Global stocks (any region)
us_stock = analyze("AAPL", region="us")
hk_stock = analyze("0700.HK", region="hk")
uk_stock = analyze("HSBA", region="gb")

# News with sentiment
news = get_news("TCS")
# Returns headlines with sentiment_score, sentiment_label, snippet

# Market mood (region-specific)
mood_in = get_market_mood(region="in")  # Includes MMI from tickertape
mood_us = get_market_mood(region="us")  # S&P 500 + VIX
mood_de = get_market_mood(region="de")  # DAX + VDAX

# Stock screener (any region)
results_in = screen_stocks({"sector": "Technology", "pe_max": 30}, region="in")
results_us = screen_stocks({"sector": "Technology", "pe_max": 40}, region="us")

# Ticker search
apple_results = search_tickers("Apple", instrument_type="stock", region="us")
crypto_results = search_tickers("Bitcoin", instrument_type="cryptocurrency")

# Multi-asset analysis
etf = analyze_asset("SPY", asset_type="etf")
commodity = analyze_asset("GC=F", asset_type="commodity")
crypto = analyze_asset("BTC-USD", asset_type="crypto")
currency = analyze_asset("EURUSD=X", asset_type="currency")
```

## Testing

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=stock_analyst --cov-report=term-missing

# Run specific test file
pytest tests/test_peers.py -v
```

## Data Sources

- **yfinance** — OHLCV, financials, balance sheet, cashflow, info, peer discovery via Industry API, stock screener via EquityQuery (50+ regions)
- **screener.in** — peer discovery + stock screener fallback for India (best-effort, graceful degradation)
- **tickertape.in** — Market Mood Index (MMI) scraping for India
- **VADER** — headline sentiment analysis (vaderSentiment)
- **India-adjusted defaults** — risk-free rate 7%, cost of debt 9%, tax 25%

## Supported Regions

50+ regions via yfinance: US, UK, Germany, France, Italy, Spain, Netherlands, Belgium, Switzerland, Austria, Sweden, Norway, Denmark, Finland, Poland, Czech Republic, Romania, Portugal, Greece, Hungary, Ireland, Lithuania, Latvia, Estonia, Canada, Mexico, Brazil, Argentina, Chile, Peru, Colombia, Venezuela, Australia, New Zealand, Japan, South Korea, China, Hong Kong, Singapore, Malaysia, Thailand, Philippines, Indonesia, Vietnam, Pakistan, Sri Lanka, UAE, Saudi Arabia, Kuwait, Qatar, Israel, Egypt, Turkey, South Africa, and more.

## Regions Quick Reference

| Region | Code | Primary Index | VIX |
|--------|------|---------------|-----|
| USA | `us` | S&P 500 (^GSPC) | ^VIX |
| UK | `gb` | FTSE 100 (^FTSE) | ^VIX |
| Germany | `de` | DAX (^GDAXI) | ^VDAX |
| France | `fr` | CAC 40 (^FCHI) | ^VDAX |
| Japan | `jp` | Nikkei 225 (^N225) | ^VIX |
| Hong Kong | `hk` | Hang Seng (^HSI) | ^VIX |
| India | `in` | Nifty 50 (^NSEI) | ^INDIAVIX |
| Australia | `au` | ASX 200 (^AXJO) | ^VIX |
| Canada | `ca` | TSX (^GSPTSE) | ^VIX |
| Brazil | `br` | Bovespa (^BVSP) | ^VIX |

## License

MIT
