#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG238_InstHoldingPct v0100 — 三大法人持股率(外資 / 投信 / 自營 / 合計):淨買賣超累積 ÷ 已發行股數。

操作員 2026-11-10 令「補持股率引擎」+ VDF 缺漏檢查(T5):ENG098 / ENG099 會讀 foreign_holding_pct · trust_holding_pct ·
dealer_holding_pct,倉內卻沒有任何引擎產生這三欄。本引擎只做這一件事,欄名照 ENG098(不改 ENG098)。

算法(照實,不冒充官方持股):
  · 官方日報(T86 / TPEX 3insti)只給「當日淨買賣超」(股),沒有起始持股 → 本引擎算的是「自錨點日起累積淨買賣超 ÷ 已發行股數 × 100」,
    每列帶 basis = cumsum_since:<錨點日>;錨點日 = 該股在庫內最早一筆法人資料日(或 --anchor 指定)。
  · 外資若庫內有官方外資持股比(表 tw_qfiis:date · code · foreign_hold_pct;MI_QFIIS 類)→ foreign_holding_pct 用官方值,
    basis_foreign = official_qfiis,另記 foreign_cum_pct 供對帳;沒有就用累積值並標 cumsum。
  · 分母 shares_issued 取 MDL009 v0103 清單(vdf_master_lists.duckdb · tw_stock_list)「當日或之前最近一筆」;缺 → 持股率留空 + 原因,不猜。
輸入只讀(read_only 連線);輸出寫本引擎自己的 DuckDB(vdf_tw_holding.duckdb · 表 tw_inst_holding_pct · 鍵 date+code 只增)
+ parquet / csv / 報告。不觸網、不需同意閘、不碰 TA-Lib。

  python VDF_ENG238_InstHoldingPct_v0100.py run [--stock-db P] [--chip-db P] [--out D] [--anchor YYYY-MM-DD]
  python VDF_ENG238_InstHoldingPct_v0100.py --selftest
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

import argparse
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

VERSION = "v0100"
TAG = "VDF_ENG238_InstHoldingPct " + VERSION
HERE = Path(__file__).resolve().parent
VDF = HERE.parent
NETS = (("foreign", "foreign_net"), ("trust", "trust_net"), ("dealer", "dealer_net"))
OUT_TABLE = "tw_inst_holding_pct"
OUT_DB = "vdf_tw_holding.duckdb"


def _f(v):
    try:
        return None if v in (None, "") else float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return None


def shares_lookup(stock_rows: list) -> dict:
    """{code: [(date, shares)] 依日期排序};只收有股數的列。"""
    out: dict = {}
    for r in stock_rows:
        s = _f(r.get("shares_issued"))
        if s and s > 0:
            out.setdefault(str(r.get("ticker") or r.get("code")), []).append((str(r.get("date"))[:10], s))
    for k in out:
        out[k].sort()
    return out


def shares_on(lk: dict, code: str, day: str):
    """當日或之前最近一筆股數;都在當日之後就取最早一筆並標 future_snapshot。"""
    seq = lk.get(code) or []
    if not seq:
        return None, "no_shares_issued"
    best = None
    for d, s in seq:
        if d <= day:
            best = (s, "")
    return best if best else (seq[0][1], "future_snapshot")


