#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  APM-007: vap_chart_technical.py - Technical Analysis Chart                ║
║  Module ID: APM-007 | Version: 4.0.0                                       ║
║  K-line + SMA/EMA/BB overlays + Volume/MACD/RSI/KD sub-panels            ║
║  Uses adj_close priority throughout                                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
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

import logging
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from vap_config import (
    SEABORN_TAB10, UP_COLOR, DOWN_COLOR, ChartDefaults, CHART_DEFAULTS,
    get_price_column, resolve_ohlcv_columns,
)

logger = logging.getLogger(__name__)


class VAPTechnicalChart:
    """
    Builds a comprehensive technical analysis chart with configurable
    overlays and sub-panels using Plotly.
    """

    def __init__(self, df: pd.DataFrame, config: Optional[ChartDefaults] = None):
        self.df = df
        self.cfg = config or CHART_DEFAULTS
        self.col_map = resolve_ohlcv_columns(df)

    def build(self) -> go.Figure:
        """Build the complete technical chart figure."""
        # Determine sub-panels
        panels = ["price"]
        panel_heights = [0.45]

        if self.cfg.volume_enabled:
            panels.append("volume")
            panel_heights.append(self.cfg.volume_height_pct)
        if self.cfg.macd_enabled:
            panels.append("macd")
            panel_heights.append(self.cfg.macd_height_pct)
        if self.cfg.rsi_enabled:
            panels.append("rsi")
            panel_heights.append(self.cfg.rsi_height_pct)
        if self.cfg.kd_enabled:
            panels.append("kd")
            panel_heights.append(self.cfg.kd_height_pct)

        # Normalize heights
        total = sum(panel_heights)
        panel_heights = [h / total for h in panel_heights]

        fig = make_subplots(
            rows=len(panels), cols=1, shared_xaxes=True,
            vertical_spacing=0.02, row_heights=panel_heights,
            subplot_titles=[None] * len(panels),
        )

        row_map = {name: i + 1 for i, name in enumerate(panels)}
        price_row = row_map["price"]

        # ─── Price Panel ────────────────────────────────────
        o = self.col_map.get("open")
        h = self.col_map.get("high")
        l = self.col_map.get("low")
        c = self.col_map.get("close")

        if self.cfg.chart_type == "candlestick" and o and h and l:
            fig.add_trace(go.Candlestick(
                x=self.df.index, open=self.df[o], high=self.df[h],
                low=self.df[l], close=self.df[c],
                increasing_line_color=UP_COLOR, decreasing_line_color=DOWN_COLOR,
                name="Price", showlegend=False,
            ), row=price_row, col=1)
        else:
            fig.add_trace(go.Scatter(
                x=self.df.index, y=self.df[c],
                mode="lines", name="Close",
                line={"color": SEABORN_TAB10[0], "width": self.cfg.line_width},
            ), row=price_row, col=1)

        # ─── SMA Overlays ──────────────────────────────────
        sma_colors = [SEABORN_TAB10[i % len(SEABORN_TAB10)] for i in range(len(self.cfg.sma_active))]
        for i, period in enumerate(self.cfg.sma_active):
            col_name = f"SMA_{period}"
            if col_name in self.df.columns:
                fig.add_trace(go.Scatter(
                    x=self.df.index, y=self.df[col_name],
                    mode="lines", name=f"SMA {period}",
                    line={"color": sma_colors[i], "width": 1.0, "dash": "solid"},
                    opacity=0.8,
                ), row=price_row, col=1)

        # ─── EMA Overlays ──────────────────────────────────
        for i, period in enumerate(self.cfg.ema_active):
            col_name = f"EMA_{period}"
            if col_name in self.df.columns:
                fig.add_trace(go.Scatter(
                    x=self.df.index, y=self.df[col_name],
                    mode="lines", name=f"EMA {period}",
                    line={"color": SEABORN_TAB10[(i + 5) % 10], "width": 1.0, "dash": "dot"},
                    opacity=0.8,
                ), row=price_row, col=1)

        # ─── Bollinger Bands ───────────────────────────────
        if all(c in self.df.columns for c in ["BB_UPPER", "BB_MIDDLE", "BB_LOWER"]):
            fig.add_trace(go.Scatter(
                x=self.df.index, y=self.df["BB_UPPER"],
                mode="lines", name="BB Upper",
                line={"color": "#8172B3", "width": 0.8, "dash": "dash"},
                opacity=0.5, showlegend=False,
            ), row=price_row, col=1)
            fig.add_trace(go.Scatter(
                x=self.df.index, y=self.df["BB_LOWER"],
                mode="lines", name="BB Lower",
                line={"color": "#8172B3", "width": 0.8, "dash": "dash"},
                fill="tonexty", fillcolor="rgba(129,114,179,0.08)",
                opacity=0.5, showlegend=False,
            ), row=price_row, col=1)

        # ─── SAR ──────────────────────────────────────────
        if "SAR" in self.df.columns and self.cfg.vwap_enabled:
            fig.add_trace(go.Scatter(
                x=self.df.index, y=self.df["SAR"],
                mode="markers", name="SAR",
                marker={"color": "#DA8BC3", "size": 2},
            ), row=price_row, col=1)

        # ─── Volume Panel ──────────────────────────────────
        if "volume" in row_map:
            vol_col = self.col_map.get("volume")
            if vol_col and vol_col in self.df.columns:
                colors = [UP_COLOR if self.df[c].iloc[i] >= self.df[c].iloc[max(0, i - 1)]
                          else DOWN_COLOR for i in range(len(self.df))]
                fig.add_trace(go.Bar(
                    x=self.df.index, y=self.df[vol_col],
                    marker_color=colors, name="Volume",
                    opacity=0.6, showlegend=False,
                ), row=row_map["volume"], col=1)

        # ─── MACD Panel ───────────────────────────────────
        if "macd" in row_map:
            if "MACD" in self.df.columns:
                fig.add_trace(go.Scatter(
                    x=self.df.index, y=self.df["MACD"],
                    mode="lines", name="MACD",
                    line={"color": SEABORN_TAB10[0], "width": 1.2},
                ), row=row_map["macd"], col=1)
            if "MACD_SIGNAL" in self.df.columns:
                fig.add_trace(go.Scatter(
                    x=self.df.index, y=self.df["MACD_SIGNAL"],
                    mode="lines", name="Signal",
                    line={"color": SEABORN_TAB10[1], "width": 1.0},
                ), row=row_map["macd"], col=1)
            if "MACD_HIST" in self.df.columns:
                colors = [UP_COLOR if v >= 0 else DOWN_COLOR for v in self.df["MACD_HIST"]]
                fig.add_trace(go.Bar(
                    x=self.df.index, y=self.df["MACD_HIST"],
                    marker_color=colors, name="Histogram",
                    opacity=0.5, showlegend=False,
                ), row=row_map["macd"], col=1)

        # ─── RSI Panel ────────────────────────────────────
        if "rsi" in row_map:
            rsi_col = f"RSI_{self.cfg.rsi_period}"
            if rsi_col in self.df.columns:
                fig.add_trace(go.Scatter(
                    x=self.df.index, y=self.df[rsi_col],
                    mode="lines", name=f"RSI({self.cfg.rsi_period})",
                    line={"color": SEABORN_TAB10[4], "width": 1.2},
                ), row=row_map["rsi"], col=1)
                # Overbought/Oversold lines
                for level in [70, 30]:
                    fig.add_hline(y=level, line_dash="dash", line_color="#888",
                                 line_width=0.5, row=row_map["rsi"], col=1)

        # ─── KD Panel ─────────────────────────────────────
        if "kd" in row_map:
            if "STOCH_K" in self.df.columns:
                fig.add_trace(go.Scatter(
                    x=self.df.index, y=self.df["STOCH_K"],
                    mode="lines", name="K",
                    line={"color": SEABORN_TAB10[0], "width": 1.0},
                ), row=row_map["kd"], col=1)
            if "STOCH_D" in self.df.columns:
                fig.add_trace(go.Scatter(
                    x=self.df.index, y=self.df["STOCH_D"],
                    mode="lines", name="D",
                    line={"color": SEABORN_TAB10[1], "width": 1.0},
                ), row=row_map["kd"], col=1)
                for level in [80, 20]:
                    fig.add_hline(y=level, line_dash="dash", line_color="#888",
                                 line_width=0.5, row=row_map["kd"], col=1)

        # ─── Layout ───────────────────────────────────────
        fig.update_layout(
            title=None,
            template="plotly_white",
            font={"family": self.cfg.font_family, "size": 11},
            xaxis_rangeslider_visible=False,
            height=1080, width=1920,
            margin={"l": 60, "r": 30, "t": 30, "b": 30},
            legend={"orientation": "h", "y": 1.02, "x": 0, "font": {"size": 10}},
            hovermode="x unified",
        )

        # Hide rangeslider for all x-axes
        for i in range(1, len(panels) + 1):
            fig.update_xaxes(rangeslider_visible=False, row=i, col=1)

        return fig
