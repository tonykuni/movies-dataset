#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
vrn_table_omni_v0101 — 本地免費表格函式庫統包引擎(TOOL-029)
==================================================================================
v0100→v0101(工作站首戰 MQ-1560 回饋修,三缺陷+兩強化):
  ① ppstructure 車道 API 斷點修 — paddleocr 3.x 移除 PPStructure,改
     PPStructureV3(pipeline.predict 直餵 PDF);雙軌支援 2.x/3.x,
     HTML 產物遞迴收割+解析為列
  ② 視覺車道模型下載鎖同意閘 — ppstructure/docling 首跑需下載模型權重
     (網路行為紅線):模型未快取+VIA_NET_CONSENT 未同意=誠實 SKIP_同意閘
  ③ 缺件提示 — ximgproc→via-install opencv-contrib-python;
     pi_heif→via-install pi-heif(FAIL 註記附修復令)
  ④ 掃描件前診 — fitz 探文字層逐頁;圖片件誠實告示「文字車道 0 屬預期,
     以視覺車道為準」,交叉共識分軌(文字/視覺)不誤判
  ⑤ --selftest — HTML 表解析+數位原生擷取+掃描件前診三檢(合成件,零網路)
治理不變:本地免費 9 車道實作;雲端 7 列管不實作(同意閘+金鑰只走環境變數);
缺件誠實 NOT_INSTALLED;安裝一律 via-install 閘;唯讀零寫主表。
用法:via-tables                          → 車道可用性矩陣(不擷取)
     via-tables --extract <pdf|檔名>     → 全可用車道擷取+交叉對帳+存證
     via-tables --extract <…> --engines camelot,ppstructure → 指定車道
     via-tables --extract <…> --pages 1-5 → 頁範圍(車道支援者生效)
     via-tables --selftest               → 三檢自測(零網路)
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

import csv
import importlib.util
import json
import re
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


class _ConsentGate(RuntimeError):
    """模型未快取且網路同意閘未開——誠實 SKIP,不發包(紅線)。"""


def _has(mod: str) -> bool:
    try:
        return importlib.util.find_spec(mod) is not None
    except Exception:
        return False


def _java() -> bool:
    return shutil.which("java") is not None


def _consent() -> bool:
    try:
        return bool(_NET and _NET.net_consent())
    except Exception:
        return False


def _model_cached(*rel_dirs: str) -> bool:
    for d in rel_dirs:
        p = Path.home() / d
        if p.is_dir() and any(p.iterdir()):
            return True
    return False


# ── HTML 表產物 → 列(ppstructure/unstructured 共用)────────────────
def _html_rows(html: str):
    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S | re.I):
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S | re.I)
        rows.append([re.sub(r"<[^>]+>", "", c).strip() for c in cells])
    return [r for r in rows if any(x for x in r)]


def _harvest_html(obj, sink: list):
    """遞迴收割任意巢狀結構內的 <table> HTML 字串(3.x 結果形狀防波堤)。"""
    if isinstance(obj, str):
        if "<table" in obj.lower():
            sink.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            _harvest_html(v, sink)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            _harvest_html(v, sink)


# ── 車道正規化契約:extract(pdf, pages) → list[dict] ────────────────
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
    if not _model_cached(".cache/docling", ".cache/huggingface") and not _consent():
        raise _ConsentGate("TableFormer 模型未快取+同意閘關——同意後 setx VIA_NET_CONSENT YES(新視窗)首跑下載")
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
            rows = _html_rows(html) if html else [
                [c.strip() for c in r.split("|")] for r in el.text.splitlines() if r.strip()]
            t = _norm(rows, page=getattr(getattr(el, "metadata", None), "page_number", None))
            if t:
                t["html"] = html[:2000]
                out.append(t)
    return out


def _lane_ppstructure(pdf: Path, pages):
    if not _model_cached(".paddlex/official_models", ".paddleocr") and not _consent():
        raise _ConsentGate("Paddle 模型未快取+同意閘關——同意後 setx VIA_NET_CONSENT YES(新視窗)首跑下載")
    try:  # 3.x 新 API(pipeline 直餵 PDF;頁範圍由 pipeline 全量,誠實註記)
        from paddleocr import PPStructureV3
        pipe = PPStructureV3()
        htmls: list[str] = []
        for res in pipe.predict(input=str(pdf)):
            d = getattr(res, "json", None) or (res if isinstance(res, dict) else None)
            if d is None:
                d = {k: getattr(res, k) for k in dir(res) if k in ("res", "table_res_list")}
            _harvest_html(d, htmls)
        out = []
        for h in htmls:
            t = _norm(_html_rows(h))
            if t:
                t["html"] = h[:4000]
                out.append(t)
        return out
    except ImportError:
        pass
    from paddleocr import PPStructure  # 2.x 舊 API:逐頁點陣化
    import fitz
    import numpy as np
    eng = PPStructure(table=True, ocr=True, show_log=False)
    out = []
    with fitz.open(pdf) as doc:
        idxs = pages if pages else range(len(doc))
        for i in idxs:
            if i >= len(doc):
                continue
            pix = doc[i].get_pixmap(dpi=200)
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3]
            for res in eng(img):
                if res.get("type") == "table":
                    html = res.get("res", {}).get("html", "")
                    t = _norm(_html_rows(html), page=i + 1)
                    if t:
                        t["html"] = html[:4000]
                        out.append(t)
    return out


