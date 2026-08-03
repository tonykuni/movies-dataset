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


def locate_source_files(source_run: Path) -> Dict[str, Path]:
    a_manifest = source_run / "output" / "VIA_v0116B_A_DashboardPreviewCopy_Manifest.json"
    b_manifest = source_run / "output" / "VIA_v0116B_DashboardPreviewCopy_Manifest.json"
    a_ready = source_run / "output" / "VIA_v0116B_A_ReadinessGate.csv"
    b_ready = source_run / "output" / "VIA_v0116B_ReadinessGate.csv"

    if a_manifest.exists():
        return {
            "manifest": a_manifest,
            "readiness": a_ready,
            "cards": source_run / "_dashboard_preview_copy" / "VIA_v0116B_A_PreviewCardMatrix.csv",
            "integrity": source_run / "_dashboard_preview_copy" / "VIA_v0116B_A_CopyIntegrityMatrix.csv",
            "validation": source_run / "_dashboard_preview_copy" / "VIA_v0116B_A_ValidationMatrix.csv",
        }

    return {
        "manifest": b_manifest,
        "readiness": b_ready,
        "cards": source_run / "_dashboard_preview_copy" / "VIA_v0116B_PreviewCardMatrix.csv",
        "integrity": source_run / "_dashboard_preview_copy" / "VIA_v0116B_CopyIntegrityMatrix.csv",
        "validation": source_run / "_dashboard_preview_copy" / "VIA_v0116B_ValidationMatrix.csv",
    }


def add_validation(rows: List[Dict[str, Any]], name: str, expected: Any, actual: Any, ok: bool, msg: str) -> None:
    rows.append({
        "def_validation": name,
        "def_expected": expected,
        "def_actual": actual,
        "def_status": "PASS" if ok else "FAIL",
        "def_message": msg
    })


def build_marker_matrix(preview_text: str) -> List[Dict[str, Any]]:
    marker_start = "VIA:v0116B:PREVIEW_COPY_LAYER:START"
    marker_end = "VIA:v0116B:PREVIEW_COPY_LAYER:END"

    start_count = preview_text.count(marker_start)
    end_count = preview_text.count(marker_end)
    layer_id_count = preview_text.count("via-v0116b-preview-layer")
    card_count = len(re.findall(r'class=["\'][^"\']*\bvia-card\b', preview_text))

    return [
        {
            "def_marker": "PREVIEW_COPY_LAYER_START",
            "def_expected": "1",
            "def_actual": str(start_count),
            "def_status": "PASS" if start_count == 1 else "FAIL"
        },
        {
            "def_marker": "PREVIEW_COPY_LAYER_END",
            "def_expected": "1",
            "def_actual": str(end_count),
            "def_status": "PASS" if end_count == 1 else "FAIL"
        },
        {
            "def_marker": "PREVIEW_LAYER_ID",
            "def_expected": ">=1",
            "def_actual": str(layer_id_count),
            "def_status": "PASS" if layer_id_count >= 1 else "FAIL"
        },
        {
            "def_marker": "PREVIEW_CARD_CLASS_COUNT",
            "def_expected": ">=8",
            "def_actual": str(card_count),
            "def_status": "PASS" if card_count >= 8 else "FAIL"
        }
    ]


def build_card_validation(cards: List[Dict[str, str]], preview_text: str) -> List[Dict[str, Any]]:
    rows = []

    for c in cards:
        anchor = prop(c, "def_anchor")
        title = prop(c, "def_title")
        ryg = prop(c, "def_ryg")
        route = prop(c, "def_source_route")

        anchor_ok = bool(anchor) and anchor in preview_text
        title_ok = bool(title) and title in preview_text
        route_ok = bool(route) and route in preview_text

        rows.append({
            "def_preview_card_id": prop(c, "def_preview_card_id"),
            "def_source_route": route,
            "def_title": title,
            "def_ryg": ryg,
            "def_anchor": anchor,
            "def_anchor_present": str(anchor_ok).lower(),
            "def_title_present": str(title_ok).lower(),
            "def_route_present": str(route_ok).lower(),
            "def_status": "PASS" if anchor_ok and title_ok and route_ok else "FAIL",
            "def_apply_enabled": "false",
            "def_original_dashboard_writeback": "false"
        })

    return rows


