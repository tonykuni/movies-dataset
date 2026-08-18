# -*- coding: utf-8 -*-
"""
VERITAS INTELLIGENCE ANALYTICS
via_subgroup_sandbox_validation_v0100.py

SubGroup SSOT v0100 × 三清單引擎 v0201 沙盒驗證管線。

目的
----
1. 以 VIA_TW_SubGroup_SSOT_v0100.xlsx(20_成員名冊)作為新一代 membership 輸入,
   餵入 v0201 引擎的分析核心(controlled DGP → 動態 Criteria → 族群指數 → 熱力圖)。
2. 在無三清單 HTML 原始輸入的沙盒環境,完整重演
   TEST → DEBUG → OPTIMIZE → TEST → CONSOLIDATE → BACK-TEST → USER-TEST → ACTIVATE。
3. 治理不變項與 v0200 相同:無固定市場紅線、DISPLAY_ONLY 不進 COUNT、
   append-only 輸出、零網路、零下單、零來源改寫。

計數治理
--------
SSOT `計入族群指數` = Y            → CountingFlag COUNT
SSOT `計入族群指數` = N(避免重複計數) → CountingFlag DISPLAY_ONLY(一股多族群 SECONDARY)
SSOT `計入族群指數` = N(待歸類)      → CountingFlag DISPLAY_ONLY
SSOT `MethodA角色` LEADER/PEER/LAGGARD → Rank L/P/G(僅供 DGP 角色訊號;非活準則)
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

from pathlib import Path
from typing import Any, Dict, List
import argparse
import ast
import datetime as dt
import hashlib
import importlib.util
import json
import re
import sys

import numpy as np
import pandas as pd
import openpyxl

SCRIPT_DIR = Path(__file__).resolve().parent
ENGINE_PATH = SCRIPT_DIR / "VIA_ThreeList_Grouping_DynamicValidationPipeline_v0201.py"
DEFAULT_SSOT = SCRIPT_DIR.parent / "input" / "VIA_TW_SubGroup_SSOT_v0100.xlsx"
DEFAULT_OUT = SCRIPT_DIR.parent / "evidence" / "RUN_SUBGROUP_SANDBOX_V0100"
PLOT_OUT = SCRIPT_DIR.parent / "output" / "RUN_SUBGROUP_SANDBOX_V0100_plots"

VERSION = "0.1.00"
SANDBOX_SEEDS = [17, 20260817]
SANDBOX_SCENARIOS = ["ROTATION", "MARKET_TIDE"]
SANDBOX_OBSERVATIONS = 150

COUNT_MAP = {
    "Y": "COUNT",
    "N(避免重複計數)": "DISPLAY_ONLY",
    "N(待歸類)": "DISPLAY_ONLY",
}
ROLE_TOKEN_MAP = {"LEADER": "L", "PEER": "P", "LAGGARD": "G"}
MARKET_MAP = {"上市": "TWSE", "上櫃": "TPEX"}
SUFFIX_MAP = {"上市": ".TW", "上櫃": ".TWO"}


def load_engine():
    spec = importlib.util.spec_from_file_location("via_three_list_v0201", ENGINE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def def_extract_subgroup_ssot(path: Path) -> pd.DataFrame:
    wb = openpyxl.load_workbook(path, read_only=True)
    ws = wb["20_成員名冊"]
    rows = list(ws.iter_rows(values_only=True))
    header = list(rows[0])
    df = pd.DataFrame(rows[1:], columns=header)
    df = df[df["TW_TICKER"].notna()].copy()
    df["Ticker"] = df["TW_TICKER"].astype(str).str.strip()

    def map_role(value: object) -> str:
        s = str(value or "").upper()
        for token, rank in ROLE_TOKEN_MAP.items():
            if token in s:
                return rank
        return ""

    out = pd.DataFrame({
        "Group": df["L2"].astype(str).str.strip(),
        "Subgroup": df["L1"].astype(str).str.strip(),
        "Rank": df["MethodA角色(來源)"].map(map_role),
        "Ticker": df["Ticker"],
        "YFTicker": df["YFINANCE"].astype(str).str.strip(),
        "Name": df["個股"].astype(str).str.strip(),
        "MarketRaw": df["市場"].astype(str).str.strip(),
        "Market": df["市場"].map(MARKET_MAP),
        "Dimension": "D02_SUBGROUP_SSOT_V0100",
        "CountingFlag": df["計入族群指數"].map(COUNT_MAP).fillna("DISPLAY_ONLY"),
        "SourceID": "SUBGROUP_SSOT_V0100",
        "EvidenceStatus": "SSOT_ROSTER_ROW",
        "Attribution": df["歸屬"].astype(str).str.strip(),
        "Positioning": df["定位"].astype(str).str.strip(),
        "SourceMetricUse": "DISPLAY_ONLY_NOT_LIVE_CRITERIA",
    })
    out["MembershipKey"] = out["Dimension"] + "|" + out["Group"] + "|" + out["Ticker"]
    return out


def def_empty_dynamic(engine) -> pd.DataFrame:
    cols = ["Group", "Rank", "Ticker", "YFTicker", "Name", "Market", "CountingFlag"]
    return pd.DataFrame(columns=cols)


def def_audit_fixed_thresholds(engine_path: Path) -> List[Any]:
    tree = ast.parse(engine_path.read_text("utf-8"))
    prohibited = {0.85, 0.80, 0.60}
    findings: List[Any] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for item in [node.left, *node.comparators]:
                if isinstance(item, ast.Constant) and isinstance(item.value, (int, float)):
                    if float(item.value) in prohibited:
                        findings.append((node.lineno, item.value))
        if isinstance(node, ast.Call):
            name = ""
            if isinstance(node.func, ast.Attribute):
                name = node.func.attr.lower()
            elif isinstance(node.func, ast.Name):
                name = node.func.id.lower()
            if "quantile" in name:
                for arg in node.args:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, (int, float)) and float(arg.value) in prohibited:
                        findings.append((node.lineno, arg.value))
    return findings


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="VIA SubGroup SSOT sandbox validation")
    parser.add_argument("--ssot", type=Path, default=DEFAULT_SSOT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--no-plots", action="store_true")
    ns = parser.parse_args(argv)

    engine = load_engine()
    out_dir: Path = ns.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    tests: List[Dict[str, Any]] = []

    def add_test(tid: str, name: str, ok: bool, severity: str, evidence: str) -> None:
        tests.append({"TestID": tid, "TestName": name, "Status": "PASS" if ok else "FAIL", "Severity": severity, "Evidence": evidence})

    # ---------------- TEST-1 : SSOT extraction contracts ----------------
    roster = def_extract_subgroup_ssot(ns.ssot)
    add_test("S01", "SSOT 成員名冊列數契約", len(roster) == 378, "HARD", f"rows={len(roster)}")
    add_test("S02", "L2 次族群數契約", roster["Group"].nunique() == 77, "HARD", f"groups={roster['Group'].nunique()}")
    ticker_fullmatch = roster["Ticker"].str.fullmatch(r"\d{4}")
    invalid_tickers = int((~ticker_fullmatch).sum())
    add_test("S03", "四碼 ticker contract", bool(ticker_fullmatch.all()), "HARD", f"invalid={invalid_tickers}")
    suffix_expect = roster["Ticker"] + roster["MarketRaw"].map(SUFFIX_MAP)
    suffix_ok = roster["YFTicker"].eq(suffix_expect)
    add_test("S04", "YFinance suffix 與市場一致", bool(suffix_ok.all()), "HARD", f"conflicts={int((~suffix_ok).sum())}")
    counted = roster[roster["CountingFlag"] == "COUNT"]
    dup = int(counted.duplicated(["Dimension", "Group", "Ticker"]).sum())
    add_test("S05", "COUNT 列無重複計數", dup == 0, "HARD", f"duplicates={dup}")
    count_dist = roster["CountingFlag"].value_counts().to_dict()
    add_test("S06", "一股多族群 SECONDARY 均為 DISPLAY_ONLY", count_dist.get("COUNT", 0) == 298, "HARD", str(count_dist))

    # ---------------- DEBUG : AST audit(v0201 引擎無固定市場紅線) ----------------
    findings = def_audit_fixed_thresholds(ENGINE_PATH)
    add_test("S07", "v0201 executable AST 無固定市場門檻", len(findings) == 0, "HARD", f"findings={findings}")

    # ---------------- OPTIMIZE + BACK-TEST : 兩情境 × 兩種子 ----------------
    digests: Dict[str, List[str]] = {s: [] for s in SANDBOX_SCENARIOS}
    scenario_rows: List[Dict[str, Any]] = []
    main_analysis = None
    for scenario in SANDBOX_SCENARIOS:
        for seed in SANDBOX_SEEDS:
            panel = engine.def_generate_controlled_panel(
                roster, def_empty_dynamic(engine), seed, scenario, observations=SANDBOX_OBSERVATIONS,
            )
            analysis = engine.def_analyze_membership(
                roster, panel["prices"], panel["turnover"], panel["market_return"], seed,
            )
            ledger = analysis["criteria_ledger"]
            digest = hashlib.sha256(ledger.to_csv(index=False).encode("utf-8")).hexdigest()[:16]
            digests[scenario].append(digest)
            raw_returns = engine.def_safe_log_returns(panel["prices"])
            raw_meds = []
            for group, gm in roster[roster["CountingFlag"] == "COUNT"].groupby("Group"):
                tickers = [t for t in gm["YFTicker"] if t in raw_returns.columns]
                if len(tickers) < 2:
                    continue
                pair = engine.def_pairwise_values(raw_returns[tickers].corr())
                if pair.size:
                    raw_meds.append(float(np.nanmedian(pair)))
            scenario_rows.append({
                "Scenario": scenario,
                "Seed": seed,
                "CriteriaDigest": digest,
                "CriteriaRows": len(ledger),
                "FixedThresholdRows": int(ledger["MarketThresholdHardcoded"].sum()),
                "GroupsAnalyzed": len(analysis["group_summary"]),
                "MembersAnalyzed": len(analysis["member_metrics"]),
                "RawMedianWithinCorr": float(np.nanmedian(raw_meds)) if raw_meds else np.nan,
                "ResidualMedianWithinCorr": float(analysis["group_summary"]["WithinMedianCorr"].median()),
                "ValidGroups": int((analysis["group_summary"]["GroupValidity"] == "VALID_GROUP").sum()),
            })
            if scenario == "ROTATION" and seed == SANDBOX_SEEDS[-1]:
                main_analysis = analysis
                main_capacity, main_capacity_meta = engine.def_classify_trading_capacity(
                    panel["prices"], panel["turnover"], seed,
                )

    scen_df = pd.DataFrame(scenario_rows)
    add_test("S08", "動態 Criteria 全數非固定紅線", int(scen_df["FixedThresholdRows"].sum()) == 0, "HARD", scen_df[["Scenario", "Seed", "FixedThresholdRows"]].to_json(orient="records"))
    cross = len(set(digests["ROTATION"]) | set(digests["MARKET_TIDE"])) > 1
    add_test("S09", "動態 Criteria 跨情境/種子變動", bool(cross), "HARD", json.dumps(digests))
    tide = scen_df[scen_df["Scenario"] == "MARKET_TIDE"]
    tide_ok = bool((tide["RawMedianWithinCorr"] > tide["ResidualMedianWithinCorr"]).all())
    add_test("S10", "Market Tide 殘差化壓低假相關", tide_ok, "HARD", tide[["Seed", "RawMedianWithinCorr", "ResidualMedianWithinCorr"]].to_json(orient="records"))

    # ---------------- TEST-2 : 指數與角色覆蓋 ----------------
    assert main_analysis is not None
    eligible_groups = int((counted.groupby("Group")["YFTicker"].nunique() >= 1).sum())
    idx_groups = main_analysis["group_index_full"].shape[1]
    add_test("S11", "Full Index 覆蓋所有 COUNT 族群", idx_groups == eligible_groups, "HARD", f"index_groups={idx_groups} eligible={eligible_groups}")
    member_cov = main_analysis["member_metrics"]["YFTicker"].nunique()
    expected_cov = counted["YFTicker"].nunique()
    add_test("S12", "會員角色指標覆蓋", member_cov == expected_cov, "HARD", f"metrics={member_cov} expected={expected_cov}")
    roles = set(main_analysis["member_metrics"]["DynamicRole"].unique())
    add_test("S13", "DynamicRole 僅允許授權狀態", roles <= {"LEADER", "PEER", "TRUE_LAGGARD", "MEMBER", "MIXED_ROLE", "OUTLIER"}, "HARD", str(sorted(roles)))
    cap_cov = main_capacity["YFTicker"].nunique()
    add_test("S14", "交易容量動態分類覆蓋", cap_cov >= expected_cov, "HARD", f"capacity={cap_cov}")

    # ---------------- PLOTS(寫入 output 槽,不入版控) ----------------
    heatmap_count = 0
    if not ns.no_plots:
        PLOT_OUT.mkdir(parents=True, exist_ok=True)
        engine.def_plot_group_indices(main_analysis["group_index_full"], PLOT_OUT / "all_subgroup_indices_full.png", "VIA 77 SubGroup Full Equal-Weight Indices")
        engine.def_plot_group_indices(main_analysis["group_index_core"], PLOT_OUT / "all_subgroup_indices_core.png", "VIA 77 SubGroup Core Equal-Weight Indices")
        for group, corr in main_analysis["correlation_map"].items():
            p = PLOT_OUT / "heatmaps" / f"residual_corr_{engine.def_sanitize_filename(group)}.png"
            engine.def_plot_heatmap(corr, p, f"{group} · Residual Return Correlation")
            if p.exists():
                heatmap_count += 1
    plot_eligible = int((counted.groupby("Group")["YFTicker"].nunique() >= 2).sum())
    add_test("S15", "各族群 residual heatmap 生成", ns.no_plots or heatmap_count == plot_eligible, "HARD", f"heatmaps={heatmap_count} eligible={plot_eligible}")

    # ---------------- USER-TEST : 保留警告(fail-closed,不得自動消除) ----------------
    no_count_groups = sorted(set(roster["Group"]) - set(counted["Group"]))
    tests.append({
        "TestID": "S16",
        "TestName": "無 COUNT 成員之 L2 族群保留為 Review Warning",
        "Status": "WARN" if no_count_groups else "PASS",
        "Severity": "REVIEW",
        "Evidence": f"groups_without_count_members={no_count_groups}",
    })
    single_member_groups = sorted(counted.groupby("Group")["YFTicker"].nunique().loc[lambda s: s == 1].index)
    tests.append({
        "TestID": "S17",
        "TestName": "單一 COUNT 成員族群無法計算 within-corr(保留警告)",
        "Status": "WARN" if single_member_groups else "PASS",
        "Severity": "REVIEW",
        "Evidence": f"single_member_groups={single_member_groups}",
    })

    # ---------------- CONSOLIDATE : append-only evidence ----------------
    engine.def_write_csv(roster, out_dir / "subgroup_membership_input.csv")
    engine.def_write_csv(scen_df, out_dir / "sandbox_scenario_summary.csv")
    engine.def_write_csv(main_analysis["group_summary"], out_dir / "subgroup_validity_summary.csv")
    engine.def_write_csv(main_analysis["member_metrics"], out_dir / "subgroup_member_role_metrics.csv")
    engine.def_write_csv(pd.concat([main_analysis["criteria_ledger"], main_capacity_meta], ignore_index=True), out_dir / "dynamic_criteria_ledger.csv")
    engine.def_write_csv(main_capacity, out_dir / "trading_capacity_latest.csv")
    engine.def_write_csv(main_analysis["group_index_full"].reset_index(names="Date"), out_dir / "subgroup_index_full_daily.csv")
    engine.def_write_csv(main_analysis["group_index_core"].reset_index(names="Date"), out_dir / "subgroup_index_core_daily.csv")

    # ---------------- ACTIVATE : fail-closed gate ----------------
    test_df = pd.DataFrame(tests)
    hard_fail = int(((test_df["Status"] == "FAIL") & (test_df["Severity"] == "HARD")).sum())
    review_warn = int((test_df["Status"] == "WARN").sum())
    if hard_fail == 0:
        status = "SANDBOX_VALIDATION_PASS_REVIEW_WARNINGS_RETAINED" if review_warn else "SANDBOX_VALIDATION_PASS"
    else:
        status = "SANDBOX_VALIDATION_BLOCKED"
    summary = {
        "Harness": "via_subgroup_sandbox_validation",
        "Version": VERSION,
        "Engine": str(ENGINE_PATH.name),
        "GeneratedAt": dt.datetime.now().isoformat(timespec="seconds"),
        "PythonVersion": sys.version.split()[0],
        "SSOTFile": ns.ssot.name,
        "SSOTSHA256": engine.def_sha256(ns.ssot),
        "RosterRows": int(len(roster)),
        "SubGroups": int(roster["Group"].nunique()),
        "CountRows": int(len(counted)),
        "DisplayOnlyRows": int((roster["CountingFlag"] == "DISPLAY_ONLY").sum()),
        "Scenarios": SANDBOX_SCENARIOS,
        "Seeds": SANDBOX_SEEDS,
        "Observations": SANDBOX_OBSERVATIONS,
        "HardFailures": hard_fail,
        "ReviewWarnings": review_warn,
        "GroupsWithoutCountMembers": no_count_groups,
        "SingleCountMemberGroups": single_member_groups,
        "HeatmapsRendered": heatmap_count,
        "Status": status,
        "Policy": "research-only / append-only / fail-closed / no-network / no-order / DGP-not-live-market",
    }
    engine.def_write_csv(test_df, out_dir / "sandbox_test_ledger.csv")
    engine.def_write_json(summary, out_dir / "sandbox_run_summary.json")

    manifest = {
        str(p.relative_to(out_dir)): engine.def_sha256(p)
        for p in sorted(out_dir.rglob("*"))
        if p.is_file() and p.name != "SHA256_MANIFEST.json"
    }
    engine.def_write_json(manifest, out_dir / "SHA256_MANIFEST.json")

    print("=" * 88)
    print(f"VIA SubGroup Sandbox Validation v{VERSION}")
    print("Status      :", status)
    print("Hard Fail   :", hard_fail)
    print("Review Warn :", review_warn)
    print("Roster      :", len(roster), "rows /", roster["Group"].nunique(), "L2 subgroups")
    print("Heatmaps    :", heatmap_count)
    print("Evidence    :", out_dir)
    print("=" * 88)
    for t in tests:
        print(f"  [{t['Status']}] {t['TestID']} {t['TestName']} :: {t['Evidence'][:100]}")
    return 0 if hard_fail == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
