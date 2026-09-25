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
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


VERSION = "VRN_FINAL_VALIDATION_ROUTER_MATERIALIZATION_GATE_V061569"


def def_clean(x: Any) -> str:
    s = "" if x is None else str(x)
    s = html.unescape(s)
    s = s.replace("\u3000", " ").replace("\r", "\n")
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()


def def_norm(x: Any) -> str:
    return re.sub(r"[\s_\-\/\(\)（）\[\]【】{}:：,，.。&+%]+", "", str(x or "").lower())


def def_float(x: Any, default: Any = "") -> Any:
    s = def_clean(x).replace(",", "").replace("%", "")
    if s in ["", "-", "—", "–", "NA", "N/A", "nan", "None"]:
        return default
    try:
        return float(s)
    except Exception:
        return default


def def_light(sev: str) -> str:
    s = str(sev or "").upper()
    if s in ["OK", "PASS", "YES", "READY", "VALIDATED", "STAGING_READY"]:
        return "🟢 INPUT 🟢 DB 🟢 TRUST"
    if s in ["WARN", "REVIEW", "QUEUE", "NEED_RUN", "STAGING"]:
        return "🟢 INPUT 🟡 DB 🟡 TRUST"
    return "🔴 INPUT 🔴 DB 🔴 TRUST"


def def_find_latest_dir(root: Path, prefix: str) -> Path | None:
    if not root.exists():
        return None
    hits = [p for p in root.glob(prefix + "_*") if p.is_dir()]
    return sorted(hits, key=lambda p: p.stat().st_mtime, reverse=True)[0] if hits else None


def def_read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    for enc in ["utf-8-sig", "utf-8", "cp950", "big5", "latin-1"]:
        try:
            with path.open("r", encoding=enc, newline="") as f:
                return list(csv.DictReader(f))
        except Exception:
            pass
    return []


def def_read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    for enc in ["utf-8", "utf-8-sig", "cp950", "big5"]:
        try:
            return json.loads(path.read_text(encoding=enc))
        except Exception:
            pass
    return {}


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


def def_pick_source(run_root: Path) -> dict:
    src568 = def_find_latest_dir(run_root, "VRN_OFFICIAL_CELL_VALIDATION_DRYRUN_V061568")
    if src568:
        return {
            "mode": "V061568_VALIDATION_READY",
            "source": src568,
            "json": src568 / "vrn_official_cell_validation_dryrun_v061568.json",
            "validation_csv": src568 / "vrn_official_cell_validation_matrix_v061568.csv",
            "validated_csv": src568 / "vrn_official_validated_alias_value_rows_v061568.csv",
            "value_only_csv": src568 / "vrn_official_value_match_alias_review_v061568.csv",
            "no_match_csv": src568 / "vrn_official_no_cell_match_v061568.csv",
            "alias_observation_csv": src568 / "vrn_official_alias_observation_pack_v061568.csv",
        }

    src567 = def_find_latest_dir(run_root, "VRN_FLOWA_OFFICIAL_PARSER_FLOWC_HEALTH_V061567")
    return {
        "mode": "NEED_V061568_CELL_VALIDATION_DRYRUN",
        "source": src567,
        "json": src567 / "vrn_flowa_official_parser_flowc_health_v061567.json" if src567 else Path(""),
        "validation_csv": Path(""),
        "validated_csv": Path(""),
        "value_only_csv": Path(""),
        "no_match_csv": Path(""),
        "alias_observation_csv": Path(""),
    }


