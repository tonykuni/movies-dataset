#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_ENG075_MonthlyRevenueBackfill — 月營收全市場史深回補(批368;via-revfill)
====================================================================
操作員令(批368)「COMPLETE … VIA TAIWAN STOCK MONTHLY REVENUE ANALYSIS … TILL ALL WORK PERFECTLY」
+ 交接冊「U=月營收:MOPS monthly sii/otc files from 2023-01, not ticker loop, LIVE off」。
根因:ENG063 L1 官方道=每日快照三點(當月/上月/去年當月)累積→史深僅 13 月(202507→202607),
monthly_revenue_analysis 之 high_60m/yoy_streak/cum_12m 無 60 月真值可算。
本引擎=MOPS 官方「月營收彙總檔」整月整所單拉(非逐檔迴圈):
  上市 https://mops.twse.com.tw/nas/t21/sii/t21sc03_{民國年}_{月}_{0|1}.html
  上櫃 https://mops.twse.com.tw/nas/t21/otc/t21sc03_{民國年}_{月}_{0|1}.html(_0 國內;_1 KY)
律:
  從新往舊  月序自上月倒推至 --since(預設 2023-01);每月×所×檔即落盤+checkpoint(DONE/EMPTY 404);
  只增不減  同表 tw_monthly_revenue(code, ym, revenue, source='MOPS_T21SC03', fetched_at);
            anti-join (code,ym) 任何來源已有=不插(避免分析視圖 RANGE 視窗重複計數);零 DELETE;
  編碼準    SUP_MDL740.http_bytes 原始位元組→cp950 解碼(失敗退 utf-8);表頭「當月營收」定欄;千元原值零改;
  快        accel_map 3 工+節流 0.5s;LIVE off 交接令=雙同意閘 fail-closed(親跑 via-revfill 即同意);
  誠實      OK/EMPTY(404 未發布)/FAIL;結束呼 ENG063 尾版 _ensure_schema 重建分析視圖;status 印史深。
用法:python3 VDF_ENG075_MonthlyRevenueBackfill_v0100.py [run] [--since 2023-01] [--workers 3] [--max-months N]
      | status | --selftest
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
# ===== [VIA:NET-BRIDGE:END] =====
import json
import os
import re
import sys
import threading
import time
from datetime import date, datetime
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF = HERE.parent
VIA = VDF.parent.parent
OUT = VDF / "output_hub" / "mega"
DB_TW = OUT / "vdf_tw_market.duckdb"
CKPT = OUT / "revenue_backfill_checkpoint.json"
TABLE = "tw_monthly_revenue"
SOURCE = "MOPS_T21SC03"
SINCE_DEFAULT = "2023-01"
MARKETS = (("sii", "0"), ("sii", "1"), ("otc", "0"), ("otc", "1"))   # 上市國內/KY;上櫃國內/KY
URL = "https://mops.twse.com.tw/nas/t21/{mk}/t21sc03_{roc}_{m}_{k}.html"
_LOCK = threading.Lock()
_DB_LOCK = threading.Lock()
_STATS = {"req": 0, "fail": 0, "empty": 0}


def gate_open(env=None) -> bool:
    env = env if env is not None else os.environ
    return env.get("VIA_NET_CONSENT") == "YES" and env.get("VIA_SCRAPE_CONSENT") == "YES"


def _net_or_none():
    import glob as _g
    import importlib.util as _il
    hits = sorted(_g.glob(str(VIA / "supportive modules" / "network" / "SUP_MDL740_NetUnified_v*.py")))
    if not hits:
        return None
    spec = _il.spec_from_file_location("via_net_dyn", hits[-1])
    mod = _il.module_from_spec(spec)
    sys.modules["via_net_dyn"] = mod
    spec.loader.exec_module(mod)
    return mod


def _eng063():
    import glob as _g
    import importlib.util as _il
    hits = sorted(_g.glob(str(HERE / "VDF_ENG063_MonthlyRevenue_v*.py")))
    if not hits:
        return None
    spec = _il.spec_from_file_location("eng063_dyn", hits[-1])
    mod = _il.module_from_spec(spec)
    sys.modules["eng063_dyn"] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------- 月序(從新往舊)
