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


VERSION = "VRN_PARSER_REPAIR_ROUTER_VALIDATION_GATE_V0615653"


def def_clean(x: Any) -> str:
    s = "" if x is None else str(x)
    s = s.replace("\u3000", " ").replace("\r", "\n")
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()


def def_flat(x: Any) -> str:
    return re.sub(r"\s+", " ", def_clean(x)).strip()


def def_norm(x: Any) -> str:
    return re.sub(r"[\s_\-\/\(\)（）\[\]【】{}:：,，.。&+%]+", "", str(x or "").lower())


def def_int(x: Any, default: int = 0) -> int:
    try:
        return int(float(str(x).replace(",", "").replace("%", "").strip()))
    except Exception:
        return default


def def_float(x: Any, default: Any = "") -> Any:
    s = def_flat(x).replace(",", "").replace("%", "")
    if s in ["", "-", "—", "–", "NA", "N/A", "nan", "None"]:
        return default
    try:
        return float(s)
    except Exception:
        return default


def def_light(sev: str) -> str:
    s = str(sev or "").upper()
    if s in ["OK", "PASS", "YES", "READY", "VALIDATION_READY", "ROUTED"]:
        return "🟢 INPUT 🟢 DB 🟢 TRUST"
    if s in ["WARN", "REVIEW", "QUEUE", "ALIAS", "PERIOD", "ROUTER"]:
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


def def_pick_parser_source(run_root: Path) -> tuple[Path, Path, str]:
    src5652 = def_find_latest_dir(run_root, "VRN_PERIOD_ALIAS_LEARNING_PREFLIGHT_V0615652")
    if src5652:
        csv_path = src5652 / "vrn_repaired_parser_matrix_v0615652.csv"
        if csv_path.exists():
            return src5652, csv_path, "V0615652_REPAIRED"

    src5651 = def_find_latest_dir(run_root, "VRN_ACCOUNT_PERIOD_VALUE_PARSER_PREFLIGHT_V0615651")
    if src5651:
        csv_path = src5651 / "vrn_account_period_value_parser_matrix_v0615651.csv"
        if csv_path.exists():
            return src5651, csv_path, "V0615651_BASE"

    raise RuntimeError("Cannot find parser source v0615652 or v0615651.")


def def_route_of(row: dict, source_mode: str) -> str:
    if source_mode == "V0615652_REPAIRED":
        return def_get(row, ["parser route repaired"]) or def_get(row, ["parser route"])
    return def_get(row, ["parser route"])


def def_account_raw(row: dict, source_mode: str) -> str:
    return def_get(row, ["account raw"])


def def_account_key(row: dict, source_mode: str) -> str:
    if source_mode == "V0615652_REPAIRED":
        return def_get(row, ["account key repaired"]) or def_get(row, ["account key"])
    return def_get(row, ["account key"])


def def_account_canonical(row: dict, source_mode: str) -> str:
    if source_mode == "V0615652_REPAIRED":
        return def_get(row, ["account canonical repaired"]) or def_get(row, ["account canonical"])
    return def_get(row, ["account canonical"])


def def_period_year(row: dict, source_mode: str) -> str:
    if source_mode == "V0615652_REPAIRED":
        return def_get(row, ["period year repaired"]) or def_get(row, ["period year"])
    return def_get(row, ["period year"])


def def_period_type(row: dict, source_mode: str) -> str:
    if source_mode == "V0615652_REPAIRED":
        return def_get(row, ["period type repaired"]) or def_get(row, ["period type"])
    return def_get(row, ["period type"])


def def_statement(row: dict, source_mode: str) -> str:
    if source_mode == "V0615652_REPAIRED":
        return def_get(row, ["statement normalized repaired"]) or def_get(row, ["statement normalized"])
    return def_get(row, ["statement normalized"])


def def_value_numeric(row: dict, source_mode: str) -> Any:
    if source_mode == "V0615652_REPAIRED":
        return def_get(row, ["value numeric repaired"]) or def_get(row, ["value numeric parsed"]) or def_get(row, ["value numeric"])
    return def_get(row, ["value numeric parsed"]) or def_get(row, ["value numeric"])


