"""VTR Document 資料契約的 Python 實作。

對應 `contracts/vtr-document.schema.json`。該 JSON Schema 是 SSOT；本模組是它的
Python 綁定，不是第二套真實來源。欄位名稱與語意必須與 schema 逐字一致。

刻意只用標準函式庫：確定性層（步驟 1–2 + PROTECT）必須能在沒有安裝任何第三方
套件的環境跑起來，包含 CI。模型層（步驟 3 以後）才會引入 torch / transformers。
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

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field, replace
from typing import Any, Iterable, Literal, Optional

SCHEMA_VERSION = "vtr-document/1.0"

Lang = Literal["zh", "en", "mixed"]
Decision = Literal["auto", "review", "reject"]
Source = Literal["deterministic", "model", "lexicon", "llm_arbiter", "human"]
Script = Literal["cjk", "latin", "digit", "punct", "other"]
RunRole = Literal["main", "embedded", "protected"]

SENTINEL_RE = re.compile(r"⟦P\d{4}⟧")
SEGMENT_ID_RE = re.compile(r"^s\d{5,}$")

PROTECTION_KINDS = (
    "lexicon", "part_number", "url", "email",
    "code_ident", "number_unit", "timestamp", "id_code",
)

STAGE_NAMES = (
    "LANG_DETECT", "NORMALIZE", "PROTECT", "PUNCTUATE", "SEGMENT",
    "SPELL", "GRAMMAR", "LEXICON", "STRUCTURE", "UNPROTECT",
)


class ContractError(ValueError):
    """Document 不符合資料契約。"""


# --------------------------------------------------------------------------- #
# 值物件
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Run:
    """句內的 script run（見 00_ARCHITECTURE.md §5.1）。"""

    start: int
    end: int
    script: Script
    role: RunRole = "main"

    def slice_of(self, text: str) -> str:
        return text[self.start:self.end]


@dataclass(frozen=True)
class Protection:
    """P0 遮罩區。sentinel 在遮罩期間取代 surface。"""

    sentinel: str
    surface: str
    kind: str
    lexicon_id: Optional[str] = None

    def __post_init__(self) -> None:
        if not SENTINEL_RE.fullmatch(self.sentinel):
            raise ContractError(f"sentinel 格式不合法: {self.sentinel!r}")
        if self.kind not in PROTECTION_KINDS:
            raise ContractError(f"protection.kind 不合法: {self.kind!r}")


@dataclass(frozen=True)
class Patch:
    """單一改動。這是引擎與人之間唯一的溝通單位。"""

    patch_id: str
    stage: str
    segment_id: str
    span: tuple[int, int]
    before: str
    after: str
    rule_id: str
    source: Source
    confidence: float
    decision: Decision
    evidence: Optional[str] = None

    def __post_init__(self) -> None:
        if self.stage not in STAGE_NAMES:
            raise ContractError(f"未知 stage: {self.stage!r}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ContractError(f"confidence 超出 [0,1]: {self.confidence}")
        if self.span[0] > self.span[1] or self.span[0] < 0:
            raise ContractError(f"span 不合法: {self.span}")

    @property
    def is_noop(self) -> bool:
        return self.before == self.after


@dataclass(frozen=True)
class Revision:
    """append-only。每個 Stage 產生一個。"""

    rev: int
    stage: str
    at: str
    engine: str
    content_hash: str
    patches_applied: tuple[Patch, ...] = ()
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Segment:
    id: str
    lang: Lang
    text: str
    speaker: Optional[str] = None
    t_start: Optional[float] = None
    t_end: Optional[float] = None
    runs: tuple[Run, ...] = ()
    protections: tuple[Protection, ...] = ()
    flags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not SEGMENT_ID_RE.match(self.id):
            raise ContractError(f"segment id 格式不合法: {self.id!r}")

    def sentinels(self) -> set[str]:
        """目前文字中實際存在的 sentinel（不是 protections 宣告的）。

        兩者的差異就是 sentinel 完整性違反 —— 見 pipeline.assert_invariants。
        """
        return set(SENTINEL_RE.findall(self.text))

    def declared_sentinels(self) -> set[str]:
        return {p.sentinel for p in self.protections}


@dataclass(frozen=True)
class Document:
    doc_id: str
    meta: dict[str, Any]
    segments: tuple[Segment, ...] = ()
    revisions: tuple[Revision, ...] = ()
    review_queue: tuple[Patch, ...] = ()
    structure: Optional[dict[str, Any]] = None
    schema_version: str = SCHEMA_VERSION

    # -- 衍生 --------------------------------------------------------------- #

    @property
    def content_hash(self) -> str:
        """segments 的正規化序列化 SHA-256。

        **只涵蓋內容，不涵蓋衍生標註。** `lang` 與 `runs` 由 LANG_DETECT 從
        text 完全決定，且該步驟不產生 patch —— 若把它們算進雜湊，patch 重播
        就永遠無法重建當初記錄的雜湊值（重播只會套 patch，不會重跑標註）。

        實務上這也是正確的語意：雜湊要回答的是「文字內容是不是同一份」，
        而不是「標註跑過沒有」。標註隨時可由 text 重算。
        """
        payload = [
            {
                "id": s.id,
                "text": s.text,
                "speaker": s.speaker,
                "t_start": s.t_start,
                "t_end": s.t_end,
                "protections": [
                    {"sentinel": p.sentinel, "surface": p.surface,
                     "kind": p.kind, "lexicon_id": p.lexicon_id}
                    for p in s.protections
                ],
            }
            for s in self.segments
        ]
        blob = json.dumps(payload, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"))
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    @property
    def rev(self) -> int:
        return self.revisions[-1].rev if self.revisions else -1

    def segment(self, segment_id: str) -> Segment:
        for s in self.segments:
            if s.id == segment_id:
                return s
        raise KeyError(f"找不到 segment {segment_id!r}")

    def with_segments(self, segments: Iterable[Segment]) -> "Document":
        return replace(self, segments=tuple(segments))

    def text(self, joiner: str = "\n") -> str:
        return joiner.join(s.text for s in self.segments)

    # -- 序列化 ------------------------------------------------------------- #

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["content_hash"] = self.content_hash
        d["segments"] = [_strip_none_lists(s) for s in d["segments"]]
        for r in d["revisions"]:
            r["patches_applied"] = [_patch_out(p) for p in r["patches_applied"]]
        d["review_queue"] = [_patch_out(p) for p in d["review_queue"]]
        if d.get("structure") is None:
            d.pop("structure", None)
        return d

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent) + "\n"

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "Document":
        version = d.get("schema_version")
        if version != SCHEMA_VERSION:
            raise ContractError(
                f"schema_version 應為 {SCHEMA_VERSION}，實得 {version!r}")
        segments = tuple(
            Segment(
                id=s["id"], lang=s["lang"], text=s["text"],
                speaker=s.get("speaker"), t_start=s.get("t_start"),
                t_end=s.get("t_end"),
                runs=tuple(Run(**r) for r in s.get("runs", [])),
                protections=tuple(Protection(**p) for p in s.get("protections", [])),
                flags=tuple(s.get("flags", [])),
            )
            for s in d.get("segments", [])
        )
        revisions = tuple(
            Revision(
                rev=r["rev"], stage=r["stage"], at=r["at"],
                engine=r.get("engine", "unknown"),
                content_hash=r["content_hash"],
                patches_applied=tuple(_patch_in(p) for p in r.get("patches_applied", [])),
                metrics=r.get("metrics", {}),
            )
            for r in d.get("revisions", [])
        )
        return Document(
            doc_id=d["doc_id"], meta=d.get("meta", {}), segments=segments,
            revisions=revisions,
            review_queue=tuple(_patch_in(p) for p in d.get("review_queue", [])),
            structure=d.get("structure"),
        )

    @staticmethod
    def from_json(text: str) -> "Document":
        return Document.from_dict(json.loads(text))

    @staticmethod
    def from_raw_text(
        raw: str, doc_id: str, meta: Optional[dict[str, Any]] = None
    ) -> "Document":
        """由原始逐字稿建立 rev -1 的文件。

        此時尚未經過 LANG_DETECT，因此 lang 一律先標 mixed —— **不猜測**。
        每個非空行成為一個 segment（ASR 輸出的自然單位）。
        """
        meta = dict(meta or {})
        meta.setdefault("source", "asr")
        meta.setdefault("primary_lang", "mixed")
        lines = [ln.strip() for ln in raw.splitlines()]
        segments = tuple(
            Segment(id=f"s{i:05d}", lang="mixed", text=ln)
            for i, ln in enumerate(l for l in lines if l)
        )
        return Document(doc_id=doc_id, meta=meta, segments=segments)


# --------------------------------------------------------------------------- #
# Patch 套用
# --------------------------------------------------------------------------- #

def apply_patches(segment: Segment, patches: Iterable[Patch]) -> Segment:
    """把 patch 套到單一 segment。

    由後往前套用，因此前面的 span 座標不會位移。重疊的 patch 是引擎缺陷，
    直接拋錯而不是靜默取其一 —— 靜默取捨會讓 patch log 與實際結果不符，
    整條稽核鏈就失效了。
    """
    ordered = sorted(patches, key=lambda p: p.span, reverse=True)
    text = segment.text
    prev_start: Optional[int] = None
    for p in ordered:
        start, end = p.span
        if end > len(text):
            raise ContractError(
                f"{p.patch_id}: span {p.span} 超出 segment {segment.id} 長度 {len(text)}")
        if text[start:end] != p.before:
            raise ContractError(
                f"{p.patch_id}: before 與實際文字不符 "
                f"（預期 {p.before!r}，實得 {text[start:end]!r}）")
        if prev_start is not None and end > prev_start:
            raise ContractError(f"{p.patch_id}: 與後續 patch 的 span 重疊")
        text = text[:start] + p.after + text[end:]
        prev_start = start
    # 文字改變後，既有 runs 的座標已失效，一律清空由 LANG_DETECT 重算。
    return replace(segment, text=text, runs=())


def group_by_segment(patches: Iterable[Patch]) -> dict[str, list[Patch]]:
    out: dict[str, list[Patch]] = {}
    for p in patches:
        out.setdefault(p.segment_id, []).append(p)
    return out


# --------------------------------------------------------------------------- #
# 內部
# --------------------------------------------------------------------------- #

def _patch_out(p: dict[str, Any]) -> dict[str, Any]:
    p = dict(p)
    p["span"] = list(p["span"])
    return p


def _patch_in(p: dict[str, Any]) -> Patch:
    return Patch(
        patch_id=p["patch_id"], stage=p["stage"], segment_id=p["segment_id"],
        span=(p["span"][0], p["span"][1]), before=p["before"], after=p["after"],
        rule_id=p["rule_id"], source=p.get("source", "deterministic"),
        confidence=p["confidence"], decision=p["decision"],
        evidence=p.get("evidence"),
    )


def _strip_none_lists(s: dict[str, Any]) -> dict[str, Any]:
    s = dict(s)
    for key in ("runs", "protections", "flags"):
        s[key] = list(s.get(key) or [])
    return s
