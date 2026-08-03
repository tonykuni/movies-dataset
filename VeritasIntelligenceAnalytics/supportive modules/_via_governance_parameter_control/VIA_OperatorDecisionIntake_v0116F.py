from __future__ import annotations

import argparse
import csv
import html
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


ALLOWED = {"PENDING", "APPROVE_LATER", "HOLD", "REJECT", "REQUEST_MORE_EVIDENCE"}


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


def build_decision_intake(template: List[Dict[str, str]], operator: str, decision: str, note: str) -> List[Dict[str, Any]]:
    decision = decision.upper().strip()
    if decision not in ALLOWED:
        decision = "PENDING"

    rows = []
    now = datetime.now().isoformat(timespec="seconds")

    for r in template:
        rows.append({
            "def_decision_id": prop(r, "def_decision_id"),
            "def_subsystem": prop(r, "def_subsystem"),
            "def_flow_name": prop(r, "def_flow_name"),
            "def_allowed_decisions": prop(r, "def_allowed_decisions"),
            "def_previous_decision": prop(r, "def_current_decision"),
            "def_intake_decision": decision,
            "def_decision_note": note,
            "def_operator": operator,
            "def_decision_timestamp": now,
            "def_patch_allowed_now": "false",
            "def_apply_enabled": "false",
            "def_source_mutation": "false",
            "def_db_write": "false"
        })

    return rows


