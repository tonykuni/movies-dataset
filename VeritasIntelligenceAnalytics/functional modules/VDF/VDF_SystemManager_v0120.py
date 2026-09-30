#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF manager tail. The tool lamp follows the lock, not the unversioned accelerator.

v0106 pointed TOOLS at the newest VeritasCeleritas_v*.py, then later tails
reloaded the v0104 body and dropped that patch. read_tool then required
supportive modules/accelerator/VeritasCeleritas.py, which is not the lock.
This file restores the lock path before collect. It does not fetch and it
does not set a consent gate.
"""
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
import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
PRIOR = HERE / "VDF_SystemManager_v0119.py"
LOCK = VIA / "supportive modules" / "registry" / "VIA_ToolVersion_Lock_v0100.json"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _accel_rel() -> str | None:
    if LOCK.is_file():
        try:
            doc = json.loads(LOCK.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            doc = {}
        raw = str((doc.get("accelerator") or {}).get("path") or "")
        prefix = "VeritasIntelligenceAnalytics/"
        rel = raw[len(prefix):] if raw.startswith(prefix) else raw
        if rel and (VIA / rel).is_file():
            return rel.replace("\\", "/")
    hits = sorted((VIA / "supportive modules").glob("VeritasCeleritas_v*.py"))
    if not hits:
        return None
    return str(hits[-1].relative_to(VIA)).replace("\\", "/")


_PRIOR_MOD = None


def _prior():
    global _PRIOR_MOD
    if _PRIOR_MOD is None:
        _PRIOR_MOD = _load(PRIOR, "vdf_v0119_for_v0120")
    return _PRIOR_MOD


def _facade():
    body = _prior()._facade()
    rel = _accel_rel()
    if rel:
        tools = dict(body.TOOLS)
        tools["VeritasCeleritas.py"] = (rel, "鎖冊加速器尾版;無版號舊檔不當正典")
        body.TOOLS = tools
    return body


def collect() -> dict:
    _facade()
    return _prior().collect()


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VDF] 拒絕。只能經 via-vcgc。")
        return 2
    if "measure" in sys.argv[1:]:
        return _prior().main()
    return _prior().main()


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main() == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    card = collect()
    tool = card.get("tool") or {}
    slot = ((tool.get("tools") or {}).get("VeritasCeleritas.py") or {})
    ok = (
        denied
        and slot.get("exists") is True
        and str(slot.get("canon") or "").endswith("VeritasCeleritas_v1141.py")
        and tool.get("state") != "ABSENT"
        and os.environ.get("VIA_NET_CONSENT", "") != "YES"
    )
    print("  [OK]" if ok else "  [FAIL] " + str(tool.get("state")) + " " + str(slot.get("canon")))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
