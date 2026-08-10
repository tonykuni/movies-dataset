# -*- coding: utf-8 -*-
"""CALIBRATE-13 flow_calibrate.py — optimize→test→debug→backtest→calibrate 迴圈(v0100R)。

README 流程:train/OOS 切分 → grid 掃描(window×kappa×min_tier)→ DEBUG 逐組記失敗 gate
→ best=train 通過且 ICIR 最高 → OOS 確認(G009)→ PROVED_VALID / NOT_VALID。
反證保證:synthetic.alpha=0 時必須 NOT_VALID。
"""
import json
from collections import Counter
from pathlib import Path

from flow_core import compute_fis, load_params, load_universe, TIER_ORDER
from flow_validate import evaluate

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUTP = ROOT / "data" / "output" / "calibration.json"


def _split_dates(panel, frac):
    dates = sorted({str(r["snapshot_date"]) for r in panel})
    k = max(1, int(len(dates) * frac))
    return set(dates[:k]), set(dates[k:])


def _rets_from_panel(panel):
    """#9 look-ahead shift:fwd = 下一日報酬;same = 當日報酬(G010 分解用)。"""
    by_t = {}
    for r in panel:
        by_t.setdefault(str(r["ticker"]), []).append(r)
    fwd, same = {}, {}
    for t, rows in by_t.items():
        rows = sorted(rows, key=lambda r: str(r["snapshot_date"]))
        for i in range(1, len(rows)):
            d0, d1 = str(rows[i - 1]["snapshot_date"]), str(rows[i]["snapshot_date"])
            try:
                r1 = float(rows[i]["close"]) / float(rows[i - 1]["close"]) - 1.0
            except Exception:
                continue
            fwd[(d0, t)] = r1
            same[(d1, t)] = r1
    return fwd, same


def _tier_filter(rows, min_tier):
    keep = TIER_ORDER.get(min_tier, 1)
    return [r for r in rows if TIER_ORDER.get(r["confidence"], -1) >= keep]


def calibrate(panel, params=None, write=True):
    p = params or load_params()
    uni = load_universe()
    cal = p.get("calibration", {})
    grid = cal.get("grid", {})
    train_d, oos_d = _split_dates(panel, float(cal.get("train_frac", 0.7)))
    fwd, same = _rets_from_panel(panel)
    combos, debug, best = [], [], None
    for W in grid.get("window", [20]):
        for K in grid.get("kappa", [1.5]):
            for MT in grid.get("min_tier", ["B"]):
                p2 = json.loads(json.dumps(p))
                p2["fis"]["window"] = W
                p2["fis"]["kappa"] = K
                rows = _tier_filter(compute_fis(panel, p2, uni), MT)
                tr = [r for r in rows if r["date"] in train_d]
                ev = evaluate(tr, fwd, same, p2)
                rec = {"window": W, "kappa": K, "min_tier": MT,
                       "train_passed": ev["passed"], "failed": ev["failed"],
                       "train_score": ev["metrics"]["icir"]}
                combos.append(rec)
                if not ev["passed"]:
                    debug.append({"combo": rec, "failed_gates": ev["failed"]})
                elif best is None or rec["train_score"] > best["train_score"]:
                    best = dict(rec, rows=rows)
    result = {"version": "v0100R", "n_combos": len(combos),
              "n_train_pass": sum(1 for c in combos if c["train_passed"]),
              "grid_log": combos}
    if best is None:
        cnt = Counter(g for d in debug for g in d["failed_gates"])
        result.update({"status": "NOT_VALID",
                       "reason": "全 grid 無組通過 train gates;最常失敗:%s" %
                                 ("、".join("%s×%d" % kv for kv in cnt.most_common(3)) or "無資料"),
                       "best": None})
    else:
        oos = [r for r in best.pop("rows") if r["date"] in oos_d]
        ev_oos = evaluate(oos, fwd, same, p)
        ic_oos = ev_oos["metrics"]["ic"]
        # G009:OOS 同號且顯著(t≥1.5 放寬於 train)
        if ic_oos > 0 and ev_oos["metrics"]["t"] >= 1.5:
            result.update({"status": "PROVED_VALID",
                           "reason": "train gates 全綠 + OOS 同號顯著(IC %.4f · t %.2f)" %
                                     (ic_oos, ev_oos["metrics"]["t"]),
                           "best": best, "oos": ev_oos["metrics"],
                           "calibrated_params": {"window": best["window"], "kappa": best["kappa"],
                                                 "min_tier": best["min_tier"]}})
        else:
            result.update({"status": "NOT_VALID",
                           "reason": "train 通過但 OOS 未確認(G009:IC %.4f · t %.2f)" %
                                     (ic_oos, ev_oos["metrics"]["t"]),
                           "best": best, "oos": ev_oos["metrics"]})
    if write:
        OUTP.parent.mkdir(parents=True, exist_ok=True)
        OUTP.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    return result
