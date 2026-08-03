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


def int_prop(row: Dict[str, Any], key: str) -> int:
    try:
        return int(prop(row, key, "0"))
    except Exception:
        return 0


def build_ui_routes(readiness: Dict[str, str]) -> List[Dict[str, Any]]:
    blocked = "source_read;rescan;source_mutation;canonical_merge;db_write;apply;external_call;delete;stop_process"
    allowed = "view;filter;sort;export_csv;export_json;open_static_html;copy_path_text_only"

    return [
        {
            "def_ui_route_id": "F8-UI-ROUTE-001",
            "def_ui_zone": "Executive Gate",
            "def_source_matrix": "VIA_v0115F7_ReadinessGate",
            "def_ryg": "GREEN",
            "def_expected_rows": "1",
            "def_contract": "show final gate, counts, next phase, all no-action safety flags",
            "def_allowed_ui_actions": allowed,
            "def_blocked_actions": blocked,
            "def_next": "v0115F9_DASHBOARD_BINDING_PREVIEW_ONLY"
        },
        {
            "def_ui_route_id": "F8-UI-ROUTE-002",
            "def_ui_zone": "GREEN Clearance Ledger",
            "def_source_matrix": "F7 summary + F6 green candidate package",
            "def_ryg": "GREEN",
            "def_expected_rows": prop(readiness, "def_green_ledger_rows"),
            "def_contract": "display clearance ledger candidates as candidate-only assets; no auto-clear",
            "def_allowed_ui_actions": allowed,
            "def_blocked_actions": blocked,
            "def_next": "v0115F9_GREEN_LEDGER_UI_BINDING_PREVIEW_ONLY"
        },
        {
            "def_ui_route_id": "F8-UI-ROUTE-003",
            "def_ui_zone": "RED Evidence Pack",
            "def_source_matrix": "F7 summary + F6 red evidence package",
            "def_ryg": "RED",
            "def_expected_rows": prop(readiness, "def_red_evidence_rows"),
            "def_contract": "display red evidence candidates as locked manual review; no repair button",
            "def_allowed_ui_actions": allowed,
            "def_blocked_actions": blocked + ";auto_fix;batch_fix",
            "def_next": "v0115F9_RED_EVIDENCE_UI_BINDING_PREVIEW_ONLY"
        },
        {
            "def_ui_route_id": "F8-UI-ROUTE-004",
            "def_ui_zone": "YELLOW Confirmation",
            "def_source_matrix": "F7 summary + F6 yellow confirmation package",
            "def_ryg": "YELLOW",
            "def_expected_rows": prop(readiness, "def_yellow_confirmation_rows"),
            "def_contract": "display boundary/artifact/path-size confirmation candidates; no full read",
            "def_allowed_ui_actions": allowed,
            "def_blocked_actions": blocked + ";full_file_read",
            "def_next": "v0115F9_YELLOW_CONFIRMATION_UI_BINDING_PREVIEW_ONLY"
        },
        {
            "def_ui_route_id": "F8-UI-ROUTE-005",
            "def_ui_zone": "Governance Parameter Bridge",
            "def_source_matrix": "F6 GovernanceParameterBridge + F7 governance validation",
            "def_ryg": "GREEN",
            "def_expected_rows": prop(readiness, "def_governance_params"),
            "def_contract": "display default parameters read-only; mutable=false",
            "def_allowed_ui_actions": allowed,
            "def_blocked_actions": blocked + ";parameter_writeback",
            "def_next": "v0115F9_GOVERNANCE_PARAMETER_UI_BINDING_PREVIEW_ONLY"
        },
        {
            "def_ui_route_id": "F8-UI-ROUTE-006",
            "def_ui_zone": "Subsystem Matrix",
            "def_source_matrix": "VIA_v0115F7_SubsystemMatrix",
            "def_ryg": "GREEN",
            "def_expected_rows": "9",
            "def_contract": "display subsystem distribution with hydra control wording",
            "def_allowed_ui_actions": allowed,
            "def_blocked_actions": blocked,
            "def_next": "v0115F9_SUBSYSTEM_UI_BINDING_PREVIEW_ONLY"
        },
        {
            "def_ui_route_id": "F8-UI-ROUTE-007",
            "def_ui_zone": "Validation Matrix",
            "def_source_matrix": "VIA_v0115F7_FinalValidationMatrix",
            "def_ryg": "GREEN",
            "def_expected_rows": prop(readiness, "def_validation_rows"),
            "def_contract": "display PASS/FAIL validation rows; fail must remain 0 before next gate",
            "def_allowed_ui_actions": allowed,
            "def_blocked_actions": blocked,
            "def_next": "v0115F9_VALIDATION_UI_BINDING_PREVIEW_ONLY"
        },
        {
            "def_ui_route_id": "F8-UI-ROUTE-008",
            "def_ui_zone": "Export Contract",
            "def_source_matrix": "all F8 contract outputs",
            "def_ryg": "GREEN",
            "def_expected_rows": "csv/json/html",
            "def_contract": "export F8 contract only; no source mutation and no db write",
            "def_allowed_ui_actions": "export_contract_csv;export_contract_json;open_static_html",
            "def_blocked_actions": blocked,
            "def_next": "v0115F9_PREVIEW_ONLY"
        }
    ]


