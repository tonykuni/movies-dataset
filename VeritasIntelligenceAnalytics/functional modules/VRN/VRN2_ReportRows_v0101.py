#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VRN2_ReportRows v0101 — v0100 薄尾(v0100 一字不動):改成「轉接層」,不再當第三條平行路。

操作員 2026-11-10:「先前有成過 為何重工」→ 同意改法(YES)。
來源優先序(每行標 source,誠實可查):
  個股   ① VRN-2 主線冊(VIA_Reports/vrn2/output · VRN2_Summary_latest 的 POINT_1–4 + VRN2_BasicInfo_latest 的評等 / 目標價 / 收盤)
           —— 主線已經過 VerbatimVerifier / IndependentVerifier 逐值驗證,轉接層只搬、不重抽。
         ② 主線冊沒有這份 → 暫代(v0100 抽取),行上標「暫代」與原因。
  非個股 ① 操作員自己的非個股摘要器 v0310(nonstock_v0310/engine)的 RESULTS.json:topic_detail(一主題一行)·
           company_detail(晨會一家一行)· 產業報告依 topic 的 INDUSTRY 併成一產業一行。
           有 internal/NON_STOCK_CORE_v0200.py 才跑得動(hard gate);或用 --nonstock-out 指桌機已跑好的輸出夾。
         ② 缺 NON_STOCK_CORE 也沒有現成輸出 → 暫代(v0100 抽取),行上標「暫代 · 缺 NON_STOCK_CORE」。
  v0100 的擷取還原(字距 / 兩欄 / 模板殘字 / 斷行)仍用於暫代行與原句驗證。
邊界:只讀主線冊與 v0310 輸出;只寫自己的輸出夾;不改 VRN-2 主線、不改 v0310、不 import VCGC;零網路;不用 TA-Lib。
用法:python VRN2_ReportRows_v0101.py run [--pdf-dir D] [--out O] [--vrn2-books B] [--nonstock-out N] · --selftest
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

VERSION = "v0101"
ENGINE = "VRN2_ReportRows " + VERSION
HERE = Path(__file__).resolve().parent
_PRIOR = HERE / "VRN2_ReportRows_v0100.py"
_spec = importlib.util.spec_from_file_location("vrn2_reportrows_v0100_for_v0101", _PRIOR)
P = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = P
_spec.loader.exec_module(P)

VIA = P.VIA
NS_DIR = HERE / "nonstock_v0310"
NS_ENGINE = NS_DIR / "engine" / "VIA_NON_STOCK_SUMMARIZER_ENGINE_v0310.py"
NS_CORE = NS_DIR / "internal" / "NON_STOCK_CORE_v0200.py"
NS_CORE_SHA = "92f53d82c2facb41e599bf730b8be524901ed5d355aaed22a73444e85dccfa27"
DEFAULT_BOOKS = VIA / "VIA_Reports" / "vrn2" / "output"
SRC_MAIN = "VRN-2 主線"
SRC_NS = "非個股摘要器 v0310"
SRC_STANDIN = "暫代"


def norm_key(name: str) -> str:
    """檔名比對鍵:只留 ASCII 英數(主線冊的檔名把中文換成 _,原檔名有中文;兩邊都去掉後一致)。"""
    return re.sub(r"[^0-9A-Za-z]+", "", Path(str(name)).stem).lower()


def _clean_point(s) -> str:
    return re.sub(r"^[\s➢•⚫●▪■◆*\-–]+", "", str(s or "")).strip()


def _rows(path: Path) -> list:
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return d if isinstance(d, list) else (d.get("rows") or [])


