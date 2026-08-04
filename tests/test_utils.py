"""Tests for stock_analyst.utils — concurrency and batch helpers."""

import time
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from stock_analyst.utils.concurrency import parallel_map, parallel_map_dict
from stock_analyst.utils.batch import batch_download_history


class TestParallelMap:
    def test_preserves_order(self):
        result = parallel_map(lambda x: x * 2, [1, 2, 3, 4, 5])
        assert result == [2, 4, 6, 8, 10]

    def test_empty_input(self):
        assert parallel_map(lambda x: x, []) == []

    def test_single_item(self):
        assert parallel_map(lambda x: x + 1, [10]) == [11]

    def test_skips_failures(self):
        def maybe_fail(x):
            if x == 3:
                raise ValueError("boom")
            return x

        result = parallel_map(maybe_fail, [1, 2, 3, 4, 5])
        assert result == [1, 2, 4, 5]

    def test_runs_concurrently(self):
        """Verify parallel execution is faster than sequential."""
        def slow(x):
            time.sleep(0.1)
            return x

        start = time.time()
        result = parallel_map(slow, [1, 2, 3, 4, 5], max_workers=5)
        elapsed = time.time() - start
        assert len(result) == 5
        # 5 items at 0.1s each sequentially = 0.5s; parallel should be < 0.3s
        assert elapsed < 0.4

    def test_max_workers_capped(self):
        """Workers capped to len(items) if smaller than max_workers."""
        result = parallel_map(lambda x: x, [1, 2], max_workers=100)
        assert result == [1, 2]


class TestParallelMapDict:
    def test_returns_dict(self):
        result = parallel_map_dict(lambda x: x * 10, ["a", "b", "c"])
        assert result == {"a": "aaaaaaaaaa", "b": "bbbbbbbbbb", "c": "cccccccccc"}

    def test_empty_input(self):
        assert parallel_map_dict(lambda x: x, []) == {}

    def test_skips_failures(self):
        def maybe_fail(x):
            if x == "b":
                raise ValueError("boom")
            return x.upper()

        result = parallel_map_dict(maybe_fail, ["a", "b", "c"])
        assert result == {"a": "A", "c": "C"}

    def test_numeric_keys(self):
        result = parallel_map_dict(lambda x: x ** 2, [1, 2, 3])
        assert result == {1: 1, 2: 4, 3: 9}


class TestBatchDownloadHistory:
    def test_empty_symbols(self):
        assert batch_download_history([]) == {}

    @patch("stock_analyst.utils.batch.yf.download")
    def test_single_symbol(self, mock_download):
        df = pd.DataFrame({"Close": [100, 101, 102]})
        mock_download.return_value = df
        result = batch_download_history(["AAPL"])
        assert "AAPL" in result
        mock_download.assert_called_once()

    @patch("stock_analyst.utils.batch.yf.download")
    def test_multi_symbol(self, mock_download):
        # Simulate multi-index return from yf.download with group_by='ticker'
        idx = pd.date_range("2024-01-01", periods=3)
        arrays = [["AAPL", "AAPL", "MSFT", "MSFT"], ["Close", "Volume", "Close", "Volume"]]
        tuples = list(zip(*arrays))
        mi = pd.MultiIndex.from_tuples(tuples)
        df = pd.DataFrame([[100, 1000, 200, 2000], [101, 1100, 201, 2100], [102, 1200, 202, 2200]],
                          index=idx, columns=mi)
        mock_download.return_value = df

        result = batch_download_history(["AAPL", "MSFT"])
        assert "AAPL" in result
        assert "MSFT" in result
        # Should have called download with threads=True
        call_kwargs = mock_download.call_args[1]
        assert call_kwargs["threads"] is True
        assert call_kwargs["group_by"] == "ticker"
