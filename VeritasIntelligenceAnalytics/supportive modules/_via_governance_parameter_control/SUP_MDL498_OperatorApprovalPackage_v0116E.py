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


def build_three_subsystem_flow_sync() -> List[Dict[str, Any]]:
    subsystems = [
        ("VDF_VeritasDataForge", "data / registry / market-data governance"),
        ("VAP_VisualizationAnalytics", "dashboard / UI / visualization governance"),
        ("VRN_VeritasReportNova", "report / evidence / extraction governance"),
    ]

    flows = [
        ("FLOW_A", "DASHBOARD_BINDING_APPROVAL", "Approve dashboard route/card binding logic only."),
        ("FLOW_B", "RISK_GUARD_APPROVAL", "Approve red/yellow/green guard behavior and no dangerous UI."),
        ("FLOW_C", "ROLLBACK_AUDIT_APPROVAL", "Approve backup/hash/rollback/audit seal requirements."),
    ]

    rows: List[Dict[str, Any]] = []
    n = 0

    for subsystem, scope in subsystems:
        for flow_id, flow_name, purpose in flows:
            n += 1
            rows.append({
                "def_sync_id": f"V0116E-SYNC-{n:03d}",
                "def_subsystem": subsystem,
                "def_subsystem_scope": scope,
                "def_flow_id": flow_id,
                "def_flow_name": flow_name,
                "def_flow_purpose": purpose,
                "def_sync_mode": "INDEPENDENT_FLOW_SYNCHRONIZED_REVIEW",
                "def_operator_decision": "PENDING",
                "def_apply_enabled": "false",
                "def_patch_allowed": "false",
                "def_source_mutation": "false",
                "def_db_write": "false",
                "def_blocker_if_not_approved": "block_future_apply_branch"
            })

    return rows


