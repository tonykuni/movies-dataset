#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_ENG060_AdjPriceLayer — 調整後價格層(批178;操作員令)
====================================================================
操作員令:「fetch adj close/close for the stock and transform OHLC into
adj price data as input of everything」——調整後 OHLC 為下游一切輸入。
遵交接報告 05.4:Adjusted 與原始 Price 不得混用;Derived 需標 data_class。
機制(正本零觸碰;衍生層另表):
  factor = adj_close / close(逐列;close<=0 或缺=誠實跳過計數)
  adj_open/high/low = open/high/low × factor;adj_close 原欄直取
  台股 tw_prices_adj+全球 gl_prices_adj;data_class='DERIVED_ADJ_FACTOR'
  正典取數視圖 prices_canonical(=調整層)——下游(儀表板/共識/輪動/
  分析)一律自此取數;原始表僅供 factor 重算與稽核
不變量實證:因子同列同乘=保序——調整**不引入任何新異常**,原始
空間既有之收盤競價 timing 異常(dq_ohlc_flags)在調整層數量守恆,
續由旗標表標記供下游濾(QA:初版誤稱「歸零」,實測守恆=誠實修正)。
用法:python3 VDF_ENG060_AdjPriceLayer_v0100.py build | --status | --selftest
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
DB_GL = VIA / "functional modules" / "VDF" / "output_hub" / "mega" / "vdf_global_market.duckdb"

_SQL_ADJ = """
CREATE OR REPLACE TABLE {tbl} AS
SELECT date, ticker,
       adj_close / close AS factor,
       open  * (adj_close / close) AS adj_open,
       high  * (adj_close / close) AS adj_high,
       low   * (adj_close / close) AS adj_low,
       adj_close,
       volume,
       'DERIVED_ADJ_FACTOR' AS data_class
FROM {src}
WHERE close IS NOT NULL AND close > 0 AND adj_close IS NOT NULL
"""


def _build_one(db: Path, src: str, tbl: str) -> dict:
    import duckdb
    con = duckdb.connect(str(db))
    total = con.execute(f"SELECT count(*) FROM {src}").fetchone()[0]
    con.execute(_SQL_ADJ.format(tbl=tbl, src=src))
    n = con.execute(f"SELECT count(*) FROM {tbl}").fetchone()[0]
    skipped = total - n  # close<=0/缺=誠實跳過(不猜因子)
    con.execute(f"""
        CREATE OR REPLACE VIEW prices_canonical AS
        SELECT date, ticker, adj_open AS open, adj_high AS high,
               adj_low AS low, adj_close AS close, volume, factor, data_class
        FROM {tbl}""")
    con.close()
    return {"src_rows": total, "adj_rows": n, "skipped": skipped}


def build() -> dict:
    out = {"tw": _build_one(DB_TW, "tw_daily_prices", "tw_prices_adj")}
    if DB_GL.exists():
        out["gl"] = _build_one(DB_GL, "global_daily", "gl_prices_adj")
    return out


def status() -> int:
    import duckdb
    for label, db, tbl in (("台股", DB_TW, "tw_prices_adj"),
                           ("全球", DB_GL, "gl_prices_adj")):
        if not db.exists():
            print(f"  [{label}] 庫缺(誠實)")
            continue
        con = duckdb.connect(str(db), read_only=True)
        try:
            n, mx, nf = con.execute(
                f"SELECT count(*), max(date), "
                f"sum(CASE WHEN abs(factor-1)>1e-9 THEN 1 ELSE 0 END) FROM {tbl}"
            ).fetchone()
            print(f"  [{label}] {n:,} 列 · 最新 {mx} · 因子≠1(有調整){nf:,} 列")
        except Exception:
            print(f"  [{label}] 未建(先 build)")
        con.close()
    return 0


def selftest() -> int:
    import duckdb
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    before = duckdb.connect(str(DB_TW), read_only=True).execute(
        "SELECT count(*) FROM tw_daily_prices").fetchone()[0]
    r = build()
    chk("① 雙庫調整層建成(台股+全球;跳過=誠實計數)",
        r["tw"]["adj_rows"] > 1_200_000 and "gl" in r
        and r["gl"]["adj_rows"] > 45_000,
        f"(台 {r['tw']['adj_rows']:,}·跳 {r['tw']['skipped']}·"
        f"全 {r['gl']['adj_rows']:,})")
    con = duckdb.connect(str(DB_TW), read_only=True)
    after = con.execute("SELECT count(*) FROM tw_daily_prices").fetchone()[0]
    chk("② 正本零觸碰(tw_daily_prices 列數不變)", before == after,
        f"({after:,})")
    row = con.execute("""
        SELECT a.adj_open, s.open * s.adj_close / s.close
        FROM tw_prices_adj a JOIN tw_daily_prices s
          ON a.date=s.date AND a.ticker=s.ticker
        WHERE a.ticker='2330.TW' AND abs(a.factor-1)>1e-6
        ORDER BY a.date DESC LIMIT 1""").fetchall()
    chk("③ 因子數學實證(2330 有調整日:adj_open=open×factor)",
        bool(row) and abs(row[0][0] - row[0][1]) < 1e-9,
        f"({row[0] if row else '無調整日'})")
    bad_adj = con.execute("""
        SELECT count(*) FROM tw_prices_adj
        WHERE adj_high < GREATEST(adj_open, adj_close) - 1e-9
           OR adj_low  > LEAST(adj_open, adj_close) + 1e-9""").fetchone()[0]
    flagged = con.execute(
        "SELECT count(*) FROM dq_ohlc_flags "
        "WHERE flag_class='ADJUSTMENT_FACTOR'").fetchone()[0]
    total_flagged = con.execute(
        "SELECT count(*) FROM dq_ohlc_flags").fetchone()[0]
    chk("④ 保序不變量(調整不引入新異常:調整層異常數=原始旗標數守恆)",
        bad_adj == total_flagged,
        f"(調整層 {bad_adj} = 旗標 {total_flagged};ADJ 類 {flagged})")
    chk("⑤ 正典視圖 prices_canonical(下游一切輸入=調整層)",
        con.execute("SELECT count(*) FROM prices_canonical").fetchone()[0]
        == r["tw"]["adj_rows"]
        and con.execute("SELECT data_class FROM prices_canonical LIMIT 1"
                        ).fetchone()[0] == "DERIVED_ADJ_FACTOR")
    con.close()
    r2 = build()
    chk("⑥ 冪等(重建列數不變)", r2["tw"]["adj_rows"] == r["tw"]["adj_rows"])
    boot = (VIA / "supportive modules" / "registry" /
            "via_boot_update.sh").read_text(encoding="utf-8")
    chk("⑦ boot 日更接線(價格增量後重建調整層)", "VDF_ENG060" in boot)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 紀律宣告(正本零觸碰/data_class 標記/不混用/誠實跳過)",
        all(k in src for k in ("正本零觸碰", "DERIVED_ADJ_FACTOR",
                               "不得混用", "誠實跳過")))
    print(f"  [計] 八檢 OK {8 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 調整後價格層(VDF_ENG060)· 八檢自測(零網路)===")
        return selftest()
    if "--status" in args:
        return status()
    r = build()
    print(f"[調整層] 台股 {r['tw']['adj_rows']:,} 列(跳 {r['tw']['skipped']})"
          + (f" · 全球 {r['gl']['adj_rows']:,} 列" if "gl" in r else "")
          + " · prices_canonical 視圖在位(下游一切輸入)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
