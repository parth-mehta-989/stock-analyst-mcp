"""Abstract DataProvider and YFinanceProvider."""

from typing import Any, Dict, List, Optional, Protocol

import pandas as pd
import yfinance as yf

from stock_analyst.config import Settings
from stock_analyst.utils.batch import batch_download_history


class DataProvider(Protocol):
    def get_info(self, symbol: str) -> Dict[str, Any]: ...
    def get_financials(self, symbol: str) -> pd.DataFrame: ...
    def get_balance_sheet(self, symbol: str) -> pd.DataFrame: ...
    def get_cashflow(self, symbol: str) -> pd.DataFrame: ...
    def get_history(self, symbol: str, period: str, interval: str) -> pd.DataFrame: ...
    def get_history_batch(self, symbols: List[str], period: str, interval: str) -> Dict[str, pd.DataFrame]: ...
    def get_recommendations(self, symbol: str) -> Optional[pd.DataFrame]: ...
    def get_news(self, symbol: str) -> list: ...


class YFinanceProvider:
    def __init__(self, config: Settings) -> None:
        self._exchange = config.default_exchange

    def _ticker(self, symbol: str) -> yf.Ticker:
        sym = symbol.upper().strip()
        return yf.Ticker(sym)

    def get_info(self, symbol: str) -> Dict[str, Any]:
        return self._ticker(symbol).info

    def get_financials(self, symbol: str) -> pd.DataFrame:
        return self._ticker(symbol).income_stmt

    def get_balance_sheet(self, symbol: str) -> pd.DataFrame:
        return self._ticker(symbol).balance_sheet

    def get_cashflow(self, symbol: str) -> pd.DataFrame:
        return self._ticker(symbol).cashflow

    def get_history(self, symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        df = yf.download(
            self._ticker(symbol).ticker,
            period=period,
            interval=interval,
            progress=False,
        )
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
        return df

    def get_history_batch(self, symbols: List[str], period: str = "1y", interval: str = "1d") -> Dict[str, pd.DataFrame]:
        """Download OHLCV history for multiple symbols in one call (19x faster)."""
        cleaned = [s.upper().strip() for s in symbols]
        return batch_download_history(cleaned, period=period, interval=interval)

    def get_recommendations(self, symbol: str) -> Optional[pd.DataFrame]:
        try:
            return self._ticker(symbol).recommendations
        except Exception:
            return None

    def get_news(self, symbol: str) -> list:
        try:
            return self._ticker(symbol).news or []
        except Exception:
            return []


def get_provider(config: Settings) -> DataProvider:
    return YFinanceProvider(config)
