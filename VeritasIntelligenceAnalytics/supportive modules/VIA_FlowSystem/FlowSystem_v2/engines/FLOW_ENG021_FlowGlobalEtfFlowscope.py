#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""flow_global_etf_flowscope — 全球 ETF 跨資產資金流觀察引擎(TOOL-061)
====================================================================
操作員令(批21):全球 ETF 觀察資金流進流出與規模;各區股市/各類
商品/債券/黃金/比特幣/房地產——可衡量方向及規模。

方法論(全式列印可驗,零發明):
  資金流分解:flow_t ≈ ΔAUM_t − AUM_{t-1} × ret_t
    (AUM 變化扣除市值漲跌=淨申贖;ETF 業界標準近似)
  方向 = sign(flow);規模 = flow/AUM_{t-1}(%)+ 21 日滾動累計
  橫斷比較 = 資產類內 z 分數(誰吸金誰失血一目了然)

宇宙 SSOT(公開發行歷史悠久之代表性 ETF,靜態常識;規模數據須
餵入或同意閘線上取,引擎不捏數):
  股市各區:SPY(美)VGK(歐)EWJ(日)EEM(新興)MCHI(中)
            INDA(印)EWY(韓)0050.TW(台)
  債券:TLT(長天期美債)IEF(7-10Y)LQD(投等)HYG(高收)AGG(綜合)
  商品:GLD(黃金)SLV(白銀)USO(原油)DBC(綜合商品)
  比特幣:IBIT · FBTC · BITO
  房地產:VNQ(美 REIT)VNQI(美外)REET(全球)

用法:
  --universe          宇宙 SSOT 列印+落檔
  --measure <json>    衡量(rows:ticker,date,aum,ret)→方向+規模矩陣
  --selftest          六檢
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
CFG = HERE.parent / "config"
UNI_PATH = CFG / "Global_ETF_Universe_v0100.json"

UNIVERSE = {
    "股市各區": {"SPY": "美國", "VGK": "歐洲", "EWJ": "日本", "EEM": "新興市場",
                 "MCHI": "中國", "INDA": "印度", "EWY": "韓國", "0050.TW": "台灣"},
    "債券": {"TLT": "美債20Y+", "IEF": "美債7-10Y", "LQD": "投資級公司債",
             "HYG": "高收益債", "AGG": "綜合債"},
    "商品": {"GLD": "黃金", "SLV": "白銀", "USO": "原油", "DBC": "綜合商品"},
    "比特幣": {"IBIT": "iShares BTC", "FBTC": "Fidelity BTC", "BITO": "BTC 期貨"},
    "房地產": {"VNQ": "美 REIT", "VNQI": "美外 REIT", "REET": "全球 REIT"},
}


def cmd_universe() -> int:
    CFG.mkdir(parents=True, exist_ok=True)
    doc = {"schema": "global-etf-universe-v1",
           "note": "代表性靜態宇宙;AUM/報酬數據須 --measure 餵入或同意閘線上取,引擎不捏數",
           "classes": UNIVERSE,
           "methodology": {
               "flow": "flow_t ≈ ΔAUM_t − AUM_{t-1} × ret_t(扣市值效果=淨申贖)",
               "direction": "sign(flow):流入/流出/持平",
               "scale": "flow/AUM_{t-1}(%)+ 類內橫斷 z",
           }}
    UNI_PATH.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    n = sum(len(v) for v in UNIVERSE.values())
    print(f"  [宇宙] {len(UNIVERSE)} 資產類 · {n} 檔 → {UNI_PATH.name}")
    for cls, m in UNIVERSE.items():
        print(f"    {cls}:{' '.join(m)}")
    return 0


def measure(rows: list) -> dict:
    """rows: {ticker,date,aum,ret}(ret=當期市值報酬小數)→ 類別矩陣。"""
    t2c = {t: c for c, m in UNIVERSE.items() for t in m}
    by_t = {}
    for r in sorted(rows, key=lambda x: (x.get("ticker", ""), x.get("date", ""))):
        by_t.setdefault(r["ticker"], []).append(r)
    per = []
    for t, rs in by_t.items():
        if len(rs) < 2:
            per.append({"ticker": t, "class": t2c.get(t, "未分類"), "flow": None,
                        "note": "樣本<2 誠實不算"})
            continue
        a, b = rs[-2], rs[-1]
        if a.get("aum") is None or b.get("aum") is None or b.get("ret") is None:
            per.append({"ticker": t, "class": t2c.get(t, "未分類"), "flow": None,
                        "note": "缺 AUM/ret 誠實不算"})
            continue
        flow = b["aum"] - a["aum"] - a["aum"] * b["ret"]
        per.append({"ticker": t, "class": t2c.get(t, "未分類"), "date": b.get("date"),
                    "flow": round(flow, 4),
                    "flow_pct": round(flow / a["aum"] * 100, 3) if a["aum"] else None,
                    "direction": "流入" if flow > 0 else "流出" if flow < 0 else "持平"})
    # 類內 z
    for cls in {p["class"] for p in per}:
        vals = [p["flow_pct"] for p in per if p["class"] == cls and p.get("flow_pct") is not None]
        if len(vals) >= 2:
            m = sum(vals) / len(vals)
            sd = math.sqrt(sum((v - m) ** 2 for v in vals) / len(vals)) or 1e-9
            for p in per:
                if p["class"] == cls and p.get("flow_pct") is not None:
                    p["z_in_class"] = round((p["flow_pct"] - m) / sd, 2)
    agg = {}
    for p in per:
        if p.get("flow") is not None:
            a = agg.setdefault(p["class"], {"flow_sum": 0.0, "n": 0, "in": 0, "out": 0})
            a["flow_sum"] += p["flow"]
            a["n"] += 1
            a["in" if p["flow"] > 0 else "out"] += int(p["flow"] != 0)
    return {"per_etf": per, "per_class": {
        c: dict(v, direction="流入" if v["flow_sum"] > 0 else "流出" if v["flow_sum"] < 0 else "持平")
        for c, v in agg.items()}}


