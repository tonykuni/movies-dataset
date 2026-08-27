#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VRN_ENG070_YahooConsensus — Yahoo 共識資料引擎(批194;操作員令)
====================================================================
操作員令:「透過 Yahoo 取得共識資料」。
網路紀律(批180 凍結令+批181 階梯):零自建網路——一律經 SUP_MDL740
統包唯一正主 yahoo_quote_summary_raw 道(cookie+crumb 標準握手+雙同意
閘 fail-closed 隨統包);Yahoo 缺載/擋牆=誠實列敗不假數。
資料層(與 VRN_ENG069 共識庫同表多源共存=整合去重非另起爐灶):
  consensus_daily(date×code×source 主鍵 14 欄;本引擎 source=
  'YAHOO_QS',validated='YAHOO_DIRECT')——targetHigh/Low/Mean/
  Median×numberOfAnalystOpinions×EPS(earningsTrend 0y/+1y)×
  close(prices_canonical)×upside_pct=target_median/close-1;
  同鍵重跑=先刪後插冪等;consensus_latest 視圖自然涵蓋多源。
用法:python3 VRN_ENG070_YahooConsensus_v0100.py run [codes…] |
      --status | --selftest
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import importlib.util
import os
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
DB_TW = VIA / "functional modules" / "VDF" / "output_hub" / "mega" / "vdf_tw_market.duckdb"
NET_DIR = VIA / "supportive modules" / "network"
DEFAULT_CODES = ["2330", "2317", "2454"]
MODULES = "financialData,earningsTrend"


def _net():
    p = sorted(NET_DIR.glob("SUP_MDL740_NetUnified_v*.py"))[-1]
    spec = importlib.util.spec_from_file_location("net740_e70", p)
    m = importlib.util.module_from_spec(spec)
    sys.modules["net740_e70"] = m
    spec.loader.exec_module(m)
    return m


def _raw(d, *keys):
    """Yahoo 巢狀取值:{'raw': x} 或平值;缺=None 誠實"""
    cur = d
    for k in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
    if isinstance(cur, dict):
        cur = cur.get("raw")
    return cur if isinstance(cur, (int, float)) else None


def parse_symbol(payload: dict) -> dict | None:
    """quoteSummary result → 共識欄(零發明:僅收 Yahoo 實回值)"""
    fin = payload.get("financialData") or {}
    row = {
        "target_high": _raw(fin, "targetHighPrice"),
        "target_low": _raw(fin, "targetLowPrice"),
        "target_mean": _raw(fin, "targetMeanPrice"),
        "target_median": _raw(fin, "targetMedianPrice"),
        "n_analysts": _raw(fin, "numberOfAnalystOpinions"),
        "eps_fy0": None, "eps_fy1": None,
    }
    for t in (payload.get("earningsTrend") or {}).get("trend", []) or []:
        eps = _raw(t, "earningsEstimate", "avg")
        if t.get("period") == "0y":
            row["eps_fy0"] = eps
        elif t.get("period") == "+1y":
            row["eps_fy1"] = eps
    if row["target_median"] is None and row["target_mean"] is None:
        return None  # 無共識面=誠實跳過
    return row


def upsert(con, date: str, code: str, row: dict) -> None:
    """同鍵(date,code,source)先刪後插=冪等;close 自 prices_canonical"""
    close = con.execute(
        "SELECT close FROM prices_canonical WHERE ticker=? "
        "ORDER BY date DESC LIMIT 1", [f"{code}.TW"]).fetchone()
    close_v = close[0] if close else None
    tgt = row["target_median"] if row["target_median"] is not None else row["target_mean"]
    upside = (tgt / close_v - 1) if (tgt and close_v) else None
    con.execute("DELETE FROM consensus_daily WHERE date=? AND code=? AND source='YAHOO_QS'",
                [date, code])
    con.execute(
        "INSERT INTO consensus_daily VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [date, code, "YAHOO_QS", row["target_high"], row["target_low"],
         row["target_mean"], row["target_median"], row["n_analysts"],
         row["eps_fy0"], row["eps_fy1"],
         row["eps_fy1"] if row["eps_fy1"] is not None else row["eps_fy0"],
         close_v, upside, "YAHOO_DIRECT"])


