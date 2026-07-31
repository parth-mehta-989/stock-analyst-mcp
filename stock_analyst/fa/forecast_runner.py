"""Wraps financial-analyst forecast_builder.py."""

import logging
import sys
from typing import Any, Dict, List, Optional

from stock_analyst.config import Settings

logger = logging.getLogger(__name__)

_builder_cls = None


def _load_builder(config: Settings):
    global _builder_cls
    if _builder_cls is not None:
        return _builder_cls

    scripts_dir = config.fa_scripts_dir
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    try:
        from forecast_builder import ForecastBuilder
        _builder_cls = ForecastBuilder
        return _builder_cls
    except ImportError as e:
        logger.error("Cannot import forecast_builder from %s: %s", scripts_dir, e)
        raise


def run_forecast(mapped_data: Dict[str, Any], config: Settings, scenarios: Optional[List[str]] = None) -> Dict[str, Any]:
    """Run forecast and return compact summary."""
    cls = _load_builder(config)
    builder = cls(mapped_data)

    scenarios = scenarios or config.forecast_scenarios

    try:
        results = builder.run_full_forecast(scenarios=scenarios)
    except Exception as e:
        return {"error": str(e)}

    # Compact: trend + scenario comparison
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
