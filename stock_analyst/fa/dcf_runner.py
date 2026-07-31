"""Run DCF valuation."""

from typing import Any, Dict

from stock_analyst.fa.dcf_valuation import DCFModel, safe_divide


def run_dcf(mapped_data: Dict[str, Any], config=None) -> Dict[str, Any]:
    """Run DCF valuation and return compact summary."""
    model = DCFModel()
    model.set_historical_financials(mapped_data["historical"])
    model.set_assumptions(mapped_data["assumptions"])

    try:
        results = model.run_full_valuation()
    except (ValueError, ZeroDivisionError) as e:
        return {"error": str(e)}

    return {
        "wacc": results.get("wacc"),
        "value_per_share": results.get("value_per_share"),
        "enterprise_value": results.get("enterprise_value"),
        "equity_value": results.get("equity_value"),
        "sensitivity_range": _extract_sensitivity_range(results),
    }


def _extract_sensitivity_range(results: Dict[str, Any]) -> Dict[str, Any]:
    """Extract min/max share price from sensitivity table."""
    sa = results.get("sensitivity_analysis", {})
    table = sa.get("share_price_table", [])
    if not table:
        return {}

    all_vals = []
    for row in table:
        for v in row:
            if v is not None and v != float("inf"):
                all_vals.append(v)

    if not all_vals:
        return {}

    return {
        "min_share_price": round(min(all_vals), 2),
        "max_share_price": round(max(all_vals), 2),
    }
