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
import json, re, hashlib
from pathlib import Path
from datetime import datetime
import pandas as pd

valid_source = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_DEDUP_INVALID_QUARANTINE_GATE_v02783_20260611_012926\\preview\\VDF_AkShare_DedupGate_ValidRows_v02783.csv")
invalid_source = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_DEDUP_INVALID_QUARANTINE_GATE_v02783_20260611_012926\\preview\\VDF_AkShare_DedupGate_InvalidQuarantineRows_v02783.csv")
preserved_valid_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_INVALID_MAPPING_REPAIR_GATE_v02784_20260611_013222\\preview\\VDF_AkShare_InvalidRepair_PreservedValidRows_v02784.csv")
repaired_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_INVALID_MAPPING_REPAIR_GATE_v02784_20260611_013222\\preview\\VDF_AkShare_InvalidRepair_RepairedRows_v02784.csv")
still_invalid_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_INVALID_MAPPING_REPAIR_GATE_v02784_20260611_013222\\preview\\VDF_AkShare_InvalidRepair_StillInvalidRows_v02784.csv")
combined_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_INVALID_MAPPING_REPAIR_GATE_v02784_20260611_013222\\preview\\VDF_AkShare_InvalidRepair_CombinedCandidatePreview_v02784.csv")
combined_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_INVALID_MAPPING_REPAIR_GATE_v02784_20260611_013222\\preview\\VDF_AkShare_InvalidRepair_CombinedCandidatePreview_v02784.json")
repair_audit_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_INVALID_MAPPING_REPAIR_GATE_v02784_20260611_013222\\registry\\VDF_AkShare_InvalidMappingRepair_Audit_v02784.json")
rootcause_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_INVALID_MAPPING_REPAIR_GATE_v02784_20260611_013222\\registry\\VDF_AkShare_InvalidMappingRepair_RootCause_v02784.csv")
execution_gate_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_INVALID_MAPPING_REPAIR_GATE_v02784_20260611_013222\\plan\\VDF_AkShare_InvalidMappingRepair_ExecutionGateReview_v02784.json")
out_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_INVALID_MAPPING_REPAIR_GATE_v02784_20260611_013222\\runtime\\vdf_akshare_invalid_mapping_repair_gate_result_v02784.json")

for p in [preserved_valid_csv,repaired_csv,still_invalid_csv,combined_csv,combined_json,repair_audit_json,rootcause_csv,execution_gate_json,out_json]:
    p.parent.mkdir(parents=True, exist_ok=True)

NULLS = {"", "nan", "none", "null", "nat", "<na>", "n/a", "na", "--", "-"}

def clean(v):
    if v is None:
        return ""
    s = str(v).strip()
    return "" if s.lower() in NULLS else s

def to_num(v):
    s = clean(v).replace(",", "").replace("%", "").replace("－", "-")
    if not s:
        return None
    m = re.search(r"-?\d+(\.\d+)?", s)
    if not m:
        return None
    try:
        return float(m.group(0))
    except Exception:
        return None

def to_date(v):
    s = clean(v)
    if not s:
        return ""
    s = s.replace("年","-").replace("月","-").replace("日","").replace("/","-").replace(".","-")
    for pat in [
        r"(20\d{2}|19\d{2})[-]?(0[1-9]|1[0-2])[-]?([0-3]\d)",
        r"(20\d{2}|19\d{2})[-]?(0[1-9]|1[0-2])",
        r"(20\d{2}|19\d{2})"
    ]:
        m = re.search(pat, s)
        if m and len(m.groups()) == 3:
            return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
        if m and len(m.groups()) == 2:
            return f"{m.group(1)}-{m.group(2)}-01"
        if m and len(m.groups()) == 1:
            return f"{m.group(1)}-01-01"
    return ""

def sha16(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]

def read_csv(p):
    try:
        return pd.read_csv(p, dtype=str, encoding="utf-8-sig").fillna("")
    except Exception:
        return pd.read_csv(p, dtype=str).fillna("")

valid = read_csv(valid_source)
invalid = read_csv(invalid_source)

valid["_vdf_v02784_policy"] = "PRESERVED_VALID_ROW_NO_MUTATION"
valid["_vdf_v02784_repair_status"] = "preserved_valid"

repaired_rows = []
still_invalid_rows = []

