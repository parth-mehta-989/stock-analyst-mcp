"""Tests for stock_analyst.engine.peers."""

from unittest.mock import MagicMock, patch, PropertyMock

import pandas as pd
import pytest

from stock_analyst.cache.base import NullCache
from stock_analyst.config import Settings
from stock_analyst.engine.peers import PeerAnalyzer, _strip_exchange, _exchange


class TestStripExchange:
    def test_ns(self):
        assert _strip_exchange("TCS.NS") == "TCS"

    def test_bo(self):
        assert _strip_exchange("Wipro.BO") == "WIPRO"

    def test_plain(self):
        assert _strip_exchange("INFY") == "INFY"

    def test_whitespace(self):
        assert _strip_exchange("  tcs  ") == "TCS"


class TestExchange:
    def test_ns(self):
        assert _exchange("TCS.NS") == "NSE"

    def test_bo(self):
        assert _exchange("534064.BO") == "BSE"

    def test_plain(self):
        assert _exchange("INFY") == ""


@pytest.fixture
def peer_analyzer(config, null_cache):
    provider = MagicMock()
    return PeerAnalyzer(provider, null_cache, config)


class TestYfinanceIndustry:
    def test_success(self, peer_analyzer):
        peer_analyzer._provider.get_info.return_value = {
            "industryKey": "information-technology-services",
        }
        top_companies = pd.DataFrame(
            {"name": [None, None, None], "rating": ["Buy", "Hold", "Buy"]},
            index=["TCS.NS", "INFY.NS", "WIPRO.BO"],
        )
        with patch("stock_analyst.engine.peers.yf") as mock_yf:
            mock_industry = MagicMock()
            mock_industry.top_companies = top_companies
            mock_yf.Industry.return_value = mock_industry
            result = peer_analyzer._yfinance_industry("TCS")

        assert "TCS.NS" in result
        assert "INFY.NS" in result
        assert "WIPRO.BO" in result
        # Suffixes should be preserved for exchange-aware fetch
        assert all(s.endswith(".NS") or s.endswith(".BO") for s in result)

    def test_no_industry_key(self, peer_analyzer):
        peer_analyzer._provider.get_info.return_value = {}
        result = peer_analyzer._yfinance_industry("TCS")
        assert result == []

    def test_empty_top_companies(self, peer_analyzer):
        peer_analyzer._provider.get_info.return_value = {
            "industryKey": "some-industry",
        }
        with patch("stock_analyst.engine.peers.yf") as mock_yf:
            mock_industry = MagicMock()
            mock_industry.top_companies = pd.DataFrame()
            mock_yf.Industry.return_value = mock_industry
            result = peer_analyzer._yfinance_industry("TCS")

        assert result == []

    def test_exception_handled(self, peer_analyzer):
        peer_analyzer._provider.get_info.side_effect = Exception("network error")
        result = peer_analyzer._yfinance_industry("TCS")
        assert result == []


class TestScrapeScreener:
    def test_disabled(self, null_cache):
        config = Settings(cache_backend="none", screener_enabled=False)
        provider = MagicMock()
        pa = PeerAnalyzer(provider, null_cache, config)
        # screener won't be called if yfinance returns results
        # but _scrape_screener itself should work when called directly
        with patch("stock_analyst.engine.peers.requests") as mock_req:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.content = b'<html><section id="peers"><table class="data-table"><tr><th>Name</th></tr><tr><td><a href="/company/INFY/consolidated/">Infosys</a></td></tr></table></section></html>'
            mock_req.get.return_value = mock_resp
            result = pa._scrape_screener("TCS")
        assert "INFY" in result

    def test_404(self, peer_analyzer):
        with patch("stock_analyst.engine.peers.requests") as mock_req:
            mock_resp = MagicMock()
            mock_resp.status_code = 404
            mock_req.get.return_value = mock_resp
            result = peer_analyzer._scrape_screener("INVALID")
        assert result == []

    def test_no_peer_section(self, peer_analyzer):
        with patch("stock_analyst.engine.peers.requests") as mock_req:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.content = b"<html><body>No peers here</body></html>"
            mock_req.get.return_value = mock_resp
            result = peer_analyzer._scrape_screener("TCS")
        assert result == []

    def test_exception(self, peer_analyzer):
        with patch("stock_analyst.engine.peers.requests") as mock_req:
            mock_req.get.side_effect = Exception("timeout")
            result = peer_analyzer._scrape_screener("TCS")
        assert result == []


