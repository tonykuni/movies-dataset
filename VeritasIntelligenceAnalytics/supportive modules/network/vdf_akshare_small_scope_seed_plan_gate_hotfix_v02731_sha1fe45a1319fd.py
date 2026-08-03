import json
import csv
from pathlib import Path
from datetime import datetime

sample_result_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_SAMPLE_CALL_GATE_v0272_20260610_143930\\registry\\VDF_AkShare_SampleCallGate_Result_v0272.json")
sample_payload_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_SAMPLE_CALL_GATE_v0272_20260610_143930\\staging\\VDF_AkShare_SamplePayload_Max1Row_v0272.json")
seed_plan_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_SMALL_SCOPE_SEED_PLAN_GATE_HOTFIX_v02731_20260610_144716\\plan\\VDF_AkShare_SmallScopeSeedPlan_v02731.json")
seed_plan_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_SMALL_SCOPE_SEED_PLAN_GATE_HOTFIX_v02731_20260610_144716\\plan\\VDF_AkShare_SmallScopeSeedPlan_v02731.csv")
quarantine_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_SMALL_SCOPE_SEED_PLAN_GATE_HOTFIX_v02731_20260610_144716\\registry\\VDF_AkShare_FailedTimeout_Quarantine_v02731.json")
out = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_SMALL_SCOPE_SEED_PLAN_GATE_HOTFIX_v02731_20260610_144716\\runtime\\vdf_akshare_small_scope_seed_plan_gate_hotfix_result_v02731.json")

CATEGORY_TO_TARGET = {
    "BDI_FREIGHT": {
        "target_table": "VDF_Global_Freight_AkShare_Candidate",
        "canonical_family": "VDF_Global_Freight",
        "symbol_hint": "BDI_OR_FREIGHT_INDEX",
        "priority": "P0"
    },
    "IRON_ORE": {
        "target_table": "VDF_Global_Commodity_AkShare_Candidate",
        "canonical_family": "VDF_Global_Commodity",
        "symbol_hint": "IRON_ORE",
        "priority": "P0"
    },
    "COKING_COAL": {
        "target_table": "VDF_Global_Commodity_AkShare_Candidate",
        "canonical_family": "VDF_Global_Commodity",
        "symbol_hint": "COKING_COAL",
        "priority": "P0"
    },
    "STEEL": {
        "target_table": "VDF_Global_Commodity_AkShare_Candidate",
        "canonical_family": "VDF_Global_Commodity",
        "symbol_hint": "STEEL",
        "priority": "P1"
    },
    "COMMODITY_FUTURES": {
        "target_table": "VDF_Global_Commodity_AkShare_Candidate",
        "canonical_family": "VDF_Global_Commodity",
        "symbol_hint": "COMMODITY_FUTURES",
        "priority": "P1"
    },
    "MACRO_CHINA": {
        "target_table": "VDF_Global_Macro_AkShare_Candidate",
        "canonical_family": "VDF_Global_Macro",
        "symbol_hint": "CHINA_MACRO",
        "priority": "P2"
    }
}

result = {
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "status": "VDF_AKSHARE_SMALL_SCOPE_SEED_PLAN_GATE_HOTFIX_READY",
    "risk": "LOW",
    "policy": "Hotfix plan only. Use OK_SAMPLE only. Quarantine failed/timeout. No function call. No fetch. No DB write.",
    "sample_result_rows": 0,
    "ok_sample_count": 0,
    "quarantine_count": 0,
    "seed_plan_count": 0,
    "categories": {},
    "target_tables": {},
    "recommendation": "UNKNOWN",
    "outputs": {}
}

