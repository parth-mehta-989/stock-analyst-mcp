"""Tests for stock_analyst.config."""

import os

import pytest

from stock_analyst.config import Settings, _csv_to_list, _csv_to_int_list


class TestHelpers:
    def test_csv_to_list_string(self):
        assert _csv_to_list("a,b,c") == ["a", "b", "c"]

    def test_csv_to_list_passthrough(self):
        assert _csv_to_list(["a"]) == ["a"]

    def test_csv_to_list_strips(self):
        assert _csv_to_list(" a , b ") == ["a", "b"]

    def test_csv_to_list_empty(self):
        assert _csv_to_list("") == []

    def test_csv_to_int_list(self):
        assert _csv_to_int_list("12,26,9") == [12, 26, 9]

    def test_csv_to_int_list_passthrough(self):
        assert _csv_to_int_list([1, 2]) == [1, 2]


class TestSettings:
    def test_defaults(self, config):
        assert config.default_exchange == ".NS"
        assert config.cache_backend == "none"
        assert config.fa_dcf_enabled is True

    def test_ema_periods_property(self, config):
        assert config.ema_periods == [20, 50, 200]

    def test_macd_params_property(self, config):
        assert config.macd_params == [12, 26, 9]

    def test_forecast_scenarios_property(self, config):
        assert "base" in config.forecast_scenarios
        assert "bull" in config.forecast_scenarios
        assert "bear" in config.forecast_scenarios

    def test_peer_metrics_properties(self, config):
        assert "pe" in config.peer_fundamental_metrics_list
        assert "rsi" in config.peer_technical_metrics_list

    def test_env_override(self, monkeypatch):
        monkeypatch.setenv("SA_DEFAULT_EXCHANGE", ".BO")
        monkeypatch.setenv("SA_CACHE_BACKEND", "none")
        s = Settings()
        assert s.default_exchange == ".BO"
