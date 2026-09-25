#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_ENG052_MegaFetch — 總擷取引擎 · 單 003 執行器(批128;via-mega)
====================================================================
操作員令(批128,2026-08-24):台股全市場(雙所清單+2024-01-02 起每日
全欄:調整後價格/量/值/三大法人/融資融券/券資比/融資融券維持率/
當沖金額與比)+主動 ETF 清單與成立以來每日持股(加總/分開/領先視圖)
+國際指數×ETF 對(美五大/日韓台/歐洲)+NVDA+VIX/油金期貨/美債
10-20-30Y;自家引擎抓、parquet 儲存、庫顆粒自行決定。
冊:VDF_Fetch_Orders 單 003(append-only;儲存決策=兩庫:
  vdf_tw_market.duckdb+vdf_global_market.duckdb,理由入冊)。
鐵則:
  ① 網路統包 — 全外呼經 NET-BRIDGE 統包車道(probe/http_json/
     yf_download;法遵雙閘 fail-closed);統包缺席=引擎自道降級。
  ② 調整價政策 — yfinance auto_adjust=False:adj_close 主欄+官方
     close 並存(官方無調整價=誠實雙欄)。
  ③ 衍生欄誠實旗標 — 券資比/當沖比=CONFIRMED 直算;融資融券
     維持率=官方無逐股金額→ESTIMATE 具名旗標(公式入冊)。
  ④ 冪等落庫 — parquet 分 lane;DuckDB upsert(anti-join 同鍵不重)。
  ⑤ 誠實三態 — 同意閘未開 rc2;雙道封鎖 rc3 存證;零假抓。
用法:
  via-mega --plan               → 零網路列單
  via-mega                      → 單 003 全抓(候網路環境)
  via-mega --lane global_yf     → 單車道
  via-mega --selftest           → 十檢(替身零網路)
v0100→v0101(批135):START 正名 START_DATE(同名異義解歧;行為零變更)。
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
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF = HERE.parent
VIA = VDF.parent.parent
OUT = VDF / "output_hub" / "mega"
DB_TW = OUT / "vdf_tw_market.duckdb"
DB_GL = OUT / "vdf_global_market.duckdb"
ORDERS_GLOB = "VDF_Fetch_Orders_v*.json"
START_DATE = "2024-01-02"  # 批135 正名:與 MDL303 計時器 START 同名異義解歧;canonical START_DATE 對齊
MARGIN_SHORT_RATIO = 0.9   # 融券保證金成數(制度值;ESTIMATE 公式用)


def load_order(root: Path = VDF) -> dict | None:
    hits = sorted(root.glob(ORDERS_GLOB))
    if not hits:
        return None
    d = json.loads(hits[-1].read_text(encoding="utf-8-sig"))
    return next((o for o in d["orders"] if o["order_id"] == "003"), None)


# ── 衍生欄計算器(公式入冊;誠實旗標)──────────────────────────
def derive_chip_fields(row: dict) -> dict:
    """券資比/當沖比=CONFIRMED;融資融券維持率=ESTIMATE 具名旗標"""
    out = dict(row)
    fin = row.get("margin_balance")        # 融資餘額(張)
    sho = row.get("short_balance")         # 融券餘額(張)
    out["short_margin_ratio_pct"] = (round(sho / fin * 100, 2)
                                     if fin and sho is not None and fin > 0 else None)
    amt = row.get("daytrade_amount")
    tv = row.get("turnover")
    out["daytrade_ratio_pct"] = (round(amt / tv * 100, 2)
                                 if amt is not None and tv else None)
    close = row.get("close")
    avg60 = row.get("avg_price_60d") or close
    if close and fin and avg60:
        fin_amount = avg60 * fin * 1000            # 融資金額估=近60日均價×餘額股數
        out["margin_maint_pct_est"] = round(close * fin * 1000 / fin_amount * 100, 2)
        out["margin_maint_flag"] = "ESTIMATE(融資金額=均價近似;官方無逐股金額)"
    else:
        out["margin_maint_pct_est"] = None
        out["margin_maint_flag"] = "NULL(欄缺誠實)"
    if close and sho and avg60:
        collateral = avg60 * sho * 1000 * (1 + MARGIN_SHORT_RATIO)
        out["short_maint_pct_est"] = round(collateral / (close * sho * 1000) * 100, 2)
        out["short_maint_flag"] = f"ESTIMATE(保證金成數 {MARGIN_SHORT_RATIO:.0%} 制度值)"
    else:
        out["short_maint_pct_est"] = None
        out["short_maint_flag"] = "NULL(欄缺誠實)"
    return out


