#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v0102→v0103(批690 Z92 誠實燈):v0102 把「快照冊不在」做成 SKIP 了,但 `features_daily`(因子庫)不在時 ③ 前那句
  `SELECT count(*) FROM features_daily` 還是丟 CatalogException 整支炸掉(容器/新機因子庫沒建)。v0103:先探表,不在 →
  [NODATA] ② + ③–⑦ 誠實 SKIP、⑧ boot/紀律照檢,rc=2;預設 build 路同樣先探。八檢不變;⑧ 只寫一處(兩條路共用)。
v0101→v0102(批538 VDF 實測):整支引擎吃的是**族群分類快照冊**(ROTATION_TW_*),本境那份快照不在、
  group_features_daily 這張表也不在。舊自測的反應是:①②④ 報 FAIL,然後 ⑤ 直接一句
  `CatalogException: Table with name group_features_daily does not exist!` 把整支炸掉。
  上游沒產生 ≠ 本引擎有缺陷(LL51:缺件會 Traceback = 假紅)。
  v0102:快照/表不在 → 誠實 SKIP 並講出補法(via-datahome link / group_class),不炸不報紅;
  快照在、表也在,數字不合才是真 FAIL。誠實三態(OK/FAIL/SKIP)與 VRN_ENG068 同律。
VDF_ENG062_GroupFeatureLayer v0101(批349 快照缺=誠實 FAIL 不拋例外)— 族群聚合因子層(批193;Phase 2 續深)
====================================================================
消費鏈第三站:族群×日聚合因子=族群層儀表板/輪動觀察免重算。
  輸入 A = features_daily(VDF_ENG061 因子庫=個股因子單一正主)
  輸入 B = 最新輪動快照 latest_classification.csv(glob 尾版
           ROTATION_TW_*;GroupId×Ticker 成員對映=快照冊直出零發明)
  產出   = group_features_daily(gid×date 聚合:成員數/MA20 上方比/
           20 日平均報酬/60 日中位報酬/60 日贏家輸家/量能 Z 平均)
紀律:正本零觸碰(另表);聚合=庫內 SQL(DuckDB L1 輕型);冪等
CREATE OR REPLACE;成員對映不自造(快照冊唯一出處;快照缺=誠實空);
data_class='DERIVED_GROUP_FEATURE';零固定參數(群集自快照動態)。
用法:python3 VDF_ENG062_GroupFeatureLayer_v0100.py build | --status | --selftest
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

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent.parent
DB_TW = VIA / "functional modules" / "VDF" / "output_hub" / "mega" / "vdf_tw_market.duckdb"
ROT_ROOT = VIA / "functional modules" / "GroupIndex" / "output_hub" / "rotation_runs"

_SQL_GROUP = """
CREATE OR REPLACE TABLE group_features_daily AS
SELECT m.GroupId AS gid, f.date,
       count(*) AS n_members,
       count(*) FILTER (WHERE f.ma20_ratio IS NOT NULL) AS n_ma20,
       count(*) FILTER (WHERE f.ma20_ratio > 0) AS above_ma20,
       avg(f.ret_20d) AS avg_ret_20d,
       median(f.ret_60d) AS med_ret_60d,
       count(*) FILTER (WHERE f.ret_60d > 0) AS win60,
       count(*) FILTER (WHERE f.ret_60d < 0) AS lose60,
       avg(f.volu_z20) AS avg_volu_z20,
       'DERIVED_GROUP_FEATURE' AS data_class
FROM features_daily f
JOIN members m ON f.ticker = m.Ticker
GROUP BY m.GroupId, f.date
"""


def _latest_classification() -> Path | None:
    runs = sorted(ROT_ROOT.glob("ROTATION_TW_*")) if ROT_ROOT.exists() else []
    for r in reversed(runs):
        p = r / "csv" / "latest_classification.csv"
        if p.exists():
            return p
    return None


