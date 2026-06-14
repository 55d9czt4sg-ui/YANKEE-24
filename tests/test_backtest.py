import pandas as pd

from yankee.backtest.engine import run_backtest
from yankee.backtest.strategies import STRATEGIES, get_strategy, sma_crossover_strategy


def test_flat_positions_preserve_capital(price_df):
    positions = pd.Series(0, index=price_df.index)
    result = run_backtest(price_df, positions, initial_capital=10_000)

    assert result.total_return == 0
    assert result.num_trades == 0
    assert (result.equity_curve == 10_000).all()


def test_long_only_tracks_buy_and_hold_in_uptrend(uptrend_df):
    positions = pd.Series(1, index=uptrend_df.index)
    result = run_backtest(uptrend_df, positions, initial_capital=10_000)

    assert result.total_return > 0
    assert result.cagr > 0
    assert result.num_trades == 1
    assert result.win_rate == 1.0


def test_commission_reduces_returns_when_trading(uptrend_df):
    positions = sma_crossover_strategy(uptrend_df, fast=10, slow=30)

    no_cost = run_backtest(uptrend_df, positions, initial_capital=10_000, commission=0.0)
    with_cost = run_backtest(uptrend_df, positions, initial_capital=10_000, commission=0.01)

    assert with_cost.total_return <= no_cost.total_return


def test_get_strategy_unknown_raises():
    try:
        get_strategy("does_not_exist")
        assert False, "expected KeyError"
    except KeyError:
        pass


def test_all_strategies_produce_valid_positions(price_df):
    for name in STRATEGIES:
        strategy = get_strategy(name)
        positions = strategy(price_df)
        assert isinstance(positions, pd.Series)
        assert len(positions) == len(price_df)
        assert positions.dropna().isin([-1, 0, 1]).all()

        # Should run through the backtester without error.
        result = run_backtest(price_df, positions)
        assert result.equity_curve.iloc[0] > 0
