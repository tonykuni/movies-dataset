#!/usr/bin/env python3
"""Resource-aware router, backend orchestrator, and consensus fusion engine."""

from __future__ import annotations

# =============================================================================
# 01. PARAMETERS
# =============================================================================

ORCHESTRATOR_NAME = "GenericLayoutExtractionOS"
ORCHESTRATOR_VERSION = "2.1.0"
ORCHESTRATOR_SCHEMA = "GLE-ORCHESTRATOR/2.1"

DEFAULT_MODE = "auto"  # auto | consensus | tables | paddle | ocr | all
DEFAULT_REQUIRED_CAPABILITIES = ["text", "bbox", "layout"]
DEFAULT_STOP_ON_ACCEPT = True
DEFAULT_RUN_CORE_LAYOUT = True
DEFAULT_FUSION_MIN_CONFIDENCE = 0.35
DEFAULT_MAX_ADAPTERS = 64
DEFAULT_USE_CACHE = True
DEFAULT_CACHE_SUBDIRECTORY = ".gle_cache"

MODE_ADAPTERS = {
    "consensus": ["pdfplumber", "pymupdf", "pdfminer_six"],
    "tables": ["pdfplumber", "camelot", "tabula_py", "table_transformer", "paddle_ppstructure"],
    "paddle": ["pdfplumber", "pymupdf", "paddleocr", "paddle_ppstructure", "paddle_layout", "paddle_pdf_pipeline", "paddle_detection"],
    "ocr": ["tesseract", "paddleocr", "paddle_ppstructure", "paddle_pdf_pipeline", "easyocr", "ocrmypdf", "transkribus_core"],
}


# =============================================================================
# 02. IMPORTS
# =============================================================================

import argparse
import csv
import hashlib
import json
import os
import sys
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional, Sequence

from adapter_sdk import (
    ADAPTER_SCHEMA_VERSION,
    AdapterConfig,
    AdapterContext,
    AdapterElement,
    AdapterProbe,
    AdapterResult,
    BaseAdapter,
    QualityMetrics,
    STATUS_FAIL,
    STATUS_PASS,
    STATUS_SKIPPED_POLICY,
    STATUS_SKIPPED_UNAVAILABLE,
    STATUS_TIMEOUT,
    STATUS_WARN,
    normalize_text,
    text_signature,
    utc_timestamp,
)
from all_backend_engines import adapter_registry, build_all_adapters


# =============================================================================
# 03. ORCHESTRATOR DATA CONTRACTS
# =============================================================================

@dataclass
class OrchestratorConfig:
    mode: str = DEFAULT_MODE
    required_capabilities: list[str] = field(default_factory=lambda: list(DEFAULT_REQUIRED_CAPABILITIES))
    selected_adapters: list[str] = field(default_factory=list)
    disabled_adapters: list[str] = field(default_factory=list)
    stop_on_accept: bool = DEFAULT_STOP_ON_ACCEPT
    run_core_layout: bool = DEFAULT_RUN_CORE_LAYOUT
    fusion_min_confidence: float = DEFAULT_FUSION_MIN_CONFIDENCE
    max_adapters: int = DEFAULT_MAX_ADAPTERS
    use_cache: bool = DEFAULT_USE_CACHE
    cache_subdirectory: str = DEFAULT_CACHE_SUBDIRECTORY
    stack_metadata: dict[str, Any] = field(default_factory=dict)
    adapter: AdapterConfig = field(default_factory=AdapterConfig)

    def validate(self) -> None:
        if self.mode not in {"auto", "consensus", "tables", "paddle", "ocr", "all"}:
            raise ValueError(f"unsupported mode: {self.mode}")
        if not 0.0 <= self.fusion_min_confidence <= 1.0:
            raise ValueError("fusion_min_confidence must be between 0 and 1")
        if self.max_adapters < 1:
            raise ValueError("max_adapters must be positive")
        cache_path = Path(self.cache_subdirectory)
        if cache_path.is_absolute() or ".." in cache_path.parts:
            raise ValueError("cache_subdirectory must be a safe relative path")
        if self.adapter.timeout_seconds < 1 or self.adapter.heavy_timeout_seconds < 1:
            raise ValueError("adapter timeouts must be positive")
        if self.adapter.min_text_characters < 0 or self.adapter.min_structural_elements < 1:
            raise ValueError("adapter minimum counts are invalid")
        for name in (
            "min_readable_ratio", "max_replacement_ratio", "max_duplicate_ratio",
            "min_bbox_element_ratio",
        ):
            value = float(getattr(self.adapter, name))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"adapter.{name} must be between 0 and 1")
        if self.adapter.dpi < 72 or self.adapter.max_output_characters < 1:
            raise ValueError("adapter dpi/output limit is invalid")


