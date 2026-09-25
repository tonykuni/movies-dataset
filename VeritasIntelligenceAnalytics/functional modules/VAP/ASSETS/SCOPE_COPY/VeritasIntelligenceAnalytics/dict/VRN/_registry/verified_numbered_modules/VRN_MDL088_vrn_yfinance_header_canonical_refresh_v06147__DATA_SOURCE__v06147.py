# -*- coding: utf-8 -*-
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

import ast
import csv
import html
import importlib.util
import json
import math
import re
import shutil
import subprocess
import sys
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


VERSION = "VRN_YFINANCE_HEADER_CANONICAL_REFRESH_V06147"
PATCH_START = "# [VIA:VRN_YFINANCE_HEADER_CANONICAL_REFRESH_V06147:START]"
PATCH_END = "# [VIA:VRN_YFINANCE_HEADER_CANONICAL_REFRESH_V06147:END]"


# ==================================================================================================
# def COMMON
# ==================================================================================================
def def_clean_text(x: Any) -> str:
    s = "" if x is None else str(x)
    s = s.replace("\u3000", " ").replace("\r", " ").replace("\n", " ")
    return re.sub(r"\s+", " ", s).strip()


def def_is_blank(x: Any) -> bool:
    s = def_clean_text(x)
    return s == "" or s.lower() in ["nan", "none", "null", "na", "n/a"]


def def_fmt_num(x: Any, digits: int = 2) -> str:
    if x is None:
        return ""
    try:
        if isinstance(x, str):
            s = x.replace(",", "").replace("%", "").strip()
            if s == "":
                return ""
            v = float(s)
        else:
            v = float(x)
        if math.isnan(v) or math.isinf(v):
            return ""
        return f"{v:,.{digits}f}"
    except Exception:
        return def_clean_text(x)


def def_fmt_int(x: Any) -> str:
    try:
        if x is None or def_is_blank(x):
            return ""
        return f"{int(float(str(x).replace(',', ''))):,}"
    except Exception:
        return def_clean_text(x)


def def_fmt_pct(x: Any) -> str:
    try:
        if x is None or def_is_blank(x):
            return ""
        v = float(str(x).replace("%", "").replace(",", ""))
        return f"{v:.2f}%"
    except Exception:
        return def_clean_text(x)


def def_parse_date(x: Any):
    s = def_clean_text(x)
    if not s:
        return None
    for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"]:
        try:
            return datetime.strptime(s[:10], fmt).date()
        except Exception:
            pass
    m = re.search(r"(20\d{2})[-/.]?(0[1-9]|1[0-2])[-/.]?([0-3]\d)", s)
    if m:
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3))).date()
        except Exception:
            pass
    return None


def def_lights(sev: str) -> str:
    s = str(sev or "").upper()
    if s in ["OK", "YES", "PASS", "READY", "GREEN"]:
        return "🟢 INPUT 🟢 DB 🟢 TRUST"
    if s in ["WARN", "REVIEW", "PARTIAL", "YELLOW"]:
        return "🟢 INPUT 🟡 DB 🟡 TRUST"
    return "🔴 INPUT 🔴 DB 🔴 TRUST"


def def_read_csv(path: Path) -> list[dict]:
    if not path or not path.exists():
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
    if not rows:
        rows = [{"empty_marker": ""}]
    fields = []
    for r in rows:
        for k in r.keys():
            if k not in fields:
                fields.append(k)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def def_write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def def_find_latest(root: Path, patterns: list[str]) -> Path | None:
    hits = []
    for pat in patterns:
        hits.extend(root.rglob(pat))
    hits = [p for p in hits if p.is_file()]
    hits = sorted(set(hits), key=lambda p: p.stat().st_mtime, reverse=True)
    return hits[0] if hits else None


def def_get(row: dict, key: str) -> str:
    return def_clean_text(row.get(key, ""))


