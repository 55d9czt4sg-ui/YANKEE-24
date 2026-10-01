"""Data models for Core Market Regime Framework."""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class Ticker:
    """Represents a stock ticker with price and derivative data."""

    name: str
    current_price: float
    current_iv: float
    bullish_target: float
    put_wall: Optional[float]
    call_wall: Optional[float]

    def distance_to_put_wall_pct(self) -> float:
        """Calculate % distance above put wall."""
        if self.put_wall is None or self.put_wall <= 0:
            return float("inf")
        return ((self.current_price - self.put_wall) / self.put_wall) * 100


@dataclass
class GEXData:
    """Gamma Exposure data from QuantWheel."""

    net_gamma: float
    gamma_buildup_pct: float
    put_wall: Optional[float] = None
    call_wall: Optional[float] = None


@dataclass
class VannaData:
    """Vanna & Charm data from QuantWheel."""

    vanna_regime: str  # "positive" or "negative"
    bull_bear_ratio: float
    bullish_target: float


@dataclass
class Setup:
    """A candidate setup meeting all filtering criteria."""

    ticker: Ticker
    gex: GEXData
    vanna: VannaData
    filters_passed: Dict[str, bool]
    composite_rank: float  # 0-10
    status: str  # "EXPLOSIVE", "HOT", "PRIME", "SOLID", "CAUTION"
    trade_recommendation: str  # "BUY_DIPS", "SHORT_PUTS", "MOMENTUM_SCALP", "SKIP"

    def all_filters_passed(self) -> bool:
        """Check if all 6 required filters passed."""
        required = {
            "positive_gamma",
            "positive_vanna",
            "iv_dropping",
            "put_wall_proximity",
            "dte_range",
            "bullish_drift",
        }
        return all(self.filters_passed.get(f, False) for f in required)


@dataclass
class ScanResult:
    """Complete scan results."""

    timestamp: str
    universe: List[str]  # ["SPX", "NDX"]
    tickers_scanned: int
    candidates_passed: int
    ranked_list: List[Setup]
    data_freshness_minutes: int = 0
    cache_hit_rate: float = 0.0

    def top_n(self, n: int) -> List[Setup]:
        """Return top N ranked setups."""
        return self.ranked_list[:n]
