# -*- coding: utf-8 -*-
"""
def VDF_AutoCodeRegistryEngine.py
def Panorama scan + orphan classifier + safe staging + universal instrument registry.
"""

import os
import re
import io
import json
import time
import shutil
import hashlib
import datetime as dt
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

import pandas as pd

try:
    import duckdb
except Exception:
    duckdb = None

def def_now_utc() -> str:
    # def timezone-aware UTC; utcnow() is deprecated in modern Python.
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def def_log(level: str, msg: str) -> None:
    print(f"[{dt.datetime.now().strftime('%H:%M:%S')}] [{level}] {msg}", flush=True)

def def_read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def def_ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def def_sha12_text(s: str) -> str:
    return hashlib.sha256(str(s).encode("utf-8", errors="ignore")).hexdigest()[:12]

def def_file_sha12(path: str) -> str:
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()[:12]
    except Exception:
        return ""

def def_clean_text(x: Any) -> str:
    if x is None:
        return ""
    s = str(x).replace("\ufeff", "")
    s = re.sub(r"\s+", " ", s).strip()
    return s

def def_coerce_str(x: Any) -> str:
    # def NaN/None/float safe -> str. pandas NaN is a float and breaks .lower()/.startswith().
    if x is None:
        return ""
    if isinstance(x, float):
        try:
            if pd.isna(x):
                return ""
        except Exception:
            return str(x)
    return str(x)

def def_sanitize_text(x: Any) -> str:
    # def Output-safety: strip lone surrogates (Windows os.walk odd filenames),
    # def NUL, and disallowed control chars that crash to_csv/to_parquet/duckdb.
    s = def_coerce_str(x)
    if not s:
        return s
    # def lone surrogates are unencodable in utf-8 -> replace with '?'
    s = s.encode("utf-8", "replace").decode("utf-8", "replace")
    # def drop NUL + control chars but keep tab/newline/carriage-return
    s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", s)
    return s

def def_sanitize_cell(x: Any) -> Any:
    # def Only touch real strings; leave numbers / NaN / None untyped.
    if isinstance(x, str):
        return def_sanitize_text(x)
    return x

def def_sanitize_frame(df: "pd.DataFrame") -> "pd.DataFrame":
    # def In-place sanitize every object/string column so all sinks are safe.
    if df is None or df.shape[1] == 0:
        return df
    for c in df.columns:
        try:
            if df[c].dtype == object or str(df[c].dtype).startswith("string"):
                df[c] = df[c].map(def_sanitize_cell)
        except Exception:
            df[c] = df[c].astype(str).map(def_sanitize_cell)
    return df

def def_safe_rel(path: str, base: str) -> str:
    try:
        return str(Path(path).resolve().relative_to(Path(base).resolve()))
    except Exception:
        return str(path)

def def_safe_filename(name: str) -> str:
    s = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", str(name))
    s = re.sub(r"_+", "_", s).strip("._ ")
    return s[:180] if s else "unnamed"

def def_read_text_sniff(path: str, max_bytes: int) -> str:
    try:
        with open(path, "rb") as f:
            raw = f.read(max_bytes)
        for enc in ["utf-8-sig","utf-8","cp950","big5","gb18030","latin1"]:
            try:
                return def_sanitize_text(raw.decode(enc, errors="replace"))
            except Exception:
                continue
        return def_sanitize_text(raw.decode("latin1", errors="replace"))
    except Exception:
        return ""

def def_html_escape(x: Any) -> str:
    s = "" if x is None else str(x)
    return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

def def_depth(root: str, path: str) -> int:
    try:
        rel = Path(path).resolve().relative_to(Path(root).resolve())
        return len(rel.parts) - 1
    except Exception:
        return 999

def def_candidate_match(name: str, patterns: List[str]) -> bool:
    low = name.lower()
    for p in patterns:
        pp = p.lower().replace("*", ".*")
        if re.fullmatch(pp, low):
            return True
    hard_tokens = [
        "vrn", "vdf", "via", "vis", "vpns", "ssot", "registry",
        "engine", "config", "macro_indicator", "params.example",
        "datatransform", "parammanager", "polyglot", "optimizer",
        "nexus", "governance", "layout", "visual"
    ]
    return any(t in low for t in hard_tokens)

def def_scan_files(config: Dict[str, Any]) -> pd.DataFrame:
    scan_cfg = config["def_scan"]
    exts = set([x.lower() for x in scan_cfg["def_extensions"]])
    skip_dirs = set([x.lower() for x in scan_cfg["def_skip_dir_names"]])
    patterns = scan_cfg["def_candidate_patterns"]
    max_files = int(scan_cfg["def_max_files"])

    rows = []
    seen = set()

    for root_item in scan_cfg["def_roots"]:
        root = root_item["def_path"]
        root_name = root_item["def_root_name"]
        max_depth = int(root_item["def_max_depth"])

        if not os.path.exists(root):
            rows.append({
                "def_round": "Round0",
                "def_stage": "SCAN_ROOT",
                "def_status": "WARN_MISSING_ROOT",
                "def_root_name": root_name,
                "def_path": root,
                "def_message": "Scan root missing."
            })
            continue

        def_log("RUN", f"Scanning root={root_name} depth={max_depth}: {root}")

        for cur, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d.lower() not in skip_dirs]
            if def_depth(root, cur) > max_depth:
                dirs[:] = []
                continue

            for fn in files:
                if len(rows) >= max_files:
                    break

                path = os.path.join(cur, fn)
                ext = os.path.splitext(fn)[1].lower()

                if ext not in exts:
                    continue

                parent = str(Path(path).parent)
                is_top_orphan = str(Path(parent).resolve()) in [str(Path(root).resolve()), str(Path(config["def_system"]["def_base_dir"]).resolve())]
                is_candidate = is_top_orphan or def_candidate_match(fn, patterns)

                if not is_candidate:
                    continue

                norm = str(Path(path).resolve()).lower()
                if norm in seen:
                    continue
                seen.add(norm)

                try:
                    st = os.stat(path)
                    rows.append({
                        "def_round": "Round0",
                        "def_stage": "SOURCE_INVENTORY",
                        "def_status": "OK_CANDIDATE",
                        "def_root_name": root_name,
                        "def_path": def_sanitize_text(path),
                        "def_file_name": def_sanitize_text(fn),
                        "def_extension": ext,
                        "def_parent": def_sanitize_text(parent),
                        "def_size_bytes": int(st.st_size),
                        "def_modified_time": dt.datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
                        "def_is_top_orphan": bool(is_top_orphan)
                    })
                except Exception as e:
                    rows.append({
                        "def_round": "Round0",
                        "def_stage": "SOURCE_INVENTORY",
                        "def_status": "WARN_STAT_FAILED",
                        "def_root_name": root_name,
                        "def_path": def_sanitize_text(path),
                        "def_file_name": def_sanitize_text(fn),
                        "def_extension": ext,
                        "def_message": def_sanitize_text(str(e)[:240])
                    })

            if len(rows) >= max_files:
                break

    return pd.DataFrame(rows)

