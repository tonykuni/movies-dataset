#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG055_OmniFetch tail. The newest file carries both bridges and the whole working surface again.

0120→0121(側線 2026-09-28,PR #328 CI):ca098982 的兩層薄尾(v0119 · VDF_ENG055_OmniFetch_v0120.py)
只轉 main(),lane_global, run 都不見了,tests/ 直接叫尾版就 AttributeError(Windows UAT 的 daily 測試)。
本支在自己的 namespace 跑具體實作 VDF_ENG055_OmniFetch_v0118.py 的本體,再照 v0119 把 gate_open 換成 CGC_MDL224 ScrapeGate
(同一個正主,不另寫);模組層覆寫(例 DB_GL / REP)因此真的生效。舊版全留作版史(L04)。selftest 不抓網路。
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
    VIA_ACCEL = None
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
import importlib.util as _tail_ilu
import sys as _tail_sys
from pathlib import Path as _TailPath

_TAIL_SELF = _TailPath(__file__).resolve()
_TAIL_BODY = _TAIL_SELF.parent / "VDF_ENG055_OmniFetch_v0118.py"
_TAIL_GATE = _TAIL_SELF.parents[3] / "supportive modules" / "registry" / "CGC_MDL224_ScrapeGate_v0100.py"
_TAIL_SURFACE = ('lane_global', 'run')
_TAIL_NET_PATH = globals().get("VIA_NET_TOOL_PATH")


def _tail_load(path, name):
    spec = _tail_ilu.spec_from_file_location(name, path)
    module = _tail_ilu.module_from_spec(spec)
    _tail_sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_tail_name = __name__
globals()["__name__"] = "vdf_eng055_omnifetch_body_in_tail"   # the body's own main block must not fire
globals()["__file__"] = str(_TAIL_BODY)                 # the body reads paths / its own source from here
try:
    exec(compile(_TAIL_BODY.read_text(encoding="utf-8"), str(_TAIL_BODY), "exec"), globals())
finally:
    globals()["__name__"] = _tail_name
gate_open = _tail_load(_TAIL_GATE, "scrape_gate_for_vdf_eng055_omnifetch_tail").gate_open  # same swap v0119 made
_body_main = main  # noqa: F821


def main() -> int:  # noqa: F811
    return _body_main()


def selftest() -> int:
    text = _TAIL_SELF.read_text(encoding="utf-8")
    bridges = "VIA:ACCEL-BRIDGE" in text and "VIA:NET-BRIDGE" in text and bool(_TAIL_NET_PATH)
    surface = all(callable(globals().get(n)) for n in _TAIL_SURFACE)
    g = gate_open
    gate = (g({}) is False and g({"VIA_NET_CONSENT": "YES", "VIA_SCRAPE_CONSENT": "OFF"}) is False
            and g({"VIA_NET_CONSENT": "YES", "VIA_SCRAPE_CONSENT": "YES"}) is True)
    print(f"  [{'OK' if bridges else 'FAIL'}] 加速橋 + 網路橋在尾版上")
    print(f"  [{'OK' if surface else 'FAIL'}] 尾版帶著具體實作的面:{', '.join(_TAIL_SURFACE)}")
    print(f"  [{'OK' if gate else 'FAIL'}] gate_open = CGC_MDL224 ScrapeGate(同意閘沒開就關)")
    return 0 if (bridges and surface and gate) else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in _tail_sys.argv else main())
