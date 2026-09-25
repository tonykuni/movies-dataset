#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL084_GovTriage — 中央治理議題分圈歸類器(批133;via-govtriage)
====================================================================
批132 中央治理 AUDIT 嚴格鏡頭 gate=HOLD_REMEDIATION_REQUIRED(65,342
開放議題)之正確下一步:議題按「圈」歸類——嚴格鏡頭無豁免圈,把
收容原件/檢疫區/備份存證/run 產物全數計入;本器疊上母系統圈政策,
萃出「活動圈」真實 CRITICAL/HIGH 清單=人工審查的實際工作面。
圈(誠實七分):
  ACTIVE            活動圈(真實工作面)
  EXEMPT_INTAKE     原件收容區(正本不就地修改鐵律;上游原樣)
  QUARANTINE        檢疫/已被修版取代之壞件(_review_quarantine 等)
  SCOPE_BACKUP      SCOPE_COPY/備份/rename_runs 存證副本
  RUNS_EVIDENCE     run 產物與證據圈(VIA_Reports/.via_runs)
  LEGACY_NET        network 收容 legacy(統包涵蓋)
  DICT_ARCHIVE      dict 歷史歸檔
另:沙盒修補件對勘 — Complete 交付之 8 件 core 修補版 vs 樹內在役版
hash 對比(依其政策 no promotion:僅出審查佇列,零自動套用)。
用法:
  via-govtriage              → 最新 centralgov run 議題分圈+矩陣+清單
  via-govtriage --patches    → 沙盒修補件對勘佇列
  via-govtriage --selftest   → 六檢(合成議題零長跑)
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
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
CG_RUNS = VIA / "VIA_Reports" / "centralgov_runs"
OUT = VIA / "VIA_Reports" / "govtriage_runs"

CIRCLES = [  # 先到先判(順序即優先權)
    ("QUARANTINE", ("_review_quarantine", "quarantine", "_syntaxfix_",
                    "_rebuilds_superseded", "_inbox_to_classify")),
    ("SCOPE_BACKUP", ("SCOPE_COPY", "backup_", "rename_runs", "rollback",
                      "_via_mother_root_reconciliation_runs")),
    ("RUNS_EVIDENCE", ("VIA_Reports", ".via_runs", "/runs/", "evidence",
                       "_vdf_envs", "output_hub")),
    ("EXEMPT_INTAKE", ("new modules engines", "VeritasAutoPlot_v42_EcoSystem",
                       "webscraping_dualengine", "TALib/vendor", "/dict/",
                       "50_Protection_Acceleration", "VIA_Standalone_Package",
                       "docs/history", "references/intake", "_from_vap_iso_cleanup",
                       "package_samples", "_used_", "uploads")),
    ("LEGACY_NET", ("supportive modules/network/",)),
    ("DICT_ARCHIVE", ("dict/",)),
]

SANDBOX_CORES = ["VIA_EnvManager.py", "VIA_SSOT_Unified.py", "VIA_RegistryCore_v1.py",
                 "VIA_Runtime_Bridge_All_in_One.py", "VeritasCeleritas.py",
                 "VeritasAegisNexus.py", "VIA_Panorama_AST_RuntimeInjector.py"]


def circle_of(rp: str) -> str:
    r = rp.replace("\\", "/")
    for name, frags in CIRCLES:
        if any(f in r for f in frags):
            return name
    return "ACTIVE"


def latest_run() -> Path | None:
    hits = sorted(CG_RUNS.glob("RUN_*"))
    return hits[-1] if hits else None


def load_issues(run_dir: Path):
    import pandas as pd
    for cand in ("round_3/issues.csv.gz", "round_3/issues.csv",
                 "round_2/issues.csv.gz", "round_1/issues.csv.gz"):
        p = run_dir / cand
        if p.exists():
            return pd.read_csv(p, dtype=str, keep_default_na=False), p.name
    return None, "議題表缺"


def triage(df) -> dict:
    df = df.copy()
    df["circle"] = df["relative_path"].map(circle_of)
    mat = df.groupby(["circle", "severity"]).size().unstack(fill_value=0)
    act = df[df["circle"] == "ACTIVE"]
    act_crit = act[act["severity"] == "CRITICAL"]
    act_high = act[act["severity"] == "HIGH"]
    by_cat = act_crit.groupby("category").size().sort_values(ascending=False)
    top_files = (act_crit.groupby("relative_path").size()
                 .sort_values(ascending=False).head(15))
    auto_fix = act[act["auto_fixable"].str.lower().isin(("true", "1", "yes"))]
    return {"total": len(df),
            "matrix": {c: {s: int(v) for s, v in row.items() if v}
                       for c, row in mat.iterrows()},
            "active_total": len(act),
            "active_critical": len(act_crit), "active_high": len(act_high),
            "active_critical_by_category": {k: int(v) for k, v in by_cat.items()},
            "active_critical_top_files": {k: int(v) for k, v in top_files.items()},
            "active_auto_fixable": len(auto_fix)}


def compare_patches() -> list[dict]:
    """Complete 交付沙盒修補件 vs 樹內在役版(hash 對勘;零套用)"""
    sand = (VIA / "new modules engines" / "VIA_CentralGovernance_ALL_v0100"
            / "complete" / "VIA_CentralGovernance_AdaptiveDownward_v0100_Delivery" / "sandbox")
    rows = []
    for name in SANDBOX_CORES:
        sp = sand / name
        tp = VIA / "supportive modules" / name
        if not sp.exists():
            rows.append({"file": name, "state": "SANDBOX_MISSING"})
            continue
        if not tp.exists():
            rows.append({"file": name, "state": "TREE_MISSING",
                         "note": "樹內無在役同名件"})
            continue
        hs = hashlib.sha256(sp.read_bytes()).hexdigest()[:16]
        ht = hashlib.sha256(tp.read_bytes()).hexdigest()[:16]
        bak = sand / f"{name}.before_PATCH_ENVMANAGER_EXEC_AND_OUTPUT_GATE.bak"
        rows.append({"file": name,
                     "state": "IDENTICAL" if hs == ht else "PATCH_CANDIDATE_REVIEW",
                     "sandbox_sha16": hs, "tree_sha16": ht,
                     "note": ("全同=已在役" if hs == ht else
                              "沙盒修補版異於在役版;依交付政策 no promotion=候操作員審查,零自動套用")})
    return rows


