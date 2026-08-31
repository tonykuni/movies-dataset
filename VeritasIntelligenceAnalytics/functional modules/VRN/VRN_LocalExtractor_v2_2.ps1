#requires -Version 7.0
[CmdletBinding(PositionalBinding=$false)]
param(
    [string]$VrnDir         = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN",
    [string]$InputDir       = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\input",
    [string]$SupportiveDir  = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module",
    [string]$DbDir          = "C:\VeritasIntelligenceAnalytics\VeritasReportNova\database",
    [string]$PythonExe      = "C:\Users\tonyk\envs\via_core_312\Scripts\python.exe",
    [int]$MinScore          = 80,
    [switch]$NoOpen
)
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

# ╔══════════════════════════════════════════════════════════════════════════════════╗
# ║  VRN_LocalExtractor v2.2 · BROKER LONGEST-MATCH FIX                                ║
# ║                                                                                    ║
# ║  v2.1 → v2.2 changes:                                                              ║
# ║    × v2.1 first-match-by-length-desc → wrong winner when length tied               ║
# ║    ✓ v2.2 collect ALL matches, take longest (most specific)                        ║
# ║    ✓ v2.2 add `broker_match_alias` field for debugging                             ║
# ║    ✓ v2.2 ensure CTBC alias incl 中國信託證券 (longer than 中信)                    ║
# ║                                                                                    ║
# ║  Output: vrn_financial_data_local_v2_2.duckdb (additive — v2/v2.1 untouched)       ║
# ╚══════════════════════════════════════════════════════════════════════════════════╝

$ErrorActionPreference = "Continue"
$script:t0 = [datetime]::Now

$RunId        = "VRN_LOCAL_V2_2_" + (Get-Date -Format "yyyyMMdd_HHmmss")
$RunDir       = Join-Path $VrnDir "_local_runs\$RunId"
$ExtractorPy  = Join-Path $RunDir "VRN_LocalExtractor_v2_2.py"
$ResultJson   = Join-Path $RunDir "extraction_results.json"
$LocalDuckdb  = Join-Path $DbDir  "vrn_financial_data_local_v2_2.duckdb"
$HtmlReport   = Join-Path $RunDir "VRN_LocalExtract_Report_v2_2.html"
$LogFile      = Join-Path $RunDir "extract.log"
$SsotPath     = Join-Path $SupportiveDir "VIA_SSOT_Unified.py"

foreach ($d in @($RunDir, $DbDir)) {
    if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
}

Write-Host ""
Write-Host "════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  VRN_LocalExtractor v2.2 · Broker Longest-Match Fix" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Input    : $InputDir"
Write-Host "  Output   : $LocalDuckdb"
Write-Host ""

Write-Host "──── Phase 0 · Deps ────" -ForegroundColor Yellow
$needs = @()
foreach ($pkg in @(@("pdfplumber","pdfplumber"), @("docx","python-docx"),
                    @("rapidfuzz","rapidfuzz"), @("duckdb","duckdb"))) {
    & $PythonExe -c "import $($pkg[0])" 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { $needs += $pkg[1] }
}
if ($needs.Count -gt 0) {
    & $PythonExe -m pip install --quiet @needs
}
Write-Host "  [OK] Deps ready" -ForegroundColor Green

Write-Host ""
Write-Host "──── Phase 1 · Generating v2.2 extractor ────" -ForegroundColor Yellow

$Code = @'
# -*- coding: utf-8 -*-
"""VRN Local Extractor v2.2 — broker longest-match strategy."""
from __future__ import annotations
import sys, os, re, json, glob, traceback, time
from pathlib import Path
from datetime import datetime
from collections import Counter
import importlib.util

INPUT_DIR    = r"__INPUT_DIR__"
RUN_DIR      = r"__RUN_DIR__"
SSOT_PATH    = r"__SSOT_PATH__"
RESULT_JSON  = r"__RESULT_JSON__"
LOCAL_DUCKDB = r"__LOCAL_DUCKDB__"
LOG_FILE     = r"__LOG_FILE__"
MIN_SCORE    = __MIN_SCORE__

import pdfplumber
import duckdb
from rapidfuzz import process, fuzz

LOCKED_TW_TICKER = re.compile(r"(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})")

# ═══════════════════════════════════════════════════════════════════
# (1) SSOT canonical corpus
# ═══════════════════════════════════════════════════════════════════
SSOT = None
SSOT_LOADED = False
try:
    if Path(SSOT_PATH).exists():
        spec = importlib.util.spec_from_file_location("via_ssot", SSOT_PATH)
        SSOT = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(SSOT)
        SSOT_LOADED = True
        print(f"[SSOT] Loaded: {SSOT_PATH}")
except Exception as e:
    print(f"[SSOT] Load failed ({e})")

ALIAS2CANON = {}
CANON_SET = set()
if SSOT_LOADED and hasattr(SSOT, 'FinancialStatementData'):
    fsd = SSOT.FinancialStatementData()
    for mname in ['get_income_statement_data','get_balance_sheet_data',
                  'get_cash_flow_data','get_financial_ratios_data','get_per_share_data']:
        if not hasattr(fsd, mname): continue
        for entry in getattr(fsd, mname)():
            canon = (entry.get('tw_stock','') or '').strip()
            if not canon or canon == '--': continue
            CANON_SET.add(canon)
            ALIAS2CANON[canon.lower()] = canon
            for f in ('zh','en','twse','tpex'):
                v = entry.get(f, '')
                if isinstance(v, str) and v.strip() and v != '--':
                    ALIAS2CANON[v.strip().lower()] = canon
            syns = entry.get('synonyms', '')
            if isinstance(syns, str):
                for s in syns.split(','):
                    s = s.strip()
                    if s: ALIAS2CANON[s.lower()] = canon

