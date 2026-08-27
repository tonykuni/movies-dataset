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

file_list_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_NARROW_SOURCE_CONTRACT_DRYRUN_v02782_20260611_002315\\runtime\\vdf_akshare_v0274_source_file_list_v02782.json")
profile_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_NARROW_SOURCE_CONTRACT_DRYRUN_v02782_20260611_002315\\registry\\VDF_AkShare_NarrowSource_RawColumnProfile_v02782.csv")
selection_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_NARROW_SOURCE_CONTRACT_DRYRUN_v02782_20260611_002315\\registry\\VDF_AkShare_NarrowSource_RawColumnSelection_v02782.csv")
preview_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_NARROW_SOURCE_CONTRACT_DRYRUN_v02782_20260611_002315\\preview\\VDF_AkShare_NarrowSource_ContractDryRunPreview_v02782.csv")
preview_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_NARROW_SOURCE_CONTRACT_DRYRUN_v02782_20260611_002315\\preview\\VDF_AkShare_NarrowSource_ContractDryRunPreview_v02782.json")
invalid_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_NARROW_SOURCE_CONTRACT_DRYRUN_v02782_20260611_002315\\preview\\VDF_AkShare_NarrowSource_InvalidRows_v02782.csv")
duplicate_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_NARROW_SOURCE_CONTRACT_DRYRUN_v02782_20260611_002315\\preview\\VDF_AkShare_NarrowSource_DuplicateRows_v02782.csv")
rootcause_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_NARROW_SOURCE_CONTRACT_DRYRUN_v02782_20260611_002315\\registry\\VDF_AkShare_NarrowSource_RootCause_v02782.csv")
contract_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_NARROW_SOURCE_CONTRACT_DRYRUN_v02782_20260611_002315\\plan\\VDF_AkShare_NarrowSource_CanonicalKeyContract_v02782.json")
execution_gate_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_NARROW_SOURCE_CONTRACT_DRYRUN_v02782_20260611_002315\\plan\\VDF_AkShare_NarrowSource_ExecutionGateReview_v02782.json")
out_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_NARROW_SOURCE_CONTRACT_DRYRUN_v02782_20260611_002315\\runtime\\vdf_akshare_narrow_source_contract_dryrun_result_v02782.json")

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
    try:
        dt = pd.to_datetime(s, errors="coerce")
        if pd.notna(dt):
            return dt.strftime("%Y-%m-%d")
    except Exception:
        pass
    return ""

def sha16(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]

def read_csv(path):
    try:
        return pd.read_csv(path, dtype=str, encoding="utf-8-sig").fillna("")
    except Exception:
        try:
            return pd.read_csv(path, dtype=str).fillna("")
        except Exception:
            return pd.DataFrame()

def score_col(df, col, mode):
    vals = df[col].astype(str).map(clean)
    nonblank = int((vals != "").sum())
    denom = max(1, min(500, nonblank))
    head = vals[vals != ""].head(500)
    nums = sum(1 for x in head if to_num(x) is not None)
    dates = sum(1 for x in head if to_date(x) != "")
    nr = nums / denom
    dr = dates / denom
    br = nonblank / max(1, len(df))
    name = str(col).lower()

    metadata_penalty = 0
    if re.search(r"row|index|hash|policy|path|file|source_file|record|matrix|status|risk|message|report|html|json|csv", name):
        metadata_penalty = 80

    if mode == "symbol":
        score = 0
        if re.search(r"vdf_symbol_hint|symbol|ticker|code|品種|品种|商品|合約|合约|名稱|名称|name|variety|category", name):
            score += 70
        score += 20 * br
        score -= 35 * nr
        score -= 50 * dr
        score -= metadata_penalty
        return score

    if mode == "date":
        score = 0
        if re.search(r"date|time|日期|時間|时间|交易日|seeded|created|updated|報告期|报告期|月份|month|period|year", name):
            score += 70
        score += 80 * dr
        score -= 35 * nr if dr < .2 else 0
        score -= metadata_penalty * .4
        return score

    if mode == "value":
        score = 0
        if re.search(r"value|price|close|open|high|low|指數|指数|價格|价格|收盤|收盘|開盤|开盘|最高|最低|現貨|现货|結算|结算|最新|數值|数值|成交|volume|bdi|cpi|rate|yield|庫存|库存|產量|产量|進口|进口|出口", name):
            score += 70
        score += 90 * nr
        score -= 90 * dr
        score -= metadata_penalty
        return score

    if mode == "source":
        score = 0
        if re.search(r"vdf_source_function|source|function|provider|original|來源|来源|函數|函数|akshare", name):
            score += 80
        score += 10 * br
        return score

    return 0

