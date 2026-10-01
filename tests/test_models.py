"""Tests for data models."""

import pytest
from datetime import datetime
from models import Ticker, GEXData, VannaData, Setup, ScanResult


def test_ticker_creation():
    t = Ticker(
        name="NVDA",
        current_price=221.82,
        current_iv=18.5,
        bullish_target=230.0,
        put_wall=220.0,
        call_wall=222.5,
    )
    assert t.name == "NVDA"
    assert t.current_price == 221.82
    assert t.put_wall == 220.0


def test_missing_put_wall_fails_proximity():
    t = Ticker(
        name="NVDA",
        current_price=221.82,
        current_iv=18.5,
        bullish_target=230.0,
        put_wall=None,
        call_wall=None,
    )
    assert t.distance_to_put_wall_pct() == float("inf")


def test_gex_data_creation():
    gex = GEXData(net_gamma=150.5, gamma_buildup_pct=50.7)
    assert gex.net_gamma == 150.5
    assert gex.gamma_buildup_pct == 50.7


def test_vanna_data_creation():
    vanna = VannaData(
        vanna_regime="positive", bull_bear_ratio=2.48, bullish_target=230.0
    )
    assert vanna.vanna_regime == "positive"
    assert vanna.bull_bear_ratio == 2.48


def test_setup_creation():
    t = Ticker(
        name="NVDA",
        current_price=221.82,
        current_iv=18.5,
        bullish_target=230.0,
        put_wall=220.0,
        call_wall=222.5,
    )
    gex = GEXData(net_gamma=150.5, gamma_buildup_pct=50.7)
    vanna = VannaData(
        vanna_regime="positive", bull_bear_ratio=2.48, bullish_target=230.0
    )
    filters_passed = {
        "positive_gamma": True,
        "positive_vanna": True,
        "iv_dropping": True,
        "put_wall_proximity": True,
        "dte_range": True,
        "bullish_drift": True,
    }
    setup = Setup(
        ticker=t,
        gex=gex,
        vanna=vanna,
        filters_passed=filters_passed,
        composite_rank=8.2,
        status="PRIME",
        trade_recommendation="BUY_DIPS",
    )
    assert setup.ticker.name == "NVDA"
    assert setup.composite_rank == 8.2
    assert setup.status == "PRIME"


def test_scan_result_creation():
    result = ScanResult(
        timestamp="2026-10-01T13:35:22Z",
        universe=["SPX", "NDX"],
        tickers_scanned=600,
        candidates_passed=23,
        ranked_list=[],
    )
    assert result.tickers_scanned == 600
    assert result.candidates_passed == 23
