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
import hashlib
import json

import pandas as pd

ENGINE_PATH = Path(__file__).with_name("VIA_ThreeList_Grouping_DynamicValidationPipeline_v0201.py")
RUN_DIR = Path(__file__).resolve().parent.parent / "evidence" / "RUN_SUBGROUP_SANDBOX_V0100"


def def_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def test_engine_v0201_compiles_on_this_python() -> None:
    # v0200 could not compile below Python 3.12 (f-string backslash); v0201 must.
    compile(ENGINE_PATH.read_text("utf-8"), str(ENGINE_PATH), "exec")


def test_no_prohibited_fixed_market_thresholds_in_v0201_ast() -> None:
    tree = ast.parse(ENGINE_PATH.read_text("utf-8"))
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


def test_sandbox_run_summary_gate() -> None:
    summary = json.loads((RUN_DIR / "sandbox_run_summary.json").read_text("utf-8"))
    assert summary["Status"].startswith("SANDBOX_VALIDATION_PASS")
    assert summary["HardFailures"] == 0
    assert summary["RosterRows"] == 378
    assert summary["SubGroups"] == 77
    assert summary["CountRows"] == 298


def test_sandbox_test_ledger_no_hard_failures() -> None:
    ledger = pd.read_csv(RUN_DIR / "sandbox_test_ledger.csv")
    assert not ((ledger["Status"] == "FAIL") & (ledger["Severity"] == "HARD")).any()
    # review warnings must be retained, never silently dropped
    warn_rows = ledger[ledger["Severity"] == "REVIEW"]
    assert len(warn_rows) >= 1


def test_counting_governance_in_membership_input() -> None:
    roster = pd.read_csv(RUN_DIR / "subgroup_membership_input.csv", dtype={"Ticker": str})
    assert set(roster["CountingFlag"]) == {"COUNT", "DISPLAY_ONLY"}
    counted = roster[roster["CountingFlag"] == "COUNT"]
    assert counted.duplicated(["Dimension", "Group", "Ticker"]).sum() == 0
    assert roster["Ticker"].str.fullmatch(r"\d{4}").all()


def test_dynamic_criteria_adapt_and_no_fixed_thresholds() -> None:
    scen = pd.read_csv(RUN_DIR / "sandbox_scenario_summary.csv")
    assert set(scen["Scenario"]) == {"ROTATION", "MARKET_TIDE"}
    assert (scen["FixedThresholdRows"] == 0).all()
    assert scen["CriteriaDigest"].nunique() > 1
    tide = scen[scen["Scenario"] == "MARKET_TIDE"]
    assert (tide["RawMedianWithinCorr"] > tide["ResidualMedianWithinCorr"]).all()


def test_evidence_manifest_verifies() -> None:
    manifest = json.loads((RUN_DIR / "SHA256_MANIFEST.json").read_text("utf-8"))
    assert len(manifest) >= 8
    for rel, expected in manifest.items():
        path = RUN_DIR / rel
        assert path.exists(), rel
        assert def_sha256(path) == expected, rel