def def_make_validation_candidate(row: dict, source_mode: str) -> dict:
    account_key = def_account_key(row, source_mode)
    period_year = def_period_year(row, source_mode)
    period_type = def_period_type(row, source_mode)
    statement = def_statement(row, source_mode)
    value_num = def_value_numeric(row, source_mode)

    route = "OFFICIAL_VALIDATION_CANDIDATE"
    severity = "OK"
    reason = "parser ready; validation preflight allowed"

    if not account_key or not period_year or value_num == "":
        route = "OFFICIAL_VALIDATION_BLOCKED"
        severity = "WARN"
        reason = "missing account_key / period_year / value"

    return {
        "Status Lights": def_light(severity),
        "validation candidate id": def_get(row, ["draft row id"]) or f"VALIDATION_CANDIDATE_{abs(hash(str(row))) % 999999}",
        "source mode": source_mode,
        "staging table id": def_get(row, ["staging table id"]),
        "filename": def_get(row, ["filename"]),
        "ticker": def_get(row, ["ticker"]),
        "name": def_get(row, ["name"]),
        "page": def_get(row, ["page"]),
        "table no": def_get(row, ["table no"]),
        "statement": statement,
        "account raw": def_account_raw(row, source_mode),
        "account canonical": def_account_canonical(row, source_mode),
        "account key": account_key,
        "period year": period_year,
        "period type": period_type,
        "value numeric": value_num,
        "unit": def_get(row, ["unit repaired"]) or def_get(row, ["unit"]),
        "validation route": route,
        "validation reason": reason,
        "official source required": "MOPS/TWSE/TPEX historical for ACTUAL; report internal formula for FORECAST",
        "db write": "NO",
        "canonical mutation": "NO",
        "ssot mutation": "NO",
        "Severity": severity,
    }


def def_build_hotspot(rows: list[dict], source_mode: str, keyword: str) -> list[dict]:
    counter = Counter()
    examples = {}
    for r in rows:
        route = def_route_of(r, source_mode)
        if keyword not in route:
            continue
        if keyword == "ACCOUNT_ALIAS_CANDIDATE":
            k = def_account_raw(r, source_mode)
        elif keyword == "PERIOD_REVIEW":
            k = "|".join([
                def_get(r, ["filename"]),
                def_get(r, ["page"]),
                def_get(r, ["table no"]),
                def_get(r, ["col index"]),
                def_get(r, ["period raw"]) or def_get(r, ["period raw repaired"]) or "",
            ])
        elif keyword == "STATEMENT_REVIEW":
            k = "|".join([
                def_get(r, ["filename"]),
                def_get(r, ["page"]),
                def_get(r, ["table no"]),
                def_account_raw(r, source_mode),
            ])
        else:
            k = route
        counter[k] += 1
        examples.setdefault(k, r)

    out = []
    for k, v in sorted(counter.items(), key=lambda x: (-x[1], x[0]))[:800]:
        ex = examples[k]
        if keyword == "ACCOUNT_ALIAS_CANDIDATE":
            route = "SSOT_ALIAS_CANDIDATE_PACK_ONLY"
            action = "review alias frequency; do not patch until official/formula validation passes"
            key_cols = {"account raw": k}
        elif keyword == "PERIOD_REVIEW":
            route = "PERIOD_HEADER_REPAIR_QUEUE"
            action = "inspect table header by filename/page/table/col; likely multi-row header propagation needed"
            parts = k.split("|")
            key_cols = {
                "filename": parts[0] if len(parts) > 0 else "",
                "page": parts[1] if len(parts) > 1 else "",
                "table no": parts[2] if len(parts) > 2 else "",
                "col index": parts[3] if len(parts) > 3 else "",
                "period raw": parts[4] if len(parts) > 4 else "",
            }
        elif keyword == "STATEMENT_REVIEW":
            route = "STATEMENT_CLASSIFIER_REVIEW_QUEUE"
            action = "map account/table context to statement type"
            parts = k.split("|")
            key_cols = {
                "filename": parts[0] if len(parts) > 0 else "",
                "page": parts[1] if len(parts) > 1 else "",
                "table no": parts[2] if len(parts) > 2 else "",
                "account raw": parts[3] if len(parts) > 3 else "",
            }
        else:
            route = "REVIEW"
            action = "review"
            key_cols = {"key": k}

        row = {
            "Status Lights": def_light("WARN"),
            "hotspot type": keyword,
            "rows": v,
            "repair route": route,
            "recommended action": action,
            "db write": "NO",
            "canonical mutation": "NO",
            "ssot mutation": "NO",
            "Severity": "WARN",
        }
        row.update(key_cols)
        out.append(row)
    return out


