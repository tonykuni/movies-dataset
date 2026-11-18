#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_ENG049_ContentReconcile v0105 — v0104 薄尾(前版一字不動):個股統一矩陣 + 非個股分類矩陣(matrix 動詞)。

操作員令(2026-11-13):「將個股報告 VRN 除了財務數據驗證外 BASIC INFO + SUMMARY 整合成一個矩陣 + 各類非個股報告矩陣重新整合」
「FINANCIAL DATA 驗證方式已有請檢查 · 有歷史數據就蓋過」。

個股統一矩陣 —— 一份報告一列,欄序照操作員指定:
  REPORT DATE · FILENAME · FORMAT · SIZE(MB) · BROKER · ANALYST · TICKER · YFINANCE TICKER · BLOOMBERG TICKER · NAME · RATING ·
  REPORT TARGET PRICE · FACTSET TARGET PRICE · YFINANCE TARGET PRICE · ADJ CLOSE · VALID STATUS ·
  {Y0,Y1,Y2} × DILUTED EPS / BVPS / DPS / ROE / DILUTED EPS GROWTH RATE / PER / PBR / CASH YIELD · TOPIC & SUMMARY(四點)· 燈 · 缺漏
  年度預設 = 今年起三年(--years 2026,2027,2028 可改)。

財報值的來源與驗證(沿用既有,不另發明):
  ① 報告值只收 VRN2_FinancialData 裡 VERIFY 有證據的列(對欄 pypdfium2 / 轉置表 pdfplumber 再驗);VERIFY 空的不收,記「未驗證」數。
  ② 有歷史數據就蓋過(照 VRN2_HistoryAlign 規則):歷史來源 = VDF 1-6 FinancialModel(只讀)+ VRN2_Market_latest.json。
     重疊年度的 EPS 至少一期差 ≤ 3% → 同公司同單位 → 歷史值蓋過報告值(來源標「歷史」);
     重疊年度全部差 > 3% → 不蓋,標 HIST_CONFLICT 給人看;沒有重疊年度 → 歷史值直接補上(那幾年報告本來就沒有)。
  ③ 報告沒印的比率才推算,且標「推算」:PER = ADJ CLOSE ÷ EPS · PBR = ADJ CLOSE ÷ BVPS · CASH YIELD = DPS ÷ ADJ CLOSE ·
     EPS GROWTH = EPS(y) ÷ EPS(y-1) − 1 · BVPS = 股東權益總額 ÷(股本 ÷ 10,台股面額 10 元)· ROE = 稅後純益 ÷ 股東權益總額。
     DPS 不從現金流量表推(發放現金股利屬前一年度盈餘,年度對不上)。
  每格的來源存在 JSON 的 _SRC(報告 / 歷史 / 推算 / VDF清單 / 共識冊 / SSOT 候選),HTML 滑鼠移上去看得到。

VALID STATUS(兩個月內 / 財報公布前):規則同 VRN2_Workbench v0108 的時效欄,期間改為操作員本令的兩個月 ——
  報告日早於最近一個法定財報公布日(3/31 · 5/15 · 8/14 · 11/14)→ 過期(較新的官方財報已公布);距今超過 2 個月 → 過期;否則有效。

非個股矩陣(重新整合)—— 一份一列,先依類別分組(產業 / 晨會 / 市場策略 / 海外市場 / 未分類),欄:
  REPORT DATE · FILENAME · FORMAT · SIZE(MB) · BROKER · ANALYST · CATEGORY · TYPE · SUBJECT · MAIN INDUSTRY · DIRECTION · HORIZON ·
  VALID STATUS · MENTIONED TICKERS · KEY POINT 1~4 · EVIDENCE · VERBATIM · STATUS · 燈。

唯讀:只讀 SSOT v2 · VIA_Reports/vrn2/output · VIA_Reports/vrn2/nonstock · VDF 清單與 FinancialModel(只讀互監,不改 VDF 檔);
只寫 VIA_Reports/vrn_reconcile_runs/matrix_<ts>.{json,html} + _stock / _nonstock 的 .csv(與 .parquet,有 pandas 時)。
零網路 · 零落庫 · 不用 TA-Lib · 不寫同意閘。FactSet / YFinance 目標價只讀 VRN-2 共識冊(VRN2_Combined),本版不出網去抓。
用法:py VRN_ENG049_ContentReconcile_v0105.py matrix [--ssot F.jsonl] [--out-dir D] [--nonstock-dir D] [--input-dir D …]
       [--vdf-dir D] [--years 2026,2027,2028] [--asof YYYY-MM-DD] [--json] [--no-write] · 其餘動詞照 v0104 · --selftest
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
import datetime as _dt
import html
import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path

VERSION = "v0105"
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

STATUTORY = [(3, 31), (5, 15), (8, 14), (11, 14)]   # 年報 · Q1 · Q2 · Q3 法定公布期限(同 VRN2_Workbench v0108)
VALID_MONTHS = 2
METRICS = [  # (欄名, 報告列名正則)—— 比率類的「%」值照原樣收(5.2 = 5.2%)
    ("DILUTED EPS", r"每股(稅後)?盈餘|eps"),
    ("BVPS", r"^每股淨值|^bvps\b|^book value per share"),
    ("DPS", r"^每股(現金)?股利|^現金股利$|^dps\b|^dividend per share"),
    ("ROE", r"^roe\b|^股東權益報酬率|^權益報酬率"),
    ("DILUTED EPS GROWTH RATE", r"^(每股盈餘|eps)\s*(成長率|growth)"),
    ("PER", r"^本益比|^per?\b|^p/?e\b"),
    ("PBR", r"^股價淨值比|^pbr?\b|^p/?b\b"),
    ("CASH YIELD", r"^(現金)?殖利率|^(cash |dividend )?yield"),
]
BASE_COLS = ["REPORT DATE", "FILENAME", "FORMAT", "SIZE(MB)", "BROKER", "ANALYST", "TICKER", "YFINANCE TICKER", "BLOOMBERG TICKER", "NAME",
             "RATING", "REPORT TARGET PRICE", "FACTSET TARGET PRICE", "YFINANCE TARGET PRICE", "ADJ CLOSE", "VALID STATUS"]
