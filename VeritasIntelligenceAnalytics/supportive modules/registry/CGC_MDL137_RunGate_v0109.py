#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL137_RunGate v0109 — 薄尾:能跑閘不再探 / 不再教裝 TA-Lib(R30 操作員令「刪除一切 TA-LIB 指令 模組化刪除 不要外擴 刪除後修正」)

量過(R30):v0108 的 FAMILY_LIBS["vap"]["optional"] 還列著 "talib"——probe 會在 vap 家族境裡 `importlib.import_module("talib")`;
PIP_NAMES 還有 "talib" → "TA-Lib"——缺件時補庫句會印出 `uv pip install … TA-Lib`。這是全樹最後一處會「去碰」TA-Lib 的活碼(L50 第一條)。
本尾版只做一件事:載入前一版後,從它自己的兩張表拿掉 talib(同一個物件,v0108 的函式照舊讀自己的全域);其餘整支照 v0108(__getattr__ 轉接)。
不改任何別支、不動禁令守衛(CGC_MDL190 / 205 / 206 · QuantGuard 照舊守)。只收 VCGC 呼叫的規矩照前一版。
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
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "CGC_MDL137_RunGate"
ENGINE = Path(__file__).stem
BANNED = ("talib",)


def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d+)$", p.stem)
    return int(m.group(1)) if m else -1


PRIOR = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(STEM + "_prior_for_" + ENGINE, PRIOR)
_PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _PRIOR
_spec.loader.exec_module(_PRIOR)


def strip_banned(family_libs: dict, pip_names: dict) -> None:
    """In place: the prior's own tables lose the banned libraries (its functions read the same objects)."""
    for fam in family_libs.values():
        for k in ("required", "optional"):
            if isinstance(fam.get(k), list):
                fam[k][:] = [x for x in fam[k] if x not in BANNED]
    for b in BANNED:
        pip_names.pop(b, None)


strip_banned(_PRIOR.FAMILY_LIBS, _PRIOR.PIP_NAMES)


def __getattr__(name: str):
    return getattr(_PRIOR, name)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    libs = [x for fam in _PRIOR.FAMILY_LIBS.values() for k in ("required", "optional") for x in fam.get(k, [])]
    chk("R30 三個家族的探針名單都沒有 talib(不再 import)", "talib" not in libs, _PRIOR.FAMILY_LIBS.get("vap"))
    chk("R30 補庫對照沒有 TA-Lib(不會印 pip install TA-Lib)", "talib" not in _PRIOR.PIP_NAMES and "TA-Lib" not in _PRIOR.PIP_NAMES.values())
    fam, pip = {"x": {"required": ["a"], "optional": ["talib", "b"]}}, {"talib": "TA-Lib", "a": "a"}
    strip_banned(fam, pip)
    chk("R30 拿法是原地改前一版的表(函式讀得到;其他庫一個不少)", fam["x"]["optional"] == ["b"] and pip == {"a": "a"})
    if not all(ok):
        return 1
    return _PRIOR.selftest()


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return _PRIOR.main()


if __name__ == "__main__":
    sys.exit(main())