def _lane_deepseek_ocr(pdf: Path, pages):
    raise RuntimeError("需本地 VLM 權重+GPU(VIA_DEEPSEEK_OCR_DIR 未備)— 誠實 NOT_READY")


# ── 車道登錄(本地 9 + 雲端列管 7)────────────────────────────────
TEXT_LANES = {"pymupdf", "pdfplumber", "camelot", "tabula"}  # 依文字層;掃描件必零
LANES = [
    ("pymupdf",      "fitz",         _lane_pymupdf,      "基座內建 find_tables(免費)"),
    ("pdfplumber",   "pdfplumber",   _lane_pdfplumber,   "字元級定位+表格偵測"),
    ("camelot",      "camelot",      _lane_camelot,      "lattice 優先,空退 stream"),
    ("tabula",       "tabula",       _lane_tabula,       "需 Java"),
    ("img2table",    "img2table",    _lane_img2table,    "OpenCV 格線法(輕量;視覺)"),
    ("docling",      "docling",      _lane_docling,      "IBM TableFormer(重;視覺)"),
    ("unstructured", "unstructured", _lane_unstructured, "LLM 前置切塊(重;視覺)"),
    ("ppstructure",  "paddleocr",    _lane_ppstructure,  "百度版面分析(重;中文強;視覺)"),
    ("deepseek_ocr", "transformers", _lane_deepseek_ocr, "VLM;需權重+GPU(誠實 NOT_READY)"),
]
CLOUD = [
    ("llamaparse", "LlamaIndex 雲解析"), ("reducto", "視覺大模型 API"),
    ("textract", "AWS"), ("azure_docint", "Azure Document Intelligence"),
    ("google_docai", "Google Cloud"), ("nanonets", "IDP 平台"), ("abbyy", "FlexiCapture"),
]
HINTS = {  # 已知缺件→修復令(經閘)
    "ximgproc": "修:via-install opencv-contrib-python",
    "pi_heif": "修:via-install pi-heif",
    "pdf2image": "修:via-install pdf2image(另需 poppler)",
    "pytesseract": "修:需 Tesseract 本體(擇需)",
}


def _hint(msg: str) -> str:
    for key, fix in HINTS.items():
        if key in msg:
            return f"({fix})"
    return ""


def matrix() -> int:
    print("=== 表格統包引擎 v0101 · 車道可用性矩陣(唯讀零擷取)===")
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
    print('       視覺車道補件:via-install opencv-contrib-python pi-heif · 重量擇需:via-install docling paddleocr')
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


def _preflight(pdf: Path):
    """掃描件前診:文字層逐頁探測(fitz 缺席誠實 None)。"""
    try:
        import fitz
        with fitz.open(pdf) as doc:
            n = len(doc)
            n_txt = sum(1 for pg in doc if pg.get_text().strip())
        return n, n_txt
    except Exception:
        return None, None


