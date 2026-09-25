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

file_list_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_NARROW_SOURCE_FILELIST_CANONICALIZER_v027822_20260611_004445\\runtime\\vdf_akshare_v0274_source_file_list_canonical_v027822.json")
profile_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_NARROW_SOURCE_FILELIST_CANONICALIZER_v027822_20260611_004445\\registry\\VDF_AkShare_NarrowSource_RawColumnProfile_Canonicalizer_v027822.csv")
selection_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_NARROW_SOURCE_FILELIST_CANONICALIZER_v027822_20260611_004445\\registry\\VDF_AkShare_NarrowSource_RawColumnSelection_Canonicalizer_v027822.csv")
preview_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_NARROW_SOURCE_FILELIST_CANONICALIZER_v027822_20260611_004445\\preview\\VDF_AkShare_NarrowSource_ContractDryRunPreview_Canonicalizer_v027822.csv")
preview_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_NARROW_SOURCE_FILELIST_CANONICALIZER_v027822_20260611_004445\\preview\\VDF_AkShare_NarrowSource_ContractDryRunPreview_Canonicalizer_v027822.json")
invalid_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_NARROW_SOURCE_FILELIST_CANONICALIZER_v027822_20260611_004445\\preview\\VDF_AkShare_NarrowSource_InvalidRows_Canonicalizer_v027822.csv")
duplicate_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_NARROW_SOURCE_FILELIST_CANONICALIZER_v027822_20260611_004445\\preview\\VDF_AkShare_NarrowSource_DuplicateRows_Canonicalizer_v027822.csv")
rootcause_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_NARROW_SOURCE_FILELIST_CANONICALIZER_v027822_20260611_004445\\registry\\VDF_AkShare_NarrowSource_RootCause_Canonicalizer_v027822.csv")
out_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_NARROW_SOURCE_FILELIST_CANONICALIZER_v027822_20260611_004445\\runtime\\vdf_akshare_narrow_source_filelist_canonicalizer_result_v027822.json")

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
        score = 20 * br - 35 * nr - 50 * dr - metadata_penalty
        if re.search(r"vdf_symbol_hint|symbol|ticker|code|品種|品种|商品|合約|合约|名稱|名称|name|variety|category|description", name):
            score += 70
        return score
    if mode == "date":
        score = 80 * dr - (35 * nr if dr < .2 else 0) - metadata_penalty * .4
        if re.search(r"date|time|日期|時間|时间|交易日|seeded|created|updated|報告期|报告期|月份|month|period|year", name):
            score += 70
        return score
    if mode == "value":
        score = 90 * nr - 90 * dr - metadata_penalty
        if re.search(r"value|price|close|open|high|low|指數|指数|價格|价格|收盤|收盘|開盤|开盘|最高|最低|現貨|现货|結算|结算|最新|數值|数值|成交|volume|bdi|cpi|rate|yield|庫存|库存|產量|产量|進口|进口|出口", name):
            score += 70
        return score
    if mode == "source":
        score = 10 * br
        if re.search(r"vdf_source_function|source|function|provider|original|來源|来源|函數|函数|akshare", name):
            score += 80
        return score
    return 0

def best_col(df, mode):
    ranked = sorted([(score_col(df, c, mode), c) for c in df.columns], reverse=True)
    return ranked[0][1] if ranked and ranked[0][0] > 0 else ""

def sha16(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]

raw = json.loads(file_list_json.read_text(encoding="utf-8"))
if isinstance(raw, dict):
    raw = [raw]
elif isinstance(raw, str):
    raw = [{"path": raw, "name": Path(raw).name, "size": 0}]
elif not isinstance(raw, list):
    raw = []

files = []
for x in raw:
    if isinstance(x, str):
        x = {"path": x, "name": Path(x).name, "size": 0}
    if isinstance(x, dict) and x.get("path") and Path(x["path"]).exists():
        files.append(x)

profiles = []
selections = []
rows = []