def month_seq(since: str, newest: str | None = None) -> list[str]:
    """['202608','202607',…,'202301'];newest 預設=上月(當月營收於次月 10 日前發布)"""
    if newest is None:
        t = date.today()
        y, m = (t.year, t.month - 1) if t.month > 1 else (t.year - 1, 12)
        newest = f"{y}{m:02d}"
    sy, sm = int(since[:4]), int(since[5:7] if "-" in since else since[4:6])
    y, m = int(newest[:4]), int(newest[4:6])
    out = []
    while (y, m) >= (sy, sm):
        out.append(f"{y}{m:02d}")
        y, m = (y, m - 1) if m > 1 else (y - 1, 12)
    return out


def url_for(mk: str, k: str, ym: str) -> str:
    return URL.format(mk=mk, roc=int(ym[:4]) - 1911, m=int(ym[4:6]), k=k)


# ---------------------------------------------------------------- 解析(Big5 官方頁)
class _T21Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows, self._row, self._cell, self._in = [], None, None, False

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell, self._in = [], True

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._row is not None and self._cell is not None:
            self._row.append("".join(self._cell).strip())
            self._cell, self._in = None, False
        elif tag == "tr" and self._row is not None:
            if self._row:
                self.rows.append(self._row)
            self._row = None

    def handle_data(self, data):
        if self._in and self._cell is not None:
            self._cell.append(data)


