#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN panorama probe · 母系統 64 件進件的十段管線全景實測（唯讀、禁網、不發明）.

Every incoming research report is pushed through the ten VRN pipeline stages the
Console models (S01 PATH_RESOLVE … S10 SUMMARIZER).  For each file and each stage
the probe reports OK / WARN / SKIP / READY / BLOCKED / FAIL together with the reason,
so the first broken segment is visible instead of an opaque red light.

* roster: the mother incoming list in ``src/lib/via/incoming-roster.ts`` or a real
  directory (``--incoming``); bytes are only touched when they exist;
* filename contract (ticker / report date / broker / rating / type / risk) mirrors
  the TypeScript VRN layer and the VIS ticker SSOT kept in ``attachments``;
* nothing that needs network, OCR models or the mother pipeline is executed: those
  stages report READY (all prerequisites present, not run) or BLOCKED with reasons;
* outputs: console matrix, ``--json``, ``--html``.  Exit code is 0 unless
  ``--strict`` is given and a FAIL exists.
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
import datetime as _dt
import hashlib
import html
import importlib.util
import json
import os
import platform
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

PROBE_NAME = "VRN_PanoramaProbe"
PROBE_VERSION = "v0101"
PROJECT_ROOT = Path(__file__).resolve().parents[3]
# v0101(母倉 批728):這支原本住在姊妹倉根(TS 主控台 + attachments/);搬回母倉後那一層不在,
#   母倉收容夾 VIA_GrokConsole_AuroraAcorn_b383 就是同一個 app 的收容副本(名冊位元相同、十段表相同)——
#   APP_ROOT 先找倉根,再找收容副本(唯讀,L03 零觸碰);兩處都沒有就照舊指倉根,缺什麼照實報 ABSENT。
APP_CANDIDATES = (
    PROJECT_ROOT,
    PROJECT_ROOT / "supportive modules" / "references" / "intake" / "VIA_GrokConsole_AuroraAcorn_b383",
)
APP_ROOT = next((c for c in APP_CANDIDATES if (c / "src" / "lib" / "via" / "incoming-roster.ts").is_file()), PROJECT_ROOT)
ROSTER_TS = APP_ROOT / "src" / "lib" / "via" / "incoming-roster.ts"
ATTACHMENTS = APP_ROOT / "attachments"
MOTHER_INCOMING_DIR = (
    "C:\\Users\\tonyk\\OneDrive\\Documents\\movies-dataset\\VeritasIntelligenceAnalytics"
    "\\functional modules\\VRN\\input\\incoming"
)

# =============================================================================
# 00. Parameters (stage table mirrors src/lib/via/catalog.ts PIPELINE)
# =============================================================================

STAGES: tuple[tuple[str, str, str], ...] = (
    ("S01", "PATH_RESOLVE", "路徑解析"),
    ("S02", "HASH_FINGERPRINT", "指紋"),
    ("S03", "DEDUP_GATE", "去重閘"),
    ("S04", "FORMAT_CLASSIFY", "格式分類"),
    ("S05", "ACCEL_MOUNT", "加速器掛載"),
    ("S06", "OCR_ROUTE", "OCR 路由"),
    ("S07", "NLP_ENRICH", "NLP 增強"),
    ("S08", "TABLE_EXTRACT", "表擷取"),
    ("S09", "FINANCIAL_SSOT", "財務 SSOT"),
    ("S10", "SUMMARIZER", "摘要"),
)
STAGE_IDS = tuple(s[0] for s in STAGES)
STATUS_ORDER = ("OK", "READY", "WARN", "SKIP", "BLOCKED", "FAIL")
STATUS_LETTER = {"OK": "O", "READY": "R", "WARN": "W", "SKIP": "S", "BLOCKED": "B", "FAIL": "F"}
STATUS_LIGHT = {"OK": "ok", "READY": "ok", "WARN": "warn", "SKIP": "idle", "BLOCKED": "warn", "FAIL": "bad"}

ALLOWED_EXT = {"pdf", "xlsx", "xls", "csv", "docx", "md", "pptx", "html", "txt"}
OFIE_EXT = {
    "pdf", "docx", "doc", "xlsx", "xls", "pptx", "ppt", "html", "htm", "md", "txt", "csv",
    "json", "xml", "rtf", "odt", "ods", "odp", "epub",
}
BRIDGE_EXT = {"docx", "doc", "pptx", "ppt", "xlsx", "xls", "msg", "html", "htm", "epub", "csv"}
NON_STOCK = (
    "Insights", "Thoughts on", "展望", "日股", "早報", "晨報", "晨會", "晨訊", "晨間", "期貨",
    "港股", "產業", "盤前", "盤勢", "美股", "解盤", "講座", "趨勢", "完善化", "Roadmap",
    "Minutes", "Brief",
)
BROKER_PREFIX: dict[str, tuple[str, str]] = {
    "MS": ("Morgan Stanley", "MS"),
    "GS": ("Goldman Sachs", "GS"),
    "JP": ("J.P. Morgan", "JPM"),
    "CITI": ("Citigroup", "CITI"),
    "CLST": ("CLSA Taiwan", "CLSA"),
    "DAIWA": ("Daiwa 大和", "DAI"),
    "UBS": ("UBS", "UBS"),
    "MQ": ("Macquarie 麥格理", "MAQ"),
    "KGI": ("凱基投顧", "KGI"),
    "CTBC": ("中國信託證券", "CTBC"),
}
BROKER_ZH: tuple[tuple[str, str, str], ...] = (
    ("兆豐", "兆豐投顧", "MKC"),
    ("凱基", "凱基投顧", "KGI"),
    ("華南", "華南投顧", "HNSC"),
    ("統一", "統一投顧", "PSC"),
    ("台新", "台新投顧", "TSC"),
    ("國泰", "國泰證期", "CT"),
    ("元大", "元大投顧", "YT"),
    ("富邦", "富邦投顧", "FB"),
    ("永豐", "永豐投顧", "SJP"),
    ("玉山", "玉山投顧", "ESB"),
    ("群益", "群益投顧", "CP"),
    ("日盛", "日盛投顧", "JS"),
    ("康和", "康和投顧", "CH"),
    ("宏遠", "宏遠投顧", "HY"),
    ("合庫", "合庫投顧", "TCB"),
    ("第一金", "第一金投顧", "FCB"),
)
BROKER_MARKERS = ("投顧", "證券", "證期", "金控", "研究部", "投資", "個股", "訪談", "晨會", "早報",
                  "期貨", "日股", "美股", "港股", "分析", "報告", "速報")
ORDINAL_RE = re.compile(r"第[一二三四五六七八九十\d]+場")
RATING_FALLBACK: dict[str, tuple[str, ...]] = {
    "BUY": ("買進", "買入", "增持", "加碼", "Buy", "Outperform", "Overweight"),
    "HOLD": ("持有", "中立", "觀望", "Hold", "Neutral", "Equal Weight"),
    "SELL": ("賣出", "減持", "減碼", "Sell", "Underperform", "Underweight"),
    "NOT_RATED": ("未評等", "未評級", "無評等", "Not Rated", "NR"),
}
YEAR_BAND = range(2021, 2031)
DATE_CUES = ("年", "Q1", "Q2", "Q3", "Q4", "H1", "H2", "FY", "上半年", "下半年", "第一季", "第二季", "第三季", "第四季")

