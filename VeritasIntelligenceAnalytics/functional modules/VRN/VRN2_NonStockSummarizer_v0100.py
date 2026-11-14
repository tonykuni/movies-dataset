#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VRN2_NonStockSummarizer v0100 — VRN-2 非個股車道入口:非個股摘要器 v0310 + 多格式輸入 → 矩陣輸出。

操作員 2026-11-12:「非個股 v0300 用在 VRN-2,摘要非個股報告、新聞、訊息;輸入有 PDF / Word / 圖片 / 文字,
要確保 VRN-2 都讀得到,經 v0300 摘要,結果用矩陣輸出;VRN-2 個股報告與非個股報告都能處理。」
(v0300 → v0310 只多了 reuse hard gate 與 bundled 標記,摘要邏輯一字相同;本支用倉內較新的 v0310。)

做法(v0310 原檔一字不改,SHA 釘住):
  ① 核心:nonstock_v0310/internal/NON_STOCK_CORE_v0200.py(操作員原件)在 → 原樣載入 v0310(模式 ORIGINAL);
     不在 → 執行期把 v0310 的 BUNDLED_CORE 指向 VRN-2 自建核心 VRN2_NonStockCore_v0100(模式 STANDIN · 每列標「暫代」)。
  ② 讀檔:PDF 有 PyMuPDF(fitz)→ v0310 自己的 VRN-2 版面 + 修復鏈;沒有 → 核心的 pdfplumber / pypdf / pdftotext,
     字太少(影像 PDF)→ VCGC 鎖版 OCR 隔離境車道。Word / 圖片 / 文字 / 網頁 / 訊息(JSON · .eml · LINE 匯出)/ 筆記 一律經核心讀。
  ③ 車道:PDF 用 VRN_ReportLaneCheck 的分類(與 VRN-2 主線 v0231 同一套排除字)— 個股報告歸 VRN-2 主線(矩陣列「個股車道」,
     --all 才在這裡一起摘要);其他格式一律非個股(新聞 / 訊息 / 筆記)。
  ④ 摘要:v0310 的一報告一主列(標題 + 四點)· 主題 / 公司 / 證據子表,照 v0310 契約。
  ⑤ 矩陣:NONSTOCK_MATRIX(一檔一列:編號 · 檔名 · 格式 · 讀取器 · 車道 · 類型 · 日期 · 來源 · 主題 · 標題 · 四點 · 方向 · 期間 ·
     公司 / 主題 / 證據數 · 原句驗證 · 狀態 · 說明)+ FORMAT_MATRIX(格式 × 狀態)→ CSV · Parquet · JSON · HTML;
     另寫 v0310 同形的 RESULTS.json / REPORT_SUMMARY / TOPIC_DETAIL / COMPANY_DETAIL / EVIDENCE_DETAIL(VRN2_ReportRows 直接吃)。
  ⑥ 原句驗證:四點都是抽取句,逐點回原文比對(去空白後子字串);對不上照實記,不改寫。
狀態五態(誠實):PASS(四點 ≥ 3 且原句全對)· REVIEW(點數不足或原句有對不上)· NODATA(讀到 0 字)·
  ABSENT(要的讀取工具不在:OCR 車道 / LibreOffice)· ERROR(例外)· 另 STOCK_LANE(個股報告 → VRN-2 主線)。
邊界:只讀輸入檔;只寫 --out 夾;不改 v0310 / reuse / 主線;零網路([VIA:NET-BRIDGE] 留名:本支不出網);不用 TA-Lib;不 import VCGC。
用法:python VRN2_NonStockSummarizer_v0100.py run <檔或夾…> [--out D] [--all] · doctor · --selftest
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

import argparse
import csv
import hashlib
import html
import importlib.util
import json
import re
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

VERSION = "v0100"
ENGINE = "VRN2_NonStockSummarizer " + VERSION
HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
NS_DIR = HERE / "nonstock_v0310"
NS_ENGINE = NS_DIR / "engine" / "VIA_NON_STOCK_SUMMARIZER_ENGINE_v0310.py"
NS_ENGINE_SHA = "86903811ad13b33ec4687105cc8143c0ea88997590807e235fcdf3224dcee5ef"   # 入倉 82d6154df 的原檔
NS_CORE = NS_DIR / "internal" / "NON_STOCK_CORE_v0200.py"
NS_CORE_SHA = "92f53d82c2facb41e599bf730b8be524901ed5d355aaed22a73444e85dccfa27"     # REUSE_MANIFEST_v0310
STANDIN_CORE = HERE / "VRN2_NonStockCore_v0100.py"
LANE_FILE = HERE / "VRN_ReportLaneCheck_v0100.py"
CORE_LINE = 'BUNDLED_CORE = ROOT/"internal"/"NON_STOCK_CORE_v0200.py"'
DEFAULT_OUT = VIA / "VIA_Reports" / "vrn2" / "nonstock"

