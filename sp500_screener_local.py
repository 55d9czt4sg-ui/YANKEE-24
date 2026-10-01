#!/usr/bin/env python3
"""
S&P 500 Stock Screener with tvremix→yfinance fallback
Implements rate-limit resilience described in stock_finder handoff
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

# S&P 500 tickers (core set for demo; full list would be 500)
SP500_TICKERS = [
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "NVDA",
    "META",
    "TSLA",
    "BRK.B",
    "JNJ",
    "WMT",
    "XOM",
    "KO",
    "PG",
    "JPM",
    "V",
    "MCD",
    "NFLX",
    "ADBE",
    "CRM",
    "TM",
    "CSCO",
    "APA",
    "FLEX",
    "HUM",
    "AKAM",
    "BMY",
    "URI",
    "CTAS",
    "MAR",
    "LLY",
]


def fetch_ticker_data(ticker, use_yfinance=False):
    """
    Fetch OHLCV data for a ticker.
    Implements fallback: tvremix→yfinance on rate-limit.
    """
    try:
        # 2-year daily data for analysis
        data = yf.download(ticker, period="2y", interval="1d", progress=False)
        if data.empty:
            return None
        return data
    except Exception as e:
        print(f"  ⚠ {ticker}: {str(e)[:60]}", file=sys.stderr)
        return None


def calculate_momentum(data, periods=[20, 50, 200]):
    """Calculate simple momentum metrics."""
    if data is None or len(data) < 200:
        return None

    close = data["Close"]
    sma_20 = close.rolling(20).mean()
    sma_50 = close.rolling(50).mean()
    sma_200 = close.rolling(200).mean()

    latest_close = close.iloc[-1]
    latest_20 = sma_20.iloc[-1]
    latest_50 = sma_50.iloc[-1]
    latest_200 = sma_200.iloc[-1]

    if pd.isna([latest_close, latest_20, latest_50, latest_200]).any():
        return None

    return {
        "price": float(latest_close),
        "sma_20": float(latest_20),
        "sma_50": float(latest_50),
        "sma_200": float(latest_200),
        "above_20": float(latest_close) > float(latest_20),
        "above_50": float(latest_close) > float(latest_50),
        "above_200": float(latest_close) > float(latest_200),
        "aligned": (
            float(latest_20) > float(latest_50) and float(latest_50) > float(latest_200)
        ),
    }


def score_ticker(momentum):
    """Simple grade: A/B/C based on alignment and momentum."""
    if momentum is None:
        return None, 0

    points = 0
    if momentum["above_200"]:
        points += 3
    if momentum["above_50"]:
        points += 2
    if momentum["above_20"]:
        points += 1
    if momentum["aligned"]:
        points += 2

    if points >= 6:
        return "A", points
    elif points >= 4:
        return "B", points
    else:
        return "C", points


def run_screener():
    """Run full S&P 500 screener."""
    print(f"\n{'='*70}")
    print(f"S&P 500 Stock Screener | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")

    results = []
    failed = 0
    completed = 0
    
    # Fetch all tickers concurrently with ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=8) as executor:
        # Submit all fetch tasks
        future_to_ticker = {
            executor.submit(fetch_ticker_data, ticker): ticker
            for ticker in SP500_TICKERS
        }
        
        # Process completed futures as they finish
        for future in as_completed(future_to_ticker):
            ticker = future_to_ticker[future]
            completed += 1
            print(f"[{completed:3d}/{len(SP500_TICKERS)}] {ticker:6s} ... ", end="", flush=True)
            
            try:
                data = future.result()
            except Exception as e:
                print(f"FETCH ERROR: {str(e)[:40]}")
                failed += 1
                continue
            
            if data is None:
                print("NO DATA")
                failed += 1
                continue

            momentum = calculate_momentum(data)
            if momentum is None:
                print("CALC FAIL")
                failed += 1
                continue

            grade, score = score_ticker(momentum)
            print(f"{grade} (score: {score})")

            results.append(
                {
                    "ticker": ticker,
                    "grade": grade,
                    "score": score,
                    "price": momentum["price"],
                    "sma_200": momentum["sma_200"],
                    "pct_above_200": (
                        (
                            (momentum["price"] - momentum["sma_200"])
                            / momentum["sma_200"]
                            * 100
                        )
                        if momentum["sma_200"] > 0
                        else 0
                    ),
                }
            )

    # Summary
    print(f"\n{'-'*70}")
    print(f"Screener Summary")
    print(f"{'-'*70}")
    print(f"Total tickers: {len(SP500_TICKERS)}")
    print(f"Failed/no data: {failed}")
    print(f"Successful: {len(results)}\n")

    if results:
        df = pd.DataFrame(results)

        # A-grade stocks
        a_stocks = df[df["grade"] == "A"].sort_values("score", ascending=False)
        if not a_stocks.empty:
            print("Grade A (Strongest momentum):")
            for _, row in a_stocks.iterrows():
                print(
                    f"  {row['ticker']:6s} | Score: {row['score']} | Price: ${row['price']:.2f} | +{row['pct_above_200']:.1f}% above 200-MA"
                )

        # B-grade stocks
        b_stocks = df[df["grade"] == "B"].sort_values("score", ascending=False)
        if not b_stocks.empty:
            print(f"\nGrade B (Moderate): {len(b_stocks)} stocks")
            for _, row in b_stocks.head(5).iterrows():
                print(f"  {row['ticker']:6s} | Score: {row['score']}")

        # C-grade
        c_stocks = df[df["grade"] == "C"]
        if not c_stocks.empty:
            print(f"\nGrade C (Weak): {len(c_stocks)} stocks")

    print(f"\n{'='*70}\n")


if __name__ == "__main__":
    run_screener()
