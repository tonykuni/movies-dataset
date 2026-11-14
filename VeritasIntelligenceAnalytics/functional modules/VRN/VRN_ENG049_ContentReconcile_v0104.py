#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_ENG049_ContentReconcile v0104 — v0103 薄尾(前版一字不動):對帳矩陣橫向擴張成 VRN 輸出驗證矩陣(verify 動詞)。

操作員令(2026-11-13):「將這個矩陣橫向擴張為 VRN 的輸出驗證矩陣」。v0102/v0103 的對帳只到「擷取產物在不在」
(覆蓋層 · 文字塊 · 表格列 · 目標價可尋性);本版在同一列(鍵 = SSOT v2 的 source_document)往右接上 VRN-2 下游每一段的
實際產出與驗證結果,一列看到底:

  A 擷取   對帳態(FULL / TEXT_ONLY / TABLE_ONLY / DOCX_TXT / FIRSTPAGE / NO_EXTRACTION)· 文字塊 · 表格列 · 首頁字數
  B SSOT   類型 · 代號 · 券商 · 日期 · 評等 · 目標價候選 · 記錄態
  C 基本   VRN2_BasicInfo 有無 · 欄位驗證(VERIFIED / 原文 / 兩條讀法)數 / 總欄數 · 缺漏欄
  D 財報   VRN2_FinancialData 值數 · 帶 VERIFY 證據的值數(逐值對回原文的讀法)
  E 摘要   VRN2_Summary 四點(POINTS_OK)
  F 拒收   VRN2_Rejected 列數(驗證器擋下、不進冊;不是錯,照列)
  G 一致   SSOT 代號 ↔ 輸出 TICKER · SSOT 券商 ↔ 輸出 BROKER / BROKER_EN
  H 燈     GREEN 全段到位且一致 · YELLOW 有拒收 / 缺欄 / 摘要不足 · RED 代號或券商對不上、或財報值沒有驗證證據
           · NODATA 本輪輸出冊沒有這份(沒跑到,不冒充綠)· N/A 非個股(個股輸出冊本來就不收)

對鍵:先比正規化全名;對不上再比檔名裡 ≥ 4 碼的數字串(代號 · 日期)—— 輸出冊的檔名可能被系統把中文換成底線。
唯讀:只讀 SSOT v2 · staging · first_page_text · VIA_Reports/vrn2/output;只寫 VIA_Reports/vrn_reconcile_runs/verify_<ts>.{json,csv,html}。
零網路 · 零落庫 · 不用 TA-Lib · 不寫同意閘。
用法:py VRN_ENG049_ContentReconcile_v0104.py verify [--ssot F.jsonl] [--out-dir D] [--staging D] [--json] · 其餘照 v0103 · --selftest
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
# [VIA:NET-BRIDGE] 留名:本版不出網

import csv
import html
import importlib.util
import json
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path

VERSION = "v0104"
HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
STEM = "VRN_ENG049_ContentReconcile"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)

STOCK_TYPES = {"COMPANY_REPORT", "COMPANY_INTERVIEW", "COMPANY_UPDATE", "INITIATION", "STOCK"}
OK_MARKS = ("VERIFIED", "原文", "兩條讀法", "首頁")
BASIC_FIELDS = ["REPORT_DATE", "TICKER", "NAME", "BROKER", "ANALYST", "RATING", "TARGET_PRICE", "CURRENT_PRICE_REPORT", "UPSIDE_PCT", "TITLE"]
SUMMARY_FIELDS = ["POINT_1", "POINT_2", "POINT_3", "POINT_4", "POINTS_OK"]
# 個股矩陣:BASIC INFO 每欄值 + 驗證態 · SUMMARY 四點全攤開(操作員 2026-11-13「BASIC INFO + SUMMARY FOR STOCK REPORTS」)
STOCK_COLUMNS = [("A 擷取", ["對帳態", "首頁字數"]),
                 ("B SSOT", ["代號", "券商", "日期", "評等", "目標價候選"]),
                 ("C BASIC INFO", ["B." + f for f in BASIC_FIELDS] + ["欄位驗證", "缺漏欄"]),
                 ("D SUMMARY", ["S." + f for f in SUMMARY_FIELDS]),
                 ("E 財報 / 拒收", ["財報值", "有驗證證據", "拒收列"]),
                 ("F 一致", ["代號一致", "券商一致"]),
                 ("G 燈", ["燈", "原因"])]
