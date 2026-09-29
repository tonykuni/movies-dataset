#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL245_SDDValidator v0104 — 薄尾:X-REQ-BACK 需求 ↔ 工作流回指檢(上下雙向真的雙向)

X-REQ 的綠燈字寫「(雙向)」,實際驗的是「需求歸屬指得到東西」與「工作流引用的需求存在」;
「需求說它在某條工作流(或那條的某一步),那條工作流的 spec.requirements 有沒有回指它」沒有驗。
實測(側線 2026-09-29 i,PR #375 頭):單向 4 條 —— VCGC-REQ072→VCGC-WKF001 · VCGC-REQ073→VCGC-WKF004 ·
VRN-REQ006→VRN-WKF002 / VRN-WKF003。
本版在原 check_requirements 之後多一列 X-REQ-BACK:有單向 = YELLOW(不擋鎖;補法是工作流冊出新版、
把需求補進 spec.requirements,只增),全回指 = GREEN。其餘整支照 v0103(交接加鎖閘 · 收尾閘不動)。
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
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL245_SDDValidator"
ENGINE = Path(__file__).stem


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location("_sdd_prior_v0104", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR
while "PRIOR" in vars(BASE):
    BASE = vars(BASE)["PRIOR"]
_V0103_REQ = BASE.check_requirements


def back_links(state: dict) -> list:
    """Requirements whose homes name a registered workflow (or one of its steps) that does not list them back."""
    listed = {w.get("code"): set((w.get("spec") or {}).get("requirements") or []) for _, w in state.get("wkfs") or []}
    step_of = {st.get("code"): w.get("code") for _, w in state.get("wkfs") or [] for st in w.get("steps") or []}
    miss = set()
    for r in (state.get("req") or {}).get("requirements") or []:
        for home in r.get("homes") or []:
            wkf = home if home in listed else step_of.get(home)
            if wkf and r.get("code") not in listed[wkf]:
                miss.add(f"{r.get('code')}→{wkf}")
    return sorted(miss)


def check_requirements(state, rows):
    _V0103_REQ(state, rows)
    if not state.get("req"):
        return
    miss = back_links(state)
    if miss:
        BASE._row(rows, "YELLOW", "X-REQ-BACK", f"需求指到工作流、工作流沒回指 {len(miss)} 條(單向;補在該工作流冊新版的 spec.requirements,只增):{miss[:8]}")
    else:
        BASE._row(rows, "GREEN", "X-REQ-BACK", "需求 ↔ 工作流真雙向:需求歸屬指到的每條工作流(含其步)都回指該需求")


BASE.check_requirements = check_requirements


def __getattr__(name: str):
    return getattr(PRIOR, name)


def main(argv=None):
    return PRIOR.main(argv)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    wk = {"code": "VCGC-WKF001", "spec": {"requirements": ["VCGC-REQ001"]}, "steps": [{"code": "VCGC-WKF001-STP002"}]}
    state = {"wkfs": [("b", wk)], "req": {"requirements": [
        {"code": "VCGC-REQ001", "homes": ["VCGC-WKF001"]},
        {"code": "VCGC-REQ002", "homes": ["VCGC-WKF001-STP002", "L08"]},
        {"code": "VCGC-REQ003", "homes": ["docs/x.md"]}]}}
    chk("① 單向抓得到:步歸屬也算到它的工作流;律 / 文件歸屬不算", back_links(state) == ["VCGC-REQ002→VCGC-WKF001"], back_links(state))
    wk["spec"]["requirements"].append("VCGC-REQ002")
    chk("② 回指補上 = 0 條", back_links(state) == [])
    rows = []
    saved = globals()["_V0103_REQ"]
    globals()["_V0103_REQ"] = lambda s, r: None
    try:
        check_requirements(state, rows)
        wk["spec"]["requirements"].remove("VCGC-REQ002")
        check_requirements(state, rows)
    finally:
        globals()["_V0103_REQ"] = saved
    chk("③ 列:全回指 GREEN · 有單向 YELLOW(不紅、不擋鎖)", [r.get("lamp") for r in rows if r.get("rule") == "X-REQ-BACK"] == ["GREEN", "YELLOW"],
        [r.get("lamp") for r in rows])
    chk("④ 裝進本體:本體 check() 呼叫的就是本版", BASE.check_requirements is check_requirements)
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑤ 檔頭 · 加速器橋 · 網路橋在;不碰 TA-Lib", "VIA:ACCEL-BRIDGE" in text and "VIA:NET-BRIDGE" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M))
    print(f"[SDD v0104] 本版 {sum(ok)}/{len(ok)}")
    if not all(ok):
        return 1
    return PRIOR.selftest()


if __name__ == "__main__":
    raise SystemExit(selftest() if sys.argv[1:] == ["--selftest"] else main())
