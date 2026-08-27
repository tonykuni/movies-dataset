"""
VeritasAutoPlot™ ETF Flow Chart Engine
========================================
# ANCHOR:VAP_CHART_FLOW_ENTRY
Specialized charts for VDF CentralHub LEGO v6 ETF fund flow visualization.
- ETF Category × Ticker Matrix Heatmap
- Dollar Volume Ratio Time Series
- INFLOW/OUTFLOW Event Timeline
- RS Flow Relative Strength
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from .design_system import COLORS, SURFACES


def _flow_layout(**overrides) -> dict:
    """Base layout for flow charts."""
    layout = {
        "template": "plotly_white",
        "plot_bgcolor": "#ffffff",
        "paper_bgcolor": "#ffffff",
        "font": {"family": "'DM Sans', 'Inter', sans-serif", "size": 12, "color": "#1e1d1a"},
        "hovermode": "x unified",
        "showlegend": True,
        "legend": {"orientation": "h", "y": -0.15, "x": 0.5, "xanchor": "center"},
        "margin": {"t": 50, "r": 60, "b": 50, "l": 60},
    }
    layout.update(overrides)
    return layout


# ============================================================
# 1. DVOL RATIO TIME SERIES
# ============================================================

def chart_dvol_ratio(df: pd.DataFrame, title: str = "Dollar Volume Ratio",
                     threshold: float = 2.0) -> go.Figure:
    """Dollar volume ratio with INFLOW/OUTFLOW markers."""
    fig = go.Figure()

    if 'dvol_ratio' not in df.columns:
        return fig

    # Base line
    fig.add_trace(go.Scatter(
        x=df.index, y=df['dvol_ratio'],
        mode='lines', name='DVol Ratio',
        line=dict(color=SURFACES['text_muted'], width=1),
    ))

    # INFLOW markers
    if 'flow_label' in df.columns:
        inflow = df[df['flow_label'] == 'INFLOW']
        if not inflow.empty:
            fig.add_trace(go.Scatter(
                x=inflow.index, y=inflow['dvol_ratio'],
                mode='markers', name='INFLOW',
                marker=dict(color=COLORS['green'], size=6, symbol='triangle-up'),
            ))

        outflow = df[df['flow_label'] == 'OUTFLOW']
        if not outflow.empty:
            fig.add_trace(go.Scatter(
                x=outflow.index, y=outflow['dvol_ratio'],
                mode='markers', name='OUTFLOW',
                marker=dict(color=COLORS['red'], size=6, symbol='triangle-down'),
            ))

    fig.add_hline(y=threshold, line_dash="dot", line_color=COLORS['via_amber'],
                  annotation_text=f"Threshold ({threshold}x)")
    fig.add_hline(y=1.0, line_color=SURFACES['text_faint'], line_width=0.5)

    fig.update_layout(**_flow_layout(title=title, height=350))
    fig.update_xaxes(gridcolor=SURFACES['grid_fusion'])
    fig.update_yaxes(title_text="DVol Ratio", gridcolor=SURFACES['grid_fusion'])
    return fig


# ============================================================
# 2. FLOW SUMMARY BAR (Daily INFLOW/OUTFLOW/NEUTRAL counts)
# ============================================================

def chart_flow_summary(df: pd.DataFrame, title: str = "Daily Flow Summary") -> go.Figure:
    """Stacked bar of daily INFLOW/OUTFLOW/NEUTRAL counts."""
    fig = go.Figure()

    if 'flow_label' not in df.columns:
        return fig

    # Count by date
    counts = df.groupby([df.index, 'flow_label']).size().unstack(fill_value=0)

    for label, color in [('INFLOW', COLORS['green']), ('OUTFLOW', COLORS['red']), ('NEUTRAL', COLORS['gray'])]:
        if label in counts.columns:
            fig.add_trace(go.Bar(
                x=counts.index, y=counts[label],
                name=label, marker_color=color, opacity=0.8,
            ))

    fig.update_layout(**_flow_layout(title=title, height=300, barmode='stack'))
    fig.update_xaxes(gridcolor=SURFACES['grid_fusion'])
    fig.update_yaxes(title_text="Count", gridcolor=SURFACES['grid_fusion'])
    return fig


# ============================================================
# 3. ETF CATEGORY × TICKER HEATMAP
# ============================================================

def chart_etf_matrix(df: pd.DataFrame,
                     value_col: str = 'dvol_ratio',
                     title: str = "ETF Category × Ticker Matrix") -> go.Figure:
    """Heatmap of ETF categories vs tickers."""
    fig = go.Figure()

    if 'etf_category' not in df.columns or value_col not in df.columns:
        return fig

    ticker_col = 'ticker' if 'ticker' in df.columns else df.columns[0]

    # Pivot
    pivot = df.pivot_table(
        values=value_col,
        index='etf_category',
        columns=ticker_col,
        aggfunc='last',
    )

    # Color mapping based on flow labels
    colorscale = [
        [0, COLORS['red']],
        [0.5, SURFACES['bg_alt']],
        [1, COLORS['green']],
    ]

    fig.add_trace(go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale=colorscale,
        text=np.round(pivot.values, 2),
        texttemplate="%{text}",
        textfont={"size": 9},
        hoverongaps=False,
        colorbar=dict(title=value_col, thickness=15),
    ))

    fig.update_layout(**_flow_layout(title=title, height=max(300, len(pivot) * 40 + 100)))
    return fig


# ============================================================
# 4. RS FLOW (Relative Strength)
# ============================================================

def chart_rs_flow(rs_df: pd.DataFrame,
                  target_name: str = "Target",
                  base_name: str = "Base",
                  title: str = "Relative Strength Flow") -> go.Figure:
    """RS Flow time series with trigger zones."""
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[0.6, 0.4], vertical_spacing=0.05)

    if 'RS_flow' in rs_df.columns:
        # Cumulative RS
        rs_cum = rs_df['RS_flow'].cumsum()
        fig.add_trace(go.Scatter(
            x=rs_df.index, y=rs_cum,
            mode='lines', name=f'RS ({target_name}/{base_name})',
            line=dict(color=COLORS['via_blue'], width=2),
        ), row=1, col=1)

    # Individual returns
    if 'Target_Ret' in rs_df.columns:
        fig.add_trace(go.Scatter(
            x=rs_df.index,
            y=(1 + rs_df['Target_Ret']).cumprod() - 1,
            mode='lines', name=target_name,
            line=dict(color=COLORS['green'], width=1.5),
        ), row=2, col=1)

    if 'Base_Ret' in rs_df.columns:
        fig.add_trace(go.Scatter(
            x=rs_df.index,
            y=(1 + rs_df['Base_Ret']).cumprod() - 1,
            mode='lines', name=base_name,
            line=dict(color=COLORS['orange'], width=1.5),
        ), row=2, col=1)

    fig.update_layout(**_flow_layout(title=title, height=500))
    fig.update_yaxes(title_text="Cumulative RS", row=1, col=1, gridcolor=SURFACES['grid_fusion'])
    fig.update_yaxes(title_text="Cumulative Return", row=2, col=1, gridcolor=SURFACES['grid_fusion'])
    fig.update_xaxes(gridcolor=SURFACES['grid_fusion'])
    return fig


# ============================================================
# 5. PRICE + FLOW OVERLAY
# ============================================================

def chart_price_flow_overlay(df: pd.DataFrame,
                             title: str = "Price with Fund Flow Overlay") -> go.Figure:
    """Price chart with INFLOW/OUTFLOW markers and volume bars colored by flow."""
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[0.7, 0.3], vertical_spacing=0.03)

    price_col = 'Main_Price' if 'Main_Price' in df.columns else 'Close' if 'Close' in df.columns else 'close'

    if price_col in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df[price_col],
            mode='lines', name='Price',
            line=dict(color=COLORS['via_blue'], width=2),
        ), row=1, col=1)

    # Flow markers on price
    if 'flow_label' in df.columns and price_col in df.columns:
        inflow = df[df['flow_label'] == 'INFLOW']
        if not inflow.empty:
            fig.add_trace(go.Scatter(
                x=inflow.index, y=inflow[price_col],
                mode='markers', name='INFLOW',
                marker=dict(color=COLORS['green'], size=8, symbol='triangle-up'),
            ), row=1, col=1)

        outflow = df[df['flow_label'] == 'OUTFLOW']
        if not outflow.empty:
            fig.add_trace(go.Scatter(
                x=outflow.index, y=outflow[price_col],
                mode='markers', name='OUTFLOW',
                marker=dict(color=COLORS['red'], size=8, symbol='triangle-down'),
            ), row=1, col=1)

    # Volume colored by flow
    if 'dollar_vol' in df.columns:
        colors = []
        for _, row in df.iterrows():
            label = row.get('flow_label', 'NEUTRAL')
            if label == 'INFLOW':
                colors.append(COLORS['green'])
            elif label == 'OUTFLOW':
                colors.append(COLORS['red'])
            else:
                colors.append(COLORS['gray'])

        fig.add_trace(go.Bar(
            x=df.index, y=df['dollar_vol'],
            name='Dollar Volume', marker_color=colors, opacity=0.6,
        ), row=2, col=1)

    fig.update_layout(**_flow_layout(title=title, height=550))
    fig.update_yaxes(title_text="Price", row=1, col=1, gridcolor=SURFACES['grid_fusion'])
    fig.update_yaxes(title_text="Dollar Volume", row=2, col=1, gridcolor=SURFACES['grid_fusion'])
    fig.update_xaxes(gridcolor=SURFACES['grid_fusion'])
    return fig
