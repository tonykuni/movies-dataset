#requires -Version 7.0

# =============================================================================
# VRN Stock-Only Full Extractor v2.2
#   - v1: full PDF/table/HTML extractor (preserved 100%, append-only)
#   - v2.2 NEW: classifier upgraded with broker_in_filename + pdf_buy_hints +
#               threshold 0.50 -> 0.40 + SSOT import-first / fallback to embed
# =============================================================================
# LL compliance: no <# #> block comments, no naked :F\d in DQ, param() first,
# $script: scope, Sort-Object hashtable, [System.IO.File]::WriteAllText only via
# Write-TextAtomic chokepoint.

param(
    [string]$VIA_ROOT      = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics",
    [switch]$NoOpenHtml,
    [switch]$DisableSSOT
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# =============================================================================
# CONFIG ($script: scope)
# =============================================================================
$script:VIA_ROOT      = $VIA_ROOT
$script:VRN_DIR       = Join-Path $VIA_ROOT "module\VRN"
$script:INPUT_DIR     = Join-Path $script:VRN_DIR "input"
$script:SUPPORT_DIR   = Join-Path $VIA_ROOT "module\supportive_module"

$script:VISUAL_TEMPLATE_CANDIDATES = @(
    "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VPN_v35_Dashboard (3).html",
    "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\VPN_v35_Dashboard (3).html",
    "C:\Users\tonyk\OneDrive\Desktop\VPN_v35_Dashboard (3).html",
    "C:\Users\tonyk\OneDrive\桌面\VPN_v35_Dashboard (3).html"
)

$script:TIMESTAMP  = Get-Date -Format "yyyyMMdd_HHmmss"
$script:RUN_DIR    = Join-Path $script:VRN_DIR ("_full_extract_runs\VRN_STOCKONLY_VISUAL_FULL_v22_" + $script:TIMESTAMP)
$script:PY_SCRIPT  = Join-Path $script:RUN_DIR "vrn_stockonly_visual_full_v22.py"

$script:BASIC_CSV       = Join-Path $script:RUN_DIR "vrn_basic_info.csv"
$script:FIN_CSV         = Join-Path $script:RUN_DIR "vrn_financial_data.csv"
$script:REJECT_CSV      = Join-Path $script:RUN_DIR "vrn_rejected_non_stock_reports.csv"
$script:INPUT_MATRIX_JSON = Join-Path $script:RUN_DIR "vrn_input_matrix.json"
$script:BLOCKS_JSON     = Join-Path $script:RUN_DIR "vrn_restored_blocks.json"
$script:TABLES_JSON     = Join-Path $script:RUN_DIR "vrn_restored_tables.json"
$script:SOURCE_MAP_JSON = Join-Path $script:RUN_DIR "vrn_source_map.json"
$script:SUMMARY_JSON    = Join-Path $script:RUN_DIR "vrn_stockonly_visual_full_summary.json"
$script:DUCKDB_PATH     = Join-Path $script:RUN_DIR "vrn_stockonly_visual_full.duckdb"
$script:HTML_OUT        = Join-Path $script:RUN_DIR "VRN_StockOnly_VisualLocked_MultiPage_UI_v22.html"
$script:LOG_FILE        = Join-Path $script:RUN_DIR "vrn_v22.log"

$script:ENABLE_YFINANCE = $true
$script:ENABLE_DUCKDB   = $true
$script:STOCK_ONLY      = $true
$script:USE_SSOT        = -not $DisableSSOT

$script:PYTHON_CANDIDATES = @(
    "C:\Users\tonyk\envs\via_core_312\Scripts\python.exe",
    "C:\Users\tonyk\envs\via_core\Scripts\python.exe",
    "C:\Python312\python.exe",
    "C:\Python313\python.exe",
    "python",
    "py"
)

# =============================================================================
# HELPERS
# =============================================================================
function Save-PhaseLog {
    param([string]$Line, [string]$Color = "Gray")
    $stamp = (Get-Date -Format "HH:mm:ss")
    $msg = ("[{0}] {1}" -f $stamp, $Line)
    Write-Host $msg -ForegroundColor $Color
    if (Test-Path -LiteralPath (Split-Path $script:LOG_FILE -Parent)) {
        try {
            [System.IO.File]::AppendAllText(
                $script:LOG_FILE,
                ([string]$msg + [Environment]::NewLine),
                [System.Text.UTF8Encoding]::new($false)
            )
        } catch {}
    }
}

function Ensure-Dir {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Force -Path $Path | Out-Null
    }
}

function Get-Python {
    foreach ($p in $script:PYTHON_CANDIDATES) {
        try {
            if ($p -eq "python" -or $p -eq "py") {
                if (Get-Command $p -ErrorAction SilentlyContinue) { return $p }
            } elseif (Test-Path -LiteralPath $p) {
                return $p
            }
        } catch {}
    }
    throw "no usable python"
}

function Get-VisualTemplate {
    foreach ($p in $script:VISUAL_TEMPLATE_CANDIDATES) {
        if (Test-Path -LiteralPath $p) { return $p }
    }
    return ""
}

function Write-TextAtomic {
    param([string]$Path, [object]$Text)
    $s = if ($null -eq $Text) { '' }
         elseif ($Text -is [array]) { [string]::Join([Environment]::NewLine, ($Text | ForEach-Object { [string]$_ })) }
         else { [string]$Text }
    $enc = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($Path, $s, $enc)
}

