#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG238_InstHoldingPct v0101 — 薄尾:空值列可補值 · 全空欄型別修正(桌機 2026-11-11 實跑揭露)

桌機實錄(操作員貼回 2026-11-11 01:07):ENG238 v0100 run → YELLOW · 列 1,176,852 · 缺股數 1,176,852 · 新增 1,176,852。
原因兩層:
  ① 清單是 MDL009 v0102 產的(VDF 擷取冊把 MDL009 釘在 v0102)→ 沒有 shares_issued(另由 MDL008 v0108 改指 v0103)。
  ② v0100 寫庫是「鍵 date+code 已在就略過」:空值列一旦寫入,之後清單補了股數再跑也補不上;且第一次建表時持股率欄
     全是 None,DuckDB 把欄型別定成 "NULL" —— 之後就算有值也存不進去。
本版只改寫庫一步(compute / 讀庫 / 報告照 v0100):
  · 新鍵照舊只增(date+code 反連接)。
  · 舊列持股率空(inst_total_pct 為空)且本輪算得出 → 補值(UPDATE;不刪列 · 有值的列一律不動)。
  · 表上欄型別是 "NULL" / 整數的數值欄 → 先改 DOUBLE(全空欄改型別不丟資料)。
  · 報告多 duckdb_filled(補值列數)· duckdb_retyped(改型別欄)。
不碰 TA-Lib;不讀寫同意閘;零網路(只讀兩個本機庫)。
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

VERSION = "v0101"
TAG = "VDF_ENG238_InstHoldingPct " + VERSION
HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG238_InstHoldingPct"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)

VDF, OUT_TABLE, OUT_DB = PRIOR.VDF, PRIOR.OUT_TABLE, PRIOR.OUT_DB
compute, find_default = PRIOR.compute, PRIOR.find_default
NUM_COLS = ("shares_issued", "foreign_cum_shares", "trust_cum_shares", "dealer_cum_shares", "foreign_holding_pct",
            "trust_holding_pct", "dealer_holding_pct", "foreign_cum_pct", "inst_total_pct")
FILL_COLS = NUM_COLS + ("note", "basis", "basis_foreign")


def __getattr__(name):
    return getattr(PRIOR, name)


def write_db_v0101(con, df) -> dict:
    """新鍵只增;舊列持股率空且本輪有值 → 補;"NULL" / 整數型別的數值欄先改 DOUBLE。"""
    con.register("df_in", df)
    con.execute(f"CREATE TABLE IF NOT EXISTS {OUT_TABLE} AS SELECT * FROM df_in LIMIT 0")
    types = {r[0]: str(r[1]).upper() for r in con.execute(f"DESCRIBE {OUT_TABLE}").fetchall()}
    retyped = []
    for c in NUM_COLS:
        if c in types and types[c] not in ("DOUBLE", "FLOAT", "REAL", "DECIMAL"):
            con.execute(f'ALTER TABLE {OUT_TABLE} ALTER COLUMN "{c}" SET DATA TYPE DOUBLE')
            retyped.append(c)
    before = con.execute(f"SELECT COUNT(*) FROM {OUT_TABLE}").fetchall()[0][0]
    con.execute(f"INSERT INTO {OUT_TABLE} BY NAME SELECT * FROM df_in i WHERE NOT EXISTS "
                f"(SELECT 1 FROM {OUT_TABLE} t WHERE t.date = i.date AND t.code = i.code)")
    added = con.execute(f"SELECT COUNT(*) FROM {OUT_TABLE}").fetchall()[0][0] - before
    cols = [c for c in FILL_COLS if c in types and c in df.columns]
    cond = (f"t.date = i.date AND t.code = i.code AND t.inst_total_pct IS NULL AND i.inst_total_pct IS NOT NULL")
    filled = con.execute(f"SELECT COUNT(*) FROM {OUT_TABLE} t JOIN df_in i ON {cond}").fetchall()[0][0]
    if filled:
        sets = ", ".join(f'"{c}" = i."{c}"' for c in cols)
        con.execute(f"UPDATE {OUT_TABLE} t SET {sets} FROM df_in i WHERE {cond}")
    return {"duckdb_added": added, "duckdb_filled": filled, "duckdb_retyped": retyped}


