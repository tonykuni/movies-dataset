#!/usr/bin/env python3
"""Shared contracts and utilities for every GenericLayoutEngine backend."""

from __future__ import annotations

# =============================================================================
# 01. PARAMETERS
# =============================================================================

ADAPTER_SCHEMA_VERSION = "GLE-ADAPTER/2.0"
DEFAULT_ADAPTER_TIMEOUT_SECONDS = 300
DEFAULT_HEAVY_ADAPTER_TIMEOUT_SECONDS = 900
DEFAULT_MIN_TEXT_CHARACTERS = 40
DEFAULT_MIN_READABLE_RATIO = 0.70
DEFAULT_MAX_REPLACEMENT_RATIO = 0.03
DEFAULT_MAX_DUPLICATE_RATIO = 0.40
DEFAULT_MIN_FREE_MEMORY_GB_HEAVY = 4.0
DEFAULT_MAX_OUTPUT_CHARACTERS = 8_000_000

STATUS_PASS = "PASS"
STATUS_WARN = "WARN"
STATUS_FAIL = "FAIL"
STATUS_SKIPPED_UNAVAILABLE = "SKIPPED_UNAVAILABLE"
STATUS_SKIPPED_POLICY = "SKIPPED_POLICY"
STATUS_TIMEOUT = "TIMEOUT"


# =============================================================================
# 02. IMPORTS
# =============================================================================

import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import time
import unicodedata
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional, Sequence


# =============================================================================
# 03. DATA CONTRACTS
# =============================================================================

@dataclass
class AdapterConfig:
    timeout_seconds: int = DEFAULT_ADAPTER_TIMEOUT_SECONDS
    heavy_timeout_seconds: int = DEFAULT_HEAVY_ADAPTER_TIMEOUT_SECONDS
    min_text_characters: int = DEFAULT_MIN_TEXT_CHARACTERS
    min_readable_ratio: float = DEFAULT_MIN_READABLE_RATIO
    max_replacement_ratio: float = DEFAULT_MAX_REPLACEMENT_RATIO
    max_duplicate_ratio: float = DEFAULT_MAX_DUPLICATE_RATIO
    min_free_memory_gb_heavy: float = DEFAULT_MIN_FREE_MEMORY_GB_HEAVY
    max_output_characters: int = DEFAULT_MAX_OUTPUT_CHARACTERS
    ocr_languages: str = "chi_tra+chi_sim+eng"
    dpi: int = 180
    device: str = "cpu"
    model_cache_dir: Optional[str] = None
    allow_model_downloads: bool = False
    allow_cloud_backends: bool = False
    environment: dict[str, str] = field(default_factory=dict)


@dataclass
class AdapterProbe:
    name: str
    available: bool
    module_available: bool = False
    binary_available: bool = False
    configured: bool = True
    version: Optional[str] = None
    reason: str = ""


@dataclass
class AdapterElement:
    page: int
    text: str = ""
    bbox: Optional[list[float]] = None
    element_type: str = "TEXT"
    subtype: str = "BODY"
    confidence: float = 1.0
    reading_order: Optional[int] = None
    row: Optional[int] = None
    column: Optional[int] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def fingerprint(self, adapter_name: str) -> str:
        seed = json.dumps(
            [adapter_name, self.page, self.bbox, normalize_text(self.text), self.element_type, self.subtype],
            ensure_ascii=False,
            sort_keys=True,
        )
        return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16].upper()


@dataclass
class QualityMetrics:
    character_count: int = 0
    readable_ratio: float = 0.0
    replacement_ratio: float = 0.0
    duplicate_ratio: float = 0.0
    element_count: int = 0
    page_count: int = 0
    bbox_element_ratio: float = 0.0
    table_count: int = 0
    figure_count: int = 0
    quality_score: float = 0.0


@dataclass
class AdapterResult:
    adapter_name: str
    resource_level: int
    priority: int
    status: str
    started_utc: str
    duration_ms: int
    capabilities: list[str]
    probe: AdapterProbe
    elements: list[AdapterElement] = field(default_factory=list)
    document_text: str = ""
    markdown: str = ""
    artifacts: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    error: Optional[str] = None
    quality: QualityMetrics = field(default_factory=QualityMetrics)
    accepted: bool = False
    stop_reason: Optional[str] = None

    def to_dict(self, include_elements: bool = True) -> dict[str, Any]:
        payload = asdict(self)
        if not include_elements:
            payload.pop("elements", None)
            payload["element_count"] = len(self.elements)
        return payload


@dataclass
class AdapterContext:
    input_path: Path
    work_dir: Path
    config: AdapterConfig
    page_images: list[Path] = field(default_factory=list)
    document_profile: dict[str, Any] = field(default_factory=dict)


