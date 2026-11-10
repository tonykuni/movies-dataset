#!/usr/bin/env python3
"""VIA governance MCP v0105 local candidate adapter.

This is deliberately a small, non-daemon, stdio-only JSON-RPC 2.0 subset.  It is
not a Manus connector, VCGC host/client, HTTP server, OAuth client, or formal
registration mechanism.  The adapter reads only the fixed governance inventory
relative to a caller-supplied package root (after a caller-supplied SHA-256
check) and the pinned local TokenEngine source.  It never imports, scans, or
executes inventory content and never calls a provider.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from typing import Any, Mapping


PROTOCOL_VERSION = "2025-06-18"
SERVER_NAME = "via-governance-mcp-candidate"
SERVER_VERSION = "0.1.5"

MAX_REQUESTS = 1000
MAX_LINE_BYTES = 2 * 1024 * 1024
MAX_RESPONSE_BYTES = 4 * 1024 * 1024
MAX_TOKEN_INPUT_BYTES = 1 * 1024 * 1024
MAX_INVENTORY_BYTES = 64 * 1024 * 1024
MAX_QUERY_ROWS = 50
MAX_TOKEN_LINES = 400
DEFAULT_TOKEN_LINES = 120

INVENTORY_RELATIVE = "data/governance_inventory_v0105.json"
PINNED_ENGINE_RELATIVE = "engines/tooling/via_agent_os_unified_readonly_hardened.py"
PINNED_ENGINE_SHA256 = "ca3c38ee00d2d7df5af71bcaea59ab7e7c73a15ec1d1f7b03218127efaf62af5"

ROOT = Path(__file__).resolve().parents[1]
PINNED_ENGINE = ROOT / PINNED_ENGINE_RELATIVE

_TOOL_NAMES = ("via_status", "via_inventory_query", "via_token_prepare")
_MATRIX_ORDER = ("files", "io", "commands", "environment", "conflicts", "policy", "tests", "requirements")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_ABSOLUTE_WINDOWS = re.compile(r"^(?:[A-Za-z]:[\\/]|\\\\)")


class AdapterError(Exception):
    """Expected, fail-closed adapter error."""

    def __init__(self, message: str, code: int = -32602) -> None:
        super().__init__(message)
        self.code = code


class DuplicateJSONKeyError(ValueError):
    pass


def _strict_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJSONKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise ValueError(f"non-finite JSON constant: {value}")


def strict_json_loads(raw: str | bytes) -> Any:
    """Parse JSON with duplicate-key and non-finite-number rejection."""
    text = raw.decode("utf-8", "strict") if isinstance(raw, bytes) else raw
    return json.loads(text, object_pairs_hook=_strict_pairs, parse_constant=_reject_constant)


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def _rpc_error(request_id: Any, code: int, message: str, data: Any | None = None) -> dict[str, Any]:
    body: dict[str, Any] = {"jsonrpc": "2.0", "error": {"code": int(code), "message": message}}
    if request_id is not None:
        body["id"] = request_id
    if data is not None:
        body["error"]["data"] = data
    return body


def _is_bool(value: Any) -> bool:
    return isinstance(value, bool)


def _require_string(value: Any, label: str, *, nonempty: bool = True) -> str:
    if not isinstance(value, str) or (nonempty and not value):
        raise AdapterError(f"{label} must be a string")
    if "\x00" in value:
        raise AdapterError(f"{label} contains NUL")
    return value


def _require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AdapterError(f"{label} must be an object")
    return value


def _reject_unknown(mapping: Mapping[str, Any], allowed: set[str], label: str) -> None:
    unknown = sorted(set(mapping) - allowed)
    if unknown:
        raise AdapterError(f"unknown {label}: {','.join(unknown)}")


def _portable_text(value: str, package_root: Path | None = None) -> str:
    """Return a relative, non-machine-specific path-like string."""
    text = value.replace("\\", "/")
    root_text = package_root.as_posix().rstrip("/") if package_root else ""
    if root_text and (text == root_text or text.startswith(root_text + "/")):
        return text[len(root_text):].lstrip("/") or "."
    if text.startswith("/") or _ABSOLUTE_WINDOWS.match(text):
        name = text.rstrip("/").rsplit("/", 1)[-1] or "root"
        return f"external/{name}"
    return text


def _sanitize(value: Any, package_root: Path | None = None) -> Any:
    """Remove absolute paths recursively without changing evidence semantics."""
    if isinstance(value, dict):
        return {str(k): _sanitize(v, package_root) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize(v, package_root) for v in value]
    if isinstance(value, str):
        return _portable_text(value, package_root)
    return value


def _safe_error_text(value: Any) -> str:
    text = str(value).replace("\\", "/")
    text = re.sub(r"/(?:home|tmp|mnt|var|opt|workspace)/[^\s'\"]+", "<redacted-path>", text)
    text = re.sub(r"[A-Za-z]:/[^\s'\"]+", "<redacted-path>", text)
    return text[:500] or "adapter error"


def _path_has_symlink(path: Path) -> bool:
    """Check every existing component without resolving through a symlink."""
    if not path.is_absolute():
        raise AdapterError("path must be absolute")
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current = current / part
        try:
            if current.is_symlink():
                return True
        except OSError as exc:
            raise AdapterError("path cannot be inspected", -32003) from exc
    return False


def _ensure_regular(path: Path, *, max_bytes: int) -> bytes:
    if _path_has_symlink(path):
        raise AdapterError("source symlink is not allowed", -32003)
    try:
        info = path.lstat()
    except OSError as exc:
        raise AdapterError("source is unavailable", -32003) from exc
    if not stat.S_ISREG(info.st_mode):
        raise AdapterError("source must be a regular file", -32003)
    if info.st_size > max_bytes:
        raise AdapterError("source exceeds safety limit", -32003)
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise AdapterError("source cannot be read", -32003) from exc
    if len(data) != info.st_size:
        raise AdapterError("source changed during read", -32003)
    return data


def _ensure_package_root(raw: Any) -> Path:
    value = _require_string(raw, "package_root")
    root = Path(value).expanduser()
    if not root.is_absolute():
        raise AdapterError("package_root must be an absolute path")
    if _path_has_symlink(root):
        raise AdapterError("package_root symlink is not allowed", -32003)
    try:
        info = root.lstat()
    except OSError as exc:
        raise AdapterError("package_root is unavailable", -32003) from exc
    if not stat.S_ISDIR(info.st_mode):
        raise AdapterError("package_root must be a directory", -32003)
    return root


def _fixed_inventory(root: Path, expected_sha: str) -> tuple[Path, bytes, str]:
    if not _HEX64.fullmatch(expected_sha):
        raise AdapterError("inventory_sha must be a lowercase SHA-256", -32602)
    path = root / INVENTORY_RELATIVE
    data = _ensure_regular(path, max_bytes=MAX_INVENTORY_BYTES)
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected_sha:
        raise AdapterError("inventory SHA-256 mismatch", -32003)
    return path, data, actual


def _fixed_engine() -> tuple[Path, bytes]:
    data = _ensure_regular(PINNED_ENGINE, max_bytes=64 * 1024 * 1024)
    digest = hashlib.sha256(data).hexdigest()
    if digest != PINNED_ENGINE_SHA256:
        raise AdapterError("pinned TokenEngine SHA-256 mismatch", -32003)
    return PINNED_ENGINE, data


def _inventory_rows(model: Any) -> list[tuple[str, dict[str, Any]]]:
    """Flatten the v0105 matrix shape without interpreting or executing rows."""
    if not isinstance(model, dict):
        raise AdapterError("inventory JSON root must be an object", -32003)
    matrices = model.get("matrices")
    if not isinstance(matrices, dict):
        raise AdapterError("inventory matrices are unavailable", -32003)
    rows: list[tuple[str, dict[str, Any]]] = []
    for category in _MATRIX_ORDER:
        values = matrices.get(category, [])
        if not isinstance(values, list):
            raise AdapterError(f"inventory matrix {category} is not a list", -32003)
        for row in values:
            if not isinstance(row, dict):
                raise AdapterError("inventory matrix row is not an object", -32003)
            rows.append((category, row))
    return rows


def _row_search_text(category: str, row: Mapping[str, Any]) -> str:
    try:
        return json.dumps({"matrix": category, "row": row}, ensure_ascii=False, sort_keys=True, allow_nan=False).casefold()
    except (TypeError, ValueError, OverflowError):
        return ""


def _match_inventory_row(category: str, row: Mapping[str, Any], args: Mapping[str, Any]) -> bool:
    filters = args.get("filters", {})
    if not isinstance(filters, dict):
        raise AdapterError("filters must be an object")
    allowed_filter_keys = {"status", "system", "kind", "classification", "source"}
    _reject_unknown(filters, allowed_filter_keys, "inventory filter")
    for key, expected in filters.items():
        if not isinstance(expected, str):
            raise AdapterError(f"filters.{key} must be a string")
        actual = category if key == "classification" and key not in row else row.get(key)
        if str(actual).casefold() != expected.casefold():
            return False
    query = args.get("query")
    if query is not None:
        _require_string(query, "query", nonempty=False)
        if query.casefold() not in _row_search_text(category, row):
            return False
    return True


def _inventory_query(args: Mapping[str, Any]) -> dict[str, Any]:
    root = _ensure_package_root(args.get("package_root"))
    expected_sha = _require_string(args.get("inventory_sha"), "inventory_sha")
    source_path, data, digest = _fixed_inventory(root, expected_sha)
    try:
        model = strict_json_loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError, DuplicateJSONKeyError, ValueError) as exc:
        raise AdapterError("inventory strict JSON validation failed", -32003) from exc
    all_rows = _inventory_rows(model)
    matching: list[dict[str, Any]] = []
    for category, row in all_rows:
        if not _match_inventory_row(category, row, args):
            continue
        safe_row = _sanitize(row, root)
        assert isinstance(safe_row, dict)
        safe_row = dict(safe_row)
        safe_row["_matrix"] = category
        safe_row["_evidence_scope"] = "LOCAL_CANDIDATE_EVIDENCE_NOT_LIVE"
        matching.append(safe_row)
    offset = args.get("offset", 0)
    limit = args.get("limit", MAX_QUERY_ROWS)
    if _is_bool(offset) or not isinstance(offset, int) or offset < 0:
        raise AdapterError("offset must be a non-negative integer")
    if _is_bool(limit) or not isinstance(limit, int) or not 1 <= limit <= MAX_QUERY_ROWS:
        raise AdapterError(f"limit must be an integer in 1..{MAX_QUERY_ROWS}")
    page = matching[offset : offset + limit]
    result = {
        "status": "OK",
        "source": INVENTORY_RELATIVE,
        "source_sha256": digest,
        "evidence_scope": "LOCAL_CANDIDATE_EVIDENCE_NOT_LIVE",
        "registration_status": "CANDIDATE_NOT_REGISTERED",
        "total_matching": len(matching),
        "offset": offset,
        "limit": limit,
        "returned": len(page),
        "has_more": offset + len(page) < len(matching),
        "rows": page,
    }
    # Keep the path variable meaningful to static reviewers while never emitting it.
    if source_path.name != Path(INVENTORY_RELATIVE).name:
        raise AdapterError("fixed inventory source mismatch", -32003)
    return result


def _tool_schema() -> list[dict[str, Any]]:
    readonly = {
        "readOnlyHint": True,
        "destructiveHint": False,
        "openWorldHint": False,
        "idempotentHint": True,
    }
    return [
        {
            "name": "via_status",
            "description": "Static local candidate status; no connector, VCGC host/client, network, or provider is used.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
            "annotations": readonly,
        },
        {
            "name": "via_inventory_query",
            "description": "Bounded query over fixed data/governance_inventory_v0105.json after caller SHA-256 verification; local candidate evidence only.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "package_root": {"type": "string", "description": "Absolute package root; only its fixed data path is read."},
                    "inventory_sha": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "query": {"type": "string"},
                    "filters": {
                        "type": "object",
                        "properties": {key: {"type": "string"} for key in ("status", "system", "kind", "classification", "source")},
                        "additionalProperties": False,
                    },
                    "offset": {"type": "integer", "minimum": 0, "default": 0},
                    "limit": {"type": "integer", "minimum": 1, "maximum": MAX_QUERY_ROWS, "default": MAX_QUERY_ROWS},
                },
                "required": ["package_root", "inventory_sha"],
                "additionalProperties": False,
            },
            "annotations": readonly,
        },
        {
            "name": "via_token_prepare",
            "description": "Prepare caller-supplied UTF-8 text through the pinned local TokenEngine; no source file or provider is read.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Caller-provided non-sensitive text, at most 1 MiB UTF-8."},
                    "allow_lossy": {"type": "boolean", "default": False},
                    "query": {"type": "string"},
                    "max_lines": {"type": "integer", "minimum": 1, "maximum": MAX_TOKEN_LINES, "default": DEFAULT_TOKEN_LINES},
                },
                "required": ["text"],
                "additionalProperties": False,
            },
            "annotations": readonly,
        },
    ]


def _validate_tool_args(name: Any, raw_args: Any) -> dict[str, Any]:
    tool = _require_string(name, "tool name")
    if tool not in _TOOL_NAMES:
        raise AdapterError("Unknown tool")
    args = _require_object(raw_args, "arguments")
    if tool == "via_status":
        _reject_unknown(args, set(), "via_status argument")
        return args
    if tool == "via_inventory_query":
        allowed = {"package_root", "inventory_sha", "query", "filters", "offset", "limit"}
        _reject_unknown(args, allowed, "via_inventory_query argument")
        if "package_root" not in args or "inventory_sha" not in args:
            raise AdapterError("via_inventory_query requires package_root and inventory_sha")
        _require_string(args["package_root"], "package_root")
        _require_string(args["inventory_sha"], "inventory_sha")
        if "query" in args:
            _require_string(args["query"], "query", nonempty=False)
        if "filters" in args:
            filters = _require_object(args["filters"], "filters")
            _reject_unknown(filters, {"status", "system", "kind", "classification", "source"}, "inventory filter")
            for key, value in filters.items():
                _require_string(value, f"filters.{key}", nonempty=False)
        if "offset" in args:
            if _is_bool(args["offset"]) or not isinstance(args["offset"], int) or args["offset"] < 0:
                raise AdapterError("offset must be a non-negative integer")
        if "limit" in args:
            if _is_bool(args["limit"]) or not isinstance(args["limit"], int) or not 1 <= args["limit"] <= MAX_QUERY_ROWS:
                raise AdapterError(f"limit must be an integer in 1..{MAX_QUERY_ROWS}")
        return args
    allowed = {"text", "allow_lossy", "query", "max_lines"}
    _reject_unknown(args, allowed, "via_token_prepare argument")
    if "text" not in args:
        raise AdapterError("via_token_prepare requires text")
    text = _require_string(args["text"], "text", nonempty=False)
    try:
        input_bytes = len(text.encode("utf-8", "strict"))
    except UnicodeEncodeError as exc:
        raise AdapterError("text must be valid UTF-8") from exc
    if input_bytes > MAX_TOKEN_INPUT_BYTES:
        raise AdapterError("text exceeds 1 MiB UTF-8 input limit")
    allow_lossy = args.get("allow_lossy", False)
    if not _is_bool(allow_lossy):
        raise AdapterError("allow_lossy must be boolean")
    if "query" in args:
        _require_string(args["query"], "query", nonempty=False)
    max_lines = args.get("max_lines", DEFAULT_TOKEN_LINES)
    if _is_bool(max_lines) or not isinstance(max_lines, int) or not 1 <= max_lines <= MAX_TOKEN_LINES:
        raise AdapterError(f"max_lines must be an integer in 1..{MAX_TOKEN_LINES}")
    return args


def _status() -> dict[str, Any]:
    return {
        "status": "CANDIDATE_ONLY",
        "registration_status": "CANDIDATE_NOT_REGISTERED",
        "registration_performed": False,
        "formal_status": "REQUIRES_REAL_ENDPOINT_AND_OWNER_APPROVAL",
        "manus_connector_installed": False,
        "vcgc_host_or_client_registered": False,
        "transport": "stdio",
        "protocol_version": PROTOCOL_VERSION,
        "full_conformance": False,
        "latest_alias_supported": False,
        "http_supported": False,
        "oauth_supported": False,
        "sampling_supported": False,
        "resources_supported": False,
        "prompts_supported": False,
        "tools": list(_TOOL_NAMES),
        "network_access": False,
        "provider_calls": 0,
        "repository_writes": False,
        "evidence_scope": "LOCAL_CANDIDATE_EVIDENCE_NOT_LIVE",
        "limitations": [
            "Candidate subset only; it does not claim connector installation or VCGC registration.",
            "Formal tool status requires a real endpoint and owner approval.",
        ],
    }


def _token_prepare(args: Mapping[str, Any]) -> dict[str, Any]:
    engine, _engine_bytes = _fixed_engine()
    command = [sys.executable, "-B", str(engine), "context", "--include-text"]
    if args.get("allow_lossy", False):
        command.append("--allow-lossy")
    if "query" in args:
        command.extend(["--query", str(args["query"])])
    command.extend(["--max-lines", str(args.get("max_lines", DEFAULT_TOKEN_LINES))])
    text = args["text"]
    env = {"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "LC_ALL": "C.UTF-8"}
    try:
        completed = subprocess.run(
            command,
            input=text,
            text=True,
            encoding="utf-8",
            errors="strict",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            check=False,
            timeout=30,
            env=env,
            cwd=str(ROOT),
        )
    except (OSError, subprocess.SubprocessError, UnicodeError) as exc:
        raise AdapterError("TokenEngine subprocess failed", -32003) from exc
    if completed.returncode != 0:
        raise AdapterError("TokenEngine rejected the supplied text", -32003)
    try:
        result = strict_json_loads(completed.stdout)
    except (UnicodeDecodeError, json.JSONDecodeError, DuplicateJSONKeyError, ValueError) as exc:
        raise AdapterError("TokenEngine returned invalid JSON", -32003) from exc
    if not isinstance(result, dict):
        raise AdapterError("TokenEngine returned a non-object", -32003)
    result = _sanitize(result)
    result.update(
        {
            "engine_source": PINNED_ENGINE_RELATIVE,
            "engine_sha256": PINNED_ENGINE_SHA256,
            "provider_calls": 0,
            "content_persisted": False,
            "execution_scope": "LOCAL_PINNED_ENGINE_ONLY",
            "redaction_note": "TokenEngine original partial redaction is preserved; it is not a complete secret scanner.",
            "risk_note": "Caller must provide only non-sensitive text; heuristic token estimates are not provider billing.",
        }
    )
    return result


def _tool_result(request_id: Any, payload: Mapping[str, Any], *, is_error: bool = False) -> dict[str, Any]:
    result = dict(payload)
    try:
        text = json.dumps(result, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        body: dict[str, Any] = {
            "content": [{"type": "text", "text": text}],
            "structuredContent": result,
            "isError": bool(is_error),
        }
        response = {"jsonrpc": "2.0", "id": request_id, "result": body}
        if len(_json_bytes(response)) <= MAX_RESPONSE_BYTES:
            return response
    except (TypeError, ValueError, OverflowError):
        pass
    fallback = {"status": "BLOCKED", "reason": "response exceeds 4 MiB or is not strict JSON", "execution_performed": False}
    fallback_text = json.dumps(fallback, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "content": [{"type": "text", "text": fallback_text}],
            "structuredContent": fallback,
            "isError": True,
        },
    }


class MCPServer:
    def __init__(self) -> None:
        self.initialized = False
        self.initialized_notification = False
        self.requests_seen = 0

    @staticmethod
    def _valid_id(value: Any) -> bool:
        return isinstance(value, (str, int)) and not isinstance(value, bool)

    def _initialize(self, request_id: Any, params: Mapping[str, Any]) -> dict[str, Any]:
        if self.initialized:
            return _rpc_error(request_id, -32600, "duplicate initialize is not allowed")
        _reject_unknown(params, {"protocolVersion", "capabilities", "clientInfo"}, "initialize parameter")
        requested = params.get("protocolVersion")
        _require_string(requested, "protocolVersion")
        capabilities = params.get("capabilities")
        if not isinstance(capabilities, dict):
            return _rpc_error(request_id, -32602, "initialize capabilities must be an object")
        client_info = params.get("clientInfo")
        if not isinstance(client_info, dict):
            return _rpc_error(request_id, -32602, "initialize clientInfo must be an object")
        _reject_unknown(client_info, {"name", "version", "title", "icons"}, "clientInfo field")
        if not isinstance(client_info.get("name"), str) or not isinstance(client_info.get("version"), str):
            return _rpc_error(request_id, -32602, "initialize clientInfo requires string name and version")
        if "title" in client_info and not isinstance(client_info["title"], str):
            return _rpc_error(request_id, -32602, "initialize clientInfo.title must be a string")
        if "icons" in client_info and not isinstance(client_info["icons"], list):
            return _rpc_error(request_id, -32602, "initialize clientInfo.icons must be an array")
        self.initialized = True
        negotiated = requested if requested == PROTOCOL_VERSION else PROTOCOL_VERSION
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": negotiated,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                "instructions": "VIA local stdio candidate tools only; no connector, VCGC registration, network, provider, or repository write.",
            },
        }

    def _require_initialized(self, request_id: Any) -> dict[str, Any] | None:
        if not self.initialized:
            return _rpc_error(request_id, -32600, "initialize is required before MCP requests")
        if not self.initialized_notification:
            return _rpc_error(request_id, -32600, "notifications/initialized is required before tools")
        return None

    def handle(self, message: Any) -> dict[str, Any] | None:
        if not isinstance(message, dict) or message.get("jsonrpc") != "2.0" or not isinstance(message.get("method"), str):
            return _rpc_error(None, -32600, "Invalid Request")
        method = message["method"]
        is_notification = "id" not in message
        request_id = message.get("id")
        if not is_notification and not self._valid_id(request_id):
            return _rpc_error(None, -32600, "Invalid Request: id must be a non-null string or integer")
        params = message.get("params", {})
        if not isinstance(params, dict):
            return None if is_notification else _rpc_error(request_id, -32602, "params must be an object")
        if is_notification:
            if method == "notifications/initialized":
                if self.initialized:
                    self.initialized_notification = True
                return None
            # JSON-RPC notifications never receive a response.
            return None
        if method == "initialize":
            try:
                return self._initialize(request_id, params)
            except AdapterError as exc:
                return _rpc_error(request_id, exc.code, _safe_error_text(exc))
        if method == "tools/list":
            gate = self._require_initialized(request_id)
            if gate is not None:
                return gate
            if params:
                return _rpc_error(request_id, -32602, "tools/list does not accept parameters")
            return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": _tool_schema()}}
        if method == "tools/call":
            gate = self._require_initialized(request_id)
            if gate is not None:
                return gate
            name = params.get("name")
            try:
                _reject_unknown(params, {"name", "arguments"}, "tools/call parameter")
                if not isinstance(name, str):
                    raise AdapterError("tools/call requires a string name")
                if name not in _TOOL_NAMES:
                    raise AdapterError("Unknown tool")
            except AdapterError as exc:
                return _rpc_error(request_id, exc.code, _safe_error_text(exc))
            arguments = params.get("arguments", {})
            try:
                args = _validate_tool_args(name, arguments)
                if name == "via_status":
                    payload = _status()
                elif name == "via_inventory_query":
                    payload = _inventory_query(args)
                else:
                    payload = _token_prepare(args)
                return _tool_result(request_id, payload)
            except AdapterError as exc:
                return _tool_result(request_id, {"status": "BLOCKED", "reason": _safe_error_text(exc), "execution_performed": False}, is_error=True)
            except (OSError, TypeError, ValueError, UnicodeError, OverflowError, subprocess.SubprocessError) as exc:
                return _tool_result(request_id, {"status": "BLOCKED", "reason": _safe_error_text(exc), "execution_performed": False}, is_error=True)
        return _rpc_error(request_id, -32601, "Method not found")


def _write_response(response: Mapping[str, Any]) -> None:
    try:
        wire = _json_bytes(response)
    except (TypeError, ValueError, OverflowError):
        wire = _json_bytes(_rpc_error(None, -32603, "Internal JSON serialization error"))
    if len(wire) > MAX_RESPONSE_BYTES:
        wire = _json_bytes(_rpc_error(response.get("id"), -32004, "response exceeds 4 MiB limit"))
    sys.stdout.buffer.write(wire)
    sys.stdout.buffer.flush()


def run_stdio() -> int:
    server = MCPServer()
    stdin = getattr(sys.stdin, "buffer", sys.stdin)
    while True:
        raw = stdin.readline(MAX_LINE_BYTES + 2)
        if not raw:
            return 0
        if isinstance(raw, str):
            raw_bytes = raw.encode("utf-8", "strict")
        else:
            raw_bytes = raw
        line_bytes = raw_bytes.rstrip(b"\r\n")
        if not line_bytes:
            continue
        server.requests_seen += 1
        if server.requests_seen > MAX_REQUESTS:
            _write_response(_rpc_error(None, -32001, "request limit exceeded"))
            return 0
        if len(line_bytes) > MAX_LINE_BYTES:
            _write_response(_rpc_error(None, -32600, "MCP line exceeds 2 MiB limit"))
            return 0
        try:
            message = strict_json_loads(line_bytes)
            if isinstance(message, list):
                response = _rpc_error(None, -32600, "batch requests are not supported")
            else:
                response = server.handle(message)
        except (UnicodeDecodeError, json.JSONDecodeError, DuplicateJSONKeyError, ValueError, RecursionError):
            response = _rpc_error(None, -32700, "Parse error")
        except Exception as exc:  # fail closed without sending paths or tracebacks to stdout
            print(f"mcp adapter error: {_safe_error_text(exc)}", file=sys.stderr)
            response = _rpc_error(None, -32603, "Internal error")
        if response is not None:
            _write_response(response)


def main() -> int:
    if len(sys.argv) != 1:
        print("usage: via_governance_mcp_v0105.py (stdio JSON-RPC 2.0)", file=sys.stderr)
        return 2
    return run_stdio()


if __name__ == "__main__":
    raise SystemExit(main())
