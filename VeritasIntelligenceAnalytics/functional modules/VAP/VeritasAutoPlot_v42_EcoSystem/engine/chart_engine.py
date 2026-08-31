"""
VeritasAutoPlot™ Chart Engine
==============================
Generates Plotly figures following the locked VIA Fusion design system.
Chart types: Candlestick, Line, Dual-Axis, MACD, RSI, KD, Bubble Radar, Valuation
"""

# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from .design_system import (
    COLORS, SURFACES, FONTS, PLOTLY_LAYOUT, PLOTLY_CONFIG,
    MA_CONFIG, BB_CONFIG, DUAL_AXIS, CANDLE
)


def _base_layout(**overrides) -> dict:
    """Return the locked Veritas layout dict."""
    layout = {
        "template": PLOTLY_LAYOUT["template"],
        "plot_bgcolor": PLOTLY_LAYOUT["plot_bgcolor"],
        "paper_bgcolor": PLOTLY_LAYOUT["paper_bgcolor"],
        "font": {
            "family": PLOTLY_LAYOUT["font_family"],
            "size": PLOTLY_LAYOUT["font_size"],
            "color": PLOTLY_LAYOUT["font_color"],
        },
        "hovermode": PLOTLY_LAYOUT["hovermode"],
        "showlegend": True,
        "legend": {"orientation": "h", "y": -0.15, "x": 0.5, "xanchor": "center"},
        "margin": PLOTLY_LAYOUT["margin"],
    }
    layout.update(overrides)
    return layout


# ============================================================
# 1. PRICE + MA + BB CHART
# ============================================================

def chart_price_ma(df: pd.DataFrame, title: str = "Price & Moving Averages",
                   show_bb: bool = True, show_ma: list = None) -> go.Figure:
    """Line chart with SMA overlays and optional Bollinger Bands."""
    fig = go.Figure()

    # Main price line
    fig.add_trace(go.Scatter(
        x=df.index, y=df['Main_Price'],
        mode='lines', name='Price',
        line=dict(color=COLORS['blue'], width=2),
    ))

    # MA lines
    if show_ma is None:
        show_ma = [k for k, v in MA_CONFIG.items() if v['default_on']]

    for period in show_ma:
        col = f'SMA_{period}'
        if col in df.columns:
            cfg = MA_CONFIG.get(period, {})
            fig.add_trace(go.Scatter(
                x=df.index, y=df[col],
                mode='lines', name=cfg.get('label', col),
                line=dict(color=cfg.get('color', '#888'), width=cfg.get('width', 1)),
            ))

    # Bollinger Bands
    if show_bb and 'BB_Upper' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df['BB_Upper'], mode='lines',
            name='BB Upper', line=dict(color=BB_CONFIG['line_color'], dash='dash', width=1),
        ))
        fig.add_trace(go.Scatter(
            x=df.index, y=df['BB_Lower'], mode='lines',
            name='BB Lower', line=dict(color=BB_CONFIG['line_color'], dash='dash', width=1),
            fill='tonexty', fillcolor=BB_CONFIG['fill_color'],
        ))

    fig.update_layout(**_base_layout(title=title))
    fig.update_xaxes(gridcolor=SURFACES['grid_fusion'])
    fig.update_yaxes(gridcolor=SURFACES['grid_fusion'])
    return fig


# ============================================================
# 2. CANDLESTICK + VOLUME
# ============================================================

