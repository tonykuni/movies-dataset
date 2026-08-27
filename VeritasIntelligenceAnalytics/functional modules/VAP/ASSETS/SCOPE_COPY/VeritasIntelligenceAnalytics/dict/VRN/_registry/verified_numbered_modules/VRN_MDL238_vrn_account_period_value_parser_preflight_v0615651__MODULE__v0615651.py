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

import csv
import html
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


VERSION = "VRN_ACCOUNT_PERIOD_VALUE_PARSER_PREFLIGHT_V0615651"


def def_clean(x: Any) -> str:
    s = "" if x is None else str(x)
    s = s.replace("\u3000", " ").replace("\r", "\n")
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()


def def_flat(x: Any) -> str:
    return re.sub(r"\s+", " ", def_clean(x)).strip()


def def_norm(x: Any) -> str:
    return re.sub(r"[\s_\-\/\(\)（）\[\]【】{}:：,，.。&+]+", "", str(x or "").lower())


def def_float(x: Any, default: Any = "") -> Any:
    s = def_flat(x).replace(",", "").replace("%", "")
    if s in ["", "-", "—", "–", "NA", "N/A", "nan", "None"]:
        return default
    try:
        return float(s)
    except Exception:
        return default


def def_int(x: Any, default: int = 0) -> int:
    try:
        return int(float(str(x).replace(",", "").replace("%", "").strip()))
    except Exception:
        return default


def def_light(sev: str) -> str:
    s = str(sev or "").upper()
    if s in ["OK", "PASS", "YES", "READY", "PARSER_READY", "FORMULA_PASS"]:
        return "🟢 INPUT 🟢 DB 🟢 TRUST"
    if s in ["WARN", "REVIEW", "QUEUE", "ALIAS", "PREFLIGHT", "FORMULA_REVIEW"]:
        return "🟢 INPUT 🟡 DB 🟡 TRUST"
    return "🔴 INPUT 🔴 DB 🔴 TRUST"


def def_find_latest_dir(root: Path, prefix: str) -> Path | None:
    hits = [p for p in root.glob(prefix + "_*") if p.is_dir()]
    return sorted(hits, key=lambda p: p.stat().st_mtime, reverse=True)[0] if hits else None


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
    if not rows:
        rows = [{"empty_marker": ""}]
    fields = []
    for r in rows:
        for k in r:
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


def def_get(row: dict, aliases: list[str]) -> str:
    mp = {def_norm(k): k for k in row.keys()}
    for a in aliases:
        na = def_norm(a)
        if na in mp:
            return def_clean(row.get(mp[na]))
    for k in row.keys():
        nk = def_norm(k)
        for a in aliases:
            if def_norm(a) in nk:
                return def_clean(row.get(k))
    return ""