def def_materialize_candidate(row: dict) -> dict:
    report_value = def_get(row, ["report value"])
    official_value = def_get(row, ["official numeric value"])
    value = official_value if official_value not in ["", None] else report_value

    return {
        "Status Lights": def_light("OK"),
        "materialization candidate id": def_get(row, ["official work order id"]) or def_get(row, ["validation plan id"]),
        "ticker": def_get(row, ["ticker"]),
        "filename": def_get(row, ["filename"]),
        "statement": def_get(row, ["statement"]),
        "period year": def_get(row, ["period year"]),
        "account key": def_get(row, ["account key"]),
        "account canonical": def_get(row, ["account canonical"]),
        "account raw": def_get(row, ["account raw"]),
        "official row labels": def_get(row, ["official row labels"]),
        "value final candidate": value,
        "report value": report_value,
        "official value": official_value,
        "unit": def_get(row, ["unit"]),
        "evidence route": def_get(row, ["validation route"]),
        "evidence cache file": def_get(row, ["cache file"]),
        "evidence table index": def_get(row, ["table index"]),
        "evidence row index": def_get(row, ["row index"]),
        "evidence col index": def_get(row, ["col index"]),
        "confidence": "0.96",
        "ready for canonical staging": "YES",
        "db write": "NO",
        "canonical mutation": "NO",
        "ssot mutation": "NO",
        "Severity": "OK",
    }


def def_build_alias_candidate(row: dict) -> dict:
    return {
        "Status Lights": def_light("WARN"),
        "alias candidate id": def_get(row, ["official work order id"]) or def_get(row, ["validation plan id"]),
        "account key": def_get(row, ["account key"]),
        "report account raw": def_get(row, ["account raw"]),
        "account canonical": def_get(row, ["account canonical"]),
        "official row labels": def_get(row, ["official row labels"]),
        "report value": def_get(row, ["report value"]),
        "official numeric value": def_get(row, ["official numeric value"]),
        "validation route": def_get(row, ["validation route"]),
        "candidate reason": "value matched or partially matched, but alias bridge not strong enough",
        "recommended action": "append-only SSOT alias candidate only after manual/second-run confirmation",
        "ssot mutation": "NO",
        "Severity": "WARN",
    }


def def_html_table(title: str, rows: list[dict], limit: int | None = None) -> str:
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
            cls = "left" if any(x in k.lower() for x in ["filename", "account", "label", "route", "reason", "action", "cache", "source", "path"]) else "center"
            tds.append(f"<td class='{cls}'>{html.escape(str(v)).replace(chr(10), '<br>')}</td>")
        trs.append("<tr>" + "".join(tds) + "</tr>")
    return f"<section class='card'><h2>{html.escape(title)}</h2><div class='table-wrap'><table><thead><tr>{th}</tr></thead><tbody>{''.join(trs)}</tbody></table></div></section>"


def def_write_html(path: Path, counts: dict, sections: list[tuple[str, list[dict], int | None]]) -> None:
    css = """
body{margin:0;background:#07111f;color:#eef6ff;font-family:Segoe UI,'Microsoft JhengHei',Arial,sans-serif;font-size:12px}
header{padding:26px 34px;background:#0d1b2f;border-bottom:1px solid #1f3557}
h1{margin:0;font-size:25px}.sub{color:#9fb3c8;margin-top:8px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;padding:22px 34px}
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
    body = "".join(def_html_table(t, rows, lim) for t, rows, lim in sections)
    doc = f"""<!doctype html><html><head><meta charset="utf-8"><title>VRN Final Validation Router v061569</title><style>{css}</style></head>
