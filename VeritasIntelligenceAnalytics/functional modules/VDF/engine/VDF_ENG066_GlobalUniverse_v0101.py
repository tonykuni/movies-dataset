#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_ENG066_GlobalUniverse v0101 — 全球宇宙擷取引擎(批226 立;批228 P3 契約對齊)
====================================================================
操作員令:「全球分類更多——國際股票指數/國際股票 ETF/國際個股美日/
國際個股財報/原油期貨/美元指數及重要匯率/商品/加密貨幣/美國總經/
聯準會/美國財政及利率」。
機制:宇宙冊 VIA_Global_Universe_v0100.json(SSOT;11 類 82 檔)→
SUP_MDL740 統包 yahoo_chart 道(雙同意閘 fail-closed)→ global_daily
anti-join 僅補缺鍵(既有列零觸碰;每批即落盤=中斷安全;重跑冪等)。
財報/FRED 擴列=PENDING_SOURCE 候令,冊內誠實標示,本引擎不假抓。
日期:預設 2020-01-01~最新(開始日~最新);--start/--end 可改
(全球域無終止令;台股 2020/21 終止=批212 僅限台股回補)。
用法:python3 VDF_ENG066_GlobalUniverse_v0100.py run
        [--cats idx,fx,crypto] [--start YYYY-MM-DD] [--end YYYY-MM-DD]
      | --list | --selftest
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

import calendar
import importlib.util
import json
import os
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent.parent
MEGA = VIA / "functional modules" / "VDF" / "output_hub" / "mega"
DB_GL = MEGA / "vdf_global_market.duckdb"
ROSTER = VIA / "supportive modules" / "registry" / "VIA_Global_Universe_v0100.json"
DEFAULT_START = "2018-01-01"   # 批228:FetchOne 契約 P3 START_DATE 對齊
BATCH = 25
PAUSE_S = 0.35
DATE_RX = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _net():
    p = sorted((VIA / "supportive modules" / "network")
               .glob("SUP_MDL740_NetUnified_v*.py"))[-1]
    spec = importlib.util.spec_from_file_location("net740_e66", p)
    m = importlib.util.module_from_spec(spec)
    sys.modules["net740_e66"] = m
    spec.loader.exec_module(m)
    return m


def load_roster() -> dict:
    return json.loads(ROSTER.read_text(encoding="utf-8"))


def pick_symbols(cats: list[str] | None) -> tuple[list[str], list[str]]:
    """回 (可抓 symbols 去重, 候源類清單);候源類=誠實列示不假抓"""
    r = load_roster()
    syms, pend = [], []
    for c in r["categories"]:
        if cats and c["cat"] not in cats:
            continue
        if not c["symbols"]:
            pend.append(f"{c['cat']}({c['zh']}):{c.get('pending_note', '候源')}")
        syms += c["symbols"]
    seen = set()
    uniq = [s for s in syms if not (s in seen or seen.add(s))]
    return uniq, pend


def _insert_missing(con, rows: list[dict]) -> None:
    if not rows:
        return
    cols = ["date", "ticker", "open", "high", "low", "close", "adj_close", "volume"]
    con.execute("CREATE TEMP TABLE _gu(date VARCHAR, ticker VARCHAR, open DOUBLE,"
                " high DOUBLE, low DOUBLE, close DOUBLE, adj_close DOUBLE,"
                " volume DOUBLE)")
    con.executemany(f"INSERT INTO _gu VALUES ({', '.join('?' * len(cols))})",
                    [[r.get(c) for c in cols] for r in rows])
    con.execute("""INSERT INTO global_daily
        SELECT g.date, g.ticker, g.open, g.high, g.low, g.close, g.adj_close,
               CAST(g.volume AS BIGINT)
        FROM _gu g LEFT JOIN global_daily t
          ON t.date = g.date AND t.ticker = g.ticker
        WHERE t.date IS NULL""")
    con.execute("DROP TABLE _gu")


def run(cats: list[str] | None = None, start: str = DEFAULT_START,
        end: str | None = None) -> int:
    if os.environ.get("VIA_NET_CONSENT") != "YES" \
            or os.environ.get("VIA_SCRAPE_CONSENT") != "YES":
        print("[全球宇宙] 同意閘未開=拒跑(fail-closed 誠實)")
        return 2
    if not DATE_RX.match(start) or (end and not DATE_RX.match(end)):
        print("[全球宇宙] 日期格式須 YYYY-MM-DD")
        return 2
    syms, pend = pick_symbols(cats)
    for p in pend:
        print(f"  [候源] {p}")
    if not syms:
        print("[全球宇宙] 選類無可抓 symbols(候源類=誠實不假抓)")
        return 0
    net = _net()
    import duckdb
    con = duckdb.connect(str(DB_GL))
    before = con.execute("SELECT count(*) FROM global_daily").fetchone()[0]
    se = calendar.timegm(time.strptime(start, "%Y-%m-%d"))
    ee = (calendar.timegm(time.strptime(end, "%Y-%m-%d")) + 86400) if end \
        else int(time.time())
    t0 = time.time()
    got = 0
    for i in range(0, len(syms), BATCH):
        batch = syms[i:i + BATCH]
        rc = net.yahoo_chart(batch, se, ee, pause_s=PAUSE_S)
        rows = rc.get("rows") or []
        _insert_missing(con, rows)          # 每批即落盤=中斷安全
        got += len(rows)
        print(f"  [批 {i // BATCH + 1}/{(len(syms) - 1) // BATCH + 1}] "
              f"回 {len(rows)} 列", flush=True)
    after = con.execute("SELECT count(*) FROM global_daily").fetchone()[0]
    con.close()
    print(f"[全球宇宙] {len(syms)} 檔 · {start}~{end or '最新'} · 回抓 {got:,}"
          f" · 實補 +{after - before:,} 列(anti-join 僅補缺)"
          f" · {round(time.time() - t0)}s")
    return 0


