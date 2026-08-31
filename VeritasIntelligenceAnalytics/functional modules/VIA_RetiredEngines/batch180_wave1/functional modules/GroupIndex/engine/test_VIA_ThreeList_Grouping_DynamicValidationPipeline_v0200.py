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

import pandas as pd

MODULE_PATH = Path(__file__).with_name("VIA_ThreeList_Grouping_DynamicValidationPipeline_v0200.py")
SPEC = importlib.util.spec_from_file_location("via_three_list_v0200", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def locate_run_dir() -> Path:
    base = Path(__file__).resolve().parent
    candidates = [
        base / "RUN_FINAL_V0200",
        base / "runs" / "RUN_FINAL_V0200",
        base / "evidence" / "RUN_FINAL_V0200",
    ]
    for candidate in candidates:
        if (candidate / "run_summary.json").exists():
            return candidate
    raise AssertionError(f"RUN_FINAL_V0200 not found under {base}")


def test_source_extraction_contracts() -> None:
    source_a, _ = MODULE.def_extract_source_a(MODULE.DEFAULT_SOURCE_A)
    controls, meta = MODULE.def_extract_source_b(MODULE.DEFAULT_SOURCE_B)
    source_c = MODULE.def_extract_source_c(MODULE.DEFAULT_SOURCE_C)
    assert len(source_a) == 238
    assert source_a["Group"].nunique() == 39
    assert source_a["Ticker"].nunique() == 238
    assert source_a["Ticker"].astype(str).str.fullmatch(r"\d{4}").all()
    assert meta["ControlRole"] == "SCOPE_AND_GOVERNANCE_ONLY"
    assert len(controls) == 4
    assert source_c["GroupDynamic"].nunique() == 3
    assert len(source_c) == 27


def test_counting_governance() -> None:
    source_a, _ = MODULE.def_extract_source_a(MODULE.DEFAULT_SOURCE_A)
    source_c = MODULE.def_extract_source_c(MODULE.DEFAULT_SOURCE_C)
    rec = MODULE.def_reconcile_dynamic_identity(source_a, source_c)
    canonical = MODULE.def_build_canonical_input(source_a)
    dynamic = MODULE.def_build_dynamic_input(rec)
    assert set(canonical["CountingFlag"]) == {"COUNT"}
    assert set(dynamic["CountingFlag"]) == {"DISPLAY_ONLY"}
    combined = pd.concat([canonical, dynamic], ignore_index=True)
    counted = combined[combined["CountingFlag"] == "COUNT"]
    assert counted.duplicated(["Dimension", "Group", "Ticker"]).sum() == 0


def test_dynamic_criteria_adapt_across_regimes() -> None:
    source_a, _ = MODULE.def_extract_source_a(MODULE.DEFAULT_SOURCE_A)
    source_c = MODULE.def_extract_source_c(MODULE.DEFAULT_SOURCE_C)
    rec = MODULE.def_reconcile_dynamic_identity(source_a, source_c)
    canonical = MODULE.def_build_canonical_input(source_a)
    dynamic = MODULE.def_build_dynamic_input(rec)
    digests = []
    for scenario in ["ROTATION", "MARKET_TIDE"]:
        panel = MODULE.def_generate_controlled_panel(canonical, dynamic, 17, scenario, observations=120)
        result = MODULE.def_analyze_membership(
            canonical,
            panel["prices"],
            panel["turnover"],
            panel["market_return"],
            17,
        )
        ledger = result["criteria_ledger"]
        assert not ledger.empty
        assert not ledger["MarketThresholdHardcoded"].any()
        digests.append(ledger.to_csv(index=False))
    assert digests[0] != digests[1]


def test_final_run_outputs_and_activation() -> None:
    run_dir = locate_run_dir()
    summary = json.loads((run_dir / "run_summary.json").read_text("utf-8"))
    activation = json.loads((run_dir / "activation_status.json").read_text("utf-8"))
    tests = pd.read_csv(run_dir / "test_validation_ledger.csv")
    user = pd.read_csv(run_dir / "user_test_ledger.csv")
    phases = pd.read_csv(run_dir / "pipeline_phase_ledger.csv")
    assert summary["HardFailures"] == 0
    assert phases.loc[phases["Phase"] == "TEST-2", "Status"].iloc[0] == "PASS"
    assert "manifest_mode=immutable_postcheck" in summary["FinalPhase"]["Detail"]
    assert summary["ManifestVerified"] is True
    assert activation["Status"].startswith("CONTROLLED_ACTIVATION_PASS")
    assert activation["CanonicalMutation"] == 0
    assert activation["NetworkExecution"] == 0
    assert activation["OrderExecution"] == 0
    assert not ((tests["Status"] == "FAIL") & (tests["Severity"] == "HARD")).any()
    assert not (user["Status"] == "FAIL").any()


def test_manifest_and_html_assets() -> None:
    run_dir = locate_run_dir()
    manifest = json.loads((run_dir / "SHA256_MANIFEST.json").read_text("utf-8"))
    assert len(manifest) > 40
    for rel, expected in manifest.items():
        path = run_dir / rel
        assert path.exists(), rel
        assert MODULE.def_sha256(path) == expected, rel
    html_ok, missing = MODULE.def_validate_html_assets(run_dir / "index.html")
    assert html_ok, missing


def test_backtest_has_all_scenarios_and_dynamic_digests() -> None:
    run_dir = locate_run_dir()
    summary = pd.read_csv(run_dir / "backtest_summary.csv")
    assert set(summary["Scenario"]) == set(MODULE.CONTROLLED_SCENARIOS)
    assert (summary["Seeds"] == len(MODULE.CONTROLLED_SEEDS)).all()
    assert (summary["UniqueCriteriaDigests"] > 1).all()
    market_tide = summary[summary["Scenario"] == "MARKET_TIDE"].iloc[0]
    assert market_tide["RawMedianWithinCorrMedian"] > market_tide["ResidualMedianWithinCorrMedian"]


def test_no_prohibited_fixed_market_thresholds_in_executable_ast() -> None:
    tree = ast.parse(MODULE_PATH.read_text("utf-8"))
    prohibited = {0.85, 0.80, 0.60}
    findings = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            operands = [node.left, *node.comparators]
            for item in operands:
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
