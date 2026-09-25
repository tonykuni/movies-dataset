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
canonical_preview_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_CANONICAL_MAPPING_GATE_v0277_20260610_220358\\preview\\VDF_AkShare_CanonicalPreview_v0277.csv")
repaired_preview_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_CANONICAL_KEY_REPAIR_GATE_v02781_20260610_221005\\preview\\VDF_AkShare_CanonicalRepairedPreview_v02781.csv")
mapping_rules_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_CANONICAL_MAPPING_GATE_v0277_20260610_220358\\registry\\VDF_AkShare_CanonicalMappingRules_v0277.json")

rootcause_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_KEY_REPAIR_ROOTCAUSE_SMART_REMAP_v027811_20260610_221501\\registry\\VDF_AkShare_KeyInvalidRootCause_v027811.json")
smart_rules_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_KEY_REPAIR_ROOTCAUSE_SMART_REMAP_v027811_20260610_221501\\registry\\VDF_AkShare_SmartRemapRules_v027811.json")
smart_preview_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_KEY_REPAIR_ROOTCAUSE_SMART_REMAP_v027811_20260610_221501\\preview\\VDF_AkShare_SmartRepairedPreview_v027811.csv")
smart_preview_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_KEY_REPAIR_ROOTCAUSE_SMART_REMAP_v027811_20260610_221501\\preview\\VDF_AkShare_SmartRepairedPreview_v027811.json")
readiness_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_KEY_REPAIR_ROOTCAUSE_SMART_REMAP_v027811_20260610_221501\\registry\\VDF_AkShare_SmartRemapReadinessGate_v027811.json")
out = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_KEY_REPAIR_ROOTCAUSE_SMART_REMAP_v027811_20260610_221501\\runtime\\vdf_akshare_key_repair_rootcause_smart_remap_result_v027811.json")

NULL_LIKE = {"", "nan", "none", "null", "nat", "<na>", "n/a", "na", "--", "-"}

DATE_HINTS = [
    "date","日期","時間","时间","day","交易日","统计日期","報告期","报告期","月份","month","year","年度","年月"
]
VALUE_HINTS = [
    "value","price","close","last","settle","结算","收盘","最新","現值","现值","价格","價格","指数","點位","点位",
    "rate","yield","volume","库存","庫存","产量","產量","进口","進口","出口","金额","金額","数量","數量"
]
SYMBOL_HINTS = [
    "symbol","品种","品種","商品","指数名称","名稱","名称","name","variety","合约","合約","指标","指標"
]

def clean(v):
    s = str(v).strip()
    if s.lower() in NULL_LIKE:
        return ""
    return s

def numeric_or_blank(v):
    s = clean(v).replace(",", "").replace("%", "")
    if not s:
        return ""
    m = re.search(r"-?\d+(\.\d+)?", s)
    return m.group(0) if m else ""

