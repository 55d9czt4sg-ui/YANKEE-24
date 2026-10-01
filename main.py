#!/usr/bin/env python3
"""CLI entry point for Core Market Regime Framework."""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
import config
from quantwheel_client import QuantWheelClient
from models import Ticker, GEXData, VannaData, Setup, ScanResult
from screener import ScreeningEngine, IVTrendAnalyzer, DealerScorer
from output import CLIFormatter, JSONExporter, CSVExporter


def parse_args():
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Core Market Regime Framework - Daily bullish drift screener",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                            # Full scan, CLI output
  python main.py --export-json              # Export results to JSON
  python main.py --top-n 10                 # Show only top 10 candidates
  python main.py --min-gamma-buildup 200    # Filter by gamma buildup
  python main.py --watchlist my_tickers.txt # Use custom ticker list
        """
    )

    parser.add_argument("--watchlist", type=str, default=None,
                       help="Path to custom ticker list (JSON or txt)")
    parser.add_argument("--export-json", action="store_true",
                       help="Export results to JSON file")
    parser.add_argument("--export-csv", action="store_true",
                       help="Export results to CSV file")
    parser.add_argument("--top-n", type=int, default=None,
                       help="Show only top N candidates")
    parser.add_argument("--min-gamma-buildup", type=float, default=None,
                       help="Filter: gamma buildup minimum (percent)")
    parser.add_argument("--min-dealer-score", type=int, default=None,
                       help="Filter: dealer score minimum (0-100)")
    parser.add_argument("--max-price", type=float, default=None,
                       help="Filter: price maximum")
    parser.add_argument("--min-bull-bear", type=float, default=None,
                       help="Filter: bull/bear ratio minimum")
    parser.add_argument("--no-cache", action="store_true",
                       help="Skip cache, fetch all fresh")
    parser.add_argument("--cache-ttl", type=int, default=config.CACHE_TTL_MINUTES,
                       help="Cache TTL in minutes (default: %(default)s)")
    parser.add_argument("--quiet", action="store_true",
                       help="Suppress CLI output (JSON/CSV only)")
    parser.add_argument("--debug", action="store_true",
                       help="Print detailed logs")

    return parser.parse_args()


def load_tickers(watchlist_path: Optional[str]) -> List[str]:
    """Load ticker list (from watchlist or default SPX+NDX)."""
    if watchlist_path:
        path = Path(watchlist_path)
        if path.suffix.lower() == ".json":
            import json
            with open(path) as f:
                tickers = json.load(f)
            if not isinstance(tickers, list) or not all(
                isinstance(ticker, str) for ticker in tickers
            ):
                raise ValueError("JSON watchlist must be an array of ticker strings")
        else:
            with open(path) as f:
                tickers = [line.strip() for line in f if line.strip()]
        normalized = []
        seen = set()
        for ticker in tickers:
            symbol = ticker.strip().upper()
            if symbol and symbol not in seen:
                normalized.append(symbol)
                seen.add(symbol)
        return normalized

    return config.ALL_TICKERS


def run_scan(
    tickers: List[str], args, client: Optional[QuantWheelClient] = None
) -> ScanResult:
    """Execute the screening scan."""
    if client is None:
        client = QuantWheelClient(
            cache_ttl_minutes=args.cache_ttl,
            no_cache=getattr(args, "no_cache", False),
        )
    engine = ScreeningEngine()

    results = []
    warnings = []

    for ticker_symbol in tickers:
        try:
            # Fetch data
            quote = client.get_quote_data(ticker_symbol)
            if quote is None:
                warnings.append(f"{ticker_symbol}: Quote data missing (skipped)")
                continue

            price = quote["price"]
            iv = quote["iv"]
            if iv is None:
                warnings.append(f"{ticker_symbol}: IV data missing (skipped)")
                continue
            iv_3day_avg = quote["iv_3day_avg"]
            iv_5day_avg = quote["iv_5day_avg"]
            if iv_3day_avg is None or iv_5day_avg is None:
                warnings.append(f"{ticker_symbol}: Historical IV data missing (skipped)")
                continue

            # Fetch GEX + Vanna
            # NOTE: For real implementation, fetch for multiple expirations (0-7, 8-14, 15-21 DTE)
            gex = client.get_gex(ticker_symbol, "2026-10-18")  # Placeholder expiration
            vanna = client.get_vanna_charm(ticker_symbol)

            if gex is None or vanna is None:
                warnings.append(f"{ticker_symbol}: GEX/Vanna data missing (skipped)")
                continue
            if gex.put_wall is None or gex.put_wall <= 0:
                warnings.append(f"{ticker_symbol}: Put wall data missing (skipped)")
                continue

            # Build ticker object
            ticker = Ticker(
                name=ticker_symbol,
                current_price=price,
                current_iv=iv,
                bullish_target=vanna.bullish_target,
                put_wall=gex.put_wall,
                call_wall=gex.call_wall,
            )

            # Check all conditions
            filters_passed = engine.check_conditions(
                ticker, gex, vanna,
                iv_3day_avg=iv_3day_avg,
                iv_5day_avg=iv_5day_avg,
                expirations_dte=[10, 17, 24],  # TODO: Calculate actual DTEs
            )

            if not engine.apply_filter_dict(filters_passed):
                continue

            # Calculate scores
            dealer_scorer = DealerScorer()
            dealer_score = dealer_scorer.calculate_dealer_score(
                filters_passed["positive_gamma"],
                filters_passed["positive_vanna"],
                filters_passed["iv_dropping"],
                vanna.bull_bear_ratio,
                filters_passed["bullish_drift"],
            )

            status = engine.get_status_badge(gex.gamma_buildup_pct)
            trade_rec = engine.get_trade_recommendation(status)

            # Create setup
            setup = Setup(
                ticker=ticker,
                gex=gex,
                vanna=vanna,
                filters_passed=filters_passed,
                composite_rank=0.0,  # TODO: Calculate once all candidates are collected
                status=status,
                trade_recommendation=trade_rec,
            )

            results.append(setup)

        except Exception as e:
            if args.debug:
                print(f"⚠️  Error processing {ticker_symbol}: {e}")
            warnings.append(f"{ticker_symbol}: Unexpected error (skipped)")

    # Calculate real dealer scores and relative ranks across all candidates.
    dealer_scores = {}
    if results:
        gamma_builtups = [s.gex.gamma_buildup_pct for s in results]
        bull_bears = [s.vanna.bull_bear_ratio for s in results]
        dealer_scorer = DealerScorer()
        dealer_scores_list = [
            dealer_scorer.calculate_dealer_score(
                s.filters_passed["positive_gamma"],
                s.filters_passed["positive_vanna"],
                s.filters_passed["iv_dropping"],
                s.vanna.bull_bear_ratio,
                s.filters_passed["bullish_drift"],
            )
            for s in results
        ]
        proximities = [s.ticker.distance_to_put_wall_pct() for s in results]

        for index, setup in enumerate(results):
            dealer_scores[setup.ticker.name] = dealer_scores_list[index]
            rotated = lambda values: [
                values[index], *values[:index], *values[index + 1 :]
            ]
            setup.composite_rank = dealer_scorer.calculate_composite_rank(
                rotated(gamma_builtups),
                rotated(bull_bears),
                rotated(dealer_scores_list),
                rotated(proximities),
            )

    # Sort by composite rank (descending)
    results.sort(key=lambda s: s.composite_rank, reverse=True)

    # Apply CLI filters
    if args.min_gamma_buildup is not None:
        results = [s for s in results if s.gex.gamma_buildup_pct >= args.min_gamma_buildup]
    if args.min_dealer_score is not None:
        results = [
            s for s in results
            if dealer_scores.get(s.ticker.name, 0) >= args.min_dealer_score
        ]
    if args.max_price is not None:
        results = [s for s in results if s.ticker.current_price <= args.max_price]
    if args.min_bull_bear is not None:
        results = [s for s in results if s.vanna.bull_bear_ratio >= args.min_bull_bear]

    if args.top_n is not None:
        results = results[:args.top_n]

    # Print warnings
    if warnings and not args.quiet:
        print("\n⚠️  WARNINGS")
        print("-" * 80)
        for warning in warnings:
            print(warning)

    # Build scan result
    cache_stats = client.cache_stats()
    if not isinstance(cache_stats, dict):
        cache_stats = {}
    known_universes = {
        ticker.upper() for ticker in config.SPX_500_TICKERS + config.NDX_100_TICKERS
    }
    universe = (
        ["SPX", "NDX"]
        if tickers and set(t.upper() for t in tickers).issubset(known_universes)
        else ["custom"]
    )
    scan_result = ScanResult(
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        universe=universe,
        tickers_scanned=len(tickers),
        candidates_passed=len(results),
        ranked_list=results,
        data_freshness_minutes=int(cache_stats.get("oldest_cache_age_minutes", 0)),
        cache_hit_rate=float(cache_stats.get("cache_hit_rate", 0.0)),
    )

    return scan_result


def main():
    """Main entry point."""
    args = parse_args()

    # Load tickers
    tickers = load_tickers(args.watchlist)

    # Run scan
    scan_result = run_scan(tickers, args)

    # Format output
    cli_formatter = CLIFormatter()
    json_exporter = JSONExporter()
    csv_exporter = CSVExporter()

    # Display CLI if not quiet
    if not args.quiet:
        print(cli_formatter.format_table(scan_result))

    # Export JSON
    if args.export_json:
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
        json_path = Path("scans") / f"{timestamp}.json"
        json_path.parent.mkdir(exist_ok=True)
        with open(json_path, "w") as f:
            f.write(json_exporter.export(scan_result))
        if not args.quiet:
            print(f"\n✅ JSON exported to {json_path}")

    # Export CSV
    if args.export_csv:
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
        csv_path = Path("scans") / f"{timestamp}.csv"
        csv_path.parent.mkdir(exist_ok=True)
        with open(csv_path, "w") as f:
            f.write(csv_exporter.export(scan_result))
        if not args.quiet:
            print(f"✅ CSV exported to {csv_path}")


if __name__ == "__main__":
    main()
