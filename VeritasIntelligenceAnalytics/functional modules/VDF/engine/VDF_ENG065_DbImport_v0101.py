#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_ENG065_DbImport — 資料庫 parquet 合併匯入引擎(批216;操作員令)
====================================================================
操作員問:「請提供目前已下載更新的資料庫如何取得 如何ZIP?」
→ 整庫 ZIP 373MB 超過傳輸上限(30MiB)=不可行;正道=
  雲端匯出「原始表」zstd parquet 分包(衍生層由 boot 鏈重建)
  +本引擎在工作站合併匯入。
紀律:
  只增不減=僅 INSERT;anti-join(EXCEPT 集合語意,NULL 安全)
  僅補缺列;既有列零觸碰;重跑冪等(0 新增);零網路。
檔名協定:tw__<table>.parquet → vdf_tw_market.duckdb;
          gl__<table>.parquet → vdf_global_market.duckdb;
          表缺=依 parquet 結構建表後全插(fresh 庫自舉)。
用法:python3 VDF_ENG065_DbImport_v0101.py import <資料夾>
      | --selftest
v0100→v0101(側線 2026-09-24 第十一段;主線批號由併線的手指定 L25;掉球 Z194「私有去重寫入還剩 3 支,都是關聯層」):
  `_import_one` 的去重寫入交正典 SUP_MDL753 v0111 `upsert_select`(關聯層去重寫入的唯一實作),語意逐條照舊:
  無鍵=EXCEPT 整列去重(NULL 視為相等)· 表在=共同欄照表序、零共同欄=SKIP · 表缺=`seed_all` 建表全插(fresh 庫自舉:跟雲端匯出
  逐列相同,連完全重複的列也照搬)· 回新增列數。自測 +⑨(fresh 庫完全重複列照搬 · 零共同欄 SKIP 不動表)。
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
# ===== [VIA:LIB-BRIDGE:v0100] 三庫正典橋(批597;缺席大聲拋,不 graceful) =====
import sys as _lb_sys
from functools import partial as _lb_partial
from pathlib import Path as _lb_Path
_lb_p = _lb_Path(__file__).resolve()
while _lb_p.parent != _lb_p:
    if (_lb_p / "supportive modules").is_dir():
        _lb_sys.path.insert(0, str(_lb_p / "supportive modules"))
        break
    _lb_p = _lb_p.parent
import VIA_LibCanon as _LIB          # 正典缺席=大聲拋,不假裝有(LL151)
# ===== [VIA:LIB-BRIDGE:END] =====
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

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent.parent
MEGA = VIA / "functional modules" / "VDF" / "output_hub" / "mega"
DBS = {"tw": MEGA / "vdf_tw_market.duckdb",
       "gl": MEGA / "vdf_global_market.duckdb"}


def _import_one(con, table: str, pq: Path) -> tuple[str, int]:
    """單表合併:表缺=建表全插;表在=EXCEPT anti-join 僅補缺列。
    回 (狀態, 新增列數);狀態∈ OK/SKIP。
    v0101:交正典 upsert_select(無鍵=EXCEPT 集合 anti-join,NULL 視為相等;共同欄照表序;零共同欄=None→SKIP;
    表缺 seed_all=依 parquet 結構建表全插)。"""
    pq_s = str(pq).replace("'", "''")
    n = _LIB.UTILS.upsert_select(con, table, f"read_parquet('{pq_s}')", seed_all=True)
    return ("SKIP", 0) if n is None else ("OK", n)   # 零共同欄=誠實跳過


def run_import(folder: str, dbs: dict[str, Path] | None = None) -> int:
    import duckdb
    dbs = dbs or DBS
    fdir = Path(folder)
    files = sorted(fdir.glob("*.parquet"))
    if not files:
        print(f"[匯入] {fdir} 無 parquet=誠實無事可做")
        return 2
    stats = {"OK": 0, "SKIP": 0, "rows": 0}
    cons = {}
    try:
        for pq in files:
            name = pq.stem                      # tw__table / gl__table
            if "__" not in name:
                print(f"  [SKIP] {pq.name}(不合檔名協定 tw__|gl__)")
                stats["SKIP"] += 1
                continue
            pfx, table = name.split("__", 1)
            if pfx not in dbs:
                print(f"  [SKIP] {pq.name}(未知庫前綴 {pfx})")
                stats["SKIP"] += 1
                continue
            if pfx not in cons:
                cons[pfx] = duckdb.connect(str(dbs[pfx]))
            st, n = _import_one(cons[pfx], table, pq)
            stats[st] += 1
            stats["rows"] += n
            print(f"  [{st}] {pfx}:{table} +{n:,} 列(anti-join 僅補缺;既有零觸碰)")
    finally:
        for c in cons.values():
            c.close()
    print(f"[匯入計] OK {stats['OK']} · SKIP {stats['SKIP']} · 新增 {stats['rows']:,} 列"
          f"(冪等:重跑=0 新增)")
    return 0


