from __future__ import annotations

"""Atomic dual-format output and append-only run identity for VIA v0.5."""

# =============================================================================
# def 00 PARAMETERS
# =============================================================================

import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import Mapping

import pandas as pd


ENGINE_ID = "VIA_APPEND_ONLY_IO_V0500"
ENGINE_VERSION = "0.5.0"
CSV_ENCODING = "utf-8-sig"
CSV_DATE_FORMAT = "%Y/%m/%d"
PARQUET_COMPRESSION = "zstd"


def def_frame_hash(frame: pd.DataFrame) -> str:
    normalized = frame.copy()
    normalized = normalized.reindex(sorted(normalized.columns), axis=1)
    normalized = normalized.sort_values(list(normalized.columns), kind="stable", na_position="last") if len(normalized.columns) else normalized
    payload = normalized.to_csv(index=False, date_format="%Y-%m-%dT%H:%M:%S", lineterminator="\n")
    return hashlib.sha256(payload.encode("utf-8")).hexdigest().upper()


def def_run_identity(tables: Mapping[str, pd.DataFrame], as_of: str | pd.Timestamp) -> dict[str, object]:
    table_hashes = {name: def_frame_hash(frame) for name, frame in sorted(tables.items())}
    canonical = json.dumps(
        {"AsOf": pd.Timestamp(as_of).isoformat(), "Tables": table_hashes},
        sort_keys=True,
        separators=(",", ":"),
    )
    run_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest().upper()
    return {
        "AsOf": pd.Timestamp(as_of).strftime("%Y-%m-%d"),
        "RunHash": run_hash,
        "TableHashes": table_hashes,
    }


def def_hash_state(current_hash: str, original_hash: str, proposed_hash: str) -> str:
    """LL-style idempotent state machine: original→apply, proposed→skip, other→fail."""

    current = str(current_hash).strip().upper()
    original = str(original_hash).strip().upper()
    proposed = str(proposed_hash).strip().upper()
    if current == original:
        return "APPLY"
    if current == proposed:
        return "SKIP_ALREADY_APPLIED"
    return "FAIL_UNEXPECTED_HASH"


def def_require_parquet_engine() -> None:
    try:
        pd.io.parquet.get_engine("auto")
    except Exception as exc:
        raise RuntimeError(
            "Parquet engine unavailable; install pyarrow. CSV-only output is prohibited by the v0.5 dual-format contract."
        ) from exc


def def_atomic_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding=CSV_ENCODING, newline="", delete=False, dir=path.parent) as stream:
        temporary = Path(stream.name)
        frame.to_csv(stream, index=False, date_format=CSV_DATE_FORMAT)
    os.replace(temporary, path)


def def_atomic_parquet(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(delete=False, dir=path.parent, suffix=".parquet") as stream:
        temporary = Path(stream.name)
    try:
        frame.to_parquet(temporary, index=False, compression=PARQUET_COMPRESSION)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def def_write_dual_table(frame: pd.DataFrame, output_stem: Path) -> tuple[Path, Path]:
    """Write ``name.csv`` and ``name.parquet``; no hidden version suffix."""

    def_require_parquet_engine()
    csv_path = output_stem.with_suffix(".csv")
    parquet_path = output_stem.with_suffix(".parquet")
    def_atomic_parquet(frame, parquet_path)
    def_atomic_csv(frame, csv_path)
    return csv_path, parquet_path


def def_append_only_run_directory(
    output_root: Path,
    identity: Mapping[str, object],
) -> tuple[Path, str]:
    as_of = str(identity["AsOf"]).replace("-", "")
    run_hash = str(identity["RunHash"]).upper()
    run_dir = output_root / f"RUN_{as_of}_{run_hash[:12]}"
    manifest = run_dir / "manifest.json"
    if not run_dir.exists():
        return run_dir, "CREATE_REQUIRED"
    if not manifest.exists():
        raise RuntimeError(f"append-only run directory exists without manifest: {run_dir}")
    existing = json.loads(manifest.read_text(encoding="utf-8"))
    if str(existing.get("RunHash", "")).upper() == run_hash:
        return run_dir, "SKIP_IDENTICAL_RUN"
    raise RuntimeError(f"append-only run hash conflict: {run_dir}")


def def_write_run(
    tables: Mapping[str, pd.DataFrame],
    output_root: Path,
    as_of: str | pd.Timestamp,
) -> dict[str, object]:
    """Persist an immutable run.  An identical run is idempotently skipped."""

    # Fail before reserving a permanent run name.  A missing parquet engine or
    # a mid-write exception must never strand an unretryable RUN directory.
    def_require_parquet_engine()
    identity = def_run_identity(tables, as_of)
    output_root.mkdir(parents=True, exist_ok=True)
    run_dir, status = def_append_only_run_directory(output_root, identity)
    if status == "SKIP_IDENTICAL_RUN":
        return {**identity, "Status": status, "RunDirectory": str(run_dir)}
    staging = Path(
        tempfile.mkdtemp(prefix=f".{run_dir.name}.staging-", dir=output_root)
    )
    try:
        files: dict[str, dict[str, str]] = {}
        for name, frame in sorted(tables.items()):
            csv_path, parquet_path = def_write_dual_table(frame, staging / name)
            files[name] = {"CSV": csv_path.name, "Parquet": parquet_path.name}
        manifest = {**identity, "Status": "COMPLETED", "Files": files}
        manifest_path = staging / "manifest.json"
        temporary = manifest_path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        os.replace(temporary, manifest_path)
        os.replace(staging, run_dir)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return {**manifest, "RunDirectory": str(run_dir)}
