#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
================================================================================
  VDF_MDL201_GenerateFullRegistry.py
================================================================================
  VDF Registry · 自動展開全 inventory 至 JSON registry
  Version    : 1.0.0   |   Module ID : VDF-REG-GEN-001

  從現有模組內嵌的 dict 自動產出完整 VDF_MDL403_RegistryFull.json:
    - MDL003 FRED_REGISTRY  → 47 series (US.Rates.*, Inflation, Employ, ...)
    - MDL003 AKSHARE_REGISTRY → 13 codes (CN futures + shipping + macro)
    - MDL003 AAII + CNN endpoints → 2 sentiment items
    - MDL002 MARKETS (19 groups × tickers) → ~175 YF items
    - MDL001-VRF SSOT regex → TW universe dynamic loader reference

  Cross-validation 自動配對規則 (auto-pair):
    - 同概念在多源 → 自動加 cross_check tolerance
    - 例: DGS10 (FRED) + ^TNX (YF) 自動配對
    - 例: GOLDAMGBD228NLBM (FRED) + GC=F (YF) 自動配對
    - 例: CHNMFGPMI (FRED) + cn_pmi_mfg (AKShare) 自動配對

USAGE
================================================================================
  python VDF_MDL201_GenerateFullRegistry.py             # 產 full registry
  python VDF_MDL201_GenerateFullRegistry.py --validate  # 同時跑 schema 驗證
  python VDF_MDL201_GenerateFullRegistry.py --output OUTPUT.json
