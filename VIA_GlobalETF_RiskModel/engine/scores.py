# -*- coding: utf-8 -*-
"""
scores.py — M20_RiskScores：五大風險分數 + 跨資產脈衝 + 區域勢能 + 財政脆弱度
=============================================================================
MODULE M20_RiskScores
  [MCFL-M20-C21-F201..F204] compute_scores        — usd/rate/credit/commodity
  [MCFL-M20-C21-F206]       compute_fragility     — 國家財政外部脆弱度
  [MCFL-M20-C26-F230]       compute_regional_potential — 利差×匯率勢能
  [MCFL-M20-C28-F250]       compute_pulse         — 跨資產 Risk Pulse

合成式（與 MDL008 FIS 對齊）：
  component_z = robust_z(metric[t], metric[t-252 .. t-1])   ← T-1：樣本不含當日
  fis         = 100 * tanh(weighted_mean_z / 2)             ← ±100
  risk_0_100  = 50 + fis / 2
反循環：z 基準永遠是各 component 自身歷史，不對分數自我校準。
"""
from __future__ import annotations

from . import mathkit as mk
from .factors import resolve_indicator


def _component_metric_series(panel, comp_id, n_obs):
    """component 指標的全歷史序列（供 robust-z 與 sparkline）。"""
    out = []
    for end in range(n_obs):
        try:
            out.append(resolve_indicator(panel, comp_id, end=end))
        except ValueError:
            raise
    return out


def _risk_from_z(z_mean):
    fis = mk.fis_scale(z_mean)
    if fis is None:
        return None, None
    return fis, mk.clamp(50.0 + fis / 2.0, 0.0, 100.0)


def band_for(value, bands):
    if value is None:
        return {"id": "pending", "label": "P", "label_zh": "待補", "status": "pending"}
    for b in bands:
        if value <= b["max"]:
            return b
    return bands[-1]


