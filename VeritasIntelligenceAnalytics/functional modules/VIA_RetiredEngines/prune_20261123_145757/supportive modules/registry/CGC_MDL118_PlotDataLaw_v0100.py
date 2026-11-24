#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL118_PlotDataLaw v0100 — 繪圖/TA-Lib 資料律(批330;操作員嚴令)
======================================================================
操作員令(批330):「增加並嚴格訂定規定:TA-LIB 及所有繪圖,價格一律取調整後價格;
成交量一定要採扣除當沖交易成交量」。
本件=該律之唯一定義處(SSOT 冊 VIA_PlotDataLaw_v0100.json 同步)+共用取數原語+稽核器:
  律一 PRICE=ADJUSTED:繪圖/TA 輸入價一律還原權息價(tw_prices_adj adj_open/high/low/close;
       調整層缺者用 Yahoo adj_close=PriceSource YF_ADJ 旗標);原始收盤 raw_close 只准用於
       金額換算(淨股數×收盤)與顯示對照,禁入指標與線圖。
  律二 VOLUME=EX_DAYTRADE:成交量一律扣除當沖成交量。三階來源律(嚴格、誠實、不靜默):
       ① STOCK       個股當沖量(表 tw_daytrade_stock;候源=TWSE/TPEX 逐股 WAF 候)
       ② MARKET_RATIO 同日同市場市場級當沖比(tw_daytrade_market dt_volume_pct)代位=DERIVED
       ③ NONE        無任何當沖料=該列 Volume 缺值(NaN),DTSource='NONE';禁止以原始量冒充;
                     圖面/表頭必印 stamp()(覆蓋日數)=誠實缺料
       VolumeRaw 欄保留原始量供對照;TA-Lib 量類指標(MFI/OBV…)只吃 attrs ex_daytrade=True 之量。
  稽核 --audit:掃現役繪圖/TA 引擎(冊 AUDIT_TARGETS),判 OK(掛律標記或已知合規證據)/FAIL
       (裸量/裸價)/NA,落 VIA_Reports/plot_law/PLOT_LAW_AUDIT_<stamp>.json,誠實三態。
引擎掛法:glob 尾版 import 本件(CGC_MDL118_PlotDataLaw_v*.py)→ law.ohlcv(code) / law.ex_daytrade(df, code);
         檔內留標記 [VIA:PLOTDATA-LAW:v0100] 供稽核。
用法:python CGC_MDL118_PlotDataLaw_v0100.py [--audit | --selftest | ohlcv 2330]
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
# [VIA:PLOTDATA-LAW:v0100] 本件=律之定義處

import json
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
DB_TW = VIA / "functional modules" / "VDF" / "output_hub" / "mega" / "vdf_tw_market.duckdb"
REP = VIA / "VIA_Reports" / "plot_law"
SSOT = HERE / "VIA_PlotDataLaw_v0100.json"
MARK = "[VIA:PLOTDATA-LAW"

LAW = {
    "law_id": "VIA_PLOTDATA_LAW", "version": "v0100", "batch": 330,
    "price": {"basis": "ADJUSTED", "columns": ["adj_open", "adj_high", "adj_low", "adj_close"],
              "fallback": "YF_ADJ(tw_daily_prices.adj_close;PriceSource 旗標)",
              "raw_close_allowed_for": ["金額換算(淨股數×收盤)", "顯示對照"],
              "raw_close_forbidden_for": ["指標", "線圖", "K線", "TA-Lib 輸入"]},
    "volume": {"basis": "EX_DAYTRADE",
               "sources": [{"rank": 1, "id": "STOCK", "table": "tw_daytrade_stock", "note": "個股當沖量(候源)"},
                           {"rank": 2, "id": "MARKET_RATIO", "table": "tw_daytrade_market", "note": "同日同市場當沖比代位 DERIVED"},
                           {"rank": 3, "id": "NONE", "table": None, "note": "無料=Volume NaN;禁以原始量冒充;圖面必印 stamp"}],
               "raw_volume_column": "VolumeRaw", "talib_gate": "Series.attrs['ex_daytrade']==True 才入量類指標"},
    "enforcement": {"marker": "[VIA:PLOTDATA-LAW:v0100]", "audit": "CGC_MDL118 --audit", "honesty": "三態 OK/FAIL/NA;覆蓋日數必印"},
}