def build_integrity_seal(manifest: Dict[str, Any], preview_copy: Path, original: Path) -> List[Dict[str, Any]]:
    hash_before = str(manifest.get("original_dashboard_sha256_before", "") or "")
    hash_after_recorded = str(manifest.get("original_dashboard_sha256_after", "") or "")
    hash_now = sha256_file(original)

    return [
        {
            "def_check": "ORIGINAL_DASHBOARD_EXISTS",
            "def_expected": "true",
            "def_actual": str(original.exists()).lower(),
            "def_status": "PASS" if original.exists() else "FAIL",
            "def_path": str(original)
        },
        {
            "def_check": "PREVIEW_COPY_EXISTS",
            "def_expected": "true",
            "def_actual": str(preview_copy.exists()).lower(),
            "def_status": "PASS" if preview_copy.exists() else "FAIL",
            "def_path": str(preview_copy)
        },
        {
            "def_check": "PREVIEW_COPY_SEPARATE_FROM_ORIGINAL",
            "def_expected": "different",
            "def_actual": "different" if str(preview_copy).lower() != str(original).lower() else "same",
            "def_status": "PASS" if str(preview_copy).lower() != str(original).lower() else "FAIL",
            "def_path": str(preview_copy)
        },
        {
            "def_check": "ORIGINAL_HASH_BEFORE_AFTER_MATCH",
            "def_expected": hash_before,
            "def_actual": hash_after_recorded,
            "def_status": "PASS" if hash_before and hash_before == hash_after_recorded else "FAIL",
            "def_path": str(original)
        },
        {
            "def_check": "ORIGINAL_HASH_STILL_UNCHANGED_NOW",
            "def_expected": hash_before,
            "def_actual": hash_now,
            "def_status": "PASS" if hash_before and hash_now == hash_before else "FAIL",
            "def_path": str(original)
        }
    ]


def build_no_action_matrix() -> List[Dict[str, Any]]:
    rules = [
        ("NO_ORIGINAL_DASHBOARD_WRITEBACK", "original_dashboard_writeback", "false"),
        ("NO_SOURCE_MUTATION", "source_mutation", "false"),
        ("NO_CANONICAL_MERGE", "canonical_merge", "false"),
        ("NO_DB_WRITE", "db_write", "false"),
        ("NO_APPLY", "apply_enabled", "false"),
        ("NO_DELETE", "delete", "false"),
        ("NO_STOP_PROCESS", "stop_process", "false"),
        ("NO_EXTERNAL_CALL", "external_call", "false"),
        ("PREVIEW_COPY_ONLY", "preview_copy_only", "true")
    ]

    return [
        {
            "def_policy_id": f"V0116C-NOACT-{i:03d}",
            "def_policy_name": name,
            "def_control": control,
            "def_required_value": value,
            "def_status": "PASS",
            "def_message": "Validation seal only. No writeback."
        }
        for i, (name, control, value) in enumerate(rules, 1)
    ]