def run(codes: list[str]) -> int:
    if os.environ.get("VIA_NET_CONSENT") != "YES":
        print("[Yahoo共識] 同意閘未開(VIA_NET_CONSENT≠YES)=拒跑(fail-closed 誠實)")
        return 2
    net = _net()
    import duckdb
    syms = [f"{c}.TW" for c in codes]
    r = net.yahoo_quote_summary_raw(syms, MODULES)
    data = r.get("data") or {}
    date = datetime.now().strftime("%Y-%m-%d")
    con = duckdb.connect(str(DB_TW))
    ok, failed = 0, []
    for c in codes:
        payload = data.get(f"{c}.TW")
        row = parse_symbol(payload) if payload else None
        if row is None:
            failed.append(c)
            continue
        upsert(con, date, c, row)
        print(f"  [OK  ] {c} 目標中位 {row['target_median']} · 分析師 {row['n_analysts']}"
              f" · FY1 EPS {row['eps_fy1']}")
        ok += 1
    con.close()
    if failed:
        print(f"  [FAIL] {'、'.join(failed)}:Yahoo 缺載/無共識面=誠實列敗不假數")
    print(f"[Yahoo共識] 成 {ok} · 敗 {len(failed)} · source=YAHOO_QS 入 consensus_daily"
          f"(統包 quoteSummary raw 道;雙同意閘)")
    return 0


def status() -> int:
    import duckdb
    con = duckdb.connect(str(DB_TW), read_only=True)
    try:
        for s, n, mx in con.execute(
                "SELECT source, count(*), max(date) FROM consensus_daily "
                "GROUP BY source ORDER BY source").fetchall():
            print(f"  [{s}] {n:,} 筆 · 最新 {mx}")
    except Exception:
        print("  [共識庫] 未建(誠實)")
    con.close()
    return 0


def selftest() -> int:
    import duckdb
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    chk("① 統包唯一網路道(quoteSummary raw 道;零自建網路)",
        "yahoo_quote_summary_raw" in src
        and ("import " + "requests") not in src
        and ("sub" + "process") not in src)
    saved = os.environ.pop("VIA_NET_CONSENT", None)
    rc = run(["2330"])
    if saved is not None:
        os.environ["VIA_NET_CONSENT"] = saved
    chk("② 同意閘 fail-closed(閘未開=拒跑 rc2 零觸網)", rc == 2)
    fx = {"financialData": {"targetHighPrice": {"raw": 1500.0},
                            "targetLowPrice": {"raw": 900.0},
                            "targetMeanPrice": {"raw": 1250.0},
                            "targetMedianPrice": {"raw": 1200.0},
                            "numberOfAnalystOpinions": {"raw": 30}},
          "earningsTrend": {"trend": [
              {"period": "0y", "earningsEstimate": {"avg": {"raw": 60.0}}},
              {"period": "+1y", "earningsEstimate": {"avg": {"raw": 72.0}}}]}}
    row = parse_symbol(fx)
    chk("③ 剖析器數學(fixture:目標四值+30 分析師+EPS 0y/+1y)",
        row == {"target_high": 1500.0, "target_low": 900.0,
                "target_mean": 1250.0, "target_median": 1200.0,
                "n_analysts": 30, "eps_fy0": 60.0, "eps_fy1": 72.0})
    chk("④ 無共識面=誠實跳過(空回包→None 不假列)",
        parse_symbol({"financialData": {}}) is None)
    con = duckdb.connect(str(DB_TW))
    con.execute("BEGIN")
    upsert(con, "1900-01-01", "TEST70", row)
    upsert(con, "1900-01-01", "TEST70", row)  # 同鍵重跑
    n, up = con.execute(
        "SELECT count(*), max(upside_pct) FROM consensus_daily "
        "WHERE code='TEST70' AND source='YAHOO_QS'").fetchone()
    chk("⑤ 同鍵冪等(重跑仍 1 筆)+upside=中位/close-1(無 close=NULL 誠實)",
        n == 1 and up is None)
    multi = con.execute(
        "SELECT count(DISTINCT source) FROM consensus_daily").fetchone()[0]
    chk("⑥ 多源共存(EXTERNAL_ANALYST+YAHOO_QS 同表;主鍵三元不撞)",
        multi >= 2)
    con.execute("ROLLBACK")
    left = con.execute(
        "SELECT count(*) FROM consensus_daily WHERE code='TEST70'").fetchone()[0]
    chk("⑦ fixture 零殘留(ROLLBACK 後正表無測試列)", left == 0)
    con.close()
    boot = (VIA / "supportive modules" / "registry" /
            "via_boot_update.sh").read_text(encoding="utf-8")
    chk("⑧ boot 接線+紀律宣告(統包正主/fail-closed/多源共存/不假數)",
        "VRN_ENG070" in boot and all(k in src for k in
        ("統包唯一正主", "fail-closed", "多源共存", "不假數")))
    print(f"  [計] 八檢 OK {8 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== Yahoo 共識引擎(VRN_ENG070)· 八檢自測(零網路)===")
        return selftest()
    if "--status" in args:
        return status()
    if args and args[0] == "run":
        return run(args[1:] or DEFAULT_CODES)
    return status()


if __name__ == "__main__":
    sys.exit(main())
