# Configuration Guide: get_config & set_config Tools

The stock-analyst MCP server exposes two tools for dynamic configuration management: `get_config` and `set_config`. This allows MCP clients to customize analysis parameters on-the-fly without restarting.

**v0.5.0 Update**: Performance improvements via parallel I/O don't require configuration changes. Peer analysis is now 3-19x faster by default.

## Quick Start

### View Current Configuration

```python
from stock_analyst import get_config

config = get_config()
print(config)
```

Returns:
```json
{
  "data_provider": "yfinance",
  "default_exchange": ".NS",
  "default_period": "1y",
  "default_interval": "1d",
  "cache_backend": "redis",
  "cache_ttl": 3600,
  "technical_analysis": {
    "ema_periods": "20,50,200",
    "rsi_period": 14,
    "macd_params": "12,26,9",
    "bollinger_enabled": true,
    "bollinger_period": 20
  },
  "financial_analysis": {
    "dcf_enabled": true,
    "dcf_projection_years": 5,
    "dcf_terminal_growth": 0.025,
    "dcf_exit_multiple": 12.0,
    "wacc_risk_free_rate": 0.07,
    "wacc_equity_risk_premium": 0.06,
    "wacc_cost_of_debt": 0.09,
    "wacc_tax_rate": 0.25,
    "wacc_debt_weight": 0.3,
    "wacc_equity_weight": 0.7,
    "forecast_scenarios": "base,bull,bear"
  },
  "peer_comparison": {
    "max_count": 10,
    "fundamental_comparison": true,
    "technical_comparison": true,
    "fundamental_metrics": "pe,pb,roe,debt_to_equity,dividend_yield,market_cap,net_margin",
    "technical_metrics": "rsi,ema_trend,macd_signal,price_vs_ema200"
  },
  "output": {
    "format": "json",
    "include_raw": false,
    "pretty": true
  }
}
```

### Update a Configuration

```python
from stock_analyst import set_config

# Change technical analysis period to 1 day
result = set_config("default_period", "1d")
print(result)
```

Returns:
```json
{
  "status": "success",
  "key": "default_period",
  "new_value": "1d",
  "affected_tools": ["all_tools"],
  "message": "Config updated: default_period = 1d"
}
```

## Use Cases

### 1. Short-Term Technical Analysis

```python
from stock_analyst import set_config, get_technicals

# Switch to 1-day data with faster RSI
set_config("default_period", "1d")
set_config("ta_rsi_period", "7")  # Faster RSI for day trading

signals = get_technicals("RELIANCE")
# Now uses 1-day OHLCV with RSI(7) instead of RSI(14)
```

### 2. Conservative DCF Valuation

```python
from stock_analyst import set_config, get_dcf_valuation

# Use conservative assumptions
set_config("fa_dcf_projection_years", "10")
set_config("fa_dcf_terminal_growth", "0.02")  # 2% terminal growth
set_config("fa_wacc_risk_free_rate", "0.08")  # Higher risk-free rate
set_config("fa_wacc_equity_risk_premium", "0.08")  # Higher risk premium

valuation = get_dcf_valuation("RELIANCE")
# More conservative valuation
```

### 3. Aggressive Growth Assumptions

```python
from stock_analyst import set_config, get_dcf_valuation

# Use aggressive assumptions
set_config("fa_dcf_projection_years", "5")
set_config("fa_dcf_terminal_growth", "0.04")  # 4% terminal growth
set_config("fa_wacc_risk_free_rate", "0.06")  # Lower risk-free rate
set_config("fa_dcf_exit_multiple", "15.0")  # Higher exit multiple

valuation = get_dcf_valuation("INFY")
# More optimistic valuation
```

### 4. Focused Peer Comparison

```python
from stock_analyst import set_config, get_peer_comparison

# Compare with fewer, more relevant peers
set_config("peers_max_count", "5")

comparison = get_peer_comparison("HDFCBANK")
# Only top 5 peers instead of 10
```

### 5. Medium-Term Swing Trading

```python
from stock_analyst import set_config, get_technicals

# 3-month data with custom EMA periods
set_config("default_period", "3mo")
set_config("ta_ema_periods", "10,30,50")  # Faster EMAs for swing trading
set_config("ta_rsi_period", "10")  # Faster RSI

signals = get_technicals("TCS")
# Optimized for swing trading timeframe
```

## Configuration Keys Reference

### Data & Cache
- `default_period` (str): Historical period - `1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max`
- `default_interval` (str): Data interval - `1m, 5m, 15m, 30m, 60m, 1d, 1wk, 1mo`
- `cache_ttl` (int): Cache TTL in seconds (default: 3600)

