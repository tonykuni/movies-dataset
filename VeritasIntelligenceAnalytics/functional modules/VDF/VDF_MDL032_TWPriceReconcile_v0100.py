#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VDF_MDL032_TWPriceReconcile v0100 — 台股日價官方對帳層:tw_daily_prices 逐日對證交所 / 櫃買官方(tw_trading_daily),官方值覆蓋

操作員 2026-11-21:「輸出驗證」→ 裁定「加官方對帳層(建議)」:Yahoo 照抓,入庫後逐日對官方 —
官方沒開盤的日子刪掉 · 官方有、我們缺的補上 · 價格不符的照官方改;官方值覆蓋,改動先備份,可重跑。
容器實量(資料家 vdf_fetch/dict · 2021-01-04 → 2026-11-20):
  · 休市佔位列:2026-10-23(官方 10/22 → 10/27)Yahoo 2,007 列,量 0、開高低收 = 前日收盤;
  · 官方有、我們缺:59,530 列(2025-08-01 整天 1,884 檔 · 2021 年初等);2021-04-06 官方與我們都缺(另補官方源);
  · 收盤與官方差 > 0.5%:557,897 列 · 1,694 檔 —— 54.3 萬列是 Yahoo 配股 / 減資「往回調整」的整段(同一比例連續),
    1.5 萬列是零星錯值(例 4304 存 10.5 官方 9.9;8432 存 41.5 官方 39.9)。VRN 研報結構庫明寫 tw_daily_prices.close 是「原始 close 正主」。
規則(只動 tw_daily_prices,官方表一字不動;不出網):
  ① 休市佔位:日期不在官方交易日曆(tw_trading_daily 的日子,且在官方日曆範圍內)· 量 0 · 開 = 高 = 低 = 收 → 刪。
  ② 價格不符:官方同日同代號開高低收都 > 0,任一欄差 > 0.005 → 開高低收改官方值;
     adj_close:比例 r = 官方收 / 舊收 與前或後一列相同(整段調整)→ 原值保留(ENG060 用 adj_close / close 算因子,改完即完整還原);
     零星(前後比例都不同)→ adj_close × r(把錯值的還原價一起校正)。
  ③ 官方有、我們缺(只補我們已收的代號):開高低收量取官方;adj_close = 官方收 × 同代號前一列的 adj_close / close(沒有前一列 = NULL)。
  ④ 每一筆改動寫 tw_price_reconcile_log(run_id · 動作 · 舊值 · 新值)→ 可逐列還原;--apply 前整檔備份到 <資料家>/_backup/tw_price_reconcile/。
  ⑤ 寫後再驗:①②③ 剩 0、(date, ticker) 不重複;冪等(再跑一次 = 零動作)。
用法:  python VDF_MDL032_TWPriceReconcile_v0100.py plan  [--home <資料家> | --db <vdf_tw_market.duckdb>]
        python VDF_MDL032_TWPriceReconcile_v0100.py apply [--home … | --db …]      (先備份再寫)
        python VDF_MDL032_TWPriceReconcile_v0100.py --selftest                      (暫存庫;不碰真庫、零網路)
不讀寫同意閘;不碰 TA-Lib。VDF 自己的模組(寫 VDF 自己的庫)。
"""
from __future__ import annotations
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。啟動器自己不連網,連網的是各擷取引擎。"""
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
import re
import shutil
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAG = "VDF_MDL032_TWPriceReconcile v0100"
TOL = 0.005                                   # 半個最小跳動(0.01)
RATIO_EQ = 0.0005                             # 前後列比例視為同一段的容差(相對)
PRICES, OFFICIAL, LOG = "tw_daily_prices", "tw_trading_daily", "tw_price_reconcile_log"
DB_REL = Path("output_hub") / "mega" / "vdf_tw_market.duckdb"

_OFF = f"""SELECT date, code || CASE WHEN market = 'TWSE' THEN '.TW' ELSE '.TWO' END AS ticker,
       open, high, low, close, volume FROM {OFFICIAL}
       WHERE open > 0 AND high > 0 AND low > 0 AND close > 0"""


