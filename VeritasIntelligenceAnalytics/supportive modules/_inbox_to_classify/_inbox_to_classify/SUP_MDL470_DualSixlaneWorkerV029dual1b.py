import os, sys, json, glob, re, hashlib, shutil, traceback
from datetime import datetime
import pandas as pd
import pyarrow.parquet as pq
import duckdb

lane = sys.argv[1]
project_root = sys.argv[2]
run_root = sys.argv[3]
lane_dir = sys.argv[4]
stage_dir = sys.argv[5]
audit_dir = sys.argv[6]
write_vrn_merge = sys.argv[7].lower() == "true"

active_root = os.path.join(project_root, "dict", "VDF", "_active")
vdf_db_root = os.path.join(project_root, "dict", "VDF", "DATABASE")
vrn_ssot_root = os.path.join(project_root, "dict", "VRN", "SSOT")
vrn_db_root = os.path.join(project_root, "dict", "VRN", "DATABASE")

os.makedirs(lane_dir, exist_ok=True)
os.makedirs(stage_dir, exist_ok=True)
os.makedirs(audit_dir, exist_ok=True)

def now():
    return datetime.now().isoformat()

def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def sha1(s, n=40):
    return hashlib.sha1(str(s).encode("utf-8", "ignore")).hexdigest()[:n]

def latest(pattern):
    files = glob.glob(pattern, recursive=True)
    files = [f for f in files if os.path.isfile(f)]
    if not files:
        return ""
    return max(files, key=os.path.getmtime)

def file_count(pattern):
    return len([f for f in glob.glob(pattern, recursive=True) if os.path.isfile(f)])

def safe_read_parquet(path):
    if not path or not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_parquet(path).astype(str).fillna("")

def pq_info(path):
    out = {"path":path, "exists":os.path.exists(path), "rows":0, "size":0, "columns":[]}
    if os.path.exists(path):
        out["size"] = os.path.getsize(path)
        try:
            pf = pq.ParquetFile(path)
            out["rows"] = pf.metadata.num_rows
            out["columns"] = pf.schema.names
        except Exception as e:
            out["error"] = str(e)
    return out

def write_parquet_atomic(df, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    df.to_parquet(tmp, index=False, compression="zstd")
    if os.path.exists(path):
        bak = path + ".bak_" + datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(path, bak)
    os.replace(tmp, path)

def clean_name(x):
    return re.sub(r"[^a-z0-9]+", "_", str(x or "").strip().lower()).strip("_")

def pick_col(df, names):
    cmap = {clean_name(c): c for c in df.columns}
    for n in names:
        k = clean_name(n)
        if k in cmap:
            return cmap[k]
    return ""

def extract_year(text):
    s = str(text or "")
    m = re.search(r"(20\d{2}|19\d{2})", s)
    if m:
        return m.group(1)
    return ""

def extract_quarter(text):
    s = str(text or "")
    m = re.search(r"\bQ([1-4])\b|第?\s*([一二三四1234])\s*季", s, re.I)
    if not m:
        return ""
    q = m.group(1) or m.group(2)
    zh = {"一":"1","二":"2","三":"3","四":"4"}
    return "Q" + zh.get(q, q)

def normalize_number(raw):
    s = str(raw or "").strip()
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1]
    s = s.replace(",", "").replace("％", "%")
    s = re.sub(r"[^\d\.\-\+%]", "", s)
    if s.endswith("%"):
        s = s[:-1]
    try:
        v = float(s)
        if neg:
            v = -v
        return str(v)
    except Exception:
        return ""

def extract_numbers(text):
    s = str(text or "")
    vals = []
    rx = r"(?<![A-Za-z0-9])[-+]?\(?\d{1,3}(?:,\d{3})*(?:\.\d+)?\)?%?(?![A-Za-z0-9])|(?<![A-Za-z0-9])[-+]?\d+(?:\.\d+)?%?(?![A-Za-z0-9])"
    for m in re.finditer(rx, s):
        raw = m.group(0)
        clean = raw.replace(",", "").replace("%", "").replace("(", "").replace(")", "")
        if clean in [str(y) for y in range(1990, 2035)]:
            continue
        num = normalize_number(raw)
        if num != "":
            vals.append((raw, num))
    return vals

def record_hash(row, keys):
    return sha1("|".join(str(row.get(k, "")) for k in keys), 40)

def result(status, risk, metrics, outputs, checks=None):
    return {
        "lane": lane,
        "generated_at": now(),
        "status": status,
        "risk": risk,
        "metrics": metrics or {},
        "outputs": outputs or {},
        "checks": checks or []
    }

