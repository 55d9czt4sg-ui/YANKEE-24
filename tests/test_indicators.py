import pandas as pd

from yankee.indicators.core import atr, bollinger_bands, ema, macd, rsi, sma, stochastic_oscillator


def test_sma_basic():
    series = pd.Series([1, 2, 3, 4, 5])
    result = sma(series, window=2)
    assert pd.isna(result.iloc[0])
    assert result.iloc[1] == 1.5
    assert result.iloc[-1] == 4.5


def test_ema_no_nans_and_tracks_series():
    series = pd.Series(range(1, 21), dtype=float)
    result = ema(series, window=5)
    assert not result.isna().any()
    # EMA of a monotonically increasing series should also increase.
    assert (result.diff().dropna() > 0).all()


def test_rsi_bounds(price_df):
    result = rsi(price_df["Close"], window=14)
    valid = result.dropna()
    assert not valid.empty
    assert valid.between(0, 100).all()


def test_rsi_strong_uptrend_is_high():
    series = pd.Series(range(1, 31), dtype=float)  # strictly increasing
    result = rsi(series, window=14)
    assert result.iloc[-1] > 90


def test_macd_columns(price_df):
    result = macd(price_df["Close"])
    assert set(result.columns) == {"macd", "signal", "hist"}
    # hist should equal macd - signal
    pd.testing.assert_series_equal(result["hist"], (result["macd"] - result["signal"]).rename("hist"))


def test_bollinger_band_ordering(price_df):
    bands = bollinger_bands(price_df["Close"], window=20)
    valid = bands.dropna()
    assert (valid["upper"] >= valid["mid"]).all()
    assert (valid["mid"] >= valid["lower"]).all()


def test_atr_non_negative(price_df):
    result = atr(price_df, window=14)
    valid = result.dropna()
    assert not valid.empty
    assert (valid >= 0).all()


def test_stochastic_oscillator_bounds(price_df):
    result = stochastic_oscillator(price_df)
    valid = result.dropna()
    assert not valid.empty
    assert valid["%K"].between(0, 100).all()
    assert valid["%D"].between(0, 100).all()