class TestDiscoverPeers:
    def test_returns_from_cache(self, null_cache, config):
        cache = MagicMock()
        cache.get.return_value = ["INFY.NS", "WIPRO.BO"]
        provider = MagicMock()
        pa = PeerAnalyzer(provider, cache, config)
        result = pa.discover_peers("TCS")
        assert result == ["INFY.NS", "WIPRO.BO"]

    def test_removes_target(self, peer_analyzer):
        peer_analyzer._yfinance_industry = MagicMock(return_value=["TCS.NS", "INFY.NS", "WIPRO.BO"])
        result = peer_analyzer.discover_peers("TCS")
        assert "TCS.NS" not in result
        assert "TCS.BO" not in result
        assert "INFY.NS" in result

    def test_falls_back_to_screener(self, config, null_cache):
        config = Settings(cache_backend="none", screener_enabled=True)
        provider = MagicMock()
        pa = PeerAnalyzer(provider, null_cache, config)
        pa._yfinance_industry = MagicMock(return_value=[])
        pa._scrape_screener = MagicMock(return_value=["INFY", "WIPRO"])
        result = pa.discover_peers("TCS")
        assert "INFY" in result

    def test_respects_max_count(self, config, null_cache):
        config = Settings(cache_backend="none", screener_enabled=False, peers_max_count=2)
        provider = MagicMock()
        pa = PeerAnalyzer(provider, null_cache, config)
        pa._yfinance_industry = MagicMock(return_value=["INFY.NS", "WIPRO.BO", "HCLTECH.NS", "TECHM.BO"])
        result = pa.discover_peers("TCS")
        assert len(result) <= 2


class TestFullSymbol:
    def test_appends_default_exchange(self, peer_analyzer):
        assert peer_analyzer._full_symbol("TCS") == "TCS.NS"

    def test_preserves_ns(self, peer_analyzer):
        assert peer_analyzer._full_symbol("TCS.NS") == "TCS.NS"

    def test_preserves_bo(self, peer_analyzer):
        assert peer_analyzer._full_symbol("534064.BO") == "534064.BO"


class TestGetPeerFundamentals:
    def test_fetches_all_with_exchange_suffix(self, peer_analyzer, sample_info):
        peer_analyzer._provider.get_info.return_value = sample_info
        result = peer_analyzer.get_peer_fundamentals("TCS", ["INFY.NS", "WIPRO.BO"])
        assert "TCS.NS" in result
        assert "INFY.NS" in result
        assert "WIPRO.BO" in result
        assert result["TCS.NS"]["pe"] == 30.0
        assert result["TCS.NS"]["exchange"] == "NSE"
        assert result["WIPRO.BO"]["exchange"] == "BSE"

    def test_appends_default_exchange_to_bare_symbols(self, peer_analyzer, sample_info):
        peer_analyzer._provider.get_info.return_value = sample_info
        result = peer_analyzer.get_peer_fundamentals("TCS", ["INFY", "WIPRO"])
        assert "TCS.NS" in result
        assert "INFY.NS" in result
        assert "WIPRO.NS" in result

    def test_handles_failure(self, peer_analyzer):
        peer_analyzer._provider.get_info.side_effect = Exception("fail")
        result = peer_analyzer.get_peer_fundamentals("TCS", ["INFY"])
        assert result == {}


class TestGetPeerTechnicals:
    def test_fetches_all_with_exchange_suffix(self, peer_analyzer, sample_ohlcv):
        # get_peer_technicals now uses get_history_batch for batch download
        peer_analyzer._provider.get_history_batch.return_value = {
            "TCS.NS": sample_ohlcv,
            "INFY.NS": sample_ohlcv,
            "WIPRO.BO": sample_ohlcv,
        }
        result = peer_analyzer.get_peer_technicals("TCS", ["INFY.NS", "WIPRO.BO"])
        assert "TCS.NS" in result
        assert "INFY.NS" in result
        assert "WIPRO.BO" in result
        assert result["TCS.NS"]["exchange"] == "NSE"
