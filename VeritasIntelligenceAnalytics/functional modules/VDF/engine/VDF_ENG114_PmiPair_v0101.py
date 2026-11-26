#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:GOV-PARAM:v0100] VDF_ENG114_PmiPair v0101 = VDF_ENG114_PmiPair_v0100.py 全文 + 參數解耦(產生:VIA_GovernanceApply v0100;操作員 2026-11-25「全做」):模組層 1 個參數改讀 VDF 參數冊 engine_params,預設 = 原值;本機路徑改自 VIA 根解析。其餘位元組與前版相同。
"""Two PMI prints per economy that this AKShare actually has. Does not invent the rest."""
from __future__ import annotations

# ===== [VIA:GOV-PARAM:v0100] 參數解耦橋(值在 VDF_Unified_Params 尾版 engine_params;缺冊 / 缺鍵 = 原值,零行為變更) =====
_VDF_GOV_FAMILY = "VDF_ENG114_PmiPair"
_VDF_GOV_BOOK = None


def _VDF_VIA_ROOT_REL(rel):
    """本機路徑改自 VIA 根解析:環境變數 VIA_ROOT(資料根)先,再往上找含 supportive modules 的程式根。"""
    import os as _gp_os
    from pathlib import Path as _gp_P
    roots = [_gp_P(_gp_os.environ["VIA_ROOT"])] if _gp_os.environ.get("VIA_ROOT") else []
    _gp_p = _gp_P(__file__).resolve()
    while _gp_p.parent != _gp_p:
        if (_gp_p / "supportive modules").is_dir():
            roots.append(_gp_p)
            break
        _gp_p = _gp_p.parent
    for _gp_r in roots:
        if (_gp_r / rel).exists():
            return str(_gp_r / rel)
    return str((roots[-1] if roots else _gp_P(__file__).resolve().parent) / rel)


def _VDF_PARAM(name, default):
    """讀 VDF 參數冊尾版 engine_params[家族][名];讀不到 = 原值(誠實:不補 0、不編值)。"""
    global _VDF_GOV_BOOK
    try:
        if _VDF_GOV_BOOK is None:
            import json as _gp_json
            from pathlib import Path as _gp_P
            _gp_here = _gp_P(__file__).resolve().parent
            _gp_hits = sorted({q for d in (_gp_here, _gp_here.parent) for q in d.glob("VDF_Unified_Params_v*.json")}, key=lambda q: q.name)
            _VDF_GOV_BOOK = ((_gp_json.loads(_gp_hits[-1].read_text(encoding="utf-8")).get("engine_params") or {})
                             .get(_VDF_GOV_FAMILY) or {}) if _gp_hits else {}
        ent = _VDF_GOV_BOOK.get(name)
        if not isinstance(ent, dict):
            return default
        if "via_root_rel" in ent:
            return _VDF_VIA_ROOT_REL(ent["via_root_rel"])
        if "regex" in ent:
            import re as _gp_re
            return _gp_re.compile(ent["regex"])
        if "value" not in ent:
            return default
        v = ent["value"]
        return type(default)(v) if isinstance(default, (tuple, frozenset, set)) and isinstance(v, list) else v
    except Exception:
        return default
# ===== [VIA:GOV-PARAM:END] =====
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
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import json
import os
import socket
import sys
from datetime import datetime

HTTP_TIMEOUT = _VDF_PARAM("HTTP_TIMEOUT", 30)
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