def chart_candlestick(df: pd.DataFrame, title: str = "K-Line Chart") -> go.Figure:
    """Candlestick chart with volume subplot."""
    has_ohlc = all(any(c.lower() == n for c in df.columns) for n in ['open', 'high', 'low', 'close'])
    if not has_ohlc:
        return chart_price_ma(df, title=title)

    open_col = next(c for c in df.columns if c.lower() == 'open')
    high_col = next(c for c in df.columns if c.lower() == 'high')
    low_col = next(c for c in df.columns if c.lower() == 'low')
    close_col = next(c for c in df.columns if c.lower() == 'close')

    has_vol = any('vol' in c.lower() for c in df.columns)
    row_heights = [0.75, 0.25] if has_vol else [1.0]
    rows = 2 if has_vol else 1

    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True,
                        row_heights=row_heights, vertical_spacing=0.03)

    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df[open_col], high=df[high_col],
        low=df[low_col], close=df[close_col],
        increasing_line_color=CANDLE['rise_color'],
        decreasing_line_color=CANDLE['fall_color'],
        increasing_fillcolor=CANDLE['rise_color'],
        decreasing_fillcolor=CANDLE['fall_color'],
        name='K-Line',
    ), row=1, col=1)

    if has_vol:
        vol_col = next(c for c in df.columns if 'vol' in c.lower())
        colors = [CANDLE['rise_color'] if df[close_col].iloc[i] >= df[open_col].iloc[i]
                  else CANDLE['fall_color'] for i in range(len(df))]
        fig.add_trace(go.Bar(
            x=df.index, y=df[vol_col], name='Volume',
            marker_color=colors, opacity=0.6,
        ), row=2, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1, gridcolor=SURFACES['grid_fusion'])

    fig.update_layout(**_base_layout(title=title, xaxis_rangeslider_visible=False))
    fig.update_xaxes(gridcolor=SURFACES['grid_fusion'])
    fig.update_yaxes(title_text="Price", row=1, col=1, gridcolor=SURFACES['grid_fusion'])
    return fig


# ============================================================
# 3. MACD CHART
# ============================================================

def chart_macd(df: pd.DataFrame, title: str = "MACD") -> go.Figure:
    """MACD oscillator chart."""
    fig = go.Figure()

    if 'MACD_Hist' in df.columns:
        colors = [COLORS['green'] if v >= 0 else COLORS['red'] for v in df['MACD_Hist']]
        fig.add_trace(go.Bar(
            x=df.index, y=df['MACD_Hist'], name='Histogram',
            marker_color=colors, opacity=0.6,
        ))

    if 'MACD' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df['MACD'], mode='lines', name='MACD',
            line=dict(color=COLORS['blue'], width=1.5),
        ))

    if 'MACD_Signal' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df['MACD_Signal'], mode='lines', name='Signal',
            line=dict(color=COLORS['orange'], width=1.5),
        ))

    fig.add_hline(y=0, line_color=SURFACES['text_muted'], line_width=0.5)
    fig.update_layout(**_base_layout(title=title, height=250))
    fig.update_xaxes(gridcolor=SURFACES['grid_fusion'])
    fig.update_yaxes(gridcolor=SURFACES['grid_fusion'])
    return fig


# ============================================================
# 4. RSI CHART
# ============================================================

def chart_rsi(df: pd.DataFrame, title: str = "RSI (14)") -> go.Figure:
    """RSI oscillator chart with overbought/oversold zones."""
    fig = go.Figure()

    if 'RSI' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df['RSI'], mode='lines', name='RSI',
            line=dict(color=COLORS['purple'], width=1.5),
        ))

    fig.add_hline(y=70, line_dash="dash", line_color=COLORS['red'], line_width=0.8,
                  annotation_text="Overbought (70)")
    fig.add_hline(y=30, line_dash="dash", line_color=COLORS['green'], line_width=0.8,
                  annotation_text="Oversold (30)")
    fig.add_hline(y=50, line_color=SURFACES['text_faint'], line_width=0.5)

    fig.update_layout(**_base_layout(title=title, height=200))
    fig.update_yaxes(range=[0, 100], gridcolor=SURFACES['grid_fusion'])
    fig.update_xaxes(gridcolor=SURFACES['grid_fusion'])
    return fig


# ============================================================
# 5. KD CHART
# ============================================================

