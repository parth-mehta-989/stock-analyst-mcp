"""Tests for stock_analyst.engine.fundamentals."""

from unittest.mock import MagicMock

import pytest

from stock_analyst.engine.fundamentals import FundamentalAnalyzer


@pytest.fixture
def fa(config, null_cache, sample_info, sample_financials, sample_balance_sheet, sample_cashflow):
    provider = MagicMock()
    provider.get_info.return_value = sample_info
    provider.get_financials.return_value = sample_financials
    provider.get_balance_sheet.return_value = sample_balance_sheet
    provider.get_cashflow.return_value = sample_cashflow
    return FundamentalAnalyzer(provider, null_cache, config)


class TestFundamentalAnalyzer:
    def test_fetch_all_structure(self, fa):
        result = fa.fetch_all("TCS")
        assert "ratio_input" in result
        assert "dcf_input" in result
        assert "forecast_input" in result
        assert "info_summary" in result

    def test_info_summary(self, fa):
        result = fa.fetch_all("TCS")
        summary = result["info_summary"]
        assert summary["name"] == "Test Corp Ltd"
        assert summary["sector"] == "Technology"
        assert summary["current_price"] == 3500.0

    def test_cache_hit(self, config, sample_info, sample_financials, sample_balance_sheet, sample_cashflow):
        cache = MagicMock()
        cache.get.return_value = {"cached": True}
        provider = MagicMock()
        fa = FundamentalAnalyzer(provider, cache, config)
        result = fa.fetch_all("TCS")
        assert result == {"cached": True}
        provider.get_info.assert_not_called()

    def test_caches_raw_data(self, fa):
        # null_cache won't store but should not crash
        result = fa.fetch_all("TCS")
        assert result is not None
