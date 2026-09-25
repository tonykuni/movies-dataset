#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  APM-003: vap_layout.py - Anti-Overlap Layout Engine                       ║
║  Module ID: APM-003 | Version: 4.0.0                                       ║
║  Auto-spacing, responsive sizing, label scatter, annotation placement      ║
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



# === VIA_SUPPORT_BRIDGE_BEGIN ===
# 自動產生(append-only)。原始邏輯未被修改。
# 採 **lazy**:用 PEP 562 的 module-level __getattr__,寫法像 eager(VC.foo),
# 但只有真的存取時才 import —— 支援模組內容未知、可能在 import 時做實際工作,
# 且其中一支損壞時不該拖垮整個 vdf 模組。
import sys as _s, os as _o
_VIA_SUP = r"C:\Users\tonyk\Downloads\movies-dataset\VeritasIntelligenceAnalytics\supportive modules"
if _o.path.isdir(_VIA_SUP) and _VIA_SUP not in _s.path:
    _s.path.insert(0, _VIA_SUP)

_VIA_MAP = {"VEM": "VIA_EnvManager", "VAN": "VeritasAegisNexus",
            "VC": "VeritasCeleritas", "VNS": "VIA_NetSupport"}
_VIA_CACHE = {}
VIA_SUPPORT = {"path": _VIA_SUP, "aliases": dict(_VIA_MAP), "loaded": {}, "errors": {}}

def via_support(name):
    """取得支援模組(別名或全名)。首次呼叫才 import,之後走快取。"""
    mod_name = _VIA_MAP.get(name, name)
    if mod_name in _VIA_CACHE:
        return _VIA_CACHE[mod_name]
    try:
        m = __import__(mod_name)
        _VIA_CACHE[mod_name] = m
        VIA_SUPPORT["loaded"][mod_name] = getattr(m, "__file__", None)
        return m
    except Exception as e:
        VIA_SUPPORT["errors"][mod_name] = "%s: %s" % (type(e).__name__, str(e)[:160])
        _VIA_CACHE[mod_name] = None
        return None

def __getattr__(name):
    # PEP 562:模組層級 __getattr__。讓 VEM/VAN/VC/VNS 可直接當名稱用。
    if name in _VIA_MAP:
        m = via_support(name)
        if m is None:
            raise AttributeError("支援模組 %s 載入失敗: %s"
                                 % (_VIA_MAP[name], VIA_SUPPORT["errors"].get(_VIA_MAP[name])))
        return m
    raise AttributeError(name)

def via_support_status(load_all=False):
    """回報掛載狀態。load_all=True 會強制載入全部(僅供健檢)。"""
    if load_all:
        for a in _VIA_MAP:
            via_support(a)
    return {"path": _VIA_SUP,
            "loaded": dict(VIA_SUPPORT["loaded"]),
            "errors": dict(VIA_SUPPORT["errors"]),
            "available": sorted(_VIA_MAP.values())}
# === VIA_SUPPORT_BRIDGE_END ===


import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class AnnotationBox:
    """Bounding box for an annotation in data coordinates."""
    x: float
    y: float
    width: float
    height: float
    text: str
    priority: int = 0

    @property
    def x_end(self) -> float:
        return self.x + self.width

    @property
    def y_end(self) -> float:
        return self.y + self.height

    def overlaps(self, other: "AnnotationBox") -> bool:
        return not (self.x_end < other.x or other.x_end < self.x or
                    self.y_end < other.y or other.y_end < self.y)


class VAPLayoutEngine:
    """
    Anti-overlap layout engine for chart annotations.
    Handles label spacing, annotation scatter, responsive sizing.
    """

    def __init__(self, chart_width: int = 1920, chart_height: int = 1080,
                 margin_pct: float = 0.05):
        self.chart_width = chart_width
        self.chart_height = chart_height
        self.margin_pct = margin_pct
        self.placed_boxes: List[AnnotationBox] = []

    def resolve_overlaps(self, boxes: List[AnnotationBox],
                         max_iterations: int = 50) -> List[AnnotationBox]:
        """
        Iteratively adjust annotation positions to eliminate overlaps.
        Uses force-directed displacement with priority ordering.
        """
        sorted_boxes = sorted(boxes, key=lambda b: -b.priority)

        for iteration in range(max_iterations):
            has_overlap = False
            for i, box_a in enumerate(sorted_boxes):
                for j, box_b in enumerate(sorted_boxes):
                    if i >= j:
                        continue
                    if box_a.overlaps(box_b):
                        has_overlap = True
                        # Displace lower-priority box
                        target = box_b if box_a.priority >= box_b.priority else box_a
                        dy = (box_a.height + box_b.height) * 0.6
                        if target.y > box_a.y:
                            target.y += dy
                        else:
                            target.y -= dy
            if not has_overlap:
                break

        self.placed_boxes = sorted_boxes
        return sorted_boxes

    def compute_subpanel_heights(self, panels: Dict[str, float],
                                 total_height: int = None) -> Dict[str, int]:
        """
        Compute pixel heights for sub-panels (volume, MACD, RSI, KD).
        panels: dict of {panel_name: height_fraction}
        Remaining height goes to the main price panel.
        """
        total = total_height or self.chart_height
        usable = int(total * (1 - 2 * self.margin_pct))

        sub_total_pct = sum(panels.values())
        main_pct = max(0.3, 1.0 - sub_total_pct)

        heights = {"main": int(usable * main_pct)}
        for name, pct in panels.items():
            heights[name] = int(usable * pct)

        # Adjust rounding
        diff = usable - sum(heights.values())
        heights["main"] += diff

        return heights

    def auto_figsize(self, device: str = "desktop") -> Tuple[int, int]:
        """Return optimal figure size for device type."""
        sizes = {
            "desktop": (1920, 1080),
            "tablet":  (1024, 768),
            "mobile":  (414, 736),
            "print":   (2400, 1600),
        }
        return sizes.get(device, sizes["desktop"])

    def compute_sma_label_positions(self, df: pd.DataFrame,
                                     sma_columns: List[str]) -> List[dict]:
        """
        Compute non-overlapping label positions for SMA lines.
        Places labels at the right edge of the chart, staggered vertically.
        """
        if not sma_columns or df.empty:
            return []

        labels = []
        last_values = []
        for col in sma_columns:
            if col in df.columns:
                val = df[col].dropna().iloc[-1] if not df[col].dropna().empty else None
                if val is not None:
                    last_values.append((col, val))

        # Sort by value and stagger
        last_values.sort(key=lambda x: x[1])
        min_gap = (last_values[-1][1] - last_values[0][1]) * 0.02 if len(last_values) > 1 else 0

        for i, (col, val) in enumerate(last_values):
            adjusted_y = val
            if i > 0:
                prev_y = labels[-1]["y"]
                if abs(adjusted_y - prev_y) < min_gap:
                    adjusted_y = prev_y + min_gap
            labels.append({"column": col, "y": adjusted_y, "text": col.replace("_", " ")})

        return labels
