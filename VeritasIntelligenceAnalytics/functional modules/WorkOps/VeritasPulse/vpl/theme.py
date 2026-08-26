"""VeritasPulse (VPL) — VIA Visual Lock v1 theme tokens.
Single source of truth for colours / fonts across charts and PPT.
"""
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

# === VIA Visual Lock v1 / VPN v3.5 base palette (hex, no '#') ===
BG          = "F5F4F0"  # warm off-white
PANEL       = "FBFAF7"
PANEL_ALT   = "F0EEE8"
INK         = "1A1916"
INK_SOFT    = "56524A"
INK_FAINT   = "8F897C"
LINE        = "E2DFD6"
ACCENT      = "5E7032"  # olive green — primary (per Tony's palette)
OLIVE       = "7E9150"  # bright olive accent
AMBER       = "9A6B2F"  # focus / warning
RUST        = "8A3B2E"  # critical / overdue
BLUE        = "35506B"  # synced / info
PLUM        = "5D4566"
TEAL        = "2F6B6B"

# matplotlib needs '#'
def mpl(c: str) -> str:
    return "#" + c

# Semantic sequences for charts (ordered, VIA-locked)
SERIES = [ACCENT, BLUE, AMBER, PLUM, TEAL, RUST]
SERIES_MPL = [mpl(c) for c in SERIES]

# Status -> colour (traffic-light / lights)
STATUS = {
    "done":    ACCENT,
    "active":  AMBER,
    "blocked": RUST,
    "waiting": INK_FAINT,
}

# Fonts (VIA brand). Fall back gracefully if not installed on host.
FONT_DISPLAY = "Syne"      # titles
FONT_BODY    = "DM Sans"   # body
FONT_MONO    = "DM Mono"   # data / labels
# Safe fallbacks for hosts without the brand fonts:
FONT_DISPLAY_FB = "Segoe UI Semibold"
FONT_BODY_FB    = "Segoe UI"
FONT_MONO_FB    = "Consolas"
