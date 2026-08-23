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
import csv
import json
import traceback
import multiprocessing as mp
from pathlib import Path
from datetime import datetime

shortlist_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_SIGNATURE_DOC_PROBE_v0271_20260610_141608\\registry\\VDF_AkShare_SignatureDocShortlist_v0271.csv")
out = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_SAMPLE_CALL_GATE_v0272_20260610_143930\\runtime\\vdf_akshare_sample_call_gate_result_v0272.json")
result_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_SAMPLE_CALL_GATE_v0272_20260610_143930\\registry\\VDF_AkShare_SampleCallGate_Result_v0272.csv")
result_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_SAMPLE_CALL_GATE_v0272_20260610_143930\\registry\\VDF_AkShare_SampleCallGate_Result_v0272.json")
payload_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_SAMPLE_CALL_GATE_v0272_20260610_143930\\staging\\VDF_AkShare_SamplePayload_Max1Row_v0272.json")
max_per_category = int("2")
timeout_seconds = int("25")

TARGET_PRIORITY = ["BDI_FREIGHT", "IRON_ORE", "COKING_COAL", "STEEL", "COMMODITY_FUTURES", "MACRO_CHINA"]

result = {
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "status": "VDF_AKSHARE_SAMPLE_CALL_GATE_READY",
    "risk": "LOW",
    "policy": "Sample-call only. Max 1-row per function. Staging only. No DB write.",
    "akshare_import": False,
    "akshare_version": "",
    "shortlist_input_rows": 0,
    "attempt_count": 0,
    "success_count": 0,
    "skip_count": 0,
    "fail_count": 0,
    "timeout_count": 0,
    "categories": {},
    "successful_functions": [],
    "recommendation": "UNKNOWN",
    "outputs": {}
}