MODULES: tuple[tuple[str, str, str], ...] = (
    ("MDL001", "VRN_MDL001_Converter*.py", "S04"),
    ("MDL002", "VRN_MDL002_LayoutExtractor*.py", "S06"),
    ("MDL003", "VRN_MDL003_TableRestorer*.py", "S08"),
    ("MDL004", "VRN_MDL004_OCR_FetchingPDFTable*.py", "S08"),
    ("MDL005", "VRN_MDL005_OCRFetchingPDFText*.py", "S08"),
    ("MDL006", "VRN_MDL006_ConsolidatorAndPhaseValidator*.py", "S09"),
    ("MDL007", "VRN_MDL007_APIDataFetcher*.py", "S09"),
    ("MDL008", "VRN_MDL008_CrossValidator*.py", "S09"),
    ("RUNNER", "VRN_Pipeline_Runner*.py", "S08"),
    ("FOUR_ENGINE", "VRN_BatchFourEngine_v*.py", "S04"),
    ("SUMMARIZER_1", "VIA_Financial_Document_Summarizer_Engine*.py", "S10"),
    ("SUMMARIZER_2", "VIA_SummarizerEngine*.py", "S10"),
    ("TICKER_SSOT", "VIS_VRN_TickerFilenameSSOT_v*.py", "S06"),
    ("TW_TICKER_RX", "VIA_TWTickerRegex.py", "S06"),
)
SSOT_FILES: tuple[str, ...] = (
    "VRN_Broker_Dict_v0100.json", "VRN_Rating_Dict_v0100.json", "VRN_TickerDate_Regex_v0100.json",
    "VRN_FinData_Synonym_v0100.json", "VRN_AnnualExtract_SSOT_v0100.json", "VRN_Method_SSOT_v0100.json",
    "VRN_Canonical_Trilingual_Fill_v0100.json", "VRN_Report_Parser_Integrated_SSOT.json",
)
DEPS: tuple[tuple[str, str], ...] = (
    ("pandas", "S08/S09 表格與 Phase 對照"),
    ("numpy", "S08 數值"),
    ("pyarrow", "S09 parquet 落盤"),
    ("polars", "S05 PS-16 PolarsLazy"),
    ("duckdb", "S09 PS-18 DuckDBScan"),
    ("xxhash", "S02 快速指紋（可退回 sha256）"),
    ("fitz", "S04/S08 PyMuPDF 轉檔與版面"),
    ("pdfplumber", "S08 表擷取"),
    ("pypdf", "S06 文字層探測"),
    ("docx", "S04 python-docx"),
    ("markitdown", "S04 docx→md 橋"),
    ("paddleocr", "S08 OCR"),
    ("pytesseract", "S08 OCR"),
    ("PIL", "S08 影像"),
    ("cv2", "S08 影像"),
    ("rapidfuzz", "S05 加速器候選"),
    ("regex", "S05 加速器候選"),
    ("psutil", "S05 加速器候選"),
)
TABLE_DEPS = ("pandas", "fitz")
S08_MODULES = ("MDL003", "MDL004")
S09_MODULES = ("MDL006",)
S10_MODULES = ("SUMMARIZER_1", "SUMMARIZER_2")

# =============================================================================
# 01. Helpers
# =============================================================================


def def_nfkc(text: str) -> str:
    return unicodedata.normalize("NFKC", text)


def def_split_ext(name: str) -> tuple[str, str]:
    stem, dot, ext = name.rpartition(".")
    if not dot or not stem:
        return name, ""
    return stem, ext.lower()


def def_valid_date(year: int, month: int, day: int) -> str:
    try:
        return _dt.date(year, month, day).isoformat()
    except ValueError:
        return ""


def def_find_spec(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError, AttributeError):
        return False


def def_load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# =============================================================================
# 02. Roster
# =============================================================================


def def_load_roster(ts_path: Path = ROSTER_TS) -> list[str]:
    """Names from ``MOTHER_INCOMING`` in incoming-roster.ts (single source of truth)."""
    text = ts_path.read_text(encoding="utf-8")
    match = re.search(r"MOTHER_INCOMING\s*:\s*string\[\]\s*=\s*\[(.*?)\];", text, re.S)
    if not match:
        raise RuntimeError("MOTHER_INCOMING not found in %s" % ts_path)
    return [m.group(1) for m in re.finditer(r'"((?:[^"\\]|\\.)+)"', match.group(1))]


def def_list_incoming(directory: Path) -> list[str]:
    names = [p.name for p in directory.iterdir() if p.is_file() and not p.name.startswith(("~$", "."))]
    return sorted(names)


# =============================================================================
# 03. Knowledge (attachments SSOT, graceful)
# =============================================================================


class Knowledge:
    """Ticker SSOT module, broker and rating dictionaries; every piece is optional."""

    def __init__(self, attachments: Path = ATTACHMENTS) -> None:
        self.sources: dict[str, str] = {}
        self.ticker = None
        self.broker_aliases: list[tuple[str, str, str]] = []  # alias, canonical, abbr
        self.rating_levels: dict[str, list[str]] = {}
        hits = sorted(attachments.glob("VIS_VRN_TickerFilenameSSOT_v*.py")) if attachments.is_dir() else []
        if hits:
            try:
                self.ticker = def_load_module("via_vrn_ticker_filename_ssot", hits[-1])
                self.sources["ticker_ssot"] = str(hits[-1].relative_to(PROJECT_ROOT)) if hits[-1].is_relative_to(PROJECT_ROOT) else str(hits[-1])
            except Exception as error:  # noqa: BLE001 - graceful by design
                self.sources["ticker_ssot"] = "LOAD_FAIL " + error.__class__.__name__
        broker = attachments / "VRN_Broker_Dict_v0100.json"
        if broker.is_file():
            try:
                payload = json.loads(broker.read_text(encoding="utf-8"))
                for canonical, spec in payload.get("brokers", {}).items():
                    abbr = str(spec.get("abbr", canonical))
                    for alias in spec.get("aliases", []) or [canonical]:
                        self.broker_aliases.append((str(alias), canonical, abbr))
                self.sources["broker_dict"] = broker.name
            except (OSError, ValueError) as error:
                self.sources["broker_dict"] = "LOAD_FAIL " + error.__class__.__name__
        rating = attachments / "VRN_Rating_Dict_v0100.json"
        if rating.is_file():
            try:
                payload = json.loads(rating.read_text(encoding="utf-8"))
                for level, spec in payload.get("levels", {}).items():
                    words = list(spec.get("zh", [])) + list(spec.get("en", []))
                    self.rating_levels[level] = [str(w) for w in words]
                self.sources["rating_dict"] = rating.name
            except (OSError, ValueError) as error:
                self.sources["rating_dict"] = "LOAD_FAIL " + error.__class__.__name__
        if not self.rating_levels:
            self.rating_levels = {k: list(v) for k, v in RATING_FALLBACK.items()}
            self.sources.setdefault("rating_dict", "builtin-fallback")


# =============================================================================
# 04. Filename contract
# =============================================================================