TAIL_COLS = ["TOPIC & SUMMARY", "燈", "缺漏"]
NS_COLS = ["REPORT DATE", "FILENAME", "FORMAT", "SIZE(MB)", "BROKER", "ANALYST", "CATEGORY", "TYPE", "SUBJECT", "MAIN INDUSTRY", "DIRECTION",
           "HORIZON", "VALID STATUS", "MENTIONED TICKERS", "KEY POINT 1", "KEY POINT 2", "KEY POINT 3", "KEY POINT 4", "EVIDENCE", "VERBATIM",
           "STATUS", "燈"]
NS_CATEGORY = [("產業", {"INDUSTRY_REPORT", "AI", "PCB_SUBSTRATE", "THERMAL", "MEMORY", "AUTOMATION_ROBOTICS", "SEMICONDUCTOR"}),
               ("晨會", {"MORNING_MEETING", "INVESTMENT_MORNING_NOTE"}),
               ("市場策略", {"MARKET_STRATEGY", "FUTURES"}),
               ("海外市場", {"US_MARKET", "JAPAN_MARKET", "HK_MARKET", "OVERSEAS_OUTLOOK"})]
CORE = ["TICKER", "NAME", "RATING", "REPORT TARGET PRICE", "ADJ CLOSE"]


def __getattr__(name):
    return getattr(PRIOR, name)


def stock_cols(years: list) -> list:
    return BASE_COLS + [f"{y} {m}" for m, _ in METRICS for y in years] + TAIL_COLS


# ---------- 小工具 ----------
def num(v):
    if v in (None, "", "—", "-", "N/A", "NA"):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(",", "").replace("%", "")
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    try:
        f = float(s)
    except ValueError:
        return None
    return -f if neg else f


def fmt(v, kind="num") -> str:
    if v is None:
        return "—"
    if kind == "pct":
        return f"{v:.2f}%"
    return f"{v:,.2f}"


def year_of(period) -> int | None:
    s = str(period or "")
    m = re.search(r"(20\d{2})", s) or re.search(r"FY\s?(\d{2})\b", s, re.I)
    if not m:
        return None
    y = int(m.group(1))
    return y + 2000 if y < 100 else y


def norm_date(v) -> str:
    s = str(v or "").strip()
    m = re.search(r"(20\d{2})[-/.]?(\d{1,2})[-/.]?(\d{1,2})", s)
    if not m:
        return ""
    try:
        return _dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
    except ValueError:
        return ""


def latest_deadline(asof: _dt.date) -> _dt.date:
    return max(_dt.date(y, m, d) for y in (asof.year - 1, asof.year) for m, d in STATUTORY if _dt.date(y, m, d) <= asof)


def add_months(d: _dt.date, n: int) -> _dt.date:
    y, m = divmod(d.month - 1 + n, 12)
    y, m = d.year + y, m + 1
    for day in (d.day, 30, 29, 28):
        try:
            return _dt.date(y, m, day)
        except ValueError:
            continue
    return d


def validity(report_date, asof: _dt.date) -> tuple:
    rd = norm_date(report_date)
    if not rd:
        return "—", "報告日讀不出"
    d = _dt.date.fromisoformat(rd)
    dl = latest_deadline(asof)
    if d < dl:
        return "過期", f"報告日在法定財報日 {dl.isoformat()} 之前(較新的官方財報已公布)"
    if add_months(d, VALID_MONTHS) < asof:
        return "過期", f"距今超過 {VALID_MONTHS} 個月"
    return "有效", f"{VALID_MONTHS} 個月內 · 最近法定財報日 {dl.isoformat()}"


def file_info(name: str, dirs: list) -> tuple:
    ext = Path(name).suffix.lower().lstrip(".")
    fmt_ = {"pdf": "PDF", "docx": "WORD", "doc": "WORD", "txt": "TEXT", "png": "IMAGE", "jpg": "IMAGE", "jpeg": "IMAGE", "msg": "MSG",
            "eml": "MSG", "xlsx": "EXCEL", "pptx": "PPT"}.get(ext, ext.upper() or "—")
    for d in dirs:
        p = Path(d) / name
        if p.is_file():
            return fmt_, round(p.stat().st_size / 1048576, 2)
    return fmt_, None


def input_dirs(extra: list) -> list:
    out = list(extra)
    hist = VIA / "VIA_Reports" / "vrn2" / "VRN2_Input_History.jsonl"
    if hist.is_file():
        for line in hist.read_text(encoding="utf-8", errors="replace").splitlines()[-20:]:
            try:
                sd = json.loads(line).get("source_dir")
            except ValueError:
                continue
            if sd and sd not in out:
                out.append(sd)
    out += [str(HERE / "tw_stock_report_input"), str(HERE / "staging" / "input")]
    return [d for d in out if Path(d).is_dir()]


