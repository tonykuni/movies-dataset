"""vtr_py — DG-IN Meeting Transcript Restoration Engine（Python 版）。

目前實作範圍：確定性層（步驟 1 LANG_DETECT、2 NORMALIZE、P0 PROTECT/UNPROTECT）
與其賴以成立的骨架（資料契約、pipeline 不變式、信心度閘門、版本重播）。

步驟 3–8 需要模型層，尚未實作 —— 見 docs/01_PYTHON_ENGINE_SPEC.md。
本層刻意零第三方相依，因此可在未安裝任何套件的環境（含 CI）直接執行。
"""
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

from .context import ENGINE_ID, Config, Context
from .document import Document, Patch, Revision, Segment
from .gate import ConfidenceGate
from .pipeline import Pipeline, StageResult, preprocessing_pipeline

__version__ = "1.0.0"

__all__ = [
    "Config", "Context", "ENGINE_ID",
    "Document", "Segment", "Patch", "Revision",
    "ConfidenceGate",
    "Pipeline", "StageResult", "preprocessing_pipeline",
    "__version__",
]
