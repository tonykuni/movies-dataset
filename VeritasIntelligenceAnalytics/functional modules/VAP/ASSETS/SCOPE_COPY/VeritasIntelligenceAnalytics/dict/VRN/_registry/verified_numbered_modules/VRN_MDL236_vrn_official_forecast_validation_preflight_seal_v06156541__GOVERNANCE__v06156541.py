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


VERSION = "VRN_OFFICIAL_FORECAST_VALIDATION_PREFLIGHT_SEAL_V06156541"


def def_clean(x: Any) -> str:
    s = "" if x is None else str(x)
    s = s.replace("\u3000", " ").replace("\r", "\n")
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()


def def_norm(x: Any) -> str:
    return re.sub(r"[\s_\-\/\(\)（）\[\]【】{}:：,，.。&+%]+", "", str(x or "").lower())


def def_float(x: Any, default: Any = None) -> Any:
    s = def_clean(x).replace(",", "").replace("%", "")
    if s in ["", "-", "—", "–", "NA", "N/A", "nan", "None"]:
        return default
    try:
        return float(s)
    except Exception:
        return default


def def_light(sev: str) -> str:
    s = str(sev or "").upper()
    if s in ["OK", "PASS", "YES", "READY", "WORK_ORDER_READY", "FORMULA_PASS", "SEALED"]:
        return "🟢 INPUT 🟢 DB 🟢 TRUST"
    if s in ["WARN", "REVIEW", "QUEUE", "PREFLIGHT", "PLAN", "NETWORK_LOCKED"]:
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
            cls = "left" if any(x in k.lower() for x in ["filename", "account", "route", "reason", "source", "formula", "preferred", "evidence", "endpoint", "url"]) else "center"
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
    doc = f"""<!doctype html><html><head><meta charset="utf-8"><title>VRN Official Forecast Validation Preflight Seal v06156541</title><style>{css}</style></head>
<body><header><h1>VRN · Official + Forecast Validation Preflight Seal v0.6.15.6.5.4.1</h1>
<div class="sub">official historical work order · forecast formula consistency · network locked · no DB / canonical / SSOT</div></header>
<div class="grid">{cards}</div><main>{body}</main></body></html>"""
    path.write_text(doc, encoding="utf-8")


def def_make_actual_work_order(candidates: list[dict]) -> list[dict]:
    out = []
    for i, r in enumerate(candidates, 1):
        ticker = def_get(r, ["ticker"])
        year = def_get(r, ["period year"])
        account_key = def_get(r, ["account key"])
        statement = def_get(r, ["statement"])

        if statement == "BALANCE_SHEET":
            official_table_hint = "資產負債表 / Balance Sheet"
        elif statement == "INCOME_STATEMENT":
            official_table_hint = "綜合損益表 / Income Statement"
        elif statement == "CASH_FLOW":
            official_table_hint = "現金流量表 / Cash Flow Statement"
        elif statement == "RATIO_ANALYSIS":
            official_table_hint = "derived ratio from official statement values"
        else:
            official_table_hint = "statement review required"

        out.append({
            "Status Lights": def_light("OK"),
            "official work order id": f"VRN_OFFICIAL_ACTUAL_{i:04d}",
            "ticker": ticker,
            "filename": def_get(r, ["filename"]),
            "statement": statement,
            "official table hint": official_table_hint,
            "account raw": def_get(r, ["account raw"]),
            "account canonical": def_get(r, ["account canonical"]),
            "account key": account_key,
            "period year": year,
            "period type": def_get(r, ["period type"]),
            "report value": def_get(r, ["value numeric"]),
            "unit": def_get(r, ["unit"]),
            "preferred official source": "MOPS/TWSE/TPEX official financial statement history",
            "fetch key": f"{ticker}|{year}|{statement}|{account_key}",
            "network execution now": "NO",
            "validation route": "OFFICIAL_HISTORICAL_WORK_ORDER_READY",
            "db write": "NO",
            "canonical mutation": "NO",
            "ssot mutation": "NO",
            "Severity": "OK",
        })
    return out


def def_group_candidates(candidates: list[dict]) -> tuple[dict, dict]:
    grouped = defaultdict(dict)
    meta = {}
    for r in candidates:
        key = (
            def_get(r, ["staging table id"]),
            def_get(r, ["filename"]),
            def_get(r, ["ticker"]),
            def_get(r, ["statement"]),
            def_get(r, ["period year"]),
            def_get(r, ["period type"]),
        )
        account_key = def_get(r, ["account key"])
        val = def_float(def_get(r, ["value numeric"]))
        if account_key and val is not None:
            grouped[key][account_key] = val
            meta.setdefault(key, r)
    return grouped, meta


