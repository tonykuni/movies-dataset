import os, sys, json, glob, re, traceback
from datetime import datetime

base = sys.argv[1]
run_dir = sys.argv[2]
candidate_dir = sys.argv[3]
runtime_dir = sys.argv[4]
registry_dir = sys.argv[5]

vdf_db = os.path.join(base, "dict", "VDF", "DATABASE")
vdf_active = os.path.join(base, "dict", "VDF", "_active")
vrn_db = os.path.join(base, "dict", "VRN", "DATABASE")
ssot_path = os.path.join(base, "VIA_UnifiedInput_SSOT.json")

os.makedirs(candidate_dir, exist_ok=True)
os.makedirs(runtime_dir, exist_ok=True)
os.makedirs(registry_dir, exist_ok=True)

rows = []

def now():
    return datetime.now().isoformat(timespec="seconds")

def add(gate, step, status, risk, metric, value, message, path=""):
    rows.append({
        "Time": now(),
        "Gate": gate,
        "Step": step,
        "Status": status,
        "Risk": risk,
        "Metric": metric,
        "Value": str(value),
        "Message": message,
        "Path": path
    })

def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def latest(pattern):
    files = [f for f in glob.glob(pattern, recursive=True) if os.path.isfile(f)]
    if not files:
        return ""
    return max(files, key=os.path.getmtime)

def is_archive(path):
    p = path.lower()
    return any(x in p for x in ["\\backup", "\\backups", "\\temp", "\\_tmp", "\\_archive", "\\_old", "\\_deprecated", "重新整合"])

def safe_int(x):
    try:
        return int(float(str(x).replace(",","")))
    except Exception:
        return 0

ok = warn = fail = 0

