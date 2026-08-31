#!/usr/bin/env python3
"""MarkdownEditingEngine: safe polyglot Markdown repair orchestrator."""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import dataclasses
import datetime as dt
import hashlib
import html
import importlib.metadata as importlib_metadata
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

try:
    from engine.semantic_reconstruction import (
        RECONSTRUCTION_SCHEMA_VERSION,
        def_analyze_markdown_file,
        def_compare_reconstruction,
        def_safe_repair_markdown_text,
        def_write_reconstruction_indexes,
        def_write_structure_sidecar,
    )
except ModuleNotFoundError:  # direct script execution resolves modules from engine/
    from semantic_reconstruction import (
        RECONSTRUCTION_SCHEMA_VERSION,
        def_analyze_markdown_file,
        def_compare_reconstruction,
        def_safe_repair_markdown_text,
        def_write_reconstruction_indexes,
        def_write_structure_sidecar,
    )


# =============================================================================
# 參數區：所有可調整預設值集中於此，亦可由 config/engine.json 覆寫。
# =============================================================================

ENGINE_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = ENGINE_ROOT / "config" / "engine.json"
DEFAULT_TIMEOUT_SECONDS = 120
DEFAULT_MAX_WORKERS = 4
DEFAULT_FORMATTER = "prettier"
DEFAULT_ENCODING = "utf-8"
REPORT_SCHEMA_VERSION = "1.2"
TOC_START = "<!-- markdown-editing-engine:toc:start -->"
TOC_END = "<!-- markdown-editing-engine:toc:end -->"
SUPPORTED_EXTENSIONS = {".md", ".markdown", ".mdown", ".mkd"}
EXCLUDED_DIR_NAMES = {
    ".git",
    ".venv",
    "node_modules",
    "book",
    "dist",
    "reports",
    ".markdown-editing-backup",
    ".rumdl_cache",
}
SEMANTIC_KEYS = (
    "headings",
    "links",
    "images",
    "codeBlocks",
    "inlineCode",
    "frontmatter",
    "html",
    "textContentHash",
)
INLINE_LINK_TARGET_PATTERN = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
REFERENCE_TARGET_PATTERN = re.compile(r"^\s{0,3}\[[^\]]+\]:\s*(\S+)", re.MULTILINE)
HTML_TARGET_PATTERN = re.compile(r"\b(?:href|src)\s*=\s*['\"]([^'\"]+)['\"]", re.IGNORECASE)


@dataclasses.dataclass
class CommandResult:
    name: str
    command: list[str]
    exit_code: int
    duration_ms: int
    stdout: str
    stderr: str
    status: str


@dataclasses.dataclass
class FileResult:
    path: str
    status: str = "pending"
    changed: bool = False
    before_sha256: str = ""
    after_sha256: str = ""
    backup_path: str | None = None
    quarantine_path: str | None = None
    semantic_guard: str = "not-run"
    reconstruction_gate: str = "not-run"
    reconstruction_source_gate: str = "not-run"
    reconstruction_confidence: float = 0.0
    reconstruction_report_path: str | None = None
    reconstruction_findings: list[dict[str, Any]] = dataclasses.field(default_factory=list)
    tool_results: list[dict[str, Any]] = dataclasses.field(default_factory=list)
    warnings: list[str] = dataclasses.field(default_factory=list)
    errors: list[str] = dataclasses.field(default_factory=list)


def def_now_run_id() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def def_load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding=DEFAULT_ENCODING) as handle:
        return json.load(handle)


def def_load_config(path: Path) -> dict[str, Any]:
    config = def_load_json(path)
    if config.get("schema_version") not in {"1.0", "1.1", "1.2"}:
        raise ValueError(f"Unsupported config schema: {config.get('schema_version')}")
    required_sections = {"pipeline", "normalization", "mutators", "validators", "safety"}
    missing_sections = sorted(required_sections - config.keys())
    if missing_sections:
        raise ValueError(f"Missing config sections: {', '.join(missing_sections)}")
    if any(not isinstance(config[section], dict) for section in required_sections):
        raise ValueError("Config sections must be JSON objects")
    formatter = config["pipeline"].get("formatter")
    if formatter not in {"prettier", "mdformat", "rumdl", "pandoc", "none"}:
        raise ValueError(f"Unsupported pipeline formatter: {formatter}")
    workers = config["pipeline"].get("max_workers", DEFAULT_MAX_WORKERS)
    if not isinstance(workers, int) or isinstance(workers, bool) or not 1 <= workers <= 16:
        raise ValueError("pipeline.max_workers must be an integer from 1 to 16")
    timeout = config["pipeline"].get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS)
    if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout < 1:
        raise ValueError("pipeline.timeout_seconds must be a positive integer")
    return config