def compute(inst_rows: list, stock_rows: list, qfiis_rows: list | None = None, anchor: str | None = None) -> list:
    """逐股依日期累積淨買賣超 ÷ 股數 × 100。回列(欄名對齊 ENG098)。"""
    lk = shares_lookup(stock_rows)
    off = {(str(q["date"])[:10], str(q["code"])): _f(q.get("foreign_hold_pct")) for q in (qfiis_rows or [])}
    by: dict = {}
    for r in inst_rows:
        d = str(r.get("date"))[:10]
        if anchor and d < anchor:
            continue
        by.setdefault(str(r.get("code") or r.get("ticker")), []).append((d, r))
    out = []
    for code, seq in sorted(by.items()):
        seq.sort(key=lambda x: x[0])
        start = seq[0][0]
        cum = {k: 0.0 for k, _ in NETS}
        for d, r in seq:
            for k, col in NETS:
                v = _f(r.get(col))
                cum[k] += v or 0.0
            shares, why = shares_on(lk, code, d)
            row = {"date": d, "code": code, "market": r.get("market") or "", "shares_issued": shares,
                   "basis": f"cumsum_since:{start}", "note": why}
            for k, _ in NETS:
                row[f"{k}_cum_shares"] = cum[k]
                row[f"{k}_holding_pct"] = (cum[k] / shares * 100.0) if shares else None
            row["foreign_cum_pct"] = row["foreign_holding_pct"]
            row["basis_foreign"] = "cumsum"
            o = off.get((d, code))
            if o is not None:
                row["foreign_holding_pct"] = o
                row["basis_foreign"] = "official_qfiis"
            parts = [row[f"{k}_holding_pct"] for k, _ in NETS]
            row["inst_total_pct"] = sum(parts) if all(p is not None for p in parts) else None
            out.append(row)
    return out


def _read(db: Path, sql: str) -> list:
    import duckdb
    con = duckdb.connect(str(db), read_only=True)
    try:
        cur = con.execute(sql)
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, t)) for t in cur.fetchall()]
    finally:
        con.close()


def _has_table(db: Path, table: str) -> bool:
    try:
        return bool(_read(db, f"SELECT COUNT(*) AS n FROM information_schema.tables WHERE table_name = '{table}'")[0]["n"])
    except Exception:  # noqa: BLE001
        return False


def find_default(name: str) -> Path | None:
    cands = {"stock": [Path.cwd() / "vdf_master_lists.duckdb", VDF / "vdf_master_lists.duckdb", VDF.parent.parent / "vdf_master_lists.duckdb"],
             "chip": [VDF / "output_hub" / "mega" / "vdf_tw_market.duckdb", Path.cwd() / "vdf_tw_market.duckdb"]}[name]
    return next((p for p in cands if p.is_file()), None)


