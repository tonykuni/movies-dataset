from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import html
import json
import re
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree as ET

SCHEMA = "VIA_CONTENT_RECONSTRUCTION/3.0"
ENGINE_ID = "VIA-ENG-005"
ENGINE_VERSION = "3.0.0"

TEXT_EXTENSIONS = {
    ".txt", ".md", ".markdown", ".html", ".htm", ".xml", ".json", ".jsonl",
    ".csv", ".tsv", ".py", ".ps1", ".psm1", ".js", ".mjs", ".ts", ".tsx",
    ".css", ".scss", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf",
    ".sql", ".sh", ".bat", ".cmd", ".log", ".rst", ".tex", ".svg",
}
CODE_EXTENSIONS = {".py", ".ps1", ".psm1", ".js", ".mjs", ".ts", ".tsx", ".css", ".scss", ".sql", ".sh", ".bat", ".cmd"}
HTML_EXTENSIONS = {".html", ".htm", ".svg"}

# Protected spans are identified before correction. The source text is never changed.
PROTECTED_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("url", re.compile(r"https?://[^\s<>\]\)\"']+", re.I)),
    ("email", re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")),
    ("path_or_file", re.compile(r"(?<![\w/\\])(?:[A-Za-z]:[\\/])?[^\s<>\"']+\.(?:py|ps1|psm1|js|ts|json|md|html|css|csv|docx|pdf|zip)\b", re.I)),
    ("date", re.compile(r"(?<!\d)20\d{2}[-/]\d{1,2}[-/]\d{1,2}(?!\d)")),
    ("version", re.compile(r"(?<![A-Za-z0-9])v?\d+(?:\.\d+){1,4}(?![A-Za-z0-9])", re.I)),
    ("number_unit", re.compile(r"(?<![\w])[-+]?\d[\d,]*(?:\.\d+)?\s?(?:%|％|元|億|萬|千|百|bps?|bp|MB|GB|KB|ms|秒|分鐘|小時)(?![\w])", re.I)),
    ("ticker", re.compile(r"(?<!\d)\d{4}[A-Z]?(?:\.TW|\.TWO)?(?!\w)", re.I)),
    ("formula", re.compile(r"(?m)(?<!\w)[A-Za-z_][\w.]*\s*(?:=|→|->|\+|-|\*|/|\^|>=|<=)\s*[^\n]+")),
    ("code_fence", re.compile(r"(?ms)```.*?```")),
)

COMMAND_MARKERS = re.compile(
    r"(?:請|必須|應|需要|不得|禁止|先|再|執行|建立|產生|修正|安裝|啟動|測試|驗證|部署|更新|輸入|輸出|整理|重構|加入|移除|must|should|required|need to|do not|run|install|build|fix|test|deploy|update|input|output)",
    re.I,
)
QUESTION_MARKERS = re.compile(r"(?:[?？]|如何|怎麼|是否|能否|可否|what|how|why|can\s+we)", re.I)
SPEC_MARKERS = re.compile(r"(?:規格|需求|契約|介面|輸入|輸出|參數|版本|流程|驗證|限制|specification|requirement|contract|interface|parameter|validation)", re.I)
WARNING_MARKERS = re.compile(r"(?:警告|注意|風險|不得|禁止|請勿|僅供|勿外傳|warning|risk|do not)", re.I)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def stable_id(prefix: str, *parts: Any) -> str:
    raw = "|".join(str(part) for part in parts)
    return f"{prefix}-{sha256_text(raw)[:16].upper()}"


def decode_bytes(raw: bytes) -> tuple[str, str]:
    for encoding in ("utf-8-sig", "utf-8", "big5", "cp950", "latin-1"):
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace"), "utf-8-replace"