def best_col(df, mode):
    if df.empty:
        return ""
    cols = list(df.columns)
    ranked = sorted([(score_col(df, c, mode), c) for c in cols], reverse=True)
    return ranked[0][1] if ranked and ranked[0][0] > 0 else ""

def profile_row(file_path, df, col):
    vals = df[col].astype(str).map(clean)
    nonblank = int((vals != "").sum())
    denom = max(1, min(500, nonblank))
    head = vals[vals != ""].head(500)
    nums = sum(1 for x in head if to_num(x) is not None)
    dates = sum(1 for x in head if to_date(x) != "")
    return {
        "file_path": str(file_path),
        "file_name": Path(file_path).name,
        "column_name": str(col),
        "row_count": int(len(df)),
        "non_blank_count": nonblank,
        "non_blank_ratio": round(nonblank / max(1, len(df)), 4),
        "numeric_ratio": round(nums / denom, 4),
        "date_ratio": round(dates / denom, 4),
        "symbol_score": round(score_col(df, col, "symbol"), 4),
        "date_score": round(score_col(df, col, "date"), 4),
        "value_score": round(score_col(df, col, "value"), 4),
        "source_score": round(score_col(df, col, "source"), 4),
        "sample": " | ".join(vals[vals != ""].head(6).tolist())
    }

files = json.loads(file_list_json.read_text(encoding="utf-8"))

profiles = []
selections = []
rows = []

for fp in files:
    df = read_csv(fp)
    if df.empty:
        continue

    for c in df.columns:
        profiles.append(profile_row(fp, df, c))

    symbol_col = best_col(df, "symbol")
    date_col = best_col(df, "date")
    value_col = best_col(df, "value")
    source_col = best_col(df, "source")

    selections.append({
        "file_name": Path(fp).name,
        "file_path": fp,
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "symbol_col": symbol_col,
        "date_col": date_col,
        "value_col": value_col,
        "source_col": source_col
    })

    file_stem = Path(fp).stem
    for idx, r in df.iterrows():
        symbol_raw = clean(r.get(symbol_col, "")) if symbol_col else ""
        if not symbol_raw:
            symbol_raw = clean(r.get("vdf_symbol_hint", "")) or clean(r.get("vdf_selected_category", "")) or file_stem

        source = clean(r.get(source_col, "")) if source_col else ""
        if not source:
            source = clean(r.get("vdf_source_function", "")) or "AkShare"

        date = to_date(r.get(date_col, "")) if date_col else ""
        if not date:
            date = to_date(r.get("vdf_seeded_at", ""))
        if not date:
            # dry-run only fallback, not merge-eligible without review
            date = datetime.now().strftime("%Y-%m-%d")

        val = to_num(r.get(value_col, "")) if value_col else None

        # source-scoped symbol to avoid fake duplicate from generic symbol/category
        series_symbol = f"{source}::{symbol_raw}::{value_col or 'value'}"

        invalid = []
        if not series_symbol:
            invalid.append("symbol_blank")
        if not date:
            invalid.append("date_blank_or_unparseable")
        if val is None:
            invalid.append("value_blank_or_non_numeric")
        if not source:
            invalid.append("source_blank")

        key = f"VDF_Global_Commodity|{series_symbol}|{date}|{source}"
        rows.append({
            "family": "VDF_Global_Commodity",
            "symbol": series_symbol,
            "raw_symbol": symbol_raw,
            "date": date,
            "value": "" if val is None else val,
            "source": source,
            "source_file": fp,
            "source_file_name": Path(fp).name,
            "row_no": int(idx) + 1,
            "symbol_col": symbol_col,
            "date_col": date_col,
            "value_col": value_col,
            "source_col": source_col,
            "canonical_key": key,
            "is_valid": len(invalid) == 0,
            "invalid_reasons": ";".join(invalid),
            "record_hash": sha16(r.to_dict()),
            "dryrun_policy": "NARROW_SOURCE_V0274_ONLY_NO_DB_WRITE"
        })

profile_df = pd.DataFrame(profiles)
selection_df = pd.DataFrame(selections)
preview_df = pd.DataFrame(rows)

for p in [profile_csv, selection_csv, preview_csv, preview_json, invalid_csv, duplicate_csv, rootcause_csv, contract_json, execution_gate_json, out_json]:
    p.parent.mkdir(parents=True, exist_ok=True)

profile_df.to_csv(profile_csv, index=False, encoding="utf-8-sig")
selection_df.to_csv(selection_csv, index=False, encoding="utf-8-sig")
preview_df.to_csv(preview_csv, index=False, encoding="utf-8-sig")
preview_df.to_json(preview_json, orient="records", force_ascii=False, indent=2)

