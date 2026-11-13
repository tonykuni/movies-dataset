#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG238_InstHoldingPct v0102 — 薄尾:股數也讀 MDL009 同輪 latest.parquet(清單庫同日重跑補不到新欄)

桌機實錄(操作員貼回 2026-11-11 02:16):總控 fetch run MDL009 → [OK] 49.4s(冊 v0108 已指 v0103);ENG238 v0101 run → 改型別 6 欄,
但仍「缺股數 1,176,852 · 補 0」。根因在清單庫的寫法(MDL009 v0100 起):DuckDB tw_stock_list 以 date + ticker 反連接只補新列 ——
今天稍早 v0102 已寫過同日列,v0103 同日重跑只 ALTER ADD COLUMN 新欄、舊列新欄全 NULL → 庫裡今天沒有 shares_issued。
MDL009 同一輪寫的 <清單庫夾>/0-1-TWStockList/tw_stock_list_latest.parquet 則是 v0103 全欄(含股數)。
本版只改「讀清單」一步:清單列 = 庫列 + latest.parquet 列(同 date + ticker 以有股數者為準);其餘(compute · 補值寫庫 · 改型別)照 v0101。
明天起清單庫新日期列本來就帶股數;本版讓今天就能算,不必改 MDL009 / 擷取冊(不擴範圍)。
另:v0101 自測「重現桌機 NULL 型別」判準太窄 —— 桌機 DuckDB 把全空欄定成 INTEGER(容器版定成 "NULL");本版判準 = 「不是 DOUBLE」。
不碰 TA-Lib;不讀寫同意閘;零網路(只讀本機庫 / 檔)。
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

import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path

VERSION = "v0102"
TAG = "VDF_ENG238_InstHoldingPct " + VERSION
HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG238_InstHoldingPct"
LIST_PARQUET = Path("0-1-TWStockList") / "tw_stock_list_latest.parquet"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
P0 = PRIOR.PRIOR                                            # v0100(_read · _has_table · compute)
OUT_TABLE, OUT_DB, NUM_COLS = PRIOR.OUT_TABLE, PRIOR.OUT_DB, PRIOR.NUM_COLS


def __getattr__(name):
    return getattr(PRIOR, name)


def list_parquet(stock_db: Path | None) -> Path | None:
    if not stock_db:
        return None
    for base in (Path(stock_db).parent, Path(stock_db).parent.parent):
        p = base / LIST_PARQUET
        if p.is_file():
            return p
    return None


def read_list_rows_v0102(stock_db: Path) -> tuple[list, dict]:
    """清單列 = 庫 tw_stock_list + latest.parquet;同 (date, ticker) 有股數者勝。回 (列, 來源統計)。"""
    rows = P0._read(stock_db, "SELECT * FROM tw_stock_list")
    st = {"db_rows": len(rows), "db_with_shares": sum(1 for r in rows if P0._f(r.get("shares_issued"))), "parquet": None, "parquet_rows": 0,
          "parquet_with_shares": 0}
    pq = list_parquet(stock_db)
    if pq is not None:
        try:
            import pandas as pd
            prow = pd.read_parquet(pq).to_dict("records")
        except Exception as e:                                   # 讀不了照實記,不中斷
            st["parquet"] = f"{pq} · 讀取失敗 {type(e).__name__}"
            prow = []
        else:
            st["parquet"] = str(pq)
        st["parquet_rows"] = len(prow)
        st["parquet_with_shares"] = sum(1 for r in prow if P0._f(r.get("shares_issued")))
        key = {(str(r.get("date"))[:10], str(r.get("ticker"))): i for i, r in enumerate(rows)}
        for r in prow:
            k = (str(r.get("date"))[:10], str(r.get("ticker")))
            if k in key:
                if P0._f(r.get("shares_issued")) and not P0._f(rows[key[k]].get("shares_issued")):
                    rows[key[k]] = dict(rows[key[k]], **{c: r.get(c) for c in r})
            else:
                key[k] = len(rows)
                rows.append(r)
    return rows, st


def run(stock_db: Path | None, chip_db: Path | None, out: Path, anchor: str | None = None) -> dict:
    """同 v0101 run;清單改讀「庫 + latest.parquet」。"""
    if not stock_db or not Path(stock_db).is_file() or not P0._has_table(stock_db, "tw_stock_list"):
        return PRIOR.run(stock_db, chip_db, out, anchor)        # 缺庫的 RED 訊息照 v0101
    merged, st = read_list_rows_v0102(stock_db)
    keep = P0._read
    P0._read = lambda db, sql: merged if (Path(db) == Path(stock_db) and sql.strip() == "SELECT * FROM tw_stock_list") else keep(db, sql)
    try:
        rep = PRIOR.run(stock_db, chip_db, out, anchor)
    finally:
        P0._read = keep
    rep["engine"] = TAG
    rep["list_sources"] = st
    if st["parquet_with_shares"] and rep.get("why", "").startswith("清單沒有 shares_issued"):
        rep.pop("why", None)
    print(f"[{TAG}] 清單來源 · 庫 {st['db_rows']} 列(有股數 {st['db_with_shares']})· latest.parquet {st['parquet_rows']} 列"
          f"(有股數 {st['parquet_with_shares']})" + ("" if st["parquet"] else " · 找不到 latest.parquet(先經總控跑 MDL009)"))
    if out and Path(out).is_dir():
        (Path(out) / "verify_report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8")
    return rep


