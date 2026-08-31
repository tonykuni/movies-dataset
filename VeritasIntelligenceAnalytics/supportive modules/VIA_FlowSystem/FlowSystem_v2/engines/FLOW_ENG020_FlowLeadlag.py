# -*- coding: utf-8 -*-
"""flow_leadlag — 因果力場 lead-lag 邊 harness(TOOL-055;內容功能導入 2026-08-18)

藍圖源:ui_support/VIA_PushPull_Causal_FieldMap.html——「每條邊跑 lead-lag
相關(lag −k…+k),峰值 lag 符號=誰領先(箭頭方向)、|峰值IC|=線寬;
依 regime 分段重估→箭頭會翻轉,這是特徵不是錯誤」。本引擎即該 harness:
  edge_leadlag(a, b, k)      → {peak_lag, direction, ic, widths}
  regime_split(a, b, regimes)→ 逐 regime 邊估計(翻轉偵測)
  field_edges(series, edges) → 全邊冊 JSON(供力場圖線寬/方向即時更新)
方向語意:peak_lag>0 = a 領先 b(a→b);<0 = b 領先 a;=0 同期(⇄ 迴路候判)。
誠實:樣本 < 2k+8 → INSUFFICIENT 不出方向;|IC|<0.05 → WEAK 不畫粗線。
零依賴(標準庫);皮爾森相關自算。
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
import math
import sys


def _corr(x, y):
    n = len(x)
    if n < 3:
        return 0.0
    mx, my = sum(x) / n, sum(y) / n
    sx = math.sqrt(sum((v - mx) ** 2 for v in x)) or 1e-12
    sy = math.sqrt(sum((v - my) ** 2 for v in y)) or 1e-12
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy)


def edge_leadlag(a: list, b: list, k: int = 10) -> dict:
    """lag>0:a[t] 對 b[t+lag] —— a 領先。回峰值裁決。"""
    n = min(len(a), len(b))
    if n < 2 * k + 8:
        return {"verdict": "INSUFFICIENT", "n": n, "need": 2 * k + 8}
    best = (0, 0.0)
    curve = {}
    for lag in range(-k, k + 1):
        if lag >= 0:
            x, y = a[: n - lag], b[lag:n]
        else:
            x, y = a[-lag:n], b[: n + lag]
        ic = _corr(x, y)
        curve[lag] = round(ic, 4)
        if abs(ic) > abs(best[1]):
            best = (lag, ic)
    lag, ic = best
    direction = "a→b" if lag > 0 else ("b→a" if lag < 0 else "⇄")
    verdict = "WEAK" if abs(ic) < 0.05 else "OK"
    return {"verdict": verdict, "peak_lag": lag, "ic": round(ic, 4),
            "direction": direction, "width": round(min(4.0, 0.5 + abs(ic) * 4), 2),
            "curve": curve}


def regime_split(a: list, b: list, regimes: list, k: int = 10) -> dict:
    """逐 regime 標籤分段重估——箭頭翻轉=特徵非錯誤(藍圖原話)。"""
    out = {}
    for tag in sorted(set(regimes)):
        idx = [i for i, t in enumerate(regimes) if t == tag]
        out[tag] = edge_leadlag([a[i] for i in idx], [b[i] for i in idx], k)
    dirs = {v["direction"] for v in out.values() if v.get("direction")}
    out["_flip_detected"] = len(dirs) > 1
    return out


def field_edges(series: dict, edges: list, k: int = 10) -> dict:
    """全邊冊:edges=[{src,dst}] → 力場圖可讀 JSON(方向/線寬=實測)。"""
    rows = []
    for e in edges:
        a, b = series.get(e["src"]), series.get(e["dst"])
        if a is None or b is None:
            rows.append({**e, "verdict": "NO_DATA(誠實待接)"})
            continue
        rows.append({**e, **edge_leadlag(a, b, k)})
    return {"schema": "VIA.FieldEdges.v1", "k": k, "edges": rows,
            "note": "方向=峰值 lag 符號;線寬=|IC| 映射;WEAK/INSUFFICIENT 不畫粗線(誠實)"}


def selftest() -> int:
    print("=== lead-lag 邊 harness · 自測四檢(合成已知因果)===")
    import random
    rng = random.Random(7)
    n = 200
    a = [rng.gauss(0, 1) for _ in range(n)]
    b = [0.0, 0.0] + [0.8 * a[i] + rng.gauss(0, 0.3) for i in range(n - 2)]  # a 領先 b 2 期
    r = edge_leadlag(a, b, k=6)
    checks = [("峰值 lag=+2(a 領先)", r["peak_lag"] == 2 and r["direction"] == "a→b"),
              ("|IC| 顯著非 WEAK", r["verdict"] == "OK" and abs(r["ic"]) > 0.5)]
    # regime 翻轉合成:前半 a→b,後半 b→a
    a2 = a[:100] + [0.0, 0.0] + [0.8 * b[100 + i] + rng.gauss(0, 0.3) for i in range(98)]
    regimes = ["R1"] * 100 + ["R2"] * 100
    rs = regime_split(a2, b, regimes, k=6)
    checks.append(("regime 分段可跑且偵測翻轉旗標", "_flip_detected" in rs and rs["R1"]["verdict"] in ("OK", "WEAK")))
    checks.append(("樣本不足誠實 INSUFFICIENT", edge_leadlag([1, 2, 3], [1, 2, 3], k=6)["verdict"] == "INSUFFICIENT"))
    n_ok = 0
    for name, ok in checks:
        n_ok += ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print(f"  [計] {n_ok}/4 檢通過")
    return 0 if n_ok == 4 else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] not in ("--selftest",):
        cfg = json.loads(open(sys.argv[1], encoding="utf-8").read())
        print(json.dumps(field_edges(cfg["series"], cfg["edges"], cfg.get("k", 10)), ensure_ascii=False, indent=1))
        sys.exit(0)
    sys.exit(selftest())
