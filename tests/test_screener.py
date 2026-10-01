"""Tests for screener module (IV trend + dealer scoring + filtering engine)."""

import pytest
from screener import IVTrendAnalyzer, DealerScorer, ScreeningEngine
from models import Ticker, GEXData, VannaData, Setup


def test_iv_trend_dropping():
    """Current IV below 3-day avg = dropping."""
    analyzer = IVTrendAnalyzer()
    is_dropping, direction = analyzer.calculate_iv_trend(
        current_iv=18.0, iv_3day_avg=19.0, iv_5day_avg=20.0
    )
    assert is_dropping == True
    assert direction == "DROPPING"


def test_iv_trend_rising():
    """Current IV above 3-day avg = rising."""
    analyzer = IVTrendAnalyzer()
    is_dropping, direction = analyzer.calculate_iv_trend(
        current_iv=20.0, iv_3day_avg=19.0, iv_5day_avg=18.0
    )
    assert is_dropping == False
    assert direction == "RISING"


def test_iv_trend_flat():
    """Current IV equal to 3-day avg = flat."""
    analyzer = IVTrendAnalyzer()
    is_dropping, direction = analyzer.calculate_iv_trend(
        current_iv=19.0, iv_3day_avg=19.0, iv_5day_avg=19.0
    )
    assert is_dropping == False
    assert direction == "FLAT"


def test_dealer_score_all_aligned():
    """All conditions aligned = high dealer score."""
    scorer = DealerScorer()
    score = scorer.calculate_dealer_score(
        has_pos_gamma=True,
        has_pos_vanna=True,
        is_iv_dropping=True,
        bull_bear_ratio=2.5,
        has_bullish_drift=True,
    )
    assert score >= 85  # Should be in "strong alignment" range


def test_dealer_score_partial_alignment():
    """Some conditions aligned = moderate dealer score."""
    scorer = DealerScorer()
    score = scorer.calculate_dealer_score(
        has_pos_gamma=True,
        has_pos_vanna=True,
        is_iv_dropping=False,
        bull_bear_ratio=1.5,
        has_bullish_drift=True,
    )
    assert 60 <= score < 85


def test_dealer_score_misaligned():
    """No conditions aligned = low dealer score."""
    scorer = DealerScorer()
    score = scorer.calculate_dealer_score(
        has_pos_gamma=False,
        has_pos_vanna=False,
        is_iv_dropping=False,
        bull_bear_ratio=0.8,
        has_bullish_drift=False,
    )
    assert score < 60


def test_composite_rank_calculation():
    """Composite rank combines 4 weighted metrics (0-10)."""
    scorer = DealerScorer()
    rank = scorer.calculate_composite_rank(
        gamma_buildup_pcts=[100.0, 150.0, 50.0],  # List of all candidates' gamma
        bull_bear_ratios=[2.5, 2.0, 1.5],  # List of all candidates' ratios
        dealer_scores=[90, 85, 75],  # List of all candidates' scores
        put_wall_proximities_pct=[0.5, 1.5, 3.0],  # List of all candidates' proximities
    )
    assert 0 <= rank <= 10


def test_composite_rank_normalization():
    """Composite rank uses decile normalization (accounts for outliers)."""
    scorer = DealerScorer()
    # Rank a moderate ticker among high and low extremes
    # Note: First candidate (500% gamma, 95 dealer score) is the top performer
    rank_top = scorer.calculate_composite_rank(
        gamma_buildup_pcts=[500.0, 150.0, 50.0],
        bull_bear_ratios=[3.0, 2.0, 1.5],
        dealer_scores=[95, 85, 70],
        put_wall_proximities_pct=[0.1, 1.5, 2.9],
    )
    # Top candidate should score high (7+)
    assert 6 <= rank_top <= 10

    # Now rank the middle candidate (150% gamma, 85 dealer score)
    rank_middle = scorer.calculate_composite_rank(
        gamma_buildup_pcts=[150.0, 500.0, 50.0],
        bull_bear_ratios=[2.0, 3.0, 1.5],
        dealer_scores=[85, 95, 70],
        put_wall_proximities_pct=[1.5, 0.1, 2.9],
    )
    # Middle candidate should land around 5-6, not be skewed by outliers
    assert 4 <= rank_middle <= 7