def def_build_official_validation_plan(candidates: list[dict]) -> list[dict]:
    groups = defaultdict(int)
    examples = {}
    for r in candidates:
        key = (
            r.get("ticker", ""),
            r.get("statement", ""),
            r.get("period type", ""),
            r.get("period year", ""),
        )
        groups[key] += 1
        examples.setdefault(key, r)

    out = []
    for i, (k, count) in enumerate(sorted(groups.items(), key=lambda x: (-x[1], x[0])), 1):
        ticker, statement, ptype, year = k
        ex = examples[k]
        if ptype == "ACTUAL":
            route = "OFFICIAL_HISTORICAL_VALIDATION_PREFLIGHT"
            source = "MOPS/TWSE/TPEX official historical financial data"
        elif ptype == "FORECAST":
            route = "REPORT_FORMULA_INTERNAL_VALIDATION_PREFLIGHT"
            source = "report table internal formula / trend consistency"
        else:
            route = "PERIOD_TYPE_REVIEW_BEFORE_VALIDATION"
            source = "period mapping review"

        out.append({
            "Status Lights": def_light("OK" if "VALIDATION_PREFLIGHT" in route else "WARN"),
            "plan id": f"VRN_VALIDATION_PLAN_{i:04d}",
            "ticker": ticker,
            "filename example": ex.get("filename", ""),
            "statement": statement,
            "period type": ptype,
            "period year": year,
            "candidate rows": count,
            "validation plan route": route,
            "preferred evidence source": source,
            "network now": "NO",
            "db write": "NO",
            "canonical mutation": "NO",
            "ssot mutation": "NO",
            "Severity": "OK" if "VALIDATION_PREFLIGHT" in route else "WARN",
        })
    return out


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
            cls = "left" if any(x in k.lower() for x in ["filename", "account", "period", "route", "reason", "source", "action", "evidence"]) else "center"
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
    doc = f"""<!doctype html><html><head><meta charset="utf-8"><title>VRN Parser Repair Router Validation Gate v0615653</title><style>{css}</style></head>
<body><header><h1>VRN · Parser Repair Router + Official Validation Candidate Gate v0.6.15.6.5.3</h1>
<div class="sub">router only · validation candidate gate · alias/period hotspots · no DB/canonical/SSOT write</div></header>
<div class="grid">{cards}</div><main>{body}</main></body></html>"""
    path.write_text(doc, encoding="utf-8")


