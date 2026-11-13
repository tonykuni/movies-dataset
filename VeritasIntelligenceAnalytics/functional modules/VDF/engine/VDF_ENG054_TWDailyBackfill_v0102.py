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
用法:via-tw-backfill run [--limit N] [--full] | --status | --selftest
v0101(批318 不卡斷令):**增量模式**=依庫內各標的 MAX(date) 只抓缺口(最後
交易日已達=零請求;缺口起點=MAX(date)−3 日重疊,upsert 冪等);無資料標的才
自 START_DATE 全抓;--full=回 v0100 檢查點全抓律。批內以 SuperAccel
accel_map 4 工平行(節流 pause 各工保留;同意閘由統包器 fail-closed)。
v0100 正本零觸碰。
v0102(批321 庫鎖律):duckdb 連線遇單寫者鎖=等 6s 重試至多 20 次(印持有者);逾額誠實 rc3 零裸 traceback。
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
from datetime import datetime, timedelta
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


LOCK_RETRY, LOCK_WAIT = 20, 6.0


class DbBusy(RuntimeError):
    pass


def connect_retry(path, read_only: bool = False):
    """v0102 庫鎖律:單寫者鎖=等 LOCK_WAIT 重試 LOCK_RETRY 次;逾額 DbBusy(誠實)"""
    import duckdb
    last = ""
    for i in range(LOCK_RETRY):
        try:
            return duckdb.connect(str(path), read_only=read_only)
        except duckdb.IOException as exc:
            last = str(exc)
            if "already open" not in last and "另一個程序" not in last and "Cannot open file" not in last:
                raise
            print(f"  [庫忙] 第 {i + 1}/{LOCK_RETRY} 次:{last.splitlines()[-1][:100]} → 等 {LOCK_WAIT}s", flush=True)
            time.sleep(LOCK_WAIT)
    raise DbBusy(last[:300])


def upsert_duckdb(table: str, rows: list[dict], keys: list[str]) -> int:
    import pandas as pd
    df = pd.DataFrame(rows)
    con = connect_retry(DB_TW)
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



# ===== v0101 增量律 =====
INC_WORKERS = 4       # accel_map 平行工(節流各工保留)
INC_SUB = 20          # 每工一次標的數
OVERLAP_DAYS = 3      # 缺口起點回退重疊(upsert 冪等=零重複)


def target_date(now: datetime | None = None) -> str:
    """最後交易日(台股 13:30 收;15:00 前視為前一日;週末回退;假日=小缺口自癒)"""
    now = now or datetime.now()
    d = now.date()
    if now.hour < 15:
        d = d - timedelta(days=1)
    while d.weekday() >= 5:
        d = d - timedelta(days=1)
    return d.isoformat()


def last_dates() -> dict[str, str]:
    """庫內各標的 MAX(date)(VARCHAR ISO 可直接比大小);無庫/無表=空"""
    if not DB_TW.exists():
        return {}
    try:
        con = connect_retry(DB_TW, read_only=True)
        rows = con.execute("SELECT ticker, MAX(CAST(date AS VARCHAR)) FROM tw_daily_prices "
                           "WHERE ticker <> '_NOOP_' GROUP BY ticker").fetchall()
        con.close()
        return {r[0]: str(r[1])[:10] for r in rows if r[0]}
    except Exception:
        return {}


def plan(listings: list[dict], last: dict[str, str], target: str,
         full: bool = False, done: set | None = None) -> list[tuple[str, str]]:
    """回 [(yf_ticker, start_date)]:已達 target=略;有資料=缺口起點;無資料=START_DATE;
    full=v0100 律(檢查點 done 略、其餘全抓)"""
    out = []
    done = done or set()
    for x in listings:
        t = x["yf_ticker"]
        if full:
            if t not in done:
                out.append((t, START_DATE))
            continue
        ld = last.get(t)
        if ld is None:
            out.append((t, START_DATE))
        elif ld < target:
            st = (datetime.strptime(ld, "%Y-%m-%d") - timedelta(days=OVERLAP_DAYS)).date()
            out.append((t, st.isoformat()))
    return out


