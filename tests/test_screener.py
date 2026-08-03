"""Tests for stock_analyst.engine.screener."""

from unittest.mock import MagicMock, patch

import pytest

from stock_analyst.engine.screener import (
    StockScreener,
    _build_equity_query,
    _FILTER_MAP,
    _SORT_MAP,
)


@pytest.fixture
def screener(config, null_cache):
    return StockScreener(null_cache, config)


class TestBuildEquityQuery:
    def test_region_always_included(self):
        q = _build_equity_query({})
        # Should produce a single region=in query
        assert q is not None

    def test_sector_filter(self):
        q = _build_equity_query({"sector": "Technology"})
        assert q is not None

    def test_numeric_min_max(self):
        q = _build_equity_query({"pe_min": 5, "pe_max": 30})
        assert q is not None

    def test_combined_filters(self):
        q = _build_equity_query({
            "sector": "Technology",
            "market_cap_min": 1e10,
            "roe_min": 0.15,
            "pe_max": 40,
        })
        assert q is not None

    def test_unknown_filter_ignored(self):
        q = _build_equity_query({"unknown_key": 999})
        assert q is not None


class TestStockScreener:
    @patch("stock_analyst.engine.screener.yf.screen")
    def test_yfinance_screen_success(self, mock_screen, screener):
        mock_screen.return_value = {
            "quotes": [
                {
                    "symbol": "TCS.NS",
                    "longName": "Tata Consultancy Services",
                    "exchange": "NSI",
                    "sector": "Technology",
                    "industry": "IT Services",
                    "marketCap": 12000000000000,
                    "regularMarketPrice": 3500,
                    "trailingPE": 30,
                    "priceToBook": 12,
                    "dividendYield": 0.012,
                    "fiftyTwoWeekChangePercent": 15.5,
                },
            ],
        }
        result = screener.screen({"sector": "Technology"})
        assert result["source"] == "yfinance"
        assert result["count"] == 1
        assert result["stocks"][0]["symbol"] == "TCS.NS"
        assert result["stocks"][0]["market_cap"] == 12000000000000

    @patch("stock_analyst.engine.screener.yf.screen")
    def test_yfinance_screen_empty(self, mock_screen, screener):
        mock_screen.return_value = {"quotes": []}
        result = screener._yfinance_screen({}, "market_cap", False, 50)
        assert result["count"] == 0

    @patch("stock_analyst.engine.screener.yf.screen")
    def test_yfinance_screen_exception(self, mock_screen, screener):
        mock_screen.side_effect = Exception("API error")
        result = screener._yfinance_screen({}, "market_cap", False, 50)
        assert result["count"] == 0

    @patch("stock_analyst.engine.screener.requests.get")
    def test_screener_in_fallback(self, mock_get, screener):
        html = """
        <table class="data-table">
            <tr><th>S.No.</th><th>Name</th></tr>
            <tr><td>1</td><td><a href="/company/TCS/">TCS Ltd</a></td></tr>
        </table>
        """
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = html.encode()
        mock_get.return_value = mock_resp
        result = screener._screener_in_screen({"market_cap_min": 500}, 50)
        assert result["source"] == "screener.in"
        assert result["count"] >= 1

    @patch("stock_analyst.engine.screener.requests.get")
    def test_screener_in_error(self, mock_get, screener):
        mock_get.side_effect = Exception("timeout")
        result = screener._screener_in_screen({}, 50)
        assert result["count"] == 0

    def test_limit_respected(self, screener):
        with patch("stock_analyst.engine.screener.yf.screen") as mock_screen:
            mock_screen.return_value = {
                "quotes": [{"symbol": f"S{i}.NS"} for i in range(100)],
            }
            result = screener.screen({}, limit=5)
            assert len(result["stocks"]) == 5

    def test_cache_key_not_used(self, screener):
        """Screener does not use cache by default."""
        with patch("stock_analyst.engine.screener.yf.screen") as mock_screen:
            mock_screen.return_value = {"quotes": []}
            screener.screen({})
            mock_screen.assert_called_once()

    def test_available_filters(self):
        info = StockScreener.available_filters()
        assert "filters" in info
        assert "sort_options" in info
        assert "market_cap_min" in info["filters"]
        assert "market_cap" in info["sort_options"]


class TestFilterAndSortMaps:
    def test_filter_map_has_expected_keys(self):
        expected = ["market_cap_min", "pe_max", "roe_min", "beta_min"]
        for key in expected:
            assert key in _FILTER_MAP

    def test_sort_map_has_expected_keys(self):
        expected = ["market_cap", "pe", "roe", "price"]
        for key in expected:
            assert key in _SORT_MAP