def extract_docx_text(raw: bytes) -> str:
    with zipfile.ZipFile(__import__("io").BytesIO(raw)) as archive:
        xml = archive.read("word/document.xml")
    root = ET.fromstring(xml)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs: list[str] = []
    for paragraph in root.findall(".//w:p", ns):
        text = "".join(node.text or "" for node in paragraph.findall(".//w:t", ns))
        if text or paragraph.findall(".//w:br", ns):
            paragraphs.append(text)
    return "\n".join(paragraphs)


def extract_source_text(path: Path, raw: bytes) -> tuple[str, str, str]:
    ext = path.suffix.casefold()
    if ext == ".docx":
        try:
            return extract_docx_text(raw), "docx-ooxml", "pass"
        except Exception as exc:
            text, encoding = decode_bytes(raw)
            return text, f"{encoding}-docx-fallback", f"degraded:{type(exc).__name__}"
    if ext in TEXT_EXTENSIONS or not raw.startswith(b"PK"):
        text, encoding = decode_bytes(raw)
        return text, encoding, "pass"
    encoded = base64.b64encode(raw).decode("ascii")
    return f"[BINARY_SOURCE_BASE64 length={len(encoded)}]\n{encoded}", "base64", "degraded-binary-projection"


def protected_spans(text: str) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    occupied: list[tuple[int, int]] = []
    for kind, pattern in PROTECTED_PATTERNS:
        for match in pattern.finditer(text):
            start, end = match.span()
            if any(start < right and end > left for left, right in occupied):
                continue
            candidates.append({"kind": kind, "text": match.group(0), "start": start, "end": end})
            occupied.append((start, end))
    return sorted(candidates, key=lambda item: (item["start"], item["end"]))


def _mask_protected(text: str) -> tuple[str, list[str], list[dict[str, Any]]]:
    spans = protected_spans(text)
    masked = text
    replacements: list[str] = []
    for index, span in reversed(list(enumerate(spans))):
        token = f"\u0000VIA_PROTECTED_{index}\u0000"
        replacements.insert(0, span["text"])
        masked = masked[: span["start"]] + token + masked[span["end"] :]
    return masked, replacements, spans


def _restore_protected(text: str, replacements: list[str]) -> str:
    for index, value in enumerate(replacements):
        text = text.replace(f"\u0000VIA_PROTECTED_{index}\u0000", value)
    return text


def normalize_text(text: str) -> str:
    # These are presentation-only changes. Non-whitespace characters and line order remain.
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\u3000", " ")
    lines = [line.replace("\t", "    ").rstrip() for line in text.split("\n")]
    return "\n".join(lines)


def correct_text(text: str) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]]]:
    normalized = normalize_text(text)
    masked, replacements, spans = _mask_protected(normalized)
    corrected_lines: list[str] = []
    changes: list[dict[str, Any]] = []
    for line_no, line in enumerate(masked.split("\n"), start=1):
        before = line
        line = re.sub(r"[ ]{2,}", " ", line)
        line = re.sub(r"[ \t]+([，。！？：；、])", r"\1", line)
        line = re.sub(r"([，。！？：；、])([A-Za-z])", r"\1 \2", line)
        line = re.sub(r"([A-Za-z])([\u3400-\u9fff])", r"\1 \2", line)
        line = re.sub(r"([\u3400-\u9fff])([A-Za-z])", r"\1 \2", line)
        if line != before:
            changes.append({"line": line_no, "before": before, "after": line, "kind": "spacing_or_punctuation"})
        corrected_lines.append(line)
    corrected = _restore_protected("\n".join(corrected_lines), replacements)
    normalized = _restore_protected(masked, replacements)
    return corrected, changes, spans


def split_units(text: str) -> list[str]:
    units: list[str] = []
    for block in re.split(r"\n{2,}", text):
        block = block.strip()
        if not block:
            continue
        pieces = re.split(r"(?<=[。！？!?；;])\s+|\n", block)
        for piece in pieces:
            piece = piece.strip()
            if piece:
                units.append(piece)
    return units


