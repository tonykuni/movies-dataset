from __future__ import annotations

import argparse
import csv
import html
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def read_json(path: Path) -> Any:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


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


def first(rows: List[Dict[str, str]]) -> Dict[str, str]:
    return rows[0] if rows else {}


def checklist_for_flow(flow: str, subsystem: str) -> Dict[str, str]:
    if flow == "DASHBOARD_BINDING_APPROVAL":
        return {
            "criteria": "Preview copy inspected; 8 cards readable; target section acceptable; BEFORE_BODY_END insertion plan acceptable.",
            "risk": "Wrong placement may reduce UI clarity but does not affect data/source if patch remains guarded.",
            "recommended_default": "HOLD",
            "approve_condition": "Approve later only after visually confirming preview copy and card location."
        }

    if flow == "RISK_GUARD_APPROVAL":
        return {
            "criteria": "RED has no repair/apply/batch-fix button; YELLOW no full-file-read; all GREEN read-only; secret safety preserved.",
            "risk": "If guard is weak, future dashboard may expose unsafe buttons.",
            "recommended_default": "HOLD",
            "approve_condition": "Approve later only if all guard rows remain locked and no apply UI is exposed."
        }

    return {
        "criteria": "Backup pattern, hash check, rollback restore rule, preview-copy-as-reference rule all accepted.",
        "risk": "Without rollback, future patch branch cannot fail safely.",
        "recommended_default": "HOLD",
        "approve_condition": "Approve later only after accepting backup-before-apply and hash-verify-before/after requirements."
    }