NS_FIELDS = ["FORMAT", "READER", "LANE", "MAIN_INDUSTRY", "TITLE", "DIRECTION", "HORIZON", "POINT_1", "POINT_2", "POINT_3", "POINT_4",
             "COMPANY_COUNT", "TOPIC_COUNT", "EVIDENCE_COUNT", "VERBATIM", "STATUS"]
# 非個股矩陣(新設計):讀取 → 內容 → 四重點 → 證據 / 原句驗證 → 燈(操作員 2026-11-13「DESIGN NEW MATRICS FOR NON-STOCK REPORTS」)
NONSTOCK_COLUMNS = [("A 擷取", ["對帳態", "首頁字數"]),
                    ("B SSOT", ["類型", "券商", "日期", "提及代號"]),
                    ("C 讀取", ["N.FORMAT", "N.READER", "N.LANE"]),
                    ("D 內容", ["N.MAIN_INDUSTRY", "N.TITLE", "N.DIRECTION", "N.HORIZON"]),
                    ("E 四重點", ["N.POINT_1", "N.POINT_2", "N.POINT_3", "N.POINT_4"]),
                    ("F 證據", ["N.COMPANY_COUNT", "N.TOPIC_COUNT", "N.EVIDENCE_COUNT", "N.VERBATIM"]),
                    ("G 燈", ["N.STATUS", "燈", "原因"])]
COLUMNS = STOCK_COLUMNS


def __getattr__(name):
    return getattr(PRIOR, name)


def _body():
    return PRIOR._load_body()


def norm(s: str) -> str:
    return _body().norm(str(s or ""))


def digits(s: str) -> set:
    return set(re.findall(r"\d{4,}", str(s or "")))


def _txt(v) -> str:
    if isinstance(v, list):
        return " / ".join(str(x.get("value") if isinstance(x, dict) else x) for x in v if x not in (None, ""))
    return "" if v is None else str(v)


def ssot_records(path: Path | None = None) -> tuple:
    cands = [path] if path else [HERE / "SSOT/v2/VRN_ResearchReport_SSOT.v2.jsonl"] + sorted((HERE / "SSOT/v2/generations").glob("*.jsonl"))
    for p in cands:
        if p and Path(p).is_file():
            return [json.loads(l) for l in Path(p).read_text(encoding="utf-8-sig").splitlines() if l.strip()], Path(p)
    return [], None


def _rows(path: Path) -> list:
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return d if isinstance(d, list) else (d.get("rows") or [])


def outputs(out_dir: Path, ns_dir: Path | None = None) -> dict:
    d = {k: _rows(out_dir / f"VRN2_{k}_latest.json") for k in ("BasicInfo", "FinancialData", "Summary", "Rejected")}
    try:
        d["NonStock"] = json.loads(((ns_dir or VIA / "VIA_Reports" / "vrn2" / "nonstock") / "NONSTOCK_MATRIX.json").read_text(encoding="utf-8")).get("matrix") or []
    except (OSError, ValueError):
        d["NonStock"] = []
    for r in d["NonStock"]:
        r.setdefault("FILENAME", r.get("FILE_NAME", ""))
    return d


def match(doc: str, rows: list) -> list:
    nd = norm(doc)
    hit = [r for r in rows if norm(r.get("FILENAME", "")) == nd]
    if hit:
        return hit
    dd = digits(Path(doc).stem)
    return [r for r in rows if dd and dd <= digits(Path(str(r.get("FILENAME", ""))).stem)] if dd else []


def _same(a: str, b: str) -> bool | None:
    a, b = re.sub(r"[^0-9A-Z]", "", str(a).upper()), re.sub(r"[^0-9A-Z]", "", str(b).upper())
    if not a or not b:
        return None
    return a in b or b in a


def coverage(staging: Path) -> dict:
    b = _body()
    t = b.load_flat(staging / "mdl005_temp", "VRN_MDL005_Text") or []
    tb = b.load_flat(staging / "mdl004_temp", "VRN_MDL004_Tables") or []
    dx = {norm(p.stem) for p in (staging / "docx_txt").glob("*.txt")} if (staging / "docx_txt").exists() else set()
    fp_dir = VIA / "VIA_Reports" / "first_page_text"
    fp = {norm(p.stem): p for p in fp_dir.glob("*.txt")} if fp_dir.exists() else {}
    return {"text": t, "table": tb, "docx": dx, "fp": fp}


