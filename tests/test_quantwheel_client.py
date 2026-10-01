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