# =============================================================================
# WRITE PYTHON EXTRACTOR (v2.2 — classifier upgraded + SSOT dual-path)
# =============================================================================
function Write-PythonExtractor {
    $VisualTemplatePath = Get-VisualTemplate
    $useSsotFlag = if ($script:USE_SSOT) { "True" } else { "False" }

$Code = @'
# -*- coding: utf-8 -*-
import csv
import json
import os
import re
import sys
import traceback
from pathlib import Path
from datetime import datetime

# =============================================================================
# CONFIG (PS-injected)
# =============================================================================
VIA_ROOT    = Path(r"__VIA_ROOT__")
VRN_DIR     = Path(r"__VRN_DIR__")
INPUT_DIR   = Path(r"__INPUT_DIR__")
SUPPORT_DIR = Path(r"__SUPPORT_DIR__")
RUN_DIR     = Path(r"__RUN_DIR__")
VISUAL_TEMPLATE_PATH = Path(r"__VISUAL_TEMPLATE_PATH__") if r"__VISUAL_TEMPLATE_PATH__" else None

BASIC_CSV         = Path(r"__BASIC_CSV__")
FIN_CSV           = Path(r"__FIN_CSV__")
REJECT_CSV        = Path(r"__REJECT_CSV__")
INPUT_MATRIX_JSON = Path(r"__INPUT_MATRIX_JSON__")
BLOCKS_JSON       = Path(r"__BLOCKS_JSON__")
TABLES_JSON       = Path(r"__TABLES_JSON__")
SOURCE_MAP_JSON   = Path(r"__SOURCE_MAP_JSON__")
SUMMARY_JSON      = Path(r"__SUMMARY_JSON__")
DUCKDB_PATH       = Path(r"__DUCKDB_PATH__")
HTML_OUT          = Path(r"__HTML_OUT__")

ENABLE_YFINANCE = (r"__ENABLE_YFINANCE__".lower() == "true")
ENABLE_DUCKDB   = (r"__ENABLE_DUCKDB__".lower() == "true")
STOCK_ONLY      = (r"__STOCK_ONLY__".lower() == "true")
USE_SSOT        = (r"__USE_SSOT__" == "True")

# =============================================================================
# SSOT DUAL-PATH (v2.2 — true/false/null injection + traceback)
#   1. Inject JSON-style true/false/null as Python builtins (SSOT internal
#      contains JSON-style dict literals that NameError under Py3.12 dynamic
#      module load — spec_from_file_location triggers this path)
#   2. Try import VIA_SSOT_Unified from supportive_module
#   3. If fail, fall back to embedded dicts below
# =============================================================================
SSOT = None
SSOT_LOADED = False
SSOT_ERROR = ""
if USE_SSOT:
    try:
        import builtins as _b
        if not hasattr(_b, "true"):  _b.true  = True
        if not hasattr(_b, "false"): _b.false = False
        if not hasattr(_b, "null"):  _b.null  = None
        sys.path.insert(0, str(SUPPORT_DIR))
        import VIA_SSOT_Unified as _ssot_mod
        SSOT = _ssot_mod
        SSOT_LOADED = True
    except Exception as exc:
        SSOT_ERROR = f"{type(exc).__name__}: {exc}"
        try:
            SSOT_ERROR += " | tb: " + traceback.format_exc().splitlines()[-3].strip()[:120]
        except Exception:
            pass
        SSOT_LOADED = False


def ssot_extract(rule, text, fallback=""):
    """Try SSOT extract() with named rule; fall back to passed default."""
    if SSOT_LOADED and SSOT is not None:
        try:
            r = SSOT.extract(rule, text)
            return r if r is not None else fallback
        except Exception:
            return fallback
    return fallback


def ssot_normalize(value, fallback=None):
    if SSOT_LOADED and SSOT is not None:
        try:
            r = SSOT.normalize(value)
            return r if r is not None else (fallback if fallback is not None else value)
        except Exception:
            pass
    return fallback if fallback is not None else value


# =============================================================================
# SCHEMAS (UNCHANGED FROM v1)
# =============================================================================
BASIC_HEADERS = [
    "report_date","report_code","filename","broker","analyst","ticker",
    "yfinance_ticker","bloomberg_ticker","name","name_en","rating","rating_cat",
    "target_price","consensus_target_high","consensus_target_low",
    "consensus_target_mean","consensus_target_median","consensus_rating",
    "consensus_rating_mean","analyst_count","analyst_strong_buy","analyst_buy",
    "analyst_hold","analyst_sell","analyst_strong_sell","adj_close",
    "adj_close_date","upside_pct","upside_source","summary",
]
FIN_HEADERS = [
    "report_date","report_code","filename","broker","ticker","yfinance_ticker",
    "bloomberg_ticker","name","category","time_period","data_label","unit","value",
    "source","verification_confidence",
]
FIN_UI_HEADERS = FIN_HEADERS + ["備注"]

# =============================================================================
# DICTIONARIES — v1 ORIGINAL (PRESERVED) + v2.2 APPEND-ONLY
# =============================================================================

# ── v1 BROKER_ALIASES (PRESERVED, unchanged) ─────────────────────────────────
BROKER_ALIASES = {
    "兆豐": ["兆豐", "Mega"],
    "國泰": ["國泰", "Cathay", "國泰證期"],
    "台新": ["台新", "Taishin"],
    "統一": ["統一", "President"],
    "凱基": ["凱基", "KGI"],
    "華南": ["華南", "Hua Nan", "華南投顧", "華南永昌"],
    "中信": ["中信", "CTBC"],
    "元大": ["元大", "Yuanta"],
    "富邦": ["富邦", "Fubon"],
    "永豐": ["永豐", "SinoPac"],
    "Daiwa": ["Daiwa", "大和", "大和證券", "大和資本", "Daiwa Securities", "Daiwa Capital"],
    "GS":    ["GS", "Goldman", "Goldman Sachs", "高盛"],
    "MS":    ["MS", "Morgan Stanley", "摩根士丹利"],
    "JP":    ["JP", "JPM", "JPMorgan", "JP Morgan", "摩根大通"],
    "Citi":  ["Citi", "Citigroup", "花旗"],
    "UBS":   ["UBS", "瑞銀"],
    "CLSA":  ["CLSA", "CLST", "里昂"],
    # v2.2 APPEND
    "Nomura":   ["NMR", "Nomura", "野村", "野村證券"],
    "Mizuho":   ["Mizuho", "瑞穗"],
    "BAML":     ["BAML", "Bank of America", "美林", "Merrill Lynch"],
    "HSBC":     ["HSBC", "滙豐", "匯豐"],
    "DB":       ["DB", "Deutsche", "德意志"],
    "Barclays": ["Barclays", "巴克萊"],
    "GF":       ["GF"],
    "群益":     ["群益"],
    "新光":     ["新光"],
    "宏遠":     ["宏遠"],
    "第一金":   ["第一金", "First Securities"],
}

# ── v1 RATING_ALIASES (PRESERVED, unchanged) ─────────────────────────────────
RATING_ALIASES = {
    "strong_buy": ["強力買進", "strong buy", "strong-buy"],
    "buy":        ["買進", "買入", "buy", "overweight", "outperform", "增持", "加碼"],
    "hold":       ["中立", "持有", "hold", "neutral", "equal-weight", "market perform"],
    "sell":       ["賣出", "sell", "underweight", "underperform", "減碼"],
    "not_rated":  ["未評等", "無評等", "not rated", "nr"],
}

# ── v1 STOCK_TERMS (PRESERVED) + v2.2 APPEND ─────────────────────────────────
STOCK_TERMS = [
    # v1 original
    "個股", "個股報告", "訪談", "速報", "初次評等", "公司報告",
    "company report", "initiation", "equity research", "company update",
    "target price", "rating", "tp", "Daiwa", "大和",
    # v2.2 append (only-add per "功能只增不減")
    "個股介紹", "個股介紹報告", "評估報告", "Memo", "memo",
    "目標價", "合理價", "投資建議", "評等",
    "Buy", "Sell", "Hold", "Outperform", "Underperform", "Neutral",
    "Overweight", "Underweight",
    "中立", "買進", "賣出", "持有", "強力買進", "增持", "減碼", "加碼",
]

# ── v1 REJECT_TERMS (PRESERVED) + v2.2 APPEND ────────────────────────────────
REJECT_TERMS = [
    # v1 original
    "產業", "產業報告", "產業趨勢", "晨會", "晨會報告", "投資早報", "市場日報",
    "盤勢", "策略", "展望", "總經", "總體", "期貨", "日股", "美股", "港股",
    "海外", "commodity", "commodities", "macro", "strategy", "outlook", "industry",
    "sector", "market daily", "morning", "futures", "ETF", "etf",
    # v2.2 append — sector reports & talk topics
    "Memory", "Thermal Solutions", "Automation", "PCB CCL", "Hardware Insights",
    "Thoughts on", "大趨勢", "投資展望", "海外投資展望", "2026", "Asia Hardware",
]

# ── v2.2 NEW: STRONG_REJECT — these ALWAYS reject regardless of score ────────
# These keywords mark documents that are categorically NOT individual stock reports.
# Hit ANY one of these → is_stock=False immediately, no matter how many positive signals.
STRONG_REJECT_TERMS = [
    # Morning briefing / market commentary (not individual stock report)
    "晨會", "晨會報告", "盤勢", "盤勢分析",
    "投資早報", "早報", "市場日報", "Market Daily",
    # Other market segments (not TW stock)
    "期貨", "期貨晨間", "日股", "港股", "美股",
    # Macro / sector / trend talks (not individual stock)
    "大趨勢", "投資展望", "海外投資展望",
    "產業趨勢", "產業展望", "Hardware Insights", "Asia Hardware",
    # Sector reports (talking about sector, not single company)
    "Thoughts on", "Memory", "Thermal Solutions", "Automation",
    "PCB CCL", "AI PCB CCL",
]

# ── v2.2 NEW: BROKER_IN_FILENAME flat keyword list (strong stock signal) ─────
BROKER_IN_FN_KEYWORDS = []
for canon, arr in BROKER_ALIASES.items():
    for a in arr:
        if a not in BROKER_IN_FN_KEYWORDS:
            BROKER_IN_FN_KEYWORDS.append(a)

# ── v2.2 NEW: PDF body rating/target buy hints ───────────────────────────────
PDF_BUY_HINTS = [
    "target price", "目標價", "合理價", "TP:", "TP ", " TP=",
    "Rating:", "rating ", "Buy", "Sell", "Hold", "Outperform",
    "Underperform", "Neutral", "Overweight", "Underweight",
    "Equal-weight", "中立", "買進", "賣出", "持有", "投資建議",
]

SYNONYMS = {
    "revenue": ["營業收入", "營業收入淨額", "營收", "total revenue", "revenue", "sales", "net sales"],
    "cost_of_revenue": ["營業成本", "銷貨成本", "cost of revenue", "cogs"],
    "gross_profit": ["營業毛利", "營業毛利淨額", "毛利", "gross profit"],
    "operating_expenses": ["營業費用", "operating expenses", "opex"],
    "operating_income": ["營業利益", "營業利益淨額", "operating income", "operating profit", "ebit"],
    "pretax_income": ["稅前淨利", "稅前利益", "pretax income"],
    "tax_expense": ["所得稅", "tax expense", "income tax"],
    "net_income": ["本期淨利", "稅後純益", "稅後淨利", "net income", "net profit"],
    "basic_eps": ["基本每股盈餘", "basic eps"],
    "diluted_eps": ["稀釋每股盈餘", "diluted eps", "EPS"],
    "gross_margin": ["毛利率", "gross margin"],
    "operating_margin": ["營業利益率", "營益率", "operating margin"],
    "net_margin": ["純益率", "淨利率", "net margin"],
    "roe": ["股東權益報酬率", "roe"],
    "roa": ["總資產報酬率", "roa"],
    "pe_ratio": ["本益比", "per", "p/e", "pe ratio"],
    "pb_ratio": ["股價淨值比", "pbr", "p/b", "pb ratio"],
    "dividend_yield": ["殖利率", "dividend yield"],
    "total_assets": ["資產總額", "total assets"],
    "total_liabilities": ["負債總額", "total liabilities"],
    "total_equity": ["權益總額", "股東權益", "total equity"],
    "operating_cash_flow": ["營業活動現金流", "operating cash flow"],
    "investing_cash_flow": ["投資活動現金流", "investing cash flow"],
    "financing_cash_flow": ["籌資活動現金流", "financing cash flow"],
    "capex": ["資本支出", "capex"],
    "free_cash_flow": ["自由現金流", "free cash flow", "fcf"],
}
FIN_TABLE_KEYWORDS = [
    "營業收入", "營收", "毛利", "營業利益", "稅後", "淨利", "EPS", "每股盈餘",
    "資產", "負債", "權益", "現金流", "ROE", "ROA", "毛利率", "營益率",
    "income statement", "balance sheet", "cash flow", "revenue", "gross profit", "eps"
]

# =============================================================================
# UTILITIES (UNCHANGED)
# =============================================================================
def now_iso(): return datetime.now().isoformat(timespec="seconds")

def safe_str(x): return "" if x is None else str(x).strip()

def clean_text(x):
    s = safe_str(x).replace("\u3000", " ")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", s)
    s = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[A-Za-z0-9])", " ", s)
    s = re.sub(r"(?<=[A-Za-z0-9])\s+(?=[\u4e00-\u9fff])", " ", s)
    return s.strip()

def clean_number(x):
    s = safe_str(x)
    if not s: return ""
    if s.lower() in {"na","n.a.","nan","--","---"}: return ""
    s = s.replace(",", "").replace("%", "").replace(" ", "")
    s = re.sub(r"^\((.*?)\)$", r"-\1", s)
    s = s.replace("O","0").replace("o","0")
    try: return float(s)
    except Exception: return ""

def html_esc(x):
    s = safe_str(x)
    return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def write_json(path, data):
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def write_csv(path, headers, rows):
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for r in rows: w.writerow({h: r.get(h, "") for h in headers})

def sha16(path):
    p = Path(path)
    if not p.exists(): return ""
    import hashlib
    h = hashlib.sha256(); h.update(p.read_bytes())
    return h.hexdigest()[:16]

# =============================================================================
# INPUT DISCOVERY (UNCHANGED)
# =============================================================================
def list_input_files():
    allowed = {".pdf",".docx",".doc",".png",".jpg",".jpeg",".webp"}
    if not INPUT_DIR.exists(): return []
    return [p for p in sorted(INPUT_DIR.iterdir()) if p.is_file() and p.suffix.lower() in allowed]