TW_YF_RE = re.compile(r"(?<!\d)([1-9]\d{3})\.(TW|TWO)\b", re.I)
TW_BB_RE = re.compile(r"(?<!\d)([1-9]\d{3})\s+TT\b", re.I)
TW_BB_TIGHT_RE = re.compile(r"(?<!\d)([1-9]\d{3})TT\b", re.I)
TW_CORE_RE = re.compile(r"(?<!\d)([1-9]\d{3})(?!\d)")
DATE_YMD8_RE = re.compile(r"(?<!\d)(20\d{2})(\d{2})(\d{2})(?!\d)")
DATE_DASH_RE = re.compile(r"(20\d{2})[_-](\d{2})[_-](\d{2})")
DATE_ROC7_RE = re.compile(r"(?<!\d)(1[01]\d)(\d{2})(\d{2})(?!\d)")
DATE_YY6_RE = re.compile(r"(?:CTBC|早報)(\d{2})(\d{2})(\d{2})(?!\d)", re.I)
DATE_Q_RE = re.compile(r"(20\d{2})\s*Q([1-4])", re.I)
DATE_FY_RE = re.compile(r"FY(20\d{2})", re.I)


def def_simple_tokens(stem: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for chunk in re.findall(r"[0-9]+|[A-Za-z]+|[\u4e00-\u9fff]+", stem):
        kind = "DIGIT" if chunk.isdigit() else "LATIN" if chunk.isascii() else "CJK"
        out.append((chunk, kind))
    return out


def def_extract_ticker(name: str, knowledge: Knowledge | None) -> dict[str, Any]:
    """Return ticker core / kind / recovered / note, mirroring resolveTwTicker()."""
    text = def_nfkc(name)
    yf = TW_YF_RE.search(text)
    if yf:
        return {"core": yf.group(1), "kind": "yfinance", "recovered": False, "note": yf.group(0)}
    bb = TW_BB_RE.search(text)
    if bb:
        return {"core": bb.group(1), "kind": "bloomberg", "recovered": False, "note": bb.group(0)}
    tight = TW_BB_TIGHT_RE.search(text)
    if tight:
        return {"core": tight.group(1), "kind": "bloomberg", "recovered": True, "note": tight.group(0) + " · 缺空格已回收"}
    stem, _ext = def_split_ext(text)
    if knowledge is not None and knowledge.ticker is not None and hasattr(knowledge.ticker, "tokenize_filename"):
        tokens = list(knowledge.ticker.tokenize_filename(stem))
        judge = getattr(knowledge.ticker, "disambiguate_year_vs_ticker", None)
    else:
        tokens = def_simple_tokens(stem)
        judge = None
    for index, (token, kind) in enumerate(tokens):
        if kind != "DIGIT" or len(token) != 4 or not TW_CORE_RE.fullmatch(token):
            continue
        neighbour = "".join(t for t, _k in tokens[max(0, index - 1):index] + tokens[index + 1:index + 2])
        if int(token) in YEAR_BAND:
            if judge is not None:
                verdict, _conf, reason = judge(token, neighbor_text=neighbour)
            else:
                verdict = "YEAR" if any(c in neighbour for c in DATE_CUES) else "AMBIGUOUS"
                reason = "builtin year-band rule"
            if verdict != "TICKER":
                continue
            return {"core": token, "kind": "native", "recovered": False, "note": "year-band · " + reason}
        return {"core": token, "kind": "native", "recovered": False, "note": token}
    return {"core": "", "kind": "", "recovered": False, "note": "無四碼代號"}


def def_extract_date(name: str) -> tuple[str, str]:
    text = def_nfkc(name)
    m = DATE_YMD8_RE.search(text)
    if m:
        iso = def_valid_date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        if iso:
            return iso, "ymd8"
    m = DATE_DASH_RE.search(text)
    if m:
        iso = def_valid_date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        if iso:
            return iso, "ymd-dash"
    m = DATE_ROC7_RE.search(text)
    if m:
        iso = def_valid_date(int(m.group(1)) + 1911, int(m.group(2)), int(m.group(3)))
        if iso:
            return iso, "roc7"
    m = DATE_YY6_RE.search(text)
    if m:
        yy = int(m.group(1))
        iso = def_valid_date(2000 + yy if yy <= 50 else 1900 + yy, int(m.group(2)), int(m.group(3)))
        if iso:
            return iso, "yymmdd6"
    m = DATE_Q_RE.search(text)
    if m:
        return "%s-%s" % (m.group(1), ("03-31", "06-30", "09-30", "12-31")[int(m.group(2)) - 1]), "quarter"
    m = DATE_FY_RE.search(text)
    if m:
        return m.group(1) + "-12-31", "fiscal"
    return "", ""


def def_match_broker(name: str, knowledge: Knowledge | None) -> dict[str, str]:
    text = def_nfkc(name)
    stem, _ext = def_split_ext(text)
    head = re.match(r"\s*([A-Za-z]{2,6})(?=[-_ ])", stem)
    if head and head.group(1).upper() in BROKER_PREFIX:
        canonical, abbr = BROKER_PREFIX[head.group(1).upper()]
        return {"broker": canonical, "abbr": abbr, "source": "prefix " + head.group(1)}
    tail = re.search(r"(?<![A-Za-z0-9])(CTBC|KGI|UBS|CLST|MQ)(?=\d|[-_ ]|$)", stem, re.I)
    if tail:
        canonical, abbr = BROKER_PREFIX[tail.group(1).upper()]
        return {"broker": canonical, "abbr": abbr, "source": "token " + tail.group(1)}
    cleaned = ORDINAL_RE.sub(" ", stem)
    best: tuple[int, str, str, str] | None = None
    for key, canonical, abbr in BROKER_ZH:
        pos = cleaned.find(key)
        if pos < 0:
            continue
        follower = cleaned[pos + len(key):pos + len(key) + 3]
        marked = any(follower.startswith(mk) for mk in BROKER_MARKERS)
        run_start = pos == 0 or not ("\u4e00" <= cleaned[pos - 1] <= "\u9fff")
        if not (marked or run_start):
            continue
        candidate = (pos, canonical, abbr, key)
        if best is None or candidate[0] < best[0]:
            best = candidate
    if best is not None:
        return {"broker": best[1], "abbr": best[2], "source": "zh " + best[3]}
    if knowledge is not None:
        for alias, canonical, abbr in sorted(knowledge.broker_aliases, key=lambda a: -len(a[0])):
            if len(alias) < 4:
                continue
            if alias.lower() in stem.lower():
                return {"broker": canonical, "abbr": abbr, "source": "dict " + alias}
    return {"broker": "", "abbr": "", "source": ""}


def def_classify_rating(name: str, knowledge: Knowledge | None) -> dict[str, str]:
    text = def_nfkc(name)
    levels = knowledge.rating_levels if knowledge is not None else RATING_FALLBACK
    best: tuple[int, str, str] | None = None
    for level, words in levels.items():
        for word in words:
            if not word:
                continue
            if word.isascii():
                pattern = re.compile(r"(?<![A-Za-z0-9])" + re.escape(word) + r"(?![A-Za-z0-9])", re.I)
                match = pattern.search(text)
                pos = match.start() if match else -1
            else:
                pos = text.find(word)
            if pos < 0:
                continue
            candidate = (len(word), level, word)
            if best is None or candidate[0] > best[0]:
                best = candidate
    if best is None:
        return {"cat": "", "word": ""}
    return {"cat": best[1], "word": best[2]}


def def_guess_type(name: str, ext: str, non_stock: bool) -> str:
    low = name.lower()
    if non_stock:
        return "non_stock"
    if re.search(r"initiation|初次", name, re.I):
        return "INITIATION"
    if re.search(r"法人|conference|法說", name, re.I):
        return "CONFERENCE_CALL"
    if re.search(r"年報|annual", name, re.I):
        return "EARNINGS_REVIEW"
    if "memo" in low and ext == "docx":
        return "MEMO"
    if ext == "csv":
        return "holdings"
    if ext == "xlsx":
        return "financial_sheet"
    if ext in ("md", "markdown"):
        return "markdown_note"
    if ext == "pdf":
        return "COMPANY_UPDATE"
    if ext in OFIE_EXT:
        return "omni_doc"
    return "unclassified"


def def_parse_contract(name: str, knowledge: Knowledge | None = None) -> dict[str, Any]:
    text = def_nfkc(name)
    stem, ext = def_split_ext(text)
    ticker = def_extract_ticker(text, knowledge)
    report_date, date_kind = def_extract_date(text)
    broker = def_match_broker(text, knowledge)
    rating = def_classify_rating(text, knowledge)
    non_stock = any(k in text for k in NON_STOCK)
    report_type = def_guess_type(text, ext, non_stock)
    reasons: list[str] = []
    if not ticker["core"]:
        reasons.append("無代號")
    if not report_date:
        reasons.append("無日期")
    if non_stock:
        reasons.append("非個股")
    if "scan" in text.lower():
        reasons.append("scan")
    if ext == "csv":
        risk = "GREEN"
    elif not ticker["core"] or not report_date or non_stock or "scan" in text.lower():
        risk = "YELLOW"
    else:
        risk = "GREEN"
    company = ""
    cjk = re.findall(r"[\u4e00-\u9fff]{2,6}", stem)
    if cjk:
        company = cjk[0]
    return {
        "name": name,
        "stem": stem,
        "ext": ext,
        "ticker": ticker["core"],
        "ticker_kind": ticker["kind"],
        "ticker_recovered": ticker["recovered"],
        "ticker_note": ticker["note"],
        "bloomberg": (ticker["core"] + " TT") if ticker["core"] else "",
        "report_date": report_date,
        "date_kind": date_kind,
        "broker": broker["broker"],
        "broker_abbr": broker["abbr"],
        "broker_source": broker["source"],
        "rating_cat": rating["cat"],
        "rating_word": rating["word"],
        "report_type": report_type,
        "non_stock": non_stock,
        "company": company,
        "risk": risk,
        "reasons": reasons,
    }


# =============================================================================
# 05. Environment probe (modules, deps, accelerators)
# =============================================================================


def def_find_supportive(start: Path) -> Path | None:
    probe = start.resolve()
    while True:
        candidate = probe / "supportive modules"
        if candidate.is_dir():
            return candidate
        if probe.parent == probe:
            return None
        probe = probe.parent


def def_probe_environment(repo_root: Path = PROJECT_ROOT, vrn_root: Path | None = None) -> dict[str, Any]:
    roots = [repo_root / "functional modules" / "VRN"]
    if vrn_root is not None and vrn_root.resolve() != roots[0].resolve():
        roots.append(vrn_root)
    roots.append(repo_root / "attachments")
    if ATTACHMENTS.resolve() not in [r.resolve() for r in roots]:
        roots.append(ATTACHMENTS)          # v0101 母倉:收容副本的 attachments(唯讀)
    modules: dict[str, dict[str, str]] = {}
    for key, pattern, stage in MODULES:
        found = None
        for root in roots:
            if not root.is_dir():
                continue
            hits = sorted(root.rglob(pattern))
            if hits:
                found = hits[-1]
                break
        entry = {"stage": stage, "pattern": pattern, "status": "ABSENT", "path": "", "syntax": ""}
        if found is not None:
            entry["status"] = "PRESENT"
            entry["path"] = str(found.relative_to(repo_root)) if found.is_relative_to(repo_root) else str(found)
            try:
                compile(found.read_text(encoding="utf-8-sig"), str(found), "exec")
                entry["syntax"] = "OK"
            except (SyntaxError, UnicodeDecodeError, OSError) as error:
                entry["syntax"] = "FAIL " + error.__class__.__name__
        modules[key] = entry
    ssot: dict[str, str] = {}
    # v0101 母倉:活的冊住在 VRN/knowledge 與 VRN/SSOT(不是倉根 attachments/);先找活冊,再找收容副本
    ssot_roots = [roots[0], roots[0] / "knowledge", roots[0] / "SSOT"] + roots[1:]
    for fn in SSOT_FILES:
        hit = None
        for root in ssot_roots:
            candidate = root / fn if root.is_dir() else None
            if candidate is not None and candidate.is_file():
                hit = candidate
                break
        ssot[fn] = "PRESENT" if hit else "ABSENT"
    deps = {name: {"available": def_find_spec(name), "used_by": used} for name, used in DEPS}
    supportive = def_find_supportive(Path(__file__).parent)
    via_home = os.environ.get("VIA_HOME", "")
    if supportive is None and via_home:
        candidate = Path(via_home) / "supportive modules"
        supportive = candidate if candidate.is_dir() else None
    accel_entry = supportive / "VIA_SuperAccel_Module.py" if supportive else None
    ps20_entry = supportive / "VIA_PS_Accel_Module.ps1" if supportive else None
    net_hits = sorted((supportive / "network").glob("via_net_unified_v*.py")) if supportive and (supportive / "network").is_dir() else []
    accel_obj = globals().get("VIA_ACCEL")
    accel = {
        "bridge_marker": "PRESENT" if "VIA_ACCEL" in globals() else "ABSENT",
        "bridge_resolved": accel_obj is not None,
        "supportive_dir": str(supportive) if supportive else "",
        "super_accel_entry": "PRESENT" if accel_entry and accel_entry.is_file() else "ABSENT",
        "ps20_module": "PRESENT" if ps20_entry and ps20_entry.is_file() else "ABSENT",
        "net_unified": net_hits[-1].name if net_hits else "ABSENT",
        "lib_candidates": {name: def_find_spec(name) for name in ("polars", "pyarrow", "duckdb", "numpy", "pandas", "regex", "rapidfuzz", "pydantic", "psutil", "watchfiles", "talib")},
    }
    accel["lib_available"] = sum(1 for v in accel["lib_candidates"].values() if v)
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "cwd": str(Path.cwd()),
        "repo_root": str(repo_root),
        "vrn_tree": "PRESENT" if (repo_root / "functional modules" / "VRN" / "engine").is_dir() else "ABSENT",
        "net_env": {"VIA_NET": os.environ.get("VIA_NET", ""), "VIA_LIVE": os.environ.get("VIA_LIVE", ""),
                    "VIA_NET_CONSENT": "SET" if os.environ.get("VIA_NET_CONSENT") else "UNSET"},
        "modules": modules,
        "ssot": ssot,
        "deps": deps,
        "accel": accel,
    }


