"""Technical "setup" detectors for screening stocks.

Each detector takes an OHLCV price DataFrame (as returned by
yankee.data.loader.get_price_history) and returns a boolean pd.Series,
aligned to df.index, that is True on bars where the setup condition
fires.

These are intentionally simple, well-known technical patterns intended
as a starting point for further research -- not trading advice.
"""

from __future__ import annotations

import pandas as pd

from yankee.data.loader import get_price_history
from yankee.indicators.core import bollinger_bands, macd, rsi, sma


def golden_cross(df: pd.DataFrame, fast: int = 50, slow: int = 200) -> pd.Series:
    """Fast SMA crosses above slow SMA (bullish)."""
    fast_sma = sma(df["Close"], fast)
    slow_sma = sma(df["Close"], slow)
    above = fast_sma > slow_sma
    return (above & ~above.shift(1).fillna(False)).rename("golden_cross")


def death_cross(df: pd.DataFrame, fast: int = 50, slow: int = 200) -> pd.Series:
    """Fast SMA crosses below slow SMA (bearish)."""
    fast_sma = sma(df["Close"], fast)
    slow_sma = sma(df["Close"], slow)
    below = fast_sma < slow_sma
    return (below & ~below.shift(1).fillna(False)).rename("death_cross")


def rsi_oversold(df: pd.DataFrame, window: int = 14, threshold: float = 30) -> pd.Series:
    """RSI below threshold (potential bounce / mean-reversion long)."""
    return (rsi(df["Close"], window) < threshold).rename("rsi_oversold")


def rsi_overbought(df: pd.DataFrame, window: int = 14, threshold: float = 70) -> pd.Series:
    """RSI above threshold (potential pullback / mean-reversion short)."""
    return (rsi(df["Close"], window) > threshold).rename("rsi_overbought")


def macd_bullish_crossover(df: pd.DataFrame) -> pd.Series:
    """MACD line crosses above its signal line."""
    m = macd(df["Close"])
    above = m["macd"] > m["signal"]
    return (above & ~above.shift(1).fillna(False)).rename("macd_bullish_crossover")


def macd_bearish_crossover(df: pd.DataFrame) -> pd.Series:
    """MACD line crosses below its signal line."""
    m = macd(df["Close"])
    below = m["macd"] < m["signal"]
    return (below & ~below.shift(1).fillna(False)).rename("macd_bearish_crossover")


def new_52w_high(df: pd.DataFrame, window: int = 252) -> pd.Series:
    """Close makes a new N-bar high (default ~52 weeks of daily bars)."""
    rolling_max = df["Close"].rolling(window=window, min_periods=window).max()
    return (df["Close"] >= rolling_max).rename("new_52w_high")


def new_52w_low(df: pd.DataFrame, window: int = 252) -> pd.Series:
    """Close makes a new N-bar low (default ~52 weeks of daily bars)."""
    rolling_min = df["Close"].rolling(window=window, min_periods=window).min()
    return (df["Close"] <= rolling_min).rename("new_52w_low")


def bollinger_band_squeeze(df: pd.DataFrame, window: int = 20, lookback: int = 120, percentile: float = 0.1) -> pd.Series:
    """Band width is in the bottom `percentile` of its recent range.

    A tight squeeze often precedes a volatility expansion / breakout.
    """
    bands = bollinger_bands(df["Close"], window=window)
    width = (bands["upper"] - bands["lower"]) / bands["mid"]
    threshold = width.rolling(window=lookback, min_periods=window).quantile(percentile)
    return (width <= threshold).rename("bollinger_band_squeeze")


def volume_spike(df: pd.DataFrame, window: int = 20, multiplier: float = 2.0) -> pd.Series:
    """Volume is at least `multiplier` times its recent average."""
    avg_volume = df["Volume"].rolling(window=window, min_periods=window).mean()
    return (df["Volume"] >= multiplier * avg_volume).rename("volume_spike")


SETUPS: dict[str, callable] = {
    "golden_cross": golden_cross,
    "death_cross": death_cross,
    "rsi_oversold": rsi_oversold,
    "rsi_overbought": rsi_overbought,
    "macd_bullish_crossover": macd_bullish_crossover,
    "macd_bearish_crossover": macd_bearish_crossover,
    "new_52w_high": new_52w_high,
    "new_52w_low": new_52w_low,
    "bollinger_band_squeeze": bollinger_band_squeeze,
    "volume_spike": volume_spike,
}


def scan(df: pd.DataFrame, setups: list[str] | None = None) -> dict[str, bool]:
    """Evaluate the requested setups against the most recent bar of `df`.

    Args:
        df: OHLCV price DataFrame.
        setups: names of setups (keys of SETUPS) to evaluate. Defaults
            to all available setups.

    Returns:
        Dict mapping setup name -> whether it fired on the latest bar.
        Returns False for setups that can't be computed (e.g. not
        enough history).
    """
    setups = setups or list(SETUPS.keys())
    results: dict[str, bool] = {}
    for name in setups:
        try:
            series = SETUPS[name](df)
            results[name] = bool(series.iloc[-1]) if not series.empty else False
        except Exception:
            results[name] = False
    return results


def scan_tickers(
    tickers: list[str],
    setups: list[str] | None = None,
    period: str = "1y",
    interval: str = "1d",
) -> pd.DataFrame:
    """Scan multiple tickers for the requested setups on their latest bar.

    Returns a long-form DataFrame with columns: Ticker, Setup, Date,
    Close -- one row per (ticker, setup) combination that currently
    matches.
    """
    rows = []
    for ticker in tickers:
        df = get_price_history(ticker, period=period, interval=interval)
        if df.empty:
            continue

        matches = scan(df, setups=setups)
        last_date = df.index[-1]
        last_close = df["Close"].iloc[-1]

        for setup_name, matched in matches.items():
            if matched:
                rows.append(
                    {
                        "Ticker": ticker,
                        "Setup": setup_name,
                        "Date": last_date,
                        "Close": last_close,
                    }
                )

    return pd.DataFrame(rows, columns=["Ticker", "Setup", "Date", "Close"])
