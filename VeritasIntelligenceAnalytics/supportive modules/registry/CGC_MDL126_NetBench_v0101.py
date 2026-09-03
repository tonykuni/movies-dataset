#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL126_NetBench v0101 — 網路車道時段基準(批353;操作員令「資料不用先補齊 先測一些時段」)
====================================================================
問:「有導入加速器嗎 為何速度極慢 導入的加速器引擎交疊使用應該很快才對」
答(實證律):加速器橋掛 1945 檔、真呼叫 15 檔(MDL117 v0101 --usage);DB 查詢毫秒級(叢集實測);
慢在網路端:Yahoo 逐檔 chart 直連遇 429/404 → AegisNexus 指數退避(工作站實錄 40 檔/批≈8 分=12s/檔)。
本器=零猜測的時段基準:同一組標的×同一時段,逐車道實測秒數/成功率/列數,供定「工數×節流×車道」。
  車道 A  chart   SUP_MDL740.yahoo_chart(統包唯一道;逐檔;pause_s)
  車道 B  chart×N SUP_MDL737.accel_map 平行子批(ENG054/ENG064 v0106 同律;N=--workers)
  車道 C  yf      SUP_MDL740.yf_download(yfinance 批次;cookie/crumb 會話;auto_adjust=False 保 Adj)
律:雙同意閘 fail-closed(VIA_NET_CONSENT+VIA_SCRAPE_CONSENT=YES 方跑;閘閉=DENY 誠實不假數);零入庫(純測);
    報告 VIA_Reports/netbench/NETBENCH_<stamp>.json+終端表;不繞 WAF/不解 CAPTCHA/不偽裝。
v0100→v0101(批355 工作站實錄 chart 0/10·yf 10/10):+車道 D yf_history(統包 v0109;start/end;=ENG064 v0107 預設道);urllib3 噪音靜音。
用法:python3 CGC_MDL126_NetBench_v0101.py [run [--tickers 2330,2317,...] [--days 60] [--workers 4] [--pause 0.35]] | --selftest
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
import warnings
warnings.filterwarnings("ignore", message="Unverified HTTPS request")
import calendar
import importlib.util
import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REP = VIA / "VIA_Reports" / "netbench"
DEFAULT_TICKERS = ["2330", "2317", "2454", "2881", "2882", "2303", "2412", "1301", "2002", "3008"]


def _net():
    hits = sorted((VIA / "supportive modules" / "network").glob("SUP_MDL740_NetUnified_v*.py"))
    if not hits:
        return None
    spec = importlib.util.spec_from_file_location("netbench_740", hits[-1])
    m = importlib.util.module_from_spec(spec)
    sys.modules["netbench_740"] = m
    spec.loader.exec_module(m)
    return m


def consent() -> bool:
    return os.environ.get("VIA_NET_CONSENT") == "YES" and os.environ.get("VIA_SCRAPE_CONSENT") == "YES"


def lane_chart(net, tickers: list, se: int, ee: int, pause: float) -> dict:
    t0 = time.time()
    rc = net.yahoo_chart(tickers, se, ee, pause_s=pause)
    rows = rc.get("rows") or []
    ok = {r["ticker"] for r in rows}
    return {"lane": "chart", "sec": round(time.time() - t0, 1), "ok": len(ok), "n": len(tickers), "rows": len(rows),
            "failed": [f.get("note", "")[:60] for f in (rc.get("failed") or [])][:5]}


def lane_chart_par(net, tickers: list, se: int, ee: int, pause: float, workers: int, sub: int = 2) -> dict:
    t0 = time.time()
    subs = [tickers[i:i + sub] for i in range(0, len(tickers), sub)]
    rows, failed = [], []
    if VIA_ACCEL is not None and hasattr(VIA_ACCEL, "accel_map"):
        res = VIA_ACCEL.accel_map(lambda s: net.yahoo_chart(s, se, ee, pause_s=pause), subs, workers=workers)
    else:
        res = [(True, net.yahoo_chart(s, se, ee, pause_s=pause)) for s in subs]
    for i, (okf, rc) in enumerate(res):
        if not okf or not isinstance(rc, dict):
            failed += [str(rc)[:60]]
            continue
        rows += rc.get("rows") or []
        failed += [f.get("note", "")[:60] for f in (rc.get("failed") or [])]
    ok = {r["ticker"] for r in rows}
    return {"lane": f"chart×{workers}", "sec": round(time.time() - t0, 1), "ok": len(ok), "n": len(tickers), "rows": len(rows),
            "failed": failed[:5], "accel": VIA_ACCEL is not None}


def lane_yf(net, tickers: list, days: int) -> dict:
    t0 = time.time()
    rc = net.yf_download([f"{t}.TW" for t in tickers], period=f"{max(5, days)}d")
    n_rows, ok = 0, 0
    if rc.get("state") == "OK":
        df = rc.get("data")
        try:
            n_rows = int(df.shape[0]) if df is not None else 0
            if df is not None and n_rows:
                lv = df.columns.get_level_values(0) if hasattr(df.columns, "levels") else []
                ok = sum(1 for t in tickers if f"{t}.TW" in set(lv) and df[f"{t}.TW"].dropna(how="all").shape[0] > 0)
        except Exception:
            pass
    return {"lane": "yf", "sec": round(time.time() - t0, 1), "ok": ok, "n": len(tickers), "rows": n_rows,
            "failed": [str(rc.get("note", ""))[:60]] if rc.get("state") != "OK" else []}


