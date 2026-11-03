#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VIA Agent OS — single-file, local-first, fail-closed implementation scaffold.

Python 3.10+; standard library only.

Safety contract:
- No network calls, shell/subprocess execution, dynamic imports, package installs,
  eval/exec of scanned source, agent spawning, or recursive skill execution.
- AST scanning is read-only. It creates a metadata overlay; it never rewrites source.
- Default commands are read-only/dry-run. SSOT writes require --apply.
- Existing SSOT fields and unknown data are preserved. A backup precedes writes.
- Token estimates are heuristic unless actual provider usage is supplied.
- The dashboard is a self-contained file:// HTML snapshot with no server/CDN/fetch.
- Metrics persistence is opt-in and stores counts/status only, never prompt content.
- VCGC and unseen chat-window code are NOT considered connected until an explicit,
  reviewed mount/adapter and local checkout are supplied.

This file is a safe, executable scaffold. It does not claim to reproduce unseen
legacy modules or to disable code in a VCGC checkout it cannot inspect.
"""
from __future__ import annotations

import argparse
import ast
import datetime as _dt
import hashlib
import html
import json
import math
import os
import re
import sys
import tempfile
import time
import unittest
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

APP_ID = "via-agent-os"
CONTRACT_VERSION = "1.0.0"
SSOT_SCHEMA = "VIA_SSOT/1.0"
MOUNT_CONTRACT = "VIA_MOUNT_MANIFEST/1.0"
MAX_SCAN_FILES = 1500
MAX_SOURCE_BYTES = 2 * 1024 * 1024
MAX_SYMBOLS_PER_FILE = 250
MAX_AST_NODES = 50000
MAX_AST_DEPTH = 200
MAX_QUERY_LINES = 400
MAX_CONTEXT_BYTES = 8 * 1024 * 1024
MAX_METRICS_BYTES = 16 * 1024 * 1024
MAX_METRIC_EVENTS = 10000
EXCLUDED_DIRS = {
    ".git", ".hg", ".svn", ".venv", "venv", "node_modules", "__pycache__",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", "dist", "build", ".tox",
    ".via", "secrets", "secret", "credentials", "private", "uploads",
}

# Never execute source code just because it parses or is listed in a mount.
EXPECTED_INTERFACES = (
    "process_file", "process_file_accelerated", "analyze_layout", "run_ocr",
    "integrate", "analyze_finance", "run_audit", "process", "execute", "run",
    "main", "health_check",
)


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key refused: {key}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant refused: {value}")


def strict_json_loads(text: str) -> Any:
    """Parse JSON while rejecting duplicate keys and NaN/Infinity values."""
    return json.loads(text, object_pairs_hook=_unique_json_object,
                      parse_constant=_reject_json_constant)


@dataclass(frozen=True)
class SkillSpec:
    id: str
    name: str
    version: str
    purpose: str
    trigger_when: tuple[str, ...]
    required_inputs: tuple[str, ...]
    optional_inputs: tuple[str, ...]
    process: tuple[str, ...]
    outputs: tuple[str, ...]
    success_criteria: tuple[str, ...]
    memory_write: tuple[str, ...]
    memory_read: tuple[str, ...]
    routing: str
    constraints: tuple[str, ...]
    examples: tuple[str, ...]

    def as_contract(self) -> dict[str, Any]:
        data = asdict(self)
        for key, value in list(data.items()):
            if isinstance(value, tuple):
                data[key] = list(value)
        data["contract_version"] = CONTRACT_VERSION
        data["implementation_status"] = "DETERMINISTIC_SCAFFOLD"
        return data


SKILLS: tuple[SkillSpec, ...] = (
    SkillSpec(
        "via-planner", "VIA Planner", "1.0.0",
        "拆解目標與限制，產生有依賴、驗收和風險的可執行計畫。",
        ("new feature", "new project", "roadmap planning"), ("objective",),
        ("budget", "deadline", "constraints", "requested_tasks"),
        ("define_goal", "identify_components", "create_epics", "generate_tasks", "define_dependencies", "record_risks"),
        ("roadmap", "risks", "assumptions", "open_questions"),
        ("每項工作可執行且有驗收條件", "依賴與未知事項明確標示"),
        ("project_roadmap",), ("architecture_decisions", "project_context"),
        "local deterministic planner; optional external model adapter is not enabled",
        ("規劃模式不改寫來源碼", "缺少資訊時列出問題，不假裝已知"),
        ("以 objective、deadline、constraints 產生 Epic/Task/Subtask",),
    ),
    SkillSpec(
        "via-architect", "VIA Architect", "1.0.0",
        "定義模組邊界、介面、相依方向，並檢查循環依賴。",
        ("new module", "architecture change", "integration request"), ("requirements",),
        ("modules", "technology_stack", "graph_index"),
        ("identify_domains", "define_boundaries", "design_interfaces", "check_dependencies"),
        ("architecture", "dependency_order", "cycles", "missing_dependencies"),
        ("每個模組有穩定 ID", "循環與未知相依明確回報"),
        ("architecture_decisions",), ("graphify_report", "architecture_decisions"),
        "local static contract analysis",
        ("不執行模組", "不自行安裝相依", "不把 AST 推論當執行時事實"),
        ("提供 modules=[{id, depends_on}] 取得拓樸與循環檢查",),
    ),
    SkillSpec(
        "via-decision-log", "VIA Decision Log", "1.0.0",
        "形成可追溯 ADR，保存決策、理由、替代方案和影響。",
        ("architecture decision", "strategy decision", "framework selection"),
        ("decision", "rationale"), ("alternatives", "impact", "date", "owner"),
        ("capture", "classify", "validate", "assign_stable_id"),
        ("adr",), ("決策可重現且記錄日期、理由及影響"),
        ("adr",), ("adr", "project_context"), "local deterministic formatter",
        ("此函式只產生記錄草稿；SSOT 寫入須由 register --apply 執行"),
        ("輸入 decision/rationale，輸出 ADR-日期-雜湊 ID",),
    ),
    SkillSpec(
        "via-factor-builder", "VIA Factor Builder", "1.0.0",
        "將可檢驗假說整理成可測量的因子定義。",
        ("new factor", "alpha research"), ("hypothesis",),
        ("name", "category", "dataset", "market", "signal", "formula", "regime", "failure_case"),
        ("define_signal", "define_formula", "define_regime", "define_failure_case"),
        ("factor",), ("假說可量測、可測試、可重現"),
        ("factor_library",), ("factor_library", "project_context"), "local deterministic contract builder",
        ("不提供投資建議", "不執行使用者公式", "資料與公式由使用者提供"),
        ("提供 hypothesis、signal、formula，輸出 factor contract",),
    ),
    SkillSpec(
        "via-factor-validator", "VIA Factor Validator", "1.0.0",
        "檢查因子驗證所需證據、偏誤、流動性、成本及樣本資訊。",
        ("factor completed", "backtest result available"), ("factor", "evidence"),
        ("minimum_observations", "acceptance_policy"),
        ("check_sample", "check_lookahead", "check_survivorship", "check_liquidity", "check_costs", "check_out_of_sample"),
        ("validation", "missing_evidence", "risks", "review_status"),
        ("不得在證據缺失時標為 PASS", "限制與資料版本可追溯"),
        ("factor_validation",), ("factor_library", "data_provenance"), "local evidence checklist; no statistical claim without data",
        ("不執行回測", "不推導未提供的統計量", "不得把缺失值當零"),
        ("提供 factor 與 evidence，輸出缺項及審查狀態",),
    ),
    SkillSpec(
        "via-strategy-builder", "VIA Strategy Builder", "1.0.0",
        "將已驗證因子整理為可回測策略規格。",
        ("validated factor", "strategy design"), ("factor_list",),
        ("entry", "exit", "stop", "position", "risk_limits", "cost_assumptions"),
        ("rank_factors", "combine_factors", "define_entry", "define_exit", "define_risk"),
        ("strategy", "missing_fields", "backtest_requirements"),
        ("進出場、停損、部位與成本假設完整"), ("strategy_library",),
        ("factor_library", "factor_validation"), "local deterministic schema validator",
        ("不下單", "不提供個人化投資建議", "不推定缺失的風險參數"),
        ("提供 factor_list 與 entry/exit/stop/position",),
    ),
    SkillSpec(
        "via-code-review", "VIA Code Review", "1.0.0",
        "以唯讀 AST 檢查定位疑慮並分類 Delete/Refactor/Keep。",
        ("pull request", "major edit", "module scan"), ("source_code",),
        ("relative_path", "expected_interfaces"),
        ("parse_ast", "index_symbols", "detect_risky_patterns", "classify_findings"),
        ("findings", "ast_index", "compile_status"),
        ("掃描不執行程式碼", "所有建議均有位置且不自動修改"),
        ("code_patterns",), ("architecture_decisions", "graphify_report"), "local static AST analyzer",
        ("不呼叫 eval/exec/import", "不自動刪改來源碼", "靜態規則可能有誤報"),
        ("提供 source_code，回報 AST 定位及安全提示",),
    ),
    SkillSpec(
        "via-memory-manager", "VIA Memory Manager", "1.0.0",
        "分類、評分、去重與核准記憶候選，避免短期噪音污染。",
        ("session end", "major decision", "factor update"), ("memory_candidate",),
        ("existing_fingerprints", "threshold", "approved"),
        ("classify", "score_importance", "detect_secrets", "deduplicate", "approve_or_reject"),
        ("memory_action", "fingerprint", "reason"),
        ("重複與暫存記錄不寫入", "保存需要明確核准"),
        ("memory_index",), ("all_scoped_memory",), "local deterministic policy; no external storage",
        ("預設只產生候選不落盤", "拒絕憑證、debug log、安裝歷史"),
        ("candidate={content,kind,importance,scope,approved}",),
    ),
)
SKILL_BY_ID = {s.id: s for s in SKILLS}


# Common credential patterns are intentionally conservative. They are a safety
# filter, not a complete secret scanner; users must never paste credentials.
SECRET_PATTERNS = (
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{12,}"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r'''(?i)(?P<prefix>"(?:api[_-]?key|access[_-]?token|refresh[_-]?token|password|client[_-]?secret|authorization|token)"\s*:\s*)"(?P<value>(?:\\.|[^"\\])*)"'''),
    re.compile(r'''(?i)(?P<prefix>(?<!["\w])(?:api[_-]?key|access[_-]?token|refresh[_-]?token|password|client[_-]?secret|authorization)\s*[:=]\s*)(?:(?P<dq>"(?:\\.|[^"\\])*"?)|(?P<sq>'(?:\\.|[^'\\])*'?)|(?P<bare>[^\s,'";}]+))'''),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)


def redact_secrets(text: str) -> tuple[str, int]:
    """Redact common credential forms in-memory; does not persist raw text."""
    result = text
    count = 0
    for index, pattern in enumerate(SECRET_PATTERNS):
        if index == 2:  # JSON string field; preserve JSON quotes and structure.
            result, n = pattern.subn(lambda m: m.group("prefix") + '"[REDACTED]"', result)
        elif index == 3:  # YAML/env-style key assignment.
            def replace_assignment(match: re.Match[str]) -> str:
                prefix = match.group("prefix")
                if match.group("dq") is not None:
                    quote = '"' if match.group("dq").startswith('"') else ""
                    close = '"' if match.group("dq").endswith('"') else ""
                    return prefix + quote + "[REDACTED]" + close
                if match.group("sq") is not None:
                    quote = "'" if match.group("sq").startswith("'") else ""
                    close = "'" if match.group("sq").endswith("'") else ""
                    return prefix + quote + "[REDACTED]" + close
                return prefix + "[REDACTED]"
            result, n = pattern.subn(replace_assignment, result)
        else:
            result, n = pattern.subn("[REDACTED]", result)
        count += n
    return result, count


def estimate_tokens(text: str) -> int:
    """Heuristic only: CJK code points and other text use rough separate ratios.

    Use model/provider-reported usage for billing-grade numbers. Tokenizers differ
    by model, Unicode normalization and message framing; this estimate is not an
    invoice and is intentionally labelled approximate.
    """
    cjk = 0
    other = 0
    for ch in text:
        code = ord(ch)
        if (0x3400 <= code <= 0x9FFF or 0xF900 <= code <= 0xFAFF or
                0x3040 <= code <= 0x30FF or 0xAC00 <= code <= 0xD7AF):
            cjk += 1
        else:
            other += 1
    return int(math.ceil(cjk * 1.5 + other / 4.0)) if text else 0


def stable_hash(text: str, length: int = 12) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:length]


@dataclass
class ContextResult:
    prepared_text: str
    source_hash: str
    mode: str
    lossy: bool
    redacted_count: int
    chars_before: int
    chars_after: int
    tokens_before_est: int
    tokens_after_est: int
    estimated_savings_percent: float
    note: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class TokenEngine:
    """Single active replacement engine; no legacy compressor is auto-loaded."""
    engine_id = "via-token-engine"
    policy = "EXCLUSIVE_REPLACEMENT"

    def __init__(self) -> None:
        self._usage_records: list[dict[str, Any]] = []

    def prepare(self, text: str, *, allow_lossy: bool = False,
                query: str | None = None, max_lines: int = 120) -> ContextResult:
        if not isinstance(text, str):
            raise TypeError("TokenEngine.prepare expects text str")
        redacted, redacted_count = redact_secrets(text)
        prepared = redacted
        mode = "passthrough"
        lossy = False
        note = "原文保留；只遮罩已辨識的常見憑證。未保證抓到所有秘密。"

        # Deterministic JSON whitespace compaction. Preserve array order and keys,
        # verify semantic round-trip, and keep original when invalid/not smaller.
        try:
            parsed = strict_json_loads(redacted)
            compact = json.dumps(parsed, ensure_ascii=False, separators=(",", ":"))
            if strict_json_loads(compact) == parsed and len(compact) < len(redacted):
                prepared, mode = compact, "json_lossless_semantic_compact"
                note = "JSON 語義 round-trip 通過；保留原始來源雜湊。"
        except (json.JSONDecodeError, TypeError, ValueError):
            pass

        # Selective text extraction is explicitly lossy and opt-in. It keeps line
        # numbers as provenance; source text is not saved by this engine.
        if allow_lossy and query and mode == "passthrough":
            lines = redacted.splitlines()
            terms = [x.lower() for x in re.findall(r"[\w\u3400-\u9fff]+", query) if len(x) > 1]
            try:
                max_lines = int(max_lines)
            except (TypeError, ValueError):
                max_lines = 120
            max_lines = max(1, min(max_lines, MAX_QUERY_LINES))
            if terms and len(lines) > max_lines:
                selected: set[int] = set()
                for i, line in enumerate(lines):
                    lowered = line.lower()
                    if any(term in lowered for term in terms):
                        selected.update(range(max(0, i - 1), min(len(lines), i + 2)))
                if selected:
                    ranked = sorted(selected)
                    if len(ranked) > max_lines:
                        ranked = ranked[:max_lines]
                    prepared = "\n".join(f"[L{i + 1}] {lines[i]}" for i in ranked)
                    mode, lossy = "query_line_extraction", True
                    note = "有損抽取已明確啟用；行號供回查，必須保留原始來源於呼叫端。"

        before_chars, after_chars = len(redacted), len(prepared)
        before_tokens, after_tokens = estimate_tokens(redacted), estimate_tokens(prepared)
        savings = (100.0 * (before_tokens - after_tokens) / before_tokens) if before_tokens else 0.0
        return ContextResult(
            prepared_text=prepared, source_hash=stable_hash(redacted, 64), mode=mode,
            lossy=lossy, redacted_count=redacted_count,
            chars_before=before_chars, chars_after=after_chars,
            tokens_before_est=before_tokens, tokens_after_est=after_tokens,
            estimated_savings_percent=round(max(-100.0, savings), 2), note=note,
        )

    def record_provider_usage(self, *, provider: str, model: str,
                              prompt_tokens: int, completion_tokens: int,
                              request_id: str = "") -> dict[str, Any]:
        """Record caller-supplied provider usage; this method makes no API call."""
        if min(prompt_tokens, completion_tokens) < 0:
            raise ValueError("usage token counts must be non-negative")
        record = {
            "provider": provider, "model": model,
            "prompt_tokens": int(prompt_tokens),
            "completion_tokens": int(completion_tokens),
            "total_tokens": int(prompt_tokens + completion_tokens),
            "request_id_hash": stable_hash(request_id) if request_id else "",
            "measured_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
            "source": "provider_reported",
        }
        self._usage_records.append(record)
        return record


# ---------- AST: read-only locator / classifier / numbering overlay ----------


def _slug(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return value[:48] or "module"


def classify_module_path(relative_path: str) -> str:
    parts = {p.lower() for p in Path(relative_path).parts}
    text = relative_path.lower()
    if "test" in parts or "tests" in parts or Path(relative_path).name.startswith("test_"):
        return "test"
    if any(x in text for x in ("token", "compress", "context")):
        return "token"
    if "memory" in text or "agentmemory" in text:
        return "memory"
    if "graph" in text or "ast" in text:
        return "code-intelligence"
    if "skill" in text or "agent" in text:
        return "skill-orchestration"
    if "route" in text or "gateway" in text:
        return "routing"
    if any(x in text for x in ("mount", "integration", "adapter", "vcgc")):
        return "integration"
    if any(x in text for x in ("ssot", "registry", "governance")):
        return "governance"
    return "general"


def _function_complexity(node: ast.AST) -> int:
    branches = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.With,
                ast.AsyncWith, ast.BoolOp, ast.IfExp, ast.Match)
    count = 1
    stack = list(getattr(node, "body", []))
    while stack:
        child = stack.pop()
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if isinstance(child, branches):
            count += 1
        stack.extend(ast.iter_child_nodes(child))
    return count


class _SymbolVisitor(ast.NodeVisitor):
    def __init__(self, rel: str) -> None:
        self.rel = rel
        self.scope: list[str] = []
        self.symbols: list[dict[str, Any]] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        qual = ".".join(self.scope + [node.name])
        self.symbols.append({
            "kind": "class", "name": node.name, "qualname": qual,
            "line": node.lineno, "end_line": getattr(node, "end_lineno", node.lineno),
            "stable_id": "VIA-CLS-" + stable_hash(self.rel + "::" + qual, 10).upper(),
        })
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node, "function")

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node, "async_function")

    def _visit_function(self, node: ast.AST, kind: str) -> None:
        name = getattr(node, "name", "unknown")
        qual = ".".join(self.scope + [name])
        self.symbols.append({
            "kind": kind, "name": name, "qualname": qual,
            "line": getattr(node, "lineno", 0),
            "end_line": getattr(node, "end_lineno", getattr(node, "lineno", 0)),
            "complexity_hint": _function_complexity(node),
            "stable_id": "VIA-FN-" + stable_hash(self.rel + "::" + qual, 10).upper(),
        })
        self.scope.append(name)
        self.generic_visit(node)
        self.scope.pop()


def _unsafe_call_findings(tree: ast.AST, relative_path: str) -> list[dict[str, Any]]:
    risks: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        dotted = []
        cur: ast.AST = node.func
        while isinstance(cur, ast.Attribute):
            dotted.append(cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name):
            dotted.append(cur.id)
        name = ".".join(reversed(dotted))
        severity = None
        if name in {"eval", "exec", "compile", "__import__"}:
            severity = "REVIEW_DYNAMIC_CODE"
        elif name in {"os.system", "subprocess.Popen", "subprocess.run", "subprocess.call"}:
            severity = "REVIEW_PROCESS_EXECUTION"
        elif name in {"pickle.loads", "marshal.loads"}:
            severity = "REVIEW_UNTRUSTED_DESERIALIZATION"
        if severity:
            risks.append({
                "classification": "REFACTOR", "severity": severity,
                "path": relative_path, "line": getattr(node, "lineno", 0),
                "symbol": name, "auto_fix": False,
                "note": "Static warning only; verify call context manually. No code was executed or changed.",
            })
    return risks


def scan_source(source: str, relative_path: str = "module.py") -> dict[str, Any]:
    """Parse/compile source without importing or executing it."""
    rel = Path(relative_path).as_posix()
    category = classify_module_path(rel)
    digest = stable_hash(rel, 10).upper()
    result: dict[str, Any] = {
        "module_id": f"VIA-MOD-{category.upper()}-{digest}",
        "module_number": None,
        "category": category,
        "relative_path": rel,
        "status": "PENDING",
        "imports": [],
        "symbols": [],
        "detected_interfaces": [],
        "findings": [],
        "source_hash": stable_hash(source, 64),
        "executed": False,
        "source_modified": False,
    }
    try:
        tree = ast.parse(source, filename=rel, type_comments=True)
    except (SyntaxError, ValueError, TypeError, RecursionError) as exc:
        result["status"] = "SYNTAX_FAIL"
        result["findings"].append({
            "classification": "REFACTOR", "severity": "SYNTAX_ERROR",
            "line": getattr(exc, "lineno", None), "message": str(exc), "auto_fix": False,
        })
        return result

    # Bound parser output before any recursive visitor walks the tree.
    stack: list[tuple[ast.AST, int]] = [(tree, 1)]
    node_count = 0
    depth_exceeded = False
    while stack:
        node, depth = stack.pop()
        node_count += 1
        if node_count > MAX_AST_NODES or depth > MAX_AST_DEPTH:
            depth_exceeded = True
            break
        stack.extend((child, depth + 1) for child in ast.iter_child_nodes(node))
    if depth_exceeded:
        result["status"] = "AST_LIMIT"
        result["findings"].append({
            "classification": "REVIEW", "severity": "AST_SIZE_OR_DEPTH_LIMIT",
            "node_count_at_least": node_count, "depth_at_least": depth,
            "max_nodes": MAX_AST_NODES, "max_depth": MAX_AST_DEPTH,
            "auto_fix": False,
        })
        return result
    try:
        compile(tree, rel, "exec")  # compile only; never exec the code object
    except (SyntaxError, ValueError, TypeError, RecursionError) as exc:
        result["status"] = "COMPILE_FAIL"
        result["findings"].append({
            "classification": "REFACTOR", "severity": "COMPILE_ERROR",
            "line": getattr(exc, "lineno", None), "message": str(exc), "auto_fix": False,
        })
        return result

    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    visitor = _SymbolVisitor(rel)
    visitor.visit(tree)
    symbols = visitor.symbols[:MAX_SYMBOLS_PER_FILE]
    top_level_names = {
        n.name for n in tree.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }
    result.update({
        "status": "AST_OK",
        "imports": sorted(imports),
        "symbols": symbols,
        "detected_interfaces": sorted(set(EXPECTED_INTERFACES) & top_level_names),
        "findings": _unsafe_call_findings(tree, rel),
    })
    counts: dict[str, int] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            counts[node.name] = counts.get(node.name, 0) + 1
    for name, count in counts.items():
        if count > 1:
            result["findings"].append({
                "classification": "REFACTOR", "severity": "DUPLICATE_TOP_LEVEL_SYMBOL",
                "line": next(getattr(n, "lineno", 0) for n in tree.body if getattr(n, "name", None) == name),
                "symbol": name, "count": count, "auto_fix": False,
            })
    return result


def _skip_path(path: Path, root: Path) -> bool:
    try:
        rel = path.relative_to(root)
    except ValueError:
        return True
    return any(part.lower() in EXCLUDED_DIRS for part in rel.parts)


def scan_project(root_value: str | Path, *, max_files: int = MAX_SCAN_FILES) -> dict[str, Any]:
    root = Path(root_value).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise ValueError(f"scan root is not a directory: {root}")
    if max_files < 1:
        raise ValueError("max_files must be at least 1")
    max_files = min(max_files, MAX_SCAN_FILES)
    files: list[Path] = []
    walk_errors: list[str] = []
    limit_reached = False
    def on_walk_error(error: OSError) -> None:
        walk_errors.append(type(error).__name__)
    for current, dirs, names in os.walk(root, topdown=True, followlinks=False, onerror=on_walk_error):
        current_path = Path(current)
        dirs[:] = sorted(
            (name for name in dirs
             if name.lower() not in EXCLUDED_DIRS and not (current_path / name).is_symlink()),
            key=str.casefold,
        )
        for name in sorted(names, key=str.casefold):
            if not name.lower().endswith(".py"):
                continue
            path = current_path / name
            if path.is_symlink():
                continue
            files.append(path)
            if len(files) >= max_files:
                limit_reached = True
                break
        if limit_reached:
            break
    files.sort(key=lambda p: p.relative_to(root).as_posix().casefold())
    modules: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    for ordinal, path in enumerate(files, start=1):
        rel = path.relative_to(root).as_posix()
        try:
            if path.stat().st_size > MAX_SOURCE_BYTES:
                skipped.append({"path": rel, "reason": "MAX_SOURCE_BYTES"})
                continue
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            skipped.append({"path": rel, "reason": type(exc).__name__})
            continue
        record = scan_source(source, rel)
        record["module_number"] = f"VIA-PY-{ordinal:04d}"
        modules.append(record)
    return {
        "schema": "VIA_AST_INDEX/1.0",
        "root_label": root.name,
        "scanned_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "mode": "READ_ONLY_AST_OVERLAY",
        "count": len(modules),
        "skipped_count": len(skipped),
        "scan_limit_reached": limit_reached,
        "walk_error_count": len(walk_errors),
        "modules": modules,
        "skipped": skipped,
        "limits": {"max_files": max_files, "max_source_bytes": MAX_SOURCE_BYTES,
                   "excluded_dirs": sorted(EXCLUDED_DIRS)},
    }


# ---------- Eight deterministic VIA core Skill implementations ----------


def _require(payload: Mapping[str, Any], *keys: str) -> list[str]:
    return [key for key in keys if key not in payload or payload[key] in (None, "", [])]


def via_planner(payload: Mapping[str, Any]) -> dict[str, Any]:
    missing = _require(payload, "objective")
    if missing:
        return {"status": "NEEDS_INPUT", "missing": missing}
    objective = str(payload["objective"]).strip()
    requested = payload.get("requested_tasks")
    if not isinstance(requested, list) or not requested:
        requested = ["確認範圍與驗收條件", "完成最小可行切片", "執行測試與安全檢查", "記錄結果並決定下一步"]
    tasks = [{"id": f"T{i:03d}", "title": str(item), "depends_on": [f"T{i-1:03d}"] if i > 1 else [],
              "acceptance": "由負責人核定；未核定前標記為待確認"}
             for i, item in enumerate(requested, 1)]
    return {
        "status": "DRAFT", "objective": objective,
        "epics": [{"id": "E001", "title": objective, "tasks": tasks}],
        "constraints": list(payload.get("constraints", [])) if isinstance(payload.get("constraints", []), list) else [str(payload.get("constraints"))],
        "budget": payload.get("budget"), "deadline": payload.get("deadline"),
        "risks": ["專案來源碼／VCGC 尚未提供時不可宣稱已整合", "驗收指標須以實際基線核定"],
        "open_questions": ["哪些既有行為必須逐項保持不變？", "SSOT 的正式 schema 與位置為何？"],
    }


def _topological_sort(modules: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    ids = {str(m.get("id")) for m in modules if m.get("id")}
    indegree = {key: 0 for key in ids}
    outgoing = {key: [] for key in ids}
    missing: list[dict[str, str]] = []
    for module in modules:
        mid = str(module.get("id", ""))
        for dep in module.get("depends_on", []) or []:
            dep = str(dep)
            if dep not in ids:
                missing.append({"module": mid, "dependency": dep})
            else:
                indegree[mid] += 1
                outgoing[dep].append(mid)
    queue = sorted(k for k, degree in indegree.items() if degree == 0)
    order: list[str] = []
    while queue:
        current = queue.pop(0)
        order.append(current)
        for child in sorted(outgoing[current]):
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
                queue.sort()
    cycles = sorted(k for k, degree in indegree.items() if degree > 0)
    return {"order": order, "cycles": cycles, "missing_dependencies": missing,
            "status": "OK" if not cycles and not missing else "REVIEW"}


def via_architect(payload: Mapping[str, Any]) -> dict[str, Any]:
    missing = _require(payload, "requirements")
    if missing:
        return {"status": "NEEDS_INPUT", "missing": missing}
    modules = payload.get("modules", [])
    if not isinstance(modules, list):
        return {"status": "INVALID_INPUT", "error": "modules must be a list of {id, depends_on}"}
    topology = _topological_sort(modules)
    return {
        "status": topology["status"],
        "requirements": payload["requirements"],
        "modules": modules,
        "dependency_order": topology["order"],
        "cycles": topology["cycles"],
        "missing_dependencies": topology["missing_dependencies"],
        "interfaces": payload.get("interfaces", []),
        "decision": "AST／靜態關係只作線索；不可當作執行時依賴證據。",
    }


def via_decision_log(payload: Mapping[str, Any]) -> dict[str, Any]:
    missing = _require(payload, "decision", "rationale")
    if missing:
        return {"status": "NEEDS_INPUT", "missing": missing}
    date = str(payload.get("date") or _dt.datetime.now(_dt.timezone.utc).date().isoformat())
    material = "|".join((date, str(payload["decision"]), str(payload["rationale"])))
    return {
        "status": "DRAFT", "adr": {
            "id": f"ADR-{date.replace('-', '')}-{stable_hash(material, 6).upper()}",
            "date": date, "decision": str(payload["decision"]),
            "reason": str(payload["rationale"]),
            "alternatives": payload.get("alternatives", []),
            "impact": payload.get("impact", "未提供；待負責人評估"),
            "owner": payload.get("owner", "未指定"),
            "approval": "PENDING",
        },
    }


def via_factor_builder(payload: Mapping[str, Any]) -> dict[str, Any]:
    missing = _require(payload, "hypothesis")
    if missing:
        return {"status": "NEEDS_INPUT", "missing": missing}
    factor = {
        "id": str(payload.get("id") or "FACTOR-" + stable_hash(str(payload["hypothesis"]), 8).upper()),
        "name": payload.get("name", "未命名因子"),
        "category": payload.get("category", "未分類"),
        "hypothesis": str(payload["hypothesis"]),
        "market": payload.get("market", "未指定"),
        "dataset": payload.get("dataset", "未指定"),
        "signal": payload.get("signal", "待定義"),
        "formula": payload.get("formula", "待定義"),
        "regime": payload.get("regime", "待定義"),
        "expected_behavior": payload.get("expected_behavior", "待定義"),
        "failure_case": payload.get("failure_case", "待定義"),
        "risk": payload.get("risk", []),
        "data_version": payload.get("data_version", "未提供"),
        "status": "DRAFT",
    }
    pending = [k for k in ("signal", "formula", "regime", "failure_case", "data_version") if factor[k] in ("待定義", "未提供")]
    return {"status": "DRAFT" if pending else "READY_FOR_VALIDATION", "factor": factor, "missing_fields": pending}


def via_factor_validator(payload: Mapping[str, Any]) -> dict[str, Any]:
    missing = _require(payload, "factor", "evidence")
    if missing:
        return {"status": "NEEDS_INPUT", "missing": missing}
    evidence = payload["evidence"]
    if not isinstance(evidence, Mapping):
        return {"status": "INVALID_INPUT", "error": "evidence must be an object"}
    required = ("sample_size", "data_period", "data_version", "lookahead_check",
                "survivorship_check", "liquidity_check", "transaction_costs",
                "out_of_sample_check")
    absent = [key for key in required if key not in evidence or evidence[key] in (None, "", [])]
    risk_flags = [key for key in required if evidence.get(key) in (False, "FAIL", "HIGH_RISK")]
    min_obs = int(payload.get("minimum_observations", 0) or 0)
    sample_size = evidence.get("sample_size")
    if isinstance(sample_size, (int, float)) and min_obs and sample_size < min_obs:
        risk_flags.append("sample_size_below_policy_minimum")
    status = "INCOMPLETE" if absent else ("REVIEW_REQUIRED" if risk_flags else "EVIDENCE_COMPLETE_NOT_STATISTICAL_CERTIFICATION")
    return {"status": status, "factor_id": payload["factor"].get("id") if isinstance(payload["factor"], Mapping) else None,
            "missing_evidence": absent, "risk_flags": sorted(set(risk_flags)),
            "evidence": dict(evidence),
            "disclaimer": "此檢查只驗證欄位與明示風險，不計算顯著性，也不認證因子有效。"}


def via_strategy_builder(payload: Mapping[str, Any]) -> dict[str, Any]:
    missing = _require(payload, "factor_list")
    required = ("entry", "exit", "stop", "position")
    absent = [key for key in required if payload.get(key) in (None, "", [])]
    if missing:
        return {"status": "NEEDS_INPUT", "missing": missing}
    strategy = {key: payload.get(key) for key in required}
    strategy.update({"factor_list": payload["factor_list"],
                     "risk_limits": payload.get("risk_limits"),
                     "cost_assumptions": payload.get("cost_assumptions"),
                     "data_version": payload.get("data_version"),
                     "status": "DRAFT" if absent else "READY_FOR_BACKTEST"})
    return {"status": strategy["status"], "strategy": strategy,
            "missing_fields": absent,
            "backtest_requirements": ["point-in-time data", "transaction costs", "slippage", "liquidity", "out-of-sample period"]}


def via_code_review(payload: Mapping[str, Any]) -> dict[str, Any]:
    missing = _require(payload, "source_code")
    if missing:
        return {"status": "NEEDS_INPUT", "missing": missing}
    report = scan_source(str(payload["source_code"]), str(payload.get("relative_path", "module.py")))
    findings = report["findings"]
    return {"status": report["status"], "classification": "REVIEW" if findings else "KEEP",
            "findings": findings, "ast_index": report,
            "actions": {"delete": [], "refactor": findings, "keep": report["detected_interfaces"]},
            "source_changed": False}


def via_memory_manager(payload: Mapping[str, Any]) -> dict[str, Any]:
    missing = _require(payload, "memory_candidate")
    if missing:
        return {"status": "NEEDS_INPUT", "missing": missing}
    candidate = payload["memory_candidate"]
    if not isinstance(candidate, Mapping):
        return {"status": "INVALID_INPUT", "error": "memory_candidate must be an object"}
    content = str(candidate.get("content", ""))
    kind = str(candidate.get("kind", "unknown")).lower()
    if not content.strip():
        return {"status": "REJECTED", "action": "reject", "reason": "empty content"}
    if any(word in kind for word in ("debug", "log", "install", "credential", "secret")):
        return {"status": "REJECTED", "action": "reject", "reason": "temporary/noisy/sensitive memory category"}
    redacted, found = redact_secrets(content)
    if found:
        return {"status": "REJECTED", "action": "reject", "reason": "secret-like content detected; do not persist", "redacted_preview": redacted[:160]}
    fingerprint = stable_hash(" ".join(content.split()), 64)
    existing = set(str(x) for x in payload.get("existing_fingerprints", []))
    if fingerprint in existing:
        return {"status": "DUPLICATE", "action": "archive", "fingerprint": fingerprint}
    importance = max(0, min(100, int(candidate.get("importance", 0) or 0)))
    threshold = max(0, min(100, int(payload.get("threshold", 60) or 0)))
    approved = bool(payload.get("approved", candidate.get("approved", False)))
    if not approved or importance < threshold:
        return {"status": "REVIEW_REQUIRED", "action": "reject", "fingerprint": fingerprint,
                "reason": "需要人工核准且達到重要性門檻；本函式不寫入記憶庫"}
    return {"status": "APPROVED_CANDIDATE", "action": "save", "fingerprint": fingerprint,
            "memory": {"content": content, "kind": kind,
                       "scope": candidate.get("scope", "project"),
                       "source": candidate.get("source", "unspecified"),
                       "expires_at": candidate.get("expires_at"),
                       "importance": importance},
            "persisted": False}


SKILL_RUNNERS = {
    "via-planner": via_planner,
    "via-architect": via_architect,
    "via-decision-log": via_decision_log,
    "via-factor-builder": via_factor_builder,
    "via-factor-validator": via_factor_validator,
    "via-strategy-builder": via_strategy_builder,
    "via-code-review": via_code_review,
    "via-memory-manager": via_memory_manager,
}


def run_skill(skill_id: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    if skill_id not in SKILL_RUNNERS:
        raise KeyError(f"unknown skill: {skill_id}")
    # Skills are one-shot deterministic functions. No skill can recursively call
    # another skill or spawn an agent; a workflow orchestrator must be reviewed.
    return SKILL_RUNNERS[skill_id](payload)


SKILL_SMOKE_INPUTS: dict[str, dict[str, Any]] = {
    "via-planner": {"objective": "dashboard smoke", "requested_tasks": ["validate", "report"]},
    "via-architect": {"requirements": "one module", "modules": [{"id": "core", "depends_on": []}]},
    "via-decision-log": {"decision": "use local report", "rationale": "offline and reproducible", "date": "2026-11-03"},
    "via-factor-builder": {"hypothesis": "sample hypothesis", "signal": "provided signal", "formula": "provided formula", "regime": "test", "failure_case": "missing data", "data_version": "fixture-v1"},
    "via-factor-validator": {"factor": {"id": "SMOKE-F1"}, "evidence": {
        "sample_size": 100, "data_period": "fixture", "data_version": "fixture-v1",
        "lookahead_check": "PASS", "survivorship_check": "PASS", "liquidity_check": "PASS",
        "transaction_costs": "included", "out_of_sample_check": "PASS"}},
    "via-strategy-builder": {"factor_list": ["SMOKE-F1"], "entry": "fixture entry", "exit": "fixture exit", "stop": "fixture stop", "position": "fixture size"},
    "via-code-review": {"relative_path": "smoke.py", "source_code": "def smoke(value):\n    return value\n"},
    "via-memory-manager": {"memory_candidate": {"content": "smoke decision record", "kind": "decision", "importance": 80, "approved": True, "scope": "test"}},
}


def run_skill_smokes() -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    for skill_id, payload in SKILL_SMOKE_INPUTS.items():
        try:
            output = run_skill(skill_id, payload)
            results[skill_id] = {"ok": "status" in output and output["status"] not in {"ERROR", "INVALID_INPUT"},
                                 "status": str(output.get("status", "UNKNOWN"))}
        except Exception as exc:
            results[skill_id] = {"ok": False, "status": "ERROR", "error": type(exc).__name__}
    return results


def run_skill_acceptance_suite() -> dict[str, Any]:
    """Run deterministic, in-process positive/negative checks for all eight Skills."""
    if not __debug__:
        raise RuntimeError("acceptance suite requires assertions enabled; do not run Python with -O")
    case_results: list[dict[str, Any]] = []

    def planner_missing() -> str:
        out = via_planner({})
        assert out["status"] == "NEEDS_INPUT" and "objective" in out["missing"]
        return "必要欄位缺漏時阻擋產生計畫。"

    def planner_dependencies() -> str:
        out = via_planner({"objective": "fixture plan", "requested_tasks": ["scan", "test"]})
        tasks = out["epics"][0]["tasks"]
        assert out["status"] == "DRAFT" and [x["id"] for x in tasks] == ["T001", "T002"]
        assert tasks[1]["depends_on"] == ["T001"]
        return "產生穩定任務編號與前置依賴；狀態維持 DRAFT。"

    def architect_missing() -> str:
        out = via_architect({})
        assert out["status"] == "NEEDS_INPUT" and "requirements" in out["missing"]
        return "缺少架構需求時拒絕生成。"

    def architect_cycle() -> str:
        out = via_architect({"requirements": "fixture", "modules": [
            {"id": "A", "depends_on": ["B"]}, {"id": "B", "depends_on": ["A"]}]})
        assert out["status"] == "REVIEW" and set(out["cycles"]) == {"A", "B"}
        return "循環依賴被標示為 REVIEW，沒有執行模組。"

    def decision_required_fields() -> str:
        out = via_decision_log({"decision": "fixture decision"})
        assert out["status"] == "NEEDS_INPUT" and "rationale" in out["missing"]
        return "缺少 rationale 時不建立 ADR。"

    def decision_deterministic_id() -> str:
        payload = {"decision": "keep local mode", "rationale": "repeatable fixture", "date": "2026-11-03"}
        first, second = via_decision_log(payload), via_decision_log(payload)
        assert first["status"] == "DRAFT" and first["adr"]["approval"] == "PENDING"
        assert first["adr"]["id"] == second["adr"]["id"]
        return "相同輸入產生相同 ADR ID，且仍需人工核准。"

    def factor_builder_incomplete() -> str:
        out = via_factor_builder({"hypothesis": "fixture hypothesis"})
        assert out["status"] == "DRAFT" and {"signal", "formula", "regime", "failure_case", "data_version"}.issubset(set(out["missing_fields"]))
        return "定義不完整的因子只會輸出 DRAFT 與待補欄位。"

    def factor_builder_ready() -> str:
        out = via_factor_builder({"hypothesis": "fixture hypothesis", "signal": "fixture signal",
            "formula": "fixture formula", "regime": "fixture regime", "failure_case": "fixture failure",
            "data_version": "synthetic-v1"})
        assert out["status"] == "READY_FOR_VALIDATION" and not out["missing_fields"]
        return "欄位齊備可交給驗證；沒有宣稱因子有效。"

    valid_evidence = {"sample_size": 1000, "data_period": "synthetic-period", "data_version": "synthetic-v1",
        "lookahead_check": "PASS", "survivorship_check": "PASS", "liquidity_check": "PASS",
        "transaction_costs": "included", "out_of_sample_check": "PASS"}

    def validator_incomplete() -> str:
        out = via_factor_validator({"factor": {"id": "FIXTURE-F1"}, "evidence": {"sample_size": 10}})
        assert out["status"] == "INCOMPLETE" and "lookahead_check" in out["missing_evidence"]
        return "未提供完整驗證證據時標示 INCOMPLETE。"

    def validator_risk_flag() -> str:
        evidence = dict(valid_evidence, lookahead_check="FAIL")
        out = via_factor_validator({"factor": {"id": "FIXTURE-F1"}, "evidence": evidence})
        assert out["status"] == "REVIEW_REQUIRED" and "lookahead_check" in out["risk_flags"]
        return "前視偏誤失敗會觸發 REVIEW_REQUIRED。"

    def validator_policy_minimum() -> str:
        evidence = dict(valid_evidence, sample_size=20)
        out = via_factor_validator({"factor": {"id": "FIXTURE-F1"}, "evidence": evidence, "minimum_observations": 100})
        assert out["status"] == "REVIEW_REQUIRED" and "sample_size_below_policy_minimum" in out["risk_flags"]
        return "低於明示樣本門檻時觸發 REVIEW_REQUIRED。"

    def validator_complete_not_certified() -> str:
        out = via_factor_validator({"factor": {"id": "FIXTURE-F1"}, "evidence": valid_evidence})
        assert out["status"] == "EVIDENCE_COMPLETE_NOT_STATISTICAL_CERTIFICATION"
        assert "不計算顯著性" in out["disclaimer"]
        return "完整欄位不等於統計認證或因子有效。"

    def strategy_missing_factor() -> str:
        out = via_strategy_builder({"entry": "fixture entry"})
        assert out["status"] == "NEEDS_INPUT" and "factor_list" in out["missing"]
        return "未提供 factor_list 時阻擋策略輸出。"

    def strategy_ready_with_backtest_gates() -> str:
        out = via_strategy_builder({"factor_list": ["FIXTURE-F1"], "entry": "fixture entry",
            "exit": "fixture exit", "stop": "fixture stop", "position": "fixture sizing"})
        assert out["status"] == "READY_FOR_BACKTEST"
        assert {"transaction costs", "slippage", "out-of-sample period"}.issubset(set(out["backtest_requirements"]))
        return "策略進入回測前保留成本、滑價與樣本外檢查閘。"

    def review_missing_source() -> str:
        out = via_code_review({})
        assert out["status"] == "NEEDS_INPUT" and "source_code" in out["missing"]
        return "缺少來源碼時拒絕執行審查。"

    def review_static_only() -> str:
        out = via_code_review({"source_code": "def f(value):\n    return eval(value)\n", "relative_path": "fixture.py"})
        severities = {item.get("severity") for item in out["findings"]}
        assert out["classification"] == "REVIEW" and "REVIEW_DYNAMIC_CODE" in severities
        assert out["ast_index"]["executed"] is False and out["source_changed"] is False
        return "eval 僅被 AST 靜態標記；程式未執行、未修改。"

    def review_syntax_failure() -> str:
        out = via_code_review({"source_code": "def broken(:\n    pass\n"})
        assert out["status"] == "SYNTAX_FAIL" and out["source_changed"] is False
        return "語法錯誤被回報；不嘗試自動修補或執行來源。"

    def memory_missing() -> str:
        out = via_memory_manager({})
        assert out["status"] == "NEEDS_INPUT" and "memory_candidate" in out["missing"]
        return "缺少候選記憶時不寫入任何資料。"

    def memory_sensitive_kind() -> str:
        out = via_memory_manager({"memory_candidate": {"content": "fixture log", "kind": "debug_log"}})
        assert out["status"] == "REJECTED" and out["action"] == "reject"
        return "debug/log 類別被拒絕保存。"

    def memory_secret_content() -> str:
        out = via_memory_manager({"memory_candidate": {"content": 'api_key="abcdefgh123456789"',
            "kind": "decision", "importance": 90, "approved": True}})
        assert out["status"] == "REJECTED" and out["action"] == "reject"
        return "合成的假憑證字串觸發拒絕；未使用或保存真實憑證。"

    def memory_approval_gate() -> str:
        out = via_memory_manager({"memory_candidate": {"content": "fixture decision", "kind": "decision", "importance": 90}})
        assert out["status"] == "REVIEW_REQUIRED" and "persisted" not in out
        return "缺少明確核准時只要求人工審查。"

    def memory_duplicate() -> str:
        content = "fixture duplicate decision"
        fingerprint = stable_hash(content, 64)
        out = via_memory_manager({"memory_candidate": {"content": content, "kind": "decision", "importance": 90},
                                  "approved": True, "existing_fingerprints": [fingerprint]})
        assert out["status"] == "DUPLICATE" and out["action"] == "archive"
        return "正規化指紋命中時標示重複並封存，不新增。"

    def memory_approved_candidate_not_persisted() -> str:
        out = via_memory_manager({"memory_candidate": {"content": "fixture approved decision", "kind": "decision", "importance": 90},
                                  "approved": True})
        assert out["status"] == "APPROVED_CANDIDATE" and out["persisted"] is False
        return "核准後只回傳候選物件；本 Skill 本身不落盤。"

    for skill, case, fn in [
        ("via-planner", "missing_objective_guard", planner_missing),
        ("via-planner", "stable_task_dependencies", planner_dependencies),
        ("via-architect", "missing_requirements_guard", architect_missing),
        ("via-architect", "cycle_detection", architect_cycle),
        ("via-decision-log", "rationale_required", decision_required_fields),
        ("via-decision-log", "deterministic_id_and_pending_approval", decision_deterministic_id),
        ("via-factor-builder", "incomplete_factor_stays_draft", factor_builder_incomplete),
        ("via-factor-builder", "complete_factor_ready_for_validation", factor_builder_ready),
        ("via-factor-validator", "missing_evidence_incomplete", validator_incomplete),
        ("via-factor-validator", "lookahead_failure_review_gate", validator_risk_flag),
        ("via-factor-validator", "minimum_observation_gate", validator_policy_minimum),
        ("via-factor-validator", "complete_evidence_not_certification", validator_complete_not_certified),
        ("via-strategy-builder", "factor_list_required", strategy_missing_factor),
        ("via-strategy-builder", "backtest_gate_preserved", strategy_ready_with_backtest_gates),
        ("via-code-review", "source_required", review_missing_source),
        ("via-code-review", "static_dynamic_code_warning", review_static_only),
        ("via-code-review", "syntax_failure_no_autofix", review_syntax_failure),
        ("via-memory-manager", "candidate_required", memory_missing),
        ("via-memory-manager", "debug_log_rejected", memory_sensitive_kind),
        ("via-memory-manager", "synthetic_secret_rejected", memory_secret_content),
        ("via-memory-manager", "explicit_approval_required", memory_approval_gate),
        ("via-memory-manager", "duplicate_fingerprint_archived", memory_duplicate),
        ("via-memory-manager", "approved_candidate_not_persisted", memory_approved_candidate_not_persisted),
    ]:
        started = time.perf_counter()
        try:
            detail = fn()
            item = {"skill_id": skill, "case_id": case, "status": "PASS", "detail": detail,
                    "duration_ms": int((time.perf_counter() - started) * 1000)}
        except Exception as exc:
            item = {"skill_id": skill, "case_id": case, "status": "FAIL",
                    "detail": f"{type(exc).__name__}: {str(exc)[:240]}",
                    "duration_ms": int((time.perf_counter() - started) * 1000)}
        case_results.append(item)

    grouped = []
    for spec in SKILLS:
        items = [x for x in case_results if x["skill_id"] == spec.id]
        passed = sum(x["status"] == "PASS" for x in items)
        grouped.append({"skill_id": spec.id, "name": spec.name,
            "status": "PASS" if items and passed == len(items) else "FAIL",
            "passed": passed, "total": len(items), "cases": items})
    passed_count = sum(x["status"] == "PASS" for x in case_results)
    suite_ok = bool(case_results) and len(grouped) == 8 and passed_count == len(case_results) and all(x["status"] == "PASS" for x in grouped)
    token_benchmarks = run_token_fixture_benchmarks()
    return {"schema": "VIA_SKILL_TEST_REPORT/1.0",
        "status": "PASS" if suite_ok else "FAIL",
        "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "execution_mode": "deterministic in-process; synthetic fixtures; no network, subprocess, agent calls, or source writes",
        "skill_count": len(grouped), "case_count": len(case_results), "passed_count": passed_count,
        "failed_count": len(case_results) - passed_count, "skills": grouped, "cases": case_results,
        "token_benchmarks": token_benchmarks}


def run_token_fixture_benchmarks() -> dict[str, Any]:
    """Measure small synthetic fixtures only; estimates are not production savings."""
    json_fixture = json.dumps({"rows": [{"metric": "volume", "value": 123},
        {"metric": "turnover", "value": 45}], "note": "synthetic test fixture"}, ensure_ascii=False, indent=2)
    plain_fixture = "\n".join(f"row {i:04d}: ordinary fixture text with no filtering" for i in range(240))
    lossy_fixture = "\n".join(
        f"row {i:04d}: target_signal fixture marker" if i % 60 == 0 else f"row {i:04d}: ordinary fixture context"
        for i in range(720))
    runs = [
        ("json_lossless_compaction", json_fixture, TokenEngine().prepare(json_fixture)),
        ("plain_text_safe_passthrough", plain_fixture, TokenEngine().prepare(plain_fixture)),
        ("query_extraction_lossy_opt_in", lossy_fixture,
         TokenEngine().prepare(lossy_fixture, allow_lossy=True, query="target_signal", max_lines=72)),
    ]
    rows = []
    for name, source, result in runs:
        rows.append({"fixture_id": name, "scope": "SYNTHETIC_TEST_ONLY", "mode": result.mode,
            "lossy": result.lossy, "before_chars": result.chars_before, "after_chars": result.chars_after,
            "before_tokens_est": result.tokens_before_est, "after_tokens_est": result.tokens_after_est,
            "saved_tokens_est": result.tokens_before_est - result.tokens_after_est,
            "saving_percent_est": result.estimated_savings_percent,
            "semantic_roundtrip": strict_json_loads(result.prepared_text) == strict_json_loads(source)
                if name == "json_lossless_compaction" else None})
    return {"label": "synthetic fixtures; not VIA/VCGC/provider measurements",
            "fixture_count": len(rows), "fixtures": rows}


# ---------- Agent-neutral routing and E1/E2/E3 mount contract ----------


def route_file(path_value: str) -> dict[str, str]:
    path = Path(path_value)
    ext = path.suffix.lower()
    if ext in {".py", ".js", ".ts", ".ps1", ".psm1"}:
        engine = "E3"
    elif ext in {".json", ".csv", ".tsv", ".xlsx", ".docx", ".pdf", ".html"}:
        engine = "E1"
    elif ext in {".md", ".txt", ".log"}:
        engine = "E2"
    else:
        engine = "UNROUTED"
    return {"path": path.name, "extension": ext, "engine": engine,
            "action": "route_only_no_execution"}


def validate_mount(manifest: Mapping[str, Any], mount_dir: Path) -> dict[str, Any]:
    errors: list[str] = []
    if manifest.get("contract") != MOUNT_CONTRACT:
        errors.append("unsupported contract")
    if not manifest.get("id"):
        errors.append("missing id")
    if manifest.get("engine") not in {"E1", "E2", "E3"}:
        errors.append("engine must be E1/E2/E3")
    if manifest.get("language") not in {"py", "js", "ps", "exe"}:
        errors.append("unsupported language")
    entry = manifest.get("entry")
    if not isinstance(entry, Mapping) or not isinstance(entry.get("cmd"), list) or not entry["cmd"]:
        errors.append("entry.cmd must be a non-empty argv list")
    else:
        # Validate shape only. Do NOT execute command or resolve remote assets.
        if any(not isinstance(x, str) or not x for x in entry["cmd"]):
            errors.append("entry.cmd elements must be non-empty strings")
        first = entry["cmd"][0] if entry["cmd"] else ""
        if first.lower() in {"bash", "sh", "cmd", "powershell", "pwsh", "python", "python3"}:
            if len(entry["cmd"]) > 1 and any(x in entry["cmd"] for x in ("-c", "-Command", "-EncodedCommand")):
                errors.append("inline command execution is not permitted by the inspection scaffold")
    outputs = manifest.get("outputs", [])
    if not isinstance(outputs, list):
        errors.append("outputs must be a list")
    return {"mount_id": manifest.get("id", mount_dir.name),
            "mount_dir": mount_dir.name,
            "status": "INVALID" if errors else "VALIDATED_NOT_EXECUTED",
            "errors": errors,
            "manifest": dict(manifest),
            "execution_performed": False}


def discover_mounts(root_value: str | Path) -> list[dict[str, Any]]:
    root = Path(root_value).expanduser().resolve(strict=True)
    mounts_dir = root / ".via" / "mounts"
    if not mounts_dir.exists():
        return []
    if mounts_dir.is_symlink() or not mounts_dir.is_dir():
        return [{"status": "INVALID", "error": "mount directory must be a real directory"}]
    results = []
    for manifest_path in sorted(mounts_dir.glob("*/mount.json")):
        if manifest_path.is_symlink() or not manifest_path.is_file():
            results.append({"status": "INVALID", "error": "manifest is symlink or not a regular file"})
            continue
        try:
            data = strict_json_loads(manifest_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("manifest root must be an object")
            results.append(validate_mount(data, manifest_path.parent))
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            results.append({"mount_dir": manifest_path.parent.name, "status": "INVALID", "error": str(exc)})
    return results


# ---------- SSOT registration: namespace merge, backup, atomic replace ----------


def _utc_stamp() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _builtin_modules() -> list[dict[str, Any]]:
    return [
        {"id": "VIA-MOD-TOKEN-ENGINE-001", "name": "VIA Token Engine", "category": "token",
         "status": "ACTIVE_SCAFFOLD", "policy": "EXCLUSIVE_REPLACEMENT", "entry": "TokenEngine.prepare"},
        {"id": "VIA-MOD-AST-INDEX-001", "name": "VIA AST Indexer", "category": "code-intelligence",
         "status": "ACTIVE_READ_ONLY", "entry": "scan_project"},
        {"id": "VIA-MOD-SKILL-REGISTRY-001", "name": "VIA Eight Skill Registry", "category": "skill-orchestration",
         "status": "ACTIVE_DETERMINISTIC", "entry": "run_skill"},
        {"id": "VIA-MOD-VCGC-ADAPTER-001", "name": "VCGC Mount Adapter", "category": "integration",
         "status": "UNVERIFIED_NOT_CONNECTED", "entry": "discover_mounts"},
    ]


def build_ssot_payload(ast_index: Mapping[str, Any], test_report: Mapping[str, Any],
                       mounts: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "app_id": APP_ID,
        "ssot_schema": SSOT_SCHEMA,
        "contract_version": CONTRACT_VERSION,
        "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "registration_status": "SELFTEST_PASSED",
        "token_engine": {
            "id": "via-token-engine", "mode": "EXCLUSIVE_REPLACEMENT",
            "active": True, "legacy_engine_autoload": False,
            "vcgc_status": "UNVERIFIED_NOT_CONNECTED",
            "vcgc_note": "不會停用或修改未提供的 VCGC 程式碼；需先提供 checkout 與 reviewed adapter。",
        },
        "skills": [s.as_contract() for s in SKILLS],
        "modules": _builtin_modules(),
        "ast_index": list(ast_index.get("modules", [])),
        "ast_summary": {"count": ast_index.get("count", 0),
                        "skipped_count": ast_index.get("skipped_count", 0),
                        "mode": ast_index.get("mode", "READ_ONLY_AST_OVERLAY")},
        "mounts": [{"id": m.get("mount_id", m.get("mount_dir", "unknown")),
                    "status": m.get("status", "UNKNOWN"),
                    "execution_performed": False} for m in mounts],
        "test_report": dict(test_report),
        "guardrails": {
            "network_access": False, "subprocess": False,
            "dynamic_import_of_scanned_code": False, "source_autofix": False,
            "recursive_agent_calls": False, "max_skill_call_depth": 1,
            "ssot_write_requires_apply": True, "backup_before_replace": True,
        },
    }


def _merge_records(existing: Any, incoming: Sequence[Mapping[str, Any]], key: str,
                   conflicts: list[str], path: str) -> list[dict[str, Any]]:
    records = existing if isinstance(existing, list) else []
    merged: list[dict[str, Any]] = [dict(x) for x in records if isinstance(x, Mapping)]
    positions = {str(row.get(key)): i for i, row in enumerate(merged) if row.get(key) is not None}
    for item in incoming:
        row = dict(item)
        rid = str(row.get(key, ""))
        if rid and rid in positions:
            old = merged[positions[rid]]
            for field, value in row.items():
                if field not in old:
                    old[field] = value
                elif old[field] != value:
                    conflicts.append(f"{path}[{rid}].{field}: existing value preserved")
        else:
            merged.append(row)
            if rid:
                positions[rid] = len(merged) - 1
    return merged


def merge_ssot(existing: Mapping[str, Any] | None, payload: Mapping[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Merge only our namespace; preserve all unknown root and record fields."""
    data = dict(existing or {})
    if not isinstance(data, dict):
        raise ValueError("SSOT root must be a JSON object")
    namespace = data.get(APP_ID, {})
    if not isinstance(namespace, dict):
        raise ValueError(f"existing {APP_ID} namespace is not an object; refusing to overwrite")
    namespace = dict(namespace)
    conflicts: list[str] = []
    for key, value in payload.items():
        if key == "skills":
            namespace[key] = _merge_records(namespace.get(key), value, "id", conflicts, APP_ID + ".skills")
        elif key in {"modules", "ast_index", "mounts"}:
            merge_key = "id" if key in {"modules", "mounts"} else "module_id"
            namespace[key] = _merge_records(namespace.get(key), value, merge_key, conflicts, APP_ID + "." + key)
        elif key not in namespace:
            namespace[key] = value
        elif key == "generated_at":
            namespace[key] = value
        elif namespace[key] != value:
            conflicts.append(f"{APP_ID}.{key}: existing value preserved")
    namespace["registration_conflicts"] = conflicts
    data[APP_ID] = namespace
    return data, conflicts


