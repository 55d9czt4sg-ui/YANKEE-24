"""Plotly chart builders for price/volume/indicator visualization."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def candlestick_chart(
    df: pd.DataFrame,
    title: str = "",
    overlays: dict[str, pd.Series] | None = None,
    indicator_panels: dict[str, pd.DataFrame | pd.Series] | None = None,
    show_volume: bool = True,
) -> go.Figure:
    """Build a candlestick chart with optional overlays and indicator subplots.

    Args:
        df: OHLCV DataFrame with Open, High, Low, Close, Volume columns.
        title: chart title.
        overlays: series plotted on the price panel (e.g. moving
            averages, Bollinger bands), keyed by trace name.
        indicator_panels: each entry adds a separate subplot row below
            the price/volume panels. Values may be a Series (single
            line) or a DataFrame (one line per column), keyed by panel
            name (used as the y-axis title).
        show_volume: whether to include a volume subplot.

    Returns:
        A plotly Figure.
    """
    overlays = overlays or {}
    indicator_panels = indicator_panels or {}

    panel_names = list(indicator_panels.keys())
    n_rows = 1 + (1 if show_volume else 0) + len(panel_names)

    row_heights = [0.5] if show_volume or panel_names else [1.0]
    if show_volume:
        row_heights = [0.5, 0.15] + [0.35 / max(len(panel_names), 1)] * len(panel_names)
        if not panel_names:
            row_heights = [0.7, 0.3]
    elif panel_names:
        row_heights = [0.6] + [0.4 / len(panel_names)] * len(panel_names)
    else:
        row_heights = [1.0]

    # Normalize so heights sum to 1.
    total = sum(row_heights)
    row_heights = [h / total for h in row_heights]

    fig = make_subplots(
        rows=n_rows,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=row_heights,
    )

    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="Price",
        ),
        row=1,
        col=1,
    )

    for name, series in overlays.items():
        fig.add_trace(
            go.Scatter(x=series.index, y=series, mode="lines", name=name),
            row=1,
            col=1,
        )

    current_row = 2
    if show_volume:
        colors = [
            "green" if c >= o else "red"
            for o, c in zip(df["Open"], df["Close"])
        ]
        fig.add_trace(
            go.Bar(x=df.index, y=df["Volume"], name="Volume", marker_color=colors),
            row=current_row,
            col=1,
        )
        fig.update_yaxes(title_text="Volume", row=current_row, col=1)
        current_row += 1

    for panel_name, panel_data in indicator_panels.items():
        if isinstance(panel_data, pd.Series):
            fig.add_trace(
                go.Scatter(x=panel_data.index, y=panel_data, mode="lines", name=panel_name),
                row=current_row,
                col=1,
            )
        else:
            for col_name in panel_data.columns:
                fig.add_trace(
                    go.Scatter(
                        x=panel_data.index,
                        y=panel_data[col_name],
                        mode="lines",
                        name=f"{panel_name} {col_name}",
                    ),
                    row=current_row,
                    col=1,
                )
        fig.update_yaxes(title_text=panel_name, row=current_row, col=1)
        current_row += 1

    fig.update_layout(
        title=title,
        xaxis_rangeslider_visible=False,
        height=350 + 150 * (n_rows - 1),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=20, t=60, b=20),
    )

    return fig