def def_account_alias_map() -> list[tuple[str, str, str]]:
    return [
        ("cashandequivalents", "Cash & equivalents", "cash_and_equivalents"),
        ("cash", "Cash & equivalents", "cash_and_equivalents"),
        ("accountsreceivable", "Accounts receivable", "accounts_receivable"),
        ("receivables", "Accounts receivable", "accounts_receivable"),
        ("inventories", "Inventories", "inventories"),
        ("inventory", "Inventories", "inventories"),
        ("othercurrentassets", "Other current assets", "other_current_assets"),
        ("currentassets", "Current assets", "current_assets"),
        ("fixedassets", "Fixed assets", "fixed_assets"),
        ("ppe", "Fixed assets", "fixed_assets"),
        ("investments", "Investments", "investments"),
        ("goodwill", "Goodwill", "goodwill"),
        ("otherintangibleassets", "Other intangible assets", "intangible_assets"),
        ("intangibleassets", "Other intangible assets", "intangible_assets"),
        ("othernoncurrentassets", "Other non-current assets", "other_non_current_assets"),
        ("totalassets", "Total assets", "total_assets"),
        ("shorttermloansod", "Short term loans/OD", "short_term_debt"),
        ("shorttermdebt", "Short term loans/OD", "short_term_debt"),
        ("accountspayable", "Accounts payable", "accounts_payable"),
        ("taxespayable", "Taxes payable", "taxes_payable"),
        ("othercurrentliabs", "Other current liabilities", "other_current_liabilities"),
        ("othercurrentliabilities", "Other current liabilities", "other_current_liabilities"),
        ("currentliabilities", "Current liabilities", "current_liabilities"),
        ("longtermdebtleasesother", "Long-term debt/leases/other", "long_term_debt"),
        ("longtermdebt", "Long-term debt/leases/other", "long_term_debt"),
        ("provisionsotherltliabs", "Provisions/other LT liabilities", "other_long_term_liabilities"),
        ("totalliabilities", "Total liabilities", "total_liabilities"),
        ("shareholdersequity", "Shareholders equity", "shareholders_equity"),
        ("totalequity", "Shareholders equity", "shareholders_equity"),
        ("totaldebt", "Total debt", "total_debt"),
        ("revenue", "Revenue", "revenue"),
        ("revenuenet", "Revenue", "revenue"),
        ("sales", "Revenue", "revenue"),
        ("營業收入", "Revenue", "revenue"),
        ("營收", "Revenue", "revenue"),
        ("cogs", "Cost of goods sold", "cogs"),
        ("costofgoodssold", "Cost of goods sold", "cogs"),
        ("營業成本", "Cost of goods sold", "cogs"),
        ("grossprofit", "Gross profit", "gross_profit"),
        ("營業毛利", "Gross profit", "gross_profit"),
        ("opex", "Operating expenses", "operating_expenses"),
        ("operatingexpenses", "Operating expenses", "operating_expenses"),
        ("營業費用", "Operating expenses", "operating_expenses"),
        ("operatingincome", "Operating income", "operating_income"),
        ("營業利益", "Operating income", "operating_income"),
        ("netincome", "Net income", "net_income"),
        ("稅後淨利", "Net income", "net_income"),
        ("eps", "Diluted EPS", "diluted_eps"),
        ("dilutedeps", "Diluted EPS", "diluted_eps"),
        ("每股盈餘", "Diluted EPS", "diluted_eps"),
        ("basiceps", "Basic EPS", "basic_eps"),
        ("grossmargin", "Gross margin", "gross_margin"),
        ("operatingmargin", "Operating margin", "operating_margin"),
        ("netmargin", "Net margin", "net_margin"),
        ("roe", "ROE", "roe"),
        ("roa", "ROA", "roa"),
        ("operatingcashflow", "Operating cash flow", "operating_cash_flow"),
        ("capex", "Capital expenditure", "capex"),
        ("freecashflow", "Free cash flow", "free_cash_flow"),
    ]


def def_account_map(account_raw: str) -> dict:
    n = def_norm(account_raw)
    if not n:
        return {"account canonical": "", "account key": "", "account match score": 0.0, "account route": "ACCOUNT_ALIAS_CANDIDATE"}

    best = {"account canonical": "", "account key": "", "account match score": 0.0, "account route": "ACCOUNT_ALIAS_CANDIDATE"}

    for alias, canonical, key in def_account_alias_map():
        a = def_norm(alias)
        if not a:
            continue
        if n == a:
            return {"account canonical": canonical, "account key": key, "account match score": 1.0, "account route": "ACCOUNT_READY"}
        if a in n or n in a:
            score = min(len(a), len(n)) / max(len(a), len(n))
            if score > best["account match score"]:
                best = {
                    "account canonical": canonical,
                    "account key": key,
                    "account match score": round(score, 3),
                    "account route": "ACCOUNT_READY" if score >= 0.72 else "ACCOUNT_ALIAS_CANDIDATE",
                }

    return best