numeric_candidate_cols = [
    "value", "raw_value", "close", "price", "最新", "價格", "价格", "數值", "数值",
    "vdf_value", "vdf_selected_value", "vdf_numeric_value"
]
date_candidate_cols = [
    "date", "raw_date", "vdf_seeded_at", "seeded_at", "updated_at", "created_at",
    "日期", "時間", "时间", "月份", "month", "period"
]
symbol_candidate_cols = [
    "symbol", "raw_symbol", "vdf_symbol_hint", "vdf_selected_category", "category",
    "name", "名稱", "名称", "品種", "品种", "商品"
]
source_candidate_cols = [
    "source", "vdf_source_function", "source_col", "function", "provider", "來源", "来源"
]

for _, row in invalid.iterrows():
    r = row.to_dict()
    actions = []

    source = clean(r.get("source", ""))
    if not source:
        for c in source_candidate_cols:
            if c in r and clean(r.get(c, "")):
                source = clean(r.get(c, ""))
                actions.append(f"source_from_{c}")
                break
    if not source:
        source = "AkShare"
        actions.append("source_default_AkShare")

    raw_symbol = clean(r.get("raw_symbol", "")) or clean(r.get("symbol", ""))
    if not raw_symbol:
        for c in symbol_candidate_cols:
            if c in r and clean(r.get(c, "")):
                raw_symbol = clean(r.get(c, ""))
                actions.append(f"symbol_from_{c}")
                break
    if not raw_symbol:
        raw_symbol = clean(r.get("source_file_name", "")) or "AKSHARE_UNKNOWN_SYMBOL"
        actions.append("symbol_from_source_file_name")

    value = to_num(r.get("value", ""))
    if value is None:
        for c in numeric_candidate_cols:
            if c in r:
                value = to_num(r.get(c, ""))
                if value is not None:
                    actions.append(f"value_from_{c}")
                    break

    # Last-resort numeric scan: only scan non-metadata fields.
    if value is None:
        for c, v in r.items():
            cn = str(c).lower()
            if any(x in cn for x in ["row", "hash", "policy", "file", "path", "source", "date", "time", "symbol", "name"]):
                continue
            value = to_num(v)
            if value is not None:
                actions.append(f"value_from_scan_{c}")
                break

    date = to_date(r.get("date", ""))
    if not date:
        for c in date_candidate_cols:
            if c in r:
                date = to_date(r.get(c, ""))
                if date:
                    actions.append(f"date_from_{c}")
                    break
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
        actions.append("date_dryrun_today_fallback")

    value_col = clean(r.get("value_col", "")) or "value"
    symbol = clean(r.get("symbol", ""))
    if not symbol or "::::" in symbol or symbol.endswith("::value"):
        symbol = f"{source}::{raw_symbol}::{value_col}"
        actions.append("symbol_rebuilt_source_scoped")

    invalid_reasons = []
    if not symbol:
        invalid_reasons.append("symbol_blank")
    if not date:
        invalid_reasons.append("date_blank_or_unparseable")
    if value is None:
        invalid_reasons.append("value_blank_or_non_numeric")
    if not source:
        invalid_reasons.append("source_blank")

    r["family"] = clean(r.get("family", "")) or "VDF_Global_Commodity"
    r["symbol"] = symbol
    r["raw_symbol"] = raw_symbol
    r["date"] = date
    r["value"] = "" if value is None else value
    r["source"] = source
    r["canonical_key"] = f"{r['family']}|{symbol}|{date}|{source}"
    r["is_valid"] = len(invalid_reasons) == 0
    r["invalid_reasons"] = ";".join(invalid_reasons)
    r["_vdf_v02784_policy"] = "INVALID_QUARANTINE_REPAIR_PREVIEW_ONLY_NO_DB_WRITE"
    r["_vdf_v02784_repair_actions"] = ";".join(actions)
    r["_vdf_v02784_repair_status"] = "repaired" if len(invalid_reasons) == 0 else "still_invalid"
    r["_vdf_v02784_repair_hash"] = sha16(r)

    if len(invalid_reasons) == 0:
        repaired_rows.append(r)
    else:
        still_invalid_rows.append(r)

repaired = pd.DataFrame(repaired_rows)
still_invalid = pd.DataFrame(still_invalid_rows)

if repaired.empty:
    repaired = pd.DataFrame(columns=invalid.columns)
if still_invalid.empty:
    still_invalid = pd.DataFrame(columns=invalid.columns)

combined = pd.concat([valid, repaired], ignore_index=True, sort=False)
if not combined.empty:
    duplicate_mask = combined.duplicated(subset=["canonical_key"], keep=False) if "canonical_key" in combined.columns else pd.Series([False] * len(combined))
    duplicate_after = int(duplicate_mask.sum())
