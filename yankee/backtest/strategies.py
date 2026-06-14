"""Example strategies producing target position series for the backtester.

Each function returns a pd.Series aligned to df.index with values in
{-1, 0, 1} representing the desired position (short, flat, long) on
each bar.
"""

from __future__ import annotations

import pandas as pd

from yankee.indicators.core import ema, macd, rsi, sma

STRATEGIES: dict[str, callable] = {}


def _register(name: str):
    def decorator(func):
        STRATEGIES[name] = func
        return func

    return decorator


@_register("sma_crossover")
def sma_crossover_strategy(df: pd.DataFrame, fast: int = 50, slow: int = 200) -> pd.Series:
    """Long when the fast SMA is above the slow SMA, otherwise flat."""
    fast_sma = sma(df["Close"], fast)
    slow_sma = sma(df["Close"], slow)
    position = (fast_sma > slow_sma).astype(int)
    return position.rename("position")


@_register("ema_crossover")
def ema_crossover_strategy(df: pd.DataFrame, fast: int = 12, slow: int = 26) -> pd.Series:
    """Long when the fast EMA is above the slow EMA, otherwise flat."""
    fast_ema = ema(df["Close"], fast)
    slow_ema = ema(df["Close"], slow)
    position = (fast_ema > slow_ema).astype(int)
    return position.rename("position")


@_register("rsi_mean_reversion")
def rsi_mean_reversion_strategy(
    df: pd.DataFrame,
    window: int = 14,
    lower: float = 30,
    upper: float = 70,
) -> pd.Series:
    """Buy when RSI drops below `lower`, exit when it rises above `upper`."""
    r = rsi(df["Close"], window)

    position = pd.Series(0, index=df.index, dtype=int)
    in_position = False
    for i, value in enumerate(r):
        if pd.isna(value):
            position.iloc[i] = 0
            continue
        if not in_position and value < lower:
            in_position = True
        elif in_position and value > upper:
            in_position = False
        position.iloc[i] = 1 if in_position else 0

    return position.rename("position")


@_register("macd_trend")
def macd_strategy(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.Series:
    """Long when the MACD line is above its signal line, otherwise flat."""
    m = macd(df["Close"], fast=fast, slow=slow, signal=signal)
    position = (m["macd"] > m["signal"]).astype(int)
    return position.rename("position")


def get_strategy(name: str) -> callable:
    """Look up a registered strategy by name."""
    if name not in STRATEGIES:
        raise KeyError(f"Unknown strategy '{name}'. Available: {sorted(STRATEGIES)}")
    return STRATEGIES[name]
