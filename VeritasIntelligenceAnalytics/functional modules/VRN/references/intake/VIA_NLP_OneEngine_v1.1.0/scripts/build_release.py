"""Build and verify a deterministic release ZIP and SHA-256 manifest."""

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = PROJECT_ROOT / "dist"
VERSION = "1.1.0"
ARCHIVE_PATH = DIST_DIR / f"VIA_NLP_OneEngine_v{VERSION}.zip"
MANIFEST_PATH = PROJECT_ROOT / "MANIFEST.sha256"
ARCHIVE_PREFIX = f"VIA_NLP_OneEngine_v{VERSION}"
FIXED_TIMESTAMP = (2026, 8, 27, 0, 0, 0)
EXCLUDED_DIRS = {"dist", "runtime", "benchmark_runtime", "__pycache__", ".venv", ".testvenv", ".pytest_cache"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def should_include(path: Path) -> bool:
    relative = path.relative_to(PROJECT_ROOT)
    if any(part in EXCLUDED_DIRS or part.endswith(".egg-info") for part in relative.parts):
        return False
    if path.suffix.lower() in EXCLUDED_SUFFIXES:
        return False
    return path != MANIFEST_PATH


def source_files() -> list[Path]:
    return sorted((path for path in PROJECT_ROOT.rglob("*") if path.is_file() and should_include(path)), key=lambda item: item.as_posix())


def write_manifest(files: list[Path]) -> None:
    lines = [f"{sha256_file(path)}  {path.relative_to(PROJECT_ROOT).as_posix()}" for path in files]
    MANIFEST_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def build_archive(files: list[Path]) -> None:
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    all_files = files + [MANIFEST_PATH]
    with zipfile.ZipFile(ARCHIVE_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(all_files, key=lambda item: item.as_posix()):
            relative = path.relative_to(PROJECT_ROOT).as_posix()
            info = zipfile.ZipInfo(f"{ARCHIVE_PREFIX}/{relative}", date_time=FIXED_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o755 if path.name.endswith(".ps1") else 0o644) << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def verify_archive(files: list[Path]) -> None:
    expected = {path.relative_to(PROJECT_ROOT).as_posix(): sha256_file(path) for path in files}
    with zipfile.ZipFile(ARCHIVE_PATH) as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"Corrupt ZIP member: {bad}")
        names = set(archive.namelist())
        for relative, digest in expected.items():
            member = f"{ARCHIVE_PREFIX}/{relative}"
            if member not in names:
                raise RuntimeError(f"Missing ZIP member: {member}")
            actual = hashlib.sha256(archive.read(member)).hexdigest()
            if actual != digest:
                raise RuntimeError(f"ZIP hash mismatch: {member}")


def main() -> int:
    files = source_files()
    write_manifest(files)
    build_archive(files)
    verify_archive(files)
    print(
        {
            "archive": str(ARCHIVE_PATH),
            "files": len(files) + 1,
            "bytes": ARCHIVE_PATH.stat().st_size,
            "sha256": sha256_file(ARCHIVE_PATH),
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
