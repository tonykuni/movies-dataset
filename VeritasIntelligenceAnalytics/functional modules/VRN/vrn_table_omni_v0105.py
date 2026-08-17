#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""

vrn_table_omni_v0105 — 本地免費表格函式庫統包引擎(TOOL-029)
==================================================================================
v0103→v0104:cv2 修復提示改錨 opencv-contrib-python(full;順 paddlex/
  img2table 相依鏈,headless 會被 pip 回拉互撞)。
v0102→v0103(工作站全車道總攻回饋):
  ① img2table 接 OCR 後端 — 掃描件「表 1 值 0」根因=無 OCR 只出結構。
     後端鏈:EasyOCR(繁中+英;快取/同意閘)→Tesseract→無(誠實告示);
     並移入重車道(OCR 慢,享子行程逾時+心跳保護)
  ② ppstructure 依賴缺修復令 — PaddleX pipeline creation 依賴錯誤→
     提示 via-install "paddleocr[doc-parser]";worker 錯誤全文放寬 400 字;
     OMP_NUM_THREADS=1 注入子行程(Paddle 警示消除)
  ③ unstructured OCR 缺件提示 — unstructured_pytesseract→
     via-install unstructured.pytesseract(另需 Tesseract 本體)
  ④ 「結構有值空」誠實標注 — tables>0 而 cells=0 時明示 OCR 後端缺
v0101→v0102(工作站 ppstructure 卡站回饋;操作員令:導入加速器+動態進度條):
  ① PPStructureV3 瘦身管線 — 根因:預設 pipeline 載 15 模型含 PP-Chart2Table
     (VLM 大模型)+公式/印章/方向/展平,CPU 載入極慢如當機。修:只留表格鏈
     (停用 chart/formula/seal/orientation/unwarping;參數依版本簽名自適應)
  ② 重車道子行程隔離 — docling/unstructured/ppstructure 改 worker 子行程:
     逾時斷路(預設 900s,--timeout 覆寫)誠實 TIMEOUT 不卡斷、Ctrl+C 不傷主程、
     子行程輸出即時串流(模型載入/逐頁進度可見)
  ③ 動態進度 — 逐頁解析即時列印+靜默心跳(30s 無輸出印「仍在跑+餘時」)
  ④ 輕車道並行加速 — pymupdf/pdfplumber/camelot/tabula/img2table 執行緒併發
     (牆鐘=最慢者),結果按序列印;錨點導入 VeritasCeleritas(graceful)
  ⑤ 缺件提示增補 — unstructured_inference;ximgproc=cv2 多發行版互撞明示修法
用法:via-tables                          → 車道可用性矩陣(不擷取)
     via-tables --extract <pdf|檔名>     → 全可用車道擷取+交叉對帳+存證
     via-tables --extract <…> --engines ppstructure --timeout 1200 → 指定+逾時
     via-tables --extract <…> --pages 1-5 → 頁範圍(車道支援者生效)
     via-tables --selftest               → 四檢自測(零網路)
