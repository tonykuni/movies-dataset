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

dryrun_preview_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_CANDIDATE_TO_CANONICAL_DRYRUN_v0278_20260610_220705\\preview\\VDF_AkShare_CandidateToCanonicalDryRunPreview_v0278.csv")
dryrun_preview_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_CANDIDATE_TO_CANONICAL_DRYRUN_v0278_20260610_220705\\preview\\VDF_AkShare_CandidateToCanonicalDryRunPreview_v0278.json")
dryrun_audit_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_CANDIDATE_TO_CANONICAL_DRYRUN_v0278_20260610_220705\\registry\\VDF_AkShare_CandidateToCanonicalDryRunAudit_v0278.json")
canonical_preview_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_CANONICAL_MAPPING_GATE_v0277_20260610_220358\\preview\\VDF_AkShare_CanonicalPreview_v0277.csv")
mapping_rules_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_CANONICAL_MAPPING_GATE_v0277_20260610_220358\\registry\\VDF_AkShare_CanonicalMappingRules_v0277.json")

repair_audit_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_CANONICAL_KEY_REPAIR_GATE_v02781_20260610_221005\\registry\\VDF_AkShare_CanonicalKeyRepairAudit_v02781.json")
repaired_preview_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_CANONICAL_KEY_REPAIR_GATE_v02781_20260610_221005\\preview\\VDF_AkShare_CanonicalRepairedPreview_v02781.json")
repaired_preview_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_CANONICAL_KEY_REPAIR_GATE_v02781_20260610_221005\\preview\\VDF_AkShare_CanonicalRepairedPreview_v02781.csv")
readiness_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_CANONICAL_KEY_REPAIR_GATE_v02781_20260610_221005\\registry\\VDF_AkShare_KeyRepairReadinessGate_v02781.json")
out = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_CANONICAL_KEY_REPAIR_GATE_v02781_20260610_221005\\runtime\\vdf_akshare_canonical_key_repair_gate_result_v02781.json")

NULL_LIKE = {"", "nan", "none", "null", "nat", "<na>", "n/a", "na", "--", "-"}

def clean(v):
    s = str(v).strip()
    if s.lower() in NULL_LIKE:
        return ""
    return s

def numeric_or_blank(v):
    s = clean(v).replace(",", "")
    if not s:
        return ""
    m = re.search(r"-?\d+(\.\d+)?", s)
    return m.group(0) if m else ""

def normalize_date(v):
    s = clean(v)
    if not s:
        return ""
    # yyyy-mm-dd / yyyy/mm/dd / yyyymmdd
    s2 = s.replace("/", "-").replace(".", "-")
    m = re.search(r"(20\d{2}|19\d{2})[-]?(0[1-9]|1[0-2])[-]?([0-3]\d)", s2)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    # yyyy-mm
    m = re.search(r"(20\d{2}|19\d{2})[-]?(0[1-9]|1[0-2])", s2)
    if m:
        return f"{m.group(1)}-{m.group(2)}-01"
    return s

