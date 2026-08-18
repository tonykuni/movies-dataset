from __future__ import annotations

import argparse
import csv
import html
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        rows = [{"def_empty": "true"}]
    cols: List[str] = []
    seen = set()
    for r in rows:
        for k in r.keys():
            if k not in seen:
                seen.add(k)
                cols.append(k)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def prop(row: Dict[str, Any], key: str, default: str = "") -> str:
    v = row.get(key, default)
    return "" if v is None else str(v)


def h(x: Any) -> str:
    return html.escape("" if x is None else str(x))


def precheck_profile(package_name: str) -> Dict[str, str]:
    if package_name == "TRUE_DANGER_MANUAL_REVIEW_QUEUE":
        return {
            "def_precheck_track": "RED_TRUE_DANGER_MANUAL_ONLY",
            "def_ryg": "RED",
            "def_fix_class": "Sequence-Dependent",
            "def_hydra_risk": "HIGH",
            "def_allowed_action": "manual_review_queue_only",
            "def_required_checks": "active_source_boundary; dangerous_command_context; no_apply_guard; no_mutation_guard; operator_approval_required",
            "def_repair_allowed": "false",
            "def_next_gate": "v0115F6_TRUE_DANGER_CONTEXT_EVIDENCE_PACK_ONLY"
        }

    if package_name == "TRUE_SECRET_RUNTIME_PARAMETER_REVIEW_QUEUE":
        return {
            "def_precheck_track": "RED_TRUE_SECRET_RUNTIME_ONLY",
            "def_ryg": "RED",
            "def_fix_class": "Sequence-Dependent",
            "def_hydra_risk": "HIGH",
            "def_allowed_action": "secret_runtime_parameter_review_only",
            "def_required_checks": "no_plaintext_secret_output; env_presence_only; ui_no_localstorage; html_masking_required; operator_approval_required",
            "def_repair_allowed": "false",
            "def_next_gate": "v0115F6_TRUE_SECRET_RUNTIME_EVIDENCE_PACK_ONLY"
        }

    if package_name == "BOUNDARY_CONFIRMATION_QUEUE":
        return {
            "def_precheck_track": "YELLOW_BOUNDARY_CONFIRMATION",
            "def_ryg": "YELLOW",
            "def_fix_class": "Multi-subsystem synchronization",
            "def_hydra_risk": "MEDIUM",
            "def_allowed_action": "boundary_confirmation_only",
            "def_required_checks": "gate_status; dryrun_status; no_apply_label; no_mutation_label; disabled_boundary_marker",
            "def_repair_allowed": "false",
            "def_next_gate": "v0115F6_BOUNDARY_CONFIRMATION_EVIDENCE_PACK_ONLY"
        }

    if package_name == "ARTIFACT_FALSE_POSITIVE_CONFIRMATION_QUEUE":
        return {
            "def_precheck_track": "YELLOW_ARTIFACT_FALSE_POSITIVE_CONFIRMATION",
            "def_ryg": "YELLOW",
            "def_fix_class": "Parallel-Fixable",
            "def_hydra_risk": "MEDIUM",
            "def_allowed_action": "artifact_confirmation_ledger_candidate_only",
            "def_required_checks": "backup_path; output_path; report_path; template_path; historical_run_path",
            "def_repair_allowed": "false",
            "def_next_gate": "v0115F6_ARTIFACT_FALSE_POSITIVE_LEDGER_CANDIDATE_ONLY"
        }

    if package_name == "SECRET_FIELDNAME_CLEARANCE_QUEUE":
        return {
            "def_precheck_track": "GREEN_SECRET_FIELDNAME_CLEARANCE",
            "def_ryg": "GREEN",
            "def_fix_class": "Parallel-Fixable",
            "def_hydra_risk": "LOW",
            "def_allowed_action": "clearance_ledger_candidate_only",
            "def_required_checks": "field_name_only; parameter_name_only; schema_contract_only; no_secret_value; no_runtime_exposure",
            "def_repair_allowed": "false",
            "def_next_gate": "v0115F6_SECRET_FIELDNAME_CLEARANCE_LEDGER_CANDIDATE_ONLY"
        }

    if package_name == "COMMENT_DOC_FALSE_POSITIVE_CLEARANCE_QUEUE":
        return {
            "def_precheck_track": "GREEN_COMMENT_DOC_FALSE_POSITIVE_CLEARANCE",
            "def_ryg": "GREEN",
            "def_fix_class": "Parallel-Fixable",
            "def_hydra_risk": "LOW",
            "def_allowed_action": "false_positive_ledger_candidate_only",
            "def_required_checks": "comment_only; docstring_only; css_only; display_text_only; no_executable_context",
            "def_repair_allowed": "false",
            "def_next_gate": "v0115F6_COMMENT_DOC_FALSE_POSITIVE_LEDGER_CANDIDATE_ONLY"
        }

    if package_name == "PATH_SIZE_REVIEW_QUEUE":
        return {
            "def_precheck_track": "YELLOW_PATH_SIZE_SAMPLE_PLAN",
            "def_ryg": "YELLOW",
            "def_fix_class": "Sequence-Dependent",
            "def_hydra_risk": "MEDIUM",
            "def_allowed_action": "sample_plan_only",
            "def_required_checks": "file_size; file_type; sample_strategy; no_full_read; bounded_bytes_only",
            "def_repair_allowed": "false",
            "def_next_gate": "v0115F6_PATH_SIZE_SAMPLE_PLAN_ONLY"
        }

    return {
        "def_precheck_track": "MANUAL_REVIEW_ONLY",
        "def_ryg": "YELLOW",
        "def_fix_class": "Sequence-Dependent",
        "def_hydra_risk": "MEDIUM",
        "def_allowed_action": "manual_review_only",
        "def_required_checks": "manual_review",
        "def_repair_allowed": "false",
        "def_next_gate": "v0115F6_MANUAL_REVIEW_ONLY"
    }