def build() -> dict:
    import duckdb
    cls = _latest_classification()
    if cls is None:
        return {"note": "無輪動快照成員冊(誠實空,不自造對映)"}
    con = duckdb.connect(str(DB_TW))
    con.execute(f"""
        CREATE OR REPLACE TEMP VIEW members AS
        SELECT DISTINCT GroupId, Ticker, MembershipStatus
        FROM read_csv_auto('{cls.as_posix()}')""")
    n_mem, n_gid = con.execute(
        "SELECT count(*), count(DISTINCT GroupId) FROM members").fetchone()
    con.execute(_SQL_GROUP)
    n, mx = con.execute(
        "SELECT count(*), max(date) FROM group_features_daily").fetchone()
    con.close()
    return {"rows": n, "latest": str(mx), "groups": n_gid,
            "members": n_mem, "src": cls.parent.parent.name}


def _missing_tables(db, need) -> list:
    """批690:表不在=缺料(NODATA rc2),不是壞掉(L16;批584/689B 同律)。回缺的表名;庫檔不在=全缺。"""
    if not db.exists():
        return list(need)
    import duckdb
    con = duckdb.connect(str(db), read_only=True)
    try:
        have = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
    finally:
        con.close()
    return [t for t in need if t not in have]

NEED_TABLES = ("features_daily",)
REMEDY = ("補料=`VDF_ENG061 build`(因子庫 boot ②c;其上游 `via-price` → `VDF_ENG060 build`)")


def status() -> int:
    import duckdb
    if not DB_TW.exists():
        print("  [台股] 庫缺(誠實)")
        return 0
    con = duckdb.connect(str(DB_TW), read_only=True)
    try:
        rows = con.execute("""
            SELECT gid, above_ma20, n_ma20, win60, lose60
            FROM group_features_daily
            WHERE date = (SELECT max(date) FROM group_features_daily)
            ORDER BY CAST(above_ma20 AS DOUBLE)/nullif(n_ma20,0) DESC
            LIMIT 12""").fetchall()
        print("  [族群寬度榜|最新日]")
        for g, a, n, w, l in rows:
            print(f"    {g:12s} MA20上方 {a}/{n} · 60日勝 {w}/負 {l}")
    except Exception:
        print("  [族群因子層] 未建(先 build)")
    con.close()
    return 0


