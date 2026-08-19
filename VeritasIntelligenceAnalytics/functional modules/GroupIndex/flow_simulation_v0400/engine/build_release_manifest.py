from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


EXCLUDED_PARTS = {"__pycache__", ".venv"}
EXCLUDED_NAMES = {".via-monitor.pid", "release_manifest.json"}


def def_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def def_main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    summary_path = project_root / "evidence" / "run_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    files: list[dict[str, object]] = []
    for path in sorted(project_root.rglob("*")):
        relative = path.relative_to(project_root)
        if not path.is_file() or EXCLUDED_PARTS.intersection(relative.parts):
            continue
        if path.name in EXCLUDED_NAMES or path.suffix.lower() == ".zip":
            continue
        files.append(
            {
                "Path": relative.as_posix(),
                "Bytes": path.stat().st_size,
                "SHA256": def_sha256(path),
            }
        )
    manifest = {
        "SystemId": summary["SystemId"],
        "Version": summary["Version"],
        "GeneratedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "Gate": summary["Gate"],
        "DataMode": summary["DataMode"],
        "HardFailures": summary["HardFailures"],
        "CanonicalMutation": summary["CanonicalMutation"],
        "NetworkExecution": summary["NetworkExecution"],
        "OrderExecution": summary["OrderExecution"],
        "FileCount": len(files),
        "Files": files,
    }
    target = project_root / "evidence" / "release_manifest.json"
    target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Release manifest: {target}")
    print(f"Files recorded: {len(files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(def_main())