def child_call(function_name, q):
    try:
        import akshare as ak
        import pandas as pd

        fn = getattr(ak, function_name)
        obj = fn()

        row_count = 0
        col_count = 0
        sample = None
        obj_type = type(obj).__name__

        if isinstance(obj, pd.DataFrame):
            row_count = int(len(obj))
            col_count = int(len(obj.columns))
            if row_count > 0:
                sample = obj.head(1).astype(str).to_dict(orient="records")
            else:
                sample = []
        elif isinstance(obj, dict):
            row_count = 1
            col_count = len(obj.keys())
            sample = [{str(k): str(v) for k, v in obj.items()}]
        elif isinstance(obj, (list, tuple)):
            row_count = len(obj)
            col_count = 1
            sample = [str(obj[0])] if len(obj) > 0 else []
        else:
            row_count = 1 if obj is not None else 0
            col_count = 1
            sample = [str(obj)[:800]]

        q.put({
            "ok": True,
            "object_type": obj_type,
            "row_count": row_count,
            "col_count": col_count,
            "sample": sample
        })
    except Exception as e:
        q.put({
            "ok": False,
            "error": str(e),
            "traceback": traceback.format_exc()[-1800:]
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
    import akshare as ak
    result["akshare_import"] = True
    result["akshare_version"] = str(getattr(ak, "__version__", "unknown"))

    if not shortlist_csv.exists():
        raise RuntimeError("Shortlist CSV missing.")

    with shortlist_csv.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    result["shortlist_input_rows"] = len(rows)

    # category -> top functions by total_score
    selected = []
    seen_func = set()

    for cat in TARGET_PRIORITY:
        cat_rows = [r for r in rows if r.get("selected_category") == cat]
        cat_rows = sorted(cat_rows, key=lambda r: (-int(float(r.get("total_score") or 0)), r.get("function","")))
        kept = 0
        for r in cat_rows:
            fn = r.get("function","").strip()
            if not fn:
                continue
            # avoid calling same function twice across categories
            if fn in seen_func:
                continue
            seen_func.add(fn)
            selected.append(r)
            kept += 1
            if kept >= max_per_category:
                break

    samples = []
    results = []

    for r in selected:
        cat = r.get("selected_category","")
        fn = r.get("function","")
        sig = r.get("signature","")
        total_score = r.get("total_score","")

        item = {
            "selected_category": cat,
            "function": fn,
            "total_score": total_score,
            "signature": sig,
            "status": "NOT_RUN",
            "risk": "LOW",
            "object_type": "",
            "row_count": 0,
            "col_count": 0,
            "sample_rows_saved": 0,
            "error": "",
            "next_action": "review before v027.3 small-scope seed plan"
        }

        # Conservative rule: only call no-required-arg functions.
        # If signature includes required-looking args without default, skip.
        # This is heuristic but prevents broad accidental calls with guessed symbols.
        sig_body = sig.strip()
        if sig_body.startswith("(") and sig_body.endswith(")"):
            inside = sig_body[1:-1].strip()
        else:
            inside = ""

        requires_arg = False
        if inside and inside not in ["", "*"]:
            parts = [p.strip() for p in inside.split(",") if p.strip()]
            for p in parts:
                if "=" not in p and not p.startswith("*") and p not in ["self"]:
                    requires_arg = True
                    break

        if requires_arg:
            item["status"] = "SKIP_REQUIRES_ARGUMENT"
            item["risk"] = "MEDIUM"
            item["error"] = "Function signature appears to require arguments; no guessed symbols allowed in v027.2."
            result["skip_count"] += 1
            results.append(item)
            continue

        result["attempt_count"] += 1
        call = call_with_timeout(fn, timeout_seconds)

        if call.get("ok"):
            item["status"] = "OK_SAMPLE"
            item["object_type"] = str(call.get("object_type",""))
            item["row_count"] = int(call.get("row_count") or 0)
            item["col_count"] = int(call.get("col_count") or 0)

            sample = call.get("sample")
            if sample is None:
                sample = []
            if isinstance(sample, list):
                saved = sample[:1]
            else:
                saved = [sample]

            item["sample_rows_saved"] = len(saved)
            samples.append({
                "selected_category": cat,
                "function": fn,
                "object_type": item["object_type"],
                "row_count": item["row_count"],
                "col_count": item["col_count"],
                "sample_max_1row": saved
            })
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

        results.append(item)

    cats = {}
    for x in results:
        cats[x["selected_category"]] = cats.get(x["selected_category"], 0) + 1
    result["categories"] = cats
    result["successful_functions"] = [x["function"] for x in results if x["status"] == "OK_SAMPLE"]

    result_csv.parent.mkdir(parents=True, exist_ok=True)
    with result_csv.open("w", encoding="utf-8-sig", newline="") as f:
        fieldnames = [
            "selected_category","function","total_score","status","risk","object_type",
            "row_count","col_count","sample_rows_saved","signature","error","next_action"
        ]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for item in results:
            w.writerow({k: item.get(k, "") for k in fieldnames})

    result_json.parent.mkdir(parents=True, exist_ok=True)
    result_json.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    payload_json.parent.mkdir(parents=True, exist_ok=True)
    payload_json.write_text(json.dumps({
        "generated_at": result["generated_at"],
        "policy": result["policy"],
        "max_1row_samples": samples
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    result["outputs"] = {
        "sample_result_csv": str(result_csv),
        "sample_result_json": str(result_json),
        "sample_payload_json": str(payload_json)
    }

    if result["success_count"] <= 0:
        result["status"] = "VDF_AKSHARE_SAMPLE_CALL_GATE_READY_WITH_REVIEW"
        result["risk"] = "MEDIUM"
        result["recommendation"] = "NO_SAMPLE_SUCCESS_REVIEW_SIGNATURES_OR_ADD_SAFE_ARGS"
    else:
        result["recommendation"] = "ALLOW_V0273_AKSHARE_SMALL_SCOPE_SEED_PLAN_GATE_ONLY"

except Exception as e:
    result["status"] = "VDF_AKSHARE_SAMPLE_CALL_GATE_WITH_REVIEW"
    result["risk"] = "HIGH"
    result["error"] = str(e)
    result["recommendation"] = "BLOCK_SAMPLE_CALL_GATE_REPAIR_ENV_OR_SHORTLIST"

out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({
    "status": result["status"],
    "risk": result["risk"],
    "akshare_import": result["akshare_import"],
    "akshare_version": result["akshare_version"],
    "shortlist_input_rows": result["shortlist_input_rows"],
    "attempt_count": result["attempt_count"],
    "success_count": result["success_count"],
    "skip_count": result["skip_count"],
    "fail_count": result["fail_count"],
    "timeout_count": result["timeout_count"],
    "categories": result["categories"],
    "recommendation": result["recommendation"]
}, ensure_ascii=False))
