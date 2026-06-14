"""Technical indicators operating on pandas Series/DataFrames.

Price DataFrames are expected to have columns: Open, High, Low, Close,
Volume (the schema returned by yankee.data.loader.get_price_history).
"""

from __future__ import annotations

import pandas as pd


def sma(series: pd.Series, window: int = 20) -> pd.Series:
    """Simple moving average."""
    return series.rolling(window=window, min_periods=window).mean().rename(f"SMA_{window}")


def ema(series: pd.Series, window: int = 20) -> pd.Series:
    """Exponential moving average."""
    return series.ewm(span=window, adjust=False).mean().rename(f"EMA_{window}")


def rsi(series: pd.Series, window: int = 14) -> pd.Series:
    """Relative Strength Index (Wilder's smoothing), 0-100."""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()

    rs = avg_gain / avg_loss
    result = 100 - (100 / (1 + rs))
    # Where average loss is zero, RSI is 100 (no losses to average).
    result = result.where(avg_loss != 0, 100.0)
    return result.rename(f"RSI_{window}")


def macd(
    series: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.DataFrame:
    """Moving Average Convergence Divergence.

    Returns a DataFrame with columns: macd, signal, hist.
    """
    fast_ema = series.ewm(span=fast, adjust=False).mean()
    slow_ema = series.ewm(span=slow, adjust=False).mean()
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return pd.DataFrame({"macd": macd_line, "signal": signal_line, "hist": hist})


def bollinger_bands(series: pd.Series, window: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    """Bollinger Bands.

    Returns a DataFrame with columns: mid, upper, lower.
    """
    mid = series.rolling(window=window, min_periods=window).mean()
    std = series.rolling(window=window, min_periods=window).std()
    upper = mid + num_std * std
    lower = mid - num_std * std
    return pd.DataFrame({"mid": mid, "upper": upper, "lower": lower})


def atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
    """Average True Range. Requires High, Low, Close columns."""
    high, low, close = df["High"], df["Low"], df["Close"]
    prev_close = close.shift(1)

    tr = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    return tr.ewm(alpha=1 / window, min_periods=window, adjust=False).mean().rename(f"ATR_{window}")


def stochastic_oscillator(df: pd.DataFrame, k_window: int = 14, d_window: int = 3) -> pd.DataFrame:
    """Stochastic Oscillator. Requires High, Low, Close columns.

    Returns a DataFrame with columns: %K, %D.
    """
    low_min = df["Low"].rolling(window=k_window, min_periods=k_window).min()
    high_max = df["High"].rolling(window=k_window, min_periods=k_window).max()

    percent_k = 100 * (df["Close"] - low_min) / (high_max - low_min)
    percent_d = percent_k.rolling(window=d_window, min_periods=d_window).mean()

    return pd.DataFrame({"%K": percent_k, "%D": percent_d})
