#!/usr/bin/env python3
"""Resource-aware router, backend orchestrator, and consensus fusion engine."""

from __future__ import annotations

# =============================================================================
# 01. PARAMETERS
# =============================================================================

ORCHESTRATOR_NAME = "GenericLayoutExtractionOS"
ORCHESTRATOR_VERSION = "2.0.0"
ORCHESTRATOR_SCHEMA = "GLE-ORCHESTRATOR/2.0"

DEFAULT_MODE = "auto"  # auto | consensus | tables | paddle | ocr | all
DEFAULT_REQUIRED_CAPABILITIES = ["text", "bbox", "layout"]
DEFAULT_STOP_ON_ACCEPT = True
DEFAULT_RUN_CORE_LAYOUT = True
DEFAULT_FUSION_MIN_CONFIDENCE = 0.35
DEFAULT_MAX_ADAPTERS = 64

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
import json
import os
import sys
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional, Sequence

from adapter_sdk import (
    AdapterConfig,
    AdapterContext,
    AdapterElement,
    AdapterProbe,
    AdapterResult,
    BaseAdapter,
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
    adapter: AdapterConfig = field(default_factory=AdapterConfig)

    def validate(self) -> None:
        if self.mode not in {"auto", "consensus", "tables", "paddle", "ocr", "all"}:
            raise ValueError(f"unsupported mode: {self.mode}")
        if not 0.0 <= self.fusion_min_confidence <= 1.0:
            raise ValueError("fusion_min_confidence must be between 0 and 1")
        if self.max_adapters < 1:
            raise ValueError("max_adapters must be positive")


@dataclass
class CanonicalElement:
    canonical_id: str
    page: int
    text: str
    bbox: Optional[list[float]]
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
    stop_reason: str
    document_profile: dict[str, Any]
    adapter_results: list[AdapterResult]
    canonical_elements: list[CanonicalElement]
    outputs: dict[str, Any]


# =============================================================================
# 04. CONFIGURATION
# =============================================================================

def load_orchestrator_config(path: Optional[Path]) -> OrchestratorConfig:
    config = OrchestratorConfig()
    if path is None:
        return config
    payload = json.loads(path.read_text(encoding="utf-8"))
    adapter_payload = payload.pop("adapter", {})
    known = set(OrchestratorConfig.__dataclass_fields__) - {"adapter"}
    unknown = sorted(set(payload) - known)
    if unknown:
        raise ValueError(f"unknown orchestrator config keys: {', '.join(unknown)}")
    for key, value in payload.items():
        setattr(config, key, value)
    adapter_known = set(AdapterConfig.__dataclass_fields__)
    adapter_unknown = sorted(set(adapter_payload) - adapter_known)
    if adapter_unknown:
        raise ValueError(f"unknown adapter config keys: {', '.join(adapter_unknown)}")
    for key, value in adapter_payload.items():
        setattr(config.adapter, key, value)
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


def document_profile_from_results(results: Sequence[AdapterResult]) -> dict[str, Any]:
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
            and results[0].quality.character_count < 40
        ),
        "table_count_max": max((result.quality.table_count for result in passed), default=0),
        "page_count_max": max((result.quality.page_count for result in passed), default=0),
        "best_adapter": best.adapter_name if best else None,
        "best_quality_score": best.quality.quality_score if best else 0.0,
        "successful_adapters": [result.adapter_name for result in passed],
    }


def execute_route(
    input_path: Path,
    work_dir: Path,
    config: OrchestratorConfig,
) -> tuple[list[AdapterResult], list[str], str, dict[str, Any]]:
    route = build_route(config)
    context = AdapterContext(input_path=input_path, work_dir=work_dir, config=config.adapter)
    results: list[AdapterResult] = []
    executed_route: list[str] = []
    stop_reason = "route exhausted"
    ocr_names = set(MODE_ADAPTERS["ocr"])

    for adapter in route:
        if config.mode == "auto" and results and should_jump_to_ocr(results[0], config):
            if adapter.name not in ocr_names:
                skipped = adapter.skip_result(
                    context,
                    STATUS_SKIPPED_POLICY,
                    "probable scanned document: jumping from pdfplumber to OCR lane",
                )
                results.append(skipped)
                executed_route.append(adapter.name)
                continue
        result = adapter.run(context)
        results.append(result)
        executed_route.append(adapter.name)
        context.document_profile = document_profile_from_results(results)

        if config.mode == "all":
            continue
        if config.mode in {"consensus", "tables", "paddle", "ocr"}:
            continue
        if result.accepted and required_capabilities_met(result, config.required_capabilities):
            stop_reason = f"{adapter.name}: accepted and required capabilities met"
            if config.stop_on_accept:
                break
        elif result.accepted:
            stop_reason = f"{adapter.name}: quality passed but missing required capabilities"

    profile = document_profile_from_results(results)
    return results, executed_route, stop_reason, profile


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


def elements_match(first: AdapterElement, second: AdapterElement) -> bool:
    if first.page != second.page:
        return False
    first_signature = text_signature(first.text)
    second_signature = text_signature(second.text)
    if first_signature and first_signature == second_signature:
        return True
    if not first_signature and not second_signature:
        return (
            first.element_type == second.element_type
            and first.subtype == second.subtype
            and bbox_iou(first.bbox, second.bbox) >= 0.55
        )
    return bbox_iou(first.bbox, second.bbox) >= 0.78 and (
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
        "accepted", "stop_reason", "quality_score", "character_count", "element_count",
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
                    "accepted": result.accepted,
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
        "schema": "GLE-CONSENSUS/2.0",
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
    run_id = f"GLE-RUN-{time.strftime('%Y%m%d-%H%M%S', time.gmtime())}-{os.getpid()}"

    results, route, stop_reason, profile = execute_route(input_path, work_dir, config)
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
    run = run_orchestrator(args.input, args.output, config)
    payload = {
        "status": "PASS" if run.canonical_elements else "WARN",
        "run_id": run.run_id,
        "route": run.route,
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