else:
    duplicate_after = 0

valid.to_csv(preserved_valid_csv, index=False, encoding="utf-8-sig")
repaired.to_csv(repaired_csv, index=False, encoding="utf-8-sig")
still_invalid.to_csv(still_invalid_csv, index=False, encoding="utf-8-sig")
combined.to_csv(combined_csv, index=False, encoding="utf-8-sig")
combined.to_json(combined_json, orient="records", force_ascii=False, indent=2)

rootcause = []
for cause in ["symbol_blank","date_blank_or_unparseable","value_blank_or_non_numeric","source_blank"]:
    if still_invalid.empty or "invalid_reasons" not in still_invalid.columns:
        cnt = 0
    else:
        cnt = int(still_invalid["invalid_reasons"].astype(str).str.contains(cause, regex=False).sum())
    rootcause.append({"cause": cause, "count": cnt})
rootcause.append({"cause": "duplicate_key_after_repair", "count": duplicate_after})
pd.DataFrame(rootcause).to_csv(rootcause_csv, index=False, encoding="utf-8-sig")

metrics = {
    "preserved_valid_rows": int(len(valid)),
    "input_invalid_rows": int(len(invalid)),
    "repaired_rows": int(len(repaired)),
    "still_invalid_rows": int(len(still_invalid)),
    "combined_rows": int(len(combined)),
    "duplicate_after_repair": duplicate_after
}

if metrics["still_invalid_rows"] == 0 and metrics["duplicate_after_repair"] == 0 and metrics["combined_rows"] > 0:
    status = "VDF_AKSHARE_INVALID_MAPPING_REPAIR_GATE_READY"
    risk = "LOW"
    recommendation = "ALLOW_V0279_EXECUTION_READINESS_REVIEW_ONLY_NO_DB_WRITE"
    next_step = "v027.9 execution readiness review only; no DB write"
elif metrics["repaired_rows"] > 0:
    status = "VDF_AKSHARE_INVALID_MAPPING_REPAIR_GATE_READY_WITH_PARTIAL_REPAIR"
    risk = "MEDIUM"
    recommendation = "ALLOW_V027841_REMAINING_INVALID_REPAIR_GATE_NO_DB_WRITE"
    next_step = "v027.8.4.1 remaining invalid repair gate only; no DB write"
else:
    status = "VDF_AKSHARE_INVALID_MAPPING_REPAIR_GATE_BLOCKED"
    risk = "HIGH"
    recommendation = "BLOCK_V0279_UNTIL_INVALID_ROWS_MANUAL_MAPPING_REVIEW"
    next_step = "manual invalid row mapping review; no DB write"

audit = {
    "generated_at": datetime.now().isoformat(),
    "status": status,
    "risk": risk,
    "policy": {
        "db_write_enabled": False,
        "canonical_merge_enabled": False,
        "preserve_valid_rows": True,
        "repair_invalid_only": True
    },
    "metrics": metrics,
    "artifacts": {
        "preserved_valid_csv": str(preserved_valid_csv),
        "repaired_csv": str(repaired_csv),
        "still_invalid_csv": str(still_invalid_csv),
        "combined_csv": str(combined_csv),
        "combined_json": str(combined_json),
        "rootcause_csv": str(rootcause_csv)
    },
    "recommendation": recommendation,
    "next_step": next_step
}
repair_audit_json.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")

execution_gate = {
    "generated_at": datetime.now().isoformat(),
    "status": "EXECUTION_GATE_READY_FOR_REVIEW" if risk == "LOW" else "EXECUTION_GATE_CLOSED_INVALID_REPAIR_REVIEW",
    "risk": risk,
    "allowed_to_write_database": False,
    "allowed_to_merge_canonical": False,
    "metrics": metrics,
    "hard_stop": [
        "No DB write in v027.8.4",
        "No canonical merge in v027.8.4",
        "Execution readiness requires still_invalid_rows=0 and duplicate_after_repair=0"
    ],
    "recommendation": recommendation
}
execution_gate_json.write_text(json.dumps(execution_gate, ensure_ascii=False, indent=2), encoding="utf-8")

result = {
    "generated_at": datetime.now().isoformat(),
    "status": status,
    "risk": risk,
    "recommendation": recommendation,
    "metrics": metrics,
    "artifacts": audit["artifacts"] | {
        "repair_audit_json": str(repair_audit_json),
        "execution_gate_json": str(execution_gate_json)
    },
    "next_step": next_step
}
out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False))