try:
    if lane == "VDF1_RUNTIME":
        runtime_files = glob.glob(os.path.join(project_root, "**", "*Runtime*.json"), recursive=True)
        runtime_files = [f for f in runtime_files if os.path.isfile(f)]
        vdf_like = [f for f in runtime_files if re.search(r"VDF|VeritasDataForge|DataForge|TWSE|TPEX|MOPS", os.path.basename(f), re.I)]
        final_seal = latest(os.path.join(project_root, "**", "VIA_FinalOperationsSeal_Runtime_v02876.json"))
        daily_health = latest(os.path.join(project_root, "**", "VIA_DailyHealthNonThrowingMonitor_Runtime_v028754.json"))

        status = "VDF_RUNTIME_REVIEW_REQUIRED"
        risk = "MEDIUM"
        if vdf_like:
            status = "VDF_RUNTIME_FOUND"
            risk = "LOW"

        out = result(status, risk, {
            "runtime_total": len(runtime_files),
            "vdf_runtime_count": len(vdf_like),
            "final_seal_found": bool(final_seal),
            "daily_health_found": bool(daily_health)
        }, {
            "latest_vdf_runtime": max(vdf_like, key=os.path.getmtime) if vdf_like else "",
            "final_seal": final_seal,
            "daily_health": daily_health
        })

    elif lane == "VDF2_DATA":
        parquet_files = glob.glob(os.path.join(vdf_db_root, "**", "*.parquet"), recursive=True)
        duckdb_files = glob.glob(os.path.join(vdf_db_root, "**", "*.duckdb"), recursive=True)

        parquet_infos = []
        for p in sorted(parquet_files)[:500]:
            info = pq_info(p)
            parquet_infos.append(info)

        duck_infos = []
        for d in sorted(duckdb_files)[:50]:
            item = {"path": d, "exists": True, "tables": [], "status": "READY"}
            try:
                con = duckdb.connect(d, read_only=True)
                tables = con.execute("SHOW TABLES").fetchall()
                item["tables"] = [x[0] for x in tables]
                con.close()
            except Exception as e:
                item["status"] = "ERROR"
                item["error"] = str(e)
            duck_infos.append(item)

        bad_parquet = [x for x in parquet_infos if "error" in x]
        bad_duck = [x for x in duck_infos if x.get("status") == "ERROR"]

        status = "VDF_DATA_INTEGRITY_READY" if not bad_parquet and not bad_duck and parquet_files else "VDF_DATA_INTEGRITY_REVIEW_REQUIRED"
        risk = "LOW" if status.endswith("READY") else "MEDIUM"

        inv_csv = os.path.join(lane_dir, "VDF2_DataInventory.csv")
        pd.DataFrame(parquet_infos).to_csv(inv_csv, index=False, encoding="utf-8-sig")

        out = result(status, risk, {
            "parquet_count": len(parquet_files),
            "duckdb_count": len(duckdb_files),
            "bad_parquet": len(bad_parquet),
            "bad_duckdb": len(bad_duck)
        }, {
            "inventory_csv": inv_csv
        }, parquet_infos[:30] + duck_infos[:20])

    elif lane == "VDF3_GAP_PLAN":
        expected_keywords = {
            "ticker_master": ["ticker","master","basic","listed","security"],
            "price_daily": ["price","daily","ohlc","history"],
            "index_daily": ["index"],
            "institutional": ["institutional","foreign","dealer","trust"],
            "margin_short": ["margin","short"],
            "revenue": ["revenue","monthly"],
            "financials": ["financial","income","balance","cashflow"],
            "etf": ["etf"],
            "macro": ["fred","macro"],
            "commodity": ["commodity","bdi","steel"]
        }

        files = glob.glob(os.path.join(vdf_db_root, "**", "*.parquet"), recursive=True)
        lower_names = [os.path.basename(f).lower() for f in files]

        coverage = []
        for cat, kws in expected_keywords.items():
            found = any(any(k in n for k in kws) for n in lower_names)
            coverage.append({"category": cat, "found": found})

        found_count = sum(1 for x in coverage if x["found"])
        missing = [x["category"] for x in coverage if not x["found"]]

        status = "VDF_GAP_PLAN_READY" if found_count >= 6 else "VDF_GAP_PLAN_REVIEW_REQUIRED"
        risk = "LOW" if found_count >= 8 else "MEDIUM"

        plan_json = os.path.join(lane_dir, "VDF3_GapPlan.json")
        write_json(plan_json, {
            "generated_at": now(),
            "coverage": coverage,
            "found_count": found_count,
            "missing": missing,
            "policy": {
                "full_rerun": False,
                "next_action": "Targeted VDF finish gate only; no blind full rerun."
            }
        })

        out = result(status, risk, {
            "expected_categories": len(expected_keywords),
            "found_categories": found_count,
            "missing_categories": len(missing)
        }, {"gap_plan_json": plan_json}, coverage)

    elif lane == "VRN1_TABLE_GEOMETRY":
        active_pointer = os.path.join(vrn_ssot_root, "VRN_ACTIVE_STAGE_POINTER.json")
        pointer = read_json(active_pointer)
        report_text_path = pointer.get("latest_report_text_parquet","")
        ssot_tables = pointer.get("ssot_tables", {}) or {}
        financial_alias_path = ssot_tables.get("financial_alias","")
        basic_path = os.path.join(vrn_db_root, "StockReportBasicInfo.parquet")
        fin_db_path = os.path.join(vrn_db_root, "StockReportFinancialData.parquet")
        stage_path = os.path.join(stage_dir, "VRN_ReportFinancialData_TableLikeExpansion_Stage_v029VRN1D1.parquet")
        audit_csv = os.path.join(audit_dir, "VRN_ReportFinancialData_TableLikeExpansion_AuditSample_v029VRN1D1.csv")

        text_df = safe_read_parquet(report_text_path)
        alias_df = safe_read_parquet(financial_alias_path)
        basic_df = safe_read_parquet(basic_path)

        text_col = pick_col(text_df, ["text","line_text","content","sentence","cell_text","raw_text"])
        report_col = pick_col(text_df, ["report_id"])
        file_col = pick_col(text_df, ["file_id"])
        page_col = pick_col(text_df, ["page","page_no","pageno"])
        src_col = pick_col(text_df, ["source_path","path","file_path","filename","file_name"])

        aliases = []
        for _, r in alias_df.iterrows():
            can = r.get("canonical","") or r.get("account_canonical","")
            al = r.get("alias","") or r.get("account_alias","")
            st = r.get("statement","")
            if can and al:
                aliases.append({"canonical": str(can), "alias": str(al), "statement": str(st)})
        aliases.sort(key=lambda x: len(x["alias"]), reverse=True)

        basic_by_report = {}
        basic_by_file = {}
        if not basic_df.empty:
            br = pick_col(basic_df, ["report_id"])
            bf = pick_col(basic_df, ["file_id"])
            bt = pick_col(basic_df, ["tw_ticker","ticker"])
            bn = pick_col(basic_df, ["company_name","name"])
            bb = pick_col(basic_df, ["broker"])
            bd = pick_col(basic_df, ["report_date"])
            for _, r in basic_df.iterrows():
                item = {
                    "report_id": r.get(br,"") if br else "",
                    "file_id": r.get(bf,"") if bf else "",
                    "tw_ticker": r.get(bt,"") if bt else "",
                    "company_name": r.get(bn,"") if bn else "",
                    "broker": r.get(bb,"") if bb else "",
                    "report_date": r.get(bd,"") if bd else ""
                }
                if item["report_id"]: basic_by_report[item["report_id"]] = item
                if item["file_id"]: basic_by_file[item["file_id"]] = item

        rows = []
        scanned = 0
        matched = 0

        target_cols = [
            "report_id","file_id","tw_ticker","company_name","broker","report_date",
            "period","fiscal_year","fiscal_quarter","statement",
            "account_canonical","account_alias","value","value_raw","unit","currency",
            "source_table_id","source_page","source_text","source_text_hash","value_index",
            "historical_check_confidence","historical_check",
            "add_sub_check_confidence","add_sub_check",
            "division_check_confidence","division_check",
            "final_trust_confidence","final_trust_band",
            "validation_status","source_stage","source_path","ingested_at","record_hash"
        ]

        if text_col and aliases:
            for _, tr in text_df.iterrows():
                txt = str(tr.get(text_col,"") or "")
                if len(txt.strip()) < 2:
                    continue
                scanned += 1
                nums = extract_numbers(txt)
                if not nums:
                    continue

                ma = None
                for a in aliases:
                    al = a["alias"]
                    if re.search(r"[\u4e00-\u9fff]", al):
                        ok = al in txt
                    else:
                        ok = re.search(r"(?<![A-Za-z])" + re.escape(al) + r"(?![A-Za-z])", txt, re.I) is not None
                    if ok:
                        ma = a
                        break
                if not ma:
                    continue

                matched += 1
                rid = str(tr.get(report_col,"") if report_col else "")
                fid = str(tr.get(file_col,"") if file_col else "")
                bi = basic_by_report.get(rid) or basic_by_file.get(fid) or {}
                if not rid: rid = bi.get("report_id","")
                if not fid: fid = bi.get("file_id","")
                year = extract_year(txt) or extract_year(bi.get("report_date",""))
                quarter = extract_quarter(txt)
                src = str(tr.get(src_col,"") if src_col else "")
                page = str(tr.get(page_col,"") if page_col else "")
                source_hash = sha1(txt, 24)

                for vi, (raw_value, norm_value) in enumerate(nums, start=1):
                    row = {
                        "report_id": rid,
                        "file_id": fid,
                        "tw_ticker": bi.get("tw_ticker",""),
                        "company_name": bi.get("company_name",""),
                        "broker": bi.get("broker",""),
                        "report_date": bi.get("report_date",""),
                        "period": (year + quarter) if year or quarter else "",
                        "fiscal_year": year,
                        "fiscal_quarter": quarter,
                        "statement": ma.get("statement",""),
                        "account_canonical": ma.get("canonical",""),
                        "account_alias": ma.get("alias",""),
                        "value": norm_value,
                        "value_raw": raw_value,
                        "unit": "%" if "%" in txt else "",
                        "currency": "TWD",
                        "source_table_id": "",
                        "source_page": page,
                        "source_text": txt[:1000],
                        "source_text_hash": source_hash,
                        "value_index": str(vi),
                        "historical_check_confidence": "",
                        "historical_check": "PENDING",
                        "add_sub_check_confidence": "",
                        "add_sub_check": "PENDING",
                        "division_check_confidence": "",
                        "division_check": "PENDING",
                        "final_trust_confidence": "0.50",
                        "final_trust_band": "ORANGE",
                        "validation_status": "STAGE_TABLELIKE_EXPANSION_REVIEW",
                        "source_stage": "VRN_1D1_REPORTTEXT_TABLELIKE_EXPANSION",
                        "source_path": src,
                        "ingested_at": now()
                    }
                    row["record_hash"] = record_hash(row, ["report_id","file_id","account_canonical","source_text_hash","value","value_index"])
                    rows.append(row)

        stage_df = pd.DataFrame(rows, columns=target_cols)
        if not stage_df.empty:
            stage_df = stage_df.astype(str).fillna("")
            stage_df = stage_df.drop_duplicates(subset=["record_hash"], keep="last").reset_index(drop=True)
        write_parquet_atomic(stage_df, stage_path)
        stage_df.head(500).to_csv(audit_csv, index=False, encoding="utf-8-sig")

        merged_rows = 0
        if write_vrn_merge:
            old = safe_read_parquet(fin_db_path)
            if not old.empty:
                # align columns
                for c in stage_df.columns:
                    if c not in old.columns:
                        old[c] = ""
                for c in old.columns:
                    if c not in stage_df.columns:
                        stage_df[c] = ""
                merged = pd.concat([old[stage_df.columns], stage_df], ignore_index=True)
            else:
                merged = stage_df.copy()
            if not merged.empty:
                merged = merged.astype(str).fillna("").drop_duplicates(subset=["record_hash"], keep="last").reset_index(drop=True)
            write_parquet_atomic(merged, fin_db_path)
            merged_rows = len(merged)

        out = result("VRN_1D1_TABLELIKE_EXPANSION_READY" if len(stage_df)>0 else "VRN_1D1_TABLELIKE_EXPANSION_REVIEW", "LOW" if len(stage_df)>0 else "MEDIUM", {
            "text_rows": len(text_df),
            "scanned_text_rows": scanned,
            "matched_text_rows": matched,
            "stage_rows": len(stage_df),
            "merged_total_rows": merged_rows
        }, {
            "stage_parquet": stage_path,
            "audit_csv": audit_csv,
            "financial_db_parquet": fin_db_path
        })

    elif lane == "VRN2_VALIDATION":
        fin_db_path = os.path.join(vrn_db_root, "StockReportFinancialData.parquet")
        out_path = os.path.join(stage_dir, "VRN_FinancialDataValidation_v029VRN1D1.parquet")
        audit_csv = os.path.join(audit_dir, "VRN_FinancialDataValidation_AuditSample_v029VRN1D1.csv")
        df = safe_read_parquet(fin_db_path)

        checks = []
        if df.empty:
            val = pd.DataFrame(columns=["check_id","status","severity","message"])
        else:
            dups = int(df["record_hash"].duplicated().sum()) if "record_hash" in df.columns else 0
            blank_value = int((df["value"].astype(str).str.len() == 0).sum()) if "value" in df.columns else len(df)
            accounts = int(df["account_canonical"].nunique()) if "account_canonical" in df.columns else 0
            reports = int(df["report_id"].nunique()) if "report_id" in df.columns else 0

            checks = [
                {"check_id":"DUP_RECORD_HASH","status":"PASS" if dups==0 else "FAIL","severity":"HIGH","value":dups,"message":"record_hash duplicates"},
                {"check_id":"BLANK_VALUE","status":"PASS" if blank_value==0 else "WARN","severity":"MEDIUM","value":blank_value,"message":"blank value count"},
                {"check_id":"ACCOUNT_COVERAGE","status":"PASS" if accounts>=5 else "WARN","severity":"MEDIUM","value":accounts,"message":"canonical account coverage"},
                {"check_id":"REPORT_COVERAGE","status":"PASS" if reports>=10 else "WARN","severity":"MEDIUM","value":reports,"message":"report_id coverage"}
            ]
            val = pd.DataFrame(checks)

        write_parquet_atomic(val, out_path)
        val.to_csv(audit_csv, index=False, encoding="utf-8-sig")
        fail = sum(1 for x in checks if x.get("status") == "FAIL")
        warn = sum(1 for x in checks if x.get("status") == "WARN")

        out = result("VRN_VALIDATION_READY" if fail==0 else "VRN_VALIDATION_REVIEW_REQUIRED", "LOW" if fail==0 and warn==0 else "MEDIUM", {
            "financial_rows": len(df),
            "fail": fail,
            "warn": warn,
            "checks": len(checks)
        }, {"validation_parquet":out_path,"audit_csv":audit_csv}, checks)

    elif lane == "VRN3_EXCEPTION_REVIEW":
        basic_path = os.path.join(vrn_db_root, "StockReportBasicInfo.parquet")
        fin_path = os.path.join(vrn_db_root, "StockReportFinancialData.parquet")
        out_path = os.path.join(stage_dir, "VRN_ExceptionBrokerDateReview_v029VRN1D1.parquet")
        audit_csv = os.path.join(audit_dir, "VRN_ExceptionBrokerDateReview_AuditSample_v029VRN1D1.csv")
        basic = safe_read_parquet(basic_path)
        fin = safe_read_parquet(fin_path)

        rows = []
        if not basic.empty:
            for col, label in [("broker","missing_broker"),("report_date","missing_report_date"),("tw_ticker","missing_ticker")]:
                if col in basic.columns:
                    bad = basic[basic[col].astype(str).str.len() == 0]
                    for _, r in bad.iterrows():
                        rows.append({
                            "review_type": label,
                            "report_id": r.get("report_id",""),
                            "file_id": r.get("file_id",""),
                            "tw_ticker": r.get("tw_ticker",""),
                            "broker": r.get("broker",""),
                            "report_date": r.get("report_date",""),
                            "severity": "MEDIUM" if label!="missing_ticker" else "HIGH",
                            "action": "manual_or_alias_review",
                            "source": basic_path
                        })

        if fin.empty:
            rows.append({
                "review_type": "financial_empty",
                "report_id": "",
                "file_id": "",
                "tw_ticker": "",
                "broker": "",
                "report_date": "",
                "severity": "HIGH",
                "action": "run_vrn_1d_or_1d1",
                "source": fin_path
            })

        rev = pd.DataFrame(rows)
        if rev.empty:
            rev = pd.DataFrame(columns=["review_type","report_id","file_id","tw_ticker","broker","report_date","severity","action","source"])
        write_parquet_atomic(rev, out_path)
        rev.head(500).to_csv(audit_csv, index=False, encoding="utf-8-sig")

        high = int((rev["severity"]=="HIGH").sum()) if not rev.empty else 0
        med = int((rev["severity"]=="MEDIUM").sum()) if not rev.empty else 0

        out = result("VRN_REVIEW_MATRIX_READY" if high==0 else "VRN_REVIEW_MATRIX_READY_WITH_HIGH_REVIEW", "LOW" if high==0 and med==0 else "MEDIUM", {
            "review_rows": len(rev),
            "high": high,
            "medium": med
        }, {"review_parquet":out_path,"audit_csv":audit_csv})

    else:
        out = result("UNKNOWN_LANE", "HIGH", {}, {}, [{"error":"unknown lane"}])

except Exception as e:
    out = result("LANE_FATAL", "HIGH", {"error": str(e)}, {}, [{"traceback": traceback.format_exc()}])

out_path = os.path.join(lane_dir, lane + "_Runtime.json")
write_json(out_path, out)
print(json.dumps(out, ensure_ascii=False))