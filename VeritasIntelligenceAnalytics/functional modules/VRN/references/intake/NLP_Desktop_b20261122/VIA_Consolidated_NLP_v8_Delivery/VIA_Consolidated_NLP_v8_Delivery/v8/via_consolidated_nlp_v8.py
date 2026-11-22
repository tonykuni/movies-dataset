from __future__ import annotations

"""VIA Consolidated NLP v8.

One editable facade with seven cohesive modules. The modules are deliberately
kept in one file so a maintainer can edit one canonical surface while legacy
v5/v7 adapters remain behind stable compatibility functions. Source code is
parsed statically; it is never imported or executed.
"""

import ast
import hashlib
import json
import re
import sys
import threading
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
V7_DIR = ROOT / "nlp_v7_upgrade" / "unified"
if str(V7_DIR) not in sys.path:
    sys.path.insert(0, str(V7_DIR))

from via_nlp_unified_v7 import artifact_payloads as v7_artifact_payloads  # type: ignore
from via_nlp_unified_v7 import process_text as v7_process_text  # type: ignore

V8_SCHEMA = "VIA_CONSOLIDATED_NLP_RESULT/8.0"
V8_ENGINE_ID = "VIA-ENG-022"
V8_ENGINE_VERSION = "8.0.0"
V8_REGISTRY_ID = "VIA-SSOT-REG-000006"
MAX_TEXT_CHARS = 2_000_000


@dataclass(frozen=True)
class V8Policy:
    source_write: bool = False
    source_delete: bool = False
    code_execution: bool = False
    network: bool = False
    package_install: bool = False
    human_review_required: bool = True


@dataclass(frozen=True)
class ConsolidatedModule:
    module_id: str
    canonical_name: str
    name_zh: str
    responsibility: str
    legacy_aliases: tuple[str, ...]
    editable_surface: str


CONSOLIDATED_MODULES: tuple[ConsolidatedModule, ...] = (
    ConsolidatedModule(
        "VIA-MOD-001", "Input & Source Ledger", "輸入與來源帳本",
        "Read any supported input, preserve source text, calculate hashes and create deterministic source records.",
        ("VIA-ENG-001", "VIA-ENG-003", "VIA-ENG-013"), "source_ledger",
    ),
    ConsolidatedModule(
        "VIA-MOD-002", "Text & NLP Normalization", "文字與 NLP 正規化",
        "Protect tokens, repair spacing and punctuation, segment text, detect language and expose lexicon projections.",
        ("VIA-ENG-004", "VIA-ENG-018"), "text_nlp",
    ),
    ConsolidatedModule(
        "VIA-MOD-003", "Discussion & Instruction Reconstruction", "討論與指令重建",
        "Reconstruct topics, returns, speakers, questions, instructions, commands and proposal-only command convergence.",
        ("VIA-ENG-005", "VIA-ENG-019", "VIA-ENG-020"), "discussion_commands",
    ),
    ConsolidatedModule(
        "VIA-MOD-004", "Knowledge & Mind Map", "知識體與心智圖",
        "Build evidence-linked knowledge body, typed graph, bilingual projections and append-only Mind Map evolution.",
        ("VIA-ENG-007", "VIA-ENG-016", "VIA-ENG-021"), "knowledge_mindmap",
    ),
    ConsolidatedModule(
        "VIA-MOD-005", "AST & Code Module Intelligence", "AST 與程式模組理解",
        "Statically inventory Python AST, functions, classes, imports, parameters and module composition without execution.",
        ("VIA-ENG-006", "VIA-ENG-012", "VIA-ENG-015"), "ast_modules",
    ),
    ConsolidatedModule(
        "VIA-MOD-006", "Governance & Safe Export", "治理與安全輸出",
        "Apply source, evidence, conflict, execution and review gates, then emit reproducible artifacts.",
        ("VIA-ENG-008", "VIA-ENG-009", "VIA-ENG-017"), "governance",
    ),
    ConsolidatedModule(
        "VIA-MOD-007", "Acceleration & Runtime Fabric", "加速與執行基礎",
        "Provide bounded CPU execution, caching, deterministic serialization and runtime policy for all consolidated modules.",
        ("VIA-ENG-010", "VIA-ENG-011"), "runtime",
    ),
)

_POLICY = V8Policy()
V8_POLICY = _POLICY
_PROCESS_LOCK = threading.RLock()


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _clean(value: Any, limit: int = 240) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()[:limit]


def normalize_text(text: str) -> dict[str, Any]:
    """Create a reviewable normalization projection without mutating source."""
    protected = re.findall(r"(?:https?://\S+|\b[\w.-]+@[\w.-]+\.[A-Za-z]{2,}\b|--?[\w-]+(?:=\S+)?)", text)
    normalized = text.replace("\u00a0", " ")
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized).strip()
    return {
        "schema": "VIA_CONSOLIDATED_TEXT_PROJECTION/8.0",
        "source_sha256": _sha256(text),
        "normalized_sha256": _sha256(normalized),
        "source_characters": len(text),
        "normalized_characters": len(normalized),
        "protected_token_count": len(protected),
        "protected_tokens_preview": protected[:50],
        "source_preserved": True,
        "normalized_text": normalized,
    }