def run() -> int:
    rd = latest_run()
    if rd is None:
        print("[SKIP] centralgov run 缺(先跑 via-cg --audit)")
        return 0
    df, src = load_issues(rd)
    if df is None:
        print(f"[FAIL] {src}")
        return 1
    t = triage(df)
    print(f"=== 治理議題分圈(批133)· {rd.name[:40]} · {src} · {t['total']:,} 議題 ===")
    for c in ("ACTIVE", "EXEMPT_INTAKE", "QUARANTINE", "SCOPE_BACKUP",
              "RUNS_EVIDENCE", "LEGACY_NET", "DICT_ARCHIVE"):
        row = t["matrix"].get(c, {})
        if row:
            print(f"  [{c:<14}] " + " · ".join(f"{s} {v:,}" for s, v in sorted(row.items())))
    print(f"  [活動圈] 議題 {t['active_total']:,} · CRITICAL {t['active_critical']:,}"
          f" · HIGH {t['active_high']:,} · auto_fixable {t['active_auto_fixable']:,}")
    print("  [活動圈 CRITICAL 分類] "
          + " · ".join(f"{k}×{v}" for k, v in list(t["active_critical_by_category"].items())[:6]))
    for f, n in list(t["active_critical_top_files"].items())[:8]:
        print(f"    · {n:>3} {f[:90]}")
    patches = compare_patches()
    n_cand = sum(1 for r in patches if r["state"] == "PATCH_CANDIDATE_REVIEW")
    print(f"  [沙盒修補對勘] {len(patches)} 件 · 候審 {n_cand} · 全同 "
          f"{sum(1 for r in patches if r['state'] == 'IDENTICAL')}")
    OUT.mkdir(parents=True, exist_ok=True)
    op = OUT / f"TRIAGE_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    op.write_text(json.dumps({"schema": "via.govtriage.v1", "run": rd.name,
                              "source": src, "triage": t, "patch_review": patches},
                             ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [存] {op.relative_to(VIA)}")
    return 0


def selftest() -> int:
    import pandas as pd
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    chk("① 分圈規則(七圈先到先判)",
        circle_of("functional modules/ChipWar/_review_quarantine/x.py") == "QUARANTINE"
        and circle_of("functional modules/VAP/ASSETS/SCOPE_COPY/y.py") == "SCOPE_BACKUP"
        and circle_of("new modules engines/z.py") == "EXEMPT_INTAKE"
        and circle_of("VIA_Reports/run/x.json") == "RUNS_EVIDENCE"
        and circle_of("supportive modules/network/SUP_MDL620_x.py") == "LEGACY_NET"
        and circle_of("functional modules/VRN/vrn_report_digest_v0113.py") == "ACTIVE")
    df = pd.DataFrame([
        {"relative_path": "functional modules/VRN/a.py", "severity": "CRITICAL",
         "category": "SYNTAX", "auto_fixable": "False"},
        {"relative_path": "functional modules/VRN/a.py", "severity": "HIGH",
         "category": "SECURITY", "auto_fixable": "True"},
        {"relative_path": "new modules engines/b.py", "severity": "CRITICAL",
         "category": "SYNTAX", "auto_fixable": "False"},
        {"relative_path": "VIA_Reports/c.json", "severity": "LOW",
         "category": "FORMAT", "auto_fixable": "True"}])
    t = triage(df)
    chk("② 分圈矩陣(ACTIVE 2/EXEMPT 1/RUNS 1)",
        t["total"] == 4 and t["matrix"]["ACTIVE"]["CRITICAL"] == 1
        and t["matrix"]["EXEMPT_INTAKE"]["CRITICAL"] == 1
        and t["matrix"]["RUNS_EVIDENCE"]["LOW"] == 1)
    chk("③ 活動圈萃取(CRIT 1/HIGH 1/autofix 1)",
        t["active_critical"] == 1 and t["active_high"] == 1
        and t["active_auto_fixable"] == 1
        and t["active_critical_by_category"] == {"SYNTAX": 1})
    chk("④ top files 具名", list(t["active_critical_top_files"]) == ["functional modules/VRN/a.py"])
    pr = compare_patches()
    chk("⑤ 沙盒修補對勘(7 件全出列+雙 sha)",
        len(pr) == 7 and all("state" in r for r in pr)
        and all(("sandbox_sha16" in r) for r in pr if r["state"] in ("IDENTICAL", "PATCH_CANDIDATE_REVIEW")))
    chk("⑥ 零自動套用(候審件僅列示)",
        all("no promotion" in r.get("note", "") or r["state"] != "PATCH_CANDIDATE_REVIEW"
            for r in pr))
    n = 6 - len(fails)
    print(f"  [計] 六檢 OK {n} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 治理議題分圈器 · 六檢自測(合成議題)===")
        return selftest()
    if "--patches" in args:
        for r in compare_patches():
            print(f"  [{r['state']:<22}] {r['file']:<40} {r.get('note', '')[:60]}")
        return 0
    return run()


if __name__ == "__main__":
    sys.exit(main())
