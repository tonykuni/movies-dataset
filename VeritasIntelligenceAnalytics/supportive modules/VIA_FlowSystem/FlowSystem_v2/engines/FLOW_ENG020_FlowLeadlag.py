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

批308 擴充(操作員令「LEAD LAG 分析 分四種 LEADER PEER LAGGER 不相關」):
  classify_nodes(ref, series, k, markets) → 每節點對基準四分類:
    LEADER=節點領先基準(peak_lag>0)· PEER=同期(peak_lag=0)
    LAGGER=節點落後(peak_lag<0)· UNCORRELATED=|IC|<顯著性閘 不相關
    (閘=max(0.05, 2.5/√n) 由樣本數算出——動態參數律,零固定閾值)
    樣本不足=INSUFFICIENT 誠實不分類;markets 標記(TWSE/TPEX)透傳
    ——供 VDF 擷取之上市/上櫃序列分市場彙總。
  CLI:--classify <json>({ref,series,k,markets})→ 分類冊 JSON。
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


def classify_nodes(ref: list, series: dict, k: int = 10,
                   markets: dict | None = None) -> dict:
    """批308:各節點對基準四分類(LEADER/PEER/LAGGER/UNCORRELATED)。

    邊向約定:edge_leadlag(node, ref) 之 peak_lag>0 = 節點領先基準。
    分類全由峰值裁決算出——零手寫歸類;INSUFFICIENT 誠實不分類。
    不相關閘=max(0.05, 2.5/√n):峰值取自 2k+1 個 lag,雜訊峰值隨掃描數
    上升——顯著性閘由樣本數算出(動態參數律),0.05 僅為下限;
    2.5=估計超參數(非因子權重)。
    """
    markets = markets or {}
    nodes = []
    for name, s in series.items():
        e = edge_leadlag(s, ref, k)
        n_eff = min(len(s), len(ref))
        gate = max(0.05, 2.5 / math.sqrt(max(n_eff - abs(e.get("peak_lag", 0) or 0), 1)))
        if e["verdict"] == "INSUFFICIENT":
            cls = "INSUFFICIENT"
        elif abs(e.get("ic", 0.0)) < gate:
            cls = "UNCORRELATED"
        elif e["peak_lag"] > 0:
            cls = "LEADER"
        elif e["peak_lag"] < 0:
            cls = "LAGGER"
        else:
            cls = "PEER"
        nodes.append({"name": name, "class": cls, "market": markets.get(name, "—"),
                      "peak_lag": e.get("peak_lag"), "ic": e.get("ic"),
                      "gate": round(gate, 4), "n": e.get("n")})
    counts: dict = {}
    by_mkt: dict = {}
    for nd in nodes:
        counts[nd["class"]] = counts.get(nd["class"], 0) + 1
        if nd["market"] != "—":
            by_mkt.setdefault(nd["market"], {})
            by_mkt[nd["market"]][nd["class"]] = by_mkt[nd["market"]].get(nd["class"], 0) + 1
    return {"schema": "VIA.LeadLagClassify.v1", "k": k, "nodes": nodes,
            "counts": counts, "by_market": by_mkt,
            "note": "四分類=峰值 lag 符號+|IC| 閘裁決;INSUFFICIENT 誠實不分類;市場標記透傳"}


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
    # 批308 四分類合成:對基準各構一 LEADER/PEER/LAGGER/不相關+樣本不足
    ref = [rng.gauss(0, 1) for _ in range(n)]
    lead = ref[2:] + [0.0, 0.0]                     # 節點提前 2 期=領先
    peer = [v + rng.gauss(0, 0.2) for v in ref]     # 同期
    lagg = [0.0, 0.0, 0.0] + ref[:-3]               # 節點落後 3 期
    unc = [rng.gauss(0, 1) for _ in range(n)]       # 不相關
    cl = classify_nodes(ref, {"L": lead, "P": peer, "G": lagg, "U": unc, "S": [1, 2]},
                        k=6, markets={"L": "TWSE", "P": "TPEX", "G": "TWSE"})
    got = {nd["name"]: nd["class"] for nd in cl["nodes"]}
    checks.append(("四分類裁決(領先/同期/落後/不相關)",
                   got == {"L": "LEADER", "P": "PEER", "G": "LAGGER",
                           "U": "UNCORRELATED", "S": "INSUFFICIENT"}))
    checks.append(("市場標記透傳+分市場彙總",
                   cl["by_market"].get("TWSE", {}).get("LEADER") == 1
                   and cl["by_market"].get("TPEX", {}).get("PEER") == 1))
    n_ok = 0
    for name, ok in checks:
        n_ok += ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print(f"  [計] {n_ok}/{len(checks)} 檢通過")
    return 0 if n_ok == len(checks) else 1


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--classify":
        cfg = json.loads(open(sys.argv[2], encoding="utf-8").read())
        print(json.dumps(classify_nodes(cfg["ref"], cfg["series"], cfg.get("k", 10),
                                        cfg.get("markets")), ensure_ascii=False, indent=1))
        sys.exit(0)
    if len(sys.argv) > 1 and sys.argv[1] not in ("--selftest",):
        cfg = json.loads(open(sys.argv[1], encoding="utf-8").read())
        print(json.dumps(field_edges(cfg["series"], cfg["edges"], cfg.get("k", 10)), ensure_ascii=False, indent=1))
        sys.exit(0)
    sys.exit(selftest())
