#!/usr/bin/env python3
"""VIA · VeritasDataForge (VDF) movies intake v001 · 電影資料集鍛造引擎.

Forges the repository movies dataset (<Repo>/data/*.csv) into the VDF
analytical database consumed by VeritasAutoPlot:

    <Base>/functional modules/VDF/db/movies_dataset.sqlite

Curated analytical tables (year-keyed so AutoPlot auto-pairing works):

    movies_genres_summary   verbatim copy of data/movies_genres_summary.csv
    yearly_box_office       per-year aggregates from data/movie_metadata.csv
    yearly_tmdb             per-year aggregates from data/tmdb_5000_movies.csv

Governance (per VDF_Subsystem_Manifest.json):
    - Products only: writes are confined to <Base>/functional modules/VDF/db
      plus the intake summary under VDF/qa/evidence. Sources are read-only.
    - Modes: Refresh (default, atomic rebuild), ValidateOnly, DryRun.
    - Every Refresh emits qa/evidence/movies_intake_summary.json with sha256
      of each source, row counts in/out, and the resulting gate.

Zero third-party dependencies. Usage:
    python vdf_movies_intake_v001.py --base <Base> [--source <dir>]
        [--mode Refresh|ValidateOnly|DryRun]
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import argparse
import csv
import hashlib
import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

VERSION = "v001"

SOURCES = {
    "movies_genres_summary": "movies_genres_summary.csv",
    "movie_metadata": "movie_metadata.csv",
    "tmdb_5000_movies": "tmdb_5000_movies.csv",
}

YEAR_MIN, YEAR_MAX = 1900, 2030


def log(message: str) -> None:
    print(f"[VDF] {message}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def to_float(raw: str | None) -> float | None:
    if raw is None:
        return None
    raw = raw.strip()
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def to_year(raw: str | None) -> int | None:
    value = to_float(raw)
    if value is None:
        return None
    year = int(value)
    return year if YEAR_MIN <= year <= YEAR_MAX else None


def mean(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 4) if values else None


# ------------------------------------------------------------- table builders
def build_genres_summary(rows: list[dict]) -> tuple[list[str], list[tuple]]:
    columns = ["year", "gross", "popularity", "imdb_score", "vote_average", "genre"]
    out: list[tuple] = []
    for row in rows:
        year = to_year(row.get("year"))
        if year is None:
            continue
        out.append((year, to_float(row.get("gross")), to_float(row.get("popularity")),
                    to_float(row.get("imdb_score")), to_float(row.get("vote_average")),
                    (row.get("genre") or "").strip()))
    return columns, out


def build_yearly_box_office(rows: list[dict]) -> tuple[list[str], list[tuple]]:
    columns = ["title_year", "movie_count", "total_gross", "total_budget",
               "avg_imdb_score", "avg_duration"]
    buckets: dict[int, dict[str, list[float]]] = {}
    for row in rows:
        year = to_year(row.get("title_year"))
        if year is None:
            continue
        bucket = buckets.setdefault(year, {"gross": [], "budget": [], "imdb": [], "dur": []})
        for key, col in (("gross", "gross"), ("budget", "budget"),
                         ("imdb", "imdb_score"), ("dur", "duration")):
            value = to_float(row.get(col))
            if value is not None:
                bucket[key].append(value)
    out = [(year, len(b["imdb"]), round(sum(b["gross"]), 0), round(sum(b["budget"]), 0),
            mean(b["imdb"]), mean(b["dur"]))
           for year, b in sorted(buckets.items())]
    return columns, out


def build_yearly_tmdb(rows: list[dict]) -> tuple[list[str], list[tuple]]:
    columns = ["year", "movie_count", "total_revenue", "total_budget",
               "avg_popularity", "avg_vote_average"]
    buckets: dict[int, dict[str, list[float]]] = {}
    for row in rows:
        date = (row.get("release_date") or "").strip()
        year = to_year(date[:4]) if len(date) >= 4 else None
        if year is None:
            continue
        bucket = buckets.setdefault(year, {"rev": [], "budget": [], "pop": [], "vote": []})
        for key, col in (("rev", "revenue"), ("budget", "budget"),
                         ("pop", "popularity"), ("vote", "vote_average")):
            value = to_float(row.get(col))
            if value is not None:
                bucket[key].append(value)
    out = [(year, len(b["vote"]), round(sum(b["rev"]), 0), round(sum(b["budget"]), 0),
            mean(b["pop"]), mean(b["vote"]))
           for year, b in sorted(buckets.items())]
    return columns, out


BUILDERS = {
    "movies_genres_summary": ("movies_genres_summary", build_genres_summary),
    "yearly_box_office": ("movie_metadata", build_yearly_box_office),
    "yearly_tmdb": ("tmdb_5000_movies", build_yearly_tmdb),
}


# --------------------------------------------------------------------- forge
def forge(base: Path, source_dir: Path, mode: str) -> int:
    db_dir = base / "functional modules" / "VDF" / "db"
    db_path = db_dir / "movies_dataset.sqlite"
    # Summary lives under qa/evidence, NOT under db/ — AutoPlot scans db/ for
    # data files and .json is a data suffix there.
    summary_path = (base / "functional modules" / "VDF" / "qa" / "evidence"
                    / "movies_intake_summary.json")

    summary: dict = {"engine": f"vdf_movies_intake_{VERSION}", "mode": mode,
                     "source_dir": str(source_dir), "sources": {}, "tables": {}}

    source_rows: dict[str, list[dict]] = {}
    missing: list[str] = []
    for name, filename in SOURCES.items():
        path = source_dir / filename
        if not path.is_file():
            missing.append(filename)
            continue
        rows = read_csv(path)
        source_rows[name] = rows
        summary["sources"][filename] = {"sha256": sha256_file(path), "rows": len(rows)}
        log(f"SOURCE {filename}: {len(rows)} rows · sha256 {summary['sources'][filename]['sha256'][:12]}…")
    if missing:
        summary["gate"] = "RED_MISSING_SOURCES"
        summary["missing"] = missing
        log(f"RED missing sources: {', '.join(missing)}")
        _write_summary(summary_path, summary, mode)
        return 2

    tables: dict[str, tuple[list[str], list[tuple]]] = {}
    for table, (source, builder) in BUILDERS.items():
        columns, rows = builder(source_rows[source])
        if not rows:
            summary["gate"] = "RED_EMPTY_TABLE"
            summary["tables"][table] = {"rows": 0}
            log(f"RED table {table} produced no rows")
            _write_summary(summary_path, summary, mode)
            return 2
        tables[table] = (columns, rows)
        summary["tables"][table] = {"rows": len(rows), "columns": columns}
        log(f"TABLE {table}: {len(rows)} rows × {len(columns)} cols")

    if mode == "ValidateOnly":
        summary["gate"] = "GREEN_VALIDATE_ONLY_NO_WRITE"
        log("GREEN ValidateOnly — sources parse, all tables non-empty, nothing written")
        print(json.dumps(summary, indent=2))
        return 0
    if mode == "DryRun":
        summary["gate"] = "GREEN_DRY_RUN_NO_WRITE"
        log(f"GREEN DryRun — would write {db_path} and {summary_path.name}")
        print(json.dumps(summary, indent=2))
        return 0

    # Refresh: build into a temp file, then atomic replace.
    db_dir.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix="movies_dataset_", suffix=".sqlite", dir=db_dir)
    os.close(fd)
    tmp_path = Path(tmp_name)
    try:
        # sqlite3's context manager only manages the transaction — it does not
        # close the connection, and Windows refuses os.replace while the file
        # handle is open. Close explicitly before replacing.
        conn = sqlite3.connect(tmp_path)
        try:
            for table, (columns, rows) in tables.items():
                column_sql = ", ".join(f'"{c}"' for c in columns)
                placeholders = ", ".join("?" for _ in columns)
                conn.execute(f'CREATE TABLE "{table}" ({column_sql})')
                conn.executemany(
                    f'INSERT INTO "{table}" ({column_sql}) VALUES ({placeholders})', rows)
            conn.commit()
        finally:
            conn.close()
        tmp_path.replace(db_path)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise

    summary["database"] = {"path": str(db_path), "sha256": sha256_file(db_path),
                           "bytes": db_path.stat().st_size}
    summary["gate"] = "GREEN_REFRESH_DB_WRITTEN"
    _write_summary(summary_path, summary, mode)
    log(f"GREEN Refresh — {db_path} ({summary['database']['bytes']} bytes, "
        f"sha256 {summary['database']['sha256'][:12]}…)")
    log(f"SUMMARY {summary_path}")
    return 0


def _write_summary(path: Path, summary: dict, mode: str) -> None:
    if mode in ("ValidateOnly", "DryRun"):
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", required=True, help="VIA base directory")
    parser.add_argument("--source", help="movies dataset directory (default <Base>/../data)")
    parser.add_argument("--mode", choices=["Refresh", "ValidateOnly", "DryRun"],
                        default="Refresh")
    args = parser.parse_args()

    base = Path(args.base).expanduser().resolve()
    if not base.is_dir():
        log(f"RED base not found: {base}")
        return 2
    source_dir = (Path(args.source).expanduser().resolve()
                  if args.source else (base.parent / "data"))
    if not source_dir.is_dir():
        log(f"RED source dir not found: {source_dir}")
        return 2
    log(f"VDF movies intake {VERSION} · base={base} · source={source_dir} · mode={args.mode}")
    return forge(base, source_dir, args.mode)


if __name__ == "__main__":
    sys.exit(main())
