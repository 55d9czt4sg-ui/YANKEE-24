import numpy as np
import pandas as pd
import pytest


def make_price_df(n: int = 300, start_price: float = 100.0, drift: float = 0.0, seed: int = 42) -> pd.DataFrame:
    """Synthetic OHLCV data for tests (no network access)."""
    rng = np.random.default_rng(seed)
    returns = rng.normal(loc=drift, scale=0.01, size=n)
    close = start_price * np.cumprod(1 + returns)

    open_ = close * (1 + rng.normal(0, 0.001, n))
    high = np.maximum(open_, close) * (1 + np.abs(rng.normal(0, 0.002, n)))
    low = np.minimum(open_, close) * (1 - np.abs(rng.normal(0, 0.002, n)))
    volume = rng.integers(1_000_000, 5_000_000, n)

    index = pd.date_range("2023-01-02", periods=n, freq="B", name="Date")

    return pd.DataFrame(
        {
            "Open": open_,
            "High": high,
            "Low": low,
            "Close": close,
            "Volume": volume,
        },
        index=index,
    )


@pytest.fixture
def price_df() -> pd.DataFrame:
    return make_price_df()


@pytest.fixture
def uptrend_df() -> pd.DataFrame:
    return make_price_df(n=300, drift=0.003, seed=1)
