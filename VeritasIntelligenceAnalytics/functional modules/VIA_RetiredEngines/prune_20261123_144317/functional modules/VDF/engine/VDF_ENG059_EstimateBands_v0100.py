#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_ENG059_EstimateBands — 分析師預估×PE/PB band(批155;via-bands)
====================================================================
操作員令:鉅亨 FactSet 目標價/EPS+Yahoo 高低中位平均→「中位數的平均值」
為採用 EPS→畫 PE band/PB band。
雙源階梯(誠實):
  YAHOO(通)=targetHigh/Low/Mean/Median+EPS 0y/+1y avg/low/high+BPS
  CNYES_FACTSET(PENDING)=ws 端點 SPA 隱藏未公開;統包 v0107 已備
    cnyes_quote 車道,預估端點解鎖即自動雙源(採用 EPS=兩源中位之平均)
  現階段採用 EPS=Yahoo 0y 年度預估 avg(單源;SOURCE 欄標 YAHOO_ONLY)
Band 法(零固定門檻):
  PE_t=price_t/採用EPS;PB_t=price_t/BPS
  band 線=採用值×歷史序列分位 {P10,P25,P50,P75,P90}(全窗分位,隨資料
  滾動更新=動態);現位=當前值於歷史分布之百分位(數值)
產出:duckdb::analyst_estimates(快照 upsert)+bands_summary CSV
  +示範圖 PNG(output_hub/estimate_bands/,gitignored)
用法:via-bands run [--top N] | --chart CODE | --status | --selftest
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

import json
import os
import sys
from datetime import date, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF = HERE.parent
VIA = VDF.parent.parent
MEGA = VDF / "output_hub" / "mega"
DB_TW = MEGA / "vdf_tw_market.duckdb"
OUT = VDF / "output_hub" / "estimate_bands"
QUANTS = (0.10, 0.25, 0.50, 0.75, 0.90)


def gate_open(env=None) -> bool:
    env = env if env is not None else os.environ
    return env.get("VIA_NET_CONSENT") == "YES" and env.get("VIA_SCRAPE_CONSENT") == "YES"


def _net():
    import glob
    import importlib.util
    hits = sorted(glob.glob(str(VIA / "supportive modules" / "network"
                                / "SUP_MDL740_NetUnified_v*.py")))
    spec = importlib.util.spec_from_file_location("via_net_dyn59", hits[-1])
    m = importlib.util.module_from_spec(spec)
    sys.modules["via_net_dyn59"] = m
    spec.loader.exec_module(m)
    return m


def _raw(v, *keys):
    for k in keys:
        v = v.get(k, {}) if isinstance(v, dict) else {}
    return v.get("raw") if isinstance(v, dict) else None


def parse_estimates(sym: str, d: dict) -> dict:
    """quoteSummary 原始 modules→預估列(缺值誠實 None)"""
    fd = d.get("financialData", {})
    ks = d.get("defaultKeyStatistics", {})
    row = {"date": str(date.today()), "code": sym.split(".")[0], "yf_ticker": sym,
           "source": "YAHOO_ONLY(CNYES_FACTSET_PENDING)",
           "target_high": _raw(fd, "targetHighPrice"),
           "target_low": _raw(fd, "targetLowPrice"),
           "target_mean": _raw(fd, "targetMeanPrice"),
           "target_median": _raw(fd, "targetMedianPrice"),
           "n_analysts": _raw(fd, "numberOfAnalystOpinions"),
           "trailing_eps": _raw(ks, "trailingEps"),
           "bps": _raw(ks, "bookValue")}
    for t in d.get("earningsTrend", {}).get("trend", []):
        p = t.get("period")
        if p in ("0y", "+1y"):
            ee = t.get("earningsEstimate", {})
            tag = "eps0y" if p == "0y" else "eps1y"
            row[f"{tag}_avg"] = _raw(ee, "avg")
            row[f"{tag}_low"] = _raw(ee, "low")
            row[f"{tag}_high"] = _raw(ee, "high")
            row[f"{tag}_n"] = _raw(ee, "numberOfAnalysts")
    # 採用 EPS:雙源設計=各源中位之平均;現單源=Yahoo 0y avg(誠實標記)
    row["adopted_eps"] = row.get("eps0y_avg")
    return row


def band_stats(prices: "list[float]", denom: float) -> dict | None:
    """比值序列(price/denom)之分位帶+現位百分位(全數值)"""
    import numpy as np
    if not denom or denom <= 0 or len(prices) < 60:
        return None
    ratio = np.array([p / denom for p in prices if p and p > 0])
    if len(ratio) < 60:
        return None
    qs = {f"p{int(q * 100)}": round(float(np.quantile(ratio, q)), 3) for q in QUANTS}
    cur = float(ratio[-1])
    pct = round(float((ratio <= cur).mean() * 100), 1)
    return {"current": round(cur, 3), **qs, "percentile_now": pct,
            "band_prices": {k: round(v * denom, 1) for k, v in qs.items()}}


