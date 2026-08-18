# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import csv
import html
import json
import re
import shutil
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any


VERSION = "VRN_VALUATION_DICTIONARY_SOURCEBANK_REPAIR_V0595"


# ==================================================================================================
# def 01_CONFIG
# ==================================================================================================
def def_config() -> dict:
    via_root = Path(r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics")
    vrn_root = via_root / "module" / "VRN"
    run_root = vrn_root / "_vrn_operation_ui_runs"
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = run_root / f"VRN_VALUATION_DICTIONARY_SOURCEBANK_REPAIR_V0595_INNER_{ts}"

    return {
        "via_root": via_root,
        "vrn_root": vrn_root,
        "run_root": run_root,
        "canonical_dir": vrn_root / "_vrn_canonical_active",
        "integrated_root": vrn_root / "_vrn_integrated_trust_runs",
        "stable_root": vrn_root / "_vrn_stable_release",
        "input_dir": vrn_root / "input",
        "supportive_dir": via_root / "module" / "supportive_module",
        "config_dir": vrn_root / "config",
        "run_dir": run_dir,
        "backup_dir": run_dir / "backup_before_v0595",
        "out_html": run_dir / "VRN_Valuation_Dictionary_SourceBank_Repair_v0595.html",
        "out_json": run_dir / "vrn_valuation_dictionary_sourcebank_repair_v0595.json",
        "out_basic_csv": run_dir / "vrn_basicinfo_valuation_repair_preview_v0595.csv",
        "out_audit_csv": run_dir / "vrn_valuation_repair_audit_v0595.csv",
        "out_source_bank_csv": run_dir / "vrn_firstpage_sourcebank_v0595.csv",
        "out_missing_diag_csv": run_dir / "vrn_valuation_missing_diagnosis_v0595.csv",
        "out_file_matrix_csv": run_dir / "vrn_related_file_matrix_v0595.csv",
        "out_support_csv": run_dir / "vrn_supportive_matrix_v0595.csv",
        "out_dictionary_json": vrn_root / "config" / "VRN_Valuation_Dictionary_v0595.json",
        "out_rule_lock_json": vrn_root / "config" / "VRN_Valuation_Dictionary_SourceBank_Repair_RuleLock_v0595.json",
    }


# ==================================================================================================
# def 02_UTILS
# ==================================================================================================
def def_now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def def_h(x: Any) -> str:
    return html.escape("" if x is None else str(x))


def def_nonblank(x: Any) -> bool:
    return str(x or "").strip() not in ["", "nan", "None", "null", "undefined"]


def def_clean_text(x: Any) -> str:
    s = "" if x is None else str(x)
    s = s.replace("\u3000", " ")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def def_read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    for enc in ["utf-8-sig", "utf-8", "cp950", "big5"]:
        try:
            with path.open("r", encoding=enc, newline="") as f:
                return list(csv.DictReader(f))
        except Exception:
            pass
    return []


def def_write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cols = []
    for r in rows:
        for k in r.keys():
            if k not in cols:
                cols.append(k)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def def_write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def def_first(row: dict, keys: list[str]) -> str:
    for k in keys:
        if def_nonblank(row.get(k, "")):
            return str(row.get(k)).strip()
    return ""


def def_safe_json_loads(x: Any) -> dict:
    if not def_nonblank(x):
        return {}
    try:
        obj = json.loads(str(x))
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def def_norm_filename(x: Any) -> str:
    s = str(x or "").strip().replace("\\", "/").split("/")[-1]
    s = re.sub(r"\.pdf$", "", s, flags=re.I)
    return s.lower()


def def_norm_ticker(x: Any) -> str:
    m = re.search(r"\b[1-9]\d{3}\b", str(x or ""))
    return m.group(0) if m else ""


def def_window(text: str, start: int, end: int, radius: int = 380) -> str:
    a = max(0, start - radius)
    b = min(len(text), end + radius)
    return def_clean_text(text[a:b])


def def_find_latest_files(root: Path, patterns: list[str], max_files: int = 180) -> list[Path]:
    hits = []
    if not root.exists():
        return []
    for pat in patterns:
        try:
            hits.extend(root.rglob(pat))
        except Exception:
            pass
    hits = [p for p in hits if p.exists() and p.is_file()]
    hits = sorted(set(hits), key=lambda p: p.stat().st_mtime, reverse=True)
    return hits[:max_files]


def def_lights(sev: str) -> str:
    s = str(sev or "").upper()
    if "ERR" in s or "RED" in s:
        return "🔴 INPUT  🔴 DB  🔴 TRUST"
    if "WARN" in s or "MISSING" in s or "YELLOW" in s:
        return "🟢 INPUT  🟡 DB  🟡 TRUST"
    return "🟢 INPUT  🟢 DB  🟢 TRUST"


# ==================================================================================================
# def 03_VALUATION_DICTIONARY
# ==================================================================================================
def def_valuation_dictionary() -> dict:
    return {
        "metadata": {
            "system_name": "Veritas Intelligence System",
            "module": "Valuation_Dictionary",
            "version": "0.5.9.5",
            "encoding": "UTF-8",
            "last_updated": "2026-05-21",
            "source_policy": "broker_report_text_only_yfinance_never_overwrites_valuation_method",
        },
        "categories": [
            {"category_id": "CAT_ABS", "category_en": "Absolute Valuation", "category_zh": "絕對估值法"},
            {"category_id": "CAT_REL", "category_en": "Relative Valuation", "category_zh": "相對估值法"},
            {"category_id": "CAT_AST", "category_en": "Asset-Based Valuation", "category_zh": "資產基礎估值法"},
        ],
        "methods": [
            {
                "uid": "VAL_001",
                "canonical": "P/E",
                "category_id": "CAT_REL",
                "name_en": "Price-to-Earnings Ratio",
                "name_zh": "本益比",
                "abbreviations": ["P/E", "PER", "PE", "PE Ratio", "P/E Ratio"],
                "synonyms_en": ["Earnings Multiple", "Price Multiple", "Price-to-Earnings", "Forward P/E", "Trailing P/E"],
                "synonyms_zh": ["市盈率", "價格盈餘倍數", "預估本益比", "目標本益比", "合理本益比", "常態本益比", "歷史本益比", "本益比評價", "本益比法", "本益比區間"],
                "regex": [
                    r"(?i)\bP\s*/?\s*E\b", r"(?i)\bPER\b", r"(?i)\bPE\s*ratio\b",
                    r"(?i)\bprice[- ]?to[- ]?earnings\b", r"(?i)\bearnings\s+multiple\b",
                    r"(?i)\bforward\s+P\s*/?\s*E\b", r"(?i)\btrailing\s+P\s*/?\s*E\b",
                    r"(?i)\bFY\d{2}E?\s*P\s*/?\s*E\b",
                    r"(?i)\b\d+(\.\d+)?\s*x\s*(P\s*/?\s*E|PE|PER)\b",
                    r"(?i)(P\s*/?\s*E|PE|PER)\s*(of|multiple|ratio)?\s*\d+(\.\d+)?\s*x",
                    r"(?i)implying.{0,80}(P\s*/?\s*E|PE|PER).{0,60}\d+(\.\d+)?\s*x",
                    r"(?i)our\s+(TP|PT|target price|price target).{0,140}(P\s*/?\s*E|PE|PER)",
                    r"(?i)we\s+(derive|value|set).{0,160}(P\s*/?\s*E|PE|PER|earnings multiple)",
                    r"(?i)applying.{0,100}\d+(\.\d+)?\s*x.{0,70}(earnings|EPS|P\s*/?\s*E|PE|PER)",
                    r"(?i)(sector|peer|historical).{0,60}(average|premium|discount).{0,100}(P\s*/?\s*E|PE|PER|multiple)",
                    r"本益比|市盈率|價格盈餘倍數|預估本益比|目標本益比|合理本益比|常態本益比|歷史本益比|展望年本益比",
                    r"本益比評價|本益比法|本益比區間|本益比倍數",
                    r"\d+(\.\d+)?\s*倍\s*本益比", r"\d+(\.\d+)?\s*x\s*本益比",
                    r"以.{0,100}?\d+(\.\d+)?\s*[xX倍]?.{0,40}本益比.{0,90}?評價",
                    r"基於.{0,110}?\d+(\.\d+)?\s*[xX倍]?.{0,40}(PER|PE|P/E|本益比)",
                    r"評價區間.{0,100}\d+(\.\d+)?\s*[xX倍]\s*[-~–至]\s*\d+(\.\d+)?\s*[xX倍]?.{0,90}(PER|PE|P/E|本益比)",
                    r"常態本益比.{0,80}\d+(\.\d+)?\s*[-~–至]\s*\d+(\.\d+)?\s*倍",
                    r"給[予與].{0,80}\d+(\.\d+)?\s*倍",
                    r"推導目標價.{0,160}(本益比|PER|PE|P/E)",
                    r"目標價隱含.{0,160}(本益比|PER|PE|P/E)",
                    r"參考同業.{0,160}(本益比|PER|PE|P/E|倍數)",
                    r"歷史區間.{0,160}(本益比|PER|PE|P/E|倍數)",
                    r"以.{0,50}(明年|後年|202\d年|FY\d{2}).{0,80}EPS.{0,90}(估算|評價|推導)"
                ],
            },
            {
                "uid": "VAL_002",
                "canonical": "P/B",
                "category_id": "CAT_REL",
                "name_en": "Price-to-Book Ratio",
                "name_zh": "股價淨值比",
                "abbreviations": ["P/B", "PBR", "PB Ratio", "PTB"],
                "synonyms_en": ["Price-to-Equity Ratio", "Book Multiple"],
                "synonyms_zh": ["市淨率", "價格帳面價值比", "市值淨值比", "淨值比"],
                "regex": [
                    r"(?i)\bP\s*/\s*B\b", r"(?i)\bPBR\b", r"(?i)\bPBV\b", r"(?i)\bPTB\b",
                    r"(?i)\bprice[- ]?to[- ]?book\b", r"(?i)\bbook\s+value\s+multiple\b",
                    r"股價淨值比|市淨率|價格帳面價值比|市值淨值比|淨值比|帳面價值倍數|每股淨值",
                    r"\d+(\.\d+)?\s*x\s*(P\s*/\s*B|PBR|PBV|PTB)"
                ],
            },
            {
                "uid": "VAL_003",
                "canonical": "DCF",
                "category_id": "CAT_ABS",
                "name_en": "Discounted Cash Flow",
                "name_zh": "現金流量折現法",
                "abbreviations": ["DCF"],
                "synonyms_en": ["DCF Model", "Discounted Cashflow"],
                "synonyms_zh": ["折現現金流模型", "現金流折現估值", "現金流折現", "折現現金流"],
                "regex": [
                    r"(?i)\bDCF\b", r"(?i)\bdiscounted\s+cash\s*flow\b",
                    r"(?i)\bWACC\b", r"(?i)\bterminal\s+value\b",
                    r"現金流量折現|折現現金流|現金流折現|自由現金流折現|折現率|加權平均資金成本|終值|永續成長率"
                ],
            },
            {
                "uid": "VAL_004",
                "canonical": "DDM",
                "category_id": "CAT_ABS",
                "name_en": "Dividend Discount Model",
                "name_zh": "股利折現模型",
                "abbreviations": ["DDM"],
                "synonyms_en": ["Dividend Discount", "Dividend Yield Valuation"],
                "synonyms_zh": ["股息折現法", "股利折現", "殖利率評價"],
                "regex": [
                    r"(?i)\bDDM\b", r"(?i)\bdividend\s+discount\b", r"(?i)\bdividend\s+yield\b",
                    r"股利折現|股利折現模型|股息折現|殖利率評價|現金股利殖利率"
                ],
            },
            {
                "uid": "VAL_005",
                "canonical": "FCFF",
                "category_id": "CAT_ABS",
                "name_en": "Free Cash Flow to Firm",
                "name_zh": "企業自由現金流量模型",
                "abbreviations": ["FCFF"],
                "synonyms_en": ["Free Cash Flow to the Firm"],
                "synonyms_zh": ["企業自由現金流", "公司自由現金流"],
                "regex": [r"(?i)\bFCFF\b", r"(?i)\bfree\s+cash\s+flow\s+to\s+(the\s+)?firm\b", r"企業自由現金流量|企業自由現金流|公司自由現金流"],
            },
            {
                "uid": "VAL_006",
                "canonical": "FCFE",
                "category_id": "CAT_ABS",
                "name_en": "Free Cash Flow to Equity",
                "name_zh": "股權自由現金流量模型",
                "abbreviations": ["FCFE"],
                "synonyms_en": ["Free Cash Flow to Shareholders"],
                "synonyms_zh": ["股權自由現金流", "股東自由現金流"],
                "regex": [r"(?i)\bFCFE\b", r"(?i)\bfree\s+cash\s+flow\s+to\s+equity\b", r"股權自由現金流量|股權自由現金流|股東自由現金流"],
            },
            {
                "uid": "VAL_007",
                "canonical": "RIV",
                "category_id": "CAT_ABS",
                "name_en": "Residual Income Valuation",
                "name_zh": "剩餘所得估值法",
                "abbreviations": ["RIV", "RI"],
                "synonyms_en": ["Residual Income", "Residual Income Model"],
                "synonyms_zh": ["剩餘收益", "剩餘利益", "超額報酬模型"],
                "regex": [r"(?i)\bRIV\b", r"(?i)\bresidual\s+income\b", r"剩餘所得|剩餘收益|剩餘利益|超額報酬模型"],
            },
            {
                "uid": "VAL_008",
                "canonical": "APV",
                "category_id": "CAT_ABS",
                "name_en": "Adjusted Present Value",
                "name_zh": "調整後現值法",
                "abbreviations": ["APV"],
                "synonyms_en": ["Adjusted PV"],
                "synonyms_zh": ["調整現值", "調整後現值"],
                "regex": [r"(?i)\bAPV\b", r"(?i)\badjusted\s+present\s+value\b", r"調整後現值|調整現值"],
            },
            {
                "uid": "VAL_009",
                "canonical": "GGM",
                "category_id": "CAT_ABS",
                "name_en": "Gordon Growth Model",
                "name_zh": "戈登成長模型",
                "abbreviations": ["GGM"],
                "synonyms_en": ["Constant Growth Model", "Gordon Model"],
                "synonyms_zh": ["戈登模型", "股利穩定成長模型"],
                "regex": [r"(?i)\bGGM\b", r"(?i)\bgordon\s+growth\s+model\b", r"(?i)\bconstant\s+growth\s+model\b", r"戈登成長模型|戈登模型|股利穩定成長模型"],
            },
            {
                "uid": "VAL_010",
                "canonical": "EVA",
                "category_id": "CAT_ABS",
                "name_en": "Economic Value Added",
                "name_zh": "經濟附加價值",
                "abbreviations": ["EVA"],
                "synonyms_en": ["Economic Profit"],
                "synonyms_zh": ["經濟利潤", "經濟增加值"],
                "regex": [r"(?i)\bEVA\b", r"(?i)\beconomic\s+value\s+added\b", r"經濟附加價值|經濟利潤|經濟增加值"],
            },
            {
                "uid": "VAL_011",
                "canonical": "P/S",
                "category_id": "CAT_REL",
                "name_en": "Price-to-Sales Ratio",
                "name_zh": "股價營收比",
                "abbreviations": ["P/S", "PSR"],
                "synonyms_en": ["Sales Multiple", "Revenue Multiple"],
                "synonyms_zh": ["市銷率", "價格營收比", "營收倍數"],
                "regex": [r"(?i)\bP\s*/\s*S\b", r"(?i)\bPSR\b", r"(?i)\bprice[- ]?to[- ]?sales\b", r"(?i)\bsales\s+multiple\b", r"(?i)\brevenue\s+multiple\b", r"股價營收比|市銷率|價格營收比|營收倍數"],
            },
            {
                "uid": "VAL_012",
                "canonical": "P/CF",
                "category_id": "CAT_REL",
                "name_en": "Price-to-Cash Flow Ratio",
                "name_zh": "股價現金流量比",
                "abbreviations": ["P/CF", "PCF"],
                "synonyms_en": ["Price-to-Cashflow"],
                "synonyms_zh": ["市現率", "價格現金流比"],
                "regex": [r"(?i)\bP\s*/\s*CF\b", r"(?i)\bPCF\b", r"(?i)\bprice[- ]?to[- ]?cash\s*flow\b", r"股價現金流量比|市現率|價格現金流比"],
            },
            {
                "uid": "VAL_013",
                "canonical": "PEG",
                "category_id": "CAT_REL",
                "name_en": "Price-to-Earnings-to-Growth Ratio",
                "name_zh": "本益成長比",
                "abbreviations": ["PEG", "PEG Ratio"],
                "synonyms_en": ["Price Earnings Growth"],
                "synonyms_zh": ["市盈率相對盈利增長比率"],
                "regex": [r"(?i)\bPEG\b", r"(?i)\bprice\s+earnings\s+growth\b", r"本益成長比|PEG評價|市盈率相對盈利增長比率"],
            },
            {
                "uid": "VAL_014",
                "canonical": "EV/EBITDA",
                "category_id": "CAT_REL",
                "name_en": "Enterprise Value to EBITDA",
                "name_zh": "企業價值倍數",
                "abbreviations": ["EV/EBITDA"],
                "synonyms_en": ["Enterprise Multiple"],
                "synonyms_zh": ["息稅折舊攤銷前盈餘倍數", "企業乘數"],
                "regex": [r"(?i)\bEV\s*/?\s*EBITDA\b", r"(?i)\bEV[- ]?to[- ]?EBITDA\b", r"(?i)\benterprise\s+value\s+to\s+EBITDA\b", r"(?i)\benterprise\s+multiple\b", r"企業價值.{0,30}EBITDA|EV/EBITDA|EBITDA倍數|企業價值倍數|企業乘數"],
            },
            {
                "uid": "VAL_015",
                "canonical": "EV/Sales",
                "category_id": "CAT_REL",
                "name_en": "Enterprise Value to Sales",
                "name_zh": "企業價值對營收比",
                "abbreviations": ["EV/Sales", "EV/S"],
                "synonyms_en": ["Enterprise Value to Revenue", "EV/Revenue"],
                "synonyms_zh": ["企業價值營收比"],
                "regex": [r"(?i)\bEV\s*/\s*Sales\b", r"(?i)\bEV\s*/\s*S\b", r"(?i)\bEV\s*/\s*Revenue\b", r"(?i)\benterprise\s+value\s+to\s+(sales|revenue)\b", r"企業價值對營收比|企業價值營收比"],
            },
            {
                "uid": "VAL_016",
                "canonical": "EV/EBIT",
                "category_id": "CAT_REL",
                "name_en": "Enterprise Value to EBIT",
                "name_zh": "企業價值對息稅前利潤比",
                "abbreviations": ["EV/EBIT"],
                "synonyms_en": ["EBIT Multiple"],
                "synonyms_zh": ["EBIT倍數"],
                "regex": [r"(?i)\bEV\s*/?\s*EBIT\b", r"(?i)\bEV[- ]?to[- ]?EBIT\b", r"(?i)\benterprise\s+value\s+to\s+EBIT\b", r"(?i)\bEBIT\s+multiple\b", r"企業價值對息稅前利潤比|企業價值.{0,20}EBIT|EBIT倍數"],
            },
            {
                "uid": "VAL_017",
                "canonical": "NAV",
                "category_id": "CAT_AST",
                "name_en": "Net Asset Value",
                "name_zh": "淨資產價值法",
                "abbreviations": ["NAV"],
                "synonyms_en": ["Net Asset Value Method"],
                "synonyms_zh": ["資產淨值法", "資產淨值"],
                "regex": [r"(?i)\bNAV\b", r"(?i)\bnet\s+asset\s+value\b", r"淨資產價值|資產淨值法|資產淨值"],
            },
            {
                "uid": "VAL_018",
                "canonical": "SOTP",
                "category_id": "CAT_AST",
                "name_en": "Sum of the Parts",
                "name_zh": "分部估值法",
                "abbreviations": ["SOTP"],
                "synonyms_en": ["Break-up Value Valuation", "Parts Valuation", "Sum-of-the-Parts"],
                "synonyms_zh": ["加總估值法", "拆分估值法", "分類加總法", "分項加總法"],
                "regex": [r"(?i)\bSOTP\b", r"(?i)\bsum[- ]of[- ]the[- ]parts\b", r"(?i)\bsum\s+of\s+parts\b", r"(?i)\bsegment\s+valuation\b", r"分部估值|加總估值|拆分估值|分類加總|分項加總|分部加總|各業務加總|事業群加總"],
            },
            {
                "uid": "VAL_019",
                "canonical": "Replacement Cost",
                "category_id": "CAT_AST",
                "name_en": "Replacement Cost Method",
                "name_zh": "重置成本法",
                "abbreviations": [],
                "synonyms_en": ["Replacement Cost"],
                "synonyms_zh": ["重置成本"],
                "regex": [r"(?i)\breplacement\s+cost\b", r"重置成本法|重置成本"],
            },
            {
                "uid": "VAL_020",
                "canonical": "Liquidation Value",
                "category_id": "CAT_AST",
                "name_en": "Liquidation Value",
                "name_zh": "清算價值法",
                "abbreviations": [],
                "synonyms_en": ["Liquidation Method"],
                "synonyms_zh": ["清算價值"],
                "regex": [r"(?i)\bliquidation\s+value\b", r"清算價值法|清算價值"],
            },
            {
                "uid": "VAL_021",
                "canonical": "BV",
                "category_id": "CAT_AST",
                "name_en": "Book Value",
                "name_zh": "帳面價值",
                "abbreviations": ["BV"],
                "synonyms_en": ["Book Value Method"],
                "synonyms_zh": ["帳面值"],
                "regex": [r"(?i)\bBV\b", r"(?i)\bbook\s+value\b", r"帳面價值|帳面值"],
            },
            {
                "uid": "VAL_022",
                "canonical": "NTA",
                "category_id": "CAT_AST",
                "name_en": "Net Tangible Assets",
                "name_zh": "有形資產淨值",
                "abbreviations": ["NTA"],
                "synonyms_en": ["Net Tangible Asset Value"],
                "synonyms_zh": ["有形淨資產"],
                "regex": [r"(?i)\bNTA\b", r"(?i)\bnet\s+tangible\s+assets?\b", r"有形資產淨值|有形淨資產"],
            },
        ],
    }


def def_method_patterns() -> dict:
    d = def_valuation_dictionary()
    out = {}
    for m in d["methods"]:
        out[m["canonical"]] = m["regex"]
    return out


def def_method_hard_gate(method: str, evidence: str) -> bool:
    e = evidence or ""
    gates = {
        "P/E": r"(?i)(\bP\s*/?\s*E\b|\bPER\b|\bPE\s*ratio\b|price[- ]?to[- ]?earnings|earnings\s+multiple|本益比|EPS|每股盈餘)",
        "P/B": r"(?i)(\bP\s*/\s*B\b|\bPBR\b|\bPBV\b|\bPTB\b|price[- ]?to[- ]?book|book\s+value|股價淨值比|市淨率|淨值比|帳面價值|每股淨值)",
        "P/S": r"(?i)(\bP\s*/\s*S\b|\bPSR\b|price[- ]?to[- ]?sales|sales\s+multiple|revenue\s+multiple|股價營收比|市銷率|營收倍數)",
        "P/CF": r"(?i)(\bP\s*/\s*CF\b|\bPCF\b|price[- ]?to[- ]?cash\s*flow|股價現金流量比|市現率)",
        "EV/EBITDA": r"(?i)(EV\s*/?\s*EBITDA|EV[- ]?to[- ]?EBITDA|EBITDA\s+multiple|企業價值.{0,30}EBITDA|EBITDA倍數|企業價值倍數)",
        "EV/Sales": r"(?i)(EV\s*/\s*Sales|EV\s*/\s*S|EV\s*/\s*Revenue|enterprise\s+value\s+to\s+(sales|revenue)|企業價值對營收比)",
        "EV/EBIT": r"(?i)(EV\s*/?\s*EBIT|EV[- ]?to[- ]?EBIT|EBIT\s+multiple|企業價值.{0,20}EBIT|EBIT倍數)",
        "DCF": r"(?i)(\bDCF\b|discounted\s+cash\s*flow|WACC|terminal\s+value|現金流量折現|折現現金流|現金流折現|終值)",
        "DDM": r"(?i)(\bDDM\b|dividend\s+discount|dividend\s+yield|股利折現|殖利率評價)",
        "FCFF": r"(?i)(\bFCFF\b|free\s+cash\s+flow\s+to\s+(the\s+)?firm|企業自由現金流)",
        "FCFE": r"(?i)(\bFCFE\b|free\s+cash\s+flow\s+to\s+equity|股權自由現金流)",
        "RIV": r"(?i)(\bRIV\b|residual\s+income|剩餘所得|剩餘收益)",
        "APV": r"(?i)(\bAPV\b|adjusted\s+present\s+value|調整後現值)",
        "GGM": r"(?i)(\bGGM\b|gordon\s+growth\s+model|戈登成長)",
        "EVA": r"(?i)(\bEVA\b|economic\s+value\s+added|經濟附加價值)",
        "PEG": r"(?i)(\bPEG\b|price\s+earnings\s+growth|本益成長比)",
        "NAV": r"(?i)(\bNAV\b|net\s+asset\s+value|淨資產價值|資產淨值)",
        "SOTP": r"(?i)(\bSOTP\b|sum[- ]of[- ]the[- ]parts|sum\s+of\s+parts|segment\s+valuation|分部估值|加總估值|分項加總)",
        "Replacement Cost": r"(?i)(replacement\s+cost|重置成本)",
        "Liquidation Value": r"(?i)(liquidation\s+value|清算價值)",
        "BV": r"(?i)(\bBV\b|book\s+value|帳面價值|帳面值)",
        "NTA": r"(?i)(\bNTA\b|net\s+tangible\s+assets?|有形資產淨值|有形淨資產)",
    }
    pat = gates.get(method)
    return True if not pat else bool(re.search(pat, e))


# ==================================================================================================
# def 04_SUPPORTIVE_APPEND
# ==================================================================================================
def def_backup(path: Path, backup_dir: Path) -> str:
    if not path.exists():
        return ""
    backup_dir.mkdir(parents=True, exist_ok=True)
    dst = backup_dir / f"{path.name}.bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(path, dst)
    return str(dst)


def def_append_once(path: Path, anchor: str, block: str) -> dict:
    if not path.exists():
        return {"path": str(path), "status": "ERR", "action": "MISSING", "detail": "file missing"}

    txt = path.read_text(encoding="utf-8", errors="ignore")
    if anchor in txt:
        return {"path": str(path), "status": "OK", "action": "SKIP_EXISTS", "detail": anchor}

    path.write_text(txt.rstrip() + "\n\n" + block.strip() + "\n", encoding="utf-8")
    return {"path": str(path), "status": "OK", "action": "APPENDED", "detail": anchor}


def def_patch_supportive(cfg: dict, valuation_dict: dict) -> list[dict]:
    ssot_py = cfg["supportive_dir"] / "VIA_SSOT_Unified.py"
    aug_ps1 = cfg["supportive_dir"] / "VIA_SSOT_PanoramicAugmenter_v2.ps1"
    rows = []

    py_anchor = "# [VIA:ANCHOR:VRN_VALUATION_DICTIONARY_V0595:START]"
    py_block = f'''
# [VIA:ANCHOR:VRN_VALUATION_DICTIONARY_V0595:START]
# def VRN Valuation Dictionary v05.9.5
# def append-only; no deletion; no existing symbol mutation
VRN_VALUATION_DICTIONARY_V0595 = {repr(valuation_dict)}

def vrn_get_valuation_dictionary_v0595():
    return VRN_VALUATION_DICTIONARY_V0595
# [VIA:ANCHOR:VRN_VALUATION_DICTIONARY_V0595:END]
'''.strip()

    ps_anchor = "# [VIA:ANCHOR:VRN_VALUATION_DICTIONARY_V0595:START]"
    ps_block = '''
# [VIA:ANCHOR:VRN_VALUATION_DICTIONARY_V0595:START]
# def VRN Valuation Dictionary v05.9.5
# def append-only; no deletion; no existing symbol mutation
function Get-VRNValuationDictionaryV0595 {
    [CmdletBinding()]
    param()
    return [ordered]@{
        AbsoluteValuation = @("DCF","DDM","FCFF","FCFE","RIV","APV","GGM","EVA")
        RelativeValuation = @("P/E","P/B","P/S","P/CF","PEG","EV/EBITDA","EV/Sales","EV/EBIT")
        AssetBasedValuation = @("NAV","SOTP","Replacement Cost","Liquidation Value","BV","NTA")
    }
}
# [VIA:ANCHOR:VRN_VALUATION_DICTIONARY_V0595:END]
'''.strip()

    for path, name, anchor, block in [
        (ssot_py, "VIA_SSOT_Unified.py", py_anchor, py_block),
        (aug_ps1, "VIA_SSOT_PanoramicAugmenter_v2.ps1", ps_anchor, ps_block),
    ]:
        bk = def_backup(path, cfg["backup_dir"])
        res = def_append_once(path, anchor, block)
        ok = res["status"] == "OK"

        detail = res["detail"]
        if path.suffix.lower() == ".py" and path.exists():
            try:
                ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
                detail += " | AST OK"
            except Exception as e:
                ok = False
                detail += " | AST ERR: " + str(e)

        rows.append({
            "Status Lights": def_lights("OK" if ok else "ERR"),
            "File": str(path),
            "Name": name,
            "Backup": bk,
            "Action": res["action"],
            "Status": "OK" if ok else "ERR",
            "Detail": detail,
            "Severity": "OK" if ok else "ERR",
        })

    return rows


# ==================================================================================================
# def 05_SOURCE_BANK
# ==================================================================================================
def def_related_file_patterns() -> list[str]:
    return [
        "vrn_basicinfo*.csv",
        "vrn_basicinfo*.json",
        "vrn_*source_text*.csv",
        "vrn_*sentence*.csv",
        "vrn_*first*page*.csv",
        "vrn_*page1*.csv",
        "vrn_*repaired*.csv",
        "vrn_*text*.csv",
        "vrn_*valuation*.csv",
        "VRN_*v05*.json",
        "*.pdf",
    ]


def def_collect_related_files(cfg: dict) -> list[Path]:
    files = []
    for p in [
        cfg["canonical_dir"] / "vrn_basicinfo_active.csv",
        cfg["canonical_dir"] / "vrn_financial_active.csv",
    ]:
        if p.exists():
            files.append(p)

    for root in [cfg["run_root"], cfg["integrated_root"], cfg["stable_root"], cfg["input_dir"]]:
        files.extend(def_find_latest_files(root, def_related_file_patterns(), max_files=220))

    seen = set()
    out = []
    for p in files:
        key = str(p).lower()
        if key not in seen and p.exists():
            seen.add(key)
            out.append(p)
    return out[:280]


def def_extract_pdf_first_page_text(path: Path) -> str:
    if path.suffix.lower() != ".pdf":
        return ""
    try:
        import pdfplumber
        with pdfplumber.open(str(path)) as pdf:
            if not pdf.pages:
                return ""
            return def_clean_text(pdf.pages[0].extract_text() or "")
    except Exception:
        return ""


def def_file_matrix(files: list[Path]) -> list[dict]:
    rows = []
    for p in files:
        rows.append({
            "Status Lights": "🟢 INPUT  🟢 DB  🟢 TRUST",
            "Path": str(p),
            "Name": p.name,
            "Type": "PDF" if p.suffix.lower() == ".pdf" else "CSV_OR_JSON",
            "Size": p.stat().st_size if p.exists() else 0,
            "Modified": datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S") if p.exists() else "",
            "Severity": "OK",
        })
    return rows


def def_row_key(row: dict) -> tuple[str, str]:
    filename = def_norm_filename(def_first(row, ["Filename", "File", "Source File", "source_file", "PDF", "Path"]))
    ticker = def_norm_ticker(def_first(row, ["Ticker", "Primary TW_TICKER", "Primary Tw Ticker", "ticker", "Stock Code"]))
    return filename, ticker


def def_pdf_key(path: Path) -> tuple[str, str]:
    return def_norm_filename(path.name), def_norm_ticker(path.name)


def def_source_zone_candidates(row: dict) -> list[tuple[str, str]]:
    zones = []

    def add(zone: str, value: Any):
        if def_nonblank(value):
            zones.append((zone, str(value)))

    for col in [
        "Valuation Method", "Valuation", "Valuation Evidence Text",
        "Target Price", "Rating", "Summary",
        "Source Text", "source_text", "Method", "method",
        "Sentence", "Sentence Text", "Text", "Page Text", "First Page Text",
        "FirstPage Text", "Page1 Text", "Repaired Text", "Body Text",
        "Title", "Main Title", "Subtitle", "Heading", "Chunk Text", "Content",
        "Filename Normalized", "Filename Tokens"
    ]:
        raw = row.get(col, "")
        obj = def_safe_json_loads(raw)
        if obj:
            for k in ["valuation", "target_price", "rating", "analyst", "summary", "body", "title", "page_text", "first_page"]:
                add(f"{col}.{k}", obj.get(k, ""))
        else:
            add(col, raw)

    return zones


def def_build_source_bank(files: list[Path]) -> tuple[dict, list[dict]]:
    bank: dict[tuple[str, str], list[tuple[str, str, str]]] = {}
    rows = []

    def add_bank(key, source, zone, text):
        text = def_clean_text(text)
        if not text:
            return
        bank.setdefault(key, []).append((source, zone, text))

    for p in files:
        if p.suffix.lower() == ".csv":
            data = def_read_csv(p)
            for r in data:
                key = def_row_key(r)
                fn, tk = key
                if key == ("", ""):
                    continue
                zones = def_source_zone_candidates(r)
                for z, t in zones:
                    add_bank(key, str(p), z, t)
                    if tk:
                        add_bank(("", tk), str(p), z, t)
                    if fn:
                        add_bank((fn, ""), str(p), z, t)

                rows.append({
                    "Status Lights": def_lights("OK" if zones else "WARN"),
                    "Source File": str(p),
                    "Filename Key": fn,
                    "Ticker Key": tk,
                    "Rows": len(data),
                    "Zone Count": len(zones),
                    "Has Source Text": any("source text" in z.lower() for z, _ in zones),
                    "Has First Page Text": any(("first" in z.lower() and "page" in z.lower()) or "page1" in z.lower() for z, _ in zones),
                    "Has Sentence Units": any("sentence" in z.lower() for z, _ in zones),
                    "Severity": "OK" if zones else "WARN",
                })

        elif p.suffix.lower() == ".pdf":
            key = def_pdf_key(p)
            text = def_extract_pdf_first_page_text(p)
            if text:
                add_bank(key, str(p), "PDF_FIRST_PAGE_TEXT_LAYER", text)
                if key[1]:
                    add_bank(("", key[1]), str(p), "PDF_FIRST_PAGE_TEXT_LAYER", text)
                if key[0]:
                    add_bank((key[0], ""), str(p), "PDF_FIRST_PAGE_TEXT_LAYER", text)

            rows.append({
                "Status Lights": def_lights("OK" if text else "WARN"),
                "Source File": str(p),
                "Filename Key": key[0],
                "Ticker Key": key[1],
                "Rows": 1,
                "Zone Count": 1 if text else 0,
                "Has Source Text": False,
                "Has First Page Text": bool(text),
                "Has Sentence Units": False,
                "Severity": "OK" if text else "WARN",
            })

    return bank, rows


def def_base_rows(cfg: dict) -> tuple[list[dict], Path, str]:
    candidates = def_find_latest_files(cfg["run_root"], [
        "vrn_basicinfo_valuation_precision_rebind_v0593.csv",
        "vrn_basicinfo_valuation_rebind_v0592.csv",
        "vrn_basicinfo_yfinance_field_fixed_preview_v0589.csv",
        "vrn_basicinfo_yfinance_input_ticker_v0588.csv",
    ], max_files=1)
    if candidates:
        return def_read_csv(candidates[0]), candidates[0], "LATEST_OPERATION_PREVIEW"

    p = cfg["canonical_dir"] / "vrn_basicinfo_active.csv"
    return def_read_csv(p), p, "CANONICAL_ACTIVE"


# ==================================================================================================
# def 06_EXTRACTION
# ==================================================================================================
def def_score_zone(zone: str) -> int:
    z = zone.lower()
    if "valuation evidence" in z:
        return 112
    if "valuation" in z:
        return 108
    if "target_price" in z or "target price" in z:
        return 94
    if "first" in z and "page" in z:
        return 88
    if "pdf_first_page" in z:
        return 86
    if "repaired" in z:
        return 84
    if "sentence" in z:
        return 78
    if "body" in z or "content" in z or "text" in z:
        return 70
    if "filename" in z:
        return 25
    return 50


def def_extract_valuation_for_row(row: dict, bank: dict, patterns: dict) -> dict:
    fn, tk = def_row_key(row)
    keys = [(fn, tk), ("", tk), (fn, "")]
    zones = []

    for z, t in def_source_zone_candidates(row):
        zones.append(("[BASE_ROW]", z, t))

    seen = set()
    for key in keys:
        for src, zone, text in bank.get(key, []):
            sig = (src, zone, text[:220])
            if sig in seen:
                continue
            seen.add(sig)
            zones.append((src, zone, text))

    matches = []

    for src, zone, text0 in zones:
        text = def_clean_text(text0)
        if not text:
            continue

        for method, pats in patterns.items():
            for pat in pats:
                try:
                    for m in re.finditer(pat, text, flags=re.MULTILINE):
                        ev = def_window(text, m.start(), m.end(), radius=380)
                        if not def_method_hard_gate(method, ev):
                            continue
                        matches.append({
                            "method": method,
                            "source": src,
                            "zone": zone,
                            "pattern": pat,
                            "evidence": ev,
                            "start": m.start(),
                            "end": m.end(),
                        })
                except Exception:
                    pass

    has_source_text = any("source text" in z.lower() for _, z, _ in zones)
    has_firstpage = any(("first" in z.lower() and "page" in z.lower()) or "pdf_first_page" in z.lower() or "repaired" in z.lower() for _, z, _ in zones)
    has_sentence = any("sentence" in z.lower() for _, z, _ in zones)

    if not matches:
        return {
            "Valuation Method": "",
            "Valuation Evidence Text": "",
            "Valuation Source File": "",
            "Valuation Source Zone": "",
            "Valuation Confidence": 0.0,
            "Valuation Rebind Decision": "NO_VALUATION_METHOD_FOUND_AFTER_SOURCEBANK",
            "Valuation Synonym Match Count": 0,
            "Valuation Source Count": len(zones),
            "Has Source Text": has_source_text,
            "Has First Page Repaired Text": has_firstpage,
            "Has Sentence Units": has_sentence,
        }

    def score(m: dict) -> int:
        ev = m["evidence"]
        s = def_score_zone(m["zone"])
        if m["source"] == "[BASE_ROW]":
            s += 3
        if re.search(r"\d+(\.\d+)?\s*(x|X|倍)", ev):
            s += 14
        if re.search(r"目標價|target price|price target|TP|PT", ev, re.I):
            s += 8
        if re.search(r"評價|valuation|value|derive|based on|基於|以|給[予與]|implying|applying", ev, re.I):
            s += 8
        if re.search(r"EPS|每股盈餘", ev, re.I):
            s += 4
        return s

    matches = sorted(matches, key=score, reverse=True)
    best = matches[0]

    methods = []
    for m in matches:
        method = m["method"]
        if method not in methods and def_method_hard_gate(method, m["evidence"]):
            methods.append(method)

    return {
        "Valuation Method": " + ".join(methods[:3]),
        "Valuation Evidence Text": best["evidence"],
        "Valuation Source File": best["source"],
        "Valuation Source Zone": best["zone"],
        "Valuation Confidence": min(0.99, round(score(best) / 145, 2)),
        "Valuation Rebind Decision": "V0595_DICTIONARY_SOURCEBANK_REPAIR",
        "Valuation Synonym Match Count": len(matches),
        "Valuation Source Count": len(zones),
        "Has Source Text": has_source_text,
        "Has First Page Repaired Text": has_firstpage,
        "Has Sentence Units": has_sentence,
    }


# ==================================================================================================
# def 07_HTML
# ==================================================================================================
def def_format_header(x: str) -> str:
    acr = {"DB", "API", "ID", "URL", "HTML", "JSON", "CSV", "SQL", "EPS", "ROE", "ROA", "TWD", "USD", "YTD", "QOQ", "YOY"}
    out = []
    for p in str(x or "").replace("_", " ").split():
        u = p.upper()
        if u in acr:
            out.append(u)
        elif re.search(r"[\u4e00-\u9fff]", p):
            out.append(p)
        else:
            out.append(p[:1].upper() + p[1:].lower())
    return " ".join(out)


def def_cell_class(col: str, val: Any) -> str:
    c = col.lower()
    if col == "Status Lights":
        return "status"
    if any(k in c for k in ["filename", "file", "path", "source", "text", "evidence", "reason", "decision", "pattern", "zone", "detail", "backup"]):
        return "left"
    if any(k in c for k in ["score", "confidence", "count", "rows", "size"]):
        return "num"
    if len(str(val or "")) > 30:
        return "left"
    return "center"


def def_band(row: dict) -> str:
    s = str(row.get("Severity") or row.get("Status") or "").upper()
    if "ERR" in s or "RED" in s:
        return "red"
    if "WARN" in s or "MISSING" in s or "YELLOW" in s:
        return "yellow"
    return "green"


def def_table(rows: list[dict], limit: int = 1400) -> str:
    if not rows:
        return "<div class='empty'>No rows.</div>"

    rows = rows[:limit]
    cols = []
    for r in rows:
        for k in r:
            if k not in cols:
                cols.append(k)

    if "Status Lights" in cols:
        cols = ["Status Lights"] + [c for c in cols if c != "Status Lights"]
    else:
        cols = ["Status Lights"] + cols

    th = "".join(f"<th>{def_h(def_format_header(c))}</th>" for c in cols)
    trs = []

    for r in rows:
        band = def_band(r)
        cells = []
        for c in cols:
            val = r.get(c, "")
            if c == "Status Lights" and not val:
                val = def_lights(r.get("Severity", "OK"))
            cls = def_cell_class(c, val)
            collapse = " collapse" if cls == "left" and len(str(val)) > 130 else ""
            cells.append(f"<td class='{cls}{collapse}'>{def_h(val)}</td>")
        trs.append(f"<tr class='{band}'>" + "".join(cells) + "</tr>")

    return "<table><thead><tr>" + th + "</tr></thead><tbody>" + "\n".join(trs) + "</tbody></table>"


def def_render_html(path: Path, result: dict, overview: list[dict], audit: list[dict], missing: list[dict], basic: list[dict], source_bank: list[dict], files: list[dict], support: list[dict]) -> None:
    cards = [
        ("System Pass", result["system_pass"]),
        ("Basic Rows", result["counts"]["basic_rows"]),
        ("Found", result["counts"]["valuation_found"]),
        ("Missing", result["counts"]["valuation_missing"]),
        ("With Source Text", result["counts"]["with_source_text"]),
        ("With FirstPage", result["counts"]["with_firstpage"]),
        ("With Sentence", result["counts"]["with_sentence_units"]),
        ("Methods", result["counts"]["dictionary_methods"]),
    ]

    card_html = "".join(f"<div class='stat'><div class='n'>{def_h(v)}</div><div class='l'>{def_h(k)}</div></div>" for k, v in cards)

    doc = f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>VRN Valuation Dictionary SourceBank Repair v05.9.5</title>
<style>
:root {{
  --bg:#f5f4f0;--sf:#fff;--sf2:#fafaf8;--bd:#dbd9d3;--bl:#4c78a8;--tl:#439a9a;--vi:#7a6daa;
  --gn:#5a9e6f;--gn-l:#cde8d5;--am:#c4943a;--am-l:#f5e2b8;--co:#c96b5a;--co-l:#f5d0c8;
  --i0:#1e1d1a;--i2:#6b6860;--i3:#9c9890;--mo:Consolas,monospace;--sa:"Segoe UI","Microsoft JhengHei",system-ui,sans-serif;
}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);font-family:var(--sa);font-size:11px;color:var(--i0)}}
.wrap{{max-width:1800px;margin:0 auto;padding:12px}}
.hdr{{background:var(--sf);border:1px solid var(--bd);border-radius:16px;padding:16px 18px;margin-bottom:10px;display:flex;gap:12px;position:relative;overflow:hidden}}
.hdr:before{{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,var(--bl),var(--tl),var(--vi),var(--am),var(--co))}}
.logo{{width:42px;height:42px;border-radius:12px;background:#1e3a5f;color:#8dcff0;display:flex;align-items:center;justify-content:center;font-weight:900;font-family:var(--mo)}}
.h1{{font-size:20px;font-weight:850}}.h1 span{{color:var(--bl)}}.sub{{font-size:10px;color:var(--i3);margin-top:2px}}
.tabs{{display:flex;gap:4px;margin-bottom:10px;flex-wrap:wrap}}
.tabs button{{border:1px solid var(--bd);background:var(--sf);border-radius:999px;padding:8px 14px;font-weight:750;font-size:11px;cursor:pointer;transition:.16s;color:var(--i2)}}
.tabs button:hover{{transform:translateY(-1px);box-shadow:0 8px 18px rgba(30,29,26,.08);border-color:var(--bl);color:var(--bl)}}
.tabs button.on{{background:var(--bl);border-color:var(--bl);color:white}}
.tabs button:active{{transform:scale(.94) translateY(1px);box-shadow:inset 0 2px 8px rgba(0,0,0,.18)}}
.page{{display:none}}.page.on{{display:block}}
.card{{background:var(--sf);border:1px solid var(--bd);border-radius:16px;margin-bottom:10px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.035)}}
.card h3{{margin:0;padding:10px 12px;background:var(--sf2);border-bottom:1px solid var(--bd);font-size:12px}}
.statgrid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:8px;margin-bottom:10px}}
.stat{{background:var(--sf);border:1px solid var(--bd);border-radius:14px;padding:10px;transition:.16s}}
.stat:hover{{transform:translateY(-2px) scale(1.01);box-shadow:0 12px 26px rgba(30,29,26,.10)}}
.stat .n{{text-align:right;font-family:var(--mo);font-size:20px;font-weight:900}}.stat .l{{text-align:center;color:var(--i3);font-size:9px;text-transform:uppercase}}
.tablewrap{{overflow:auto;max-height:76vh;border:1px solid var(--bd);border-radius:12px;resize:both;background:var(--sf)}}
table{{border-collapse:collapse;width:max-content;min-width:100%;font-size:10px;table-layout:auto}}
th{{position:sticky;top:0;z-index:2;background:#ef0000;color:#fff;padding:8px 9px;border:1px solid var(--bd);text-align:center;vertical-align:top;white-space:normal;overflow-wrap:anywhere}}
td{{padding:6px 8px;border:1px solid var(--bd);vertical-align:top;white-space:normal;overflow-wrap:anywhere;word-break:break-word;max-width:840px;line-height:1.35;text-align:center}}
td.left{{text-align:left;min-width:260px;max-width:980px}}
td.center{{text-align:center}}
td.num{{text-align:right;font-family:var(--mo);font-variant-numeric:tabular-nums;white-space:nowrap}}
td.status{{text-align:center;font-family:var(--mo);font-weight:900;white-space:nowrap;min-width:150px}}
td.collapse{{display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden}}
tr.green td{{background:linear-gradient(0deg,rgba(205,232,213,.84),rgba(255,255,255,.92))}}
tr.yellow td{{background:linear-gradient(0deg,rgba(245,226,184,.86),rgba(255,255,255,.92))}}
tr.red td{{background:linear-gradient(0deg,rgba(245,208,200,.9),rgba(255,255,255,.92))}}
pre{{background:#1e1d1a;color:#d1fae5;border-radius:10px;padding:12px;overflow:auto;white-space:pre-wrap}}
</style>
<script>
function tab(id){{
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('on'));
  document.querySelectorAll('.tabs button').forEach(b=>b.classList.remove('on'));
  document.getElementById(id).classList.add('on');
  document.getElementById('b_'+id).classList.add('on');
  try{{ if(navigator.vibrate) navigator.vibrate(18); }}catch(e){{}}
}}
</script>
</head>
<body>
<div class="wrap">
  <div class="hdr">
    <div class="logo">VRN</div>
    <div>
      <div class="h1"><span>VeritasReportNova</span> Valuation Dictionary SourceBank Repair <span style="font-size:12px;color:var(--i3)">v05.9.5</span></div>
      <div class="sub">full valuation dictionary · source text · repaired first-page · sentence units · PDF fallback · no canonical mutation</div>
    </div>
  </div>

  <div class="tabs">
    <button id="b_overview" class="on" onclick="tab('overview')">01 Overview</button>
    <button id="b_audit" onclick="tab('audit')">02 Valuation Repair</button>
    <button id="b_missing" onclick="tab('missing')">03 Missing Diagnosis</button>
    <button id="b_basic" onclick="tab('basic')">04 BasicInfo Preview</button>
    <button id="b_sourcebank" onclick="tab('sourcebank')">05 Source Bank</button>
    <button id="b_files" onclick="tab('files')">06 Related Files</button>
    <button id="b_support" onclick="tab('support')">07 Supportive</button>
    <button id="b_json" onclick="tab('json')">08 JSON</button>
  </div>

  <div id="overview" class="page on"><div class="statgrid">{card_html}</div><div class="card"><h3>Overview Matrix</h3><div class="tablewrap">{def_table(overview)}</div></div></div>
  <div id="audit" class="page"><div class="card"><h3>Valuation Repair Audit</h3><div class="tablewrap">{def_table(audit)}</div></div></div>
  <div id="missing" class="page"><div class="card"><h3>Missing Diagnosis</h3><div class="tablewrap">{def_table(missing)}</div></div></div>
  <div id="basic" class="page"><div class="card"><h3>BasicInfo Preview</h3><div class="tablewrap">{def_table(basic)}</div></div></div>
  <div id="sourcebank" class="page"><div class="card"><h3>Source Bank</h3><div class="tablewrap">{def_table(source_bank)}</div></div></div>
  <div id="files" class="page"><div class="card"><h3>Related Files</h3><div class="tablewrap">{def_table(files)}</div></div></div>
  <div id="support" class="page"><div class="card"><h3>Supportive Matrix</h3><div class="tablewrap">{def_table(support)}</div></div></div>
  <div id="json" class="page"><div class="card"><h3>JSON</h3><pre>{def_h(json.dumps(result, ensure_ascii=False, indent=2))}</pre></div></div>
</div>
</body>
</html>"""
    path.write_text(doc, encoding="utf-8")


# ==================================================================================================
# def 08_MAIN
# ==================================================================================================
def def_main() -> None:
    cfg = def_config()
    cfg["run_dir"].mkdir(parents=True, exist_ok=True)
    cfg["backup_dir"].mkdir(parents=True, exist_ok=True)
    cfg["config_dir"].mkdir(parents=True, exist_ok=True)

    valuation_dict = def_valuation_dictionary()
    patterns = def_method_patterns()
    def_write_json(cfg["out_dictionary_json"], valuation_dict)

    support_rows = def_patch_supportive(cfg, valuation_dict)

    files = def_collect_related_files(cfg)
    file_rows = def_file_matrix(files)
    bank, source_bank_rows = def_build_source_bank(files)

    base_rows, base_src, base_src_type = def_base_rows(cfg)

    audit_rows = []
    basic_out = []
    missing_rows = []

    for row in base_rows:
        r = dict(row)
        old_val = def_first(r, ["Valuation Method", "Valuation"])
        ex = def_extract_valuation_for_row(r, bank, patterns)
        found = def_nonblank(ex["Valuation Method"])

        if found:
            r["Valuation Method"] = ex["Valuation Method"]
            r["Valuation Evidence Text"] = ex["Valuation Evidence Text"]
            r["Valuation Source File"] = ex["Valuation Source File"]
            r["Valuation Source Zone"] = ex["Valuation Source Zone"]
            r["Valuation Confidence"] = ex["Valuation Confidence"]
            r["Valuation Rebind Decision"] = ex["Valuation Rebind Decision"]
            r["Valuation Synonym Match Count"] = ex["Valuation Synonym Match Count"]
            r["Valuation Source Count"] = ex["Valuation Source Count"]
            status = "FOUND"
            severity = "OK"
        else:
            r["Valuation Evidence Text"] = ""
            r["Valuation Source File"] = ""
            r["Valuation Source Zone"] = ""
            r["Valuation Confidence"] = 0
            r["Valuation Rebind Decision"] = ex["Valuation Rebind Decision"]
            r["Valuation Synonym Match Count"] = 0
            r["Valuation Source Count"] = ex["Valuation Source Count"]
            status = "MISSING"
            severity = "WARN"

        audit = {
            "Status Lights": def_lights(severity),
            "Filename": def_first(r, ["Filename", "File"]),
            "Ticker": def_first(r, ["Ticker", "Primary TW_TICKER", "Primary Tw Ticker"]),
            "Name": def_first(r, ["Name"]),
            "Old Valuation Method": old_val,
            "New Valuation Method": r.get("Valuation Method", ""),
            "Valuation Source File": r.get("Valuation Source File", ""),
            "Valuation Source Zone": r.get("Valuation Source Zone", ""),
            "Valuation Confidence": r.get("Valuation Confidence", ""),
            "Valuation Synonym Match Count": r.get("Valuation Synonym Match Count", ""),
            "Valuation Source Count": r.get("Valuation Source Count", ""),
            "Has Source Text": ex["Has Source Text"],
            "Has First Page Repaired Text": ex["Has First Page Repaired Text"],
            "Has Sentence Units": ex["Has Sentence Units"],
            "Valuation Evidence Text": r.get("Valuation Evidence Text", ""),
            "Status": status,
            "Severity": severity,
        }

        audit_rows.append(audit)
        basic_out.append(r)

        if not found:
            missing_rows.append({
                **audit,
                "Diagnosis": "Has related text but no valuation anchor." if ex["Valuation Source Count"] > 0 else "No related Source Text / first-page / sentence unit found.",
                "Next Fix": "Need M01/M02 repaired first-page source export connected."
            })

    found_count = sum(1 for r in audit_rows if r["Status"] == "FOUND")
    missing_count = sum(1 for r in audit_rows if r["Status"] == "MISSING")
    with_source_text = sum(1 for r in audit_rows if str(r["Has Source Text"]).lower() == "true")
    with_firstpage = sum(1 for r in audit_rows if str(r["Has First Page Repaired Text"]).lower() == "true")
    with_sentence = sum(1 for r in audit_rows if str(r["Has Sentence Units"]).lower() == "true")
    support_errors = sum(1 for r in support_rows if r["Severity"] == "ERR")

    # 修正 missing_rows 中 Next Fix 的保守語句，避免上方相容語句造成混淆
    for r in missing_rows:
        if int(float(str(r.get("Valuation Source Count", "0") or "0"))) > 0:
            r["Next Fix"] = "Need full-document body/table search or stronger broker-specific title/body source export."
        else:
            r["Next Fix"] = "Need M01/M02 repaired first-page source export connected."

    overview = [
        {"Status Lights": "🟢 INPUT  🟢 DB  🟢 TRUST", "Gate": "BASE_SOURCE", "Value": str(base_src), "Severity": "OK"},
        {"Status Lights": "🟢 INPUT  🟢 DB  🟢 TRUST", "Gate": "BASE_SOURCE_TYPE", "Value": base_src_type, "Severity": "OK"},
        {"Status Lights": "🟢 INPUT  🟢 DB  🟢 TRUST", "Gate": "RELATED_FILES_SCANNED", "Value": len(files), "Severity": "OK"},
        {"Status Lights": "🟢 INPUT  🟢 DB  🟢 TRUST", "Gate": "DICTIONARY_METHODS", "Value": len(valuation_dict["methods"]), "Severity": "OK"},
        {"Status Lights": "🟢 INPUT  🟢 DB  🟢 TRUST", "Gate": "VALUATION_FOUND", "Value": found_count, "Severity": "OK"},
        {"Status Lights": def_lights("WARN" if missing_count else "OK"), "Gate": "VALUATION_MISSING", "Value": missing_count, "Severity": "WARN" if missing_count else "OK"},
        {"Status Lights": "🟢 INPUT  🟢 DB  🟢 TRUST", "Gate": "WITH_SOURCE_TEXT", "Value": with_source_text, "Severity": "OK"},
        {"Status Lights": "🟢 INPUT  🟢 DB  🟢 TRUST", "Gate": "WITH_FIRSTPAGE_REPAIRED_TEXT", "Value": with_firstpage, "Severity": "OK"},
        {"Status Lights": "🟢 INPUT  🟢 DB  🟢 TRUST", "Gate": "WITH_SENTENCE_UNITS", "Value": with_sentence, "Severity": "OK"},
        {"Status Lights": def_lights("OK" if support_errors == 0 else "ERR"), "Gate": "SUPPORT_ERRORS", "Value": support_errors, "Severity": "OK" if support_errors == 0 else "ERR"},
        {"Status Lights": "🟢 INPUT  🟢 DB  🟢 TRUST", "Gate": "NO_STABLE_CANONICAL_MUTATION", "Value": True, "Severity": "OK"},
    ]

    rule_lock = {
        "version": VERSION,
        "rules": [
            "Fix v05.9.4 KeyError by using out_missing_diag_csv.",
            "Valuation dictionary includes absolute, relative, and asset-based methods.",
            "Source Text / repaired first-page / sentence units / PDF first-page are checked.",
            "PBR hard gate prevents PER evidence from becoming P/B.",
            "YFinance never overwrites broker valuation method.",
            "No stable/canonical mutation.",
        ],
    }
    def_write_json(cfg["out_rule_lock_json"], rule_lock)

    result = {
        "version": VERSION,
        "generated_at": def_now(),
        "system_pass": len(base_rows) > 0 and support_errors == 0,
        "mode": "READ_ONLY_VALUATION_DICTIONARY_SOURCEBANK_REPAIR",
        "sources": {
            "base_source": str(base_src),
            "base_source_type": base_src_type,
            "canonical_dir": str(cfg["canonical_dir"]),
            "input_dir": str(cfg["input_dir"]),
            "run_dir": str(cfg["run_dir"]),
        },
        "counts": {
            "basic_rows": len(base_rows),
            "valuation_found": found_count,
            "valuation_missing": missing_count,
            "with_source_text": with_source_text,
            "with_firstpage": with_firstpage,
            "with_sentence_units": with_sentence,
            "related_files": len(files),
            "source_bank_rows": len(source_bank_rows),
            "support_errors": support_errors,
            "dictionary_methods": len(valuation_dict["methods"]),
        },
        "outputs": {
            "html": str(cfg["out_html"]),
            "json": str(cfg["out_json"]),
            "basic_csv": str(cfg["out_basic_csv"]),
            "audit_csv": str(cfg["out_audit_csv"]),
            "source_bank_csv": str(cfg["out_source_bank_csv"]),
            "missing_diagnosis_csv": str(cfg["out_missing_diag_csv"]),
            "related_file_matrix_csv": str(cfg["out_file_matrix_csv"]),
            "support_csv": str(cfg["out_support_csv"]),
            "dictionary_json": str(cfg["out_dictionary_json"]),
            "rule_lock_json": str(cfg["out_rule_lock_json"]),
        },
    }

    def_write_csv(cfg["out_basic_csv"], basic_out)
    def_write_csv(cfg["out_audit_csv"], audit_rows)
    def_write_csv(cfg["out_source_bank_csv"], source_bank_rows)
    def_write_csv(cfg["out_missing_diag_csv"], missing_rows)
    def_write_csv(cfg["out_file_matrix_csv"], file_rows)
    def_write_csv(cfg["out_support_csv"], support_rows)
    def_write_json(cfg["out_json"], result)
    def_render_html(cfg["out_html"], result, overview, audit_rows, missing_rows, basic_out, source_bank_rows, file_rows, support_rows)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        def_main()
    except Exception:
        print(traceback.format_exc())
        raise