#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vrn_scan_ocr_rescue_v0100 — 純影像掃描件 OCR 救援(Mega-Prompt 第 2 輪)
========================================================================
對象:via-pdfcheck 判決 IMAGE_ONLY_SCAN 之檔(MQ-1560 案)。
流程:①fitz 逐頁渲染(預設 300 DPI)②paddleocr 辨識(工作站 SmokeTest
已證綠)③產 MDL005 相容文字列(engine=paddleocr_rescue,segment=OCR_RESCUE)
④併回主表 VRN_MDL005_Text:先備份 .pre_<ts>.bak → 剔同 pdf_name 舊列 →
追加 → parquet+csv 重寫(append-only 備份永留)。
誠實界線:本引擎只救文字層;表格層(MDL004)掃描件另候 PPStructure 鏈,
該檔對帳將為 TEXT_ONLY(覆蓋達成,FULL 候表格鏈)——不假 FULL。
用法:py vrn_scan_ocr_rescue_v0100.py <pattern> [--dpi 300] [--dry-run]
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    pattern = args[0]
    dpi = int(args[args.index("--dpi") + 1]) if "--dpi" in args else 300
    dry = "--dry-run" in args
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    files = sorted((HERE / "input/incoming").glob(pattern))
    if not files:
        print(f"[FAIL] 收件夾無匹配:{pattern}")
        return 1

    try:
        import fitz
    except ImportError:
        print("[FAIL] fitz(PyMuPDF)未安裝 — 誠實停止")
        return 1
    try:
        from paddleocr import PaddleOCR
    except Exception as exc:
        print(f"[FAIL] paddleocr 不可用:{type(exc).__name__}: {exc} — 誠實停止(工作站候修後重跑)")
        return 1
    try:
        import pandas as pd
    except ImportError:
        print("[FAIL] pandas 未安裝 — 誠實停止")
        return 1

    print(f"=== 掃描件 OCR 救援 v0100 · {len(files)} 檔 · {dpi} DPI · {'DRY-RUN' if dry else 'LIVE'} ===")
    ocr = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)
    all_rows = []
    for f in files:
        doc = fitz.open(f)
        print(f"  ── {f.name} · {doc.page_count} 頁 ──")
        for i in range(doc.page_count):
            pg = doc[i]
            pix = pg.get_pixmap(dpi=dpi)
            import numpy as np
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
            if pix.n == 4:
                img = img[:, :, :3]
            try:
                result = ocr.ocr(img, cls=True)
            except TypeError:
                result = ocr.ocr(img)
            lines = []
            for res in (result or []):
                for item in (res or []):
                    try:
                        txt, conf = item[1][0], float(item[1][1])
                    except Exception:
                        continue
                    if txt and txt.strip():
                        lines.append((txt.strip(), conf))
            for seq, (txt, conf) in enumerate(lines, 1):
                all_rows.append({
                    "pdf_name": f.name, "page_no": i + 1,
                    "block_id": f"P{i + 1:03d}OCR{seq:03d}",
                    "text": txt, "engine": "paddleocr_rescue",
                    "segment": "OCR_RESCUE", "confidence": round(conf, 4),
                })
            chars = sum(len(t) for t, _ in lines)
            print(f"     p{i + 1}:{len(lines)} 行 · {chars:,} 字元")
        doc.close()

    if not all_rows:
        print("  [FAIL] OCR 全頁零行 — 誠實停止(影像品質候查;不寫主表)")
        return 1
    print(f"  [OCR] 共 {len(all_rows)} 行文字")
    if dry:
        print("  [dry-run] 不寫主表")
        return 0

    solo = pd.DataFrame(all_rows)
    main_dir = HERE / "staging/ocr_out/mdl005_temp"
    main_dir.mkdir(parents=True, exist_ok=True)
    mp = main_dir / "VRN_MDL005_Text.parquet"
    names = set(solo["pdf_name"].astype(str))
    if mp.exists():
        import shutil
        bak = mp.with_name(mp.stem + f".pre_{ts}.bak.parquet")
        shutil.copy2(mp, bak)
        main = pd.read_parquet(mp)
        before = len(main)
        if "pdf_name" in main.columns:
            main = main[~main["pdf_name"].astype(str).isin(names)]
        dropped = before - len(main)
        merged = pd.concat([main, solo], ignore_index=True)
        print(f"  [備份] {bak.name}")
    else:
        dropped = 0
        merged = solo
    merged.to_parquet(mp, index=False)
    merged.to_csv(mp.with_suffix(".csv"), index=False, encoding="utf-8-sig")
    print(f"  [合併] 舊列剔 {dropped} · 新增 {len(solo)} · 主表共 {len(merged):,} 列(parquet+csv 重寫)")
    print("  [次步] via-reconcile 驗覆蓋(該檔預期 TEXT_ONLY — 表格層候 PPStructure 鏈,誠實不假 FULL)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
