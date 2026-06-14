"""Market data access via yfinance, with simple on-disk caching.

All functions return pandas objects with a normalized schema so the rest
of the toolkit (indicators, screener, backtest, charts) can rely on
consistent column names: Open, High, Low, Close, Volume (and Adj Close
when available), indexed by a DatetimeIndex named "Date".
"""

from __future__ import annotations

import time

import pandas as pd
import yfinance as yf

from yankee.config import CACHE_DIR

# How long a cached price history is considered fresh.
CACHE_TTL_SECONDS = 60 * 60 * 4  # 4 hours


def _cache_path(ticker: str, period: str, interval: str) -> "pathlib.Path":
    safe_ticker = ticker.upper().replace("/", "_")
    return CACHE_DIR / f"{safe_ticker}_{period}_{interval}.csv"


def get_price_history(
    ticker: str,
    period: str = "1y",
    interval: str = "1d",
    use_cache: bool = True,
) -> pd.DataFrame:
    """Fetch OHLCV history for a single ticker.

    Args:
        ticker: e.g. "AAPL".
        period: yfinance period string, e.g. "1mo", "6mo", "1y", "5y", "max".
        interval: yfinance interval string, e.g. "1d", "1h", "1wk".
        use_cache: read/write a local CSV cache to avoid repeat downloads.

    Returns:
        DataFrame indexed by Date with columns Open, High, Low, Close,
        Volume (and Adj Close when present). Empty DataFrame if no data
        is available.
    """
    cache_file = _cache_path(ticker, period, interval)

    if use_cache and cache_file.exists():
        age = time.time() - cache_file.stat().st_mtime
        if age < CACHE_TTL_SECONDS:
            df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
            df.index.name = "Date"
            return df

    try:
        df = yf.Ticker(ticker).history(period=period, interval=interval)
    except Exception:
        # yfinance can raise unexpected errors (e.g. TypeError) when the
        # underlying HTTP request fails outright (network blocked, rate
        # limited, etc). Treat that the same as "no data".
        return pd.DataFrame()

    if df.empty:
        return df

    df = df.rename_axis("Date")
    # Drop columns yfinance sometimes adds that we don't use downstream.
    for extra_col in ("Dividends", "Stock Splits", "Capital Gains"):
        if extra_col in df.columns:
            df = df.drop(columns=extra_col)

    if use_cache:
        df.to_csv(cache_file)

    return df


def get_multiple_history(
    tickers: list[str],
    period: str = "1y",
    interval: str = "1d",
    use_cache: bool = True,
) -> dict[str, pd.DataFrame]:
    """Fetch OHLCV history for multiple tickers, keyed by ticker symbol."""
    return {t: get_price_history(t, period=period, interval=interval, use_cache=use_cache) for t in tickers}


def get_info(ticker: str) -> dict:
    """Return the raw company info/profile dict from yfinance for a ticker.

    Useful for due diligence: sector, industry, market cap, valuation
    ratios, business summary, etc.
    """
    return yf.Ticker(ticker).info


def get_financials(ticker: str) -> dict[str, pd.DataFrame]:
    """Return key financial statements for a ticker.

    Returns a dict with keys: "income_statement", "balance_sheet",
    "cash_flow" mapping to DataFrames (annual figures).
    """
    t = yf.Ticker(ticker)
    return {
        "income_statement": t.income_stmt,
        "balance_sheet": t.balance_sheet,
        "cash_flow": t.cashflow,
    }


def is_stale(ticker: str, period: str = "1y", interval: str = "1d") -> bool:
    """Whether the cached history for a ticker is missing or expired."""
    cache_file = _cache_path(ticker, period, interval)
    if not cache_file.exists():
        return True
    age = time.time() - cache_file.stat().st_mtime
    return age >= CACHE_TTL_SECONDS


def clear_cache() -> None:
    """Remove all cached price history files."""
    for f in CACHE_DIR.glob("*.csv"):
        f.unlink()
