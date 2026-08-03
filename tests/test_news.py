"""Tests for stock_analyst.engine.news."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from stock_analyst.engine.news import NewsAnalyzer, _sentiment, _fetch_snippet


@pytest.fixture
def news_analyzer(config, null_cache):
    provider = MagicMock()
    return NewsAnalyzer(provider, null_cache, config)


class TestSentiment:
    def test_positive(self):
        result = _sentiment("Stock surges to record high, amazing growth")
        assert result["label"] == "positive"
        assert result["score"] > 0

    def test_negative(self):
        result = _sentiment("Company reports massive losses, stock crashes")
        assert result["label"] == "negative"
        assert result["score"] < 0

    def test_neutral(self):
        result = _sentiment("Company announces quarterly results")
        assert result["label"] == "neutral"

    def test_empty(self):
        result = _sentiment("")
        assert result["label"] == "neutral"
        assert result["score"] == 0.0


class TestFetchSnippet:
    @patch("stock_analyst.engine.news.requests.get")
    def test_success(self, mock_get):
        html = "<html><body><p>Article body text here for testing.</p></body></html>"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = html.encode()
        mock_get.return_value = mock_resp
        snippet = _fetch_snippet("http://example.com/article", max_chars=50)
        assert len(snippet) <= 50
        assert "Article body" in snippet

    @patch("stock_analyst.engine.news.requests.get")
    def test_http_error(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_get.return_value = mock_resp
        assert _fetch_snippet("http://example.com/404") == ""

    @patch("stock_analyst.engine.news.requests.get")
    def test_exception(self, mock_get):
        mock_get.side_effect = Exception("timeout")
        assert _fetch_snippet("http://example.com") == ""

    def test_empty_url(self):
        assert _fetch_snippet("") == ""


class TestNewsAnalyzer:
    def test_basic_structure(self, news_analyzer):
        news_analyzer._provider.get_news.return_value = [
            {"title": "Stock rises", "publisher": "ET", "link": "http://example.com"},
        ]
        news_analyzer._provider.get_recommendations.return_value = None
        with patch("stock_analyst.engine.news._fetch_snippet", return_value=""):
            result = news_analyzer.analyze("TCS")
        assert result["symbol"] == "TCS"
        assert len(result["headlines"]) == 1
        assert result["headlines"][0]["title"] == "Stock rises"
        assert "sentiment_score" in result["headlines"][0]
        assert "sentiment_label" in result["headlines"][0]

    def test_max_headlines(self, news_analyzer):
        items = [{"title": f"News {i}", "publisher": "P", "link": "l"} for i in range(10)]
        news_analyzer._provider.get_news.return_value = items
        news_analyzer._provider.get_recommendations.return_value = None
        with patch("stock_analyst.engine.news._fetch_snippet", return_value=""):
            result = news_analyzer.analyze("TCS")
        assert len(result["headlines"]) == 5

    def test_sentiment_summary(self, news_analyzer):
        items = [
            {"title": "Amazing growth record high", "publisher": "P", "link": ""},
            {"title": "Stock crashes massive losses", "publisher": "P", "link": ""},
        ]
        news_analyzer._provider.get_news.return_value = items
        news_analyzer._provider.get_recommendations.return_value = None
        result = news_analyzer.analyze("TCS")
        assert "sentiment_summary" in result
        assert "average_score" in result["sentiment_summary"]
        assert "overall_label" in result["sentiment_summary"]
        assert result["sentiment_summary"]["headline_count"] == 2

    def test_snippet_fetched(self, news_analyzer):
        news_analyzer._provider.get_news.return_value = [
            {"title": "News", "publisher": "P", "link": "http://example.com"},
        ]
        news_analyzer._provider.get_recommendations.return_value = None
        with patch("stock_analyst.engine.news._fetch_snippet", return_value="snippet text") as mock_fetch:
            result = news_analyzer.analyze("TCS")
        assert result["headlines"][0]["snippet"] == "snippet text"
        mock_fetch.assert_called_once()

    def test_snippet_disabled(self, config, null_cache):
        config.news_fetch_snippets = False
        provider = MagicMock()
        provider.get_news.return_value = [
            {"title": "News", "publisher": "P", "link": "http://example.com"},
        ]
        provider.get_recommendations.return_value = None
        na = NewsAnalyzer(provider, null_cache, config)
        result = na.analyze("TCS")
        assert result["headlines"][0]["snippet"] == ""

    def test_recommendations(self, news_analyzer):
        news_analyzer._provider.get_news.return_value = []
        recs = pd.DataFrame({
            "strongBuy": [5, 6],
            "buy": [10, 12],
            "hold": [8, 7],
        })
        news_analyzer._provider.get_recommendations.return_value = recs
        result = news_analyzer.analyze("TCS")
        assert int(result["recommendations"]["strongBuy"]) == 6

    def test_empty_recommendations(self, news_analyzer):
        news_analyzer._provider.get_news.return_value = []
        news_analyzer._provider.get_recommendations.return_value = pd.DataFrame()
        result = news_analyzer.analyze("TCS")
        assert result["recommendations"] == {}

    def test_cache_hit(self, config):
        cache = MagicMock()
        cache.get.return_value = {"cached": True}
        provider = MagicMock()
        na = NewsAnalyzer(provider, cache, config)
        result = na.analyze("TCS")
        assert result["cached"] is True