EXTRA_CORPUS = {
    "target_price": ["目標價","Target Price","TP","12-Month Target","目標股價"],
    "rating":       ["買進","賣出","持有","增持","減持","Outperform","Underperform","Buy","Sell","Hold","Overweight","Underweight","Strong Buy","Neutral","Reduce","Accumulate"],
    "market_cap":   ["市值","Market Cap","Mkt Cap","總市值"],
}
for canon, aliases in EXTRA_CORPUS.items():
    CANON_SET.add(canon)
    ALIAS2CANON[canon.lower()] = canon
    for a in aliases:
        ALIAS2CANON[a.strip().lower()] = canon

ALL_ALIASES = sorted(ALIAS2CANON.keys(), key=len, reverse=True)
print(f"[SSOT] Canonical: {len(CANON_SET)} canonicals, {len(ALIAS2CANON)} aliases")

# ═══════════════════════════════════════════════════════════════════
# (2) BROKER dict — full, with longest-match strategy
# ═══════════════════════════════════════════════════════════════════
BROKER_DICT_FULL = [
    {"code": ["MS","Morgan Stanley","摩根士丹利","摩根史坦利"],            "en": "Morgan Stanley"},
    {"code": ["GS","Goldman Sachs","高盛"],                                 "en": "Goldman Sachs"},
    {"code": ["JPM","JP","JPMorgan","JP Morgan","JPMorgan Chase","摩根大通","JP摩根"], "en": "JPMorgan Chase"},
    {"code": ["CITI","Citi","Citigroup","花旗銀行","花旗"],                  "en": "Citigroup"},
    {"code": ["BAML","Bank of America","美林證券","美林"],                   "en": "BAML"},
    {"code": ["CS","Credit Suisse","瑞士信貸","瑞信"],                       "en": "Credit Suisse"},
    {"code": ["UBS","UBS Group","瑞銀集團","瑞銀"],                          "en": "UBS"},
    {"code": ["DB","Deutsche Bank","德意志銀行","德銀"],                     "en": "Deutsche Bank"},
    {"code": ["HSBC","HSBC Holdings","滙豐控股","匯豐"],                     "en": "HSBC"},
    {"code": ["RBC","Royal Bank of Canada","加拿大皇家銀行"],                "en": "RBC"},
    {"code": ["BARCLAYS","Barclays","巴克萊銀行"],                           "en": "Barclays"},
    {"code": ["NMR","Nomura","Nomura Securities","野村證券","野村"],          "en": "Nomura"},
    {"code": ["MIZUHO","Mizuho","瑞穗"],                                     "en": "Mizuho"},
    {"code": ["MUFG","Mitsubishi UFJ","三菱UFJ"],                            "en": "MUFG"},
    {"code": ["凱基","KGI Securities","KGI"],                                "en": "KGI"},
    {"code": ["國泰","Cathay Securities"],                                    "en": "Cathay"},
    {"code": ["群益","Capital Securities"],                                   "en": "Capital"},
    {"code": ["元大","Yuanta Securities"],                                    "en": "Yuanta"},
    {"code": ["永豐","SinoPac Securities"],                                   "en": "SinoPac"},
    {"code": ["第一","First Securities","第一金"],                            "en": "First"},
    {"code": ["台新","Taishin Securities"],                                   "en": "Taishin"},
    {"code": ["富邦","Fubon Securities"],                                     "en": "Fubon"},
    {"code": ["新光","Shin Kong Securities"],                                 "en": "Shin Kong"},
    {"code": ["MEGA","兆豐證券","兆豐金控","兆豐"],                          "en": "Mega Securities"},
    {"code": ["CTBC","中國信託證券","中信證券","中信銀","中信投顧","中信"],   "en": "CTBC Securities"},
    {"code": ["UNI","統一投顧","統一證券","統一"],                            "en": "Uni-President Capital"},
    {"code": ["ENTIE","華南永昌","華南投顧","華南"],                          "en": "Entie"},
    {"code": ["DAIWA","大和證券","Daiwa","大和"],                             "en": "Daiwa"},
    {"code": ["MBK","Maybank","Maybank Kim Eng","馬銀","美邦"],               "en": "Maybank Kim Eng"},
    {"code": ["CTY","康和證券","康和"],                                       "en": "Concord"},
    {"code": ["CLST","CLSA","里昂證券","里昂"],                               "en": "CLSA"},
    {"code": ["GF","廣發證券","廣發"],                                        "en": "GF Securities"},
    {"code": ["BNP","BNP Paribas","巴黎銀行"],                                "en": "BNP Paribas"},
]

BROKER_LOOKUP = {}
BROKER_DISPLAY = {}
for entry in BROKER_DICT_FULL:
    canon = entry['code'][0]
    BROKER_DISPLAY[canon] = entry['en']
    for c in entry['code']:
        if c.strip():
            BROKER_LOOKUP[c.strip().lower()] = canon

