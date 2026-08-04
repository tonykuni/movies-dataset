import json, re, hashlib
from pathlib import Path
from datetime import datetime
import pandas as pd

file_list_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_RAW_COLUMN_PROFILE_CANONICAL_CONTRACT_HOTFIX_v0278121_20260611_001912\\runtime\\vdf_akshare_input_file_list_v0278121.json")
profile_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_RAW_COLUMN_PROFILE_CANONICAL_CONTRACT_HOTFIX_v0278121_20260611_001912\\registry\\VDF_AkShare_RawColumnProfile_Hotfix_v0278121.csv")
profile_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_RAW_COLUMN_PROFILE_CANONICAL_CONTRACT_HOTFIX_v0278121_20260611_001912\\registry\\VDF_AkShare_RawColumnProfile_Hotfix_v0278121.json")
selection_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_RAW_COLUMN_PROFILE_CANONICAL_CONTRACT_HOTFIX_v0278121_20260611_001912\\registry\\VDF_AkShare_RawColumnSelection_Hotfix_v0278121.csv")
selection_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_RAW_COLUMN_PROFILE_CANONICAL_CONTRACT_HOTFIX_v0278121_20260611_001912\\registry\\VDF_AkShare_RawColumnSelection_Hotfix_v0278121.json")
preview_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_RAW_COLUMN_PROFILE_CANONICAL_CONTRACT_HOTFIX_v0278121_20260611_001912\\preview\\VDF_AkShare_CanonicalContractPreview_Hotfix_v0278121.csv")
preview_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_RAW_COLUMN_PROFILE_CANONICAL_CONTRACT_HOTFIX_v0278121_20260611_001912\\preview\\VDF_AkShare_CanonicalContractPreview_Hotfix_v0278121.json")
invalid_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_RAW_COLUMN_PROFILE_CANONICAL_CONTRACT_HOTFIX_v0278121_20260611_001912\\preview\\VDF_AkShare_CanonicalContractInvalidRows_Hotfix_v0278121.csv")
duplicate_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_RAW_COLUMN_PROFILE_CANONICAL_CONTRACT_HOTFIX_v0278121_20260611_001912\\preview\\VDF_AkShare_CanonicalContractDuplicateRows_Hotfix_v0278121.csv")
rootcause_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_RAW_COLUMN_PROFILE_CANONICAL_CONTRACT_HOTFIX_v0278121_20260611_001912\\registry\\VDF_AkShare_CanonicalContractRootCause_Hotfix_v0278121.csv")
rootcause_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_RAW_COLUMN_PROFILE_CANONICAL_CONTRACT_HOTFIX_v0278121_20260611_001912\\registry\\VDF_AkShare_CanonicalContractRootCause_Hotfix_v0278121.json")
contract_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_RAW_COLUMN_PROFILE_CANONICAL_CONTRACT_HOTFIX_v0278121_20260611_001912\\plan\\VDF_AkShare_CanonicalKeyContract_Hotfix_v0278121.json")
remap_plan_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_RAW_COLUMN_PROFILE_CANONICAL_CONTRACT_HOTFIX_v0278121_20260611_001912\\plan\\VDF_AkShare_RemapPatchPlan_Hotfix_v0278121.json")
out_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_RAW_COLUMN_PROFILE_CANONICAL_CONTRACT_HOTFIX_v0278121_20260611_001912\\runtime\\vdf_akshare_raw_column_profile_contract_hotfix_result_v0278121.json")

NULLS = {"", "nan", "none", "null", "nat", "<na>", "n/a", "na", "--", "-"}

def clean(v):
    if v is None:
        return ""
    s = str(v).strip()
    if s.lower() in NULLS:
        return ""
    return s

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
    patterns = [
        r"(20\d{2}|19\d{2})[-]?(0[1-9]|1[0-2])[-]?([0-3]\d)",
        r"(20\d{2}|19\d{2})[-]?(0[1-9]|1[0-2])",
        r"(20\d{2}|19\d{2})"
    ]
    for i, pat in enumerate(patterns):
        m = re.search(pat, s)
        if m:
            if i == 0:
                return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
            if i == 1:
                return f"{m.group(1)}-{m.group(2)}-01"
            return f"{m.group(1)}-01-01"
    try:
        dt = pd.to_datetime(s, errors="coerce")
        if pd.notna(dt):
            return dt.strftime("%Y-%m-%d")
    except Exception:
        pass
    return ""

