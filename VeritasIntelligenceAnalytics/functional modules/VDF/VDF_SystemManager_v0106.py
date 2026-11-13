#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF manager tail. Versioned tool files replace the unversioned canon.

The old paths stay on disk for history. This tail does not delete them and
does not rewrite v0104. Direct start is still refused.
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
VIA = HERE.parents[1]
BODY = HERE / "VDF_SystemManager_v0104.py"
_body = None


def _newest(folder: Path, stem: str) -> Path | None:
    hits = []
    for path in folder.glob(stem + "_v*.py"):
        found = re.search(r"_v(\d+)", path.name)
        if found:
            hits.append((int(found.group(1)), path))
    return max(hits)[1] if hits else None


def _load():
    global _body
    if _body is None:
        spec = importlib.util.spec_from_file_location(BODY.stem + "_via_v0106", BODY)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        accel = _newest(VIA / "supportive modules", "VeritasCeleritas")
        nexus = _newest(VIA / "supportive modules" / "network", "VeritasAegisNexus")
        tools = dict(module.TOOLS)
        if accel is not None:
            tools["VeritasCeleritas.py"] = (str(accel.relative_to(VIA)).replace("\\", "/"), "有版號尾版取代無版號舊檔")
        if nexus is not None:
            tools["VeritasAegisNexus.py"] = (str(nexus.relative_to(VIA)).replace("\\", "/"), "有版號尾版取代無版號舊檔")
        module.TOOLS = tools
        _body = module
    return _body


def __getattr__(name: str):
    return getattr(_load(), name)


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VDF] 拒絕。只能經 via-vcgc。")
        return 2
    return _load().main()


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    ok = main() == 2
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
