#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vrn_scan_ocr_rescue_v0104 — 純影像掃描件 OCR 救援(mobile 模型加速版)
========================================================================
對象:via-pdfcheck 判決 IMAGE_ONLY_SCAN 之檔(MQ-1560 案)。
流程:①fitz 逐頁渲染(預設 300 DPI)②paddleocr 辨識(工作站 SmokeTest
已證綠)③產 MDL005 相容文字列(engine=paddleocr_rescue,segment=OCR_RESCUE)
④併回主表 VRN_MDL005_Text:先備份 .pre_<ts>.bak → 剔同 pdf_name 舊列 →
追加 → parquet+csv 重寫(append-only 備份永留)。
誠實界線:本引擎只救文字層;表格層(MDL004)掃描件另候 PPStructure 鏈,
該檔對帳將為 TEXT_ONLY(覆蓋達成,FULL 候表格鏈)——不假 FULL。
v0102(操作員機二爆修正):3.x 參數關過後倒在 paddlex 管線建立 —
DependencyError: OCR requires additional dependencies(torch 重裝連帶拔件
後遺症;SmokeTest 只驗 import,pipeline 建立才需 paddlex[ocr])。
本版:依賴錯誤誠實攔截,印精準補件令後停;版號橫幅動態化。
v0104(四輪實錄修正):300DPI 偵測段仍崩、200DPI 過偵測進辨識但 server
模型 CPU 過慢遭 Ctrl+C。對策:①預設改 PP-OCRv5 mobile det/rec(CPU 快一
量級)②關文件前處理(方向分類/UVDoc 攤平——掃描件多不需)③DPI 改
150 起跳(150→200→300 升階)④逐頁起跑先報進度。--server 可切回大模型。
用法:py vrn_scan_ocr_rescue_v0104.py <pattern> [--dpi 150] [--server] [--dry-run]
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
    dpi = int(args[args.index("--dpi") + 1]) if "--dpi" in args else 150
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

    server = "--server" in args

    def build_ocr():
        """版本自適應建構:3.x mobile 優先(CPU 速度)→3.x 預設→2.x 梯次。"""
        last = None
        mobile = {} if server else {
            "text_detection_model_name": "PP-OCRv5_mobile_det",
            "text_recognition_model_name": "PP-OCRv5_mobile_rec",
        }
        for kw in ({"use_textline_orientation": True, "lang": "ch",
                    "use_doc_orientation_classify": False, "use_doc_unwarping": False, **mobile},
                   {"use_textline_orientation": True, "lang": "ch"},
                   {"use_angle_cls": True, "lang": "ch", "show_log": False},
                   {"use_angle_cls": True, "lang": "ch"},
                   {"lang": "ch"}):
            try:
                o = PaddleOCR(**kw)
                print(f"  [paddle] 建構參數:{kw}")
                return o
            except (ValueError, TypeError) as exc:
                last = exc  # 參數不合 → 試下一梯
            except Exception as exc:
                # 依賴層錯誤(paddlex DependencyError/RuntimeError)— 換參數無解,誠實停
                msg = str(exc)
                cause = str(getattr(exc, "__cause__", "") or "")
                if "depend" in (msg + cause).lower() or "Dependency" in cause:
                    print("  [FAIL] paddlex OCR 附屬件缺失(torch 重裝連帶拔件後遺症)— 誠實停止")
                    print('  [補件] py -m pip install --user "paddlex[ocr]"')
                    print("  [註]  補件後重跑本指令;SmokeTest 只驗 import,管線建立才需此件")
                    raise SystemExit(1)
                raise
        raise last

    def run_ocr(o, image):
        """辨識雙路:3.x predict(rec_texts/rec_scores)→ 2.x ocr(item[1])。回 [(text, conf)]。"""
        try:
            res = o.predict(image)
            lines = []
            for r in (res or []):
                texts = scores = None
                try:
                    texts, scores = r["rec_texts"], r["rec_scores"]
                except Exception:
                    j = getattr(r, "json", None)
                    if isinstance(j, dict):
                        rr = j.get("res", j)
                        texts, scores = rr.get("rec_texts"), rr.get("rec_scores")
                for t, c in zip(texts or [], scores or [1.0] * len(texts or [])):
                    if t and str(t).strip():
                        lines.append((str(t).strip(), float(c)))
            return lines
        except AttributeError:
            pass
        try:
            result = o.ocr(image, cls=True)
        except TypeError:
            result = o.ocr(image)
        lines = []
        for res in (result or []):
            for item in (res or []):
                try:
                    t, c = item[1][0], float(item[1][1])
                except Exception:
                    continue
                if t and t.strip():
                    lines.append((t.strip(), c))
        return lines
    try:
        import pandas as pd
    except ImportError:
        print("[FAIL] pandas 未安裝 — 誠實停止")
        return 1

    print(f"=== 掃描件 OCR 救援 v0104 · {len(files)} 檔 · {dpi} DPI 起跳 · {'server' if server else 'mobile'} 模型 · {'DRY-RUN' if dry else 'LIVE'} ===")
    ocr = build_ocr()
    all_rows = []
    for f in files:
        doc = fitz.open(f)
        print(f"  ── {f.name} · {doc.page_count} 頁 ──")
        import tempfile
        import os as _os
        for i in range(doc.page_count):
            pg = doc[i]
            print(f"     p{i + 1}/{doc.page_count} 起跑…", flush=True)
            lines = []
            for try_dpi in dict.fromkeys([dpi, 200, 300]):  # DPI 升階梯(150 起跳;去重保序)
                pix = pg.get_pixmap(dpi=try_dpi)
                fd, tmp_png = tempfile.mkstemp(suffix=".png")
                _os.close(fd)
                try:
                    pix.save(tmp_png)  # 餵檔案路徑:paddlex 自理讀圖/前處理(裸 numpy 大圖曾致原生層崩)
                    lines = run_ocr(ocr, tmp_png)
                    if lines:
                        if try_dpi != dpi:
                            print(f"     (p{i + 1} 於 {try_dpi} DPI 降階成功)")
                        break
                except Exception as exc:
                    print(f"     (p{i + 1} @{try_dpi}DPI {type(exc).__name__}:{str(exc)[:50]} → 降階重試)")
                finally:
                    try:
                        _os.remove(tmp_png)
                    except OSError:
                        pass
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
