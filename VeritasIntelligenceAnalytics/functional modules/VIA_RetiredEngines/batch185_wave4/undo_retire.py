#!/usr/bin/env python3
"""undo:批185 第四波讓位整批還原(零刪除紀律;manifest 逐筆 to→from;於 VIA 根執行)"""
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批181 全覆蓋令;graceful 零行為變更) =====
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
import json, shutil, hashlib
from pathlib import Path
m = json.loads((Path(__file__).parent / "RETIRE_MANIFEST.json").read_text(encoding="utf-8"))
for mv in m["moves"]:
    src, dst = Path(mv["to"]), Path(mv["from"])
    assert hashlib.sha256(src.read_bytes()).hexdigest() == mv["sha256"], mv["to"]
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
print("undone:", len(m["moves"]))