# Categorize: short ASCII codes use word-boundary, others use substring
SHORT_RE = {}      # alias_lower → compiled regex (word-boundary)
LONG_LIST = []     # list of (alias_lower, canon, length)  — will be searched all
for alias, canon in BROKER_LOOKUP.items():
    if len(alias) <= 5 and re.fullmatch(r'[a-z]+', alias):
        SHORT_RE[alias] = re.compile(r'(?<![a-z])' + re.escape(alias) + r'(?![a-z])', re.I)
    else:
        LONG_LIST.append((alias, canon, len(alias)))

print(f"[Broker] {len(BROKER_DISPLAY)} canonicals, {len(BROKER_LOOKUP)} aliases "
      f"(long={len(LONG_LIST)}, short={len(SHORT_RE)})")

def find_broker_in_text(text):
    """v2.2 LONGEST-MATCH: collect all matches, take longest (most specific).
       Returns (canon, alias_used). Empty if no match."""
    if not text: return ("", "")
    tl = text.lower()
    matches = []  # (length, canon, alias)

    # Long aliases: collect every match
    for alias, canon, length in LONG_LIST:
        if len(alias) >= 2 and alias in tl:
            matches.append((length, canon, alias))

    # Short ASCII codes: word-boundary
    for alias, regex in SHORT_RE.items():
        if regex.search(text):
            matches.append((len(alias), BROKER_LOOKUP[alias], alias))

    if not matches:
        return ("", "")
    matches.sort(key=lambda x: (-x[0], x[2]))  # longest first, then alphabetical for stable
    return (matches[0][1], matches[0][2])

# fin_type
INCOME_KW    = {"revenue","cost_of_revenue","gross_profit","operating_expenses","rd_expenses",
                "operating_income","non_operating_income","pretax_income","tax_expense","net_income",
                "basic_eps","diluted_eps","eps"}
BALANCE_KW   = {"cash","accounts_receivable","inventory","current_assets","ppe","total_assets",
                "accounts_payable","short_term_debt","current_liabilities","long_term_debt",
                "total_liabilities","share_capital","retained_earnings","shareholders_equity"}
CASHFLOW_KW  = {"operating_cashflow","investing_cashflow","financing_cashflow",
                "depreciation","amortization","capex","free_cashflow","dividends_paid"}
RATIO_KW     = {"roe","roa","gross_margin","operating_margin","net_margin","current_ratio",
                "quick_ratio","debt_ratio","debt_to_equity","pe_ratio","pb_ratio","ps_ratio",
                "book_value_per_share","dividend_per_share","cashflow_per_share",
                "sales_per_share","shares_outstanding","weighted_avg_shares",
                "diluted_shares","dividend_yield","payout_ratio"}
META_KW      = {"target_price","rating","market_cap"}

def reverse_fin_type(canonical):
    if canonical in INCOME_KW:    return "income_statement"
    if canonical in BALANCE_KW:   return "balance_sheet"
    if canonical in CASHFLOW_KW:  return "cash_flow"
    if canonical in RATIO_KW:     return "ratio"
    if canonical in META_KW:      return "metadata"
    return "unknown"

# ═══════════════════════════════════════════════════════════════════
# (3) Filename tokenizer (R1-R4) — unchanged from v2.1
# ═══════════════════════════════════════════════════════════════════
PUNCT_SPLIT = re.compile(
    r'[\s,\-_+\.\(\)\[\]【】「」（）{}~%、,。\u3000│｜·•~`!?@#$&*=:;\'"<>/\\]+'
)
TYPE_BOUNDARY = re.compile(
    r'(?<=[\u4e00-\u9fff])(?=[A-Za-z0-9])|(?<=[A-Za-z0-9])(?=[\u4e00-\u9fff])|(?<=[A-Za-z])(?=\d)|(?<=\d)(?=[A-Za-z])'
)

def tokenize_filename(fname):
    base = os.path.splitext(os.path.basename(fname))[0]
    parts = PUNCT_SPLIT.split(base)
    tokens = []
    for p in parts:
        if not p: continue
        sub = TYPE_BOUNDARY.split(p)
        tokens.extend([s.strip() for s in sub if s.strip()])
    return tokens

def classify_token(tok):
    if not tok: return None
    if tok.isdigit():
        n = len(tok)
        if n == 4 and tok[0] != '0':
            year = int(tok)
            if not (2021 <= year <= 2030):
                return ('ticker', tok)
            return ('year', tok)
        if n == 8: return ('date_full', tok)
        if n == 7 and tok[0] == '1': return ('roc_date', tok)
        if n == 6: return ('date_short', tok)
        return ('number', tok)
    has_zh = bool(re.search(r'[\u4e00-\u9fff]', tok))
    has_en = bool(re.search(r'[A-Za-z]', tok))
    if has_zh and not has_en: return ('zh', tok)
    if has_en and not has_zh: return ('en', tok)
    return ('mixed', tok)

def parse_date_token(t, kind):
    try:
        if kind == 'date_full' and len(t) == 8:
            return f"{t[0:4]}-{t[4:6]}-{t[6:8]}"
        if kind == 'date_short' and len(t) == 6:
            yy = int(t[0:2])
            century = "20" if yy < 50 else "19"
            return f"{century}{t[0:2]}-{t[2:4]}-{t[4:6]}"
        if kind == 'roc_date' and len(t) == 7:
            roc = int(t[0:3])
            return f"{1911+roc}-{t[3:5]}-{t[5:7]}"
    except Exception: pass
    return ""