class _ASTInventory(ast.NodeVisitor):
    def __init__(self) -> None:
        self.imports: list[dict[str, Any]] = []
        self.functions: list[dict[str, Any]] = []
        self.classes: list[dict[str, Any]] = []
        self.assignments: list[dict[str, Any]] = []
        self.calls: list[dict[str, Any]] = []

    def visit_Import(self, node: ast.Import) -> Any:
        for alias in node.names:
            self.imports.append({"name": alias.name, "alias": alias.asname, "line": node.lineno})
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> Any:
        module = node.module or ""
        self.imports.append({"name": module, "symbols": [a.name for a in node.names], "line": node.lineno})
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        self.functions.append({
            "name": node.name,
            "line": node.lineno,
            "end_line": getattr(node, "end_lineno", node.lineno),
            "parameters": [arg.arg for arg in node.args.args],
            "decorators": [ast.unparse(item) for item in node.decorator_list],
            "async": False,
        })
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> Any:
        self.functions.append({
            "name": node.name,
            "line": node.lineno,
            "end_line": getattr(node, "end_lineno", node.lineno),
            "parameters": [arg.arg for arg in node.args.args],
            "decorators": [ast.unparse(item) for item in node.decorator_list],
            "async": True,
        })
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> Any:
        self.classes.append({
            "name": node.name,
            "line": node.lineno,
            "end_line": getattr(node, "end_lineno", node.lineno),
            "bases": [ast.unparse(item) for item in node.bases],
            "methods": [item.name for item in node.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))],
        })
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> Any:
        targets = [ast.unparse(item) for item in node.targets]
        self.assignments.append({"targets": targets, "value": _clean(ast.unparse(node.value), 180), "line": node.lineno})
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> Any:
        self.calls.append({"callee": _clean(ast.unparse(node.func), 120), "line": node.lineno})
        self.generic_visit(node)


def ast_inventory(source_name: str, text: str) -> dict[str, Any]:
    suffix = Path(source_name).suffix.lower()
    candidate = suffix in {".py", ".pyw", ".pyi"} or bool(re.search(r"\b(import|from)\s+[A-Za-z_]", text[:10000]))
    result: dict[str, Any] = {
        "schema": "VIA_CONSOLIDATED_AST_INVENTORY/8.0",
        "source_name": source_name,
        "source_sha256": _sha256(text),
        "analysis_mode": "python_ast" if candidate else "text_static_fallback",
        "parse_status": "not_applicable" if not candidate else "pending",
        "imports": [], "functions": [], "classes": [], "assignments": [], "calls": [],
        "risk_flags": [], "execution_authorized": False,
    }
    if not candidate:
        result["risk_flags"] = ["non_python_input_static_fallback"]
        return result
    try:
        tree = ast.parse(text, filename=source_name)
        visitor = _ASTInventory()
        visitor.visit(tree)
        result.update({
            "parse_status": "PASS",
            "imports": visitor.imports,
            "functions": visitor.functions,
            "classes": visitor.classes,
            "assignments": visitor.assignments,
            "calls": visitor.calls,
            "statistics": {
                "imports": len(visitor.imports), "functions": len(visitor.functions),
                "classes": len(visitor.classes), "assignments": len(visitor.assignments), "calls": len(visitor.calls),
            },
        })
    except SyntaxError as exc:
        result["parse_status"] = "PASS_WITH_REVIEW"
        result["risk_flags"] = ["syntax_error_or_fragment", _clean(exc.msg)]
    return result


def _quality(v7_result: dict[str, Any], ast_result: dict[str, Any], normalization: dict[str, Any]) -> dict[str, Any]:
    q = dict(v7_result.get("projection", {}).get("quality", {}))
    q.update({
        "v8_source_preserved": True,
        "v8_source_mutated": False,
        "ast_execution_authorized": False,
        "ast_parse_status": ast_result.get("parse_status"),
        "normalized_projection_available": True,
        "review_required": True,
        "policy": asdict(_POLICY),
    })
    return q


