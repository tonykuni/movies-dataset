#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_ENG079_LocalDbConsolidate v0105 — 本機三庫整併入正典 DuckDB 引擎(薄尾:目標表有主鍵就照主鍵只補缺,不再撞主鍵)

v0104 → v0105(R40 工作站實錄 2026-10-01,`run --apply`):
  RED  rest  tw__consensus_daily.parquet:FAIL Constraint Error: Duplicate key "date: 2026-08-25, code: 2441, source: EXTERNAL_ANALYST"
  violates primary key constraint(scan 同一檔計畫 +477,apply 一列都寫不進,整單元紅)。
  根因:ENG065 協定檔的鍵律只認 date+ticker;consensus_daily 的欄是 date · code · source,鍵律回 [] = EXCEPT(整列比對)。
  正典表本身有 PRIMARY KEY(date, code, source):來源列與既有列主鍵相同、其他欄不同時,EXCEPT 當它是新列 → INSERT 撞主鍵。
  本尾版只換計畫 / 實寫兩格(_count_new · _insert_new 在本體命名空間,換掉即生效;計畫與實寫仍同一條正典 upsert_select):
    目標表有 PRIMARY KEY / UNIQUE,且那幾欄都在可寫欄內,而傳進來的鍵是空的(EXCEPT)或不在主鍵範圍內 → 改用主鍵當鍵:
    主鍵已在 = 既有列零觸碰(正本律,不覆寫);來源同主鍵多列 = 自去重只進一列(正典 upsert_select 原律)。
    表沒有主鍵 / 唯一鍵,或傳進來的鍵本來就落在主鍵內 → 一字不動照 v0104。
  台帳、路由、ENG065 協定、FRAME 守門、其餘動詞全照 v0104。零網路 · 不安裝 · 不用 TA-Lib。
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


import importlib.util
import os
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG079_LocalDbConsolidate"


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", path.stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


def _body():
    """The chain module that defines the plan / write cells itself (the v0103 body)."""
    m, seen = PRIOR, set()
    while m is not None and id(m) not in seen:
        seen.add(id(m))
        if callable(vars(m).get("_insert_new")) and callable(vars(m).get("consolidate")):
            return m
        m = vars(m).get("PRIOR")
    return None


BODY = _body()
_COUNT0, _INSERT0 = BODY._count_new, BODY._insert_new


def table_pk(con, table: str) -> list:
    """Columns of the target table's PRIMARY KEY (else its first UNIQUE constraint); [] when none / table absent."""
    try:
        rows = con.execute("SELECT constraint_type, constraint_column_names FROM duckdb_constraints() "
                           "WHERE table_name = ? AND constraint_type IN ('PRIMARY KEY', 'UNIQUE')", [table]).fetchall()
    except Exception:
        return []
    rows.sort(key=lambda r: 0 if r[0] == "PRIMARY KEY" else 1)
    return [str(c) for c in rows[0][1]] if rows else []


def keys_for(con, table: str, cols: list, keys: list) -> list:
    """Use the table's own key when the passed key could let a row through that collides with it."""
    pk = table_pk(con, table)
    if pk and set(pk) <= set(cols) and (not keys or not set(keys) <= set(pk)):
        return pk
    return list(keys)


def _count_new(con, table, cols, keys, where="", src="_src_norm"):
    return _COUNT0(con, table, cols, keys_for(con, table, cols, keys), where, src)


def _insert_new(con, table, cols, keys, where="", src="_src_norm"):
    return _INSERT0(con, table, cols, keys_for(con, table, cols, keys), where, src)


BODY._count_new, BODY._insert_new = _count_new, _insert_new


