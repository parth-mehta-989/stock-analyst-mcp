"""Tests for stock_analyst.analysis.report."""

import pytest

from stock_analyst.analysis.report import StockReport


class TestStockReport:
    def test_defaults(self):
        r = StockReport(symbol="TCS")
        assert r.symbol == "TCS"
        assert r.name == ""
        assert r.fundamentals == {}

    def test_to_dict(self):
        r = StockReport(symbol="TCS", name="Tata", current_price=3500)
        d = r.to_dict()
        assert d["symbol"] == "TCS"
        assert d["current_price"] == 3500
        assert isinstance(d["fundamentals"], dict)

    def test_all_fields(self):
        r = StockReport(
            symbol="TCS", name="Tata", sector="Tech", industry="IT",
            current_price=3500, market_cap=12e12, currency="INR",
            fundamentals={"a": 1}, dcf_valuation={"b": 2},
            technicals={"c": 3}, peer_comparison={"d": 4},
            news={"e": 5}, forecast={"f": 6},
        )
        d = r.to_dict()
        assert all(k in d for k in ["fundamentals", "dcf_valuation", "technicals", "peer_comparison", "news", "forecast"])