# ===== FILTERING ENGINE TESTS (TASK 5) =====


def test_filter_positive_gamma():
    """Filter rejects if gamma is negative."""
    engine = ScreeningEngine()
    ticker = Ticker("NVDA", 221.82, 18.5, 230.0, 220.0, 222.5)
    gex = GEXData(net_gamma=-100.0, gamma_buildup_pct=-10.0)  # Negative
    vanna = VannaData("positive", 2.48, 230.0)
    setup = Setup(ticker, gex, vanna, {"positive_gamma": False}, 5.0, "CAUTION", "SKIP")

    assert engine.apply_filter(setup) == False


def test_filter_positive_vanna():
    """Filter rejects if vanna regime is negative."""
    engine = ScreeningEngine()
    ticker = Ticker("NVDA", 221.82, 18.5, 230.0, 220.0, 222.5)
    gex = GEXData(net_gamma=150.0, gamma_buildup_pct=50.0)
    vanna = VannaData("negative", 0.8, 210.0)  # Negative regime
    setup = Setup(ticker, gex, vanna, {"positive_vanna": False}, 5.0, "CAUTION", "SKIP")

    assert engine.apply_filter(setup) == False


def test_filter_iv_dropping():
    """Filter rejects if IV is rising or flat."""
    engine = ScreeningEngine()
    ticker = Ticker("NVDA", 221.82, 20.0, 230.0, 220.0, 222.5)
    gex = GEXData(net_gamma=150.0, gamma_buildup_pct=50.0)
    vanna = VannaData("positive", 2.48, 230.0)
    setup = Setup(ticker, gex, vanna, {"iv_dropping": False}, 5.0, "SOLID", "BUY_DIPS")

    assert engine.apply_filter(setup) == False


def test_filter_put_wall_proximity():
    """Filter rejects if price > 3% above put wall."""
    engine = ScreeningEngine()
    ticker = Ticker("NVDA", 240.0, 18.5, 230.0, 220.0, 222.5)  # 9% above put wall
    gex = GEXData(net_gamma=150.0, gamma_buildup_pct=50.0)
    vanna = VannaData("positive", 2.48, 230.0)
    setup = Setup(
        ticker, gex, vanna, {"put_wall_proximity": False}, 5.0, "SOLID", "BUY_DIPS"
    )

    assert engine.apply_filter(setup) == False


def test_filter_dte_range():
    """Filter rejects if no expirations in 0-21 DTE."""
    engine = ScreeningEngine()
    ticker = Ticker("NVDA", 221.82, 18.5, 230.0, 220.0, 222.5)
    gex = GEXData(net_gamma=150.0, gamma_buildup_pct=50.0)
    vanna = VannaData("positive", 2.48, 230.0)
    setup = Setup(ticker, gex, vanna, {"dte_range": False}, 5.0, "SOLID", "BUY_DIPS")

    assert engine.apply_filter(setup) == False


def test_filter_bullish_drift():
    """Filter rejects if no bullish drift target."""
    engine = ScreeningEngine()
    ticker = Ticker("NVDA", 221.82, 18.5, 210.0, 220.0, 222.5)  # Target below price
    gex = GEXData(net_gamma=150.0, gamma_buildup_pct=50.0)
    vanna = VannaData("positive", 2.48, 210.0)
    setup = Setup(
        ticker, gex, vanna, {"bullish_drift": False}, 5.0, "SOLID", "BUY_DIPS"
    )

    assert engine.apply_filter(setup) == False


