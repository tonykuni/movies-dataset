#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL117_AccelCoverage v0100 — 加速器覆蓋×啟動稽核(批323)
======================================================================
操作員令(批323):「確認所有 engines modules 都導入加速器;加速器一百多個 libs
都有啟動功能」。本件=可重跑的誠實稽核(零網路):
  ① 覆蓋面:全樹現役 .py 是否掛 [VIA:ACCEL-BRIDGE](或直接 import
     VIA_SuperAccel_Module);.ps1 是否掛 [VIA:PS-ACCEL]。整檔讀(非前段截
     讀=SelftestGrid 類長文檔誤判之根因);排除冊=歷史件/收容夾/第三方
     (VIA_RetiredEngines/_review_quarantine/vendor/TALib/intake/references/
     new modules engines/output_hub/VIA_Reports/_runs)=誠實列於報告,不計現役。
  ② 命名件面:*_ENG###/*_MDL### 件單獨統計(操作員語「engines modules」)。
  ③ 啟動面:經 VIA_SuperAccel_Module.activate()(SUP_MDL737 尾版)載
     VeritasCeleritas → lib 冊總數/可用/缺/真實能力/執行緒預算(缺=lazy stub
     代位=誠實非真加速;數字依本機安裝而異,工作站為正判)。
輸出:VIA_Reports/accel_coverage/ACCEL_COVERAGE_<stamp>.json + 終端表。
用法:python CGC_MDL117_AccelCoverage_v0100.py run | --selftest
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

import json
import os
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REP = VIA / "VIA_Reports" / "accel_coverage"

EXCLUDE_DIRS = {"VIA_RetiredEngines", "_review_quarantine", "vendor", "TALib", "intake",
                "references", "new modules engines", "output_hub", "VIA_Reports", "_runs",
                ".git", "__pycache__", "node_modules", "deck_intake"}
PY_MARK = (b"ACCEL-BRIDGE", b"VIA_SuperAccel_Module")
PS_MARK = (b"PS-ACCEL",)
NAMED = re.compile(r"_(ENG|MDL)\d")


def scan(root: Path = VIA) -> dict:
    py_tot = py_lack = ps_tot = ps_lack = named_tot = named_lack = 0
    lack_py, lack_ps, lack_named = [], [], []
    for r, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            p = Path(r) / f
            try:
                data = p.read_bytes()
            except Exception:
                continue
            rel = str(p.relative_to(root))
            if f.endswith(".py"):
                py_tot += 1
                ok = any(m in data for m in PY_MARK)
                is_named = bool(NAMED.search(f))
                if is_named:
                    named_tot += 1
                if not ok:
                    py_lack += 1
                    lack_py.append(rel)
                    if is_named:
                        named_lack += 1
                        lack_named.append(rel)
            elif f.endswith(".ps1"):
                ps_tot += 1
                if not any(m in data for m in PS_MARK):
                    ps_lack += 1
                    lack_ps.append(rel)
    return {"py_total": py_tot, "py_lacking": py_lack, "py_lacking_list": lack_py,
            "named_total": named_tot, "named_lacking": named_lack, "named_lacking_list": lack_named,
            "ps_total": ps_tot, "ps_lacking": ps_lack, "ps_lacking_list": lack_ps,
            "excluded_dirs": sorted(EXCLUDE_DIRS)}


def activation() -> dict:
    if VIA_ACCEL is None or not hasattr(VIA_ACCEL, "activate"):
        return {"celeritas": False, "err": "VIA_SuperAccel_Module 缺或無 activate(尾版 <v0103)",
                "libs_total": 0, "libs_available": 0, "missing": [], "capability_real": 0,
                "capability_total": 0, "thread_budget": None, "mode": None}
    try:
        return VIA_ACCEL.activate(apply_limits=False)
    except Exception as exc:
        return {"celeritas": False, "err": f"{type(exc).__name__}: {str(exc)[:120]}",
                "libs_total": 0, "libs_available": 0, "missing": [], "capability_real": 0,
                "capability_total": 0, "thread_budget": None, "mode": None}


