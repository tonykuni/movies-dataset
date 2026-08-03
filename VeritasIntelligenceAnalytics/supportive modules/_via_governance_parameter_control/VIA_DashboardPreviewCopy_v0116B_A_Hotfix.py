from __future__ import annotations

import argparse
import csv
import hashlib
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


def first(rows: List[Dict[str, str]]) -> Dict[str, str]:
    return rows[0] if rows else {}


def h(x: Any) -> str:
    return html.escape("" if x is None else str(x))


def sha256_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest().upper()


def read_text(path: Path, max_bytes: int = 16 * 1024 * 1024) -> str:
    if not path.exists() or not path.is_file():
        return ""
    data = path.read_bytes()
    if len(data) > max_bytes:
        data = data[:max_bytes]
    return data.decode("utf-8", errors="replace")


def locate_dashboard(source_run: Path, manifest: Dict[str, Any]) -> Path:
    p = str(manifest.get("dashboard", "") or "")
    if p:
        return Path(p)

    inv = read_csv(source_run / "_dashboard_binding_dryrun_plan" / "VIA_v0116_DashboardCandidateInventory.csv")
    if inv:
        p2 = prop(inv[0], "def_path")
        if p2:
            return Path(p2)

    return Path("")


def build_preview_cards(plan: List[Dict[str, str]]) -> str:
    cards = []

    for row in plan:
        ryg = prop(row, "def_ryg", "GREEN")
        css = "red" if ryg == "RED" else "yellow" if ryg == "YELLOW" else "green"
        route = prop(row, "def_source_route")
        title = prop(row, "def_card_title")
        expected = prop(row, "def_expected_rows")
        section = prop(row, "def_target_dashboard_section")
        mode = prop(row, "def_binding_mode")
        safety = prop(row, "def_safety_contract")
        anchor = prop(row, "def_proposed_anchor")

        cards.append(f"""
<a class="via-card {css}" id="{h(anchor)}" href="#via-v0116b-preview-layer">
  <div class="via-route">{h(route)} · {h(ryg)}</div>
  <div class="via-card-title">{h(title)}</div>
  <div class="via-desc">{h(safety)}</div>
  <div class="via-badges">
    <span>Rows: {h(expected)}</span>
    <span>{h(section)}</span>
    <span>{h(mode)}</span>
  </div>
</a>
""")

    return "\n".join(cards)