def _safe_root(root_value: str | Path) -> Path:
    root = Path(root_value).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise ValueError("--root must be an existing directory")
    if root == Path(root.anchor) or root == Path.home().resolve():
        raise ValueError("refusing to register at filesystem root or home directory; pass a project directory")
    return root


def _atomic_json_write(path: Path, data: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink() or path.is_symlink():
        raise ValueError("refusing to write through symlinks")
    text = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent,
                                         prefix="." + path.name + ".", suffix=".tmp", delete=False) as handle:
            temp_name = handle.name
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if temp_name and os.path.exists(temp_name):
            try:
                os.unlink(temp_name)
            except OSError:
                pass


def _normalize_metric_record(event: Mapping[str, Any]) -> dict[str, Any]:
    event_type = str(event.get("event_type", ""))
    fields: dict[str, tuple[str, ...]] = {
        "context": ("mode", "lossy", "redacted_count", "before_tokens_est", "after_tokens_est",
                    "saved_tokens_est", "savings_percent_est", "skill_id", "source"),
        "skill": ("skill_id", "status", "input_tokens_est", "output_tokens_est", "duration_ms", "source"),
        "provider_usage": ("provider", "model", "prompt_tokens", "completion_tokens",
                           "baseline_prompt_tokens", "skill_id", "request_id_hash", "source"),
    }
    if event_type not in fields:
        raise ValueError("unsupported metrics event_type")
    out: dict[str, Any] = {
        "schema": "VIA_METRICS/1.0", "event_type": event_type,
        "timestamp": str(event.get("timestamp") or _dt.datetime.now(_dt.timezone.utc).isoformat())[:48],
    }
    string_fields = {"mode", "skill_id", "status", "source", "provider", "model", "request_id_hash"}
    int_fields = {"redacted_count", "before_tokens_est", "after_tokens_est", "saved_tokens_est",
                  "input_tokens_est", "output_tokens_est", "duration_ms", "prompt_tokens",
                  "completion_tokens", "baseline_prompt_tokens"}
    for key in fields[event_type]:
        if key not in event:
            continue
        value = event[key]
        if key in string_fields:
            value = str(value)[:96]
            if key == "skill_id" and value and value not in SKILL_BY_ID:
                raise ValueError("unknown skill_id in metrics")
            if key == "status" and not re.fullmatch(r"[A-Za-z0-9_ -]{1,48}", value):
                value = "OTHER"
        elif key == "lossy":
            value = bool(value)
        elif key == "savings_percent_est":
            value = float(value)
            if not math.isfinite(value) or abs(value) > 1000:
                raise ValueError("invalid savings_percent_est")
            value = round(value, 2)
        elif key in int_fields:
            value = int(value)
            if abs(value) > 10**12:
                raise ValueError("metrics integer out of range")
            if key != "saved_tokens_est" and value < 0:
                raise ValueError(f"{key} must be non-negative")
        out[key] = value
    if event_type == "skill" and out.get("skill_id") not in SKILL_BY_ID:
        raise ValueError("skill metrics require a known skill_id")
    return out


