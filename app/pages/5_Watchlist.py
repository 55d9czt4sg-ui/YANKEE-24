import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd
import streamlit as st

from yankee.data.loader import get_price_history
from yankee.tracking.db import (
    add_to_watchlist,
    get_open_positions,
    get_trades,
    get_watchlist,
    log_trade,
    remove_from_watchlist,
)

st.set_page_config(page_title="Watchlist | Yankee", layout="wide")
st.title("Watchlist & Trade Journal")

tab_watchlist, tab_trades, tab_positions = st.tabs(["Watchlist", "Trade journal", "Open positions"])

with tab_watchlist:
    st.subheader("Watchlist")

    with st.form("add_watchlist", clear_on_submit=True):
        c1, c2, c3 = st.columns([2, 4, 1])
        new_ticker = c1.text_input("Ticker").upper().strip()
        new_notes = c2.text_input("Notes")
        submitted = c3.form_submit_button("Add", type="primary")
        if submitted and new_ticker:
            add_to_watchlist(new_ticker, notes=new_notes)
            st.rerun()

    watchlist = get_watchlist()
    if watchlist.empty:
        st.info("Your watchlist is empty. Add a ticker above.")
    else:
        rows = []
        for _, row in watchlist.iterrows():
            df = get_price_history(row["Ticker"], period="5d", interval="1d")
            last_close = df["Close"].iloc[-1] if not df.empty else None
            rows.append({**row, "Last close": last_close})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        remove_ticker = st.selectbox("Remove ticker", [""] + list(watchlist["Ticker"]))
        if st.button("Remove") and remove_ticker:
            remove_from_watchlist(remove_ticker)
            st.rerun()

with tab_trades:
    st.subheader("Log a trade")

    with st.form("log_trade", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        trade_ticker = c1.text_input("Ticker").upper().strip()
        side = c2.selectbox("Side", ["BUY", "SELL"])
        quantity = c3.number_input("Quantity", min_value=0.0, step=1.0)
        price = c4.number_input("Price", min_value=0.0, step=0.01)
        notes = st.text_input("Notes (optional)")
        submitted = st.form_submit_button("Log trade", type="primary")
        if submitted and trade_ticker and quantity > 0:
            log_trade(
                trade_ticker,
                side,
                quantity,
                price,
                executed_at=datetime.now().isoformat(),
                notes=notes,
            )
            st.rerun()

    st.subheader("Trade history")
    trades = get_trades()
    if trades.empty:
        st.info("No trades logged yet.")
    else:
        st.dataframe(trades.sort_values("ExecutedAt", ascending=False), use_container_width=True, hide_index=True)

with tab_positions:
    st.subheader("Open positions")
    positions = get_open_positions()
    if positions.empty:
        st.info("No open positions.")
    else:
        rows = []
        for _, row in positions.iterrows():
            df = get_price_history(row["Ticker"], period="5d", interval="1d")
            last_close = df["Close"].iloc[-1] if not df.empty else None
            market_value = last_close * row["Quantity"] if last_close is not None else None
            unrealized = (market_value - row["CostBasis"]) if market_value is not None else None
            rows.append(
                {
                    **row,
                    "Last close": last_close,
                    "Market value": market_value,
                    "Unrealized P/L": unrealized,
                }
            )
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