def is_stock(rec: dict) -> bool:
    """個股 = 類型是公司報告類 · 或有主代號 · 或類型空白但檔名帶「-四碼代號-」(如 華南投顧-4153-鈺緯-Memo)。"""
    rt = _txt(rec.get("final_report_type_proposal"))
    if rt in STOCK_TYPES or _txt(rec.get("final_primary_ticker_proposals")):
        return True
    return not rt and bool(re.search(r"[-_(]\d{4}[A-Z]?[-_),]", str(rec.get("source_document", ""))))


def _short(v, n=60) -> str:
    t = "" if v is None else str(v)
    return t if len(t) <= n else t[:n - 1] + "…"


def _base(rec: dict, cov: dict) -> dict:
    keys = ("pdf_name", "source_document", "source_pdf", "file_name")
    doc = rec.get("source_document", "")
    nd, ns = norm(doc), norm(Path(doc).stem)
    tblk = [r for r in cov["text"] if any(norm(str(r.get(k, ""))) == nd for k in keys)]
    trow = [r for r in cov["table"] if any(norm(str(r.get(k, ""))) == nd for k in keys)]
    fpp = cov["fp"].get(ns)
    if doc.lower().endswith((".docx", ".doc")):
        st = "DOCX_TXT" if ns in cov["docx"] else ("FIRSTPAGE" if fpp else "NO_EXTRACTION")
    else:
        st = "FULL" if tblk and trow else "TEXT_ONLY" if tblk else "TABLE_ONLY" if trow else "FIRSTPAGE" if fpp else "NO_EXTRACTION"
    return {"source_document": doc, "對帳態": st, "文字塊": len(tblk), "表格列": len(trow),
            "首頁字數": len(fpp.read_text(encoding="utf-8", errors="replace")) if fpp else 0,
            "類型": _txt(rec.get("final_report_type_proposal")) or "—", "代號": _txt(rec.get("final_primary_ticker_proposals")) or "—",
            "券商": _txt(rec.get("final_broker_proposal")) or "—", "日期": _txt(rec.get("report_date_guess")) or "—",
            "評等": _txt(rec.get("rating_content_guess")) or "—", "目標價候選": _txt(rec.get("filtered_target_price_proposals")) or "—",
            "提及代號": (lambda t: f"{len([x for x in t.split(';') if x])} 檔" if t else "—")(_txt(rec.get("mentioned_tickers_review_only"))),
            "記錄態": rec.get("canonical_record_state", "?")}


def build_stock(rec: dict, outs: dict, cov: dict) -> dict:
    row = _base(rec, cov)
    doc = row["source_document"]
    bi, fd = match(doc, outs["BasicInfo"]), match(doc, outs["FinancialData"])
    sm, rj = match(doc, outs["Summary"]), match(doc, outs["Rejected"])
    b, s = (bi[0] if bi else {}), (sm[0] if sm else {})
    stat = b.get("_STATUS") or {}
    for f in BASIC_FIELDS:
        v = b.get(f)
        mark = stat.get(f)
        row["B." + f] = ("—" if v in (None, "") else _short(v, 40)) + (f" [{_short(mark, 18)}]" if mark else "")
    good = [k for k, v in stat.items() if any(m in str(v) for m in OK_MARKS)]
    miss = [k for k, v in stat.items() if str(v).startswith("MISSING")]
    row["欄位驗證"] = f"{len(good)}/{len(stat)}" if stat else "—"
    row["缺漏欄"] = " · ".join(miss) or "—"
    for f in SUMMARY_FIELDS:
        v = s.get(f)
        row["S." + f] = "—" if v in (None, "") else _short(v, 80)
    ver = [r for r in fd if str(r.get("VERIFY") or "").strip()]
    row.update({"財報值": len(fd), "有驗證證據": len(ver), "拒收列": len(rj)})
    same_t = _same(row["代號"] if row["代號"] != "—" else "", b.get("TICKER")) if b else None
    same_b = _same(row["券商"].replace("_", "") if row["券商"] != "—" else "", b.get("BROKER_EN") or b.get("BROKER")) if b else None
    row["代號一致"] = "—" if same_t is None else ("是" if same_t else "否")
    row["券商一致"] = "—" if same_b is None else ("是" if same_b else "否")
    why = []
    if not (bi or fd or sm):
        lamp = "NODATA"
        why.append("本輪輸出冊沒有這份(沒跑到;不冒充綠)")
    else:
        if same_t is False:
            why.append("代號對不上")
        if fd and len(ver) < len(fd):
            why.append(f"財報值 {len(fd) - len(ver)} 個沒有驗證證據")
        lamp = "RED" if why else "GREEN"
        if lamp == "GREEN":
            if not bi:
                why.append("缺 BASIC INFO 列")
            if not sm:
                why.append("缺 SUMMARY 列")
            elif not s.get("POINTS_OK"):
                why.append("摘要四點未過(POINTS_OK=0)")
            if rj:
                why.append(f"拒收 {len(rj)} 列")
            if miss:
                why.append("缺漏欄 " + " · ".join(miss))
            if same_b is False:
                why.append("券商寫法不同(SSOT 代碼 vs 輸出名)")
            lamp = "YELLOW" if why else "GREEN"
    row.update({"燈": lamp, "原因": " · ".join(why) or "BASIC INFO + SUMMARY 全欄到位 · 財報值全有驗證證據"})
    return row


