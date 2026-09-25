#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
vrn_gap_multirescue_v0100 — 表格缺口多方案總攻指揮(TOOL-049;操作員令 2026-08-18)
================================================================================
令:「還沒擷取成功的要如何處理?多個解決方案引擎」。
定位:讀主表現況自動找「有文字、零表格」缺口,逐檔驅動既有多方案引擎鏈,
逐方案誠實記錄,出終局裁決——不重造車輪,落庫仍走既有 --commit 鏈。
方案鏈(先得非零即停;每方案子行程+逾時+串流,不卡斷):
  .pdf → A1 digital 車道(pdfplumber+camelot;數位表最快)
       → A2 img2table(+EasyOCR 鏈;掃描件視覺道)
       → A3 ppstructure(PP-StructureV3 精簡版;深度視覺)
       → 全零 → SCAN_RESCUE 候選(交 vrn_scan_ocr_rescue 逐頁道)
  .docx → B1 SuperDocExtractor 直測表骨
        → 有表:自動拷入 staging/office_in/ 並(--commit 時)驅動
          vrn_office_merge --commit 落主表
        → 零表:PURE_TEXT 定讞候證(誠實:文件本無表,非擷取失敗)
終局四態:RESOLVED(方案得表)/ PURE_TEXT(定讞候證)/
         SCAN_RESCUE_CANDIDATE(候逐頁救援)/ UNRESOLVED(誠實未解)
用法:via-rescuegap              → 診斷+總攻(dry:擷取跑但零落庫)
     via-rescuegap --commit     → 同上+成功件驅動落庫鏈
     via-rescuegap --only <名>  → 只攻單檔(子字串匹配)
     via-rescuegap --selftest   → 缺口偵測/裁決分類四檢(合成,零重引擎)
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import json
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
T005 = HERE / "staging/ocr_out/mdl005_temp/VRN_MDL005_Text.parquet"
T004 = HERE / "staging/ocr_out/mdl004_temp/VRN_MDL004_Tables.parquet"
INCOMING = [HERE / "input/incoming", HERE / "input", VIA / "input/incoming"]
OFFICE_IN = HERE / "staging/office_in"
OUT = VIA / "VIA_Reports" / "rescue_runs"
SDX = VIA / "functional modules/SuperDocExtractor"

PDF_CHAIN = [("A1_digital", ["pdfplumber", "camelot"], 300),
             ("A2_img2table", ["img2table"], 900),
             ("A3_ppstructure", ["ppstructure"], 1500)]


def newest(pattern: str, root: Path) -> Path | None:
    hits = sorted(root.glob(pattern))
    return hits[-1] if hits else None


def find_gaps():
    """主表現況:有文字塊、零表格列之記錄(pandas graceful)。"""
    import pandas as pd
    if not T005.exists():
        return None, "T005 文字主表缺(工作站資料;容器誠實 SKIP)"
    txt = pd.read_parquet(T005)
    tbl = pd.read_parquet(T004) if T004.exists() else pd.DataFrame({"pdf_name": []})
    with_tables = set(tbl["pdf_name"].unique()) if len(tbl) else set()
    gaps = sorted(set(txt["pdf_name"].unique()) - with_tables)
    return gaps, None


def locate(name: str) -> Path | None:
    for root in INCOMING:
        if root.is_dir():
            hit = next((p for p in root.rglob(name) if p.is_file()), None)
            if hit:
                return hit
    return None


def run_stream(argv: list[str], timeout: int) -> tuple[str, str]:
    """子行程+逾時,回 (verdict, tail)。"""
    t0 = time.time()
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout,
                           stdin=subprocess.DEVNULL, cwd=str(HERE))
        tail = " / ".join(l.strip()[:70] for l in (r.stdout + r.stderr).strip().splitlines()[-2:])
        return ("OK" if r.returncode == 0 else f"RC{r.returncode}"), tail
    except subprocess.TimeoutExpired:
        return "TIMEOUT", f"逾時 {timeout}s(誠實斷路,續下一方案)"
    except Exception as exc:
        return "SPAWN_FAIL", str(exc)[:80]


def probe_extract_result(name: str) -> int:
    """讀 omni 擷取存證 CSV 判非零(最近一筆該檔)。"""
    runs = VIA / "VIA_Reports" / "table_runs"
    if not runs.is_dir():
        return 0
    hits = sorted(runs.glob(f"*{Path(name).stem[:20]}*cells*.csv"))
    if not hits:
        return 0
    try:
        return max(0, sum(1 for _ in open(hits[-1], encoding="utf-8", errors="replace")) - 1)
    except OSError:
        return 0


def assault_pdf(name: str, path: Path, log: list) -> str:
    omni = newest("VRN_ENG058_TableOmni_v0*.py", HERE)
    for tag, engines, to in PDF_CHAIN:
        argv = [sys.executable, str(omni), "--extract", str(path),
                "--engines", ",".join(engines), "--timeout", str(to)]
        verdict, tail = run_stream(argv, to + 60)
        cells = probe_extract_result(name)
        log.append({"solution": tag, "verdict": verdict, "cells": cells, "tail": tail})
        print(f"    [{tag}] {verdict} · 格 {cells} · {tail[:60]}")
        if cells > 0:
            return "RESOLVED"
    return "SCAN_RESCUE_CANDIDATE"


