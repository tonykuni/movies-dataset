#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v0102→v0103(批690 Z92 誠實燈):`tw_prices_adj`/`prices_canonical` 不在(調整層還沒建)時自測第二句 SELECT 就丟 CatalogException 整支炸掉
  (L16 缺料≠壞掉;LL51 缺件 Traceback=假紅)。v0103:先探表,不在 → [NODATA] ② + ③–⑨ 誠實 SKIP,rc=2(① 目錄冊照檢);
  預設 build 路同樣先探。表在、數字不合才是 FAIL。九檢不變。
v0101→v0102(批538 VDF 實測):④ 同樣把驗算標的寫死成 2330.TW,本境 features_daily 有 892 檔、就是沒有 2330,
  於是「無列」報紅。改成優先 2330.TW、沒有就挑任何一支**兩張表都有**的標的驗 ret_1d 手算對合;
  一支都挑不到才誠實 SKIP。檢查要能在任何一份真資料上成立,不是只在某一台機器上成立。
VDF_ENG061_FeatureStore v0101 — 因子庫(批188;Roadmap Phase 2;批368 ②⑥ 相對門檻)
====================================================================
v0100→v0101(批368 雲端實錄:②⑥ 寫死 >1,200,000/1,000,000 列=史深 2022→ 宇宙 552 檔時假紅):②=列數等於調整層(雙庫);⑥=ret_1d≥95%、ma20≥90% 列數;其餘零觸碰。
操作員 Roadmap Phase 2(批179)+平台定位令(批176:priority=庫>
分析函數>模板)。因子庫=分析基礎設施第二層:
  唯一輸入 = prices_canonical(調整價正典層,批178=下游一切輸入)
  因子 SSOT = VIA_Feature_Catalog_v0100.json(公式明載零發明;
             11 因子:報酬 4+波動 1+均線乖離 2+高低點距離 2+
             量能 Z 1+日內振幅 1)
  產出 = features_daily(雙庫;data_class='DERIVED_FEATURE')
紀律:正本零觸碰(另表);視窗不足=NULL 誠實不外插;冪等
CREATE OR REPLACE;DuckDB SQL 庫內原地(批181 階梯 DATAFRAME L1
輕型優先);零網路;零固定參數(視窗自目錄冊載入)。
用法:python3 VDF_ENG061_FeatureStore_v0100.py build | --status | --selftest
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
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent.parent
DB_TW = VIA / "functional modules" / "VDF" / "output_hub" / "mega" / "vdf_tw_market.duckdb"
DB_GL = VIA / "functional modules" / "VDF" / "output_hub" / "mega" / "vdf_global_market.duckdb"
CATALOG_P = VIA / "supportive modules" / "registry" / "VIA_Feature_Catalog_v0100.json"

# 因子 SQL(公式=目錄冊 formula 欄之 DuckDB 實作;視窗不足→NULL:
# cnt 檢查=該視窗內實有列數不足宣告視窗即誠實 NULL)
_SQL_FEATURES = """
CREATE OR REPLACE TABLE features_daily AS
WITH base AS (
  SELECT date, ticker, open, high, low, close, volume,
         row_number() OVER w AS rn,
         close / nullif(lag(close, 1) OVER w, 0) - 1 AS _r1
  FROM prices_canonical
  WINDOW w AS (PARTITION BY ticker ORDER BY date)
)
SELECT date, ticker,
  CASE WHEN rn >= 2  THEN close / nullif(lag(close, 1)  OVER w, 0) - 1 END AS ret_1d,
  CASE WHEN rn >= 6  THEN close / nullif(lag(close, 5)  OVER w, 0) - 1 END AS ret_5d,
  CASE WHEN rn >= 21 THEN close / nullif(lag(close, 20) OVER w, 0) - 1 END AS ret_20d,
  CASE WHEN rn >= 61 THEN close / nullif(lag(close, 60) OVER w, 0) - 1 END AS ret_60d,
  CASE WHEN rn >= 21 THEN stddev_samp(_r1) OVER (w ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) * sqrt(252) END AS vol_20d_ann,
  CASE WHEN rn >= 20 THEN close / nullif(avg(close) OVER (w ROWS BETWEEN 19 PRECEDING AND CURRENT ROW), 0) - 1 END AS ma20_ratio,
  CASE WHEN rn >= 60 THEN close / nullif(avg(close) OVER (w ROWS BETWEEN 59 PRECEDING AND CURRENT ROW), 0) - 1 END AS ma60_ratio,
  CASE WHEN rn >= 252 THEN close / nullif(max(high) OVER (w ROWS BETWEEN 251 PRECEDING AND CURRENT ROW), 0) - 1 END AS hi252_dist,
  CASE WHEN rn >= 252 THEN close / nullif(min(low)  OVER (w ROWS BETWEEN 251 PRECEDING AND CURRENT ROW), 0) - 1 END AS lo252_dist,
  CASE WHEN rn >= 20 THEN (volume - avg(volume) OVER (w ROWS BETWEEN 19 PRECEDING AND CURRENT ROW))
       / nullif(stddev_samp(volume) OVER (w ROWS BETWEEN 19 PRECEDING AND CURRENT ROW), 0) END AS volu_z20,
  (high - low) / nullif(close, 0) AS rng_1d,
  'DERIVED_FEATURE' AS data_class
FROM base
WINDOW w AS (PARTITION BY ticker ORDER BY date)
"""