# =============================================================================
# 06. Per-file stage evaluation
# =============================================================================


def def_stage(status: str, detail: str) -> dict[str, str]:
    return {"status": status, "light": STATUS_LIGHT[status], "detail": detail}


def def_sniff(path: Path) -> tuple[int, str, str]:
    size = path.stat().st_size
    digest = hashlib.sha256()
    magic = b""
    with path.open("rb") as handle:
        first = handle.read(8)
        magic = first
        digest.update(first)
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return size, digest.hexdigest()[:16], magic.hex()


def def_pdf_text_layer(path: Path) -> str:
    """'TEXT_LAYER' / 'OCR_NEEDED' / 'UNKNOWN' using pypdf when present."""
    if not def_find_spec("pypdf"):
        return "UNKNOWN"
    try:
        import pypdf  # type: ignore

        reader = pypdf.PdfReader(str(path))
        text = ""
        for page in reader.pages[:2]:
            text += page.extract_text() or ""
        return "TEXT_LAYER" if len(text.strip()) >= 40 else "OCR_NEEDED"
    except Exception:  # noqa: BLE001 - probe must not crash on bad PDFs
        return "UNKNOWN"


def def_probe_file(name: str, path: Path | None, env: dict[str, Any], contract: dict[str, Any],
                   dup: dict[str, str]) -> dict[str, Any]:
    stages: dict[str, dict[str, str]] = {}
    ext = contract["ext"]
    text = def_nfkc(name)
    # S01
    problems = []
    if not text.strip():
        problems.append("空檔名")
    if any(ord(c) < 32 for c in text):
        problems.append("控制字元")
    if ext not in ALLOWED_EXT:
        problems.append("副檔名 .%s 不在允許清單" % (ext or "?"))
    if len(text) > 255:
        problems.append("檔名逾 255 字")
    if problems:
        stages["S01"] = def_stage("FAIL", " · ".join(problems))
    else:
        stages["S01"] = def_stage("OK", "ext=.%s · %s" % (ext, str(path) if path else "名冊件（無本機路徑）"))
    # S02
    size = None
    sha = ""
    magic = ""
    if path is not None and path.is_file():
        try:
            size, sha, magic = def_sniff(path)
        except OSError as error:
            stages["S02"] = def_stage("FAIL", "讀取失敗 " + error.__class__.__name__)
        else:
            if size == 0:
                stages["S02"] = def_stage("FAIL", "零位元組")
            else:
                stages["S02"] = def_stage("OK", "%s:%d · sha256 %s" % (ext, size, sha))
    else:
        stages["S02"] = def_stage("BLOCKED", "本台無位元組（進件目錄不在此主機；母機以 --incoming 指向 C:\\ 進件夾）")
    # S03
    notes = [v for v in (dup.get("name"), dup.get("bytes"), dup.get("triple")) if v]
    stages["S03"] = def_stage("WARN" if notes else "OK", " · ".join(notes) if notes else "無重複")
    # S04
    if ext not in OFIE_EXT:
        stages["S04"] = def_stage("FAIL", "OFIE 拒 .%s" % ext)
    else:
        route = "PDF → MDL001 轉檔 → MDL002 版面" if ext == "pdf" else (
            "DOCX → markitdown 橋 → .md（VRNFourEngineSuite 不吃 docx）" if ext in BRIDGE_EXT else "OFIE 直入")
        status = "OK"
        extra = []
        if ext in BRIDGE_EXT and not env["deps"]["markitdown"]["available"]:
            status = "WARN"
            extra.append("markitdown 未裝")
        if magic:
            raw = bytes.fromhex(magic)
            if ext == "pdf" and not raw.startswith(b"%PDF-"):
                status = "FAIL"
                extra.append("magic 非 %PDF-")
            if ext in ("docx", "xlsx", "pptx") and not raw.startswith(b"PK\x03\x04"):
                status = "FAIL"
                extra.append("magic 非 ZIP/OOXML")
            if status != "FAIL":
                extra.append("magic OK")
        elif size is None:
            extra.append("magic 待位元組")
        stages["S04"] = def_stage(status, route + (" · " + " · ".join(extra) if extra else ""))
    # S05
    accel = env["accel"]
    lib_note = "加速候選庫 %d/%d" % (accel["lib_available"], len(accel["lib_candidates"]))
    if accel["bridge_resolved"]:
        stages["S05"] = def_stage("OK", "ACCEL-BRIDGE 已解析 VIA_SuperAccel_Module · " + lib_note)
    else:
        stages["S05"] = def_stage("WARN", "ACCEL-BRIDGE 掛載（graceful）· SuperAccel 入口 %s · PS20 模組 %s · NetUnified %s · %s" % (
            accel["super_accel_entry"], accel["ps20_module"], accel["net_unified"], lib_note))
    # S06
    contract_note = "ticker %s%s · %s · %s · %s · %s" % (
        contract["ticker"] or "—",
        " (%s%s)" % (contract["ticker_kind"], " 回收" if contract["ticker_recovered"] else "") if contract["ticker"] else "",
        contract["report_date"] or "無日期",
        contract["broker"] or "券商未識別",
        contract["report_type"],
        contract["risk"],
    )
    if contract["rating_cat"]:
        contract_note += " · 評等 %s(%s)" % (contract["rating_cat"], contract["rating_word"])
    if ext == "pdf":
        layer = def_pdf_text_layer(path) if path is not None and path.is_file() and size else "UNKNOWN"
        route_note = {"TEXT_LAYER": "文字層 → 免 OCR", "OCR_NEEDED": "無文字層 → OCR（MDL004/005）",
                      "UNKNOWN": "文字層/掃描判定待位元組或 pypdf"}[layer]
    else:
        route_note = "非 PDF → 不走 OCR"
    if contract["risk"] == "RED":
        status = "FAIL"
    elif contract["risk"] == "YELLOW":
        status = "WARN"
    else:
        status = "OK"
    stages["S06"] = def_stage(status, contract_note + " · " + route_note + (" · " + "/".join(contract["reasons"]) if contract["reasons"] else ""))
    # S07
    net = env["net_env"]
    if net["VIA_NET"] == "1" and net["VIA_NET_CONSENT"] == "SET":
        stages["S07"] = def_stage("SKIP", "閘開（VIA_NET=1 且 CONSENT）· 探針不外呼 · 仍 quote-or-abstain")
    else:
        stages["S07"] = def_stage("SKIP", "閘關正確 · 不外呼（VIA_NET=%s · CONSENT %s）" % (net["VIA_NET"] or "0", net["VIA_NET_CONSENT"]))
    # S08 — a module counts only when it is present AND compiles; upstream byte/format gates must have passed
    missing_mod = [m for m in S08_MODULES if env["modules"][m]["status"] != "PRESENT"]
    broken_mod = [m for m in S08_MODULES if env["modules"][m]["status"] == "PRESENT" and env["modules"][m]["syntax"] != "OK"]
    missing_dep = [d for d in TABLE_DEPS if not env["deps"][d]["available"]]
    reasons = []
    if missing_mod:
        reasons.append("模組缺 " + "/".join(missing_mod) + "（正典樹 functional modules/VRN 不在庫內）")
    if broken_mod:
        reasons.append("模組語法失敗 " + "/".join("%s(%s)" % (m, env["modules"][m]["syntax"]) for m in broken_mod))
    if missing_dep:
        reasons.append("套件缺 " + "/".join(missing_dep))
    if size is None:
        reasons.append("無位元組")
    upstream_bad = [sid for sid in ("S02", "S04") if stages[sid]["status"] == "FAIL"]   # zero bytes, bad magic, wrong ext
    if upstream_bad:
        reasons.append("上游 " + "/".join(upstream_bad) + " FAIL（位元組／格式閘）")
    if reasons:
        stages["S08"] = def_stage("BLOCKED", " · ".join(reasons))
    else:
        stages["S08"] = def_stage("READY", "MDL003/004 與套件齊備 · 未執行（探針唯讀，請跑 VRN_Pipeline_Runner）")
    # S09 — the financial-SSOT gate: every required SSOT must be present, MDL006 must compile
    missing9 = [m for m in S09_MODULES if env["modules"][m]["status"] != "PRESENT"
                or env["modules"][m]["syntax"] != "OK"]
    ssot_absent = [k for k, v in env["ssot"].items() if v != "PRESENT"]
    if missing9:
        stages["S09"] = def_stage("BLOCKED", "模組缺或語法失敗 " + "/".join(
            "%s(%s)" % (m, env["modules"][m]["syntax"] or env["modules"][m]["status"]) for m in missing9))
    elif stages["S08"]["status"] != "READY":
        stages["S09"] = def_stage("BLOCKED", "上游 S08 未產出 · MDL006 %s · SSOT %d/%d" % (
            env["modules"]["MDL006"]["path"] or "ABSENT", len(env["ssot"]) - len(ssot_absent), len(env["ssot"])))
    elif ssot_absent:
        stages["S09"] = def_stage("BLOCKED", "SSOT 缺 %d/%d：%s" % (len(ssot_absent), len(env["ssot"]), "/".join(ssot_absent)))
    else:
        stages["S09"] = def_stage("READY", "MDL006 齊備 · SSOT %d/%d · 未執行" % (len(env["ssot"]) - len(ssot_absent), len(env["ssot"])))
    # S10 — a summariser engine counts only when it compiles
    engines = [m for m in S10_MODULES if env["modules"][m]["status"] == "PRESENT" and env["modules"][m]["syntax"] == "OK"]
    if not engines:
        stages["S10"] = def_stage("BLOCKED", "摘要引擎缺席或語法失敗")
    elif stages["S09"]["status"] != "READY":
        stages["S10"] = def_stage("BLOCKED", "上游 S09 未產出 · 引擎 %s 在庫" % "/".join(engines))
    else:
        stages["S10"] = def_stage("READY", "引擎 %s 齊備 · 未執行" % "/".join(engines))
    stuck = next((sid for sid in STAGE_IDS if stages[sid]["status"] in ("FAIL", "BLOCKED")), None)
    statuses = [stages[sid]["status"] for sid in STAGE_IDS]
    if "FAIL" in statuses:
        light = "bad"
    elif "BLOCKED" in statuses or "WARN" in statuses:
        light = "warn"
    else:
        light = "ok"
    return {
        "name": name,
        "path": str(path) if path else "",
        "size": size,
        "sha256_16": sha,
        "contract": contract,
        "stages": stages,
        "stuck_step": stuck,
        "stuck_kind": stages[stuck]["status"] if stuck else "",
        "light": light,
        "letters": "".join(STATUS_LETTER[s] for s in statuses),
    }


