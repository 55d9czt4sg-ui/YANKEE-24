"""
Fetch SEC 13F institutional holding changes for a ticker from QuiverQuant.

Usage:
    QUIVER_API_KEY=your_key python3 nvda_13f.py [TICKER]

If QUIVER_API_KEY is not set, falls back to the key below -- replace it
with your own (rotate the old one, it was pasted into a chat).
"""

import os
import sys
import requests
import pandas as pd

API_KEY = os.environ.get("QUIVER_API_KEY")
if not API_KEY:
    print("Error: QUIVER_API_KEY environment variable not set", file=sys.stderr)
    sys.exit(1)


def get_13f_changes(ticker="NVDA", most_recent=True):
    url = "https://api.quiverquant.com/beta/live/sec13fchanges"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    # QuiverQuant's API expects a lowercase JSON-style bool as a query string value
    params = {"ticker": ticker, "most_recent": str(most_recent).lower()}
    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "NVDA"
    try:
        data = get_13f_changes(ticker)
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error: {e}", file=sys.stderr)
        print(f"Response body: {e.response.text[:1000]}", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}", file=sys.stderr)
        sys.exit(1)

    if not data:
        print("No data returned.")
        sys.exit(0)

    df = pd.DataFrame(data)
    out_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), f"{ticker}_13f_changes.csv"
    )
    df.to_csv(out_path, index=False)
    print(f"Rows: {len(df)}  ->  saved to {out_path}")
    print(df.head(20).to_string(index=False))