def selftest() -> int:
    import tempfile
    import duckdb
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    chk("① 零網路宣告(無 http 庫/僅本地檔案系統)",
        all(("import " + k) not in src for k in ("requests", "httpx", "aiohttp"))
        and ("yahoo_" + "chart") not in src)
    chk("② 檔名協定(tw__/gl__ 前綴→雙庫路由;不合=誠實 SKIP)",
        'name.split("__", 1)' in src and "tw" in DBS and "gl" in DBS)
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        seed = duckdb.connect(str(tdp / "seed.duckdb"))
        seed.execute("CREATE TABLE x(date VARCHAR, ticker VARCHAR, close DOUBLE)")
        seed.execute("INSERT INTO x VALUES ('2023-01-01','A',1.0),"
                     "('2023-01-02','B',NULL)")
        seed.execute(f"COPY x TO '{tdp}/tw__demo.parquet' (FORMAT PARQUET)")
        seed.close()
        dbs = {"tw": tdp / "t.duckdb", "gl": tdp / "g.duckdb"}
        rc1 = run_import(str(tdp), dbs)
        con = duckdb.connect(str(dbs["tw"]))
        n1 = con.execute("SELECT count(*) FROM demo").fetchone()[0]
        chk("③ fresh 庫自舉(表缺=依 parquet 建表全插)", rc1 == 0 and n1 == 2)
        con.execute("UPDATE demo SET close=9.9 WHERE ticker='A'")
        con.close()
        run_import(str(tdp), dbs)
        con = duckdb.connect(str(dbs["tw"]))
        n2 = con.execute("SELECT count(*) FROM demo").fetchone()[0]
        vA = con.execute("SELECT close FROM demo WHERE ticker='A' "
                         "AND date='2023-01-01'").fetchall()
        chk("④ 正本零觸碰(工作站改值 9.9 不被雲端值覆蓋;anti-join 補該缺列)",
            9.9 in [r[0] for r in vA])
        chk("⑤ NULL 安全冪等(EXCEPT 集合語意:NULL 列不重複插)",
            con.execute("SELECT count(*) FROM demo WHERE ticker='B'")
               .fetchone()[0] == 1)
        n3_before = n2
        run_import(str(tdp), dbs)
        n3 = con.execute("SELECT count(*) FROM demo").fetchone()[0]
        chk("⑥ 重跑冪等(第三跑 0 新增)", n3 == n3_before)
        con.close()
        (tdp / "bad.parquet").write_bytes(b"")
        rcname = run_import(str(tdp), dbs)   # bad 檔名不合協定=SKIP 不炸
        chk("⑦ 誠實三態(不合協定=SKIP;空夾=rc2)",
            rcname == 0 and run_import(str(tdp / "nothing_here_x"), dbs) == 2)
    chk("⑧ 只增不減紀律宣告(僅 INSERT;正表路徑無刪除/覆寫語句)",
        ("DELETE " + "FROM") not in src and ("DROP " + "TABLE") not in src
        and "只增不減" in src)
    # ⑨ v0101:交正典後兩條邊界照舊——fresh 庫自舉=整批照搬(連完全重複的列);零共同欄=SKIP 不動表
    with tempfile.TemporaryDirectory() as td9:
        t9 = Path(td9)
        seed = duckdb.connect(str(t9 / "seed.duckdb"))
        seed.execute("CREATE TABLE d(code VARCHAR, v DOUBLE)")
        seed.execute("INSERT INTO d VALUES ('A', 1.0), ('A', 1.0), ('B', NULL)")
        seed.execute(f"COPY d TO '{t9}/tw__dups.parquet' (FORMAT PARQUET)")
        seed.execute("CREATE TABLE o(zzz INTEGER)")
        seed.execute(f"COPY o TO '{t9}/tw__other.parquet' (FORMAT PARQUET)")
        seed.close()
        dbs9 = {"tw": t9 / "t.duckdb", "gl": t9 / "g.duckdb"}
        c9 = duckdb.connect(str(dbs9["tw"]))
        c9.execute("CREATE TABLE other(code VARCHAR)")
        c9.execute("INSERT INTO other VALUES ('keep')")
        c9.close()
        run_import(str(t9), dbs9)
        run_import(str(t9), dbs9)                                    # 重跑:表在了走 EXCEPT,0 新增
        c9 = duckdb.connect(str(dbs9["tw"]))
        st9 = _import_one(c9, "other", t9 / "tw__other.parquet")      # 零共同欄 → 狀態 SKIP(不是 OK 0)
        n9 = c9.execute("SELECT count(*) FROM dups").fetchone()[0]
        o9 = c9.execute("SELECT * FROM other").fetchall()
        oc9 = [r[0] for r in c9.execute("DESCRIBE other").fetchall()]
        c9.close()
    chk("⑨ v0101 交正典 upsert_select 邊界照舊(fresh 庫自舉=整批照搬,完全重複的列也照搬 3 列;重跑 0;零共同欄=狀態 SKIP、不加欄不動列)",
        n9 == 3 and st9 == ("SKIP", 0) and o9 == [("keep",)] and oc9 == ["code"], f"(dups {n9} · other {st9} {o9} {oc9})")
    print(f"  [計] 九檢 OK {9 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 資料庫合併匯入引擎(VDF_ENG065 v0101)· 九檢自測(零網路)===")
        return selftest()
    if args and args[0] == "import" and len(args) > 1:
        return run_import(args[1])
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
