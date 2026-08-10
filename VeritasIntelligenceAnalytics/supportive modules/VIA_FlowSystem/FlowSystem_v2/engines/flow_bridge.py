# -*- coding: utf-8 -*-
"""VDF-FLOW-BRIDGE flow_bridge.py — 真實資料入口(v0100R)。

live 模式讀 data/input/daily_data.json(schema:{records:[{snapshot_date,ticker,close,
shares_out,aum_reported?}]},由 fetch_global_etf_tracker_v4 / TWSE / yfinance 側車寫入);
缺席=誠實回 None(呼叫端退 synth,不冒充真實)。零爬站 — 本引擎只讀本地檔。
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DAILY = ROOT / "data" / "input" / "daily_data.json"
PERF = ROOT / "data" / "input" / "perf_prices.json"
REF = ROOT / "data" / "input" / "reference_flows.json"


def _load(p):
    if not p.exists():
        return None
    try:
        j = json.loads(p.read_text(encoding="utf-8-sig"))
        return j.get("records") if isinstance(j, dict) else j
    except Exception:
        return None


def load_daily():
    return _load(DAILY)


def load_perf_prices():
    return _load(PERF)


def load_reference_flows():
    return _load(REF)


def source_status():
    return {"daily_data": DAILY.exists(), "perf_prices": PERF.exists(),
            "reference_flows": REF.exists()}
