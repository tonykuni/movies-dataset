"""P0：保護遮罩 Stage（PROTECT）。

本 Stage 直接回傳已遮罩的 segment（而非只回傳 patch），因為遮罩同時要更新
`protections`，兩者必須原子性地一起發生。pipeline 對 PROTECT / UNPROTECT
不重複套用文字（見 pipeline._apply_to）。

目前只接上 pattern 偵測器。SSOT Lexicon 的精確命中（`VTR.PROTECT.lexicon_exact`）
待 lexicon/matcher 模組完成後接入 —— 屆時詞庫命中的優先序高於所有 pattern。
"""

from __future__ import annotations

from dataclasses import replace

from ..context import Context
from ..document import Document, Patch, Segment
from ..pipeline import StageResult
from ..protect import find_candidates, mask


class ProtectStage:
    name = "PROTECT"

    def apply(self, doc: Document, ctx: Context) -> StageResult:
        kinds = list(ctx.config.get(
            "protect.enabled_kinds",
            ["url", "email", "timestamp", "part_number",
             "code_ident", "number_unit"]))

        segments: list[Segment] = []
        patches: list[Patch] = []
        counter = 0
        by_kind: dict[str, int] = {}
        unresolved = 0

        for seg in doc.segments:
            candidates = find_candidates(seg.text, kinds)
            if not candidates:
                segments.append(seg)
                continue

            def _next_id() -> str:
                nonlocal counter
                counter += 1
                return ctx.new_patch_id(counter)

            new_seg, seg_patches = mask(seg, candidates, _next_id)
            segments.append(new_seg)
            patches.extend(seg_patches)

            for c in candidates:
                by_kind[c.kind] = by_kind.get(c.kind, 0) + 1
                if c.unresolved:
                    unresolved += 1

        for kind, n in sorted(by_kind.items()):
            ctx.metrics.set(f"protected_{kind}", n)
        ctx.metrics.set("protected_total", sum(by_kind.values()))
        ctx.metrics.set("unresolved_entities", unresolved)
        ctx.metrics.set("lexicon_attached", ctx.lexicon is not None)
        if ctx.lexicon is None:
            ctx.metrics.set(
                "lexicon_note",
                "SSOT Lexicon 尚未接入；本次僅套用 pattern 遮罩")

        return StageResult(doc=replace(doc, segments=tuple(segments)),
                           patches=tuple(patches))


class UnprotectStage:
    """P0'：還原遮罩（UNPROTECT）。

    放在這裡而非獨立檔案，是因為它與 ProtectStage 是同一個機制的兩端，
    分開維護容易讓 sentinel 格式或 protections 語意漂移。
    """

    name = "UNPROTECT"

    def apply(self, doc: Document, ctx: Context) -> StageResult:
        from ..protect import unmask

        segments: list[Segment] = []
        patches: list[Patch] = []
        counter = 0

        for seg in doc.segments:
            if not seg.protections:
                segments.append(seg)
                continue

            def _next_id() -> str:
                nonlocal counter
                counter += 1
                return ctx.new_patch_id(counter)

            new_seg, seg_patches = unmask(seg, _next_id)
            segments.append(new_seg)
            patches.extend(seg_patches)

        ctx.metrics.set("restored", len(patches))
        return StageResult(doc=replace(doc, segments=tuple(segments)),
                           patches=tuple(patches))
