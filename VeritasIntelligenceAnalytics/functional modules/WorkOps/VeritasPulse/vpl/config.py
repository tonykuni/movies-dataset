"""VPL-CFG · central configuration surface.

"所有功能都要高度彈性可修改" — one file drives the whole system. Edit
config.json (or this default) to: enable/disable any module, change the accent
colour / brand name, set LLM providers + endpoints, news sources, default
minutes mode. build_app merges config.json over these defaults at build time,
and the app also applies the live bits (accent, brand, providers) at runtime.
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
import json
import os

DEFAULT_CONFIG = {
    "brand": "VeritasPulse",
    "brand_sub": "VPL · Veritas v1",
    "accent": "#5e7032",          # olive green — change to re-theme everything
    "default_minutes_mode": "comprehensive",   # or "concise"
    # module on/off overrides (id: bool). Omitted ids keep registry default.
    "modules": {},                # e.g. {"ledger": false, "flow": true}
    # LLM providers — flexible on/off + endpoint (OpenAI-compatible)
    "llm_providers": [
        {"k": "openai",  "name": "ChatGPT", "on": True,  "endpoint": ""},
        {"k": "claude",  "name": "Claude",  "on": True,  "endpoint": ""},
        {"k": "gemini",  "name": "Gemini",  "on": False, "endpoint": ""},
        {"k": "copilot", "name": "Copilot", "on": False, "endpoint": ""},
        {"k": "notion",  "name": "Notion",  "on": False, "endpoint": ""},
    ],
    "news_sources": [
        {"name": "CNBC", "url": "https://www.cnbc.com/", "enabled": True},
        {"name": "Yahoo奇摩股市", "url": "https://tw.stock.yahoo.com/", "enabled": True},
        {"name": "鉅亨網", "url": "https://www.cnyes.com/", "enabled": True},
    ],
    "world_clocks": ["Asia/Taipei", "America/New_York", "Europe/London", "Asia/Tokyo"],
    "weather_default": {"lat": 25.04, "lon": 121.56, "name": "Taipei"},
    "pwa": True,
}


def load(out_dir: str = "output") -> dict:
    """Merge an optional config.json over the defaults (shallow + module merge)."""
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))  # deep copy
    path = os.path.join(out_dir, "config.json")
    if os.path.exists(path):
        try:
            user = json.loads(open(path, encoding="utf-8").read())
            for k, v in user.items():
                if k == "modules" and isinstance(v, dict):
                    cfg["modules"].update(v)
                else:
                    cfg[k] = v
        except Exception:
            pass
    return cfg


def write_default(out_dir: str = "output") -> str:
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "config.json")
    if not os.path.exists(path):
        open(path, "w", encoding="utf-8").write(
            json.dumps(DEFAULT_CONFIG, ensure_ascii=False, indent=2))
    return path
