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


def safe_int(value: Any) -> int:
    try:
        return int(str(value))
    except Exception:
        return 0


def file_status(path: Path) -> str:
    return "FOUND" if path.exists() else "MISSING"


def build_final_policy_matrix() -> List[Dict[str, Any]]:
    policies = [
        ("FINAL-POLICY-001", "Local Only", "external_call", "false", "No external call in final seal."),
        ("FINAL-POLICY-002", "No Source Read", "source_read", "false", "Final seal reads generated matrices only."),
        ("FINAL-POLICY-003", "No Project Rescan", "project_rescan", "false", "No 80872-file project scan in F10."),
        ("FINAL-POLICY-004", "No Source Mutation", "source_mutation", "false", "No source writeback."),
        ("FINAL-POLICY-005", "No Canonical Merge", "canonical_merge", "false", "No canonical merge or SSOT merge."),
        ("FINAL-POLICY-006", "No DB Write", "db_write", "false", "No DB write."),
        ("FINAL-POLICY-007", "No Apply", "apply_enabled", "false", "No apply."),
        ("FINAL-POLICY-008", "No Delete", "delete", "false", "No delete."),
        ("FINAL-POLICY-009", "No Stop-Process", "stop_process", "false", "No Stop-Process."),
        ("FINAL-POLICY-010", "No Read-Host", "read_host", "false", "No blocking interactive prompt."),
        ("FINAL-POLICY-011", "No Forced Close", "forced_close", "false", "PowerShell remains open."),
        ("FINAL-POLICY-012", "Secret Safety", "plaintext_secret_export", "false", "No plaintext secret export to UI/CSV/JSON/HTML."),
    ]

    return [
        {
            "def_policy_id": pid,
            "def_policy_name": name,
            "def_control": key,
            "def_required_value": value,
            "def_status": "PASS",
            "def_message": msg,
            "def_apply_enabled": "false",
            "def_source_mutation": "false",
            "def_db_write": "false"
        }
        for pid, name, key, value, msg in policies
    ]


