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
    cols = []
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


def build_binding_cards(routes: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    rows = []
    for i, r in enumerate(routes, 1):
        ryg = prop(r, "def_ryg")
        zone = prop(r, "def_ui_zone")
        route_id = prop(r, "def_ui_route_id")
        target_anchor = "route-" + route_id.lower().replace("_", "-")

        if ryg == "RED":
            action_mode = "LOCKED_MANUAL_REVIEW_PREVIEW"
            button_label = "View Locked Evidence"
        elif ryg == "YELLOW":
            action_mode = "CONFIRMATION_PREVIEW_ONLY"
            button_label = "View Confirmation"
        else:
            action_mode = "READONLY_PREVIEW"
            button_label = "Open Preview"

        rows.append({
            "def_binding_id": f"F9-BIND-{i:03d}",
            "def_ui_route_id": route_id,
            "def_ui_zone": zone,
            "def_ryg": ryg,
            "def_expected_rows": prop(r, "def_expected_rows"),
            "def_dashboard_anchor": target_anchor,
            "def_card_title": zone,
            "def_card_subtitle": prop(r, "def_contract"),
            "def_button_label": button_label,
            "def_action_mode": action_mode,
            "def_allowed_ui_actions": prop(r, "def_allowed_ui_actions"),
            "def_blocked_actions": prop(r, "def_blocked_actions"),
            "def_source_read": "false",
            "def_apply_enabled": "false",
            "def_source_mutation": "false",
            "def_db_write": "false"
        })
    return rows


def build_action_guard_matrix(bindings: List[Dict[str, Any]], widgets: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    rows = []
    n = 0

    for b in bindings:
        n += 1
        rows.append({
            "def_guard_id": f"F9-GUARD-ROUTE-{n:03d}",
            "def_scope": "route",
            "def_target": prop(b, "def_ui_zone"),
            "def_ryg": prop(b, "def_ryg"),
            "def_allowed": prop(b, "def_allowed_ui_actions"),
            "def_blocked": prop(b, "def_blocked_actions"),
            "def_enforcement": "static_preview_only",
            "def_apply_enabled": "false",
            "def_source_mutation": "false"
        })

    for w in widgets:
        n += 1
        rows.append({
            "def_guard_id": f"F9-GUARD-WIDGET-{n:03d}",
            "def_scope": "widget",
            "def_target": prop(w, "def_widget_name"),
            "def_ryg": "GREEN" if "Red" not in prop(w, "def_widget_name") else "RED",
            "def_allowed": prop(w, "def_js_allowed"),
            "def_blocked": prop(w, "def_js_blocked"),
            "def_enforcement": "client_filter_only_no_fetch_no_write",
            "def_apply_enabled": "false",
            "def_source_mutation": "false"
        })

    return rows


def build_dashboard_map(bindings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    groups = [
        ("DASH-SECTION-001", "Executive", "Executive Gate;Validation Matrix;Export Contract"),
        ("DASH-SECTION-002", "Risk Control", "RED Evidence Pack;YELLOW Confirmation;RYG Policy"),
        ("DASH-SECTION-003", "Clearance", "GREEN Clearance Ledger;Governance Parameter Bridge"),
        ("DASH-SECTION-004", "Subsystems", "Subsystem Matrix;PROCESS / SUPPORTIVE MODULES / VDF / VAP / OTHERS")
    ]

    rows = []
    for sid, title, contains in groups:
        count = 0
        for b in bindings:
            if any(x.strip().lower() in prop(b, "def_ui_zone").lower() for x in contains.split(";")):
                count += 1
        rows.append({
            "def_dashboard_section_id": sid,
            "def_section_title": title,
            "def_contains": contains,
            "def_bound_route_count": str(count),
            "def_mode": "preview_only",
            "def_writeback": "false",
            "def_apply_enabled": "false",
            "def_source_mutation": "false"
        })
    return rows


def build_quantity_validation(readiness: Dict[str, str], routes: List[Dict[str, str]], widgets: List[Dict[str, str]], bindings: List[Dict[str, Any]], guards: List[Dict[str, Any]], dashmap: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []

    def add(name: str, expected: Any, actual: Any, ok: bool, msg: str) -> None:
        rows.append({
            "def_validation": name,
            "def_expected": expected,
            "def_actual": actual,
            "def_status": "PASS" if ok else "FAIL",
            "def_message": msg
        })

    add("F8_GATE_READY", "GOVERNANCE_UI_CONTRACT_SEAL_READY_REVIEW_ONLY", prop(readiness, "def_gate_status"), prop(readiness, "def_gate_status") == "GOVERNANCE_UI_CONTRACT_SEAL_READY_REVIEW_ONLY", "F8 gate must be ready.")
    add("INPUT_448", 448, prop(readiness, "def_input_rows"), prop(readiness, "def_input_rows") == "448", "Input continuity.")
    add("GREEN_294", 294, prop(readiness, "def_green_ledger_rows"), prop(readiness, "def_green_ledger_rows") == "294", "Green continuity.")
    add("RED_63", 63, prop(readiness, "def_red_evidence_rows"), prop(readiness, "def_red_evidence_rows") == "63", "Red continuity.")
    add("YELLOW_91", 91, prop(readiness, "def_yellow_confirmation_rows"), prop(readiness, "def_yellow_confirmation_rows") == "91", "Yellow continuity.")
    add("GOV_34", 34, prop(readiness, "def_governance_params"), prop(readiness, "def_governance_params") == "34", "Governance continuity.")
    add("F8_QUANTITY_FAIL_0", 0, prop(readiness, "def_quantity_validation_fail"), prop(readiness, "def_quantity_validation_fail") == "0", "F8 quantity fail must be zero.")
    add("ROUTES_8", 8, len(routes), len(routes) == 8, "F8 route count.")
    add("WIDGETS_9", 9, len(widgets), len(widgets) == 9, "F8 widget count.")
    add("BINDINGS_8", 8, len(bindings), len(bindings) == 8, "F9 binding count.")
    add("DASHMAP_4", 4, len(dashmap), len(dashmap) == 4, "Dashboard section count.")
    add("GUARDS_PRESENT", ">=17", len(guards), len(guards) >= 17, "Route + widget guards present.")
    add("NO_SOURCE_READ", "false", prop(readiness, "def_source_read"), prop(readiness, "def_source_read") == "false", "No source read.")
    add("NO_RESCAN", "false", prop(readiness, "def_rescan"), prop(readiness, "def_rescan") == "false", "No rescan.")
    add("NO_APPLY", "false", prop(readiness, "def_apply_enabled"), prop(readiness, "def_apply_enabled") == "false", "No apply.")
    add("NO_MUTATION", "false", prop(readiness, "def_source_mutation"), prop(readiness, "def_source_mutation") == "false", "No source mutation.")
    add("NO_DB_WRITE", "false", prop(readiness, "def_db_write"), prop(readiness, "def_db_write") == "false", "No DB write.")

    return rows


def build_readiness(quantity: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    fail = sum(1 for r in quantity if prop(r, "def_status") != "PASS")
    return [{
        "def_gate_status": "DASHBOARD_BINDING_PREVIEW_READY_REVIEW_ONLY" if fail == 0 else "BLOCKED_BY_F9_BINDING_VALIDATION_FAIL",
        "def_allow_next": "true" if fail == 0 else "false",
        "def_reason": "F9 generated dashboard binding preview from F8 UI contract. No source read, no mutation, no apply.",
        "def_input_rows": "448",
        "def_green_ledger_rows": "294",
        "def_red_evidence_rows": "63",
        "def_yellow_confirmation_rows": "91",
        "def_governance_params": "34",
        "def_ui_routes": "8",
        "def_widgets": "9",
        "def_binding_cards": "8",
        "def_quantity_validation_fail": str(fail),
        "def_source_read": "false",
        "def_rescan": "false",
        "def_execution_enabled": "false",
        "def_apply_enabled": "false",
        "def_source_mutation": "false",
        "def_canonical_merge": "false",
        "def_db_write": "false",
        "def_next_allowed_phase": "v0115F10 final read-only seal only"
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
            if "FAIL" in joined or "RED" in joined or "LOCKED" in joined:
                cls = " class='risk-red'"
            elif "YELLOW" in joined or "CONFIRM" in joined:
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
        ("Routes", readiness["def_ui_routes"]),
        ("Fail", readiness["def_quantity_validation_fail"]),
        ("Next", "v0115F10")
    ]:
        cards += f"<div class='card'><div class='k'>{h(k)}</div><div class='v'>{h(v)}</div></div>"

    nav = ""
    for b in payload["bindings"]:
        cls = "green"
        if prop(b, "def_ryg") == "RED":
            cls = "red"
        elif prop(b, "def_ryg") == "YELLOW":
            cls = "yellow"
        nav += f"""
        <a class="navcard {cls}" href="#{h(prop(b, 'def_dashboard_anchor'))}">
            <div class="route">{h(prop(b, 'def_ui_route_id'))}</div>
            <div class="title">{h(prop(b, 'def_card_title'))}</div>
            <div class="desc">{h(prop(b, 'def_card_subtitle'))}</div>
            <div class="button">{h(prop(b, 'def_button_label'))}</div>
        </a>
        """

    style = """
:root{--bg:#f7f6f2;--paper:#fffefa;--line:#dedbd2;--ink:#24231f;--muted:#706d64;--seal:#8f2f24;--red:#c96b5a;--yellow:#c4943a;--green:#5a9e6f;--sky:#9fbcc2}
body{margin:0;background:radial-gradient(circle at 12% 10%,rgba(159,188,194,.24),transparent 28%),radial-gradient(circle at 88% 0%,rgba(180,200,190,.22),transparent 31%),linear-gradient(135deg,rgba(255,255,255,.70),rgba(247,246,242,1));color:var(--ink);font-family:'Microsoft JhengHei','Noto Sans TC',Arial,sans-serif;font-size:8.5px;line-height:1.35}
.wrap{max-width:1880px;margin:0 auto;padding:16px}.header{display:grid;grid-template-columns:1fr auto;gap:16px;align-items:start;margin-bottom:10px}
h1{font-size:15px;margin:0 0 4px;font-weight:650}.sub{font-size:8.2px;color:var(--muted)}
.seal{border:2px solid var(--seal);color:var(--seal);width:42px;height:42px;display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:700;border-radius:6px;background:rgba(255,255,255,.48)}
.cards{display:grid;grid-template-columns:repeat(8,1fr);gap:7px;margin:10px 0}.card{background:var(--paper);border:1px solid var(--line);border-radius:10px;padding:7px;min-height:43px;box-shadow:0 8px 22px rgba(60,50,30,.045)}
.k{font-size:7.5px;color:var(--muted)}.v{font:650 9.8px Consolas,monospace;margin-top:4px;word-break:break-word}
.navgrid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:12px 0}
.navcard{text-decoration:none;color:var(--ink);background:rgba(255,254,250,.95);border:1px solid var(--line);border-radius:15px;padding:12px;min-height:96px;box-shadow:0 10px 26px rgba(60,50,30,.045);transition:transform .25s ease,border-color .25s ease}
.navcard:hover{transform:translateY(-2px);border-color:var(--sky)}
.navcard.red{border-left:5px solid var(--red)}.navcard.yellow{border-left:5px solid var(--yellow)}.navcard.green{border-left:5px solid var(--green)}
.route{font:650 7.5px Consolas,monospace;color:var(--muted)}.title{font-size:11px;font-weight:650;margin:6px 0}.desc{font-size:7.8px;color:#555;min-height:30px}.button{margin-top:8px;display:inline-block;border:1px solid var(--line);border-radius:999px;padding:3px 8px;background:#fff;font-size:7.7px}
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
<head><meta charset="utf-8"/><title>VIA v0115F9 Dashboard Binding Preview</title><style>{style}</style><script>{js}</script></head>
<body><div class="wrap">
  <div class="header">
    <div>
      <h1>def VIA v0115F9 · Dashboard Binding Preview Only</h1>
      <div class="sub">Dashboard Entry Preview · RYG Route Cards · Widget Guards · No Source Read · No Apply</div>
    </div>
    <div class="seal">理</div>
  </div>

  <div class="cards">{cards}</div>

  <div class="sec">
    <h2>def Executive Judgment</h2>
    <span class="tag">DASHBOARD PREVIEW ONLY</span><span class="tag">NO SOURCE READ</span><span class="tag">NO MUTATION</span><span class="tag">NO APPLY</span><span class="tag">NO DB WRITE</span>
    <div class="note">F9 只將 F8 UI contract 轉成中央 dashboard binding preview。這不是寫回既有 dashboard，也不是 source 修復。所有卡片只允許 view/filter/export/open static HTML。</div>
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

  <div class="navgrid">{nav}</div>

  <div class="sec"><h2>def Readiness Gate</h2>{render_table(payload["readiness"], ["def_gate_status","def_allow_next","def_reason","def_input_rows","def_green_ledger_rows","def_red_evidence_rows","def_yellow_confirmation_rows","def_governance_params","def_ui_routes","def_widgets","def_binding_cards","def_quantity_validation_fail","def_source_read","def_rescan","def_apply_enabled","def_source_mutation","def_db_write","def_next_allowed_phase"], 20)}</div>
  <div class="sec"><h2>def Dashboard Binding Cards</h2>{render_table(payload["bindings"], ["def_binding_id","def_ui_route_id","def_ui_zone","def_ryg","def_expected_rows","def_dashboard_anchor","def_card_title","def_button_label","def_action_mode","def_blocked_actions","def_apply_enabled"], 80)}</div>
  <div class="sec"><h2>def Dashboard Section Map</h2>{render_table(payload["dashmap"], ["def_dashboard_section_id","def_section_title","def_contains","def_bound_route_count","def_mode","def_writeback","def_apply_enabled"], 40)}</div>
  <div class="sec"><h2>def Action Guard Matrix</h2>{render_table(payload["guards"], ["def_guard_id","def_scope","def_target","def_ryg","def_allowed","def_blocked","def_enforcement","def_apply_enabled","def_source_mutation"], 120)}</div>
  <div class="sec"><h2>def Quantity Validation Matrix</h2>{render_table(payload["quantity"], ["def_validation","def_expected","def_actual","def_status","def_message"], 80)}</div>
  <div class="sec"><h2>def Carried F8 Route Contract</h2>{render_table(payload["routes"], ["def_ui_route_id","def_ui_zone","def_source_matrix","def_ryg","def_expected_rows","def_contract","def_allowed_ui_actions","def_blocked_actions","def_next"], 80)}</div>

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
    binding = run_dir / "_dashboard_binding_preview"

    output.mkdir(parents=True, exist_ok=True)
    report.mkdir(parents=True, exist_ok=True)
    binding.mkdir(parents=True, exist_ok=True)

    cdir = source_run / "_governance_ui_contract_seal"

    f8_ready = first(read_csv(source_run / "output" / "VIA_v0115F8_ReadinessGate.csv"))
    routes = read_csv(cdir / "VIA_v0115F8_UIRouteContract.csv")
    widgets = read_csv(cdir / "VIA_v0115F8_WidgetContract.csv")
    quantity_f8 = read_csv(cdir / "VIA_v0115F8_QuantityValidationMatrix.csv")
    process = read_csv(cdir / "VIA_v0115F8_ProcessSupportiveVdfVapOthersMatrix.csv")
    policy = read_csv(cdir / "VIA_v0115F8_RYGPolicyMatrix.csv")

    bindings = build_binding_cards(routes)
    guards = build_action_guard_matrix(bindings, widgets)
    dashmap = build_dashboard_map(bindings)
    quantity = build_quantity_validation(f8_ready, routes, widgets, bindings, guards, dashmap)
    readiness = build_readiness(quantity)

    write_csv(binding / "VIA_v0115F9_DashboardBindingCards.csv", bindings)
    write_csv(binding / "VIA_v0115F9_ActionGuardMatrix.csv", guards)
    write_csv(binding / "VIA_v0115F9_DashboardSectionMap.csv", dashmap)
    write_csv(binding / "VIA_v0115F9_QuantityValidationMatrix.csv", quantity)
    write_csv(binding / "VIA_v0115F9_CarriedF8_UIRouteContract.csv", routes)
    write_csv(binding / "VIA_v0115F9_CarriedF8_WidgetContract.csv", widgets)
    write_csv(binding / "VIA_v0115F9_CarriedF8_ProcessMatrix.csv", process)
    write_csv(binding / "VIA_v0115F9_CarriedF8_RYGPolicyMatrix.csv", policy)
    write_csv(output / "VIA_v0115F9_ReadinessGate.csv", readiness)

    write_json(binding / "VIA_v0115F9_DashboardBindingCards.json", bindings)
    write_json(binding / "VIA_v0115F9_ActionGuardMatrix.json", guards)
    write_json(binding / "VIA_v0115F9_DashboardSectionMap.json", dashmap)
    write_json(binding / "VIA_v0115F9_QuantityValidationMatrix.json", quantity)
    write_json(output / "VIA_v0115F9_ReadinessGate.json", readiness)

    html_path = report / "VIA_v0115F9_DashboardBindingPreview_OnePage.html"
    payload = {
        "source_run": str(source_run),
        "run_dir": str(run_dir),
        "readiness": readiness,
        "bindings": bindings,
        "guards": guards,
        "dashmap": dashmap,
        "quantity": quantity,
        "routes": routes,
        "widgets": widgets,
        "quantity_f8": quantity_f8,
        "process": process,
        "policy": policy
    }
    write_html(html_path, payload)

    manifest = {
        "schema_version": "VIA_v0115F9_DashboardBindingPreviewOnly",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "gate": readiness[0]["def_gate_status"],
        "source_run": str(source_run),
        "run_dir": str(run_dir),
        "report": str(html_path),
        "outputs": {
            "dashboard_binding_cards": str(binding / "VIA_v0115F9_DashboardBindingCards.csv"),
            "action_guard_matrix": str(binding / "VIA_v0115F9_ActionGuardMatrix.csv"),
            "dashboard_section_map": str(binding / "VIA_v0115F9_DashboardSectionMap.csv"),
            "quantity_validation": str(binding / "VIA_v0115F9_QuantityValidationMatrix.csv"),
            "readiness": str(output / "VIA_v0115F9_ReadinessGate.csv")
        },
        "policy": {
            "dashboard_binding_preview_only": True,
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
    write_json(output / "VIA_v0115F9_DashboardBindingPreview_Manifest.json", manifest)

    print("")
    print("=" * 80)
    print("def VIA v0115F9 Dashboard Binding Preview COMPLETE")
    print("=" * 80)
    print(f"Gate       : {readiness[0]['def_gate_status']}")
    print(f"Input Rows : {readiness[0]['def_input_rows']}")
    print(f"Green      : {readiness[0]['def_green_ledger_rows']}")
    print(f"Red        : {readiness[0]['def_red_evidence_rows']}")
    print(f"Yellow     : {readiness[0]['def_yellow_confirmation_rows']}")
    print(f"Routes     : {readiness[0]['def_ui_routes']}")
    print(f"Widgets    : {readiness[0]['def_widgets']}")
    print(f"Fail       : {readiness[0]['def_quantity_validation_fail']}")
    print(f"Report     : {html_path}")
    print(f"Binding    : {binding}")
    print(f"Output     : {output}")
    print("[SAFE] Dashboard preview only. No source read. No rescan. No apply. No source mutation. No DB write.")


if __name__ == "__main__":
    main()