@dataclass
class CanonicalElement:
    canonical_id: str
    page: int
    text: str
    bbox: Optional[list[float]]
    bbox_normalized: Optional[list[float]]
    element_type: str
    subtype: str
    confidence: float
    source_adapters: list[str]
    source_fingerprints: list[str]
    reading_order: Optional[int]
    row: Optional[int]
    column: Optional[int]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class OrchestratorRun:
    run_id: str
    input_file: str
    mode: str
    started_utc: str
    finished_utc: str
    duration_ms: int
    route: list[str]
    route_decisions: list[dict[str, Any]]
    stop_reason: str
    document_profile: dict[str, Any]
    adapter_results: list[AdapterResult]
    canonical_elements: list[CanonicalElement]
    outputs: dict[str, Any]


# =============================================================================
# 04. CONFIGURATION
# =============================================================================

def load_config_payload(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.casefold() in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore
        except ImportError as exc:
            raise RuntimeError("YAML policy requires PyYAML") from exc
        payload = yaml.safe_load(text)
    else:
        payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("configuration root must be an object")
    return payload


def apply_adapter_config(config: OrchestratorConfig, payload: dict[str, Any]) -> None:
    adapter_known = set(AdapterConfig.__dataclass_fields__)
    adapter_unknown = sorted(set(payload) - adapter_known)
    if adapter_unknown:
        raise ValueError(f"unknown adapter config keys: {', '.join(adapter_unknown)}")
    for key, value in payload.items():
        setattr(config.adapter, key, value)


def load_engine_stack_config(payload: dict[str, Any]) -> OrchestratorConfig:
    """Load the fixed-field YAML shape used by the attachment's engine stack."""
    stack = payload.get("pdf_extraction_engine")
    if not isinstance(stack, dict):
        raise ValueError("pdf_extraction_engine must be an object")
    allowed_stack_keys = {
        "version", "strategy", "mode", "required_capabilities", "stop_on_accept",
        "run_core_layout", "use_cache", "cache_subdirectory", "engines", "adapter",
    }
    unknown_stack_keys = sorted(set(stack) - allowed_stack_keys)
    if unknown_stack_keys:
        raise ValueError(f"unknown engine stack keys: {', '.join(unknown_stack_keys)}")
    config = OrchestratorConfig()
    config.mode = str(stack.get("mode", "auto"))
    if "required_capabilities" in stack:
        config.required_capabilities = list(stack["required_capabilities"])
    config.stop_on_accept = bool(stack.get("stop_on_accept", True))
    config.run_core_layout = bool(stack.get("run_core_layout", True))
    config.use_cache = bool(stack.get("use_cache", True))
    config.cache_subdirectory = str(stack.get("cache_subdirectory", DEFAULT_CACHE_SUBDIRECTORY))
    config.stack_metadata = {
        "version": stack.get("version"),
        "strategy": stack.get("strategy", "light_to_heavy_fallback"),
    }
    engines = stack.get("engines", [])
    if not isinstance(engines, list) or not engines:
        raise ValueError("pdf_extraction_engine.engines must be a non-empty list")
    normalized: list[tuple[int, str, bool]] = []
    seen_names: set[str] = set()
    seen_priorities: set[int] = set()
    allowed_engine_keys = {
        "name", "enabled", "priority", "strength", "type", "role", "handles", "fallback_if",
    }
    for position, item in enumerate(engines, start=1):
        if not isinstance(item, dict) or not item.get("name"):
            raise ValueError(f"engine entry {position} requires name")
        unknown_engine_keys = sorted(set(item) - allowed_engine_keys)
        if unknown_engine_keys:
            raise ValueError(
                f"unknown keys in engine entry {position}: {', '.join(unknown_engine_keys)}"
            )
        name = str(item["name"])
        priority = int(item.get("priority", position))
        if name in seen_names:
            raise ValueError(f"duplicate engine name: {name}")
        if priority in seen_priorities:
            raise ValueError(f"duplicate engine priority: {priority}")
        seen_names.add(name)
        seen_priorities.add(priority)
        normalized.append((priority, name, bool(item.get("enabled", True))))
    normalized.sort(key=lambda item: (item[0], item[1]))
    config.selected_adapters = [name for _, name, enabled in normalized if enabled]
    config.disabled_adapters = [name for _, name, enabled in normalized if not enabled]
    apply_adapter_config(config, dict(stack.get("adapter", {})))
    config.validate()
    return config


def load_orchestrator_config(path: Optional[Path]) -> OrchestratorConfig:
    config = OrchestratorConfig()
    if path is None:
        return config
    payload = load_config_payload(path)
    if "pdf_extraction_engine" in payload:
        return load_engine_stack_config(payload)
    payload = dict(payload)
    adapter_payload = payload.pop("adapter", {})
    known = set(OrchestratorConfig.__dataclass_fields__) - {"adapter"}
    unknown = sorted(set(payload) - known)
    if unknown:
        raise ValueError(f"unknown orchestrator config keys: {', '.join(unknown)}")
    for key, value in payload.items():
        setattr(config, key, value)
    apply_adapter_config(config, adapter_payload)
    config.validate()
    return config


# =============================================================================
# 05. ROUTING POLICY
# =============================================================================

def required_capabilities_met(result: AdapterResult, required: Sequence[str]) -> bool:
    capabilities = set(result.capabilities)
    return all(capability in capabilities for capability in required)


def build_route(config: OrchestratorConfig) -> list[BaseAdapter]:
    registry = adapter_registry()
    if config.selected_adapters:
        unknown = sorted(set(config.selected_adapters) - set(registry))
        if unknown:
            raise ValueError(f"unknown adapters: {', '.join(unknown)}")
        route = [registry[name] for name in config.selected_adapters]
    elif config.mode in MODE_ADAPTERS:
        route = [registry[name] for name in MODE_ADAPTERS[config.mode]]
    else:
        route = build_all_adapters()
    route = [adapter for adapter in route if adapter.name not in config.disabled_adapters]
    if config.mode != "all":
        route = [adapter for adapter in route if adapter.resource_level <= 5]
    return route[: config.max_adapters]


def should_jump_to_ocr(result: AdapterResult, config: OrchestratorConfig) -> bool:
    if result.adapter_name != "pdfplumber":
        return False
    return result.quality.character_count < config.adapter.min_text_characters


def document_profile_from_results(
    results: Sequence[AdapterResult],
    min_text_characters: int = 40,
) -> dict[str, Any]:
    passed = [result for result in results if result.status in {STATUS_PASS, STATUS_WARN}]
    best = max(passed, key=lambda result: result.quality.quality_score, default=None)
    return {
        "native_text_present": any(
            result.adapter_name in {"pdfplumber", "pypdf", "poppler_pdftotext", "pymupdf", "pdfminer_six"}
            and result.quality.character_count > 0
            for result in passed
        ),
        "probable_scanned": bool(
            results
            and results[0].adapter_name == "pdfplumber"
            and results[0].quality.character_count < min_text_characters
        ),
        "table_count_max": max((result.quality.table_count for result in passed), default=0),
        "page_count_max": max((result.quality.page_count for result in passed), default=0),
        "best_adapter": best.adapter_name if best else None,
        "best_quality_score": best.quality.quality_score if best else 0.0,
        "successful_adapters": [result.adapter_name for result in passed],
    }


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def adapter_cache_key(
    adapter: BaseAdapter,
    context: AdapterContext,
    input_digest: str,
    probe: AdapterProbe,
) -> str:
    seed = {
        "adapter_schema": ADAPTER_SCHEMA_VERSION,
        "adapter": adapter.name,
        "adapter_version": probe.version,
        "available": probe.available,
        "configured": probe.configured,
        "input_sha256": input_digest,
        "config": asdict(context.config),
    }
    encoded = json.dumps(seed, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def result_from_cache(payload: dict[str, Any], cache_key: str) -> AdapterResult:
    payload = dict(payload)
    payload["probe"] = AdapterProbe(**payload["probe"])
    payload["quality"] = QualityMetrics(**payload.get("quality", {}))
    payload["elements"] = [AdapterElement(**item) for item in payload.get("elements", [])]
    payload["cache_source_duration_ms"] = int(payload.get("duration_ms", 0))
    payload["duration_ms"] = 0
    payload["cache_hit"] = True
    payload["cache_key"] = cache_key
    return AdapterResult(**payload)


def run_adapter_cached(
    adapter: BaseAdapter,
    context: AdapterContext,
    input_digest: str,
    cache_dir: Path,
    use_cache: bool,
) -> AdapterResult:
    probe = adapter.probe(context)
    cache_key = adapter_cache_key(adapter, context, input_digest, probe)
    cache_path = cache_dir / f"{adapter.name}-{cache_key[:24]}.json"
    if use_cache and probe.available and cache_path.exists():
        try:
            payload = json.loads(cache_path.read_text(encoding="utf-8"))
            if payload.get("cache_key") == cache_key and payload.get("result", {}).get("status") in {STATUS_PASS, STATUS_WARN}:
                return result_from_cache(payload["result"], cache_key)
        except (OSError, ValueError, TypeError, KeyError):
            pass

    result = adapter.run(context, probe=probe)
    result.cache_key = cache_key
    if use_cache and result.status in {STATUS_PASS, STATUS_WARN}:
        cache_dir.mkdir(parents=True, exist_ok=True)
        serialized = result.to_dict(include_elements=True)
        serialized["cache_hit"] = False
        serialized["cache_source_duration_ms"] = None
        cache_path.write_text(
            json.dumps(
                {"schema": "GLE-CACHE/2.1", "cache_key": cache_key, "result": serialized},
                ensure_ascii=False,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
    return result


def execute_route(
    input_path: Path,
    work_dir: Path,
    config: OrchestratorConfig,
) -> tuple[list[AdapterResult], list[str], list[dict[str, Any]], str, dict[str, Any]]:
    route = build_route(config)
    context = AdapterContext(input_path=input_path, work_dir=work_dir, config=config.adapter)
    results: list[AdapterResult] = []
    executed_route: list[str] = []
    route_decisions: list[dict[str, Any]] = []
    stop_reason = "route exhausted"
    ocr_names = set(MODE_ADAPTERS["ocr"])
    input_digest = file_sha256(input_path)
    cache_dir = work_dir / config.cache_subdirectory

    index = 0
    while index < len(route):
        adapter = route[index]
        result = run_adapter_cached(
            adapter, context, input_digest, cache_dir, config.use_cache
        )
        results.append(result)
        executed_route.append(adapter.name)
        context.document_profile = document_profile_from_results(
            results, config.adapter.min_text_characters
        )

        if config.mode == "auto" and len(results) == 1 and should_jump_to_ocr(result, config):
            skipped_names = [
                candidate.name for candidate in route[index + 1:]
                if candidate.name not in ocr_names
            ]
            route = route[: index + 1] + [
                candidate for candidate in route[index + 1:]
                if candidate.name in ocr_names
            ]
            route_decisions.append(
                {
                    "decision": "jump_to_ocr",
                    "reason": "pdfplumber text below minimum threshold",
                    "character_count": result.quality.character_count,
                    "threshold": config.adapter.min_text_characters,
                    "skipped_adapters": skipped_names,
                }
            )

        if config.mode == "all":
            index += 1
            continue
        if config.mode not in {"consensus", "tables", "paddle", "ocr"}:
            if result.accepted and required_capabilities_met(result, config.required_capabilities):
                stop_reason = f"{adapter.name}: accepted and required capabilities met"
                if config.stop_on_accept:
                    break
            elif result.accepted:
                stop_reason = f"{adapter.name}: quality passed but missing required capabilities"
        index += 1

    profile = document_profile_from_results(results, config.adapter.min_text_characters)
    return results, executed_route, route_decisions, stop_reason, profile


# =============================================================================
# 06. CONSENSUS FUSION
# =============================================================================

def bbox_iou(first: Optional[Sequence[float]], second: Optional[Sequence[float]]) -> float:
    if not first or not second or len(first) < 4 or len(second) < 4:
        return 0.0
    x0 = max(float(first[0]), float(second[0]))
    y0 = max(float(first[1]), float(second[1]))
    x1 = min(float(first[2]), float(second[2]))
    y1 = min(float(first[3]), float(second[3]))
    intersection = max(0.0, x1 - x0) * max(0.0, y1 - y0)
    area_first = max(0.0, float(first[2]) - float(first[0])) * max(0.0, float(first[3]) - float(first[1]))
    area_second = max(0.0, float(second[2]) - float(second[0])) * max(0.0, float(second[3]) - float(second[1]))
    return intersection / max(area_first + area_second - intersection, 1e-9)


def normalized_element_bbox(element: AdapterElement) -> Optional[list[float]]:
    if not element.bbox or len(element.bbox) < 4:
        return None
    width = element.metadata.get("page_width")
    height = element.metadata.get("page_height")
    try:
        width_value = float(width)
        height_value = float(height)
    except (TypeError, ValueError):
        return None
    if width_value <= 0 or height_value <= 0:
        return None
    x0, y0, x1, y1 = map(float, element.bbox[:4])
    return [
        max(0.0, min(1.0, x0 / width_value)),
        max(0.0, min(1.0, y0 / height_value)),
        max(0.0, min(1.0, x1 / width_value)),
        max(0.0, min(1.0, y1 / height_value)),
    ]


def elements_match(first: AdapterElement, second: AdapterElement) -> bool:
    if first.page != second.page:
        return False
    first_signature = text_signature(first.text)
    second_signature = text_signature(second.text)
    if first_signature and first_signature == second_signature:
        return True
    first_bbox = normalized_element_bbox(first)
    second_bbox = normalized_element_bbox(second)
    comparable_first = first_bbox if first_bbox is not None and second_bbox is not None else first.bbox
    comparable_second = second_bbox if first_bbox is not None and second_bbox is not None else second.bbox
    if not first_signature and not second_signature:
        return (
            first.element_type == second.element_type
            and first.subtype == second.subtype
            and bbox_iou(comparable_first, comparable_second) >= 0.55
        )
    return bbox_iou(comparable_first, comparable_second) >= 0.78 and (
        first_signature in second_signature or second_signature in first_signature
    )


def choose_consensus_type(items: Sequence[tuple[str, AdapterElement]]) -> tuple[str, str]:
    votes: Counter[tuple[str, str]] = Counter()
    for _, element in items:
        votes[(element.element_type, element.subtype)] += max(1, int(round(element.confidence * 10)))
    return votes.most_common(1)[0][0] if votes else ("TEXT", "BODY")


def fuse_results(results: Sequence[AdapterResult], min_confidence: float) -> list[CanonicalElement]:
    source_elements: list[tuple[str, AdapterElement]] = []
    for result in results:
        if result.status not in {STATUS_PASS, STATUS_WARN}:
            continue
        for element in result.elements:
            if element.confidence >= min_confidence:
                source_elements.append((result.adapter_name, element))

    clusters: list[list[tuple[str, AdapterElement]]] = []
    for item in source_elements:
        for cluster in clusters:
            if any(elements_match(item[1], existing[1]) for existing in cluster):
                cluster.append(item)
                break
        else:
            clusters.append([item])

    page_counters: defaultdict[int, int] = defaultdict(int)
    canonical: list[CanonicalElement] = []
    for cluster in sorted(
        clusters,
        key=lambda items: (
            items[0][1].page,
            min((element.reading_order or 10**9) for _, element in items),
            min((element.bbox[1] if element.bbox else 10**9) for _, element in items),
        ),
    ):
        page = cluster[0][1].page
        page_counters[page] += 1
        best_adapter, best = max(
            cluster,
            key=lambda item: (
                item[1].confidence,
                bool(item[1].bbox),
                len(normalize_text(item[1].text)),
            ),
        )
        element_type, subtype = choose_consensus_type(cluster)
        adapters = sorted({adapter_name for adapter_name, _ in cluster})
        fingerprints = sorted({element.fingerprint(adapter_name) for adapter_name, element in cluster})
        confidence = min(
            1.0,
            max(element.confidence for _, element in cluster) + min(0.12, (len(adapters) - 1) * 0.04),
        )
        canonical.append(
            CanonicalElement(
                canonical_id=f"CAN-P{page:04d}-E{page_counters[page]:05d}",
                page=page,
                text=normalize_text(best.text),
                bbox=best.bbox,
                bbox_normalized=normalized_element_bbox(best),
                element_type=element_type,
                subtype=subtype,
                confidence=confidence,
                source_adapters=adapters,
                source_fingerprints=fingerprints,
                reading_order=best.reading_order,
                row=best.row,
                column=best.column,
                metadata={
                    "best_source": best_adapter,
                    "source_count": len(cluster),
                    "source_types": sorted({f"{element.element_type}.{element.subtype}" for _, element in cluster}),
                },
            )
        )
    return canonical


# =============================================================================
# 07. EXPORTERS AND CORE LAYOUT BRIDGE
# =============================================================================

def export_backend_audit(results: Sequence[AdapterResult], output_dir: Path) -> Path:
    path = output_dir / "backend_audit.csv"
    fields = [
        "adapter_name", "resource_level", "priority", "status", "available", "duration_ms",
        "cache_hit", "cache_source_duration_ms", "accepted", "acceptance_basis", "stop_reason",
        "quality_score", "character_count", "element_count",
        "bbox_element_ratio", "table_count", "error",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    "adapter_name": result.adapter_name,
                    "resource_level": result.resource_level,
                    "priority": result.priority,
                    "status": result.status,
                    "available": result.probe.available,
                    "duration_ms": result.duration_ms,
                    "cache_hit": result.cache_hit,
                    "cache_source_duration_ms": result.cache_source_duration_ms,
                    "accepted": result.accepted,
                    "acceptance_basis": result.acceptance_basis,
                    "stop_reason": result.stop_reason,
                    "quality_score": round(result.quality.quality_score, 6),
                    "character_count": result.quality.character_count,
                    "element_count": result.quality.element_count,
                    "bbox_element_ratio": round(result.quality.bbox_element_ratio, 6),
                    "table_count": result.quality.table_count,
                    "error": result.error,
                }
            )
    return path


def export_consensus(elements: Sequence[CanonicalElement], output_dir: Path) -> tuple[Path, Path]:
    json_path = output_dir / "consensus_layout.json"
    jsonl_path = output_dir / "consensus_elements.jsonl"
    payload = {
        "schema": "GLE-CONSENSUS/2.1",
        "element_count": len(elements),
        "elements": [asdict(element) for element in elements],
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    with jsonl_path.open("w", encoding="utf-8", newline="\n") as handle:
        for element in elements:
            handle.write(json.dumps(asdict(element), ensure_ascii=False, sort_keys=True) + "\n")
    return json_path, jsonl_path


def run_core_layout_bridge(input_path: Path, output_dir: Path, config: OrchestratorConfig) -> dict[str, Any]:
    if not config.run_core_layout:
        return {"status": "SKIPPED_POLICY"}
    try:
        from generic_layout_engine import EngineConfig, analyze_document

        core_config = EngineConfig(
            dpi=config.adapter.dpi,
            ocr_mode="auto",
            ocr_languages=config.adapter.ocr_languages,
        )
        document, outputs = analyze_document(input_path, output_dir / "core_layout", core_config)
        return {"status": "PASS", "statistics": document.statistics, "outputs": outputs}
    except Exception as exc:
        return {"status": "FAIL", "error": f"{type(exc).__name__}: {exc}"}


def export_run(run: OrchestratorRun, output_dir: Path) -> Path:
    path = output_dir / "multi_engine_run.json"
    payload = {
        "schema": ORCHESTRATOR_SCHEMA,
        "orchestrator": ORCHESTRATOR_NAME,
        "version": ORCHESTRATOR_VERSION,
        "run_id": run.run_id,
        "input_file": run.input_file,
        "mode": run.mode,
        "started_utc": run.started_utc,
        "finished_utc": run.finished_utc,
        "duration_ms": run.duration_ms,
        "route": run.route,
        "route_decisions": run.route_decisions,
        "stop_reason": run.stop_reason,
        "document_profile": run.document_profile,
        "adapter_results": [result.to_dict(include_elements=False) for result in run.adapter_results],
        "canonical_element_count": len(run.canonical_elements),
        "outputs": run.outputs,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def run_orchestrator(
    input_path: Path,
    output_dir: Path,
    config: OrchestratorConfig,
) -> OrchestratorRun:
    config.validate()
    input_path = input_path.resolve()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    work_dir = output_dir / "backend_work"
    work_dir.mkdir(parents=True, exist_ok=True)
    started_utc = utc_timestamp()
    started = time.monotonic()
    run_id = f"GLE-RUN-{time.strftime('%Y%m%d-%H%M%S', time.gmtime())}-{os.getpid()}-{time.time_ns() % 1_000_000_000:09d}"

    results, route, route_decisions, stop_reason, profile = execute_route(
        input_path, work_dir, config
    )
    canonical = fuse_results(results, config.fusion_min_confidence)
    consensus_json, consensus_jsonl = export_consensus(canonical, output_dir)
    audit_csv = export_backend_audit(results, output_dir)
    core_output = run_core_layout_bridge(input_path, output_dir, config)
    outputs = {
        "consensus_json": consensus_json.name,
        "consensus_jsonl": consensus_jsonl.name,
        "backend_audit_csv": audit_csv.name,
        "core_layout": core_output,
    }
    run = OrchestratorRun(
        run_id=run_id,
        input_file=str(input_path),
        mode=config.mode,
        started_utc=started_utc,
        finished_utc=utc_timestamp(),
        duration_ms=int((time.monotonic() - started) * 1000),
        route=route,
        route_decisions=route_decisions,
        stop_reason=stop_reason,
        document_profile=profile,
        adapter_results=results,
        canonical_elements=canonical,
        outputs=outputs,
    )
    run_path = export_run(run, output_dir)
    run.outputs["run_json"] = run_path.name
    export_run(run, output_dir)
    return run


# =============================================================================
# 08. CLI
# =============================================================================

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Resource-aware multi-engine PDF/image extraction OS")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="run automatic or selected backend route")
    run_parser.add_argument("input", type=Path)
    run_parser.add_argument("--output", required=True, type=Path)
    run_parser.add_argument("--config", type=Path)
    run_parser.add_argument("--mode", choices=["auto", "consensus", "tables", "paddle", "ocr", "all"])
    run_parser.add_argument("--adapter", action="append", dest="adapters")
    run_parser.add_argument("--no-core-layout", action="store_true")
    run_parser.add_argument("--no-cache", action="store_true")

    subparsers.add_parser("probe", help="probe every registered backend")
    subparsers.add_parser("list", help="list routing order and capabilities")
    return parser


def command_probe() -> int:
    context = AdapterContext(input_path=Path("probe.pdf"), work_dir=Path.cwd(), config=AdapterConfig())
    payload = []
    for adapter in build_all_adapters():
        try:
            probe = adapter.probe(context)
        except Exception as exc:
            probe = AdapterProbe(name=adapter.name, available=False, reason=f"probe failed: {type(exc).__name__}: {exc}")
        payload.append(
            {
                "name": adapter.name,
                "resource_level": adapter.resource_level,
                "priority": adapter.priority,
                "capabilities": list(adapter.capabilities),
                "probe": asdict(probe),
            }
        )
    print(json.dumps({"schema": ORCHESTRATOR_SCHEMA, "adapters": payload}, ensure_ascii=False, indent=2))
    return 0


def command_list() -> int:
    payload = [
        {
            "name": adapter.name,
            "resource_level": adapter.resource_level,
            "priority": adapter.priority,
            "heavy": adapter.heavy,
            "capabilities": list(adapter.capabilities),
        }
        for adapter in build_all_adapters()
    ]
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def command_run(args: argparse.Namespace) -> int:
    config = load_orchestrator_config(args.config)
    if args.mode:
        config.mode = args.mode
    if args.adapters:
        config.selected_adapters = args.adapters
    if args.no_core_layout:
        config.run_core_layout = False
    if args.no_cache:
        config.use_cache = False
    run = run_orchestrator(args.input, args.output, config)
    payload = {
        "status": "PASS" if run.canonical_elements else "WARN",
        "run_id": run.run_id,
        "route": run.route,
        "route_decisions": run.route_decisions,
        "stop_reason": run.stop_reason,
        "profile": run.document_profile,
        "canonical_element_count": len(run.canonical_elements),
        "outputs": run.outputs,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if run.canonical_elements else 1


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "probe":
            return command_probe()
        if args.command == "list":
            return command_list()
        if args.command == "run":
            return command_run(args)
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error": type(exc).__name__, "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
