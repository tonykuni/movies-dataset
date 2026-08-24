#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_ENG049_FiveDayFetch — 五日相關數據擷取引擎(批112;via-fetch5d)
====================================================================
令:「VDF 接好加速器跟網路工具組後,啟動擷取五日相關數據」。
目標宇宙(兩冊聯集,glob 最新版):
  ① TA 規格冊 universe(DXY/匯率三/公債殖利率/VIX/黃金/BTC/加密 ETF/雙基準)
  ② VDF 台股焦點清單(族群冊 149 檔,yfinance 三代號)
法遵閘:VIA_NET_CONSENT=YES 才實連(批112 操作員明令啟動=本波同意,
  仍須 env 明示;缺=誠實 FAIL-CLOSED)。
預檢:實抓前單點探測 Yahoo 端點;環境網路政策封鎖(403/CONNECT 拒)=
  誠實 NETWORK_POLICY_BLOCKED,列印待抓清單存證,不硬撞不假抓。
抓法:yf.download 批次(5d,1d K,auto_adjust=False 保 Adj Close 分離);
輸出:output_hub/fiveday/(long csv utf-8-sig+json+parquet)。
用法:
  via-fetch5d            → 預檢+實抓(需同意閘)
  via-fetch5d --plan     → 只列目標宇宙(零網路)
  via-fetch5d --selftest → 八檢(沙盒零網路)
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

import json
import os
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF = HERE.parent
VIA = VDF.parent.parent
OUT = VDF / "output_hub" / "fiveday"
PREFLIGHT_HOST = "https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC?range=1d&interval=1d"


def _newest(folder: Path, pattern: str) -> Path | None:
    hits = sorted(folder.glob(pattern))
    return hits[-1] if hits else None


def build_universe(root: Path = VDF) -> dict:
    """兩冊聯集 → {ticker: 說明};zh 名保留"""
    tickers = {}
    ta = _newest(root, "VDF_TA_Engine_Spec_v*.json")
    if ta:
        spec = json.loads(ta.read_text(encoding="utf-8-sig"))
        for u in spec.get("universe", []):
            yf = u.get("yf") or ""
            for t in [x.strip() for x in yf.split("/") if x.strip() and "(" not in x]:
                tickers[t] = u["zh"]
    fu = _newest(root, "VDF_TW_Focus_Universe_v*.json")
    if fu:
        uni = json.loads(fu.read_text(encoding="utf-8-sig"))
        for m in uni.get("members", []):
            if m.get("yfinance"):
                tickers[m["yfinance"]] = f"{m['name']}({m['group']})"
    return tickers