try:
    if not sample_result_json.exists():
        raise RuntimeError("Sample result JSON missing.")
    if not sample_payload_json.exists():
        raise RuntimeError("Sample payload JSON missing.")

    rows = json.loads(sample_result_json.read_text(encoding="utf-8"))
    payload = json.loads(sample_payload_json.read_text(encoding="utf-8"))

    result["sample_result_rows"] = len(rows)

    ok_rows = [r for r in rows if r.get("status") == "OK_SAMPLE"]
    bad_rows = [r for r in rows if r.get("status") != "OK_SAMPLE"]

    result["ok_sample_count"] = len(ok_rows)
    result["quarantine_count"] = len(bad_rows)

    sample_lookup = {}
    for s in payload.get("max_1row_samples", []):
        sample_lookup[s.get("function")] = s

    plan = []
    for r in ok_rows:
        cat = r.get("selected_category", "")
        meta = CATEGORY_TO_TARGET.get(cat, {
            "target_table": "VDF_AkShare_Unclassified_Candidate",
            "canonical_family": "VDF_Unclassified",
            "symbol_hint": cat or "UNKNOWN",
            "priority": "P3"
        })

        fn = r.get("function", "")
        sample = sample_lookup.get(fn, {})

        plan.append({
            "selected": True,
            "stage": "v027.4_small_scope_candidate_seed_staging_only",
            "mode": "SEED_PLAN_ONLY_NO_DB_WRITE",
            "selected_category": cat,
            "function": fn,
            "priority": meta["priority"],
            "target_table": meta["target_table"],
            "canonical_family": meta["canonical_family"],
            "symbol_hint": meta["symbol_hint"],
            "object_type": r.get("object_type", ""),
            "sample_row_count_reported": r.get("row_count", 0),
            "sample_col_count_reported": r.get("col_count", 0),
            "sample_payload_available": fn in sample_lookup,
            "sample_max_1row": sample.get("sample_max_1row", []),
            "risk": "LOW",
            "reason": "Function passed v027.2 OK_SAMPLE gate.",
            "future_policy": [
                "v027.4 may call only OK_SAMPLE functions from this seed plan.",
                "v027.4 must write staging candidates only.",
                "v027.4 must not overwrite DATABASE canonical tables.",
                "v027.4 must generate candidate CSV/JSON/Parquet.",
                "v027.5 must final-seal candidate before any merge."
            ]
        })

    quarantine = []
    for r in bad_rows:
        quarantine.append({
            "selected": False,
            "selected_category": r.get("selected_category", ""),
            "function": r.get("function", ""),
            "status": r.get("status", ""),
            "risk": "MEDIUM" if r.get("status") in ["CALL_FAIL", "TIMEOUT", "SKIP_REQUIRES_ARGUMENT"] else "HIGH",
            "error": r.get("error", ""),
            "reason": "Excluded from seed plan because it did not pass v027.2 OK_SAMPLE gate.",
            "future_action": "review manually or re-probe with explicit safe args in separate isolated gate"
        })

    result["seed_plan_count"] = len(plan)

    cats = {}
    targets = {}
    for p in plan:
        cats[p["selected_category"]] = cats.get(p["selected_category"], 0) + 1
        targets[p["target_table"]] = targets.get(p["target_table"], 0) + 1

    result["categories"] = cats
    result["target_tables"] = targets

    seed_plan_json.parent.mkdir(parents=True, exist_ok=True)
    seed_plan_json.write_text(json.dumps({
        "generated_at": result["generated_at"],
        "policy": result["policy"],
        "seed_plan_count": result["seed_plan_count"],
        "categories": result["categories"],
        "target_tables": result["target_tables"],
        "plan": plan
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    seed_plan_csv.parent.mkdir(parents=True, exist_ok=True)
    with seed_plan_csv.open("w", encoding="utf-8-sig", newline="") as f:
        fieldnames = [
            "selected_category","function","priority","target_table","canonical_family",
            "symbol_hint","object_type","sample_row_count_reported","sample_col_count_reported",
            "sample_payload_available","risk","reason"
        ]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for p in plan:
            w.writerow({k: p.get(k, "") for k in fieldnames})

    quarantine_json.parent.mkdir(parents=True, exist_ok=True)
    quarantine_json.write_text(json.dumps({
        "generated_at": result["generated_at"],
        "quarantine_count": len(quarantine),
        "quarantine": quarantine
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    result["outputs"] = {
        "seed_plan_json": str(seed_plan_json),
        "seed_plan_csv": str(seed_plan_csv),
        "quarantine_json": str(quarantine_json)
    }

    if result["seed_plan_count"] <= 0:
        result["status"] = "VDF_AKSHARE_SMALL_SCOPE_SEED_PLAN_GATE_HOTFIX_READY_WITH_REVIEW"
        result["risk"] = "MEDIUM"
        result["recommendation"] = "NO_OK_SAMPLE_FUNCTIONS_REVIEW_V0272"
    else:
        result["recommendation"] = "ALLOW_V0274_AKSHARE_SMALL_SCOPE_CANDIDATE_SEED_STAGING_ONLY"

except Exception as e:
    result["status"] = "VDF_AKSHARE_SMALL_SCOPE_SEED_PLAN_GATE_HOTFIX_WITH_REVIEW"
    result["risk"] = "HIGH"
    result["error"] = str(e)
    result["recommendation"] = "BLOCK_SEED_PLAN_GATE_REPAIR_SAMPLE_RESULTS"

out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({
    "status": result["status"],
    "risk": result["risk"],
    "sample_result_rows": result["sample_result_rows"],
    "ok_sample_count": result["ok_sample_count"],
    "quarantine_count": result["quarantine_count"],
    "seed_plan_count": result["seed_plan_count"],
    "categories": result["categories"],
    "target_tables": result["target_tables"],
    "recommendation": result["recommendation"]
}, ensure_ascii=False))