def read_records(path):
    p = Path(path)
    try:
        if p.suffix.lower() == ".csv":
            df = pd.read_csv(p, dtype=str, encoding="utf-8-sig").fillna("")
            return df
        if p.suffix.lower() == ".json":
            raw = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                return pd.DataFrame(raw).astype(str).fillna("")
            if isinstance(raw, dict):
                arrays = [(k,v) for k,v in raw.items() if isinstance(v, list)]
                if arrays:
                    arrays.sort(key=lambda x: len(x[1]), reverse=True)
                    return pd.DataFrame(arrays[0][1]).astype(str).fillna("")
                return pd.DataFrame([raw]).astype(str).fillna("")
    except Exception:
        return pd.DataFrame()
    return pd.DataFrame()

def sha16(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]

def profile_col(file_path, df, col):
    vals = df[col].astype(str).map(clean)
    row_count = len(df)
    non_blank = int((vals != "").sum())
    unique = int(vals[vals != ""].nunique())
    sample = " | ".join(vals[vals != ""].head(8).tolist())
    denom = max(1, min(500, non_blank))
    head_vals = vals[vals != ""].head(500)
    numeric_count = sum(1 for x in head_vals if to_num(x) is not None)
    date_count = sum(1 for x in head_vals if to_date(x) != "")

    non_blank_ratio = round(non_blank / max(1,row_count), 4)
    numeric_ratio = round(numeric_count / denom, 4)
    date_ratio = round(date_count / denom, 4)
    name = str(col).lower()

    symbol_score = 0
    if re.search(r"symbol|ticker|code|品種|品种|商品|合約|合约|名稱|名称|name|variety", name):
        symbol_score += 60
    if non_blank_ratio >= .8:
        symbol_score += 15
    if unique <= max(2, int(row_count * .5)):
        symbol_score += 10
    if date_ratio > .4:
        symbol_score -= 40
    if numeric_ratio > .7:
        symbol_score -= 25

    date_score = 0
    if re.search(r"date|time|日期|時間|时间|交易日|報告期|报告期|月份|month|period|year", name):
        date_score += 60
    if date_ratio >= .7:
        date_score += 40
    elif date_ratio >= .3:
        date_score += 20
    if numeric_ratio > .8 and date_ratio < .2:
        date_score -= 25

    value_score = 0
    if re.search(r"value|price|close|open|high|low|指數|指数|價格|价格|收盤|收盘|開盤|开盘|最高|最低|現貨|现货|結算|结算|最新|數值|数值|成交|volume|bdi|cpi|rate|yield|庫存|库存|產量|产量|進口|进口|出口", name):
        value_score += 60
    if numeric_ratio >= .8:
        value_score += 45
    elif numeric_ratio >= .5:
        value_score += 25
    if date_ratio > .4:
        value_score -= 50
    if re.search(r"date|time|日期", name):
        value_score -= 40

    source_score = 0
    if re.search(r"source|function|provider|original|來源|来源|函數|函数|akshare", name):
        source_score += 80
    if non_blank_ratio >= .8:
        source_score += 10

    return {
        "file_path": str(file_path),
        "file_name": Path(file_path).name,
        "column_name": str(col),
        "row_count": row_count,
        "non_blank_count": non_blank,
        "non_blank_ratio": non_blank_ratio,
        "unique_count": unique,
        "numeric_ratio": numeric_ratio,
        "date_ratio": date_ratio,
        "symbol_score": symbol_score,
        "date_score": date_score,
        "value_score": value_score,
        "source_score": source_score,
        "sample_values": sample
    }

def best_col(profiles, score):
    if not profiles:
        return ""
    ranked = sorted(
        [p for p in profiles if p["non_blank_count"] > 0],
        key=lambda x: (x.get(score,0), x.get("non_blank_ratio",0), x.get("numeric_ratio",0)),
        reverse=True
    )
    if not ranked:
        return ""
    return ranked[0]["column_name"]

files = json.loads(file_list_json.read_text(encoding="utf-8"))

profiles = []
selections = []
preview_rows = []

