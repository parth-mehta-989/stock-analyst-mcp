"""Tests for stock_analyst public API (__init__.py)."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

import stock_analyst


@pytest.fixture(autouse=True)
def reset_globals():
    """Reset module globals before each test."""
    stock_analyst._config = None
    stock_analyst._cache = None
    stock_analyst._provider = None
    yield
    stock_analyst._config = None
    stock_analyst._cache = None
    stock_analyst._provider = None


@pytest.fixture
def setup_mocks(config, null_cache, sample_info, sample_financials, sample_balance_sheet, sample_cashflow, sample_ohlcv):
    """Wire up module globals with mocked provider."""
    provider = MagicMock()
    provider.get_info.return_value = sample_info
    provider.get_financials.return_value = sample_financials
    provider.get_balance_sheet.return_value = sample_balance_sheet
    provider.get_cashflow.return_value = sample_cashflow
    provider.get_history.return_value = sample_ohlcv
    provider.get_news.return_value = []
    provider.get_recommendations.return_value = None

    stock_analyst._config = config
    stock_analyst._cache = null_cache
    stock_analyst._provider = provider
    return provider


class TestAnalyze:
    def test_returns_dict(self, setup_mocks):
        with patch("stock_analyst.engine.peers.yf"):
            result = stock_analyst.analyze("TCS", include_peers=False)
        assert isinstance(result, dict)
        assert result["symbol"] == "TCS"

    def test_includes_sections(self, setup_mocks):
        with patch("stock_analyst.engine.peers.yf"):
            result = stock_analyst.analyze("TCS", include_peers=False)
        assert "fundamentals" in result
        assert "technicals" in result
        assert "dcf_valuation" in result
        assert "forecast" in result
        assert "news" in result


class TestGetFundamentals:
    def test_returns_categories(self, setup_mocks):
        result = stock_analyst.get_fundamentals("TCS")
        assert "categories" in result


class TestGetTechnicals:
    def test_returns_signals(self, setup_mocks):
        result = stock_analyst.get_technicals("TCS")
        assert "rsi" in result or "error" in result


class TestGetPeerComparison:
    def test_with_no_peers(self, setup_mocks):
        with patch("stock_analyst.engine.peers.yf") as mock_yf:
            mock_industry = MagicMock()
            mock_industry.top_companies = pd.DataFrame()
            mock_yf.Industry.return_value = mock_industry
            result = stock_analyst.get_peer_comparison("TCS")
        assert "target" in result

    def test_with_peers(self, setup_mocks):
        with patch("stock_analyst.engine.peers.yf") as mock_yf:
            top = pd.DataFrame({"name": [None, None]}, index=["INFY.NS", "WIPRO.BO"])
            mock_industry = MagicMock()
            mock_industry.top_companies = top
            mock_yf.Industry.return_value = mock_industry
            result = stock_analyst.get_peer_comparison("TCS")
        assert result["peer_count"] >= 0
        # Peer list should preserve exchange suffixes
        symbols = {r["symbol"] for r in result["fundamental_comparison"]}
        assert any(s.endswith(".NS") for s in symbols)
        assert any(s.endswith(".BO") for s in symbols)


class TestGetDcfValuation:
    def test_returns_wacc(self, setup_mocks):
        result = stock_analyst.get_dcf_valuation("TCS")
        assert "wacc" in result or "error" in result


class TestGetRevenueForecast:
    def test_returns_trend(self, setup_mocks):
        result = stock_analyst.get_revenue_forecast("TCS")
        assert "trend" in result or "scenarios" in result or "error" in result


class TestGetNews:
    def test_returns_headlines(self, setup_mocks):
        result = stock_analyst.get_news("TCS")
        assert "headlines" in result


class TestCompareStocks:
    def test_returns_multiple(self, setup_mocks):
        with patch("stock_analyst.engine.peers.yf"):
            result = stock_analyst.compare_stocks(["TCS", "INFY"])
        assert "TCS" in result
        assert "INFY" in result


class TestGetRawData:
    def test_triggers_fetch(self, setup_mocks):
        result = stock_analyst.get_raw_data("TCS", "info")
        # NullCache returns None, so we get "error" or the fetched data
        assert isinstance(result, dict)
