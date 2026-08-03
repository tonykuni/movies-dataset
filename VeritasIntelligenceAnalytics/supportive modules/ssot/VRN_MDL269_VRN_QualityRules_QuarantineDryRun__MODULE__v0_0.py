# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path
from typing import Dict, Any, List

P_RULE_MODULE = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIS_VRN_BasicInfoFinancialQualityRules_v0100.py"
P_FINANCIALDATA_CSV = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\_vrn_basicinfo_financial_matrix_runs\RUN_20260531_085452\VRN_FinancialData_Matrix.csv"
P_BASICINFO_CSV = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\_vrn_basicinfo_financial_matrix_runs\RUN_20260531_085452\VRN_BasicInfo_Matrix.csv"
P_OUT_DIR = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\_vrn_quality_rules_sync3_preview_runs\RUN_20260531_095804"


def def_load_module(path: str):
    spec = importlib.util.spec_from_file_location("vrn_quality_rules", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load rule module")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def def_read_csv(path: str) -> List[Dict[str, Any]]:
    if not Path(path).exists():
        return []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def def_write_csv(path: str, rows: List[Dict[str, Any]]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        rows = [{"Light": "⚪", "Status": "EMPTY", "Note": "No rows"}]
    fields = []
    for r in rows:
        for k in r.keys():
            if k not in fields:
                fields.append(k)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def def_norm_row_keys(row: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(row)
    mapping = {
        "SourceFile": ["SourceFile", "Source File", "source_file"],
        "Ticker": ["Ticker", "ticker", "YFinance Ticker"],
        "AccountRaw": ["AccountRaw", "Account Raw"],
        "ValueRaw": ["ValueRaw", "Value Raw"],
        "PeriodNormalized": ["PeriodNormalized", "Period Normalized"],
    }
    for k, aliases in mapping.items():
        if k not in out or not str(out.get(k, "")).strip():
            for a in aliases:
                if a in row and str(row.get(a, "")).strip():
                    out[k] = row.get(a)
                    break
    return out


def def_light(risk: str) -> str:
    if risk == "HIGH":
        return "🔴"
    if risk == "YELLOW":
        return "🟡"
    return "🟢"


def def_main() -> None:
    mod = def_load_module(P_RULE_MODULE)
    out_dir = Path(P_OUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    financial_rows = def_read_csv(P_FINANCIALDATA_CSV)
    basic_rows = def_read_csv(P_BASICINFO_CSV)

    quarantine = []
    keep = []
    rescue = []

    for row in financial_rows:
        rr = def_norm_row_keys(row)
        q = mod.def_classify_financial_row_quality_v0100(rr)
        risk = q.get("row_quality_risk", "GREEN")
        action = q.get("row_quality_action", "KEEP_AS_FINANCIAL_OBSERVATION")
        merged = dict(rr)
        merged.update(q)
        merged["Light"] = def_light(risk)
        merged["DryRunMutation"] = False
        merged["DryRunDbWrite"] = False

        if action in {"QUARANTINE", "REQUIRES_TABLE_GEOMETRY_SPLIT"}:
            quarantine.append(merged)
        else:
            keep.append(merged)

    for row in basic_rows:
        rescued = mod.def_rescue_basicinfo_from_source_v0100(dict(row))
        risk = "GREEN" if rescued.get("BasicInfoRescueStatus") == "PASS" else "YELLOW"
        rescued["Light"] = def_light(risk)
        rescued["DryRunMutation"] = False
        rescued["DryRunDbWrite"] = False
        rescue.append(rescued)

    def_write_csv(str(out_dir / "VRN_QualityRules_Quarantine_DryRun.csv"), quarantine)
    def_write_csv(str(out_dir / "VRN_QualityRules_Keep_DryRun.csv"), keep)
    def_write_csv(str(out_dir / "VRN_BasicInfo_Rescue_DryRun.csv"), rescue)

    summary = {
        "hard_pass": True,
        "financial_input_rows": len(financial_rows),
        "quarantine_rows": len(quarantine),
        "keep_rows": len(keep),
        "basicinfo_input_rows": len(basic_rows),
        "basicinfo_rescue_rows": len(rescue),
        "mutation": False,
        "db_write": False,
        "outputs": {
            "quarantine": str(out_dir / "VRN_QualityRules_Quarantine_DryRun.csv"),
            "keep": str(out_dir / "VRN_QualityRules_Keep_DryRun.csv"),
            "basicinfo_rescue": str(out_dir / "VRN_BasicInfo_Rescue_DryRun.csv"),
        },
    }

    with open(out_dir / "VRN_QualityRules_DryRun_Summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    def_main()
