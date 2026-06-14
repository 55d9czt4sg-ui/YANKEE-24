import streamlit as st

st.set_page_config(page_title="Yankee | Stock Research", layout="wide")

st.title("📈 Yankee Stock Research Toolkit")

st.markdown(
    """
Welcome to **Yankee** — a personal stock research and trading workflow toolkit.

Use the pages in the sidebar:

- **Charting** — interactive candlestick charts with moving averages, RSI,
  MACD and Bollinger Bands.
- **Screener** — scan a list of tickers for technical "setups" (golden
  crosses, RSI extremes, breakouts, volume spikes, etc.).
- **Backtest** — test simple rules-based strategies against historical
  data and review performance stats (CAGR, Sharpe, drawdown, win rate).
- **Research** — due-diligence view of a company: profile, key stats and
  financial statements.
- **Watchlist** — track tickers you're following and log trades to
  monitor open positions.

---

⚠️ **Disclaimer**: This tool is for personal research and education only.
Nothing here is financial advice. Market data is provided by Yahoo Finance
via `yfinance` and may be delayed or inaccurate.
"""
)
