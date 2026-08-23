# -*- coding: utf-8 -*-
"""VDF-FLOW-GRID-22 flow_grid.py — Region×Sector 網格 + Fidelity 評分卡(v0100R)。

README v0104:US 列 direct(XL* 直接讀);其餘區列 proxy = 區域錨點 baseline × US-sector tilt;
fidelity 評分卡 10 類(asset_class×backing),weak/blind 類明標需非 ETF 真值佐證。
"""
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
import statistics
from pathlib import Path

from flow_core import load_universe
from flow_roles import fidelity_classes

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUTP = ROOT / "data" / "output" / "grid.json"

SECTORS = ["Tech", "Financials", "Health", "Discretionary", "Staples", "Energy",
           "Industrials", "Materials", "Utilities", "RealEstate", "Comm"]
REGIONS = ["US", "Europe", "Japan", "China", "Taiwan", "Korea", "EM"]

ADVICE = {
    "cash/physical": "資金停泊風向標;直接可信",
    "gold/physical": "避險量能;直接可信",
    "bond/physical": "利率/信用流;直接可信",
    "equity/physical": "核心流;fidelity 最高",
    "crypto/physical": "現貨 ETF 申贖直讀",
    "crypto/futures": "僅作 positioning;需鏈上真值佐證",
    "commodity/futures": "血統=期貨;需 CFTC COT 佐證",
    "fx/futures": "positioning 專用;不進現貨池",
    "vol/futures": "衰減結構;僅短線情緒",
    "equity/leveraged": "槓桿重置噪音;打折使用",
}


def _last_fis(rows):
    last = {}
    for r in rows or []:
        cur = last.get(r["ticker"])
        if cur is None or r["date"] > cur["date"]:
            last[r["ticker"]] = r
    return {t: r["fis"] for t, r in last.items()}


def build_grid(rows, write=True):
    uni = load_universe()
    fis = _last_fis(rows)
    # US sector tilt(XL* 直接)
    sec_map = {}
    for t, u in uni.items():
        if u.get("sector") and t in fis:
            sec_map.setdefault(u["sector"], []).append(fis[t])
    us_tilt = {s: statistics.fmean(v) for s, v in sec_map.items() if v}
    # 區域錨點 baseline
    reg_map = {}
    for t, u in uni.items():
        if t in fis:
            reg_map.setdefault(u.get("region", "US"), []).append(fis[t])
    base = {r: statistics.fmean(v) for r, v in reg_map.items() if v}
    grid_rows = []
    for reg in REGIONS:
        direct = reg == "US"
        anchor = base.get(reg, 0.0)
        cells = []
        for s in SECTORS:
            tilt = us_tilt.get(s, 0.0)
            cells.append(tilt if direct else round(0.5 * anchor + 0.5 * tilt, 2))
        grid_rows.append({"region": reg, "direct": direct, "cells": cells})
    fid_rows = []
    for cls, members in sorted(fidelity_classes(uni).items()):
        fids = sorted(m["fidelity"] for m in members)
        med = fids[len(fids) // 2]
        roles = {m["monitor_role"] for m in members}
        live = [fis[m["ticker"]] for m in members if m["ticker"] in fis]
        fid_rows.append({"cls": cls, "median_fidelity": med,
                         "backing_role": "/".join(sorted(roles)),
                         "live_fis": round(statistics.fmean(live), 1) if live else None,
                         "n": len(members),
                         "advice": ADVICE.get(cls, "一般監控")})
    result = {"version": "v0100R",
              "region_sector": {"sectors": SECTORS, "rows": grid_rows,
                                "note": "proxy = 0.5×區域錨點 + 0.5×US-sector tilt(v0100R 簡式;原式到件替換)"},
              "fidelity": fid_rows}
    if write:
        OUTP.parent.mkdir(parents=True, exist_ok=True)
        OUTP.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    return result