def build_operator_approval_board(patch_plan: List[Dict[str, str]], guards: List[Dict[str, str]], rollback: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    n = 0

    for p in patch_plan:
        n += 1
        rows.append({
            "def_approval_id": f"V0116E-APPROVAL-PATCH-{n:03d}",
            "def_approval_group": "PATCH_PLAN_CARD_APPROVAL",
            "def_subject": prop(p, "def_title"),
            "def_route": prop(p, "def_source_route"),
            "def_ryg": prop(p, "def_ryg"),
            "def_expected_rows": prop(p, "def_expected_rows"),
            "def_required_operator_action": "review_and_optionally_approve_later",
            "def_default_decision": "PENDING",
            "def_auto_approve": "false",
            "def_patch_allowed_now": "false",
            "def_apply_enabled": "false"
        })

    for g in guards:
        n += 1
        rows.append({
            "def_approval_id": f"V0116E-APPROVAL-GUARD-{n:03d}",
            "def_approval_group": "RISK_GUARD_APPROVAL",
            "def_subject": prop(g, "def_guard_name"),
            "def_route": prop(g, "def_control"),
            "def_ryg": "RED" if "RED" in prop(g, "def_guard_name") else "GREEN",
            "def_expected_rows": "1",
            "def_required_operator_action": "confirm_guard_must_remain_enforced",
            "def_default_decision": "PENDING",
            "def_auto_approve": "false",
            "def_patch_allowed_now": "false",
            "def_apply_enabled": "false"
        })

    for r in rollback:
        n += 1
        rows.append({
            "def_approval_id": f"V0116E-APPROVAL-ROLLBACK-{n:03d}",
            "def_approval_group": "ROLLBACK_AUDIT_APPROVAL",
            "def_subject": prop(r, "def_step"),
            "def_route": prop(r, "def_expected_path_pattern"),
            "def_ryg": "YELLOW",
            "def_expected_rows": "1",
            "def_required_operator_action": "confirm_future_rollback_requirement",
            "def_default_decision": "PENDING",
            "def_auto_approve": "false",
            "def_patch_allowed_now": "false",
            "def_apply_enabled": "false"
        })

    return rows


def build_subsystem_route_map(sync_rows: List[Dict[str, Any]], patch_plan: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    route_summary = {
        "VDF_VeritasDataForge": "Governance Parameter Bridge; Validation Matrix; Export Contract",
        "VAP_VisualizationAnalytics": "Executive Gate; Subsystem Matrix; Dashboard UI route guards",
        "VRN_VeritasReportNova": "RED Evidence Pack; YELLOW Confirmation; GREEN Clearance Ledger",
    }

    for s in sorted(set(prop(r, "def_subsystem") for r in sync_rows)):
        rows.append({
            "def_subsystem": s,
            "def_related_dashboard_routes": route_summary.get(s, ""),
            "def_sync_flow_count": str(sum(1 for r in sync_rows if prop(r, "def_subsystem") == s)),
            "def_patch_plan_total": str(len(patch_plan)),
            "def_patch_mode": "plan_only",
            "def_operator_decision": "PENDING",
            "def_apply_enabled": "false"
        })

    return rows


def build_decision_template(sync_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []

    for r in sync_rows:
        rows.append({
            "def_decision_id": "DECISION-" + prop(r, "def_sync_id"),
            "def_subsystem": prop(r, "def_subsystem"),
            "def_flow_name": prop(r, "def_flow_name"),
            "def_allowed_decisions": "APPROVE_LATER;REJECT;HOLD;REQUEST_MORE_EVIDENCE",
            "def_current_decision": "PENDING",
            "def_decision_note": "",
            "def_operator": "",
            "def_decision_timestamp": "",
            "def_apply_enabled": "false",
            "def_source_mutation": "false"
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
        ("NO_AUTO_APPROVE", "auto_approve", "false"),
        ("REQUIRES_OPERATOR_APPROVAL", "operator_approval", "true"),
    ]

    rows = []
    for i, (name, control, value) in enumerate(rules, 1):
        rows.append({
            "def_policy_id": f"V0116E-NOACT-{i:03d}",
            "def_policy_name": name,
            "def_control": control,
            "def_required_value": value,
            "def_status": "PASS",
            "def_message": "Operator approval package only. No writeback."
        })

    return rows


def build_validation(
    d_ready: Dict[str, str],
    patch_plan: List[Dict[str, str]],
    ops: List[Dict[str, str]],
    guards: List[Dict[str, str]],
    rollback: List[Dict[str, str]],
    sync_rows: List[Dict[str, Any]],
    approval_board: List[Dict[str, Any]],
    decision_template: List[Dict[str, Any]],
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

    add("V0116D_GATE_READY", "DASHBOARD_INTEGRATION_PATCH_PLAN_READY_REVIEW_ONLY", prop(d_ready, "def_gate_status"), prop(d_ready, "def_gate_status") == "DASHBOARD_INTEGRATION_PATCH_PLAN_READY_REVIEW_ONLY", "v0116D must be ready.")
    add("INPUT_448", "448", prop(d_ready, "def_input_rows"), prop(d_ready, "def_input_rows") == "448", "Input continuity.")
    add("PATCH_PLAN_ROWS_8", 8, len(patch_plan), len(patch_plan) == 8, "Patch plan rows.")
    add("PATCH_OPS_GE_9", ">=9", len(ops), len(ops) >= 9, "Patch ops rows.")
    add("GUARDS_GE_10", ">=10", len(guards), len(guards) >= 10, "Guard rows.")
    add("ROLLBACK_ROWS_4", 4, len(rollback), len(rollback) == 4, "Rollback rows.")
    add("SYNC_ROWS_9", 9, len(sync_rows), len(sync_rows) == 9, "3 subsystems x 3 flows.")
    add("DECISION_ROWS_9", 9, len(decision_template), len(decision_template) == 9, "One decision row per subsystem-flow.")
    add("APPROVAL_BOARD_PRESENT", ">=23", len(approval_board), len(approval_board) >= 23, "Patch + guard + rollback approval rows.")
    add("NO_AUTO_APPROVE", "false", ",".join(sorted(set(prop(r, "def_auto_approve") for r in approval_board))), all(prop(r, "def_auto_approve") == "false" for r in approval_board), "No auto approval.")
    add("ALL_DECISIONS_PENDING", "PENDING", ",".join(sorted(set(prop(r, "def_current_decision") for r in decision_template))), all(prop(r, "def_current_decision") == "PENDING" for r in decision_template), "All operator decisions pending.")
    add("NO_PATCH_ALLOWED", "false", ",".join(sorted(set(prop(r, "def_patch_allowed") for r in sync_rows))), all(prop(r, "def_patch_allowed") == "false" for r in sync_rows), "No patch allowed.")
    add("NO_APPLY", "false", ",".join(sorted(set(prop(r, "def_apply_enabled") for r in sync_rows))), all(prop(r, "def_apply_enabled") == "false" for r in sync_rows), "No apply.")
    add("NO_SOURCE_MUTATION", "false", ",".join(sorted(set(prop(r, "def_source_mutation") for r in sync_rows))), all(prop(r, "def_source_mutation") == "false" for r in sync_rows), "No source mutation.")
    add("NO_DB_WRITE", "false", ",".join(sorted(set(prop(r, "def_db_write") for r in sync_rows))), all(prop(r, "def_db_write") == "false" for r in sync_rows), "No DB write.")
    add("NO_ACTION_POLICY_PRESENT", ">=10", len(no_action), len(no_action) >= 10, "No-action policy matrix.")

    return rows


def build_readiness(validation: List[Dict[str, Any]], d_ready: Dict[str, str]) -> List[Dict[str, Any]]:
    fail = sum(1 for r in validation if prop(r, "def_status") != "PASS")

    return [{
        "def_gate_status": "OPERATOR_APPROVAL_PACKAGE_READY_REVIEW_ONLY" if fail == 0 else "BLOCKED_BY_v0116E_APPROVAL_PACKAGE_VALIDATION_FAIL",
        "def_allow_next": "true" if fail == 0 else "false",
        "def_reason": "v0116E generated operator approval package for 3 subsystems x 3 independent synchronized flows. No patch, no apply.",
        "def_input_rows": prop(d_ready, "def_input_rows", "448"),
        "def_green_ledger_rows": prop(d_ready, "def_green_ledger_rows", "294"),
        "def_red_evidence_rows": prop(d_ready, "def_red_evidence_rows", "63"),
        "def_yellow_confirmation_rows": prop(d_ready, "def_yellow_confirmation_rows", "91"),
        "def_patch_plan_rows": prop(d_ready, "def_patch_plan_rows", "8"),
        "def_subsystems": "3",
        "def_flows_per_subsystem": "3",
        "def_sync_rows": "9",
        "def_validation_fail": str(fail),
        "def_operator_decision": "PENDING",
        "def_patch_allowed_now": "false",
        "def_original_dashboard_writeback": "false",
        "def_source_mutation": "false",
        "def_canonical_merge": "false",
        "def_apply_enabled": "false",
        "def_db_write": "false",
        "def_next_allowed_phase": "v0116F operator decision intake only"
    }]


def render_table(rows: List[Dict[str, Any]], cols: List[str]) -> str:
    out = ["<table><thead><tr>"]
    for c in cols:
        out.append(f"<th>{h(c)}</th>")
    out.append("</tr></thead><tbody>")
    for r in rows:
        joined = " ".join(str(v) for v in r.values()).upper()
        cls = "risk-green"
        if "FAIL" in joined or "RED" in joined or "BLOCK" in joined:
            cls = "risk-red"
        elif "YELLOW" in joined or "PENDING" in joined:
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
        ("Input", prop(readiness, "def_input_rows")),
        ("Green", prop(readiness, "def_green_ledger_rows")),
        ("Red", prop(readiness, "def_red_evidence_rows")),
        ("Yellow", prop(readiness, "def_yellow_confirmation_rows")),
        ("SyncRows", prop(readiness, "def_sync_rows")),
        ("Fail", prop(readiness, "def_validation_fail")),
        ("Next", "v0116F")
    ]:
        cards += f"<div class='card'><div class='k'>{h(k)}</div><div class='v'>{h(v)}</div></div>"

    doc = f"""<!doctype html>
<html lang="zh-Hant">
<head><meta charset="utf-8"/><title>VIA v0116E Operator Approval Package</title>{style}</head>
<body><div class="wrap">
<h1>def VIA v0116E · Operator Approval Package Only</h1>
<div class="sub">3 Subsystems × 3 Independent Flows · Synchronized Review · No Patch · No Apply</div>
<div class="cards">{cards}</div>

<div class="sec"><h2>Readiness Gate</h2>{render_table(payload["readiness"], ["def_gate_status","def_allow_next","def_reason","def_input_rows","def_green_ledger_rows","def_red_evidence_rows","def_yellow_confirmation_rows","def_patch_plan_rows","def_subsystems","def_flows_per_subsystem","def_sync_rows","def_validation_fail","def_operator_decision","def_patch_allowed_now","def_original_dashboard_writeback","def_source_mutation","def_apply_enabled","def_db_write","def_next_allowed_phase"])}</div>
<div class="sec"><h2>Validation Matrix</h2>{render_table(payload["validation"], ["def_validation","def_expected","def_actual","def_status","def_message"])}</div>
<div class="sec"><h2>3 Subsystems × 3 Independent Flow Sync Matrix</h2>{render_table(payload["sync"], ["def_sync_id","def_subsystem","def_subsystem_scope","def_flow_id","def_flow_name","def_flow_purpose","def_sync_mode","def_operator_decision","def_patch_allowed","def_apply_enabled","def_blocker_if_not_approved"])}</div>
<div class="sec"><h2>Subsystem Route Map</h2>{render_table(payload["subsystem_map"], ["def_subsystem","def_related_dashboard_routes","def_sync_flow_count","def_patch_plan_total","def_patch_mode","def_operator_decision","def_apply_enabled"])}</div>
<div class="sec"><h2>Operator Approval Board</h2>{render_table(payload["approval"], ["def_approval_id","def_approval_group","def_subject","def_route","def_ryg","def_expected_rows","def_required_operator_action","def_default_decision","def_auto_approve","def_patch_allowed_now","def_apply_enabled"])}</div>
<div class="sec"><h2>Operator Decision Template</h2>{render_table(payload["decision"], ["def_decision_id","def_subsystem","def_flow_name","def_allowed_decisions","def_current_decision","def_decision_note","def_operator","def_decision_timestamp","def_apply_enabled"])}</div>
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
    package = run_dir / "_operator_approval_package"

    output.mkdir(parents=True, exist_ok=True)
    report.mkdir(parents=True, exist_ok=True)
    package.mkdir(parents=True, exist_ok=True)

    d_ready = first(read_csv(source_run / "output" / "VIA_v0116D_ReadinessGate.csv"))
    d_manifest = read_json(source_run / "output" / "VIA_v0116D_DashboardIntegrationPatchPlan_Manifest.json")
    pdir = source_run / "_dashboard_integration_patch_plan"

    patch_plan = read_csv(pdir / "VIA_v0116D_DashboardIntegrationPatchPlan.csv")
    ops = read_csv(pdir / "VIA_v0116D_PatchOperationMatrix.csv")
    guards = read_csv(pdir / "VIA_v0116D_RiskGuardMatrix.csv")
    rollback = read_csv(pdir / "VIA_v0116D_RollbackPlanMatrix.csv")

    sync_rows = build_three_subsystem_flow_sync()
    approval_board = build_operator_approval_board(patch_plan, guards, rollback)
    subsystem_map = build_subsystem_route_map(sync_rows, patch_plan)
    decision_template = build_decision_template(sync_rows)
    no_action = build_no_action_matrix()
    validation = build_validation(
        d_ready, patch_plan, ops, guards, rollback,
        sync_rows, approval_board, decision_template, no_action
    )
    readiness = build_readiness(validation, d_ready)

    write_csv(package / "VIA_v0116E_ThreeSubsystemFlowSyncMatrix.csv", sync_rows)
    write_csv(package / "VIA_v0116E_SubsystemRouteMap.csv", subsystem_map)
    write_csv(package / "VIA_v0116E_OperatorApprovalBoard.csv", approval_board)
    write_csv(package / "VIA_v0116E_OperatorDecisionTemplate.csv", decision_template)
    write_csv(package / "VIA_v0116E_NoActionMatrix.csv", no_action)
    write_csv(package / "VIA_v0116E_ValidationMatrix.csv", validation)
    write_csv(output / "VIA_v0116E_ReadinessGate.csv", readiness)

    write_json(package / "VIA_v0116E_ThreeSubsystemFlowSyncMatrix.json", sync_rows)
    write_json(package / "VIA_v0116E_SubsystemRouteMap.json", subsystem_map)
    write_json(package / "VIA_v0116E_OperatorApprovalBoard.json", approval_board)
    write_json(package / "VIA_v0116E_OperatorDecisionTemplate.json", decision_template)
    write_json(package / "VIA_v0116E_NoActionMatrix.json", no_action)
    write_json(package / "VIA_v0116E_ValidationMatrix.json", validation)
    write_json(output / "VIA_v0116E_ReadinessGate.json", readiness)

    report_path = report / "VIA_v0116E_OperatorApprovalPackage_Report.html"
    payload = {
        "readiness": readiness,
        "validation": validation,
        "sync": sync_rows,
        "subsystem_map": subsystem_map,
        "approval": approval_board,
        "decision": decision_template,
        "no_action": no_action
    }
    write_report(report_path, payload)

    final_manifest = {
        "schema_version": "VIA_v0116E_OperatorApprovalPackageOnly",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "gate": readiness[0]["def_gate_status"],
        "source_run": str(source_run),
        "run_dir": str(run_dir),
        "v0116d_manifest": d_manifest,
        "report": str(report_path),
        "outputs": {
            "readiness": str(output / "VIA_v0116E_ReadinessGate.csv"),
            "three_subsystem_flow_sync": str(package / "VIA_v0116E_ThreeSubsystemFlowSyncMatrix.csv"),
            "subsystem_route_map": str(package / "VIA_v0116E_SubsystemRouteMap.csv"),
            "operator_approval_board": str(package / "VIA_v0116E_OperatorApprovalBoard.csv"),
            "operator_decision_template": str(package / "VIA_v0116E_OperatorDecisionTemplate.csv"),
            "validation": str(package / "VIA_v0116E_ValidationMatrix.csv")
        },
        "policy": {
            "operator_approval_package_only": True,
            "three_subsystems": ["VDF_VeritasDataForge", "VAP_VisualizationAnalytics", "VRN_VeritasReportNova"],
            "flows_per_subsystem": 3,
            "patch_allowed_now": False,
            "auto_approve": False,
            "original_dashboard_writeback": False,
            "source_mutation": False,
            "canonical_merge": False,
            "db_write": False,
            "apply_enabled": False
        }
    }
    write_json(output / "VIA_v0116E_OperatorApprovalPackage_Manifest.json", final_manifest)

    print("")
    print("=" * 80)
    print("def VIA v0116E Operator Approval Package COMPLETE")
    print("=" * 80)
    print(f"Gate        : {readiness[0]['def_gate_status']}")
    print(f"Input Rows  : {readiness[0]['def_input_rows']}")
    print(f"Green       : {readiness[0]['def_green_ledger_rows']}")
    print(f"Red         : {readiness[0]['def_red_evidence_rows']}")
    print(f"Yellow      : {readiness[0]['def_yellow_confirmation_rows']}")
    print(f"PatchPlan   : {readiness[0]['def_patch_plan_rows']}")
    print(f"Subsystems  : {readiness[0]['def_subsystems']}")
    print(f"Flows/Sub   : {readiness[0]['def_flows_per_subsystem']}")
    print(f"SyncRows    : {readiness[0]['def_sync_rows']}")
    print(f"Fail        : {readiness[0]['def_validation_fail']}")
    print(f"Report      : {report_path}")
    print(f"PackageDir  : {package}")
    print("[SAFE] Operator approval package only. No patch. No auto approval. No apply. No DB write.")


if __name__ == "__main__":
    main()
