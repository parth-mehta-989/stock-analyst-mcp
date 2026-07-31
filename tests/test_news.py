"""Tests for stock_analyst.engine.news."""

from unittest.mock import MagicMock

import pandas as pd
import pytest

from stock_analyst.engine.news import NewsAnalyzer


@pytest.fixture
def news_analyzer(config, null_cache):
    provider = MagicMock()
    return NewsAnalyzer(provider, null_cache, config)


class TestNewsAnalyzer:
    def test_basic_structure(self, news_analyzer):
        news_analyzer._provider.get_news.return_value = [
            {"title": "Stock rises", "publisher": "ET", "link": "http://example.com"},
        ]
        news_analyzer._provider.get_recommendations.return_value = None
        result = news_analyzer.analyze("TCS")
        assert result["symbol"] == "TCS"
        assert len(result["headlines"]) == 1
        assert result["headlines"][0]["title"] == "Stock rises"

    def test_max_headlines(self, news_analyzer):
        items = [{"title": f"News {i}", "publisher": "P", "link": "l"} for i in range(10)]
        news_analyzer._provider.get_news.return_value = items
        news_analyzer._provider.get_recommendations.return_value = None
        result = news_analyzer.analyze("TCS")
        assert len(result["headlines"]) == 5

    def test_recommendations(self, news_analyzer):
        news_analyzer._provider.get_news.return_value = []
        recs = pd.DataFrame({
            "strongBuy": [5, 6],
            "buy": [10, 12],
            "hold": [8, 7],
        })
        news_analyzer._provider.get_recommendations.return_value = recs
        result = news_analyzer.analyze("TCS")
        # pandas int64 may serialize as str via the str() path
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
