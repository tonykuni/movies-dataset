"""步驟 2：正規化（NORMALIZE）。

三個刻意的設計決定：

1. **不做整串 NFKC。** NFKC 會把全形標點拉成 ASCII：`，`(U+FF0C) → `,`、
   `？`(U+FF1F) → `?`。對中文會議紀錄而言那是破壞不是正規化。因此 NFKC 只作用
   於「不在保留集合」的字元。

2. **所有 patch 一律錨定在 Stage 執行前的座標系，且互不重疊。** 這讓 pipeline
   的第 3 條不變式能真正驗證，也讓每個改動可以獨立接受或拒絕。

3. **語助詞標記而非刪除。**「那個」有時是語助詞、有時是指示代詞（「那個料號」）。
   誤刪會改變語意，因此一律產生 review 級的刪除建議，永不自動套用。
"""

from __future__ import annotations

import difflib
import unicodedata
from dataclasses import replace
from typing import Callable, Iterable, NamedTuple, Optional

from ..context import Context
from ..document import Document, Patch, Segment
from ..pipeline import StageResult

#: 中文語境要保留全形的標點。這些字元永遠不進 NFKC，也不進 fullwidth_ascii。
PRESERVE_FULLWIDTH = "，；：？！（）「」『』《》〈〉【】、。…—"

#: 半形 → 全形（僅在 CJK 語境套用）
HALF_TO_FULL_PUNCT = {
    ",": "，", ";": "；", ":": "：", "?": "？", "!": "！",
    "(": "（", ")": "）",
}

WHITESPACE_CHARS = " \t　 ​"


class Claim(NamedTuple):
    """一段被某條規則認領的區間（座標為 Stage 執行前的原文）。"""

    start: int
    end: int
    after: str
    rule_id: str
    confidence: float
    evidence: str
    priority: int          # 數字小者優先
    source: str = "deterministic"


# --------------------------------------------------------------------------- #
# 字元分類
# --------------------------------------------------------------------------- #

def _is_cjk(ch: str) -> bool:
    cp = ord(ch)
    return (0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF
            or 0xF900 <= cp <= 0xFAFF)


def _is_cjk_punct(ch: str) -> bool:
    return ch in PRESERVE_FULLWIDTH


def _is_latin_or_digit(ch: str) -> bool:
    return ch.isascii() and ch.isalnum()


# --------------------------------------------------------------------------- #
# Phase A：長度不變的逐字元規則
# --------------------------------------------------------------------------- #

def _claims_fullwidth_ascii(text: str) -> list[Claim]:
    out: list[Claim] = []
    for i, ch in enumerate(text):
        if ch in PRESERVE_FULLWIDTH:
            continue
        cp = ord(ch)
        if 0xFF01 <= cp <= 0xFF5E:
            half = chr(cp - 0xFEE0)
            out.append(Claim(i, i + 1, half, "VTR.NORMALIZE.fullwidth_ascii",
                             1.0, f"全形 {ch!r} → 半形 {half!r}", priority=30))
    return out


def _claims_nfkc(text: str) -> list[Claim]:
    """NFKC 的收尾規則。

    只處理 1:1 的相容字元（如 `﹒` → `.`、`Ⅻ` → 略）。長度會改變的相容分解
    （連字 `ﬁ` → `fi`）在本版不處理 —— 會議逐字稿裡幾乎不會出現，而支援它
    需要與模型層共用的對齊機制，屬於步驟 3 以後的範圍。
    """
    out: list[Claim] = []
    for i, ch in enumerate(text):
        if ch in PRESERVE_FULLWIDTH or 0xFF01 <= ord(ch) <= 0xFF5E:
            continue
        norm = unicodedata.normalize("NFKC", ch)
        if norm != ch and len(norm) == 1:
            out.append(Claim(i, i + 1, norm, "VTR.NORMALIZE.nfkc",
                             1.0, f"NFKC {ch!r} → {norm!r}", priority=40))
    return out


def _claims_cjk_punct(text: str) -> list[Claim]:
    """CJK 語境中的半形標點 → 全形。

    護欄：數字之間的 `.` 與 `:` 不轉（版本號 `1.2`、時間碼 `14:30`）。
    """
    out: list[Claim] = []
    for i, ch in enumerate(text):
        full = HALF_TO_FULL_PUNCT.get(ch)
        if full is None:
            continue
        prev = text[i - 1] if i else ""
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if not (_is_cjk(prev) or _is_cjk_punct(prev)):
            continue
        if ch in ".:" and prev.isdigit() and nxt.isdigit():
            continue
        out.append(Claim(i, i + 1, full, "VTR.NORMALIZE.cjk_punct",
                         1.0, f"CJK 語境半形 {ch!r} → 全形 {full!r}", priority=20))
    return out