def def_formula_checks(candidates: list[dict]) -> list[dict]:
    grouped, meta = def_group_candidates(candidates)
    out = []

    def add_check(key, name, lhs_key, rhs_keys, fn, tolerance):
        vals = grouped[key]
        lhs = vals.get(lhs_key)
        rhs_values = [vals.get(k) for k in rhs_keys]
        if lhs is None or any(v is None for v in rhs_values):
            return
        rhs = fn(rhs_values)
        diff = abs(float(lhs) - float(rhs))
        ok = diff <= tolerance
        m = meta[key]
        out.append({
            "Status Lights": def_light("OK" if ok else "WARN"),
            "formula check": name,
            "filename": def_get(m, ["filename"]),
            "ticker": def_get(m, ["ticker"]),
            "statement": def_get(m, ["statement"]),
            "period year": def_get(m, ["period year"]),
            "period type": def_get(m, ["period type"]),
            "lhs account": lhs_key,
            "lhs value": lhs,
            "rhs accounts": " + ".join(rhs_keys),
            "rhs value": rhs,
            "diff": round(diff, 4),
            "tolerance": tolerance,
            "formula route": "FORMULA_PASS" if ok else "FORMULA_REVIEW",
            "evidence type": "REPORT_INTERNAL_FORMULA_PREFLIGHT",
            "db write": "NO",
            "canonical mutation": "NO",
            "ssot mutation": "NO",
            "Severity": "OK" if ok else "WARN",
        })

    for key in grouped:
        add_check(key, "current_assets_components", "current_assets", ["cash_and_equivalents", "accounts_receivable", "inventories", "other_current_assets"], sum, 10.0)
        add_check(key, "total_assets_components", "total_assets", ["current_assets", "fixed_assets", "investments", "goodwill", "intangible_assets", "other_non_current_assets"], sum, 10.0)
        add_check(key, "current_liabilities_components", "current_liabilities", ["short_term_debt", "accounts_payable", "taxes_payable", "other_current_liabilities"], sum, 10.0)
        add_check(key, "gross_profit_check", "gross_profit", ["revenue", "cogs"], lambda x: x[0] - x[1], 10.0)
        add_check(key, "operating_income_check", "operating_income", ["gross_profit", "operating_expenses"], lambda x: x[0] - x[1], 10.0)

    return out


def def_build_validation_summary(candidates: list[dict]) -> list[dict]:
    counter = Counter()
    for r in candidates:
        key = (
            def_get(r, ["ticker"]),
            def_get(r, ["statement"]),
            def_get(r, ["period type"]),
            def_get(r, ["period year"]),
        )
        counter[key] += 1

    out = []
    for i, (key, n) in enumerate(sorted(counter.items(), key=lambda x: (-x[1], x[0])), 1):
        ticker, statement, ptype, year = key
        if ptype == "ACTUAL":
            route = "OFFICIAL_HISTORICAL_VALIDATION_WORK_ORDER"
            source = "MOPS/TWSE/TPEX official historical financials"
            sev = "OK"
        elif ptype == "FORECAST":
            route = "REPORT_INTERNAL_FORMULA_VALIDATION_PREFLIGHT"
            source = "report internal formula and trend consistency"
            sev = "OK"
        else:
            route = "PERIOD_TYPE_REVIEW"
            source = "period mapping review"
            sev = "WARN"

        out.append({
            "Status Lights": def_light(sev),
            "summary id": f"VRN_VALIDATION_SUMMARY_{i:04d}",
            "ticker": ticker,
            "statement": statement,
            "period type": ptype,
            "period year": year,
            "candidate rows": n,
            "validation route": route,
            "preferred evidence source": source,
            "network now": "NO",
            "db write": "NO",
            "canonical mutation": "NO",
            "ssot mutation": "NO",
            "Severity": sev,
        })
    return out


def def_build_next_network_plan(actual_work_order: list[dict]) -> list[dict]:
    groups = Counter()
    example = {}
    for r in actual_work_order:
        key = (
            def_get(r, ["ticker"]),
            def_get(r, ["period year"]),
            def_get(r, ["statement"]),
        )
        groups[key] += 1
        example.setdefault(key, r)

    out = []
    for i, (key, n) in enumerate(sorted(groups.items(), key=lambda x: (-x[1], x[0])), 1):
        ticker, year, statement = key
        if statement == "BALANCE_SHEET":
            route = "FETCH_OFFICIAL_BALANCE_SHEET_HISTORY"
        elif statement == "INCOME_STATEMENT":
            route = "FETCH_OFFICIAL_INCOME_STATEMENT_HISTORY"
        elif statement == "CASH_FLOW":
            route = "FETCH_OFFICIAL_CASH_FLOW_HISTORY"
        else:
            route = "FETCH_DERIVED_RATIO_SOURCE_VALUES"

        out.append({
            "Status Lights": def_light("NETWORK_LOCKED"),
            "network plan id": f"VRN_NETWORK_PLAN_{i:04d}",
            "ticker": ticker,
            "period year": year,
            "statement": statement,
            "work order rows": n,
            "next fetch route": route,
            "network locked now": "YES",
            "requires next run flag": "ENABLE_NETWORK_TRUE",
            "db write": "NO",
            "canonical mutation": "NO",
            "ssot mutation": "NO",
            "Severity": "WARN",
        })
    return out


