#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""flow_tw_baseline — 台股基準動態參數引擎(批308)
====================================================================
操作員令(批308):「如何降低台股大盤連動:台股成交值扣除台積電及
當沖交易影響作為基準動態參數,分大中小型股;外資主導還是內資主導」。

降低大盤連動方法論(明文,零發明):
  ① 基準面:TAIEX 與總成交值皆被台積電權重+當沖回轉腿灌水——
     基準成交值 B_t = (TWSE 成交值+TPEx 成交值) − 台積電成交值
                      − 當沖影響值(當沖買進+賣出)/2(半沖計=回轉雙腿摺半)
  ② 動態參數律(循宏觀 v2 權重鐵律):閾值/位階全由資料算出——
     B_z = (B_t − 滾動均) / 滾動標準差;B_pct = 滾動百分位;視窗=min(n,60)
     樣本 < 8 誠實不出參數。零固定閾值。
  ③ 分層面:個股市值 = 已發行普通股數(t187ap03_L 官方)× 收盤價——
     大型=市值排名前 50、中型=51–150、小型=其餘(循臺灣50/中型100
     官方指數構成法);逐層成交值占比+門檻市值每日重算(動態)。
  ④ 主導判定:外資參與率 f_t = (外資買+外資賣)/(2×成交值);
     f_t > 自身滾動中位數 ⇒ FOREIGN_LED,否則 DOMESTIC_LED;
     附外資淨額方向。中位數=算出非設定。
  ⑤ 去連動評估:corr(ΔTAIEX, Δ總成交值) vs corr(ΔTAIEX, ΔB_t) 併列
     ——B 對大盤相關降幅即為證;個股再以 r_i − β_i·r_TAIEX(β 滾動)
     取殘差比較(β 中和式列印;本引擎出基準,殘差歸下游)。

資料道(官方 OpenAPI;同意閘;雲端 WAF 封鎖之集=工作站側車):
  TWSE FMTQIK(大盤成交值+TAIEX)· STOCK_DAY_ALL(個股成交值/收盤;
  台積電 2330 抽值)· t187ap03_L(發行股數)——實連可達
  TPEx daily_trading_index+intraday_trading_statistics(上櫃當沖)
  +3insti_summary(上櫃三大法人)——實連可達
  TWSE 當沖統計(TWTB4U)+三大法人(T86/BFI82U)——雲端 IP 遭官方
  WAF 封鎖(工作站實測 2026-09-02);--ingest 工作站列餵入,誠實缺席
用法:
  --fetch            實連累積當日快照(同意閘)入側車庫
  --ingest <json>    工作站列餵入(rows:date,twse_dt_buy,twse_dt_sell,
                     twse_foreign_buy,twse_foreign_sell …)併庫去重
  --report           基準+分層+主導+去連動評估(全式列印)
  --selftest         八檢(合成沙盒零網路)
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

import json
import math
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DB_PATH = ROOT / "data" / "input" / "tw_baseline_db.json"
TIER_PATH = ROOT / "data" / "output" / "tw_cap_tiers.json"
OUT_PATH = ROOT / "data" / "output" / "tw_baseline_report.json"
NOW = datetime.now().strftime("%Y-%m-%d %H:%M")

ENDPOINTS = {
    "twse_fmtqik": "https://openapi.twse.com.tw/v1/exchangeReport/FMTQIK",
    "twse_stock_day": "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL",
    "twse_registry": "https://openapi.twse.com.tw/v1/opendata/t187ap03_L",
    "tpex_index": "https://www.tpex.org.tw/openapi/v1/tpex_daily_trading_index",
    "tpex_daytrade": "https://www.tpex.org.tw/openapi/v1/tpex_intraday_trading_statistics",
    "tpex_3insti": "https://www.tpex.org.tw/openapi/v1/tpex_3insti_summary",
    # 雲端 WAF 封鎖冊(工作站道;此地誠實 SKIP):
    "twse_daytrade_ws": "https://www.twse.com.tw/rwd/zh/afterTrading/TWTB4U?response=json",
    "twse_3insti_ws": "https://www.twse.com.tw/rwd/zh/afterTrading/BFI82U?response=json",
}
TSMC = "2330"
TIER_RULE = {"LARGE": 50, "MID": 150}  # 排名門檻(市值門檻值每日算出)


