# -*- coding: utf-8 -*-
from __future__ import annotations

import html
import json
import math
import os
import re
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


VERSION = "VRN_NAME_SHORT_FINANCIAL_VALIDATION_V0606"
TW_STOCK_REGEX = re.compile(r"^(?!202[1-9])(?!2030)[1-9]\d{3}$")


# ==================================================================================================
# def 01_IO_UTILS
# ==================================================================================================
def def_read_csv(path: str | Path) -> pd.DataFrame:
    path = str(path or "")
    if not path or not os.path.exists(path):
        return pd.DataFrame()
    for enc in ["utf-8-sig", "utf-8", "cp950", "big5"]:
        try:
            return pd.read_csv(path, dtype=str, encoding=enc).fillna("")
        except Exception:
            pass
    return pd.read_csv(path, dtype=str).fillna("")


def def_write_csv(path: str | Path, df: pd.DataFrame) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.fillna("").astype(str).to_csv(path, index=False, encoding="utf-8-sig")


def def_write_json(path: str | Path, obj: Any) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def def_safe_parquet(path: str, df: pd.DataFrame) -> tuple[bool, str]:
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        if df is None or df.empty:
            df = pd.DataFrame({"empty_marker": []})
        df.fillna("").astype(str).to_parquet(path, index=False)
        return True, ""
    except Exception as e:
        return False, str(e)


def def_safe_duckdb(path: str, tables: dict[str, pd.DataFrame]) -> tuple[bool, str, pd.DataFrame]:
    rows = []
    try:
        import duckdb
        con = duckdb.connect(path)
        con.execute("CREATE SCHEMA IF NOT EXISTS vrn")
        for name, df in tables.items():
            if df is None or df.empty:
                df = pd.DataFrame({"empty_marker": []})
            con.register("tmp_df", df.fillna("").astype(str))
            con.execute(f"CREATE OR REPLACE TABLE vrn.{name} AS SELECT * FROM tmp_df")
            con.unregister("tmp_df")
            cnt = con.execute(f"SELECT COUNT(*) FROM vrn.{name}").fetchone()[0]
            rows.append({"Status Lights": def_status_lights("OK"), "DB View": f"vrn.{name}", "Rows": cnt, "Status": "OK", "Error": "", "Severity": "OK"})
        con.close()
        return True, "", pd.DataFrame(rows)
    except Exception as e:
        rows.append({"Status Lights": def_status_lights("ERR"), "DB View": "duckdb", "Rows": 0, "Status": "ERR", "Error": str(e), "Severity": "ERR"})
        return False, str(e), pd.DataFrame(rows)


# ==================================================================================================
# def 02_COMMON_UTILS
# ==================================================================================================
def def_status_lights(sev: str) -> str:
    s = str(sev or "").upper()
    if s in ["OK", "GREEN", "PASS"]:
        return "🟢 INPUT 🟢 DB 🟢 TRUST"
    if s in ["WARN", "YELLOW", "ORANGE", "REVIEW", "PARTIAL"]:
        return "🟢 INPUT 🟡 DB 🟡 TRUST"
    return "🔴 INPUT 🔴 DB 🔴 TRUST"


def def_band(score: float) -> str:
    try:
        s = float(score)
    except Exception:
        s = 0
    if s >= 0.88:
        return "GREEN"
    if s >= 0.78:
        return "YELLOW"
    if s >= 0.65:
        return "ORANGE"
    return "RED"


def def_clean_num(x: Any):
    if x is None:
        return None
    s = str(x).strip()
    if not s:
        return None
    s = s.replace(",", "").replace("％", "%")
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1]
    s = s.replace("%", "")
    try:
        v = float(s)
        return -v if neg else v
    except Exception:
        return None


def def_format_num(x: Any, decimals: int = 2, suffix: str = "") -> str:
    v = def_clean_num(x)
    if v is None:
        return "" if x is None else str(x)
    return f"{v:,.{decimals}f}{suffix}"


def def_first(row: dict, cols: list[str]) -> str:
    for c in cols:
        if c in row and str(row.get(c, "")).strip():
            return str(row.get(c, "")).strip()
    return ""


def def_valid_tw_ticker(t: str) -> bool:
    return bool(TW_STOCK_REGEX.match(str(t or "").strip()))


def def_ticker_from_row(row: dict) -> str:
    candidates = [
        def_first(row, ["Ticker", "ticker", "Primary TW_TICKER", "TW_TICKER"]),
        def_first(row, ["YFinance Ticker", "Yfinance Ticker"]),
        def_first(row, ["Bloomberg Ticker"]),
        def_first(row, ["Filename", "filename"]),
    ]
    for x in candidates:
        m = re.search(r"(?<!\d)([1-9]\d{3})(?!\d)", str(x or ""))
        if m:
            t = m.group(1)
            if def_valid_tw_ticker(t):
                return t
    return ""


def def_normalize_header(c: str) -> str:
    c = str(c or "").replace("_", " ").strip()
    acr = {"ID", "DB", "API", "URL", "PDF", "CSV", "JSON", "HTML", "SSOT", "TWSE", "TPEX", "MOPS", "EPS", "ROE", "ROA", "PE", "PB", "EBITDA"}
    out = []
    for p in c.split():
        up = p.upper()
        if up in acr:
            out.append(up)
        elif re.search(r"[\u4e00-\u9fff]", p):
            out.append(p)
        else:
            out.append(p[:1].upper() + p[1:].lower())
    return " ".join(out)


