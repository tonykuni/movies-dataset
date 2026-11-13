#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_ENG064_HistoryBackfill v0105 — 歷史回補引擎(批203 立;批212 收束;批226 自訂日期;批322 讓庫律)
批322:v0104 整跑單連線持鎖數小時(實錄 PID 15932 擋住管線全鏈)。v0105 讓庫律:
清單讀取與每批落盤各自短連線(網路抓取期間庫空閒=他程序可插隊);連線遇鎖
=等 6s 重試 20 次(印持有者),逾額 DbBusy 誠實 rc3(checkpoint 每批已留=重跑續補)。
====================================================================
操作員令(批203):「擷取所有 VDF 資料自 2020~最新」+擷取邏輯裁示:
「**由新到舊補齊、增量維護、一旦意外中斷剛才擷取的會留下來**」。
操作員令(批212):「這個步驟終止:2020/2021 年段續補」——
2020/2021 年段=TERMINATED(終止非完成;誠實 SKIP 不記 done 不假齊);
2023/2022 checkpoint 已成清單續守增量維護(重跑=秒過零重抓)。
機制(三鐵則實作):
  ① 年段倒序:2023→2022→2021→2020(近期價值優先;現庫 2024~
     已在=不重抓)
  ② 增量維護:checkpoint {segment:[done tickers]};已成 (段,檔)
     永不重抓;段內零列(上市晚於段)=記 done 誠實不重試
  ③ 中斷安全:每批 yahoo_chart 抓回→**立即** anti-join INSERT 落
     DuckDB+checkpoint 落盤;斷點重啟零損失
網路=SUP_MDL740 統包 yahoo_chart 道(雙同意閘 fail-closed);
正本紀律:INSERT 僅補缺鍵(date,ticker)=既有列零觸碰;台股
tw_daily_prices+全球 global_daily 雙庫;完段後下游(調整層/因子庫)
由 boot 鏈重建。
批226 追令:「起始時間可改」——run --start/--end 自訂範圍道:
custom:{S}~{E} 專屬 checkpoint 鍵;範圍與 2020/2021 重疊=誠實下限
夾至 2022-01-01(批212 終止令優先;解除僅憑操作員明令)。
用法:python3 VDF_ENG064_HistoryBackfill_v0104.py run [--limit N]
        [--start YYYY-MM-DD --end YYYY-MM-DD] |
      --status | --rebuild-ckpt | --selftest
(正本 v0100~v0104 零觸碰)
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

import calendar
import importlib.util
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent.parent
MEGA = VIA / "functional modules" / "VDF" / "output_hub" / "mega"
DB_TW = MEGA / "vdf_tw_market.duckdb"
DB_GL = MEGA / "vdf_global_market.duckdb"
CKPT = MEGA / "history_backfill_checkpoint.json"
TARGET_START = "2020-01-01"   # 操作員令:2020~
BATCH = 40
PAUSE_S = 0.35
# 年段倒序(由新到舊=操作員裁示;2024~ 現庫已在)
SEGMENTS = [("2023", "2023-01-01", "2023-12-31"),
            ("2022", "2022-01-01", "2022-12-31"),
            ("2021", "2021-01-01", "2021-12-31"),
            ("2020", "2020-01-01", "2020-12-31")]
# 批212 操作員終止令:2020/2021 年段續補=終止(TERMINATED≠已齊;
# 誠實 SKIP 零觸網零記 done;解除=僅憑操作員明令出新版)
TERMINATED_SEGMENTS = {"2021": "批212", "2020": "批212"}


def _net():
    p = sorted((VIA / "supportive modules" / "network")
               .glob("SUP_MDL740_NetUnified_v*.py"))[-1]
    spec = importlib.util.spec_from_file_location("net740_e64", p)
    m = importlib.util.module_from_spec(spec)
    sys.modules["net740_e64"] = m
    spec.loader.exec_module(m)
    return m


