"""Tests for stock_analyst.analysis.formatter."""

import json

import pytest

from stock_analyst.analysis.formatter import to_json, to_markdown, _fmt_num
from stock_analyst.analysis.report import StockReport


@pytest.fixture
def report():
    return StockReport(
        symbol="TCS",
        name="Tata Consultancy Services",
        sector="Technology",
        industry="IT Services",
        current_price=3500.0,
        market_cap=12_000_000_000_000,
        currency="INR",
        fundamentals={
            "categories": {
                "profitability": {
                    "roe": {"value": 0.45, "name": "Return on Equity", "interpretation": "Excellent"},
                },
            },
        },
        technicals={"rsi": 55, "ema_trend": "bullish", "symbol": "TCS"},
        peer_comparison={
            "fundamental_comparison": [
                {"symbol": "TCS", "pe": 30, "ranks": {"pe": 2}},
                {"symbol": "INFY", "pe": 25, "ranks": {"pe": 1}},
            ],
            "target_fundamental_ranking": {"pe": "2/2"},
        },
        dcf_valuation={"wacc": 0.11, "value_per_share": {"perpetuity_growth": 4000, "exit_multiple": 3800}},
        news={"headlines": [{"title": "TCS wins deal", "publisher": "ET"}]},
    )


class TestToJson:
    def test_valid_json(self, report):
        result = to_json(report)
        data = json.loads(result)
        assert data["symbol"] == "TCS"

    def test_pretty(self, report):
        result = to_json(report, pretty=True)
        assert "\n" in result

    def test_compact(self, report):
        result = to_json(report, pretty=False)
        assert "\n" not in result


class TestToMarkdown:
    def test_header(self, report):
        md = to_markdown(report)
        assert "# Tata Consultancy Services" in md

    def test_fundamentals_table(self, report):
        md = to_markdown(report)
        assert "Return on Equity" in md

    def test_technicals_section(self, report):
        md = to_markdown(report)
        assert "Technical Analysis" in md
        assert "rsi" in md

    def test_peer_section(self, report):
        md = to_markdown(report)
        assert "Peer Comparison" in md

    def test_dcf_section(self, report):
        md = to_markdown(report)
        assert "DCF Valuation" in md

    def test_news_section(self, report):
        md = to_markdown(report)
        assert "TCS wins deal" in md

    def test_empty_report(self):
        report = StockReport(symbol="EMPTY")
        md = to_markdown(report)
        assert "EMPTY" in md


class TestFmtNum:
    def test_trillion(self):
        assert "T" in _fmt_num(1.5e12)

    def test_billion(self):
        assert "B" in _fmt_num(2.5e9)

    def test_crore(self):
        assert "Cr" in _fmt_num(5e7)

    def test_lakh(self):
        assert "L" in _fmt_num(2e5)

    def test_small(self):
        assert _fmt_num(1234) == "1,234"

    def test_none(self):
        assert _fmt_num(None) == "N/A"
