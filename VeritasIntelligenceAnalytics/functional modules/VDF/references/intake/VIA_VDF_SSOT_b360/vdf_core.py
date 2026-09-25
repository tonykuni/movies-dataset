#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:MODULE_SPEC:START]
# MODULE_NAME:       vdf_core
# MODULE_VERSION:    2.0.0
# MODULE_ROLE:       VDF unified core. Merges what used to be SystemManager +
#                    DuckDB sink + matrix view generator into one file.
#                    Holds: matrix loader, parquet store, runner, fetcher
#                    registry, DuckDB mirror, CLI.
# MODULE_ZONE:       D5
# MODULE_TYPE:       PIPELINE_STEP
# DEPENDENCIES:      pandas, pyarrow, requests
# OPTIONAL_DEPENDENCIES: yfinance, fredapi, akshare, duckdb,
#                       VeritasCeleritas, VeritasAegisNexus
# ERROR_POLICY:      RETURN_SAFE_DEFAULT
# SAFE_SKIP:         True
# MERGE_UNIT_ID:     VDF-D5-CORE-002
# [VIA:MODULE_SPEC:END]
"""
VDF Core (v2).

Single entry point for all data acquisitions and the supporting infrastructure.

Usage:
    python vdf_core.py --mode full
    python vdf_core.py --mode category --category tw_stock
    python vdf_core.py --mode ticker --ticker 2330.TW
    python vdf_core.py --mode dry-run
    python vdf_core.py --mode test
    python vdf_core.py --mode gen-views     # regenerate config/*.md + *.csv
"""

# [VIA:ANCHOR:D5_CORE:START]

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


# =========================================================================
# PATHS / CONSTANTS
# =========================================================================

_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parent  # VDF/

DEFAULT_MATRIX_PATH = _PROJECT_ROOT / "config" / "vdf_fetch_matrix.json"
DEFAULT_OUTPUT_DIR = _PROJECT_ROOT / "output"
DEFAULT_TEMP_DIR = _PROJECT_ROOT / "temp"
DEFAULT_LOG_DIR = _PROJECT_ROOT / "logs"