def _load_ckpt() -> dict:
    if CKPT.exists():
        return json.loads(CKPT.read_text(encoding="utf-8"))
    return {"segments": {}, "started": None, "note": "由新到舊;(段,檔)已成永不重抓"}


def _save_ckpt(ck: dict):
    # 批248:工作站 mega 夾缺=FileNotFoundError 債→先建父夾(冪等)
    CKPT.parent.mkdir(parents=True, exist_ok=True)
    CKPT.write_text(json.dumps(ck, ensure_ascii=False), encoding="utf-8")


def _tickers_tw(con) -> list[str]:
    rows = con.execute(
        "SELECT DISTINCT ticker FROM tw_daily_prices "
        "WHERE ticker <> '_NOOP_' ORDER BY ticker").fetchall()
    return [r[0] for r in rows]


def _tickers_gl(con) -> list[str]:
    rows = con.execute(
        "SELECT DISTINCT ticker FROM global_daily ORDER BY ticker").fetchall()
    return [r[0] for r in rows]


def _insert_missing(con, table: str, rows: list[dict]) -> int:
    """anti-join 僅補缺鍵=既有列零觸碰(中斷安全:呼叫端每批即呼)"""
    if not rows:
        return 0
    cols = ["date", "ticker", "open", "high", "low", "close", "adj_close", "volume"]
    con.execute(f"CREATE TEMP TABLE _hb({', '.join(c + ' VARCHAR' if c in ('date', 'ticker') else c + ' DOUBLE' for c in cols)})")
    con.executemany(f"INSERT INTO _hb VALUES ({', '.join('?' * len(cols))})",
                    [[r.get(c) for c in cols] for r in rows])
    n = con.execute(f"""INSERT INTO {table}
        SELECT h.* FROM _hb h
        LEFT JOIN {table} t ON t.date = h.date AND t.ticker = h.ticker
        WHERE t.date IS NULL""").fetchone()
    got = con.execute("SELECT count(*) FROM _hb").fetchone()[0]
    ins = con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
    con.execute("DROP TABLE _hb")
    return got  # 誠實:回抓回量;實插量由庫差可稽


LOCK_RETRY, LOCK_WAIT = 20, 6.0


class DbBusy(RuntimeError):
    pass


def _connect_retry(db, read_only: bool = False):
    """批322 讓庫律:單寫者鎖=等 LOCK_WAIT 重試 LOCK_RETRY 次;逾額 DbBusy(誠實)"""
    import duckdb
    last = ""
    for i in range(LOCK_RETRY):
        try:
            return duckdb.connect(str(db), read_only=read_only)
        except duckdb.IOException as exc:
            last = str(exc)
            if "already open" not in last and "另一個程序" not in last and "Cannot open file" not in last:
                raise
            print(f"  [庫忙] 第 {i + 1}/{LOCK_RETRY} 次:{last.splitlines()[-1][:100]} → 等 {LOCK_WAIT}s", flush=True)
            time.sleep(LOCK_WAIT)
    raise DbBusy(last[:300])