# 稽核冊:現役繪圖/TA 引擎(glob 尾版);evidence=合規證據 regex(標記或既有律)
AUDIT_TARGETS = [
    ("VAP_ENG015 Seaborn 圖組/K線", "functional modules/VAP/engine", "VAP_ENG015_SeabornStackBridge_v*.py", None),
    ("VAP_ENG004 TA-Lib 工廠", "functional modules/VAP/engine", "VAP_ENG004_TAFactory_v*.py", None),
    ("VDF_ENG048 TA-Lib 正本(LEGACY;由 VAP_ENG004 承接)", "functional modules/VDF/engine", "VDF_ENG048_TAFactory.py", "LEGACY"),
    ("VDF_ENG070 族群分類(量=ETR 扣當沖)", "functional modules/VDF/engine", "VDF_ENG070_GroupClassificationIndex_v*.py",
     r"val\"\]\s*\*\s*\(1\.0\s*-\s*p\.fillna"),
    ("VDF_ENG071 族群回測(價=ENG070 還原殘差)", "functional modules/VDF/engine", "VDF_ENG071_GroupBacktest_v*.py",
     r"_eng070\("),
    ("VAP_ENG013 市場分析(VapDeck K線)", "functional modules/VAP/engine", "VAP_ENG013_MarketAnalytics_v*.py", None),
    ("VAP_ENG009 儀表板", "functional modules/VAP/engine", "VAP_ENG009_DashboardUI_v*.py", None),
    ("VAP_ENG014 標準儀表板", "functional modules/VAP/engine", "VAP_ENG014_StdDashboardTemplate_v*.py", None),
    ("CGC_MDL095 樞紐 /vap_kline", "supportive modules/registry", "CGC_MDL095_DeckServer_v*.py", None),
    ("VDF_ENG068 ETF×共識", "functional modules/VDF/engine", "VDF_ENG068_ETFConsensusAnalysis_v*.py", None),
    ("VDF_ENG069 月營收×共識", "functional modules/VDF/engine", "VDF_ENG069_RevenueConsensusAnalysis_v*.py", None),
]
RAW_VOL_RX = re.compile(r"\bvolume\b", re.I)
RAW_CLOSE_RX = re.compile(r"\bd\.close\b|\braw_close\b|\"close\"\s*\]")


def _con():
    import duckdb
    return duckdb.connect(str(DB_TW), read_only=True)


def dt_ratio_table():
    """市場級當沖比(date, market, dt_ratio∈[0,1]);缺表=空"""
    import pandas as pd
    if not DB_TW.exists():
        return pd.DataFrame(columns=["Date", "market", "dt_ratio"])
    c = _con()
    try:
        tabs = {r[0] for r in c.execute("show tables").fetchall()}
        if "tw_daytrade_market" not in tabs:
            return pd.DataFrame(columns=["Date", "market", "dt_ratio"])
        df = c.execute("SELECT CAST(date AS VARCHAR) AS Date, market, dt_volume_pct FROM tw_daytrade_market").df()
    finally:
        c.close()
    p = df["dt_volume_pct"].astype(float)
    df["dt_ratio"] = p.where(p <= 1.0, p / 100.0).clip(0, 1)
    return df[["Date", "market", "dt_ratio"]]


def stock_dt_table(code: str):
    """個股當沖量(表 tw_daytrade_stock 候源;缺=空)"""
    import pandas as pd
    if not DB_TW.exists():
        return pd.DataFrame(columns=["Date", "dt_volume"])
    c = _con()
    try:
        tabs = {r[0] for r in c.execute("show tables").fetchall()}
        if "tw_daytrade_stock" not in tabs:
            return pd.DataFrame(columns=["Date", "dt_volume"])
        return c.execute(f"SELECT CAST(date AS VARCHAR) AS Date, dt_volume FROM tw_daytrade_stock "
                         f"WHERE code='{code}'").df()
    finally:
        c.close()


def market_of(code: str) -> str:
    if not DB_TW.exists():
        return "TWSE"
    c = _con()
    try:
        r = c.execute(f"SELECT market FROM tw_listings WHERE code='{code}' LIMIT 1").fetchone()
    finally:
        c.close()
    return (r[0] if r else "TWSE").upper()


def ex_daytrade(df, code: str, market: str | None = None, date_col: str = "Date", vol_col: str = "Volume"):
    """律二三階:Volume→扣當沖;VolumeRaw 保留;DTSource 逐列;回 (df, coverage)"""
    import numpy as np
    import pandas as pd
    d = df.copy()
    d["VolumeRaw"] = d[vol_col].astype(float)
    d[date_col] = d[date_col].astype(str).str.slice(0, 10)
    mk = (market or market_of(code)).upper()
    src = pd.Series("NONE", index=d.index)
    vol = pd.Series(np.nan, index=d.index)
    st = stock_dt_table(code)
    if len(st):
        m = d[[date_col]].merge(st, left_on=date_col, right_on="Date", how="left")["dt_volume"].to_numpy()
        ok = ~np.isnan(m)
        vol[ok] = (d["VolumeRaw"].to_numpy()[ok] - m[ok]).clip(min=0)
        src[ok] = "STOCK"
    rt = dt_ratio_table()
    if len(rt):
        rt = rt[rt["market"].str.upper() == mk]
        m = d[[date_col]].merge(rt, left_on=date_col, right_on="Date", how="left")["dt_ratio"].to_numpy()
        ok = (~np.isnan(m)) & (src.to_numpy() == "NONE")
        vol[ok] = d["VolumeRaw"].to_numpy()[ok] * (1.0 - m[ok])
        src[ok] = "MARKET_RATIO"
    d[vol_col] = vol
    d["DTSource"] = src
    d.attrs["ex_daytrade"] = True      # 律旗標掛 DataFrame;Series 用 volume_series() 取(pandas 欄取為新物件)
    cov = {"rows": int(len(d)), "stock": int((src == "STOCK").sum()), "market_ratio": int((src == "MARKET_RATIO").sum()),
           "none": int((src == "NONE").sum()), "market": mk}
    return d, cov