def build_final_dashboard_contract(readiness: Dict[str, str], bindings: List[Dict[str, str]], guards: List[Dict[str, str]], dashmap: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    return [
        {
            "def_contract_id": "FINAL-DASH-001",
            "def_contract_name": "Dashboard Binding Preview",
            "def_status": "SEALED_READ_ONLY",
            "def_gate_source": prop(readiness, "def_gate_status"),
            "def_binding_cards": str(len(bindings)),
            "def_action_guards": str(len(guards)),
            "def_dashboard_sections": str(len(dashmap)),
            "def_allowed": "view;filter;sort;export_csv;export_json;open_static_html;copy_path_text_only",
            "def_blocked": "source_read;rescan;source_mutation;canonical_merge;db_write;apply;external_call;delete;stop_process;auto_fix;batch_fix;full_file_read;parameter_writeback",
            "def_writeback": "false"
        },
        {
            "def_contract_id": "FINAL-DASH-002",
            "def_contract_name": "RED Evidence Pack Lock",
            "def_status": "SEALED_LOCKED",
            "def_gate_source": "F9 RED binding",
            "def_binding_cards": "1",
            "def_action_guards": str(sum(1 for r in guards if prop(r, "def_ryg") == "RED")),
            "def_dashboard_sections": "Risk Control",
            "def_allowed": "view;filter;export",
            "def_blocked": "auto_fix;batch_fix;apply;source_mutation",
            "def_writeback": "false"
        },
        {
            "def_contract_id": "FINAL-DASH-003",
            "def_contract_name": "YELLOW Confirmation Preview",
            "def_status": "SEALED_CONFIRMATION_ONLY",
            "def_gate_source": "F9 YELLOW binding",
            "def_binding_cards": "1",
            "def_action_guards": str(sum(1 for r in guards if prop(r, "def_ryg") == "YELLOW")),
            "def_dashboard_sections": "Risk Control",
            "def_allowed": "view;filter;confirmation_preview",
            "def_blocked": "full_file_read;apply;source_mutation",
            "def_writeback": "false"
        },
        {
            "def_contract_id": "FINAL-DASH-004",
            "def_contract_name": "GREEN Clearance Candidate",
            "def_status": "SEALED_CANDIDATE_ONLY",
            "def_gate_source": "F9 GREEN binding",
            "def_binding_cards": str(sum(1 for r in bindings if prop(r, "def_ryg") == "GREEN")),
            "def_action_guards": str(sum(1 for r in guards if prop(r, "def_ryg") == "GREEN")),
            "def_dashboard_sections": "Executive;Clearance;Subsystems",
            "def_allowed": "view;filter;ledger_candidate_preview",
            "def_blocked": "auto_clear;db_write;canonical_merge",
            "def_writeback": "false"
        }
    ]


def build_final_artifact_index(source_run: Path, run_dir: Path) -> List[Dict[str, Any]]:
    bdir = source_run / "_dashboard_binding_preview"
    odir = source_run / "output"
    rdir = source_run / "report"

    candidates = [
        ("F9_READINESS", odir / "VIA_v0115F9_ReadinessGate.csv"),
        ("F9_MANIFEST", odir / "VIA_v0115F9_DashboardBindingPreview_Manifest.json"),
        ("F9_HTML", rdir / "VIA_v0115F9_DashboardBindingPreview_OnePage.html"),
        ("F9_BINDING_CARDS", bdir / "VIA_v0115F9_DashboardBindingCards.csv"),
        ("F9_ACTION_GUARD", bdir / "VIA_v0115F9_ActionGuardMatrix.csv"),
        ("F9_DASHBOARD_MAP", bdir / "VIA_v0115F9_DashboardSectionMap.csv"),
        ("F9_QUANTITY_VALIDATION", bdir / "VIA_v0115F9_QuantityValidationMatrix.csv"),
        ("F9_CARRIED_F8_ROUTE", bdir / "VIA_v0115F9_CarriedF8_UIRouteContract.csv"),
        ("F9_CARRIED_F8_WIDGET", bdir / "VIA_v0115F9_CarriedF8_WidgetContract.csv"),
        ("F9_CARRIED_F8_PROCESS", bdir / "VIA_v0115F9_CarriedF8_ProcessMatrix.csv"),
        ("F9_CARRIED_F8_POLICY", bdir / "VIA_v0115F9_CarriedF8_RYGPolicyMatrix.csv"),
    ]

    rows = []
    for i, (name, path) in enumerate(candidates, 1):
        rows.append({
            "def_artifact_id": f"FINAL-ART-{i:03d}",
            "def_artifact_name": name,
            "def_path": str(path),
            "def_status": file_status(path),
            "def_source_read": "false",
            "def_source_mutation": "false",
            "def_apply_enabled": "false"
        })

    rows.append({
        "def_artifact_id": "FINAL-ART-999",
        "def_artifact_name": "F10_FINAL_RUN_DIR",
        "def_path": str(run_dir),
        "def_status": "CREATED",
        "def_source_read": "false",
        "def_source_mutation": "false",
        "def_apply_enabled": "false"
    })

    return rows


def build_final_continuity_matrix(readiness: Dict[str, str], quantity: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    qfail = prop(readiness, "def_quantity_validation_fail")
    return [
        {
            "def_phase": "F1-F3",
            "def_layer": "P0 Triage / Active Context / Decision Matrix",
            "def_status": "CARRIED_FORWARD",
            "def_evidence": "448 active P0 rows split into True/Boundary/Fieldname/FalsePositive/PathSize before F4.",
            "def_no_action_policy": "no source mutation; review-only"
        },
        {
            "def_phase": "F4",
            "def_layer": "Grouped Review / Clearance Package",
            "def_status": "CARRIED_FORWARD",
            "def_evidence": "Red=63 Yellow=91 Green=294 grouping preserved.",
            "def_no_action_policy": "no source read; no apply"
        },
        {
            "def_phase": "F5",
            "def_layer": "Package-Specific Precheck",
            "def_status": "CARRIED_FORWARD",
            "def_evidence": "Precheck validation fail=0; red/yellow/green counts preserved.",
            "def_no_action_policy": "no source read; no apply; no DB write"
        },
        {
            "def_phase": "F6",
            "def_layer": "Ledger / Evidence Candidate",
            "def_status": "CARRIED_FORWARD",
            "def_evidence": "Green ledger=294; Red evidence=63; Yellow confirmation=91.",
            "def_no_action_policy": "candidate-only"
        },
        {
            "def_phase": "F7",
            "def_layer": "Validation Only",
            "def_status": "CARRIED_FORWARD",
            "def_evidence": "Final validation rows=28; fail=0.",
            "def_no_action_policy": "validation-only"
        },
        {
            "def_phase": "F8",
            "def_layer": "Governance UI Contract Seal",
            "def_status": "CARRIED_FORWARD",
            "def_evidence": "Routes=8; Widgets=9; quantity validation fail=0.",
            "def_no_action_policy": "UI contract only"
        },
        {
            "def_phase": "F9",
            "def_layer": "Dashboard Binding Preview",
            "def_status": "SEALED",
            "def_evidence": f"Gate={prop(readiness,'def_gate_status')}; QuantityFail={qfail}; QuantityRows={len(quantity)}.",
            "def_no_action_policy": "dashboard preview only; no writeback"
        },
        {
            "def_phase": "F10",
            "def_layer": "Final Read-Only Seal",
            "def_status": "READY_TO_SEAL",
            "def_evidence": "Final seal generated from F9 outputs only.",
            "def_no_action_policy": "final audit seal only"
        }
    ]


def build_final_quantity_validation(readiness: Dict[str, str], bindings: List[Dict[str, str]], guards: List[Dict[str, str]], dashmap: List[Dict[str, str]], quantity_f9: List[Dict[str, str]], artifact_index: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []

    def add(name: str, expected: Any, actual: Any, ok: bool, msg: str) -> None:
        rows.append({
            "def_validation": name,
            "def_expected": expected,
            "def_actual": actual,
            "def_status": "PASS" if ok else "FAIL",
            "def_message": msg
        })

    add("F9_GATE_READY", "DASHBOARD_BINDING_PREVIEW_READY_REVIEW_ONLY", prop(readiness, "def_gate_status"), prop(readiness, "def_gate_status") == "DASHBOARD_BINDING_PREVIEW_READY_REVIEW_ONLY", "F9 gate must be ready.")
    add("INPUT_448", "448", prop(readiness, "def_input_rows"), prop(readiness, "def_input_rows") == "448", "Input continuity.")
    add("GREEN_294", "294", prop(readiness, "def_green_ledger_rows"), prop(readiness, "def_green_ledger_rows") == "294", "Green continuity.")
    add("RED_63", "63", prop(readiness, "def_red_evidence_rows"), prop(readiness, "def_red_evidence_rows") == "63", "Red continuity.")
    add("YELLOW_91", "91", prop(readiness, "def_yellow_confirmation_rows"), prop(readiness, "def_yellow_confirmation_rows") == "91", "Yellow continuity.")
    add("GOV_34", "34", prop(readiness, "def_governance_params"), prop(readiness, "def_governance_params") == "34", "Governance continuity.")
    add("ROUTES_8", "8", prop(readiness, "def_ui_routes"), prop(readiness, "def_ui_routes") == "8", "Routes continuity.")
    add("WIDGETS_9", "9", prop(readiness, "def_widgets"), prop(readiness, "def_widgets") == "9", "Widgets continuity.")
    add("BINDING_CARDS_8", "8", prop(readiness, "def_binding_cards"), prop(readiness, "def_binding_cards") == "8", "Binding continuity.")
    add("F9_QUANTITY_FAIL_0", "0", prop(readiness, "def_quantity_validation_fail"), prop(readiness, "def_quantity_validation_fail") == "0", "F9 quantity fail must be zero.")
    add("BINDING_ROWS_8", 8, len(bindings), len(bindings) == 8, "Binding rows.")
    add("DASHMAP_ROWS_4", 4, len(dashmap), len(dashmap) == 4, "Dashboard map rows.")
    add("GUARD_ROWS_GE_17", ">=17", len(guards), len(guards) >= 17, "Guard rows.")
    add("F9_QUANTITY_ROWS_GE_17", ">=17", len(quantity_f9), len(quantity_f9) >= 17, "F9 quantity validation rows.")
    add("ARTIFACTS_PRESENT", "all FOUND/CREATED", ",".join(sorted(set(prop(r, "def_status") for r in artifact_index))), all(prop(r, "def_status") in {"FOUND","CREATED"} for r in artifact_index), "All final artifact references must exist.")
    add("NO_SOURCE_READ", "false", prop(readiness, "def_source_read"), prop(readiness, "def_source_read") == "false", "No source read.")
    add("NO_RESCAN", "false", prop(readiness, "def_rescan"), prop(readiness, "def_rescan") == "false", "No rescan.")
    add("NO_APPLY", "false", prop(readiness, "def_apply_enabled"), prop(readiness, "def_apply_enabled") == "false", "No apply.")
    add("NO_MUTATION", "false", prop(readiness, "def_source_mutation"), prop(readiness, "def_source_mutation") == "false", "No source mutation.")
    add("NO_DB_WRITE", "false", prop(readiness, "def_db_write"), prop(readiness, "def_db_write") == "false", "No DB write.")

    return rows


def build_final_readiness(quantity: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    fail = sum(1 for r in quantity if prop(r, "def_status") != "PASS")
    return [{
        "def_gate_status": "FINAL_READ_ONLY_SEAL_READY_REVIEW_ONLY" if fail == 0 else "BLOCKED_BY_F10_FINAL_SEAL_VALIDATION_FAIL",
        "def_allow_next": "true" if fail == 0 else "false",
        "def_reason": "F10 final read-only audit seal generated from F9 dashboard binding preview. No source read, no mutation, no apply.",
        "def_input_rows": "448",
        "def_green_ledger_rows": "294",
        "def_red_evidence_rows": "63",
        "def_yellow_confirmation_rows": "91",
        "def_governance_params": "34",
        "def_ui_routes": "8",
        "def_widgets": "9",
        "def_binding_cards": "8",
        "def_final_validation_fail": str(fail),
        "def_source_read": "false",
        "def_project_rescan": "false",
        "def_execution_enabled": "false",
        "def_apply_enabled": "false",
        "def_source_mutation": "false",
        "def_canonical_merge": "false",
        "def_db_write": "false",
        "def_final_status": "VIA_v0115F10_FINAL_READ_ONLY_AUDIT_SEALED" if fail == 0 else "REVIEW_REQUIRED"
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
            if "FAIL" in joined or "RED" in joined or "BLOCKED" in joined:
                cls = " class='risk-red'"
            elif "YELLOW" in joined or "REVIEW" in joined:
                cls = " class='risk-yellow'"
            elif "PASS" in joined or "GREEN" in joined or "SEALED" in joined:
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

    cards = ""
    for k, v in [
        ("Gate", readiness["def_gate_status"]),
        ("Input", readiness["def_input_rows"]),
        ("Green", readiness["def_green_ledger_rows"]),
        ("Red", readiness["def_red_evidence_rows"]),
        ("Yellow", readiness["def_yellow_confirmation_rows"]),
        ("Routes", readiness["def_ui_routes"]),
        ("Fail", readiness["def_final_validation_fail"]),
        ("Status", readiness["def_final_status"])
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
.footer{margin:12px 0 4px;color:var(--muted);font-size:8px}.path{font-family:Consolas,monospace;color:#355b63}
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

    doc = f"""<!doctype html>
<html lang="zh-Hant">
<head><meta charset="utf-8"/><title>VIA v0115F10 Final Read-Only Seal</title><style>{style}</style><script>{js}</script></head>
<body><div class="wrap">
  <div class="header">
    <div>
      <h1>def VIA v0115F10 · Final Read-Only Seal Only</h1>
      <div class="sub">Final Audit Seal · F1-F9 Continuity · Dashboard Contract · No Source Read · No Apply</div>
    </div>
    <div class="seal">理</div>
  </div>

  <div class="cards">{cards}</div>

  <div class="sec">
    <h2>def Executive Judgment</h2>
    <span class="tag">FINAL SEAL ONLY</span><span class="tag">NO SOURCE READ</span><span class="tag">NO PROJECT RESCAN</span><span class="tag">NO MUTATION</span><span class="tag">NO APPLY</span><span class="tag">NO DB WRITE</span>
    <div class="note">F10 封存 F1-F9 治理成果為 final read-only audit seal。這不是修 source、不是寫 dashboard、不是 canonical merge。下一步若要進入實際整合，必須另開新分支，且先做 dry-run binding plan。</div>
    <input id="q" class="search" oninput="filterTables(this.value)" placeholder="搜尋 PASS / FAIL / SEALED / RED / GREEN / POLICY / ARTIFACT / DASHBOARD ..."/>
    <button class="btn" onclick="quick('PASS')">PASS</button>
    <button class="btn" onclick="quick('FAIL')">FAIL</button>
    <button class="btn" onclick="quick('SEALED')">SEALED</button>
    <button class="btn" onclick="quick('POLICY')">POLICY</button>
    <button class="btn" onclick="quick('ARTIFACT')">ARTIFACT</button>
    <button class="btn" onclick="quick('DASHBOARD')">DASHBOARD</button>
    <button class="btn" onclick="quick('')">RESET</button>
  </div>

  <div class="sec"><h2>def Final Readiness Gate</h2>{render_table(payload["readiness"], ["def_gate_status","def_allow_next","def_reason","def_input_rows","def_green_ledger_rows","def_red_evidence_rows","def_yellow_confirmation_rows","def_governance_params","def_ui_routes","def_widgets","def_binding_cards","def_final_validation_fail","def_source_read","def_project_rescan","def_apply_enabled","def_source_mutation","def_db_write","def_final_status"], 20)}</div>
  <div class="sec"><h2>def Final Quantity Validation</h2>{render_table(payload["quantity"], ["def_validation","def_expected","def_actual","def_status","def_message"], 80)}</div>
  <div class="sec"><h2>def Final Audit Continuity Matrix</h2>{render_table(payload["continuity"], ["def_phase","def_layer","def_status","def_evidence","def_no_action_policy"], 40)}</div>
  <div class="sec"><h2>def Final No-Action Policy Matrix</h2>{render_table(payload["policy"], ["def_policy_id","def_policy_name","def_control","def_required_value","def_status","def_message"], 80)}</div>
  <div class="sec"><h2>def Final Dashboard Contract Matrix</h2>{render_table(payload["dashboard_contract"], ["def_contract_id","def_contract_name","def_status","def_gate_source","def_binding_cards","def_action_guards","def_dashboard_sections","def_allowed","def_blocked","def_writeback"], 40)}</div>
  <div class="sec"><h2>def Final Artifact Index</h2>{render_table(payload["artifact_index"], ["def_artifact_id","def_artifact_name","def_path","def_status","def_source_read","def_source_mutation","def_apply_enabled"], 80)}</div>

  <div class="footer">
    SourceRun: <span class="path">{h(payload["source_run"])}</span><br/>
    RunDir: <span class="path">{h(payload["run_dir"])}</span><br/>
    SAFE: No external call · No project rescan · No source read · No source mutation · No canonical merge · No DB write · No apply
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
    seal = run_dir / "_final_read_only_seal"

    output.mkdir(parents=True, exist_ok=True)
    report.mkdir(parents=True, exist_ok=True)
    seal.mkdir(parents=True, exist_ok=True)

    bdir = source_run / "_dashboard_binding_preview"
    f9_ready = first(read_csv(source_run / "output" / "VIA_v0115F9_ReadinessGate.csv"))
    f9_manifest = read_json(source_run / "output" / "VIA_v0115F9_DashboardBindingPreview_Manifest.json")
    bindings = read_csv(bdir / "VIA_v0115F9_DashboardBindingCards.csv")
    guards = read_csv(bdir / "VIA_v0115F9_ActionGuardMatrix.csv")
    dashmap = read_csv(bdir / "VIA_v0115F9_DashboardSectionMap.csv")
    quantity_f9 = read_csv(bdir / "VIA_v0115F9_QuantityValidationMatrix.csv")

    artifact_index = build_final_artifact_index(source_run, run_dir)
    policy = build_final_policy_matrix()
    dashboard_contract = build_final_dashboard_contract(f9_ready, bindings, guards, dashmap)
    continuity = build_final_continuity_matrix(f9_ready, quantity_f9)
    quantity = build_final_quantity_validation(f9_ready, bindings, guards, dashmap, quantity_f9, artifact_index)
    readiness = build_final_readiness(quantity)

    write_csv(seal / "VIA_v0115F10_FinalReadinessGate.csv", readiness)
    write_csv(seal / "VIA_v0115F10_FinalQuantityValidationMatrix.csv", quantity)
    write_csv(seal / "VIA_v0115F10_FinalAuditContinuityMatrix.csv", continuity)
    write_csv(seal / "VIA_v0115F10_FinalNoActionPolicyMatrix.csv", policy)
    write_csv(seal / "VIA_v0115F10_FinalDashboardContractMatrix.csv", dashboard_contract)
    write_csv(seal / "VIA_v0115F10_FinalArtifactIndex.csv", artifact_index)
    write_csv(output / "VIA_v0115F10_ReadinessGate.csv", readiness)

    write_json(seal / "VIA_v0115F10_FinalReadinessGate.json", readiness)
    write_json(seal / "VIA_v0115F10_FinalQuantityValidationMatrix.json", quantity)
    write_json(seal / "VIA_v0115F10_FinalAuditContinuityMatrix.json", continuity)
    write_json(seal / "VIA_v0115F10_FinalNoActionPolicyMatrix.json", policy)
    write_json(seal / "VIA_v0115F10_FinalDashboardContractMatrix.json", dashboard_contract)
    write_json(seal / "VIA_v0115F10_FinalArtifactIndex.json", artifact_index)
    write_json(output / "VIA_v0115F10_ReadinessGate.json", readiness)

    html_path = report / "VIA_v0115F10_FinalReadOnlySeal_OnePage.html"
    payload = {
        "source_run": str(source_run),
        "run_dir": str(run_dir),
        "readiness": readiness,
        "quantity": quantity,
        "continuity": continuity,
        "policy": policy,
        "dashboard_contract": dashboard_contract,
        "artifact_index": artifact_index
    }
    write_html(html_path, payload)

    final_seal = {
        "schema_version": "VIA_v0115F10_FinalReadOnlySealOnly",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "gate": readiness[0]["def_gate_status"],
        "final_status": readiness[0]["def_final_status"],
        "source_run": str(source_run),
        "run_dir": str(run_dir),
        "report": str(html_path),
        "f9_manifest": f9_manifest,
        "counts": {
            "input_rows": 448,
            "green_ledger": 294,
            "red_evidence": 63,
            "yellow_confirmation": 91,
            "governance_params": 34,
            "routes": 8,
            "widgets": 9,
            "binding_cards": 8,
            "final_validation_fail": safe_int(readiness[0]["def_final_validation_fail"]),
        },
        "outputs": {
            "final_readiness": str(seal / "VIA_v0115F10_FinalReadinessGate.csv"),
            "final_quantity_validation": str(seal / "VIA_v0115F10_FinalQuantityValidationMatrix.csv"),
            "final_continuity": str(seal / "VIA_v0115F10_FinalAuditContinuityMatrix.csv"),
            "final_policy": str(seal / "VIA_v0115F10_FinalNoActionPolicyMatrix.csv"),
            "final_dashboard_contract": str(seal / "VIA_v0115F10_FinalDashboardContractMatrix.csv"),
            "final_artifact_index": str(seal / "VIA_v0115F10_FinalArtifactIndex.csv"),
            "html_report": str(html_path)
        },
        "policy": {
            "final_read_only_seal_only": True,
            "no_source_read": True,
            "no_project_rescan": True,
            "external_call": False,
            "execution_enabled": False,
            "apply_enabled": False,
            "source_mutation": False,
            "canonical_merge": False,
            "db_write": False,
            "delete": False,
            "stop_process": False
        }
    }
    write_json(output / "VIA_v0115F10_FinalReadOnlySeal_Manifest.json", final_seal)
    write_json(seal / "VIA_v0115F10_FINAL_AUDIT_SEAL.json", final_seal)

    print("")
    print("=" * 80)
    print("def VIA v0115F10 Final Read-Only Seal COMPLETE")
    print("=" * 80)
    print(f"Gate       : {readiness[0]['def_gate_status']}")
    print(f"Final      : {readiness[0]['def_final_status']}")
    print(f"Input Rows : {readiness[0]['def_input_rows']}")
    print(f"Green      : {readiness[0]['def_green_ledger_rows']}")
    print(f"Red        : {readiness[0]['def_red_evidence_rows']}")
    print(f"Yellow     : {readiness[0]['def_yellow_confirmation_rows']}")
    print(f"Routes     : {readiness[0]['def_ui_routes']}")
    print(f"Widgets    : {readiness[0]['def_widgets']}")
    print(f"Fail       : {readiness[0]['def_final_validation_fail']}")
    print(f"Report     : {html_path}")
    print(f"Seal       : {seal}")
    print(f"Output     : {output}")
    print("[SAFE] Final read-only seal only. No source read. No project rescan. No apply. No source mutation. No DB write.")


if __name__ == "__main__":
    main()