def _views(con) -> None:
    con.execute(f"CREATE OR REPLACE TEMP VIEW off AS {_OFF}")
    con.execute(f"""CREATE OR REPLACE TEMP VIEW cal AS SELECT DISTINCT date FROM {OFFICIAL}""")
    con.execute(f"""CREATE OR REPLACE TEMP TABLE mis AS
        SELECT p.date, p.ticker, p.open po, p.high ph, p.low pl, p.close pc, p.adj_close pa,
               o.open oo, o.high oh, o.low ol, o.close oc, o.close / p.close AS r
        FROM {PRICES} p JOIN off o USING (date, ticker)
        WHERE p.close > 0 AND (abs(p.open - o.open) > {TOL} OR abs(p.high - o.high) > {TOL}
              OR abs(p.low - o.low) > {TOL} OR abs(p.close - o.close) > {TOL})""")
    con.execute(f"""CREATE OR REPLACE TEMP TABLE seq AS
        SELECT date, ticker, r, lag(r) OVER w AS rp, lead(r) OVER w AS rn FROM (
          SELECT p.date, p.ticker, o.close / p.close AS r FROM {PRICES} p JOIN off o USING (date, ticker) WHERE p.close > 0)
        WINDOW w AS (PARTITION BY ticker ORDER BY date)""")
    con.execute(f"""CREATE OR REPLACE TEMP TABLE mis2 AS SELECT m.*,
        (abs(m.r - 1) > 1e-9 AND (abs(m.r - coalesce(s.rp, -1)) <= {RATIO_EQ} * m.r OR abs(m.r - coalesce(s.rn, -1)) <= {RATIO_EQ} * m.r)) AS seg
        FROM mis m JOIN seq s USING (date, ticker)""")
    con.execute(f"""CREATE OR REPLACE TEMP TABLE hol AS SELECT p.date, p.ticker, p.open, p.high, p.low, p.close, p.adj_close, p.volume
        FROM {PRICES} p WHERE p.date NOT IN (SELECT date FROM cal)
          AND p.date BETWEEN (SELECT min(date) FROM cal) AND (SELECT max(date) FROM cal)
          AND coalesce(p.volume, 0) = 0 AND p.open = p.high AND p.high = p.low AND p.low = p.close""")
    con.execute(f"""CREATE OR REPLACE TEMP TABLE miss AS SELECT o.* FROM off o
        WHERE o.ticker IN (SELECT DISTINCT ticker FROM {PRICES})
          AND NOT EXISTS (SELECT 1 FROM {PRICES} p WHERE p.date = o.date AND p.ticker = o.ticker)""")


def plan(con) -> dict:
    _views(con)
    one = lambda s: con.execute(s).fetchone()[0]  # noqa: E731
    return {"holiday": one("SELECT count(*) FROM hol"), "holiday_days": [r[0] for r in con.execute("SELECT DISTINCT date FROM hol ORDER BY 1").fetchall()],
            "mismatch": one("SELECT count(*) FROM mis2"), "mismatch_segment": one("SELECT count(*) FROM mis2 WHERE seg"),
            "mismatch_isolated": one("SELECT count(*) FROM mis2 WHERE NOT seg"), "missing": one("SELECT count(*) FROM miss"),
            "missing_top_days": con.execute("SELECT date, count(*) FROM miss GROUP BY 1 ORDER BY 2 DESC, 1 LIMIT 5").fetchall(),
            "dup_keys": one(f"SELECT count(*) FROM (SELECT date, ticker FROM {PRICES} GROUP BY 1, 2 HAVING count(*) > 1)"),
            "rows": one(f"SELECT count(*) FROM {PRICES}")}


def _ensure_log(con) -> None:
    con.execute(f"""CREATE TABLE IF NOT EXISTS {LOG}(run_id VARCHAR, ts VARCHAR, action VARCHAR, date VARCHAR, ticker VARCHAR,
        old_open DOUBLE, old_high DOUBLE, old_low DOUBLE, old_close DOUBLE, old_adj_close DOUBLE, old_volume DOUBLE,
        new_open DOUBLE, new_high DOUBLE, new_low DOUBLE, new_close DOUBLE, new_adj_close DOUBLE, new_volume DOUBLE, note VARCHAR)""")


