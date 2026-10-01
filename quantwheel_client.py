"""QuantWheel API client with caching layer."""

from typing import Optional, Dict, Any, Callable
from models import GEXData, VannaData
import config
import time
import logging

logger = logging.getLogger(__name__)

MCP_TOOL_GET_GEX = "get_gex"
MCP_TOOL_GET_VANNA = "get_vanna_charm"
MCP_TOOL_GET_QUOTE = "get_stock_quote"


class Cache:
    """Simple in-memory cache with TTL."""

    def __init__(self):
        self._cache: Dict[str, tuple[Any, float]] = (
            {}
        )  # key -> (value, expiry_timestamp)
        self.hits = 0
        self.misses = 0

    def set(self, key: str, value: Any, ttl_minutes: int = 5):
        """Store a value with expiry."""
        expiry = time.time() + (ttl_minutes * 60)
        self._cache[key] = (value, expiry)

    def get(self, key: str) -> Optional[Any]:
        """Retrieve value if not expired."""
        if key not in self._cache:
            self.misses += 1
            return None

        value, expiry = self._cache[key]
        if time.time() > expiry:
            del self._cache[key]
            self.misses += 1
            return None

        self.hits += 1
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
        no_cache: bool = False,
        mcp_tool_caller: Optional[Callable[[str, Dict[str, Any]], Any]] = None,
    ):
        self.cache = Cache()
        self.cache_ttl_minutes = cache_ttl_minutes
        self.call_count = 0  # Track API calls for stats
        self.mcp_enabled = mcp_enabled  # Toggle for testing/mocking
        self.no_cache = no_cache
        self.mcp_tool_caller = mcp_tool_caller

    def _call_mcp_tool(
        self,
        tool_name: str,
        params: Dict[str, Any],
        timeout_sec: int = config.QW_API_TIMEOUT_SEC,
    ) -> Optional[Dict[str, Any]]:
        """Call an MCP tool through the supplied MCP client."""
        if not self.mcp_enabled:
            logger.debug(f"MCP disabled, skipping tool call: {tool_name}")
            return None

        if self.mcp_tool_caller is None:
            logger.error(
                "QuantWheel MCP transport is not configured; provide an MCP tool caller"
            )
            return None

        try:
            response = self.mcp_tool_caller(tool_name, params)
            if isinstance(response, dict):
                return response
            logger.debug(f"MCP tool {tool_name} returned non-dict: {type(response)}")
        except Exception as e:
            logger.debug(f"MCP call error for {tool_name}: {e}")
        return None

    def get_gex(self, ticker: str, expiration: str) -> Optional[GEXData]:
        """Fetch GEX (gamma exposure) data for ticker + expiration."""
        cache_key = f"gex:{ticker}:{expiration}"

        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        # Fetch from QuantWheel
        try:
            data = self._fetch_gex_from_qw(ticker, expiration)
            if data is None:
                return None

            gex_data = GEXData(
                net_gamma=data["net_gamma"],
                gamma_buildup_pct=data.get("gamma_buildup_pct", 0.0),
                put_wall=data.get("put_wall"),
                call_wall=data.get("call_wall"),
            )
            self._cache_set(cache_key, gex_data)
            self.call_count += 1
            return gex_data
        except Exception as e:
            print(f"⚠️  GEX fetch failed for {ticker}: {e}")
            return None

    def get_vanna_charm(self, ticker: str) -> Optional[VannaData]:
        """Fetch Vanna & Charm data for ticker."""
        cache_key = f"vanna:{ticker}"

        # Try cache first
        cached = self._cache_get(cache_key)
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
            self._cache_set(cache_key, vanna_data)
            self.call_count += 1
            return vanna_data
        except Exception as e:
            print(f"⚠️  Vanna fetch failed for {ticker}: {e}")
            return None

    def get_quote_data(self, ticker: str) -> Optional[Dict[str, Optional[float]]]:
        """Fetch price, IV, and historical IV averages when provided."""
        cache_key = f"quote:{ticker}"

        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        try:
            data = self._fetch_quote_from_qw(ticker)
            if data is None:
                return None

            self._cache_set(cache_key, data)
            self.call_count += 1
            return data
        except Exception as e:
            print(f"⚠️  Quote fetch failed for {ticker}: {e}")
            return None

    def get_quote(self, ticker: str) -> Optional[tuple[float, Optional[float]]]:
        """Fetch current price and IV. Missing IV remains None."""
        data = self.get_quote_data(ticker)
        if data is None:
            return None
        return data["price"], data["iv"]

    def _cache_get(self, key: str) -> Optional[Any]:
        return None if self.no_cache else self.cache.get(key)

    def _cache_set(self, key: str, value: Any):
        if not self.no_cache:
            self.cache.set(key, value, self.cache_ttl_minutes)

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
            "hits": self.cache.hits,
            "misses": self.cache.misses,
            "cache_hit_rate": (
                self.cache.hits / (self.cache.hits + self.cache.misses)
                if self.cache.hits + self.cache.misses
                else 0.0
            ),
            "oldest_cache_age_minutes": max(
                (
                    max(
                        0,
                        time.time()
                        - (expiry - self.cache_ttl_minutes * 60),
                    )
                    / 60
                    for _, expiry in self.cache._cache.values()
                    if time.time() <= expiry
                ),
                default=0,
            ),
        }

    # Private methods (MCP tool integration)

    def _fetch_gex_from_qw(self, ticker: str, expiration: str) -> Optional[Dict]:
        """
        Call QuantWheel MCP get_gex tool.
        Returns gamma values and optional walls, or None on error.
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
                put_wall = response.get("putWall", response.get("put_wall"))
                call_wall = response.get("callWall", response.get("call_wall"))

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
                    "put_wall": float(put_wall) if put_wall is not None else None,
                    "call_wall": float(call_wall) if call_wall is not None else None,
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
        Returns the available price/IV fields; missing IV values remain None.
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

                iv = response.get("iv", response.get("impliedVolatility"))
                iv_3day_avg = response.get(
                    "iv_3day_avg", response.get("iv3DayAvg")
                )
                iv_5day_avg = response.get(
                    "iv_5day_avg", response.get("iv5DayAvg")
                )

                return {
                    "price": float(price),
                    "iv": float(iv) if iv is not None else None,
                    "iv_3day_avg": (
                        float(iv_3day_avg) if iv_3day_avg is not None else None
                    ),
                    "iv_5day_avg": (
                        float(iv_5day_avg) if iv_5day_avg is not None else None
                    ),
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
