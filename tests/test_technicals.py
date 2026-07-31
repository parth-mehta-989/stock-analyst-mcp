"""Tests for stock_analyst.engine.technicals."""

from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

from stock_analyst.engine.technicals import TechnicalAnalyzer


@pytest.fixture
def ta(config, null_cache, sample_ohlcv):
    provider = MagicMock()
    provider.get_history.return_value = sample_ohlcv
    return TechnicalAnalyzer(provider, null_cache, config)


class TestTechnicalAnalyzer:
    def test_analyze_returns_dict(self, ta):
        result = ta.analyze("TCS")
        assert isinstance(result, dict)
        assert result["symbol"] == "TCS"

    def test_current_price(self, ta):
        result = ta.analyze("TCS")
        assert result["current_price"] > 0

    def test_ema_values(self, ta):
        result = ta.analyze("TCS")
        assert result.get("ema_20") is not None
        assert result.get("ema_50") is not None
        # EMA 200 may be None with only 120 data points

    def test_ema_trend(self, ta):
        result = ta.analyze("TCS")
        assert result["ema_trend"] in ("bullish", "bearish", "neutral", "insufficient_data")

    def test_rsi(self, ta):
        result = ta.analyze("TCS")
        assert result.get("rsi") is not None
        assert 0 <= result["rsi"] <= 100

    def test_rsi_signal(self, ta):
        result = ta.analyze("TCS")
        assert result["rsi_signal"] in ("overbought", "oversold", "neutral", "insufficient_data")

    def test_macd_signal(self, ta):
        result = ta.analyze("TCS")
        assert result["macd_signal"] in (
            "bullish", "bearish", "bullish_crossover", "bearish_crossover",
            "neutral", "insufficient_data",
        )

    def test_bollinger(self, ta):
        result = ta.analyze("TCS")
        assert result.get("bollinger_position") in ("upper", "lower", "middle", "insufficient_data")

    def test_overall_signal(self, ta):
        result = ta.analyze("TCS")
        assert result["overall_signal"] in (
            "bullish", "moderately_bullish", "neutral",
            "moderately_bearish", "bearish", "insufficient_data",
        )

    def test_52w_high(self, ta):
        result = ta.analyze("TCS")
        assert "price_vs_52w_high_pct" in result

    def test_empty_data(self, config, null_cache):
        provider = MagicMock()
        provider.get_history.return_value = pd.DataFrame()
        ta = TechnicalAnalyzer(provider, null_cache, config)
        result = ta.analyze("EMPTY")
        assert "error" in result

    def test_cache_hit(self, config, sample_ohlcv):
        cache = MagicMock()
        cache.get.return_value = {"symbol": "TCS", "cached": True}
        provider = MagicMock()
        ta = TechnicalAnalyzer(provider, cache, config)
        result = ta.analyze("TCS")
        assert result["cached"] is True
        provider.get_history.assert_not_called()