def _load_catalog() -> dict:
    return json.loads(CATALOG_P.read_text(encoding="utf-8"))


def _build_one(db: Path) -> dict:
    import duckdb
    con = duckdb.connect(str(db))
    con.execute(_SQL_FEATURES)
    n, tk = con.execute(
        "SELECT count(*), count(DISTINCT ticker) FROM features_daily"
    ).fetchone()
    con.close()
    return {"rows": n, "tickers": tk}


def build() -> dict:
    out = {"tw": _build_one(DB_TW)}
    if DB_GL.exists():
        out["gl"] = _build_one(DB_GL)
    return out


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

NEED_TABLES = ("tw_prices_adj", "prices_canonical")
REMEDY = ("補料=`via-price`(價格增量)後 `VDF_ENG060 build`(調整層 boot ②b)再 `VDF_ENG061 build`(boot ②c)")


def status() -> int:
    import duckdb
    cat = _load_catalog()
    print(f"  [目錄冊] {len(cat['features'])} 因子(SSOT 公式明載)")
    for label, db in (("台股", DB_TW), ("全球", DB_GL)):
        if not db.exists():
            print(f"  [{label}] 庫缺(誠實)")
            continue
        con = duckdb.connect(str(db), read_only=True)
        try:
            n, mx = con.execute(
                "SELECT count(*), max(date) FROM features_daily").fetchone()
            print(f"  [{label}] features_daily {n:,} 列 · 最新 {mx}")
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

    cat = _load_catalog()
    chk("① 因子目錄冊 SSOT(11 因子公式明載+append-only+正典輸入契約)",
        len(cat["features"]) == 11 and cat["append_only"] is True
        and "prices_canonical" in cat["input_contract"]["source"])
    miss = _missing_tables(DB_TW, NEED_TABLES)
    if miss:                          # 批690:缺料誠實 NODATA,不炸不報紅
        print(f"  [NODATA] ② 調整層/正典視圖不在:{', '.join(miss)}(庫 {'在' if DB_TW.exists() else '不在'})")
        print(f"           {REMEDY}")
        print("  [SKIP] ③–⑨ 正本/數學/NULL/覆蓋/data_class/冪等/boot:上游沒料,誠實跳過(不是壞掉,也不假裝過)")
        print(f"  [計] 九檢 OK {1 - len(fails)} · FAIL {len(fails)} · NODATA 1 · SKIP 7(誠實多態)")
        return 1 if fails else 2
    con0 = duckdb.connect(str(DB_TW), read_only=True)
    before = con0.execute("SELECT count(*) FROM tw_prices_adj").fetchone()[0]
    con0.close()
    r = build()
    con_g = duckdb.connect(str(DB_GL), read_only=True) if DB_GL.exists() else None
    gl_adj = con_g.execute("SELECT count(*) FROM gl_prices_adj").fetchone()[0] if con_g else 0
    if con_g:
        con_g.close()
    chk("② 雙庫因子庫建成(列數=調整層同量;批368 相對律)",
        r["tw"]["rows"] > 0 and r["tw"]["rows"] == before and "gl" in r and r["gl"]["rows"] > 0 and r["gl"]["rows"] == gl_adj,
        f"(台 {r['tw']['rows']:,}·{r['tw']['tickers']} 檔·全 {r['gl']['rows']:,})")
    con = duckdb.connect(str(DB_TW), read_only=True)
    after = con.execute("SELECT count(*) FROM tw_prices_adj").fetchone()[0]
    chk("③ 正本零觸碰(調整層列數不變)", before == after)
    def _math_row(tk):
        return con.execute("""
        WITH t AS (SELECT date, close,
                   lag(close,1) OVER (ORDER BY date) AS pc
                   FROM prices_canonical WHERE ticker=?)
        SELECT f.ret_1d, t.close/t.pc-1
        FROM features_daily f JOIN t ON f.date=t.date
        WHERE f.ticker=? AND t.pc IS NOT NULL
        ORDER BY f.date DESC LIMIT 1""", [tk, tk]).fetchone()
    _tk = "2330.TW"
    row = _math_row(_tk)
    if row is None:                  # 批538:本庫沒有 2330.TW 就挑任何一支兩張表都有的標的
        _cand = con.execute("SELECT f.ticker FROM features_daily f "
                            "JOIN prices_canonical p ON p.ticker=f.ticker "
                            "GROUP BY f.ticker HAVING count(*)>1 LIMIT 1").fetchone()
        if _cand:
            _tk = _cand[0]
            row = _math_row(_tk)
    chk(f"④ 批538 數學實證({_tk} 末日 ret_1d=close/prev-1 手算對合;取任一兩表都有的標的,不綁 2330)",
        row is not None and abs(row[0] - row[1]) < 1e-12,
        f"({row[0]:.6f} vs {row[1]:.6f})" if row else "(無列)")
    head_null = con.execute("""
        SELECT count(*) FROM (
          SELECT ret_60d, row_number() OVER (PARTITION BY ticker ORDER BY date) rn
          FROM features_daily WHERE ticker='2330.TW') WHERE rn <= 60 AND ret_60d IS NOT NULL
        """).fetchone()[0]
    chk("⑤ 視窗不足=NULL 誠實(2330 前 60 列 ret_60d 全 NULL 不外插)",
        head_null == 0)
    nn = con.execute("""
        SELECT sum(CASE WHEN ret_1d IS NOT NULL THEN 1 ELSE 0 END),
               sum(CASE WHEN ma20_ratio IS NOT NULL THEN 1 ELSE 0 END)
        FROM features_daily""").fetchone()
    chk("⑥ 覆蓋充足(ret_1d≥95%·ma20≥90% 列數;批368 相對律)",
        nn[0] >= 0.95 * r["tw"]["rows"] and nn[1] >= 0.90 * r["tw"]["rows"],
        f"(ret_1d {nn[0]:,}·ma20 {nn[1]:,})")
    dc = con.execute("SELECT DISTINCT data_class FROM features_daily").fetchall()
    chk("⑦ data_class='DERIVED_FEATURE' 全表單一", dc == [("DERIVED_FEATURE",)])
    con.close()
    r2 = build()
    chk("⑧ 冪等(重建列數不變)", r2["tw"]["rows"] == r["tw"]["rows"])
    boot = (VIA / "supportive modules" / "registry" /
            "via_boot_update.sh").read_text(encoding="utf-8")
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑨ boot 接線+紀律宣告(正本零觸碰/NULL 誠實/冪等/零固定參數)",
        "VDF_ENG061" in boot and all(k in src for k in
        ("正本零觸碰", "誠實不外插", "冪等", "零固定參數")))
    print(f"  [計] 九檢 OK {9 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 因子庫(VDF_ENG061)· 九檢自測(零網路)===")
        return selftest()
    if "--status" in args:
        return status()
    miss = _missing_tables(DB_TW, NEED_TABLES)
    if miss:
        print(f"[NODATA] 表不在:{', '.join(miss)} —— {REMEDY}。缺料不是壞掉(L16)")
        return 2
    r = build()
    print(f"[因子庫] 台股 {r['tw']['rows']:,} 列"
          + (f" · 全球 {r['gl']['rows']:,} 列" if "gl" in r else "")
          + " · features_daily 在位(11 因子=目錄冊 SSOT)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
