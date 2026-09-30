"""VRN 受控實測：原檔唯讀、每輪新目錄、原擷取正主、實際 Parquet + DuckDB。
批次處理成功與欄位驗收分開，不能把無料／失敗標為綠燈。
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====


import argparse
from contextlib import contextmanager
import csv
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys

# def 01_PARAMETERS
HERE = Path(__file__).resolve().parent
OWNER = HERE / "engine" / "VRN_Integrated_ReportDatabase_Engine.py"
VDF = HERE.parent / "VDF"
VERSION = "v0100"
MEMORY_LIMIT = "512MB"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _quote(path):
    return "'" + str(path).replace("'", "''") + "'"


def owner():
    body = load(OWNER, "vrn_probe_owner")
    def write_parquet(df, path, numeric_columns=()):
        import duckdb
        numeric_columns = numeric_columns or (body.BASICINFO_NUMERIC_COLUMNS if "ReportTitle" in df.columns else body.FINANCIALDATA_NUMERIC_COLUMNS)
        typed = body.coerce_frame_types(df, numeric_columns)
        temporary = path.with_suffix(".parquet.tmp")
        try:
            with duckdb.connect(config={"memory_limit": MEMORY_LIMIT}) as con:
                con.register("frame", typed)
                con.execute("COPY frame TO " + _quote(temporary) + " (FORMAT PARQUET, COMPRESSION ZSTD)")
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)
    def read_parquet(path, columns):
        import duckdb
        if not path.exists():
            return body.require_pandas().DataFrame(columns=list(columns))
        with duckdb.connect(config={"memory_limit": MEMORY_LIMIT}) as con:
            df = con.execute("SELECT * FROM read_parquet(?)", [str(path)]).fetchdf()
        if list(df.columns) != list(columns):
            raise ValueError("HEADER_MISMATCH: " + str(path))
        return df
    body.write_parquet_mandatory = write_parquet
    body.read_existing_parquet = read_parquet
    return body


def summary_rc(summary):
    if summary.get("FailedFiles", 0):
        return 1
    if not summary.get("ProcessedFiles") or not summary.get("BasicRowsNew") or summary.get("SkippedOcrFiles", 0):
        return 2
    return 0


def vdf_lookup(root, target):
    store = load(max(VDF.glob("VDF_ParquetStore_v*.py")), "vrn_vdf_store")
    root = Path(root).expanduser().absolute()
    store._owned(root)
    with store._connect(root, read_only=True) as con:
        products = con.execute("SELECT ticker,name FROM products WHERE state='ready' ORDER BY ticker").fetchall()
    rows, unsupported, seen = [], [], {}
    for symbol, name in products:
        match = re.fullmatch(r"([1-9][0-9]{3})\.(TW|TWO)", symbol)
        if not match:
            unsupported.append(symbol)
            continue
        code, market = match.groups()
        if code in seen:
            raise ValueError("VDF→VRN 四碼衝突，不合併市場: " + code)
        seen[code] = symbol
        rows.append((code, name, "TWSE" if market == "TW" else "TPEX", symbol))
    with target.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["Ticker", "Name", "Market", "YF_TICKER"])
        writer.writerows(rows)
    return {"mapped": len(rows), "unsupported": unsupported, "source": str(root), "source_read_only": True,
            "rule": "existing VRN parser: Taiwan 4-digit equities; ETFs/overseas remain unsupported"}


def run(input_path, output, vdf_root=None):
    body = owner()
    source = Path(input_path).expanduser().resolve()
    output = Path(output).expanduser().absolute()
    if not source.exists():
        raise ValueError("INPUT_MISSING")
    if source == output or source.is_dir() and output.is_relative_to(source):
        raise ValueError("輸出目錄不可位於輸入資料內")
    if any(p.is_symlink() for p in [output, *output.parents]):
        raise ValueError("輸出不可含符號連結")
    files = body.scan_input_files(source)
    if not files:
        return {"state": "NODATA", "rc": 2, "processed": 0, "production_acceptance": "NOT_EVALUATED"}
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.mkdir(exist_ok=False)  # 每輪独立，失敗證據保留；不覆寫成功來源。
    mapping = vdf_lookup(vdf_root, output / "VDF_TickerNames.csv") if vdf_root else None
    args = body.build_arg_parser().parse_args(["--input", str(source), "--output", str(output), "--duckdb", "--json"])
    args.online_name_update = False
    args.ticker_ssot = str(output / "VDF_TickerNames.csv") if mapping else ""
    summary = body.process_batch(args)
    unchanged = all(p.exists() and hashlib.sha256(p.read_bytes()).hexdigest() == hashes[str(p)] for p in files)
    rc = max(summary_rc(summary), 0 if unchanged else 1)
    import duckdb
    paths = summary["OutputFiles"]
    with duckdb.connect(paths["DuckDB"], read_only=True) as con:
        headers = {table: con.execute("DESCRIBE " + table).fetchall() for table in ("StockReportBasicInfo", "StockReportFinancialData")}
        counts = {table: con.execute("SELECT count(*) FROM " + table).fetchone()[0] for table in headers}
    if [r[0] for r in headers["StockReportBasicInfo"]] != body.BASICINFO_COLUMNS or [r[0] for r in headers["StockReportFinancialData"]] != body.FINANCIALDATA_COLUMNS:
        rc = 1
    result = {"state": "FAILED" if rc == 1 else "NODATA_OR_PARTIAL" if rc else "EXECUTED_REVIEW_REQUIRED", "rc": rc,
              "summary": summary, "headers": headers, "actual_counts": counts, "input_unchanged": unchanged,
              "vdf_mapping": mapping, "network_enabled": False, "llm_calls": 0,
              "production_acceptance": "NOT_EVALUATED", "field_accuracy": "REVIEW_REQUIRED", "source_sha256": hashes}
    (output / "VRN_PROBE.json").write_text(json.dumps(result, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return result


def main(argv=None):
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[DENY] VCGC entry required")
        return 2
    if argv == ["--selftest"]:
        return load(HERE / "tests" / "test_ReportProbe_v0100.py", "vrn_probe_tests").run_tests(sys.modules[__name__])
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--vdf-root")
    args = parser.parse_args(argv)
    try:
        result = run(args.input, args.output, args.vdf_root)
        print(json.dumps(result, ensure_ascii=False, default=str, indent=1))
        return result["rc"]
    except Exception as exc:
        print(json.dumps({"state": "FAILED", "rc": 1, "error": type(exc).__name__ + ": " + str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
