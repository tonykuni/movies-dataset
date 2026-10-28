#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Same tab store. The engine tree and the database root may be the same path or two paths."""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0111] 最新有版號的正本加速器(動態取最高 VeritasCeleritas_v####;退回鎖版 v1141)· 正本網路工具 VeritasAegisNexus_v1652(找不到 = 不改任何行為) =====
import importlib as _cb_il
import re as _cb_re
import sys as _cb_sys
from pathlib import Path as _cb_Path
_ACCEL, _ACCEL_VER = None, ""
_cb_p = _cb_Path(__file__).resolve()
while _cb_p.parent != _cb_p:
    if (_cb_p / "supportive modules").is_dir():
        _cb_sup = _cb_p / "supportive modules"
        _cb_c = sorted(list(_cb_sup.glob("VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")) + list(_cb_sup.glob("*/VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")),
                       key=lambda x: int(_cb_re.search(r"_v(\d{4})", x.name).group(1)))
        for _cb_d in [str(_cb_sup)] + ([str(_cb_c[-1].parent)] if _cb_c else []) + [str(x.parent) for x in list(_cb_sup.glob("*/VeritasAegisNexus_v1652.py"))[:1]]:
            if _cb_d not in _cb_sys.path:
                _cb_sys.path.insert(0, _cb_d)
        if _cb_c:
            try:
                _ACCEL, _ACCEL_VER = _cb_il.import_module(_cb_c[-1].stem), _cb_c[-1].stem
            except Exception:  # noqa: BLE001
                _ACCEL = None
        break
    _cb_p = _cb_p.parent
if _ACCEL is None:
    try:
        import VeritasCeleritas_v1141 as _ACCEL  # noqa: F401  退回鎖版
        _ACCEL_VER = "VeritasCeleritas_v1141"
    except Exception:  # noqa: BLE001
        _ACCEL = None


def _net():
    """正本網路工具(只在需要出網時載入;本引擎不出網)。"""
    try:
        import VeritasAegisNexus_v1652 as _NET  # noqa: WPS433
        return _NET
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:ACCEL-BRIDGE:END] =====

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
import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _prior():
    spec = importlib.util.spec_from_file_location("tab_v0100", HERE / "VRN_ENG109_TabStore_v0100.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def place() -> dict:
    prior = _prior()
    engine = HERE
    data = prior.choose_root()
    cloud = prior.cloud_of(data)
    try:
        same = data.resolve().is_relative_to(engine.resolve().parents[1])
    except Exception:
        same = False
    return {
        "engine": str(engine),
        "data": str(data),
        "same": same,
        "cloud": cloud,
        "off_pc": cloud != "local",
    }


def run() -> dict:
    prior = _prior()
    where = place()
    link = prior.probe(Path(where["data"]))
    card = prior.run()
    card["door"] = "VRN_ENG109_TabStore_v0101"
    card["engine"] = where["engine"]
    card["data"] = where["data"]
    card["same"] = where["same"]
    card["cloud"] = link["cloud"]
    card["linked"] = link["linked"]
    card["off_pc"] = where["off_pc"]
    card["off_pc_means"] = "the last synced cloud copy, not the powered-off computer"
    return card


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    print(json.dumps(run(), ensure_ascii=False, indent=1))
    return 0


def selftest() -> int:
    prior = _prior()
    own = place()
    os.environ["VIA_VRN_DATA"] = r"C:\Users\tonyk\OneDrive\VIA-DATA"
    split = place()
    os.environ["VIA_VRN_DATA"] = r"C:\temp\via-local"
    plain = place()
    os.environ.pop("VIA_VRN_DATA", None)
    rejected = prior.store({"basic": {}, "page1": {}, "financial": []}, Path("/tmp/vrn_tab_v0101"))
    ok = (
        own["same"] is True
        and split["same"] is False
        and split["cloud"] == "onedrive"
        and split["off_pc"] is True
        and plain["cloud"] == "local"
        and plain["off_pc"] is False
        and rejected["written"] == 0
    )
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