def parse_filename_meta(fname):
    base = os.path.splitext(os.path.basename(fname))[0]
    tokens = tokenize_filename(fname)
    classified = [classify_token(t) for t in tokens]
    classified = [c for c in classified if c]

    broker_canon, broker_alias = find_broker_in_text(base)

    out = {"filename": fname,
           "broker": broker_canon,
           "broker_match_alias": broker_alias,
           "ticker": "", "name_candidates": [], "report_date": "",
           "_tokens": classified}

    for kind, val in classified:
        if kind == 'ticker' and not out['ticker']:
            out['ticker'] = val
        elif kind == 'date_full' and not out['report_date']:
            out['report_date'] = parse_date_token(val, kind)
        elif kind == 'roc_date' and not out['report_date']:
            out['report_date'] = parse_date_token(val, kind)
        elif kind == 'date_short' and not out['report_date']:
            out['report_date'] = parse_date_token(val, kind)
        elif kind == 'zh' and len(val) <= 12:
            v_lower = val.lower()
            is_broker = False
            for alias, _, _ in LONG_LIST:
                if alias in v_lower or v_lower in alias:
                    is_broker = True; break
            if not is_broker:
                out['name_candidates'].append(val)
    return out

# Page 1 cross-validate
def cross_validate_page1(fname_meta, page1_text):
    if not page1_text: return fname_meta
    final = dict(fname_meta)

    p1_tickers = set()
    for m in re.finditer(r'(?<!\d)([1-9]\d{3})(?!\d)', page1_text):
        cand = m.group(1)
        if LOCKED_TW_TICKER.fullmatch(cand) and not (2021 <= int(cand) <= 2030):
            p1_tickers.add(cand)
    if fname_meta['ticker'] and fname_meta['ticker'] in p1_tickers:
        final['ticker_confidence'] = 'high'
    elif p1_tickers:
        if not fname_meta['ticker']:
            final['ticker'] = sorted(p1_tickers)[0]
            final['ticker_confidence'] = 'medium'
        else:
            final['ticker_confidence'] = 'low'
    else:
        final['ticker_confidence'] = 'unverified' if fname_meta['ticker'] else 'missing'

    p1_broker, p1_alias = find_broker_in_text(page1_text)
    if p1_broker:
        if fname_meta['broker'] and p1_broker != fname_meta['broker']:
            final['broker'] = p1_broker
            final['broker_match_alias'] = p1_alias
            final['broker_confidence'] = 'page1_override'
        else:
            final['broker'] = p1_broker
            final['broker_match_alias'] = p1_alias if p1_alias else fname_meta.get('broker_match_alias','')
            final['broker_confidence'] = 'high'
    elif fname_meta['broker']:
        final['broker_confidence'] = 'filename_only'
    else:
        final['broker_confidence'] = 'missing'

    final['name'] = ""
    for nc in fname_meta['name_candidates']:
        if len(nc) >= 2 and nc in page1_text:
            final['name'] = nc; break
    if not final['name'] and fname_meta['name_candidates']:
        final['name'] = fname_meta['name_candidates'][0]
    return final

# ═══════════════════════════════════════════════════════════════════
# (5) Sentence-level parsing — unchanged
# ═══════════════════════════════════════════════════════════════════
def find_title(full_text, max_lines=10):
    for line in full_text.split('\n')[:max_lines]:
        line = line.strip()
        if line and '。' not in line and 4 <= len(line) <= 60:
            if re.search(r'[\u4e00-\u9fffA-Za-z]', line):
                return line
    return ""

SENTENCE_SPLIT = re.compile(r'[。!?！？]\s*')

def text_to_sentences(text, title=None):
    if title: text = text.replace(title, ' ', 1)
    body = re.sub(r'\n+', ' ', text)
    body = re.sub(r'\s+', ' ', body)
    return [s.strip() for s in SENTENCE_SPLIT.split(body) if s.strip() and len(s) <= 500]

PERIOD_RE = re.compile(r'\b(20\d{2})([EAFP]|\(F\)|\(E\)|\(A\))?(?![\d/])', re.I)
NUM_RE    = re.compile(r'-?\d{1,3}(?:,\d{3})*(?:\.\d+)?|-?\d+\.?\d*')

def normalize_period(s):
    if not s: return ""
    return s.strip().upper().replace("(", "").replace(")", "").replace(" ", "")

def find_canonical(line_lower):
    for alias in ALL_ALIASES:
        if len(alias) >= 2 and alias in line_lower:
            return ALIAS2CANON[alias], 100, alias
    match = process.extractOne(line_lower[:80], ALL_ALIASES,
                                scorer=fuzz.partial_ratio, score_cutoff=MIN_SCORE)
    if match:
        return ALIAS2CANON[match[0]], int(match[1]), match[0]
    return None, 0, None

def extract_unit(line):
    if "百萬元" in line: return "mn_ntd"
    if "千元"   in line: return "thousand_ntd"
    if "億元"   in line: return "hundred_mn_ntd"
    if "NT$M" in line or "NT$mn" in line: return "mn_ntd"
    if "US$M" in line or "US$mn" in line: return "mn_usd"
    if "%" in line or "％" in line: return "pct"
    if "倍" in line: return "ratio"
    if "元" in line: return "ntd"
    return ""

