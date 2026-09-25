#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VRN_Financial_Synonyms_SSOT.py
================================
VRN Single Source of Truth — Financial Term Synonyms & Normalization
Provides: metric aliases, Chinese/English mappings, sector codes,
broker term normalization for Taiwan equity research reports

ANCHOR[VRN:ANCHOR:SYN-001] — Metric synonyms
ANCHOR[VRN:ANCHOR:SYN-002] — Chinese/English field mappings
ANCHOR[VRN:ANCHOR:SYN-003] — Sector / industry codes
ANCHOR[VRN:ANCHOR:SYN-004] — Currency & unit normalization
ANCHOR[VRN:ANCHOR:SYN-005] — Report type synonyms
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
import re
from typing import Dict, List, Optional, Tuple

__version__   = "1.0.0"
__module_id__ = "VRN_FINANCIAL_SYNONYMS_SSOT"

# ── ANCHOR[VRN:ANCHOR:SYN-001] — Metric synonyms ────────────────────────────
# Maps various spellings/abbreviations → canonical field name
METRIC_SYNONYMS: Dict[str, str] = {
    # Revenue
    "revenue": "revenue", "sales": "revenue", "turnover": "revenue",
    "net sales": "revenue", "total revenue": "revenue",
    "營收": "revenue", "營業收入": "revenue", "總收入": "revenue",
    "收入": "revenue", "銷售收入": "revenue",
    # Net Income
    "net income": "net_income", "net profit": "net_income",
    "profit after tax": "net_income", "pat": "net_income",
    "淨利": "net_income", "稅後淨利": "net_income", "純益": "net_income",
    "稅後盈餘": "net_income", "本期淨利": "net_income",
    # EPS
    "eps": "eps", "earnings per share": "eps", "diluted eps": "eps_diluted",
    "basic eps": "eps_basic",
    "每股盈餘": "eps", "每股純益": "eps", "稀釋eps": "eps_diluted",
    # DPS
    "dps": "dps", "dividend per share": "dps", "dividend": "dps",
    "每股股息": "dps", "每股現金股息": "dps", "現金股利": "dps",
    # Target Price
    "target price": "target_price", "tp": "target_price", "price target": "target_price",
    "目標價": "target_price", "目標股價": "target_price",
    # Operating Profit
    "operating profit": "op_profit", "ebit": "ebit", "operating income": "op_profit",
    "營業利益": "op_profit", "營業獲利": "op_profit",
    # EBITDA
    "ebitda": "ebitda",
    # Gross Profit
    "gross profit": "gross_profit", "gross margin": "gross_margin",
    "毛利": "gross_profit", "毛利率": "gross_margin",
    # P/E
    "pe": "pe_ratio", "p/e": "pe_ratio", "price to earnings": "pe_ratio",
    "本益比": "pe_ratio",
    # P/B
    "pb": "pb_ratio", "p/b": "pb_ratio", "price to book": "pb_ratio",
    "股價淨值比": "pb_ratio",
    # ROE / ROA
    "roe": "roe", "return on equity": "roe", "股東權益報酬率": "roe",
    "roa": "roa", "return on assets": "roa", "資產報酬率": "roa",
    # Cash Flow
    "free cash flow": "fcf", "fcf": "fcf", "operating cash flow": "ocf",
    "自由現金流": "fcf", "營業現金流": "ocf",
}

# ── ANCHOR[VRN:ANCHOR:SYN-002] — Chinese/English field mappings ─────────────
CN_EN_FIELD_MAP: Dict[str, str] = {
    "公司名稱": "company_name",   "公司": "company_name",
    "股票代號": "ticker",          "代號": "ticker",   "代碼": "ticker",
    "產業": "sector",              "行業": "sector",
    "評等": "rating",              "投資建議": "rating",
    "目標價": "target_price",      "目標股價": "target_price",
    "報告日期": "report_date",     "日期": "report_date",
    "券商": "broker",              "發行機構": "broker",
    "分析師": "analyst",
    "預測年度": "fiscal_year",     "會計年度": "fiscal_year",
    "收盤價": "close_price",       "股價": "close_price",
    "市值": "market_cap",
    "股本": "shares_outstanding",
}

