import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st

from yankee.data.loader import get_financials, get_info, get_price_history

st.set_page_config(page_title="Research | Yankee", layout="wide")
st.title("Research / Due Diligence")

ticker = st.text_input("Ticker", value="AAPL").upper().strip()

if not ticker:
    st.stop()

try:
    info = get_info(ticker)
except Exception as exc:
    st.error(f"Could not fetch info for '{ticker}': {exc}")
    st.stop()

if not info or info.get("regularMarketPrice") is None and info.get("currentPrice") is None:
    st.warning("Limited or no data available for this ticker.")

name = info.get("longName") or info.get("shortName") or ticker
st.subheader(f"{name} ({ticker})")
st.caption(f"{info.get('sector', 'N/A')} — {info.get('industry', 'N/A')}")

price = info.get("currentPrice") or info.get("regularMarketPrice")

cols = st.columns(4)
cols[0].metric("Price", f"${price:,.2f}" if price else "N/A")
cols[1].metric("Market cap", f"${info.get('marketCap'):,}" if info.get("marketCap") else "N/A")
cols[2].metric("P/E (trailing)", f"{info.get('trailingPE'):.2f}" if info.get("trailingPE") else "N/A")
cols[3].metric("52w range", f"{info.get('fiftyTwoWeekLow', 'N/A')} – {info.get('fiftyTwoWeekHigh', 'N/A')}")

cols = st.columns(4)
cols[0].metric("Forward P/E", f"{info.get('forwardPE'):.2f}" if info.get("forwardPE") else "N/A")
cols[1].metric("PEG ratio", f"{info.get('pegRatio'):.2f}" if info.get("pegRatio") else "N/A")
cols[2].metric("Dividend yield", f"{info.get('dividendYield') * 100:.2f}%" if info.get("dividendYield") else "N/A")
cols[3].metric("Beta", f"{info.get('beta'):.2f}" if info.get("beta") else "N/A")

with st.expander("Business summary"):
    st.write(info.get("longBusinessSummary", "No summary available."))

st.subheader("Recent price action")
df = get_price_history(ticker, period="6mo", interval="1d")
if not df.empty:
    st.line_chart(df["Close"])

st.subheader("Financial statements (annual)")
try:
    financials = get_financials(ticker)
    for label, frame in [
        ("Income statement", financials["income_statement"]),
        ("Balance sheet", financials["balance_sheet"]),
        ("Cash flow", financials["cash_flow"]),
    ]:
        with st.expander(label):
            if frame is None or frame.empty:
                st.write("No data available.")
            else:
                st.dataframe(frame, use_container_width=True)
except Exception as exc:
    st.warning(f"Could not load financial statements: {exc}")

with st.expander("Raw info (all fields)"):
    st.json(info)
