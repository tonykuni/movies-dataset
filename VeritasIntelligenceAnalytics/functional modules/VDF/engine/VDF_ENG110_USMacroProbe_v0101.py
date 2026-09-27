#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Same one-point probe. The key comes from the environment or the local key file, never from git."""
from __future__ import annotations
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
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF = HERE.parent
KEY_FILE = VDF / "output_hub" / "mega" / ".fred_api_key"
OUT = VDF / "VDF_USMacro_Probe_v0100.json"


def _prior():
    spec = importlib.util.spec_from_file_location("probe_v0100", HERE / "VDF_ENG110_USMacroProbe_v0100.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def key_from() -> tuple[str, str]:
    env = os.environ.get("FRED_API_KEY", "").strip()
    if env:
        return env, "env"
    if KEY_FILE.is_file():
        text = KEY_FILE.read_text(encoding="utf-8").strip()
        if text:
            return text, "keyfile"
    return "", "missing"


def run() -> dict:
    prior = _prior()
    key, source = key_from()
    os.environ["FRED_API_KEY"] = key
    card = prior.run()
    card["door"] = "VDF_ENG110_USMacroProbe_v0101"
    card["fred_key"] = source
    if source == "missing":
        card["next"] = "put the key in output_hub/mega/.fred_api_key or FRED_API_KEY, then run this door again"
    else:
        card["next"] = "none"
    return card


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    card = run()
    OUT.write_text(json.dumps(card, ensure_ascii=False, indent=1), encoding="utf-8")
    show = dict(card)
    show["rows"] = [row for row in card["rows"] if row.get("state") != "SKIP"]
    print(json.dumps(show, ensure_ascii=False, indent=1))
    return 0 if card["fred_key"] != "missing" else 2


def selftest() -> int:
    os.environ.pop("FRED_API_KEY", None)
    missing, source = key_from()
    os.environ["FRED_API_KEY"] = "probe-selftest"
    found, found_source = key_from()
    os.environ.pop("FRED_API_KEY", None)
    ok = missing == "" and source == "missing" and found == "probe-selftest" and found_source == "env" and not KEY_FILE.exists()
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
