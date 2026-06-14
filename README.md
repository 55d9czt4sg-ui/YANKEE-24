# Yankee — Stock Research & Trading Toolkit

A personal toolkit for stock/ETF research: charting, technical screening
("setups"), simple rules-based backtesting, due-diligence research, and a
watchlist/trade journal. Built with Python, [yfinance](https://github.com/ranaroussi/yfinance)
for market data, [Streamlit](https://streamlit.io/) for the UI, and
[Plotly](https://plotly.com/python/) for charts.

> ⚠️ For personal research and education only. Not financial advice.

## Setup

```bash
pip install -r requirements.txt
```

Requires Python 3.10+.

## Running the app

```bash
streamlit run app/Home.py
```

This opens a multi-page app:

- **Charting** — candlestick charts with SMA/Bollinger overlays and
  RSI/MACD subplots for any ticker.
- **Screener** — scan a list of tickers for technical setups (golden
  cross, RSI extremes, new 52-week highs/lows, MACD crossovers,
  Bollinger squeezes, volume spikes).
- **Backtest** — run simple rules-based strategies (SMA/EMA crossover,
  RSI mean-reversion, MACD trend) against historical data and view
  CAGR, Sharpe ratio, max drawdown, and win rate vs. buy & hold.
- **Research** — company profile, valuation metrics, and financial
  statements for due diligence.
- **Watchlist** — track tickers and log trades; open positions and
  unrealized P/L are derived from the trade log.

## Running tests

```bash
pytest
```

Tests use synthetic price data and do not require network access.

## Project layout

```
yankee/            # core library (importable, no Streamlit dependency)
  data/loader.py       # yfinance data access + on-disk CSV caching
  indicators/core.py   # SMA, EMA, RSI, MACD, Bollinger Bands, ATR, Stochastic
  screener/setups.py   # technical "setup" detectors + multi-ticker scanner
  backtest/engine.py   # vectorized backtest engine + performance stats
  backtest/strategies.py # example strategies (registry-based)
  tracking/db.py       # SQLite watchlist & trade journal
  charts/plotting.py   # Plotly candlestick/indicator chart builder

app/               # Streamlit UI
  Home.py
  pages/           # one file per page, numbered for sidebar order

tests/             # pytest suite (synthetic data, no network calls)
```

Local data (price cache, SQLite DB) is written under `data/` at the repo
root and is gitignored.
