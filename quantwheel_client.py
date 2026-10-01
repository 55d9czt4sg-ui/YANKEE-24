"""QuantWheel API client with caching layer."""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from models import GEXData, VannaData
import config
import time
import logging
import subprocess
import json
import os

logger = logging.getLogger(__name__)

# MCP tool IDs for QuantWheel integration
MCP_SERVER_ID = "mcp__11431736-9636-4f13-b188-bd28f29f1080"
MCP_TOOL_GET_GEX = f"{MCP_SERVER_ID}__get_gex"
MCP_TOOL_GET_VANNA = f"{MCP_SERVER_ID}__get_vanna_charm"
MCP_TOOL_GET_QUOTE = f"{MCP_SERVER_ID}__get_stock_quote"


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

    def __init__(
        self,
        cache_ttl_minutes: int = config.CACHE_TTL_MINUTES,
        mcp_enabled: bool = True,
    ):
        self.cache = Cache()
        self.cache_ttl_minutes = cache_ttl_minutes
        self.call_count = 0  # Track API calls for stats
        self.mcp_enabled = mcp_enabled  # Toggle for testing/mocking

    def _call_mcp_tool(
        self,
        tool_name: str,
        params: Dict[str, Any],
        timeout_sec: int = config.QW_API_TIMEOUT_SEC,
    ) -> Optional[Dict[str, Any]]:
        """
        Call an MCP tool via Claude Code / Anthropic SDK.
        Falls back to mock if MCP is disabled or unavailable.
        """
        if not self.mcp_enabled:
            logger.debug(f"MCP disabled, skipping tool call: {tool_name}")
            return None

        try:
            # Try direct import first (for Claude Code environment)
            try:
                module_name = tool_name.replace("-", "_")
                mcp_module = __import__(f"mcp__{module_name}", fromlist=[tool_name])
                tool_func = getattr(mcp_module, tool_name, None)

                if tool_func:
                    response = tool_func(**params)
                    if isinstance(response, dict):
                        return response
                    logger.debug(
                        f"MCP tool {tool_name} returned non-dict: {type(response)}"
                    )
                    return None

            except (ImportError, AttributeError):
                logger.debug(f"MCP tool not found via import: {tool_name}")
                return None

        except Exception as e:
            logger.debug(f"MCP call error for {tool_name}: {e}")
            return None

        return None

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

    # Private methods (MCP tool integration)

    def _fetch_gex_from_qw(self, ticker: str, expiration: str) -> Optional[Dict]:
        """
        Call QuantWheel MCP get_gex tool.
        Returns: {"net_gamma": float, "gamma_buildup_pct": float} or None on error.
        """
        for attempt in range(config.QW_MAX_RETRIES):
            try:
                response = self._call_mcp_tool(
                    MCP_TOOL_GET_GEX,
                    {"ticker": ticker, "expiration": expiration},
                    timeout_sec=config.QW_API_TIMEOUT_SEC,
                )

                if response is None:
                    logger.debug(
                        f"GEX fetch returned None for {ticker} (attempt {attempt + 1})"
                    )
                    if attempt < config.QW_MAX_RETRIES - 1:
                        time.sleep(1)
                        continue
                    return None

                # Validate response has required fields
                if not isinstance(response, dict):
                    logger.debug(
                        f"Invalid GEX response type for {ticker}: {type(response)}"
                    )
                    return None

                # Extract gamma data from response (handle camelCase and snake_case)
                net_gamma = response.get("netGamma", response.get("net_gamma"))
                gamma_buildup_pct = response.get(
                    "gammaBuildup", response.get("gamma_buildup_pct", 0.0)
                )

                if net_gamma is None:
                    logger.debug(f"Missing netGamma in GEX response for {ticker}")
                    if attempt < config.QW_MAX_RETRIES - 1:
                        time.sleep(1)
                        continue
                    return None

                return {
                    "net_gamma": float(net_gamma),
                    "gamma_buildup_pct": (
                        float(gamma_buildup_pct) if gamma_buildup_pct else 0.0
                    ),
                }

            except TimeoutError:
                logger.debug(
                    f"GEX fetch timeout for {ticker} (attempt {attempt + 1}/{config.QW_MAX_RETRIES})"
                )
                if attempt < config.QW_MAX_RETRIES - 1:
                    time.sleep(1)
                    continue
                return None

            except Exception as e:
                logger.debug(
                    f"GEX fetch error for {ticker} (attempt {attempt + 1}): {e}"
                )
                if attempt < config.QW_MAX_RETRIES - 1:
                    time.sleep(1)
                    continue
                return None

        return None

    def _fetch_vanna_from_qw(self, ticker: str) -> Optional[Dict]:
        """
        Call QuantWheel MCP get_vanna_charm tool.
        Returns: {"vanna_regime": str, "bull_bear_ratio": float, "bullish_target": float} or None.
        """
        for attempt in range(config.QW_MAX_RETRIES):
            try:
                response = self._call_mcp_tool(
                    MCP_TOOL_GET_VANNA,
                    {"ticker": ticker},
                    timeout_sec=config.QW_API_TIMEOUT_SEC,
                )

                if response is None:
                    logger.debug(
                        f"Vanna fetch returned None for {ticker} (attempt {attempt + 1})"
                    )
                    if attempt < config.QW_MAX_RETRIES - 1:
                        time.sleep(1)
                        continue
                    return None

                if not isinstance(response, dict):
                    logger.debug(
                        f"Invalid Vanna response type for {ticker}: {type(response)}"
                    )
                    return None

                # Extract from now bucket (tactical, 0-45 DTE)
                now_bucket = response.get("now", {})

                # Get vanna regime and key levels
                vanna_regime = now_bucket.get("vannaRegime", "unknown")
                bull_bear_ratio = now_bucket.get("bullBearRatio", 0.0)
                bullish_target = now_bucket.get("bullDriftTarget", 0.0)

                if not vanna_regime or vanna_regime == "unknown":
                    logger.debug(f"Invalid vanna regime for {ticker}: {vanna_regime}")
                    if attempt < config.QW_MAX_RETRIES - 1:
                        time.sleep(1)
                        continue
                    return None

                return {
                    "vanna_regime": str(vanna_regime),
                    "bull_bear_ratio": (
                        float(bull_bear_ratio) if bull_bear_ratio else 0.0
                    ),
                    "bullish_target": float(bullish_target) if bullish_target else 0.0,
                }

            except TimeoutError:
                logger.debug(
                    f"Vanna fetch timeout for {ticker} (attempt {attempt + 1}/{config.QW_MAX_RETRIES})"
                )
                if attempt < config.QW_MAX_RETRIES - 1:
                    time.sleep(1)
                    continue
                return None

            except Exception as e:
                logger.debug(
                    f"Vanna fetch error for {ticker} (attempt {attempt + 1}): {e}"
                )
                if attempt < config.QW_MAX_RETRIES - 1:
                    time.sleep(1)
                    continue
                return None

        return None

    def _fetch_quote_from_qw(self, ticker: str) -> Optional[Dict]:
        """
        Call QuantWheel MCP get_stock_quote tool.
        Returns: {"price": float, "iv": float} or None on error.
        Note: This returns price only; IV from stock quote may be 0.
        """
        for attempt in range(config.QW_MAX_RETRIES):
            try:
                response = self._call_mcp_tool(
                    MCP_TOOL_GET_QUOTE,
                    {"ticker": ticker},
                    timeout_sec=config.QW_API_TIMEOUT_SEC,
                )

                if response is None:
                    logger.debug(
                        f"Quote fetch returned None for {ticker} (attempt {attempt + 1})"
                    )
                    if attempt < config.QW_MAX_RETRIES - 1:
                        time.sleep(1)
                        continue
                    return None

                if not isinstance(response, dict):
                    logger.debug(
                        f"Invalid quote response type for {ticker}: {type(response)}"
                    )
                    return None

                # Extract price from quote response (handle multiple field names)
                price = response.get("price", response.get("last", response.get("mid")))

                if price is None:
                    logger.debug(f"Missing price in quote response for {ticker}")
                    if attempt < config.QW_MAX_RETRIES - 1:
                        time.sleep(1)
                        continue
                    return None

                # IV is typically not in stock quote response; stock quote only has price
                iv = response.get("iv", 0.0)

                return {
                    "price": float(price),
                    "iv": float(iv) if iv else 0.0,
                }

            except TimeoutError:
                logger.debug(
                    f"Quote fetch timeout for {ticker} (attempt {attempt + 1}/{config.QW_MAX_RETRIES})"
                )
                if attempt < config.QW_MAX_RETRIES - 1:
                    time.sleep(1)
                    continue
                return None

            except Exception as e:
                logger.debug(
                    f"Quote fetch error for {ticker} (attempt {attempt + 1}): {e}"
                )
                if attempt < config.QW_MAX_RETRIES - 1:
                    time.sleep(1)
                    continue
                return None

        return None
