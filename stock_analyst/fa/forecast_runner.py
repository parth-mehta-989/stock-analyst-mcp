"""Run revenue forecast."""

from typing import Any, Dict, List, Optional

from stock_analyst.fa.forecast_builder import ForecastBuilder


def run_forecast(mapped_data: Dict[str, Any], config=None, scenarios: Optional[List[str]] = None) -> Dict[str, Any]:
    """Run forecast and return compact summary."""
    if config and scenarios is None:
        scenarios = config.forecast_scenarios

    scenarios = scenarios or ["base", "bull", "bear"]
    builder = ForecastBuilder(mapped_data)

    try:
        results = builder.run_full_forecast(scenarios=scenarios)
    except Exception as e:
        return {"error": str(e)}

    compact: Dict[str, Any] = {}

    trend = results.get("trend_analysis", {})
    if trend:
        compact["trend"] = {
            "direction": trend.get("trend", {}).get("direction"),
            "r_squared": trend.get("trend", {}).get("r_squared"),
            "average_growth_rate": trend.get("average_growth_rate"),
        }

    sc = results.get("scenario_comparison", {})
    if sc:
        compact["scenarios"] = sc.get("comparison", [])

    return compact
