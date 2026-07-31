"""Shared fixtures for stock_analyst tests."""

import pandas as pd
import pytest

from stock_analyst.cache.base import NullCache
from stock_analyst.config import Settings


@pytest.fixture
def config():
    """Settings with sane test defaults."""
    return Settings(
        cache_backend="none",
        screener_enabled=False,
        log_level="DEBUG",
        default_exchange=".NS",
    )


@pytest.fixture
def null_cache():
    return NullCache()


@pytest.fixture
def sample_info():
    """Typical yfinance Ticker.info dict."""
    return {
        "longName": "Test Corp Ltd",
        "sector": "Technology",
        "industry": "Information Technology Services",
        "industryKey": "information-technology-services",
        "currentPrice": 3500.0,
        "marketCap": 12_000_000_000_000,
        "currency": "INR",
        "sharesOutstanding": 3_600_000_000,
        "trailingPE": 30.0,
        "priceToBook": 12.0,
        "returnOnEquity": 0.45,
        "debtToEquity": 5.0,
        "dividendYield": 0.012,
        "profitMargins": 0.25,
        "revenueGrowth": 0.08,
        "operatingMargins": 0.28,
        "returnOnAssets": 0.20,
        "earningsGrowth": 0.10,
        "beta": 0.7,
    }


@pytest.fixture
def sample_financials():
    """Minimal income_stmt DataFrame."""
    data = {
        pd.Timestamp("2024-03-31"): [250_000_000_000, 180_000_000_000, 50_000_000_000, 40_000_000_000, 1_000_000_000, 55_000_000_000],
        pd.Timestamp("2023-03-31"): [230_000_000_000, 165_000_000_000, 45_000_000_000, 36_000_000_000, 900_000_000, 50_000_000_000],
    }
    return pd.DataFrame(
        data,
        index=["Total Revenue", "Cost Of Revenue", "Operating Income", "Net Income", "Interest Expense", "EBITDA"],
    )


@pytest.fixture
def sample_balance_sheet():
    data = {
        pd.Timestamp("2024-03-31"): [100_000_000_000, 200_000_000_000, 80_000_000_000, 60_000_000_000, 5_000_000_000, 30_000_000_000, 10_000_000_000, 25_000_000_000],
    }
    return pd.DataFrame(
        data,
        index=["Stockholders Equity", "Total Assets", "Current Assets", "Current Liabilities", "Inventory", "Cash And Cash Equivalents", "Total Debt", "Net Receivables"],
    )


@pytest.fixture
def sample_cashflow():
    data = {
        pd.Timestamp("2024-03-31"): [60_000_000_000],
    }
    return pd.DataFrame(data, index=["Operating Cash Flow"])


@pytest.fixture
def sample_ohlcv():
    """120 days of synthetic OHLCV data."""
    import numpy as np
    dates = pd.bdate_range("2024-01-01", periods=120)
    np.random.seed(42)
    base = 3500 + np.cumsum(np.random.randn(120) * 10)
    df = pd.DataFrame({
        "Open": base - 5,
        "High": base + 15,
        "Low": base - 15,
        "Close": base,
        "Volume": np.random.randint(1_000_000, 10_000_000, 120),
    }, index=dates)
    return df