def def_sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def def_sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def def_resolve_executable(name: str) -> str | None:
    windows_suffix = ".cmd" if os.name == "nt" else ""
    candidates = [
        ENGINE_ROOT / "node_modules" / ".bin" / f"{name}{windows_suffix}",
        ENGINE_ROOT / ".venv" / ("Scripts" if os.name == "nt" else "bin") / (
            f"{name}.exe" if os.name == "nt" else name
        ),
        ENGINE_ROOT / "bin" / (f"{name}.exe" if os.name == "nt" else name),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    return shutil.which(name)


def def_python_package_version(name: str) -> str | None:
    try:
        return importlib_metadata.version(name)
    except importlib_metadata.PackageNotFoundError:
        return None


def def_node_package_path(name: str) -> str | None:
    candidate = ENGINE_ROOT / "node_modules" / name
    return str(candidate) if candidate.exists() else None


def def_node_package_version(name: str) -> str | None:
    package_json = ENGINE_ROOT / "node_modules" / name / "package.json"
    if not package_json.is_file():
        return None
    try:
        return str(def_load_json(package_json).get("version") or "") or None
    except (OSError, json.JSONDecodeError):
        return None


def def_tool_registry() -> dict[str, dict[str, Any]]:
    registry = {
        "prettier": {"executable": def_resolve_executable("prettier"), "role": "formatter"},
        "markdownlint-cli2": {
            "executable": def_resolve_executable("markdownlint-cli2"),
            "role": "fixer-validator",
        },
        "remark": {"executable": def_resolve_executable("remark"), "role": "ast-validator"},
        "prettier-plugin-lint-md": {
            "executable": str(ENGINE_ROOT / "node_modules" / "prettier-plugin-lint-md")
            if (ENGINE_ROOT / "node_modules" / "prettier-plugin-lint-md").exists()
            else None,
            "role": "zh-typography-plugin",
        },
        "mdast-util-from-markdown": {
            "executable": str(ENGINE_ROOT / "node_modules" / "mdast-util-from-markdown")
            if (ENGINE_ROOT / "node_modules" / "mdast-util-from-markdown").exists()
            else None,
            "role": "ast-library",
        },
        "rumdl": {"executable": def_resolve_executable("rumdl"), "role": "fast-fixer-validator"},
        "pymarkdown": {"executable": def_resolve_executable("pymarkdown"), "role": "strict-validator"},
        "mdformat": {"executable": def_resolve_executable("mdformat"), "role": "formatter-validator"},
        "markdown-table-fixer": {
            "executable": def_resolve_executable("markdown-table-fixer"),
            "role": "table-fixer",
        },
        "prettydiff": {
            "executable": def_resolve_executable("prettydiff"),
            "role": "legacy-optional",
            "note": "Unverified legacy adapter; never auto-installed or enabled.",
        },
        "pandoc": {"executable": def_resolve_executable("pandoc"), "role": "ast-validator-converter"},
        "mdbook": {"executable": def_resolve_executable("mdbook"), "role": "site-builder"},
        "node-ast-worker": {
            "executable": def_resolve_executable("node") if (ENGINE_ROOT / "node" / "ast_reorganizer.mjs").is_file() else None,
            "role": "reorganizer-semantic-guard",
        },
        "rust-mdscan": {"executable": def_resolve_executable("mdscan"), "role": "encoding-fence-validator"},
        "go-mdlinkcheck": {"executable": def_resolve_executable("mdlinkcheck"), "role": "local-link-validator"},
        "cspell": {"executable": def_resolve_executable("cspell"), "role": "offline-spelling-validator"},
        "remark-preset-lint-recommended": {
            "executable": def_node_package_path("remark-preset-lint-recommended"),
            "role": "remark-ast-rule-preset",
        },
        "mdformat-gfm": {
            "executable": sys.executable if def_python_package_version("mdformat-gfm") else None,
            "version": def_python_package_version("mdformat-gfm"),
            "role": "gfm-format-extension",
        },
        "mdformat-frontmatter": {
            "executable": sys.executable if def_python_package_version("mdformat-frontmatter") else None,
            "version": def_python_package_version("mdformat-frontmatter"),
            "role": "frontmatter-format-extension",
        },
        "mdit-py-plugins": {
            "executable": sys.executable if def_python_package_version("mdit-py-plugins") else None,
            "version": def_python_package_version("mdit-py-plugins"),
            "role": "independent-python-parser",
        },
        "semantic-reconstruction": {
            "executable": sys.executable,
            "version": RECONSTRUCTION_SCHEMA_VERSION,
            "role": "sentence-table-information-guard",
        },
    }
    capability_map = {
        "prettier": ["format", "gfm"],
        "markdownlint-cli2": ["lint", "fix"],
        "remark": ["ast", "lint"],
        "cspell": ["spell", "dictionary", "offline"],
        "mdit-py-plugins": ["parse", "gfm", "frontmatter", "tasklist"],
        "semantic-reconstruction": ["segment", "table-shape", "information", "evidence", "guard"],
        "rust-mdscan": ["encoding", "fence", "fast"],
        "go-mdlinkcheck": ["local-link", "offline"],
        "pandoc": ["ast", "convert"],
        "mdbook": ["publish", "site"],
    }
    package_version_map = {
        "prettier": ("node", "prettier"),
        "markdownlint-cli2": ("node", "markdownlint-cli2"),
        "remark": ("node", "remark-cli"),
        "prettier-plugin-lint-md": ("node", "prettier-plugin-lint-md"),
        "mdast-util-from-markdown": ("node", "mdast-util-from-markdown"),
        "cspell": ("node", "cspell"),
        "remark-preset-lint-recommended": ("node", "remark-preset-lint-recommended"),
        "rumdl": ("python", "rumdl"),
        "pymarkdown": ("python", "pymarkdownlnt"),
        "mdformat": ("python", "mdformat"),
        "markdown-table-fixer": ("python", "markdown-table-fixer"),
        "mdformat-gfm": ("python", "mdformat-gfm"),
        "mdformat-frontmatter": ("python", "mdformat-frontmatter"),
        "mdit-py-plugins": ("python", "mdit-py-plugins"),
    }
    for name, metadata in registry.items():
        version_source = package_version_map.get(name)
        if version_source and not metadata.get("version"):
            environment, package = version_source
            metadata["version"] = (
                def_node_package_version(package)
                if environment == "node"
                else def_python_package_version(package)
            )
        metadata.setdefault("capabilities", capability_map.get(name, [metadata["role"]]))
        metadata.setdefault("priority", 100 if name in {"prettier", "markdownlint-cli2", "node-ast-worker"} else 200)
        metadata.setdefault("cost", "low")
        metadata.setdefault("sla_ms", 5000)
        metadata.setdefault("optional", name not in {"prettier", "markdownlint-cli2", "node-ast-worker"})
        metadata.setdefault(
            "blocking",
            name not in {"mdformat", "markdown-table-fixer", "prettydiff", "mdbook"},
        )
        metadata.setdefault("mutates", metadata["role"] in {"formatter", "fixer-validator", "table-fixer"})
    return registry


def def_run_command(
    name: str,
    command: list[str],
    timeout_seconds: int,
    cwd: Path = ENGINE_ROOT,
    accepted_codes: set[int] | None = None,
) -> CommandResult:
    accepted = accepted_codes or {0}
    start = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding=DEFAULT_ENCODING,
            errors="replace",
            timeout=timeout_seconds,
            check=False,
        )
        exit_code = completed.returncode
        stdout = completed.stdout[-12000:]
        stderr = completed.stderr[-12000:]
        status = "ok" if exit_code in accepted else "issues"
    except subprocess.TimeoutExpired as error:
        exit_code = 124
        stdout = str(error.stdout or "")[-12000:]
        stderr = f"timeout after {timeout_seconds}s\n{error.stderr or ''}"[-12000:]
        status = "timeout"
    except OSError as error:
        exit_code = 127
        stdout = ""
        stderr = str(error)
        status = "unavailable"
    return CommandResult(
        name=name,
        command=command,
        exit_code=exit_code,
        duration_ms=round((time.perf_counter() - start) * 1000),
        stdout=stdout,
        stderr=stderr,
        status=status,
    )