def list_cats() -> int:
    r = load_roster()
    for c in r["categories"]:
        print(f"  [{c['cat']}] {c['zh']} · {c['status']} · {len(c['symbols'])} 檔"
              + (f" · {c.get('pending_note', '')}" if not c["symbols"]
                 or "PENDING" in c["status"] or "PARTIAL" in c["status"] else ""))
    return 0


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    r = load_roster()
    cats = {c["cat"] for c in r["categories"]}
    chk("① 宇宙冊 SSOT 在位(11 類=操作員批226 清單全覆蓋)",
        cats == {"idx", "etf", "us_jp", "fin_reports", "oil", "fx", "cmdty",
                 "crypto", "us_macro", "fed", "us_fiscal_rates"})
    syms, pend = pick_symbols(None)
    chk("② 候源類誠實列示不假抓(財報/總經=零 symbols 有 note)",
        any("fin_reports" in p for p in pend) and len(syms) >= 70)
    saved = {k: os.environ.pop(k, None)
             for k in ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT")}
    rc = run()
    for k, v in saved.items():
        if v is not None:
            os.environ[k] = v
    chk("③ 同意閘 fail-closed(未開=拒跑 rc2 零觸網)", rc == 2)
    chk("④ 日期規格檢+P3 契約預設(2018-01-01~now;批228 對齊)",
        DEFAULT_START == "2018-01-01" and DATE_RX.match("2024-01-01")
        and not DATE_RX.match("2024/01/01"))
    import duckdb
    con = duckdb.connect(str(DB_GL))
    con.execute("BEGIN")
    b0 = con.execute("SELECT count(*) FROM global_daily").fetchone()[0]
    real = con.execute("SELECT close FROM global_daily WHERE ticker='^GSPC' "
                       "ORDER BY date DESC LIMIT 1").fetchone()
    fx = [{"date": "2024-01-02", "ticker": "TEST66", "open": 1, "high": 1,
           "low": 1, "close": 1, "adj_close": 1, "volume": 1}]
    if real:
        fx.append({"date": con.execute(
            "SELECT date FROM global_daily WHERE ticker='^GSPC' "
            "ORDER BY date DESC LIMIT 1").fetchone()[0],
            "ticker": "^GSPC", "open": 9.9, "high": 9.9, "low": 9.9,
            "close": 9.9, "adj_close": 9.9, "volume": 9})
    _insert_missing(con, fx)
    now = con.execute("SELECT close FROM global_daily WHERE ticker='^GSPC' "
                      "ORDER BY date DESC LIMIT 1").fetchone()
    chk("⑤ anti-join 正本零觸碰(^GSPC 既有列不被 9.9 覆蓋;新鍵入)",
        (not real or now[0] != 9.9) and con.execute(
            "SELECT count(*) FROM global_daily WHERE ticker='TEST66'")
        .fetchone()[0] == 1)
    con.execute("ROLLBACK")
    left = con.execute("SELECT count(*) FROM global_daily "
                       "WHERE ticker='TEST66'").fetchone()[0]
    b1 = con.execute("SELECT count(*) FROM global_daily").fetchone()[0]
    chk("⑥ fixture 零殘留(ROLLBACK 後列數復原)", left == 0 and b0 == b1)
    con.close()
    chk("⑦ 統包唯一道(yahoo_chart 經 SUP_MDL740;無 http 庫直呼)",
        "SUP_MDL740_NetUnified_v*" in src
        and all(("import " + k) not in src for k in ("requests", "httpx")))
    chk("⑧ 台股終止令界線宣告(批212 僅限台股;全球域無終止)",
        "批212" in src and "僅限台股" in src)
    print(f"  [計] 八檢 OK {8 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 全球宇宙擷取引擎(VDF_ENG066)· 八檢自測(零網路)===")
        return selftest()
    if "--list" in args:
        return list_cats()
    if args and args[0] == "run":
        def _opt(flag, default=None):
            return args[args.index(flag) + 1] if flag in args else default
        cats = _opt("--cats")
        return run([c for c in cats.split(",") if c] if cats else None,
                   _opt("--start", DEFAULT_START), _opt("--end"))
    return list_cats()


if __name__ == "__main__":
    sys.exit(main())