def preflight(http_probe=None) -> dict:
    """單點探測;403/CONNECT 拒=環境網路政策封鎖(誠實,不硬撞)"""
    if http_probe is not None:
        return http_probe()
    try:
        import urllib.request
        req = urllib.request.Request(PREFLIGHT_HOST, headers={"User-Agent": "Mozilla/5.0 VeritasDataForge/VDF"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return {"reachable": r.status == 200, "detail": f"HTTP {r.status}"}
    except Exception as exc:
        msg = str(exc)
        blocked = "403" in msg or "CONNECT" in msg or "Tunnel" in msg.lower() or "policy" in msg.lower()
        return {"reachable": False, "blocked_by_policy": blocked, "detail": msg[:140]}


def fetch_5d(tickers: list[str], fetch_fn=None) -> dict:
    """yf.download 批次 5d;fetch_fn 可注入替身(selftest)"""
    if fetch_fn is not None:
        return fetch_fn(tickers)
    import yfinance as yf
    df = yf.download(tickers, period="5d", interval="1d", auto_adjust=False,
                     progress=False, threads=True, group_by="ticker")
    rows = []
    got = set()
    for t in tickers:
        try:
            sub = df[t] if len(tickers) > 1 else df
            sub = sub.dropna(how="all")
            for dt, r in sub.iterrows():
                rows.append({"date": str(dt)[:10], "ticker": t,
                             "open": r.get("Open"), "high": r.get("High"),
                             "low": r.get("Low"), "close": r.get("Close"),
                             "adj_close": r.get("Adj Close"), "volume": r.get("Volume")})
            if len(sub):
                got.add(t)
        except Exception:
            continue
    return {"rows": rows, "ok_tickers": sorted(got),
            "fail_tickers": sorted(set(tickers) - got)}


def write_run(result: dict, meta: dict) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    jp = OUT / f"FIVEDAY_{ts}.json"
    jp.write_text(json.dumps({**meta, **{k: result[k] for k in ("ok_tickers", "fail_tickers")},
                              "row_count": len(result["rows"]), "rows": result["rows"]},
                             ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    try:
        import pandas as pd
        df = pd.DataFrame(result["rows"])
        df.to_csv(OUT / f"FIVEDAY_{ts}.csv", index=False, encoding="utf-8-sig")
        df.to_parquet(OUT / f"FIVEDAY_{ts}.parquet", index=False)
    except Exception:
        pass
    return jp


def run(plan_only: bool, http_probe=None, fetch_fn=None, env=None) -> int:
    env = env if env is not None else os.environ
    uni = build_universe()
    print(f"=== 五日擷取(批112)· 目標宇宙 {len(uni)} 檔(TA 冊+台股焦點 149)===")
    if plan_only:
        for t, zh in list(uni.items())[:12]:
            print(f"  {t:<12} {zh}")
        print(f"  …共 {len(uni)} 檔(--plan 零網路)")
        return 0
    if env.get("VIA_NET_CONSENT", "") != "YES":
        print("[FAIL-CLOSED] VIA_NET_CONSENT≠YES:同意閘未開,零外呼(絕不代設)")
        return 2
    pf = preflight(http_probe=http_probe)
    if not pf.get("reachable"):
        state = "NETWORK_POLICY_BLOCKED" if pf.get("blocked_by_policy") else "NETWORK_UNREACHABLE"
        print(f"[{state}] 預檢失敗:{pf['detail']}")
        print(f"  誠實結束:待抓 {len(uni)} 檔清單已備;於可達網路環境(工作站)重跑即實抓")
        jp = write_run({"rows": [], "ok_tickers": [], "fail_tickers": sorted(uni)},
                       {"schema": "vdf.fiveday.run.v1", "state": state,
                        "preflight": pf, "universe_count": len(uni)})
        print(f"  [存證] {jp.name}")
        return 3
    res = fetch_5d(sorted(uni), fetch_fn=fetch_fn)
    jp = write_run(res, {"schema": "vdf.fiveday.run.v1", "state": "FETCHED",
                         "universe_count": len(uni)})
    print(f"  [計] 列 {len(res['rows'])} · OK {len(res['ok_tickers'])} 檔 · FAIL {len(res['fail_tickers'])} 檔 · {jp.name}")
    return 0 if not res["fail_tickers"] else 1


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    uni = build_universe()
    chk("① 宇宙聯集(TA 冊+焦點 149)", len(uni) >= 155, f"({len(uni)} 檔)")
    chk("② 台股焦點入宇宙(2330.TW)", "2330.TW" in uni)
    chk("③ TA 冊件入宇宙(TWD=X/GC=F/BTC-USD)",
        all(t in uni for t in ("TWD=X", "GC=F", "BTC-USD")))
    # ④ 同意閘 fail-closed
    chk("④ 同意閘未開=rc2", run(False, env={}) == 2)
    # ⑤ 預檢封鎖=rc3+存證
    rc = run(False, env={"VIA_NET_CONSENT": "YES"},
             http_probe=lambda: {"reachable": False, "blocked_by_policy": True,
                                 "detail": "CONNECT 403(沙盒模擬)"})
    chk("⑤ 政策封鎖=rc3 誠實存證", rc == 3)
    # ⑥ 替身抓取管線(5 列合成)
    def fake_fetch(ts):
        rows = [{"date": f"2026-08-{18+i:02d}", "ticker": ts[0], "open": 1, "high": 2,
                 "low": 0.5, "close": 1.5, "adj_close": 1.4, "volume": 100} for i in range(5)]
        return {"rows": rows, "ok_tickers": [ts[0]], "fail_tickers": ts[1:]}
    rc = run(False, env={"VIA_NET_CONSENT": "YES"},
             http_probe=lambda: {"reachable": True, "detail": "HTTP 200(沙盒)"},
             fetch_fn=fake_fetch)
    chk("⑥ 替身管線通(rc1=部分 FAIL 誠實)", rc == 1)
    # ⑦ 落檔驗證(最新 run json 有 5 列)
    latest = sorted(OUT.glob("FIVEDAY_*.json"))[-1]
    d = json.loads(latest.read_text(encoding="utf-8"))
    chk("⑦ run 存證含列+Adj 欄", d["row_count"] == 5 and d["rows"][0]["adj_close"] == 1.4)
    # ⑧ yfinance 工具組在位
    try:
        import yfinance
        chk("⑧ yfinance 網路工具組在位", True, f"(v{yfinance.__version__})")
    except Exception:
        chk("⑧ yfinance 網路工具組在位", False)
    n = 8 - len(fails)
    print(f"  [計] 八檢 OK {n} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== ENG049 五日擷取 · 八檢自測(沙盒零網路)===")
        return selftest()
    return run("--plan" in args)


if __name__ == "__main__":
    sys.exit(main())