def def_main() -> None:
    if len(sys.argv) < 3:
        raise SystemExit("usage: py <run_root> <run_dir>")

    run_root = Path(sys.argv[1])
    run_dir = Path(sys.argv[2])
    run_dir.mkdir(parents=True, exist_ok=True)

    source_dir, parser_csv, source_mode = def_pick_parser_source(run_root)
    rows = [r for r in def_read_csv(parser_csv) if "empty_marker" not in r]

    ready_rows = [r for r in rows if def_route_of(r, source_mode) == "PARSER_READY"]
    official_candidates = [def_make_validation_candidate(r, source_mode) for r in ready_rows]
    official_candidates_ready = [r for r in official_candidates if r.get("validation route") == "OFFICIAL_VALIDATION_CANDIDATE"]

    alias_hotspots = def_build_hotspot(rows, source_mode, "ACCOUNT_ALIAS_CANDIDATE")
    period_hotspots = def_build_hotspot(rows, source_mode, "PERIOD_REVIEW")
    statement_hotspots = def_build_hotspot(rows, source_mode, "STATEMENT_REVIEW")
    validation_plan = def_build_official_validation_plan(official_candidates_ready)

    route_summary = []
    for k, v in sorted(Counter(def_route_of(r, source_mode) for r in rows).items(), key=lambda x: (-x[1], x[0])):
        sev = "OK" if k == "PARSER_READY" else "WARN"
        route_summary.append({
            "Status Lights": def_light(sev),
            "parser route": k,
            "rows": v,
            "rate": f"{(v / max(len(rows), 1)) * 100:.2f}%",
            "Severity": sev,
        })

    hard_rules = [
        {"Status Lights": def_light("OK"), "Rule": "No DB write", "Reason": "This is validation gate only.", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Rule": "No SSOT patch", "Reason": "Alias hotspot is candidate pack only.", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Rule": "No canonical mutation", "Reason": "Official/historical validation has not run.", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Rule": "No network now", "Reason": "This run only prepares validation plan.", "Severity": "OK"},
    ]

    outputs = {
        "html": str(run_dir / "VRN_Parser_Repair_Router_Validation_Gate_v0615653.html"),
        "json": str(run_dir / "vrn_parser_repair_router_validation_gate_v0615653.json"),
        "official_validation_candidates_csv": str(run_dir / "vrn_official_validation_candidates_v0615653.csv"),
        "official_validation_plan_csv": str(run_dir / "vrn_official_validation_plan_v0615653.csv"),
        "alias_hotspots_csv": str(run_dir / "vrn_account_alias_hotspots_v0615653.csv"),
        "period_hotspots_csv": str(run_dir / "vrn_period_hotspots_v0615653.csv"),
        "statement_hotspots_csv": str(run_dir / "vrn_statement_hotspots_v0615653.csv"),
        "route_summary_csv": str(run_dir / "vrn_parser_route_summary_v0615653.csv"),
        "hard_rules_csv": str(run_dir / "vrn_validation_gate_hard_rules_v0615653.csv"),
    }

    def_write_csv(Path(outputs["official_validation_candidates_csv"]), official_candidates_ready)
    def_write_csv(Path(outputs["official_validation_plan_csv"]), validation_plan)
    def_write_csv(Path(outputs["alias_hotspots_csv"]), alias_hotspots)
    def_write_csv(Path(outputs["period_hotspots_csv"]), period_hotspots)
    def_write_csv(Path(outputs["statement_hotspots_csv"]), statement_hotspots)
    def_write_csv(Path(outputs["route_summary_csv"]), route_summary)
    def_write_csv(Path(outputs["hard_rules_csv"]), hard_rules)

    final_pass = len(official_candidates_ready) > 0

    counts = {
        "Final": "PASS" if final_pass else "REVIEW",
        "Source Mode": source_mode,
        "Input Rows": len(rows),
        "Parser Ready": len(ready_rows),
        "Official Candidates": len(official_candidates_ready),
        "Validation Plans": len(validation_plan),
        "Alias Hotspots": len(alias_hotspots),
        "Period Hotspots": len(period_hotspots),
        "Statement Hotspots": len(statement_hotspots),
        "DB Write": "NO",
        "Canonical": "NO",
        "SSOT": "NO",
    }

    overview = [
        {"Status Lights": def_light("OK" if final_pass else "WARN"), "Gate": "VALIDATION_CANDIDATE_GATE_PASS", "Value": "YES" if final_pass else "REVIEW", "Severity": "OK" if final_pass else "WARN"},
        {"Status Lights": def_light("OK"), "Gate": "SOURCE_RUN", "Value": str(source_dir), "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "SOURCE_MODE", "Value": source_mode, "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "PARSER_READY_ROWS", "Value": len(ready_rows), "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "OFFICIAL_VALIDATION_CANDIDATES", "Value": len(official_candidates_ready), "Severity": "OK"},
        {"Status Lights": def_light("WARN" if alias_hotspots else "OK"), "Gate": "ALIAS_HOTSPOTS", "Value": len(alias_hotspots), "Severity": "WARN" if alias_hotspots else "OK"},
        {"Status Lights": def_light("WARN" if period_hotspots else "OK"), "Gate": "PERIOD_HOTSPOTS", "Value": len(period_hotspots), "Severity": "WARN" if period_hotspots else "OK"},
        {"Status Lights": def_light("OK"), "Gate": "NO_DB_WRITE", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "NO_CANONICAL_MUTATION", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "NO_SSOT_MUTATION", "Value": "YES", "Severity": "OK"},
    ]

    next_steps = [
        {
            "Status Lights": def_light("WARN"),
            "Next Step": "Run official/historical validation preflight on official candidates only.",
            "Reason": "Only Parser Ready rows have account / period / value / statement fit.",
            "Severity": "WARN",
        },
        {
            "Status Lights": def_light("WARN"),
            "Next Step": "Use alias hotspots as SSOT candidate pack only, not patch.",
            "Reason": "Alias must be validated by official data or formula consistency first.",
            "Severity": "WARN",
        },
        {
            "Status Lights": def_light("WARN"),
            "Next Step": "Use period hotspots to build next targeted header repair.",
            "Reason": "Remaining period issues are likely table/header-layout specific.",
            "Severity": "WARN",
        },
    ]

    result = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "system_pass": final_pass,
        "source_run": str(source_dir),
        "source_mode": source_mode,
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
            ("04 Official Validation Plan", validation_plan, 1000),
            ("05 Official Validation Candidates", official_candidates_ready, 1200),
            ("06 Account Alias Hotspots", alias_hotspots, 800),
            ("07 Period Hotspots", period_hotspots, 800),
            ("08 Statement Hotspots", statement_hotspots, 800),
            ("09 Hard Rules", hard_rules, None),
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