def main() -> int:
    return PRIOR.main()


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {Path(__file__).stem} · 薄尾自測(主鍵感知的只補缺)===")
    try:
        import duckdb
    except ModuleNotFoundError as exc:
        print(f"[ABSENT] duckdb 缺:{exc}(ModuleNotFoundError)")
        return 3

    def fixture(root: Path):
        s = root / "src"
        for part in ("VIA_db_part1_prices", "VIA_db_part2_chips", "VIA_db_part3_rest"):
            (s / part).mkdir(parents=True)
        (root / "reports").mkdir()
        db = root / "vdf_tw_market.duckdb"
        c = duckdb.connect(str(db))
        c.execute("CREATE TABLE consensus_daily(date DATE, code VARCHAR, source VARCHAR, tp DOUBLE, PRIMARY KEY(date, code, source))")
        c.execute("INSERT INTO consensus_daily VALUES ('2026-08-25', '2441', 'EXTERNAL_ANALYST', 100.0)")
        c.close()
        pq = (s / "VIA_db_part3_rest" / "tw__consensus_daily.parquet").as_posix()
        w = duckdb.connect()
        w.execute("COPY (SELECT * FROM (VALUES (DATE '2026-08-25', '2441', 'EXTERNAL_ANALYST', 111.0),"
                  " (DATE '2026-08-26', '2441', 'EXTERNAL_ANALYST', 120.0),"
                  " (DATE '2026-08-26', '2441', 'EXTERNAL_ANALYST', 121.0),"
                  " (DATE '2026-08-26', '2330', 'EXTERNAL_ANALYST', 900.0)) v(date, code, source, tp)) TO '" + pq + "' (FORMAT PARQUET)")
        w.close()
        return s, db

    kw = lambda r: dict(reports=r / "reports", mega=r / "mega", do_print=False)
    with tempfile.TemporaryDirectory() as td:
        r = Path(td)
        s, db = fixture(r)
        saved = BODY._count_new, BODY._insert_new
        BODY._count_new, BODY._insert_new = _COUNT0, _INSERT0          # 照 v0104:重現工作站的紅
        try:
            old = BODY.consolidate(s, db, None, apply=True, **kw(r))
        finally:
            BODY._count_new, BODY._insert_new = saved
        u0 = {u["unit"]: u for u in old["units"]}.get("tw__consensus_daily.parquet", {})
        chk("① 重現(照 v0104):主鍵表 + 協定檔無 date+ticker → EXCEPT → 撞主鍵 FAIL(工作站同一句)",
            u0.get("state") == "FAIL" and "constraint" in str(u0.get("note", "")).lower(), str(u0.get("note", ""))[:90])
    with tempfile.TemporaryDirectory() as td:
        r = Path(td)
        s, db = fixture(r)
        plan = BODY.consolidate(s, db, None, apply=False, **kw(r))
        ap = BODY.consolidate(s, db, None, apply=True, **kw(r))
        again = BODY.consolidate(s, db, None, apply=True, force=True, **kw(r))
        c = duckdb.connect(str(db), read_only=True)
        rows = c.execute("SELECT date::VARCHAR, code, tp FROM consensus_daily ORDER BY date, code").fetchall()
        c.close()
    up = {u["unit"]: u for u in plan["units"]}.get("tw__consensus_daily.parquet", {})
    ua = {u["unit"]: u for u in ap["units"]}.get("tw__consensus_daily.parquet", {})
    ug = {u["unit"]: u for u in again["units"]}.get("tw__consensus_daily.parquet", {})
    chk("② 本版:照表的主鍵 (date, code, source) 只補缺 → 不撞;計畫 = 實寫 = 2(新主鍵 2441@08-26 一列 · 2330@08-26 一列)",
        up.get("planned_new") == 2 and ua.get("state") == "OK" and ua.get("rows_new") == 2 and ap["verdict"] != "RED",
        (up.get("planned_new"), ua.get("state"), ua.get("rows_new")))
    chk("③ 既有列零觸碰(2441@08-25 仍是 100,不被來源 111 覆寫);來源同主鍵兩列只進一列;表共 3 列",
        len(rows) == 3 and rows[0] == ("2026-08-25", "2441", 100.0) and sum(1 for x in rows if x[0] == "2026-08-26" and x[1] == "2441") == 1, rows)
    chk("④ 重跑(--force 跳過台帳)冪等:新增 0、不紅", ug.get("rows_new") == 0 and ug.get("state") == "OK", (ug.get("state"), ug.get("rows_new")))
    c = duckdb.connect()
    c.execute("CREATE TABLE t(a INT, b INT)")
    c.execute("CREATE TABLE k(date DATE, ticker VARCHAR, kind VARCHAR, x INT, PRIMARY KEY(date, ticker, kind))")
    no_pk, inside = keys_for(c, "t", ["a", "b"], []), keys_for(c, "k", ["date", "ticker", "kind", "x"], ["date", "ticker", "kind"])
    sub = keys_for(c, "k", ["date", "ticker", "kind", "x"], ["date", "ticker"])
    missing = keys_for(c, "k", ["date", "ticker", "x"], [])
    c.close()
    chk("⑤ 不該改的不改:無主鍵表照 EXCEPT;傳入鍵本來就在主鍵內(含更嚴的子集)照用;主鍵欄不全在可寫欄 → 不硬用",
        no_pk == [] and inside == ["date", "ticker", "kind"] and sub == ["date", "ticker"] and missing == [], (no_pk, inside, sub, missing))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 加速器橋 · 網路橋在;不碰 TA-Lib", "VIA:ACCEL-BRIDGE" in src and "VIA:NET-BRIDGE" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M))
    print(f"  {Path(__file__).stem} 薄尾 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    rc = PRIOR.selftest()
    return rc if all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv[1:] else main())
