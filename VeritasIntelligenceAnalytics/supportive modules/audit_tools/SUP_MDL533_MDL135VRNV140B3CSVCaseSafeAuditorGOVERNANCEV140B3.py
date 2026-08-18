import csv
import json
import re
import sys
from pathlib import Path
from datetime import datetime

STAGING_CSV = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output\_staging\VRN_v140B3_BasicInfo_Consensus_Staging_20260526_182456\BasicInfo_Consensus_Staging.csv"
COVERAGE_CSV = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output\_staging\VRN_v140B3_BasicInfo_Consensus_Staging_20260526_182456\BasicInfo_Consensus_Coverage.csv"
UNMATCHED_CSV = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output\_staging\VRN_v140B3_BasicInfo_Consensus_Staging_20260526_182456\BasicInfo_Consensus_Unmatched.csv"
OUT_SCHEMA_CSV = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output\_staging\VRN_v140B3_BasicInfo_Consensus_Staging_20260526_182456\BasicInfo_Consensus_Schema_Manifest.csv"
OUT_HEADER_AUDIT_CSV = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output\_staging\VRN_v140B3_BasicInfo_Consensus_Staging_20260526_182456\BasicInfo_Consensus_Header_Duplicate_Audit.csv"
OUT_JSON = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output\_route_lock_runs\RUN_20260526_182456_VRN_V140B3_CSV_CASESAFE_STAGING_SEAL\VRN_v140B3_CSV_CaseSafe_Auditor.json"

def def_norm_header(x):
    return re.sub(r"[^a-z0-9]", "", str(x or "").strip().lower())

def def_source_prefix(col):
    c = str(col or "")
    if c.startswith("yf_"):
        return "YFinance"
    if c.startswith("factset_"):
        return "FactSet"
    if c.startswith("VRN_"):
        return "VRN"
    return "BasicInfo"

def def_type_guess(sample):
    s = str(sample or "").strip()
    if re.fullmatch(r"-?\d+(\.\d+)?", s):
        return "number_like"
    if re.fullmatch(r"(?i:true|false)", s):
        return "bool_like"
    if re.match(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}", s):
        return "date_like"
    return "text"

def def_open_csv(path):
    return open(path, "r", encoding="utf-8-sig", newline="", errors="ignore")

def def_count_csv_rows(path):
    p = Path(path)
    if not p.exists():
        return 0, 0
    with def_open_csv(path) as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return 0, 0
        count = 0
        for _ in reader:
            count += 1
        return len(header), count

def def_schema_and_audit(path, sample_limit=200):
    p = Path(path)
    if not p.exists():
        return [], [], 0, 0

    with def_open_csv(path) as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return [], [], 0, 0

        samples = [""] * len(header)
        non_empty = [0] * len(header)
        row_count = 0

        for row in reader:
            row_count += 1
            if row_count <= sample_limit:
                for i, v in enumerate(row[:len(header)]):
                    s = str(v or "").strip()
                    if s:
                        non_empty[i] += 1
                        if not samples[i]:
                            samples[i] = s

    norm_groups = {}
    for i, h in enumerate(header):
        norm = def_norm_header(h)
        norm_groups.setdefault(norm, []).append(i)

    schema = []
    audit = []
    seen_norm = {}

    for i, h in enumerate(header):
        norm = def_norm_header(h)
        seen_norm[norm] = seen_norm.get(norm, 0) + 1
        case_dup = len(norm_groups.get(norm, [])) > 1

        schema.append({
            "Ordinal": i + 1,
            "ColumnOriginal": h,
            "ColumnNormalized": norm,
            "CaseDuplicate": case_dup,
            "DuplicateIndex": seen_norm[norm],
            "TypeGuess": def_type_guess(samples[i]),
            "Sample": samples[i],
            "NonEmptyInFirst200": non_empty[i],
            "SourcePrefix": def_source_prefix(h),
        })

    for norm, idxs in norm_groups.items():
        if len(idxs) > 1:
            audit.append({
                "ColumnNormalized": norm,
                "DuplicateCount": len(idxs),
                "OriginalColumns": " | ".join([header[i] for i in idxs]),
                "Ordinals": " | ".join([str(i+1) for i in idxs]),
                "Risk": "CASE_DUPLICATE_HEADER",
                "Action": "Keep original CSV unchanged; avoid PowerShell Import-Csv; use Python reader for DB gate mapping",
            })

    return schema, audit, len(header), row_count

def def_write_csv(path, rows):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        p.write_text("", encoding="utf-8-sig")
        return
    keys = []
    for r in rows:
        for k in r.keys():
            if k not in keys:
                keys.append(k)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow(r)

def def_main():
    schema, audit, columns, rows = def_schema_and_audit(STAGING_CSV)
    coverage_cols, coverage_rows = def_count_csv_rows(COVERAGE_CSV)
    unmatched_cols, unmatched_rows = def_count_csv_rows(UNMATCHED_CSV)

    def_write_csv(OUT_SCHEMA_CSV, schema)
    def_write_csv(OUT_HEADER_AUDIT_CSV, audit)

    result = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "staging_csv": STAGING_CSV,
        "rows": rows,
        "columns": columns,
        "coverage_rows": coverage_rows,
        "unmatched_rows": unmatched_rows,
        "schema_csv": OUT_SCHEMA_CSV,
        "header_audit_csv": OUT_HEADER_AUDIT_CSV,
        "duplicate_header_groups": len(audit),
        "system_pass": rows > 0 and columns > 0,
    }

    Path(OUT_JSON).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8-sig")
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    def_main()
