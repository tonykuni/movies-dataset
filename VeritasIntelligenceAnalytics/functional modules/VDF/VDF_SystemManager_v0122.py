#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_SystemManager v0122 — 薄尾:三方對照 · Parquet 增量 · 鎖 · 管理員互比(動詞 universe 加四個子動詞)

操作員(R50 2026-10-02):「動做引擎化 串流程由SYSTEM MANAGER管理 都要記下版本 引擎時測成功就鎖住含版號及時間都要註冊 …
輸出PARQUET由DUCKDB管理 增量擷取 輸出後相同資料不同來源 三個重複齊對照 三種資料同一個主詞日齊數量應該相同 自動完成
兩方的SYSTEM MANAGER工應互比要依樣強大」。冊 VDF_InputUniverse_SSOT_v0101(OUT-06 · OUT-07 · xcheck · parquet · lock 節)。
  universe list                    同前版,另把 OUT-01 只增寫進 output_hub/universe/VDF_Universe.duckdb::universe_list
  universe xcheck [--days N] [--dry]  ① 加權收盤三來源(ENG232 官方 · ENG055 tw_market_agg.taiex · yfinance ^TWII 代理)同日對照
                                   ② 個股代號三表(價量 tw_daily_prices · 籌碼 tw_chip_inst · 成交值 tw_trading_daily)同日數量相同
                                   結果寫 OUT-06 / OUT-07(DuckDB 只增,鍵 date + run)與 VIA_Reports/vdf/universe/XCHECK_latest.json
  universe parquet [--apply] [--home <dir>]  輸出 Parquet 由 DuckDB 管:寫手 = CGC_MDL238(來源唯讀開、讀回列數驗),
                                   只出冊上的表,目錄列數沒變且檔在 = 略過(增量);預設乾跑
  universe lock                    VDF-WKF011 各站引擎尾版 · 自測結果 · 鎖帳(VIA_LampLock 的 locked_at + 版號);鎖由 SDD lock 寫
  universe parity                  兩個管理員互比(CGC_MDL252;VDF 與 VRN 不互相匯入)
  universe validate [OUT-xx]       同前版;OUT-06 / OUT-07 不給檔 = 讀 DuckDB 最新一輪
其餘動詞全照前版。不抓網、不代設同意閘、不碰 TA-Lib。只收 VCGC 呼叫(VIA_FROM_VCGC=YES)。
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
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

# ===== [VIA:LIB-BRIDGE:v0100] 三庫正典橋(批597;缺席大聲拋,不 graceful) =====
import sys as _lb_sys
from pathlib import Path as _lb_Path
_lb_p = _lb_Path(__file__).resolve()
while _lb_p.parent != _lb_p:
    if (_lb_p / "supportive modules").is_dir():
        _lb_sys.path.insert(0, str(_lb_p / "supportive modules"))
        break
    _lb_p = _lb_p.parent
import VIA_LibCanon as _LIB          # 正典缺席=大聲拋,不假裝有(LL151)
# ===== [VIA:LIB-BRIDGE:END] =====

import importlib.util
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
_STEM = "VDF_SystemManager"
REG = VIA / "supportive modules" / "registry"
REPORTS = VIA / "VIA_Reports" / "vdf" / "universe"
HUB = HERE / "output_hub"
DB_UNI = HUB / "universe" / "VDF_Universe.duckdb"
DB_TW = HUB / "mega" / "vdf_tw_market.duckdb"
DB_GL = HUB / "mega" / "vdf_global_market.duckdb"
DB_IDX = HUB / "tw_index" / "VDF_TWIndex_Daily.duckdb"
WKF = "VDF-WKF011"


