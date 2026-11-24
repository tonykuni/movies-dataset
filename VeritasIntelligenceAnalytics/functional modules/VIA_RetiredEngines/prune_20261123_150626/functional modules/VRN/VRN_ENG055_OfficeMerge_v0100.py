#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
vrn_office_merge_v0100 — Office(xlsx/csv)併主表橋(TOOL-044;操作員核准 2026-08-18)
====================================================================================
缺口:DOCX 已有 via-docx→via-docxmerge 鏈;xlsx/csv 表骨無橋入 VRN 主表。
本橋比照 docxmerge 契約,以 SuperDocExtractor(TOOL-026)為擷取引擎:
  ① 收件夾 staging/office_in/ 內 *.xlsx/*.xls/*.csv → extract_any()
     (合併格還原/參差列修復/編碼修復/數值等價全繼承)
  ② 摺入 MDL004(表格格):{pdf_name=檔名, page_no=工作表序(csv=1),
     table_no, row, col, value, engine="office_merge"}
  ③ 文字层(xlsx 罕有;有才寫):MDL005 {pdf_name, page_no=1,
     block_id=P001OFCnnn, text, engine="office_merge", segment="OFFICE_TEXT"}
  ④ dry-run 預設;--commit 寫;寫前 .pre_<ts>.bak.parquet;冪等剔同 pdf_name;
     欄位自適應缺欄誠實 None;零件誠實停
誠實界線:office 件多未入 VRN SSOT v2(64 報告)——落主表帶 engine 標記,
對帳矩陣外屬附表資料(候 SSOT 收錄再入對帳)。
用法:via-officemerge            → dry-run 計畫
     via-officemerge --commit   → 執行併表
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

import shutil
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
INBOX = HERE / "staging/office_in"
T005 = HERE / "staging/ocr_out/mdl005_temp/VRN_MDL005_Text.parquet"
T004 = HERE / "staging/ocr_out/mdl004_temp/VRN_MDL004_Tables.parquet"
SDX = VIA / "functional modules/SuperDocExtractor"
EXTS = {".xlsx", ".xls", ".csv"}


def main() -> int:
    commit = "--commit" in sys.argv[1:]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    try:
        import pandas as pd
    except ImportError:
        print("[FAIL] pandas 未裝 — 誠實停止")
        return 1
    sys.path.insert(0, str(SDX))
    try:
        from superextract.pipeline import extract_any
    except ImportError as exc:
        print(f"[FAIL] SuperDocExtractor 缺({exc})— 誠實停止")
        return 1
    INBOX.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in INBOX.iterdir() if p.suffix.lower() in EXTS)
    if not files:
        print(f"[SKIP] 收件夾空:{INBOX}(把 xlsx/csv 丟入後重跑;誠實零動作)")
        return 0

    print(f"=== Office 併主表橋 v0100 · {len(files)} 件 · {'COMMIT' if commit else 'DRY-RUN(--commit 才寫)'} ===")
    text_rows, cell_rows, names = [], [], set()
    for f in files:
        try:
            res = extract_any(str(f))
        except Exception as exc:
            print(f"  [FAIL] {f.name} · {type(exc).__name__}: {str(exc)[:70]}(誠實記錄,不斷鏈)")
            continue
        names.add(f.name)
        n_cells = 0
        for tno, g in enumerate(res.tables, 1):
            page = tno if f.suffix.lower() in (".xlsx", ".xls") else 1  # xlsx 工作表序≈page
            for r_i, row in enumerate(g.rows):
                for c_i, val in enumerate(row):
                    if val is not None and str(val).strip():
                        cell_rows.append({"pdf_name": f.name, "page_no": page, "table_no": tno,
                                          "row": r_i, "col": c_i, "value": str(val),
                                          "engine": "office_merge"})
                        n_cells += 1
        lines = [l.strip() for l in (res.text or "").splitlines() if l.strip()]
        for i, txt in enumerate(lines, 1):
            text_rows.append({"pdf_name": f.name, "page_no": 1, "block_id": f"P001OFC{i:03d}",
                              "text": txt, "engine": "office_merge", "segment": "OFFICE_TEXT"})
        issues = len(res.issues)
        print(f"  [檔] {f.name} · 表 {len(res.tables)} · 格 {n_cells} · 文字 {len(lines)} 行"
              + (f" · 驗證議題 {issues}(見引擎報告)" if issues else ""))

    print(f"  [計畫] 表格列 {len(cell_rows)} · 文字列 {len(text_rows)} · 檔 {len(names)}(冪等剔同名舊列)")
    if not cell_rows and not text_rows:
        print("  [停] 零可併內容(誠實)")
        return 0
    if not commit:
        print("  [dry-run] 零寫入。確認後:via-officemerge --commit")
        return 0

    for path, rows in ((T004, cell_rows), (T005, text_rows)):
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
            main_df = main_df[~main_df["pdf_name"].isin(names)]  # 冪等:剔同名舊列
            for col in main_df.columns:
                if col not in newdf.columns:
                    newdf[col] = None  # 欄位自適應:缺欄誠實 None
            newdf = newdf[[c for c in main_df.columns]]
            out = pd.concat([main_df, newdf], ignore_index=True)
            print(f"  [併] {path.name}:舊剔 {before - len(main_df)} · 新增 {len(newdf)} · 共 {len(out):,}"
                  f"(備份 {bak.name})")
        else:
            out = newdf
            print(f"  [併] {path.name}:新建 · {len(out):,} 列")
        out.to_parquet(path, index=False)
    print("  [次步] via-store --commit 落庫更新(人工確認)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
