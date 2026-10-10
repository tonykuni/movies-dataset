#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Canonical seat. The body stays VeritasCeleritas_v1141.py. This file does not copy it."""
# ===== [VIA:ACCEL-BRIDGE:v0100] 加速器橋(2026-10-08 accel sweep 注入;L103 最高政策 PY 導入加速器;缺席不擋,記黃) =====
import sys as _ab_sys
from pathlib import Path as _ab_Path
_ab_p = _ab_Path(__file__).resolve()
while _ab_p.parent != _ab_p:
    if (_ab_p / "supportive modules").is_dir():
        _ab_sys.path.insert(0, str(_ab_p / "supportive modules"))
        break
    _ab_p = _ab_p.parent
try:
    import VeritasCeleritas_v1141 as _ACCEL  # noqa: F401
except Exception:  # noqa: BLE001
    _ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

from __future__ import annotations

import runpy
import sys
from pathlib import Path

BODY = Path(__file__).resolve().parent.parent / "VeritasCeleritas_v1141.py"


def main() -> int:
    if not BODY.is_file():
        print("ABSENT " + BODY.name)
        return 2
    sys.argv[0] = str(BODY)
    runpy.run_path(str(BODY), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
