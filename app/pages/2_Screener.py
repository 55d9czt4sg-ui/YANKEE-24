import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st

from yankee.screener.setups import SETUPS, scan_tickers
from yankee.tracking.db import get_watchlist

st.set_page_config(page_title="Screener | Yankee", layout="wide")
st.title("Screener")

st.markdown("Scan a list of tickers for technical setups on their most recent bar.")

watchlist = get_watchlist()
default_tickers = ", ".join(watchlist["Ticker"]) if not watchlist.empty else "AAPL, MSFT, NVDA, AMZN, GOOGL"

with st.sidebar:
    tickers_input = st.text_area("Tickers (comma or whitespace separated)", value=default_tickers, height=120)
    period = st.selectbox("Period", ["6mo", "1y", "2y", "5y"], index=1)
    interval = st.selectbox("Interval", ["1d", "1wk"], index=0)
    selected_setups = st.multiselect("Setups", list(SETUPS.keys()), default=list(SETUPS.keys()))
    run = st.button("Run scan", type="primary")

tickers = [t.strip().upper() for t in tickers_input.replace(",", " ").split() if t.strip()]

if run:
    if not tickers:
        st.warning("Enter at least one ticker.")
    elif not selected_setups:
        st.warning("Select at least one setup.")
    else:
        with st.spinner(f"Scanning {len(tickers)} ticker(s)..."):
            results = scan_tickers(tickers, setups=selected_setups, period=period, interval=interval)

        if results.empty:
            st.info("No setups matched for the given tickers.")
        else:
            st.success(f"{len(results)} match(es) found.")
            st.dataframe(results, use_container_width=True, hide_index=True)
else:
    st.info("Configure tickers and setups in the sidebar, then click **Run scan**.")

with st.expander("Setup descriptions"):
    for name, func in SETUPS.items():
        st.markdown(f"**{name}** — {(func.__doc__ or '').strip()}")
