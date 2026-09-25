#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path


# =========================================================
# 1. 全域參數
# =========================================================

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PACKAGE_ROOT.parent
OUTPUT_BASENAME = PACKAGE_ROOT.name
MANIFEST_PATH = PACKAGE_ROOT / "MANIFEST.json"
CHECKSUM_PATH = PACKAGE_ROOT / "SHA256SUMS.txt"
ZIP_PATH = OUTPUT_DIR / f"{OUTPUT_BASENAME}.zip"
ZIP_SHA256_PATH = OUTPUT_DIR / f"{OUTPUT_BASENAME}.sha256"
OUTER_MANIFEST_PATH = OUTPUT_DIR / f"{OUTPUT_BASENAME}_manifest.json"
HASH_CHUNK_BYTES = 1024 * 1024
ZIP_COMPRESSION = zipfile.ZIP_DEFLATED
ZIP_COMPRESSLEVEL = 9
PAYLOAD_EXCLUSIONS = {MANIFEST_PATH.name, CHECKSUM_PATH.name}


# =========================================================
# 2. 檔案盤點與雜湊
# =========================================================

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(HASH_CHUNK_BYTES):
            digest.update(chunk)
    return digest.hexdigest()


def iter_payload_files() -> list[Path]:
    return sorted(
        path
        for path in PACKAGE_ROOT.rglob("*")
        if path.is_file() and path.name not in PAYLOAD_EXCLUSIONS
    )


def build_manifest(files: list[Path]) -> dict[str, object]:
    entries = []
    total_size = 0
    for path in files:
        size_bytes = path.stat().st_size
        total_size += size_bytes
        entries.append(
            {
                "path": path.relative_to(PACKAGE_ROOT).as_posix(),
                "size_bytes": size_bytes,
                "sha256": sha256_file(path),
            }
        )
    return {
        "package": OUTPUT_BASENAME,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "file_count": len(entries),
        "total_size_bytes": total_size,
        "excluded_rebuildable": [
            "node_modules",
            ".sites-runtime",
            ".wrangler",
            ".vinext",
            "__pycache__",
            "*.pyc",
            ".openai/hosting.json",
        ],
        "files": entries,
    }


# =========================================================
# 3. Manifest 與 Checksum 輸出
# =========================================================

def write_manifest(manifest: dict[str, object]) -> None:
    content = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    MANIFEST_PATH.write_text(content, encoding="utf-8")
    OUTER_MANIFEST_PATH.write_text(content, encoding="utf-8")


def write_checksums(files: list[Path]) -> None:
    checksum_files = [*files, MANIFEST_PATH]
    lines = [
        f"{sha256_file(path)}  {path.relative_to(PACKAGE_ROOT).as_posix()}"
        for path in checksum_files
    ]
    CHECKSUM_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


# =========================================================
# 4. ZIP 建立與驗證
# =========================================================

def build_zip() -> None:
    with zipfile.ZipFile(
        ZIP_PATH,
        mode="w",
        compression=ZIP_COMPRESSION,
        compresslevel=ZIP_COMPRESSLEVEL,
    ) as archive:
        for path in sorted(PACKAGE_ROOT.rglob("*")):
            if path.is_file():
                archive.write(
                    path,
                    arcname=(Path(OUTPUT_BASENAME) / path.relative_to(PACKAGE_ROOT)).as_posix(),
                )


def validate_zip(expected_file_count: int) -> dict[str, object]:
    with zipfile.ZipFile(ZIP_PATH, mode="r") as archive:
        bad_member = archive.testzip()
        file_members = [item for item in archive.infolist() if not item.is_dir()]
    if bad_member is not None:
        raise RuntimeError(f"ZIP CRC validation failed: {bad_member}")
    expected_total = expected_file_count + 2
    if len(file_members) != expected_total:
        raise RuntimeError(
            f"ZIP file count mismatch: expected {expected_total}, got {len(file_members)}"
        )
    return {
        "zip_path": str(ZIP_PATH),
        "zip_size_bytes": ZIP_PATH.stat().st_size,
        "zip_sha256": sha256_file(ZIP_PATH),
        "zip_file_count": len(file_members),
        "crc_status": "PASS",
    }


def write_zip_checksum(zip_report: dict[str, object]) -> None:
    ZIP_SHA256_PATH.write_text(
        f"{zip_report['zip_sha256']}  {ZIP_PATH.name}\n",
        encoding="utf-8",
    )


# =========================================================
# 5. 主流程
# =========================================================

def main() -> int:
    files = iter_payload_files()
    manifest = build_manifest(files)
    write_manifest(manifest)
    write_checksums(files)
    build_zip()
    zip_report = validate_zip(expected_file_count=len(files))
    write_zip_checksum(zip_report)
    print(
        json.dumps(
            {
                "manifest_file_count": manifest["file_count"],
                "manifest_total_size_bytes": manifest["total_size_bytes"],
                **zip_report,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