# =============================================================================
# 07. Run and aggregate
# =============================================================================


def def_dedup_info(names: list[str], contracts: dict[str, dict[str, Any]], shas: dict[str, str]) -> dict[str, dict[str, str]]:
    info: dict[str, dict[str, str]] = {n: {} for n in names}
    seen_name: dict[str, str] = {}
    seen_sha: dict[str, str] = {}
    seen_triple: dict[tuple[str, str, str], str] = {}
    for name in names:
        key = def_nfkc(name).lower()
        if key in seen_name:
            info[name]["name"] = "同名重複 dupOf=" + seen_name[key]
        else:
            seen_name[key] = name
        sha = shas.get(name)
        if sha:
            if sha in seen_sha:
                info[name]["bytes"] = "位元組相同 dupOf=" + seen_sha[sha]
            else:
                seen_sha[sha] = name
        c = contracts[name]
        if c["ticker"] and c["report_date"] and c["broker_abbr"]:
            triple = (c["broker_abbr"], c["ticker"], c["report_date"])
            if triple in seen_triple:
                info[name]["triple"] = "同券商同標的同日 dupOf=" + seen_triple[triple]
            else:
                seen_triple[triple] = name
    return info


def def_run(names: list[str], incoming: Path | None, env: dict[str, Any] | None = None,
            knowledge: Knowledge | None = None, roster_source: str = "") -> dict[str, Any]:
    env = env if env is not None else def_probe_environment()
    knowledge = knowledge if knowledge is not None else Knowledge()
    contracts = {n: def_parse_contract(n, knowledge) for n in names}
    shas: dict[str, str] = {}
    if incoming is not None and incoming.is_dir():
        for n in names:
            p = incoming / n
            if p.is_file():
                try:
                    shas[n] = def_sniff(p)[1]
                except OSError:
                    pass
    dup = def_dedup_info(names, contracts, shas)
    files = []
    for n in names:
        path = (incoming / n) if incoming is not None else None
        files.append(def_probe_file(n, path, env, contracts[n], dup[n]))
    stage_summary: dict[str, dict[str, int]] = {sid: {s: 0 for s in STATUS_ORDER} for sid in STAGE_IDS}
    stuck_summary: dict[str, int] = {}
    risk_summary = {"GREEN": 0, "YELLOW": 0, "RED": 0}
    for f in files:
        for sid in STAGE_IDS:
            stage_summary[sid][f["stages"][sid]["status"]] += 1
        if f["stuck_step"]:
            stuck_summary[f["stuck_step"]] = stuck_summary.get(f["stuck_step"], 0) + 1
        risk_summary[f["contract"]["risk"]] += 1
    root_causes = def_root_causes(files, env, incoming)
    lights = [f["light"] for f in files]
    verdict = "RED" if "bad" in lights else "AMBER" if "warn" in lights else "GREEN"
    return {
        "probe": PROBE_NAME + " " + PROBE_VERSION,
        "generated": _dt.datetime.now().isoformat(timespec="seconds"),
        "roster_source": roster_source,
        "incoming": str(incoming) if incoming else "",
        "incoming_present": bool(incoming is not None and incoming.is_dir()),
        "knowledge": knowledge.sources,
        "count": len(files),
        "verdict": verdict,
        "stages": [{"id": s[0], "name": s[1], "title": s[2]} for s in STAGES],
        "stage_summary": stage_summary,
        "stuck_summary": stuck_summary,
        "risk_summary": risk_summary,
        "root_causes": root_causes,
        "env": env,
        "files": files,
    }