def process_text_v8(source_name: str, text: str, quality: str = "balanced") -> dict[str, Any]:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("text must be a non-empty string")
    if len(text) > MAX_TEXT_CHARS:
        raise ValueError(f"v8 maximum is {MAX_TEXT_CHARS} characters; split into reviewed bundles")
    with _PROCESS_LOCK:
        v7_result = v7_process_text(source_name, text, quality=quality)
        normalization = normalize_text(text)
        ast_result = ast_inventory(source_name, text)
    full_output = v7_result["full_output"]
    source = {
        "source_name": source_name,
        "source_sha256": _sha256(text),
        "source_characters": len(text),
        "source_is_immutable": True,
    }
    module_map = {module.module_id: asdict(module) for module in CONSOLIDATED_MODULES}
    projection = {
        "schema": V8_SCHEMA,
        "engine": {"engine_id": V8_ENGINE_ID, "engine_version": V8_ENGINE_VERSION, "base_engine": "VIA-ENG-021"},
        "registry_id": V8_REGISTRY_ID,
        "source": source,
        "canonical_modules": list(module_map),
        "legacy_engines_preserved": sorted({alias for module in CONSOLIDATED_MODULES for alias in module.legacy_aliases}),
        "quality": _quality(v7_result, ast_result, normalization),
        "compatibility": {
            "v5_outputs_preserved": True,
            "v7_outputs_preserved": True,
            "consolidated_edit_surface": True,
            "one_facade": True,
        },
    }
    return {
        "schema": V8_SCHEMA,
        "projection": projection,
        "source_ledger": {"source": source, "completeness": full_output.get("completeness", {})},
        "modules": module_map,
        "text_nlp": normalization,
        "discussion_commands": {
            "context_reconstruction": full_output.get("context_reconstruction", {}),
            "instruction_reconstruction": full_output.get("instruction_reconstruction", {}),
            "command_execution_authorized": False,
        },
        "knowledge_mindmap": {
            "body_of_knowledge": full_output.get("body_of_knowledge", {}),
            "mind_map": full_output.get("mind_map", {}),
            "mind_map_evolution": full_output.get("mind_map_evolution", {}),
        },
        "ast_modules": ast_result,
        "governance": {
            "quality_gates": full_output.get("quality_gates", {}),
            "policy": asdict(_POLICY),
            "review_required": True,
            "writeback_authorized": False,
        },
        "v7_compatibility": v7_result,
    }


def consolidated_mind_map_mermaid(result: dict[str, Any], max_modules: int = 7) -> str:
    lines = ["flowchart LR", '    ROOT["VIA Consolidated NLP v8"]']
    modules = list(result.get("modules", {}).values())[:max_modules]
    for index, module in enumerate(modules, 1):
        alias = f"M{index:03d}"
        label = re.sub(r'["\n\r]', " ", f"{module['module_id']} {module['name_zh']}")
        lines.append(f'    {alias}["{label}"]')
        lines.append(f"    ROOT --> {alias}")
    lines.extend([
        '    M001 --> M002', '    M002 --> M003', '    M003 --> M004',
        '    M004 --> M005', '    M005 --> M006', '    M006 --> M007',
        '    M006 --> OUT["MD / HTML / JSON / ZIP / Review Queue"]',
    ])
    return "\n".join(lines) + "\n"


def artifact_payloads_v8(result: dict[str, Any]) -> dict[str, Any]:
    v7 = result["v7_compatibility"]
    payloads = {
        "v8_unified.json": result,
        "v8_source_ledger.json": result["source_ledger"],
        "v8_text_nlp.json": result["text_nlp"],
        "v8_discussion_commands.json": result["discussion_commands"],
        "v8_knowledge_mindmap.json": result["knowledge_mindmap"],
        "v8_ast_modules.json": result["ast_modules"],
        "v8_governance.json": result["governance"],
        "v8_module_registry.json": {"registry_id": V8_REGISTRY_ID, "modules": result["modules"]},
        "v8_mind_map.mmd": consolidated_mind_map_mermaid(result),
    }
    for name, payload in v7_artifact_payloads(v7).items():
        payloads.setdefault(f"compat_{name}", payload)
    return payloads


def process_path_v8(path: str | Path, quality: str = "balanced") -> dict[str, Any]:
    selected = Path(path).expanduser().resolve(strict=True)
    if not selected.is_file():
        raise ValueError("input path must point to a regular file")
    suffix = selected.suffix.lower()
    if suffix == ".docx":
        from zipfile import ZipFile
        from xml.etree import ElementTree
        namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        with ZipFile(selected) as archive:
            root = ElementTree.fromstring(archive.read("word/document.xml"))
        text = "\n".join("".join(node.text or "" for node in paragraph.findall(".//w:t", namespace)).strip() for paragraph in root.findall(".//w:p", namespace))
    elif suffix == ".pdf":
        from pypdf import PdfReader
        text = "\n\n".join(page.extract_text() or "" for page in PdfReader(str(selected)).pages)
    else:
        text = selected.read_text(encoding="utf-8", errors="replace")
    return process_text_v8(selected.name, text, quality=quality)


__all__ = [
    "CONSOLIDATED_MODULES", "V8_ENGINE_ID", "V8_ENGINE_VERSION", "V8_POLICY", "V8_REGISTRY_ID",
    "ast_inventory", "artifact_payloads_v8", "normalize_text", "process_path_v8", "process_text_v8",
]
