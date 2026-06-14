import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st

from yankee.charts.plotting import candlestick_chart
from yankee.data.loader import get_price_history
from yankee.indicators.core import bollinger_bands, macd, rsi, sma

st.set_page_config(page_title="Charting | Yankee", layout="wide")
st.title("Charting")

with st.sidebar:
    ticker = st.text_input("Ticker", value="AAPL").upper().strip()
    period = st.selectbox("Period", ["3mo", "6mo", "1y", "2y", "5y", "max"], index=2)
    interval = st.selectbox("Interval", ["1d", "1wk", "1mo"], index=0)

    st.subheader("Overlays")
    show_sma_fast = st.checkbox("SMA 50", value=True)
    show_sma_slow = st.checkbox("SMA 200", value=True)
    show_bbands = st.checkbox("Bollinger Bands (20, 2)", value=False)

    st.subheader("Indicators")
    show_rsi = st.checkbox("RSI (14)", value=True)
    show_macd = st.checkbox("MACD (12, 26, 9)", value=True)

if not ticker:
    st.stop()

df = get_price_history(ticker, period=period, interval=interval)

if df.empty:
    st.error(f"No price data found for '{ticker}'.")
    st.stop()

overlays = {}
if show_sma_fast:
    overlays["SMA 50"] = sma(df["Close"], 50)
if show_sma_slow:
    overlays["SMA 200"] = sma(df["Close"], 200)
if show_bbands:
    bands = bollinger_bands(df["Close"])
    overlays["BB Upper"] = bands["upper"]
    overlays["BB Mid"] = bands["mid"]
    overlays["BB Lower"] = bands["lower"]

indicator_panels = {}
if show_rsi:
    indicator_panels["RSI"] = rsi(df["Close"])
if show_macd:
    indicator_panels["MACD"] = macd(df["Close"])

fig = candlestick_chart(
    df,
    title=f"{ticker} — {period} ({interval})",
    overlays=overlays,
    indicator_panels=indicator_panels,
)

st.plotly_chart(fig, use_container_width=True)

latest = df.iloc[-1]
cols = st.columns(5)
cols[0].metric("Close", f"{latest['Close']:.2f}")
cols[1].metric("Open", f"{latest['Open']:.2f}")
cols[2].metric("High", f"{latest['High']:.2f}")
cols[3].metric("Low", f"{latest['Low']:.2f}")
cols[4].metric("Volume", f"{latest['Volume']:,.0f}")

with st.expander("Raw data"):
    st.dataframe(df.sort_index(ascending=False), use_container_width=True)
