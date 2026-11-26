#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF_MDL023_StageMerge v0100 — 倉內擷取暫存庫併入資料家正典庫(同名庫 · 同名表 · 鍵只補缺;來源零觸碰)

操作員 2026-11-26:「資料庫是否與 …\via_database\vdf_database 相同 · 若不同則整合 · 是否有增量擷取 · 有無重複擷取」。
桌機實錄:這一輪全族群擷取寫進倉內暫存 …\VIA_Reports\vdf_fetch\dict\output_hub(MDL008 / MDL012 預設家;v0113 已改成資料家),
台股日價 +3,958,808 列(2018 起)· 全球 +177,982 列 · ETF 持股 · 指數 · 總經 …,資料家的正典庫沒有這些列 → 兩份庫不同。
本支把暫存庫的列「只補缺」併進資料家同名庫,之後兩邊對齊、下一輪擷取依資料家水位只抓缺口(不重抓)。
  來源:倉內暫存 <VIA>\VIA_Reports\vdf_fetch\dict\output_hub\**\*.duckdb(--src 可改;略過 _backup · quarantine · selftest · _sha 副本 · .wal)
  目標:資料家 output_hub(VDF_MDL020_DataPlane 尾版 resolve_home:--home > env VIA_VDF_DB_HOME > 資料家冊)同一相對路徑的同名庫;
        同一個實體檔(接點 / 捷徑)= 已是同一份,跳過。
  逐表:目標表在 → 鍵 = 目標表主鍵 / 唯一鍵 > DataPlane 冊 outputs 的 key > 整列(共同欄)。不從欄名猜部分鍵
        (財報同一天有年 / 季兩列,猜成 date+ticker+source 會把不同列併掉;PR #763 Codex P1)。
        只插「目標沒有的鍵」(來源同鍵多列只取一列)· 只寫共同欄 · 來源多出的欄點名不加(黃)· 既有列零觸碰。
        目標表不在 → 照來源建表(整表複製)。目標庫不在 → 開新暫存庫、唯讀 ATTACH 來源(會套用來源的 .wal,中斷留下的已提交交易
        不會掉;整檔複製會掉 —— PR #763 Codex P1)逐表 CREATE TABLE AS、核列數,再原子換名(來源不動)。
  每張表一個交易(BEGIN / COMMIT;錯 = ROLLBACK,該表紅、其他表照做)。
動詞:plan(預設,唯讀:每表 待併列數 · 鍵 · 狀態)· apply(要 VDF / VCGC 入口旗標 VIA_FROM_VDFSM 或 VIA_FROM_VCGC = YES)· --selftest
收據:<VIA>\VIA_Reports\vdf\stage_merge\STAGE_MERGE_latest.json(庫 · 表 · 鍵欄名 · 待併 / 已併列數 · 燈;不含資料值)。
rc:0 綠(沒有待併 / 全併完)· 2 黃(有待併沒 apply · 有多欄 · 找不到資料家)· 1 紅(有表失敗)。零網路;不設同意閘;不用 TA-Lib。
用法:py VDF_MDL023_StageMerge_v0100.py plan [--src 夾] [--home 資料家] [--json] · apply [同上] · --selftest
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
import re
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
TAG = "VDF_MDL023_StageMerge v0100"
DEFAULT_SRC = VIA / "VIA_Reports" / "vdf_fetch" / "dict" / "output_hub"
RECEIPT = VIA / "VIA_Reports" / "vdf" / "stage_merge" / "STAGE_MERGE_latest.json"
SKIP_PARTS = ("_backup", "quarantine", "_quarantine", "selftest")
_SHA = re.compile(r"_sha[0-9a-f]{6,}$")
ENTRY = ("VIA_FROM_VDFSM", "VIA_FROM_VCGC")


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(str(p)).stem)
    return int(m.group(1)) if m else -1


def _qi(c: str) -> str:
    return '"' + str(c).replace('"', '""') + '"'


def _ql(s: str) -> str:
    return "'" + str(s).replace("'", "''") + "'"


def data_home(arg=None) -> tuple:
    """資料家(底下有 output_hub 的那一層):--home > DataPlane 尾版 resolve_home(env VIA_VDF_DB_HOME > 資料家冊)。"""
    if arg:
        p = Path(arg)
        for q in (p, p / "vdf_database"):
            if (q / "output_hub").is_dir():
                return q, "--home"
        return None, f"--home {arg} 底下沒有 output_hub"
    try:
        import importlib.util
        ts = sorted(HERE.glob("VDF_MDL020_DataPlane_v*.py"), key=_vnum)
        sp = importlib.util.spec_from_file_location("VDF_MDL023_dataplane", ts[-1])
        m = importlib.util.module_from_spec(sp)
        sys.modules[sp.name] = m
        sp.loader.exec_module(m)
        h, why = m.resolve_home(None)
    except Exception as exc:  # noqa: BLE001 — 判不出家照實說
        return None, f"DataPlane 讀不到:{type(exc).__name__}"
    if h is None:
        return None, why
    for q in (Path(h), Path(h) / "vdf_database"):
        if (q / "output_hub").is_dir():
            return q, why
    return None, f"{why}:底下沒有 output_hub"


def _skip(p: Path) -> bool:
    low = [x.lower() for x in p.parts]
    return any(s in low for s in SKIP_PARTS) or bool(_SHA.search(p.stem)) or p.name.endswith(".wal")


def pairs(src_root: Path, home: Path) -> list:
    out = []
    if not src_root.is_dir():
        return out
    for s in sorted(src_root.rglob("*.duckdb")):
        if not s.is_file() or _skip(s.relative_to(src_root)):
            continue
        rel = s.relative_to(src_root)
        t = home / "output_hub" / rel
        same = t.exists() and os.path.normcase(str(t.resolve())) == os.path.normcase(str(s.resolve()))
        out.append({"rel": str(rel).replace("\\", "/"), "src": s, "dst": t, "same": same})
    return out


def _connect(db: Path, read_only=False, retries=6, wait=3.0):
    import duckdb
    last = None
    for _ in range(retries):
        try:
            return duckdb.connect(str(db), read_only=read_only)
        except Exception as exc:  # noqa: BLE001 — 單寫者鎖:短等重試
            last = exc
            time.sleep(wait)
    raise RuntimeError(f"開不了 {db.name}:{str(last)[:120]}")


def _tables(con, catalog: str) -> list:
    return [r[0] for r in con.execute(
        "select table_name from information_schema.tables where table_catalog = ? and table_schema = 'main' and table_type = 'BASE TABLE' order by 1",
        [catalog]).fetchall()]


def _cols(con, catalog: str, table: str) -> list:
    return [r[0] for r in con.execute(
        "select column_name from information_schema.columns where table_catalog = ? and table_schema = 'main' and table_name = ? order by ordinal_position",
        [catalog, table]).fetchall()]


def _pk(con, catalog: str, table: str) -> list:
    try:
        rows = con.execute("select constraint_column_names from duckdb_constraints() where database_name = ? and schema_name = 'main' "
                           "and table_name = ? and constraint_type in ('PRIMARY KEY', 'UNIQUE') order by constraint_type = 'UNIQUE'",
                           [catalog, table]).fetchall()
    except Exception:  # noqa: BLE001 — 舊版 DuckDB 沒這張表 → 退回推鍵
        return []
    return list(rows[0][0]) if rows else []


def book_keys(book_dir: Path = HERE) -> dict:
    """DataPlane 冊尾版 outputs:(庫檔名, 表名) → 鍵欄(冊上寫的業務鍵)。"""
    hits = sorted(Path(book_dir).glob("VDF_DataPlane_SSOT_v*.json"), key=_vnum)
    if not hits:
        return {}
    try:
        outs = json.loads(hits[-1].read_text(encoding="utf-8")).get("outputs") or []
    except (OSError, ValueError):
        return {}
    return {(str(o.get("db") or ""), str(o.get("table") or "")): list(o["key"]) for o in outs if o.get("key")}


BOOK_KEYS = {}


def choose_key(con, dst_cat: str, table: str, common: list, db_name: str = "") -> tuple:
    """主鍵 / 唯一鍵 > DataPlane 冊上的業務鍵 > 整列。不猜部分鍵(會把不同列併掉)。"""
    pk = _pk(con, dst_cat, table)
    if pk and all(c in common for c in pk):
        return pk, "主鍵"
    low = {c.lower(): c for c in common}
    bk = BOOK_KEYS.get((db_name, table))
    if not bk:                                       # 庫名對不上:表名在冊上只出現一次 → 同一個業務表
        same = [v for (d, t), v in BOOK_KEYS.items() if t == table]
        bk = same[0] if len(same) == 1 else None
    if bk and all(k.lower() in low for k in bk):
        return [low[k.lower()] for k in bk], "冊上業務鍵"
    return list(common), "整列"


def merge_table(con, table: str, apply: bool, db_name: str = "") -> dict:
    row = {"table": table}
    s_cols = _cols(con, "s", table)
    if table not in _tables(con, "t"):
        n = con.execute(f"select count(*) from s.main.{_qi(table)}").fetchone()[0]
        row.update(key=[], key_kind="新表", new=n, extra_cols=[], state="NEW_TABLE")
        if apply and n:
            con.execute("begin")
            try:
                con.execute(f"create table t.main.{_qi(table)} as select * from s.main.{_qi(table)}")
                con.execute("commit")
                row.update(merged=n, state="CREATED")
            except Exception as exc:  # noqa: BLE001
                con.execute("rollback")
                row.update(state="FAIL", why=str(exc)[:160])
        return row
    t_cols = _cols(con, "t", table)
    common = [c for c in s_cols if c in t_cols]
    extra = [c for c in s_cols if c not in t_cols]
    key, kind = choose_key(con, "t", table, common, db_name)
    row.update(key=key, key_kind=kind, extra_cols=extra)
    if not common:
        row.update(new=0, state="NO_COMMON_COLS")
        return row
    cl = ", ".join(_qi(c) for c in common)
    kl = ", ".join(_qi(c) for c in key)
    cond = " and ".join(f"y.{_qi(c)} is not distinct from x.{_qi(c)}" for c in key)
    whole = len(key) == len(common)
    src = (f"(select distinct {cl} from s.main.{_qi(table)}) x" if whole
           else f"(select distinct on ({kl}) {cl} from s.main.{_qi(table)}) x")
    where = f"where not exists (select 1 from t.main.{_qi(table)} y where {cond})"
    n = con.execute(f"select count(*) from {src} {where}").fetchone()[0]
    row.update(new=n, state="UPTODATE" if n == 0 else "PENDING")
    if apply and n:
        con.execute("begin")
        try:
            con.execute(f"insert into t.main.{_qi(table)} ({cl}) select {', '.join('x.' + _qi(c) for c in common)} from {src} {where}")
            con.execute("commit")
            row.update(merged=n, state="MERGED")
        except Exception as exc:  # noqa: BLE001
            con.execute("rollback")
            row.update(state="FAIL", why=str(exc)[:160])
    return row


def merge_db(p: dict, apply: bool) -> dict:
    s, t = p["src"], p["dst"]
    out = {"db": p["rel"], "tables": [], "state": "OK"}
    if p["same"]:
        out["state"] = "SAME_FILE"
        return out
    if not t.exists():
        out["state"] = "NEW_DB"
        if apply:
            out.update(new_db_snapshot(s, t))
        return out
    con = _connect(t)
    try:
        con.execute(f"attach {_ql(str(s))} as s (read_only)")
        cat = con.execute("select current_database()").fetchone()[0]
        if cat != "t":
            con.execute(f"use {_qi(cat)}")
        for tb in _tables(con, "s"):
            try:
                out["tables"].append(_merge_aliased(con, cat, tb, apply, t.name))
            except Exception as exc:  # noqa: BLE001 — 單表錯照實紅,其他表照做
                out["tables"].append({"table": tb, "state": "FAIL", "why": str(exc)[:160]})
        con.execute("detach s")
    finally:
        con.close()
    return out


def new_db_snapshot(s: Path, t: Path) -> dict:
    """目標庫不在:新暫存庫 + 唯讀 ATTACH 來源(套用來源 .wal)→ 逐表 CREATE TABLE AS → 核列數 → 原子換名。不整檔複製。"""
    t.parent.mkdir(parents=True, exist_ok=True)
    tmp = t.with_name(f".{t.stem}.mdl023_{os.getpid()}.duckdb")
    for q in (tmp, tmp.with_name(tmp.name + ".wal")):
        q.unlink(missing_ok=True)
    con = _connect(tmp)
    rows = {}
    try:
        con.execute(f"attach {_ql(str(s))} as s (read_only)")
        for tb in _tables(con, "s"):
            con.execute(f"create table {_qi(tb)} as select * from s.main.{_qi(tb)}")
            a = con.execute(f"select count(*) from s.main.{_qi(tb)}").fetchone()[0]
            b = con.execute(f"select count(*) from {_qi(tb)}").fetchone()[0]
            if a != b:
                raise RuntimeError(f"{tb} 列數不符 {a} → {b}")
            rows[tb] = b
        con.execute("detach s")
        con.execute("checkpoint")
    except Exception as exc:  # noqa: BLE001 — 新庫建不成:刪暫存、照實紅
        con.close()
        for q in (tmp, tmp.with_name(tmp.name + ".wal")):
            q.unlink(missing_ok=True)
        return {"state": "FAIL", "why": str(exc)[:160]}
    con.close()
    os.replace(tmp, t)
    return {"state": "COPIED", "tables_copied": len(rows), "rows_copied": sum(rows.values())}


def _merge_aliased(con, cat: str, table: str, apply: bool, db_name: str = "") -> dict:
    """目標庫的 catalog 名是檔名 stem;merge_table 寫死 t → 用 VIEW 別名太繞,這裡把 t 換成實際 catalog。"""
    return merge_table(_Alias(con, cat), table, apply, db_name)


class _Alias:
    """把 SQL 裡的 't.' / catalog 't' 換成目標庫實際的 catalog 名(DuckDB 以檔名 stem 當 catalog)。"""

    def __init__(self, con, cat: str):
        self.con, self.cat = con, cat

    def execute(self, sql: str, params=None):
        sql = sql.replace("t.main.", _qi(self.cat) + ".main.")
        if params:
            params = [self.cat if x == "t" else x for x in params]
            return self.con.execute(sql, params)
        return self.con.execute(sql)


def lamp_of(dbs: list, apply: bool, home_ok: bool) -> tuple:
    if not home_ok:
        return "YELLOW", 2
    tabs = [t for d in dbs for t in d["tables"]]
    if any(t.get("state") == "FAIL" for t in tabs) or any(d.get("state") == "FAIL" for d in dbs):
        return "RED", 1
    pending = any(t.get("state") in ("PENDING", "NEW_TABLE") for t in tabs) or any(d.get("state") == "NEW_DB" for d in dbs)
    extra = any(t.get("extra_cols") for t in tabs)
    if pending or extra:
        return "YELLOW", 2
    return "GREEN", 0


def run(argv: list, apply: bool) -> int:
    def opt(k):
        return argv[argv.index(k) + 1] if k in argv and argv.index(k) + 1 < len(argv) else None
    if apply and not any(os.environ.get(k, "").upper() == "YES" for k in ENTRY):
        print(f"[{TAG}] RED · apply 要從 VDF 管理器 / VCGC 入口進(VIA_FROM_VDFSM 或 VIA_FROM_VCGC = YES);零寫入")
        return 1
    src = Path(opt("--src") or DEFAULT_SRC)
    home, why = data_home(opt("--home"))
    BOOK_KEYS.clear()
    BOOK_KEYS.update(book_keys())
    res = {"tool": TAG, "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "apply": apply, "src": str(src),
           "home": str(home) if home else None, "home_why": why, "dbs": []}
    if home is None:
        print(f"[{TAG}] YELLOW · 找不到資料家({why});不併")
    else:
        print(f"[{TAG}] {'APPLY' if apply else 'PLAN(唯讀)'} · 暫存 {src} → 資料家 {home / 'output_hub'}({why})")
        for p in pairs(src, home):
            d = merge_db(p, apply)
            res["dbs"].append(d)
            print(f"  [{d['state']:<9}] {d['db']}")
            for t in d["tables"]:
                n = t.get("merged", t.get("new", 0))
                print(f"     {t.get('state', ''):<12} {t['table']:<40} {'已併' if 'merged' in t else '待併'} {n:>12,} · 鍵 {t.get('key_kind', '')} "
                      f"{','.join(t.get('key') or [])[:60]}" + (f" · 多欄未併 {','.join(t['extra_cols'])[:60]}" if t.get("extra_cols") else "")
                      + (f" · {t['why']}" if t.get("why") else ""))
    lamp, rc = lamp_of(res["dbs"], apply, home is not None)
    res.update(lamp=lamp, rc=rc)
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8")
    if "--json" in argv:
        print(json.dumps(res, ensure_ascii=False, default=str)[:4000])
    print(f"[{TAG}] {lamp} · 庫 {len(res['dbs'])} · 收據 {RECEIPT.relative_to(VIA) if RECEIPT.is_relative_to(VIA) else RECEIPT}")
    return rc


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""), flush=True)

    import duckdb
    global RECEIPT
    keep_receipt = RECEIPT
    print(f"=== {TAG} · 自測(全在暫存夾;不碰本機資料家 · 收據也寫暫存夾)===", flush=True)
    chk("① 加速器真的載到(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    chk("② 網路工具橋在位(載入不出網)", VIA_NET_TOOL_PATH is not None)
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        RECEIPT = td / "receipt" / "STAGE_MERGE_latest.json"
        src = td / "stage" / "output_hub"
        home = td / "via_database" / "vdf_database"
        (src / "mega").mkdir(parents=True)
        (home / "output_hub" / "mega").mkdir(parents=True)
        c = duckdb.connect(str(src / "mega" / "vdf_tw_market.duckdb"))
        c.execute("create table tw_daily_prices(date varchar, ticker varchar, close double, extra_x int)")
        c.execute("insert into tw_daily_prices values ('2018-01-02','2330.TW',1,9),('2018-01-02','2330.TW',1,9),('2026-11-20','2330.TW',2,9),('2026-11-20','2317.TW',3,9)")
        c.execute("create table us_macro(date varchar, series varchar, value double)")
        c.execute("insert into us_macro values ('2026-10-01','CPI',1)")
        c.execute("create table only_in_stage(a int)")
        c.execute("insert into only_in_stage values (1),(2)")
        c.execute("create table tw_financial(Date varchar, Ticker varchar, Source varchar, Period_Type varchar, v double)")
        c.execute("insert into tw_financial values ('2025-12-31','2330.TW','yfinance','annual',1),('2025-12-31','2330.TW','yfinance','quarterly',2)")
        c.close()
        c = duckdb.connect(str(src / "mega" / "aaii_sentiment.duckdb"))
        c.execute("create table aaii(date varchar, bullish double)")
        c.execute("checkpoint")
        c.execute("PRAGMA disable_checkpoint_on_shutdown")
        c.execute("set checkpoint_threshold='10GB'")
        c.execute("insert into aaii values ('2026-11-19', 33.3)")   # 已提交、只在 .wal(模擬中斷的暫存庫)
        c.close()
        wal_left = (src / "mega" / "aaii_sentiment.duckdb.wal").is_file()
        t = duckdb.connect(str(home / "output_hub" / "mega" / "vdf_tw_market.duckdb"))
        t.execute("create table tw_daily_prices(date varchar, ticker varchar, close double, primary key(date, ticker))")
        t.execute("insert into tw_daily_prices values ('2026-11-20','2330.TW',2.5)")
        t.execute("create table us_macro(date varchar, series varchar, value double)")
        t.execute("insert into us_macro values ('2026-10-01','CPI',1)")
        t.execute("create table tw_financial(Date varchar, Ticker varchar, Source varchar, Period_Type varchar, v double)")
        t.execute("insert into tw_financial values ('2025-12-31','2330.TW','yfinance','annual',1)")
        t.close()
        before = (src / "mega" / "vdf_tw_market.duckdb").stat().st_size
        keep = {k: os.environ.get(k) for k in ENTRY}
        try:
            for k in ENTRY:
                os.environ.pop(k, None)
            rc_gate = run(["--src", str(src), "--home", str(td / "via_database")], apply=True)
            p1 = run(["--src", str(src), "--home", str(td / "via_database")], apply=False)
            plan = json.loads(RECEIPT.read_text(encoding="utf-8")) if RECEIPT.is_file() else {}
            os.environ["VIA_FROM_VDFSM"] = "YES"
            a1 = run(["--src", str(src), "--home", str(td / "via_database")], apply=True)
            a2 = run(["--src", str(src), "--home", str(td / "via_database")], apply=True)
            again = json.loads(RECEIPT.read_text(encoding="utf-8"))
        finally:
            for k, v in keep.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        q = duckdb.connect(str(home / "output_hub" / "mega" / "vdf_tw_market.duckdb"), read_only=True)
        px = q.execute("select date, ticker, close from tw_daily_prices order by 1, 2").fetchall()
        um = q.execute("select count(*) from us_macro").fetchone()[0]
        oi = q.execute("select count(*) from only_in_stage").fetchone()[0]
        fin = q.execute("select Period_Type from tw_financial order by 1").fetchall()
        q.close()
        aq = duckdb.connect(str(home / "output_hub" / "mega" / "aaii_sentiment.duckdb"), read_only=True)
        aaii_n = aq.execute("select count(*) from aaii").fetchone()[0]
        aq.close()
        tabs = {t["table"]: t for d in plan.get("dbs", []) for t in d["tables"]}
        chk("③ 沒入口旗標 apply → RED rc 1 零寫入", rc_gate == 1)
        chk("④ plan 唯讀:價表鍵 = 目標主鍵 · 待併 2(同鍵兩列只算一列 · 目標已有的 2330@11-20 不算)· 多欄 extra_x 點名 · 總經已有 = 0 · 新表 / 新庫列待併 · 黃 rc 2",
            p1 == 2 and tabs["tw_daily_prices"]["new"] == 2 and tabs["tw_daily_prices"]["key_kind"] == "主鍵"
            and tabs["tw_daily_prices"]["extra_cols"] == ["extra_x"] and tabs["us_macro"]["new"] == 0
            and tabs["only_in_stage"]["state"] == "NEW_TABLE" and any(d["state"] == "NEW_DB" for d in plan["dbs"]), tabs)
        chk("⑤ apply:只補缺 —— 既有列零觸碰(2330@11-20 收盤仍 2.5)· 補進 2018 那列與 2317 · 新表建好 · 新庫複製到資料家",
            px == [("2018-01-02", "2330.TW", 1.0), ("2026-11-20", "2317.TW", 3.0), ("2026-11-20", "2330.TW", 2.5)] and um == 1 and oi == 2
            and (home / "output_hub" / "mega" / "aaii_sentiment.duckdb").is_file() and a1 == 2, (px, um, oi, a1))
        chk("⑥ 再跑一次冪等:待併 0 · 只剩多欄黃(不寫第二次)",
            a2 == 2 and all(t.get("new", 0) == 0 for d in again["dbs"] for t in d["tables"]) and not any(d["state"] == "NEW_DB" for d in again["dbs"]), again)
        chk("⑦ 來源庫零觸碰(大小不變)", (src / "mega" / "vdf_tw_market.duckdb").stat().st_size == before)
        chk("⑦b 沒主鍵、冊上也沒鍵的財報表 → 整列當鍵:同日同代號的年 / 季兩列都保留(季報補進來,不被年報吃掉;Codex P1)",
            fin == [("annual",), ("quarterly",)] and tabs["tw_financial"]["key_kind"] == "整列" and tabs["tw_financial"]["new"] == 1, (fin, tabs.get("tw_financial")))
        chk("⑦c 新庫:來源只在 .wal 裡的已提交列也搬到(唯讀 ATTACH 套用 WAL,不整檔複製;Codex P1)", wal_left and aaii_n == 1, (wal_left, aaii_n))
        chk("⑦d 冊上業務鍵:us_macro 用 DataPlane 冊的 date + series", tabs["us_macro"]["key_kind"] == "冊上業務鍵"
            and tabs["us_macro"]["key"] == ["date", "series"], tabs["us_macro"])
        same = pairs(home / "output_hub", home)
        chk("⑧ 來源就是資料家同一實體檔 → SAME_FILE 跳過", all(p["same"] for p in same) and same, [p["rel"] for p in same])
        chk("⑨ 收據只有庫 · 表 · 鍵欄名 · 列數 · 燈(不含資料值 2330 / 33.3)",
            "33.3" not in RECEIPT.read_text(encoding="utf-8") and "2.5" not in RECEIPT.read_text(encoding="utf-8"))
    RECEIPT = keep_receipt
    src_txt = Path(__file__).read_text(encoding="utf-8")
    chk("⑩ 檔面:第 3 行加速器標記 · 雙橋 · 零 TA-Lib · 不設同意閘",
        src_txt.splitlines()[2].startswith("# [VIA:ACCEL-BRIDGE") and "[VIA:NET-BRIDGE:v0100]" in src_txt
        and not re.search(r"^\s*(import|from)\s+talib", src_txt, re.M)
        and not re.search(r"^\s*os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src_txt, re.M))
    print(f"[selftest] {TAG} {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main() -> int:
    a = sys.argv[1:]
    if a[:1] == ["--selftest"]:
        return selftest()
    if a[:1] == ["apply"]:
        return run(a[1:], apply=True)
    return run(a[1:] if a[:1] == ["plan"] else a, apply=False)


if __name__ == "__main__":
    sys.exit(main())