def chart_kd(df: pd.DataFrame, title: str = "KD Stochastic") -> go.Figure:
    """KD oscillator chart."""
    fig = go.Figure()

    if 'K' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df['K'], mode='lines', name='K',
            line=dict(color=COLORS['blue'], width=1.5),
        ))
    if 'D' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df['D'], mode='lines', name='D',
            line=dict(color=COLORS['orange'], width=1.5),
        ))

    fig.add_hline(y=80, line_dash="dash", line_color=COLORS['red'], line_width=0.8)
    fig.add_hline(y=20, line_dash="dash", line_color=COLORS['green'], line_width=0.8)

    fig.update_layout(**_base_layout(title=title, height=200))
    fig.update_yaxes(range=[0, 100], gridcolor=SURFACES['grid_fusion'])
    fig.update_xaxes(gridcolor=SURFACES['grid_fusion'])
    return fig


# ============================================================
# 6. DUAL AXIS CHART
# ============================================================

def chart_dual_axis(df: pd.DataFrame, left_col: str, right_col: str,
                    title: str = "Dual Axis Comparison") -> go.Figure:
    """Smart dual-axis chart with correlation stats."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Scatter(
        x=df.index, y=df[left_col], mode='lines', name=left_col,
        line=dict(color=DUAL_AXIS['left_color'], width=2),
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=df.index, y=df[right_col], mode='lines', name=right_col,
        line=dict(color=DUAL_AXIS['right_color'], width=2),
    ), secondary_y=True)

    fig.update_layout(**_base_layout(title=title))
    fig.update_yaxes(title_text=left_col, gridcolor=DUAL_AXIS['left_grid'], secondary_y=False)
    fig.update_yaxes(title_text=right_col, gridcolor=DUAL_AXIS['right_grid'], secondary_y=True)
    fig.update_xaxes(gridcolor=SURFACES['grid_fusion'])
    return fig


# ============================================================
# 7. BUBBLE RADAR CHART
# ============================================================

def chart_bubble_radar(df: pd.DataFrame, threshold: float = 3.0,
                       title: str = "Bubble Radar") -> go.Figure:
    """Two-panel bubble detection chart: Price + Z-Score oscillator."""
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[0.7, 0.3], vertical_spacing=0.05)

    # Price line
    fig.add_trace(go.Scatter(
        x=df.index, y=df['Main_Price'], mode='lines',
        line=dict(color=SURFACES['text_faint'], width=1), name='Price',
    ), row=1, col=1)

    # Bubble markers
    if 'Z_Score' in df.columns:
        bubbles = df[df['Z_Score'] > threshold]
        if not bubbles.empty:
            fig.add_trace(go.Scatter(
                x=bubbles.index, y=bubbles['Main_Price'],
                mode='markers', marker=dict(color=COLORS['red'], size=4),
                name='Bubble Zone',
            ), row=1, col=1)

        oversold = df[df['Z_Score'] < -threshold]
        if not oversold.empty:
            fig.add_trace(go.Scatter(
                x=oversold.index, y=oversold['Main_Price'],
                mode='markers', marker=dict(color=COLORS['green'], size=4),
                name='Oversold Zone',
            ), row=1, col=1)

    # MA240 baseline
    if 'SMA_240' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df['SMA_240'],
            line=dict(color=COLORS['blue'], width=1.5, dash='dash'),
            name='Rational Trend (MA240)',
        ), row=1, col=1)

    # Z-Score oscillator
    if 'Z_Score' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df['Z_Score'],
            line=dict(color=COLORS['orange'], width=1.5),
            name='Bubble Index (Z-Score)', fill='tozeroy',
        ), row=2, col=1)

        fig.add_hline(y=threshold, line_dash="dot", line_color=COLORS['red'],
                      annotation_text=f"Bubble ({threshold}σ)", row=2, col=1)
        fig.add_hline(y=-threshold, line_dash="dot", line_color=COLORS['green'],
                      annotation_text=f"Oversold (-{threshold}σ)", row=2, col=1)
        fig.add_hline(y=0, line_color=SURFACES['text_muted'], line_width=0.5, row=2, col=1)

    fig.update_layout(**_base_layout(title=title, height=600))
    fig.update_yaxes(title_text="Price", row=1, col=1, gridcolor=SURFACES['grid_fusion'])
    fig.update_yaxes(title_text="σ", row=2, col=1, gridcolor=SURFACES['grid_fusion'])
    fig.update_xaxes(gridcolor=SURFACES['grid_fusion'])
    return fig


# ============================================================
# 8. VALUATION CHANNEL CHART
# ============================================================

def chart_valuation(df: pd.DataFrame, title: str = "Valuation Channel") -> go.Figure:
    """Log-linear regression channel with fair value bands."""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df.index, y=df['Main_Price'], mode='lines', name='Price',
        line=dict(color=COLORS['blue'], width=2),
    ))

    if 'Fair_Value' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df['Fair_Value'], mode='lines', name='Fair Value',
            line=dict(color=COLORS['yellow'], width=2, dash='dash'),
        ))

    if 'Overvalued_Line' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df['Overvalued_Line'], mode='lines', name='Overvalued (+2σ)',
            line=dict(color=COLORS['red'], width=1, dash='dot'),
        ))

    if 'Undervalued_Line' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df['Undervalued_Line'], mode='lines', name='Undervalued (-2σ)',
            line=dict(color=COLORS['green'], width=1, dash='dot'),
            fill='tonexty', fillcolor='rgba(85,168,104,0.05)',
        ))

    fig.update_layout(**_base_layout(title=title))
    fig.update_xaxes(gridcolor=SURFACES['grid_fusion'])
    fig.update_yaxes(gridcolor=SURFACES['grid_fusion'])
    return fig


# ============================================================
# 9. DISTRIBUTION CHART
# ============================================================

def chart_distribution(df: pd.DataFrame, title: str = "Return Distribution") -> go.Figure:
    """Histogram of daily returns with normal distribution overlay."""
    fig = go.Figure()

    returns = df['Daily_Ret'].dropna()

    fig.add_trace(go.Histogram(
        x=returns, nbinsx=80, name='Actual Returns',
        marker_color=COLORS['blue'], opacity=0.7,
        histnorm='probability density',
    ))

    # Normal distribution overlay
    x_range = np.linspace(returns.min(), returns.max(), 200)
    from scipy.stats import norm
    mu, std = returns.mean(), returns.std()
    fig.add_trace(go.Scatter(
        x=x_range, y=norm.pdf(x_range, mu, std),
        mode='lines', name='Normal Distribution',
        line=dict(color=SURFACES['text_muted'], width=2, dash='dash'),
    ))

    fig.update_layout(**_base_layout(title=title, height=350))
    fig.update_xaxes(title_text="Daily Return", gridcolor=SURFACES['grid_fusion'])
    fig.update_yaxes(title_text="Density", gridcolor=SURFACES['grid_fusion'])
    return fig


# ============================================================
# 10. DRAWDOWN CHART
# ============================================================

def chart_drawdown(df: pd.DataFrame, title: str = "Underwater Plot (Drawdown)") -> go.Figure:
    """Drawdown visualization showing recovery periods."""
    fig = go.Figure()

    if 'Drawdown' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df['Drawdown'] * 100,
            fill='tozeroy', fillcolor='rgba(196,78,82,0.15)',
            line=dict(color=COLORS['red'], width=1),
            name='Drawdown',
        ))

    fig.add_hline(y=0, line_color=SURFACES['text_muted'], line_width=0.5)
    fig.update_layout(**_base_layout(title=title, height=250))
    fig.update_yaxes(title_text="Drawdown %", gridcolor=SURFACES['grid_fusion'])
    fig.update_xaxes(gridcolor=SURFACES['grid_fusion'])
    return fig


# ============================================================
# 11. FULL STACK CHART (Price + Volume + MACD + RSI)
# ============================================================

def chart_full_stack(df: pd.DataFrame, title: str = "Full Technical Analysis") -> go.Figure:
    """Multi-panel stacked chart: Price+MA, Volume, MACD, RSI."""
    has_vol = any('vol' in c.lower() for c in df.columns)
    panels = 4 if has_vol else 3
    heights = [0.40, 0.12, 0.24, 0.24] if has_vol else [0.45, 0.28, 0.27]

    fig = make_subplots(
        rows=panels, cols=1, shared_xaxes=True,
        row_heights=heights, vertical_spacing=0.03,
        subplot_titles=[title, 'Volume', 'MACD', 'RSI'] if has_vol
                       else [title, 'MACD', 'RSI'],
    )

    # Panel 1: Price + MA
    fig.add_trace(go.Scatter(
        x=df.index, y=df['Main_Price'], mode='lines', name='Price',
        line=dict(color=COLORS['blue'], width=2),
    ), row=1, col=1)

    for period, cfg in MA_CONFIG.items():
        col = f'SMA_{period}'
        if col in df.columns and cfg['default_on']:
            fig.add_trace(go.Scatter(
                x=df.index, y=df[col], mode='lines', name=cfg['label'],
                line=dict(color=cfg['color'], width=cfg['width']),
            ), row=1, col=1)

    # BB
    if 'BB_Upper' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df['BB_Upper'], mode='lines', name='BB Upper',
            line=dict(color=BB_CONFIG['line_color'], dash='dash', width=1),
            showlegend=False,
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=df['BB_Lower'], mode='lines', name='BB Lower',
            line=dict(color=BB_CONFIG['line_color'], dash='dash', width=1),
            fill='tonexty', fillcolor=BB_CONFIG['fill_color'], showlegend=False,
        ), row=1, col=1)

    current_row = 2

    # Panel 2: Volume
    if has_vol:
        vol_col = next(c for c in df.columns if 'vol' in c.lower())
        has_ohlc = all(any(c.lower() == n for c in df.columns) for n in ['open', 'close'])
        if has_ohlc:
            open_c = next(c for c in df.columns if c.lower() == 'open')
            close_c = next(c for c in df.columns if c.lower() == 'close')
            colors = [CANDLE['rise_color'] if df[close_c].iloc[i] >= df[open_c].iloc[i]
                      else CANDLE['fall_color'] for i in range(len(df))]
        else:
            colors = COLORS['blue']
        fig.add_trace(go.Bar(
            x=df.index, y=df[vol_col], name='Volume',
            marker_color=colors, opacity=0.6, showlegend=False,
        ), row=current_row, col=1)
        current_row += 1

    # Panel: MACD
    if 'MACD_Hist' in df.columns:
        hist_colors = [COLORS['green'] if v >= 0 else COLORS['red'] for v in df['MACD_Hist']]
        fig.add_trace(go.Bar(
            x=df.index, y=df['MACD_Hist'], name='MACD Hist',
            marker_color=hist_colors, opacity=0.6, showlegend=False,
        ), row=current_row, col=1)
    if 'MACD' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df['MACD'], mode='lines', name='MACD',
            line=dict(color=COLORS['blue'], width=1.2), showlegend=False,
        ), row=current_row, col=1)
    if 'MACD_Signal' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df['MACD_Signal'], mode='lines', name='Signal',
            line=dict(color=COLORS['orange'], width=1.2), showlegend=False,
        ), row=current_row, col=1)
    fig.add_hline(y=0, line_color=SURFACES['text_muted'], line_width=0.5, row=current_row, col=1)
    current_row += 1

    # Panel: RSI
    if 'RSI' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df['RSI'], mode='lines', name='RSI',
            line=dict(color=COLORS['purple'], width=1.5), showlegend=False,
        ), row=current_row, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color=COLORS['red'], line_width=0.5, row=current_row, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color=COLORS['green'], line_width=0.5, row=current_row, col=1)

    fig.update_layout(**_base_layout(height=900))
    for i in range(1, panels + 1):
        fig.update_yaxes(gridcolor=SURFACES['grid_fusion'], row=i, col=1)
        fig.update_xaxes(gridcolor=SURFACES['grid_fusion'], row=i, col=1)

    return fig