MATRIX_COLS = ["NO", "FILE_NAME", "FORMAT", "READER", "LANE", "REPORT_TYPE", "REPORT_DATE", "SOURCE", "MAIN_INDUSTRY", "TITLE",
               "POINT_1", "POINT_2", "POINT_3", "POINT_4", "DIRECTION", "HORIZON", "COMPANY_COUNT", "TOPIC_COUNT", "EVIDENCE_COUNT",
               "VERBATIM", "CORE", "STATUS", "NOTE", "REPORT_ID"]
MATRIX_ZH = {"NO": "編號", "FILE_NAME": "檔名", "FORMAT": "格式", "READER": "讀取器", "LANE": "車道", "REPORT_TYPE": "類型",
             "REPORT_DATE": "日期", "SOURCE": "來源", "MAIN_INDUSTRY": "主題 / 產業", "TITLE": "標題", "POINT_1": "重點 ①",
             "POINT_2": "重點 ②", "POINT_3": "重點 ③", "POINT_4": "重點 ④", "DIRECTION": "方向", "HORIZON": "期間",
             "COMPANY_COUNT": "公司", "TOPIC_COUNT": "主題", "EVIDENCE_COUNT": "證據", "VERBATIM": "原句驗證", "CORE": "核心",
             "STATUS": "狀態", "NOTE": "說明", "REPORT_ID": "報告 ID"}
STATUSES = ["PASS", "REVIEW", "NODATA", "ABSENT", "ERROR", "STOCK_LANE"]
STATUS_ZH = {"PASS": "通過", "REVIEW": "待看", "NODATA": "沒讀到字", "ABSENT": "缺讀取工具", "ERROR": "錯誤", "STOCK_LANE": "個股 → 主線"}


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else ""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ── ① 載入 v0310(原件核心優先;沒有 → VRN-2 自建核心暫代)─────────────────────────
def core_state() -> dict:
    if NS_CORE.is_file():
        sha = _sha(NS_CORE)
        return {"mode": "ORIGINAL", "core": "NON_STOCK_CORE_v0200", "path": str(NS_CORE), "sha_match": sha == NS_CORE_SHA,
                "why": "操作員原件" + ("" if sha == NS_CORE_SHA else "(SHA 與 manifest 不同 · 照實記)")}
    return {"mode": "STANDIN", "core": "VRN2_NonStockCore_v0100", "path": str(STANDIN_CORE), "sha_match": None,
            "why": "缺 internal/NON_STOCK_CORE_v0200.py(SHA %s…)→ VRN-2 自建核心暫代" % NS_CORE_SHA[:8]}


_ENGINE_CACHE: dict = {}


def load_engine():
    """回 (v0310 模組, core_state)。v0310 檔本身不動:STANDIN 模式只在執行期把 BUNDLED_CORE 那一行換成自建核心路徑。"""
    if "e" in _ENGINE_CACHE:
        return _ENGINE_CACHE["e"], _ENGINE_CACHE["st"]
    st = core_state()
    st["engine_sha_match"] = _sha(NS_ENGINE) == NS_ENGINE_SHA
    if st["mode"] == "ORIGINAL":
        eng = _load("vrn2_nonstock_v0310_original", NS_ENGINE)
    else:
        src = NS_ENGINE.read_text(encoding="utf-8")
        if src.count(CORE_LINE) != 1:
            raise RuntimeError("v0310 的 BUNDLED_CORE 行對不上(檔被換過?)→ 不硬套")
        src = src.replace(CORE_LINE, "BUNDLED_CORE = Path(%r)" % str(STANDIN_CORE), 1)
        spec = importlib.util.spec_from_loader("vrn2_nonstock_v0310_standin", loader=None, origin=str(NS_ENGINE))
        eng = importlib.util.module_from_spec(spec)
        eng.__file__ = str(NS_ENGINE)                          # ROOT = nonstock_v0310(reuse/vrn2 照原路徑找)
        sys.modules[spec.name] = eng
        exec(compile(src, str(NS_ENGINE), "exec"), eng.__dict__)  # noqa: S102 — 倉內 SHA 釘住的 v0310 原檔
    _ENGINE_CACHE.update(e=eng, st=st)
    return eng, st