"""
from __future__ import annotations

import csv
import importlib.util
import inspect
import json
import re
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

VISION_DPI = 300  # v0105:視覺車道高品質轉檔 DPI(--dpi 覆寫;200→300 提升掃描件辨識)
HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
STAGING = HERE / "staging"
OUT = VIA / "VIA_Reports" / "tableomni_runs"
HEAVY = {"img2table", "docling", "unstructured", "ppstructure"}  # 子行程隔離車道(OCR/模型慢件)
DEFAULT_TIMEOUT = 900


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
_ACCEL = _via_load("VeritasCeleritas")  # 指令加速器(操作員令:每引擎導入)


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
    import warnings
    import camelot
    pg = ",".join(str(i + 1) for i in pages) if pages else "all"
    out = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # image-based 頁警示由前診統一告示,免洗版
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


def _i2t_ocr():
    """img2table OCR 後端鏈:EasyOCR(繁中+英)→Tesseract→None(誠實)。"""
    try:
        if _model_cached(".EasyOCR") or _consent():
            from img2table.ocr import EasyOCR
            return EasyOCR(lang=["ch_tra", "en"]), "easyocr(繁中+英)"
    except Exception:
        pass
    try:
        from img2table.ocr import TesseractOCR
        return TesseractOCR(lang="chi_tra+eng"), "tesseract(繁中+英)"
    except Exception:
        pass
    return None, None


def _lane_img2table(pdf: Path, pages):
    from img2table.document import PDF as I2TPDF
    ocr, backend = _i2t_ocr()
    if backend:
        print(f"    [img2table] OCR 後端:{backend}(首跑載模慢屬正常)", flush=True)
    else:
        print("    [img2table] 無 OCR 後端——掃描件僅出結構、值空(EasyOCR 需快取/同意閘;誠實)", flush=True)
    doc = I2TPDF(str(pdf), pages=list(pages) if pages else None)
    out = []
    for pno, tabs in (doc.extract_tables(ocr=ocr) or {}).items():
        for tb in tabs:
            rows = [[c.value for c in r] for r in tb.content.values()]
            t = _norm(rows, page=pno + 1)
            if t:
                out.append(t)
    return out


def _lane_docling(pdf: Path, pages):
    if not _model_cached(".cache/docling", ".cache/huggingface") and not _consent():
        raise _ConsentGate("TableFormer 模型未快取+同意閘關——同意後 setx VIA_NET_CONSENT YES(新視窗)首跑下載")
    print("    [docling] 模型載入中(首跑下載;CPU 推理慢屬正常)…", flush=True)
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
    print("    [unstructured] 版面分析中(hi_res 模型;CPU 慢屬正常)…", flush=True)
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


def _slim_kwargs(cls, opts: dict) -> dict:
    """依版本簽名過濾參數(不認的鍵剔除;**kwargs 版全收)。"""
    try:
        sig = inspect.signature(cls.__init__)
        if any(p.kind is p.VAR_KEYWORD for p in sig.parameters.values()):
            return opts
        return {k: v for k, v in opts.items() if k in sig.parameters}
    except (TypeError, ValueError):
        return {}


def _lane_ppstructure(pdf: Path, pages):
    if not _model_cached(".paddlex/official_models", ".paddleocr") and not _consent():
        raise _ConsentGate("Paddle 模型未快取+同意閘關——同意後 setx VIA_NET_CONSENT YES(新視窗)首跑下載")
    try:  # 3.x 新 API:瘦身管線只留表格鏈(卡站根因=預設載 VLM 圖表模型)
        from paddleocr import PPStructureV3
        opts = _slim_kwargs(PPStructureV3, {
            "use_doc_orientation_classify": False, "use_doc_unwarping": False,
            "use_formula_recognition": False, "use_chart_recognition": False,
            "use_seal_recognition": False})
        print(f"    [ppstructure] 瘦身載模(表格鏈;停用圖表VLM/公式/印章/方向/展平 {len(opts)} 項)…", flush=True)
        pipe = PPStructureV3(**opts)
        htmls: list[str] = []
        for i, res in enumerate(pipe.predict(input=str(pdf)), 1):
            d = getattr(res, "json", None) or (res if isinstance(res, dict) else None)
            if d is None:
                d = {k: getattr(res, k) for k in dir(res) if k in ("res", "table_res_list")}
            before = len(htmls)
            _harvest_html(d, htmls)
            print(f"    [ppstructure] 頁 {i} 解析完成(本頁表 {len(htmls) - before})", flush=True)
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
            pix = doc[i].get_pixmap(dpi=VISION_DPI)  # v0105:預設 300 高品質轉檔(操作員令)
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3]
            for res in eng(img):
                if res.get("type") == "table":
                    html = res.get("res", {}).get("html", "")
                    t = _norm(_html_rows(html), page=i + 1)
                    if t:
                        t["html"] = html[:4000]
                        out.append(t)
            print(f"    [ppstructure] 頁 {i + 1} 解析完成", flush=True)
    return out


def _lane_deepseek_ocr(pdf: Path, pages):
    raise RuntimeError("需本地 VLM 權重+GPU(VIA_DEEPSEEK_OCR_DIR 未備)— 誠實 NOT_READY")


# ── 車道登錄(本地 9 + 雲端列管 7)────────────────────────────────
TEXT_LANES = {"pymupdf", "pdfplumber", "camelot", "tabula"}  # 依文字層;掃描件必零
LANES = [
    ("pymupdf",      "fitz",         _lane_pymupdf,      "基座內建 find_tables(免費)"),
    ("pdfplumber",   "pdfplumber",   _lane_pdfplumber,   "字元級定位+表格偵測"),
    ("camelot",      "camelot",      _lane_camelot,      "lattice 優先,空退 stream"),
    ("tabula",       "tabula",       _lane_tabula,      "需 Java"),
    ("img2table",    "img2table",    _lane_img2table,    "OpenCV 格線+OCR 後端鏈(視覺;子行程)"),
    ("docling",      "docling",      _lane_docling,      "IBM TableFormer(重;視覺;子行程)"),
    ("unstructured", "unstructured", _lane_unstructured, "LLM 前置切塊(重;視覺;子行程)"),
    ("ppstructure",  "paddleocr",    _lane_ppstructure,  "百度版面分析(重;中文強;視覺;子行程)"),
    ("deepseek_ocr", "transformers", _lane_deepseek_ocr, "VLM;需權重+GPU(誠實 NOT_READY)"),
]
LANE_FN = {k: fn for k, _p, fn, _n in LANES}
CLOUD = [
    ("llamaparse", "LlamaIndex 雲解析"), ("reducto", "視覺大模型 API"),
    ("textract", "AWS"), ("azure_docint", "Azure Document Intelligence"),
    ("google_docai", "Google Cloud"), ("nanonets", "IDP 平台"), ("abbyy", "FlexiCapture"),
]
HINTS = {  # 已知缺件→修復令(經閘)
    "ximgproc": "修:cv2 多發行版互撞——py -m pip uninstall -y opencv-python-headless opencv-contrib-python-headless opencv-contrib-python 後 via-install opencv-contrib-python",
    "pi_heif": "修:via-install pi-heif",
    "unstructured_inference": "修:via-install unstructured-inference",
    "unstructured_pytesseract": "修:via-install unstructured.pytesseract(另需 Tesseract 本體)",
    "pipeline creation": "修:via-install \"paddleocr[doc-parser]\"(PP-StructureV3 附加依賴)",
    "pdf2image": "修:via-install pdf2image(另需 poppler)",
    "pytesseract": "修:需 Tesseract 本體(擇需)",
}


def _hint(msg: str) -> str:
    for key, fix in HINTS.items():
        if key in msg:
            return f"({fix})"
    return ""


def _lane_ok(key: str, probe: str) -> bool:
    if key == "deepseek_ocr":
        return False  # 權重未備即不可用(誠實)
    return _has(probe) and (key != "tabula" or _java())


def matrix() -> int:
    print("=== 表格統包引擎 v0104 · 車道可用性矩陣(唯讀零擷取)===")
    n_in = 0
    for key, probe, _fn, note in LANES:
        ok = _lane_ok(key, probe)
        n_in += 1 if ok else 0
        print(f"  [{'INSTALLED    ' if ok else 'NOT_INSTALLED'}] {key:13s} · {note}")
    for key, note in CLOUD:
        gate = "同意閘開" if _consent() else "同意閘關"
        print(f"  [CLOUD·列管   ] {key:13s} · {note}(非本地免費——本版不實作;{gate}+金鑰只走環境變數)")
    accel = "在(錨點導入)" if _ACCEL else "缺(graceful)"
    print(f"  [計] 本地車道 {n_in}/{len(LANES)} 可用 · 雲端 {len(CLOUD)} 列管 · 加速器 Celeritas {accel}")
    print('  [裝] 缺件經閘安裝(儲存規定):via-install camelot-py pdfplumber img2table tabula-py')
    print('       視覺車道補件:via-install "paddleocr[doc-parser]" unstructured.pytesseract · 重量擇需:via-install docling')
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


def _write_lane(run: Path, key: str, tabs: list) -> dict:
    ldir = run / key
    ldir.mkdir(parents=True, exist_ok=True)
    cells = 0
    for n, t in enumerate(tabs, 1):
        cells += sum(1 for r in t["rows"] for c in r if str(c).strip())
        with open(ldir / f"table_{n}.csv", "w", encoding="utf-8-sig", newline="") as fh:
            csv.writer(fh).writerows(t["rows"])
    return {"tables": len(tabs), "cells": cells}


def _run_light(key: str, fn, pdf: Path, pages, run: Path) -> dict:
    t0 = time.time()
    try:
        tabs = fn(pdf, pages)
        return {"lane": key, "state": "OK", **_write_lane(run, key, tabs),
                "secs": round(time.time() - t0, 1)}
    except _ConsentGate as gate:
        return {"lane": key, "state": "SKIP_同意閘", "tables": 0, "note": str(gate)}
    except Exception as exc:
        return {"lane": key, "state": "FAIL", "tables": 0, "note": str(exc)[:400]}


def _run_worker(key: str, pdf: Path, pages_spec: str | None, run: Path, timeout: int) -> dict:
    """重車道子行程:串流輸出+靜默心跳+逾時斷路(誠實 TIMEOUT 不卡斷)。"""
    import os
    argv = [sys.executable, str(Path(__file__).resolve()), "--worker", key,
            "--pdf", str(pdf), "--run-dir", str(run)]
    if pages_spec:
        argv += ["--pages", pages_spec]
    env = os.environ.copy()
    env["OMP_NUM_THREADS"] = "1"  # Paddle 併行警示消除(單件推理最佳)
    t0 = time.time()
    proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            stdin=subprocess.DEVNULL, text=True, encoding="utf-8", errors="replace", env=env)
    result_line = {"line": None}
    last_out = {"t": time.time()}

    def _pump():
        for line in proc.stdout:
            line = line.rstrip()
            last_out["t"] = time.time()
            if line.startswith("WORKER_RESULT "):
                result_line["line"] = line[len("WORKER_RESULT "):]
            elif line.strip():
                print(f"    {line[:150]}", flush=True)

    th = threading.Thread(target=_pump, daemon=True)
    th.start()
    while proc.poll() is None:
        if time.time() - t0 > timeout:
            proc.kill()
            proc.wait()
            return {"lane": key, "state": "TIMEOUT", "tables": 0,
                    "note": f"逾時 {timeout}s 斷路(--timeout 可調;誠實不卡斷)"}
        if time.time() - last_out["t"] > 30:
            last_out["t"] = time.time()
            left = int(timeout - (time.time() - t0))
            print(f"    [心跳] {key} 仍在跑 · 已 {int(time.time() - t0)}s · 逾時餘 {left}s", flush=True)
        time.sleep(1)
    th.join(timeout=5)
    secs = round(time.time() - t0, 1)
    if result_line["line"]:
        try:
            r = json.loads(result_line["line"])
            return {"lane": key, "secs": secs, **r}
        except json.JSONDecodeError:
            pass
    return {"lane": key, "state": "FAIL", "tables": 0, "secs": secs,
            "note": f"worker rc={proc.returncode} 無結果行(誠實)"}


def worker(argv: list[str]) -> int:
    """子行程模式:單車道執行,結果以 WORKER_RESULT JSON 行回傳(ASCII 安全)。"""
    key = argv[argv.index("--worker") + 1]
    pdf = Path(argv[argv.index("--pdf") + 1])
    run = Path(argv[argv.index("--run-dir") + 1])
    pages = _parse_pages(argv[argv.index("--pages") + 1]) if "--pages" in argv else None
    try:
        tabs = LANE_FN[key](pdf, pages)
        res = {"state": "OK", **_write_lane(run, key, tabs)}
    except _ConsentGate as gate:
        res = {"state": "SKIP_CONSENT", "tables": 0, "note": str(gate)}
    except Exception as exc:
        res = {"state": "FAIL", "tables": 0, "note": str(exc)[:400]}
    print("WORKER_RESULT " + json.dumps(res, ensure_ascii=True), flush=True)
    return 0


def extract(argv: list[str]) -> int:
    pdf = _resolve_pdf(argv[argv.index("--extract") + 1])
    if pdf is None:
        print("[FAIL] PDF 不存在(絕對路徑或 staging 內檔名)— 誠實停止")
        return 1
    pages_spec = argv[argv.index("--pages") + 1] if "--pages" in argv else None
    pages = _parse_pages(pages_spec) if pages_spec else None
    only = set(argv[argv.index("--engines") + 1].split(",")) if "--engines" in argv else None
    timeout = int(argv[argv.index("--timeout") + 1]) if "--timeout" in argv else DEFAULT_TIMEOUT
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run = OUT / f"RUN_{ts}"
    print(f"=== 表格統包擷取 v0104 · {pdf.name} · 頁={pages_spec or '全'} · 重車道逾時 {timeout}s ===")
    n_pg, n_txt = _preflight(pdf)
    scanned = n_pg is not None and n_txt == 0
    if n_pg is not None:
        kind = "掃描/圖片件——文字車道 0 屬預期,以視覺車道為準" if scanned else ("混合件(部分頁無文字層)" if n_txt < n_pg else "數位原生")
        print(f"  [前診] 頁 {n_pg} · 有文字層 {n_txt} · {kind}")

    sel = [(k, p, fn, note) for k, p, fn, note in LANES if not only or k in only]
    light = [(k, fn) for k, p, fn, _ in sel if k not in HEAVY and _lane_ok(k, p)]
    heavy = [k for k, p, _fn, _ in sel if k in HEAVY and _lane_ok(k, p)]
    missing = [k for k, p, _fn, _ in sel if not _lane_ok(k, p)]
    results = []
    # 輕車道並行(加速器:牆鐘=最慢者;結果按序列印)
    if light:
        print(f"  [併] 輕車道 {len(light)} 條並行(加速器)…", flush=True)
        with ThreadPoolExecutor(max_workers=min(4, len(light))) as ex:
            futs = {k: ex.submit(_run_light, k, fn, pdf, pages, run) for k, fn in light}
        for k, _fn in light:
            r = futs[k].result()
            results.append(r)
            if r["state"] == "OK":
                zero = "(掃描件屬預期)" if scanned and k in TEXT_LANES and r["tables"] == 0 else ""
                if r["tables"] > 0 and r["cells"] == 0:
                    zero = "(結構有、值空——OCR 後端缺/未同意,誠實)"
                print(f"  [OK  ] {k:13s} · 表 {r['tables']} · 非空格 {r['cells']} · {r['secs']}s{zero}")
            elif r["state"] == "SKIP_同意閘":
                print(f"  [SKIP] {k:13s} · {r['note']}(紅線:未同意不發包)")
            else:
                print(f"  [FAIL] {k:13s} · {r['note'][:160]}{_hint(r.get('note', ''))}(誠實記錄,不斷鏈)")
    # 重車道子行程(串流進度+心跳+逾時斷路)
    for k in heavy:
        print(f"  [跑  ] {k}(子行程隔離;逾時 {timeout}s)…", flush=True)
        r = _run_worker(k, pdf, pages_spec, run, timeout)
        results.append(r)
        st = r["state"]
        if st == "OK":
            hollow = "(結構有、值空——OCR 後端缺/未同意,誠實)" if r["tables"] > 0 and r.get("cells", 0) == 0 else ""
            print(f"  [OK  ] {k:13s} · 表 {r['tables']} · 非空格 {r.get('cells', 0)} · {r.get('secs', '?')}s{hollow}")
        elif st in ("SKIP_CONSENT", "SKIP_同意閘"):
            print(f"  [SKIP] {k:13s} · {r.get('note', '')}(紅線:未同意不發包)")
        elif st == "TIMEOUT":
            print(f"  [逾時] {k:13s} · {r['note']}")
        else:
            print(f"  [FAIL] {k:13s} · {r.get('note', '')[:160]}{_hint(r.get('note', ''))}(誠實記錄,不斷鏈)")
    for k in missing:
        results.append({"lane": k, "state": "NOT_INSTALLED", "tables": 0})
        print(f"  [NOT_INSTALLED] {k}")

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
                              "timeout": timeout, "lanes": results,
                              "cloud_registered_not_implemented": [c[0] for c in CLOUD],
                              "policy": "readonly·no_main_table_write·install_via_gate_only·model_dl_consent_gated"},
                             ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [存證] {ev.relative_to(VIA)}(CSV 逐車道逐表)")
    print("  [鐵則] 唯讀擷取;主表落庫另走 via-store 家族(人工確認)")
    return 0


def selftest() -> int:
    """四檢自測(合成件;零網路零模型)。"""
    import tempfile
    import fitz
    print("=== 表格統包 v0104 · 自測四檢(零網路)===")
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
        # ④ worker 子行程協議往返(重車道隔離的同一條管線)
        rdir = Path(td) / "run"
        r = _run_worker("pymupdf", digital, None, rdir, timeout=120)
        ok = r.get("state") == "OK" and r.get("tables") == 1 and (rdir / "pymupdf/table_1.csv").exists()
        n_pass += ok
        print(f"  [{'PASS' if ok else 'FAIL'}] worker 子行程協議(串流+結果行+CSV 落地)")
    print(f"  [計] {n_pass}/4 檢通過")
    return 0 if n_pass == 4 else 1


def _apply_dpi(argv):
    global VISION_DPI
    if "--dpi" in argv:
        try:
            VISION_DPI = max(72, min(600, int(argv[argv.index("--dpi") + 1])))
        except (ValueError, IndexError):
            print("[WARN] --dpi 參數無效,沿用 300")
    return VISION_DPI


def main() -> int:
    _apply_dpi(sys.argv[1:])
    argv = sys.argv[1:]
    if "--worker" in argv:
        return worker(argv)
    if "--selftest" in argv:
        return selftest()
    if "--extract" in argv:
        return extract(argv)
    return matrix()


if __name__ == "__main__":
    sys.exit(main())
