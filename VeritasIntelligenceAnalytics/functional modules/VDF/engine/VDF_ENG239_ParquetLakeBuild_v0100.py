#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG239_ParquetLakeBuild v0100 — VDF 自 2022-01-01 起擷取 → Parquet 資料庫(DuckDB 管家)一支跑完。

操作員令(2026-11-13):「給我一個指令能成功跑 VDF 取 2022-01-01~最新的數據建立 PARQUET 資料庫」
「確認資料庫管理有無導入 DUCKDB 去管理 PARQUET 格式儲存的檔案」。

run 三步(VDF 自己的程式,不讀 VCGC 支援工具;政策 L131):
  ① 擷取:呼叫 VDF 自己的歷史回補引擎 VDF_ENG064_HistoryBackfill 尾版 `run --start <起> --end <今天>`
     (台股 tw_daily_prices + 全球 global_daily;只補缺鍵、斷點續跑、由新到舊)。
     出網要操作員在自己的視窗開兩道同意閘(VIA_NET_CONSENT=YES · VIA_SCRAPE_CONSENT=YES);本引擎不代設。
     閘沒開 → 回補引擎照例拒抓,本引擎照實記「擷取被閘擋」,仍用庫內現有資料續做 ②③(不冒充已抓)。
  ② 入湖:掃 VDF 的 DuckDB 庫(functional modules/VDF/output_hub/**.duckdb · VIA_Reports/vdf_fetch/**.duckdb),
     每張表寫成 Parquet(zstd):<湖>/<庫>/<表>/part-<UTC>.parquet。
     有日期欄的表只收 >= 起始日,且只增:只寫比湖內最新日期更新的列(重跑 = 零新分片);
     沒日期欄的表:內容指紋變了才寫一個新分片(快照)。每個新分片追一行 _manifest.jsonl。
  ③ 管家:<湖>/VDF_catalog.duckdb 每表一個 VIEW v_<庫>__<表> = read_parquet(<夾>/*.parquet, union_by_name)
     (日期表取全部分片;快照表只取最新分片)。讀側一律用 DuckDB 掃 Parquet,不複製資料。
status:每表 列數 · 最早 / 最晚日期 · 分片數 · 距今天數 → 印出 + <湖>/LAKE_STATUS_latest.json。
預設湖位置:<VIA>/VIA_Reports/vdf_lake(不入版控)。不用 TA-Lib · 不寫同意閘 · 不刪任何分片。
用法:py VDF_ENG239_ParquetLakeBuild_v0100.py run [--start 2022-01-01] [--end YYYY-MM-DD] [--skip-fetch] [--lake <夾>] [--limit N]
      py VDF_ENG239_ParquetLakeBuild_v0100.py status [--lake <夾>] · --selftest
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
# [VIA:NET-BRIDGE] 留名:本檔不直接出網;擷取由 VDF_ENG064(經網路工具 · 雙同意閘)負責
import datetime as _dt
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

VERSION = "v0100"
STEM = "VDF_ENG239_ParquetLakeBuild"
HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent.parent
DEFAULT_LAKE = VIA / "VIA_Reports" / "vdf_lake"
DB_GLOBS = [(VIA / "functional modules" / "VDF" / "output_hub", "**/*.duckdb"), (VIA / "VIA_Reports" / "vdf_fetch", "**/*.duckdb")]
DATE_COLS = ("date", "trade_date", "dt", "as_of", "period_end", "日期", "Date")
START_DEFAULT = "2022-01-01"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})\.py$", str(p))
    return int(m.group(1)) if m else -1


def now_utc() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def safe(name: str) -> str:
    return re.sub(r"[^0-9A-Za-z_]+", "_", name).strip("_") or "x"


# ───────── ① 擷取 ─────────
def fetch(start: str, end: str, limit: int | None) -> dict:
    eng = sorted((VIA / "functional modules" / "VDF" / "engine").glob("VDF_ENG064_HistoryBackfill_v*.py"), key=_vnum)
    if not eng:
        return {"state": "ABSENT", "note": "找不到 VDF_ENG064_HistoryBackfill"}
    gates = {k: os.environ.get(k, "") for k in ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT")}
    args = [sys.executable, str(eng[-1]), "run", "--start", start, "--end", end] + (["--limit", str(limit)] if limit else [])
    env = dict(os.environ, VIA_FROM_VCGC=os.environ.get("VIA_FROM_VCGC", "YES"), PYTHONUTF8="1")
    print(f"[①擷取] {eng[-1].name} run --start {start} --end {end} · 同意閘 {gates}", flush=True)
    p = subprocess.run(args, env=env, cwd=str(VIA))
    gated = not all(v.upper() == "YES" for v in gates.values())
    state = "GATED" if gated else ("OK" if p.returncode == 0 else "PARTIAL")
    return {"state": state, "rc": p.returncode, "engine": eng[-1].name, "gates": gates,
            "note": "同意閘沒開 → 回補引擎拒抓;湖用庫內現有資料" if gated else ""}


# ───────── ② 入湖 ─────────
def find_dbs(extra: list | None = None) -> list:
    out = []
    for base, pat in DB_GLOBS + [(Path(e), "**/*.duckdb") for e in (extra or [])]:
        if base.is_dir():
            out += [p for p in base.glob(pat) if p.is_file() and ".wal" not in p.name]
    return sorted(set(out))


def _date_col(cols: list) -> str | None:
    low = {c.lower(): c for c in cols}
    for c in DATE_COLS:
        if c.lower() in low:
            return low[c.lower()]
    return None


_MEM = None


def _mem():
    """一條記憶體內 DuckDB 連線(新舊版 DuckDB 都用 execute().fetchone(),不用 relation)。"""
    global _MEM
    if _MEM is None:
        import duckdb
        _MEM = duckdb.connect()
    return _MEM


def _manifest(lake: Path, row: dict):
    with open(lake / "_manifest.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")


def ingest(lake: Path, start: str, dbs: list) -> list:
    import duckdb
    lake.mkdir(parents=True, exist_ok=True)
    res = []
    for db in dbs:
        try:
            src = duckdb.connect(str(db), read_only=True)
        except Exception as e:  # noqa: BLE001 — 鎖住 / 損壞的庫照實記
            res.append({"db": db.name, "table": "*", "state": "SKIP", "note": f"開不了:{str(e)[:80]}"})
            continue
        try:
            tables = [r[0] for r in src.execute("select table_name from information_schema.tables where table_type='BASE TABLE' and table_schema='main'").fetchall()]
            for t in tables:
                cols = [r[0] for r in src.execute(f'describe "{t}"').fetchall()]
                dc = _date_col(cols)
                tdir = lake / safe(db.stem) / safe(t)
                tdir.mkdir(parents=True, exist_ok=True)
                parts = sorted(tdir.glob("part-*.parquet"))
                part = tdir / f"part-{now_utc()}.parquet"
                if dc:
                    lake_max = None
                    if parts:
                        lake_max = _mem().execute(f"select max(cast(\"{dc}\" as date)) from read_parquet('{tdir.as_posix()}/*.parquet', union_by_name=true)").fetchone()[0]
                    lo = max(_dt.date.fromisoformat(start), lake_max + _dt.timedelta(days=1)) if lake_max else _dt.date.fromisoformat(start)
                    q = f'select * from "{t}" where try_cast("{dc}" as date) >= DATE \'{lo.isoformat()}\''
                    n = src.execute(f"select count(*) from ({q})").fetchone()[0]
                    if n:
                        src.execute(f"copy ({q}) to '{part.as_posix()}' (format parquet, compression zstd)")
                        _manifest(lake, {"at": now_utc(), "db": db.name, "table": t, "part": part.name, "rows": n, "date_col": dc, "from": lo.isoformat()})
                    res.append({"db": db.name, "table": t, "state": "APPEND" if n else "UPTODATE", "rows_new": n, "date_col": dc, "from": lo.isoformat()})
                else:
                    tmp = tdir / f".probe-{now_utc()}.parquet"
                    src.execute(f'copy (select * from "{t}") to \'{tmp.as_posix()}\' (format parquet, compression zstd)')
                    n = _mem().execute(f"select count(*) from read_parquet('{tmp.as_posix()}')").fetchone()[0]
                    fp = hashlib.sha256(json.dumps(_mem().execute(f"select * from read_parquet('{tmp.as_posix()}') order by all").fetchall(), default=str).encode()).hexdigest()
                    last_fp = None
                    if parts:
                        last_fp = hashlib.sha256(json.dumps(_mem().execute(f"select * from read_parquet('{parts[-1].as_posix()}') order by all").fetchall(), default=str).encode()).hexdigest()
                    if fp != last_fp:
                        tmp.rename(part)
                        _manifest(lake, {"at": now_utc(), "db": db.name, "table": t, "part": part.name, "rows": n, "date_col": None, "snapshot": True})
                        res.append({"db": db.name, "table": t, "state": "SNAPSHOT", "rows_new": n})
                    else:
                        tmp.unlink()
                        res.append({"db": db.name, "table": t, "state": "UPTODATE", "rows_new": 0})
        finally:
            src.close()
    return res


# ───────── ③ 管家 ─────────
def catalog(lake: Path) -> Path:
    import duckdb
    cat = lake / "VDF_catalog.duckdb"
    con = duckdb.connect(str(cat))
    try:
        for dbdir in sorted(p for p in lake.iterdir() if p.is_dir() and not p.name.startswith(".")):
            for tdir in sorted(p for p in dbdir.iterdir() if p.is_dir()):
                parts = sorted(tdir.glob("part-*.parquet"))
                if not parts:
                    continue
                cols = [r[0] for r in _mem().execute(f"describe select * from read_parquet('{parts[-1].as_posix()}')").fetchall()]
                src = f"'{tdir.as_posix()}/*.parquet'" if _date_col(cols) else f"'{parts[-1].as_posix()}'"
                con.execute(f'create or replace view "v_{dbdir.name}__{tdir.name}" as select * from read_parquet({src}, union_by_name=true)')
    finally:
        con.close()
    return cat


def status(lake: Path, write: bool = True) -> dict:
    import duckdb
    cat = lake / "VDF_catalog.duckdb"
    if not cat.is_file():
        print(f"[VDF 湖] 還沒有目錄 {cat};先跑 run")
        return {"state": "NODATA", "tables": []}
    con = duckdb.connect(str(cat), read_only=True)
    rows = []
    today = _dt.date.today()
    try:
        for (v,) in con.execute("select view_name from duckdb_views() where not internal order by 1").fetchall():
            cols = [r[0] for r in con.execute(f'describe "{v}"').fetchall()]
            dc = _date_col(cols)
            n = con.execute(f'select count(*) from "{v}"').fetchone()[0]
            lo = hi = None
            if dc:
                lo, hi = con.execute(f'select min(try_cast("{dc}" as date)), max(try_cast("{dc}" as date)) from "{v}"').fetchone()
            db, _, t = v[2:].partition("__")
            nparts = len(list((lake / db / t).glob("part-*.parquet")))
            rows.append({"view": v, "rows": n, "date_col": dc, "min_date": str(lo) if lo else None, "max_date": str(hi) if hi else None,
                         "lag_days": (today - hi).days if hi else None, "parts": nparts})
    finally:
        con.close()
    out = {"engine": f"{STEM} {VERSION}", "at": now_utc(), "lake": str(lake), "catalog": str(cat), "tables": rows}
    if write:
        (lake / "LAKE_STATUS_latest.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8")
    print(f"[VDF 湖] {lake} · 目錄 {cat.name} · {len(rows)} 張表")
    for r in rows:
        print(f"  {r['view']:<58} 列 {r['rows']:>10,} · {r['min_date'] or '—'} → {r['max_date'] or '—'} · 分片 {r['parts']}"
              + (f" · 落後 {r['lag_days']} 天" if r["lag_days"] is not None else ""))
    return out


def run(argv: list) -> int:
    def opt(k, d=None):
        return argv[argv.index(k) + 1] if k in argv and argv.index(k) + 1 < len(argv) else d
    start = opt("--start", START_DEFAULT)
    end = opt("--end", _dt.date.today().isoformat())
    lake = Path(opt("--lake") or DEFAULT_LAKE)
    print(f"[VDF {STEM} {VERSION}] 起 {start} · 迄 {end} · 湖 {lake}", flush=True)
    f = {"state": "SKIPPED"} if "--skip-fetch" in argv else fetch(start, end, int(opt("--limit")) if opt("--limit") else None)
    print(f"[①擷取] {f['state']} {f.get('note', '')}", flush=True)
    res = ingest(lake, start, find_dbs())
    new = sum(r.get("rows_new", 0) for r in res)
    print(f"[②入湖] 庫內 {len({r['db'] for r in res})} 個 DuckDB · {len(res)} 張表 · 新寫 {new:,} 列 · "
          f"{sum(1 for r in res if r['state'] in ('APPEND', 'SNAPSHOT'))} 個新分片", flush=True)
    cat = catalog(lake)
    print(f"[③管家] {cat}", flush=True)
    st = status(lake)
    lamp = "RED" if not st["tables"] else ("YELLOW" if f["state"] in ("GATED", "PARTIAL", "ABSENT") else "GREEN")
    print(f"[VDF 湖] {lamp} · 擷取 {f['state']} · 表 {len(st['tables'])}" + (" · 擷取沒跑成,湖只含庫內現有資料" if lamp == "YELLOW" else ""))
    return {"GREEN": 0, "YELLOW": 2, "RED": 1}[lamp]


def selftest() -> int:
    import duckdb
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        db = td / "vdf_tw_market.duckdb"
        c = duckdb.connect(str(db))
        c.execute("create table tw_daily_prices(ticker varchar, date date, close double)")
        c.execute("insert into tw_daily_prices values ('2330','2021-12-30',600),('2330','2022-01-03',615),('2330','2026-11-12',1100)")
        c.execute("create table tw_stock_list(ticker varchar, name varchar)")
        c.execute("insert into tw_stock_list values ('2330','台積電')")
        c.close()
        lake = td / "lake"
        r1 = ingest(lake, "2022-01-01", [db])
        chk("① 日期表只收 >= 2022-01-01(2021-12-30 不收)· 快照表整張收", {x["table"]: x["rows_new"] for x in r1} == {"tw_daily_prices": 2, "tw_stock_list": 1}, r1)
        r2 = ingest(lake, "2022-01-01", [db])
        chk("② 重跑零新分片(日期只增 · 快照指紋相同)", all(x["state"] == "UPTODATE" for x in r2), [x["state"] for x in r2])
        c = duckdb.connect(str(db))
        c.execute("insert into tw_daily_prices values ('2330','2026-11-13',1110)")
        c.execute("update tw_stock_list set name='台灣積體電路'")
        c.close()
        r3 = ingest(lake, "2022-01-01", [db])
        chk("③ 新日期只寫新列(1 列)· 快照內容變了才寫新分片", {x["table"]: x["rows_new"] for x in r3} == {"tw_daily_prices": 1, "tw_stock_list": 1}, r3)
        cat = catalog(lake)
        con = duckdb.connect(str(cat), read_only=True)
        n = con.execute('select count(*) from "v_vdf_tw_market__tw_daily_prices"').fetchone()[0]
        nm = con.execute('select name from "v_vdf_tw_market__tw_stock_list"').fetchone()[0]
        con.close()
        chk("④ 管家 VIEW 讀 Parquet:日期表三分片合計 3 列 · 快照表只取最新分片", n == 3 and nm == "台灣積體電路", (n, nm))
        st = status(lake, write=False)
        row = next(x for x in st["tables"] if x["view"].endswith("tw_daily_prices"))
        chk("⑤ status:最早 2022-01-03 · 最晚 2026-11-13 · 分片 2", row["min_date"] == "2022-01-03" and row["max_date"] == "2026-11-13" and row["parts"] == 2, row)
        man = (lake / "_manifest.jsonl").read_text(encoding="utf-8").splitlines()
        chk("⑥ 每個新分片追一行 _manifest.jsonl(只增)", len(man) == 4, len(man))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 不代設同意閘 · 不用 TA-Lib · 不讀 VCGC 支援工具路徑 · 不刪分片",
        "environ[\"VIA_NET" + "_CONSENT\"] =" not in src and "import " + "talib" not in src and "supportive modules/" + "network" not in src
        and ".unlink()" in src and "part.unlink" + "()" not in src)
    print(f"[selftest] {STEM} {VERSION} {sum(ok)}/{len(ok)}")
    return 0 if all(ok) else 1


def main() -> int:
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    if a[0] == "--selftest":
        return selftest()
    if a[0] == "run":
        return run(a[1:])
    if a[0] == "status":
        return 0 if status(Path(a[a.index("--lake") + 1]) if "--lake" in a else DEFAULT_LAKE)["tables"] else 2
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