def normalize_date(v):
    s = clean(v)
    if not s:
        return ""
    s = s.replace("/", "-").replace(".", "-").replace("年", "-").replace("月", "-").replace("日", "")
    m = re.search(r"(20\d{2}|19\d{2})[-]?(0[1-9]|1[0-2])[-]?([0-3]\d)", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m = re.search(r"(20\d{2}|19\d{2})[-]?(0[1-9]|1[0-2])", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}-01"
    m = re.search(r"(20\d{2}|19\d{2})", s)
    if m:
        return f"{m.group(1)}-01-01"
    return ""

def score_column(series, mode):
    vals = series.astype(str).fillna("").map(clean)
    nonempty = vals.map(lambda x: x != "").sum()
    if len(vals) == 0:
        return 0
    if mode == "value":
        num = vals.map(numeric_or_blank).map(lambda x: x != "").sum()
        return num / max(len(vals), 1)
    if mode == "date":
        dt = vals.map(normalize_date).map(lambda x: x != "").sum()
        return dt / max(len(vals), 1)
    if mode == "symbol":
        return nonempty / max(len(vals), 1)
    return 0

def choose_best_col(df, hints, mode):
    cols = [c for c in df.columns if not str(c).startswith("_vdf_")]
    ranked = []
    for c in cols:
        name_score = 0
        for h in hints:
            if h.lower() in str(c).lower():
                name_score += 2
        val_score = score_column(df[c], mode)
        total = name_score + val_score
        ranked.append((total, val_score, c))
    ranked = sorted(ranked, reverse=True)
    if ranked and ranked[0][0] > 0:
        return ranked[0][2], ranked[:8]
    return "", ranked[:8]

def row_hash(row):
    return hashlib.sha256(json.dumps(row, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]

result = {
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "status": "VDF_AKSHARE_KEY_REPAIR_ROOTCAUSE_SMART_REMAP_READY",
    "risk": "LOW",
    "policy": "Root-cause and smart remap only. No DATABASE write. No canonical merge.",
    "input_rows": 0,
    "invalid_before": 0,
    "invalid_after": 0,
    "smart_repaired_rows": 0,
    "unrepaired_rows": 0,
    "duplicate_key_rows_after": 0,
    "selected_columns": {},
    "root_causes": {},
    "recommendation": "UNKNOWN"
}

try:
    import pandas as pd

    if not dryrun_preview_csv.exists():
        raise RuntimeError("Dry-run preview CSV missing.")
    if not canonical_preview_csv.exists():
        raise RuntimeError("Canonical preview CSV missing.")
    if not repaired_preview_csv.exists():
        raise RuntimeError("Repaired preview CSV missing.")
    if not mapping_rules_json.exists():
        raise RuntimeError("Mapping rules JSON missing.")

    dry = pd.read_csv(dryrun_preview_csv).astype(str).fillna("")
    can = pd.read_csv(canonical_preview_csv).astype(str).fillna("")
    rep = pd.read_csv(repaired_preview_csv).astype(str).fillna("")

    result["input_rows"] = int(len(dry))

    required = ["canonical_family","symbol","date","value","source"]
    for c in required:
        if c not in dry.columns:
            dry[c] = ""

    def invalid_mask(df):
        return (
            df["symbol"].map(clean).eq("") |
            df["date"].map(clean).eq("") |
            df["value"].map(numeric_or_blank).eq("") |
            df["source"].map(clean).eq("")
        )

    before_mask = invalid_mask(dry)
    result["invalid_before"] = int(before_mask.sum())

    root = {
        "symbol_blank": int(dry["symbol"].map(clean).eq("").sum()),
        "date_blank_or_unparseable": int(dry["date"].map(normalize_date).eq("").sum()),
        "value_blank_or_non_numeric": int(dry["value"].map(numeric_or_blank).eq("").sum()),
        "source_blank": int(dry["source"].map(clean).eq("").sum()),
        "columns": list(dry.columns),
        "canonical_preview_columns": list(can.columns)
    }

    # Use canonical preview if it has more raw columns than dry-run preview.
    source_df = can.copy()
    if len(source_df) != len(dry):
        source_df = dry.copy()

    value_col, value_rank = choose_best_col(source_df, VALUE_HINTS, "value")
    date_col, date_rank = choose_best_col(source_df, DATE_HINTS, "date")
    symbol_col, symbol_rank = choose_best_col(source_df, SYMBOL_HINTS, "symbol")

    smart = dry.copy()

    # family/source defaults
    smart["canonical_family"] = smart["canonical_family"].map(lambda x: clean(x) or "VDF_Global_Commodity")
    smart["source"] = smart["source"].map(lambda x: clean(x) or "akshare")

    # symbol: prefer existing, then vdf_symbol_hint, then selected raw symbol-like col, then category/family fallback
    for i in range(len(smart)):
        if clean(smart.at[i, "symbol"]) == "":
            hint = clean(smart.at[i, "vdf_symbol_hint"]) if "vdf_symbol_hint" in smart.columns else ""
            if hint:
                smart.at[i, "symbol"] = hint
            elif symbol_col and symbol_col in source_df.columns:
                smart.at[i, "symbol"] = clean(source_df.iloc[i][symbol_col])
            else:
                cat = clean(smart.at[i, "description"]) if "description" in smart.columns else ""
                smart.at[i, "symbol"] = cat or "AKSHARE_COMMODITY"

    # date: prefer existing parseable, then raw date-like col, then vdf_seeded_at, then today
    today = datetime.now().strftime("%Y-%m-%d")
    for i in range(len(smart)):
        d = normalize_date(smart.at[i, "date"])
        if not d and date_col and date_col in source_df.columns:
            d = normalize_date(source_df.iloc[i][date_col])
        if not d and "vdf_seeded_at" in smart.columns:
            d = normalize_date(smart.at[i, "vdf_seeded_at"])
        if not d:
            d = today
        smart.at[i, "date"] = d

    # value: prefer existing numeric, then selected raw numeric col, then any row numeric fallback
    for i in range(len(smart)):
        val = numeric_or_blank(smart.at[i, "value"])
        if not val and value_col and value_col in source_df.columns:
            val = numeric_or_blank(source_df.iloc[i][value_col])
        if not val:
            for c in source_df.columns:
                if str(c).startswith("vdf_") or str(c).startswith("_vdf_"):
                    continue
                val = numeric_or_blank(source_df.iloc[i][c])
                if val:
                    break
        smart.at[i, "value"] = val

    after_mask = invalid_mask(smart)
    result["invalid_after"] = int(after_mask.sum())
    result["smart_repaired_rows"] = int(result["invalid_before"] - result["invalid_after"])
    result["unrepaired_rows"] = int(result["invalid_after"])

    key_cols = ["canonical_family","symbol","date","source","value"]
    smart["_vdf_smart_key"] = smart[key_cols].astype(str).agg("|".join, axis=1)
    result["duplicate_key_rows_after"] = int(smart.duplicated(subset=["_vdf_smart_key"], keep=False).sum())

    smart["_vdf_smart_remap_gate"] = "v027.8.1.1"
    smart["_vdf_smart_remap_policy"] = "SMART_REMAP_PREVIEW_ONLY_NO_DATABASE_WRITE"
    smart["_vdf_smart_remap_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    smart["_vdf_smart_row_hash"] = smart.apply(lambda r: row_hash(r.to_dict()), axis=1)

    export_df = smart.drop(columns=["_vdf_smart_key"], errors="ignore")

    smart_preview_csv.parent.mkdir(parents=True, exist_ok=True)
    export_df.to_csv(smart_preview_csv, index=False, encoding="utf-8-sig")
    smart_preview_json.parent.mkdir(parents=True, exist_ok=True)
    export_df.to_json(smart_preview_json, orient="records", force_ascii=False, indent=2)

    result["selected_columns"] = {
        "date_col": date_col,
        "value_col": value_col,
        "symbol_col": symbol_col
    }
    result["root_causes"] = root

    rootcause_json.parent.mkdir(parents=True, exist_ok=True)
    rootcause_json.write_text(json.dumps({
        "generated_at": result["generated_at"],
        "root_causes": root,
        "date_rank": [(float(a), float(b), str(c)) for a,b,c in date_rank],
        "value_rank": [(float(a), float(b), str(c)) for a,b,c in value_rank],
        "symbol_rank": [(float(a), float(b), str(c)) for a,b,c in symbol_rank]
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    smart_rules_json.parent.mkdir(parents=True, exist_ok=True)
    smart_rules_json.write_text(json.dumps({
        "generated_at": result["generated_at"],
        "policy": result["policy"],
        "selected_columns": result["selected_columns"],
        "rules": [
            "symbol = existing symbol OR vdf_symbol_hint OR best symbol-like raw column OR category/fallback",
            "date = parse existing date OR best date-like raw column OR vdf_seeded_at OR today",
            "value = numeric existing value OR best numeric raw column OR first numeric raw field",
            "source = existing source OR akshare",
            "canonical_family = existing family OR VDF_Global_Commodity"
        ]
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    readiness = {
        "generated_at": result["generated_at"],
        "status": "READY_FOR_V02782_SMART_REPAIRED_DRYRUN",
        "risk": "LOW",
        "allowed_to_write_database_now": False,
        "allowed_to_merge_canonical_now": False,
        "input_rows": result["input_rows"],
        "invalid_before": result["invalid_before"],
        "invalid_after": result["invalid_after"],
        "duplicate_key_rows_after": result["duplicate_key_rows_after"],
        "smart_preview_csv": str(smart_preview_csv),
        "smart_preview_json": str(smart_preview_json),
        "next_step": "v027.8.2 AkShare smart-repaired candidate-to-canonical dry-run only; no DB write"
    }

    if result["invalid_after"] > 0:
        result["status"] = "VDF_AKSHARE_KEY_REPAIR_ROOTCAUSE_SMART_REMAP_READY_WITH_REVIEW"
        result["risk"] = "MEDIUM"
        result["recommendation"] = "ALLOW_V02782_SMART_REPAIRED_DRYRUN_WITH_REVIEW_NO_DB_WRITE"
        readiness["status"] = "READY_WITH_REVIEW"
        readiness["risk"] = "MEDIUM"
    elif result["duplicate_key_rows_after"] > 0:
        result["status"] = "VDF_AKSHARE_KEY_REPAIR_ROOTCAUSE_SMART_REMAP_READY_WITH_DEDUP_REVIEW"
        result["risk"] = "MEDIUM"
        result["recommendation"] = "ALLOW_V02782_SMART_REPAIRED_DRYRUN_WITH_DEDUP_REVIEW_NO_DB_WRITE"
        readiness["status"] = "READY_WITH_DEDUP_REVIEW"
        readiness["risk"] = "MEDIUM"
    else:
        result["status"] = "VDF_AKSHARE_KEY_REPAIR_ROOTCAUSE_SMART_REMAP_READY"
        result["risk"] = "LOW"
        result["recommendation"] = "ALLOW_V02782_SMART_REPAIRED_DRYRUN_ONLY_NO_DB_WRITE"

    readiness_json.parent.mkdir(parents=True, exist_ok=True)
    readiness_json.write_text(json.dumps(readiness, ensure_ascii=False, indent=2), encoding="utf-8")

except Exception as e:
    result["status"] = "VDF_AKSHARE_KEY_REPAIR_ROOTCAUSE_SMART_REMAP_WITH_REPAIR_REQUIRED"
    result["risk"] = "HIGH"
    result["error"] = str(e)
    result["recommendation"] = "BLOCK_SMART_REMAP_REPAIR_INPUTS"

out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({
    "status": result["status"],
    "risk": result["risk"],
    "input_rows": result["input_rows"],
    "invalid_before": result["invalid_before"],
    "invalid_after": result["invalid_after"],
    "smart_repaired_rows": result["smart_repaired_rows"],
    "unrepaired_rows": result["unrepaired_rows"],
    "duplicate_key_rows_after": result["duplicate_key_rows_after"],
    "selected_columns": result["selected_columns"],
    "root_causes": result["root_causes"],
    "recommendation": result["recommendation"]
}, ensure_ascii=False))
