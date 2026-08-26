#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VIA_ENG170_WorkPulseUnified — WorkOps×VeritasPulse 整合門面(批185)
====================================================================
操作員令:「veritaspulse WorkOps 整合為一」。
整合為一=單一 WorkOps 域三子系統+單一門面入口(本引擎):
  RC   = VIA_WorkOps_Product_RC_v0200(工作管理產品正主;legacy
         engines/ 同名 DIFF 四件已讓位 batch185_wave4)
  VTR  = VTR/engine/vtr_py(文件正規化管線:lang_detect→normalize→
         protect;規則冊 config/vtr.json)
  PULSE= VeritasPulse(會議/簡報產品:minutes/excel 模板/ppt/圖表;
         批185 git mv 併入本域,名冊 23 鍵遷移編號不變)
紀律:只增不減(讓位=封存非刪除,undo 可還原);hash 定生死(SAME=
重複去重;DIFF 同名=RC 正主);正本不就地修改;引用面僅盤點型檔案
=移域零破壞。
v0100→v0101(批186 操作員裁示):「Taiwan revenue 保留 in py code;
RC 刪除」——RC 整域 180 件讓位封存 batch186_wave5(零刪除常令:
manifest+undo+git 歷史三保險,物理刪除候明示第二令);domains 改
二現役(VTR+PULSE)+RC=RETIRED 誠實態;taiwan_revenue_engine=KEEP
裁定(py 套件形式留位)→套件審查 4 群全數結案。
用法:python3 VIA_ENG170_WorkPulseUnified_v0101.py [--status] | --selftest
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

import hashlib
import json
import py_compile
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent          # functional modules/WorkOps
VIA = HERE.parent.parent
RC = HERE / "VIA_WorkOps_Product_RC_v0200"
VTR = HERE / "VTR" / "engine" / "vtr_py"
PULSE = HERE / "VeritasPulse"
EXCLUDE_FRAGS = ("__pycache__", "/docs/history/", "docs\\history")


RC_RETIRED = (VIA / "functional modules" / "VIA_RetiredEngines" /
              "batch186_wave5" / "functional modules" / "WorkOps" /
              "VIA_WorkOps_Product_RC_v0200")
TWREV = VIA / "functional modules" / "GroupIndex" / "engine" / "taiwan_revenue_engine"


def domains() -> dict:
    """子域盤點(誠實:RC=RETIRED 批186 裁示;缺=False 不假在)"""
    return {
        "RC": {"root": str(RC_RETIRED.relative_to(VIA)),
               "state": "RETIRED(批186 操作員裁示;undo 可還原)",
               "present": RC_RETIRED.exists(),
               "engines": sorted(p.name for p in
                                 (RC_RETIRED / "engines").glob("*.py"))
               if (RC_RETIRED / "engines").exists() else []},
        "VTR": {"root": str(VTR.relative_to(VIA)), "state": "ACTIVE",
                "present": VTR.exists(),
                "stages": sorted(p.name for p in (VTR / "stages").glob("s*.py"))
                if (VTR / "stages").exists() else []},
        "PULSE": {"root": str(PULSE.relative_to(VIA)), "state": "ACTIVE",
                  "present": PULSE.exists(),
                  "vpl": sorted(str(p.relative_to(PULSE)) for p in
                                (PULSE / "vpl").rglob("*.py"))
                  if (PULSE / "vpl").exists() else []},
        "TWREV": {"root": str(TWREV.relative_to(VIA)),
                  "state": "KEEP(批186 操作員裁示:保留 in py code)",
                  "present": TWREV.exists(),
                  "py": sorted(p.name for p in TWREV.rglob("*.py")
                               if "__pycache__" not in str(p))
                  if TWREV.exists() else []},
    }


def dedup_audit() -> dict:
    """域內去重稽核:同名同 hash=重複(hash 定生死);歷史夾除外。
    __init__.py 套件標記=Python 結構件(同 hash 屬常態)非功能重複,
    不入稽核(QA:初版誤列→誠實修)"""
    by_name = defaultdict(list)
    for p in HERE.rglob("*.py"):
        sp = str(p)
        if any(k in sp for k in EXCLUDE_FRAGS) or p.name == "__init__.py":
            continue
        by_name[p.name].append(p)
    same_hash, diff_name = [], []
    for name, paths in by_name.items():
        if len(paths) < 2:
            continue
        hashes = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
        if len(set(hashes.values())) < len(paths):
            same_hash.append(name)
        else:
            diff_name.append(name)
    return {"n_files": sum(len(v) for v in by_name.values()),
            "dup_same_hash": sorted(same_hash),
            "dup_diff_hash_names": sorted(diff_name)}