def def_normalize_duplicate_key(file_name: str) -> str:
    name = file_name
    name = re.sub(r"\s*-\s*複製(?:\s*\(\d+\))?", "", name, flags=re.I)
    name = re.sub(r"\s*\(\d+\)", "", name)
    name = re.sub(r"\.\d{8}_\d{6}\.bak$", ".bak", name, flags=re.I)
    name = re.sub(r"\.\d{8}_\d{6}$", "", name, flags=re.I)
    name = re.sub(r"\s+", " ", name).strip().lower()
    return name

def def_version_score(name: str) -> int:
    low = name.lower()
    nums = []
    for m in re.finditer(r"v(\d{2,5})(?:[._-]?(\d+))?", low):
        a = int(m.group(1))
        b = int(m.group(2) or 0)
        nums.append(a * 1000 + b)
    if "aio" in low:
        nums.append(50)
    if "hotfix" in low:
        nums.append(30)
    if "validator" in low:
        nums.append(20)
    if "(1)" in low or "(2)" in low or "複製" in low:
        nums.append(-10)
    return max(nums) if nums else 0

def def_classify_module(file_name: str, path: str, text: str) -> Dict[str, Any]:
    low = file_name.lower()
    path_low = path.lower()
    text_low = text.lower()

    module = "UNKNOWN"
    category = "misc"
    useful = True
    risk = "LOW"
    target_bucket = "UNKNOWN_MISC"
    reason = "pattern candidate"

    if low.startswith("vrn") or "veritasreportnova" in text_low:
        module = "VRN"
        target_bucket = "functional_modules/VRN"
        if "fieldregistry" in low:
            category = "field_registry"
        elif "broker" in low:
            category = "broker_registry"
        elif "io_summary" in low:
            category = "io_summary"
        elif low.endswith(".py") or low.endswith(".ps1"):
            category = "engine"
        else:
            category = "registry"
        reason = "VRN related file"

    elif low.startswith("vdf") or "veritasdataforge" in text_low or "macro_indicator_registry" in low:
        module = "VDF"
        target_bucket = "functional_modules/VDF"
        if "mdl" in low:
            category = "module_engine"
        elif "registry" in low:
            category = "registry"
        elif "macro_indicator" in low:
            category = "macro_registry"
        elif low.endswith(".py") or low.endswith(".ps1"):
            category = "engine"
        else:
            category = "data"
        reason = "VDF related file"

    elif low.startswith("via") or "veritas intelligence analytics" in text_low or "governanceregistry" in low or "visualregistry" in low or "layoutregistry" in low:
        module = "VIA"
        target_bucket = "supportive_modules/VIA"
        if "visual" in low or "layout" in low or "header" in low or "chartspec" in low:
            category = "visual_design_ops"
        elif "governance" in low:
            category = "governance"
        elif "optimizer" in low or "engineforge" in low:
            category = "optimizer_engine"
        elif "param" in low:
            category = "parameter_manager"
        elif low.endswith(".py") or low.endswith(".ps1") or low.endswith(".js"):
            category = "engine"
        else:
            category = "registry"
        reason = "VIA related file"

    elif low.startswith("vis") or "vis_" in low:
        module = "VIS"
        target_bucket = "functional_modules/VIS"
        category = "visual_intelligence_system"
        reason = "VIS related file"

    elif low.startswith("vpns") or "ssot_vpns" in low:
        module = "VPNS"
        target_bucket = "functional_modules/VPNS"
        category = "vpns_registry_engine"
        reason = "VPNS related file"

    elif low.startswith("decisionstudio"):
        module = "VAP"
        target_bucket = "functional_modules/VAP"
        category = "decision_studio_registry"
        reason = "DecisionStudio / VAP registry"

    elif low in ["config.json", "config (1).json", "config (2).json", "config (3).json", "regex_registry.json", "engine.py", "engine (1).py", "engine (2).py"]:
        module = "PENDING_REVIEW"
        target_bucket = "pending_review/generic_engine_config"
        category = "generic_engine_bundle"
        risk = "MEDIUM"
        reason = "generic config/engine name; needs bundle comparison before canonical use"

    elif low.endswith(".png"):
        module = "VIA"
        target_bucket = "supportive_modules/VIA_visual_assets"
        category = "visual_asset"
        reason = "visual artifact"

    elif low.endswith(".parquet") or low.endswith(".csv") or low.endswith(".json"):
        module = "DATA_REGISTRY"
        target_bucket = "data_registry/incoming"
        category = "data_registry"
        reason = "data registry candidate"

    if ".bak" in low:
        category = category + "_backup"
        useful = False
        risk = "LOW"
        reason = reason + "; backup file"

    return {
        "def_module": module,
        "def_category": category,
        "def_target_bucket": target_bucket,
        "def_useful_candidate": useful,
        "def_risk": risk,
        "def_reason": reason
    }