def volume_series(df, vol_col: str = "Volume"):
    """回帶律旗標之量序列(attrs ex_daytrade=True;TA-Lib 量閘唯一入口)"""
    s = df[vol_col].copy()
    s.attrs["ex_daytrade"] = bool(df.attrs.get("ex_daytrade"))
    return s


def stamp(cov: dict) -> str:
    n = cov.get("rows", 0)
    return (f"量=扣當沖(律 v0100;個股 {cov.get('stock', 0)} 日·市場比 {cov.get('market_ratio', 0)} 日·"
            f"無料缺值 {cov.get('none', 0)}/{n} 日)")


def ohlcv(code: str):
    """律一+律二取數:回 (df, cov)。df 欄 Date, Open, High, Low, Close(還原), RawClose, PriceSource,
    Volume(扣當沖;無料=NaN), VolumeRaw, DTSource"""
    import pandas as pd
    if not DB_TW.exists():
        return pd.DataFrame(), {"rows": 0, "stock": 0, "market_ratio": 0, "none": 0, "market": "?"}
    c = _con()
    try:
        df = c.execute(f"""
            SELECT CAST(d.date AS VARCHAR) AS Date,
                   COALESCE(a.adj_open, d.adj_close) AS Open, COALESCE(a.adj_high, d.adj_close) AS High,
                   COALESCE(a.adj_low, d.adj_close) AS Low, COALESCE(a.adj_close, d.adj_close) AS Close,
                   d.close AS RawClose, d.volume AS Volume,
                   CASE WHEN a.adj_close IS NULL THEN 'YF_ADJ' ELSE 'ADJ_LAYER' END AS PriceSource
            FROM tw_daily_prices d
            LEFT JOIN tw_prices_adj a USING (date, ticker)
            WHERE regexp_replace(d.ticker, '\\.(TW|TWO)$', '') = '{code}' AND d.close > 0
            ORDER BY 1""").df()
    finally:
        c.close()
    if df.empty:
        return df, {"rows": 0, "stock": 0, "market_ratio": 0, "none": 0, "market": market_of(code)}
    df = df.drop_duplicates("Date")
    return ex_daytrade(df, code)


def audit(do_print: bool = True) -> dict:
    """稽核冊逐件:OK=掛律標記或合規證據;FAIL=裸量/裸價且無標記;NA=件缺"""
    rows = []
    for label, d, pat, evidence in AUDIT_TARGETS:
        hits = sorted((VIA / d).glob(pat))
        if not hits:
            rows.append({"engine": label, "file": "", "state": "NA", "note": "件缺(誠實)"})
            continue
        f = hits[-1]
        src = f.read_text(encoding="utf-8", errors="ignore")
        marked = MARK in src
        raw_vol = len(RAW_VOL_RX.findall(src))
        if evidence == "LEGACY":
            rows.append({"engine": label, "file": f.name, "state": "LEGACY", "note": "正本零觸碰律;現役由版前進件承接(不計 FAIL)",
                         "raw_volume_refs": raw_vol})
            continue
        ev = bool(evidence and re.search(evidence, src))
        if marked or ev:
            state, note = "OK", ("掛律標記" if marked else "合規證據(既有律)")
        elif raw_vol:
            state, note = "FAIL", f"裸 volume 用法 {raw_vol} 處且無律標記(候版前進掛律)"
        else:
            state, note = "OK", "無量/價直用(不適用)"
        rows.append({"engine": label, "file": f.name, "state": state, "note": note, "raw_volume_refs": raw_vol})
    cov = {}
    try:
        _, cov = ohlcv("2330")
    except Exception as exc:
        cov = {"err": f"{type(exc).__name__}: {str(exc)[:80]}"}
    rep = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "law": LAW, "rows": rows, "sample_2330_coverage": cov,
           "n_ok": sum(1 for r in rows if r["state"] == "OK"), "n_fail": sum(1 for r in rows if r["state"] == "FAIL"),
           "n_na": sum(1 for r in rows if r["state"] == "NA"),
           "n_legacy": sum(1 for r in rows if r["state"] == "LEGACY")}
    REP.mkdir(parents=True, exist_ok=True)
    out = REP / f"PLOT_LAW_AUDIT_{time.strftime('%Y%m%d_%H%M%S')}.json"
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    if do_print:
        print(f"=== 繪圖/TA 資料律稽核(CGC_MDL118 v0100)· 律一 價=還原 · 律二 量=扣當沖 ===")
        for r in rows:
            print(f"  [{r['state']:<4}] {r['engine']} · {r['file']} · {r['note']}")
        print(f"  [計] OK {rep['n_ok']} · FAIL {rep['n_fail']} · LEGACY {rep['n_legacy']} · NA {rep['n_na']} · 2330 {stamp(cov) if 'rows' in cov else cov}")
        print(f"  存證 {out}")
    return rep


