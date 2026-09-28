#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL233_ToolActivate v0101 — 四件工具同一把尺:加速器 · 網路 · LAYOUT · NLP 都經 VCGC 啟用、鎖版號

操作員 2026-09-28 R24:「用新的加速器 網路工具 LAYOUT NLP 註冊」。v0100 的工具鎖冊只管兩家(accelerator · network);
LAYOUT(SUP_MDL743_GenericLayoutHub)與 NLP(SUP_MDL866_VIAUnifiedNLPOrchestrator)只記在座位冊與版號冊,沒有進鎖冊、
也不經 activate 的十項檢查。v0101 把兩家加進 FAMILIES,檢查照 v0100 原樣(檔在該在的夾 · 四位版號 · AST · 零 TA-Lib ·
加速器橋 · 匯入層不開子行程 · 必備 API · 公開名稱不少於現役 · 參數只增不減 · 冊上已登錄),`activate <family> <file> --apply`
才寫鎖冊;之後 pinned('layout') / pinned('nlp') 就是這兩家的唯一答案。必備 API:兩家都是 thin tail,入口是 main / selftest
(LAYOUT 另有 def_run_batch)。其餘照 v0100。只收 VCGC 呼叫。零網路。
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
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "CGC_MDL233_ToolActivate"


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", path.stem)
    return int(m.group(1)) if m else -1


PRIOR = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(STEM + "_prior_for_" + Path(__file__).stem, PRIOR)
_PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _PRIOR
_spec.loader.exec_module(_PRIOR)
ENGINE = Path(__file__).stem
RULES = _PRIOR.SUPP / "70_VRN_Rules"
NEW_FAMILIES = {
    "layout": ("SUP_MDL743_GenericLayoutHub", RULES, ("main", "selftest", "def_run_batch"), ()),
    "nlp": ("SUP_MDL866_VIAUnifiedNLPOrchestrator", RULES, ("main", "selftest"), ()),
}
_PRIOR.FAMILIES.update(NEW_FAMILIES)          # the prior's checks / plan / apply / status all read this one dict
FAMILIES = _PRIOR.FAMILIES


def __getattr__(name: str):
    return getattr(_PRIOR, name)


def main(argv=None) -> int:
    return _PRIOR.main(argv)


def selftest() -> int:
    for k in NEW_FAMILIES:                         # v0100's own checks measure v0100's two families
        FAMILIES.pop(k, None)
    try:
        rc = _PRIOR.selftest()
    finally:
        FAMILIES.update(NEW_FAMILIES)
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    chk("⑪ 四家同一把尺:accelerator · network · layout · nlp", set(FAMILIES) >= {"accelerator", "network", "layout", "nlp"},
        ", ".join(sorted(FAMILIES)))
    for fam, fn in (("layout", "SUP_MDL743_GenericLayoutHub_v0109.py"), ("nlp", "SUP_MDL866_VIAUnifiedNLPOrchestrator_v0105.py")):
        res = _PRIOR.checks(fam, fn)
        bad = [c["check"] + ":" + c["detail"] for c in res if not c["ok"]]
        chk(f"⑫ {fam} 新版過 v0100 的全部檢查({fn})", not bad, "; ".join(bad)[:160] or f"{len(res)} 檢")
    wrong = _PRIOR.checks("layout", "SUP_MDL866_VIAUnifiedNLPOrchestrator_v0105.py")
    chk("⑬ 家別不對的檔擋下(NLP 檔不能當 LAYOUT 啟用)", not all(c["ok"] for c in wrong))
    ok = rc == 0 and all(results)
    print(f"  {ENGINE} selftest +{sum(results)}/{len(results)} {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