class NameIndex:
    """報告身分索引(Codex #626 P1):先比完整檔名;去中文的寬鬆鍵 / (代號, 日期) 只在**唯一**候選時才用 —— 兩份只差中文的報告不會互相覆蓋。"""

    def __init__(self):
        self.exact, self.loose, self.td = {}, {}, {}

    def add(self, name: str, rec, ticker="", date=""):
        self.exact.setdefault(Path(str(name)).name, []).append(rec)
        self.loose.setdefault(norm_key(name), []).append(rec)
        if ticker and date:
            self.td.setdefault((str(ticker), str(date)), []).append(rec)

    def get(self, name: str, ticker="", date=""):
        for hits in (self.exact.get(Path(str(name)).name), self.loose.get(norm_key(name)),
                     self.td.get((str(ticker), str(date))) if ticker and date else None):
            if hits:
                return hits[0] if len(hits) == 1 else None          # 有歧義 → 不猜
        return None

    def __bool__(self):
        return bool(self.exact)


def load_main_books(books_dir) -> NameIndex:
    """VRN-2 主線冊 → NameIndex({"summary":…, "basic":…})。"""
    idx = NameIndex()
    if not books_dir:
        return idx
    b = Path(books_dir)
    basic = NameIndex()
    for r in _rows(b / "VRN2_BasicInfo_latest.json"):
        basic.add(r.get("FILENAME", ""), r)
    for r in _rows(b / "VRN2_Summary_latest.json"):
        fn = r.get("FILENAME", "")
        idx.add(fn, {"summary": r, "basic": basic.get(fn) or {}}, r.get("TICKER", ""), r.get("REPORT_DATE", ""))
    return idx


def main_points(rec: dict) -> list:
    s = (rec or {}).get("summary") or {}
    return [p for p in (_clean_point(s.get("POINT_%d" % i)) for i in range(1, 5)) if p]


def ns_core_state() -> dict:
    if not NS_CORE.is_file():
        return {"ok": False, "why": "缺 internal/NON_STOCK_CORE_v0200.py(SHA-256 %s…)" % NS_CORE_SHA[:8]}
    import hashlib
    sha = hashlib.sha256(NS_CORE.read_bytes()).hexdigest()
    return {"ok": True, "sha_match": sha == NS_CORE_SHA, "why": "NON_STOCK_CORE 在" + ("" if sha == NS_CORE_SHA else "(SHA 與 manifest 不同 · 照實記)")}