def selftest() -> int:
    checks = []

    def ck(name, cond, note=""):
        checks.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}]   {name}" + (f" · {note}" if note else ""))

    rc0 = P0.selftest()
    ck("v0100 本體自測照過(compute · 讀庫 · 燈)", rc0 == 0, f"rc {rc0}")
    try:
        import duckdb
        import pandas as pd
    except Exception as e:
        ck("duckdb / pandas 可用", False, str(e))
        return 1
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        s_db, c_db, out = td / "vdf_master_lists.duckdb", td / "vdf_tw_market.duckdb", td / "out"
        con = duckdb.connect(str(c_db))
        con.execute("CREATE TABLE tw_chip_inst(date DATE, code VARCHAR, market VARCHAR, foreign_net DOUBLE, trust_net DOUBLE, "
                    "dealer_net DOUBLE, total_net DOUBLE)")
        con.execute("INSERT INTO tw_chip_inst VALUES ('2026-11-03','2330','TWSE',10000,2000,-1000,11000),"
                    "('2026-11-04','2330','TWSE',5000,0,1000,6000)")
        con.close()
        con = duckdb.connect(str(s_db))                          # 桌機實況:庫只有舊欄 + 新欄 NULL(同日重跑補不到)
        con.execute("CREATE TABLE tw_stock_list(date VARCHAR, ticker VARCHAR, name VARCHAR, shares_issued VARCHAR)")
        con.execute("INSERT INTO tw_stock_list VALUES ('2026-11-11','2330','台積電',NULL)")
        con.close()
        r0 = P0.run(s_db, c_db, out)
        con = duckdb.connect(str(out / OUT_DB))
        t0 = {r[0]: str(r[1]).upper() for r in con.execute(f"DESCRIBE {OUT_TABLE}").fetchall()}
        con.close()
        ck("重現桌機:v0100 全空寫入 → 持股率欄不是 DOUBLE(容器 NULL · 桌機 INTEGER 都算)",
           r0.get("duckdb_added") == 2 and t0.get("inst_total_pct") not in ("DOUBLE", "FLOAT", "REAL"), t0.get("inst_total_pct"))
        r1 = run(s_db, c_db, out)
        ck("沒有 latest.parquet → 照 v0101(YELLOW · 補 0)· 報找不到", r1.get("lamp") == "YELLOW" and r1.get("duckdb_filled") == 0
           and r1["list_sources"]["parquet"] is None, r1.get("lamp"))
        (td / LIST_PARQUET).parent.mkdir(parents=True)
        pd.DataFrame([{"date": "2026-11-11", "ticker": "2330", "name": "台積電", "shares_issued": "1000000"}]).to_parquet(td / LIST_PARQUET, index=False)
        r2 = run(s_db, c_db, out)
        con = duckdb.connect(str(out / OUT_DB))
        got = {str(r[0])[:10]: r for r in con.execute(f"SELECT date, foreign_holding_pct, shares_issued FROM {OUT_TABLE}").fetchall()}
        cnt = con.execute(f"SELECT COUNT(*) FROM {OUT_TABLE}").fetchall()[0][0]
        con.close()
        ck("庫缺股數 · latest.parquet 有 → 用 parquet 股數補上空值列(外資 15000/1e6 = 1.5%)",
           r2.get("duckdb_filled") == 2 and abs(got["2026-11-04"][1] - 1.5) < 1e-9 and r2["list_sources"]["parquet_with_shares"] == 1,
           (r2.get("duckdb_filled"), got.get("2026-11-04")))
        ck("不刪列 · 不重複(列數仍 2)· GREEN · 不再報『清單沒有股數』", cnt == 2 and r2.get("lamp") == "GREEN" and "why" not in r2, (cnt, r2.get("lamp")))
        ck("清單庫本身一字不動(只讀)", duckdb.connect(str(s_db), read_only=True).execute(
            "SELECT shares_issued FROM tw_stock_list").fetchall() == [(None,)])
        rows, _st = read_list_rows_v0102(s_db)
        ck("同 date + ticker 合併成一列(不重複)", len(rows) == 1 and rows[0]["shares_issued"] == "1000000", len(rows))
    src = Path(__file__).read_text(encoding="utf-8")
    ck("不碰 TA-Lib · 不寫同意閘", ("ta" + "lib") not in src.lower().replace("ta-lib", "") and "VIA_NET_CONSENT\"] =" not in src)
    names = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    ck("尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in names), f"{len(names)} 支")
    print(f"  [計] {TAG} 本版 {sum(checks)}/{len(checks)} · " + ("PASS" if all(checks) else "FAIL"))
    return 0 if all(checks) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    P0.run, P0.TAG, P0.VERSION = run, TAG, VERSION              # v0100 的參數解析照用,跑的是本版
    return P0.main(args)


if __name__ == "__main__":
    sys.exit(main())
