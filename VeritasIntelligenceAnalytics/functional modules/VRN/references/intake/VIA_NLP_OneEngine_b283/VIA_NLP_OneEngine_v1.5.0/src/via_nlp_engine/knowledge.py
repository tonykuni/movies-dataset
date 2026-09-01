"""Lossless dialogue segmentation, knowledge reconstruction and code governance."""

from __future__ import annotations

import ast
import hashlib
import json
import math
import re
import shutil
import subprocess
import tomllib
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .discourse import (
    CPUHierarchicalTopicOrganizer,
    build_dialogue_flow,
    build_refinement_ledger,
    infer_content_roles,
)
from .code_reconstruction import CodeDiscussionReconstructor
from .code_restoration import CodeRestorer
from .bilingual_ops import decorate_mind_map
from .context_reconstruction import ContextReconstructor
from .discussion_ops import DiscussionKnowledgeReconstructor
from .function_classifier import FunctionClassifier
from .instruction_ops import InstructionReconstructor
from .knowledge_body_ops import build_bilingual_knowledge_body
from .layout_analysis import MarkdownLayoutAnalyzer
from .mindmap_enrichment import enrich_mind_map_v15
from .mindmap_evolution import build_mind_map_evolution
from .provider_registry import LocalProviderRegistry
from .template_reconstruction import StandardTemplateReconstructor
from .text_ops import TextProcessor
from .table_ops import TextTableExtractor


DEFAULT_SEGMENT_CHARS = 8000
MAX_SSOT_TERMS = 500
MAX_MINDMAP_TOPIC_POINTS = 8
MAX_AI_GRAPH_EDGES = 4000

STRONG_BOUNDARY_RE = re.compile(
    r"(?m)^(?=(?:\s*(?:\d{4}[-/]\d{1,2}[-/]\d{1,2}[ T])?\d{1,2}:\d{2}(?::\d{2})?\s+\S|\s*(?:User|Assistant|使用者|助理|Human|AI)\s*[:：]|\s*-\s*(?:role|speaker|author)\s*:\s*\S|\s*#{1,6}\s+|\s*[-=]{8,}\s*$))"
)
FENCED_CODE_RE = re.compile(r"(?ms)^```(?P<language>[^\n`]*)\n(?P<code>.*?)^```\s*$")
VIA_SOURCE_CODE_RECORD_RE = re.compile(
    r"(?ms)^===== BEGIN VIA SOURCE RECORD (?P<record_id>[^\n]+) =====\n"
    r"SourceName: (?P<source_name>[^\n]+)\n"
    r"SourceExtension: (?P<extension>\.[^\n]+)\n"
    r"ExtractedTextSHA256: (?P<sha256>[0-9a-f]{64})\n"
    r"===== BEGIN EXTRACTED CONTENT =====\n"
    r"(?P<code>.*?)"
    r"(?=\n===== END EXTRACTED CONTENT =====\n===== END VIA SOURCE RECORD (?P=record_id) =====)"
)
PAIR_TERM_RE = re.compile(r"(?P<left>[\u3400-\u9fff][\u3400-\u9fff·\-／/ ]{1,30})\s*[（(]\s*(?P<right>[A-Za-z][A-Za-z0-9 ._+&/\-]{1,50})\s*[）)]")
ACRONYM_RE = re.compile(r"(?<![A-Za-z0-9])(?:[A-Z][A-Z0-9]{1,10}|[A-Z]{2,8}(?:-[A-Z0-9]{1,8})+)(?![A-Za-z0-9])")
TIMESTAMP_RE = re.compile(
    r"^\s*(?P<stamp>(?:\d{4}[-/]\d{1,2}[-/]\d{1,2}[ T])?\d{1,2}:\d{2}(?::\d{2})?)\s+(?P<speaker>[^\n:：]{1,80})(?:[:：])?"
)
MESSAGE_PREFIX_RE = re.compile(r"^\s*(?P<speaker>User|Assistant|使用者|助理|Human|AI)\s*[:：]", re.I)
ROLE_FIELD_RE = re.compile(r"^\s*-\s*(?:role|speaker|author)\s*:\s*(?P<speaker>[^\r\n]+)", re.I)
HEADING_RE = re.compile(r"^\s*(?:#{1,6}\s+|(?:第?[一二三四五六七八九十\d]+[、.)．]|[一二三四五六七八九十]+、)\s*)")
UNFENCED_CODE_HINT_RE = re.compile(
    r"^\s*(?:from\s+\w+\s+import|import\s+\w+|def\s+\w+\s*\(|class\s+\w+|function\s+\w+\s*\(|const\s+\w+\s*=|let\s+\w+\s*=|param\s*\(|function\s+[A-Za-z][\w-]*\s*\{|\$[A-Za-z_]\w*\s*=|\{\s*\"[^\"]+\"\s*:|SELECT\s+|WITH\s+\w+\s+AS\s*\(|CREATE\s+(?:TABLE|VIEW)|<!DOCTYPE\s+html|<html\b|<script\b|<style\b|#!/(?:usr/bin/env\s+)?(?:ba)?sh\b|[A-Za-z_][\w.-]*\s*=\s*[^=])",
    re.I,
)
UNFENCED_CODE_CONTINUATION_RE = re.compile(
    r"^\s*(?:FROM|WHERE|JOIN|LEFT\s+JOIN|RIGHT\s+JOIN|INNER\s+JOIN|GROUP\s+BY|ORDER\s+BY|HAVING|LIMIT|UNION|VALUES|SET|ON|AND|OR|ELSE|ELIF|FI|DONE|THEN|RETURN|CATCH|FINALLY|</?[A-Za-z][^>]*>|[.#]?[A-Za-z][\w-]*(?:\s+[.#]?[A-Za-z][\w-]*)*\s*\{|[}\])],?\s*$)",
    re.I,
)
DESTRUCTIVE_CODE_RE = re.compile(r"\b(?:rm\s+-rf|Remove-Item\b.*-Recurse|DROP\s+(?:TABLE|DATABASE)|shutil\.rmtree|os\.remove|del\s+/[sq])\b", re.I)
NETWORK_CODE_RE = re.compile(r"\b(?:requests\.(?:get|post)|urllib\.request|Invoke-WebRequest|fetch\s*\(|axios\.)", re.I)

