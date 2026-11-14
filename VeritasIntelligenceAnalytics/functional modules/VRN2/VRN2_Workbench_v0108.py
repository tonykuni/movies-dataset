#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_Workbench v0108 — v0107 薄尾(v0107 與它的動態前版一字不改):ENG049 對帳頁視覺模板鎖定 + 資料頁顯示規則 + 全冊最後一欄 Source。

操作員 2026-11-03:
  「Ticker Symbol / 股票代號 改為 Ticker / YFinance · Ticker / YFinance Ticker 同步顯示 · 代號下一欄一定接 Name」
  「Broker 一律用英文縮寫顯示」
  「報告日左邊加一欄:在官方法定公布財報日期之前或超過 30 個交易日 → 一律顯示過期」
  「VRN-RECONCILE · READ-ONLY · 零落庫 · OCR EXTRACTION × SSOT v2 · CONTENT RECONCILE MATRIX 的 html 作為靜態 U/I 視覺模板 ·
    字體大小及視覺顏色一致且鎖定 · 左右面板及其他部分再加上去」
  「擷取下來的時間一律用 YYYY · YYYY-MM · YYYY-MM-DD 顯示」
  「所有的資料最後都要新增一欄 Source · 區隔歷史資料(TWSE / TPEX)還是報告預估資料」

