"""P0 保護遮罩（00_ARCHITECTURE.md §2.3）。

這是整條管線裡最關鍵的一個機制。沒有它，步驟 3–6 會親手破壞第 6 模組要保護
的東西：標點恢復把 `VIA-0162B` 切成 `VIA-0162 B`、拼寫修正把 `VeritasAutoPlot`
拆成三個字、模型「順手」把 `A7X-2201` 改成更常見的 `A7X-2021`。

遮罩符使用 U+27E6/U+27E7（⟦⟧）：不出現於中英文會議語料、不被主流 tokenizer
拆成語意單位、人工複核時一眼可辨。
"""

from __future__ import annotations

import re
from dataclasses import replace
from typing import Iterable, NamedTuple, Optional

from .document import Patch, Protection, Segment

SENTINEL_FMT = "⟦P{:04d}⟧"


class Candidate(NamedTuple):
    """一個待遮罩的區間。"""

    start: int
    end: int
    kind: str
    rule_id: str
    lexicon_id: Optional[str] = None
    #: True 代表命中 pattern 但不在詞庫 —— 標記 unresolved_entity，交人工。
    unresolved: bool = False

    @property
    def length(self) -> int:
        return self.end - self.start


# --------------------------------------------------------------------------- #
# Pattern 偵測器
#
# 順序即優先序：先偵測到的區間會佔用位置，後續重疊的候選被丟棄。
# 因此把「更具體、更長」的規則放前面。
# --------------------------------------------------------------------------- #