def def_period_parse(period_raw: str) -> dict:
    p = def_flat(period_raw).upper().replace(" ", "")
    out = {
        "period raw normalized": p,
        "period year": "",
        "period type": "UNKNOWN",
        "period confidence": 0.0,
        "period route": "PERIOD_REVIEW",
    }

    m = re.search(r"(20\d{2})", p)
    if m:
        out["period year"] = int(m.group(1))

    if re.search(r"CT|E|F|EST|FCST|FORECAST|預估|預測", p):
        out["period type"] = "FORECAST"
    elif re.search(r"A|ACT|ACTUAL|實際", p):
        out["period type"] = "ACTUAL"
    elif re.search(r"Q[1-4]|[1-4]Q", p):
        out["period type"] = "QUARTER"
    elif out["period year"]:
        out["period type"] = "YEAR"

    if out["period year"] and 2000 <= int(out["period year"]) <= 2035:
        out["period confidence"] = 0.96 if out["period type"] in ["ACTUAL", "FORECAST", "QUARTER"] else 0.84
        out["period route"] = "PERIOD_READY"

    return out


def def_statement_normalize(statement: str, account_raw: str, account_key: str) -> str:
    blob = def_norm(statement + " " + account_raw + " " + account_key)
    if account_key in ["revenue", "cogs", "gross_profit", "operating_expenses", "operating_income", "net_income", "basic_eps", "diluted_eps"]:
        return "INCOME_STATEMENT"
    if account_key in ["cash_and_equivalents", "accounts_receivable", "inventories", "current_assets", "total_assets", "accounts_payable", "current_liabilities", "total_liabilities", "shareholders_equity", "total_debt"]:
        return "BALANCE_SHEET"
    if account_key in ["operating_cash_flow", "capex", "free_cash_flow"]:
        return "CASH_FLOW"
    if account_key in ["gross_margin", "operating_margin", "net_margin", "roe", "roa"]:
        return "RATIO_ANALYSIS"
    if "income" in blob or "損益" in blob:
        return "INCOME_STATEMENT"
    if "balance" in blob or "assets" in blob or "liabilities" in blob or "equity" in blob or "資產" in blob or "負債" in blob:
        return "BALANCE_SHEET"
    if "cashflow" in blob or "現金流" in blob:
        return "CASH_FLOW"
    return "UNCLASSIFIED_FINANCIAL_TABLE"


def def_unit_infer(account_key: str, value_raw: str) -> dict:
    raw = def_flat(value_raw)
    if "%" in raw or account_key in ["gross_margin", "operating_margin", "net_margin", "roe", "roa"]:
        return {"unit": "%", "unit confidence": 0.96, "unit route": "UNIT_READY"}
    if account_key in ["basic_eps", "diluted_eps"]:
        return {"unit": "TWD/share", "unit confidence": 0.90, "unit route": "UNIT_READY"}
    return {"unit": "mn TWD", "unit confidence": 0.72, "unit route": "UNIT_DEFAULT_REVIEW"}


def def_parse_row(row: dict) -> dict:
    account_raw = def_get(row, ["account raw"])
    period_raw = def_get(row, ["period raw"])
    value_raw = def_get(row, ["value raw"])
    value_numeric = def_float(def_get(row, ["value numeric"]), "")

    account = def_account_map(account_raw)
    period = def_period_parse(period_raw)
    statement = def_statement_normalize(def_get(row, ["statement type"]), account_raw, account.get("account key", ""))
    unit = def_unit_infer(account.get("account key", ""), value_raw)

    issues = []
    if account["account route"] != "ACCOUNT_READY":
        issues.append("ACCOUNT_ALIAS_CANDIDATE")
    if period["period route"] != "PERIOD_READY":
        issues.append("PERIOD_REVIEW")
    if value_numeric == "":
        issues.append("VALUE_REVIEW")
    if statement == "UNCLASSIFIED_FINANCIAL_TABLE":
        issues.append("STATEMENT_REVIEW")

    route = "PARSER_READY" if not issues else " | ".join(issues)
    sev = "OK" if route == "PARSER_READY" else "WARN"

    confidence = (
        float(account["account match score"]) * 0.35
        + float(period["period confidence"]) * 0.25
        + (1.0 if value_numeric != "" else 0.0) * 0.25
        + (0.90 if statement != "UNCLASSIFIED_FINANCIAL_TABLE" else 0.30) * 0.15
    )

    out = dict(row)
    out.update({
        "Status Lights": def_light(sev),
        "statement normalized": statement,
        "account canonical": account["account canonical"],
        "account key": account["account key"],
        "account match score": account["account match score"],
        "account route": account["account route"],
        "period year": period["period year"],
        "period type": period["period type"],
        "period confidence": period["period confidence"],
        "period route": period["period route"],
        "value numeric parsed": value_numeric,
        "value route": "VALUE_READY" if value_numeric != "" else "VALUE_REVIEW",
        "unit": unit["unit"],
        "unit confidence": unit["unit confidence"],
        "unit route": unit["unit route"],
        "parser route": route,
        "parser confidence": round(confidence, 4),
        "db write": "NO",
        "canonical mutation": "NO",
        "ssot mutation": "NO",
        "Severity": sev,
    })
    return out