def def_root_causes(files: list[dict[str, Any]], env: dict[str, Any], incoming: Path | None) -> list[dict[str, Any]]:
    causes: list[dict[str, Any]] = []

    def count(stage: str, status: str) -> int:
        return sum(1 for f in files if f["stages"][stage]["status"] == status)

    n_bytes = count("S02", "BLOCKED")
    if n_bytes:
        causes.append({"code": "RC1_NO_BYTES", "stage": "S02", "affected": n_bytes, "severity": "BLOCKED",
                       "title": "本台沒有進件位元組",
                       "detail": "進件夾 %s 不在此主機；S02/S04 magic/S06 文字層/S08 之後全部要位元組。" % (str(incoming) if incoming else MOTHER_INCOMING_DIR),
                       "fix": "母機執行：python \"functional modules/VRN/engine/VRN_PanoramaProbe.py\" --incoming \"%s\" --html out.html" % MOTHER_INCOMING_DIR})
    absent = [k for k, v in env["modules"].items() if v["status"] != "PRESENT" and k.startswith("MDL")]
    if absent:
        causes.append({"code": "RC2_VRN_TREE_ABSENT", "stage": "S08", "affected": count("S08", "BLOCKED"), "severity": "BLOCKED",
                       "title": "VRN 正典模組不在庫內：" + "/".join(absent),
                       "detail": "attachments/VRN_Subsystem_Manifest.json 宣稱 CANONICAL_TREE_IN_REPO_VALIDATED，但 functional modules/VRN 只有本探針；庫內僅有 MDL006/MDL008/Runner 附件副本。",
                       "fix": "把母機 functional modules/VRN 正典樹（MDL001–MDL008）以 candidate 方式匯入，再由中央治理 stage→approve→promote。"})
    missing_deps = [k for k, v in env["deps"].items() if not v["available"]]
    if missing_deps:
        causes.append({"code": "RC3_DEPS_ABSENT", "stage": "S04/S08/S09", "affected": len(files), "severity": "BLOCKED",
                       "title": "選配套件缺席 %d/%d" % (len(missing_deps), len(env["deps"])),
                       "detail": "缺：" + ", ".join(missing_deps),
                       "fix": "以 VIA_EnvManager 在 via_vrn 環境安裝（pip/uv check 後原子接手），不動 base。"})
    if not env["accel"]["bridge_resolved"]:
        causes.append({"code": "RC4_ACCEL_GRACEFUL", "stage": "S05", "affected": len(files), "severity": "WARN",
                       "title": "加速器橋 graceful 缺席",
                       "detail": "supportive modules/VIA_SuperAccel_Module.py 不在此樹（入口 %s · PS20 模組 %s · NetUnified %s）。橋已掛，零行為變更。" % (
                           env["accel"]["super_accel_entry"], env["accel"]["ps20_module"], env["accel"]["net_unified"]),
                       "fix": "母機（VIA_HOME）自動解析；或設定 VIA_HOME 指向 VeritasIntelligenceAnalytics。"})
    yellow = [f for f in files if f["contract"]["risk"] == "YELLOW"]
    if yellow:
        causes.append({"code": "RC5_CONTRACT_YELLOW", "stage": "S06", "affected": len(yellow), "severity": "WARN",
                       "title": "檔名契約黃燈（非個股／無代號／無日期）",
                       "detail": "；".join("%s: %s" % (f["name"][:28], "/".join(f["contract"]["reasons"])) for f in yellow[:8]) + ("；…" if len(yellow) > 8 else ""),
                       "fix": "黃燈依規不轉紅；晨會／早報／產業件進 TAB 1 留檔，不發明代號。"})
    causes.append({"code": "RC6_NLP_GATE", "stage": "S07", "affected": len(files), "severity": "SKIP",
                   "title": "NLP 閘關（政策，非故障）",
                   "detail": "VIA_NET=%s · CONSENT %s · 不外呼。" % (env["net_env"]["VIA_NET"] or "0", env["net_env"]["VIA_NET_CONSENT"]),
                   "fix": "不需處理；LIVE 需明示 VIA_NET=1 與 VIA_NET_CONSENT。"})
    fails = [f for f in files if f["light"] == "bad"]
    if fails:
        causes.insert(0, {"code": "RC0_FAIL", "stage": "多段", "affected": len(fails), "severity": "FAIL",
                          "title": "實際失敗件",
                          "detail": "；".join("%s @ %s: %s" % (f["name"][:28], f["stuck_step"], f["stages"][f["stuck_step"]]["detail"][:60]) for f in fails[:8]),
                          "fix": "逐件處理：零位元組／magic 不符／副檔名拒收。"})
    return causes