def def_command_dict(result: CommandResult) -> dict[str, Any]:
    payload = dataclasses.asdict(result)
    payload["command"] = [Path(part).name if index == 0 else part for index, part in enumerate(result.command)]
    return payload


def def_discover_markdown_files(input_path: Path, recursive: bool) -> list[Path]:
    resolved = input_path.resolve()
    if resolved.is_file():
        if resolved.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported Markdown extension: {resolved.suffix}")
        return [resolved]
    if not resolved.is_dir():
        raise FileNotFoundError(resolved)
    iterator = resolved.rglob("*") if recursive else resolved.glob("*")
    files = []
    for candidate in iterator:
        if not candidate.is_file() or candidate.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        if any(part in EXCLUDED_DIR_NAMES for part in candidate.relative_to(resolved).parts):
            continue
        files.append(candidate.resolve())
    return sorted(files, key=lambda item: str(item).casefold())


def def_basic_normalize(path: Path, final_newline: bool) -> None:
    raw = path.read_bytes()
    if b"\x00" in raw:
        raise ValueError("NUL byte detected; file is not safe UTF-8 Markdown")
    text = raw.decode("utf-8-sig", errors="replace")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if final_newline:
        text = text.rstrip("\n") + "\n"
    path.write_text(text, encoding=DEFAULT_ENCODING, newline="\n")


def def_apply_reconstruction_repair(path: Path) -> CommandResult:
    start = time.perf_counter()
    source = path.read_text(encoding="utf-8-sig")
    repaired, audit = def_safe_repair_markdown_text(source)
    if audit["changed"]:
        path.write_text(repaired, encoding=DEFAULT_ENCODING, newline="\n")
    return CommandResult(
        name="semantic-reconstruction-safe-repair",
        command=["internal", "split-first-merge-never", str(path)],
        exit_code=0,
        duration_ms=round((time.perf_counter() - start) * 1000),
        stdout=json.dumps(audit, ensure_ascii=False),
        stderr="",
        status="ok",
    )


def def_python_signature(path: Path) -> dict[str, Any]:
    text = path.read_bytes().decode("utf-8-sig", errors="replace")
    text = re.sub(r"^(#{1,6})(?=[^#\s])", r"\1 ", text, flags=re.MULTILINE)
    headings = []
    links = []
    images = []
    code_blocks = []
    inline_code = re.findall(r"(?<!`)`([^`\n]+)`(?!`)", text)
    in_fence = False
    fence_marker = ""
    fence_language = ""
    fence_lines: list[str] = []
    visible_lines: list[str] = []
    for line in text.splitlines():
        fence_match = re.match(r"^\s*(`{3,}|~{3,})(.*)$", line)
        if fence_match:
            marker = fence_match.group(1)
            if not in_fence:
                in_fence = True
                fence_marker = marker[0]
                fence_language = fence_match.group(2).strip()
                fence_lines = []
            elif marker[0] == fence_marker:
                code_blocks.append({"lang": fence_language, "hash": def_sha256_bytes("\n".join(fence_lines).encode())})
                in_fence = False
            continue
        if in_fence:
            fence_lines.append(line)
            continue
        heading = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if heading:
            headings.append({"depth": len(heading.group(1)), "text": heading.group(2)})
        visible_lines.append(line)
    for match in re.finditer(r"(!?)\[([^\]]*)\]\(([^)\s]+)(?:\s+['\"][^'\"]*['\"])?\)", text):
        payload = {"text": match.group(2), "url": match.group(3)}
        (images if match.group(1) else links).append(payload)
    frontmatter = []
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end > 0:
            frontmatter.append(def_sha256_bytes(text[4:end].encode()))
    html_values = re.findall(r"<[^>]+>", text)
    return {
        "headings": headings,
        "links": links,
        "images": images,
        "codeBlocks": code_blocks,
        "inlineCode": inline_code,
        "frontmatter": frontmatter,
        "html": [def_sha256_bytes(item.encode()) for item in html_values],
        "textContentHash": def_sha256_bytes(re.sub(r"\s+", "", "\n".join(visible_lines)).encode()),
        "parser": "python-fallback",
    }


def def_semantic_signature(path: Path, registry: dict[str, dict[str, Any]], timeout_seconds: int) -> dict[str, Any]:
    node = registry["node-ast-worker"]["executable"]
    if node:
        command = [node, str(ENGINE_ROOT / "node" / "ast_reorganizer.mjs"), "signature", str(path)]
        result = def_run_command("node-ast-signature", command, timeout_seconds)
        if result.exit_code == 0:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                pass
    return def_python_signature(path)


def def_semantic_signature_for_guard(
    path: Path,
    registry: dict[str, dict[str, Any]],
    timeout_seconds: int,
    strip_managed_toc: bool,
) -> dict[str, Any]:
    if not strip_managed_toc:
        return def_semantic_signature(path, registry, timeout_seconds)
    text = path.read_text(encoding="utf-8-sig")
    pattern = re.compile(re.escape(TOC_START) + r".*?" + re.escape(TOC_END) + r"\s*", flags=re.DOTALL)
    stripped = pattern.sub("", text)
    with tempfile.NamedTemporaryFile(mode="w", suffix=path.suffix, encoding=DEFAULT_ENCODING, delete=False) as handle:
        handle.write(stripped)
        temporary = Path(handle.name)
    try:
        return def_semantic_signature(temporary, registry, timeout_seconds)
    finally:
        temporary.unlink(missing_ok=True)


def def_signatures_equal(before: dict[str, Any], after: dict[str, Any]) -> tuple[bool, list[str]]:
    differences = [key for key in SEMANTIC_KEYS if before.get(key) != after.get(key)]
    return not differences, differences


