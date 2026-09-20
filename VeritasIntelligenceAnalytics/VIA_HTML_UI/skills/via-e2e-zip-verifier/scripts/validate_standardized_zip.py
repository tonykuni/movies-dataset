#!/usr/bin/env python3
"""Validate a VIA standardized-template ZIP by extracting it safely and running the directory contract."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

from validate_standardized_package import validate


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def locate_root(extracted: Path) -> Path:
    candidates = sorted(extracted.glob("*/manifest.json"))
    if len(candidates) != 1:
        raise FileNotFoundError(f"expected one standardized package root, found {len(candidates)}")
    return candidates[0].parent


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("zip", type=Path)
    parser.add_argument("--checksum-file", type=Path)
    parser.add_argument("--out-dir", type=Path, default=Path("/tmp/via-standardized-zip-verify"))
    parser.add_argument("--run-extracted-e2e", action="store_true")
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    archive = args.zip.resolve()
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    checks = []
    actual = digest(archive)
    expected = None
    if args.checksum_file and args.checksum_file.exists():
        expected = args.checksum_file.read_text(encoding="utf-8").split()[0]
    checks.append({"name": "sha256", "passed": expected is None or expected == actual, "detail": {"actual": actual, "expected": expected}})
    extract = out_dir / "extracted"
    if extract.exists():
        shutil.rmtree(extract)
    extract.mkdir(parents=True)
    with zipfile.ZipFile(archive) as zf:
        unsafe = []
        for info in zf.infolist():
            normalized = Path(info.filename.replace("\\", "/"))
            if normalized.is_absolute() or ".." in normalized.parts:
                unsafe.append(info.filename)
        checks.append({"name": "zip_path_safety", "passed": not unsafe, "detail": unsafe})
        corrupt = zf.testzip()
        checks.append({"name": "zip_integrity", "passed": corrupt is None, "detail": corrupt or {"members": len(zf.infolist())}})
        if unsafe or corrupt:
            result = {"archive": str(archive), "summary": {"total": len(checks), "passed": sum(x["passed"] for x in checks), "failed": sum(not x["passed"] for x in checks)}, "passed": False, "checks": checks}
            rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
            if args.json:
                args.json.parent.mkdir(parents=True, exist_ok=True)
                args.json.write_text(rendered, encoding="utf-8")
            print(rendered, end="")
            return 1
        zf.extractall(extract)
    try:
        root = locate_root(extract)
        nested = validate(root, args.run_extracted_e2e, out_dir / "standardized")
        checks.extend(nested["checks"])
    except Exception as exc:
        checks.append({"name": "standardized_contract", "passed": False, "detail": str(exc)})
    result = {"archive": str(archive), "root": str(extract), "checks": checks, "summary": {"total": len(checks), "passed": sum(x["passed"] for x in checks), "failed": sum(not x["passed"] for x in checks)}}
    result["passed"] = result["summary"]["failed"] == 0
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
