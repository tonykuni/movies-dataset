#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  APM-011: vap_chart_dashboard.py - Dashboard Grid Compositor               ║
║  Module ID: APM-011 | Version: 4.0.0                                       ║
║  Grid-based KPI cards + multi-chart composite layout                      ║
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
from typing import List, Dict, Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from vap_config import SEABORN_TAB10, UP_COLOR, DOWN_COLOR, get_price_column

logger = logging.getLogger(__name__)


class VAPDashboard:
    """
    Grid-based dashboard compositor.
    Combines KPI indicators, sparklines, and embedded chart modules
    into a single composite figure.
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self._close_col = get_price_column(df)

    def compute_kpis(self) -> Dict[str, dict]:
        """Compute standard KPI metrics from DataFrame."""
        close = self.df[self._close_col]
        kpis = {}

        # Current Price
        last_price = close.iloc[-1]
        prev_price = close.iloc[-2] if len(close) > 1 else last_price
        change = last_price - prev_price
        change_pct = (change / prev_price * 100) if prev_price != 0 else 0
        kpis["price"] = {
            "label": "Last Price", "value": f"{last_price:,.2f}",
            "change": f"{change:+.2f} ({change_pct:+.2f}%)",
            "color": UP_COLOR if change >= 0 else DOWN_COLOR,
        }

        # Volume
        if "volume" in self.df.columns:
            vol = self.df["volume"].iloc[-1]
            vol_avg = self.df["volume"].rolling(20).mean().iloc[-1]
            vol_ratio = vol / vol_avg if vol_avg > 0 else 0
            kpis["volume"] = {
                "label": "Volume", "value": f"{vol:,.0f}",
                "change": f"vs Avg: {vol_ratio:.1f}x",
                "color": UP_COLOR if vol_ratio >= 1 else DOWN_COLOR,
            }

        # RSI
        rsi_col = [c for c in self.df.columns if c.startswith("RSI_")]
        if rsi_col:
            rsi_val = self.df[rsi_col[0]].iloc[-1]
            rsi_status = "Overbought" if rsi_val > 70 else ("Oversold" if rsi_val < 30 else "Neutral")
            kpis["rsi"] = {
                "label": f"RSI", "value": f"{rsi_val:.1f}",
                "change": rsi_status,
                "color": DOWN_COLOR if rsi_val > 70 else (UP_COLOR if rsi_val < 30 else "#888"),
            }

        # MACD
        if "MACD_HIST" in self.df.columns:
            hist = self.df["MACD_HIST"].iloc[-1]
            hist_prev = self.df["MACD_HIST"].iloc[-2] if len(self.df) > 1 else 0
            trend = "Bullish" if hist > 0 else "Bearish"
            momentum = "Increasing" if abs(hist) > abs(hist_prev) else "Decreasing"
            kpis["macd"] = {
                "label": "MACD Hist", "value": f"{hist:.4f}",
                "change": f"{trend} ({momentum})",
                "color": UP_COLOR if hist > 0 else DOWN_COLOR,
            }

        # ATR
        atr_col = [c for c in self.df.columns if c.startswith("ATR_")]
        if atr_col:
            atr_val = self.df[atr_col[0]].iloc[-1]
            atr_pct = (atr_val / last_price * 100) if last_price > 0 else 0
            kpis["atr"] = {
                "label": "ATR", "value": f"{atr_val:.2f}",
                "change": f"{atr_pct:.2f}% of price",
                "color": "#888",
            }

        # Performance stats
        if len(close) > 5:
            ret_5d = (close.iloc[-1] / close.iloc[-6] - 1) * 100 if len(close) > 5 else 0
            ret_20d = (close.iloc[-1] / close.iloc[-21] - 1) * 100 if len(close) > 20 else 0
            kpis["perf_5d"] = {
                "label": "5D Return", "value": f"{ret_5d:+.2f}%",
                "change": "", "color": UP_COLOR if ret_5d >= 0 else DOWN_COLOR,
            }
            kpis["perf_20d"] = {
                "label": "20D Return", "value": f"{ret_20d:+.2f}%",
                "change": "", "color": UP_COLOR if ret_20d >= 0 else DOWN_COLOR,
            }

        return kpis

    def build(self, grid_rows: int = 3, grid_cols: int = 3) -> go.Figure:
        """
        Build dashboard with KPI sparklines and summary charts.
        Top row: KPI indicator numbers
        Middle: Price chart with SMA
        Bottom: Volume + MACD side by side
        """
        close = self.df[self._close_col]
        kpis = self.compute_kpis()

        fig = make_subplots(
            rows=3, cols=3,
            specs=[
                [{"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}],
                [{"type": "xy", "colspan": 3}, None, None],
                [{"type": "xy", "colspan": 2}, None, {"type": "xy"}],
            ],
            row_heights=[0.15, 0.50, 0.35],
            vertical_spacing=0.06, horizontal_spacing=0.04,
            subplot_titles=["", "", "", "Price & Moving Averages", "", "Volume"],
        )

        # Row 1: KPI Indicators
        kpi_list = list(kpis.values())[:3]
        for i, kpi in enumerate(kpi_list):
            fig.add_trace(go.Indicator(
                mode="number+delta",
                value=float(kpi["value"].replace(",", "").replace("%", "").replace("+", "")),
                title={"text": kpi["label"], "font": {"size": 13}},
                number={"font": {"size": 22, "color": kpi["color"]}},
            ), row=1, col=i + 1)

        # Row 2: Price chart with SMAs
        fig.add_trace(go.Scatter(
            x=self.df.index, y=close,
            mode="lines", name="Price",
            line={"color": SEABORN_TAB10[0], "width": 1.5},
        ), row=2, col=1)

        # Add available SMAs
        for sma_col in sorted([c for c in self.df.columns if c.startswith("SMA_")]):
            period = sma_col.split("_")[1]
            fig.add_trace(go.Scatter(
                x=self.df.index, y=self.df[sma_col],
                mode="lines", name=f"SMA {period}",
                line={"width": 0.8}, opacity=0.7,
            ), row=2, col=1)

        # Row 3 left: Volume
        if "volume" in self.df.columns:
            vol_colors = [UP_COLOR if close.iloc[i] >= close.iloc[max(0, i - 1)]
                          else DOWN_COLOR for i in range(len(self.df))]
            fig.add_trace(go.Bar(
                x=self.df.index, y=self.df["volume"],
                marker_color=vol_colors, name="Volume",
                opacity=0.5, showlegend=False,
            ), row=3, col=1)

        # Row 3 right: RSI
        rsi_cols = [c for c in self.df.columns if c.startswith("RSI_")]
        if rsi_cols:
            fig.add_trace(go.Scatter(
                x=self.df.index, y=self.df[rsi_cols[0]],
                mode="lines", name="RSI",
                line={"color": SEABORN_TAB10[4], "width": 1.2},
                showlegend=False,
            ), row=3, col=3)
            fig.add_hline(y=70, line_dash="dash", line_color="#ccc",
                          line_width=0.5, row=3, col=3)
            fig.add_hline(y=30, line_dash="dash", line_color="#ccc",
                          line_width=0.5, row=3, col=3)

        fig.update_layout(
            template="plotly_white", height=900, width=1920,
            margin={"l": 50, "r": 30, "t": 40, "b": 30},
            showlegend=True,
            legend={"orientation": "h", "y": 0.62, "x": 0, "font": {"size": 9}},
            hovermode="x unified",
        )

        # Remove rangesliders
        for ax in ["xaxis", "xaxis2", "xaxis3", "xaxis4"]:
            if ax in fig.layout:
                fig.layout[ax].rangeslider = {"visible": False}

        return fig
