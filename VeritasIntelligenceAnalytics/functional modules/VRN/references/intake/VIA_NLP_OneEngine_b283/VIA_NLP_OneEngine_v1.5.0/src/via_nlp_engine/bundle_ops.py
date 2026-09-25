"""Deterministic multi-document intake and reconstruction package export."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Iterable

from .ingest import DEFAULT_MAX_FILE_BYTES, MARKITDOWN_EXTENSIONS, SUPPORTED_EXTENSIONS, read_local_document


DEFAULT_MAX_BUNDLE_FILES = 1000
DEFAULT_MAX_BUNDLE_BYTES = 512 * 1024 * 1024
FIXED_ZIP_TIMESTAMP = (2026, 9, 1, 0, 0, 0)
PACKAGE_FILENAMES = {
    "full": "VIA_Knowledge_Full.json",
    "summary": "VIA_Reconstruction_Summary.json",
    "mind_map": "VIA_MindMap.json",
    "mind_map_evolution": "VIA_MindMap_Evolution.json",
    "knowledge_registry": "VIA_Knowledge_Registry.json",
    "bilingual_knowledge_body": "VIA_Bilingual_Knowledge_Body.json",
    "instruction_reconstruction": "VIA_Instruction_Reconstruction.json",
    "code_reconstruction": "VIA_Code_Reconstruction.json",
    "function_classification": "VIA_Function_Classification.json",
    "code_restoration": "VIA_Code_Restoration.json",
    "context_reconstruction": "VIA_Context_Reconstruction.json",
    "template_reconstruction": "VIA_Template_Reconstruction.json",
    "layout_analysis": "VIA_Markdown_Layout_Analysis.json",
    "local_provider_registry": "VIA_Local_Provider_Registry.json",
    "source_records": "VIA_Source_Record_Ledger.json",
    "handoff": "VIA_Handoff.md",
    "archive": "VIA_Discussion_Reconstruction_Package.zip",
}


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _iter_input_files(
    inputs: Iterable[str | Path],
    recursive: bool,
    use_markitdown: bool = False,
) -> list[Path]:
    discovered: dict[str, Path] = {}
    for raw in inputs:
        selected = Path(raw).expanduser().resolve(strict=True)
        if selected.is_file():
            candidates = [selected]
        elif selected.is_dir():
            candidates = selected.rglob("*") if recursive else selected.iterdir()
        else:
            continue
        for candidate in candidates:
            if candidate.is_symlink() or not candidate.is_file():
                continue
            allowed = MARKITDOWN_EXTENSIONS if use_markitdown else SUPPORTED_EXTENSIONS
            if candidate.suffix.lower() not in allowed:
                continue
            resolved = candidate.resolve(strict=True)
            discovered[str(resolved).casefold()] = resolved
    return sorted(discovered.values(), key=lambda item: item.as_posix().casefold())


def read_document_bundle(
    inputs: Iterable[str | Path],
    recursive: bool = True,
    max_files: int = DEFAULT_MAX_BUNDLE_FILES,
    max_total_bytes: int = DEFAULT_MAX_BUNDLE_BYTES,
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
    use_markitdown: bool = False,
) -> dict[str, Any]:
    files = _iter_input_files(inputs, recursive=recursive, use_markitdown=use_markitdown)
    if not files:
        raise ValueError("No supported input files were found")
    if len(files) > max_files:
        raise ValueError(f"Bundle contains {len(files)} files; maximum is {max_files}")
    total_bytes = sum(item.stat().st_size for item in files)
    if total_bytes > max_total_bytes:
        raise ValueError(f"Bundle contains {total_bytes} bytes; maximum is {max_total_bytes}")

    combined_parts: list[str] = []
    records: list[dict[str, Any]] = []
    position = 0
    used_record_ids: dict[str, int] = {}
    for index, path in enumerate(files, start=1):
        payload = read_local_document(path, max_bytes=max_file_bytes, use_markitdown=use_markitdown)
        text = str(payload["text"])
        raw = path.read_bytes()
        source_file_sha256 = _sha256_bytes(raw)
        record_key = _sha256_text(f"{path.name.casefold()}\0{source_file_sha256}")
        base_record_id = f"RECORD-{record_key[:16].upper()}"
        duplicate_number = used_record_ids.get(base_record_id, 0) + 1
        used_record_ids[base_record_id] = duplicate_number
        record_id = base_record_id if duplicate_number == 1 else f"{base_record_id}-DUP{duplicate_number:03d}"
        header = (
            f"===== BEGIN VIA SOURCE RECORD {record_id} =====\n"
            f"SourceName: {path.name}\n"
            f"SourceExtension: {path.suffix.lower()}\n"
            f"ExtractedTextSHA256: {_sha256_text(text)}\n"
            "===== BEGIN EXTRACTED CONTENT =====\n"
        )
        footer = f"\n===== END EXTRACTED CONTENT =====\n===== END VIA SOURCE RECORD {record_id} =====\n"
        combined_parts.append(header)
        position += len(header)
        content_start = position
        combined_parts.append(text)
        position += len(text)
        content_end = position
        combined_parts.append(footer)
        position += len(footer)
        records.append(
            {
                "record_id": record_id,
                "record_key": record_key,
                "source_order": index,
                "source_name": path.name,
                "extension": path.suffix.lower(),
                "source_size_bytes": len(raw),
                "source_file_sha256": source_file_sha256,
                "extracted_text_chars": len(text),
                "extracted_text_sha256": _sha256_text(text),
                "combined_content_span": {"start": content_start, "end": content_end},
                "ingest_metadata": {
                    key: value
                    for key, value in payload["metadata"].items()
                    if key != "path"
                },
            }
        )

    combined = "".join(combined_parts)
    exact = all(
        _sha256_text(combined[item["combined_content_span"]["start"] : item["combined_content_span"]["end"]])
        == item["extracted_text_sha256"]
        for item in records
    )
    return {
        "schema": "VIA_SOURCE_RECORD_BUNDLE/1.0",
        "text": combined,
        "source_record_ledger": records,
        "completeness": {
            "file_count": len(records),
            "source_total_bytes": total_bytes,
            "combined_text_chars": len(combined),
            "combined_text_sha256": _sha256_text(combined),
            "all_extracted_records_exactly_reconstructable": exact,
            "input_order": "deterministic_path_sort",
            "record_identity": "source_name_plus_source_sha256_stable_key",
            "unsupported_files": "ignored",
            "symlinks": "ignored",
        },
    }


def export_reconstruction_package(
    output_directory: str | Path,
    bundle: dict[str, Any],
    process_result: dict[str, Any],
) -> dict[str, Any]:
    output_dir = Path(output_directory).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    knowledge = process_result["output"]
    summary = {
        "schema": "VIA_DISCUSSION_RECONSTRUCTION_SUMMARY/1.0",
        "engine_version": process_result["engine_version"],
        "source_records": bundle["completeness"],
        "knowledge": {
            "segments": knowledge["completeness"]["segment_count"],
            "topics": len(knowledge["body_of_knowledge"]["topics"]),
            "topic_returns": knowledge["dialogue_flow"]["metrics"]["topic_returns"],
            "knowledge_units": knowledge["quality_gates"]["knowledge_units"],
            "knowledge_conflicts": knowledge["quality_gates"]["knowledge_conflicts"],
            "structured_tables": knowledge["quality_gates"]["structured_tables"],
            "instructions": knowledge["quality_gates"]["instructions"],
            "commands": knowledge["quality_gates"]["commands"],
        },
        "code": {
            "blocks": len(knowledge["code_registry"]),
            "families": knowledge["quality_gates"]["code_families"],
            "languages": knowledge["code_integration_blueprint"]["languages"],
            "build_readiness": knowledge["code_reconstruction_package"]["build_readiness"],
            "classified_functions": knowledge["function_classification"]["statistics"]["functions"],
            "module_templates": knowledge["code_restoration"]["statistics"]["module_templates"],
        },
        "context": {
            "document_mode": knowledge["context_reconstruction"]["document_mode"]["value"],
            "threads": knowledge["context_reconstruction"]["statistics"]["topic_threads"],
            "reply_links": knowledge["context_reconstruction"]["statistics"]["reply_links"],
            "unanswered_questions": knowledge["context_reconstruction"]["statistics"]["unanswered_questions"],
        },
        "template": {
            "schema": knowledge["template_reconstruction"]["selected_template"]["template_schema"],
            "missing_required_slots": knowledge["template_reconstruction"]["missing_required_slots"],
        },
        "layout": {
            "schema": knowledge["layout_analysis"]["schema"],
            "blocks": knowledge["layout_analysis"]["statistics"]["blocks"],
            "exact_reconstruction": knowledge["layout_analysis"]["completeness"]["exact_reconstruction"],
        },
        "quality_gates": knowledge["quality_gates"],
        "activation": "review_required_no_code_executed",
    }
    full_payload = {
        "schema": "VIA_DISCUSSION_RECONSTRUCTION_PACKAGE/1.0",
        "bundle_manifest": {
            "schema": bundle["schema"],
            "source_record_ledger": bundle["source_record_ledger"],
            "completeness": bundle["completeness"],
        },
        "process_result": {
            "task": process_result["task"],
            "language": process_result["language"],
            "output": process_result["output"],
            "route": process_result["route"],
            "warnings": process_result["warnings"],
            "engine_version": process_result["engine_version"],
        },
    }
    payloads = {
        PACKAGE_FILENAMES["full"]: full_payload,
        PACKAGE_FILENAMES["summary"]: summary,
        PACKAGE_FILENAMES["mind_map"]: knowledge["mind_map"],
        PACKAGE_FILENAMES["mind_map_evolution"]: knowledge["mind_map_evolution"],
        PACKAGE_FILENAMES["knowledge_registry"]: knowledge["knowledge_object_registry"],
        PACKAGE_FILENAMES["bilingual_knowledge_body"]: knowledge["bilingual_knowledge_body"],
        PACKAGE_FILENAMES["instruction_reconstruction"]: knowledge["instruction_reconstruction"],
        PACKAGE_FILENAMES["code_reconstruction"]: {
            "code_reconstruction_package": knowledge["code_reconstruction_package"],
            "code_integration_blueprint": knowledge["code_integration_blueprint"],
        },
        PACKAGE_FILENAMES["function_classification"]: knowledge["function_classification"],
        PACKAGE_FILENAMES["code_restoration"]: knowledge["code_restoration"],
        PACKAGE_FILENAMES["context_reconstruction"]: knowledge["context_reconstruction"],
        PACKAGE_FILENAMES["template_reconstruction"]: knowledge["template_reconstruction"],
        PACKAGE_FILENAMES["layout_analysis"]: knowledge["layout_analysis"],
        PACKAGE_FILENAMES["local_provider_registry"]: knowledge["local_provider_registry"],
        PACKAGE_FILENAMES["source_records"]: {
            "schema": bundle["schema"],
            "source_record_ledger": bundle["source_record_ledger"],
            "completeness": bundle["completeness"],
        },
    }
    written: list[Path] = []
    for filename, payload in payloads.items():
        path = output_dir / filename
        _atomic_write_text(path, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        written.append(path)
    handoff_path = output_dir / PACKAGE_FILENAMES["handoff"]
    _atomic_write_text(handoff_path, _handoff_markdown(summary))
    written.append(handoff_path)
    archive_path = output_dir / PACKAGE_FILENAMES["archive"]
    _write_deterministic_zip(archive_path, written)
    return {
        "output_directory": str(output_dir),
        "archive": str(archive_path),
        "archive_sha256": _sha256_bytes(archive_path.read_bytes()),
        "files": [str(item) for item in written],
        "summary": summary,
    }


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", dir=path.parent, delete=False) as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    os.replace(temporary, path)


def _write_deterministic_zip(path: Path, files: list[Path]) -> None:
    with tempfile.NamedTemporaryFile("wb", dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for source in sorted(files, key=lambda item: item.name):
                info = zipfile.ZipInfo(source.name, date_time=FIXED_ZIP_TIMESTAMP)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                archive.writestr(info, source.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        with zipfile.ZipFile(temporary, "r") as archive:
            if archive.testzip() is not None:
                raise RuntimeError("Generated reconstruction ZIP failed integrity verification")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _handoff_markdown(summary: dict[str, Any]) -> str:
    knowledge = summary["knowledge"]
    code = summary["code"]
    context = summary["context"]
    template = summary["template"]
    layout = summary["layout"]
    return (
        "# VIA Discussion Reconstruction Handoff\n\n"
        f"- Engine: {summary['engine_version']}\n"
        f"- Source records: {summary['source_records']['file_count']}\n"
        f"- Segments / Topics / Returns: {knowledge['segments']} / {knowledge['topics']} / {knowledge['topic_returns']}\n"
        f"- Knowledge units / Conflicts: {knowledge['knowledge_units']} / {knowledge['knowledge_conflicts']}\n"
        f"- Instructions / Commands: {knowledge['instructions']} / {knowledge['commands']}\n"
        f"- Code blocks / Families: {code['blocks']} / {code['families']}\n"
        f"- Languages: {', '.join(code['languages']) or '(none)'}\n"
        f"- Build readiness: {code['build_readiness']['status']}\n\n"
        f"- Context mode / Threads / Reply links: {context['document_mode']} / {context['threads']} / {context['reply_links']}\n"
        f"- Standard template: {template['schema']}\n"
        f"- Markdown layout blocks / Exact: {layout['blocks']} / {layout['exact_reconstruction']}\n\n"
        "## Review order\n\n"
        "1. Read `VIA_Reconstruction_Summary.json`.\n"
        "2. Review `VIA_Context_Reconstruction.json` and unresolved reply links.\n"
        "3. Resolve `conflict_register` in `VIA_Knowledge_Registry.json`.\n"
        "4. Review code families, function categories, module templates and unresolved calls.\n"
        "5. Review missing standard-template slots and Markdown layout classification.\n"
        "4. Review `VIA_Instruction_Reconstruction.json`; commands are evidence-only and never executed.\n"
        "5. Compare `VIA_MindMap_Evolution.json`; update/deprecation proposals require approval.\n"
        "6. Use `VIA_MindMap.json` and `VIA_Bilingual_Knowledge_Body.json` for Chinese/English navigation.\n"
        "7. Keep `VIA_Knowledge_Full.json` as the evidence package.\n\n"
        "No extracted code was executed, merged, written as canonical source, or activated.\n"
    )
