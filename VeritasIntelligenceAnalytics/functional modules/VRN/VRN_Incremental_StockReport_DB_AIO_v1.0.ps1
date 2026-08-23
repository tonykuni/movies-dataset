#requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# =============================================================================
# def PARAMS
# =============================================================================
$P_VRN_BASE = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN"
$P_SUPPORTIVE_BASE = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module"
$P_PYTHON = "C:\Users\tonyk\envs\via_core_312\Scripts\python.exe"

$P_VERSION = "VRN_INCREMENTAL_STOCKREPORT_DB_AIO_v1.0"
$P_RUN_STAMP = Get-Date -Format "yyyyMMdd_HHmmss"
$P_OPEN_HTML = $true
$P_KEEP_POWERSHELL_OPEN = $true
$P_PROGRESS_ID = 961

# Output formats: parquet REQUIRED (canonical) + duckdb + csv(utf-8-sig). json/gsheet optional.
$P_EMIT_JSON = $true
$P_EMIT_GSHEET_STUB = $true

# No-Hydra: single writer, single upsert path, append-only. No parser-core rewrite, no delete.
$P_PARSER_CORE_REWRITE = $false
$P_DELETE = $false
$P_FULL_22_RERUN = $false

$P_MODULE_PATH = Join-Path $P_SUPPORTIVE_BASE "VIS_VRN_IncrementalDBStore_v0100.py"
# Canonical DB dir (PERSISTS across runs = the incremental store).
$P_DB_DIR = Join-Path $P_VRN_BASE "_vrn_stockreport_db"

# 8 geometry files: their financial rows come from recon GREEN, NOT raw matrix (no double-write).
$P_TARGET_SUBSTRINGS = @(
    "凱基投顧_鋼鐵產業", "凱基投顧_1476", "GS-2317", "GS-2382",
    "JP-2330", "6933_AMAX", "兆豐晨會報告(二)", "UBS-Asia Hardware Insights"
)

# =============================================================================
# def RESET
# =============================================================================
Get-ChildItem Function:\def_* -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue

# =============================================================================
# def UTILITIES
# =============================================================================
function def_Log {
    param([string]$Level, [string]$Message)
    $ts = Get-Date -Format "HH:mm:ss.fff"
    $color = "Gray"
    if ($Level -eq "BOOT") { $color = "Cyan" }
    elseif ($Level -eq "OK") { $color = "Green" }
    elseif ($Level -eq "WARN") { $color = "Yellow" }
    elseif ($Level -eq "ERR") { $color = "Red" }
    Write-Host "[$ts] [$Level] $Message" -ForegroundColor $color
}

function def_Progress {
    param([int]$Percent, [string]$Stage, [string]$Message)
    if ($Percent -lt 0) { $Percent = 0 }
    if ($Percent -gt 100) { $Percent = 100 }
    Write-Progress -Id $P_PROGRESS_ID -Activity "VRN Incremental StockReport DB" -Status "$Stage · $Message" -PercentComplete $Percent
    Write-Host ("[{0,3}%] {1} :: {2}" -f $Percent, $Stage, $Message) -ForegroundColor DarkCyan
}

function def_EnsureDir {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function def_HtmlEncode {
    param([object]$Value)
    if ($null -eq $Value) { return "" }
    return [System.Net.WebUtility]::HtmlEncode([string]$Value)
}

function def_ImportCsvSafe {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return @() }
    try { return @(Import-Csv -LiteralPath $Path -Encoding UTF8) }
    catch { try { return @(Import-Csv -LiteralPath $Path) } catch { return @() } }
}

function def_WriteJson {
    param([object]$Data, [string]$Path)
    $Data | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $Path -Encoding UTF8
}

function def_FindLatestCsvByName {
    param([string]$NamePattern)
    $files = @(Get-ChildItem -LiteralPath $P_VRN_BASE -Recurse -File -Filter "*.csv" -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like $NamePattern } |
        Sort-Object LastWriteTime -Descending)
    if ($files.Count -gt 0) { return $files[0].FullName }
    return ""
}

function def_NewFallbackDecision {
    param([object]$Runtime)
    return [pscustomobject]@{
        Light = $Runtime.Light; Risk = $Runtime.Risk; Status = $Runtime.Status
        ModuleSelfCheck = $false; BatchId = $P_RUN_STAMP
        InfoActiveRows = 0; InfoTotalRows = 0; InfoInserted = 0; InfoSkipped = 0; InfoConflicts = 0
        FinActiveRows = 0; FinTotalRows = 0; FinInserted = 0; FinSkipped = 0; FinConflicts = 0
        PanoramaHigh = 0; PanoramaYellow = 0
        ParquetWritten = $false; DuckDbWritten = $false; CsvWritten = $false
        ParserCoreRewrite = $false; Delete = $false
    }
}

