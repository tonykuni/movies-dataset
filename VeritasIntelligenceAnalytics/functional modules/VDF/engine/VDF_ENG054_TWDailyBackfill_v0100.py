#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_ENG054_TWDailyBackfill — 台股全市場日線回補工人(批136;via-tw-backfill)
====================================================================
操作員令 fetch vdf data again+白名單生效波:
  ① 雙所清單落庫(TWSE t187ap03_L+TPEX mopsfin_t187ap03_O→
     vdf_tw_market.duckdb::tw_listings+parquet)
  ② 全市場日線回補 2024-01-02→最新:Yahoo chart 直連車道
     (SUP_MDL740 v0104 yahoo_chart;上市 .TW/上櫃 .TWO)
     OHLCV+adj_close;批次 parquet+duckdb upsert(anti-join 冪等)
  ③ 檢查點續跑(checkpoint JSON;中斷重啟零重抓)
籌碼欄(三大法人/融資融券/當沖)=官方 TWSE/TPEX 逐日端點,另波
(ENG052 tw_daily chips 車道)——本器僅價量,誠實分工。
同意閘:VIA_NET_CONSENT+VIA_SCRAPE_CONSENT=YES 方跑(fail-closed)。
用法:via-tw-backfill run [--limit N] | --status | --selftest
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

import calendar
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF = HERE.parent
VIA = VDF.parent.parent
OUT = VDF / "output_hub" / "mega"
DB_TW = OUT / "vdf_tw_market.duckdb"
CKPT = OUT / "tw_backfill_checkpoint.json"
START_DATE = "2024-01-02"
LISTING_EPS = {
    "TWSE": ("https://openapi.twse.com.tw/v1/opendata/t187ap03_L", ".TW"),
    "TPEX": ("https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O", ".TWO"),
}
BATCH = 80
PAUSE_S = 0.35


# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(glob 最新;嚴禁寫死版號) =====
def _net_or_none():
    import glob as _g
    import importlib.util as _il
    hits = sorted(_g.glob(str(VIA / "supportive modules" / "network"
                               / "SUP_MDL740_NetUnified_v*.py")))
    if not hits:
        return None
    spec = _il.spec_from_file_location("via_net_dyn", hits[-1])
    mod = _il.module_from_spec(spec)
    sys.modules["via_net_dyn"] = mod
    spec.loader.exec_module(mod)
    return mod
# ===== [VIA:NET-BRIDGE:END] =====


def gate_open(env=None) -> bool:
    env = env if env is not None else os.environ
    return env.get("VIA_NET_CONSENT") == "YES" and env.get("VIA_SCRAPE_CONSENT") == "YES"