def build_nonstock(rec: dict, outs: dict, cov: dict) -> dict:
    row = _base(rec, cov)
    hit = match(row["source_document"], outs.get("NonStock") or [])
    n = hit[0] if hit else {}
    for f in NS_FIELDS:
        v = n.get(f)
        row["N." + f] = "—" if v in (None, "") else _short(v, 80 if f.startswith("POINT") else 40)
    st = str(n.get("STATUS") or "")
    why = []
    if not n:
        lamp = "NODATA"
        why.append("非個股矩陣(VIA_Reports/vrn2/nonstock/NONSTOCK_MATRIX.json)沒有這份 → 跑 VRN2_NonStockSummarizer")
    elif st == "PASS":
        pts = sum(1 for k in ("POINT_1", "POINT_2", "POINT_3", "POINT_4") if str(n.get(k) or "").strip())
        lamp = "GREEN" if pts >= 3 else "YELLOW"
        why.append(f"原句驗證通過 · 重點 {pts}/4")
    elif st in ("REVIEW", "STOCK_LANE"):
        lamp = "YELLOW"
        why.append("待人看" if st == "REVIEW" else "摘要器判為個股 → 與 SSOT 類型不一致,要裁定車道")
    elif st in ("NODATA", "ABSENT"):
        lamp = "NODATA"
        why.append("沒讀到字" if st == "NODATA" else "缺讀取工具(交 VCGC 裝)")
    else:
        lamp = "RED"
        why.append(f"摘要器 {st or '未知狀態'}")
    row.update({"燈": lamp, "原因": " · ".join(why)})
    return row


def build(records: list, outs: dict, cov: dict) -> dict:
    stock, nonstock = [], []
    for rec in records:
        (stock if is_stock(rec) else nonstock).append(build_stock(rec, outs, cov) if is_stock(rec) else build_nonstock(rec, outs, cov))
    return {"stock": stock, "nonstock": nonstock}


def summary(rows: list) -> dict:
    lamps = {}
    for r in rows:
        lamps[r["燈"]] = lamps.get(r["燈"], 0) + 1
    verdict = "RED" if lamps.get("RED") else ("YELLOW" if lamps.get("YELLOW") or lamps.get("NODATA") else ("GREEN" if rows else "NODATA"))
    return {"records": len(rows), "lamps": lamps, "verdict": verdict}


def _col_cover(rows: list, cols: list) -> dict:
    return {c: sum(1 for r in rows if str(r.get(c, "—")).strip() not in ("—", "", "0")) for _, cs in cols for c in cs if c not in ("燈", "原因")}


