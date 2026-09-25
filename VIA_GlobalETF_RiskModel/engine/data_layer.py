# -*- coding: utf-8 -*-
"""
data_layer.py — M10_DataForge：資料載入與 T4 合成示範世界
=============================================================================
MODULE M10_DataForge
  [MCFL-M10-C11-F101] load_config / load_json      — SSOT 與資料檔載入
  [MCFL-M10-C11-F102] load_csv_wide                — 寬表 CSV（date + tickers）
  [MCFL-M10-C12-F110] DemoWorld.generate           — regime 腳本化合成市場
真值階梯：
  demo 產生的一切皆為 T4 SYNTHETIC，僅供管線驗證，provenance 全程掛
  data_source=synthetic_demo / evidence=Est。真實資料請用 --prices/--macro CSV
  （T3 價量估算層），或接 MDL008 (VIA_GlobalETFFlow) 的 T1 真流輸出。
治理：只讀來源、不寫回 canonical；輸出一律 UTF-8 (No BOM)。
"""
from __future__ import annotations

import csv
import datetime as _dt
import json
import math
import random
from pathlib import Path

MODULE_ROOT = Path(__file__).resolve().parents[1]


# --------------------------------------------------------------------------- #
# 載入器
# --------------------------------------------------------------------------- #

def load_json(path):
    """[MCFL-M10-C11-F101]"""
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_config(path=None):
    path = Path(path) if path else MODULE_ROOT / "config" / "global_etf_risk_config.json"
    return load_json(path)


def universe_tickers(config):
    out = []
    for group, members in config["def_etf_universe"].items():
        for m in members:
            out.append({"ticker": m["ticker"], "name": m["name"], "group": group,
                        "region": m["region"], "haven_level": m["haven_level"]})
    return out


class MarketData:
    """對齊後的市場資料容器。prices/macro 皆為與 dates 等長的 list[float|None]。"""

    def __init__(self, dates, prices, macro, provenance):
        self.dates = dates
        self.prices = prices
        self.macro = macro
        self.provenance = provenance

    @property
    def asof(self):
        return self.dates[-1] if self.dates else None

    def has(self, ticker):
        return ticker in self.prices or ticker in self.macro

    def series(self, key):
        if key in self.prices:
            return self.prices[key]
        return self.macro.get(key)


def _ffill(values):
    out, last = [], None
    for v in values:
        if v is not None:
            last = v
        out.append(last)
    return out


def load_csv_wide(prices_csv, macro_csv=None, macro_series=None):
    """寬表 CSV：第一欄 date（YYYY-MM-DD 升冪），其餘欄名=ticker/序列名。
    空值向前補。 [MCFL-M10-C11-F102]"""
    def read(path):
        with open(path, "r", encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.reader(fh))
        header = [h.strip() for h in rows[0]]
        cols = {h: [] for h in header[1:]}
        dates = []
        for row in rows[1:]:
            if not row or not row[0].strip():
                continue
            dates.append(row[0].strip())
            for i, h in enumerate(header[1:], start=1):
                raw = row[i].strip() if i < len(row) else ""
                val = None
                if raw:
                    try:
                        v = float(raw)
                        # NaN/inf 一律視為缺值：不得穿透進窗口計算
                        val = v if math.isfinite(v) else None
                    except ValueError:
                        val = None
                cols[h].append(val)
        for i in range(len(dates) - 1):
            if dates[i] >= dates[i + 1]:
                raise ValueError(
                    "CSV 日期需嚴格升冪且不重複（%s：第 %d 列 %s >= %s）"
                    % (path, i + 2, dates[i], dates[i + 1]))
        return dates, {k: _ffill(v) for k, v in cols.items()}

    dates, prices = read(prices_csv)
    macro = {}
    if macro_csv:
        mdates, mcols = read(macro_csv)
        if mdates == dates:
            macro = mcols
        else:
            # 以 prices 日期軸為準，對 macro 做 as-of 對齊（往前取最近值）
            for name, vals in mcols.items():
                aligned, j = [], -1
                for d in dates:
                    while j + 1 < len(mdates) and mdates[j + 1] <= d:
                        j += 1
                    aligned.append(vals[j] if j >= 0 else None)
                macro[name] = _ffill(aligned)
    if macro_series:
        missing = [s for s in macro_series if s not in macro]
        if missing:
            raise ValueError("macro CSV 缺少序列: %s" % ", ".join(missing))
    provenance = {
        "data_source": "csv",
        "truth_tier": "T3",
        "evidence": "Est",
        "note": "價量估算層：分數/輪動/同步皆由價格推導，非 T1 真流",
        "prices_csv": str(prices_csv),
        "macro_csv": str(macro_csv) if macro_csv else None,
    }
    return MarketData(dates, prices, macro, provenance)


