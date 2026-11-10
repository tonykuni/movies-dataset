#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA remote VCGC preflight; this is not a VCGC client or MCP handshake client.

Default mode validates a local profile and never opens a network connection.
--tls-check performs an explicit TLS-only handshake to the configured HTTPS
host; it sends no HTTP request, MCP message, OAuth token, or user data.
--tools-json checks a locally exported tools/list response against an exact
read-only allowlist; it never invokes a tool.
"""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import os
import re
import socket
import ssl
import sys
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlsplit

PROFILE_SCHEMA = "VIA_VCGC_REMOTE_PROFILE/1.0"
SUPPORTED_MCP_VERSIONS = {"2026-07-28", "2025-11-25"}
MAX_PROFILE_BYTES = 128 * 1024
MAX_TOOLS_JSON_BYTES = 1024 * 1024
MAX_DNS_RESULTS = 32
MAX_JSON_NODES = 20000
MAX_JSON_DEPTH = 64
MAX_LIST_ITEMS = 1000
MAX_TIMEOUT_SECONDS = 10
_SECRET_KEY_PARTS = ("token", "secret", "password", "credential", "private_key", "api_key")
_PLACEHOLDER_RE = re.compile(r"(?:<[^>]+>|\b(?:TODO|TBD|PLACEHOLDER|VCGC_HOST|AUTH_HOST|ACTUAL_[A-Z0-9_]+)\b)", re.I)


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise ValueError(f"duplicate JSON key refused: {key}")
        out[key] = value
    return out


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant refused: {value}")


def strict_json_loads(text: str) -> Any:
    return json.loads(text, object_pairs_hook=_unique_pairs, parse_constant=_reject_constant)


def _read_bounded_json(path_value: str | Path, limit: int) -> Any:
    path = Path(path_value).expanduser()
    if path.is_symlink() or not path.is_file():
        raise ValueError("input must be a regular, non-symlink file")
    if path.stat().st_size > limit:
        raise ValueError("input exceeds the configured size limit")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(str(path), flags)
    try:
        with os.fdopen(fd, "rb", closefd=False) as stream:
            raw = stream.read(limit + 1)
        if len(raw) > limit:
            raise ValueError("input grew beyond the configured size limit")
        try:
            return strict_json_loads(raw.decode("utf-8"))
        except RecursionError as exc:
            raise ValueError("JSON nesting exceeds the parser safety limit") from exc
    finally:
        os.close(fd)


def _https_host(value: Any, field: str) -> tuple[str | None, int | None, str | None]:
    if not isinstance(value, str) or not value:
        return None, None, f"{field} must be an HTTPS URL"
    try:
        parsed = urlsplit(value)
        host = parsed.hostname
        port = parsed.port or 443
    except ValueError:
        return None, None, f"{field} is not a valid URL"
    if parsed.scheme.lower() != "https" or not host:
        return None, None, f"{field} must use HTTPS and include a host"
    if parsed.username is not None or parsed.password is not None:
        return None, None, f"{field} must not contain URL credentials"
    if parsed.query or parsed.fragment:
        return None, None, f"{field} must not contain query strings or fragments"
    if not 1 <= port <= 65535:
        return None, None, f"{field} has an invalid port"
    return host.lower().rstrip("."), port, None


def _inspect_profile_structure(value: Any, root_path: str = "$") -> tuple[list[str], list[str], list[str]]:
    forbidden: list[str] = []
    placeholders: list[str] = []
    errors: list[str] = []
    stack: list[tuple[str, Any, int, frozenset[int]]] = [(root_path, value, 0, frozenset())]
    nodes = 0
    while stack:
        path, item, depth, ancestors = stack.pop()
        nodes += 1
        if nodes > MAX_JSON_NODES:
            errors.append(f"JSON structure exceeds {MAX_JSON_NODES} nodes")
            break
        if depth > MAX_JSON_DEPTH:
            errors.append(f"JSON structure exceeds depth {MAX_JSON_DEPTH} at {path[:160]}")
            continue
        if isinstance(item, (Mapping, list)):
            identity = id(item)
            if identity in ancestors:
                errors.append(f"cyclic structure refused at {path[:160]}")
                continue
            next_ancestors = ancestors | {identity}
        else:
            next_ancestors = ancestors
        if isinstance(item, Mapping):
            for key, child in reversed(list(item.items())):
                key_text = str(key)
                normalized = key_text.lower().replace("-", "_")
                child_path = f"{path}.{key_text}"
                if any(part in normalized for part in _SECRET_KEY_PARTS):
                    forbidden.append(child_path[:200])
                stack.append((child_path, child, depth + 1, next_ancestors))
        elif isinstance(item, list):
            if len(item) > MAX_LIST_ITEMS:
                errors.append(f"list exceeds {MAX_LIST_ITEMS} items at {path[:160]}")
            for index in range(min(len(item), MAX_LIST_ITEMS) - 1, -1, -1):
                stack.append((f"{path}[{index}]", item[index], depth + 1, next_ancestors))
        elif isinstance(item, str) and _PLACEHOLDER_RE.search(item):
            placeholders.append(path[:200])
        if len(forbidden) > 100 or len(placeholders) > 100 or len(errors) > 100:
            errors.append("profile findings exceed the safety cap")
            break
    return forbidden[:100], placeholders[:100], errors[:100]


def _find_forbidden_keys(value: Any, path: str = "$") -> list[str]:
    return _inspect_profile_structure(value, path)[0]


def _find_placeholders(value: Any, path: str = "$") -> list[str]:
    return _inspect_profile_structure(value, path)[1]


def validate_profile(profile: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(profile, Mapping):
        return {"valid": False, "errors": ["profile root must be an object"]}

    if profile.get("schema") != PROFILE_SCHEMA:
        errors.append("schema must be VIA_VCGC_REMOTE_PROFILE/1.0")
    if profile.get("transport") != "streamable-http":
        errors.append("transport must be streamable-http; REST/other transports need a separately reviewed adapter")
    if profile.get("mcp_protocol_version") not in SUPPORTED_MCP_VERSIONS:
        errors.append("mcp_protocol_version must name an explicitly reviewed supported version")

    endpoint_host, endpoint_port, endpoint_error = _https_host(profile.get("endpoint"), "endpoint")
    if endpoint_error:
        errors.append(endpoint_error)

    allowed_hosts = profile.get("allowed_hosts")
    if not isinstance(allowed_hosts, list) or not allowed_hosts or any(not isinstance(x, str) or not x for x in allowed_hosts):
        errors.append("allowed_hosts must be a non-empty exact-host allowlist")
        allowed_host_set: set[str] = set()
    else:
        normalized_hosts = [host.lower().rstrip(".") for host in allowed_hosts]
        if len(set(normalized_hosts)) != len(normalized_hosts) or any("*" in host for host in normalized_hosts):
            errors.append("allowed_hosts must contain unique exact hostnames; wildcards are forbidden")
        allowed_host_set = set(normalized_hosts)
        if endpoint_host and endpoint_host not in allowed_host_set:
            errors.append("endpoint hostname is not in allowed_hosts")

    if profile.get("tls_verify") is not True:
        errors.append("tls_verify must be true")
    if profile.get("allow_redirects") is not False:
        errors.append("allow_redirects must be false")
    if profile.get("write_tools_enabled") is not False:
        errors.append("write_tools_enabled must be false")
    if profile.get("enabled") is not False:
        errors.append("profile must remain disabled until separately approved")
    if not isinstance(profile.get("allow_private_network", False), bool):
        errors.append("allow_private_network must be boolean")

    auth = profile.get("oauth")
    if not isinstance(auth, Mapping) or auth.get("mode") != "oauth2.1":
        errors.append("oauth.mode must be oauth2.1 for the remote MCP profile")
    else:
        issuer_host, _, issuer_error = _https_host(auth.get("issuer_url"), "oauth.issuer_url")
        if issuer_error:
            errors.append(issuer_error)
        issuer_hosts = profile.get("issuer_allowed_hosts")
        if not isinstance(issuer_hosts, list) or not issuer_hosts or any(not isinstance(x, str) for x in issuer_hosts):
            errors.append("issuer_allowed_hosts must be an explicit exact-host allowlist")
        elif issuer_host and issuer_host not in {x.lower().rstrip(".") for x in issuer_hosts}:
            errors.append("OAuth issuer hostname is not in issuer_allowed_hosts")
        resource_host, _, resource_error = _https_host(auth.get("resource"), "oauth.resource")
        if resource_error:
            errors.append(resource_error)
        if profile.get("endpoint") and auth.get("resource") != profile.get("endpoint"):
            errors.append("oauth.resource must exactly equal the canonical MCP endpoint URI")
        scopes = auth.get("scopes")
        read_scopes = auth.get("read_only_scopes")
        if not isinstance(scopes, list) or not scopes or any(not isinstance(x, str) or not x for x in scopes):
            errors.append("oauth.scopes must be a non-empty list")
        if not isinstance(read_scopes, list) or any(not isinstance(x, str) or not x for x in read_scopes):
            errors.append("oauth.read_only_scopes must be an explicit list")
        elif isinstance(scopes, list) and not set(scopes).issubset(set(read_scopes)):
            errors.append("requested OAuth scopes must be a subset of read_only_scopes")

    tools = profile.get("allowed_tools")
    if not isinstance(tools, list) or not tools:
        errors.append("allowed_tools must be an explicit non-empty allowlist")
    else:
        names: list[str] = []
        for index, tool in enumerate(tools):
            if not isinstance(tool, Mapping) or not isinstance(tool.get("name"), str) or not tool.get("name"):
                errors.append(f"allowed_tools[{index}] must include a tool name")
                continue
            names.append(tool["name"])
            if tool.get("access") != "read":
                errors.append(f"allowed_tools[{index}].access must be read")
        if len(names) != len(set(names)):
            errors.append("allowed_tools names must be unique")

    data_scope = profile.get("data_scope")
    if not isinstance(data_scope, list) or not data_scope or any(not isinstance(x, str) or not x.strip() for x in data_scope):
        errors.append("data_scope must enumerate approved repository/project/data boundaries")

    timeout = profile.get("timeout_seconds", 5)
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 1 <= timeout <= MAX_TIMEOUT_SECONDS:
        errors.append(f"timeout_seconds must be between 1 and {MAX_TIMEOUT_SECONDS}")

    ca_file = profile.get("ca_file")
    if ca_file not in (None, ""):
        if not isinstance(ca_file, str):
            errors.append("ca_file must be a local file path or empty")
        else:
            ca_path = Path(ca_file).expanduser()
            if ca_path.is_symlink() or not ca_path.is_file():
                errors.append("ca_file must name an existing regular non-symlink file")

    pin = profile.get("certificate_sha256")
    if pin not in (None, "") and (not isinstance(pin, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", pin)):
        errors.append("certificate_sha256 must be an optional 64-hex SHA-256 fingerprint")

    secret_keys, placeholders, structure_errors = _inspect_profile_structure(profile)
    if secret_keys:
        errors.append("profile must not contain credentials or secret-valued fields")
    if placeholders:
        errors.append("profile still contains placeholder values: " + ", ".join(placeholders[:12]))
    errors.extend(structure_errors)

    return {"valid": not errors, "errors": errors,
            "endpoint_host": endpoint_host, "endpoint_port": endpoint_port,
            "network_requests_performed": 0, "credentials_sent": False}


def check_tools_list(profile: Mapping[str, Any], tools_document: Any) -> dict[str, Any]:
    if isinstance(tools_document, Mapping) and isinstance(tools_document.get("result"), Mapping):
        tools_document = tools_document["result"]
    if isinstance(tools_document, Mapping) and isinstance(tools_document.get("tools"), list):
        tools = tools_document["tools"]
    else:
        return {"valid": False, "status": "INVALID_TOOLS_LIST", "unexpected": [], "missing": []}
    actual: list[str] = []
    for item in tools:
        if not isinstance(item, Mapping) or not isinstance(item.get("name"), str):
            return {"valid": False, "status": "INVALID_TOOLS_LIST", "unexpected": [], "missing": []}
        actual.append(item["name"])
    expected = [x["name"] for x in profile.get("allowed_tools", []) if isinstance(x, Mapping) and isinstance(x.get("name"), str)]
    unexpected = sorted(set(actual) - set(expected))
    missing = sorted(set(expected) - set(actual))
    duplicate_actual = len(actual) != len(set(actual))
    valid = not unexpected and not missing and not duplicate_actual
    return {"valid": valid, "status": "PASS" if valid else "TOOL_ALLOWLIST_MISMATCH",
            "expected_count": len(expected), "actual_count": len(actual),
            "unexpected": unexpected, "missing": missing,
            "duplicate_actual_names": duplicate_actual,
            "tool_call_performed": False}


def _ip_allowed(address: str, allow_private: bool) -> bool:
    ip = ipaddress.ip_address(address.split("%", 1)[0])
    return ip.is_global or (allow_private and not (ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_unspecified))


def tls_probe(profile: Mapping[str, Any]) -> dict[str, Any]:
    """Explicit TLS-only check. No HTTP/MCP/OAuth message or credential is sent."""
    valid = validate_profile(profile)
    if not valid["valid"]:
        return {"status": "BLOCKED_INVALID_PROFILE", "errors": valid["errors"],
                "http_request_sent": False, "mcp_handshake_performed": False, "credentials_sent": False}
    host, port = valid["endpoint_host"], valid["endpoint_port"]
    timeout = float(profile.get("timeout_seconds", 5))
    try:
        results = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        if not results or len(results) > MAX_DNS_RESULTS:
            return {"status": "BLOCKED_DNS_RESULT_LIMIT", "http_request_sent": False,
                    "mcp_handshake_performed": False, "credentials_sent": False}
        addresses = []
        for family, socktype, proto, _, sockaddr in results:
            address = sockaddr[0]
            if address not in addresses:
                addresses.append(address)
            if not _ip_allowed(address, bool(profile.get("allow_private_network", False))):
                return {"status": "BLOCKED_NON_GLOBAL_DESTINATION", "resolved_ip_count": len(addresses),
                        "http_request_sent": False, "mcp_handshake_performed": False, "credentials_sent": False}

        ca_file = profile.get("ca_file")
        context = ssl.create_default_context(cafile=ca_file or None)
        last_error: Exception | None = None
        for family, socktype, proto, _, sockaddr in results:
            sock = socket.socket(family, socktype, proto)
            try:
                sock.settimeout(timeout)
                sock.connect(sockaddr)  # connect to the exact resolved address; no second DNS lookup
                with context.wrap_socket(sock, server_hostname=host) as tls_socket:
                    cert_der = tls_socket.getpeercert(binary_form=True)
                    cert_info = tls_socket.getpeercert()
                    fingerprint = hashlib.sha256(cert_der).hexdigest()
                    expected_pin = profile.get("certificate_sha256")
                    if expected_pin and fingerprint.lower() != expected_pin.lower():
                        return {"status": "BLOCKED_CERTIFICATE_PIN_MISMATCH", "fingerprint_sha256": fingerprint,
                                "http_request_sent": False, "mcp_handshake_performed": False, "credentials_sent": False}
                    return {"status": "TLS_OK", "host": host, "port": port, "resolved_ips": addresses,
                            "fingerprint_sha256": fingerprint,
                            "certificate_subject": cert_info.get("subject", []),
                            "http_request_sent": False, "mcp_handshake_performed": False,
                            "credentials_sent": False}
            except (OSError, ssl.SSLError, TimeoutError) as exc:
                last_error = exc
                try:
                    sock.close()
                except OSError:
                    pass
        return {"status": "TLS_FAILED", "error_type": type(last_error).__name__ if last_error else "UnknownError",
                "http_request_sent": False, "mcp_handshake_performed": False, "credentials_sent": False}
    except (OSError, ValueError, ssl.SSLError) as exc:
        return {"status": "TLS_FAILED", "error_type": type(exc).__name__,
                "http_request_sent": False, "mcp_handshake_performed": False, "credentials_sent": False}


def _json_print(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="local VCGC remote profile JSON; contains no credentials")
    parser.add_argument("--tls-check", action="store_true", help="explicitly perform TLS-only handshake; sends no HTTP or credentials")
    parser.add_argument("--tools-json", help="local JSON file containing the host's tools/list response; no tool is invoked")
    args = parser.parse_args(argv)
    try:
        profile = _read_bounded_json(args.config, MAX_PROFILE_BYTES)
        result = validate_profile(profile)
        result["status"] = "CONFIG_VALID" if result["valid"] else "BLOCKED_INVALID_PROFILE"
        if result["valid"] and args.tools_json:
            tools_doc = _read_bounded_json(args.tools_json, MAX_TOOLS_JSON_BYTES)
            result["tools_allowlist_check"] = check_tools_list(profile, tools_doc)
            if not result["tools_allowlist_check"]["valid"]:
                result["valid"] = False
                result["status"] = "BLOCKED_TOOL_ALLOWLIST_MISMATCH"
        if result["valid"] and args.tls_check:
            result["tls_probe"] = tls_probe(profile)
            if result["tls_probe"].get("status") != "TLS_OK":
                result["valid"] = False
                result["status"] = result["tls_probe"].get("status", "TLS_FAILED")
        result["http_request_sent"] = False
        result["mcp_handshake_performed"] = False
        result["tool_call_performed"] = False
        result["credentials_sent"] = False
        _json_print(result)
        return 0 if result["valid"] else (3 if args.tls_check and result.get("tls_probe", {}).get("status") not in (None, "TLS_OK") else 2)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        _json_print({"status": "BLOCKED_INPUT", "error_type": type(exc).__name__,
                     "http_request_sent": False, "mcp_handshake_performed": False,
                     "tool_call_performed": False, "credentials_sent": False})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