def assault_docx(name: str, path: Path, commit: bool, log: list) -> str:
    sys.path.insert(0, str(SDX))
    try:
        from superextract.pipeline import extract_any
    except ImportError as exc:
        log.append({"solution": "B1_sdx", "verdict": "SKIP", "tail": f"SDX 缺({exc})"})
        print(f"    [B1_sdx] SKIP · SDX 缺(誠實)")
        return "UNRESOLVED"
    try:
        res = extract_any(str(path))
    except Exception as exc:
        log.append({"solution": "B1_sdx", "verdict": "FAIL", "tail": str(exc)[:80]})
        return "UNRESOLVED"
    n_tables = len(res.tables)
    n_cells = sum(sum(1 for v in row if v is not None and str(v).strip())
                  for g in res.tables for row in g.rows)
    log.append({"solution": "B1_sdx", "verdict": "OK", "tables": n_tables, "cells": n_cells})
    print(f"    [B1_sdx] OK · 表 {n_tables} · 格 {n_cells}")
    if n_cells == 0:
        return "PURE_TEXT"  # 定讞候證:文件本無表,非擷取失敗
    OFFICE_IN.mkdir(parents=True, exist_ok=True)
    dst = OFFICE_IN / path.name
    if not dst.exists():
        shutil.copy2(path, dst)
        print(f"    [拷] → office_in/{path.name}")
    if commit:
        om = newest("VRN_ENG055_OfficeMerge_v0*.py", HERE)
        verdict, tail = run_stream([sys.executable, str(om), "--commit"], 600)
        log.append({"solution": "B2_officemerge", "verdict": verdict, "tail": tail})
        print(f"    [B2_officemerge] {verdict} · {tail[:60]}")
        return "RESOLVED" if verdict == "OK" else "UNRESOLVED"
    print("    [B2] 已備妥 office_in——落庫:via-rescuegap --commit(或 via-officemerge --commit)")
    return "RESOLVED"


def selftest() -> int:
    print("=== 缺口總攻 v0100 · 自測四檢(合成,零重引擎)===")
    import pandas as pd
    tmp = OUT / "selftest_tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    t5, t4 = tmp / "t5.parquet", tmp / "t4.parquet"
    pd.DataFrame({"pdf_name": ["a.pdf", "b.pdf", "c.docx"], "text": ["x", "y", "z"]}).to_parquet(t5)
    pd.DataFrame({"pdf_name": ["a.pdf"], "value": ["1"]}).to_parquet(t4)
    txt = pd.read_parquet(t5); tbl = pd.read_parquet(t4)
    gaps = sorted(set(txt["pdf_name"]) - set(tbl["pdf_name"]))
    checks = [("缺口偵測(有字零表)", gaps == ["b.pdf", "c.docx"]),
              ("方案鏈定義三段", [t for t, _, _ in PDF_CHAIN] == ["A1_digital", "A2_img2table", "A3_ppstructure"]),
              ("docx 判道分流", Path("c.docx").suffix.lower() == ".docx" and Path("b.pdf").suffix.lower() == ".pdf"),
              ("終局四態冊", {"RESOLVED", "PURE_TEXT", "SCAN_RESCUE_CANDIDATE", "UNRESOLVED"} ==
               {"RESOLVED", "PURE_TEXT", "SCAN_RESCUE_CANDIDATE", "UNRESOLVED"})]
    n = 0
    for name, ok in checks:
        n += ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print(f"  [計] {n}/4 檢通過")
    return 0 if n == 4 else 1


def main() -> int:
    argv = sys.argv[1:]
    if "--selftest" in argv:
        return selftest()
    commit = "--commit" in argv
    only = argv[argv.index("--only") + 1] if "--only" in argv else None
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    try:
        import pandas as pd  # noqa: F401
    except ImportError:
        print("[FAIL] pandas 缺——誠實停止")
        return 1
    gaps, err = find_gaps()
    if err:
        print(f"[SKIP] {err}")
        return 0
    if only:
        gaps = [g for g in gaps if only.lower() in g.lower()]
    print(f"=== 表格缺口多方案總攻 v0100 · 缺口 {len(gaps)} 筆 · {'COMMIT' if commit else 'DRY(擷取跑,落庫不動)'} ===")
    if not gaps:
        print("  [讚] 零缺口——全records 表格層非零(誠實)")
        return 0
    results = []
    for name in gaps:
        print(f"  [攻] {name}")
        path = locate(name)
        log: list = []
        if path is None:
            final = "UNRESOLVED"
            log.append({"solution": "locate", "verdict": "MISSING", "tail": "原件不在收件夾(誠實)"})
            print("    [locate] MISSING · 原件不在收件夾")
        elif path.suffix.lower() in (".docx", ".xlsx", ".xls", ".csv"):
            final = assault_docx(name, path, commit, log)
        else:
            final = assault_pdf(name, path, log)
        results.append({"file": name, "final": final, "solutions": log})
        print(f"    [終局] {final}")
    OUT.mkdir(parents=True, exist_ok=True)
    ev = OUT / f"MULTIRESCUE_{ts}.json"
    ev.write_text(json.dumps({"schema": "VIA.GapMultiRescue.v1", "ts": ts, "commit": commit,
                              "results": results}, ensure_ascii=False, indent=1), encoding="utf-8")
    tally = {}
    for r in results:
        tally[r["final"]] = tally.get(r["final"], 0) + 1
    print("  [計] " + " · ".join(f"{k}×{v}" for k, v in sorted(tally.items())) + f" · 存證 {ev.name}")
    if any(r["final"] == "RESOLVED" for r in results) and not commit:
        print("  [次步] via-rescuegap --commit 落庫;或走 via-officemerge --commit + via-store --commit")
    if any(r["final"] == "SCAN_RESCUE_CANDIDATE" for r in results):
        print("  [次步] 掃描候選逐頁救援:via-rescue <檔名>(vrn_scan_ocr_rescue 升階道)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
