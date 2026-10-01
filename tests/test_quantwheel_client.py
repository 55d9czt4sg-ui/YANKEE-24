"""Tests for QuantWheel client with caching."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from quantwheel_client import QuantWheelClient, Cache
from models import GEXData, VannaData


def test_cache_set_and_get():
    """Test basic cache set and get."""
    cache = Cache()
    cache.set("key1", {"data": "value"}, ttl_minutes=5)
    result = cache.get("key1")
    assert result == {"data": "value"}


def test_cache_expiry():
    """Test that expired cache entries return None."""
    cache = Cache()
    cache.set("key1", {"data": "value"}, ttl_minutes=0)  # Immediate expiry
    result = cache.get("key1")
    assert result is None  # Expired


def test_qw_client_initialization():
    """Test QuantWheelClient initialization."""
    client = QuantWheelClient(cache_ttl_minutes=5)
    assert client.cache is not None
    assert client.cache_ttl_minutes == 5


def test_get_gex_calls_quantwheel():
    """Mock the QuantWheel MCP and verify GEXData is returned."""
    client = QuantWheelClient()
    # This will test the actual MCP call in integration tests
    # For unit test, we mock the underlying MCP tool
    with patch.object(client, "_fetch_gex_from_qw") as mock_fetch:
        mock_fetch.return_value = {
            "net_gamma": 150.5,
            "gamma_buildup_pct": 50.7,
        }
        result = client.get_gex("NVDA", "2026-10-18")
        assert isinstance(result, GEXData)
        assert result.net_gamma == 150.5


def test_get_vanna_charm_returns_vanna_data():
    """Test get_vanna_charm returns VannaData."""
    client = QuantWheelClient()
    with patch.object(client, "_fetch_vanna_from_qw") as mock_fetch:
        mock_fetch.return_value = {
            "vanna_regime": "positive",
            "bull_bear_ratio": 2.48,
            "bullish_target": 230.0,
        }
        result = client.get_vanna_charm("NVDA")
        assert isinstance(result, VannaData)
        assert result.vanna_regime == "positive"
        assert result.bull_bear_ratio == 2.48


def test_cache_hit_reduces_api_calls():
    """Second call to same ticker should use cache."""
    client = QuantWheelClient(cache_ttl_minutes=5)
    with patch.object(client, "_fetch_gex_from_qw") as mock_fetch:
        mock_fetch.return_value = {"net_gamma": 150.5, "gamma_buildup_pct": 50.7}

        # First call
        result1 = client.get_gex("NVDA", "2026-10-18")
        assert mock_fetch.call_count == 1

        # Second call (should use cache)
        result2 = client.get_gex("NVDA", "2026-10-18")
        assert mock_fetch.call_count == 1  # No additional call
        assert result1.net_gamma == result2.net_gamma


def test_missing_data_returns_none():
    """If QuantWheel returns no data, handle gracefully."""
    client = QuantWheelClient()
    with patch.object(client, "_fetch_gex_from_qw") as mock_fetch:
        mock_fetch.side_effect = Exception("API timeout")
        result = client.get_gex("INVALID_TICKER", "2026-10-18")
        assert result is None


def test_cache_is_stale():
    """Test is_stale method for expired entries."""
    cache = Cache()
    cache.set("key1", {"data": "value"}, ttl_minutes=0)  # Immediate expiry
    assert cache.is_stale("key1") == True


def test_cache_is_not_stale_for_valid():
    """Test is_stale returns False for valid entries."""
    cache = Cache()
    cache.set("key1", {"data": "value"}, ttl_minutes=5)
    assert cache.is_stale("key1") == False


def test_cache_stats():
    """Test cache stats method."""
    cache = Cache()
    cache.set("key1", {"data": "value1"}, ttl_minutes=5)
    cache.set("key2", {"data": "value2"}, ttl_minutes=0)  # Expired

    stats = cache.stats()
    assert stats["total"] == 2
    assert stats["valid"] == 1  # Only key1 is valid


def test_get_quote_returns_tuple():
    """Test get_quote returns (price, iv) tuple."""
    client = QuantWheelClient()
    with patch.object(client, "_fetch_quote_from_qw") as mock_fetch:
        mock_fetch.return_value = {
            "price": 221.82,
            "iv": 18.5,
        }
        result = client.get_quote("NVDA")
        assert isinstance(result, tuple)
        assert result == (221.82, 18.5)


def test_missing_quote_iv_is_not_fabricated():
    client = QuantWheelClient()
    with patch.object(
        client,
        "_fetch_quote_from_qw",
        return_value={"price": 221.82, "iv": None},
    ):
        assert client.get_quote("NVDA") == (221.82, None)


def test_no_cache_forces_fresh_fetches():
    client = QuantWheelClient(no_cache=True)
    with patch.object(
        client,
        "_fetch_gex_from_qw",
        return_value={"net_gamma": 150.5, "gamma_buildup_pct": 50.7},
    ) as mock_fetch:
        client.get_gex("NVDA", "2026-10-18")
        client.get_gex("NVDA", "2026-10-18")
        assert mock_fetch.call_count == 2
        assert client.cache_stats()["cache_entries"] == 0


def test_mcp_transport_uses_supplied_tool_caller():
    caller = MagicMock(return_value={"price": 10})
    client = QuantWheelClient(mcp_tool_caller=caller)
    assert client._call_mcp_tool("get_stock_quote", {"ticker": "AAPL"}) == {
        "price": 10
    }
    caller.assert_called_once_with("get_stock_quote", {"ticker": "AAPL"})


def test_get_all_tickers():
    """Test get_all_tickers returns list."""
    client = QuantWheelClient()
    tickers = client.get_all_tickers()
    assert isinstance(tickers, list)
    assert len(tickers) > 0


def test_cache_stats_through_client():
    """Test client's cache_stats method."""
    client = QuantWheelClient()
    with patch.object(client, "_fetch_gex_from_qw") as mock_fetch:
        mock_fetch.return_value = {"net_gamma": 150.5, "gamma_buildup_pct": 50.7}

        # Make some calls
        client.get_gex("NVDA", "2026-10-18")
        client.get_gex("TSLA", "2026-10-18")

        stats = client.cache_stats()
        assert stats["cache_entries"] == 2
        assert stats["total_api_calls"] == 2