def def_formula_preflight(rows: list[dict]) -> list[dict]:
    by_key = defaultdict(dict)
    for r in rows:
        if r.get("parser route") != "PARSER_READY":
            continue
        key = (
            r.get("staging table id", ""),
            r.get("filename", ""),
            r.get("ticker", ""),
            r.get("statement normalized", ""),
            r.get("period year", ""),
            r.get("period type", ""),
        )
        by_key[key][r.get("account key", "")] = def_float(r.get("value numeric parsed"), None)

    checks = []

    def add_check(key_tuple, vals, name, lhs_key, rhs_keys, fn, tolerance):
        lhs = vals.get(lhs_key)
        rhs_values = [vals.get(k) for k in rhs_keys]
        if lhs is None or any(v is None for v in rhs_values):
            return
        rhs = fn(rhs_values)
        diff = abs(float(lhs) - float(rhs))
        ok = diff <= tolerance
        staging, filename, ticker, statement, year, ptype = key_tuple
        checks.append({
            "Status Lights": def_light("OK" if ok else "WARN"),
            "formula check": name,
            "staging table id": staging,
            "filename": filename,
            "ticker": ticker,
            "statement": statement,
            "period year": year,
            "period type": ptype,
            "lhs account": lhs_key,
            "lhs value": lhs,
            "rhs accounts": " + ".join(rhs_keys),
            "rhs value": rhs,
            "diff": round(diff, 4),
            "formula route": "FORMULA_PREFLIGHT_PASS" if ok else "FORMULA_PREFLIGHT_REVIEW",
            "db write": "NO",
            "canonical mutation": "NO",
            "ssot mutation": "NO",
            "Severity": "OK" if ok else "WARN",
        })

    for key, vals in by_key.items():
        add_check(key, vals, "current_assets_components", "current_assets", ["cash_and_equivalents", "accounts_receivable", "inventories", "other_current_assets"], sum, 10.0)
        add_check(key, vals, "total_assets_components", "total_assets", ["current_assets", "fixed_assets", "investments", "goodwill", "intangible_assets", "other_non_current_assets"], sum, 10.0)
        add_check(key, vals, "current_liabilities_components", "current_liabilities", ["short_term_debt", "accounts_payable", "taxes_payable", "other_current_liabilities"], sum, 10.0)
        add_check(key, vals, "gross_profit_check", "gross_profit", ["revenue", "cogs"], lambda x: x[0] - x[1], 10.0)
        add_check(key, vals, "operating_income_check", "operating_income", ["gross_profit", "operating_expenses"], lambda x: x[0] - x[1], 10.0)

    return checks


