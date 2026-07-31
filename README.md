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

## Data Sources

- **yfinance** — OHLCV, financials, balance sheet, cashflow, info, peer discovery via Industry API
- **screener.in** — peer discovery fallback (best-effort, graceful degradation)
- **India-adjusted defaults** — risk-free rate 7%, cost of debt 9%, tax 25%

## License

MIT