def file_matrix_row(path, parsed=None, cls=None, preview=None):
    p = Path(path)
    return {
        "filename": p.name, "path": str(p), "suffix": p.suffix.lower(),
        "size_bytes": p.stat().st_size if p.exists() else 0,
        "size_mb": round((p.stat().st_size if p.exists() else 0)/1024/1024, 3),
        "sha16": sha16(p),
        "pages": parsed.get("pages","") if parsed else "",
        "parse_ok": parsed.get("ok",False) if parsed else False,
        "stock_score": cls.get("score","") if cls else "",
        "is_stock_report": cls.get("is_stock",False) if cls else False,
        "ticker": cls.get("ticker","") if cls else "",
        "broker": (preview or {}).get("broker","") if preview else "",
        "name":   (preview or {}).get("name","")   if preview else "",
        "rating": (preview or {}).get("rating_cat","") if preview else "",
        "strong_reject": ",".join(cls.get("strong_reject_terms",[])) if cls else "",
        "status": "STOCK_REPORT" if cls and cls.get("is_stock") else "REJECT_OR_PENDING",
    }

# =============================================================================
# PARSING (UNCHANGED FROM v1)
# =============================================================================
def parse_pdf(path):
    out = {"ok": False, "error": "", "blocks": [], "pages": 0}
    try:
        import fitz
    except Exception as exc:
        out["error"] = "PyMuPDF not available: " + str(exc); return out
    try:
        doc = fitz.open(str(path)); out["pages"] = len(doc)
        for page_index, page in enumerate(doc):
            page_no = page_index + 1; rect = page.rect
            page_dict = page.get_text("dict"); seq = 0
            for b in page_dict.get("blocks", []):
                seq += 1
                bbox = b.get("bbox", [0,0,0,0])
                raw_type = "IMAGE" if b.get("type") == 1 else "TEXT"
                text_lines = []; spans = []
                for line in b.get("lines", []):
                    line_text = ""
                    for span in line.get("spans", []):
                        st = span.get("text",""); line_text += st; spans.append(span)
                    if line_text.strip(): text_lines.append(line_text)
                text = clean_text("\n".join(text_lines))
                if not text and raw_type != "IMAGE": continue
                sizes = [float(s.get("size") or 0) for s in spans if s.get("size")]
                fonts = [str(s.get("font") or "") for s in spans]
                out["blocks"].append({
                    "source_file": str(path), "filename": path.name,
                    "page_no": page_no, "page_index": page_index,
                    "page_width": float(rect.width), "page_height": float(rect.height),
                    "seq": seq, "block_id": f"P{page_no:03d}_{raw_type}_{seq:05d}",
                    "raw_block_type": raw_type, "bbox": [float(x) for x in bbox],
                    "x0": float(bbox[0]), "y0": float(bbox[1]),
                    "x1": float(bbox[2]), "y1": float(bbox[3]),
                    "text": text,
                    "font_size_max": max(sizes) if sizes else 0,
                    "font_size_avg": sum(sizes)/len(sizes) if sizes else 0,
                    "bold": any("bold" in f.lower() for f in fonts),
                    "span_count": len(spans),
                })
        doc.close(); out["ok"] = True
    except Exception as exc:
        out["error"] = f"{type(exc).__name__}: {exc}"
    return out

def parse_docx(path):
    out = {"ok": False, "error": "", "blocks": [], "pages": 1}
    try: import docx
    except Exception as exc:
        out["error"] = "python-docx not available: " + str(exc); return out
    try:
        doc = docx.Document(str(path)); seq = 0
        for p in doc.paragraphs:
            text = clean_text(p.text)
            if not text: continue
            seq += 1
            out["blocks"].append({
                "source_file": str(path), "filename": path.name,
                "page_no": 1, "page_index": 0, "page_width": 1000.0, "page_height": 1400.0,
                "seq": seq, "block_id": f"P001_TEXT_{seq:05d}", "raw_block_type": "TEXT",
                "bbox": [0, seq*20, 1000, seq*20+18],
                "x0": 0, "y0": seq*20, "x1": 1000, "y1": seq*20+18,
                "text": text, "font_size_max": 10, "font_size_avg": 10,
                "bold": False, "span_count": 1,
            })
        out["ok"] = True
    except Exception as exc:
        out["error"] = f"{type(exc).__name__}: {exc}"
    return out

def parse_image(path):
    return {"ok": False, "error": "IMAGE_REGISTERED_ONLY: use M04/M05 OCR",
            "blocks": [], "pages": 0}

def parse_file(path):
    suf = path.suffix.lower()
    if suf == ".pdf": return parse_pdf(path)
    if suf in [".docx",".doc"]: return parse_docx(path)
    if suf in [".png",".jpg",".jpeg",".webp"]: return parse_image(path)
    return {"ok": False, "error": "unsupported", "blocks": [], "pages": 0}

# =============================================================================
# BASIC INFO EXTRACTORS (v2.2: try SSOT first, fallback to local regex)
# =============================================================================
def extract_ticker(text):
    # v2.2: SSOT first
    if SSOT_LOADED:
        r = ssot_extract("TW_TICKER", text, "")
        if r: return r
    # fallback
    patterns = [
        r"(?<!\d)(?!202[1-9])(?!2030)([1-9]\d{3})\s*TT\b",
        r"(?<!\d)(?!202[1-9])(?!2030)([1-9]\d{3})\.(TW|TWO)\b",
        r"(?<!\d)(?!202[1-9])(?!2030)([1-9]\d{3})(?!\d)",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.I)
        if m: return m.group(1)
    return ""

def extract_date(text):
    m = re.search(r"(20\d{2})[/-]?(\d{2})[/-]?(\d{2})", text)
    if m: return f"{m.group(1)}/{m.group(2)}/{m.group(3)}"
    m = re.search(r"(\d{3})[/-](\d{2})[/-](\d{2})", text)
    if m: return f"{int(m.group(1)) + 1911:04d}/{m.group(2)}/{m.group(3)}"
    return ""

def extract_broker(text):
    low = text.lower()
    for canon, arr in BROKER_ALIASES.items():
        for a in arr:
            if a.lower() in low: return canon
    return ""

def extract_broker_from_filename(filename):
    low = filename.lower()
    for kw in BROKER_IN_FN_KEYWORDS:
        # broker keyword should be at word boundary / dash / underscore for high precision
        if re.search(r"(^|[\s\-_\.])" + re.escape(kw.lower()) + r"([\s\-_\.\d]|$)", low):
            for canon, arr in BROKER_ALIASES.items():
                if kw in arr: return canon
            return kw
    return ""

def extract_rating(text):
    low = text.lower()
    for cat, arr in RATING_ALIASES.items():
        for a in arr:
            if a.lower() in low: return a, cat
    return "", ""

def extract_target_price(text):
    patterns = [
        r"(目標價|合理價|target price|price target|TP)\D{0,20}([0-9]+(?:\.[0-9]+)?)",
        r"([0-9]+(?:\.[0-9]+)?)\D{0,10}(目標價|target price|price target|TP)"
    ]
    for pat in patterns:
        m = re.search(pat, text, re.I)
        if m:
            for g in m.groups():
                v = clean_number(g)
                if v != "": return v
    return ""

def extract_analyst(text):
    m = re.search(r"(分析師|Analyst)\s*[:：]?\s*([A-Za-z\u4e00-\u9fff ,.\-]{2,80})", text, re.I)
    if m: return clean_text(m.group(2))
    return ""

def guess_name(filename, ticker, broker):
    stem = Path(filename).stem
    s = stem
    if ticker: s = s.replace(ticker, " ")
    if broker:
        for a in BROKER_ALIASES.get(broker, []):
            s = re.sub(re.escape(a), " ", s, flags=re.I)
    s = re.sub(r"20\d{6}", " ", s)
    s = re.sub(r"\d{4}[.\s]*(TW|TWO|TT)?", " ", s, flags=re.I)
    s = re.sub(r"[()\[\]【】（）_\-]+", " ", s)
    reject = {"個股報告","訪談速報","初次評等","買進","中立","賣出","報告","研究部","Daiwa","大和","Memo","個股介紹"}
    for c in re.findall(r"[\u4e00-\u9fffA-Za-z][\u4e00-\u9fffA-Za-z\-]{1,20}", s):
        if c not in reject and len(c) >= 2: return c
    return ""

def build_report_code(broker, ticker, name, report_date, filename):
    b = broker or "UNKNOWN"; t = ticker or "0000"
    n = name or "UNKNOWN"; d = re.sub(r"\D","", report_date or "")
    if len(d) < 8:
        m = re.search(r"(20\d{2})(\d{2})(\d{2})", filename)
        d = "".join(m.groups()) if m else "00000000"
    return f"{b}-{t}-{n}-{d[:8]}"

