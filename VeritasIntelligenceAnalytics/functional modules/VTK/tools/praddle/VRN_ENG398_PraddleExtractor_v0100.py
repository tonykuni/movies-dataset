#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VRN_ENG398_PraddleExtractor v0100 — PRADDLE 擷取編排器:pdfplumber / 原生 → RapidOCR → PaddleOCR(無法才用重型)× LAYOUT 修復驗證

操作員 2026-10-02(VCGC-REQ126 · VRN-REQ006):「增加引擎」PaddleOCR + RapidOCR 雙引擎、LAYOUT / TEXT / TABLE / GRAPH 各五組、
pdfplumber + 1 雙引擎、10 個組合、30 大表格問題;「跟 LAYOUT 引擎相互搭配並修復驗證才能」;「PRADDLE 工具們高風險要獨立環境」;
「只有輸出準確度提高、擷取更快:從 NON-OCR → OCR,從 pdfplumber 單引擎 → 雙引擎 → paddle 重型工具,無法才使用重型工具」。

**先查再造(全景盤點後的分工;本支只做編排,不造第二份)**
  原生分流(L01 / T01 / C01)   SUP_MDL746 PDFPlumberPlusHub triage():DIGITAL / THIN / SCANNED(密度 + 絕對字數)
  原生擷取與版面(L02–L05 · T05 · Tab02/03 · Gr04)
                              SUP_MDL743 GenericLayoutHub def_run_batch():GLE 原生行 → 字型分類(頁首頁尾 / 浮水印 = NOISE_ROLES)
                              → 表格還原(年度列種子 · 無框表 · 左右並排拆表)→ 合併格 → 閱讀順序 → 跨頁接續 → 並排關係 → 驗算 checksum
  OCR 車道(T02 / T03 · C04 / C05)
                              via_ocr_super v0102 run_lane_boxes():**每車道一個隔離境**(RapidOCR → via_rapidocr ·
                              PaddleOCR → via_paddle_311 …),子行程跑、JSON 回主行程;本行程**不 import 任何 OCR 套件**(高風險隔離)
  掃描頁的版面修復            同一條 SUP_MDL743 def_repair_document():OCR 行照 GLE 文件格式組裝(source_method 用 GLE 既有的 OCR 行格式名
                              tesseract.tsv_line;實際引擎記在 metadata.ocr_engine),掃描頁也走同一套表格還原 / 閱讀順序 / 跨頁接續 / 驗算
  數值解析                    SUP_MDL743 LayoutCommon def_number()(括號負數 · 千分位 · %;零 / 空白 / 破折號分開)
