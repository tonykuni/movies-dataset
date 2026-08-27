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
import json
import re
import hashlib
from pathlib import Path
from datetime import datetime

candidate_manifest_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_SMALL_SCOPE_CANDIDATE_SEED_STAGING_v0274_20260610_145643\\registry\\VDF_AkShare_CandidateSeedManifest_v0274.json")
staging_dir = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_SMALL_SCOPE_CANDIDATE_SEED_STAGING_v0274_20260610_145643\\staging")
mapping_rules_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_CANONICAL_MAPPING_GATE_v0277_20260610_220358\\registry\\VDF_AkShare_CanonicalMappingRules_v0277.json")
canonical_preview_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_CANONICAL_MAPPING_GATE_v0277_20260610_220358\\preview\\VDF_AkShare_CanonicalPreview_v0277.json")
canonical_preview_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_CANONICAL_MAPPING_GATE_v0277_20260610_220358\\preview\\VDF_AkShare_CanonicalPreview_v0277.csv")
readiness_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_CANONICAL_MAPPING_GATE_v0277_20260610_220358\\registry\\VDF_AkShare_MergeReadinessGate_v0277.json")
out = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_CANONICAL_MAPPING_GATE_v0277_20260610_220358\\runtime\\vdf_akshare_canonical_mapping_gate_result_v0277.json")

CANONICAL = {
    "VDF_Global_Commodity": ["symbol","date","value","source","unit","frequency","description"],
    "VDF_Global_Freight": ["symbol","date","value","source","unit","route","frequency"],
    "VDF_Global_Macro": ["symbol","date","value","source","unit","frequency","description"]
}

DATE_PATTERNS = ["date","日期","时间","time","day","交易日","统计日期"]
VALUE_PATTERNS = ["value","price","close","收盘","现值","最新价","价格","指数","点位","结算价","昨结算","现货价"]
UNIT_PATTERNS = ["unit","单位"]
SYMBOL_PATTERNS = ["symbol","品种","商品","指数名称","名称","name","variety"]

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def norm(s):
    return str(s).strip().lower()

def choose_col(cols, patterns):
    low_map = {norm(c): c for c in cols}
    for p in patterns:
        p_low = norm(p)
        for c in cols:
            if p_low in norm(c):
                return c
    return ""

def infer_date_from_any(row):
    for k, v in row.items():
        if any(p in str(k) for p in DATE_PATTERNS):
            if str(v).strip():
                return str(v).strip()
    return ""

def infer_value_from_any(row):
    for k, v in row.items():
        if any(p.lower() in str(k).lower() for p in VALUE_PATTERNS):
            s = str(v).replace(",", "").strip()
            if s:
                m = re.search(r"-?\d+(\.\d+)?", s)
                if m:
                    return m.group(0)
    # fallback first numeric-like value excluding vdf_* columns
    for k, v in row.items():
        if str(k).startswith("vdf_"):
            continue
        s = str(v).replace(",", "").strip()
        m = re.search(r"-?\d+(\.\d+)?", s)
        if m:
            return m.group(0)
    return ""

result = {
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "status": "VDF_AKSHARE_CANONICAL_MAPPING_GATE_READY_WITH_DRYRUN_REQUIRED",
    "risk": "MEDIUM",
    "policy": "Mapping gate only. Preview only. No DATABASE write. No canonical merge.",
    "candidate_rows_total": 0,
    "preview_rows_total": 0,
    "mapping_rule_count": 0,
    "canonical_family_counts": {},
    "invalid_preview_rows": 0,
    "candidate_tables": {},
    "recommendation": "UNKNOWN"
}