for item in files:
    fp = item["path"]
    try:
        df = pd.read_csv(fp, dtype=str, encoding="utf-8-sig").fillna("")
    except Exception:
        df = pd.read_csv(fp, dtype=str).fillna("")

    if df.empty:
        continue

    for c in df.columns:
        vals = df[c].astype(str).map(clean)
        nonblank = int((vals != "").sum())
        denom = max(1, min(500, nonblank))
        head = vals[vals != ""].head(500)
        nums = sum(1 for x in head if to_num(x) is not None)
        dates = sum(1 for x in head if to_date(x) != "")
        profiles.append({
            "file_name": Path(fp).name,
            "file_path": fp,
            "column_name": c,
            "row_count": len(df),
            "non_blank_count": nonblank,
            "numeric_ratio": round(nums / denom, 4),
            "date_ratio": round(dates / denom, 4),
            "symbol_score": round(score_col(df, c, "symbol"), 4),
            "date_score": round(score_col(df, c, "date"), 4),
            "value_score": round(score_col(df, c, "value"), 4),
            "source_score": round(score_col(df, c, "source"), 4),
            "sample": " | ".join(vals[vals != ""].head(5).tolist())
        })

    symbol_col = best_col(df, "symbol")
    date_col = best_col(df, "date")
    value_col = best_col(df, "value")
    source_col = best_col(df, "source")

    selections.append({
        "file_name": Path(fp).name,
        "file_path": fp,
        "row_count": len(df),
        "column_count": len(df.columns),
        "symbol_col": symbol_col,
        "date_col": date_col,
        "value_col": value_col,
        "source_col": source_col
    })

    for idx, r in df.iterrows():
        source = clean(r.get(source_col, "")) if source_col else ""
        if not source:
            source = clean(r.get("vdf_source_function", "")) or "AkShare"

        raw_symbol = clean(r.get(symbol_col, "")) if symbol_col else ""
        if not raw_symbol:
            raw_symbol = clean(r.get("vdf_symbol_hint", "")) or clean(r.get("vdf_selected_category", "")) or Path(fp).stem

        date = to_date(r.get(date_col, "")) if date_col else ""
        if not date:
            date = to_date(r.get("vdf_seeded_at", ""))
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        value = to_num(r.get(value_col, "")) if value_col else None

        symbol = f"{source}::{raw_symbol}::{value_col or 'value'}"
        invalid = []
        if not symbol:
            invalid.append("symbol_blank")
        if not date:
            invalid.append("date_blank_or_unparseable")
        if value is None:
            invalid.append("value_blank_or_non_numeric")
        if not source:
            invalid.append("source_blank")

        key = f"VDF_Global_Commodity|{symbol}|{date}|{source}"
        rows.append({
            "family": "VDF_Global_Commodity",
            "symbol": symbol,
            "raw_symbol": raw_symbol,
            "date": date,
            "value": "" if value is None else value,
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
            "dryrun_policy": "FILELIST_CANONICALIZER_NO_DB_WRITE"
        })

profile_df = pd.DataFrame(profiles)
selection_df = pd.DataFrame(selections)
preview_df = pd.DataFrame(rows)

for p in [profile_csv, selection_csv, preview_csv, preview_json, invalid_csv, duplicate_csv, rootcause_csv, out_json]:
    p.parent.mkdir(parents=True, exist_ok=True)

profile_df.to_csv(profile_csv, index=False, encoding="utf-8-sig")
selection_df.to_csv(selection_csv, index=False, encoding="utf-8-sig")
preview_df.to_csv(preview_csv, index=False, encoding="utf-8-sig")
preview_df.to_json(preview_json, orient="records", force_ascii=False, indent=2)

invalid_df = preview_df[preview_df["is_valid"] != True].copy() if not preview_df.empty else preview_df
valid_df = preview_df[preview_df["is_valid"] == True].copy() if not preview_df.empty else preview_df
dup_df = valid_df[valid_df.duplicated(subset=["canonical_key"], keep=False)].copy() if not valid_df.empty else pd.DataFrame()

invalid_df.to_csv(invalid_csv, index=False, encoding="utf-8-sig")
dup_df.to_csv(duplicate_csv, index=False, encoding="utf-8-sig")

rootcause = []
for cause in ["symbol_blank","date_blank_or_unparseable","value_blank_or_non_numeric","source_blank"]:
    c = int(invalid_df["invalid_reasons"].astype(str).str.contains(cause, regex=False).sum()) if not invalid_df.empty else 0
    rootcause.append({"cause": cause, "count": c})
rootcause.append({"cause": "duplicate_key_after_filelist_canonicalizer", "count": int(len(dup_df))})
pd.DataFrame(rootcause).to_csv(rootcause_csv, index=False, encoding="utf-8-sig")

metrics = {
    "source_files": len(files),
    "profile_columns": len(profile_df),
    "selection_files": len(selection_df),
    "preview_rows": len(preview_df),
    "valid_rows": len(valid_df),
    "invalid_after": len(invalid_df),
    "duplicate_after": len(dup_df)
}

risk = "LOW" if metrics["preview_rows"] > 0 and metrics["invalid_after"] == 0 and metrics["duplicate_after"] == 0 else ("MEDIUM" if metrics["valid_rows"] > 0 else "HIGH")
status = "VDF_AKSHARE_NARROW_SOURCE_FILELIST_CANONICALIZER_READY" if risk == "LOW" else ("VDF_AKSHARE_NARROW_SOURCE_FILELIST_CANONICALIZER_READY_WITH_REVIEW" if risk == "MEDIUM" else "VDF_AKSHARE_NARROW_SOURCE_FILELIST_CANONICALIZER_BLOCKED")
recommendation = "ALLOW_V02783_DEDUP_GATE_ONLY_NO_DB_WRITE" if metrics["valid_rows"] > 0 else "BLOCK_V02783_UNTIL_SOURCE_CSV_CONTENT_REVIEW"

result = {
    "generated_at": datetime.now().isoformat(),
    "status": status,
    "risk": risk,
    "recommendation": recommendation,
    "metrics": metrics,
    "artifacts": {
        "profile_csv": str(profile_csv),
        "selection_csv": str(selection_csv),
        "preview_csv": str(preview_csv),
        "preview_json": str(preview_json),
        "invalid_csv": str(invalid_csv),
        "duplicate_csv": str(duplicate_csv),
        "rootcause_csv": str(rootcause_csv)
    },
    "next_step": "v027.8.3 dedup gate only; no DB write" if metrics["valid_rows"] > 0 else "source CSV content review"
}
out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False))
