#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  APM-008: vap_chart_twoaxis.py - Dual Y-Axis Comparison Chart             ║
║  Module ID: APM-008 | Version: 4.0.0                                       ║
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
from typing import Optional
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from vap_config import SEABORN_TAB10, get_price_column

logger = logging.getLogger(__name__)


class VAPTwoAxisChart:
    """Dual Y-axis comparison chart with correlation statistics."""

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def build(self, left_col: str, right_col: str,
              left_type: str = "line", right_type: str = "bar",
              left_label: str = None, right_label: str = None,
              show_correlation: bool = True) -> go.Figure:

        left_label = left_label or left_col
        right_label = right_label or right_col

        fig = go.Figure()

        # Left axis
        if left_type == "line":
            fig.add_trace(go.Scatter(
                x=self.df.index, y=self.df[left_col],
                mode="lines", name=left_label,
                line={"color": SEABORN_TAB10[0], "width": 1.5},
                yaxis="y1",
            ))
        elif left_type == "bar":
            fig.add_trace(go.Bar(
                x=self.df.index, y=self.df[left_col],
                name=left_label, marker_color=SEABORN_TAB10[0],
                opacity=0.6, yaxis="y1",
            ))

        # Right axis
        if right_type == "line":
            fig.add_trace(go.Scatter(
                x=self.df.index, y=self.df[right_col],
                mode="lines", name=right_label,
                line={"color": SEABORN_TAB10[1], "width": 1.5},
                yaxis="y2",
            ))
        elif right_type == "bar":
            fig.add_trace(go.Bar(
                x=self.df.index, y=self.df[right_col],
                name=right_label, marker_color=SEABORN_TAB10[1],
                opacity=0.4, yaxis="y2",
            ))

        # Correlation annotation
        annotations = []
        if show_correlation:
            valid = self.df[[left_col, right_col]].dropna()
            if len(valid) > 10:
                corr = valid[left_col].corr(valid[right_col])
                r_sq = corr ** 2
                annotations.append({
                    "x": 0.02, "y": 0.98, "xref": "paper", "yref": "paper",
                    "text": f"R={corr:.3f} | R\u00B2={r_sq:.3f}",
                    "showarrow": False,
                    "font": {"size": 12, "color": "#333", "family": "JetBrains Mono"},
                    "bgcolor": "rgba(255,255,255,0.8)",
                    "borderpad": 4,
                })

        fig.update_layout(
            template="plotly_white",
            yaxis={"title": left_label, "titlefont": {"color": SEABORN_TAB10[0]},
                   "tickfont": {"color": SEABORN_TAB10[0]}},
            yaxis2={"title": right_label, "titlefont": {"color": SEABORN_TAB10[1]},
                    "tickfont": {"color": SEABORN_TAB10[1]},
                    "overlaying": "y", "side": "right"},
            height=700, width=1920,
            margin={"l": 70, "r": 70, "t": 30, "b": 30},
            legend={"orientation": "h", "y": 1.05},
            hovermode="x unified",
            annotations=annotations,
        )
        return fig