KEYWORD_CATEGORIES = {
    "governance": {"SSOT", "Regex", "治理", "合約", "契約", "Hydra", "稽核", "版本", "回滾", "sandbox", "governance"},
    "nlp": {"NLP", "斷詞", "實體", "摘要", "語意", "翻譯", "keyword", "embedding", "RAG", "LLM", "token"},
    "engineering": {"Python", "PowerShell", "JavaScript", "API", "AST", "JSON", "DuckDB", "Polars", "FastAPI", "cache"},
    "finance": {"股票", "營收", "EPS", "市場", "資金", "利率", "匯率", "通膨", "ETF", "財報", "投資"},
    "workflow": {"流程", "任務", "路由", "測試", "修復", "部署", "整合", "pipeline", "monitor", "加速器"},
}


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _json_safe(value: Any) -> Any:
    """Convert static-parser literals to deterministic JSON-compatible values."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (set, frozenset)):
        converted = [_json_safe(item) for item in value]
        return sorted(converted, key=lambda item: json.dumps(item, ensure_ascii=False, sort_keys=True, default=str))
    if isinstance(value, bytes):
        return {"type": "bytes", "hex": value.hex()}
    return {"type": type(value).__name__, "representation": str(value)}


def _inside(position: int, ranges: list[tuple[int, int]]) -> bool:
    return any(start < position < end for start, end in ranges)


def _split_large_exact(text: str, absolute_start: int, maximum: int) -> list[tuple[int, int, str]]:
    if len(text) <= maximum:
        return [(absolute_start, absolute_start + len(text), text)]
    output: list[tuple[int, int, str]] = []
    local_start = 0
    while local_start < len(text):
        local_end = min(len(text), local_start + maximum)
        if local_end < len(text):
            boundary = text.rfind("\n", local_start + maximum // 2, local_end)
            if boundary > local_start:
                local_end = boundary + 1
        piece = text[local_start:local_end]
        output.append((absolute_start + local_start, absolute_start + local_end, piece))
        local_start = local_end
    return output


@dataclass(slots=True)
class RawSegment:
    segment_id: str
    start: int
    end: int
    text: str
    kind: str
    timestamp: str | None
    speaker: str | None
    sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "segment_id": self.segment_id,
            "source_span": {"start": self.start, "end": self.end},
            "text": self.text,
            "kind": self.kind,
            "timestamp": self.timestamp,
            "speaker": self.speaker,
            "sha256": self.sha256,
        }


class LosslessSegmenter:
    def __init__(self, max_segment_chars: int = DEFAULT_SEGMENT_CHARS) -> None:
        self.max_segment_chars = max_segment_chars

    def segment(self, text: str) -> dict[str, Any]:
        code_ranges = [(match.start(), match.end()) for match in FENCED_CODE_RE.finditer(text)]
        boundaries = {0, len(text)}
        for match in STRONG_BOUNDARY_RE.finditer(text):
            if not _inside(match.start(), code_ranges):
                boundaries.add(match.start())
        ordered = sorted(boundaries)
        pieces: list[tuple[int, int, str]] = []
        for start, end in zip(ordered, ordered[1:]):
            if end > start:
                pieces.extend(_split_large_exact(text[start:end], start, self.max_segment_chars))

        segments: list[RawSegment] = []
        for index, (start, end, piece) in enumerate(pieces, start=1):
            stripped = piece.lstrip()
            first = stripped.splitlines()[0] if stripped else ""
            timestamp_match = TIMESTAMP_RE.match(first)
            message_match = MESSAGE_PREFIX_RE.match(first) or ROLE_FIELD_RE.match(first)
            if stripped.startswith("```"):
                kind = "code"
            elif timestamp_match or message_match:
                kind = "message"
            elif HEADING_RE.match(first):
                kind = "heading_section"
            elif "```" in piece:
                kind = "mixed_text_code"
            else:
                kind = "article"
            segments.append(
                RawSegment(
                    segment_id=f"SEG-{index:06d}",
                    start=start,
                    end=end,
                    text=piece,
                    kind=kind,
                    timestamp=timestamp_match.group("stamp") if timestamp_match else None,
                    speaker=(
                        timestamp_match.group("speaker").strip()
                        if timestamp_match
                        else message_match.group("speaker").strip()
                        if message_match
                        else None
                    ),
                    sha256=_sha256_text(piece),
                )
            )

        reconstructed = "".join(item.text for item in segments)
        exact = reconstructed == text
        return {
            "segments": [item.to_dict() for item in segments],
            "completeness": {
                "source_characters": len(text),
                "reconstructed_characters": len(reconstructed),
                "coverage_ratio": 1.0 if exact else len(reconstructed) / max(1, len(text)),
                "exact_reconstruction": exact,
                "source_sha256": _sha256_text(text),
                "reconstructed_sha256": _sha256_text(reconstructed),
                "segment_count": len(segments),
            },
        }


class CodeExtractor:
    LANGUAGE_ALIASES = {
        "py": "python", "python3": "python", "ps": "powershell", "ps1": "powershell", "psm1": "powershell",
        "shell": "bash", "sh": "bash", "js": "javascript", "jsx": "javascript", "javascriptsvg": "javascript",
        "ts": "typescript", "tsx": "typescript", "jsonc": "json", "yml": "yaml", "htm": "html",
        "postgresql": "sql", "sqlite": "sql", "csssvg": "css", "": "unknown",
    }
    SOURCE_EXTENSION_LANGUAGES = {
        ".py": "python", ".ps1": "powershell", ".psm1": "powershell",
        ".js": "javascript", ".jsx": "javascript", ".ts": "typescript", ".tsx": "typescript",
        ".json": "json", ".sql": "sql", ".html": "html", ".htm": "html",
        ".xml": "xml", ".css": "css", ".yaml": "yaml", ".yml": "yaml",
        ".toml": "toml", ".sh": "bash", ".bash": "bash",
    }

    def extract(self, text: str, segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        blocks: list[dict[str, Any]] = []
        occupied: list[tuple[int, int]] = []
        for match in VIA_SOURCE_CODE_RECORD_RE.finditer(text):
            extension = match.group("extension").casefold()
            language = self.SOURCE_EXTENSION_LANGUAGES.get(extension)
            if language is None:
                continue
            block = self._build_block(
                len(blocks) + 1,
                language,
                match.group("code"),
                match.start("code"),
                match.end("code"),
                segments,
                "source_record",
                self._language_detection(language, "source_extension", extension),
            )
            block["source_record"] = {
                "record_id": match.group("record_id"),
                "source_name": match.group("source_name"),
                "extension": extension,
                "declared_extracted_text_sha256": match.group("sha256"),
                "hash_verified": _sha256_text(match.group("code")) == match.group("sha256"),
            }
            blocks.append(block)
            occupied.append((match.start("code"), match.end("code")))
        for match in FENCED_CODE_RE.finditer(text):
            if any(match.start() < right and match.end() > left for left, right in occupied):
                continue
            declared_raw = match.group("language").strip().split()[0] if match.group("language").strip() else ""
            language = self._language(declared_raw)
            if language == "unknown":
                language = self._guess_language(match.group("code"))
                detection = self._language_detection(language, "heuristic", declared_raw)
            else:
                detection = self._language_detection(language, "declared", declared_raw)
            blocks.append(
                self._build_block(
                    len(blocks) + 1,
                    language,
                    match.group("code"),
                    match.start(),
                    match.end(),
                    segments,
                    "fenced",
                    detection,
                )
            )
            occupied.append((match.start(), match.end()))

        line_records = list(self._line_records(text))
        candidate: list[tuple[int, int, str]] = []
        for start, end, line in line_records:
            if any(start >= left and start < right for left, right in occupied):
                if len(candidate) >= 3:
                    blocks.append(self._unfenced_block(candidate, blocks, segments))
                candidate = []
                continue
            if UNFENCED_CODE_HINT_RE.match(line) or (
                candidate
                and (
                    line.startswith((" ", "\t"))
                    or not line.strip()
                    or UNFENCED_CODE_CONTINUATION_RE.match(line)
                )
            ):
                candidate.append((start, end, line))
            else:
                if len([item for item in candidate if item[2].strip()]) >= 3:
                    blocks.append(self._unfenced_block(candidate, blocks, segments))
                candidate = []
        if len([item for item in candidate if item[2].strip()]) >= 3:
            blocks.append(self._unfenced_block(candidate, blocks, segments))
        return blocks

    @staticmethod
    def _line_records(text: str) -> Iterable[tuple[int, int, str]]:
        position = 0
        for line in text.splitlines(keepends=True):
            yield position, position + len(line), line
            position += len(line)

    def _unfenced_block(self, records: list[tuple[int, int, str]], blocks: list[dict[str, Any]], segments: list[dict[str, Any]]) -> dict[str, Any]:
        code = "".join(item[2] for item in records).strip("\n")
        language = self._guess_language(code)
        return self._build_block(
            len(blocks) + 1,
            language,
            code,
            records[0][0],
            records[-1][1],
            segments,
            "heuristic",
            self._language_detection(language, "heuristic", ""),
        )

    def _language(self, value: str) -> str:
        lower = value.lower()
        return self.LANGUAGE_ALIASES.get(lower, lower or "unknown")

    @staticmethod
    def _language_detection(language: str, source: str, declared_tag: str) -> dict[str, Any]:
        heuristic_confidence = {
            "python": 0.92,
            "powershell": 0.90,
            "javascript": 0.86,
            "typescript": 0.86,
            "sql": 0.86,
            "html": 0.90,
            "xml": 0.90,
            "css": 0.82,
            "bash": 0.90,
            "json": 0.86,
            "toml": 0.68,
            "yaml": 0.58,
            "unknown": 0.0,
        }
        confidence = 1.0 if source in {"declared", "source_extension"} else heuristic_confidence.get(language, 0.5)
        return {
            "source": source,
            "declared_tag": declared_tag or None,
            "confidence": confidence,
            "review_required": confidence < 0.75,
        }

    @staticmethod
    def _guess_language(code: str) -> str:
        if re.search(r"(?m)^\s*(?:def|class|from\s+\w+\s+import|import\s+\w+)", code):
            return "python"
        if re.search(r"(?mi)^\s*(?:param\s*\(|function\s+[\w-]+|\$\w+\s*=)", code):
            return "powershell"
        if re.search(r"(?m)^\s*(?:function|const|let|var)\s+", code):
            return "javascript"
        if re.search(r"(?mi)^\s*(?:SELECT|WITH\s+\w+\s+AS\s*\(|CREATE\s+(?:TABLE|VIEW)|INSERT\s+INTO|UPDATE\s+\w+\s+SET)\b", code):
            return "sql"
        if re.search(r"(?is)^\s*(?:<!DOCTYPE\s+html|<html\b|<div\b|<script\b|<style\b)", code):
            return "html"
        if re.search(r"(?m)^\s*(?:[.#]?[A-Za-z][\w-]*(?:\s+[.#]?[A-Za-z][\w-]*)*)\s*\{", code):
            return "css"
        if re.search(r"(?m)^\s*#!/(?:usr/bin/env\s+)?(?:ba)?sh\b", code):
            return "bash"
        if code.lstrip().startswith(("{", "[")):
            return "json"
        if re.search(r"(?m)^[A-Za-z_][\w.-]*\s*=\s*[^=]", code):
            return "toml"
        if re.search(r"(?m)^[A-Za-z_][\w.-]*\s*:\s*\S", code):
            return "yaml"
        return "unknown"

    def _build_block(
        self,
        index: int,
        language: str,
        code: str,
        start: int,
        end: int,
        segments: list[dict[str, Any]],
        extraction: str,
        language_detection: dict[str, Any],
    ) -> dict[str, Any]:
        syntax, engine_spec = self._inspect(language, code)
        engine_spec = _json_safe(engine_spec)
        risks = []
        if DESTRUCTIVE_CODE_RE.search(code):
            risks.append("destructive_operation")
        if NETWORK_CODE_RE.search(code):
            risks.append("network_access")
        if len(code) > 100_000:
            risks.append("oversized_code_block")
        references = [
            item["segment_id"]
            for item in segments
            if start < int(item["source_span"]["end"]) and end > int(item["source_span"]["start"])
        ]
        return {
            "code_id": f"CODE-{index:05d}",
            "language": language,
            "language_detection": language_detection,
            "extraction": extraction,
            "source_span": {"start": start, "end": end},
            "source_segments": references,
            "sha256": _sha256_text(code),
            "code": code,
            "syntax": syntax,
            "engine_spec": engine_spec,
            "hydra_risks": risks,
            "execution_policy": "never_execute_from_untrusted_text",
        }

    def _inspect(self, language: str, code: str) -> tuple[dict[str, Any], dict[str, Any]]:
        spec: dict[str, Any] = {
            "parameters": {},
            "functions": [],
            "function_contracts": [],
            "classes": [],
            "imports": [],
            "dependencies": [],
            "calls": [],
        }
        if language == "python":
            try:
                tree = ast.parse(code)
            except SyntaxError as exc:
                return {"status": "invalid", "error": str(exc), "line": exc.lineno, "column": exc.offset}, spec
            for node in tree.body:
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    spec["imports"].append(ast.unparse(node))
                    if isinstance(node, ast.Import):
                        spec["dependencies"].extend(alias.name.split(".")[0] for alias in node.names)
                    elif node.module:
                        spec["dependencies"].append(node.module.split(".")[0])
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    spec["functions"].append(node.name)
                    positional = list(node.args.posonlyargs) + list(node.args.args)
                    defaults = [None] * (len(positional) - len(node.args.defaults)) + list(node.args.defaults)
                    arguments = []
                    for argument, default in zip(positional, defaults):
                        arguments.append(
                            {
                                "name": argument.arg,
                                "annotation": ast.unparse(argument.annotation) if argument.annotation else None,
                                "default": ast.unparse(default) if default is not None else None,
                                "kind": "positional",
                            }
                        )
                    for argument, default in zip(node.args.kwonlyargs, node.args.kw_defaults):
                        arguments.append(
                            {
                                "name": argument.arg,
                                "annotation": ast.unparse(argument.annotation) if argument.annotation else None,
                                "default": ast.unparse(default) if default is not None else None,
                                "kind": "keyword_only",
                            }
                        )
                    if node.args.vararg:
                        arguments.append({"name": node.args.vararg.arg, "annotation": None, "default": None, "kind": "vararg"})
                    if node.args.kwarg:
                        arguments.append({"name": node.args.kwarg.arg, "annotation": None, "default": None, "kind": "kwarg"})
                    calls = sorted(
                        {
                            ast.unparse(child.func)
                            for child in ast.walk(node)
                            if isinstance(child, ast.Call) and isinstance(child.func, (ast.Name, ast.Attribute))
                        }
                    )
                    spec["calls"].extend(calls)
                    spec["function_contracts"].append(
                        {
                            "name": node.name,
                            "async": isinstance(node, ast.AsyncFunctionDef),
                            "arguments": arguments,
                            "returns": ast.unparse(node.returns) if node.returns else None,
                            "calls": calls,
                            "docstring": (ast.get_docstring(node) or "")[:500],
                        }
                    )
                elif isinstance(node, ast.ClassDef):
                    spec["classes"].append(node.name)
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id.isupper():
                            try:
                                spec["parameters"][target.id] = ast.literal_eval(node.value)
                            except (ValueError, TypeError):
                                spec["parameters"][target.id] = {"expression": ast.unparse(node.value)}
            spec["dependencies"] = sorted(set(spec["dependencies"]))
            spec["calls"] = sorted(set(spec["calls"]))
            return {"status": "valid", "backend": "python_ast"}, spec
        if language == "json":
            try:
                value = json.loads(code)
                if isinstance(value, dict):
                    spec["parameters"] = value
                return {"status": "valid", "backend": "json"}, spec
            except json.JSONDecodeError as exc:
                return {"status": "invalid", "error": str(exc), "line": exc.lineno, "column": exc.colno}, spec
        if language in {"javascript", "typescript"}:
            declared_functions = re.findall(r"\bfunction\s+([A-Za-z_$][\w$]*)\s*\(", code)
            arrow_functions = re.findall(r"\b(?:const|let)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>", code)
            spec["functions"] = list(dict.fromkeys(declared_functions + arrow_functions))
            for name, arguments in re.findall(r"\bfunction\s+([A-Za-z_$][\w$]*)\s*\(([^)]*)\)", code):
                spec["function_contracts"].append(
                    {
                        "name": name,
                        "async": False,
                        "arguments": [
                            {"name": item.strip().split("=")[0].strip(), "default": item.split("=", 1)[1].strip() if "=" in item else None}
                            for item in arguments.split(",")
                            if item.strip()
                        ],
                        "returns": None,
                        "calls": [],
                    }
                )
            for name, arguments in re.findall(r"\b(?:const|let)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\(([^)]*)\)\s*=>", code):
                spec["function_contracts"].append(
                    {
                        "name": name,
                        "async": bool(re.search(rf"\b(?:const|let)\s+{re.escape(name)}\s*=\s*async\b", code)),
                        "arguments": [{"name": item.strip().split("=")[0].strip(), "default": item.split("=", 1)[1].strip() if "=" in item else None} for item in arguments.split(",") if item.strip()],
                        "returns": None,
                        "calls": [],
                    }
                )
            imports = re.findall(r"\bfrom\s+['\"]([^'\"]+)['\"]", code)
            requires = re.findall(r"\brequire\s*\(\s*['\"]([^'\"]+)['\"]", code)
            spec["dependencies"] = sorted(set(imports + requires))
            for name, raw in re.findall(r"(?m)^\s*(?:const|let)\s+([A-Za-z_$][\w$]*)\s*=\s*([^;\n]+)", code):
                if name.upper() == name or name.endswith(("Config", "CONFIG")):
                    spec["parameters"][name] = {"expression": raw.strip()}
            return self._balanced_syntax(code, "javascript_lexical"), spec
        if language == "powershell":
            spec["functions"] = re.findall(r"(?mi)^\s*function\s+([A-Za-z][\w-]*)", code)
            for name, default in re.findall(r"(?m)\[\w+(?:\[\])?\]\s*\$(\w+)\s*(?:=\s*([^,\r\n)]+))?", code):
                spec["parameters"][name] = default.strip() if default else None
            spec["function_contracts"] = [
                {"name": name, "async": False, "arguments": [], "returns": None, "calls": []}
                for name in spec["functions"]
            ]
            spec["dependencies"] = sorted(set(re.findall(r"(?mi)^\s*(?:Import-Module|#requires\s+-Modules?)\s+['\"]?([A-Za-z0-9_.-]+)", code)))
            powershell_syntax = self._powershell_ast(code)
            return powershell_syntax or self._balanced_syntax(code, "powershell_lexical_fallback"), spec
        if language == "sql":
            statements = re.findall(r"(?mi)^\s*(SELECT|WITH|CREATE|INSERT|UPDATE|DELETE|MERGE|DROP|ALTER)\b", code)
            read_tables = re.findall(r"(?i)\b(?:FROM|JOIN)\s+([A-Za-z_][\w.$-]*)", code)
            write_tables = re.findall(r"(?i)\b(?:INSERT\s+INTO|UPDATE|MERGE\s+INTO|CREATE\s+TABLE|DELETE\s+FROM)\s+([A-Za-z_][\w.$-]*)", code)
            ctes = re.findall(r"(?i)(?:\bWITH|,)\s*([A-Za-z_][\w$-]*)\s+AS\s*\(", code)
            spec["functions"] = list(dict.fromkeys(ctes))
            spec["dependencies"] = sorted(set(read_tables))
            spec["reads"] = sorted(set(read_tables))
            spec["writes"] = sorted(set(write_tables))
            spec["statements"] = [item.upper() for item in statements]
            spec["parameters"] = {name: None for name in sorted(set(re.findall(r"(?<!:):([A-Za-z_]\w*)", code)))}
            return self._balanced_syntax(code, "sql_lexical"), spec
        if language == "bash":
            functions = re.findall(r"(?m)^\s*(?:function\s+)?([A-Za-z_]\w*)\s*\(\s*\)\s*\{", code)
            spec["functions"] = list(dict.fromkeys(functions))
            spec["function_contracts"] = [
                {"name": name, "async": False, "arguments": [], "returns": None, "calls": []}
                for name in spec["functions"]
            ]
            spec["dependencies"] = sorted(set(re.findall(r"(?m)^\s*(?:source|\.)\s+['\"]?([^'\"\s]+)", code)))
            for name, value in re.findall(r"(?m)^\s*([A-Z][A-Z0-9_]*)\s*=\s*([^\r\n]+)", code):
                spec["parameters"][name] = value.strip()
            return self._balanced_syntax(code, "bash_lexical"), spec
        if language in {"html", "xml"}:
            spec["dependencies"] = sorted(
                set(re.findall(r"(?i)\b(?:src|href)\s*=\s*['\"]([^'\"]+)['\"]", code))
            )
            spec["parameters"] = {
                f"id:{name}": None for name in sorted(set(re.findall(r"(?i)\bid\s*=\s*['\"]([^'\"]+)['\"]", code)))
            }
            spec["elements"] = re.findall(r"(?i)<([A-Za-z][\w:-]*)\b", code)
            if language == "xml":
                try:
                    ET.fromstring(code)
                    return {"status": "valid", "backend": "xml_elementtree"}, spec
                except ET.ParseError as exc:
                    return {"status": "invalid", "backend": "xml_elementtree", "error": str(exc)}, spec
            return self._balanced_syntax(code, "html_lexical"), spec
        if language == "css":
            selectors = [item.strip() for item in re.findall(r"(?m)([^{}]+)\s*\{", code) if item.strip()]
            spec["selectors"] = selectors
            spec["parameters"] = {
                name: value.strip()
                for name, value in re.findall(r"(?m)(--[A-Za-z0-9_-]+)\s*:\s*([^;}{]+)", code)
            }
            return self._balanced_syntax(code, "css_lexical"), spec
        if language == "toml":
            try:
                value = tomllib.loads(code)
                spec["parameters"] = value
                return {"status": "valid", "backend": "python_tomllib"}, spec
            except tomllib.TOMLDecodeError as exc:
                return {"status": "invalid", "backend": "python_tomllib", "error": str(exc)}, spec
        if language == "yaml":
            top_level = re.findall(r"(?m)^([A-Za-z_][\w.-]*)\s*:\s*([^\r\n#]*)", code)
            spec["parameters"] = {name: value.strip() or None for name, value in top_level}
            status = "valid_lexical_only" if top_level else "invalid"
            return {"status": status, "backend": "yaml_lexical_no_coercion"}, spec
        return {"status": "unchecked", "backend": "none"}, spec

    @staticmethod
    def _balanced_syntax(code: str, backend: str) -> dict[str, Any]:
        pairs = {"(": ")", "[": "]", "{": "}"}
        stack: list[str] = []
        quote: str | None = None
        escaped = False
        for char in code:
            if escaped:
                escaped = False
                continue
            if char == "\\":
                escaped = True
                continue
            if quote:
                if char == quote:
                    quote = None
                continue
            if char in {'"', "'", "`"}:
                quote = char
            elif char in pairs:
                stack.append(pairs[char])
            elif char in pairs.values():
                if not stack or stack.pop() != char:
                    return {"status": "invalid", "error": f"unexpected {char}", "backend": backend}
        if quote or stack:
            return {"status": "invalid", "error": "unclosed quote or bracket", "backend": backend}
        return {"status": "valid_lexical_only", "backend": backend}

    @staticmethod
    def _powershell_ast(code: str) -> dict[str, Any] | None:
        executable = shutil.which("pwsh")
        if not executable:
            return None
        parser_script = """
