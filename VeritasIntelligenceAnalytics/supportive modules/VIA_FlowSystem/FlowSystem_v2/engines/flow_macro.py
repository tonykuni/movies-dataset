# -*- coding: utf-8 -*-
"""VDF-FLOW-MACRO flow_macro.py — 宏觀對照層(v0100R;操作員 2026/08/12 令)。

全球各類各區 ETF 現金流 × 各地匯率/利率/美元指數/經濟強弱 → 資金流動強弱及方向判讀:
  每區宏觀分 = w1·本幣動能 + w2·利差(區−美) + w3·經濟強度(PMI−50) − w4·美元逆風(DXY 走強×敏感區)
  判讀:FIS 與宏觀分同號=順風(流入獲支撐/流出有理由);異號=背離(流入無宏觀支撐=慎追;
       流出但宏觀轉佳=潛在轉折關注)。
資料:data/input/macro_data.json 側車(bridge;零爬站);缺=合成 demo 明標 source=synthetic。
產物:data/output/macro_overlay.json — flow_ui 吸收成「宏觀對照」卡。
"""
import json
import math
import random
from pathlib import Path

from flow_core import bucket_fis, load_json, load_universe

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CFG = ROOT / "config" / "macro.json"
INP = ROOT / "data" / "input" / "macro_data.json"
OUTP = ROOT / "data" / "output" / "macro_overlay.json"


def load_macro_cfg():
    return load_json(CFG, {}) or {}


def _synth_macro(cfg, n=60, seed=17):
    """合成 demo(明標):各區 fx/econ 隨機漫步 + DXY;真實側車到位即棄用。"""
    rng = random.Random(seed)
    recs, dxy = [], []
    v_dxy = 103.0
    fxv = {r: 100.0 for r in cfg.get("regions", {})}
    econ = {r: 50.0 + rng.uniform(-4, 4) for r in cfg.get("regions", {})}
    for i in range(n):
        d = "2026-%02d-%02d" % (5 + i // 28, 1 + i % 28)
        v_dxy *= 1 + rng.gauss(0, 0.003)
        dxy.append({"date": d, "value": round(v_dxy, 2)})
        for r, rc in cfg.get("regions", {}).items():
            fxv[r] *= 1 + rng.gauss(0, 0.004)
            econ[r] = max(38.0, min(62.0, econ[r] + rng.gauss(0, 0.35)))
            recs.append({"date": d, "region": r, "fx_rate": round(fxv[r], 3),
                         "policy_rate": rc.get("policy_rate", 3.0),
                         "econ_pmi": round(econ[r], 1)})
    return {"source": "synthetic demo(真實側車 macro_data.json 到位即自動切換)",
            "records": recs, "dxy": dxy}


def load_macro_data(cfg):
    d = load_json(INP, None)
    if d and d.get("records"):
        return d, True
    return _synth_macro(cfg), False


def _mom(vals, k=20):
    """近 k 期動能 %。"""
    v = [x for x in vals if x is not None]
    if len(v) < 2:
        return 0.0
    tail = v[-min(k, len(v)):]
    return (tail[-1] / tail[0] - 1.0) * 100.0 if tail[0] else 0.0


def build_overlay(rows, write=True):
    """rows = FIS panel rows;合成/真實宏觀 → 每區判讀矩陣。"""
    cfg = load_macro_cfg()
    data, real = load_macro_data(cfg)
    uni = load_universe()
    w = cfg.get("weights", {})
    us_rate = float(cfg.get("us_policy_rate", 4.25))
    region_fis = bucket_fis(rows or [], lambda r, u: u.get("region", "US"), universe=uni)
    by_r = {}
    for rec in data.get("records", []):
        by_r.setdefault(str(rec["region"]), []).append(rec)
    dxy_vals = [x["value"] for x in data.get("dxy", [])]
    dxy_mom = _mom(dxy_vals)
    dxy_regime = "美元走強" if dxy_mom > 0.5 else ("美元走弱" if dxy_mom < -0.5 else "美元持平")
    out_rows = []
    for region, rc in cfg.get("regions", {}).items():
        recs = sorted(by_r.get(region, []), key=lambda x: str(x["date"]))
        if not recs:
            continue
        fx_m = _mom([r["fx_rate"] for r in recs])
        if rc.get("fx_invert"):
            fx_m = -fx_m  # USDxxx 上升=本幣貶 → 反號成「本幣動能」
        rate_diff = float(recs[-1].get("policy_rate", 3.0)) - us_rate
        econ_z = (float(recs[-1].get("econ_pmi", 50.0)) - 50.0)
        headwind = max(0.0, dxy_mom) if rc.get("dxy_sensitive") else 0.0
        score = (float(w.get("fx_momentum", .3)) * max(-3, min(3, fx_m)) / 3.0
                 + float(w.get("rate_diff", .25)) * max(-4, min(4, rate_diff)) / 4.0
                 + float(w.get("econ", .3)) * max(-8, min(8, econ_z)) / 8.0
                 - float(w.get("dxy_headwind", .15)) * min(3, headwind) / 3.0) * 100.0
        fis = region_fis.get(region)
        if fis is None:
            verdict, vk = "無流量樣本", "na"
        elif fis >= 0 and score >= 0:
            verdict, vk = "順風流入(宏觀支撐)", "ok"
        elif fis < 0 and score < 0:
            verdict, vk = "順風流出(宏觀同向)", "ok"
        elif fis >= 0 and score < 0:
            verdict, vk = "背離:流入無宏觀支撐 — 慎追", "warn"
        else:
            verdict, vk = "背離:流出但宏觀轉佳 — 關注轉折", "turn"
        out_rows.append({"region": region, "fis": fis,
                         "fx_label": rc.get("fx", ""), "fx_momentum": round(fx_m, 2),
                         "rate_diff": round(rate_diff, 2),
                         "econ_label": rc.get("econ_label", ""), "econ": round(econ_z, 1),
                         "macro_score": round(score, 1),
                         "verdict": verdict, "vk": vk})
    out_rows.sort(key=lambda r: -(abs(r["fis"]) if r["fis"] is not None else 0))
    strength = sum(abs(r["fis"]) for r in out_rows if r["fis"] is not None) / (len([r for r in out_rows if r["fis"] is not None]) or 1)
    result = {"version": "v0100R", "real_data": real,
              "source": data.get("source", ""),
              "dxy": {"momentum": round(dxy_mom, 2), "regime": dxy_regime},
              "overall_strength": round(strength, 1),
              "rows": out_rows,
              "honest_note": "宏觀分=規則組合非預測;判讀口徑見 config/macro.json;"
                             + ("真實側車資料" if real else "合成 demo — 接 macro_data.json 即真")}
    if write:
        OUTP.parent.mkdir(parents=True, exist_ok=True)
        OUTP.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    return result