try:
    # -------------------------------------------------------------------------
    # VDF_1A_FINISH_SEAL_REVIEW
    # -------------------------------------------------------------------------
    vdf_parquets = [f for f in glob.glob(os.path.join(vdf_db, "**", "*.parquet"), recursive=True) if os.path.isfile(f)]
    vdf_duckdb = [f for f in glob.glob(os.path.join(vdf_db, "**", "*.duckdb"), recursive=True) if os.path.isfile(f)]
    vdf_runtime = latest(os.path.join(vdf_active, "**", "*Runtime*.json"))

    add("VDF_1A_FINISH_SEAL_REVIEW", "Database Inventory", "OK_FOUND" if vdf_parquets else "WARN_EMPTY", "LOW" if vdf_parquets else "MEDIUM", "parquet_count", len(vdf_parquets), "VDF parquet inventory checked.", vdf_db)
    add("VDF_1A_FINISH_SEAL_REVIEW", "DuckDB Inventory", "OK_FOUND" if vdf_duckdb else "WARN_NOT_FOUND", "LOW" if vdf_duckdb else "MEDIUM", "duckdb_count", len(vdf_duckdb), "VDF DuckDB inventory checked.", vdf_db)
    add("VDF_1A_FINISH_SEAL_REVIEW", "Latest Runtime", "OK_FOUND" if vdf_runtime else "WARN_RUNTIME_NOT_FOUND", "LOW" if vdf_runtime else "MEDIUM", "runtime", bool(vdf_runtime), "Latest VDF active runtime located.", vdf_runtime)

    vdf_candidate = {
        "generated_at": now(),
        "status": "VDF_1A_FINISH_SEAL_CANDIDATE_READY" if vdf_parquets else "VDF_1A_FINISH_SEAL_REVIEW_REQUIRED",
        "risk": "LOW" if vdf_parquets else "MEDIUM",
        "policy": {
            "canonical_promotion": False,
            "destructive_delete": False,
            "stop_process": False,
            "blind_full_rerun": False
        },
        "inventory": {
            "parquet_count": len(vdf_parquets),
            "duckdb_count": len(vdf_duckdb),
            "latest_runtime": vdf_runtime,
            "sample_parquets": vdf_parquets[:40],
            "duckdb_files": vdf_duckdb[:20]
        }
    }

    vdf_candidate_path = os.path.join(candidate_dir, "VDF_1A_FinishSeal_Candidate_v0319.json")
    write_json(vdf_candidate_path, vdf_candidate)
    add("VDF_1A_FINISH_SEAL_REVIEW", "Candidate", "OK_CREATED", "LOW", "candidate", "created", "VDF finish seal candidate created. No canonical overwrite.", vdf_candidate_path)

    # -------------------------------------------------------------------------
    # VRN_1D2_VALIDATION
    # -------------------------------------------------------------------------
    try:
        import pandas as pd
        fin_path = os.path.join(vrn_db, "StockReportFinancialData.parquet")
        basic_path = os.path.join(vrn_db, "StockReportBasicInfo.parquet")

        if os.path.exists(fin_path):
            fin = pd.read_parquet(fin_path).astype(str).fillna("")
        else:
            fin = pd.DataFrame()

        if os.path.exists(basic_path):
            basic = pd.read_parquet(basic_path).astype(str).fillna("")
        else:
            basic = pd.DataFrame()

        fin_rows = len(fin)
        dup_hash = int(fin["record_hash"].duplicated().sum()) if "record_hash" in fin.columns else 0
        blank_value = int((fin["value"].astype(str).str.len() == 0).sum()) if "value" in fin.columns and not fin.empty else 0
        accounts = int(fin["account_canonical"].nunique()) if "account_canonical" in fin.columns and not fin.empty else 0
        reports = int(fin["report_id"].nunique()) if "report_id" in fin.columns and not fin.empty else 0
        basic_rows = len(basic)

        add("VRN_1D2_VALIDATION", "FinancialData Rows", "OK_FOUND" if fin_rows > 0 else "FAIL_EMPTY", "LOW" if fin_rows > 0 else "HIGH", "financial_rows", fin_rows, "VRN FinancialData row count checked.", fin_path)
        add("VRN_1D2_VALIDATION", "Duplicate Hash", "OK_PASS" if dup_hash == 0 else "FAIL_DUPLICATE", "LOW" if dup_hash == 0 else "HIGH", "duplicate_record_hash", dup_hash, "record_hash duplicate check.", fin_path)
        add("VRN_1D2_VALIDATION", "Blank Value", "OK_PASS" if blank_value == 0 else "WARN_BLANK_VALUE", "LOW" if blank_value == 0 else "MEDIUM", "blank_value", blank_value, "blank value check.", fin_path)
        add("VRN_1D2_VALIDATION", "Account Coverage", "OK_PASS" if accounts >= 5 else "WARN_LOW_COVERAGE", "LOW" if accounts >= 5 else "MEDIUM", "account_canonical_count", accounts, "canonical account coverage check.", fin_path)
        add("VRN_1D2_VALIDATION", "Report Coverage", "OK_PASS" if reports >= 10 else "WARN_LOW_COVERAGE", "LOW" if reports >= 10 else "MEDIUM", "report_count", reports, "report_id coverage check.", fin_path)
        add("VRN_1D2_VALIDATION", "BasicInfo Rows", "OK_FOUND" if basic_rows > 0 else "WARN_NOT_FOUND", "LOW" if basic_rows > 0 else "MEDIUM", "basic_rows", basic_rows, "VRN BasicInfo row count checked.", basic_path)

        validation = {
            "generated_at": now(),
            "status": "VRN_1D2_VALIDATION_READY" if fin_rows > 0 and dup_hash == 0 else "VRN_1D2_VALIDATION_REVIEW_REQUIRED",
            "risk": "LOW" if fin_rows > 0 and dup_hash == 0 else "HIGH",
            "metrics": {
                "financial_rows": fin_rows,
                "duplicate_record_hash": dup_hash,
                "blank_value": blank_value,
                "account_canonical_count": accounts,
                "report_count": reports,
                "basic_rows": basic_rows
            },
            "policy": {
                "canonical_promotion": False,
                "destructive_delete": False
            }
        }

        validation_path = os.path.join(candidate_dir, "VRN_1D2_Validation_Result_v0319.json")
        write_json(validation_path, validation)
        add("VRN_1D2_VALIDATION", "Validation Result", "OK_CREATED", "LOW", "validation_json", "created", "VRN 1D2 validation result created.", validation_path)

    except Exception as e:
        add("VRN_1D2_VALIDATION", "Python Validation", "FAIL_EXCEPTION", "HIGH", "exception", str(e), traceback.format_exc(), vrn_db)

    # -------------------------------------------------------------------------
    # SSOT_SUPPLEMENT_REVIEW
    # -------------------------------------------------------------------------
    required_keys = ["base", "vrn", "vdf", "supportive_modules", "field_registry", "broker_list"]
    ssot = {}
    if os.path.exists(ssot_path):
        try:
            ssot = read_json(ssot_path)
            add("SSOT_SUPPLEMENT_REVIEW", "SSOT Load", "OK_LOADED", "LOW", "ssot", "loaded", "VIA SSOT loaded.", ssot_path)
        except Exception as e:
            add("SSOT_SUPPLEMENT_REVIEW", "SSOT Load", "FAIL_PARSE", "HIGH", "error", str(e), "SSOT parse failed.", ssot_path)
    else:
        add("SSOT_SUPPLEMENT_REVIEW", "SSOT Load", "WARN_NOT_FOUND", "MEDIUM", "ssot", "missing", "SSOT file not found.", ssot_path)

    missing = [k for k in required_keys if k not in ssot]
    for k in required_keys:
        add("SSOT_SUPPLEMENT_REVIEW", "Required Key", "OK_PRESENT" if k in ssot else "WARN_MISSING", "LOW" if k in ssot else "MEDIUM", "key", k, "SSOT required key check.", ssot_path)

    supplement = {
        "generated_at": now(),
        "status": "SSOT_SUPPLEMENT_CANDIDATE_READY",
        "risk": "MEDIUM" if missing else "LOW",
        "missing_keys": missing,
        "candidate_only": True,
        "canonical_overwrite": False,
        "supplement": {}
    }

    for k in missing:
        if k == "base":
            supplement["supplement"][k] = {"project_root": base}
        elif k == "vrn":
            supplement["supplement"][k] = {"database": vrn_db, "financial_data": os.path.join(vrn_db, "StockReportFinancialData.parquet")}
        elif k == "vdf":
            supplement["supplement"][k] = {"database": vdf_db, "active": vdf_active}
        elif k == "supportive_modules":
            supplement["supplement"][k] = {"root": os.path.join(base, "supportive modules")}
        elif k == "field_registry":
            supplement["supplement"][k] = {"status": "candidate_required"}
        elif k == "broker_list":
            supplement["supplement"][k] = {"status": "candidate_required"}

    ssot_candidate_path = os.path.join(candidate_dir, "VIA_UnifiedInput_SSOT_Supplement_Candidate_v0319.json")
    write_json(ssot_candidate_path, supplement)
    add("SSOT_SUPPLEMENT_REVIEW", "Supplement Candidate", "OK_CREATED", "LOW" if not missing else "MEDIUM", "missing_keys", len(missing), "SSOT supplement candidate created. No canonical overwrite.", ssot_candidate_path)

    # -------------------------------------------------------------------------
    # POLICY_PATTERN_REVIEW
    # -------------------------------------------------------------------------
    scan_roots = [
        os.path.join(base, "supportive modules"),
        os.path.join(base, "dict", "VDF"),
        os.path.join(base, "dict", "VRN"),
        os.path.join(os.path.expanduser("~"), "OneDrive", "VeritasIntelligenceAnalytics", "module", "VRN"),
        os.path.join(os.path.expanduser("~"), "OneDrive", "VeritasIntelligenceAnalytics", "module", "VeritasDataForge")
    ]

    policy_patterns = [
        ("Stop-Process", re.compile(r"\bStop-Process\b", re.I)),
        ("pip install", re.compile(r"\bpip\s+install\b", re.I))
    ]

    policy_hits = []
    max_files = 1200
    seen = 0

    for root in scan_roots:
        if not os.path.isdir(root):
            continue
        for path in glob.glob(os.path.join(root, "**", "*"), recursive=True):
            if seen >= max_files:
                break
            if not os.path.isfile(path):
                continue
            if not path.lower().endswith((".ps1", ".py", ".psm1", ".txt", ".md")):
                continue
            seen += 1
            try:
                text = open(path, "r", encoding="utf-8", errors="ignore").read()
            except Exception:
                continue

            for name, rx in policy_patterns:
                if rx.search(text):
                    cls = "ARCHIVE_REVIEW" if is_archive(path) else "ACTIVE_REVIEW"
                    risk = "LOW" if cls == "ARCHIVE_REVIEW" else "MEDIUM"
                    policy_hits.append({"pattern": name, "path": path, "class": cls, "risk": risk})
                    add("POLICY_PATTERN_REVIEW", "Pattern", "WARN_POLICY_PATTERN", risk, "pattern", name, cls, path)

    policy_path = os.path.join(candidate_dir, "PolicyPattern_Classification_v0319.json")
    write_json(policy_path, {
        "generated_at": now(),
        "status": "POLICY_PATTERN_CLASSIFICATION_READY",
        "risk": "MEDIUM" if any(x["class"] == "ACTIVE_REVIEW" for x in policy_hits) else "LOW",
        "max_files_scanned": max_files,
        "files_scanned": seen,
        "hits": policy_hits,
        "policy": {
            "auto_delete": False,
            "auto_modify": False,
            "manual_review_required": True
        }
    })
    add("POLICY_PATTERN_REVIEW", "Classification", "OK_CREATED", "LOW", "hits", len(policy_hits), "Policy pattern classification created. No auto-delete.", policy_path)

