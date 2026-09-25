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
import csv
import traceback
import multiprocessing as mp
from pathlib import Path
from datetime import datetime

seed_plan_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_SMALL_SCOPE_SEED_PLAN_GATE_HOTFIX_v02731_20260610_144716\\plan\\VDF_AkShare_SmallScopeSeedPlan_v02731.json")
staging_dir = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_SMALL_SCOPE_CANDIDATE_SEED_STAGING_v0274_20260610_145643\\staging")
out = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_SMALL_SCOPE_CANDIDATE_SEED_STAGING_v0274_20260610_145643\\runtime\\vdf_akshare_candidate_seed_staging_result_v0274.json")
manifest_path = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_SMALL_SCOPE_CANDIDATE_SEED_STAGING_v0274_20260610_145643\\registry\\VDF_AkShare_CandidateSeedManifest_v0274.json")
result_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_SMALL_SCOPE_CANDIDATE_SEED_STAGING_v0274_20260610_145643\\registry\\VDF_AkShare_CandidateSeedRun_Result_v0274.csv")
result_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_SMALL_SCOPE_CANDIDATE_SEED_STAGING_v0274_20260610_145643\\registry\\VDF_AkShare_CandidateSeedRun_Result_v0274.json")
timeout_seconds = int("45")
max_rows_per_function = int("300")

result = {
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "status": "VDF_AKSHARE_SMALL_SCOPE_CANDIDATE_SEED_STAGING_READY",
    "risk": "LOW",
    "policy": "Staging candidate only. No DATABASE write. No canonical merge.",
    "seed_plan_count": 0,
    "attempt_count": 0,
    "success_count": 0,
    "fail_count": 0,
    "timeout_count": 0,
    "staging_tables": {},
    "total_rows_staged": 0,
    "recommendation": "UNKNOWN",
    "outputs": {}
}

def child_call(function_name, q):
    try:
        import akshare as ak
        import pandas as pd

        fn = getattr(ak, function_name)
        obj = fn()

        if isinstance(obj, pd.DataFrame):
            df = obj.copy()
        elif isinstance(obj, dict):
            df = pd.DataFrame([obj])
        elif isinstance(obj, (list, tuple)):
            df = pd.DataFrame({"value": list(obj)})
        else:
            df = pd.DataFrame({"value": [obj]})

        q.put({
            "ok": True,
            "rows": len(df),
            "columns": list(df.columns),
            "data": df.head(max_rows_per_function).astype(str).to_dict(orient="records")
        })
    except Exception as e:
        q.put({
            "ok": False,
            "error": str(e),
            "traceback": traceback.format_exc()[-2400:]
        })

def call_with_timeout(function_name, timeout_seconds):
    q = mp.Queue()
    p = mp.Process(target=child_call, args=(function_name, q))
    p.start()
    p.join(timeout_seconds)

    if p.is_alive():
        p.terminate()
        p.join(3)
        return {
            "ok": False,
            "timeout": True,
            "error": f"timeout after {timeout_seconds}s"
        }

    if not q.empty():
        return q.get()

    return {
        "ok": False,
        "timeout": False,
        "error": "child returned no result"
    }