for fp in files:
    df = read_records(fp)
    if df.empty:
        continue

    local_profiles = []
    for col in df.columns:
        pr = profile_col(fp, df, col)
        profiles.append(pr)
        local_profiles.append(pr)

    symbol_col = best_col(local_profiles, "symbol_score")
    date_col = best_col(local_profiles, "date_score")
    value_col = best_col(local_profiles, "value_score")
    source_col = best_col(local_profiles, "source_score")

    selections.append({
        "file_name": Path(fp).name,
        "file_path": fp,
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "symbol_col": symbol_col,
        "date_col": date_col,
        "value_col": value_col,
        "source_col": source_col,
        "symbol_score": max([p["symbol_score"] for p in local_profiles] or [0]),
        "date_score": max([p["date_score"] for p in local_profiles] or [0]),
        "value_score": max([p["value_score"] for p in local_profiles] or [0]),
        "source_score": max([p["source_score"] for p in local_profiles] or [0]),
        "selection_risk": "MEDIUM_REVIEW" if not date_col or not value_col else "LOW"
    })

    for idx, row in df.iterrows():
        symbol = clean(row.get(symbol_col, "")) if symbol_col else ""
        date = to_date(row.get(date_col, "")) if date_col else ""
        val = to_num(row.get(value_col, "")) if value_col else None
        source = clean(row.get(source_col, "")) if source_col else "AkShare"
        if not source:
            source = "AkShare"

        invalid = []
        if not symbol:
            invalid.append("symbol_blank")
        if not date:
            invalid.append("date_blank_or_unparseable")
        if val is None:
            invalid.append("value_blank_or_non_numeric")
        if not source:
            invalid.append("source_blank")

        key = f"VDF_Global_Commodity|{symbol}|{date}|{source}"
        preview_rows.append({
            "row_no": int(idx) + 1,
            "family": "VDF_Global_Commodity",
            "symbol": symbol,
            "date": date,
            "value": val if val is not None else "",
            "source": source,
            "source_file": fp,
            "source_file_name": Path(fp).name,
            "symbol_col": symbol_col,
            "date_col": date_col,
            "value_col": value_col,
            "source_col": source_col,
            "canonical_key": key,
            "is_valid": len(invalid) == 0,
            "invalid_reasons": ";".join(invalid),
            "record_hash": sha16(row.to_dict())
        })

profile_df = pd.DataFrame(profiles)
selection_df = pd.DataFrame(selections)
preview_df = pd.DataFrame(preview_rows)

for p in [profile_csv, profile_json, selection_csv, selection_json, preview_csv, preview_json, invalid_csv, duplicate_csv, rootcause_csv, rootcause_json, contract_json, remap_plan_json, out_json]:
    p.parent.mkdir(parents=True, exist_ok=True)

profile_df.to_csv(profile_csv, index=False, encoding="utf-8-sig")
profile_df.to_json(profile_json, orient="records", force_ascii=False, indent=2)
selection_df.to_csv(selection_csv, index=False, encoding="utf-8-sig")
selection_df.to_json(selection_json, orient="records", force_ascii=False, indent=2)
preview_df.to_csv(preview_csv, index=False, encoding="utf-8-sig")
preview_df.to_json(preview_json, orient="records", force_ascii=False, indent=2)

invalid_df = preview_df[preview_df["is_valid"] != True] if not preview_df.empty else preview_df
valid_df = preview_df[preview_df["is_valid"] == True] if not preview_df.empty else preview_df

dup_df = pd.DataFrame()
if not valid_df.empty and "canonical_key" in valid_df.columns:
    dup_mask = valid_df.duplicated(subset=["canonical_key"], keep=False)
    dup_df = valid_df[dup_mask].copy()

invalid_df.to_csv(invalid_csv, index=False, encoding="utf-8-sig")
dup_df.to_csv(duplicate_csv, index=False, encoding="utf-8-sig")

rootcause = []
for cause in ["symbol_blank", "date_blank_or_unparseable", "value_blank_or_non_numeric", "source_blank"]:
    if invalid_df.empty:
        c = 0
    else:
        c = int(invalid_df["invalid_reasons"].astype(str).str.contains(cause, regex=False).sum())
    rootcause.append({"cause": cause, "count": c})
rootcause.append({"cause": "duplicate_key_after_contract", "count": int(len(dup_df))})

pd.DataFrame(rootcause).to_csv(rootcause_csv, index=False, encoding="utf-8-sig")
rootcause_json.write_text(json.dumps(rootcause, ensure_ascii=False, indent=2), encoding="utf-8")

