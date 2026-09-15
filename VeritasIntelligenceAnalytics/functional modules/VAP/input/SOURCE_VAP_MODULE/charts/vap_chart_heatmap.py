#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  APM-010: vap_chart_heatmap.py - Heatmap Module                           ║
║  Module ID: APM-010 | Version: 4.0.0                                       ║
║  Correlation matrix, calendar heatmap, sector rotation                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import logging
from typing import List, Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from vap_config import SEABORN_TAB10

logger = logging.getLogger(__name__)


class VAPHeatmapChart:
    """Heatmap variants for correlation, calendar, and sector analysis."""

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def build_correlation(self, columns: List[str] = None,
                          method: str = "pearson") -> go.Figure:
        """Build correlation matrix heatmap."""
        if columns:
            data = self.df[columns].dropna()
        else:
            numeric = self.df.select_dtypes(include=[np.number])
            data = numeric.iloc[:, :20].dropna()

        corr = data.corr(method=method)

        fig = go.Figure(data=go.Heatmap(
            z=corr.values, x=corr.columns.tolist(), y=corr.index.tolist(),
            colorscale="RdBu_r", zmin=-1, zmax=1,
            text=np.round(corr.values, 2), texttemplate="%{text}",
            textfont={"size": 9},
            hovertemplate="%{x} vs %{y}: %{z:.3f}<extra></extra>",
        ))

        fig.update_layout(
            template="plotly_white", height=700, width=800,
            margin={"l": 120, "r": 30, "t": 40, "b": 120},
            xaxis={"tickangle": 45},
        )
        return fig

    def build_calendar(self, value_col: str = None, year: int = None) -> go.Figure:
        """Build calendar heatmap of daily returns."""
        if value_col and value_col in self.df.columns:
            series = self.df[value_col]
        else:
            close_cols = [c for c in self.df.columns if "close" in c.lower()]
            if close_cols:
                series = self.df[close_cols[0]].pct_change() * 100
            else:
                raise ValueError("No suitable column for calendar heatmap")

        if year:
            series = series[series.index.year == year]

        df_cal = pd.DataFrame({"value": series})
        df_cal["weekday"] = df_cal.index.dayofweek
        df_cal["week"] = df_cal.index.isocalendar().week.values

        pivot = df_cal.pivot_table(index="weekday", columns="week",
                                    values="value", aggfunc="mean")

        fig = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=[f"W{w}" for w in pivot.columns],
            y=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][:len(pivot.index)],
            colorscale=[[0, "#C44E52"], [0.5, "#FFFFFF"], [1, "#55A868"]],
            zmid=0,
            hovertemplate="Week %{x}<br>%{y}<br>Return: %{z:.2f}%<extra></extra>",
        ))

        fig.update_layout(
            template="plotly_white", height=300, width=1200,
            margin={"l": 60, "r": 30, "t": 40, "b": 30},
            yaxis={"autorange": "reversed"},
        )
        return fig

    def build_sector_rotation(self, sector_data: pd.DataFrame,
                               window: int = 20) -> go.Figure:
        """
        Build sector rotation heatmap.
        sector_data: DataFrame where each column is a sector/stock,
                     values are prices or returns.
        """
        if sector_data.empty:
            raise ValueError("sector_data is empty")

        # Compute rolling returns
        returns = sector_data.pct_change(window) * 100

        # Use last N periods as columns
        n_show = min(12, len(returns))
        recent = returns.tail(n_show).T

        # Format dates for display
        col_labels = [d.strftime("%m/%d") for d in recent.columns]

        fig = go.Figure(data=go.Heatmap(
            z=recent.values,
            x=col_labels,
            y=recent.index.tolist(),
            colorscale=[[0, "#C44E52"], [0.5, "#F7F7F7"], [1, "#55A868"]],
            zmid=0,
            text=np.round(recent.values, 1),
            texttemplate="%{text}%",
            textfont={"size": 9},
            hovertemplate="%{y}<br>%{x}<br>%{z:.1f}%<extra></extra>",
        ))

        fig.update_layout(
            template="plotly_white",
            height=max(300, len(recent) * 30 + 100),
            width=900,
            margin={"l": 120, "r": 30, "t": 40, "b": 40},
            xaxis={"title": f"Rolling {window}d Return (%)"},
        )
        return fig