def _vnum(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
PRIOR = _load(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)
ENGINE_TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def __getattr__(name):
    return getattr(PRIOR, name)


def collect() -> dict:
    return PRIOR.collect()


def book() -> dict:
    return PRIOR.book()


def _tail(folder: Path, pattern: str) -> Path | None:
    hits = sorted(folder.glob(pattern), key=_vnum)
    return hits[-1] if hits else None


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _con(db: Path):
    """唯讀連線;庫不在 = None(照實 NODATA)。"""
    if not Path(db).is_file():
        return None
    import duckdb
    return duckdb.connect(str(db), read_only=True)


def _tables(con) -> set:
    return {t for (t,) in con.execute("SHOW TABLES").fetchall()}


def _schema(out_id: str) -> str:
    """冊上 OUT-xx 欄位 → CREATE TABLE 欄型(DuckDB 管;型別照冊)。"""
    it = PRIOR._item(out_id)
    return ", ".join(f'"{c["key"]}" {c.get("dtype") or "VARCHAR"}' for c in PRIOR.resolve_columns(it))


def store(out_id: str, rows: list, db: Path = DB_UNI) -> dict:
    """只增入庫(VIA_LibCanon.UTILS.upsert_rows;同鍵不動)。空字串 = NULL(不假填)。"""
    if not rows:
        return {"added": 0, "total": 0}
    it = PRIOR._item(out_id)
    table = it["item"]
    keys = it.get("keys") or []
    clean = [{k: (None if v == "" else v) for k, v in r.items()} for r in rows]
    Path(db).parent.mkdir(parents=True, exist_ok=True)
    new, total = _LIB.UTILS.upsert_rows(db, table, clean, keys, schema=_schema(out_id), counts=True)
    return {"db": str(db), "table": table, "added": int(new), "total": int(total)}


# ---------------------------------------------------------------- xcheck ①:加權三來源
def _series(db: Path, table: str, date_col: str, val_col: str, where: str = "") -> dict:
    con = _con(db)
    if con is None:
        return {}
    try:
        if table not in _tables(con):
            return {}
        cols = {r[0] for r in con.execute(f'DESCRIBE "{table}"').fetchall()}
        if date_col not in cols or val_col not in cols:
            return {}
        sql = f'SELECT substr(CAST("{date_col}" AS VARCHAR), 1, 10), "{val_col}" FROM "{table}"' + (f" WHERE {where}" if where else "")
        return {d: float(v) for d, v in con.execute(sql).fetchall() if v is not None}
    finally:
        con.close()


def xcheck_index(days: int = 20, dbs: dict | None = None) -> dict:
    dbs = dbs or {"idx": DB_IDX, "tw": DB_TW, "gl": DB_GL}
    tol = book()["xcheck"]["index"]["tolerance"]
    off = _series(dbs["idx"], "tw_index_daily", "date", "close", "index_code = 'TAIEX'")
    agg = _series(dbs["tw"], "tw_market_agg", "date", "taiex")
    yf = _series(dbs["gl"], "global_daily", "date", "close", "ticker = '^TWII'")
    dates = sorted(set(off) | set(agg), reverse=True)[:days]
    rows, run = [], _today()
    for d in sorted(dates):
        v = {"official": off.get(d), "agg": agg.get(d), "yf": yf.get(d)}
        have = {k: x for k, x in v.items() if x}
        diffs = []
        if "official" in have and "agg" in have:
            diffs.append(("official_vs_agg", abs(have["official"] - have["agg"]) / have["official"]))
        base = have.get("official") or have.get("agg")
        if base and "yf" in have:
            diffs.append(("vs_yf", abs(have["yf"] - base) / base))
        over = [k for k, x in diffs if x > tol[k]]
        lamp = "NODATA" if not have else ("RED" if over else ("GREEN" if len(have) == 3 else "YELLOW"))
        rows.append({"date": d, "official_close": v["official"], "agg_taiex": v["agg"], "yf_close": v["yf"], "n_sources": len(have),
                     "max_rel_diff": round(max((x for _k, x in diffs), default=0.0), 6), "lamp": lamp, "run": run})
    lamps = [r["lamp"] for r in rows]
    verdict = "NODATA" if not rows else ("RED" if "RED" in lamps else ("GREEN" if all(x == "GREEN" for x in lamps) else "YELLOW"))
    return {"rows": rows, "verdict": verdict, "have": {"official": len(off), "agg": len(agg), "yf": len(yf)}}


# ---------------------------------------------------------------- xcheck ②:三種資料同主詞同日代號數
COUNT_SRC = (("prices", "tw_daily_prices", "split_part(CAST(ticker AS VARCHAR), '.', 1)"),
             ("chips", "tw_chip_inst", "CAST(code AS VARCHAR)"),
             ("trading", "tw_trading_daily", "CAST(code AS VARCHAR)"))


def xcheck_counts(days: int = 20, db: Path | None = None) -> dict:
    db = db or DB_TW
    rx = book()["inputs"][0]["code_regex"]
    con = _con(db)
    if con is None:
        return {"rows": [], "verdict": "NODATA", "note": f"庫不在:{db}"}
    try:
        have = _tables(con)
        if "tw_daily_prices" not in have:
            return {"rows": [], "verdict": "NODATA", "note": "tw_daily_prices 不在"}
        dates = [r[0] for r in con.execute("SELECT DISTINCT substr(CAST(date AS VARCHAR), 1, 10) d FROM tw_daily_prices "
                                           f"ORDER BY d DESC LIMIT {int(days)}").fetchall()]
        if not dates:
            return {"rows": [], "verdict": "NODATA", "note": "價表空"}
        lo = min(dates)
        sets, missing = {}, []
        for name, t, code in COUNT_SRC:
            if t not in have:
                missing.append(t)
                continue
            q = (f"SELECT DISTINCT substr(CAST(date AS VARCHAR), 1, 10) d, {code} c FROM \"{t}\" "
                 f"WHERE substr(CAST(date AS VARCHAR), 1, 10) >= ? AND regexp_full_match({code}, ?)")
            per = {}
            for d, c in con.execute(q, [lo, rx]).fetchall():
                per.setdefault(d, set()).add(c)
            sets[name] = per
    finally:
        con.close()
    rows, run, newest = [], _today(), max(dates)
    for d in sorted(dates):
        s = {n: sets[n].get(d, set()) for n in sets}
        ns = {n: len(v) for n, v in s.items()}
        allv = list(s.values())
        inter = set.intersection(*allv) if allv else set()
        union = set.union(*allv) if allv else set()
        sample = ",".join(sorted(union - inter)[:8])
        if missing or len(s) < 3:
            lamp = "YELLOW"
        elif any(n == 0 for n in ns.values()):
            lamp = "YELLOW" if d == newest else "RED"           # 最新日籌碼 / 成交值晚到 = 日更未齊(黃);舊日缺 = 紅
        else:
            lamp = "GREEN" if len(set(ns.values())) == 1 and len(inter) == ns["prices"] else "YELLOW"
        rows.append({"date": d, "prices_n": ns.get("prices"), "chips_n": ns.get("chips"), "trading_n": ns.get("trading"),
                     "all3_n": len(inter), "only_sample": sample, "lamp": lamp, "run": run})
    lamps = [r["lamp"] for r in rows]
    verdict = "RED" if "RED" in lamps else ("GREEN" if all(x == "GREEN" for x in lamps) else "YELLOW")
    return {"rows": rows, "verdict": verdict, "missing_tables": missing}


def xcheck(days: int = 20, write: bool = True, dbs: dict | None = None, out_db: Path = DB_UNI, reports: Path = REPORTS) -> dict:
    dbs = dbs or {"idx": DB_IDX, "tw": DB_TW, "gl": DB_GL}
    ix = xcheck_index(days, dbs)
    ct = xcheck_counts(days, dbs["tw"])
    rep = {"schema": "VIA.VDF.XCheck.v1", "engine": ENGINE_TAG, "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "index": ix, "counts": ct, "book": PRIOR.book_path().name}
    if write:
        rep["stored"] = {"OUT-06": store("OUT-06", ix["rows"], out_db), "OUT-07": store("OUT-07", ct["rows"], out_db)}
        reports.mkdir(parents=True, exist_ok=True)
        (reports / "XCHECK_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return rep


# ---------------------------------------------------------------- parquet:CGC_MDL238 是唯一寫手(增量)
def _mdl238():
    return _load(_tail(REG, "CGC_MDL238_OperatorConsole_v*.py"), "_cgc_mdl238_for_vdf_universe")


def _mdl252():
    return _load(_tail(REG, "CGC_MDL252_ManagerParity_v*.py"), "_cgc_mdl252_for_vdf")


def parquet(apply: bool = False, home: str | None = None, m238=None) -> dict:
    """冊 parquet.tables 經 CGC_MDL252.parquet_incremental(兩個管理員同一份;寫手 CGC_MDL238)。"""
    return _mdl252().parquet_incremental(m238 or _mdl238(), book()["parquet"]["tables"], apply, home)


# ---------------------------------------------------------------- lock:版號 + 時間(SDD lock 寫 VIA_LampLock;這裡只讀)
def lock_view() -> dict:
    wb = _tail(REG, "VIA_Workflow_VDF_SSOT_v[0-9][0-9][0-9][0-9].json")
    wk = next((w for w in json.loads(wb.read_text(encoding="utf-8"))["workflows"] if w["code"] == WKF), None) if wb else None
    ll = _tail(REG, "VIA_LampLock_v[0-9][0-9][0-9][0-9].json")
    lock = (json.loads(ll.read_text(encoding="utf-8")).get("wkf") or {}).get(WKF) if ll else None
    selfp = VIA / "VIA_Reports" / "sdd" / "SDD_SELF_latest.json"
    self_rep = json.loads(selfp.read_text(encoding="utf-8")) if selfp.is_file() else {}
    per = (self_rep.get("per_step") or {}).get(WKF, {})
    steps = []
    for st in (wk or {}).get("steps") or []:
        pat = st.get("engine") or ""
        cur = _tail(VIA / Path(pat).parent, Path(pat).name) if "*" in pat else None
        locked = ((lock or {}).get("versions") or {}).get(str(Path(pat).parent / cur.name) if cur else "", None)
        steps.append({"code": st["code"], "alias": st.get("alias"), "tail": cur.name if cur else None, "self": per.get(st["code"], "NOT_RUN"),
                      "locked": bool(locked), "moved": bool(lock) and not locked})
    state = ("ABSENT" if not wk else "OPEN" if not lock else
             "RELOCK" if any(s["moved"] for s in steps) else "LOCKED")
    return {"wkf": WKF, "book": wb.name if wb else None, "lamplock": ll.name if ll else None, "state": state,
            "locked_at": (lock or {}).get("locked_at"), "head": (lock or {}).get("head"), "steps": steps}


# ---------------------------------------------------------------- 讀回 OUT-06 / OUT-07(驗證用)
def _read_out(out_id: str, db: Path = DB_UNI):
    it = PRIOR._item(out_id)
    con = _con(db)
    if con is None:
        return None
    try:
        if it["item"] not in _tables(con):
            return None
        return con.execute(f'SELECT * FROM "{it["item"]}" WHERE run = (SELECT max(run) FROM "{it["item"]}")').df()
    finally:
        con.close()


def validate(out_id: str, df=None, universe_rep: dict | None = None) -> dict:
    if df is None and out_id in ("OUT-06", "OUT-07"):
        raw = _read_out(out_id)
        if raw is None:
            return {"table": f"vdf_universe_{out_id.lower()}", "lamp": "NODATA", "problems": [f"{out_id} 還沒產出(先 universe xcheck)"]}
        df = PRIOR.frame(out_id, raw.to_dict("records"))
    return PRIOR.validate(out_id, df, universe_rep)


def universe(args: list) -> int:
    sub = args[0] if args else "headers"
    days = int(PRIOR_arg(args, "--days") or 20)
    if sub == "list":
        rep = PRIOR.build_universe()
        out = PRIOR.write_universe(rep, args[args.index("--out") + 1] if "--out" in args else None)
        rows = [{**r, "verified": (True if r.get("verified") is True else None)} for r in rep["rows"]]
        st = store("OUT-01", rows)
        t = rep["tally"]
        print(f"[VDF 輸入清單] 個股 {t.get('TW_STOCK', 0)} · 主動股票 ETF(有每日持股){t.get('TW_ACTIVE_EQUITY_ETF', 0)} · "
              f"指數 {t.get('TW_INDEX', 0)} · {out['csv']} · DuckDB {st.get('table')} +{st.get('added')} / {st.get('total')}")
        for n in rep["notes"]:
            print("  [註] " + n)
        return 0 if t.get("TW_STOCK") and t.get("TW_ACTIVE_EQUITY_ETF") else 2
    if sub == "xcheck":
        rep = xcheck(days, write="--dry" not in args)
        ix, ct = rep["index"], rep["counts"]
        print(f"[VDF 三方對照] 加權三來源 {ix['verdict']}(官方 {ix['have']['official']} · ENG055 {ix['have']['agg']} · yf {ix['have']['yf']} 日)"
              f" · 三表同日代號數 {ct['verdict']}" + (f"(缺表 {ct.get('missing_tables')})" if ct.get("missing_tables") else "")
              + (f" · {ct.get('note')}" if ct.get("note") else ""))
        for r in ix["rows"][-5:]:
            print(f"  [{r['lamp']:<6}] {r['date']} 官方 {r['official_close']} · ENG055 {r['agg_taiex']} · yf {r['yf_close']} · 差 {r['max_rel_diff']}")
        for r in ct["rows"][-5:]:
            print(f"  [{r['lamp']:<6}] {r['date']} 價量 {r['prices_n']} · 籌碼 {r['chips_n']} · 成交值 {r['trading_n']} · 三表都有 {r['all3_n']}"
                  + (f" · 缺 {r['only_sample']}" if r["only_sample"] else ""))
        worst = [ix["verdict"], ct["verdict"]]
        return 1 if "RED" in worst else (0 if all(x == "GREEN" for x in worst) else 2)
    if sub == "parquet":
        r = parquet("--apply" in args, PRIOR_arg(args, "--home"))
        print(f"[VDF Parquet] {r['state']} · " + (f"資料家 {r.get('home')} · 表 {r['plan']} · 要寫 {len(r['todo'])} · 沒變略過 {r.get('skip', 0)}"
                                                   + (f" · 已寫 {r.get('written')}" if r.get("applied") else " · 乾跑(--apply 才寫)")
                                                   if r["state"] != "NODATA" or r.get("home") else r.get("why", "")))
        return {"OK": 0, "NODATA": 2}.get(r["state"], 1)
    if sub == "lock":
        v = lock_view()
        print(f"[VDF 鎖] {v['wkf']} {v['state']} · 鎖於 {v['locked_at'] or '—'} · 冊 {v['book']} · 鎖帳 {v['lamplock']}")
        for s in v["steps"]:
            print(f"  {s['code']:<20} {s['alias'] or '':<16} {s['tail'] or '缺':<44} 自測 {s['self']:<8} {'已鎖' if s['locked'] else ('要重驗' if s['moved'] else '未鎖')}")
        if v["state"] in ("OPEN", "RELOCK"):
            print("  → via-vcgc sdd selftests → sdd real → run CGC_MDL245_SDDValidator lock --apply(版號 + 時間寫 VIA_LampLock)")
        return 0 if v["state"] == "LOCKED" else 2
    if sub == "parity":
        m = _mdl252()
        rep = m.parity()
        m.write(rep)
        m.show(rep)
        return {"GREEN": 0, "YELLOW": 2}.get(rep["verdict"], 1)
    if sub == "validate":
        ids = [a for a in args[1:] if a.startswith("OUT-")] or [o["id"] for o in book()["outputs"]]
        worst = 0
        for oid in ids:
            df = None
            if "--file" in args:
                import pandas as pd
                fp = args[args.index("--file") + 1]
                df = pd.read_parquet(fp) if fp.endswith(".parquet") else pd.read_csv(fp, encoding="utf-8-sig", dtype=str)
            r = validate(oid, df)
            lamp = r.get("lamp")
            worst = max(worst, {"GREEN": 0, "YELLOW": 0, "NODATA": 0}.get(lamp, 1))
            print(f"  [{lamp}] {oid} {r.get('table')} · 列 {r.get('rows')} · " + " ; ".join((r.get("problems") or []) + (r.get("warn") or [])))
        return worst
    return PRIOR.universe(args)


def PRIOR_arg(a: list, k: str):
    return a[a.index(k) + 1] if k in a and a.index(k) + 1 < len(a) else None


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VDF] 拒絕。只能經 via-vcgc。")
        return 2
    a = sys.argv[1:]
    if a and a[0] == "universe":
        return universe(a[1:])
    return PRIOR.main()


def selftest() -> int:
    import tempfile
    import duckdb
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {ENGINE_TAG} · 薄尾自測(三方對照 · Parquet 增量 · 鎖 · 互比;暫存庫,零網路)===")
    bk = book()
    chk("① 冊 v0101:七項輸出(+OUT-06 加權三來源 · OUT-07 三表代號數)· 順序 15 站收在 E-11:lock · xcheck/parquet/lock 三節",
        len(bk["outputs"]) == 7 and bk["loop"]["order"][-3:] == ["E-11:xcheck", "E-11:parquet", "E-11:lock"]
        and all(k in bk for k in ("xcheck", "parquet", "lock")), PRIOR.book_path().name)
    with tempfile.TemporaryDirectory() as td:
        T = Path(td)
        dbs = {"idx": T / "idx.duckdb", "tw": T / "tw.duckdb", "gl": T / "gl.duckdb"}
        c = duckdb.connect(str(dbs["idx"]))
        c.execute("CREATE TABLE tw_index_daily(date VARCHAR, index_code VARCHAR, close DOUBLE)")
        c.execute("INSERT INTO tw_index_daily VALUES ('2026-09-29','TAIEX',20000),('2026-09-30','TAIEX',20100),('2026-10-01','TAIEX',20200),"
                  "('2026-10-01','TPEX',250)")
        c.close()
        c = duckdb.connect(str(dbs["tw"]))
        c.execute("CREATE TABLE tw_market_agg(date DATE, volume DOUBLE, taiex DOUBLE)")
        c.execute("INSERT INTO tw_market_agg VALUES ('2026-09-29',1,20000),('2026-09-30',1,20100),('2026-10-01',1,20402)")
        c.execute("CREATE TABLE tw_daily_prices(date VARCHAR, ticker VARCHAR, close DOUBLE)")
        c.execute("INSERT INTO tw_daily_prices VALUES ('2026-09-29','2330.TW',1),('2026-09-29','6488.TWO',1),('2026-09-29','0050.TW',1),"
                  "('2026-09-30','2330.TW',1),('2026-09-30','6488.TWO',1),('2026-10-01','2330.TW',1)")
        c.execute("CREATE TABLE tw_chip_inst(date DATE, code VARCHAR, market VARCHAR)")
        c.execute("INSERT INTO tw_chip_inst VALUES ('2026-09-29','2330','TWSE'),('2026-09-29','6488','TPEX'),('2026-09-29','0050','TWSE'),"
                  "('2026-09-30','2330','TWSE')")
        c.execute("CREATE TABLE tw_trading_daily(date VARCHAR, code VARCHAR, market VARCHAR)")
        c.execute("INSERT INTO tw_trading_daily VALUES ('2026-09-29','2330','TWSE'),('2026-09-29','6488','TPEX'),"
                  "('2026-09-30','2330','TWSE'),('2026-09-30','6488','TPEX'),('2026-10-01','2330','TWSE')")
        c.close()
        c = duckdb.connect(str(dbs["gl"]))
        c.execute("CREATE TABLE global_daily(date VARCHAR, ticker VARCHAR, close DOUBLE)")
        c.execute("INSERT INTO global_daily VALUES ('2026-09-29','^TWII',20010),('2026-10-01','^TWII',20200),('2026-09-29','^N225',1)")
        c.close()
        ix = xcheck_index(20, dbs)
        lam = {r["date"]: r["lamp"] for r in ix["rows"]}
        chk("② 加權三來源:三來源齊且差在容許內 = GREEN · 少 yf = YELLOW · ENG055 與官方差 1% = RED",
            lam == {"2026-09-29": "GREEN", "2026-09-30": "YELLOW", "2026-10-01": "RED"} and ix["verdict"] == "RED", lam)
        ct = xcheck_counts(20, dbs["tw"])
        cl = {r["date"]: (r["prices_n"], r["chips_n"], r["trading_n"], r["all3_n"], r["lamp"]) for r in ct["rows"]}
        chk("③ 三表同日代號數:只算個股四碼(0050 不算)· 齊 = GREEN · 籌碼缺 6488 = YELLOW 列樣本 · 最新日籌碼 0 = 黃(日更未齊)",
            cl == {"2026-09-29": (2, 2, 2, 2, "GREEN"), "2026-09-30": (2, 1, 2, 1, "YELLOW"), "2026-10-01": (1, 0, 1, 0, "YELLOW")}
            and any(r["only_sample"] == "6488" for r in ct["rows"]), cl)
        out_db = T / "uni.duckdb"
        rep = xcheck(20, True, dbs, out_db, T / "rep")
        rep2 = xcheck(20, True, dbs, out_db, T / "rep")
        chk("④ 對照結果入 DuckDB(OUT-06 / OUT-07,鍵 date + run)只增:同日重跑 +0",
            rep["stored"]["OUT-06"]["added"] == 3 and rep["stored"]["OUT-07"]["added"] == 3
            and rep2["stored"]["OUT-06"]["added"] == 0 and (T / "rep" / "XCHECK_latest.json").is_file(), rep2["stored"])
        v6 = PRIOR.validate("OUT-06", PRIOR.frame("OUT-06", ix["rows"]))
        v7 = PRIOR.validate("OUT-07", PRIOR.frame("OUT-07", ct["rows"]))
        chk("⑤ OUT-06 / OUT-07 表頭 → DataFrame → CGC_MDL249 驗證過(必填 · 型別 · 主鍵)", v6["lamp"] == "GREEN" and v7["lamp"] == "GREEN",
            (v6.get("problems"), v7.get("problems")))
        st = store("OUT-01", [{"seq": 1, "group": "TW_STOCK", "code": "2330", "name": "台積電", "market": "TWSE", "yf_ticker": "2330.TW",
                               "bb_ticker": "2330 TT", "industry": "", "issuer": "", "verified": None, "last_holdings_date": "",
                               "source": "t", "state": "OK"}], out_db)
        st2 = store("OUT-01", [{"seq": 9, "group": "TW_STOCK", "code": "2330", "name": "改名", "market": "TWSE", "state": "OK"}], out_db)
        chk("⑥ OUT-01 清單入 DuckDB:空字串 = NULL · 型別照冊 · 同鍵不動(只增)", st["added"] == 1 and st2["added"] == 0
            and duckdb.connect(str(out_db), read_only=True).execute("SELECT name, last_holdings_date FROM universe_list").fetchall() == [("台積電", None)])

        class FakeM238:
            def __init__(self, home):
                self.home, self.applied = home, None

            def data_home(self, override=None):
                return (self.home, "test") if self.home else (None, "資料家不可用")

            def parquet_plan(self, home):
                return [{"db": "vdf_tw_market", "table": "tw_daily_prices", "rows": 6, "view": "vdf_tw_market__tw_daily_prices", "exists": True},
                        {"db": "vdf_tw_market", "table": "tw_chip_inst", "rows": 4, "view": "vdf_tw_market__tw_chip_inst", "exists": True},
                        {"db": "x", "table": "not_mine", "rows": 1, "view": "x__not_mine", "exists": False}]

            def parquet_apply(self, home, plan):
                self.applied = [r["view"] for r in plan]
                return {"written": len(plan), "failed": [], "catalog": str(Path(home) / "VIA_Parquet_Catalog.duckdb")}

        home = T / "home"
        home.mkdir()
        c = duckdb.connect(str(home / "VIA_Parquet_Catalog.duckdb"))
        c.execute("CREATE TABLE _via_catalog(view VARCHAR PRIMARY KEY, db VARCHAR, tbl VARCHAR, rows BIGINT, parquet VARCHAR, updated_at VARCHAR)")
        c.execute("INSERT INTO _via_catalog VALUES ('vdf_tw_market__tw_daily_prices','vdf_tw_market','tw_daily_prices',6,'p','t')")
        c.close()
        fm = FakeM238(home)
        r0 = parquet(False, None, fm)
        r1 = parquet(True, None, fm)
        chk("⑦ Parquet 增量:只挑冊上的表 · 列數沒變略過 · 乾跑不寫 · --apply 只寫變了的(寫手 = CGC_MDL238)",
            r0["plan"] == 2 and r0["todo"] == ["vdf_tw_market__tw_chip_inst"] and not r0["applied"]
            and r1["applied"] and fm.applied == ["vdf_tw_market__tw_chip_inst"], (r0, fm.applied))
        chk("⑧ 資料家不可用 = NODATA(不假寫)", parquet(True, None, FakeM238(None))["state"] == "NODATA")
    lv = lock_view()
    chk("⑨ 鎖:VDF-WKF011 在工作流冊;各站尾版解得到;沒鎖 = OPEN / 已鎖 = LOCKED(版號 + 時間在 VIA_LampLock)",
        lv["state"] in ("OPEN", "LOCKED", "RELOCK") and lv["steps"] and all(s["tail"] for s in lv["steps"]), (lv["state"], lv["book"]))
    pr = _mdl252().side_report("VDF")
    chk("⑩ 互比(CGC_MDL252):本管理員 universe 七項能力全在", all(pr["have"][k] for k in ("headers", "frame", "validate", "loop", "xcheck", "parquet", "lock")),
        {k: v for k, v in pr["have"].items() if not v})
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑪ 加速器橋 · 網路橋 · 正典橋在;不碰 TA-Lib;不代設同意閘",
        all(x in src for x in ("VIA:ACCEL-BRIDGE", "VIA:NET-BRIDGE", "VIA:LIB-BRIDGE")) and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and "VIA_NET_CONSENT\"] =" not in src)
    books = sorted(HERE.glob("VDF_InputUniverse_SSOT_v[0-9][0-9][0-9][0-9].json"), key=_vnum)
    keep = PRIOR.book_path
    PRIOR.book_path = lambda: books[0]                 # 前版自測是照 v0100 冊寫的(五項輸出 · 12 站):釘回它那一版的冊再跑
    os.environ["VIA_FROM_VCGC"] = "YES"
    try:
        rc = PRIOR.selftest()
    finally:
        PRIOR.book_path = keep
    good = all(ok)
    print(f"  [計] {ENGINE_TAG} 薄尾 {sum(ok)}/{len(ok)} · 前版 {'PASS' if rc == 0 else 'FAIL'} · 合計 {'PASS' if good and rc == 0 else 'FAIL'}")
    return 0 if good and rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
