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


def build_gap_review(gap_rows: List[Dict[str, str]], decisions: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    decision_map = {
        (prop(r, "def_subsystem"), prop(r, "def_flow_name")): r
        for r in decisions
    }

    rows: List[Dict[str, Any]] = []
    for i, g in enumerate(gap_rows, 1):
        subsystem = prop(g, "def_subsystem")
        flow = prop(g, "def_flow_name")
        d = decision_map.get((subsystem, flow), {})
        decision = prop(g, "def_decision")

        if decision == "PENDING":
            severity = "YELLOW"
            action = "operator_must_decide_approve_hold_reject_or_request_more_evidence"
        elif decision == "APPROVE_LATER":
            severity = "GREEN"
            action = "no_gap_for_review_only_next_phase"
        elif decision == "REJECT":
            severity = "RED"
            action = "block_future_apply_branch"
        else:
            severity = "YELLOW"
            action = "operator_follow_up_required"

        rows.append({
            "def_gap_review_id": f"V0116F2-GAPREVIEW-{i:03d}",
            "def_subsystem": subsystem,
            "def_flow_name": flow,
            "def_decision": decision,
            "def_gap": prop(g, "def_gap"),
            "def_gap_severity": severity,
            "def_blocks_future_apply": prop(g, "def_blocks_future_apply"),
            "def_operator": prop(d, "def_operator"),
            "def_decision_timestamp": prop(d, "def_decision_timestamp"),
            "def_next_required_action": action,
            "def_patch_allowed_now": "false",
            "def_apply_enabled": "false",
            "def_source_mutation": "false",
            "def_db_write": "false"
        })

    return rows


def build_subsystem_gap_summary(gap_review: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    subsystems = sorted(set(prop(r, "def_subsystem") for r in gap_review))
    rows: List[Dict[str, Any]] = []

    for s in subsystems:
        items = [r for r in gap_review if prop(r, "def_subsystem") == s]
        total = len(items)
        approved = sum(1 for r in items if prop(r, "def_decision") == "APPROVE_LATER")
        pending = sum(1 for r in items if prop(r, "def_decision") == "PENDING")
        blocked = sum(1 for r in items if prop(r, "def_blocks_future_apply") == "true")

        if approved == total and total > 0:
            status = "READY_FOR_NEXT_REVIEW_ONLY"
        elif blocked > 0:
            status = "BLOCKS_FUTURE_APPLY_UNTIL_OPERATOR_DECISION"
        else:
            status = "PENDING_REVIEW"

        rows.append({
            "def_subsystem": s,
            "def_total_flows": str(total),
            "def_approved": str(approved),
            "def_pending": str(pending),
            "def_blocks_future_apply": str(blocked),
            "def_subsystem_gap_status": status,
            "def_apply_enabled": "false"
        })

    return rows


def build_flow_gap_summary(gap_review: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    flows = sorted(set(prop(r, "def_flow_name") for r in gap_review))
    rows: List[Dict[str, Any]] = []

    for f in flows:
        items = [r for r in gap_review if prop(r, "def_flow_name") == f]
        total = len(items)
        approved = sum(1 for r in items if prop(r, "def_decision") == "APPROVE_LATER")
        pending = sum(1 for r in items if prop(r, "def_decision") == "PENDING")
        blocked = sum(1 for r in items if prop(r, "def_blocks_future_apply") == "true")

        rows.append({
            "def_flow_name": f,
            "def_total_subsystems": str(total),
            "def_approved": str(approved),
            "def_pending": str(pending),
            "def_blocks_future_apply": str(blocked),
            "def_flow_gap_status": "CLEAR" if approved == total and total > 0 else "GAP_OPEN",
            "def_apply_enabled": "false"
        })

    return rows


def build_operator_next_decision_matrix(gap_review: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []

    for r in gap_review:
        rows.append({
            "def_next_decision_id": "NEXT-" + prop(r, "def_gap_review_id"),
            "def_subsystem": prop(r, "def_subsystem"),
            "def_flow_name": prop(r, "def_flow_name"),
            "def_current_decision": prop(r, "def_decision"),
            "def_recommended_allowed_decisions": "APPROVE_LATER;HOLD;REJECT;REQUEST_MORE_EVIDENCE",
            "def_recommended_default": "HOLD" if prop(r, "def_decision") == "PENDING" else prop(r, "def_decision"),
            "def_decision_requirement": "required_before_future_apply_branch" if prop(r, "def_blocks_future_apply") == "true" else "optional_for_review_only",
            "def_patch_allowed_now": "false",
            "def_apply_enabled": "false"
        })

    return rows


def build_no_action_matrix() -> List[Dict[str, Any]]:
    rules = [
        ("NO_PATCH_NOW", "patch_allowed_now", "false"),
        ("NO_ORIGINAL_DASHBOARD_WRITEBACK", "original_dashboard_writeback", "false"),
        ("NO_SOURCE_MUTATION", "source_mutation", "false"),
        ("NO_CANONICAL_MERGE", "canonical_merge", "false"),
        ("NO_DB_WRITE", "db_write", "false"),
        ("NO_APPLY", "apply_enabled", "false"),
        ("NO_DELETE", "delete", "false"),
        ("NO_STOP_PROCESS", "stop_process", "false"),
        ("APPROVAL_GAP_REVIEW_ONLY", "approval_gap_review_only", "true"),
    ]

    return [
        {
            "def_policy_id": f"V0116F2-NOACT-{i:03d}",
            "def_policy_name": name,
            "def_control": control,
            "def_required_value": value,
            "def_status": "PASS",
            "def_message": "Approval gap review only. No writeback."
        }
        for i, (name, control, value) in enumerate(rules, 1)
    ]


def build_validation(
    f_ready: Dict[str, str],
    decisions: List[Dict[str, str]],
    gap_review: List[Dict[str, Any]],
    subsystem_summary: List[Dict[str, Any]],
    flow_summary: List[Dict[str, Any]],
    next_decision: List[Dict[str, Any]],
    no_action: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    def add(name: str, expected: Any, actual: Any, ok: bool, msg: str) -> None:
        rows.append({
            "def_validation": name,
            "def_expected": expected,
            "def_actual": actual,
            "def_status": "PASS" if ok else "FAIL",
            "def_message": msg
        })

    add("V0116F_GATE_READY", "OPERATOR_DECISION_INTAKE_READY_PENDING_OR_PARTIAL_REVIEW_ONLY", prop(f_ready, "def_gate_status"), prop(f_ready, "def_gate_status") in {
        "OPERATOR_DECISION_INTAKE_READY_PENDING_OR_PARTIAL_REVIEW_ONLY",
        "OPERATOR_DECISION_INTAKE_READY_ALL_APPROVED_REVIEW_ONLY"
    }, "v0116F must be ready.")
    add("INPUT_448", "448", prop(f_ready, "def_input_rows"), prop(f_ready, "def_input_rows") == "448", "Input continuity.")
    add("DECISION_ROWS_9", 9, len(decisions), len(decisions) == 9, "Decision rows.")
    add("GAP_REVIEW_ROWS_9", 9, len(gap_review), len(gap_review) == 9, "Gap review rows.")
    add("SUBSYSTEM_SUMMARY_ROWS_3", 3, len(subsystem_summary), len(subsystem_summary) == 3, "Subsystem summary rows.")
    add("FLOW_SUMMARY_ROWS_3", 3, len(flow_summary), len(flow_summary) == 3, "Flow summary rows.")
    add("NEXT_DECISION_ROWS_9", 9, len(next_decision), len(next_decision) == 9, "Next decision rows.")
    add("NO_PATCH_ALLOWED", "false", ",".join(sorted(set(prop(r, "def_patch_allowed_now") for r in gap_review))), all(prop(r, "def_patch_allowed_now") == "false" for r in gap_review), "No patch.")
    add("NO_APPLY", "false", ",".join(sorted(set(prop(r, "def_apply_enabled") for r in gap_review))), all(prop(r, "def_apply_enabled") == "false" for r in gap_review), "No apply.")
    add("NO_SOURCE_MUTATION", "false", ",".join(sorted(set(prop(r, "def_source_mutation") for r in gap_review))), all(prop(r, "def_source_mutation") == "false" for r in gap_review), "No source mutation.")
    add("NO_DB_WRITE", "false", ",".join(sorted(set(prop(r, "def_db_write") for r in gap_review))), all(prop(r, "def_db_write") == "false" for r in gap_review), "No DB write.")
    add("NO_ACTION_POLICY_PRESENT", ">=9", len(no_action), len(no_action) >= 9, "No-action policy matrix.")

    return rows


def build_readiness(validation: List[Dict[str, Any]], f_ready: Dict[str, str], gap_review: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    fail = sum(1 for r in validation if prop(r, "def_status") != "PASS")
    gaps_open = sum(1 for r in gap_review if prop(r, "def_gap") != "NONE")
    blocks = sum(1 for r in gap_review if prop(r, "def_blocks_future_apply") == "true")
    pending = sum(1 for r in gap_review if prop(r, "def_decision") == "PENDING")
    approved = sum(1 for r in gap_review if prop(r, "def_decision") == "APPROVE_LATER")

    if fail == 0 and gaps_open == 0 and approved == 9:
        gate = "APPROVAL_GAP_REVIEW_CLEAR_ALL_APPROVED_REVIEW_ONLY"
        next_phase = "v0116G pre-apply backup package only"
    elif fail == 0:
        gate = "APPROVAL_GAP_REVIEW_READY_GAPS_OPEN_REVIEW_ONLY"
        next_phase = "v0116F3 operator decision recommendation only"
    else:
        gate = "BLOCKED_BY_v0116F2_GAP_REVIEW_VALIDATION_FAIL"
        next_phase = "blocked"

    return [{
        "def_gate_status": gate,
        "def_allow_next": "true" if fail == 0 else "false",
        "def_reason": "v0116F2 reviewed operator approval gaps. No patch, no apply.",
        "def_input_rows": prop(f_ready, "def_input_rows", "448"),
        "def_decision_rows": prop(f_ready, "def_decision_rows", "9"),
        "def_approved": str(approved),
        "def_pending": str(pending),
        "def_gap_open": str(gaps_open),
        "def_blocks_future_apply": str(blocks),
        "def_validation_fail": str(fail),
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
        if "FAIL" in joined or "REJECT" in joined or "RED" in joined:
            cls = "risk-red"
        elif "PENDING" in joined or "GAP_OPEN" in joined or "YELLOW" in joined or "HOLD" in joined:
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
        ("Approved", prop(readiness, "def_approved")),
        ("Pending", prop(readiness, "def_pending")),
        ("GapOpen", prop(readiness, "def_gap_open")),
        ("Blocks", prop(readiness, "def_blocks_future_apply")),
        ("Fail", prop(readiness, "def_validation_fail")),
        ("Next", prop(readiness, "def_next_allowed_phase")),
        ("Apply", prop(readiness, "def_apply_enabled"))
    ]:
        cards += f"<div class='card'><div class='k'>{h(k)}</div><div class='v'>{h(v)}</div></div>"

    doc = f"""<!doctype html>
<html lang="zh-Hant">
<head><meta charset="utf-8"/><title>VIA v0116F2 Approval Gap Review</title>{style}</head>
<body><div class="wrap">
<h1>def VIA v0116F2 · Approval Gap Review Only</h1>
<div class="sub">Pending Approval Gap Review · 3 Subsystems × 3 Flows · No Patch · No Apply</div>
<div class="cards">{cards}</div>

<div class="sec"><h2>Readiness Gate</h2>{render_table(payload["readiness"], ["def_gate_status","def_allow_next","def_reason","def_input_rows","def_decision_rows","def_approved","def_pending","def_gap_open","def_blocks_future_apply","def_validation_fail","def_patch_allowed_now","def_original_dashboard_writeback","def_source_mutation","def_apply_enabled","def_db_write","def_next_allowed_phase"])}</div>
<div class="sec"><h2>Validation Matrix</h2>{render_table(payload["validation"], ["def_validation","def_expected","def_actual","def_status","def_message"])}</div>
<div class="sec"><h2>Approval Gap Review Matrix</h2>{render_table(payload["gap_review"], ["def_gap_review_id","def_subsystem","def_flow_name","def_decision","def_gap","def_gap_severity","def_blocks_future_apply","def_operator","def_decision_timestamp","def_next_required_action","def_apply_enabled"])}</div>
<div class="sec"><h2>Subsystem Gap Summary</h2>{render_table(payload["subsystem_summary"], ["def_subsystem","def_total_flows","def_approved","def_pending","def_blocks_future_apply","def_subsystem_gap_status","def_apply_enabled"])}</div>
<div class="sec"><h2>Flow Gap Summary</h2>{render_table(payload["flow_summary"], ["def_flow_name","def_total_subsystems","def_approved","def_pending","def_blocks_future_apply","def_flow_gap_status","def_apply_enabled"])}</div>
<div class="sec"><h2>Operator Next Decision Matrix</h2>{render_table(payload["next_decision"], ["def_next_decision_id","def_subsystem","def_flow_name","def_current_decision","def_recommended_allowed_decisions","def_recommended_default","def_decision_requirement","def_patch_allowed_now","def_apply_enabled"])}</div>
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
    gap_dir = run_dir / "_approval_gap_review"

    output.mkdir(parents=True, exist_ok=True)
    report.mkdir(parents=True, exist_ok=True)
    gap_dir.mkdir(parents=True, exist_ok=True)

    f_ready = first(read_csv(source_run / "output" / "VIA_v0116F_ReadinessGate.csv"))
    f_manifest = read_json(source_run / "output" / "VIA_v0116F_OperatorDecisionIntake_Manifest.json")
    f_dir = source_run / "_operator_decision_intake"

    decisions = read_csv(f_dir / "VIA_v0116F_OperatorDecisionIntakeMatrix.csv")
    gap_rows = read_csv(f_dir / "VIA_v0116F_ApprovalGapMatrix.csv")

    gap_review = build_gap_review(gap_rows, decisions)
    subsystem_summary = build_subsystem_gap_summary(gap_review)
    flow_summary = build_flow_gap_summary(gap_review)
    next_decision = build_operator_next_decision_matrix(gap_review)
    no_action = build_no_action_matrix()
    validation = build_validation(f_ready, decisions, gap_review, subsystem_summary, flow_summary, next_decision, no_action)
    readiness = build_readiness(validation, f_ready, gap_review)

    write_csv(gap_dir / "VIA_v0116F2_ApprovalGapReviewMatrix.csv", gap_review)
    write_csv(gap_dir / "VIA_v0116F2_SubsystemGapSummary.csv", subsystem_summary)
    write_csv(gap_dir / "VIA_v0116F2_FlowGapSummary.csv", flow_summary)
    write_csv(gap_dir / "VIA_v0116F2_OperatorNextDecisionMatrix.csv", next_decision)
    write_csv(gap_dir / "VIA_v0116F2_NoActionMatrix.csv", no_action)
    write_csv(gap_dir / "VIA_v0116F2_ValidationMatrix.csv", validation)
    write_csv(output / "VIA_v0116F2_ReadinessGate.csv", readiness)

    write_json(gap_dir / "VIA_v0116F2_ApprovalGapReviewMatrix.json", gap_review)
    write_json(gap_dir / "VIA_v0116F2_SubsystemGapSummary.json", subsystem_summary)
    write_json(gap_dir / "VIA_v0116F2_FlowGapSummary.json", flow_summary)
    write_json(gap_dir / "VIA_v0116F2_OperatorNextDecisionMatrix.json", next_decision)
    write_json(gap_dir / "VIA_v0116F2_NoActionMatrix.json", no_action)
    write_json(gap_dir / "VIA_v0116F2_ValidationMatrix.json", validation)
    write_json(output / "VIA_v0116F2_ReadinessGate.json", readiness)

    report_path = report / "VIA_v0116F2_ApprovalGapReview_Report.html"
    payload = {
        "readiness": readiness,
        "validation": validation,
        "gap_review": gap_review,
        "subsystem_summary": subsystem_summary,
        "flow_summary": flow_summary,
        "next_decision": next_decision,
        "no_action": no_action
    }
    write_report(report_path, payload)

    final_manifest = {
        "schema_version": "VIA_v0116F2_ApprovalGapReviewOnly",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "gate": readiness[0]["def_gate_status"],
        "source_run": str(source_run),
        "run_dir": str(run_dir),
        "v0116f_manifest": f_manifest,
        "report": str(report_path),
        "outputs": {
            "readiness": str(output / "VIA_v0116F2_ReadinessGate.csv"),
            "gap_review": str(gap_dir / "VIA_v0116F2_ApprovalGapReviewMatrix.csv"),
            "subsystem_summary": str(gap_dir / "VIA_v0116F2_SubsystemGapSummary.csv"),
            "flow_summary": str(gap_dir / "VIA_v0116F2_FlowGapSummary.csv"),
            "next_decision": str(gap_dir / "VIA_v0116F2_OperatorNextDecisionMatrix.csv"),
            "validation": str(gap_dir / "VIA_v0116F2_ValidationMatrix.csv")
        },
        "policy": {
            "approval_gap_review_only": True,
            "patch_allowed_now": False,
            "original_dashboard_writeback": False,
            "source_mutation": False,
            "canonical_merge": False,
            "db_write": False,
            "apply_enabled": False
        }
    }
    write_json(output / "VIA_v0116F2_ApprovalGapReview_Manifest.json", final_manifest)

    print("")
    print("=" * 80)
    print("def VIA v0116F2 Approval Gap Review COMPLETE")
    print("=" * 80)
    print(f"Gate        : {readiness[0]['def_gate_status']}")
    print(f"Approved    : {readiness[0]['def_approved']}")
    print(f"Pending     : {readiness[0]['def_pending']}")
    print(f"GapOpen     : {readiness[0]['def_gap_open']}")
    print(f"Blocks      : {readiness[0]['def_blocks_future_apply']}")
    print(f"Fail        : {readiness[0]['def_validation_fail']}")
    print(f"Next        : {readiness[0]['def_next_allowed_phase']}")
    print(f"Report      : {report_path}")
    print(f"GapDir      : {gap_dir}")
    print("[SAFE] Approval gap review only. No patch. No apply. No DB write.")


if __name__ == "__main__":
    main()
