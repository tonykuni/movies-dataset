#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN-2 SystemManager v0248 — 薄尾(前版 = v0247)。基本資料冊 Headers V3(操作員 2026-10-27)。

① 欄序固定:Report Date … Adjusted Close Before Report · Topic and Summary · 7 項 × 三年(Diluted EPS / DPS / BVPS / ROE / PER / PBR / Cash Yield · Year N = 報告年)·
   Recent Report and Pre Earnings Flag(倒數第二欄)· Status(最末欄)· 其餘既有欄位保留在中段後(只增不減)
② 三年數值來源:年度數據冊(已經 v0247 一期核對 · VALUE_FINAL = 實際蓋過預估)· PER / PBR / Cash Yield 用最新還原收盤重算 · ROE 優先 NI / 平均權益 · 全部純小數
③ 近期標註:Report Date 距今 ≤ 2 個月 → RECENT · 法定財報期限(Q1 5/15 · Q2 8/14 · Q3 11/14 · 年報 3/31)→ 報告日在最近一個已結束期間的公告期限之前 / 之後
④ 表頭對照冊 SSOT/VRN2_BasicInfo_Headers_v0100.json(程式鍵 → Formal English Title Case → 中文)· 另出 VRN2_BasicInfo_latest_formal.csv(正式英文表頭 · R-HDR-01)· 既有 JSON / CSV / Parquet 鍵名不變
不改 v0247 / 另一線任何函式。
"""
from __future__ import annotations

import csv
import datetime as _dt
import hashlib
import importlib.util
import inspect
import json
import re
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAG = "v0248"
DISPLAY_NAME = "VRN-2 SystemManager"
PRIOR_NAME = "VRN_SystemManager_v0247.py"
PRIOR_PATH = HERE / PRIOR_NAME
if not PRIOR_PATH.exists():
    raise FileNotFoundError("前版 %s 不在 · v0248 不接" % PRIOR_NAME)
_spec = importlib.util.spec_from_file_location("vrn_manager_prior_for_v0248", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
for _name, _value in vars(PRIOR).items():
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = _value


def _rebind(fn):
    return types.FunctionType(fn.__code__, globals(), fn.__name__, fn.__defaults__, fn.__closure__)


HEADERS_V3 = [
    ("REPORT_DATE", "Report Date", "報告日期"), ("FILENAME", "File Name", "檔案名稱"), ("TICKER", "Ticker Symbol", "股票代號"), ("YFINANCE_TICKER", "Yahoo Finance Ticker", "Yahoo 財經代號"),
    ("BLOOMBERG_TICKER", "Bloomberg Ticker", "彭博代號"), ("NAME", "Company Name", "公司名稱"), ("BROKER", "Broker", "券商"), ("ANALYST", "Analyst", "分析師"), ("RATING", "Rating", "評等"),
    ("TARGET_PRICE", "Target Price", "目標價"), ("TARGET_PRICE(ADJ)", "Adjusted Target Price", "調整後目標價"), ("CURRENT_PRICE_REPORT", "Current Price at Report", "報告發布時股價"),
    ("UPSIDE_ADJ", "Adjusted Upside Percentage", "調整後潛在上漲空間(純小數)"), ("ADJ_CLOSE", "Adjusted Close", "調整後收盤價"), ("ADJ_CLOSE_BEFORE_REPORT", "Adjusted Close Before Report", "報告前調整後收盤價"),
    ("TOPIC_SUMMARY", "Topic and Summary", "主題與摘要"),
] + [("%s_Y%d" % (k, i), "%s Year N%s" % (en, "" if i == 0 else "+%d" % i), "N%s年 %s" % ("" if i == 0 else "+%d" % i, zh))
     for k, en, zh in (("DILUTED_EPS", "Diluted EPS", "稀釋每股盈餘"), ("DPS", "DPS", "每股股息"), ("BVPS", "BVPS", "每股淨值"), ("ROE", "ROE", "股東權益報酬率"), ("PER", "PER", "本益比"), ("PBR", "PBR", "股價淨值比"), ("CASH_YIELD", "Cash Yield", "現金殖利率")) for i in range(3)] + [
    ("RECENT_REPORT_PRE_EARNINGS_FLAG", "Recent Report and Pre Earnings Flag", "近期雙月內報告暨財報發布前標註"), ("STATUS", "Status", "狀態")]

_STD3 = {"eps_diluted": ("稀釋每股盈餘", "稀釋EPS", "Diluted EPS", "EPS (diluted)"), "eps_any": ("每股盈餘", "EPS", "每股稅後盈餘", "EPS(元)"),
         "dps": ("每股股利", "每股股息", "現金股利", "每股現金股利", "DPS", "Dividend per share", "Dividend/share", "Div/sh"),
         "bvps": ("每股淨值", "每股帳面價值", "BVPS", "Book value per share", "BV/share", "BVPS(元)"),
         "roe": ("股東權益報酬率", "ROE", "淨值報酬率"), "equity": ("權益總額", "權益總計", "股東權益總額", "股東權益", "Total equity", "Shareholders' equity"),
         "net_income": ("稅後淨利", "本期淨利", "稅後純益", "歸屬母公司淨利", "Net income", "Net profit")}
_DEADLINES = ((3, 31, "年報(前一年 Q4)"), (5, 15, "Q1"), (8, 14, "Q2"), (11, 14, "Q3"))


def _std3(item: str) -> str:
    a = str(item or "").replace(" ", "").lower()
    for k, names in _STD3.items():
        if any(n.replace(" ", "").lower() in a for n in names):
            return k
    return ""


def _flag(report_date: str, today: _dt.date = None) -> str:
    today = today or _dt.date.today()
    try:
        rd = _dt.date.fromisoformat(str(report_date)[:10])
    except ValueError:
        return "報告日無法判讀"
    recent = (today - rd).days <= 61
    # 最近一個已結束的季度 → 其公告期限
    q_end = {1: (rd.year - 1, 12, 31), 2: (rd.year - 1, 12, 31), 3: (rd.year - 1, 12, 31), 4: (rd.year, 3, 31), 5: (rd.year, 3, 31), 6: (rd.year, 3, 31),
             7: (rd.year, 6, 30), 8: (rd.year, 6, 30), 9: (rd.year, 6, 30), 10: (rd.year, 9, 30), 11: (rd.year, 9, 30), 12: (rd.year, 9, 30)}[rd.month]
    qe = _dt.date(*q_end)
    dl, lab = {12: (_dt.date(qe.year + 1, 3, 31), "年報(Q4 %d)" % qe.year), 3: (_dt.date(qe.year, 5, 15), "Q1 %d" % qe.year), 6: (_dt.date(qe.year, 8, 14), "Q2 %d" % qe.year), 9: (_dt.date(qe.year, 11, 14), "Q3 %d" % qe.year)}[qe.month]
    pre = rd <= dl
    return "%s · %s 財報期限 %s · 報告在期限%s(%s)" % ("兩個月內" if recent else "非兩個月內(距今 %d 天)" % (today - rd).days, lab, dl.isoformat(), "之前" if pre else "之後", "財測可能未含該期實際" if pre else "財測應已含該期實際")


def _years(fin: list, fname: str) -> dict:
    """年度數據冊 → {std: {year: value}}(VALUE_FINAL 優先 · 已含 v0247 實際蓋過預估)。EPS:稀釋優先 · 只有單列 EPS 時視為稀釋(EPS_KIND)。"""
    out = {}
    for r in fin:
        if r.get("FILENAME") != fname:
            continue
        y = str(r.get("PERIOD_STD") or "")[:4]
        if not y.isdigit():
            continue
        std = _std3(r.get("ITEM"))
        if std == "eps_any":
            std = "eps_diluted" if str(r.get("EPS_KIND") or "diluted") == "diluted" else "eps_basic"
        if not std:
            continue
        v = r.get("VALUE_FINAL") if r.get("VALUE_FINAL") not in (None, "") else r.get("VALUE_NUM")
        try:
            v = float(v)
        except (TypeError, ValueError):
            continue
        out.setdefault(std, {}).setdefault(int(y), v)
    return out


def _fill_years(row: dict, yrs: dict, adj_close) -> None:
    try:
        n = int(str(row.get("REPORT_DATE") or "")[:4])
    except ValueError:
        return
    px = float(adj_close) if adj_close not in (None, "") else None
    for i in range(3):
        y = n + i
        eps = (yrs.get("eps_diluted") or {}).get(y)
        dps = (yrs.get("dps") or {}).get(y)
        bv = (yrs.get("bvps") or {}).get(y)
        ni, eq, eq0 = (yrs.get("net_income") or {}).get(y), (yrs.get("equity") or {}).get(y), (yrs.get("equity") or {}).get(y - 1)
        roe = round(ni / ((eq + eq0) / 2.0), 9) if ni is not None and eq is not None and eq0 is not None and (eq + eq0) else None
        if roe is None and (yrs.get("roe") or {}).get(y) is not None:
            rv = (yrs.get("roe") or {})[y]; roe = round(rv / 100.0, 9) if abs(rv) > 1.5 else round(rv, 9)   # 報告值 % → 純小數 · 註記非平均權益
            row.setdefault("_ROE_NOTE", []).append("ROE Y%d 用報告值(非平均權益)" % i)
        row["DILUTED_EPS_Y%d" % i] = "" if eps is None else eps
        row["DPS_Y%d" % i] = "" if dps is None else dps
        row["BVPS_Y%d" % i] = "" if bv is None else bv
        row["ROE_Y%d" % i] = "" if roe is None else roe
        row["PER_Y%d" % i] = round(px / eps, 9) if px and eps else ""
        row["PBR_Y%d" % i] = round(px / bv, 9) if px and bv else ""
        row["CASH_YIELD_Y%d" % i] = round(dps / px, 9) if px and dps is not None else ""


def _order(row: dict) -> dict:
    keys = [k for k, _, _ in HEADERS_V3]
    front = [k for k in keys if k not in ("RECENT_REPORT_PRE_EARNINGS_FLAG", "STATUS")]
    rest = [k for k in row if k not in keys and k not in ("_STATUS", "_ROE_NOTE")]
    new = {k: row.get(k, "") for k in front}
    for k in rest:
        new[k] = row[k]
    new["RECENT_REPORT_PRE_EARNINGS_FLAG"] = row.get("RECENT_REPORT_PRE_EARNINGS_FLAG", "")
    st = row.get("STATUS", "")
    if row.get("_ROE_NOTE"):
        st = (st + " · " if st else "") + " / ".join(row["_ROE_NOTE"])
    new["STATUS"] = st
    return new


def apply_v3(basic: list, summ: list, fin: list, market: dict, today: _dt.date = None) -> int:
    smap = {s.get("FILENAME"): s for s in summ}
    pf = (market or {}).get("per_file") or {}
    n = 0
    for i, row in enumerate(basic):
        f = row.get("FILENAME")
        s = smap.get(f) or {}
        pts = [s.get("POINT_%d" % k) for k in range(1, 5) if s.get("POINT_%d" % k)]
        row["TOPIC_SUMMARY"] = (s.get("TITLE") or row.get("TITLE") or "") + ((" | " + " | ".join(pts)) if pts else "")
        if row.get("UPSIDE_ADJ") in (None, "") and (pf.get(f) or {}).get("upside_adj") is not None:
            row["UPSIDE_ADJ"] = pf[f]["upside_adj"]
        _fill_years(row, _years(fin, f), row.get("ADJ_CLOSE") or (pf.get(f) or {}).get("adj_close"))
        row["RECENT_REPORT_PRE_EARNINGS_FLAG"] = _flag(row.get("REPORT_DATE"), today)
        basic[i] = _order(row)
        n += 1
    return n


def _write_headers_book(v2: Path) -> None:
    ssd = HERE / "SSOT"; ssd.mkdir(exist_ok=True)
    p = ssd / "VRN2_BasicInfo_Headers_v0100.json"
    if not p.exists():
        p.write_text(json.dumps({"book": "VRN2_BasicInfo_Headers", "version": "v0100", "rule": "R-HDR-01:介面 / 匯出用 Formal English Title Case · 程式鍵不變 · 只增不減", "columns": [{"key": k, "en": e, "zh": z} for k, e, z in HEADERS_V3]}, ensure_ascii=False, indent=1), encoding="utf-8")


def _write_formal_csv(od: Path, basic: list) -> None:
    en = {k: e for k, e, _ in HEADERS_V3}
    cols = list(basic[0].keys()) if basic else [k for k, _, _ in HEADERS_V3]
    with (od / "VRN2_BasicInfo_latest_formal.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh); w.writerow([en.get(c, c.replace("_", " ").title()) for c in cols])
        for r in basic:
            w.writerow([r.get(c, "") if not isinstance(r.get(c), (dict, list)) else json.dumps(r.get(c), ensure_ascii=False) for c in cols])


def _out_books(res, acc, st, v2):
    basic, fin, summ, gaps, made = PRIOR._out_books(res, acc, st, v2)
    try:
        od = Path(v2) / "output"
        market = {}
        try:
            market = json.loads((Path(v2) / "market" / "VRN2_Market_latest.json").read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            pass
        n = apply_v3(basic, summ, fin, market)
        _rewrite_book(od, "BasicInfo", basic); _write_formal_csv(od, basic); _write_headers_book(v2)
        f3 = sum(1 for b in basic if b.get("DILUTED_EPS_Y0") not in ("", None))
        rc = sum(1 for b in basic if "兩個月內" in str(b.get("RECENT_REPORT_PRE_EARNINGS_FLAG", "")) and "非" not in str(b.get("RECENT_REPORT_PRE_EARNINGS_FLAG", ""))[:5])
        print("  [計] v0248 Headers V3:基本資料 %d 份 · 三年 EPS 有值 %d · 兩個月內報告 %d · 正式英文表頭 CSV + 表頭冊 → VRN2_BasicInfo_latest_formal.csv / SSOT/VRN2_BasicInfo_Headers_v0100.json" % (n, f3, rc), flush=True)
    except Exception as exc:  # noqa: BLE001
        print("  [計] v0248 Headers V3 未完成 %s %s" % (type(exc).__name__, str(exc)[:80]), flush=True)
    return basic, fin, summ, gaps, made


def completion(*args, **kwargs):
    result = PRIOR.completion(*args, **kwargs)
    try:
        result["manager"] = "%s %s" % (DISPLAY_NAME, TAG)
    except Exception:  # noqa: BLE001
        pass
    return result


_MY_SIG = hashlib.sha1("|".join(inspect.getsource(f) for f in (apply_v3, _flag)).encode("utf-8")).hexdigest()[:12]
for _n in ("_base_acceptance", "_acc_parallel", "_acc_shard_main", "_acc_one", "_acc_one_core", "_acc_basic", "acceptance", "_acc_sig", "_native_vrn2", "vrn2", "_idem_check", "main", "_success_register", "_ui_panel_html", "_out_html"):
    globals()[_n] = _rebind(getattr(PRIOR, _n))


def selftest() -> int:
    ok = [0, 0]
    def chk(name, cond):
        ok[0 if cond else 1] += 1
        print("  [%s] %s" % ("OK" if cond else "FAIL", name))
    f1 = _flag("2025-08-19", _dt.date(2026, 10, 27)); f2 = _flag("2026-09-15", _dt.date(2026, 10, 27)); f3 = _flag("2026-05-10", _dt.date(2026, 10, 27))
    chk("⓪ v0248 標註:%s | %s | %s" % (f1, f2, f3), "非兩個月內" in f1 and "Q2 2025" in f1 and "之後" in f1 and f2.startswith("兩個月內") and "Q2 2026" in f2 and "Q1 2026" in f3 and "之前" in f3)
    basic = [{"REPORT_DATE": "2025-08-19", "FILENAME": "x.pdf", "TICKER": "6873", "ADJ_CLOSE": 200.0, "TITLE": "t", "EMAIL": "a@b", "STATUS": "ok"}]
    summ = [{"FILENAME": "x.pdf", "TITLE": "泓德(6873.TW): 下修", "POINT_1": "p1", "POINT_2": "p2"}]
    fin = [{"FILENAME": "x.pdf", "ITEM": "每股盈餘(元)", "PERIOD_STD": "2025", "VALUE_NUM": 9.76, "EPS_KIND": "diluted"}, {"FILENAME": "x.pdf", "ITEM": "每股盈餘(元)", "PERIOD_STD": "2026", "VALUE_NUM": 13.0, "EPS_KIND": "diluted"},
           {"FILENAME": "x.pdf", "ITEM": "每股淨值(NT$元)", "PERIOD_STD": "2025", "VALUE_NUM": 90.7}, {"FILENAME": "x.pdf", "ITEM": "每股現金股利(NT$元)", "PERIOD_STD": "2025", "VALUE_NUM": 5.3},
           {"FILENAME": "x.pdf", "ITEM": "股東權益報酬率", "PERIOD_STD": "2025", "VALUE_NUM": 10.9}, {"FILENAME": "x.pdf", "ITEM": "稅後淨利", "PERIOD_STD": "2026", "VALUE_NUM": 1590.0},
           {"FILENAME": "x.pdf", "ITEM": "權益總計", "PERIOD_STD": "2025", "VALUE_NUM": 9281.0}, {"FILENAME": "x.pdf", "ITEM": "權益總計", "PERIOD_STD": "2026", "VALUE_NUM": 10500.0}]
    apply_v3(basic, summ, fin, {"per_file": {"x.pdf": {"upside_adj": 0.04}}}, _dt.date(2026, 10, 27))
    b = basic[0]; ks = list(b.keys())
    chk("⓪ v0248 三年欄:EPS N %s / N+1 %s · PER N %s · PBR N %s · CY N %s · ROE N(報告值→小數)%s · ROE N+1(平均權益)%s" % (b["DILUTED_EPS_Y0"], b["DILUTED_EPS_Y1"], b["PER_Y0"], b["PBR_Y0"], b["CASH_YIELD_Y0"], b["ROE_Y0"], b["ROE_Y1"]),
        b["DILUTED_EPS_Y0"] == 9.76 and b["DILUTED_EPS_Y1"] == 13.0 and abs(b["PER_Y0"] - 200 / 9.76) < 1e-9 and abs(b["PBR_Y0"] - 200 / 90.7) < 1e-9 and abs(b["CASH_YIELD_Y0"] - 5.3 / 200) < 1e-9 and b["ROE_Y0"] == 0.109 and abs(b["ROE_Y1"] - 1590 / ((9281 + 10500) / 2)) < 1e-9)
    chk("⓪ v0248 欄序:首欄 %s · 第 16 欄 %s · 倒數第二 %s · 末欄 %s · 既有 EMAIL 保留 %s · UPSIDE_ADJ %s" % (ks[0], ks[15], ks[-2], ks[-1], "EMAIL" in ks, b["UPSIDE_ADJ"]),
        ks[0] == "REPORT_DATE" and ks[15] == "TOPIC_SUMMARY" and ks[-2] == "RECENT_REPORT_PRE_EARNINGS_FLAG" and ks[-1] == "STATUS" and "EMAIL" in ks and b["UPSIDE_ADJ"] == 0.04 and b["TOPIC_SUMMARY"].startswith("泓德(6873.TW): 下修 | p1 | p2") and "ROE Y0 用報告值" in b["STATUS"])
    chk("⓪ v0248 表頭冊 %d 欄 · 正式英文 %s / %s" % (len(HEADERS_V3), HEADERS_V3[12][1], HEADERS_V3[-2][1]), len(HEADERS_V3) == 39 and HEADERS_V3[12][1] == "Adjusted Upside Percentage")
    chk("⓪ v0248 綁定:vrn2 內部 _out_books / completion 走本版 %s %s" % (_native_vrn2.__globals__["_out_books"] is _out_books, _native_vrn2.__globals__["completion"] is completion), _native_vrn2.__globals__["_out_books"] is _out_books and _native_vrn2.__globals__["completion"] is completion)
    import os
    if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") != "1":
        print("          ── 前版鏈(v0247)自測 ──")
        rc = PRIOR.selftest()
        chk("③ 前版鏈 v0247 自測 rc %s" % rc, rc == 0)
    p, f = ok
    print("[計] VRN-2 SystemManager v0248(VRN_SystemManager_v0248.py)自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(main(sys.argv[1:]))