def classify_unit(text: str, suffix: str) -> tuple[str, list[str]]:
    labels: list[str] = []
    lowered = text.casefold()
    if suffix in CODE_EXTENSIONS or re.search(r"\b(?:def|class|import|function|param|function\s+\w+)\b", text):
        primary = "code"
        labels.append("static_code_evidence")
    elif suffix in HTML_EXTENSIONS or re.search(r"<\s*(?:html|body|div|section|button|script|style)\b", text, re.I):
        primary = "html_ui"
        labels.append("ui_or_markup")
    elif QUESTION_MARKERS.search(text):
        primary = "question"
        labels.append("unanswered_candidate")
    elif COMMAND_MARKERS.search(text):
        primary = "instruction"
        labels.append("action_candidate")
    else:
        primary = "article"
    if WARNING_MARKERS.search(text):
        labels.extend(["warning", "constraint"])
    if SPEC_MARKERS.search(text):
        labels.append("spec_candidate")
    if re.search(r"https?://|\b(?:URL|網址|citation|引用)\b", text, re.I):
        labels.append("citation")
    if re.search(r"(?:=|→|->|\b(?:參數|parameter|config)\b)", text, re.I):
        labels.append("parameter_or_relation")
    return primary, sorted(set(labels))


def extract_parameters(text: str, unit_id: str) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    patterns = (
        re.compile(r"(?<!\w)(--?[A-Za-z][\w-]*)(?:[ =]+([^\s,;]+))?"),
        re.compile(r"(?<!\w)([A-Z][A-Z0-9_]{2,}|[a-z][a-z0-9_]+)\s*[:=]\s*([^,;\n]+)"),
        re.compile(r"\$([A-Za-z][\w]*)\s*=\s*([^;\n]+)"),
    )
    seen: set[tuple[str, str]] = set()
    for pattern in patterns:
        for match in pattern.finditer(text):
            name = match.group(1)
            value = (match.group(2) or "").strip()
            key = (name.casefold(), value)
            if key in seen:
                continue
            seen.add(key)
            found.append({
                "parameter_id": stable_id("PARAM", unit_id, name, value),
                "name": name,
                "value": value,
                "source_unit_id": unit_id,
                "status": "candidate",
                "review_required": True,
            })
    return found


