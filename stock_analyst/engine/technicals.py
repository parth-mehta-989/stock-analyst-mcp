"""Technical analysis: EMA, RSI, MACD, Bollinger via pandas-ta + signal generation."""

import logging
from typing import Any, Dict

import pandas as pd
import pandas_ta as ta

from stock_analyst.cache.base import Cache
from stock_analyst.config import Settings
from stock_analyst.engine.data_provider import DataProvider

logger = logging.getLogger(__name__)


class TechnicalAnalyzer:
    def __init__(self, provider: DataProvider, cache: Cache, config: Settings) -> None:
        self._provider = provider
        self._cache = cache
        self._config = config

    def analyze(self, symbol: str, period: str = "", interval: str = "") -> Dict[str, Any]:
        period = period or self._config.default_period
        interval = interval or self._config.default_interval

        cache_key = f"technicals:{symbol}:{period}:{interval}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        df = self._provider.get_history(symbol, period, interval)
        if df.empty:
            return {"error": f"No historical data for {symbol}"}

        # Cache raw OHLCV
        try:
            self._cache.set(f"raw:{symbol}:ohlcv", df.tail(30).to_dict())
        except Exception:
            pass

        # Compute indicators
        ema_periods = self._config.ema_periods
        for p in ema_periods:
            df[f"EMA_{p}"] = ta.ema(df["Close"], length=p)

        df["RSI"] = ta.rsi(df["Close"], length=self._config.ta_rsi_period)

        macd_p = self._config.macd_params
        macd_df = ta.macd(df["Close"], fast=macd_p[0], slow=macd_p[1], signal=macd_p[2])
        if macd_df is not None:
            df = pd.concat([df, macd_df], axis=1)

        if self._config.ta_bollinger_enabled:
            bb = ta.bbands(df["Close"], length=self._config.ta_bollinger_period)
            if bb is not None:
                df = pd.concat([df, bb], axis=1)

        result = self._build_summary(df, symbol)
        self._cache.set(cache_key, result)
        return result

    def _build_summary(self, df: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        latest = df.iloc[-1]
        price = float(latest["Close"])

        summary: Dict[str, Any] = {
            "symbol": symbol,
            "current_price": round(price, 2),
        }

        # EMA values and trend
        for p in self._config.ema_periods:
            col = f"EMA_{p}"
            if col in df.columns:
                summary[f"ema_{p}"] = round(float(latest[col]), 2) if pd.notna(latest[col]) else None

        ema_short = summary.get(f"ema_{self._config.ema_periods[0]}")
        ema_long = summary.get(f"ema_{self._config.ema_periods[-1]}")
        if ema_short and ema_long:
            if price > ema_short > ema_long:
                summary["ema_trend"] = "bullish"
            elif price < ema_short < ema_long:
                summary["ema_trend"] = "bearish"
            else:
                summary["ema_trend"] = "neutral"
        else:
            summary["ema_trend"] = "insufficient_data"

        # RSI
        rsi_val = float(latest["RSI"]) if pd.notna(latest.get("RSI")) else None
        summary["rsi"] = round(rsi_val, 2) if rsi_val else None
        if rsi_val:
            if rsi_val > 70:
                summary["rsi_signal"] = "overbought"
            elif rsi_val < 30:
                summary["rsi_signal"] = "oversold"
            else:
                summary["rsi_signal"] = "neutral"
        else:
            summary["rsi_signal"] = "insufficient_data"

        # MACD
        macd_p = self._config.macd_params
        macd_col = f"MACD_{macd_p[0]}_{macd_p[1]}_{macd_p[2]}"
        signal_col = f"MACDs_{macd_p[0]}_{macd_p[1]}_{macd_p[2]}"
        if macd_col in df.columns and signal_col in df.columns:
            macd_val = float(latest[macd_col]) if pd.notna(latest[macd_col]) else None
            signal_val = float(latest[signal_col]) if pd.notna(latest[signal_col]) else None
            if macd_val is not None and signal_val is not None:
                prev = df.iloc[-2]
                prev_macd = float(prev[macd_col]) if pd.notna(prev[macd_col]) else None
                prev_signal = float(prev[signal_col]) if pd.notna(prev[signal_col]) else None
                if prev_macd is not None and prev_signal is not None:
                    if prev_macd <= prev_signal and macd_val > signal_val:
                        summary["macd_signal"] = "bullish_crossover"
                    elif prev_macd >= prev_signal and macd_val < signal_val:
                        summary["macd_signal"] = "bearish_crossover"
                    elif macd_val > signal_val:
                        summary["macd_signal"] = "bullish"
                    else:
                        summary["macd_signal"] = "bearish"
                else:
                    summary["macd_signal"] = "neutral"
            else:
                summary["macd_signal"] = "insufficient_data"
        else:
            summary["macd_signal"] = "insufficient_data"

        # Bollinger position
        if self._config.ta_bollinger_enabled:
            bp = self._config.ta_bollinger_period
            # pandas-ta names: BBU_20_2.0_2.0, BBL_20_2.0_2.0
            bb_upper = next((c for c in df.columns if c.startswith(f"BBU_{bp}")), None)
            bb_lower = next((c for c in df.columns if c.startswith(f"BBL_{bp}")), None)
            if bb_upper and bb_lower:
                upper = float(latest[bb_upper]) if pd.notna(latest[bb_upper]) else None
                lower = float(latest[bb_lower]) if pd.notna(latest[bb_lower]) else None
                if upper and lower:
                    if price >= upper:
                        summary["bollinger_position"] = "upper"
                    elif price <= lower:
                        summary["bollinger_position"] = "lower"
                    else:
                        summary["bollinger_position"] = "middle"
                else:
                    summary["bollinger_position"] = "insufficient_data"
            else:
                summary["bollinger_position"] = "insufficient_data"

        # 52-week high %
        high_52w = df["High"].rolling(window=min(252, len(df))).max().iloc[-1]
        if pd.notna(high_52w) and high_52w > 0:
            summary["price_vs_52w_high_pct"] = round((price - float(high_52w)) / float(high_52w) * 100, 2)

        # Overall signal
        signals = []
        if summary.get("ema_trend") == "bullish":
            signals.append(1)
        elif summary.get("ema_trend") == "bearish":
            signals.append(-1)
        if summary.get("rsi_signal") == "oversold":
            signals.append(1)
        elif summary.get("rsi_signal") == "overbought":
            signals.append(-1)
        if "bullish" in str(summary.get("macd_signal", "")):
            signals.append(1)
        elif "bearish" in str(summary.get("macd_signal", "")):
            signals.append(-1)

        if signals:
            avg = sum(signals) / len(signals)
            if avg > 0.5:
                summary["overall_signal"] = "bullish"
            elif avg > 0:
                summary["overall_signal"] = "moderately_bullish"
            elif avg < -0.5:
                summary["overall_signal"] = "bearish"
            elif avg < 0:
                summary["overall_signal"] = "moderately_bearish"
            else:
                summary["overall_signal"] = "neutral"
        else:
            summary["overall_signal"] = "insufficient_data"

        return summary