def _f(x) -> float | None:
    try:
        return float(str(x).replace(",", ""))
    except (TypeError, ValueError):
        return None


def _roc_to_iso(d: str) -> str:
    """民國 1150901 → 2026-09-01(非民國制原樣回)。"""
    s = str(d).strip()
    if len(s) == 7 and s.isdigit():
        return f"{int(s[:3]) + 1911}-{s[3:5]}-{s[5:7]}"
    return s


def load_db() -> dict:
    if DB_PATH.exists():
        return json.loads(DB_PATH.read_text(encoding="utf-8"))
    return {"schema": "tw-baseline-db-v1", "rows": []}


def save_db(db: dict):
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    DB_PATH.write_text(json.dumps(db, ensure_ascii=False, indent=1), encoding="utf-8")


def upsert(db: dict, date: str, **fields):
    for r in db["rows"]:
        if r.get("date") == date:
            for k, v in fields.items():
                if v is not None:
                    r[k] = v
            return
    db["rows"].append({"date": date, **{k: v for k, v in fields.items() if v is not None}})


# ─────────────────────────── 核心算式 ───────────────────────────

def compute_baseline(row: dict) -> dict:
    """B = (TWSE+TPEx 成交值) − 台積電 − 當沖影響(買+賣)/2;缺件誠實列名。"""
    twse_v, tpex_v = row.get("twse_value"), row.get("tpex_value")
    tsmc_v = row.get("tsmc_value")
    missing = [k for k, v in (("twse_value", twse_v), ("tsmc_value", tsmc_v)) if v is None]
    total = (twse_v or 0) + (tpex_v or 0)
    dt_legs, dt_missing = 0.0, []
    for mkt in ("twse", "tpex"):
        b, s = row.get(f"{mkt}_dt_buy"), row.get(f"{mkt}_dt_sell")
        if b is None and s is None:
            dt_missing.append(mkt)
        else:
            dt_legs += ((b or 0) + (s or 0)) / 2  # 半沖計
    if missing:
        return {"baseline": None, "note": "缺件誠實不算:" + ",".join(missing)}
    base = total - tsmc_v - dt_legs
    out = {"turnover_total": total, "tsmc_value": tsmc_v, "dt_value": round(dt_legs, 0),
           "baseline": round(base, 0),
           "tsmc_share": round(tsmc_v / total, 4) if total else None,
           "dt_share": round(dt_legs / total, 4) if total else None}
    if tpex_v is None:
        out["note"] = "TPEx 成交值缺——基準=僅 TWSE 側(誠實記)"
    if dt_missing:
        out["dt_coverage"] = "當沖僅蓋:" + ",".join(m for m in ("twse", "tpex")
                                                if m not in dt_missing) or "無"
    return out


def dyn_params(vals: list[float], window: int = 60) -> dict:
    """動態參數律:z+百分位,視窗=min(n,window);n<8 誠實不出。"""
    n = len(vals)
    if n < 8:
        return {"verdict": "樣本不足", "n": n, "need": 8}
    w = vals[-min(n, window):]
    m = sum(w) / len(w)
    sd = math.sqrt(sum((v - m) ** 2 for v in w) / len(w)) or 1e-9
    cur = vals[-1]
    pct = sum(1 for v in w if v <= cur) / len(w)
    return {"window": len(w), "mean": round(m, 0), "sd": round(sd, 0),
            "z": round((cur - m) / sd, 2), "pct": round(pct, 3)}