做法(window.VRN2_DATA 一個字都不改 —— 前版規則:U/I 匯出要跟輸出冊逐字相同):
  ① 模板:VRN_ENG049_ContentReconcile v0102 寫的對帳頁(本倉 functional modules\\VRN)的字型 / 字級 / 顏色抽成一組鎖定 token
     (底 #f2f1ec · 字 #33403f · 標題 Cormorant Garamond 19px · 內文 Microsoft JhengHei 9.5–11px · 表頭 / 標籤 Consolas 9px 大寫 ·
     白底表格 #dbd9d3 框 · 綠 / 琥珀 / 紅三種淡底標籤)→ 一段 CSS 蓋在整頁最後(左欄 · 頁首 · 分頁 · 卡片 · 矩陣 · 00 系統現況 · v0107 區塊全部套)。
     字級只用 19 / 11 / 9.5 / 9 / 8 px 與內文 clamp;顏色只用模板 15 色;這段 CSS 的 SHA-256 釘在本檔(改就要出新版)。
  ② 資料頁(02)顯示層:在頁面 JS 裡換欄 / 換格,不動資料 ——
     · 報告日左邊加「Freshness / 時效」:報告日早於最近一個已過的法定財報期限(3/31 年報 · 5/15 Q1 · 8/14 Q2 · 11/14 Q3)
       或距今超過 30 個交易日 → 過期;交易日 = 週一到五 − VDF 的台股休市表(VDF_MDL001 TW_KNOWN_HOLIDAYS · 唯讀借用)。
     · TICKER → 一欄「Ticker / YFinance」(2330 / 2330.TW · 冊裡沒有 Yahoo 代號就用 Combined / 基本資料 / 市場冊對)· 下一欄一定是 Name
       (冊裡沒有 NAME 的冊用 Combined 合併後的名稱補 · 滑過看來源)· 原本的 YFINANCE_TICKER / NAME 欄不再重複。
     · Broker 顯示英文縮寫(KGI · GS · MS · JPM · CTBC · MQ …;滑過看原文)· 縮寫表是候選(等 VCGC 核發 · VRN 不自建正式同義字)· 對不到照原文並標記。
     · 期間 / 日期一律 YYYY · YYYY-MM · YYYY-MM-DD(2026E → 2026 · Dec-26F → 2026-12 · 12/25 → 2025-12 · FY26E → 2026;滑過看原文)。
     · 每一冊最後一欄 Source:歷史 TWSE/TPEX · 報告預估 · 報告實際 · 報告 …(E / F / CT = 預估 · A = 實際 · 沒標的照財年是否已過報告日判)。
  ③ 匯出(整冊 CSV · 擷取 CSV / JSON · 每頁 JSON / MD):值照輸出冊原樣,最後多一欄 SOURCE(跟畫面同規則)。
  ④ v0107 的 Basic Info · 合併檢視照新規則重排(時效 · 報告日 · Ticker / YFinance · Name · 券商縮寫 … · Source)。
動詞同前版:render · logo · --selftest。
"""
from __future__ import annotations

import ast
import datetime as _dt
import hashlib
import html
import importlib.util
import json
import re
import sys
from pathlib import Path

VERSION = "v0108"
DISPLAY_NAME = "VRN2_Workbench"
PRIOR_NAME = "VRN2_Workbench_v0107.py"
HERE = Path(__file__).resolve().parent


def _load_prior():
    path = HERE / PRIOR_NAME
    if not path.is_file():
        raise FileNotFoundError("前版 %s 不在 %s" % (PRIOR_NAME, HERE))
    spec = importlib.util.spec_from_file_location("vrn2_workbench_prior_v0107_for108", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PRIOR = _load_prior()

TEMPLATE_SOURCE = "VRN_ENG049_ContentReconcile_v0102.py(functional modules\\VRN)· VRN-RECONCILE · READ-ONLY · 零落庫 · OCR EXTRACTION × SSOT v2 · CONTENT RECONCILE MATRIX"
PALETTE = ("#f2f1ec", "#ffffff", "#33403f", "#1b1a17", "#6b6860", "#dcdad3", "#dbd9d3", "#ebe9e3", "#3d7a52",
           "#e6efec", "#2c4f4a", "#f2ecdd", "#6f5c31", "#f3e7e6", "#9e2b25")
SIZES_PX = (19, 11, 9.5, 9, 8)
F_BODY = '"Microsoft JhengHei","Segoe UI",sans-serif'
F_DISP = "'Cormorant Garamond',Georgia,serif"
F_MONO = "Consolas,monospace"

_CSS = """<style id="wb108-tpl">/* VRN2_Workbench v0108 · 視覺模板鎖定(來源 VRN_ENG049_ContentReconcile v0102 對帳頁)· 只用模板 15 色 · 字級 19 / 11 / 9.5 / 9 / 8 px */
:root{--bg:#f2f1ec;--paper:#ffffff;--paper2:#ffffff;--zebra:#ffffff;--soft:#ebe9e3;--ink:#33403f;--ink2:#33403f;--mut:#6b6860;--mut2:#6b6860;--line:#dbd9d3;
--up:#9e2b25;--down:#3d7a52;--blue:#2c4f4a;--teal:#2c4f4a;--am:#6f5c31;--co:#9e2b25;--vi:#6f5c31;
font:400 clamp(9.5px,1.05vw,11px)/1.5 "Microsoft JhengHei","Segoe UI",sans-serif;color:#33403f;background:#f2f1ec}
body{background:#f2f1ec;color:#33403f;font-family:"Microsoft JhengHei","Segoe UI",sans-serif;font-size:clamp(9.5px,1.05vw,11px);line-height:1.5}
main,aside,.box,td,button,a.action,input,select,.subtle,.ask,.dialog-note,.unitnote,.kv .cell b,.kv .cell .d,.sm-lb,.sm-dt,.sm-l,.sm-sl,.sm-leg,.sm-state,.sm-empty,#drop{font-family:"Microsoft JhengHei","Segoe UI",sans-serif}
header.vh{background:#f2f1ec;color:#1b1a17;border-bottom:1px solid #dcdad3}
header.vh::after{display:none}
header.vh small,.num{font:400 9.5px Consolas,monospace;letter-spacing:.16em;text-transform:uppercase;color:#6b6860}
header.vh h1{font:500 19px 'Cormorant Garamond',Georgia,serif;letter-spacing:.055em;color:#1b1a17}
header.vh .tag{font:400 11px "Microsoft JhengHei","Segoe UI",sans-serif;color:#6b6860}
header.vh .meta{font:400 9.5px Consolas,monospace;color:#6b6860}
aside{background:#ffffff;border-right:1px solid #dcdad3}
.box{background:#ffffff;border:1px solid #dbd9d3;border-radius:8px;box-shadow:none}
.cards>.box{border-left:3px solid #2c4f4a}
h2{font:700 11px "Microsoft JhengHei","Segoe UI",sans-serif;color:#1b1a17;letter-spacing:.02em}
h3,.sm-sect,.sm-colh,.sm-k,.kv .cell small,.stat small,.frm label{font:700 9px Consolas,monospace;letter-spacing:.05em;text-transform:uppercase;color:#6b6860}
.subtle,.unitnote,.sm-l,.sm-sl,.sm-sub,.sm-mut{font-size:11px;color:#6b6860}
.stat{background:#ffffff;border:1px solid #dbd9d3;border-radius:8px}
.stat b,.sm-sn,.sm-n,.sm-title{font:500 19px 'Cormorant Garamond',Georgia,serif!important;letter-spacing:.055em;color:#1b1a17;white-space:normal!important;overflow-wrap:anywhere}
.kv .cell,.sm-card{background:#ffffff;border:1px solid #dbd9d3}
.kv .cell b{font-size:11px;font-weight:700;color:#1b1a17}
.tabs button{font:700 9px Consolas,monospace;letter-spacing:.1em;text-transform:uppercase;color:#6b6860}
.tabs button.active,.subtabs button.active{background:#2c4f4a;color:#ffffff;border-color:#2c4f4a}
.subtabs button,button,a.action{font:600 11px "Microsoft JhengHei","Segoe UI",sans-serif;color:#33403f;background:#ffffff;border-color:#dbd9d3}
button.primary,a.action.primary{background:#2c4f4a;color:#ffffff;border-color:#2c4f4a}
button.danger{background:#ffffff;color:#9e2b25;border-color:#9e2b25}
input[type=text],input[type=date],select{font:400 11px Consolas,monospace;color:#33403f;background:#ffffff;border-color:#dbd9d3}
.matrix,.sm-mx,.sm-detail{background:#ffffff;border:1px solid #dbd9d3;border-radius:8px}
table{background:#ffffff;font-size:inherit}
th,td{padding:4px 8px;border-bottom:1px solid #ebe9e3;vertical-align:top}
th,#wb107 table th,#wb107b table th{background:#ffffff;color:#6b6860;font:700 9px Consolas,monospace;text-transform:uppercase;letter-spacing:.05em}
tbody tr:nth-child(even) td{background:#ffffff}
td.n,.mono,pre,.sm-ep,.sm-sb,.sm-db,.sm-v,.outfolder .path{font-family:Consolas,monospace;font-size:.95em}
.pill,.w8tag,.sm-badge,.sm-st,.sm-src,.sm-h,#wb107 .asof{display:inline-block;padding:1px 7px;border-radius:9px;font:700 8px Consolas,monospace;letter-spacing:.05em;border:none;background:#f2ecdd;color:#6f5c31}
.pill.good,.w8tag.g,.sm-st.GREEN{background:#e6efec;color:#2c4f4a}
.pill.bad,.w8tag.r,.sm-st.RED,#wb107 .asof{background:#f3e7e6;color:#9e2b25}
.pill.gray,.w8tag.n{background:#ebe9e3;color:#6b6860}
.w8tag.o,.sm-st.YELLOW{background:#f2ecdd;color:#6f5c31}
.lamp.GREEN{background:#3d7a52}.lamp.YELLOW{background:#6f5c31}.lamp.RED{background:#9e2b25}.lamp.GRAY{background:#dbd9d3}
#notice{background:#1b1a17;color:#ffffff;font:400 11px Consolas,monospace}
.w8foot{font:400 9px Consolas,monospace;letter-spacing:.1em;color:#6b6860;text-transform:uppercase;text-align:center;padding:9px 0 3px}
.w8unk{border-bottom:1px dotted #9e2b25}
.w8dim{color:#6b6860}
#wb107b sup.src{font:700 8px Consolas,monospace;background:#ebe9e3;color:#6b6860}#wb107b sup.src.m{background:#e6efec;color:#2c4f4a}#wb107b sup.src.o{background:#f2ecdd;color:#6f5c31}
</style>"""
CSS_SHA256 = "4a9fe74d7aba4e9cc2552ccbc6db3c26a18046510f3b32d32ce84f3636eb0e7a"      # 建置時填(鎖定:CSS 一改就對不上 → 自測紅 → 要出新版)

STATUTORY = ((3, 31, "年報"), (5, 15, "Q1"), (8, 14, "Q2"), (11, 14, "Q3"))   # 上市櫃一般公司法定公布期限(證交法第 36 條)
STALE_TDAYS = 30
BROKER_ABBR = {   # 候選(VRN 顯示用 · 等 VCGC 核發正式同義字 · 不寫進輸出冊)
    "凱基": "KGI", "凱基投顧": "KGI", "KGI": "KGI", "中信": "CTBC", "中信投顧": "CTBC", "中國信託": "CTBC", "CTBC": "CTBC",
    "國泰": "Cathay", "國泰證券": "Cathay", "兆豐": "Mega", "兆豐投顧": "Mega", "兆豐證券": "Mega", "華南": "HNS", "華南投顧": "HNS", "華南永昌": "HNS",
    "元大": "Yuanta", "富邦": "Fubon", "群益": "Capital", "永豐": "SinoPac", "統一": "PSC", "玉山": "E.SUN", "第一金": "FSC", "台新": "Taishin",
    "日盛": "JihSun", "宏遠": "Horizon", "康和": "Concord", "合庫": "TCB", "元富": "MasterLink", "福邦": "Fubon",
    "Goldman Sachs": "GS", "GS": "GS", "Morgan Stanley": "MS", "MS": "MS", "J.P. Morgan": "JPM", "JPMorgan": "JPM", "JP Morgan": "JPM", "JPM": "JPM",
    "Citi": "Citi", "Citigroup": "Citi", "Daiwa": "Daiwa", "CLSA": "CLSA", "UBS": "UBS", "GF": "GF", "GF Securities": "GF", "GFHK": "GF",
    "Macquarie": "MQ", "MQ": "MQ", "Nomura": "Nomura", "HSBC": "HSBC", "BofA": "BofA", "BofA Securities": "BofA", "Bank of America": "BofA",
    "Jefferies": "Jefferies", "Mizuho": "Mizuho", "Credit Suisse": "CS", "Deutsche Bank": "DB", "Barclays": "Barclays", "Bernstein": "Bernstein",
    "Morningstar": "Morningstar", "Fubon": "Fubon", "Yuanta": "Yuanta", "SinoPac": "SinoPac", "Mega": "Mega", "Cathay": "Cathay",
}
MON = {m: i for i, m in enumerate(("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"), 1)}


# ── 純函式(Python 版 · 自測與 Basic 合併卡用;頁面 JS 用同一套規則)──────────────────────────────
def norm_date(s) -> str:
    """YYYY-MM-DD(讀得出年月日的);讀不出 → ""。ISO 時間帶時區 → 台北日期。"""
    t = str(s if s is not None else "").strip()
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::\d{2}(?:\.\d+)?)?(Z|[+-]\d{2}:?\d{2})$", t)
    if m:
        base = _dt.datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)))
        z = m.group(6)
        off = 0 if z == "Z" else (1 if z[0] == "+" else -1) * (int(z[1:3]) * 60 + int(z[-2:]))
        return (base - _dt.timedelta(minutes=off) + _dt.timedelta(hours=8)).date().isoformat()
    m = re.match(r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", t)
    return "%s-%02d-%02d" % (m.group(1), int(m.group(2)), int(m.group(3))) if m else ""


def _y(s: str) -> int:
    return int(s) if len(s) == 4 else 2000 + int(s)


def norm_period(p, report_date="") -> tuple:
    """(顯示 YYYY / YYYY-MM / YYYY-MM-DD, 種類 act / est / "")。讀不出照原文。"""
    s = str(p if p is not None else "").strip()
    flag, disp, end = "", "", None
    pats = (
        (r"^(\d{4})-(\d{2})-(\d{2})$", lambda m: ("%s-%s-%s" % m.groups(), (int(m.group(1)), int(m.group(2))), "")),
        (r"^(\d{4})[-/](\d{1,2})$", lambda m: ("%s-%02d" % (m.group(1), int(m.group(2))), (int(m.group(1)), int(m.group(2))), "")),
        (r"^(\d{4})\s*\(?\s*(A|E|F|CT|CL)?\s*\)?$", lambda m: (m.group(1), (int(m.group(1)), 12), m.group(2) or "")),
        (r"^FY\s*(\d{2}|\d{4})\s*(A|E|F)?$", lambda m: ("%d" % _y(m.group(1)), (_y(m.group(1)), 12), m.group(2) or "")),
        (r"^(\d{2})(A|E|F)$", lambda m: ("%d" % _y(m.group(1)), (_y(m.group(1)), 12), m.group(2))),
        (r"^(\d{1,2})/(\d{2})(A|E|F)?$", lambda m: ("%d-%02d" % (_y(m.group(2)), int(m.group(1))), (_y(m.group(2)), int(m.group(1))), m.group(3) or "")),
        (r"^([A-Za-z]{3})[- ](\d{2}|\d{4})(A|E|F)?$", lambda m: ("%d-%02d" % (_y(m.group(2)), MON[m.group(1).lower()]), (_y(m.group(2)), MON[m.group(1).lower()]), m.group(3) or "")
         if m.group(1).lower() in MON else None),
        (r"^([1-4])Q\s*(\d{2}|\d{4})(A|E|F)?$", lambda m: ("%d-%02d" % (_y(m.group(2)), int(m.group(1)) * 3), (_y(m.group(2)), int(m.group(1)) * 3), m.group(3) or "")),
        (r"^(\d{4})\s*Q([1-4])(A|E|F)?$", lambda m: ("%s-%02d" % (m.group(1), int(m.group(2)) * 3), (int(m.group(1)), int(m.group(2)) * 3), m.group(3) or "")),
        (r"^([12])H\s*(\d{2}|\d{4})(A|E|F)?$", lambda m: ("%d-%02d" % (_y(m.group(2)), int(m.group(1)) * 6), (_y(m.group(2)), int(m.group(1)) * 6), m.group(3) or "")),
    )
    for pat, fn in pats:
        m = re.match(pat, s, re.I)
        if m:
            got = fn(m)
            if got:
                disp, end, flag = got
                break
    if not disp:
        return s, ""
    flag = flag.upper()
    if flag == "A":
        return disp, "act"
    if flag in ("E", "F", "CT", "CL"):
        return disp, "est"
    rd = norm_date(report_date)
    if not rd or not end:
        return disp, ""
    y, mth = end
    last = _dt.date(y + (mth == 12), (mth % 12) + 1, 1) - _dt.timedelta(days=1)
    return disp, ("act" if last.isoformat() < rd else "est")


def source_of(book: str, row: dict) -> str:
    """每一冊最後一欄 Source(歷史 TWSE/TPEX · 報告預估 · 報告實際 · 報告 …)。"""
    b = str(book)
    if b == "FinancialAligned" and str(row.get("VALUE_SOURCE") or "").upper().startswith("HISTORY"):
        return "歷史 TWSE/TPEX"
    if b in ("FinancialData", "FinancialAligned"):
        kind = norm_period(row.get("PERIOD"), row.get("REPORT_DATE"))[1]
        return {"est": "報告預估", "act": "報告實際"}.get(kind, "報告")
    return {"Rejected": "報告(未過驗證)", "Deleted": "報告(被歷史否定)", "Combined": "報告 + TWSE/TPEX/Yahoo + 共識",
            "MarketConsensus": "TWSE/TPEX + 共識"}.get(b, "報告")


def broker_abbr(b) -> tuple:
    """(顯示, 有對到)。"""
    raw = str(b if b is not None else "").strip()
    if not raw:
        return "", True
    if raw in BROKER_ABBR:
        return BROKER_ABBR[raw], True
    low = {k.lower(): v for k, v in BROKER_ABBR.items()}
    if raw.lower() in low:
        return low[raw.lower()], True
    for k, v in sorted(BROKER_ABBR.items(), key=lambda kv: -len(kv[0])):
        if len(k) >= 2 and (raw.startswith(k) or raw.lower().startswith(k.lower() + " ")):
            return v, True
    return raw, False


def latest_deadline(asof: _dt.date) -> _dt.date:
    cands = [_dt.date(y, m, d) for y in (asof.year - 1, asof.year) for m, d, _ in STATUTORY]
    return max(d for d in cands if d <= asof)


def trading_days(d0: _dt.date, d1: _dt.date, hol: set) -> int:
    """(d0, d1] 的交易日數 = 週一到五 − 休市日。"""
    n, d = 0, d0 + _dt.timedelta(days=1)
    while d <= d1:
        if d.weekday() < 5 and d.isoformat() not in hol:
            n += 1
        d += _dt.timedelta(days=1)
    return n


def freshness(report_date, asof: _dt.date, hol: set) -> tuple:
    rd = norm_date(report_date)
    if not rd:
        return "", "報告日讀不出"
    dl = latest_deadline(asof)
    if rd < dl.isoformat():
        return "過期", "法定財報日 %s 之前(較新的官方財報已公布)" % dl.isoformat()
    n = trading_days(_dt.date.fromisoformat(rd), asof, hol)
    if n > STALE_TDAYS:
        return "過期", "距今 %d 個交易日 > %d" % (n, STALE_TDAYS)
    return "有效", "距今 %d 個交易日 · 最近法定財報日 %s" % (n, dl.isoformat())


def vdf_holidays(root) -> tuple:
    """VDF 台股休市表(VDF_MDL001 的 TW_KNOWN_HOLIDAYS_* · 只讀 ast · 不 import VDF)→ (set, 說明)。"""
    folder = Path(root) / "functional modules" / "VDF"
    files = sorted(folder.glob("VDF_MDL001_TWEquityEngine*.py")) if folder.is_dir() else []
    for f in reversed(files):
        try:
            tree = ast.parse(f.read_text(encoding="utf-8", errors="replace"))
        except (OSError, SyntaxError, ValueError):
            continue
        got = set()
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id.startswith("TW_KNOWN_HOLIDAYS") for t in node.targets):
                try:
                    got |= {str(x) for x in ast.literal_eval(node.value)}
                except ValueError:
                    pass
        if got:
            return got, "VDF %s · %d 天(唯讀借用)" % (f.name, len(got))
    return set(), "沒有 VDF 休市表 · 只扣週末"


def _asof() -> _dt.date:
    import os
    if re.match(r"^\d{4}-\d{2}-\d{2}$", os.environ.get("VRN2_ASOF", "")):
        return _dt.date.fromisoformat(os.environ["VRN2_ASOF"])
    return (_dt.datetime.now(_dt.timezone.utc) + _dt.timedelta(hours=8)).date()


def lookups(v2: Path) -> dict:
    """名稱 / Yahoo 代號對照(Combined 合併後 → 基本資料 → 市場冊)。"""
    nf, nt, yf = {}, {}, {}
    for book in ("Combined", "BasicInfo"):
        for r in PRIOR._book(v2, book) or []:
            fn, tk = str(r.get("FILENAME") or "").strip(), str(r.get("TICKER") or "").strip()
            name, y = str(r.get("NAME") or "").strip(), str(r.get("YFINANCE_TICKER") or "").strip()
            if name and fn:
                nf.setdefault(fn, name)
            if name and tk:
                nt.setdefault(tk, name)
            if y and tk:
                yf.setdefault(tk, y)
    mk = PRIOR.jread107(Path(v2) / "market" / "VRN2_Market_latest.json", {}) or {}
    for tk, m in (mk.get("per_ticker") or {}).items():
        if isinstance(m, dict) and m.get("yfinance_ticker"):
            yf.setdefault(str(tk), str(m["yfinance_ticker"]))
    return {"nf": nf, "nt": nt, "yf": yf}


def payload(root: Path, v2: Path, asof: _dt.date | None = None) -> dict:
    asof = asof or _asof()
    hol, hol_src = vdf_holidays(root)
    lk = lookups(v2)
    return {"v": VERSION, "asof": asof.isoformat(), "deadline": latest_deadline(asof).isoformat(), "stale": STALE_TDAYS, "hol": sorted(hol), "hol_src": hol_src,
            "br": BROKER_ABBR, **lk}


_JS = r"""
  /* VRN2_Workbench v0108 顯示層:window.VRN2_DATA 原樣 · 畫面換欄換格 · 匯出原值 + 最後一欄 SOURCE */
  var W8 = window.VRN2_WB108 || {}, W8H = {}, W8TD = {}; (W8.hol || []).forEach(function(d){ W8H[d] = 1; });
  if (typeof HDR === 'object') HDR.TICKER = 'Ticker / YFinance';
  var W8HDR = {FRESH:'Freshness / 時效', TICKER_YF:'Ticker / YFinance', SOURCE:'Source / 來源'};
  var W8MON = {jan:1, feb:2, mar:3, apr:4, may:5, jun:6, jul:7, aug:8, sep:9, oct:10, nov:11, dec:12};
  function w8hdr(c){ return W8HDR[c] || hdr(c); }
  function w8p2(n){ return ('0' + n).slice(-2); }
  function w8y(s){ return s.length === 4 ? +s : 2000 + (+s); }
  function w8d(s){ var t = String(s == null ? '' : s).trim(), m = t.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::\d{2}(?:\.\d+)?)?(Z|[+-]\d{2}:?\d{2})$/);
    if (m) { var z = m[6], off = z === 'Z' ? 0 : (z[0] === '+' ? 1 : -1) * (+z.slice(1, 3) * 60 + +z.slice(-2)); var ms = Date.UTC(+m[1], +m[2] - 1, +m[3], +m[4], +m[5]) - off * 60000 + 8 * 3600000; var d = new Date(ms); return d.getUTCFullYear() + '-' + w8p2(d.getUTCMonth() + 1) + '-' + w8p2(d.getUTCDate()); }
    m = t.match(/^(\d{4})[-\/.](\d{1,2})[-\/.](\d{1,2})/); return m ? m[1] + '-' + w8p2(+m[2]) + '-' + w8p2(+m[3]) : ''; }
  function w8tdays(a, b){ var k = a + '|' + b; if (k in W8TD) return W8TD[k]; var d = new Date(a + 'T00:00:00Z'), e = new Date(b + 'T00:00:00Z'), n = 0;
    d.setUTCDate(d.getUTCDate() + 1); while (d <= e) { var w = d.getUTCDay(), iso = d.toISOString().slice(0, 10); if (w > 0 && w < 6 && !W8H[iso]) n++; d.setUTCDate(d.getUTCDate() + 1); } return (W8TD[k] = n); }
  function w8fresh(rd){ var d = w8d(rd); if (!d || !W8.asof) return ['', '報告日讀不出'];
    if (d < W8.deadline) return ['過期', '法定財報日 ' + W8.deadline + ' 之前(較新的官方財報已公布)'];
    var n = w8tdays(d, W8.asof); return n > (W8.stale || 30) ? ['過期', '距今 ' + n + ' 個交易日 > ' + (W8.stale || 30)] : ['有效', '距今 ' + n + ' 個交易日 · 最近法定財報日 ' + W8.deadline]; }
  function w8period(p, rd){ var s = String(p == null ? '' : p).trim(), m, disp = '', end = null, fl = '';
    if ((m = s.match(/^(\d{4})-(\d{2})-(\d{2})$/))) { disp = s; end = [+m[1], +m[2]]; }
    else if ((m = s.match(/^(\d{4})[-\/](\d{1,2})$/))) { disp = m[1] + '-' + w8p2(+m[2]); end = [+m[1], +m[2]]; }
    else if ((m = s.match(/^(\d{4})\s*\(?\s*(A|E|F|CT|CL)?\s*\)?$/i))) { disp = m[1]; end = [+m[1], 12]; fl = m[2] || ''; }
    else if ((m = s.match(/^FY\s*(\d{2}|\d{4})\s*(A|E|F)?$/i))) { disp = '' + w8y(m[1]); end = [w8y(m[1]), 12]; fl = m[2] || ''; }
    else if ((m = s.match(/^(\d{2})(A|E|F)$/i))) { disp = '' + w8y(m[1]); end = [w8y(m[1]), 12]; fl = m[2]; }
    else if ((m = s.match(/^(\d{1,2})\/(\d{2})(A|E|F)?$/i))) { disp = w8y(m[2]) + '-' + w8p2(+m[1]); end = [w8y(m[2]), +m[1]]; fl = m[3] || ''; }
    else if ((m = s.match(/^([A-Za-z]{3})[- ](\d{2}|\d{4})(A|E|F)?$/i)) && W8MON[m[1].toLowerCase()]) { var mo = W8MON[m[1].toLowerCase()]; disp = w8y(m[2]) + '-' + w8p2(mo); end = [w8y(m[2]), mo]; fl = m[3] || ''; }
    else if ((m = s.match(/^([1-4])Q\s*(\d{2}|\d{4})(A|E|F)?$/i))) { disp = w8y(m[2]) + '-' + w8p2(+m[1] * 3); end = [w8y(m[2]), +m[1] * 3]; fl = m[3] || ''; }
    else if ((m = s.match(/^(\d{4})\s*Q([1-4])(A|E|F)?$/i))) { disp = m[1] + '-' + w8p2(+m[2] * 3); end = [+m[1], +m[2] * 3]; fl = m[3] || ''; }
    else if ((m = s.match(/^([12])H\s*(\d{2}|\d{4})(A|E|F)?$/i))) { disp = w8y(m[2]) + '-' + w8p2(+m[1] * 6); end = [w8y(m[2]), +m[1] * 6]; fl = m[3] || ''; }
    if (!disp) return [s, '']; fl = String(fl).toUpperCase();
    if (fl === 'A') return [disp, 'act']; if (fl === 'E' || fl === 'F' || fl === 'CT' || fl === 'CL') return [disp, 'est'];
    var r = w8d(rd); if (!r || !end) return [disp, ''];
    var last = new Date(Date.UTC(end[0], end[1], 0)).toISOString().slice(0, 10); return [disp, last < r ? 'act' : 'est']; }
  function w8source(r, ds){ if (ds === 'FinancialAligned' && /^HISTORY/i.test(String(r.VALUE_SOURCE || ''))) return '歷史 TWSE/TPEX';
    if (ds === 'FinancialData' || ds === 'FinancialAligned') { var k = w8period(r.PERIOD, r.REPORT_DATE)[1]; return k === 'est' ? '報告預估' : k === 'act' ? '報告實際' : '報告'; }
    return {Rejected:'報告(未過驗證)', Deleted:'報告(被歷史否定)', Combined:'報告 + TWSE/TPEX/Yahoo + 共識', MarketConsensus:'TWSE/TPEX + 共識'}[ds] || '報告'; }
  function w8br(b){ var raw = String(b == null ? '' : b).trim(), B = W8.br || {}, k; if (!raw) return ['', 1]; if (B[raw]) return [B[raw], 1];
    for (k in B) if (k.toLowerCase() === raw.toLowerCase()) return [B[k], 1];
    var ks = Object.keys(B).sort(function(a, c){ return c.length - a.length; });
    for (var i = 0; i < ks.length; i++) { k = ks[i]; if (k.length >= 2 && (raw.indexOf(k) === 0 || raw.toLowerCase().indexOf(k.toLowerCase() + ' ') === 0)) return [B[k], 1]; }
    return [raw, 0]; }
  function w8key(C, re){ for (var i = 0; i < C.length; i++) if (re.test(C[i])) return C[i]; return null; }
  function w8cols(ds, C){ var tk = w8key(C, /^ticker$/i), yf = w8key(C, /^yfinance_ticker$/i), nm = w8key(C, /^name$/i), out = [];
    C.forEach(function(c){ if (tk && (c === yf || c === nm)) return; if (c === 'REPORT_DATE') out.push('FRESH'); if (c === tk) { out.push('TICKER_YF'); out.push(nm || 'NAME'); return; } out.push(c); });
    out.push('SOURCE'); return out; }
  function w8tag(t, cls, tip){ return '<span class="w8tag ' + cls + '"' + (tip ? ' title="' + hx(tip) + '"' : '') + '>' + hx(t) + '</span>'; }
  function w8tk(r){ return String(r.TICKER || r.ticker || '').trim(); }
  function w8cell(r, c, ds){
    if (c === 'FRESH') { var f = w8fresh(r.REPORT_DATE); return '<td class="k">' + (f[0] ? w8tag(f[0], f[0] === '過期' ? 'r' : 'g', f[1]) : '<span class="w8dim" title="' + hx(f[1]) + '">—</span>') + '</td>'; }
    if (c === 'TICKER_YF') { var t = w8tk(r), y = String(r.YFINANCE_TICKER || r.yfinance_ticker || (W8.yf || {})[t] || '').trim(); return '<td class="k">' + hx(t) + ' <span class="w8dim">/ ' + hx(y || '—') + '</span></td>'; }
    if (/^name$/i.test(c)) { var nm = String(r[c] || '').trim(), how = '冊內'; if (!nm) { nm = (W8.nf || {})[r.FILENAME] || (W8.nt || {})[w8tk(r)] || ''; how = 'Combined / 基本資料對照'; } return '<td title="' + hx(nm ? '名稱來源:' + how : '') + '">' + hx(nm) + '</td>'; }
    if (c === 'BROKER') { var b = w8br(r.BROKER); return '<td class="k' + (b[1] ? '' : ' w8unk') + '" title="' + hx(b[1] ? '原文 ' + (r.BROKER || '') : '沒有英文縮寫對照(候選表 · 等 VCGC 核發)') + '">' + hx(b[0]) + '</td>'; }
    if (c === 'PERIOD') { var p = w8period(r.PERIOD, r.REPORT_DATE); return '<td class="k" title="原文 ' + hx(r.PERIOD) + '">' + hx(p[0]) + '</td>'; }
    if (c === 'REPORT_DATE' || /(^|_)DATE$|^date$|_AT_UTC$|_at_utc$/.test(c)) { var dd = w8d(r[c]); return '<td class="k"' + (dd && dd !== String(r[c]) ? ' title="原文 ' + hx(r[c]) + '"' : '') + '>' + hx(dd || r[c]) + '</td>'; }
    if (c === 'SOURCE') { var s = w8source(r, ds); return '<td>' + w8tag(s, /^歷史/.test(s) ? 'g' : /預估/.test(s) ? 'o' : 'n') + '</td>'; }
    return cell(r, c, ds); }
  function w8src(R, ds){ return (R || []).map(function(r){ var o = {}, k; for (k in r) o[k] = r[k]; o.SOURCE = w8source(r, ds); return o; }); }
"""

_REPL = (("var R = rows(st.ds), C = cols(st.ds),", "var R = rows(st.ds), C = w8cols(st.ds, cols(st.ds)),"),
         ("hx(hdr(c))", "hx(w8hdr(c))"),
         ("cell(r, c, st.ds)", "w8cell(r, c, st.ds)"),
         ("csv(R, cols(st.ds), true)", "csv(w8src(R, st.ds), cols(st.ds).concat(['SOURCE']), true)"),
         ("csv(X, cols(ds), true)", "csv(w8src(X, ds), cols(ds).concat(['SOURCE']), true)"),
         ("rows: X}", "rows: w8src(X, ds)}"),
         ("data = rows(st.ds); C = cols(st.ds);", "data = w8src(rows(st.ds), st.ds); C = cols(st.ds).concat(['SOURCE']);"),
         ("data = xrows(); C = cols($('#xDs').value);", "data = w8src(xrows(), $('#xDs').value); C = cols($('#xDs').value).concat(['SOURCE']);"))
_BOOT = re.compile(r"\n  setTab\('\w+'\); renderData\(\); renderX\(\); selCount\(\);")
_DATA_ANCHOR = "<script>window.VRN2_DATA = "


def basic_block_html(v2: Path, w8: dict) -> str:
    """Basic Info · 合併檢視(v0107 卡 → 新規則:時效 · 報告日 · Ticker / YFinance · Name · 券商縮寫 … · Source)。id 照舊 wb107b。"""
    e = html.escape
    bm = PRIOR.basic_merged(v2)
    head = ('\n<section class="box wb108" id="wb107b"><h2>Basic Info · 合併檢視(原文 × Combined)<span class="pill good">Workbench v0108</span></h2>')
    if not bm["ok"]:
        return head + '<div class="subtle">%s</div></section>\n' % e(bm["why"])
    asof, hol = _dt.date.fromisoformat(w8["asof"]), set(w8["hol"])
    rows, n_stale = [], 0
    for r in bm["rows"][:PRIOR.BASIC_MAX_ROWS]:
        st, why = freshness(r["REPORT_DATE"], asof, hol)
        n_stale += st == "過期"
        nm, adj, up = r["NAME"], r["ADJ_CLOSE"], r["UPSIDE"]
        br, ok = broker_abbr(r["BROKER"])
        yf = w8["yf"].get(r["TICKER"], "")
        merged = bool(nm[1] == "合" or adj[1] == "合")
        src = "報告 + 合併(TWSE/TPEX/Yahoo/VDF)" if merged else "報告"
        rows.append('<tr><td>%s</td><td class="k">%s</td><td class="k" title="%s">%s <span class="w8dim">/ %s</span></td><td>%s%s</td><td class="k%s" title="%s">%s</td>'
                    '<td>%s</td><td class="n">%s</td><td class="n">%s</td><td class="n">%s%s</td><td class="n" title="%s">%s%s</td><td class="n">%s</td><td class="n">%s</td><td>%s</td></tr>' % (
                        ('<span class="w8tag %s" title="%s">%s</span>' % ("r" if st == "過期" else "g", e(why), e(st))) if st else "—",
                        e(norm_date(r["REPORT_DATE"]) or r["REPORT_DATE"]), e(r["FILENAME"]), e(r["TICKER"]), e(yf or "—"),
                        e(nm[0]), PRIOR._src(nm[1], nm[2]), "" if ok else " w8unk", e(("原文 " + r["BROKER"]) if ok else "沒有英文縮寫對照(候選表 · 等 VCGC 核發)"), e(br),
                        e(r["RATING"]), e(r["TARGET_PRICE"]), e(r["TARGET_PRICE(ADJ)"]), e(adj[0]), PRIOR._src(adj[1], adj[2]),
                        e(up[2]), e(up[0]), PRIOR._src(up[1], up[2]), e(r["FACTSET"]), e(r["YAHOO"]),
                        '<span class="w8tag %s">%s</span>' % ("o" if merged else "n", e(src))))
    leg = ('<div class="subtle">%d 份 · 過期 %d(時效基準 %s · 最近法定財報日 %s · 交易日 = 週一到五 − %s)· NAME 原文 %d → 合併 %d · ADJ_CLOSE 原文 %d → 合併 %d · '
           '<b>原</b> = 報告原文 · <b>合</b> = Combined 合併冊補上(滑過看來源)· 兩冊內容不改</div>') % (
        bm["n"], n_stale, w8["asof"], w8["deadline"], e(w8["hol_src"]), bm["name_basic"], bm["name_merged"], bm["adj_basic"], bm["adj_merged"])
    table = ('<div class="matrix" style="max-height:46vh;overflow:auto"><table><thead><tr><th>Freshness / 時效</th><th>Report Date / 報告日期</th><th>Ticker / YFinance</th>'
             '<th>Company Name / 公司名稱</th><th>Broker / 券商</th><th>Rating / 評等</th><th>Target Price / 目標價</th><th>Adjusted Target Price / 調整後目標價</th>'
             '<th>Adjusted Close / 調整後收盤價</th><th>Upside (Adj) / 上漲空間(還原)</th><th>FactSet Median</th><th>YFinance Median</th><th>Source / 來源</th></tr></thead>'
             '<tbody>%s</tbody></table></div>' % "".join(rows))
    return head + leg + table + '<div class="w8foot">VERITAS REPORT NOVA · 視覺模板 ENG049 對帳頁 · 鎖定 %s</div></section>\n' % CSS_SHA256[:12]


def augment108(page: str, root: Path, v2: Path, asof: _dt.date | None = None) -> tuple:
    """(頁面, 說明)· 純函式可測 · 重入不重複。"""
    if 'id="wb108-tpl"' in page:
        return page, "已是 v0108"
    w8 = payload(root, v2, asof)
    notes = []
    if page.count("</head>") == 1:
        page = page.replace("</head>", _CSS + "\n</head>", 1)
    if page.count("</title>") >= 1:
        page = page.replace("</title>", "</title><!-- VRN2_Workbench %s over v0107 · UI 模板 ENG049 鎖定 %s -->" % (VERSION, CSS_SHA256[:12]), 1)
    js_ok = page.count(_DATA_ANCHOR) == 1 and len(_BOOT.findall(page)) == 1 and all(page.count(a) == 1 for a, _ in _REPL)
    if js_ok:
        for a, b in _REPL:
            page = page.replace(a, b, 1)
        data = json.dumps(w8, ensure_ascii=False).replace("</", "<\\/")
        page = page.replace(_DATA_ANCHOR, "<script>window.VRN2_WB108 = %s;</script>\n%s" % (data, _DATA_ANCHOR), 1)
        m = _BOOT.search(page)
        page = page[:m.start()] + "\n" + _JS + page[m.start():]
    else:
        notes.append("資料頁顯示層沒接上(前版版型變了 · 資料照前版顯示)")
    i0 = page.find('<section class="box" id="wb107b">')
    if i0 >= 0:
        i1 = page.find("</section>", i0)
        if i1 > i0:
            page = page[:i0] + basic_block_html(v2, w8).strip("\n") + page[i1 + len("</section>"):]
    else:
        notes.append("沒有 v0107 的 Basic 合併卡")
    return page, " · ".join(notes) or "模板 + 顯示層 + Basic 卡都套上"


def render(root: Path, out_path: Path | None = None, logo: str | None = None, assets_zip: Path | None = None) -> Path:
    root = Path(root).resolve()
    out = PRIOR.render(root, out_path, logo, assets_zip)
    v2 = root / "VIA_Reports" / "vrn2"
    page = Path(out).read_text(encoding="utf-8")
    try:
        page, note = augment108(page, root, v2)
    except Exception as error:  # noqa: BLE001  後處理失敗不毀 v0107 頁
        print("    [U/I] [YELLOW] Workbench v0108 後處理沒做成(v0107 頁照出):%s: %s" % (type(error).__name__, str(error)[:160]), flush=True)
        return Path(out)
    if "沒接上" in note:
        print("    [U/I] [YELLOW] Workbench v0108 · %s" % note, flush=True)
    tmp = Path(out).with_suffix(".v0108.tmp")
    tmp.write_text(page, encoding="utf-8")
    tmp.replace(Path(out))
    return Path(out)


def selftest() -> int:
    import tempfile
    fails = []

    def chk(label, cond):
        print("[%s] %s" % ("PASS" if cond else "FAIL", label))
        if not cond:
            fails.append(label)

    src = Path(__file__).read_text(encoding="utf-8")
    css_sha = hashlib.sha256(_CSS.encode("utf-8")).hexdigest()
    colors = {c.lower() for c in re.findall(r"#[0-9a-fA-F]{6}\b", _CSS)}
    flat = re.sub(r"clamp\([^)]*\)", "", _CSS)
    sizes = {float(x) for x in re.findall(r"font(?:-size)?:[^;}]*?(\d+(?:\.\d+)?)px", flat)}
    chk("① 前版 v0107 鏈 · 第 3 行加速器標記 · 模板 CSS SHA-256 = 釘住的值(鎖定)", PRIOR.VERSION == "v0107" and src.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]" and css_sha == CSS_SHA256)
    chk("② 模板鎖定:CSS 只用模板 15 色 · 字級(font 宣告)只用 19 / 11 / 9.5 / 9 / 8 px · 三種字型(JhengHei · Cormorant · Consolas)",
        colors <= set(PALETTE) and sizes == {float(x) for x in SIZES_PX} and F_BODY in _CSS and F_DISP in _CSS and F_MONO in _CSS)
    exp = {"2026E": ("2026", "est"), "Dec-26F": ("2026-12", "est"), "Dec-24A": ("2024-12", "act"), "12/25": ("2025-12", "act"), "12/27e": ("2027-12", "est"),
           "FY26E": ("2026", "est"), "FY24": ("2024", "act"), "26E": ("2026", "est"), "2026(F)": ("2026", "est"), "2025CT": ("2025", "est"),
           "2024": ("2024", "act"), "2026": ("2026", "est"), "Mar-26": ("2026-03", "act"), "1Q26": ("2026-03", "act"), "2Q26E": ("2026-06", "est"), "2026-05-20": ("2026-05-20", "est"), "abc": ("abc", "")}
    got = {k: norm_period(k, "2026-05-20") for k in exp}
    chk("③ 期間一律 YYYY / YYYY-MM / YYYY-MM-DD · E / F / CT = 預估 · A = 實際 · 沒標的照財年末是否早於報告日", got == exp)
    chk("④ 日期:2026/5/2 → 2026-05-02 · ISO UTC 2026-11-01T17:30:00Z → 台北 2026-11-02 · 讀不出 → 空",
        norm_date("2026/5/2") == "2026-05-02" and norm_date("2026-11-01T17:30:00Z") == "2026-11-02" and norm_date("2026-11-01T01:19:00+00:00") == "2026-11-01" and norm_date("x") == "")
    hol = {"2026-10-09"}
    a = _dt.date(2026, 11, 3)
    chk("⑤ 時效:法定財報日(11/03 → 最近 08-14)之前 → 過期 · 30 交易日內 → 有效 · 超過 30 → 過期 · 休市日不算",
        latest_deadline(a) == _dt.date(2026, 8, 14) and freshness("2026-08-13", a, hol)[0] == "過期" and freshness("2026-10-20", a, hol)[0] == "有效"
        and freshness("2026-09-01", a, hol)[0] == "過期" and "> 30" in freshness("2026-09-01", a, hol)[1]
        and trading_days(_dt.date(2026, 10, 5), _dt.date(2026, 10, 12), hol) == 4 and latest_deadline(_dt.date(2026, 2, 1)) == _dt.date(2025, 11, 14)
        and freshness("", a, hol)[0] == "")
    chk("⑥ 券商英文縮寫:凱基 KGI · Goldman Sachs GS · J.P. Morgan JPM · 中信 CTBC · Macquarie MQ · 對不到照原文並標記",
        broker_abbr("凱基") == ("KGI", True) and broker_abbr("Goldman Sachs") == ("GS", True) and broker_abbr("J.P. Morgan") == ("JPM", True)
        and broker_abbr("中信") == ("CTBC", True) and broker_abbr("macquarie") == ("MQ", True) and broker_abbr("某某投顧") == ("某某投顧", False))
    chk("⑦ Source:FinancialAligned HISTORY → 歷史 TWSE/TPEX · FinancialData 2026E → 報告預估 · 2024A → 報告實際 · BasicInfo → 報告 · Rejected / Combined 各自",
        source_of("FinancialAligned", {"VALUE_SOURCE": "HISTORY(覆蓋)", "PERIOD": "2024"}) == "歷史 TWSE/TPEX" and source_of("FinancialData", {"PERIOD": "2026E", "REPORT_DATE": "2026-05-01"}) == "報告預估"
        and source_of("FinancialData", {"PERIOD": "2024A"}) == "報告實際" and source_of("BasicInfo", {}) == "報告" and source_of("Rejected", {}) == "報告(未過驗證)" and "共識" in source_of("Combined", {}))
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "VIA"
        v2 = root / "VIA_Reports" / "vrn2"
        PRIOR._fixture_v2(v2)
        vdf = root / "functional modules" / "VDF"
        vdf.mkdir(parents=True)
        (vdf / "VDF_MDL001_TWEquityEngine_shax.py").write_text('import os\nTW_KNOWN_HOLIDAYS_2025_2026 = {"2026-10-09", "2026-01-01"}\nprint("never run")\n', encoding="utf-8")
        hs, why = vdf_holidays(root)
        chk("⑧ 休市表從 VDF 檔用 ast 讀(不 import · 不執行)", hs == {"2026-10-09", "2026-01-01"} and "唯讀借用" in why)
        lk = lookups(v2)
        chk("⑨ 名稱 / Yahoo 代號對照:Combined 名稱(合成公司0)補 · 冊內有的照冊", lk["nf"].get("A-1101.pdf") == "合成公司0" and lk["nt"].get("2330") == "合成公司1")
        base = ('<!DOCTYPE html><html><head><title>VRN</title><style>:root{}</style></head><body><main>'
                '<section class="tabsec" data-tab="data"><table><thead id="dsHead"></thead></table></section></main>'
                '<script>window.VRN2_DATA = {"dsOrder":[],"books":{}};</script><script>(function(){\n'
                "  var HDR = {TICKER:'Ticker Symbol / 股票代號'}; function hdr(c){ return HDR[c] || c; } function cell(r, c, ds){ return '<td>' + r[c] + '</td>'; }\n"
                "  function renderData(){ var R = rows(st.ds), C = cols(st.ds), n = 1; var th = C.map(function(c){ return hx(hdr(c)); }); var tb = R.map(function(r){ return C.map(function(c){ return cell(r, c, st.ds); }); }); }\n"
                "  if (a === 'csvAll') { dl('x', csv(R, cols(st.ds), true)); } else if (a === 'extract') { X = 1; dl(nm, JSON.stringify({rows: X}, null, 1)); dl(nm, csv(X, cols(ds), true)); }\n"
                "  if (st.tab === 'data') { data = rows(st.ds); C = cols(st.ds); } else if (st.tab === 'export') { data = xrows(); C = cols($('#xDs').value); }\n"
                "  setTab('summary'); renderData(); renderX(); selCount(); fitStats();\n})();</script></body></html>")
        page = PRIOR.augment(base, v2)
        got, note = augment108(page, root, v2, _dt.date(2026, 11, 3))
        chk("⑩ 頁面:模板 CSS 在 v0107 之後 · VRN2_WB108 資料在 VRN2_DATA 前 · 顯示層在開機前 · 八個錨點都換上 · VRN2_DATA 一字不改",
            got.count('id="wb108-tpl"') == 1 and got.index('id="wb107-css"') < got.index('id="wb108-tpl"') and got.index("window.VRN2_WB108") < got.index("window.VRN2_DATA")
            and got.index("function w8cell(") < got.index("setTab('summary')") and "C = w8cols(st.ds, cols(st.ds))" in got and "w8cell(r, c, st.ds)" in got
            and "csv(w8src(R, st.ds), cols(st.ds).concat(['SOURCE']), true)" in got and "rows: w8src(X, ds)}" in got and '{"dsOrder":[],"books":{}}' in got and "沒接上" not in note)
        chk("⑪ Basic 合併卡重排:時效欄在報告日左邊 · Ticker / YFinance · Name 緊接 · 券商縮寫 · Source 最後 · id 照舊 wb107b",
            got.count('id="wb107b"') == 1 and "Workbench v0108" in got and got.index("Freshness / 時效") < got.index("Report Date / 報告日期") < got.index("Ticker / YFinance")
            < got.index("Company Name / 公司名稱") < got.index("Broker / 券商") and got.index("Source / 來源") > got.index("YFinance Median"))
        chk("⑫ 重入不重複 · 前版版型變了(錨點不在)→ 顯示層不接 · 頁照出並寫原因", augment108(got, root, v2)[0] == got
            and "沒接上" in augment108(PRIOR.augment("<html><head><title>x</title></head><body><main>y</main></body></html>", v2), root, v2)[1])
    n = 12
    print("[%s] %s %s 自測 %s(%d 項)" % ("GREEN" if not fails else "RED", DISPLAY_NAME, VERSION, "全過" if not fails else "不過:%s" % "; ".join(fails), n))
    return 0 if not fails else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        return selftest()
    if argv and argv[0] == "logo":
        return PRIOR.main(argv)
    import argparse
    import os
    ap = argparse.ArgumentParser(prog="VRN2_Workbench_v0108")
    ap.add_argument("verb", nargs="?", default="render")
    ap.add_argument("--root", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--logo", default=None)
    a = ap.parse_args(argv)
    if a.verb != "render":
        return PRIOR.main(argv)
    root = Path(a.root) if a.root else (os.environ.get("VIA_ROOT") and Path(os.environ["VIA_ROOT"])) or HERE.parent.parent
    path = render(root, a.out, a.logo)
    print("[GREEN] %s %s(前版 v0107)· %s" % (DISPLAY_NAME, VERSION, path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