def def_table(title: str, rows: list[dict], limit: int | None = None) -> str:
    if limit is not None:
        rows = rows[:limit]
    if not rows:
        return f"<section class='card'><h2>{html.escape(title)}</h2><p>No rows.</p></section>"

    fields = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)

    th = "".join(f"<th>{html.escape(str(k))}</th>" for k in fields)
    trs = []
    for r in rows:
        tds = []
        for k in fields:
            v = "" if r.get(k) is None else str(r.get(k, ""))
            cls = "left" if any(x in k.lower() for x in ["filename", "account", "period", "route", "formula", "rhs", "lhs", "reason", "next"]) else "center"
            tds.append(f"<td class='{cls}'>{html.escape(str(v)).replace(chr(10), '<br>')}</td>")
        trs.append("<tr>" + "".join(tds) + "</tr>")
    return f"<section class='card'><h2>{html.escape(title)}</h2><div class='table-wrap'><table><thead><tr>{th}</tr></thead><tbody>{''.join(trs)}</tbody></table></div></section>"


def def_write_html(path: Path, counts: dict, sections: list[tuple[str, list[dict], int | None]]) -> None:
    css = """
body{margin:0;background:#07111f;color:#eef6ff;font-family:Segoe UI,'Microsoft JhengHei',Arial,sans-serif;font-size:12px}
header{padding:26px 34px;background:#0d1b2f;border-bottom:1px solid #1f3557}
h1{margin:0;font-size:25px}.sub{color:#9fb3c8;margin-top:8px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(185px,1fr));gap:14px;padding:22px 34px}
.kpi{background:#0d1b2f;border:1px solid #1f3557;border-radius:18px;padding:16px}
.v{font-size:25px;font-weight:800}.k{color:#9fb3c8}
main{padding:0 34px 34px}
.card{background:#0d1b2f;border:1px solid #1f3557;border-radius:18px;padding:18px;margin:18px 0}
.table-wrap{overflow:auto;max-height:76vh;border:1px solid #1f3557;border-radius:14px}
table{border-collapse:collapse;min-width:100%;width:max-content}
th{position:sticky;top:0;background:#132541;padding:10px;text-align:center}
td{padding:8px 10px;border-bottom:1px solid rgba(255,255,255,.08);vertical-align:top;max-width:1120px;white-space:normal;word-break:break-word}
td.left{text-align:left}td.center{text-align:center}
"""
    cards = "".join(
        f"<div class='kpi'><div class='v'>{html.escape(str(v))}</div><div class='k'>{html.escape(str(k))}</div></div>"
        for k, v in counts.items()
    )
    body = "".join(def_table(t, rows, lim) for t, rows, lim in sections)
    doc = f"""<!doctype html><html><head><meta charset="utf-8"><title>VRN Account Period Value Parser Preflight v0615651</title><style>{css}</style></head>
<body><header><h1>VRN · Account / Period / Value Parser Preflight v0.6.15.6.5.1</h1>
<div class="sub">canonical draft rows · parser route · formula preflight · no DB/canonical/SSOT write</div></header>
<div class="grid">{cards}</div><main>{body}</main></body></html>"""
    path.write_text(doc, encoding="utf-8")