def _fitz_ok() -> bool:
    try:
        import fitz  # noqa: F401
        return True
    except ImportError:
        return False


def extract(eng, path: Path) -> tuple:
    """(blocks, meta, title_map)。PDF 有 fitz → v0310 自己的 VRN-2 版面鏈;其他一律經核心讀。"""
    core = eng.CORE
    if path.suffix.lower() == ".pdf" and _fitz_ok():
        try:
            blocks, meta, tmap = eng.def_extract_pdf_vrn2(path)
            meta = dict(meta, format="PDF", reader="VRN-2 版面(PyMuPDF)+ MDL003 修復")
            if blocks:
                return blocks, meta, tmap
        except Exception as exc:  # noqa: BLE001 — 版面鏈失敗退核心讀法,原因記進 meta
            fallback_why = "版面鏈 %s" % type(exc).__name__
        else:
            fallback_why = "版面鏈 0 塊"
    else:
        fallback_why = ""
    blocks, meta = core.def_extract_input(path)
    meta = dict(meta)
    meta.setdefault("reader", meta.get("pdf_reader", ""))
    if path.suffix.lower() == ".pdf":
        meta["reader"] = meta.get("pdf_reader", "") + ("(無 fitz)" if not _fitz_ok() else "(" + fallback_why + ")")
    tmap = {}                                                    # 每頁第一個標題塊當頁標題(訊息不用:一則一列)
    if meta.get("format") != "MESSAGE":
        for b in blocks:
            if b.page not in tmap and b.block_type == "HEADING":
                tmap[b.page] = b.text
    return blocks, meta, tmap


def analyze(eng, path: Path) -> dict:
    """照 v0310 def_analyze_one 的步驟,只把讀檔換成 extract()。"""
    blocks, meta, title_map = extract(eng, path)
    if not blocks or not sum(len(b.text) for b in blocks):
        return {"status": "NODATA", "meta": meta}
    profile, subtype = eng.def_route_profile(path, blocks)
    if profile == eng.CORE.PROFILE_MESSENGER:
        blocks = eng.CORE.def_parse_messenger_blocks(path, blocks)
    if profile == eng.CORE.PROFILE_EVERNOTE:
        blocks = eng.CORE.def_apply_note_layers(blocks)
    units = eng.def_build_topic_units(profile, blocks, title_map)
    rid = "RPT-%s" % eng.def_hash8(path.name + eng.def_file_sha(path)[:16])
    topics, claims = eng.def_topic_rows(path, rid, profile, units)
    full = eng.CORE.def_extract_claims(blocks)                  # 不漏句:v0310 只從 ≥30 字的單位抽,短段落的句子在這裡補回
    have = {c.text for c in claims}
    claims = claims + [c for c in full if c.text not in have]
    report = eng.def_report_summary(path, profile, subtype, blocks, title_map, claims, topics)
    for r in topics:
        r["REPORT_ID"] = report["REPORT_ID"]
    companies = eng.def_company_rows(report["REPORT_ID"], blocks, claims)
    evidence = eng.def_evidence_rows(report["REPORT_ID"], claims)
    return {"status": "OK", "report": report, "topics": topics, "companies": companies, "evidence": evidence, "meta": meta,
            "source_text": "\n".join(b.text for b in blocks)}


def verbatim(points: list, source_text: str) -> tuple:
    """抽取句逐點回原文(去空白、去 v0310 截斷的「…」;「涉及公司:」是 v0310 組的,不算抽取句)。"""
    hay = re.sub(r"\s+", "", source_text or "")
    n = ok = 0
    for p in points:
        if not p or p.startswith("涉及公司："):
            continue
        n += 1
        needle = re.sub(r"\s+", "", p.rstrip("…"))
        ok += bool(needle) and needle in hay
    return ok, n


# ── ② 車道 / 收集 ──────────────────────────────────────────────────────────
def collect(inputs: list, exts: set) -> list:
    out = []
    for raw in inputs:
        p = Path(raw)
        if p.is_dir():
            out.extend(sorted(x for x in p.iterdir() if x.is_file() and x.suffix.lower() in exts and not x.name.startswith("~$")))
        elif p.is_file():
            out.append(p)
    seen, res = set(), []
    for p in out:
        k = str(p.resolve())
        if k not in seen:
            seen.add(k)
            res.append(p)
    return res


def lane_of(path: Path, lane_mod, excl, first_text: str = "") -> dict:
    if path.suffix.lower() != ".pdf" or lane_mod is None:
        return {"lane": "non_stock", "why": "非 PDF(新聞 / 訊息 / 筆記 / 文件)一律非個股車道"}
    return lane_mod.classify(path.name, excl, first_text[:400])