# ==================================================================================================
# def 03_SOURCE
# ==================================================================================================
def def_load_source(source_json: str, canonical_dir: str) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    source_json = "" if source_json == "__NONE__" else source_json
    meta = {"source_json": source_json, "source_type": ""}
    basic = pd.DataFrame()
    financial = pd.DataFrame()

    if source_json and os.path.exists(source_json):
        try:
            obj = json.loads(Path(source_json).read_text(encoding="utf-8"))
            outputs = obj.get("outputs", {})
            meta["source_type"] = obj.get("version", "OPERATION_JSON")
            basic_path = outputs.get("basic_csv") or outputs.get("basic") or ""
            financial_path = outputs.get("financial_csv") or outputs.get("financial") or ""
            if basic_path:
                basic = def_read_csv(basic_path)
            if financial_path:
                financial = def_read_csv(financial_path)
            meta["basic_source"] = basic_path
            meta["financial_source"] = financial_path
        except Exception as e:
            meta["source_error"] = str(e)

    if basic.empty:
        p = Path(canonical_dir) / "vrn_basicinfo_active.csv"
        basic = def_read_csv(p)
        meta["basic_source"] = str(p)

    if financial.empty:
        p = Path(canonical_dir) / "vrn_financial_active.csv"
        financial = def_read_csv(p)
        meta["financial_source"] = str(p)

    if not meta["source_type"]:
        meta["source_type"] = "CANONICAL_ACTIVE_FALLBACK"

    return basic.fillna(""), financial.fillna(""), meta


# ==================================================================================================
# def 04_OFFICIAL_SHORT_NAME
# ==================================================================================================
def def_fetch_json_url(url: str, timeout: int = 12):
    try:
        import requests
        r = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200:
            return r.json(), ""
        return None, f"HTTP_{r.status_code}"
    except Exception as e:
        return None, str(e)


def def_fallback_short_registry() -> dict:
    return {
        "2330": {"Short Name": "台積電", "Full Name": "台灣積體電路製造股份有限公司", "Market": "TWSE"},
        "2308": {"Short Name": "台達電", "Full Name": "台達電子工業股份有限公司", "Market": "TWSE"},
        "2317": {"Short Name": "鴻海", "Full Name": "鴻海精密工業股份有限公司", "Market": "TWSE"},
        "2382": {"Short Name": "廣達", "Full Name": "廣達電腦股份有限公司", "Market": "TWSE"},
        "3014": {"Short Name": "聯陽", "Full Name": "聯陽半導體股份有限公司", "Market": "TWSE"},
        "3017": {"Short Name": "奇鋐", "Full Name": "奇鋐科技股份有限公司", "Market": "TWSE"},
        "3231": {"Short Name": "緯創", "Full Name": "緯創資通股份有限公司", "Market": "TWSE"},
        "3653": {"Short Name": "健策", "Full Name": "健策精密工業股份有限公司", "Market": "TWSE"},
        "3661": {"Short Name": "世芯-KY", "Full Name": "世芯電子股份有限公司", "Market": "TWSE"},
        "3665": {"Short Name": "貿聯-KY", "Full Name": "貿聯控股(BizLink Holding Inc.)", "Market": "TWSE"},
        "3706": {"Short Name": "神達", "Full Name": "神達控股股份有限公司", "Market": "TWSE"},
        "6533": {"Short Name": "晶心科", "Full Name": "晶心科技股份有限公司", "Market": "TWSE"},
        "6669": {"Short Name": "緯穎", "Full Name": "緯穎科技服務股份有限公司", "Market": "TWSE"},
        "6768": {"Short Name": "志強-KY", "Full Name": "志強國際企業股份有限公司", "Market": "TWSE"},
        "6873": {"Short Name": "泓德能源", "Full Name": "泓德能源科技股份有限公司", "Market": "TWSE"},
        "6933": {"Short Name": "AMAX-KY", "Full Name": "艾瑪斯科技控股股份有限公司", "Market": "TWSE"},
        "8210": {"Short Name": "勤誠", "Full Name": "勤誠興業股份有限公司", "Market": "TWSE"},
        "2606": {"Short Name": "裕民", "Full Name": "裕民航運股份有限公司", "Market": "TWSE"},
        "2637": {"Short Name": "慧洋-KY", "Full Name": "慧洋海運股份有限公司", "Market": "TWSE"},
        "4171": {"Short Name": "瑞基", "Full Name": "瑞基海洋生物科技股份有限公司", "Market": "TPEX"},
        "6143": {"Short Name": "振曜", "Full Name": "振曜科技股份有限公司", "Market": "TPEX"},
    }


def def_clean_short_name(name: str) -> str:
    s = str(name or "").strip()
    s = re.sub(r"\(.*?\)", "", s).strip()
    remove_terms = [
        "股份有限公司", "科技股份有限公司", "控股股份有限公司", "國際企業股份有限公司",
        "精密工業股份有限公司", "電子工業股份有限公司", "電腦股份有限公司",
        "資通股份有限公司", "興業股份有限公司", "航運股份有限公司",
        "半導體股份有限公司", "有限公司", "公司"
    ]
    for term in remove_terms:
        if s.endswith(term):
            s = s[: -len(term)]
            break
    s = s.strip(" -_　")
    return s


