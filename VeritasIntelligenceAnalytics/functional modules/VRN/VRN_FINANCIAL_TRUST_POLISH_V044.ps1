#requires -Version 7.0
# ===== [VIA:PS-ACCEL:v0100] PS 20 加速器橋(批255 全樹導入;graceful 缺席零影響) =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====
<#
================================================================================
  VRN Financial Trust Polish v04.4
  Canonical de-collapse + Index whitelist + Two-stage Division + 19-col BasicInfo
  + LL#34 PS7 Test-Path parser fix + Add/Sub tolerance bands (PASS-SOFT/WARN/FAIL)

  v04.4 changes vs v04.3:
    1. Add/Sub now uses tolerance bands: PASS-EXACT(<=1%) / PASS-SOFT(<=5%) /
       WARN(<=10%) / FAIL(>10%) instead of binary PASS/FAIL.
    2. Division uses two-stage judgment: Stage A magnitude check ([0.5x..3.0x]),
       Stage B tolerance band. Sign-aware (handles negative ROE).
    3. Division ratio expected x100 to align with report % units
       (fixes v04.3 "ROE expected=0.07% actual=33.10%" bug).
    4. Full 19-column BasicInfo prepend in Financial Matrix / Formula Checks /
       Noise Quarantine tabs (Tony's locked column order).
    5. Formula Check tab now has Historical Check Confidence + Historical Check
       as columns 1-2 (was missing in v04.3).
    6. Final trust uses weighted-average + boost stacking; bands GREEN>=0.92,
       YELLOW>=0.78, ORANGE>=0.60, RED otherwise.
================================================================================
#>

param(
  [string]$SourceDir = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\_vrn_integrated_trust_runs",
  [string]$BasicInfoCsv = "vrn_basicinfo_validated_v041.csv",
  [string]$FinancialCsv = "vrn_financial_validated_v041.csv",
  [string]$Python = "C:\Users\tonyk\envs\via_core_312\Scripts\python.exe",
  [switch]$Open
)

#region -----------------------------------------------------------------------
# Setup
#region -----------------------------------------------------------------------

$ErrorActionPreference = 'Stop'
$VerbosePreference     = 'SilentlyContinue'

$script:TS         = Get-Date -Format "yyyyMMdd_HHmmss"
$script:RunName    = "VRN_FINANCIAL_TRUST_POLISH_V044_$($script:TS)"
$script:RunDir     = Join-Path $SourceDir $script:RunName
$script:LogPath    = Join-Path $script:RunDir "polish_v044.log"

function Write-Log {
  param([string]$Message, [string]$Level = "INFO")
  $ts = Get-Date -Format "HH:mm:ss"
  $line = "[$ts][$Level] $Message"
  Write-Host $line
  if (Test-Path -LiteralPath $script:RunDir) {
    Add-Content -LiteralPath $script:LogPath -Value $line -Encoding UTF8
  }
}

function Show-Prog {
  param([string]$Stage, [int]$Pct = -1)
  if ($Pct -ge 0) {
    Write-Host "[PROGRESS] [$Pct/100] $Stage" -ForegroundColor Cyan
  } else {
    Write-Host "[PROGRESS] $Stage" -ForegroundColor Cyan
  }
}

#endregion

#region -----------------------------------------------------------------------
# Locate latest v04.1 source directory
#region -----------------------------------------------------------------------

Show-Prog "Locating latest v04.1 source"

# LL#34 fix: each Test-Path wrapped in () so -and parses as logical operator
$candidateDirs = Get-ChildItem -LiteralPath $SourceDir -Directory -ErrorAction SilentlyContinue |
  Where-Object {
    $_.Name -match 'VRN_BASICINFO_FINANCIAL_TRUST_V041' -and
    (Test-Path -LiteralPath (Join-Path $_.FullName $BasicInfoCsv)) -and
    (Test-Path -LiteralPath (Join-Path $_.FullName $FinancialCsv))
  } |
  Sort-Object -Property @{e='LastWriteTime'; desc=$true}

if (-not $candidateDirs) {
  throw "No v04.1 source dir with both CSVs found under: $SourceDir"
}

$srcDir          = $candidateDirs[0].FullName
$srcBasicInfo    = Join-Path $srcDir $BasicInfoCsv
$srcFinancial    = Join-Path $srcDir $FinancialCsv

Write-Host "Source v04.1: $srcDir"
Write-Host "  BasicInfo : $srcBasicInfo"
Write-Host "  Financial : $srcFinancial"

#endregion

#region -----------------------------------------------------------------------
# Create output directory
#region -----------------------------------------------------------------------

New-Item -Path $script:RunDir -ItemType Directory -Force | Out-Null
Write-Log "Run directory created: $($script:RunDir)"

$outBasicCsv     = Join-Path $script:RunDir "vrn_basicinfo_validated_v044.csv"
$outBasicParquet = Join-Path $script:RunDir "vrn_basicinfo_validated_v044.parquet"
$outFinCsv       = Join-Path $script:RunDir "vrn_financial_validated_v044.csv"
$outFinParquet   = Join-Path $script:RunDir "vrn_financial_validated_v044.parquet"
$outNoiseCsv     = Join-Path $script:RunDir "vrn_financial_noise_quarantine_v044.csv"
$outJson         = Join-Path $script:RunDir "vrn_financial_trust_polish_v044.json"
$outHtml         = Join-Path $script:RunDir "vrn_financial_trust_polish_v044.html"

#endregion

#region -----------------------------------------------------------------------
# Embedded Python script
#region -----------------------------------------------------------------------

Show-Prog "Writing embedded Python pipeline" 10

$pyScript = Join-Path $script:RunDir "_v044_pipeline.py"

# Python source: docstring contained in $py via here-string. All Python logic
# (canonical de-collapse, build_index, historical/addsub/division checks,
# final trust aggregation, BasicInfo lookup, HTML rendering) is below.

$py = @'
# -*- coding: utf-8 -*-
"""
VRN Financial Trust Polish v04.4 - embedded Python pipeline
Generated by PS7 wrapper. Reads v04.1 CSVs -> writes v04.4 CSV/parquet/JSON/HTML.
"""
import sys, os, json, csv, re, datetime, html
from statistics import median

if len(sys.argv) < 8:
    print("Usage: pipeline.py SRC_BASIC SRC_FIN OUT_BASIC OUT_FIN OUT_NOISE OUT_JSON OUT_HTML")
    sys.exit(2)

(SRC_BASIC, SRC_FIN, OUT_BASIC, OUT_FIN, OUT_NOISE, OUT_JSON, OUT_HTML) = sys.argv[1:8]
RUN_NAME = os.path.basename(os.path.dirname(OUT_JSON))


# ============================================================
# BasicInfo column order (locked - 19 cols in Tony's specified order)
# ============================================================
BASICINFO_COLS = [
    "Report Date", "Report Code", "Broker", "Analyst",
    "Ticker", "YFinance Ticker", "Bloomberg Ticker", "Name",
    "Rating", "Target Price", "Last Adj Close", "Last Data Date",
    "YFinance Consensus Target Price Low",
    "YFinance Consensus Target Price Mean",
    "YFinance Consensus Target Price Median",
    "YFinance Consensus Target Price High",
    "YFinance Rating Breakdown",
    "YFinance Analyst Count Breakdown",
    "Validation Status",
]


# ============================================================
# Canonical de-collapse
# ============================================================
DERIVED_HINT_PAT = re.compile(
    r"(PS|per share|每股|YoY|QoQ|growth|成長率|payout|配息|ratio|比率"
    r"|margin|率$|EV/|P/|PE|PB|days|天|turnover|週轉|\(%\)|％|\(x\)|倍|cover|\(NT\$|\$\))",
    re.IGNORECASE,
)

# Main-account whitelist - only these enter the index for cross-check formulas
MAIN_ACCOUNT_WHITELIST = {
    "Revenue", "COGS", "Gross Profit",
    "Operating Expense", "Operating Income", "Non-Operating Income",
    "Pre-tax Income", "Tax", "Net Income", "Diluted EPS",
    "Cash and Equivalents", "Accounts Receivable", "Inventory",
    "Current Assets", "Fixed Assets", "Total Assets",
    "Current Liabilities", "Non-current Liabilities", "Total Liabilities",
    "Total Equity",
    "Operating Cash Flow", "CapEx", "Free Cash Flow",
    "Financing Cash Flow", "Investing Cash Flow",
    "Net Change in Cash",
}

# Main-account mapping table (v04.3 -> v04.4) - applies only when item lacks
# a derived-metric hint. Maps Chinese/English variants to canonical English.
MAIN_ACCOUNT_MAP = {
    # Revenue
    "revenue": "Revenue", "sales": "Revenue", "營收": "Revenue",
    "營業收入": "Revenue", "net sales": "Revenue", "total revenue": "Revenue",
    # COGS
    "cogs": "COGS", "cost of goods sold": "COGS", "cost of sales": "COGS",
    "銷貨成本": "COGS", "營業成本": "COGS",
    # Gross Profit
    "gross profit": "Gross Profit", "毛利": "Gross Profit", "營業毛利": "Gross Profit",
    # Operating Expense
    "operating expense": "Operating Expense", "opex": "Operating Expense",
    "營業費用": "Operating Expense",
    # Operating Income
    "operating income": "Operating Income", "operating profit": "Operating Income",
    "營業利益": "Operating Income", "營業淨利": "Operating Income",
    "operating result": "Operating Income",
    # Non-operating
    "non-op": "Non-Operating Income", "non-operating income": "Non-Operating Income",
    "業外收入": "Non-Operating Income", "業外損益": "Non-Operating Income",
    # Pre-tax
    "pretax profit": "Pre-tax Income", "pre-tax income": "Pre-tax Income",
    "稅前淨利": "Pre-tax Income", "稅前純益": "Pre-tax Income",
    # Tax
    "tax": "Tax", "income tax": "Tax", "所得稅": "Tax",
    # Net Income
    "net income": "Net Income", "net profit": "Net Income",
    "稅後淨利": "Net Income", "本期淨利": "Net Income", "淨利": "Net Income",
    # EPS
    "eps": "Diluted EPS", "diluted eps": "Diluted EPS",
    "每股盈餘": "Diluted EPS",
    # Cash
    "cash and equivalents": "Cash and Equivalents",
    "cash & equivalents": "Cash and Equivalents",
    "現金及約當現金": "Cash and Equivalents", "cash": "Cash and Equivalents",
    "期初現金與約當現金餘額": "Cash and Equivalents",
    "期末現金與約當現金餘額": "Cash and Equivalents",
    "本期現金與約當現金增加數": "Cash and Equivalents",
    # AR
    "accounts receivable": "Accounts Receivable",
    "應收帳款及票據": "Accounts Receivable", "應收帳款與票據": "Accounts Receivable",
    "trade receivables": "Accounts Receivable",
    # Inventory
    "inventory": "Inventory", "inventories": "Inventory", "存貨": "Inventory",
    # Current Assets
    "current assets": "Current Assets", "流動資產": "Current Assets",
    "流動資產合計": "Current Assets", "非流動資產合計": "Current Assets",
    "other current assets": "Current Assets", "other non-current assets": "Current Assets",
    # Fixed Assets
    "fixed assets": "Fixed Assets", "不動產、廠房及設備": "Fixed Assets",
    "固定資產": "Fixed Assets",
    # Total Assets
    "total assets": "Total Assets", "資產總計": "Total Assets",
    "資產總額": "Total Assets",
    # Current Liabilities
    "current liabilities": "Current Liabilities",
    "流動負債": "Current Liabilities", "流動負債合計": "Current Liabilities",
    # Non-current Liabilities
    "non-current liabilities": "Non-current Liabilities",
    "其他非流動負債": "Non-current Liabilities",
    "長期負債合計": "Non-current Liabilities",
    "非流動負債": "Non-current Liabilities",
    # Total Liabilities
    "total liabilities": "Total Liabilities",
    "負債總計": "Total Liabilities", "負債總額": "Total Liabilities",
    # Total Equity
    "total equity": "Total Equity", "shareholder funds": "Total Equity",
    "權益總計": "Total Equity", "負債與權益總計": "Total Equity",
    "負債及權益總計": "Total Equity",
    # Cash flows
    "operating cash flow": "Operating Cash Flow",
    "net operating cashflow": "Operating Cash Flow",
    "營業活動之淨現金流入": "Operating Cash Flow",
    "營業活動現金流量": "Operating Cash Flow",
    "capex": "CapEx", "capital expenditure": "CapEx",
    "資本支出": "CapEx",
    "free cash flow": "Free Cash Flow", "free cashflow": "Free Cash Flow",
    "自由現金流": "Free Cash Flow", "自由現金流量": "Free Cash Flow",
    "financing cash flow": "Financing Cash Flow",
    "net financing cashflow": "Financing Cash Flow",
    "融資活動之淨現金流入(出)": "Financing Cash Flow",
    "其他籌資活動現金流量": "Financing Cash Flow",
    "investing cash flow": "Investing Cash Flow",
    "投資活動之淨現金流入(出)": "Investing Cash Flow",
    # Net change in cash
    "incr/(decr) in net cash": "Net Change in Cash",
    "net change in cash": "Net Change in Cash",
    "現金及約當現金增減": "Net Change in Cash",
}


def canonical_item_name(item):
    """De-collapse derived metrics; only collapse explicit margin/ratio names."""
    if not item:
        return ""
    s = str(item).strip()
    if not s:
        return ""

    # If item carries a derived-metric hint, return as-is (no collapse to main account)
    if DERIVED_HINT_PAT.search(s):
        low = s.lower()
        if "gross margin" in low:    return "Gross Margin"
        if "operating margin" in low or "op margin" in low: return "Operating Margin"
        if "net margin" in low:      return "Net Margin"
        if low.strip() in ("roe", "roe (%)", "roe(%)"):  return "ROE"
        if low.strip() in ("roa", "roa (%)", "roa(%)"):  return "ROA"
        if "inventory turnover" in low or "存貨週轉" in s: return "Inventory Turnover"
        if "receivable turnover" in low or "應收週轉" in s: return "Receivable Turnover"
        return s

    # No hint: try main-account mapping
    low = s.lower()
    if low in MAIN_ACCOUNT_MAP:
        return MAIN_ACCOUNT_MAP[low]
    # Try Chinese match (raw, lower-stripped)
    if s in MAIN_ACCOUNT_MAP:
        return MAIN_ACCOUNT_MAP[s]

    return s


# ============================================================
# Build index (whitelist-gated)
# ============================================================
def build_index(rows):
    idx = {}
    for r in rows:
        canon = r.get("canonical", "")
        if canon not in MAIN_ACCOUNT_WHITELIST:
            continue
        year = r.get("year")
        if not year:
            continue
        try:
            year = int(year)
        except (ValueError, TypeError):
            continue
        key = (r.get("filename", ""), r.get("ticker", ""), canon, year)
        val = r.get("value")
        if val is None:
            continue
        idx.setdefault(key, []).append(val)
    return {k: median(v) for k, v in idx.items()}


def get_latest_in_file(idx, filename, ticker, canon):
    matching = [k[3] for k in idx
                if k[0] == filename and k[1] == ticker and k[2] == canon]
    if not matching:
        return None
    return idx.get((filename, ticker, canon, max(matching)))


# ============================================================
# Historical / Add-Sub / Division checks
# ============================================================
def historical_check(canon, year, value, idx, filename, ticker):
    if canon not in MAIN_ACCOUNT_WHITELIST:
        return (0.70, "DERIVED_METRIC_NO_HISTORICAL", None)
    if not year or value is None:
        return (0.40, "NO_YEAR_OR_VALUE", None)
    try:
        y = int(year)
    except (ValueError, TypeError):
        return (0.40, "NO_YEAR_OR_VALUE", None)
    prev_key = (filename, ticker, canon, y - 1)
    if prev_key not in idx:
        return (0.62, "NO_PREVIOUS_YEAR_IN_REPORT", None)
    prev = idx[prev_key]
    if prev == 0:
        return (0.62, "PREV_YEAR_ZERO", None)
    yoy = abs(value - prev) / abs(prev) * 100
    if yoy < 30:
        return (0.94, f"HISTORICAL_OK_YOY={yoy:.2f}%", yoy)
    if yoy < 100:
        return (0.78, f"HISTORICAL_MEDIUM_YOY={yoy:.2f}%", yoy)
    return (0.55, f"HISTORICAL_OUTLIER_YOY={yoy:.2f}%", yoy)


def _tolerance_band(actual, expected, label):
    if expected == 0:
        return (0.72, f"NO_BASIS_{label}")
    diff_pct = abs(actual - expected) / abs(expected) * 100
    if diff_pct <= 1:
        return (0.96, f"PASS-EXACT {label} expected={expected:.2f}")
    if diff_pct <= 5:
        return (0.88, f"PASS-SOFT {label} expected={expected:.2f} diff={diff_pct:.1f}%")
    if diff_pct <= 10:
        return (0.70, f"WARN {label} expected={expected:.2f} diff={diff_pct:.1f}%")
    return (0.45, f"FAIL {label} expected={expected:.2f} diff={diff_pct:.1f}%")


def _two_stage_division(actual, expected, label):
    if expected == 0:
        return (0.72, f"NO_BASIS_{label}")
    if (actual * expected) < 0:
        return (0.45, f"FAIL-RANGE {label} expected={expected:.2f}% actual={actual:.2f}% (sign mismatch)")
    abs_e, abs_a = abs(expected), abs(actual)
    if not (abs_e * 0.5 <= abs_a <= abs_e * 3.0):
        return (0.45, f"FAIL-RANGE {label} expected={expected:.2f}% actual={actual:.2f}%")
    diff_pct = abs(actual - expected) / abs(expected) * 100
    if diff_pct <= 1:
        return (0.96, f"PASS-EXACT {label} expected={expected:.2f}% actual={actual:.2f}%")
    if diff_pct <= 5:
        return (0.88, f"PASS-SOFT {label} expected={expected:.2f}% actual={actual:.2f}% diff={diff_pct:.1f}%")
    if diff_pct <= 10:
        return (0.70, f"WARN {label} expected={expected:.2f}% actual={actual:.2f}% diff={diff_pct:.1f}%")
    return (0.85, f"PASS-RANGE {label} expected={expected:.2f}% actual={actual:.2f}% diff={diff_pct:.1f}%")


def add_sub_check(canon, year, value, idx, filename, ticker):
    if not year or value is None:
        return (0.72, "NO_ADD_SUB_FORMULA_APPLICABLE")
    try:
        y = int(year)
    except (ValueError, TypeError):
        return (0.72, "NO_ADD_SUB_FORMULA_APPLICABLE")
    if canon == "Total Liabilities":
        cur = idx.get((filename, ticker, "Current Liabilities", y))
        ncl = idx.get((filename, ticker, "Non-current Liabilities", y))
        if cur is not None and ncl is not None:
            return _tolerance_band(value, cur + ncl, "Liabilities=Current+NonCurrent")
    if canon == "Total Assets":
        ca = idx.get((filename, ticker, "Current Assets", y))
        fa = idx.get((filename, ticker, "Fixed Assets", y))
        if ca is not None and fa is not None:
            return _tolerance_band(value, ca + fa, "Assets=Current+Fixed")
    if canon == "Free Cash Flow":
        cfo = idx.get((filename, ticker, "Operating Cash Flow", y))
        capex = idx.get((filename, ticker, "CapEx", y))
        if cfo is not None and capex is not None:
            return _tolerance_band(value, cfo - abs(capex), "FCF=CFO-CapEx")
    return (0.72, "NO_ADD_SUB_FORMULA_APPLICABLE")


def division_check(canon, year, value, idx, filename, ticker):
    if value is None:
        return (0.72, "NO_DIVISION_FORMULA_APPLICABLE")
    if year:
        try:
            y = int(year)
        except (ValueError, TypeError):
            y = None
    else:
        y = None

    def _resolve(item):
        if y is not None:
            v = idx.get((filename, ticker, item, y))
            if v is not None:
                return v
        return get_latest_in_file(idx, filename, ticker, item)

    if canon == "ROE":
        ni = _resolve("Net Income"); eq = _resolve("Total Equity")
        if ni is not None and eq and eq != 0:
            return _two_stage_division(value, (ni / eq) * 100, "ROE")
    if canon == "ROA":
        ni = _resolve("Net Income"); ta = _resolve("Total Assets")
        if ni is not None and ta and ta != 0:
            return _two_stage_division(value, (ni / ta) * 100, "ROA")
    if canon == "Gross Margin":
        gp = _resolve("Gross Profit"); rev = _resolve("Revenue")
        if gp is not None and rev and rev != 0:
            return _two_stage_division(value, (gp / rev) * 100, "GrossMargin")
    if canon == "Operating Margin":
        op = _resolve("Operating Income"); rev = _resolve("Revenue")
        if op is not None and rev and rev != 0:
            return _two_stage_division(value, (op / rev) * 100, "OperatingMargin")
    if canon == "Net Margin":
        ni = _resolve("Net Income"); rev = _resolve("Revenue")
        if ni is not None and rev and rev != 0:
            return _two_stage_division(value, (ni / rev) * 100, "NetMargin")
    return (0.72, "NO_DIVISION_FORMULA_APPLICABLE")


def final_trust(hist_c, addsub_c, div_c):
    score = hist_c * 0.40 + addsub_c * 0.30 + div_c * 0.30
    if addsub_c >= 0.96: score += 0.04
    elif addsub_c >= 0.88: score += 0.025
    if div_c >= 0.96: score += 0.04
    elif div_c >= 0.88: score += 0.025
    elif div_c >= 0.85: score += 0.015
    if hist_c >= 0.88 and addsub_c >= 0.88 and div_c >= 0.88:
        score += 0.02
    score = round(min(0.99, score), 4)
    if score >= 0.92: return (score, "GREEN")
    if score >= 0.78: return (score, "YELLOW")
    if score >= 0.60: return (score, "ORANGE")
    return (score, "RED")


# ============================================================
# BasicInfo lookup
# ============================================================
def build_basicinfo_lookup(basicinfo_rows):
    by_ticker = {}
    by_filename = {}
    for r in basicinfo_rows:
        rec = {col: (r.get(col) or "") for col in BASICINFO_COLS}
        t = (rec.get("Ticker") or "").strip()
        f = (r.get("Filename") or "").strip()
        if t:
            by_ticker[t] = rec
        if f:
            by_filename[f] = rec
    return by_ticker, by_filename


def get_basicinfo(by_ticker, by_filename, ticker, filename):
    if ticker and ticker.strip() in by_ticker:
        return by_ticker[ticker.strip()]
    if filename and filename.strip() in by_filename:
        return by_filename[filename.strip()]
    return {col: "" for col in BASICINFO_COLS}


# ============================================================
# Read CSV (UTF-8 with BOM tolerant)
# ============================================================
def read_csv(path):
    out = []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            out.append(row)
    return out


def write_csv(path, rows, fieldnames):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def to_float(x):
    if x is None or x == "":
        return None
    try:
        return float(str(x).replace(",", "").strip())
    except (ValueError, TypeError):
        return None


def to_int_year(x):
    if x is None or x == "":
        return None
    s = str(x).strip()
    if not s:
        return None
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return None


# ============================================================
# Noise classification
# ============================================================
def is_noise(row):
    """Return (is_noise_bool, reason_string)."""
    cat = (row.get("Category") or "").strip()
    data = (row.get("Data") or "").strip()
    year = (row.get("Year") or "").strip()
    value = row.get("Value")

    # Unit row (contains 單位)
    if "單位" in data:
        return (True, "UNIT_ROW")

    # Pure numeric data in unclassified table (PURE_NUMERIC_DATA_IN_UNCLASSIFIED_TABLE)
    if cat == "Unclassified Financial Table":
        # Pure numeric data string
        if re.match(r"^[\d,\.\-]+$", data.replace(" ", "")):
            return (True, "PURE_NUMERIC_DATA_IN_UNCLASSIFIED_TABLE")
        # Year is given but data is just the year repeated, or non-meaningful
        # Common pattern: data="QOQ" or "YOY" or "Average" "Max" "Min" "Median" "Standard Deviation"
        if not year and data in {"QOQ", "YOY", "Average", "Max", "Min", "Median",
                                  "Standard Deviation", "Minimum"}:
            return (True, "NO_YEAR_AND_UNCLASSIFIED")

    return (False, "")


# ============================================================
# Main pipeline
# ============================================================
print(f"[PY] Loading v04.1 source CSVs...")
basic_rows_raw = read_csv(SRC_BASIC)
fin_rows_raw   = read_csv(SRC_FIN)
print(f"[PY] BasicInfo rows: {len(basic_rows_raw)}")
print(f"[PY] Financial rows in: {len(fin_rows_raw)}")

# Write v04.4 BasicInfo CSV (passthrough with all 19 cols + Filename)
basic_fieldnames = (["Filename"] + BASICINFO_COLS)
write_csv(OUT_BASIC, basic_rows_raw, basic_fieldnames)
print(f"[PY] BasicInfo CSV -> {OUT_BASIC}")

# Build BasicInfo lookup
by_t, by_f = build_basicinfo_lookup(basic_rows_raw)
print(f"[PY] BasicInfo lookups: {len(by_t)} by ticker / {len(by_f)} by filename")

# Classify noise + build canonical-form financial rows
keep_rows = []
noise_rows = []

for r in fin_rows_raw:
    item = (r.get("Data") or "").strip()
    canon = canonical_item_name(item)
    year_raw = (r.get("Year") or "").strip()
    value = to_float(r.get("Value"))
    fn = (r.get("Filename") or "").strip()
    tkr = (r.get("Ticker") or "").strip()
    cat = (r.get("Category") or "").strip()

    enriched = dict(r)
    enriched["Canonical Data"] = canon

    # Noise check
    noise_flag, noise_reason = is_noise(r)
    if noise_flag:
        enriched["Data Quality Gate"] = "NOISE_QUARANTINE"
        enriched["Data Quality Reason"] = noise_reason
        noise_rows.append(enriched)
        continue

    # Keep it
    enriched["Data Quality Gate"] = "KEEP"
    enriched["filename"] = fn
    enriched["ticker"] = tkr
    enriched["canonical"] = canon
    enriched["year"] = year_raw
    enriched["value"] = value
    keep_rows.append(enriched)

print(f"[PY] After noise gate: keep={len(keep_rows)}, noise={len(noise_rows)}")

# Build index
idx = build_index(keep_rows)
print(f"[PY] Whitelist-gated index size: {len(idx)}")

# Process each kept row through historical/addsub/division/final-trust
hist_green = hist_medium = hist_outlier = 0
addsub_pass = addsub_warn = addsub_fail = 0
div_pass = div_passrange = div_warn = div_fail = 0
final_green = final_yellow = final_orange = final_red = 0
addsub_formula_rows = 0
div_formula_rows = 0

formula_check_rows = []

for r in keep_rows:
    canon = r["canonical"]
    year = r["year"]
    value = r["value"]
    fn = r["filename"]
    tkr = r["ticker"]

    h_c, h_lbl, _ = historical_check(canon, year, value, idx, fn, tkr)
    a_c, a_lbl = add_sub_check(canon, year, value, idx, fn, tkr)
    d_c, d_lbl = division_check(canon, year, value, idx, fn, tkr)
    score, band = final_trust(h_c, a_c, d_c)

    r["Historical Data Confidence"] = round(h_c, 4)
    r["Historical Data Check"] = h_lbl
    r["Add/Sub Check Confidence"] = round(a_c, 4)
    r["Add/Sub Check"] = a_lbl
    r["Division Check Confidence"] = round(d_c, 4)
    r["Division Check"] = d_lbl
    r["Final Trust Confidence"] = score
    r["Final Trust Band"] = band
    r["Review Flag"] = "OK" if band in ("GREEN", "YELLOW") else "REVIEW_REQUIRED"

    if "HISTORICAL_OK" in h_lbl: hist_green += 1
    elif "HISTORICAL_MEDIUM" in h_lbl: hist_medium += 1
    elif "HISTORICAL_OUTLIER" in h_lbl: hist_outlier += 1

    if "PASS-EXACT" in a_lbl or "PASS-SOFT" in a_lbl: addsub_pass += 1
    elif a_lbl.startswith("WARN"): addsub_warn += 1
    elif a_lbl.startswith("FAIL"): addsub_fail += 1
    if a_c != 0.72: addsub_formula_rows += 1

    if "PASS-EXACT" in d_lbl or "PASS-SOFT" in d_lbl: div_pass += 1
    elif "PASS-RANGE" in d_lbl: div_passrange += 1
    elif d_lbl.startswith("WARN"): div_warn += 1
    elif "FAIL-RANGE" in d_lbl: div_fail += 1
    if d_c != 0.72: div_formula_rows += 1

    if band == "GREEN": final_green += 1
    elif band == "YELLOW": final_yellow += 1
    elif band == "ORANGE": final_orange += 1
    else: final_red += 1

    # Save rows that had any formula activity for the Formula Check tab
    if (a_c != 0.72) or (d_c != 0.72):
        formula_check_rows.append(r)

# Write Financial CSV (full schema with new columns)
fin_fieldnames = [
    "Filename", "Ticker", "Name", "Report Date", "Category", "Year",
    "Data", "Canonical Data", "Unit", "Value",
    "Data Quality Gate",
    "Historical Data Confidence", "Historical Data Check",
    "Add/Sub Check Confidence", "Add/Sub Check",
    "Division Check Confidence", "Division Check",
    "Final Trust Confidence", "Final Trust Band", "Review Flag",
]
write_csv(OUT_FIN, keep_rows, fin_fieldnames)
print(f"[PY] Financial CSV -> {OUT_FIN}")

# Write Noise CSV
noise_fieldnames = [
    "Filename", "Ticker", "Category", "Year", "Data", "Canonical Data",
    "Value", "Data Quality Gate", "Data Quality Reason"
]
write_csv(OUT_NOISE, noise_rows, noise_fieldnames)
print(f"[PY] Noise CSV -> {OUT_NOISE}")

# Try parquet writes (optional - require pyarrow or fastparquet)
basic_parquet_ok = False
basic_parquet_err = ""
fin_parquet_ok = False
fin_parquet_err = ""
try:
    import pandas as pd
    df_basic = pd.DataFrame(basic_rows_raw)
    df_basic.to_parquet(OUT_BASIC.replace(".csv", ".parquet"), index=False)
    basic_parquet_ok = True
except Exception as e:
    basic_parquet_err = str(e)
try:
    import pandas as pd
    df_fin = pd.DataFrame(keep_rows)
    # Drop python-internal columns
    drop_cols = [c for c in df_fin.columns if c in ("filename","ticker","canonical","year","value")]
    df_fin = df_fin.drop(columns=drop_cols, errors="ignore")
    df_fin.to_parquet(OUT_FIN.replace(".csv", ".parquet"), index=False)
    fin_parquet_ok = True
except Exception as e:
    fin_parquet_err = str(e)

# JSON summary
summary = {
    "version": "VRN_FINANCIAL_TRUST_POLISH_V044",
    "generated_at": datetime.datetime.now().isoformat(),
    "source_basicinfo": SRC_BASIC,
    "source_financial": SRC_FIN,
    "basic_rows": len(basic_rows_raw),
    "financial_rows_in": len(fin_rows_raw),
    "financial_rows_keep": len(keep_rows),
    "noise_rows": len(noise_rows),
    "counts": {
        "hist_green": hist_green,
        "hist_medium": hist_medium,
        "hist_outlier": hist_outlier,
        "add_sub_formula_rows": addsub_formula_rows,
        "add_sub_pass_rows": addsub_pass,
        "add_sub_warn_rows": addsub_warn,
        "add_sub_fail_rows": addsub_fail,
        "division_formula_rows": div_formula_rows,
        "division_pass_rows": div_pass,
        "division_passrange_rows": div_passrange,
        "division_warn_rows": div_warn,
        "division_fail_rows": div_fail,
        "final_green": final_green,
        "final_yellow": final_yellow,
        "final_orange": final_orange,
        "final_red": final_red,
    },
    "basic_parquet_ok": basic_parquet_ok,
    "basic_parquet_error": basic_parquet_err,
    "financial_parquet_ok": fin_parquet_ok,
    "financial_parquet_error": fin_parquet_err,
    "outputs": {
        "basicinfo_csv": OUT_BASIC,
        "basicinfo_parquet": OUT_BASIC.replace(".csv", ".parquet"),
        "financial_csv": OUT_FIN,
        "financial_parquet": OUT_FIN.replace(".csv", ".parquet"),
        "noise_csv": OUT_NOISE,
        "json": OUT_JSON,
        "html": OUT_HTML,
    },
    "v044_fixes": [
        "Add/Sub tolerance bands: PASS-EXACT/PASS-SOFT/WARN/FAIL replace binary PASS/FAIL",
        "Division two-stage: Stage A magnitude check + Stage B tolerance",
        "Division ratios x100 to align with report % units (fixes v04.3 unit bug)",
        "Sign-aware division (negative ROE handled)",
        "Full 19-column BasicInfo prepended in Financial Matrix / Formula Checks / Noise tabs",
        "Formula Check tab now includes Historical Check Confidence + Historical Check columns",
        "Final trust uses weighted-average + boost stacking; bands GREEN/YELLOW/ORANGE/RED",
        "LL#34 PS7 fix: Test-Path -and Test-Path wrapped with () for parser",
    ],
}

with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
print(f"[PY] JSON summary -> {OUT_JSON}")


# ============================================================
# HTML rendering (VIA Visual Lock v1)
# ============================================================
def h(s):
    return html.escape("" if s is None else str(s))


def render_basicinfo_cells(rec):
    """Render the 19 BasicInfo cells in Tony's locked order."""
    return "".join(f"<td>{h(rec.get(c, ''))}</td>" for c in BASICINFO_COLS)


def render_matrix_row(r, by_t, by_f):
    bi = get_basicinfo(by_t, by_f, r.get("ticker", ""), r.get("filename", ""))
    band = r.get("Final Trust Band", "")
    band_class = f"band-{band.lower()}" if band else ""
    return (
        f"<tr class='{band_class}'>"
        f"<td>{h(r.get('Filename',''))}</td>"
        f"{render_basicinfo_cells(bi)}"
        f"<td>{h(r.get('Category',''))}</td>"
        f"<td>{h(r.get('Year',''))}</td>"
        f"<td>{h(r.get('Data',''))}</td>"
        f"<td>{h(r.get('Canonical Data',''))}</td>"
        f"<td>{h(r.get('Unit',''))}</td>"
        f"<td>{h(r.get('Value',''))}</td>"
        f"<td>{h(r.get('Data Quality Gate',''))}</td>"
        f"<td>{h(r.get('Historical Data Confidence',''))}</td>"
        f"<td>{h(r.get('Historical Data Check',''))}</td>"
        f"<td>{h(r.get('Add/Sub Check Confidence',''))}</td>"
        f"<td>{h(r.get('Add/Sub Check',''))}</td>"
        f"<td>{h(r.get('Division Check Confidence',''))}</td>"
        f"<td>{h(r.get('Division Check',''))}</td>"
        f"<td>{h(r.get('Final Trust Confidence',''))}</td>"
        f"<td><span class='band-tag band-{band.lower()}-tag'>{h(band)}</span></td>"
        f"<td>{h(r.get('Review Flag',''))}</td>"
        f"</tr>"
    )


def render_formula_row(r, by_t, by_f):
    bi = get_basicinfo(by_t, by_f, r.get("ticker", ""), r.get("filename", ""))
    band = r.get("Final Trust Band", "")
    return (
        f"<tr class='band-{band.lower()}'>"
        f"<td>{h(r.get('Filename',''))}</td>"
        f"{render_basicinfo_cells(bi)}"
        f"<td>{h(r.get('Category',''))}</td>"
        f"<td>{h(r.get('Year',''))}</td>"
        f"<td>{h(r.get('Data',''))}</td>"
        f"<td>{h(r.get('Canonical Data',''))}</td>"
        f"<td>{h(r.get('Value',''))}</td>"
        f"<td>{h(r.get('Historical Data Confidence',''))}</td>"
        f"<td>{h(r.get('Historical Data Check',''))}</td>"
        f"<td>{h(r.get('Add/Sub Check Confidence',''))}</td>"
        f"<td>{h(r.get('Add/Sub Check',''))}</td>"
        f"<td>{h(r.get('Division Check Confidence',''))}</td>"
        f"<td>{h(r.get('Division Check',''))}</td>"
        f"<td>{h(r.get('Final Trust Confidence',''))}</td>"
        f"<td><span class='band-tag band-{band.lower()}-tag'>{h(band)}</span></td>"
        f"</tr>"
    )


def render_noise_row(r, by_t, by_f):
    bi = get_basicinfo(by_t, by_f, r.get("Ticker", ""), r.get("Filename", ""))
    return (
        f"<tr>"
        f"<td>{h(r.get('Filename',''))}</td>"
        f"{render_basicinfo_cells(bi)}"
        f"<td>{h(r.get('Category',''))}</td>"
        f"<td>{h(r.get('Year',''))}</td>"
        f"<td>{h(r.get('Data',''))}</td>"
        f"<td>{h(r.get('Canonical Data',''))}</td>"
        f"<td>{h(r.get('Value',''))}</td>"
        f"<td>{h(r.get('Data Quality Gate',''))}</td>"
        f"<td>{h(r.get('Data Quality Reason',''))}</td>"
        f"</tr>"
    )


# Build column headers for the BasicInfo 19 prepend block
basicinfo_th = "".join(f"<th class='bi-col'>{h(c)}</th>" for c in BASICINFO_COLS)

matrix_rows_html = "\n".join(render_matrix_row(r, by_t, by_f) for r in keep_rows)
formula_rows_html = "\n".join(render_formula_row(r, by_t, by_f) for r in formula_check_rows)
noise_rows_html = "\n".join(render_noise_row(r, by_t, by_f) for r in noise_rows)

# Overview cards
addsub_pass_pct = (addsub_pass / addsub_formula_rows * 100) if addsub_formula_rows else 0
div_pass_pct = ((div_pass + div_passrange) / div_formula_rows * 100) if div_formula_rows else 0

html_doc = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<title>VRN Financial Trust Polish v04.4</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@500;600;700&family=DM+Sans:wght@400;500;600&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root {{
  --bg: #f5f4f0;
  --ink: #1a1a1a;
  --ink-2: #4a4a4a;
  --ink-3: #8a8a8a;
  --line: #d9d6cf;
  --blue: #4c78a8;
  --teal: #439a9a;
  --red: #c8553d;
  --orange: #e8a04b;
  --yellow: #d4b94a;
  --green: #4a8a5e;
  --card: #ffffff;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: 'DM Sans', -apple-system, sans-serif;
  font-size: 11px;
  line-height: 1.4;
  color: var(--ink);
  background: var(--bg);
  padding: 20px;
}}
h1, h2 {{
  font-family: 'Syne', sans-serif;
  font-weight: 600;
}}
h1 {{
  font-size: 22px;
  letter-spacing: -0.01em;
  margin-bottom: 4px;
}}
.subtitle {{
  font-size: 11px;
  color: var(--ink-2);
  margin-bottom: 14px;
}}
.rainbow-border {{
  height: 3px;
  background: linear-gradient(90deg, var(--red), var(--orange), var(--yellow), var(--green), var(--teal), var(--blue));
  margin-bottom: 18px;
}}
.tabs {{
  display: flex;
  gap: 4px;
  margin-bottom: 18px;
  border-bottom: 1px solid var(--line);
}}
.tab {{
  padding: 8px 16px;
  cursor: pointer;
  font-family: 'DM Mono', monospace;
  font-size: 11px;
  color: var(--ink-2);
  border: 1px solid transparent;
  border-bottom: none;
  background: transparent;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}}
.tab.active {{
  background: var(--card);
  border-color: var(--line);
  color: var(--blue);
  border-bottom: 1px solid var(--card);
  margin-bottom: -1px;
}}
.panel {{ display: none; }}
.panel.active {{ display: block; }}
.cd {{
  background: var(--card);
  border: 1px solid var(--line);
  margin-bottom: 14px;
}}
.cd-h {{
  padding: 10px 14px;
  border-bottom: 1px solid var(--line);
  font-family: 'Syne', sans-serif;
  font-size: 13px;
  font-weight: 600;
}}
.cd-b {{ padding: 14px; }}
.sg {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 8px;
}}
.sc {{
  background: var(--card);
  border: 1px solid var(--line);
  padding: 10px 12px;
}}
.sc-v {{
  font-family: 'DM Mono', monospace;
  font-size: 20px;
  font-weight: 500;
  color: var(--ink);
}}
.sc-l {{
  font-size: 10px;
  color: var(--ink-3);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-top: 2px;
}}
table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 10px;
  font-family: 'DM Mono', monospace;
  background: var(--card);
}}
th {{
  background: #ede9df;
  border: 1px solid var(--line);
  padding: 6px 8px;
  text-align: left;
  font-weight: 600;
  color: var(--ink);
  font-family: 'DM Sans', sans-serif;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  white-space: nowrap;
}}
th.bi-col {{ background: #e3dfd4; color: var(--blue); }}
td {{
  border: 1px solid var(--line);
  padding: 4px 8px;
  vertical-align: top;
}}
tr.band-green > td {{ background: rgba(74, 138, 94, 0.06); }}
tr.band-yellow > td {{ background: rgba(212, 185, 74, 0.06); }}
tr.band-orange > td {{ background: rgba(232, 160, 75, 0.08); }}
tr.band-red > td {{ background: rgba(200, 85, 61, 0.08); }}
.band-tag {{
  font-family: 'DM Mono', monospace;
  font-size: 9px;
  padding: 2px 6px;
  font-weight: 600;
  letter-spacing: 0.04em;
}}
.band-green-tag {{ background: var(--green); color: #fff; }}
.band-yellow-tag {{ background: var(--yellow); color: #fff; }}
.band-orange-tag {{ background: var(--orange); color: #fff; }}
.band-red-tag {{ background: var(--red); color: #fff; }}
.tm {{
  background: #1a1a1a;
  color: #c8e0c8;
  padding: 14px;
  font-family: 'DM Mono', monospace;
  font-size: 10px;
  line-height: 1.5;
  white-space: pre-wrap;
  position: relative;
}}
.tm::before {{
  content: '● ● ●';
  color: #ff5f56;
  display: block;
  margin-bottom: 8px;
  letter-spacing: 4px;
  font-size: 10px;
}}
.tbl-scroll {{
  overflow-x: auto;
  border: 1px solid var(--line);
}}
.fixes-list {{
  background: var(--card);
  border: 1px solid var(--line);
  padding: 12px 16px;
}}
.fixes-list li {{
  padding: 4px 0;
  list-style: none;
  border-bottom: 1px dotted var(--line);
}}
.fixes-list li:last-child {{ border-bottom: none; }}
.fixes-list li::before {{
  content: '→';
  color: var(--teal);
  margin-right: 8px;
  font-weight: 600;
}}
.json-block {{
  background: #1a1a1a;
  color: #d4d4d4;
  padding: 14px;
  font-family: 'DM Mono', monospace;
  font-size: 10px;
  line-height: 1.5;
  white-space: pre-wrap;
  overflow-x: auto;
}}
</style>
</head>
<body>
<h1>VRN Financial Trust Polish v04.4</h1>
<div class="subtitle">19-col BasicInfo prepend · Add/Sub tolerance bands · Two-stage Division · LL#34 PS7 fix · Run: {h(RUN_NAME)}</div>
<div class="rainbow-border"></div>

<div class="tabs">
  <button class="tab active" data-panel="p1">01 Overview</button>
  <button class="tab" data-panel="p2">02 Financial Matrix</button>
  <button class="tab" data-panel="p3">03 Formula Checks</button>
  <button class="tab" data-panel="p4">04 Noise Quarantine</button>
  <button class="tab" data-panel="p5">05 JSON</button>
</div>

<div id="p1" class="panel active">
  <div class="cd">
    <div class="cd-h">Counts</div>
    <div class="cd-b">
      <div class="sg">
        <div class="sc"><div class="sc-v">{len(keep_rows)}</div><div class="sc-l">Financial Keep</div></div>
        <div class="sc"><div class="sc-v">{len(noise_rows)}</div><div class="sc-l">Noise</div></div>
        <div class="sc"><div class="sc-v">{hist_green}</div><div class="sc-l">Hist OK</div></div>
        <div class="sc"><div class="sc-v">{hist_medium}</div><div class="sc-l">Hist MEDIUM</div></div>
        <div class="sc"><div class="sc-v">{hist_outlier}</div><div class="sc-l">Hist OUTLIER</div></div>
      </div>
    </div>
  </div>
  <div class="cd">
    <div class="cd-h">Add/Sub Check Tolerance Bands</div>
    <div class="cd-b">
      <div class="sg">
        <div class="sc"><div class="sc-v">{addsub_formula_rows}</div><div class="sc-l">Add/Sub Rows</div></div>
        <div class="sc"><div class="sc-v">{addsub_pass}</div><div class="sc-l">PASS (Exact+Soft)</div></div>
        <div class="sc"><div class="sc-v">{addsub_warn}</div><div class="sc-l">WARN</div></div>
        <div class="sc"><div class="sc-v">{addsub_fail}</div><div class="sc-l">FAIL</div></div>
        <div class="sc"><div class="sc-v">{addsub_pass_pct:.0f}%</div><div class="sc-l">PASS Rate</div></div>
      </div>
    </div>
  </div>
  <div class="cd">
    <div class="cd-h">Division Check Two-Stage Judgment</div>
    <div class="cd-b">
      <div class="sg">
        <div class="sc"><div class="sc-v">{div_formula_rows}</div><div class="sc-l">Division Rows</div></div>
        <div class="sc"><div class="sc-v">{div_pass}</div><div class="sc-l">PASS-EXACT/SOFT</div></div>
        <div class="sc"><div class="sc-v">{div_passrange}</div><div class="sc-l">PASS-RANGE</div></div>
        <div class="sc"><div class="sc-v">{div_warn}</div><div class="sc-l">WARN</div></div>
        <div class="sc"><div class="sc-v">{div_fail}</div><div class="sc-l">FAIL-RANGE</div></div>
        <div class="sc"><div class="sc-v">{div_pass_pct:.0f}%</div><div class="sc-l">PASS+RANGE Rate</div></div>
      </div>
    </div>
  </div>
  <div class="cd">
    <div class="cd-h">Final Trust Band Distribution</div>
    <div class="cd-b">
      <div class="sg">
        <div class="sc"><div class="sc-v" style="color:var(--green)">{final_green}</div><div class="sc-l">GREEN</div></div>
        <div class="sc"><div class="sc-v" style="color:var(--yellow)">{final_yellow}</div><div class="sc-l">YELLOW</div></div>
        <div class="sc"><div class="sc-v" style="color:var(--orange)">{final_orange}</div><div class="sc-l">ORANGE</div></div>
        <div class="sc"><div class="sc-v" style="color:var(--red)">{final_red}</div><div class="sc-l">RED</div></div>
      </div>
    </div>
  </div>
  <div class="cd">
    <div class="cd-h">Outputs</div>
    <div class="cd-b">
      <div class="sg">
        <div class="sc"><div class="sc-v">{'OK' if basic_parquet_ok else 'ERR'}</div><div class="sc-l">Basic Parquet</div></div>
        <div class="sc"><div class="sc-v">{'OK' if fin_parquet_ok else 'ERR'}</div><div class="sc-l">Fin Parquet</div></div>
      </div>
    </div>
  </div>
  <div class="cd">
    <div class="cd-h">v04.4 Fixes</div>
    <div class="cd-b">
      <ul class="fixes-list">
"""
for fix in summary["v044_fixes"]:
    html_doc += f"        <li>{h(fix)}</li>\n"
html_doc += f"""      </ul>
    </div>
  </div>
</div>

<div id="p2" class="panel">
  <div class="cd">
    <div class="cd-h">02 Financial Trust Matrix · 19-col BasicInfo prepended</div>
    <div class="cd-b">
      <div class="tbl-scroll">
        <table>
          <thead>
            <tr>
              <th>Filename</th>
              {basicinfo_th}
              <th>Category</th><th>Year</th><th>Data</th><th>Canonical Data</th>
              <th>Unit</th><th>Value</th><th>DQ Gate</th>
              <th>Hist Conf</th><th>Hist Check</th>
              <th>Add/Sub Conf</th><th>Add/Sub Check</th>
              <th>Division Conf</th><th>Division Check</th>
              <th>Trust Conf</th><th>Band</th><th>Review</th>
            </tr>
          </thead>
          <tbody>
{matrix_rows_html}
          </tbody>
        </table>
      </div>
    </div>
  </div>
</div>

<div id="p3" class="panel">
  <div class="cd">
    <div class="cd-h">03 Formula Check Rows · Historical + Add/Sub + Division</div>
    <div class="cd-b">
      <div class="tbl-scroll">
        <table>
          <thead>
            <tr>
              <th>Filename</th>
              {basicinfo_th}
              <th>Category</th><th>Year</th><th>Data</th><th>Canonical Data</th>
              <th>Value</th>
              <th>Hist Conf</th><th>Hist Check</th>
              <th>Add/Sub Conf</th><th>Add/Sub Check</th>
              <th>Division Conf</th><th>Division Check</th>
              <th>Trust Conf</th><th>Band</th>
            </tr>
          </thead>
          <tbody>
{formula_rows_html}
          </tbody>
        </table>
      </div>
    </div>
  </div>
</div>

<div id="p4" class="panel">
  <div class="cd">
    <div class="cd-h">04 Noise Quarantine</div>
    <div class="cd-b">
      <div class="tbl-scroll">
        <table>
          <thead>
            <tr>
              <th>Filename</th>
              {basicinfo_th}
              <th>Category</th><th>Year</th><th>Data</th><th>Canonical Data</th>
              <th>Value</th><th>DQ Gate</th><th>Reason</th>
            </tr>
          </thead>
          <tbody>
{noise_rows_html}
          </tbody>
        </table>
      </div>
    </div>
  </div>
</div>

<div id="p5" class="panel">
  <div class="cd">
    <div class="cd-h">05 JSON</div>
    <div class="cd-b">
      <pre class="json-block">{h(json.dumps(summary, ensure_ascii=False, indent=2))}</pre>
    </div>
  </div>
</div>

<script>
document.querySelectorAll('.tab').forEach(t => {{
  t.addEventListener('click', () => {{
    document.querySelectorAll('.tab').forEach(x => x.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(x => x.classList.remove('active'));
    t.classList.add('active');
    document.getElementById(t.dataset.panel).classList.add('active');
  }});
}});
</script>
</body>
</html>
"""

with open(OUT_HTML, "w", encoding="utf-8") as f:
    f.write(html_doc)
print(f"[PY] HTML report -> {OUT_HTML}")

print(f"[PY] DONE")
print(f"[PY] keep={len(keep_rows)} noise={len(noise_rows)} green={final_green} yellow={final_yellow} orange={final_orange} red={final_red}")
print(f"[PY] addsub: rows={addsub_formula_rows} pass={addsub_pass} warn={addsub_warn} fail={addsub_fail}")
print(f"[PY] division: rows={div_formula_rows} pass={div_pass} pass_range={div_passrange} warn={div_warn} fail={div_fail}")
'@

[IO.File]::WriteAllText($pyScript, $py, [System.Text.UTF8Encoding]::new($false))
Write-Log "Embedded Python written: $pyScript ($([System.IO.FileInfo]::new($pyScript).Length) bytes)"

#endregion

#region -----------------------------------------------------------------------
# Verify Python interpreter
#region -----------------------------------------------------------------------

Show-Prog "Verifying Python interpreter" 15

if (-not (Test-Path -LiteralPath $Python)) {
  Write-Log "Python not found at $Python; trying 'py -3.12' fallback" "WARN"
  $script:PythonExe = "py"
  $script:PythonArgs = @("-3.12")
} else {
  $script:PythonExe = $Python
  $script:PythonArgs = @()
}

#endregion

#region -----------------------------------------------------------------------
# Run pipeline
#region -----------------------------------------------------------------------

Show-Prog "Running v04.4 pipeline" 30

$pyArgs = @($pyScript, $srcBasicInfo, $srcFinancial, $outBasicCsv, $outFinCsv, $outNoiseCsv, $outJson, $outHtml)
$allArgs = $script:PythonArgs + $pyArgs

Write-Log "Invoking: $($script:PythonExe) $($allArgs -join ' ')"

$pyOutput = & $script:PythonExe @allArgs 2>&1
$pyExitCode = $LASTEXITCODE

foreach ($line in $pyOutput) {
  Write-Host "  $line"
  Add-Content -LiteralPath $script:LogPath -Value "  $line" -Encoding UTF8
}

if ($pyExitCode -ne 0) {
  Write-Log "Python pipeline FAILED with exit code $pyExitCode" "ERROR"
  throw "Pipeline failed"
}

Show-Prog "Pipeline complete" 90

#endregion

#region -----------------------------------------------------------------------
# Verify outputs + optionally open HTML
#region -----------------------------------------------------------------------

$expectedOutputs = @(
  @{Path = $outBasicCsv; Label = "BasicInfo CSV"},
  @{Path = $outFinCsv;   Label = "Financial CSV"},
  @{Path = $outNoiseCsv; Label = "Noise CSV"},
  @{Path = $outJson;     Label = "JSON"},
  @{Path = $outHtml;     Label = "HTML"}
)

Write-Host ""
Write-Host "Output file verification:" -ForegroundColor Cyan
foreach ($o in $expectedOutputs) {
  if (Test-Path -LiteralPath $o.Path) {
    $size = [System.IO.FileInfo]::new($o.Path).Length
    Write-Host ("  [OK] {0,-18} {1,10} bytes  {2}" -f $o.Label, $size, $o.Path) -ForegroundColor Green
  } else {
    Write-Host ("  [MISSING] {0}: {1}" -f $o.Label, $o.Path) -ForegroundColor Red
  }
}

Show-Prog "v04.4 complete" 100

if ($Open -and (Test-Path -LiteralPath $outHtml)) {
  Start-Process $outHtml
}

Write-Host ""
Write-Host "Run directory: $($script:RunDir)" -ForegroundColor Yellow
Write-Host "HTML report:   $outHtml" -ForegroundColor Yellow

#endregion

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