try:
    import pandas as pd

    if not seed_plan_json.exists():
        raise RuntimeError("Seed plan JSON missing.")

    seed_plan = json.loads(seed_plan_json.read_text(encoding="utf-8"))
    plan = seed_plan.get("plan", [])
    plan = [p for p in plan if p.get("selected") is True]

    result["seed_plan_count"] = len(plan)

    staging_dir.mkdir(parents=True, exist_ok=True)

    run_rows = []
    staged_by_table = {}
    manifest_items = []

    for p in plan:
        fn = p.get("function", "")
        target_table = p.get("target_table", "VDF_AkShare_Unclassified_Candidate")
        category = p.get("selected_category", "")
        symbol_hint = p.get("symbol_hint", "")
        canonical_family = p.get("canonical_family", "")
        priority = p.get("priority", "")

        item = {
            "function": fn,
            "selected_category": category,
            "target_table": target_table,
            "canonical_family": canonical_family,
            "symbol_hint": symbol_hint,
            "priority": priority,
            "status": "NOT_RUN",
            "risk": "LOW",
            "reported_rows": 0,
            "staged_rows": 0,
            "columns": "",
            "error": ""
        }

        result["attempt_count"] += 1
        call = call_with_timeout(fn, timeout_seconds)

        if call.get("ok"):
            data = call.get("data", [])
            reported_rows = int(call.get("rows") or 0)
            cols = call.get("columns") or []

            df = pd.DataFrame(data)
            if len(df) > 0:
                df.insert(0, "vdf_source_function", fn)
                df.insert(1, "vdf_selected_category", category)
                df.insert(2, "vdf_target_table", target_table)
                df.insert(3, "vdf_symbol_hint", symbol_hint)
                df.insert(4, "vdf_canonical_family", canonical_family)
                df.insert(5, "vdf_priority", priority)
                df.insert(6, "vdf_seeded_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                df.insert(7, "vdf_policy", "STAGING_ONLY_NO_DATABASE_WRITE")

                if target_table not in staged_by_table:
                    staged_by_table[target_table] = []
                staged_by_table[target_table].append(df)

            item["status"] = "OK_STAGED"
            item["reported_rows"] = reported_rows
            item["staged_rows"] = int(len(df))
            item["columns"] = "|".join([str(x) for x in cols])
            result["success_count"] += 1
        else:
            if call.get("timeout"):
                item["status"] = "TIMEOUT"
                item["risk"] = "MEDIUM"
                result["timeout_count"] += 1
            else:
                item["status"] = "CALL_FAIL"
                item["risk"] = "MEDIUM"
                result["fail_count"] += 1
            item["error"] = str(call.get("error",""))

        run_rows.append(item)

    for table, frames in staged_by_table.items():
        if not frames:
            continue
        table_df = pd.concat(frames, ignore_index=True)

        csv_path = staging_dir / f"{table}_v0274.csv"
        json_path = staging_dir / f"{table}_v0274.json"
        parquet_path = staging_dir / f"{table}_v0274.parquet"

        table_df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        table_df.to_json(json_path, orient="records", force_ascii=False, indent=2)

        parquet_written = False
        try:
            table_df.to_parquet(parquet_path, index=False)
            parquet_written = True
        except Exception:
            parquet_path = ""

        result["staging_tables"][table] = int(len(table_df))
        result["total_rows_staged"] += int(len(table_df))

        manifest_items.append({
            "target_table": table,
            "rows": int(len(table_df)),
            "csv": str(csv_path),
            "json": str(json_path),
            "parquet": str(parquet_path) if parquet_written else "",
            "parquet_written": parquet_written
        })

    result_csv.parent.mkdir(parents=True, exist_ok=True)
    with result_csv.open("w", encoding="utf-8-sig", newline="") as f:
        fieldnames = [
            "function","selected_category","target_table","canonical_family","symbol_hint",
            "priority","status","risk","reported_rows","staged_rows","columns","error"
        ]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in run_rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})

    result_json.parent.mkdir(parents=True, exist_ok=True)
    result_json.write_text(json.dumps(run_rows, ensure_ascii=False, indent=2), encoding="utf-8")

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps({
        "generated_at": result["generated_at"],
        "policy": result["policy"],
        "staging_dir": str(staging_dir),
        "max_rows_per_function": max_rows_per_function,
        "timeout_seconds": timeout_seconds,
        "manifest_items": manifest_items,
        "run_rows": run_rows
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    result["outputs"] = {
        "candidate_manifest": str(manifest_path),
        "candidate_run_csv": str(result_csv),
        "candidate_run_json": str(result_json),
        "staging_dir": str(staging_dir)
    }

    if result["success_count"] <= 0:
        result["status"] = "VDF_AKSHARE_SMALL_SCOPE_CANDIDATE_SEED_STAGING_READY_WITH_REVIEW"
        result["risk"] = "MEDIUM"
        result["recommendation"] = "NO_CANDIDATE_STAGED_REVIEW_FUNCTIONS"
    elif result["fail_count"] > 0 or result["timeout_count"] > 0:
        result["status"] = "VDF_AKSHARE_SMALL_SCOPE_CANDIDATE_SEED_STAGING_READY_WITH_NOTES"
        result["risk"] = "MEDIUM"
        result["recommendation"] = "ALLOW_V0275_CANDIDATE_STAGING_FINAL_SEAL_WITH_QUARANTINE_NOTES"
    else:
        result["recommendation"] = "ALLOW_V0275_CANDIDATE_STAGING_FINAL_SEAL"

except Exception as e:
    result["status"] = "VDF_AKSHARE_SMALL_SCOPE_CANDIDATE_SEED_STAGING_WITH_REVIEW"
    result["risk"] = "HIGH"
    result["error"] = str(e)
    result["recommendation"] = "BLOCK_CANDIDATE_SEED_STAGING_REPAIR"

out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({
    "status": result["status"],
    "risk": result["risk"],
    "seed_plan_count": result["seed_plan_count"],
    "attempt_count": result["attempt_count"],
    "success_count": result["success_count"],
    "fail_count": result["fail_count"],
    "timeout_count": result["timeout_count"],
    "total_rows_staged": result["total_rows_staged"],
    "staging_tables": result["staging_tables"],
    "recommendation": result["recommendation"]
}, ensure_ascii=False))