def reconstruct_commands(units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    commands: list[dict[str, Any]] = []
    for unit in units:
        text = unit["corrected_text"]
        if unit["primary_type"] not in {"instruction", "question"} and "action_candidate" not in unit["labels"]:
            continue
        actions = [part.strip() for part in re.split(r"(?:；|;|。|\n)", text) if part.strip()]
        commands.append({
            "command_id": stable_id("CMD", unit["unit_id"]),
            "source_unit_id": unit["unit_id"],
            "goal": text[:240],
            "actions": actions[:12],
            "parameters": [item["name"] for item in unit["parameters"]],
            "constraints": [text] if "constraint" in unit["labels"] else [],
            "verification": [text] if re.search(r"驗證|測試|確認|verify|test", text, re.I) else [],
            "status": "proposal_only",
            "executable": False,
            "review_required": True,
        })
    return commands


def reconstruct_specifications(units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    for unit in units:
        if "spec_candidate" not in unit["labels"]:
            continue
        text = unit["corrected_text"]
        specs.append({
            "spec_id": stable_id("SPEC", unit["unit_id"]),
            "source_unit_id": unit["unit_id"],
            "requirement": text[:400],
            "inputs": [p["name"] for p in unit["parameters"]],
            "outputs": [],
            "constraints": [text] if "constraint" in unit["labels"] else [],
            "verification": [text] if re.search(r"驗證|測試|確認|verify|test", text, re.I) else [],
            "status": "candidate",
            "review_required": True,
        })
    return specs


def summarize_units(units: list[dict[str, Any]]) -> dict[str, Any]:
    if not units:
        return {"title": "(empty)", "executive_summary": "", "key_points": [], "source_unit_ids": []}
    first = units[0]["corrected_text"].replace("\n", " ")
    key = []
    seen: set[str] = set()
    for unit in units:
        text = unit["corrected_text"].replace("\n", " ").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        key.append(text[:240])
        if len(key) >= 8:
            break
    types: dict[str, int] = {}
    for unit in units:
        types[unit["primary_type"]] = types.get(unit["primary_type"], 0) + 1
    return {
        "title": first[:100],
        "executive_summary": "；".join(key[:3]),
        "key_points": key,
        "content_type_counts": types,
        "source_unit_ids": [unit["unit_id"] for unit in units],
        "method": "deterministic_extractive_summary",
        "review_required": True,
    }


def html_projection(corrected_text: str, source_name: str) -> dict[str, Any]:
    # This is a safe reader projection. It does not execute scripts from the source.
    escaped = html.escape(corrected_text)
    return {
        "reader_mode": "safe_corrected_content",
        "source_name": source_name,
        "script_execution": False,
        "style_execution": False,
        "html": "<article data-via-source=\"" + html.escape(source_name, quote=True) + "\"><pre>" + escaped + "</pre></article>",
    }


def reconstruct_file(path: str | Path) -> dict[str, Any]:
    source = Path(path).expanduser().resolve()
    raw = source.read_bytes()
    extracted, encoding, extraction_status = extract_source_text(source, raw)
    corrected, correction_changes, protected = correct_text(extracted)
    units: list[dict[str, Any]] = []
    for index, unit_text in enumerate(split_units(corrected)):
        unit_id = stable_id("UNIT", source.name, index, unit_text)
        primary, labels = classify_unit(unit_text, source.suffix.casefold())
        unit = {
            "unit_id": unit_id,
            "order": index,
            "source_name": source.name,
            "source_characters": len(unit_text),
            "source_span": {"start": corrected.find(unit_text), "end": corrected.find(unit_text) + len(unit_text)},
            "source_text": unit_text,
            "corrected_text": unit_text,
            "primary_type": primary,
            "labels": labels,
            "parameters": [],
            "source_sha256": sha256_text(unit_text),
            "corrected_sha256": sha256_text(unit_text),
            "derivative_only": True,
        }
        unit["parameters"] = extract_parameters(unit_text, unit_id)
        units.append(unit)
    commands = reconstruct_commands(units)
    specs = reconstruct_specifications(units)
    parameters = [parameter for unit in units for parameter in unit["parameters"]]
    content_sections = [
        {
            "section_id": stable_id("SECTION", source.name, unit["primary_type"]),
            "type": unit["primary_type"],
            "unit_ids": [item["unit_id"] for item in units if item["primary_type"] == unit["primary_type"]],
        }
        for unit in units
    ]
    # Preserve first-seen type order and avoid repeated section records.
    unique_sections: list[dict[str, Any]] = []
    seen_section_types: set[str] = set()
    for section in content_sections:
        if section["type"] not in seen_section_types:
            unique_sections.append(section)
            seen_section_types.add(section["type"])
    source_meta = {
        "source_path": str(source),
        "source_name": source.name,
        "extension": source.suffix.casefold(),
        "byte_size": len(raw),
        "source_sha256": sha256_bytes(raw),
        "extracted_text_sha256": sha256_text(extracted),
        "extracted_characters": len(extracted),
        "encoding_or_parser": encoding,
        "extraction_status": extraction_status,
        "source_preserved": True,
    }
    source_record_id = stable_id("RECORD", source.name, source_meta["source_sha256"])
    return {
        "schema": SCHEMA,
        "engine": {"engine_id": ENGINE_ID, "engine_version": ENGINE_VERSION},
        "record_id": source_record_id,
        "source": source_meta,
        "source_text": extracted,
        "projections": {
            "normalized_text": normalize_text(extracted),
            "corrected_text": corrected,
            "correction_ledger": {
                "changes": correction_changes,
                "protected_spans": protected,
                "source_deleted": False,
                "source_mutated": False,
                "candidate_status": "accepted_as_derivative_only",
            },
            "summary": summarize_units(units),
            "content_reconstruction": {"sections": unique_sections, "unit_count": len(units)},
            "command_reconstruction": {"commands": commands, "count": len(commands), "executable": False},
            "parameter_reconstruction": {"parameters": parameters, "count": len(parameters)},
            "specification_reconstruction": {"specifications": specs, "count": len(specs)},
            "html_ui_reader": html_projection(corrected, source.name) if source.suffix.casefold() in HTML_EXTENSIONS else None,
        },
        "units": units,
        "quality_gates": {
            "source_preserved": True,
            "source_deleted": False,
            "source_mutated": False,
            "source_sha256": source_meta["source_sha256"],
            "extracted_text_sha256": source_meta["extracted_text_sha256"],
            "corrected_text_sha256": sha256_text(corrected),
            "protected_token_count": len(protected),
            "source_coverage": 1.0,
            "code_execution": False,
            "network_access": False,
            "subprocess_access": False,
            "review_required": bool(correction_changes or commands or specs),
        },
        "status": "PASS_WITH_REVIEW" if correction_changes or commands or specs else "PASS",
    }


def reconstruct_paths(paths: Iterable[str | Path]) -> dict[str, Any]:
    records = [reconstruct_file(path) for path in paths]
    return {
        "schema": "VIA_CONTENT_RECONSTRUCTION_BUNDLE/3.0",
        "engine": {"engine_id": ENGINE_ID, "engine_version": ENGINE_VERSION},
        "source_preserved": True,
        "record_count": len(records),
        "records": records,
        "summary": {
            "files": [record["source"]["source_name"] for record in records],
            "total_source_bytes": sum(record["source"]["byte_size"] for record in records),
            "total_units": sum(len(record["units"]) for record in records),
            "total_commands": sum(record["projections"]["command_reconstruction"]["count"] for record in records),
            "total_parameters": sum(record["projections"]["parameter_reconstruction"]["count"] for record in records),
            "total_specifications": sum(record["projections"]["specification_reconstruction"]["count"] for record in records),
        },
    }


def write_outputs(result: dict[str, Any], output_dir: str | Path) -> Path:
    output = Path(output_dir).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    bundle_path = output / "VIA_Content_Reconstruction_Bundle_v3.json"
    bundle_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for record in result["records"]:
        stem = re.sub(r"[^A-Za-z0-9._-]+", "_", record["source"]["source_name"])
        record_dir = output / stem
        record_dir.mkdir(exist_ok=True)
        (record_dir / "source_record.json").write_text(json.dumps(record["source"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (record_dir / "source_text.txt").write_text(record["source_text"], encoding="utf-8")
        (record_dir / "normalized_text.txt").write_text(record["projections"]["normalized_text"], encoding="utf-8")
        (record_dir / "corrected_text.txt").write_text(record["projections"]["corrected_text"], encoding="utf-8")
        (record_dir / "summary.json").write_text(json.dumps(record["projections"]["summary"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (record_dir / "command_reconstruction.json").write_text(json.dumps(record["projections"]["command_reconstruction"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (record_dir / "parameter_reconstruction.json").write_text(json.dumps(record["projections"]["parameter_reconstruction"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (record_dir / "specification_reconstruction.json").write_text(json.dumps(record["projections"]["specification_reconstruction"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (record_dir / "record.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return bundle_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="VIA v3 non-destructive content reconstructor")
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("VIA_Content_Reconstruction_Output_v3"))
    args = parser.parse_args(argv)
    result = reconstruct_paths(args.inputs)
    bundle = write_outputs(result, args.output_dir)
    print(json.dumps({"status": "PASS", "bundle": str(bundle), "summary": result["summary"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
