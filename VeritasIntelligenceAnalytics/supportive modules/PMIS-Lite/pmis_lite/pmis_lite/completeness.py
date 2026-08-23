"""擷取完整性驗證層 —— 對應「不可遺漏」與「提高涵蓋率」。

把失敗分三類，這是提高涵蓋率的關鍵：
  STRUCTURAL  結構性略過：來源本來就沒內容（空列、摘要任務、空白列）→ 不算漏，不計入分母
  RECOVERABLE 可救回：有內容但沒抓到（掃描檔需OCR、不支援類型）→ 算缺口，且系統應再努力救
  ERROR       真錯誤：解析爆掉、檔案壞 → 算缺口，需人關注

涵蓋率 = 成功擷取 / (成功 + 可救回 + 錯誤)，結構性略過不拉低分母。
這樣涵蓋率才誠實：它衡量的是「該抓到卻沒抓到」的比例，而非把空列也算成漏。
真正提高涵蓋率的方法 = 把 RECOVERABLE 救回來（OCR、支援更多類型）。
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

from dataclasses import dataclass, field

# 原因關鍵字 → 類別
_STRUCTURAL = ("empty_row", "no_title_or_body", "no_name", "empty", "blank", "structural")
_RECOVERABLE = ("unsupported_type", "no_text_layer", "ocr_unavailable", "ocr_empty", "需OCR", "scanned")


def categorize(reason: str) -> str:
    r = (reason or "").lower()
    if any(k in r for k in _STRUCTURAL):
        return "structural"
    if any(k in r for k in _RECOVERABLE):
        return "recoverable"
    return "error"


@dataclass
class SourceAudit:
    source: str
    seen: int = 0
    extracted: int = 0
    failures: list = field(default_factory=list)   # [(ref, reason)]

    def _count(self, cat: str) -> int:
        return sum(1 for _, reason in self.failures if categorize(reason) == cat)

    @property
    def failed(self) -> int:
        return len(self.failures)

    @property
    def structural(self) -> int:
        return self._count("structural")

    @property
    def recoverable(self) -> int:
        return self._count("recoverable")

    @property
    def errors(self) -> int:
        return self._count("error")

    @property
    def denom(self) -> int:
        # 分母排除結構性略過
        return self.extracted + self.recoverable + self.errors

    @property
    def coverage_pct(self) -> float:
        return round(100 * self.extracted / self.denom, 1) if self.denom else 100.0

    @property
    def unexplained_gap(self) -> int:
        return max(self.seen - self.extracted - self.failed, 0)

    @property
    def status(self) -> str:
        # 有未解釋遺漏 → FAIL；有 error → WARN；可救回不影響 PASS 但會被標示
        if self.unexplained_gap > 0:
            return "FAIL"
        if self.errors > 0:
            return "WARN"
        return "PASS"


class CompletenessReport:
    def __init__(self):
        self.audits: dict[str, SourceAudit] = {}

    def audit(self, source: str) -> SourceAudit:
        if source not in self.audits:
            self.audits[source] = SourceAudit(source=source)
        return self.audits[source]

    # 為了相容舊欄位名（failed += 1 / failures.append）保留：
    # 舊程式用 a.failed += 1 會失敗（property），故 adapter 改為只 append failures。

    def overall(self) -> dict:
        seen = sum(a.seen for a in self.audits.values())
        ext = sum(a.extracted for a in self.audits.values())
        structural = sum(a.structural for a in self.audits.values())
        recoverable = sum(a.recoverable for a in self.audits.values())
        errors = sum(a.errors for a in self.audits.values())
        gap = sum(a.unexplained_gap for a in self.audits.values())
        denom = ext + recoverable + errors
        status = "FAIL" if gap > 0 else ("WARN" if errors > 0 else "PASS")
        return {
            "seen": seen, "extracted": ext, "structural_skipped": structural,
            "recoverable": recoverable, "errors": errors, "unexplained_gap": gap,
            "status": status,
            "coverage_pct": round(100 * ext / denom, 1) if denom else 100.0,
        }

    def recoverable_items(self) -> list:
        out = []
        for a in self.audits.values():
            for ref, reason in a.failures:
                if categorize(reason) == "recoverable":
                    out.append((a.source, ref, reason))
        return out

    def to_markdown(self) -> str:
        o = self.overall()
        L = [f"## 擷取完整性驗證　**{o['status']}**　涵蓋率 {o['coverage_pct']}%"]
        L.append(f"- 可見 {o['seen']} · 擷取 {o['extracted']} · "
                 f"結構性略過 {o['structural_skipped']}(不算漏) · "
                 f"**可救回 {o['recoverable']}** · 錯誤 {o['errors']} · 未解釋遺漏 {o['unexplained_gap']}\n")
        L.append("| 來源 | 可見 | 擷取 | 結構略過 | 可救回 | 錯誤 | 涵蓋率 | 狀態 |")
        L.append("|---|---|---|---|---|---|---|---|")
        for a in self.audits.values():
            L.append(f"| {a.source} | {a.seen} | {a.extracted} | {a.structural} "
                     f"| {a.recoverable} | {a.errors} | {a.coverage_pct}% | {a.status} |")
        rec = self.recoverable_items()
        if rec:
            L.append("\n### 可救回項目（系統建議的補強動作）")
            for src, ref, reason in rec[:50]:
                action = _suggest(reason)
                L.append(f"- `{src}` {ref} → {reason}　**建議：{action}**")
        return "\n".join(L)


def _suggest(reason: str) -> str:
    r = (reason or "").lower()
    if "unsupported_type" in r:
        return "加裝對應解析器或轉存常見格式"
    if "no_text_layer" in r or "scanned" in r:
        return "開啟 OCR（掃描檔轉文字）"
    if "ocr_unavailable" in r:
        return "安裝 OCR 引擎(tesseract) 後可自動救回"
    return "檢視原因"