# ── ③ 一批跑 → 矩陣 ─────────────────────────────────────────────────────────
def run(inputs: list, out: Path, include_stock: bool = False) -> dict:
    eng, st = load_engine()
    core = eng.CORE
    files = collect(inputs, core.ALL_EXT if hasattr(core, "ALL_EXT") else {".pdf", ".txt", ".md", ".html", ".htm", ".docx", ".enex", ".json"})
    lane_mod = _load("vrn2_lane_for_nonstock", LANE_FILE) if LANE_FILE.is_file() else None
    excl = lane_mod.load_excl(HERE)[0] if lane_mod else None
    out.mkdir(parents=True, exist_ok=True)
    reports, topics, companies, evidence, runs, matrix = [], [], [], [], [], []
    for i, p in enumerate(files, 1):
        fmt = getattr(core, "FORMAT_OF", {}).get(p.suffix.lower(), p.suffix.lower().lstrip(".").upper() or "?")
        row = {"NO": "NS-%03d" % i, "FILE_NAME": p.name, "FORMAT": fmt, "CORE": "原件" if st["mode"] == "ORIGINAL" else "暫代"}
        try:
            lane = lane_of(p, lane_mod, excl)
            if lane.get("lane") == "stock" and lane_mod is not None:
                cover = ""
                try:
                    b0, _m0 = core.def_extract_input(p)
                    cover = " ".join(b.text for b in b0[:3])
                except Exception:  # noqa: BLE001 — 只為取首頁標題給分類用,讀不到就照檔名分
                    cover = ""
                lane = lane_of(p, lane_mod, excl, cover)
            row["LANE"] = "個股" if lane.get("lane") == "stock" else "非個股"
            if lane.get("lane") == "stock" and not include_stock:
                row.update(STATUS="STOCK_LANE", NOTE="個股報告(%s)→ VRN-2 主線處理;--all 才在這裡一起摘要" % lane.get("why", ""))
                runs.append({"file": p.name, "status": "STOCK_LANE"})
                matrix.append(row)
                continue
            x = analyze(eng, p)
            row["READER"] = x["meta"].get("reader", "")
            if x["status"] == "NODATA":
                row.update(STATUS="NODATA", NOTE="讀到 0 字(%s)" % (x["meta"].get("pdf_reader") or x["meta"].get("reader") or ""))
                runs.append({"file": p.name, "status": "NODATA"})
                matrix.append(row)
                continue
            rep = x["report"]
            if st["mode"] == "STANDIN":
                rep["NLP_ENGINE"] = "VRN_M07_EXTRACTIVE+VRN2_NonStockCore_v0100(暫代)"
            if rep.get("LAYOUT_ENGINE", "").startswith("VRN_M03") and not str(row["READER"]).startswith("VRN-2 版面"):
                rep["LAYOUT_ENGINE"], rep["TEXT_REPAIR_ENGINE"] = row["READER"], "VRN2_NonStockCore 正規化"
            pts = [rep.get("POINT_%d" % k, "") for k in range(1, 5)]
            vok, vn = verbatim(pts, x["source_text"])
            status = rep.get("STATUS", "REVIEW")
            if vn and vok < vn:
                status = "REVIEW"
            rep["STATUS"] = status
            row.update({k: rep.get(k, "") for k in MATRIX_COLS if k in rep})
            row.update(VERBATIM="%d/%d" % (vok, vn), STATUS=status, LANE=row["LANE"],
                       NOTE=("四點 %d/4" % sum(bool(p_) for p_ in pts)) + ("" if status == "PASS" else " · 原句對不上 %d" % (vn - vok) if vn > vok else ""))
            reports.append(rep)
            topics += x["topics"]
            companies += x["companies"]
            evidence += x["evidence"]
            runs.append({"file": p.name, "status": status, "report_id": rep["REPORT_ID"], "topics": len(x["topics"]),
                         "companies": len(x["companies"]), "evidence": len(x["evidence"]), "reader": row["READER"]})
        except Exception as exc:  # noqa: BLE001 — 一檔失敗不擋整批;分 ABSENT / ERROR 照實記
            absent = type(exc).__name__ == "ReaderUnavailable"
            row.update(STATUS="ABSENT" if absent else "ERROR", NOTE=("%s" if absent else "%s") % str(exc)[:220] if absent
                       else "%s: %s" % (type(exc).__name__, str(exc)[:200]))
            row.setdefault("LANE", "非個股")
            runs.append({"file": p.name, "status": row["STATUS"], "error": row["NOTE"]})
        matrix.append(row)
    fmt_matrix = format_matrix(matrix)
    lamp = lamp_of(matrix)
    write_all(eng, out, st, reports, topics, companies, evidence, runs, matrix, fmt_matrix, lamp)
    return {"engine": ENGINE, "at": _now(), "lamp": lamp, "files": len(files), "core": st, "status": dict(Counter(r["STATUS"] for r in matrix)),
            "by_format": dict(Counter(r["FORMAT"] for r in matrix)), "reports": len(reports), "topics": len(topics),
            "companies": len(companies), "evidence": len(evidence), "out": str(out)}


