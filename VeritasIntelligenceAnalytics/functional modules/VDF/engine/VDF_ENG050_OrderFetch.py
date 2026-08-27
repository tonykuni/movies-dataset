#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_ENG050_OrderFetch — 擷取單接單引擎(批114;via-order)
====================================================================
冊:VDF_Fetch_Orders(glob 最新版;append-only 單號制)。
雙車道:
  twse_official:TWSE/TPEX 官方端點,{YYYYMMDD} 逐交易日回溯至湊滿 5 交易日
  yfinance:yf.download 批次 5d(auto_adjust=False 保 Adj Close 分離)
鐵則:同意閘 VIA_NET_CONSENT=YES;預檢單點探測(雙車道各一);
  封鎖=誠實 NETWORK_POLICY_BLOCKED 存證不硬撞;空白取前一交易日;
  台股籌碼 T+1 紀律(FQ-01/02/04);零假抓零模擬。
輸出:output_hub/orders/ORDER_<id>_<ts>/(每標的 json+csv;yf 線另 parquet)。
用法:
  via-order --order 001          → 接單實抓
  via-order --order 001 --plan   → 零網路列單
  via-order --selftest           → 八檢(沙盒零網路)
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

import csv
import io
import json
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF = HERE.parent
OUT = VDF / "output_hub" / "orders"
ORDERS_GLOB = "VDF_Fetch_Orders_v*.json"
UA = {"User-Agent": "Mozilla/5.0 VeritasDataForge/VDF"}
PROBES = {"twse_official": "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL",
          "yfinance": "https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC?range=1d&interval=1d"}


def load_orders(root: Path = VDF) -> dict | None:
    hits = sorted(root.glob(ORDERS_GLOB))
    return json.loads(hits[-1].read_text(encoding="utf-8-sig")) if hits else None


def get_order(oid: str, book: dict | None = None) -> dict | None:
    book = book or load_orders()
    if book is None:
        return None
    return next((o for o in book["orders"] if o["order_id"] == oid), None)


def trading_days_back(n: int, today: date | None = None) -> list[str]:
    """回溯 n 個平日(YYYYMMDD;假日由端點空回應自然跳過=誠實)"""
    d = today or date.today()
    out = []
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.strftime("%Y%m%d"))
        d -= timedelta(days=1)
    return out


def _http_json(url: str, timeout: int = 30, http=None):
    if http is not None:
        return http(url)
    import urllib.request
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def preflight(lane: str, http=None) -> dict:
    try:
        _http_json(PROBES[lane], timeout=15, http=http)
        return {"lane": lane, "reachable": True}
    except Exception as exc:
        msg = str(exc)
        return {"lane": lane, "reachable": False,
                "blocked_by_policy": ("403" in msg or "CONNECT" in msg or "Tunnel" in msg),
                "detail": msg[:120]}


def fetch_twse_lane(targets: list[dict], days: list[str], http=None) -> dict:
    results = []
    for t in targets:
        ep = t["endpoint"]
        if "{YYYYMMDD}" in ep:
            got = []
            for d in days:
                try:
                    data = _http_json(ep.replace("{YYYYMMDD}", d), http=http)
                    if data and (data.get("data") or data.get("tables")):
                        got.append({"date": d, "payload": data})
                except Exception:
                    continue
            results.append({"key": t["key"], "state": "OK" if got else "EMPTY",
                            "days": len(got), "data": got})
        else:
            try:
                data = _http_json(ep, http=http)
                results.append({"key": t["key"], "state": "OK",
                                "rows": len(data) if isinstance(data, list) else 1,
                                "data": data})
            except Exception as exc:
                results.append({"key": t["key"], "state": "FAIL", "note": str(exc)[:100]})
    return {"results": results}


def fetch_yf_lane(targets: list[dict], fetch_fn=None) -> dict:
    tickers = [t["yf"] for t in targets]
    if fetch_fn is not None:
        return fetch_fn(tickers)
    import yfinance as yf
    df = yf.download(tickers, period="5d", interval="1d", auto_adjust=False,
                     progress=False, threads=True, group_by="ticker")
    rows, got = [], set()
    for t in tickers:
        try:
            sub = (df[t] if len(tickers) > 1 else df).dropna(how="all")
            for dt, r in sub.iterrows():
                rows.append({"date": str(dt)[:10], "ticker": t,
                             "open": r.get("Open"), "high": r.get("High"),
                             "low": r.get("Low"), "close": r.get("Close"),
                             "adj_close": r.get("Adj Close"), "volume": r.get("Volume")})
            if len(sub):
                got.add(t)
        except Exception:
            continue
    return {"rows": rows, "ok": sorted(got), "fail": sorted(set(tickers) - got)}


def write_order_run(oid: str, payload: dict) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = OUT / f"ORDER_{oid}_{ts}"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    yf_rows = payload.get("yf", {}).get("rows", [])
    if yf_rows:
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=list(yf_rows[0].keys()))
        w.writeheader()
        w.writerows(yf_rows)
        (run_dir / "yf_5d.csv").write_text(buf.getvalue(), encoding="utf-8-sig")
    return run_dir