try:
    import pandas as pd

    if not candidate_manifest_json.exists():
        raise RuntimeError("Candidate manifest missing.")
    if not staging_dir.exists():
        raise RuntimeError("Staging dir missing.")

    manifest = json.loads(candidate_manifest_json.read_text(encoding="utf-8"))
    manifest_items = manifest.get("manifest_items", [])

    all_preview = []
    mapping_rules = []

    for item in manifest_items:
        target_table = item.get("target_table", "")
        csv_path = item.get("csv", "")
        if not csv_path:
            continue
        p = Path(csv_path)
        if not p.exists():
            continue

        df = pd.read_csv(p)
        result["candidate_rows_total"] += int(len(df))
        result["candidate_tables"][target_table] = int(len(df))

        cols = list(df.columns)
        families = sorted(set([str(x) for x in df.get("vdf_canonical_family", pd.Series(dtype=str)).dropna().unique().tolist()]))
        if not families:
            families = ["VDF_Global_Commodity"]

        date_col = choose_col(cols, DATE_PATTERNS)
        value_col = choose_col(cols, VALUE_PATTERNS)
        symbol_col = choose_col(cols, SYMBOL_PATTERNS)

        for family in families:
            canonical_cols = CANONICAL.get(family, CANONICAL["VDF_Global_Commodity"])
            rule = {
                "target_table": target_table,
                "canonical_family": family,
                "source_csv": str(p),
                "source_csv_sha256": sha256_file(p),
                "candidate_rows": int(len(df)),
                "source_columns": cols,
                "canonical_columns": canonical_cols,
                "selected_mapping": {
                    "symbol": "vdf_symbol_hint" if "vdf_symbol_hint" in cols else symbol_col,
                    "date": date_col,
                    "value": value_col,
                    "source": "vdf_source_function",
                    "unit": "",
                    "frequency": "",
                    "description": "vdf_selected_category",
                    "route": "vdf_symbol_hint"
                },
                "mapping_confidence": {
                    "symbol": "HIGH" if "vdf_symbol_hint" in cols else ("MEDIUM" if symbol_col else "LOW"),
                    "date": "MEDIUM" if date_col else "LOW",
                    "value": "MEDIUM" if value_col else "LOW",
                    "source": "HIGH" if "vdf_source_function" in cols else "LOW",
                    "description": "HIGH" if "vdf_selected_category" in cols else "LOW"
                },
                "manual_review_required": False
            }

            if not value_col:
                rule["manual_review_required"] = True
            if not date_col:
                rule["manual_review_required"] = True

            mapping_rules.append(rule)

        for _, row in df.iterrows():
            rd = row.to_dict()
            family = str(rd.get("vdf_canonical_family", "VDF_Global_Commodity"))
            if family not in CANONICAL:
                family = "VDF_Global_Commodity"

            symbol = str(rd.get("vdf_symbol_hint", "")).strip()
            date = str(rd.get(date_col, "")).strip() if date_col else infer_date_from_any(rd)
            value = str(rd.get(value_col, "")).strip() if value_col else infer_value_from_any(rd)
            source = str(rd.get("vdf_source_function", "akshare")).strip()
            desc = str(rd.get("vdf_selected_category", "")).strip()

            preview = {
                "canonical_family": family,
                "symbol": symbol,
                "date": date,
                "value": value,
                "source": source,
                "unit": "",
                "frequency": "",
                "description": desc,
                "route": symbol if family == "VDF_Global_Freight" else "",
                "vdf_mapping_gate": "v027.7",
                "vdf_mapping_policy": "PREVIEW_ONLY_NO_DATABASE_WRITE",
                "vdf_target_table": rd.get("vdf_target_table", target_table),
                "vdf_seeded_at": rd.get("vdf_seeded_at", ""),
                "vdf_original_row_hash": hashlib.sha256(json.dumps(rd, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]
            }
            all_preview.append(preview)

    preview_df = pd.DataFrame(all_preview)

    if len(preview_df) > 0:
        invalid = preview_df[
            (preview_df["symbol"].astype(str).str.strip() == "") |
            (preview_df["value"].astype(str).str.strip() == "")
        ]
        result["invalid_preview_rows"] = int(len(invalid))

        counts = {}
        for fam, sub in preview_df.groupby("canonical_family"):
            counts[str(fam)] = int(len(sub))
        result["canonical_family_counts"] = counts

        canonical_preview_csv.parent.mkdir(parents=True, exist_ok=True)
        preview_df.to_csv(canonical_preview_csv, index=False, encoding="utf-8-sig")
        canonical_preview_json.parent.mkdir(parents=True, exist_ok=True)
        preview_df.to_json(canonical_preview_json, orient="records", force_ascii=False, indent=2)

    result["preview_rows_total"] = int(len(preview_df))
    result["mapping_rule_count"] = len(mapping_rules)

    mapping_rules_json.parent.mkdir(parents=True, exist_ok=True)
    mapping_rules_json.write_text(json.dumps({
        "generated_at": result["generated_at"],
        "policy": result["policy"],
        "mapping_rule_count": len(mapping_rules),
        "rules": mapping_rules
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    readiness = {
        "generated_at": result["generated_at"],
        "status": "READY_FOR_V0278_DRYRUN_WITH_REVIEW",
        "risk": "MEDIUM",
        "allowed_to_write_database": False,
        "allowed_to_merge_canonical": False,
        "candidate_rows_total": result["candidate_rows_total"],
        "preview_rows_total": result["preview_rows_total"],
        "invalid_preview_rows": result["invalid_preview_rows"],
        "mapping_rule_count": result["mapping_rule_count"],
        "canonical_family_counts": result["canonical_family_counts"],
        "next_step": "v027.8 AkShare candidate-to-canonical dry-run only; no DB write",
        "notes": [
            "Preview generated only.",
            "DATABASE write remains blocked.",
            "Canonical merge remains blocked.",
            "v027.8 must be dry-run only."
        ]
    }

    if result["preview_rows_total"] <= 0:
        result["status"] = "VDF_AKSHARE_CANONICAL_MAPPING_GATE_WITH_REPAIR_REQUIRED"
        result["risk"] = "HIGH"
        result["recommendation"] = "BLOCK_NO_CANONICAL_PREVIEW_ROWS"
        readiness["status"] = "BLOCK_NO_PREVIEW_ROWS"
        readiness["risk"] = "HIGH"
    elif result["invalid_preview_rows"] > 0:
        result["status"] = "VDF_AKSHARE_CANONICAL_MAPPING_GATE_READY_WITH_REVIEW"
        result["risk"] = "MEDIUM"
        result["recommendation"] = "ALLOW_V0278_DRYRUN_ONLY_WITH_MAPPING_REVIEW"
        readiness["status"] = "READY_FOR_V0278_DRYRUN_WITH_MAPPING_REVIEW"
        readiness["risk"] = "MEDIUM"
    else:
        result["status"] = "VDF_AKSHARE_CANONICAL_MAPPING_GATE_READY"
        result["risk"] = "LOW"
        result["recommendation"] = "ALLOW_V0278_CANDIDATE_TO_CANONICAL_DRYRUN_ONLY_NO_DB_WRITE"
        readiness["status"] = "READY_FOR_V0278_DRYRUN"
        readiness["risk"] = "LOW"

    readiness_json.parent.mkdir(parents=True, exist_ok=True)
    readiness_json.write_text(json.dumps(readiness, ensure_ascii=False, indent=2), encoding="utf-8")

except Exception as e:
    result["status"] = "VDF_AKSHARE_CANONICAL_MAPPING_GATE_WITH_REPAIR_REQUIRED"
    result["risk"] = "HIGH"
    result["error"] = str(e)
    result["recommendation"] = "BLOCK_CANONICAL_MAPPING_GATE_REPAIR_INPUTS"

out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({
    "status": result["status"],
    "risk": result["risk"],
    "candidate_rows_total": result["candidate_rows_total"],
    "preview_rows_total": result["preview_rows_total"],
    "invalid_preview_rows": result["invalid_preview_rows"],
    "mapping_rule_count": result["mapping_rule_count"],
    "canonical_family_counts": result["canonical_family_counts"],
    "candidate_tables": result["candidate_tables"],
    "recommendation": result["recommendation"]
}, ensure_ascii=False))