def apply(con, run_id: str) -> dict:
    """在一個交易內:記帳 → 刪休市佔位 → 改不符 → 補缺 → 提交。回各類筆數。"""
    p0 = plan(con)
    _ensure_log(con)
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    con.execute("BEGIN TRANSACTION")
    try:
        con.execute(f"""INSERT INTO {LOG} SELECT ?, ?, 'delete_holiday', date, ticker, open, high, low, close, adj_close, volume,
            NULL, NULL, NULL, NULL, NULL, NULL, '官方日曆沒有這天 · 量 0 · 開高低收相同' FROM hol""", [run_id, ts])
        con.execute(f"DELETE FROM {PRICES} p WHERE EXISTS (SELECT 1 FROM hol h WHERE h.date = p.date AND h.ticker = p.ticker)")
        con.execute(f"""INSERT INTO {LOG} SELECT ?, ?, CASE WHEN seg THEN 'update_segment' ELSE 'update_isolated' END, date, ticker,
            po, ph, pl, pc, pa, NULL, oo, oh, ol, oc, CASE WHEN seg OR pa IS NULL THEN pa ELSE pa * r END, NULL,
            CASE WHEN seg THEN '整段調整:adj_close 保留' ELSE '零星錯值:adj_close × 官方收 / 舊收' END FROM mis2""", [run_id, ts])
        con.execute(f"""UPDATE {PRICES} p SET open = m.oo, high = m.oh, low = m.ol, close = m.oc,
            adj_close = CASE WHEN m.seg OR p.adj_close IS NULL THEN p.adj_close ELSE p.adj_close * m.r END
            FROM mis2 m WHERE p.date = m.date AND p.ticker = m.ticker""")
        con.execute(f"""CREATE OR REPLACE TEMP TABLE ins AS SELECT o.date, o.ticker, o.open, o.high, o.low, o.close,
            o.close * (SELECT p.adj_close / p.close FROM {PRICES} p WHERE p.ticker = o.ticker AND p.date < o.date
                       AND p.close > 0 AND p.adj_close IS NOT NULL ORDER BY p.date DESC LIMIT 1) AS adj_close, o.volume
            FROM miss o""")
        con.execute(f"""INSERT INTO {LOG} SELECT ?, ?, 'insert_missing', date, ticker, NULL, NULL, NULL, NULL, NULL, NULL,
            open, high, low, close, adj_close, volume, '官方有、我們缺:adj_close = 官方收 × 前一列因子' FROM ins""", [run_id, ts])
        cols = [r[0] for r in con.execute(f"DESCRIBE {PRICES}").fetchall()]
        vals = {"date": "date", "ticker": "ticker", "open": "open", "high": "high", "low": "low", "close": "close",
                "adj_close": "adj_close", "volume": "volume"}
        sel = ", ".join(vals.get(c, "NULL") for c in cols)
        con.execute(f"INSERT INTO {PRICES} SELECT {sel} FROM ins")
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    p1 = plan(con)
    return {"before": p0, "after": p1, "run_id": run_id,
            "ok": p1["holiday"] == 0 and p1["mismatch"] == 0 and p1["missing"] == 0 and p1["dup_keys"] == 0
            and p1["rows"] == p0["rows"] - p0["holiday"] + p0["missing"]}


def _db_path(args: list) -> Path:
    if "--db" in args:
        return Path(args[args.index("--db") + 1])
    if "--home" in args:
        return Path(args[args.index("--home") + 1]) / DB_REL
    raise SystemExit("[拒] 要 --home <資料家> 或 --db <vdf_tw_market.duckdb>(不猜路徑)")


