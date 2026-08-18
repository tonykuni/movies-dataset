# -*- coding: utf-8 -*-
"""OneClick PS1 靜態結構驗證(沙盒無 pwsh:結構/契約檢查,runtime 於本機執行)。"""
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
import re

PS1 = Path(__file__).with_name("Invoke-VIA-GroupIndex-Suite-OneClick-v0100.ps1")
TEXT = PS1.read_text("utf-8")


def strip_ps_literals(text: str) -> str:
    text = re.sub(r"<#.*?#>", "", text, flags=re.S)          # block comments
    text = re.sub(r'"(?:`.|[^"`])*"', '""', text)            # double-quoted strings
    text = re.sub(r"'[^']*'", "''", text)                    # single-quoted strings
    text = re.sub(r"(?m)#.*$", "", text)                     # line comments
    return text


def test_ps1_balanced_delimiters() -> None:
    body = strip_ps_literals(TEXT)
    for open_ch, close_ch in [("{", "}"), ("(", ")"), ("[", "]")]:
        assert body.count(open_ch) == body.count(close_ch), f"unbalanced {open_ch}{close_ch}"


def test_ps1_references_all_engines_and_tests() -> None:
    for name in [
        "VIA_GroupIndex_EnvPreflight_v0100.py",
        "test_VIA_GroupIndex_EnvPreflight_v0100.py",
        "VIA_SectorFlow_AdaptiveChainedIndex_v0100.py",
        "VIA_SectorFlow_SignalTradeBacktest_v0100.py",
        "VIA_LiveWire_ContractAdapter_v0100.py",
        "VIA_SectorFlow_Dashboard_Builder_v0100.py",
        "VIA_GroupIndex_MasterValidation_v0100.py",
        "VIA_ActiveStockETF.py",
        "VIA_ActiveStockETF_mocktest.py",
        "VIA_GlobalETFFlow.py",
        "VIA_ETF_Consoles_Evidence_v0100.py",
        "VIA_FinMind_Ingest_v010.py",
        "VIA_SectorWhaleEngine_v020.py",
        "VIA_GovFundEngine_v040.py",
        "VIA_ChipWar_Console_v010.py",
        "VIA_ChipWar_Revenue_Evidence_v0100.py",
        "test_VIA_VAP_AxisLock_v0100.py",
        "test_VIA_ETF_Consoles_v0100.py",
        "test_VIA_ChipWar_Revenue_v0100.py",
    ]:
        assert name in TEXT, name
        assert PS1.with_name(name).exists(), f"referenced file missing: {name}"


def test_ps1_gate_matrix_covers_four_runs() -> None:
    for token in [
        "RUN_SECTORFLOW_V0100", "RUN_SECTORFLOW_TRADE_V0100",
        "RUN_LIVEWIRE_ADAPTER_V0100", "RUN_ETF_CONSOLES_V0100",
        "RUN_CHIPWAR_REVENUE_V0100", "RUN_MASTER_VALIDATION_V0100",
        "CONTROLLED_ACTIVATION_PASS", "TRADE_BACKTEST_PASS",
        "ADAPTER_VERIFIED_FAIL_CLOSED", "ETF_CONSOLES_PASS",
        "CHIPWAR_REVENUE_PASS", "CONTROLLED_SUITE_ACTIVATION_PASS",
    ]:
        assert token in TEXT, token


def test_ps1_fail_closed_and_governance() -> None:
    assert "#requires -Version 7.0" in TEXT
    assert "Set-StrictMode -Version Latest" in TEXT
    assert TEXT.count("throw") >= 4                       # compile/unit/engine/gate 全 fail-closed
    assert "$LASTEXITCODE -ne 0" in TEXT
    assert "exit $exitCode" in TEXT
    for p in ["$PythonExe", "$EnforceEnv", "$SyncRepo", "$ResetEvidence", "$SetupSmoke",
              "$SkipEngines", "$OpenHtml", "$KeepOpen"]:
        assert p in TEXT, p


def test_ps1_sync_hash_smoke_segments_contract() -> None:
    # [S1] GIT-SYNC:evidence 還原 + 分支同步 + launcher 自我更新重執行
    assert "def_SyncRepo" in TEXT
    assert "claude/via-group-classification-index-5h274b" in TEXT
    assert "git -C $RepoRoot restore" in TEXT
    assert "VIA_ONECLICK_RESYNCED" in TEXT
    # [S2] HASH-AUDIT:git 乾淨度 + SHA-256 列印
    assert "def_HashAudit" in TEXT
    assert "status --porcelain" in TEXT
    assert "Get-FileHash" in TEXT
    # [S3] SMOKE-TOOLING:playwright-core 只裝進 smoke_tooling
    assert "def_SmokeTooling" in TEXT
    assert "smoke_tooling" in TEXT
    assert "playwright-core" in TEXT


def test_ps1_env_preflight_segment_contract() -> None:
    # [0] ENV-PREFLIGHT:via_ python 自動解析 + EnvManager 契約 enforce
    assert "def_ResolveViaPython" in TEXT
    for candidate in ["via_groupindex_312", "via_core_313", "via_core_312"]:
        assert candidate in TEXT, candidate
    assert "--enforce" in TEXT
    assert "ENV-PREFLIGHT" in TEXT
