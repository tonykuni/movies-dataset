#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
vrn_table_omni_v0100 — 本地免費表格函式庫統包引擎(TOOL-029,操作員令 2026-08-12)
==================================================================================
令:apply and implement all local free libs into one engine(表格擷取選型目錄
一~五類)。治理裁定:
  ① 本地免費者實作 — 目錄第一/二類(Camelot/pdfplumber/Tabula/img2table/
     Docling/Unstructured/PP-StructureV2/DeepSeek-OCR)+ 基座 PyMuPDF 內建
     find_tables,共 9 條本地車道,全數車道化統一介面
  ② 雲端/商用者列管不實作 — 第三~五類(LlamaParse/Reducto/Textract/Azure/
     Google/Nanonets/ABBYY)非「本地免費」範疇;誠實列 CLOUD 車道並鎖
     網路同意閘(VIA_NET_CONSENT)+金鑰只走環境變數(紅線),本版不發包
  ③ graceful 全退化 — 函式庫缺席=NOT_INSTALLED 誠實列示,零假綠;
     安裝一律經 via-install 閘(儲存規定),本引擎永不代裝
  ④ 唯讀 — 產物只落 VIA_Reports/tableomni_runs/RUN_<ts>/(gitignore 運行區);
     主表落庫另走 via-docxmerge/via-store 家族,本引擎零寫主表
  ⑤ 多引擎交叉驗證 — ≥2 車道出表時做表數/格數共識對帳(SuperDocExtractor 式)
用法:via-tables                          → 車道可用性矩陣(不擷取)
     via-tables --extract <pdf|檔名>     → 全可用車道擷取+交叉對帳+存證
     via-tables --extract <…> --engines camelot,pdfplumber → 指定車道
     via-tables --extract <…> --pages 1-5 → 頁範圍(車道支援者生效)
