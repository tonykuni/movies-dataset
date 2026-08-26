# -*- coding: utf-8 -*-
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
import ast
import importlib.util
import json
import sys

import numpy as np
import pandas as pd

MODULE_PATH = Path(__file__).with_name("GRP_ENG012_SectorFlowAdaptiveChainedIndex_v0100.py")
SPEC = importlib.util.spec_from_file_location("via_sectorflow_v0100", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)

RUN_DIR = MODULE.DEFAULT_OUT_DIR / MODULE.DEFAULT_RUN_TAG


def test_membership_contract() -> None:
    membership = MODULE.def_extract_sector_membership(MODULE.DEFAULT_SSOT)
    assert membership["Group"].nunique() == 14
    assert len(membership) == 378
    counted = membership[membership["CountingFlag"] == "COUNT"]
    assert len(counted) == 298
    assert membership["Ticker"].astype(str).str.fullmatch(r"\d{4}").all()
    assert counted.duplicated(["Group", "Ticker"]).sum() == 0


def test_cleaning_quarantines_non_common_and_strips_daytrade() -> None:
    membership = MODULE.def_extract_sector_membership(MODULE.DEFAULT_SSOT)
    bundle = MODULE.def_generate_sector_panel(membership, 17, "ROTATION")
    clean, quarantined = MODULE.def_clean_universe(bundle["panel"])
    assert quarantined["Ticker"].nunique() == len(MODULE.EXCLUDED_SYNTHETIC_INSTRUMENTS)
    assert clean["Ticker"].str.fullmatch(r"\d{4}").all()
    assert (clean["RealTurnover"] >= 0).all()
    assert (clean["RealTurnover"] <= clean["Turnover"] + 1e-6).all()
    # 分母必須已剔除台積電。
    assert (clean["AdjustedMarketRealTurnover"] < clean["MarketRealTotal"]).all()


def test_chained_index_continuity_and_base() -> None:
    chained = pd.read_csv(RUN_DIR / "sector_chained_index_daily.csv", parse_dates=["Date"])
    base_ts = pd.Timestamp(MODULE.INDEX_BASE_DATE)
    plot_ts = pd.Timestamp(MODULE.INDEX_PLOT_START)
    assert chained["Date"].min() >= plot_ts
    assert chained["Date"].min() < base_ts  # 基期前歷史確實存在(反推段)
    for group, g in chained.groupby("Group"):
        g = g.sort_values("Date")
        idx = g["ChainedIndex"].to_numpy(dtype=float)
        rets = g["BasketRet"].to_numpy(dtype=float)
        # 錨定:基期日點位 = 100(基期前為幾何反推,基期後為正推)。
        at_base = g[g["Date"] == base_ts]
        assert len(at_base) == 1, group
        assert abs(float(at_base["ChainedIndex"].iloc[0]) - MODULE.INDEX_BASE_VALUE) < 1e-6, group
        recon = idx[:-1] * (1.0 + rets[1:])
        assert np.max(np.abs(idx[1:] - recon)) < 1e-6, group
        # 換檔至少發生一次且未造成任何點位斷裂(上式已涵蓋)。
        assert g["PeriodID"].nunique() >= 2, group


def test_dynamic_criteria_adapt_across_scenarios() -> None:
    backtest = pd.read_csv(RUN_DIR / "backtest_summary.csv")
    assert set(backtest["Scenario"]) == set(MODULE.CONTROLLED_SCENARIOS)
    assert backtest["CriteriaDigest"].nunique() > 1
    criteria = pd.read_csv(RUN_DIR / "dynamic_criteria_ledger.csv")
    assert not criteria["MarketThresholdHardcoded"].any()


def test_market_tide_residual_control() -> None:
    backtest = pd.read_csv(RUN_DIR / "backtest_summary.csv")
    tide = backtest[backtest["Scenario"] == "MARKET_TIDE"]
    assert (tide["RawMedianWithinCorr"] > tide["ResidualMedianWithinCorr"]).all()
    assert (backtest["OrthoPureAbsCorr"] < backtest["OrthoRawAbsCorr"]).all()


def test_final_run_gate_and_activation() -> None:
    summary = json.loads((RUN_DIR / "run_summary.json").read_text("utf-8"))
    activation = json.loads((RUN_DIR / "activation_status.json").read_text("utf-8"))
    tests = pd.read_csv(RUN_DIR / "test_validation_ledger.csv")
    phases = pd.read_csv(RUN_DIR / "pipeline_phase_ledger.csv")
    assert summary["HardFailures"] == 0
    assert summary["ManifestVerified"] is True
    assert activation["Status"].startswith("CONTROLLED_ACTIVATION_PASS")
    assert activation["NetworkExecution"] == 0
    assert activation["OrderExecution"] == 0
    assert not ((tests["Status"] == "FAIL") & (tests["Severity"] == "HARD")).any()
    for phase in ["TEST-1", "DEBUG-1", "OPTIMIZE-1", "TEST-2", "DEBUG-2", "BACK-TEST",
                  "DEBUG-3", "CONSOLIDATE", "TEST-3", "DEBUG-4", "ACTIVATE", "FINAL-TEST"]:
        assert phase in set(phases["Phase"]), phase
        assert phases.loc[phases["Phase"] == phase, "Status"].iloc[-1] in {"PASS", "BLOCKED"}, phase
    assert phases.loc[phases["Phase"] == "FINAL-TEST", "Status"].iloc[-1] == "PASS"


def test_manifest_integrity() -> None:
    manifest = json.loads((RUN_DIR / "SHA256_MANIFEST.json").read_text("utf-8"))
    assert len(manifest) > 10
    for rel, expected in manifest.items():
        path = RUN_DIR / rel
        assert path.exists(), rel
        assert MODULE.def_sha256(path) == expected, rel


def test_no_prohibited_fixed_market_thresholds_in_executable_ast() -> None:
    tree = ast.parse(MODULE_PATH.read_text("utf-8"))
    prohibited = {0.85, 0.80, 0.60}
    findings = []
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
    assert findings == []


def test_lookahead_free_review_replay() -> None:
    flows = pd.read_csv(RUN_DIR / "sector_flow_daily.csv")
    reviews = pd.read_csv(RUN_DIR / "review_roles.csv", parse_dates=["ReviewDate"])
    assert not reviews.empty
    # 每次定審均只能使用 ReviewDate(含)之前的資料 —— 由引擎 F21 稽核背書;
    # 此處驗證輸出結構:每期都有角色、允許的角色標籤集合。
    assert set(reviews["Role"].unique()) <= {"LEADER", "PEER", "LAGGARD", "MEMBER", "FALLBACK_ALL"}
    assert reviews["PeriodID"].nunique() >= 2
    assert set(flows["StrategySignal"].unique()) <= {"DYNAMIC_BUY", "DYNAMIC_SETUP", "DYNAMIC_EXIT", "HOLD"}
