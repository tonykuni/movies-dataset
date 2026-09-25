"""Dependency-free request and response contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


TaskName = Literal[
    "auto",
    "analyze",
    "reorganize",
    "knowledge",
    "govern",
    "translate",
    "normalize",
    "repair",
    "keywords",
    "classify",
    "entities",
    "structure",
    "restore_transcript",
    "summarize",
    "embed",
    "chat",
]


@dataclass(slots=True)
class ProcessRequest:
    text: str
    task: TaskName = "auto"
    language: str = "auto"
    quality: Literal["fast", "balanced", "deep"] = "balanced"
    tier: int | None = None
    options: dict[str, Any] = field(default_factory=dict)
    request_id: str | None = None


@dataclass(slots=True)
class RouteDecision:
    task: str
    requested_tier: int
    selected_tier: int
    pipeline: list[str]
    degraded: bool = False
    reason: str = ""


@dataclass(slots=True)
class ResourceSnapshot:
    timestamp: str
    ram_percent: float
    available_ram_mb: float
    process_rss_mb: float
    cpu_percent: float
    pressure: Literal["normal", "warning", "shed", "critical", "unknown"]
    source: str


@dataclass(slots=True)
class ProcessResult:
    request_id: str
    task: str
    language: str
    output: dict[str, Any]
    route: RouteDecision
    resources_before: ResourceSnapshot
    resources_after: ResourceSnapshot
    elapsed_ms: float
    cache_hit: bool = False
    warnings: list[str] = field(default_factory=list)
    engine_version: str = "1.1.0"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class FeedbackRecord:
    request_id: str
    task: str
    text: str
    predicted_label: str | None = None
    corrected_label: str | None = None
    corrected_text: str | None = None
    accepted: bool = True
    note: str = ""


@dataclass(slots=True)
class BatchItem:
    item_id: str
    request: ProcessRequest
