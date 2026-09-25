"""Lossless dialogue segmentation, knowledge reconstruction and code governance."""

from __future__ import annotations

import ast
import hashlib
import json
import math
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .discourse import (
    CPUHierarchicalTopicOrganizer,
    build_dialogue_flow,
    build_refinement_ledger,
    infer_content_roles,
)
from .text_ops import TextProcessor


DEFAULT_SEGMENT_CHARS = 8000
MAX_SSOT_TERMS = 500
MAX_MINDMAP_TOPIC_POINTS = 8
MAX_AI_GRAPH_EDGES = 4000

STRONG_BOUNDARY_RE = re.compile(
    r"(?m)^(?=(?:\s*\d{1,2}:\d{2}\s+\S|\s*(?:User|Assistant|使用者|助理|Human|AI)\s*[:：]|\s*#{1,6}\s+|\s*[-=]{8,}\s*$))"
)
FENCED_CODE_RE = re.compile(r"(?ms)^```(?P<language>[^\n`]*)\n(?P<code>.*?)^```\s*$")
PAIR_TERM_RE = re.compile(r"(?P<left>[\u3400-\u9fff][\u3400-\u9fff·\-／/ ]{1,30})\s*[（(]\s*(?P<right>[A-Za-z][A-Za-z0-9 ._+&/\-]{1,50})\s*[）)]")
ACRONYM_RE = re.compile(r"(?<![A-Za-z0-9])(?:[A-Z][A-Z0-9]{1,10}|[A-Z]{2,8}(?:-[A-Z0-9]{1,8})+)(?![A-Za-z0-9])")
TIMESTAMP_RE = re.compile(r"^\s*(?P<time>\d{1,2}:\d{2})\s+(?P<speaker>[^\n]{1,80})")
HEADING_RE = re.compile(r"^\s*(?:#{1,6}\s+|(?:第?[一二三四五六七八九十\d]+[、.)．]|[一二三四五六七八九十]+、)\s*)")
UNFENCED_CODE_HINT_RE = re.compile(
    r"^\s*(?:from\s+\w+\s+import|import\s+\w+|def\s+\w+\s*\(|class\s+\w+|function\s+\w+\s*\(|const\s+\w+\s*=|let\s+\w+\s*=|param\s*\(|function\s+[A-Za-z][\w-]*\s*\{|\$[A-Za-z_]\w*\s*=|\{\s*\"[^\"]+\"\s*:)",
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
            if stripped.startswith("```"):
                kind = "code"
            elif timestamp_match:
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
                    timestamp=timestamp_match.group("time") if timestamp_match else None,
                    speaker=timestamp_match.group("speaker").strip() if timestamp_match else None,
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
        "py": "python", "python3": "python", "ps": "powershell", "ps1": "powershell", "shell": "bash",
        "sh": "bash", "js": "javascript", "ts": "typescript", "jsonc": "json", "": "unknown",
    }

    def extract(self, text: str, segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        blocks: list[dict[str, Any]] = []
        occupied: list[tuple[int, int]] = []
        for match in FENCED_CODE_RE.finditer(text):
            language = self._language(match.group("language").strip().split()[0] if match.group("language").strip() else "")
            blocks.append(self._build_block(len(blocks) + 1, language, match.group("code"), match.start(), match.end(), segments, "fenced"))
            occupied.append((match.start(), match.end()))

        line_records = list(self._line_records(text))
        candidate: list[tuple[int, int, str]] = []
        for start, end, line in line_records:
            if any(start >= left and start < right for left, right in occupied):
                if len(candidate) >= 3:
                    blocks.append(self._unfenced_block(candidate, blocks, segments))
                candidate = []
                continue
            if UNFENCED_CODE_HINT_RE.match(line) or (candidate and (line.startswith((" ", "\t")) or not line.strip())):
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
        return self._build_block(len(blocks) + 1, language, code, records[0][0], records[-1][1], segments, "heuristic")

    def _language(self, value: str) -> str:
        lower = value.lower()
        return self.LANGUAGE_ALIASES.get(lower, lower or "unknown")

    @staticmethod
    def _guess_language(code: str) -> str:
        if re.search(r"(?m)^\s*(?:def|class|from\s+\w+\s+import|import\s+\w+)", code):
            return "python"
        if re.search(r"(?mi)^\s*(?:param\s*\(|function\s+[\w-]+|\$\w+\s*=)", code):
            return "powershell"
        if re.search(r"(?m)^\s*(?:function|const|let|var)\s+", code):
            return "javascript"
        if code.lstrip().startswith(("{", "[")):
            return "json"
        return "unknown"

    def _build_block(
        self, index: int, language: str, code: str, start: int, end: int, segments: list[dict[str, Any]], extraction: str
    ) -> dict[str, Any]:
        syntax, engine_spec = self._inspect(language, code)
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
        self.topics = CPUHierarchicalTopicOrganizer(
            processor,
            threshold=float(config.get("topic_threshold", 0.18)),
            merge_threshold=float(config.get("topic_merge_threshold", 0.31)),
            max_topics=int(config.get("max_topics", 40)),
            max_features=int(config.get("max_features_per_segment", 96)),
            max_keywords=int(config.get("max_topic_keywords", 12)),
        )
        self.governance = json.loads(Path(governance_path).read_text(encoding="utf-8"))

    def reorganize(self, text: str) -> dict[str, Any]:
        segmentation = self.segmenter.segment(text)
        segments = segmentation["segments"]
        refinement_ledger = build_refinement_ledger(self.processor, segments)
        topics = self.topics.organize(segments)
        dialogue_flow = build_dialogue_flow(topics, segments)
        code_blocks = self.code.extract(text, segments)
        ssot = self._ssot(segments, topics)
        via_keywords = self._via_keywords(text)
        organized_sections = self._organized_sections(topics, segments, refinement_ledger)
        mind_map = self._mind_map(text, topics, segments, refinement_ledger, organized_sections, dialogue_flow, code_blocks, via_keywords)
        code_blueprint = self._code_blueprint(code_blocks)
        summary = self.processor.summarize(text, max_points=4)
        segmentation["completeness"].update(
            {
                "refined_segment_coverage": len(refinement_ledger) / max(1, len(segments)),
                "organized_segment_coverage": len({segment_id for topic in topics for segment_id in topic["segment_ids"]}) / max(1, len(segments)),
            }
        )
        return {
            "body_of_knowledge": {
                "title": self._title(text),
                "executive_summary": summary["summary"],
                "key_points": summary["key_points"],
                "topics": topics,
                "organized_sections": organized_sections,
                "source_segment_count": len(segments),
            },
            "mind_map": mind_map,
            "dialogue_flow": dialogue_flow,
            "ssot_dictionary": ssot,
            "via_keywords": via_keywords,
            "code_registry": code_blocks,
            "code_integration_blueprint": code_blueprint,
            "source_ledger": segments,
            "refinement_ledger": refinement_ledger,
            "completeness": segmentation["completeness"],
            "reorganization_policy": {
                "content_deletion": "forbidden",
                "source_text_mutation": "none",
                "topic_order": "derived_index_only",
                "ssot_promotion": "candidate_requires_review",
                "refined_content": "derivative_with_source_hash",
                "deep_semantics": "optional_local_model_only",
            },
        }

    def _organized_sections(
        self,
        topics: list[dict[str, Any]],
        segments: list[dict[str, Any]],
        refinement_ledger: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        segment_map = {item["segment_id"]: item for item in segments}
        refined_map = {item["segment_id"]: item for item in refinement_ledger}
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
            for function_name in spec["functions"]:
                symbol_owners.setdefault(function_name, []).append(block["code_id"])
            modules.append(
                {
                    "module_id": block["code_id"],
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
        dependency_map: dict[str, set[str]] = {module["module_id"]: set() for module in modules}
        dependency_edges: list[dict[str, Any]] = []
        for module in modules:
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
            "schema": "VIA_ENGINE_BLUEPRINT/2.0",
            "status": "review_required_before_generation_or_execution",
            "languages": sorted({item["language"] for item in code_blocks}),
            "modules": modules,
            "parameters": resolved_parameters,
            "parameter_conflicts": conflicts,
            "duplicate_symbols": duplicate_symbols,
            "dependency_graph": {
                "edges": dependency_edges,
                "topological_order": topology,
                "cycles": cycles,
                "topology_complete": len(topology) == len(modules),
            },
            "interface_contracts": [
                {"module_id": module["module_id"], **contract}
                for module in modules
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
            "format": "VIA_MIND_MAP_JSON/2.0",
            "root": human_root,
            "human_view": {"root": human_root},
            "ai_view": {
                "schema": "VIA_KNOWLEDGE_GRAPH/2.0",
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
