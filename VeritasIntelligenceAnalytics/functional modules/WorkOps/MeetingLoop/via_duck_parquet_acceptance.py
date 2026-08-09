#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

# =============================================================================
# def 00_PARAMETERS
# =============================================================================

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ENGINE = BASE_DIR / "via_meetingloop_engine.py"
SAMPLE = BASE_DIR / "sample_meeting.txt"
DATA_DIR = BASE_DIR / "data"
SSOT_DIR = BASE_DIR / "ssot"
REPORT_PATH = BASE_DIR / "DATA_ENV_ACCEPTANCE_REPORT.json"
DUCKDB_PATH = SSOT_DIR / "via_meetingloop_v005.duckdb"
PARQUET_ROOT = DATA_DIR / "acceptance_v005"
UX_PAYLOAD = BASE_DIR / "UX_DUCKDB_PAYLOAD.json"

# =============================================================================
# def 01_IMPORTS
# =============================================================================

import argparse
import csv
import datetime as dt
import hashlib
import importlib.metadata
import json
import re
import shutil
import subprocess
import sys
from typing import Any

# =============================================================================
# def 02_FOUNDATION
# =============================================================================

def def_now_iso() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")

def def_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except Exception:
        return "NOT_INSTALLED"

def def_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def def_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

def def_read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))

def def_normalize_action_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    result = []
    for row in rows:
        due_raw = str(row.get("original_due_date", "")).strip()
        due_value = None
        for fmt in ("%Y/%m/%d", "%Y-%m-%d"):
            try:
                due_value = dt.datetime.strptime(due_raw[:10], fmt).date()
                break
            except Exception:
                pass
        progress = row.get("progress_percent")
        try:
            progress_value = int(progress) if progress not in ("", None, "None") else None
        except Exception:
            progress_value = None
        source_ids = row.get("source_segment_ids", "")
        if source_ids.startswith("["):
            try:
                source_ids_value = json.loads(source_ids.replace("'", '"'))
            except Exception:
                source_ids_value = [source_ids]
        else:
            source_ids_value = [x for x in source_ids.split("|") if x]
        result.append({
            "meeting_id": row["meeting_id"],
            "action_id": row["action_id"],
            "action_item": row["action_item"],
            "primary_owner": row.get("primary_owner", ""),
            "status": row.get("status", ""),
            "progress_percent": progress_value,
            "original_due_date": due_value,
            "source_segment_ids": source_ids_value
        })
    return result

# =============================================================================
# def 03_ENGINE_REAL_OUTPUT
# =============================================================================

def def_run_real_engine() -> tuple[Path, dict[str, Any]]:
    if not ENGINE.exists():
        raise FileNotFoundError(f"Core engine missing: {ENGINE}")
    if not SAMPLE.exists():
        raise FileNotFoundError(f"Sample transcript missing: {SAMPLE}")
    result = subprocess.run(
        [sys.executable, str(ENGINE), "process", "--source", str(SAMPLE)],
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        timeout=180
    )
    if result.returncode != 0:
        raise RuntimeError("Core engine process failed:\n" + result.stdout + "\n" + result.stderr)
    match = re.search(r"^def RunDir\s+:\s*(.+)$", result.stdout, re.MULTILINE)
    if not match:
        raise RuntimeError("RunDir not found in engine output")
    run_dir = Path(match.group(1).strip())
    manifest_path = run_dir / "11_run_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    return run_dir, manifest

# =============================================================================
# def 04_ACCEPTANCE
# =============================================================================

