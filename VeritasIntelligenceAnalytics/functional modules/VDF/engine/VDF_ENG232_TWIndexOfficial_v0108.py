#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF_ENG232_TWIndexOfficial v0108 — 薄尾(v0100–v0107 一字不動):欄型修補也認「整欄空值被推成整數型」

2026-11-28 主機 diag:v0103–v0105 自測 ② ③ 不過 ——「第一批法人欄全空 → 欄型 INTEGER」「ensure_schema 修 0 欄」。
  容器 duckdb 2.0.1 把整欄空值推成 NULL 型(寫數字就報錯,v0103 會改回 DOUBLE);
  主機的 duckdb 把同一欄推成 INTEGER,之後寫 12.5 不報錯、悄悄四捨五入成 13 —— 比報錯更糟(資料默默變了)。
  v0103 的 ensure_schema 只認 NULL → 主機上修 0 欄。表是 ddl() 明示建的話數字欄一律 DOUBLE,
  所以數字欄出現任何整數型(TINYINT … BIGINT / HUGEINT · 無號版)都只可能是「第一批資料推出來的」。
本版:ensure_schema 對 NUM_COLS 裡 NULL 或任何整數型的欄一律改 DOUBLE(放寬、不丟值;原列不動);
  DOUBLE / DECIMAL / 文字欄不碰。掛在 v0103 模組層,v0103–v0107 的寫庫與自測都走本版判法。
  前版鏈 ②(負控:寫數字要報錯)在「這台 duckdb 會悄悄四捨五入」時前提不成立 —— 本版先實測這台的行為,
  成立才把那一行算已知;其餘任何一行不過照實紅。另附唯讀檢查 `--check-db <庫>`:列 tw_index_daily 數字欄的現況欄型。
零網路(自測)· 不碰 TA-Lib · 不設同意閘。
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(VDF 全導入令;惰性載入=import 時零網路、零行為變更) =====
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
except Exception:  # noqa: BLE001
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT;網路只認 AegisNexus);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import contextlib
import importlib.util
import io
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAMILY = "VDF_ENG232_TWIndexOfficial"
TAG = "VDF_ENG232_TWIndexOfficial v0108"
INT_TYPES = {"NULL", "TINYINT", "SMALLINT", "INTEGER", "BIGINT", "HUGEINT", "UTINYINT", "USMALLINT", "UINTEGER", "UBIGINT", "UHUGEINT",
             "INT1", "INT2", "INT4", "INT8", "INT"}
STALE_SIG = "② 負控:第一批法人欄全空"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0108", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)                 # v0107
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def _chain() -> list:
    out, m = [], PRIOR
    while m is not None and all(m is not x for x in out):
        out.append(m)
        m = vars(m).get("PRIOR")
    return out


V0103 = next(m for m in _chain() if callable(vars(m).get("ensure_schema")) and "NUM_COLS" in vars(m))
BASE = PRIOR.BASE
_ORIG_ENSURE = V0103.ensure_schema


def ensure_schema(db) -> dict:
    """表不在 → 照 ddl() 建(數字欄 DOUBLE);表在且數字欄型是 NULL 或任何整數型 → 改 DOUBLE。回 {created, fixed}。"""
    import duckdb
    db = Path(db)
    db.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db))
    try:
        had = BASE.TABLE in {t for (t,) in con.execute("SHOW TABLES").fetchall()}
        con.execute(V0103.ddl())
        fixed = []
        for _cid, name, typ, *_rest in con.execute("PRAGMA table_info('%s')" % BASE.TABLE).fetchall():
            if name in V0103.NUM_COLS and str(typ).strip('"').upper() in INT_TYPES:
                con.execute('ALTER TABLE %s ALTER COLUMN "%s" TYPE DOUBLE' % (BASE.TABLE, name))
                fixed.append(name)
        return {"created": not had, "fixed": fixed}
    finally:
        con.close()


V0103.ensure_schema = ensure_schema


def duckdb_rounds_silently() -> dict:
    """這台 duckdb:整欄空值推成什麼型 · 寫 12.5 是報錯還是悄悄變值(只在暫存庫)。"""
    import duckdb
    import pandas as pd
    df = pd.DataFrame([{"x": None}])  # noqa: F841
    con = duckdb.connect()
    try:
        con.execute("CREATE TABLE t AS SELECT * FROM df")
        typ = str(con.execute("PRAGMA table_info('t')").fetchall()[0][2]).strip('"').upper()
        try:
            con.execute("INSERT INTO t VALUES (12.5)")
            got = con.execute("SELECT x FROM t WHERE x IS NOT NULL").fetchone()[0]
            return {"type": typ, "error": "", "stored": got, "silent": got != 12.5}
        except Exception as exc:  # noqa: BLE001
            return {"type": typ, "error": type(exc).__name__, "stored": None, "silent": False}
    finally:
        con.close()


