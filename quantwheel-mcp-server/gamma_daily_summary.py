#!/usr/bin/env python3
"""
Gamma Monitor Daily Summary Builder
Parses latest gamma_monitor_*.log and outputs a clean markdown/HTML table summary.
Designed to run at ~9:30 PM ET daily after the after-hours monitor session.
"""

import re, glob, os, sys
from datetime import datetime
from collections import defaultdict

LOG_DIR = os.path.expanduser("~")


def latest_log():
    logs = sorted(
        glob.glob(f"{LOG_DIR}/gamma_monitor_*.log"), key=os.path.getmtime, reverse=True
    )
    return logs[0] if logs else None


def parse_log(path):
    checks = defaultdict(list)
    current = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            m = re.match(r"CHECK #(\d+) \| (\w+) \| ([\d: -]+) ET", line)
            if m:
                if current:
                    checks[current["symbol"]].append(current)
                current = {
                    "check": m.group(1),
                    "symbol": m.group(2),
                    "time": m.group(3).strip(),
                    "signals": [],
                }
            elif current:
                if line.startswith("Spot "):
                    parts = line.split()
                    current["spot"] = parts[1] if len(parts) > 1 else "N/A"
                elif "Put wall" in line and "Call wall" in line:
                    put_match = re.search(r"Put wall ([\d.]+)", line)
                    call_match = re.search(r"Call wall ([\d.]+)", line)
                    zero_match = re.search(r"Zero flip ([\d.]+)", line)
                    pain_match = re.search(r"Max pain ([\d.]+)", line)
                    drift_match = re.search(r"Bull drift \(vanna\) ([+-][\d.]+)", line)
                    current["put_wall"] = put_match.group(1) if put_match else "N/A"
                    current["call_wall"] = call_match.group(1) if call_match else "N/A"
                    current["zero_flip"] = zero_match.group(1) if zero_match else "N/A"
                    current["max_pain"] = pain_match.group(1) if pain_match else "N/A"
                    current["bull_drift"] = (
                        drift_match.group(1) if drift_match else "N/A"
                    )
                elif line.startswith("Gamma:"):
                    current["regime"] = "Long" if "long-gamma" in line else "Short"
                    gex = re.search(r"([+-][\d,]+)", line)
                    current["net_gex"] = gex.group(1) if gex else "N/A"
                elif line.startswith("DEX:"):
                    dex = re.search(r"\(([+-][\d,]+)\)", line)
                    dflip = re.search(r"flip ([\d.]+)", line)
                    current["dex"] = dex.group(1) if dex else "N/A"
                    current["dex_flip"] = dflip.group(1) if dflip else "N/A"
                elif line.startswith("["):
                    current["signals"].append(line)
    if current and "symbol" in current:
        checks[current["symbol"]].append(current)
    return checks


def build_markdown(checks, date_str):
    out = [f"# Gamma Monitor Daily Summary — {date_str}\n"]
    for sym in ["SPY", "QQQ"]:
        rows = checks.get(sym, [])
        if not rows:
            continue
        out.append(f"## {sym}")
        out.append(
            "| Check | Time ET | Spot | Zero Flip | Net GEX | Regime | Put Wall | Call Wall | Max Pain | DEX | Signals |"
        )
        out.append("|---|---|---|---|---|---|---|---|---|---|---|")
        for r in rows:
            sigs = " · ".join(r.get("signals", [])) or "None"
            regime_icon = "🟢" if r.get("regime") == "Long" else "🔴"
            out.append(
                f"| #{r['check']} | {r['time']} | {r.get('spot','?')} | {r.get('zero_flip','?')} | {r.get('net_gex','?')} | {regime_icon} {r.get('regime','?')}-gamma | {r.get('put_wall','?')} | {r.get('call_wall','?')} | {r.get('max_pain','?')} | {r.get('dex','?')} | {sigs} |"
            )
        out.append("")
    return "\n".join(out)


if __name__ == "__main__":
    log = latest_log()
    if not log:
        print("No log file found")
        sys.exit(1)
    print(f"Parsing: {log}")
    checks = parse_log(log)
    date_str = datetime.now().strftime("%b %d, %Y")
    md = build_markdown(checks, date_str)
    out_path = os.path.expanduser(
        f"~/gamma_summary_{datetime.now().strftime('%Y%m%d')}.md"
    )
    with open(out_path, "w") as f:
        f.write(md)
    print(md)
    print(f"\nSaved to: {out_path}")
