#!/usr/bin/env python3
"""VIA governed AI instruction registry, AST index and handoff utility.

The tool intentionally uses only the Python standard library.  It is an overlay
for the existing VIA registry: it never renames, deletes, or promotes engines.
"""

from __future__ import annotations

# ============================================================================
# 01. PARAMETERS
# ============================================================================

import argparse
import ast
import contextlib
import datetime as dt
import hashlib
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Iterator, Sequence


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PACKAGE_ROOT / "config"
MODULES_DIR = PACKAGE_ROOT / "modules"
REGISTRY_DIR = PACKAGE_ROOT / "registry"
SCHEMAS_DIR = PACKAGE_ROOT / "schemas"
TEMPLATES_DIR = PACKAGE_ROOT / "templates"
OUTPUT_DIR = PACKAGE_ROOT / "outputs"

REGISTRY_PATH = REGISTRY_DIR / "ai_module_registry.v0100.json"
EVENTS_PATH = REGISTRY_DIR / "ai_module_events.v0100.jsonl"
LOCK_PATH = REGISTRY_DIR / ".ai_module_allocator.lock"
INSTRUCTION_SCHEMA_PATH = SCHEMAS_DIR / "instruction_module.schema.json"
HANDOFF_SCHEMA_PATH = SCHEMAS_DIR / "handoff_packet.schema.json"
CONTEXT_SCHEMA_PATH = SCHEMAS_DIR / "context_pack.schema.json"
CAPSULE_SCHEMA_PATH = SCHEMAS_DIR / "system_capsule.schema.json"
CAPSULE_PATH = CONFIG_DIR / "SYSTEM_CAPSULE.v0100.json"
BRIDGE_PATH = CONFIG_DIR / "VIA_MotherSystem_Database_Bridge.v0100.json"
MODULE_TEMPLATE_PATH = TEMPLATES_DIR / "module_instruction.template.json"

ALLOWED_LAYERS = ("PREFLIGHT", "DATA", "CORE", "UI", "QA", "OPS")
REQUIRED_GATES = (
    "STATIC",
    "AST",
    "CONTRACT",
    "UNIT",
    "SANDBOX",
    "INTEGRATION",
    "REGRESSION",
    "USER_TEST",
)
MODULE_ID_PATTERN = re.compile(r"^VIA-AI-(\d{6})$")
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SHA_PATTERN = re.compile(r"^[0-9a-f]{7,40}$")
LOCK_TIMEOUT_SECONDS = 10.0
LOCK_POLL_SECONDS = 0.05
STALE_LOCK_SECONDS = 300.0
DEFAULT_MAX_CHARS_PER_FILE = 12000
DEFAULT_CONTEXT_OUTPUT = OUTPUT_DIR / "context_pack.compiled.json"
DEFAULT_AST_OUTPUT = OUTPUT_DIR / "ast_index.json"
DEFAULT_INSTRUCTION_AST_OUTPUT = OUTPUT_DIR / "instruction_ast.json"
FORBIDDEN_CONTEXT_SUFFIXES = {
    ".db",
    ".duckdb",
    ".sqlite",
    ".sqlite3",
    ".parquet",
    ".pdf",
    ".bin",
    ".onnx",
    ".gguf",
    ".pt",
    ".pth",
}
IGNORED_DIRECTORY_NAMES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "node_modules",
}


# ============================================================================
# 02. FILE AND HASH HELPERS
# ============================================================================


def utc_now() -> str:
    """Return a stable UTC timestamp."""
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    """Read one UTF-8 JSON object."""
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Read an append-only JSONL ledger."""
    records: list[dict[str, Any]] = []
    if not path.exists():
        return records
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"Expected object at {path}:{line_number}")
            records.append(value)
    return records


def atomic_write_json(path: Path, value: Any) -> None:
    """Atomically write UTF-8 JSON in the target directory."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="\n",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temporary_path = Path(handle.name)
    os.replace(temporary_path, path)