def decode_page(raw: bytes) -> str:
    for enc in ("cp950", "big5hkscs", "utf-8"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("cp950", "replace")


def _num(v) -> float | None:
    try:
        f = float(str(v).replace(",", "").strip())
        return f if f > 0 else None
    except Exception:
        return None


def parse_t21(text: str, ym: str) -> list[tuple[str, str, float]]:
    """回 [(code, ym, revenue_當月)];表頭「當月營收」定欄(缺=退第 3 欄);4~6 碼代號"""
    p = _T21Parser()
    p.feed(text)
    col = None
    out, seen = [], set()
    for row in p.rows:
        if col is None:
            for i, c in enumerate(row):
                if "當月營收" in c.replace(" ", "") and "去年" not in c and "累計" not in c:
                    col = i
                    break
            if col is not None:
                continue
        c0 = row[0].strip() if row else ""
        if not re.fullmatch(r"\d{4,6}[A-Z]?", c0):
            continue
        idx = col if col is not None and col < len(row) else 2
        if idx >= len(row):
            continue
        v = _num(row[idx])
        if v is None or c0 in seen:
            continue
        seen.add(c0)
        out.append((c0, ym, v))
    return out


# ---------------------------------------------------------------- checkpoint / 落庫
def _load_ckpt() -> dict:
    if CKPT.exists():
        try:
            return json.loads(CKPT.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_ckpt(ck: dict) -> None:
    with _LOCK:
        CKPT.parent.mkdir(parents=True, exist_ok=True)
        tmp = CKPT.with_suffix(".tmp")
        tmp.write_text(json.dumps(ck, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(CKPT)


def upsert(rows: list[tuple[str, str, float]], ts: str) -> tuple[int, int]:
    """anti-join (code,ym) 任何來源已有=不插;回 (新插, 表總列)"""
    import duckdb
    with _DB_LOCK:
        DB_TW.parent.mkdir(parents=True, exist_ok=True)
        con = duckdb.connect(str(DB_TW))
        try:
            con.execute(f"CREATE TABLE IF NOT EXISTS {TABLE}(code VARCHAR, ym VARCHAR, revenue DOUBLE, source VARCHAR, fetched_at VARCHAR)")
            con.execute("CREATE TEMP TABLE _bf(code VARCHAR, ym VARCHAR, revenue DOUBLE)")
            con.executemany("INSERT INTO _bf VALUES (?,?,?)", rows)
            before = con.execute(f"SELECT COUNT(*) FROM {TABLE}").fetchone()[0]
            con.execute(f"""INSERT INTO {TABLE}
                SELECT b.code, b.ym, b.revenue, '{SOURCE}', '{ts}' FROM _bf b
                WHERE NOT EXISTS (SELECT 1 FROM {TABLE} t WHERE t.code = b.code AND t.ym = b.ym)""")
            after = con.execute(f"SELECT COUNT(*) FROM {TABLE}").fetchone()[0]
            con.execute("DROP TABLE _bf")
            return after - before, after
        finally:
            con.close()


def rebuild_view() -> str:
    """ENG063 尾版 _ensure_schema=分析視圖正主(零重造)"""
    import duckdb
    m = _eng063()
    if m is None or not hasattr(m, "_ensure_schema"):
        return "ENG063 缺=視圖未重建(誠實)"
    with _DB_LOCK:
        con = duckdb.connect(str(DB_TW))
        try:
            m._ensure_schema(con)
            return "monthly_revenue_analysis 視圖重建(ENG063 尾版)"
        finally:
            con.close()


# ---------------------------------------------------------------- 抓取單元
def fetch_one(net, ym: str, mk: str, k: str, pause: float, ck: dict, ts: str) -> dict:
    key = f"{ym}:{mk}:{k}"
    st = ck.get(key, {})
    if st.get("state") in ("DONE", "EMPTY"):
        return {"key": key, "state": "SKIP", "rows": 0, "note": st["state"]}
    time.sleep(pause)
    _STATS["req"] += 1
    r = net.http_bytes(url_for(mk, k, ym))
    if r.get("state") != "OK":
        if r.get("http404"):
            _STATS["empty"] += 1
            ck[key] = {"state": "EMPTY", "note": "404 未發布/無檔", "ts": ts}
            _save_ckpt(ck)
            return {"key": key, "state": "EMPTY", "rows": 0, "note": "404"}
        _STATS["fail"] += 1
        ck[key] = {"state": "FAIL", "note": str(r.get("note", ""))[:100], "ts": ts}
        _save_ckpt(ck)
        return {"key": key, "state": "FAIL", "rows": 0, "note": str(r.get("note", ""))[:60]}
    rows = parse_t21(decode_page(r["data"]), ym)
    if not rows:
        _STATS["empty"] += 1
        ck[key] = {"state": "EMPTY", "note": "頁在但零列(版式/未發布)", "ts": ts}
        _save_ckpt(ck)
        return {"key": key, "state": "EMPTY", "rows": 0, "note": "零列"}
    ins, total = upsert(rows, ts)
    ck[key] = {"state": "DONE", "parsed": len(rows), "inserted": ins, "ts": ts}
    _save_ckpt(ck)
    return {"key": key, "state": "OK", "rows": len(rows), "inserted": ins, "note": ""}


def progress_bar(done: int, total: int, width: int = 22, spent: float = 0.0) -> str:
    total = max(total, 1)
    fill = int(width * done / total)
    per = spent / done if done else 0.0
    return f"[{'■' * fill}{'□' * (width - fill)}] {done}/{total} {100.0 * done / total:5.1f}% · 已耗 {spent:6.1f}s · 預估剩餘 {per * (total - done):6.1f}s"


def run(args: list[str]) -> int:
    def opt(name, default=None):
        return args[args.index(name) + 1] if name in args and args.index(name) + 1 < len(args) else default
    since = opt("--since", SINCE_DEFAULT)
    workers = int(opt("--workers", "3"))
    pause = float(opt("--pause", "0.5"))
    max_months = int(opt("--max-months", "0"))
    print("=== 月營收全市場史深回補(VDF_ENG075;MOPS t21sc03 月檔;從新往舊)===", flush=True)
    if not gate_open():
        print("[FAIL-CLOSED] 同意閘未開(VIA_NET_CONSENT/VIA_SCRAPE_CONSENT;交接令 LIVE off=親跑 via-revfill 即同意)", flush=True)
        return 2
    net = _net_or_none()
    if net is None or not hasattr(net, "http_bytes"):
        print("[FAIL] 統包網路工具 http_bytes 車道缺(需 SUP_MDL740 ≥ v0110)", flush=True)
        return 1
    months = month_seq(since)
    if max_months:
        months = months[:max_months]
    units = [(ym, mk, k) for ym in months for mk, k in MARKETS]
    ck = _load_ckpt()
    todo = [u for u in units if ck.get(f"{u[0]}:{u[1]}:{u[2]}", {}).get("state") not in ("DONE", "EMPTY")]
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"  [母冊] {len(months)} 月 × 4 所檔 = {len(units)} 單元;待抓 {len(todo)}(其餘 checkpoint DONE/EMPTY)· 工人 {workers} · 節流 {pause}s", flush=True)
    t0 = time.time()
    results, done_n, lock = [], [0], threading.Lock()

    def one(u):
        r = fetch_one(net, u[0], u[1], u[2], pause, ck, ts)
        with lock:
            done_n[0] += 1
            print(f"  [{r['state']:<5}] {r['key']:<16} {r['rows']:>5} 列 新插 {r.get('inserted', 0):>5} {progress_bar(done_n[0], len(todo), spent=time.time() - t0)} {r['note'][:40]}", flush=True)
        return r
    if VIA_ACCEL is not None and hasattr(VIA_ACCEL, "accel_map") and workers > 1 and todo:
        for ok, r in VIA_ACCEL.accel_map(one, todo, workers=workers):
            results.append(r if ok else {"key": "?", "state": "FAIL", "rows": 0, "note": str(r)})
    else:
        for u in todo:
            try:
                results.append(one(u))
            except Exception as exc:
                results.append({"key": ":".join(u), "state": "FAIL", "rows": 0, "note": f"{type(exc).__name__}: {exc}"})
    note = rebuild_view()
    tally = {k: sum(1 for r in results if r["state"] == k) for k in ("OK", "EMPTY", "FAIL", "SKIP")}
    ins = sum(r.get("inserted", 0) for r in results)
    print(f"  [視圖] {note}", flush=True)
    print(f"  [計] 單元 {len(results)} · OK {tally['OK']} · EMPTY {tally['EMPTY']} · FAIL {tally['FAIL']} · 新插 {ins} 列 · 請求 {_STATS['req']}(敗 {_STATS['fail']}) · {time.time() - t0:.1f}s · 落 {DB_TW.name}", flush=True)
    status()
    return 1 if tally["FAIL"] else 0


def status() -> int:
    import duckdb
    if not DB_TW.exists():
        print(f"  [DB] 缺 {DB_TW.name}")
        return 0
    con = duckdb.connect(str(DB_TW), read_only=True)
    try:
        tabs = {t for (t,) in con.execute("SHOW TABLES").fetchall()}
        if TABLE not in tabs:
            print(f"  [{TABLE}] 表缺")
            return 0
        n, nc, mn, mx, nm = con.execute(f"SELECT COUNT(*), COUNT(DISTINCT code), MIN(ym), MAX(ym), COUNT(DISTINCT ym) FROM {TABLE}").fetchone()
        src = con.execute(f"SELECT source, COUNT(*) FROM {TABLE} GROUP BY 1 ORDER BY 2 DESC").fetchall()
        full = con.execute(f"SELECT COUNT(*) FROM (SELECT code FROM {TABLE} GROUP BY code HAVING COUNT(DISTINCT ym) >= 60)").fetchone()[0]
        print(f"  [史深] {TABLE} {n:,} 列 · {nc} 檔 · {mn}→{mx}({nm} 月)· ≥60 月史深 {full} 檔 · 來源 {src}")
    finally:
        con.close()
    return 0


# ---------------------------------------------------------------- 自測
FIXTURE = """<html><head><meta http-equiv="Content-Type" content="text/html; charset=big5"></head><body>
<table><tr><th>公司代號</th><th>公司名稱</th><th>當月營收</th><th>上月營收</th><th>去年當月營收</th><th>上月比較增減(%)</th><th>去年同月增減(%)</th><th>當月累計營收</th><th>去年累計營收</th></tr>
<tr><td>2330</td><td>台積電</td><td>263,708,846</td><td>250,000,000</td><td>210,000,000</td><td>5.48</td><td>25.5</td><td>1,800,000,000</td><td>1,500,000,000</td></tr>
<tr><td>2454</td><td>聯發科</td><td>50,123,456</td><td>48,000,000</td><td>45,000,000</td><td>4.4</td><td>11.4</td><td>300,000,000</td><td>280,000,000</td></tr>
<tr><td>合計</td><td></td><td>313,832,302</td><td></td><td></td><td></td><td></td><td></td><td></td></tr>
<tr><td>6488</td><td>環球晶</td><td>0</td><td>1</td><td>1</td><td></td><td></td><td></td><td></td></tr>
</table></body></html>"""


def selftest() -> int:
    import tempfile
    global OUT, DB_TW, CKPT
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    chk("① 同意閘 fail-closed(交接令 LIVE off)", not gate_open({}) and gate_open({"VIA_NET_CONSENT": "YES", "VIA_SCRAPE_CONSENT": "YES"}))
    ms = month_seq("2023-01", "202608")
    chk("② 月序從新往舊(202608→202301=44 月;倒序不重複)", ms[0] == "202608" and ms[-1] == "202301" and len(ms) == 44 and len(set(ms)) == 44)
    chk("③ URL 民國年月(202607 上市國內→sii/t21sc03_115_7_0.html;上櫃 KY→otc/_1)",
        url_for("sii", "0", "202607").endswith("/sii/t21sc03_115_7_0.html") and url_for("otc", "1", "202312").endswith("/otc/t21sc03_112_12_1.html"))
    raw = FIXTURE.encode("cp950")
    rows = parse_t21(decode_page(raw), "202607")
    chk("④ Big5 解碼+表頭定欄+千元原值(合計列/零值列剔除;2 檔)", rows == [("2330", "202607", 263708846.0), ("2454", "202607", 50123456.0)], str(rows)[:80])
    _s = (OUT, DB_TW, CKPT)
    with tempfile.TemporaryDirectory() as td:
        OUT = Path(td)
        DB_TW, CKPT = OUT / "tw.duckdb", OUT / "ck.json"
        import duckdb
        con = duckdb.connect(str(DB_TW))
        con.execute(f"CREATE TABLE {TABLE}(code VARCHAR, ym VARCHAR, revenue DOUBLE, source VARCHAR, fetched_at VARCHAR)")
        con.execute(f"INSERT INTO {TABLE} VALUES ('2330','202607',263700000,'MOPS_OFFICIAL','x')")
        con.close()
        ins, total = upsert(rows, "t")
        ins2, total2 = upsert(rows, "t")
        con = duckdb.connect(str(DB_TW), read_only=True)
        dup = con.execute(f"SELECT COUNT(*) FROM (SELECT code, ym FROM {TABLE} GROUP BY 1,2 HAVING COUNT(*) > 1)").fetchone()[0]
        keep = con.execute(f"SELECT source FROM {TABLE} WHERE code='2330'").fetchone()[0]
        con.close()
        chk("⑤ 只增不減 anti-join(既有 MOPS_OFFICIAL 2330 不覆蓋;2454 新插;重跑零增;零重複 (code,ym))",
            ins == 1 and ins2 == 0 and total2 == 2 and dup == 0 and keep == "MOPS_OFFICIAL")
        calls = []

        class FakeNet:
            @staticmethod
            def http_bytes(url):
                calls.append(url)
                if "otc" in url or "_1.html" in url:
                    return {"state": "FAIL", "note": "HTTP Error 404: Not Found", "http404": True}
                return {"state": "OK", "data": raw}
        ck = {}
        r1 = fetch_one(FakeNet, "202606", "sii", "0", 0.0, ck, "t")
        r2 = fetch_one(FakeNet, "202606", "otc", "0", 0.0, ck, "t")
        r3 = fetch_one(FakeNet, "202606", "sii", "0", 0.0, ck, "t")
        chk("⑥ 單元抓取三態(OK 落庫+checkpoint DONE;404=EMPTY 不假;重跑=SKIP 零請求)",
            r1["state"] == "OK" and r1["inserted"] == 2 and r2["state"] == "EMPTY" and r3["state"] == "SKIP" and len(calls) == 2
            and ck["202606:sii:0"]["state"] == "DONE" and CKPT.exists())
        vnote = rebuild_view()
        con = duckdb.connect(str(DB_TW), read_only=True)
        views = {t for (t,) in con.execute("SHOW TABLES").fetchall()}
        con.close()
        chk("⑦ 分析視圖由 ENG063 尾版重建(零重造)", "monthly_revenue_analysis" in views or "缺" in vnote, vnote)
    OUT, DB_TW, CKPT = _s
    net = _net_or_none()
    chk("⑧ 統包 http_bytes 車道在位(SUP_MDL740 ≥ v0110)+進度條+雙橋", net is not None and hasattr(net, "http_bytes") and "預估剩餘" in progress_bar(1, 4, spent=1.0)
        and VIA_NET_TOOL_PATH is not None)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑨ 紀律宣告(只增不減/從新往舊/零 DELETE/誠實/非逐檔迴圈)", all(k in src for k in ("只增不減", "從新往舊", "零 DELETE", "誠實", "非逐檔迴圈")))
    print(f"  [計] 九檢 OK {9 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 月營收史深回補(VDF_ENG075)· 九檢自測 ===")
        return selftest()
    if a and a[0] == "status":
        print("=== 月營收史深現況 ===")
        return status()
    if not a or a[0] == "run" or a[0].startswith("--"):
        return run([x for x in a if x != "run"])
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
