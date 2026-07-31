"""Map yfinance data to financial-analyst skill input schemas."""

import math
from typing import Any, Dict, List, Optional

import pandas as pd

from stock_analyst.config import Settings


def _safe_float(val: Any) -> float:
    if val is None:
        return 0.0
    try:
        f = float(val)
        return 0.0 if (math.isnan(f) or math.isinf(f)) else f
    except (TypeError, ValueError):
        return 0.0


def _get_latest(df: pd.DataFrame, row_name: str) -> float:
    """Get the most recent value from a financial statement DataFrame."""
    if df is None or df.empty:
        return 0.0
    for name in [row_name]:
        if name in df.index:
            vals = df.loc[name].dropna()
            if not vals.empty:
                return _safe_float(vals.iloc[0])
    return 0.0


def _get_series(df: pd.DataFrame, row_name: str) -> List[float]:
    """Get all year values for a row, most-recent-first → reversed to oldest-first."""
    if df is None or df.empty:
        return []
    if row_name in df.index:
        vals = df.loc[row_name].dropna().tolist()
        return [_safe_float(v) for v in reversed(vals)]
    return []


def map_to_ratio_input(
    info: Dict[str, Any],
    financials: pd.DataFrame,
    balance_sheet: pd.DataFrame,
    cashflow: pd.DataFrame,
) -> Dict[str, Any]:
    """Map yfinance data to ratio_calculator.py input schema."""
    return {
        "income_statement": {
            "revenue": _get_latest(financials, "Total Revenue"),
            "cost_of_goods_sold": _get_latest(financials, "Cost Of Revenue"),
            "operating_income": _get_latest(financials, "Operating Income"),
            "net_income": _get_latest(financials, "Net Income"),
            "interest_expense": _get_latest(financials, "Interest Expense"),
            "ebitda": _get_latest(financials, "EBITDA"),
        },
        "balance_sheet": {
            "total_equity": _get_latest(balance_sheet, "Stockholders Equity"),
            "total_assets": _get_latest(balance_sheet, "Total Assets"),
            "current_assets": _get_latest(balance_sheet, "Current Assets"),
            "current_liabilities": _get_latest(balance_sheet, "Current Liabilities"),
            "inventory": _get_latest(balance_sheet, "Inventory"),
            "cash_and_equivalents": _get_latest(balance_sheet, "Cash And Cash Equivalents"),
            "total_debt": _get_latest(balance_sheet, "Total Debt"),
            "accounts_receivable": _get_latest(balance_sheet, "Net Receivables"),
        },
        "cash_flow": {
            "operating_cash_flow": _get_latest(cashflow, "Operating Cash Flow"),
        },
        "market_data": {
            "market_cap": _safe_float(info.get("marketCap")),
            "share_price": _safe_float(info.get("currentPrice")),
            "shares_outstanding": _safe_float(info.get("sharesOutstanding")),
            "earnings_growth_rate": _safe_float(info.get("earningsGrowth")),
        },
    }


def map_to_dcf_input(
    info: Dict[str, Any],
    financials: pd.DataFrame,
    balance_sheet: pd.DataFrame,
    config: Settings,
) -> Dict[str, Any]:
    """Map yfinance data to dcf_valuation.py input schema."""
    revenue_series = _get_series(financials, "Total Revenue")
    total_debt = _get_latest(balance_sheet, "Total Debt")
    cash = _get_latest(balance_sheet, "Cash And Cash Equivalents")
    net_debt = total_debt - cash

    return {
        "historical": {
            "revenue": revenue_series if revenue_series else [0.0],
            "net_debt": net_debt,
            "shares_outstanding": _safe_float(info.get("sharesOutstanding", 1)),
        },
        "assumptions": {
            "projection_years": config.fa_dcf_projection_years,
            "terminal_growth_rate": config.fa_dcf_terminal_growth,
            "exit_ev_ebitda_multiple": config.fa_dcf_exit_multiple,
            "terminal_ebitda_margin": 0.20,
            "wacc_inputs": {
                "risk_free_rate": config.fa_wacc_risk_free_rate,
                "equity_risk_premium": config.fa_wacc_equity_risk_premium,
                "beta": _safe_float(info.get("beta", 1.0)),
                "cost_of_debt": config.fa_wacc_cost_of_debt,
                "tax_rate": config.fa_wacc_tax_rate,
                "debt_weight": config.fa_wacc_debt_weight,
                "equity_weight": config.fa_wacc_equity_weight,
            },
        },
    }


def map_to_forecast_input(
    financials: pd.DataFrame,
    config: Settings,
) -> Dict[str, Any]:
    """Map yfinance data to forecast_builder.py input schema."""
    revenue_series = _get_series(financials, "Total Revenue")
    historical_periods = [{"revenue": r} for r in revenue_series]

    # Compute average growth rate from revenue series
    growth_rates = []
    for i in range(1, len(revenue_series)):
        if revenue_series[i - 1] > 0:
            g = (revenue_series[i] - revenue_series[i - 1]) / revenue_series[i - 1]
            growth_rates.append(g)
    avg_growth = sum(growth_rates) / len(growth_rates) if growth_rates else 0.05

    # Derive gross margin from latest financials
    revenue = _get_latest(financials, "Total Revenue")
    cogs = _get_latest(financials, "Cost Of Revenue")
    gross_margin = (revenue - cogs) / revenue if revenue > 0 else 0.40

    scenarios = {}
    for s in config.forecast_scenarios:
        if s == "base":
            scenarios[s] = {"growth_adjustment": 0.0, "margin_adjustment": 0.0}
        elif s == "bull":
            scenarios[s] = {"growth_adjustment": 0.05, "margin_adjustment": 0.02}
        elif s == "bear":
            scenarios[s] = {"growth_adjustment": -0.05, "margin_adjustment": -0.02}

    return {
        "forecast_periods": 12,
        "historical_periods": historical_periods,
        "assumptions": {
            "revenue_growth_rate": avg_growth,
            "gross_margin": gross_margin,
            "opex_pct_revenue": 0.25,
        },
        "scenarios": scenarios,
    }