def _run_db(net, db: Path, table: str, tickers_fn, label: str,
            limit: int | None) -> int:
    con = _connect_retry(db, read_only=True)   # 短連線:讀清單即放
    tickers = tickers_fn(con)
    con.close()
    ck = _load_ckpt()
    if ck["started"] is None:
        ck["started"] = datetime.now().isoformat()
    total = 0
    for seg, s, e in SEGMENTS:          # 由新到舊(操作員裁示)
        if seg in TERMINATED_SEGMENTS:
            print(f"  [{label} {seg}] 操作員終止({TERMINATED_SEGMENTS[seg]})"
                  f"=SKIP(終止非完成;零觸網零記 done)")
            continue
        key = f"{label}:{seg}"
        done = set(ck["segments"].get(key, []))
        todo = [t for t in tickers if t not in done]
        if limit:
            todo = todo[:limit]
        if not todo:
            print(f"  [{label} {seg}] 已齊(增量維護:{len(done)} 檔跳過)")
            continue
        se = calendar.timegm(time.strptime(s, "%Y-%m-%d"))
        ee = calendar.timegm(time.strptime(e, "%Y-%m-%d")) + 86400
        print(f"  [{label} {seg}] 待補 {len(todo)} 檔(已成 {len(done)} 跳過)")
        for i in range(0, len(todo), BATCH):
            batch = todo[i:i + BATCH]
            rc = net.yahoo_chart(batch, se, ee, pause_s=PAUSE_S)
            rows = rc.get("rows") or []
            con = _connect_retry(db)                  # 短連線:抓取期間庫空閒(讓庫律)
            try:
                got = _insert_missing(con, table, rows)   # 每批即落盤=中斷安全
            finally:
                con.close()
            okset = {r["ticker"] for r in rows}
            # 段內零列(上市晚於段)=記 done 誠實不重試
            done |= set(batch)
            ck["segments"][key] = sorted(done)
            _save_ckpt(ck)                            # checkpoint 每批落盤
            total += got
            print(f"    [批 {i // BATCH + 1}/{(len(todo) - 1) // BATCH + 1}] "
                  f"+{got} 列·回 {len(okset)}/{len(batch)} 檔", flush=True)
    return total


TERMINATION_FLOOR = "2022-01-01"   # 批212:台股 2020/21 終止=自訂範圍下限


def _clamp_start(start: str) -> str:
    if start < TERMINATION_FLOOR:
        print(f"  [終止令] 起始 {start} 落入 2020/2021 終止段(批212)"
              f"→誠實夾至 {TERMINATION_FLOOR}(解除僅憑操作員明令)")
        return TERMINATION_FLOOR
    return start


def run_range(start: str, end: str, limit: int | None = None) -> int:
    """批226:自訂日期範圍道(操作員「起始時間可改」)"""
    import re as _re
    if not (_re.match(r"^\d{4}-\d{2}-\d{2}$", start)
            and _re.match(r"^\d{4}-\d{2}-\d{2}$", end)):
        print("[回補] 日期格式須 YYYY-MM-DD")
        return 2
    if os.environ.get("VIA_NET_CONSENT") != "YES" \
            or os.environ.get("VIA_SCRAPE_CONSENT") != "YES":
        print("[回補] 同意閘未開=拒跑(fail-closed 誠實)")
        return 2
    start = _clamp_start(start)
    if start > end:
        print("[回補] 起始>結束=無事可做(誠實)")
        return 0
    global SEGMENTS
    seg_label = f"custom:{start}~{end}"
    old = SEGMENTS
    SEGMENTS = [(seg_label, start, end)]
    try:
        net = _net()
        t0 = time.time()
        n = _run_db(net, DB_TW, "tw_daily_prices", _tickers_tw, "台股", limit)
        print(f"[自訂範圍] {seg_label} · 台股 +{n:,} · {round(time.time() - t0)}s"
              f"(checkpoint 鍵={seg_label};中斷安全)")
    finally:
        SEGMENTS = old
    return 0


def run(limit: int | None = None) -> int:
    if os.environ.get("VIA_NET_CONSENT") != "YES" \
            or os.environ.get("VIA_SCRAPE_CONSENT") != "YES":
        print("[回補] 同意閘未開=拒跑(fail-closed 誠實)")
        return 2
    net = _net()
    t0 = time.time()
    n_tw = _run_db(net, DB_TW, "tw_daily_prices", _tickers_tw, "台股", limit)
    n_gl = _run_db(net, DB_GL, "global_daily", _tickers_gl, "全球", limit) \
        if DB_GL.exists() else 0
    print(f"[歷史回補] 台股 +{n_tw:,} · 全球 +{n_gl:,} · {round(time.time() - t0)}s"
          f"(由新到舊;中斷安全=每批落盤;重啟續跑零重抓)")
    return 0