# --------------------------------------------------------------------------- #
# T4 合成示範世界（僅供管線驗證）
# --------------------------------------------------------------------------- #

# regime 腳本：(id, 起點比例, 終點比例)
DEMO_REGIME_SCRIPT = [
    ("risk_on_global_reflation", 0.00, 0.25),
    ("rate_shock",               0.25, 0.45),
    ("usd_squeeze",              0.45, 0.63),
    ("growth_scare",             0.63, 0.79),
    ("ai_concentration_boom",    0.79, 1.00),
]

# 因子日參數 (mu, sigma)：g 全球股、u 美元、r Δ10Y(pp)、c 信用壓力、
# m 商品、ai 集中化、cn 中國
DEMO_FACTOR_PARAMS = {
    "risk_on_global_reflation": {"g": (0.0009, 0.008), "u": (-0.0004, 0.003),
                                 "r": (0.002, 0.030),  "c": (-0.0005, 0.0015),
                                 "m": (0.0012, 0.010), "ai": (0.0002, 0.003),
                                 "cn": (0.0005, 0.006)},
    "rate_shock":                {"g": (-0.0005, 0.011), "u": (0.0005, 0.0035),
                                 "r": (0.010, 0.040),   "c": (0.0006, 0.0025),
                                 "m": (0.0002, 0.010),  "ai": (-0.0005, 0.004),
                                 "cn": (-0.0005, 0.007)},
    "usd_squeeze":               {"g": (-0.0003, 0.010), "u": (0.0012, 0.0035),
                                 "r": (0.001, 0.030),   "c": (0.0010, 0.0030),
                                 "m": (-0.0006, 0.010), "ai": (0.0000, 0.0035),
                                 "cn": (-0.0012, 0.008)},
    "growth_scare":              {"g": (-0.0012, 0.013), "u": (0.0002, 0.003),
                                 "r": (-0.012, 0.040),  "c": (0.0014, 0.0035),
                                 "m": (-0.0015, 0.011), "ai": (-0.0002, 0.004),
                                 "cn": (-0.0006, 0.008)},
    "ai_concentration_boom":     {"g": (0.0007, 0.0075), "u": (0.0002, 0.0028),
                                 "r": (0.003, 0.025),   "c": (-0.0004, 0.0012),
                                 "m": (0.0000, 0.009),  "ai": (0.0022, 0.0040),
                                 "cn": (0.0002, 0.006)},
}

