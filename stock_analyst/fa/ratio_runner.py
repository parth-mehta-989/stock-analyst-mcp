"""Wraps financial-analyst ratio_calculator.py."""

import logging
import sys
from typing import Any, Dict, Optional

from stock_analyst.config import Settings

logger = logging.getLogger(__name__)

_calculator_cls = None


def _load_calculator(config: Settings):
    global _calculator_cls
    if _calculator_cls is not None:
        return _calculator_cls

    scripts_dir = config.fa_scripts_dir
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    try:
        from ratio_calculator import FinancialRatioCalculator
        _calculator_cls = FinancialRatioCalculator
        return _calculator_cls
    except ImportError as e:
        logger.error("Cannot import ratio_calculator from %s: %s", scripts_dir, e)
        raise


def run_ratios(mapped_data: Dict[str, Any], config: Settings, category: Optional[str] = None) -> Dict[str, Any]:
    """Run ratio calculation and return results with interpretations."""
    cls = _load_calculator(config)
    calc = cls(mapped_data)
    calc.calculate_all()
    return calc.to_json(category=category)
