"""QuantWheel API client with caching layer."""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from models import GEXData, VannaData
import config
import time


class Cache:
    """Simple in-memory cache with TTL."""

    def __init__(self):
        self._cache: Dict[str, tuple[Any, float]] = (
            {}
        )  # key -> (value, expiry_timestamp)

    def set(self, key: str, value: Any, ttl_minutes: int = 5):
        """Store a value with expiry."""
        expiry = time.time() + (ttl_minutes * 60)
        self._cache[key] = (value, expiry)

    def get(self, key: str) -> Optional[Any]:
        """Retrieve value if not expired."""
        if key not in self._cache:
            return None

        value, expiry = self._cache[key]
        if time.time() > expiry:
            del self._cache[key]
            return None

        return value

    def is_stale(self, key: str) -> bool:
        """Check if key exists but is expired."""
        if key not in self._cache:
            return False
        _, expiry = self._cache[key]
        return time.time() > expiry

    def stats(self) -> Dict[str, int]:
        """Return cache stats."""
        now = time.time()
        valid = sum(1 for _, exp in self._cache.values() if now < exp)
        total = len(self._cache)
        return {"valid": valid, "total": total}


class QuantWheelClient:
    """Wrapper around QuantWheel MCP tools with caching."""

    def __init__(self, cache_ttl_minutes: int = config.CACHE_TTL_MINUTES):
        self.cache = Cache()
        self.cache_ttl_minutes = cache_ttl_minutes
        self.call_count = 0  # Track API calls for stats

    def get_gex(self, ticker: str, expiration: str) -> Optional[GEXData]:
        """Fetch GEX (gamma exposure) data for ticker + expiration."""
        cache_key = f"gex:{ticker}:{expiration}"

        # Try cache first
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        # Fetch from QuantWheel
        try:
            data = self._fetch_gex_from_qw(ticker, expiration)
            if data is None:
                return None

            gex_data = GEXData(
                net_gamma=data.get("net_gamma", 0.0),
                gamma_buildup_pct=data.get("gamma_buildup_pct", 0.0),
            )
            self.cache.set(cache_key, gex_data, self.cache_ttl_minutes)
            self.call_count += 1
            return gex_data
        except Exception as e:
            print(f"⚠️  GEX fetch failed for {ticker}: {e}")
            return None

    def get_vanna_charm(self, ticker: str) -> Optional[VannaData]:
        """Fetch Vanna & Charm data for ticker."""
        cache_key = f"vanna:{ticker}"

        # Try cache first
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        # Fetch from QuantWheel
        try:
            data = self._fetch_vanna_from_qw(ticker)
            if data is None:
                return None

            vanna_data = VannaData(
                vanna_regime=data.get("vanna_regime", "unknown"),
                bull_bear_ratio=data.get("bull_bear_ratio", 0.0),
                bullish_target=data.get("bullish_target", 0.0),
            )
            self.cache.set(cache_key, vanna_data, self.cache_ttl_minutes)
            self.call_count += 1
            return vanna_data
        except Exception as e:
            print(f"⚠️  Vanna fetch failed for {ticker}: {e}")
            return None

    def get_quote(self, ticker: str) -> Optional[tuple[float, float]]:
        """Fetch current price and IV. Returns (price, iv) or None."""
        cache_key = f"quote:{ticker}"

        # Try cache first
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        # Fetch from QuantWheel
        try:
            data = self._fetch_quote_from_qw(ticker)
            if data is None:
                return None

            quote = (data.get("price", 0.0), data.get("iv", 0.0))
            self.cache.set(cache_key, quote, self.cache_ttl_minutes)
            self.call_count += 1
            return quote
        except Exception as e:
            print(f"⚠️  Quote fetch failed for {ticker}: {e}")
            return None

    def get_all_tickers(self):
        """Return list of all tickers (SPX 500 + NDX 100)."""
        return config.ALL_TICKERS

    def cache_stats(self) -> Dict[str, Any]:
        """Return cache statistics."""
        stats = self.cache.stats()
        return {
            "cache_entries": stats["total"],
            "valid_entries": stats["valid"],
            "total_api_calls": self.call_count,
        }

    # Private methods (to be mocked in tests or implemented with actual MCP calls)

    def _fetch_gex_from_qw(self, ticker: str, expiration: str) -> Optional[Dict]:
        """Call QuantWheel MCP get_gex tool. Placeholder for MCP integration."""
        # TODO: Implement actual QuantWheel MCP call
        # For now, return dummy data for testing
        return {
            "net_gamma": 0.0,
            "put_wall": 0.0,
            "call_wall": 0.0,
            "gamma_buildup_pct": 0.0,
        }

    def _fetch_vanna_from_qw(self, ticker: str) -> Optional[Dict]:
        """Call QuantWheel MCP get_vanna_charm tool. Placeholder for MCP integration."""
        # TODO: Implement actual QuantWheel MCP call
        return {
            "vanna_regime": "unknown",
            "bull_bear_ratio": 0.0,
            "bullish_target": 0.0,
        }

    def _fetch_quote_from_qw(self, ticker: str) -> Optional[Dict]:
        """Call QuantWheel MCP get_quote tool. Placeholder for MCP integration."""
        # TODO: Implement actual QuantWheel MCP call
        return {
            "price": 0.0,
            "iv": 0.0,
        }