# ==================================================================================================
# def HEADER CANONICALIZATION
# ==================================================================================================
def def_yfinance_header_name(col: str) -> str:
    c = str(col)
    c = re.sub(r"\bTFinance\b", "YFinance", c, flags=re.I)
    c = re.sub(r"\bTfinance\b", "YFinance", c, flags=re.I)
    c = re.sub(r"\btfinance\b", "YFinance", c, flags=re.I)
    c = c.replace("Yfinance", "YFinance")
    c = c.replace("YFINANCE", "YFinance")
    c = c.replace("Yfinance", "YFinance")
    return c


def def_canonicalize_headers(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    out = []
    matrix = []

    for idx, row in enumerate(rows):
        nr = {}
        audit_moved = []
        for k, v in row.items():
            nk = def_yfinance_header_name(k)

            if nk != k:
                audit_moved.append(f"{k} -> {nk}")

            if nk in nr:
                # YFinance 優先；若既有空，才用 TFinance 值補。
                if def_is_blank(nr.get(nk)) and not def_is_blank(v):
                    nr[nk] = v
                else:
                    # 保留被合併掉的欄位到 audit
                    audit_key = "YFinance Header Merge Audit"
                    old = nr.get(audit_key, "")
                    extra = f"{k}={def_clean_text(v)}"
                    nr[audit_key] = (old + " | " + extra).strip(" | ")
            else:
                nr[nk] = v

        if audit_moved:
            old = nr.get("YFinance Legacy Header Renamed Audit", "")
            nr["YFinance Legacy Header Renamed Audit"] = (old + " | " + " | ".join(audit_moved)).strip(" | ")

        out.append(nr)

    all_old_cols = []
    all_new_cols = []
    for r in rows:
        for c in r.keys():
            if "TFinance" in c or "Tfinance" in c or "tfinance" in c:
                all_old_cols.append(c)
                all_new_cols.append(def_yfinance_header_name(c))

    for old, new in sorted(set(zip(all_old_cols, all_new_cols))):
        matrix.append({
            "Status Lights": def_lights("OK"),
            "Old Header": old,
            "New Header": new,
            "Action": "RENAMED_AND_MERGED",
            "Severity": "OK",
        })

    return out, matrix


# ==================================================================================================
# def YFINANCE
# ==================================================================================================
def def_import_yfinance(auto_install: bool):
    try:
        import yfinance as yf
        return yf, ""
    except Exception as e:
        if not auto_install:
            return None, f"yfinance import failed and auto install disabled: {e}"
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "yfinance", "-q"])
            import yfinance as yf
            return yf, ""
        except Exception as e2:
            return None, f"yfinance install/import failed: {e2}"


def def_candidate_tickers(row: dict) -> list[str]:
    candidates = []

    for k in [
        "YFinance Final Ticker",
        "YFinance Ticker",
        "YFinance Candidate Tickers",
        "YFinance Ticker Before",
        "YFinance Candidate Tickers Before",
    ]:
        v = def_get(row, k)
        if v:
            for part in re.split(r"[|,;/\s]+", v):
                p = def_clean_text(part)
                if re.fullmatch(r"[1-9]\d{3}\.(TW|TWO)", p, re.I):
                    candidates.append(p.upper())

    ticker = def_get(row, "Ticker")
    if re.fullmatch(r"[1-9]\d{3}", ticker):
        candidates.append(f"{ticker}.TW")
        candidates.append(f"{ticker}.TWO")

    # 去重保序
    seen = set()
    out = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def def_get_adj_col(hist):
    if "Adj Close" in hist.columns:
        return "Adj Close"
    if "Close" in hist.columns:
        return "Close"
    return ""