def test_filter_all_conditions_pass():
    """All 6 conditions pass = setup included."""
    engine = ScreeningEngine()
    ticker = Ticker("NVDA", 221.82, 18.5, 230.0, 220.0, 222.5)
    gex = GEXData(net_gamma=150.0, gamma_buildup_pct=50.0)
    vanna = VannaData("positive", 2.48, 230.0)
    setup = Setup(
        ticker,
        gex,
        vanna,
        {
            "positive_gamma": True,
            "positive_vanna": True,
            "iv_dropping": True,
            "put_wall_proximity": True,
            "dte_range": True,
            "bullish_drift": True,
        },
        8.2,
        "PRIME",
        "BUY_DIPS",
    )

    assert engine.apply_filter(setup) == True


def test_check_conditions_all_pass():
    """check_conditions returns True for all conditions when they pass."""
    engine = ScreeningEngine()
    ticker = Ticker(
        "NVDA", 221.82, 18.0, 230.0, 220.0, 222.5
    )  # Price 0.8% above put wall
    gex = GEXData(net_gamma=150.0, gamma_buildup_pct=50.0)
    vanna = VannaData("positive", 2.48, 230.0)

    conditions = engine.check_conditions(
        ticker=ticker,
        gex=gex,
        vanna=vanna,
        iv_3day_avg=19.0,  # Current IV (18.0) < 3day avg
        iv_5day_avg=20.0,
        expirations_dte=[7, 14, 21],  # Valid DTEs
    )

    assert conditions["positive_gamma"] == True
    assert conditions["positive_vanna"] == True
    assert conditions["iv_dropping"] == True
    assert conditions["put_wall_proximity"] == True
    assert conditions["dte_range"] == True
    assert conditions["bullish_drift"] == True


def test_get_status_badge_explosive():
    """Status badge: gamma >= 500% = EXPLOSIVE."""
    engine = ScreeningEngine()
    status = engine.get_status_badge(500.0)
    assert status == "EXPLOSIVE"


def test_get_status_badge_hot():
    """Status badge: gamma 150-500% = HOT."""
    engine = ScreeningEngine()
    status = engine.get_status_badge(300.0)
    assert status == "HOT"


def test_get_status_badge_prime():
    """Status badge: gamma 50-150% = PRIME."""
    engine = ScreeningEngine()
    status = engine.get_status_badge(100.0)
    assert status == "PRIME"


def test_get_status_badge_solid():
    """Status badge: gamma 0-50% = SOLID."""
    engine = ScreeningEngine()
    status = engine.get_status_badge(25.0)
    assert status == "SOLID"


def test_get_status_badge_caution():
    """Status badge: gamma < 0% = CAUTION."""
    engine = ScreeningEngine()
    status = engine.get_status_badge(-10.0)
    assert status == "CAUTION"


def test_get_trade_recommendation_explosive():
    """Trade recommendation: EXPLOSIVE = MOMENTUM_SCALP_OR_CALL_SPREAD."""
    engine = ScreeningEngine()
    rec = engine.get_trade_recommendation("EXPLOSIVE")
    assert rec == "MOMENTUM_SCALP_OR_CALL_SPREAD"


def test_get_trade_recommendation_hot():
    """Trade recommendation: HOT = BUY_DIPS_OR_SHORT_PUTS."""
    engine = ScreeningEngine()
    rec = engine.get_trade_recommendation("HOT")
    assert rec == "BUY_DIPS_OR_SHORT_PUTS"


def test_get_trade_recommendation_prime():
    """Trade recommendation: PRIME = BUY_DIPS."""
    engine = ScreeningEngine()
    rec = engine.get_trade_recommendation("PRIME")
    assert rec == "BUY_DIPS"


def test_get_trade_recommendation_solid():
    """Trade recommendation: SOLID = DIP_BUYER."""
    engine = ScreeningEngine()
    rec = engine.get_trade_recommendation("SOLID")
    assert rec == "DIP_BUYER"


def test_get_trade_recommendation_caution():
    """Trade recommendation: CAUTION = SKIP."""
    engine = ScreeningEngine()
    rec = engine.get_trade_recommendation("CAUTION")
    assert rec == "SKIP"
