"""Tests for stock_analyst.engine.data_provider."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from stock_analyst.engine.data_provider import YFinanceProvider, get_provider


class TestYFinanceProvider:
    @pytest.fixture
    def provider(self, config):
        return YFinanceProvider(config)

    def test_ticker_appends_exchange(self, provider):
        t = provider._ticker("TCS")
        assert t.ticker == "TCS.NS"

    def test_ticker_preserves_ns(self, provider):
        t = provider._ticker("TCS.NS")
        assert t.ticker == "TCS.NS"

    def test_ticker_preserves_bo(self, provider):
        t = provider._ticker("RELIANCE.BO")
        assert t.ticker == "RELIANCE.BO"

    def test_ticker_uppercase(self, provider):
        t = provider._ticker("infy")
        assert t.ticker == "INFY.NS"

    def test_ticker_strips(self, provider):
        t = provider._ticker("  TCS  ")
        assert t.ticker == "TCS.NS"


class TestGetProvider:
    def test_returns_yfinance_provider(self, config):
        p = get_provider(config)
        assert isinstance(p, YFinanceProvider)