except Exception as e:
    add("NEXTGATE_EXECUTION", "Fatal", "FAIL_FATAL", "HIGH", "exception", str(e), traceback.format_exc(), run_dir)

# finalize
for r in rows:
    st = r.get("Status","")
    rk = r.get("Risk","")
    if st.startswith("OK") or "READY" in st or "CREATED" in st or "FOUND" in st or "PASS" in st:
        ok += 1
    elif st.startswith("FAIL") or st.startswith("BLOCK") or rk == "HIGH":
        fail += 1
    else:
        warn += 1

runtime_json = os.path.join(runtime_dir, "VIA_VRN_VDF_NextGate_Execution_Runtime_v0319.json")
matrix_json = os.path.join(registry_dir, "VIA_VRN_VDF_NextGate_Execution_Matrix_v0319.json")
matrix_csv = os.path.join(registry_dir, "VIA_VRN_VDF_NextGate_Execution_Matrix_v0319.csv")

write_json(matrix_json, rows)

try:
    import pandas as pd
    pd.DataFrame(rows).to_csv(matrix_csv, index=False, encoding="utf-8-sig")
except Exception:
    with open(matrix_csv, "w", encoding="utf-8") as f:
        f.write("Gate,Step,Status,Risk,Metric,Value,Message,Path\n")
        for r in rows:
            f.write(",".join(str(r.get(k,"")).replace(",", " ") for k in ["Gate","Step","Status","Risk","Metric","Value","Message","Path"]) + "\n")

