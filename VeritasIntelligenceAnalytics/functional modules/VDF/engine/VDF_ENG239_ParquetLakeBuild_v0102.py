#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG239_ParquetLakeBuild v0102 — 薄尾:② 入湖補「晚到的舊日期列」(PR 631 審查 P1)。

v0100 的 ② 對日期表用「整張表湖內最大日期」當水位,只收水位之後的列。回補引擎(ENG064)補的是缺鍵、含舊日期,
族群也可新增成員(例:TW_FIN 加 3017)→ 新成員 2022 起的歷史日期都 ≤ 水位,被永遠漏掉(湖少列、VIEW 少列,沒有任何燈)。
本版在 v0100 / v0101 原樣入湖之後,對每張已有分片的日期表多跑一趟「鍵差」:
  鍵 = 日期欄 + 識別欄(code · ticker · market · source · series … 見 KEY_COLS);來源有、湖沒有的鍵(日期 >= 起始日)
  → 另寫一個 part-<時間>-late.parquet(只增 · 追 _manifest 一行 late_keys)。
已在湖裡的鍵不重寫(值的修正照 v0100 原行為不入湖,不製造同鍵兩版);沒有識別欄的表,鍵 = 日期(總經單序列補舊日期也收)。
其餘(⓪ 全族群 · ① 回補 · ③ 管家 VIEW · status)照 v0101 / v0100 一字不變。
用法同 v0101:py VDF_ENG239_ParquetLakeBuild_v0102.py run --all [--start 2022-01-01] [--jobs 5] · --selftest
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

import importlib.util
import json
import re
import sys
from pathlib import Path

VERSION = "v0102"
STEM = "VDF_ENG239_ParquetLakeBuild"
HERE = Path(__file__).resolve().parent


def _vnum_v0102(p) -> int:
    m = re.search(r"_v(\d{4})\.py$", str(p))
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum_v0102(p) < 102), key=_vnum_v0102)
_spec = importlib.util.spec_from_file_location(STEM + "_prior_for_v0102", PRIOR_PATH)
P1 = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = P1
_spec.loader.exec_module(P1)
P0 = getattr(P1, "P", P1)                     # v0101 是薄尾 → 本體 v0100 在 P1.P
VIA = P0.VIA
_INGEST_BEFORE_V0102 = P0.ingest
KEY_COLS = ("code", "ticker", "symbol", "stock_id", "market", "source", "src", "series", "series_id", "indicator", "country",
            "region", "ym", "etf_ticker", "holding_ticker", "yf_ticker", "etf_yf_ticker", "holding_yf_ticker", "portfolio_date")


def _q(c: str) -> str:
    return '"' + c.replace('"', '""') + '"'


def late_rows(lake: Path, start: str, dbs: list) -> dict:
    """鍵差:來源有、湖沒有的鍵(日期 >= start)→ 另寫 late 分片。回 {(db 名, 表): 列數 | 錯誤字串}。"""
    import duckdb
    out = {}
    for db in dbs:
        try:
            src = duckdb.connect(str(db), read_only=True)
        except Exception as e:  # noqa: BLE001 — 開不了的庫 v0100 已照實記 SKIP;這裡只留痕
            out[(db.name, "*")] = "SKIP " + str(e)[:80]
            continue
        try:
            tables = [r[0] for r in src.execute("select table_name from information_schema.tables where table_type='BASE TABLE' and table_schema='main'").fetchall()]
            for t in tables:
                cols = [r[0] for r in src.execute(f"describe {_q(t)}").fetchall()]
                dc = P0._date_col(cols)
                tdir = lake / P0.safe(db.stem) / P0.safe(t)
                parts = sorted(tdir.glob("part-*.parquet")) if dc else []
                if not parts:
                    continue
                glob = f"{tdir.as_posix()}/*.parquet"
                try:
                    lake_cols = {r[0] for r in src.execute(f"describe select * from read_parquet('{glob}', union_by_name=true)").fetchall()}
                    keys = [dc] + [c for c in cols if c != dc and c.lower() in KEY_COLS and c in lake_cols]
                    on = " and ".join(f"s.{_q(k)} is not distinct from l.{_q(k)}" for k in keys)
                    q = (f"select s.* from {_q(t)} s where try_cast(s.{_q(dc)} as date) >= DATE '{start}' and not exists "
                         f"(select 1 from read_parquet('{glob}', union_by_name=true) l where {on})")
                    n = src.execute(f"select count(*) from ({q})").fetchone()[0]
                    if n:
                        part = tdir / f"part-{P0.now_utc()}-late.parquet"
                        src.execute(f"copy ({q}) to '{part.as_posix()}' (format parquet, compression zstd)")
                        P0._manifest(lake, {"at": P0.now_utc(), "db": db.name, "table": t, "part": part.name, "rows": n, "date_col": dc,
                                            "late_keys": keys, "from": start})
                    out[(db.name, t)] = n
                except Exception as e:  # noqa: BLE001 — 照實記錯,不冒充補齊
                    out[(db.name, t)] = f"ERROR {str(e)[:120]}"
        finally:
            src.close()
    return out