def def_filename_short_name(filename: str, ticker: str) -> str:
    fn = Path(str(filename or "")).name
    patterns = [
        rf"([\u4e00-\u9fffA-Za-z0-9\-]+)\({ticker}",
        rf"{ticker}[-_ ]*([\u4e00-\u9fffA-Za-z0-9\-]+)",
        rf"[-_ ]([\u4e00-\u9fffA-Za-z0-9\-]+)[-_ ]*{ticker}",
    ]
    for p in patterns:
        m = re.search(p, fn)
        if m:
            raw = m.group(1)
            raw = re.sub(r"^(個股報告|訪談速報|投顧|證期研究部|華南投顧|兆豐|國泰|CTBC)+", "", raw)
            raw = raw.strip("-_ ，,()（）")
            if raw and len(raw) <= 20:
                return raw
    return ""


def def_official_registry() -> tuple[dict, pd.DataFrame]:
    reg = {}
    logs = []

    endpoints = [
        ("TWSE", "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_AVG_ALL"),
        ("TWSE", "https://openapi.twse.com.tw/v1/opendata/t187ap03_L"),
        ("TPEX", "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_quotes"),
        ("TPEX", "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O"),
    ]

    code_keys = ["公司代號", "證券代號", "Code", "StockNo", "stock_no", "SecuritiesCompanyCode"]
    short_keys = ["公司簡稱", "證券名稱", "Name", "StockName", "stock_name", "CompanyName", "公司名稱"]
    full_keys = ["公司名稱", "FullName", "CompanyFullName"]

    for market, url in endpoints:
        data, err = def_fetch_json_url(url)
        added = 0

        if isinstance(data, list):
            for item in data:
                if not isinstance(item, dict):
                    continue

                code = ""
                for k in code_keys:
                    if k in item and str(item.get(k, "")).strip():
                        code = str(item.get(k, "")).strip()
                        break
                if not code:
                    for v in item.values():
                        m = re.search(r"(?<!\d)([1-9]\d{3})(?!\d)", str(v))
                        if m and def_valid_tw_ticker(m.group(1)):
                            code = m.group(1)
                            break

                if not def_valid_tw_ticker(code):
                    continue

                short = ""
                full = ""
                for k in short_keys:
                    if k in item and str(item.get(k, "")).strip():
                        short = str(item.get(k, "")).strip()
                        break
                for k in full_keys:
                    if k in item and str(item.get(k, "")).strip():
                        full = str(item.get(k, "")).strip()
                        break

                if code not in reg:
                    reg[code] = {"Short Name": def_clean_short_name(short), "Full Name": full or short, "Market": market, "Source": url}
                    added += 1

        logs.append({
            "Status Lights": def_status_lights("OK" if added else "WARN"),
            "Market": market,
            "Endpoint": url,
            "Rows Added": added,
            "Error": err,
            "Severity": "OK" if added else "WARN",
        })

    for k, v in def_fallback_short_registry().items():
        reg.setdefault(k, {**v, "Source": "FALLBACK_REGISTRY"})
        if not reg[k].get("Short Name"):
            reg[k]["Short Name"] = v.get("Short Name", "")
        if not reg[k].get("Full Name"):
            reg[k]["Full Name"] = v.get("Full Name", "")
        if not reg[k].get("Market"):
            reg[k]["Market"] = v.get("Market", "")

    return reg, pd.DataFrame(logs).fillna("")