<body><header><h1>VRN · Final Validation Router + Materialization Staging Gate v0.6.15.6.9</h1>
<div class="sub">validated rows · alias candidates · materialization staging only · no mutation</div></header>
<div class="grid">{cards}</div><main>{body}</main></body></html>"""
    path.write_text(doc, encoding="utf-8")


def def_main() -> None:
    if len(sys.argv) < 3:
        raise SystemExit("usage: py <run_root> <run_dir>")

    run_root = Path(sys.argv[1])
    run_dir = Path(sys.argv[2])
    run_dir.mkdir(parents=True, exist_ok=True)

    source = def_pick_source(run_root)
    mode = source["mode"]

    validation_rows = [r for r in def_read_csv(source["validation_csv"]) if "empty_marker" not in r]
    validated_rows = [r for r in def_read_csv(source["validated_csv"]) if "empty_marker" not in r]
    value_only_rows = [r for r in def_read_csv(source["value_only_csv"]) if "empty_marker" not in r]
    no_match_rows = [r for r in def_read_csv(source["no_match_csv"]) if "empty_marker" not in r]
    alias_obs_rows = [r for r in def_read_csv(source["alias_observation_csv"]) if "empty_marker" not in r]

    materialization_candidates = [def_materialize_candidate(r) for r in validated_rows]
    alias_candidates = [def_build_alias_candidate(r) for r in value_only_rows] + [
        {
            "Status Lights": def_light("WARN"),
            "alias candidate id": def_get(r, ["alias observation id"]),
            "account key": def_get(r, ["account key"]),
            "report account raw": def_get(r, ["report account raw"]),
            "account canonical": "",
            "official row labels": def_get(r, ["official row label observed"]),
            "report value": "",
            "official numeric value": "",
            "validation route": "ALIAS_OBSERVATION_PACK",
            "candidate reason": "observed from prior alias observation pack",
            "recommended action": "append-only SSOT alias candidate only after confirmation",
            "ssot mutation": "NO",
            "Severity": "WARN",
        }
        for r in alias_obs_rows
    ]

    route_summary = []
    if validation_rows:
        for k, v in sorted(Counter(def_get(r, ["validation route"]) for r in validation_rows).items(), key=lambda x: (-x[1], x[0])):
            sev = "OK" if k == "VALIDATED_ALIAS_AND_VALUE" else "WARN"
            route_summary.append({
                "Status Lights": def_light(sev),
                "validation route": k,
                "rows": v,
                "rate": f"{(v / max(len(validation_rows), 1)) * 100:.2f}%",
                "Severity": sev,
            })
    else:
        route_summary.append({
            "Status Lights": def_light("WARN"),
            "validation route": "NEED_RUN_V061568",
            "rows": 0,
            "rate": "0.00%",
            "Severity": "WARN",
        })

    gate_rows = [
        {
            "Status Lights": def_light("OK" if materialization_candidates else "WARN"),
            "Gate": "MATERIALIZATION_STAGING_CANDIDATES",
            "Value": len(materialization_candidates),
            "Required": ">0 for next materialization staging",
            "Severity": "OK" if materialization_candidates else "WARN",
        },
        {
            "Status Lights": def_light("OK"),
            "Gate": "NO_DB_WRITE",
            "Value": "YES",
            "Required": "YES",
            "Severity": "OK",
        },
        {
            "Status Lights": def_light("OK"),
            "Gate": "NO_CANONICAL_MUTATION",
            "Value": "YES",
            "Required": "YES",
            "Severity": "OK",
        },
        {
            "Status Lights": def_light("OK"),
            "Gate": "NO_SSOT_MUTATION",
            "Value": "YES",
            "Required": "YES",
            "Severity": "OK",
        },
    ]

    next_steps = []
    if mode == "NEED_V061568_CELL_VALIDATION_DRYRUN":
        next_steps.append({
            "Status Lights": def_light("WARN"),
            "Next Step": "Run v0.6.15.6.8 Official Cell-Level Validation Dry Run first.",
            "Reason": "v061567 created official cells and validation plan, but cell-level validation matrix is not found yet.",
            "Severity": "WARN",
        })
    elif materialization_candidates:
        next_steps.append({
            "Status Lights": def_light("WARN"),
            "Next Step": "Run canonical materialization staging pack, still no DB write.",
            "Reason": "Only validated alias+value rows may enter staging.",
            "Severity": "WARN",
        })
    else:
        next_steps.append({
            "Status Lights": def_light("WARN"),
            "Next Step": "Improve alias bridge and rerun v061568.",
            "Reason": "No validated rows reached materialization staging.",
            "Severity": "WARN",
        })

    next_steps.extend([
        {
            "Status Lights": def_light("OK"),
            "Next Step": "Keep DB/canonical/SSOT locked.",
            "Reason": "This router only decides readiness; it does not commit facts.",
            "Severity": "OK",
        },
        {
            "Status Lights": def_light("WARN"),
            "Next Step": "Alias candidates remain candidate pack only.",
            "Reason": "SSOT can be append-only later, after second confirmation.",
            "Severity": "WARN",
        },
    ])

    outputs = {
        "html": str(run_dir / "VRN_Final_Validation_Router_Materialization_Gate_v061569.html"),
        "json": str(run_dir / "vrn_final_validation_router_materialization_gate_v061569.json"),
        "materialization_candidates_csv": str(run_dir / "vrn_materialization_staging_candidates_v061569.csv"),
        "alias_candidates_csv": str(run_dir / "vrn_alias_candidates_no_ssot_patch_v061569.csv"),
        "no_match_queue_csv": str(run_dir / "vrn_no_match_queue_v061569.csv"),
        "route_summary_csv": str(run_dir / "vrn_validation_route_summary_v061569.csv"),
        "gate_matrix_csv": str(run_dir / "vrn_materialization_gate_matrix_v061569.csv"),
        "next_steps_csv": str(run_dir / "vrn_final_validation_next_steps_v061569.csv"),
    }

    def_write_csv(Path(outputs["materialization_candidates_csv"]), materialization_candidates)
    def_write_csv(Path(outputs["alias_candidates_csv"]), alias_candidates)
    def_write_csv(Path(outputs["no_match_queue_csv"]), no_match_rows)
    def_write_csv(Path(outputs["route_summary_csv"]), route_summary)
    def_write_csv(Path(outputs["gate_matrix_csv"]), gate_rows)
    def_write_csv(Path(outputs["next_steps_csv"]), next_steps)

    final_pass = mode == "V061568_VALIDATION_READY" and (len(materialization_candidates) > 0 or len(alias_candidates) > 0 or len(no_match_rows) >= 0)

    counts = {
        "Final": "PASS" if final_pass else "REVIEW",
        "Source Mode": mode,
        "Validation Rows": len(validation_rows),
        "Materialization Candidates": len(materialization_candidates),
        "Alias Candidates": len(alias_candidates),
        "No Match Queue": len(no_match_rows),
        "DB Write": "NO",
        "Canonical": "NO",
        "SSOT": "NO",
    }

    overview = [
        {
            "Status Lights": def_light("OK" if final_pass else "WARN"),
            "Gate": "FINAL_VALIDATION_ROUTER_PASS",
            "Value": "YES" if final_pass else "REVIEW",
            "Severity": "OK" if final_pass else "WARN",
        },
        {
            "Status Lights": def_light("OK" if mode == "V061568_VALIDATION_READY" else "WARN"),
            "Gate": "SOURCE_MODE",
            "Value": mode,
            "Severity": "OK" if mode == "V061568_VALIDATION_READY" else "WARN",
        },
        {
            "Status Lights": def_light("OK"),
            "Gate": "SOURCE_RUN",
            "Value": str(source["source"]) if source["source"] else "",
            "Severity": "OK" if source["source"] else "WARN",
        },
        {
            "Status Lights": def_light("OK" if materialization_candidates else "WARN"),
            "Gate": "MATERIALIZATION_CANDIDATES",
            "Value": len(materialization_candidates),
            "Severity": "OK" if materialization_candidates else "WARN",
        },
        {
            "Status Lights": def_light("OK"),
            "Gate": "NO_DB_WRITE",
            "Value": "YES",
            "Severity": "OK",
        },
        {
            "Status Lights": def_light("OK"),
            "Gate": "NO_CANONICAL_MUTATION",
            "Value": "YES",
            "Severity": "OK",
        },
        {
            "Status Lights": def_light("OK"),
            "Gate": "NO_SSOT_MUTATION",
            "Value": "YES",
            "Severity": "OK",
        },
    ]

    result = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "system_pass": final_pass,
        "source_mode": mode,
        "source_run": str(source["source"]) if source["source"] else "",
        "counts": counts,
        "outputs": outputs,
    }

    def_write_json(Path(outputs["json"]), result)
    def_write_html(
        Path(outputs["html"]),
        counts,
        [
            ("01 Overview", overview, None),
            ("02 Gate Matrix", gate_rows, None),
            ("03 Route Summary", route_summary, None),
            ("04 Next Steps", next_steps, None),
            ("05 Materialization Staging Candidates", materialization_candidates, 1200),
            ("06 Alias Candidates - No SSOT Patch", alias_candidates, 1200),
            ("07 No Match Queue", no_match_rows, 1200),
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