PROD_OUTPUT_DIR = Path(r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output")
PROD_TEMP_DIR = Path(r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\temp")

VERITAS_SUPPORT_PATHS = [
    Path(r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module"),
    Path(r"C:\Users\tonyk\OneDrive\Pictures\VeritasIntelligenceAnalytics\module\supportive_module"),
    _PROJECT_ROOT / "src",
]
for _p in VERITAS_SUPPORT_PATHS:
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

FRED_API_KEY = os.environ.get("VDF_FRED_API_KEY", "<REDACTED:VDF_FRED_API_KEY>")


# =========================================================================
# LOGGER
# =========================================================================

DEFAULT_LOG_DIR.mkdir(parents=True, exist_ok=True)
_log_file = DEFAULT_LOG_DIR / f"vdf_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Only set up handlers once (in case of re-import by API server)
_root_logger = logging.getLogger()
if not _root_logger.handlers:
    _formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    _stream_h = logging.StreamHandler(sys.stdout)
    _stream_h.setFormatter(_formatter)
    _file_h = logging.FileHandler(_log_file, encoding="utf-8")
    _file_h.setFormatter(_formatter)
    _root_logger.addHandler(_stream_h)
    _root_logger.addHandler(_file_h)
    _root_logger.setLevel(logging.INFO)

log = logging.getLogger("VDF")


# =========================================================================
# IMPORT GUARDS
# =========================================================================

def _try_import(name: str):
    try:
        return __import__(name)
    except Exception as e:
        log.warning("[IMPORT] %s unavailable: %s", name, e)
        return None

pd = _try_import("pandas")
pa = _try_import("pyarrow")
yf = _try_import("yfinance")
requests = _try_import("requests")
fredapi = _try_import("fredapi")
ak = _try_import("akshare")
duckdb = _try_import("duckdb")

_PD_OK = pd is not None
_PA_OK = pa is not None
_YF_OK = yf is not None
_REQ_OK = requests is not None
_FRED_OK = fredapi is not None
_AK_OK = ak is not None
_DUCKDB_OK = duckdb is not None

# Optional Veritas modules - load via the bridge (one place, graceful)
try:
    from vdf_bridge import get_bridge, registry_record, env_health_check
    _BRIDGE = get_bridge()
    _BRIDGE_OK = True
    _summary = _BRIDGE.summary()
    log.info("[BOOT] bridge loaded - supportive modules: %s",
             {k: v for k, v in _summary.items() if k != "capabilities"})
    log.info("[BOOT] bridge capabilities: %s", _summary["capabilities"])
    # record this run in the VIA registry (no-op if registry absent)
    registry_record(
        module_name="vdf_core",
        version="2.0.0",
        role="PIPELINE_STEP",
        extra={"entry": "vdf_core.main"},
    )
    # env health check (logs missing deps)
    _health = env_health_check()
    _missing = [k.replace("has_", "") for k, v in _health.items()
                if k.startswith("has_") and v is False]
    if _missing:
        log.info("[BOOT] env health - missing optional deps: %s", _missing)
except Exception as e:
    _BRIDGE = None
    _BRIDGE_OK = False
    log.warning("[BOOT] bridge unavailable: %s - all supportive modules will be skipped", e)


# =========================================================================
# MATRIX
# =========================================================================

@dataclass
class CategorySpec:
    id: str
    name: str
    description: str
    output_file: str
    schema_group: str
    primary_key: List[str]
    update_frequency: str
    source_pipeline: List[Dict[str, Any]]
    tickers: List[Dict[str, Any]] = field(default_factory=list)
    indicators: List[Dict[str, Any]] = field(default_factory=list)
    universe_source: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FetchMatrix:
    schema_version: str
    global_cfg: Dict[str, Any]
    unified_headers: Dict[str, List[str]]
    categories: List[CategorySpec]
    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path) -> "FetchMatrix":
        if not path.exists():
            raise FileNotFoundError(f"Matrix config not found: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        cats = []
        for c in data.get("categories", []):
            cats.append(CategorySpec(
                id=c["id"],
                name=c["name"],
                description=c.get("description", ""),
                output_file=c["output_file"],
                schema_group=c["schema_group"],
                primary_key=c["primary_key"],
                update_frequency=c.get("update_frequency", "daily"),
                source_pipeline=c.get("source_pipeline", []),
                tickers=c.get("tickers", []),
                indicators=c.get("indicators", []),
                universe_source=c.get("universe_source"),
                raw=c,
            ))
        return cls(
            schema_version=data.get("schema_version", "1.0.0"),
            global_cfg=data.get("global", {}),
            unified_headers=data.get("unified_headers", {}),
            categories=cats,
            raw=data,
        )

    def get_category(self, cat_id: str) -> Optional[CategorySpec]:
        for c in self.categories:
            if c.id == cat_id:
                return c
        return None


# =========================================================================
# PARQUET STORE
# =========================================================================

class ParquetStore:
    """Append-with-dedup parquet store. Atomic merge writes."""

    def __init__(self, output_dir: Path, temp_dir: Path):
        self.output_dir = Path(output_dir)
        self.temp_dir = Path(temp_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def path(self, filename: str) -> Path:
        return self.output_dir / filename

    def load_existing(self, filename: str):
        if not _PD_OK:
            return None
        fp = self.path(filename)
        if not fp.exists():
            return None
        try:
            df = pd.read_parquet(fp)
            log.info("[STORE] loaded existing %s rows=%d", filename, len(df))
            return df
        except Exception as e:
            log.warning("[STORE] failed to load %s: %s -- treating as empty", filename, e)
            return None

    def save_merge(self, filename: str, new_df, primary_key: List[str]) -> Dict[str, Any]:
        if not _PD_OK or new_df is None or len(new_df) == 0:
            return {"ok": False, "reason": "no_data", "wrote": 0}

        for k in primary_key:
            if k not in new_df.columns:
                log.error("[STORE] primary_key column %s missing in new_df", k)
                return {"ok": False, "reason": f"missing_pk_{k}", "wrote": 0}

        # Use bridge for accelerated DataFrame ops when available
        try:
            from vdf_bridge import accelerated_concat, accelerated_drop_duplicates
            _use_accel = True
        except Exception:
            _use_accel = False

        existing = self.load_existing(filename)
        if existing is not None and not existing.empty:
            all_cols = list({*existing.columns, *new_df.columns})
            existing = existing.reindex(columns=all_cols)
            new_df = new_df.reindex(columns=all_cols)
            if _use_accel:
                combined = accelerated_concat([existing, new_df])
            else:
                combined = pd.concat([existing, new_df], ignore_index=True)
        else:
            combined = new_df.copy()

        before = len(combined)
        if _use_accel:
            combined = accelerated_drop_duplicates(combined, subset=primary_key)
        else:
            combined = combined.drop_duplicates(subset=primary_key, keep="last")
        try:
            combined = combined.sort_values(primary_key).reset_index(drop=True)
        except Exception:
            pass

        fp = self.path(filename)
        tmp_fp = self.temp_dir / (filename + ".tmp.parquet")
        try:
            combined.to_parquet(tmp_fp, index=False, engine="pyarrow")
            os.replace(tmp_fp, fp)
            log.info("[STORE] wrote %s rows=%d (deduped %d)", filename, len(combined), before - len(combined))
            return {"ok": True, "wrote": len(combined), "deduped": before - len(combined)}
        except Exception as e:
            log.error("[STORE] write failed %s: %s", filename, e)
            log.debug(traceback.format_exc())
            return {"ok": False, "reason": str(e), "wrote": 0}


# =========================================================================
# FETCHER REGISTRY
# =========================================================================

class FetcherRegistry:
    def __init__(self):
        self._map = {}
    def register(self, cat_id: str, fn):
        self._map[cat_id] = fn
    def get(self, cat_id: str):
        return self._map.get(cat_id)
    def list(self) -> List[str]:
        return sorted(self._map.keys())

REGISTRY = FetcherRegistry()


def register_all_fetchers():
    """Import and register every category fetcher. Safe to call repeatedly."""
    # Market data (yfinance + TWSE/TPEX)
    try:
        from vdf_fetchers_market import (
            fetch_yfinance_prices,
            fetch_tw_index_official,
            fetch_tw_stock_unified,
        )
        # All yfinance-only price categories
        for cat in ("tw_etf_passive", "tw_etf_active",
                    "intl_stock", "intl_index",
                    "commodity", "fx"):
            REGISTRY.register(cat, fetch_yfinance_prices)
        # Back-compat: old "tw_etf" / "intl_etf" names still work
        REGISTRY.register("tw_etf", fetch_yfinance_prices)
        REGISTRY.register("intl_etf", fetch_yfinance_prices)
        REGISTRY.register("tw_stock", fetch_tw_stock_unified)
        REGISTRY.register("tw_index", fetch_tw_index_official)
    except Exception as e:
        log.warning("[REGISTRY] market fetchers unavailable: %s", e)
        log.debug(traceback.format_exc())

    # Financials (MOPS + yfinance)
    try:
        from vdf_fetchers_financials import fetch_stock_financials
        REGISTRY.register("tw_financials", fetch_stock_financials)
    except Exception as e:
        log.warning("[REGISTRY] financials fetcher unavailable: %s", e)
        log.debug(traceback.format_exc())

    # Macro / sentiment / shipping
    try:
        from vdf_fetchers_macro import (
            fetch_macro_fred,
            fetch_sentiment,
            fetch_shipping,
        )
        REGISTRY.register("macro", fetch_macro_fred)
        REGISTRY.register("sentiment", fetch_sentiment)
        REGISTRY.register("shipping", fetch_shipping)
    except Exception as e:
        log.warning("[REGISTRY] macro fetchers unavailable: %s", e)
        log.debug(traceback.format_exc())


# =========================================================================
# RUNNER
# =========================================================================

class VDFRunner:
    def __init__(self, matrix: FetchMatrix, store: ParquetStore, ctx: Dict[str, Any]):
        self.matrix = matrix
        self.store = store
        self.ctx = ctx
        self.report: Dict[str, Any] = {
            "started_at": datetime.now().isoformat(),
            "categories": {},
            "ctx": {k: v for k, v in ctx.items() if k != "logger"},
        }

    def run_category(self, cat_id: str) -> Dict[str, Any]:
        spec = self.matrix.get_category(cat_id)
        if spec is None:
            log.error("[RUN] unknown category: %s", cat_id)
            return {"ok": False, "reason": "unknown_category"}

        fn = REGISTRY.get(cat_id)
        if fn is None:
            log.warning("[RUN] no fetcher for %s -- skipping", cat_id)
            return {"ok": False, "reason": "no_fetcher", "category": cat_id}

        log.info("=" * 78)
        log.info("[RUN] CATEGORY: %s (%s)", cat_id, spec.name)
        log.info("=" * 78)

        t0 = time.time()
        try:
            df = fn(spec, self.ctx)
            if df is None or (hasattr(df, "empty") and df.empty):
                log.warning("[RUN] %s returned empty", cat_id)
                result = {"ok": True, "wrote": 0, "reason": "empty"}
            else:
                save_res = self.store.save_merge(
                    filename=spec.output_file,
                    new_df=df,
                    primary_key=spec.primary_key,
                )
                result = {"ok": save_res.get("ok", False), **save_res, "fetched_rows": len(df)}
        except Exception as e:
            log.error("[RUN] %s failed: %s", cat_id, e)
            log.debug(traceback.format_exc())
            result = {"ok": False, "reason": str(e)}

        result["elapsed_sec"] = round(time.time() - t0, 2)
        self.report["categories"][cat_id] = result
        log.info("[RUN] %s done in %.2fs - %s", cat_id, result["elapsed_sec"], result)
        return result

    def run_all(self) -> Dict[str, Any]:
        for c in self.matrix.categories:
            self.run_category(c.id)
        self._finalize()
        return self.report

    def run_one(self, cat_id: str) -> Dict[str, Any]:
        self.run_category(cat_id)
        self._finalize()
        return self.report

    def _finalize(self):
        # DuckDB mirror
        if self.ctx.get("output_format", "parquet") == "parquet+duckdb":
            try:
                duck_results = mirror_to_duckdb(self.store.output_dir)
                self.report["duckdb_mirror"] = duck_results
                log.info("[RUN] DuckDB mirror: %s", duck_results)
            except Exception as e:
                log.warning("[RUN] DuckDB mirror failed: %s", e)
                self.report["duckdb_mirror"] = {"error": str(e)}

        self.report["finished_at"] = datetime.now().isoformat()
        rpt_path = self.store.output_dir / f"vdf_run_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            rpt_path.write_text(json.dumps(self.report, indent=2, default=str), encoding="utf-8")
            log.info("[RUN] report saved: %s", rpt_path)
        except Exception as e:
            log.warning("[RUN] report save failed: %s", e)


# =========================================================================
# DUCKDB MIRROR (was vdf_duckdb_sink.py)
# =========================================================================

def mirror_to_duckdb(output_dir: Path, db_filename: str = "vdf_unified.duckdb",
                     table_prefix: str = "") -> Dict[str, str]:
    """Mirror all *.parquet in output_dir to a DuckDB DB. Skips silently if duckdb absent."""
    if duckdb is None:
        return {"status": "skipped_no_duckdb"}

    output_dir = Path(output_dir)
    if not output_dir.exists():
        return {"status": "no_output_dir"}

    db_path = output_dir / db_filename
    results: Dict[str, str] = {}
    try:
        con = duckdb.connect(str(db_path))
    except Exception as e:
        log.error("[duck] connect failed: %s", e)
        return {"status": f"connect_failed:{e}"}

    try:
        for pq in sorted(output_dir.glob("*.parquet")):
            name = pq.stem.lower()
            if "tmp" in name or "test_dump" in name:
                continue
            table = f"{table_prefix}{name}"
            try:
                con.execute(
                    f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM read_parquet('{pq.as_posix()}')"
                )
                cnt = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                results[table] = f"ok rows={cnt}"
                log.info("[duck] %s <- %s (%d rows)", table, pq.name, cnt)
            except Exception as e:
                results[table] = f"fail: {e}"
                log.warning("[duck] %s failed: %s", table, e)
    finally:
        try: con.close()
        except Exception: pass
    return results


def duckdb_query(output_dir: Path, sql: str, db_filename: str = "vdf_unified.duckdb"):
    if duckdb is None:
        log.error("[duck] duckdb missing")
        return None
    db_path = Path(output_dir) / db_filename
    if not db_path.exists():
        log.error("[duck] db not found: %s", db_path)
        return None
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        return con.execute(sql).fetchdf()
    finally:
        con.close()


# =========================================================================
# MATRIX VIEW GENERATOR (was gen_matrix_view.py)
# =========================================================================

def generate_matrix_views(matrix_path: Path = DEFAULT_MATRIX_PATH) -> Dict[str, Path]:
    """Generate Markdown + CSV views from matrix JSON."""
    config_dir = matrix_path.parent
    out_md = config_dir / "vdf_fetch_matrix.md"
    out_csv = config_dir / "vdf_fetch_matrix.csv"
    data = json.loads(matrix_path.read_text(encoding="utf-8"))

    # Markdown
    md = [
        "# VDF Fetch Matrix\n",
        f"_Schema version: {data['schema_version']}_  \n",
        f"_Build date: {data['build_date']}_\n\n",
        "## Global Settings\n\n",
        "| Setting | Value |\n",
        "|---|---|\n",
    ]
    for k, v in data["global"].items():
        md.append(f"| `{k}` | `{v}` |\n")

    md.append("\n## Unified Headers\n\n")
    # v3 schema: prices_core / tw_chip_extension; v1 schema: core / tw_chip
    hdrs = data.get("unified_headers", {})
    core_key = "prices_core" if "prices_core" in hdrs else "core"
    chip_key = "tw_chip_extension" if "tw_chip_extension" in hdrs else "tw_chip"
    md.append(f"### {core_key}\n")
    md.append("`" + "` | `".join(hdrs.get(core_key, [])) + "`\n\n")
    md.append(f"### {chip_key}\n")
    md.append("`" + "` | `".join(hdrs.get(chip_key, [])) + "`\n\n")
    if "tw_financial" in hdrs:
        md.append("### tw_financial\n")
        md.append("`" + "` | `".join(hdrs["tw_financial"]) + "`\n\n")
    if "macro" in hdrs:
        md.append("### macro\n")
        md.append("`" + "` | `".join(hdrs["macro"]) + "`\n\n")

    md.append("## Categories\n\n")
    md.append("| ID | Name (中文) | Sources | # Items | Output | Frequency |\n")
    md.append("|---|---|---|---|---|---|\n")
    for c in data["categories"]:
        sources = c.get("data_sources") or []
        if not sources:
            pipe = c["source_pipeline"][0] if c.get("source_pipeline") else {}
            sources = [pipe.get("primary", "-")]
        src_str = " / ".join(sources)
        name = c.get("name_zh") or c.get("name") or c["id"]
        items = len(c.get("tickers", [])) + len(c.get("indicators", []))
        md.append(f"| `{c['id']}` | {name} | `{src_str}` | {items} | `{c['output_file']}` | {c.get('update_frequency','daily')} |\n")

    out_md.write_text("".join(md), encoding="utf-8")
    log.info("[VIEW] wrote %s", out_md)

    # CSV
    with open(out_csv, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["category_id", "category_name", "item_type", "item_id", "item_name",
                    "primary_source", "fallback_sources", "output_file", "update_frequency", "extra"])
        for c in data["categories"]:
            pipe = c["source_pipeline"][0] if c["source_pipeline"] else {}
            primary = pipe.get("primary", "")
            fallback = "|".join(pipe.get("fallback", []) or [])
            for t in c.get("tickers", []):
                w.writerow([c["id"], c["name"], "ticker",
                            t.get("ticker", ""), t.get("name", ""),
                            primary, fallback, c["output_file"], c["update_frequency"],
                            json.dumps({k: v for k, v in t.items() if k not in ("ticker", "name")})])
            for ind in c.get("indicators", []):
                key = ind.get("series_id") or ind.get("indicator", "")
                w.writerow([c["id"], c["name"], "indicator",
                            key, ind.get("name", ind.get("indicator", "")),
                            primary, fallback, c["output_file"], c["update_frequency"],
                            json.dumps({k: v for k, v in ind.items() if k not in ("series_id", "indicator", "name")})])
    log.info("[VIEW] wrote %s", out_csv)
    return {"md": out_md, "csv": out_csv}


# =========================================================================
# UTILITIES
# =========================================================================

def parse_date_arg(s: str, default_today: bool = False) -> str:
    if not s or s.upper() == "TODAY":
        return datetime.now().strftime("%Y-%m-%d")
    try:
        s = s.replace("/", "-")
        datetime.strptime(s, "%Y-%m-%d")
        return s
    except Exception:
        if default_today:
            return datetime.now().strftime("%Y-%m-%d")
        raise ValueError(f"Bad date: {s}")


# =========================================================================
# CLI
# =========================================================================

def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="vdf_core",
        description="Veritas Data Forge - unified core (manager + duckdb + matrix views)",
    )
    p.add_argument("--mode", choices=["full", "category", "ticker", "dry-run", "test", "list", "gen-views"], default="full")
    p.add_argument("--category", default=None)
    p.add_argument("--ticker", default=None)
    p.add_argument("--start", default=None)
    p.add_argument("--end", default=None)
    p.add_argument("--output-format", choices=["parquet", "parquet+duckdb"], default="parquet")
    p.add_argument("--matrix", default=str(DEFAULT_MATRIX_PATH))
    p.add_argument("--output-dir", default=None)
    p.add_argument("--temp-dir", default=None)
    p.add_argument("--prod-paths", action="store_true")
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--full-refresh", action="store_true")
    p.add_argument("--skip-chips", action="store_true")
    p.add_argument("--fred-key", default=None, help="FRED API key (overrides env VDF_FRED_API_KEY and matrix default)")
    p.add_argument("--verbose", action="store_true")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_arg_parser().parse_args(argv)
    if args.verbose:
        log.setLevel(logging.DEBUG)

    matrix_path = Path(args.matrix)

    # Mode: gen-views (just regenerate the .md/.csv views, no fetch)
    if args.mode == "gen-views":
        generate_matrix_views(matrix_path)
        return 0

    matrix = FetchMatrix.load(matrix_path)
    log.info("[BOOT] matrix loaded: %d categories", len(matrix.categories))

    # output paths
    if args.prod_paths:
        out_dir = PROD_OUTPUT_DIR
        tmp_dir = PROD_TEMP_DIR
    else:
        out_dir = Path(args.output_dir) if args.output_dir else DEFAULT_OUTPUT_DIR
        tmp_dir = Path(args.temp_dir) if args.temp_dir else DEFAULT_TEMP_DIR
    store = ParquetStore(out_dir, tmp_dir)
    log.info("[BOOT] output=%s temp=%s", out_dir, tmp_dir)

    # dates
    start = args.start or matrix.global_cfg.get("default_start_date", "2010-01-01")
    end_raw = args.end or matrix.global_cfg.get("default_end_date", "TODAY")
    start = parse_date_arg(start)
    end = parse_date_arg(end_raw, default_today=True)

    ctx = {
        "start": start,
        "end": end,
        "output_format": args.output_format,
        # Priority: CLI arg > env (FRED_API_KEY) > matrix default
        "fred_api_key": (
            args.fred_key
            or FRED_API_KEY
            or matrix.global_cfg.get("fred_api_key_default", "")
        ),
        "limit": args.limit,
        "full_refresh": args.full_refresh,
        "skip_chips": args.skip_chips,
        "ticker_override": args.ticker,
        "store": store,
        "matrix": matrix,
    }
    log.info("[BOOT] date range: %s -> %s", start, end)
    log.info("[BOOT] FRED key source: %s", "CLI" if args.fred_key else ("env" if os.environ.get("VDF_FRED_API_KEY") else "matrix-default"))

    register_all_fetchers()
    log.info("[BOOT] registered fetchers: %s", REGISTRY.list())

    # Mode: list
    if args.mode == "list":
        print("Available categories:")
        for c in matrix.categories:
            ready = "[OK]" if REGISTRY.get(c.id) else "[--]"
            print(f"  {ready} {c.id:<14} -> {c.name:<40} -> {c.output_file}")
        return 0

    # Mode: dry-run
    if args.mode == "dry-run":
        log.info("[DRY-RUN] matrix validated")
        for c in matrix.categories:
            ready = "OK" if REGISTRY.get(c.id) else "NO-FETCHER"
            n_items = len(c.tickers) if c.tickers else (len(c.indicators) if c.indicators else 0)
            log.info("  [%s] %-14s items=%d output=%s", ready, c.id, n_items, c.output_file)
        return 0

    # Mode: test
    if args.mode == "test":
        from vdf_tests import run_all_tests
        return run_all_tests(matrix=matrix, store=store, ctx=ctx)

    runner = VDFRunner(matrix=matrix, store=store, ctx=ctx)

    if args.mode == "full":
        runner.run_all()
    elif args.mode == "category":
        if not args.category:
            log.error("--category required when mode=category")
            return 2
        runner.run_one(args.category)
    elif args.mode == "ticker":
        if not args.ticker:
            log.error("--ticker required when mode=ticker")
            return 2
        t = args.ticker.upper()
        if t.endswith(".TW") or t.endswith(".TWO"):
            cat = "tw_stock"
        elif t in ("^TWII", "^TWO"):
            cat = "tw_index"
        elif "=X" in t:
            cat = "fx"
        elif "=F" in t:
            cat = "commodity"
        else:
            cat = "intl_stock"
        ctx["ticker_override"] = args.ticker
        runner.run_one(cat)

    return 0


# Backwards-compatibility aliases (existing code/API server imports these names)
_lazy_register = register_all_fetchers


if __name__ == "__main__":
    sys.exit(main())

# [VIA:ANCHOR:D5_CORE:END]