def format_matrix(matrix: list) -> list:
    fmts = sorted({r["FORMAT"] for r in matrix})
    rows = []
    for f in fmts:
        c = Counter(r["STATUS"] for r in matrix if r["FORMAT"] == f)
        rows.append({"FORMAT": f, **{s: c.get(s, 0) for s in STATUSES}, "TOTAL": sum(c.values())})
    return rows


def lamp_of(matrix: list) -> str:
    if not matrix:
        return "NODATA"
    st = Counter(r["STATUS"] for r in matrix)
    if st.get("ERROR"):
        return "RED"
    if st.get("REVIEW") or st.get("NODATA") or st.get("ABSENT"):
        return "YELLOW"
    return "GREEN" if st.get("PASS") else "NODATA"


def _csv(path: Path, cols: list, rows: list, header=None) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header or cols)
        for r in rows:
            w.writerow([r.get(c, "") for c in cols])


def write_all(eng, out, st, reports, topics, companies, evidence, runs, matrix, fmt_matrix, lamp) -> None:
    eng.def_write_csv(out / "REPORT_SUMMARY.csv", eng.REPORT_COLUMNS, reports)
    eng.def_write_csv(out / "TOPIC_DETAIL.csv", eng.TOPIC_COLUMNS, topics)
    eng.def_write_csv(out / "COMPANY_DETAIL.csv", eng.COMPANY_COLUMNS, companies)
    eng.def_write_csv(out / "EVIDENCE_DETAIL.csv", eng.EVIDENCE_COLUMNS, evidence)
    pq = {k: eng.def_write_parquet_if_available(out / f, rows) for k, f, rows in
          [("report", "REPORT_SUMMARY.parquet", reports), ("topic", "TOPIC_DETAIL.parquet", topics),
           ("company", "COMPANY_DETAIL.parquet", companies), ("evidence", "EVIDENCE_DETAIL.parquet", evidence),
           ("matrix", "NONSTOCK_MATRIX.parquet", [{c: str(r.get(c, "")) for c in MATRIX_COLS} for r in matrix])]}
    _csv(out / "NONSTOCK_MATRIX.csv", MATRIX_COLS, matrix, [MATRIX_ZH[c] for c in MATRIX_COLS])
    _csv(out / "FORMAT_MATRIX.csv", ["FORMAT", *STATUSES, "TOTAL"], fmt_matrix, ["格式", *[STATUS_ZH[s] for s in STATUSES], "合計"])
    payload = {"engine_id": getattr(eng, "ENGINE_ID", ""), "version": getattr(eng, "ENGINE_VERSION", ""), "wrapper": ENGINE,
               "network_allowed": False, "core": st, "lamp": lamp, "runs": runs, "report_summary": reports, "topic_detail": topics,
               "company_detail": companies, "matrix": matrix, "format_matrix": fmt_matrix, "parquet": pq, "at": _now()}
    (out / "RESULTS.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "NONSTOCK_MATRIX.json").write_text(json.dumps({"lamp": lamp, "core": st, "matrix": matrix, "format_matrix": fmt_matrix},
                                                         ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "NONSTOCK_MATRIX.html").write_text(render_html(matrix, fmt_matrix, st, lamp), encoding="utf-8")


