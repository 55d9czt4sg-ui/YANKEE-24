import pandas as pd
import pytest

from yankee.screener import setups
from yankee.screener.setups import SETUPS, scan, scan_tickers
from tests.conftest import make_price_df


def test_all_setups_return_boolean_series(price_df):
    for name, func in SETUPS.items():
        result = func(price_df)
        assert isinstance(result, pd.Series), name
        assert result.dtype == bool, name
        assert len(result) == len(price_df), name


def test_golden_cross_fires_in_uptrend(uptrend_df):
    result = setups.golden_cross(uptrend_df, fast=50, slow=200)
    assert result.any()


def test_new_52w_high_fires_in_uptrend(uptrend_df):
    result = setups.new_52w_high(uptrend_df, window=200)
    # A strict uptrend should keep making new highs near the end.
    assert result.iloc[-10:].any()


def test_scan_returns_dict_of_bools(price_df):
    result = scan(price_df, setups=["golden_cross", "rsi_oversold"])
    assert set(result.keys()) == {"golden_cross", "rsi_oversold"}
    assert all(isinstance(v, bool) for v in result.values())


def test_scan_handles_insufficient_history():
    short_df = make_price_df(n=5)
    result = scan(short_df, setups=["golden_cross"])
    assert result["golden_cross"] is False


def test_scan_tickers_uses_data_loader(monkeypatch, uptrend_df):
    monkeypatch.setattr(setups, "get_price_history", lambda ticker, period, interval: uptrend_df)

    result = scan_tickers(["FAKE"], setups=["new_52w_high"], period="1y", interval="1d")

    assert list(result.columns) == ["Ticker", "Setup", "Date", "Close"]
    if not result.empty:
        assert (result["Ticker"] == "FAKE").all()


def test_scan_tickers_skips_empty_data(monkeypatch):
    monkeypatch.setattr(setups, "get_price_history", lambda ticker, period, interval: pd.DataFrame())

    result = scan_tickers(["FAKE"], period="1y", interval="1d")
    assert result.empty