def build_widget_contract(routes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    widgets = [
        ("F8-WIDGET-001", "RYG Count Cards", "Gate/Input/Green/Red/Yellow/Gov/Fail/Next", "top cards", "read-only"),
        ("F8-WIDGET-002", "Search Filter", "client-side text filter", "all tables", "read-only"),
        ("F8-WIDGET-003", "Green Ledger Table", "candidate-only ledger table", "green route", "read-only"),
        ("F8-WIDGET-004", "Red Evidence Table", "manual-review locked table", "red route", "read-only"),
        ("F8-WIDGET-005", "Yellow Confirmation Table", "boundary/path-size confirmation table", "yellow route", "read-only"),
        ("F8-WIDGET-006", "Governance Parameter Table", "default parameter bridge", "gov route", "read-only"),
        ("F8-WIDGET-007", "Subsystem Matrix Table", "hydra control by subsystem", "subsystem route", "read-only"),
        ("F8-WIDGET-008", "Validation Table", "PASS/FAIL final validation", "validation route", "read-only"),
        ("F8-WIDGET-009", "Export Panel", "CSV/JSON/HTML contract locations", "footer", "read-only")
    ]

    for wid, name, purpose, target, mode in widgets:
        rows.append({
            "def_widget_id": wid,
            "def_widget_name": name,
            "def_purpose": purpose,
            "def_target_route": target,
            "def_mode": mode,
            "def_js_allowed": "filter;quick_filter;table_display",
            "def_js_blocked": "fetch;post;write_file;localStorage_secret;sessionStorage_secret;eval",
            "def_source_read": "false",
            "def_apply_enabled": "false",
            "def_source_mutation": "false",
            "def_db_write": "false"
        })
    return rows


def build_policy_matrix() -> List[Dict[str, Any]]:
    return [
        {
            "def_policy_id": "F8-POLICY-001",
            "def_policy_name": "RED Lock",
            "def_ryg": "RED",
            "def_rule": "RED rows are evidence-pack candidates only and require manual review.",
            "def_allowed": "view/filter/export",
            "def_blocked": "auto_fix;apply;source_mutation;batch_fix"
        },
        {
            "def_policy_id": "F8-POLICY-002",
            "def_policy_name": "YELLOW Confirmation",
            "def_ryg": "YELLOW",
            "def_rule": "YELLOW rows need boundary/artifact/path-size confirmation only.",
            "def_allowed": "view/filter/export/confirmation_preview",
            "def_blocked": "full_file_read;apply;source_mutation"
        },
        {
            "def_policy_id": "F8-POLICY-003",
            "def_policy_name": "GREEN Candidate",
            "def_ryg": "GREEN",
            "def_rule": "GREEN rows are clearance ledger candidates only, not auto-cleared.",
            "def_allowed": "view/filter/export/ledger_candidate_preview",
            "def_blocked": "auto_clear;db_write;canonical_merge"
        },
        {
            "def_policy_id": "F8-POLICY-004",
            "def_policy_name": "Governance Parameter Readonly",
            "def_ryg": "GREEN",
            "def_rule": "Governance parameters displayed as read-only contract.",
            "def_allowed": "view/export",
            "def_blocked": "parameter_writeback;source_mutation"
        },
        {
            "def_policy_id": "F8-POLICY-005",
            "def_policy_name": "Secret Safety",
            "def_ryg": "RED",
            "def_rule": "No plaintext secret in UI, CSV, JSON, HTML, localStorage, sessionStorage, or URL.",
            "def_allowed": "masking_contract;runtime_parameter_label",
            "def_blocked": "plaintext_secret_export;ui_secret_storage"
        }
    ]


def build_process_matrix(readiness: Dict[str, str]) -> List[Dict[str, Any]]:
    return [
        {
            "PROCESS": "01 Governance UI Contract Seal",
            "SUPPORTIVE MODULES": "Bridge validated F7 outputs into central U/I contract; no writeback.",
            "VDF": "VDF rows shown by RYG, with RED locked and GREEN candidate-only.",
            "VAP": "VAP UI/template risks shown as candidate/confirmation only.",
            "OTHERS": "VRN/VIS/VETF/Registry/Unclassified are routed into read-only panels.",
            "RYG": "GREEN",
            "COUNT": prop(readiness, "def_input_rows"),
            "NEXT": "v0115F9 dashboard binding preview only"
        },
        {
            "PROCESS": "02 Red Evidence Contract",
            "SUPPORTIVE MODULES": "Danger/secret evidence packs remain manual review only.",
            "VDF": "No VDF danger/secret repair until evidence pack is operator reviewed.",
            "VAP": "VAP active script danger remains locked.",
            "OTHERS": "Unclassified must be classified before action.",
            "RYG": "RED",
            "COUNT": prop(readiness, "def_red_evidence_rows"),
            "NEXT": "manual review route only"
        },
        {
            "PROCESS": "03 Yellow Confirmation Contract",
            "SUPPORTIVE MODULES": "Boundary/artifact/path-size confirmation only.",
            "VDF": "VDF boundary and artifact rows need confirmation before clearance.",
            "VAP": "Path-size and template rows are preview only; no full read.",
            "OTHERS": "Registry large files stay sample-plan only.",
            "RYG": "YELLOW",
            "COUNT": prop(readiness, "def_yellow_confirmation_rows"),
            "NEXT": "confirmation preview only"
        },
        {
            "PROCESS": "04 Green Ledger Contract",
            "SUPPORTIVE MODULES": "Green rows become clearance ledger candidates only.",
            "VDF": "Fieldname/schema/parameter labels routed to candidate ledger.",
            "VAP": "Comment/doc/CSS false-positive rows routed to candidate ledger.",
            "OTHERS": "No canonical merge and no DB write.",
            "RYG": "GREEN",
            "COUNT": prop(readiness, "def_green_ledger_rows"),
            "NEXT": "ledger validation route only"
        }
    ]


def build_quantity_validation(readiness: Dict[str, str], validation: List[Dict[str, str]], summary: List[Dict[str, str]], subsystem: List[Dict[str, str]], routes: List[Dict[str, Any]], widgets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    def add(name: str, expected: Any, actual: Any, ok: bool, msg: str) -> None:
        rows.append({
            "def_validation": name,
            "def_expected": expected,
            "def_actual": actual,
            "def_status": "PASS" if ok else "FAIL",
            "def_message": msg
        })

    input_rows = int_prop(readiness, "def_input_rows")
    green = int_prop(readiness, "def_green_ledger_rows")
    red = int_prop(readiness, "def_red_evidence_rows")
    yellow = int_prop(readiness, "def_yellow_confirmation_rows")
    gov = int_prop(readiness, "def_governance_params")
    fail = int_prop(readiness, "def_validation_fail")

    add("F7_GATE_READY", "LEDGER_EVIDENCE_VALIDATION_READY_REVIEW_ONLY", prop(readiness, "def_gate_status"), prop(readiness, "def_gate_status") == "LEDGER_EVIDENCE_VALIDATION_READY_REVIEW_ONLY", "F7 gate must be ready.")
    add("INPUT_448", 448, input_rows, input_rows == 448, "Continuity from F1-F7.")
    add("GREEN_294", 294, green, green == 294, "Green ledger candidate count.")
    add("RED_63", 63, red, red == 63, "Red evidence pack candidate count.")
    add("YELLOW_91", 91, yellow, yellow == 91, "Yellow confirmation candidate count.")
    add("RYG_SUM_448", 448, green + red + yellow, (green + red + yellow) == 448, "Green+Red+Yellow must equal input.")
    add("GOV_34", 34, gov, gov == 34, "Governance bridge count.")
    add("VALIDATION_FAIL_0", 0, fail, fail == 0, "F7 validation fail must be zero.")
    add("VALIDATION_ROWS_28", 28, len(validation), len(validation) == 28, "F7 validation rows.")
    add("SUMMARY_GROUPS_4", 4, len(summary), len(summary) == 4, "F7 summary groups.")
    add("SUBSYSTEM_ROWS_9", 9, len(subsystem), len(subsystem) == 9, "Subsystem matrix rows.")
    add("UI_ROUTES_8", 8, len(routes), len(routes) == 8, "UI route contract rows.")
    add("UI_WIDGETS_9", 9, len(widgets), len(widgets) == 9, "Widget contract rows.")
    add("NO_SOURCE_READ", "false", prop(readiness, "def_source_read"), prop(readiness, "def_source_read") == "false", "No source read.")
    add("NO_RESCAN", "false", prop(readiness, "def_rescan"), prop(readiness, "def_rescan") == "false", "No rescan.")
    add("NO_APPLY", "false", prop(readiness, "def_apply_enabled"), prop(readiness, "def_apply_enabled") == "false", "No apply.")
    add("NO_MUTATION", "false", prop(readiness, "def_source_mutation"), prop(readiness, "def_source_mutation") == "false", "No source mutation.")
    add("NO_DB_WRITE", "false", prop(readiness, "def_db_write"), prop(readiness, "def_db_write") == "false", "No DB write.")

    return rows


def build_readiness(quantity: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    fail = sum(1 for r in quantity if prop(r, "def_status") != "PASS")
    return [{
        "def_gate_status": "GOVERNANCE_UI_CONTRACT_SEAL_READY_REVIEW_ONLY" if fail == 0 else "BLOCKED_BY_F8_CONTRACT_VALIDATION_FAIL",
        "def_allow_next": "true" if fail == 0 else "false",
        "def_reason": "F8 sealed governance UI contract from F7 validated matrices. No source read, no mutation, no apply.",
        "def_input_rows": "448",
        "def_green_ledger_rows": "294",
        "def_red_evidence_rows": "63",
        "def_yellow_confirmation_rows": "91",
        "def_governance_params": "34",
        "def_quantity_validation_fail": str(fail),
        "def_source_read": "false",
        "def_rescan": "false",
        "def_execution_enabled": "false",
        "def_apply_enabled": "false",
        "def_source_mutation": "false",
        "def_canonical_merge": "false",
        "def_db_write": "false",
        "def_next_allowed_phase": "v0115F9 dashboard binding preview only"
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
            if "FAIL" in joined or "RED" in joined:
                cls = " class='risk-red'"
            elif "YELLOW" in joined:
                cls = " class='risk-yellow'"
            elif "PASS" in joined or "GREEN" in joined:
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
        ("Gov", readiness["def_governance_params"]),
        ("Fail", readiness["def_quantity_validation_fail"]),
        ("Next", "v0115F9")
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
<head><meta charset="utf-8"/><title>VIA v0115F8 Governance UI Contract Seal</title><style>{style}</style><script>{js}</script></head>
<body><div class="wrap">
  <div class="header">
    <div>
      <h1>def VIA v0115F8 · Governance UI Contract Seal Only</h1>
      <div class="sub">Central HTML U/I Contract · RYG Routes · Widgets · Quantity Validation · No Source Read · No Apply</div>
    </div>
    <div class="seal">理</div>
  </div>

  <div class="cards">{cards}</div>

  <div class="sec">
    <h2>def Executive Judgment</h2>
    <span class="tag">UI CONTRACT ONLY</span><span class="tag">NO SOURCE READ</span><span class="tag">NO MUTATION</span><span class="tag">NO APPLY</span><span class="tag">NO DB WRITE</span>
    <div class="note">F8 只封存中央 HTML U/I 契約：Green ledger、Red evidence、Yellow confirmation、Governance parameter bridge、Subsystem matrix、Validation matrix。這不是 source 修復，也不是 canonical merge。</div>
    <input id="q" class="search" oninput="filterTables(this.value)" placeholder="搜尋 PASS / FAIL / GREEN / RED / YELLOW / ROUTE / WIDGET / VDF / VAP ..."/>
    <button class="btn" onclick="quick('PASS')">PASS</button>
    <button class="btn" onclick="quick('FAIL')">FAIL</button>
    <button class="btn" onclick="quick('GREEN')">GREEN</button>
    <button class="btn" onclick="quick('RED')">RED</button>
    <button class="btn" onclick="quick('YELLOW')">YELLOW</button>
    <button class="btn" onclick="quick('ROUTE')">ROUTE</button>
    <button class="btn" onclick="quick('WIDGET')">WIDGET</button>
    <button class="btn" onclick="quick('')">RESET</button>
  </div>

  <div class="sec"><h2>def Readiness Gate</h2>{render_table(payload["readiness"], ["def_gate_status","def_allow_next","def_reason","def_input_rows","def_green_ledger_rows","def_red_evidence_rows","def_yellow_confirmation_rows","def_governance_params","def_quantity_validation_fail","def_source_read","def_rescan","def_apply_enabled","def_source_mutation","def_db_write","def_next_allowed_phase"], 20)}</div>
  <div class="sec"><h2>def Quantity Validation Matrix</h2>{render_table(payload["quantity"], ["def_validation","def_expected","def_actual","def_status","def_message"], 80)}</div>
  <div class="sec"><h2>def PROCESS / SUPPORTIVE MODULES / VDF / VAP / OTHERS</h2>{render_table(payload["process"], ["PROCESS","SUPPORTIVE MODULES","VDF","VAP","OTHERS","RYG","COUNT","NEXT"], 20)}</div>
  <div class="sec"><h2>def UI Route Contract</h2>{render_table(payload["routes"], ["def_ui_route_id","def_ui_zone","def_source_matrix","def_ryg","def_expected_rows","def_contract","def_allowed_ui_actions","def_blocked_actions","def_next"], 80)}</div>
  <div class="sec"><h2>def Widget Contract</h2>{render_table(payload["widgets"], ["def_widget_id","def_widget_name","def_purpose","def_target_route","def_mode","def_js_allowed","def_js_blocked","def_apply_enabled"], 80)}</div>
  <div class="sec"><h2>def RYG Policy Matrix</h2>{render_table(payload["policy"], ["def_policy_id","def_policy_name","def_ryg","def_rule","def_allowed","def_blocked"], 40)}</div>
  <div class="sec"><h2>def F7 Subsystem Matrix</h2>{render_table(payload["subsystem"], ["def_subsystem","def_green_ledger","def_red_evidence","def_yellow_confirmation","def_total","def_hydra_control","def_apply_enabled"], 80)}</div>

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
    contract = run_dir / "_governance_ui_contract_seal"

    output.mkdir(parents=True, exist_ok=True)
    report.mkdir(parents=True, exist_ok=True)
    contract.mkdir(parents=True, exist_ok=True)

    f7_dir = source_run / "_ledger_evidence_validation_only"
    readiness_rows = read_csv(source_run / "output" / "VIA_v0115F7_ReadinessGate.csv")
    validation = read_csv(f7_dir / "VIA_v0115F7_FinalValidationMatrix.csv")
    summary = read_csv(f7_dir / "VIA_v0115F7_SummaryMatrix.csv")
    subsystem = read_csv(f7_dir / "VIA_v0115F7_SubsystemMatrix.csv")

    f7_ready = first(readiness_rows)

    routes = build_ui_routes(f7_ready)
    widgets = build_widget_contract(routes)
    policy = build_policy_matrix()
    process = build_process_matrix(f7_ready)
    quantity = build_quantity_validation(f7_ready, validation, summary, subsystem, routes, widgets)
    readiness = build_readiness(quantity)

    write_csv(contract / "VIA_v0115F8_UIRouteContract.csv", routes)
    write_csv(contract / "VIA_v0115F8_WidgetContract.csv", widgets)
    write_csv(contract / "VIA_v0115F8_RYGPolicyMatrix.csv", policy)
    write_csv(contract / "VIA_v0115F8_ProcessSupportiveVdfVapOthersMatrix.csv", process)
    write_csv(contract / "VIA_v0115F8_QuantityValidationMatrix.csv", quantity)
    write_csv(contract / "VIA_v0115F8_F7SubsystemMatrix_Carried.csv", subsystem)
    write_csv(output / "VIA_v0115F8_ReadinessGate.csv", readiness)

    write_json(contract / "VIA_v0115F8_UIRouteContract.json", routes)
    write_json(contract / "VIA_v0115F8_WidgetContract.json", widgets)
    write_json(contract / "VIA_v0115F8_RYGPolicyMatrix.json", policy)
    write_json(contract / "VIA_v0115F8_ProcessSupportiveVdfVapOthersMatrix.json", process)
    write_json(contract / "VIA_v0115F8_QuantityValidationMatrix.json", quantity)
    write_json(contract / "VIA_v0115F8_F7SubsystemMatrix_Carried.json", subsystem)
    write_json(output / "VIA_v0115F8_ReadinessGate.json", readiness)

    html_path = report / "VIA_v0115F8_GovernanceUIContractSeal_OnePage.html"
    payload = {
        "source_run": str(source_run),
        "run_dir": str(run_dir),
        "readiness": readiness,
        "routes": routes,
        "widgets": widgets,
        "policy": policy,
        "process": process,
        "quantity": quantity,
        "subsystem": subsystem
    }
    write_html(html_path, payload)

    manifest = {
        "schema_version": "VIA_v0115F8_GovernanceUIContractSealOnly",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "gate": readiness[0]["def_gate_status"],
        "source_run": str(source_run),
        "run_dir": str(run_dir),
        "report": str(html_path),
        "outputs": {
            "ui_route_contract": str(contract / "VIA_v0115F8_UIRouteContract.csv"),
            "widget_contract": str(contract / "VIA_v0115F8_WidgetContract.csv"),
            "ryg_policy": str(contract / "VIA_v0115F8_RYGPolicyMatrix.csv"),
            "process_matrix": str(contract / "VIA_v0115F8_ProcessSupportiveVdfVapOthersMatrix.csv"),
            "quantity_validation": str(contract / "VIA_v0115F8_QuantityValidationMatrix.csv"),
            "readiness": str(output / "VIA_v0115F8_ReadinessGate.csv")
        },
        "policy": {
            "ui_contract_only": True,
            "no_source_read": True,
            "no_rescan": True,
            "external_call": False,
            "execution_enabled": False,
            "apply_enabled": False,
            "source_mutation": False,
            "canonical_merge": False,
            "db_write": False
        }
    }
    write_json(output / "VIA_v0115F8_GovernanceUIContractSeal_Manifest.json", manifest)

    print("")
    print("=" * 80)
    print("def VIA v0115F8 Governance UI Contract Seal COMPLETE")
    print("=" * 80)
    print(f"Gate       : {readiness[0]['def_gate_status']}")
    print(f"Input Rows : {readiness[0]['def_input_rows']}")
    print(f"Green      : {readiness[0]['def_green_ledger_rows']}")
    print(f"Red        : {readiness[0]['def_red_evidence_rows']}")
    print(f"Yellow     : {readiness[0]['def_yellow_confirmation_rows']}")
    print(f"Gov Params : {readiness[0]['def_governance_params']}")
    print(f"Fail       : {readiness[0]['def_quantity_validation_fail']}")
    print(f"Report     : {html_path}")
    print(f"Contract   : {contract}")
    print(f"Output     : {output}")
    print("[SAFE] UI contract only. No source read. No rescan. No apply. No source mutation. No DB write.")


if __name__ == "__main__":
    main()