def render_html(matrix: list, fmt_matrix: list, st: dict, lamp: str) -> str:
    e = lambda s: html.escape(str(s if s is not None else ""))  # noqa: E731
    lamp_cls = {"PASS": "ok", "REVIEW": "warn", "NODATA": "warn", "ABSENT": "warn", "ERROR": "bad", "STOCK_LANE": "info"}
    head = "".join("<th>%s</th>" % e(MATRIX_ZH[c]) for c in MATRIX_COLS if c != "REPORT_ID")
    body = "".join("<tr>" + "".join(
        ('<td><span class="pill %s">%s</span></td>' % (lamp_cls.get(r.get(c), ""), e(STATUS_ZH.get(r.get(c), r.get(c)))) if c == "STATUS"
         else '<td class="pt">%s</td>' % e(r.get(c, "")) if c.startswith("POINT_") or c in ("TITLE", "NOTE")
         else "<td>%s</td>" % e(r.get(c, ""))) for c in MATRIX_COLS if c != "REPORT_ID") + "</tr>" for r in matrix)
    fh = "<th>格式</th>" + "".join("<th>%s</th>" % e(STATUS_ZH[s]) for s in STATUSES) + "<th>合計</th>"
    fb = "".join("<tr><td>%s</td>%s<td>%s</td></tr>" % (e(r["FORMAT"]), "".join("<td>%s</td>" % (r[s] or "") for s in STATUSES), r["TOTAL"])
                 for r in fmt_matrix)
    return """<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VRN-2 非個股矩陣</title><style>
:root{--bg:#f6f5f2;--card:#fff;--fg:#26282b;--mute:#6b6f76;--line:#e3e1dc;--ok:#2f7d4f;--warn:#a86b12;--bad:#b3362c;--info:#3d5f8f}
@media (prefers-color-scheme:dark){:root{--bg:#17181a;--card:#1f2124;--fg:#e8e6e1;--mute:#9a9ea5;--line:#33363a;--ok:#6cc08b;--warn:#e0a84a;--bad:#ec7a6f;--info:#8fb0de}}
body{margin:0;background:var(--bg);color:var(--fg);font:13px/1.5 "Noto Sans TC","Segoe UI",system-ui,sans-serif}
main{padding:16px max(16px,env(safe-area-inset-left));max-width:2000px;margin:auto}h1{font-size:18px;margin:4px 0}
.sub{color:var(--mute)}.wrap{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:8px;margin:12px 0}
table{border-collapse:collapse;width:100%%}th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top;white-space:nowrap}
th{position:sticky;top:0;background:var(--card);font-weight:600;color:var(--mute)}td.pt{white-space:normal;min-width:220px;max-width:360px}
.pill{display:inline-block;padding:1px 8px;border-radius:10px;border:1px solid currentColor;font-size:12px}
.ok{color:var(--ok)}.warn{color:var(--warn)}.bad{color:var(--bad)}.info{color:var(--info)}.lamp{font-weight:700}
</style></head><body><main>
<h1>VRN-2 非個股摘要矩陣</h1>
<div class="sub">%s · 燈 <span class="lamp %s">%s</span> · 核心 %s(%s)· 一檔一列 · 四點皆為原文抽取句(原句驗證欄)</div>
<div class="wrap"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>
<h1>格式 × 狀態</h1><div class="wrap"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>
</main></body></html>""" % (e(ENGINE), {"GREEN": "ok", "YELLOW": "warn", "RED": "bad"}.get(lamp, "info"), e(lamp), e(st["core"]),
                            e(st["why"]), head, body, fh, fb)


def doctor() -> dict:
    st = core_state()
    try:
        import fitz  # noqa: F401
        fz = True
    except ImportError:
        fz = False
    core = _load("vrn2_nonstock_core_doctor", NS_CORE if st["mode"] == "ORIGINAL" else STANDIN_CORE)
    readers = {"pdf_text": "pdfplumber / pypdf / pdftotext", "pdf_layout_fitz": fz}
    for mod in ("pdfplumber", "pypdf", "docx", "bs4", "pypdfium2", "pandas"):
        try:
            importlib.import_module(mod)
            readers[mod] = True
        except ImportError:
            readers[mod] = False
    import shutil
    readers["libreoffice"] = bool(shutil.which("soffice") or shutil.which("libreoffice"))
    ocr = "?"
    if hasattr(core, "_ocr_module"):
        m = core._ocr_module()
        if m is not None:
            envs = m.env_map()
            ocr = {ln["k"]: m.probe_lane(ln, envs)[0] for ln in m.LANES}
    return {"engine": ENGINE, "core": st, "v0310_sha_match": _sha(NS_ENGINE) == NS_ENGINE_SHA, "readers": readers, "ocr_lanes": ocr,
            "formats": sorted(getattr(core, "ALL_EXT", []))}