def build_recommendation_matrix(gap_review: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    rows = []

    for i, g in enumerate(gap_review, 1):
        subsystem = prop(g, "def_subsystem")
        flow = prop(g, "def_flow_name")
        decision = prop(g, "def_decision")
        checklist = checklist_for_flow(flow, subsystem)

        if decision == "APPROVE_LATER":
            rec = "KEEP_APPROVE_LATER_FOR_NEXT_REVIEW_ONLY"
            severity = "GREEN"
            next_action = "eligible_for_v0116G_review_only_if_all_nine_are_approved"
        elif decision == "REJECT":
            rec = "KEEP_REJECT_AND_BLOCK_FUTURE_APPLY"
            severity = "RED"
            next_action = "do_not_apply; revise plan"
        elif decision == "REQUEST_MORE_EVIDENCE":
            rec = "COLLECT_EVIDENCE_BEFORE_APPROVAL"
            severity = "YELLOW"
            next_action = "generate evidence addendum before approval"
        else:
            rec = "HOLD_UNTIL_OPERATOR_APPROVES_OR_REQUESTS_EVIDENCE"
            severity = "YELLOW"
            next_action = "manual review required; if accepted rerun v0116F with APPROVE_LATER"

        rows.append({
            "def_recommendation_id": f"V0116F3-REC-{i:03d}",
            "def_subsystem": subsystem,
            "def_flow_name": flow,
            "def_current_decision": decision,
            "def_recommended_decision": rec,
            "def_recommended_default": checklist["recommended_default"],
            "def_recommendation_severity": severity,
            "def_review_criteria": checklist["criteria"],
            "def_primary_risk": checklist["risk"],
            "def_approve_later_condition": checklist["approve_condition"],
            "def_next_action": next_action,
            "def_patch_allowed_now": "false",
            "def_decision_writeback": "false",
            "def_apply_enabled": "false",
            "def_source_mutation": "false",
            "def_db_write": "false"
        })

    return rows


def build_evidence_checklist(recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []

    for i, r in enumerate(recommendations, 1):
        flow = prop(r, "def_flow_name")

        if flow == "DASHBOARD_BINDING_APPROVAL":
            checks = [
                "Preview copy opened successfully",
                "All 8 cards visible and readable",
                "Insertion zone BEFORE_BODY_END accepted"
            ]
        elif flow == "RISK_GUARD_APPROVAL":
            checks = [
                "RED card has no repair/apply/batch-fix UI",
                "YELLOW card has no full-file-read path",
                "All cards remain no apply / no DB write"
            ]
        else:
            checks = [
                "Pre-apply backup requirement accepted",
                "Before/after hash check accepted",
                "Rollback restore requires operator approval"
            ]

        rows.append({
            "def_checklist_id": f"V0116F3-CHECK-{i:03d}",
            "def_subsystem": prop(r, "def_subsystem"),
            "def_flow_name": flow,
            "def_check_1": checks[0],
            "def_check_2": checks[1],
            "def_check_3": checks[2],
            "def_required_before_approve_later": "true",
            "def_status": "PENDING_OPERATOR_REVIEW",
            "def_apply_enabled": "false"
        })

    return rows


def build_subsystem_recommendation_summary(recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    subsystems = sorted(set(prop(r, "def_subsystem") for r in recommendations))

    for s in subsystems:
        items = [r for r in recommendations if prop(r, "def_subsystem") == s]
        green = sum(1 for r in items if prop(r, "def_recommendation_severity") == "GREEN")
        yellow = sum(1 for r in items if prop(r, "def_recommendation_severity") == "YELLOW")
        red = sum(1 for r in items if prop(r, "def_recommendation_severity") == "RED")

        status = "READY_IF_OPERATOR_APPROVES_ALL_THREE" if red == 0 else "BLOCKED_BY_REJECT"
        if yellow > 0:
            status = "PENDING_OPERATOR_REVIEW"

        rows.append({
            "def_subsystem": s,
            "def_total_flows": str(len(items)),
            "def_green_recommendations": str(green),
            "def_yellow_recommendations": str(yellow),
            "def_red_recommendations": str(red),
            "def_recommendation_status": status,
            "def_apply_enabled": "false"
        })

    return rows


def build_flow_recommendation_summary(recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    flows = sorted(set(prop(r, "def_flow_name") for r in recommendations))

    for f in flows:
        items = [r for r in recommendations if prop(r, "def_flow_name") == f]
        green = sum(1 for r in items if prop(r, "def_recommendation_severity") == "GREEN")
        yellow = sum(1 for r in items if prop(r, "def_recommendation_severity") == "YELLOW")
        red = sum(1 for r in items if prop(r, "def_recommendation_severity") == "RED")

        rows.append({
            "def_flow_name": f,
            "def_total_subsystems": str(len(items)),
            "def_green_recommendations": str(green),
            "def_yellow_recommendations": str(yellow),
            "def_red_recommendations": str(red),
            "def_recommendation_status": "PENDING_OPERATOR_REVIEW" if yellow > 0 else "READY_FOR_NEXT_REVIEW_ONLY",
            "def_apply_enabled": "false"
        })

    return rows


def build_next_command_hint(recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    yellow = sum(1 for r in recommendations if prop(r, "def_recommendation_severity") == "YELLOW")
    red = sum(1 for r in recommendations if prop(r, "def_recommendation_severity") == "RED")

    if red > 0:
        action = "do_not_approve; revise patch plan or reject"
        decision_mode = "REJECT_OR_HOLD"
    elif yellow > 0:
        action = "after manual review, rerun v0116F with APPROVE_LATER if all nine are accepted"
        decision_mode = "APPROVE_LATER"
    else:
        action = "all clear for v0116G review-only backup package"
        decision_mode = "APPROVE_LATER"

    return [{
        "def_hint_id": "V0116F3-NEXT-001",
        "def_current_state": "recommendation_only_no_decision_writeback",
        "def_recommended_operator_action": action,
        "def_decision_mode_to_use_if_approved": decision_mode,
        "def_power_shell_change": '$DecisionMode = "APPROVE_LATER"',
        "def_note_change": '$DecisionNote = "Operator reviewed VDF/VAP/VRN three-flow package and approves next review-only phase. No patch, no apply."',
        "def_patch_allowed_now": "false",
        "def_apply_enabled": "false"
    }]


def build_no_action_matrix() -> List[Dict[str, Any]]:
    rules = [
        ("NO_DECISION_WRITEBACK", "decision_writeback", "false"),
        ("NO_PATCH_NOW", "patch_allowed_now", "false"),
        ("NO_ORIGINAL_DASHBOARD_WRITEBACK", "original_dashboard_writeback", "false"),
        ("NO_SOURCE_MUTATION", "source_mutation", "false"),
        ("NO_CANONICAL_MERGE", "canonical_merge", "false"),
        ("NO_DB_WRITE", "db_write", "false"),
        ("NO_APPLY", "apply_enabled", "false"),
        ("NO_DELETE", "delete", "false"),
        ("NO_STOP_PROCESS", "stop_process", "false"),
        ("RECOMMENDATION_ONLY", "operator_decision_recommendation_only", "true"),
    ]

    return [
        {
            "def_policy_id": f"V0116F3-NOACT-{i:03d}",
            "def_policy_name": name,
            "def_control": control,
            "def_required_value": value,
            "def_status": "PASS",
            "def_message": "Recommendation only. No writeback."
        }
        for i, (name, control, value) in enumerate(rules, 1)
    ]


def build_validation(
    f2_ready: Dict[str, str],
    gap_review: List[Dict[str, str]],
    recommendations: List[Dict[str, Any]],
    checklist: List[Dict[str, Any]],
    subsystem_summary: List[Dict[str, Any]],
    flow_summary: List[Dict[str, Any]],
    next_hint: List[Dict[str, Any]],
    no_action: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    rows = []

    def add(name: str, expected: Any, actual: Any, ok: bool, msg: str) -> None:
        rows.append({
            "def_validation": name,
            "def_expected": expected,
            "def_actual": actual,
            "def_status": "PASS" if ok else "FAIL",
            "def_message": msg
        })

    add("V0116F2_GATE_READY", "APPROVAL_GAP_REVIEW_READY_GAPS_OPEN_REVIEW_ONLY", prop(f2_ready, "def_gate_status"), prop(f2_ready, "def_gate_status") in {
        "APPROVAL_GAP_REVIEW_READY_GAPS_OPEN_REVIEW_ONLY",
        "APPROVAL_GAP_REVIEW_CLEAR_ALL_APPROVED_REVIEW_ONLY"
    }, "v0116F2 must be ready.")
    add("INPUT_448", "448", prop(f2_ready, "def_input_rows"), prop(f2_ready, "def_input_rows") == "448", "Input continuity.")
    add("GAP_ROWS_9", 9, len(gap_review), len(gap_review) == 9, "Gap rows.")
    add("RECOMMENDATION_ROWS_9", 9, len(recommendations), len(recommendations) == 9, "Recommendation rows.")
    add("CHECKLIST_ROWS_9", 9, len(checklist), len(checklist) == 9, "Evidence checklist rows.")
    add("SUBSYSTEM_SUMMARY_ROWS_3", 3, len(subsystem_summary), len(subsystem_summary) == 3, "Subsystem summary rows.")
    add("FLOW_SUMMARY_ROWS_3", 3, len(flow_summary), len(flow_summary) == 3, "Flow summary rows.")
    add("NEXT_HINT_PRESENT", 1, len(next_hint), len(next_hint) == 1, "Next command hint.")
    add("NO_DECISION_WRITEBACK", "false", ",".join(sorted(set(prop(r, "def_decision_writeback") for r in recommendations))), all(prop(r, "def_decision_writeback") == "false" for r in recommendations), "No decision writeback.")
    add("NO_PATCH_ALLOWED", "false", ",".join(sorted(set(prop(r, "def_patch_allowed_now") for r in recommendations))), all(prop(r, "def_patch_allowed_now") == "false" for r in recommendations), "No patch.")
    add("NO_APPLY", "false", ",".join(sorted(set(prop(r, "def_apply_enabled") for r in recommendations))), all(prop(r, "def_apply_enabled") == "false" for r in recommendations), "No apply.")
    add("NO_SOURCE_MUTATION", "false", ",".join(sorted(set(prop(r, "def_source_mutation") for r in recommendations))), all(prop(r, "def_source_mutation") == "false" for r in recommendations), "No source mutation.")
    add("NO_DB_WRITE", "false", ",".join(sorted(set(prop(r, "def_db_write") for r in recommendations))), all(prop(r, "def_db_write") == "false" for r in recommendations), "No DB write.")
    add("NO_ACTION_POLICY_PRESENT", ">=10", len(no_action), len(no_action) >= 10, "No-action policy matrix.")

    return rows


def build_readiness(validation: List[Dict[str, Any]], f2_ready: Dict[str, str], recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    fail = sum(1 for r in validation if prop(r, "def_status") != "PASS")
    yellow = sum(1 for r in recommendations if prop(r, "def_recommendation_severity") == "YELLOW")
    green = sum(1 for r in recommendations if prop(r, "def_recommendation_severity") == "GREEN")
    red = sum(1 for r in recommendations if prop(r, "def_recommendation_severity") == "RED")

    if fail == 0 and red == 0 and yellow > 0:
        gate = "OPERATOR_DECISION_RECOMMENDATION_READY_REVIEW_REQUIRED_ONLY"
        next_phase = "rerun v0116F with APPROVE_LATER only after manual approval"
    elif fail == 0 and red == 0:
        gate = "OPERATOR_DECISION_RECOMMENDATION_READY_ALL_CLEAR_REVIEW_ONLY"
        next_phase = "v0116G pre-apply backup package only"
    elif fail == 0:
        gate = "OPERATOR_DECISION_RECOMMENDATION_READY_WITH_REJECT_BLOCK_REVIEW_ONLY"
        next_phase = "revise_or_reject_patch_plan"
    else:
        gate = "BLOCKED_BY_v0116F3_RECOMMENDATION_VALIDATION_FAIL"
        next_phase = "blocked"

    return [{
        "def_gate_status": gate,
        "def_allow_next": "true" if fail == 0 else "false",
        "def_reason": "v0116F3 generated operator decision recommendations. No decision writeback, no patch, no apply.",
        "def_input_rows": prop(f2_ready, "def_input_rows", "448"),
        "def_recommendation_rows": "9",
        "def_green_recommendations": str(green),
        "def_yellow_recommendations": str(yellow),
        "def_red_recommendations": str(red),
        "def_validation_fail": str(fail),
        "def_decision_writeback": "false",
        "def_patch_allowed_now": "false",
        "def_original_dashboard_writeback": "false",
        "def_source_mutation": "false",
        "def_canonical_merge": "false",
        "def_apply_enabled": "false",
        "def_db_write": "false",
        "def_next_allowed_phase": next_phase
    }]


def render_table(rows: List[Dict[str, Any]], cols: List[str]) -> str:
    out = ["<table><thead><tr>"]
    for c in cols:
        out.append(f"<th>{h(c)}</th>")
    out.append("</tr></thead><tbody>")
    for r in rows:
        joined = " ".join(str(v) for v in r.values()).upper()
        cls = "risk-green"
        if "FAIL" in joined or "RED" in joined or "REJECT" in joined:
            cls = "risk-red"
        elif "YELLOW" in joined or "HOLD" in joined or "PENDING" in joined or "REVIEW_REQUIRED" in joined:
            cls = "risk-yellow"
        out.append(f"<tr class='{cls}'>")
        for c in cols:
            out.append(f"<td>{h(prop(r, c))}</td>")
        out.append("</tr>")
    out.append("</tbody></table>")
    return "".join(out)


def write_report(path: Path, payload: Dict[str, Any]) -> None:
    readiness = payload["readiness"][0]

    style = """
<style>
body{font-family:"Microsoft JhengHei","Noto Sans TC",Arial,sans-serif;background:#f7f6f2;color:#24231f;margin:0}
.wrap{max-width:1780px;margin:0 auto;padding:18px}
h1{font-size:18px}.sub{color:#706d64;font-size:12px}
.cards{display:grid;grid-template-columns:repeat(8,1fr);gap:8px;margin:12px 0}
.card{background:#fffefa;border:1px solid #dedbd2;border-radius:12px;padding:8px}
.k{font-size:10px;color:#706d64}.v{font:700 12px Consolas,monospace;margin-top:4px}
.sec{background:#fffefa;border:1px solid #dedbd2;border-radius:14px;padding:10px;margin:10px 0;overflow:auto}
table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:10px}
th,td{border-bottom:1px solid #ebe8df;padding:5px;vertical-align:top;word-break:break-word}
th{background:#f0eee8;text-align:left}
.risk-red td{background:rgba(201,107,90,.09)}
.risk-yellow td{background:rgba(196,148,58,.09)}
.risk-green td{background:rgba(90,158,111,.075)}
</style>
"""

    cards = ""
    for k, v in [
        ("Gate", prop(readiness, "def_gate_status")),
        ("Rows", prop(readiness, "def_recommendation_rows")),
        ("Green", prop(readiness, "def_green_recommendations")),
        ("Yellow", prop(readiness, "def_yellow_recommendations")),
        ("Red", prop(readiness, "def_red_recommendations")),
        ("Fail", prop(readiness, "def_validation_fail")),
        ("DecisionWB", prop(readiness, "def_decision_writeback")),
        ("Apply", prop(readiness, "def_apply_enabled"))
    ]:
        cards += f"<div class='card'><div class='k'>{h(k)}</div><div class='v'>{h(v)}</div></div>"

    doc = f"""<!doctype html>
<html lang="zh-Hant">
<head><meta charset="utf-8"/><title>VIA v0116F3 Operator Decision Recommendation</title>{style}</head>
<body><div class="wrap">
<h1>def VIA v0116F3 · Operator Decision Recommendation Only</h1>
<div class="sub">Recommendation Only · No Decision Writeback · No Patch · No Apply</div>
<div class="cards">{cards}</div>

<div class="sec"><h2>Readiness Gate</h2>{render_table(payload["readiness"], ["def_gate_status","def_allow_next","def_reason","def_input_rows","def_recommendation_rows","def_green_recommendations","def_yellow_recommendations","def_red_recommendations","def_validation_fail","def_decision_writeback","def_patch_allowed_now","def_original_dashboard_writeback","def_source_mutation","def_apply_enabled","def_db_write","def_next_allowed_phase"])}</div>
<div class="sec"><h2>Validation Matrix</h2>{render_table(payload["validation"], ["def_validation","def_expected","def_actual","def_status","def_message"])}</div>
<div class="sec"><h2>Operator Recommendation Matrix</h2>{render_table(payload["recommendations"], ["def_recommendation_id","def_subsystem","def_flow_name","def_current_decision","def_recommended_decision","def_recommended_default","def_recommendation_severity","def_review_criteria","def_primary_risk","def_approve_later_condition","def_next_action","def_apply_enabled"])}</div>
<div class="sec"><h2>Evidence Checklist Matrix</h2>{render_table(payload["checklist"], ["def_checklist_id","def_subsystem","def_flow_name","def_check_1","def_check_2","def_check_3","def_required_before_approve_later","def_status","def_apply_enabled"])}</div>
<div class="sec"><h2>Subsystem Recommendation Summary</h2>{render_table(payload["subsystem_summary"], ["def_subsystem","def_total_flows","def_green_recommendations","def_yellow_recommendations","def_red_recommendations","def_recommendation_status","def_apply_enabled"])}</div>
<div class="sec"><h2>Flow Recommendation Summary</h2>{render_table(payload["flow_summary"], ["def_flow_name","def_total_subsystems","def_green_recommendations","def_yellow_recommendations","def_red_recommendations","def_recommendation_status","def_apply_enabled"])}</div>
<div class="sec"><h2>Next Command Hint</h2>{render_table(payload["next_hint"], ["def_hint_id","def_current_state","def_recommended_operator_action","def_decision_mode_to_use_if_approved","def_power_shell_change","def_note_change","def_patch_allowed_now","def_apply_enabled"])}</div>
<div class="sec"><h2>No-Action Matrix</h2>{render_table(payload["no_action"], ["def_policy_id","def_policy_name","def_control","def_required_value","def_status","def_message"])}</div>
</div></body></html>"""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(doc, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-run", required=True)
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args()

    source_run = Path(args.source_run)
    run_dir = Path(args.run_dir)
    output = run_dir / "output"
    report = run_dir / "report"
    rec_dir = run_dir / "_operator_decision_recommendation"

    output.mkdir(parents=True, exist_ok=True)
    report.mkdir(parents=True, exist_ok=True)
    rec_dir.mkdir(parents=True, exist_ok=True)

    f2_ready = first(read_csv(source_run / "output" / "VIA_v0116F2_ReadinessGate.csv"))
    f2_manifest = read_json(source_run / "output" / "VIA_v0116F2_ApprovalGapReview_Manifest.json")
    f2_dir = source_run / "_approval_gap_review"

    gap_review = read_csv(f2_dir / "VIA_v0116F2_ApprovalGapReviewMatrix.csv")

    recommendations = build_recommendation_matrix(gap_review)
    checklist = build_evidence_checklist(recommendations)
    subsystem_summary = build_subsystem_recommendation_summary(recommendations)
    flow_summary = build_flow_recommendation_summary(recommendations)
    next_hint = build_next_command_hint(recommendations)
    no_action = build_no_action_matrix()
    validation = build_validation(f2_ready, gap_review, recommendations, checklist, subsystem_summary, flow_summary, next_hint, no_action)
    readiness = build_readiness(validation, f2_ready, recommendations)

    write_csv(rec_dir / "VIA_v0116F3_OperatorRecommendationMatrix.csv", recommendations)
    write_csv(rec_dir / "VIA_v0116F3_EvidenceChecklistMatrix.csv", checklist)
    write_csv(rec_dir / "VIA_v0116F3_SubsystemRecommendationSummary.csv", subsystem_summary)
    write_csv(rec_dir / "VIA_v0116F3_FlowRecommendationSummary.csv", flow_summary)
    write_csv(rec_dir / "VIA_v0116F3_NextCommandHint.csv", next_hint)
    write_csv(rec_dir / "VIA_v0116F3_NoActionMatrix.csv", no_action)
    write_csv(rec_dir / "VIA_v0116F3_ValidationMatrix.csv", validation)
    write_csv(output / "VIA_v0116F3_ReadinessGate.csv", readiness)

    write_json(rec_dir / "VIA_v0116F3_OperatorRecommendationMatrix.json", recommendations)
    write_json(rec_dir / "VIA_v0116F3_EvidenceChecklistMatrix.json", checklist)
    write_json(rec_dir / "VIA_v0116F3_SubsystemRecommendationSummary.json", subsystem_summary)
    write_json(rec_dir / "VIA_v0116F3_FlowRecommendationSummary.json", flow_summary)
    write_json(rec_dir / "VIA_v0116F3_NextCommandHint.json", next_hint)
    write_json(rec_dir / "VIA_v0116F3_NoActionMatrix.json", no_action)
    write_json(rec_dir / "VIA_v0116F3_ValidationMatrix.json", validation)
    write_json(output / "VIA_v0116F3_ReadinessGate.json", readiness)

    report_path = report / "VIA_v0116F3_OperatorDecisionRecommendation_Report.html"
    payload = {
        "readiness": readiness,
        "validation": validation,
        "recommendations": recommendations,
        "checklist": checklist,
        "subsystem_summary": subsystem_summary,
        "flow_summary": flow_summary,
        "next_hint": next_hint,
        "no_action": no_action
    }
    write_report(report_path, payload)

    final_manifest = {
        "schema_version": "VIA_v0116F3_OperatorDecisionRecommendationOnly",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "gate": readiness[0]["def_gate_status"],
        "source_run": str(source_run),
        "run_dir": str(run_dir),
        "v0116f2_manifest": f2_manifest,
        "report": str(report_path),
        "outputs": {
            "readiness": str(output / "VIA_v0116F3_ReadinessGate.csv"),
            "recommendations": str(rec_dir / "VIA_v0116F3_OperatorRecommendationMatrix.csv"),
            "evidence_checklist": str(rec_dir / "VIA_v0116F3_EvidenceChecklistMatrix.csv"),
            "subsystem_summary": str(rec_dir / "VIA_v0116F3_SubsystemRecommendationSummary.csv"),
            "flow_summary": str(rec_dir / "VIA_v0116F3_FlowRecommendationSummary.csv"),
            "next_hint": str(rec_dir / "VIA_v0116F3_NextCommandHint.csv"),
            "validation": str(rec_dir / "VIA_v0116F3_ValidationMatrix.csv")
        },
        "policy": {
            "recommendation_only": True,
            "decision_writeback": False,
            "patch_allowed_now": False,
            "original_dashboard_writeback": False,
            "source_mutation": False,
            "canonical_merge": False,
            "db_write": False,
            "apply_enabled": False
        }
    }
    write_json(output / "VIA_v0116F3_OperatorDecisionRecommendation_Manifest.json", final_manifest)

    print("")
    print("=" * 80)
    print("def VIA v0116F3 Operator Decision Recommendation COMPLETE")
    print("=" * 80)
    print(f"Gate       : {readiness[0]['def_gate_status']}")
    print(f"Rows       : {readiness[0]['def_recommendation_rows']}")
    print(f"Green      : {readiness[0]['def_green_recommendations']}")
    print(f"Yellow     : {readiness[0]['def_yellow_recommendations']}")
    print(f"Red        : {readiness[0]['def_red_recommendations']}")
    print(f"Fail       : {readiness[0]['def_validation_fail']}")
    print(f"Next       : {readiness[0]['def_next_allowed_phase']}")
    print(f"Report     : {report_path}")
    print(f"RecDir     : {rec_dir}")
    print("[SAFE] Recommendation only. No decision writeback. No patch. No apply. No DB write.")


if __name__ == "__main__":
    main()