# 每檔 ETF 的因子曝險（缺者用 0）；idio=殘差日波動、drift=額外日漂移
DEMO_LOADINGS = {
    "VT":   {"g": 0.97, "u": -0.12, "ai": 0.10, "idio": 0.0018},
    "ACWI": {"g": 0.95, "u": -0.15, "ai": 0.08, "idio": 0.0015},
    "ACWX": {"g": 0.90, "u": -0.45, "ai": -0.05, "idio": 0.0025},
    "SPY":  {"g": 1.00, "ai": 0.15, "r_eq": -0.04, "idio": 0.0030},
    "QQQ":  {"g": 1.10, "ai": 0.55, "r_eq": -0.08, "idio": 0.0040},
    "IWM":  {"g": 1.05, "ai": -0.35, "c": -0.8, "r_eq": -0.05, "idio": 0.0050},
    "RSP":  {"g": 0.95, "ai": -0.28, "idio": 0.0030},
    "SMH":  {"g": 1.15, "ai": 0.90, "r_eq": -0.07, "idio": 0.0060},
    "EFA":  {"g": 0.90, "u": -0.45, "idio": 0.0035},
    "VEA":  {"g": 0.90, "u": -0.45, "idio": 0.0035},
    "VGK":  {"g": 0.92, "u": -0.50, "idio": 0.0040},
    "EZU":  {"g": 0.95, "u": -0.55, "idio": 0.0045},
    "EWJ":  {"g": 0.85, "u": -0.30, "ai": 0.10, "idio": 0.0050},
    "EWU":  {"g": 0.85, "u": -0.40, "m": 0.10, "idio": 0.0045},
    "EWG":  {"g": 0.95, "u": -0.50, "m": 0.05, "idio": 0.0050},
    "EWQ":  {"g": 0.90, "u": -0.50, "idio": 0.0050},
    "EEM":  {"g": 0.95, "u": -0.90, "cn": 0.35, "m": 0.15, "c": -0.5, "idio": 0.0045},
    "VWO":  {"g": 0.93, "u": -0.88, "cn": 0.35, "m": 0.15, "c": -0.5, "idio": 0.0045},
    "MCHI": {"g": 0.70, "u": -0.50, "cn": 1.00, "idio": 0.0070},
    "FXI":  {"g": 0.68, "u": -0.50, "cn": 1.05, "idio": 0.0075},
    "ASHR": {"g": 0.55, "u": -0.35, "cn": 0.90, "idio": 0.0090},
    "INDA": {"g": 0.85, "u": -0.60, "m": -0.25, "idio": 0.0060},
    "EWT":  {"g": 0.95, "u": -0.50, "ai": 0.75, "cn": 0.15, "idio": 0.0060},
    "EWY":  {"g": 0.95, "u": -0.60, "ai": 0.55, "cn": 0.30, "idio": 0.0065},
    "EWZ":  {"g": 0.85, "u": -0.90, "m": 0.50, "cn": 0.25, "idio": 0.0090},
    "EWW":  {"g": 0.80, "u": -0.70, "m": 0.20, "idio": 0.0080},
    "EWS":  {"g": 0.80, "u": -0.50, "cn": 0.25, "idio": 0.0050},
    "EIDO": {"g": 0.80, "u": -0.80, "m": 0.30, "cn": 0.20, "idio": 0.0080},
    "LQD":  {"ief": 0.85, "c": -0.9, "idio": 0.0012},
    "HYG":  {"ief": 0.30, "c": -1.8, "g": 0.25, "idio": 0.0015},
    "JNK":  {"ief": 0.30, "c": -1.8, "g": 0.25, "idio": 0.0018},
    "EMB":  {"ief": 0.55, "c": -1.4, "u": -0.50, "cn": 0.10, "idio": 0.0018},
    "EMLC": {"ief": 0.30, "c": -1.0, "u": -1.30, "m": 0.15, "idio": 0.0025},
    "GLD":  {"real": -6.5, "u": -0.60, "m": 0.15, "c": 0.2, "idio": 0.0070},
    "SLV":  {"real": -4.0, "u": -0.50, "m": 0.50, "idio": 0.0110},
    "USO":  {"m": 1.50, "idio": 0.0120},
    "BNO":  {"m": 1.45, "idio": 0.0110},
    "CPER": {"m": 0.90, "cn": 0.45, "g": 0.25, "idio": 0.0090},
    "DBC":  {"m": 1.00, "cn": 0.10, "idio": 0.0050},
    "DBA":  {"m": 0.35, "idio": 0.0060},
    "UUP":  {"u": 1.00, "idio": 0.0012},
    "FXE":  {"u": -0.85, "idio": 0.0020},
    "FXY":  {"u": -0.60, "g": -0.25, "idio": 0.0030},
    "FXB":  {"u": -0.70, "idio": 0.0025},
    "VNQ":  {"g": 0.75, "r_dur": -8.0, "c": -0.6, "idio": 0.0050},
    "IBIT": {"g": 1.20, "u": -1.20, "idio": 0.0200},
}

DEMO_DURATION = {"BIL": 0.08, "SGOV": 0.08, "SHY": 1.9, "IEI": 4.5,
                 "IEF": 7.5, "TLT": 17.5}
DEMO_TIP_DURATION = 7.0

DEMO_START_PRICE = {
    "VT": 130.0, "ACWI": 130.0, "ACWX": 62.0, "SPY": 640.0, "QQQ": 580.0,
    "IWM": 230.0, "RSP": 185.0, "SMH": 280.0, "EFA": 90.0, "VEA": 56.0,
    "VGK": 75.0, "EZU": 62.0, "EWJ": 78.0, "EWU": 40.0, "EWG": 35.0,
    "EWQ": 42.0, "EEM": 48.0, "VWO": 50.0, "MCHI": 55.0, "FXI": 32.0,
    "ASHR": 30.0, "INDA": 55.0, "EWT": 60.0, "EWY": 75.0, "EWZ": 30.0,
    "EWW": 60.0, "EWS": 22.0, "EIDO": 20.0, "BIL": 91.5, "SGOV": 100.5,
    "SHY": 82.5, "IEI": 118.0, "IEF": 95.0, "TLT": 88.0, "TIP": 110.0,
    "LQD": 110.0, "HYG": 79.0, "JNK": 96.0, "EMB": 92.0, "EMLC": 25.0,
    "GLD": 310.0, "SLV": 35.0, "USO": 75.0, "BNO": 30.0, "CPER": 32.0,
    "DBC": 22.0, "DBA": 26.0, "UUP": 27.0, "FXE": 105.0, "FXY": 65.0,
    "FXB": 125.0, "VNQ": 88.0, "IBIT": 60.0,
}


def business_days_back(end_date, n):
    out, d = [], end_date
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d -= _dt.timedelta(days=1)
    return list(reversed(out))