def parse_sentence(sentence):
    out = []
    if not sentence or len(sentence) > 500: return out
    s = sentence.strip()
    s_lower = s.lower()
    canon, score, alias_used = find_canonical(s_lower)
    if not canon: return out
    unit = extract_unit(s)
    cleaned = s_lower.replace(alias_used, " ", 1) if alias_used else s_lower

    numbers = []
    for m in NUM_RE.finditer(cleaned):
        try: numbers.append((m.start(), float(m.group(0).replace(",", ""))))
        except: pass
    periods = []
    for m in PERIOD_RE.finditer(cleaned):
        periods.append((m.start(), normalize_period(m.group(0))))
    numbers = [(pos, v) for pos, v in numbers
               if not (1900 <= v <= 2100 and v == int(v))]
    if not numbers: return out

    if len(periods) >= 2 and len(periods) == len(numbers):
        for (pp, pv), (np_, nv) in zip(periods, numbers):
            out.append({"canonical": canon, "period": pv, "value": nv,
                        "unit": unit, "score": score, "raw": s[:200]})
    elif len(periods) >= 1:
        for pp, pv in periods:
            best_n, best_dist = None, 1e9
            for np_, nv in numbers:
                if np_ > pp:
                    d = np_ - pp
                    if d < best_dist: best_dist, best_n = d, nv
            if best_n is None and numbers: best_n = numbers[-1][1]
            if best_n is not None:
                out.append({"canonical": canon, "period": pv, "value": best_n,
                            "unit": unit, "score": score, "raw": s[:200]})
    else:
        out.append({"canonical": canon, "period": "", "value": numbers[-1][1],
                    "unit": unit, "score": score, "raw": s[:200]})
    return out

# ═══════════════════════════════════════════════════════════════════
# Extraction
# ═══════════════════════════════════════════════════════════════════
def extract_pdf(pdf_path):
    rows = []; pages = 0; title = ""; page1_text = ""; err = None
    try:
        with pdfplumber.open(pdf_path) as pdf:
            pages = len(pdf.pages)
            full_text_parts = []
            for i, pg in enumerate(pdf.pages):
                t = pg.extract_text() or ""
                full_text_parts.append(t)
                if i == 0: page1_text = t
            full_text = "\n".join(full_text_parts)
            title = find_title(full_text)
            for sent in text_to_sentences(full_text, title):
                rows.extend(parse_sentence(sent))
    except Exception as e: err = str(e)[:200]
    seen = set(); deduped = []
    for r in rows:
        k = (r["canonical"], r["period"], r["value"])
        if k in seen: continue
        seen.add(k); deduped.append(r)
    return {"pages": pages, "rows": deduped, "title": title,
            "page1_text": page1_text[:5000], "err": err}

def extract_docx(docx_path):
    rows = []; err = None; title = ""; page1_text = ""
    try:
        from docx import Document
        doc = Document(docx_path)
        parts = [p.text for p in doc.paragraphs if p.text]
        for tbl in doc.tables:
            for row in tbl.rows:
                parts.append(" ".join((c.text or "").strip() for c in row.cells))
        full_text = "\n".join(parts)
        page1_text = full_text[:3000]
        title = find_title(full_text)
        for sent in text_to_sentences(full_text, title):
            rows.extend(parse_sentence(sent))
    except Exception as e: err = str(e)[:200]
    seen = set(); deduped = []
    for r in rows:
        k = (r["canonical"], r["period"], r["value"])
        if k in seen: continue
        seen.add(k); deduped.append(r)
    return {"pages": 1, "rows": deduped, "title": title,
            "page1_text": page1_text, "err": err}

