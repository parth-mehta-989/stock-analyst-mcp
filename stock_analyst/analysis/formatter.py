"""JSON / Markdown output formatting."""

import json
from typing import Any, Dict

from stock_analyst.analysis.report import StockReport


def to_json(report: StockReport, pretty: bool = True) -> str:
    data = report.to_dict()
    indent = 2 if pretty else None
    return json.dumps(data, indent=indent, default=str)


def to_markdown(report: StockReport) -> str:
    lines = [
        f"# {report.name or report.symbol} ({report.symbol})",
        "",
        f"**Sector**: {report.sector} | **Industry**: {report.industry}",
        f"**Price**: {report.currency} {report.current_price} | **Market Cap**: {_fmt_num(report.market_cap)}",
        "",
    ]

    # Fundamentals
    if report.fundamentals:
        lines.append("## Financial Ratios")
        lines.append("")
        cats = report.fundamentals.get("categories", {})
        for cat_name, ratios in cats.items():
            lines.append(f"### {cat_name.title()}")
            lines.append("")
            lines.append("| Ratio | Value | Interpretation |")
            lines.append("|-------|-------|----------------|")
            for key, info in ratios.items():
                val = info.get("value", "N/A")
                if isinstance(val, float):
                    val = f"{val:.4f}"
                interp = info.get("interpretation", "")
                lines.append(f"| {info.get('name', key)} | {val} | {interp} |")
            lines.append("")

    # Technicals
    if report.technicals:
        lines.append("## Technical Analysis")
        lines.append("")
        for k, v in report.technicals.items():
            if k != "symbol":
                lines.append(f"- **{k}**: {v}")
        lines.append("")

    # Peer Comparison
    if report.peer_comparison:
        lines.append("## Peer Comparison")
        lines.append("")
        fund = report.peer_comparison.get("fundamental_comparison", [])
        if fund:
            lines.append("### Fundamental Metrics")
            lines.append("")
            headers = [k for k in fund[0].keys() if k not in ("ranks",)]
            lines.append("| " + " | ".join(headers) + " |")
            lines.append("|" + "|".join(["---"] * len(headers)) + "|")
            for row in fund:
                vals = [str(row.get(h, "")) for h in headers]
                lines.append("| " + " | ".join(vals) + " |")
            lines.append("")

        ranking = report.peer_comparison.get("target_fundamental_ranking", {})
        if ranking:
            lines.append("### Target Ranking")
            for metric, rank in ranking.items():
                lines.append(f"- **{metric}**: {rank}")
            lines.append("")

    # DCF
    if report.dcf_valuation and "error" not in report.dcf_valuation:
        lines.append("## DCF Valuation")
        lines.append("")
        dcf = report.dcf_valuation
        vps = dcf.get("value_per_share", {})
        if vps:
            lines.append(f"- **WACC**: {dcf.get('wacc')}")
            lines.append(f"- **Value/Share (Perpetuity)**: {vps.get('perpetuity_growth')}")
            lines.append(f"- **Value/Share (Exit Multiple)**: {vps.get('exit_multiple')}")
        sr = dcf.get("sensitivity_range", {})
        if sr:
            lines.append(f"- **Sensitivity Range**: {sr.get('min_share_price')} - {sr.get('max_share_price')}")
        lines.append("")

    # News
    if report.news:
        lines.append("## News & Recommendations")
        lines.append("")
        sentiment_summary = report.news.get("sentiment_summary", {})
        if sentiment_summary:
            label = sentiment_summary.get("overall_label", "N/A")
            score = sentiment_summary.get("average_score", "N/A")
            lines.append(f"**Overall Sentiment**: {label} (score: {score})")
            lines.append("")
        for h in report.news.get("headlines", []):
            sent_label = h.get("sentiment_label", "")
            sent_tag = f" [{sent_label}]" if sent_label else ""
            lines.append(f"- {h.get('title', '')} ({h.get('publisher', '')}){sent_tag}")
        lines.append("")

    return "\n".join(lines)


def _fmt_num(val) -> str:
    if val is None:
        return "N/A"
    if val >= 1e12:
        return f"{val/1e12:.2f}T"
    if val >= 1e9:
        return f"{val/1e9:.2f}B"
    if val >= 1e7:
        return f"{val/1e7:.2f}Cr"
    if val >= 1e5:
        return f"{val/1e5:.2f}L"
    return f"{val:,.0f}"
