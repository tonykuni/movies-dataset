#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline tests for vcgc_remote_preflight.py; no remote service is contacted."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).with_name("vcgc_remote_preflight.py")
spec = importlib.util.spec_from_file_location("vcgc_remote_preflight_tested", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def valid_profile() -> dict:
    endpoint = "https://mcp.example.org/via/mcp"
    return {
        "schema": mod.PROFILE_SCHEMA,
        "enabled": False,
        "transport": "streamable-http",
        "mcp_protocol_version": "2026-07-28",
        "endpoint": endpoint,
        "allowed_hosts": ["mcp.example.org"],
        "issuer_allowed_hosts": ["auth.example.org"],
        "oauth": {
            "mode": "oauth2.1",
            "issuer_url": "https://auth.example.org/realms/vcgc",
            "resource": endpoint,
            "scopes": ["vcgc:read"],
            "read_only_scopes": ["vcgc:read"],
        },
        "tls_verify": True,
        "allow_redirects": False,
        "write_tools_enabled": False,
        "allow_private_network": False,
        "timeout_seconds": 5,
        "data_scope": ["approved-project-id", "read-only metadata fields"],
        "allowed_tools": [{"name": "vcgc.status.read", "access": "read"}],
    }


class RemotePreflightTests(unittest.TestCase):
    def test_valid_profile_has_no_network_side_effect(self):
        with patch.object(mod.socket, "getaddrinfo", side_effect=AssertionError("network must not run")):
            result = mod.validate_profile(valid_profile())
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["network_requests_performed"], 0)
        self.assertFalse(result["credentials_sent"])

    def test_http_userinfo_query_and_fragment_rejected(self):
        for endpoint in (
            "http://mcp.example.org/via/mcp",
            "https://user:pass@mcp.example.org/via/mcp",
            "https://mcp.example.org/via/mcp?token=x",
            "https://mcp.example.org/via/mcp#fragment",
        ):
            with self.subTest(endpoint=endpoint):
                profile = valid_profile()
                profile["endpoint"] = endpoint
                result = mod.validate_profile(profile)
                self.assertFalse(result["valid"])

    def test_host_allowlist_is_exact_and_no_wildcards(self):
        profile = valid_profile()
        profile["allowed_hosts"] = ["other.example.org"]
        self.assertFalse(mod.validate_profile(profile)["valid"])
        profile = valid_profile()
        profile["allowed_hosts"] = ["*.example.org"]
        self.assertFalse(mod.validate_profile(profile)["valid"])

    def test_oauth_scope_must_be_read_only_subset(self):
        profile = valid_profile()
        profile["oauth"]["scopes"] = ["vcgc:read", "vcgc:write"]
        result = mod.validate_profile(profile)
        self.assertFalse(result["valid"])
        self.assertTrue(any("subset" in x for x in result["errors"]))

    def test_write_flags_and_enabled_profile_are_rejected(self):
        for key, value in (("tls_verify", False), ("allow_redirects", True),
                           ("write_tools_enabled", True), ("enabled", True)):
            with self.subTest(key=key):
                profile = valid_profile()
                profile[key] = value
                self.assertFalse(mod.validate_profile(profile)["valid"])

    def test_credentials_are_not_permitted_in_profile(self):
        profile = valid_profile()
        profile["oauth"]["access_token"] = "synthetic-never-real"
        result = mod.validate_profile(profile)
        self.assertFalse(result["valid"])
        self.assertTrue(any("credentials" in x for x in result["errors"]))

    def test_placeholder_profile_is_not_ready(self):
        profile = valid_profile()
        profile["endpoint"] = "https://VCGC_HOST/via/mcp"
        profile["allowed_hosts"] = ["VCGC_HOST"]
        profile["oauth"]["resource"] = profile["endpoint"]
        result = mod.validate_profile(profile)
        self.assertFalse(result["valid"])
        self.assertTrue(any("placeholder" in x for x in result["errors"]))

    def test_unsupported_transport_and_version_are_rejected(self):
        profile = valid_profile()
        profile["transport"] = "stdio"
        profile["mcp_protocol_version"] = "unknown"
        self.assertFalse(mod.validate_profile(profile)["valid"])

    def test_tool_list_exact_match_passes_without_invoking_tools(self):
        profile = valid_profile()
        actual = {"result": {"tools": [{"name": "vcgc.status.read", "description": "read"}]}}
        result = mod.check_tools_list(profile, actual)
        self.assertTrue(result["valid"], result)
        self.assertFalse(result["tool_call_performed"])

    def test_tool_list_extra_missing_and_duplicate_names_fail(self):
        profile = valid_profile()
        extra = mod.check_tools_list(profile, {"tools": [{"name": "vcgc.status.read"}, {"name": "vcgc.delete"}]})
        self.assertFalse(extra["valid"])
        self.assertEqual(extra["unexpected"], ["vcgc.delete"])
        missing = mod.check_tools_list(profile, {"tools": []})
        self.assertFalse(missing["valid"])
        self.assertEqual(missing["missing"], ["vcgc.status.read"])
        duplicate = mod.check_tools_list(profile, {"tools": [{"name": "vcgc.status.read"}, {"name": "vcgc.status.read"}]})
        self.assertFalse(duplicate["valid"])
        self.assertTrue(duplicate["duplicate_actual_names"])

    def test_malformed_tools_list_fails_closed(self):
        result = mod.check_tools_list(valid_profile(), {"tools": [{"description": "missing name"}]})
        self.assertFalse(result["valid"])
        self.assertEqual(result["status"], "INVALID_TOOLS_LIST")

    def test_local_validate_cli_does_not_resolve_dns(self):
        with tempfile.TemporaryDirectory(prefix="vcgc-preflight-test-") as temp:
            config = Path(temp) / "profile.json"
            config.write_text(json.dumps(valid_profile()), encoding="utf-8")
            output = io.StringIO()
            with patch.object(mod.socket, "getaddrinfo", side_effect=AssertionError("DNS must not run")):
                with contextlib.redirect_stdout(output):
                    code = mod.main(["--config", str(config)])
            result = json.loads(output.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "CONFIG_VALID")
        self.assertFalse(result["http_request_sent"])
        self.assertFalse(result["mcp_handshake_performed"])

    def test_cli_tools_list_export_success_and_mismatch(self):
        with tempfile.TemporaryDirectory(prefix="vcgc-tools-cli-") as temp:
            root = Path(temp)
            config = root / "profile.json"
            tools = root / "tools.json"
            config.write_text(json.dumps(valid_profile()), encoding="utf-8")
            tools.write_text(json.dumps({"result": {"tools": [{"name": "vcgc.status.read"}]}}), encoding="utf-8")
            output = io.StringIO()
            with patch.object(mod.socket, "getaddrinfo", side_effect=AssertionError("DNS must not run")):
                with contextlib.redirect_stdout(output):
                    code = mod.main(["--config", str(config), "--tools-json", str(tools)])
            passed = json.loads(output.getvalue())
            self.assertEqual(code, 0)
            self.assertTrue(passed["tools_allowlist_check"]["valid"])

            tools.write_text(json.dumps({"tools": [{"name": "vcgc.status.read"}, {"name": "vcgc.delete"}]}), encoding="utf-8")
            output = io.StringIO()
            with patch.object(mod.socket, "getaddrinfo", side_effect=AssertionError("DNS must not run")):
                with contextlib.redirect_stdout(output):
                    code = mod.main(["--config", str(config), "--tools-json", str(tools)])
            blocked = json.loads(output.getvalue())
            self.assertEqual(code, 2)
            self.assertEqual(blocked["status"], "BLOCKED_TOOL_ALLOWLIST_MISMATCH")
            self.assertEqual(blocked["tools_allowlist_check"]["unexpected"], ["vcgc.delete"])

    def test_tls_probe_rejects_invalid_profile_before_dns(self):
        profile = valid_profile()
        profile["tls_verify"] = False
        with patch.object(mod.socket, "getaddrinfo", side_effect=AssertionError("DNS must not run")):
            result = mod.tls_probe(profile)
        self.assertEqual(result["status"], "BLOCKED_INVALID_PROFILE")
        self.assertFalse(result["credentials_sent"])

    def test_tls_probe_blocks_private_dns_by_default(self):
        profile = valid_profile()
        fake = [(mod.socket.AF_INET, mod.socket.SOCK_STREAM, 6, "", ("10.0.0.7", 443))]
        with patch.object(mod.socket, "getaddrinfo", return_value=fake), \
             patch.object(mod.socket, "socket", side_effect=AssertionError("must block before connect")):
            result = mod.tls_probe(profile)
        self.assertEqual(result["status"], "BLOCKED_NON_GLOBAL_DESTINATION")
        self.assertFalse(result["http_request_sent"])
        self.assertFalse(result["mcp_handshake_performed"])

    def test_ip_policy_requires_explicit_private_network_opt_in(self):
        self.assertFalse(mod._ip_allowed("10.1.2.3", False))
        self.assertTrue(mod._ip_allowed("10.1.2.3", True))
        self.assertFalse(mod._ip_allowed("127.0.0.1", True))
        self.assertFalse(mod._ip_allowed("169.254.1.1", True))

    def test_duplicate_keys_and_nan_are_rejected(self):
        with self.assertRaises(ValueError):
            mod.strict_json_loads('{"x":1,"x":2}')
        with self.assertRaises(ValueError):
            mod.strict_json_loads('{"x":NaN}')

    def test_profile_structure_depth_and_list_budgets_fail_closed(self):
        profile = valid_profile()
        root = {}
        cursor = root
        for _ in range(mod.MAX_JSON_DEPTH + 5):
            cursor["nested"] = {}
            cursor = cursor["nested"]
        profile["extension"] = root
        deep = mod.validate_profile(profile)
        self.assertFalse(deep["valid"])
        self.assertTrue(any("depth" in error for error in deep["errors"]))

        profile = valid_profile()
        profile["extension"] = list(range(mod.MAX_LIST_ITEMS + 1))
        large_list = mod.validate_profile(profile)
        self.assertFalse(large_list["valid"])
        self.assertTrue(any("list exceeds" in error for error in large_list["errors"]))

    def test_deep_json_file_is_rejected_not_uncaught(self):
        deep_json = '{"x":' * 10000 + "0" + "}" * 10000
        with tempfile.TemporaryDirectory(prefix="vcgc-deep-json-") as temp:
            path = Path(temp) / "deep.json"
            path.write_text(deep_json, encoding="utf-8")
            with self.assertRaises(ValueError):
                mod._read_bounded_json(path, mod.MAX_PROFILE_BYTES)

    def test_profile_file_limit_and_symlink_guard(self):
        with tempfile.TemporaryDirectory(prefix="vcgc-profile-file-") as temp:
            root = Path(temp)
            large = root / "large.json"
            large.write_bytes(b" " * (mod.MAX_PROFILE_BYTES + 1))
            with self.assertRaises(ValueError):
                mod._read_bounded_json(large, mod.MAX_PROFILE_BYTES)
            target = root / "target.json"
            target.write_text("{}", encoding="utf-8")
            link = root / "link.json"
            link.symlink_to(target)
            with self.assertRaises(ValueError):
                mod._read_bounded_json(link, mod.MAX_PROFILE_BYTES)


if __name__ == "__main__":
    unittest.main(verbosity=2)