# --------------------------------------------------------------------------- #
# Phase B：長度會變的規則
# --------------------------------------------------------------------------- #

_FILLER_STANDALONE = ("嗯", "呃", "欸", "唉", "啊")
_FILLER_DEMONSTRATIVE = ("那個", "這個", "就是說")


def _claims_filler(text: str, confidence: float) -> list[Claim]:
    out: list[Claim] = []
    i = 0
    while i < len(text):
        matched = False
        for f in _FILLER_STANDALONE:
            if text.startswith(f, i):
                j = i
                while text.startswith(f, j):
                    j += len(f)
                out.append(Claim(
                    i, j, "", "VTR.NORMALIZE.filler_mark", confidence,
                    f"疑似語助詞 {text[i:j]!r}；提出刪除建議但不自動套用",
                    priority=5))
                i = j
                matched = True
                break
        if matched:
            continue
        for f in _FILLER_DEMONSTRATIVE:
            if text.startswith(f, i):
                nxt = text[i + len(f):i + len(f) + 1]
                # 後面接名詞時是指示代詞（「那個料號」），不視為語助詞
                if nxt == "" or nxt in WHITESPACE_CHARS or _is_cjk_punct(nxt):
                    out.append(Claim(
                        i, i + len(f), "", "VTR.NORMALIZE.filler_mark",
                        confidence,
                        f"疑似語助詞 {f!r}（後接標點或句尾）；提出刪除建議",
                        priority=5))
                    i += len(f)
                    matched = True
                break
        if matched:
            continue
        i += 1
    return out


def _claims_whitespace(text: str, work: str) -> list[Claim]:
    """空白正規化。

    `work` 是 Phase A 套用後的文字（與 `text` 等長），用來判斷鄰接字元的類別；
    patch 的 before 一律取自 `text`，因此座標仍錨定在原文。
    """
    out: list[Claim] = []
    n = len(text)
    i = 0
    while i < n:
        if text[i] not in WHITESPACE_CHARS:
            i += 1
            continue
        j = i
        while j < n and text[j] in WHITESPACE_CHARS:
            j += 1
        prev = work[i - 1] if i else ""
        nxt = work[j] if j < n else ""

        if not prev or not nxt:
            desired = ""                      # 行首 / 行尾
            why = "移除行首行尾空白"
        elif _is_cjk(prev) and _is_cjk(nxt):
            desired = ""
            why = "移除 CJK 之間的空白"
        elif _is_cjk_punct(prev) or _is_cjk_punct(nxt):
            desired = ""
            why = "全形標點旁不留空白"
        elif ((_is_cjk(prev) and _is_latin_or_digit(nxt))
              or (_is_latin_or_digit(prev) and _is_cjk(nxt))):
            desired = " "
            why = "CJK–Latin 邊界保留單一空白"
        else:
            desired = " "
            why = "壓縮連續空白"

        if text[i:j] != desired:
            out.append(Claim(i, j, desired, "VTR.NORMALIZE.whitespace",
                             1.0, why, priority=10))
        i = j

    out.extend(_claims_missing_boundary_space(text, work))
    return out


def _claims_missing_boundary_space(text: str, work: str) -> list[Claim]:
    """CJK–Latin 邊界缺少空白時補上（零長度插入）。

    「看一下dashboard的資料」→「看一下 dashboard 的資料」。只掃描既有空白是
    不夠的 —— ASR 輸出的中英交界通常根本沒有空白。
    """
    out: list[Claim] = []
    for i in range(1, len(work)):
        prev, cur = work[i - 1], work[i]
        if prev in WHITESPACE_CHARS or cur in WHITESPACE_CHARS:
            continue
        boundary = ((_is_cjk(prev) and _is_latin_or_digit(cur))
                    or (_is_latin_or_digit(prev) and _is_cjk(cur)))
        if boundary:
            out.append(Claim(i, i, " ", "VTR.NORMALIZE.whitespace", 1.0,
                             f"CJK–Latin 邊界補上空白（{prev!r}|{cur!r}）",
                             priority=11))
    return out


