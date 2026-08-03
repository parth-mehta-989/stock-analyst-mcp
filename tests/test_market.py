"""Tests for stock_analyst.engine.market."""

from unittest.mock import MagicMock, patch

import pytest

from stock_analyst.engine.market import MarketAnalyzer, _mmi_label, _fetch_index


@pytest.fixture
def market_analyzer(config, null_cache):
    return MarketAnalyzer(null_cache, config)


class TestMmiLabel:
    def test_extreme_fear(self):
        assert _mmi_label(10) == "Extreme Fear"
        assert _mmi_label(29.9) == "Extreme Fear"

    def test_fear(self):
        assert _mmi_label(30) == "Fear"
        assert _mmi_label(49) == "Fear"

    def test_neutral(self):
        assert _mmi_label(50) == "Neutral"

    def test_greed(self):
        assert _mmi_label(51) == "Greed"
        assert _mmi_label(70) == "Greed"

    def test_extreme_greed(self):
        assert _mmi_label(71) == "Extreme Greed"
        assert _mmi_label(90) == "Extreme Greed"


class TestFetchIndex:
    @patch("stock_analyst.engine.market.yf.Ticker")
    def test_fetch_success(self, mock_ticker):
        mock_ticker.return_value.info = {
            "regularMarketPrice": 24000,
            "regularMarketPreviousClose": 23800,
            "previousClose": 23800,
        }
        result = _fetch_index("^NSEI")
        assert result["price"] == 24000
        assert result["change"] == 200
        assert result["change_pct"] == pytest.approx(0.84, abs=0.01)

    @patch("stock_analyst.engine.market.yf.Ticker")
    def test_fetch_exception(self, mock_ticker):
        mock_ticker.side_effect = Exception("network error")
        result = _fetch_index("^NSEI")
        assert result["price"] is None


class TestMarketAnalyzer:
    @patch("stock_analyst.engine.market._fetch_index")
    @patch("stock_analyst.engine.market.requests.get")
    def test_get_mood_full(self, mock_get, mock_fetch, market_analyzer):
        # Mock tickertape response
        html = "Market Mood Index Extreme Greed zone 73.22 Updated"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = html.encode()
        mock_get.return_value = mock_resp

        mock_fetch.return_value = {
            "price": 24000, "previous_close": 23800,
            "change": 200, "change_pct": 0.84,
        }

        result = market_analyzer.get_mood()
        assert result["mmi"]["value"] == 73.22
        assert result["mmi"]["label"] == "Extreme Greed"
        assert "assessment" in result

    @patch("stock_analyst.engine.market._fetch_index")
    @patch("stock_analyst.engine.market.requests.get")
    def test_mmi_scrape_fail_uses_vix(self, mock_get, mock_fetch, market_analyzer):
        mock_get.side_effect = Exception("timeout")
        mock_fetch.return_value = {
            "price": 25, "previous_close": 22,
            "change": 3, "change_pct": 13.6,
        }
        result = market_analyzer.get_mood()
        assert result["mmi"]["value"] is None
        assert "assessment" in result

    def test_cache_hit(self, config):
        cache = MagicMock()
        cache.get.return_value = {"cached": True}
        ma = MarketAnalyzer(cache, config)
        result = ma.get_mood()
        assert result["cached"] is True

    @patch("stock_analyst.engine.market._fetch_index")
    @patch("stock_analyst.engine.market.requests.get")
    def test_assessment_extreme_fear(self, mock_get, mock_fetch, market_analyzer):
        html = "MMI Fear zone 20.50 Updated"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = html.encode()
        mock_get.return_value = mock_resp
        mock_fetch.return_value = {"price": None, "previous_close": None, "change": None, "change_pct": None}

        result = market_analyzer.get_mood()
        assert "oversold" in result["assessment"].lower()

    @patch("stock_analyst.engine.market._fetch_index")
    @patch("stock_analyst.engine.market.requests.get")
    def test_mmi_http_error(self, mock_get, mock_fetch, market_analyzer):
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_get.return_value = mock_resp
        mock_fetch.return_value = {"price": 12, "previous_close": 11, "change": 1, "change_pct": 9.1}

        result = market_analyzer.get_mood()
        assert result["mmi"]["value"] is None
