# -*- coding: utf-8 -*-
"""
regime.py — M28_RegimeEngine：規則式 Regime 判讀（可稽核基線）
=============================================================================
MODULE M28_RegimeEngine
  [MCFL-M28-C28-F280] classify_regime — SSOT def_regimes 規則評分 + 信心

設計立場：規則全在 config（SSOT），每條 signal 的實際值/門檻/命中與否
全量輸出 → 惡魔驗證可逐條覆核。HMM/MS-VAR 屬 Tier-2 升級（見 SSOT
ModuleRegistry），必須先打贏這個可稽核基線才能取代它（反循環紀律）。
"""
from __future__ import annotations

from .factors import resolve_indicator

_OPS = {
    ">": lambda a, b: a > b,
    "<": lambda a, b: a < b,
    ">=": lambda a, b: a >= b,
    "<=": lambda a, b: a <= b,
}


def _rule_score_at(panel, spec, end, scores_at):
    """單日規則分數；end=None 為當日。回傳 (score, detail)。"""
    total_w, hit_w, detail = 0.0, 0.0, []
    for sig in spec["signals"]:
        w = float(sig.get("weight", 1.0))
        total_w += w
        actual = resolve_indicator(panel, sig["id"], end=end, scores=scores_at)
        op = _OPS[sig["op"]]
        hit = bool(actual is not None and op(actual, sig["value"]))
        if hit:
            hit_w += w
        detail.append({"id": sig["id"], "op": sig["op"],
                       "threshold": sig["value"],
                       "actual": None if actual is None else round(actual, 5),
                       "weight": w, "hit": hit})
    return (hit_w / total_w if total_w > 0 else 0.0), detail


def classify_regime(panel, config, scores_risk, scores_history=None):
    """[MCFL-M28-C28-F280]
    scores_risk: {score_id: risk_0_100}，供 score_* 指標引用。
    scores_history: {score_id: [risk...]}（尾端對齊當日），供平滑回看。

    平滑（遲滯哲學，對齊 SectorWhale I2）：regime 分數 = 近 K 日規則分數均值
    （K=def_regime_smoothing_days，預設 5）。單日單窗判讀對商品/匯率這類
    高波動腿太脆：腿在門檻邊緣閃爍會把狀態切碎。逐訊號證據仍輸出當日值。"""
    smooth = int(config.get("def_regime_smoothing_days", 5))
    n = panel.n_obs()
    ranked = []
    for spec in config["def_regimes"]:
        day_scores = []
        detail_today = None
        for b in range(smooth):
            end = n - 1 - b
            if end < 0:
                break
            scores_at = scores_risk
            if b > 0 and scores_history:
                scores_at = {}
                for sid, hist in scores_history.items():
                    if hist and len(hist) > b and hist[-1 - b] is not None:
                        scores_at[sid] = hist[-1 - b]
            s, detail = _rule_score_at(panel, spec, end, scores_at)
            if b == 0:
                detail_today = detail
            day_scores.append(s)
        score = sum(day_scores) / len(day_scores) if day_scores else 0.0
        ranked.append({"id": spec["id"], "name_zh": spec["name_zh"],
                       "score": round(score, 4),
                       "score_today": round(day_scores[0], 4) if day_scores else 0.0,
                       "smooth_days": len(day_scores),
                       "signals": detail_today or []})

    ranked.sort(key=lambda r: -r["score"])
    total = sum(r["score"] for r in ranked)
    top = ranked[0] if ranked else None
    confidence = round(top["score"] / total, 4) if (top and total > 0) else 0.0
    runner_up = ranked[1] if len(ranked) > 1 else None
    return {
        "mcfl": "MCFL-M28-C28-F280",
        "top": top,
        "confidence": confidence,
        "runner_up": ({"id": runner_up["id"], "name_zh": runner_up["name_zh"],
                       "score": runner_up["score"]} if runner_up else None),
        "ranked": [{"id": r["id"], "name_zh": r["name_zh"], "score": r["score"]}
                   for r in ranked],
        "detail": ranked,
        "evidence": "Der", "truth_tier": "T3",
        "note": "規則式基線；分數=近K日(命中權重/總權重)均值（遲滯平滑），"
                "信心=Top/Σ全體；signals 為當日逐訊號證據",
    }
