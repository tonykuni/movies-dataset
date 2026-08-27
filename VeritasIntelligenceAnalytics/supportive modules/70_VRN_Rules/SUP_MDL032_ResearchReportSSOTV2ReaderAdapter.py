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
import json
import pathlib
from typing import Any, Iterable


UNRESOLVED_STATE = "UNRESOLVED_EVIDENCE_INSUFFICIENT"
VALID_MODES = ("resolved_only", "include_unresolved", "review_queue")


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl(path: pathlib.Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            value = json.loads(stripped)
            if not isinstance(value, dict):
                raise ValueError(
                    f"JSONL line {line_number} is not an object."
                )
            value["_source_position"] = len(rows) + 1
            rows.append(value)
    return rows


def validate_record(row: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    state = str(row.get("report_date_resolution_state", ""))
    report_date = row.get("report_date_guess")
    candidates = row.get("report_date_candidates")
    evidence_state = row.get("report_date_evidence_state")
    provenance = row.get("report_date_resolution_provenance")

    if not isinstance(candidates, list):
        errors.append("CANDIDATES_NOT_ARRAY")
        candidates = []

    if len(candidates) != len({str(value) for value in candidates}):
        errors.append("CANDIDATES_NOT_UNIQUE")

    if not isinstance(provenance, dict):
        errors.append("PROVENANCE_NOT_OBJECT")

    if not str(evidence_state or "").strip():
        errors.append("EVIDENCE_STATE_MISSING")

    if state == UNRESOLVED_STATE:
        if report_date is not None:
            errors.append("UNRESOLVED_DATE_MUST_BE_NULL")
        if not candidates:
            errors.append("UNRESOLVED_CANDIDATES_REQUIRED")
    else:
        if report_date is None or not str(report_date).strip():
            errors.append("RESOLVED_DATE_REQUIRED")
        elif str(report_date) not in [str(value) for value in candidates]:
            errors.append("RESOLVED_DATE_NOT_IN_CANDIDATES")

    return errors


def select_mode(
    records: list[dict[str, Any]],
    mode: str,
    *,
    sort_by_date: bool = False,
) -> list[dict[str, Any]]:
    if mode not in VALID_MODES:
        raise ValueError(f"Unsupported mode: {mode}")

    if mode == "resolved_only":
        selected = [
            row
            for row in records
            if row.get("report_date_resolution_state")
            != UNRESOLVED_STATE
        ]
    elif mode == "review_queue":
        selected = [
            row
            for row in records
            if row.get("report_date_resolution_state")
            == UNRESOLVED_STATE
        ]
    else:
        selected = list(records)

    if sort_by_date:
        selected = sorted(
            selected,
            key=lambda row: (
                row.get("report_date_guess") is None,
                str(row.get("report_date_guess") or ""),
                int(row.get("_source_position", 0)),
            ),
        )
    else:
        selected = sorted(
            selected,
            key=lambda row: int(row.get("_source_position", 0)),
        )

    return selected


def export_row(row: dict[str, Any]) -> dict[str, Any]:
    output = {
        key: value
        for key, value in row.items()
        if key != "_source_position"
    }
    output["report_date_status"] = str(
        row.get("report_date_resolution_state", "")
    )
    output["report_date_candidates_json"] = json.dumps(
        row.get("report_date_candidates", []),
        ensure_ascii=False,
        separators=(",", ":"),
    )
    output["report_date_is_unresolved"] = (
        row.get("report_date_resolution_state")
        == UNRESOLVED_STATE
    )
    return output


def write_json(path: pathlib.Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


def write_jsonl(
    path: pathlib.Path,
    rows: Iterable[dict[str, Any]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            json.dumps(
                export_row(row),
                ensure_ascii=False,
                separators=(",", ":"),
                default=str,
            )
            for row in rows
        )
        + "\n",
        encoding="utf-8",
    )


def write_csv(
    path: pathlib.Path,
    rows: Iterable[dict[str, Any]],
) -> None:
    row_list = [export_row(row) for row in rows]
    path.parent.mkdir(parents=True, exist_ok=True)

    if not row_list:
        path.write_text("", encoding="utf-8")
        return

    fields: list[str] = []
    seen: set[str] = set()

    for row in row_list:
        for key in row:
            if key not in seen:
                seen.add(key)
                fields.append(key)

    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            extrasaction="ignore",
        )
        writer.writeheader()
        for row in row_list:
            normalized = {
                key: (
                    json.dumps(value, ensure_ascii=False)
                    if isinstance(value, (dict, list))
                    else value
                )
                for key, value in row.items()
            }
            writer.writerow(normalized)


def run_adapter(
    candidate_path: pathlib.Path,
    mode: str,
    *,
    expected_sha256: str = "",
    sort_by_date: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    actual_sha = sha256_file(candidate_path)

    if expected_sha256 and actual_sha != expected_sha256.lower():
        raise ValueError(
            f"Candidate SHA drift: {actual_sha} != {expected_sha256}"
        )

    records = read_jsonl(candidate_path)
    validation_errors: list[dict[str, Any]] = []

    for row in records:
        for error in validate_record(row):
            validation_errors.append(
                {
                    "record_id": row.get("record_id", ""),
                    "error": error,
                }
            )

    if validation_errors:
        raise ValueError(
            "Candidate validation failed: "
            + json.dumps(
                validation_errors[:20],
                ensure_ascii=False,
            )
        )

    selected = select_mode(
        records,
        mode,
        sort_by_date=sort_by_date,
    )
    unresolved = [
        row
        for row in selected
        if row.get("report_date_resolution_state")
        == UNRESOLVED_STATE
    ]
    null_dates = [
        row
        for row in selected
        if row.get("report_date_guess") is None
    ]
    candidate_coercions = [
        row
        for row in selected
        if (
            row.get("report_date_resolution_state")
            == UNRESOLVED_STATE
            and row.get("report_date_guess") is not None
        )
    ]

    summary = {
        "adapter_name": "VRN_RESEARCH_REPORT_SSOT_V2_READER_ADAPTER",
        "mode": mode,
        "candidate_path": str(candidate_path),
        "candidate_sha256": actual_sha,
        "source_record_count": len(records),
        "output_record_count": len(selected),
        "unresolved_output_count": len(unresolved),
        "null_date_output_count": len(null_dates),
        "candidate_coercion_count": len(candidate_coercions),
        "sort_by_date": sort_by_date,
        "source_order_preserved": not sort_by_date,
        "mutation_executed": False,
    }
    return selected, summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--expected-sha256", default="")
    parser.add_argument("--mode", choices=VALID_MODES, required=True)
    parser.add_argument(
        "--format",
        choices=("json", "jsonl", "csv"),
        default="json",
    )
    parser.add_argument("--output", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--sort-by-date", action="store_true")
    arguments = parser.parse_args()

    selected, summary = run_adapter(
        pathlib.Path(arguments.candidate),
        arguments.mode,
        expected_sha256=arguments.expected_sha256,
        sort_by_date=arguments.sort_by_date,
    )
    output_path = pathlib.Path(arguments.output)

    if arguments.format == "json":
        write_json(
            output_path,
            [export_row(row) for row in selected],
        )
    elif arguments.format == "jsonl":
        write_jsonl(output_path, selected)
    else:
        write_csv(output_path, selected)

    write_json(pathlib.Path(arguments.summary), summary)
    print(json.dumps(summary, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
