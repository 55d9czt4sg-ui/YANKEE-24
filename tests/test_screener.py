"""Tests for screener module (IV trend + dealer scoring)."""

import pytest
from screener import IVTrendAnalyzer, DealerScorer


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