# =============================================================================
# 04. TEXT, QUALITY, PROCESS, AND RESOURCE UTILITIES
# =============================================================================

def utc_timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def normalize_text(value: str) -> str:
    text = unicodedata.normalize("NFKC", value or "")
    text = text.replace("\u00ad", "").replace("\u200b", "")
    text = re.sub(r"[ \t\u3000]+", " ", text)
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def text_signature(value: str) -> str:
    text = normalize_text(value).casefold()
    text = re.sub(r"\d+", "#", text)
    return re.sub(r"[^\w\u3400-\u9fff#]+", "", text)[:300]


def readable_character_ratio(value: str) -> float:
    if not value:
        return 0.0
    useful = 0
    for character in value:
        category = unicodedata.category(character)
        if character.isspace() or category[0] in {"L", "N", "P", "S"}:
            useful += 1
    return useful / len(value)


def replacement_character_ratio(value: str) -> float:
    if not value:
        return 0.0
    bad = value.count("�") + value.count("\x00")
    return bad / len(value)


def duplicate_line_ratio(value: str) -> float:
    lines = [text_signature(line) for line in value.splitlines() if len(text_signature(line)) >= 4]
    if not lines:
        return 0.0
    return max(0.0, 1.0 - len(set(lines)) / len(lines))


def compute_quality(result: AdapterResult) -> QualityMetrics:
    text = normalize_text(result.document_text or "\n".join(element.text for element in result.elements))
    character_count = len(text)
    bbox_count = sum(1 for element in result.elements if element.bbox and len(element.bbox) == 4)
    page_numbers = {element.page for element in result.elements if element.page > 0}
    metrics = QualityMetrics(
        character_count=character_count,
        readable_ratio=readable_character_ratio(text),
        replacement_ratio=replacement_character_ratio(text),
        duplicate_ratio=duplicate_line_ratio(text),
        element_count=len(result.elements),
        page_count=max(page_numbers, default=0),
        bbox_element_ratio=bbox_count / max(1, len(result.elements)),
        table_count=sum(1 for element in result.elements if element.element_type == "TABLE" and element.subtype == "CONTENT"),
        figure_count=sum(1 for element in result.elements if element.element_type == "FIGURE" and element.subtype == "CONTENT"),
    )
    length_score = min(1.0, character_count / 1200.0)
    metrics.quality_score = max(
        0.0,
        min(
            1.0,
            0.30 * length_score
            + 0.30 * metrics.readable_ratio
            + 0.20 * metrics.bbox_element_ratio
            + 0.10 * (1.0 - metrics.replacement_ratio)
            + 0.10 * (1.0 - metrics.duplicate_ratio),
        ),
    )
    result.quality = metrics
    return metrics


def evaluate_acceptance(result: AdapterResult, config: AdapterConfig) -> tuple[bool, str]:
    metrics = compute_quality(result)
    if result.status not in {STATUS_PASS, STATUS_WARN}:
        return False, f"adapter status is {result.status}"
    if metrics.character_count < config.min_text_characters and "ocr" not in result.capabilities:
        return False, f"text too short: {metrics.character_count}"
    if metrics.readable_ratio < config.min_readable_ratio:
        return False, f"readable ratio too low: {metrics.readable_ratio:.3f}"
    if metrics.replacement_ratio > config.max_replacement_ratio:
        return False, f"replacement ratio too high: {metrics.replacement_ratio:.3f}"
    if metrics.duplicate_ratio > config.max_duplicate_ratio:
        return False, f"duplicate ratio too high: {metrics.duplicate_ratio:.3f}"
    return True, "quality gate passed"


def module_exists(module_name: Optional[str]) -> bool:
    return bool(module_name and importlib.util.find_spec(module_name))


def binary_path(binary_name: Optional[str]) -> Optional[str]:
    return shutil.which(binary_name) if binary_name else None


def package_version(distribution_name: str) -> Optional[str]:
    try:
        from importlib.metadata import version

        return version(distribution_name)
    except Exception:
        return None


def available_memory_gb() -> Optional[float]:
    try:
        import psutil  # type: ignore

        return psutil.virtual_memory().available / (1024 ** 3)
    except Exception:
        return None


def heavy_resource_gate(config: AdapterConfig) -> tuple[bool, str]:
    free_gb = available_memory_gb()
    if free_gb is None:
        return True, "memory telemetry unavailable"
    if free_gb < config.min_free_memory_gb_heavy:
        return False, f"free memory {free_gb:.2f} GB below {config.min_free_memory_gb_heavy:.2f} GB"
    return True, f"free memory {free_gb:.2f} GB"