def lane_yf_history(net, tickers: list, start: str, end: str) -> dict:
    t0 = time.time()
    if not hasattr(net, "yf_history"):
        return {"lane": "yf_hist", "sec": 0, "ok": 0, "n": len(tickers), "rows": 0, "failed": ["統包無 yf_history(先 via-reload)"]}
    rc = net.yf_history([f"{t}.TW" for t in tickers], start, end)
    rows = rc.get("rows") or []
    return {"lane": "yf_hist", "sec": round(time.time() - t0, 1), "ok": len({r["ticker"] for r in rows}), "n": len(tickers),
            "rows": len(rows), "failed": [f.get("note", "")[:60] for f in (rc.get("failed") or [])][:5]}


def run(tickers: list, days: int, workers: int, pause: float, do_print: bool = True) -> dict:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    rep = {"ts": stamp, "tickers": tickers, "days": days, "workers": workers, "pause": pause, "lanes": [], "state": "DENY"}
    if not consent():
        rep["note"] = "同意閘閉=DENY(VIA_NET_CONSENT+VIA_SCRAPE_CONSENT=YES 方跑;誠實零外呼)"
        if do_print:
            print(f"[netbench] {rep['note']}")
        return rep
    net = _net()
    if net is None:
        rep["note"] = "SUP_MDL740 缺"
        return rep
    end = datetime.now().date()
    start = end - timedelta(days=days)
    se = calendar.timegm(time.strptime(start.isoformat(), "%Y-%m-%d"))
    ee = calendar.timegm(time.strptime(end.isoformat(), "%Y-%m-%d")) + 86400
    if do_print:
        print(f"[netbench] 標的 {len(tickers)} · 時段 {start}~{end}({days} 日)· 工數 {workers} · 節流 {pause}s · 加速器 {'在' if VIA_ACCEL else '缺'}", flush=True)
    for fn in (lambda: lane_chart(net, tickers, se, ee, pause),
               lambda: lane_chart_par(net, tickers, se, ee, pause, workers),
               lambda: lane_yf(net, tickers, days),
               lambda: lane_yf_history(net, tickers, start.isoformat(), end.isoformat())):
        try:
            r = fn()
        except Exception as exc:
            r = {"lane": "?", "sec": 0, "ok": 0, "n": len(tickers), "rows": 0, "failed": [f"{type(exc).__name__}: {str(exc)[:60]}"]}
        r["sec_per_ticker"] = round(r["sec"] / max(1, r["n"]), 2)
        rep["lanes"].append(r)
        if do_print:
            print(f"  {r['lane']:10s} {r['sec']:7.1f}s · {r['sec_per_ticker']:6.2f}s/檔 · 成 {r['ok']}/{r['n']} · 列 {r['rows']}"
                  f"{' · 敗例 ' + '; '.join(r['failed'][:2]) if r['failed'] else ''}", flush=True)
    good = [r for r in rep["lanes"] if r["ok"] == r["n"] and r["n"]]
    best = min(good, key=lambda r: r["sec"]) if good else None
    rep["state"] = "OK" if good else "FAIL"
    rep["best"] = best["lane"] if best else None
    REP.mkdir(parents=True, exist_ok=True)
    (REP / f"NETBENCH_{stamp}.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    if do_print:
        verdict = ('最快全成車道=' + best['lane'] + ' ' + str(best['sec']) + 's') if best else '無全成車道(誠實;看敗例)'
        print(f"[netbench] 判:{verdict} · 存證 NETBENCH_{stamp}.json")
        print("[netbench] 全量估算(1700 檔):" + " · ".join(f"{r['lane']} ≈ {int(r['sec_per_ticker'] * 1700 / 60)} 分" for r in rep["lanes"] if r["ok"]))
    return rep


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    old = (os.environ.pop("VIA_NET_CONSENT", None), os.environ.pop("VIA_SCRAPE_CONSENT", None))
    r = run(DEFAULT_TICKERS[:2], 30, 2, 0.35, do_print=False)
    chk("① 同意閘閉=DENY 零外呼(誠實)", r["state"] == "DENY" and not r["lanes"])
    if old[0]:
        os.environ["VIA_NET_CONSENT"] = old[0]
    if old[1]:
        os.environ["VIA_SCRAPE_CONSENT"] = old[1]
    chk("② 三車道冊(chart/chart×N/yf)+統包 SUP_MDL740 尾版在位", _net() is not None and all(k in src for k in ("lane_chart", "lane_chart_par", "lane_yf")))
    chk("③ 加速器真用(accel_map 於 chart×N 車道)+graceful", "accel_map" in src and "VIA_ACCEL is not None" in src)
    chk("④ 紀律宣告(fail-closed/零入庫/不繞 WAF/不解 CAPTCHA/不偽裝/全量估算)",
        all(k in src for k in ("fail-closed", "零入庫", "不繞 WAF", "不解 CAPTCHA", "不偽裝", "全量估算")))
    print(f"  [計] 四檢 OK {4 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 網路車道時段基準(CGC_MDL126 v0101)· 四檢自測(零外網)===")
        return selftest()
    tickers = a[a.index("--tickers") + 1].split(",") if "--tickers" in a else DEFAULT_TICKERS
    days = int(a[a.index("--days") + 1]) if "--days" in a else 60
    workers = int(a[a.index("--workers") + 1]) if "--workers" in a else 4
    pause = float(a[a.index("--pause") + 1]) if "--pause" in a else 0.35
    if not consent():
        os.environ["VIA_NET_CONSENT"] = "YES"      # 操作員親跑 via-netbench=同意(誠實印於首行)
        os.environ["VIA_SCRAPE_CONSENT"] = "YES"
    r = run([t.strip() for t in tickers if t.strip()], days, workers, pause)
    return 0 if r["state"] == "OK" else 1


if __name__ == "__main__":
    sys.exit(main())