def run(stock_db: Path | None, chip_db: Path | None, out: Path, anchor: str | None = None) -> dict:
    """同 v0100 run(讀庫 · compute · 燈 · 報告 · parquet / csv),只換寫庫一步。"""
    rep = {"engine": TAG, "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "stock_db": str(stock_db) if stock_db else None, "chip_db": str(chip_db) if chip_db else None}
    if not stock_db or not stock_db.is_file() or not PRIOR._has_table(stock_db, "tw_stock_list"):
        rep.update(lamp="RED", why="找不到清單庫 / tw_stock_list(先跑 MDL009 v0103 —— 要有 shares_issued)")
        return rep
    if not chip_db or not chip_db.is_file() or not PRIOR._has_table(chip_db, "tw_chip_inst"):
        rep.update(lamp="RED", why="找不到法人庫 / tw_chip_inst(先跑 ENG056 ChipBackfill)")
        return rep
    stocks = PRIOR._read(stock_db, "SELECT * FROM tw_stock_list")
    inst = PRIOR._read(chip_db, "SELECT * FROM tw_chip_inst")
    qf = PRIOR._read(chip_db, "SELECT * FROM tw_qfiis") if PRIOR._has_table(chip_db, "tw_qfiis") else []
    rows = compute(inst, stocks, qf, anchor)
    n = len(rows)
    nos = sum(1 for r in rows if r["shares_issued"] is None)
    rep.update(rows=n, codes=len({r["code"] for r in rows}), missing_shares=nos,
               official_foreign=sum(1 for r in rows if r["basis_foreign"] == "official_qfiis"),
               shares_in_list=sum(1 for s in stocks if PRIOR._f(s.get("shares_issued"))))
    rep["lamp"] = "RED" if not n else ("YELLOW" if (nos / n) > 0.05 or rep["shares_in_list"] == 0 else "GREEN")
    if rep["shares_in_list"] == 0:
        rep["why"] = ("清單沒有 shares_issued 欄值(清單是 MDL009 v0102 或更舊產的)→ 經 VDF 總控跑 MDL009(MDL008 v0108 起指 v0103)後重算;"
                      "本版重算會把先前的空值列補上")
    if not n:
        out.mkdir(parents=True, exist_ok=True)
        (out / "verify_report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        return rep
    import duckdb
    import pandas as pd
    df = pd.DataFrame(rows)
    for c in NUM_COLS:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("float64")   # 全空也定成 DOUBLE,不再建出 "NULL" 型別
    out.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out / f"{OUT_TABLE}_latest.parquet", index=False)
    df.to_csv(out / f"{OUT_TABLE}_latest.csv", index=False, encoding="utf-8-sig")
    con = duckdb.connect(str(out / OUT_DB))
    try:
        rep.update(write_db_v0101(con, df))
    finally:
        con.close()
    print(f"[{TAG}] 寫庫 · 新增 {rep['duckdb_added']} · 空值列補上 {rep['duckdb_filled']} · 改型別 {len(rep['duckdb_retyped'])} 欄")
    (out / "verify_report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return rep


def selftest() -> int:
    checks = []

    def ck(name, cond, note=""):
        checks.append((name, bool(cond)))
        print(f"  [{'OK' if cond else 'FAIL'}]   {name}" + (f" · {note}" if note else ""))

    rc0 = PRIOR.selftest()
    ck("v0100 本體自測照過(compute · 讀庫 · 燈)", rc0 == 0, f"rc {rc0}")
    try:
        import duckdb
        import pandas as pd
    except Exception as e:                                     # 沒 duckdb / pandas = 寫庫段無從驗,照實紅
        ck("duckdb / pandas 可用", False, str(e))
        duckdb = None
    if duckdb is not None:
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            s_db, c_db, out = td / "vdf_master_lists.duckdb", td / "vdf_tw_market.duckdb", td / "out"
            con = duckdb.connect(str(c_db))
            con.execute("CREATE TABLE tw_chip_inst(date DATE, code VARCHAR, market VARCHAR, foreign_net DOUBLE, trust_net DOUBLE, "
                        "dealer_net DOUBLE, total_net DOUBLE)")
            con.execute("INSERT INTO tw_chip_inst VALUES ('2026-11-03','2330','TWSE',10000,2000,-1000,11000),"
                        "('2026-11-04','2330','TWSE',5000,0,1000,6000)")
            con.close()
            con = duckdb.connect(str(s_db))
            con.execute("CREATE TABLE tw_stock_list(date VARCHAR, ticker VARCHAR, shares_issued VARCHAR)")
            con.execute("INSERT INTO tw_stock_list VALUES ('2026-11-01','2330','')")
            con.close()
            # 先用 v0100 寫出桌機那種庫(全空 → "NULL" 型別)
            r0 = PRIOR.run(s_db, c_db, out)
            con = duckdb.connect(str(out / OUT_DB))
            t0 = {r[0]: str(r[1]) for r in con.execute(f"DESCRIBE {OUT_TABLE}").fetchall()}
            con.close()
            ck("重現桌機:v0100 全空寫入 → 持股率欄型別 NULL", r0.get("duckdb_added") == 2 and "NULL" in t0.get("inst_total_pct", "").upper(),
               t0.get("inst_total_pct"))
            con = duckdb.connect(str(s_db))
            con.execute("UPDATE tw_stock_list SET shares_issued='1000000'")
            con.close()
            r1 = run(s_db, c_db, out)
            con = duckdb.connect(str(out / OUT_DB))
            got = {str(r[0])[:10]: r for r in con.execute(f"SELECT date, foreign_holding_pct, inst_total_pct, shares_issued FROM {OUT_TABLE}").fetchall()}
            t1 = {r[0]: str(r[1]) for r in con.execute(f"DESCRIBE {OUT_TABLE}").fetchall()}
            cnt = con.execute(f"SELECT COUNT(*) FROM {OUT_TABLE}").fetchall()[0][0]
            con.close()
            ck("改型別:持股率 / 股數欄 → DOUBLE", t1.get("inst_total_pct") == "DOUBLE" and t1.get("shares_issued") == "DOUBLE"
               and "inst_total_pct" in r1.get("duckdb_retyped", []), r1.get("duckdb_retyped"))
            ck("清單補股數後重算 → 空值列補上(外資 15000/1e6 = 1.5%)", r1.get("duckdb_filled") == 2 and r1.get("duckdb_added") == 0
               and abs(got["2026-11-04"][1] - 1.5) < 1e-9 and got["2026-11-04"][3] == 1e6, (r1.get("duckdb_filled"), got.get("2026-11-04")))
            ck("不刪列 · 不重複(列數仍 2)", cnt == 2, cnt)
            ck("燈:清單有股數 → GREEN", r1.get("lamp") == "GREEN", r1.get("lamp"))
            r2 = run(s_db, c_db, out)
            ck("再跑:補 0 · 增 0(有值的列不動)", r2.get("duckdb_filled") == 0 and r2.get("duckdb_added") == 0, (r2.get("duckdb_filled"), r2.get("duckdb_added")))
            out2 = td / "out2"
            con = duckdb.connect(str(s_db))
            con.execute("UPDATE tw_stock_list SET shares_issued=''")
            con.close()
            r3 = run(s_db, c_db, out2)
            con = duckdb.connect(str(out2 / OUT_DB))
            t3 = {r[0]: str(r[1]) for r in con.execute(f"DESCRIBE {OUT_TABLE}").fetchall()}
            con.close()
            ck("新庫全空也建成 DOUBLE(不再出 NULL 型別)· YELLOW 指路", t3.get("inst_total_pct") == "DOUBLE" and r3.get("lamp") == "YELLOW"
               and "MDL008 v0108" in r3.get("why", ""), t3.get("inst_total_pct"))
    src = Path(__file__).read_text(encoding="utf-8")
    ck("不碰 TA-Lib · 不寫同意閘", ("ta" + "lib") not in src.lower().replace("ta-lib", "") and "VIA_NET_CONSENT\"] =" not in src)
    names = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    ck("尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in names), f"{len(names)} 支")
    ok = sum(c for _n, c in checks)
    print(f"  [計] {TAG} 本版 {ok}/{len(checks)} · " + ("PASS" if ok == len(checks) else "FAIL"))
    return 0 if ok == len(checks) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    PRIOR.run, PRIOR.TAG, PRIOR.VERSION = run, TAG, VERSION     # v0100 的參數解析照用,跑的是本版
    return PRIOR.main(args)


if __name__ == "__main__":
    sys.exit(main())
