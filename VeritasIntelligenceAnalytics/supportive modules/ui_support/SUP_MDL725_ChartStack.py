#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  APM-009: vap_chart_stack.py - Vertical Stack Multi-Panel Chart            ║
║  Module ID: APM-009 | Version: 4.0.0                                       ║
║  Up to 6 synchronized panels with shared X-axis                           ║
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
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from vap_config import SEABORN_TAB10, UP_COLOR, DOWN_COLOR

logger = logging.getLogger(__name__)


class VAPStackChart:
    """Vertical stack of synchronized panels."""

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def build(self, panels: List[Dict], heights: List[float] = None) -> go.Figure:
        """
        Build stacked chart.
        panels: list of dicts with keys:
            - columns: list of column names to plot
            - chart_type: "line" | "bar" | "area"
            - title: panel title
            - colors: optional color list
        """
        n = len(panels)
        if not heights:
            heights = [1.0 / n] * n

        titles = [p.get("title", "") for p in panels]
        fig = make_subplots(
            rows=n, cols=1, shared_xaxes=True,
            vertical_spacing=0.03, row_heights=heights,
            subplot_titles=titles,
        )

        for i, panel in enumerate(panels):
            row = i + 1
            columns = panel.get("columns", [])
            chart_type = panel.get("chart_type", "line")
            colors = panel.get("colors", SEABORN_TAB10)

            for j, col in enumerate(columns):
                if col not in self.df.columns:
                    continue
                color = colors[j % len(colors)]

                if chart_type == "line":
                    fig.add_trace(go.Scatter(
                        x=self.df.index, y=self.df[col],
                        mode="lines", name=col,
                        line={"color": color, "width": 1.2},
                    ), row=row, col=1)
                elif chart_type == "bar":
                    bar_colors = [UP_COLOR if v >= 0 else DOWN_COLOR for v in self.df[col]]
                    fig.add_trace(go.Bar(
                        x=self.df.index, y=self.df[col],
                        marker_color=bar_colors, name=col, opacity=0.6,
                    ), row=row, col=1)
                elif chart_type == "area":
                    fig.add_trace(go.Scatter(
                        x=self.df.index, y=self.df[col],
                        mode="lines", name=col, fill="tozeroy",
                        line={"color": color, "width": 1.0},
                        fillcolor=color.replace(")", ",0.15)").replace("rgb", "rgba")
                        if "rgb" in color else color + "26",
                    ), row=row, col=1)

        fig.update_layout(
            template="plotly_white", height=200 * n + 100, width=1920,
            margin={"l": 60, "r": 30, "t": 40, "b": 30},
            legend={"orientation": "h", "y": 1.02},
            hovermode="x unified",
        )
        for i in range(1, n + 1):
            fig.update_xaxes(rangeslider_visible=False, row=i, col=1)

        return fig