def def_main() -> None:
    if len(sys.argv) < 3:
        raise SystemExit("usage: py <run_root> <run_dir>")

    run_root = Path(sys.argv[1])
    run_dir = Path(sys.argv[2])
    run_dir.mkdir(parents=True, exist_ok=True)

    source = def_find_latest_dir(run_root, "VRN_TARGETED_TABLE_BODY_EXPORT_DRYRUN_V061564")
    if not source:
        raise RuntimeError("Cannot find latest VRN_TARGETED_TABLE_BODY_EXPORT_DRYRUN_V061564 run.")

    draft_csv = source / "vrn_canonical_row_draft_preflight_v061564.csv"
    source_review_csv = source / "vrn_source_review_isolation_not_exported_v061564.csv"

    draft_rows = [r for r in def_read_csv(draft_csv) if "empty_marker" not in r]
    source_review_rows = [r for r in def_read_csv(source_review_csv) if "empty_marker" not in r]

    parsed = [def_parse_row(r) for r in draft_rows]
    ready = [r for r in parsed if r.get("parser route") == "PARSER_READY"]
    account_alias = [r for r in parsed if "ACCOUNT_ALIAS_CANDIDATE" in str(r.get("parser route", ""))]
    period_review = [r for r in parsed if "PERIOD_REVIEW" in str(r.get("parser route", ""))]
    value_review = [r for r in parsed if "VALUE_REVIEW" in str(r.get("parser route", ""))]
    statement_review = [r for r in parsed if "STATEMENT_REVIEW" in str(r.get("parser route", ""))]

    formula_checks = def_formula_preflight(parsed)
    formula_pass = [r for r in formula_checks if r.get("formula route") == "FORMULA_PREFLIGHT_PASS"]
    formula_review = [r for r in formula_checks if r.get("formula route") != "FORMULA_PREFLIGHT_PASS"]

    route_summary = []
    for k, v in sorted(Counter(r.get("parser route", "") for r in parsed).items(), key=lambda x: (-x[1], x[0])):
        sev = "OK" if k == "PARSER_READY" else "WARN"
        route_summary.append({
            "Status Lights": def_light(sev),
            "parser route": k,
            "rows": v,
            "rate": f"{(v / max(len(parsed), 1)) * 100:.2f}%",
            "Severity": sev,
        })

    account_alias_summary = []
    for k, v in sorted(Counter(r.get("account raw", "") for r in account_alias).items(), key=lambda x: (-x[1], x[0]))[:500]:
        account_alias_summary.append({
            "Status Lights": def_light("WARN"),
            "account raw": k,
            "rows": v,
            "recommended action": "SSOT_ALIAS_CANDIDATE_REVIEW_ONLY_NO_PATCH",
            "Severity": "WARN",
        })

    source_review_out = []
    for r in source_review_rows:
        rr = dict(r)
        rr["Status Lights"] = def_light("WARN")
        rr["parser status"] = "SOURCE_REVIEW_ISOLATED_NOT_PARSED"
        rr["reason"] = "source/caption evidence controls confidence upgrade"
        rr["db write"] = "NO"
        rr["canonical mutation"] = "NO"
        rr["ssot mutation"] = "NO"
        rr["Severity"] = "WARN"
        source_review_out.append(rr)

    outputs = {
        "html": str(run_dir / "VRN_Account_Period_Value_Parser_Preflight_v0615651.html"),
        "json": str(run_dir / "vrn_account_period_value_parser_preflight_v0615651.json"),
        "parser_matrix_csv": str(run_dir / "vrn_account_period_value_parser_matrix_v0615651.csv"),
        "parser_ready_csv": str(run_dir / "vrn_parser_ready_rows_v0615651.csv"),
        "account_alias_candidates_csv": str(run_dir / "vrn_account_alias_candidates_v0615651.csv"),
        "account_alias_summary_csv": str(run_dir / "vrn_account_alias_summary_v0615651.csv"),
        "period_review_csv": str(run_dir / "vrn_period_review_v0615651.csv"),
        "value_review_csv": str(run_dir / "vrn_value_review_v0615651.csv"),
        "statement_review_csv": str(run_dir / "vrn_statement_review_v0615651.csv"),
        "formula_preflight_csv": str(run_dir / "vrn_formula_preflight_v0615651.csv"),
        "source_review_isolation_csv": str(run_dir / "vrn_source_review_isolation_v0615651.csv"),
        "route_summary_csv": str(run_dir / "vrn_parser_route_summary_v0615651.csv"),
    }

    def_write_csv(Path(outputs["parser_matrix_csv"]), parsed)
    def_write_csv(Path(outputs["parser_ready_csv"]), ready)
    def_write_csv(Path(outputs["account_alias_candidates_csv"]), account_alias)
    def_write_csv(Path(outputs["account_alias_summary_csv"]), account_alias_summary)
    def_write_csv(Path(outputs["period_review_csv"]), period_review)
    def_write_csv(Path(outputs["value_review_csv"]), value_review)
    def_write_csv(Path(outputs["statement_review_csv"]), statement_review)
    def_write_csv(Path(outputs["formula_preflight_csv"]), formula_checks)
    def_write_csv(Path(outputs["source_review_isolation_csv"]), source_review_out)
    def_write_csv(Path(outputs["route_summary_csv"]), route_summary)

    final_pass = len(parsed) > 0 and len(value_review) == 0 and len(period_review) == 0

    counts = {
        "Final": "PASS" if final_pass else "REVIEW",
        "Input Draft Rows": len(draft_rows),
        "Parser Ready": len(ready),
        "Account Alias": len(account_alias),
        "Period Review": len(period_review),
        "Value Review": len(value_review),
        "Statement Review": len(statement_review),
        "Formula Checks": len(formula_checks),
        "Formula Pass": len(formula_pass),
        "Formula Review": len(formula_review),
        "Source Review Isolated": len(source_review_out),
        "DB Write": "NO",
        "Canonical": "NO",
        "SSOT": "NO",
    }

    overview = [
        {"Status Lights": def_light("OK" if final_pass else "WARN"), "Gate": "ACCOUNT_PERIOD_VALUE_PREFLIGHT_PASS", "Value": "YES" if final_pass else "REVIEW", "Severity": "OK" if final_pass else "WARN"},
        {"Status Lights": def_light("OK"), "Gate": "SOURCE_RUN", "Value": str(source), "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "INPUT_DRAFT_ROWS", "Value": len(draft_rows), "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "PARSER_READY_ROWS", "Value": len(ready), "Severity": "OK"},
        {"Status Lights": def_light("WARN" if account_alias else "OK"), "Gate": "ACCOUNT_ALIAS_CANDIDATES", "Value": len(account_alias), "Severity": "WARN" if account_alias else "OK"},
        {"Status Lights": def_light("WARN" if period_review else "OK"), "Gate": "PERIOD_REVIEW_ROWS", "Value": len(period_review), "Severity": "WARN" if period_review else "OK"},
        {"Status Lights": def_light("WARN" if value_review else "OK"), "Gate": "VALUE_REVIEW_ROWS", "Value": len(value_review), "Severity": "WARN" if value_review else "OK"},
        {"Status Lights": def_light("OK"), "Gate": "NO_DB_WRITE", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "NO_CANONICAL_MUTATION", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "NO_SSOT_MUTATION", "Value": "YES", "Severity": "OK"},
    ]

    next_steps = [
        {"Status Lights": def_light("WARN"), "Next Step": "Only Parser Ready rows can enter official/historical validation preflight.", "Reason": "Parser Ready means account / period / value / statement passed dry-run parsing.", "Severity": "WARN"},
        {"Status Lights": def_light("WARN"), "Next Step": "Account Alias rows are candidates only; do not patch SSOT yet.", "Reason": "Need frequency + formula + official historical match before append-only SSOT update.", "Severity": "WARN"},
        {"Status Lights": def_light("WARN"), "Next Step": "Still no DB/canonical write.", "Reason": "Historical / formula / unit validation has not been sealed.", "Severity": "WARN"},
    ]

    result = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "system_pass": final_pass,
        "source_run": str(source),
        "counts": counts,
        "outputs": outputs,
    }

    def_write_json(Path(outputs["json"]), result)
    def_write_html(
        Path(outputs["html"]),
        counts,
        [
            ("01 Overview", overview, None),
            ("02 Parser Route Summary", route_summary, None),
            ("03 Next Steps", next_steps, None),
            ("04 Parser Ready Rows", ready, 1200),
            ("05 Account Alias Summary", account_alias_summary, 500),
            ("06 Account Alias Candidate Rows", account_alias, 800),
            ("07 Formula Preflight", formula_checks, 800),
            ("08 Period Review", period_review, 800),
            ("09 Value Review", value_review, 800),
            ("10 Statement Review", statement_review, 800),
            ("11 Source Review Isolation", source_review_out, 800),
        ],
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        def_main()
    except Exception:
        import traceback
        print(traceback.format_exc())
        raise