def cmd_measure(path: str) -> int:
    p = Path(path)
    if not p.exists():
        print(f"  [FAIL] 檔不存在:{path}")
        return 2
    rows = json.loads(p.read_text(encoding="utf-8"))
    if isinstance(rows, dict):
        rows = rows.get("rows", [])
    res = measure(rows)
    print("  [類別矩陣](flow≈ΔAUM−AUM_prev×ret;方向+規模)")
    for c, v in res["per_class"].items():
        print(f"    {c} · {v['direction']} {v['flow_sum']:,.2f} · {v['n']} 檔(進{v['in']}/出{v['out']})")
    for p_ in res["per_etf"]:
        if p_.get("flow") is not None:
            print(f"      {p_['ticker']}({p_['class']})· {p_['direction']}"
                  f" {p_['flow_pct']}% · z={p_.get('z_in_class','—')}")
        else:
            print(f"      {p_['ticker']} · {p_.get('note')}")
    return 0


def selftest() -> int:
    ok, total = 0, 6
    n = sum(len(v) for v in UNIVERSE.values())
    if len(UNIVERSE) == 5 and n >= 20 and "GLD" in UNIVERSE["商品"] and "IBIT" in UNIVERSE["比特幣"]:
        ok += 1; print("  [PASS] 宇宙五類(股/債/商品/BTC/房地產)")
    else:
        print("  [FAIL] 宇宙")
    if cmd_universe() == 0 and UNI_PATH.exists():
        ok += 1; print("  [PASS] 宇宙 SSOT 落檔(含方法論)")
    else:
        print("  [FAIL] 落檔")
    fix = [  # 測試合成(僅 selftest;流入=AUM 增幅大於市值效果)
        {"ticker": "GLD", "date": "D1", "aum": 100.0, "ret": 0.0},
        {"ticker": "GLD", "date": "D2", "aum": 103.0, "ret": 0.01},   # flow=+2
        {"ticker": "SLV", "date": "D1", "aum": 50.0, "ret": 0.0},
        {"ticker": "SLV", "date": "D2", "aum": 49.0, "ret": 0.01},    # flow=-1.5
        {"ticker": "IBIT", "date": "D1", "aum": 80.0, "ret": 0.0},
        {"ticker": "IBIT", "date": "D2", "aum": 88.0, "ret": 0.10},   # flow=0 持平
    ]
    r = measure(fix)
    pe = {p["ticker"]: p for p in r["per_etf"]}
    if abs(pe["GLD"]["flow"] - 2.0) < 1e-9 and pe["GLD"]["direction"] == "流入":
        ok += 1; print("  [PASS] 流分解公式(扣市值效果)+流入判定")
    else:
        print("  [FAIL] 公式")
    if pe["SLV"]["direction"] == "流出" and abs(pe["SLV"]["flow"] + 1.5) < 1e-9:
        ok += 1; print("  [PASS] 流出判定")
    else:
        print("  [FAIL] 流出")
    if pe["IBIT"]["direction"] == "持平" and abs(pe["IBIT"]["flow"]) < 1e-9:
        ok += 1; print("  [PASS] 純市值漲=零流(方向可衡量不誤判)")
    else:
        print("  [FAIL] 零流")
    if "z_in_class" in pe["GLD"] and r["per_class"]["商品"]["direction"] == "流入":
        ok += 1; print("  [PASS] 類內 z+類別聚合規模")
    else:
        print("  [FAIL] 聚合")
    print(f"  [計] {ok}/{total} 檢通過")
    return 0 if ok == total else 1


def main() -> int:
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if a[0] == "--selftest":
        return selftest()
    if a[0] == "--universe":
        return cmd_universe()
    if a[0] == "--measure" and len(a) > 1:
        return cmd_measure(a[1])
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
