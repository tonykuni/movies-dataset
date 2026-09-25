"""信心度閘門（00_ARCHITECTURE.md §3）。

這是「敢不敢自動套用」的唯一依據。所有 Stage 都必須經由 gate.decide() 取得
decision，不得自行填寫 —— 否則門檻調整就無法一處生效。
"""

from __future__ import annotations
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

from dataclasses import dataclass

from .document import Decision, Source


@dataclass(frozen=True)
class ConfidenceGate:
    auto_threshold: float = 0.85
    review_threshold: float = 0.60
    #: 單獨 LLM 判斷的信心度上限。刻意低於 auto_threshold，
    #: 因此 LLM 永遠不能在無人複核下改動會議紀錄。
    llm_only_ceiling: float = 0.80

    def __post_init__(self) -> None:
        if not 0.0 <= self.review_threshold <= self.auto_threshold <= 1.0:
            raise ValueError(
                f"門檻順序不合法: review={self.review_threshold} "
                f"auto={self.auto_threshold}")
        if self.llm_only_ceiling >= self.auto_threshold:
            raise ValueError(
                f"llm_only_ceiling({self.llm_only_ceiling}) 必須小於 "
                f"auto_threshold({self.auto_threshold})，否則 LLM 可自動套用")

    def effective_confidence(self, confidence: float, source: Source) -> float:
        """套用來源上限後的信心度。"""
        if source == "llm_arbiter":
            return min(confidence, self.llm_only_ceiling)
        return confidence

    def decide(self, confidence: float, source: Source = "deterministic") -> Decision:
        conf = self.effective_confidence(confidence, source)
        if conf >= self.auto_threshold:
            return "auto"
        if conf >= self.review_threshold:
            return "review"
        return "reject"
