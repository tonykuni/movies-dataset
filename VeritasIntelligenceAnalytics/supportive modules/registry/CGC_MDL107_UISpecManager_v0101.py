#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL107_UISpecManager v0101 — 樣式冊改讀 VIA_UI_TemplateSSOT **尾版**(不再釘死 v0100;換模板時跟著換)

R26 Z275:TemplateSSOT 消費者分兩種,跟隨尾版的會跟著模板轉接器(CGC_MDL241)換版,釘死 v0100 的不會 → 換模板後各頁樣式不一致。
v0100 在模組層寫死 `SSOTP = …/VIA_UI_TemplateSSOT_v0100.json`,而且都在呼叫時才讀 → v0101 只把這個常數改成尾版
(glob VIA_UI_TemplateSSOT_v*.json 取版號最大者;冊不在時退回 v0100 原路徑)。其餘整支 v0100 原樣(thin tail;__getattr__ 轉接)。
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
STEM = "CGC_MDL107_UISpecManager"


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", path.stem)
    return int(m.group(1)) if m else -1


PRIOR = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(STEM + "_prior_for_" + Path(__file__).stem, PRIOR)
_PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _PRIOR
_spec.loader.exec_module(_PRIOR)
ENGINE = Path(__file__).stem
PINNED = _PRIOR.SSOTP


def ssot_tail() -> Path:
    hits = sorted(HERE.glob("VIA_UI_TemplateSSOT_v*.json"), key=_vnum)
    return hits[-1] if hits else PINNED


_PRIOR.SSOTP = ssot_tail()            # every v0100 function reads this global at call time
SSOTP = _PRIOR.SSOTP


def __getattr__(name: str):
    return getattr(_PRIOR, name)


def selftest() -> int:
    rc = _PRIOR.selftest()
    tail = ssot_tail()
    ok_tail = _PRIOR.SSOTP == tail and tail.exists()
    print(f"  [{'OK' if ok_tail else 'FAIL'}] Z275 樣式冊讀尾版 · {tail.name}(v0100 釘死的是 {PINNED.name})")
    ok_fb = True
    try:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            t = Path(td)
            for n in ("VIA_UI_TemplateSSOT_v0100.json", "VIA_UI_TemplateSSOT_v0107.json", "VIA_UI_TemplateSSOT_v0099.json"):
                (t / n).write_text("{}", encoding="utf-8")
            pick = sorted(t.glob("VIA_UI_TemplateSSOT_v*.json"), key=_vnum)[-1].name
            ok_fb = pick == "VIA_UI_TemplateSSOT_v0107.json"
    except OSError:
        ok_fb = False
    print(f"  [{'OK' if ok_fb else 'FAIL'}] Z275 尾版律:版號最大者勝(v0107 > v0100 > v0099)")
    ok = rc == 0 and ok_tail and ok_fb
    print(f"  {ENGINE} selftest +{int(ok_tail) + int(ok_fb)}/2 · v0100 rc={rc} · {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return _PRIOR.main()


if __name__ == "__main__":
    sys.exit(main())