def selftest() -> int:
    import duckdb
    fails = []

    skips = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    def skp(name, why=""):
        print(f"  [SKIP] {name} {why}")
        skips.append(name)

    def _chk8():                      # ⑧ 不吃料,兩條路(有料/NODATA)共用同一處判準(L05)
        boot = (VIA / "supportive modules" / "registry" /
                "via_boot_update.sh").read_text(encoding="utf-8")
        src = Path(__file__).read_text(encoding="utf-8")
        chk("⑧ boot 接線+紀律宣告(正本零觸碰/快照冊唯一出處/冪等/零固定參數)",
            "VDF_ENG062" in boot and all(k in src for k in
            ("正本零觸碰", "快照冊直出", "冪等", "零固定參數")))

    cls = _latest_classification()
    _REMEDY = "(族群分類快照冊不在=上游未產生,非本引擎缺陷;補法 via-datahome link / group_class 後複判)"
    if cls is None:
        skp("① 成員對映=快照冊直出(glob 尾版;不自造)", _REMEDY)
    else:
        chk("① 成員對映=快照冊直出(glob 尾版;不自造)",
            "ROTATION_TW_" in str(cls), f"({cls.parent.parent.name})")
    miss = _missing_tables(DB_TW, NEED_TABLES)
    if miss:                          # 批690:因子庫不在=缺料誠實 NODATA,不炸不報紅
        print(f"  [NODATA] ② 因子庫不在:{', '.join(miss)}(庫 {'在' if DB_TW.exists() else '不在'})")
        print(f"           {REMEDY}")
        print("  [SKIP] ③–⑦ 正本/聚合數學/守恆/data_class/冪等:上游沒料,誠實跳過(不是壞掉,也不假裝過)")
        _chk8()
        _ran = 2 - len([x for x in skips if x.startswith("①")])
        print(f"  [計] 八檢 OK {_ran - len(fails)} · FAIL {len(fails)} · NODATA 1 · SKIP {5 + len(skips)}(誠實多態)")
        return 1 if fails else 2
    con0 = duckdb.connect(str(DB_TW), read_only=True)
    before = con0.execute("SELECT count(*) FROM features_daily").fetchone()[0]
    con0.close()
    r = build()
    if cls is None:
        skp("② 族群因子層建成(≥10 群聚合)", _REMEDY)
    else:
        chk("② 族群因子層建成(≥10 群聚合)",
            r.get("rows", 0) > 10_000 and r.get("groups", 0) >= 10,
            f"({r.get('rows', 0):,} 列·{r.get('groups')} 群·{r.get('members')} 成員)")
    con = duckdb.connect(str(DB_TW), read_only=True)
    after = con.execute("SELECT count(*) FROM features_daily").fetchone()[0]
    chk("③ 正本零觸碰(features_daily 列數不變)", before == after)
    _has_gfd = con.execute("SELECT count(*) FROM information_schema.tables "
                           "WHERE table_name='group_features_daily'").fetchone()[0] > 0
    row = None if not _has_gfd else con.execute("""
        SELECT g.above_ma20,
          (SELECT count(*) FROM features_daily f
           JOIN (SELECT DISTINCT Ticker FROM read_csv_auto(?) WHERE GroupId=g.gid) m
             ON f.ticker=m.Ticker
           WHERE f.date=g.date AND f.ma20_ratio > 0)
        FROM group_features_daily g
        WHERE g.date=(SELECT max(date) FROM group_features_daily)
        ORDER BY g.n_members DESC LIMIT 1""", [cls.as_posix()]).fetchone() if cls is not None else None
    if cls is None or not _has_gfd:
        skp("④ 聚合數學實證(最大群最新日 above_ma20=逐檔重算對合)", _REMEDY)
        skp("⑤ 守恆不變量(勝+負≤成員數∧上方≤有值數;違反 0 列)", _REMEDY)
        skp("⑥ data_class='DERIVED_GROUP_FEATURE' 全表單一", _REMEDY)
        skp("⑦ 冪等(重建列數不變)", _REMEDY)
        con.close()
    else:
        chk("④ 聚合數學實證(最大群最新日 above_ma20=逐檔重算對合)",
            row is not None and row[0] == row[1], f"({row})")
        inv = con.execute("""
            SELECT count(*) FROM group_features_daily
            WHERE win60 + lose60 > n_members OR above_ma20 > n_ma20""").fetchone()[0]
        chk("⑤ 守恆不變量(勝+負≤成員數∧上方≤有值數;違反 0 列)", inv == 0)
        dc = con.execute(
            "SELECT DISTINCT data_class FROM group_features_daily").fetchall()
        chk("⑥ data_class='DERIVED_GROUP_FEATURE' 全表單一",
            dc == [("DERIVED_GROUP_FEATURE",)])
        con.close()
        r2 = build()
        chk("⑦ 冪等(重建列數不變)", r2.get("rows") == r.get("rows"))
    _chk8()
    print(f"  [計] 八檢 OK {8 - len(fails) - len(skips)} · FAIL {len(fails)}"
          f" · SKIP {len(skips)}(誠實三態;上游件未產生非本引擎缺陷)")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 族群聚合因子層(VDF_ENG062)· 八檢自測(零網路)===")
        return selftest()
    if "--status" in args:
        return status()
    miss = _missing_tables(DB_TW, NEED_TABLES)
    if miss:
        print(f"[NODATA] 表不在:{', '.join(miss)} —— {REMEDY}。缺料不是壞掉(L16)")
        return 2
    r = build()
    if "rows" in r:
        print(f"[族群因子層] {r['rows']:,} 列 · {r['groups']} 群×{r['members']} 成員"
              f" · 最新 {r['latest']} · 源 {r['src']}")
    else:
        print(f"[族群因子層] {r['note']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
