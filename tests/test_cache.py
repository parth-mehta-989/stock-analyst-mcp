"""Tests for cache implementations."""

import json
import time

import pytest

from stock_analyst.cache.base import NullCache
from stock_analyst.cache.csv_cache import CsvCache


class TestNullCache:
    def test_get_returns_none(self):
        c = NullCache()
        assert c.get("any_key") is None

    def test_set_noop(self):
        c = NullCache()
        c.set("key", {"data": 1})
        assert c.get("key") is None

    def test_exists_false(self):
        c = NullCache()
        assert c.exists("key") is False


class TestCsvCache:
    def test_set_and_get(self, tmp_path):
        c = CsvCache(str(tmp_path), default_ttl=3600)
        c.set("test_key", {"hello": "world"})
        assert c.get("test_key") == {"hello": "world"}

    def test_exists(self, tmp_path):
        c = CsvCache(str(tmp_path), default_ttl=3600)
        assert c.exists("missing") is False
        c.set("present", [1, 2])
        assert c.exists("present") is True

    def test_expiry(self, tmp_path):
        c = CsvCache(str(tmp_path), default_ttl=1)
        c.set("expire_me", "data")
        assert c.get("expire_me") == "data"
        time.sleep(1.1)
        assert c.get("expire_me") is None

    def test_key_sanitization(self, tmp_path):
        c = CsvCache(str(tmp_path), default_ttl=3600)
        c.set("raw:TCS:info", {"pe": 30})
        assert c.get("raw:TCS:info") == {"pe": 30}

    def test_overwrite(self, tmp_path):
        c = CsvCache(str(tmp_path), default_ttl=3600)
        c.set("k", "v1")
        c.set("k", "v2")
        assert c.get("k") == "v2"
