"""StockReport dataclass — combines all analysis into compact output."""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass
class StockReport:
    symbol: str
    name: str = ""
    sector: str = ""
    industry: str = ""
    current_price: Optional[float] = None
    market_cap: Optional[float] = None
    currency: str = "INR"

    # Fundamental ratios (from financial-analyst skill)
    fundamentals: Dict[str, Any] = field(default_factory=dict)

    # DCF valuation summary
    dcf_valuation: Dict[str, Any] = field(default_factory=dict)

    # Technical signals (compact)
    technicals: Dict[str, Any] = field(default_factory=dict)

    # Peer comparison
    peer_comparison: Dict[str, Any] = field(default_factory=dict)

    # News + recommendations
    news: Dict[str, Any] = field(default_factory=dict)

    # Revenue forecast
    forecast: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
