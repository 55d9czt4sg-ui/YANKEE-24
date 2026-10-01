"""Output formatters: CLI, JSON, CSV."""

import json
import csv
from io import StringIO
from datetime import datetime
from typing import List, Optional
from models import ScanResult, Setup

try:
    from tabulate import tabulate

    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False


class CLIFormatter:
    """Format scan results as CLI table."""

    def format_table(self, results: ScanResult) -> str:
        """Format results as pretty CLI table with summary."""
        lines = []

        # Title
        lines.append("")
        lines.append("BULLISH DRIFT SCAN - SPX + NDX")
        lines.append("=" * 95)

        # Table headers
        headers = [
            "Rank",
            "Ticker",
            "Price",
            "Target",
            "Put Wall",
            "Call Wall",
            "Bull/Bear",
            "Gamma ↑",
            "Composite",
            "Status",
        ]

        # Table rows
        rows = []
        for i, setup in enumerate(results.ranked_list, 1):
            rows.append(
                [
                    str(i),
                    setup.ticker.name,
                    f"${setup.ticker.current_price:.2f}",
                    f"${setup.ticker.bullish_target:.2f}",
                    f"${setup.ticker.put_wall:.2f}",
                    f"${setup.ticker.call_wall:.2f}",
                    f"{setup.vanna.bull_bear_ratio:.2f}x",
                    f"+{setup.gex.gamma_buildup_pct:.1f}%",
                    f"{setup.composite_rank:.1f}/10",
                    setup.status,
                ]
            )

        if rows:
            if HAS_TABULATE:
                table_str = tabulate(rows, headers=headers, tablefmt="grid")
                lines.append(table_str)
            else:
                # Fallback: simple text table
                lines.append(self._format_simple_table(headers, rows))
        else:
            lines.append("(No candidates found)")

        # Summary
        lines.append("")
        lines.append("📊 SUMMARY")
        lines.append("-" * 80)
        lines.append(f"Tickers Scanned:        {results.tickers_scanned}")
        lines.append(f"Passed Filters:         {results.candidates_passed}")
        top_rank = results.ranked_list[0] if results.ranked_list else None
        if top_rank:
            lines.append(
                f"Top Ranked Setup:       {top_rank.ticker.name} (Rank 1, Score {top_rank.composite_rank:.1f}/10)"
            )
        lines.append(f"Scan Completed:         {results.timestamp}")
        lines.append(f"Data Freshness:         ~{results.data_freshness_minutes} min")
        lines.append(f"Cache Hit Rate:         {results.cache_hit_rate*100:.0f}%")

        return "\n".join(lines)

    @staticmethod
    def _format_simple_table(headers: List[str], rows: List[List[str]]) -> str:
        """Format a simple text table (fallback when tabulate is unavailable)."""
        lines = []
        col_widths = [len(h) for h in headers]

        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))

        # Header
        header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
        lines.append(header_line)
        lines.append("-" * len(header_line))

        # Rows
        for row in rows:
            row_line = " | ".join(
                str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)
            )
            lines.append(row_line)

        return "\n".join(lines)


class JSONExporter:
    """Export scan results as JSON."""

    def export(self, results: ScanResult) -> str:
        """Export results to JSON string."""
        data = {
            "scan": {
                "timestamp": results.timestamp,
                "universe": results.universe,
                "tickers_scanned": results.tickers_scanned,
                "candidates_passed": results.candidates_passed,
                "data_freshness_minutes": results.data_freshness_minutes,
                "cache_hit_rate": results.cache_hit_rate,
            },
            "candidates": [
                {
                    "rank": i + 1,
                    "ticker": setup.ticker.name,
                    "current_price": setup.ticker.current_price,
                    "bullish_target": setup.ticker.bullish_target,
                    "put_wall": setup.ticker.put_wall,
                    "call_wall": setup.ticker.call_wall,
                    "bull_bear_ratio": setup.vanna.bull_bear_ratio,
                    "gamma_buildup_pct": setup.gex.gamma_buildup_pct,
                    "composite_rank": setup.composite_rank,
                    "status": setup.status,
                    "trade_recommendation": setup.trade_recommendation,
                    "filters_passed": setup.filters_passed,
                }
                for i, setup in enumerate(results.ranked_list)
            ],
        }

        return json.dumps(data, indent=2)


class CSVExporter:
    """Export scan results as CSV."""

    def export(self, results: ScanResult) -> str:
        """Export results to CSV string."""
        output = StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(
            [
                "rank",
                "ticker",
                "price",
                "target",
                "put_wall",
                "call_wall",
                "bull_bear_ratio",
                "gamma_buildup_pct",
                "composite_rank",
                "status",
                "trade_recommendation",
            ]
        )

        # Rows
        for i, setup in enumerate(results.ranked_list, 1):
            writer.writerow(
                [
                    i,
                    setup.ticker.name,
                    f"{setup.ticker.current_price:.2f}",
                    f"{setup.ticker.bullish_target:.2f}",
                    f"{setup.ticker.put_wall:.2f}",
                    f"{setup.ticker.call_wall:.2f}",
                    f"{setup.vanna.bull_bear_ratio:.2f}",
                    f"{setup.gex.gamma_buildup_pct:.1f}",
                    f"{setup.composite_rank:.1f}",
                    setup.status,
                    setup.trade_recommendation,
                ]
            )

        return output.getvalue()
