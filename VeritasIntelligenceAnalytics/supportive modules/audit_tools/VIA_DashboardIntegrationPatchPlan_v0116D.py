from __future__ import annotations

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


def read_text(path: Path, max_bytes: int = 24 * 1024 * 1024) -> str:
    if not path.exists() or not path.is_file():
        return ""
    data = path.read_bytes()
    if len(data) > max_bytes:
        data = data[:max_bytes]
    return data.decode("utf-8", errors="replace")


def classify_target_section(title: str, ryg: str) -> str:
    t = title.lower()
    if ryg == "RED" or "evidence" in t:
        return "Risk Control"
    if ryg == "YELLOW" or "confirmation" in t:
        return "Risk Control"
    if "clearance" in t or "parameter" in t:
        return "Clearance"
    if "subsystem" in t:
        return "Subsystems"
    return "Executive"


def locate_v0116b_source_from_c_manifest(c_manifest: Dict[str, Any]) -> Path:
    source_run = str(c_manifest.get("source_run", "") or "")
    return Path(source_run)


def locate_b_files(source_run: Path) -> Dict[str, Path]:
    return {
        "manifest_a": source_run / "output" / "VIA_v0116B_A_DashboardPreviewCopy_Manifest.json",
        "manifest_b": source_run / "output" / "VIA_v0116B_DashboardPreviewCopy_Manifest.json",
        "cards_a": source_run / "_dashboard_preview_copy" / "VIA_v0116B_A_PreviewCardMatrix.csv",
        "cards_b": source_run / "_dashboard_preview_copy" / "VIA_v0116B_PreviewCardMatrix.csv",
        "validation_a": source_run / "_dashboard_preview_copy" / "VIA_v0116B_A_ValidationMatrix.csv",
        "validation_b": source_run / "_dashboard_preview_copy" / "VIA_v0116B_ValidationMatrix.csv",
    }


def load_b_manifest_and_cards(c_manifest: Dict[str, Any]) -> Dict[str, Any]:
    b_source = locate_v0116b_source_from_c_manifest(c_manifest)
    files = locate_b_files(b_source)

    if files["manifest_a"].exists():
        return {
            "b_source": b_source,
            "b_manifest": read_json(files["manifest_a"]),
            "cards": read_csv(files["cards_a"]),
            "b_validation": read_csv(files["validation_a"])
        }

    return {
        "b_source": b_source,
        "b_manifest": read_json(files["manifest_b"]),
        "cards": read_csv(files["cards_b"]),
        "b_validation": read_csv(files["validation_b"])
    }


def detect_dashboard_insert_zones(original_text: str) -> List[Dict[str, Any]]:
    zones: List[Dict[str, Any]] = []

    candidates = [
        ("BEFORE_BODY_END", "</body>", "append before closing body; safest because no existing module collision"),
        ("AFTER_NOTIFY_AREA", "id=\"notifyArea\"", "near existing notification/status area"),
        ("AFTER_PAGE7", "id=\"pg7\"", "near page 7 validation/reporting page"),
        ("AFTER_ENGINE_GRID", "id=\"engGrid\"", "near engine grid area"),
        ("AFTER_VISUAL_LOCK", "id=\"visualLock\"", "near visual lock safety area")
    ]

    for i, (name, needle, meaning) in enumerate(candidates, 1):
        idx = original_text.find(needle)
        zones.append({
            "def_zone_id": f"V0116D-ZONE-{i:03d}",
            "def_zone_name": name,
            "def_needle": needle,
            "def_position": str(idx),
            "def_found": str(idx >= 0).lower(),
            "def_safety_rank": "P0" if name == "BEFORE_BODY_END" else "P1",
            "def_meaning": meaning,
            "def_patch_allowed_now": "false"
        })

    return zones


