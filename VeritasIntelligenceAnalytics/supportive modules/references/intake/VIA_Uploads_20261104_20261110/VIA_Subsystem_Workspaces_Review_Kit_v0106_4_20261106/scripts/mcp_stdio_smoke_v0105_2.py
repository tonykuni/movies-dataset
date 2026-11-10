#!/usr/bin/env python3
"""Finite stdio smoke test for the v0105 VIA governance MCP candidate.

This helper reads only the caller-supplied absolute package root's three fixed,
SHA-pinned files, starts the existing MCP entry point without a shell, sends a
finite initialized JSON-RPC session, captures stdout/stderr, and writes a
create-once receipt. It does not scan a filesystem, register a connector, or
modify the candidate package.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
from typing import Any, Mapping


SCRIPT_RELATIVE = Path("scripts/via_governance_mcp_v0105.py")
ENGINE_RELATIVE = Path("engines/tooling/via_agent_os_unified_readonly_hardened.py")
INVENTORY_RELATIVE = Path("data/governance_inventory_v0105.json")
SCRIPT_SHA256 = "901b91eb4add9db2c19f5a62e6ea291caa6a681294148fc6ca7ebc14a349225a"
ENGINE_SHA256 = "ca3c38ee00d2d7df5af71bcaea59ab7e7c73a15ec1d1f7b03218127efaf62af5"
INVENTORY_SHA256 = "43c74dbe2b35862d06d507ef27c16cd15502686abeb1bb101362a15632a74754"
PROTOCOL_VERSION = "2025-06-18"
TOOL_NAMES = ["via_status", "via_inventory_query", "via_token_prepare"]
TIMEOUT_SECONDS = 30
MAX_FILE_BYTES = {
    SCRIPT_RELATIVE: 2 * 1024 * 1024,
    ENGINE_RELATIVE: 64 * 1024 * 1024,
    INVENTORY_RELATIVE: 64 * 1024 * 1024,
}


class SmokeFailure(Exception):
    """Expected finite smoke-test failure."""


class DuplicateKeyError(ValueError):
    pass


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise ValueError(f"non-finite JSON value: {value}")


def strict_json(raw: bytes) -> Any:
    return json.loads(
        raw.decode("utf-8", "strict"),
        object_pairs_hook=_pairs,
        parse_constant=_reject_constant,
    )


def wire(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def _reject_symlink_components(path: Path) -> None:
    """Reject symlink components without resolving or scanning the path."""
    if not path.is_absolute():
        raise SmokeFailure(f"path must be absolute: {path}")
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current = current / part
        try:
            if current.is_symlink():
                raise SmokeFailure(f"symlink path component is not allowed: {path}")
        except OSError as exc:
            raise SmokeFailure(f"path cannot be inspected: {path}") from exc


def _regular_file_bytes(path: Path, maximum: int) -> bytes:
    _reject_symlink_components(path)
    try:
        info = path.lstat()
    except OSError as exc:
        raise SmokeFailure(f"required file is unavailable: {path}") from exc
    if not stat.S_ISREG(info.st_mode):
        raise SmokeFailure(f"required path is not a regular file: {path}")
    if info.st_size > maximum:
        raise SmokeFailure(f"required file exceeds safety limit: {path}")
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise SmokeFailure(f"required file cannot be read: {path}") from exc
    if len(data) != info.st_size:
        raise SmokeFailure(f"required file changed during read: {path}")
    return data


def _absolute_directory(raw: str) -> Path:
    path = Path(raw).expanduser()
    if not path.is_absolute():
        raise SmokeFailure("--package-root must be an absolute directory")
    _reject_symlink_components(path)
    try:
        info = path.lstat()
    except OSError as exc:
        raise SmokeFailure(f"package root is unavailable: {path}") from exc
    if not stat.S_ISDIR(info.st_mode):
        raise SmokeFailure("--package-root must be a directory")
    return path


def pin_package(root: Path) -> dict[str, Any]:
    expected = {
        SCRIPT_RELATIVE: SCRIPT_SHA256,
        ENGINE_RELATIVE: ENGINE_SHA256,
        INVENTORY_RELATIVE: INVENTORY_SHA256,
    }
    actual: dict[str, str] = {}
    for relative, expected_sha in expected.items():
        data = _regular_file_bytes(root / relative, MAX_FILE_BYTES[relative])
        digest = hashlib.sha256(data).hexdigest()
        actual[str(relative).replace("\\", "/")] = digest
        if digest != expected_sha:
            raise SmokeFailure(f"SHA-256 mismatch for {relative}: expected {expected_sha}, got {digest}")
    return {
        "script": {"path": str(SCRIPT_RELATIVE).replace("\\", "/"), "sha256": actual[str(SCRIPT_RELATIVE).replace("\\", "/")]},
        "engine": {"path": str(ENGINE_RELATIVE).replace("\\", "/"), "sha256": actual[str(ENGINE_RELATIVE).replace("\\", "/")]},
        "inventory": {"path": str(INVENTORY_RELATIVE).replace("\\", "/"), "sha256": actual[str(INVENTORY_RELATIVE).replace("\\", "/")]},
    }


def build_requests(root: Path) -> list[dict[str, Any]]:
    package_root = str(root)
    return [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "mcp_stdio_smoke_v0105_2", "version": "1"},
            },
        },
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "via_status", "arguments": {}}},
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "via_inventory_query",
                "arguments": {
                    "package_root": package_root,
                    "inventory_sha": INVENTORY_SHA256,
                    "query": "VIA",
                    "offset": 0,
                    "limit": 1,
                },
            },
        },
        {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "via_token_prepare",
                "arguments": {
                    "text": '{"smoke":"v0105","scope":"sandbox-only","contains_sensitive_data":false}',
                    "allow_lossy": False,
                    "max_lines": 20,
                },
            },
        },
    ]


def run_process(root: Path, script: Path, requests: list[dict[str, Any]]) -> tuple[int, bytes, bytes, bool]:
    payload = b"".join(wire(request) for request in requests)
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    # Keep the caller's environment, including SystemRoot on Windows. The
    # existing MCP script itself owns its TokenEngine child environment.
    command = [sys.executable, "-B", str(script)]
    try:
        process = subprocess.Popen(
            command,
            cwd=str(root),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            shell=False,
        )
    except (OSError, ValueError) as exc:
        raise SmokeFailure(f"could not start existing MCP script: {exc}") from exc
    try:
        stdout, stderr = process.communicate(input=payload, timeout=TIMEOUT_SECONDS)
        returncode = process.returncode
        return returncode, stdout, stderr, True
    except subprocess.TimeoutExpired as exc:
        process.kill()
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            stdout, stderr = b"", b""
        raise SmokeFailure(
            "MCP process exceeded the finite timeout after stdin EOF; it did not close cleanly"
        ) from exc


def _response_lines(stdout: bytes) -> list[dict[str, Any]]:
    if not stdout:
        raise SmokeFailure("MCP stdout was empty")
    raw_lines = stdout.splitlines()
    if not raw_lines or any(not line.strip() for line in raw_lines):
        raise SmokeFailure("MCP stdout contains an empty line or no newline-delimited response")
    responses: list[dict[str, Any]] = []
    for line in raw_lines:
        try:
            value = strict_json(line)
        except (UnicodeDecodeError, json.JSONDecodeError, DuplicateKeyError, ValueError) as exc:
            raise SmokeFailure("MCP stdout contains a non-JSON banner or malformed response") from exc
        if not isinstance(value, dict):
            raise SmokeFailure("MCP stdout response is not a JSON object")
        responses.append(value)
    return responses


def _result(responses: list[dict[str, Any]], request_id: int) -> dict[str, Any]:
    matches = [value for value in responses if value.get("id") == request_id]
    if len(matches) != 1:
        raise SmokeFailure(f"expected exactly one response for id {request_id}")
    response = matches[0]
    if "error" in response:
        raise SmokeFailure(f"MCP response id {request_id} returned an error")
    result = response.get("result")
    if not isinstance(result, dict):
        raise SmokeFailure(f"MCP response id {request_id} has no result object")
    if result.get("isError") is True:
        raise SmokeFailure(f"MCP tool response id {request_id} has isError=true")
    return result


def _structured(result: Mapping[str, Any], request_id: int) -> dict[str, Any]:
    value = result.get("structuredContent")
    if not isinstance(value, dict):
        raise SmokeFailure(f"MCP response id {request_id} has no structuredContent object")
    return value


def _assert_bool(mapping: Mapping[str, Any], key: str, expected: bool, label: str) -> None:
    if mapping.get(key) is not expected:
        raise SmokeFailure(f"{label}.{key} expected {expected!r}")


def validate(responses: list[dict[str, Any]], root: Path) -> dict[str, Any]:
    if len(responses) != 5:
        raise SmokeFailure(f"expected 5 responses (notification has no response), got {len(responses)}")
    init = _result(responses, 1)
    if init.get("protocolVersion") != PROTOCOL_VERSION:
        raise SmokeFailure("initialize did not negotiate protocol 2025-06-18")
    if not isinstance(init.get("capabilities"), dict) or not isinstance(init["capabilities"].get("tools"), dict):
        raise SmokeFailure("initialize response did not expose tools capability")

    tools_result = _result(responses, 2)
    tools = tools_result.get("tools")
    if not isinstance(tools, list) or [item.get("name") for item in tools if isinstance(item, dict)] != TOOL_NAMES or len(tools) != 3:
        raise SmokeFailure("tools/list did not expose exactly the three allowlisted tools")
    expected_annotations = {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False, "idempotentHint": True}
    for tool in tools:
        if not isinstance(tool, dict) or tool.get("annotations") != expected_annotations:
            raise SmokeFailure("tools/list annotation flags are not the read-only candidate flags")

    status_result = _result(responses, 3)
    status = _structured(status_result, 3)
    exact_status_flags: dict[str, Any] = {
        "status": "CANDIDATE_ONLY",
        "registration_status": "CANDIDATE_NOT_REGISTERED",
        "registration_performed": False,
        "manus_connector_installed": False,
        "vcgc_host_or_client_registered": False,
        "transport": "stdio",
        "network_access": False,
        "provider_calls": 0,
        "repository_writes": False,
        "full_conformance": False,
        "latest_alias_supported": False,
        "http_supported": False,
        "oauth_supported": False,
        "sampling_supported": False,
        "resources_supported": False,
        "prompts_supported": False,
    }
    for key, expected in exact_status_flags.items():
        if status.get(key) != expected:
            raise SmokeFailure(f"via_status.{key} did not match {expected!r}")

    inventory_result = _result(responses, 4)
    inventory = _structured(inventory_result, 4)
    if inventory.get("source") != str(INVENTORY_RELATIVE).replace("\\", "/"):
        raise SmokeFailure("inventory response source is not the fixed inventory path")
    if inventory.get("source_sha256") != INVENTORY_SHA256:
        raise SmokeFailure("inventory response SHA does not match the pinned caller SHA")
    if inventory.get("evidence_scope") != "LOCAL_CANDIDATE_EVIDENCE_NOT_LIVE":
        raise SmokeFailure("inventory response is not marked local candidate evidence")
    if inventory.get("registration_status") != "CANDIDATE_NOT_REGISTERED":
        raise SmokeFailure("inventory response is not marked candidate-not-registered")
    if inventory.get("limit") != 1 or inventory.get("offset") != 0:
        raise SmokeFailure("inventory query was not bounded to offset 0, limit 1")
    if not isinstance(inventory.get("rows"), list) or len(inventory["rows"]) > 1:
        raise SmokeFailure("inventory response exceeded the bounded one-row sample")

    token_result = _result(responses, 5)
    token = _structured(token_result, 5)
    if token.get("engine_source") != str(ENGINE_RELATIVE).replace("\\", "/"):
        raise SmokeFailure("token response does not identify the pinned TokenEngine source")
    if token.get("engine_sha256") != ENGINE_SHA256:
        raise SmokeFailure("token response engine SHA does not match the pinned engine")
    if token.get("provider_calls") != 0:
        raise SmokeFailure("token response provider_calls is not zero")
    _assert_bool(token, "content_persisted", False, "via_token_prepare")
    if token.get("execution_scope") != "LOCAL_PINNED_ENGINE_ONLY":
        raise SmokeFailure("token response execution scope is not local pinned engine only")

    return {
        "initialize_protocol_version": init["protocolVersion"],
        "initialized_notification_sent": True,
        "tools": TOOL_NAMES,
        "tools_exact_three": True,
        "read_only_tool_annotations": True,
        "via_status_flags": exact_status_flags,
        "inventory_sample": {
            "source": inventory["source"],
            "source_sha256_matches": True,
            "evidence_scope": inventory["evidence_scope"],
            "registration_status": inventory["registration_status"],
            "offset": inventory["offset"],
            "limit": inventory["limit"],
            "returned": inventory["returned"],
        },
        "token_sample": {
            "engine_sha256_matches": True,
            "provider_calls": token["provider_calls"],
            "content_persisted": token["content_persisted"],
            "execution_scope": token["execution_scope"],
            "safe_non_sensitive_sample": True,
        },
        "no_response_errors": True,
        "provider_calls_zero": True,
        "registration_flags_clear": True,
    }


def _response_summary(responses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    for response in responses:
        row: dict[str, Any] = {"id": response.get("id"), "has_error": "error" in response}
        result = response.get("result")
        if isinstance(result, dict):
            row["is_error"] = result.get("isError", False)
            if isinstance(result.get("structuredContent"), dict):
                content = result["structuredContent"]
                row["structured_status"] = content.get("status")
                if "provider_calls" in content:
                    row["provider_calls"] = content.get("provider_calls")
                if "registration_performed" in content:
                    row["registration_performed"] = content.get("registration_performed")
        summary.append(row)
    return summary


def _scope() -> tuple[str, str]:
    if os.name == "nt":
        return "Windows", "RUN_ON_WINDOWS_BY_CALLER"
    return "Sandbox", "NOT_RUN"


def write_once(path: Path, receipt: Mapping[str, Any]) -> None:
    if path.exists():
        raise SmokeFailure(f"refusing to overwrite existing output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(receipt, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.write("\n")
    except FileExistsError as exc:
        raise SmokeFailure(f"refusing to overwrite existing output: {path}") from exc


@dataclass
class Capture:
    returncode: int | None = None
    stdout_bytes: int = 0
    stderr_bytes: int = 0
    stderr_text: str = ""
    eof_sent: bool = False
    responses: list[dict[str, Any]] | None = None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", required=True, help="absolute staged candidate/package root")
    parser.add_argument("--out", required=True, help="absolute create-once JSON receipt path")
    args = parser.parse_args(argv)
    capture = Capture()
    scope, windows_compatibility = _scope()
    receipt: dict[str, Any] = {
        "schema": "VIA.MCPStdioSmokeReceipt.v0105.2",
        "status": "FAIL",
        "scope": scope,
        "windows_compatibility": windows_compatibility,
        "package_root": args.package_root,
        "transport": {
            "kind": "stdio",
            "jsonrpc": "2.0",
            "protocol_version": PROTOCOL_VERSION,
            "wire_format": "UTF-8 newline-delimited JSON",
            "shell": False,
            "existing_entrypoint_only": True,
        },
        "process": {
            "timeout_seconds": TIMEOUT_SECONDS,
            "eof_sent": False,
            "returncode": None,
            "stdout_bytes": 0,
            "stderr_bytes": 0,
            "stderr_empty": False,
        },
        "checks": {},
        "responses": [],
        "provider_calls": 0,
        "registration_performed": False,
        "network_access": False,
        "repository_writes": False,
        "validation_errors": [],
    }
    output_path = Path(args.out).expanduser()
    try:
        if not output_path.is_absolute():
            raise SmokeFailure("--out must be an absolute path")
        if output_path.exists():
            raise SmokeFailure(f"refusing to overwrite existing output: {output_path}")
        root = _absolute_directory(args.package_root)
        pins = pin_package(root)
        receipt["pinned_files"] = pins
        script = root / SCRIPT_RELATIVE
        requests = build_requests(root)
        returncode, stdout, stderr, eof_sent = run_process(root, script, requests)
        capture.returncode = returncode
        capture.stdout_bytes = len(stdout)
        capture.stderr_bytes = len(stderr)
        capture.stderr_text = stderr.decode("utf-8", "replace")[:1000]
        capture.eof_sent = eof_sent
        receipt["process"].update(
            {
                "command": [sys.executable, "-B", str(SCRIPT_RELATIVE).replace("\\", "/")],
                "returncode": returncode,
                "eof_sent": eof_sent,
                "stdout_bytes": len(stdout),
                "stderr_bytes": len(stderr),
                "stderr_empty": not stderr,
                "environment": {
                    "python": sys.version.split()[0],
                    "platform": sys.platform,
                    "systemroot_present": bool(os.environ.get("SystemRoot")),
                    "utf8_environment_set": True,
                },
            }
        )
        if returncode != 0:
            raise SmokeFailure(f"MCP process exited with code {returncode}")
        if stderr:
            raise SmokeFailure("MCP stderr was not empty; stdout/stderr separation check failed")
        responses = _response_lines(stdout)
        capture.responses = responses
        checks = validate(responses, root)
        receipt["checks"] = checks
        receipt["responses"] = _response_summary(responses)
        receipt["status"] = "PASS"
        receipt["process"]["clean_eof_exit"] = True
        print(f"PASS: stdio smoke receipt -> {output_path}")
        write_once(output_path, receipt)
        return 0
    except (SmokeFailure, OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        message = str(exc)[:1000] or exc.__class__.__name__
        receipt["validation_errors"] = [message]
        receipt["process"].update(
            {
                "returncode": capture.returncode,
                "eof_sent": capture.eof_sent,
                "stdout_bytes": capture.stdout_bytes,
                "stderr_bytes": capture.stderr_bytes,
                "stderr_empty": capture.stderr_bytes == 0,
            }
        )
        if capture.responses is not None:
            receipt["responses"] = _response_summary(capture.responses)
        try:
            write_once(output_path, receipt)
        except SmokeFailure as write_exc:
            print(f"FAIL: {message}; receipt not written: {write_exc}", file=sys.stderr)
            return 1
        print(f"FAIL: {message}; receipt -> {output_path}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