def def_run_acceptance() -> dict[str, Any]:
    report: dict[str, Any] = {
        "gate": "DATA_ENV_REJECTED",
        "generated_at": def_now_iso(),
        "python": sys.version,
        "versions": {
            "duckdb": def_version("duckdb"),
            "pyarrow": def_version("pyarrow")
        },
        "tests": {},
        "artifacts": {},
        "errors": []
    }

    try:
        import duckdb
        import pyarrow as pa
        import pyarrow.parquet as pq
    except Exception as exc:
        report["errors"].append(f"IMPORT_FAILURE: {type(exc).__name__}: {exc}")
        def_write_json(REPORT_PATH, report)
        return report

    try:
        if PARQUET_ROOT.exists():
            shutil.rmtree(PARQUET_ROOT)
        PARQUET_ROOT.mkdir(parents=True, exist_ok=True)
        SSOT_DIR.mkdir(parents=True, exist_ok=True)

        # ---------------------------------------------------------------------
        # Synthetic explicit-schema contract test
        # ---------------------------------------------------------------------
        transcript_schema = pa.schema([
            ("meeting_id", pa.string()),
            ("segment_id", pa.string()),
            ("sequence_no", pa.int32()),
            ("speaker_name", pa.string()),
            ("approved_text", pa.string()),
            ("review_status", pa.string()),
            ("source_hash", pa.string())
        ])
        action_schema = pa.schema([
            ("meeting_id", pa.string()),
            ("action_id", pa.string()),
            ("action_item", pa.string()),
            ("primary_owner", pa.string()),
            ("status", pa.string()),
            ("progress_percent", pa.int32()),
            ("original_due_date", pa.date32()),
            ("source_segment_ids", pa.list_(pa.string()))
        ])

        synthetic_transcript = [{
            "meeting_id": "MTG-TEST-20260801-001",
            "segment_id": "SEG-00001",
            "sequence_no": 1,
            "speaker_name": "Tony Huang",
            "approved_text": "Synthetic schema acceptance.",
            "review_status": "CONFIRMED",
            "source_hash": hashlib.sha256(b"synthetic").hexdigest()
        }]
        synthetic_action = [{
            "meeting_id": "MTG-TEST-20260801-001",
            "action_id": "TST-ACT-20260801-001",
            "action_item": "Synthetic action acceptance",
            "primary_owner": "Tony Huang",
            "status": "IN_PROGRESS",
            "progress_percent": 25,
            "original_due_date": dt.date(2026, 8, 4),
            "source_segment_ids": ["SEG-00001"]
        }]

        synthetic_transcript_path = PARQUET_ROOT / "synthetic" / "transcript.parquet"
        synthetic_action_path = PARQUET_ROOT / "synthetic" / "actions.parquet"
        synthetic_transcript_path.parent.mkdir(parents=True, exist_ok=True)
        pq.write_table(pa.Table.from_pylist(synthetic_transcript, schema=transcript_schema),
                       synthetic_transcript_path, compression="zstd")
        pq.write_table(pa.Table.from_pylist(synthetic_action, schema=action_schema),
                       synthetic_action_path, compression="zstd")
        transcript_read = pq.read_table(synthetic_transcript_path)
        action_read = pq.read_table(synthetic_action_path)
        report["tests"]["synthetic_schema_roundtrip"] = (
            transcript_read.schema.equals(transcript_schema)
            and action_read.schema.equals(action_schema)
            and transcript_read.num_rows == 1
            and action_read.num_rows == 1
        )

        # ---------------------------------------------------------------------
        # Real core-engine-output acceptance
        # ---------------------------------------------------------------------
        run_dir, manifest = def_run_real_engine()
        transcript_csv = run_dir / "01_transcript_segments.csv"
        action_csv = run_dir / "06_actions.csv"
        workbench = Path(manifest["workbench"])
        if not transcript_csv.exists() or not action_csv.exists() or not workbench.exists():
            raise RuntimeError("Real engine outputs are incomplete")

        raw_transcript_rows = def_read_csv(transcript_csv)
        raw_action_rows = def_read_csv(action_csv)
        transcript_rows = [{
            "meeting_id": row["meeting_id"],
            "segment_id": row["segment_id"],
            "sequence_no": int(row["sequence_no"]),
            "speaker_name": row.get("speaker_name", ""),
            "approved_text": row.get("approved_text", ""),
            "review_status": row.get("review_status", ""),
            "source_hash": row.get("source_hash", "")
        } for row in raw_transcript_rows]
        action_rows = def_normalize_action_rows(raw_action_rows)

        real_transcript_path = (
            PARQUET_ROOT / "real" / "silver" / "transcript_segments"
            / f"meeting_id={manifest['meeting_id']}" / "part-00000.parquet"
        )
        real_action_path = (
            PARQUET_ROOT / "real" / "gold" / "actions"
            / f"meeting_id={manifest['meeting_id']}" / "part-00000.parquet"
        )
        real_transcript_path.parent.mkdir(parents=True, exist_ok=True)
        real_action_path.parent.mkdir(parents=True, exist_ok=True)

        pq.write_table(
            pa.Table.from_pylist(transcript_rows, schema=transcript_schema),
            real_transcript_path,
            compression="zstd"
        )
        pq.write_table(
            pa.Table.from_pylist(action_rows, schema=action_schema),
            real_action_path,
            compression="zstd"
        )

        real_transcript_read = pq.read_table(real_transcript_path)
        real_action_read = pq.read_table(real_action_path)
        report["tests"]["real_engine_parquet_roundtrip"] = (
            real_transcript_read.num_rows == manifest["segment_count"]
            and real_action_read.num_rows == manifest["action_count"]
            and real_transcript_read.schema.equals(transcript_schema)
            and real_action_read.schema.equals(action_schema)
        )

        # ---------------------------------------------------------------------
        # Persistent DuckDB + views + SQL
        # ---------------------------------------------------------------------
        con = duckdb.connect(str(DUCKDB_PATH))
        try:
            transcript_pattern = str(
                PARQUET_ROOT / "real" / "silver" / "transcript_segments" / "**" / "*.parquet"
            ).replace("\\", "/")
            action_pattern = str(
                PARQUET_ROOT / "real" / "gold" / "actions" / "**" / "*.parquet"
            ).replace("\\", "/")

            con.execute(
                f"""CREATE OR REPLACE VIEW vw_transcript_segments AS
                    SELECT * FROM read_parquet(
                        '{transcript_pattern}',
                        hive_partitioning=true,
                        union_by_name=true
                    )"""
            )
            con.execute(
                f"""CREATE OR REPLACE VIEW vw_actions AS
                    SELECT * FROM read_parquet(
                        '{action_pattern}',
                        hive_partitioning=true,
                        union_by_name=true
                    )"""
            )

            transcript_count = int(con.execute(
                "SELECT count(*) FROM vw_transcript_segments"
            ).fetchone()[0])
            action_count = int(con.execute(
                "SELECT count(*) FROM vw_actions"
            ).fetchone()[0])
            open_actions = con.execute(
                """SELECT action_id, primary_owner, status, progress_percent
                   FROM vw_actions
                   WHERE status NOT IN ('COMPLETED', 'CANCELLED')
                   ORDER BY action_id"""
            ).fetchall()

            report["tests"]["duckdb_persistent_views"] = (
                transcript_count == manifest["segment_count"]
                and action_count == manifest["action_count"]
            )
            report["tests"]["duckdb_open_action_query"] = len(open_actions) == action_count

            # -----------------------------------------------------------------
            # UX data roundtrip built from actual DuckDB query
            # -----------------------------------------------------------------
            ux_payload = {
                "meeting_id": manifest["meeting_id"],
                "source_run_dir": str(run_dir),
                "source_workbench": str(workbench),
                "kpi": {
                    "transcript_segments": transcript_count,
                    "actions": action_count,
                    "open_actions": len(open_actions),
                    "data_gate": "DATA_ENV_ACCEPTED"
                },
                "open_actions": [{
                    "action_id": row[0],
                    "primary_owner": row[1],
                    "status": row[2],
                    "progress_percent": row[3]
                } for row in open_actions]
            }
            def_write_json(UX_PAYLOAD, ux_payload)
            read_back = json.loads(UX_PAYLOAD.read_text(encoding="utf-8"))
            report["tests"]["ux_payload_actual_data_roundtrip"] = (
                read_back["meeting_id"] == manifest["meeting_id"]
                and read_back["kpi"]["transcript_segments"] == manifest["segment_count"]
                and read_back["kpi"]["actions"] == manifest["action_count"]
                and Path(read_back["source_workbench"]).exists()
            )
        finally:
            con.close()

        report["tests"]["core_engine_self_test"] = manifest["gate"] == "REVIEW_REQUIRED"
        report["tests"]["source_workbench_exists"] = workbench.exists()

        report["artifacts"] = {
            "real_run_dir": str(run_dir),
            "real_workbench": str(workbench),
            "synthetic_transcript_parquet": str(synthetic_transcript_path),
            "synthetic_action_parquet": str(synthetic_action_path),
            "real_transcript_parquet": str(real_transcript_path),
            "real_transcript_sha256": def_sha256(real_transcript_path),
            "real_action_parquet": str(real_action_path),
            "real_action_sha256": def_sha256(real_action_path),
            "duckdb": str(DUCKDB_PATH),
            "ux_payload": str(UX_PAYLOAD)
        }

        report["gate"] = (
            "DATA_ENV_ACCEPTED"
            if report["tests"] and all(report["tests"].values())
            else "DATA_ENV_REJECTED"
        )
    except Exception as exc:
        report["errors"].append(f"ACCEPTANCE_FAILURE: {type(exc).__name__}: {exc}")
        report["gate"] = "DATA_ENV_REJECTED"

    def_write_json(REPORT_PATH, report)
    return report

# =============================================================================
# def 05_CLI
# =============================================================================

def def_main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    report = def_run_acceptance()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.strict and report["gate"] != "DATA_ENV_ACCEPTED":
        return 3
    return 0

if __name__ == "__main__":
    raise SystemExit(def_main())
