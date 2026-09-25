"""自建自練：引擎自我成長的訓練迴圈（核可制，可測學習曲線）。

流程：從資料自舉 → 產生關鍵字候選 → 人核可(嚴謹) → append-only 寫回 →
歸類率上升 → 再產生候選 → 再核可…… 每一輪都記錄，畫成學習曲線。

「自練」不是黑箱亂學：每個新詞都要人點頭(或高信心自動鎖定)，只增不減、可回溯。
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

import json
import os
import time


def train_round(records, cls, dim="product", auto_approve_score=None, approved=None):
    """跑一輪：分類 → 產候選 → 套用核可的 → 回傳本輪成果。

    approved：人工核可清單（每項 {bucket, term}）。
    auto_approve_score：高於此分數自動鎖定（None=全靠人工）。
    """
    from .classify import classify_all, seed_buckets_from_data
    from .keywords import generate_keyword_candidates, apply_approved

    seed_buckets_from_data(records, cls, dims=(dim,))
    before = classify_all(records, cls)["stats"].get(dim, {}).get("rate", 0.0)
    cands = generate_keyword_candidates(records, cls, dim=dim, min_count=2, min_score=0.6)

    to_apply = list(approved or [])
    if auto_approve_score is not None:
        for c in cands:
            if c["score"] >= auto_approve_score:
                to_apply.append({"bucket": c["bucket"], "term": c["term"]})

    # 補齊 apply_approved 需要的欄位（dim + 核可狀態）
    normalized = [{"dim": dim, "bucket": a["bucket"], "term": a["term"],
                   "status": "confirmed"} for a in to_apply]
    if normalized:
        apply_approved(cls, normalized)               # append-only 寫回詞庫
    after = classify_all(records, cls)["stats"].get(dim, {}).get("rate", 0.0)
    return {"before": before, "after": after, "candidates": cands,
            "applied": to_apply, "gain": round(after - before, 1)}


def run_training(records, dim="product", rounds=3, auto_approve_score=0.9,
                 ledger_path=None):
    """多輪自我成長，記錄學習曲線。回傳每輪 rate + 最終詞庫。"""
    cls = {dim: {}}
    curve = []
    for i in range(rounds):
        r = train_round(records, cls, dim=dim, auto_approve_score=auto_approve_score)
        curve.append({"round": i + 1, "rate": r["after"], "gain": r["gain"],
                      "learned": [f"{a['bucket']}←{a['term']}" for a in r["applied"]]})
        if ledger_path:
            _append_ledger(ledger_path, {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                         "dim": dim, **curve[-1]})
        if r["gain"] == 0 and i > 0:
            break                                     # 收斂：學不到新東西就停
    return {"curve": curve, "final_keywords": cls,
            "final_rate": curve[-1]["rate"] if curve else 0.0}


def _append_ledger(path, entry):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def curve_markdown(result):
    """把學習曲線印成表，證明『越練越準』。"""
    lines = ["| 輪次 | 歸類率 | 本輪提升 | 這輪學到 |", "|---|---|---|---|"]
    for c in result["curve"]:
        learned = "、".join(c["learned"][:4]) + ("…" if len(c["learned"]) > 4 else "") or "—"
        lines.append(f"| {c['round']} | {c['rate']}% | +{c['gain']} | {learned} |")
    lines.append(f"\n最終歸類率：**{result['final_rate']}%**（append-only，可回溯每輪學了什麼）")
    return "\n".join(lines)