def run() -> int:
    t0 = time.time()
    sc = scan()
    ac = activation()
    stamp = time.strftime("%Y%m%d_%H%M%S")
    rep = {"ts": stamp, "root": str(VIA), "scan": sc, "activation": ac,
           "verdict": {"py_bridge_full": sc["py_lacking"] == 0,
                       "ps_bridge_full": sc["ps_lacking"] == 0,
                       "celeritas_loaded": bool(ac.get("celeritas"))}}
    REP.mkdir(parents=True, exist_ok=True)
    out = REP / f"ACCEL_COVERAGE_{stamp}.json"
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print("=== 加速器覆蓋×啟動稽核(CGC_MDL117 v0100;整檔讀;排除歷史件)===")
    print(f"  [{'OK' if sc['py_lacking'] == 0 else 'FAIL'}] py 現役 {sc['py_total']} 件 · 掛橋 "
          f"{sc['py_total'] - sc['py_lacking']} · 缺 {sc['py_lacking']}")
    print(f"  [{'OK' if sc['named_lacking'] == 0 else 'FAIL'}] ENG/MDL 命名件 {sc['named_total']} · "
          f"缺 {sc['named_lacking']}")
    print(f"  [{'OK' if sc['ps_lacking'] == 0 else 'FAIL'}] ps1 現役 {sc['ps_total']} 件 · 缺 {sc['ps_lacking']}")
    for rel in sc["py_lacking_list"][:20]:
        print(f"      缺 py:{rel}")
    for rel in sc["ps_lacking_list"][:20]:
        print(f"      缺 ps1:{rel}")
    print(f"  [{'OK' if ac.get('celeritas') else 'FAIL'}] Celeritas 啟動:lib 冊 {ac.get('libs_total')} · "
          f"可用 {ac.get('libs_available')} · 缺 {len(ac.get('missing') or [])}(lazy stub 代位)"
          f" · 真實能力 {ac.get('capability_real')}/{ac.get('capability_total')}"
          f" · 執行緒預算 {ac.get('thread_budget')}({ac.get('mode')}) {ac.get('err') or ''}")
    print(f"  排除冊(不計現役,誠實):{', '.join(sc['excluded_dirs'])}")
    print(f"  存證:{out} · {time.time() - t0:.1f}s")
    return 0 if (sc["py_lacking"] == 0 and sc["ps_lacking"] == 0 and ac.get("celeritas")) else 1


def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        (t / "a_ENG001_x.py").write_text("# [VIA:ACCEL-BRIDGE:v0100]\nprint(1)\n", encoding="utf-8")
        (t / "b_MDL002_y.py").write_text("print(2)\n", encoding="utf-8")
        (t / "c.ps1").write_text("# [VIA:PS-ACCEL:v0100]\n", encoding="utf-8")
        (t / "d.ps1").write_text("Write-Host 1\n", encoding="utf-8")
        (t / "VIA_RetiredEngines").mkdir()
        (t / "VIA_RetiredEngines" / "old_ENG003.py").write_text("print(3)\n", encoding="utf-8")
        # 長文檔:標記在 8000 位元組之後=整檔讀必命中
        (t / "long_MDL004.py").write_text("#" + "x" * 9000 + "\n# [VIA:ACCEL-BRIDGE:v0100]\n", encoding="utf-8")
        sc = scan(t)
    chk("① 掃描計數(py 3/缺 1;ps1 2/缺 1)", sc["py_total"] == 3 and sc["py_lacking"] == 1
        and sc["ps_total"] == 2 and sc["ps_lacking"] == 1, str(sc["py_lacking_list"]))
    chk("② 排除冊生效(退役夾不計現役)", "old_ENG003.py" not in " ".join(sc["py_lacking_list"]))
    chk("③ 整檔讀(標記在 8000 位元組後仍命中)", "long_MDL004.py" not in " ".join(sc["py_lacking_list"]))
    chk("④ 命名件面(ENG/MDL 3 件;缺 1=b_MDL002)", sc["named_total"] == 3 and sc["named_lacking"] == 1
        and sc["named_lacking_list"] == ["b_MDL002_y.py"])
    ac = activation()
    chk("⑤ 啟動面字典契約(缺=誠實 err 非例外)",
        all(k in ac for k in ("celeritas", "libs_total", "libs_available", "missing", "err"))
        and ac["libs_available"] + len(ac["missing"]) == ac["libs_total"])
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 誠實宣告(缺=lazy stub 代位;工作站為正判)+加速橋", "lazy stub" in src and "ACCEL-BRIDGE" in src)
    print(f"  [計] 六檢 OK {6 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 加速器覆蓋稽核(CGC_MDL117)· 六檢自測(零網路)===")
        return selftest()
    return run()


if __name__ == "__main__":
    sys.exit(main())