def render(mx: dict, summ: dict, meta: dict) -> str:
    color = {"GREEN": "#2e7d32", "YELLOW": "#b26a00", "RED": "#c62828", "NODATA": "#6b7280"}

    def table(title, rows, cols, sm):
        head1 = "".join(f'<th colspan="{len(c)}">{html.escape(g)}</th>' for g, c in cols)
        head2 = "".join(f"<th>{html.escape(c.split('.', 1)[-1])}</th>" for _, cs in cols for c in cs)
        cover = _col_cover(rows, cols)
        foot = "".join(f"<td>{cover.get(c, '')}</td>" if c in cover else "<td></td>" for _, cs in cols for c in cs)
        body = "".join("<tr><td>%s</td>%s</tr>" % (html.escape(r["source_document"]), "".join(
            f'<td style="color:{color.get(r[c], "inherit")};font-weight:600">{html.escape(str(r[c]))}</td>' if c == "燈"
            else f"<td>{html.escape(str(r.get(c, '—')))}</td>" for _, cs in cols for c in cs)) for r in rows)
        return (f"<h3>{html.escape(title)} · 記錄 {sm['records']} · 總判 <span style=\"color:{color.get(sm['verdict'], '#000')}\">{sm['verdict']}</span>"
                f" · 燈 {html.escape(json.dumps(sm['lamps'], ensure_ascii=False))}</h3>"
                f'<div style="overflow-x:auto"><table><tr><th rowspan="2">記錄(source_document)</th>{head1}</tr><tr>{head2}</tr>{body}'
                f"<tr><th>欄覆蓋(非空列數)</th>{foot}</tr></table></div>")
    return ("<!doctype html><meta charset=utf-8><title>VRN 輸出驗證矩陣</title><style>body{font:13px system-ui;margin:16px}"
            "table{border-collapse:collapse}td,th{border:1px solid #ccc;padding:3px 6px;white-space:nowrap;vertical-align:top}th{background:#f3f3f3}</style>"
            f"<h2>VRN-RECONCILE · OUTPUT VERIFY MATRIX · {html.escape(meta['ts'])} · READ-ONLY · 零落庫 · 總判 {summ['verdict']}</h2>"
            f"<p>SSOT {html.escape(meta['ssot'])} · 個股輸出冊 {html.escape(meta['out_dir'])} · 非個股矩陣 {html.escape(meta['ns_dir'])}</p>"
            + table("個股報告 · BASIC INFO + SUMMARY", mx["stock"], STOCK_COLUMNS, summ["stock"])
            + table("非個股報告 · 讀取 → 內容 → 四重點 → 證據 / 原句驗證", mx["nonstock"], NONSTOCK_COLUMNS, summ["nonstock"]))