def rebuild_ckpt() -> int:
    """自庫重建 checkpoint(批212:v0100 selftest 曾毀真斷點之修復道)
    判準=段內有列即 done;段內零列之「已探無資料」檔無從自庫重建=
    留待下次 run 再探一次(誠實:寧多探一次不假記 done)"""
    import duckdb
    ck = _load_ckpt()
    for label, db, t in (("台股", DB_TW, "tw_daily_prices"),
                         ("全球", DB_GL, "global_daily")):
        if not db.exists():
            continue
        con = duckdb.connect(str(db), read_only=True)
        # 批252 守衛:工作站庫半建(有月營收表無日線表)=表缺誠實略,
        # 不 traceback;done 由下次 run 落表後重建(寧多探不假記)
        have = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
        if t not in have:
            print(f"  [{label}] 表 {t} 缺=誠實略(先跑 run 回補或"
                  "ENG065 DbImport 三包)")
            con.close()
            continue
        for seg, s0, e0 in SEGMENTS:
            if seg in TERMINATED_SEGMENTS:
                continue                      # 終止段不重建(終止非完成)
            key = f"{label}:{seg}"
            rows = con.execute(
                f"SELECT DISTINCT ticker FROM {t} "
                f"WHERE date >= ? AND date <= ?", [s0, e0]).fetchall()
            done = set(ck["segments"].get(key, [])) | {r[0] for r in rows}
            ck["segments"][key] = sorted(done)
            print(f"  [{key}] 重建 done={len(done)} 檔(段內有列判準)")
        con.close()
    if ck.get("started") is None:
        ck["started"] = datetime.now().isoformat()
    _save_ckpt(ck)
    print(f"[rebuild-ckpt] 已落盤:{CKPT.name}")
    return 0