def compute_tiers(stocks: list[dict], shares: dict[str, float]) -> dict:
    """市值=股數×收盤;排名分層(前50/51-150/其餘);門檻市值輸出=動態。"""
    rows = []
    n_noshare = 0
    for s in stocks:
        code, close, tv = s.get("Code"), _f(s.get("ClosingPrice")), _f(s.get("TradeValue"))
        sh = shares.get(code)
        if not code or close is None:
            continue
        if sh is None:
            n_noshare += 1  # ETF/非普通股名錄外——分層誠實不含
            continue
        rows.append({"code": code, "name": s.get("Name", ""), "cap": sh * close,
                     "value": tv or 0.0})
    rows.sort(key=lambda r: -r["cap"])
    for i, r in enumerate(rows):
        r["rank"] = i + 1
        r["tier"] = ("LARGE" if i < TIER_RULE["LARGE"]
                     else "MID" if i < TIER_RULE["MID"] else "SMALL")
    agg = {t: {"n": 0, "value": 0.0, "cap": 0.0} for t in ("LARGE", "MID", "SMALL")}
    for r in rows:
        a = agg[r["tier"]]
        a["n"] += 1
        a["value"] += r["value"]
        a["cap"] += r["cap"]
    tot_v = sum(a["value"] for a in agg.values()) or 1e-9
    for a in agg.values():
        a["value_share"] = round(a["value"] / tot_v, 4)
        a["value"] = round(a["value"], 0)
        a["cap"] = round(a["cap"], 0)
    thresholds = {"LARGE_min_cap": rows[TIER_RULE["LARGE"] - 1]["cap"]
                  if len(rows) >= TIER_RULE["LARGE"] else None,
                  "MID_min_cap": rows[TIER_RULE["MID"] - 1]["cap"]
                  if len(rows) >= TIER_RULE["MID"] else None}
    return {"tiers": agg, "thresholds_dynamic": thresholds, "n_ranked": len(rows),
            "n_excluded_no_shares": n_noshare, "top": rows[:5]}


def compute_dominance(rows: list[dict], mkt: str) -> dict:
    """外資參與率 f=(買+賣)/(2×成交值);f>自身滾動中位數 ⇒ FOREIGN_LED。"""
    hist = []
    for r in rows:
        fb, fs = r.get(f"{mkt}_foreign_buy"), r.get(f"{mkt}_foreign_sell")
        tv = r.get(f"{mkt}_value")
        if None in (fb, fs, tv) or not tv:
            continue
        hist.append({"date": r["date"], "f": (fb + fs) / (2 * tv), "net": fb - fs})
    if not hist:
        return {"verdict": "樣本不足(無法人×成交值同日列)", "n": 0}
    fs_ = sorted(h["f"] for h in hist)
    med = fs_[len(fs_) // 2]
    cur = hist[-1]
    led = "FOREIGN_LED" if cur["f"] > med else "DOMESTIC_LED"
    return {"date": cur["date"], "foreign_participation": round(cur["f"], 4),
            "rolling_median": round(med, 4), "n": len(hist), "verdict": led,
            "foreign_net": round(cur["net"], 0),
            "net_direction": "外資淨買" if cur["net"] > 0 else "外資淨賣" if cur["net"] < 0 else "持平"}


def _corr(x: list, y: list) -> float:
    n = min(len(x), len(y))
    if n < 3:
        return 0.0
    x, y = x[-n:], y[-n:]
    mx, my = sum(x) / n, sum(y) / n
    sx = math.sqrt(sum((v - mx) ** 2 for v in x)) or 1e-12
    sy = math.sqrt(sum((v - my) ** 2 for v in y)) or 1e-12
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy)