# =============================================================================
# CLASSIFIER (v2.2 — THE KEY FIX)
# =============================================================================
def classify_report(filename, blocks):
    """
    v2.2 classifier (append-only on v2.2 logic):
      ─── STAGE 1: STRONG_REJECT check (hits → immediate reject, no score) ───
      Any STRONG_REJECT_TERMS match in filename OR first page text → is_stock=False

      ─── STAGE 2: Score-based decision (only if no strong-reject) ────────────
      ticker_found                  +0.42
      broker_in_filename            +0.20
      stock_terms (any source)      +0.30
      pdf_buy_hints (rating/target) +0.20
      reject_terms                  -0.45
      multi_tickers (>=4) noise     -0.18
      THRESHOLD                     0.40
    is_stock = score>=0.40 AND ticker AND not (reject AND no signal)
    """
    first_page = "\n".join([b.get("text","") for b in blocks if int(b.get("page_no") or 1) == 1])
    probe = filename + "\n" + first_page[:7000]
    low = probe.lower()
    fn_low = filename.lower()

    ticker = extract_ticker(probe)
    stock_hits   = [x for x in STOCK_TERMS  if x.lower() in low]
    reject_hits  = [x for x in REJECT_TERMS if x.lower() in low]
    pdf_buy_hits = [x for x in PDF_BUY_HINTS if x.lower() in low]
    broker_in_fn = extract_broker_from_filename(filename)
    multi_tickers = len(set(re.findall(r"(?<!\d)(?!202[1-9])(?!2030)([1-9]\d{3})(?!\d)", probe))) >= 4

    # ── STAGE 1: STRONG_REJECT — categorical reject ──────────────────────────
    strong_reject_hits = [x for x in STRONG_REJECT_TERMS if x.lower() in low]
    if strong_reject_hits:
        return {
            "is_stock": False,
            "score": 0.0,
            "ticker": ticker,
            "stock_terms": stock_hits,
            "reject_terms": reject_hits,
            "strong_reject_terms": strong_reject_hits,
            "pdf_buy_hints": pdf_buy_hits,
            "broker_in_fn": broker_in_fn,
            "reasons": [f"STRONG_REJECT={strong_reject_hits[0]}"],
            "first_page_text": first_page[:5000],
            "classifier_version": "v2.2",
            "threshold": 0.40,
        }

    # ── STAGE 2: Normal score-based classification ───────────────────────────
    score = 0.0
    reasons = []
    if ticker:        score += 0.42; reasons.append(f"ticker={ticker}")
    if broker_in_fn:  score += 0.20; reasons.append(f"broker_fn={broker_in_fn}")
    if stock_hits:    score += 0.30; reasons.append(f"stock={stock_hits[0]}")
    if pdf_buy_hits:  score += 0.20; reasons.append(f"buy_hint={pdf_buy_hits[0]}")
    if reject_hits and not stock_hits:
        score -= 0.45; reasons.append(f"reject={reject_hits[0]}")
    if multi_tickers and not stock_hits:
        score -= 0.18; reasons.append("multi_ticker_noise")

    score = max(0.0, min(1.0, score))
    THRESHOLD = 0.40
    has_signal = bool(stock_hits) or bool(broker_in_fn) or bool(pdf_buy_hits)
    is_stock = (score >= THRESHOLD) and bool(ticker) and not (reject_hits and not has_signal)

    return {
        "is_stock": is_stock,
        "score": round(score, 4),
        "ticker": ticker,
        "stock_terms": stock_hits,
        "reject_terms": reject_hits,
        "strong_reject_terms": [],
        "pdf_buy_hints": pdf_buy_hits,
        "broker_in_fn": broker_in_fn,
        "reasons": reasons,
        "first_page_text": first_page[:5000],
        "classifier_version": "v2.2",
        "threshold": THRESHOLD,
    }

# =============================================================================
# LAYOUT / TEXT / TABLE (UNCHANGED FROM v1)
# =============================================================================
def assign_zone(block):
    if int(block.get("page_no") or 1) != 1: return "non_cover"
    w = float(block.get("page_width") or 1000); h = float(block.get("page_height") or 1400)
    x0, x1, y0 = float(block.get("x0") or 0), float(block.get("x1") or 0), float(block.get("y0") or 0)
    xc = (x0 + x1) / 2
    if y0 <= h*0.28 and xc <= w*0.50: return "cover_top_left"
    if y0 <= h*0.28 and xc >  w*0.50: return "cover_top_right"
    if h*0.20 < y0 <= h*0.55:         return "cover_center_title_body"
    if y0 > h*0.85:                   return "cover_footer"
    return "cover_body"

def detect_text_subtype(block, page_font_max):
    text = safe_str(block.get("text")); size = float(block.get("font_size_max") or 0)
    bold = bool(block.get("bold"))
    no_period = not re.search(r"[。！？.!?]$", text)
    if int(block.get("page_no") or 1) == 1 and size >= max(16, page_font_max*0.82) and no_period and len(text) <= 120:
        return "TITLE_MAJOR"
    if size >= max(13, page_font_max*0.68) and no_period and len(text) <= 150: return "TITLE_MID"
    if size >= 11.5 and (bold or no_period) and len(text) <= 180: return "TITLE_SMALL"
    if size <= 7.5: return "SMALL_TEXT_OR_FOOTNOTE"
    return "BODY"

def is_fin_table_line(text):
    if not text or not re.search(r"\d", text): return False
    low = text.lower()
    return any(k.lower() in low for k in FIN_TABLE_KEYWORDS)

def classify_blocks(blocks):
    page_font = {}
    for b in blocks:
        p = int(b.get("page_no") or 1)
        page_font[p] = max(page_font.get(p,0), float(b.get("font_size_max") or 0))
    out = []
    for i, b in enumerate(blocks, 1):
        nb = dict(b); text = nb.get("text",""); raw = nb.get("raw_block_type","")
        if raw == "IMAGE":   nb["block_type"]="FIGURE"; nb["subtype"]="FIGURE_OR_IMAGE"
        elif is_fin_table_line(text): nb["block_type"]="TABLE"; nb["subtype"]="TABLE_CANDIDATE_LINE"
        else: nb["block_type"]="TEXT"; nb["subtype"]=detect_text_subtype(nb, page_font.get(int(nb.get("page_no") or 1),0))
        nb["zone"] = assign_zone(nb)
        nb["element_id"] = nb.get("block_id") or f"E{i:06d}"
        out.append(nb)
    return out

def repair_text(blocks):
    text_blocks = [b for b in blocks if b.get("block_type")=="TEXT"]
    text_blocks.sort(key=lambda x: (int(x.get("page_no") or 1), float(x.get("y0") or 0), float(x.get("x0") or 0)))
    out = []; buffer = ""; meta = None
    for b in text_blocks:
        text = clean_text(b.get("text",""))
        if not text: continue
        subtype = b.get("subtype","")
        if subtype.startswith("TITLE"):
            if buffer:
                m=dict(meta or {}); m["text_repaired"]=buffer; m["repair_rule"]="join_until_sentence_end"; out.append(m)
                buffer,meta="",None
            m=dict(b); m["text_repaired"]=text; m["repair_rule"]="title_no_period"; out.append(m); continue
        if subtype == "SMALL_TEXT_OR_FOOTNOTE": continue
        if not buffer: buffer=text; meta=dict(b)
        else: buffer += text
        if re.search(r"[。！？.!?]$", buffer):
            m=dict(meta or b); m["text_repaired"]=buffer; m["repair_rule"]="join_until_sentence_end"
            out.append(m); buffer,meta="",None
    if buffer:
        m=dict(meta or {}); m["text_repaired"]=buffer; m["repair_rule"]="tail_flush"; out.append(m)
    return out

def lookup_synonym(label):
    low = safe_str(label).lower()
    for canon, arr in SYNONYMS.items():
        for a in arr:
            if a.lower() in low or low in a.lower(): return canon
    return label.strip()

def guess_fin_category(canon, raw=""):
    s = (canon + " " + raw).lower()
    if any(x in s for x in ["revenue","cost","gross_profit","operating_income","pretax","tax","net_income"]): return "IS"
    if any(x in s for x in ["assets","liabilities","equity"]): return "BS"
    if any(x in s for x in ["cash_flow","capex","free_cash_flow"]): return "CF"
    if any(x in s for x in ["margin","roe","roa","ratio","yield","pe_","pb_"]): return "RATIO"
    if "eps" in s: return "PER_SHARE"
    return "UNKNOWN"

def normalize_time(token):
    s = safe_str(token)
    m = re.search(r"(20\d{2})", s)
    if m: return m.group(1)
    m = re.search(r"(\d{2,3})年", s)
    if m:
        y = int(m.group(1))
        if y < 200: return str(y + 1911)
    m = re.search(r"(\d{2})Q[1-4]|[1-4]Q(\d{2})", s, re.I)
    if m:
        y = m.group(1) or m.group(2); return "20" + y
    return s

def extract_times(text):
    raw = re.findall(r"(20\d{2}[A-Za-z]*|\d{2}Q[1-4]|[1-4]Q\d{2}|\d{2,3}年|\d{4}Q[1-4])", text, re.I)
    out = []
    for x in raw:
        t = normalize_time(x)
        if t and t not in out: out.append(t)
    return out

def split_label_values(text):
    s = clean_text(text)
    m = re.search(r"(?<![A-Za-z])\(?-?\d[\d,]*(?:\.\d+)?\)?%?", s)
    if not m: return s, []
    label = s[:m.start()].strip()
    vals = s[m.start():].split()
    return label, vals

def build_tables(blocks):
    sorted_blocks = sorted(blocks, key=lambda x: (int(x.get("page_no") or 1), float(x.get("y0") or 0), float(x.get("x0") or 0)))
    tables = []
    current_times = []; current_rows = []; current_context = []; last_context = []

    def flush(filename=""):
        if not current_rows: return
        tid = f"T{len(tables)+1:04d}"
        tables.append({
            "table_id": tid, "filename": filename,
            "time_header": list(current_times),
            "context_up_3": list(current_context[-3:]),
            "rows": list(current_rows),
            "status": "RESTORED_TABLE_JSON_FIRST"
        })

    for b in sorted_blocks:
        text = clean_text(b.get("text",""))
        if b.get("block_type")=="TEXT":
            ctx = {"block_id": b.get("block_id"), "page_no": b.get("page_no"), "subtype": b.get("subtype"), "text": text[:300]}
            last_context.append(ctx); last_context = last_context[-3:]
            continue
        if b.get("block_type") != "TABLE": continue
        times = extract_times(text)
        label, vals = split_label_values(text)
        if len(times) >= 2 and len(vals) <= 2:
            if current_rows: flush(b.get("filename",""))
            current_times.clear(); current_times.extend(times)
            current_rows.clear()
            current_context = list(last_context[-3:])
            continue
        if vals:
            if not current_times: current_context = list(last_context[-3:])
            canon = lookup_synonym(label)
            current_rows.append({
                "filename": b.get("filename",""), "page_no": b.get("page_no"),
                "block_id": b.get("block_id"), "label_raw": label,
                "data_label": canon, "category": guess_fin_category(canon, label),
                "values_raw": vals, "values": [clean_number(v) for v in vals],
                "source_text": text,
            })
    flush("")
    return tables

