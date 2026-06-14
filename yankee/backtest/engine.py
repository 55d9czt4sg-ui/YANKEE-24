"""A simple vectorized backtesting engine.

Strategies produce a "target position" series of -1 (short), 0 (flat),
or 1 (long) for each bar. The engine assumes the position decided on bar
`t` is held over the return from bar `t` to `t+1` (i.e. positions are
shifted by one bar to avoid lookahead bias), and reports portfolio
performance statistics.

This is meant for quick research/idea validation, not order-level
execution simulation (no bid/ask spreads, partial fills, etc.).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

TRADING_DAYS_PER_YEAR = 252


@dataclass
class BacktestResult:
    equity_curve: pd.Series
    returns: pd.Series
    positions: pd.Series
    total_return: float
    cagr: float
    sharpe: float
    max_drawdown: float
    num_trades: int
    win_rate: float

    def summary(self) -> dict:
        return {
            "total_return": self.total_return,
            "cagr": self.cagr,
            "sharpe": self.sharpe,
            "max_drawdown": self.max_drawdown,
            "num_trades": self.num_trades,
            "win_rate": self.win_rate,
        }


def _trade_returns(close: pd.Series, positions: pd.Series) -> list[float]:
    """Per-trade returns for each contiguous non-zero position segment."""
    trades: list[float] = []
    current_pos = 0
    entry_price: float | None = None

    for price, pos in zip(close.to_numpy(), positions.to_numpy()):
        if pos != current_pos:
            if current_pos != 0 and entry_price is not None:
                trades.append(current_pos * (price - entry_price) / entry_price)
            entry_price = price if pos != 0 else None
            current_pos = pos

    if current_pos != 0 and entry_price is not None:
        trades.append(current_pos * (close.iloc[-1] - entry_price) / entry_price)

    return trades


def run_backtest(
    df: pd.DataFrame,
    positions: pd.Series,
    initial_capital: float = 10_000.0,
    commission: float = 0.0,
) -> BacktestResult:
    """Run a vectorized backtest.

    Args:
        df: OHLCV price DataFrame with a "Close" column.
        positions: target position per bar, in {-1, 0, 1} (or any
            scaling factor for leverage/sizing), aligned to df.index.
        initial_capital: starting portfolio value.
        commission: fractional cost applied to the absolute change in
            position on each bar (e.g. 0.001 = 10 bps per turnover).

    Returns:
        BacktestResult with the equity curve and summary statistics.
    """
    close = df["Close"]
    positions = positions.reindex(df.index).fillna(0)

    daily_returns = close.pct_change().fillna(0)

    # Position held during bar t is decided on bar t-1's close to avoid
    # lookahead bias.
    held_positions = positions.shift(1).fillna(0)

    position_changes = positions.diff().abs().fillna(0)
    costs = position_changes * commission

    strategy_returns = held_positions * daily_returns - costs

    equity_curve = initial_capital * (1 + strategy_returns).cumprod()
    equity_curve.name = "equity"

    total_return = equity_curve.iloc[-1] / initial_capital - 1 if len(equity_curve) else 0.0

    if len(df.index) >= 2:
        num_years = (df.index[-1] - df.index[0]).days / 365.25
    else:
        num_years = 0.0

    if num_years > 0 and equity_curve.iloc[-1] > 0:
        cagr = (equity_curve.iloc[-1] / initial_capital) ** (1 / num_years) - 1
    else:
        cagr = 0.0

    std = strategy_returns.std()
    sharpe = (strategy_returns.mean() / std * math.sqrt(TRADING_DAYS_PER_YEAR)) if std else 0.0

    running_max = equity_curve.cummax()
    drawdown = (equity_curve - running_max) / running_max.replace(0, np.nan)
    max_drawdown = drawdown.min() if not drawdown.empty else 0.0

    trades = _trade_returns(close, positions)
    num_trades = len(trades)
    win_rate = (sum(1 for t in trades if t > 0) / num_trades) if num_trades else 0.0

    return BacktestResult(
        equity_curve=equity_curve,
        returns=strategy_returns,
        positions=positions,
        total_return=float(total_return),
        cagr=float(cagr),
        sharpe=float(sharpe),
        max_drawdown=float(max_drawdown) if not pd.isna(max_drawdown) else 0.0,
        num_trades=num_trades,
        win_rate=float(win_rate),
    )