"""
from __future__ import annotations

import csv
import importlib.util
import json
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
STAGING = HERE / "staging"
OUT = VIA / "VIA_Reports" / "tableomni_runs"


# ── 錨點 v2:橋接優先載入輔助模組(缺席 graceful None)──────────────
def _via_load(name: str):
    try:
        sys.path.insert(0, str(VIA / "supportive modules"))
        from VRN_SupportBridge import require  # type: ignore
        return require(name)
    except Exception:
        try:
            import importlib
            sys.path.insert(0, str(VIA / "supportive modules"))
            return importlib.import_module(name)
        except Exception:
            return None


_NET = _via_load("VIA_NetSupport")


def _has(mod: str) -> bool:
    try:
        return importlib.util.find_spec(mod) is not None
    except Exception:
        return False


def _java() -> bool:
    return shutil.which("java") is not None


# ── 車道正規化契約:extract(pdf, pages) → list[dict] ────────────────
#    每表 {"page": int|None, "n_rows", "n_cols", "rows": [[str,…],…]}
def _norm(rows, page=None):
    rows = [[("" if c is None else str(c)) for c in r] for r in rows if r]
    if not rows:
        return None
    return {"page": page, "n_rows": len(rows), "n_cols": max(len(r) for r in rows), "rows": rows}


def _lane_pymupdf(pdf: Path, pages):
    import fitz
    out = []
    with fitz.open(pdf) as doc:
        idxs = pages if pages else range(len(doc))
        for i in idxs:
            if i >= len(doc):
                continue
            for tab in doc[i].find_tables().tables:
                t = _norm(tab.extract(), page=i + 1)
                if t:
                    out.append(t)
    return out


def _lane_pdfplumber(pdf: Path, pages):
    import pdfplumber
    out = []
    with pdfplumber.open(pdf) as doc:
        idxs = pages if pages else range(len(doc.pages))
        for i in idxs:
            if i >= len(doc.pages):
                continue
            for rows in doc.pages[i].extract_tables():
                t = _norm(rows, page=i + 1)
                if t:
                    out.append(t)
    return out


def _lane_camelot(pdf: Path, pages):
    import camelot
    pg = ",".join(str(i + 1) for i in pages) if pages else "all"
    out = []
    for flavor in ("lattice", "stream"):
        try:
            tabs = camelot.read_pdf(str(pdf), pages=pg, flavor=flavor)
        except Exception:
            continue
        for tb in tabs:
            t = _norm(tb.df.values.tolist(), page=int(getattr(tb, "page", 0)) or None)
            if t:
                t["note"] = flavor
                out.append(t)
        if out:
            break  # lattice 有果即用;空才退 stream
    return out


def _lane_tabula(pdf: Path, pages):
    if not _java():
        raise RuntimeError("Java 缺席(Tabula 依賴)")
    import tabula
    pg = ",".join(str(i + 1) for i in pages) if pages else "all"
    dfs = tabula.read_pdf(str(pdf), pages=pg, multiple_tables=True, silent=True) or []
    out = []
    for df in dfs:
        t = _norm([list(df.columns)] + df.astype(str).values.tolist())
        if t:
            out.append(t)
    return out


def _lane_img2table(pdf: Path, pages):
    from img2table.document import PDF as I2TPDF
    doc = I2TPDF(str(pdf), pages=list(pages) if pages else None)
    out = []
    for pno, tabs in (doc.extract_tables() or {}).items():
        for tb in tabs:
            rows = [[c.value for c in r] for r in tb.content.values()]
            t = _norm(rows, page=pno + 1)
            if t:
                out.append(t)
    return out


def _lane_docling(pdf: Path, pages):
    from docling.document_converter import DocumentConverter
    doc = DocumentConverter().convert(str(pdf)).document
    out = []
    for tb in getattr(doc, "tables", []):
        try:
            df = tb.export_to_dataframe()
            rows = [list(df.columns)] + df.astype(str).values.tolist()
        except Exception:
            rows = []
        t = _norm(rows)
        if t:
            out.append(t)
    return out


def _lane_unstructured(pdf: Path, pages):
    from unstructured.partition.pdf import partition_pdf
    els = partition_pdf(filename=str(pdf), infer_table_structure=True)
    out = []
    for el in els:
        if getattr(el, "category", "") == "Table":
            html = getattr(getattr(el, "metadata", None), "text_as_html", "") or ""
            rows = [[c.strip() for c in r.split("|")] for r in el.text.splitlines() if r.strip()]
            t = _norm(rows, page=getattr(getattr(el, "metadata", None), "page_number", None))
            if t:
                t["html"] = html[:2000]
                out.append(t)
    return out


def _lane_ppstructure(pdf: Path, pages):
    from paddleocr import PPStructure  # noqa: F401 — 重量車道;頁面點陣化後解析
    import fitz
    eng = PPStructure(table=True, ocr=True, show_log=False)
    out = []
    with fitz.open(pdf) as doc:
        idxs = pages if pages else range(len(doc))
        for i in idxs:
            if i >= len(doc):
                continue
            pix = doc[i].get_pixmap(dpi=200)
            import numpy as np
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3]
            for res in eng(img):
                if res.get("type") == "table":
                    html = res.get("res", {}).get("html", "")
                    out.append({"page": i + 1, "n_rows": html.count("<tr"), "n_cols": 0,
                                "rows": [], "html": html[:4000]})
    return out


def _lane_deepseek_ocr(pdf: Path, pages):
    raise RuntimeError("需本地 VLM 權重+GPU(VIA_DEEPSEEK_OCR_DIR 未備)— 誠實 NOT_READY")


# ── 車道登錄(本地 9 + 雲端列管 7)────────────────────────────────
LANES = [
    # (鍵, 探測模組, 執行器, 註)
    ("pymupdf",      "fitz",         _lane_pymupdf,      "基座內建 find_tables(免費)"),
    ("pdfplumber",   "pdfplumber",   _lane_pdfplumber,   "字元級定位+表格偵測"),
    ("camelot",      "camelot",      _lane_camelot,      "lattice 優先,空退 stream"),
    ("tabula",       "tabula",       _lane_tabula,       "需 Java"),
    ("img2table",    "img2table",    _lane_img2table,    "OpenCV 格線法(輕量)"),
    ("docling",      "docling",      _lane_docling,      "IBM TableFormer(重)"),
    ("unstructured", "unstructured", _lane_unstructured, "LLM 前置切塊(重)"),
    ("ppstructure",  "paddleocr",    _lane_ppstructure,  "百度版面分析(重;中文強)"),
    ("deepseek_ocr", "transformers", _lane_deepseek_ocr, "VLM;需權重+GPU(誠實 NOT_READY)"),
]
CLOUD = [
    ("llamaparse", "LlamaIndex 雲解析"), ("reducto", "視覺大模型 API"),
    ("textract", "AWS"), ("azure_docint", "Azure Document Intelligence"),
    ("google_docai", "Google Cloud"), ("nanonets", "IDP 平台"), ("abbyy", "FlexiCapture"),
]


def _consent() -> bool:
    try:
        return bool(_NET and _NET.net_consent())
    except Exception:
        return False


def matrix() -> int:
    print("=== 表格統包引擎 v0100 · 車道可用性矩陣(唯讀零擷取)===")
    n_in = 0
    for key, probe, _fn, note in LANES:
        ok = _has(probe) and (key != "tabula" or _java())
        if key == "deepseek_ocr":
            ok = False  # 權重未備即不可用(誠實)
        n_in += 1 if ok else 0
        print(f"  [{'INSTALLED    ' if ok else 'NOT_INSTALLED'}] {key:13s} · {note}")
    for key, note in CLOUD:
        gate = "同意閘開" if _consent() else "同意閘關"
        print(f"  [CLOUD·列管   ] {key:13s} · {note}(非本地免費——本版不實作;{gate}+金鑰只走環境變數)")
    print(f"  [計] 本地車道 {n_in}/{len(LANES)} 可用 · 雲端 {len(CLOUD)} 列管")
    print('  [裝] 缺件經閘安裝(儲存規定):via-install camelot-py pdfplumber img2table tabula-py')
    print('       重量車道(擇需):via-install docling unstructured paddleocr')
    return 0


def _resolve_pdf(arg: str) -> Path | None:
    p = Path(arg)
    if p.is_file():
        return p
    hits = sorted(STAGING.rglob(arg)) if STAGING.is_dir() else []
    return hits[0] if hits else None


def _parse_pages(spec: str):
    a, _, b = spec.partition("-")
    return range(int(a) - 1, int(b or a))


def extract(argv: list[str]) -> int:
    pdf = _resolve_pdf(argv[argv.index("--extract") + 1])
    if pdf is None:
        print("[FAIL] PDF 不存在(絕對路徑或 staging 內檔名)— 誠實停止")
        return 1
    pages = _parse_pages(argv[argv.index("--pages") + 1]) if "--pages" in argv else None
    only = set(argv[argv.index("--engines") + 1].split(",")) if "--engines" in argv else None
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run = OUT / f"RUN_{ts}"
    print(f"=== 表格統包擷取 · {pdf.name} · 頁={argv[argv.index('--pages') + 1] if '--pages' in argv else '全'} ===")
    results = []
    for key, probe, fn, note in LANES:
        if only and key not in only:
            continue
        if not _has(probe) or (key == "tabula" and not _java()):
            results.append({"lane": key, "state": "NOT_INSTALLED", "tables": 0})
            print(f"  [NOT_INSTALLED] {key}")
            continue
        t0 = time.time()
        try:
            tabs = fn(pdf, pages)
            secs = round(time.time() - t0, 1)
            ldir = run / key
            ldir.mkdir(parents=True, exist_ok=True)
            cells = 0
            for n, t in enumerate(tabs, 1):
                cells += sum(1 for r in t["rows"] for c in r if str(c).strip())
                with open(ldir / f"table_{n}.csv", "w", encoding="utf-8-sig", newline="") as fh:
                    csv.writer(fh).writerows(t["rows"])
            results.append({"lane": key, "state": "OK", "tables": len(tabs), "cells": cells, "secs": secs})
            print(f"  [OK  ] {key:13s} · 表 {len(tabs)} · 非空格 {cells} · {secs}s")
        except Exception as exc:
            results.append({"lane": key, "state": "FAIL", "tables": 0, "note": str(exc)[:120]})
            print(f"  [FAIL] {key:13s} · {str(exc)[:90]}(誠實記錄,不斷鏈)")
    ran = [r for r in results if r["state"] == "OK"]
    if len(ran) >= 2:
        counts = sorted(r["tables"] for r in ran)
        med = counts[len(counts) // 2]
        agree = sum(1 for r in ran if r["tables"] == med)
        print(f"  [交叉] {len(ran)} 車道成表 · 表數共識={med}(同意 {agree}/{len(ran)})· 詳見存證")
    elif len(ran) == 1:
        print(f"  [交叉] 僅 1 車道可跑({ran[0]['lane']})— 無從交叉,誠實單源")
    else:
        print("  [交叉] 零車道成果——先經 via-install 閘補裝(誠實)")
    run.mkdir(parents=True, exist_ok=True)
    ev = run / "summary.json"
    ev.write_text(json.dumps({"schema": "VIA.TableOmni.v1", "ts": ts, "pdf": pdf.name,
                              "lanes": results, "cloud_registered_not_implemented": [c[0] for c in CLOUD],
                              "policy": "readonly·no_main_table_write·install_via_gate_only"},
                             ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [存證] {ev.relative_to(VIA)}(CSV 逐車道逐表)")
    print("  [鐵則] 唯讀擷取;主表落庫另走 via-store 家族(人工確認)")
    return 0


def main() -> int:
    argv = sys.argv[1:]
    if "--extract" in argv:
        return extract(argv)
    return matrix()


if __name__ == "__main__":
    sys.exit(main())