def append_metric(root_value: str | Path, event: Mapping[str, Any]) -> dict[str, Any]:
    """Append a content-free event to .via/metrics.jsonl; never overwrites history."""
    root = _safe_root(root_value)
    via_dir = root / ".via"
    if via_dir.is_symlink():
        raise ValueError("refusing symlink .via directory")
    via_dir.mkdir(parents=True, exist_ok=True)
    path = via_dir / "metrics.jsonl"
    lock = via_dir / ".metrics.lock"
    if path.is_symlink():
        raise ValueError("refusing symlink metrics file")
    if path.exists() and path.stat().st_size > MAX_METRICS_BYTES:
        raise ValueError("metrics log reached the configured size limit; archive it manually")
    clean = _normalize_metric_record(event)
    clean["event_id"] = stable_hash(json.dumps(clean, ensure_ascii=False, sort_keys=True), 24)
    line = (json.dumps(clean, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    if len(line) > 4096:
        raise ValueError("metrics event too large")
    try:
        lock_fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise RuntimeError("metrics lock exists; no automatic lock deletion") from exc
    try:
        os.close(lock_fd)
        if via_dir.is_symlink():
            raise ValueError("refusing symlink .via directory")
        if path.is_symlink():
            raise ValueError("refusing symlink metrics file")
        if path.exists() and path.stat().st_size + len(line) > MAX_METRICS_BYTES:
            raise ValueError("metrics log reached the configured size limit; archive it manually")
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = os.open(str(path), flags, 0o600)
        try:
            remaining = memoryview(line)
            while remaining:
                written = os.write(fd, remaining)
                if written <= 0:
                    raise OSError("short write while appending metrics")
                remaining = remaining[written:]
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        try:
            lock.unlink()
        except FileNotFoundError:
            pass
    return {"path": str(path), "event_id": clean["event_id"], "event_type": clean["event_type"]}


def read_metric_log(root_value: str | Path) -> tuple[list[dict[str, Any]], int]:
    root = _safe_root(root_value)
    via_dir = root / ".via"
    if via_dir.is_symlink():
        raise ValueError("refusing symlink .via directory")
    path = via_dir / "metrics.jsonl"
    if not path.exists():
        return [], 0
    if path.is_symlink() or not path.is_file():
        raise ValueError("metrics path must be a regular non-symlink file")
    if path.stat().st_size > MAX_METRICS_BYTES:
        raise ValueError("metrics log exceeds the configured read limit")
    events: list[dict[str, Any]] = []
    malformed = 0
    for line in path.read_text(encoding="utf-8").splitlines()[-MAX_METRIC_EVENTS:]:
        try:
            parsed = strict_json_loads(line)
            if not isinstance(parsed, Mapping):
                raise ValueError("metrics row is not an object")
            events.append(_normalize_metric_record(parsed))
        except (ValueError, TypeError, json.JSONDecodeError):
            malformed += 1
    return events, malformed


def register_ssot(root_value: str | Path, payload: Mapping[str, Any], *, apply: bool) -> dict[str, Any]:
    root = _safe_root(root_value)
    ssot_dir = root / ".via"
    if ssot_dir.is_symlink():
        raise ValueError("refusing symlink .via directory")
    ssot_path = ssot_dir / "ssot.json"
    if ssot_path.is_symlink():
        raise ValueError("refusing symlink SSOT file")
    existing: dict[str, Any] | None = None
    if ssot_path.exists():
        if not ssot_path.is_file():
            raise ValueError("SSOT path exists but is not a regular file")
        try:
            loaded = strict_json_loads(ssot_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"existing SSOT is unreadable/invalid; refusing overwrite: {exc}") from exc
        if not isinstance(loaded, dict):
            raise ValueError("existing SSOT root must be a JSON object; refusing overwrite")
        existing = loaded
    merged, conflicts = merge_ssot(existing, payload)
    result = {"status": "DRY_RUN" if not apply else "REGISTERED",
              "ssot_path": str(ssot_path), "conflicts": conflicts,
              "added_skills": len(SKILLS), "apply": apply,
              "backup_path": None}
    if not apply:
        result["note"] = "未寫入任何檔案；加入 --apply 才會建立備份並原子更新 SSOT。"
        return result

    ssot_dir.mkdir(parents=True, exist_ok=True)
    lock_path = ssot_dir / ".ssot.lock"
    try:
        fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise RuntimeError("SSOT lock exists; another writer may be active. No automatic lock deletion.") from exc
    backup = None
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as lock:
            lock.write(_dt.datetime.now(_dt.timezone.utc).isoformat())
            lock.flush()
            os.fsync(lock.fileno())
        # Re-read after lock so a concurrent update cannot be silently lost.
        if ssot_path.exists():
            latest = strict_json_loads(ssot_path.read_text(encoding="utf-8"))
            if not isinstance(latest, dict):
                raise ValueError("SSOT changed to a non-object during registration")
            merged, conflicts = merge_ssot(latest, payload)
            result["conflicts"] = conflicts
            backup = ssot_path.with_name(ssot_path.name + ".bak." + _utc_stamp())
            if backup.exists():
                raise FileExistsError(f"backup already exists: {backup}")
            # Exclusive backup create; preserve the original bytes exactly.
            with ssot_path.open("rb") as src, backup.open("xb") as dst:
                dst.write(src.read())
                dst.flush()
                os.fsync(dst.fileno())
            result["backup_path"] = str(backup)
        _atomic_json_write(ssot_path, merged)
    finally:
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass
    return result


# ---------- Test suite: auto-gate registration, never auto-repair source ----------

class _EngineTests(unittest.TestCase):
    def test_eight_core_skills(self) -> None:
        self.assertEqual(len(SKILLS), 8)
        self.assertEqual(set(SkillSpec.__dataclass_fields__), set(SKILLS[0].__dataclass_fields__))

    def test_json_compaction_round_trip_and_not_larger(self) -> None:
        source = '{\n  "rows": [\n    {"metric": "volume", "value": 123},\n    {"metric": "turnover", "value": 45}\n  ]\n}'
        result = TokenEngine().prepare(source)
        self.assertEqual(json.loads(result.prepared_text), json.loads(source))
        self.assertLessEqual(result.chars_after, result.chars_before)

    def test_json_duplicate_keys_are_not_compacted(self) -> None:
        source = '{"metric": 1, "metric": 2}'
        result = TokenEngine().prepare(source)
        self.assertEqual(result.prepared_text, source)
        self.assertEqual(result.mode, "passthrough")

    def test_plain_text_is_not_lossily_changed_by_default(self) -> None:
        source = "line one\nline two\nline one"
        result = TokenEngine().prepare(source)
        self.assertEqual(result.prepared_text, source)
        self.assertFalse(result.lossy)

    def test_common_secret_redaction(self) -> None:
        result = TokenEngine().prepare('api_key="abcdefgh123456789"')
        self.assertEqual(result.redacted_count, 1)
        self.assertIn("[REDACTED]", result.prepared_text)
        json_result = TokenEngine().prepare('{\n  "api_key": "abcdefgh123456789",\n  "safe": 1\n}')
        self.assertEqual(json_result.redacted_count, 1)
        self.assertEqual(strict_json_loads(json_result.prepared_text)["api_key"], "[REDACTED]")

    def test_ast_scan_does_not_execute_source(self) -> None:
        source = "import pathlib\npathlib.Path('should_not_exist').write_text('bad')\ndef f():\n    return 1\n"
        report = scan_source(source, "token/engine.py")
        self.assertEqual(report["status"], "AST_OK")
        self.assertFalse(report["executed"])
        self.assertTrue(report["module_id"].startswith("VIA-MOD-TOKEN-"))

    def test_architecture_cycle_is_reported(self) -> None:
        result = via_architect({"requirements": "split services", "modules": [
            {"id": "A", "depends_on": ["B"]}, {"id": "B", "depends_on": ["A"]}]})
        self.assertEqual(result["status"], "REVIEW")
        self.assertTrue(result["cycles"])

    def test_memory_requires_approval_and_rejects_logs(self) -> None:
        log = via_memory_manager({"memory_candidate": {"content": "trace", "kind": "debug_log"}})
        self.assertEqual(log["action"], "reject")
        pending = via_memory_manager({"memory_candidate": {"content": "ADR approved", "kind": "decision", "importance": 90}})
        self.assertEqual(pending["status"], "REVIEW_REQUIRED")

    def test_ssot_merge_preserves_unknown_data(self) -> None:
        old = {"version": 2, "user_data": {"do_not_delete": True}, APP_ID: {"custom": "keep"}}
        payload = {"app_id": APP_ID, "skills": [SKILLS[0].as_contract()], "modules": [], "ast_index": [], "mounts": []}
        merged, _ = merge_ssot(old, payload)
        self.assertEqual(merged["version"], 2)
        self.assertTrue(merged["user_data"]["do_not_delete"])
        self.assertEqual(merged[APP_ID]["custom"], "keep")

    def test_router_does_not_execute(self) -> None:
        self.assertEqual(route_file("example.py")["engine"], "E3")
        self.assertEqual(route_file("notes.md")["engine"], "E2")
        self.assertEqual(route_file("data.json")["engine"], "E1")
        self.assertEqual(route_file("example.py")["action"], "route_only_no_execution")

    def test_factor_validator_never_passes_missing_evidence(self) -> None:
        result = via_factor_validator({"factor": {"id": "F1"}, "evidence": {"sample_size": 10}})
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertTrue(result["missing_evidence"])

    def test_all_eight_skills_smoke(self) -> None:
        results = run_skill_smokes()
        self.assertEqual(set(results), set(SKILL_RUNNERS))
        self.assertTrue(all(item["ok"] for item in results.values()), results)

    def test_detailed_acceptance_report_and_token_fixtures(self) -> None:
        report = run_skill_acceptance_suite()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["skill_count"], 8)
        self.assertEqual(report["case_count"], 23)
        self.assertEqual(report["passed_count"], 23)
        self.assertTrue(all(item["status"] == "PASS" and item["total"] > 0 for item in report["skills"]))
        benchmarks = run_token_fixture_benchmarks()
        self.assertEqual(benchmarks["fixture_count"], 3)
        self.assertTrue(benchmarks["fixtures"][0]["semantic_roundtrip"])
        self.assertEqual(benchmarks["fixtures"][1]["saved_tokens_est"], 0)
        self.assertTrue(benchmarks["fixtures"][2]["lossy"])

    def test_metrics_store_drops_unapproved_content(self) -> None:
        with tempfile.TemporaryDirectory(prefix="via-metric-test-") as temp:
            root = Path(temp) / "project"
            root.mkdir()
            append_metric(root, {"event_type": "context", "mode": "passthrough",
                "before_tokens_est": 10, "after_tokens_est": 10, "saved_tokens_est": 0,
                "source": "test", "raw_prompt": "must never be written"})
            path = root / ".via" / "metrics.jsonl"
            self.assertNotIn("must never be written", path.read_text(encoding="utf-8"))
            events, malformed = read_metric_log(root)
            self.assertEqual(malformed, 0)
            self.assertEqual(len(events), 1)
            self.assertNotIn("raw_prompt", events[0])

    def test_dashboard_is_offline_and_separates_provider_savings(self) -> None:
        metrics = [{"event_type": "provider_usage", "provider": "fixture", "model": "fixture-model",
                    "prompt_tokens": 80, "completion_tokens": 5, "baseline_prompt_tokens": 100,
                    "skill_id": "via-planner", "source": "provider_reported"}]
        data = build_dashboard_data("fixture", {"count": 0, "skipped_count": 0},
            {"ok": True, "tests_run": 12, "failures": 0, "errors": 0}, [], metrics, 0,
            {"status": "none", "schema": "none", "vcgc_status": "UNVERIFIED_NOT_CONNECTED"})
        document = upgrade_dashboard_document(make_interactive_dashboard(data))
        self.assertEqual(data["summary"]["actual_prompt_saved_tokens"], 20)
        self.assertEqual(data["acceptance_report"]["case_count"], 23)
        self.assertEqual(data["token_benchmarks"]["fixture_count"], 3)
        self.assertIn("via-dashboard-data", document)
        self.assertIn("Token 節省試算器", document)
        self.assertIn('id="tab-tests"', document)
        self.assertIn("acceptance-case-table", document)
        self.assertIn("token-benchmark-table", document)
        self.assertNotIn("<script src=", document)
        self.assertNotIn("fetch(", document)


def run_selftests() -> dict[str, Any]:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(_EngineTests)
    result = unittest.TestResult()
    suite.run(result)
    details = []
    for test, err in result.failures:
        details.append({"test": str(test), "kind": "FAIL", "detail": err[-1200:]})
    for test, err in result.errors:
        details.append({"test": str(test), "kind": "ERROR", "detail": err[-1200:]})
    return {"ok": result.wasSuccessful(), "tests_run": result.testsRun,
            "failures": len(result.failures), "errors": len(result.errors), "details": details,
            "executed_at": _dt.datetime.now(_dt.timezone.utc).isoformat()}


# ---------- Reports / CLI ----------


def _json_print(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


def _load_json_input(data: str | None, file_value: str | None) -> dict[str, Any]:
    if data and file_value:
        raise ValueError("use either --data or --data-file, not both")
    raw = Path(file_value).read_text(encoding="utf-8") if file_value else (data or "{}")
    parsed = strict_json_loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("skill input JSON must be an object")
    return parsed


def make_html_report(ast_index: Mapping[str, Any], test_report: Mapping[str, Any]) -> str:
    rows = []
    for module in ast_index.get("modules", []):
        rows.append("<tr>" + "".join(
            f"<td>{html.escape(str(module.get(k, '')))}</td>"
            for k in ("module_number", "module_id", "category", "relative_path", "status")
        ) + "</tr>")
    counts: dict[str, int] = {}
    for module in ast_index.get("modules", []):
        key = str(module.get("category", "unknown"))
        counts[key] = counts.get(key, 0) + 1
    summary = " ".join(f"{html.escape(k)}: {v}" for k, v in sorted(counts.items())) or "尚無掃描模組"
    test_label = "PASS" if test_report.get("ok") else "FAIL"
    return f"""<!doctype html><html lang=\"zh-Hant\"><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>VIA Workflow Matrix</title>
<style>body{{font:14px/1.5 system-ui,sans-serif;margin:24px;background:#f7f8fa;color:#182230}}h1{{font-size:22px}}.cards{{display:flex;gap:12px;flex-wrap:wrap}}.card{{background:white;border:1px solid #d9e0e8;border-radius:8px;padding:12px 16px}}table{{border-collapse:collapse;width:100%;background:white;margin-top:16px}}th,td{{border:1px solid #d9e0e8;padding:7px;text-align:left}}th{{background:#eaf0f6}}.ok{{color:#087443}}.warn{{color:#8a4b00}}code{{overflow-wrap:anywhere}}</style>
<h1>VIA Agent OS — 唯讀 AST / SSOT Workflow Matrix</h1><div class=\"cards\"><div class=\"card\">AST 模組：{int(ast_index.get('count',0))}</div><div class=\"card\">Self-test：<b class=\"{'ok' if test_report.get('ok') else 'warn'}\">{test_label}</b> ({int(test_report.get('tests_run',0))} tests)</div><div class=\"card\">Token engine：EXCLUSIVE_REPLACEMENT / dry-run first</div></div><p>{summary}</p><table><thead><tr><th>自動編號</th><th>穩定模組 ID</th><th>分類</th><th>相對路徑</th><th>AST 狀態</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
<p>安全狀態：未執行原始碼、未呼叫網路或子程序、未自動修改來源碼。VCGC 未提供 checkout／adapter 時為 UNVERIFIED_NOT_CONNECTED。</p></html>"""


def _dashboard_ssot_info(root: Path) -> dict[str, Any]:
    path = root / ".via" / "ssot.json"
    if not path.exists():
        return {"status": "尚無 SSOT", "schema": "未建立", "vcgc_status": "UNVERIFIED_NOT_CONNECTED"}
    if path.is_symlink() or not path.is_file():
        return {"status": "SSOT 路徑不安全", "schema": "未知", "vcgc_status": "UNVERIFIED_NOT_CONNECTED"}
    try:
        data = strict_json_loads(path.read_text(encoding="utf-8"))
        namespace = data.get(APP_ID, {}) if isinstance(data, Mapping) else {}
        token_engine = namespace.get("token_engine", {}) if isinstance(namespace, Mapping) else {}
        return {"status": str(namespace.get("registration_status", "已存在")) if isinstance(namespace, Mapping) else "SSOT 格式待確認",
                "schema": str(namespace.get("ssot_schema", data.get("version", "未知"))) if isinstance(namespace, Mapping) else "未知",
                "vcgc_status": str(token_engine.get("vcgc_status", "UNVERIFIED_NOT_CONNECTED")) if isinstance(token_engine, Mapping) else "UNVERIFIED_NOT_CONNECTED"}
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
        return {"status": "SSOT 無法解析", "schema": "未知", "vcgc_status": "UNVERIFIED_NOT_CONNECTED"}


def build_dashboard_data(root_label: str, ast_index: Mapping[str, Any],
                         test_report: Mapping[str, Any], mounts: Sequence[Mapping[str, Any]],
                         metrics: Sequence[Mapping[str, Any]], malformed_metrics: int,
                         ssot_info: Mapping[str, Any],
                         acceptance_report: Mapping[str, Any] | None = None) -> dict[str, Any]:
    smokes = run_skill_smokes()
    acceptance = dict(acceptance_report) if acceptance_report is not None else run_skill_acceptance_suite()
    token_benchmarks = acceptance.get("token_benchmarks") or run_token_fixture_benchmarks()
    acceptance_by_skill = {item["skill_id"]: item for item in acceptance.get("skills", [])}
    skills: list[dict[str, Any]] = []
    for spec in SKILLS:
        runs = [m for m in metrics if m.get("event_type") == "skill" and m.get("skill_id") == spec.id]
        contexts = [m for m in metrics if m.get("event_type") == "context" and m.get("skill_id") == spec.id]
        acceptance_skill = acceptance_by_skill.get(spec.id, {})
        latest = max(runs, key=lambda x: str(x.get("timestamp", ""))) if runs else None
        contract = spec.as_contract()
        skills.append({
            "id": spec.id, "name": spec.name, "purpose": spec.purpose,
            "readiness": "PASS" if smokes.get(spec.id, {}).get("ok") else "FAIL",
            "smoke_status": smokes.get(spec.id, {}).get("status", "UNKNOWN"),
            "acceptance_status": str(acceptance_skill.get("status", "UNKNOWN")),
            "acceptance_passed": int(acceptance_skill.get("passed", 0)),
            "acceptance_total": int(acceptance_skill.get("total", 0)),
            "execution_count": len(runs),
            "last_status": str(latest.get("status", "")) if latest else "未執行",
            "last_run_at": str(latest.get("timestamp", "")) if latest else "",
            "associated_context_events": len(contexts),
            "estimated_context_saved_tokens": sum(int(x.get("saved_tokens_est", 0)) for x in contexts),
            "contract": contract,
        })

    context_events = [m for m in metrics if m.get("event_type") == "context"]
    skill_events = [m for m in metrics if m.get("event_type") == "skill"]
    provider_events = [m for m in metrics if m.get("event_type") == "provider_usage"]
    context_before = sum(int(m.get("before_tokens_est", 0)) for m in context_events)
    context_after = sum(int(m.get("after_tokens_est", 0)) for m in context_events)
    context_saved = context_before - context_after
    paired_provider = [m for m in provider_events if m.get("baseline_prompt_tokens") is not None]
    actual_prompt_saved = sum(int(m["baseline_prompt_tokens"]) - int(m.get("prompt_tokens", 0)) for m in paired_provider)
    actual_prompt_baseline = sum(int(m["baseline_prompt_tokens"]) for m in paired_provider)
    actual_prompt_pct = (100.0 * actual_prompt_saved / actual_prompt_baseline) if actual_prompt_baseline else None

    demo_json = '{\n  "rows": [\n    {"metric": "volume", "value": 123},\n    {"metric": "turnover", "value": 45}\n  ]\n}'
    demo = TokenEngine().prepare(demo_json)
    vcgc_mounts = [m for m in mounts if "vcgc" in str(m.get("mount_id", m.get("mount_dir", ""))).lower()]
    vcgc_status = "UNVERIFIED_NOT_CONNECTED"
    if vcgc_mounts:
        vcgc_status = "MANIFEST_VALIDATED_NOT_EXECUTED" if any(m.get("status") == "VALIDATED_NOT_EXECUTED" for m in vcgc_mounts) else "MOUNT_REVIEW_REQUIRED"
    return {
        "schema": "VIA_DASHBOARD/1.0", "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "root_label": root_label, "skills": skills,
        "acceptance_report": acceptance, "token_benchmarks": token_benchmarks,
        "selftest": {"ok": bool(test_report.get("ok")), "tests_run": int(test_report.get("tests_run", 0)),
                     "failures": int(test_report.get("failures", 0)), "errors": int(test_report.get("errors", 0))},
        "ast": {"count": int(ast_index.get("count", 0)), "skipped": int(ast_index.get("skipped_count", 0)),
                "limit_reached": bool(ast_index.get("scan_limit_reached", False))},
        "metrics": list(metrics), "malformed_metrics": int(malformed_metrics),
        "summary": {
            "skill_count": len(SKILLS), "skill_runs": len(skill_events),
            "context_events": len(context_events), "provider_events": len(provider_events),
            "context_before_tokens_est": context_before, "context_after_tokens_est": context_after,
            "context_saved_tokens_est": context_saved,
            "context_saved_percent_est": (100.0 * context_saved / context_before) if context_before else None,
            "actual_prompt_tokens": sum(int(m.get("prompt_tokens", 0)) for m in provider_events),
            "actual_completion_tokens": sum(int(m.get("completion_tokens", 0)) for m in provider_events),
            "actual_paired_count": len(paired_provider), "actual_prompt_saved_tokens": actual_prompt_saved,
            "actual_prompt_saved_percent": actual_prompt_pct,
        },
        "demo_fixture": {"label": "內建小型 JSON fixture；不是 VIA/VCGC 實測",
                          "chars_before": demo.chars_before, "chars_after": demo.chars_after,
                          "tokens_before_est": demo.tokens_before_est, "tokens_after_est": demo.tokens_after_est,
                          "saving_percent_est": demo.estimated_savings_percent, "mode": demo.mode},
        "integration": {"token_policy": "EXCLUSIVE_REPLACEMENT", "vcgc_status": vcgc_status,
                        "ssot": dict(ssot_info), "mounts": [{"id": str(m.get("mount_id", m.get("mount_dir", "unknown"))),
                                                            "status": str(m.get("status", "UNKNOWN")),
                                                            "executed": False} for m in mounts]},
    }


def make_interactive_dashboard(data: Mapping[str, Any]) -> str:
    """Return a self-contained, no-server/no-CDN HTML dashboard for file://."""
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    payload = payload.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")
    payload = payload.replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    template = r'''<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'">
<title>VIA Agent OS｜Skill 與 Token 儀表板</title>
<style>
:root{--blue:#4c78a8;--teal:#55a868;--coral:#c44e52;--purple:#8172b3;--gold:#ccb974;--cyan:#64b5cd;--bg:#f7f8f5;--sidebar:#fcfcf9;--panel:#fffefb;--line:#dbd9d3;--ink:#282725;--muted:#77736d;--shadow:0 4px 18px rgba(35,45,50,.055)}
*{box-sizing:border-box}body{margin:0;background:linear-gradient(135deg,#f7f8f5,#ecefeb);color:var(--ink);font:14px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}.app{display:grid;grid-template-columns:252px minmax(0,1fr);min-height:100vh}.side{background:linear-gradient(180deg,var(--sidebar),#f1f4f1);border-right:1px solid var(--line);padding:22px 16px;position:sticky;top:0;height:100vh;overflow:auto}.brand{font-size:18px;font-weight:750;letter-spacing:.01em}.subbrand{font-size:12px;color:var(--muted);margin:3px 0 22px}.nav{display:grid;gap:6px}.nav button,.action{font:inherit;border:1px solid transparent;background:transparent;color:var(--ink);text-align:left;padding:10px 12px;border-radius:9px;cursor:pointer}.nav button:hover,.nav button.active{background:#e8edf1;border-color:#d8e0e8;color:#274a68}.sidebox{background:rgba(255,255,255,.75);border:1px solid var(--line);border-radius:12px;padding:12px;margin-top:20px}.sidebox p{margin:4px 0;font-size:12px}.main{min-width:0;padding:26px clamp(16px,3vw,42px) 48px}.top{display:flex;justify-content:space-between;gap:16px;align-items:flex-start;margin-bottom:20px}.eyebrow{color:var(--blue);font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase}.top h1{margin:3px 0;font-size:clamp(22px,3vw,32px);letter-spacing:-.03em}.muted{color:var(--muted)}.pill{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--line);background:white;border-radius:99px;padding:5px 10px;font-size:12px;white-space:nowrap}.pill.good{color:#286b45;border-color:#cfe4d5;background:#f1faf3}.pill.warn{color:#805f13;border-color:#eadfb5;background:#fff9e8}.pill.bad{color:#9a3438;border-color:#efc9cb;background:#fff2f2}.grid{display:grid;gap:14px}.kpis{grid-template-columns:repeat(4,minmax(150px,1fr));margin:16px 0}.panel,.kpi{background:var(--panel);border:1px solid var(--line);border-radius:14px;box-shadow:var(--shadow)}.kpi{padding:16px}.kpi .label{font-size:12px;color:var(--muted)}.kpi .value{font-size:26px;font-weight:760;margin-top:6px}.kpi .hint{font-size:11px;color:var(--muted);margin-top:4px}.panel{padding:18px;margin:14px 0}.panel h2{margin:0 0 4px;font-size:17px}.panel h3{font-size:14px;margin:0 0 8px}.panelhead{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}.cols{grid-template-columns:minmax(0,1.2fr) minmax(260px,.8fr)}.bars{display:flex;align-items:flex-end;gap:8px;min-height:155px;padding:12px 4px 4px;border-bottom:1px solid var(--line)}.baritem{flex:1;min-width:25px;display:flex;flex-direction:column;align-items:center;gap:5px;height:140px;justify-content:flex-end}.bar{width:min(44px,76%);min-height:2px;background:linear-gradient(180deg,var(--cyan),var(--blue));border-radius:6px 6px 2px 2px}.baritem small{font-size:10px;color:var(--muted);text-align:center;overflow:hidden;max-width:100%}.callout{border-left:4px solid var(--gold);background:#fffaf0;padding:12px 14px;border-radius:5px 10px 10px 5px}.callout strong{display:block;margin-bottom:4px}.tablewrap{overflow:auto}table{width:100%;border-collapse:collapse;background:var(--panel);font-size:12px}th,td{padding:9px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}th{position:sticky;top:0;background:#f2f4f1;color:#5e5b55;font-weight:700}tr:hover td{background:#fafbf8}.skillgrid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.skillrow{width:100%;border:1px solid var(--line);border-radius:11px;background:#fffefb;padding:13px;text-align:left;font:inherit;cursor:pointer}.skillrow:hover,.skillrow.selected{border-color:var(--blue);box-shadow:0 0 0 2px rgba(76,120,168,.12)}.skilltitle{display:flex;justify-content:space-between;gap:10px;align-items:center}.skillrow p{margin:7px 0;color:var(--muted);font-size:12px}.toolbar{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}.toolbar input,.toolbar select,.sim input{border:1px solid var(--line);border-radius:8px;padding:9px 10px;font:inherit;background:white;color:var(--ink)}.toolbar input{min-width:220px;flex:1}.detail{white-space:pre-wrap;overflow:auto;max-height:360px;background:#f7f8f6;border:1px solid var(--line);border-radius:8px;padding:12px;font-size:11px}.action{background:var(--blue);color:white;border:0;text-align:center;padding:9px 12px}.action:hover{filter:brightness(.94)}.action.secondary{background:#e7edf2;color:#284c6c}.sim{display:flex;gap:8px;flex-wrap:wrap;align-items:center}.sim input{width:145px}.simresult{font-weight:700;color:var(--blue)}.empty{padding:20px;text-align:center;color:var(--muted);border:1px dashed var(--line);border-radius:10px}.foot{font-size:11px;color:var(--muted);padding:16px 3px}.hidden{display:none!important}.small{font-size:11px}.systemgrid{grid-template-columns:repeat(3,minmax(0,1fr))}.nowrap{white-space:nowrap}
@media(max-width:980px){.app{grid-template-columns:205px minmax(0,1fr)}.kpis{grid-template-columns:repeat(2,minmax(140px,1fr))}.cols{grid-template-columns:1fr}.systemgrid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:680px){.app{display:block}.side{position:relative;height:auto;padding:14px;border-right:0;border-bottom:1px solid var(--line)}.nav{grid-template-columns:repeat(4,minmax(0,1fr))}.nav button{text-align:center;font-size:11px;padding:9px 5px}.sidebox{display:none}.main{padding:18px 12px 32px}.top{display:block}.top>.pill{margin-top:10px}.skillgrid{grid-template-columns:1fr}.systemgrid{grid-template-columns:1fr}.kpis{gap:8px}.kpi{padding:12px}.kpi .value{font-size:21px}.panel{padding:13px}.toolbar input{min-width:100%}}
</style></head><body>
<script id="via-dashboard-data" type="application/json">__VIA_DATA__</script>
<div class="app"><aside class="side"><div class="brand">VIA Agent OS</div><div class="subbrand">Skills · Context · Token 效率</div>
<nav class="nav" aria-label="儀表板導覽"><button class="active" data-tab="overview">總覽</button><button data-tab="skills">八大 Skills</button><button data-tab="tokens">Token 用量</button><button data-tab="system">引擎／SSOT</button></nav>
<div class="sidebox"><strong>本機安全模式</strong><p>離線 HTML · 無 CDN · 無 API 呼叫</p><p>原始碼 AST：唯讀</p><p id="side-vcgc">VCGC：未連接</p></div><div class="sidebox"><strong>量測說明</strong><p>估算與供應商回報分開計算。</p><p>沒有紀錄時顯示「尚無實測」。</p></div></aside>
<main class="main"><header class="top"><div><div class="eyebrow">Local-first · Self-contained</div><h1>VIA Skill 與 Token 儀表板</h1><div class="muted" id="generated"></div></div><span class="pill good">本機靜態快照</span></header>
<section id="tab-overview"><div class="grid kpis" id="kpis"></div><div class="grid cols"><article class="panel"><div class="panelhead"><div><h2>上下文 Token 估算趨勢</h2><div class="muted small">來源：本機 metrics.jsonl；只呈現摘要數字，不含輸入內容。</div></div><span class="pill" id="metric-count"></span></div><div id="chart" class="bars"></div><div id="chart-empty" class="empty hidden">尚無已記錄的上下文量測</div></article><article class="panel"><h2>基線與資料可信度</h2><p id="baseline-text" class="muted"></p><div class="callout"><strong>內建示範（非專案實測）</strong><div id="demo-text"></div></div><p class="small muted">本機 estimator 是粗略估算；需以同一任務、同一模型的 provider usage 對照，才可計算實際 prompt-token 差異。</p></article></div>
<article class="panel"><div class="panelhead"><div><h2>八個 Skill 狀態摘要</h2><div class="muted small">Smoke test readiness 與實際執行紀錄分開呈現。</div></div><button class="action secondary" data-go="skills">查看技能</button></div><div class="tablewrap"><table><thead><tr><th>Skill</th><th>Smoke</th><th>實際執行次數</th><th>最近狀態</th><th>Skill 關聯 Context 節省</th></tr></thead><tbody id="overview-skills"></tbody></table></div></article></section>
<section id="tab-skills" class="hidden"><article class="panel"><div class="panelhead"><div><h2>VIA 核心 Skill Registry</h2><div class="muted small">按需搜尋、狀態篩選並檢視完整契約。</div></div><span class="pill" id="skill-total"></span></div><div class="toolbar"><input id="skill-search" type="search" placeholder="搜尋 ID、名稱、用途…" aria-label="搜尋技能"><select id="skill-filter" aria-label="技能狀態"><option value="all">全部</option><option value="ready">Smoke 通過</option><option value="run">已有實際執行</option><option value="notrun">尚未執行</option><option value="failed">Smoke 失敗</option></select></div><div class="grid cols"><div id="skill-list" class="skillgrid"></div><div class="panel"><h3 id="detail-title">選一個 Skill 查看</h3><div id="detail-status" class="muted small"></div><pre id="skill-detail" class="detail">契約內容會在此顯示；不會自動呼叫模型。</pre></div></div></article></section>
<section id="tab-tokens" class="hidden"><div class="grid kpis" id="token-kpis"></div><div class="grid cols"><article class="panel"><h2>用量紀錄</h2><p class="muted small">估算 context 節省與 provider 回報分區，不混加不同指標。</p><div class="tablewrap"><table><thead><tr><th>時間</th><th>事件</th><th>Skill / 模式</th><th>Token 數值（依事件）</th><th>來源</th></tr></thead><tbody id="metrics-table"></tbody></table></div><div id="metrics-empty" class="empty hidden">尚無執行／provider usage 記錄。可以用 Python CLI 的 --record-root 或 usage add 建立。</div></article><article class="panel"><h2>Token 節省試算器</h2><p class="muted small">手動輸入同一任務的基線與處理後 Token；此計算不會寫入實測紀錄。</p><div class="sim"><input type="number" min="0" id="sim-before" placeholder="基線 Token"><span>→</span><input type="number" min="0" id="sim-after" placeholder="處理後 Token"><button class="action" id="sim-run">計算</button></div><p class="simresult" id="sim-result">請輸入兩個非負數</p><button class="action secondary" id="export-metrics">匯出摘要 CSV</button></article></div></section>
<section id="tab-system" class="hidden"><div class="grid systemgrid" id="system-cards"></div><article class="panel"><h2>E1／E2／E3 Mount 狀態</h2><div class="tablewrap"><table><thead><tr><th>Mount ID</th><th>Manifest 狀態</th><th>執行</th></tr></thead><tbody id="mount-table"></tbody></table></div><div id="mount-empty" class="empty hidden">未發現 mount manifest；本頁只檢查宣告，不會執行命令。</div></article><article class="panel"><h2>操作邊界</h2><p class="muted">儀表板由 Python 單檔生成；HTML 使用內嵌 CSS/JavaScript，可用 file:// 開啟。沒有 server、fetch、WebSocket、CDN 或遠端套件。VCGC 沒有 repo／已驗證 mount 時維持未連接狀態。</p></article></section>
<footer class="foot">資料來源為產生當下的本機快照。Token estimator 僅供趨勢觀察；正式節省率以相同任務與模型的實際 usage、品質與延遲回歸測試為準。</footer></main></div>
<script>
(()=>{'use strict';
const D=JSON.parse(document.getElementById('via-dashboard-data').textContent);const $=s=>document.querySelector(s);const $$=s=>Array.from(document.querySelectorAll(s));
const fmt=n=>Number(n||0).toLocaleString('zh-Hant');const pct=n=>n===null||n===undefined?'—':`${Number(n).toFixed(1)}%`;
$('#generated').textContent=`工作區：${D.root_label} · 產生時間：${D.generated_at}`;$('#side-vcgc').textContent=`VCGC：${D.integration.vcgc_status}`;
const cards=[['核心 Skills',D.summary.skill_count,'契約與 smoke test'],['Self-test',D.selftest.ok?'PASS':'FAIL',`${D.selftest.tests_run} 項測試`],['Skill 執行紀錄',D.summary.skill_runs,'只計入已記錄的執行'],['估算 Context 節省',D.summary.context_events?`${fmt(D.summary.context_saved_tokens_est)} tokens`:'尚無實測',D.summary.context_events?`${pct(D.summary.context_saved_percent_est)} · heuristic`:'等待 --record-root 量測']];
function cardHtml(item){const e=document.createElement('article');e.className='kpi';const a=document.createElement('div');a.className='label';a.textContent=item[0];const b=document.createElement('div');b.className='value';b.textContent=String(item[1]);const c=document.createElement('div');c.className='hint';c.textContent=item[2];e.append(a,b,c);return e}
cards.forEach(x=>$('#kpis').append(cardHtml(x)));
const actualSaved=D.summary.actual_paired_count?`${fmt(D.summary.actual_prompt_saved_tokens)} prompt tokens`:'尚無配對基線';const actualPct=D.summary.actual_prompt_saved_percent===null?'需同任務 baseline':pct(D.summary.actual_prompt_saved_percent);
[['估算輸入前',fmt(D.summary.context_before_tokens_est),'heuristic'],['估算輸入後',fmt(D.summary.context_after_tokens_est),'heuristic'],['供應商回報 Prompt',D.summary.provider_events?fmt(D.summary.actual_prompt_tokens):'尚無實測','provider-reported'],['配對實際節省',actualSaved,actualPct]].forEach(x=>$('#token-kpis').append(cardHtml(x)));
$('#metric-count').textContent=`${D.summary.context_events} 筆 context · ${D.summary.provider_events} 筆 provider`;
$('#baseline-text').textContent=D.selftest.ok?`程式自測通過 ${D.selftest.tests_run} 項；八個 Skill smoke 狀態各自呈現。這不是實際模型流量。`:`Self-test 未通過（${D.selftest.failures} fail / ${D.selftest.errors} error），應停止註冊與上線。`;
$('#demo-text').textContent=`${D.demo_fixture.chars_before} → ${D.demo_fixture.chars_after} 字元；估算 ${D.demo_fixture.tokens_before_est} → ${D.demo_fixture.tokens_after_est} tokens（${pct(D.demo_fixture.saving_percent_est)}）。僅示範 JSON 空白壓縮，不能當成 VIA 節省承諾。`;
function addSkillRow(tbody,s){const tr=document.createElement('tr');[s.id,s.readiness,s.execution_count,s.last_status,s.associated_context_events?`${fmt(s.estimated_context_saved_tokens)} tokens`:"尚無關聯量測"].forEach(v=>{const td=document.createElement('td');td.textContent=String(v);tr.append(td)});tbody.append(tr)}
D.skills.forEach(s=>addSkillRow($('#overview-skills'),s));$('#skill-total').textContent=`${D.skills.length} 個技能`;
let selected=null;function renderSkills(){const q=$('#skill-search').value.trim().toLowerCase();const f=$('#skill-filter').value;const list=$('#skill-list');list.replaceChildren();const shown=D.skills.filter(s=>{const text=`${s.id} ${s.name} ${s.purpose}`.toLowerCase();return (!q||text.includes(q))&&(f==='all'||(f==='ready'&&s.readiness==='PASS')||(f==='run'&&s.execution_count>0)||(f==='notrun'&&s.execution_count===0)||(f==='failed'&&s.readiness!=='PASS'))});shown.forEach(s=>{const b=document.createElement('button');b.className='skillrow'+(selected===s.id?' selected':'');b.type='button';const head=document.createElement('div');head.className='skilltitle';const title=document.createElement('strong');title.textContent=s.id;const badge=document.createElement('span');badge.className='pill '+(s.readiness==='PASS'?'good':'bad');badge.textContent=`Smoke ${s.readiness}`;head.append(title,badge);const p=document.createElement('p');p.textContent=s.purpose;const small=document.createElement('div');small.className='small muted';small.textContent=`執行 ${s.execution_count} 次 · 最近：${s.last_status} · Context 節省估算 ${s.associated_context_events?fmt(s.estimated_context_saved_tokens)+' tokens':'尚無關聯量測'}`;b.append(head,p,small);b.addEventListener('click',()=>{selected=s.id;$('#detail-title').textContent=s.name;$('#detail-status').textContent=`Smoke: ${s.readiness} · 最近執行：${s.last_status} · 次數：${s.execution_count}`;$('#skill-detail').textContent=JSON.stringify(s.contract,null,2);renderSkills()});list.append(b)});if(!shown.length){const e=document.createElement('div');e.className='empty';e.textContent='沒有符合的 Skill';list.append(e)}}
$('#skill-search').addEventListener('input',renderSkills);$('#skill-filter').addEventListener('change',renderSkills);renderSkills();
function renderChart(){const el=$('#chart');el.replaceChildren();const groups={};D.metrics.filter(x=>x.event_type==='context').forEach(x=>{const day=String(x.timestamp||'').slice(0,10)||'未知';groups[day]=(groups[day]||0)+Number(x.saved_tokens_est||0)});const entries=Object.entries(groups).sort((a,b)=>a[0].localeCompare(b[0])).slice(-14);if(!entries.length){$('#chart-empty').classList.remove('hidden');return}$('#chart-empty').classList.add('hidden');const max=Math.max(1,...entries.map(x=>Math.abs(x[1])));entries.forEach(([day,value])=>{const item=document.createElement('div');item.className='baritem';const b=document.createElement('div');b.className='bar';b.style.height=`${Math.max(3,Math.abs(value)/max*120)}px`;b.title=`${day}: ${fmt(value)} estimated tokens`;b.style.background=value<0?'var(--coral)':'linear-gradient(180deg,var(--cyan),var(--blue))';const n=document.createElement('small');n.textContent=fmt(value);const d=document.createElement('small');d.textContent=day.slice(5);item.append(n,b,d);el.append(item)})}renderChart();
const eventRows=D.metrics.slice().reverse().slice(0,100);const tbody=$('#metrics-table');eventRows.forEach(e=>{const tr=document.createElement('tr');const vals=[e.timestamp||'',e.event_type||'',e.skill_id||e.mode||e.provider||'',e.event_type==='context'?`${fmt(e.before_tokens_est)} / ${fmt(e.after_tokens_est)}`:e.event_type==='provider_usage'?`${fmt(e.prompt_tokens)} / ${fmt(e.completion_tokens)}`:`${fmt(e.input_tokens_est)} / ${fmt(e.output_tokens_est)}`,e.source||''];vals.forEach(v=>{const td=document.createElement('td');td.textContent=String(v);tr.append(td)});tbody.append(tr)});if(!eventRows.length)$('#metrics-empty').classList.remove('hidden');
function sysCard(label,value,hint){const e=cardHtml([label,value,hint]);$('#system-cards').append(e)}sysCard('AST 模組',D.ast.count,D.ast.limit_reached?'已達掃描上限':'唯讀 AST overlay');sysCard('SSOT',D.integration.ssot.status,D.integration.ssot.schema);sysCard('Token policy',D.integration.token_policy,'單引擎替換模式');sysCard('VCGC',D.integration.vcgc_status,'無 repo 時不宣稱已連接');sysCard('略過／錯誤 metrics',D.malformed_metrics,'格式錯誤列已忽略');sysCard('核心測試',D.selftest.ok?'通過':'未通過',`${D.selftest.tests_run} tests`);
const mt=$('#mount-table');D.integration.mounts.forEach(m=>{const tr=document.createElement('tr');[m.id,m.status,m.executed?'是':'否'].forEach(x=>{const td=document.createElement('td');td.textContent=String(x);tr.append(td)});mt.append(tr)});if(!D.integration.mounts.length)$('#mount-empty').classList.remove('hidden');
$$('[data-tab]').forEach(btn=>btn.addEventListener('click',()=>{$$('[data-tab]').forEach(x=>x.classList.toggle('active',x===btn));$$('main section[id^="tab-"]').forEach(x=>x.classList.toggle('hidden',x.id!==`tab-${btn.dataset.tab}`))}));$$('[data-go]').forEach(btn=>btn.addEventListener('click',()=>document.querySelector(`[data-tab="${btn.dataset.go}"]`).click()));
$('#sim-run').addEventListener('click',()=>{const before=Number($('#sim-before').value),after=Number($('#sim-after').value);$('#sim-result').textContent=Number.isFinite(before)&&Number.isFinite(after)&&before>0&&after>=0?`估算節省 ${fmt(before-after)} tokens（${pct((before-after)/before*100)}）· 手動試算，不寫入紀錄`:'請輸入有效的基線與處理後 Token 數'});
$('#export-metrics').addEventListener('click',()=>{const rows=[['timestamp','event_type','skill_id','mode','before_tokens_est','after_tokens_est','saved_tokens_est','prompt_tokens','completion_tokens','source']];D.metrics.forEach(e=>rows.push([e.timestamp,e.event_type,e.skill_id||'',e.mode||'',e.before_tokens_est??'',e.after_tokens_est??'',e.saved_tokens_est??'',e.prompt_tokens??'',e.completion_tokens??'',e.source||'']));const csv=rows.map(r=>r.map(x=>'"'+String(x??'').replaceAll('"','""')+'"').join(',')).join('\r\n');const a=document.createElement('a');a.href=URL.createObjectURL(new Blob(['\ufeff'+csv],{type:'text/csv;charset=utf-8'}));a.download='via-token-metrics.csv';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)});
})();
</script></body></html>'''
    return template.replace("__VIA_DATA__", payload)


def upgrade_dashboard_document(document: str) -> str:
    """Extend the standalone page with acceptance and synthetic token benchmark views."""
    def replace_once(source: str, old: str, new: str) -> str:
        count = source.count(old)
        if count != 1:
            raise RuntimeError(f"dashboard template anchor count must be 1, found {count}: {old[:70]}")
        return source.replace(old, new, 1)

    document = replace_once(document,
        '<button data-tab="tokens">Token 用量</button><button data-tab="system">引擎／SSOT</button>',
        '<button data-tab="tokens">Token 用量</button><button data-tab="tests">驗收報告</button><button data-tab="system">引擎／SSOT</button>')
    document = replace_once(document, 'grid-template-columns:repeat(4,minmax(0,1fr))',
                             'grid-template-columns:repeat(5,minmax(0,1fr))')
    document = replace_once(document, '<th>Smoke</th><th>實際執行次數</th>',
                             '<th>Smoke</th><th>Acceptance</th><th>實際執行次數</th>')
    document = replace_once(document,
        '[s.id,s.readiness,s.execution_count,s.last_status,s.associated_context_events?`${fmt(s.estimated_context_saved_tokens)} tokens`:"尚無關聯量測"]',
        '[s.id,s.readiness,`${s.acceptance_status} ${s.acceptance_passed}/${s.acceptance_total}`,s.execution_count,s.last_status,s.associated_context_events?`${fmt(s.estimated_context_saved_tokens)} tokens`:"尚無關聯量測"]')
    document = replace_once(document,
        'badge.textContent=`Smoke ${s.readiness}`;head.append(title,badge);',
        'badge.textContent=`Smoke ${s.readiness} · Tests ${s.acceptance_status} ${s.acceptance_passed}/${s.acceptance_total}`;head.append(title,badge);')

    report_section = '''<section id="tab-tests" class="hidden">
<div class="grid kpis" id="acceptance-kpis"></div>
<article class="panel"><h2>八個 VIA 核心 Skill 自動驗收</h2><p class="muted small" id="acceptance-description"></p><div class="tablewrap"><table><thead><tr><th>Skill ID</th><th>Skill 名稱</th><th>結果</th><th>通過</th><th>案例數</th></tr></thead><tbody id="acceptance-skill-table"></tbody></table></div></article>
<article class="panel"><h2>逐案測試報告</h2><p class="muted small">案例使用合成 fixture；不呼叫網路、agent、子程序，不執行或修改來源碼。</p><div class="toolbar"><input id="case-search" type="search" placeholder="搜尋 Skill、case ID 或結果說明" aria-label="搜尋測試案例"><select id="case-filter" aria-label="篩選測試結果"><option value="all">全部狀態</option><option value="PASS">PASS</option><option value="FAIL">FAIL</option></select></div><div class="tablewrap"><table><thead><tr><th>Skill</th><th>Case ID</th><th>狀態</th><th>驗證內容</th><th>耗時 ms</th></tr></thead><tbody id="acceptance-case-table"></tbody></table></div></article>
<article class="panel"><h2>TokenEngine fixture benchmark</h2><p class="muted small" id="token-benchmark-note"></p><div class="tablewrap"><table><thead><tr><th>Fixture</th><th>模式</th><th>Token 前</th><th>Token 後</th><th>估算節省</th><th>有損</th><th>JSON round-trip</th></tr></thead><tbody id="token-benchmark-table"></tbody></table></div><p class="small muted">以上是測試 fixture 的 tokenizer 粗估，不代表真實模型帳單或 VCGC 生產節省；有損抽取只在明確 opt-in 測試中執行。</p></article>
</section>
'''
    document = replace_once(document, '<section id="tab-system"', report_section + '<section id="tab-system"')

    report_js = r'''
const AR=D.acceptance_report||{};
[['驗收狀態',AR.status||'UNKNOWN','確定性本機測試'],['Skills',AR.skill_count||0,'預期 8 個核心 Skills'],['通過案例',`${AR.passed_count||0}/${AR.case_count||0}`,'逐案例結果如下'],['失敗案例',AR.failed_count||0,'失敗時應阻擋上線']].forEach(x=>$('#acceptance-kpis').append(cardHtml(x)));
$('#acceptance-description').textContent=`${AR.execution_mode||'測試模式未提供'} · 產生時間：${AR.generated_at||'未知'}`;
function appendTextRow(body,values){const tr=document.createElement('tr');values.forEach(v=>{const td=document.createElement('td');td.textContent=String(v??'');tr.append(td)});body.append(tr)}
(AR.skills||[]).forEach(s=>appendTextRow($('#acceptance-skill-table'),[s.skill_id,s.name,s.status,`${s.passed}/${s.total}`,s.total]));
function renderAcceptanceCases(){const q=$('#case-search').value.trim().toLowerCase(),f=$('#case-filter').value,body=$('#acceptance-case-table');body.replaceChildren();const rows=(AR.cases||[]).filter(c=>{const hay=`${c.skill_id} ${c.case_id} ${c.detail}`.toLowerCase();return(!q||hay.includes(q))&&(f==='all'||c.status===f)});rows.forEach(c=>appendTextRow(body,[c.skill_id,c.case_id,c.status,c.detail,c.duration_ms]));if(!rows.length)appendTextRow(body,['—','—','—','沒有符合的案例','—'])}
$('#case-search').addEventListener('input',renderAcceptanceCases);$('#case-filter').addEventListener('change',renderAcceptanceCases);renderAcceptanceCases();
(D.token_benchmarks&&D.token_benchmarks.fixtures||[]).forEach(f=>appendTextRow($('#token-benchmark-table'),[f.fixture_id,f.mode,fmt(f.before_tokens_est),fmt(f.after_tokens_est),`${fmt(f.saved_tokens_est)} (${pct(f.saving_percent_est)})`,f.lossy?'是':'否',f.semantic_roundtrip===true?'PASS':f.semantic_roundtrip===false?'FAIL':'N/A']));
$('#token-benchmark-note').textContent=`${D.token_benchmarks&&D.token_benchmarks.label||'無 Token fixture'} · ${D.token_benchmarks&&D.token_benchmarks.fixture_count||0} 個合成案例`;
'''
    return replace_once(document, "})();\n</script></body></html>", report_js + "})();\n</script></body></html>")


def _atomic_html_write(path_value: str | Path, content: str, *, overwrite: bool = False) -> tuple[Path, str | None]:
    path = Path(path_value).expanduser().absolute()
    if not path.parent.exists() or not path.parent.is_dir():
        raise ValueError("dashboard output directory must already exist")
    if path.parent.is_symlink() or path.is_symlink():
        raise ValueError("refusing to write dashboard through symlinks")
    if path.exists() and not overwrite:
        raise FileExistsError("dashboard output exists; pass --overwrite to replace it with a backup")
    backup = None
    if path.exists():
        backup_path = path.with_name(path.name + ".bak." + _utc_stamp())
        with path.open("rb") as src, backup_path.open("xb") as dst:
            dst.write(src.read())
            dst.flush()
            os.fsync(dst.fileno())
        backup = str(backup_path)
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent,
                                         prefix="." + path.name + ".", suffix=".tmp", delete=False) as handle:
            temp_name = handle.name
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
        os.chmod(path, 0o644)
    finally:
        if temp_name and os.path.exists(temp_name):
            try:
                os.unlink(temp_name)
            except OSError:
                pass
    return path, backup


def cmd_selftest(_: argparse.Namespace) -> int:
    report = run_selftests()
    _json_print(report)
    return 0 if report["ok"] else 2


def cmd_skills(args: argparse.Namespace) -> int:
    if args.skill_action == "list":
        _json_print({"skills": [s.as_contract() for s in SKILLS]})
        return 0
    if args.skill_action == "test":
        report = run_skill_acceptance_suite()
        if args.out:
            output = Path(args.out).expanduser().absolute()
            if output.is_symlink() or output.parent.is_symlink():
                raise ValueError("refusing to write test report through symlinks")
            backup = None
            if output.exists():
                if not args.overwrite:
                    raise FileExistsError("test report exists; pass --overwrite to create a backup and replace")
                backup_path = output.with_name(output.name + ".bak." + _utc_stamp())
                with output.open("rb") as src, backup_path.open("xb") as dst:
                    dst.write(src.read())
                    dst.flush()
                    os.fsync(dst.fileno())
                backup = str(backup_path)
            _atomic_json_write(output, report)
            os.chmod(output, 0o644)
            _json_print({"status": "REPORT_WRITTEN" if report["status"] == "PASS" else "REPORT_WRITTEN_WITH_FAILURES",
                "out": str(output), "backup_path": backup, "skill_count": report["skill_count"],
                "case_count": report["case_count"], "passed_count": report["passed_count"],
                "failed_count": report["failed_count"], "suite_status": report["status"],
                "token_fixture_count": report["token_benchmarks"]["fixture_count"]})
        else:
            _json_print(report)
        return 0 if report["status"] == "PASS" else 2
    payload = _load_json_input(args.data, args.data_file)
    started = time.perf_counter()
    try:
        result = run_skill(args.skill_id, payload)
    except (KeyError, TypeError, ValueError) as exc:
        if args.record_root:
            append_metric(args.record_root, {"event_type": "skill", "skill_id": args.skill_id,
                "status": "ERROR", "input_tokens_est": estimate_tokens(json.dumps(payload, ensure_ascii=False)),
                "output_tokens_est": 0, "duration_ms": int((time.perf_counter() - started) * 1000),
                "source": "local_skill_runner"})
        _json_print({"status": "ERROR", "error": str(exc)})
        return 2
    if args.record_root:
        append_metric(args.record_root, {"event_type": "skill", "skill_id": args.skill_id,
            "status": str(result.get("status", "UNKNOWN")),
            "input_tokens_est": estimate_tokens(json.dumps(payload, ensure_ascii=False)),
            "output_tokens_est": estimate_tokens(json.dumps(result, ensure_ascii=False, default=str)),
            "duration_ms": int((time.perf_counter() - started) * 1000),
            "source": "local_skill_runner"})
    _json_print(result)
    return 0


def cmd_context(args: argparse.Namespace) -> int:
    input_path = Path(args.input).expanduser()
    if input_path.is_symlink() or not input_path.is_file():
        raise ValueError("context input must be a regular non-symlink file")
    if input_path.stat().st_size > MAX_CONTEXT_BYTES:
        raise ValueError(f"context input exceeds {MAX_CONTEXT_BYTES} byte safety limit")
    raw = input_path.read_text(encoding="utf-8")
    result = TokenEngine().prepare(raw, allow_lossy=args.allow_lossy,
                                   query=args.query, max_lines=args.max_lines)
    metric_written = None
    if args.record_root:
        metric_written = append_metric(args.record_root, {"event_type": "context",
            "timestamp": _dt.datetime.now(_dt.timezone.utc).isoformat(), "mode": result.mode,
            "lossy": result.lossy, "redacted_count": result.redacted_count,
            "before_tokens_est": result.tokens_before_est, "after_tokens_est": result.tokens_after_est,
            "saved_tokens_est": result.tokens_before_est - result.tokens_after_est,
            "savings_percent_est": result.estimated_savings_percent,
            "skill_id": args.skill_id or "", "source": "heuristic_local"})
    payload = result.as_dict()
    if args.include_text:
        payload["prepared_text"] = result.prepared_text
    else:
        payload.pop("prepared_text", None)
    if metric_written:
        payload["metric_recorded"] = metric_written
    _json_print(payload)
    return 0


def cmd_scan(args: argparse.Namespace) -> int:
    index = scan_project(args.root)
    if args.out:
        out = Path(args.out).expanduser()
        _atomic_json_write(out, index)
        _json_print({"status": "WRITTEN", "out": str(out), "count": index["count"],
                     "mode": index["mode"], "source_modified": False})
    else:
        _json_print(index)
    return 0


def cmd_mounts(args: argparse.Namespace) -> int:
    _json_print({"mounts": discover_mounts(args.root),
                 "note": "Manifest validation only; mount commands are never run."})
    return 0


def cmd_route(args: argparse.Namespace) -> int:
    _json_print(route_file(args.path))
    return 0


def cmd_usage_add(args: argparse.Namespace) -> int:
    event: dict[str, Any] = {"event_type": "provider_usage", "provider": args.provider,
        "model": args.model, "prompt_tokens": args.prompt_tokens,
        "completion_tokens": args.completion_tokens, "source": "provider_reported"}
    if args.baseline_prompt_tokens is not None:
        event["baseline_prompt_tokens"] = args.baseline_prompt_tokens
    if args.skill_id:
        event["skill_id"] = args.skill_id
    if args.request_id:
        event["request_id_hash"] = stable_hash(args.request_id)
    result = append_metric(args.root, event)
    _json_print({"status": "RECORDED", **result,
                 "note": "僅記錄供應商回報數字；不呼叫 API、不保存 prompt。baseline 需為同任務可比較值。"})
    return 0


def cmd_dashboard(args: argparse.Namespace) -> int:
    root = _safe_root(args.root)
    tests = run_selftests()
    acceptance = run_skill_acceptance_suite()
    ast_index = scan_project(root)
    mounts = discover_mounts(root)
    metrics, malformed = read_metric_log(root)
    data = build_dashboard_data(str(args.label or root.name)[:120], ast_index, tests, mounts, metrics,
                                malformed, _dashboard_ssot_info(root), acceptance)
    document = upgrade_dashboard_document(make_interactive_dashboard(data))
    output, backup = _atomic_html_write(args.out, document, overwrite=args.overwrite)
    _json_print({"status": "DASHBOARD_WRITTEN", "out": str(output), "file_uri": output.as_uri(),
        "backup_path": backup, "standalone": True, "external_requests": 0,
        "selftest_ok": tests["ok"], "skill_count": len(SKILLS),
        "acceptance_status": acceptance["status"], "acceptance_passed": acceptance["passed_count"],
        "acceptance_cases": acceptance["case_count"],
        "metric_events": len(metrics), "context_events": data["summary"]["context_events"],
        "provider_events": data["summary"]["provider_events"],
        "token_fixture_count": data["token_benchmarks"]["fixture_count"],
        "demo_fixture_only": data["demo_fixture"]["label"]})
    return 0


def cmd_bootstrap(args: argparse.Namespace) -> int:
    test_report = run_selftests()
    if not test_report["ok"]:
        _json_print({"status": "BLOCKED", "reason": "self-tests failed; SSOT not written", "test_report": test_report})
        return 2
    root = _safe_root(args.root)
    ast_index = scan_project(root)
    mounts = discover_mounts(root)
    payload = build_ssot_payload(ast_index, test_report, mounts)
    result = register_ssot(root, payload, apply=args.apply)
    report_html = make_html_report(ast_index, test_report)
    result.update({"selftest": test_report, "ast_modules": ast_index["count"],
                   "mounts": len(mounts), "report_html_preview_chars": len(report_html),
                   "token_engine_mode": "EXCLUSIVE_REPLACEMENT",
                   "vcgc": "UNVERIFIED_NOT_CONNECTED"})
    _json_print(result)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="via_agent_os.py",
        description="Single-file VIA eight-Skill engine; local-first, AST-read-only, tests-before-SSOT.")
    subs = parser.add_subparsers(dest="command", required=True)

    p_test = subs.add_parser("selftest", help="run deterministic unit tests")
    p_test.set_defaults(func=cmd_selftest)

    p_skills = subs.add_parser("skills", help="list or run one deterministic VIA Skill")
    skill_sub = p_skills.add_subparsers(dest="skill_action", required=True)
    p_list = skill_sub.add_parser("list", help="list the eight Skill contracts")
    p_list.set_defaults(func=cmd_skills)
    p_skill_test = skill_sub.add_parser("test", help="run deterministic acceptance tests for all eight Skills")
    p_skill_test.add_argument("--out", help="new JSON report path; existing files require --overwrite")
    p_skill_test.add_argument("--overwrite", action="store_true", help="backup an existing report before replacing")
    p_skill_test.set_defaults(func=cmd_skills)
    p_run = skill_sub.add_parser("run", help="run exactly one Skill; no recursion/agent calls")
    p_run.add_argument("skill_id", choices=sorted(SKILL_RUNNERS))
    p_run.add_argument("--data", help="input JSON object; avoid secrets")
    p_run.add_argument("--data-file", help="path to a JSON object input")
    p_run.add_argument("--record-root", help="opt in to append content-free execution metrics under <root>/.via")
    p_run.set_defaults(func=cmd_skills)

    p_context = subs.add_parser("context", help="measure/compact one text file; JSON lossless mode by default")
    p_context.add_argument("--input", required=True)
    p_context.add_argument("--query")
    p_context.add_argument("--allow-lossy", action="store_true", help="explicitly permit query-line extraction")
    p_context.add_argument("--max-lines", type=int, default=120)
    p_context.add_argument("--include-text", action="store_true", help="include prepared text in stdout")
    p_context.add_argument("--skill-id", choices=sorted(SKILL_RUNNERS), help="optional association for the context metric")
    p_context.add_argument("--record-root", help="opt in to append content-free estimates under <root>/.via")
    p_context.set_defaults(func=cmd_context)

    p_scan = subs.add_parser("scan", help="read-only AST inventory; never imports/executes modules")
    p_scan.add_argument("--root", required=True)
    p_scan.add_argument("--out", help="explicit output JSON path; omitted means stdout")
    p_scan.set_defaults(func=cmd_scan)

    p_mounts = subs.add_parser("mounts", help="validate E1/E2/E3 mount manifests without executing them")
    p_mounts.add_argument("--root", required=True)
    p_mounts.set_defaults(func=cmd_mounts)

    p_route = subs.add_parser("route", help="route by file extension only; never executes")
    p_route.add_argument("path")
    p_route.set_defaults(func=cmd_route)

    p_usage = subs.add_parser("usage", help="record provider-reported usage numbers; makes no API call")
    usage_sub = p_usage.add_subparsers(dest="usage_action", required=True)
    p_usage_add = usage_sub.add_parser("add", help="append actual provider usage to local metrics")
    p_usage_add.add_argument("--root", required=True)
    p_usage_add.add_argument("--provider", required=True)
    p_usage_add.add_argument("--model", required=True)
    p_usage_add.add_argument("--prompt-tokens", required=True, type=int)
    p_usage_add.add_argument("--completion-tokens", required=True, type=int)
    p_usage_add.add_argument("--baseline-prompt-tokens", type=int, help="same task/model baseline, if available")
    p_usage_add.add_argument("--skill-id", choices=sorted(SKILL_RUNNERS))
    p_usage_add.add_argument("--request-id", help="only a one-way hash is stored")
    p_usage_add.set_defaults(func=cmd_usage_add)

    p_dashboard = subs.add_parser("dashboard", help="generate standalone interactive HTML for file://")
    p_dashboard.add_argument("--root", required=True, help="existing VIA project directory")
    p_dashboard.add_argument("--out", required=True, help="new HTML output path; existing files require --overwrite")
    p_dashboard.add_argument("--label", help="optional snapshot label; does not change scanned root")
    p_dashboard.add_argument("--overwrite", action="store_true", help="backup an existing output before replacing")
    p_dashboard.set_defaults(func=cmd_dashboard)

    p_boot = subs.add_parser("bootstrap", help="selftest + AST index + SSOT merge; dry-run unless --apply")
    p_boot.add_argument("--root", required=True, help="existing VIA project directory; home/root is refused")
    p_boot.add_argument("--apply", action="store_true", help="create backup and update <root>/.via/ssot.json")
    p_boot.set_defaults(func=cmd_bootstrap)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        _json_print({"status": "BLOCKED", "error": str(exc), "writes_performed": False})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