# ---------- 歷史與清單(只讀 VDF / VRN-2 市場冊) ----------
def _read_table(p: Path) -> list:
    try:
        if p.suffix == ".parquet":
            import pandas as pd
            return pd.read_parquet(p).to_dict("records")
        if p.suffix == ".csv":
            with open(p, encoding="utf-8-sig") as fh:
                return list(csv.DictReader(fh))
    except Exception:
        return []
    return []


def load_vdf(vdf_dir: Path) -> dict:
    """{ticker: {"name", "yf", "bbg", "adj": (date, close), "hist": {(metric, year): value}}} —— VDF 自報的只讀互監。"""
    out = {}

    def slot(t):
        t = re.sub(r"\.(TW|TWO)$", "", str(t or "").strip().upper())
        return out.setdefault(t, {"hist": {}}) if t else {"hist": {}}
    lists = sorted((vdf_dir / "0-1-TWStockList").glob("tw_stock_list_*.parquet")) if vdf_dir.is_dir() else []
    for r in _read_table(lists[-1]) if lists else []:
        s = slot(r.get("ticker"))
        s.update({"name": r.get("name") or "", "yf": r.get("yf_ticker") or "", "bbg": r.get("bloomberg_ticker") or ""})
    fm = vdf_dir / "1-6-FinancialModel"
    for r in _read_table(fm / "income_statement_annual.parquet"):
        y, v = year_of(r.get("period_end")), num(r.get("Diluted EPS"))
        if y and v is not None:
            slot(r.get("ticker"))["hist"][("DILUTED EPS", y)] = v
    for r in _read_table(fm / "ratios_annual.parquet"):
        y, v = year_of(r.get("period_end")), num(r.get("roe_pct"))
        if y and v is not None:
            slot(r.get("ticker"))["hist"][("ROE", y)] = v
    for r in _read_table(fm / "daily_history.parquet"):
        c, d = num(r.get("Adj Close")), str(r.get("date") or "")[:10]
        s = slot(r.get("ticker"))
        if c is not None and d >= (s.get("adj") or ("", 0))[0]:
            s["adj"] = (d, c)
    mk = VIA / "VIA_Reports" / "vrn2" / "market" / "VRN2_Market_latest.json"
    try:
        m = json.loads(mk.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        m = {}
    for r in (m.get("rows") or m.get("history") or []) if isinstance(m, dict) else []:
        y, v = year_of(r.get("PERIOD") or r.get("period")), num(r.get("EPS") or r.get("DILUTED_EPS"))
        if y and v is not None:
            slot(r.get("TICKER") or r.get("ticker"))["hist"][("DILUTED EPS", y)] = v
    out.pop("", None)
    return out


# ---------- 財報值:驗證過的報告值 → 歷史蓋過 → 推算 ----------
SKIP_RX = r"成長|年增|增減|yoy|growth|稅前|pre-?tax"     # 年增率表、稅前 EPS 不當成 EPS 本值
RAW_ALIAS = {"股東權益總額": ("股東權益總額", "權益總計", "權益總額", "母公司業主權益"), "股本": ("股本", "普通股股本"),
             "稅後純益": ("稅後純益", "母公司業主-稅後純益", "本期淨利")}


def eps_rank(item: str) -> int:
    """EPS 候選列的優先序(小的先):稀釋 / 調整後 → 有單位或「稅後」的本值 → 只寫每股盈餘 / EPS → 公告基本。"""
    s = item.lower()
    if re.search(r"稀釋|diluted|調整後", s):
        return 0
    if re.search(r"\(元\)|\(twd\)|\(nt\$?\)|稅後", s) and "基本" not in s:
        return 1
    return 3 if re.search(r"基本|basic", s) else 2


def report_values(fin_rows: list) -> tuple:
    vals, raw, unverified, best = {}, {}, 0, {}
    for r in fin_rows:
        item, y, v = str(r.get("ITEM") or "").strip(), year_of(r.get("PERIOD")), num(r.get("VALUE"))
        if y is None or v is None:
            continue
        if not str(r.get("VERIFY") or "").strip():
            unverified += 1
            continue
        key = re.sub(r"\s+", "", item)
        for canon, names in RAW_ALIAS.items():
            if key in names:
                raw.setdefault((canon, y), v)
        if re.search(SKIP_RX, item + " " + str(r.get("SECTION") or ""), re.I):
            continue
        for m, rx in METRICS:
            if not re.search(rx, item, re.I):
                continue
            rank = eps_rank(item) if m == "DILUTED EPS" else 0
            if (m, y) not in best or rank < best[(m, y)]:
                best[(m, y)] = rank
                vals[(m, y)] = (v, f"報告「{item}」(" + str(r.get("VERIFY"))[:20] + ")")
            break
    return vals, raw, unverified


def apply_history(vals: dict, hist: dict) -> tuple:
    if not hist:
        return vals, "無歷史"
    overlap = [(k, v) for k, v in hist.items() if k[0] == "DILUTED EPS" and k in vals and vals[k][0]]
    if overlap and not any(abs(hv / vals[k][0] - 1) <= 0.03 for k, hv in overlap):
        return vals, "HIST_CONFLICT(重疊年度 EPS 全部差 > 3%,不蓋)"
    out = dict(vals)
    for k, hv in hist.items():
        out[k] = (hv, "歷史")
    return out, f"歷史蓋過 {len(hist)} 格" + (f"(對上 {len(overlap)} 期)" if overlap else "(無重疊年度,直接補)")


def derive(vals: dict, raw: dict, years: list, adj) -> dict:
    out = dict(vals)
    for y in set(years) | {years[0] - 1}:
        eq, cap, ni = raw.get(("股東權益總額", y)), raw.get(("股本", y)), raw.get(("稅後純益", y))
        if ("BVPS", y) not in out and eq and cap:
            out[("BVPS", y)] = (eq / (cap / 10), "推算(權益÷股本/10)")
        if ("ROE", y) not in out and eq and ni is not None:
            out[("ROE", y)] = (ni / eq * 100, "推算(稅後純益÷權益)")
    for y in years:
        e, e0 = out.get(("DILUTED EPS", y)), out.get(("DILUTED EPS", y - 1))
        if ("DILUTED EPS GROWTH RATE", y) not in out and e and e0 and e0[0]:
            out[("DILUTED EPS GROWTH RATE", y)] = ((e[0] / e0[0] - 1) * 100, "推算(EPS 年增)")
        if adj:
            if ("PER", y) not in out and e and e[0]:
                out[("PER", y)] = (adj / e[0], "推算(ADJ CLOSE÷EPS)")
            b = out.get(("BVPS", y))
            if ("PBR", y) not in out and b and b[0]:
                out[("PBR", y)] = (adj / b[0], "推算(ADJ CLOSE÷BVPS)")
            d = out.get(("DPS", y))
            if ("CASH YIELD", y) not in out and d:
                out[("CASH YIELD", y)] = (d[0] / adj * 100, "推算(DPS÷ADJ CLOSE)")
    return out


# ---------- 列 ----------
def _first(rows: list) -> dict:
    return rows[0] if rows else {}


def stock_row(rec: dict, outs: dict, vdf: dict, years: list, asof: _dt.date, dirs: list) -> dict:
    doc = rec.get("source_document", "")
    b = _first(PRIOR.match(doc, outs.get("BasicInfo") or []))
    s = _first(PRIOR.match(doc, outs.get("Summary") or []))
    c = _first(PRIOR.match(doc, outs.get("Combined") or []))
    fin = PRIOR.match(doc, outs.get("FinancialData") or [])
    src, row = {}, {}

    def put(col, v, where):
        if v not in (None, "", "—"):
            row[col], src[col] = v, where
        else:
            row[col] = "—"
    tk = str(b.get("TICKER") or PRIOR._txt(rec.get("final_primary_ticker_proposals")).split(";")[0]).strip()
    v = vdf.get(tk.upper(), {})
    rd = norm_date(b.get("REPORT_DATE") or rec.get("report_date_guess"))
    fmt_, size = file_info(doc, dirs)
    put("REPORT DATE", rd, "輸出冊" if b.get("REPORT_DATE") else "SSOT")
    put("FILENAME", doc, "SSOT")
    put("FORMAT", fmt_, "副檔名")
    put("SIZE(MB)", size, "輸入夾")
    put("BROKER", b.get("BROKER_EN") or b.get("BROKER") or PRIOR._txt(rec.get("final_broker_proposal")), "輸出冊" if b else "SSOT")
    put("ANALYST", b.get("ANALYST"), "輸出冊")
    put("TICKER", tk, "輸出冊" if b.get("TICKER") else "SSOT")
    put("YFINANCE TICKER", b.get("YFINANCE_TICKER") or v.get("yf"), "輸出冊" if b.get("YFINANCE_TICKER") else "VDF清單")
    put("BLOOMBERG TICKER", b.get("BLOOMBERG_TICKER") or v.get("bbg") or (f"{tk} TT" if tk else ""),
        "輸出冊" if b.get("BLOOMBERG_TICKER") else ("VDF清單" if v.get("bbg") else "推算(代號 + TT)"))
    put("NAME", b.get("NAME") or v.get("name"), "輸出冊" if b.get("NAME") else "VDF清單")
    put("RATING", b.get("RATING") or PRIOR._txt(rec.get("rating_content_guess")), "輸出冊" if b.get("RATING") else "SSOT")
    tp = num(b.get("TARGET_PRICE"))
    tp_src = "輸出冊"
    if tp is None:
        cand = [num(x) for x in re.split(r"[;/ ]+", PRIOR._txt(rec.get("validated_target_prices_review_ready"))) if num(x)]
        tp, tp_src = (cand[0], "SSOT 已驗目標價") if len(cand) == 1 else (None, "")
    put("REPORT TARGET PRICE", fmt(tp) if tp is not None else None, tp_src)
    put("FACTSET TARGET PRICE", fmt(num(c.get("FACTSET_TARGET_PRICE_MEDIAN"))) if num(c.get("FACTSET_TARGET_PRICE_MEDIAN")) is not None else None, "共識冊")
    put("YFINANCE TARGET PRICE", fmt(num(c.get("YFINANCE_TARGET_PRICE_MEDIAN"))) if num(c.get("YFINANCE_TARGET_PRICE_MEDIAN")) is not None else None, "共識冊")
    adj = num(b.get("ADJ_CLOSE"))
    adj_src = "輸出冊"
    if adj is None and v.get("adj"):
        adj, adj_src = v["adj"][1], f"VDF 股價({v['adj'][0]})"
    put("ADJ CLOSE", fmt(adj) if adj is not None else None, adj_src)
    st, why = validity(rd, asof)
    put("VALID STATUS", st if st != "—" else None, why)
    vals, raw, unver = report_values(fin)
    vals, hnote = apply_history(vals, v.get("hist") or {})
    vals = derive(vals, raw, years, adj)
    for m, _ in METRICS:
        for y in years:
            hit = vals.get((m, y))
            kind = "pct" if m in ("ROE", "DILUTED EPS GROWTH RATE", "CASH YIELD") else "num"
            put(f"{y} {m}", fmt(hit[0], kind) if hit else None, hit[1] if hit else "")
    pts = [str(s.get(f"POINT_{i}") or "").strip() for i in range(1, 5)]
    put("TOPIC & SUMMARY", " ‖ ".join(f"{i}. {p}" for i, p in enumerate(pts, 1) if p) or c.get("TOPIC & SUMMARY"), "摘要冊")
    miss = [k for k in CORE if row.get(k) == "—"]
    fin_cells = sum(1 for k in row if re.match(r"^20\d{2} ", k) and row[k] != "—")
    if not (b or s or fin):
        lamp = "NODATA"
    elif "HIST_CONFLICT" in hnote or (fin and not vals and unver):
        lamp = "RED"
    elif miss or not fin_cells or not any(pts):
        lamp = "YELLOW"
    else:
        lamp = "GREEN"
    row["燈"] = lamp
    row["缺漏"] = " · ".join(([f"缺 {', '.join(miss)}"] if miss else []) + [f"財報格 {fin_cells}", hnote]
                           + ([f"未驗證值 {unver}(不收)"] if unver else []) + ([] if (b or s or fin) else ["本輪 VRN-2 輸出冊沒有這份"]))
    row["_SRC"] = src
    return row


def ns_category(rt: str) -> str:
    for name, keys in NS_CATEGORY:
        if rt in keys:
            return name
    return "未分類"


def nonstock_row(rec: dict, outs: dict, asof: _dt.date, dirs: list) -> dict:
    doc = rec.get("source_document", "")
    n = _first(PRIOR.match(doc, outs.get("NonStock") or []))
    rt = PRIOR._txt(rec.get("final_report_type_proposal")) or PRIOR._txt(rec.get("report_type_content_guess"))
    rd = norm_date(n.get("REPORT_DATE") or rec.get("report_date_guess"))
    fmt_, size = file_info(doc, dirs)
    st, why = validity(rd, asof)
    mt = [t for t in PRIOR._txt(rec.get("mentioned_tickers_review_only")).split(";") if t]

    def g(*ks):
        for k in ks:
            if n.get(k) not in (None, ""):
                return PRIOR._short(n.get(k), 120)
        return "—"
    status = str(n.get("STATUS") or "")
    pts = sum(1 for i in range(1, 5) if str(n.get(f"POINT_{i}") or "").strip())
    lamp = ("NODATA" if not n else "GREEN" if status == "PASS" and pts >= 3 else "YELLOW" if status in ("PASS", "REVIEW", "STOCK_LANE")
            else "NODATA" if status in ("NODATA", "ABSENT") else "RED")
    return {"REPORT DATE": rd or "—", "FILENAME": doc, "FORMAT": fmt_, "SIZE(MB)": size if size is not None else "—",
            "BROKER": g("BROKER_EN", "BROKER") if n else (PRIOR._txt(rec.get("final_broker_proposal")) or "—"), "ANALYST": g("ANALYST"),
            "CATEGORY": ns_category(rt), "TYPE": rt or "—", "SUBJECT": PRIOR._txt(rec.get("subject_guess")) or "—",
            "MAIN INDUSTRY": g("MAIN_INDUSTRY"), "DIRECTION": g("DIRECTION"), "HORIZON": g("HORIZON"), "VALID STATUS": st,
            "MENTIONED TICKERS": (f"{len(mt)} 檔:" + ", ".join(mt[:12]) + (" …" if len(mt) > 12 else "")) if mt else "—",
            **{f"KEY POINT {i}": g(f"POINT_{i}") for i in range(1, 5)},
            "EVIDENCE": g("EVIDENCE_COUNT"), "VERBATIM": g("VERBATIM"), "STATUS": status or "—", "燈": lamp,
            "_SRC": {"VALID STATUS": why, "CATEGORY": f"類型 {rt or '空'} → {ns_category(rt)}"}}


def build_matrix(records: list, outs: dict, vdf: dict, years: list, asof: _dt.date, dirs: list) -> dict:
    stock = [stock_row(r, outs, vdf, years, asof, dirs) for r in records if PRIOR.is_stock(r)]
    ns = [nonstock_row(r, outs, asof, dirs) for r in records if not PRIOR.is_stock(r)]
    order = [c for c, _ in NS_CATEGORY] + ["未分類"]
    ns.sort(key=lambda r: (order.index(r["CATEGORY"]), r["REPORT DATE"]))
    stock.sort(key=lambda r: (r["TICKER"], r["REPORT DATE"]))
    return {"stock": stock, "nonstock": ns}


def tally(rows: list) -> dict:
    lamps = {}
    for r in rows:
        lamps[r["燈"]] = lamps.get(r["燈"], 0) + 1
    return {"records": len(rows), "lamps": lamps}


def render_matrix(mx: dict, years: list, meta: dict) -> str:
    color = {"GREEN": "#2e7d32", "YELLOW": "#b26a00", "RED": "#c62828", "NODATA": "#6b7280", "有效": "#2e7d32", "過期": "#c62828"}

    def cell(r, c):
        v = str(r.get(c, "—"))
        tip = html.escape(str((r.get("_SRC") or {}).get(c, "")))
        sty = f' style="color:{color[v]};font-weight:600"' if v in color else ""
        mark = ' class="d"' if "推算" in tip else (' class="h"' if tip == "歷史" else "")
        return f'<td title="{tip}"{sty}{mark}>{html.escape(v)}</td>'

    def table(title, rows, groups):
        h1 = "".join(f'<th colspan="{len(cs)}">{html.escape(g)}</th>' for g, cs in groups)
        h2 = "".join(f"<th>{html.escape(c)}</th>" for _, cs in groups for c in cs)
        body = "".join("<tr>" + "".join(cell(r, c) for _, cs in groups for c in cs) + "</tr>" for r in rows)
        t = tally(rows)
        return (f"<h3>{html.escape(title)} · {t['records']} 份 · 燈 {html.escape(json.dumps(t['lamps'], ensure_ascii=False))}</h3>"
                f'<div class="w"><table><tr>{h1}</tr><tr>{h2}</tr>{body}</table></div>')
    sg = [("BASIC INFO", BASE_COLS)] + [(m, [f"{y} {m}" for y in years]) for m, _ in METRICS] + [("SUMMARY · 燈", TAIL_COLS)]
    ng = [("檔案", NS_COLS[:6]), ("分類", NS_COLS[6:12]), ("時效 · 提及", NS_COLS[12:14]), ("四重點", NS_COLS[14:18]), ("證據 · 燈", NS_COLS[18:])]
    blocks = []
    for cat in [c for c, _ in NS_CATEGORY] + ["未分類"]:
        rows = [r for r in mx["nonstock"] if r["CATEGORY"] == cat]
        if rows:
            blocks.append(table(f"非個股 · {cat}", rows, ng))
    return ("<!doctype html><meta charset=utf-8><title>VRN 報告矩陣</title><style>body{font:13px system-ui;margin:16px}"
            ".w{overflow-x:auto}table{border-collapse:collapse}td,th{border:1px solid #ccc;padding:3px 6px;white-space:nowrap;vertical-align:top}"
            "th{background:#f3f3f3}td.d{color:#5b5bd6}td.h{background:#eef7ee}</style>"
            f"<h2>VRN 報告矩陣 · {html.escape(meta['ts'])} · READ-ONLY · 零落庫</h2>"
            f"<p>SSOT {html.escape(meta['ssot'])} · 時效基準 {html.escape(meta['asof'])} · 年度 {', '.join(map(str, years))} · "
            "滑鼠移到格子看來源;藍字 = 推算 · 綠底 = 歷史蓋過 · 財報值只收 VERIFY 有證據的列</p>"
            + table("個股報告 · BASIC INFO + 財務預估 + SUMMARY", mx["stock"], sg) + "".join(blocks))


def matrix(argv: list) -> int:
    def opt(k, d=None):
        return argv[argv.index(k) + 1] if k in argv and argv.index(k) + 1 < len(argv) else d
    recs, sp = PRIOR.ssot_records(Path(opt("--ssot")) if opt("--ssot") else None)
    if not recs:
        print("[VRN-MATRIX] NODATA · 找不到 SSOT v2 記錄")
        return 2
    asof = _dt.date.fromisoformat(opt("--asof")) if opt("--asof") else _dt.date.today()
    years = [int(y) for y in opt("--years").split(",")] if opt("--years") else [asof.year, asof.year + 1, asof.year + 2]
    out_dir = Path(opt("--out-dir") or VIA / "VIA_Reports" / "vrn2" / "output")
    outs = PRIOR.outputs(out_dir, Path(opt("--nonstock-dir") or VIA / "VIA_Reports" / "vrn2" / "nonstock"))
    outs["Combined"] = PRIOR._rows(out_dir / "VRN2_Combined_latest.json")
    extra = [argv[i + 1] for i, a in enumerate(argv) if a == "--input-dir" and i + 1 < len(argv)]
    vdf = load_vdf(Path(opt("--vdf-dir") or VIA / "VIA_Reports" / "vdf_fetch" / "dict"))
    mx = build_matrix(recs, outs, vdf, years, asof, input_dirs(extra))
    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    meta = {"ts": ts, "ssot": sp.name, "asof": asof.isoformat(), "years": years, "out_dir": str(out_dir)}
    summ = {"stock": tally(mx["stock"]), "nonstock": tally(mx["nonstock"])}
    if "--no-write" not in argv:
        od = VIA / "VIA_Reports" / "vrn_reconcile_runs"
        od.mkdir(parents=True, exist_ok=True)
        (od / f"matrix_{ts}.json").write_text(json.dumps({"schema": "VIA.VRN.ReportMatrix.v1", "engine": STEM + " " + VERSION, **meta,
                                                          "summary": summ, **mx}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        for name, rows, cols in (("stock", mx["stock"], stock_cols(years)), ("nonstock", mx["nonstock"], NS_COLS)):
            with open(od / f"matrix_{ts}_{name}.csv", "w", encoding="utf-8-sig", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
                w.writeheader()
                w.writerows(rows)
            try:
                import pandas as pd
                pd.DataFrame([{c: str(r.get(c, "—")) for c in cols} for r in rows], columns=cols).to_parquet(od / f"matrix_{ts}_{name}.parquet", index=False)
            except Exception:
                pass
        (od / f"matrix_{ts}.html").write_text(render_matrix(mx, years, meta), encoding="utf-8")
        meta["files"] = str(od / f"matrix_{ts}*")
    if "--json" in argv:
        print(json.dumps({"summary": summ, **mx}, ensure_ascii=False, indent=1))
        return 0
    print(f"VRN-MATRIX · {ts} · READ-ONLY · 零落庫 · 時效基準 {asof.isoformat()} · 年度 {years}")
    print(f"[個股統一矩陣] {summ['stock']['records']} 份 · 燈 {json.dumps(summ['stock']['lamps'], ensure_ascii=False)}")
    for r in mx["stock"]:
        fc = sum(1 for k in r if re.match(r"^20\d{2} ", k) and r[k] != "—")
        print(f"  {r['燈']:<6} {r['TICKER'][:6]:<6} {r['NAME'][:8]:<8} {r['BROKER'][:10]:<10} {r['REPORT DATE']:<10} {r['VALID STATUS']:<4} "
              f"評等 {r['RATING'][:6]:<6} TP {r['REPORT TARGET PRICE'][:10]:<10} 財報格 {fc:>2} · {r['缺漏'][:70]}")
    print(f"[非個股矩陣] {summ['nonstock']['records']} 份 · 燈 {json.dumps(summ['nonstock']['lamps'], ensure_ascii=False)}")
    for cat in [c for c, _ in NS_CATEGORY] + ["未分類"]:
        rows = [r for r in mx["nonstock"] if r["CATEGORY"] == cat]
        if rows:
            print(f"  {cat} {len(rows)} 份:" + " · ".join(f"{r['FILENAME'][:28]}({r['燈']})" for r in rows[:6]) + (" …" if len(rows) > 6 else ""))
    if meta.get("files"):
        print("存證 " + meta["files"])
    return 0


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")
    a = _dt.date(2026, 11, 13)
    chk("① 時效:法定財報日(11/13 → 最近 08-14)之前過期 · 兩個月內有效 · 超過兩個月過期",
        latest_deadline(a) == _dt.date(2026, 8, 14) and validity("2026-08-13", a)[0] == "過期" and validity("2026-10-20", a)[0] == "有效"
        and validity("2026-11-15", _dt.date(2027, 1, 20))[0] == "過期" and validity("", a)[0] == "—")
    fin = [{"ITEM": "每股盈餘", "PERIOD": "2025", "VALUE": "10.0", "VERIFY": "對欄(pypdfium2)"},
           {"ITEM": "每股盈餘", "PERIOD": "2026E", "VALUE": "12.0", "VERIFY": "對欄(pypdfium2)"},
           {"ITEM": "每股盈餘", "PERIOD": "2027E", "VALUE": "15.0", "VERIFY": ""},
           {"ITEM": "股東權益總額", "PERIOD": "2026E", "VALUE": "1,000", "VERIFY": "對欄"},
           {"ITEM": "股本", "PERIOD": "2026E", "VALUE": "100", "VERIFY": "對欄"},
           {"ITEM": "稅後純益", "PERIOD": "2026E", "VALUE": "120", "VERIFY": "對欄"}]
    vals, raw, unver = report_values(fin)
    chk("② 財報只收 VERIFY 有證據的列(2027E 沒證據 → 不收,記未驗證 1)",
        vals.get(("DILUTED EPS", 2026), (0,))[0] == 12.0 and ("DILUTED EPS", 2027) not in vals and unver == 1, unver)
    mix = [{"ITEM": "每股盈餘", "PERIOD": "2023E", "VALUE": "26.06", "VERIFY": "v", "SECTION": ""},
           {"ITEM": "每股盈餘 (元)", "PERIOD": "2023E", "VALUE": "9.53", "VERIFY": "v"},
           {"ITEM": "稅前EPS", "PERIOD": "2026(F)", "VALUE": "9.9", "VERIFY": "v"}, {"ITEM": "稅後EPS", "PERIOD": "2026(F)", "VALUE": "8.1", "VERIFY": "v"},
           {"ITEM": "公告基本 EPS(元)", "PERIOD": "2027F", "VALUE": "5.0", "VERIFY": "v"}, {"ITEM": "調整後 EPS(元)", "PERIOD": "2027F", "VALUE": "4.8", "VERIFY": "v"},
           {"ITEM": "EPS (TWD)", "PERIOD": "2025", "VALUE": "3.3", "VERIFY": "v"}, {"ITEM": "權益總計", "PERIOD": "2026F", "VALUE": "500", "VERIFY": "v"}]
    mv, mraw, _ = report_values(mix)
    chk("②′ EPS 欄名各家不同:(元) 本值勝過同名年增率列 · 稅前 EPS 不收 · 調整後勝過公告基本 · EPS (TWD) 收 · 權益總計 = 股東權益總額",
        mv[("DILUTED EPS", 2023)][0] == 9.53 and mv[("DILUTED EPS", 2026)][0] == 8.1 and mv[("DILUTED EPS", 2027)][0] == 4.8
        and mv[("DILUTED EPS", 2025)][0] == 3.3 and mraw.get(("股東權益總額", 2026)) == 500, {k[1]: v[0] for k, v in mv.items()})
    v2, note = apply_history(vals, {("DILUTED EPS", 2025): 10.2, ("DILUTED EPS", 2024): 8.0})
    chk("③ 歷史蓋過:重疊年度差 ≤ 3% → 歷史值蓋過並補沒有的年度", v2[("DILUTED EPS", 2025)] == (10.2, "歷史") and ("DILUTED EPS", 2024) in v2, note)
    v3, note3 = apply_history(vals, {("DILUTED EPS", 2025): 20.0})
    chk("④ 歷史差 > 3% 全部對不上 → 不蓋 · 標 HIST_CONFLICT", v3[("DILUTED EPS", 2025)][0] == 10.0 and "HIST_CONFLICT" in note3, note3)
    d = derive(vals, raw, [2026, 2027, 2028], 120.0)
    chk("⑤ 推算:BVPS = 權益÷(股本/10) = 100 · PER = 120÷12 = 10 · PBR = 1.2 · ROE = 12% · EPS 年增 20%",
        abs(d[("BVPS", 2026)][0] - 100) < 1e-9 and abs(d[("PER", 2026)][0] - 10) < 1e-9 and abs(d[("PBR", 2026)][0] - 1.2) < 1e-9
        and abs(d[("ROE", 2026)][0] - 12) < 1e-9 and abs(d[("DILUTED EPS GROWTH RATE", 2026)][0] - 20) < 1e-9
        and all("推算" in d[k][1] for k in (("BVPS", 2026), ("PER", 2026))))
    chk("⑥ DPS 不從現金流量表推 · 沒 DPS 就沒殖利率", ("DPS", 2026) not in d and ("CASH YIELD", 2026) not in d)
    rec = {"source_document": "華南投顧-6143-振曜-1141128.pdf", "final_report_type_proposal": "COMPANY_REPORT", "final_primary_ticker_proposals": "6143",
           "report_date_guess": "2025-11-28", "final_broker_proposal": "HUANAN", "validated_target_prices_review_ready": "350"}
    outs = {"BasicInfo": [{"FILENAME": "華南投顧-6143-振曜-1141128.pdf", "TICKER": "6143", "RATING": "買進", "ANALYST": "陳逸民", "BROKER_EN": "HNS"}],
            "Summary": [{"FILENAME": "華南投顧-6143-振曜-1141128.pdf", "POINT_1": "營收成長", "POINT_2": "毛利改善", "POINT_3": "新產品"}],
            "FinancialData": [dict(r, FILENAME="華南投顧-6143-振曜-1141128.pdf") for r in fin], "Combined": []}
    vdf = {"6143": {"name": "振曜", "yf": "6143.TWO", "bbg": "6143 TT", "adj": ("2026-11-12", 240.0), "hist": {}}}
    with tempfile.TemporaryDirectory() as td:
        Path(td, "華南投顧-6143-振曜-1141128.pdf").write_bytes(b"%PDF" + b"0" * 2097152)
        r = stock_row(rec, outs, vdf, [2026, 2027, 2028], a, [td])
    cols = stock_cols([2026, 2027, 2028])
    chk("⑦ 個股列:欄序照操作員指定(REPORT DATE 起 · FILENAME · FORMAT · SIZE …)· 每欄都有值或 —",
        cols[:6] == ["REPORT DATE", "FILENAME", "FORMAT", "SIZE(MB)", "BROKER", "ANALYST"] and all(c in r for c in cols), len(cols))
    chk("⑧ 名稱 / YF 由 VDF 清單補 · 目標價由 SSOT 已驗補 · ADJ CLOSE 由 VDF 股價補 · 格式 PDF · 大小 2.0 MB",
        r["NAME"] == "振曜" and r["YFINANCE TICKER"] == "6143.TWO" and r["REPORT TARGET PRICE"] == "350.00" and r["ADJ CLOSE"] == "240.00"
        and r["FORMAT"] == "PDF" and r["SIZE(MB)"] == 2.0 and r["_SRC"]["NAME"] == "VDF清單", (r["NAME"], r["SIZE(MB)"]))
    chk("⑨ 個股列 2026 EPS 12 · PER 20(240÷12)· 過期(2025-11-28 早於 08-14)· 摘要三點 · 燈 YELLOW 以下不冒充綠",
        r["2026 DILUTED EPS"] == "12.00" and r["2026 PER"] == "20.00" and r["VALID STATUS"] == "過期" and r["TOPIC & SUMMARY"].count("‖") == 2
        and r["燈"] in ("GREEN", "YELLOW"), r["燈"])
    nr = nonstock_row({"source_document": "MS-Memory 20251204.pdf", "final_report_type_proposal": "MEMORY",
                       "mentioned_tickers_review_only": "2408;2344;", "report_date_guess": "2025-12-04"}, {"NonStock": []}, a, [])
    chk("⑩ 非個股列:MEMORY → 產業 · 沒摘要器結果 → NODATA · 提及代號 2 檔", nr["CATEGORY"] == "產業" and nr["燈"] == "NODATA"
        and nr["MENTIONED TICKERS"].startswith("2 檔") and list(nr)[:len(NS_COLS)] == NS_COLS, nr["CATEGORY"])
    with tempfile.TemporaryDirectory() as td:
        html_ = render_matrix({"stock": [r], "nonstock": [nr]}, [2026, 2027, 2028], {"ts": "t", "ssot": "s", "asof": "2026-11-13"})
        Path(td, "m.html").write_text(html_, encoding="utf-8")
        chk("⑪ HTML:個股表 + 非個股依類別分表 · 來源寫在 title", "非個股 · 產業" in html_ and 'title="VDF清單"' in html_)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑫ 不用 TA-Lib · 不出網 · 不寫同意閘", "import " + "talib" not in src and "urlopen" + "(" not in src and "VIA_NET_" + "CONSENT=" not in src)
    print(f"[selftest] {VERSION} 本版 {sum(ok)}/{len(ok)}")
    if not all(ok):
        return 1
    return PRIOR.selftest()


def main() -> int:
    a = sys.argv[1:]
    if a[:1] == ["--selftest"]:
        return selftest()
    if a[:1] == ["matrix"]:
        return matrix(a[1:])
    return PRIOR.main()


if __name__ == "__main__":
    sys.exit(main())
