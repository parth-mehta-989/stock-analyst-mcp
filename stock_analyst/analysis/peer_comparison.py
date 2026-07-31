"""Peer comparison: fundamental + technical tables with rankings."""

from typing import Any, Dict, List, Optional


def _strip_exchange(symbol: str) -> str:
    """Remove .NS / .BO suffix and normalize."""
    return symbol.upper().strip().replace(".NS", "").replace(".BO", "")


def _exchange(symbol: str) -> str:
    """Return exchange label from symbol suffix."""
    s = symbol.upper().strip()
    if s.endswith(".NS"):
        return "NSE"
    if s.endswith(".BO"):
        return "BSE"
    return ""


def build_peer_comparison(
    target_symbol: str,
    peer_fundamentals: Dict[str, Any],
    peer_technicals: Dict[str, Any],
    fundamental_metrics: List[str],
    technical_metrics: List[str],
) -> Dict[str, Any]:
    """Build compact peer comparison with rankings."""
    target_sym = _strip_exchange(target_symbol)

    # Find the full key for the target (e.g. TCS.NS) from the fundamentals dict
    target_full = next(
        (k for k in peer_fundamentals if _strip_exchange(k) == target_sym),
        target_symbol,
    )

    result: Dict[str, Any] = {
        "target": target_full,
        "peer_count": len(peer_fundamentals) - 1,
    }

    # Fundamental comparison
    if peer_fundamentals:
        fund_table = []
        for sym, data in peer_fundamentals.items():
            row = {
                "symbol": sym,
                "exchange": data.get("exchange") or _exchange(sym),
                "name": data.get("name", sym),
            }
            for metric in fundamental_metrics:
                row[metric] = data.get(metric)
            fund_table.append(row)

        # Rankings (higher is better for most metrics, lower for PE/PB/D_E)
        lower_is_better = {"pe", "pb", "debt_to_equity"}
        rankings = {}
        for metric in fundamental_metrics:
            vals = [(r["symbol"], r[metric]) for r in fund_table if r[metric] is not None]
            if vals:
                reverse = metric not in lower_is_better
                sorted_vals = sorted(vals, key=lambda x: x[1], reverse=reverse)
                for rank, (sym, _) in enumerate(sorted_vals, 1):
                    rankings.setdefault(sym, {})[metric] = rank

        # Add rank to each row
        for row in fund_table:
            row["ranks"] = rankings.get(row["symbol"], {})

        result["fundamental_comparison"] = fund_table

        # Target ranking summary
        target_ranks = rankings.get(target_full, {})
        if target_ranks:
            total_peers = len(peer_fundamentals)
            result["target_fundamental_ranking"] = {
                metric: f"{rank}/{total_peers}"
                for metric, rank in target_ranks.items()
            }

    # Technical comparison
    if peer_technicals:
        tech_table = []
        for sym, data in peer_technicals.items():
            row = {"symbol": sym, "exchange": data.get("exchange") or _exchange(sym)}
            for metric in technical_metrics:
                row[metric] = data.get(metric)
            tech_table.append(row)

        result["technical_comparison"] = tech_table

    return result
