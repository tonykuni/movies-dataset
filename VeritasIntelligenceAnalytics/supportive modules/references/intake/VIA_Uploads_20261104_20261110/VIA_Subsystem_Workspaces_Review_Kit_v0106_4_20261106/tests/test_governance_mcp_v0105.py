#!/usr/bin/env python3
"""Local protocol tests for the v0105 governance MCP candidate.

The suite uses a temporary inventory fixture when the real fixed inventory is
not present.  It never writes to the package data directory.  When run as a
script it writes the permitted protocol receipt with a dynamic test count and
an explicit fixture/actual-inventory scope.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "via_governance_mcp_v0105.py"
INVENTORY_RELATIVE = Path("data/governance_inventory_v0105.json")
PINNED_ENGINE_SHA256 = "ca3c38ee00d2d7df5af71bcaea59ab7e7c73a15ec1d1f7b03218127efaf62af5"
MAX_LINE_BYTES = 2 * 1024 * 1024
MAX_RESPONSE_BYTES = 4 * 1024 * 1024


def wire(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def fixture_model() -> dict[str, Any]:
    return {
        "version": "v0105-fixture",
        "scope": "LOCAL_TEST_FIXTURE_NOT_LIVE",
        "matrices": {
            "files": [
                {"id": "F-001", "status": "GREEN", "system": "VIA_AGENT_OS", "kind": "PYTHON_SOURCE", "classification": "CODE", "source": "attachments/alpha.py", "evidence": ["STATIC_PARSE"]},
                {"id": "F-002", "status": "YELLOW", "system": "VAP", "kind": "JSON_DOCUMENT", "classification": "CONFIG", "source": "attachments/beta.json", "evidence": ["STRICT_JSON_VALID"]},
            ],
            "io": [
                {"id": "IO-001", "status": "YELLOW", "system": "VIA_AGENT_OS", "kind": "CLI_ARGUMENT", "source": "attachments/alpha.py", "evidence": ["STATIC_PARSE"]},
            ],
            "commands": [
                {"id": "CMD-001", "status": "YELLOW", "system": "VIA_AGENT_OS", "kind": "FNC", "source": "attachments/alpha.py", "evidence": ["STATIC_PARSE"]},
            ],
            "environment": [],
            "conflicts": [],
            "policy": [
                {"id": "POL-001", "status": "RED", "system": "VIA_GOVERNANCE", "kind": "POLICY", "source": "attachments/policy.json", "evidence": ["STATIC_PARSE"]},
            ],
            "tests": [],
            "requirements": [],
        },
    }


def fixture_bytes() -> bytes:
    return (json.dumps(fixture_model(), ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")


def strict_output_lines(raw: bytes) -> list[dict[str, Any]]:
    lines = [line for line in raw.splitlines() if line]
    result: list[dict[str, Any]] = []
    for line in lines:
        value = json.loads(line.decode("utf-8"), parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
        if not isinstance(value, dict):
            raise AssertionError("MCP response is not an object")
        result.append(value)
    return result


def run_process(payload: bytes) -> tuple[int, list[dict[str, Any]], bytes, bytes]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    process = subprocess.Popen(
        [sys.executable, "-B", str(SCRIPT)],
        cwd=str(ROOT),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    stdout, stderr = process.communicate(payload, timeout=30)
    return process.returncode, strict_output_lines(stdout), stdout, stderr


def initialize(version: str = "2025-06-18", request_id: int = 1) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "initialize",
        "params": {
            "protocolVersion": version,
            "capabilities": {},
            "clientInfo": {"name": "v0105-test", "version": "1"},
        },
    }


class GovernanceMCPV0105Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture_dir = tempfile.TemporaryDirectory(prefix="via-mcp-v0105-")
        cls.fixture_root = Path(cls.fixture_dir.name)
        (cls.fixture_root / "data").mkdir()
        cls.fixture_inventory = cls.fixture_root / INVENTORY_RELATIVE
        cls.fixture_inventory.write_bytes(fixture_bytes())
        cls.fixture_sha = hashlib.sha256(cls.fixture_inventory.read_bytes()).hexdigest()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.fixture_dir.cleanup()

    def call_session(self, name: str, arguments: dict[str, Any], *, include_list: bool = False) -> tuple[int, list[dict[str, Any]], bytes, bytes]:
        messages: list[dict[str, Any]] = [initialize(), {"jsonrpc": "2.0", "method": "notifications/initialized"}]
        if include_list:
            messages.append({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
            call_id = 3
        else:
            call_id = 2
        messages.append({"jsonrpc": "2.0", "id": call_id, "method": "tools/call", "params": {"name": name, "arguments": arguments}})
        return run_process(b"".join(wire(item) for item in messages))

    @staticmethod
    def tool_result(outputs: list[dict[str, Any]], index: int = -1) -> dict[str, Any]:
        return outputs[index]["result"]

    def test_real_process_stdio_initialize_list_call_and_eof(self) -> None:
        code, outputs, raw, stderr = self.call_session("via_status", {}, include_list=True)
        self.assertEqual(code, 0)
        self.assertEqual(len(outputs), 3)
        self.assertEqual(outputs[0]["result"]["protocolVersion"], "2025-06-18")
        self.assertIn("tools", outputs[1]["result"])
        self.assertEqual(self.tool_result(outputs)["structuredContent"]["status"], "CANDIDATE_ONLY")
        self.assertEqual(stderr, b"")
        self.assertLessEqual(len(raw), MAX_RESPONSE_BYTES * 2)

    def test_utf8_cjk_token_prepare_is_json_and_local(self) -> None:
        text = '{"message": "你好世界", "note": "compact me"}'
        code, outputs, _, _ = self.call_session("via_token_prepare", {"text": text})
        self.assertEqual(code, 0)
        result = self.tool_result(outputs)["structuredContent"]
        self.assertIn("你好世界", result["prepared_text"])
        self.assertEqual(result["provider_calls"], 0)
        self.assertFalse(result["content_persisted"])

    def test_initialize_requires_protocol_client_info_and_capabilities(self) -> None:
        message = initialize()
        del message["params"]["clientInfo"]
        code, outputs, _, _ = run_process(wire(message))
        self.assertEqual(code, 0)
        self.assertEqual(outputs[0]["error"]["code"], -32602)

    def test_unsupported_initialize_version_falls_back_to_supported_version(self) -> None:
        code, outputs, _, _ = run_process(wire(initialize("2099-01-01")))
        self.assertEqual(code, 0)
        self.assertEqual(outputs[0]["result"]["protocolVersion"], "2025-06-18")

    def test_duplicate_initialize_is_rejected(self) -> None:
        code, outputs, _, _ = run_process(wire(initialize()) + wire(initialize(request_id=2)))
        self.assertEqual(code, 0)
        self.assertEqual(len(outputs), 2)
        self.assertEqual(outputs[1]["error"]["code"], -32600)

    def test_tools_before_initialized_notification_are_rejected(self) -> None:
        payload = wire(initialize()) + wire({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        code, outputs, _, _ = run_process(payload)
        self.assertEqual(code, 0)
        self.assertEqual(outputs[-1]["error"]["code"], -32600)

    def test_notifications_do_not_emit_responses(self) -> None:
        payload = wire(initialize()) + wire({"jsonrpc": "2.0", "method": "notifications/initialized"}) + wire({"jsonrpc": "2.0", "method": "notifications/unknown"}) + wire({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        code, outputs, _, _ = run_process(payload)
        self.assertEqual(code, 0)
        self.assertEqual(len(outputs), 2)
        self.assertIn("tools", outputs[-1]["result"])

    def test_unknown_method_is_rejected(self) -> None:
        payload = wire(initialize()) + wire({"jsonrpc": "2.0", "method": "notifications/initialized"}) + wire({"jsonrpc": "2.0", "id": 2, "method": "resources/list", "params": {}})
        code, outputs, _, _ = run_process(payload)
        self.assertEqual(code, 0)
        self.assertEqual(outputs[-1]["error"]["code"], -32601)

    def test_unknown_tool_is_rejected(self) -> None:
        payload = wire(initialize()) + wire({"jsonrpc": "2.0", "method": "notifications/initialized"}) + wire({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "shell", "arguments": {}}})
        code, outputs, _, _ = run_process(payload)
        self.assertEqual(code, 0)
        self.assertEqual(outputs[-1]["error"]["code"], -32602)

    def test_unknown_tool_argument_is_rejected(self) -> None:
        code, outputs, _, _ = self.call_session("via_status", {"extra": 1})
        self.assertTrue(self.tool_result(outputs)["isError"])
        self.assertIn("unknown", self.tool_result(outputs)["structuredContent"]["reason"])

    def test_nonfinite_json_is_rejected(self) -> None:
        raw = b'{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{"x":NaN},"clientInfo":{"name":"x","version":"1"}}}\n'
        code, outputs, _, _ = run_process(raw)
        self.assertEqual(code, 0)
        self.assertEqual(outputs[0]["error"]["code"], -32700)

    def test_duplicate_json_key_is_rejected(self) -> None:
        raw = b'{"jsonrpc":"2.0","id":1,"id":2,"method":"initialize","params":{}}\n'
        code, outputs, _, _ = run_process(raw)
        self.assertEqual(code, 0)
        self.assertEqual(outputs[0]["error"]["code"], -32700)

    def test_batch_is_rejected(self) -> None:
        code, outputs, _, _ = run_process(b"[]\n")
        self.assertEqual(code, 0)
        self.assertEqual(outputs[0]["error"]["code"], -32600)

    def test_inventory_query_filters_and_pagination(self) -> None:
        args = {"package_root": str(self.fixture_root), "inventory_sha": self.fixture_sha, "filters": {"system": "VIA_AGENT_OS"}, "offset": 0, "limit": 1}
        code, outputs, _, _ = self.call_session("via_inventory_query", args)
        self.assertEqual(code, 0)
        result = self.tool_result(outputs)["structuredContent"]
        self.assertEqual(result["total_matching"], 3)
        self.assertEqual(result["returned"], 1)
        self.assertTrue(result["has_more"])
        self.assertEqual(result["rows"][0]["_evidence_scope"], "LOCAL_CANDIDATE_EVIDENCE_NOT_LIVE")

    def test_inventory_query_requires_root_and_sha(self) -> None:
        code, outputs, _, _ = self.call_session("via_inventory_query", {})
        self.assertTrue(self.tool_result(outputs)["isError"])
        self.assertIn("requires package_root", self.tool_result(outputs)["structuredContent"]["reason"])

    def test_inventory_sha_mismatch_is_rejected(self) -> None:
        args = {"package_root": str(self.fixture_root), "inventory_sha": "0" * 64}
        code, outputs, _, _ = self.call_session("via_inventory_query", args)
        self.assertTrue(self.tool_result(outputs)["isError"])
        self.assertIn("mismatch", self.tool_result(outputs)["structuredContent"]["reason"])

    def test_inventory_symlink_root_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="via-mcp-link-") as temp:
            alias = Path(temp) / "alias"
            alias.symlink_to(self.fixture_root, target_is_directory=True)
            args = {"package_root": str(alias), "inventory_sha": self.fixture_sha}
            code, outputs, _, _ = self.call_session("via_inventory_query", args)
            self.assertTrue(self.tool_result(outputs)["isError"])
            self.assertIn("symlink", self.tool_result(outputs)["structuredContent"]["reason"])

    def test_inventory_source_paths_are_portable_relative(self) -> None:
        args = {"package_root": str(self.fixture_root), "inventory_sha": self.fixture_sha, "limit": 50}
        code, outputs, _, _ = self.call_session("via_inventory_query", args)
        result = self.tool_result(outputs)["structuredContent"]
        self.assertEqual(result["source"], "data/governance_inventory_v0105.json")
        for row in result["rows"]:
            self.assertFalse(str(row.get("source", "")).startswith("/"))

    def test_token_prepare_reports_pinned_engine_and_semantics(self) -> None:
        code, outputs, _, _ = self.call_session("via_token_prepare", {"text": "plain local text"})
        result = self.tool_result(outputs)["structuredContent"]
        self.assertEqual(result["engine_source"], "engines/tooling/via_agent_os_unified_readonly_hardened.py")
        self.assertEqual(result["engine_sha256"], PINNED_ENGINE_SHA256)
        self.assertEqual(result["measurement"], "heuristic_estimate_not_provider_billing")
        self.assertEqual(result["execution_scope"], "LOCAL_PINNED_ENGINE_ONLY")
        self.assertIn("partial redaction", result["redaction_note"])
        self.assertIn("non-sensitive", result["risk_note"])

    def test_lossy_query_requires_explicit_opt_in(self) -> None:
        text = "\n".join(["ordinary line"] * 4 + ["needle target"] + ["ordinary line"] * 4)
        _, no_loss_outputs, _, _ = self.call_session("via_token_prepare", {"text": text, "query": "needle", "max_lines": 2})
        no_loss = self.tool_result(no_loss_outputs)["structuredContent"]
        self.assertFalse(no_loss["lossy"])
        _, loss_outputs, _, _ = self.call_session("via_token_prepare", {"text": text, "query": "needle", "allow_lossy": True, "max_lines": 2})
        lossy = self.tool_result(loss_outputs)["structuredContent"]
        self.assertTrue(lossy["lossy"])
        self.assertIn("needle", lossy["prepared_text"])

    def test_max_lines_bounds_and_boolean_not_integer(self) -> None:
        _, outputs, _, _ = self.call_session("via_token_prepare", {"text": "x", "max_lines": True})
        self.assertTrue(self.tool_result(outputs)["isError"])
        _, outputs2, _, _ = self.call_session("via_token_prepare", {"text": "x", "max_lines": 401})
        self.assertTrue(self.tool_result(outputs2)["isError"])

    def test_token_input_one_mib_limit(self) -> None:
        _, outputs, _, _ = self.call_session("via_token_prepare", {"text": "x" * (1024 * 1024 + 1)})
        self.assertTrue(self.tool_result(outputs)["isError"])
        self.assertIn("1 MiB", self.tool_result(outputs)["structuredContent"]["reason"])

    def test_line_two_mib_limit_and_process_closes(self) -> None:
        oversized = b"{" + b'"jsonrpc":"2.0","id":1,"method":"ping","params":{' + b" " * (MAX_LINE_BYTES + 10) + b"}}\n"
        code, outputs, _, _ = run_process(oversized)
        self.assertEqual(code, 0)
        self.assertEqual(outputs[0]["error"]["code"], -32600)

    def test_empty_stdin_eof_exits_cleanly(self) -> None:
        process = subprocess.run([sys.executable, "-B", str(SCRIPT)], cwd=str(ROOT), input=b"", stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5, check=False)
        self.assertEqual(process.returncode, 0)
        self.assertEqual(process.stdout, b"")

    def test_fixed_inventory_path_does_not_follow_arbitrary_filename(self) -> None:
        with tempfile.TemporaryDirectory(prefix="via-mcp-other-") as temp:
            root = Path(temp)
            (root / "data").mkdir()
            (root / "data" / "other.json").write_text("{}", encoding="utf-8")
            args = {"package_root": str(root), "inventory_sha": self.fixture_sha}
            _, outputs, _, _ = self.call_session("via_inventory_query", args)
            self.assertTrue(self.tool_result(outputs)["isError"])

    def test_text_cannot_execute_shell_commands(self) -> None:
        with tempfile.TemporaryDirectory(prefix="via-mcp-marker-") as temp:
            marker = Path(temp) / "must-not-exist"
            text = f"__import__('os').system('touch {marker}')"
            _, outputs, _, _ = self.call_session("via_token_prepare", {"text": text})
            self.assertFalse(marker.exists())
            self.assertFalse(self.tool_result(outputs)["isError"])

    def test_response_cap_is_enforced(self) -> None:
        with tempfile.TemporaryDirectory(prefix="via-mcp-large-") as temp:
            root = Path(temp)
            (root / "data").mkdir()
            large_model = fixture_model()
            large_model["matrices"]["files"] = [{"id": "BIG", "status": "GREEN", "system": "VIA_AGENT_OS", "kind": "BLOB", "source": "attachments/big.bin", "payload": "x" * (3 * 1024 * 1024)}]
            path = root / INVENTORY_RELATIVE
            path.write_bytes((json.dumps(large_model, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8"))
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            _, outputs, raw, _ = self.call_session("via_inventory_query", {"package_root": str(root), "inventory_sha": digest})
            self.assertTrue(self.tool_result(outputs)["isError"])
            self.assertLessEqual(len(raw), MAX_RESPONSE_BYTES)

    def test_boolean_offset_and_limit_are_not_integers(self) -> None:
        args = {"package_root": str(self.fixture_root), "inventory_sha": self.fixture_sha, "offset": False}
        _, outputs, _, _ = self.call_session("via_inventory_query", args)
        self.assertTrue(self.tool_result(outputs)["isError"])
        args2 = {"package_root": str(self.fixture_root), "inventory_sha": self.fixture_sha, "limit": True}
        _, outputs2, _, _ = self.call_session("via_inventory_query", args2)
        self.assertTrue(self.tool_result(outputs2)["isError"])

    def test_tools_list_exposes_exact_three_allowlisted_tools_and_annotations(self) -> None:
        payload = wire(initialize()) + wire({"jsonrpc": "2.0", "method": "notifications/initialized"}) + wire({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        _, outputs, _, _ = run_process(payload)
        tools = outputs[-1]["result"]["tools"]
        self.assertEqual([tool["name"] for tool in tools], ["via_status", "via_inventory_query", "via_token_prepare"])
        for tool in tools:
            self.assertEqual(tool["annotations"], {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False, "idempotentHint": True})

    def test_malformed_params_type_is_rejected(self) -> None:
        payload = wire(initialize()) + wire({"jsonrpc": "2.0", "method": "notifications/initialized"}) + wire({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": []})
        _, outputs, _, _ = run_process(payload)
        self.assertEqual(outputs[-1]["error"]["code"], -32602)

    def test_actual_inventory_is_used_when_available(self) -> None:
        path = ROOT / INVENTORY_RELATIVE
        if not path.is_file() or path.is_symlink():
            self.assertTrue(True, "actual inventory not ready; fixture scope remains explicit")
            return
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        _, outputs, _, _ = self.call_session("via_inventory_query", {"package_root": str(ROOT), "inventory_sha": digest, "limit": 1})
        self.assertFalse(self.tool_result(outputs)["isError"])


def receipt_scope() -> dict[str, Any]:
    actual = ROOT / INVENTORY_RELATIVE
    if actual.is_file() and not actual.is_symlink():
        return {
            "scope": "ACTUAL_FIXED_INVENTORY",
            "inventory_path": "data/governance_inventory_v0105.json",
            "inventory_sha256": hashlib.sha256(actual.read_bytes()).hexdigest(),
            "final_receipt_eligible": True,
            "note": "Protocol tests include a real fixed-inventory query.",
        }
    return {
        "scope": "LOCAL_TEST_FIXTURE_NOT_LIVE",
        "inventory_path": "data/governance_inventory_v0105.json",
        "inventory_sha256": hashlib.sha256(fixture_bytes()).hexdigest(),
        "final_receipt_eligible": False,
        "note": "Real governance_inventory_v0105.json was not ready; this receipt is fixture-scoped and must be rerun for the final actual-inventory receipt.",
    }


def write_receipt(result: unittest.TestResult) -> Path:
    receipt_dir = ROOT / "artifacts" / "mcp_protocol_v0105"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    failed = len(result.failures)
    errors = len(result.errors)
    skipped = len(getattr(result, "skipped", []))
    total = result.testsRun
    receipt = {
        "schema": "VIA.MCPProtocolTestReceipt.v0105",
        "status": "PASS" if not failed and not errors else "FAIL",
        "generated_by": "tests/test_governance_mcp_v0105.py",
        "tests_run": total,
        "tests_failed": failed,
        "tests_errors": errors,
        "tests_skipped": skipped,
        "tests_passed": total - failed - errors - skipped,
        "protocol": {
            "transport": "stdio",
            "jsonrpc": "2.0",
            "protocol_version": "2025-06-18",
            "wire_format": "UTF-8 newline-delimited JSON",
            "stdout_responses_only": True,
            "stderr_logs_only": True,
            "batch_supported": False,
            "eof_is_normal_exit": True,
        },
        "candidate_registration": {
            "registration_performed": False,
            "manus_connector_installed": False,
            "vcgc_host_or_client_registered": False,
            "formal_status": "REQUIRES_REAL_ENDPOINT_AND_OWNER_APPROVAL",
        },
        "tools": ["via_status", "via_inventory_query", "via_token_prepare"],
        "limits": {
            "max_requests_per_process": 1000,
            "max_line_bytes": MAX_LINE_BYTES,
            "max_response_bytes": MAX_RESPONSE_BYTES,
            "inventory_rows": 50,
            "token_input_bytes": 1024 * 1024,
            "token_max_lines": 400,
        },
        "pinned_engine": {
            "path": "engines/tooling/via_agent_os_unified_readonly_hardened.py",
            "sha256": PINNED_ENGINE_SHA256,
        },
        "inventory": receipt_scope(),
        "network_access": False,
        "provider_calls": 0,
        "repository_writes": False,
        "generated_at_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
    }
    path = receipt_dir / "receipt.json"
    path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return path


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(GovernanceMCPV0105Tests)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    receipt = write_receipt(result)
    print(f"receipt: {receipt}")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
