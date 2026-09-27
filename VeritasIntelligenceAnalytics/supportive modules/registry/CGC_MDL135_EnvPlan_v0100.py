#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Environment plan on top of the existing conflict lists. It does not install or delete."""
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
import json
import sys
from pathlib import Path

RULES = Path(__file__).with_name("VIA_EnvPlan_Rules_v0100.json")


def _rules() -> dict:
    return json.loads(RULES.read_text(encoding="utf-8"))


def _canon(name: str) -> str:
    return str(name or "").strip().lower().replace("_", "-")


def build_plan(wanted: list[str], installed: dict[str, list[str]]) -> dict:
    rules = _rules()
    high = {_canon(x) for x in rules["high"]}
    medium = {_canon(x) for x in rules["medium"]}
    special = {_canon(k): v for k, v in rules["special"].items()}
    multi = {_canon(x) for x in rules["multi_version"]}
    have: dict[str, set[str]] = {}
    for env, pkgs in installed.items():
        for pkg in pkgs:
            have.setdefault(_canon(pkg), set()).add(env)
    fresh = [_canon(pkg) for pkg in wanted if _canon(pkg) not in have]
    isolate: dict[str, list[str]] = {}
    pulled: list[str] = []
    for env, pkgs in installed.items():
        for pkg in pkgs:
            name = _canon(pkg)
            if name in multi:
                continue
            if name not in high and name not in medium and name not in special:
                continue
            if env.lower() in {"base"} or not env.lower().startswith("via_"):
                home = special.get(name, "via_" + name.replace("-", "_"))
                isolate.setdefault(home, [])
                if name not in isolate[home]:
                    isolate[home].append(name)
                pulled.append(name)
    add_clean: list[str] = []
    for name in fresh:
        if name in multi:
            add_clean.append(name)
            continue
        if name in high or name in medium or name in special:
            home = special.get(name, "via_" + name.replace("-", "_"))
            isolate.setdefault(home, [])
            if name not in isolate[home]:
                isolate[home].append(name)
        else:
            add_clean.append(name)
    dirty = [name for name in pulled if name not in multi]
    verdict = "GREEN" if all(home.startswith("via_") for home in isolate) else "RED"
    return {
        "verdict": verdict,
        "new": fresh,
        "add_clean": add_clean,
        "isolate": isolate,
        "pulled_from_base": sorted(set(dirty)),
        "multi_version": sorted(multi),
        "execute_install": verdict == "GREEN",
        "execute_delete": False,
    }


def selftest() -> int:
    plan = build_plan(
        ["pandas", "numpy", "paddleocr", "requests", "httpx"],
        {"BASE": ["pandas", "numpy", "paddleocr"], "via_core": ["requests"]},
    )
    ok = (
        plan["verdict"] == "GREEN"
        and plan["isolate"].get("via_paddle_311") == ["paddleocr"]
        and "numpy" not in plan["pulled_from_base"]
        and "httpx" in plan["isolate"].get("via_httpx", [])
        and plan["add_clean"] == []
        and plan["execute_install"] is True
        and plan["execute_delete"] is False
    )
    print(f"[環境計畫] {plan['verdict']} · 拉出 {plan['pulled_from_base'] or '無'} · 新增 {plan['add_clean'] or '無'} · 刪除不自動")
    print("  [OK]" if ok else f"  [FAIL] {plan}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest())