def check_db(db: str) -> int:
    """唯讀:列真庫 tw_index_daily 數字欄的現況欄型(整數型 = 可能已被四捨五入過)。"""
    import duckdb
    con = duckdb.connect(db, read_only=True)
    try:
        rows = {n: str(t) for _c, n, t, *_ in con.execute("PRAGMA table_info('%s')" % BASE.TABLE).fetchall()}
    finally:
        con.close()
    bad = {n: t for n, t in rows.items() if n in V0103.NUM_COLS and t.strip('"').upper() in INT_TYPES}
    print(f"[{TAG}] check-db · {Path(db).name} · {BASE.TABLE} · 數字欄 {len([n for n in rows if n in V0103.NUM_COLS])} · "
          + ("整數型 " + ", ".join(f"{n}={t}" for n, t in bad.items()) + "(寫入的小數可能已被四捨五入)" if bad else "全部是 DOUBLE(沒有被推成整數型)"))
    return 1 if bad else 0


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:240]) if note and not cond else ""), flush=True)

    print(f"[計] {TAG} 自測開始(本版 4 項 + 前版 {PRIOR_PATH.name} 鏈 · 暫存庫 · 零網路)", flush=True)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T1 加速器真的載到(VIA_ACCEL is not None)· 第 3 行標記 · 網路橋在", VIA_ACCEL is not None
        and src.splitlines()[2] == "# [VIA:ACCEL-BRIDGE:v0111]" and VIA_NET_TOOL_PATH is not None)
    import duckdb
    with tempfile.TemporaryDirectory(prefix="eng232_v0108_") as td:
        db = Path(td) / "x.duckdb"
        con = duckdb.connect(str(db))
        cols = ", ".join(["date VARCHAR", "index_code VARCHAR", "index_name VARCHAR"]
                         + [f'"{c}" ' + ("INTEGER" if c == "inst_foreign_net" else "BIGINT" if c == "volume" else "DOUBLE") for c in V0103.NUM_COLS]
                         + ["source VARCHAR", "note VARCHAR"])
        con.execute(f"CREATE TABLE {BASE.TABLE} ({cols})")
        con.execute(f"INSERT INTO {BASE.TABLE} (date, index_code, inst_foreign_net, volume, close) VALUES ('2023-01-03', 'TAIEX', 5, 7, 1.5)")
        con.close()
        s1 = ensure_schema(db)
        con = duckdb.connect(str(db))
        con.execute(f"INSERT INTO {BASE.TABLE} (date, index_code, inst_foreign_net, volume) VALUES ('2023-11-01', 'TAIEX', 12.5, 3.25)")
        got = con.execute(f"SELECT inst_foreign_net, volume, close FROM {BASE.TABLE} ORDER BY date").fetchall()
        types = {n: str(t) for _c, n, t, *_ in con.execute(f"PRAGMA table_info('{BASE.TABLE}')").fetchall()}
        con.close()
        chk("T2 數字欄被推成整數型(INTEGER · BIGINT)→ 改 DOUBLE · 原列照留 · 之後寫 12.5 / 3.25 不再被四捨五入",
            sorted(s1["fixed"]) == ["inst_foreign_net", "volume"] and got == [(5.0, 7.0, 1.5), (12.5, 3.25, None)]
            and types["inst_foreign_net"] == "DOUBLE" and types["volume"] == "DOUBLE", (s1, got, types))
        s2 = ensure_schema(db)
        chk("T3 再跑一次不重複修 · DOUBLE / 文字欄不碰", s2["fixed"] == [] and types["date"] == "VARCHAR", s2)
    probe = duckdb_rounds_silently()
    print(f"  [資訊] 這台 duckdb {duckdb.__version__}:整欄空值推成 {probe['type']} · 寫 12.5 → "
          + (f"報錯 {probe['error']}" if probe["error"] else f"存成 {probe['stored']}(悄悄變值)" if probe["silent"] else "存成 12.5"), flush=True)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = PRIOR.selftest() if callable(getattr(PRIOR, "selftest", None)) else 1
    out = buf.getvalue()
    print(out, end="")
    fails = [ln.strip() for ln in out.splitlines() if "[FAIL]" in ln]
    wrap = [ln for ln in fails if re.search(r"前版.{0,40}(自測|鏈)", ln)]
    stale = [ln for ln in fails if STALE_SIG in ln]
    other = [ln for ln in fails if ln not in wrap and ln not in stale]
    known = bool(stale) and probe["silent"] and not other and "Traceback" not in out
    chk("T4 前版鏈(v0107 → v0100)照過;或只有 ② 負控那一行不過,而且這台 duckdb 確實「悄悄變值」(②「要報錯」的前提不成立)",
        rc == 0 or known, (rc, other[:3]))
    print(f"[計] {TAG} 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    if args[:1] == ["--check-db"] and len(args) > 1:
        return check_db(args[1])
    return PRIOR.main(args) if callable(getattr(PRIOR, "main", None)) else 2


if __name__ == "__main__":
    raise SystemExit(main())