def row_hash(row):
    return hashlib.sha256(json.dumps(row, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]

result = {
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "status": "VDF_AKSHARE_CANONICAL_KEY_REPAIR_GATE_READY",
    "risk": "LOW",
    "policy": "Key repair preview only. No DATABASE write. No canonical merge.",
    "input_rows": 0,
    "invalid_before": 0,
    "invalid_after": 0,
    "repaired_rows": 0,
    "unrepaired_rows": 0,
    "duplicate_key_rows_after": 0,
    "repair_actions": {},
    "recommendation": "UNKNOWN"
}

try:
    import pandas as pd

    if not dryrun_preview_csv.exists():
        raise RuntimeError("Dry-run preview CSV missing.")
    if not dryrun_preview_json.exists():
        raise RuntimeError("Dry-run preview JSON missing.")
    if not dryrun_audit_json.exists():
        raise RuntimeError("Dry-run audit JSON missing.")
    if not canonical_preview_csv.exists():
        raise RuntimeError("Canonical preview CSV missing.")
    if not mapping_rules_json.exists():
        raise RuntimeError("Mapping rules JSON missing.")

    df = pd.read_csv(dryrun_preview_csv).astype(str).fillna("")
    original = df.copy()
    result["input_rows"] = int(len(df))

    required = ["canonical_family", "symbol", "date", "value", "source"]
    for c in required:
        if c not in df.columns:
            df[c] = ""

    def is_invalid(frame):
        chk = frame.copy()
        bad = (
            chk["symbol"].apply(lambda x: clean(x) == "") |
            chk["date"].apply(lambda x: clean(x) == "") |
            chk["value"].apply(lambda x: numeric_or_blank(x) == "") |
            chk["source"].apply(lambda x: clean(x) == "")
        )
        return bad

    invalid_before_mask = is_invalid(df)
    result["invalid_before"] = int(invalid_before_mask.sum())

    repair_counts = {
        "symbol_from_family_or_target": 0,
        "date_from_seeded_at": 0,
        "date_from_today": 0,
        "value_numeric_clean": 0,
        "source_from_original_function": 0,
        "source_from_akshare": 0,
        "family_defaulted": 0
    }

    today = datetime.now().strftime("%Y-%m-%d")

    for i, row in df.iterrows():
        # canonical family
        if clean(row.get("canonical_family", "")) == "":
            df.at[i, "canonical_family"] = "VDF_Global_Commodity"
            repair_counts["family_defaulted"] += 1

        # symbol
        if clean(row.get("symbol", "")) == "":
            hint = clean(row.get("vdf_symbol_hint", ""))
            target = clean(row.get("vdf_target_table", ""))
            family = clean(row.get("canonical_family", "VDF_Global_Commodity"))
            if hint:
                df.at[i, "symbol"] = hint
            elif "Commodity" in target or "Commodity" in family:
                df.at[i, "symbol"] = "AKSHARE_COMMODITY"
            else:
                df.at[i, "symbol"] = "AKSHARE_SERIES"
            repair_counts["symbol_from_family_or_target"] += 1

        # date
        if clean(row.get("date", "")) == "":
            seeded = normalize_date(row.get("vdf_seeded_at", ""))
            if seeded:
                df.at[i, "date"] = seeded
                repair_counts["date_from_seeded_at"] += 1
            else:
                df.at[i, "date"] = today
                repair_counts["date_from_today"] += 1
        else:
            df.at[i, "date"] = normalize_date(row.get("date", ""))

        # value
        val = numeric_or_blank(row.get("value", ""))
        if val:
            if str(row.get("value","")) != val:
                repair_counts["value_numeric_clean"] += 1
            df.at[i, "value"] = val

        # source
        if clean(row.get("source", "")) == "":
            src = clean(row.get("vdf_source_function", ""))
            if src:
                df.at[i, "source"] = src
                repair_counts["source_from_original_function"] += 1
            else:
                df.at[i, "source"] = "akshare"
                repair_counts["source_from_akshare"] += 1

    invalid_after_mask = is_invalid(df)
    result["invalid_after"] = int(invalid_after_mask.sum())
    result["repaired_rows"] = int(result["invalid_before"] - result["invalid_after"])
    result["unrepaired_rows"] = int(result["invalid_after"])
    result["repair_actions"] = repair_counts

    key_cols = ["canonical_family", "symbol", "date", "source", "value"]
    df["_vdf_repaired_key"] = df[key_cols].astype(str).agg("|".join, axis=1)
    result["duplicate_key_rows_after"] = int(df.duplicated(subset=["_vdf_repaired_key"], keep=False).sum())

    df["_vdf_key_repair_gate"] = "v027.8.1"
    df["_vdf_key_repair_policy"] = "REPAIR_PREVIEW_ONLY_NO_DATABASE_WRITE"
    df["_vdf_key_repair_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df["_vdf_key_repair_row_hash"] = df.apply(lambda r: row_hash(r.to_dict()), axis=1)

    export_df = df.drop(columns=["_vdf_repaired_key"], errors="ignore")

    repaired_preview_csv.parent.mkdir(parents=True, exist_ok=True)
    export_df.to_csv(repaired_preview_csv, index=False, encoding="utf-8-sig")

    repaired_preview_json.parent.mkdir(parents=True, exist_ok=True)
    export_df.to_json(repaired_preview_json, orient="records", force_ascii=False, indent=2)

    audit = {
        "generated_at": result["generated_at"],
        "policy": result["policy"],
        "input_rows": result["input_rows"],
        "invalid_before": result["invalid_before"],
        "invalid_after": result["invalid_after"],
        "repaired_rows": result["repaired_rows"],
        "unrepaired_rows": result["unrepaired_rows"],
        "duplicate_key_rows_after": result["duplicate_key_rows_after"],
        "repair_actions": repair_counts,
        "repaired_preview_csv": str(repaired_preview_csv),
        "repaired_preview_json": str(repaired_preview_json)
    }

    repair_audit_json.parent.mkdir(parents=True, exist_ok=True)
    repair_audit_json.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")

    readiness = {
        "generated_at": result["generated_at"],
        "allowed_to_write_database_now": False,
        "allowed_to_merge_canonical_now": False,
        "input_rows": result["input_rows"],
        "invalid_before": result["invalid_before"],
        "invalid_after": result["invalid_after"],
        "duplicate_key_rows_after": result["duplicate_key_rows_after"],
        "next_step": "v027.8.2 repaired dry-run only; no DB write",
        "notes": [
            "Key repair produced preview only.",
            "DATABASE write remains blocked.",
            "Canonical merge remains blocked.",
            "Use repaired preview for next dry-run."
        ]
    }

    if result["invalid_after"] > 0:
        result["status"] = "VDF_AKSHARE_CANONICAL_KEY_REPAIR_GATE_READY_WITH_REVIEW"
        result["risk"] = "MEDIUM"
        result["recommendation"] = "ALLOW_V02782_REPAIRED_DRYRUN_WITH_REVIEW_NO_DB_WRITE"
        readiness["status"] = "READY_WITH_KEY_REVIEW"
        readiness["risk"] = "MEDIUM"
    elif result["duplicate_key_rows_after"] > 0:
        result["status"] = "VDF_AKSHARE_CANONICAL_KEY_REPAIR_GATE_READY_WITH_DEDUP_REVIEW"
        result["risk"] = "MEDIUM"
        result["recommendation"] = "ALLOW_V02782_REPAIRED_DRYRUN_WITH_DEDUP_REVIEW_NO_DB_WRITE"
        readiness["status"] = "READY_WITH_DEDUP_REVIEW"
        readiness["risk"] = "MEDIUM"
    else:
        result["status"] = "VDF_AKSHARE_CANONICAL_KEY_REPAIR_GATE_READY"
        result["risk"] = "LOW"
        result["recommendation"] = "ALLOW_V02782_REPAIRED_DRYRUN_ONLY_NO_DB_WRITE"
        readiness["status"] = "READY_FOR_V02782_REPAIRED_DRYRUN"
        readiness["risk"] = "LOW"

    readiness_json.parent.mkdir(parents=True, exist_ok=True)
    readiness_json.write_text(json.dumps(readiness, ensure_ascii=False, indent=2), encoding="utf-8")

except Exception as e:
    result["status"] = "VDF_AKSHARE_CANONICAL_KEY_REPAIR_GATE_WITH_REPAIR_REQUIRED"
    result["risk"] = "HIGH"
    result["error"] = str(e)
    result["recommendation"] = "BLOCK_KEY_REPAIR_GATE_REPAIR_INPUTS"

out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({
    "status": result["status"],
    "risk": result["risk"],
    "input_rows": result["input_rows"],
    "invalid_before": result["invalid_before"],
    "invalid_after": result["invalid_after"],
    "repaired_rows": result["repaired_rows"],
    "unrepaired_rows": result["unrepaired_rows"],
    "duplicate_key_rows_after": result["duplicate_key_rows_after"],
    "repair_actions": result["repair_actions"],
    "recommendation": result["recommendation"]
}, ensure_ascii=False))
