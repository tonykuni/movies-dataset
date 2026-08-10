# -*- coding: utf-8 -*-
"""VDF-FLOW-CORE-11 flow_core.py — FIS 強度 + 雙估計器信任 + 聚合(v0100R 重建版)。

v0100R:依 FlowSystem_v2/README.md(至 v0120)規格重建;原 session 檔到件時依整合去重裁定替換。
硬化(README v0109):#1 分割守衛 · #7 新生排除 · #13 z 外露 · #14 權重上限 · #2 stale-shares 雙估計器。
"""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CFG = ROOT / "config"

TIER_ORDER = {"A": 3, "B": 2, "C": 1, "D": 0}


def load_json(p, default=None):
    p = Path(p)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8-sig"))
        except Exception:
            return default
    return default


def load_params():
    return load_json(CFG / "params.json", {}) or {}


def load_universe():
    j = load_json(CFG / "universe.json", {}) or {}
    return {e["ticker"]: e for e in j.get("etfs", [])}


def _mean(xs):
    xs = [x for x in xs if x is not None and math.isfinite(x)]
    return sum(xs) / len(xs) if xs else 0.0


def _std(xs):
    xs = [x for x in xs if x is not None and math.isfinite(x)]
    if len(xs) < 2:
        return 0.0
    m = sum(xs) / len(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def _san(x):
    """#8 NaN/Inf 消毒。"""
    try:
        x = float(x)
        return x if math.isfinite(x) else None
    except Exception:
        return None


def compute_fis(panel, params=None, universe=None):
    """panel: [{snapshot_date,ticker,close,shares_out,aum_reported?}] →
    rows: [{date,ticker,fis,flow_z,flow_usd,confidence,corp_action,conflict}]。
    流量主估計 = Δshares × close;副估計 = ΔAUM − ret×AUM_prev(在 aum_reported 時);
    衝突(同日兩估計符號相反且皆大)→ confidence 降級 CONFLICT。"""
    p = params or load_params()
    fisP = p.get("fis", {})
    W = int(fisP.get("window", 20))
    kappa = float(fisP.get("kappa", 1.5))
    buf = int(fisP.get("inception_buffer", 20))
    by_t = {}
    for r in panel:
        by_t.setdefault(str(r.get("ticker")), []).append(r)
    out = []
    for t, rows in by_t.items():
        rows = sorted(rows, key=lambda r: str(r.get("snapshot_date")))
        flows = []
        for i, r in enumerate(rows):
            close = _san(r.get("close"))
            sh = _san(r.get("shares_out"))
            if close is None or sh is None:
                flows.append(None)
                continue
            if i == 0:
                flows.append(0.0)
                continue
            p_close = _san(rows[i - 1].get("close")) or close
            p_sh = _san(rows[i - 1].get("shares_out")) or sh
            d_sh = sh - p_sh
            ret = (close / p_close - 1.0) if p_close else 0.0
            corp = False
            # #1 分割守衛:(1+Δshares%)·(1+ret) ≈ 1 → 分割簽名,d_shares 歸零
            if p_sh > 0 and abs((sh / p_sh) * (1.0 + ret) - 1.0) < 0.02 and abs(sh / p_sh - 1.0) > 0.2:
                d_sh = 0.0
                corp = True
            flow_usd = d_sh * close
            conflict = False
            aum = _san(r.get("aum_reported"))
            p_aum = _san(rows[i - 1].get("aum_reported"))
            if aum is not None and p_aum is not None and p_aum > 0:
                flow2 = aum - p_aum * (1.0 + ret)
                big = max(abs(flow_usd), abs(flow2)) > 0.002 * p_aum
                if big and flow_usd * flow2 < 0:
                    conflict = True  # #2 stale-shares:兩估計大而反向
            flows.append({"flow_usd": flow_usd, "corp": corp, "conflict": conflict,
                          "aum": aum if aum is not None else sh * close})
        for i, r in enumerate(rows):
            f = flows[i]
            if f is None or isinstance(f, float):
                continue
            win = [x["flow_usd"] for x in flows[max(1, i - W + 1):i + 1]
                   if isinstance(x, dict)]
            mu, sd = _mean(win), _std(win)
            z = (f["flow_usd"] - mu) / sd if sd > 1e-12 else 0.0
            conf = "A"
            if i < buf:
                conf = "D"      # #7 新生/清算排除
            elif f["conflict"]:
                conf = "CONFLICT"
            elif len(win) < max(5, W // 2):
                conf = "C"
            out.append({"date": str(r.get("snapshot_date")), "ticker": t,
                        "fis": round(100.0 * math.tanh(z / kappa), 2),
                        "flow_z": round(z, 4),          # #13 z 外露
                        "flow_usd": round(f["flow_usd"], 2),
                        "aum": round(f["aum"], 2),
                        "confidence": conf,
                        "corp_action": f["corp"], "conflict": f["conflict"]})
    return out


def role_gate(rows, universe=None):
    """monitor_role 閘門:期貨/FX positioning 不進現貨流量池。"""
    uni = universe or load_universe()
    return [r for r in rows if (uni.get(r["ticker"], {}).get("monitor_role", "spot")) == "spot"]


def bucket_fis(rows, key_fn, params=None, universe=None):
    """聚合:AUM 加權 + #14 權重上限 weight_cap;confidence D/CONFLICT 不進 A/B 聚合。"""
    p = params or load_params()
    cap = float(p.get("fis", {}).get("weight_cap", 0.25))
    uni = universe or load_universe()
    groups = {}
    for r in role_gate(rows, uni):
        if r["confidence"] in ("D", "CONFLICT"):
            continue
        k = key_fn(r, uni.get(r["ticker"], {}))
        if k is None:
            continue
        groups.setdefault(k, []).append(r)
    out = {}
    for k, rs in groups.items():
        tot = sum(x["aum"] for x in rs) or 1.0
        ws = [min(cap, x["aum"] / tot) for x in rs]
        wt = sum(ws) or 1.0
        out[k] = round(sum(w * x["fis"] for w, x in zip(ws, rs)) / wt, 2)
    return out


def gram(rows, params=None, universe=None):
    """GRAM 雙形(README v0105):標準化 tanh 版 + 原始 net$/pool 版;皆過 role 閘門。"""
    p = params or load_params()
    uni = universe or load_universe()
    gk = float(p.get("gram", {}).get("kappa", 1.5))
    th = float(p.get("gram", {}).get("raw_threshold", 0.05))
    tf = bucket_fis(rows, lambda r, u: "T%d" % u.get("risk_tier", 3), p, uni)
    hi = _mean([tf.get("T3"), tf.get("T4")])
    lo = _mean([tf.get("T1"), tf.get("T2")])
    score = round(100.0 * math.tanh(((hi - lo) / 2.0) / (gk * 50.0)), 2)
    pool = sum(r["aum"] for r in role_gate(rows, uni)) or 1.0
    net_hi = sum(r["flow_usd"] for r in role_gate(rows, uni)
                 if uni.get(r["ticker"], {}).get("risk_tier", 3) >= 3)
    net_lo = sum(r["flow_usd"] for r in role_gate(rows, uni)
                 if uni.get(r["ticker"], {}).get("risk_tier", 3) <= 2)
    raw = (net_hi - net_lo) / pool
    regime = "RISK_ON" if raw > th else ("RISK_OFF" if raw < -th else "NEUTRAL")
    return {"gram_score": score, "gram_raw": round(raw, 4), "regime": regime,
            "tier_fis": tf}


def roro(rows, params=None, universe=None):
    """RORO 單針:GRAM 標準化分數映射 0-100(50=中性)。"""
    g = gram(rows, params, universe)
    return {"roro": round(50.0 + g["gram_score"] / 2.0, 1), **g}


def snapshot(rows, params=None, universe=None):
    """最新快照:per-ticker 最末日 FIS、bucket、RORO、regime、輕量補強欄。"""
    uni = universe or load_universe()
    last = {}
    for r in rows:
        cur = last.get(r["ticker"])
        if cur is None or r["date"] > cur["date"]:
            last[r["ticker"]] = r
    per = sorted(last.values(), key=lambda r: -abs(r["fis"]))
    stressed = sum(1 for r in per if abs(r["fis"]) > 60) / (len(per) or 1)
    return {"per_ticker": per,
            "bucket": bucket_fis(rows, lambda r, u: u.get("risk_bucket"), params, uni),
            "asset_class": bucket_fis(rows, lambda r, u: u.get("asset_class"), params, uni),
            **roro(rows, params, uni),
            "regime_market": "STRESSED" if stressed > 0.3 else ("ELEVATED" if stressed > 0.15 else "CALM"),
            "non_usd_n": sum(1 for r in per if uni.get(r["ticker"], {}).get("currency", "USD") != "USD"),
            "region_semantics": "exposure_not_origin"}
