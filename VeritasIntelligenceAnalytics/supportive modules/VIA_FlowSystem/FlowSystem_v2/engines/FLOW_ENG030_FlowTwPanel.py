#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""flow_tw_panel — 台股族群成員真實面板道(批309)
====================================================================
供 APCE(FLOW_ENG029)之長表面板:族群冊(TW_Group_Classification 最新版)
成員 × 日 × 欄。資料道(誠實標源):
  Yahoo chart(還原收盤/OHLC/量;trust=medium;VDF 冊既定 yfinance 道)
    → 歷史面(自 2025-12-30 起);成交值=量×收盤 PROXY(官方值到日覆蓋)
  TWSE STOCK_DAY_ALL(上市個股成交值/收盤;官方)——當日快照累積
  TPEx mainboard_quotes(上櫃個股成交值/收盤/資本額;官方)——當日累積
  TPEx 3insti_daily_trading(上櫃個股三大法人買賣超股數)——當日累積
  TPEx mainboard_margin_balance(上櫃融資融券餘額)——當日累積
  官方股數:t187ap03_L(上市)+t187ap03_O IssueShares(上櫃)→ 市值分層
  TWSE 個股當沖/法人/融資:雲端 IP 遭 WAF 封鎖=工作站側車(--ingest)
面板落 data/input/tw_apce_panel.json({rows:[…],coverage,provenance});
Yahoo 原始檔快取 data/input/yahoo_raw/<ticker>.json(當日不重抓)。
用法:
  --build     建/更新面板(同意閘;Yahoo 歷史+官方當日快照)
  --run       跑 APCE(基準日 2026-01-01)→ data/output/apce_latest.json
  --ingest <json>  工作站列餵入(date,ticker,dt_turnover,f_net,s_net,d_net,…)
  --selftest  六檢(解析器零網路)
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(路徑引導版;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import importlib.util
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CFG = ROOT / "config"
INP = ROOT / "data" / "input"
PANEL = INP / "tw_apce_panel.json"
YRAW = INP / "yahoo_raw"
VIA = ROOT.parent.parent.parent
VAL308 = VIA / "validation" / "VIA_Batch308_TwFlow_Buildout"
NOW = datetime.now().strftime("%Y-%m-%d %H:%M")
TODAY = datetime.now().strftime("%Y%m%d")

ENDPOINTS = {
    "yahoo": "https://query1.finance.yahoo.com/v8/finance/chart/{sym}?period1=1767052800&period2={p2}&interval=1d&events=div,split",
    "twse_stock_day": "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL",
    "tpex_quotes": "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_quotes",
    "tpex_3insti": "https://www.tpex.org.tw/openapi/v1/tpex_3insti_daily_trading",
    "tpex_margin": "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_margin_balance",
    "twse_registry": "https://openapi.twse.com.tw/v1/opendata/t187ap03_L",
    "tpex_registry": "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O",
}
K3 = {"f": "ForeignInvestorsInclude MainlandAreaInvestors-Difference",
      "s": "SecuritiesInvestmentTrustCompanies-Difference", "d": "Dealers-Difference"}


def _f(x):
    try:
        return float(str(x).replace(",", "").replace("+", ""))
    except (TypeError, ValueError):
        return None


def _roc(d: str) -> str:
    s = str(d).strip()
    return f"{int(s[:3]) + 1911}-{s[3:5]}-{s[5:7]}" if (len(s) == 7 and s.isdigit()) else s


def load_members() -> list[dict]:
    hits = sorted(CFG.glob("TW_Group_Classification_v*.json"))
    g = json.loads(hits[-1].read_text(encoding="utf-8"))
    out = []
    for gname, mem in g["groups"].items():
        for m in mem:
            if str(m.get("official_status", "")).startswith("NOT_IN_OFFICIAL"):
                continue  # 官方查無=誠實不入面板
            out.append({"ticker": m["ticker"], "sector": gname, "market": m.get("market", "TWSE"),
                        "yf": m.get("yfinance") or (m["ticker"] + (".TW" if m.get("market") == "TWSE" else ".TWO"))})
    seen, uniq = set(), []
    for m in out:  # 跨群多屬取首群(指數不重複計數;冊載 DISPLAY_ONLY 律)
        if m["ticker"] not in seen:
            seen.add(m["ticker"])
            uniq.append(m)
    return uniq


# ─────────────────────────── 解析器 ───────────────────────────

def parse_yahoo(raw: str, meta: dict) -> list[dict]:
    try:
        r = json.loads(raw)["chart"]["result"][0]
    except Exception:
        return []
    ts = r.get("timestamp", [])
    q = r["indicators"]["quote"][0]
    adj = (r["indicators"].get("adjclose") or [{}])[0].get("adjclose", [None] * len(ts))
    rows = []
    for k, t in enumerate(ts):
        d = datetime.fromtimestamp(int(t), tz=timezone.utc).strftime("%Y-%m-%d")
        c, v = q["close"][k], q["volume"][k]
        if c is None:
            continue
        rows.append({"date": d, "ticker": meta["ticker"], "sector": meta["sector"], "market": meta["market"],
                     "open": q["open"][k], "high": q["high"][k], "low": q["low"][k], "close": c,
                     "adj_close": adj[k] if k < len(adj) else None, "volume": v,
                     "turnover": (v * c) if v is not None else None, "turnover_basis": "PROXY_VOL_X_CLOSE",
                     "src": "yahoo(trust=medium)"})
    return rows


def parse_twse_day(rows: list) -> dict:
    """STOCK_DAY_ALL → {ticker:{date,close,turnover(官方),open,high,low,volume}}"""
    out = {}
    for r in rows:
        c = str(r.get("Code", "")).strip()
        if c:
            out[c] = {"date": _roc(r.get("Date")), "close": _f(r.get("ClosingPrice")), "open": _f(r.get("OpeningPrice")),
                      "high": _f(r.get("HighestPrice")), "low": _f(r.get("LowestPrice")),
                      "volume": _f(r.get("TradeVolume")), "turnover": _f(r.get("TradeValue"))}
    return out


def parse_tpex_quotes(rows: list) -> dict:
    out = {}
    for r in rows:
        c = str(r.get("SecuritiesCompanyCode", "")).strip()
        if c:
            out[c] = {"date": _roc(r.get("Date")), "close": _f(r.get("Close")), "open": _f(r.get("Open")),
                      "high": _f(r.get("High")), "low": _f(r.get("Low")), "volume": _f(r.get("TradingShares")),
                      "turnover": _f(r.get("TransactionAmount")),
                      "shares": (_f(r.get("Capitals")) / 10.0) if _f(r.get("Capitals")) else None}
    return out


def parse_tpex_3insti(rows: list) -> dict:
    out = {}
    for r in rows:
        c = str(r.get("SecuritiesCompanyCode", "")).strip()
        if c:
            out[c] = {"date": _roc(r.get("Date")), "f_net": _f(r.get(K3["f"])), "s_net": _f(r.get(K3["s"])),
                      "d_net": _f(r.get(K3["d"]))}
    return out


def parse_tpex_margin(rows: list) -> dict:
    out = {}
    for r in rows:
        c = str(r.get("SecuritiesCompanyCode", "")).strip()
        if c:
            ml, mp = _f(r.get("MarginPurchaseBalance")), _f(r.get("MarginPurchaseBalancePreviousDay"))
            out[c] = {"date": _roc(r.get("Date")), "margin_long": ml, "margin_short": _f(r.get("ShortSaleBalance")),
                      "margin_long_diff": (ml - mp) if (ml is not None and mp is not None) else None}
    return out


def load_shares() -> dict:
    """官方股數:上市 t187ap03_L + 上櫃 t187ap03_O(IssueShares);來源=批308 快照或本地 twse_shares_last。"""
    sh = {}
    p = INP / "twse_shares_last.json"
    if p.exists():
        sh.update({k: float(v) for k, v in json.loads(p.read_text(encoding="utf-8")).items()})
    snap = VAL308 / "tpex_t187ap03_O_snapshot_20260902.json"
    if snap.exists():
        for r in json.loads(snap.read_text(encoding="utf-8")):
            c, v = str(r.get("SecuritiesCompanyCode", "")).strip(), _f(r.get("IssueShares"))
            if c and v:
                sh[c] = v
    return sh


# ─────────────────────────── 命令 ───────────────────────────

def load_panel() -> dict:
    if PANEL.exists():
        return json.loads(PANEL.read_text(encoding="utf-8"))
    return {"schema": "tw-apce-panel-v1", "rows": [], "provenance": []}


def save_panel(pan: dict):
    INP.mkdir(parents=True, exist_ok=True)
    rows = pan["rows"]
    cols = ["open", "high", "low", "close", "adj_close", "volume", "turnover", "dt_turnover", "shares",
            "f_net", "s_net", "d_net", "margin_long", "margin_short"]
    n = len(rows) or 1
    pan["coverage"] = {c: round(sum(1 for r in rows if r.get(c) is not None) / n, 3) for c in cols}
    pan["n_rows"], pan["n_tickers"] = len(rows), len({r["ticker"] for r in rows})
    pan["dates"] = sorted({r["date"] for r in rows})
    pan["ts"] = NOW
    PANEL.write_text(json.dumps(pan, ensure_ascii=False), encoding="utf-8")


def upsert(pan: dict, key_rows: dict, fields: dict, note: str):
    """key_rows:{(date,ticker):row};fields:{(date,ticker):{...}} 覆蓋/新增(官方值優先)。"""
    n_new = n_up = 0
    for k, f in fields.items():
        d, t = k
        if k in key_rows:
            for kk, vv in f.items():
                if vv is not None:
                    key_rows[k][kk] = vv
            n_up += 1
        else:
            r = {"date": d, "ticker": t, **f}
            pan["rows"].append(r)
            key_rows[k] = r
            n_new += 1
    pan["provenance"].append({"ts": NOW, "note": note, "new": n_new, "updated": n_up})
    return n_new, n_up


def cmd_build() -> int:
    if VIA_ACCEL is None:
        print("  [SKIP] SuperAccel 未載——無網路道(誠實)")
        return 0
    members = load_members()
    meta = {m["ticker"]: m for m in members}
    pan = load_panel()
    key_rows = {(r["date"], r["ticker"]): r for r in pan["rows"]}
    shares = load_shares()
    # ① Yahoo 歷史(當日快取不重抓)
    YRAW.mkdir(parents=True, exist_ok=True)
    p2 = int(time.time())
    n_ok = n_skip = 0
    fields = {}
    for m in members:
        cf = YRAW / f"{m['ticker']}_{TODAY}.json"
        if cf.exists():
            raw = cf.read_text(encoding="utf-8")
        else:
            raw = VIA_ACCEL.fetch(ENDPOINTS["yahoo"].format(sym=m["yf"], p2=p2), timeout=20, cache=False)
            if raw:
                cf.write_text(raw, encoding="utf-8")
            time.sleep(0.15)
        rows = parse_yahoo(raw, m) if raw else []
        if not rows:
            n_skip += 1
            continue
        n_ok += 1
        for r in rows:
            r["shares"] = shares.get(m["ticker"])
            fields[(r["date"], r["ticker"])] = r
    # 既有官方 turnover 不被 PROXY 覆蓋
    for k, f in fields.items():
        if k in key_rows and key_rows[k].get("turnover_basis") == "OFFICIAL":
            f.pop("turnover", None)
            f.pop("turnover_basis", None)
    upsert(pan, key_rows, fields, f"yahoo 歷史 {n_ok} 檔(缺 {n_skip})")
    print(f"  [Yahoo] {n_ok} 檔歷史入面板(trust=medium;{n_skip} 檔無回應誠實缺)")
    # ② 官方當日快照(成交值/收盤 覆蓋 PROXY)
    def getj(key, timeout=60):
        raw = VIA_ACCEL.fetch(ENDPOINTS[key], timeout=timeout, cache=False)
        try:
            return json.loads(raw) if raw else None
        except Exception:
            return None
    sd = getj("twse_stock_day")
    if sd:
        q = parse_twse_day(sd)
        f = {(v["date"], t): {**v, "turnover_basis": "OFFICIAL", "sector": meta[t]["sector"], "market": meta[t]["market"],
                             "shares": shares.get(t)} for t, v in q.items() if t in meta and v["turnover"] is not None}
        n1, n2 = upsert(pan, key_rows, f, "TWSE STOCK_DAY_ALL 官方當日")
        print(f"  [TWSE] 官方個股成交值/收盤 {len(f)} 檔(新 {n1}/覆 {n2})")
    else:
        print("  [SKIP] TWSE STOCK_DAY_ALL 未達(限流/WAF;誠實缺席)")
    tq = getj("tpex_quotes")
    if tq:
        q = parse_tpex_quotes(tq)
        f = {(v["date"], t): {**{k: vv for k, vv in v.items() if k != "shares"}, "turnover_basis": "OFFICIAL",
                             "sector": meta[t]["sector"], "market": meta[t]["market"],
                             "shares": v["shares"] or shares.get(t)} for t, v in q.items() if t in meta and v["turnover"] is not None}
        n1, n2 = upsert(pan, key_rows, f, "TPEx quotes 官方當日")
        print(f"  [TPEx] 官方個股成交值/收盤/資本額 {len(f)} 檔(新 {n1}/覆 {n2})")
    else:
        print("  [SKIP] TPEx quotes 未達(誠實缺席)")
    t3 = getj("tpex_3insti")
    if t3:
        q = parse_tpex_3insti(t3)
        f = {(v["date"], t): v for t, v in q.items() if t in meta}
        upsert(pan, key_rows, f, "TPEx 3insti 官方當日")
        print(f"  [TPEx] 三大法人買賣超 {len(f)} 檔")
    tm = getj("tpex_margin")
    if tm:
        q = parse_tpex_margin(tm)
        f = {(v["date"], t): v for t, v in q.items() if t in meta}
        upsert(pan, key_rows, f, "TPEx margin 官方當日")
        print(f"  [TPEx] 融資融券餘額 {len(f)} 檔")
    print("  [SKIP] TWSE 個股當沖/三大法人/融資券——雲端 IP 遭 WAF 封鎖(工作站 --ingest 道;誠實缺席)")
    # sector/market 補齊
    for r in pan["rows"]:
        m = meta.get(r["ticker"])
        if m:
            r.setdefault("sector", m["sector"])
            r.setdefault("market", m["market"])
    save_panel(pan)
    print(f"  [面板] {pan['n_rows']} 列 · {pan['n_tickers']} 檔 · {pan['dates'][0]}→{pan['dates'][-1]} · 覆蓋 {pan['coverage']}")
    return 0


def cmd_ingest(path: str) -> int:
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(rows, dict):
        rows = rows.get("rows", [])
    pan = load_panel()
    key_rows = {(r["date"], r["ticker"]): r for r in pan["rows"]}
    f = {(r["date"], r["ticker"]): {k: _f(v) for k, v in r.items() if k not in ("date", "ticker")} for r in rows if r.get("date") and r.get("ticker")}
    n1, n2 = upsert(pan, key_rows, f, f"工作站餵入 {Path(path).name}")
    save_panel(pan)
    print(f"  [餵入] 新 {n1}/覆 {n2} · 面板 {pan['n_rows']} 列")
    return 0


def cmd_run(base: str = "2026-01-01") -> int:
    pan = load_panel()
    if not pan["rows"]:
        print("  [SKIP] 面板空——先 --build(誠實)")
        return 0
    spec = importlib.util.spec_from_file_location("flow_apce", HERE / "FLOW_ENG029_FlowApce.py")
    apce = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(apce)
    eng = apce.APCE()
    eng.resolve_params()
    res = eng.run(pan["rows"], base_date=base)
    apce.OUT_DIR.mkdir(parents=True, exist_ok=True)
    (apce.OUT_DIR / "apce_latest.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [APCE] {res['asof']} · {res['n_tickers']} 檔 · {res['n_dates']} 日 · 分層制 {res['tier_basis']}")
    print(f"  [角色] {res['role_counts']}")
    dl = res["asof"]
    print("  [族群健康 · 指數(2026-01-01=100)eq/tier/att]")
    for sec, hh in sorted(res["health"].items(), key=lambda kv: -(kv[1]["pc1_absorption"] or -1)):
        v = res["indices"][sec].get(dl, {})
        print(f"    {sec:<9} PC1={str(hh['pc1_absorption']):<7} n={hh['n_members']:<3} {hh['index_grade']:<14} "
              f"{v.get('eq')}/{v.get('tier')}/{v.get('att')}")
    sig = [r for r in res["latest"] if r["Signal_Strong_Leader"] or r["Signal_Washout_Buy"] or r["Signal_SITC_Ignition"]]
    print(f"  [訊號] {len(sig)} 檔:" + ", ".join(f"{r['ticker']}({r['sector']}:{r['role']})" for r in sig[:12]))
    print(f"  [出] {apce.OUT_DIR / 'apce_latest.json'}")
    return 0


def selftest() -> int:
    ok, total = 0, 6
    y = json.dumps({"chart": {"result": [{"timestamp": [1767052800, 1767139200],
                    "indicators": {"quote": [{"open": [1, 2], "high": [2, 3], "low": [0.5, 1.5], "close": [1.5, 2.5], "volume": [100, 200]}],
                                   "adjclose": [{"adjclose": [1.4, 2.4]}]}}]}})
    r = parse_yahoo(y, {"ticker": "X", "sector": "S", "market": "TWSE"})
    if len(r) == 2 and r[1]["turnover"] == 500 and r[1]["adj_close"] == 2.4 and r[0]["turnover_basis"] == "PROXY_VOL_X_CLOSE":
        ok += 1; print("  [PASS] Yahoo 解析(還原收盤+成交值代理標記)")
    else:
        print(f"  [FAIL] yahoo:{r}")
    q = parse_twse_day([{"Date": "1150901", "Code": "2330", "ClosingPrice": "2440.00", "TradeValue": "77463413685", "TradeVolume": "31855287"}])
    if q["2330"]["date"] == "2026-09-01" and q["2330"]["turnover"] == 77463413685.0:
        ok += 1; print("  [PASS] TWSE 日成交解析(民國→西元;官方成交值)")
    else:
        print("  [FAIL] twse")
    q = parse_tpex_quotes([{"Date": "1150903", "SecuritiesCompanyCode": "6147", "Close": "100", "TradingShares": "1000", "TransactionAmount": "100000", "Capitals": "1000000000"}])
    if q["6147"]["shares"] == 1e8 and q["6147"]["turnover"] == 100000.0:
        ok += 1; print("  [PASS] TPEx 收盤解析(資本額→股數÷10)")
    else:
        print("  [FAIL] tpex quotes")
    q = parse_tpex_3insti([{"Date": "1150903", "SecuritiesCompanyCode": "6147", K3["f"]: "1,000", K3["s"]: "-200", K3["d"]: "50"}])
    if q["6147"]["f_net"] == 1000 and q["6147"]["s_net"] == -200:
        ok += 1; print("  [PASS] TPEx 三大法人解析(千分位/負值)")
    else:
        print("  [FAIL] 3insti")
    q = parse_tpex_margin([{"Date": "1150903", "SecuritiesCompanyCode": "6147", "MarginPurchaseBalance": "5000", "MarginPurchaseBalancePreviousDay": "4900", "ShortSaleBalance": "300"}])
    if q["6147"]["margin_long_diff"] == 100 and q["6147"]["margin_short"] == 300:
        ok += 1; print("  [PASS] TPEx 融資券解析(餘額差=淨增減)")
    else:
        print("  [FAIL] margin")
    pan = {"rows": [], "provenance": []}
    kr = {}
    upsert(pan, kr, {("2026-01-02", "X"): {"close": 1.0, "turnover": 5.0, "turnover_basis": "PROXY"}}, "a")
    upsert(pan, kr, {("2026-01-02", "X"): {"turnover": 7.0, "turnover_basis": "OFFICIAL", "f_net": None}}, "b")
    if len(pan["rows"]) == 1 and pan["rows"][0]["turnover"] == 7.0 and pan["rows"][0]["close"] == 1.0 and "f_net" not in pan["rows"][0]:
        ok += 1; print("  [PASS] upsert(官方覆蓋代理;None 不覆蓋;去重)")
    else:
        print(f"  [FAIL] upsert:{pan}")
    print(f"  [計] {ok}/{total} 檢通過")
    return 0 if ok == total else 1


def main() -> int:
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if a[0] == "--selftest":
        return selftest()
    if a[0] == "--build":
        return cmd_build()
    if a[0] == "--run":
        return cmd_run(a[a.index("--base") + 1] if "--base" in a else "2026-01-01")
    if a[0] == "--ingest" and len(a) > 1:
        return cmd_ingest(a[1])
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