_PATTERNS: tuple[tuple[str, str, re.Pattern[str]], ...] = (
    ("url", "VTR.PROTECT.pattern_url",
     re.compile(r"https?://[^\s，。、；：！？）」』]+")),
    ("email", "VTR.PROTECT.pattern_email",
     re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    ("timestamp", "VTR.PROTECT.pattern_timestamp",
     re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b")),
    # 料號。三種常見型態，刻意都放寬到「寧可多遮、不可漏遮」：
    #   帶連字號且前綴可含數字（A7X-2201、VIA-0162B）
    #   不帶連字號（VIA0162B）
    #   VIA 版本碼（v0162B）
    # 過度遮罩的代價是「這段沒被修」，漏遮的代價是「料號被改錯」。
    # 兩者不對等，因此規則往寬的一側靠。
    ("part_number", "VTR.PROTECT.pattern_part_number",
     re.compile(r"\b[A-Z][A-Z0-9]{1,4}[-_]\d{2,6}[A-Z]?\b")),
    ("part_number", "VTR.PROTECT.pattern_part_number",
     re.compile(r"\b[A-Z]{2,4}\d{3,6}[A-Z]?\b")),
    ("part_number", "VTR.PROTECT.pattern_part_number",
     re.compile(r"\bv\d{3,4}[A-Z]?\b")),
    # CamelCase 識別字：VeritasAutoPlot / iPhone / getUserName
    ("code_ident", "VTR.PROTECT.pattern_code_ident",
     re.compile(r"\b[A-Za-z][a-z0-9]*(?:[A-Z][a-z0-9]+)+\b")),
    ("number_unit", "VTR.PROTECT.pattern_number_unit",
     re.compile(r"\b\d+(?:\.\d+)?\s?(?:%|ms|GB|MB|KB|TB|kg|cm|mm|px|fps)\b")),
)


def find_candidates(text: str, enabled_kinds: Iterable[str]) -> list[Candidate]:
    """依 pattern 找出所有待遮罩區間，已解重疊。"""
    enabled = set(enabled_kinds)
    found: list[Candidate] = []
    taken: list[tuple[int, int]] = []

    for kind, rule_id, pattern in _PATTERNS:
        if kind not in enabled:
            continue
        for m in pattern.finditer(text):
            start, end = m.span()
            if any(start < t_end and end > t_start for t_start, t_end in taken):
                continue  # 與更高優先序的候選重疊
            taken.append((start, end))
            found.append(Candidate(
                start=start, end=end, kind=kind, rule_id=rule_id,
                # pattern 命中但未在詞庫確認的料號，一律標為待確認 —— 不猜測。
                unresolved=(kind == "part_number"),
            ))
    return sorted(found, key=lambda c: c.start)


# --------------------------------------------------------------------------- #
# 遮罩 / 還原
# --------------------------------------------------------------------------- #

def next_sentinel_index(segment: Segment) -> int:
    """下一個可用的 sentinel 序號（避開已存在的）。"""
    used = {
        int(p.sentinel[2:-1])
        for p in segment.protections
        if p.sentinel[2:-1].isdigit()
    }
    return max(used, default=0) + 1


def mask(
    segment: Segment,
    candidates: Iterable[Candidate],
    make_patch_id,
) -> tuple[Segment, list[Patch]]:
    """把候選區間換成 sentinel，回傳新 segment 與對應 patch。

    由後往前替換，因此候選的座標不需重算。
    """
    cands = sorted(candidates, key=lambda c: c.start, reverse=True)
    text = segment.text
    idx = next_sentinel_index(segment)
    protections = list(segment.protections)
    patches: list[Patch] = []
    flags = set(segment.flags)

    # 先依出現順序配號，讀起來才是 P0001, P0002, ...
    numbering = {id(c): n for n, c in enumerate(sorted(cands, key=lambda c: c.start), idx)}

    for c in cands:
        surface = text[c.start:c.end]
        sentinel = SENTINEL_FMT.format(numbering[id(c)])
        protections.append(Protection(
            sentinel=sentinel, surface=surface, kind=c.kind,
            lexicon_id=c.lexicon_id))
        patches.append(Patch(
            patch_id=make_patch_id(),
            stage="PROTECT",
            segment_id=segment.id,
            span=(c.start, c.end),
            before=surface,
            after=sentinel,
            rule_id=c.rule_id,
            source="lexicon" if c.lexicon_id else "deterministic",
            confidence=1.0,
            decision="auto",
            evidence=(f"保護 {c.kind}：{surface!r} → {sentinel}"
                      + ("（未在詞庫確認，標記 unresolved_entity）"
                         if c.unresolved else "")),
        ))
        if c.unresolved:
            flags.add("unresolved_entity")
        text = text[:c.start] + sentinel + text[c.end:]

    new_seg = replace(
        segment,
        text=text,
        protections=tuple(protections),
        flags=tuple(sorted(flags)),
        runs=(),  # 座標已變，交由 LANG_DETECT 重算
    )
    return new_seg, list(reversed(patches))


def unmask(segment: Segment, make_patch_id) -> tuple[Segment, list[Patch]]:
    """把 sentinel 還原成 surface。

    找不到對應 sentinel 的 protection 不是可容忍的狀況 —— 代表某個 Stage
    弄丟了遮罩，呼叫端應依 sentinel 完整性檢查回退該 Stage。
    """
    text = segment.text
    patches: list[Patch] = []
    for p in sorted(segment.protections, key=lambda p: p.sentinel, reverse=True):
        pos = text.find(p.sentinel)
        if pos < 0:
            continue
        patches.append(Patch(
            patch_id=make_patch_id(),
            stage="UNPROTECT",
            segment_id=segment.id,
            span=(pos, pos + len(p.sentinel)),
            before=p.sentinel,
            after=p.surface,
            rule_id="VTR.UNPROTECT.restore",
            source="lexicon" if p.lexicon_id else "deterministic",
            confidence=1.0,
            decision="auto",
            evidence=f"還原 {p.kind}：{p.sentinel} → {p.surface!r}",
        ))
        text = text[:pos] + p.surface + text[pos + len(p.sentinel):]
    return replace(segment, text=text, protections=(), runs=()), patches


# --------------------------------------------------------------------------- #
# 完整性檢查
# --------------------------------------------------------------------------- #

class SentinelViolation(NamedTuple):
    segment_id: str
    missing: tuple[str, ...]
    unexpected: tuple[str, ...]

    def describe(self) -> str:
        parts = []
        if self.missing:
            parts.append(f"遺失 {', '.join(sorted(self.missing))}")
        if self.unexpected:
            parts.append(f"出現未宣告的 {', '.join(sorted(self.unexpected))}")
        return f"segment {self.segment_id}: " + "；".join(parts)


def check_sentinels(segments: Iterable[Segment]) -> list[SentinelViolation]:
    """比對「宣告的 protections」與「文字中實際存在的 sentinel」。

    任何差異都代表某個 Stage 動到了遮罩區。這是回退該 Stage 的唯一判準。
    """
    violations: list[SentinelViolation] = []
    for seg in segments:
        declared = seg.declared_sentinels()
        present = seg.sentinels()
        missing = declared - present
        unexpected = present - declared
        if missing or unexpected:
            violations.append(SentinelViolation(
                segment_id=seg.id,
                missing=tuple(sorted(missing)),
                unexpected=tuple(sorted(unexpected)),
            ))
    return violations
