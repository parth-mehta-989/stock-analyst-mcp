"""Run financial ratio calculations."""

from typing import Any, Dict, Optional

from stock_analyst.fa.ratio_calculator import FinancialRatioCalculator


def run_ratios(mapped_data: Dict[str, Any], config=None, category: Optional[str] = None) -> Dict[str, Any]:
    """Run ratio calculation and return results with interpretations."""
    calc = FinancialRatioCalculator(mapped_data)
    calc.calculate_all()
    return calc.to_json(category=category)