# ═══════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════
def main():
    Path(RUN_DIR).mkdir(parents=True, exist_ok=True)
    Path(Path(LOCAL_DUCKDB).parent).mkdir(parents=True, exist_ok=True)

    files = []
    for ext in ("*.pdf","*.docx","*.doc"):
        files.extend(glob.glob(os.path.join(INPUT_DIR, "**", ext), recursive=True))
    files = sorted(set(files))
    print(f"[FILES] Found {len(files)} files")

    log_lines = [f"# v2.2 log · {datetime.now().isoformat()}"]
    all_rows = []
    file_summaries = []

    t0 = time.time()
    for i, f in enumerate(files, 1):
        ext = Path(f).suffix.lower()
        fname_meta = parse_filename_meta(f)
        t_file = time.time()

        if ext == ".pdf":   res = extract_pdf(f)
        elif ext in (".docx",".doc"): res = extract_docx(f)
        else:               continue

        meta = cross_validate_page1(fname_meta, res.get('page1_text',''))
        elapsed = time.time() - t_file

        n = len(res["rows"])
        status = "ERR" if res["err"] else ("OK" if n > 0 else "EMPTY")
        msg = (f"  [{i:>2}/{len(files)}] {status:<5} "
               f"{Path(f).name[:46]:<46} "
               f"broker={meta.get('broker','?'):<8} via={meta.get('broker_match_alias','-')[:10]:<10} "
               f"ticker={meta.get('ticker','?'):<5} rows={n:<4} {elapsed:.1f}s")
        if res["err"]: msg += f"  ERR: {res['err'][:40]}"
        print(msg)
        log_lines.append(msg)

        for r in res["rows"]:
            all_rows.append({
                "filename":           Path(f).name,
                "report_title":       res.get('title','')[:200],
                "broker":             meta.get('broker',''),
                "broker_full":        BROKER_DISPLAY.get(meta.get('broker',''), ''),
                "broker_match_alias": meta.get('broker_match_alias',''),
                "ticker":             meta.get('ticker',''),
                "yfinance_ticker":    (meta.get('ticker','')+'.TW') if meta.get('ticker') else '',
                "bloomberg_ticker":   (meta.get('ticker','')+' TT') if meta.get('ticker') else '',
                "name":               meta.get('name',''),
                "report_date":        meta.get('report_date',''),
                "ticker_conf":        meta.get('ticker_confidence',''),
                "broker_conf":        meta.get('broker_confidence',''),
                "canonical":          r["canonical"],
                "fin_type":           reverse_fin_type(r["canonical"]),
                "period":             r["period"],
                "value":              r["value"],
                "unit":               r["unit"],
                "score":              r["score"],
                "raw":                r["raw"],
            })
        file_summaries.append({
            "filename":           Path(f).name,
            "title":              res.get('title','')[:120],
            "broker":             meta.get('broker',''),
            "broker_full":        BROKER_DISPLAY.get(meta.get('broker',''),''),
            "broker_match_alias": meta.get('broker_match_alias',''),
            "ticker":             meta.get('ticker',''),
            "name":               meta.get('name',''),
            "report_date":        meta.get('report_date',''),
            "pages":              res["pages"], "rows": n, "err": res["err"],
            "ticker_conf":        meta.get('ticker_confidence',''),
            "broker_conf":        meta.get('broker_confidence',''),
        })

    elapsed_total = time.time() - t0

    print(f"\n[DB] Writing {len(all_rows)} rows → {LOCAL_DUCKDB}")
    if Path(LOCAL_DUCKDB).exists(): Path(LOCAL_DUCKDB).unlink()
    con = duckdb.connect(LOCAL_DUCKDB)
    con.execute("""
        CREATE TABLE vrn_financial_local_v2_2 (
            "filename"           VARCHAR, "report_title"       VARCHAR,
            "broker"             VARCHAR, "broker_full"        VARCHAR,
            "broker_match_alias" VARCHAR,
            "ticker"             VARCHAR, "yfinance_ticker"    VARCHAR,
            "bloomberg_ticker"   VARCHAR, "name"               VARCHAR,
            "report_date"        VARCHAR, "ticker_conf"        VARCHAR,
            "broker_conf"        VARCHAR, "canonical"          VARCHAR,
            "fin_type"           VARCHAR, "period"             VARCHAR,
            "value"              DOUBLE,  "unit"               VARCHAR,
            "score"              INTEGER, "raw"                VARCHAR
        )
    """)
    if all_rows:
        cols = ["filename","report_title","broker","broker_full","broker_match_alias",
                "ticker","yfinance_ticker","bloomberg_ticker","name","report_date",
                "ticker_conf","broker_conf","canonical","fin_type","period",
                "value","unit","score","raw"]
        ph = ",".join(["?"]*len(cols))
        col_quoted = ",".join(f'"{c}"' for c in cols)
        con.executemany(
            f"INSERT INTO vrn_financial_local_v2_2 ({col_quoted}) VALUES ({ph})",
            [tuple(r.get(c) for c in cols) for r in all_rows],
        )
    n_db = con.execute("SELECT COUNT(*) FROM vrn_financial_local_v2_2").fetchone()[0]
    con.close()
    print(f"[DB] Wrote {n_db} rows")

    # Stats
    canon_hist = Counter(r["canonical"] for r in all_rows)
    fin_hist   = Counter(r["fin_type"] for r in all_rows)
    period_hist= Counter(r["period"] for r in all_rows)
    broker_hist= Counter(s["broker"] for s in file_summaries if s["broker"])
    broker_conf_hist = Counter(s.get("broker_conf","") for s in file_summaries)
    ticker_conf_hist = Counter(s.get("ticker_conf","") for s in file_summaries)
    alias_hist = Counter(s.get("broker_match_alias","") for s in file_summaries if s.get("broker_match_alias",""))

    print(f"\n[STATS] Total rows: {len(all_rows)} from {len(file_summaries)} files")
    print(f"[STATS] Total time: {elapsed_total:.1f}s")
    print(f"\n[STATS] Broker dist (file count, with match alias):")
    for k,v in broker_hist.most_common():
        print(f"    {k:<10} {v:<3}  ({BROKER_DISPLAY.get(k,'')})")
    print(f"\n[STATS] Top 10 match aliases used:")
    for k,v in alias_hist.most_common(10):
        print(f"    {k!r:<22} {v}")
    print(f"\n[STATS] Broker confidence:")
    for k,v in broker_conf_hist.most_common():
        print(f"    {(k or 'unknown'):<22} {v}")
    print(f"\n[STATS] Ticker confidence:")
    for k,v in ticker_conf_hist.most_common():
        print(f"    {(k or 'unknown'):<22} {v}")
    print(f"\n[STATS] fin_type:")
    for k,v in fin_hist.most_common():
        print(f"    {k:<22} {v}")
    print(f"\n[STATS] Top 20 canonical:")
    for k,v in canon_hist.most_common(20):
        print(f"    {k:<22} {v}")

    summary = {
        "generated":      datetime.now().isoformat(timespec="seconds"),
        "version":        "v2.2 (longest-match)",
        "input_dir":      INPUT_DIR,
        "files_total":    len(file_summaries),
        "rows_total":     len(all_rows),
        "elapsed_sec":    elapsed_total,
        "duckdb":         LOCAL_DUCKDB,
        "ssot_loaded":    SSOT_LOADED,
        "corpus_size":    {"canonicals": len(CANON_SET), "aliases": len(ALIAS2CANON)},
        "broker_dict_size":{"canonicals": len(BROKER_DISPLAY), "aliases": len(BROKER_LOOKUP)},
        "canon_hist":     dict(canon_hist.most_common()),
        "fin_type_hist":  dict(fin_hist.most_common()),
        "period_hist":    dict(period_hist.most_common(20)),
        "broker_hist":    dict(broker_hist.most_common()),
        "broker_alias_hist":dict(alias_hist.most_common()),
        "broker_conf":    dict(broker_conf_hist.most_common()),
        "ticker_conf":    dict(ticker_conf_hist.most_common()),
        "broker_display": BROKER_DISPLAY,
        "files":          file_summaries[:200],
    }
    Path(RESULT_JSON).write_text(json.dumps(summary, ensure_ascii=False, indent=2),
                                  encoding="utf-8")
    Path(LOG_FILE).write_text("\n".join(log_lines), encoding="utf-8")
    print(f"\n[JSON] {RESULT_JSON}")

