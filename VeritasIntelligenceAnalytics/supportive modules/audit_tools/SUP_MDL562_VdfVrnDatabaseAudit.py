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
import csv
import json
import os
import sys
from pathlib import Path
from datetime import datetime

root = Path(sys.argv[1])
vdf_out = Path(sys.argv[2])
vrn_out = Path(sys.argv[3])
result_json = Path(sys.argv[4])

vdf_out.mkdir(parents=True, exist_ok=True)
vrn_out.mkdir(parents=True, exist_ok=True)
result_json.parent.mkdir(parents=True, exist_ok=True)

rows = []
excluded_parts = {".git", "__pycache__", "node_modules", "venv", ".venv"}

for path in root.rglob("*"):
    if not path.is_file():
        continue
    parts = set(path.parts)
    if parts & excluded_parts:
        continue

    try:
        stat = path.stat()
    except Exception:
        continue

    rel = str(path.relative_to(root))
    lower = rel.lower()

    subsystem = "VIA"
    if "\\vdf\\" in lower or "/vdf/" in lower or "dict\\vdf" in lower or "dict/vdf" in lower or "functional modules\\vdf" in lower:
        subsystem = "VDF"
    elif "\\vrn\\" in lower or "/vrn/" in lower or "dict\\vrn" in lower or "dict/vrn" in lower or "functional modules\\vrn" in lower:
        subsystem = "VRN"

    rows.append({
        "Subsystem": subsystem,
        "Name": path.name,
        "Extension": path.suffix.lower(),
        "RelativePath": rel,
        "FullPath": str(path),
        "SizeBytes": int(stat.st_size),
        "LastWriteTime": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
    })

summary = {}
for r in rows:
    key = (r["Subsystem"], r["Extension"])
    if key not in summary:
        summary[key] = {"Subsystem": r["Subsystem"], "Extension": r["Extension"], "FileCount": 0, "TotalBytes": 0}
    summary[key]["FileCount"] += 1
    summary[key]["TotalBytes"] += r["SizeBytes"]

summary_rows = list(summary.values())

outputs = []
warnings = []
errors = []

def write_csv(path, data):
    if not data:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(data[0].keys()))
        w.writeheader()
        w.writerows(data)

def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

try:
    vdf_inventory_csv = vdf_out / "VDF_Audit_FileInventory.csv"
    vdf_summary_csv = vdf_out / "VDF_Audit_FileSummary.csv"
    vrn_inventory_csv = vrn_out / "VRN_Audit_FileInventory.csv"
    vrn_summary_csv = vrn_out / "VRN_Audit_FileSummary.csv"

    write_csv(vdf_inventory_csv, [r for r in rows if r["Subsystem"] in ("VDF", "VIA")])
    write_csv(vdf_summary_csv, [r for r in summary_rows if r["Subsystem"] in ("VDF", "VIA")])
    write_csv(vrn_inventory_csv, [r for r in rows if r["Subsystem"] in ("VRN", "VIA")])
    write_csv(vrn_summary_csv, [r for r in summary_rows if r["Subsystem"] in ("VRN", "VIA")])

    outputs += [str(vdf_inventory_csv), str(vdf_summary_csv), str(vrn_inventory_csv), str(vrn_summary_csv)]

    vdf_inventory_json = vdf_out / "VDF_Audit_FileInventory.json"
    vdf_summary_json = vdf_out / "VDF_Audit_FileSummary.json"
    vrn_inventory_json = vrn_out / "VRN_Audit_FileInventory.json"
    vrn_summary_json = vrn_out / "VRN_Audit_FileSummary.json"

    write_json(vdf_inventory_json, [r for r in rows if r["Subsystem"] in ("VDF", "VIA")])
    write_json(vdf_summary_json, [r for r in summary_rows if r["Subsystem"] in ("VDF", "VIA")])
    write_json(vrn_inventory_json, [r for r in rows if r["Subsystem"] in ("VRN", "VIA")])
    write_json(vrn_summary_json, [r for r in summary_rows if r["Subsystem"] in ("VRN", "VIA")])

    outputs += [str(vdf_inventory_json), str(vdf_summary_json), str(vrn_inventory_json), str(vrn_summary_json)]
except Exception as e:
    errors.append(f"CSV/JSON write failed: {e}")

parquet_ok = False
duckdb_ok = False

try:
    import pandas as pd
    import pyarrow  # noqa: F401

    df = pd.DataFrame(rows)
    sf = pd.DataFrame(summary_rows)

    vdf_inv_pq = vdf_out / "VDF_Audit_FileInventory.parquet"
    vdf_sum_pq = vdf_out / "VDF_Audit_FileSummary.parquet"
    vrn_inv_pq = vrn_out / "VRN_Audit_FileInventory.parquet"
    vrn_sum_pq = vrn_out / "VRN_Audit_FileSummary.parquet"

    df[df["Subsystem"].isin(["VDF", "VIA"])].to_parquet(vdf_inv_pq, index=False)
    sf[sf["Subsystem"].isin(["VDF", "VIA"])].to_parquet(vdf_sum_pq, index=False)
    df[df["Subsystem"].isin(["VRN", "VIA"])].to_parquet(vrn_inv_pq, index=False)
    sf[sf["Subsystem"].isin(["VRN", "VIA"])].to_parquet(vrn_sum_pq, index=False)

    outputs += [str(vdf_inv_pq), str(vdf_sum_pq), str(vrn_inv_pq), str(vrn_sum_pq)]
    parquet_ok = True
except Exception as e:
    warnings.append(f"Parquet write skipped or failed: {e}")

try:
    import duckdb
    import pandas as pd

    df = pd.DataFrame(rows)
    sf = pd.DataFrame(summary_rows)

    vdf_db = vdf_out / "VDF_Audit_SystemInventory.duckdb"
    vrn_db = vrn_out / "VRN_Audit_SystemInventory.duckdb"

    con = duckdb.connect(str(vdf_db))
    con.execute("CREATE OR REPLACE TABLE file_inventory AS SELECT * FROM df WHERE Subsystem IN ('VDF','VIA')")
    con.execute("CREATE OR REPLACE TABLE file_summary AS SELECT * FROM sf WHERE Subsystem IN ('VDF','VIA')")
    con.close()

    con = duckdb.connect(str(vrn_db))
    con.execute("CREATE OR REPLACE TABLE file_inventory AS SELECT * FROM df WHERE Subsystem IN ('VRN','VIA')")
    con.execute("CREATE OR REPLACE TABLE file_summary AS SELECT * FROM sf WHERE Subsystem IN ('VRN','VIA')")
    con.close()

    outputs += [str(vdf_db), str(vrn_db)]
    duckdb_ok = True
except Exception as e:
    warnings.append(f"DuckDB write skipped or failed: {e}")

result = {
    "status": "OK" if not errors else "FAIL",
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "root": str(root),
    "vdf_out": str(vdf_out),
    "vrn_out": str(vrn_out),
    "file_count": len(rows),
    "summary_rows": len(summary_rows),
    "parquet_ok": parquet_ok,
    "duckdb_ok": duckdb_ok,
    "outputs": outputs,
    "warnings": warnings,
    "errors": errors,
    "top_extensions": sorted(summary_rows, key=lambda x: x["FileCount"], reverse=True)[:30],
}

result_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False))