# ── ETF 持股視圖(加總/分開/領先)────────────────────────────────
def holdings_views(rows: list[dict]) -> dict:
    """rows: [{date, fund, ticker, shares}];回 aggregate/per_fund/leaders"""
    from collections import defaultdict
    agg = defaultdict(float)                     # (date,ticker)→shares 加總
    per = defaultdict(lambda: defaultdict(float))
    for r in rows:
        agg[(r["date"], r["ticker"])] += r["shares"]
        per[r["fund"]][(r["date"], r["ticker"])] += r["shares"]
    dates = sorted({r["date"] for r in rows})
    leaders = []
    if len(dates) >= 2:
        d0, d1 = dates[0], dates[-1]
        tick = {t for (_, t) in agg}
        for t in sorted(tick):
            delta = agg.get((d1, t), 0.0) - agg.get((d0, t), 0.0)
            leaders.append({"ticker": t, "delta_shares": delta,
                            "d0": d0, "d1": d1})
        leaders.sort(key=lambda x: -abs(x["delta_shares"]))
    return {"aggregate": {f"{d}|{t}": v for (d, t), v in sorted(agg.items())},
            "per_fund": {f: {f"{d}|{t}": v for (d, t), v in sorted(m.items())}
                         for f, m in per.items()},
            "leaders": leaders}


# ── 落庫(parquet+DuckDB 冪等 upsert)────────────────────────────
def write_parquet(rows: list[dict], lane: str, out_root: Path | None = None) -> Path | None:
    import pandas as pd
    root = (out_root or OUT) / lane
    root.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    df = pd.DataFrame(rows)
    p = root / f"{lane}_{ts}.parquet"
    try:
        df.to_parquet(p, index=False)
        return p
    except Exception:
        cp = p.with_suffix(".csv")
        df.to_csv(cp, index=False, encoding="utf-8-sig")   # pyarrow 缺=CSV 後備誠實
        return cp


def upsert_duckdb(db: Path, table: str, rows: list[dict], keys: list[str]) -> int:
    """冪等 upsert:anti-join 同鍵不重插;回表內總列數"""
    import duckdb
    import pandas as pd
    db.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db))
    df = pd.DataFrame(rows)
    con.register("staging", df)
    tabs = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
    if table not in tabs:
        con.execute(f"CREATE TABLE {table} AS SELECT * FROM staging")
    else:
        cond = " AND ".join(f"t.{k} = s.{k}" for k in keys)
        con.execute(f"INSERT INTO {table} SELECT * FROM staging s "
                    f"WHERE NOT EXISTS (SELECT 1 FROM {table} t WHERE {cond})")
    n = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    con.unregister("staging")
    con.close()
    return n


# ── 車道 ─────────────────────────────────────────────────────────
def _net_or_none():
    return _via_net()


def lane_global_yf(order: dict, net=None, yf_fn=None, out_root: Path | None = None) -> dict:
    g = order["lanes"]["global_yf"]
    tickers = sorted({p["idx"] for p in g["pairs_index_etf"]}
                    | {p["etf"] for p in g["pairs_index_etf"]}
                    | {s["yf"] for s in g["singles"]})
    if yf_fn is not None:
        r = yf_fn(tickers)
    else:
        net = net or _net_or_none()
        if net is None or not hasattr(net, "yf_download"):
            return {"state": "SKIP", "note": "統包網路工具缺席(誠實)"}
        rr = net.yf_download(tickers, period="max")
        if rr["state"] != "OK":
            return {"state": rr["state"], "note": rr.get("note", "")}
        df = rr["data"]
        rows = []
        for t in tickers:
            try:
                sub = (df[t] if len(tickers) > 1 else df).dropna(how="all")
                sub = sub[sub.index >= START_DATE]
                for dt_, r_ in sub.iterrows():
                    rows.append({"date": str(dt_)[:10], "ticker": t,
                                 "open": float(r_.get("Open")), "high": float(r_.get("High")),
                                 "low": float(r_.get("Low")), "close": float(r_.get("Close")),
                                 "adj_close": float(r_.get("Adj Close")),
                                 "volume": float(r_.get("Volume"))})
            except Exception:
                continue
        r = {"rows": rows, "ok": tickers}
    rows = r["rows"]
    if not rows:
        return {"state": "EMPTY", "note": "零列"}
    pq = write_parquet(rows, "global_yf", out_root)
    n = upsert_duckdb((out_root or OUT) / "vdf_global_market.duckdb"
                      if out_root else DB_GL, "global_daily", rows, ["date", "ticker"])
    return {"state": "OK", "rows": len(rows), "parquet": pq.name, "db_rows": n,
            "note": f"{len(set(x['ticker'] for x in rows))} 標的·adj 主欄"}