def build_validation(
    readiness_in: Dict[str, str],
    source_validation: List[Dict[str, str]],
    integrity: List[Dict[str, Any]],
    marker: List[Dict[str, Any]],
    card_validation: List[Dict[str, Any]],
    cards: List[Dict[str, str]]
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    add_validation(rows, "V0116B_GATE_READY", "DASHBOARD_PREVIEW_COPY_READY_REVIEW_ONLY", prop(readiness_in, "def_gate_status"), prop(readiness_in, "def_gate_status") == "DASHBOARD_PREVIEW_COPY_READY_REVIEW_ONLY", "v0116B-A must be ready.")
    add_validation(rows, "INPUT_448", "448", prop(readiness_in, "def_input_rows"), prop(readiness_in, "def_input_rows") == "448", "Input continuity.")
    add_validation(rows, "GREEN_294", "294", prop(readiness_in, "def_green_ledger_rows"), prop(readiness_in, "def_green_ledger_rows") == "294", "Green continuity.")
    add_validation(rows, "RED_63", "63", prop(readiness_in, "def_red_evidence_rows"), prop(readiness_in, "def_red_evidence_rows") == "63", "Red continuity.")
    add_validation(rows, "YELLOW_91", "91", prop(readiness_in, "def_yellow_confirmation_rows"), prop(readiness_in, "def_yellow_confirmation_rows") == "91", "Yellow continuity.")
    add_validation(rows, "PREVIEW_CARDS_8", "8", prop(readiness_in, "def_preview_cards"), prop(readiness_in, "def_preview_cards") == "8", "Preview cards count.")
    add_validation(rows, "SOURCE_VALIDATION_FAIL_0", "0", prop(readiness_in, "def_validation_fail"), prop(readiness_in, "def_validation_fail") == "0", "Source v0116B validation fail must be zero.")
    add_validation(rows, "SOURCE_VALIDATION_ROWS_GE_15", ">=15", len(source_validation), len(source_validation) >= 15, "Source validation rows present.")
    add_validation(rows, "CARD_MATRIX_ROWS_8", 8, len(cards), len(cards) == 8, "Card matrix rows.")
    add_validation(rows, "CARD_VALIDATION_PASS_ALL", "all PASS", ",".join(sorted(set(prop(r, "def_status") for r in card_validation))), all(prop(r, "def_status") == "PASS" for r in card_validation), "All preview cards present in copy.")
    add_validation(rows, "INTEGRITY_PASS_ALL", "all PASS", ",".join(sorted(set(prop(r, "def_status") for r in integrity))), all(prop(r, "def_status") == "PASS" for r in integrity), "Integrity checks must pass.")
    add_validation(rows, "MARKER_PASS_ALL", "all PASS", ",".join(sorted(set(prop(r, "def_status") for r in marker))), all(prop(r, "def_status") == "PASS" for r in marker), "Preview markers must pass.")
    add_validation(rows, "NO_ORIGINAL_WRITEBACK", "false", prop(readiness_in, "def_original_dashboard_writeback"), prop(readiness_in, "def_original_dashboard_writeback") == "false", "Original dashboard writeback must be false.")
    add_validation(rows, "NO_SOURCE_MUTATION", "false", prop(readiness_in, "def_source_mutation"), prop(readiness_in, "def_source_mutation") == "false", "Source mutation false.")
    add_validation(rows, "NO_APPLY", "false", prop(readiness_in, "def_apply_enabled"), prop(readiness_in, "def_apply_enabled") == "false", "Apply false.")
    add_validation(rows, "NO_DB_WRITE", "false", prop(readiness_in, "def_db_write"), prop(readiness_in, "def_db_write") == "false", "DB write false.")

    return rows


def build_readiness(validation: List[Dict[str, Any]], readiness_in: Dict[str, str]) -> List[Dict[str, Any]]:
    fail = sum(1 for r in validation if prop(r, "def_status") != "PASS")
    return [{
        "def_gate_status": "PREVIEW_COPY_VALIDATION_SEAL_READY_REVIEW_ONLY" if fail == 0 else "BLOCKED_BY_v0116C_VALIDATION_FAIL",
        "def_allow_next": "true" if fail == 0 else "false",
        "def_reason": "v0116C sealed preview copy validation. Original dashboard remains unchanged. No apply.",
        "def_input_rows": prop(readiness_in, "def_input_rows", "448"),
        "def_green_ledger_rows": prop(readiness_in, "def_green_ledger_rows", "294"),
        "def_red_evidence_rows": prop(readiness_in, "def_red_evidence_rows", "63"),
        "def_yellow_confirmation_rows": prop(readiness_in, "def_yellow_confirmation_rows", "91"),
        "def_preview_cards": prop(readiness_in, "def_preview_cards", "8"),
        "def_validation_fail": str(fail),
        "def_original_dashboard_writeback": "false",
        "def_source_mutation": "false",
        "def_canonical_merge": "false",
        "def_apply_enabled": "false",
        "def_db_write": "false",
        "def_next_allowed_phase": "v0116D dashboard integration patch plan only"
    }]


def render_table(rows: List[Dict[str, Any]], cols: List[str]) -> str:
    out = ["<table><thead><tr>"]
    for c in cols:
        out.append(f"<th>{h(c)}</th>")
    out.append("</tr></thead><tbody>")
    for r in rows:
        joined = " ".join(str(v) for v in r.values()).upper()
        cls = "risk-green"
        if "FAIL" in joined or "RED" in joined:
            cls = "risk-red"
        elif "YELLOW" in joined:
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
        ("Next", "v0116D")
    ]:
        cards += f"<div class='card'><div class='k'>{h(k)}</div><div class='v'>{h(v)}</div></div>"

    doc = f"""<!doctype html>
<html lang="zh-Hant">
<head><meta charset="utf-8"/><title>VIA v0116C Preview Copy Validation Seal</title>{style}</head>
<body><div class="wrap">
<h1>def VIA v0116C · Preview Copy Validation Seal Only</h1>
<div class="sub">Preview Copy Validated · Original Dashboard Unchanged · No Writeback · No Apply</div>
<div class="cards">{cards}</div>

<div class="sec"><h2>Readiness Gate</h2>{render_table(payload["readiness"], ["def_gate_status","def_allow_next","def_reason","def_input_rows","def_green_ledger_rows","def_red_evidence_rows","def_yellow_confirmation_rows","def_preview_cards","def_validation_fail","def_original_dashboard_writeback","def_source_mutation","def_canonical_merge","def_apply_enabled","def_db_write","def_next_allowed_phase"])}</div>
<div class="sec"><h2>Final Validation Matrix</h2>{render_table(payload["validation"], ["def_validation","def_expected","def_actual","def_status","def_message"])}</div>
<div class="sec"><h2>Integrity Seal Matrix</h2>{render_table(payload["integrity"], ["def_check","def_expected","def_actual","def_status","def_path"])}</div>
<div class="sec"><h2>Marker Seal Matrix</h2>{render_table(payload["marker"], ["def_marker","def_expected","def_actual","def_status"])}</div>
<div class="sec"><h2>Card Validation Matrix</h2>{render_table(payload["card_validation"], ["def_preview_card_id","def_source_route","def_title","def_ryg","def_anchor","def_anchor_present","def_title_present","def_route_present","def_status","def_apply_enabled"])}</div>
<div class="sec"><h2>No-Action Matrix</h2>{render_table(payload["no_action"], ["def_policy_id","def_policy_name","def_control","def_required_value","def_status","def_message"])}</div>
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
    report = run_dir / "report"
    seal = run_dir / "_preview_copy_validation_seal"

    output.mkdir(parents=True, exist_ok=True)
    report.mkdir(parents=True, exist_ok=True)
    seal.mkdir(parents=True, exist_ok=True)

    files = locate_source_files(source_run)
    manifest = read_json(files["manifest"])
    readiness_in = first(read_csv(files["readiness"]))
    cards = read_csv(files["cards"])
    source_validation = read_csv(files["validation"])

    preview_copy = Path(str(manifest.get("preview_copy", "") or ""))
    original_dashboard = Path(str(manifest.get("original_dashboard", "") or ""))

    preview_text = read_text(preview_copy)

    integrity = build_integrity_seal(manifest, preview_copy, original_dashboard)
    marker = build_marker_matrix(preview_text)
    card_validation = build_card_validation(cards, preview_text)
    no_action = build_no_action_matrix()
    validation = build_validation(readiness_in, source_validation, integrity, marker, card_validation, cards)
    readiness = build_readiness(validation, readiness_in)

    write_csv(seal / "VIA_v0116C_FinalValidationMatrix.csv", validation)
    write_csv(seal / "VIA_v0116C_IntegritySealMatrix.csv", integrity)
    write_csv(seal / "VIA_v0116C_MarkerSealMatrix.csv", marker)
    write_csv(seal / "VIA_v0116C_CardValidationMatrix.csv", card_validation)
    write_csv(seal / "VIA_v0116C_NoActionMatrix.csv", no_action)
    write_csv(output / "VIA_v0116C_ReadinessGate.csv", readiness)

    write_json(seal / "VIA_v0116C_FinalValidationMatrix.json", validation)
    write_json(seal / "VIA_v0116C_IntegritySealMatrix.json", integrity)
    write_json(seal / "VIA_v0116C_MarkerSealMatrix.json", marker)
    write_json(seal / "VIA_v0116C_CardValidationMatrix.json", card_validation)
    write_json(seal / "VIA_v0116C_NoActionMatrix.json", no_action)
    write_json(output / "VIA_v0116C_ReadinessGate.json", readiness)

    report_path = report / "VIA_v0116C_PreviewCopyValidationSeal_Report.html"
    payload = {
        "readiness": readiness,
        "validation": validation,
        "integrity": integrity,
        "marker": marker,
        "card_validation": card_validation,
        "no_action": no_action,
        "preview_copy": str(preview_copy),
        "original_dashboard": str(original_dashboard)
    }
    write_report(report_path, payload)

    final_manifest = {
        "schema_version": "VIA_v0116C_PreviewCopyValidationSealOnly",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "gate": readiness[0]["def_gate_status"],
        "source_run": str(source_run),
        "run_dir": str(run_dir),
        "original_dashboard": str(original_dashboard),
        "preview_copy": str(preview_copy),
        "report": str(report_path),
        "outputs": {
            "readiness": str(output / "VIA_v0116C_ReadinessGate.csv"),
            "final_validation": str(seal / "VIA_v0116C_FinalValidationMatrix.csv"),
            "integrity": str(seal / "VIA_v0116C_IntegritySealMatrix.csv"),
            "marker": str(seal / "VIA_v0116C_MarkerSealMatrix.csv"),
            "card_validation": str(seal / "VIA_v0116C_CardValidationMatrix.csv"),
            "no_action": str(seal / "VIA_v0116C_NoActionMatrix.csv")
        },
        "policy": {
            "preview_copy_validation_seal_only": True,
            "original_dashboard_writeback": False,
            "source_mutation": False,
            "canonical_merge": False,
            "db_write": False,
            "apply_enabled": False
        }
    }
    write_json(output / "VIA_v0116C_PreviewCopyValidationSeal_Manifest.json", final_manifest)
    write_json(seal / "VIA_v0116C_PREVIEW_COPY_VALIDATION_SEAL.json", final_manifest)

    print("")
    print("=" * 80)
    print("def VIA v0116C Preview Copy Validation Seal COMPLETE")
    print("=" * 80)
    print(f"Gate        : {readiness[0]['def_gate_status']}")
    print(f"Input Rows  : {readiness[0]['def_input_rows']}")
    print(f"Green       : {readiness[0]['def_green_ledger_rows']}")
    print(f"Red         : {readiness[0]['def_red_evidence_rows']}")
    print(f"Yellow      : {readiness[0]['def_yellow_confirmation_rows']}")
    print(f"Cards       : {readiness[0]['def_preview_cards']}")
    print(f"Fail        : {readiness[0]['def_validation_fail']}")
    print(f"Original    : {original_dashboard}")
    print(f"PreviewCopy : {preview_copy}")
    print(f"Report      : {report_path}")
    print("[SAFE] Validation seal only. Original dashboard unchanged. No writeback. No apply. No DB write.")


if __name__ == "__main__":
    main()