vrn_financial_rows = 0
for r in rows:
    if r["Gate"] == "VRN_1D2_VALIDATION" and r["Metric"] == "financial_rows":
        vrn_financial_rows = safe_int(r["Value"])

vdf_parquet_count = 0
for r in rows:
    if r["Gate"] == "VDF_1A_FINISH_SEAL_REVIEW" and r["Metric"] == "parquet_count":
        vdf_parquet_count = safe_int(r["Value"])

status = "VIA_VRN_VDF_NEXTGATE_EXECUTION_READY"
risk = "LOW"
next_action = "USER_REVIEW"

if fail > 0:
    status = "VIA_VRN_VDF_NEXTGATE_EXECUTION_REVIEW_REQUIRED"
    risk = "HIGH"
    next_action = "TARGET_ACTIVE_FAIL"
elif warn > 0:
    status = "VIA_VRN_VDF_NEXTGATE_EXECUTION_READY_WITH_REVIEW"
    risk = "MEDIUM"
    next_action = "REVIEW_CANDIDATES"

runtime = {
    "generated_at": now(),
    "status": status,
    "risk": risk,
    "ok": ok,
    "warn": warn,
    "fail": fail,
    "next": next_action,
    "vrn_progress": 96 if vrn_financial_rows >= 29114 else 88,
    "vdf_progress": 88 if vdf_parquet_count >= 20 else 82 if vdf_parquet_count > 0 else 65,
    "vrn_financial_rows": vrn_financial_rows,
    "vdf_parquet_count": vdf_parquet_count,
    "runtime_json": runtime_json,
    "matrix_json": matrix_json,
    "matrix_csv": matrix_csv,
    "candidate_dir": candidate_dir,
    "run_dir": run_dir,
    "policy": {
        "canonical_promotion": False,
        "stop_process": False,
        "destructive_delete": False,
        "blind_full_rerun": False
    }
}

write_json(runtime_json, runtime)
print(json.dumps({"runtime": runtime, "rows": rows}, ensure_ascii=False))