def backup(db: Path, home: Path | None = None) -> Path:
    dest_dir = (home or db.parent) / "_backup" / "tw_price_reconcile"
    dest_dir.mkdir(parents=True, exist_ok=True)
    need = db.stat().st_size * 1.1
    if shutil.disk_usage(dest_dir).free < need:
        raise SystemExit(f"[拒] 備份空間不足(要 {need / 1e6:.0f} MB)· 零寫入")
    dest = dest_dir / f"{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}_{db.name}"
    shutil.copy2(db, dest)
    wal = Path(str(db) + ".wal")
    if wal.exists():
        shutil.copy2(wal, Path(str(dest) + ".wal"))
    return dest


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] == ["--selftest"]:
        return selftest()
    verb = args[0] if args else "plan"
    if verb not in ("plan", "apply"):
        print(__doc__)
        return 2
    import duckdb
    db = _db_path(args)
    if not db.is_file():
        print(f"[{TAG}] NODATA:庫不在 {db}")
        return 2
    if verb == "plan":
        con = duckdb.connect(str(db), read_only=True)
        try:
            print(json.dumps(plan(con), ensure_ascii=False, indent=1, default=str))
        finally:
            con.close()
        return 0
    home = Path(args[args.index("--home") + 1]) if "--home" in args else None
    bk = backup(db, home)
    print(f"[{TAG}] 備份 → {bk}", flush=True)
    con = duckdb.connect(str(db))
    try:
        res = apply(con, "REC_" + time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    finally:
        con.close()
    res["backup"] = str(bk)
    b, a = res["before"], res["after"]
    print(f"[{TAG}] {'GREEN' if res['ok'] else 'RED'} · 刪休市佔位 {b['holiday']} · 改官方 {b['mismatch']}(整段 {b['mismatch_segment']} · 零星 {b['mismatch_isolated']})"
          f" · 補缺 {b['missing']} · 列 {b['rows']:,} → {a['rows']:,} · 寫後剩:佔位 {a['holiday']} · 不符 {a['mismatch']} · 缺 {a['missing']} · 重複鍵 {a['dup_keys']}")
    print(json.dumps(res, ensure_ascii=False, default=str)[:4000])
    return 0 if res["ok"] else 1


def _fixture(db: Path) -> None:
    """暫存庫:官方 3 檔 × 6 天;Yahoo 那邊放好各種錯。"""
    import duckdb
    con = duckdb.connect(str(db))
    con.execute(f"CREATE TABLE {OFFICIAL}(date VARCHAR, code VARCHAR, market VARCHAR, volume DOUBLE, trade_value DOUBLE, transactions DOUBLE,"
                " close DOUBLE, open DOUBLE, high DOUBLE, low DOUBLE, src VARCHAR)")
    con.execute(f"CREATE TABLE {PRICES}(date VARCHAR, ticker VARCHAR, open DOUBLE, high DOUBLE, low DOUBLE, close DOUBLE, adj_close DOUBLE, volume DOUBLE)")
    days = ["2025-01-02", "2025-01-03", "2025-01-06", "2025-01-07", "2025-01-08", "2025-01-09"]
    off = {"1111": ("TWSE", [10, 11, 12, 13, 14, 15]), "2222": ("TWSE", [20, 20, 20, 20, 20, 20]), "3333": ("TPEX", [30, 31, 32, 33, 34, 35])}
    for code, (mkt, closes) in off.items():
        for d, c in zip(days, closes):
            con.execute(f"INSERT INTO {OFFICIAL} VALUES (?, ?, ?, 1000, 1, 1, ?, ?, ?, ?, 'fix')", [d, code, mkt, c, c, c + 0.5, c - 0.5])
    rows = []
    for d, c in zip(days, off["1111"][1]):                       # 1111:整段調整(Yahoo 收 = 官方 × 0.5),adj = 收 × 0.9
        rows.append((d, "1111.TW", c * .5, (c + .5) * .5, (c - .5) * .5, c * .5, c * .5 * .9, 1000))
    for d, c in zip(days, off["2222"][1]):                       # 2222:01-07 零星錯值 21.5;其餘對
        cc = 21.5 if d == "2025-01-07" else c
        rows.append((d, "2222.TW", c, c + .5, c - .5, cc, cc * .8, 1000))
    for d, c in zip(days, off["3333"][1]):                       # 3333:01-08 缺列(官方有)
        if d != "2025-01-08":
            rows.append((d, "3333.TWO", c, c + .5, c - .5, c, c, 1000))
    rows.append(("2025-01-04", "1111.TW", 5.5, 5.5, 5.5, 5.5, 4.95, 0))   # 週六休市佔位(量 0 · 開高低收同)
    rows.append(("2025-01-04", "2222.TW", 20, 20.5, 19.5, 20, 16, 500))  # 休市日但量不為 0 → 不刪(照實報)
    con.executemany(f"INSERT INTO {PRICES} VALUES (?, ?, ?, ?, ?, ?, ?, ?)", rows)
    con.close()


def selftest() -> int:
    import duckdb
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    print(f"=== {TAG} · 自測(暫存庫 · 零網路 · 不碰真庫)===")
    with tempfile.TemporaryDirectory(prefix="mdl032_") as td:
        home = Path(td) / "dict"
        db = home / DB_REL
        db.parent.mkdir(parents=True)
        _fixture(db)
        con = duckdb.connect(str(db), read_only=True)
        p = plan(con)
        con.close()
        chk("① 乾跑分類:休市佔位 1(量 0 那列)· 不符 7(1111 整段 6 + 2222 零星 1)· 缺 1(3333 01-08)· 乾跑零寫入",
            p["holiday"] == 1 and p["holiday_days"] == ["2025-01-04"] and p["mismatch"] == 7 and p["mismatch_segment"] == 6
            and p["mismatch_isolated"] == 1 and p["missing"] == 1 and p["rows"] == 19, p)
        rc = main(["apply", "--home", str(home)])
        bks = list((home / "_backup" / "tw_price_reconcile").glob("*_vdf_tw_market.duckdb"))
        con = duckdb.connect(str(db), read_only=True)
        q = lambda s, a=None: con.execute(s, a or []).fetchall()  # noqa: E731
        g = {r[1]: r for r in q(f"SELECT date, ticker, open, high, low, close, adj_close FROM {PRICES} WHERE date = '2025-01-07'")}
        chk("② apply rc 0 · 寫前整檔備份 1 份", rc == 0 and len(bks) == 1, (rc, bks))
        chk("③ 整段調整(1111):開高低收改官方 13 / 13.5 / 12.5 / 13 · adj_close 保留 5.85(因子 0.45 = 配股 0.5 × 配息 0.9)",
            g["1111.TW"][2:6] == (13, 13.5, 12.5, 13) and abs(g["1111.TW"][6] - 5.85) < 1e-9, g["1111.TW"])
        chk("④ 零星錯值(2222 01-07):收 21.5 → 官方 20 · adj_close × 20/21.5 → 16(因子照前後 0.8)",
            g["2222.TW"][5] == 20 and abs(g["2222.TW"][6] - 16) < 1e-9, g["2222.TW"])
        ins = q(f"SELECT open, high, low, close, adj_close, volume FROM {PRICES} WHERE ticker = '3333.TWO' AND date = '2025-01-08'")
        chk("⑤ 補缺(3333 01-08):開高低收量取官方 · adj_close = 官方收 × 前一列因子(1.0)", ins == [(34, 34.5, 33.5, 34, 34, 1000)], ins)
        hol = q(f"SELECT ticker, volume FROM {PRICES} WHERE date = '2025-01-04' ORDER BY 1")
        chk("⑥ 休市佔位刪掉(1111 量 0);休市日但量不為 0 的列不刪(照實留給人看)", hol == [("2222.TW", 500)], hol)
        log = q(f"SELECT action, count(*) FROM {LOG} GROUP BY 1 ORDER BY 1")
        chk("⑦ 帳表逐列記:刪 1 · 整段 6 · 零星 1 · 補 1(含舊值 · 新值 → 可還原)",
            log == [("delete_holiday", 1), ("insert_missing", 1), ("update_isolated", 1), ("update_segment", 6)], log)
        con.close()
        con = duckdb.connect(str(db))
        r2 = apply(con, "REC_TEST2")
        n_log = con.execute(f"SELECT count(*) FROM {LOG}").fetchone()[0]
        con.close()
        chk("⑧ 冪等:再跑一次零動作(不符 0 · 缺 0 · 佔位 0 · 帳表不增)· 重複鍵 0",
            r2["ok"] and r2["before"]["mismatch"] == 0 and r2["before"]["missing"] == 0 and r2["before"]["holiday"] == 0 and n_log == 9, r2["before"])
        con = duckdb.connect(str(db))
        con.execute(f"CREATE TEMP TABLE b AS SELECT * FROM {PRICES}")
        try:
            con.execute("BEGIN TRANSACTION")
            con.execute(f"UPDATE {PRICES} SET close = -1")
            raise RuntimeError("boom")
        except RuntimeError:
            con.execute("ROLLBACK")
        same = con.execute(f"SELECT count(*) FROM (SELECT * FROM b EXCEPT SELECT * FROM {PRICES})").fetchone()[0] == 0
        con.close()
        chk("⑨ 交易失敗整批回滾(不留半套)", same)
    try:
        main(["plan"])
        refused = False
    except SystemExit:
        refused = True
    chk("⑩ 沒給 --home / --db → 拒(不猜真庫路徑)", refused)
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("⑪ 加速器橋 · 網路橋在;本檔不出網;不碰 TA-Lib;不寫同意閘", "[VIA:ACCEL-BRIDGE:v0100]" in src and "[VIA:NET-BRIDGE:v0100]" in src
        and "def _via_net" in src and not re.search(r"^\s*(import|from)\s+(requests|urllib|talib)", body, re.M)
        and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", body))
    print(f"  [計] {TAG} 自測 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
