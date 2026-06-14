# CLAUDE.md

Guidance for AI assistants working in this repository.

## What this is

Yankee is a personal stock/ETF research and trading-workflow toolkit:
charting, technical screening, rules-based backtesting, due-diligence
research, and a watchlist/trade journal. Python core library + a
Streamlit UI. Market data comes from Yahoo Finance via `yfinance`.

This is for personal research/education — not a brokerage integration
and not financial advice. Don't add live order-execution/broker API
code without explicit direction from the user.

## Project layout

```
yankee/                  # core library — no Streamlit imports here
  config.py              # paths: CACHE_DIR, DB_PATH (under data/, gitignored)
  data/loader.py         # yfinance access + CSV caching
  indicators/core.py      # SMA, EMA, RSI, MACD, Bollinger Bands, ATR, Stochastic
  screener/setups.py      # technical "setup" detectors + SETUPS registry + scanner
  backtest/engine.py      # vectorized backtest engine (run_backtest, BacktestResult)
  backtest/strategies.py   # STRATEGIES registry of position-generating strategies
  tracking/db.py           # SQLite watchlist & trade journal
  charts/plotting.py       # Plotly candlestick/indicator chart builder

app/                     # Streamlit UI (depends on yankee/, not vice versa)
  Home.py
  pages/1_Charting.py
  pages/2_Screener.py
  pages/3_Backtest.py
  pages/4_Research.py
  pages/5_Watchlist.py

tests/                   # pytest, synthetic data only, no network calls
```

## Conventions

### Price data schema

`yankee.data.loader.get_price_history(ticker, period, interval)` returns
a `DataFrame` with columns `Open, High, Low, Close, Volume`, indexed by
a `DatetimeIndex` named `"Date"`. Every other module (indicators,
screener, backtest, charts) assumes this shape. Empty `DataFrame` means
"no data" — callers must check `.empty` rather than assuming success.

`get_price_history` **must never raise** on network failure — it wraps
the `yfinance` call in `try/except` and returns an empty `DataFrame`
instead. (Yahoo's endpoints can be unreachable in sandboxed
environments, and `yfinance` itself raises ugly low-level exceptions —
e.g. `TypeError` — instead of a clean error when the HTTP request fails
outright.)

Price history is cached to CSV under `data/cache/` (`CACHE_TTL_SECONDS`,
currently 4 hours). `data/` is gitignored — never commit cache files or
the SQLite DB.

### Indicators (`yankee/indicators/core.py`)

Pure functions on `pd.Series`/`pd.DataFrame`, no I/O. Single-output
indicators return a named `Series` (e.g. `sma()` -> `"SMA_20"`).
Multi-output indicators return a `DataFrame` with fixed lowercase column
names (`macd()` -> `macd, signal, hist`; `bollinger_bands()` -> `mid,
upper, lower`; `stochastic_oscillator()` -> `%K, %D`).

### Screener setups (`yankee/screener/setups.py`)

Each setup detector takes an OHLCV `DataFrame` and returns a boolean
`Series` aligned to `df.index` (`True` where the setup fires on that
bar). New setups must be added to the `SETUPS` dict so they're picked up
by `scan()` / `scan_tickers()` and the Screener page automatically.
`scan()` swallows exceptions per-setup (returns `False`) so one bad
setup/insufficient history doesn't break the whole scan.

### Backtest engine (`yankee/backtest/`)

Strategies (`strategies.py`) return a target **position** `Series` in
`{-1, 0, 1}` (short/flat/long), aligned to `df.index`. New strategies
register themselves via the `@_register("name")` decorator into
`STRATEGIES`, which both `get_strategy()` and the Backtest page read
from — register new strategies there rather than hardcoding names
elsewhere.

`run_backtest()` (`engine.py`) is vectorized and **shifts positions by
one bar** before applying returns, to avoid lookahead bias (a position
decided using bar `t`'s close is held over the `t -> t+1` return).
Commission is a fractional cost applied to `|Δposition|` per bar. It
returns a `BacktestResult` dataclass (equity curve, returns, positions,
total_return, cagr, sharpe, max_drawdown, num_trades, win_rate).

### Tracking (`yankee/tracking/db.py`)

SQLite with two tables: `watchlist` (ticker, notes) and `trades`
(BUY/SELL fills). Open positions and average cost basis are *derived*
from the trade log on read (`get_open_positions()`) — there is no
separate positions table. Every function accepts an optional `db_path`
override (defaults to `yankee.config.DB_PATH`); tests use this with
`tmp_path` to avoid touching the real DB. `init_db()` is idempotent and
called automatically by the other functions.

### Charts (`yankee/charts/plotting.py`)

`candlestick_chart()` builds one Plotly figure with the price/volume
panel plus one subplot row per entry in `indicator_panels` (a `Series`
=> single line, a `DataFrame` => one line per column). Add new
chart-overlay indicators via the `overlays`/`indicator_panels` dicts
rather than new chart functions.

### Streamlit app (`app/`)

Each page is standalone and begins with a `sys.path.insert(0, ...)`
bootstrap (3 levels up from `app/pages/*.py`, 2 from `app/Home.py`) so
`yankee` is importable without installing the package. Keep this
bootstrap snippet at the top of any new page. Pages are numbered
(`1_`, `2_`, ...) to control sidebar ordering — follow the existing
numbering when adding pages.

## Development workflow

```bash
pip install -r requirements.txt   # install deps
streamlit run app/Home.py         # run the app (http://localhost:8501)
pytest                             # run the test suite
```

- Tests must not depend on network access — use the fixtures in
  `tests/conftest.py` (`price_df`, `uptrend_df`, synthetic OHLCV data)
  and, for screener/data-layer tests, `monkeypatch` `get_price_history`.
- When verifying Streamlit pages in an agent/headless context,
  `streamlit.testing.v1.AppTest` can run a page in-process and surface
  exceptions without a browser — useful since Yahoo Finance hosts are
  often blocked by sandbox network policies.
- Don't add heavy new dependencies (e.g. TA-Lib, full broker SDKs)
  without checking with the user first — the project intentionally
  keeps a small, pure-Python/pandas dependency footprint.
