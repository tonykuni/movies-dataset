from __future__ import annotations

# ============================================================================
# 01. PARAMETERS
# ============================================================================

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = PACKAGE_ROOT / "src" / "via_ai_workflow.py"
BRIDGE_PATH = PACKAGE_ROOT.parents[1] / "registry" / "CGC_MDL142_AIWorkflowBridge_v0100.py"
SPEC = importlib.util.spec_from_file_location("via_ai_workflow", SOURCE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to import {SOURCE_PATH}")
WORKFLOW = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = WORKFLOW
SPEC.loader.exec_module(WORKFLOW)


# ============================================================================
# 02. TESTS
# ============================================================================


class WorkflowContractTests(unittest.TestCase):
    def test_mother_system_bridge_selftest_passes(self) -> None:
        bridge_spec = importlib.util.spec_from_file_location("via_ai_bridge", BRIDGE_PATH)
        self.assertIsNotNone(bridge_spec)
        self.assertIsNotNone(bridge_spec.loader if bridge_spec else None)
        bridge = importlib.util.module_from_spec(bridge_spec)
        assert bridge_spec is not None and bridge_spec.loader is not None
        bridge_spec.loader.exec_module(bridge)
        result = bridge.selftest()
        self.assertEqual("PASS", result["status"], result)
        self.assertEqual("CGC_MDL142", result["module"]["module_id"])

    def test_package_validation_passes(self) -> None:
        result = WORKFLOW.validate_all()
        self.assertEqual("PASS", result["status"], result["errors"])
        self.assertEqual(6, result["module_count"])

    def test_instruction_ast_has_all_layers(self) -> None:
        document = WORKFLOW.compile_instruction_ast(WORKFLOW.load_manifests())
        module_nodes = [node for node in document["nodes"] if node["node_type"] == "module"]
        self.assertEqual(list(WORKFLOW.ALLOWED_LAYERS), [node["layer"] for node in module_nodes])
        self.assertTrue(any(edge["type"] == "depends_on" for edge in document["edges"]))

    def test_schema_rejects_unknown_property(self) -> None:
        manifest = WORKFLOW.load_manifests()[0].copy()
        manifest["unexpected"] = True
        errors = WORKFLOW.validate_json_document(manifest, WORKFLOW.INSTRUCTION_SCHEMA_PATH)
        self.assertTrue(any("unexpected property" in error for error in errors))

    def test_python_ast_index_extracts_symbols(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "sample.py"
            source.write_text("import json\n\ndef alpha(value):\n    return json.dumps(value)\n", encoding="utf-8")
            result = WORKFLOW.build_python_ast_index(root)
            self.assertEqual(1, result["file_count"])
            self.assertEqual(0, result["error_count"])
            self.assertEqual("alpha", result["files"][0]["symbols"][0]["name"])
            self.assertIn("json.dumps", result["files"][0]["calls"])

    def test_context_pack_uses_ast_symbol_slice(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "target.py"
            source.write_text(
                "def keep_me():\n    return 1\n\ndef exclude_me():\n    return 2\n",
                encoding="utf-8",
            )
            task = {
                "task_id": "VIA-TASK-TEST",
                "goal": "Load only one symbol.",
                "module_ids": ["VIA-AI-000003"],
                "repository_root": str(root),
                "base_sha": "1234567",
                "path_allowlist": ["target.py"],
                "symbol_allowlist": ["target.keep_me"],
                "constraints": [],
                "acceptance": ["Only the requested symbol is included."],
                "token_budget": {
                    "max_input_tokens": 1000,
                    "include_full_files": False,
                    "max_chars_per_file": 1000,
                },
            }
            task_path = root / "task.json"
            task_path.write_text(json.dumps(task), encoding="utf-8")
            result = WORKFLOW.compile_context_pack(task_path)
            content = result["files"][0]["content"]
            self.assertIn("keep_me", content)
            self.assertNotIn("exclude_me", content)
            self.assertEqual("ast_symbol_slice", result["files"][0]["content_mode"])

    def test_handoff_ready_requires_all_gates(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            packet_path = Path(temporary_directory) / "handoff.json"
            packet = json.loads((PACKAGE_ROOT / "templates" / "handoff_packet.template.json").read_text(encoding="utf-8"))
            packet["status"] = "ready_for_review"
            packet_path.write_text(json.dumps(packet), encoding="utf-8")
            result = WORKFLOW.validate_handoff(packet_path)
            self.assertEqual("FAIL", result["status"])
            self.assertTrue(any("USER_TEST" in error for error in result["errors"]))

    def test_context_pack_rejects_database_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "market.duckdb").write_bytes(b"not-a-real-database")
            task = {
                "task_id": "VIA-TASK-DATA-GATE",
                "goal": "Confirm data-plane files are rejected.",
                "module_ids": ["VIA-AI-000002"],
                "repository_root": str(root),
                "base_sha": "1234567",
                "path_allowlist": ["market.duckdb"],
                "symbol_allowlist": [],
                "constraints": [],
                "acceptance": ["Database content is not loaded."],
                "token_budget": {"max_input_tokens": 1000, "include_full_files": False},
            }
            task_path = root / "task.json"
            task_path.write_text(json.dumps(task), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "data-plane artifact"):
                WORKFLOW.compile_context_pack(task_path)

    def test_allocator_and_lease_are_monotonic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            registry_dir = root / "registry"
            modules_dir = root / "modules"
            registry_dir.mkdir()
            modules_dir.mkdir()
            registry_path = registry_dir / "registry.json"
            events_path = registry_dir / "events.jsonl"
            lock_path = registry_dir / ".lock"
            shutil.copy2(WORKFLOW.REGISTRY_PATH, registry_path)
            shutil.copy2(WORKFLOW.EVENTS_PATH, events_path)
            with mock.patch.multiple(
                WORKFLOW,
                REGISTRY_PATH=registry_path,
                EVENTS_PATH=events_path,
                LOCK_PATH=lock_path,
                MODULES_DIR=modules_dir,
            ):
                lease = WORKFLOW.lease_id_range("Agent-A", 2, "agent/a", "1234567")
                first = WORKFLOW.allocate_module("CORE", "leased-one", "Leased one", "Agent-A", lease["lease_id"])
                second = WORKFLOW.allocate_module("QA", "leased-two", "Leased two", "Agent-A", lease["lease_id"])
                direct = WORKFLOW.allocate_module("OPS", "direct-three", "Direct three", "Agent-B")
            self.assertEqual("VIA-AI-000007", first["module_id"])
            self.assertEqual("VIA-AI-000008", second["module_id"])
            self.assertEqual("VIA-AI-000009", direct["module_id"])
            updated = json.loads(registry_path.read_text(encoding="utf-8"))
            self.assertEqual(10, updated["next_sequence"])
            self.assertEqual("consumed", updated["leases"][0]["status"])

    def test_database_artifacts_are_denied_from_github(self) -> None:
        bridge = WORKFLOW.read_json(WORKFLOW.BRIDGE_PATH)
        self.assertFalse(bridge["data_plane"]["upload_to_github"])
        self.assertIn("duckdb_database", bridge["github_denylist"])
        self.assertIn("parquet_dataset", bridge["github_denylist"])


if __name__ == "__main__":
    unittest.main()
