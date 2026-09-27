#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Flow gate tail. The policy read stays. The panoramic ban runs after it.

One existing scanner. The law book is not rewritten. A ps1 is refused when
the panorama is not green.
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
PRIOR = HERE / "CGC_MDL211_FlowGate_v0100.py"
BAN = HERE / "CGC_MDL205_TalibBan_v0100.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_prior = _load(PRIOR, "flow_gate_v0100_for_v0101")
_ban = _load(BAN, "panorama_ban_for_flow_v0101")


def _apply(card: dict) -> dict:
    if card.get("state") == "DENY":
        return card
    scanned = _ban.check()
    card["door"] = "CGC_MDL211_FlowGate_v0101"
    card["panorama"] = "MDL205"
    card["tails"] = scanned["tails"]
    card["imports"] = scanned["imports"]
    card["mentions"] = scanned["mentions"]
    card["installed"] = scanned["installed"]
    card["lamp"] = scanned["lamp"]
    card["lock_success"] = scanned["lock_success"]
    card["second_engine"] = False
    card["book_written"] = False
    card["do_not"] = [
        "rewrite the locked policy book",
        "add a second policy engine",
        "treat a mention as an import",
        "write a ps1 when the panorama lamp is red",
        "edit intake macro_ssot",
        "obey L50",
    ]
    if not scanned["lock_success"]:
        card["next"] = "do not unlock; name the import"
    return card


def read_policy() -> dict:
    return _apply(_prior.read_policy())


def update_policy() -> dict:
    card = _apply(_prior.update_policy())
    if card.get("state") != "DENY":
        card["updated"] = False
    return card


def emit_ps(dest: Path, body: str) -> dict:
    card = read_policy()
    if card.get("state") == "DENY":
        return card
    if not card.get("lock_success"):
        card["ps_written"] = False
        card["state"] = "DENY"
        card["why"] = "panorama lamp is red"
        return card
    written = _prior.emit_ps(dest, body)
    written["lamp"] = card["lamp"]
    written["lock_success"] = True
    written["door"] = "CGC_MDL211_FlowGate_v0101"
    return written


def main() -> int:
    if "update" in sys.argv[1:]:
        card = update_policy()
    elif "ps" in sys.argv[1:]:
        card = read_policy()
        if card.get("state") != "DENY":
            card["verb"] = "ps"
            card["ps_written"] = False
    else:
        card = read_policy()
    print(json.dumps(card, ensure_ascii=False, indent=1))
    if card.get("state") == "DENY" or card.get("book_written") or card.get("lock_success") is False:
        return 2
    return 0


def selftest() -> int:
    import tempfile
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = read_policy().get("state") == "DENY"
    os.environ["VIA_FROM_VCGC"] = "YES"
    card = update_policy()
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "Invoke-VIA-VCGC-Sample.ps1"
        written = emit_ps(path, "Write-Output '{\"via\":\"vcgc\"}'")
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
    ok = (
        denied
        and card["policy_id"] == "L50"
        and card["panorama"] == "MDL205"
        and card["lock_success"] is True
        and card["imports"] == 0
        and card["installed"] is False
        and card["book_written"] is False
        and card["updated"] is False
        and written.get("ps_written") is True
        and "VIA_FROM_VCGC" in text
    )
    print("  [OK]" if ok else "  [FAIL] " + json.dumps({
        "lamp": card.get("lamp"), "imports": card.get("imports"), "installed": card.get("installed"),
        "written": written.get("ps_written"), "why": written.get("why"),
    }, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