def merged_environment(config: AdapterConfig) -> dict[str, str]:
    environment = dict(os.environ)
    environment.update(config.environment)
    if config.model_cache_dir:
        environment.setdefault("HF_HOME", config.model_cache_dir)
        environment.setdefault("PADDLE_HOME", str(Path(config.model_cache_dir) / "paddle"))
    if not config.allow_model_downloads:
        environment.setdefault("HF_HUB_OFFLINE", "1")
        environment.setdefault("TRANSFORMERS_OFFLINE", "1")
    return environment


def run_command(
    command: Sequence[str],
    config: AdapterConfig,
    timeout_seconds: Optional[int] = None,
    cwd: Optional[Path] = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout_seconds or config.timeout_seconds,
        cwd=str(cwd) if cwd else None,
        env=merged_environment(config),
    )


def truncate_output(value: str, limit: int) -> tuple[str, bool]:
    if len(value) <= limit:
        return value, False
    return value[:limit], True


# =============================================================================
# 05. BASE ADAPTER
# =============================================================================

class BaseAdapter(ABC):
    name = "base"
    resource_level = 1
    priority = 1000
    capabilities: tuple[str, ...] = ()
    heavy = False

    @abstractmethod
    def probe(self, context: AdapterContext) -> AdapterProbe:
        raise NotImplementedError

    @abstractmethod
    def extract(self, context: AdapterContext) -> AdapterResult:
        raise NotImplementedError

    def skip_result(self, context: AdapterContext, status: str, reason: str) -> AdapterResult:
        probe = self.probe(context)
        return AdapterResult(
            adapter_name=self.name,
            resource_level=self.resource_level,
            priority=self.priority,
            status=status,
            started_utc=utc_timestamp(),
            duration_ms=0,
            capabilities=list(self.capabilities),
            probe=probe,
            error=reason if status in {STATUS_FAIL, STATUS_TIMEOUT} else None,
            stop_reason=reason,
        )

    def run(self, context: AdapterContext) -> AdapterResult:
        probe = self.probe(context)
        if not probe.available:
            return self.skip_result(context, STATUS_SKIPPED_UNAVAILABLE, probe.reason or "unavailable")
        if self.heavy:
            allowed, reason = heavy_resource_gate(context.config)
            if not allowed:
                return self.skip_result(context, STATUS_SKIPPED_POLICY, reason)
        started = time.monotonic()
        try:
            result = self.extract(context)
        except subprocess.TimeoutExpired as exc:
            return AdapterResult(
                adapter_name=self.name,
                resource_level=self.resource_level,
                priority=self.priority,
                status=STATUS_TIMEOUT,
                started_utc=utc_timestamp(),
                duration_ms=int((time.monotonic() - started) * 1000),
                capabilities=list(self.capabilities),
                probe=probe,
                error=str(exc),
            )
        except Exception as exc:
            return AdapterResult(
                adapter_name=self.name,
                resource_level=self.resource_level,
                priority=self.priority,
                status=STATUS_FAIL,
                started_utc=utc_timestamp(),
                duration_ms=int((time.monotonic() - started) * 1000),
                capabilities=list(self.capabilities),
                probe=probe,
                error=f"{type(exc).__name__}: {exc}",
            )
        result.duration_ms = int((time.monotonic() - started) * 1000)
        result.probe = probe
        result.adapter_name = self.name
        result.resource_level = self.resource_level
        result.priority = self.priority
        result.capabilities = list(self.capabilities)
        result.document_text, truncated = truncate_output(
            result.document_text, context.config.max_output_characters
        )
        if truncated:
            result.warnings.append("document_text truncated by max_output_characters")
        result.accepted, result.stop_reason = evaluate_acceptance(result, context.config)
        return result


class ExternalCommandAdapter(BaseAdapter):
    module_name: Optional[str] = None
    binary_name: Optional[str] = None
    distribution_name: Optional[str] = None
    environment_command_key: Optional[str] = None

    def configured_command(self, context: AdapterContext) -> Optional[str]:
        if not self.environment_command_key:
            return None
        return context.config.environment.get(self.environment_command_key) or os.environ.get(
            self.environment_command_key
        )

    def probe(self, context: AdapterContext) -> AdapterProbe:
        configured_command = self.configured_command(context)
        module_available = module_exists(self.module_name)
        found_binary = binary_path(self.binary_name)
        available = bool(configured_command or module_available or found_binary)
        reason = "available" if available else (
            f"requires module={self.module_name!r}, binary={self.binary_name!r}, "
            f"or env={self.environment_command_key!r}"
        )
        return AdapterProbe(
            name=self.name,
            available=available,
            module_available=module_available,
            binary_available=bool(found_binary or configured_command),
            configured=bool(configured_command) if self.environment_command_key else True,
            version=package_version(self.distribution_name) if self.distribution_name else None,
            reason=reason,
        )