def compute_decouple(rows: list[dict]) -> dict:
    """去連動評估:corr(ΔTAIEX, Δ總值) vs corr(ΔTAIEX, ΔB);n<8 誠實不算。"""
    seq = [r for r in sorted(rows, key=lambda r: r["date"])
           if r.get("taiex") is not None and compute_baseline(r).get("baseline") is not None]
    if len(seq) < 8:
        return {"verdict": "樣本不足", "n": len(seq), "need": 8,
                "formula": "corr(ΔTAIEX,Δ總成交值) vs corr(ΔTAIEX,ΔB);β中和:r_i−β_i·r_TAIEX(β=滾動迴歸)"}
    d_tx, d_tot, d_base = [], [], []
    prev = None
    for r in seq:
        b = compute_baseline(r)
        if prev is not None:
            pb = compute_baseline(prev)
            d_tx.append(r["taiex"] - prev["taiex"])
            d_tot.append(b["turnover_total"] - pb["turnover_total"])
            d_base.append(b["baseline"] - pb["baseline"])
        prev = r
    c_tot, c_base = _corr(d_tx, d_tot), _corr(d_tx, d_base)
    return {"n": len(seq), "corr_taiex_turnover": round(c_tot, 4),
            "corr_taiex_baseline": round(c_base, 4),
            "decoupling_gain": round(abs(c_tot) - abs(c_base), 4),
            "verdict": "基準較總值去連動" if abs(c_base) < abs(c_tot) else "無降幅(誠實記)"}


# ─────────────────────────── 命令 ───────────────────────────

def cmd_fetch() -> int:
    if VIA_ACCEL is None:
        print("  [SKIP] SuperAccel 未載——無網路道(誠實)")
        return 0
    db = load_db()

    def get_json(key, timeout=45):
        raw = VIA_ACCEL.fetch(ENDPOINTS[key], timeout=timeout, cache=False)
        if not raw:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return None

    fm = get_json("twse_fmtqik")
    if fm:
        r = fm[-1]
        upsert(db, _roc_to_iso(r.get("Date")), twse_value=_f(r.get("TradeValue")),
               taiex=_f(r.get("TAIEX")), taiex_chg=_f(r.get("Change")))
        print(f"  [OK] TWSE FMTQIK — {_roc_to_iso(r.get('Date'))} 成交值 {_f(r.get('TradeValue')):,.0f}")
    else:
        print("  [SKIP] TWSE FMTQIK 未達(誠實缺席)")
    sd = get_json("twse_stock_day", timeout=60)
    if sd:
        date = _roc_to_iso(sd[0].get("Date")) if sd else None
        tsmc = next((s for s in sd if s.get("Code") == TSMC), None)
        if date and tsmc:
            upsert(db, date, tsmc_value=_f(tsmc.get("TradeValue")),
                   tsmc_close=_f(tsmc.get("ClosingPrice")))
            print(f"  [OK] TWSE STOCK_DAY_ALL — {len(sd)} 檔;台積電成交值 {_f(tsmc.get('TradeValue')):,.0f}")
        (ROOT / "data" / "input").mkdir(parents=True, exist_ok=True)
        (ROOT / "data" / "input" / "twse_stock_day_last.json").write_text(
            json.dumps(sd, ensure_ascii=False), encoding="utf-8")
    else:
        print("  [SKIP] TWSE STOCK_DAY_ALL 未達(誠實缺席)")
    reg = get_json("twse_registry", timeout=90)
    if reg:
        shares = {}
        for r in reg:
            sh = _f(r.get("已發行普通股數或TDR原股發行股數"))
            if r.get("公司代號") and sh:
                shares[r["公司代號"]] = sh
        (ROOT / "data" / "input" / "twse_shares_last.json").write_text(
            json.dumps(shares, ensure_ascii=False), encoding="utf-8")
        print(f"  [OK] TWSE t187ap03_L — 發行股數 {len(shares)} 檔(gzip 道)")
    else:
        print("  [SKIP] TWSE t187ap03_L 未達(誠實缺席)")
    ti = get_json("tpex_index")
    if ti:
        r = ti[-1]
        upsert(db, _roc_to_iso(r.get("Date")), tpex_value=_f(r.get("TradeAmount")),
               tpex_index=_f(r.get("TPExIndex")))
        print(f"  [OK] TPEx 日成交量值 — 成交值 {_f(r.get('TradeAmount')):,.0f}")
    else:
        print("  [SKIP] TPEx 日成交量值未達(誠實缺席)")
    td = get_json("tpex_daytrade")
    if td:
        r = td[-1]
        upsert(db, _roc_to_iso(r.get("Date")),
               tpex_dt_buy=_f(r.get("DayTradingValueOfBuys")),
               tpex_dt_sell=_f(r.get("DayTradingValueOfSells")))
        print("  [OK] TPEx 當沖統計 — 買賣兩腿收錄")
    else:
        print("  [SKIP] TPEx 當沖統計未達(誠實缺席)")
    t3 = get_json("tpex_3insti")
    if t3:
        fr = next((r for r in t3 if "外資及陸資合計" in str(r.get("Investor", ""))), None)
        if fr:
            upsert(db, _roc_to_iso(fr.get("Date")),
                   tpex_foreign_buy=_f(fr.get("PurchaseAmount")),
                   tpex_foreign_sell=_f(fr.get("SaleAmount")))
            print("  [OK] TPEx 三大法人 — 外資買賣金額收錄")
    else:
        print("  [SKIP] TPEx 三大法人未達(誠實缺席)")
    for k in ("twse_daytrade_ws", "twse_3insti_ws"):
        raw = VIA_ACCEL.fetch(ENDPOINTS[k], timeout=20, cache=False)
        got = None
        if raw:
            try:
                got = json.loads(raw)  # 官網 HTML 殼/導頁≠資料——JSON 驗身才算收
            except Exception:
                got = None
        if isinstance(got, dict) and got.get("data"):
            (ROOT / "data" / "input" / f"{k}_last.json").write_text(raw, encoding="utf-8")
            print(f"  [收] {k} 可達——原始檔落庫候解析(工作站冊)")
        else:
            print(f"  [SKIP] {k} — 雲端道無資料體(WAF/導頁;工作站波餵入;誠實缺席)")
    save_db(db)
    print(f"  [庫] {len(db['rows'])} 日列(側車 {DB_PATH.name})")
    return 0


