"""Tests for stock_analyst.analysis.peer_comparison."""

import pytest

from stock_analyst.analysis.peer_comparison import build_peer_comparison


@pytest.fixture
def peer_fundamentals():
    return {
        "TCS": {"pe": 30, "pb": 12, "roe": 0.45, "debt_to_equity": 5, "name": "TCS"},
        "INFY": {"pe": 25, "pb": 8, "roe": 0.30, "debt_to_equity": 10, "name": "Infosys"},
        "WIPRO": {"pe": 20, "pb": 3, "roe": 0.18, "debt_to_equity": 30, "name": "Wipro"},
    }


@pytest.fixture
def peer_technicals():
    return {
        "TCS": {"rsi": 55, "ema_trend": "bullish", "macd_signal": "bullish"},
        "INFY": {"rsi": 65, "ema_trend": "neutral", "macd_signal": "bearish"},
        "WIPRO": {"rsi": 30, "ema_trend": "bearish", "macd_signal": "neutral"},
    }


class TestBuildPeerComparison:
    def test_basic_structure(self, peer_fundamentals, peer_technicals):
        result = build_peer_comparison(
            "TCS", peer_fundamentals, peer_technicals,
            ["pe", "pb", "roe", "debt_to_equity"],
            ["rsi", "ema_trend"],
        )
        assert result["target"] == "TCS"
        assert result["peer_count"] == 2
        assert "fundamental_comparison" in result
        assert "technical_comparison" in result

    def test_ranking_lower_is_better(self, peer_fundamentals, peer_technicals):
        result = build_peer_comparison(
            "TCS", peer_fundamentals, peer_technicals,
            ["pe", "debt_to_equity"],
            [],
        )
        # PE: lower is better -> WIPRO(20)=1, INFY(25)=2, TCS(30)=3
        tcs_ranks = None
        for row in result["fundamental_comparison"]:
            if row["symbol"] == "TCS":
                tcs_ranks = row["ranks"]
        assert tcs_ranks["pe"] == 3  # highest PE = worst rank

    def test_ranking_higher_is_better(self, peer_fundamentals, peer_technicals):
        result = build_peer_comparison(
            "TCS", peer_fundamentals, peer_technicals,
            ["roe"],
            [],
        )
        # ROE: higher is better -> TCS(0.45)=1
        tcs_ranks = None
        for row in result["fundamental_comparison"]:
            if row["symbol"] == "TCS":
                tcs_ranks = row["ranks"]
        assert tcs_ranks["roe"] == 1

    def test_target_ranking_summary(self, peer_fundamentals, peer_technicals):
        result = build_peer_comparison(
            "TCS", peer_fundamentals, peer_technicals,
            ["pe", "roe"],
            [],
        )
        ranking = result.get("target_fundamental_ranking", {})
        assert "pe" in ranking
        assert "roe" in ranking
        assert ranking["roe"] == "1/3"

    def test_empty_fundamentals(self, peer_technicals):
        result = build_peer_comparison("TCS", {}, peer_technicals, ["pe"], ["rsi"])
        assert result["peer_count"] == -1  # 0 - 1
        assert "fundamental_comparison" not in result

    def test_empty_technicals(self, peer_fundamentals):
        result = build_peer_comparison("TCS", peer_fundamentals, {}, ["pe"], ["rsi"])
        assert "technical_comparison" not in result

    def test_none_values_in_metrics(self):
        fund = {
            "TCS": {"pe": 30, "name": "TCS"},
            "INFY": {"pe": None, "name": "Infosys"},
        }
        result = build_peer_comparison("TCS", fund, {}, ["pe"], [])
        # INFY has None PE, should not crash ranking
        assert len(result["fundamental_comparison"]) == 2

    def test_exchange_suffix_target_matching(self, peer_fundamentals, peer_technicals):
        result = build_peer_comparison("TCS.NS", peer_fundamentals, peer_technicals, ["pe"], [])
        # Target key in dict is "TCS" but input is "TCS.NS"; should match by normalized ticker
        assert result["target"] == "TCS"

    def test_exchange_column(self):
        fund = {
            "TCS.NS": {"pe": 30, "name": "TCS"},
            "534064.BO": {"pe": 20, "name": "BSE Peer"},
        }
        tech = {
            "TCS.NS": {"rsi": 55},
            "534064.BO": {"rsi": 40},
        }
        result = build_peer_comparison("TCS.NS", fund, tech, ["pe"], ["rsi"])
        symbols = {r["symbol"]: r["exchange"] for r in result["fundamental_comparison"]}
        assert symbols["TCS.NS"] == "NSE"
        assert symbols["534064.BO"] == "BSE"
        tech_symbols = {r["symbol"]: r["exchange"] for r in result["technical_comparison"]}
        assert tech_symbols["534064.BO"] == "BSE"
