"""News headlines + analyst recommendations + sentiment analysis."""

import logging
from typing import Any, Dict, List

import requests
from bs4 import BeautifulSoup
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from stock_analyst.cache.base import Cache
from stock_analyst.config import Settings
from stock_analyst.engine.data_provider import DataProvider
from stock_analyst.utils.concurrency import parallel_map

logger = logging.getLogger(__name__)

_vader = SentimentIntensityAnalyzer()


def _sentiment(text: str) -> Dict[str, Any]:
    """Compute VADER sentiment on text. Returns score + label."""
    if not text:
        return {"score": 0.0, "label": "neutral"}
    scores = _vader.polarity_scores(text)
    compound = scores["compound"]
    if compound >= 0.05:
        label = "positive"
    elif compound <= -0.05:
        label = "negative"
    else:
        label = "neutral"
    return {"score": round(compound, 4), "label": label}


def _fetch_snippet(url: str, max_chars: int = 500, timeout: int = 10) -> str:
    """Fetch article URL and extract first N chars of body text."""
    if not url:
        return ""
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=timeout,
            allow_redirects=True,
        )
        if resp.status_code != 200:
            return ""
        soup = BeautifulSoup(resp.content, "html.parser")
        # Remove scripts/styles
        for tag in soup(["script", "style", "nav", "header", "footer"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        return text[:max_chars] if text else ""
    except Exception as e:
        logger.debug("Snippet fetch failed for %s: %s", url, e)
        return ""


class NewsAnalyzer:
    def __init__(self, provider: DataProvider, cache: Cache, config: Settings) -> None:
        self._provider = provider
        self._cache = cache
        self._config = config

    def analyze(self, symbol: str) -> Dict[str, Any]:
        cache_key = f"news:{symbol}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        max_headlines = self._config.news_max_headlines
        fetch_snippets = self._config.news_fetch_snippets
        snippet_max = self._config.news_snippet_max_chars

        result: Dict[str, Any] = {
            "symbol": symbol,
            "headlines": [],
            "recommendations": {},
            "sentiment_summary": {},
        }

        # Headlines with sentiment
        news_items = self._provider.get_news(symbol)
        sentiment_scores: List[float] = []

        valid_items = [i for i in news_items[:max_headlines] if isinstance(i, dict)]

        # Build headlines with sentiment (CPU-bound, fast)
        headlines: List[Dict[str, Any]] = []
        for item in valid_items:
            title = item.get("title", "")
            sent = _sentiment(title)
            sentiment_scores.append(sent["score"])
            headlines.append({
                "title": title,
                "publisher": item.get("publisher", ""),
                "link": item.get("link", ""),
                "sentiment_score": sent["score"],
                "sentiment_label": sent["label"],
                "snippet": "",
            })

        # Fetch snippets in parallel (I/O-bound)
        if fetch_snippets:
            links = [h["link"] for h in headlines]
            snippets = parallel_map(
                lambda url: _fetch_snippet(url, max_chars=snippet_max),
                [lnk for lnk in links if lnk],
                label="snippets",
            )
            # Map snippets back by index
            snippet_iter = iter(snippets)
            for h in headlines:
                if h["link"]:
                    h["snippet"] = next(snippet_iter, "")

        result["headlines"] = headlines

        # Aggregate sentiment summary
        if sentiment_scores:
            avg = round(sum(sentiment_scores) / len(sentiment_scores), 4)
            if avg >= 0.05:
                overall = "positive"
            elif avg <= -0.05:
                overall = "negative"
            else:
                overall = "neutral"
            result["sentiment_summary"] = {
                "average_score": avg,
                "overall_label": overall,
                "headline_count": len(sentiment_scores),
            }

        # Analyst recommendations summary
        recs = self._provider.get_recommendations(symbol)
        if recs is not None and not recs.empty:
            try:
                latest = recs.iloc[-1] if len(recs) > 0 else None
                if latest is not None:
                    rec_dict = {}
                    for col in recs.columns:
                        val = latest.get(col)
                        if val is not None:
                            rec_dict[col] = int(val) if isinstance(val, (int, float)) else str(val)
                    result["recommendations"] = rec_dict
            except Exception as e:
                logger.debug("Recommendations parse failed: %s", e)

        self._cache.set(cache_key, result)
        return result
