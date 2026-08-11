# -*- coding: utf-8 -*-
"""VDF-FLOW-BRIDGE flow_bridge.py — 真實資料入口(v0101R)。

live 模式讀 data/input/daily_data.json(schema:{records:[{snapshot_date,ticker,close,
shares_out,aum_reported?}]},由 fetch_global_etf_tracker_v4 / TWSE / yfinance 側車寫入);
缺席=誠實回 None(呼叫端退 synth,不冒充真實)。零爬站 — 本引擎只讀本地檔。

changelog:
  v0101R 2026-08-11 整合去重令:新增 etf_flow_precise.csv 真值入口(原始會話 MarketFlow
    正典 schema:date,ticker,aum,shares_outstanding,nav_per_share,ret_1d,flow_raw,
    flow_method,source,evidence_status)。只取 flow_raw 非空且 evidence_status 具證據之列
    (原鐵律:無 AUM/shares 證據不得寫 flow_raw — 空檔=誠實,不轉出任何真值);
    load_reference_flows() 於 reference_flows.json 缺席時自動後備此 CSV,
    映射為 Pillar A 期望格式 {snapshot_date,ticker,ref_flow}。
  v0100R 初版:daily/perf/reference 三入口。
"""
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DAILY = ROOT / "data" / "input" / "daily_data.json"
PERF = ROOT / "data" / "input" / "perf_prices.json"
REF = ROOT / "data" / "input" / "reference_flows.json"
FLOW_PRECISE = ROOT / "data" / "input" / "etf_flow_precise.csv"


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


def load_flow_precise():
    """etf_flow_precise.csv → Pillar A 真值列。無證據列一律不出(誠實空)。"""
    if not FLOW_PRECISE.exists():
        return None
    rows = []
    try:
        with FLOW_PRECISE.open(encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                raw = (r.get("flow_raw") or "").strip()
                ev = (r.get("evidence_status") or "").strip().upper()
                if not raw or ev in ("", "NONE", "NO_EVIDENCE", "FAIL"):
                    continue
                try:
                    rows.append({"snapshot_date": (r.get("date") or "").strip(),
                                 "ticker": (r.get("ticker") or "").strip(),
                                 "ref_flow": float(raw)})
                except ValueError:
                    continue
    except Exception:
        return None
    return rows or None


def load_reference_flows():
    ref = _load(REF)
    if ref:
        return ref
    return load_flow_precise()


def source_status():
    return {"daily_data": DAILY.exists(), "perf_prices": PERF.exists(),
            "reference_flows": REF.exists(),
            "etf_flow_precise": FLOW_PRECISE.exists()}
