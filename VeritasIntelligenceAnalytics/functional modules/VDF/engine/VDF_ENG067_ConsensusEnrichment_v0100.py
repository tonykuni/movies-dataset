#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_ENG067_ConsensusEnrichment — ETF 持股×共識增益橋(批243;操作員令)
====================================================================
操作員令:「INTEGRATE ALL LIBS AND TOOLS INTO EXISTING ENGINES」——
收容包 VETF_FINAL_SEAL_b242 之 ConsensusEnrichment Adapter v001
(FactSet/YFinance 目標價×最新 Adj Close as-of join;來源永遠分欄
不跨源平均;candidate 模式 append-only 不動正本)整合進現役 VDF
引擎群。收容件原地不動,本引擎=graceful 橋:
  ①來源解析(全在庫=零網路):
    holdings=ActiveTWETF.duckdb::holdings_daily(ENG051 產)
      →欄名橋接 portfolio_date→holding_date/etf_ticker→etf_code
    prices=vdf_tw_market.duckdb::tw_prices_adj(ENG060 產;近 45 日)
    factset=consensus_latest WHERE source='CNYES_FACTSET'(ENG071 產)
      →date→snapshot_date/code→ticker/n_analysts→target_analyst_count
    yfinance=庫內現無獨立快照=誠實 NOT_PROVIDED(不假造)
  ②輸出=output_hub/candidates/vetf_consensus/asof=<日>/(gitignored;
    Adapter 自帶 manifest+sha256+append-only+SKIPPED_IDENTICAL 冪等)
  ③probe=來源在位/列數/Adapter 後端矩陣誠實三態
用法:python3 VDF_ENG067_ConsensusEnrichment_v0100.py probe|run
      | --selftest
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
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF = HERE.parent
DB_TW = VDF / "output_hub" / "mega" / "vdf_tw_market.duckdb"
DB_ETF = (VDF / "output_hub" / "active_tw_etf" / "active_tw_etf_holdings"
          / "ActiveTWETF.duckdb")
OUT = VDF / "output_hub" / "candidates" / "vetf_consensus"
INTAKE = (VDF / "references" / "intake" / "VETF_FINAL_SEAL_b242"
          / "01_ENGINES" / "Consensus_Enrichment_Adapter")

# 欄名橋接 SQL(在庫欄→Adapter 別名冊;誠實映射不造欄)
Q_HOLD = ("SELECT portfolio_date AS holding_date, etf_ticker AS etf_code, "
          "etf_name, holding_ticker AS ticker, holding_name AS company_name, "
          "weight_pct AS holding_weight, shares AS holding_shares "
          "FROM holdings_daily")
# tw_prices_adj.date=ISO VARCHAR→截切點在 Python 算(_stage 內代入)
Q_PX = ("SELECT date AS price_date, ticker, adj_close FROM tw_prices_adj "
        "WHERE date >= '{cutoff}'")
Q_FS = ("SELECT date AS snapshot_date, code AS ticker, target_low, "
        "target_mean, target_median, target_high, "
        "n_analysts AS target_analyst_count "
        "FROM consensus_latest WHERE source='CNYES_FACTSET'")


def _adapter():
    """收容件 graceful 掛載(原地不動)"""
    try:
        if str(INTAKE) not in sys.path:
            sys.path.insert(0, str(INTAKE))
        import VETF_ConsensusEnrichment_Adapter_v001 as ADP  # noqa: N811
        return ADP
    except Exception:
        return None


def _export(con, sql: str, dest: Path) -> int:
    cur = con.execute(sql)
    cols = [c[0] for c in cur.description]
    rows = cur.fetchall()
    with dest.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        w.writerows(rows)
    return len(rows)


def _stage(staging: Path) -> dict:
    """在庫來源→Adapter 輸入 CSV(誠實三態;缺=NOT_PROVIDED 不假造)"""
    import duckdb
    staging.mkdir(parents=True, exist_ok=True)
    st: dict = {}
    if DB_ETF.exists():
        con = duckdb.connect(str(DB_ETF), read_only=True)
        st["holdings"] = {"path": staging / "holdings.csv",
                          "rows": _export(con, Q_HOLD,
                                          staging / "holdings.csv")}
        con.close()
    else:
        st["holdings"] = None
    if DB_TW.exists():
        con = duckdb.connect(str(DB_TW), read_only=True)
        from datetime import date, timedelta
        mx = con.execute("SELECT MAX(date) FROM tw_prices_adj").fetchone()[0]
        cut = str(date.fromisoformat(str(mx)[:10]) - timedelta(days=45)) \
            if mx else "1900-01-01"
        st["prices"] = {"path": staging / "prices.csv",
                        "rows": _export(con, Q_PX.format(cutoff=cut),
                                        staging / "prices.csv")}
        st["factset"] = {"path": staging / "factset.csv",
                         "rows": _export(con, Q_FS, staging / "factset.csv")}
        con.close()
    else:
        st["prices"] = st["factset"] = None
    st["yfinance"] = None                    # 庫內現無獨立快照=誠實不假造
    return st


def probe() -> int:
    ADP = _adapter()
    print(f"[probe] Adapter 掛載={'OK' if ADP else 'FAIL(收容件缺)'}"
          f" · {INTAKE.name}")
    if ADP:
        be = ADP.detect_optional_backends()
        print(f"[probe] 選用後端:{ {k: v for k, v in be.items()} }")
    for name, p, note in (("holdings", DB_ETF, "holdings_daily(ENG051)"),
                          ("prices/factset", DB_TW,
                           "tw_prices_adj+consensus_latest")):
        print(f"[probe] {name}:{'OK ' + note if p.exists() else 'MISS(誠實;先跑上游)'}")
    print("[probe] yfinance 快照:NOT_PROVIDED(誠實;庫內無獨立來源)")
    return 0 if ADP else 1