def cmd_ingest(path: str) -> int:
    p = Path(path)
    if not p.exists():
        print(f"  [FAIL] 檔不存在:{path}")
        return 2
    rows = json.loads(p.read_text(encoding="utf-8"))
    if isinstance(rows, dict):
        rows = rows.get("rows", [])
    db = load_db()
    n = 0
    for r in rows:
        if r.get("date"):
            upsert(db, r["date"], **{k: _f(v) for k, v in r.items() if k != "date"})
            n += 1
    save_db(db)
    print(f"  [餵入] {n} 列(工作站道)· 庫 {len(db['rows'])} 日列")
    return 0


def cmd_report() -> int:
    db = load_db()
    rows = sorted(db["rows"], key=lambda r: r["date"])
    if not rows:
        print("  [SKIP] 庫空——先 --fetch 或 --ingest(誠實)")
        return 0
    cur = rows[-1]
    b = compute_baseline(cur)
    print(f"  ═ 基準動態參數({cur['date']})═")
    if b.get("baseline") is None:
        print(f"    {b['note']}")
    else:
        print(f"    總成交值 {b['turnover_total']:,.0f} − 台積電 {b['tsmc_value']:,.0f}"
              f"(占 {b['tsmc_share']:.1%})− 當沖 {b['dt_value']:,.0f}"
              f"(占 {b['dt_share']:.1%})")
        print(f"    基準 B = {b['baseline']:,.0f}")
        if b.get("note"):
            print(f"    [註] {b['note']}")
        if b.get("dt_coverage"):
            print(f"    [註] {b['dt_coverage']}(TWSE 當沖候工作站餵入)")
        hist = [compute_baseline(r).get("baseline") for r in rows]
        hist = [h for h in hist if h is not None]
        dp = dyn_params(hist)
        print(f"    動態參數:{dp}")
    tiers = None
    sd_p = ROOT / "data" / "input" / "twse_stock_day_last.json"
    sh_p = ROOT / "data" / "input" / "twse_shares_last.json"
    if sd_p.exists() and sh_p.exists():
        tiers = compute_tiers(json.loads(sd_p.read_text(encoding="utf-8")),
                              json.loads(sh_p.read_text(encoding="utf-8")))
        print(f"  ═ 大中小型分層(市值=官方股數×收盤;排名 50/150 制)═")
        for t in ("LARGE", "MID", "SMALL"):
            a = tiers["tiers"][t]
            print(f"    {t:<6} {a['n']:>4} 檔 · 成交值占 {a['value_share']:.1%}")
        th = tiers["thresholds_dynamic"]
        print(f"    門檻市值(動態):大型 ≥{th['LARGE_min_cap']:,.0f} · 中型 ≥{th['MID_min_cap']:,.0f}")
        print(f"    [誠實] 名錄外(ETF 等)不分層 {tiers['n_excluded_no_shares']} 檔")
    else:
        print("  ═ 大中小型分層 ═\n    [SKIP] 個股/股數快照缺——先 --fetch")
    print("  ═ 外資/內資主導 ═")
    for mkt, label in (("twse", "TWSE(候工作站 T86/BFI82U 餵入)"), ("tpex", "TPEx")):
        d = compute_dominance(rows, mkt)
        if d.get("n"):
            print(f"    {label}:{d['verdict']} · 參與率 {d['foreign_participation']:.1%}"
                  f"(中位 {d['rolling_median']:.1%})· {d['net_direction']}"
                  f" {abs(d['foreign_net']):,.0f}")
        else:
            print(f"    {label}:{d['verdict']}")
    dec = compute_decouple(rows)
    print(f"  ═ 去連動評估 ═\n    {dec}")
    out = {"ts": NOW, "date": cur["date"], "baseline": b, "tiers": tiers,
           "dominance": {m: compute_dominance(rows, m) for m in ("twse", "tpex")},
           "decouple": dec,
           "methodology": ["B=(TWSE+TPEx成交值)−台積電−當沖(買+賣)/2",
                           "動態參數:z+百分位(滾動視窗;零固定閾值)",
                           "分層:市值排名 前50/51-150/其餘(門檻每日重算)",
                           "主導:外資參與率>自身滾動中位數 ⇒ FOREIGN_LED",
                           "去連動:corr(ΔTAIEX,Δ總值) vs corr(ΔTAIEX,ΔB);下游 β 中和 r_i−β_i·r_TAIEX"]}
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    if tiers:
        TIER_PATH.write_text(json.dumps(tiers, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [出] {OUT_PATH.name}" + (f" + {TIER_PATH.name}" if tiers else ""))
    return 0


def selftest() -> int:
    ok, total = 0, 8
    # ① 基準式(半沖計)
    r = compute_baseline({"twse_value": 1000.0, "tpex_value": 200.0, "tsmc_value": 300.0,
                          "twse_dt_buy": 100.0, "twse_dt_sell": 100.0,
                          "tpex_dt_buy": 20.0, "tpex_dt_sell": 20.0})
    if r["baseline"] == 1000 + 200 - 300 - 120 and r["dt_value"] == 120:
        ok += 1; print("  [PASS] 基準式 B=總−台積電−當沖(買+賣)/2")
    else:
        print(f"  [FAIL] 基準式:{r}")
    # ② 缺件誠實
    r = compute_baseline({"twse_value": 1000.0})
    if r["baseline"] is None and "tsmc_value" in r["note"]:
        ok += 1; print("  [PASS] 缺件誠實不算(列名)")
    else:
        print(f"  [FAIL] 缺件:{r}")
    # ③ 當沖覆蓋註記
    r = compute_baseline({"twse_value": 1000.0, "tsmc_value": 300.0,
                          "tpex_dt_buy": 20.0, "tpex_dt_sell": 20.0})
    if r["baseline"] == 680 and "tpex" in r.get("dt_coverage", ""):
        ok += 1; print("  [PASS] 當沖覆蓋註記(僅蓋 tpex 誠實記)")
    else:
        print(f"  [FAIL] 覆蓋:{r}")
    # ④ 動態參數律(樣本閘+z)
    d1 = dyn_params([1, 2, 3])
    d2 = dyn_params([100.0] * 9 + [130.0])
    if d1.get("verdict") == "樣本不足" and d2["z"] > 2 and d2["pct"] == 1.0:
        ok += 1; print("  [PASS] 動態參數(n<8 誠實;z/百分位算出非設定)")
    else:
        print(f"  [FAIL] 參數:{d1}/{d2}")
    # ⑤ 分層(排名制+名錄外剔除)
    stocks = [{"Code": f"C{i:03d}", "Name": f"s{i}", "ClosingPrice": "10",
               "TradeValue": "100"} for i in range(200)]
    shares = {f"C{i:03d}": 1000.0 * (200 - i) for i in range(180)}  # 20 檔名錄外
    t = compute_tiers(stocks, shares)
    if (t["tiers"]["LARGE"]["n"], t["tiers"]["MID"]["n"], t["tiers"]["SMALL"]["n"],
            t["n_excluded_no_shares"]) == (50, 100, 30, 20):
        ok += 1; print("  [PASS] 分層 50/100/其餘+名錄外誠實剔除")
    else:
        print(f"  [FAIL] 分層:{ {k: v['n'] for k, v in t['tiers'].items()} }")
    # ⑥ 門檻動態輸出
    if t["thresholds_dynamic"]["LARGE_min_cap"] == 1000.0 * (200 - 49) * 10:
        ok += 1; print("  [PASS] 門檻市值=算出(第50名市值,非設定)")
    else:
        print(f"  [FAIL] 門檻:{t['thresholds_dynamic']}")
    # ⑦ 主導判定(中位數律)
    rows = [{"date": f"D{i}", "tpex_value": 100.0, "tpex_foreign_buy": 20.0 + i,
             "tpex_foreign_sell": 20.0} for i in range(9)]
    d = compute_dominance(rows, "tpex")
    if d["verdict"] == "FOREIGN_LED" and d["net_direction"] == "外資淨買":
        ok += 1; print("  [PASS] 主導判定(參與率>滾動中位 ⇒ FOREIGN_LED+淨向)")
    else:
        print(f"  [FAIL] 主導:{d}")
    # ⑧ 去連動評估(構造:TAIEX 隨台積電動、基準獨立)
    rows = []
    for i in range(15):
        tsmc = 300.0 + (40.0 if i % 2 else -40.0)   # 台積電值震盪
        base_part = 700.0 + i * 2                    # 基準面平穩趨勢
        rows.append({"date": f"D{i:02d}", "taiex": 20000 + (80 if i % 2 else -80) + i,
                     "twse_value": tsmc + base_part, "tsmc_value": tsmc})
    dec = compute_decouple(rows)
    if dec.get("decoupling_gain", -1) > 0.3 and dec["verdict"] == "基準較總值去連動":
        ok += 1; print(f"  [PASS] 去連動評估(降幅 {dec['decoupling_gain']} 可證)")
    else:
        print(f"  [FAIL] 去連動:{dec}")
    print(f"  [計] {ok}/{total} 檢通過")
    return 0 if ok == total else 1


def main() -> int:
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if a[0] == "--selftest":
        return selftest()
    if a[0] == "--fetch":
        return cmd_fetch()
    if a[0] == "--ingest" and len(a) > 1:
        return cmd_ingest(a[1])
    if a[0] == "--report":
        return cmd_report()
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
