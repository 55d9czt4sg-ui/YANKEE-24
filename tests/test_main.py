"""Integration tests for main.py CLI orchestration."""

import pytest
import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from main import parse_args, load_tickers, run_scan
from models import ScanResult


def test_parse_args_default():
    """Default args with no flags."""
    sys.argv = ["main.py"]
    args = parse_args()
    assert args.watchlist is None
    assert args.export_json is False
    assert args.export_csv is False
    assert args.top_n is None
    assert args.quiet is False


def test_parse_args_export_json():
    """--export-json flag."""
    sys.argv = ["main.py", "--export-json"]
    args = parse_args()
    assert args.export_json is True


def test_parse_args_export_csv():
    """--export-csv flag."""
    sys.argv = ["main.py", "--export-csv"]
    args = parse_args()
    assert args.export_csv is True


def test_parse_args_top_n():
    """--top-n N flag."""
    sys.argv = ["main.py", "--top-n", "10"]
    args = parse_args()
    assert args.top_n == 10


def test_parse_args_min_gamma_buildup():
    """--min-gamma-buildup N flag."""
    sys.argv = ["main.py", "--min-gamma-buildup", "200"]
    args = parse_args()
    assert args.min_gamma_buildup == 200.0


def test_parse_args_min_dealer_score():
    """--min-dealer-score N flag."""
    sys.argv = ["main.py", "--min-dealer-score", "80"]
    args = parse_args()
    assert args.min_dealer_score == 80


def test_parse_args_max_price():
    """--max-price N flag."""
    sys.argv = ["main.py", "--max-price", "300"]
    args = parse_args()
    assert args.max_price == 300.0


def test_parse_args_min_bull_bear():
    """--min-bull-bear N flag."""
    sys.argv = ["main.py", "--min-bull-bear", "2.0"]
    args = parse_args()
    assert args.min_bull_bear == 2.0


def test_parse_args_quiet():
    """--quiet flag suppresses output."""
    sys.argv = ["main.py", "--quiet"]
    args = parse_args()
    assert args.quiet is True


def test_parse_args_debug():
    """--debug flag enables verbose logging."""
    sys.argv = ["main.py", "--debug"]
    args = parse_args()
    assert args.debug is True


def test_parse_args_no_cache():
    """--no-cache flag skips caching."""
    sys.argv = ["main.py", "--no-cache"]
    args = parse_args()
    assert args.no_cache is True


def test_parse_args_cache_ttl():
    """--cache-ttl N flag."""
    sys.argv = ["main.py", "--cache-ttl", "10"]
    args = parse_args()
    assert args.cache_ttl == 10


def test_load_tickers_default():
    """Load default SPX+NDX tickers when no watchlist."""
    tickers = load_tickers(None)
    assert isinstance(tickers, list)
    assert len(tickers) > 0
    # Check for some known tickers
    assert "MSFT" in tickers or "AAPL" in tickers


def test_load_tickers_from_txt():
    """Load tickers from .txt file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("NVDA\nTSLA\nAMZN\n")
        f.flush()
        tickers = load_tickers(f.name)
        assert tickers == ["NVDA", "TSLA", "AMZN"]
        Path(f.name).unlink()


def test_load_tickers_from_json():
    """Load tickers from .json file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(["NVDA", "TSLA", "AMZN"], f)
        f.flush()
        tickers = load_tickers(f.name)
        assert tickers == ["NVDA", "TSLA", "AMZN"]
        Path(f.name).unlink()


def test_run_scan_returns_scan_result():
    """run_scan returns a ScanResult object."""
    args = MagicMock()
    args.cache_ttl = 5
    args.debug = False
    args.quiet = False
    args.min_gamma_buildup = None
    args.min_dealer_score = None
    args.max_price = None
    args.min_bull_bear = None
    args.top_n = None

    with patch("main.QuantWheelClient") as mock_qw:
        mock_client = MagicMock()
        mock_qw.return_value = mock_client
        mock_client.get_quote.return_value = None  # Skip tickers

        result = run_scan(["NVDA"], args)
        assert isinstance(result, ScanResult)
        assert result.tickers_scanned == 1


def test_parse_args_help():
    """--help flag displays help text."""
    sys.argv = ["main.py", "--help"]
    with pytest.raises(SystemExit):
        parse_args()
