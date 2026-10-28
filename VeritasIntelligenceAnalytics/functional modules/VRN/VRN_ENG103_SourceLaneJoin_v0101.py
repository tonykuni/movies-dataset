#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN reads the sealed TWSE/TPEX/yfinance rows. It does not fetch them again."""
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
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
LOCK = VIA / "supportive modules" / "registry" / "VIA_SourceLaneLock_v0100.json"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def locked_rows() -> dict:
    data = json.loads(LOCK.read_text(encoding="utf-8"))
    return {row["code"]: row for row in data["rows"]}


def quote_for(code: str) -> dict:
    bare = str(code or "").split(".")[0].strip()
    row = locked_rows().get(bare)
    if not row or not row.get("overlap"):
        return {"state": "NODATA", "code": bare}
    return {"state": "OK", "code": bare, "symbol": row["symbol"], "market": row["market"],
            "close": row["exchange_close"], "adj_close": row["adj_close"]}


def survey(folder: Path) -> dict:
    if not folder.is_dir():
        return {"state": "ABSENT", "path": str(folder), "stock": 0, "other": 0, "priced": []}
    parser = _load(HERE / "VRN_ENG084_FilenameTokenParse_v0100.py", "fn84")
    stock = other = 0
    priced = []
    for item in sorted(folder.iterdir()):
        if not item.is_file():
            continue
        parsed = parser.parse_filename(item.stem)
        tick = parsed.get("ticker") or {}
        code = tick.get("canonical") or ""
        if tick.get("state") == "GREEN" and code:
            stock += 1
            got = quote_for(code)
            if got["state"] == "OK":
                priced.append({"file": item.name, "symbol": got["symbol"], "close": got["close"]})
        else:
            other += 1
    return {"state": "OK", "path": str(folder), "stock": stock, "other": other, "priced": priced}


def selftest() -> int:
    ok = quote_for("2330")["symbol"] == "2330.TW" and quote_for("6488.TWO")["close"] == 948
    ok = ok and quote_for("9999")["state"] == "NODATA"
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest())