def append_jsonl(path: Path, value: dict[str, Any]) -> None:
    """Append one compact JSON event and force it to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(payload + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def sha256_bytes(value: bytes) -> str:
    """Return lowercase SHA-256 for bytes."""
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    """Stream a file into SHA-256."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_relative(path: Path, root: Path) -> str:
    """Return a POSIX relative path and reject path escapes."""
    resolved_root = root.resolve()
    resolved_path = path.resolve()
    try:
        return resolved_path.relative_to(resolved_root).as_posix()
    except ValueError as exc:
        raise ValueError(f"Path escapes repository root: {path}") from exc


@contextlib.contextmanager
def exclusive_lock(path: Path) -> Iterator[None]:
    """Create a portable exclusive lock file with stale-lock recovery."""
    started = time.monotonic()
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor: int | None = None
    while descriptor is None:
        try:
            descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(descriptor, f"pid={os.getpid()} time={utc_now()}\n".encode("utf-8"))
            os.fsync(descriptor)
        except FileExistsError:
            try:
                age = time.time() - path.stat().st_mtime
                if age > STALE_LOCK_SECONDS:
                    path.unlink()
                    continue
            except FileNotFoundError:
                continue
            if time.monotonic() - started >= LOCK_TIMEOUT_SECONDS:
                raise TimeoutError(f"Allocator lock timeout: {path}")
            time.sleep(LOCK_POLL_SECONDS)
    try:
        yield
    finally:
        if descriptor is not None:
            os.close(descriptor)
        try:
            path.unlink()
        except FileNotFoundError:
            pass


# ============================================================================
# 03. MINIMAL JSON SCHEMA VALIDATION
# ============================================================================


def json_type_matches(value: Any, expected: str) -> bool:
    """Match JSON Schema primitive types without external dependencies."""
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return True


def resolve_local_ref(schema_root: dict[str, Any], reference: str) -> dict[str, Any]:
    """Resolve a local JSON pointer such as #/$defs/io."""
    if not reference.startswith("#/"):
        raise ValueError(f"Only local schema refs are supported: {reference}")
    current: Any = schema_root
    for token in reference[2:].split("/"):
        decoded = token.replace("~1", "/").replace("~0", "~")
        current = current[decoded]
    if not isinstance(current, dict):
        raise ValueError(f"Schema ref does not resolve to an object: {reference}")
    return current


