"""Integration tests for full pipeline: data fetch -> filter -> score -> rank -> output."""

import json
import csv
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

from models import Ticker, GEXData, VannaData, Setup, ScanResult
from screener import ScreeningEngine, DealerScorer
from output import CLIFormatter, JSONExporter, CSVExporter
import main


class TestFullScanPipeline:
    """Test 1: Full pipeline with mock QuantWheel data."""

    @patch("main.QuantWheelClient")
    def test_full_scan_pipeline(self, mock_client_class):
        """Test complete scan: fetch -> filter -> score -> rank -> output."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        test_data = {
            "AAPL": {"quote": (150.0, 18.0), "gex": 125.5, "vanna": 2.5},
            "MSFT": {"quote": (400.0, 16.0), "gex": 95.3, "vanna": 1.8},
            "NVDA": {"quote": (880.0, 22.0), "gex": 145.2, "vanna": 3.2},
            "TSLA": {"quote": (250.0, 24.0), "gex": 155.0, "vanna": 2.1},
            "META": {"quote": (500.0, 20.0), "gex": 105.5, "vanna": 2.8},
            "GOOGL": {"quote": (140.0, 14.0), "gex": -50.0, "vanna": -1.5},
            "AMZN": {"quote": (190.0, 17.0), "gex": 85.0, "vanna": -2.0},
            "NFLX": {"quote": (220.0, 19.0), "gex": 75.0, "vanna": 1.5},
            "INTC": {"quote": (50.0, 28.0), "gex": 30.0, "vanna": 0.5},
            "AMD": {"quote": (200.0, 21.0), "gex": 35.0, "vanna": 1.0},
        }

        def mock_get_quote_data(ticker):
            quote = test_data.get(ticker, {}).get("quote")
            if quote is None:
                return None
            return {
                "price": quote[0],
                "iv": quote[1],
                "iv_3day_avg": quote[1] * 1.1,
                "iv_5day_avg": quote[1] * 1.15,
            }

        def mock_get_gex(ticker, expiration):
            if ticker in test_data:
                buildup = test_data[ticker]["gex"]
                return GEXData(
                    net_gamma=buildup * 1000,
                    gamma_buildup_pct=buildup,
                    put_wall=test_data[ticker]["quote"][0] * 0.99,
                    call_wall=test_data[ticker]["quote"][0] * 1.05,
                )
            return None

        def mock_get_vanna_charm(ticker):
            if ticker in test_data:
                bb_ratio = test_data[ticker]["vanna"]
                regime = "positive" if bb_ratio > 0 else "negative"
                return VannaData(
                    vanna_regime=regime,
                    bull_bear_ratio=bb_ratio,
                    bullish_target=test_data[ticker]["quote"][0] * 1.1,
                )
            return None

        mock_client.get_quote_data.side_effect = mock_get_quote_data
        mock_client.get_gex.side_effect = mock_get_gex
        mock_client.get_vanna_charm.side_effect = mock_get_vanna_charm

        args = Mock()
        args.cache_ttl = 60
        args.no_cache = False
        args.debug = False
        args.min_gamma_buildup = None
        args.min_dealer_score = None
        args.max_price = None
        args.min_bull_bear = None
        args.top_n = None
        args.quiet = True
        mock_client.cache_stats.return_value = {
            "cache_hit_rate": 0.0,
            "oldest_cache_age_minutes": 0,
        }

        tickers = list(test_data.keys())
        result = main.run_scan(tickers, args)

        assert result.tickers_scanned == 10
        assert result.candidates_passed == 8
        assert {setup.ticker.name for setup in result.ranked_list} == {
            "AAPL", "MSFT", "NVDA", "TSLA", "META", "NFLX", "INTC", "AMD"
        }
        ranks = {setup.ticker.name: setup.composite_rank for setup in result.ranked_list}
        assert ranks["NVDA"] > ranks["AAPL"]
        assert result.ranked_list == sorted(
            result.ranked_list, key=lambda setup: setup.composite_rank, reverse=True
        )


class TestCLIIntegration:
    """Test 2: CLI full workflow with file I/O."""

    @patch("main.QuantWheelClient")
    def test_cli_full_workflow(self, mock_client_class):
        """Test CLI with watchlist file and parsed output."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        prices = {
            "AAPL": (150.0, 18.0),
            "MSFT": (400.0, 16.0),
            "NVDA": (880.0, 22.0),
            "TSLA": (250.0, 24.0),
            "META": (500.0, 20.0),
        }

        mock_client.get_quote_data.side_effect = lambda t: (
            {
                "price": quote[0],
                "iv": quote[1],
                "iv_3day_avg": quote[1] * 1.1,
                "iv_5day_avg": quote[1] * 1.15,
            }
            if (quote := prices.get(t))
            else None
        )
        mock_client.get_gex.side_effect = lambda t, e: (
            GEXData(
                net_gamma=100000,
                gamma_buildup_pct=100,
                put_wall=prices[t][0] * 0.99,
            )
            if t in prices
            else None
        )
        mock_client.get_vanna_charm.side_effect = lambda t: (
            VannaData(vanna_regime="positive", bull_bear_ratio=2.5, bullish_target=1000)
            if t in prices
            else None
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("AAPL\nMSFT\nNVDA\nTSLA\nMETA\n")
            watchlist_path = f.name

        try:
            args = Mock()
            args.watchlist = watchlist_path
            args.cache_ttl = 60
            args.no_cache = False
            args.debug = False
            args.min_gamma_buildup = None
            args.min_dealer_score = None
            args.max_price = None
            args.min_bull_bear = None
            args.top_n = 3
            args.quiet = True
            mock_client.cache_stats.return_value = {
                "cache_hit_rate": 0.0,
                "oldest_cache_age_minutes": 0,
            }

            tickers = main.load_tickers(watchlist_path)
            assert len(tickers) == 5
            assert "AAPL" in tickers

            result = main.run_scan(tickers, args)
            assert result.tickers_scanned == 5
        finally:
            Path(watchlist_path).unlink()


class TestExportPipeline:
    """Test 3: Export to JSON and CSV files."""

    def test_export_pipeline(self):
        """Test JSON and CSV export with file validation."""
        setups = []
        for i in range(3):
            ticker = Ticker(
                name=f"TEST{i}",
                current_price=100.0 + i * 50,
                current_iv=20.0 + i * 2,
                bullish_target=120.0 + i * 50,
                put_wall=80.0 + i * 50,
                call_wall=120.0 + i * 50,
            )
            gex = GEXData(
                net_gamma=(100.0 + i * 25) * 1000, gamma_buildup_pct=100.0 + i * 25
            )
            vanna = VannaData(
                vanna_regime="positive",
                bullish_target=120.0 + i * 50,
                bull_bear_ratio=2.5 + i * 0.1,
            )
            setup = Setup(
                ticker=ticker,
                gex=gex,
                vanna=vanna,
                filters_passed={
                    "positive_gamma": True,
                    "positive_vanna": True,
                    "iv_dropping": True,
                    "put_wall_proximity": True,
                    "dte_range": True,
                    "bullish_drift": True,
                },
                composite_rank=100.0 - i * 20,
                status="EXPLOSIVE" if i == 0 else "HOT",
                trade_recommendation="BUY" if i < 2 else "HOLD",
            )
            setups.append(setup)

        result = ScanResult(
            timestamp="2026-10-01T14:30:00Z",
            universe=["TEST"],
            tickers_scanned=3,
            candidates_passed=3,
            ranked_list=setups,
            data_freshness_minutes=2,
            cache_hit_rate=0.85,
        )

        # Export JSON
        json_exporter = JSONExporter()
        json_str = json_exporter.export(result)
        json_data = json.loads(json_str)
        assert json_data["scan"]["tickers_scanned"] == 3
        assert json_data["scan"]["candidates_passed"] == 3
        assert len(json_data["candidates"]) == 3

        # Export CSV
        csv_exporter = CSVExporter()
        csv_str = csv_exporter.export(result)
        csv_rows = list(csv.DictReader(csv_str.strip().split("\n")))
        assert len(csv_rows) == 3
        assert csv_rows[0]["ticker"] == "TEST0"


class TestAllConditionsTogether:
    """Test 4: All 6 filtering conditions applied together."""

    def test_all_conditions_together(self):
        """Test that all 6 conditions are checked together."""
        engine = ScreeningEngine()

        test_cases = [
            {
                "positive_gamma": True,
                "positive_vanna": True,
                "iv_dropping": True,
                "put_wall_proximity": True,
                "dte_range": True,
                "bullish_drift": True,
            },
            {
                "positive_gamma": False,
                "positive_vanna": True,
                "iv_dropping": True,
                "put_wall_proximity": True,
                "dte_range": True,
                "bullish_drift": True,
            },
            {
                "positive_gamma": True,
                "positive_vanna": False,
                "iv_dropping": True,
                "put_wall_proximity": True,
                "dte_range": True,
                "bullish_drift": True,
            },
        ]

        for test_case in test_cases:
            all_pass = engine.apply_filter_dict(test_case)
            if test_case == test_cases[0]:
                assert all_pass
            else:
                assert not all_pass


class TestScoringConsistency:
    """Test 5: Scoring consistency (deterministic)."""

    def test_scoring_is_consistent(self):
        """Test that same candidate scores identically."""
        scorer = DealerScorer()

        results_scores = []
        for _ in range(100):
            score = scorer.calculate_dealer_score(
                has_pos_gamma=True,
                has_pos_vanna=True,
                is_iv_dropping=True,
                bull_bear_ratio=2.5,
                has_bullish_drift=True,
            )
            results_scores.append(score)

        assert len(set(results_scores)) == 1
        assert results_scores[0] > 0


class TestErrorResilience:
    """Test 6: Scan handles missing data gracefully."""

    @patch("main.QuantWheelClient")
    def test_scan_handles_missing_data(self, mock_client_class):
        """Test that scan completes even with missing data."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        def mock_get_quote(ticker):
            return None if ticker == "NOGEX" else (150.0, 18.0)

        def mock_get_gex(ticker, expiration):
            return (
                None
                if ticker == "NOGEX"
                else GEXData(net_gamma=100000, gamma_buildup_pct=100)
            )

        def mock_get_vanna_charm(ticker):
            return (
                None
                if ticker == "NOVANNA"
                else VannaData(
                    vanna_regime="positive", bull_bear_ratio=2.5, bullish_target=200
                )
            )

        mock_client.get_quote.side_effect = mock_get_quote
        mock_client.get_gex.side_effect = mock_get_gex
        mock_client.get_vanna_charm.side_effect = mock_get_vanna_charm

        args = Mock()
        args.cache_ttl = 60
        args.debug = False
        args.min_gamma_buildup = None
        args.min_dealer_score = None
        args.max_price = None
        args.min_bull_bear = None
        args.top_n = None
        args.quiet = True

        tickers = ["AAPL", "NOGEX", "NOVANNA", "MSFT"]
        result = main.run_scan(tickers, args)

        assert result.tickers_scanned == 4
        # Only complete tickers should be in results
        assert all(s.ticker.name in ["AAPL", "MSFT"] for s in result.ranked_list)


class TestOutputValidation:
    """Test 7: All output formats are valid."""

    def test_all_outputs_are_valid(self):
        """Test CLI, JSON, and CSV output validity."""
        ticker = Ticker(
            name="TEST",
            current_price=100.0,
            current_iv=20.0,
            bullish_target=120.0,
            put_wall=80.0,
            call_wall=120.0,
        )
        gex = GEXData(net_gamma=100000, gamma_buildup_pct=100.0)
        vanna = VannaData(
            vanna_regime="positive", bullish_target=120.0, bull_bear_ratio=2.5
        )
        setup = Setup(
            ticker=ticker,
            gex=gex,
            vanna=vanna,
            filters_passed={
                "positive_gamma": True,
                "positive_vanna": True,
                "iv_dropping": True,
                "put_wall_proximity": True,
                "dte_range": True,
                "bullish_drift": True,
            },
            composite_rank=95.0,
            status="EXPLOSIVE",
            trade_recommendation="BUY",
        )

        result = ScanResult(
            timestamp="2026-10-01T14:30:00Z",
            universe=["TEST"],
            tickers_scanned=1,
            candidates_passed=1,
            ranked_list=[setup],
            data_freshness_minutes=2,
            cache_hit_rate=0.85,
        )

        # CLI
        cli_formatter = CLIFormatter()
        cli_output = cli_formatter.format_table(result)
        assert isinstance(cli_output, str)
        assert "TEST" in cli_output

        # JSON
        json_exporter = JSONExporter()
        json_output = json_exporter.export(result)
        json_data = json.loads(json_output)
        assert json_data["scan"]["candidates_passed"] == 1

        # CSV
        csv_exporter = CSVExporter()
        csv_output = csv_exporter.export(result)
        csv_rows = list(csv.DictReader(csv_output.strip().split("\n")))
        assert len(csv_rows) == 1


class TestEdgeCases:
    """Test 8: Edge cases and boundary conditions."""

    def test_empty_results(self):
        """Test scan with zero candidates."""
        result = ScanResult(
            timestamp="2026-10-01T14:30:00Z",
            universe=["TEST"],
            tickers_scanned=10,
            candidates_passed=0,
            ranked_list=[],
            data_freshness_minutes=2,
            cache_hit_rate=0.85,
        )

        cli_formatter = CLIFormatter()
        json_exporter = JSONExporter()
        csv_exporter = CSVExporter()

        cli_output = cli_formatter.format_table(result)
        assert isinstance(cli_output, str)

        json_output = json_exporter.export(result)
        json_data = json.loads(json_output)
        assert json_data["scan"]["candidates_passed"] == 0

        csv_output = csv_exporter.export(result)
        if csv_output.strip():
            csv_rows = list(csv.DictReader(csv_output.strip().split("\n")))
            assert len(csv_rows) == 0

    def test_large_candidate_set(self):
        """Test results with many candidates."""
        setups = []
        for i in range(50):
            ticker = Ticker(
                name=f"TEST{i:02d}",
                current_price=100.0 + i,
                current_iv=20.0 + (i % 5),
                bullish_target=120.0 + i,
                put_wall=80.0 + i,
                call_wall=120.0 + i,
            )
            gex = GEXData(
                net_gamma=(100.0 + i * 2) * 1000, gamma_buildup_pct=100.0 + (i % 20)
            )
            vanna = VannaData(
                vanna_regime="positive",
                bullish_target=120.0 + i,
                bull_bear_ratio=2.5 + (i % 10) * 0.1,
            )
            setup = Setup(
                ticker=ticker,
                gex=gex,
                vanna=vanna,
                filters_passed={
                    "positive_gamma": True,
                    "positive_vanna": True,
                    "iv_dropping": i % 2 == 0,
                    "put_wall_proximity": True,
                    "dte_range": True,
                    "bullish_drift": i % 3 == 0,
                },
                composite_rank=100.0 - (i % 50),
                status=["EXPLOSIVE", "HOT", "PRIME", "SOLID", "CAUTION"][i % 5],
                trade_recommendation=["BUY", "HOLD", "SKIP"][i % 3],
            )
            setups.append(setup)

        result = ScanResult(
            timestamp="2026-10-01T14:30:00Z",
            universe=["TEST"],
            tickers_scanned=100,
            candidates_passed=50,
            ranked_list=setups,
            data_freshness_minutes=2,
            cache_hit_rate=0.85,
        )

        json_exporter = JSONExporter()
        json_output = json_exporter.export(result)
        json_data = json.loads(json_output)
        assert len(json_data["candidates"]) == 50

        csv_exporter = CSVExporter()
        csv_output = csv_exporter.export(result)
        csv_rows = list(csv.DictReader(csv_output.strip().split("\n")))
        assert len(csv_rows) == 50
