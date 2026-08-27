# -*- coding: utf-8 -*-
"""環境前哨檢查測試:分類邏輯 / 工具檢核 / 白名單缺口 / fail-closed 語意。"""
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

import json

import VIA_GroupIndex_EnvPreflight_v0100 as pf


def test_detect_env_classification_contract() -> None:
    env = pf.def_detect_env()
    assert env["Classification"] in {
        "VIA_MANAGED", "BASE_OR_SYSTEM_POLLUTION_RISK", "UNMANAGED_FOREIGN_ENV",
    }
    # 沙盒/CI 為系統 Python:必須誠實標記為污染風險,不得偽裝為 via_ 管理環境
    if not env["IsManagedVia"]:
        assert env["Classification"] != "VIA_MANAGED"
    assert env["PythonExe"]
    assert env["PythonVersion"].count(".") >= 1


def test_required_tools_all_importable() -> None:
    rows = pf.def_check_tools()
    assert {r["Import"] for r in rows} == set(pf.REQUIRED_TOOLS)
    missing = [r["PipName"] for r in rows if not r["Installed"]]
    assert missing == [], f"GroupIndex 缺件: {missing}"
    for r in rows:
        assert r["Version"], r["Import"]


def test_whitelist_gap_matches_envmanager_contract() -> None:
    wl = pf.def_whitelist_gap()
    gap = set(wl["ViaCoreWhitelistGap"])
    # via_core 白名單已涵蓋 numpy/pandas/openpyxl;GroupIndex 額外需求即為缺口
    assert gap == {"scikit-learn", "matplotlib", "seaborn", "beautifulsoup4", "pytest"}
    assert "OPTION_A" in wl["Recommendation"] and "OPTION_B" in wl["Recommendation"]
    assert "via_groupindex_312" in wl["Recommendation"]


def test_report_only_never_hard_fails_and_writes_report() -> None:
    report = pf.def_run_preflight(enforce=False)
    assert report["HardFailures"] == 0
    assert report["Mode"] == "REPORT_ONLY"
    assert report["Status"] in {"ENV_PREFLIGHT_PASS", "ENV_PREFLIGHT_REPORT_ONLY_NONCOMPLIANT"}
    on_disk = json.loads((pf.RUN_OUT / "env_preflight_report.json").read_text("utf-8"))
    assert on_disk["Status"] == report["Status"]
    assert on_disk["Policy"].startswith("scan-classify-recommend only")


def test_enforce_blocks_outside_via_env() -> None:
    report = pf.def_run_preflight(enforce=True)
    env_ok = report["CurrentEnv"]["IsManagedVia"]
    if env_ok and not report["MissingTools"]:
        assert report["Status"] == "ENV_PREFLIGHT_PASS" and report["HardFailures"] == 0
    else:
        assert report["Status"] == "ENV_PREFLIGHT_BLOCKED" and report["HardFailures"] >= 1
    # 治理不變項:enforce 亦不得產生任何安裝/改寫行為,僅建議命令字串
    assert report["Policy"].startswith("scan-classify-recommend only")