def ingest(lake: Path, start: str, dbs: list) -> list:
    res = _INGEST_BEFORE_V0102(lake, start, dbs)
    late = late_rows(lake, start, dbs)
    for r in res:
        k = (r.get("db"), r.get("table"))
        if k not in late:
            continue
        v = late[k]
        if isinstance(v, str) and v.startswith("SKIP"):
            continue
        if isinstance(v, str):
            r["state"], r["note"] = "ERROR", "鍵差 " + v
        elif v:
            r["rows_new"] = r.get("rows_new", 0) + v
            r["late_rows"] = v
            r["state"] = "APPEND"
    return res


P0.ingest = ingest                            # v0100 run() 依模組全域名找 ingest → 本版接手(⓪ ① ③ 不動)
run = P1.run


def __getattr__(name):
    """尾版律 TAILAPI:前版公開名稱(catalog · fetch · fetch_all · find_dbs · now_utc · safe · status …)經本檔轉接。"""
    for mod in (P1, P0):                      # v0101 薄尾沒轉接 → 再往本體 v0100 找
        if hasattr(mod, name):
            return getattr(mod, name)
    raise AttributeError(f"{STEM} {VERSION}:前版鏈沒有 {name}")


def selftest() -> int:
    import tempfile
    import duckdb
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        db = td / "vdf_tw_market.duckdb"
        c = duckdb.connect(str(db))
        c.execute("create table tw_daily_prices(ticker varchar, date date, close double)")
        c.execute("insert into tw_daily_prices values ('2330','2022-01-03',615),('2330','2026-11-13',1110)")
        c.execute("create table us_macro(date date, v double)")
        c.execute("insert into us_macro values ('2026-10-01',1.0)")
        c.close()
        lake = td / "lake"
        r1 = {x["table"]: x["rows_new"] for x in ingest(lake, "2022-01-01", [db])}
        chk("① 首輪照 v0100 全收(2 + 1)", r1 == {"tw_daily_prices": 2, "us_macro": 1}, r1)
        c = duckdb.connect(str(db))
        c.execute("insert into tw_daily_prices values ('3017','2022-01-03',50),('3017','2026-11-12',900),('3017','2026-11-13',910)")
        c.execute("insert into us_macro values ('2025-01-01',0.5)")
        c.execute("update tw_daily_prices set close=1111 where ticker='2330' and date='2026-11-13'")
        c.close()
        r2 = ingest(lake, "2022-01-01", [db])
        m2 = {x["table"]: (x["state"], x["rows_new"], x.get("late_rows")) for x in r2}
        chk("② 新成員 3017 的舊日期(≤ 水位)補進湖 3 列 · 總經單序列補舊日期 1 列", m2 == {"tw_daily_prices": ("APPEND", 3, 3), "us_macro": ("APPEND", 1, 1)}, m2)
        r3 = ingest(lake, "2022-01-01", [db])
        chk("③ 重跑零新列(鍵差只補一次)", all(x["rows_new"] == 0 and x["state"] == "UPTODATE" for x in r3), r3)
        con = duckdb.connect()
        n = con.execute(f"select count(*) from read_parquet('{(lake / 'vdf_tw_market' / 'tw_daily_prices').as_posix()}/*.parquet')").fetchone()[0]
        n2330 = con.execute(f"select count(*) from read_parquet('{(lake / 'vdf_tw_market' / 'tw_daily_prices').as_posix()}/*.parquet') where ticker='2330'").fetchone()[0]
        con.close()
        chk("④ 湖內 5 列 · 2330 值修正不重寫(不製造同鍵兩版)", n == 5 and n2330 == 2, (n, n2330))
        man = [json.loads(x) for x in (lake / "_manifest.jsonl").read_text(encoding="utf-8").splitlines()]
        chk("⑤ late 分片各追一行 manifest(帶鍵欄)", sum(1 for x in man if x.get("late_keys")) == 2
            and any(x.get("late_keys") == ["date", "ticker"] for x in man), man[-2:])
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 不代設同意閘 · 不用 TA-Lib · 不刪分片", "environ[\"VIA_NET" + "_CONSENT\"] =" not in src and "import " + "talib" not in src
        and "part.unlink" + "()" not in src)
    print(f"  前版鏈 {PRIOR_PATH.name} selftest ↓")
    keep = P0.ingest
    P0.ingest = _INGEST_BEFORE_V0102          # 前版鏈自測照前版原行為跑
    try:
        prior_rc = P1.selftest()
    finally:
        P0.ingest = keep
    chk("⑦ 前版鏈 v0101 → v0100 自測照過", prior_rc == 0, prior_rc)
    print(f"[selftest] {STEM} {VERSION} {sum(ok)}/{len(ok)}")
    return 0 if all(ok) else 1


def main() -> int:
    a = sys.argv[1:]
    if a and a[0] == "--selftest":
        return selftest()
    if a and a[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    return P1.main()


if __name__ == "__main__":
    sys.exit(main())