# ── ④ 自測 ──────────────────────────────────────────────────────────────
def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""), flush=True)

    print("=== %s 自測(v0310 不改 · 多格式 → 矩陣)===" % ENGINE, flush=True)
    sha0 = _sha(NS_ENGINE)
    chk("① v0310 原檔 SHA 釘住(入倉 82d6154df)", sha0 == NS_ENGINE_SHA, sha0[:12])
    eng, st = load_engine()
    chk("② 引擎載入 · 核心模式照實(%s)" % st["mode"], hasattr(eng, "def_four_points") and st["mode"] in ("ORIGINAL", "STANDIN"), st["why"])
    chk("③ 載入不寫回 v0310 檔", _sha(NS_ENGINE) == sha0)
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "in"
        d.mkdir()
        (d / "20261112_產業專題_散熱.txt").write_text(
            "散熱產業專題\n\n結論:AI伺服器液冷滲透率提升,帶動散熱模組需求成長 40%。\n\n"
            "由於GB300功耗上升,CSP資本支出上調,推升水冷板與快接頭出貨。\n\n"
            "奇鋐(3017)與雙鴻(3324)為主要受惠者,2026年營收可望年增 35%。\n\n"
            "若關稅提高,下半年出貨可能放緩,需留意風險。", encoding="utf-8")
        (d / "news_shipping.html").write_text("<h1>航運快訊</h1><p>記者報導:貨櫃運價回升 12%,帶動長榮(2603)獲利改善。</p>"
                                              "<p>由於紅海航線受阻,運力吃緊推升運價。</p><p>若需求放緩,明年運價恐回落。</p>", encoding="utf-8")
        (d / "line_chat.json").write_text(json.dumps({"messages": [
            {"time": "09:01", "sender": "A", "text": "美債殖利率走高,聯準會降息時點延後,科技股承壓。"},
            {"time": "09:05", "sender": "B", "text": "PCB 族群訂單能見度到明年,金像電(2368)受惠AI伺服器需求成長 30%。"},
            {"time": "09:09", "sender": "C", "text": "若油價續漲,通膨可能再升溫,債市風險增加。"}]}, ensure_ascii=False), encoding="utf-8")
        try:
            import docx
            doc = docx.Document()
            doc.add_heading("記憶體產業展望", 1)
            doc.add_paragraph("結論:HBM 供給吃緊,推升 DRAM 報價上漲 15%。")
            doc.add_paragraph("由於 AI 伺服器需求成長,南亞科(2408)2026年獲利可望轉佳。")
            doc.add_paragraph("若終端需求不如預期,下半年報價可能回落。")
            doc.save(str(d / "memory_outlook.docx"))
            has_docx = True
        except ImportError:
            has_docx = False
        from PIL import Image
        Image.new("RGB", (60, 30), "white").save(d / "scan.png")
        (d / "empty.txt").write_text("   \n", encoding="utf-8")
        out = Path(td) / "out"
        s = run([str(d)], out)
        mx = {r["FILE_NAME"]: r for r in json.loads((out / "NONSTOCK_MATRIX.json").read_text(encoding="utf-8"))["matrix"]}
        t = mx.get("20261112_產業專題_散熱.txt", {})
        chk("④ 文字產業報告 → PASS · 四點都在 · 原句驗證全對", t.get("STATUS") == "PASS" and t.get("VERBATIM", "").split("/")[0] == t.get("VERBATIM", "/").split("/")[1]
            and all(t.get("POINT_%d" % k) for k in (1, 2, 3)), (t.get("STATUS"), t.get("VERBATIM"), t.get("REPORT_TYPE")))
        chk("⑤ 產業路由(INDUSTRY_REPORT)· 主題 = Thermal", t.get("REPORT_TYPE") == "INDUSTRY_REPORT" and "Thermal" in t.get("MAIN_INDUSTRY", ""),
            (t.get("REPORT_TYPE"), t.get("MAIN_INDUSTRY")))
        n = mx.get("news_shipping.html", {})
        chk("⑥ 新聞網頁 → NEWS · 有摘要", n.get("REPORT_TYPE") == "NEWS" and n.get("POINT_1"), (n.get("REPORT_TYPE"), n.get("STATUS")))
        m = mx.get("line_chat.json", {})
        chk("⑦ 訊息 JSON → MESSENGER · 有摘要", m.get("REPORT_TYPE") == "MESSENGER" and m.get("POINT_1"), (m.get("REPORT_TYPE"), m.get("STATUS")))
        w = mx.get("memory_outlook.docx", {})
        chk("⑧ Word(.docx)→ 有摘要 · 讀取器 python-docx", (not has_docx) or (w.get("POINT_1") and w.get("READER") == "python-docx"),
            (w.get("STATUS"), w.get("READER")) if has_docx else "ABSENT(無 python-docx)")
        im = mx.get("scan.png", {})
        chk("⑨ 圖片:有 OCR 車道 → 摘要;沒有 → ABSENT(照實,不假抽)", im.get("STATUS") in ("ABSENT", "NODATA", "PASS", "REVIEW")
            and (im.get("STATUS") != "ABSENT" or "OCR" in im.get("NOTE", "")), (im.get("STATUS"), im.get("NOTE", "")[:60]))
        chk("⑩ 空檔 → NODATA", mx.get("empty.txt", {}).get("STATUS") == "NODATA", mx.get("empty.txt", {}).get("STATUS"))
        files_ok = all((out / f).is_file() for f in ("NONSTOCK_MATRIX.csv", "NONSTOCK_MATRIX.html", "NONSTOCK_MATRIX.json", "FORMAT_MATRIX.csv",
                                                     "RESULTS.json", "REPORT_SUMMARY.csv", "TOPIC_DETAIL.csv", "COMPANY_DETAIL.csv", "EVIDENCE_DETAIL.csv"))
        chk("⑪ 矩陣 CSV / HTML / JSON + 格式 × 狀態 + v0310 同形子表都寫出", files_ok)
        res = json.loads((out / "RESULTS.json").read_text(encoding="utf-8"))
        chk("⑫ RESULTS.json 與 v0310 同鍵(VRN2_ReportRows 可直接吃)", all(k in res for k in ("report_summary", "topic_detail", "company_detail", "runs")))
        hdr = (out / "NONSTOCK_MATRIX.csv").read_text(encoding="utf-8-sig").splitlines()[0]
        chk("⑬ 矩陣表頭(編號 · 檔名 · 格式 · 讀取器 · 車道 · … · 原句驗證 · 狀態)", hdr.startswith("編號,檔名,格式,讀取器,車道") and "原句驗證" in hdr)
        chk("⑭ 燈號照實(有 NODATA/ABSENT → 不是 GREEN)", s["lamp"] in ("YELLOW", "RED") and s["lamp"] == lamp_of(list(mx.values())), s["lamp"])
        if st["mode"] == "STANDIN":
            rs = res["report_summary"]
            chk("⑮ 暫代核心每列都標「暫代」(不冒充原件)", rs and all("暫代" in r.get("NLP_ENGINE", "") for r in rs) and all(r["CORE"] == "暫代" for r in mx.values()))
        else:
            chk("⑮ 原件核心模式", all(r["CORE"] == "原件" for r in mx.values()))
        sv = lane_of(Path("MS-2308 20251128.pdf"), _load("vrn2_lane_st", LANE_FILE), _load("vrn2_lane_st2", LANE_FILE).load_excl(HERE)[0])
        chk("⑯ 個股 PDF 分到個股車道(與主線同一套分類)", sv.get("lane") == "stock", sv.get("why"))
        ok_v, n_v = verbatim(["AI 伺服器 需求成長…", "涉及公司：台積電(2330)"], "結論:AI伺服器需求成長 40%")
        chk("⑰ 原句驗證:去空白 · 去「…」· 公司清單不算", (ok_v, n_v) == (1, 1), (ok_v, n_v))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑱ 零網路 · 不用 TA-Lib · 不 import VCGC · 不寫同意閘",
        not re.search(r"^\s*(?:import|from)\s+(talib|requests|urllib|CGC_)", src, re.M)
        and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", src))
    n = sum(ok)
    print("[%s] %s selftest · %d/%d" % ("PASS" if n == len(ok) else "FAIL", ENGINE, n, len(ok)), flush=True)
    return 0 if n == len(ok) else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=ENGINE)
    ap.add_argument("verb", nargs="?", default="selftest", choices=["run", "doctor", "selftest"])
    ap.add_argument("inputs", nargs="*")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--all", action="store_true", help="個股報告也在這裡一起摘要(預設歸 VRN-2 主線)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest or a.verb == "selftest":
        return selftest()
    if a.verb == "doctor":
        print(json.dumps(doctor(), ensure_ascii=False, indent=2))
        return 0
    if not a.inputs:
        ap.error("run 要給檔或夾")
    s = run(a.inputs, Path(a.out), a.all)
    print("[%s] %s · 檔 %d · 狀態 %s · 格式 %s · 報告 %d · 主題 %d · 公司 %d · 證據 %d · 核心 %s → %s" % (
        s["lamp"], ENGINE, s["files"], json.dumps(s["status"], ensure_ascii=False), json.dumps(s["by_format"], ensure_ascii=False),
        s["reports"], s["topics"], s["companies"], s["evidence"], s["core"]["mode"], Path(a.out) / "NONSTOCK_MATRIX.html"), flush=True)
    return {"GREEN": 0, "YELLOW": 2, "NODATA": 2, "RED": 1}.get(s["lamp"], 1)


if __name__ == "__main__":
    sys.exit(main())