# =============================================================================
# def WRITE MODULE
# =============================================================================
function def_WriteModule {
    param([string]$Path)
    def_Progress 12 "STEP 1/4 Module" "新增 IncrementalDBStore supportive module"

    $py = @'
# -*- coding: utf-8 -*-
"""VIS_VRN_IncrementalDBStore_v0100 - incremental, append-only maintenance of
StockReportInfo.parquet + StockReportFinancialData.parquet.
parquet = canonical (required); duckdb + csv(utf-8-sig) derived; json optional.
Single writer, single upsert path, atomic temp->replace. No Hydra. No parser-core rewrite."""
from __future__ import annotations
import hashlib, os, re
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

INFO_COLS = ["product_id","layer","ticker","company","broker","analyst","rating",
             "target_price","report_date","missing_fields","source_file","source_page",
             "value_hash","revision","status","batch_id","ingest_ts","recon_note"]
FIN_COLS  = ["product_id","layer","ticker","account","period","fiscal_year","value",
             "col_ref","forecast_flag","bug_class","row_status","source_file","source_page",
             "value_hash","revision","status","batch_id","ingest_ts","recon_note"]

def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def _s(x: Any) -> str:
    return re.sub(r"\s+", " ", str(x if x is not None else "").strip())

def _h8(x: str) -> str:
    return hashlib.sha256(_s(x).encode("utf-8")).hexdigest()[:8]

def product_id_7seg(segments: List[Any]) -> str:
    segs = (list(segments) + [""] * 7)[:7]
    return "-".join(_h8(s) for s in segs)

def value_hash(mutable: List[Any]) -> str:
    return hashlib.sha256("||".join(_s(m) for m in mutable).encode("utf-8")).hexdigest()[:16]

def build_info_rows(basic_rows, batch_id):
    out = []
    for r in basic_rows:
        sf = _s(r.get("SourceFile")); tk = _s(r.get("Ticker"))
        pid = product_id_7seg(["TW.Equity.Info", sf, tk, _s(r.get("SourcePage")),
                               _s(r.get("Company")), _s(r.get("Broker")), _s(r.get("ReportDate"))])
        mutable = [r.get("Company"), r.get("Broker"), r.get("Analyst"), r.get("Rating"),
                   r.get("TargetPrice"), r.get("ReportDate"), r.get("MissingFields")]
        out.append({"product_id": pid, "layer": "TW.Equity.Info", "ticker": tk,
                    "company": _s(r.get("Company")), "broker": _s(r.get("Broker")),
                    "analyst": _s(r.get("Analyst")), "rating": _s(r.get("Rating")),
                    "target_price": _s(r.get("TargetPrice")), "report_date": _s(r.get("ReportDate")),
                    "missing_fields": _s(r.get("MissingFields")), "source_file": sf,
                    "source_page": _s(r.get("SourcePage")), "value_hash": value_hash(mutable),
                    "revision": 1, "status": "ACTIVE", "batch_id": batch_id, "ingest_ts": _now(),
                    "recon_note": _s(r.get("SuggestedFix"))[:160]})
    return out

def build_fin_rows(green_rows, batch_id):
    out = []
    for r in green_rows:
        sf = _s(r.get("SourceFile")); tk = _s(r.get("Ticker"))
        acct = _s(r.get("AccountReconstructed") or r.get("Account"))
        per = _s(r.get("PeriodNormalized")); fy = _s(r.get("FiscalYear"))
        col = _s(r.get("ColRef")) or per or fy or "COL_1"
        val = _s(r.get("ValueReconstructed") or r.get("Value"))
        pid = product_id_7seg(["TW.Equity.Financial", sf, tk, acct, per, fy, col])
        out.append({"product_id": pid, "layer": "TW.Equity.Financial", "ticker": tk,
                    "account": acct, "period": per, "fiscal_year": fy, "value": val,
                    "col_ref": col, "forecast_flag": _s(r.get("ForecastFlag")),
                    "bug_class": _s(r.get("BugClass")), "row_status": _s(r.get("RowStatus")),
                    "source_file": sf, "source_page": _s(r.get("SourcePage")),
                    "value_hash": value_hash([val, r.get("ForecastFlag")]),
                    "revision": 1, "status": "ACTIVE", "batch_id": batch_id, "ingest_ts": _now(),
                    "recon_note": _s(r.get("ReconNote"))[:160]})
    return out

_MERGED_KW = ["營收","毛利","營業利益","稅前","稅後","每股盈餘","毛利率","營利率","淨利率"]

def is_clean_matrix_fin_row(r):
    tk = _s(r.get("Ticker"))
    acct = _s(r.get("AccountNormalized")) or _s(r.get("AccountRaw"))
    valn = _s(r.get("ValueNormalized")); valr = _s(r.get("ValueRaw")); val = valn or valr
    if not tk or not acct or not val:
        return False
    if "e+" in valn.lower() or len(re.sub(r"\D", "", valn)) >= 15:
        return False
    if sum(1 for kw in _MERGED_KW if kw in acct) >= 2:
        return False
    if re.search(r"\d[\d,\.]*\s+\d[\d,\.]*\s+\d", valr):
        return False
    try:
        float(val.replace(",", "").replace("%", "").replace("(", "-").replace(")", ""))
    except Exception:
        return False
    return True

def build_fin_rows_from_matrix(matrix_rows, batch_id, exclude_substrings):
    out = []
    for r in matrix_rows:
        sf = _s(r.get("SourceFile"))
        if any(x in sf for x in exclude_substrings):
            continue
        if not is_clean_matrix_fin_row(r):
            continue
        tk = _s(r.get("Ticker"))
        acct = _s(r.get("AccountNormalized")) or _s(r.get("AccountRaw"))
        per = _s(r.get("PeriodNormalized")); fy = _s(r.get("FiscalYear"))
        col = per or fy or "COL_1"
        val = _s(r.get("ValueNormalized")) or _s(r.get("ValueRaw"))
        pid = product_id_7seg(["TW.Equity.Financial", sf, tk, acct, per, fy, col])
        out.append({"product_id": pid, "layer": "TW.Equity.Financial", "ticker": tk,
                    "account": acct, "period": per, "fiscal_year": fy, "value": val,
                    "col_ref": col, "forecast_flag": "", "bug_class": "CLEAN_MATRIX",
                    "row_status": _s(r.get("ValidationStatus")), "source_file": sf,
                    "source_page": _s(r.get("SourcePage")), "value_hash": value_hash([val]),
                    "revision": 1, "status": "ACTIVE", "batch_id": batch_id, "ingest_ts": _now(),
                    "recon_note": "clean matrix row (no geometry defect)"})
    return out

def upsert(existing, incoming, cols):
    if existing is None or existing.empty:
        existing = pd.DataFrame(columns=cols)
    existing = existing.reindex(columns=cols)
    act = existing[existing["status"] == "ACTIVE"] if not existing.empty else existing
    active_vh = dict(zip(act.get("product_id", []), act.get("value_hash", [])))
    active_rev = dict(zip(act.get("product_id", []), act.get("revision", [])))
    stats = {"insert": 0, "skip": 0, "conflict": 0}
    ledger = []; new_rows = []; supersede_ids = []
    seen = {}
    for row in incoming:
        seen[row["product_id"]] = row
    for pid, row in seen.items():
        if pid not in active_vh:
            row["revision"] = 1; row["status"] = "ACTIVE"; new_rows.append(row); stats["insert"] += 1
        elif str(active_vh[pid]) == str(row["value_hash"]):
            stats["skip"] += 1
        else:
            old_rev = int(active_rev.get(pid, 1) or 1)
            row["revision"] = old_rev + 1; row["status"] = "ACTIVE"
            new_rows.append(row); supersede_ids.append(pid); stats["conflict"] += 1
            ledger.append({"product_id": pid, "old_revision": old_rev, "new_revision": old_rev + 1,
                           "old_value_hash": str(active_vh[pid]), "new_value_hash": str(row["value_hash"]),
                           "batch_id": row["batch_id"], "ts": row["ingest_ts"]})
    if supersede_ids and not existing.empty:
        m = (existing["product_id"].isin(supersede_ids)) & (existing["status"] == "ACTIVE")
        existing.loc[m, "status"] = "SUPERSEDED"
    merged = pd.concat([existing, pd.DataFrame(new_rows, columns=cols)], ignore_index=True) if new_rows else existing
    return merged.reindex(columns=cols), stats, ledger

def write_parquet_atomic(df, path, cols):
    df = df.reindex(columns=cols)
    df = df.astype(str).where(pd.notnull(df), "")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    pq.write_table(pa.Table.from_pandas(df, preserve_index=False), tmp)
    os.replace(tmp, path)

def read_parquet_safe(path, cols):
    if not os.path.isfile(path):
        return pd.DataFrame(columns=cols)
    try:
        return pq.read_table(path).to_pandas().reindex(columns=cols)
    except Exception:
        return pd.DataFrame(columns=cols)

def panoramic_analysis(df, cols, id_fields, table):
    issues = []
    def add(rnd, cat, klass, sev, count, note):
        issues.append({"Light": "🔴" if sev == "HIGH" else ("🟡" if sev == "YELLOW" else "🟢"),
                       "Table": table, "Round": rnd, "Category": cat, "FixClass": klass,
                       "Severity": sev, "Count": count, "Note": note})
    missing_cols = [c for c in cols if c not in df.columns]
    add("R1_FULL", "SCHEMA_CONFORMANCE", "PARALLEL", "HIGH" if missing_cols else "GREEN",
        len(missing_cols), ("missing: " + ",".join(missing_cols)) if missing_cols else "all columns present")
    null_id = int(df[id_fields].apply(lambda r: any(_s(v) == "" for v in r), axis=1).sum()) if not df.empty else 0
    add("R1_FULL", "NULL_IDENTITY_FIELDS", "PARALLEL", "YELLOW" if null_id else "GREEN", null_id,
        "rows with an empty identity field" if null_id else "no empty identity fields")
    act = df[df["status"] == "ACTIVE"] if not df.empty else df
    dup_active = int(act["product_id"].duplicated().sum()) if not act.empty else 0
    add("R2_SEQ", "DUP_ACTIVE_PRODUCT_ID", "SEQUENTIAL", "HIGH" if dup_active else "GREEN", dup_active,
        "duplicate ACTIVE product_id" if dup_active else "1 ACTIVE per product_id")
    rev_bad = int((pd.to_numeric(df["revision"], errors="coerce").fillna(0) < 1).sum()) if not df.empty else 0
    add("R2_SEQ", "REVISION_MONOTONIC", "SEQUENTIAL", "YELLOW" if rev_bad else "GREEN", rev_bad,
        "revision < 1" if rev_bad else "revisions >= 1")
    add("R3_CLEAN", "TOTAL_ROWS", "CLEANUP", "GREEN", int(len(df)), "total rows incl. revision history")
    add("R3_CLEAN", "ACTIVE_ROWS", "CLEANUP", "GREEN", int(len(act)), "active rows (current truth)")
    return issues

def self_check():
    b1 = build_fin_rows([{"SourceFile":"f","Ticker":"2317","AccountReconstructed":"Revenues (NT$m)",
                          "PeriodNormalized":"2025","FiscalYear":"2025","ColRef":"2025","ValueReconstructed":"895,709"}], "B1")
    df, s1, _ = upsert(pd.DataFrame(columns=FIN_COLS), b1, FIN_COLS)
    df, s2, _ = upsert(df, b1, FIN_COLS)
    b3 = build_fin_rows([{"SourceFile":"f","Ticker":"2317","AccountReconstructed":"Revenues (NT$m)",
                          "PeriodNormalized":"2025","FiscalYear":"2025","ColRef":"2025","ValueReconstructed":"999,999"}], "B3")
    df, s3, led = upsert(df, b3, FIN_COLS)
    act = df[df["status"] == "ACTIVE"]
    ok = (s1["insert"] == 1 and s2["skip"] == 1 and s3["conflict"] == 1 and len(act) == 1
          and act.iloc[0]["value"] == "999,999" and int(act.iloc[0]["revision"]) == 2 and len(led) == 1)
    return {"hard_pass": bool(ok), "s1": s1, "s2": s2, "s3": s3,
            "active_rows": int(len(act)), "total_rows": int(len(df))}

if __name__ == "__main__":
    print(self_check())
'@
    Set-Content -LiteralPath $Path -Value $py -Encoding UTF8
}