def run(stock_db: Path | None, chip_db: Path | None, out: Path, anchor: str | None = None) -> dict:
    rep = {"engine": TAG, "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "stock_db": str(stock_db) if stock_db else None, "chip_db": str(chip_db) if chip_db else None}
    if not stock_db or not stock_db.is_file() or not _has_table(stock_db, "tw_stock_list"):
        rep.update(lamp="RED", why="找不到清單庫 / tw_stock_list(先跑 MDL009 v0103 —— 要有 shares_issued)")
        return rep
    if not chip_db or not chip_db.is_file() or not _has_table(chip_db, "tw_chip_inst"):
        rep.update(lamp="RED", why="找不到法人庫 / tw_chip_inst(先跑 ENG056 ChipBackfill)")
        return rep
    stocks = _read(stock_db, "SELECT * FROM tw_stock_list")
    inst = _read(chip_db, "SELECT * FROM tw_chip_inst")
    qf = _read(chip_db, "SELECT * FROM tw_qfiis") if _has_table(chip_db, "tw_qfiis") else []
    rows = compute(inst, stocks, qf, anchor)
    n = len(rows)
    nos = sum(1 for r in rows if r["shares_issued"] is None)
    rep.update(rows=n, codes=len({r["code"] for r in rows}), missing_shares=nos,
               official_foreign=sum(1 for r in rows if r["basis_foreign"] == "official_qfiis"),
               shares_in_list=sum(1 for s in stocks if _f(s.get("shares_issued"))))
    rep["lamp"] = "RED" if not n else ("YELLOW" if (nos / n) > 0.05 or rep["shares_in_list"] == 0 else "GREEN")
    if rep["shares_in_list"] == 0:
        rep["why"] = "清單沒有 shares_issued 欄值(清單是 MDL009 v0102 或更舊產的)→ 跑 MDL009 v0103 後重算"
    out.mkdir(parents=True, exist_ok=True)
    (out / "verify_report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if not n:
        return rep
    import duckdb
    import pandas as pd
    df = pd.DataFrame(rows)
    df.to_parquet(out / f"{OUT_TABLE}_latest.parquet", index=False)
    df.to_csv(out / f"{OUT_TABLE}_latest.csv", index=False, encoding="utf-8-sig")
    con = duckdb.connect(str(out / OUT_DB))
    try:
        con.register("df_in", df)
        con.execute(f"CREATE TABLE IF NOT EXISTS {OUT_TABLE} AS SELECT * FROM df_in LIMIT 0")
        before = con.execute(f"SELECT COUNT(*) FROM {OUT_TABLE}").fetchall()[0][0]
        con.execute(f"INSERT INTO {OUT_TABLE} SELECT * FROM df_in i WHERE NOT EXISTS "
                    f"(SELECT 1 FROM {OUT_TABLE} t WHERE t.date = i.date AND t.code = i.code)")
        rep["duckdb_added"] = con.execute(f"SELECT COUNT(*) FROM {OUT_TABLE}").fetchall()[0][0] - before
    finally:
        con.close()
    return rep


def selftest() -> int:
    checks = []

    def ck(name, cond, note=""):
        checks.append((name, bool(cond), note))

    stocks = [{"date": "2026-11-01", "ticker": "2330", "shares_issued": "1000000"},
              {"date": "2026-11-05", "ticker": "2330", "shares_issued": "2000000"},
              {"date": "2026-11-01", "ticker": "6488", "shares_issued": ""}]
    inst = [{"date": "2026-11-03", "code": "2330", "market": "TWSE", "foreign_net": 10000, "trust_net": 2000, "dealer_net": -1000},
            {"date": "2026-11-04", "code": "2330", "market": "TWSE", "foreign_net": 5000, "trust_net": 0, "dealer_net": 1000},
            {"date": "2026-11-06", "code": "2330", "market": "TWSE", "foreign_net": 0, "trust_net": 0, "dealer_net": 0},
            {"date": "2026-11-03", "code": "6488", "market": "TPEX", "foreign_net": 1, "trust_net": 1, "dealer_net": 1}]
    rows = compute(inst, stocks)
    g = {(r["date"], r["code"]): r for r in rows}
    r4 = g[("2026-11-04", "2330")]
    ck("累積 ÷ 股數 × 100(外資 15000/1e6 = 1.5%)", abs(r4["foreign_holding_pct"] - 1.5) < 1e-9, r4["foreign_holding_pct"])
    ck("投信 / 自營照算(0.2% · 0%)", abs(r4["trust_holding_pct"] - 0.2) < 1e-9 and abs(r4["dealer_holding_pct"]) < 1e-9)
    ck("合計 = 三者相加", abs(r4["inst_total_pct"] - 1.7) < 1e-9, r4["inst_total_pct"])
    ck("分母取當日或之前最近一筆股數(11-06 用 2e6)", g[("2026-11-06", "2330")]["shares_issued"] == 2000000)
    ck("basis 標明累積錨點(不冒充官方持股)", r4["basis"] == "cumsum_since:2026-11-03" and r4["basis_foreign"] == "cumsum")
    r6488 = g[("2026-11-03", "6488")]
    ck("缺股數 → 持股率留空 + 原因(不猜)", r6488["foreign_holding_pct"] is None and r6488["note"] == "no_shares_issued")
    rows_q = compute(inst, stocks, [{"date": "2026-11-04", "code": "2330", "foreign_hold_pct": 72.3}])
    q = {(r["date"], r["code"]): r for r in rows_q}[("2026-11-04", "2330")]
    ck("有官方外資持股比 → 外資用官方值、累積值留對帳", q["foreign_holding_pct"] == 72.3 and q["basis_foreign"] == "official_qfiis"
       and abs(q["foreign_cum_pct"] - 1.5) < 1e-9)
    ck("錨點日參數生效", compute(inst, stocks, anchor="2026-11-04")[0]["basis"] == "cumsum_since:2026-11-04")
    ck("欄名對齊 ENG098", {"foreign_holding_pct", "trust_holding_pct", "dealer_holding_pct"} <= set(r4))
    try:
        import duckdb  # noqa: F401
        import pandas  # noqa: F401
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            s_db, c_db = td / "vdf_master_lists.duckdb", td / "vdf_tw_market.duckdb"
            import duckdb as _d
            con = _d.connect(str(s_db))
            con.execute("CREATE TABLE tw_stock_list(date VARCHAR, ticker VARCHAR, shares_issued VARCHAR)")
            con.execute("INSERT INTO tw_stock_list VALUES ('2026-11-01','2330','1000000')")
            con.close()
            con = _d.connect(str(c_db))
            con.execute("CREATE TABLE tw_chip_inst(date DATE, code VARCHAR, market VARCHAR, foreign_net DOUBLE, trust_net DOUBLE, dealer_net DOUBLE, total_net DOUBLE)")
            con.execute("INSERT INTO tw_chip_inst VALUES ('2026-11-03','2330','TWSE',10000,2000,-1000,11000)")
            con.close()
            rep = run(s_db, c_db, td / "out")
            ck("run:讀兩庫 · 寫本引擎庫 · GREEN", rep["lamp"] == "GREEN" and rep.get("duckdb_added") == 1, rep.get("lamp"))
            rep2 = run(s_db, c_db, td / "out")
            ck("run 重跑只增不重複(鍵 date+code)", rep2.get("duckdb_added") == 0, rep2.get("duckdb_added"))
            ck("缺清單庫 → RED + 說明下一步", run(td / "none.duckdb", c_db, td / "o2")["lamp"] == "RED")
            con = _d.connect(str(s_db))
            con.execute("DELETE FROM tw_stock_list")
            con.execute("INSERT INTO tw_stock_list VALUES ('2026-11-01','2330','')")
            con.close()
            rep3 = run(s_db, c_db, td / "o3")
            ck("清單沒股數(舊版清單)→ YELLOW + 指向 MDL009 v0103", rep3["lamp"] == "YELLOW" and "v0103" in rep3.get("why", ""))
    except ImportError as e:
        ck("duckdb / pandas 可用", False, str(e))
    ok = sum(1 for _, c, _ in checks if c)
    for n, c, note in checks:
        print(("  [OK]   " if c else "  [FAIL] ") + n + (f" — {note}" if note and not c else ""))
    print(f"  [計] {TAG} 自測 {ok}/{len(checks)} · " + ("PASS" if ok == len(checks) else "FAIL"))
    return 0 if ok == len(checks) else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="VDF_ENG238_InstHoldingPct_" + VERSION, description="三大法人持股率(累積淨買賣超 ÷ 已發行股數)")
    ap.add_argument("--selftest", action="store_true")
    sub = ap.add_subparsers(dest="verb")
    p = sub.add_parser("run")
    p.add_argument("--stock-db")
    p.add_argument("--chip-db")
    p.add_argument("--out")
    p.add_argument("--anchor")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.verb != "run":
        ap.print_help()
        return 0
    stock = Path(a.stock_db) if a.stock_db else find_default("stock")
    chip = Path(a.chip_db) if a.chip_db else find_default("chip")
    out = Path(a.out) if a.out else VDF / "output_hub" / "holding"
    rep = run(stock, chip, out, a.anchor)
    print(f"[{TAG}] {rep['lamp']} · 列 {rep.get('rows', 0)} · 股 {rep.get('codes', 0)} · 缺股數 {rep.get('missing_shares', 0)} · "
          f"官方外資 {rep.get('official_foreign', 0)} · 新增 {rep.get('duckdb_added', 0)}" + (f" · {rep['why']}" if rep.get("why") else ""))
    return {"GREEN": 0, "YELLOW": 0, "RED": 1}[rep["lamp"]]


if __name__ == "__main__":
    sys.exit(main())
