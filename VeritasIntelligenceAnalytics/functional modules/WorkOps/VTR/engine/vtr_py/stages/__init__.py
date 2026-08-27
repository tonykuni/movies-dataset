"""VTR Stage 實作。每個 Stage 都是純函式：(Document, Context) -> StageResult。"""
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

from .s1_lang_detect import LangDetectStage
from .s2_normalize import NormalizeStage
from .s3_protect import ProtectStage, UnprotectStage

__all__ = [
    "LangDetectStage",
    "NormalizeStage",
    "ProtectStage",
    "UnprotectStage",
]