def build_precheck_rows(package_rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for i, r in enumerate(package_rows, 1):
        pkg = prop(r, "def_package_name")
        p = precheck_profile(pkg)

        out.append({
            "def_precheck_id": f"F5-PRE-{i:06d}",
            "def_package_row_id": prop(r, "def_package_row_id"),
            "def_package_name": pkg,
            "def_precheck_track": p["def_precheck_track"],
            "def_ryg": p["def_ryg"],
            "def_fix_class": p["def_fix_class"],
            "def_hydra_risk": p["def_hydra_risk"],
            "def_subsystem": prop(r, "def_subsystem"),
            "def_decision_bucket": prop(r, "def_decision_bucket"),
            "def_source_rel_path": prop(r, "def_source_rel_path"),
            "def_allowed_action": p["def_allowed_action"],
            "def_required_checks": p["def_required_checks"],
            "def_repair_allowed": p["def_repair_allowed"],
            "def_next_gate": p["def_next_gate"],
            "def_source_read": "false",
            "def_apply_enabled": "false",
            "def_source_mutation": "false",
            "def_db_write": "false"
        })
    return out


def split_outputs(precheck_rows: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    buckets = {
        "red_true_danger_manual_review": [],
        "red_true_secret_runtime_review": [],
        "yellow_boundary_confirmation": [],
        "yellow_artifact_false_positive_confirmation": [],
        "yellow_path_size_sample_plan": [],
        "green_secret_fieldname_clearance": [],
        "green_comment_doc_false_positive": []
    }

    for r in precheck_rows:
        pkg = prop(r, "def_package_name")
        if pkg == "TRUE_DANGER_MANUAL_REVIEW_QUEUE":
            buckets["red_true_danger_manual_review"].append(r)
        elif pkg == "TRUE_SECRET_RUNTIME_PARAMETER_REVIEW_QUEUE":
            buckets["red_true_secret_runtime_review"].append(r)
        elif pkg == "BOUNDARY_CONFIRMATION_QUEUE":
            buckets["yellow_boundary_confirmation"].append(r)
        elif pkg == "ARTIFACT_FALSE_POSITIVE_CONFIRMATION_QUEUE":
            buckets["yellow_artifact_false_positive_confirmation"].append(r)
        elif pkg == "PATH_SIZE_REVIEW_QUEUE":
            buckets["yellow_path_size_sample_plan"].append(r)
        elif pkg == "SECRET_FIELDNAME_CLEARANCE_QUEUE":
            buckets["green_secret_fieldname_clearance"].append(r)
        elif pkg == "COMMENT_DOC_FALSE_POSITIVE_CLEARANCE_QUEUE":
            buckets["green_comment_doc_false_positive"].append(r)

    return buckets


def build_summary(precheck_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    g = defaultdict(lambda: {"count": 0, "examples": []})
    for r in precheck_rows:
        key = (
            prop(r, "def_ryg"),
            prop(r, "def_precheck_track"),
            prop(r, "def_subsystem"),
            prop(r, "def_fix_class"),
            prop(r, "def_next_gate")
        )
        g[key]["count"] += 1
        if len(g[key]["examples"]) < 5:
            g[key]["examples"].append(prop(r, "def_source_rel_path"))

    rows = []
    n = 0
    for (ryg, track, subsystem, fix_class, next_gate), payload in g.items():
        n += 1
        rows.append({
            "def_summary_id": f"F5-SUM-{n:04d}",
            "def_ryg": ryg,
            "def_precheck_track": track,
            "def_subsystem": subsystem,
            "def_fix_class": fix_class,
            "def_count": payload["count"],
            "def_next_gate": next_gate,
            "def_examples": " | ".join(payload["examples"]),
            "def_repair_allowed": "false",
            "def_apply_enabled": "false"
        })

    order = {"RED": 0, "YELLOW": 1, "GREEN": 2}
    return sorted(rows, key=lambda x: (order.get(x["def_ryg"], 9), -int(x["def_count"]), x["def_subsystem"]))


def build_process_matrix(precheck_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    c = Counter(prop(r, "def_precheck_track") for r in precheck_rows)
    subs = Counter(prop(r, "def_subsystem") for r in precheck_rows)

    return [
        {
            "PROCESS": "ROUND 1 · Comprehensive Fix Candidate Split",
            "SUPPORTIVE MODULES": "只產生 review/clearance package，不修 source；支援模組先鎖 NoApply/NoMutation",
            "VDF": "VDF 先切 TRUE_DANGER、TRUE_SECRET、Boundary、Fieldname 四類，不混修",
            "VAP": "VAP UI/template/CSS/JS 先分出 artifact、comment、fieldname，避免 UI 被誤修",
            "OTHERS": "VRN / VIS / Registry / Unclassified 只進分流矩陣",
            "METHOD": "Parallel-safe items only become ledger candidates; RED stays locked.",
            "RYG": "YELLOW"
        },
        {
            "PROCESS": "ROUND 2 · Sequential Risk Review",
            "SUPPORTIVE MODULES": f"RED={c['RED_TRUE_DANGER_MANUAL_ONLY'] + c['RED_TRUE_SECRET_RUNTIME_ONLY']} 必須 sequence-dependent review",
            "VDF": "VDF danger/secret 不可批次修；先建 context evidence pack",
            "VAP": "VAP active script 若真危險，先人工確認執行邊界",
            "OTHERS": "Unclassified 必須先歸類，不可直接清除",
            "METHOD": "Hydra control: no simultaneous fixes on RED nodes.",
            "RYG": "RED"
        },
        {
            "PROCESS": "ROUND 3 · Final Polishing / Ledger Candidate",
            "SUPPORTIVE MODULES": "fieldname/comment 類可入 clearance ledger candidate",
            "VDF": f"Fieldname clearance candidates total={c['GREEN_SECRET_FIELDNAME_CLEARANCE']}",
            "VAP": f"Comment/doc false positive candidates total={c['GREEN_COMMENT_DOC_FALSE_POSITIVE_CLEARANCE']}",
            "OTHERS": "Path-size only sample plan, no full read.",
            "METHOD": "Only ledger candidate; no canonical merge.",
            "RYG": "GREEN"
        },
        {
            "PROCESS": "MATRIX Total Progress",
            "SUPPORTIVE MODULES": f"Supportive rows={subs['Supportive_NexusCore_Env']}",
            "VDF": f"VDF rows={subs['VDF_VeritasDataForge']}",
            "VAP": f"VAP rows={subs['VAP_VisualizationAnalytics']}",
            "OTHERS": f"Others rows={len(precheck_rows) - subs['Supportive_NexusCore_Env'] - subs['VDF_VeritasDataForge'] - subs['VAP_VisualizationAnalytics']}",
            "METHOD": "PROCESS / SUPPORTIVE MODULES / VDF / VAP / OTHERS single-page governance.",
            "RYG": "GREEN"
        }
    ]


def build_default_parameters(precheck_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    c = Counter(prop(r, "def_ryg") for r in precheck_rows)
    track = Counter(prop(r, "def_precheck_track") for r in precheck_rows)

    return {
        "schema_version": "VIA_v0115F5_GovernanceDefaultParameters",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "governance_policy": {
            "max_repair_rounds": 3,
            "panoramic_analysis_after_each_fix": True,
            "no_external_call": True,
            "no_source_read_in_f5": True,
            "no_rescan_in_f5": True,
            "no_source_mutation": True,
            "no_canonical_merge": True,
            "no_db_write": True,
            "no_apply": True,
            "no_delete": True,
            "no_stop_process": True,
            "no_forced_close": True
        },
        "default_parameters": {
            "html_ui_auto_open": True,
            "write_csv": True,
            "write_json": True,
            "write_html": True,
            "max_html_rows": 900,
            "red_requires_manual_review": True,
            "yellow_requires_confirmation": True,
            "green_clearance_candidate_only": True,
            "path_size_full_read_allowed": False,
            "secret_plaintext_allowed": False,
            "runtime_secret_policy": "env_presence_or_runtime_parameter_only"
        },
        "counts": {
            "input_rows": len(precheck_rows),
            "red_rows": c["RED"],
            "yellow_rows": c["YELLOW"],
            "green_rows": c["GREEN"],
            "true_danger_rows": track["RED_TRUE_DANGER_MANUAL_ONLY"],
            "true_secret_rows": track["RED_TRUE_SECRET_RUNTIME_ONLY"],
            "fieldname_clearance_rows": track["GREEN_SECRET_FIELDNAME_CLEARANCE"],
            "comment_false_positive_rows": track["GREEN_COMMENT_DOC_FALSE_POSITIVE_CLEARANCE"],
            "path_size_rows": track["YELLOW_PATH_SIZE_SAMPLE_PLAN"]
        },
        "next_phase": {
            "recommended": "v0115F6_GREEN_CLEARANCE_LEDGER_CANDIDATE_ONLY_AND_RED_EVIDENCE_PACK_ONLY",
            "blocked": [
                "source mutation",
                "automatic fix on RED nodes",
                "canonical merge",
                "db write",
                "full read of path-size queue",
                "secret plaintext export"
            ]
        }
    }


def build_validation(precheck_rows: List[Dict[str, Any]], default_params: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = []

    def add(name: str, ok: bool, msg: str) -> None:
        rows.append({
            "def_validation": name,
            "def_status": "PASS" if ok else "FAIL",
            "def_message": msg
        })

    c = Counter(prop(r, "def_ryg") for r in precheck_rows)
    total = len(precheck_rows)

    add("INPUT_NOT_EMPTY", total > 0, f"input={total}")
    add("RYG_SUM_MATCH", c["RED"] + c["YELLOW"] + c["GREEN"] == total, f"red={c['RED']} yellow={c['YELLOW']} green={c['GREEN']} total={total}")
    add("NO_REPAIR_ALLOWED", all(prop(r, "def_repair_allowed") == "false" for r in precheck_rows), "all repair_allowed=false")
    add("NO_APPLY", all(prop(r, "def_apply_enabled") == "false" for r in precheck_rows), "all apply=false")
    add("NO_SOURCE_READ", all(prop(r, "def_source_read") == "false" for r in precheck_rows), "all source_read=false")
    add("NO_SOURCE_MUTATION", all(prop(r, "def_source_mutation") == "false" for r in precheck_rows), "all source_mutation=false")
    add("NO_DB_WRITE", all(prop(r, "def_db_write") == "false" for r in precheck_rows), "all db_write=false")
    add("MAX_ROUNDS_EQ_3", default_params["governance_policy"]["max_repair_rounds"] == 3, "max_repair_rounds=3")
    add("SECRET_PLAINTEXT_BLOCKED", default_params["default_parameters"]["secret_plaintext_allowed"] is False, "secret_plaintext_allowed=false")
    add("PATH_SIZE_FULL_READ_BLOCKED", default_params["default_parameters"]["path_size_full_read_allowed"] is False, "path_size_full_read_allowed=false")

    return rows


def build_readiness(precheck_rows: List[Dict[str, Any]], validation: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    c = Counter(prop(r, "def_ryg") for r in precheck_rows)
    track = Counter(prop(r, "def_precheck_track") for r in precheck_rows)
    fail = sum(1 for r in validation if prop(r, "def_status") != "PASS")

    return [{
        "def_gate_status": "PACKAGE_SPECIFIC_PRECHECK_READY_REVIEW_ONLY" if fail == 0 else "BLOCKED_BY_PRECHECK_VALIDATION_FAIL",
        "def_allow_next": "true" if fail == 0 else "false",
        "def_reason": "v0115F5 precheck package generated. No source read, no mutation, no apply.",
        "def_input_rows": str(len(precheck_rows)),
        "def_red_rows": str(c["RED"]),
        "def_yellow_rows": str(c["YELLOW"]),
        "def_green_rows": str(c["GREEN"]),
        "def_true_danger_rows": str(track["RED_TRUE_DANGER_MANUAL_ONLY"]),
        "def_true_secret_rows": str(track["RED_TRUE_SECRET_RUNTIME_ONLY"]),
        "def_fieldname_clearance_rows": str(track["GREEN_SECRET_FIELDNAME_CLEARANCE"]),
        "def_comment_false_positive_rows": str(track["GREEN_COMMENT_DOC_FALSE_POSITIVE_CLEARANCE"]),
        "def_path_size_rows": str(track["YELLOW_PATH_SIZE_SAMPLE_PLAN"]),
        "def_validation_fail": str(fail),
        "def_source_read": "false",
        "def_execution_enabled": "false",
        "def_apply_enabled": "false",
        "def_source_mutation": "false",
        "def_canonical_merge": "false",
        "def_db_write": "false",
        "def_next_allowed_phase": "v0115F6 ledger/evidence-pack candidate only"
    }]


def render_table(rows: List[Dict[str, Any]], cols: List[str], max_rows: int = 900) -> str:
    out = ["<table><thead><tr>"]
    for c in cols:
        out.append(f"<th>{h(c)}</th>")
    out.append("</tr></thead><tbody>")

    if not rows:
        out.append(f"<tr><td colspan='{len(cols)}'>No rows</td></tr>")
    else:
        for r in rows[:max_rows]:
            joined = " ".join(str(v) for v in r.values()).upper()
            cls = ""
            if "RED" in joined:
                cls = " class='risk-red'"
            elif "YELLOW" in joined:
                cls = " class='risk-yellow'"
            elif "GREEN" in joined:
                cls = " class='risk-green'"
            out.append(f"<tr{cls}>")
            for c in cols:
                v = prop(r, c)
                if len(v) > 520:
                    v = v[:520] + "..."
                out.append(f"<td>{h(v)}</td>")
            out.append("</tr>")

    out.append("</tbody></table>")
    return "".join(out)


def write_html(path: Path, payload: Dict[str, Any]) -> None:
    readiness = payload["readiness"][0]
    default_params = payload["default_parameters"]

    cards = ""
    for k, v in [
        ("Gate", readiness["def_gate_status"]),
        ("Input", readiness["def_input_rows"]),
        ("Red", readiness["def_red_rows"]),
        ("Yellow", readiness["def_yellow_rows"]),
        ("Green", readiness["def_green_rows"]),
        ("Danger", readiness["def_true_danger_rows"]),
        ("Secret", readiness["def_true_secret_rows"]),
        ("Next", "v0115F6")
    ]:
        cards += f"<div class='card'><div class='k'>{h(k)}</div><div class='v'>{h(v)}</div></div>"

    style = """
:root{--bg:#f7f6f2;--paper:#fffefa;--line:#dedbd2;--ink:#24231f;--muted:#706d64;--seal:#8f2f24;--red:#c96b5a;--yellow:#c4943a;--green:#5a9e6f;--sky:#9fbcc2}
body{margin:0;background:radial-gradient(circle at 12% 10%,rgba(159,188,194,.24),transparent 28%),radial-gradient(circle at 88% 0%,rgba(180,200,190,.22),transparent 31%),linear-gradient(135deg,rgba(255,255,255,.70),rgba(247,246,242,1));color:var(--ink);font-family:'Microsoft JhengHei','Noto Sans TC',Arial,sans-serif;font-size:8.5px;line-height:1.35}
.wrap{max-width:1880px;margin:0 auto;padding:16px}.header{display:grid;grid-template-columns:1fr auto;gap:16px;align-items:start;margin-bottom:10px}
h1{font-size:15px;margin:0 0 4px;font-weight:650}.sub{font-size:8.2px;color:var(--muted)}
.seal{border:2px solid var(--seal);color:var(--seal);width:42px;height:42px;display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:700;border-radius:6px;background:rgba(255,255,255,.48)}
.cards{display:grid;grid-template-columns:repeat(8,1fr);gap:7px;margin:10px 0}.card{background:var(--paper);border:1px solid var(--line);border-radius:10px;padding:7px;min-height:43px;box-shadow:0 8px 22px rgba(60,50,30,.045)}
.k{font-size:7.5px;color:var(--muted)}.v{font:650 9.8px Consolas,monospace;margin-top:4px;word-break:break-word}
.sec{background:rgba(255,254,250,.93);border:1px solid var(--line);border-radius:13px;padding:9px;margin-bottom:10px;overflow:hidden;box-shadow:0 10px 26px rgba(60,50,30,.045)}
h2{font-size:10px;margin:0 0 7px;font-weight:650}.note{white-space:pre-wrap;background:#fbfaf6;border:1px solid #e8e4da;border-radius:10px;padding:8px;color:#514d45;font-size:8.2px}
table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:7.45px}th,td{border-bottom:1px solid #ebe8df;padding:3px 4px;vertical-align:top;word-break:break-word;overflow-wrap:anywhere}
th{background:#f0eee8;text-align:left;font-weight:650;color:#555149;position:sticky;top:0}tr:hover td{background:#f8f7f1}
.risk-red td{background:rgba(201,107,90,.09)}.risk-yellow td{background:rgba(196,148,58,.09)}.risk-green td{background:rgba(90,158,111,.075)}
.tag{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:2px 7px;background:white;margin-right:4px;color:var(--muted)}
.search{width:100%;padding:7px 9px;border:1px solid var(--line);border-radius:9px;background:white;margin:6px 0 8px;font-size:9px}
.btn{border:1px solid var(--line);background:white;border-radius:999px;padding:4px 9px;cursor:pointer;font-size:8px;margin-right:4px}.btn:hover{border-color:var(--sky)}
pre{white-space:pre-wrap;background:#fbfaf6;border:1px solid #e8e4da;border-radius:10px;padding:8px;font-size:7.6px;max-height:260px;overflow:auto}.footer{margin:12px 0 4px;color:var(--muted);font-size:8px}.path{font-family:Consolas,monospace;color:#355b63}
"""
    js = """
function filterTables(q){
  q=(q||'').toLowerCase();
  document.querySelectorAll('tbody tr').forEach(function(tr){
    var t=tr.innerText.toLowerCase();
    tr.style.display=t.indexOf(q)>=0?'':'none';
  });
}
function quick(q){document.getElementById('q').value=q;filterTables(q);}
"""

    default_json = json.dumps(default_params, ensure_ascii=False, indent=2)

    doc = f"""<!doctype html>
<html lang="zh-Hant">
<head><meta charset="utf-8"/><title>VIA v0115F5 Package-Specific Precheck</title><style>{style}</style><script>{js}</script></head>
<body><div class="wrap">
  <div class="header">
    <div>
      <h1>def VIA v0115F5 · Package-Specific Precheck + Governance Default Parameters</h1>
      <div class="sub">PROCESS · SUPPORTIVE MODULES · VDF · VAP · OTHERS · RYG · SSOT Default Parameters · No Source Read · No Apply</div>
    </div>
    <div class="seal">理</div>
  </div>

  <div class="cards">{cards}</div>

  <div class="sec">
    <h2>def Executive Judgment</h2>
    <span class="tag">PRECHECK ONLY</span><span class="tag">DEFAULT PARAMETERS</span><span class="tag">NO SOURCE READ</span><span class="tag">NO MUTATION</span><span class="tag">NO APPLY</span><span class="tag">NO DB WRITE</span>
    <div class="note">v0115F5 只做 package-specific precheck 與 governance default parameter control。RED 節點只能建立 evidence pack；YELLOW 節點只能 boundary/path confirmation；GREEN 節點只能 clearance ledger candidate。仍不可修 source。</div>
    <input id="q" class="search" oninput="filterTables(this.value)" placeholder="搜尋 RED / YELLOW / GREEN / VDF / VAP / SECRET / DANGER / FIELDNAME / PATH_SIZE ..."/>
    <button class="btn" onclick="quick('RED')">RED</button>
    <button class="btn" onclick="quick('YELLOW')">YELLOW</button>
    <button class="btn" onclick="quick('GREEN')">GREEN</button>
    <button class="btn" onclick="quick('VDF')">VDF</button>
    <button class="btn" onclick="quick('VAP')">VAP</button>
    <button class="btn" onclick="quick('SECRET')">SECRET</button>
    <button class="btn" onclick="quick('DANGER')">DANGER</button>
    <button class="btn" onclick="quick('')">RESET</button>
  </div>

  <div class="sec"><h2>def Readiness Gate</h2>{render_table(payload["readiness"], ["def_gate_status","def_allow_next","def_reason","def_input_rows","def_red_rows","def_yellow_rows","def_green_rows","def_true_danger_rows","def_true_secret_rows","def_fieldname_clearance_rows","def_comment_false_positive_rows","def_path_size_rows","def_validation_fail","def_apply_enabled","def_source_read","def_source_mutation","def_db_write","def_next_allowed_phase"], 20)}</div>
  <div class="sec"><h2>def PROCESS / SUPPORTIVE MODULES / VDF / VAP / OTHERS</h2>{render_table(payload["process_matrix"], ["PROCESS","SUPPORTIVE MODULES","VDF","VAP","OTHERS","METHOD","RYG"], 20)}</div>
  <div class="sec"><h2>def Precheck Summary Matrix</h2>{render_table(payload["summary"], ["def_summary_id","def_ryg","def_precheck_track","def_subsystem","def_fix_class","def_count","def_next_gate","def_repair_allowed","def_apply_enabled"], 240)}</div>
  <div class="sec"><h2>def Validation Matrix</h2>{render_table(payload["validation"], ["def_validation","def_status","def_message"], 40)}</div>
  <div class="sec"><h2>def Governance Default Parameters JSON</h2><pre>{h(default_json)}</pre></div>
  <div class="sec"><h2>def Full Precheck Matrix</h2>{render_table(payload["precheck_rows"], ["def_precheck_id","def_package_row_id","def_package_name","def_precheck_track","def_ryg","def_fix_class","def_hydra_risk","def_subsystem","def_decision_bucket","def_source_rel_path","def_allowed_action","def_required_checks","def_repair_allowed","def_next_gate","def_apply_enabled"], 900)}</div>

  <div class="footer">
    SourceRun: <span class="path">{h(payload["source_run"])}</span><br/>
    RunDir: <span class="path">{h(payload["run_dir"])}</span><br/>
    SAFE: No external call · No rescan · No source read · No source mutation · No canonical merge · No DB write · No apply
  </div>
</div></body></html>"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(doc, encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-run", required=True)
    ap.add_argument("--run-dir", required=True)
    args = ap.parse_args()

    source_run = Path(args.source_run)
    run_dir = Path(args.run_dir)
    output = run_dir / "output"
    report = run_dir / "report"
    precheck_dir = run_dir / "_package_specific_precheck"
    param_dir = run_dir / "_governance_default_parameters"

    output.mkdir(parents=True, exist_ok=True)
    report.mkdir(parents=True, exist_ok=True)
    precheck_dir.mkdir(parents=True, exist_ok=True)
    param_dir.mkdir(parents=True, exist_ok=True)

    f4_path = source_run / "_grouped_review_clearance_package" / "VIA_v0115F4_GroupedReviewClearancePackage.csv"
    package_rows = read_csv(f4_path)

    precheck_rows = build_precheck_rows(package_rows)
    split = split_outputs(precheck_rows)
    summary = build_summary(precheck_rows)
    process_matrix = build_process_matrix(precheck_rows)
    default_params = build_default_parameters(precheck_rows)
    validation = build_validation(precheck_rows, default_params)
    readiness = build_readiness(precheck_rows, validation)

    write_csv(precheck_dir / "VIA_v0115F5_PackageSpecificPrecheckMatrix.csv", precheck_rows)
    write_csv(precheck_dir / "VIA_v0115F5_PrecheckSummaryMatrix.csv", summary)
    write_csv(precheck_dir / "VIA_v0115F5_ProcessSupportiveVdfVapOthersMatrix.csv", process_matrix)
    write_csv(precheck_dir / "VIA_v0115F5_ValidationMatrix.csv", validation)
    write_csv(output / "VIA_v0115F5_ReadinessGate.csv", readiness)

    write_json(precheck_dir / "VIA_v0115F5_PackageSpecificPrecheckMatrix.json", precheck_rows)
    write_json(precheck_dir / "VIA_v0115F5_PrecheckSummaryMatrix.json", summary)
    write_json(precheck_dir / "VIA_v0115F5_ProcessSupportiveVdfVapOthersMatrix.json", process_matrix)
    write_json(precheck_dir / "VIA_v0115F5_ValidationMatrix.json", validation)
    write_json(output / "VIA_v0115F5_ReadinessGate.json", readiness)

    write_json(param_dir / "VIA_v0115F5_GovernanceDefaultParameters.json", default_params)

    for name, rows in split.items():
        write_csv(precheck_dir / f"VIA_v0115F5_{name}.csv", rows)
        write_json(precheck_dir / f"VIA_v0115F5_{name}.json", rows)

    html_path = report / "VIA_v0115F5_PackageSpecificPrecheck_OnePage.html"
    payload = {
        "source_run": str(source_run),
        "run_dir": str(run_dir),
        "precheck_rows": precheck_rows,
        "summary": summary,
        "process_matrix": process_matrix,
        "default_parameters": default_params,
        "validation": validation,
        "readiness": readiness
    }
    write_html(html_path, payload)

    manifest = {
        "schema_version": "VIA_v0115F5_PackageSpecificPrecheckOnly",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "gate": readiness[0]["def_gate_status"],
        "source_run": str(source_run),
        "run_dir": str(run_dir),
        "report": str(html_path),
        "outputs": {
            "precheck_matrix": str(precheck_dir / "VIA_v0115F5_PackageSpecificPrecheckMatrix.csv"),
            "summary": str(precheck_dir / "VIA_v0115F5_PrecheckSummaryMatrix.csv"),
            "process_matrix": str(precheck_dir / "VIA_v0115F5_ProcessSupportiveVdfVapOthersMatrix.csv"),
            "default_parameters": str(param_dir / "VIA_v0115F5_GovernanceDefaultParameters.json"),
            "readiness": str(output / "VIA_v0115F5_ReadinessGate.csv")
        },
        "policy": default_params["governance_policy"]
    }
    write_json(output / "VIA_v0115F5_PackageSpecificPrecheck_Manifest.json", manifest)

    print("")
    print("=" * 80)
    print("def VIA v0115F5 Package-Specific Precheck COMPLETE")
    print("=" * 80)
    print(f"Gate       : {readiness[0]['def_gate_status']}")
    print(f"Input Rows : {len(precheck_rows)}")
    print(f"Red        : {readiness[0]['def_red_rows']}")
    print(f"Yellow     : {readiness[0]['def_yellow_rows']}")
    print(f"Green      : {readiness[0]['def_green_rows']}")
    print(f"Report     : {html_path}")
    print(f"Precheck   : {precheck_dir}")
    print(f"Params     : {param_dir}")
    print(f"Output     : {output}")
    print("[SAFE] No source read. No rescan. No apply. No source mutation. No DB write.")


if __name__ == "__main__":
    main()