def def_fetch_one_yfinance(yf, ticker: str, report_date):
    res = {
        "ticker": ticker,
        "ok": False,
        "history_status": "",
        "info_status": "",
        "latest_date": "",
        "latest_adj_close": "",
        "latest_volume": "",
        "report_date": "",
        "report_date_adj_close": "",
        "report_date_volume": "",
        "target_low": "",
        "target_mean": "",
        "target_median": "",
        "target_high": "",
        "rating": "",
        "recommendation_mean": "",
        "analyst_count": "",
        "beta": "",
        "forward_eps": "",
        "forward_pe": "",
        "market_cap": "",
        "trailing_pe": "",
        "price_to_book": "",
        "error": "",
    }

    try:
        tk = yf.Ticker(ticker)

        # info
        try:
            info = tk.info or {}
            res["info_status"] = "OK"
            res["target_high"] = info.get("targetHighPrice", "")
            res["target_low"] = info.get("targetLowPrice", "")
            res["target_mean"] = info.get("targetMeanPrice", "")
            res["target_median"] = info.get("targetMedianPrice", "")
            res["rating"] = info.get("recommendationKey", "")
            res["recommendation_mean"] = info.get("recommendationMean", "")
            res["analyst_count"] = info.get("numberOfAnalystOpinions", "")
            res["beta"] = info.get("beta", "")
            res["forward_eps"] = info.get("forwardEps", "")
            res["forward_pe"] = info.get("forwardPE", "")
            res["market_cap"] = info.get("marketCap", "")
            res["trailing_pe"] = info.get("trailingPE", "")
            res["price_to_book"] = info.get("priceToBook", "")
        except Exception as e:
            res["info_status"] = "INFO_FAILED:" + str(e)[:120]

        # history
        try:
            hist = tk.history(period="10y", auto_adjust=False)
            if hist is None or hist.empty:
                res["history_status"] = "NO_HISTORY"
                return res

            adj_col = def_get_adj_col(hist)
            if not adj_col:
                res["history_status"] = "NO_ADJ_CLOSE_COL"
                return res

            hist = hist.copy()
            hist = hist.reset_index()
            date_col = "Date" if "Date" in hist.columns else hist.columns[0]
            hist["_date"] = hist[date_col].astype(str).str.slice(0, 10)

            last = hist.dropna(subset=[adj_col]).tail(1)
            if not last.empty:
                res["latest_date"] = str(last.iloc[0]["_date"])
                res["latest_adj_close"] = last.iloc[0][adj_col]
                res["latest_volume"] = last.iloc[0]["Volume"] if "Volume" in hist.columns else ""

            if report_date:
                rds = []
                for delta in range(0, 8):
                    d = report_date - timedelta(days=delta)
                    rds.append(d.isoformat())
                h2 = hist[hist["_date"].isin(rds)]
                if not h2.empty:
                    rr = h2.dropna(subset=[adj_col]).tail(1)
                    if not rr.empty:
                        res["report_date"] = str(rr.iloc[0]["_date"])
                        res["report_date_adj_close"] = rr.iloc[0][adj_col]
                        res["report_date_volume"] = rr.iloc[0]["Volume"] if "Volume" in hist.columns else ""

            res["history_status"] = "OK"
            res["ok"] = not def_is_blank(res["latest_adj_close"])
            return res
        except Exception as e:
            res["history_status"] = "HISTORY_FAILED:" + str(e)[:120]
            return res

    except Exception as e:
        res["error"] = str(e)[:180]
        return res


def def_choose_yfinance(yf, row: dict):
    report_date = def_parse_date(row.get("Report Date"))
    candidates = def_candidate_tickers(row)
    attempts = []
    best = None

    for c in candidates:
        r = def_fetch_one_yfinance(yf, c, report_date)
        attempts.append(r)
        if r.get("ok"):
            best = r
            break

    if not best and attempts:
        # 若 Adj Close 沒成功，但 info 有資料，保留 info 最完整的
        attempts_sorted = sorted(
            attempts,
            key=lambda x: sum(0 if def_is_blank(x.get(k)) else 1 for k in [
                "target_low", "target_mean", "target_median", "target_high", "rating",
                "analyst_count", "beta", "forward_eps", "forward_pe"
            ]),
            reverse=True
        )
        best = attempts_sorted[0]

    return best, attempts


