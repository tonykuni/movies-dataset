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

import pandas as pd

MODULE_PATH = Path(__file__).with_name("VIA_LiveWire_ContractAdapter_v0100.py")
SPEC = importlib.util.spec_from_file_location("via_livewire_v0100", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)

RUN_DIR = MODULE.DEFAULT_OUT


def test_ticker_regex_contract() -> None:
    assert MODULE.def_validate_ticker("2330")
    assert MODULE.def_validate_ticker("3081")
    assert not MODULE.def_validate_ticker("0050")     # ETF
    assert not MODULE.def_validate_ticker("23300")    # 5 碼
    assert not MODULE.def_validate_ticker("030001")   # 權證
    assert not MODULE.def_validate_ticker("9999A")    # 特別股後綴


def test_schema_neutralizer_variants() -> None:
    for raw in [
        {"S": {"components": [{"symbol": "2330", "company": "台積電", "type": "LEADER"}]}},
        {"S": {"stocks": [{"code": "3037", "stock_name": "欣興"}]}},
        [{"group": "S", "members": [{"id": "1519", "title": "華城", "category": "leader"}]}],
    ]:
        nd = MODULE.def_normalize_database(raw)
        m = nd["S"]["members"][0]
        assert MODULE.def_validate_ticker(m["ticker"])
        assert m["name"]
        assert m["role"] == m["role"].upper()


def test_fetcher_fail_closed_never_fabricates() -> None:
    fetcher = MODULE.HonestMarketDataFetcher(allow_network=False)
    st = fetcher.fetch_daily("2330")
    assert st.status == "UNAVAILABLE_NETWORK"
    assert st.data is None            # 修復 A01 缺陷:無真值絕不回傳編造數字
    assert fetcher.fetch_daily("0050").status == "INVALID_TICKER"


def test_panel_contract_gatekeeper() -> None:
    good = pd.DataFrame({
        "Date": pd.to_datetime(["2026-01-02"]), "Ticker": ["2330"], "Group": ["C"],
        "Market": ["TWSE"], "AdjClose": [1000.0], "Turnover": [5e9],
        "DaytradeTurnover": [1e9], "ForeignNet": [1e8], "TrustNet": [0.0],
        "DealerNet": [0.0], "WhaleNet": [0.0],
    })
    assert MODULE.def_validate_panel_contract(good) == []
    bad = good.copy()
    bad["DaytradeTurnover"] = 9e9
    assert "DAYTRADE_EXCEEDS_TURNOVER" in MODULE.def_validate_panel_contract(bad)
    assert any("MISSING_COLUMNS" in f for f in MODULE.def_validate_panel_contract(good.drop(columns=["WhaleNet"])))


def test_reconcile_three_strategies() -> None:
    local = pd.DataFrame({
        "Ticker": ["3081", "2330", "6442"],
        "Name": ["聯亞光電", "台積電", "光聖"],
        "Group": ["I", "C", "I"],
        "Market": ["TPEX", "TWSE", "TPEX"],
    })
    mother = {"CPO": {"members": [
        {"ticker": "3081", "name": "聯亞", "role": "LEADER"},          # 精確 ticker
        {"ticker": "6442-ERR", "name": "光聖科技", "role": "PEER"},    # 錯碼 → 名稱模糊
        {"ticker": "8888", "name": "未上市新創", "role": "LAGGARD"},   # fail-closed
    ]}}
    ledger, result = MODULE.def_reconcile_against_local(mother, local, similarity_threshold=55.0)
    kinds = ledger["MatchType"].tolist()
    assert kinds[0] == "EXACT_TICKER_MATCH"
    assert kinds[1].startswith("FUZZY_NAME_MATCH")
    assert kinds[2] == "UNMAPPED_FAIL_CLOSED"
    assert len(result.unmapped) == 1


def test_evidence_run_gate_and_v11_reconcile() -> None:
    summary = json.loads((RUN_DIR / "adapter_run_summary.json").read_text("utf-8"))
    tests = pd.read_csv(RUN_DIR / "adapter_test_ledger.csv")
    ledger = pd.read_csv(RUN_DIR / "mother_ssot_reconcile_ledger.csv")
    assert summary["HardFailures"] == 0
    assert summary["Status"] == "ADAPTER_VERIFIED_FAIL_CLOSED"
    assert not ((tests["Status"] == "FAIL") & (tests["Severity"] == "HARD")).any()
    rec = summary["ReconcileSummary"]
    assert rec["total"] == len(ledger) == 76
    assert rec["exact"] + rec["fuzzy"] + rec["unmapped"] == rec["total"]
    assert len(summary["IntakeAudit"]["integrated"]) == 4
    assert len(summary["IntakeAudit"]["rejected"]) == 4