def regime_at(i, n):
    frac = i / max(1, n - 1)
    for rid, a, b in DEMO_REGIME_SCRIPT:
        if a <= frac < b or (b == 1.0 and frac >= a):
            return rid
    return DEMO_REGIME_SCRIPT[-1][0]


def generate_demo(config, asof=None, days=780, seed=20260816):
    """[MCFL-M10-C12-F110] regime 腳本化 T4 合成世界。
    同 seed 同參數 → 完全再現（種子再現性閘）。"""
    if asof is None:
        asof = _dt.date.today()
    elif isinstance(asof, str):
        asof = _dt.date.fromisoformat(asof)
    while asof.weekday() >= 5:
        asof -= _dt.timedelta(days=1)

    rng = random.Random(seed)
    dates_d = business_days_back(asof, days)
    dates = [d.isoformat() for d in dates_d]
    tickers = [u["ticker"] for u in universe_tickers(config)]

    macro = {"DGS2": [], "DGS10": [], "DFII10": [], "T10YIE": []}
    prices = {t: [] for t in tickers}
    level = {t: DEMO_START_PRICE.get(t, 50.0) for t in tickers}
    regime_track = []

    for i in range(days):
        rid = regime_at(i, days)
        regime_track.append(rid)
        p = DEMO_FACTOR_PARAMS[rid]
        f = {k: rng.gauss(mu, sd) for k, (mu, sd) in p.items()}

        # 殖利率演化：f["r"] 即 Δ10Y 日變動（單位 pp），直接累加水位
        d10 = f["r"]
        d2 = 1.1 * d10 + rng.gauss(0.0, 0.008)
        die = 0.35 * f["m"] + rng.gauss(0.0, 0.006)
        y10_prev = macro["DGS10"][-1] if macro["DGS10"] else 4.55
        y2_prev = macro["DGS2"][-1] if macro["DGS2"] else 4.85
        ie_prev = macro["T10YIE"][-1] if macro["T10YIE"] else 2.30
        real_prev = macro["DFII10"][-1] if macro["DFII10"] else (4.55 - 2.30)
        y10 = min(6.5, max(1.5, y10_prev + d10))
        y2 = min(6.8, max(1.2, y2_prev + d2))
        ie = min(3.4, max(1.2, ie_prev + die))
        real = y10 - ie
        d_real = real - real_prev
        macro["DGS2"].append(round(y2, 4))
        macro["DGS10"].append(round(y10, 4))
        macro["T10YIE"].append(round(ie, 4))
        macro["DFII10"].append(round(real, 4))

        # 債券 ETF 報酬（先算 IEF 供信用債引用）
        bond_ret = {}
        for t, dur in DEMO_DURATION.items():
            dy = d2 if dur <= 2.0 else d10
            carry = (y2 if dur <= 2.0 else y10) / 100.0 / 252.0
            bond_ret[t] = -dur * dy / 100.0 + carry + rng.gauss(0.0, 0.0004)
        bond_ret["TIP"] = (-DEMO_TIP_DURATION * d_real / 100.0
                           + y10 / 100.0 / 252.0 + rng.gauss(0.0, 0.0005))
        ief_ret = bond_ret["IEF"]

        for t in tickers:
            if t in bond_ret:
                ret = bond_ret[t]
            else:
                ld = DEMO_LOADINGS.get(t, {"g": 0.6, "idio": 0.006})
                ret = ld.get("drift", 0.0)
                ret += ld.get("g", 0.0) * f["g"]
                ret += ld.get("u", 0.0) * f["u"]
                ret += ld.get("m", 0.0) * f["m"]
                ret += ld.get("ai", 0.0) * f["ai"]
                ret += ld.get("cn", 0.0) * f["cn"]
                ret += ld.get("c", 0.0) * f["c"]
                ret += ld.get("ief", 0.0) * ief_ret
                ret += ld.get("r_eq", 0.0) * d10          # 股票的利率敏感（pp）
                ret += ld.get("r_dur", 0.0) * d10 / 100.0  # REIT 久期式敏感
                ret += ld.get("real", 0.0) * d_real / 100.0
                ret += rng.gauss(0.0, ld.get("idio", 0.005))
            level[t] *= math.exp(ret)
            prices[t].append(round(level[t], 4))

    provenance = {
        "data_source": "synthetic_demo",
        "truth_tier": "T4",
        "evidence": "Est",
        "seed": seed,
        "days": days,
        "regime_script": [{"id": r, "from": a, "to": b} for r, a, b in DEMO_REGIME_SCRIPT],
        "scripted_regime_at_asof": regime_track[-1],
        "note": "SYNTHETIC(T4) 合成市場，僅供管線/儀表板驗證，禁止作為投資判讀",
    }
    return MarketData(dates, prices, macro, provenance)
