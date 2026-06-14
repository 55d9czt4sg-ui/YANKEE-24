"""SQLite-backed watchlist and trade journal.

Two tables are used:

- ``watchlist``: tickers you're following, with optional notes.
- ``trades``: a simple trade journal (BUY/SELL fills), from which open
  positions and cost basis are derived.

All functions accept an optional `db_path` for testing; by default they
use yankee.config.DB_PATH.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from yankee.config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS watchlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL UNIQUE,
    added_at TEXT NOT NULL,
    notes TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    side TEXT NOT NULL CHECK(side IN ('BUY', 'SELL')),
    quantity REAL NOT NULL,
    price REAL NOT NULL,
    executed_at TEXT NOT NULL,
    notes TEXT DEFAULT ''
);
"""


@contextmanager
def _connect(db_path: Path = DB_PATH):
    conn = sqlite3.connect(db_path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: Path = DB_PATH) -> None:
    """Create the watchlist/trades tables if they don't already exist."""
    with _connect(db_path) as conn:
        conn.executescript(SCHEMA)


def add_to_watchlist(ticker: str, notes: str = "", db_path: Path = DB_PATH) -> None:
    init_db(db_path)
    ticker = ticker.upper().strip()
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO watchlist (ticker, added_at, notes)
            VALUES (?, ?, ?)
            ON CONFLICT(ticker) DO UPDATE SET notes = excluded.notes
            """,
            (ticker, datetime.now(timezone.utc).isoformat(), notes),
        )


def remove_from_watchlist(ticker: str, db_path: Path = DB_PATH) -> None:
    init_db(db_path)
    ticker = ticker.upper().strip()
    with _connect(db_path) as conn:
        conn.execute("DELETE FROM watchlist WHERE ticker = ?", (ticker,))


def get_watchlist(db_path: Path = DB_PATH) -> pd.DataFrame:
    init_db(db_path)
    with _connect(db_path) as conn:
        return pd.read_sql_query(
            "SELECT ticker AS Ticker, added_at AS AddedAt, notes AS Notes "
            "FROM watchlist ORDER BY ticker",
            conn,
        )


def log_trade(
    ticker: str,
    side: str,
    quantity: float,
    price: float,
    executed_at: str | None = None,
    notes: str = "",
    db_path: Path = DB_PATH,
) -> int:
    """Record a BUY or SELL fill. Returns the new trade's row id."""
    init_db(db_path)
    side = side.upper().strip()
    if side not in ("BUY", "SELL"):
        raise ValueError("side must be 'BUY' or 'SELL'")

    executed_at = executed_at or datetime.now(timezone.utc).isoformat()

    with _connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO trades (ticker, side, quantity, price, executed_at, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (ticker.upper().strip(), side, quantity, price, executed_at, notes),
        )
        return cur.lastrowid


def get_trades(ticker: str | None = None, db_path: Path = DB_PATH) -> pd.DataFrame:
    init_db(db_path)
    query = (
        "SELECT id AS Id, ticker AS Ticker, side AS Side, quantity AS Quantity, "
        "price AS Price, executed_at AS ExecutedAt, notes AS Notes FROM trades"
    )
    params: tuple = ()
    if ticker:
        query += " WHERE ticker = ?"
        params = (ticker.upper().strip(),)
    query += " ORDER BY executed_at"

    with _connect(db_path) as conn:
        return pd.read_sql_query(query, conn, params=params)


def get_open_positions(db_path: Path = DB_PATH) -> pd.DataFrame:
    """Derive net open positions and average cost basis from the trade log.

    Returns a DataFrame with columns: Ticker, Quantity, AvgCost, CostBasis.
    Tickers with a net quantity of zero are excluded.
    """
    trades = get_trades(db_path=db_path)
    if trades.empty:
        return pd.DataFrame(columns=["Ticker", "Quantity", "AvgCost", "CostBasis"])

    rows = []
    for ticker, group in trades.groupby("Ticker"):
        quantity = 0.0
        cost_basis = 0.0
        for _, trade in group.iterrows():
            signed_qty = trade["Quantity"] if trade["Side"] == "BUY" else -trade["Quantity"]
            if trade["Side"] == "BUY":
                cost_basis += trade["Quantity"] * trade["Price"]
            else:
                # Reduce cost basis proportionally to the average cost at time of sale.
                if quantity > 0:
                    avg_cost = cost_basis / quantity
                    cost_basis -= trade["Quantity"] * avg_cost
            quantity += signed_qty

        if abs(quantity) > 1e-9:
            avg_cost = cost_basis / quantity if quantity else 0.0
            rows.append(
                {
                    "Ticker": ticker,
                    "Quantity": quantity,
                    "AvgCost": avg_cost,
                    "CostBasis": cost_basis,
                }
            )

    return pd.DataFrame(rows, columns=["Ticker", "Quantity", "AvgCost", "CostBasis"])