def def_main() -> None:
    if len(sys.argv) < 4:
        raise SystemExit("usage: py <run_root> <run_dir> <enable_network>")

    run_root = Path(sys.argv[1])
    run_dir = Path(sys.argv[2])
    enable_network = str(sys.argv[3]).lower() in ["1", "true", "yes", "y"]
    run_dir.mkdir(parents=True, exist_ok=True)

    source = def_find_latest_dir(run_root, "VRN_PARSER_REPAIR_ROUTER_VALIDATION_GATE_V0615653")
    if not source:
        raise RuntimeError("Cannot find latest VRN_PARSER_REPAIR_ROUTER_VALIDATION_GATE_V0615653 run.")

    candidate_csv = source / "vrn_official_validation_candidates_v0615653.csv"
    alias_csv = source / "vrn_account_alias_hotspots_v0615653.csv"
    period_csv = source / "vrn_period_hotspots_v0615653.csv"
    statement_csv = source / "vrn_statement_hotspots_v0615653.csv"

    candidates = [r for r in def_read_csv(candidate_csv) if "empty_marker" not in r]
    alias_hotspots = [r for r in def_read_csv(alias_csv) if "empty_marker" not in r]
    period_hotspots = [r for r in def_read_csv(period_csv) if "empty_marker" not in r]
    statement_hotspots = [r for r in def_read_csv(statement_csv) if "empty_marker" not in r]

    actual = [r for r in candidates if def_get(r, ["period type"]).upper() == "ACTUAL"]
    forecast = [r for r in candidates if def_get(r, ["period type"]).upper() == "FORECAST"]

    actual_work_order = def_make_actual_work_order(actual)
    forecast_formula = def_formula_checks(forecast)
    all_formula = def_formula_checks(candidates)

    formula_pass = [r for r in all_formula if def_get(r, ["formula route"]) == "FORMULA_PASS"]
    formula_review = [r for r in all_formula if def_get(r, ["formula route"]) != "FORMULA_PASS"]

    validation_summary = def_build_validation_summary(candidates)
    network_plan = def_build_next_network_plan(actual_work_order)

    hard_rules = [
        {"Status Lights": def_light("OK"), "Rule": "NO_NETWORK_THIS_RUN" if not enable_network else "NETWORK_FLAG_TRUE_BUT_EXECUTION_STILL_LOCKED", "Reason": "This version only prepares network plan; actual fetching belongs to next isolated run.", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Rule": "NO_DB_WRITE", "Reason": "Candidate rows are not final facts.", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Rule": "NO_CANONICAL_MUTATION", "Reason": "Historical validation has not executed.", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Rule": "NO_SSOT_MUTATION", "Reason": "Alias hotspots are review only.", "Severity": "OK"},
    ]

    outputs = {
        "html": str(run_dir / "VRN_Official_Forecast_Validation_Preflight_Seal_v06156541.html"),
        "json": str(run_dir / "vrn_official_forecast_validation_preflight_seal_v06156541.json"),
        "actual_official_work_order_csv": str(run_dir / "vrn_actual_official_validation_work_order_v06156541.csv"),
        "forecast_formula_preflight_csv": str(run_dir / "vrn_forecast_formula_preflight_v06156541.csv"),
        "all_formula_preflight_csv": str(run_dir / "vrn_all_formula_preflight_v06156541.csv"),
        "formula_review_csv": str(run_dir / "vrn_formula_review_v06156541.csv"),
        "validation_summary_csv": str(run_dir / "vrn_validation_summary_v06156541.csv"),
        "next_network_plan_csv": str(run_dir / "vrn_next_official_network_plan_v06156541.csv"),
        "alias_hotspots_passthrough_csv": str(run_dir / "vrn_alias_hotspots_passthrough_v06156541.csv"),
        "period_hotspots_passthrough_csv": str(run_dir / "vrn_period_hotspots_passthrough_v06156541.csv"),
        "statement_hotspots_passthrough_csv": str(run_dir / "vrn_statement_hotspots_passthrough_v06156541.csv"),
        "hard_rules_csv": str(run_dir / "vrn_validation_preflight_hard_rules_v06156541.csv"),
    }

    def_write_csv(Path(outputs["actual_official_work_order_csv"]), actual_work_order)
    def_write_csv(Path(outputs["forecast_formula_preflight_csv"]), forecast_formula)
    def_write_csv(Path(outputs["all_formula_preflight_csv"]), all_formula)
    def_write_csv(Path(outputs["formula_review_csv"]), formula_review)
    def_write_csv(Path(outputs["validation_summary_csv"]), validation_summary)
    def_write_csv(Path(outputs["next_network_plan_csv"]), network_plan)
    def_write_csv(Path(outputs["alias_hotspots_passthrough_csv"]), alias_hotspots)
    def_write_csv(Path(outputs["period_hotspots_passthrough_csv"]), period_hotspots)
    def_write_csv(Path(outputs["statement_hotspots_passthrough_csv"]), statement_hotspots)
    def_write_csv(Path(outputs["hard_rules_csv"]), hard_rules)

    final_pass = len(candidates) > 0 and len(actual_work_order) > 0 and len(network_plan) > 0

    counts = {
        "Final": "PASS" if final_pass else "REVIEW",
        "Input Candidates": len(candidates),
        "Actual Work Orders": len(actual_work_order),
        "Forecast Rows": len(forecast),
        "Formula Checks": len(all_formula),
        "Formula Pass": len(formula_pass),
        "Formula Review": len(formula_review),
        "Network Plans": len(network_plan),
        "Alias Hotspots": len(alias_hotspots),
        "Period Hotspots": len(period_hotspots),
        "Statement Hotspots": len(statement_hotspots),
        "Network": "NO",
        "DB Write": "NO",
        "Canonical": "NO",
        "SSOT": "NO",
    }

    overview = [
        {"Status Lights": def_light("OK" if final_pass else "WARN"), "Gate": "OFFICIAL_FORECAST_PREFLIGHT_SEAL_PASS", "Value": "YES" if final_pass else "REVIEW", "Severity": "OK" if final_pass else "WARN"},
        {"Status Lights": def_light("OK"), "Gate": "SOURCE_RUN", "Value": str(source), "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "INPUT_CANDIDATES", "Value": len(candidates), "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "ACTUAL_WORK_ORDERS", "Value": len(actual_work_order), "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "FORECAST_ROWS", "Value": len(forecast), "Severity": "OK"},
        {"Status Lights": def_light("WARN" if formula_review else "OK"), "Gate": "FORMULA_REVIEW", "Value": len(formula_review), "Severity": "WARN" if formula_review else "OK"},
        {"Status Lights": def_light("OK"), "Gate": "NETWORK_EXECUTION_THIS_RUN", "Value": "NO", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "NO_DB_WRITE", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "NO_CANONICAL_MUTATION", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "NO_SSOT_MUTATION", "Value": "YES", "Severity": "OK"},
    ]

    next_steps = [
        {"Status Lights": def_light("WARN"), "Next Step": "Run isolated official fetch dry run using next_network_plan only.", "Reason": "Network must be isolated from parser/canonical flow.", "Severity": "WARN"},
        {"Status Lights": def_light("WARN"), "Next Step": "Use Formula Review to improve formula coverage before final matrix.", "Reason": "Forecast rows are validated by internal table consistency.", "Severity": "WARN"},
        {"Status Lights": def_light("WARN"), "Next Step": "Keep alias/period/statement hotspots outside canonical.", "Reason": "They are repair queues, not facts.", "Severity": "WARN"},
    ]

    result = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "system_pass": final_pass,
        "source_run": str(source),
        "enable_network_arg": enable_network,
        "network_executed": False,
        "counts": counts,
        "outputs": outputs,
    }

    def_write_json(Path(outputs["json"]), result)
    def_write_html(
        Path(outputs["html"]),
        counts,
        [
            ("01 Overview", overview, None),
            ("02 Next Steps", next_steps, None),
            ("03 Validation Summary", validation_summary, 1000),
            ("04 Actual Official Validation Work Order", actual_work_order, 1200),
            ("05 Next Official Network Plan", network_plan, 1000),
            ("06 Forecast Formula Preflight", forecast_formula, 1000),
            ("07 All Formula Preflight", all_formula, 1000),
            ("08 Formula Review", formula_review, 1000),
            ("09 Alias Hotspots Passthrough", alias_hotspots, 500),
            ("10 Period Hotspots Passthrough", period_hotspots, 500),
            ("11 Statement Hotspots Passthrough", statement_hotspots, 500),
            ("12 Hard Rules", hard_rules, None),
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