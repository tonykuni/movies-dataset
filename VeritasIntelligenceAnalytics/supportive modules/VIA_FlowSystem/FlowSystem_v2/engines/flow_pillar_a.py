# -*- coding: utf-8 -*-
"""PILLARA-19 flow_pillar_a.py — Pillar A 測量校準(v0100R)。

VAL-G001:估計流量 vs 真值(reference_flows.json:ICI/issuer NAV/CFTC COT/AkShare)
rank-corr + 符號一致率。無 reference → UNCALIBRATED(系統降 NOT_SOLID,
標 signal indicative only — 不假裝校準過)。
"""
import json
from pathlib import Path

from flow_bridge import load_reference_flows
from flow_validate import rank_ic

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUTP = ROOT / "data" / "output" / "pillar_a.json"


def validate_a(fis_rows, write=True):
    ref = load_reference_flows()
    if not ref:
        result = {"version": "v0100R", "status": "UNCALIBRATED",
                  "reason": "data/input/reference_flows.json 不在位 — 真值源(ICI/issuer NAV/CFTC COT/AkShare)待接;signal indicative only"}
    else:
        refmap = {(str(r["snapshot_date"]), str(r["ticker"])): float(r["ref_flow"]) for r in ref}
        est, tru = [], []
        for r in fis_rows:
            k = (r["date"], r["ticker"])
            if k in refmap:
                est.append(r["flow_usd"])
                tru.append(refmap[k])
        if len(est) < 10:
            result = {"version": "v0100R", "status": "UNCALIBRATED",
                      "reason": "重疊樣本 %d < 10 — 真值覆蓋不足" % len(est)}
        else:
            rc = rank_ic(est, tru) or 0.0
            sign = sum(1 for a, b in zip(est, tru) if a * b > 0) / len(est)
            ok = rc >= 0.5 and sign >= 0.7
            result = {"version": "v0100R",
                      "status": "CALIBRATED" if ok else "MISCALIBRATED",
                      "rank_corr": round(rc, 3), "sign_agree": round(sign, 3),
                      "n": len(est),
                      "reason": "VAL-G001 %s(rank-corr %.3f · 符號一致 %.0f%%)" %
                                ("通過" if ok else "未過", rc, 100 * sign)}
    if write:
        OUTP.parent.mkdir(parents=True, exist_ok=True)
        OUTP.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    return result