# =============================================================================
# YFINANCE / CALC (UNCHANGED)
# =============================================================================
def yfinance_fetch_consensus(yfinance_ticker):
    result = {k: "" for k in [
        "consensus_target_high","consensus_target_low","consensus_target_mean",
        "consensus_target_median","consensus_rating","consensus_rating_mean",
        "analyst_count","analyst_strong_buy","analyst_buy","analyst_hold",
        "analyst_sell","analyst_strong_sell"]}
    result["_error"] = ""
    if not ENABLE_YFINANCE or not yfinance_ticker:
        result["_error"] = "disabled_or_empty"; return result
    try:
        import yfinance as yf
        t = yf.Ticker(yfinance_ticker)
        try:
            info = t.info or {}
            mapping = {
                "consensus_target_high":"targetHighPrice","consensus_target_low":"targetLowPrice",
                "consensus_target_mean":"targetMeanPrice","consensus_target_median":"targetMedianPrice",
                "consensus_rating":"recommendationKey","consensus_rating_mean":"recommendationMean",
                "analyst_count":"numberOfAnalystOpinions"}
            for k,src in mapping.items():
                result[k] = info.get(src,"") or ""
        except Exception as exc:
            result["_error"] += f"info:{type(exc).__name__}:{exc}; "
        try:
            rec = t.recommendations
            if rec is not None and len(rec) > 0:
                latest = rec.tail(1)
                for col,out_col in [("strongBuy","analyst_strong_buy"),("buy","analyst_buy"),
                                    ("hold","analyst_hold"),("sell","analyst_sell"),("strongSell","analyst_strong_sell")]:
                    if col in latest.columns:
                        result[out_col] = int(latest[col].iloc[0])
        except Exception as exc:
            result["_error"] += f"recommendations:{type(exc).__name__}:{exc}; "
    except Exception as exc:
        result["_error"] += f"yfinance:{type(exc).__name__}:{exc}"
    return result

def yfinance_fetch_adj_close(yfinance_ticker):
    result = {"adj_close":"","adj_close_date":"","_error":""}
    if not ENABLE_YFINANCE or not yfinance_ticker:
        result["_error"]="disabled_or_empty"; return result
    try:
        import yfinance as yf
        t = yf.Ticker(yfinance_ticker)
        hist = t.history(period="15d", auto_adjust=False)
        if hist is None or len(hist)==0:
            result["_error"]="empty_history"; return result
        last = hist.dropna(how="all").tail(1)
        col = "Adj Close" if "Adj Close" in last.columns else "Close"
        idx = last.index[0]
        result["adj_close"] = float(last[col].iloc[0])
        result["adj_close_date"] = str(idx.date()) if hasattr(idx,"date") else str(idx)[:10]
    except Exception as exc:
        result["_error"] = f"{type(exc).__name__}: {exc}"
    return result

def enrich_and_calc(row, source_map):
    yft = row.get("yfinance_ticker",""); yf_errors = {}
    consensus = yfinance_fetch_consensus(yft); yf_errors["consensus"] = consensus.get("_error","")
    for k in ["consensus_target_high","consensus_target_low","consensus_target_mean",
              "consensus_target_median","consensus_rating","consensus_rating_mean",
              "analyst_count","analyst_strong_buy","analyst_buy","analyst_hold",
              "analyst_sell","analyst_strong_sell"]:
        row[k] = consensus.get(k,""); source_map[k] = "YFinance_info/recommendations"
    adj = yfinance_fetch_adj_close(yft); yf_errors["adj_close"] = adj.get("_error","")
    row["adj_close"] = adj.get("adj_close",""); row["adj_close_date"] = adj.get("adj_close_date","")
    source_map["adj_close"] = "YFinance_history"; source_map["adj_close_date"] = "YFinance_history"
    tp = clean_number(row.get("target_price")); ac = clean_number(row.get("adj_close"))
    if tp != "" and ac != "" and ac != 0:
        row["upside_pct"] = round((tp - ac)/ac*100.0, 4)
        row["upside_source"] = "PDF_target / YFinance_adj_close"
        source_map["upside_pct"]="CALC"; source_map["upside_source"]="LINEAGE"
    else:
        row["upside_pct"]=""; row["upside_source"]="MISSING_target_or_adj_close"
        source_map["upside_pct"]="CALC_FAILED"; source_map["upside_source"]="LINEAGE"
    return yf_errors

# =============================================================================
# ROW BUILDERS (UNCHANGED)
# =============================================================================
def extract_topic(repaired_text):
    cands = []
    for b in repaired_text:
        if b.get("subtype","").startswith("TITLE"):
            txt = clean_text(b.get("text_repaired",""))
            if txt and not re.search(r"[。！？.!?]$", txt):
                cands.append((float(b.get("font_size_max") or 0), txt))
    cands.sort(key=lambda x: -x[0])
    return cands[0][1] if cands else ""

def build_basic_row(path, blocks, repaired_text, cls):
    filename = path.name
    first_page = cls.get("first_page_text","")
    probe = filename + "\n" + first_page
    ticker = cls.get("ticker") or extract_ticker(probe)
    broker = extract_broker(probe) or cls.get("broker_in_fn","")
    report_date = extract_date(probe)
    rating, rating_cat = extract_rating(probe)
    target_price = extract_target_price(probe)
    analyst = extract_analyst(probe)
    name = guess_name(filename, ticker, broker)
    topic = extract_topic(repaired_text)
    row = {h: "" for h in BASIC_HEADERS}
    row.update({
        "report_date": report_date, "filename": filename, "broker": broker,
        "analyst": analyst, "ticker": ticker,
        "yfinance_ticker": f"{ticker}.TW" if ticker else "",
        "bloomberg_ticker": f"{ticker} TT" if ticker else "",
        "name": name, "name_en": "", "rating": rating, "rating_cat": rating_cat,
        "target_price": target_price,
        "summary": " / ".join(([topic] if topic else []) + [b.get("text_repaired","") for b in repaired_text if len(b.get("text_repaired",""))>30][:3])[:1200],
    })
    row["report_code"] = build_report_code(broker, ticker, name, report_date, filename)
    source_map = {
        "report_date":"Filename+PDF_page1","report_code":"CALC","filename":"FILE",
        "broker":"Filename+PDF_page1","analyst":"PDF_page1","ticker":"Filename+PDF_page1",
        "yfinance_ticker":"CALC","bloomberg_ticker":"CALC","name":"Filename+PDF_page1",
        "rating":"PDF_page1","rating_cat":"NORMALIZE","target_price":"PDF_page1",
        "summary":"PDF_page1/LayoutText",
    }
    return row, source_map

def build_financial_rows(tables, basic_row):
    out = []
    for t in tables:
        times = t.get("time_header") or []
        if not times: continue
        for row in t.get("rows", []):
            values = row.get("values") or []
            for idx, tp in enumerate(times):
                val = values[idx] if idx < len(values) else ""
                if val == "": continue
                r = {h:"" for h in FIN_HEADERS}
                r.update({
                    "report_date": basic_row.get("report_date",""),
                    "report_code": basic_row.get("report_code",""),
                    "filename": row.get("filename") or basic_row.get("filename",""),
                    "broker": basic_row.get("broker",""), "ticker": basic_row.get("ticker",""),
                    "yfinance_ticker": basic_row.get("yfinance_ticker",""),
                    "bloomberg_ticker": basic_row.get("bloomberg_ticker",""),
                    "name": basic_row.get("name",""), "category": row.get("category","UNKNOWN"),
                    "time_period": normalize_time(tp), "data_label": row.get("data_label",""),
                    "unit": "mn_ntd", "value": val, "source": "Report",
                    "verification_confidence": "RESTORED_TABLE_STRUCTURAL",
                })
                out.append(r)
    return out

def fin_note(row):
    notes = []
    if not row.get("data_label"):  notes.append("缺 data_label")
    if not row.get("time_period"): notes.append("缺 time_period")
    if row.get("value") in ["", None]: notes.append("缺 value")
    if row.get("category") in ["","UNKNOWN"]: notes.append("category 未確認")
    if "STRUCTURAL" in str(row.get("verification_confidence","")):
        notes.append("表格結構還原，待 M06/M08 交叉驗證")
    return "；".join(notes) if notes else "OK"

# =============================================================================
# CONFIDENCE / HTML (UNCHANGED)
# =============================================================================
def basic_confidence(row, source_map):
    missing = [c for c in ["report_code","filename","ticker","name"] if not safe_str(row.get(c))]
    broker_ok = bool(safe_str(row.get("broker"))); target_ok = clean_number(row.get("target_price")) != ""
    adj_ok = clean_number(row.get("adj_close")) != ""; upside_ok = clean_number(row.get("upside_pct")) != ""
    lineage = str(row.get("upside_source",""))
    if missing: return "low","低可信","核心欄位缺失: " + ",".join(missing)
    if broker_ok and target_ok and adj_ok and upside_ok and "PDF_target / YFinance_adj_close" in lineage:
        return "high","交互驗證通過","PDF/Filename + YFinance + CALC 三源成立"
    if broker_ok and (target_ok or adj_ok or row.get("rating_cat")):
        return "medium","中等可信","身份欄位存在，但 YFinance 或 CALC 尚未完整"
    return "low","低可信","資料不足，需回看 PDF 首頁或外部驗證"

def fin_level(row):
    note = fin_note(row)
    if note == "OK": return "high"
    if "缺 value" in note or "缺 data_label" in note: return "low"
    return "medium"

def badge(text, cls):
    return f"<span class='badge {cls}'>{html_esc(text)}</span>"

def build_basic_rows_html(basic_rows, source_maps):
    trs = []
    ths = "<th class='sticky-left'>confidence</th>" + "".join(f"<th>{html_esc(h)}</th>" for h in BASIC_HEADERS)
    for r in basic_rows:
        level, label, reason = basic_confidence(r, source_maps.get(r.get("report_code",""), {}))
        tds = [f"<td class='sticky-left conf-{level}'>{badge(label, level)}<br><small>{html_esc(reason)}</small></td>"]
        for h in BASIC_HEADERS:
            val = r.get(h, "")
            cls = f" class='conf-{level} key-cell'" if h in ["report_code","broker","ticker","name","target_price","adj_close","upside_pct"] else ""
            if h == "summary":
                tds.append(f"<td{cls}><div class='summary-cell'>{html_esc(val)}</div></td>")
            else:
                tds.append(f"<td{cls}>{html_esc(val)}</td>")
        trs.append("<tr>" + "".join(tds) + "</tr>")
    return f"<table class='wide-table'><thead><tr>{ths}</tr></thead><tbody>{''.join(trs)}</tbody></table>"

