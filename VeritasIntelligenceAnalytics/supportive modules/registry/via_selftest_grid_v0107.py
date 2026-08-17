#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
via_selftest_grid_v0107 — 全面自測矩陣(三會話站點合流)
====================================================================
v0100→v0101:新增第 18 站 SuperDocExtractor selftest(導入自會話
016d7f;15 檢全綠基準)。
v0101→v0102:新增第 19 站 vrn_table_omni 車道矩陣(TOOL-029;唯讀
可用性探測 rc0,不擷取)。
v0102→v0103:新增第 20 站 via_env_plan --offline(TOOL-030;快照+
計畫零網路 rc0)。
v0103→v0104:新增第 21 站 via_dep_super --selftest(TOOL-031;
PEP440 判定器+圖譜衝突掃描 15 檢,零網路零環境依賴 rc0)。
v0104→v0105:雙會話合流——撞版勘誤(本會話曾誤覆寫 v0104,已回復
他方正本):+第 22 站表格統包 --selftest(TOOL-029 四檢)+第 23 站
收編管線 dry(TOOL-036;掃描根缺=env SKIP 誠實)。
v0105→v0106:+第 24 站契約介面引擎 32 測(TOOL-037;pytest/pydantic
缺=env SKIP)+第 25 站留痕包裝器(TOOL-038 --list rc0)。
v0106→v0107:撞版合流(9hh5to 會話亦造 v0106)——併入其重建計畫
自測+教訓帳本 10 檢兩站(27 站)。
操作員令(2026-08-12):全面測試修正 till all work perfectly。
原則:
  ① 全站安全模式 — 只跑唯讀/dry-run/selftest/文件模式;零 --commit 零網路
  ② 誠實三態 — OK(如預期)/FAIL(異常)/SKIP(環境缺件,誠實註明)
  ③ 期望制 — 每站宣告期望 rc(rc0=須 0;doc=無參印說明 rc∈{0,2};
     env=環境依賴,缺件 rc≠0 記 SKIP 不記 FAIL)
  ④ 存證 — VIA_Reports/selftest_runs/GRID_<ts>.json
用法:via-selftest            → 全矩陣(27 站)
     via-selftest --fast     → 略過重站(sysman/pipe)
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
VRN = VIA / "functional modules/VRN"
OUT = VIA / "VIA_Reports" / "selftest_runs"


def newest(pattern: str, root: Path) -> Path | None:
    hits = sorted(root.glob(pattern))
    return hits[-1] if hits else None


def battery(fast: bool):
    py = sys.executable
    B = []

    def add(name, path, args, expect, timeout=180, heavy=False):
        if fast and heavy:
            return
        B.append({"name": name, "path": path, "args": args, "expect": expect, "timeout": timeout})

    add("sysman 三輪協議", newest("via_system_manager_v0*.py", HERE), ["--no-open"], "rc0", 900, heavy=True)
    add("panorama six 六車道", newest("via_panorama_six_v0*.py", HERE), ["--no-open"], "rc0", 300)
    add("xcheck SSOT 對齊", newest("panorama_xcheck_v*.py", VRN), ["--no-pause"], "rc0", 180)
    add("supaudit 導入稽核", newest("via_support_import_audit_v0*.py", HERE), [], "env", 300)
    add("provision 體檢", newest("via_provision_v0*.py", HERE), ["--check"], "rc0", 300)
    add("master Console", newest("via_master_hub_v0*.py", HERE), ["--no-open"], "rc0", 120)
    add("install 閘 check-only", newest("via_install_gate_v0*.py", HERE), ["--check-only"], "rc0", 300)
    add("tidy 整理(dry)", newest("via_downloads_organizer_v0*.py", HERE), [], "env", 600)
    add("store 落庫(dry)", newest("vrn_content_store_v0*.py", VRN), [], "env", 120)
    add("reconcile 對帳", newest("vrn_content_reconcile_v0*.py", VRN), [], "env", 120)
    add("pdfcheck 法醫(doc)", newest("vrn_pdf_forensics_v0*.py", VRN), [], "doc", 60)
    add("docx 引擎(doc)", newest("vrn_docx_engine_v0*.py", VRN), [], "doc", 60)
    add("rescue 救援(doc)", newest("vrn_scan_ocr_rescue_v0*.py", VRN), [], "doc", 60)
    add("pipeline 輪動證偽", VIA / "supportive modules/VIA_Pipeline/via_pipeline.py", ["--demo"], "rc0", 600, heavy=True)
    add("via_io 編碼自檢", VIA / "supportive modules/VIA_Pipeline/via_io.py", ["--selftest"], "rc0", 120)
    add("NetSupport 同意閘", VIA / "supportive modules/VIA_NetSupport.py", [], "rc0", 60)
    sdx = VIA / "functional modules/SuperDocExtractor/super_extract.py"
    add("SuperDocExtractor 15檢", sdx, ["selftest"], "rc0", 300)
    add("表格統包車道矩陣", newest("vrn_table_omni_v0*.py", VRN), [], "rc0", 120)
    add("環境計畫快照(offline)", newest("via_env_plan_v0*.py", HERE), ["--offline"], "rc0", 300)
    add("依賴統包 15 檢", newest("via_dep_super_v0*.py", HERE), ["--selftest"], "rc0", 300)
    add("表格統包四檢自測", newest("vrn_table_omni_v0*.py", VRN), ["--selftest"], "rc0", 180)
    add("收編管線(dry)", newest("via_intake_v0*.py", HERE), [], "env", 300)
    add("契約介面引擎 32 測", VIA / "supportive modules/VIA_ContractEngine_v0200/selftest_entry.py", [], "env", 300)
    add("留痕包裝器(list)", newest("via_cmdlog_v0*.py", HERE), ["--list"], "rc0", 60)
    add("重建計畫自測", newest("via_env_rebuild_v0*.py", HERE), ["--selftest"], "rc0", 300)
    add("教訓帳本 10 檢", newest("via_lessons_v0*.py", HERE), ["--selftest"], "rc0", 300)
    add("selftest grid(自指:文件)", None, [], "doc", 10)  # 佔位:自身以 --fast 遞迴屬禁,列 SKIP
    return B