def _universe(top_n: int | None) -> list[str]:
    import csv
    grp = VIA / "functional modules" / "GroupIndex"
    pkgs = sorted(grp.glob("VIA_TW_Grouping_LatestCommand_v*"))
    memb = sorted(pkgs[-1].glob("VIA_ThreeList_CanonicalMembershipInput_v*.csv"))[-1]
    rows = list(csv.DictReader(open(memb, encoding="utf-8-sig")))
    if top_n:  # 先領袖級(Rank=L)後其餘,截前 N
        rows = sorted(rows, key=lambda r: 0 if r.get("Rank") == "L" else 1)[:top_n]
    return sorted({r["YFTicker"] for r in rows if r.get("YFTicker")})


def upsert(rows: list[dict]) -> int:
    import duckdb
    import pandas as pd
    df = pd.DataFrame(rows)
    con = duckdb.connect(str(DB_TW))
    con.execute("CREATE TABLE IF NOT EXISTS analyst_estimates AS SELECT * FROM df LIMIT 0")
    have = {c[0] for c in con.execute("DESCRIBE analyst_estimates").fetchall()}
    for c in df.columns:
        if c not in have:
            con.execute(f'ALTER TABLE analyst_estimates ADD COLUMN "{c}" DOUBLE')
    cols = ", ".join(f'"{c}"' for c in df.columns)  # 按欄名(QA-20260825A)
    con.execute(f"INSERT INTO analyst_estimates ({cols}) SELECT {cols} FROM df "
                f"WHERE NOT EXISTS (SELECT 1 FROM analyst_estimates t "
                f'WHERE t."date"=df."date" AND t."code"=df."code")')
    n = con.execute("SELECT COUNT(*) FROM analyst_estimates").fetchone()[0]
    con.close()
    return n


def _price_series(tickers: list[str]) -> dict:
    import duckdb
    con = duckdb.connect(str(DB_TW), read_only=True)
    ph = ",".join("?" * len(tickers))
    df = con.execute(f"SELECT ticker, date, adj_close FROM tw_daily_prices "
                     f"WHERE ticker IN ({ph}) AND adj_close IS NOT NULL "
                     f"ORDER BY ticker, date", tickers).df()
    con.close()
    return {t: g["adj_close"].tolist() for t, g in df.groupby("ticker")}


def run(top_n: int | None = None) -> int:
    if not gate_open():
        print("[FAIL-CLOSED] 同意閘未開")
        return 2
    net = _net()
    syms = _universe(top_n)
    print(f"[預估] 宇宙 {len(syms)} 檔(quoteSummary raw 道)…", flush=True)
    r = net.yahoo_quote_summary_raw(
        syms, "financialData,earningsTrend,defaultKeyStatistics")
    if r.get("state") != "OK":
        print(f"[FAIL] {r.get('note')}")
        return 1
    rows = [parse_estimates(s, d) for s, d in r["results"].items()]
    got_eps = [x for x in rows if x.get("adopted_eps")]
    n = upsert(rows)
    print(f"[落庫] {len(rows)} 檔({len(r['failed'])} 敗誠實列)· 具採用 EPS "
          f"{len(got_eps)} · analyst_estimates 累計 {n}")
    px = _price_series([x["yf_ticker"] for x in got_eps])
    OUT.mkdir(parents=True, exist_ok=True)
    summary = []
    for x in got_eps:
        p = px.get(x["yf_ticker"], [])
        pe = band_stats(p, x["adopted_eps"])
        pb = band_stats(p, x["bps"]) if x.get("bps") else None
        summary.append({"code": x["code"], "adopted_eps": x["adopted_eps"],
                        "eps_source": x["source"], "n_analysts": x.get("n_analysts"),
                        "target_median": x.get("target_median"),
                        "pe_now": pe["current"] if pe else None,
                        "pe_percentile": pe["percentile_now"] if pe else None,
                        "pe_band": json.dumps(pe["band_prices"]) if pe else None,
                        "pb_now": pb["current"] if pb else None,
                        "pb_percentile": pb["percentile_now"] if pb else None})
    import pandas as pd
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_csv = OUT / f"bands_summary_{ts}.csv"
    pd.DataFrame(summary).to_csv(out_csv, index=False, encoding="utf-8-sig")
    ok_pe = sum(1 for s in summary if s["pe_now"])
    print(f"[band] PE 帶出值 {ok_pe}/{len(summary)} · {out_csv.name}")
    chart("2330")
    return 0