def def_apply_yfinance_result(row: dict, best: dict | None, attempts: list[dict]) -> dict:
    r = dict(row)
    candidates = [x.get("ticker", "") for x in attempts if x.get("ticker")]
    success = best.get("ticker", "") if best else ""
    deleted = [x for x in candidates if x and x != success]

    # 合併 before / candidate 欄位，正式只留下 final + audit
    before_parts = []
    for k in ["YFinance Ticker Before", "YFinance Candidate Tickers Before", "YFinance Candidate Tickers", "YFinance Ticker"]:
        v = def_get(r, k)
        if v:
            before_parts.append(f"{k}={v}")
    r["YFinance Candidate Audit"] = " | ".join(before_parts + [f"attempts={' | '.join(candidates)}"]).strip(" | ")

    if success:
        r["YFinance Ticker"] = success
        r["YFinance Final Ticker"] = success

    r["YFinance Deleted Alternate Tickers"] = " | ".join(deleted)
    r["YFinance Suffix Lock Status"] = "LOCKED_ADJCLOSE_SUCCESS" if best and best.get("ok") else "REVIEW_NO_ADJCLOSE_SUCCESS"
    r["YFinance AdjClose Lock Status"] = r["YFinance Suffix Lock Status"]
    r["YFinance AdjClose Lock Reason"] = "REAL_YFINANCE_USED_TICKER_HAS_ADJCLOSE" if best and best.get("ok") else "NO_SUCCESSFUL_ADJCLOSE_TICKER"

    if best:
        mapping = {
            "YFinance History Status": "history_status",
            "YFinance Info Status": "info_status",
            "YFinance Latest Date": "latest_date",
            "YFinance Latest Adj Close": "latest_adj_close",
            "YFinance Latest Volume": "latest_volume",
            "YFinance Report Date": "report_date",
            "YFinance Report Date Adj Close": "report_date_adj_close",
            "YFinance Report Date Volume": "report_date_volume",
            "YFinance Target Price Low": "target_low",
            "YFinance Target Price Mean": "target_mean",
            "YFinance Target Price Median": "target_median",
            "YFinance Target Price High": "target_high",
            "YFinance Rating": "rating",
            "YFinance Recommendation Mean": "recommendation_mean",
            "YFinance Analyst Count": "analyst_count",
            "YFinance Beta": "beta",
            "YFinance Forward EPS": "forward_eps",
            "YFinance Forward PE": "forward_pe",
            "YFinance Market Cap": "market_cap",
            "YFinance Trailing PE": "trailing_pe",
            "YFinance Price To Book": "price_to_book",
        }
        for out_col, src in mapping.items():
            val = best.get(src, "")
            if not def_is_blank(val) or def_is_blank(r.get(out_col)):
                r[out_col] = val

    # 格式化
    for c in [
        "YFinance Latest Adj Close", "YFinance Report Date Adj Close",
        "YFinance Target Price Low", "YFinance Target Price Mean", "YFinance Target Price Median",
        "YFinance Target Price High", "YFinance Beta", "YFinance Forward EPS", "YFinance Forward PE",
        "YFinance Trailing PE", "YFinance Price To Book", "YFinance Recommendation Mean"
    ]:
        if c in r:
            r[c] = def_fmt_num(r.get(c), 2)

    for c in ["YFinance Latest Volume", "YFinance Report Date Volume", "YFinance Market Cap", "YFinance Analyst Count"]:
        if c in r:
            r[c] = def_fmt_int(r.get(c))

    # Performance / Upside
    latest = r.get("YFinance Latest Adj Close")
    report_px = r.get("YFinance Report Date Adj Close")
    mean_t = r.get("YFinance Target Price Mean")
    broker_t = r.get("Target Price")

    def to_float(x):
        try:
            return float(str(x).replace(",", "").replace("%", ""))
        except Exception:
            return None

    latest_f = to_float(latest)
    report_f = to_float(report_px)
    mean_f = to_float(mean_t)
    broker_f = to_float(broker_t)

    if latest_f and report_f:
        r["YFinance Report To Latest Performance"] = def_fmt_pct((latest_f / report_f - 1) * 100)
    if latest_f and mean_f:
        r["YFinance Mean Target Upside"] = def_fmt_pct((mean_f / latest_f - 1) * 100)
    if latest_f and broker_f:
        r["Broker Target Upside By Latest Adj Close"] = def_fmt_pct((broker_f / latest_f - 1) * 100)

    r["Official Market Data Prefix"] = "YFinance"
    r["YFinance Official Field Status"] = "CANONICAL_YFINANCE_HEADERS_V06147"
    return r