if __name__ == "__main__":
    try: main()
    except BaseException:
        print("[FATAL]"); print(traceback.format_exc()); raise
'@

$Code = $Code `
    -replace '__INPUT_DIR__',    ($InputDir   -replace '\\','\\') `
    -replace '__RUN_DIR__',      ($RunDir     -replace '\\','\\') `
    -replace '__SSOT_PATH__',    ($SsotPath   -replace '\\','\\') `
    -replace '__RESULT_JSON__',  ($ResultJson -replace '\\','\\') `
    -replace '__LOCAL_DUCKDB__', ($LocalDuckdb -replace '\\','\\') `
    -replace '__LOG_FILE__',     ($LogFile    -replace '\\','\\') `
    -replace '__MIN_SCORE__',    "$MinScore"

Set-Content -LiteralPath $ExtractorPy -Value $Code -Encoding UTF8

& $PythonExe -m py_compile $ExtractorPy
if ($LASTEXITCODE -ne 0) {
    Write-Host "  [FAIL] Python compile failed" -ForegroundColor Red
    return
}
Write-Host "  [OK] Compiled" -ForegroundColor Green

Write-Host ""
Write-Host "──── Phase 2 · Running v2.2 extractor ────" -ForegroundColor Yellow
& $PythonExe $ExtractorPy
$rcExt = $LASTEXITCODE

# HTML Report
Write-Host ""
Write-Host "──── Phase 3 · HTML Report ────" -ForegroundColor Yellow

$ReportPyCode = @'
# -*- coding: utf-8 -*-
import json, html as h, sys
from pathlib import Path
RESULT_JSON, HTML_OUT, DUCKDB_PATH = sys.argv[1], sys.argv[2], sys.argv[3]
data = json.loads(Path(RESULT_JSON).read_text(encoding="utf-8"))
display = data.get("broker_display", {})

def safe(s): return h.escape(str(s) if s is not None else "")
def hist_rows(d):
    if not d: return ""
    return "".join(f"<tr><td>{safe(k)}</td><td>{v}</td></tr>" for k,v in d.items())

broker_hist_rows = "".join(
    f"<tr><td><b>{safe(k)}</b></td><td>{safe(display.get(k,''))}</td><td>{v}</td></tr>"
    for k,v in data.get('broker_hist',{}).items()
)
alias_hist_rows = "".join(
    f"<tr><td>{safe(k)}</td><td>{v}</td></tr>"
    for k,v in data.get('broker_alias_hist',{}).items()
)

file_rows = ""
for f in data["files"]:
    cls = "ok" if f["rows"]>0 and not f.get("err") else ("warn" if f.get("err") else "skip")
    title = (f.get('title') or '')[:80]
    file_rows += (f'<tr class="{cls}">'
                  f'<td>{safe(f["filename"])}</td>'
                  f'<td>{safe(title)}</td>'
                  f'<td><b>{safe(f["broker"])}</b></td>'
                  f'<td>{safe(f.get("broker_full",""))}</td>'
                  f'<td><i>{safe(f.get("broker_match_alias",""))}</i></td>'
                  f'<td>{safe(f["ticker"])}</td>'
                  f'<td>{safe(f.get("name",""))}</td>'
                  f'<td>{safe(f["report_date"])}</td>'
                  f'<td>{safe(f["pages"])}</td>'
                  f'<td><b>{f["rows"]}</b></td>'
                  f'<td>{safe(f.get("broker_conf",""))}</td>'
                  f'<td>{safe(f.get("ticker_conf",""))}</td>'
                  f'<td>{safe(f.get("err",""))}</td>'
                  f'</tr>')

corpus = data.get("corpus_size", {})
brokers = data.get("broker_dict_size", {})

html = f"""<!doctype html>
<html lang="zh-TW"><head><meta charset="utf-8">
<title>VRN Local Extract v2.2 · Longest-Match</title>
<style>
body{{font-family:'DM Sans','Noto Sans TC',Arial;background:#f5f4f0;color:#1e1d1a;margin:0;padding:14px;font-size:11.5px}}
.w{{max-width:1750px;margin:auto}}
.hdr{{background:#fff;border:1px solid #dbd9d3;border-radius:12px;padding:14px;position:relative;overflow:hidden}}
.hdr::before{{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,#4c78a8,#439a9a,#7a6daa,#c4943a,#c96b5a)}}
h1{{margin:0;font-size:18px;color:#264653}}
.sub{{font-size:11px;color:#6b6860;margin-top:4px;font-family:monospace}}
.kpi{{display:grid;grid-template-columns:repeat(7,1fr);gap:8px;margin-top:12px}}
.k{{background:#fff;border:1px solid #dbd9d3;border-radius:8px;padding:10px;text-align:center}}
.kn{{font-size:18px;font-weight:700;color:#4c78a8;font-family:monospace}}
.kl{{font-size:9px;color:#9c9890;text-transform:uppercase;letter-spacing:.4px;margin-top:2px}}
.grid{{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:10px;margin-top:10px}}
.card{{background:#fff;border:1px solid #dbd9d3;border-radius:8px;overflow:hidden;max-height:400px;overflow-y:auto}}
.card h3{{margin:0;padding:8px 11px;background:#edecea;border-bottom:1px solid #dbd9d3;font-size:11px;color:#3d3c38;position:sticky;top:0}}
table{{width:100%;border-collapse:collapse;font-size:10.5px}}
td{{padding:5px 8px;border-bottom:1px solid #f0eee9}}
th{{background:#264653;color:#fff;padding:6px 8px;text-align:left;font-size:10px}}
tr.ok td{{background:#fff}}
tr.warn td{{background:#fef3c7}}
tr.skip td{{background:#f3f4f6;color:#9c9890}}
tr:hover td{{background:#f5f4f0!important}}
.full{{margin-top:10px}}
i{{color:#7a6daa;font-style:normal;font-family:monospace}}
</style></head><body>
<div class="w">
<div class="hdr">
  <h1>VRN Local Extractor v2.2 · Broker Longest-Match</h1>
  <div class="sub">Generated {safe(data['generated'])} · DuckDB: {safe(DUCKDB_PATH)}</div>
  <div class="kpi">
    <div class="k"><div class="kn">{data['files_total']}</div><div class="kl">Files</div></div>
    <div class="k"><div class="kn">{data['rows_total']}</div><div class="kl">Rows</div></div>
    <div class="k"><div class="kn">{data['elapsed_sec']:.1f}s</div><div class="kl">Elapsed</div></div>
    <div class="k"><div class="kn">{data['rows_total']/max(data['files_total'],1):.1f}</div><div class="kl">Avg/File</div></div>
    <div class="k"><div class="kn">{corpus.get('canonicals',0)}</div><div class="kl">Canonicals</div></div>
    <div class="k"><div class="kn">{corpus.get('aliases',0)}</div><div class="kl">Aliases</div></div>
    <div class="k"><div class="kn">{brokers.get('canonicals',0)}</div><div class="kl">Brokers</div></div>
  </div>
</div>

<div class="grid">
  <div class="card"><h3>Broker (file count)</h3>
    <table><tr><th>code</th><th>name</th><th>n</th></tr>{broker_hist_rows}</table>
  </div>
  <div class="card"><h3>Match Alias Used</h3>
    <table><tr><th>alias</th><th>n</th></tr>{alias_hist_rows}</table>
    <h3 style="margin-top:8px">Broker Conf</h3>
    <table><tr><th>level</th><th>n</th></tr>{hist_rows(data.get('broker_conf',{}))}</table>
  </div>
  <div class="card"><h3>Canonical (top 30)</h3>
    <table><tr><th>canonical</th><th>n</th></tr>
    {''.join(f'<tr><td>{safe(k)}</td><td>{v}</td></tr>' for k,v in list(data['canon_hist'].items())[:30])}
    </table>
  </div>
  <div class="card"><h3>fin_type / Period</h3>
    <table><tr><th>fin_type</th><th>n</th></tr>{hist_rows(data['fin_type_hist'])}</table>
    <h3 style="margin-top:8px">Period (top 20)</h3>
    <table><tr><th>period</th><th>n</th></tr>{hist_rows(data['period_hist'])}</table>
  </div>
</div>

<div class="full card" style="max-height:none"><h3>Files Processed (broker via match-alias)</h3>
  <table>
    <tr><th>filename</th><th>title</th><th>broker</th><th>broker_full</th><th>matched alias</th><th>ticker</th>
        <th>name</th><th>date</th><th>pages</th><th>rows</th><th>broker_conf</th>
        <th>ticker_conf</th><th>err</th></tr>
    {file_rows}
  </table>
</div>

</div></body></html>
"""
Path(HTML_OUT).write_text(html, encoding="utf-8")
print(f"[HTML] {HTML_OUT}")
'@

$reportPy = Join-Path $RunDir "build_report.py"
Set-Content -LiteralPath $reportPy -Value $ReportPyCode -Encoding UTF8

if (Test-Path $ResultJson) {
    & $PythonExe $reportPy $ResultJson $HtmlReport $LocalDuckdb
    if ($rcExt -eq 0 -and (Test-Path $HtmlReport)) {
        Write-Host "  [OK] Report: $HtmlReport" -ForegroundColor Green
        if (-not $NoOpen) { Start-Process $HtmlReport }
    }
}

$elapsed = [math]::Round(([datetime]::Now - $script:t0).TotalSeconds, 1)
Write-Host ""
Write-Host "════════════════════════════════════════════════════════════════════════════" -ForegroundColor Green
if ($rcExt -eq 0) {
    Write-Host "  ✓ DONE · elapsed=${elapsed}s" -ForegroundColor Green
} else {
    Write-Host "  ! rc=$rcExt · elapsed=${elapsed}s" -ForegroundColor Yellow
}
Write-Host "════════════════════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  Output : $LocalDuckdb"
Write-Host "  Report : $HtmlReport"
Write-Host ""
try { Read-Host "Press Enter to exit" | Out-Null } catch {}