def def_apply_toc(path: Path, registry: dict[str, dict[str, Any]], timeout_seconds: int) -> CommandResult:
    node = registry["node-ast-worker"]["executable"]
    if not node:
        return CommandResult("node-toc", [], 127, 0, "", "Node AST worker unavailable", "unavailable")
    return def_run_command(
        "node-toc",
        [node, str(ENGINE_ROOT / "node" / "ast_reorganizer.mjs"), "toc", str(path)],
        timeout_seconds,
    )


def def_apply_mutators(
    path: Path,
    config: dict[str, Any],
    registry: dict[str, dict[str, Any]],
    formatter: str,
    add_toc: bool,
    timeout_seconds: int,
) -> list[CommandResult]:
    results: list[CommandResult] = []
    def_basic_normalize(path, bool(config["normalization"]["final_newline"]))
    if add_toc:
        results.append(def_apply_toc(path, registry, timeout_seconds))

    formatter_executable = registry.get(formatter, {}).get("executable")
    if formatter != "none" and not formatter_executable:
        results.append(CommandResult(formatter, [], 127, 0, "", "Selected formatter unavailable", "unavailable"))
    elif formatter == "prettier":
        command = [
            formatter_executable,
            "--config",
            str(ENGINE_ROOT / "config" / ".prettierrc.json"),
            "--write",
            str(path),
        ]
        if config["mutators"]["lint_md_chinese_typography"]:
            command[1:1] = ["--plugin=prettier-plugin-lint-md"]
        results.append(def_run_command("prettier", command, timeout_seconds))
    elif formatter == "mdformat":
        results.append(def_run_command("mdformat", [formatter_executable, str(path)], timeout_seconds))
    elif formatter == "rumdl":
        results.append(def_run_command("rumdl", [formatter_executable, "fmt", str(path)], timeout_seconds))
    elif formatter == "pandoc":
        converted = path.with_suffix(path.suffix + ".pandoc.tmp")
        command = [
            formatter_executable,
            "--from=gfm",
            "--to=gfm",
            "--sandbox",
            str(path),
            "--output",
            str(converted),
        ]
        result = def_run_command("pandoc-roundtrip", command, timeout_seconds)
        results.append(result)
        if result.exit_code == 0 and converted.is_file():
            os.replace(converted, path)
        elif converted.exists():
            converted.unlink()

    table_fixer = registry["markdown-table-fixer"]["executable"]
    if table_fixer and config["mutators"]["markdown_table_fixer"]:
        maximum_line_length = str(config.get("pipeline", {}).get("table_fixer_max_line_length", 10000))
        results.append(
            def_run_command(
                "markdown-table-fixer",
                [table_fixer, "lint", str(path), "--auto-fix", "--max-line-length", maximum_line_length],
                timeout_seconds,
                accepted_codes={0, 1},
            )
        )

    markdownlint = registry["markdownlint-cli2"]["executable"]
    if markdownlint and config["mutators"]["markdownlint_fix"]:
        results.append(
            def_run_command(
                "markdownlint-cli2-fix",
                [
                    markdownlint,
                    "--config",
                    str(ENGINE_ROOT / "config" / ".markdownlint-cli2.jsonc"),
                    "--fix",
                    str(path),
                ],
                timeout_seconds,
                accepted_codes={0, 1},
            )
        )
    if config.get("reconstruction", {}).get("safe_structure_repair", True):
        results.append(def_apply_reconstruction_repair(path))
    return results


def def_run_markdown_it_validator(path: Path) -> CommandResult:
    start = time.perf_counter()
    try:
        from markdown_it import MarkdownIt
        from mdit_py_plugins.footnote import footnote_plugin
        from mdit_py_plugins.front_matter import front_matter_plugin
        from mdit_py_plugins.tasklists import tasklists_plugin

        parser = MarkdownIt("commonmark", {"html": True})
        parser.enable("table").enable("strikethrough")
        parser.use(front_matter_plugin).use(footnote_plugin).use(tasklists_plugin)
        source = path.read_text(encoding="utf-8-sig")
        tokens = parser.parse(source)
        output = json.dumps(
            {"ok": True, "tokens": len(tokens), "parser": "markdown-it-py+mdit-py-plugins"},
            ensure_ascii=False,
        )
        return CommandResult(
            name="markdown-it-py",
            command=["python", "markdown-it-py+mdit-py-plugins", str(path)],
            exit_code=0,
            duration_ms=round((time.perf_counter() - start) * 1000),
            stdout=output,
            stderr="",
            status="ok",
        )
    except ImportError as error:
        return CommandResult(
            "markdown-it-py",
            [],
            127,
            round((time.perf_counter() - start) * 1000),
            "",
            str(error),
            "unavailable",
        )
    except Exception as error:  # parser errors must be reported, not crash the entire batch
        return CommandResult(
            "markdown-it-py",
            ["python", "markdown-it-py+mdit-py-plugins", str(path)],
            1,
            round((time.perf_counter() - start) * 1000),
            "",
            str(error),
            "issues",
        )