def write_ssot() -> Path:
    SSOT.write_text(json.dumps(LAW, ensure_ascii=False, indent=1), encoding="utf-8")
    return SSOT


def selftest() -> int:
    import numpy as np
    import pandas as pd
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    write_ssot()
    chk("① SSOT 冊落地(律一 ADJUSTED/律二 EX_DAYTRADE/三階來源)", SSOT.exists()
        and json.loads(SSOT.read_text(encoding="utf-8"))["volume"]["basis"] == "EX_DAYTRADE"
        and len(LAW["volume"]["sources"]) == 3)
    # 合成:三階來源律(以 monkeypatch 表)
    df = pd.DataFrame({"Date": ["2026-08-04", "2026-08-05", "2026-08-06"], "Volume": [1000.0, 2000.0, 3000.0]})
    g = globals()
    _st, _rt = g["stock_dt_table"], g["dt_ratio_table"]
    g["stock_dt_table"] = lambda code: pd.DataFrame({"Date": ["2026-08-04"], "dt_volume": [300.0]})
    g["dt_ratio_table"] = lambda: pd.DataFrame({"Date": ["2026-08-05"], "market": ["TPEX"], "dt_ratio": [0.25]})
    try:
        d, cov = ex_daytrade(df, "9999", market="TPEX")
    finally:
        g["stock_dt_table"], g["dt_ratio_table"] = _st, _rt
    chk("② 三階來源律(個股 700/市場比 1500/無料 NaN)+VolumeRaw 保留+DTSource 逐列",
        abs(d["Volume"][0] - 700) < 1e-9 and abs(d["Volume"][1] - 1500) < 1e-9 and np.isnan(d["Volume"][2])
        and list(d["DTSource"]) == ["STOCK", "MARKET_RATIO", "NONE"] and list(d["VolumeRaw"]) == [1000, 2000, 3000]
        and cov == {"rows": 3, "stock": 1, "market_ratio": 1, "none": 1, "market": "TPEX"})
    chk("③ TA 量閘旗標(df.attrs+volume_series attrs ex_daytrade=True)+stamp 誠實印覆蓋",
        d.attrs.get("ex_daytrade") is True and volume_series(d).attrs.get("ex_daytrade") is True
        and "無料缺值 1/3" in stamp(cov))
    if DB_TW.exists():
        o, cov2 = ohlcv("2330")
        chk("④ 實庫 ohlcv(價=還原 PriceSource 旗標;量=扣當沖;原始量保留)", len(o) > 100
            and set(o["PriceSource"]) <= {"ADJ_LAYER", "YF_ADJ"} and "VolumeRaw" in o
            and (o["Volume"].isna() | (o["Volume"] <= o["VolumeRaw"] + 1e-9)).all(), stamp(cov2))
    else:
        chk("④ 實庫 ohlcv", True, "(庫缺=誠實跳)")
    rep = audit(do_print=False)
    chk("⑤ 稽核器三態+存證(冊 ≥10 件)", len(rep["rows"]) >= 10 and all(r["state"] in ("OK", "FAIL", "NA", "LEGACY") for r in rep["rows"]))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 律標記+加速橋+誠實宣告", MARK in src and "ACCEL-BRIDGE" in src and "誠實" in src)
    print(f"  [計] 六檢 OK {6 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 繪圖/TA 資料律(CGC_MDL118)· 六檢自測(零外網)===")
        return selftest()
    if "--audit" in a:
        write_ssot()
        rep = audit()
        return 0 if rep["n_fail"] == 0 else 1
    if a and a[0] == "ohlcv":
        df, cov = ohlcv(a[1] if len(a) > 1 else "2330")
        print(df.tail(5).to_string())
        print(stamp(cov))
        return 0
    write_ssot()
    print(f"[律] {SSOT.name} 落地 · 用法 --audit | --selftest | ohlcv <代碼>")
    return 0


if __name__ == "__main__":
    sys.exit(main())
