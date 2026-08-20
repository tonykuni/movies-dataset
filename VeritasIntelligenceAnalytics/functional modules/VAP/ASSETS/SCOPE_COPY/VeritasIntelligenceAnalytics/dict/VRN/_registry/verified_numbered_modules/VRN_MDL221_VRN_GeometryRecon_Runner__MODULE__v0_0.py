# -*- coding: utf-8 -*-
from __future__ import annotations
import csv, importlib.util, json, os, sys

MODULE_PATH = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIS_VRN_GeometryReconstructor_v0100.py"
MATRIX_CSV  = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\_vrn_basicinfo_financial_matrix_runs\RUN_20260531_085452\VRN_FinancialData_Matrix.csv"
OUT_DIR     = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\_vrn_geometry_reconstructor_runs\RUN_20260531_211959"
TARGETS     = ["凱基投顧_鋼鐵產業", "凱基投顧_1476", "GS-2317", "GS-2382", "JP-2330", "6933_AMAX", "兆豐晨會報告(二)", "UBS-Asia Hardware Insights"]

def imp(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import " + path)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m; spec.loader.exec_module(m); return m

def read_csv(p):
    if not os.path.isfile(p): return []
    with open(p, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def write_csv(p, rows):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    if not rows: rows = [{"Light":"⚪","Risk":"GREEN","Status":"EMPTY","Note":"No rows"}]
    fields = []
    for r in rows:
        for k in r.keys():
            if k not in fields: fields.append(k)
    with open(p, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)

def is_target(src):
    s = src or ""
    return any(t in s for t in TARGETS)

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    mod = imp(MODULE_PATH, "VIS_VRN_GeometryReconstructor_v0100_runtime")
    sc = mod.self_check()

    rows = [r for r in read_csv(MATRIX_CSV) if is_target(r.get("SourceFile", ""))]
    files = sorted({r.get("SourceFile","") for r in rows})

    green, quarantine, validation = [], [], []
    counts = {"B1_TRANSPOSE_DEAD_SEGMENT":0,"B2_CONCAT_OVERFLOW":0,"B3_MERGED_MULTI_ACCOUNT":0,
              "B4_SPLIT_NUMBER":0,"OTHER":0}
    recon_total = 0

    for r in rows:
        out = mod.reconstruct(r)
        bug = out["Bug"]; counts[bug] = counts.get(bug, 0) + 1
        if bug == "OTHER":
            continue
        for lr in out["LongRows"]:
            rr = dict(lr); rr["RowRisk"] = out["Risk"]; rr["RowStatus"] = out["Status"]
            rr["Light"] = "🟢" if out["Risk"] == "GREEN" else "🟡"
            recon_total += 1
            (green if out["Risk"] == "GREEN" else quarantine).append(rr)
        validation.append({"Light":"🟢" if out["Risk"]=="GREEN" else "🟡","Risk":out["Risk"],
                           "Status":out["Status"],"Bug":bug,"SourceFile":out.get("AccountRaw_orig","")[:0] or r.get("SourceFile",""),
                           "SourcePage":r.get("SourcePage",""),"AccountRaw":out["AccountRaw_orig"],
                           "ValueRaw":out["ValueRaw_orig"],"RestoredRows":len(out["LongRows"]),
                           "DbWrite":False,"CanonicalWrite":False,"ParserCoreRewrite":False,"Delete":False})

    risk = "GREEN"; status = "GEOMETRY_RECONSTRUCT_PASS"
    if not sc.get("hard_pass", False):
        risk, status = "HIGH", "MODULE_SELF_CHECK_FAIL"
    elif quarantine:
        risk, status = "YELLOW", "GEOMETRY_RECONSTRUCT_WITH_QUARANTINE"

    summary = {"Light":"🔴" if risk=="HIGH" else ("🟡" if risk=="YELLOW" else "🟢"),
               "Risk":risk,"Status":status,"ModuleSelfCheck":bool(sc.get("hard_pass",False)),
               "TargetFiles":len(files),"InputFinancialRows":len(rows),"ReconstructedRows":recon_total,
               "DbReadyGreenRows":len(green),"QuarantineRows":len(quarantine),
               "B1":counts["B1_TRANSPOSE_DEAD_SEGMENT"],"B2":counts["B2_CONCAT_OVERFLOW"],
               "B3":counts["B3_MERGED_MULTI_ACCOUNT"],"B4":counts["B4_SPLIT_NUMBER"],
               "ExecutionMode":"TARGETED_8FILE_ONLY","DbWrite":False,"CanonicalWrite":False,
               "ParserCoreRewrite":False,"Delete":False}

    write_csv(os.path.join(OUT_DIR, "VRN_GeometryRecon_DBReadyGreen.csv"), green)
    write_csv(os.path.join(OUT_DIR, "VRN_GeometryRecon_Quarantine.csv"), quarantine)
    write_csv(os.path.join(OUT_DIR, "VRN_GeometryRecon_CrossValidation.csv"), validation)
    write_csv(os.path.join(OUT_DIR, "VRN_GeometryRecon_Summary.csv"), [summary])
    with open(os.path.join(OUT_DIR, "VRN_GeometryRecon_AIO.json"), "w", encoding="utf-8") as f:
        json.dump({"Summary":summary,"SelfCheck":sc,"Files":files,
                   "DBReadyGreen":green,"Quarantine":quarantine,"CrossValidation":validation},
                  f, ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