def build_basic_cards_html(basic_rows, source_maps):
    cards = []
    for r in basic_rows:
        level, label, reason = basic_confidence(r, source_maps.get(r.get("report_code",""), {}))
        cards.append(
            '<div class="info-card conf-border-' + level + '">'
            '<div class="card-top"><div>'
            f'<div class="card-title">{html_esc(r.get("name") or r.get("filename"))}</div>'
            f'<div class="card-sub">{html_esc(r.get("ticker"))} · {html_esc(r.get("broker"))} · {html_esc(r.get("report_date"))}</div>'
            '</div>' + badge(label, level) + '</div>'
            '<div class="metric-grid">'
            f'<div><span>Rating</span><b>{html_esc(r.get("rating_cat"))}</b></div>'
            f'<div><span>Target</span><b>{html_esc(r.get("target_price"))}</b></div>'
            f'<div><span>Adj Close</span><b>{html_esc(r.get("adj_close"))}</b></div>'
            f'<div><span>Upside</span><b>{html_esc(r.get("upside_pct"))}</b></div>'
            '</div>'
            f'<div class="lineage">{html_esc(r.get("upside_source"))}</div>'
            f'<div class="summary-cell">{html_esc(r.get("summary"))}</div>'
            '</div>')
    return "\n".join(cards)

def build_fin_html(fin_rows):
    ths = "".join(f"<th>{html_esc(h)}</th>" for h in FIN_UI_HEADERS)
    trs = []
    for r in fin_rows:
        note = fin_note(r); level = fin_level(r)
        r2 = dict(r); r2["備注"] = note
        tds = []
        for h in FIN_UI_HEADERS:
            cls = f" class='conf-{level} bold-low'" if h=="備注" and level=="low" else (f" class='conf-{level}'" if h=="備注" else "")
            tds.append(f"<td{cls}>{html_esc(r2.get(h,''))}</td>")
        trs.append("<tr>" + "".join(tds) + "</tr>")
    return f"<table class='wide-table'><thead><tr>{ths}</tr></thead><tbody>{''.join(trs)}</tbody></table>"

def build_input_matrix_html(rows):
    trs = []
    for r in rows:
        level = "high" if r.get("is_stock_report") else "medium"
        if not r.get("parse_ok"): level = "low"
        if r.get("strong_reject"): level = "low"
        strong_html = ""
        if r.get("strong_reject"):
            strong_html = f'<span class="badge low" title="STRONG REJECT">{html_esc(r.get("strong_reject"))}</span>'
        trs.append(
            '<tr>'
            f'<td>{html_esc(r.get("filename"))}</td>'
            f'<td>{html_esc(r.get("suffix"))}</td>'
            f'<td>{html_esc(r.get("size_mb"))}</td>'
            f'<td>{html_esc(r.get("pages"))}</td>'
            f'<td class="mono">{html_esc(r.get("ticker"))}</td>'
            f'<td>{html_esc(r.get("broker"))}</td>'
            f'<td>{html_esc(r.get("name"))}</td>'
            f'<td>{html_esc(r.get("rating"))}</td>'
            f'<td class="mono">{html_esc(r.get("stock_score"))}</td>'
            f'<td class="conf-{level}">{html_esc(r.get("status"))} {strong_html}</td>'
            f'<td class="path">{html_esc(r.get("path"))}</td>'
            '</tr>')
    return ("<table><thead><tr>"
            "<th>檔名</th><th>類型</th><th>大小MB</th><th>頁數</th>"
            "<th>Ticker</th><th>Broker</th><th>Name</th><th>Rating</th>"
            "<th>Score</th><th>狀態</th><th>路徑</th>"
            "</tr></thead><tbody>" + "".join(trs) + "</tbody></table>")

def build_reject_html(rows):
    trs = []
    for r in rows:
        trs.append(f"<tr><td>{html_esc(r.get('filename'))}</td><td>{html_esc(r.get('score'))}</td><td>{html_esc('|'.join(r.get('reject_terms') or []))}</td><td>{html_esc('|'.join(r.get('reasons') or []))}</td><td>{html_esc(r.get('parse_error',''))}</td></tr>")
    return "<table><thead><tr><th>filename</th><th>score</th><th>reject_terms</th><th>reasons</th><th>parse_error</th></tr></thead><tbody>" + "".join(trs) + "</tbody></table>"

def build_source_html(source_maps):
    trs = []
    for rc, smap in source_maps.items():
        for k, v in smap.items():
            level = "high" if "YFinance" in str(v) or "PDF" in str(v) or "CALC" in str(v) else "medium"
            trs.append(f"<tr><td>{html_esc(rc)}</td><td>{html_esc(k)}</td><td class='conf-{level}'>{html_esc(v)}</td></tr>")
    return "<table><thead><tr><th>report_code</th><th>field</th><th>source</th></tr></thead><tbody>" + "".join(trs) + "</tbody></table>"

def get_visual_template_note():
    if VISUAL_TEMPLATE_PATH and VISUAL_TEMPLATE_PATH.exists():
        return f"Visual template detected: {VISUAL_TEMPLATE_PATH.name}"
    return "Visual template not found; using embedded visual-lock style."

