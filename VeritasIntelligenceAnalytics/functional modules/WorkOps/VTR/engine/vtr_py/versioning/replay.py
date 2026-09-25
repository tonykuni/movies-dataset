"""重播與回滾。

回滾即是重播 —— 不刪除任何東西，只重播到更早的 rev。這讓「回滾」本身也是一個
可稽核的動作，而不是一次無痕的狀態覆寫。

重播的正確性由 content_hash 驗證：重播到 rev N 得到的文件內容雜湊，必須等於
當初記錄在 revision N 上的雜湊。不相等就代表 patch log 與文件已經不一致，
這是嚴重缺陷，直接拋錯而非回傳一份看似合理的結果。
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

from dataclasses import replace

from ..document import Document, Segment, apply_patches, group_by_segment


class ReplayMismatch(RuntimeError):
    """重播結果與記錄的 content_hash 不符。"""


def replay_to(doc: Document, target_rev: int) -> Document:
    """由原始狀態重播到指定 rev。

    `doc` 必須帶有完整的 revisions。回傳的文件只保留 <= target_rev 的 revision。
    """
    revisions = [r for r in doc.revisions if r.rev <= target_rev]
    if not revisions:
        raise ReplayMismatch(f"文件沒有 rev <= {target_rev} 的紀錄")

    # 由最終狀態反推原始狀態：把所有 revision 的 patch 反向套回去。
    cur = doc
    for rev in reversed(doc.revisions):
        cur = _revert(cur, rev)

    # 再正向重播到 target。
    for rev in revisions:
        segments = list(cur.segments)
        by_seg = group_by_segment(rev.patches_applied)
        for i, seg in enumerate(segments):
            ps = by_seg.get(seg.id)
            if ps:
                segments[i] = _forward(seg, ps, rev.stage)
        cur = replace(cur, segments=tuple(segments))
        if cur.content_hash != rev.content_hash:
            raise ReplayMismatch(
                f"重播到 rev {rev.rev}（{rev.stage}）後 content_hash 不符："
                f"重播得 {cur.content_hash[:12]}，紀錄為 {rev.content_hash[:12]}")

    # 標註（lang / runs）是衍生值，不隨 patch 重播 —— 直接由文字重算。
    cur = _refresh_annotations(cur)
    return replace(cur, revisions=tuple(revisions), review_queue=())


def _refresh_annotations(doc: Document) -> Document:
    """重跑 LANG_DETECT 以刷新衍生標註。

    重播只還原內容；標註若沿用舊值會與新文字不一致（例如回滾到正規化之前，
    lang 卻仍是正規化之後判定的值）。因為標註完全由文字決定，重算比重播正確。
    """
    from ..context import Context
    from ..stages.s1_lang_detect import LangDetectStage

    return LangDetectStage().apply(doc, Context()).doc


def _forward(seg: Segment, patches, stage: str) -> Segment:
    if stage in ("PROTECT", "UNPROTECT"):
        return _apply_masking(seg, patches, stage)
    return apply_patches(seg, patches)


def _revert(doc: Document, rev) -> Document:
    """把一個 revision 的 patch 反向套回去。"""
    segments = list(doc.segments)
    by_seg = group_by_segment(rev.patches_applied)
    for i, seg in enumerate(segments):
        ps = by_seg.get(seg.id)
        if not ps:
            continue
        text = seg.text
        # 反向：由前往後，用 after 的長度推回 before。
        #
        # 不需要位移補償：patch 的 span 是「Stage 執行前」的座標，而由前往後
        # 還原時，位置 p.span[0] 之前的內容都已經回到原始長度，因此原始座標
        # 直接就是當下座標。（先前這裡多加了一個累積 offset，導致第二筆之後
        # 全部對錯位置 —— 症狀是 after 與實際文字不符。）
        for p in sorted(ps, key=lambda p: p.span[0]):
            start = p.span[0]
            end = start + len(p.after)
            if text[start:end] != p.after:
                raise ReplayMismatch(
                    f"{p.patch_id}: 反向重播時 after 與實際文字不符 "
                    f"（預期 {p.after!r}，實得 {text[start:end]!r}）")
            text = text[:start] + p.before + text[end:]
        segments[i] = replace(seg, text=text, runs=(), protections=())
    return replace(doc, segments=tuple(segments))


def _apply_masking(seg: Segment, patches, stage: str) -> Segment:
    """PROTECT / UNPROTECT 的重播：套文字並重建 protections。"""
    from ..document import Protection

    text = seg.text
    for p in sorted(patches, key=lambda p: p.span, reverse=True):
        start, end = p.span
        text = text[:start] + p.after + text[end:]

    if stage == "PROTECT":
        protections = tuple(
            Protection(sentinel=p.after, surface=p.before,
                       kind=_kind_of(p.rule_id))
            for p in sorted(patches, key=lambda p: p.span)
        )
        return replace(seg, text=text, protections=protections, runs=())
    return replace(seg, text=text, protections=(), runs=())


def _kind_of(rule_id: str) -> str:
    tail = rule_id.rsplit(".", 1)[-1]
    return tail.replace("pattern_", "") if tail.startswith("pattern_") else "lexicon"
