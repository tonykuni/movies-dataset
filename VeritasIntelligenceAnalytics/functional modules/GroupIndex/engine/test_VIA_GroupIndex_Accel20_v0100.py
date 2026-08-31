# -*- coding: utf-8 -*-
"""Accel20 治理主控台契約測試:20 加速器齊備、HARD 零、KEY PROMPT 存檔、非阻塞啟動器。"""
from __future__ import annotations

from pathlib import Path
import json

import VIA_GroupIndex_Accel20_Console_v0100 as ac

ENGINE_DIR = Path(__file__).resolve().parent
RUN = ENGINE_DIR.parent / "evidence" / "RUN_ACCEL20_V0100"


def test_key_prompt_saved_verbatim_sections() -> None:
    key = (ENGINE_DIR.parent.parent.parent / "supportive modules" / "VIA_Central_Governance" /
           "VIA_CentralGovernanceConsole_MegaPrompt_KEY.md").read_text("utf-8")
    for token in ["20 個加速器", "Zero-Hydra Risk", "Parallel-Fixable", "Sequence-Dependent",
                  "六個獨立流程", "launch.ps1", "MODULE", "FUNCTION-LIB",
                  "activate system → test → debug → until perfect"]:
        assert token in key, token


def test_all_twenty_accelerators_mounted() -> None:
    summary = json.loads((RUN / "accel20_summary.json").read_text("utf-8"))
    acc = summary["Accelerators"]
    assert len([k for k in acc if k.startswith("A")]) == 20
    assert summary["Status"] == "ACCEL20_GOVERNANCE_PASS"
    assert summary["HardFailures"] == 0
    assert summary["Rounds"] <= 3                    # 三輪全景上限
    assert acc["A01_AST"]["parsedOK"] == acc["A01_AST"]["total"]


def test_console_scans_all_python_engines() -> None:
    targets = ac.def_collect_py_targets()
    names = {t.name for t in targets}
    # 所有 PY 引擎都要裝加速器:五大引擎 + LiveData 消費台 + 套件模組 + canonical GovFund
    for must in ["VIA_SectorFlow_AdaptiveChainedIndex_v0100.py", "VIA_GlobalETFFlow.py",
                 "VIA_ActiveStockETF.py", "VIA_ChipWar_Console_v010.py",
                 "VIA_GovFundEngine_v040.py", "cli.py",
                 "VIA_TW_Branch_Capital_Circle_Engine.py", "forward_valuation_vintage_v2.py"]:
        assert must in names, must
    assert len(targets) >= 45


def test_matrix_html_four_zones_and_ryg() -> None:
    html = (RUN / "accel20_matrix.html").read_text("utf-8")
    for token in ["MODULE", "ENGINE", "FUNCTION-LIB", "動態進度條", "Narration",
                  "Hydra 風險矩陣", "SSOT 對照矩陣", "word-break:break-word"]:
        assert token in html, token


def test_nonblocking_launcher_contract() -> None:
    text = (ENGINE_DIR / "launch.ps1").read_text("utf-8")
    assert "Start-Process" in text and "-PassThru" in text
    assert "RedirectStandardOutput" in text
    assert "-KeepOpen 0" in text                     # 背景模式不等待 Enter(不卡斷)
    assert '-File "{0}"' in text                     # 含空白路徑必須顯式引號(Start-Process 不自動引)
    assert "-NoProfile" in text                      # 子行程隔離使用者 profile
    assert "Get-Content" in text                     # log 追蹤指引