def status() -> int:
    d = domains()
    for k, v in d.items():
        n = len(v.get("engines") or v.get("stages") or v.get("vpl") or [])
        print(f"  [{'在位' if v['present'] else '缺'}] {k:6s} {v['root']} · {n} 件")
    a = dedup_audit()
    print(f"  [去重] 域內 {a['n_files']} 件 · 同 hash 重複 {len(a['dup_same_hash'])}"
          f" · 同名異版 {len(a['dup_diff_hash_names'])}(歷史夾除外)")
    return 0


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    d = domains()
    chk("① 域態=批186 裁示(VTR+PULSE 現役+TWREV KEEP+RC RETIRED 在收容區)",
        all(v["present"] for v in d.values())
        and d["RC"]["state"].startswith("RETIRED")
        and d["TWREV"]["state"].startswith("KEEP")
        and not RC.exists(),
        f"(VTR {len(d['VTR']['stages'])} 段·PULSE {len(d['PULSE']['vpl'])} 件·"
        f"TWREV {len(d['TWREV']['py'])} py·RC 收容 {len(d['RC']['engines'])} 引擎)")
    chk("② PULSE 移域完整(舊根不存+vpl 套件齊)",
        not (VIA / "functional modules" / "VeritasPulse").exists()
        and len(d["PULSE"]["vpl"]) >= 10)
    a = dedup_audit()
    chk("③ 同 hash 重複清零(hash 定生死;歷史夾除外)",
        len(a["dup_same_hash"]) == 0, f"({a['dup_same_hash'] or '無'})")
    chk("④ legacy 四件讓位後 RC 正主唯一(engines/ 不再有同名)",
        not any((HERE / "engines" / f"workops_{n}.py").exists()
                for n in ("closure_intelligence", "milestone_manager",
                          "onboarding", "unified_search")))
    wave_ok = True
    for wave_dir, n_exp in (("batch185_wave4", 5), ("batch186_wave5", 180)):
        mf = (VIA / "functional modules" / "VIA_RetiredEngines" / wave_dir /
              "RETIRE_MANIFEST.json")
        man = json.loads(mf.read_text(encoding="utf-8"))
        bad = sum(1 for mv in man["moves"]
                  if not (VIA / mv["to"]).exists()
                  or hashlib.sha256((VIA / mv["to"]).read_bytes()).hexdigest() != mv["sha256"])
        wave_ok = (wave_ok and len(man["moves"]) >= n_exp and bad == 0
                   and (mf.parent / "undo_retire.py").exists())
    chk("⑤ wave4+wave5 manifest 自洽(sha 全符+undo 在位;RC 180 件可還原)",
        wave_ok)
    comp_bad = []
    for p in list(VTR.rglob("*.py")) + list((PULSE / "vpl").rglob("*.py")) + \
             list(TWREV.rglob("*.py")):
        if any(k in str(p) for k in EXCLUDE_FRAGS):
            continue
        try:
            py_compile.compile(str(p), doraise=True)
        except Exception:
            comp_bad.append(p.name)
    chk("⑥ 現役子域編譯檢全過(VTR+PULSE+TWREV;零執行)",
        not comp_bad, f"({comp_bad or '全過'})")
    reg = json.loads((VIA / "supportive modules" / "registry" /
                      "VIA_Naming_Registry_v0100.json").read_text(encoding="utf-8"))
    mig = sum(1 for v in reg["items"].values()
              if "WorkOps/VeritasPulse" in json.dumps(v.get("members", [])))
    chk("⑦ 名冊鍵遷移落冊(≥20 件新路徑+VIA_ENG170 登錄)",
        mig >= 20 and "functional modules/WorkOps/VIA_ENG170_WorkPulseUnified"
        in reg["items"] and reg["counters"]["VIA_ENG"] >= 170, f"(遷移 {mig})")
    chk("⑧ 引用面零破壞(現役 py/sh 語料無舊根路徑引用;自家族歷版"
        "=檢查字面量非消費,除外)",
        not any("functional modules/VeritasPulse" in
                p.read_text(encoding="utf-8", errors="ignore")
                for root in ("functional modules", "supportive modules", "bin")
                if (VIA / root).exists()
                for p in (VIA / root).rglob("*.py")
                if "VIA_RetiredEngines" not in str(p)
                and "VIA_Reports" not in str(p)
                and not p.name.startswith("VIA_ENG170_WorkPulseUnified")))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑨ 紀律宣告(只增不減/hash 定生死/undo 可還原/加速橋)",
        all(k in src for k in ("只增不減", "hash 定生死", "undo",
                               "VIA:ACCEL-BRIDGE")))
    print(f"  [計] 九檢 OK {9 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        print("=== WorkPulse 整合門面(VIA_ENG170)· 九檢自測(零網路)===")
        return selftest()
    return status()


if __name__ == "__main__":
    sys.exit(main())
