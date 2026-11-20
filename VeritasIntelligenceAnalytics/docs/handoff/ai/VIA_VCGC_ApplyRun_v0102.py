#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VIA_VCGC_ApplyRun v0102 — 薄尾:G 道多一步「VCGC 自己的 omniroute」(與 VDF / VRN 那兩步並排)

操作員 2026-11-20 17:13:「VCGC 也要導入 OMNIROUTE」。VCGC 的管理器 CGC_SystemManager v0116 起有 omniroute 動詞;
本版只把它排進 G 道(VDF-omniroute 前面),其餘全部照 v0101 / v0100。用法同前版。
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VIA_VCGC_ApplyRun"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0102", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.PRIOR                       # v0100:run() 在這一層,它用這一層的 plan
VERSION = "v0102"
TAG = "VIA_VCGC_ApplyRun " + VERSION


def __getattr__(name):
    return getattr(PRIOR, name)


def plan(via: Path, only: list[str]):
    g, notes = _PREV_PLAN(via, only)
    if "G" in g:
        sm = BASE.tail(via / "supportive modules" / "registry", "CGC_SystemManager_v*.py")
        step = BASE.Step("G", "VCGC-omniroute", sm, ["omniroute"], 300)
        names = [s.name for s in g["G"]]
        g["G"].insert(names.index("VDF-omniroute") if "VDF-omniroute" in names else len(names), step)
        if sm is None or _vnum(sm) < 116:
            notes.append("[G] VCGC 管理器尾版還沒有 omniroute(要 CGC_SystemManager v0116 以上)")
    return g, notes


_PREV_PLAN = BASE.plan                   # = v0101 的 plan(它再接 v0100 原本那支)
BASE.plan = plan
BASE.VERSION, BASE.TAG = VERSION, TAG


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""))

    print("=== %s 薄尾自測(前版鏈另跑)===" % TAG)
    via = BASE.find_via(HERE)
    if via is None:
        chk("① 找不到 VIA 夾(這台不是倉):跳過 = 黃", False)
    else:
        keep = PRIOR.sr_stage
        me1 = sys.modules[PRIOR.__name__]
        me1.sr_stage = lambda *a, **k: (Path("VCGC_SafeRepair.py"), "自測替身(不解包)")
        try:
            g, _ = BASE.plan(via, ["G", "R"])
        finally:
            me1.sr_stage = keep
        gn, rn = [s.name for s in g["G"]], [s.name for s in g["R"]]
        sm = [s for s in g["G"] if s.name == "VCGC-omniroute"]
        chk("① G 道有 VCGC-omniroute,排在 VDF-omniroute 前面 · 入口是 VCGC 管理器尾版 · 不帶「自己的入口」旗(它就是 VCGC)",
            "VCGC-omniroute" in gn and gn.index("VCGC-omniroute") + 1 == gn.index("VDF-omniroute") and sm and sm[0].entry
            and Path(sm[0].entry).name.startswith("CGC_SystemManager_v") and not sm[0].own, gn)
        chk("② R 道照前版(含 SafeRepair 那一步)· 計畫走 run() 用的那一層", "R1-saferepair" in rn and BASE.plan is plan, rn[:10])
    src = Path(__file__).read_text(encoding="utf-8")
    chk("③ 加速器橋在 · 不碰 TA-Lib · 沒有色碼", "[VIA:ACCEL-BRIDGE" in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M) and not re.search(r"#[0-9a-fA-F]{6}\b", src))
    rc_prior = PRIOR.selftest()
    chk("④ 前版 %s 自測照過" % PRIOR_PATH.stem, rc_prior == 0, rc_prior)
    good = all(ok)
    print("[%s] %s selftest · %d/%d" % ("PASS" if good else "FAIL", TAG, sum(ok), len(ok)))
    return 0 if good else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a == ["--selftest"]:
        return selftest()
    return BASE.main(a)


if __name__ == "__main__":
    raise SystemExit(main())
