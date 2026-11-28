#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""test_v0301_workflow — 薄尾(前版一字不動):補上 VIA 加速器橋(CLAUDE.md REQ266)

在子行程實跑前版測試(它自己讀 v0300 引擎),收它輸出的那一筆 JSON;再加一項本版檢查:加速器真的載到。
輸出照前版格式(stdout 一筆 JSON),所以 VIA_PanoramaFusion_SuperEngine 的 selftest 照樣能讀。
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PATTERN = re.compile(r"^test_v(\d{4})_workflow$")


def _vnum(p) -> int:
    m = PATTERN.match(Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob("*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)


def main() -> int:
    src = Path(__file__).read_text(encoding="utf-8")
    accel_ok = VIA_ACCEL is not None and src.splitlines()[2] == "# [VIA:ACCEL-BRIDGE:v0111]"
    try:
        cp = subprocess.run([sys.executable, "-B", str(PRIOR_PATH)], cwd=str(HERE), capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=1800, stdin=subprocess.DEVNULL)
        prior = json.loads(cp.stdout.strip().splitlines()[-1])
        rc = cp.returncode
    except (subprocess.TimeoutExpired, ValueError, IndexError) as exc:
        prior, rc = {"passed": False, "tests": 0, "reason": type(exc).__name__}, 1
        cp = None
    if cp is not None and rc:
        sys.stderr.write("\n".join(cp.stderr.splitlines()[-40:]) + "\n")
    passed = bool(prior.get("passed")) and rc == 0 and accel_ok
    out = dict(prior, version="v0301", prior=PRIOR_PATH.name, prior_tests=prior.get("tests", 0),
               tests=int(prior.get("tests", 0) or 0) + 1, accel_loaded=accel_ok, passed=passed)
    print(json.dumps(out, ensure_ascii=False, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
