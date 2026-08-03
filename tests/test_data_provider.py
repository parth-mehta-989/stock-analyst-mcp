"""Tests for stock_analyst.engine.data_provider."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from stock_analyst.engine.data_provider import YFinanceProvider, get_provider


class TestYFinanceProvider:
    @pytest.fixture
    def provider(self, config):
        return YFinanceProvider(config)

    def test_ticker_passes_symbol_through(self, provider):
        """Provider now passes symbols through; resolution happens at public API layer."""
        t = provider._ticker("TCS")
        assert t.ticker == "TCS"

    def test_ticker_preserves_ns(self, provider):
        t = provider._ticker("TCS.NS")
        assert t.ticker == "TCS.NS"

    def test_ticker_preserves_bo(self, provider):
        t = provider._ticker("RELIANCE.BO")
        assert t.ticker == "RELIANCE.BO"

    def test_ticker_uppercase(self, provider):
        t = provider._ticker("infy")
        assert t.ticker == "INFY"

    def test_ticker_strips(self, provider):
        t = provider._ticker("  TCS  ")
        assert t.ticker == "TCS"

    def test_ticker_preserves_us_ticker(self, provider):
        t = provider._ticker("AAPL")
        assert t.ticker == "AAPL"

    def test_ticker_preserves_explicit_suffixes(self, provider):
        t = provider._ticker("0700.HK")
        assert t.ticker == "0700.HK"


class TestGetProvider:
    def test_returns_yfinance_provider(self, config):
        p = get_provider(config)
        assert isinstance(p, YFinanceProvider)
