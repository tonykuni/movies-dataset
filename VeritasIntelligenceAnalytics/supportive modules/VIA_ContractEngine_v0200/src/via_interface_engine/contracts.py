"""Core interface, protocol, metadata, lifecycle, and result contracts."""

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

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from enum import StrEnum
import re
from types import MappingProxyType
from typing import Any, ClassVar, Literal, Mapping

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from .config import (
    DEFAULT_AUTHOR,
    DEFAULT_LANGUAGE,
    DEFAULT_SUBSYSTEM,
    DEPENDENCY_URN_PATTERN,
    ENGINE_COMPATIBILITY,
    MODULE_NAME_PATTERN,
    SEMANTIC_VERSION_PATTERN,
)


# def 01 BASE DATA CONTRACTS
class VIAInputModel(BaseModel):
    """Default input policy: coerce HTML strings, forbid unknown fields."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class VIAOutputModel(BaseModel):
    """Default output policy: deterministic and closed to unknown fields."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )


# def 02 MANIFEST CONTRACT
class ModuleManifest(VIAInputModel):
    """Validated, self-describing metadata required from every module."""

    name: str = Field(
        ...,
        pattern=MODULE_NAME_PATTERN,
        description="全域唯一模組名稱",
    )
    version: str = Field(
        ...,
        pattern=SEMANTIC_VERSION_PATTERN,
        description="Semantic Version",
    )
    author: str = Field(default=DEFAULT_AUTHOR, min_length=1, max_length=128)
    description: str = Field(default="", max_length=1000)
    subsystem: str = Field(default=DEFAULT_SUBSYSTEM, min_length=2, max_length=64)
    language: Literal["PY", "PS", "JS", "JSON", "HTML"] = DEFAULT_LANGUAGE
    capability: str | None = Field(default=None, min_length=2, max_length=64)
    dependencies: tuple[str, ...] = Field(
        default_factory=tuple,
        validation_alias=AliasChoices("dependencies", "requires"),
    )
    engine_compat: str = Field(default=ENGINE_COMPATIBILITY)
    permissions: tuple[str, ...] = Field(default_factory=tuple)
    tags: tuple[str, ...] = Field(default_factory=tuple)
    enabled: bool = True

    @field_validator("dependencies")
    @classmethod
    def def_validate_dependencies(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(item.strip() for item in value)
        if any(not item for item in normalized):
            raise ValueError("dependencies 不得包含空白名稱")
        for item in normalized:
            is_name = re.fullmatch(MODULE_NAME_PATTERN, item) is not None
            is_urn = re.fullmatch(DEPENDENCY_URN_PATTERN, item, flags=re.IGNORECASE) is not None
            if not is_name and not is_urn:
                raise ValueError("dependencies 必須使用合法模組名稱或 URN")
        if len(set(normalized)) != len(normalized):
            raise ValueError("dependencies 不得重複")
        return normalized


# def 03 LIFECYCLE CONTRACTS
class ModuleState(StrEnum):
    DISCOVERED = "DISCOVERED"
    SETTING_UP = "SETTING_UP"
    READY = "READY"
    EXECUTING = "EXECUTING"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"
    PAUSED = "PAUSED"
    ERROR = "ERROR"
    TEARING_DOWN = "TEARING_DOWN"
    UNLOADED = "UNLOADED"


class ExecutionStatus(StrEnum):
    SUCCESS = "SUCCESS"
    REJECTED = "REJECTED"
    ERROR = "ERROR"


class ModuleContext:
    """Read-only, namespaced context supplied during module setup."""

    def __init__(
        self,
        *,
        run_id: str,
        subsystem: str,
        config: Mapping[str, Any] | None = None,
    ) -> None:
        self._run_id = run_id
        self._subsystem = subsystem
        self._config = MappingProxyType(dict(config or {}))

    @property
    def run_id(self) -> str:
        return self._run_id

    @property
    def subsystem(self) -> str:
        return self._subsystem

    @property
    def config(self) -> Mapping[str, Any]:
        return self._config


class VIAModuleABC(ABC):
    """Mandatory interface implemented by every governed VIA module."""

    __manifest__: ClassVar[Mapping[str, Any] | ModuleManifest]

    @abstractmethod
    def setup(self, context: ModuleContext) -> None:
        """Initialize the module using a read-only namespaced context."""

    def on_load(self, context: ModuleContext) -> None:
        """Canonical load hook; delegates to the mandatory setup contract."""

        self.setup(context)

    @abstractmethod
    def health_check(self) -> bool:
        """Prove that the module is alive without mutating business state."""

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> VIAOutputModel:
        """Run business logic through explicit typed arguments."""

    @abstractmethod
    def teardown(self) -> None:
        """Release every resource acquired by the module."""


# def 04 EXECUTION RESULT CONTRACT
class ExecutionEnvelope(VIAOutputModel):
    module_name: str
    resource_urn: str | None = None
    status: ExecutionStatus
    output: dict[str, Any] | None = None
    errors: list[dict[str, Any]] = Field(default_factory=list)
    message: str = ""


class CommandSchemaRecord(VIAOutputModel):
    module_name: str
    resource_urn: str
    manifest: dict[str, Any]
    input_parameter: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    injected_dependencies: list[dict[str, str]]


class RegistryMetricsSnapshot(VIAOutputModel):
    success_count: int = 0
    failure_count: int = 0
    validation_rejection_count: int = 0
    timeout_count: int = 0
    health_check_count: int = 0
    health_failure_count: int = 0
    last_latency_ms: float | None = None
    last_error: str = ""
    last_success_at: str | None = None
    updated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class RegistryRecordSnapshot(VIAOutputModel):
    resource_urn: str
    module_name: str
    version: str
    state: ModuleState
    declared_dependencies: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    source_ref: str
    source_sha256: str
    process_id: int
    instance_locator: str
    registered_at: str
    metrics: RegistryMetricsSnapshot