**本支新增的只有**(盤點確認沒有正主):
  ① 階梯裁決 ladder_page():RapidOCR 平均信心 ≥ 0.85 直接採用;不足且 Paddle 就緒才升級;Paddle 不在就照實留 Rapid 並標低信心
  ② 儲存格正規化 norm_cell()(30 大問題中規則判得了的):貨幣符號分離(#20)· 各種破折號 / 負號統一(#17)· 數值欄 O/o→0、l/I→1(#9)·
     全形數字(NFKC)· % 單位分離(#19)· 空白 ≠ 0 ≠ 破折號(#18)· 欄數不齊補齊並記錄(#29)
  ③ 逐格信心與旗標(#28):格子由哪些 OCR 行組成就取最低信心;< 0.6 或數值欄解析不出 → FLAGGED_MANUAL_REVIEW
  ④ 互核:同一頁原生與 OCR 都有時(--ocr force),數值集合交集率 → AGREE / PARTIAL / DISAGREE
  ⑤ 原生文字層是 CID 亂碼(#27)→ 該頁改走 OCR
輸出 VIA_Reports/vrn/praddle/<檔名>_<sha8>/PRADDLE.json · PRADDLE_cells.csv(只寫報告夾,不寫正式庫)。
零網路(OCR 首跑下模型 = 隔離境的同意閘,操作員的手);不用 TA-Lib;只收 VCGC 呼叫(--selftest 例外)。
CLI:via-vcgc run --family vrn VRN_ENG398_PraddleExtractor probe | run --in <pdf|夾> [--ocr auto|off|force] [--pages 1-3] | --selftest
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

import csv
import hashlib
import importlib.util
import json
import os
import re
import sys
import tempfile
import time
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
RULES = VIA / "supportive modules" / "70_VRN_Rules"
REG = VIA / "supportive modules" / "registry"
OUT = VIA / "VIA_Reports" / "vrn" / "praddle"
ENGINE = Path(__file__).stem

RAPID_ACCEPT = 0.85        # Rapid 平均信心達此值就不叫重型
CELL_FLAG = 0.60           # 格子最低信心低於此值 → 人工複查
DPI = 300                  # 掃描頁渲染(與 ENG072 HQ 帶一致)
CID_RATIO = 0.20           # 原生文字裡 (cid:N) / U+FFFD 佔比超過此值 = 編碼壞,改走 OCR
HEAVY = ("paddleocr", "paddle", "rapidocr_onnxruntime", "onnxruntime", "cv2")
DASHES = "—–−‐‒﹣－-"
CURRENCY_RX = re.compile(r"^(NT\$|US\$|HK\$|RMB|NTD|USD|TWD|\$|¥|￥|€|£)\s*", re.I)
CONFUSE = str.maketrans({"O": "0", "o": "0", "l": "1", "I": "1"})
_MODS: dict = {}


def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d+)$", p.stem)
    return int(m.group(1)) if m else -1


def _load(key: str, folder: Path, stem: str):
    """尾版律:同家族取版號最大那支;缺 / 載不起來 = None 並留因由(不猜、不退舊版)。"""
    if key in _MODS:
        return _MODS[key]["mod"]
    rec = {"mod": None, "why": "", "src": ""}
    _MODS[key] = rec
    hits = [p for p in folder.glob(stem + "_v*.py") if _vnum(p) >= 0]
    if not hits:
        rec["why"] = f"{stem}_v*.py 不在 {folder.name}"
        return None
    path = max(hits, key=_vnum)
    rec["src"] = path.name
    try:
        spec = importlib.util.spec_from_file_location(f"praddle_{key}", path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        rec["mod"] = mod
    except Exception as exc:
        rec["why"] = f"{path.name} 載不起來:{type(exc).__name__}:{str(exc)[:80]}"
    return rec["mod"]


def layout_hub():
    return _load("layout", RULES, "SUP_MDL743_GenericLayoutHub")


def ppp_hub():
    return _load("ppp", RULES, "SUP_MDL746_PDFPlumberPlusHub")


def ocr_super():
    return _load("ocr", REG, "via_ocr_super")


def why(key: str) -> str:
    return (_MODS.get(key) or {}).get("why", "")


# ---------------------------------------------------------------- OCR 車道(隔離境)
def lanes() -> dict:
    """RapidOCR / PaddleOCR 兩車道各在自己的隔離境裡的狀態(READY / NO_ENV / NO_MOD / NO_BIN);探測在該境子行程 import。"""
    m = ocr_super()
    if m is None or not hasattr(m, "run_lane_boxes"):
        return {"_why": why("ocr") or "via_ocr_super 沒有 run_lane_boxes(要 v0102 以上)"}
    envs = m.env_map()
    out = {}
    for lane in m.LANES:
        if lane["k"] in ("rapidocr", "paddleocr"):
            state, py = m.probe_lane(lane, envs)
            out[lane["k"]] = {"state": state, "py": py, "env": lane["envs"][0], "lane": lane}
    return out


def ladder_page(image: str, lane_map: dict, runner=None) -> tuple:
    """輕 → 重:Rapid 夠信心就停;不夠且 Paddle 就緒才升級;回 (結果或 None, 步驟, 路線)。runner 可注入(自測)。"""
    runner = runner or (lambda lane, py, img: ocr_super().run_lane_boxes(lane, py, img))
    steps, best = [], None
    for k in ("rapidocr", "paddleocr"):
        ln = lane_map.get(k) or {}
        if ln.get("state") != "READY":
            steps.append({"k": k, "state": ln.get("state") or "ABSENT", "env": ln.get("env")})
            continue
        t0 = time.time()
        res = runner(ln["lane"], ln["py"], image)
        steps.append({"k": k, "state": "RAN", "ok": res.get("ok"), "n": res.get("n", 0), "avg": res.get("avg", 0.0),
                      "err": res.get("err", ""), "sec": round(time.time() - t0, 1), "env": ln.get("env")})
        if res.get("ok") and res.get("n", 0) >= 1 and (best is None or res["avg"] >= best["avg"]):
            best = res
        if k == "rapidocr" and best is not None and best["avg"] >= RAPID_ACCEPT:
            return best, steps, "rapid"
    if best is None:
        return None, steps, "no_ocr"
    if best["k"] == "paddleocr":
        return best, steps, "paddle"
    heavy_ran = any(s["k"] == "paddleocr" and s["state"] == "RAN" for s in steps)
    return best, steps, ("rapid_low_conf" if heavy_ran else "rapid_low_conf_no_heavy")


# ---------------------------------------------------------------- 儲存格正規化(規則判得了的那幾類)
def norm_cell(raw, numeric_col: bool, def_number) -> dict:
    """回 {raw, text, value, unit, fixes, blank, dash}。value = Decimal 字串或 None;空白 / 破折號 / 0 三者分開。"""
    t = unicodedata.normalize("NFKC", "" if raw is None else str(raw)).strip()
    out = {"raw": raw, "text": t, "value": None, "unit": None, "fixes": [], "blank": not t, "dash": False}
    if not t:
        return out
    if all(ch in DASHES for ch in t):
        out["dash"] = True
        return out
    m = CURRENCY_RX.match(t)
    if m:
        out["unit"] = m.group(1).upper()
        t = t[m.end():].strip()
        out["fixes"].append("currency")
    if t[:1] in DASHES and t[:1] != "-":
        t = "-" + t[1:]
        out["fixes"].append("dash")
    if numeric_col and re.search(r"\d", t) and re.search(r"[OolI]", t) and re.fullmatch(r"[\d,.\s()%OolI\-]+", t):
        t = t.translate(CONFUSE)
        out["fixes"].append("ocr_confusion")
    if t.endswith("%"):
        out["unit"] = out["unit"] or "%"
    v = def_number(t)
    out["text"] = t
    out["value"] = str(v) if v is not None else None
    return out


NUMERIC_LIKE_RX = re.compile(r"[(\-]?[\dOolI][\dOolI,.]*[\dOolI]%?\)?")


def fix_ocr_numeric(text: str) -> tuple:
    """T04 錯字修正(進 LAYOUT 之前):整段長得像數字(至少一個真數字 · 只含數字 / O o l I / , . ( ) % -)才把 O o→0、l I→1。
    回 (修正後, 有沒有改)。文字欄(營業收入、IOU、Oil…)一律不動。"""
    s = (text or "").strip()
    if re.search(r"\d", s) and re.search(r"[OolI]", s) and NUMERIC_LIKE_RX.fullmatch(s):
        return s.translate(CONFUSE), True
    return text, False


def _cid_ratio(text: str) -> float:
    if not text:
        return 0.0
    bad = len(re.findall(r"\(cid:\d+\)", text)) * 6 + text.count("�")
    return min(1.0, bad / max(1, len(text)))


# ---------------------------------------------------------------- OCR 結果 → GLE 文件格式(給 LAYOUT 修復鏈)
def ocr_document(pdf_name: str, sha: str, page_results: dict, page_sizes: dict) -> tuple:
    """回 (document, 字 id → 信心)。像素框 → 點(72 / DPI);一行 OCR = 一個 GLE 行 + 一個字元幾何。"""
    common = layout_hub().STAGES["common"]
    geometry, pages, conf = [], [], {}
    scale = 72.0 / DPI
    for pn in sorted(page_results):
        res = page_results[pn]
        w_pt, h_pt = page_sizes[pn]
        elements = []
        for i, ln in enumerate(res["lines"]):
            b = [round(v * scale, 2) for v in ln["bbox"]]
            size = round(max(1.0, b[3] - b[1]), 2)
            eid = f"PRD-{sha[:8].upper()}-P{pn:04d}-L{i + 1:04d}"
            text, fixed = fix_ocr_numeric(ln["text"])
            meta = {"ocr_engine": res["k"], "dpi": DPI}
            if fixed:
                meta["ocr_raw"] = ln["text"]
            elements.append({"element_id": eid, "element_type": "TEXT", "subtype": "BODY", "source_method": "tesseract.tsv_line",
                             "raw_text": text, "repaired_text": text, "bbox_pt": b, "page": pn,
                             "font": {"size": size, "is_bold": False, "source": "ocr_box_height"}, "confidence": ln["conf"],
                             "metadata": meta})
            wid = common.def_id("W", sha, len(geometry))
            conf[wid] = ln["conf"]
            if fixed:
                conf["raw:" + wid] = ln["text"]
            geometry.append({"page": pn, "text": text, "bbox": b, "element_type": "TEXT", "subtype": "BODY",
                             "confidence": ln["conf"], "metadata": dict(meta, font_size=size)})
        pages.append({"physical_page": pn, "page_id": f"P{pn:04d}", "printed_page": None, "width": w_pt, "height": h_pt,
                      "elements": elements, "used_ocr": True, "warnings": [], "native_character_count": 0})
    sizes = sorted(e["font"]["size"] for p in pages for e in p["elements"])
    body = sizes[len(sizes) // 2] if sizes else 10.0
    doc = {"filename": pdf_name, "input_sha256": sha, "native_geometry": geometry,
           "layout": {"pages": pages, "body_font_size": body}}
    return doc, conf


# ---------------------------------------------------------------- 表格:正規化 · 逐格信心 · 旗標
def finish_table(table: dict, source: str, conf: dict, def_number) -> dict:
    rows = table.get("rows") or []
    width = max((len(r) for r in rows), default=0)
    hc = int(table.get("header_count") or 0)
    padded = 0
    for r in rows:
        while len(r) < width:
            r.append({"raw": "", "text": "", "number": None, "source_ids": [], "padded": True})
            padded += 1
    numeric = []
    for c in range(width):
        body = [r[c] for r in rows[hc:] if (r[c].get("text") or "").strip()]
        numeric.append(bool(body) and sum(x.get("number") is not None for x in body) * 2 >= len(body))
    out_rows, flags = [], 0
    for ri, r in enumerate(rows):
        orow = []
        for ci, cell in enumerate(r):
            n = norm_cell(cell.get("text") or cell.get("raw"), numeric[ci] and ri >= hc, def_number)
            cs = [conf[s] for s in cell.get("source_ids") or [] if s in conf]
            n["conf"] = round(min(cs), 4) if cs else None
            raws = [conf["raw:" + s] for s in cell.get("source_ids") or [] if "raw:" + s in conf]
            if raws:
                n["fixes"].insert(0, "ocr_confusion@ocr")
                n["ocr_raw"] = " ".join(raws)
            f = []
            if n["conf"] is not None and n["conf"] < CELL_FLAG:
                f.append("low_conf")
            if numeric[ci] and ri >= hc and not n["blank"] and not n["dash"] and n["value"] is None:
                f.append("unparsed_number")
            if f:
                n["flags"] = ["FLAGGED_MANUAL_REVIEW:" + x for x in f]
                flags += 1
            orow.append(n)
        out_rows.append(orow)
    return {"id": table.get("id"), "source": source, "pages": table.get("pages") or [table.get("page")],
            "header_count": hc, "columns": width, "numeric_columns": numeric, "rows": out_rows,
            "caption": table.get("caption") or "", "checksum": table.get("checksum"), "state": table.get("state"),
            "padded_cells": padded, "flagged_cells": flags}


def _numbers(lines, def_number) -> set:
    vals = set()
    for ln in lines:
        for tok in re.findall(r"[(\-−–—]?\d[\d,]*(?:\.\d+)?%?\)?", ln.get("text") or ""):
            v = def_number(tok.replace("−", "-").replace("–", "-").replace("—", "-"))
            if v is not None:
                vals.add(str(abs(v)))
    return vals


def xcheck(native_lines, ocr_lines, def_number) -> dict:
    a, b = _numbers(native_lines, def_number), _numbers(ocr_lines, def_number)
    if not a and not b:
        return {"state": "NODATA", "native": 0, "ocr": 0}
    j = len(a & b) / max(1, len(a | b))
    return {"state": "AGREE" if j >= 0.9 else ("PARTIAL" if j >= 0.5 else "DISAGREE"), "jaccard": round(j, 3),
            "native": len(a), "ocr": len(b), "only_native": sorted(a - b)[:10], "only_ocr": sorted(b - a)[:10]}


# ---------------------------------------------------------------- 主流程
def _pages(spec: str | None, n: int) -> list:
    if not spec:
        return list(range(1, n + 1))
    out = []
    for part in spec.split(","):
        a, _, b = part.partition("-")
        lo, hi = int(a), int(b or a)
        out.extend(p for p in range(lo, hi + 1) if 1 <= p <= n)
    return sorted(set(out))


def run_pdf(pdf: Path, ocr: str = "auto", pages: str | None = None, out_root: Path = OUT, lane_map=None, runner=None) -> dict:
    import fitz  # 原生層(主境既有,不是高風險件)
    hub, ppp = layout_hub(), ppp_hub()
    if hub is None:
        return {"state": "ABSENT", "why": why("layout")}
    common = hub.STAGES["common"]
    raw = pdf.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    out = out_root / f"{pdf.stem}_{sha[:8]}"
    out.mkdir(parents=True, exist_ok=True)
    t_all = time.time()
    doc = fitz.open(str(pdf))
    sel = _pages(pages, doc.page_count)
    page_rows, need_ocr, sizes, native_text = [], [], {}, {}
    for pn in sel:
        pg = doc[pn - 1]
        sizes[pn] = (round(pg.rect.width, 2), round(pg.rect.height, 2))
        tri = ppp.triage(pdf, pn) if ppp is not None else {"state": "UNKNOWN", "why": why("ppp")}
        txt = pg.get_text() or ""
        native_text[pn] = txt
        cid = _cid_ratio(txt)
        state = tri.get("state", "UNKNOWN")
        route = "native"
        if cid > CID_RATIO:
            state, route = "SCANNED", "ocr(cid_garbage)"
        elif state == "SCANNED" or (state == "UNKNOWN" and len(txt.strip()) < 10):
            route = "ocr"
        if ocr == "off" and route != "native":
            route = "native(ocr_off)"
        if ocr == "force" or route.startswith("ocr"):
            need_ocr.append(pn)
        page_rows.append({"page": pn, "triage": state, "n_chars": tri.get("n_chars"), "density": tri.get("density"),
                          "cid_ratio": round(cid, 3), "route": route})
    # ① 原生層 → LAYOUT 修復鏈(整份;非 OCR 頁取這裡)
    native = {"tables": [], "lines": []}
    if any(not r["route"].startswith("ocr") for r in page_rows):
        rep = hub.def_run_batch(pdf, out / "native")
        d0 = (rep.get("documents") or [{}])[0].get("repair") or {}
        native = {"tables": d0.get("tables") or [], "lines": (d0.get("text") or {}).get("lines") or [],
                  "errors": rep.get("errors") or []}
    # ② 需要 OCR 的頁 → 隔離境車道(輕 → 重)→ 同一條 LAYOUT 修復鏈
    ocr_rep = {"tables": [], "lines": []}
    if need_ocr and ocr != "off":
        lane_map = lane_map if lane_map is not None else lanes()
        results, tmp = {}, Path(tempfile.mkdtemp(prefix="praddle_"))
        for pn in need_ocr:
            png = tmp / f"p{pn:04d}.png"
            doc[pn - 1].get_pixmap(dpi=DPI).save(str(png))       # 一頁一張,用完即刪(#26 記憶體)
            best, steps, route = ladder_page(str(png), lane_map, runner)
            png.unlink(missing_ok=True)
            row = next(r for r in page_rows if r["page"] == pn)
            row.update(ladder=steps, ocr_route=route, ocr_avg=(best or {}).get("avg"))
            if best is not None:
                results[pn] = best
        if results:
            odoc, conf = ocr_document(pdf.name, sha, results, sizes)
            rep2 = hub.def_repair_document(odoc, out / "ocr", pdf)
            ocr_rep = {"tables": rep2.get("tables") or [], "lines": (rep2.get("text") or {}).get("lines") or [], "conf": conf}
    doc.close()
    ocr_pages = {r["page"] for r in page_rows if r["route"].startswith("ocr") and r.get("ocr_route") not in (None, "no_ocr")}
    tables = [finish_table(t, "native", {}, common.def_number) for t in native["tables"]
              if not set(t.get("pages") or [t.get("page")]) & ocr_pages]
    tables += [finish_table(t, "ocr", ocr_rep.get("conf") or {}, common.def_number) for t in ocr_rep["tables"]]
    checks = {}
    if ocr == "force":
        for pn in sel:
            checks[pn] = xcheck([x for x in native["lines"] if x.get("page") == pn],
                                [x for x in ocr_rep["lines"] if x.get("page") == pn], common.def_number)
    no_ocr = [r["page"] for r in page_rows if r["route"].startswith("ocr") and r.get("ocr_route") in (None, "no_ocr")]
    flagged = sum(t["flagged_cells"] for t in tables)
    disagree = [p for p, c in checks.items() if c["state"] == "DISAGREE"]
    verdict = ("NODATA" if no_ocr and not tables and not native["lines"] else
               "YELLOW" if (no_ocr or flagged or disagree or native.get("errors")) else "GREEN")
    report = {"engine": ENGINE, "pdf": str(pdf), "sha256": sha, "dpi": DPI, "ocr_mode": ocr, "verdict": verdict,
              "pages": page_rows, "no_ocr_pages": no_ocr, "tables": tables, "flagged_cells": flagged,
              "native_lines": len(native["lines"]), "ocr_lines": len(ocr_rep["lines"]), "xcheck": checks,
              "sec": round(time.time() - t_all, 1), "heavy_imported_here": sorted(m for m in HEAVY if m in sys.modules)}
    (out / "PRADDLE.json").write_text(json.dumps(report, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    with (out / "PRADDLE_cells.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["table", "source", "row", "col", "raw", "text", "value", "unit", "conf", "fixes", "flags"])
        for t in tables:
            for ri, r in enumerate(t["rows"]):
                for ci, c in enumerate(r):
                    w.writerow([t["id"], t["source"], ri, ci, c["raw"], c["text"], c["value"], c["unit"], c["conf"],
                                "|".join(c["fixes"]), "|".join(c.get("flags") or [])])
    report["out"] = str(out)
    return report


def _print(rep: dict) -> None:
    print(f"[PRADDLE] {rep.get('verdict')} · {Path(rep.get('pdf', '?')).name} · 頁 {len(rep.get('pages', []))} · "
          f"表 {len(rep.get('tables', []))} · 旗標格 {rep.get('flagged_cells', 0)} · {rep.get('sec')}s · {rep.get('out', '')}")
    for r in rep.get("pages", []):
        tail = f" · OCR {r.get('ocr_route')} avg {r.get('ocr_avg')}" if r.get("ocr_route") else ""
        print(f"  p{r['page']:<3} {r['triage']:<8} → {r['route']}{tail}")
    if rep.get("no_ocr_pages"):
        print(f"  [缺 OCR] 掃描頁 {rep['no_ocr_pages']} 沒有就緒車道(RapidOCR 隔離境 via_rapidocr / PaddleOCR via_paddle_311;"
              f"via-vcgc run via_ocr_super --plan 看安裝計畫,裝件是操作員的手)")


# ---------------------------------------------------------------- 自測(容器:沒有任何 OCR 套件也要驗到規則與 LAYOUT 搭配)
def selftest() -> int:
    print(f"=== {ENGINE} · 自測(編排 · 階梯 · 正規化 · LAYOUT 修復搭配 · 高風險隔離)===")
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    hub, ppp, osu = layout_hub(), ppp_hub(), ocr_super()
    chk("① 三個正主掛得上(SUP_MDL743 LAYOUT · SUP_MDL746 分流 · via_ocr_super 隔離境車道含 run_lane_boxes)",
        hub is not None and ppp is not None and osu is not None and hasattr(osu, "run_lane_boxes"),
        f"{_MODS.get('layout', {}).get('src')} · {_MODS.get('ppp', {}).get('src')} · {_MODS.get('ocr', {}).get('src')}")
    dn = hub.STAGES["common"].def_number
    cases = {
        ("(1,234)", True): ("-1234", None, []), ("—1,234", True): ("-1234", None, ["dash"]),
        ("NT$1,234", True): ("1234", "NT$", ["currency"]), ("15.2%", True): ("15.2", "%", []),
        ("1O5O", True): ("1050", None, ["ocr_confusion"]), ("lO5O", False): (None, None, []),
        ("０", True): ("0", None, []),
    }
    bad = []
    for (raw, num), (val, unit, fixes) in cases.items():
        n = norm_cell(raw, num, dn)
        if (n["value"], n["unit"], n["fixes"]) != (val, unit, fixes):
            bad.append((raw, n["value"], n["unit"], n["fixes"]))
    blank, dash = norm_cell("", True, dn), norm_cell("—", True, dn)
    chk("② 儲存格正規化:括號負數 · 各種破折號 · 貨幣分離 · % 單位 · 數值欄 O→0(文字欄不動)· 全形數字;空白 / 破折號 / 0 三者分開",
        not bad and blank["blank"] and blank["value"] is None and dash["dash"] and dash["value"] is None, bad or "7 例全對")

    calls = []

    def fake_runner(avgs):
        def run(lane, py, img):
            calls.append(lane["k"])
            a = avgs.get(lane["k"])
            return {"k": lane["k"], "ok": a is not None, "n": 1 if a is not None else 0, "avg": a or 0.0,
                    "lines": [{"text": "x", "conf": a or 0.0, "bbox": [0, 0, 1, 1]}], "err": "" if a is not None else "fail"}
        return run
    lm = {"rapidocr": {"state": "READY", "py": "py", "env": "via_rapidocr", "lane": {"k": "rapidocr"}},
          "paddleocr": {"state": "READY", "py": "py", "env": "via_paddle_311", "lane": {"k": "paddleocr"}}}
    r1 = ladder_page("i", lm, fake_runner({"rapidocr": 0.93, "paddleocr": 0.97}))
    c1, calls[:] = list(calls), []
    r2 = ladder_page("i", lm, fake_runner({"rapidocr": 0.70, "paddleocr": 0.95}))
    c2, calls[:] = list(calls), []
    lm_np = dict(lm, paddleocr={"state": "NO_ENV", "env": "via_paddle_311"})
    r3 = ladder_page("i", lm_np, fake_runner({"rapidocr": 0.70}))
    r4 = ladder_page("i", {"rapidocr": {"state": "NO_MOD"}, "paddleocr": {"state": "NO_ENV"}}, fake_runner({}))
    chk("③ 階梯:Rapid ≥ 0.85 就停(不叫重型)· 不足才升 Paddle · Paddle 不在照實留 Rapid 標低信心 · 兩道都不在 = no_ocr",
        r1[2] == "rapid" and c1 == ["rapidocr"] and r2[2] == "paddle" and c2 == ["rapidocr", "paddleocr"]
        and r3[2] == "rapid_low_conf_no_heavy" and r4[0] is None and r4[2] == "no_ocr",
        (r1[2], r2[2], r3[2], r4[2]))

    # ④ OCR 結果走同一條 LAYOUT 修復鏈:合成一張財報表(像素框 @300dpi)
    px = DPI / 72.0
    rows = [("項目", "2024", "2025"), ("營業收入", "1,234", "1,5O0"), ("營業成本", "(567)", "(600)"), ("營業利益", "667", "9O0")]
    lines, y = [], 100.0
    for r in rows:
        for x, t in zip((60.0, 260.0, 360.0), r):
            conf = 0.45 if t == "9O0" else 0.95
            lines.append({"text": t, "conf": conf, "bbox": [x * px, y * px, (x + 8 * len(t)) * px, (y + 10) * px]})
        y += 16.0
    sha = hashlib.sha256(b"praddle-selftest").hexdigest()
    odoc, conf = ocr_document("synthetic.pdf", sha, {1: {"k": "rapidocr", "lines": lines}}, {1: (595.0, 842.0)})
    with tempfile.TemporaryDirectory() as td:
        rep = hub.def_repair_document(odoc, Path(td), None)
    tabs = [finish_table(t, "ocr", conf, dn) for t in rep.get("tables") or []]
    t0 = tabs[0] if tabs else {}
    vals = [[c["value"] for c in r] for r in t0.get("rows", [])]
    flags = [(ri, ci, c.get("flags")) for ri, r in enumerate(t0.get("rows", [])) for ci, c in enumerate(r) if c.get("flags")]
    chk("④ 掃描頁 OCR 行照 GLE 格式進 SUP_MDL743 修復鏈:年度列種子還原出表格 · 括號負數 · 數值欄 O→0",
        len(tabs) == 1 and t0["header_count"] == 1 and vals[1][1:] == ["1234", "1500"] and vals[2][1:] == ["-567", "-600"],
        vals)
    chk("⑤ 逐格信心:格子取組成 OCR 行的最低信心;< 0.6 標 FLAGGED_MANUAL_REVIEW(只標那一格)",
        flags == [(3, 2, ["FLAGGED_MANUAL_REVIEW:low_conf"])], flags)

    pdf = VIA / "functional modules" / "VRN" / "references" / "intake" / "PDFRegressionEvidence_v1.0.0_b245" / \
        "PDFRegressionEvidence_v1.0.0" / "synthetic_financial_report.pdf"
    if pdf.is_file() and os.environ.get("VIA_FROM_VCGC") != "YES":
        chk("⑥ 數位原生 PDF(LAYOUT 整批只收 VCGC 呼叫;直跑 --selftest 跳過,經 via-vcgc run 才量)", True, "SKIP")
    elif pdf.is_file():
        with tempfile.TemporaryDirectory() as td:
            called = []
            rep = run_pdf(pdf, "auto", None, Path(td), lane_map={}, runner=lambda *a: called.append(a))
            saved = (Path(rep["out"]) / "PRADDLE.json").is_file()
        chk("⑥ 數位原生 PDF:分流 DIGITAL → 只走 pdfplumber / 原生 + LAYOUT,一次 OCR 都不叫;報告落地",
            rep["verdict"] in ("GREEN", "YELLOW") and all(r["route"] == "native" for r in rep["pages"])
            and not called and rep["native_lines"] > 0 and saved,
            f"{rep['verdict']} · 頁 {[r['triage'] for r in rep['pages']]} · 原生行 {rep['native_lines']} · {rep['sec']}s")
    else:
        chk("⑥ 數位原生 PDF(樣本不在 → 跳過,不冒充)", True, "SKIP")
    chk("⑦ CID 亂碼判得出(編碼壞的原生層改走 OCR)", _cid_ratio("(cid:12)(cid:34)(cid:56)ab") > CID_RATIO and _cid_ratio("營業收入 1,234") == 0.0)
    chk("⑧ 高風險隔離:本行程沒有 import paddle / rapidocr / onnxruntime / cv2;車道在各自隔離境(via_rapidocr · via_paddle_311)",
        not [m for m in HEAVY if m in sys.modules] and {x["envs"][0] for x in osu.LANES if x["k"] in ("rapidocr", "paddleocr")}
        == {"via_rapidocr", "via_paddle_311"})
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑨ 加速器橋 · VCGC 閘(VIA_FROM_VCGC)· 不用 TA-Lib / requests / urllib(零網路)",
        "[VIA:ACCEL-BRIDGE" in src and 'os.environ.get("VIA_FROM_VCGC")' in src
        and not re.search(r"^\s*(import|from)\s+(talib|requests|urllib)", src, re.M))
    good = all(ok)
    print(f"[VRN_ENG398 v0100 PRADDLE 擷取編排] 自測 {sum(ok)}/{len(ok)} {'PASS' if good else 'FAIL'}")
    return 0 if good else 1


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        return selftest()
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    if a[:1] == ["probe"]:
        layout_hub(), ppp_hub()
        lm = lanes()
        print(f"[PRADDLE 車道] LAYOUT {_MODS.get('layout', {}).get('src') or '缺'} · 分流 {_MODS.get('ppp', {}).get('src') or '缺'}")
        for k, v in lm.items():
            if not k.startswith("_"):
                print(f"  {k:<10} {v['state']:<7} 隔離境 {v['env']} · python {v.get('py') or '—'}")
        if lm.get("_why"):
            print("  " + lm["_why"])
        return 0
    if a[:1] == ["run"] and "--in" in a:
        given = Path(a[a.index("--in") + 1])
        src = next((c for c in (given, VIA / given, VIA.parent / given) if c.exists()), given)   # VCGC 的工作目錄不一定是倉根
        mode = a[a.index("--ocr") + 1] if "--ocr" in a else "auto"
        pages = a[a.index("--pages") + 1] if "--pages" in a else None
        pdfs = [src] if src.is_file() else sorted(src.rglob("*.pdf"))
        if not pdfs:
            print(f"  找不到 PDF:{given}(也找過 {VIA / given})")
            return 3
        worst = 0
        for p in pdfs:
            rep = run_pdf(p, mode, pages)
            _print(rep)
            worst = max(worst, {"GREEN": 0, "YELLOW": 2, "NODATA": 2}.get(rep.get("verdict"), 1))
        return worst
    print("用法:probe | run --in <pdf|夾> [--ocr auto|off|force] [--pages 1-3] | --selftest")
    return 2


if __name__ == "__main__":
    sys.exit(main())