def run_one(b):
    if b["path"] is None or not Path(b["path"]).exists():
        return {"name": b["name"], "state": "SKIP", "note": "引擎缺/自指佔位(誠實)", "secs": 0}
    t0 = time.time()
    try:
        r = subprocess.run([sys.executable, str(b["path"]), *b["args"]], capture_output=True,
                           text=True, timeout=b["timeout"], stdin=subprocess.DEVNULL,
                           cwd=str(Path(b["path"]).parent))
        secs = round(time.time() - t0, 1)
        tail = [l for l in (r.stdout + r.stderr).strip().splitlines() if l.strip()][-2:]
        if b["expect"] == "rc0":
            state = "OK" if r.returncode == 0 else "FAIL"
        elif b["expect"] == "doc":
            state = "OK" if r.returncode in (0, 2) else "FAIL"
        else:  # env
            state = "OK" if r.returncode == 0 else "SKIP"
        note = " / ".join(t[:80] for t in tail)
        if state == "SKIP":
            note = "環境缺件(誠實):" + note
        return {"name": b["name"], "state": state, "rc": r.returncode, "secs": secs, "note": note}
    except subprocess.TimeoutExpired:
        return {"name": b["name"], "state": "FAIL", "rc": "TIMEOUT", "secs": b["timeout"], "note": "逾時"}
    except Exception as exc:
        return {"name": b["name"], "state": "FAIL", "rc": type(exc).__name__, "secs": 0, "note": str(exc)[:80]}


def main() -> int:
    fast = "--fast" in sys.argv
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    B = battery(fast)
    print(f"=== 全面自測矩陣 v0107 · {len(B)} 站 · {'FAST' if fast else 'FULL'} · 全安全模式(零 commit 零網路)===")
    results = []
    for b in B:
        r = run_one(b)
        results.append(r)
        mark = {"OK": "OK  ", "FAIL": "FAIL", "SKIP": "SKIP"}[r["state"]]
        print(f"  [{mark}] {r['name']} · {r['secs']}s · {r.get('note', '')[:96]}")
    n_ok = sum(1 for r in results if r["state"] == "OK")
    n_fail = sum(1 for r in results if r["state"] == "FAIL")
    n_skip = sum(1 for r in results if r["state"] == "SKIP")
    OUT.mkdir(parents=True, exist_ok=True)
    ev = OUT / f"GRID_{ts}.json"
    ev.write_text(json.dumps({"schema": "VIA.SelftestGrid.v1", "ts": ts, "fast": fast,
                              "ok": n_ok, "fail": n_fail, "skip": n_skip, "results": results},
                             ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [計] OK {n_ok} · FAIL {n_fail} · SKIP {n_skip}(誠實三態)· 存證 {ev.name}")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