$source = [Console]::In.ReadToEnd()
$tokens = $null
$errors = $null
[void][System.Management.Automation.Language.Parser]::ParseInput($source, [ref]$tokens, [ref]$errors)
$result = [ordered]@{
  status = $(if ($errors.Count -eq 0) { 'valid' } else { 'invalid' })
  backend = 'powershell_ast'
  errors = @($errors | ForEach-Object { [ordered]@{
    message = $_.Message
    line = $_.Extent.StartLineNumber
    column = $_.Extent.StartColumnNumber
    error_id = $_.ErrorId
  }})
}
$result | ConvertTo-Json -Depth 5 -Compress
"""
        try:
            completed = subprocess.run(
                [executable, "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", parser_script],
                input=code,
                text=True,
                capture_output=True,
                timeout=10,
                check=False,
            )
            if completed.returncode != 0:
                return {"status": "parser_failed", "backend": "powershell_ast", "error": completed.stderr[-1000:]}
            value = json.loads(completed.stdout)
            return value if isinstance(value, dict) else None
        except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
            return None


class KnowledgeBuilder:
    def __init__(self, processor: TextProcessor, governance_path: str | Path, config: dict[str, Any] | None = None) -> None:
        config = config or {}
        self.processor = processor
        self.config = config
        self.segmenter = LosslessSegmenter(int(config.get("max_segment_chars", DEFAULT_SEGMENT_CHARS)))
        self.code = CodeExtractor()
        self.discussion_reconstructor = DiscussionKnowledgeReconstructor(
            max_units=int(config.get("max_knowledge_units", 2000)),
            max_conflicts=int(config.get("max_knowledge_conflicts", 500)),
        )
        self.code_reconstructor = CodeDiscussionReconstructor(
            max_families=int(config.get("max_code_families", 500)),
        )
        self.function_classifier = FunctionClassifier()
        self.code_restorer = CodeRestorer()
        self.context_reconstructor = ContextReconstructor()
        self.template_reconstructor = StandardTemplateReconstructor()
        self.layout_analyzer = MarkdownLayoutAnalyzer()
        self.provider_registry = LocalProviderRegistry()
        self.instruction_reconstructor = InstructionReconstructor()
        self.tables = TextTableExtractor(
            enabled=bool(config.get("extract_structured_tables", True)),
            max_columns=int(config.get("max_table_columns", 24)),
            max_tables=int(config.get("max_structured_tables", 500)),
        )
        self.topics = CPUHierarchicalTopicOrganizer(
            processor,
            threshold=float(config.get("topic_threshold", 0.18)),
            merge_threshold=float(config.get("topic_merge_threshold", 0.31)),
            max_topics=int(config.get("max_topics", 40)),
            max_features=int(config.get("max_features_per_segment", 96)),
            max_keywords=int(config.get("max_topic_keywords", 12)),
            anchor_boost=float(config.get("anchor_boost", 0.28)),
            anchor_conflict_penalty=float(config.get("anchor_conflict_penalty", 0.22)),
        )
        self.governance = json.loads(Path(governance_path).read_text(encoding="utf-8"))

    def reorganize(self, text: str) -> dict[str, Any]:
        segmentation = self.segmenter.segment(text)
        segments = segmentation["segments"]
        refinement_ledger = build_refinement_ledger(self.processor, segments)
        topics = self.topics.organize(segments)
        dialogue_flow = build_dialogue_flow(topics, segments)
        extracted_code_blocks = self.code.extract(text, segments)
        code_reconstruction = self.code_reconstructor.build(extracted_code_blocks)
        code_blocks = code_reconstruction["code_blocks"]
        function_classification = self.function_classifier.build(code_reconstruction)
        code_restoration = self.code_restorer.build(code_reconstruction, function_classification)
        structured_tables = self.tables.extract(segments)
        knowledge_registry = self.discussion_reconstructor.build(segments, refinement_ledger, topics)
        instruction_registry = self.instruction_reconstructor.build(
            segments,
            refinement_ledger,
            code_blocks,
            text,
        )
        context_reconstruction = self.context_reconstructor.build(
            segments,
            refinement_ledger,
            topics,
            dialogue_flow,
            code_blocks,
            instruction_registry,
            knowledge_registry["conflict_register"],
        )
        template_reconstruction = self.template_reconstructor.build(text, context_reconstruction)
        layout_analysis = self.layout_analyzer.build(text, segments, refinement_ledger)
        local_provider_registry = self.provider_registry.status()
        bilingual_knowledge_body = build_bilingual_knowledge_body(
            text,
            topics,
            knowledge_registry,
            instruction_registry,
            code_reconstruction,
        )
        ssot = self._ssot(segments, topics)
        via_keywords = self._via_keywords(text)
        organized_sections = self._organized_sections(topics, segments, refinement_ledger, structured_tables)
        mind_map = self._mind_map(
            text,
            topics,
            segments,
            refinement_ledger,
            organized_sections,
            dialogue_flow,
            code_blocks,
            via_keywords,
            structured_tables,
            knowledge_registry,
            code_reconstruction,
            instruction_registry,
        )
        mind_map = decorate_mind_map(mind_map, text)
        mind_map = enrich_mind_map_v15(
            mind_map,
            context_reconstruction,
            function_classification,
            template_reconstruction,
            layout_analysis,
            max_edges=int(self.config.get("max_ai_graph_edges", MAX_AI_GRAPH_EDGES)),
        )
        mind_map_evolution = build_mind_map_evolution(
            mind_map,
            conflict_register=knowledge_registry["conflict_register"],
        )
        code_blueprint = self._code_blueprint(code_blocks)
        summary = self.processor.summarize(text, max_points=4)
        fact_gate_failures = sum(
            item.get("fact_integrity", {}).get("status") != "pass" for item in refinement_ledger
        )
        unresolved_topics = sum(item.get("semantic_status") != "resolved" for item in topics)
        segmentation["completeness"].update(
            {
                "refined_segment_coverage": len(refinement_ledger) / max(1, len(segments)),
                "organized_segment_coverage": len({segment_id for topic in topics for segment_id in topic["segment_ids"]}) / max(1, len(segments)),
                "fact_integrity_candidate_pass_ratio": (len(refinement_ledger) - fact_gate_failures) / max(1, len(refinement_ledger)),
                "fact_integrity_output_pass_ratio": 1.0,
            }
        )
        return {
            "body_of_knowledge": {
                "title": self._title(text),
                "executive_summary": summary["summary"],
                "key_points": summary["key_points"],
                "topics": topics,
                "organized_sections": organized_sections,
                "structured_tables": structured_tables,
                "knowledge_registers": knowledge_registry["registers"],
                "source_segment_count": len(segments),
            },
            "mind_map": mind_map,
            "mind_map_evolution": mind_map_evolution,
            "dialogue_flow": dialogue_flow,
            "ssot_dictionary": ssot,
            "via_keywords": via_keywords,
            "code_registry": code_blocks,
            "code_reconstruction_package": code_reconstruction,
            "function_classification": function_classification,
            "code_restoration": code_restoration,
            "code_integration_blueprint": code_blueprint,
            "context_reconstruction": context_reconstruction,
            "template_reconstruction": template_reconstruction,
            "layout_analysis": layout_analysis,
            "local_provider_registry": local_provider_registry,
            "knowledge_object_registry": knowledge_registry,
            "instruction_reconstruction": instruction_registry,
            "bilingual_knowledge_body": bilingual_knowledge_body,
            "source_ledger": segments,
            "refinement_ledger": refinement_ledger,
            "completeness": segmentation["completeness"],
            "quality_gates": {
                "source_reconstruction": "pass" if segmentation["completeness"]["exact_reconstruction"] else "fail",
                "fact_integrity": "pass" if fact_gate_failures == 0 else "pass_with_source_fallback",
                "fact_integrity_fallbacks": fact_gate_failures,
                "unresolved_topic_buckets": unresolved_topics,
                "structured_tables": len(structured_tables),
                "knowledge_units": knowledge_registry["statistics"]["unique_units"],
                "knowledge_conflicts": len(knowledge_registry["conflict_register"]),
                "knowledge_silent_conflict_resolution": False,
                "instructions": instruction_registry["statistics"]["instruction_count"],
                "commands": instruction_registry["statistics"]["command_count"],
                "command_execution_authorized": False,
                "bilingual_structural_labels": "pass",
                "mind_map_dynamic_corrections_applied_silently": False,
                "code_families": len(code_reconstruction["families"]),
                "classified_functions": function_classification["statistics"]["functions"],
                "code_module_templates": code_restoration["statistics"]["module_templates"],
                "context_threads": context_reconstruction["statistics"]["topic_threads"],
                "template_missing_required_slots": len(template_reconstruction["missing_required_slots"]),
                "layout_exact_reconstruction": layout_analysis["completeness"]["exact_reconstruction"],
                "local_provider_groups": local_provider_registry["provider_group_count"],
                "automatic_code_merge": False,
                "silent_table_fill": False,
                "automatic_threshold_promotion": False,
            },
            "reorganization_policy": {
                "content_deletion": "forbidden",
                "source_text_mutation": "none",
                "topic_order": "derived_index_only",
                "ssot_promotion": "candidate_requires_review",
                "refined_content": "derivative_with_source_hash",
                "knowledge_conflicts": "explicit_register_human_resolution_only",
                "instructions": "source_grounded_procedure_proposal_never_auto_execute",
                "bilingual_projection": "verified_glossary_or_source_preserved_with_review_flag",
                "mind_map_evolution": "append_only_snapshot_delta_human_approval_for_corrections",
                "code_revisions": "family_candidates_never_auto_merge",
                "context_reconstruction": "chronology_preserved_reply_links_are_reviewable_candidates",
                "standard_template": "source_filled_derivative_never_replaces_source_ledger",
                "markdown_layout": "all_characters_classified_no_layout_writeback",
                "local_providers": "read_only_detection_explicit_activation_no_auto_install",
                "deep_semantics": "optional_local_model_only",
            },
        }

    def _organized_sections(
        self,
        topics: list[dict[str, Any]],
        segments: list[dict[str, Any]],
        refinement_ledger: list[dict[str, Any]],
        structured_tables: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        segment_map = {item["segment_id"]: item for item in segments}
        refined_map = {item["segment_id"]: item for item in refinement_ledger}
        tables_by_segment: dict[str, list[dict[str, Any]]] = {}
        for table in structured_tables:
            tables_by_segment.setdefault(table["source_segment"], []).append(table)
        sections: list[dict[str, Any]] = []
        for topic in topics:
            members = [segment_map[segment_id] for segment_id in topic["segment_ids"]]
            original = "".join(item["text"] for item in members)
            optimized_parts = [refined_map[item["segment_id"]]["optimized_text"] for item in members]
            optimized = "\n\n".join(part for part in optimized_parts if part)
            lane_items: dict[str, list[dict[str, Any]]] = {}
            for member in members:
                refined = refined_map[member["segment_id"]]
                for unit in refined["semantic_units"] or [refined["optimized_text"]]:
                    for role in infer_content_roles(unit, member["kind"]):
                        lane_items.setdefault(role, []).append({"text": unit, "source_segment": member["segment_id"]})
            topic_summary = self.processor.summarize(optimized, max_points=4)
            sections.append(
                {
                    "topic_id": topic["topic_id"],
                    "title": topic["title"],
                    "segment_ids": topic["segment_ids"],
                    "source_hashes": [item["sha256"] for item in members],
                    "original_content": original,
                    "optimized_view": optimized,
                    "topic_summary": topic_summary,
                    "knowledge_lanes": lane_items,
                    "structured_tables": [
                        table
                        for member in members
                        for table in tables_by_segment.get(member["segment_id"], [])
                    ],
                    "ai_context": {
                        "topic_id": topic["topic_id"],
                        "keywords": topic["keywords"],
                        "requirements": lane_items.get("requirement", []),
                        "decisions": lane_items.get("decision", []),
                        "questions": lane_items.get("question", []),
                        "issues": lane_items.get("issue", []),
                        "actions": lane_items.get("action", []),
                        "parameters": lane_items.get("parameter", []),
                        "source_segments": topic["segment_ids"],
                    },
                    "source_content_sha256": _sha256_text(original),
                    "optimized_content_sha256": _sha256_text(optimized),
                    "optimized_view_is_derivative": True,
                }
            )
        return sections

    @staticmethod
    def _code_blueprint(code_blocks: list[dict[str, Any]]) -> dict[str, Any]:
        parameters: dict[str, list[dict[str, Any]]] = {}
        modules: list[dict[str, Any]] = []
        symbol_owners: dict[str, list[str]] = {}
        for block in code_blocks:
            spec = block["engine_spec"]
            build_candidate = block.get("canonical_promotion") == "candidate_requires_review" or not block.get("family_id")
            if build_candidate:
                for function_name in spec["functions"]:
                    symbol_owners.setdefault(function_name, []).append(block["code_id"])
            modules.append(
                {
                    "module_id": block["code_id"],
                    "family_id": block.get("family_id"),
                    "revision": block.get("revision"),
                    "duplicate_of": block.get("duplicate_of"),
                    "build_candidate": build_candidate,
                    "language": block["language"],
                    "functions": spec["functions"],
                    "function_contracts": spec.get("function_contracts", []),
                    "classes": spec["classes"],
                    "imports": spec["imports"],
                    "external_dependencies": spec.get("dependencies", []),
                    "calls": spec.get("calls", []),
                    "syntax_status": block["syntax"]["status"],
                    "hydra_risks": block["hydra_risks"],
                    "source_segments": block["source_segments"],
                }
            )
            for name, value in spec["parameters"].items():
                parameters.setdefault(name, []).append({"value": value, "source_code_id": block["code_id"]})
        conflicts = []
        resolved_parameters: dict[str, Any] = {}
        for name, candidates in parameters.items():
            distinct = {json.dumps(item["value"], ensure_ascii=False, sort_keys=True, default=str) for item in candidates}
            if len(distinct) == 1:
                resolved_parameters[name] = candidates[0]["value"]
            else:
                conflicts.append({"parameter": name, "candidates": candidates, "resolution": "human_required"})
        dependency_map: dict[str, set[str]] = {
            module["module_id"]: set()
            for module in modules
            if module["build_candidate"]
        }
        dependency_edges: list[dict[str, Any]] = []
        for module in modules:
            if not module["build_candidate"]:
                continue
            for call in module["calls"]:
                short_name = str(call).split(".")[-1]
                owners = [owner for owner in symbol_owners.get(short_name, []) if owner != module["module_id"]]
                for owner in owners:
                    dependency_map[module["module_id"]].add(owner)
                    dependency_edges.append(
                        {
                            "from": owner,
                            "to": module["module_id"],
                            "relation": "must_precede",
                            "symbol": short_name,
                        }
                    )
        remaining = {name: set(values) for name, values in dependency_map.items()}
        topology: list[str] = []
        while remaining:
            ready = sorted(name for name, dependencies in remaining.items() if not dependencies)
            if not ready:
                break
            topology.extend(ready)
            for name in ready:
                remaining.pop(name)
            for dependencies in remaining.values():
                dependencies.difference_update(ready)
        cycles = sorted(remaining)
        duplicate_symbols = [
            {"symbol": symbol, "owners": owners, "resolution": "namespace_or_human_required"}
            for symbol, owners in sorted(symbol_owners.items())
            if len(owners) > 1
        ]
        return {
            "schema": "VIA_ENGINE_BLUEPRINT/3.0",
            "status": "review_required_before_generation_or_execution",
            "languages": sorted({item["language"] for item in code_blocks}),
            "modules": modules,
            "build_candidate_modules": [module["module_id"] for module in modules if module["build_candidate"]],
            "parameters": resolved_parameters,
            "parameter_conflicts": conflicts,
            "duplicate_symbols": duplicate_symbols,
            "dependency_graph": {
                "edges": dependency_edges,
                "topological_order": topology,
                "cycles": cycles,
                "topology_complete": len(topology) == len(dependency_map),
            },
            "interface_contracts": [
                {"module_id": module["module_id"], **contract}
                for module in modules
                if module["build_candidate"]
                for contract in module["function_contracts"]
            ],
            "build_stages": [
                {"stage": 1, "name": "syntax_and_hydra_gate", "automatic": True},
                {"stage": 2, "name": "ssot_parameter_resolution", "automatic": not bool(conflicts)},
                {"stage": 3, "name": "dependency_topology", "automatic": not bool(cycles)},
                {"stage": 4, "name": "sandbox_generation", "automatic": False},
                {"stage": 5, "name": "human_activation", "automatic": False},
            ],
            "proposed_entrypoint": "central_task_router",
            "source_order": [item["code_id"] for item in code_blocks],
            "candidate_source_order": [
                item["code_id"]
                for item in code_blocks
                if item.get("canonical_promotion") == "candidate_requires_review" or not item.get("family_id")
            ],
            "automatic_revision_merge": False,
            "execution_authorized": False,
        }

    def knowledge(self, text: str) -> dict[str, Any]:
        return self.reorganize(text)

    def govern(self, text: str) -> dict[str, Any]:
        knowledge = self.reorganize(text)
        code_blocks = knowledge["code_registry"]
        issues: list[dict[str, Any]] = []
        for block in code_blocks:
            if block["syntax"]["status"] == "invalid":
                issues.append(
                    {
                        "issue_id": f"ISSUE-{len(issues)+1:04d}",
                        "code_id": block["code_id"],
                        "category": "syntax",
                        "classification": "Parallel-Fixable" if block["language"] in {"python", "json"} else "Sequence-Dependent",
                        "hydra_risk": "medium",
                        "detail": block["syntax"],
                        "action": "proposal_only",
                    }
                )
            for risk in block["hydra_risks"]:
                issues.append(
                    {
                        "issue_id": f"ISSUE-{len(issues)+1:04d}",
                        "code_id": block["code_id"],
                        "category": risk,
                        "classification": "Sequence-Dependent",
                        "hydra_risk": "high",
                        "action": "isolate_and_require_human_approval",
                    }
                )
        parallel_count = sum(item["classification"] == "Parallel-Fixable" for item in issues)
        sequence_count = len(issues) - parallel_count
        rounds = [
            {"round": 1, "name": "Comprehensive Fix", "status": "analyzed", "parallel_fixable": parallel_count, "isolated_hydra": sum(item["hydra_risk"] == "high" for item in issues)},
            {"round": 2, "name": "Sequential Fix", "status": "plan_ready", "sequence_dependent": sequence_count, "auto_applied": 0},
            {"round": 3, "name": "Final Hardening", "status": "gated", "requires_sandbox_execution": bool(code_blocks), "activation": "not_authorized_from_text"},
        ]
        pipelines = []
        for item in self.governance["pipelines"]:
            status = "ready"
            if item["id"] in {"P1", "P5"} and code_blocks:
                status = "analysis_complete_execution_gated"
            pipelines.append({**item, "status": status})
        return {
            "governance_policy": self.governance,
            "rounds": rounds,
            "pipelines": pipelines,
            "issues": issues,
            "matrix": {
                "MODULE": {"segments": len(knowledge["source_ledger"]), "topics": len(knowledge["body_of_knowledge"]["topics"])},
                "ENGINE": {"code_blocks": len(code_blocks), "hydra_high": sum(item["hydra_risk"] == "high" for item in issues)},
                "FUNCTION-LIB": {"ssot_candidates": len(knowledge["ssot_dictionary"]["entries"]), "via_keywords": len(knowledge["via_keywords"])},
                "OTHERS": {"coverage_ratio": knowledge["completeness"]["coverage_ratio"], "exact_reconstruction": knowledge["completeness"]["exact_reconstruction"]},
            },
            "knowledge": knowledge,
        }

    def _title(self, text: str) -> str:
        for line in text.splitlines():
            cleaned = line.strip().lstrip("#").strip()
            if 2 <= len(cleaned) <= 160:
                return cleaned
        return "VIA Body of Knowledge"

    def _ssot(self, segments: list[dict[str, Any]], topics: list[dict[str, Any]]) -> dict[str, Any]:
        aliases: dict[str, set[str]] = {}
        canonical_sources: dict[str, set[str]] = {}
        for segment in segments:
            text = segment["text"]
            for match in PAIR_TERM_RE.finditer(text):
                left = SPACE_CLEAN(match.group("left"))
                right = SPACE_CLEAN(match.group("right"))
                canonical = right
                aliases.setdefault(canonical, set()).update({left, right})
                canonical_sources.setdefault(canonical, set()).add(segment["segment_id"])
            for acronym in ACRONYM_RE.findall(text):
                aliases.setdefault(acronym, set()).add(acronym)
                canonical_sources.setdefault(acronym, set()).add(segment["segment_id"])
        for topic in topics:
            for term in topic["keywords"]:
                canonical = term.upper() if term.isascii() and len(term) <= 12 else term
                aliases.setdefault(canonical, set()).add(term)
                canonical_sources.setdefault(canonical, set()).update(topic["segment_ids"][:20])

        entries = []
        for canonical in sorted(aliases, key=lambda value: (-len(canonical_sources.get(value, set())), value.lower()))[:MAX_SSOT_TERMS]:
            alias_values = sorted(aliases[canonical])
            entries.append(
                {
                    "canonical": canonical,
                    "aliases": alias_values,
                    "literal_regex": "(?:" + "|".join(re.escape(item) for item in sorted(alias_values, key=len, reverse=True)) + ")",
                    "source_segments": sorted(canonical_sources.get(canonical, set())),
                    "status": "candidate",
                    "promotion_gate": "human_review_required",
                }
            )
        alias_owner: dict[str, list[str]] = {}
        for entry in entries:
            for alias in entry["aliases"]:
                alias_owner.setdefault(alias.lower(), []).append(entry["canonical"])
        conflicts = [
            {"alias": alias, "canonical_candidates": owners}
            for alias, owners in alias_owner.items()
            if len(set(owners)) > 1
        ]
        return {"version": "candidate-1", "entries": entries, "conflicts": conflicts, "silent_promotion": False}

    def _via_keywords(self, text: str) -> list[dict[str, Any]]:
        extracted = self.processor.keywords(text, top_k=100)
        output: list[dict[str, Any]] = []
        lower = text.lower()
        seen: set[str] = set()
        for category, terms in KEYWORD_CATEGORIES.items():
            for term in sorted(terms):
                count = lower.count(term.lower())
                if count and term.lower() not in seen:
                    output.append({"keyword": term, "category": category, "count": count, "source": "via_seed"})
                    seen.add(term.lower())
        for item in extracted:
            if item["term"].lower() not in seen:
                output.append({"keyword": item["term"], "category": "discovered", "count": item["count"], "score": item["score"], "source": "document"})
                seen.add(item["term"].lower())
        return sorted(output, key=lambda item: (-int(item.get("count", 0)), str(item["keyword"]).lower()))[:150]

    def _mind_map(
        self,
        text: str,
        topics: list[dict[str, Any]],
        segments: list[dict[str, Any]],
        refinement_ledger: list[dict[str, Any]],
        organized_sections: list[dict[str, Any]],
        dialogue_flow: dict[str, Any],
        code_blocks: list[dict[str, Any]],
        via_keywords: list[dict[str, Any]],
        structured_tables: list[dict[str, Any]],
        knowledge_registry: dict[str, Any],
        code_reconstruction: dict[str, Any],
        instruction_registry: dict[str, Any],
    ) -> dict[str, Any]:
        refined_map = {item["segment_id"]: item for item in refinement_ledger}
        section_map = {item["topic_id"]: item for item in organized_sections}
        human_children = []
        for topic in topics:
            points = []
            for segment_id in topic["segment_ids"][:MAX_MINDMAP_TOPIC_POINTS]:
                refined = refined_map[segment_id]
                points.append(
                    {
                        "name": refined["optimized_text"][:200] or "(blank)",
                        "roles": refined["roles"],
                        "source_segment": segment_id,
                    }
                )
            lanes = section_map[topic["topic_id"]]["knowledge_lanes"]
            human_children.append(
                {
                    "id": topic["topic_id"],
                    "name": topic["title"],
                    "keywords": topic["keywords"],
                    "segment_ids": topic["segment_ids"],
                    "recurrence_count": topic["recurrence_count"],
                    "episodes": [
                        {
                            "id": episode["episode_id"],
                            "name": refined_map[episode["segment_ids"][0]]["optimized_text"][:160] or "(blank)",
                            "segment_ids": episode["segment_ids"],
                            "source_order": [episode["first_source_order"], episode["last_source_order"]],
                        }
                        for episode in topic["episodes"]
                    ],
                    "branches": [
                        {
                            "name": role,
                            "count": len(items),
                            "items": items[:MAX_MINDMAP_TOPIC_POINTS],
                        }
                        for role, items in sorted(lanes.items())
                    ],
                    "children": points,
                }
            )
        human_root = {
            "name": self._title(text),
            "children": human_children,
            "cross_references": {
                "code_ids": [item["code_id"] for item in code_blocks],
                "top_via_keywords": [item["keyword"] for item in via_keywords[:30]],
                "topic_returns": dialogue_flow["return_links"],
                "knowledge_register_counts": {
                    role: len(items) for role, items in knowledge_registry["registers"].items()
                },
                "code_family_ids": [item["family_id"] for item in code_reconstruction["families"]],
            },
        }

        nodes: list[dict[str, Any]] = [
            {
                "node_id": "ROOT",
                "node_type": "knowledge_root",
                "label": self._title(text),
                "source_segments": [item["segment_id"] for item in segments],
            }
        ]
        edges: list[dict[str, Any]] = []
        for topic in topics:
            nodes.append(
                {
                    "node_id": topic["topic_id"],
                    "node_type": "topic",
                    "label": topic["title"],
                    "keywords": topic["keywords"],
                    "source_segments": topic["segment_ids"],
                    "attributes": {"recurrence_count": topic["recurrence_count"], "speakers": topic["speakers"]},
                }
            )
            edges.append({"from": "ROOT", "to": topic["topic_id"], "relation": "contains_topic", "confidence": 1.0})
            for episode in topic["episodes"]:
                nodes.append(
                    {
                        "node_id": episode["episode_id"],
                        "node_type": "topic_episode",
                        "label": f"{topic['title']} · Episode {episode['episode_id'].rsplit('-', 1)[-1]}",
                        "source_segments": episode["segment_ids"],
                        "attributes": {
                            "first_source_order": episode["first_source_order"],
                            "last_source_order": episode["last_source_order"],
                        },
                    }
                )
                edges.append(
                    {
                        "from": topic["topic_id"],
                        "to": episode["episode_id"],
                        "relation": "contains_episode",
                        "confidence": 1.0,
                    }
                )
                for segment_id in episode["segment_ids"]:
                    edges.append(
                        {
                            "from": episode["episode_id"],
                            "to": segment_id,
                            "relation": "episode_grounded_by",
                            "confidence": 1.0,
                        }
                    )
        topic_for_segment = {segment_id: topic["topic_id"] for topic in topics for segment_id in topic["segment_ids"]}
        for segment in segments:
            refined = refined_map[segment["segment_id"]]
            nodes.append(
                {
                    "node_id": segment["segment_id"],
                    "node_type": "source_segment",
                    "label": refined["optimized_text"][:200] or "(blank)",
                    "roles": refined["roles"],
                    "keywords": refined["keywords"],
                    "source_segments": [segment["segment_id"]],
                    "source_sha256": segment["sha256"],
                }
            )
            edges.append(
                {
                    "from": topic_for_segment[segment["segment_id"]],
                    "to": segment["segment_id"],
                    "relation": "grounded_by",
                    "confidence": 1.0,
                }
            )
        for table in structured_tables:
            nodes.append(
                {
                    "node_id": table["table_id"],
                    "node_type": "structured_table",
                    "label": " · ".join(table["headers"])[:200],
                    "source_segments": [table["source_segment"]],
                    "attributes": {
                        "kind": table["kind"],
                        "confidence": table["confidence"],
                        "review_required": table["review_required"],
                    },
                }
            )
            edges.append(
                {
                    "from": table["source_segment"],
                    "to": table["table_id"],
                    "relation": "contains_structured_table",
                    "confidence": table["confidence"],
                }
            )
        for unit in knowledge_registry["knowledge_units"]:
            nodes.append(
                {
                    "node_id": unit["knowledge_id"],
                    "node_type": "knowledge_unit",
                    "label": unit["text"][:200],
                    "roles": unit["roles"],
                    "source_segments": unit["source_segments"],
                    "attributes": {
                        "status": unit["status"],
                        "occurrence_count": len(unit["occurrences"]),
                        "is_derivative": True,
                    },
                }
            )
            for segment_id in unit["source_segments"]:
                edges.append(
                    {
                        "from": segment_id,
                        "to": unit["knowledge_id"],
                        "relation": "supports_knowledge_unit",
                        "confidence": 1.0,
                    }
                )
        for conflict in knowledge_registry["conflict_register"]:
            nodes.append(
                {
                    "node_id": conflict["conflict_id"],
                    "node_type": "knowledge_conflict",
                    "label": conflict["parameter"],
                    "source_segments": sorted(
                        {
                            segment_id
                            for candidate in conflict["candidates"]
                            for segment_id in candidate["source_segments"]
                        }
                    ),
                    "attributes": {"status": conflict["status"], "resolution": conflict["resolution"]},
                }
            )
            for candidate in conflict["candidates"]:
                edges.append(
                    {
                        "from": candidate["knowledge_id"],
                        "to": conflict["conflict_id"],
                        "relation": "conflicting_candidate",
                        "confidence": 1.0,
                    }
                )
        for family in code_reconstruction["families"]:
            nodes.append(
                {
                    "node_id": family["family_id"],
                    "node_type": "code_family",
                    "label": family["signature"][:200],
                    "source_segments": sorted(
                        {
                            segment_id
                            for revision in family["revisions"]
                            for segment_id in revision["source_segments"]
                        }
                    ),
                    "attributes": {
                        "language": family["language"],
                        "revision_count": family["revision_count"],
                        "candidate_code_id": family["candidate_code_id"],
                        "candidate_applied": False,
                    },
                }
            )
            edges.append(
                {
                    "from": "ROOT",
                    "to": family["family_id"],
                    "relation": "contains_code_family",
                    "confidence": 1.0,
                }
            )
        for instruction in instruction_registry["instructions"]:
            nodes.append(
                {
                    "node_id": instruction["instruction_id"],
                    "node_type": "instruction",
                    "label": instruction["text"][:200],
                    "source_segments": instruction["source_segments"],
                    "attributes": {
                        "instruction_type": instruction["instruction_type"],
                        "confidence": instruction["confidence"],
                        "status": instruction["status"],
                        "execution_authorized": False,
                    },
                }
            )
            edges.append(
                {
                    "from": "ROOT",
                    "to": instruction["instruction_id"],
                    "relation": "contains_instruction",
                    "confidence": instruction["confidence"],
                }
            )
        for command in instruction_registry["command_units"]:
            nodes.append(
                {
                    "node_id": command["command_id"],
                    "node_type": "command",
                    "label": command["reconstructed_command"][:200],
                    "source_segments": command["source_segments"],
                    "attributes": {
                        "shell": command["shell"],
                        "confidence": command["confidence"],
                        "continuation_balanced": command["completeness"]["continuation_balanced"],
                        "execution_authorized": False,
                    },
                }
            )
            edges.append(
                {
                    "from": "ROOT",
                    "to": command["command_id"],
                    "relation": "contains_command",
                    "confidence": command["confidence"],
                }
            )
        for previous, current in zip(segments, segments[1:]):
            edges.append(
                {
                    "from": previous["segment_id"],
                    "to": current["segment_id"],
                    "relation": "source_next",
                    "confidence": 1.0,
                }
            )
        for transition in dialogue_flow["transitions"]:
            edges.append(
                {
                    "from": transition["from_topic"],
                    "to": transition["to_topic"],
                    "relation": "switches_to",
                    "weight": transition["count"],
                    "confidence": 1.0,
                }
            )
        for link in dialogue_flow["return_links"]:
            edges.append(
                {
                    "from": link["source_segment"],
                    "to": link["topic_id"],
                    "relation": "returns_to_topic",
                    "gap_segments": link["gap_segments"],
                    "confidence": 1.0,
                }
            )
        maximum_edges = int(self.config.get("max_ai_graph_edges", MAX_AI_GRAPH_EDGES))
        return {
            "format": "VIA_MIND_MAP_JSON/3.0",
            "root": human_root,
            "human_view": {"root": human_root},
            "ai_view": {
                "schema": "VIA_KNOWLEDGE_GRAPH/3.0",
                "nodes": nodes,
                "edges": edges[:maximum_edges],
                "edges_truncated": len(edges) > maximum_edges,
                "retrieval_contract": {
                    "lookup_key": "node_id",
                    "source_join_key": "source_segments",
                    "source_of_truth": "source_ledger",
                    "derivative_join_key": "refinement_ledger.segment_id",
                    "never_treat_derivative_as_source": True,
                },
                "semantic_enrichment": {"status": "cpu_sparse_only", "deep_model_loaded": False},
            },
        }

    def enrich_semantic_graph(
        self,
        knowledge: dict[str, Any],
        vectors: list[list[float]],
        threshold: float | None = None,
    ) -> dict[str, Any]:
        topics = knowledge["body_of_knowledge"]["topics"]
        if len(vectors) != len(topics):
            raise ValueError("semantic vector count must equal topic count")
        selected_threshold = float(threshold if threshold is not None else self.config.get("deep_similarity_threshold", 0.62))
        semantic_edges: list[dict[str, Any]] = []
        for left_index, left in enumerate(vectors):
            left_norm = math.sqrt(sum(float(value) ** 2 for value in left))
            for right_index in range(left_index + 1, len(vectors)):
                right = vectors[right_index]
                right_norm = math.sqrt(sum(float(value) ** 2 for value in right))
                score = sum(float(a) * float(b) for a, b in zip(left, right)) / (left_norm * right_norm) if left_norm and right_norm else 0.0
                if score >= selected_threshold:
                    semantic_edges.append(
                        {
                            "from": topics[left_index]["topic_id"],
                            "to": topics[right_index]["topic_id"],
                            "relation": "deep_semantic_related",
                            "confidence": round(score, 6),
                        }
                    )
        ai_view = knowledge["mind_map"]["ai_view"]
        ai_view["edges"].extend(semantic_edges)
        ai_view["semantic_enrichment"] = {
            "status": "completed",
            "deep_model_loaded": True,
            "topic_vectors": len(vectors),
            "relation_count": len(semantic_edges),
            "threshold": selected_threshold,
            "vectors_persisted": False,
        }
        return knowledge


def SPACE_CLEAN(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" -/／")
