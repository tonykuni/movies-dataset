#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Two PMI prints per economy that this AKShare actually has. Does not invent the rest."""
from __future__ import annotations

import json
import os
import socket
import sys
from datetime import datetime

HTTP_TIMEOUT = 30
PAIRS = (
    {"economy": "中國官方", "manufacturing": "macro_china_pmi", "services": "macro_china_pmi", "man_col": "制造业-指数", "srv_col": "非制造业-指数"},
    {"economy": "中國財新", "manufacturing": "macro_china_cx_pmi_yearly", "services": "macro_china_cx_services_pmi_yearly"},
    {"economy": "美國ISM", "manufacturing": "macro_usa_ism_pmi", "services": "macro_usa_ism_non_pmi"},
    {"economy": "美國Markit", "manufacturing": "macro_usa_pmi", "services": "macro_usa_services_pmi"},
    {"economy": "歐元區", "manufacturing": "macro_euro_manufacturing_pmi", "services": "macro_euro_services_pmi"},
)
ABSENT = ["日本", "英國", "德國", "台灣"]


def allowed() -> bool:
    return os.environ.get("VIA_CENTRAL_ENTRY") == "1" and os.environ.get("VIA_FROM_VCGC") == "YES"


def _patch_requests():
    import requests
    original = requests.get

    def limited(*args, **kwargs):
        kwargs.setdefault("timeout", HTTP_TIMEOUT)
        return original(*args, **kwargs)

    requests.get = limited
    return original


def _last(df, col=None):
    import pandas as pd
    date_col = next((c for c in df.columns if str(c) in ("日期", "月份", "时间") or "日期" in str(c)), df.columns[0])
    if col and col in df.columns:
        value_col = col
    else:
        prefer = [c for c in df.columns if any(k in str(c) for k in ("今值", "现值", "最新值"))]
        value_col = prefer[0] if prefer else [c for c in df.columns if c != date_col][0]
    work = df.copy()
    work["_d"] = work[date_col].astype(str)
    work[value_col] = pd.to_numeric(work[value_col], errors="coerce")
    ok = work.dropna(subset=[value_col]).sort_values("_d")
    if ok.empty:
        return None
    row = ok.iloc[-1]
    return {"date": row["_d"], "value": float(row[value_col])}


def _one(ak, fn, col=None):
    if not hasattr(ak, fn):
        return {"fn": fn, "state": "MISSING", "why": "function is not on this akshare"}
    try:
        point = _last(getattr(ak, fn)(), col)
    except Exception as exc:
        return {"fn": fn, "state": "FAIL", "why": type(exc).__name__}
    if point is None:
        return {"fn": fn, "state": "NODATA"}
    point.update({"fn": fn, "state": "LIVE"})
    return point


def probe() -> dict:
    socket.setdefaulttimeout(HTTP_TIMEOUT)
    try:
        import akshare as ak
    except ImportError:
        ak = None
    original = _patch_requests() if ak is not None else None
    rows = []
    try:
        if ak is None:
            rows = [{"economy": p["economy"], "state": "ABSENT", "why": "akshare is not installed"} for p in PAIRS]
        else:
            for pair in PAIRS:
                man = _one(ak, pair["manufacturing"], pair.get("man_col"))
                srv = _one(ak, pair["services"], pair.get("srv_col"))
                rows.append({"economy": pair["economy"], "manufacturing": man, "services": srv})
    finally:
        if original is not None:
            import requests
            requests.get = original
    return {
        "via": "vcgc",
        "door": "VDF_ENG114_PmiPair_v0100",
        "probed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "pairs": len(PAIRS),
        "absent_economies": ABSENT,
        "rows": rows,
        "us_owner": "FRED",
        "enter": "vcgc",
        "exit": "vcgc",
        "central": True,
        "intake_edited": False,
        "tree_edited": False,
        "do_not": [
            "invent a PMI function for an absent economy",
            "let akshare replace FRED",
            "edit intake macro_ssot",
            "wait forever on a proxy tunnel",
        ],
        "next": "none",
    }


def main() -> int:
    if not allowed():
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-pmipair through Invoke-VIAPython"}, ensure_ascii=False))
        return 2
    print(json.dumps(probe(), ensure_ascii=False, indent=1))
    return 0


def selftest() -> int:
    os.environ.pop("VIA_CENTRAL_ENTRY", None)
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = not allowed()
    os.environ["VIA_CENTRAL_ENTRY"] = "1"
    os.environ["VIA_FROM_VCGC"] = "YES"
    names = [p["manufacturing"] for p in PAIRS] + [p["services"] for p in PAIRS]
    ok = denied and allowed() and len(PAIRS) == 5 and "日本" in ABSENT and len(set(names)) == 9
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