def _claims_converter(text: str, convert: Callable[[str], str]) -> list[Claim]:
    """簡繁／用語轉換（OpenCC s2twp）。

    詞組轉換會改變長度，因此用 difflib 取最小 hunk 並錨定回原文座標。
    轉換器以參數注入 —— 這讓本路徑不需安裝 opencc 也能測試。
    """
    converted = convert(text)
    if converted == text:
        return []
    out: list[Claim] = []
    sm = difflib.SequenceMatcher(a=text, b=converted, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        out.append(Claim(
            i1, i2, converted[j1:j2], "VTR.NORMALIZE.opencc_s2twp", 1.0,
            f"簡繁／用語轉換 {text[i1:i2]!r} → {converted[j1:j2]!r}",
            priority=15))
    return out


# --------------------------------------------------------------------------- #
# 認領解衝突
# --------------------------------------------------------------------------- #

def resolve_claims(claims: Iterable[Claim]) -> list[Claim]:
    """優先序低者先佔位；重疊者丟棄。

    這保證同一 Stage 產生的 patch 互不重疊 —— 否則套用順序會變成隱藏狀態，
    patch log 與實際結果就對不起來。
    """
    ordered = sorted(claims, key=lambda c: (c.priority, c.start, -(c.end - c.start)))
    taken: list[tuple[int, int]] = []
    kept: list[Claim] = []
    for c in ordered:
        if any(c.start < e and c.end > s for s, e in taken):
            continue
        taken.append((c.start, c.end))
        kept.append(c)
    return sorted(kept, key=lambda c: c.start)


# --------------------------------------------------------------------------- #
# Stage
# --------------------------------------------------------------------------- #

def _load_opencc(profile: str) -> Optional[Callable[[str], str]]:
    try:
        import opencc  # type: ignore
    except ImportError:
        return None
    converter = opencc.OpenCC(profile)
    return converter.convert


class NormalizeStage:
    name = "NORMALIZE"

    def __init__(self, converter: Optional[Callable[[str], str]] = None) -> None:
        #: 注入式轉換器。None 代表由設定決定是否載入 opencc。
        self._converter = converter
        self._converter_injected = converter is not None

    def apply(self, doc: Document, ctx: Context) -> StageResult:
        profile = str(ctx.config.get("normalize.opencc", "s2twp"))
        filler_conf = float(ctx.config.get("normalize.filler_confidence", 0.70))
        filler_policy = str(ctx.config.get("normalize.filler_policy", "mark"))

        converter = self._converter
        if not self._converter_injected:
            converter = _load_opencc(profile)
        available = converter is not None
        ctx.metrics.set("opencc_available", available)
        ctx.metrics.set("opencc_profile", profile)
        if not available:
            # 絕不靜默跳過：降級必須出現在 revision 的 metrics 裡。
            ctx.metrics.set("degraded", True)
            ctx.metrics.set(
                "degraded_reason",
                "opencc 未安裝，簡繁／用語轉換未執行（VTR.NORMALIZE.opencc_s2twp）")

        segments: list[Segment] = []
        patches: list[Patch] = []
        counter = 0

        for seg in doc.segments:
            text = seg.text

            phase_a = _claims_cjk_punct(text) + _claims_fullwidth_ascii(text) \
                + _claims_nfkc(text)
            work = _apply_claims_to_text(text, phase_a)

            phase_b: list[Claim] = list(_claims_whitespace(text, work))
            if converter is not None:
                phase_b += _claims_converter(text, converter)
            if filler_policy != "keep":
                phase_b += _claims_filler(text, filler_conf)

            kept = resolve_claims(phase_a + phase_b)

            seg_patches: list[Patch] = []
            for c in kept:
                counter += 1
                decision = ctx.gate.decide(c.confidence, c.source)  # type: ignore[arg-type]
                if filler_policy == "remove" and c.rule_id.endswith("filler_mark"):
                    decision = "auto"
                seg_patches.append(Patch(
                    patch_id=ctx.new_patch_id(counter),
                    stage=self.name,
                    segment_id=seg.id,
                    span=(c.start, c.end),
                    before=text[c.start:c.end],
                    after=c.after,
                    rule_id=c.rule_id,
                    source=c.source,  # type: ignore[arg-type]
                    confidence=c.confidence,
                    decision=decision,
                    evidence=c.evidence,
                ))
            patches.extend(seg_patches)
            segments.append(seg)          # 文字由 pipeline 依閘門套用

        ctx.metrics.set("segments", len(doc.segments))
        return StageResult(doc=replace(doc, segments=tuple(segments)),
                           patches=tuple(patches))


def _apply_claims_to_text(text: str, claims: list[Claim]) -> str:
    """把長度不變的 Phase A 認領套到文字上，供 Phase B 判斷鄰接字元。"""
    chars = list(text)
    for c in claims:
        if c.end - c.start == len(c.after):
            for k, ch in enumerate(c.after):
                chars[c.start + k] = ch
    return "".join(chars)
