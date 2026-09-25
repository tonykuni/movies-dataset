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
import importlib.util
import json
import sys

import numpy as np
import pandas as pd

MODULE_PATH = Path(__file__).with_name("GRP_ENG014_SectorFlowSignalTradeBacktest_v0100.py")
SPEC = importlib.util.spec_from_file_location("via_sectorflow_trade_v0100", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)

RUN_DIR = MODULE.DEFAULT_OUT_DIR / MODULE.DEFAULT_RUN_TAG


def test_run_gate_and_ledger() -> None:
    summary = json.loads((RUN_DIR / "trade_run_summary.json").read_text("utf-8"))
    tests = pd.read_csv(RUN_DIR / "trade_test_ledger.csv")
    phases = pd.read_csv(RUN_DIR / "trade_phase_ledger.csv")
    assert summary["HardFailures"] == 0
    assert summary["Status"].startswith("TRADE_BACKTEST_PASS")
    assert summary["Execution"] == "T_PLUS_ONE"
    assert not ((tests["Status"] == "FAIL") & (tests["Severity"] == "HARD")).any()
    assert phases.loc[phases["Phase"] == "FINAL-TEST", "Status"].iloc[-1] == "PASS"


def test_expectancy_beats_null_in_structured_scenarios() -> None:
    bt = pd.read_csv(RUN_DIR / "trade_backtest_summary.csv")
    structured = bt[bt["Scenario"].isin(["ROTATION", "STEALTH_ACCUMULATION"])]
    assert (structured["Trades"] > 0).all()
    assert structured["NullMedianExpectancy"].notna().all()
    assert (structured["Expectancy"] > structured["NullMedianExpectancy"]).all()


def test_macro_gate_protects_in_tide_and_drain() -> None:
    bt = pd.read_csv(RUN_DIR / "trade_backtest_summary.csv")
    tide = bt[bt["Scenario"] == "MARKET_TIDE"]
    assert (tide["MaxDrawdown"] >= tide["BHMaxDrawdown"]).all()
    drain = bt[bt["Scenario"] == "DRAIN"]
    assert (drain["TotalReturn"] > drain["BHTotalReturn"]).all()


def test_costs_are_applied_and_positions_bounded() -> None:
    bt = pd.read_csv(RUN_DIR / "trade_backtest_summary.csv")
    traded = bt[bt["Trades"] > 0]
    assert (traded["GrossMinusNetDrag"] > 0).all()
    timeline = pd.read_csv(RUN_DIR / "position_timeline_main.csv")
    assert (timeline["EffectivePosition"] <= MODULE.FULL_FRACTION + 1e-9).all()
    assert (timeline["EffectivePosition"] >= 0).all()
    # T+1:每群首日有效持倉必為 0。
    first = timeline.sort_values("Date").groupby("Group")["EffectivePosition"].first()
    assert (first.fillna(0.0) == 0.0).all()


def test_trade_ledger_consistency() -> None:
    trades = pd.read_csv(RUN_DIR / "trade_ledger_main.csv", parse_dates=["EntryDate", "ExitDate"])
    assert not trades.empty
    assert (trades["ExitDate"] >= trades["EntryDate"]).all()
    round_trip = 2.0 * MODULE.FEE_RATE + MODULE.TAX_RATE + 2.0 * MODULE.SLIPPAGE_RATE
    assert np.allclose(trades["GrossReturn"] - trades["NetReturn"], round_trip)
    assert set(trades["ExitReason"].unique()) <= {"STOP", "SIGNAL_EXIT", "MACRO_HALT"}


def test_manifest_integrity() -> None:
    manifest = json.loads((RUN_DIR / "SHA256_MANIFEST.json").read_text("utf-8"))
    base = MODULE.def_load_base_engine()
    assert len(manifest) >= 8
    for rel, expected in manifest.items():
        path = RUN_DIR / rel
        assert path.exists(), rel
        assert base.def_sha256(path) == expected, rel