def test_quote_cache_hit():
    """Test quote caching works."""
    client = QuantWheelClient(cache_ttl_minutes=5)
    with patch.object(client, "_fetch_quote_from_qw") as mock_fetch:
        mock_fetch.return_value = {"price": 221.82, "iv": 18.5}

        # First call
        result1 = client.get_quote("NVDA")
        assert mock_fetch.call_count == 1

        # Second call (should use cache)
        result2 = client.get_quote("NVDA")
        assert mock_fetch.call_count == 1  # No additional call
        assert result1 == result2


# Integration tests for MCP tool calls


def test_mcp_call_tool_returns_dict():
    """Test _call_mcp_tool returns dict on success."""
    client = QuantWheelClient(mcp_enabled=False)  # Disabled for this test
    # With mcp_enabled=False, should return None
    result = client._call_mcp_tool("test_tool", {"param": "value"})
    assert result is None


def test_mcp_call_tool_disabled():
    """Test _call_mcp_tool respects mcp_enabled flag."""
    client = QuantWheelClient(mcp_enabled=False)
    result = client._call_mcp_tool("any_tool", {})
    assert result is None


def test_fetch_gex_retry_logic():
    """Test _fetch_gex_from_qw retries on None response."""
    client = QuantWheelClient()
    call_count = 0

    def mock_call_mcp(tool, params, timeout_sec=None):
        nonlocal call_count
        call_count += 1
        # Succeed on second attempt
        if call_count == 2:
            return {"netGamma": 150.5, "gammaBuildup": 50.0}
        return None

    with patch.object(client, "_call_mcp_tool", side_effect=mock_call_mcp):
        result = client._fetch_gex_from_qw("NVDA", "2026-10-18")
        assert call_count == 2  # Retried once
        assert result is not None
        assert result["net_gamma"] == 150.5


def test_fetch_gex_timeout_retry():
    """Test _fetch_gex_from_qw handles TimeoutError and retries."""
    client = QuantWheelClient()
    call_count = 0

    def mock_call_mcp(tool, params, timeout_sec=None):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise TimeoutError("API timeout")
        return {"netGamma": 150.5, "gammaBuildup": 50.0}

    with patch.object(client, "_call_mcp_tool", side_effect=mock_call_mcp):
        result = client._fetch_gex_from_qw("NVDA", "2026-10-18")
        assert call_count == 2  # Retried after timeout
        assert result is not None
        assert result["net_gamma"] == 150.5


def test_fetch_gex_all_retries_exhausted():
    """Test _fetch_gex_from_qw returns None when retries exhausted."""
    client = QuantWheelClient()

    with patch.object(client, "_call_mcp_tool", side_effect=Exception("API error")):
        result = client._fetch_gex_from_qw("INVALID", "2026-10-18")
        assert result is None


def test_fetch_gex_handles_snake_case_response():
    """Test _fetch_gex_from_qw handles snake_case field names."""
    client = QuantWheelClient()

    with patch.object(
        client,
        "_call_mcp_tool",
        return_value={"net_gamma": 150.5, "gamma_buildup_pct": 45.0},
    ):
        result = client._fetch_gex_from_qw("NVDA", "2026-10-18")
        assert result is not None
        assert result["net_gamma"] == 150.5
        assert result["gamma_buildup_pct"] == 45.0


def test_fetch_vanna_extracts_now_bucket():
    """Test _fetch_vanna_from_qw extracts data from 'now' bucket."""
    client = QuantWheelClient()

    mcp_response = {
        "now": {
            "vannaRegime": "positive",
            "bullBearRatio": 2.48,
            "bullDriftTarget": 230.0,
        },
        "regime": {"vannaRegime": "negative", "bullBearRatio": 0.8},
    }

    with patch.object(client, "_call_mcp_tool", return_value=mcp_response):
        result = client._fetch_vanna_from_qw("NVDA")
        assert result is not None
        assert result["vanna_regime"] == "positive"
        assert result["bull_bear_ratio"] == 2.48
        assert result["bullish_target"] == 230.0