def write_html(summary, basic_rows, fin_rows, rejects, input_matrix, source_maps):
    basic_conf = [basic_confidence(r, source_maps.get(r.get("report_code",""), {}))[0] for r in basic_rows]
    high = basic_conf.count("high"); med = basic_conf.count("medium"); low = basic_conf.count("low")
    fin_levels = [fin_level(r) for r in fin_rows]
    fin_high = fin_levels.count("high"); fin_med = fin_levels.count("medium"); fin_low = fin_levels.count("low")
    ssot_badge = badge(("SSOT loaded" if SSOT_LOADED else "SSOT fallback"), ("high" if SSOT_LOADED else "medium"))
    ssot_err_html = (f"<div class='small' style='color:#854d0e;margin-top:4px'>SSOT error: {html_esc(SSOT_ERROR)}</div>" if SSOT_ERROR else "")

    html = (
'<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">'
'<title>VRN Stock-Only Visual Locked Multi-Page U/I v2.2</title>'
'<style>'
':root{--bg:#f5f4f0;--sf:#fff;--bd:#dbd9d3;--bl:#4c78a8;--gn:#065f46;--gn-l:#d8f3dc;'
'--am:#854d0e;--am-l:#fef3c7;--co:#991b1b;--co-l:#fee2e2;--ink:#172033;--muted:#667085}'
'*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);'
'font-family:"DM Sans","Microsoft JhengHei","Segoe UI",Arial,sans-serif;font-size:11px}'
'.rainbow{background:linear-gradient(90deg,#ff6b6b,#feca57,#48dbfb,#1dd1a1,#5f27cd);height:4px}'
'header{background:linear-gradient(135deg,#0b1f18,#19382d);color:#fff;padding:24px 32px}'
'h1{margin:0;font-family:Syne,serif;font-weight:800;font-size:22px;letter-spacing:.02em}'
'.sub{margin-top:6px;color:#d6eadf;font-family:"DM Mono",monospace;font-size:10.5px}'
'.nav{position:sticky;top:0;z-index:50;background:#10231dee;backdrop-filter:blur(10px);padding:10px 24px;display:flex;gap:8px;flex-wrap:wrap}'
'.nav button{border:1px solid #315748;background:#173f32;color:#fff;border-radius:999px;padding:6px 12px;cursor:pointer;font-weight:700;font-size:11px}'
'.nav button.active{background:#2f7d5f}'
'.wrap{padding:20px 28px 60px}.page{display:none}.page.active{display:block}'
'.grid{display:grid;grid-template-columns:repeat(6,minmax(120px,1fr));gap:12px;margin-bottom:14px}'
'.card,.info-card{background:#fff;border:1px solid var(--bd);border-radius:14px;padding:14px;box-shadow:0 6px 18px rgba(16,24,40,.04)}'
'.k{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.05em}'
'.v{font-size:22px;font-weight:800;margin-top:4px;color:var(--bl);font-family:"DM Mono",monospace}'
'table{width:100%;border-collapse:collapse;font-size:11px;background:#fff}'
'th,td{padding:7px 8px;border-bottom:1px solid #edf0f4;text-align:left;vertical-align:top}'
'th{background:#fafafa;color:var(--bl);font-weight:700;text-transform:uppercase;font-size:10px;letter-spacing:.4px}'
'.table-scroll{overflow:auto;border:1px solid var(--bd);border-radius:14px;background:#fff;max-height:72vh}'
'.wide-table{min-width:2600px}'
'.sticky-left{position:sticky;left:0;z-index:8;background:#f7fbf8;min-width:190px}'
'.conf-high{background:var(--gn-l)!important;color:var(--gn)!important;font-weight:800}'
'.conf-medium{background:var(--am-l)!important;color:var(--am)!important;font-weight:800}'
'.conf-low{background:var(--co-l)!important;color:var(--co)!important;font-weight:900}'
'.badge{display:inline-block;border-radius:999px;padding:3px 8px;font-size:10.5px;font-weight:800}'
'.badge.high{background:var(--gn-l);color:var(--gn)}'
'.badge.medium{background:var(--am-l);color:var(--am)}'
'.badge.low{background:var(--co-l);color:var(--co)}'
'.conf-border-high{border-left:6px solid var(--gn)}'
'.conf-border-medium{border-left:6px solid var(--am)}'
'.conf-border-low{border-left:6px solid var(--co)}'
'.path{font-family:"DM Mono",monospace;font-size:10px;color:#ade8f4;background:#0f1419;padding:4px 8px;border-radius:6px;word-break:break-all}'
'.section-title{font-size:18px;font-weight:800;font-family:Syne,serif;margin:14px 0 8px;color:var(--bl)}'
'.card-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:14px}'
'.card-top{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}'
'.card-title{font-size:16px;font-weight:800}.card-sub{color:var(--muted);margin-top:3px}'
'.metric-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin:12px 0}'
'.metric-grid div{background:#f4f7f5;border-radius:10px;padding:8px}'
'.metric-grid span{display:block;color:var(--muted);font-size:11px}.metric-grid b{font-size:15px}'
'.lineage{font-family:"DM Mono",monospace;color:#315748;font-size:11px;margin:6px 0}'
'.summary-cell{max-width:680px;max-height:90px;overflow:auto;line-height:1.45}'
'.small{font-size:10.5px;color:var(--muted)}'
'</style></head><body>'
'<div class="rainbow"></div>'
'<header>'
'<h1>VRN Stock-Only Full Extract v2.2</h1>'
'<div class="sub">Classifier v2.2 · STRONG_REJECT enforced (晨會/盤勢/期貨/日股/港股/美股/投資早報/大趨勢/產業/展望) · SSOT dual-path with true/false/null injection · Generated ' + html_esc(summary.get("generated_at")) + '</div>'
'<div style="margin-top:6px">' + ssot_badge + ssot_err_html + '</div>'
'</header>'
'<div class="nav">'
'<button onclick="showPage(\'home\')" class="active">01 Base / Input</button>'
'<button onclick="showPage(\'basic-cards\')">02 BasicInfo 總覽</button>'
'<button onclick="showPage(\'basic-table\')">03 BasicInfo 30欄</button>'
'<button onclick="showPage(\'financial\')">04 FinancialData</button>'
'<button onclick="showPage(\'source\')">05 Source Map</button>'
'<button onclick="showPage(\'rejected\')">06 Rejected</button>'
'<button onclick="showPage(\'evidence\')">07 Evidence</button>'
'</div>'
'<div class="wrap">'
'<section id="home" class="page active">'
'<div class="grid">'
f'<div class="card"><div class="k">Input Files</div><div class="v">{summary.get("input_files")}</div></div>'
f'<div class="card"><div class="k">Stock Reports</div><div class="v">{summary.get("stock_reports")}</div></div>'
f'<div class="card"><div class="k">Rejected</div><div class="v">{summary.get("rejected_reports")}</div></div>'
f'<div class="card"><div class="k">Basic Rows</div><div class="v">{summary.get("basic_rows")}</div></div>'
f'<div class="card"><div class="k">Financial Rows</div><div class="v">{summary.get("financial_rows")}</div></div>'
f'<div class="card"><div class="k">Classifier</div><div class="v">v2.2</div></div>'
'</div>'
f'<div class="section-title">輸入矩陣 · 檔案 / Score / 個股判斷</div>'
f'<div class="table-scroll">{build_input_matrix_html(input_matrix)}</div>'
'</section>'
'<section id="basic-cards" class="page">'
'<div class="grid">'
f'<div class="card"><div class="k">High</div><div class="v" style="color:var(--gn)">{high}</div></div>'
f'<div class="card"><div class="k">Medium</div><div class="v" style="color:var(--am)">{med}</div></div>'
f'<div class="card"><div class="k">Low</div><div class="v" style="color:var(--co)">{low}</div></div>'
'</div>'
'<div class="section-title">BasicInfo 交互驗證卡片</div>'
f'<div class="card-grid">{build_basic_cards_html(basic_rows, source_maps)}</div>'
'</section>'
'<section id="basic-table" class="page">'
'<div class="section-title">BasicInfo 30 欄完整表</div>'
f'<div class="table-scroll">{build_basic_rows_html(basic_rows, source_maps)}</div>'
'</section>'
'<section id="financial" class="page">'
'<div class="grid">'
f'<div class="card"><div class="k">Financial Rows</div><div class="v">{len(fin_rows)}</div></div>'
f'<div class="card"><div class="k">High</div><div class="v" style="color:var(--gn)">{fin_high}</div></div>'
f'<div class="card"><div class="k">Medium</div><div class="v" style="color:var(--am)">{fin_med}</div></div>'
f'<div class="card"><div class="k">Low</div><div class="v" style="color:var(--co)">{fin_low}</div></div>'
'</div>'
'<div class="section-title">FinancialData 長表(最後一欄為「備注」)</div>'
f'<div class="table-scroll">{build_fin_html(fin_rows)}</div>'
'</section>'
'<section id="source" class="page">'
'<div class="section-title">Source Map / Lineage</div>'
f'<div class="table-scroll">{build_source_html(source_maps)}</div>'
'</section>'
'<section id="rejected" class="page">'
'<div class="section-title">Rejected Non-Stock / Parse Warnings</div>'
f'<div class="table-scroll">{build_reject_html(rejects)}</div>'
'</section>'
'<section id="evidence" class="page">'
'<div class="card">'
'<div class="section-title">Evidence Files</div>'
f'<p>{badge(get_visual_template_note(), "medium")}</p>'
f'<p class="path">Basic CSV: {BASIC_CSV}</p>'
f'<p class="path">Financial CSV: {FIN_CSV}</p>'
f'<p class="path">Rejected CSV: {REJECT_CSV}</p>'
f'<p class="path">Input Matrix JSON: {INPUT_MATRIX_JSON}</p>'
f'<p class="path">Blocks JSON: {BLOCKS_JSON}</p>'
f'<p class="path">Tables JSON: {TABLES_JSON}</p>'
f'<p class="path">Source Map JSON: {SOURCE_MAP_JSON}</p>'
f'<p class="path">Summary JSON: {SUMMARY_JSON}</p>'
f'<p class="path">DuckDB: {DUCKDB_PATH}</p>'
'</div>'
'</section>'
'</div>'
'<script>'
'function showPage(id){'
'document.querySelectorAll(".page").forEach(p=>p.classList.remove("active"));'
'document.querySelectorAll(".nav button").forEach(b=>b.classList.remove("active"));'
'document.getElementById(id).classList.add("active");'
'event.target.classList.add("active");'
'window.scrollTo({top:0,behavior:"smooth"});'
'}'
'</script></body></html>'
    )
    HTML_OUT.write_text(html, encoding="utf-8")