def def_run_validators(
    path: Path,
    config: dict[str, Any],
    registry: dict[str, dict[str, Any]],
    timeout_seconds: int,
) -> list[CommandResult]:
    results: list[CommandResult] = []

    def add_if_available(tool: str, command_tail: list[str], accepted: set[int] | None = None) -> None:
        if not config["validators"].get(tool, False):
            return
        executable = registry[tool]["executable"]
        if not executable:
            results.append(CommandResult(tool, [], 127, 0, "", "Tool unavailable", "unavailable"))
            return
        results.append(def_run_command(tool, [executable, *command_tail], timeout_seconds, accepted_codes=accepted))

    add_if_available(
        "markdownlint-cli2",
        ["--config", str(ENGINE_ROOT / "config" / ".markdownlint-cli2.jsonc"), str(path)],
    )
    add_if_available(
        "remark",
        [
            "--rc-path",
            str(ENGINE_ROOT / "config" / "remark.config.mjs"),
            "--frail",
            "--no-stdout",
            str(path),
        ],
    )
    add_if_available(
        "rumdl",
        ["check", "--no-cache", "--config", str(ENGINE_ROOT / "config" / "rumdl.toml"), str(path)],
    )
    add_if_available(
        "pymarkdown",
        [
            "--enable-extensions",
            "front-matter,markdown-tables,markdown-task-list-items,markdown-strikethrough",
            "--disable-rules",
            "md013,md025,md033,md041",
            "scan",
            str(path),
        ],
    )
    add_if_available("mdformat", ["--check", str(path)])
    add_if_available(
        "markdown-table-fixer",
        [
            "lint",
            str(path),
            "--check",
            "--max-line-length",
            str(config.get("pipeline", {}).get("table_fixer_max_line_length", 10000)),
        ],
    )
    add_if_available(
        "cspell",
        [
            "lint",
            "--root",
            str(path.parent),
            "--config",
            str(ENGINE_ROOT / "config" / "cspell.json"),
            "--no-gitignore",
            "--no-progress",
            "--no-summary",
            str(path),
        ],
    )
    if config["validators"].get("markdown-it-py", False):
        results.append(def_run_markdown_it_validator(path))

    pandoc = registry["pandoc"]["executable"]
    if config["validators"].get("pandoc"):
        if pandoc:
            with tempfile.NamedTemporaryFile(suffix=".native", delete=False) as handle:
                output_path = Path(handle.name)
            try:
                results.append(
                    def_run_command(
                        "pandoc",
                        [pandoc, "--from=gfm", "--to=native", "--sandbox", str(path), "--output", str(output_path)],
                        timeout_seconds,
                    )
                )
            finally:
                output_path.unlink(missing_ok=True)
        else:
            results.append(CommandResult("pandoc", [], 127, 0, "", "Tool unavailable", "unavailable"))

    node = registry["node-ast-worker"]["executable"]
    if config["validators"].get("node_ast"):
        if node:
            results.append(
                def_run_command(
                    "node-ast",
                    [node, str(ENGINE_ROOT / "node" / "ast_reorganizer.mjs"), "validate", str(path)],
                    timeout_seconds,
                )
            )
        else:
            results.append(CommandResult("node-ast", [], 127, 0, "", "Tool unavailable", "unavailable"))

    add_if_available("rust-mdscan", [str(path)])
    add_if_available("go-mdlinkcheck", [str(path)], accepted={0, 1})
    return results


def def_backup_file(source: Path, input_root: Path, backup_root: Path) -> Path:
    relative = def_relative_source_path(source, input_root)
    destination = backup_root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return destination


def def_relative_source_path(source: Path, input_root: Path) -> Path:
    return Path(source.name) if input_root.is_file() else source.relative_to(input_root)


def def_atomic_replace(source: Path, destination: Path) -> None:
    temporary = destination.with_name(f".{destination.name}.mde-{os.getpid()}.tmp")
    with source.open("rb") as read_handle, temporary.open("wb") as write_handle:
        shutil.copyfileobj(read_handle, write_handle)
        write_handle.flush()
        os.fsync(write_handle.fileno())
    shutil.copymode(destination, temporary)
    os.replace(temporary, destination)


def def_stage_local_link_targets(source: Path, staged: Path, stage_root: Path) -> list[str]:
    """Copy existing relative link targets so staged validators keep source context."""
    text = source.read_bytes().decode("utf-8-sig", errors="replace")
    copied: list[str] = []
    candidates = [
        *INLINE_LINK_TARGET_PATTERN.findall(text),
        *REFERENCE_TARGET_PATTERN.findall(text),
        *HTML_TARGET_PATTERN.findall(text),
    ]
    for raw_target in candidates:
        stripped_target = raw_target.strip()
        if stripped_target.startswith("<") and ">" in stripped_target:
            target = stripped_target[1 : stripped_target.index(">")]
        else:
            target = stripped_target.split(maxsplit=1)[0]
        target = target.split("#", 1)[0].split("?", 1)[0]
        if not target or target.startswith(("#", "/", "\\")) or re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target):
            continue
        source_target = (source.parent / target).resolve()
        if not source_target.is_file():
            continue
        staged_target = (staged.parent / target).resolve()
        try:
            staged_target.relative_to(stage_root.resolve())
        except ValueError:
            continue
        staged_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_target, staged_target)
        copied.append(target)
    return sorted(set(copied))


