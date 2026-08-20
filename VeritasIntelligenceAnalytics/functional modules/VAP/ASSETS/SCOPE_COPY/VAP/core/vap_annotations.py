#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  APM-004: vap_annotations.py - Chart Annotation Engine                     ║
║  Module ID: APM-004 | Version: 4.0.0                                       ║
║  Crisis shading, event vertical lines, high/low markers, auto-scatter      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

import numpy as np
import pandas as pd

from vap_config import CRISIS_PALETTE, get_price_column

logger = logging.getLogger(__name__)


@dataclass
class EventLine:
    date: datetime
    label: str
    color: str = "#888888"
    line_width: float = 1.0
    line_dash: str = "dash"


@dataclass
class HighLowMarker:
    date: datetime
    price: float
    marker_type: str  # "high" or "low"
    label: str = ""


@dataclass
class CrisisZone:
    start_date: datetime
    end_date: datetime
    drawdown_pct: float
    color: str = ""


class VAPAnnotationEngine:
    """
    Generates chart annotations: crisis shading, event lines, high/low markers.
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self._close_col = get_price_column(df)

    def detect_crisis_zones(self, threshold: float = 0.10) -> List[CrisisZone]:
        """
        Detect drawdown periods exceeding threshold.
        Uses rolling peak and drawdown calculation.
        """
        close = self.df[self._close_col]
        rolling_max = close.expanding().max()
        drawdown = (close - rolling_max) / rolling_max

        zones = []
        in_crisis = False
        start_date = None
        max_dd = 0

        for i, (date, dd) in enumerate(drawdown.items()):
            if dd < -threshold and not in_crisis:
                in_crisis = True
                start_date = date
                max_dd = dd
            elif dd < -threshold and in_crisis:
                max_dd = min(max_dd, dd)
            elif dd >= -threshold and in_crisis:
                in_crisis = False
                # Map intensity to color
                intensity = min(7, int(abs(max_dd) / threshold * 4))
                zones.append(CrisisZone(
                    start_date=start_date, end_date=date,
                    drawdown_pct=max_dd,
                    color=CRISIS_PALETTE[min(intensity, len(CRISIS_PALETTE) - 1)]
                ))
                max_dd = 0

        # Close open zone
        if in_crisis and start_date is not None:
            intensity = min(7, int(abs(max_dd) / threshold * 4))
            zones.append(CrisisZone(
                start_date=start_date, end_date=self.df.index[-1],
                drawdown_pct=max_dd,
                color=CRISIS_PALETTE[min(intensity, len(CRISIS_PALETTE) - 1)]
            ))

        logger.info(f"Detected {len(zones)} crisis zones (threshold={threshold:.0%})")
        return zones

    def find_high_low(self, window: Optional[int] = None) -> Tuple[HighLowMarker, HighLowMarker]:
        """
        Find period high and low with dates.
        If window is None, uses the entire dataset.
        """
        close = self.df[self._close_col]
        if window:
            close = close.iloc[-window:]

        high_idx = close.idxmax()
        low_idx = close.idxmin()
        high_val = close[high_idx]
        low_val = close[low_idx]

        high_marker = HighLowMarker(
            date=high_idx, price=high_val, marker_type="high",
            label=f"High: {high_val:,.2f} ({high_idx.strftime('%Y-%m-%d')})"
        )
        low_marker = HighLowMarker(
            date=low_idx, price=low_val, marker_type="low",
            label=f"Low: {low_val:,.2f} ({low_idx.strftime('%Y-%m-%d')})"
        )
        return high_marker, low_marker

    def create_event_lines(self, events: Dict[str, str]) -> List[EventLine]:
        """
        Create event vertical lines from dict of {date_str: label}.
        """
        lines = []
        for date_str, label in events.items():
            try:
                dt = pd.to_datetime(date_str)
                lines.append(EventLine(date=dt, label=label))
            except Exception:
                logger.warning(f"Invalid event date: {date_str}")
        return lines

    def to_plotly_shapes(self, crisis_zones: List[CrisisZone]) -> List[dict]:
        """Convert crisis zones to Plotly shape dicts."""
        shapes = []
        for zone in crisis_zones:
            shapes.append({
                "type": "rect",
                "xref": "x", "yref": "paper",
                "x0": zone.start_date, "x1": zone.end_date,
                "y0": 0, "y1": 1,
                "fillcolor": zone.color, "opacity": 0.15,
                "line": {"width": 0},
                "layer": "below",
            })
        return shapes

    def to_plotly_vlines(self, event_lines: List[EventLine]) -> List[dict]:
        """Convert event lines to Plotly shape dicts."""
        shapes = []
        for ev in event_lines:
            shapes.append({
                "type": "line",
                "xref": "x", "yref": "paper",
                "x0": ev.date, "x1": ev.date,
                "y0": 0, "y1": 1,
                "line": {"color": ev.color, "width": ev.line_width, "dash": ev.line_dash},
            })
        return shapes

    def to_plotly_annotations(self, high: HighLowMarker, low: HighLowMarker) -> List[dict]:
        """Convert high/low markers to Plotly annotation dicts."""
        return [
            {
                "x": high.date, "y": high.price,
                "text": high.label, "showarrow": True,
                "arrowhead": 2, "arrowcolor": "#E15241",
                "font": {"size": 10, "color": "#E15241"},
                "ax": 40, "ay": -30,
            },
            {
                "x": low.date, "y": low.price,
                "text": low.label, "showarrow": True,
                "arrowhead": 2, "arrowcolor": "#22AB94",
                "font": {"size": 10, "color": "#22AB94"},
                "ax": 40, "ay": 30,
            },
        ]
