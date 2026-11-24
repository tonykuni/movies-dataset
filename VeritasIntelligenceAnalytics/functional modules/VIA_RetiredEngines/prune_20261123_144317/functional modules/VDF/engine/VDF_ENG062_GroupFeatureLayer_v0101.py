#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
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

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    cls = _latest_classification()
    chk("① 成員對映=快照冊直出(glob 尾版;不自造)",
        cls is not None and "ROTATION_TW_" in str(cls),
        f"({cls.parent.parent.name if cls else '缺'})")
    con0 = duckdb.connect(str(DB_TW), read_only=True)
    before = con0.execute("SELECT count(*) FROM features_daily").fetchone()[0]
    con0.close()
    r = build()
    chk("② 族群因子層建成(≥10 群聚合)",
        r.get("rows", 0) > 10_000 and r.get("groups", 0) >= 10,
        f"({r.get('rows', 0):,} 列·{r.get('groups')} 群·{r.get('members')} 成員)")
    con = duckdb.connect(str(DB_TW), read_only=True)
    after = con.execute("SELECT count(*) FROM features_daily").fetchone()[0]
    chk("③ 正本零觸碰(features_daily 列數不變)", before == after)
    row = con.execute("""
        SELECT g.above_ma20,
          (SELECT count(*) FROM features_daily f
           JOIN (SELECT DISTINCT Ticker FROM read_csv_auto(?) WHERE GroupId=g.gid) m
             ON f.ticker=m.Ticker
           WHERE f.date=g.date AND f.ma20_ratio > 0)
        FROM group_features_daily g
        WHERE g.date=(SELECT max(date) FROM group_features_daily)
        ORDER BY g.n_members DESC LIMIT 1""", [cls.as_posix()]).fetchone() if cls is not None else None
    chk("④ 聚合數學實證(最大群最新日 above_ma20=逐檔重算對合)",
        row is not None and row[0] == row[1], f"({row})" if cls is not None else "(快照缺=無法實證;先 via-datahome link / group_class)")
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
    boot = (VIA / "supportive modules" / "registry" /
            "via_boot_update.sh").read_text(encoding="utf-8")
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ boot 接線+紀律宣告(正本零觸碰/快照冊唯一出處/冪等/零固定參數)",
        "VDF_ENG062" in boot and all(k in src for k in
        ("正本零觸碰", "快照冊直出", "冪等", "零固定參數")))
    print(f"  [計] 八檢 OK {8 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 族群聚合因子層(VDF_ENG062)· 八檢自測(零網路)===")
        return selftest()
    if "--status" in args:
        return status()
    r = build()
    if "rows" in r:
        print(f"[族群因子層] {r['rows']:,} 列 · {r['groups']} 群×{r['members']} 成員"
              f" · 最新 {r['latest']} · 源 {r['src']}")
    else:
        print(f"[族群因子層] {r['note']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
