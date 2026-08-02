"""VIA 啟動驅動器：掃模組 → 跑擷取引擎 → 跑測試 → 吐 JSON（給 PS 啟動器讀）。

用法：
  python via_launch_driver.py --root <專案> --data <資料夾> --out <輸出> [--pkg <pmis_lite上層>]

只做靜態掃描與樣本擷取，不動原始檔（append-only、只讀）。永不崩，錯誤入 JSON。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import traceback


def _load_pkg(pkg_parent):
    if pkg_parent and pkg_parent not in sys.path:
        sys.path.insert(0, pkg_parent)


def run_module_scan(root):
    from pmis_lite import module_scan as ms
    try:
        r = ms.scan_project(root)
        g = ms.import_guide(r["inventory"])
        return {"ok": True, "count": r["count"], "by_role": r["by_role"],
                "inventory": r["inventory"], "guide": g}
    except Exception as e:
        return {"ok": False, "error": f"{e}", "trace": traceback.format_exc()}


def run_ingest_over(data_dir, out_dir):
    from pmis_lite import ingest_engine as ie, super_bom as sb
    if not data_dir or not os.path.isdir(data_dir):
        return {"ok": True, "skipped": "no data dir", "files": 0}
    paths = []
    for dp, _, fns in os.walk(data_dir):
        for fn in fns:
            paths.append(os.path.join(dp, fn))
    seed = {"topic": {}}
    for maj, subs in sb.merged_commodity_taxonomy().items():
        for sub, kws in subs.items():
            seed["topic"][f"{maj}/{sub}"] = kws
    try:
        csv_path = os.path.join(out_dir, "ingest_numbered.csv")
        res = ie.run_ingest(paths, dims=("topic",), seed=seed, dedup_on=False,
                            csv_path=csv_path,
                            out_json=os.path.join(out_dir, "ingest_result.json"))
        return {"ok": True, "files": len(paths),
                "completeness": res["completeness"],
                "correction": res["parameters"]["correction"],
                "dedup": res["parameters"]["dedup"],
                "classification": res["parameters"]["classification"],
                "summary": res["summary"], "csv": csv_path,
                "data_count": len(res["data"])}
    except Exception as e:
        return {"ok": False, "error": f"{e}", "trace": traceback.format_exc()}


def run_tests(pkg_parent):
    """執行 test_stage1 內所有 test_ 函式，逐一計 pass/fail。"""
    test_path = os.path.join(pkg_parent or ".", "tests", "test_stage1.py")
    if not os.path.exists(test_path):
        return {"ok": True, "skipped": "no tests", "passed": 0, "failed": 0}
    ns = {"__file__": test_path, "__name__": "test_stage1"}
    try:
        src = open(test_path, encoding="utf-8").read()
        exec(compile(src, test_path, "exec"), ns)
    except Exception as e:
        return {"ok": False, "error": f"載入測試失敗 {e}"}
    fns = [k for k in ns if k.startswith("test_") and callable(ns[k])]
    passed, failed, fails = 0, 0, []
    for name in fns:
        try:
            ns[name]()
            passed += 1
        except Exception as e:
            failed += 1
            fails.append({"test": name, "error": str(e)[:200]})
    return {"ok": True, "total": len(fns), "passed": passed,
            "failed": failed, "failures": fails}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--data", default="")
    ap.add_argument("--out", default=".")
    ap.add_argument("--pkg", default="")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    _load_pkg(a.pkg)
    result = {
        "root": a.root,
        "modules": run_module_scan(a.root),
        "ingest": run_ingest_over(a.data, a.out),
        "tests": run_tests(a.pkg),
    }
    out_json = os.path.join(a.out, "via_launch_report.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(out_json)


if __name__ == "__main__":
    main()