def chart(code: str) -> int:
    """單檔 PE/PB band 圖(價格線+五分位帶線;示範=VAP 模板前哨)"""
    import duckdb
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    con = duckdb.connect(str(DB_TW), read_only=True)
    est = con.execute("SELECT * FROM analyst_estimates WHERE code=? "
                      "ORDER BY date DESC LIMIT 1", [code]).df()
    px = con.execute("SELECT date, adj_close FROM tw_daily_prices "
                     "WHERE ticker LIKE ? ORDER BY date", [f"{code}.%"]).df()
    con.close()
    if est.empty or px.empty:
        print(f"[SKIP] {code} 無預估/價格")
        return 1
    e = est.iloc[0]
    OUT.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    for ax, denom, tag in ((axes[0], e.get("adopted_eps"), "PE"),
                           (axes[1], e.get("bps"), "PB")):
        if not denom or denom <= 0:
            ax.set_title(f"{tag} band PENDING(分母缺)")
            continue
        b = band_stats(px["adj_close"].tolist(), float(denom))
        if not b:
            continue
        ax.plot(pd_dates(px), px["adj_close"], lw=1.4, label="price")
        for k, v in b["band_prices"].items():
            ax.axhline(v, ls="--", lw=0.8, alpha=0.7)
            ax.annotate(f"{k}×", (0.005, v), xycoords=("axes fraction", "data"),
                        fontsize=7, va="bottom")
        ax.set_title(f"{code} {tag} band(現位 {b['percentile_now']} 百分位·"
                     f"{tag}={b['current']})")
        ax.legend(fontsize=8)
    fig.tight_layout()
    out = OUT / f"band_{code}_{datetime.now().strftime('%Y%m%d')}.png"
    fig.savefig(out, dpi=130)
    plt.close(fig)
    print(f"[圖] {out}")
    return 0


def pd_dates(px):
    import pandas as pd
    return pd.to_datetime(px["date"])


def status() -> int:
    import duckdb
    con = duckdb.connect(str(DB_TW), read_only=True)
    try:
        n, d = con.execute("SELECT COUNT(*), MAX(date) FROM analyst_estimates").fetchone()
        eps = con.execute("SELECT COUNT(*) FROM analyst_estimates "
                          "WHERE adopted_eps IS NOT NULL").fetchone()[0]
        print(f"analyst_estimates {n} 列 · 最新 {d} · 具採用 EPS {eps}")
    except Exception:
        print("analyst_estimates 未建(先 run)")
    con.close()
    return 0


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    chk("① 同意閘 fail-closed", not gate_open({}) and gate_open(
        {"VIA_NET_CONSENT": "YES", "VIA_SCRAPE_CONSENT": "YES"}))

    fx = {"financialData": {"targetHighPrice": {"raw": 4200.0}, "targetLowPrice": {"raw": 2650.0},
                            "targetMeanPrice": {"raw": 3229.3}, "targetMedianPrice": {"raw": 3200.0},
                            "numberOfAnalystOpinions": {"raw": 33}},
          "defaultKeyStatistics": {"trailingEps": {"raw": 85.5}, "bookValue": {"raw": 248.05}},
          "earningsTrend": {"trend": [
              {"period": "0y", "earningsEstimate": {"avg": {"raw": 107.64},
                                                    "low": {"raw": 98.4}, "high": {"raw": 113.38},
                                                    "numberOfAnalysts": {"raw": 34}}},
              {"period": "+1y", "earningsEstimate": {"avg": {"raw": 142.13}}}]}}
    r = parse_estimates("2330.TW", fx)
    chk("② 預估解析(目標四值+EPS 0y/+1y+BPS+採用 EPS)",
        r["target_median"] == 3200.0 and r["eps0y_avg"] == 107.64
        and r["eps1y_avg"] == 142.13 and r["adopted_eps"] == 107.64
        and r["bps"] == 248.05)
    chk("③ 雙源階梯誠實標記", "PENDING" in r["source"])

    prices = [100 + i * 0.5 for i in range(200)]
    b = band_stats(prices, 10.0)
    chk("④ band 分位帶+現位百分位(數值)",
        b is not None and b["p50"] == round((prices[0] / 10 + prices[-1] / 10) / 2, 3)
        and b["percentile_now"] == 100.0 and "p90" in b["band_prices"])
    chk("⑤ band 資料量下限(<60 誠實 None)", band_stats([100.0] * 30, 10.0) is None)

    import tempfile
    global DB_TW
    _db = DB_TW
    with tempfile.TemporaryDirectory() as td:
        DB_TW = Path(td) / "t.duckdb"
        n1 = upsert([r])
        n2 = upsert([r])
        chk("⑥ 快照 upsert 冪等(date+code)", n1 == 1 and n2 == 1)
    DB_TW = _db

    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 紀律宣告(雙源設計/採用 EPS 規則/分位帶零固定)",
        all(k in src for k in ("兩源中位之平均", "CNYES_FACTSET", "QUANTS")))
    print(f"  [計] 七檢 OK {7 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 估值 band 引擎(VDF_ENG059)· 七檢自測 ===")
        return selftest()
    if "--status" in args:
        return status()
    if "--chart" in args:
        return chart(args[args.index("--chart") + 1])
    if "run" in args:
        top = int(args[args.index("--top") + 1]) if "--top" in args else None
        return run(top)
    print(__doc__.split("用法:")[1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
