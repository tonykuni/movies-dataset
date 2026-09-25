"""append-only patch log（JSONL）。

一行一個 Patch，永不修改。這是稽核鏈的實體形式：任何時候都能回答
「這句話為什麼變成現在這樣」，而答案是一串可讀的、帶 rule_id 與 evidence
的紀錄，不是一個黑箱模型的輸出。
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

import json
from pathlib import Path
from typing import Iterable, Iterator

from ..document import Document, Patch, _patch_in  # type: ignore[attr-defined]

PATCHLOG_NAME = "patches.jsonl"


def _row(rev: int, stage: str, at: str, p: Patch) -> dict:
    return {
        "rev": rev, "stage": stage, "at": at,
        "patch_id": p.patch_id, "segment_id": p.segment_id,
        "span": list(p.span), "before": p.before, "after": p.after,
        "rule_id": p.rule_id, "source": p.source,
        "confidence": p.confidence, "decision": p.decision,
        "evidence": p.evidence,
    }


def write_patchlog(doc: Document, path: Path) -> int:
    """把文件的完整 patch 歷史寫成 JSONL。

    包含已套用的 patch 與待裁決佇列 —— review 佇列也是歷史的一部分，
    只是它的 decision 不是 auto。
    """
    lines: list[str] = []
    for rev in doc.revisions:
        for p in rev.patches_applied:
            lines.append(json.dumps(_row(rev.rev, rev.stage, rev.at, p),
                                    ensure_ascii=False))
    for p in doc.review_queue:
        lines.append(json.dumps(
            {**_row(-1, p.stage, "", p), "queued": True}, ensure_ascii=False))

    Path(path).write_text("\n".join(lines) + ("\n" if lines else ""),
                          encoding="utf-8")
    return len(lines)


def read_patchlog(path: Path) -> Iterator[dict]:
    text = Path(path).read_text(encoding="utf-8")
    for line in text.splitlines():
        line = line.strip()
        if line:
            yield json.loads(line)


def patches_of_rev(rows: Iterable[dict], rev: int) -> list[Patch]:
    return [_patch_in(r) for r in rows if r.get("rev") == rev]
