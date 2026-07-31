# stock-analyst-mcp

MCP server for Indian stock market analysis — fundamentals, technicals, DCF valuation, peer comparison, and more.

<!-- mcp-name: io.github.parth-mehta-989/stock-analyst-mcp -->

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
| `analyze_stock` | Full analysis: fundamentals + technicals + peers + DCF + forecast + news |
| `get_fundamentals` | Financial ratios: profitability, liquidity, leverage, efficiency, valuation |
| `get_technicals` | Technical signals: EMA trend, RSI, MACD, Bollinger position |
| `get_peer_comparison` | Peer fundamental + technical metrics with rankings |
| `get_dcf_valuation` | DCF: WACC (India-adjusted), equity value/share, sensitivity range |
| `get_revenue_forecast` | Revenue forecast: base/bull/bear scenarios |
| `get_news` | Recent headlines + analyst recommendation summary |
| `compare_stocks` | Side-by-side comparison of multiple stocks |
| `get_raw_data` | Fetch cached raw financials for deep dives |
| `get_config` | View current configuration settings for all analysis tools |
| `set_config` | Update configuration settings dynamically (e.g., technical analysis period) |

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
```

## Configuration

All settings configurable via environment variables with `SA_` prefix. Defaults work out of the box for Indian markets (NSE).

| Variable | Default | Description |
|----------|---------|-------------|
| `SA_DEFAULT_EXCHANGE` | `.NS` | NSE (`.NS`) or BSE (`.BO`) |
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
from stock_analyst import analyze, get_fundamentals, get_technicals

result = analyze("RELIANCE")
ratios = get_fundamentals("TCS")
signals = get_technicals("INFY", period="6mo")
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

- **yfinance** — OHLCV, financials, balance sheet, cashflow, info, peer discovery via Industry API
- **screener.in** — peer discovery fallback (best-effort, graceful degradation)
- **India-adjusted defaults** — risk-free rate 7%, cost of debt 9%, tax 25%

## License

MIT
