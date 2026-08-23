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
from pathlib import Path
from datetime import datetime

candidate_audit_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_freeze\\VDF_AKSHARE_CANDIDATE_STAGING_FINAL_SEAL_v0275_20260610_150853\\registry\\VDF_AkShare_CandidateIntegrityAudit_v0275.json")
quarantine_audit_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_freeze\\VDF_AKSHARE_CANDIDATE_STAGING_FINAL_SEAL_v0275_20260610_150853\\registry\\VDF_AkShare_QuarantineAudit_v0275.json")
candidate_manifest_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_SMALL_SCOPE_CANDIDATE_SEED_STAGING_v0274_20260610_145643\\registry\\VDF_AkShare_CandidateSeedManifest_v0274.json")
staging_dir = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_SMALL_SCOPE_CANDIDATE_SEED_STAGING_v0274_20260610_145643\\staging")
schema_gate_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_CANDIDATE_TO_CANONICAL_MERGE_GATE_REVIEW_v0276_20260610_215641\\registry\\VDF_AkShare_SchemaGateReview_v0276.json")
dedup_gate_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_CANDIDATE_TO_CANONICAL_MERGE_GATE_REVIEW_v0276_20260610_215641\\registry\\VDF_AkShare_KeyDedupGateReview_v0276.json")
merge_preview_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_CANDIDATE_TO_CANONICAL_MERGE_GATE_REVIEW_v0276_20260610_215641\\registry\\VDF_AkShare_CandidateMergePreview_v0276.json")
out = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_CANDIDATE_TO_CANONICAL_MERGE_GATE_REVIEW_v0276_20260610_215641\\runtime\\vdf_akshare_candidate_to_canonical_merge_gate_review_result_v0276.json")

CANONICAL_SCHEMAS = {
    "VDF_Global_Commodity": [
        "symbol", "date", "value", "source", "unit", "frequency", "description"
    ],
    "VDF_Global_Freight": [
        "symbol", "date", "value", "source", "unit", "route", "frequency"
    ],
    "VDF_Global_Macro": [
        "symbol", "date", "value", "source", "unit", "frequency", "description"
    ]
}

result = {
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "status": "VDF_AKSHARE_CANDIDATE_TO_CANONICAL_MERGE_GATE_REVIEW_READY_WITH_MAPPING_REQUIRED",
    "risk": "MEDIUM",
    "policy": "Merge gate review only. No DATABASE write. No canonical merge.",
    "candidate_rows_total": 0,
    "candidate_tables": {},
    "quarantine_count": 0,
    "schema_gate": {},
    "dedup_gate": {},
    "merge_policy_gate": {},
    "recommendation": "UNKNOWN"
}