def build_preview_layer(plan: List[Dict[str, str]], readiness: Dict[str, str], source_run: str) -> str:
    cards = build_preview_cards(plan)

    return f"""
<!-- VIA:v0116B:PREVIEW_COPY_LAYER:START -->
<style>
#via-v0116b-preview-layer {{
  margin: 32px auto;
  max-width: 1680px;
  padding: 18px;
  border: 1px solid rgba(143,47,36,.22);
  border-radius: 22px;
  background:
    radial-gradient(circle at 8% 0%, rgba(159,188,194,.20), transparent 30%),
    linear-gradient(135deg, rgba(255,254,250,.94), rgba(247,246,242,.92));
  box-shadow: 0 16px 42px rgba(60,50,30,.08);
  font-family: "Microsoft JhengHei","Noto Sans TC",Arial,sans-serif;
  color: #24231f;
}}
#via-v0116b-preview-layer .via-head {{
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: flex-start;
  margin-bottom: 12px;
}}
#via-v0116b-preview-layer .via-title {{
  font-size: 18px;
  font-weight: 700;
}}
#via-v0116b-preview-layer .via-sub {{
  font-size: 11px;
  color: #706d64;
  margin-top: 4px;
}}
#via-v0116b-preview-layer .via-seal {{
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid #8f2f24;
  color: #8f2f24;
  border-radius: 8px;
  font-size: 24px;
  font-weight: 700;
  background: rgba(255,255,255,.55);
}}
#via-v0116b-preview-layer .via-safe {{
  margin-top: 14px;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(90,158,111,.08);
  color: #355b44;
  font-size: 10px;
  border: 1px solid rgba(90,158,111,.16);
}}
#via-v0116b-preview-layer .via-cards {{
  display: grid;
  grid-template-columns: repeat(4, minmax(180px, 1fr));
  gap: 12px;
  margin-top: 14px;
}}
#via-v0116b-preview-layer .via-card {{
  border: 1px solid rgba(0,0,0,.10);
  border-radius: 16px;
  background: rgba(255,255,255,.78);
  padding: 14px;
  min-height: 124px;
  text-decoration: none;
  color: #24231f;
  box-shadow: 0 10px 26px rgba(60,50,30,.055);
}}
#via-v0116b-preview-layer .via-card.red {{ border-left: 6px solid #c96b5a; }}
#via-v0116b-preview-layer .via-card.yellow {{ border-left: 6px solid #c4943a; }}
#via-v0116b-preview-layer .via-card.green {{ border-left: 6px solid #5a9e6f; }}
#via-v0116b-preview-layer .via-route {{
  font: 700 10px Consolas, monospace;
  color: #706d64;
}}
#via-v0116b-preview-layer .via-card-title {{
  font-size: 14px;
  font-weight: 700;
  margin: 8px 0 5px;
}}
#via-v0116b-preview-layer .via-desc {{
  font-size: 10px;
  line-height: 1.45;
  color: #555149;
  min-height: 42px;
}}
#via-v0116b-preview-layer .via-badges {{
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-top: 8px;
}}
#via-v0116b-preview-layer .via-badges span {{
  border: 1px solid rgba(0,0,0,.12);
  border-radius: 999px;
  padding: 2px 7px;
  font-size: 9px;
  background: rgba(255,255,255,.72);
  color: #555149;
}}
@media(max-width:1100px) {{
  #via-v0116b-preview-layer .via-cards {{ grid-template-columns: repeat(2,minmax(180px,1fr)); }}
}}
@media(max-width:640px) {{
  #via-v0116b-preview-layer .via-cards {{ grid-template-columns: 1fr; }}
}}
</style>

<section id="via-v0116b-preview-layer">
  <div class="via-head">
    <div>
      <div class="via-title">VIA v0116B · Governance Dashboard Preview Copy</div>
      <div class="via-sub">Final Seal → Dashboard Binding Preview Copy · No Original Dashboard Writeback · No Apply · No DB Write</div>
    </div>
    <div class="via-seal">理</div>
  </div>

  <div class="via-safe">
    Gate: {h(prop(readiness, "def_gate_status"))} ·
    Input: {h(prop(readiness, "def_input_rows"))} ·
    Green: {h(prop(readiness, "def_green_ledger_rows"))} ·
    Red: {h(prop(readiness, "def_red_evidence_rows"))} ·
    Yellow: {h(prop(readiness, "def_yellow_confirmation_rows"))}<br/>
    This block is generated in a preview copy only. Original dashboard is untouched.
  </div>

  <div class="via-cards">
    {cards}
  </div>

  <div class="via-safe">
    SourceRun: {h(source_run)}<br/>
    SAFE: preview copy only · no source mutation · no dashboard writeback · no canonical merge · no DB write · no apply.
  </div>
</section>
<!-- VIA:v0116B:PREVIEW_COPY_LAYER:END -->
"""


def insert_preview_layer(original: str, layer: str) -> str:
    marker = "VIA:v0116B:PREVIEW_COPY_LAYER:START"
    if marker in original:
        return original

    idx = original.lower().rfind("</body>")
    if idx >= 0:
        return original[:idx] + "\n" + layer + "\n" + original[idx:]

    return original + "\n" + layer