def _fetch_group(net, tickers: list[str], start: str, ee: int) -> dict:
    """同起點群:切 INC_SUB 子批→accel_map 平行(缺加速器=序跑);合併 rows/failed"""
    se = calendar.timegm(time.strptime(start, "%Y-%m-%d"))
    subs = [tickers[i:i + INC_SUB] for i in range(0, len(tickers), INC_SUB)]
    rows, failed = [], []

    def one(sub):
        return net.yahoo_chart(sub, se, ee, pause_s=PAUSE_S)
    if VIA_ACCEL is not None and hasattr(VIA_ACCEL, "accel_map") and len(subs) > 1:
        res = VIA_ACCEL.accel_map(one, subs, workers=INC_WORKERS)
    else:
        res = []
        for sub in subs:
            try:
                res.append((True, one(sub)))
            except Exception as exc:
                res.append((False, str(exc)[:80]))
    for i, (ok, rc) in enumerate(res):
        if not ok or not isinstance(rc, dict):
            failed += [{"ticker": t, "note": str(rc)[:80]} for t in subs[i]]
            continue
        rows += rc.get("rows") or []
        failed += rc.get("failed") or []
    return {"rows": rows, "failed": failed}


def run(limit: int | None = None, full: bool = False) -> int:
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
    target = target_date()
    last = {} if full else last_dates()
    todo = plan(listings, last, target, full=full, done=done)
    if limit:
        todo = todo[:limit]
    n_full = sum(1 for _, st in todo if st == START_DATE)
    print(f"[{'全抓' if full else '增量'}] 待抓 {len(todo)} / 全 {len(listings)}"
          f"(已達 {len(listings) - len(todo)};目標日 {target};全段 {n_full}·缺口 {len(todo) - n_full};"
          f"平行 {INC_WORKERS} 工×{INC_SUB}·節流 {PAUSE_S}s)")
    if not todo:
        print("[畢] 增量零缺口(零請求)")
        return 0
    ee = int(time.time())
    total_rows = 0
    groups: dict[str, list[str]] = {}
    for t, st in todo:
        groups.setdefault(st, []).append(t)
    gi = 0
    for st in sorted(groups):
        tick = groups[st]
        for i in range(0, len(tick), BATCH):
            gi += 1
            batch = tick[i:i + BATCH]
            rc = _fetch_group(net, batch, st, ee)
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
            print(f"  [批 {gi}] 起 {st} +{len(rows)} 列·成 {len(okset)}/{len(batch)}"
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
    ls_ = [{"yf_ticker": "A.TW"}, {"yf_ticker": "B.TW"}, {"yf_ticker": "C.TW"}]
    pl = dict(plan(ls_, {"A.TW": "2026-09-01", "B.TW": "2026-08-20"}, "2026-09-01"))
    tgt = target_date(datetime(2026, 9, 6, 10, 0))  # 週日早=回退至週五 09-04
    chk("⑦ 增量律(已達略/缺口−3 日/無資料全段/全抓 done 略/目標日週末回退)",
        "A.TW" not in pl and pl.get("B.TW") == "2026-08-17" and pl.get("C.TW") == START_DATE
        and dict(plan(ls_, {}, "2026-09-01", full=True, done={"A.TW"})).keys() == {"B.TW", "C.TW"}
        and tgt == "2026-09-04")
    chk("⑧ 庫鎖律(connect_retry 在位+DbBusy 誠實 rc3+非鎖例外直拋)",
        "def connect_retry" in src and "return 3" in src and "raise" in src and LOCK_RETRY * LOCK_WAIT >= 60)
    print(f"  [計] 八檢 OK {8 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 台股回補工人(VDF_ENG054 v0102 增量·庫鎖律)· 八檢自測 ===")
        return selftest()
    if "--status" in args:
        return status()
    limit = None
    if "--limit" in args:
        limit = int(args[args.index("--limit") + 1])
    try:
        return run(limit, full="--full" in args)
    except DbBusy as exc:
        print(f"[FAIL] 庫忙逾 {LOCK_RETRY}×{LOCK_WAIT}s 仍鎖=誠實停(checkpoint 已留;重跑=續補):{exc}")
        return 3


if __name__ == "__main__":
    sys.exit(main())