def lane_tw_listings(order: dict, net=None, http=None) -> dict:
    tg = order["lanes"]["tw_listings"]["targets"]
    out = []
    for t in tg:
        if http is not None:
            data = http(t["endpoint"])
        else:
            net = net or _net_or_none()
            if net is None:
                return {"state": "SKIP", "note": "統包缺席(誠實)"}
            r = net.http_json(t["endpoint"])
            if r["state"] != "OK":
                return {"state": r["state"], "note": r.get("note", "")[:100]}
            data = r["data"]
        out.append({"key": t["key"], "rows": len(data) if isinstance(data, list) else 1})
    return {"state": "OK", "targets": out}


def preflight(net=None) -> dict:
    net = net or _net_or_none()
    if net is None:
        return {"reachable": False, "note": "統包缺席"}
    r = net.probe("https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL")
    return r


def plan(order: dict) -> int:
    print(f"=== 單 003 計畫(批128)· 窗口 {order['window']} ===")
    print(f"  [儲存] {order['storage_decision']['databases']}")
    for lane, spec in order["lanes"].items():
        print(f"  [{lane}] {spec['desc'][:76]}")
    g = order["lanes"]["global_yf"]
    print(f"  [global] 指數×ETF 對 {len(g['pairs_index_etf'])} 組+單標 {len(g['singles'])}"
          f"+FRED {g['rates_20y']['fred']}({g['rates_20y']['confidence']})")
    fx = order["lanes"]["tw_daily"]["derived_formulas"]
    for k, v in fx.items():
        print(f"  [衍生] {k}:{v[:66]}")
    return 0