def run(oid: str, plan_only: bool, env=None, http=None, yf_fn=None) -> int:
    env = env if env is not None else os.environ
    order = get_order(oid)
    if order is None:
        print(f"[FAIL] 擷取單 {oid} 不在冊")
        return 1
    tw = order["lanes"]["twse_official"]["targets"]
    yf_t = order["lanes"]["yfinance"]["targets"]
    print(f"=== 擷取單 #{oid}(批114)· 官方線 {len(tw)} 項 + 國際線 {len(yf_t)} 檔 · 窗口 {order['window']} ===")
    if plan_only:
        for t in tw:
            print(f"  [TWSE] {t['key']:<16} {t['zh']}")
        for t in yf_t:
            print(f"  [YF]   {t['yf']:<12} {t['zh']}")
        return 0
    if env.get("VIA_NET_CONSENT", "") != "YES":
        print("[FAIL-CLOSED] VIA_NET_CONSENT≠YES:同意閘未開,零外呼(絕不代設)")
        return 2
    pf = [preflight("twse_official", http=http), preflight("yfinance", http=http)]
    blocked = [p for p in pf if not p["reachable"]]
    if len(blocked) == 2:
        print("[NETWORK_POLICY_BLOCKED] 雙車道預檢全封:" +
              " | ".join(f"{p['lane']}:{p.get('detail', '')[:60]}" for p in blocked))
        rd = write_order_run(oid, {"schema": "vdf.order.run.v1", "order": oid,
                                   "state": "NETWORK_POLICY_BLOCKED", "preflight": pf})
        print(f"  誠實結束存證:{rd.name};可達網路環境重跑即實抓")
        return 3
    days = trading_days_back(5)
    payload = {"schema": "vdf.order.run.v1", "order": oid, "state": "FETCHED",
               "days": days, "preflight": pf}
    if pf[0]["reachable"]:
        payload["twse"] = fetch_twse_lane(tw, days, http=http)
    else:
        payload["twse"] = {"state": "LANE_BLOCKED", "detail": pf[0].get("detail")}
    if pf[1]["reachable"]:
        payload["yf"] = fetch_yf_lane(yf_t, fetch_fn=yf_fn)
    else:
        payload["yf"] = {"state": "LANE_BLOCKED", "detail": pf[1].get("detail")}
    rd = write_order_run(oid, payload)
    twr = payload["twse"].get("results", [])
    yfr = payload["yf"]
    print(f"  [官方線] OK {sum(1 for r in twr if r.get('state') == 'OK')}/{len(tw)}"
          f" · [國際線] OK {len(yfr.get('ok', []))}/{len(yf_t)} 列 {len(yfr.get('rows', []))}"
          f" · 存 {rd.name}")
    return 0


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    book = load_orders()
    chk("① 擷取單冊在位", book is not None)
    o = get_order("001", book)
    chk("② 單 001 在冊(官方 7+國際 17)", o is not None
        and len(o["lanes"]["twse_official"]["targets"]) == 7
        and len(o["lanes"]["yfinance"]["targets"]) == 17)
    d5 = trading_days_back(5, today=date(2026, 8, 24))  # 週一
    chk("③ 回溯 5 平日(跨週末)", d5 == ["20260824", "20260821", "20260820", "20260819", "20260818"], str(d5[:2]))
    chk("④ 同意閘未開=rc2", run("001", False, env={}) == 2)
    rc = run("001", False, env={"VIA_NET_CONSENT": "YES"},
             http=lambda u: (_ for _ in ()).throw(RuntimeError("CONNECT 403 Forbidden(沙盒)")))
    chk("⑤ 雙道封鎖=rc3 誠實存證", rc == 3)
    # ⑥ 替身雙道管線
    def fake_http(url):
        if "STOCK_DAY_ALL" in url or "tpex" in url or "highlight" in url:
            return [{"Code": "2330", "Name": "台積電", "ClosingPrice": "1000"}]
        return {"data": [["r"]], "date": "ok"}
    def fake_yf(ts):
        return {"rows": [{"date": "2026-08-22", "ticker": ts[0], "open": 1, "high": 1,
                          "low": 1, "close": 1, "adj_close": 1, "volume": 1}],
                "ok": ts[:1], "fail": ts[1:]}
    rc = run("001", False, env={"VIA_NET_CONSENT": "YES"}, http=fake_http, yf_fn=fake_yf)
    chk("⑥ 替身雙道通(rc0)", rc == 0)
    runs = sorted(OUT.glob("ORDER_001_*/run.json"))
    d = json.loads(runs[-1].read_text(encoding="utf-8"))
    chk("⑦ run 存證(twse 7 結果+yf 列)", len(d["twse"]["results"]) == 7
        and d["yf"]["rows"][0]["adj_close"] == 1)
    chk("⑧ csv 落檔(utf-8-sig)", (runs[-1].parent / "yf_5d.csv").read_bytes()[:3] == b"\xef\xbb\xbf")
    n = 8 - len(fails)
    print(f"  [計] 八檢 OK {n} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== ENG050 擷取單引擎 · 八檢自測(沙盒零網路)===")
        return selftest()
    oid = "001"
    if "--order" in args:
        i = args.index("--order")
        oid = args[i + 1] if i + 1 < len(args) else "001"
    return run(oid, "--plan" in args)


if __name__ == "__main__":
    sys.exit(main())
