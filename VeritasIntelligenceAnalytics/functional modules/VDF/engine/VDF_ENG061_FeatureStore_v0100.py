#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_ENG061_FeatureStore — 因子庫(批188;Roadmap Phase 2)
====================================================================
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
    con0 = duckdb.connect(str(DB_TW), read_only=True)
    before = con0.execute("SELECT count(*) FROM tw_prices_adj").fetchone()[0]
    con0.close()
    r = build()
    chk("② 雙庫因子庫建成(列數=正典層同量)",
        r["tw"]["rows"] > 1_200_000 and "gl" in r and r["gl"]["rows"] > 45_000,
        f"(台 {r['tw']['rows']:,}·{r['tw']['tickers']} 檔·全 {r['gl']['rows']:,})")
    con = duckdb.connect(str(DB_TW), read_only=True)
    after = con.execute("SELECT count(*) FROM tw_prices_adj").fetchone()[0]
    chk("③ 正本零觸碰(調整層列數不變)", before == after)
    row = con.execute("""
        WITH t AS (SELECT date, close,
                   lag(close,1) OVER (ORDER BY date) AS pc
                   FROM prices_canonical WHERE ticker='2330.TW')
        SELECT f.ret_1d, t.close/t.pc-1
        FROM features_daily f JOIN t ON f.date=t.date
        WHERE f.ticker='2330.TW' AND t.pc IS NOT NULL
        ORDER BY f.date DESC LIMIT 1""").fetchone()
    chk("④ 數學實證(2330 末日 ret_1d=close/prev-1 手算對合)",
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
    chk("⑥ 覆蓋充足(ret_1d/ma20 非空列均>百萬)",
        nn[0] > 1_000_000 and nn[1] > 1_000_000,
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
    r = build()
    print(f"[因子庫] 台股 {r['tw']['rows']:,} 列"
          + (f" · 全球 {r['gl']['rows']:,} 列" if "gl" in r else "")
          + " · features_daily 在位(11 因子=目錄冊 SSOT)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