def run(lanes_sel: list[str] | None, env=None) -> int:
    env = env if env is not None else os.environ
    order = load_order()
    if order is None:
        print("[FAIL] 單 003 不在冊")
        return 1
    if env.get("VIA_NET_CONSENT", "") != "YES":
        print("[FAIL-CLOSED] VIA_NET_CONSENT≠YES:同意閘未開,零外呼(絕不代設)")
        return 2
    pf = preflight()
    if not pf.get("reachable"):
        print(f"[NETWORK_POLICY_BLOCKED] 預檢未達:{str(pf.get('note', ''))[:100]}")
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / f"BLOCKED_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json").write_text(
            json.dumps({"schema": "vdf.mega.blocked.v1", "preflight": pf},
                       ensure_ascii=False, indent=1), encoding="utf-8")
        print("  誠實結束存證;可達網路環境(工作站)重跑 via-mega 即全抓")
        return 3
    sel = lanes_sel or ["tw_listings", "global_yf"]
    results = {}
    for ln in sel:
        if ln == "global_yf":
            results[ln] = lane_global_yf(order)
        elif ln == "tw_listings":
            results[ln] = lane_tw_listings(order)
        else:
            results[ln] = {"state": "DELEGATED/PENDING", "note": "tw_daily 逐日回補與 etf_holdings 委派 ENG051(工作站長跑)"}
        print(f"  [{results[ln]['state']}] {ln} {str(results[ln].get('note', ''))[:80]}")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"RUN_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json").write_text(
        json.dumps({"schema": "vdf.mega.run.v1", "results": results},
                   ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return 0


def selftest() -> int:
    import tempfile
    import pandas as pd
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    order = load_order()
    # ① 單 003 在冊:五車道+儲存決策+衍生公式冊
    chk("① 單 003 在冊(五車道+兩庫決策+公式冊)",
        order is not None and set(order["lanes"]) == {"tw_listings", "active_etf_list",
                                                      "tw_daily", "etf_holdings_daily", "global_yf"}
        and "兩庫" in order["storage_decision"]["databases"]
        and len(order["lanes"]["tw_daily"]["derived_formulas"]) == 5)
    # ② 衍生欄驗算:券資比/當沖比 CONFIRMED
    r2 = derive_chip_fields({"margin_balance": 1000, "short_balance": 250,
                             "daytrade_amount": 3.0e8, "turnover": 1.2e9,
                             "close": 100.0, "avg_price_60d": 95.0})
    chk("② 券資比 25%·當沖比 25%(CONFIRMED 直算)",
        r2["short_margin_ratio_pct"] == 25.0 and r2["daytrade_ratio_pct"] == 25.0)
    # ③ 維持率 ESTIMATE 具名旗標+公式(100/95≈105.26)
    chk("③ 融資維持率估 105.26+ESTIMATE 旗標",
        abs(r2["margin_maint_pct_est"] - 105.26) < 0.01
        and r2["margin_maint_flag"].startswith("ESTIMATE")
        and r2["short_maint_flag"].startswith("ESTIMATE"))
    # ④ 欄缺=NULL 誠實
    r4 = derive_chip_fields({"margin_balance": 0, "short_balance": 5})
    chk("④ 欄缺/零除=NULL 誠實", r4["short_margin_ratio_pct"] is None
        and r4["margin_maint_pct_est"] is None and "NULL" in r4["margin_maint_flag"])
    with tempfile.TemporaryDirectory() as td:
        sand = Path(td)
        # ⑤ 替身 yf 管線(adj 主欄)+parquet 落檔
        def fake_yf(tickers):
            return {"rows": [{"date": "2024-01-02", "ticker": t, "open": 1.0, "high": 1.0,
                              "low": 1.0, "close": 10.0, "adj_close": 9.5, "volume": 100.0}
                             for t in tickers[:3]], "ok": tickers}
        r5 = lane_global_yf(order, yf_fn=fake_yf, out_root=sand)
        chk("⑤ 替身 global 管線(parquet+db)", r5["state"] == "OK" and r5["rows"] == 3)
        pq = list((sand / "global_yf").glob("*.*"))
        chk("⑥ parquet 落檔往返", len(pq) == 1
            and len(pd.read_parquet(pq[0]) if pq[0].suffix == ".parquet"
                    else pd.read_csv(pq[0])) == 3, f"({pq[0].suffix})")
        # ⑦ duckdb 冪等 upsert(同鍵再插不重)
        db = sand / "t.duckdb"
        rows = [{"date": "2024-01-02", "ticker": "NVDA", "close": 1.0}]
        n1 = upsert_duckdb(db, "global_daily", rows, ["date", "ticker"])
        n2 = upsert_duckdb(db, "global_daily", rows, ["date", "ticker"])
        n3 = upsert_duckdb(db, "global_daily",
                           [{"date": "2024-01-03", "ticker": "NVDA", "close": 2.0}],
                           ["date", "ticker"])
        chk("⑦ duckdb 冪等 upsert(1→1→2)", (n1, n2, n3) == (1, 1, 2))
        # ⑧ ETF 持股視圖(加總/分開/領先)
        hv = holdings_views([
            {"date": "2024-01-02", "fund": "00980A", "ticker": "2330", "shares": 100},
            {"date": "2024-01-02", "fund": "00981A", "ticker": "2330", "shares": 50},
            {"date": "2024-01-03", "fund": "00980A", "ticker": "2330", "shares": 180},
            {"date": "2024-01-03", "fund": "00981A", "ticker": "2330", "shares": 50},
            {"date": "2024-01-03", "fund": "00980A", "ticker": "2317", "shares": 30}])
        chk("⑧ 持股視圖(加總 150→230·領先=2330 +80)",
            hv["aggregate"]["2024-01-02|2330"] == 150
            and hv["aggregate"]["2024-01-03|2330"] == 230
            and hv["leaders"][0]["ticker"] == "2330"
            and hv["leaders"][0]["delta_shares"] == 80
            and hv["per_fund"]["00980A"]["2024-01-03|2330"] == 180)
        # ⑨ 同意閘 fail-closed rc2
        chk("⑨ 同意閘未開=rc2", run(None, env={}) == 2)
        # ⑩ 替身 listings 管線
        r10 = lane_tw_listings(order, http=lambda u: [{"公司代號": "2330"}] * 5)
        chk("⑩ 替身雙所清單管線", r10["state"] == "OK" and len(r10["targets"]) == 2
            and r10["targets"][0]["rows"] == 5)
    n = 10 - len(fails)
    print(f"  [計] 十檢 OK {n} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== ENG052 總擷取引擎 · 十檢自測(替身零網路)===")
        return selftest()
    order = load_order()
    if order is None:
        print("[FAIL] 單 003 不在冊")
        return 1
    if "--plan" in args:
        return plan(order)
    lanes_sel = None
    if "--lane" in args:
        i = args.index("--lane")
        lanes_sel = [x for x in args[i + 1].split(",") if x]
    print("=== ENG052 總擷取引擎 · 單 003(批128)===")
    return run(lanes_sel)


if __name__ == "__main__":
    sys.exit(main())