try:
    import pandas as pd

    if not candidate_audit_json.exists():
        raise RuntimeError("Candidate audit JSON missing.")
    if not quarantine_audit_json.exists():
        raise RuntimeError("Quarantine audit JSON missing.")
    if not candidate_manifest_json.exists():
        raise RuntimeError("Candidate manifest JSON missing.")
    if not staging_dir.exists():
        raise RuntimeError("Candidate staging directory missing.")

    candidate_audit = json.loads(candidate_audit_json.read_text(encoding="utf-8"))
    quarantine_audit = json.loads(quarantine_audit_json.read_text(encoding="utf-8"))
    manifest = json.loads(candidate_manifest_json.read_text(encoding="utf-8"))

    result["candidate_rows_total"] = int(candidate_audit.get("candidate_rows_total") or 0)
    result["candidate_tables"] = candidate_audit.get("candidate_tables", {})
    result["quarantine_count"] = int(quarantine_audit.get("quarantine_notes", {}).get("quarantine_count") or 0)

    audit_items = candidate_audit.get("audit_items", [])
    schema_items = []
    dedup_items = []
    merge_items = []

    for item in audit_items:
        target_table = item.get("target_table", "")
        expected_rows = int(item.get("expected_rows") or 0)

        csv_path = ""
        for m in manifest.get("manifest_items", []):
            if m.get("target_table") == target_table:
                csv_path = m.get("csv", "")
                break

        if not csv_path:
            schema_items.append({
                "target_table": target_table,
                "status": "BLOCK_NO_CSV",
                "risk": "HIGH",
                "message": "CSV path missing from manifest."
            })
            continue

        p = Path(csv_path)
        if not p.exists():
            schema_items.append({
                "target_table": target_table,
                "status": "BLOCK_CSV_MISSING",
                "risk": "HIGH",
                "message": str(p)
            })
            continue

        df = pd.read_csv(p)
        cols = list(df.columns)

        families = sorted(set([str(x) for x in df.get("vdf_canonical_family", pd.Series(dtype=str)).dropna().unique().tolist()]))
        source_functions = sorted(set([str(x) for x in df.get("vdf_source_function", pd.Series(dtype=str)).dropna().unique().tolist()]))

        family_reviews = []
        for family in families:
            canonical_cols = CANONICAL_SCHEMAS.get(family, [])
            has_staging_cols = all(c in cols for c in [
                "vdf_source_function",
                "vdf_selected_category",
                "vdf_target_table",
                "vdf_symbol_hint",
                "vdf_canonical_family",
                "vdf_seeded_at",
                "vdf_policy"
            ])

            # Candidate data is raw AkShare shape. It is not expected to already match canonical.
            # Therefore mapping is required unless exact canonical columns exist.
            exact_canonical_hit = all(c in cols for c in canonical_cols)
            mapping_required = not exact_canonical_hit

            family_reviews.append({
                "canonical_family": family,
                "canonical_columns_required": canonical_cols,
                "exact_canonical_columns_present": exact_canonical_hit,
                "mapping_required": mapping_required
            })

        dup_subset = [c for c in ["vdf_source_function","vdf_selected_category","vdf_symbol_hint"] if c in cols]
        duplicate_rows = 0
        if dup_subset:
            duplicate_rows = int(df.duplicated(subset=dup_subset, keep=False).sum())

        symbol_hint_null = 0
        if "vdf_symbol_hint" in cols:
            symbol_hint_null = int(df["vdf_symbol_hint"].isna().sum())

        schema_items.append({
            "target_table": target_table,
            "status": "OK_SCHEMA_REVIEW_WITH_MAPPING_REQUIRED",
            "risk": "MEDIUM",
            "expected_rows": expected_rows,
            "actual_rows": int(len(df)),
            "columns": cols,
            "canonical_families": families,
            "source_functions": source_functions,
            "family_reviews": family_reviews,
            "message": "Raw AkShare candidate staging is valid, but canonical mapping is required before merge."
        })

        dedup_items.append({
            "target_table": target_table,
            "status": "OK_DEDUP_REVIEW",
            "risk": "LOW" if duplicate_rows == 0 else "MEDIUM",
            "row_count": int(len(df)),
            "duplicate_rows_by_source_category_symbol": duplicate_rows,
            "symbol_hint_null": symbol_hint_null,
            "dedup_policy_required": duplicate_rows > 0,
            "message": "Dedup gate review only; no DB write."
        })

        merge_items.append({
            "target_table": target_table,
            "status": "BLOCK_REAL_MERGE_UNTIL_MAPPING_GATE",
            "risk": "MEDIUM",
            "canonical_families": families,
            "candidate_rows": int(len(df)),
            "allowed_now": False,
            "next_required_gate": "v027.7 canonical mapping gate only",
            "message": "Do not merge raw AkShare candidate rows directly into canonical schema."
        })

    schema_high = any(x.get("risk") == "HIGH" for x in schema_items)
    dedup_high = any(x.get("risk") == "HIGH" for x in dedup_items)

    schema_gate = {
        "status": "OK_SCHEMA_GATE_REVIEW_WITH_MAPPING_REQUIRED" if not schema_high else "BLOCK_SCHEMA_GATE",
        "risk": "MEDIUM" if not schema_high else "HIGH",
        "items": schema_items
    }

    dedup_gate = {
        "status": "OK_DEDUP_GATE_REVIEW",
        "risk": "MEDIUM" if any(x.get("risk") == "MEDIUM" for x in dedup_items) else "LOW",
        "items": dedup_items
    }

    merge_policy_gate = {
        "status": "MERGE_BLOCKED_UNTIL_CANONICAL_MAPPING_GATE",
        "risk": "MEDIUM",
        "allowed_to_merge_now": False,
        "candidate_rows_total": result["candidate_rows_total"],
        "quarantine_count": result["quarantine_count"],
        "reason": "Candidate rows are staged and sealed, but raw AkShare columns need mapping to canonical VDF schema.",
        "next_step": "v027.7 AkShare canonical mapping gate only; no DB write",
        "items": merge_items
    }

    result["schema_gate"] = {
        "status": schema_gate["status"],
        "risk": schema_gate["risk"],
        "count": len(schema_items)
    }
    result["dedup_gate"] = {
        "status": dedup_gate["status"],
        "risk": dedup_gate["risk"],
        "count": len(dedup_items)
    }
    result["merge_policy_gate"] = {
        "status": merge_policy_gate["status"],
        "risk": merge_policy_gate["risk"],
        "allowed_to_merge_now": False,
        "next_step": merge_policy_gate["next_step"]
    }

    schema_gate_json.parent.mkdir(parents=True, exist_ok=True)
    schema_gate_json.write_text(json.dumps(schema_gate, ensure_ascii=False, indent=2), encoding="utf-8")

    dedup_gate_json.parent.mkdir(parents=True, exist_ok=True)
    dedup_gate_json.write_text(json.dumps(dedup_gate, ensure_ascii=False, indent=2), encoding="utf-8")

    merge_preview_json.parent.mkdir(parents=True, exist_ok=True)
    merge_preview_json.write_text(json.dumps(merge_policy_gate, ensure_ascii=False, indent=2), encoding="utf-8")

    if schema_high or dedup_high:
        result["status"] = "VDF_AKSHARE_CANDIDATE_TO_CANONICAL_MERGE_GATE_REVIEW_WITH_REPAIR_REQUIRED"
        result["risk"] = "HIGH"
        result["recommendation"] = "BLOCK_V0277_UNTIL_SCHEMA_OR_DEDUP_REPAIR"
    else:
        result["status"] = "VDF_AKSHARE_CANDIDATE_TO_CANONICAL_MERGE_GATE_REVIEW_READY_WITH_MAPPING_REQUIRED"
        result["risk"] = "MEDIUM"
        result["recommendation"] = "ALLOW_V0277_CANONICAL_MAPPING_GATE_ONLY_NO_DB_WRITE"

except Exception as e:
    result["status"] = "VDF_AKSHARE_CANDIDATE_TO_CANONICAL_MERGE_GATE_REVIEW_WITH_REPAIR_REQUIRED"
    result["risk"] = "HIGH"
    result["error"] = str(e)
    result["recommendation"] = "BLOCK_MERGE_GATE_REVIEW_REPAIR_INPUTS"

out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({
    "status": result["status"],
    "risk": result["risk"],
    "candidate_rows_total": result["candidate_rows_total"],
    "candidate_tables": result["candidate_tables"],
    "quarantine_count": result["quarantine_count"],
    "schema_gate": result["schema_gate"],
    "dedup_gate": result["dedup_gate"],
    "merge_policy_gate": result["merge_policy_gate"],
    "recommendation": result["recommendation"]
}, ensure_ascii=False))
