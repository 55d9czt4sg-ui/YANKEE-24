"""Tests for output formatters (CLI, JSON, CSV)."""

import pytest
import json
from output import CLIFormatter, JSONExporter, CSVExporter
from models import Ticker, GEXData, VannaData, Setup, ScanResult


def test_cli_format_returns_string():
    """CLIFormatter produces a string."""
    formatter = CLIFormatter()
    result = ScanResult("2026-10-01T13:35:22Z", ["SPX", "NDX"], 600, 5, [])
    output = formatter.format_table(result)
    assert isinstance(output, str)
    assert "BULLISH DRIFT SCAN" in output


def test_cli_format_includes_summary():
    """CLI output includes summary statistics."""
    formatter = CLIFormatter()
    result = ScanResult("2026-10-01T13:35:22Z", ["SPX", "NDX"], 600, 23, [])
    output = formatter.format_table(result)
    assert "600" in output  # Tickers scanned
    assert "23" in output   # Candidates passed


def test_json_export_valid_json():
    """JSONExporter produces valid JSON string."""
    exporter = JSONExporter()
    result = ScanResult("2026-10-01T13:35:22Z", ["SPX", "NDX"], 600, 5, [])
    output = exporter.export(result)
    parsed = json.loads(output)  # Should not raise
    assert parsed["scan"]["tickers_scanned"] == 600


def test_csv_export_valid_format():
    """CSVExporter produces valid CSV format."""
    exporter = CSVExporter()
    result = ScanResult("2026-10-01T13:35:22Z", ["SPX", "NDX"], 600, 5, [])
    output = exporter.export(result)
    lines = output.strip().split("\n")
    assert len(lines) >= 1  # At least header
    assert "rank" in lines[0].lower()
    assert "ticker" in lines[0].lower()


def test_cli_format_with_candidates():
    """CLI table includes ranked candidates."""
    formatter = CLIFormatter()
    ticker = Ticker("NVDA", 221.82, 18.5, 230.0, 220.0, 222.5)
    gex = GEXData(150.0, 50.7)
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
    result = ScanResult("2026-10-01T13:35:22Z", ["SPX", "NDX"], 600, 1, [setup])
    output = formatter.format_table(result)
    assert "NVDA" in output
    assert "8.2" in output
    assert "PRIME" in output


def test_json_export_with_candidates():
    """JSONExporter includes candidate details."""
    exporter = JSONExporter()
    ticker = Ticker("NVDA", 221.82, 18.5, 230.0, 220.0, 222.5)
    gex = GEXData(150.0, 50.7)
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
    result = ScanResult("2026-10-01T13:35:22Z", ["SPX", "NDX"], 600, 1, [setup])
    output = exporter.export(result)
    parsed = json.loads(output)
    assert len(parsed["candidates"]) == 1
    assert parsed["candidates"][0]["ticker"] == "NVDA"
    assert parsed["candidates"][0]["composite_rank"] == 8.2


def test_csv_export_with_candidates():
    """CSVExporter includes candidate rows."""
    exporter = CSVExporter()
    ticker = Ticker("NVDA", 221.82, 18.5, 230.0, 220.0, 222.5)
    gex = GEXData(150.0, 50.7)
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
    result = ScanResult("2026-10-01T13:35:22Z", ["SPX", "NDX"], 600, 1, [setup])
    output = exporter.export(result)
    lines = output.strip().split("\n")
    assert len(lines) == 2  # Header + 1 candidate
    assert "NVDA" in lines[1]
