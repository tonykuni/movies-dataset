#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
vrn_docx_merge_v0100 — DOCX 產物併主表(補齊令 2026-08-12)
============================================================
缺口:對帳矩陣 4 支 DOCX Memo 文字塊/表格列=0——via-docx 產物
(staging/ocr_out/docx_struct/<stem>/text.txt + table_N.csv)未併入
MDL005/MDL004 主表。本引擎把 docx_struct 全量摺入主表:
  ① dry-run 預設 — 只出併表計畫;--commit 才寫
  ② 寫前備份 .pre_<ts>.bak.parquet(append-only 永留)
  ③ 冪等 — 同 pdf_name 舊列剔除後插入,重跑不疊加
  ④ 欄位自適應 — 讀主表既有欄位建列,缺欄誠實 None 不硬造
  ⑤ 誠實逐檔矩陣;零 docx_struct 誠實停止
用法:py vrn_docx_merge_v0100.py [--commit]
"""
from __future__ import annotations

import csv
import shutil
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
STRUCT = HERE / "staging/ocr_out/docx_struct"
T005 = HERE / "staging/ocr_out/mdl005_temp/VRN_MDL005_Text.parquet"
T004 = HERE / "staging/ocr_out/mdl004_temp/VRN_MDL004_Tables.parquet"


def main() -> int:
    commit = "--commit" in sys.argv[1:]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    try:
        import pandas as pd
    except ImportError:
        print("[FAIL] pandas 未安裝 — 誠實停止")
        return 1
    if not STRUCT.is_dir() or not any(STRUCT.iterdir()):
        print(f"[FAIL] docx_struct 空/缺({STRUCT})— 先跑 via-docx(誠實停止)")
        return 1

    print(f"=== DOCX 產物併主表 v0100 · {'COMMIT' if commit else 'DRY-RUN(--commit 才寫)'} ===")
    text_rows, cell_rows, names = [], [], set()
    for d in sorted(p for p in STRUCT.iterdir() if p.is_dir()):
        pdf_name = d.name + ".docx"
        names.add(pdf_name)
        tt = d / "text.txt"
        lines = [l.strip() for l in tt.read_text(encoding="utf-8").splitlines() if l.strip()] if tt.exists() else []
        for i, txt in enumerate(lines, 1):
            text_rows.append({"pdf_name": pdf_name, "page_no": 1, "block_id": f"P001DOCX{i:03d}",
                              "text": txt, "engine": "docx_merge", "segment": "DOCX_TEXT"})
        n_cells = 0
        for tc in sorted(d.glob("table_*.csv")):
            tno = int(tc.stem.split("_")[1])
            with open(tc, encoding="utf-8-sig", newline="") as fh:
                for r_i, row in enumerate(csv.reader(fh)):
                    for c_i, val in enumerate(row):
                        if str(val).strip():
                            cell_rows.append({"pdf_name": pdf_name, "page_no": 1, "table_no": tno,
                                              "row": r_i, "col": c_i, "value": val,
                                              "engine": "docx_merge"})
                            n_cells += 1
        print(f"  [檔] {pdf_name} · 文字 {len(lines)} 行 · 表格格 {n_cells}")

    print(f"  [計畫] 文字列 {len(text_rows)} · 表格列 {len(cell_rows)} · 檔 {len(names)}(冪等剔同名舊列)")
    if not commit:
        print("  [dry-run] 零寫入。確認後:via-docxmerge --commit")
        return 0

    for path, rows in ((T005, text_rows), (T004, cell_rows)):
        if not rows:
            print(f"  [WARN] {path.name} 零新列 — 跳過(誠實)")
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        newdf = pd.DataFrame(rows)
        if path.exists():
            bak = path.with_name(path.stem + f".pre_{ts}.bak.parquet")
            shutil.copy2(path, bak)
            main_df = pd.read_parquet(path)
            before = len(main_df)
            if "pdf_name" in main_df.columns:
                main_df = main_df[~main_df["pdf_name"].astype(str).isin(names)]
            # 欄位自適應:對齊主表欄,缺欄 None(誠實不硬造)
            for c in main_df.columns:
                if c not in newdf.columns:
                    newdf[c] = None
            newdf = newdf[[c for c in main_df.columns if c in newdf.columns]
                          + [c for c in newdf.columns if c not in main_df.columns]]
            merged = pd.concat([main_df, newdf], ignore_index=True)
            print(f"  [併] {path.name}:舊剔 {before - len(main_df)} · 新增 {len(rows)} · 共 {len(merged):,}(備份 {bak.name})")
        else:
            merged = newdf
            print(f"  [併] {path.name}:新建 {len(rows)} 列")
        merged.to_parquet(path, index=False)
        merged.to_csv(path.with_suffix(".csv"), index=False, encoding="utf-8-sig")
    print("  [次步] via-reconcile 驗——DOCX 檔文字塊/表格列應轉非零;via-store --commit 落庫更新")
    return 0


if __name__ == "__main__":
    sys.exit(main())