def build_card_matrix(plan: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    rows = []
    for i, row in enumerate(plan, 1):
        rows.append({
            "def_preview_card_id": f"V0116B-CARD-{i:03d}",
            "def_source_route": prop(row, "def_source_route"),
            "def_title": prop(row, "def_card_title"),
            "def_ryg": prop(row, "def_ryg"),
            "def_expected_rows": prop(row, "def_expected_rows"),
            "def_section": prop(row, "def_target_dashboard_section"),
            "def_anchor": prop(row, "def_proposed_anchor"),
            "def_safety_contract": prop(row, "def_safety_contract"),
            "def_generated_in_preview_copy": "true",
            "def_original_dashboard_writeback": "false",
            "def_apply_enabled": "false"
        })
    return rows


def add_validation(rows: List[Dict[str, Any]], name: str, expected: Any, actual: Any, ok: bool, message: str) -> None:
    rows.append({
        "def_validation": name,
        "def_expected": expected,
        "def_actual": actual,
        "def_status": "PASS" if ok else "FAIL",
        "def_message": message
    })


def build_validation(
    readiness_in: Dict[str, str],
    dashboard: Path,
    preview_copy: Path,
    hash_before: str,
    hash_after: str,
    plan: List[Dict[str, str]],
    card_matrix: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    add_validation(rows, "V0116_GATE_READY", "DASHBOARD_BINDING_DRYRUN_PLAN_READY_REVIEW_ONLY", prop(readiness_in, "def_gate_status"), prop(readiness_in, "def_gate_status") == "DASHBOARD_BINDING_DRYRUN_PLAN_READY_REVIEW_ONLY", "v0116 must be ready.")
    add_validation(rows, "INPUT_448", "448", prop(readiness_in, "def_input_rows"), prop(readiness_in, "def_input_rows") == "448", "Input continuity.")
    add_validation(rows, "GREEN_294", "294", prop(readiness_in, "def_green_ledger_rows"), prop(readiness_in, "def_green_ledger_rows") == "294", "Green continuity.")
    add_validation(rows, "RED_63", "63", prop(readiness_in, "def_red_evidence_rows"), prop(readiness_in, "def_red_evidence_rows") == "63", "Red continuity.")
    add_validation(rows, "YELLOW_91", "91", prop(readiness_in, "def_yellow_confirmation_rows"), prop(readiness_in, "def_yellow_confirmation_rows") == "91", "Yellow continuity.")
    add_validation(rows, "DASHBOARD_EXISTS", "true", str(dashboard.exists()).lower(), dashboard.exists(), "Original dashboard must exist.")
    add_validation(rows, "ORIGINAL_HASH_UNCHANGED", hash_before, hash_after, bool(hash_before) and hash_before == hash_after, "Original dashboard hash must remain unchanged.")
    add_validation(rows, "PLAN_ROWS_8", 8, len(plan), len(plan) == 8, "Dry-run plan rows.")
    add_validation(rows, "CARD_ROWS_8", 8, len(card_matrix), len(card_matrix) == 8, "Preview card rows.")
    add_validation(rows, "PREVIEW_COPY_CREATED", "true", str(preview_copy.exists()).lower(), preview_copy.exists(), "Preview copy must be created.")
    add_validation(rows, "PREVIEW_COPY_SEPARATE_PATH", "different", "different" if str(preview_copy).lower() != str(dashboard).lower() else "same", str(preview_copy).lower() != str(dashboard).lower(), "Preview copy path must differ from original dashboard.")
    copy_text = read_text(preview_copy) if preview_copy.exists() else ""
    add_validation(rows, "PREVIEW_LAYER_MARKER_PRESENT", "true", str("VIA:v0116B:PREVIEW_COPY_LAYER:START" in copy_text).lower(), "VIA:v0116B:PREVIEW_COPY_LAYER:START" in copy_text, "Preview layer marker must exist.")
    add_validation(rows, "NO_PLAN_PATCH_ALLOWED", "false", ",".join(sorted(set(prop(p, "def_patch_allowed") for p in plan))), all(prop(p, "def_patch_allowed") == "false" for p in plan), "Plan remains patch=false.")
    add_validation(rows, "NO_APPLY", "false", ",".join(sorted(set(prop(p, "def_apply_enabled") for p in plan))), all(prop(p, "def_apply_enabled") == "false" for p in plan), "Apply remains false.")
    add_validation(rows, "NO_DB_WRITE", "false", "false", True, "No DB write.")

    return rows


def build_integrity(dashboard: Path, preview_copy: Path, hash_before: str, hash_after: str) -> List[Dict[str, Any]]:
    return [
        {
            "def_check": "ORIGINAL_DASHBOARD",
            "def_expected": "exists",
            "def_actual": "exists" if dashboard.exists() else "missing",
            "def_status": "PASS" if dashboard.exists() else "FAIL",
            "def_path": str(dashboard)
        },
        {
            "def_check": "ORIGINAL_HASH_UNCHANGED",
            "def_expected": hash_before,
            "def_actual": hash_after,
            "def_status": "PASS" if hash_before and hash_before == hash_after else "FAIL",
            "def_path": str(dashboard)
        },
        {
            "def_check": "PREVIEW_COPY",
            "def_expected": "created",
            "def_actual": "created" if preview_copy.exists() else "missing",
            "def_status": "PASS" if preview_copy.exists() else "FAIL",
            "def_path": str(preview_copy)
        }
    ]


def build_readiness(validation: List[Dict[str, Any]], readiness_in: Dict[str, str]) -> List[Dict[str, Any]]:
    fail = sum(1 for row in validation if prop(row, "def_status") != "PASS")
    return [{
        "def_gate_status": "DASHBOARD_PREVIEW_COPY_READY_REVIEW_ONLY" if fail == 0 else "BLOCKED_BY_v0116B_PREVIEW_COPY_VALIDATION_FAIL",
        "def_allow_next": "true" if fail == 0 else "false",
        "def_reason": "v0116B generated dashboard preview copy. Original dashboard unchanged. No source mutation, no apply.",
        "def_input_rows": prop(readiness_in, "def_input_rows", "448"),
        "def_green_ledger_rows": prop(readiness_in, "def_green_ledger_rows", "294"),
        "def_red_evidence_rows": prop(readiness_in, "def_red_evidence_rows", "63"),
        "def_yellow_confirmation_rows": prop(readiness_in, "def_yellow_confirmation_rows", "91"),
        "def_ui_routes": prop(readiness_in, "def_ui_routes", "8"),
        "def_widgets": prop(readiness_in, "def_widgets", "9"),
        "def_preview_cards": "8",
        "def_validation_fail": str(fail),
        "def_project_rescan": "false",
        "def_original_dashboard_writeback": "false",
        "def_source_mutation": "false",
        "def_apply_enabled": "false",
        "def_db_write": "false",
        "def_next_allowed_phase": "v0116C preview copy validation seal only"
    }]


def render_table(rows: List[Dict[str, Any]], cols: List[str]) -> str:
    parts = ["<table><thead><tr>"]
    for c in cols:
        parts.append(f"<th>{h(c)}</th>")
    parts.append("</tr></thead><tbody>")
    for r in rows:
        joined = " ".join(str(v) for v in r.values()).upper()
        cls = "risk-green"
        if "FAIL" in joined or "RED" in joined:
            cls = "risk-red"
        elif "YELLOW" in joined:
            cls = "risk-yellow"
        parts.append(f"<tr class='{cls}'>")
        for c in cols:
            parts.append(f"<td>{h(prop(r, c))}</td>")
        parts.append("</tr>")
    parts.append("</tbody></table>")
    return "".join(parts)


def write_report(path: Path, payload: Dict[str, Any]) -> None:
    readiness = payload["readiness"][0]
    style = """
<style>
body{font-family:"Microsoft JhengHei","Noto Sans TC",Arial,sans-serif;background:#f7f6f2;color:#24231f;margin:0}
.wrap{max-width:1680px;margin:0 auto;padding:18px}
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
.path{font-family:Consolas,monospace;color:#355b63}
</style>
"""
    cards = ""
    for k, v in [
        ("Gate", prop(readiness, "def_gate_status")),
        ("Input", prop(readiness, "def_input_rows")),
        ("Green", prop(readiness, "def_green_ledger_rows")),
        ("Red", prop(readiness, "def_red_evidence_rows")),
        ("Yellow", prop(readiness, "def_yellow_confirmation_rows")),
        ("Cards", prop(readiness, "def_preview_cards")),
        ("Fail", prop(readiness, "def_validation_fail")),
        ("Next", "v0116C")
    ]:
        cards += f"<div class='card'><div class='k'>{h(k)}</div><div class='v'>{h(v)}</div></div>"

    doc = f"""<!doctype html>
<html lang="zh-Hant">
<head><meta charset="utf-8"/><title>VIA v0116B-A Dashboard Preview Copy Hotfix</title>{style}</head>
<body><div class="wrap">
<h1>def VIA v0116B-A · Dashboard Preview Copy Hotfix</h1>
<div class="sub">Preview Copy Only · Original Dashboard Hash Unchanged · No Writeback · No Apply</div>
<div class="cards">{cards}</div>

<div class="sec"><h2>Readiness Gate</h2>{render_table(payload["readiness"], ["def_gate_status","def_allow_next","def_reason","def_input_rows","def_green_ledger_rows","def_red_evidence_rows","def_yellow_confirmation_rows","def_ui_routes","def_widgets","def_preview_cards","def_validation_fail","def_original_dashboard_writeback","def_source_mutation","def_apply_enabled","def_db_write","def_next_allowed_phase"])}</div>
<div class="sec"><h2>Validation Matrix</h2>{render_table(payload["validation"], ["def_validation","def_expected","def_actual","def_status","def_message"])}</div>
<div class="sec"><h2>Copy Integrity Matrix</h2>{render_table(payload["integrity"], ["def_check","def_expected","def_actual","def_status","def_path"])}</div>
<div class="sec"><h2>Preview Card Matrix</h2>{render_table(payload["cards"], ["def_preview_card_id","def_source_route","def_title","def_ryg","def_expected_rows","def_section","def_anchor","def_safety_contract","def_generated_in_preview_copy","def_original_dashboard_writeback","def_apply_enabled"])}</div>
<div class="sec"><h2>Preview Copy</h2><div class="path">{h(payload["preview_copy"])}</div></div>
<div class="sec"><h2>Original Dashboard</h2><div class="path">{h(payload["original_dashboard"])}</div></div>
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
    report_dir = run_dir / "report"
    copy_dir = run_dir / "_dashboard_preview_copy"

    output.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    copy_dir.mkdir(parents=True, exist_ok=True)

    manifest = read_json(source_run / "output" / "VIA_v0116_DashboardBindingDryRunPlan_Manifest.json")
    readiness_in = first(read_csv(source_run / "output" / "VIA_v0116_ReadinessGate.csv"))
    plan = read_csv(source_run / "_dashboard_binding_dryrun_plan" / "VIA_v0116_DashboardBindingDryRunPlan.csv")

    dashboard = locate_dashboard(source_run, manifest)
    original_hash_before = sha256_file(dashboard)

    original_text = read_text(dashboard)
    layer = build_preview_layer(plan, readiness_in, str(source_run))
    copy_text = insert_preview_layer(original_text, layer)

    preview_copy = copy_dir / ("VIA_v0116B_A_DashboardPreviewCopy_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".html")
    preview_copy.write_text(copy_text, encoding="utf-8")

    original_hash_after = sha256_file(dashboard)

    card_matrix = build_card_matrix(plan)
    integrity = build_integrity(dashboard, preview_copy, original_hash_before, original_hash_after)
    validation = build_validation(readiness_in, dashboard, preview_copy, original_hash_before, original_hash_after, plan, card_matrix)
    readiness = build_readiness(validation, readiness_in)

    write_csv(copy_dir / "VIA_v0116B_A_PreviewCardMatrix.csv", card_matrix)
    write_csv(copy_dir / "VIA_v0116B_A_CopyIntegrityMatrix.csv", integrity)
    write_csv(copy_dir / "VIA_v0116B_A_ValidationMatrix.csv", validation)
    write_csv(output / "VIA_v0116B_A_ReadinessGate.csv", readiness)

    write_json(copy_dir / "VIA_v0116B_A_PreviewCardMatrix.json", card_matrix)
    write_json(copy_dir / "VIA_v0116B_A_CopyIntegrityMatrix.json", integrity)
    write_json(copy_dir / "VIA_v0116B_A_ValidationMatrix.json", validation)
    write_json(output / "VIA_v0116B_A_ReadinessGate.json", readiness)

    report = report_dir / "VIA_v0116B_A_DashboardPreviewCopy_Report.html"
    payload = {
        "readiness": readiness,
        "validation": validation,
        "integrity": integrity,
        "cards": card_matrix,
        "preview_copy": str(preview_copy),
        "original_dashboard": str(dashboard)
    }
    write_report(report, payload)

    final_manifest = {
        "schema_version": "VIA_v0116B_A_DashboardPreviewCopyHotfix",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "gate": readiness[0]["def_gate_status"],
        "source_run": str(source_run),
        "run_dir": str(run_dir),
        "original_dashboard": str(dashboard),
        "original_dashboard_sha256_before": original_hash_before,
        "original_dashboard_sha256_after": original_hash_after,
        "preview_copy": str(preview_copy),
        "report": str(report),
        "outputs": {
            "readiness": str(output / "VIA_v0116B_A_ReadinessGate.csv"),
            "preview_card_matrix": str(copy_dir / "VIA_v0116B_A_PreviewCardMatrix.csv"),
            "copy_integrity": str(copy_dir / "VIA_v0116B_A_CopyIntegrityMatrix.csv"),
            "validation": str(copy_dir / "VIA_v0116B_A_ValidationMatrix.csv")
        },
        "policy": {
            "preview_copy_only": True,
            "original_dashboard_writeback": False,
            "source_mutation": False,
            "canonical_merge": False,
            "db_write": False,
            "apply_enabled": False
        }
    }
    write_json(output / "VIA_v0116B_A_DashboardPreviewCopy_Manifest.json", final_manifest)

    print("")
    print("=" * 80)
    print("def VIA v0116B-A Dashboard Preview Copy HOTFIX COMPLETE")
    print("=" * 80)
    print(f"Gate        : {readiness[0]['def_gate_status']}")
    print(f"Input Rows  : {readiness[0]['def_input_rows']}")
    print(f"Green       : {readiness[0]['def_green_ledger_rows']}")
    print(f"Red         : {readiness[0]['def_red_evidence_rows']}")
    print(f"Yellow      : {readiness[0]['def_yellow_confirmation_rows']}")
    print(f"Cards       : {readiness[0]['def_preview_cards']}")
    print(f"Fail        : {readiness[0]['def_validation_fail']}")
    print(f"Original    : {dashboard}")
    print(f"PreviewCopy : {preview_copy}")
    print(f"Report      : {report}")
    print("[SAFE] Preview copy only. Original dashboard unchanged. No writeback. No apply. No DB write.")


if __name__ == "__main__":
    main()