def def_rebind_basic_names(basic: pd.DataFrame, official: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    review = []

    for _, rr in basic.iterrows():
        r = dict(rr)
        ticker = def_ticker_from_row(r)
        filename = def_first(r, ["Filename", "filename"])
        company_gate = str(def_first(r, ["Company Report Gate", "Final Gate Company Report"])).lower()

        old_name = def_first(r, ["Name"])
        official_meta = official.get(ticker, {})
        official_short = official_meta.get("Short Name", "")
        official_full = official_meta.get("Full Name", "")
        filename_short = def_filename_short_name(filename, ticker) if ticker else ""

        if not def_valid_tw_ticker(ticker):
            if company_gate in ["false", "0"]:
                sev = "OK"
                missing = ""
                status = "SKIP_NON_COMPANY_OR_NO_VALID_TICKER"
            else:
                sev = "WARN"
                missing = "Ticker"
                status = "INVALID_OR_MISSING_TICKER"
            r["Status Lights"] = def_status_lights(sev)
            r["Name Rebind Status"] = status
            r["Data Completion Missing"] = missing
            r["Data Completion Severity"] = sev
            rows.append(r)
            if sev != "OK":
                review.append({
                    "Status Lights": def_status_lights(sev),
                    "Filename": filename,
                    "Ticker": ticker,
                    "Old Name": old_name,
                    "New Name": "",
                    "Issue": missing,
                    "Severity": sev,
                })
            continue

        short = official_short or filename_short or def_clean_short_name(old_name)
        full = official_full or old_name

        r["Ticker"] = ticker
        r["Company Full Name"] = full
        r["Name"] = short
        r["TW Official Short Name"] = official_short
        r["TW Official Full Name"] = official_full
        r["Name Source"] = "OFFICIAL_SHORT_NAME" if official_short else ("FILENAME_SHORT_NAME" if filename_short else "CLEANED_EXISTING_NAME")
        r["Name Trust Score"] = "0.99" if official_short else ("0.92" if filename_short else "0.86")
        r["Name Trust Band"] = def_band(float(r["Name Trust Score"]))
        r["Name Rebind Status"] = "OK"

        missing = []
        if not short:
            missing.append("Name")
        if not def_first(r, ["YFinance Ticker", "Yfinance Ticker"]):
            missing.append("YFinance Ticker")

        sev = "OK" if not missing else "WARN"
        r["Status Lights"] = def_status_lights(sev)
        r["Data Completion Missing"] = " | ".join(missing)
        r["Data Completion Severity"] = sev

        if missing:
            review.append({
                "Status Lights": def_status_lights(sev),
                "Filename": filename,
                "Ticker": ticker,
                "Old Name": old_name,
                "New Name": short,
                "Issue": " | ".join(missing),
                "Severity": sev,
            })

        rows.append(r)

    return pd.DataFrame(rows).fillna(""), pd.DataFrame(review).fillna("")


# ==================================================================================================
# def 05_FINANCIAL_VALIDATION
# ==================================================================================================
def def_canonical_key(row: dict) -> str:
    return def_first(row, ["Data Official EN", "Category Official En", "Canonical Data", "Data", "Data Raw"])


def def_val(row: dict):
    return def_clean_num(def_first(row, ["Value Numeric", "Value", "Value Raw"]))


def def_year(row: dict):
    y = def_first(row, ["Year"])
    if re.match(r"^\d{4}$", y):
        return int(y)
    return None


def def_row_scope(row: dict) -> tuple:
    return (
        def_first(row, ["Filename"]),
        def_first(row, ["Ticker"]),
        def_first(row, ["Category", "Category Official En"]),
    )


def def_build_value_map(df: pd.DataFrame) -> dict:
    mp = {}
    for idx, rr in df.iterrows():
        r = dict(rr)
        fn = def_first(r, ["Filename"])
        ticker = def_ticker_from_row(r)
        y = def_year(r)
        key = str(def_canonical_key(r)).strip().lower()
        v = def_val(r)
        if fn and ticker and y and key and v is not None:
            mp[(fn, ticker, y, key)] = v
    return mp


def def_get(mp: dict, fn: str, ticker: str, y: int, names: list[str]):
    for n in names:
        k = (fn, ticker, y, n.lower())
        if k in mp:
            return mp[k]
    return None


def def_close(a, b, tol_ratio=0.035, tol_abs=5.0) -> bool:
    if a is None or b is None:
        return False
    return abs(a - b) <= max(tol_abs, abs(b) * tol_ratio)


def def_validation_historical(df: pd.DataFrame) -> dict:
    out = {}
    groups = {}

    for idx, rr in df.iterrows():
        r = dict(rr)
        fn = def_first(r, ["Filename"])
        ticker = def_ticker_from_row(r)
        key = str(def_canonical_key(r)).strip().lower()
        y = def_year(r)
        v = def_val(r)
        if fn and ticker and key and y and v is not None:
            groups.setdefault((fn, ticker, key), []).append((y, v, idx))

    for _, arr in groups.items():
        arr = sorted(arr)
        prev = None
        for y, v, idx in arr:
            if prev is None or prev[1] in [0, None]:
                out[idx] = (0.72, "NO_PREVIOUS_YEAR_CONTEXT_LIMITED")
            else:
                yoy = abs((v - prev[1]) / prev[1]) if prev[1] != 0 else 999
                if yoy <= 2.0:
                    out[idx] = (0.94, f"HISTORICAL_OK_YOY={yoy*100:.2f}%")
                elif yoy <= 5.0:
                    out[idx] = (0.78, f"HISTORICAL_MEDIUM_YOY={yoy*100:.2f}%")
                else:
                    out[idx] = (0.58, f"HISTORICAL_REVIEW_EXTREME_YOY={yoy*100:.2f}%")
            prev = (y, v, idx)
    return out


def def_validation_addsub(df: pd.DataFrame, mp: dict) -> dict:
    out = {idx: (0.72, "NO_ADD_SUB_FORMULA_APPLICABLE") for idx in df.index}

    formula_sets = [
        {
            "target": ["total assets", "assets", "資產總計"],
            "parts": [["total liabilities", "liabilities", "負債總計"], ["total equity", "equity", "權益總計", "股東權益"]],
            "name": "BS_ASSETS_EQ_LIAB_PLUS_EQUITY"
        },
        {
            "target": ["gross profit", "gross margin amount", "毛利"],
            "parts": [["revenue", "sales", "營收", "營業收入"], ["cost of goods sold", "cogs", "營業成本"]],
            "op": "minus",
            "name": "IS_GROSS_PROFIT_EQ_REVENUE_MINUS_COGS"
        },
        {
            "target": ["ending cash", "cash and cash equivalents ending", "期末現金"],
            "parts": [["beginning cash", "期初現金"], ["net change in cash", "淨現金流量", "現金淨增加"]],
            "name": "CF_ENDING_CASH_EQ_BEGINNING_PLUS_NET_CHANGE"
        },
    ]

    row_lookup = {}
    for idx, rr in df.iterrows():
        r = dict(rr)
        fn = def_first(r, ["Filename"])
        ticker = def_ticker_from_row(r)
        y = def_year(r)
        key = str(def_canonical_key(r)).strip().lower()
        if fn and ticker and y and key:
            row_lookup.setdefault((fn, ticker, y), []).append((key, idx))

    for (fn, ticker, y), items in row_lookup.items():
        for fs in formula_sets:
            target = def_get(mp, fn, ticker, y, fs["target"])
            if target is None:
                continue

            p1 = def_get(mp, fn, ticker, y, fs["parts"][0])
            p2 = def_get(mp, fn, ticker, y, fs["parts"][1])
            if p1 is None or p2 is None:
                continue

            expected = p1 - p2 if fs.get("op") == "minus" else p1 + p2
            ok = def_close(target, expected)

            for key, idx in items:
                if key in [x.lower() for x in fs["target"] + fs["parts"][0] + fs["parts"][1]]:
                    out[idx] = (0.94, f"{fs['name']}_PASS expected={expected:.2f}") if ok else (0.55, f"{fs['name']}_REVIEW expected={expected:.2f} actual={target:.2f}")
    return out


def def_validation_division(df: pd.DataFrame, mp: dict) -> dict:
    out = {idx: (0.72, "NO_DIVISION_FORMULA_APPLICABLE") for idx in df.index}

    ratio_sets = [
        {"ratio": ["gross margin", "毛利率"], "num": ["gross profit", "毛利"], "den": ["revenue", "sales", "營收", "營業收入"], "name": "GROSS_MARGIN"},
        {"ratio": ["operating margin", "營業利益率", "營益率"], "num": ["operating income", "營業利益"], "den": ["revenue", "sales", "營收", "營業收入"], "name": "OPERATING_MARGIN"},
        {"ratio": ["net margin", "淨利率"], "num": ["net income", "淨利"], "den": ["revenue", "sales", "營收", "營業收入"], "name": "NET_MARGIN"},
        {"ratio": ["current ratio", "流動比率"], "num": ["current assets", "流動資產"], "den": ["current liabilities", "流動負債"], "name": "CURRENT_RATIO"},
        {"ratio": ["roe", "return on equity", "股東權益報酬率"], "num": ["net income", "淨利"], "den": ["total equity", "equity", "權益總計"], "name": "ROE"},
    ]

    row_lookup = {}
    for idx, rr in df.iterrows():
        r = dict(rr)
        fn = def_first(r, ["Filename"])
        ticker = def_ticker_from_row(r)
        y = def_year(r)
        key = str(def_canonical_key(r)).strip().lower()
        if fn and ticker and y and key:
            row_lookup.setdefault((fn, ticker, y), []).append((key, idx, r))

    for (fn, ticker, y), items in row_lookup.items():
        for rs in ratio_sets:
            ratio_value = def_get(mp, fn, ticker, y, rs["ratio"])
            num = def_get(mp, fn, ticker, y, rs["num"])
            den = def_get(mp, fn, ticker, y, rs["den"])
            if ratio_value is None or num is None or den in [None, 0]:
                continue

            expected = num / den * 100
            ok = abs(ratio_value - expected) <= max(1.0, abs(expected) * 0.12)

            for key, idx, r in items:
                if key in [x.lower() for x in rs["ratio"]]:
                    out[idx] = (0.93, f"{rs['name']}_PASS expected={expected:.2f}%") if ok else (0.58, f"{rs['name']}_REVIEW expected={expected:.2f}% actual={ratio_value:.2f}%")
    return out


def def_external_basic_map(basic: pd.DataFrame) -> dict:
    mp = {}
    for _, rr in basic.iterrows():
        r = dict(rr)
        t = def_ticker_from_row(r)
        if not t:
            continue
        mp[t] = {
            "YFinance Ticker": def_first(r, ["YFinance Ticker", "Yfinance Ticker"]),
            "YFinance Last Adj Close": def_first(r, ["YFinance Last Adj Close", "Last Adj Close"]),
            "YFinance Last Volume": def_first(r, ["YFinance Last Volume"]),
            "YFinance Beta": def_first(r, ["YFinance Beta"]),
        }
    return mp


def def_apply_financial_validation(fin: pd.DataFrame, basic: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if fin is None or fin.empty:
        return pd.DataFrame(), pd.DataFrame()

    df = fin.copy().fillna("")
    mp = def_build_value_map(df)
    hist = def_validation_historical(df)
    addsub = def_validation_addsub(df, mp)
    div = def_validation_division(df, mp)
    bmap = def_external_basic_map(basic)

    rows = []
    review = []

    for idx, rr in df.iterrows():
        r = dict(rr)
        ticker = def_ticker_from_row(r)

        hs, hc = hist.get(idx, (0.70, "NO_HISTORICAL_CONTEXT"))
        as_, ac = addsub.get(idx, (0.72, "NO_ADD_SUB_FORMULA_APPLICABLE"))
        ds, dc = div.get(idx, (0.72, "NO_DIVISION_FORMULA_APPLICABLE"))

        ext = bmap.get(ticker, {})
        if ext.get("YFinance Ticker") and ext.get("YFinance Last Adj Close"):
            es, ec = 0.82, "YFINANCE_PRICE_VOLUME_CONTEXT_OK"
        elif ext.get("YFinance Ticker"):
            es, ec = 0.74, "YFINANCE_TICKER_ONLY"
        else:
            es, ec = 0.68, "EXTERNAL_CONTEXT_LIMITED"

        name_score = def_clean_num(def_first(r, ["Name Trust Score"])) or 0.90
        year_score = def_clean_num(def_first(r, ["Year Trust Score"])) or 0.90
        unit_score = def_clean_num(def_first(r, ["Unit Trust Score"])) or 0.88

        final = (
            float(name_score) * 0.12 +
            float(year_score) * 0.12 +
            float(unit_score) * 0.14 +
            hs * 0.22 +
            as_ * 0.18 +
            ds * 0.16 +
            es * 0.06
        )

        band = def_band(final)
        sev = "OK" if band in ["GREEN", "YELLOW"] else ("WARN" if band == "ORANGE" else "ERR")

        r["Ticker"] = ticker
        r["Historical Data Confidence"] = f"{hs:.2f}"
        r["Historical Data Check"] = hc
        r["Add/Sub Check Confidence"] = f"{as_:.2f}"
        r["Add/Sub Check"] = ac
        r["Division Check Confidence"] = f"{ds:.2f}"
        r["Division Check"] = dc
        r["External Trust Score"] = f"{es:.2f}"
        r["External Trust Reason"] = ec
        r["Final Trust Confidence"] = f"{final:.4f}"
        r["Final Trust Band"] = band
        r["Financial Validation Traffic"] = def_status_lights(sev)
        r["Data Quality Gate"] = "KEEP" if sev != "ERR" else "REVIEW"
        r["Value Display"] = def_format_num(def_first(r, ["Value Numeric", "Value", "Value Raw"]))
        r["Validation Version"] = VERSION

        if ext:
            for k, v in ext.items():
                if k not in r or not str(r.get(k, "")).strip():
                    r[k] = v

        if sev != "OK":
            review.append({
                "Status Lights": def_status_lights(sev),
                "Filename": def_first(r, ["Filename"]),
                "Ticker": ticker,
                "Name": def_first(r, ["Name"]),
                "Category": def_first(r, ["Category", "Category Official En"]),
                "Year": def_first(r, ["Year"]),
                "Data": def_first(r, ["Canonical Data", "Data Official EN", "Data"]),
                "Value": def_first(r, ["Value", "Value Numeric"]),
                "Historical Check": hc,
                "Add/Sub Check": ac,
                "Division Check": dc,
                "External Check": ec,
                "Final Trust Confidence": f"{final:.4f}",
                "Final Trust Band": band,
                "Severity": sev,
            })

        rows.append(r)

    return pd.DataFrame(rows).fillna(""), pd.DataFrame(review).fillna("")


# ==================================================================================================
# def 06_HTML
# ==================================================================================================
def def_table_html(title: str, df: pd.DataFrame, max_rows: int = 1200) -> str:
    if df is None or df.empty:
        return f"<section class='card'><h2>{html.escape(title)}</h2><div class='empty'>No rows.</div></section>"
    d = df.head(max_rows).copy()
    cols = list(d.columns)
    th = "".join(f"<th>{html.escape(def_normalize_header(c))}</th>" for c in cols)
    trs = []
    for _, r in d.iterrows():
        tds = []
        for c in cols:
            v = "" if pd.isna(r.get(c, "")) else str(r.get(c, ""))
            lc = c.lower()
            cls = "left" if any(k in lc for k in ["filename", "path", "source", "reason", "check", "error", "missing"]) else "center"
            cls = "right" if any(k in lc for k in ["value", "score", "confidence", "price", "volume", "rows", "count", "beta"]) else cls
            tds.append(f"<td class='{cls}'>{html.escape(v)}</td>")
        trs.append("<tr>" + "".join(tds) + "</tr>")
    return f"<section class='card'><h2>{html.escape(title)}</h2><div class='table-wrap'><table><thead><tr>{th}</tr></thead><tbody>{''.join(trs)}</tbody></table></div></section>"


def def_write_html(path: str, result: dict, sections: list[tuple[str, pd.DataFrame]]) -> None:
    css = """
:root{--bg:#07111f;--panel:#0d1b2f;--line:#1f3557;--text:#eef6ff;--muted:#9fb3c8;--green:#25d366;--yellow:#f5c542;--red:#ff4d5e;--cyan:#42d9ff}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at top,#142a45,#07111f 52%,#050914);font-family:Segoe UI,'Microsoft JhengHei',Arial,sans-serif;color:var(--text);font-size:12px}
header{padding:24px 32px;border-bottom:1px solid var(--line);position:sticky;top:0;background:rgba(7,17,31,.92);backdrop-filter:blur(12px);z-index:10}
h1{margin:0;font-size:24px}.sub{margin-top:8px;color:var(--muted)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px;padding:20px 32px}
.kpi{background:linear-gradient(180deg,rgba(66,217,255,.12),rgba(13,27,47,.92));border:1px solid var(--line);border-radius:18px;padding:16px;box-shadow:0 12px 28px rgba(0,0,0,.25);transition:.15s}
.kpi:hover{transform:translateY(-2px);border-color:var(--cyan)}.kpi .v{font-size:26px;font-weight:850}.kpi .k{color:var(--muted);margin-top:6px}
main{padding:0 32px 32px}.card{background:rgba(13,27,47,.92);border:1px solid var(--line);border-radius:18px;margin:18px 0;padding:18px}
h2{margin:0 0 12px}.table-wrap{overflow:auto;max-height:75vh;border:1px solid var(--line);border-radius:14px}
table{border-collapse:collapse;min-width:100%;width:max-content}th{position:sticky;top:0;background:#132541;color:#fff;text-align:center;vertical-align:top;padding:10px;border-bottom:1px solid var(--line);white-space:normal}
td{padding:8px 10px;border-bottom:1px solid rgba(255,255,255,.08);border-right:1px solid rgba(255,255,255,.05);vertical-align:top;text-align:center;max-width:420px;white-space:normal;word-break:break-word}
td.left{text-align:left}td.right{text-align:right;font-variant-numeric:tabular-nums}tr:hover td{background:rgba(66,217,255,.07)}.empty{color:var(--muted);padding:18px}
footer{padding:18px 32px;color:var(--muted);border-top:1px solid var(--line)}
"""
    cards = result.get("counts", {})
    card_html = "<div class='grid'>" + "".join([f"<div class='kpi'><div class='v'>{html.escape(str(v))}</div><div class='k'>{html.escape(str(k))}</div></div>" for k, v in cards.items()]) + "</div>"
    sec_html = "\n".join(def_table_html(t, d) for t, d in sections)
    doc = f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><title>VRN Name Short Financial Validation v0.6.6</title><style>{css}</style></head>
<body><header><h1>VRN · Name Short + Financial Data Validation Seal v0.6.6</h1>
<div class="sub">official short name · historical check · add/sub check · division check · external trust · no canonical mutation</div></header>
{card_html}<main>{sec_html}</main><footer>Veritas Intelligence Analytics │ AI-Augmented Investment Intelligence for Smarter Decisions and Deeper Insight</footer></body></html>"""
    Path(path).write_text(doc, encoding="utf-8")


# ==================================================================================================
# def 07_MAIN
# ==================================================================================================
def def_main():
    if len(sys.argv) < 6:
        raise SystemExit(f"usage error argc={len(sys.argv)} argv={sys.argv}")

    source_json = sys.argv[1]
    canonical_dir = sys.argv[2]
    run_dir = sys.argv[3]
    publish_canonical = str(sys.argv[4]).lower() == "true"
    config_dir = sys.argv[5]

    Path(run_dir).mkdir(parents=True, exist_ok=True)
    Path(config_dir).mkdir(parents=True, exist_ok=True)

    basic, financial, meta = def_load_source(source_json, canonical_dir)
    official, official_log = def_official_registry()

    basic2, name_review = def_rebind_basic_names(basic, official)
    financial2, validation_review = def_apply_financial_validation(financial, basic2)

    green = int((financial2.get("Final Trust Band", pd.Series(dtype=str)).astype(str) == "GREEN").sum()) if not financial2.empty else 0
    yellow = int((financial2.get("Final Trust Band", pd.Series(dtype=str)).astype(str) == "YELLOW").sum()) if not financial2.empty else 0
    orange = int((financial2.get("Final Trust Band", pd.Series(dtype=str)).astype(str) == "ORANGE").sum()) if not financial2.empty else 0
    red = int((financial2.get("Final Trust Band", pd.Series(dtype=str)).astype(str) == "RED").sum()) if not financial2.empty else 0

    overview = pd.DataFrame([
        {"Status Lights": def_status_lights("OK"), "Gate": "SOURCE_TYPE", "Value": meta.get("source_type", ""), "Severity": "OK"},
        {"Status Lights": def_status_lights("OK"), "Gate": "BASIC_ROWS", "Value": len(basic2), "Severity": "OK"},
        {"Status Lights": def_status_lights("OK"), "Gate": "FINANCIAL_ROWS", "Value": len(financial2), "Severity": "OK"},
        {"Status Lights": def_status_lights("OK" if len(name_review) == 0 else "WARN"), "Gate": "NAME_REVIEW_ROWS", "Value": len(name_review), "Severity": "OK" if len(name_review) == 0 else "WARN"},
        {"Status Lights": def_status_lights("OK" if red == 0 else "ERR"), "Gate": "FINANCIAL_VALIDATION_RED", "Value": red, "Severity": "OK" if red == 0 else "ERR"},
        {"Status Lights": def_status_lights("OK"), "Gate": "FINANCIAL_GREEN", "Value": green, "Severity": "OK"},
        {"Status Lights": def_status_lights("WARN" if yellow else "OK"), "Gate": "FINANCIAL_YELLOW", "Value": yellow, "Severity": "WARN" if yellow else "OK"},
        {"Status Lights": def_status_lights("WARN" if orange else "OK"), "Gate": "FINANCIAL_ORANGE", "Value": orange, "Severity": "WARN" if orange else "OK"},
        {"Status Lights": def_status_lights("OK"), "Gate": "NO_BROKER_RATING_TARGET_OVERWRITE", "Value": True, "Severity": "OK"},
        {"Status Lights": def_status_lights("OK"), "Gate": "NO_CANONICAL_MUTATION", "Value": not publish_canonical, "Severity": "OK"},
    ])

    out_basic = str(Path(run_dir) / "vrn_basicinfo_name_short_v0606.csv")
    out_financial = str(Path(run_dir) / "vrn_financial_validated_v0606.csv")
    out_name_review = str(Path(run_dir) / "vrn_name_short_review_v0606.csv")
    out_validation_review = str(Path(run_dir) / "vrn_financial_validation_review_v0606.csv")
    out_official = str(Path(run_dir) / "vrn_official_name_fetch_matrix_v0606.csv")
    out_overview = str(Path(run_dir) / "vrn_overview_matrix_v0606.csv")
    out_html = str(Path(run_dir) / "VRN_Name_Short_Financial_Validation_v0606.html")
    out_json = str(Path(run_dir) / "vrn_name_short_financial_validation_v0606.json")
    out_duckdb = str(Path(run_dir) / "vrn_name_short_financial_validation_v0606.duckdb")
    rule_lock = str(Path(config_dir) / "VRN_Name_Short_Financial_Validation_RuleLock_v0606.json")

    for p, d in [
        (out_basic, basic2),
        (out_financial, financial2),
        (out_name_review, name_review),
        (out_validation_review, validation_review),
        (out_official, official_log),
        (out_overview, overview),
    ]:
        def_write_csv(p, d)

    parquet_ok = True
    parquet_errors = {}
    for name, p, d in [
        ("basic", out_basic, basic2),
        ("financial", out_financial, financial2),
        ("name_review", out_name_review, name_review),
        ("validation_review", out_validation_review, validation_review),
    ]:
        ok, err = def_safe_parquet(str(Path(p).with_suffix(".parquet")), d)
        parquet_ok = parquet_ok and ok
        parquet_errors[name] = err

    duckdb_ok, duckdb_error, duckdb_matrix = def_safe_duckdb(out_duckdb, {
        "basicinfo_name_short_v0606": basic2,
        "financial_validated_v0606": financial2,
        "name_short_review_v0606": name_review,
        "financial_validation_review_v0606": validation_review,
        "official_name_fetch_matrix_v0606": official_log,
        "overview_matrix_v0606": overview,
    })

    system_pass = bool(parquet_ok and duckdb_ok and len(financial2) > 0 and red == 0)

    result = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "system_pass": system_pass,
        "source": meta,
        "counts": {
            "System Pass": system_pass,
            "Basic Rows": len(basic2),
            "Financial Rows": len(financial2),
            "Name Review": len(name_review),
            "Validation Review": len(validation_review),
            "Green": green,
            "Yellow": yellow,
            "Orange": orange,
            "Red": red,
            "Parquet OK": parquet_ok,
            "DuckDB OK": duckdb_ok,
        },
        "policy": {
            "name_output": "company short name",
            "company_full_name_preserved": True,
            "tw_stock_regex": r"^(?!202[1-9])(?!2030)[1-9]\d{3}$",
            "financial_validation_methods": [
                "historical trend check",
                "add/sub formula check",
                "division ratio check",
                "yfinance market data context",
                "final weighted trust score"
            ],
            "broker_protected_fields": ["Rating", "Target Price", "Analyst", "Report Date"],
            "canonical_mutation": publish_canonical,
            "no_fake_fill": True
        },
        "parquet_ok": parquet_ok,
        "parquet_errors": parquet_errors,
        "duckdb_ok": duckdb_ok,
        "duckdb_error": duckdb_error,
        "outputs": {
            "html": out_html,
            "json": out_json,
            "basic_csv": out_basic,
            "financial_csv": out_financial,
            "name_review_csv": out_name_review,
            "financial_validation_review_csv": out_validation_review,
            "official_name_fetch_csv": out_official,
            "overview_csv": out_overview,
            "duckdb": out_duckdb,
            "rule_lock_json": rule_lock,
        }
    }

    def_write_json(out_json, result)
    def_write_json(rule_lock, {
        "version": VERSION,
        "rules": [
            "Name column uses official company short name; Company Full Name preserves full legal name.",
            "TW_STOCK_REGEX excludes year-like 2021-2030 values.",
            "Financial data validation includes historical, add/sub, division, and external market-data context.",
            "YFinance data is reference only and does not overwrite broker Rating / Target Price.",
            "No canonical mutation by default.",
            "No fake fill."
        ]
    })

    def_write_html(out_html, result, [
        ("01 Overview", overview),
        ("02 BasicInfo Name Short", basic2),
        ("03 Financial Validated", financial2),
        ("04 Financial Validation Review", validation_review),
        ("05 Name Review", name_review),
        ("06 Official Name Fetch", official_log),
        ("07 DuckDB Views", duckdb_matrix),
    ])

    if publish_canonical and system_pass:
        cdir = Path(canonical_dir)
        cdir.mkdir(parents=True, exist_ok=True)
        def_write_csv(cdir / "vrn_basicinfo_name_short_active_v0606.csv", basic2)
        def_write_csv(cdir / "vrn_financial_validated_active_v0606.csv", financial2)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        def_main()
    except Exception:
        print(traceback.format_exc())
        raise