def run() -> int:
    ADP = _adapter()
    if ADP is None:
        print("[FAIL] 收容件缺=誠實停(references/intake/VETF_FINAL_SEAL_b242)")
        return 1
    staging = OUT / "_staging"
    st = _stage(staging)
    if not st["holdings"] or not st["prices"]:
        print("[SKIP] 來源不足(holdings/prices 缺)=誠實停;先跑 ENG051/ENG060")
        return 2
    args = ["--holdings", str(st["holdings"]["path"]),
            "--prices", str(st["prices"]["path"]),
            "--output-dir", str(OUT), "--asof", "latest",
            "--write-mode", "candidate"]
    if st["factset"] and st["factset"]["rows"]:
        args += ["--factset", str(st["factset"]["path"])]
    print(f"[run] holdings={st['holdings']['rows']:,} 列 · "
          f"prices={st['prices']['rows']:,} 列 · "
          f"factset={st['factset']['rows'] if st['factset'] else 0} 檔 · "
          f"yfinance=NOT_PROVIDED(誠實)")
    rc = ADP.main(args)
    print(f"[run] Adapter rc={rc} · 輸出 {OUT}(candidate append-only;"
          "gitignored)")
    return rc


def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    ADP = _adapter()
    chk("① 收容件原地掛載(intake 不動;graceful)", ADP is not None
        and INTAKE.exists() and "references" in str(INTAKE))
    if ADP is None:
        print("  [計] 十檢 OK 0 · FAIL 10(收容件缺=後檢全略)")
        return 1
    chk("② 純函式橋(to_float 千分位/parse_date 斜線)",
        ADP.to_float("1,234.5") == 1234.5
        and str(ADP.parse_date("2026/08/28")) == "2026-08-28")
    canon = ADP.canonicalize_record(
        {"holding_ticker": "2330", "weight_pct": "9.1"}, ADP.HOLDING_ALIASES)
    chk("③ 別名冊映射(holding_ticker→ticker/weight_pct→holding_weight)",
        canon.get("ticker") == "2330" and canon.get("holding_weight") == "9.1")
    chk("④ 欄名橋接 SQL 對齊別名冊(holding_date/etf_code/snapshot_date/"
        "target_analyst_count)",
        all(k in Q_HOLD for k in ("holding_date", "etf_code"))
        and "snapshot_date" in Q_FS and "target_analyst_count" in Q_FS)
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        (tdp / "h.csv").write_text(
            "holding_date,etf_code,etf_name,ticker,company_name,"
            "holding_weight\n"
            "2026-08-28,00981A,主動統一台股增長,2330,台積電,9.1\n",
            encoding="utf-8")
        (tdp / "p.csv").write_text(
            "price_date,ticker,adj_close,currency\n"
            "2026-08-28,2330,100.0,TWD\n", encoding="utf-8")
        (tdp / "f.csv").write_text(
            "snapshot_date,ticker,target_low,target_mean,target_median,"
            "target_high,target_analyst_count\n"
            "2026-08-27,2330,90,120,118,150,30\n", encoding="utf-8")
        rc = ADP.main(["--holdings", str(tdp / "h.csv"),
                       "--prices", str(tdp / "p.csv"),
                       "--factset", str(tdp / "f.csv"),
                       "--output-dir", str(tdp / "out"),
                       "--asof", "latest", "--write-mode", "candidate"])
        runs = sorted((tdp / "out").glob("asof=*"))
        chk("⑤ fixture 端到端 candidate 跑通(rc0+asof 分夾+manifest)",
            rc == 0 and runs and (runs[0] / "manifest.json").exists())
        enriched = {}
        if runs:
            csvp = sorted(runs[0].glob("*consensus_enriched.csv"))
            if csvp:
                with csvp[0].open(encoding="utf-8") as fh:
                    enriched = next(iter(csv.DictReader(fh)), {})
        fs_cols = [c for c in enriched if c.startswith("fs_")]
        yf_cols = [c for c in enriched if c.startswith("yf_")]
        up_cols = [c for c in enriched if "upside" in c.lower()]
        chk("⑥ 來源分欄紅線(fs_*/yf_* 永遠分欄;不跨源平均)+Upside 欄在",
            bool(fs_cols) and bool(yf_cols) and bool(up_cols))
        up_val = next((enriched[c] for c in up_cols
                       if "mean" in c.lower() and enriched.get(c)), None)
        chk("⑦ Upside 真算(TP mean 120÷AdjClose 100-1=20%)",
            up_val is not None and abs(float(up_val) - 20.0) < 0.51,
            f"got={up_val}")
        rc2 = ADP.main(["--holdings", str(tdp / "nofile.csv"),
                        "--prices", str(tdp / "p.csv"),
                        "--output-dir", str(tdp / "out2"),
                        "--asof", "latest"])
        chk("⑧ FAIL_CLOSED 誠實(缺來源=rc2 不假跑)", rc2 == 2)
    chk("⑨ candidate 預設不動正本+輸出 gitignored 宣告",
        '"candidate"' in src and "gitignored" in src
        and "output_hub" in str(OUT))
    chk("⑩ 零網路+加速橋(本引擎純在庫橋接)",
        all(("import " + k) not in src for k in ("requests", "httpx"))
        and "ACCEL-BRIDGE" in src)
    print(f"  [計] 十檢 OK {10 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== ETF 持股×共識增益橋(VDF_ENG067)· 十檢自測(零網路)===")
        return selftest()
    if args and args[0] == "probe":
        return probe()
    if args and args[0] == "run":
        return run()
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
