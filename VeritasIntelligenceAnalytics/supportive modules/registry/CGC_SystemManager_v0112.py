#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_SystemManager v0112 — 獨立 MAIN 薄尾(批1657 操作員令「VRN 現在斷開 仍與 VCGC 各自運作下互動
但獨立 MAIN;VDF VCGC 也一樣」)。

v0111→v0112:沒帶 VIA_FROM_VCGC **不再拒絕**——自立閘座(對下游模組兼容)並把入口誠實記 standalone;
經 via-vcgc 進來照舊記 via-vcgc。backup 門與其餘行為一字不動,全部轉交前版鏈(glob 取前版,不釘版號)。
三總管對齊:VDF v0129+ 本來就自立閘;VRN v0119 同批改;本版補 VCGC 這一角。各自運作、互動經動詞口/中介。
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

import importlib.util
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_SystemManager"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def _vnum(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_PRIOR_MOD = None


def __getattr__(name):
    """PEP 562:公開名稱(check/review…)照前版鏈轉接,薄尾不漏 API(TAILAPI 律)。"""
    global _PRIOR_MOD
    if _PRIOR_MOD is None:
        _PRIOR_MOD = _load(_PRIOR_PATH, "cgc_prior_attr_for_v0112")
    return getattr(_PRIOR_MOD, name)


def entry_lane() -> str:
    """入口車道:帶 VIA_FROM_VCGC=YES 進來=via-vcgc;沒帶=standalone(獨立 MAIN,不拒)。"""
    return "via-vcgc" if os.environ.get("VIA_FROM_VCGC") == "YES" else "standalone"


def main() -> int:
    lane = entry_lane()
    if lane == "standalone":
        os.environ["VIA_FROM_VCGC"] = "YES"   # 自立閘座:前版鏈與下游模組兼容;入口已誠實印
        print(f"[VCGC] 獨立 MAIN(standalone)· {TAG} · 三總管各自運作下互動")
    return _load(_PRIOR_PATH, "cgc_prior_for_v0112").main()


def selftest() -> int:
    keep = os.environ.get("VIA_FROM_VCGC")
    os.environ.pop("VIA_FROM_VCGC", None)
    a = entry_lane() == "standalone"
    os.environ["VIA_FROM_VCGC"] = "YES"
    b = entry_lane() == "via-vcgc"
    import ast as _ast
    tree = _ast.parse(Path(__file__).read_text(encoding="utf-8"))
    fn = next(n for n in tree.body if isinstance(n, _ast.FunctionDef) and n.name == "main")
    c = not any(isinstance(n, _ast.Return) and isinstance(n.value, _ast.Constant) and n.value.value == 2
                for n in _ast.walk(fn))   # 本版 main 無「rc 2 拒絕」路(功能檢,不看字樣)
    d = _PRIOR_PATH.is_file() and _vnum(_PRIOR_PATH) < _vnum(__file__)
    prior_rc = _load(_PRIOR_PATH, "cgc_prior_self_for_v0112").selftest()   # 前版自測照跑(其閘語意屬前版)
    if keep is None:
        os.environ.pop("VIA_FROM_VCGC", None)
    else:
        os.environ["VIA_FROM_VCGC"] = keep
    ok = a and b and c and d and prior_rc == 0
    print(("  [OK] " if ok else "  [FAIL] ") + f"{TAG} 獨立 MAIN:入口判別 standalone/via-vcgc · 無拒絕路 · 前版鏈 glob({_PRIOR_PATH.name})· 前版自測 {'PASS' if prior_rc == 0 else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