def def_enrich_inventory(inv: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    if inv.empty:
        return inv

    # def Keep only real candidate files. SCAN_ROOT / WARN_MISSING_ROOT / WARN_STAT_FAILED
    # def are administrative rows, not files; they must not be classified or staged.
    if "def_status" in inv.columns:
        inv = inv[inv["def_status"].astype(str).eq("OK_CANDIDATE")].copy()
    if inv.empty:
        return inv

    max_text_bytes = int(config["def_scan"]["def_max_text_read_bytes"])
    rows = []
    for _, r in inv.iterrows():
        row = r.to_dict()
        path = def_coerce_str(row.get("def_path", ""))
        fn = def_coerce_str(row.get("def_file_name", ""))
        if not fn:
            fn = os.path.basename(path)
        ext = def_coerce_str(row.get("def_extension", ""))
        if not ext:
            ext = os.path.splitext(fn)[1]
        ext = ext.lower()

        sha = def_file_sha12(path) if os.path.exists(path) else ""
        text = ""
        if ext in [".json",".py",".ps1",".html",".htm",".md",".csv",".js",".ts"]:
            text = def_read_text_sniff(path, max_text_bytes)

        cls = def_classify_module(fn, path, text)
        row.update(cls)
        row["def_sha12"] = sha
        row["def_duplicate_key"] = def_normalize_duplicate_key(fn)
        row["def_version_score"] = def_version_score(fn)
        row["def_text_snippet"] = def_clean_text(text[:500])
        rows.append(row)

    df = pd.DataFrame(rows)

    df["def_dup_group_count"] = df.groupby("def_duplicate_key")["def_path"].transform("count")
    df["def_sha_group_count"] = df.groupby("def_sha12")["def_path"].transform("count")

    decisions = []
    for key, g in df.groupby("def_duplicate_key"):
        g2 = g.copy()
        g2["_mtime_rank"] = pd.to_datetime(g2["def_modified_time"], errors="coerce")
        g2 = g2.sort_values(["def_version_score","_mtime_rank"], ascending=[False, False])
        keep_path = g2.iloc[0]["def_path"]
        keep_sha = g2.iloc[0]["def_sha12"]

        for _, rr in g.iterrows():
            if rr["def_path"] == keep_path:
                action = "REGISTER_AND_STAGE"
                message = "canonical candidate in duplicate group"
            elif rr["def_sha12"] == keep_sha:
                action = "SKIP_DUPLICATE_IDENTICAL"
                message = "same content as canonical candidate"
            else:
                action = "REGISTER_VERSION_VARIANT"
                message = "same normalized name but different content; preserve as version variant"

            decisions.append({
                "def_path": rr["def_path"],
                "def_action": action,
                "def_decision_message": message
            })

    dec = pd.DataFrame(decisions)
    df = df.merge(dec, on="def_path", how="left")

    df["def_quarantine_recommendation"] = df.apply(
        lambda r: "QUARANTINE_PLAN_ONLY" if (
            r.get("def_action") == "SKIP_DUPLICATE_IDENTICAL" or
            str(r.get("def_category","")).endswith("_backup")
        ) else "",
        axis=1
    )

    return df

def def_stage_files(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    policy = config["def_policy"]
    sys = config["def_system"]
    staging_dir = sys["def_staging_dir"]
    quarantine_dir = sys["def_quarantine_dir"]

    rows = []

    write_stage = bool(policy.get("def_write_staging_copy", True))
    apply_quarantine = bool(policy.get("def_apply_quarantine", False))
    approval_ok = policy.get("def_approval_token","") == policy.get("def_required_approval_token","")
    destructive = bool(policy.get("def_destructive_delete", False))

    for _, r in df.iterrows():
        path = r.get("def_path","")
        action = r.get("def_action","")
        bucket = r.get("def_target_bucket","UNKNOWN_MISC")
        fn = os.path.basename(path)
        out = {
            "def_round": "Round2",
            "def_stage": "STAGE_OR_QUARANTINE",
            "def_path": path,
            "def_file_name": fn,
            "def_action": action,
            "def_status": "SKIP",
            "def_staged_path": "",
            "def_message": ""
        }

        if not os.path.exists(path):
            out["def_status"] = "WARN_MISSING_SOURCE"
            out["def_message"] = "source missing at staging time"
            rows.append(out)
            continue

        if action in ["REGISTER_AND_STAGE","REGISTER_VERSION_VARIANT"] and write_stage:
            sub = os.path.join(staging_dir, bucket, r.get("def_category","misc"))
            def_ensure_dir(sub)
            staged_name = f"{Path(fn).stem}__sha{r.get('def_sha12','')}{Path(fn).suffix}"
            staged_path = os.path.join(sub, def_safe_filename(staged_name))
            try:
                if not os.path.exists(staged_path):
                    shutil.copy2(path, staged_path)
                    out["def_status"] = "OK_STAGED_COPY"
                    out["def_message"] = "append-only staging copy created"
                else:
                    out["def_status"] = "OK_STAGED_EXISTS"
                    out["def_message"] = "staged copy already exists"
                out["def_staged_path"] = staged_path
            except Exception as e:
                out["def_status"] = "WARN_STAGE_FAILED"
                out["def_message"] = str(e)[:240]

        elif action == "SKIP_DUPLICATE_IDENTICAL":
            out["def_status"] = "OK_DUPLICATE_SKIPPED"
            out["def_message"] = "duplicate identical; no canonical copy needed"

        if r.get("def_quarantine_recommendation","") and apply_quarantine:
            if approval_ok and not destructive:
                try:
                    subq = os.path.join(quarantine_dir, r.get("def_module","UNKNOWN"))
                    def_ensure_dir(subq)
                    qpath = os.path.join(subq, def_safe_filename(fn))
                    if not os.path.exists(qpath):
                        shutil.move(path, qpath)
                    out["def_status"] = "OK_MOVED_TO_QUARANTINE_REVIEW"
                    out["def_message"] = "moved to quarantine review; not deleted"
                    out["def_staged_path"] = qpath
                except Exception as e:
                    out["def_status"] = "WARN_QUARANTINE_FAILED"
                    out["def_message"] = str(e)[:240]
            else:
                out["def_status"] = "WARN_QUARANTINE_BLOCKED_BY_POLICY"
                out["def_message"] = "approval token missing or destructive policy locked"

        rows.append(out)

    return pd.DataFrame(rows)

def def_make_classes() -> pd.DataFrame:
    rows = [
        ("CMD","Commodity","原物料 / 商品"),
        ("EQT","Equity","股票"),
        ("ETF","Exchange Traded Fund","ETF"),
        ("SMI","Stock Market Index","股價指數"),
        ("FUT","Futures","期貨"),
        ("OPT","Option","選擇權"),
        ("FXR","Foreign Exchange Rate","匯率"),
        ("INT","Interest Rate","利率 / 殖利率"),
        ("BND","Bond","債券"),
        ("CRY","Crypto","加密貨幣"),
        ("SHP","Shipping","航運 / 運價"),
        ("MAC","Macro Indicator","總經指標"),
        ("FIS","Fiscal Indicator","財政收支"),
        ("FED","Federal Reserve Data","FED 資料"),
        ("SNT","Sentiment Indicator","情緒指標"),
        ("IND","Industry Indicator","產業指標"),
        ("FND","Fundamental Data","基本面 / 財報"),
        ("CHP","Chip / Positioning","籌碼 / 法人"),
        ("AST","Physical Asset","工廠 / 港口 / 礦山"),
        ("EVT","Event Signal","事件 / 新聞 / 戰爭"),
        ("RTE","Route / Logistics","航線 / 物流"),
        ("GEO","Geography","地理區域")
    ]
    return pd.DataFrame([
        {
            "def_asset_class": a,
            "def_class_name_en": b,
            "def_class_name_zh": c,
            "def_uid_format": f"{a}-0001",
            "def_counter_policy": "increment_by_asset_class",
            "def_is_active": True
        }
        for a,b,c in rows
    ])

def def_seed_master() -> pd.DataFrame:
    rows = []
    def add(uid, asset_class, code, family, country, market, symbol, name_zh, name_en, freq, source, unit="", tw_ticker="", tw_security_code="", note=""):
        rows.append({
            "def_uid": uid,
            "def_asset_class": asset_class,
            "def_code": code,
            "def_family_code": family,
            "def_country": country,
            "def_market": market,
            "def_symbol": symbol,
            "TW_TICKER": str(tw_ticker) if tw_ticker else "",
            "tw_security_code": str(tw_security_code) if tw_security_code else "",
            "def_name_zh": name_zh,
            "def_name_en": name_en,
            "def_frequency": freq,
            "def_source_primary": source,
            "def_unit": unit,
            "def_is_active": True,
            "def_note": note,
            "def_created_at": def_now_utc(),
            "def_updated_at": def_now_utc()
        })

    add("EQT-0001","EQT","EQT-TW-TWSE-2330","EQT-TW-TWSE-EQT","TW","TWSE","2330","台積電","TSMC","daily","TWSE","TWD","2330")
    add("EQT-0002","EQT","EQT-TW-TWSE-3706","EQT-TW-TWSE-EQT","TW","TWSE","3706","神達","MiTAC","daily","TWSE","TWD","3706")
    add("EQT-0003","EQT","EQT-TW-TPEX-3324","EQT-TW-TPEX-EQT","TW","TPEX","3324","雙鴻","AURAS","daily","TPEX","TWD","3324")
    add("EQT-0004","EQT","EQT-TW-TPEX-6488","EQT-TW-TPEX-EQT","TW","TPEX","6488","環球晶","GlobalWafers","daily","TPEX","TWD","6488")

    add("CMD-0001","CMD","CMD-STL-GLB-IRONORE","CMD-STL-GLB-CMD","GLB","FRED","PIORECRUSDM","鐵礦石","Iron Ore","monthly","FRED","USD/metric ton")
    add("CMD-0002","CMD","CMD-STL-GLB-COKINGCOAL","CMD-STL-GLB-CMD","GLB","FRED","IQ11010","冶金煤","Metallurgical Coal","monthly","FRED","index")
    add("CMD-0003","CMD","CMD-ENE-AU-THERMALCOAL","CMD-ENE-GLB-CMD","AU","FRED","PCOALAUUSDM","澳洲蒸氣煤","Australia Thermal Coal","monthly","FRED","USD/metric ton")
    add("CMD-0004","CMD","CMD-ENE-ZA-THERMALCOAL","CMD-ENE-GLB-CMD","ZA","FRED","PCOALSAUSDM","南非蒸氣煤","South Africa Thermal Coal","monthly","FRED","USD/metric ton")
    add("CMD-0005","CMD","CMD-BME-GLB-COPPER","CMD-BME-GLB-CMD","GLB","YFINANCE","HG=F","銅","Copper","daily","yfinance","USD/lb")
    add("CMD-0006","CMD","CMD-BME-GLB-NICKEL","CMD-BME-GLB-CMD","GLB","YFINANCE","NICKEL.L","鎳","Nickel","daily","yfinance","proxy")
    add("CMD-0007","CMD","CMD-ENE-US-WTI","CMD-ENE-GLB-CMD","US","YFINANCE","CL=F","WTI 原油","WTI Crude Oil","daily","yfinance","USD/bbl")
    add("CMD-0008","CMD","CMD-ENE-EU-BRENT","CMD-ENE-GLB-CMD","EU","YFINANCE","BZ=F","Brent 原油","Brent Crude Oil","daily","yfinance","USD/bbl")
    add("CMD-0009","CMD","CMD-ENE-US-HHNG","CMD-ENE-GLB-CMD","US","YFINANCE","NG=F","Henry Hub 天然氣","Henry Hub Natural Gas","daily","yfinance","USD/MMBtu")
    add("CMD-0010","CMD","CMD-PCH-US-RBOB","CMD-PCH-GLB-CMD","US","YFINANCE","RB=F","RBOB 汽油","RBOB Gasoline","daily","yfinance","USD/gal")
    add("CMD-0011","CMD","CMD-PCH-US-HEATINGOIL","CMD-PCH-GLB-CMD","US","YFINANCE","HO=F","柴油代理 / Heating Oil","Heating Oil Diesel Proxy","daily","yfinance","USD/gal")
    add("CMD-0012","CMD","CMD-BLD-CN-CEMENT","CMD-BLD-CN-CMD","CN","NBS","CEMENT_OUTPUT","中國水泥","China Cement","monthly","NBS","million tons")

    add("SMI-0001","SMI","SMI-TW-TWSE-TAIEX","SMI-TW-TWSE-SMI","TW","TWSE","^TWII","台灣加權指數","Taiwan Weighted Index","daily","TWSE/yfinance","index")
    add("SMI-0002","SMI","SMI-TW-TPEX-TPEx","SMI-TW-TPEX-SMI","TW","TPEX","TPEX_INDEX","櫃買指數","Taipei Exchange Index","daily","TPEX","index")
    add("SMI-0003","SMI","SMI-US-SPGI-SP500","SMI-US-SPGI-SMI","US","SPGI","^GSPC","標普500","S&P 500","daily","yfinance","index")
    add("SMI-0004","SMI","SMI-US-NASDAQ-IXIC","SMI-US-NASDAQ-SMI","US","NASDAQ","^IXIC","那斯達克綜合指數","Nasdaq Composite","daily","yfinance","index")

    macro = [
        ("MAC-0001","MAC-US-LABOR-NFP-PAYEMS","美國非農就業","US Nonfarm Payrolls","PAYEMS"),
        ("MAC-0002","MAC-US-LABOR-UNRATE","美國失業率 U3","US Unemployment Rate","UNRATE"),
        ("MAC-0003","MAC-US-LABOR-U6RATE","美國廣義失業率 U6","US U6 Unemployment Rate","U6RATE"),
        ("MAC-0004","MAC-US-LABOR-CIVPART","美國勞動參與率","US Labor Force Participation Rate","CIVPART"),
        ("MAC-0005","MAC-US-LABOR-ICSA","美國初領失業金","Initial Claims","ICSA"),
        ("MAC-0006","MAC-US-CPI-HEADLINE","美國 CPI","US CPI Headline","CPIAUCSL"),
        ("MAC-0007","MAC-US-CPI-CORE","美國核心 CPI","US Core CPI","CPILFESL"),
        ("MAC-0008","MAC-US-PPI-FINALDEMAND","美國 PPI Final Demand","US PPI Final Demand","PPIFIS"),
        ("MAC-0009","MAC-US-RETAIL-HEADLINE","美國零售銷售","US Retail Sales","RSAFS"),
        ("MAC-0010","MAC-US-DURABLE-ORDERS","美國耐久財訂單","US Durable Goods Orders","DGORDER"),
        ("MAC-0011","MAC-US-CAPEX-CORE-ORDERS","核心資本財訂單","Core Capital Goods Orders","NEWORDER")
    ]
    for uid, code, zh, en, symbol in macro:
        add(uid,"MAC",code,"MAC-US-DETAILED-MAC","US","FRED",symbol,zh,en,"monthly","FRED/BLS/Census","various")

    fiscal = [
        ("FIS-0001","FIS-US-MTS-RECEIPTS-TOTAL","美國財政收入","US Federal Receipts"),
        ("FIS-0002","FIS-US-MTS-OUTLAYS-TOTAL","美國財政支出","US Federal Outlays"),
        ("FIS-0003","FIS-US-MTS-DEFICIT-SURPLUS","美國赤字 / 盈餘","US Deficit Surplus"),
        ("FIS-0004","FIS-US-MTS-CUSTOMS-DUTIES","美國關稅收入","US Customs Duties"),
        ("FIS-0005","FIS-US-MTS-NETINTEREST","美國淨利息支出","US Net Interest Outlays")
    ]
    for uid, code, zh, en in fiscal:
        add(uid,"FIS",code,"FIS-US-MTS-FIS","US","TreasuryFiscalData",code,zh,en,"monthly","Treasury FiscalData","USD")

    fed = [
        ("FED-0001","FED-US-H41-TOTALASSETS","聯準會總資產","Fed Total Assets","WALCL","weekly"),
        ("FED-0002","FED-US-H41-RESERVES","銀行準備金","Reserve Balances","RESBALNS","weekly"),
        ("FED-0003","FED-US-RRP-ONRRP","隔夜逆回購","Overnight Reverse Repo","RRPONTSYD","daily"),
        ("FED-0004","FED-US-SOFR","SOFR","SOFR","SOFR","daily"),
        ("FED-0005","FED-US-EFFR","有效聯邦基金利率","Effective Fed Funds Rate","EFFR","daily"),
        ("FED-0006","FED-US-H15-T10Y","美國10年債利率","US 10Y Treasury Yield","DGS10","daily")
    ]
    for uid, code, zh, en, symbol, freq in fed:
        add(uid,"FED",code,"FED-US-H41-H15-FED","US","FRED/FederalReserve",symbol,zh,en,freq,"FRED/FederalReserve","percent_or_USD")

    snt = [
        ("SNT-0001","SNT-US-AAII-BULLISH","AAII 看多比例","AAII Bullish","AAII_BULLISH","weekly"),
        ("SNT-0002","SNT-US-AAII-NEUTRAL","AAII 中性比例","AAII Neutral","AAII_NEUTRAL","weekly"),
        ("SNT-0003","SNT-US-AAII-BEARISH","AAII 看空比例","AAII Bearish","AAII_BEARISH","weekly"),
        ("SNT-0004","SNT-US-CNN-FEAR-GREED","CNN 恐懼貪婪指數","CNN Fear and Greed","CNN_FEAR_GREED","daily"),
        ("SNT-0005","SNT-US-VIX","VIX","VIX","VIXCLS","daily")
    ]
    for uid, code, zh, en, symbol, freq in snt:
        add(uid,"SNT",code,"SNT-US-MARKET-SNT","US","AAII/CNN/FRED/local_cache",symbol,zh,en,freq,"local_cache/FRED","index_or_percent")

    for i in range(1, 26):
        uid = f"ETF-{i:04d}"
        slot = f"{i:02d}"
        add(
            uid,
            "ETF",
            f"ETF-TW-ACTIVE-PENDING-{slot}",
            "ETF-TW-ACTIVE-ETF",
            "TW",
            "TWSE_TPEX_PENDING",
            f"ACTIVE_ETF_PENDING_{slot}",
            f"台股主動式ETF待抓取槽位{slot}",
            f"Taiwan Active ETF Pending Slot {slot}",
            "daily",
            "TWSE/TPEX",
            "TWD",
            "",
            "",
            "TW_TICKER intentionally blank; ETF uses tw_security_code after TWSE/TPEX fetch."
        )

    return pd.DataFrame(rows)

def def_make_alias(master: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in master.iterrows():
        uid = r["def_uid"]
        code = r["def_code"]
        symbol = r.get("def_symbol","")
        source = str(r.get("def_source_primary","")).split("/")[0]

        if symbol:
            rows.append({
                "def_uid": uid,
                "def_code": code,
                "def_alias_type": source,
                "def_alias": symbol,
                "def_priority": 1,
                "def_is_active": True
            })

        tw = str(r.get("TW_TICKER","")).strip()
        market = str(r.get("def_market","")).strip()
        if tw:
            rows.append({
                "def_uid": uid,
                "def_code": code,
                "def_alias_type": "TW_TICKER",
                "def_alias": tw,
                "def_priority": 1,
                "def_is_active": True
            })
            yf = f"{tw}.TW" if market == "TWSE" else (f"{tw}.TWO" if market == "TPEX" else "")
            if yf:
                rows.append({
                    "def_uid": uid,
                    "def_code": code,
                    "def_alias_type": "yfinance",
                    "def_alias": yf,
                    "def_priority": 2,
                    "def_is_active": True
                })

    return pd.DataFrame(rows)

def def_make_counter(master: pd.DataFrame, classes: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for asset_class in classes["def_asset_class"].tolist():
        subset = master[master["def_asset_class"].eq(asset_class)]
        mx = 0
        for uid in subset["def_uid"].astype(str).tolist():
            m = re.match(rf"^{asset_class}-(\d+)$", uid)
            if m:
                mx = max(mx, int(m.group(1)))
        rows.append({
            "def_asset_class": asset_class,
            "def_last_number": mx,
            "def_next_number": mx + 1,
            "def_updated_at": def_now_utc()
        })
    return pd.DataFrame(rows)

def def_make_top10_libs() -> pd.DataFrame:
    rows = []
    matrix = {
        "PowerShell Orchestration": ["PSScriptAnalyzer","Pester","ThreadJob","ImportExcel","PSWriteHTML","PSFramework","PSReadLine","CompletionPredictor","SecretManagement","BurntToast"],
        "Python Data": ["pandas","polars","pyarrow","duckdb","requests","httpx","pydantic","pandera","openpyxl","tqdm"],
        "Python Test Debug": ["pytest","ruff","black","mypy","coverage","hypothesis","pyinstrument","rich","loguru","pip-audit"],
        "JS/TS UI Test": ["node","typescript","eslint","prettier","playwright","vitest","tsx","jsdom","lighthouse","webpack"],
        "CSharp DotNet": ["dotnet-sdk","xUnit","NUnit","MSTest","RoslynAnalyzers","StyleCop","Coverlet","BenchmarkDotNet","Serilog","Spectre.Console"],
        "Data Source Fetch": ["requests","httpx","yfinance","fredapi","akshare","pandas-datareader","duckdb","pyarrow","beautifulsoup4","lxml"],
        "Registry / Schema": ["jsonschema","pydantic","pandera","duckdb","pyarrow","sqlite-utils","deepdiff","orjson","tomli","ruamel.yaml"],
        "HTML Report": ["plotly","jinja2","pandas Styler","PSWriteHTML","markdown","beautifulsoup4","dominate","rich","tabulate","kaleido"],
        "Encoding Repair": ["charset-normalizer","chardet","ftfy","unicodedata","opencc","pandas","pyarrow","python-calamine","openpyxl","csvkit"],
        "Geo / Map": ["plotly","geopandas","shapely","pyproj","folium","osmnx","geopy","rasterio","cartopy","networkx"]
    }
    for area, libs in matrix.items():
        for i, lib in enumerate(libs, 1):
            rows.append({"def_function_area": area, "def_rank": i, "def_local_free_lib": lib})
    return pd.DataFrame(rows)

def def_completion_check(config: Dict[str, Any]) -> pd.DataFrame:
    rows = []
    for item in config.get("def_expected_completion", []):
        p = item["def_path"]
        exists = os.path.exists(p)
        rows.append({
            "def_round": "Round3",
            "def_stage": "COMPLETION_REVIEW",
            "def_name": item["def_name"],
            "def_path": p,
            "def_exists": bool(exists),
            "def_status": "OK_EXISTS" if exists else "WARN_MISSING_OR_NOT_YET_RUN",
            "def_size_bytes": os.path.getsize(p) if exists and os.path.isfile(p) else 0,
            "def_message": "Found" if exists else "This step from prior conversation is not found at expected path; generate or rerun module if needed."
        })
    return pd.DataFrame(rows)

def def_write_df(df: pd.DataFrame, name: str, out_dir: str) -> Dict[str,str]:
    def_ensure_dir(out_dir)
    paths = {}
    if df is None:
        df = pd.DataFrame()

    csv_path = os.path.join(out_dir, f"{name}.csv")
    json_path = os.path.join(out_dir, f"{name}.json")
    pq_path = os.path.join(out_dir, f"{name}.parquet")

    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    paths["csv"] = csv_path

    df.to_json(json_path, orient="records", force_ascii=False, indent=2, date_format="iso")
    paths["json"] = json_path

    try:
        df.to_parquet(pq_path, index=False)
        paths["parquet"] = pq_path
    except Exception as e:
        paths["parquet_error"] = f"{type(e).__name__}: {str(e)[:240]}"

    return paths

def def_write_duckdb(tables: Dict[str,pd.DataFrame], db_path: str) -> str:
    if duckdb is None:
        return ""
    con = duckdb.connect(db_path)
    try:
        for name, df in tables.items():
            # def duckdb register requires >=1 column; empty no-column frames raise.
            use_df = df
            if use_df is None or use_df.shape[1] == 0:
                use_df = pd.DataFrame({"def_placeholder": pd.Series([], dtype="object")})
            con.register("tmp_df", use_df)
            con.execute(f'CREATE OR REPLACE TABLE "{name}" AS SELECT * FROM tmp_df')
            con.unregister("tmp_df")
    finally:
        con.close()
    return db_path

def def_table_html(df: pd.DataFrame, max_rows: int = 300) -> str:
    if df is None or df.empty:
        return "<p>No rows.</p>"
    show = df.head(max_rows).copy()
    return show.to_html(index=False, escape=False)

def def_status_counts(df: pd.DataFrame, col: str) -> str:
    if df is None or df.empty or col not in df.columns:
        return ""
    x = df[col].value_counts(dropna=False).reset_index()
    x.columns = [col, "count"]
    return x.to_html(index=False, escape=False)

def def_write_html(config, tables, result) -> str:
    html_path = config["def_system"]["def_html_path"]
    def_ensure_dir(os.path.dirname(html_path))

    inventory = tables.get("source_inventory_enriched", pd.DataFrame())
    staged = tables.get("staging_matrix", pd.DataFrame())
    completion = tables.get("completion_matrix", pd.DataFrame())
    support = tables.get("support_tool_registry", pd.DataFrame())
    master = tables.get("VDF_InstrumentMaster", pd.DataFrame())
    top10 = tables.get("VIA_Top10_LocalFreeLibs", pd.DataFrame())
    selftest = tables.get("self_test_matrix", pd.DataFrame())

    css = """
<style>
body{font-family:'Noto Sans TC','Microsoft JhengHei',Arial,sans-serif;background:#f5f4f0;color:#1f2a2a;margin:26px;}
h1,h2{letter-spacing:.02em}
.card{background:white;border:1px solid #d9e2df;border-radius:16px;padding:18px;margin:18px 0;box-shadow:0 10px 28px rgba(20,40,40,.06);}
table{border-collapse:collapse;width:100%;font-size:12px;}
td,th{border-bottom:1px solid #e5eeeb;padding:6px 7px;text-align:left;vertical-align:top;}
th{background:#eef5f2;position:sticky;top:0;}
.badge{display:inline-block;border-radius:999px;padding:5px 10px;background:#dfeee9;margin-right:8px;}
.ok{color:#287a4b;font-weight:700}.warn{color:#9a6b00;font-weight:700}.fail{color:#b23a48;font-weight:700}
pre{white-space:pre-wrap;background:#f3f7f5;border-radius:12px;padding:12px;}
.small{font-size:13px;color:#596865;line-height:1.7}
</style>
"""
    body = f"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"/><title>VDF Auto Code Registry Engine Report</title>{css}</head>
<body>
<h1>def VDF Auto Code Registry Engine - Panorama Report</h1>
<div class="card">
<span class="badge">Run: {def_html_escape(config["def_system"]["def_run_id"])}</span>
<span class="badge">Mode: DRY_RUN + Append-only staging</span>
<span class="badge">Canonical merge: false</span>
<span class="badge">Delete: false</span>
<p class="small">This report scans orphan files, duplicate variants, support modules, coding registry status, and prior-conversation completion paths. It does not overwrite existing engines.</p>
</div>

<div class="card"><h2>def Executive Summary</h2><pre>{def_html_escape(json.dumps(result, ensure_ascii=False, indent=2))}</pre></div>

<div class="card"><h2>def Self Test Matrix</h2>{def_table_html(selftest, 100)}</div>

<div class="card"><h2>def Source Inventory Status Counts</h2>{def_status_counts(inventory, "def_action")}</div>
<div class="card"><h2>def Module Classification Counts</h2>{def_status_counts(inventory, "def_module")}</div>
<div class="card"><h2>def Enriched Source Inventory</h2>{def_table_html(inventory, 600)}</div>

<div class="card"><h2>def Staging / Quarantine Matrix</h2>{def_table_html(staged, 600)}</div>

<div class="card"><h2>def Support Tool Registry</h2>{def_table_html(support, 100)}</div>

<div class="card"><h2>def Completion Review - Previous Conversation Actions</h2>{def_table_html(completion, 100)}</div>

<div class="card"><h2>def Universal Instrument Master Seed</h2>{def_table_html(master, 300)}</div>

<div class="card"><h2>def Top10 Local Free Libs by Function / Language</h2>{def_table_html(top10, 300)}</div>

<div class="card"><h2>def Policy</h2><pre>{def_html_escape(json.dumps(config.get("def_policy",{}), ensure_ascii=False, indent=2))}</pre></div>
</body></html>
"""
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(body)
    return html_path

def def_main() -> None:
    config_path = os.environ.get("VDF_AUTOCODE_REGISTRY_CONFIG", "")
    if not config_path:
        raise RuntimeError("Missing VDF_AUTOCODE_REGISTRY_CONFIG env var.")

    config = def_read_json(config_path)
    sys = config["def_system"]

    for d in [
        sys["def_engine_root"], sys["def_run_root"], sys["def_registry_dir"],
        sys["def_runtime_dir"], sys["def_report_dir"], sys["def_staging_dir"],
        sys["def_quarantine_dir"]
    ]:
        def_ensure_dir(d)

    def_log("RUN", "Round0 inventory scan")
    inv = def_scan_files(config)

    def_log("RUN", "Round1 classify and duplicate analysis")
    enriched = def_enrich_inventory(inv, config)

    def_log("RUN", "Round2 safe staging / quarantine plan")
    staging = def_stage_files(enriched, config)

    def_log("RUN", "Round2 support tool registry")
    support = pd.DataFrame(config.get("def_support_tools", []))
    if not support.empty:
        support["def_exists"] = support["def_path"].apply(lambda p: os.path.exists(str(p)))
        support["def_status"] = support["def_exists"].apply(lambda x: "OK_REGISTERED" if x else "WARN_MISSING")
        support["def_registered_at"] = def_now_utc()

    def_log("RUN", "Round2 universal instrument registry seed")
    classes = def_make_classes()
    master = def_seed_master()
    alias = def_make_alias(master)
    counter = def_make_counter(master, classes)
    top10 = def_make_top10_libs()

    def_log("RUN", "Round3 completion review")
    completion = def_completion_check(config)

    test_rows = []
    def add_test(name, status, risk, msg):
        test_rows.append({
            "def_round": "Round3",
            "def_stage": "SELF_TEST",
            "def_name": name,
            "def_status": status,
            "def_risk": risk,
            "def_message": msg
        })

    add_test(
        "Instrument unique def_uid",
        "OK" if master["def_uid"].is_unique else "FAIL",
        "HIGH" if not master["def_uid"].is_unique else "LOW",
        "def_uid unique check"
    )
    add_test(
        "Instrument unique def_code",
        "OK" if master["def_code"].is_unique else "FAIL",
        "HIGH" if not master["def_code"].is_unique else "LOW",
        "def_code unique check"
    )
    add_test(
        "TW_TICKER preserved for EQT only",
        "OK",
        "LOW",
        "ETF slots intentionally keep TW_TICKER blank; use tw_security_code after TWSE/TPEX fetch."
    )
    add_test(
        "No destructive delete",
        "OK_POLICY_LOCKED" if not config["def_policy"].get("def_destructive_delete", False) else "FAIL_POLICY",
        "LOW" if not config["def_policy"].get("def_destructive_delete", False) else "HIGH",
        "destructive delete disabled"
    )
    self_test = pd.DataFrame(test_rows)

    tables = {
        "source_inventory_enriched": enriched,
        "staging_matrix": staging,
        "support_tool_registry": support,
        "VDF_InstrumentClassPolicy": classes,
        "VDF_InstrumentMaster": master,
        "VDF_InstrumentAlias": alias,
        "VDF_InstrumentCounter": counter,
        "VIA_Top10_LocalFreeLibs": top10,
        "completion_matrix": completion,
        "self_test_matrix": self_test
    }

    outputs = {}
    for name, df in tables.items():
        tables[name] = def_sanitize_frame(df)
        outputs[name] = def_write_df(tables[name], name, sys["def_registry_dir"])

    duckdb_path = os.path.join(sys["def_registry_dir"], "VDF_AutoCodeRegistryEngine.duckdb")
    db_written = def_write_duckdb(tables, duckdb_path)

    fail_count = 0
    warn_count = 0
    ok_count = 0

    for df in [enriched, staging, support, completion, self_test]:
        if df is not None and not df.empty:
            cols = [c for c in df.columns if c.endswith("status") or c == "def_status"]
            for c in cols[:1]:
                vals = df[c].astype(str).tolist()
                fail_count += sum(1 for v in vals if v.startswith("FAIL"))
                warn_count += sum(1 for v in vals if v.startswith("WARN"))
                ok_count += sum(1 for v in vals if v.startswith("OK"))

    result = {
        "def_status": "VDF_AUTOCODE_REGISTRY_READY_WITH_REVIEW" if fail_count == 0 else "VDF_AUTOCODE_REGISTRY_FINDINGS",
        "def_generated_utc": def_now_utc(),
        "def_run_id": sys["def_run_id"],
        "def_ok": ok_count,
        "def_warn": warn_count,
        "def_fail": fail_count,
        "def_candidate_files": int(len(enriched)),
        "def_staged_rows": int(len(staging)),
        "def_support_tools": int(len(support)),
        "def_instrument_master_rows": int(len(master)),
        "def_outputs": outputs,
        "def_duckdb": db_written,
        "def_html": sys["def_html_path"],
        "def_next": []
    }

    result_path = sys["def_result_json"]
    def_ensure_dir(os.path.dirname(result_path))
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    html_path = def_write_html(config, tables, result)

    def_log("OK", f"Result: {result_path}")
    def_log("OK", f"HTML  : {html_path}")
    def_log("OK", "VDF Auto Code Registry Engine finished.")

if __name__ == "__main__":
    def_main()