# =============================================================================
# def WRITE RUNNER
# =============================================================================
function def_WriteRunnerPy {
    param([string]$Path, [string]$RunDir, [string]$DbDir,
          [string]$BasicCsv, [string]$MatrixCsv, [string]$ReconGreenCsv)

    $py = @'
# -*- coding: utf-8 -*-
from __future__ import annotations
import csv, importlib.util, json, os, sys
import pandas as pd

MODULE_PATH = r"__MODULE_PATH__"
RUN_DIR     = r"__RUN_DIR__"
DB_DIR      = r"__DB_DIR__"
BASIC_CSV   = r"__BASIC_CSV__"
MATRIX_CSV  = r"__MATRIX_CSV__"
RECON_CSV   = r"__RECON_CSV__"
BATCH_ID    = r"__BATCH_ID__"
EMIT_JSON   = (r"__EMIT_JSON__" == "True")
EMIT_GSHEET = (r"__EMIT_GSHEET__" == "True")
TARGETS     = __TARGETS__

def imp(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import " + path)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m; spec.loader.exec_module(m); return m

def read_csv(p):
    if not p or not os.path.isfile(p): return []
    with open(p, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def append_ledger(path, rows):
    if not rows: return
    exists = os.path.isfile(path)
    fields = ["product_id","old_revision","new_revision","old_value_hash","new_value_hash","batch_id","ts","table"]
    with open(path, "a", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if not exists: w.writeheader()
        for r in rows: w.writerow(r)

def main():
    os.makedirs(RUN_DIR, exist_ok=True); os.makedirs(DB_DIR, exist_ok=True)
    M = imp(MODULE_PATH, "VIS_VRN_IncrementalDBStore_v0100_runtime")
    sc = M.self_check()

    info_parquet = os.path.join(DB_DIR, "StockReportInfo.parquet")
    fin_parquet  = os.path.join(DB_DIR, "StockReportFinancialData.parquet")

    basic = read_csv(BASIC_CSV); matrix = read_csv(MATRIX_CSV); recon = read_csv(RECON_CSV)

    # ---- SEQUENTIAL chain: load -> id -> upsert -> write-back -> derive ----
    # INFO
    info_in = M.build_info_rows(basic, BATCH_ID)
    df_info = M.read_parquet_safe(info_parquet, M.INFO_COLS)
    df_info, si, li = M.upsert(df_info, info_in, M.INFO_COLS)
    M.write_parquet_atomic(df_info, info_parquet, M.INFO_COLS)
    for r in li: r["table"] = "StockReportInfo"

    # FINANCIAL = clean matrix rows (excl. 8 geometry files) + recon GREEN fixes
    fin_in = M.build_fin_rows_from_matrix(matrix, BATCH_ID, TARGETS) + M.build_fin_rows(recon, BATCH_ID)
    df_fin = M.read_parquet_safe(fin_parquet, M.FIN_COLS)
    df_fin, sf, lf = M.upsert(df_fin, fin_in, M.FIN_COLS)
    M.write_parquet_atomic(df_fin, fin_parquet, M.FIN_COLS)
    for r in lf: r["table"] = "StockReportFinancialData"

    append_ledger(os.path.join(DB_DIR, "VRN_StockReport_ConflictLedger.csv"), li + lf)

    # ---- derive duckdb (canonical from parquet) ----
    duck_ok = False
    try:
        import duckdb
        dbp = os.path.join(DB_DIR, "VRN_StockReports.duckdb")
        con = duckdb.connect(dbp)
        con.execute("CREATE OR REPLACE TABLE StockReportInfo AS SELECT * FROM read_parquet(?)", [info_parquet])
        con.execute("CREATE OR REPLACE TABLE StockReportFinancialData AS SELECT * FROM read_parquet(?)", [fin_parquet])
        con.execute("CREATE OR REPLACE VIEW StockReportInfo_Active AS SELECT * FROM StockReportInfo WHERE status='ACTIVE'")
        con.execute("CREATE OR REPLACE VIEW StockReportFinancialData_Active AS SELECT * FROM StockReportFinancialData WHERE status='ACTIVE'")
        con.close(); duck_ok = True
    except Exception as e:
        print("duckdb skipped:", e)

    # ---- derive csv (utf-8-sig) snapshots into RUN_DIR ----
    rt_info = M.read_parquet_safe(info_parquet, M.INFO_COLS)
    rt_fin  = M.read_parquet_safe(fin_parquet,  M.FIN_COLS)
    rt_info.to_csv(os.path.join(RUN_DIR, "StockReportInfo.csv"), index=False, encoding="utf-8-sig")
    rt_fin.to_csv(os.path.join(RUN_DIR, "StockReportFinancialData.csv"), index=False, encoding="utf-8-sig")

    if EMIT_JSON:
        rt_info[rt_info["status"]=="ACTIVE"].to_json(os.path.join(RUN_DIR, "StockReportInfo_Active.json"),
                                                      orient="records", force_ascii=False)
        rt_fin[rt_fin["status"]=="ACTIVE"].to_json(os.path.join(RUN_DIR, "StockReportFinancialData_Active.json"),
                                                    orient="records", force_ascii=False)
    if EMIT_GSHEET:
        with open(os.path.join(RUN_DIR, "GSHEET_STUB.txt"), "w", encoding="utf-8") as f:
            f.write("GSheet push stub: bridge-pluggable via gspread. Not executed (no creds bound). "
                    "Push StockReportInfo_Active / StockReportFinancialData_Active CSVs when service-account is configured.")

    # ---- CLEANUP: 3-round panoramic on both tables ----
    pano = (M.panoramic_analysis(rt_info, M.INFO_COLS, ["product_id","ticker","source_file","source_page"], "StockReportInfo")
            + M.panoramic_analysis(rt_fin, M.FIN_COLS, ["product_id","ticker","account","col_ref"], "StockReportFinancialData"))
    pano_high = sum(1 for x in pano if x["Severity"] == "HIGH")
    pano_yellow = sum(1 for x in pano if x["Severity"] == "YELLOW")
    pd.DataFrame(pano).to_csv(os.path.join(RUN_DIR, "VRN_StockReport_Panorama.csv"), index=False, encoding="utf-8-sig")

    ia = int((rt_info["status"]=="ACTIVE").sum()); fa = int((rt_fin["status"]=="ACTIVE").sum())
    risk = "GREEN"; status = "STOCKREPORT_DB_INCREMENTAL_OK"
    if not sc.get("hard_pass", False) or pano_high > 0:
        risk, status = "HIGH", "STOCKREPORT_DB_PANORAMA_HIGH"
    elif pano_yellow > 0:
        risk, status = "YELLOW", "STOCKREPORT_DB_REVIEW"

    summary = {"Light": "🔴" if risk=="HIGH" else ("🟡" if risk=="YELLOW" else "🟢"),
               "Risk": risk, "Status": status, "ModuleSelfCheck": bool(sc.get("hard_pass", False)),
               "BatchId": BATCH_ID,
               "InfoActiveRows": ia, "InfoTotalRows": int(len(rt_info)),
               "InfoInserted": si["insert"], "InfoSkipped": si["skip"], "InfoConflicts": si["conflict"],
               "FinActiveRows": fa, "FinTotalRows": int(len(rt_fin)),
               "FinInserted": sf["insert"], "FinSkipped": sf["skip"], "FinConflicts": sf["conflict"],
               "PanoramaHigh": pano_high, "PanoramaYellow": pano_yellow,
               "ParquetWritten": True, "DuckDbWritten": duck_ok, "CsvWritten": True,
               "JsonWritten": bool(EMIT_JSON), "GSheetStub": bool(EMIT_GSHEET),
               "ParserCoreRewrite": False, "Delete": False}

    pd.DataFrame([summary]).to_csv(os.path.join(RUN_DIR, "VRN_StockReport_DB_Summary.csv"), index=False, encoding="utf-8-sig")
    with open(os.path.join(RUN_DIR, "VRN_StockReport_DB_AIO.json"), "w", encoding="utf-8") as f:
        json.dump({"Summary": summary, "SelfCheck": sc, "Panorama": pano,
                   "ConflictLedgerThisRun": li + lf,
                   "Canonical": {"InfoParquet": info_parquet, "FinParquet": fin_parquet}},
                  f, ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
'@
    $py = $py.Replace("__MODULE_PATH__", $P_MODULE_PATH)
    $py = $py.Replace("__RUN_DIR__", $RunDir)
    $py = $py.Replace("__DB_DIR__", $DbDir)
    $py = $py.Replace("__BASIC_CSV__", $BasicCsv)
    $py = $py.Replace("__MATRIX_CSV__", $MatrixCsv)
    $py = $py.Replace("__RECON_CSV__", $ReconGreenCsv)
    $py = $py.Replace("__BATCH_ID__", $P_RUN_STAMP)
    $py = $py.Replace("__EMIT_JSON__", [string]$P_EMIT_JSON)
    $py = $py.Replace("__EMIT_GSHEET__", [string]$P_EMIT_GSHEET_STUB)
    $py = $py.Replace("__TARGETS__", (($P_TARGET_SUBSTRINGS | ForEach-Object { '"' + $_ + '"' }) -join ", " | ForEach-Object { "[$_]" }))
    Set-Content -LiteralPath $Path -Value $py -Encoding UTF8
}

# =============================================================================
# def RUN PYTHON
# =============================================================================
function def_RunPython {
    param([string]$RunnerPy)
    def_Progress 55 "STEP 3/4 Ingest" "增量 upsert → parquet / duckdb / csv"

    if (-not (Test-Path -LiteralPath $P_PYTHON -PathType Leaf)) {
        return [pscustomobject]@{ Light = "🔴"; Risk = "HIGH"; Status = "PYTHON_MISSING"; ExitCode = -1; Stdout = ""; Stderr = "Python missing: $P_PYTHON" }
    }

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $P_PYTHON
    $psi.Arguments = "`"$RunnerPy`""
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.StandardOutputEncoding = [System.Text.Encoding]::UTF8
    $psi.StandardErrorEncoding = [System.Text.Encoding]::UTF8

    $p = New-Object System.Diagnostics.Process
    $p.StartInfo = $psi
    [void]$p.Start()
    # LL#27: drain both pipes async before WaitForExit.
    $outTask = $p.StandardOutput.ReadToEndAsync()
    $errTask = $p.StandardError.ReadToEndAsync()
    $p.WaitForExit()
    $stdout = $outTask.GetAwaiter().GetResult()
    $stderr = $errTask.GetAwaiter().GetResult()

    $risk = "GREEN"; $status = "PASS"
    if ($p.ExitCode -ne 0 -or $stdout -match '"Risk"\s*:\s*"HIGH"') { $risk = "HIGH"; $status = "FAIL" }
    elseif ($stdout -match '"Risk"\s*:\s*"YELLOW"') { $risk = "YELLOW"; $status = "REVIEW" }

    $lt = "🟢"
    if ($risk -eq "HIGH") { $lt = "🔴" } elseif ($risk -eq "YELLOW") { $lt = "🟡" }
    return [pscustomobject]@{ Light = $lt; Risk = $risk; Status = $status; ExitCode = $p.ExitCode; Stdout = $stdout; Stderr = $stderr }
}

# =============================================================================
# def HTML
# =============================================================================
function def_TableHtml {
    param([string]$Title, [object[]]$Rows, [int]$Limit = 500)
    $html = "<section class='card'><h2>$(def_HtmlEncode $Title)</h2>"
    if ($null -eq $Rows -or $Rows.Count -eq 0) { return ($html + "<div class='empty'>No rows</div></section>") }
    $take = @($Rows | Select-Object -First $Limit)
    $props = @($take[0].PSObject.Properties.Name)
    $html += "<div class='tableWrap'><table><thead><tr>"
    foreach ($p in $props) {
        $cls = ""
        if ($p -match "Note|File|Account|Value|Status|Category|Stdout|Stderr|product|recon") { $cls = " class='textCol'" }
        $html += "<th$cls>$(def_HtmlEncode $p)</th>"
    }
    $html += "</tr></thead><tbody>"
    foreach ($r in $take) {
        $sev = "GREEN"
        if ($r.PSObject.Properties.Name -contains "Severity") { $sev = [string]$r.Severity }
        elseif ($r.PSObject.Properties.Name -contains "Risk") { $sev = [string]$r.Risk }
        $trCls = if ($sev -eq "HIGH") { " class='riskHigh'" } elseif ($sev -eq "YELLOW") { " class='riskYellow'" } else { " class='riskGreen'" }
        $html += "<tr$trCls>"
        foreach ($p in $props) {
            $cls = ""
            if ($p -match "Note|File|Account|Value|Status|Category|Stdout|Stderr|product|recon") { $cls = " class='textCol'" }
            $v = ""
            if ($r.PSObject.Properties.Name -contains $p) { $v = $r.$p }
            $html += "<td$cls>$(def_HtmlEncode $v)</td>"
        }
        $html += "</tr>"
    }
    $html += "</tbody></table></div>"
    if ($Rows.Count -gt $Limit) { $html += "<div class='note'>Showing first $Limit of $($Rows.Count). Full CSV exported.</div>" }
    return ($html + "</section>")
}

function def_WriteHtml {
    param([string]$Path, [object]$Decision, [object[]]$RuntimeRows, [object[]]$SummaryRows,
          [object[]]$PanoramaRows, [object[]]$LedgerRows)
    $generated = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8"/>
<title>$P_VERSION</title>
<style>
body{font-family:Arial,'Microsoft JhengHei',sans-serif;background:#f5f4f0;color:#1a1a1a;margin:0}
.header{padding:24px 30px;background:linear-gradient(135deg,#1a1a1a,#3a3a3a);color:#f5f4f0;border-bottom:3px solid #c9a227}
.wrap{padding:20px 28px 40px}
.kpi{display:grid;grid-template-columns:repeat(8,minmax(108px,1fr));gap:12px;margin-bottom:18px}
.box,.card{background:#fff;border:1px solid #e2ddd2;border-radius:16px;padding:14px;box-shadow:0 8px 22px rgba(26,26,26,.05)}
.label{font-size:11px;color:#8a8275;text-transform:uppercase;letter-spacing:.5px}.value{font-size:20px;font-weight:800;margin-top:6px;word-break:break-word}
.card{margin:14px 0}.card h2{margin:0 0 12px;font-size:17px}
.tableWrap{overflow:auto;border:1px solid #e2ddd2;border-radius:12px;max-height:680px}
table{border-collapse:separate;border-spacing:0;width:100%;min-width:1200px;font-size:12px}
th{position:sticky;top:0;background:#efeae0;color:#3a3a3a;padding:8px 10px;border-bottom:1px solid #e2ddd2;text-align:center;vertical-align:top}
td{padding:8px 10px;border-bottom:1px solid #f0ece3;vertical-align:top;text-align:center}
.textCol{text-align:left!important;min-width:200px;max-width:640px;word-break:break-word;white-space:normal}
.riskHigh td{background:#fdecea}.riskYellow td{background:#fdf6e3}.riskGreen td{background:#eef7ed}
.note,.empty{color:#8a8275;padding-top:10px;font-size:12px}
.footer{margin-top:24px;color:#8a8275;font-size:12px}
</style>
</head>
<body>
<div class="header">
  <div style="font-size:22px;font-weight:800">$P_VERSION</div>
  <div style="margin-top:6px">VERITAS INTELLIGENCE ANALYTICS · Incremental append-only StockReport DB · parquet canonical + duckdb + csv(utf-8-sig) · Generated $generated</div>
</div>
<div class="wrap">
<div class="kpi">
<div class="box"><div class="label">Status</div><div class="value">$($Decision.Status)</div></div>
<div class="box"><div class="label">Risk</div><div class="value">$($Decision.Risk)</div></div>
<div class="box"><div class="label">Batch</div><div class="value">$($Decision.BatchId)</div></div>
<div class="box"><div class="label">Info Active</div><div class="value">$($Decision.InfoActiveRows)</div></div>
<div class="box"><div class="label">Fin Active</div><div class="value">$($Decision.FinActiveRows)</div></div>
<div class="box"><div class="label">Inserted I/F</div><div class="value">$($Decision.InfoInserted)/$($Decision.FinInserted)</div></div>
<div class="box"><div class="label">Conflicts I/F</div><div class="value">$($Decision.InfoConflicts)/$($Decision.FinConflicts)</div></div>
<div class="box"><div class="label">Pano H/Y</div><div class="value">$($Decision.PanoramaHigh)/$($Decision.PanoramaYellow)</div></div>
</div>
"@
    $html += def_TableHtml "def_00_Runtime" $RuntimeRows 6
    $html += def_TableHtml "def_01_Summary" $SummaryRows 10
    $html += def_TableHtml "def_02_Panorama (3-round: R1 parallel · R2 sequential · R3 cleanup)" $PanoramaRows 200
    $html += def_TableHtml "def_03_Conflict_Ledger (this run · append-only revision history)" $LedgerRows 300
    $html += @"
<div class="footer">
Veritas Intelligence Analytics │ AI-Augmented Investment Intelligence for Smarter Decisions and Deeper Insight
</div>
</div></body></html>
"@
    Set-Content -LiteralPath $Path -Value $html -Encoding UTF8
}

# =============================================================================
# def MAIN
# =============================================================================
function def_Main {
    def_Log "BOOT" "$P_VERSION started"
    if ($P_PARSER_CORE_REWRITE -or $P_DELETE -or $P_FULL_22_RERUN) {
        throw "NoHydra gate failed: parser-core/delete/full-rerun flag enabled."
    }

    $outRoot = Join-Path $P_VRN_BASE "_vrn_stockreport_db_runs"
    $runDir = Join-Path $outRoot "RUN_$P_RUN_STAMP"
    def_EnsureDir $outRoot
    def_EnsureDir $runDir
    def_EnsureDir $P_DB_DIR
    def_EnsureDir $P_SUPPORTIVE_BASE
    def_Log "BOOT" "RunDir: $runDir"
    def_Log "BOOT" "Canonical DB dir (incremental): $P_DB_DIR"

    def_WriteModule -Path $P_MODULE_PATH

    def_Progress 30 "STEP 2/4 Discover" "定位 BasicInfo / FinancialData matrix + GeometryRecon GREEN"
    $basicCsv = def_FindLatestCsvByName "VRN_BasicInfo_Matrix.csv"
    $matrixCsv = def_FindLatestCsvByName "VRN_FinancialData_Matrix.csv"
    $reconCsv = def_FindLatestCsvByName "VRN_GeometryRecon_DBReadyGreen.csv"
    def_Log "OK" "BasicInfo: $basicCsv"
    def_Log "OK" "FinancialData Matrix: $matrixCsv"
    def_Log "OK" "GeometryRecon GREEN: $reconCsv"
    if ([string]::IsNullOrWhiteSpace($basicCsv) -and [string]::IsNullOrWhiteSpace($matrixCsv) -and [string]::IsNullOrWhiteSpace($reconCsv)) {
        throw "No source CSV found (BasicInfo / FinancialData matrix / GeometryRecon GREEN). Run the matrix + reconstructor first."
    }

    $runnerPy = Join-Path $runDir "VRN_StockReport_DB_Runner.py"
    def_WriteRunnerPy -Path $runnerPy -RunDir $runDir -DbDir $P_DB_DIR -BasicCsv $basicCsv -MatrixCsv $matrixCsv -ReconGreenCsv $reconCsv

    $runtime = def_RunPython -RunnerPy $runnerPy
    if ($runtime.ExitCode -ne 0) {
        def_Log "ERR" "Runner exit $($runtime.ExitCode)"
        if ($runtime.Stderr) { Write-Host $runtime.Stderr -ForegroundColor DarkRed }
    }

    $summaryCsv = Join-Path $runDir "VRN_StockReport_DB_Summary.csv"
    $panoCsv = Join-Path $runDir "VRN_StockReport_Panorama.csv"
    $ledgerCsv = Join-Path $P_DB_DIR "VRN_StockReport_ConflictLedger.csv"
    $jsonPath = Join-Path $runDir "VRN_StockReport_DB_AIO.json"
    $htmlPath = Join-Path $runDir "VRN_StockReport_DB_AIO.html"

    $summaryRows = @(def_ImportCsvSafe $summaryCsv)
    $panoRows = @(def_ImportCsvSafe $panoCsv)
    $ledgerRows = @(def_ImportCsvSafe $ledgerCsv | Where-Object { $_.batch_id -eq $P_RUN_STAMP })

    $decision = if ($summaryRows.Count -gt 0) { $summaryRows[0] } else { def_NewFallbackDecision -Runtime $runtime }

    def_Progress 88 "STEP 4/4 Report" "三輪全景 + HTML matrix"
    def_WriteHtml -Path $htmlPath -Decision $decision -RuntimeRows @($runtime) -SummaryRows $summaryRows -PanoramaRows $panoRows -LedgerRows $ledgerRows

    $bundle = [ordered]@{
        Version = $P_VERSION; RunDir = $runDir; DbDir = $P_DB_DIR; ModulePath = $P_MODULE_PATH
        Sources = [ordered]@{ BasicInfo = $basicCsv; FinancialMatrix = $matrixCsv; GeometryReconGreen = $reconCsv }
        Decision = $decision; Runtime = $runtime
        Canonical = [ordered]@{
            StockReportInfoParquet = (Join-Path $P_DB_DIR "StockReportInfo.parquet")
            StockReportFinancialDataParquet = (Join-Path $P_DB_DIR "StockReportFinancialData.parquet")
            DuckDb = (Join-Path $P_DB_DIR "VRN_StockReports.duckdb")
            ConflictLedger = $ledgerCsv
        }
        SafeFlags = [ordered]@{ ParserCoreRewrite = $false; Delete = $false; Full22Rerun = $false; SingleWriter = $true }
    }
    def_WriteJson $bundle $jsonPath

    def_Progress 100 "DONE" "Incremental StockReport DB 完成"
    Write-Progress -Id $P_PROGRESS_ID -Activity "VRN Incremental StockReport DB" -Completed

    if ($P_OPEN_HTML -and (Test-Path -LiteralPath $htmlPath -PathType Leaf)) {
        try { Start-Process -FilePath $htmlPath | Out-Null } catch {}
    }

    Write-Host ""
    Write-Host "========================================================================================" -ForegroundColor DarkGray
    Write-Host "def DONE — VRN INCREMENTAL STOCKREPORT DB (parquet canonical)" -ForegroundColor Green
    Write-Host "========================================================================================" -ForegroundColor DarkGray
    "{0,-30} {1}" -f "[STATUS]", $decision.Status | Write-Host -ForegroundColor Cyan
    "{0,-30} {1}" -f "[RISK]", $decision.Risk | Write-Host -ForegroundColor Cyan
    "{0,-30} {1}" -f "[MODULE_SELF_CHECK]", $decision.ModuleSelfCheck | Write-Host -ForegroundColor Cyan
    "{0,-30} {1}" -f "[BATCH_ID]", $decision.BatchId | Write-Host -ForegroundColor Cyan
    "{0,-30} {1}" -f "[INFO_ACTIVE/TOTAL]", "$($decision.InfoActiveRows)/$($decision.InfoTotalRows)" | Write-Host -ForegroundColor Green
    "{0,-30} {1}" -f "[INFO_INS/SKIP/CONFLICT]", "$($decision.InfoInserted)/$($decision.InfoSkipped)/$($decision.InfoConflicts)" | Write-Host -ForegroundColor Cyan
    "{0,-30} {1}" -f "[FIN_ACTIVE/TOTAL]", "$($decision.FinActiveRows)/$($decision.FinTotalRows)" | Write-Host -ForegroundColor Green
    "{0,-30} {1}" -f "[FIN_INS/SKIP/CONFLICT]", "$($decision.FinInserted)/$($decision.FinSkipped)/$($decision.FinConflicts)" | Write-Host -ForegroundColor Cyan
    "{0,-30} {1}" -f "[PANORAMA_HIGH/YELLOW]", "$($decision.PanoramaHigh)/$($decision.PanoramaYellow)" | Write-Host -ForegroundColor Yellow
    "{0,-30} {1}" -f "[PARQUET/DUCKDB/CSV]", "$($decision.ParquetWritten)/$($decision.DuckDbWritten)/$($decision.CsvWritten)" | Write-Host -ForegroundColor Cyan
    "{0,-30} {1}" -f "[INFO_PARQUET]", (Join-Path $P_DB_DIR "StockReportInfo.parquet") | Write-Host -ForegroundColor Cyan
    "{0,-30} {1}" -f "[FIN_PARQUET]", (Join-Path $P_DB_DIR "StockReportFinancialData.parquet") | Write-Host -ForegroundColor Cyan
    "{0,-30} {1}" -f "[DUCKDB]", (Join-Path $P_DB_DIR "VRN_StockReports.duckdb") | Write-Host -ForegroundColor Cyan
    "{0,-30} {1}" -f "[CONFLICT_LEDGER]", $ledgerCsv | Write-Host -ForegroundColor Cyan
    "{0,-30} {1}" -f "[HTML]", $htmlPath | Write-Host -ForegroundColor Cyan
    Write-Host "========================================================================================" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "----- NEXT THREE PROCESSES -----" -ForegroundColor Cyan
    Write-Host "[NEXT_1] 再跑一次本腳本即增量：相同列 SKIP、值變 CONFLICT 升版、新檔 INSERT（parquet 為 canonical）"
    Write-Host "[NEXT_2] B3/B1 quarantine 待 PDF 幾何重抽修好後，再餵 DBReadyGreen 進來即自動納管"
    Write-Host "[NEXT_3] GSheet 推送為 bridge stub；綁好 service-account 後可把 *_Active CSV 推上去"
    Write-Host "========================================================================================" -ForegroundColor DarkGray
}

# =============================================================================
# def ENTRY — keep-open via post-catch statements (no finally keyword)
# =============================================================================
try {
    def_Main
}
catch {
    Write-Progress -Id $P_PROGRESS_ID -Activity "VRN Incremental StockReport DB" -Completed
    Write-Host ""
    Write-Host "[FATAL] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
}

Write-Host ""
Write-Host "PowerShell session remains open." -ForegroundColor Cyan

if ($P_KEEP_POWERSHELL_OPEN) {
    Write-Host "Press Enter to continue..." -ForegroundColor DarkGray
    try { [void][System.Console]::ReadLine() }
    catch { Start-Sleep -Seconds 3600 }
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