def extract(argv: list[str]) -> int:
    pdf = _resolve_pdf(argv[argv.index("--extract") + 1])
    if pdf is None:
        print("[FAIL] PDF 不存在(絕對路徑或 staging 內檔名)— 誠實停止")
        return 1
    pages = _parse_pages(argv[argv.index("--pages") + 1]) if "--pages" in argv else None
    only = set(argv[argv.index("--engines") + 1].split(",")) if "--engines" in argv else None
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run = OUT / f"RUN_{ts}"
    print(f"=== 表格統包擷取 v0101 · {pdf.name} · 頁={argv[argv.index('--pages') + 1] if '--pages' in argv else '全'} ===")
    n_pg, n_txt = _preflight(pdf)
    scanned = n_pg is not None and n_txt == 0
    if n_pg is not None:
        kind = "掃描/圖片件——文字車道 0 屬預期,以視覺車道為準" if scanned else ("混合件(部分頁無文字層)" if n_txt < n_pg else "數位原生")
        print(f"  [前診] 頁 {n_pg} · 有文字層 {n_txt} · {kind}")
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
            zero = "(掃描件屬預期)" if scanned and key in TEXT_LANES and not tabs else ""
            print(f"  [OK  ] {key:13s} · 表 {len(tabs)} · 非空格 {cells} · {secs}s{zero}")
        except _ConsentGate as gate:
            results.append({"lane": key, "state": "SKIP_同意閘", "tables": 0, "note": str(gate)})
            print(f"  [SKIP] {key:13s} · {gate}(紅線:未同意不發包)")
        except Exception as exc:
            msg = str(exc)[:150]
            results.append({"lane": key, "state": "FAIL", "tables": 0, "note": msg})
            print(f"  [FAIL] {key:13s} · {msg[:80]}{_hint(msg)}(誠實記錄,不斷鏈)")
    ran = [r for r in results if r["state"] == "OK"]
    judge = [r for r in ran if not (scanned and r["lane"] in TEXT_LANES)] or ran
    if len(judge) >= 2:
        counts = sorted(r["tables"] for r in judge)
        med = counts[len(counts) // 2]
        agree = sum(1 for r in judge if r["tables"] == med)
        axis = "視覺軌" if scanned else "全軌"
        print(f"  [交叉] {axis} {len(judge)} 車道 · 表數共識={med}(同意 {agree}/{len(judge)})· 詳見存證")
    elif len(judge) == 1:
        print(f"  [交叉] 僅 1 有效車道({judge[0]['lane']})— 無從交叉,誠實單源")
    else:
        print("  [交叉] 零車道成果——視覺車道補件/同意閘後重跑(誠實)")
    run.mkdir(parents=True, exist_ok=True)
    ev = run / "summary.json"
    ev.write_text(json.dumps({"schema": "VIA.TableOmni.v1", "ts": ts, "pdf": pdf.name,
                              "pages_total": n_pg, "pages_with_text": n_txt, "scanned": scanned,
                              "lanes": results, "cloud_registered_not_implemented": [c[0] for c in CLOUD],
                              "policy": "readonly·no_main_table_write·install_via_gate_only·model_dl_consent_gated"},
                             ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [存證] {ev.relative_to(VIA)}(CSV 逐車道逐表)")
    print("  [鐵則] 唯讀擷取;主表落庫另走 via-store 家族(人工確認)")
    return 0


def selftest() -> int:
    """三檢自測(合成件;零網路零模型)。"""
    import tempfile
    import fitz
    print("=== 表格統包 v0101 · 自測三檢(零網路)===")
    n_pass = 0
    # ① HTML 表解析
    rows = _html_rows("<table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td><b>2</b></td></tr><tr><td></td><td></td></tr></table>")
    ok = rows == [["A", "B"], ["1", "2"]]
    n_pass += ok
    print(f"  [{'PASS' if ok else 'FAIL'}] html_rows 解析(含標籤剝除+空列剔)")
    with tempfile.TemporaryDirectory() as td:
        # ② 數位原生擷取(格線+文字)
        digital = Path(td) / "digital.pdf"
        doc = fitz.open()
        page = doc.new_page()
        x0, y0, cw, rh, nc, nr = 72, 72, 120, 24, 3, 3
        for r in range(nr + 1):
            page.draw_line((x0, y0 + r * rh), (x0 + nc * cw, y0 + r * rh))
        for c in range(nc + 1):
            page.draw_line((x0 + c * cw, y0), (x0 + c * cw, y0 + nr * rh))
        for r, row in enumerate([["K", "V1", "V2"], ["a", "1", "2"], ["b", "3", "4"]]):
            for c, val in enumerate(row):
                page.insert_text((x0 + c * cw + 6, y0 + r * rh + 16), val, fontsize=10)
        doc.save(digital)
        tabs = _lane_pymupdf(digital, None)
        ok = len(tabs) == 1 and tabs[0]["n_rows"] == 3
        n_pass += ok
        print(f"  [{'PASS' if ok else 'FAIL'}] 數位原生擷取(pymupdf 1 表 3 列)")
        # ③ 掃描件前診(頁面點陣化→圖片 PDF→文字層 0)
        scanned = Path(td) / "scanned.pdf"
        pix = doc[0].get_pixmap(dpi=100)
        doc2 = fitz.open()
        pg2 = doc2.new_page(width=pix.width, height=pix.height)
        pg2.insert_image(pg2.rect, pixmap=pix)
        doc2.save(scanned)
        doc2.close()
        doc.close()
        n_pg, n_txt = _preflight(scanned)
        zero_txt = _lane_pymupdf(scanned, None)
        ok = n_pg == 1 and n_txt == 0 and zero_txt == []
        n_pass += ok
        print(f"  [{'PASS' if ok else 'FAIL'}] 掃描件前診(文字層 0/1 頁+文字車道 0)")
    print(f"  [計] {n_pass}/3 檢通過")
    return 0 if n_pass == 3 else 1


def main() -> int:
    argv = sys.argv[1:]
    if "--selftest" in argv:
        return selftest()
    if "--extract" in argv:
        return extract(argv)
    return matrix()


if __name__ == "__main__":
    sys.exit(main())