"""
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import os, sys, json, re, importlib.util
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# =====================================================================================
# 📋 ALL PARAMETERS
# =====================================================================================

HERE = Path(__file__).parent
MODULES_DIR = HERE   # 假設與本檔同層 (sandbox: /home/claude/vdf_mdl003)
OUTPUT_FILE = HERE / "VDF_MDL403_RegistryFull.json"
SCHEMA_FILE = HERE / "VDF_MDL401_RegistrySchema.json"

# =====================================================================================
# 🤝 CROSS-VALIDATION AUTO-PAIRING RULES
# =====================================================================================
# 同一概念在不同源的對應關係, 用於自動加 cross_check
# 格式: { fred_id: {yfinance_ticker?, akshare_code?, tolerance, note} }

CROSS_PAIRS = {
    # FRED ↔ YF (yield indicators)
    "DGS2":            {"yf": "^IRX",   "tol_abs": 0.10, "note": "^IRX is 13-week T-bill, proxy"},
    "DGS5":            {"yf": "^FVX",   "tol_abs": 0.05, "note": "^FVX is 5Y yield"},
    "DGS10":           {"yf": "^TNX",   "tol_abs": 0.05, "note": "^TNX is 10Y yield"},
    "DGS30":           {"yf": "^TYX",   "tol_abs": 0.05, "note": "^TYX is 30Y yield"},
    # FRED ↔ YF (commodities)
    "DCOILWTICO":      {"yf": "CL=F",   "tol_pct": 2.0,  "note": "CL=F futures front, FRED spot"},
    "DCOILBRENTEU":    {"yf": "BZ=F",   "tol_pct": 2.0,  "note": "BZ=F front-month"},
    "DHHNGSP":         {"yf": "NG=F",   "tol_pct": 5.0,  "note": "NG=F front-month"},
    "GOLDAMGBD228NLBM":{"yf": "GC=F",   "tol_pct": 1.0,  "note": "GC=F COMEX vs London AM"},
    # FRED ↔ YF (USD)
    "DTWEXBGS":        {"yf": "DX-Y.NYB","tol_pct": 1.0, "note": "DXY proxy"},
    # FRED ↔ AKShare (China)
    "CHNMFGPMI":       {"ak": "cn_pmi_mfg",  "tol_abs": 0.3, "note": "Both NBS-sourced"},
    # FRED ↔ ETF proxy
    "BAMLH0A0HYM2":    {"yf": "HYG",  "tol_pct": None, "trust_low": True, "note": "HYG inverse proxy"},
    # SP500 ↔
    "SP500":           {"yf": "^GSPC", "tol_pct": 0.1, "note": "FRED has ~1d lag"},
}

# =====================================================================================
# 📚 PROBE: import MDL002/003 to extract registries
# =====================================================================================

def _import_module(filename: str):
    """Safely import a VDF module by file."""
    path = MODULES_DIR / filename
    if not path.exists():
        return None, f"file not found: {path}"
    saved = sys.argv[:]
    sys.argv = [filename, "--no-pause"]
    try:
        spec = importlib.util.spec_from_file_location(filename, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod, None
    except Exception as e:
        return None, str(e)[:200]
    finally:
        sys.argv = saved


def extract_fred_registry():
    """從 MDL003 抽 FRED_REGISTRY."""
    mod, err = _import_module("VDF_MDL003_SentimentMacroEngine.py")
    if mod is None:
        print(f"  ⚠️ MDL003 import 失敗: {err}")
        return {}
    return getattr(mod, "FRED_REGISTRY", {})


def extract_akshare_registry():
    """從 MDL003 抽 AKSHARE_REGISTRY."""
    mod, err = _import_module("VDF_MDL003_SentimentMacroEngine.py")
    if mod is None:
        return {}
    return getattr(mod, "AKSHARE_REGISTRY", {})


def extract_yf_universe():
    """從 MDL002 抽 MARKETS + ASSET_CLASS_RULES."""
    mod, err = _import_module("VDF_MDL002_YFinanceFetchingEngine.py")
    if mod is None:
        print(f"  ⚠️ MDL002 import 失敗: {err}")
        return {}, {}
    return getattr(mod, "MARKETS", {}), getattr(mod, "ASSET_CLASS_RULES", {})


# =====================================================================================
# 🔧 BUILDER FUNCTIONS (FRED/AKShare/YF → schema-compliant item)
# =====================================================================================

# FRED theme → schema theme 映射 (因為 schema 已限定 enum)
FRED_THEME_MAP = {
    "Rates": "Rates", "Prices": "Inflation", "Employ": "Employment",
    "Growth": "Growth", "GDP": "Growth", "Credit": "Credit",
    "Fed": "Fed", "FinCond": "FinCond", "Housing": "Housing",
    "Trade": "FX", "Commodity": "Commodity", "PMI": "Macro", "Global": "Macro",
}

AK_THEME_MAP = {"Futures": "Futures", "Shipping": "Shipping", "Macro": "Macro"}

YF_THEME_MAP = {
    "INDICES_US": ("Index", "US"),         "INDICES_ASIA": ("Index", "Global"),
    "INDICES_EUROPE": ("Index", "Global"), "EQUITY_US": ("Equity", "US"),
    "EQUITY_TW_LISTED": ("Equity", "TW"),  "EQUITY_TW_OTC": ("Equity", "TW"),
    "EQUITY_ASIA": ("Equity", "Global"),   "EQUITY_EUROPE": ("Equity", "Global"),
    "ETF_REGION_GLOBAL": ("Index", "Global"),
    "ETF_SECTOR_US": ("Index", "US"),      "ETF_BONDS": ("Bond", "Global"),
    "ETF_THEMATIC": ("Index", "Global"),   "ETF_HELPER": ("Custom", "Global"),
    "ETF_TW_PASSIVE": ("Index", "TW"),     "ETF_TW_ACTIVE": ("Index", "TW"),
    "CURRENCIES": ("FX", "Global"),        "COMMODITIES": ("Commodity", "Global"),
    "BONDS_YIELDS": ("Rates", "US"),       "CRYPTO": ("Crypto", "Global"),
}


def build_fred_item(via_code: str, meta: Dict) -> Dict:
    """從 FRED_REGISTRY 一個 entry 建出符合 schema 的 item."""
    fred_id = meta.get("fred_id", "")
    raw_theme = meta.get("theme", "Macro")
    schema_theme = FRED_THEME_MAP.get(raw_theme, "Macro")
    sub_theme = meta.get("sub_theme", "")

    sources = [{
        "priority": 1,
        "name": "FRED",
        "source_id": fred_id,
        "fetcher": "VDF_MDL003.FREDFetcher._fetch_one",
        "trust": "official",
        "license": "public_domain",
        "rate_limit_per_min": 120,
        "timeout_seconds": 15,
    }]

    # Auto-pair cross-source
    validation = {"cross_check": False, "allow_single_source": True}
    if fred_id in CROSS_PAIRS:
        pair = CROSS_PAIRS[fred_id]
        if "yf" in pair:
            sources.append({
                "priority": 2,
                "name": "yfinance",
                "source_id": pair["yf"],
                "fetcher": "VDF_MDL002.YFinanceFetcher.history_latest",
                "trust": "low" if pair.get("trust_low") else "medium",
                "license": "scraped",
                "note": pair.get("note", ""),
            })
        if "ak" in pair:
            sources.append({
                "priority": 2,
                "name": "akshare",
                "source_id": pair["ak"],
                "fetcher": "VDF_MDL003.AKShareFetcher._fetch_one",
                "trust": "official",
                "license": "free_with_attribution",
                "note": pair.get("note", ""),
            })
        validation = {
            "cross_check": True,
            "consensus_method": "primary_first",
            "on_disagreement": "use_highest_trust",
            "allow_single_source": True,
        }
        if pair.get("tol_abs") is not None:
            validation["tolerance_abs"] = pair["tol_abs"]
        elif pair.get("tol_pct") is not None:
            validation["tolerance_pct"] = pair["tol_pct"]
        validation["outlier_z_threshold"] = 4.0

    # Freq normalize: 'A' (Annual) → 'Y' (per schema enum)
    freq_raw = meta.get("freq", "M")
    freq_norm = {"A": "Y", "SA": "Y", "BD": "D"}.get(freq_raw, freq_raw)
    if freq_norm not in {"D","W","M","Q","Y","intraday","irregular"}:
        freq_norm = "M"  # safe fallback

    item = {
        "via_code": via_code,
        "indicator_name": meta.get("indicator", via_code),
        "theme": schema_theme,
        "freq": freq_norm,
        "region": "US" if via_code.startswith("US.") else ("CN" if via_code.startswith("CN.") else "Global"),
        "sources": sources,
        "validation": validation,
        "downstream_modules": ["VDF-MDL003"],
        "active": True,
        "added": "2026-06-03",
        "owner": "tony",
    }
    if sub_theme:
        item["sub_theme"] = sub_theme
    if meta.get("unit"):
        item["unit"] = meta["unit"]
    return item


def build_akshare_item(code: str, meta: Dict) -> Dict:
    """從 AKSHARE_REGISTRY 建 item."""
    raw_theme = meta.get("theme", "Futures")
    schema_theme = AK_THEME_MAP.get(raw_theme, "Custom")
    sub_theme = meta.get("sub_theme", "")

    # via_code 推導: cn_copper_continuous → CN.Futures.Copper.Continuous
    parts = code.replace("cn_", "").split("_")
    if raw_theme == "Futures":
        title_parts = [p.capitalize() for p in parts]
        via_code = f"CN.Futures.{'.'.join(title_parts)}"
    elif raw_theme == "Shipping":
        via_code = "CN.Shipping." + parts[0].upper()
    elif raw_theme == "Macro":
        via_code = "CN.Macro." + "_".join([p.upper() for p in parts])
    else:
        via_code = f"CN.{raw_theme}.{code}"

    sources = [{
        "priority": 1,
        "name": "akshare",
        "source_id": code,
        "func": meta.get("func", ""),
        "sym":  meta.get("sym"),  # 允許 None
        "fetcher": "VDF_MDL003.AKShareFetcher._fetch_one",
        "trust": "high",
        "license": "scraped",
        "rate_limit_per_min": 30,
    }]
    validation = {"cross_check": False, "allow_single_source": True}
    if code == "cn_pmi_mfg":   # cross-check with FRED CHNMFGPMI
        validation = {"cross_check": True, "tolerance_abs": 0.3,
                      "consensus_method": "majority_vote",
                      "on_disagreement": "use_highest_trust",
                      "allow_single_source": True}

    item = {
        "via_code": via_code,
        "indicator_name": meta.get("name", code),
        "theme": schema_theme,
        "freq": "D" if raw_theme == "Futures" else ("M" if raw_theme == "Macro" else "D"),
        "region": "CN",
        "sources": sources,
        "validation": validation,
        "downstream_modules": ["VDF-MDL003"],
        "active": True,
        "added": "2026-06-03",
        "owner": "tony",
    }
    if sub_theme:
        item["sub_theme"] = sub_theme
    return item


def build_yf_item(ticker: str, name: str, group: str, rule: Dict) -> Dict:
    """從 MDL002 MARKETS entry 建 item."""
    theme, region = YF_THEME_MAP.get(group, ("Custom", "Global"))
    asset_class = rule.get("asset_class", "")

    # via_code 推導: AAPL → US.Equity.AAPL · 0050.TW → TW.Index.0050 · ^GSPC → US.Index.SP500
    if ticker.startswith("^"):
        clean = ticker.replace("^", "").replace(".", "_")
        symbol = {"GSPC":"SP500", "NDX":"NDX100", "DJI":"DJI", "RUT":"R2000",
                  "VIX":"VIX", "MOVE":"MOVE", "TNX":"UST10Y", "TYX":"UST30Y",
                  "FVX":"UST5Y", "IRX":"UST3M", "STOXX50E":"STOXX50",
                  "N225":"N225", "HSI":"HSI", "TWII":"TWII", "TWO":"TWO_OTC"}.get(clean, clean)
        via_code = f"{region}.{theme}.{symbol}"
    elif ticker.endswith(".TW") or ticker.endswith(".TWO"):
        tw_code = ticker.split(".")[0]
        via_code = f"TW.{theme}.{tw_code}"
    elif ticker.endswith("=X"):
        clean = ticker.replace("=X", "")
        via_code = f"Global.FX.{clean}"
    elif ticker.endswith("=F"):
        clean = ticker.replace("=F", "")
        via_code = f"Global.Commodity.{clean}"
    elif ticker.endswith("-USD"):
        clean = ticker.replace("-USD", "")
        via_code = f"Global.Crypto.{clean}"
    elif "." in ticker:  # foreign listings like DX-Y.NYB
        via_code = f"{region}.{theme}.{ticker.replace('.', '_').replace('-', '_')}"
    else:
        via_code = f"{region}.{theme}.{ticker}"

    sources = [{
        "priority": 1,
        "name": "yfinance",
        "source_id": ticker,
        "fetcher": "VDF_MDL002.YFinanceFetcher.history",
        "trust": "medium",
        "license": "scraped",
        "rate_limit_per_min": 60,
    }]

    item = {
        "via_code": via_code,
        "indicator_name": name,
        "theme": theme,
        "sub_theme": group,
        "freq": "D",
        "region": region,
        "sources": sources,
        "validation": {"cross_check": False, "allow_single_source": True,
                       "weekend_holiday_policy": "strict" if "Crypto" in theme else "forward_fill"},
        "downstream_modules": ["VDF-MDL002"],
        "active": True,
        "added": "2026-06-03",
        "owner": "tony",
        "tags": [asset_class.lower()] if asset_class else [],
    }
    return item


def build_sentiment_items() -> List[Dict]:
    """AAII + CNN F&G."""
    return [
        {
            "via_code": "Global.Sentiment.AAII",
            "indicator_name": "AAII Investor Sentiment Survey",
            "theme": "Sentiment", "sub_theme": "Retail Investor",
            "unit": "% allocation", "freq": "W", "region": "US",
            "tags": ["contrarian"],
            "sources": [
                {"priority": 1, "name": "AAII", "source_id": "sentiment_xls",
                 "url": "https://www.aaii.com/files/surveys/sentiment.xls",
                 "fetcher": "VDF_MDL003.AAIIFetcher.fetch",
                 "trust": "official", "license": "free_with_attribution"},
                {"priority": 2, "name": "AAII", "source_id": "sentiment_html",
                 "url": "https://www.aaii.com/sentimentsurvey/sent_results",
                 "fetcher": "VDF_MDL003.AAIIFetcher.fetch",
                 "trust": "high", "license": "scraped",
                 "note": "HTML fallback if xls 403/blocked"},
            ],
            "validation": {"cross_check": False, "allow_single_source": True,
                           "weekend_holiday_policy": "skip"},
            "downstream_modules": ["VDF-MDL003"],
            "active": True, "added": "2026-06-03", "owner": "tony",
        },
        {
            "via_code": "Global.Sentiment.CNN_FearGreed",
            "indicator_name": "CNN Fear & Greed Index",
            "theme": "Sentiment", "sub_theme": "Composite",
            "unit": "Index 0-100", "freq": "D", "region": "US",
            "tags": ["contrarian", "composite"],
            "sources": [
                {"priority": 1, "name": "CNN_FearGreed", "source_id": "main_index",
                 "url": "https://production.dataviz.cnn.io/index/fearandgreed/graphdata",
                 "fetcher": "VDF_MDL003.CNNFearGreedFetcher.fetch",
                 "trust": "official", "license": "scraped",
                 "note": "Includes 7 sub-indicators"},
            ],
            "validation": {"cross_check": False, "allow_single_source": True},
            "downstream_modules": ["VDF-MDL003"],
            "active": True, "added": "2026-06-03", "owner": "tony",
        },
    ]


def build_tw_universe_dynamic() -> Dict:
    """TW universe 用 SSOT regex 動態載入, 不展開所有 ~1700 ticker."""
    return {
        "via_code": "TW.Universe.Dynamic",
        "indicator_name": "TW 全市場 universe (TWSE + TPEX, dynamic)",
        "theme": "Equity", "sub_theme": "TW Universe",
        "unit": "list of tickers", "freq": "D", "region": "TW",
        "tags": ["dynamic", "ssot"],
        "sources": [
            {"priority": 1, "name": "TWSE_OpenAPI", "source_id": "STOCK_DAY_ALL",
             "url": "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL",
             "fetcher": "VDF_MDL001.TWSEOpenAPIFetcher.fetch_universe",
             "trust": "official", "license": "public_domain"},
            {"priority": 1, "name": "TPEX_OpenAPI", "source_id": "stk_quote_all",
             "url": "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes",
             "fetcher": "VDF_MDL001.TPEXOpenAPIFetcher.fetch_universe",
             "trust": "official", "license": "public_domain"},
        ],
        "validation": {
            "cross_check": False,
            "allow_single_source": False,   # 兩個都要成功才算
            "consensus_min_sources": 2,
        },
        "downstream_modules": ["VDF-MDL001", "VDF-MDL005", "VDF-MDL006"],
        "active": True, "added": "2026-06-03", "owner": "tony",
        "notes": "Dynamic universe. Each ticker fetched via SSOT regex (?!0)(?!202[1-9])(?!2030)([1-9]\\d{3}). Approximately 1700 stocks daily.",
    }


# =====================================================================================
# 🎯 Main builder
# =====================================================================================

def main():
    print(f"🚀 VDF Registry Full Builder · {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"   Modules dir: {MODULES_DIR}")

    # 1. Extract from modules
    print("\n📥 Step 1: Extract from modules")
    fred = extract_fred_registry()
    akshare = extract_akshare_registry()
    yf_markets, yf_rules = extract_yf_universe()
    print(f"   ✓ FRED      : {len(fred)} series")
    print(f"   ✓ AKShare   : {len(akshare)} codes")
    print(f"   ✓ YF MARKETS: {sum(len(v) for v in yf_markets.values())} tickers ({len(yf_markets)} groups)")

    # 2. Build items
    print("\n🔧 Step 2: Build items")
    items: List[Dict] = []
    # FRED
    for via_code, meta in fred.items():
        items.append(build_fred_item(via_code, meta))
    print(f"   ✓ FRED items: {len(items)}")
    n0 = len(items)
    # AKShare
    for code, meta in akshare.items():
        items.append(build_akshare_item(code, meta))
    print(f"   ✓ AKShare items: {len(items)-n0}")
    n0 = len(items)
    # Sentiment (AAII + CNN)
    items.extend(build_sentiment_items())
    print(f"   ✓ Sentiment items: {len(items)-n0}")
    n0 = len(items)
    # TW Universe (dynamic ref)
    items.append(build_tw_universe_dynamic())
    print(f"   ✓ TW Universe (dynamic ref): {len(items)-n0}")
    n0 = len(items)
    # YFinance 175
    for group, tickers in yf_markets.items():
        rule = yf_rules.get(group, {})
        for ticker, name in tickers.items():
            items.append(build_yf_item(ticker, name, group, rule))
    print(f"   ✓ YFinance items: {len(items)-n0}")

    # 3. De-duplicate by via_code (multi-source items may collide)
    seen = {}
    for it in items:
        vc = it["via_code"]
        if vc in seen:
            # Merge sources
            existing = seen[vc]
            existing_ids = {(s["name"], s.get("source_id", "")) for s in existing["sources"]}
            for s in it["sources"]:
                if (s["name"], s.get("source_id", "")) not in existing_ids:
                    s["priority"] = max(p["priority"] for p in existing["sources"]) + 1
                    existing["sources"].append(s)
        else:
            seen[vc] = it
    items = list(seen.values())
    print(f"\n📊 After dedup: {len(items)} unique via_code items")

    # 4. Assemble registry
    registry = {
        "meta": {
            "version": "1.0.0",
            "owner": "tony",
            "updated": datetime.now().strftime("%Y-%m-%d"),
            "description": f"VDF Extraction Registry · auto-generated from MDL002/003 · {len(items)} items",
            "ssot_locks": {
                "TW_TICKER_REGEX":     "(?!0)(?!202[1-9])(?!2030)([1-9]\\d{3})",
                "TW_BLOOMBERG_REGEX":  "([1-9]\\d{3}) TT",
                "TW_YFINANCE_REGEX":   "([1-9]\\d{3})\\.(TW|TWO)",
            },
            "fred_api_key_env": "FRED_API_KEY",
        },
        "items": items,
    }

    # 5. Write
    OUTPUT_FILE.write_text(json.dumps(registry, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n💾 Written: {OUTPUT_FILE} ({OUTPUT_FILE.stat().st_size // 1024} KB)")

    # 6. Stats
    print("\n📊 Stats:")
    from collections import Counter
    themes = Counter(it["theme"] for it in items)
    regions = Counter(it.get("region", "?") for it in items)
    multi = sum(1 for it in items if len(it["sources"]) > 1)
    cross = sum(1 for it in items if it.get("validation", {}).get("cross_check"))
    print(f"   Themes:  {dict(themes)}")
    print(f"   Regions: {dict(regions)}")
    print(f"   Multi-source items: {multi}")
    print(f"   Cross-check enabled: {cross}")
    print(f"   Total sources: {sum(len(it['sources']) for it in items)}")

    # 7. Optional schema validation
    if "--validate" in sys.argv:
        print("\n🔍 Schema validation")
        try:
            from jsonschema import Draft7Validator
            schema = json.loads(SCHEMA_FILE.read_text(encoding="utf-8"))
            validator = Draft7Validator(schema)
            errors = list(validator.iter_errors(registry))
            if errors:
                print(f"   ✗ {len(errors)} schema errors:")
                for e in errors[:5]:
                    path = ".".join(str(p) for p in e.absolute_path)
                    print(f"     · {path}: {e.message[:100]}")
            else:
                print(f"   ✓ All {len(items)} items pass schema validation")
        except ImportError:
            print("   ⚠️ jsonschema not installed, skip")

    return 0


if __name__ == "__main__":
    sys.exit(main())