def verify(argv: list) -> int:
    def opt(k, d=None):
        return argv[argv.index(k) + 1] if k in argv and argv.index(k) + 1 < len(argv) else d
    recs, sp = ssot_records(Path(opt("--ssot")) if opt("--ssot") else None)
    if not recs:
        print("[VRN-VERIFY] NODATA · 找不到 SSOT v2 記錄(SSOT/v2/VRN_ResearchReport_SSOT.v2.jsonl 或 generations/*.jsonl)")
        return 2
    out_dir = Path(opt("--out-dir") or VIA / "VIA_Reports" / "vrn2" / "output")
    ns_dir = Path(opt("--nonstock-dir") or VIA / "VIA_Reports" / "vrn2" / "nonstock")
    mx = build(recs, outputs(out_dir, ns_dir), coverage(Path(opt("--staging") or HERE / "staging" / "ocr_out")))
    ss, sn = summary(mx["stock"]), summary(mx["nonstock"])
    order = ["RED", "YELLOW", "NODATA", "GREEN"]
    verdict = next((v for v in order if v in (ss["verdict"], sn["verdict"])), "GREEN")
    summ = {"stock": ss, "nonstock": sn, "verdict": verdict}
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    meta = {"ts": ts, "ssot": sp.name, "out_dir": str(out_dir), "ns_dir": str(ns_dir)}
    if "--no-write" not in argv:
        od = VIA / "VIA_Reports" / "vrn_reconcile_runs"
        od.mkdir(parents=True, exist_ok=True)
        (od / f"verify_{ts}.json").write_text(json.dumps({"schema": "VIA.VRN.OutputVerifyMatrix.v2", "engine": STEM + " " + VERSION, **meta,
                                                           "summary": summ, "stock": mx["stock"], "nonstock": mx["nonstock"]},
                                                          ensure_ascii=False, indent=1), encoding="utf-8")
        for name, rows, cols in (("stock", mx["stock"], STOCK_COLUMNS), ("nonstock", mx["nonstock"], NONSTOCK_COLUMNS)):
            with open(od / f"verify_{ts}_{name}.csv", "w", encoding="utf-8-sig", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=["source_document"] + [c for _, cs in cols for c in cs], extrasaction="ignore")
                w.writeheader()
                w.writerows(rows)
        (od / f"verify_{ts}.html").write_text(render(mx, summ, meta), encoding="utf-8")
        meta["files"] = str(od / f"verify_{ts}*")
    if "--json" in argv:
        print(json.dumps({"summary": summ, **mx}, ensure_ascii=False, indent=1))
        return 1 if verdict == "RED" else 0
    print(f"VRN-RECONCILE · {ts} · READ-ONLY · 零落庫 · OUTPUT VERIFY MATRIX · 總判 {verdict}")
    print(f"[個股 · BASIC INFO + SUMMARY] 記錄 {ss['records']} · 燈 {json.dumps(ss['lamps'], ensure_ascii=False)}")
    for r in mx["stock"]:
        print(f"  {r['燈']:<6} {r['source_document'][:40]:<40} 代號 {r['代號'][:8]:<8} TICKER {r['B.TICKER'][:14]:<14} 評等 {r['B.RATING'][:12]:<12} "
              f"TP {r['B.TARGET_PRICE'][:10]:<10} 四點 {r['S.POINTS_OK']} · {r['原因'][:56]}")
    print(f"[非個股 · 讀取 → 內容 → 四重點 → 證據] 記錄 {sn['records']} · 燈 {json.dumps(sn['lamps'], ensure_ascii=False)}")
    for r in mx["nonstock"]:
        print(f"  {r['燈']:<6} {r['source_document'][:40]:<40} 類型 {r['類型'][:16]:<16} 主題 {r['N.MAIN_INDUSTRY'][:12]:<12} 驗證 {r['N.VERBATIM'][:10]:<10} · {r['原因'][:56]}")
    if meta.get("files"):
        print("存證 " + meta["files"])
    return 1 if verdict == "RED" else 0


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""), flush=True)

    print(f"=== {STEM} {VERSION} · 薄尾自測(個股 BASIC INFO + SUMMARY · 非個股新矩陣 · 合成夾具 · 不寫存證)===", flush=True)
    recs = [{"source_document": "華南投顧-6143-振曜-1141128.pdf", "final_report_type_proposal": "COMPANY_REPORT", "final_primary_ticker_proposals": "6143",
             "final_broker_proposal": "HUA_NAN"},
            {"source_document": "Daiwa-6278 20260521.pdf", "final_report_type_proposal": "COMPANY_REPORT", "final_primary_ticker_proposals": "9999",
             "final_broker_proposal": "DAIWA"},
            {"source_document": "GS-2383 20260519.pdf", "final_report_type_proposal": "COMPANY_REPORT", "final_primary_ticker_proposals": "2383"},
            {"source_document": "凱基期貨晨間解盤20251205.pdf", "final_report_type_proposal": "MARKET_DAILY", "mentioned_tickers_review_only": "2330;2317"},
            {"source_document": "MS-Memory 20251204.pdf", "final_report_type_proposal": "MEMORY"},
            {"source_document": "統一投顧-20251209投資早報.pdf", "final_report_type_proposal": "MARKET_DAILY"}]
    outs = {"BasicInfo": [{"FILENAME": "____-6143-__-1141128.pdf", "TICKER": "6143 TT", "RATING": "買進", "TARGET_PRICE": 120, "BROKER": "華南",
                           "BROKER_EN": "HUANAN", "_STATUS": {"BROKER": "VERIFIED", "RATING": "首頁評等區", "TEL": "MISSING · 不輸出"}},
                          {"FILENAME": "Daiwa-6278_20260521.pdf", "TICKER": "6278 TT", "BROKER_EN": "DAIWA", "_STATUS": {"BROKER": "VERIFIED"}}],
            "FinancialData": [{"FILENAME": "____-6143-__-1141128.pdf", "VERIFY": "對欄"}, {"FILENAME": "Daiwa-6278_20260521.pdf", "VERIFY": ""}],
            "Summary": [{"FILENAME": "____-6143-__-1141128.pdf", "POINT_1": "營收成長", "POINT_2": "毛利回升", "POINT_3": "評價", "POINT_4": "風險", "POINTS_OK": 4}],
            "Rejected": [{"FILENAME": "____-6143-__-1141128.pdf"}],
            "NonStock": [{"FILENAME": "凱基期貨晨間解盤20251205.pdf", "FILE_NAME": "凱基期貨晨間解盤20251205.pdf", "STATUS": "PASS", "MAIN_INDUSTRY": "大盤",
                          "POINT_1": "a", "POINT_2": "b", "POINT_3": "c", "VERBATIM": "3/3"},
                         {"FILENAME": "MS-Memory 20251204.pdf", "STATUS": "REVIEW"}]}
    cov = {"text": [], "table": [], "docx": set(), "fp": {}}
    mx = build(recs, outs, cov)
    st = {r["source_document"][:6]: r for r in mx["stock"]}
    ns = {r["source_document"][:6]: r for r in mx["nonstock"]}
    chk("① 個股 / 非個股分流(類型 + 主代號)3 / 3", len(mx["stock"]) == 3 and len(mx["nonstock"]) == 3)
    chk("①′ 類型空白但檔名帶 -四碼代號- 的 Memo → 個股;沒代號的不算", is_stock({"source_document": "華南投顧-4153-鈺緯-Memo-20251208.docx"})
        and not is_stock({"source_document": "投資早報251209.pdf"}))
    a = st["華南投顧-6"]
    chk("② 個股:BASIC INFO 每欄攤開(值 + 驗證態)· 中文換底線的檔名照樣對上",
        a["B.TICKER"] == "6143 TT" and a["B.RATING"].startswith("買進 [首頁") and a["B.BROKER"].startswith("華南 [VERIFIED"), a["B.RATING"])
    chk("③ 個股:SUMMARY 四點全攤開 + POINTS_OK", a["S.POINT_1"] == "營收成長" and a["S.POINTS_OK"] == "4")
    chk("④ 有拒收 / 缺漏欄 → YELLOW(不冒充綠)", a["燈"] == "YELLOW" and "拒收 1" in a["原因"] and "TEL" in a["缺漏欄"], a["原因"])
    chk("⑤ 代號對不上 / 財報值沒驗證證據 → RED", st["Daiwa-"]["燈"] == "RED", st["Daiwa-"]["原因"])
    chk("⑥ 個股但本輪沒輸出 → NODATA", st["GS-238"]["燈"] == "NODATA")
    chk("⑦ 非個股新矩陣:PASS + 重點 ≥ 3 → GREEN · 提及代號計數", ns["凱基期貨晨間"]["燈"] == "GREEN" and ns["凱基期貨晨間"]["提及代號"] == "2 檔"
        and ns["凱基期貨晨間"]["N.MAIN_INDUSTRY"] == "大盤", ns["凱基期貨晨間"]["原因"])
    chk("⑧ 非個股:REVIEW → YELLOW · 沒進摘要器 → NODATA(給下一步)", ns["MS-Mem"]["燈"] == "YELLOW" and ns["統一投顧-2"]["燈"] == "NODATA"
        and "NonStockSummarizer" in ns["統一投顧-2"]["原因"])
    ss, sn = summary(mx["stock"]), summary(mx["nonstock"])
    page = render(mx, {"stock": ss, "nonstock": sn, "verdict": "RED"}, {"ts": "t", "ssot": "s", "out_dir": "o", "ns_dir": "n"})
    chk("⑨ HTML 兩張表 · 段表頭(個股 7 段 · 非個股 7 段)· 欄覆蓋列 · 橫向捲動",
        page.count('colspan="') == len(STOCK_COLUMNS) + len(NONSTOCK_COLUMNS) and page.count("欄覆蓋") == 2 and "overflow-x:auto" in page)
    with tempfile.TemporaryDirectory() as td:
        rc = verify(["--ssot", str(Path(td) / "none.jsonl"), "--no-write"])
    chk("⑩ 找不到 SSOT → NODATA rc 2(不當掉)", rc == 2)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑪ 唯讀:不寫庫 · 不出網 · 不用 TA-Lib", not re.search(r"^\s*(?:import|from)\s+(talib|requests|urllib|duckdb|sqlite3)", src, re.M))
    rc0 = PRIOR.selftest()
    chk("⑫ 前版 v0103 自測照跑通過", rc0 == 0, f"rc {rc0}")
    n = sum(ok)
    print(f"[{'PASS' if n == len(ok) else 'FAIL'}] {STEM} {VERSION} selftest · {n}/{len(ok)}", flush=True)
    return 0 if n == len(ok) else 1


def main() -> int:
    a = sys.argv[1:]
    if a[:1] == ["--selftest"]:
        return selftest()
    if a[:1] == ["verify"]:
        return verify(a[1:])
    return PRIOR.main()


if __name__ == "__main__":
    sys.exit(main())
