import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import plotly.graph_objects as go
import streamlit as st

from yankee.backtest.engine import run_backtest
from yankee.backtest.strategies import STRATEGIES, get_strategy
from yankee.data.loader import get_price_history

st.set_page_config(page_title="Backtest | Yankee", layout="wide")
st.title("Backtest")

with st.sidebar:
    ticker = st.text_input("Ticker", value="AAPL").upper().strip()
    period = st.selectbox("Period", ["1y", "2y", "5y", "10y", "max"], index=2)
    interval = st.selectbox("Interval", ["1d", "1wk"], index=0)

    strategy_name = st.selectbox("Strategy", list(STRATEGIES.keys()))

    st.subheader("Parameters")
    if strategy_name in ("sma_crossover", "ema_crossover"):
        fast = st.number_input("Fast window", min_value=2, max_value=200, value=50 if strategy_name == "sma_crossover" else 12)
        slow = st.number_input("Slow window", min_value=2, max_value=400, value=200 if strategy_name == "sma_crossover" else 26)
        kwargs = {"fast": fast, "slow": slow}
    elif strategy_name == "rsi_mean_reversion":
        window = st.number_input("RSI window", min_value=2, max_value=100, value=14)
        lower = st.number_input("Oversold threshold", min_value=1, max_value=49, value=30)
        upper = st.number_input("Overbought threshold", min_value=51, max_value=99, value=70)
        kwargs = {"window": window, "lower": lower, "upper": upper}
    elif strategy_name == "macd_trend":
        fast = st.number_input("Fast EMA", min_value=2, max_value=100, value=12)
        slow = st.number_input("Slow EMA", min_value=2, max_value=200, value=26)
        signal = st.number_input("Signal EMA", min_value=2, max_value=100, value=9)
        kwargs = {"fast": fast, "slow": slow, "signal": signal}
    else:
        kwargs = {}

    initial_capital = st.number_input("Initial capital", min_value=100.0, value=10_000.0, step=1000.0)
    commission_bps = st.number_input("Commission (bps per turnover)", min_value=0.0, value=5.0, step=1.0)

    run = st.button("Run backtest", type="primary")

if not run:
    st.info("Configure the backtest in the sidebar, then click **Run backtest**.")
    st.stop()

if not ticker:
    st.warning("Enter a ticker.")
    st.stop()

df = get_price_history(ticker, period=period, interval=interval)
if df.empty:
    st.error(f"No price data found for '{ticker}'.")
    st.stop()

strategy_fn = get_strategy(strategy_name)
positions = strategy_fn(df, **kwargs)

result = run_backtest(df, positions, initial_capital=initial_capital, commission=commission_bps / 10_000)

cols = st.columns(6)
cols[0].metric("Total return", f"{result.total_return * 100:.1f}%")
cols[1].metric("CAGR", f"{result.cagr * 100:.1f}%")
cols[2].metric("Sharpe", f"{result.sharpe:.2f}")
cols[3].metric("Max drawdown", f"{result.max_drawdown * 100:.1f}%")
cols[4].metric("Trades", f"{result.num_trades}")
cols[5].metric("Win rate", f"{result.win_rate * 100:.1f}%")

buy_hold = initial_capital * (df["Close"] / df["Close"].iloc[0])

fig = go.Figure()
fig.add_trace(go.Scatter(x=result.equity_curve.index, y=result.equity_curve, name="Strategy"))
fig.add_trace(go.Scatter(x=buy_hold.index, y=buy_hold, name="Buy & hold"))
fig.update_layout(
    title=f"{ticker} — {strategy_name} equity curve",
    yaxis_title="Portfolio value",
    height=450,
)
st.plotly_chart(fig, use_container_width=True)

with st.expander("Position over time"):
    st.line_chart(result.positions)

with st.expander("Raw results"):
    st.dataframe(
        df.assign(position=result.positions, strategy_return=result.returns, equity=result.equity_curve).sort_index(
            ascending=False
        ),
        use_container_width=True,
    )
