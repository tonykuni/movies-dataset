#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v0149→v0150: the newest manager carries the whole v0148 surface again.

v0149 (TALib command key unplugged) only exposed selftest() and main(). The
master-control contract test loads the newest manager and calls do_list(),
_build_page(), do_template() and do_ui(), and it redirects OUT and
TEMPLATE_OUT on the loaded module. A thin __getattr__ proxy cannot honour
those overrides, because the functions keep reading v0148's own globals.
So this file runs the v0148 body in its own namespace (same folder, same
__file__ for the body's self-reads), then applies the v0149 unplug.
v0148 and v0149 stay on disk (L04). No talib import, nothing installed.
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
import sys as _v150_sys
from pathlib import Path as _V150Path

_V150_SELF = _V150Path(__file__).resolve()
_V150_BODY = _V150_SELF.parent / "VIA_SYSTEM_MANAGER_v0148.py"
_V150_RETIRED = "VIA_ENG003_TALibEngine"
_V150_REPLACEMENT = "VDF_ENG086_QuantGuardOneBridge"

_v150_name = __name__
globals()["__name__"] = "via_system_manager_v0148_body_in_v0150"  # the body's own main block must not fire
globals()["__file__"] = str(_V150_BODY)                             # the body's selftest reads its own source
try:
    exec(compile(_V150_BODY.read_text(encoding="utf-8"), str(_V150_BODY), "exec"), globals())
finally:
    globals()["__name__"] = _v150_name
ENGINE_CANDIDATE_NAMES.pop(_V150_RETIRED, None)  # noqa: F821  (defined by the v0148 body)
_v148_selftest = selftest  # noqa: F821


def selftest() -> int:  # noqa: F811
    gone = _V150_RETIRED not in ENGINE_CANDIDATE_NAMES  # noqa: F821
    pointed = _V150_REPLACEMENT in ENGINE_FORMAL_NAMES  # noqa: F821
    surface = all(callable(globals().get(n)) for n in ("do_list", "_build_page", "do_template", "do_ui"))
    print(f"  [{'OK' if gone else 'FAIL'}] candidate command {_V150_RETIRED} unplugged (v0149)")
    print(f"  [{'OK' if pointed else 'FAIL'}] pointer is {_V150_REPLACEMENT}")
    print(f"  [{'OK' if surface else 'FAIL'}] do_list / _build_page / do_template / do_ui on the newest manager")
    if not (gone and pointed and surface):
        return 1
    print("=== v0148 body selftest ===")
    return _v148_selftest()


if __name__ == "__main__":
    if "--selftest" in _v150_sys.argv:
        raise SystemExit(selftest())
    raise SystemExit(main())  # noqa: F821