def validate_schema_node(
    value: Any,
    schema: dict[str, Any],
    schema_root: dict[str, Any],
    location: str = "$",
) -> list[str]:
    """Validate the schema subset used by VIA contracts."""
    errors: list[str] = []
    if "$ref" in schema:
        schema = resolve_local_ref(schema_root, str(schema["$ref"]))

    expected_type = schema.get("type")
    if isinstance(expected_type, str) and not json_type_matches(value, expected_type):
        return [f"{location}: expected {expected_type}, got {type(value).__name__}"]

    if "const" in schema and value != schema["const"]:
        errors.append(f"{location}: expected constant {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{location}: value {value!r} is not in enum")

    if isinstance(value, str):
        if "minLength" in schema and len(value) < int(schema["minLength"]):
            errors.append(f"{location}: string shorter than minLength")
        if "pattern" in schema and re.fullmatch(str(schema["pattern"]), value) is None:
            errors.append(f"{location}: string does not match {schema['pattern']}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{location}: value below minimum")

    if isinstance(value, list):
        if "minItems" in schema and len(value) < int(schema["minItems"]):
            errors.append(f"{location}: fewer than minItems")
        if "maxItems" in schema and len(value) > int(schema["maxItems"]):
            errors.append(f"{location}: more than maxItems")
        if schema.get("uniqueItems"):
            normalized = [json.dumps(item, sort_keys=True, ensure_ascii=False) for item in value]
            if len(normalized) != len(set(normalized)):
                errors.append(f"{location}: duplicate array items")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                errors.extend(validate_schema_node(item, item_schema, schema_root, f"{location}[{index}]"))

    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                errors.append(f"{location}: missing required property {key}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extras = sorted(set(value) - set(properties))
            for key in extras:
                errors.append(f"{location}: unexpected property {key}")
        for key, child_schema in properties.items():
            if key in value and isinstance(child_schema, dict):
                errors.extend(validate_schema_node(value[key], child_schema, schema_root, f"{location}.{key}"))
    return errors


def validate_json_document(document: dict[str, Any], schema_path: Path) -> list[str]:
    """Validate a JSON object against a local VIA schema."""
    schema = read_json(schema_path)
    return validate_schema_node(document, schema, schema)


# ============================================================================
# 04. REGISTRY AND AUTO-NUMBERING
# ============================================================================


def module_sequence(module_id: str) -> int:
    """Extract the numeric portion of a VIA AI module ID."""
    match = MODULE_ID_PATTERN.fullmatch(module_id)
    if match is None:
        raise ValueError(f"Invalid module ID: {module_id}")
    return int(match.group(1))


def next_event_id(events: Sequence[dict[str, Any]]) -> str:
    """Allocate the next ledger event ID."""
    highest = 0
    for event in events:
        match = re.fullmatch(r"VIA-AI-EVT-(\d{6})", str(event.get("event_id", "")))
        if match:
            highest = max(highest, int(match.group(1)))
    return f"VIA-AI-EVT-{highest + 1:06d}"


def normalize_slug(slug: str) -> str:
    """Normalize and validate a stable machine slug."""
    normalized = slug.strip().lower().replace("_", "-")
    if SLUG_PATTERN.fullmatch(normalized) is None:
        raise ValueError(f"Invalid slug: {slug}")
    return normalized


def validate_registry(registry: dict[str, Any]) -> list[str]:
    """Validate registry identity, uniqueness and sequence invariants."""
    errors: list[str] = []
    modules = registry.get("modules")
    if not isinstance(modules, list):
        return ["registry.modules must be an array"]
    ids = [str(item.get("module_id", "")) for item in modules if isinstance(item, dict)]
    slugs = [str(item.get("slug", "")) for item in modules if isinstance(item, dict)]
    if len(ids) != len(set(ids)):
        errors.append("registry contains duplicate module IDs")
    if len(slugs) != len(set(slugs)):
        errors.append("registry contains duplicate slugs")
    sequences: list[int] = []
    for module_id in ids:
        try:
            sequences.append(module_sequence(module_id))
        except ValueError as exc:
            errors.append(str(exc))
    next_sequence = registry.get("next_sequence")
    if not isinstance(next_sequence, int) or next_sequence < 1:
        errors.append("registry.next_sequence must be a positive integer")
    elif sequences and next_sequence <= max(sequences):
        errors.append("registry.next_sequence must exceed registered IDs")
    leases = registry.get("leases", [])
    if not isinstance(leases, list):
        errors.append("registry.leases must be an array")
    else:
        intervals: list[tuple[int, int, str]] = []
        for lease in leases:
            if not isinstance(lease, dict):
                errors.append("registry lease must be an object")
                continue
            start = lease.get("start_sequence")
            end = lease.get("end_sequence")
            lease_id = str(lease.get("lease_id", ""))
            if not isinstance(start, int) or not isinstance(end, int) or start > end:
                errors.append(f"invalid lease interval: {lease_id}")
                continue
            intervals.append((start, end, lease_id))
        intervals.sort()
        for left, right in zip(intervals, intervals[1:]):
            if right[0] <= left[1]:
                errors.append(f"overlapping leases: {left[2]} and {right[2]}")
    return errors


def lease_id_range(agent: str, size: int, branch: str, base_sha: str) -> dict[str, Any]:
    """Reserve a non-overlapping contiguous module ID range."""
    if size < 1 or size > 1000:
        raise ValueError("Lease size must be between 1 and 1000")
    if SHA_PATTERN.fullmatch(base_sha) is None:
        raise ValueError("base_sha must contain 7 to 40 lowercase hexadecimal characters")
    with exclusive_lock(LOCK_PATH):
        registry = read_json(REGISTRY_PATH)
        events = read_jsonl(EVENTS_PATH)
        errors = validate_registry(registry)
        if errors:
            raise ValueError("; ".join(errors))
        start = int(registry["next_sequence"])
        end = start + size - 1
        leases = registry.setdefault("leases", [])
        lease_number = len(leases) + 1
        lease = {
            "lease_id": f"VIA-AI-LEASE-{lease_number:06d}",
            "agent": agent,
            "start_sequence": start,
            "end_sequence": end,
            "next_sequence": start,
            "branch": branch,
            "base_sha": base_sha,
            "status": "reserved",
            "created_at": utc_now(),
            "expires_at": None,
        }
        leases.append(lease)
        registry["next_sequence"] = end + 1
        atomic_write_json(REGISTRY_PATH, registry)
        append_jsonl(
            EVENTS_PATH,
            {
                "event_id": next_event_id(events),
                "event": "LEASE",
                **lease,
            },
        )
        return lease


def allocate_sequence(registry: dict[str, Any], lease_id: str | None) -> int:
    """Allocate from a lease or from the unleased global counter."""
    if lease_id:
        for lease in registry.get("leases", []):
            if lease.get("lease_id") != lease_id:
                continue
            if lease.get("status") != "reserved":
                raise ValueError(f"Lease is not active: {lease_id}")
            sequence = int(lease["next_sequence"])
            if sequence > int(lease["end_sequence"]):
                raise ValueError(f"Lease is exhausted: {lease_id}")
            lease["next_sequence"] = sequence + 1
            if sequence == int(lease["end_sequence"]):
                lease["status"] = "consumed"
            return sequence
        raise ValueError(f"Lease not found: {lease_id}")
    sequence = int(registry["next_sequence"])
    registry["next_sequence"] = sequence + 1
    return sequence


def allocate_module(
    layer: str,
    slug: str,
    title: str,
    owner: str,
    lease_id: str | None = None,
) -> dict[str, Any]:
    """Allocate an ID, create one manifest, update registry, and append an event."""
    normalized_layer = layer.upper()
    if normalized_layer not in ALLOWED_LAYERS:
        raise ValueError(f"Unsupported layer: {layer}")
    normalized_slug = normalize_slug(slug)
    with exclusive_lock(LOCK_PATH):
        registry = read_json(REGISTRY_PATH)
        events = read_jsonl(EVENTS_PATH)
        errors = validate_registry(registry)
        if errors:
            raise ValueError("; ".join(errors))
        if any(item.get("slug") == normalized_slug for item in registry["modules"]):
            raise ValueError(f"Slug already registered: {normalized_slug}")
        sequence = allocate_sequence(registry, lease_id)
        module_id = f"VIA-AI-{sequence:06d}"
        if any(item.get("module_id") == module_id for item in registry["modules"]):
            raise ValueError(f"Module ID already registered: {module_id}")
        filename = f"{module_id}-{normalized_slug}.instruction.json"
        manifest_path = MODULES_DIR / filename
        if manifest_path.exists():
            raise FileExistsError(f"Manifest already exists: {manifest_path}")
        manifest = read_json(MODULE_TEMPLATE_PATH)
        manifest.update(
            {
                "module_id": module_id,
                "layer": normalized_layer,
                "slug": normalized_slug,
                "title": title,
                "owner": owner,
                "purpose": title,
            }
        )
        manifest["metadata"] = {
            "generated_at": utc_now(),
            "generated_by": "via_ai_workflow.py",
            "lease_id": lease_id,
        }
        schema_errors = validate_json_document(manifest, INSTRUCTION_SCHEMA_PATH)
        if schema_errors:
            raise ValueError("; ".join(schema_errors))
        registry["modules"].append(
            {
                "module_id": module_id,
                "layer": normalized_layer,
                "slug": normalized_slug,
                "manifest": f"../modules/{filename}",
                "status": "draft",
                "owner": owner,
            }
        )
        atomic_write_json(manifest_path, manifest)
        atomic_write_json(REGISTRY_PATH, registry)
        append_jsonl(
            EVENTS_PATH,
            {
                "event_id": next_event_id(events),
                "event": "REGISTER",
                "module_id": module_id,
                "layer": normalized_layer,
                "slug": normalized_slug,
                "owner": owner,
                "version": manifest["version"],
                "lease_id": lease_id,
                "created_at": utc_now(),
            },
        )
        return manifest


# ============================================================================
# 05. INSTRUCTION AND CODE AST
# ============================================================================


def compile_instruction_ast(manifests: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Compile instruction manifests into a deterministic dependency AST."""
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, str]] = []
    ordered = sorted(manifests, key=lambda item: module_sequence(str(item["module_id"])))
    for manifest in ordered:
        module_id = str(manifest["module_id"])
        nodes.append(
            {
                "node_id": module_id,
                "node_type": "module",
                "layer": manifest["layer"],
                "slug": manifest["slug"],
                "status": manifest["status"],
            }
        )
        previous_step: str | None = None
        for step in manifest["steps"]:
            step_node = f"{module_id}:{step['step_id']}"
            nodes.append(
                {
                    "node_id": step_node,
                    "node_type": "step",
                    "action": step["action"],
                    "on_failure": step["on_failure"],
                }
            )
            edges.append({"from": module_id, "to": step_node, "type": "contains"})
            if previous_step:
                edges.append({"from": previous_step, "to": step_node, "type": "next"})
            previous_step = step_node
        for dependency in manifest["dependencies"]:
            edges.append({"from": dependency, "to": module_id, "type": "depends_on"})
    return {
        "ast_version": "0100",
        "generated_at": utc_now(),
        "nodes": nodes,
        "edges": edges,
    }


def python_arguments(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    """Return argument names for a Python function AST node."""
    arguments = [argument.arg for argument in node.args.posonlyargs]
    arguments.extend(argument.arg for argument in node.args.args)
    if node.args.vararg:
        arguments.append(f"*{node.args.vararg.arg}")
    arguments.extend(argument.arg for argument in node.args.kwonlyargs)
    if node.args.kwarg:
        arguments.append(f"**{node.args.kwarg.arg}")
    return arguments


def decorator_name(node: ast.expr) -> str:
    """Render a compact decorator identity."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{decorator_name(node.value)}.{node.attr}"
    if isinstance(node, ast.Call):
        return decorator_name(node.func)
    return node.__class__.__name__


def called_symbol(node: ast.Call) -> str | None:
    """Resolve a compact call target from an AST Call node."""
    target = node.func
    if isinstance(target, ast.Name):
        return target.id
    if isinstance(target, ast.Attribute):
        parts = [target.attr]
        current: ast.expr = target.value
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return ".".join(reversed(parts))
    return None


def index_python_file(path: Path, root: Path) -> dict[str, Any]:
    """Parse one Python file and return addressable symbols and calls."""
    source = path.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(path))
    symbols: list[dict[str, Any]] = []
    imports: list[str] = []
    calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.append(
                {
                    "kind": "async_function" if isinstance(node, ast.AsyncFunctionDef) else "function",
                    "name": node.name,
                    "line_start": node.lineno,
                    "line_end": getattr(node, "end_lineno", node.lineno),
                    "args": python_arguments(node),
                    "decorators": [decorator_name(item) for item in node.decorator_list],
                }
            )
        elif isinstance(node, ast.ClassDef):
            symbols.append(
                {
                    "kind": "class",
                    "name": node.name,
                    "line_start": node.lineno,
                    "line_end": getattr(node, "end_lineno", node.lineno),
                    "decorators": [decorator_name(item) for item in node.decorator_list],
                }
            )
        elif isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
        elif isinstance(node, ast.Call):
            name = called_symbol(node)
            if name:
                calls.add(name)
    return {
        "path": safe_relative(path, root),
        "sha256": sha256_bytes(source.encode("utf-8")),
        "symbols": sorted(symbols, key=lambda item: (item["line_start"], item["name"])),
        "imports": sorted(set(imports)),
        "calls": sorted(calls),
    }


def should_ignore(path: Path) -> bool:
    """Return True for generated or dependency directories."""
    return any(part in IGNORED_DIRECTORY_NAMES for part in path.parts)


def build_python_ast_index(root: Path) -> dict[str, Any]:
    """Build a read-only Python AST index for one approved root."""
    resolved_root = root.resolve()
    files: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for path in sorted(resolved_root.rglob("*.py")):
        if should_ignore(path.relative_to(resolved_root)):
            continue
        try:
            files.append(index_python_file(path, resolved_root))
        except (OSError, UnicodeError, SyntaxError) as exc:
            errors.append({"path": safe_relative(path, resolved_root), "error": str(exc)})
    return {
        "index_version": "0100",
        "root": str(resolved_root),
        "generated_at": utc_now(),
        "file_count": len(files),
        "error_count": len(errors),
        "files": files,
        "errors": errors,
    }


# ============================================================================
# 06. TOKEN-SAFE CONTEXT PACK
# ============================================================================


def extract_python_symbol_slices(
    path: Path,
    requested_symbols: Sequence[str],
    max_chars: int,
) -> tuple[str, list[str]]:
    """Extract only requested Python definitions using real AST line ranges."""
    source = path.read_text(encoding="utf-8-sig")
    lines = source.splitlines(keepends=True)
    tree = ast.parse(source, filename=str(path))
    requested_names = {item.rsplit(".", 1)[-1] for item in requested_symbols}
    slices: list[str] = []
    matched: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if node.name not in requested_names:
            continue
        start = max(1, node.lineno) - 1
        end = max(node.lineno, getattr(node, "end_lineno", node.lineno))
        chunk = "".join(lines[start:end])
        slices.append(chunk)
        matched.append(node.name)
    content = "\n\n".join(slices)
    return content[:max_chars], sorted(set(matched))


def compile_context_pack(task_path: Path) -> dict[str, Any]:
    """Compile a bounded, hashed context payload from an explicit allowlist."""
    task = read_json(task_path)
    errors = validate_json_document(task, CONTEXT_SCHEMA_PATH)
    if errors:
        raise ValueError("; ".join(errors))
    repository_root = Path(os.path.expandvars(task["repository_root"])).resolve()
    if not repository_root.exists():
        raise FileNotFoundError(f"Repository root not found: {repository_root}")
    token_policy = task["token_budget"]
    include_full_files = bool(token_policy["include_full_files"])
    max_chars = int(token_policy.get("max_chars_per_file", DEFAULT_MAX_CHARS_PER_FILE))
    symbols = [str(item) for item in task["symbol_allowlist"]]
    compiled_files: list[dict[str, Any]] = []
    for relative_name in task["path_allowlist"]:
        candidate = (repository_root / relative_name).resolve()
        relative_path = safe_relative(candidate, repository_root)
        if not candidate.is_file():
            raise FileNotFoundError(f"Allowlisted file not found: {relative_path}")
        if candidate.suffix.lower() in FORBIDDEN_CONTEXT_SUFFIXES:
            raise ValueError(f"Binary or data-plane artifact is forbidden in context packs: {relative_path}")
        raw = candidate.read_bytes()
        entry: dict[str, Any] = {
            "path": relative_path,
            "size_bytes": len(raw),
            "sha256": sha256_bytes(raw),
        }
        if include_full_files:
            entry["content"] = raw.decode("utf-8-sig")[:max_chars]
            entry["content_mode"] = "full_bounded"
        elif candidate.suffix.lower() == ".py" and symbols:
            content, matched = extract_python_symbol_slices(candidate, symbols, max_chars)
            entry["content"] = content
            entry["matched_symbols"] = matched
            entry["content_mode"] = "ast_symbol_slice"
        else:
            entry["content"] = raw.decode("utf-8-sig")[:max_chars]
            entry["content_mode"] = "bounded_excerpt"
        compiled_files.append(entry)
    estimated_tokens = sum(len(item.get("content", "")) for item in compiled_files) // 4
    max_tokens = int(token_policy["max_input_tokens"])
    if estimated_tokens > max_tokens:
        raise ValueError(f"Compiled context exceeds token budget: {estimated_tokens} > {max_tokens}")
    return {
        "compiled_at": utc_now(),
        "task": task,
        "estimated_input_tokens": estimated_tokens,
        "files": compiled_files,
    }


# ============================================================================
# 07. END-TO-END VALIDATION AND STATUS
# ============================================================================


def load_manifests() -> list[dict[str, Any]]:
    """Load every instruction manifest in stable filename order."""
    return [read_json(path) for path in sorted(MODULES_DIR.glob("*.instruction.json"))]


def validate_all(repository_root: Path | None = None) -> dict[str, Any]:
    """Validate contracts, registry linkage, ledger and optional parent anchors."""
    errors: list[str] = []
    warnings: list[str] = []
    registry = read_json(REGISTRY_PATH)
    events = read_jsonl(EVENTS_PATH)
    manifests = load_manifests()
    errors.extend(validate_registry(registry))
    errors.extend(f"capsule: {item}" for item in validate_json_document(read_json(CAPSULE_PATH), CAPSULE_SCHEMA_PATH))

    seen_ids: set[str] = set()
    manifest_by_id: dict[str, dict[str, Any]] = {}
    for manifest in manifests:
        module_id = str(manifest.get("module_id", "UNKNOWN"))
        for item in validate_json_document(manifest, INSTRUCTION_SCHEMA_PATH):
            errors.append(f"{module_id}: {item}")
        if module_id in seen_ids:
            errors.append(f"duplicate manifest module_id: {module_id}")
        seen_ids.add(module_id)
        manifest_by_id[module_id] = manifest
        step_ids = [step.get("step_id") for step in manifest.get("steps", [])]
        expected = [f"S{index:02d}" for index in range(1, len(step_ids) + 1)]
        if step_ids != expected:
            errors.append(f"{module_id}: step IDs must be sequential")

    registry_by_id = {str(item.get("module_id")): item for item in registry.get("modules", [])}
    if set(registry_by_id) != set(manifest_by_id):
        errors.append("registry IDs and manifest IDs differ")
    for module_id, manifest in manifest_by_id.items():
        for dependency in manifest.get("dependencies", []):
            if dependency not in manifest_by_id:
                errors.append(f"{module_id}: missing dependency {dependency}")
        registered = registry_by_id.get(module_id, {})
        if registered.get("layer") != manifest.get("layer"):
            errors.append(f"{module_id}: registry layer differs from manifest")
        manifest_path = (REGISTRY_DIR / str(registered.get("manifest", ""))).resolve()
        expected_path = (MODULES_DIR / f"{module_id}-{manifest.get('slug')}.instruction.json").resolve()
        if manifest_path != expected_path:
            errors.append(f"{module_id}: registry manifest path mismatch")

    registered_events = {
        str(event.get("module_id"))
        for event in events
        if event.get("event") == "REGISTER"
    }
    missing_events = sorted(set(manifest_by_id) - registered_events)
    if missing_events:
        errors.append(f"missing REGISTER events: {', '.join(missing_events)}")

    bridge = read_json(BRIDGE_PATH)
    if bridge.get("data_plane", {}).get("upload_to_github") is not False:
        errors.append("database bridge must deny GitHub data upload")
    if repository_root is not None:
        resolved_root = repository_root.resolve()
        capsule = read_json(CAPSULE_PATH)
        for role, relative_path in capsule["canonical_anchors"].items():
            if not (resolved_root / relative_path).exists():
                warnings.append(f"canonical anchor not present locally: {role} -> {relative_path}")

    ast_document = compile_instruction_ast(manifests)
    if not ast_document["nodes"]:
        errors.append("instruction AST contains no nodes")
    return {
        "status": "PASS" if not errors else "FAIL",
        "module_count": len(manifests),
        "event_count": len(events),
        "ast_node_count": len(ast_document["nodes"]),
        "ast_edge_count": len(ast_document["edges"]),
        "errors": errors,
        "warnings": warnings,
    }


def validate_handoff(path: Path) -> dict[str, Any]:
    """Validate a handoff packet and its ready-for-review gate semantics."""
    packet = read_json(path)
    errors = validate_json_document(packet, HANDOFF_SCHEMA_PATH)
    if packet.get("status") == "ready_for_review":
        gate_status = {item.get("name"): item.get("status") for item in packet.get("gates", [])}
        for gate in REQUIRED_GATES:
            if gate_status.get(gate) != "PASS":
                errors.append(f"ready_for_review requires PASS gate: {gate}")
        if packet.get("unresolved"):
            errors.append("ready_for_review requires an empty unresolved list")
    return {"status": "PASS" if not errors else "FAIL", "errors": errors}


def status_matrix() -> dict[str, Any]:
    """Return a compact, human- and machine-readable module status matrix."""
    registry = read_json(REGISTRY_PATH)
    modules = sorted(registry["modules"], key=lambda item: module_sequence(item["module_id"]))
    return {
        "registry_id": registry["registry_id"],
        "mode": registry["mode"],
        "next_sequence": registry["next_sequence"],
        "modules": [
            {
                "module_id": item["module_id"],
                "layer": item["layer"],
                "slug": item["slug"],
                "status": item["status"],
                "owner": item["owner"],
            }
            for item in modules
        ],
        "leases": registry.get("leases", []),
    }


# ============================================================================
# 08. COMMAND-LINE INTERFACE
# ============================================================================


def write_output(path: Path, value: Any) -> None:
    """Write JSON and echo its path for orchestration."""
    atomic_write_json(path, value)
    print(json.dumps({"status": "PASS", "output": str(path)}, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    """Build the complete command-line parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate package contracts")
    validate_parser.add_argument("--repo-root", type=Path)

    allocate_parser = subparsers.add_parser("allocate", help="Allocate one module ID and manifest")
    allocate_parser.add_argument("--layer", required=True, choices=ALLOWED_LAYERS)
    allocate_parser.add_argument("--slug", required=True)
    allocate_parser.add_argument("--title", required=True)
    allocate_parser.add_argument("--owner", required=True)
    allocate_parser.add_argument("--lease-id")

    lease_parser = subparsers.add_parser("lease", help="Reserve an ID range for one AI branch")
    lease_parser.add_argument("--agent", required=True)
    lease_parser.add_argument("--size", required=True, type=int)
    lease_parser.add_argument("--branch", required=True)
    lease_parser.add_argument("--base-sha", required=True)

    ast_parser = subparsers.add_parser("ast-index", help="Index Python symbols using ast")
    ast_parser.add_argument("--root", required=True, type=Path)
    ast_parser.add_argument("--output", type=Path, default=DEFAULT_AST_OUTPUT)

    instruction_parser = subparsers.add_parser("instruction-ast", help="Compile instruction dependency AST")
    instruction_parser.add_argument("--output", type=Path, default=DEFAULT_INSTRUCTION_AST_OUTPUT)

    context_parser = subparsers.add_parser("context-pack", help="Compile an allowlisted context pack")
    context_parser.add_argument("--task", required=True, type=Path)
    context_parser.add_argument("--output", type=Path, default=DEFAULT_CONTEXT_OUTPUT)

    handoff_parser = subparsers.add_parser("validate-handoff", help="Validate one handoff packet")
    handoff_parser.add_argument("--path", required=True, type=Path)

    subparsers.add_parser("status", help="Print registry status")
    return parser


def run_command(arguments: argparse.Namespace) -> int:
    """Execute one parsed CLI command."""
    if arguments.command == "validate":
        result = validate_all(arguments.repo_root)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "PASS" else 2
    if arguments.command == "allocate":
        result = allocate_module(
            arguments.layer,
            arguments.slug,
            arguments.title,
            arguments.owner,
            arguments.lease_id,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    if arguments.command == "lease":
        result = lease_id_range(arguments.agent, arguments.size, arguments.branch, arguments.base_sha)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    if arguments.command == "ast-index":
        result = build_python_ast_index(arguments.root)
        write_output(arguments.output, result)
        return 0 if result["error_count"] == 0 else 2
    if arguments.command == "instruction-ast":
        write_output(arguments.output, compile_instruction_ast(load_manifests()))
        return 0
    if arguments.command == "context-pack":
        write_output(arguments.output, compile_context_pack(arguments.task))
        return 0
    if arguments.command == "validate-handoff":
        result = validate_handoff(arguments.path)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "PASS" else 2
    if arguments.command == "status":
        print(json.dumps(status_matrix(), ensure_ascii=False, indent=2))
        return 0
    raise ValueError(f"Unhandled command: {arguments.command}")


def main(argv: Sequence[str] | None = None) -> int:
    """Program entry point with fail-closed error reporting."""
    parser = build_parser()
    arguments = parser.parse_args(argv)
    try:
        return run_command(arguments)
    except Exception as exc:  # CLI boundary intentionally converts failures to exit 2.
        print(json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
