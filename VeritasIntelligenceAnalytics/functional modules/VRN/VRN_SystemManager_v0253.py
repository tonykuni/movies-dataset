#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN-2 SystemManager v0253 — 薄尾(前版 = v0249 · 跳過另一線 v0250 / v0251 · v0252 未落地即併入本版)。輸出冊逐欄空格稽核與補位(操作員 2026-10-28:「全部檢視空格逐一檢視」)。

① 分析師回填:v0245 在驗收時抓到的「研究員:邱岳霖」只進驗收狀態(acc.basic.analysts)· 從未寫進基本資料冊 ANALYST → 本版回填 + STATUS 記 ANALYST:首頁標籤
② 年度數據冊 V2 欄位恆在:VDF 年度實際未就緒時也補 VALUE_FINAL(= VALUE_NUM)· VALUE_SOURCE「報告值 · 未核對」· STATUS 末欄(誠實標未核對 · 不留空)
③ 摘要冊 STATUS 不留空:POINTS n/4 · TITLE 原文 / 後援 · POINT_SOURCE · UPSIDE_ADJ ok / 缺市場資料
④ 正式英文 CSV 嚴格 39 欄(v0248 寫出 51 欄:把程式鍵 English Name / Tel / Roe Avg Equity … 一併匯出)· 程式冊鍵名不變
⑥ 輸出冊缺項全數攤開:完成判定面板「缺項 56 份」貼包只印前 8 筆 → 本版依原因分組(年度數據 / 四點原文證據 / TITLE …)全數進貼包與稽核冊
⑤ 空格稽核冊 VRN2_BlankAudit_latest.{json,md,html}:三冊每欄空格數 + 每格原因分類(市場未就緒 / 報告本無 Note·NR / 首頁未抓到 / 年度數據未抓到 / 未核對)· 一行進貼包 · 面板加連結
不改 v0249 / 另一線任何函式 · 發布層在本版補位之後才跑(累計冊拿到補位後的資料)。
"""
from __future__ import annotations

import csv
import hashlib
import html as _html
import importlib.util
import inspect
import json
import re
import subprocess
import sys
import types
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAG = "v0253"
DISPLAY_NAME = "VRN-2 SystemManager"
PRIOR_NAME = "VRN_SystemManager_v0249.py"
PRIOR_PATH = HERE / PRIOR_NAME
if not PRIOR_PATH.exists():
    raise FileNotFoundError("前版 %s 不在 · v0253 不接" % PRIOR_NAME)
_spec = importlib.util.spec_from_file_location("vrn_manager_prior_for_v0253", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
for _name, _value in vars(PRIOR).items():
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = _value


def _rebind(fn):
    return types.FunctionType(fn.__code__, globals(), fn.__name__, fn.__defaults__, fn.__closure__)


_NOTE_RX = re.compile(r"(?i)\bNote\b|\bNR\b|未評等|Not rated|Takeaway|法說|座談|速報|介紹報告|Memo|Flash")
_MKT_KEYS = ("ADJ_CLOSE", "ADJ_CLOSE_BEFORE_REPORT", "TARGET_PRICE(ADJ)", "UPSIDE_ADJ", "CURRENT_PRICE_REPORT", "ADJ_CLOSE_DATE", "ADJ_CLOSE_BEFORE_REPORT_DATE", "UPSIDE_PCT(ADJ)")
_YEAR_KEYS = tuple("%s_Y%d" % (k, i) for k in ("DILUTED_EPS", "DPS", "BVPS", "ROE", "PER", "PBR", "CASH_YIELD") for i in range(3))
_P1_KEYS = ("RATING", "TARGET_PRICE", "ANALYST", "EMAIL", "TEL", "ENGLISH_NAME")


def _blank(v) -> bool:
    return v is None or (isinstance(v, str) and not v.strip()) or (isinstance(v, float) and v != v)


def _status_append(row: dict, token: str) -> None:
    st = str(row.pop("STATUS", "") or "")
    row["STATUS"] = (st + " · " if st else "") + token


def _fill_analyst(basic: list, acc) -> int:
    """① 驗收狀態裡的分析師(首頁標籤)回填 ANALYST。"""
    lab = {}
    for e in (acc or []):
        if isinstance(e, dict):
            b = e.get("basic") or {}
            if b.get("analysts"):
                lab[Path(str(e.get("file") or "")).name] = (list(b["analysts"]), b.get("analyst_src") or "")
    n = 0
    for row in basic:
        if _blank(row.get("ANALYST")):
            names, src = lab.get(Path(str(row.get("FILENAME") or "")).name, (None, ""))
            if names:
                row["ANALYST"] = "、".join(str(x) for x in names)
                _status_append(row, "ANALYST:首頁標籤(%s)" % (src or "研究員 / 分析師"))
                n += 1
    return n


def _fin_v2_shape(fin: list) -> int:
    """② 年度數據冊每列都有 VALUE_FINAL / VALUE_SOURCE / STATUS(末欄)。"""
    n = 0
    for row in fin:
        if "VALUE_FINAL" not in row:
            row["VALUE_FINAL"] = row.get("VALUE_NUM")
            row["VALUE_SOURCE"] = "報告值 · 未核對(VDF 年度實際未就緒)"
            n += 1
        st = row.pop("STATUS", "")
        if isinstance(st, dict):
            st = " · ".join("%s:%s" % (k, v) for k, v in st.items())
        if not st:
            st = "RECON:未核對(市場財報未就緒)" if "未核對" in str(row.get("VALUE_SOURCE") or "") else "RECON:%s" % ("通過" if "通過" in str(row.get("VALUE_SOURCE") or "") else "見 VALUE_SOURCE")
        row["STATUS"] = st
    return n


def _summ_status(summ: list) -> int:
    """③ 摘要冊 STATUS 不留空。"""
    n = 0
    for row in summ:
        st = str(row.pop("STATUS", "") or "")
        if isinstance(st, dict):
            st = " · ".join("%s:%s" % (k, v) for k, v in st.items())
        pts = sum(1 for i in range(1, 5) if not _blank(row.get("POINT_%d" % i)))
        tok = ["POINTS:%d/4" % pts, "TITLE:%s" % ("原文" if not _blank(row.get("TITLE_ORIGINAL")) else ("後援" if not _blank(row.get("TITLE")) else "缺")),
               "POINT_SOURCE:%s" % (row.get("POINT_SOURCE") or "原文"), "UPSIDE_ADJ:%s" % ("ok" if not _blank(row.get("UPSIDE_ADJ")) else "缺市場資料")]
        row["STATUS"] = (st + " · " if st else "") + " · ".join(tok)
        n += 1
    return n


def _write_formal_csv_39(od: Path, basic: list) -> int:
    """④ 正式英文 CSV 嚴格 39 欄(HEADERS_V3 順序)· 程式冊不變。"""
    hv = globals().get("HEADERS_V3") or []
    keys = [k for k, _, _ in hv]
    en = {k: e for k, e, _ in hv}
    if not keys:
        return 0
    with (od / "VRN2_BasicInfo_latest_formal.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh); w.writerow([en[k] for k in keys])
        for r in basic:
            w.writerow([r.get(k, "") if not isinstance(r.get(k), (dict, list)) else json.dumps(r.get(k), ensure_ascii=False) for k in keys])
    return len(keys)


def _reason(key: str, row: dict, market_ok: bool) -> str:
    fn = str(row.get("FILENAME") or "")
    note = bool(_NOTE_RX.search(fn)) or str(row.get("RATING") or "").upper() in ("NR", "N/A", "NOTE")
    if key in _MKT_KEYS:
        return "市場資料未就緒(⑥e)" if not market_ok else ("報告無目標價 · 無法算調整後" if key in ("TARGET_PRICE(ADJ)", "UPSIDE_ADJ", "UPSIDE_PCT(ADJ)") and _blank(row.get("TARGET_PRICE")) else "市場資料部分缺(價格 / 還原因子)")
    if key in ("RATING", "TARGET_PRICE"):
        return "報告本無(Note / NR / 速報)" if note else "首頁未抓到(ENG397)"
    if key in ("ANALYST", "EMAIL", "TEL", "ENGLISH_NAME"):
        return "首頁無此欄(報告未印)" if note else "首頁未抓到(雙讀 / 標籤)"
    if key.startswith(("DILUTED_EPS", "BVPS", "DPS")):
        return "報告本無年度表(Note / NR)" if note else "年度數據未抓到(ENG397 財報頁)"
    if key.startswith(("ROE", "PER", "PBR", "CASH_YIELD")):
        if _blank(row.get("DILUTED_EPS_Y0")) and key.startswith("PER"):
            return "無 EPS 可算"
        if key.startswith(("PBR", "CASH_YIELD")) and _blank(row.get("BVPS_Y0" if key.startswith("PBR") else "DPS_Y0")):
            return "無 BVPS / DPS 可算"
        return "市場資料未就緒(⑥e)" if not market_ok else "報告未揭露"
    if key in ("ROE_AVG_EQUITY", "ROE_YEAR", "PER_DILUTED_ADJ", "PER_YEAR"):
        return "V2 註記欄(市場 / 財報就緒後才填)"
    if key in ("UPSIDE_PCT",):
        return "報告無目標價 / 報告股價 · 無法算" if _blank(row.get("TARGET_PRICE")) or _blank(row.get("CURRENT_PRICE_REPORT")) else "未分類"
    if key in ("NAME", "YFINANCE_TICKER", "BLOOMBERG_TICKER"):
        return "代號不在上市櫃名冊(外國股 / 新股)"
    if key == "TITLE":
        return "摘要器未抓到(ENG062)"
    return "未分類"


def blank_audit(basic: list, fin: list, summ: list, market: dict, od: Path, gaps: list = None) -> tuple:
    """⑤ 三冊逐欄空格稽核 → JSON / MD / HTML · 回 (一行摘要, 空格總數)。"""
    pf = (market or {}).get("per_file") or {}
    cols = {}
    cells = []
    for row in basic:
        mk = pf.get(Path(str(row.get("FILENAME") or "")).name) or pf.get(str(row.get("FILENAME") or ""))
        market_ok = bool(mk and mk.get("adj_close") is not None)
        for k, v in row.items():
            if k.startswith("_") or k == "STATUS":
                continue
            if _blank(v):
                r = _reason(k, row, market_ok)
                cols.setdefault(("BasicInfo", k), Counter())[r] += 1
                cells.append({"book": "BasicInfo", "file": row.get("FILENAME"), "key": k, "reason": r})
    for row in summ:
        for k in ("TITLE", "POINT_1", "POINT_2", "POINT_3", "POINT_4", "UPSIDE_ADJ"):
            if _blank(row.get(k)):
                r = "市場資料未就緒(⑥e)" if k == "UPSIDE_ADJ" else ("摘要器未抓到(ENG062)" if k == "TITLE" else "本文重點不足(已平均取仍缺)")
                cols.setdefault(("Summary", k), Counter())[r] += 1
                cells.append({"book": "Summary", "file": row.get("FILENAME"), "key": k, "reason": r})
    fin_tot = len(fin)
    fin_blank = {k: sum(1 for r in fin if _blank(r.get(k))) for k in ("PERIOD_STD", "VALUE_NUM", "UNIT", "VALUE_FINAL")}
    fin_unrec = sum(1 for r in fin if "未核對" in str(r.get("VALUE_SOURCE") or ""))
    by_reason = Counter(c["reason"] for c in cells)
    gap_by = Counter(str(g).split(":", 1)[1].strip() if ":" in str(g) else str(g) for g in (gaps or []))   # ⑥ 管理器缺項依原因分組
    gap_files = {}
    for g in (gaps or []):
        f_, _, r_ = str(g).partition(":")
        gap_files.setdefault(r_.strip() or "缺項", []).append(f_.strip())
    rep = {"outbook_gaps": len(gaps or []), "outbook_gap_by_reason": dict(gap_by), "outbook_gap_files": gap_files, "basic_rows": len(basic), "summary_rows": len(summ), "fin_rows": fin_tot, "fin_blank": fin_blank, "fin_unreconciled": fin_unrec,
           "columns": [{"book": b, "key": k, "blank": sum(c.values()), "reasons": dict(c)} for (b, k), c in sorted(cols.items(), key=lambda x: -sum(x[1].values()))],
           "by_reason": dict(by_reason), "cells": cells}
    try:
        (od / "VRN2_BlankAudit_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
        md = ["# VRN-2 空格稽核 · 基本資料 %d 份 · 摘要 %d 份 · 年度數據 %d 列" % (len(basic), len(summ), fin_tot), "",
              "## 輸出冊缺項(完成判定面板的數字 · 全數)", ""] + ["- %s:%d 份 → %s" % (r, len(fs), "、".join(x[:28] for x in fs[:12]) + ("…" if len(fs) > 12 else "")) for r, fs in sorted(gap_files.items(), key=lambda x: -len(x[1]))] + ["",
              "## 原因總表", ""] + ["- %s:%d 格" % (r, n) for r, n in by_reason.most_common()] + ["", "## 年度數據冊", "",
              "- 未核對(VDF 年度實際未就緒)%d / %d 列 · PERIOD_STD 空 %d · VALUE_NUM 空 %d · UNIT 空 %d" % (fin_unrec, fin_tot, fin_blank["PERIOD_STD"], fin_blank["VALUE_NUM"], fin_blank["UNIT"]),
              "", "## 每欄", "", "| 冊 | 欄 | 空格 | 原因 |", "|---|---|---|---|"] + ["| %s | %s | %d | %s |" % (c["book"], c["key"], c["blank"], " · ".join("%s %d" % (r, n) for r, n in c["reasons"].items())) for c in rep["columns"]]
        (od / "VRN2_BlankAudit_latest.md").write_text("\n".join(md) + "\n", encoding="utf-8")
        C = {"GREEN": "#16a34a", "YELLOW": "#eab308", "RED": "#dc2626", "GRAY": "#9ca3af"}
        def lamp(r):
            return "GRAY" if "報告本無" in r or "首頁無此欄" in r or "V2 註記" in r else ("YELLOW" if "未就緒" in r or "未核對" in r or "部分缺" in r else "RED")
        rows = "".join("<tr><td><span class='lp' style='background:%s'></span></td><td>%s</td><td>%s</td><td>%d</td><td>%s</td></tr>" % (C[lamp(max(c["reasons"], key=c["reasons"].get))], c["book"], _html.escape(c["key"]), c["blank"], _html.escape(" · ".join("%s %d" % (r, n) for r, n in c["reasons"].items()))) for c in rep["columns"])
        page = ("<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>VRN-2 空格稽核</title>"
                "<style>body{font:12px/1.45 'Segoe UI','Microsoft JhengHei',sans-serif;margin:0;padding:12px;color:#1f2937;background:#f8fafc}h1{font-size:15px;margin:0 0 6px}table{border-collapse:collapse;width:100%%;background:#fff;font-size:11.5px}th,td{border:1px solid #e2e8f0;padding:3px 6px;text-align:left;vertical-align:top}th{background:#f1f5f9}td:first-child,th:first-child{width:24px;text-align:center}.lp{display:inline-block;width:11px;height:11px;border-radius:50%%}</style></head><body>"
                "<h1>VRN-2 空格稽核 · 基本資料 %d 份 · 摘要 %d 份 · 年度數據 %d 列(未核對 %d)</h1><div>灰 = 報告本來就沒有(不算缺)· 黃 = 等市場 / 財報資料 · 紅 = 擷取缺口(下一輪引擎)</div>"
                "<h2 style='font-size:13px;margin:10px 0 4px'>輸出冊缺項 %d(完成判定面板數字 · 全數攤開)</h2><table><tr><th>燈</th><th>原因</th><th>份數</th><th>檔案</th></tr>%s</table>"
                "<h2 style='font-size:13px;margin:10px 0 4px'>每欄空格</h2><table><tr><th>燈</th><th>冊</th><th>欄</th><th>空格</th><th>原因</th></tr>%s</table></body></html>") % (len(basic), len(summ), fin_tot, fin_unrec, len(gaps or []),
                "".join("<tr><td><span class='lp' style='background:%s'></span></td><td>%s</td><td>%d</td><td>%s</td></tr>" % (C["RED"] if "年度數據" in r or "TITLE" in r else C["YELLOW"], _html.escape(r), len(fs), _html.escape("、".join(x[:30] for x in fs))) for r, fs in sorted(gap_files.items(), key=lambda x: -len(x[1]))), rows)
        (od / "VRN2_BlankAudit_latest.html").write_text(page, encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    top = " · ".join("%s %d" % (r, n) for r, n in by_reason.most_common(4))
    gtop = " · ".join("%s %d" % (r, n) for r, n in gap_by.most_common(6))
    return ("空格稽核 · 輸出冊缺項 %d(%s)· 基本資料空格 %d(%s)· 摘要空格 %d · 年度數據未核對 %d/%d → output/VRN2_BlankAudit_latest.html" % (len(gaps or []), gtop or "無", sum(1 for c in cells if c["book"] == "BasicInfo"), top, sum(1 for c in cells if c["book"] == "Summary"), fin_unrec, fin_tot), len(cells))


def _out_books(res, acc, st, v2):
    basic, fin, summ, gaps, made = PRIOR.PRIOR._out_books(res, acc, st, v2)   # v0248 以前(含 V2 / V3)· 發布層改在本版補位後跑
    try:
        od = Path(v2) / "output"
        market = {}
        try:
            market = json.loads((Path(v2) / "market" / "VRN2_Market_latest.json").read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            pass
        na = _fill_analyst(basic, acc)
        nf = _fin_v2_shape(fin)
        ns = _summ_status(summ)
        _rewrite_book(od, "BasicInfo", basic); _rewrite_book(od, "FinancialData", fin); _rewrite_book(od, "Summary", summ)
        nc = _write_formal_csv_39(od, basic)
        line, _ = blank_audit(basic, fin, summ, market, od, gaps)
        print("  [計] v0253 補位:分析師回填 %d · 年度數據 V2 欄位補 %d 列 · 摘要 STATUS %d · 正式 CSV %d 欄" % (na, nf, ns, nc), flush=True)
        print("  [計] v0253 " + line, flush=True)
    except Exception as exc:  # noqa: BLE001
        print("  [計] v0253 補位未完成 %s %s" % (type(exc).__name__, str(exc)[:80]), flush=True)
    try:                                                                       # 發布層(同 v0249)· 補位之後才跑
        eng = _pub_engine()
        if eng:
            r = subprocess.run([sys.executable, "-W", "ignore", str(eng), "--publish", "--v2", str(v2)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800, cwd=str(HERE))
            line = next((l for l in (r.stdout + r.stderr).splitlines() if l.strip().startswith("[計] 發布")), "")
            print("  " + (line.strip() if line else "[計] 發布未回報 rc %d" % r.returncode)[:400], flush=True)
        else:
            print("  [計] 發布引擎未落地(VRN2_Publish_v####.py)", flush=True)
    except Exception as exc:  # noqa: BLE001
        print("  [計] 發布未完成 %s" % type(exc).__name__, flush=True)
    return basic, fin, summ, gaps, made


def _ui_panel_html(v2):
    h = PRIOR._ui_panel_html(v2)
    try:
        p = Path(v2) / "output" / "VRN2_BlankAudit_latest.html"
        link = "<div style='margin:8px 0;padding:6px 8px;border:1px solid #e2e8f0;border-radius:6px;background:#fff'><b>空格稽核</b> · <a href='%s' target='_blank'>VRN2_BlankAudit_latest.html</a>(每欄空格與原因 · 灰 = 報告本無 · 黃 = 等資料 · 紅 = 擷取缺口)</div>" % _html.escape(p.as_uri() if p.exists() else "#")
        return (h or "") + link
    except Exception:  # noqa: BLE001
        return h


def completion(*args, **kwargs):
    result = PRIOR.completion(*args, **kwargs)
    try:
        result["manager"] = "%s %s" % (DISPLAY_NAME, TAG)
    except Exception:  # noqa: BLE001
        pass
    return result


_MY_SIG = hashlib.sha1(inspect.getsource(blank_audit).encode("utf-8")).hexdigest()[:12]
for _n in ("_base_acceptance", "_acc_parallel", "_acc_shard_main", "_acc_one", "_acc_one_core", "_acc_basic", "acceptance", "_acc_sig", "_native_vrn2", "vrn2", "_idem_check", "main", "_success_register", "_out_html"):
    globals()[_n] = _rebind(getattr(PRIOR, _n))


def selftest() -> int:
    ok = [0, 0]
    def chk(name, cond):
        ok[0 if cond else 1] += 1
        print("  [%s] %s" % ("OK" if cond else "FAIL", name))
    import tempfile
    acc = [{"file": "C:/x/20250819兆豐個股報告-泓德能源(6873).pdf", "basic": {"analysts": ["邱岳霖"], "analyst_src": "首頁標籤(研究員 / 分析師)"}}]
    basic = [{"FILENAME": "20250819兆豐個股報告-泓德能源(6873).pdf", "TICKER": "6873", "ANALYST": "", "RATING": "逢低買進", "TARGET_PRICE": 208, "DILUTED_EPS_Y0": 13, "STATUS": "EMAIL:MISSING"},
             {"FILENAME": "MQ-1560 20260520.pdf", "TICKER": "1560", "ANALYST": "", "RATING": "", "TARGET_PRICE": "", "DILUTED_EPS_Y0": "", "ADJ_CLOSE": "", "STATUS": ""},
             {"FILENAME": "光焱(7728,Note)-CTBC260918.pdf", "TICKER": "7728", "ANALYST": "", "RATING": "", "TARGET_PRICE": "", "DILUTED_EPS_Y0": "", "ADJ_CLOSE": "", "STATUS": ""}]
    na = _fill_analyst(basic, acc)
    chk("① 分析師回填 %d · %s · STATUS 末欄 %s" % (na, basic[0]["ANALYST"], list(basic[0].keys())[-1]), na == 1 and basic[0]["ANALYST"] == "邱岳霖" and list(basic[0].keys())[-1] == "STATUS" and "ANALYST:首頁標籤" in basic[0]["STATUS"])
    fin = [{"FILENAME": "x.pdf", "ITEM": "營收", "PERIOD_STD": "2024", "VALUE_NUM": 1.0}, {"FILENAME": "x.pdf", "ITEM": "營收", "PERIOD_STD": "2025", "VALUE_NUM": 2.0, "VALUE_FINAL": 2.5, "VALUE_SOURCE": "實際蓋過預估", "STATUS": ""}]
    nf = _fin_v2_shape(fin)
    chk("② 年度數據 V2 欄位 %d 列補 · 末欄 %s / %s · 未核對 %s" % (nf, list(fin[0].keys())[-1], list(fin[1].keys())[-1], fin[0]["STATUS"]), nf == 1 and fin[0]["VALUE_FINAL"] == 1.0 and list(fin[0].keys())[-1] == "STATUS" and "未核對" in fin[0]["STATUS"] and fin[1]["VALUE_FINAL"] == 2.5)
    summ = [{"FILENAME": "x.pdf", "TITLE": "t", "TITLE_ORIGINAL": "t", "POINT_1": "a", "POINT_2": "b", "POINT_3": "", "POINT_4": "", "UPSIDE_ADJ": ""}]
    _summ_status(summ)
    chk("③ 摘要 STATUS %s" % summ[0]["STATUS"], "POINTS:2/4" in summ[0]["STATUS"] and "缺市場資料" in summ[0]["STATUS"])
    od = Path(tempfile.mkdtemp())
    nc = _write_formal_csv_39(od, basic)
    hdr = (od / "VRN2_BasicInfo_latest_formal.csv").read_text(encoding="utf-8-sig").splitlines()[0].split(",")
    chk("④ 正式 CSV %d 欄 · 首欄 %s · 倒二 %s · 末 %s" % (nc, hdr[0], hdr[-2], hdr[-1]), nc == 39 and len(hdr) == 39 and hdr[-1] == "Status" and hdr[-2] == "Recent Report and Pre Earnings Flag")
    line, n = blank_audit(basic, fin, summ, {"per_file": {}}, od, ["MQ-1560 20260520.pdf:TITLE", "Daiwa-6278 20260521.pdf:年度數據", "欣銓.pdf:年度數據"])
    rep = json.loads((od / "VRN2_BlankAudit_latest.json").read_text(encoding="utf-8"))
    chk("⑤ 空格稽核 %d 格 · 原因 %s · HTML %s" % (n, sorted(rep["by_reason"])[:3], (od / "VRN2_BlankAudit_latest.html").exists()), n > 0 and "報告本無(Note / NR / 速報)" in rep["by_reason"] and "市場資料未就緒(⑥e)" in rep["by_reason"] and (od / "VRN2_BlankAudit_latest.html").exists())
    chk("⑥ 輸出冊缺項全數分組 %s · 貼包 %s" % (rep["outbook_gap_by_reason"], line[:40]), rep["outbook_gap_by_reason"] == {"TITLE": 1, "年度數據": 2} and "輸出冊缺項 3(年度數據 2 · TITLE 1)" in line)
    chk("⓪ v0253 綁定:vrn2 內部 _out_books / _ui_panel_html / completion 走本版", _native_vrn2.__globals__["_out_books"] is _out_books and _native_vrn2.__globals__["_ui_panel_html"] is _ui_panel_html and _native_vrn2.__globals__["completion"] is completion)
    import os
    if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") != "1":
        print("          ── 前版鏈(v0249)自測 ──")
        rc = PRIOR.selftest()
        chk("⑥ 前版鏈 v0249 自測 rc %s" % rc, rc == 0)
    p, f = ok
    print("[計] VRN-2 SystemManager v0253(VRN_SystemManager_v0253.py)自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(main(sys.argv[1:]))