def build_sync_status(decisions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    subsystems = sorted(set(prop(r, "def_subsystem") for r in decisions))
    rows = []

    for s in subsystems:
        items = [r for r in decisions if prop(r, "def_subsystem") == s]
        approved = sum(1 for r in items if prop(r, "def_intake_decision") == "APPROVE_LATER")
        pending = sum(1 for r in items if prop(r, "def_intake_decision") == "PENDING")
        hold = sum(1 for r in items if prop(r, "def_intake_decision") == "HOLD")
        reject = sum(1 for r in items if prop(r, "def_intake_decision") == "REJECT")
        more = sum(1 for r in items if prop(r, "def_intake_decision") == "REQUEST_MORE_EVIDENCE")

        if approved == 3:
            status = "SUBSYSTEM_APPROVED_FOR_NEXT_REVIEW_ONLY"
        elif reject > 0:
            status = "SUBSYSTEM_REJECTED_BLOCK_FUTURE_APPLY"
        elif hold > 0 or more > 0:
            status = "SUBSYSTEM_HELD_FOR_MORE_REVIEW"
        else:
            status = "SUBSYSTEM_PENDING"

        rows.append({
            "def_subsystem": s,
            "def_total_flows": str(len(items)),
            "def_approve_later": str(approved),
            "def_pending": str(pending),
            "def_hold": str(hold),
            "def_reject": str(reject),
            "def_request_more_evidence": str(more),
            "def_sync_status": status,
            "def_apply_enabled": "false"
        })

    return rows


def build_gap_matrix(decisions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []

    for r in decisions:
        d = prop(r, "def_intake_decision")
        gap = "NONE" if d == "APPROVE_LATER" else "DECISION_NOT_APPROVED"
        rows.append({
            "def_gap_id": "GAP-" + prop(r, "def_decision_id"),
            "def_subsystem": prop(r, "def_subsystem"),
            "def_flow_name": prop(r, "def_flow_name"),
            "def_decision": d,
            "def_gap": gap,
            "def_next_required_action": "none_for_next_review_only" if d == "APPROVE_LATER" else "operator_review_required",
            "def_blocks_future_apply": "false" if d == "APPROVE_LATER" else "true",
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
        ("DECISION_INTAKE_ONLY", "decision_intake_only", "true"),
    ]

    return [
        {
            "def_policy_id": f"V0116F-NOACT-{i:03d}",
            "def_policy_name": name,
            "def_control": control,
            "def_required_value": value,
            "def_status": "PASS",
            "def_message": "Operator decision intake only. No writeback."
        }
        for i, (name, control, value) in enumerate(rules, 1)
    ]


def build_validation(e_ready: Dict[str, str], decisions: List[Dict[str, Any]], sync: List[Dict[str, Any]], gap: List[Dict[str, Any]], no_action: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    def add(name: str, expected: Any, actual: Any, ok: bool, msg: str) -> None:
        rows.append({
            "def_validation": name,
            "def_expected": expected,
            "def_actual": actual,
            "def_status": "PASS" if ok else "FAIL",
            "def_message": msg
        })

    decisions_set = sorted(set(prop(r, "def_intake_decision") for r in decisions))

    add("V0116E_GATE_READY", "OPERATOR_APPROVAL_PACKAGE_READY_REVIEW_ONLY", prop(e_ready, "def_gate_status"), prop(e_ready, "def_gate_status") == "OPERATOR_APPROVAL_PACKAGE_READY_REVIEW_ONLY", "v0116E must be ready.")
    add("INPUT_448", "448", prop(e_ready, "def_input_rows"), prop(e_ready, "def_input_rows") == "448", "Input continuity.")
    add("SYNC_ROWS_9", 9, len(decisions), len(decisions) == 9, "3 subsystems x 3 flows decisions.")
    add("SUBSYSTEM_ROWS_3", 3, len(sync), len(sync) == 3, "3 subsystem sync rows.")
    add("GAP_ROWS_9", 9, len(gap), len(gap) == 9, "One gap row per decision.")
    add("DECISION_ALLOWED", "subset allowed", ",".join(decisions_set), all(d in ALLOWED for d in decisions_set), "Only allowed decisions.")
    add("NO_PATCH_ALLOWED", "false", ",".join(sorted(set(prop(r, "def_patch_allowed_now") for r in decisions))), all(prop(r, "def_patch_allowed_now") == "false" for r in decisions), "No patch allowed.")
    add("NO_APPLY", "false", ",".join(sorted(set(prop(r, "def_apply_enabled") for r in decisions))), all(prop(r, "def_apply_enabled") == "false" for r in decisions), "No apply.")
    add("NO_SOURCE_MUTATION", "false", ",".join(sorted(set(prop(r, "def_source_mutation") for r in decisions))), all(prop(r, "def_source_mutation") == "false" for r in decisions), "No source mutation.")
    add("NO_DB_WRITE", "false", ",".join(sorted(set(prop(r, "def_db_write") for r in decisions))), all(prop(r, "def_db_write") == "false" for r in decisions), "No DB write.")
    add("NO_ACTION_POLICY_PRESENT", ">=9", len(no_action), len(no_action) >= 9, "No-action policy matrix.")

    return rows


def build_readiness(validation: List[Dict[str, Any]], e_ready: Dict[str, str], decisions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    fail = sum(1 for r in validation if prop(r, "def_status") != "PASS")
    approved = sum(1 for r in decisions if prop(r, "def_intake_decision") == "APPROVE_LATER")
    pending = sum(1 for r in decisions if prop(r, "def_intake_decision") == "PENDING")
    hold = sum(1 for r in decisions if prop(r, "def_intake_decision") == "HOLD")
    reject = sum(1 for r in decisions if prop(r, "def_intake_decision") == "REJECT")
    more = sum(1 for r in decisions if prop(r, "def_intake_decision") == "REQUEST_MORE_EVIDENCE")

    if fail == 0 and approved == 9:
        gate = "OPERATOR_DECISION_INTAKE_READY_ALL_APPROVED_REVIEW_ONLY"
        next_phase = "v0116G pre-apply backup package only"
    elif fail == 0:
        gate = "OPERATOR_DECISION_INTAKE_READY_PENDING_OR_PARTIAL_REVIEW_ONLY"
        next_phase = "v0116F2 approval gap review only"
    else:
        gate = "BLOCKED_BY_v0116F_DECISION_INTAKE_VALIDATION_FAIL"
        next_phase = "blocked"

    return [{
        "def_gate_status": gate,
        "def_allow_next": "true" if fail == 0 else "false",
        "def_reason": "v0116F ingested operator decisions. No patch, no apply.",
        "def_input_rows": prop(e_ready, "def_input_rows", "448"),
        "def_green_ledger_rows": prop(e_ready, "def_green_ledger_rows", "294"),
        "def_red_evidence_rows": prop(e_ready, "def_red_evidence_rows", "63"),
        "def_yellow_confirmation_rows": prop(e_ready, "def_yellow_confirmation_rows", "91"),
        "def_decision_rows": "9",
        "def_approve_later": str(approved),
        "def_pending": str(pending),
        "def_hold": str(hold),
        "def_reject": str(reject),
        "def_request_more_evidence": str(more),
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
        elif "PENDING" in joined or "HOLD" in joined or "REQUEST_MORE" in joined or "GAP" in joined:
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
        ("DecisionRows", prop(readiness, "def_decision_rows")),
        ("Approved", prop(readiness, "def_approve_later")),
        ("Pending", prop(readiness, "def_pending")),
        ("Hold", prop(readiness, "def_hold")),
        ("Reject", prop(readiness, "def_reject")),
        ("Fail", prop(readiness, "def_validation_fail")),
        ("Next", prop(readiness, "def_next_allowed_phase"))
    ]:
        cards += f"<div class='card'><div class='k'>{h(k)}</div><div class='v'>{h(v)}</div></div>"

    doc = f"""<!doctype html>
<html lang="zh-Hant">
<head><meta charset="utf-8"/><title>VIA v0116F Operator Decision Intake</title>{style}</head>
<body><div class="wrap">
<h1>def VIA v0116F · Operator Decision Intake Only</h1>
<div class="sub">3 Subsystems × 3 Flows · Decision Intake · No Patch · No Apply</div>
<div class="cards">{cards}</div>

<div class="sec"><h2>Readiness Gate</h2>{render_table(payload["readiness"], ["def_gate_status","def_allow_next","def_reason","def_input_rows","def_decision_rows","def_approve_later","def_pending","def_hold","def_reject","def_request_more_evidence","def_validation_fail","def_patch_allowed_now","def_original_dashboard_writeback","def_source_mutation","def_apply_enabled","def_db_write","def_next_allowed_phase"])}</div>
<div class="sec"><h2>Validation Matrix</h2>{render_table(payload["validation"], ["def_validation","def_expected","def_actual","def_status","def_message"])}</div>
<div class="sec"><h2>Decision Intake Matrix</h2>{render_table(payload["decisions"], ["def_decision_id","def_subsystem","def_flow_name","def_previous_decision","def_intake_decision","def_decision_note","def_operator","def_decision_timestamp","def_patch_allowed_now","def_apply_enabled"])}</div>
<div class="sec"><h2>Subsystem Sync Status</h2>{render_table(payload["sync"], ["def_subsystem","def_total_flows","def_approve_later","def_pending","def_hold","def_reject","def_request_more_evidence","def_sync_status","def_apply_enabled"])}</div>
<div class="sec"><h2>Approval Gap Matrix</h2>{render_table(payload["gap"], ["def_gap_id","def_subsystem","def_flow_name","def_decision","def_gap","def_next_required_action","def_blocks_future_apply","def_apply_enabled"])}</div>
<div class="sec"><h2>No-Action Matrix</h2>{render_table(payload["no_action"], ["def_policy_id","def_policy_name","def_control","def_required_value","def_status","def_message"])}</div>
</div></body></html>"""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(doc, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-run", required=True)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--operator", required=True)
    parser.add_argument("--decision", required=True)
    parser.add_argument("--note", required=True)
    args = parser.parse_args()

    source_run = Path(args.source_run)
    run_dir = Path(args.run_dir)
    output = run_dir / "output"
    report = run_dir / "report"
    decision_dir = run_dir / "_operator_decision_intake"

    output.mkdir(parents=True, exist_ok=True)
    report.mkdir(parents=True, exist_ok=True)
    decision_dir.mkdir(parents=True, exist_ok=True)

    package_dir = source_run / "_operator_approval_package"
    e_ready = first(read_csv(source_run / "output" / "VIA_v0116E_ReadinessGate.csv"))
    e_manifest = read_json(source_run / "output" / "VIA_v0116E_OperatorApprovalPackage_Manifest.json")
    template = read_csv(package_dir / "VIA_v0116E_OperatorDecisionTemplate.csv")

    decisions = build_decision_intake(template, args.operator, args.decision, args.note)
    sync = build_sync_status(decisions)
    gap = build_gap_matrix(decisions)
    no_action = build_no_action_matrix()
    validation = build_validation(e_ready, decisions, sync, gap, no_action)
    readiness = build_readiness(validation, e_ready, decisions)

    write_csv(decision_dir / "VIA_v0116F_OperatorDecisionIntakeMatrix.csv", decisions)
    write_csv(decision_dir / "VIA_v0116F_SubsystemSyncStatusMatrix.csv", sync)
    write_csv(decision_dir / "VIA_v0116F_ApprovalGapMatrix.csv", gap)
    write_csv(decision_dir / "VIA_v0116F_NoActionMatrix.csv", no_action)
    write_csv(decision_dir / "VIA_v0116F_ValidationMatrix.csv", validation)
    write_csv(output / "VIA_v0116F_ReadinessGate.csv", readiness)

    write_json(decision_dir / "VIA_v0116F_OperatorDecisionIntakeMatrix.json", decisions)
    write_json(decision_dir / "VIA_v0116F_SubsystemSyncStatusMatrix.json", sync)
    write_json(decision_dir / "VIA_v0116F_ApprovalGapMatrix.json", gap)
    write_json(decision_dir / "VIA_v0116F_NoActionMatrix.json", no_action)
    write_json(decision_dir / "VIA_v0116F_ValidationMatrix.json", validation)
    write_json(output / "VIA_v0116F_ReadinessGate.json", readiness)

    report_path = report / "VIA_v0116F_OperatorDecisionIntake_Report.html"
    payload = {
        "readiness": readiness,
        "validation": validation,
        "decisions": decisions,
        "sync": sync,
        "gap": gap,
        "no_action": no_action
    }
    write_report(report_path, payload)

    final_manifest = {
        "schema_version": "VIA_v0116F_OperatorDecisionIntakeOnly",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "gate": readiness[0]["def_gate_status"],
        "source_run": str(source_run),
        "run_dir": str(run_dir),
        "v0116e_manifest": e_manifest,
        "operator": args.operator,
        "decision_mode": args.decision.upper().strip(),
        "report": str(report_path),
        "outputs": {
            "readiness": str(output / "VIA_v0116F_ReadinessGate.csv"),
            "decision_intake": str(decision_dir / "VIA_v0116F_OperatorDecisionIntakeMatrix.csv"),
            "sync_status": str(decision_dir / "VIA_v0116F_SubsystemSyncStatusMatrix.csv"),
            "approval_gap": str(decision_dir / "VIA_v0116F_ApprovalGapMatrix.csv"),
            "validation": str(decision_dir / "VIA_v0116F_ValidationMatrix.csv")
        },
        "policy": {
            "decision_intake_only": True,
            "patch_allowed_now": False,
            "original_dashboard_writeback": False,
            "source_mutation": False,
            "canonical_merge": False,
            "db_write": False,
            "apply_enabled": False
        }
    }
    write_json(output / "VIA_v0116F_OperatorDecisionIntake_Manifest.json", final_manifest)

    print("")
    print("=" * 80)
    print("def VIA v0116F Operator Decision Intake COMPLETE")
    print("=" * 80)
    print(f"Gate       : {readiness[0]['def_gate_status']}")
    print(f"Decision   : {args.decision.upper().strip()}")
    print(f"Approved   : {readiness[0]['def_approve_later']}")
    print(f"Pending    : {readiness[0]['def_pending']}")
    print(f"Hold       : {readiness[0]['def_hold']}")
    print(f"Reject     : {readiness[0]['def_reject']}")
    print(f"Fail       : {readiness[0]['def_validation_fail']}")
    print(f"Report     : {report_path}")
    print(f"DecisionDir: {decision_dir}")
    print("[SAFE] Decision intake only. No patch. No apply. No DB write.")


if __name__ == "__main__":
    main()