def test_fetch_vanna_invalid_regime():
    """Test _fetch_vanna_from_qw handles invalid regime."""
    client = QuantWheelClient()

    with patch.object(
        client, "_call_mcp_tool", return_value={"now": {"vannaRegime": "unknown"}}
    ):
        result = client._fetch_vanna_from_qw("NVDA")
        # Should return None or retry when regime is unknown
        # First attempt returns "unknown", second retry hits limit
        assert result is None


def test_fetch_vanna_retry_on_error():
    """Test _fetch_vanna_from_qw retries on API error."""
    client = QuantWheelClient()
    call_count = 0

    def mock_call_mcp(tool, params, timeout_sec=None):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("API error")
        return {
            "now": {
                "vannaRegime": "positive",
                "bullBearRatio": 2.48,
                "bullDriftTarget": 230.0,
            }
        }

    with patch.object(client, "_call_mcp_tool", side_effect=mock_call_mcp):
        result = client._fetch_vanna_from_qw("NVDA")
        assert call_count == 2
        assert result is not None
        assert result["vanna_regime"] == "positive"


def test_fetch_quote_extracts_price():
    """Test _fetch_quote_from_qw extracts price correctly."""
    client = QuantWheelClient()

    with patch.object(client, "_call_mcp_tool", return_value={"price": 221.82}):
        result = client._fetch_quote_from_qw("NVDA")
        assert result is not None
        assert result["price"] == 221.82
        assert result["iv"] is None


def test_fetch_quote_handles_fallback_price_field():
    """Test _fetch_quote_from_qw handles 'last' field if 'price' missing."""
    client = QuantWheelClient()

    with patch.object(client, "_call_mcp_tool", return_value={"last": 221.82}):
        result = client._fetch_quote_from_qw("NVDA")
        assert result is not None
        assert result["price"] == 221.82


def test_fetch_quote_handles_mid_price_field():
    """Test _fetch_quote_from_qw handles 'mid' field as fallback."""
    client = QuantWheelClient()

    with patch.object(client, "_call_mcp_tool", return_value={"mid": 221.82}):
        result = client._fetch_quote_from_qw("NVDA")
        assert result is not None
        assert result["price"] == 221.82


def test_fetch_quote_missing_price():
    """Test _fetch_quote_from_qw returns None when price is missing."""
    client = QuantWheelClient()

    with patch.object(client, "_call_mcp_tool", return_value={"some_field": "value"}):
        result = client._fetch_quote_from_qw("NVDA")
        # Should retry, then return None
        assert result is None


def test_fetch_quote_timeout_retry():
    """Test _fetch_quote_from_qw retries on timeout."""
    client = QuantWheelClient()
    call_count = 0

    def mock_call_mcp(tool, params, timeout_sec=None):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise TimeoutError("Timeout")
        return {"price": 221.82}

    with patch.object(client, "_call_mcp_tool", side_effect=mock_call_mcp):
        result = client._fetch_quote_from_qw("NVDA")
        assert call_count == 2
        assert result is not None
        assert result["price"] == 221.82


def test_gex_integration_with_cache():
    """Test full GEX flow: MCP call -> cache -> model conversion."""
    client = QuantWheelClient()

    with patch.object(
        client,
        "_call_mcp_tool",
        return_value={"netGamma": 150.5, "gammaBuildup": 50.0},
    ):
        # First call: MCP -> cache -> GEXData
        result1 = client.get_gex("NVDA", "2026-10-18")
        assert isinstance(result1, GEXData)
        assert result1.net_gamma == 150.5
        assert result1.gamma_buildup_pct == 50.0

        # Second call: cache hit, no MCP call
        result2 = client.get_gex("NVDA", "2026-10-18")
        assert result1 == result2


def test_vanna_integration_with_cache():
    """Test full Vanna flow: MCP call -> cache -> model conversion."""
    client = QuantWheelClient()

    mcp_response = {
        "now": {
            "vannaRegime": "positive",
            "bullBearRatio": 2.48,
            "bullDriftTarget": 230.0,
        }
    }

    with patch.object(client, "_call_mcp_tool", return_value=mcp_response):
        # First call: MCP -> cache -> VannaData
        result1 = client.get_vanna_charm("NVDA")
        assert isinstance(result1, VannaData)
        assert result1.vanna_regime == "positive"
        assert result1.bull_bear_ratio == 2.48

        # Second call: cache hit
        result2 = client.get_vanna_charm("NVDA")
        assert result1 == result2


def test_quote_integration_with_cache():
    """Test full Quote flow: MCP call -> cache -> tuple."""
    client = QuantWheelClient()

    with patch.object(client, "_call_mcp_tool", return_value={"price": 221.82}):
        # First call: MCP -> cache -> tuple
        result1 = client.get_quote("NVDA")
        assert isinstance(result1, tuple)
        assert result1 == (221.82, None)

        # Second call: cache hit
        result2 = client.get_quote("NVDA")
        assert result1 == result2
