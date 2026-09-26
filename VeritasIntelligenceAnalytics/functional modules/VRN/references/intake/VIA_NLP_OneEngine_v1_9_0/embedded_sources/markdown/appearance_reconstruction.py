#!/usr/bin/env python3
"""Lossless source-appearance snapshots and guarded restoration."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any


# =============================================================================
# 參數區：原貌保存與還原的單一真實來源。
# =============================================================================

APPEARANCE_SCHEMA_VERSION = "1.3"
DEFAULT_ENCODING = "utf-8"
UTF8_BOM = b"\xef\xbb\xbf"
NEWLINE_PATTERN = re.compile(r"\r\n|\n|\r")
HEADING_PATTERN = re.compile(r"^\s{0,3}#{1,6}(?:\s+|$)")
LIST_PATTERN = re.compile(r"^\s*(?:[-+*]|\d+[.)])\s+")
QUOTE_PATTERN = re.compile(r"^\s*>")
FENCE_PATTERN = re.compile(r"^\s*(?:`{3,}|~{3,})")
HTML_PATTERN = re.compile(r"^\s*</?[A-Za-z][^>]*>")
TABLE_DELIMITER_PATTERN = re.compile(r"^\s*\|?.*:?-{3,}:?.*\|?\s*$")


def def_sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def def_atomic_write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def def_atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    encoded = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode(DEFAULT_ENCODING)
    def_atomic_write_bytes(path, encoded)


def def_split_lines_lossless(text: str) -> list[tuple[str, str]]:
    lines: list[tuple[str, str]] = []
    cursor = 0
    for match in NEWLINE_PATTERN.finditer(text):
        lines.append((text[cursor : match.start()], match.group(0)))
        cursor = match.end()
    if cursor < len(text) or not lines:
        lines.append((text[cursor:], ""))
    return lines


def def_line_role(content: str, in_fence: bool) -> tuple[str, bool]:
    if FENCE_PATTERN.match(content):
        return "fence", not in_fence
    if in_fence:
        return "code", in_fence
    if not content.strip():
        return "blank", in_fence
    if HEADING_PATTERN.match(content):
        return "heading", in_fence
    if LIST_PATTERN.match(content):
        return "list", in_fence
    if QUOTE_PATTERN.match(content):
        return "quote", in_fence
    if TABLE_DELIMITER_PATTERN.match(content) or content.count("|") >= 2:
        return "table", in_fence
    if HTML_PATTERN.match(content):
        return "html", in_fence
    return "paragraph", in_fence


def def_build_appearance_ledger(data: bytes) -> dict[str, Any]:
    has_utf8_bom = data.startswith(UTF8_BOM)
    text = data.decode("utf-8-sig", errors="replace")
    lossless_lines = def_split_lines_lossless(text)
    newline_counts = {"crlf": 0, "lf": 0, "cr": 0, "none": 0}
    ledger: list[dict[str, Any]] = []
    in_fence = False
    for number, (content, newline) in enumerate(lossless_lines, start=1):
        newline_key = {"\r\n": "crlf", "\n": "lf", "\r": "cr", "": "none"}[newline]
        newline_counts[newline_key] += 1
        role, in_fence = def_line_role(content, in_fence)
        leading = re.match(r"^[ \t]*", content).group(0)
        trailing = re.search(r"[ \t]*$", content).group(0)
        ledger.append(
            {
                "line": number,
                "role": role,
                "content_sha256": def_sha256_bytes(content.encode(DEFAULT_ENCODING)),
                "leading_whitespace": leading,
                "trailing_whitespace": trailing,
                "newline": newline_key,
                "length": len(content),
            }
        )
    used_newlines = {key: value for key, value in newline_counts.items() if key != "none" and value}
    dominant_newline = max(used_newlines, key=used_newlines.get) if used_newlines else "none"
    return {
        "encoding": "utf-8-sig" if has_utf8_bom else "utf-8",
        "has_utf8_bom": has_utf8_bom,
        "decode_replacements": text.count("\ufffd"),
        "newline_counts": newline_counts,
        "dominant_newline": dominant_newline,
        "final_newline": bool(lossless_lines and lossless_lines[-1][1]),
        "line_count": len(lossless_lines),
        "role_counts": {
            role: sum(item["role"] == role for item in ledger)
            for role in sorted({item["role"] for item in ledger})
        },
        "line_ledger": ledger,
    }


def def_snapshot_paths(snapshot_root: Path, relative_path: Path) -> tuple[Path, Path]:
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError("Snapshot path must be relative and contained")
    container = snapshot_root / relative_path.parent / f"{relative_path.name}.appearance"
    return container / "manifest.json", container / "original.bin"


def def_capture_appearance(source: Path, snapshot_root: Path, relative_path: Path) -> dict[str, Any]:
    manifest_path, blob_path = def_snapshot_paths(snapshot_root, relative_path)
    data = source.read_bytes()
    manifest_path.parent.mkdir(parents=True, exist_ok=False)
    def_atomic_write_bytes(blob_path, data)
    manifest = {
        "schema_version": APPEARANCE_SCHEMA_VERSION,
        "captured_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source_path": str(source),
        "relative_path": str(relative_path).replace("\\", "/"),
        "source_size_bytes": len(data),
        "source_sha256": def_sha256_bytes(data),
        "original_blob": "original.bin",
        "appearance": def_build_appearance_ledger(data),
        "restore_policy": {
            "requires_hash_match": True,
            "atomic_replace": True,
            "never_reconstruct_from_normalized_text": True,
        },
    }
    def_atomic_write_json(manifest_path, manifest)
    verification = def_verify_appearance_snapshot(manifest_path)
    if not verification["valid"]:
        raise ValueError("Appearance snapshot verification failed")
    return {**manifest, "manifest_path": str(manifest_path), "blob_path": str(blob_path)}


def def_verify_appearance_snapshot(manifest_path: Path) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding=DEFAULT_ENCODING))
    if not isinstance(manifest, dict) or manifest.get("schema_version") not in {"1.3", "1.4"}:
        raise ValueError("Unsupported snapshot schema")
    if manifest.get("original_blob") != "original.bin":
        raise ValueError("Invalid snapshot blob path")
    if not re.fullmatch(r"[0-9a-f]{64}", str(manifest.get("source_sha256", ""))):
        raise ValueError("Invalid snapshot hash")
    if type(manifest.get("source_size_bytes")) is not int or manifest["source_size_bytes"] < 0:
        raise ValueError("Invalid snapshot size")
    blob_path = manifest_path.parent / "original.bin"
    if manifest_path.is_symlink() or blob_path.is_symlink():
        raise ValueError("Snapshot symlinks are not permitted")
    if not blob_path.is_file():
        return {"valid": False, "reason": "original_blob_missing", "manifest_path": str(manifest_path)}
    data = blob_path.read_bytes()
    actual_sha256 = def_sha256_bytes(data)
    valid = actual_sha256 == manifest.get("source_sha256") and len(data) == manifest.get("source_size_bytes")
    return {
        "valid": valid,
        "reason": "ok" if valid else "hash_or_size_mismatch",
        "manifest_path": str(manifest_path),
        "blob_path": str(blob_path),
        "expected_sha256": manifest.get("source_sha256"),
        "actual_sha256": actual_sha256,
        "size_bytes": len(data),
    }


def def_preview_appearance_restore(manifest_path: Path, destination: Path) -> dict[str, Any]:
    verification = def_verify_appearance_snapshot(manifest_path)
    def_validate_destination(manifest_path, destination)
    current_data = destination.read_bytes() if destination.is_file() else b""
    manifest = json.loads(manifest_path.read_text(encoding=DEFAULT_ENCODING))
    return {
        "snapshot_valid": verification["valid"],
        "destination": str(destination),
        "destination_exists": destination.is_file(),
        "current_sha256": def_sha256_bytes(current_data) if destination.is_file() else "MISSING",
        "original_sha256": manifest.get("source_sha256"),
        "would_change": not destination.is_file() or def_sha256_bytes(current_data) != manifest.get("source_sha256"),
        "original_appearance": manifest.get("appearance", {}),
    }


def def_validate_destination(manifest_path: Path, destination: Path) -> None:
    if any(part.is_symlink() for part in [destination, *destination.parents]):
        raise ValueError("Restore destination must not contain symlinks")
    if destination.resolve().is_relative_to(manifest_path.parent.resolve()):
        raise ValueError("Cannot restore into snapshot storage")
    if destination.exists() and not destination.is_file():
        raise ValueError("Restore destination is not a regular file")


def def_restore_appearance_snapshot(
    manifest_path: Path,
    destination: Path,
    expected_current_sha256: str | None = None,
    force: bool = False,
) -> dict[str, Any]:
    verification = def_verify_appearance_snapshot(manifest_path)
    if not verification["valid"]:
        raise ValueError(f"Invalid appearance snapshot: {verification['reason']}")
    def_validate_destination(manifest_path, destination)
    current_sha256 = def_sha256_bytes(destination.read_bytes()) if destination.is_file() else "MISSING"
    if expected_current_sha256 is not None and current_sha256 != expected_current_sha256:
        raise ValueError("Destination changed after restore preview")
    if expected_current_sha256 is None and not force:
        raise ValueError("Restore requires expected_current_sha256 or force=True")
    data = Path(verification["blob_path"]).read_bytes()
    if def_sha256_bytes(data) != verification["expected_sha256"]:
        raise ValueError("Snapshot changed during restore")
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{destination.name}.restore-", dir=destination.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        def_validate_destination(manifest_path, destination)
        latest = def_sha256_bytes(destination.read_bytes()) if destination.is_file() else "MISSING"
        if latest != current_sha256:
            raise ValueError("Destination changed during restore")
        if destination.exists():
            shutil.copymode(destination, temporary)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    restored_sha256 = def_sha256_bytes(destination.read_bytes())
    return {
        "restored": True,
        "destination": str(destination),
        "previous_sha256": current_sha256,
        "restored_sha256": restored_sha256,
        "exact_match": restored_sha256 == verification["expected_sha256"],
    }