def compute_scores(panel, config, history_tail=60):
    """[MCFL-M20-C21-F201..F204] SSOT def_scores 驅動的風險分數群。"""
    scaling = config["def_score_scaling"]
    lookback = int(scaling.get("z_lookback_days", 252))
    z_clip = float(scaling.get("z_clip", 3.0))
    bands = scaling["bands"]
    n = panel.n_obs()
    results = {}

    for sid, spec in config["def_scores"].items():
        comps_out, z_list, w_list = [], [], []
        metric_cache = {}
        for comp in spec["components"]:
            cid, w = comp["id"], float(comp.get("weight", 1.0))
            series = _component_metric_series(panel, cid, n)
            metric_cache[cid] = series
            val = series[-1]
            sample = [v for v in series[max(0, n - 1 - lookback):n - 1]]
            z = mk.robust_z(val, sample, clip=z_clip)
            comps_out.append({"id": cid, "desc": comp.get("desc", ""),
                              "value": val, "z": z, "weight": w})
            if z is not None:
                z_list.append(z * w)
                w_list.append(w)
        z_mean = (sum(z_list) / sum(w_list)) if w_list else None
        fis, risk = _risk_from_z(z_mean)

        # sparkline：最後 history_tail 天的 risk 序列（各日 z 皆對自身 T-1 歷史）
        history = []
        for end in range(max(lookback // 2, n - history_tail), n):
            zs, ws = [], []
            for comp in spec["components"]:
                cid, w = comp["id"], float(comp.get("weight", 1.0))
                series = metric_cache[cid]
                sample = series[max(0, end - lookback):end]
                z = mk.robust_z(series[end], sample, clip=z_clip)
                if z is not None:
                    zs.append(z * w)
                    ws.append(w)
            zm = (sum(zs) / sum(ws)) if ws else None
            _, r = _risk_from_z(zm)
            history.append(None if r is None else round(r, 2))

        results[sid] = {
            "id": sid,
            "name_zh": spec.get("name_zh", sid),
            "mcfl": spec.get("mcfl", ""),
            "fis": None if fis is None else round(fis, 2),
            "risk": None if risk is None else round(risk, 2),
            "band": band_for(risk, bands),
            "components": comps_out,
            "history": history,
            "evidence": "Est",
            "truth_tier": "T3",
        }
    return results


def compute_pulse(panel, config, history_tail=60):
    """[MCFL-M20-C28-F250] 跨資產 Risk Pulse：
    pulse_t = Σ(risk_leg w·ret1) − Σ(defense_leg w·ret1)，5 日平滑後對 60 日
    T-1 歷史取 robust-z。正值=資金偏向風險端（股/幣），負值=退守（債/REIT）。"""
    spec = config["def_cross_asset_pulse"]
    smooth = int(spec.get("smooth_days", 5))
    z_win = int(spec.get("z_window", 60))
    legs = []
    for tkr, w in spec["risk_leg"]:
        legs.append((panel.logret(tkr), float(w)))
    for tkr, w in spec["defense_leg"]:
        legs.append((panel.logret(tkr), -float(w)))
    n_ret = min(len(s) for s, _ in legs)
    raw = []
    for i in range(n_ret):
        raw.append(sum(s[len(s) - n_ret + i] * w for s, w in legs))
    smoothed = []
    for i in range(n_ret):
        window = raw[max(0, i - smooth + 1):i + 1]
        smoothed.append(sum(window) / len(window))

    def z_at(i):
        sample = smoothed[max(0, i - z_win):i]
        return mk.robust_z(smoothed[i], sample)

    history = [z_at(i) for i in range(max(z_win, n_ret - history_tail), n_ret)]
    z_last = history[-1] if history else None
    return {
        "id": "cross_asset_pulse",
        "name_zh": spec.get("name_zh", "跨資產 Risk Pulse"),
        "mcfl": spec.get("mcfl", ""),
        "z": None if z_last is None else round(z_last, 3),
        "direction": ("risk_on" if (z_last or 0) > 0.5 else
                      "risk_off" if (z_last or 0) < -0.5 else "neutral"),
        "history": [None if h is None else round(h, 3) for h in history],
        "legs": {"risk": spec["risk_leg"], "defense": spec["defense_leg"]},
        "evidence": "Est",
        "truth_tier": "T3",
    }


def compute_regional_potential(panel, config, fundamentals):
    """[MCFL-M20-C26-F230] 區域利差×匯率勢能：
    potential = (local_10y − US10Y) × ret20(fx_etf) × 100
    利差為正且該幣走強 → 正勢能（資金流入該區）；demo 用靜態 local_10y。"""
    rows = []
    us10 = panel.macro_series("DGS10")[-1]
    fx_note = "static_local_10y"
    for pair in config["def_regional_potential"]["pairs"]:
        country = fundamentals.get(pair["country"], {})
        local_y = country.get("local_10y")
        fx_ret = panel.ret(pair["fx_etf"], 20)
        if local_y is None or fx_ret is None or us10 is None:
            rows.append({"region": pair["region"], "status": "PENDING"})
            continue
        spread = local_y - us10
        potential = spread * fx_ret * 100.0
        rows.append({
            "region": pair["region"], "fx_etf": pair["fx_etf"],
            "local_10y": local_y, "us_10y": round(us10, 3),
            "spread_pp": round(spread, 3), "fx_ret20": round(fx_ret, 5),
            "potential": round(potential, 4),
            "reading_zh": ("利差×匯率同向，資金流入勢能" if potential > 0
                           else "利差或匯率背離，流出/套利平倉壓力"),
            "evidence": "Der", "note": fx_note,
        })
    return rows


def compute_fragility(panel, config, fundamentals):
    """[MCFL-M20-C21-F206] 國家財政/外部脆弱度：
    對 fundamentals 每欄取跨國百分位（higher/lower_is_riskier 決定方向），
    composite = 各欄風險百分位均值；再疊 ETF 20 日報酬做市場印證。"""
    spec = config["def_fragility"]
    hi = spec["higher_is_riskier"]
    lo = spec["lower_is_riskier"]
    bands = spec["bands"]
    countries = {k: v for k, v in fundamentals.items() if isinstance(v, dict)}
    fields = hi + lo
    pools = {f: [c.get(f) for c in countries.values() if c.get(f) is not None]
             for f in fields}
    rows = []
    for name, c in countries.items():
        pcts, detail = [], {}
        for f in fields:
            v = c.get(f)
            if v is None or not pools[f]:
                continue
            pct = mk.percentile_rank(v, pools[f])
            if pct is None:
                continue
            risk_pct = pct if f in hi else 100.0 - pct
            pcts.append(risk_pct)
            detail[f] = {"value": v, "risk_pct": round(risk_pct, 1)}
        composite = round(sum(pcts) / len(pcts), 1) if pcts else None
        etf = c.get("etf")
        etf_ret20 = panel.ret(etf, 20) if etf and panel.m.prices.get(etf) else None
        band = band_for(composite, bands)
        rows.append({
            "country": name, "name_zh": c.get("name_zh", name), "etf": etf,
            "composite": composite, "band": band,
            "etf_ret20": None if etf_ret20 is None else round(etf_ret20, 5),
            "double_weak": bool(composite is not None and composite >= 55
                                and (etf_ret20 or 0) < 0),
            "detail": detail,
            "evidence": c.get("evidence_status", "P"),
        })
    rows.sort(key=lambda r: -(r["composite"] if r["composite"] is not None else -1))
    return rows
