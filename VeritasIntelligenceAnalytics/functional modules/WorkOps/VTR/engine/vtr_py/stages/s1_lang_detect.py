"""步驟 1：語言偵測（LANG_DETECT）。

刻意**不使用**整句語言偵測（langdetect / fasttext 那一類）：它們對中英混雜句
無效，而中英混雜正是 DG-IN 會議紀錄的常態。「看一下 dashboard 的 KPI」在整句
偵測器眼中是中文，於是 `dashboard` 會被送進中文管線當成雜訊或錯字。

改用 code-point 分類 + run 合併（00_ARCHITECTURE.md §5.1）。本步驟不改動任何
文字，只做標註 —— 因此它產生 0 個 patch，只回報量測值。
"""

from __future__ import annotations

from dataclasses import replace

from ..context import Context
from ..document import Document, Run, Script, Segment
from ..pipeline import StageResult

CJK_RANGES: tuple[tuple[int, int], ...] = (
    (0x4E00, 0x9FFF),   # CJK 統一表意文字
    (0x3400, 0x4DBF),   # 擴充 A
    (0xF900, 0xFAFF),   # 相容表意文字
    (0x3000, 0x303F),   # CJK 標點
    (0xFF00, 0xFFEF),   # 全形形式
)

#: 遮罩符本身不參與語言判定 —— 它代表被保護的內容，語言未知。
SENTINEL_CHARS = "⟦⟧"


def classify(ch: str) -> Script:
    if ch in SENTINEL_CHARS:
        return "other"
    cp = ord(ch)
    if any(lo <= cp <= hi for lo, hi in CJK_RANGES):
        # 全形區塊裡的英數要歸為 latin/digit，正規化後才會變半形
        if 0xFF10 <= cp <= 0xFF19:
            return "digit"
        if 0xFF21 <= cp <= 0xFF3A or 0xFF41 <= cp <= 0xFF5A:
            return "latin"
        return "punct" if 0x3000 <= cp <= 0x303F or 0xFF00 <= cp <= 0xFF0F else "cjk"
    if ch.isascii() and ch.isalpha():
        return "latin"
    if ch.isdigit():
        return "digit"
    if ch.isspace():
        return "other"
    if not ch.isalnum():
        return "punct"
    return "other"


def raw_runs(text: str) -> list[Run]:
    """連續同類 code point 合成一個 run。"""
    runs: list[Run] = []
    if not text:
        return runs
    start = 0
    cur = classify(text[0])
    for i in range(1, len(text)):
        s = classify(text[i])
        if s != cur:
            runs.append(Run(start=start, end=i, script=cur))
            start, cur = i, s
    runs.append(Run(start=start, end=len(text), script=cur))
    return runs


def merge_short_runs(runs: list[Run], min_cjk: int, min_latin: int) -> list[Run]:
    """短 run 併入前一個 run。

    沒有這一步，「VIA的KPI」會被切成 latin/cjk/latin 三段，每段都短到無法判定
    語言，後續分流就會亂。
    """
    if not runs:
        return runs
    out: list[Run] = [runs[0]]
    for r in runs[1:]:
        length = r.end - r.start
        too_short = (
            (r.script == "cjk" and length < min_cjk)
            or (r.script == "latin" and length < min_latin)
        )
        if too_short:
            prev = out[-1]
            out[-1] = Run(start=prev.start, end=r.end, script=prev.script,
                          role=prev.role)
        else:
            out.append(r)
    return out


def assign_roles(runs: list[Run], text: str, dominant: Script) -> list[Run]:
    """標註 run 角色。

    embedded = 主體語言句子中內嵌的外語詞。它**不得**被送進該外語的獨立句法
    修復 —— 否則「看一下 dashboard 的 KPI」裡的 dashboard 會被英文 GEC 要求
    補冠詞，變成「看一下 the dashboard 的 KPI」。
    """
    out: list[Run] = []
    for r in runs:
        if r.script in ("other",) and any(
                c in SENTINEL_CHARS for c in text[r.start:r.end]):
            out.append(replace(r, role="protected"))
        elif r.script in ("cjk", "latin") and r.script != dominant:
            out.append(replace(r, role="embedded"))
        else:
            out.append(r)
    return out


def detect_segment(seg: Segment, min_cjk: int, min_latin: int,
                   mixed_threshold: float) -> Segment:
    runs = merge_short_runs(raw_runs(seg.text), min_cjk, min_latin)

    # 以 **token** 而非字元計數。一個中文字所承載的資訊量大致等同一個英文
    # 「單字」，不是一個英文字母。用字元計數會系統性高估英文比重：
    # 「看一下 dashboard 的 KPI」字元比是 4:12（判成英文，明顯錯誤），
    # token 比則是 4:2（中文為主，正確）。
    cjk_tokens = sum(r.end - r.start for r in runs if r.script == "cjk")
    latin_tokens = sum(
        len(text_slice.split())
        for text_slice in (r.slice_of(seg.text) for r in runs if r.script == "latin")
    ) or sum(1 for r in runs if r.script == "latin")
    total = cjk_tokens + latin_tokens

    if total == 0:
        lang = seg.lang            # 純數字/標點/遮罩：維持原判，不猜測
        dominant: Script = "other"
    elif cjk_tokens / total > mixed_threshold:
        lang, dominant = "zh", "cjk"
    elif latin_tokens / total > mixed_threshold:
        lang, dominant = "en", "latin"
    else:
        lang = "mixed"
        dominant = "cjk" if cjk_tokens >= latin_tokens else "latin"

    return replace(seg, lang=lang,
                   runs=tuple(assign_roles(runs, seg.text, dominant)))


class LangDetectStage:
    name = "LANG_DETECT"

    def apply(self, doc: Document, ctx: Context) -> StageResult:
        min_cjk = int(ctx.config.get("lang_detect.min_run_cjk", 2))
        min_latin = int(ctx.config.get("lang_detect.min_run_latin", 3))
        threshold = float(ctx.config.get("lang_detect.mixed_threshold", 0.7))

        segments = tuple(
            detect_segment(s, min_cjk, min_latin, threshold) for s in doc.segments)

        counts = {"zh": 0, "en": 0, "mixed": 0}
        embedded = 0
        for s in segments:
            counts[s.lang] = counts.get(s.lang, 0) + 1
            embedded += sum(1 for r in s.runs if r.role == "embedded")

        ctx.metrics.set("segments_zh", counts["zh"])
        ctx.metrics.set("segments_en", counts["en"])
        ctx.metrics.set("segments_mixed", counts["mixed"])
        ctx.metrics.set("embedded_runs", embedded)

        return StageResult(doc=replace(doc, segments=segments), patches=())