# =============================================================================
# DUCKDB (UNCHANGED)
# =============================================================================
def write_duckdb(basic_rows, fin_rows):
    status = {"enabled": False, "error": ""}
    if not ENABLE_DUCKDB:
        status["error"] = "duckdb disabled"; return status
    try:
        import duckdb
        status["enabled"] = True
        con = duckdb.connect(str(DUCKDB_PATH))
        con.execute("CREATE TABLE IF NOT EXISTS vrn_basic_info ("
                    "report_date VARCHAR, report_code VARCHAR PRIMARY KEY, filename VARCHAR,"
                    "broker VARCHAR, analyst VARCHAR, ticker VARCHAR, yfinance_ticker VARCHAR,"
                    "bloomberg_ticker VARCHAR, name VARCHAR, name_en VARCHAR, rating VARCHAR,"
                    "rating_cat VARCHAR, target_price DOUBLE, consensus_target_high DOUBLE,"
                    "consensus_target_low DOUBLE, consensus_target_mean DOUBLE,"
                    "consensus_target_median DOUBLE, consensus_rating VARCHAR,"
                    "consensus_rating_mean DOUBLE, analyst_count INTEGER,"
                    "analyst_strong_buy INTEGER, analyst_buy INTEGER, analyst_hold INTEGER,"
                    "analyst_sell INTEGER, analyst_strong_sell INTEGER, adj_close DOUBLE,"
                    "adj_close_date VARCHAR, upside_pct DOUBLE, upside_source VARCHAR,"
                    "summary VARCHAR, inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        con.execute("CREATE SEQUENCE IF NOT EXISTS seq_fin_id START 1")
        con.execute("CREATE TABLE IF NOT EXISTS vrn_financial_data ("
                    "report_date VARCHAR, report_code VARCHAR, filename VARCHAR, broker VARCHAR,"
                    "ticker VARCHAR, yfinance_ticker VARCHAR, bloomberg_ticker VARCHAR, name VARCHAR,"
                    "category VARCHAR, time_period VARCHAR, data_label VARCHAR,"
                    "unit VARCHAR DEFAULT 'mn_ntd', value DOUBLE, source VARCHAR DEFAULT 'Report',"
                    "verification_confidence VARCHAR, id BIGINT PRIMARY KEY DEFAULT nextval('seq_fin_id'),"
                    "inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        for r in basic_rows:
            vals = [r.get(c, None) if r.get(c,"") != "" else None for c in BASIC_HEADERS]
            con.execute(f"INSERT OR REPLACE INTO vrn_basic_info ({','.join(BASIC_HEADERS)}) VALUES ({','.join(['?']*len(BASIC_HEADERS))})", vals)
        for r in fin_rows:
            vals = [r.get(c, None) if r.get(c,"") != "" else None for c in FIN_HEADERS]
            con.execute(f"INSERT INTO vrn_financial_data ({','.join(FIN_HEADERS)}) VALUES ({','.join(['?']*len(FIN_HEADERS))})", vals)
        con.close()
    except Exception as exc:
        status["error"] = f"{type(exc).__name__}: {exc}"
    return status

# =============================================================================
# MAIN
# =============================================================================
def main():
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    files = list_input_files()
    all_blocks = []; all_tables = []; basic_rows = []; fin_rows = []
    rejects = []; source_maps = {}; yfinance_errors = {}; input_matrix = []

    for path in files:
        parsed = parse_file(path)
        raw_blocks = parsed.get("blocks", [])
        blocks = classify_blocks(raw_blocks)
        repaired = repair_text(blocks)
        tables = build_tables(blocks)
        cls = classify_report(path.name, blocks)

        # v2.2: pre-extract broker/name/rating for ALL files (so input matrix shows them)
        try:
            _first_page = cls.get("first_page_text","")
            _probe = path.name + "\n" + _first_page
            _ticker_p = cls.get("ticker") or extract_ticker(_probe)
            _broker_p = extract_broker(_probe) or cls.get("broker_in_fn","")
            _rating_p, _rating_cat_p = extract_rating(_probe)
            _name_p = guess_name(path.name, _ticker_p, _broker_p)
            preview = {"broker": _broker_p, "name": _name_p,
                       "rating": _rating_p, "rating_cat": _rating_cat_p}
        except Exception:
            preview = {"broker":"", "name":"", "rating":"", "rating_cat":""}

        input_matrix.append(file_matrix_row(path, parsed, cls, preview))

        if not parsed.get("ok"):
            rejects.append({
                "filename": path.name, "score": cls.get("score",0),
                "reject_terms": cls.get("reject_terms",[]),
                "reasons": ["parse_not_ok"] + cls.get("reasons",[]),
                "parse_error": parsed.get("error",""),
            }); continue

        if STOCK_ONLY and not cls.get("is_stock"):
            rejects.append({
                "filename": path.name, "score": cls.get("score",0),
                "reject_terms": cls.get("reject_terms",[]),
                "reasons": cls.get("reasons",[]), "parse_error": "",
            }); continue

        basic, smap = build_basic_row(path, blocks, repaired, cls)
        yferr = enrich_and_calc(basic, smap)
        these_fin = build_financial_rows(tables, basic)

        for b in blocks:
            b["report_code"] = basic.get("report_code",""); all_blocks.append(b)
        for t in tables:
            t["report_code"] = basic.get("report_code",""); all_tables.append(t)
        basic_rows.append(basic); fin_rows.extend(these_fin)
        source_maps[basic.get("report_code","")] = smap
        yfinance_errors[basic.get("report_code","")] = yferr

    dedup = {}
    for r in basic_rows:
        dedup[r.get("report_code") or r.get("filename")] = r
    basic_rows = list(dedup.values())

    duckdb_status = write_duckdb(basic_rows, fin_rows)

    write_csv(BASIC_CSV, BASIC_HEADERS, basic_rows)
    write_csv(FIN_CSV, FIN_HEADERS, fin_rows)
    write_csv(REJECT_CSV, ["filename","score","reject_terms","reasons","parse_error"], rejects)
    write_json(INPUT_MATRIX_JSON, input_matrix)
    write_json(BLOCKS_JSON, all_blocks)
    write_json(TABLES_JSON, all_tables)
    write_json(SOURCE_MAP_JSON, {"source_maps": source_maps, "yfinance_errors": yfinance_errors})

    summary = {
        "generated_at": now_iso(), "input_files": len(files),
        "stock_reports": len(basic_rows), "rejected_reports": len(rejects),
        "restored_blocks": len(all_blocks), "restored_tables": len(all_tables),
        "basic_rows": len(basic_rows), "financial_rows": len(fin_rows),
        "yfinance_enabled": ENABLE_YFINANCE, "duckdb": duckdb_status,
        "hard_pass": len(basic_rows) > 0,
        "policy": "STOCK_ONLY_v22_BROKER_BUY_HINTS_SSOT_DUAL_PATH",
        "classifier_version": "v2.2", "ssot_loaded": SSOT_LOADED,
        "ssot_error": SSOT_ERROR, "threshold": 0.40,
        "run_dir": str(RUN_DIR), "input_dir": str(INPUT_DIR), "output_dir": str(RUN_DIR),
        "visual_template_path": str(VISUAL_TEMPLATE_PATH) if VISUAL_TEMPLATE_PATH else "",
    }
    write_json(SUMMARY_JSON, summary)
    write_html(summary, basic_rows, fin_rows, rejects, input_matrix, source_maps)

    print(json.dumps({
        "hard_pass": summary["hard_pass"], "input_files": len(files),
        "stock_reports": len(basic_rows), "rejected_reports": len(rejects),
        "basic_rows": len(basic_rows), "financial_rows": len(fin_rows),
        "html": str(HTML_OUT), "basic_csv": str(BASIC_CSV), "fin_csv": str(FIN_CSV),
        "duckdb": str(DUCKDB_PATH),
        "ssot_loaded": SSOT_LOADED, "classifier_version": "v2.2",
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("[FATAL]"); print(traceback.format_exc()); raise
'@

    # PS-side placeholder substitution
    $Code = $Code.Replace("__VIA_ROOT__",       $script:VIA_ROOT)
    $Code = $Code.Replace("__VRN_DIR__",        $script:VRN_DIR)
    $Code = $Code.Replace("__INPUT_DIR__",      $script:INPUT_DIR)
    $Code = $Code.Replace("__SUPPORT_DIR__",    $script:SUPPORT_DIR)
    $Code = $Code.Replace("__RUN_DIR__",        $script:RUN_DIR)
    $Code = $Code.Replace("__VISUAL_TEMPLATE_PATH__", $VisualTemplatePath)
    $Code = $Code.Replace("__BASIC_CSV__",      $script:BASIC_CSV)
    $Code = $Code.Replace("__FIN_CSV__",        $script:FIN_CSV)
    $Code = $Code.Replace("__REJECT_CSV__",     $script:REJECT_CSV)
    $Code = $Code.Replace("__INPUT_MATRIX_JSON__", $script:INPUT_MATRIX_JSON)
    $Code = $Code.Replace("__BLOCKS_JSON__",    $script:BLOCKS_JSON)
    $Code = $Code.Replace("__TABLES_JSON__",    $script:TABLES_JSON)
    $Code = $Code.Replace("__SOURCE_MAP_JSON__", $script:SOURCE_MAP_JSON)
    $Code = $Code.Replace("__SUMMARY_JSON__",   $script:SUMMARY_JSON)
    $Code = $Code.Replace("__DUCKDB_PATH__",    $script:DUCKDB_PATH)
    $Code = $Code.Replace("__HTML_OUT__",       $script:HTML_OUT)
    $Code = $Code.Replace("__ENABLE_YFINANCE__", [string]$script:ENABLE_YFINANCE)
    $Code = $Code.Replace("__ENABLE_DUCKDB__",  [string]$script:ENABLE_DUCKDB)
    $Code = $Code.Replace("__STOCK_ONLY__",     [string]$script:STOCK_ONLY)
    $Code = $Code.Replace("__USE_SSOT__",       $useSsotFlag)

    Write-TextAtomic -Path $script:PY_SCRIPT -Text $Code
}

# =============================================================================
# MAIN
# =============================================================================
function Invoke-Main {
    Ensure-Dir $script:RUN_DIR
    Save-PhaseLog "=== VRN Stock-Only Visual Full v2.2 START ===" "Cyan"
    Save-PhaseLog ("VIA_ROOT  : " + $script:VIA_ROOT)
    Save-PhaseLog ("VRN_DIR   : " + $script:VRN_DIR)
    Save-PhaseLog ("INPUT_DIR : " + $script:INPUT_DIR)
    Save-PhaseLog ("RUN_DIR   : " + $script:RUN_DIR)
    Save-PhaseLog ("USE_SSOT  : " + $script:USE_SSOT)

    if (-not (Test-Path -LiteralPath $script:VRN_DIR))   { throw "VRN_DIR not found: $script:VRN_DIR" }
    if (-not (Test-Path -LiteralPath $script:INPUT_DIR)) { throw "INPUT_DIR not found: $script:INPUT_DIR" }

    $Python = Get-Python
    Save-PhaseLog ("Python   : " + $Python) "Green"

    $VisualTemplatePath = Get-VisualTemplate
    if ($VisualTemplatePath) {
        Save-PhaseLog ("Visual template: " + $VisualTemplatePath) "Green"
    } else {
        Save-PhaseLog "Visual template not found; using embedded style." "Yellow"
    }

    Save-PhaseLog "Writing embedded Python extractor v2.2..." "DarkCyan"
    Write-PythonExtractor

    Save-PhaseLog "py_compile syntax check..." "DarkCyan"
    & $Python -m py_compile $script:PY_SCRIPT
    if ($LASTEXITCODE -ne 0) { throw "Python extractor compile failed" }
    Save-PhaseLog "py_compile OK" "Green"

    Save-PhaseLog "Running VRN extractor v2.2..." "Cyan"
    & $Python -u $script:PY_SCRIPT
    if ($LASTEXITCODE -ne 0) { throw "Python extractor execution failed" }

    if ((Test-Path -LiteralPath $script:HTML_OUT) -and (-not $NoOpenHtml)) {
        Save-PhaseLog ("Opening HTML: " + $script:HTML_OUT) "Green"
        Start-Process $script:HTML_OUT
    }

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host " DONE · VRN STOCK-ONLY VISUAL FULL v2.2 COMPLETE" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ("[HTML]        " + $script:HTML_OUT)        -ForegroundColor Green
    Write-Host ("[SUMMARY]     " + $script:SUMMARY_JSON)    -ForegroundColor Green
    Write-Host ("[BASIC_CSV]   " + $script:BASIC_CSV)       -ForegroundColor Green
    Write-Host ("[FIN_CSV]     " + $script:FIN_CSV)         -ForegroundColor Green
    Write-Host ("[REJECT_CSV]  " + $script:REJECT_CSV)      -ForegroundColor Green
    Write-Host ("[INPUT_JSON]  " + $script:INPUT_MATRIX_JSON) -ForegroundColor Green
    Write-Host ("[BLOCKS]      " + $script:BLOCKS_JSON)     -ForegroundColor Green
    Write-Host ("[TABLES]      " + $script:TABLES_JSON)     -ForegroundColor Green
    Write-Host ("[SOURCE_MAP]  " + $script:SOURCE_MAP_JSON) -ForegroundColor Green
    Write-Host ("[DUCKDB]      " + $script:DUCKDB_PATH)     -ForegroundColor Green
    Write-Host ("[RUN]         " + $script:RUN_DIR)         -ForegroundColor Green
    Write-Host "PowerShell session remains open." -ForegroundColor Cyan
}

try {
    Invoke-Main
} catch {
    Write-Host ""
    Write-Host ("[FATAL] " + $_.Exception.Message) -ForegroundColor Red
    if ($_.ScriptStackTrace) { Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed }
    Write-Host "PowerShell session remains open." -ForegroundColor Yellow
}