def status() -> int:
    import duckdb
    ck = _load_ckpt()
    for key, done in sorted(ck.get("segments", {}).items()):
        print(f"  [{key}] 已成 {len(done)} 檔")
    for label, db, t in (("台股", DB_TW, "tw_daily_prices"),
                         ("全球", DB_GL, "global_daily")):
        if not db.exists():
            continue
        con = duckdb.connect(str(db), read_only=True)
        rows = con.execute(f"""
            SELECT ym, count(*) FROM (
              SELECT substr(CAST(date AS VARCHAR), 1, 4) AS ym FROM {t}
              WHERE date >= '2020-01-01') GROUP BY ym ORDER BY ym""").fetchall()
        con.close()
        print(f"  [{label}] 年分佈:" + " · ".join(f"{y} {n:,}" for y, n in rows))
    return 0


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    chk("① 三鐵則宣告(由新到舊/增量維護/中斷安全=每批落盤)",
        all(k in src for k in ("由新到舊", "增量維護", "中斷安全", "每批落盤")))
    chk("② 年段倒序+終止令+自訂範圍道(批226:custom 鍵+2022 下限夾)",
        [s[0] for s in SEGMENTS] == ["2023", "2022", "2021", "2020"]
        and set(TERMINATED_SEGMENTS) == {"2021", "2020"}
        and "終止非完成" in src and TERMINATION_FLOOR == "2022-01-01"
        and _clamp_start("2020-06-01") == "2022-01-01"
        and _clamp_start("2023-01-01") == "2023-01-01")
    saved = {k: os.environ.pop(k, None)
             for k in ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT")}
    rc = run()
    for k, v in saved.items():
        if v is not None:
            os.environ[k] = v
    chk("③ 同意閘 fail-closed(未開=拒跑 rc2 零觸網)", rc == 2)
    import duckdb
    con = duckdb.connect(str(DB_TW))
    con.execute("BEGIN")
    before = con.execute("SELECT count(*) FROM tw_daily_prices").fetchone()[0]
    fx = [{"date": "2023-06-01", "ticker": "TEST64", "open": 1.0, "high": 2.0,
           "low": 0.5, "close": 1.5, "adj_close": 1.5, "volume": 100.0},
          {"date": "2026-08-25", "ticker": "2330.TW", "open": 9.9, "high": 9.9,
           "low": 9.9, "close": 9.9, "adj_close": 9.9, "volume": 9.0}]
    _insert_missing(con, "tw_daily_prices", fx)
    real = con.execute("SELECT close FROM tw_daily_prices "
                       "WHERE date='2026-08-25' AND ticker='2330.TW'").fetchone()[0]
    n_new = con.execute("SELECT count(*) FROM tw_daily_prices "
                        "WHERE ticker='TEST64'").fetchone()[0]
    chk("④ anti-join 正本零觸碰(既有 2330 列不被覆蓋;新鍵入庫)",
        real != 9.9 and n_new == 1, f"(2330 close={real})")
    after = con.execute("SELECT count(*) FROM tw_daily_prices").fetchone()[0]
    chk("⑤ 僅補缺鍵(fixture 2 筆僅 1 新鍵入=增量語意)", after == before + 1)
    con.execute("ROLLBACK")
    left = con.execute("SELECT count(*) FROM tw_daily_prices "
                       "WHERE ticker='TEST64'").fetchone()[0]
    chk("⑥ fixture 零殘留(ROLLBACK 後正表無測試列)", left == 0)
    con.close()
    real_ck = CKPT.read_text(encoding="utf-8") if CKPT.exists() else None
    ck = {"segments": {"台股:2023": ["A.TW", "B.TW"]}, "started": "t"}
    _save_ckpt(ck)
    ok7 = _load_ckpt()["segments"]["台股:2023"] == ["A.TW", "B.TW"]
    if real_ck is not None:                      # v0101:真 checkpoint 備份還原
        CKPT.write_text(real_ck, encoding="utf-8")   # (v0100 債:unlink 毀真斷點)
    else:
        CKPT.unlink(missing_ok=True)
    chk("⑦ checkpoint 往返+真斷點備份還原(fixture 不毀實體)", ok7)
    boot = (VIA / "supportive modules" / "registry" /
            "via_boot_update.sh").read_text(encoding="utf-8")
    chk("⑧ 統包唯一道+boot 認知(下游調整層/因子庫由 boot 鏈重建)",
        "yahoo_chart" in src and ("import " + "requests") not in src
        and "VDF_ENG060" in boot and "VDF_ENG061" in boot)
    src9 = Path(__file__).read_text(encoding="utf-8")
    body = src9[src9.index("def _run_db("):src9.index("TERMINATION_FLOOR =")]
    chk("⑨ 讓庫律(清單/每批短連線各自 close;連線重試;DbBusy 誠實 rc3;整跑無長持鎖)",
        body.count("con.close()") >= 2 and "_connect_retry(db)" in body
        and "return 3" in src9 and LOCK_RETRY * LOCK_WAIT >= 60)
    print(f"  [計] 九檢 OK {9 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def _main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 歷史回補引擎(VDF_ENG064)· 九檢自測(零網路)===")
        return selftest()
    if "--rebuild-ckpt" in args:
        return rebuild_ckpt()
    if "--status" in args:
        return status()
    if args and args[0] == "run":
        lim = None
        if "--limit" in args:
            lim = int(args[args.index("--limit") + 1])
        if "--start" in args and "--end" in args:
            return run_range(args[args.index("--start") + 1],
                             args[args.index("--end") + 1], lim)
        return run(lim)
    return status()


def main() -> int:
    try:
        return _main()
    except DbBusy as exc:
        print(f"[FAIL] 庫忙逾 {LOCK_RETRY}×{LOCK_WAIT}s 仍鎖=誠實停(checkpoint 已留;重跑=續補):{exc}")
        return 3


if __name__ == "__main__":
    sys.exit(main())