invalid_df = preview_df[preview_df["is_valid"] != True].copy() if not preview_df.empty else preview_df
valid_df = preview_df[preview_df["is_valid"] == True].copy() if not preview_df.empty else preview_df

dup_df = pd.DataFrame()
if not valid_df.empty:
    dup_df = valid_df[valid_df.duplicated(subset=["canonical_key"], keep=False)].copy()

invalid_df.to_csv(invalid_csv, index=False, encoding="utf-8-sig")
dup_df.to_csv(duplicate_csv, index=False, encoding="utf-8-sig")

rootcause = []
for cause in ["symbol_blank","date_blank_or_unparseable","value_blank_or_non_numeric","source_blank"]:
    c = int(invalid_df["invalid_reasons"].astype(str).str.contains(cause, regex=False).sum()) if not invalid_df.empty else 0
    rootcause.append({"cause": cause, "count": c})
rootcause.append({"cause": "duplicate_key_after_narrow_contract", "count": int(len(dup_df))})
pd.DataFrame(rootcause).to_csv(rootcause_csv, index=False, encoding="utf-8-sig")

preview_rows = int(len(preview_df))
valid_rows = int(len(valid_df))
invalid_after = int(len(invalid_df))
duplicate_after = int(len(dup_df))

risk = "LOW" if preview_rows > 0 and invalid_after == 0 and duplicate_after == 0 else ("MEDIUM" if valid_rows > 0 else "HIGH")
status = "VDF_AKSHARE_NARROW_SOURCE_CONTRACT_DRYRUN_READY" if risk == "LOW" else ("VDF_AKSHARE_NARROW_SOURCE_CONTRACT_DRYRUN_READY_WITH_REVIEW" if risk == "MEDIUM" else "VDF_AKSHARE_NARROW_SOURCE_CONTRACT_DRYRUN_BLOCKED")
recommendation = "ALLOW_V02783_DEDUP_GATE_ONLY_NO_DB_WRITE" if valid_rows > 0 else "BLOCK_V02783_UNTIL_NARROW_SOURCE_VALUE_MAPPING_REVIEW"

contract = {
    "generated_at": datetime.now().isoformat(),
    "status": status,
    "risk": risk,
    "source_scope": "v027.4 staging candidate CSV only",
    "db_write_enabled": False,
    "canonical_merge_enabled": False,
    "canonical_family": "VDF_Global_Commodity",
    "required_fields": ["family","symbol","date","value","source"],
    "primary_key": ["family","symbol","date","source"],
    "symbol_rule": "symbol is source-scoped: source::raw_symbol::value_col",
    "date_rule": "use raw date; then vdf_seeded_at; then dry-run fallback date, still no DB write",
    "value_rule": "value must be numeric from selected raw column",
    "metrics": {
        "source_files": len(files),
        "profile_columns": int(len(profile_df)),
        "selection_files": int(len(selection_df)),
        "preview_rows": preview_rows,
        "valid_rows": valid_rows,
        "invalid_after": invalid_after,
        "duplicate_after": duplicate_after
    },
    "next_step": "v027.8.3 dedup gate only; no DB write"
}
contract_json.write_text(json.dumps(contract, ensure_ascii=False, indent=2), encoding="utf-8")

gate = {
    "generated_at": datetime.now().isoformat(),
    "status": "EXECUTION_GATE_REMAINS_CLOSED",
    "risk": "MEDIUM" if risk != "LOW" else "LOW",
    "allowed_to_write_database": False,
    "allowed_to_merge_canonical": False,
    "dryrun_status": status,
    "metrics": contract["metrics"],
    "hard_stop": [
        "No DB write in v027.8.2",
        "No canonical merge in v027.8.2",
        "Run v027.8.3 dedup gate first",
        "Only after invalid_after=0 and duplicate_after=0 may v027.9 execution review run"
    ],
    "recommendation": recommendation
}
execution_gate_json.write_text(json.dumps(gate, ensure_ascii=False, indent=2), encoding="utf-8")

result = {
    "generated_at": datetime.now().isoformat(),
    "status": status,
    "risk": risk,
    "recommendation": recommendation,
    "metrics": contract["metrics"],
    "artifacts": {
        "profile_csv": str(profile_csv),
        "selection_csv": str(selection_csv),
        "preview_csv": str(preview_csv),
        "preview_json": str(preview_json),
        "invalid_csv": str(invalid_csv),
        "duplicate_csv": str(duplicate_csv),
        "rootcause_csv": str(rootcause_csv),
        "contract_json": str(contract_json),
        "execution_gate_json": str(execution_gate_json)
    },
    "next_step": "v027.8.3 dedup gate only; no DB write"
}
out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False))
