# -*- coding: utf-8 -*-
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
import os
import re
import sys
import json
import shutil
import importlib.util
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

def def_read_csv(path: str) -> pd.DataFrame:
    if not path or not os.path.exists(path):
        return pd.DataFrame()
    for enc in ["utf-8-sig", "utf-8", "cp950"]:
        try:
            return pd.read_csv(path, dtype=str, encoding=enc).fillna("")
        except Exception:
            pass
    return pd.read_csv(path, dtype=str).fillna("")

def def_write_csv(path: str, df: pd.DataFrame):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")

def def_write_json(path: str, obj: Dict[str, Any]):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def def_load_module(path: str):
    spec = importlib.util.spec_from_file_location("VIS_VRN_FinancialSSOT_v0604", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def def_first(row: Any, cols: List[str]) -> str:
    for c in cols:
        if c in row and str(row.get(c, "")).strip():
            return str(row.get(c, "")).strip()
    return ""

def def_status_lights(sev: str) -> str:
    s = str(sev or "").upper()
    if s in ["OK", "GREEN"]:
        return "🟢 INPUT 🟢 DB 🟢 TRUST"
    if s in ["WARN", "YELLOW", "ORANGE"]:
        return "🟢 INPUT 🟡 DB 🟡 TRUST"
    return "🔴 INPUT 🔴 DB 🔴 TRUST"

def def_format_num(val: Any, unit: str = "") -> str:
    try:
        if val is None or str(val).strip() == "":
            return ""
        x = float(val)
        u = str(unit or "")
        if u == "%":
            return f"{x:,.2f}%"
        if u == "x":
            return f"{x:,.2f}x"
        return f"{x:,.2f}"
    except Exception:
        return ""

def def_numeric_tokens(raw: str) -> List[str]:
    s = str(raw or "").strip()
    if not s:
        return []
    return re.findall(r"\(?-?\d{1,3}(?:,\d{3})*(?:\.\d+)?%?\)?|\(?-?\d+(?:\.\d+)?%?\)?", s)

def def_parse_value(raw: Any) -> Tuple[Any, str, bool]:
    s = str(raw or "").strip()
    if not s:
        return "", "", False

    tokens = [t for t in def_numeric_tokens(s) if re.search(r"\d", t)]
    if len(tokens) >= 2:
        return "", s, True

    t = tokens[0] if tokens else s
    neg = bool(re.match(r"^\(.*\)$", t))
    t = t.strip("()")
    t = t.replace(",", "").replace("%", "")
    t = re.sub(r"[^0-9.\-]", "", t)
    if t in ["", "-", ".", "-."]:
        return "", s, False
    try:
        v = float(t)
        if neg:
            v = -v
        return v, s, False
    except Exception:
        return "", s, False

def def_table_html(title: str, df: pd.DataFrame, max_rows: int = 800) -> str:
    if df is None or df.empty:
        return f"<section class='card'><h2>{title}</h2><div class='empty'>No rows.</div></section>"
    show = df.head(max_rows).copy()
    html = [f"<section class='card'><h2>{title}</h2><div class='table-wrap'><table>"]
    html.append("<thead><tr>")
    for c in show.columns:
        h = str(c).replace("_", " ").title()
        html.append(f"<th>{h}</th>")
    html.append("</tr></thead><tbody>")
    for _, r in show.iterrows():
        html.append("<tr>")
        for c in show.columns:
            val = str(r.get(c, ""))
            cls = "left" if any(k in c.lower() for k in ["filename", "pdf", "reason", "explanation", "raw", "path"]) else ""
            cls = "right" if any(k in c.lower() for k in ["score", "value", "confidence", "rows", "count"]) else cls
            html.append(f"<td class='{cls}'>{val}</td>")
        html.append("</tr>")
    html.append("</tbody></table></div></section>")
    return "\n".join(html)

def def_write_html(path: str, title: str, cards: Dict[str, Any], sections: List[Tuple[str, pd.DataFrame]]):
    css = """
    :root{--bg:#07111f;--panel:#0d1b2f;--line:#1f3557;--text:#eef6ff;--muted:#9fb3c8;--green:#25d366;--yellow:#f5c542;--red:#ff4d5e;--cyan:#42d9ff;}
    *{box-sizing:border-box} body{margin:0;background:radial-gradient(circle at top,#122946 0,#07111f 45%,#050914 100%);font-family:Segoe UI,Arial,'Microsoft JhengHei',sans-serif;color:var(--text);}
    header{padding:26px 32px;border-bottom:1px solid var(--line);position:sticky;top:0;background:rgba(7,17,31,.92);backdrop-filter:blur(14px);z-index:5}
    h1{margin:0;font-size:24px;letter-spacing:.3px}.sub{color:var(--muted);margin-top:8px}
    .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;padding:22px 32px}
    .kpi{background:linear-gradient(180deg,rgba(66,217,255,.12),rgba(13,27,47,.88));border:1px solid var(--line);border-radius:18px;padding:16px;box-shadow:0 12px 28px rgba(0,0,0,.25);transition:.18s transform,.18s border-color}
    .kpi:hover{transform:translateY(-2px);border-color:var(--cyan)}
    .kpi .v{font-size:28px;font-weight:800}.kpi .k{color:var(--muted);font-size:13px;margin-top:6px}
    main{padding:0 32px 34px}.card{background:rgba(13,27,47,.92);border:1px solid var(--line);border-radius:18px;margin:18px 0;padding:18px;box-shadow:0 14px 32px rgba(0,0,0,.26)}
    h2{margin:0 0 14px;font-size:18px}.table-wrap{overflow:auto;max-height:72vh;border-radius:14px;border:1px solid var(--line)}
    table{border-collapse:collapse;width:max-content;min-width:100%;font-size:12px}
    th{position:sticky;top:0;background:#132541;color:#eaf6ff;text-align:center;vertical-align:top;padding:10px;border-bottom:1px solid var(--line);white-space:normal}
    td{padding:9px 10px;border-bottom:1px solid rgba(255,255,255,.07);border-right:1px solid rgba(255,255,255,.04);text-align:center;vertical-align:top;white-space:normal;max-width:360px;word-break:break-word}
    td.left{text-align:left} td.right{text-align:right;font-variant-numeric:tabular-nums}
    tr:hover td{background:rgba(66,217,255,.07)}
    .empty{color:var(--muted);padding:18px}.ok{color:var(--green)}.warn{color:var(--yellow)}.err{color:var(--red)}
    footer{padding:18px 32px;color:var(--muted);border-top:1px solid var(--line)}
    """
    card_html = ["<div class='grid'>"]
    for k, v in cards.items():
        card_html.append(f"<div class='kpi'><div class='v'>{v}</div><div class='k'>{k}</div></div>")
    card_html.append("</div>")
    sec_html = "\n".join([def_table_html(t, d) for t, d in sections])
    html = f"""<!doctype html><html><head><meta charset='utf-8'><title>{title}</title><style>{css}</style></head>
<body><header><h1>VRN · {title}</h1><div class='sub'>INPUT company reports · SSOT v0604 · raw-first · no canonical mutation · no fake fill</div></header>
{''.join(card_html)}<main>{sec_html}</main><footer>Veritas Intelligence Analytics │ AI-Augmented Investment Intelligence for Smarter Decisions and Deeper Insight</footer></body></html>"""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

def def_safe_parquet(path: str, df: pd.DataFrame) -> Tuple[bool, str]:
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        df.astype(str).to_parquet(path, index=False)
        return True, ""
    except Exception as e:
        return False, str(e)

def def_safe_duckdb(path: str, tables: Dict[str, pd.DataFrame]) -> Tuple[bool, str]:
    try:
        import duckdb
        con = duckdb.connect(path)
        con.execute("CREATE SCHEMA IF NOT EXISTS vrn")
        for name, df in tables.items():
            if df is None or df.empty:
                df = pd.DataFrame({"empty_marker": []})
            con.register("tmp_df", df.astype(str))
            con.execute(f"CREATE OR REPLACE TABLE vrn.{name} AS SELECT * FROM tmp_df")
            con.unregister("tmp_df")
        con.close()
        return True, ""
    except Exception as e:
        return False, str(e)

def def_rebind_financial(fin: pd.DataFrame, basic: pd.DataFrame, ssot) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    company = ssot.def_company_registry()
    out_rows = []
    review_rows = []
    quarantine_rows = []

    for _, r in fin.iterrows():
        row = dict(r)
        ticker = def_first(row, ["Ticker", "ticker"])
        filename = def_first(row, ["Filename", "filename"])
        raw_label = def_first(row, ["Data Raw", "Data Official En", "Data", "Canonical Data"])
        old_cat = def_first(row, ["Category Official En", "Category", "Canonical Kind"])
        old_unit = def_first(row, ["Unit"])
        value_raw = def_first(row, ["Value Raw", "Value", "Value Display"])

        reg = company.get(str(ticker), {})
        if not def_first(row, ["Name"]):
            row["Name"] = reg.get("name", "")
        if not def_first(row, ["Yfinance Ticker", "YFinance Ticker"]):
            row["Yfinance Ticker"] = reg.get("yf", "")
        if not def_first(row, ["Bloomberg Ticker"]):
            row["Bloomberg Ticker"] = reg.get("bbg", "")

        m = ssot.def_match_account(raw_label)
        parsed_value, raw_kept, multi_collision = def_parse_value(value_raw)

        if m["matched"]:
            row["Category Official En"] = m["category"]
            row["Data Official En"] = m["official"]
            if not old_unit or old_unit == "ratio":
                row["Unit"] = m["unit"]
            row["SSOT Match Score"] = f'{m["score"]:.2f}'
            row["SSOT Match Reason"] = m["reason"]
            row["SSOT Trust Band"] = m["band"]
        else:
            row["Category Official En"] = old_cat if old_cat and old_cat != "Unmapped" else "Unmapped"
            row["Data Official En"] = raw_label
            row["SSOT Match Score"] = "0.00"
            row["SSOT Match Reason"] = "not found in SSOT v0604"
            row["SSOT Trust Band"] = "RED"

        if parsed_value != "":
            row["Value Numeric"] = parsed_value
            row["Value Display"] = def_format_num(parsed_value, row.get("Unit", ""))
        elif multi_collision:
            row["Value Numeric"] = ""
            row["Value Display"] = ""
            row["Data Quality Reason"] = "MULTI_VALUE_CELL_COLLISION_QUARANTINED"
        else:
            row["Value Numeric"] = def_first(row, ["Value Numeric"])
            row["Value Display"] = def_first(row, ["Value Display"])

        hard_error = False
        reasons = []

        if multi_collision:
            hard_error = True
            reasons.append("multi-value cell collision; table restore needs split")

        if not m["matched"]:
            hard_error = True
            reasons.append("unmapped financial account")

        if not str(row.get("Unit", "")).strip():
            hard_error = True
            reasons.append("missing unit")

        if hard_error:
            row["Severity"] = "ERR"
            row["Status Lights"] = def_status_lights("ERR")
            row["Final Trust Band"] = "RED"
            row["Final Trust Confidence"] = "35.00"
            row["Final Trust Explanation"] = " | ".join(reasons)
            review_rows.append(row.copy())
            if multi_collision:
                quarantine_rows.append(row.copy())
        else:
            score = float(row.get("SSOT Match Score", 80) or 80)
            row["Severity"] = "OK" if score >= 80 else "WARN"
            row["Status Lights"] = def_status_lights(row["Severity"])
            row["Final Trust Band"] = "GREEN" if score >= 80 else "YELLOW"
            row["Final Trust Confidence"] = f"{min(96.0, 70.0 + score * 0.25):.2f}"
            row["Final Trust Explanation"] = "PDF table restore + SSOT v0604 alias + year window + safe numeric parser."
        out_rows.append(row)

    return pd.DataFrame(out_rows).fillna(""), pd.DataFrame(review_rows).fillna(""), pd.DataFrame(quarantine_rows).fillna("")

def def_rebind_basic(basic: pd.DataFrame, ssot) -> pd.DataFrame:
    company = ssot.def_company_registry()
    rows = []
    for _, r in basic.iterrows():
        row = dict(r)
        ticker = def_first(row, ["Ticker", "ticker"])
        reg = company.get(str(ticker), {})
        if ticker and not def_first(row, ["Name"]):
            row["Name"] = reg.get("name", "")
        if ticker and not def_first(row, ["Yfinance Ticker", "YFinance Ticker"]):
            row["Yfinance Ticker"] = reg.get("yf", "")
        if ticker and not def_first(row, ["Bloomberg Ticker"]):
            row["Bloomberg Ticker"] = reg.get("bbg", "")
        row["Status Lights"] = def_status_lights("OK" if def_first(row, ["Name"]) else "WARN")
        rows.append(row)
    return pd.DataFrame(rows).fillna("")

def def_coverage(fin: pd.DataFrame, ssot) -> Tuple[pd.DataFrame, pd.DataFrame]:
    core = ssot.def_core_items()
    rows = []
    actions = []

    if fin.empty:
        return pd.DataFrame(), pd.DataFrame()

    group_cols = ["Filename", "Ticker", "Name", "Category Official En"]
    for keys, g in fin.groupby(group_cols, dropna=False):
        filename, ticker, name, cat = keys
        if cat not in core:
            continue
        found = sorted(set([str(x) for x in g["Data Official En"].tolist() if str(x).strip()]))
        expected = core[cat]
        expected_set = set(expected)
        found_core = [x for x in expected if x in found]
        missing = [x for x in expected if x not in found]
        score = 0 if not expected else round(len(found_core) / len(expected) * 100, 2)
        if score >= 80:
            band = "GREEN"; sev = "OK"; decision = "Core coverage healthy."
        elif score >= 45:
            band = "YELLOW"; sev = "WARN"; decision = "Partial coverage; keep as improvement queue."
        else:
            band = "RED"; sev = "WARN"; decision = "Low disclosed coverage; re-run PDF restore/source-bank extraction if needed."

        row = {
            "Status Lights": def_status_lights(sev),
            "Filename": filename,
            "Ticker": ticker,
            "Name": name,
            "Category": cat,
            "Core Coverage": f"{len(found_core)}/{len(expected)}",
            "Core Coverage Score": f"{score:.2f}%",
            "Core Found Items": " | ".join(found_core),
            "Core Missing Items": " | ".join(missing),
            "Coverage Band": band,
            "Coverage Decision": decision,
            "Severity": sev,
        }
        rows.append(row)
        if sev == "WARN":
            actions.append({
                "Status Lights": def_status_lights("WARN"),
                "Filename": filename,
                "Ticker": ticker,
                "Name": name,
                "Category": cat,
                "Issue Type": "LOW_CORE_COVERAGE",
                "Core Coverage": row["Core Coverage"],
                "Core Missing Items": row["Core Missing Items"],
                "Recommended Next Step": decision,
                "Severity": "WARN",
            })

    return pd.DataFrame(rows).fillna(""), pd.DataFrame(actions).fillna("")

def def_main():
    if len(sys.argv) < 4:
        raise SystemExit("usage: script.py <source_json> <ssot_module> <out_dir>")

    src_json = sys.argv[1]
    ssot_module = sys.argv[2]
    out_dir = sys.argv[3]
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    with open(src_json, "r", encoding="utf-8") as f:
        src = json.load(f)

    outputs = src.get("outputs", {})
    basic_src = outputs.get("basic_csv", "")
    financial_src = outputs.get("financial_csv", "")
    restored_src = outputs.get("restored_csv", "")
    table_src = outputs.get("table_inventory_csv", "")
    review_src = outputs.get("review_csv", "")
    action_src = outputs.get("action_csv", "")

    ssot = def_load_module(ssot_module)
    basic = def_read_csv(basic_src)
    fin = def_read_csv(financial_src)
    restored = def_read_csv(restored_src)
    table_inv = def_read_csv(table_src)
    old_review = def_read_csv(review_src)
    old_action = def_read_csv(action_src)

    basic2 = def_rebind_basic(basic, ssot)
    fin2, review2, quarantine2 = def_rebind_financial(fin, basic2, ssot)
    coverage2, action2 = def_coverage(fin2[fin2.get("Severity", "") != "ERR"].copy(), ssot)

    support_df = pd.DataFrame(json.loads(os.environ.get("VRN_SUPPORT_MATRIX_JSON", "[]")))

    basic_csv = os.path.join(out_dir, "vrn_basicinfo_input_rebind_v0604.csv")
    fin_csv = os.path.join(out_dir, "vrn_financial_candidate_v0604.csv")
    review_csv = os.path.join(out_dir, "vrn_financial_review_v0604.csv")
    quarantine_csv = os.path.join(out_dir, "vrn_financial_quarantine_v0604.csv")
    coverage_csv = os.path.join(out_dir, "vrn_financial_coverage_v0604.csv")
    action_csv = os.path.join(out_dir, "vrn_financial_action_queue_v0604.csv")
    support_csv = os.path.join(out_dir, "vrn_supportive_matrix_v0604.csv")

    for p, d in [
        (basic_csv, basic2),
        (fin_csv, fin2),
        (review_csv, review2),
        (quarantine_csv, quarantine2),
        (coverage_csv, coverage2),
        (action_csv, action2),
        (support_csv, support_df),
    ]:
        def_write_csv(p, d)

    parquet_ok = True
    parquet_errors = {}
    for name, df in [("basic", basic2), ("financial", fin2), ("review", review2), ("coverage", coverage2), ("action", action2)]:
        ok, err = def_safe_parquet(os.path.join(out_dir, f"vrn_{name}_v0604.parquet"), df)
        parquet_ok = parquet_ok and ok
        parquet_errors[name] = err

    duckdb_path = os.path.join(out_dir, "vrn_financial_ssot_input_rebind_v0604.duckdb")
    duckdb_ok, duckdb_error = def_safe_duckdb(duckdb_path, {
        "basicinfo_input_rebind_v0604": basic2,
        "financial_candidate_v0604": fin2,
        "financial_review_v0604": review2,
        "financial_quarantine_v0604": quarantine2,
        "financial_coverage_v0604": coverage2,
        "financial_action_queue_v0604": action2,
        "supportive_matrix_v0604": support_df,
    })

    support_errors = 0
    if not support_df.empty and "Severity" in support_df.columns:
        support_errors = int((support_df["Severity"].astype(str).str.upper() == "ERR").sum())

    hard_review_rows = len(review2)
    quarantine_rows = len(quarantine2)
    system_pass = bool(duckdb_ok and parquet_ok and support_errors == 0 and quarantine_rows == 0)

    overview = pd.DataFrame([
        {"Status Lights": def_status_lights("OK" if system_pass else "WARN"), "Gate": "SYSTEM_PASS", "Value": system_pass, "Severity": "OK" if system_pass else "WARN"},
        {"Status Lights": def_status_lights("OK"), "Gate": "SOURCE_JSON", "Value": src_json, "Severity": "OK"},
        {"Status Lights": def_status_lights("OK"), "Gate": "BASIC_ROWS", "Value": len(basic2), "Severity": "OK"},
        {"Status Lights": def_status_lights("OK"), "Gate": "FINANCIAL_ROWS", "Value": len(fin2), "Severity": "OK"},
        {"Status Lights": def_status_lights("WARN" if len(action2) else "OK"), "Gate": "ACTION_QUEUE_ROWS", "Value": len(action2), "Severity": "WARN" if len(action2) else "OK"},
        {"Status Lights": def_status_lights("ERR" if hard_review_rows else "OK"), "Gate": "REVIEW_ROWS", "Value": hard_review_rows, "Severity": "ERR" if hard_review_rows else "OK"},
        {"Status Lights": def_status_lights("ERR" if quarantine_rows else "OK"), "Gate": "QUARANTINE_ROWS", "Value": quarantine_rows, "Severity": "ERR" if quarantine_rows else "OK"},
        {"Status Lights": def_status_lights("OK" if parquet_ok else "ERR"), "Gate": "PARQUET_OK", "Value": parquet_ok, "Severity": "OK" if parquet_ok else "ERR"},
        {"Status Lights": def_status_lights("OK" if duckdb_ok else "ERR"), "Gate": "DUCKDB_OK", "Value": duckdb_ok, "Severity": "OK" if duckdb_ok else "ERR"},
        {"Status Lights": def_status_lights("OK" if support_errors == 0 else "ERR"), "Gate": "SUPPORT_ERRORS", "Value": support_errors, "Severity": "OK" if support_errors == 0 else "ERR"},
        {"Status Lights": def_status_lights("OK"), "Gate": "NO_CANONICAL_MUTATION", "Value": True, "Severity": "OK"},
    ])

    overview_csv = os.path.join(out_dir, "vrn_overview_matrix_v0604.csv")
    def_write_csv(overview_csv, overview)

    html_path = os.path.join(out_dir, "VRN_Financial_SSOT_Input_Rebind_v0604.html")
    json_path = os.path.join(out_dir, "vrn_financial_ssot_input_rebind_v0604.json")

    cards = {
        "System Pass": str(system_pass),
        "Basic Rows": str(len(basic2)),
        "Financial Rows": str(len(fin2)),
        "Review Rows": str(hard_review_rows),
        "Quarantine": str(quarantine_rows),
        "Action Queue": str(len(action2)),
        "DuckDB OK": str(duckdb_ok),
        "Parquet OK": str(parquet_ok),
    }

    def_write_html(
        html_path,
        "VeritasReportNova Financial SSOT Input Rebind v0.6.4",
        cards,
        [
            ("01 Overview", overview),
            ("02 BasicInfo Rebind", basic2),
            ("03 Financial Candidate", fin2),
            ("04 Review", review2),
            ("05 Quarantine", quarantine2),
            ("06 Coverage", coverage2),
            ("07 Action Queue", action2),
            ("08 Supportive", support_df),
        ],
    )

    result = {
        "version": "VRN_FINANCIAL_SSOT_INPUT_REBIND_V0604",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "system_pass": system_pass,
        "mode": "INPUT_RESTORE_FINANCIAL_SSOT_REBIND_NO_CANONICAL_MUTATION",
        "source_json": src_json,
        "source_outputs": outputs,
        "counts": {
            "basic_rows": len(basic2),
            "financial_rows": len(fin2),
            "review_rows": hard_review_rows,
            "quarantine_rows": quarantine_rows,
            "coverage_rows": len(coverage2),
            "action_rows": len(action2),
            "support_errors": support_errors,
        },
        "parquet_ok": parquet_ok,
        "parquet_errors": parquet_errors,
        "duckdb_ok": duckdb_ok,
        "duckdb_error": duckdb_error,
        "outputs": {
            "html": html_path,
            "json": json_path,
            "overview_csv": overview_csv,
            "basic_csv": basic_csv,
            "financial_csv": fin_csv,
            "review_csv": review_csv,
            "quarantine_csv": quarantine_csv,
            "coverage_csv": coverage_csv,
            "action_csv": action_csv,
            "support_csv": support_csv,
            "duckdb": duckdb_path,
            "ssot_module": ssot_module,
        },
        "rule_lock": [
            "No canonical mutation.",
            "No stable mutation.",
            "No fake fill.",
            "Company name / YFinance ticker / Bloomberg ticker are filled by ticker registry only when blank.",
            "Financial account matching is raw-first SSOT v0604 alias mapping.",
            "Multi-value cell collisions are quarantined, not silently converted.",
            "Coverage action queue is improvement work, not system failure by itself.",
        ],
    }
    def_write_json(json_path, result)

    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    def_main()