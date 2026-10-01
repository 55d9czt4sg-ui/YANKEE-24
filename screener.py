"""Screener: filter engine and ranking logic."""

from typing import List, Tuple
import config


class IVTrendAnalyzer:
    """Analyzes IV trend (dropping/rising)."""

    @staticmethod
    def calculate_iv_trend(
        current_iv: float, iv_3day_avg: float, iv_5day_avg: float
    ) -> Tuple[bool, str]:
        """
        Determine if IV is dropping.

        Returns:
            (is_dropping: bool, trend_direction: str) where:
            - is_dropping: True if current < 3day_avg (with 1% threshold)
            - trend_direction: "DROPPING", "RISING", or "FLAT"
        """
        if current_iv < iv_3day_avg * 0.99:  # 1% threshold for "dropping"
            return True, "DROPPING"
        elif current_iv > iv_3day_avg * 1.01:
            return False, "RISING"
        else:
            return False, "FLAT"


class DealerScorer:
    """Scores dealer positioning and calculates composite ranks."""

    def calculate_dealer_score(
        self,
        has_pos_gamma: bool,
        has_pos_vanna: bool,
        is_iv_dropping: bool,
        bull_bear_ratio: float,
        has_bullish_drift: bool,
    ) -> int:
        """
        Calculate 0-100 dealer positioning score.

        Breakdown:
        - Positive gamma: +25
        - Positive vanna: +20
        - IV dropping: +20
        - Bull/bear ratio bonus: 0-20 (interpolated, capped at 1.0 - 3.0)
        - Bullish drift: +15
        """
        score = 0

        if has_pos_gamma:
            score += 25
        if has_pos_vanna:
            score += 20
        if is_iv_dropping:
            score += 20
        if has_bullish_drift:
            score += 15

        # Bull/bear ratio bonus (0-20): interpolate 1.0 -> 0, 2.5 -> 20
        if bull_bear_ratio >= 2.5:
            score += 20
        elif bull_bear_ratio >= 1.0:
            score += int((bull_bear_ratio - 1.0) / 1.5 * 20)

        return min(score, 100)  # Cap at 100

    def calculate_composite_rank(
        self,
        gamma_buildup_pcts: List[float],
        bull_bear_ratios: List[float],
        dealer_scores: List[int],
        put_wall_proximities_pct: List[float],
    ) -> float:
        """
        Calculate composite rank (0-10) using decile normalization.

        This ranks a single candidate among a list of candidates:
        - Converts each metric to 0-10 decile score
        - Applies weights: gamma 30%, bull/bear 25%, dealer 25%, proximity 20%
        - Returns weighted 0-10 composite score

        Args:
            gamma_buildup_pcts: List of all candidates' gamma buildup % (including target)
            bull_bear_ratios: List of all candidates' bull/bear ratios
            dealer_scores: List of all candidates' dealer scores (0-100)
            put_wall_proximities_pct: List of all candidates' % distance above put wall

        Returns:
            Composite rank (0-10) for the FIRST candidate in each list
        """
        if not gamma_buildup_pcts:
            return 0.0

        # Decile scoring function
        def to_decile(value: float, all_values: List[float]) -> float:
            if len(all_values) < 2:
                return 5.0  # Default middle score

            sorted_vals = sorted(all_values)
            percentile = len([v for v in sorted_vals if v < value]) / len(all_values)
            return percentile * 10.0  # 0-10

        # Score the first candidate (index 0)
        target_gamma = gamma_buildup_pcts[0]
        target_ratio = bull_bear_ratios[0]
        target_dealer = dealer_scores[0]
        target_proximity = put_wall_proximities_pct[0]

        # Convert to deciles
        gamma_decile = to_decile(target_gamma, gamma_buildup_pcts)
        ratio_decile = to_decile(target_ratio, bull_bear_ratios)
        dealer_decile = to_decile(target_dealer, dealer_scores)
        proximity_decile = 10.0 - to_decile(
            target_proximity, put_wall_proximities_pct
        )  # Invert: closer is better

        # Weighted average
        weights = config.DEALER_SCORE_WEIGHTS
        composite = (
            gamma_decile * weights["gamma_buildup"]
            + ratio_decile * weights["bull_bear_ratio"]
            + dealer_decile * weights["dealer_positioning"]
            + proximity_decile * weights["put_wall_proximity"]
        )

        return round(composite, 1)