def def_process_file(
    source: Path,
    input_root: Path,
    action: str,
    formatter: str,
    add_toc: bool,
    dry_run: bool,
    strict: bool,
    config: dict[str, Any],
    registry: dict[str, dict[str, Any]],
    backup_root: Path,
    quarantine_root: Path,
    timeout_seconds: int,
    reconstruction_root: Path | None = None,
) -> FileResult:
    result = FileResult(path=str(source))
    result.before_sha256 = def_sha256_file(source)
    try:
        source.read_bytes().decode("utf-8-sig")
    except UnicodeDecodeError:
        result.warnings.append("Invalid UTF-8 bytes repaired with U+FFFD replacement characters")
    with tempfile.TemporaryDirectory(prefix="markdown-editing-engine-") as temp_directory:
        stage_root = Path(temp_directory) / "workspace"
        stage_root.mkdir(parents=True, exist_ok=True)
        staged_relative = def_relative_source_path(source, input_root)
        staged = stage_root / staged_relative
        staged.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, staged)
        def_stage_local_link_targets(source, staged, stage_root)
        before_reconstruction = def_analyze_markdown_file(source)
        before_signature = def_semantic_signature_for_guard(source, registry, timeout_seconds, add_toc)
        if action in {"fix", "reorganize", "all"}:
            mutators = def_apply_mutators(staged, config, registry, formatter, add_toc, timeout_seconds)
            result.tool_results.extend(def_command_dict(item) for item in mutators)
            failed_mutators = [item.name for item in mutators if item.status in {"timeout", "unavailable"}]
            if failed_mutators and config["safety"]["fail_on_missing_selected_mutator"]:
                result.errors.append(f"Required mutator unavailable/timeout: {', '.join(failed_mutators)}")

        after_signature = def_semantic_signature_for_guard(staged, registry, timeout_seconds, add_toc)
        after_reconstruction = def_analyze_markdown_file(staged)
        reconstruction_comparison = def_compare_reconstruction(before_reconstruction, after_reconstruction)
        result.reconstruction_gate = (
            "passed"
            if reconstruction_comparison["passed"]
            else f"failed:{','.join(reconstruction_comparison['differences'])}"
        )
        result.reconstruction_source_gate = after_reconstruction["gate"]
        result.reconstruction_confidence = after_reconstruction["confidence"]
        result.reconstruction_findings = [
            item for item in after_reconstruction["findings"] if item["severity"] in {"error", "warning"}
        ][:100]
        if not reconstruction_comparison["passed"]:
            result.errors.append(
                "Reconstruction guard rejected changes in: "
                + ", ".join(reconstruction_comparison["differences"])
            )
        reconstruction_config = config.get("reconstruction", {})
        if after_reconstruction["gate"] == "FAIL" and reconstruction_config.get("fail_on_fail", True):
            result.errors.append("Reconstruction source gate failed")
        elif after_reconstruction["gate"] == "REVIEW":
            result.warnings.append("Reconstruction findings require review")
            if strict and reconstruction_config.get("fail_on_review_in_strict", True):
                result.errors.append("Strict reconstruction review gate failed")
        if reconstruction_root is not None and reconstruction_config.get("write_sidecar", True):
            relative = def_relative_source_path(source, input_root)
            sidecar_path = reconstruction_root / relative.parent / f"{relative.name}.structure.json"
            sidecar_payload = {
                "schema_version": RECONSTRUCTION_SCHEMA_VERSION,
                "source_path": str(source),
                "before_sha256": result.before_sha256,
                "after_sha256": def_sha256_file(staged),
                "analysis": after_reconstruction,
                "comparison": reconstruction_comparison,
                "failure_catalog": str(ENGINE_ROOT / "config" / "reconstruction_rules.json"),
            }
            def_write_structure_sidecar(sidecar_path, sidecar_payload)
            result.reconstruction_report_path = str(sidecar_path)
        semantics_equal, differences = def_signatures_equal(before_signature, after_signature)
        result.semantic_guard = "passed" if semantics_equal else f"failed:{','.join(differences)}"
        if not semantics_equal:
            result.errors.append(f"Semantic guard rejected changes in: {', '.join(differences)}")
            quarantine = quarantine_root / def_relative_source_path(source, input_root)
            quarantine.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(staged, quarantine)
            result.quarantine_path = str(quarantine)

        validator_results = def_run_validators(staged, config, registry, timeout_seconds)
        result.tool_results.extend(def_command_dict(item) for item in validator_results)
        issue_tools = [item.name for item in validator_results if item.status == "issues"]
        unavailable_tools = [item.name for item in validator_results if item.status in {"unavailable", "timeout"}]
        result_to_registry = {
            "node-ast": "node-ast-worker",
            "markdown-it-py": "mdit-py-plugins",
        }
        blocking_issue_tools = [
            name
            for name in issue_tools
            if registry.get(result_to_registry.get(name, name), {}).get("blocking", True) or name == formatter
        ]
        unavailable_required = [
            name
            for name in unavailable_tools
            if not registry.get(result_to_registry.get(name, name), {}).get("optional", True)
        ]
        if issue_tools:
            result.warnings.append(f"Validator issues: {', '.join(issue_tools)}")
        # Optional runtime absence is recorded in tool_results and doctor, but is
        # not a document defect and must not turn a clean file into a warning.
        if unavailable_required:
            result.warnings.append(f"Required validators unavailable/timeout: {', '.join(unavailable_required)}")
        if strict and (blocking_issue_tools or unavailable_required):
            details = sorted({*blocking_issue_tools, *unavailable_required})
            result.errors.append(f"Strict validation gate failed: {', '.join(details)}")

        result.after_sha256 = def_sha256_file(staged)
        result.changed = result.before_sha256 != result.after_sha256
        if result.errors:
            result.status = "failed"
            return result
        if action in {"check", "analyze-structure"}:
            result.status = "issues" if blocking_issue_tools else ("warnings" if issue_tools else "ok")
            return result
        if result.changed and not dry_run:
            if config["safety"].get("backup_before_replace", True):
                backup = def_backup_file(source, input_root, backup_root)
                result.backup_path = str(backup)
            def_atomic_replace(staged, source)
        result.status = "dry-run" if dry_run and result.changed else ("changed" if result.changed else "unchanged")
    return result


def def_build_book(input_path: Path, output_path: Path, registry: dict[str, dict[str, Any]], timeout_seconds: int) -> CommandResult:
    mdbook = registry["mdbook"]["executable"]
    if not mdbook:
        return CommandResult("mdbook", [], 127, 0, "", "mdBook unavailable", "unavailable")
    source_root = output_path / "src"
    source_root.mkdir(parents=True, exist_ok=True)
    files = def_discover_markdown_files(input_path, recursive=True)
    entries = []
    for source in files:
        relative = Path(source.name) if input_path.is_file() else source.relative_to(input_path)
        destination = source_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        title_match = re.search(r"^#\s+(.+)$", source.read_text(encoding="utf-8-sig"), flags=re.MULTILINE)
        title = title_match.group(1).strip() if title_match else source.stem
        entries.append((title, relative.as_posix(), len(relative.parts) - 1))
    summary_lines = ["# Summary", ""]
    for title, relative, depth in entries:
        summary_lines.append(f"{'  ' * depth}- [{title}]({relative})")
    (source_root / "SUMMARY.md").write_text("\n".join(summary_lines) + "\n", encoding=DEFAULT_ENCODING)
    book_toml = "[book]\nlanguage = \"zh-TW\"\nmultilingual = false\nsrc = \"src\"\ntitle = \"MarkdownEditingEngine Output\"\n"
    (output_path / "book.toml").write_text(book_toml, encoding=DEFAULT_ENCODING)
    return def_run_command("mdbook", [mdbook, "build", str(output_path)], timeout_seconds)


def def_doctor(registry: dict[str, dict[str, Any]]) -> dict[str, Any]:
    tools = []
    for name, metadata in registry.items():
        tools.append(
            {
                "name": name,
                "role": metadata["role"],
                "available": bool(metadata.get("executable")),
                "location": metadata.get("executable"),
                "version": metadata.get("version"),
                "capabilities": metadata.get("capabilities", []),
                "priority": metadata.get("priority"),
                "cost": metadata.get("cost"),
                "sla_ms": metadata.get("sla_ms"),
                "optional": metadata.get("optional"),
                "blocking": metadata.get("blocking"),
                "mutates": metadata.get("mutates"),
                "note": metadata.get("note"),
            }
        )
    return {"engine_root": str(ENGINE_ROOT), "python": sys.version, "tools": tools}


