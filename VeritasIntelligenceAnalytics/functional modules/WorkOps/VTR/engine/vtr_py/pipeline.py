"""Pipeline 執行器：Stage 串接、不變式檢查、patch 套用、版本記錄。

整台引擎的價值不在任何單一 Stage，而在這裡的四條不變式。它們讓「引擎改了什麼」
永遠可回答、可回退、可重播。

Stage 是純函式：(Document, Context) -> StageResult。Stage 不得改動傳入的
Document（dataclass 皆為 frozen），也不得自行套用 patch —— 套用與否由閘門決定。
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Iterable, Protocol, Sequence

from . import protect as protect_mod
from . import rules
from .context import Context, Metrics
from .document import (
    ContractError,
    Document,
    Patch,
    Revision,
    Segment,
    apply_patches,
    group_by_segment,
)


@dataclass(frozen=True)
class StageResult:
    doc: Document
    patches: tuple[Patch, ...] = ()
    metrics: dict[str, Any] = field(default_factory=dict)


class Stage(Protocol):
    name: str

    def apply(self, doc: Document, ctx: Context) -> StageResult: ...


class InvariantViolation(RuntimeError):
    """Stage 違反了 pipeline 不變式。"""


# --------------------------------------------------------------------------- #
# 不變式
# --------------------------------------------------------------------------- #

def check_invariants(
    before: Document, result: StageResult, stage_name: str
) -> list[str]:
    """回傳違反項目的說明；空 list 代表通過。

    1. 只有 SEGMENT 可以改變 segment 數量
    2. PROTECT 與 UNPROTECT 之間，sentinel 必須原封不動
    3. 每個 patch 的 span 必須落在套用當下的合法範圍
    4. 每個 rule_id 必須已註冊，且屬於宣稱的 stage
    """
    problems: list[str] = []
    after = result.doc

    # (1) segment 數量
    if stage_name != "SEGMENT" and len(after.segments) != len(before.segments):
        problems.append(
            f"{stage_name} 改變了 segment 數量 "
            f"（{len(before.segments)} → {len(after.segments)}）；"
            "只有 SEGMENT 步驟可以這麼做")

    # (2) sentinel 完整性 —— UNPROTECT 本來就是要移除 sentinel，故豁免
    if stage_name != "UNPROTECT":
        for v in protect_mod.check_sentinels(after.segments):
            problems.append(f"sentinel 完整性違反 —— {v.describe()}")

    # (3) patch span 合法性（以 stage 執行前的文字為座標系）
    by_seg = group_by_segment(result.patches)
    for seg_id, patches in by_seg.items():
        try:
            source_seg = before.segment(seg_id)
        except KeyError:
            if stage_name != "SEGMENT":
                problems.append(f"patch 指向不存在的 segment {seg_id}")
            continue
        for p in patches:
            start, end = p.span
            if end > len(source_seg.text):
                problems.append(
                    f"{p.patch_id}: span {p.span} 超出 segment {seg_id} "
                    f"長度 {len(source_seg.text)}")
            elif source_seg.text[start:end] != p.before:
                problems.append(
                    f"{p.patch_id}: before 與 stage 執行前的文字不符 "
                    f"（預期 {p.before!r}，實得 {source_seg.text[start:end]!r}）")

    # (4) rule_id 註冊
    for p in result.patches:
        try:
            rules.require(p.rule_id, p.stage)
        except rules.UnknownRuleError as exc:
            problems.append(f"{p.patch_id}: {exc}")
        if p.stage != stage_name:
            problems.append(
                f"{p.patch_id}: stage 標為 {p.stage}，但由 {stage_name} 產生")

    return problems


# --------------------------------------------------------------------------- #
# 執行器
# --------------------------------------------------------------------------- #

def commit(doc: Document, result: StageResult, stage_name: str,
           ctx: Context, problems: Sequence[str]) -> Document:
    """依閘門決定套用哪些 patch，並寫入一筆 revision。

    回退語意：不變式違反時，本 Stage 的 **所有** patch 一律不套用，但仍寫入
    revision 記錄違反原因。刻意不做「部分套用」—— 一個弄壞遮罩的 Stage，
    它其他的判斷也不再可信。
    """
    rev_no = doc.rev + 1
    metrics = dict(result.metrics)

    if problems:
        metrics["stage_rolled_back"] = True
        metrics["invariant_violations"] = list(problems)
        metrics["patches_discarded"] = len(result.patches)
        new_doc = doc  # 內容完全不動
        applied: tuple[Patch, ...] = ()
        review: tuple[Patch, ...] = ()
    else:
        applied = tuple(p for p in result.patches
                        if p.decision == "auto" and not p.is_noop)
        review = tuple(p for p in result.patches if p.decision == "review")
        rejected = [p for p in result.patches if p.decision == "reject"]

        segments = list(result.doc.segments)
        by_seg = group_by_segment(applied)
        for i, seg in enumerate(segments):
            seg_patches = by_seg.get(seg.id)
            if seg_patches:
                segments[i] = _apply_to(result.doc, seg, seg_patches, stage_name)

        new_doc = replace(
            result.doc,
            segments=tuple(segments),
            review_queue=result.doc.review_queue + review,
        )
        metrics["patches_proposed"] = len(result.patches)
        metrics["patches_applied"] = len(applied)
        metrics["patches_review"] = len(review)
        metrics["patches_rejected"] = len(rejected)

    revision = Revision(
        rev=rev_no,
        stage=stage_name,
        at=ctx.clock(),
        engine=ctx.engine,
        content_hash=new_doc.content_hash,
        patches_applied=applied,
        metrics=metrics,
    )
    return replace(new_doc, revisions=new_doc.revisions + (revision,))


def _apply_to(doc: Document, seg: Segment, patches: list[Patch],
              stage_name: str) -> Segment:
    """套用單一 segment 的 patch。

    PROTECT / UNPROTECT 的 Stage 已經回傳了遮罩後的 segment（因為它同時要更新
    protections），所以文字已是最終狀態，不再重複套用。
    """
    if stage_name in ("PROTECT", "UNPROTECT"):
        return seg
    return apply_patches(seg, patches)


@dataclass
class Pipeline:
    stages: tuple[Stage, ...]

    def run(self, doc: Document, ctx: Context) -> Document:
        strict = bool(ctx.config.get("pipeline.strict", False))
        cur = doc
        for stage in self.stages:
            ctx.metrics = Metrics()
            ctx.rev = cur.rev + 1
            ctx.stage = stage.name

            result = stage.apply(cur, ctx)
            merged = StageResult(
                doc=result.doc,
                patches=tuple(result.patches),
                metrics={**ctx.metrics.as_dict(), **result.metrics},
            )
            problems = check_invariants(cur, merged, stage.name)
            if problems and strict:
                raise InvariantViolation(
                    f"{stage.name} 違反不變式:\n  - " + "\n  - ".join(problems))
            cur = commit(cur, merged, stage.name, ctx, problems)
        return cur


def preprocessing_pipeline() -> Pipeline:
    """Preprocessing Pipeline（00_ARCHITECTURE.md §4）。

    步驟 1 → 2 → P0。全部確定性、零第三方相依、冪等。
    """
    from .stages.s1_lang_detect import LangDetectStage
    from .stages.s2_normalize import NormalizeStage
    from .stages.s3_protect import ProtectStage

    return Pipeline(stages=(
        LangDetectStage(),
        NormalizeStage(),
        ProtectStage(),
        # LANG_DETECT 再跑一次：遮罩改變了字面，run 必須重算，
        # 否則後續雙語分流會拿到過期的 run 座標。
        LangDetectStage(),
    ))


def rejected_and_review(doc: Document) -> tuple[list[Patch], list[Patch]]:
    review = list(doc.review_queue)
    applied = [p for r in doc.revisions for p in r.patches_applied]
    return applied, review
