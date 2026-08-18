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
import contextlib
import importlib
import io
import json
import os
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb


EXPECTED_SUPPORTIVE_MODULES = {
    "VIA_Panorama_AST_RuntimeInjector",
    "VIA_Runtime_Bridge_All_in_One",
    "VIA_SSOT_Unified",
    "VIA_EnvManager",
    "VeritasAegisNexus",
    "VIA_RegistryCore_v1",
    "VeritasCeleritas",
}


def def_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def def_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def def_table_names(connection: duckdb.DuckDBPyConnection) -> set[str]:
    rows = connection.execute(
        "select table_name from information_schema.tables where table_schema='main'"
    ).fetchall()
    return {str(row[0]) for row in rows}


def def_scalar(connection: duckdb.DuckDBPyConnection, sql: str) -> int:
    return int(connection.execute(sql).fetchone()[0])


def def_import_all_supportive_modules(core_root: Path) -> dict[str, Any]:
    os.environ["VIA_SUPPORTIVE_ROOT"] = str(core_root)
    os.chdir(core_root)
    sys.path.insert(0, str(core_root))
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout_buffer), contextlib.redirect_stderr(stderr_buffer):
            panorama = importlib.import_module("VIA_Panorama_AST_RuntimeInjector")
            bridge = importlib.import_module("VIA_Runtime_Bridge_All_in_One")
            context = bridge.def_bootstrap_runtime()
        loaded_names = set(context.loaded_modules)
        loaded_names.update({panorama.__name__, bridge.__name__})
        missing = sorted(EXPECTED_SUPPORTIVE_MODULES - loaded_names)
        errors = {str(key): str(value) for key, value in context.errors.items()}
        state_failures = sorted(
            name for name, detail in context.state.items()
            if isinstance(detail, dict) and detail.get("ok") is False
        )
        ready = not missing and not errors and not state_failures
        return {
            "ready": ready,
            "expected_count": len(EXPECTED_SUPPORTIVE_MODULES),
            "imported_count": len(loaded_names & EXPECTED_SUPPORTIVE_MODULES),
            "expected_modules": sorted(EXPECTED_SUPPORTIVE_MODULES),
            "imported_modules": sorted(loaded_names),
            "missing_modules": missing,
            "module_errors": errors,
            "state_failures": state_failures,
            "captured_stdout": stdout_buffer.getvalue()[-8000:],
            "captured_stderr": stderr_buffer.getvalue()[-8000:],
        }
    except Exception as exc:
        return {
            "ready": False,
            "expected_count": len(EXPECTED_SUPPORTIVE_MODULES),
            "imported_count": 0,
            "expected_modules": sorted(EXPECTED_SUPPORTIVE_MODULES),
            "imported_modules": [],
            "missing_modules": sorted(EXPECTED_SUPPORTIVE_MODULES),
            "module_errors": {"vdf_supportive_import": f"{type(exc).__name__}: {exc}"},
            "state_failures": [],
            "traceback": traceback.format_exc(),
            "captured_stdout": stdout_buffer.getvalue()[-8000:],
            "captured_stderr": stderr_buffer.getvalue()[-8000:],
        }


def def_bootstrap(data_root: Path, run_root: Path, core_root: Path) -> dict[str, Any]:
    manifest_path = data_root / "manifest.json"
    database_path = data_root / "via_marketflow.duckdb"
    required_tables = {"market_daily", "etf_daily", "etf_signals", "stock_price"}
    checks: list[dict[str, Any]] = []
    supportive = def_import_all_supportive_modules(core_root)
    checks.append({
        "check": "all_supportive_modules_imported",
        "ok": bool(supportive.get("ready")),
        "value": supportive.get("imported_count", 0),
        "expected": supportive.get("expected_count", 7),
    })

    manifest = (
        json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest_path.is_file()
        else {}
    )
    data_gate = str(manifest.get("gate", "NO_MANIFEST"))
    gate_ok = data_gate in {"DATA_READY_READ_ONLY_API", "DATA_READY_DEGRADED_READ_ONLY_API"}
    checks.append({"check": "data_gate", "ok": gate_ok, "value": data_gate})
    checks.append({"check": "database_exists", "ok": database_path.is_file(), "value": str(database_path)})

    tables: set[str] = set()
    market_rows = 0
    etf_rows = 0
    pk_duplicates = -1
    placeholder_rows = -1
    database_error = ""
    if database_path.is_file():
        try:
            connection = duckdb.connect(str(database_path), read_only=True)
            try:
                tables = def_table_names(connection)
                missing = sorted(required_tables - tables)
                checks.append({"check": "required_tables", "ok": not missing, "value": sorted(tables), "missing": missing})
                if "market_daily" in tables:
                    market_rows = def_scalar(connection, "select count(*) from market_daily")
                    pk_duplicates = def_scalar(
                        connection,
                        """select count(*) from (
                               select date,ticker,count(*) n from market_daily
                               group by date,ticker having count(*) > 1
                           )"""
                    )
                    placeholder_rows = def_scalar(
                        connection,
                        "select count(*) from market_daily where close is null and adj_close is null"
                    )
                if "etf_daily" in tables:
                    etf_rows = def_scalar(connection, "select count(*) from etf_daily")
            finally:
                connection.close()
        except Exception as exc:
            database_error = f"{type(exc).__name__}: {exc}"
            checks.append({"check": "database_read_only_open", "ok": False, "value": database_error})
    else:
        checks.append({"check": "required_tables", "ok": False, "value": [], "missing": sorted(required_tables)})

    checks.extend([
        {"check": "market_rows", "ok": market_rows > 0, "value": market_rows},
        {"check": "etf_rows", "ok": etf_rows > 0, "value": etf_rows},
        {"check": "market_pk_duplicates", "ok": pk_duplicates == 0, "value": pk_duplicates},
        {"check": "price_placeholder_rows", "ok": placeholder_rows == 0, "value": placeholder_rows},
    ])
    ready = all(bool(row.get("ok")) for row in checks)
    payload = {
        "schema": "via.vdf.runtime.heartbeat.v1",
        "service": "VDF",
        "status": "READY" if ready else "BLOCKED",
        "gate": "VDF_DATAHUB_READY" if ready else "VDF_DATAHUB_FAIL_CLOSED",
        "updated_utc": def_utc_now(),
        "pid": __import__("os").getpid(),
        "mode": "RUN_LOCAL_READ_ONLY",
        "data_root": str(data_root),
        "run_root": str(run_root),
        "market_rows": market_rows,
        "etf_rows": etf_rows,
        "checks": checks,
        "supportive_modules": supportive,
        "supportive_modules_all_imported": bool(supportive.get("ready")),
        "canonical_mutation": False,
        "database_write": False,
        "error": database_error,
    }
    return payload


def def_main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--core-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    payload = def_bootstrap(Path(args.data_root), Path(args.run_root), Path(args.core_root))
    def_write_json(Path(args.output), payload)
    print(json.dumps(payload, ensure_ascii=False))
    return 0 if payload["status"] == "READY" else 2


if __name__ == "__main__":
    raise SystemExit(def_main())