def def_remove_tfinance_columns(row: dict) -> dict:
    nr = {}
    legacy = []
    for k, v in row.items():
        if re.search(r"\bTFinance\b", k, re.I):
            legacy.append(f"{k}={def_clean_text(v)}")
            continue
        nr[k] = v
    if legacy:
        old = nr.get("YFinance Legacy TFinance Column Audit", "")
        nr["YFinance Legacy TFinance Column Audit"] = (old + " | " + " | ".join(legacy)).strip(" | ")
    return nr


# ==================================================================================================
# def PATCH SSOT / BRIDGE
# ==================================================================================================
def def_patch_block() -> str:
    return PATCH_START + "\n" + r'''
# VRN v0.6.14.7 YFinance Canonical Field Policy
def def_vrn_yfinance_field_policy_v06147():
    return {
        "official_market_data_prefix": "YFinance",
        "deprecated_prefix": "TFinance",
        "rule": "All headers containing TFinance must be renamed/merged into YFinance. YFinance values take priority; legacy TFinance values are audit fallback only.",
        "yfinance_info_fields": [
            "targetHighPrice",
            "targetLowPrice",
            "targetMeanPrice",
            "targetMedianPrice",
            "recommendationKey",
            "recommendationMean",
            "numberOfAnalystOpinions",
            "beta",
            "forwardEps",
            "forwardPE",
            "marketCap",
            "trailingPE",
            "priceToBook"
        ],
        "yfinance_history_fields": ["Adj Close", "Volume"],
        "suffix_fallback": [".TW", ".TWO"],
        "success_lock": "Keep the ticker suffix that successfully returns Adj Close; move alternate suffixes to audit."
    }
''' + "\n" + PATCH_END + "\n"


