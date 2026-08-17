# -*- coding: utf-8 -*-
"""OneClick PS1 靜態結構驗證(沙盒無 pwsh:結構/契約檢查,runtime 於本機執行)。"""
from __future__ import annotations

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
        "VIA_SectorFlow_AdaptiveChainedIndex_v0100.py",
        "VIA_SectorFlow_SignalTradeBacktest_v0100.py",
        "VIA_LiveWire_ContractAdapter_v0100.py",
        "VIA_SectorFlow_Dashboard_Builder_v0100.py",
        "VIA_GroupIndex_MasterValidation_v0100.py",
        "test_VIA_VAP_AxisLock_v0100.py",
    ]:
        assert name in TEXT, name
        assert PS1.with_name(name).exists(), f"referenced file missing: {name}"


def test_ps1_gate_matrix_covers_four_runs() -> None:
    for token in [
        "RUN_SECTORFLOW_V0100", "RUN_SECTORFLOW_TRADE_V0100",
        "RUN_LIVEWIRE_ADAPTER_V0100", "RUN_MASTER_VALIDATION_V0100",
        "CONTROLLED_ACTIVATION_PASS", "TRADE_BACKTEST_PASS",
        "ADAPTER_VERIFIED_FAIL_CLOSED", "CONTROLLED_SUITE_ACTIVATION_PASS",
    ]:
        assert token in TEXT, token


def test_ps1_fail_closed_and_governance() -> None:
    assert "#requires -Version 7.0" in TEXT
    assert "Set-StrictMode -Version Latest" in TEXT
    assert TEXT.count("throw") >= 4                       # compile/unit/engine/gate 全 fail-closed
    assert "$LASTEXITCODE -ne 0" in TEXT
    assert "exit $exitCode" in TEXT
    for p in ["$PythonExe", "$SkipEngines", "$OpenHtml", "$KeepOpen"]:
        assert p in TEXT, p
