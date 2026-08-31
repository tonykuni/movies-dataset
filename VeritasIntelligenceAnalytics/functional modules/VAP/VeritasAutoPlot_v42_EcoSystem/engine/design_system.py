"""
VeritasAutoPlot™ Design System Constants
=========================================
Visual Language: VIA FusionDashboard × Notion × MUJI × Seaborn
Version: v4.0 (Locked)

This module defines ALL visual constants used across the entire system.
NO other module should hardcode colors, fonts, or sizes.
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
# ============================================================
# 1. COLOR PALETTE — Seaborn Deep + VIA Fusion Accents
# ============================================================

COLORS = {
    # --- Seaborn Deep (Primary Data Colors) ---
    "blue":     "#4C72B0",
    "orange":   "#DD8452",
    "green":    "#55A868",
    "red":      "#C44E52",
    "purple":   "#8172B3",
    "brown":    "#937860",
    "pink":     "#DA8BC3",
    "gray":     "#8C8C8C",
    "yellow":   "#CCB974",
    "cyan":     "#64B5CD",

    # --- VIA Fusion Accent Colors ---
    "via_blue":   "#4c78a8",
    "via_teal":   "#439a9a",
    "via_green":  "#5a9e6f",
    "via_amber":  "#c4943a",
    "via_coral":  "#c96b5a",
    "via_violet": "#7a6daa",
    "via_rose":   "#b05580",

    # --- Functional Colors ---
    "rise":     "#55A868",
    "fall":     "#C44E52",
    "neutral":  "#8C8C8C",
    "bubble":   "#E74C3C",
    "oversold": "#27AE60",
}

# ============================================================
# 2. BACKGROUND & SURFACE — Notion/MUJI + VIA Fusion
# ============================================================

SURFACES = {
    # --- Light Theme (VIA Fusion) ---
    "bg_page":      "#f5f4f0",
    "bg_alt":       "#edecea",
    "bg_deep":      "#e5e3df",
    "surface":      "#ffffff",
    "surface_alt":  "#fafaf8",
    "border":       "#dbd9d3",
    "border_dark":  "#ccc9c1",

    # --- Dark Theme (VIA Fusion) ---
    "dark_bg":      "#1a1918",
    "dark_bg1":     "#232220",
    "dark_bg2":     "#2a2927",
    "dark_surface": "#242322",
    "dark_border":  "#3a3835",

    # --- Text Hierarchy ---
    "text_primary":   "#1e1d1a",
    "text_secondary": "#3d3c38",
    "text_tertiary":  "#6b6860",
    "text_muted":     "#9c9890",
    "text_faint":     "#c4c0b8",

    # --- Chart Specific ---
    "plot_bg":      "#ffffff",
    "grid":         "#EBEBEB",
    "grid_fusion":  "#dbd9d3",
}

# ============================================================
# 3. TYPOGRAPHY — VIA Fusion Fonts
# ============================================================

FONTS = {
    "mono":     "'DM Mono', 'JetBrains Mono', monospace",
    "sans":     "'DM Sans', 'Inter', 'Noto Sans TC', system-ui, sans-serif",
    "display":  "'Playfair Display', serif",
    "google_import": "https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&display=swap",
}

FONT_SIZES = {
    "chart_title":  "16px",
    "axis_label":   "11px",
    "legend":       "11px",
    "tooltip":      "12px",
    "kpi_number":   "22px",
    "kpi_label":    "9px",
    "badge":        "8.5px",
    "table_cell":   "10px",
    "table_header": "10px",
}

FONT_WEIGHTS = {
    "bold":      700,
    "semibold":  600,
    "medium":    500,
    "regular":   400,
}

# ============================================================
# 4. BORDER RADIUS — VIA Fusion System
# ============================================================

RADIUS = {
    "small":  "5px",
    "medium": "8px",
    "large":  "12px",
}

# ============================================================
# 5. SHADOWS — VIA Fusion System
# ============================================================

SHADOWS = {
    "sm":   "0 1px 3px rgba(0,0,0,.06)",
    "md":   "0 4px 12px rgba(0,0,0,.08)",
    "card": "0 1px 3px rgba(0,0,0,.06)",
}

# ============================================================
# 6. MA SYSTEM — ChartSpec v4.0
# ============================================================

MA_CONFIG = {
    5:   {"color": "#CCB974", "width": 1.2, "default_on": True,  "label": "MA5"},
    10:  {"color": "#64B5CD", "width": 1.2, "default_on": True,  "label": "MA10"},
    20:  {"color": "#55A868", "width": 1.5, "default_on": True,  "label": "MA20"},
    60:  {"color": "#4C72B0", "width": 2.0, "default_on": True,  "label": "MA60"},
    120: {"color": "#DA8BC3", "width": 1.5, "default_on": False, "label": "MA120"},
    240: {"color": "#8C8C8C", "width": 1.5, "default_on": False, "label": "MA240"},
}

EMA_CONFIG = {
    12: {"color": "#DD8452", "dash": "dash", "default_on": False, "label": "EMA12"},
    26: {"color": "#8172B3", "dash": "dash", "default_on": False, "label": "EMA26"},
}

# ============================================================
# 7. CANDLESTICK — ChartSpec v4.0
# ============================================================

CANDLE = {
    "rise_color":       "#55A868",
    "fall_color":       "#C44E52",
    "vol_rise_opacity":  0.6,
    "vol_fall_opacity":  0.6,
    "vol_color":        "#4C72B0",
}

# ============================================================
# 8. DUAL AXIS — ChartSpec v4.0
# ============================================================

DUAL_AXIS = {
    "left_color":       "#4C72B0",
    "right_color":      "#DD8452",
    "left_grid":        "#EBEBEB",
    "right_grid":       "rgba(0,0,0,0)",  # TRANSPARENT!
}

# ============================================================
# 9. BOLLINGER BANDS — ChartSpec v4.0
# ============================================================

BB_CONFIG = {
    "period":       20,
    "std_dev":      2.0,
    "line_color":   "rgba(76,114,176,0.4)",
    "line_dash":    "dash",
    "fill_color":   "rgba(76,114,176,0.08)",
}

# ============================================================
# 10. VERTICAL STACK PANELS — ChartSpec v4.0
# ============================================================

STACK_PANELS = {
    "price":  {"height_ratio": 0.30, "default_on": True},
    "volume": {"height_ratio": 0.10, "default_on": True},
    "macd":   {"height_ratio": 0.15, "default_on": True},
    "rsi":    {"height_ratio": 0.15, "default_on": True},
    "kd":     {"height_ratio": 0.15, "default_on": False},
    "custom": {"height_ratio": 0.15, "default_on": False},
}

# ============================================================
# 11. HEATMAP — ChartSpec v4.0
# ============================================================

HEATMAP = {
    "correlation": {"colorscale": "RdBu", "zmin": -1, "zmax": 1},
    "calendar":    {"colorscale": "RdYlGn", "zmid": 0},
    "sector":      {"colorscale": "Viridis"},
    "cell_gap_x":  2,
    "cell_gap_y":  2,
}

# ============================================================
# 12. PLOTLY GLOBAL LAYOUT — ChartSpec v4.0 + VIA Fusion
# ============================================================

PLOTLY_LAYOUT = {
    "template":         "plotly_white",
    "plot_bgcolor":     "#ffffff",
    "paper_bgcolor":    "#ffffff",
    "font_family":      "'DM Sans', 'Inter', 'Noto Sans TC', sans-serif",
    "font_size":        12,
    "font_color":       "#1e1d1a",
    "hovermode":        "x unified",
    "showlegend":       True,
    "legend_orientation": "h",
    "legend_y":         -0.15,
    "margin":           {"t": 50, "r": 60, "b": 50, "l": 60},
    "xaxis_gridcolor":  "#EBEBEB",
    "yaxis_gridcolor":  "#EBEBEB",
    "yaxis2_gridcolor": "rgba(0,0,0,0)",
}

PLOTLY_CONFIG = {
    "responsive":       True,
    "displayModeBar":   False,
    "scrollZoom":       True,
    "editable":         False,
}

# ============================================================
# 13. OUTPUT — ChartSpec v4.0
# ============================================================

OUTPUT = {
    "default_dpi":  180,
    "png_format":   "png",
    "html_standalone": True,
    "data_locked":  True,
}

# ============================================================
# 14. BADGE COLOR MAPPING — VIA Fusion
# ============================================================

BADGE_COLORS = {
    "critical": {"bg": "#f5d0c8", "text": "#c96b5a"},
    "high":     {"bg": "#dcd8f0", "text": "#7a6daa"},
    "mid":      {"bg": "#f5e2b8", "text": "#c4943a"},
    "low":      {"bg": "#cde8d5", "text": "#5a9e6f"},
    "info":     {"bg": "#d0e1f0", "text": "#4c78a8"},
    "success":  {"bg": "#cde8d5", "text": "#5a9e6f"},
    "warning":  {"bg": "#f5e2b8", "text": "#c4943a"},
    "danger":   {"bg": "#f5d0c8", "text": "#c96b5a"},
}