def run_nonstock(pdfs: list, outdir: Path) -> dict:
    """跑操作員自己的 v0310 引擎(不改它);回傳 RESULTS.json 內容或 {"error":…}。"""
    st = ns_core_state()
    if not st["ok"]:
        return {"error": st["why"]}
    if not pdfs:
        return {"report_summary": [], "topic_detail": [], "company_detail": []}
    outdir.mkdir(parents=True, exist_ok=True)
    cp = subprocess.run([sys.executable, str(NS_ENGINE), *map(str, pdfs), "--outdir", str(outdir)], cwd=str(NS_ENGINE.parent),
                        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=3600,
                        env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    res = load_ns_results(outdir)
    if not res.get("report_summary") and cp.returncode != 0:
        return {"error": "v0310 rc %s · %s" % (cp.returncode, (cp.stderr or cp.stdout).strip().splitlines()[-1:] or "")}
    return res


def load_ns_results(d) -> dict:
    p = Path(d) / "RESULTS.json" if d else None
    if not p or not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def ns_index(res: dict) -> NameIndex:
    """v0310 輸出 → NameIndex({"report":…, "topics":[…], "companies":[…]})(v0310 吃同一批檔,完整檔名會對上)。"""
    idx = NameIndex()
    by_id = {}
    for r in res.get("report_summary") or []:
        rec = {"report": r, "topics": [], "companies": []}
        idx.add(r.get("FILE_NAME", ""), rec)
        by_id[r.get("REPORT_ID")] = rec
    for t in res.get("topic_detail") or []:
        if t.get("REPORT_ID") in by_id:
            by_id[t["REPORT_ID"]]["topics"].append(t)
    for c in res.get("company_detail") or []:
        if c.get("REPORT_ID") in by_id:
            by_id[c["REPORT_ID"]]["companies"].append(c)
    return idx


def _pts(d: dict) -> list:
    return [p for p in (_clean_point(d.get("POINT_%d" % i)) for i in range(1, 5)) if p]


def ns_rows(base: dict, standin: list, rec: dict) -> list:
    """v0310 輸出 → 一行一單位(產業併成一產業一行;晨會一家一行;其他一主題一行)。"""
    kind = standin[0]["kind"] if standin else "topic"
    company_mode = any(r.get("ticker") for r in standin if r["kind"] == "topic")
    rows = []
    if kind == "industry":
        groups = {}
        for t in rec["topics"]:
            groups.setdefault(t.get("INDUSTRY") or t.get("STORY_L1") or "產業", []).append(t)
        for i, (ind, ts) in enumerate(groups.items(), 1):
            pts = []
            for t in ts:
                pts += [p for p in _pts(t) if p not in pts]
            rows.append(dict(base, kind="industry", row_no=i, row_key=ind, summary=pts[:4], data_rows=[], tickers=sorted({x for t in ts for x in str(t.get("TICKERS", "")).split(";") if x}),
                             pages=[], title=rec["report"].get("TITLE", "")))
    elif company_mode and rec["companies"]:
        for i, c in enumerate(rec["companies"], 1):
            rows.append(dict(base, kind="topic", row_no=i, row_key="%s(%s)" % (c.get("COMPANY_NAME") or "", c.get("TICKER", "")), ticker=c.get("TICKER", ""),
                             rating=c.get("RATING", ""), target_price=c.get("TARGET_PRICE", ""), summary=_pts(c), data_rows=[], tickers=[], pages=[],
                             title=rec["report"].get("TITLE", "")))
    else:
        for i, t in enumerate(rec["topics"], 1):
            rows.append(dict(base, kind="topic", row_no=i, row_key=t.get("TOPIC_TITLE", "") or t.get("TITLE", ""), summary=_pts(t), data_rows=[],
                             tickers=[x for x in str(t.get("TICKERS", "")).split(";") if x], pages=[], title=rec["report"].get("TITLE", "")))
    if not rows:                                                 # v0310 沒拆出單位 → 整份一行
        rows.append(dict(base, kind=kind, row_no=1, row_key=rec["report"].get("TITLE", ""), summary=_pts(rec["report"]), data_rows=[], tickers=[], pages=[]))
    return rows


def build_rows(name: str, pages: list, lane: dict, main=None, ns=None, ns_why="") -> list:
    standin = P.build_rows(name, pages, lane)
    if not standin or standin[0].get("status") == "NEEDS_OCR":
        for r in standin:
            r.update(source=SRC_STANDIN, source_note=r.get("note", ""))
        return standin
    whole = "\n".join(p.get("rtext") or p.get("text", "") for p in pages)
    base = {k: standin[0][k] for k in ("report_id", "file", "broker", "date", "pages_total", "lane_why") if k in standin[0]}
    kind = standin[0]["kind"]
    if kind == "stock":
        r0 = standin[0]
        rec = main.get(name, r0.get("ticker", ""), r0.get("date", "")) if main else None
        pts = main_points(rec)
        if pts:
            bi = rec.get("basic") or {}
            row = dict(r0, summary=pts, summary_labels=["重點 %d" % (i + 1) for i in range(len(pts))], data_rows=[],
                       rating=bi.get("RATING") or r0.get("rating", ""), target_price=str(bi.get("TARGET_PRICE") or "") or r0.get("target_price", ""),
                       close_price=str(bi.get("CURRENT_PRICE_REPORT") or "") or r0.get("close_price", ""),
                       title=(rec["summary"].get("TITLE") or r0.get("title", "")), source=SRC_MAIN,
                       source_note="主線冊 POINT_1–4 + BasicInfo(主線驗證器已逐值驗)")
            row.pop("status", None)
            P.verify_row(row, whole)
            return [row]
        for r in standin:
            r.update(source=SRC_STANDIN, source_note="VRN-2 主線冊沒有這份(或四點空)→ v0100 抽取暫代")
        return standin
    rec = ns.get(name) if ns else None
    rows = ns_rows(base, standin, rec) if rec else []
    if rows and any(r["summary"] for r in rows):                 # Codex #626 P2:上游沒抽到重點 → 不拿空行蓋掉暫代
        rows = [r for r in rows if r["summary"]]
        for i, r in enumerate(rows, 1):
            r["row_no"] = i
            r.update(kind_zh=P.KIND_ZH.get(r["kind"], r["kind"]), source=SRC_NS, source_note="v0310 RESULTS.json", key_numbers=P.key_numbers("\n".join(r["summary"])))
            P.verify_row(r, whole)
        return rows
    why = ("v0310 這份沒抽到重點(%s)" % (rec["report"].get("STATUS") or "空")) if rec else (ns_why or "v0310 輸出裡沒有這份(或檔名有歧義)")
    for r in standin:
        r.update(source=SRC_STANDIN, source_note=why + " → v0100 抽取暫代")
    return standin


COLS = ["report_id", "file", "broker", "date", "kind_zh", "row_no", "row_key", "ticker", "rating", "target_price", "close_price",
        "summary", "data_rows", "key_numbers", "tickers", "pages", "status", "verified_sentences", "summary_sentences", "source", "source_note"]


def write_outputs(rows: list, summary: dict, out: Path) -> None:
    for r in rows:                                               # HTML 的檔頭顯示來源(v0100 版面不動)
        r["lane_why"] = "%s · 來源:%s%s" % (r.get("lane_why", ""), r.get("source", ""), ("(" + r["source_note"] + ")") if r.get("source_note") else "")
    P.write_outputs(rows, summary, out)
    with (out / "VRN2_ReportRows_latest.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(COLS)
        for r in rows:
            w.writerow([" ｜ ".join(r.get(c) or []) if isinstance(r.get(c), list) and c != "pages" else
                        (",".join(map(str, r.get(c) or [])) if c == "pages" else r.get(c, "")) for c in COLS])


def run(pdf_dir: Path, out: Path, books_dir=DEFAULT_BOOKS, ns_out=None) -> dict:
    lane_m = P.lane_module()
    excl, excl_src = lane_m.load_excl(P.HERE)
    files = sorted(Path(pdf_dir).glob("*.pdf"))
    main = load_main_books(books_dir)
    loaded = []
    for f in files:
        pages = P.read_pdf(f)
        cover = " ".join((pages[0]["text"] if pages else "")[:400].split())
        loaded.append((f, pages, lane_m.classify(f.name, excl, cover)))
    ns_why = ""
    res = load_ns_results(ns_out) if ns_out else {}
    if not res:
        nonstock = [f for f, _, lane in loaded if lane.get("lane") != "stock"]
        res = run_nonstock(nonstock, out / "nonstock_v0310")
        ns_why = res.get("error", "")
    ns = ns_index(res)
    rows = []
    for f, pages, lane in loaded:
        rows.extend(build_rows(f.name, pages, lane, main, ns, ns_why))
    by_src = dict(Counter(r.get("source", "") for r in rows))
    summary = {"engine": ENGINE, "at": P._now(), "pdf_dir": str(pdf_dir), "classifier": excl_src, "reports": len(files), "rows": len(rows),
               "by_kind": dict(Counter(r["kind"] for r in rows)), "by_source": by_src, "status": dict(Counter(r["status"] for r in rows)),
               "vrn2_books": str(books_dir), "main_hits": sum(1 for r in rows if r.get("source") == SRC_MAIN), "nonstock": ns_why or "v0310 OK",
               "sentences": {"verified": sum(r.get("verified_sentences", 0) for r in rows), "total": sum(r.get("summary_sentences", 0) for r in rows)}}
    bad = (summary["status"].get("MISMATCH") or summary["status"].get("NEEDS_OCR") or summary["status"].get("EMPTY")
           or by_src.get(SRC_STANDIN))
    summary["lamp"] = "RED" if not rows else ("YELLOW" if bad else "GREEN")
    write_outputs(rows, summary, out)
    return summary


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""), flush=True)
    print("[%s selftest]" % ENGINE, flush=True)
    cp = subprocess.run([sys.executable, str(_PRIOR), "--selftest"], cwd=str(HERE), capture_output=True, text=True, encoding="utf-8",
                        errors="replace", timeout=600, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    prior_ok = cp.returncode == 0

    def pg(i, t):
        return {"page": i, "text": t, "lines": P.page_lines(t)}
    stock = [pg(1, "個股報告\n晶心科 (6533 TT) 中立(Neutral)\n前日收盤價 270.00 元\n目標價 300.00 元\n受部分案件遞延影響,3Q25 營收略低於預期。"),
             pg(2, "3Q25 營收為 4.7 億元(YoY+8.8%),毛利率維持高檔。\n公司仍維持每年營收成長 30%的長期目標。")]
    with tempfile.TemporaryDirectory() as td:
        b = Path(td)
        (b / "VRN2_Summary_latest.json").write_text(json.dumps([{"FILENAME": "___6533_N___-CTBC251208.pdf", "TICKER": "6533", "REPORT_DATE": "2025-12-08",
            "TITLE": "晶心科 案件遞延", "POINT_1": "➢ 受部分案件遞延影響,3Q25 營收略低於預期。", "POINT_2": "• 公司仍維持每年營收成長 30%的長期目標。",
            "POINT_3": "", "POINT_4": ""}], ensure_ascii=False), encoding="utf-8")
        (b / "VRN2_BasicInfo_latest.json").write_text(json.dumps([{"FILENAME": "___6533_N___-CTBC251208.pdf", "RATING": "中立",
            "TARGET_PRICE": "300", "CURRENT_PRICE_REPORT": "270"}], ensure_ascii=False), encoding="utf-8")
        main = load_main_books(b)
    chk("① 檔名鍵:主線冊的「___6533_N___-CTBC251208」對得到原檔名「晶心科(6533,N,中立)-CTBC251208」",
        norm_key("___6533_N___-CTBC251208.pdf") == norm_key("晶心科(6533,N,中立)-CTBC251208.pdf"))
    r = build_rows("晶心科(6533,N,中立)-CTBC251208.pdf", stock, {"lane": "stock", "ticker": "6533"}, main, {}, "")
    chk("② 個股:主線冊有 → 四點 / 評等 / TP / 收盤取主線(去前導符號)· 來源 = VRN-2 主線 · 原句驗證過",
        len(r) == 1 and r[0]["source"] == SRC_MAIN and r[0]["summary"][0].startswith("受部分案件") and r[0]["target_price"] == "300"
        and r[0]["close_price"] == "270" and r[0]["status"] == "VERIFIED", (r[0].get("source"), r[0].get("summary"), r[0].get("status")))
    r = build_rows("瑞基(4171,NR_未評等)-CTBC251208.pdf", stock, {"lane": "stock", "ticker": "4171"}, main, {}, "")
    chk("③ 個股:主線冊沒有 → 暫代(v0100 抽取)且行上寫明原因", r[0]["source"] == SRC_STANDIN and "主線冊沒有" in r[0]["source_note"], r[0].get("source_note"))
    ind = [pg(1, "產業專題\n半導體與散熱"), pg(2, "半導體\n半導體設備需求於 2026 年成長 15%,晶圓代工產能利用率提升。"),
           pg(3, "散熱\n散熱水冷滲透率將由 10% 提升至 35%,奇鋐(3017)受惠。")]
    res = {"report_summary": [{"REPORT_ID": "RPT-1", "FILE_NAME": "兆豐產業專題-半導體與散熱.pdf", "TITLE": "半導體與散熱"}],
           "topic_detail": [{"REPORT_ID": "RPT-1", "TOPIC_TITLE": "半導體", "INDUSTRY": "半導體", "POINT_1": "半導體設備需求於 2026 年成長 15%,晶圓代工產能利用率提升。"},
                            {"REPORT_ID": "RPT-1", "TOPIC_TITLE": "散熱", "INDUSTRY": "散熱", "POINT_1": "散熱水冷滲透率將由 10% 提升至 35%,奇鋐(3017)受惠。", "TICKERS": "3017"}],
           "company_detail": []}
    r = build_rows("兆豐產業專題-半導體與散熱.pdf", ind, {"lane": "non_stock"}, {}, ns_index(res), "")
    chk("④ 產業:v0310 有輸出 → 依 INDUSTRY 一產業一行 · 來源 = 非個股摘要器 v0310 · 原句驗證過",
        [x["row_key"] for x in r] == ["半導體", "散熱"] and all(x["source"] == SRC_NS and x["status"] == "VERIFIED" for x in r), [(x["row_key"], x["source"], x["status"]) for x in r])
    morn = [pg(1, "晨會報告\n目錄"), pg(2, "公司名稱 振大環球(4441)\n振大環球營收年增 12%,新產能下半年開出。\n公司名稱 美時(1795)\n美時新藥授權收入成長 20%,維持區間操作。")]
    res2 = {"report_summary": [{"REPORT_ID": "RPT-2", "FILE_NAME": "20251205兆豐晨會報告(二).pdf"}], "topic_detail": [],
            "company_detail": [{"REPORT_ID": "RPT-2", "TICKER": "4441", "COMPANY_NAME": "振大環球", "RATING": "買進", "TARGET_PRICE": "424", "POINT_1": "振大環球營收年增 12%,新產能下半年開出。"},
                               {"REPORT_ID": "RPT-2", "TICKER": "1795", "COMPANY_NAME": "美時", "RATING": "區間操作", "TARGET_PRICE": "330", "POINT_1": "美時新藥授權收入成長 20%,維持區間操作。"}]}
    r = build_rows("20251205兆豐晨會報告(二).pdf", morn, {"lane": "non_stock"}, {}, ns_index(res2), "")
    chk("⑤ 晨會:v0310 company_detail → 一家公司一行(評等 / TP 照 v0310)", [x["row_key"] for x in r] == ["振大環球(4441)", "美時(1795)"] and r[0]["target_price"] == "424"
        and all(x["source"] == SRC_NS for x in r), [(x["row_key"], x.get("target_price")) for x in r])
    r = build_rows("兆豐產業專題-半導體與散熱.pdf", ind, {"lane": "non_stock"}, {}, {}, "缺 internal/NON_STOCK_CORE_v0200.py")
    chk("⑥ 非個股:v0310 跑不動(缺 NON_STOCK_CORE)→ 暫代且寫明原因", all(x["source"] == SRC_STANDIN and "NON_STOCK_CORE" in x["source_note"] for x in r))
    res3 = {"report_summary": [{"REPORT_ID": "RPT-3", "FILE_NAME": "兆豐產業專題-半導體與散熱.pdf"}],
            "topic_detail": [{"REPORT_ID": "RPT-3", "TOPIC_TITLE": "半導體", "INDUSTRY": "半導體", "POINT_1": "這句 v0310 改寫過,原文沒有。"}], "company_detail": []}
    r = build_rows("兆豐產業專題-半導體與散熱.pdf", ind, {"lane": "non_stock"}, {}, ns_index(res3), "")
    chk("⑦ v0310 的點若不是原句 → MISMATCH 照實(轉接層不替它背書)", r[0]["status"] == "MISMATCH", r[0]["status"])
    with tempfile.TemporaryDirectory() as td:
        write_outputs(r, {"engine": ENGINE, "at": P._now(), "reports": 1, "rows": len(r), "by_kind": {}, "lamp": "YELLOW",
                          "sentences": {"verified": 0, "total": 1}}, Path(td))
        head = (Path(td) / "VRN2_ReportRows_latest.csv").read_text(encoding="utf-8-sig").splitlines()[0]
        page = (Path(td) / "VRN2_ReportRows_latest.html").read_text(encoding="utf-8")
    chk("⑧ 輸出帶來源:CSV 有 source / source_note 欄 · HTML 檔頭寫「來源:…」", head.endswith("source,source_note") and "來源:" + SRC_NS in page, head[-30:])
    src = Path(__file__).read_text(encoding="utf-8")
    two = {"report_summary": [{"REPORT_ID": "A", "FILE_NAME": "20260916兆豐台灣產業專題-航太產業.pdf"},
                              {"REPORT_ID": "B", "FILE_NAME": "20260916兆豐台灣產業專題-半導體產業.pdf"}],
           "topic_detail": [{"REPORT_ID": "A", "TOPIC_TITLE": "航太", "INDUSTRY": "航太", "POINT_1": "航太訂單能見度高,2026 年營收成長 20%。"},
                            {"REPORT_ID": "B", "TOPIC_TITLE": "半導體", "INDUSTRY": "半導體", "POINT_1": "半導體設備需求於 2026 年成長 15%,晶圓代工產能利用率提升。"}],
           "company_detail": []}
    i2 = ns_index(two)
    chk("⑦b 只差中文的兩份報告(去中文後同鍵)各自對到自己的 v0310 結果,寬鬆鍵有歧義時不猜(Codex #626 P1)",
        i2.get("20260916兆豐台灣產業專題-航太產業.pdf")["report"]["REPORT_ID"] == "A" and i2.get("20260916兆豐台灣產業專題-半導體產業.pdf")["report"]["REPORT_ID"] == "B"
        and i2.get("20260916兆豐台灣產業專題-其他.pdf") is None)
    empty = {"report_summary": [{"REPORT_ID": "E", "FILE_NAME": "兆豐產業專題-半導體與散熱.pdf", "STATUS": "REVIEW"}], "topic_detail": [], "company_detail": []}
    r = build_rows("兆豐產業專題-半導體與散熱.pdf", ind, {"lane": "non_stock"}, {}, ns_index(empty), "")
    chk("⑦c v0310 有這份但沒抽到重點 → 保留暫代(不拿空行冒充綠)· 原因寫 REVIEW(Codex #626 P2)",
        r and all(x["source"] == SRC_STANDIN and "REVIEW" in x["source_note"] and x["summary"] for x in r), [(x["source"], x.get("source_note")) for x in r])
    chk("⑨ 不用 TA-Lib · 不 import VCGC · 零網路", not re.search(r"^\s*(?:import|from)\s+(talib|CGC_|requests|urllib)", src, re.M | re.I))
    chk("⑩ 前版 v0100 自測(乾淨子行程)", prior_ok, "rc %s" % cp.returncode)
    n = sum(ok)
    print("[%s] %s selftest · %d/%d" % ("PASS" if n == len(ok) else "FAIL", ENGINE, n, len(ok)), flush=True)
    return 0 if n == len(ok) else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=ENGINE)
    ap.add_argument("verb", nargs="?", default="run", choices=["run", "selftest"])
    ap.add_argument("--pdf-dir", default=str(VIA / P.FIXTURE_REL))
    ap.add_argument("--out", default=str(VIA / "VIA_Reports" / "vrn2" / "report_rows"))
    ap.add_argument("--vrn2-books", default=str(DEFAULT_BOOKS), help="VRN-2 主線輸出冊夾(VRN2_Summary_latest.json / VRN2_BasicInfo_latest.json)")
    ap.add_argument("--nonstock-out", default="", help="v0310 已跑好的輸出夾(含 RESULTS.json);不給就在有 NON_STOCK_CORE 時當場跑")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest or a.verb == "selftest":
        return selftest()
    s = run(Path(a.pdf_dir), Path(a.out), a.vrn2_books, a.nonstock_out or None)
    print("[%s] %s · 報告 %d · 行 %d · 來源 %s · 主線命中 %d · 非個股 %s · 原句驗證 %d/%d · 狀態 %s → %s" % (
        s["lamp"], ENGINE, s["reports"], s["rows"], json.dumps(s["by_source"], ensure_ascii=False), s["main_hits"], s["nonstock"],
        s["sentences"]["verified"], s["sentences"]["total"], json.dumps(s["status"], ensure_ascii=False), Path(a.out) / "VRN2_ReportRows_latest.html"), flush=True)
    return 0 if s["lamp"] != "RED" else 2


if __name__ == "__main__":
    sys.exit(main())