### Technical Analysis
- `ta_rsi_period` (int): RSI period (default: 14)
- `ta_ema_periods` (str): Comma-separated EMA periods (default: `20,50,200`)
- `ta_macd_params` (str): MACD (fast, slow, signal) (default: `12,26,9`)
- `ta_bollinger_enabled` (bool): Enable Bollinger Bands (default: true)
- `ta_bollinger_period` (int): Bollinger Bands period (default: 20)

### Financial Analysis (DCF)
- `fa_dcf_enabled` (bool): Enable DCF valuation (default: true)
- `fa_dcf_projection_years` (int): Projection years (default: 5)
- `fa_dcf_terminal_growth` (float): Terminal growth rate (default: 0.025)
- `fa_dcf_exit_multiple` (float): Exit multiple (default: 12.0)

### WACC Parameters (India-adjusted defaults)
- `fa_wacc_risk_free_rate` (float): Risk-free rate (default: 0.07)
- `fa_wacc_equity_risk_premium` (float): Equity risk premium (default: 0.06)
- `fa_wacc_cost_of_debt` (float): Cost of debt (default: 0.09)
- `fa_wacc_tax_rate` (float): Tax rate (default: 0.25)
- `fa_wacc_debt_weight` (float): Debt weight in WACC (default: 0.30)
- `fa_wacc_equity_weight` (float): Equity weight in WACC (default: 0.70)

### Peer Comparison
- `peers_max_count` (int): Max peers to compare (default: 10)
- `peers_fundamental_comparison` (bool): Include fundamentals (default: true)
- `peers_technical_comparison` (bool): Include technicals (default: true)
- `peers_fundamental_metrics` (str): Metrics to compare (default: `pe,pb,roe,debt_to_equity,dividend_yield,market_cap,net_margin`)
- `peers_technical_metrics` (str): Technical metrics (default: `rsi,ema_trend,macd_signal,price_vs_ema200`)

### Output
- `output_format` (str): Output format - `json` or `markdown` (default: `json`)
- `output_include_raw` (bool): Include raw data (default: false)
- `output_pretty` (bool): Pretty-print output (default: true)

## Error Handling

### Invalid Key
```python
result = set_config("invalid_key", "value")
# Returns: {"error": "Unknown config key: invalid_key", "valid_keys": [...]}
```

### Type Conversion Error
```python
result = set_config("ta_rsi_period", "not_a_number")
# Returns: {"error": "Failed to convert value: invalid literal for int()...", ...}
```

### Valid Type Conversions
- `int`: "14" → 14
- `float`: "0.025" → 0.025
- `bool`: "true", "1", "yes" → True; "false", "0", "no" → False
- `str`: "20,50,200" → "20,50,200"

## Affected Tools

When you update a config, the response includes which tools are affected:

```python
result = set_config("ta_rsi_period", "21")
print(result["affected_tools"])
# Output: ["get_technicals", "analyze_stock"]
```

This helps you understand which subsequent tool calls will use the new configuration.

## Best Practices

1. **Check current config before changing**: Use `get_config()` to understand current settings
2. **Validate changes**: Check the response status and affected_tools
3. **Use appropriate periods**: Match analysis period to your investment horizon
   - Day trading: `1d`, `5d`
   - Swing trading: `1mo`, `3mo`
   - Positional: `6mo`, `1y`
   - Long-term: `2y`, `5y`
4. **Reset to defaults**: Use environment variables or restart to reset to defaults
5. **Document your assumptions**: When sharing analysis, note the config changes you made

## Integration with MCP Clients

### Claude Desktop / Devin CLI

```
User: "Analyze RELIANCE with 1-day technicals"
Assistant: 
1. Calls set_config("default_period", "1d")
2. Calls get_technicals("RELIANCE")
3. Returns short-term technical signals
```

### Programmatic Usage

```python
from stock_analyst import set_config, get_technicals, analyze

# Configure for day trading
set_config("default_period", "1d")
set_config("ta_rsi_period", "7")

# Get analysis with custom config
signals = get_technicals("RELIANCE")
full_analysis = analyze("RELIANCE")
```

## Limitations & Notes

- Configuration changes are **session-scoped** (reset on server restart)
- Changes affect **all subsequent calls** in the session
- Type conversion is **strict** (invalid types return error)
- Boolean values accept: `true/false`, `1/0`, `yes/no` (case-insensitive)
- Comma-separated values must be valid (e.g., `ta_ema_periods` must be integers)