preview_count = int(len(preview_df))
valid_count = int(len(valid_df))
invalid_count = int(len(invalid_df))
duplicate_count = int(len(dup_df))

risk = "LOW" if invalid_count == 0 and duplicate_count == 0 and valid_count > 0 else ("MEDIUM" if valid_count > 0 else "HIGH")
status = "VDF_AKSHARE_RAW_COLUMN_PROFILE_CANONICAL_CONTRACT_HOTFIX_READY" if risk == "LOW" else ("VDF_AKSHARE_RAW_COLUMN_PROFILE_CANONICAL_CONTRACT_HOTFIX_READY_WITH_REVIEW" if risk == "MEDIUM" else "VDF_AKSHARE_RAW_COLUMN_PROFILE_CANONICAL_CONTRACT_HOTFIX_BLOCKED_WITH_MAPPING_REVIEW")
recommendation = "ALLOW_V02782_CONTRACT_BASED_SMART_REPAIRED_DRYRUN_NO_DB_WRITE" if valid_count > 0 else "BLOCK_V02782_UNTIL_RAW_VALUE_DATE_MAPPING_REVIEW"

contract = {
    "generated_at": datetime.now().isoformat(),
    "status": "VDF_AKSHARE_CANONICAL_KEY_CONTRACT_HOTFIX_v0278121",
    "risk": risk,
    "scope": "VDF_Global_Commodity_AkShare_Candidate",
    "db_write_enabled": False,
    "canonical_merge_enabled": False,
    "canonical_family": "VDF_Global_Commodity",
    "required_fields": ["family","symbol","date","value","source"],
    "primary_key": ["family","symbol","date","source"],
    "validity_rule": "valid only when symbol/date/value/source are non-blank and value is numeric",
    "stop_conditions": [
        "invalid_after_contract > 0",
        "duplicate_after_contract > 0",
        "db_write_enabled = true",
        "canonical_merge_enabled = true"
    ],
    "metrics": {
        "input_files": len(files),
        "profile_columns": len(profiles),
        "selection_files": len(selections),
        "preview_rows": preview_count,
        "valid_rows": valid_count,
        "invalid_after_contract": invalid_count,
        "duplicate_after_contract": duplicate_count
    },
    "next_step": "v027.8.2 contract-based smart-repaired dry-run only; no DB write"
}
contract_json.write_text(json.dumps(contract, ensure_ascii=False, indent=2), encoding="utf-8")

remap = {
    "generated_at": datetime.now().isoformat(),
    "status": "VDF_AKSHARE_REMAP_PATCH_PLAN_HOTFIX_v0278121",
    "risk": risk,
    "policy": {
        "db_write_enabled": False,
        "canonical_merge_enabled": False,
        "destructive_delete_enabled": False,
        "stop_process_enabled": False
    },
    "raw_column_profile": str(profile_csv),
    "raw_column_selection": str(selection_csv),
    "contract_preview": str(preview_csv),
    "invalid_rows": str(invalid_csv),
    "duplicate_rows": str(duplicate_csv),
    "repair_order": [
        "Fix value mapping first.",
        "Fix date mapping second.",
        "Run v027.8.2 dry-run only.",
        "Run v027.8.3 dedup gate.",
        "Only enter v027.9 if invalid_after=0 and duplicate_after=0."
    ],
    "recommendation": recommendation
}
remap_plan_json.write_text(json.dumps(remap, ensure_ascii=False, indent=2), encoding="utf-8")

result = {
    "generated_at": datetime.now().isoformat(),
    "status": status,
    "risk": risk,
    "metrics": contract["metrics"],
    "recommendation": recommendation,
    "artifacts": {
        "profile_csv": str(profile_csv),
        "profile_json": str(profile_json),
        "selection_csv": str(selection_csv),
        "selection_json": str(selection_json),
        "preview_csv": str(preview_csv),
        "preview_json": str(preview_json),
        "invalid_csv": str(invalid_csv),
        "duplicate_csv": str(duplicate_csv),
        "rootcause_csv": str(rootcause_csv),
        "rootcause_json": str(rootcause_json),
        "contract_json": str(contract_json),
        "remap_plan_json": str(remap_plan_json)
    },
    "next_step": "v027.8.2 contract-based smart-repaired dry-run only; no DB write"
}
out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False))