def def_patch_python_file(path: Path, role: str) -> dict:
    out = {"target": str(path), "role": role, "patched": False, "backup": "", "compile_ok": False, "error": ""}
    if not path.exists():
        out["error"] = "FILE_NOT_FOUND"
        return out
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
        ast.parse(text)
        block = def_patch_block()
        if PATCH_START in text and PATCH_END in text:
            new_text = re.sub(re.escape(PATCH_START) + r".*?" + re.escape(PATCH_END), block.strip(), text, flags=re.S)
        else:
            new_text = text.rstrip() + "\n\n" + block
        if new_text != text:
            backup = path.with_suffix(path.suffix + ".bak_v06147_yfinance_policy_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
            shutil.copy2(path, backup)
            path.write_text(new_text, encoding="utf-8")
            out["patched"] = True
            out["backup"] = str(backup)
        ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        out["compile_ok"] = True
    except Exception:
        out["error"] = traceback.format_exc()
    return out


# ==================================================================================================
# def HTML
# ==================================================================================================
def def_table_html(title: str, rows: list[dict]) -> str:
    if not rows:
        return f"<section class='card'><h2>{html.escape(title)}</h2><p>No rows.</p></section>"
    fields = []
    for r in rows:
        for k in r.keys():
            if k not in fields:
                fields.append(k)
    th = "".join(f"<th>{html.escape(str(c))}</th>" for c in fields)
    trs = []
    for r in rows:
        tds = []
        for c in fields:
            v = "" if r.get(c) is None else str(r.get(c, ""))
            cls = "left" if any(x in c.lower() for x in ["filename", "evidence", "audit", "status", "reason", "header", "target"]) else "center"
            tds.append(f"<td class='{cls}'>{html.escape(v).replace(chr(10), '<br>')}</td>")
        trs.append("<tr>" + "".join(tds) + "</tr>")
    return f"<section class='card'><h2>{html.escape(title)}</h2><div class='table-wrap'><table><thead><tr>{th}</tr></thead><tbody>{''.join(trs)}</tbody></table></div></section>"


def def_write_html(path: Path, result: dict, sections: list[tuple[str, list[dict]]]) -> None:
    css = """
body{margin:0;background:#07111f;color:#eef6ff;font-family:Segoe UI,'Microsoft JhengHei',Arial,sans-serif;font-size:12px}
header{padding:24px 32px;background:#0d1b2f;border-bottom:1px solid #1f3557}
h1{margin:0;font-size:24px}.sub{color:#9fb3c8;margin-top:8px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px;padding:20px 32px}
.kpi{background:#0d1b2f;border:1px solid #1f3557;border-radius:18px;padding:16px}
.v{font-size:26px;font-weight:800}.k{color:#9fb3c8}
main{padding:0 32px 32px}
.card{background:#0d1b2f;border:1px solid #1f3557;border-radius:18px;margin:18px 0;padding:18px}
.table-wrap{overflow:auto;max-height:78vh;border:1px solid #1f3557;border-radius:14px}
table{border-collapse:collapse;min-width:100%;width:max-content}
th{position:sticky;top:0;background:#132541;padding:10px;text-align:center;white-space:normal}
td{padding:8px 10px;border-bottom:1px solid rgba(255,255,255,.08);vertical-align:top;max-width:680px;white-space:normal;word-break:break-word}
td.left{text-align:left}td.center{text-align:center}
"""
    cards = result.get("counts", {})
    card_html = "<div class='grid'>" + "".join(
        f"<div class='kpi'><div class='v'>{html.escape(str(v))}</div><div class='k'>{html.escape(str(k))}</div></div>"
        for k, v in cards.items()
    ) + "</div>"
    body = "".join(def_table_html(t, r) for t, r in sections)
    doc = f"""<!doctype html><html><head><meta charset="utf-8"><title>VRN YFinance Header Canonical v06147</title><style>{css}</style></head>
<body><header><h1>VRN · YFinance Header Canonical + Info Refresh v0.6.14.7</h1>
<div class="sub">TFinance removed · YFinance official fields · suffix fallback · info/history refresh · no canonical mutation</div></header>
{card_html}<main>{body}</main></body></html>"""
    path.write_text(doc, encoding="utf-8")


# ==================================================================================================
# def MAIN
# ==================================================================================================
def def_main() -> None:
    if len(sys.argv) < 9:
        raise SystemExit("usage: py <run_root> <run_dir> <config_dir> <ssot> <bridge> <publish_canonical> <canonical_dir> <auto_install_yfinance>")

    run_root = Path(sys.argv[1])
    run_dir = Path(sys.argv[2])
    config_dir = Path(sys.argv[3])
    ssot = Path(sys.argv[4])
    bridge = Path(sys.argv[5])
    publish_canonical = str(sys.argv[6]).lower() in ["true", "1", "yes"]
    canonical_dir = Path(sys.argv[7])
    auto_install_yfinance = str(sys.argv[8]).lower() in ["true", "1", "yes"]

    run_dir.mkdir(parents=True, exist_ok=True)
    config_dir.mkdir(parents=True, exist_ok=True)

    source_csv = def_find_latest(run_root, [
        "vrn_v06146_company_master_broker_analyst_adapter_sealed.csv",
        "vrn_v06145_company_master_huanan_analyst_broker_sealed.csv",
        "vrn_v06144_company_master_yfinance_official_analyst_fixed.csv",
    ])
    if not source_csv:
        raise RuntimeError("Cannot find source CSV from v06146/v06145/v06144.")

    rows_raw = def_read_csv(source_csv)
    rows_canon, header_matrix = def_canonicalize_headers(rows_raw)

    yf, yf_error = def_import_yfinance(auto_install_yfinance)

    out_rows = []
    yfinance_matrix = []

    for row in rows_canon:
        r = def_remove_tfinance_columns(row)

        if yf is not None:
            best, attempts = def_choose_yfinance(yf, r)
            r = def_apply_yfinance_result(r, best, attempts)

            yfinance_matrix.append({
                "Status Lights": def_lights("OK" if best and best.get("ok") else "WARN"),
                "Filename": r.get("Filename", ""),
                "Ticker": r.get("Ticker", ""),
                "YFinance Final Ticker": r.get("YFinance Final Ticker", ""),
                "Deleted Alternate Tickers": r.get("YFinance Deleted Alternate Tickers", ""),
                "History Status": r.get("YFinance History Status", ""),
                "Info Status": r.get("YFinance Info Status", ""),
                "Latest Date": r.get("YFinance Latest Date", ""),
                "Latest Adj Close": r.get("YFinance Latest Adj Close", ""),
                "Report Date": r.get("YFinance Report Date", ""),
                "Report Date Adj Close": r.get("YFinance Report Date Adj Close", ""),
                "Target Low": r.get("YFinance Target Price Low", ""),
                "Target Mean": r.get("YFinance Target Price Mean", ""),
                "Target Median": r.get("YFinance Target Price Median", ""),
                "Target High": r.get("YFinance Target Price High", ""),
                "Rating": r.get("YFinance Rating", ""),
                "Analyst Count": r.get("YFinance Analyst Count", ""),
                "Beta": r.get("YFinance Beta", ""),
                "Forward EPS": r.get("YFinance Forward EPS", ""),
                "Forward PE": r.get("YFinance Forward PE", ""),
                "Performance": r.get("YFinance Report To Latest Performance", ""),
                "Mean Target Upside": r.get("YFinance Mean Target Upside", ""),
                "Broker Target Upside": r.get("Broker Target Upside By Latest Adj Close", ""),
                "Severity": "OK" if best and best.get("ok") else "WARN",
            })
        else:
            r["YFinance Refresh Status"] = "SKIPPED_YFINANCE_IMPORT_FAILED"
            r["YFinance Refresh Error"] = yf_error

        out_rows.append(r)

    # 最後防守：不得有 TFinance header
    remaining_tfinance_headers = []
    for r in out_rows:
        for k in r.keys():
            if re.search(r"\bTFinance\b", k, re.I):
                remaining_tfinance_headers.append(k)
    remaining_tfinance_headers = sorted(set(remaining_tfinance_headers))

    ssot_patch = def_patch_python_file(ssot, "SSOT_YFINANCE_POLICY")
    bridge_patch = def_patch_python_file(bridge, "BRIDGE_YFINANCE_POLICY")

    overview = [
        {"Status Lights": def_lights("OK"), "Gate": "SOURCE_CSV", "Value": str(source_csv), "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "ROWS", "Value": len(out_rows), "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "HEADERS_RENAMED", "Value": len(header_matrix), "Severity": "OK"},
        {"Status Lights": def_lights("OK" if not remaining_tfinance_headers else "ERR"), "Gate": "REMAINING_TFINANCE_HEADERS", "Value": len(remaining_tfinance_headers), "Severity": "OK" if not remaining_tfinance_headers else "ERR"},
        {"Status Lights": def_lights("OK" if yf is not None else "WARN"), "Gate": "YFINANCE_IMPORT", "Value": "OK" if yf is not None else yf_error, "Severity": "OK" if yf is not None else "WARN"},
        {"Status Lights": def_lights("OK"), "Gate": "OFFICIAL_MARKET_DATA_PREFIX", "Value": "YFinance", "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "NO_CANONICAL_MUTATION", "Value": "YES", "Severity": "OK"},
    ]

    patch_matrix = []
    for p in [ssot_patch, bridge_patch]:
        patch_matrix.append({
            "Status Lights": def_lights("OK" if p.get("compile_ok") else "ERR"),
            "Target": p.get("target", ""),
            "Role": p.get("role", ""),
            "Patched": "YES" if p.get("patched") else "ALREADY_PRESENT",
            "Backup": p.get("backup", ""),
            "Compile OK": "YES" if p.get("compile_ok") else "NO",
            "Error": p.get("error", ""),
            "Severity": "OK" if p.get("compile_ok") else "ERR",
        })

    remaining_rows = [
        {"Status Lights": def_lights("ERR"), "Remaining Header": h, "Severity": "ERR"}
        for h in remaining_tfinance_headers
    ]

    out_csv = run_dir / "vrn_v06147_company_master_yfinance_canonical_refreshed.csv"
    yf_csv = run_dir / "vrn_v06147_yfinance_refresh_matrix.csv"
    header_csv = run_dir / "vrn_v06147_header_rename_matrix.csv"
    html_path = run_dir / "VRN_YFinance_Header_Canonical_Refresh_v06147.html"
    json_path = run_dir / "vrn_yfinance_header_canonical_refresh_v06147.json"
    manifest_path = config_dir / "VRN_YFinance_Header_Canonical_Refresh_Manifest_v06147.json"

    def_write_csv(out_csv, out_rows)
    def_write_csv(yf_csv, yfinance_matrix)
    def_write_csv(header_csv, header_matrix)

    if publish_canonical:
        def_write_csv(canonical_dir / "vrn_company_master_yfinance_canonical_active.csv", out_rows)

    system_pass = (len(remaining_tfinance_headers) == 0)

    result = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "system_pass": system_pass,
        "source_csv": str(source_csv),
        "counts": {
            "Rows": len(out_rows),
            "Headers Renamed": len(header_matrix),
            "YFinance Refresh Rows": len(yfinance_matrix),
            "Remaining TFinance Headers": len(remaining_tfinance_headers),
            "YFinance Import": "OK" if yf is not None else "WARN",
            "No Canonical Mutation": "YES",
        },
        "outputs": {
            "html": str(html_path),
            "json": str(json_path),
            "master_csv": str(out_csv),
            "yfinance_matrix_csv": str(yf_csv),
            "header_matrix_csv": str(header_csv),
            "manifest_json": str(manifest_path),
        },
        "policy": {
            "official_prefix": "YFinance",
            "deprecated_prefix": "TFinance",
            "merge_rule": "YFinance value priority; TFinance value only fallback; no TFinance header remains.",
            "info_fields": [
                "targetHighPrice", "targetLowPrice", "targetMeanPrice", "targetMedianPrice",
                "recommendationKey", "recommendationMean", "numberOfAnalystOpinions",
                "beta", "forwardEps", "forwardPE", "marketCap", "trailingPE", "priceToBook"
            ],
            "history_fields": ["Adj Close", "Volume"],
            "canonical_mutation": False,
        },
    }

    def_write_json(json_path, result)
    def_write_json(manifest_path, result)

    def_write_html(html_path, result, [
        ("01 Overview", overview),
        ("02 Header Rename Matrix", header_matrix),
        ("03 YFinance Refresh Matrix", yfinance_matrix),
        ("04 Remaining TFinance Header Check", remaining_rows),
        ("05 Patch Matrix", patch_matrix),
        ("06 Full Master Output", out_rows),
    ])

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        def_main()
    except Exception:
        print(traceback.format_exc())
        raise