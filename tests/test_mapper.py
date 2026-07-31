"""Tests for stock_analyst.engine.mapper."""

import math

import pandas as pd
import pytest

from stock_analyst.engine.mapper import (
    _safe_float,
    _get_latest,
    _get_series,
    map_to_ratio_input,
    map_to_dcf_input,
    map_to_forecast_input,
)


class TestSafeFloat:
    def test_normal(self):
        assert _safe_float(3.14) == 3.14

    def test_none(self):
        assert _safe_float(None) == 0.0

    def test_nan(self):
        assert _safe_float(float("nan")) == 0.0

    def test_inf(self):
        assert _safe_float(float("inf")) == 0.0

    def test_string_number(self):
        assert _safe_float("42") == 42.0

    def test_bad_string(self):
        assert _safe_float("abc") == 0.0


class TestGetLatest:
    def test_normal(self, sample_financials):
        val = _get_latest(sample_financials, "Total Revenue")
        assert val == 250_000_000_000

    def test_missing_row(self, sample_financials):
        assert _get_latest(sample_financials, "Nonexistent") == 0.0

    def test_empty_df(self):
        assert _get_latest(pd.DataFrame(), "anything") == 0.0

    def test_none_df(self):
        assert _get_latest(None, "anything") == 0.0


class TestGetSeries:
    def test_normal(self, sample_financials):
        series = _get_series(sample_financials, "Total Revenue")
        # reversed: oldest first
        assert series == [230_000_000_000, 250_000_000_000]

    def test_missing_row(self, sample_financials):
        assert _get_series(sample_financials, "Nonexistent") == []


class TestMapToRatioInput:
    def test_structure(self, sample_info, sample_financials, sample_balance_sheet, sample_cashflow):
        result = map_to_ratio_input(sample_info, sample_financials, sample_balance_sheet, sample_cashflow)
        assert "income_statement" in result
        assert "balance_sheet" in result
        assert "cash_flow" in result
        assert "market_data" in result
        assert result["income_statement"]["revenue"] == 250_000_000_000
        assert result["market_data"]["market_cap"] == 12_000_000_000_000

    def test_zero_on_missing(self):
        result = map_to_ratio_input({}, pd.DataFrame(), pd.DataFrame(), pd.DataFrame())
        assert result["income_statement"]["revenue"] == 0.0


class TestMapToDcfInput:
    def test_structure(self, sample_info, sample_financials, sample_balance_sheet, config):
        result = map_to_dcf_input(sample_info, sample_financials, sample_balance_sheet, config)
        assert "historical" in result
        assert "assumptions" in result
        assert len(result["historical"]["revenue"]) == 2
        assert result["assumptions"]["projection_years"] == 5


class TestMapToForecastInput:
    def test_structure(self, sample_financials, config):
        result = map_to_forecast_input(sample_financials, config)
        assert "forecast_periods" in result
        assert "historical_periods" in result
        assert "assumptions" in result
        assert "scenarios" in result
        assert result["assumptions"]["revenue_growth_rate"] > 0
