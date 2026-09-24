#!/usr/bin/env python3
"""Extract a reviewable VCGC source snapshot from an existing local checkout.

Default: read-only inventory. --zip copies source files into a versioned ZIP.
No imports of project modules, network calls, credentials, or consent changes.
"""

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import zipfile
from pathlib import Path


# Scope: active VCGC entry points, their inventory/sync ports, and direct helpers.
DEFAULT_ROOT = Path(__file__).resolve().parents[1]
VIA_REL = "VeritasIntelligenceAnalytics"
FAMILIES = (
    "CGC_MDL149_VeritasCentralGovernanceConsole",
    "CGC_MDL178_ToolInventoryRatchet",
    "CGC_MDL179_VcgcSyncHub",
    "CGC_MDL064_SelftestGrid",
    "CGC_MDL095_DeckServer",
    "CGC_MDL115_SSOTRegexDict",
    "CGC_MDL123_DataHome",
    "CGC_MDL137_RunGate",
    "CGC_MDL141_ClosingGate",
    "CGC_MDL144_CopyDoctor",
    "CGC_MDL148_EngineBus",
    "CGC_MDL158_VIAPanoramaAuditRepair",
    "CGC_MDL164_GovernanceCompletenessAudit",
    "CGC_MDL169_VIAStateMatrix",
    "CGC_MDL176_SynonymUnion",
    "CGC_MDL177_ChinaBrokerPurge",
    "CGC_MDL185_SsotBookSync",
    "SUP_MDL737_SuperAccelModule",
    "SUP_MDL749_VRNFieldRuleHub",
    "SUP_MDL750_VeritasUIHead",
    "SUP_MDL751_VIATailPick",
    "SUP_MDL752_VIAJsonIO",
)
EXCLUDED_PARTS = frozenset({"references", "intake", "BACKUP", "SCOPE_COPY", "_superseded", "__pycache__"})
MAX_SOURCE_BYTES = 2_000_000


def version(path: Path, family: str) -> int | None:
    match = re.fullmatch(re.escape(family) + r"_v(\d{3,4})\.py", path.name)
    return int(match.group(1)) if match else None


def select_sources(via: Path) -> tuple[list[Path], list[str]]:
    """Find one active version per family and refuse paths outside checkout."""
    support = via / "supportive modules"
    if not support.is_dir():
        raise ValueError("VIA supportive modules directory is missing")
    chosen, missing = [], []
    for family in FAMILIES:
        candidates = []
        for path in support.rglob(f"{family}_v*.py"):
            if EXCLUDED_PARTS.intersection(path.relative_to(support).parts):
                continue
            ver = version(path, family)
            if ver is not None:
                candidates.append((ver, path))
        if not candidates:
            missing.append(family)
            continue
        _, path = max(candidates, key=lambda pair: pair[0])
        if not path.resolve().is_relative_to(via.resolve()) or not path.is_file():
            raise ValueError(f"Unsafe source path: {family}")
        if path.stat().st_size > MAX_SOURCE_BYTES:
            raise ValueError(f"Source exceeds limit: {family}")
        chosen.append(path)
    return chosen, missing


def inventory(root: Path) -> tuple[dict, list[Path]]:
    via = root / VIA_REL
    paths, missing = select_sources(via)
    records = []
    for path in paths:
        data = path.read_bytes()
        records.append({"family": path.stem.rsplit("_v", 1)[0],
                        "path": path.relative_to(root).as_posix(),
                        "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    return {"scope": "VCGC source and direct support; no database or runtime files",
            "root": VIA_REL, "count": len(records), "missing": missing,
            "files": records}, paths


def write_zip(target: Path, root: Path, report: dict, paths: list[Path]) -> None:
    if report["missing"]:
        raise ValueError("Missing required families; refusing partial ZIP")
    if target.exists():
        raise ValueError("Output exists; refusing to overwrite")
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".vcgc_support_", suffix=".zip", dir=target.parent)
    os.close(fd)
    temporary = Path(temp_name)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for record, path in zip(report["files"], paths):
                data = path.read_bytes()
                if hashlib.sha256(data).hexdigest() != record["sha256"]:
                    raise ValueError(f"Source changed during extraction: {record['family']}")
                zf.writestr(record["path"], data)
            zf.writestr("VCGC_SUPPORT_MANIFEST.json", json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--zip", type=Path, help="write a ZIP only when all families exist")
    parser.add_argument("--json", action="store_true", help="print the full source manifest")
    args = parser.parse_args()
    root = args.root.resolve()
    if not (root / VIA_REL).is_dir():
        parser.error("--root must be a movies-dataset checkout")
    try:
        report, paths = inventory(root)
        if args.zip:
            write_zip(args.zip, root, report, paths)
    except (OSError, ValueError) as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"VCGC support: {report['count']}/{len(FAMILIES)} active source families")
        for item in report["files"]:
            print(f"{item['family']} -> {item['path']}")
        if report["missing"]:
            print("MISSING: " + ", ".join(report["missing"]))
        if args.zip:
            print(f"ZIP: {args.zip}")
    return 0 if not report["missing"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