def def_write_report(report: dict[str, Any], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = report_path.with_suffix(report_path.suffix + ".tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding=DEFAULT_ENCODING)
    os.replace(temporary, report_path)


def def_write_backup_hash_chain(file_results: list[dict[str, Any]], backup_root: Path, run_id: str) -> Path | None:
    eligible = sorted(
        (item for item in file_results if item.get("backup_path")),
        key=lambda item: item["path"].casefold(),
    )
    if not eligible:
        return None
    backup_root.mkdir(parents=True, exist_ok=True)
    chain_path = backup_root / "backup_hash_chain.jsonl"
    previous_hash = "0" * 64
    lines = []
    for sequence, item in enumerate(eligible, start=1):
        payload = {
            "run_id": run_id,
            "sequence": sequence,
            "path": item["path"],
            "backup_path": item["backup_path"],
            "before_sha256": item["before_sha256"],
            "after_sha256": item["after_sha256"],
            "previous_hash": previous_hash,
        }
        canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        entry_hash = def_sha256_bytes((previous_hash + canonical).encode(DEFAULT_ENCODING))
        payload["entry_hash"] = entry_hash
        lines.append(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        previous_hash = entry_hash
    temporary = chain_path.with_suffix(".tmp")
    temporary.write_text("\n".join(lines) + "\n", encoding=DEFAULT_ENCODING)
    os.replace(temporary, chain_path)
    return chain_path


def def_write_html_report(report: dict[str, Any], html_path: Path) -> None:
    summary = report.get("summary", {})
    summary_cards = "".join(
        f'<div class="card"><span>{html.escape(str(key))}</span><strong>{html.escape(str(value))}</strong></div>'
        for key, value in summary.items()
    )
    rows = []
    for item in report.get("files", []):
        rows.append(
            "<tr>"
            f"<td>{html.escape(item['path'])}</td>"
            f"<td>{html.escape(item['status'])}</td>"
            f"<td>{'Yes' if item['changed'] else 'No'}</td>"
            f"<td>{html.escape(item['semantic_guard'])}</td>"
            f"<td>{html.escape(item.get('reconstruction_source_gate', 'not-run'))}</td>"
            f"<td>{html.escape(str(item.get('reconstruction_confidence', 0.0)))}</td>"
            f"<td>{html.escape('; '.join(item.get('warnings', [])))}</td>"
            f"<td>{html.escape('; '.join(item.get('errors', [])))}</td>"
            "</tr>"
        )
    tool_rows = []
    for tool in report.get("doctor", {}).get("tools", []):
        tool_rows.append(
            "<tr>"
            f"<td>{html.escape(tool['name'])}</td>"
            f"<td>{html.escape(tool['role'])}</td>"
            f"<td>{'Ready' if tool['available'] else 'Unavailable'}</td>"
            f"<td>{html.escape(', '.join(tool.get('capabilities', [])))}</td>"
            "</tr>"
        )
    document = f"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MarkdownEditingEngine {html.escape(report.get('run_id', ''))}</title>
<style>
body{{margin:0;background:#f5f7fb;color:#18212f;font:13px Inter,'Noto Sans TC',sans-serif}}main{{max-width:1440px;margin:auto;padding:20px}}
h1{{font-size:22px;margin:0 0 4px}}.sub{{color:#657186;margin-bottom:16px}}.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px;margin:12px 0}}
.card{{background:white;border:1px solid #dce3ed;border-radius:8px;padding:10px}}.card span{{display:block;color:#657186;font-size:11px}}.card strong{{font-size:20px}}
section{{background:white;border:1px solid #dce3ed;border-radius:10px;padding:12px;margin-top:12px;overflow:auto}}table{{width:100%;border-collapse:collapse}}th,td{{padding:7px;border-bottom:1px solid #e7ebf1;text-align:left;vertical-align:top}}th{{background:#f8fafc;position:sticky;top:0}}
</style></head><body><main><h1>MarkdownEditingEngine · v1.2</h1><div class="sub">Run {html.escape(report.get('run_id', ''))} · {html.escape(report.get('action', ''))}</div>
<div class="cards">{summary_cards}</div><section><h2>檔案結果</h2><table><thead><tr><th>Path</th><th>Status</th><th>Changed</th><th>Semantic Guard</th><th>Reconstruction</th><th>Confidence</th><th>Warnings</th><th>Errors</th></tr></thead><tbody>{''.join(rows)}</tbody></table></section>
<section><h2>工具矩陣</h2><table><thead><tr><th>Tool</th><th>Role</th><th>State</th><th>Capabilities</th></tr></thead><tbody>{''.join(tool_rows)}</tbody></table></section></main></body></html>"""
    temporary = html_path.with_suffix(html_path.suffix + ".tmp")
    temporary.write_text(document, encoding=DEFAULT_ENCODING)
    os.replace(temporary, html_path)


def def_write_csv_report(report: dict[str, Any], csv_path: Path) -> None:
    temporary = csv_path.with_suffix(csv_path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "file",
                "file_status",
                "changed",
                "semantic_guard",
                "reconstruction_gate",
                "reconstruction_source_gate",
                "reconstruction_confidence",
                "tool",
                "tool_status",
                "exit_code",
                "duration_ms",
            ],
        )
        writer.writeheader()
        for item in report.get("files", []):
            tool_results = item.get("tool_results", []) or [{}]
            for tool in tool_results:
                writer.writerow(
                    {
                        "file": item["path"],
                        "file_status": item["status"],
                        "changed": item["changed"],
                        "semantic_guard": item["semantic_guard"],
                        "reconstruction_gate": item.get("reconstruction_gate", "not-run"),
                        "reconstruction_source_gate": item.get("reconstruction_source_gate", "not-run"),
                        "reconstruction_confidence": item.get("reconstruction_confidence", 0.0),
                        "tool": tool.get("name", ""),
                        "tool_status": tool.get("status", ""),
                        "exit_code": tool.get("exit_code", ""),
                        "duration_ms": tool.get("duration_ms", ""),
                    }
                )
    os.replace(temporary, csv_path)


def def_write_report_bundle(report: dict[str, Any], report_path: Path, config: dict[str, Any]) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    reporting = config.get("reporting", {})
    artifacts = report.setdefault("artifacts", {})
    artifacts["json"] = str(report_path)
    if reporting.get("html", True):
        html_path = report_path.with_suffix(".html")
        artifacts["html"] = str(html_path)
        def_write_html_report(report, html_path)
    if reporting.get("csv", True):
        csv_path = report_path.with_suffix(".csv")
        artifacts["csv"] = str(csv_path)
        def_write_csv_report(report, csv_path)
    def_write_report(report, report_path)


def def_parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="安全、可稽核的多語言 Markdown 重組與修復引擎")
    parser.add_argument(
        "action",
        choices=["doctor", "check", "analyze-structure", "fix", "reorganize", "build-book", "all"],
    )
    parser.add_argument("--input", type=Path, help="Markdown 檔案或資料夾")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--formatter", choices=["prettier", "mdformat", "rumdl", "pandoc", "none"])
    parser.add_argument("--recursive", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--toc", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--workers", type=int, help="平行處理檔案數；預設由設定檔控制")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--book-output", type=Path)
    return parser.parse_args(argv)


def def_main(argv: list[str] | None = None) -> int:
    args = def_parse_arguments(argv)
    config = def_load_config(args.config.resolve())
    registry = def_tool_registry()
    run_id = def_now_run_id()
    formatter = args.formatter or config["pipeline"]["formatter"] or DEFAULT_FORMATTER
    timeout_seconds = int(config["pipeline"].get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS))
    requested_workers = args.workers if args.workers is not None else config["pipeline"].get("max_workers", DEFAULT_MAX_WORKERS)
    max_workers = max(1, min(int(requested_workers), 16))
    report_path = (args.report or (ENGINE_ROOT / "reports" / f"run-{run_id}.json")).resolve()

    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "run_id": run_id,
        "started_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "action": args.action,
        "formatter": formatter,
        "dry_run": args.dry_run,
        "strict": args.strict,
        "max_workers": max_workers,
        "doctor": def_doctor(registry),
        "files": [],
    }
    if args.action == "doctor":
        report["summary"] = {"available": sum(item["available"] for item in report["doctor"]["tools"])}
        def_write_report_bundle(report, report_path, config)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    if not args.input:
        raise ValueError("--input is required for this action")

    input_path = args.input.resolve()
    if args.action == "build-book":
        output = (args.book_output or (ENGINE_ROOT / "book-output" / run_id)).resolve()
        build_result = def_build_book(input_path, output, registry, timeout_seconds)
        report["book"] = def_command_dict(build_result) | {"output": str(output)}
        report["summary"] = {"status": build_result.status}
        def_write_report_bundle(report, report_path, config)
        print(str(report_path))
        return 0 if build_result.exit_code == 0 else 2

    files = def_discover_markdown_files(input_path, args.recursive)
    backup_root = ENGINE_ROOT / ".markdown-editing-backup" / run_id
    quarantine_root = ENGINE_ROOT / "reports" / "quarantine" / run_id
    reconstruction_root = ENGINE_ROOT / "reports" / "reconstruction" / run_id
    add_toc = args.toc if args.toc is not None else bool(config["pipeline"]["add_toc"])

    def process_source(source: Path) -> FileResult:
        try:
            return def_process_file(
                source=source,
                input_root=input_path,
                action=args.action,
                formatter=formatter,
                add_toc=add_toc or args.action == "reorganize",
                dry_run=args.dry_run,
                strict=args.strict,
                config=config,
                registry=registry,
                backup_root=backup_root,
                quarantine_root=quarantine_root,
                timeout_seconds=timeout_seconds,
                reconstruction_root=reconstruction_root,
            )
        except Exception as error:  # isolate a bad file instead of aborting the batch
            failed = FileResult(path=str(source), status="failed")
            failed.before_sha256 = def_sha256_file(source) if source.is_file() else ""
            failed.errors.append(f"Unhandled per-file error: {type(error).__name__}: {error}")
            return failed

    effective_workers = min(max_workers, max(1, len(files)))
    report["effective_workers"] = effective_workers
    if effective_workers == 1:
        file_results = [process_source(source) for source in files]
    else:
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=effective_workers,
            thread_name_prefix="markdown-editing",
        ) as executor:
            file_results = list(executor.map(process_source, files))
    report["files"] = [dataclasses.asdict(item) for item in file_results]

    if args.action == "all" and config["pipeline"]["build_book_after_all"]:
        output = (args.book_output or (ENGINE_ROOT / "book-output" / run_id)).resolve()
        report["book"] = def_command_dict(def_build_book(input_path, output, registry, timeout_seconds)) | {
            "output": str(output)
        }
    statuses = [item["status"] for item in report["files"]]
    report["summary"] = {
        "files": len(statuses),
        "changed": statuses.count("changed"),
        "unchanged": statuses.count("unchanged"),
        "dry_run": statuses.count("dry-run"),
        "issues": statuses.count("issues"),
        "nonblocking_issues": statuses.count("warnings"),
        "warning_files": sum(bool(item["warnings"]) for item in report["files"]),
        "failed": statuses.count("failed"),
        "reconstruction_pass": sum(item["reconstruction_source_gate"] == "PASS" for item in report["files"]),
        "reconstruction_review": sum(item["reconstruction_source_gate"] == "REVIEW" for item in report["files"]),
        "reconstruction_fail": sum(item["reconstruction_source_gate"] == "FAIL" for item in report["files"]),
    }
    reconstruction_artifacts = def_write_reconstruction_indexes(reconstruction_root)
    if reconstruction_artifacts:
        report.setdefault("artifacts", {}).update(reconstruction_artifacts)
    if config.get("reporting", {}).get("backup_hash_chain", True):
        chain_path = def_write_backup_hash_chain(report["files"], backup_root, run_id)
        if chain_path:
            report.setdefault("artifacts", {})["backup_hash_chain"] = str(chain_path)
    report["completed_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    def_write_report_bundle(report, report_path, config)
    print(str(report_path))
    return 2 if report["summary"]["failed"] else (1 if args.strict and report["summary"]["issues"] else 0)


if __name__ == "__main__":
    try:
        raise SystemExit(def_main())
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as error:
        print(f"MarkdownEditingEngine error: {error}", file=sys.stderr)
        raise SystemExit(2) from error