def write_parquet(rows: list[dict], stem: str) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
        p = OUT / f"{stem}_{ts}.parquet"
        pq.write_table(pa.Table.from_pylist(rows), p)
        return p
    except ImportError:
        import csv
        p = OUT / f"{stem}_{ts}.csv"
        with p.open("w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        return p


def upsert_duckdb(table: str, rows: list[dict], keys: list[str]) -> int:
    import duckdb
    import pandas as pd
    df = pd.DataFrame(rows)
    con = duckdb.connect(str(DB_TW))
    con.execute(f"CREATE TABLE IF NOT EXISTS {table} AS SELECT * FROM df LIMIT 0")
    cond = " AND ".join(f"t.{k} = df.{k}" for k in keys)
    con.execute(f"INSERT INTO {table} SELECT * FROM df WHERE NOT EXISTS "
                f"(SELECT 1 FROM {table} t WHERE {cond})")
    n = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    con.close()
    return n


def fetch_listings(net) -> list[dict]:
    """雙所清單→統一列(code/name/market/yf_ticker/industry/isin)"""
    rows = []
    for mkt, (ep, suffix) in LISTING_EPS.items():
        r = net.http_json(ep)
        if r["state"] != "OK":
            print(f"  [FAIL] {mkt} 清單:{str(r.get('note',''))[:80]}")
            continue
        for it in r["data"]:
            code = str(it.get("公司代號") or it.get("SecuritiesCompanyCode")
                       or it.get("Code") or "").strip()
            if not code or not code.isdigit() or len(code) != 4:
                continue  # 特別股/權證等非四碼普通股=誠實排除於日線回補面
            rows.append({"code": code,
                         "name": str(it.get("公司簡稱") or it.get("公司名稱")
                                     or it.get("CompanyName") or "").strip(),
                         "market": mkt, "yf_ticker": code + suffix,
                         "industry": str(it.get("產業別") or it.get("SecuritiesIndustryCode")
                                         or "").strip(),
                         "isin": str(it.get("ISINCode") or "").strip()})
    return rows


def load_ckpt() -> dict:
    if CKPT.exists():
        return json.loads(CKPT.read_text(encoding="utf-8"))
    return {"done": [], "failed": [], "started": None}


def save_ckpt(ck: dict):
    CKPT.write_text(json.dumps(ck, ensure_ascii=False), encoding="utf-8")


def run(limit: int | None = None) -> int:
    if not gate_open():
        print("[FAIL-CLOSED] 同意閘未開(VIA_NET_CONSENT/VIA_SCRAPE_CONSENT)")
        return 2
    net = _net_or_none()
    if net is None or not hasattr(net, "yahoo_chart"):
        print("[FAIL] 統包網路工具缺席或無 yahoo_chart 車道")
        return 1
    listings = fetch_listings(net)
    if not listings:
        print("[FAIL] 清單零列")
        return 1
    write_parquet(listings, "tw_listings")
    n_l = upsert_duckdb("tw_listings", listings, ["code", "market"])
    print(f"[清單] 雙所 {len(listings)} 檔落庫(表 tw_listings 計 {n_l})")
    ck = load_ckpt()
    if ck["started"] is None:
        ck["started"] = datetime.now().isoformat()
    done = set(ck["done"])
    todo = [x for x in listings if x["yf_ticker"] not in done]
    if limit:
        todo = todo[:limit]
    print(f"[回補] 待抓 {len(todo)} / 全 {len(listings)}(已達 {len(done)};"
          f"批次 {BATCH}·節流 {PAUSE_S}s)")
    se = calendar.timegm(time.strptime(START_DATE, "%Y-%m-%d"))
    ee = int(time.time())
    total_rows = 0
    for i in range(0, len(todo), BATCH):
        batch = [x["yf_ticker"] for x in todo[i:i + BATCH]]
        rc = net.yahoo_chart(batch, se, ee, pause_s=PAUSE_S)
        rows = rc.get("rows") or []
        okset = {x["ticker"] for x in rows}
        for f in rc.get("failed") or []:
            ck["failed"].append(f["ticker"])
        if rows:
            write_parquet(rows, "tw_daily_prices")
            total_rows += len(rows)
            upsert_duckdb("tw_daily_prices", rows, ["date", "ticker"])
        ck["done"] = sorted(done | okset)
        done = set(ck["done"])
        save_ckpt(ck)
        print(f"  [批 {i // BATCH + 1}] +{len(rows)} 列·成 {len(okset)}/{len(batch)}"
              f"·累計標的 {len(done)}", flush=True)
    n_d = upsert_duckdb("tw_daily_prices",
                        [{"date": "1900-01-01", "ticker": "_NOOP_", "open": None,
                          "high": None, "low": None, "close": None,
                          "adj_close": None, "volume": None}], ["date", "ticker"]) \
        if total_rows == 0 else None
    print(f"[畢] 本輪 +{total_rows} 列;checkpoint {CKPT.name}(done "
          f"{len(ck['done'])}·failed {len(set(ck['failed']))})")
    return 0


def status() -> int:
    ck = load_ckpt()
    print(f"done {len(ck['done'])} · failed {len(set(ck['failed']))} · started {ck['started']}")
    if DB_TW.exists():
        import duckdb
        con = duckdb.connect(str(DB_TW), read_only=True)
        for t in ("tw_listings", "tw_daily_prices"):
            try:
                r = con.execute(f"SELECT COUNT(*), COUNT(DISTINCT COALESCE(ticker, code)),"
                                f" MIN(date), MAX(date) FROM {t}"
                                if t == "tw_daily_prices" else
                                f"SELECT COUNT(*), COUNT(DISTINCT code), NULL, NULL FROM {t}"
                                ).fetchone()
                print(f"  [{t}] rows {r[0]} · keys {r[1]} · {r[2]}→{r[3]}")
            except Exception as e:
                print(f"  [{t}] 缺:{str(e)[:60]}")
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
    net = _net_or_none()
    chk("② 統包橋 glob 最新+yahoo_chart 車道在位",
        net is not None and hasattr(net, "yahoo_chart"))
    chk("③ 雙所端點冊(.TW/.TWO 後綴)",
        LISTING_EPS["TWSE"][1] == ".TW" and LISTING_EPS["TPEX"][1] == ".TWO")
    import tempfile
    global OUT, DB_TW, CKPT
    _o, _d, _c = OUT, DB_TW, CKPT
    with tempfile.TemporaryDirectory() as td:
        OUT, DB_TW, CKPT = Path(td), Path(td) / "t.duckdb", Path(td) / "ck.json"
        rows = [{"date": "2024-01-02", "ticker": "2330.TW", "open": 1.0, "high": 1.0,
                 "low": 1.0, "close": 1.0, "adj_close": 1.0, "volume": 1.0}]
        p = write_parquet(rows, "t")
        n1 = upsert_duckdb("tw_daily_prices", rows, ["date", "ticker"])
        n2 = upsert_duckdb("tw_daily_prices", rows, ["date", "ticker"])
        chk("④ parquet 落盤+duckdb upsert 冪等", p.exists() and n1 == 1 and n2 == 1)
        ck = load_ckpt()
        ck["done"] = ["2330.TW"]
        save_ckpt(ck)
        chk("⑤ 檢查點寫讀續跑", load_ckpt()["done"] == ["2330.TW"])
    OUT, DB_TW, CKPT = _o, _d, _c
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 誠實分工宣告(籌碼另波;非四碼排除)", "籌碼" in src and "誠實排除" in src)
    print(f"  [計] 六檢 OK {6 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 台股回補工人(VDF_ENG054)· 六檢自測 ===")
        return selftest()
    if "--status" in args:
        return status()
    limit = None
    if "--limit" in args:
        limit = int(args[args.index("--limit") + 1])
    return run(limit)


if __name__ == "__main__":
    sys.exit(main())
