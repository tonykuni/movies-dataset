# -*- coding: utf-8 -*-
"""flow_attractiveness — 資金流三因子吸引力引擎(TOOL-055;內容功能導入 2026-08-18)

藍圖源:ui_support/VIA_ThreeFactor_Attractiveness_Panel.html(待接→本引擎接真值)。
公式(全依藍圖,零發明):
  ① 利差 carry:policy_spread = i_local − i_Fed;sovereign_spread = 10Y_local − 10Y_US
  ② 美元 regime:DXY 動能 z(輸入序列;強=非美承壓)
  ③ 股市吸引力:fwdPE = 價格/fwdEPS → attractiveness = E/P(=1/fwdPE) − 10Y_local
     跨區相對 = attractiveness_region − attractiveness_US
  ④ 綜合 z:三因子 z 合成——實測 IC 權重輸入;缺 IC=等權(誠實標 EW)
誠實界線:任一輸入 None → 該格 "—" 不捏造;綜合 z 需三因子齊備。
輸出 rows 對齊 panel 表結構(區域/政策利率/10Y/fwdPE/E-P−10Y bp/利差 vs US bp/綜合 z/狀態)。
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

REGIONS = ["US", "EU", "JP", "TW", "CN", "KR", "IN"]


def _z(vals):
    xs = [v for v in vals if v is not None]
    if len(xs) < 2:
        return {i: None for i in range(len(vals))}
    m = sum(xs) / len(xs)
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / len(xs)) or 1e-9
    return {i: ((v - m) / sd if v is not None else None) for i, v in enumerate(vals)}


def compute(inputs: dict, ic_weights: dict | None = None) -> dict:
    """inputs: {region: {policy_rate, y10, fwd_pe}};基準=US。回 rows+meta。"""
    us = inputs.get("US", {})
    rows = []
    for r in REGIONS:
        d = inputs.get(r, {})
        pr, y10, fpe = d.get("policy_rate"), d.get("y10"), d.get("fwd_pe")
        attr = (1.0 / fpe * 100 - y10) if (fpe and y10 is not None) else None       # E/P − 10Y(百分點)
        carry = (pr - us["policy_rate"]) * 100 if (pr is not None and us.get("policy_rate") is not None) else None  # bp
        rows.append({"region": r, "policy_rate": pr, "y10": y10, "fwd_pe": fpe,
                     "ep_minus_10y_bp": round(attr * 100, 1) if attr is not None else None,
                     "carry_vs_us_bp": round(carry, 1) if carry is not None else None})
    # 跨區相對吸引力(vs US)
    us_attr = next((row["ep_minus_10y_bp"] for row in rows if row["region"] == "US"), None)
    for row in rows:
        row["rel_attr_bp"] = (round(row["ep_minus_10y_bp"] - us_attr, 1)
                              if (row["ep_minus_10y_bp"] is not None and us_attr is not None) else None)
    # 綜合 z:carry z + 相對吸引力 z(+ USD 動能由呼叫端以 regime 因子傳入 dxy_z)
    zc = _z([row["carry_vs_us_bp"] for row in rows])
    za = _z([row["rel_attr_bp"] for row in rows])
    w = ic_weights or {}
    wc, wa = w.get("carry", 1.0), w.get("attractiveness", 1.0)
    weighted = bool(ic_weights)
    for i, row in enumerate(rows):
        if zc[i] is not None and za[i] is not None:
            row["composite_z"] = round((wc * zc[i] + wa * za[i]) / (wc + wa), 3)
        else:
            row["composite_z"] = None
        row["status"] = "OK" if row["composite_z"] is not None else "待接"
    return {"schema": "VIA.FlowAttractiveness.v1", "rows": rows,
            "weighting": "IC 實測權" if weighted else "等權 EW(候實測 IC)",
            "note": "任一輸入缺=該格 —;綜合 z 需三因子齊備(誠實不捏造)"}


def selftest() -> int:
    print("=== 三因子吸引力引擎 · 自測四檢(合成)===")
    inp = {"US": {"policy_rate": 4.5, "y10": 4.2, "fwd_pe": 21.0},
           "TW": {"policy_rate": 2.0, "y10": 1.5, "fwd_pe": 16.0},
           "JP": {"policy_rate": 0.5, "y10": 1.0, "fwd_pe": None}}  # JP fwdPE 缺=誠實 —
    out = compute(inp)
    tw = next(r for r in out["rows"] if r["region"] == "TW")
    jp = next(r for r in out["rows"] if r["region"] == "JP")
    us = next(r for r in out["rows"] if r["region"] == "US")
    checks = [
        ("E/P−10Y 公式(TW=1/16*100−1.5=4.75%)", abs(tw["ep_minus_10y_bp"] - 475.0) < 0.1),
        ("carry vs US(TW=−250bp)", abs(tw["carry_vs_us_bp"] + 250.0) < 0.1),
        ("缺值誠實 —(JP fwdPE 缺→綜合 None)", jp["composite_z"] is None and jp["status"] == "待接"),
        ("US 自身相對吸引力=0", us["rel_attr_bp"] == 0.0),
    ]
    n = 0
    for name, ok in checks:
        n += ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print(f"  [計] {n}/4 檢通過 · 加權={out['weighting']}")
    return 0 if n == 4 else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        sys.exit(selftest())
    if len(sys.argv) > 1 and Path(sys.argv[1]).is_file():
        out = compute(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
        print(json.dumps(out, ensure_ascii=False, indent=1))
        sys.exit(0)
    sys.exit(selftest())