# =============================================================================
# 08. Rendering
# =============================================================================


def def_render_console(report: dict[str, Any]) -> str:
    lines = []
    lines.append("===== %s · %s 件 · verdict %s =====" % (report["probe"], report["count"], report["verdict"]))
    lines.append("roster    : %s" % report["roster_source"])
    lines.append("incoming  : %s (%s)" % (report["incoming"] or "—", "PRESENT" if report["incoming_present"] else "ABSENT"))
    env = report["env"]
    lines.append("python    : %s · %s" % (env["python"], env["platform"]))
    lines.append("VRN tree  : %s · modules PRESENT %d/%d · deps %d/%d · accel bridge %s" % (
        env["vrn_tree"],
        sum(1 for m in env["modules"].values() if m["status"] == "PRESENT"), len(env["modules"]),
        sum(1 for d in env["deps"].values() if d["available"]), len(env["deps"]),
        "RESOLVED" if env["accel"]["bridge_resolved"] else "GRACEFUL-ABSENT"))
    lines.append("knowledge : " + ", ".join("%s=%s" % kv for kv in report["knowledge"].items()))
    lines.append("")
    lines.append("--- 段落總覽（每段各狀態件數）---")
    lines.append("%-4s %-18s %-8s " % ("id", "stage", "title") + " ".join("%7s" % s for s in STATUS_ORDER))
    for stage in report["stages"]:
        counts = report["stage_summary"][stage["id"]]
        lines.append("%-4s %-18s %-8s " % (stage["id"], stage["name"], stage["title"]) + " ".join("%7d" % counts[s] for s in STATUS_ORDER))
    lines.append("")
    lines.append("--- 卡點（第一個 BLOCKED/FAIL 段）---")
    for sid, n in sorted(report["stuck_summary"].items()):
        lines.append("  %s: %d 件" % (sid, n))
    if not report["stuck_summary"]:
        lines.append("  無")
    lines.append("--- 契約風險 --- GREEN %(GREEN)d · YELLOW %(YELLOW)d · RED %(RED)d" % report["risk_summary"])
    lines.append("")
    lines.append("--- 全景根因（依嚴重度）---")
    for rc in report["root_causes"]:
        lines.append("  [%s] %s · %s · %d 件" % (rc["severity"], rc["code"], rc["title"], rc["affected"]))
        lines.append("      %s" % rc["detail"])
        lines.append("      → %s" % rc["fix"])
    lines.append("")
    lines.append("--- 逐件矩陣 (S01..S10: O=OK R=READY W=WARN S=SKIP B=BLOCKED F=FAIL) ---")
    lines.append("%-10s %-5s %-6s %-10s %-6s %-6s %s" % ("S01..S10", "stuck", "ticker", "date", "broker", "risk", "name"))
    for f in report["files"]:
        c = f["contract"]
        lines.append("%-10s %-5s %-6s %-10s %-6s %-6s %s" % (
            f["letters"], f["stuck_step"] or "-", c["ticker"] or "-", c["report_date"] or "-", c["broker_abbr"] or "-", c["risk"], f["name"]))
    return "\n".join(lines)


