"""VTR Stage 實作。每個 Stage 都是純函式：(Document, Context) -> StageResult。"""

from .s1_lang_detect import LangDetectStage
from .s2_normalize import NormalizeStage
from .s3_protect import ProtectStage, UnprotectStage

__all__ = [
    "LangDetectStage",
    "NormalizeStage",
    "ProtectStage",
    "UnprotectStage",
]