def build_patch_plan(cards: List[Dict[str, str]], zones: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    body_zone = next((z for z in zones if prop(z, "def_zone_name") == "BEFORE_BODY_END"), {})
    body_found = prop(body_zone, "def_found") == "true"

    rows: List[Dict[str, Any]] = []
    for i, c in enumerate(cards, 1):
        title = prop(c, "def_title")
        ryg = prop(c, "def_ryg")
        section = classify_target_section(title, ryg)
        anchor = prop(c, "def_anchor")

        if ryg == "RED":
            guard = "locked_manual_review_no_repair_button"
            mode = "LOCKED_PANEL_ONLY"
        elif ryg == "YELLOW":
            guard = "confirmation_preview_no_full_read"
            mode = "CONFIRMATION_PANEL_ONLY"
        else:
            guard = "readonly_candidate_no_writeback"
            mode = "READONLY_PANEL_ONLY"

        rows.append({
            "def_patch_plan_id": f"V0116D-PATCHPLAN-{i:03d}",
            "def_source_card_id": prop(c, "def_preview_card_id"),
            "def_source_route": prop(c, "def_source_route"),
            "def_title": title,
            "def_ryg": ryg,
            "def_expected_rows": prop(c, "def_expected_rows"),
            "def_target_section": section,
            "def_target_anchor": anchor,
            "def_recommended_insert_zone": "BEFORE_BODY_END",
            "def_insert_zone_found": str(body_found).lower(),
            "def_patch_mode": mode,
            "def_guard_contract": guard,
            "def_operation": "WOULD_INSERT_PREVIEW_LAYER_OR_CARD_INTEGRATION",
            "def_patch_allowed_now": "false",
            "def_requires_operator_approval": "true",
            "def_apply_enabled": "false",
            "def_source_mutation": "false",
            "def_db_write": "false"
        })

    return rows


def build_patch_operation_matrix(plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    for i, p in enumerate(plan, 1):
        rows.append({
            "def_operation_id": f"V0116D-OP-{i:03d}",
            "def_operation_type": "HTML_INSERT_PLAN",
            "def_target": prop(p, "def_target_section"),
            "def_anchor": prop(p, "def_target_anchor"),
            "def_ryg": prop(p, "def_ryg"),
            "def_would_add_marker": f"<!-- VIA:v0116D:{prop(p, 'def_source_route')}:{prop(p, 'def_ryg')}:START -->",
            "def_would_add_card_title": prop(p, "def_title"),
            "def_blocked_now": "true",
            "def_block_reason": "v0116D is patch plan only; no source mutation",
            "def_apply_enabled": "false"
        })

    rows.append({
        "def_operation_id": "V0116D-OP-999",
        "def_operation_type": "HTML_BACKUP_PLAN",
        "def_target": "Original Dashboard",
        "def_anchor": "pre-patch backup path",
        "def_ryg": "YELLOW",
        "def_would_add_marker": "N/A",
        "def_would_add_card_title": "Would create timestamped backup before any future patch branch",
        "def_blocked_now": "true",
        "def_block_reason": "backup creation postponed to future apply branch; no write in v0116D",
        "def_apply_enabled": "false"
    })

    return rows


def build_guard_matrix(plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    base_guards = [
        ("NO_ORIGINAL_WRITEBACK", "original_dashboard_writeback", "false"),
        ("NO_SOURCE_MUTATION", "source_mutation", "false"),
        ("NO_CANONICAL_MERGE", "canonical_merge", "false"),
        ("NO_DB_WRITE", "db_write", "false"),
        ("NO_APPLY", "apply_enabled", "false"),
        ("NO_DELETE", "delete", "false"),
        ("NO_STOP_PROCESS", "stop_process", "false"),
        ("SECRET_SAFETY", "plaintext_secret_export", "false"),
        ("REQUIRE_BACKUP_BEFORE_FUTURE_APPLY", "backup_before_apply", "true"),
        ("REQUIRE_OPERATOR_APPROVAL", "operator_approval", "true")
    ]

    for i, (name, control, value) in enumerate(base_guards, 1):
        rows.append({
            "def_guard_id": f"V0116D-GUARD-{i:03d}",
            "def_guard_name": name,
            "def_control": control,
            "def_required_value": value,
            "def_status": "PASS",
            "def_message": "Patch plan only. Future apply branch must re-check.",
            "def_apply_enabled": "false"
        })

    for p in plan:
        if prop(p, "def_ryg") == "RED":
            rows.append({
                "def_guard_id": "V0116D-GUARD-RED-LOCK",
                "def_guard_name": "RED_LOCK_NO_REPAIR_BUTTON",
                "def_control": prop(p, "def_target_anchor"),
                "def_required_value": "locked",
                "def_status": "PASS",
                "def_message": "RED card must not expose repair/apply/batch-fix UI.",
                "def_apply_enabled": "false"
            })

    return rows


def build_rollback_matrix(original_dashboard: Path, preview_copy: Path) -> List[Dict[str, Any]]:
    return [
        {
            "def_rollback_id": "V0116D-ROLLBACK-001",
            "def_step": "Pre-apply backup",
            "def_required_future_action": "Create timestamped copy of original dashboard before any real patch.",
            "def_expected_path_pattern": str(original_dashboard) + ".YYYYMMDD_HHMMSS.v0116E.before_patch.bak",
            "def_status": "PLAN_ONLY",
            "def_apply_enabled": "false"
        },
        {
            "def_rollback_id": "V0116D-ROLLBACK-002",
            "def_step": "Hash verification",
            "def_required_future_action": "Compare original hash before/after future patch; fail closed if mismatch outside planned diff.",
            "def_expected_path_pattern": str(original_dashboard),
            "def_status": "PLAN_ONLY",
            "def_apply_enabled": "false"
        },
        {
            "def_rollback_id": "V0116D-ROLLBACK-003",
            "def_step": "Rollback restore",
            "def_required_future_action": "If future patch validation fails, restore from backup copy only after operator approval.",
            "def_expected_path_pattern": str(original_dashboard),
            "def_status": "PLAN_ONLY",
            "def_apply_enabled": "false"
        },
        {
            "def_rollback_id": "V0116D-ROLLBACK-004",
            "def_step": "Preview copy reference",
            "def_required_future_action": "Use validated preview copy as visual reference, not as direct overwrite.",
            "def_expected_path_pattern": str(preview_copy),
            "def_status": "PLAN_ONLY",
            "def_apply_enabled": "false"
        }
    ]


def build_quantity_validation(
    c_ready: Dict[str, str],
    c_validation: List[Dict[str, str]],
    cards: List[Dict[str, str]],
    zones: List[Dict[str, Any]],
    plan: List[Dict[str, Any]],
    ops: List[Dict[str, Any]],
    guards: List[Dict[str, Any]],
    rollback: List[Dict[str, Any]],
    original_dashboard: Path,
    preview_copy: Path,
    original_hash: str
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

    add("V0116C_GATE_READY", "PREVIEW_COPY_VALIDATION_SEAL_READY_REVIEW_ONLY", prop(c_ready, "def_gate_status"), prop(c_ready, "def_gate_status") == "PREVIEW_COPY_VALIDATION_SEAL_READY_REVIEW_ONLY", "v0116C must be ready.")
    add("INPUT_448", "448", prop(c_ready, "def_input_rows"), prop(c_ready, "def_input_rows") == "448", "Input continuity.")
    add("GREEN_294", "294", prop(c_ready, "def_green_ledger_rows"), prop(c_ready, "def_green_ledger_rows") == "294", "Green continuity.")
    add("RED_63", "63", prop(c_ready, "def_red_evidence_rows"), prop(c_ready, "def_red_evidence_rows") == "63", "Red continuity.")
    add("YELLOW_91", "91", prop(c_ready, "def_yellow_confirmation_rows"), prop(c_ready, "def_yellow_confirmation_rows") == "91", "Yellow continuity.")
    add("C_VALIDATION_FAIL_0", "0", prop(c_ready, "def_validation_fail"), prop(c_ready, "def_validation_fail") == "0", "v0116C validation fail must be zero.")
    add("C_VALIDATION_ROWS_GE_16", ">=16", len(c_validation), len(c_validation) >= 16, "v0116C validation rows.")
    add("CARD_ROWS_8", 8, len(cards), len(cards) == 8, "Preview card matrix rows.")
    add("ZONE_ROWS_GE_5", ">=5", len(zones), len(zones) >= 5, "Detected insertion zones.")
    add("PATCH_PLAN_ROWS_8", 8, len(plan), len(plan) == 8, "Patch plan rows.")
    add("PATCH_OPS_GE_9", ">=9", len(ops), len(ops) >= 9, "Patch operation rows.")
    add("GUARDS_GE_10", ">=10", len(guards), len(guards) >= 10, "Guard rows.")
    add("ROLLBACK_ROWS_4", 4, len(rollback), len(rollback) == 4, "Rollback plan rows.")
    add("ORIGINAL_DASHBOARD_EXISTS", "true", str(original_dashboard.exists()).lower(), original_dashboard.exists(), "Original dashboard must exist.")
    add("PREVIEW_COPY_EXISTS", "true", str(preview_copy.exists()).lower(), preview_copy.exists(), "Preview copy must exist.")
    add("ORIGINAL_HASH_PRESENT", "sha256", original_hash[:12], bool(original_hash), "Original hash must be captured.")
    add("NO_PATCH_ALLOWED_NOW", "false", ",".join(sorted(set(prop(p, "def_patch_allowed_now") for p in plan))), all(prop(p, "def_patch_allowed_now") == "false" for p in plan), "No patch in v0116D.")
    add("NO_APPLY", "false", ",".join(sorted(set(prop(p, "def_apply_enabled") for p in plan))), all(prop(p, "def_apply_enabled") == "false" for p in plan), "Apply false.")
    add("NO_DB_WRITE", "false", ",".join(sorted(set(prop(p, "def_db_write") for p in plan))), all(prop(p, "def_db_write") == "false" for p in plan), "DB write false.")

    return rows


def build_readiness(validation: List[Dict[str, Any]], c_ready: Dict[str, str]) -> List[Dict[str, Any]]:
    fail = sum(1 for r in validation if prop(r, "def_status") != "PASS")
    return [{
        "def_gate_status": "DASHBOARD_INTEGRATION_PATCH_PLAN_READY_REVIEW_ONLY" if fail == 0 else "BLOCKED_BY_v0116D_PATCH_PLAN_VALIDATION_FAIL",
        "def_allow_next": "true" if fail == 0 else "false",
        "def_reason": "v0116D generated dashboard integration patch plan only. No dashboard writeback, no apply.",
        "def_input_rows": prop(c_ready, "def_input_rows", "448"),
        "def_green_ledger_rows": prop(c_ready, "def_green_ledger_rows", "294"),
        "def_red_evidence_rows": prop(c_ready, "def_red_evidence_rows", "63"),
        "def_yellow_confirmation_rows": prop(c_ready, "def_yellow_confirmation_rows", "91"),
        "def_preview_cards": prop(c_ready, "def_preview_cards", "8"),
        "def_patch_plan_rows": "8",
        "def_validation_fail": str(fail),
        "def_patch_allowed_now": "false",
        "def_original_dashboard_writeback": "false",
        "def_source_mutation": "false",
        "def_canonical_merge": "false",
        "def_apply_enabled": "false",
        "def_db_write": "false",
        "def_next_allowed_phase": "v0116E operator approval package only"
    }]


def render_table(rows: List[Dict[str, Any]], cols: List[str]) -> str:
    out = ["<table><thead><tr>"]
    for c in cols:
        out.append(f"<th>{h(c)}</th>")
    out.append("</tr></thead><tbody>")
    for r in rows:
        joined = " ".join(str(v) for v in r.values()).upper()
        cls = "risk-green"
        if "FAIL" in joined or "RED" in joined or "LOCK" in joined:
            cls = "risk-red"
        elif "YELLOW" in joined or "PLAN_ONLY" in joined:
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
.wrap{max-width:1740px;margin:0 auto;padding:18px}
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
        ("PatchPlan", prop(readiness, "def_patch_plan_rows")),
        ("Fail", prop(readiness, "def_validation_fail")),
        ("Next", "v0116E")
    ]:
        cards += f"<div class='card'><div class='k'>{h(k)}</div><div class='v'>{h(v)}</div></div>"

    doc = f"""<!doctype html>
<html lang="zh-Hant">
<head><meta charset="utf-8"/><title>VIA v0116D Dashboard Integration Patch Plan</title>{style}</head>
<body><div class="wrap">
<h1>def VIA v0116D · Dashboard Integration Patch Plan Only</h1>
<div class="sub">Patch Plan Only · No Original Dashboard Writeback · No Apply · No DB Write</div>
<div class="cards">{cards}</div>

<div class="sec"><h2>Readiness Gate</h2>{render_table(payload["readiness"], ["def_gate_status","def_allow_next","def_reason","def_input_rows","def_green_ledger_rows","def_red_evidence_rows","def_yellow_confirmation_rows","def_preview_cards","def_patch_plan_rows","def_validation_fail","def_patch_allowed_now","def_original_dashboard_writeback","def_source_mutation","def_canonical_merge","def_apply_enabled","def_db_write","def_next_allowed_phase"])}</div>
<div class="sec"><h2>Quantity Validation Matrix</h2>{render_table(payload["validation"], ["def_validation","def_expected","def_actual","def_status","def_message"])}</div>
<div class="sec"><h2>Dashboard Insert Zone Matrix</h2>{render_table(payload["zones"], ["def_zone_id","def_zone_name","def_needle","def_position","def_found","def_safety_rank","def_meaning","def_patch_allowed_now"])}</div>
<div class="sec"><h2>Dashboard Integration Patch Plan</h2>{render_table(payload["plan"], ["def_patch_plan_id","def_source_card_id","def_source_route","def_title","def_ryg","def_expected_rows","def_target_section","def_target_anchor","def_recommended_insert_zone","def_insert_zone_found","def_patch_mode","def_guard_contract","def_operation","def_patch_allowed_now","def_requires_operator_approval","def_apply_enabled"])}</div>
<div class="sec"><h2>Patch Operation Matrix</h2>{render_table(payload["ops"], ["def_operation_id","def_operation_type","def_target","def_anchor","def_ryg","def_would_add_marker","def_would_add_card_title","def_blocked_now","def_block_reason","def_apply_enabled"])}</div>
<div class="sec"><h2>Risk Guard Matrix</h2>{render_table(payload["guards"], ["def_guard_id","def_guard_name","def_control","def_required_value","def_status","def_message","def_apply_enabled"])}</div>
<div class="sec"><h2>Rollback Plan Matrix</h2>{render_table(payload["rollback"], ["def_rollback_id","def_step","def_required_future_action","def_expected_path_pattern","def_status","def_apply_enabled"])}</div>
<div class="sec"><h2>Original Dashboard</h2><div class="path">{h(payload["original_dashboard"])}</div></div>
<div class="sec"><h2>Preview Copy</h2><div class="path">{h(payload["preview_copy"])}</div></div>
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
    plan_dir = run_dir / "_dashboard_integration_patch_plan"

    output.mkdir(parents=True, exist_ok=True)
    report.mkdir(parents=True, exist_ok=True)
    plan_dir.mkdir(parents=True, exist_ok=True)

    c_manifest = read_json(source_run / "output" / "VIA_v0116C_PreviewCopyValidationSeal_Manifest.json")
    c_ready = first(read_csv(source_run / "output" / "VIA_v0116C_ReadinessGate.csv"))
    c_validation = read_csv(source_run / "_preview_copy_validation_seal" / "VIA_v0116C_FinalValidationMatrix.csv")

    b_payload = load_b_manifest_and_cards(c_manifest)
    b_manifest = b_payload["b_manifest"]
    cards = b_payload["cards"]

    original_dashboard = Path(str(c_manifest.get("original_dashboard", "") or b_manifest.get("original_dashboard", "") or ""))
    preview_copy = Path(str(c_manifest.get("preview_copy", "") or b_manifest.get("preview_copy", "") or ""))

    original_text = read_text(original_dashboard)
    original_hash = sha256_file(original_dashboard)

    zones = detect_dashboard_insert_zones(original_text)
    patch_plan = build_patch_plan(cards, zones)
    ops = build_patch_operation_matrix(patch_plan)
    guards = build_guard_matrix(patch_plan)
    rollback = build_rollback_matrix(original_dashboard, preview_copy)
    validation = build_quantity_validation(
        c_ready, c_validation, cards, zones, patch_plan, ops, guards, rollback,
        original_dashboard, preview_copy, original_hash
    )
    readiness = build_readiness(validation, c_ready)

    write_csv(plan_dir / "VIA_v0116D_DashboardInsertZoneMatrix.csv", zones)
    write_csv(plan_dir / "VIA_v0116D_DashboardIntegrationPatchPlan.csv", patch_plan)
    write_csv(plan_dir / "VIA_v0116D_PatchOperationMatrix.csv", ops)
    write_csv(plan_dir / "VIA_v0116D_RiskGuardMatrix.csv", guards)
    write_csv(plan_dir / "VIA_v0116D_RollbackPlanMatrix.csv", rollback)
    write_csv(plan_dir / "VIA_v0116D_QuantityValidationMatrix.csv", validation)
    write_csv(output / "VIA_v0116D_ReadinessGate.csv", readiness)

    write_json(plan_dir / "VIA_v0116D_DashboardInsertZoneMatrix.json", zones)
    write_json(plan_dir / "VIA_v0116D_DashboardIntegrationPatchPlan.json", patch_plan)
    write_json(plan_dir / "VIA_v0116D_PatchOperationMatrix.json", ops)
    write_json(plan_dir / "VIA_v0116D_RiskGuardMatrix.json", guards)
    write_json(plan_dir / "VIA_v0116D_RollbackPlanMatrix.json", rollback)
    write_json(plan_dir / "VIA_v0116D_QuantityValidationMatrix.json", validation)
    write_json(output / "VIA_v0116D_ReadinessGate.json", readiness)

    report_path = report / "VIA_v0116D_DashboardIntegrationPatchPlan_Report.html"
    payload = {
        "readiness": readiness,
        "validation": validation,
        "zones": zones,
        "plan": patch_plan,
        "ops": ops,
        "guards": guards,
        "rollback": rollback,
        "original_dashboard": str(original_dashboard),
        "preview_copy": str(preview_copy)
    }
    write_report(report_path, payload)

    final_manifest = {
        "schema_version": "VIA_v0116D_DashboardIntegrationPatchPlanOnly",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "gate": readiness[0]["def_gate_status"],
        "source_run": str(source_run),
        "run_dir": str(run_dir),
        "original_dashboard": str(original_dashboard),
        "original_dashboard_sha256": original_hash,
        "preview_copy": str(preview_copy),
        "report": str(report_path),
        "outputs": {
            "readiness": str(output / "VIA_v0116D_ReadinessGate.csv"),
            "insert_zones": str(plan_dir / "VIA_v0116D_DashboardInsertZoneMatrix.csv"),
            "patch_plan": str(plan_dir / "VIA_v0116D_DashboardIntegrationPatchPlan.csv"),
            "patch_ops": str(plan_dir / "VIA_v0116D_PatchOperationMatrix.csv"),
            "risk_guards": str(plan_dir / "VIA_v0116D_RiskGuardMatrix.csv"),
            "rollback": str(plan_dir / "VIA_v0116D_RollbackPlanMatrix.csv"),
            "validation": str(plan_dir / "VIA_v0116D_QuantityValidationMatrix.csv")
        },
        "policy": {
            "patch_plan_only": True,
            "original_dashboard_writeback": False,
            "source_mutation": False,
            "canonical_merge": False,
            "db_write": False,
            "apply_enabled": False,
            "requires_operator_approval_before_future_apply": True
        }
    }
    write_json(output / "VIA_v0116D_DashboardIntegrationPatchPlan_Manifest.json", final_manifest)

    print("")
    print("=" * 80)
    print("def VIA v0116D Dashboard Integration Patch Plan COMPLETE")
    print("=" * 80)
    print(f"Gate        : {readiness[0]['def_gate_status']}")
    print(f"Input Rows  : {readiness[0]['def_input_rows']}")
    print(f"Green       : {readiness[0]['def_green_ledger_rows']}")
    print(f"Red         : {readiness[0]['def_red_evidence_rows']}")
    print(f"Yellow      : {readiness[0]['def_yellow_confirmation_rows']}")
    print(f"PatchPlan   : {readiness[0]['def_patch_plan_rows']}")
    print(f"Fail        : {readiness[0]['def_validation_fail']}")
    print(f"Original    : {original_dashboard}")
    print(f"PreviewCopy : {preview_copy}")
    print(f"Report      : {report_path}")
    print("[SAFE] Patch plan only. No original dashboard writeback. No apply. No DB write.")


if __name__ == "__main__":
    main()
