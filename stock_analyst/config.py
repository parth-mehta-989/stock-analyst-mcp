"""Configuration loaded from configurations.env via pydantic-settings."""

import os
from pathlib import Path
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings


def _expand_path(v: str) -> str:
    return str(Path(v).expanduser())


def _csv_to_list(v: str) -> List[str]:
    if isinstance(v, list):
        return v
    return [x.strip() for x in v.split(",") if x.strip()]


def _csv_to_int_list(v: str) -> List[int]:
    if isinstance(v, list):
        return v
    return [int(x.strip()) for x in v.split(",") if x.strip()]


class Settings(BaseSettings):
    # MCP Server
    mcp_transport: str = "streamable-http"
    mcp_port: int = 3001

    # Data Provider
    data_provider: str = "yfinance"
    default_exchange: str = ".NS"
    default_region: str = "in"
    default_period: str = "1y"
    default_interval: str = "1d"
    
    # Supported regions (yfinance EquityQuery.valid_values["region"])
    supported_regions: str = "ae,ar,at,au,be,br,ca,ch,cl,cn,co,cz,de,dk,ee,eg,es,fi,fr,gb,gr,hk,hu,id,ie,il,in,is,it,jp,kr,kw,lk,lt,lv,mx,my,nl,no,nz,pe,ph,pk,pl,pt,qa,ro,ru,sa,se,sg,sr,th,tr,tw,us,ve,vn,za"

    # Cache
    cache_backend: str = "redis"
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl: int = 3600
    csv_cache_dir: str = "~/.stock_analyst/cache"

    # Screener.in
    screener_enabled: bool = True
    screener_base_url: str = "https://www.screener.in/company"
    screener_delay: float = 2.0
    screener_timeout: int = 15

    # Output
    output_format: str = "json"
    output_include_raw: bool = False
    output_pretty: bool = True

    # Technical Analysis
    ta_ema_periods: str = "20,50,200"
    ta_rsi_period: int = 14
    ta_macd_params: str = "12,26,9"
    ta_bollinger_enabled: bool = True
    ta_bollinger_period: int = 20

    # Financial Analysis
    fa_dcf_enabled: bool = True
    fa_dcf_projection_years: int = 5
    fa_dcf_terminal_growth: float = 0.025
    fa_dcf_exit_multiple: float = 12.0
    fa_wacc_risk_free_rate: float = 0.07
    fa_wacc_equity_risk_premium: float = 0.06
    fa_wacc_cost_of_debt: float = 0.09
    fa_wacc_tax_rate: float = 0.25
    fa_wacc_debt_weight: float = 0.30
    fa_wacc_equity_weight: float = 0.70
    fa_variance_threshold_pct: float = 10.0
    fa_variance_threshold_amt: float = 5000000
    fa_forecast_scenarios: str = "base,bull,bear"

    # News & Sentiment
    news_fetch_snippets: bool = True
    news_max_headlines: int = 5
    news_snippet_max_chars: int = 500

    # Market Mood
    market_mood_url: str = "https://www.tickertape.in/market-mood-index"

    # Stock Screener
    screener_max_results: int = 50
    nse_equity_list_url: str = "https://nsearchives.nseinstitute.com/content/equities/EQUITY_L.csv"
    screener_screen_url: str = "https://www.screener.in/screen/raw/"

    # Peer Comparison
    peers_max_count: int = 10
    peers_fundamental_comparison: bool = True
    peers_technical_comparison: bool = True
    peers_fundamental_metrics: str = "pe,pb,roe,debt_to_equity,dividend_yield,market_cap,net_margin"
    peers_technical_metrics: str = "rsi,ema_trend,macd_signal,price_vs_ema200"

    # Logging
    log_level: str = "INFO"
    log_file: str = ""
    log_format: str = "text"

    # HTTP
    http_user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    http_timeout: int = 30
    http_max_retries: int = 3

    model_config = {
        "env_prefix": "SA_",
        "env_file": "configurations.env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @field_validator("csv_cache_dir")
    @classmethod
    def expand_paths(cls, v: str) -> str:
        return _expand_path(v)

    @property
    def ema_periods(self) -> List[int]:
        return _csv_to_int_list(self.ta_ema_periods)

    @property
    def macd_params(self) -> List[int]:
        return _csv_to_int_list(self.ta_macd_params)

    @property
    def forecast_scenarios(self) -> List[str]:
        return _csv_to_list(self.fa_forecast_scenarios)

    @property
    def peer_fundamental_metrics_list(self) -> List[str]:
        return _csv_to_list(self.peers_fundamental_metrics)

    @property
    def peer_technical_metrics_list(self) -> List[str]:
        return _csv_to_list(self.peers_technical_metrics)

    @property
    def supported_regions_list(self) -> List[str]:
        return _csv_to_list(self.supported_regions)


def get_settings() -> Settings:
    return Settings()
