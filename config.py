# config.py
"""Configuration constants for Core Market Regime Framework."""

# Cache settings
CACHE_TTL_MINUTES = 5

# Filtering thresholds
IV_DROP_THRESHOLD = "3day_avg"  # current_iv < 3day_avg_iv
PUT_WALL_PROXIMITY_PCT = 3.0  # price <= put_wall * (1 + PUT_WALL_PROXIMITY_PCT/100)
DTE_MIN = 0
DTE_MAX = 21

# Scoring weights (must sum to 1.0)
DEALER_SCORE_WEIGHTS = {
    "gamma_buildup": 0.30,
    "bull_bear_ratio": 0.25,
    "dealer_positioning": 0.25,
    "put_wall_proximity": 0.20,
}

# Gamma buildup thresholds for status badges
GAMMA_BUILDUP_THRESHOLDS = {
    "EXPLOSIVE": 500,      # > 500%
    "HOT": 150,            # 150-500%
    "PRIME": 50,           # 50-150%
    "SOLID": 0,            # 0-50%
    "CAUTION": float("-inf"),  # < 0%
}

# SPX 500 + NDX 100 tickers (hardcoded for MVP; can be fetched from QuantWheel later)
SPX_500_TICKERS = [
    "MSFT", "AAPL", "NVDA", "TSLA", "AMZN", "GOOG", "META", "BRK.B", "JNJ", "V",
    "WMT", "JPM", "PG", "COST", "MA", "HD", "ABBV", "CRM", "NFLX", "AVGO",
    "XOM", "PEP", "LLY", "DIS", "CSCO", "INTC", "MRK", "QCOM", "HON", "IBM",
    # ... simplified for MVP; full list has 500
]

NDX_100_TICKERS = [
    "TSLA", "AAPL", "MSFT", "AMZN", "GOOG", "META", "ASML", "COST",
    "AVGO", "NFLX", "GOOGL", "NVDA", "INTC", "CSCO", "PYPL", "CMCSA", "AMD", "QCOM",
    # ... simplified for MVP; full list has 100
]

ALL_TICKERS = list(dict.fromkeys(SPX_500_TICKERS + NDX_100_TICKERS))

# QuantWheel API settings
QW_API_TIMEOUT_SEC = 10
QW_MAX_RETRIES = 2