HTML_CSS = """
body{font-family:Segoe UI,Meiryo,'Noto Sans TC',sans-serif;background:#0b1220;color:#e8eef8;margin:24px;font-size:13px}
h1{font-size:20px;margin:0 0 4px} h2{font-size:15px;margin:22px 0 8px;color:#9cd1ff}
table{border-collapse:collapse;width:100%} th,td{border:1px solid #2a3a55;padding:4px 6px;text-align:left;vertical-align:top}
th{background:#152238;position:sticky;top:0} tr:nth-child(even){background:#101a2c}
.ok{background:#0f3d2a;color:#7dffa3} .warn{background:#4a3a0a;color:#ffd27d} .bad{background:#4a1414;color:#ff8a8a} .idle{background:#1c2536;color:#9aa8c0}
.pill{display:inline-block;padding:1px 6px;border-radius:9px;font-size:11px}
code{color:#9cd1ff} .lede{color:#9aa8c0}
"""


def def_render_html(report: dict[str, Any]) -> str:
    e = html.escape
    parts = ["<!DOCTYPE html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>",
             "<title>VRN 全景實測 · %s</title><style>%s</style></head><body>" % (e(report["generated"]), HTML_CSS)]
    parts.append("<h1>VRN 子系統全景實測 · verdict %s</h1>" % e(report["verdict"]))
    parts.append("<p class='lede'>%s · %d 件 · roster <code>%s</code> · incoming <code>%s</code> (%s) · %s</p>" % (
        e(report["probe"]), report["count"], e(report["roster_source"]), e(report["incoming"] or "—"),
        "PRESENT" if report["incoming_present"] else "ABSENT", e(report["generated"])))
    parts.append("<h2>段落總覽</h2><table><tr><th>段</th><th>名稱</th><th>中文</th>" + "".join("<th>%s</th>" % s for s in STATUS_ORDER) + "</tr>")
    for stage in report["stages"]:
        counts = report["stage_summary"][stage["id"]]
        parts.append("<tr><td>%s</td><td>%s</td><td>%s</td>" % (stage["id"], stage["name"], e(stage["title"])) + "".join("<td>%d</td>" % counts[s] for s in STATUS_ORDER) + "</tr>")
    parts.append("</table>")
    parts.append("<h2>全景根因</h2><table><tr><th>嚴重度</th><th>代碼</th><th>段</th><th>件數</th><th>說明</th><th>處置</th></tr>")
    for rc in report["root_causes"]:
        cls = {"FAIL": "bad", "BLOCKED": "warn", "WARN": "warn", "SKIP": "idle"}.get(rc["severity"], "idle")
        parts.append("<tr><td class='%s'>%s</td><td>%s</td><td>%s</td><td>%d</td><td><b>%s</b><br>%s</td><td>%s</td></tr>" % (
            cls, e(rc["severity"]), e(rc["code"]), e(rc["stage"]), rc["affected"], e(rc["title"]), e(rc["detail"]), e(rc["fix"])))
    parts.append("</table>")
    env = report["env"]
    parts.append("<h2>環境</h2><table><tr><th>項目</th><th>值</th></tr>")
    parts.append("<tr><td>Python</td><td>%s · %s</td></tr>" % (e(env["python"]), e(env["platform"])))
    parts.append("<tr><td>VRN 正典樹</td><td>%s</td></tr>" % e(env["vrn_tree"]))
    parts.append("<tr><td>模組</td><td>%s</td></tr>" % " · ".join("%s=%s" % (k, v["status"]) for k, v in env["modules"].items()))
    parts.append("<tr><td>套件</td><td>%s</td></tr>" % " · ".join("%s=%s" % (k, "有" if v["available"] else "缺") for k, v in env["deps"].items()))
    a = env["accel"]
    parts.append("<tr><td>加速器</td><td>橋 %s · 解析 %s · SuperAccel 入口 %s · PS20 模組 %s · NetUnified %s · 候選庫 %d/%d</td></tr>" % (
        a["bridge_marker"], "是" if a["bridge_resolved"] else "否（graceful）", a["super_accel_entry"], a["ps20_module"], e(a["net_unified"]), a["lib_available"], len(a["lib_candidates"])))
    parts.append("<tr><td>網路閘</td><td>VIA_NET=%s · VIA_LIVE=%s · CONSENT %s</td></tr></table>" % (
        e(env["net_env"]["VIA_NET"] or "0"), e(env["net_env"]["VIA_LIVE"] or "0"), e(env["net_env"]["VIA_NET_CONSENT"])))
    parts.append("<h2>逐件矩陣</h2><table><tr><th>#</th><th>檔名</th><th>代號</th><th>日期</th><th>券商</th><th>型別</th><th>風險</th><th>卡點</th>" +
                 "".join("<th title='%s'>%s</th>" % (e(s[1]), s[0]) for s in STAGES) + "</tr>")
    for index, f in enumerate(report["files"], 1):
        c = f["contract"]
        cells = "".join("<td class='%s' title='%s'>%s</td>" % (f["stages"][sid]["light"], e(f["stages"][sid]["detail"]), STATUS_LETTER[f["stages"][sid]["status"]]) for sid in STAGE_IDS)
        parts.append("<tr><td>%d</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td><span class='pill %s'>%s</span></td><td>%s</td>%s</tr>" % (
            index, e(f["name"]), e(c["ticker"] or "—"), e(c["report_date"] or "—"), e(c["broker_abbr"] or "—"), e(c["report_type"]),
            {"GREEN": "ok", "YELLOW": "warn", "RED": "bad"}[c["risk"]], c["risk"], e(f["stuck_step"] or "—"), cells))
    parts.append("</table><p class='lede'>O=OK · R=READY（齊備未執行）· W=WARN · S=SKIP · B=BLOCKED（本台不能跑）· F=FAIL。滑鼠停在格子看原因。</p></body></html>")
    return "".join(parts)


# =============================================================================
# 09. CLI
# =============================================================================


def def_build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--incoming", default="", help="真實進件夾；不存在時只跑名冊契約（位元組段 BLOCKED）")
    parser.add_argument("--roster-ts", default=str(ROSTER_TS), help="MOTHER_INCOMING 所在的 incoming-roster.ts")
    parser.add_argument("--names", default="", help="逐行檔名清單（取代名冊）")
    parser.add_argument("--vrn-root", default="", help="母機 functional modules/VRN 根（模組搜尋）")
    parser.add_argument("--json", default="", help="輸出 JSON 報告")
    parser.add_argument("--html", default="", help="輸出 HTML 全景")
    parser.add_argument("--strict", action="store_true", help="有 FAIL 時以 1 結束")
    parser.add_argument("--quiet", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = def_build_parser().parse_args(argv)
    incoming = Path(args.incoming) if args.incoming else None
    vrn_root = Path(args.vrn_root) if args.vrn_root else None
    if vrn_root is None and incoming is not None:
        for parent in incoming.parents:
            if parent.name == "VRN" and parent.parent.name == "functional modules":
                vrn_root = parent
                break
    if args.names:
        names = [line.strip() for line in Path(args.names).read_text(encoding="utf-8").splitlines() if line.strip()]
        roster_source = args.names
    elif incoming is not None and incoming.is_dir():
        names = def_list_incoming(incoming)
        roster_source = "dir " + str(incoming)
    else:
        names = def_load_roster(Path(args.roster_ts))
        roster_source = args.roster_ts
    env = def_probe_environment(PROJECT_ROOT, vrn_root)
    report = def_run(names, incoming, env, Knowledge(), roster_source)
    if args.json:
        Path(args.json).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.html:
        Path(args.html).write_text(def_render_html(report), encoding="utf-8")
    if not args.quiet:
        print(def_render_console(report))
    if args.strict and report["verdict"] == "RED":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
