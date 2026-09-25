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

import argparse
import csv
import hashlib
import html
import json
import re
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


def read_text_limited(path: Path, max_bytes: int = 8 * 1024 * 1024) -> str:
    if not path.exists() or not path.is_file():
        return ""
    size = path.stat().st_size
    if size > max_bytes:
        data = path.read_bytes()[:max_bytes]
        return data.decode("utf-8", errors="replace")
    return path.read_text(encoding="utf-8", errors="replace")


def sha12(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()[:12].upper()


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


def build_dashboard_inventory(dashboard: Path, text: str) -> List[Dict[str, Any]]:
    exists = dashboard.exists() and dashboard.is_file()
    return [{
        "def_dashboard_id": "DASH-CANDIDATE-001",
        "def_path": str(dashboard) if str(dashboard) else "",
        "def_exists": str(exists).lower(),
        "def_size_bytes": str(dashboard.stat().st_size) if exists else "0",
        "def_sha12": sha12(dashboard) if exists else "",
        "def_read_mode": "limited_html_read_only" if exists else "missing",
        "def_char_count": str(len(text)),
        "def_source_mutation": "false",
        "def_apply_enabled": "false",
        "def_db_write": "false"
    }]


def extract_anchor_map(text: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    seen = set()

    patterns = [
        ("HTML_ID", r'\bid\s*=\s*["\']([^"\']+)["\']'),
        ("HTML_CLASS", r'\bclass\s*=\s*["\']([^"\']+)["\']'),
        ("ANC_TOKEN", r'\bANC-[A-Z0-9\-]+'),
        ("VIA_ANCHOR", r'ANCHOR\[[^\]]+\]'),
        ("PAGE_TOKEN", r'\bpg\d+\b'),
        ("V26_MODULE", r'\bM\d{2}\b')
    ]

    n = 0
    for kind, pat in patterns:
        for m in re.finditer(pat, text):
            value = m.group(1) if m.groups() else m.group(0)
            if kind == "HTML_CLASS":
                values = [x for x in value.split() if x.strip()]
            else:
                values = [value]

            for v in values:
                key = (kind, v)
                if key in seen:
                    continue
                seen.add(key)
                n += 1
                rows.append({
                    "def_anchor_id": f"DASH-ANCHOR-{n:05d}",
                    "def_kind": kind,
                    "def_value": v,
                    "def_position": str(m.start()),
                    "def_binding_relevance": classify_anchor_relevance(v),
                    "def_patch_action": "none_dry_run_only"
                })

    return rows[:1200]


def classify_anchor_relevance(value: str) -> str:
    v = value.lower()
    if "tab" in v or v.startswith("pg"):
        return "page_navigation_candidate"
    if "card" in v or "grid" in v or "panel" in v:
        return "panel_card_candidate"
    if "table" in v or "matrix" in v:
        return "matrix_display_candidate"
    if "filter" in v or "search" in v:
        return "filter_widget_candidate"
    if "lock" in v:
        return "safety_lock_candidate"
    if "layout" in v:
        return "layout_control_candidate"
    return "general"


def infer_section(zone: str) -> str:
    z = zone.lower()
    if "red" in z or "yellow" in z or "evidence" in z or "confirmation" in z:
        return "Risk Control"
    if "green" in z or "governance parameter" in z:
        return "Clearance"
    if "subsystem" in z:
        return "Subsystems"
    return "Executive"


def build_dryrun_plan(bindings: List[Dict[str, str]], anchor_map: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    anchor_values = {prop(r, "def_value").lower() for r in anchor_map}
    has_page_nav = any(prop(r, "def_binding_relevance") == "page_navigation_candidate" for r in anchor_map)
    has_panel = any(prop(r, "def_binding_relevance") == "panel_card_candidate" for r in anchor_map)
    has_filter = any(prop(r, "def_binding_relevance") == "filter_widget_candidate" for r in anchor_map)

    rows: List[Dict[str, Any]] = []
    for i, b in enumerate(bindings, 1):
        zone = prop(b, "def_ui_zone")
        ryg = prop(b, "def_ryg")
        section = infer_section(zone)
        route = prop(b, "def_ui_route_id")
        title = prop(b, "def_card_title")
        anchor = prop(b, "def_dashboard_anchor")

        if ryg == "RED":
            safety = "locked_manual_review_no_repair_button"
        elif ryg == "YELLOW":
            safety = "confirmation_preview_no_full_read"
        else:
            safety = "read_only_candidate_no_writeback"

        rows.append({
            "def_plan_id": f"V0116-DRYRUN-{i:03d}",
            "def_source_route": route,
            "def_ui_zone": zone,
            "def_ryg": ryg,
            "def_expected_rows": prop(b, "def_expected_rows"),
            "def_target_dashboard_section": section,
            "def_proposed_anchor": anchor,
            "def_card_title": title,
            "def_binding_mode": prop(b, "def_action_mode"),
            "def_safety_contract": safety,
            "def_dashboard_has_page_nav": str(has_page_nav).lower(),
            "def_dashboard_has_panel_candidate": str(has_panel).lower(),
            "def_dashboard_has_filter_candidate": str(has_filter).lower(),
            "def_anchor_already_exists": str(anchor.lower() in anchor_values).lower(),
            "def_dryrun_action": "plan_insert_or_bind_card_preview_only",
            "def_patch_allowed": "false",
            "def_source_mutation": "false",
            "def_apply_enabled": "false",
            "def_db_write": "false"
        })

    return rows


def build_patch_diff_preview(plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for i, p in enumerate(plan, 1):
        rows.append({
            "def_diff_id": f"V0116-DIFF-{i:03d}",
            "def_target_section": prop(p, "def_target_dashboard_section"),
            "def_preview_operation": "WOULD_ADD_CARD_TO_DASHBOARD_PREVIEW_COPY_ONLY",
            "def_html_comment_marker": f"<!-- VIA:v0116:{prop(p, 'def_source_route')}:{prop(p, 'def_ryg')} -->",
            "def_card_title": prop(p, "def_card_title"),
            "def_expected_rows": prop(p, "def_expected_rows"),
            "def_blocked_now": "true",
            "def_reason_blocked": "dry-run plan only; no source mutation in v0116",
            "def_apply_enabled": "false"
        })
    return rows


def build_governance_route_matrix(plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    sections = ["Executive", "Risk Control", "Clearance", "Subsystems"]
    for sec in sections:
        items = [p for p in plan if prop(p, "def_target_dashboard_section") == sec]
        rows.append({
            "def_section": sec,
            "def_green": str(sum(1 for p in items if prop(p, "def_ryg") == "GREEN")),
            "def_red": str(sum(1 for p in items if prop(p, "def_ryg") == "RED")),
            "def_yellow": str(sum(1 for p in items if prop(p, "def_ryg") == "YELLOW")),
            "def_total": str(len(items)),
            "def_mode": "dashboard_binding_preview_only",
            "def_writeback": "false",
            "def_apply_enabled": "false"
        })
    return rows


def build_no_action_policy() -> List[Dict[str, Any]]:
    rules = [
        ("NO_EXTERNAL_CALL", "external_call", "false"),
        ("NO_PROJECT_RESCAN", "project_rescan", "false"),
        ("LIMITED_DASHBOARD_READ_ONLY", "dashboard_html_read", "limited_read_only"),
        ("NO_SOURCE_MUTATION", "source_mutation", "false"),
        ("NO_DASHBOARD_WRITEBACK", "dashboard_writeback", "false"),
        ("NO_CANONICAL_MERGE", "canonical_merge", "false"),
        ("NO_DB_WRITE", "db_write", "false"),
        ("NO_APPLY", "apply_enabled", "false"),
        ("NO_DELETE", "delete", "false"),
        ("NO_STOP_PROCESS", "stop_process", "false"),
        ("SECRET_SAFETY", "plaintext_secret_export", "false")
    ]
    return [
        {
            "def_policy_id": f"V0116-POLICY-{i:03d}",
            "def_policy_name": name,
            "def_control": control,
            "def_value": value,
            "def_status": "PASS",
            "def_message": "Dry-run only. No source/dashboard mutation."
        }
        for i, (name, control, value) in enumerate(rules, 1)
    ]


def build_validation(f10_ready: Dict[str, str], inventory: List[Dict[str, Any]], anchor_map: List[Dict[str, Any]], bindings: List[Dict[str, str]], plan: List[Dict[str, Any]], policy: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    inv = inventory[0] if inventory else {}
    rows = []

    def add(name: str, expected: Any, actual: Any, ok: bool, msg: str) -> None:
        rows.append({
            "def_validation": name,
            "def_expected": expected,
            "def_actual": actual,
            "def_status": "PASS" if ok else "FAIL",
            "def_message": msg
        })

    add("F10_GATE_READY", "FINAL_READ_ONLY_SEAL_READY_REVIEW_ONLY", prop(f10_ready, "def_gate_status"), prop(f10_ready, "def_gate_status") == "FINAL_READ_ONLY_SEAL_READY_REVIEW_ONLY", "F10 must be sealed.")
    add("F10_FINAL_STATUS", "VIA_v0115F10_FINAL_READ_ONLY_AUDIT_SEALED", prop(f10_ready, "def_final_status"), prop(f10_ready, "def_final_status") == "VIA_v0115F10_FINAL_READ_ONLY_AUDIT_SEALED", "Final audit status must be sealed.")
    add("INPUT_448", "448", prop(f10_ready, "def_input_rows"), prop(f10_ready, "def_input_rows") == "448", "Input continuity.")
    add("DASHBOARD_FOUND", "true", prop(inv, "def_exists"), prop(inv, "def_exists") == "true", "Dashboard HTML candidate must be found.")
    add("DASHBOARD_ANCHORS_PRESENT", ">0", len(anchor_map), len(anchor_map) > 0, "Dashboard IDs/classes/anchors must be extractable.")
    add("BINDING_CARDS_8", 8, len(bindings), len(bindings) == 8, "F9 binding cards carried through F10.")
    add("PLAN_ROWS_8", 8, len(plan), len(plan) == 8, "One dry-run plan row per binding route.")
    add("NO_PATCH_ALLOWED", "false", ",".join(sorted(set(prop(p, "def_patch_allowed") for p in plan))), all(prop(p, "def_patch_allowed") == "false" for p in plan), "No patch in v0116.")
    add("NO_SOURCE_MUTATION", "false", ",".join(sorted(set(prop(p, "def_source_mutation") for p in plan))), all(prop(p, "def_source_mutation") == "false" for p in plan), "No source mutation.")
    add("NO_APPLY", "false", ",".join(sorted(set(prop(p, "def_apply_enabled") for p in plan))), all(prop(p, "def_apply_enabled") == "false" for p in plan), "No apply.")
    add("NO_DB_WRITE", "false", ",".join(sorted(set(prop(p, "def_db_write") for p in plan))), all(prop(p, "def_db_write") == "false" for p in plan), "No DB write.")
    add("POLICY_MATRIX_PRESENT", ">=10", len(policy), len(policy) >= 10, "No-action policy matrix present.")

    return rows


def build_readiness(validation: List[Dict[str, Any]], f10_ready: Dict[str, str]) -> List[Dict[str, Any]]:
    fail = sum(1 for r in validation if prop(r, "def_status") != "PASS")
    return [{
        "def_gate_status": "DASHBOARD_BINDING_DRYRUN_PLAN_READY_REVIEW_ONLY" if fail == 0 else "BLOCKED_BY_v0116_DRYRUN_VALIDATION_FAIL",
        "def_allow_next": "true" if fail == 0 else "false",
        "def_reason": "v0116 generated dashboard binding dry-run plan. No dashboard writeback, no source mutation, no apply.",
        "def_input_rows": prop(f10_ready, "def_input_rows", "448"),
        "def_green_ledger_rows": prop(f10_ready, "def_green_ledger_rows", "294"),
        "def_red_evidence_rows": prop(f10_ready, "def_red_evidence_rows", "63"),
        "def_yellow_confirmation_rows": prop(f10_ready, "def_yellow_confirmation_rows", "91"),
        "def_ui_routes": prop(f10_ready, "def_ui_routes", "8"),
        "def_widgets": prop(f10_ready, "def_widgets", "9"),
        "def_binding_plan_rows": "8",
        "def_validation_fail": str(fail),
        "def_dashboard_read": "limited_html_read_only",
        "def_project_rescan": "false",
        "def_source_mutation": "false",
        "def_dashboard_writeback": "false",
        "def_apply_enabled": "false",
        "def_db_write": "false",
        "def_next_allowed_phase": "v0116B dashboard preview copy generation only"
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
        ("Routes", readiness["def_ui_routes"]),
        ("Fail", readiness["def_validation_fail"]),
        ("Next", "v0116B")
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
<head><meta charset="utf-8"/><title>VIA v0116 Dashboard Binding Dry-Run Plan</title><style>{style}</style><script>{js}</script></head>
<body><div class="wrap">
  <div class="header">
    <div>
      <h1>def VIA v0116 · Dashboard Binding Dry-Run Plan Only</h1>
      <div class="sub">F10 Seal → Central Dashboard Dry-Run Binding Plan · No Dashboard Writeback · No Apply</div>
    </div>
    <div class="seal">理</div>
  </div>

  <div class="cards">{cards}</div>

  <div class="sec">
    <h2>def Executive Judgment</h2>
    <span class="tag">DRY-RUN PLAN ONLY</span><span class="tag">LIMITED DASHBOARD READ</span><span class="tag">NO WRITEBACK</span><span class="tag">NO APPLY</span><span class="tag">NO DB WRITE</span>
    <div class="note">v0116 只做 dashboard binding dry-run plan。它讀取 F10 final seal 與 dashboard HTML 結構，產生建議對接矩陣；不修改原始 dashboard、不寫回 source、不合併 SSOT。</div>
    <input id="q" class="search" oninput="filterTables(this.value)" placeholder="搜尋 PASS / FAIL / GREEN / RED / YELLOW / Dashboard / Anchor / Plan ..."/>
    <button class="btn" onclick="quick('PASS')">PASS</button>
    <button class="btn" onclick="quick('FAIL')">FAIL</button>
    <button class="btn" onclick="quick('GREEN')">GREEN</button>
    <button class="btn" onclick="quick('RED')">RED</button>
    <button class="btn" onclick="quick('YELLOW')">YELLOW</button>
    <button class="btn" onclick="quick('ANCHOR')">ANCHOR</button>
    <button class="btn" onclick="quick('')">RESET</button>
  </div>

  <div class="sec"><h2>def Readiness Gate</h2>{render_table(payload["readiness"], ["def_gate_status","def_allow_next","def_reason","def_input_rows","def_green_ledger_rows","def_red_evidence_rows","def_yellow_confirmation_rows","def_ui_routes","def_widgets","def_binding_plan_rows","def_validation_fail","def_dashboard_read","def_project_rescan","def_source_mutation","def_dashboard_writeback","def_apply_enabled","def_db_write","def_next_allowed_phase"], 20)}</div>
  <div class="sec"><h2>def Validation Matrix</h2>{render_table(payload["validation"], ["def_validation","def_expected","def_actual","def_status","def_message"], 80)}</div>
  <div class="sec"><h2>def Dashboard Candidate Inventory</h2>{render_table(payload["inventory"], ["def_dashboard_id","def_path","def_exists","def_size_bytes","def_sha12","def_read_mode","def_char_count","def_source_mutation","def_apply_enabled"], 20)}</div>
  <div class="sec"><h2>def Dashboard Binding Dry-Run Plan</h2>{render_table(payload["plan"], ["def_plan_id","def_source_route","def_ui_zone","def_ryg","def_expected_rows","def_target_dashboard_section","def_proposed_anchor","def_card_title","def_binding_mode","def_safety_contract","def_anchor_already_exists","def_dryrun_action","def_patch_allowed","def_apply_enabled"], 100)}</div>
  <div class="sec"><h2>def Governance Route Matrix</h2>{render_table(payload["route_matrix"], ["def_section","def_green","def_red","def_yellow","def_total","def_mode","def_writeback","def_apply_enabled"], 20)}</div>
  <div class="sec"><h2>def Patch Diff Preview Matrix</h2>{render_table(payload["diff"], ["def_diff_id","def_target_section","def_preview_operation","def_html_comment_marker","def_card_title","def_expected_rows","def_blocked_now","def_reason_blocked","def_apply_enabled"], 100)}</div>
  <div class="sec"><h2>def No-Action Policy Matrix</h2>{render_table(payload["policy"], ["def_policy_id","def_policy_name","def_control","def_value","def_status","def_message"], 80)}</div>
  <div class="sec"><h2>def Dashboard Anchor Map Preview</h2>{render_table(payload["anchor_map"], ["def_anchor_id","def_kind","def_value","def_position","def_binding_relevance","def_patch_action"], 300)}</div>

  <div class="footer">
    SourceRun: <span class="path">{h(payload["source_run"])}</span><br/>
    Dashboard: <span class="path">{h(payload["dashboard"])}</span><br/>
    RunDir: <span class="path">{h(payload["run_dir"])}</span><br/>
    SAFE: No external call · No project rescan · Limited dashboard read only · No dashboard writeback · No source mutation · No canonical merge · No DB write · No apply
  </div>
</div></body></html>"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(doc, encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-run", required=True)
    ap.add_argument("--dashboard", required=False, default="")
    ap.add_argument("--run-dir", required=True)
    args = ap.parse_args()

    source_run = Path(args.source_run)
    dashboard = Path(args.dashboard) if args.dashboard else Path("")
    run_dir = Path(args.run_dir)
    output = run_dir / "output"
    report = run_dir / "report"
    plan_dir = run_dir / "_dashboard_binding_dryrun_plan"

    output.mkdir(parents=True, exist_ok=True)
    report.mkdir(parents=True, exist_ok=True)
    plan_dir.mkdir(parents=True, exist_ok=True)

    f10_ready = first(read_csv(source_run / "output" / "VIA_v0115F10_ReadinessGate.csv"))
    f10_manifest = read_json(source_run / "output" / "VIA_v0115F10_FinalReadOnlySeal_Manifest.json")
    artifact_index = read_csv(source_run / "_final_read_only_seal" / "VIA_v0115F10_FinalArtifactIndex.csv")

    # Locate F9 binding cards from artifact index.
    f9_binding_path = ""
    for r in artifact_index:
        if prop(r, "def_artifact_name") == "F9_BINDING_CARDS":
            f9_binding_path = prop(r, "def_path")
            break

    bindings = read_csv(Path(f9_binding_path)) if f9_binding_path else []

    dashboard_text = read_text_limited(dashboard) if str(dashboard) else ""
    inventory = build_dashboard_inventory(dashboard, dashboard_text)
    anchor_map = extract_anchor_map(dashboard_text)
    dryrun_plan = build_dryrun_plan(bindings, anchor_map)
    diff_preview = build_patch_diff_preview(dryrun_plan)
    route_matrix = build_governance_route_matrix(dryrun_plan)
    policy = build_no_action_policy()
    validation = build_validation(f10_ready, inventory, anchor_map, bindings, dryrun_plan, policy)
    readiness = build_readiness(validation, f10_ready)

    write_csv(plan_dir / "VIA_v0116_DashboardCandidateInventory.csv", inventory)
    write_csv(plan_dir / "VIA_v0116_DashboardAnchorMap.csv", anchor_map)
    write_csv(plan_dir / "VIA_v0116_DashboardBindingDryRunPlan.csv", dryrun_plan)
    write_csv(plan_dir / "VIA_v0116_PatchDiffPreviewMatrix.csv", diff_preview)
    write_csv(plan_dir / "VIA_v0116_GovernanceRouteMatrix.csv", route_matrix)
    write_csv(plan_dir / "VIA_v0116_NoActionPolicyMatrix.csv", policy)
    write_csv(plan_dir / "VIA_v0116_ValidationMatrix.csv", validation)
    write_csv(output / "VIA_v0116_ReadinessGate.csv", readiness)

    write_json(plan_dir / "VIA_v0116_DashboardCandidateInventory.json", inventory)
    write_json(plan_dir / "VIA_v0116_DashboardAnchorMap.json", anchor_map)
    write_json(plan_dir / "VIA_v0116_DashboardBindingDryRunPlan.json", dryrun_plan)
    write_json(plan_dir / "VIA_v0116_PatchDiffPreviewMatrix.json", diff_preview)
    write_json(plan_dir / "VIA_v0116_GovernanceRouteMatrix.json", route_matrix)
    write_json(plan_dir / "VIA_v0116_NoActionPolicyMatrix.json", policy)
    write_json(plan_dir / "VIA_v0116_ValidationMatrix.json", validation)
    write_json(output / "VIA_v0116_ReadinessGate.json", readiness)

    html_path = report / "VIA_v0116_DashboardBindingDryRunPlan_OnePage.html"
    payload = {
        "source_run": str(source_run),
        "dashboard": str(dashboard),
        "run_dir": str(run_dir),
        "readiness": readiness,
        "validation": validation,
        "inventory": inventory,
        "anchor_map": anchor_map,
        "plan": dryrun_plan,
        "diff": diff_preview,
        "route_matrix": route_matrix,
        "policy": policy
    }
    write_html(html_path, payload)

    manifest = {
        "schema_version": "VIA_v0116_DashboardBindingDryRunPlanOnly",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "gate": readiness[0]["def_gate_status"],
        "source_run": str(source_run),
        "dashboard": str(dashboard),
        "run_dir": str(run_dir),
        "report": str(html_path),
        "f10_manifest": f10_manifest,
        "outputs": {
            "dashboard_inventory": str(plan_dir / "VIA_v0116_DashboardCandidateInventory.csv"),
            "anchor_map": str(plan_dir / "VIA_v0116_DashboardAnchorMap.csv"),
            "dryrun_plan": str(plan_dir / "VIA_v0116_DashboardBindingDryRunPlan.csv"),
            "diff_preview": str(plan_dir / "VIA_v0116_PatchDiffPreviewMatrix.csv"),
            "route_matrix": str(plan_dir / "VIA_v0116_GovernanceRouteMatrix.csv"),
            "policy": str(plan_dir / "VIA_v0116_NoActionPolicyMatrix.csv"),
            "validation": str(plan_dir / "VIA_v0116_ValidationMatrix.csv"),
            "readiness": str(output / "VIA_v0116_ReadinessGate.csv"),
            "html_report": str(html_path)
        },
        "policy": {
            "dashboard_binding_dryrun_plan_only": True,
            "limited_dashboard_read_only": True,
            "no_project_rescan": True,
            "external_call": False,
            "execution_enabled": False,
            "apply_enabled": False,
            "source_mutation": False,
            "dashboard_writeback": False,
            "canonical_merge": False,
            "db_write": False,
            "delete": False,
            "stop_process": False
        }
    }
    write_json(output / "VIA_v0116_DashboardBindingDryRunPlan_Manifest.json", manifest)

    print("")
    print("=" * 80)
    print("def VIA v0116 Dashboard Binding Dry-Run Plan COMPLETE")
    print("=" * 80)
    print(f"Gate       : {readiness[0]['def_gate_status']}")
    print(f"Input Rows : {readiness[0]['def_input_rows']}")
    print(f"Green      : {readiness[0]['def_green_ledger_rows']}")
    print(f"Red        : {readiness[0]['def_red_evidence_rows']}")
    print(f"Yellow     : {readiness[0]['def_yellow_confirmation_rows']}")
    print(f"Routes     : {readiness[0]['def_ui_routes']}")
    print(f"Widgets    : {readiness[0]['def_widgets']}")
    print(f"PlanRows   : {readiness[0]['def_binding_plan_rows']}")
    print(f"Fail       : {readiness[0]['def_validation_fail']}")
    print(f"Dashboard  : {dashboard}")
    print(f"Report     : {html_path}")
    print(f"PlanDir    : {plan_dir}")
    print(f"Output     : {output}")
    print("[SAFE] Dry-run plan only. Limited dashboard read. No dashboard writeback. No source mutation. No apply. No DB write.")


if __name__ == "__main__":
    main()