# ── ANCHOR[VRN:ANCHOR:SYN-003] — Sector / industry codes ────────────────────
SECTOR_SYNONYMS: Dict[str, str] = {
    # Technology
    "technology": "Technology", "tech": "Technology", "semiconductors": "Semiconductors",
    "semiconductor": "Semiconductors", "ic design": "Semiconductors",
    "科技": "Technology", "半導體": "Semiconductors", "ic設計": "Semiconductors",
    "晶圓代工": "Foundry", "foundry": "Foundry",
    "電子": "Electronics", "electronics": "Electronics",
    "pcb": "PCB", "印刷電路板": "PCB",
    "伺服器": "Server", "server": "Server", "ai server": "AI Server",
    # Financials
    "financial": "Financials", "bank": "Banking", "banking": "Banking",
    "金融": "Financials", "銀行": "Banking", "保險": "Insurance",
    "insurance": "Insurance", "券商": "Brokerage", "brokerage": "Brokerage",
    # Consumer
    "consumer": "Consumer", "retail": "Retail",
    "消費": "Consumer", "零售": "Retail", "餐飲": "F&B", "f&b": "F&B",
    # Healthcare
    "healthcare": "Healthcare", "pharma": "Pharma", "pharmaceutical": "Pharma",
    "醫療": "Healthcare", "生技": "Biotech", "biotech": "Biotech",
    # Industrials
    "industrial": "Industrials", "machinery": "Machinery",
    "工業": "Industrials", "機械": "Machinery",
    # Energy
    "energy": "Energy", "oil": "Oil & Gas", "utilities": "Utilities",
    "能源": "Energy", "電力": "Utilities",
    # Real Estate
    "real estate": "Real Estate", "reit": "REIT",
    "房地產": "Real Estate",
}

# ── ANCHOR[VRN:ANCHOR:SYN-004] — Currency & unit normalization ───────────────
CURRENCY_MAP: Dict[str, str] = {
    "twd": "TWD", "nt$": "TWD", "nt dollar": "TWD", "新台幣": "TWD",
    "usd": "USD", "us$": "USD", "us dollar": "USD", "美元": "USD",
    "cny": "CNY", "rmb": "CNY", "人民幣": "CNY",
    "hkd": "HKD", "hk$": "HKD", "港元": "HKD",
    "jpy": "JPY", "¥": "JPY", "日圓": "JPY",
    "eur": "EUR", "€": "EUR", "歐元": "EUR",
}

UNIT_MULTIPLIERS: Dict[str, float] = {
    "": 1.0, "元": 1.0,
    "千": 1e3,   "k": 1e3,    "thousand": 1e3,
    "萬": 1e4,
    "百萬": 1e6,  "m": 1e6,    "million": 1e6, "mn": 1e6,
    "億": 1e8,
    "十億": 1e9,  "b": 1e9,    "billion": 1e9, "bn": 1e9,
    "兆": 1e12,  "t": 1e12,   "trillion": 1e12,
}

# ── ANCHOR[VRN:ANCHOR:SYN-005] — Report type synonyms ───────────────────────
REPORT_TYPE_SYNONYMS: Dict[str, str] = {
    "equity research": "equity_research", "initiation": "equity_research",
    "coverage initiation": "equity_research", "company note": "equity_research",
    "flash note": "equity_research", "update": "equity_research",
    "sector report": "sector_report", "sector": "sector_report",
    "strategy": "strategy", "outlook": "strategy",
    "economics": "economics", "macro": "economics",
    "個股報告": "equity_research", "產業報告": "sector_report",
    "策略報告": "strategy",
}

# ── Normalization helpers ─────────────────────────────────────────────────────
def normalize_metric(raw: str) -> str:
    """Map raw metric name → canonical field name."""
    if not raw: return raw
    return METRIC_SYNONYMS.get(raw.strip().lower(), raw.strip())

def normalize_field_cn(raw: str) -> str:
    """Map Chinese field label → English canonical."""
    if not raw: return raw
    return CN_EN_FIELD_MAP.get(raw.strip(), raw.strip())

def normalize_sector(raw: str) -> str:
    """Map raw sector string → canonical sector."""
    if not raw: return raw
    return SECTOR_SYNONYMS.get(raw.strip().lower(), raw.strip())

def normalize_currency(raw: str) -> str:
    """Map raw currency string → ISO code."""
    if not raw: return raw
    return CURRENCY_MAP.get(raw.strip().lower(), raw.strip().upper())

def parse_unit(raw: str) -> float:
    """Return multiplier for unit string."""
    if not raw: return 1.0
    return UNIT_MULTIPLIERS.get(raw.strip().lower(), 1.0)

def normalize_report_type(raw: str) -> str:
    """Map raw report type → canonical."""
    if not raw: return "unknown"
    return REPORT_TYPE_SYNONYMS.get(raw.strip().lower(), "unknown")

# All synonym lookup combined
SYNONYMS_ALL: Dict[str, Dict] = {
    "metric":      METRIC_SYNONYMS,
    "field_cn":    CN_EN_FIELD_MAP,
    "sector":      SECTOR_SYNONYMS,
    "currency":    CURRENCY_MAP,
    "report_type": REPORT_TYPE_SYNONYMS,
}