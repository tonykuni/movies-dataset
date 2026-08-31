from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("vofie", ROOT / "Veritas_OmniFormat_Intelligence_Engine.py")
assert SPEC and SPEC.loader
vofie = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = vofie
SPEC.loader.exec_module(vofie)


class VOFIEContractTests(unittest.TestCase):
    def test_identity(self):
        self.assertEqual(vofie.ENGINE_ID, "ENG-VOFIE-001")
        self.assertEqual(vofie.SUBSYSTEM_ID, "VIA-SUBSYS-VOFIE-001")
        self.assertEqual(vofie.ENGINE_VERSION, "1.4.0")

    def test_output_registry_is_complete(self):
        self.assertEqual(set(vofie.ALL_OUTPUT_FORMATS), set(vofie.OUTPUT_REGISTRY))

    def test_every_input_has_st(self):
        self.assertTrue(all(item["st"] in vofie.ST_LEVELS for item in vofie.FORMAT_REGISTRY.values()))

    def test_every_output_has_st(self):
        self.assertTrue(all(item["st"] in vofie.ST_LEVELS for item in vofie.OUTPUT_REGISTRY.values()))

    def test_st_profile_ids_unique(self):
        rows = vofie.profile_rows()
        self.assertEqual(len(rows), len({item["st_id"] for item in rows}))

    def test_manifest_has_no_mutating_capability(self):
        manifest = vofie.registration_manifest()
        self.assertTrue(all(not item["mutates_source"] for item in manifest["capabilities"]))

    def test_detect_kinds(self):
        expected = {"a.md": "markdown", "a.html": "html", "a.docx": "document", "a.py": "code", "a.csv": "csv", "a.json": "structured"}
        for name, kind in expected.items():
            with self.subTest(name=name):
                self.assertEqual(vofie.detect_kind(Path(name)), kind)

    def test_stable_id_deterministic(self):
        self.assertEqual(vofie.stable_id("X", "a", 1), vofie.stable_id("X", "a", 1))

    def test_stable_id_changes(self):
        self.assertNotEqual(vofie.stable_id("X", "a"), vofie.stable_id("X", "b"))

    def test_canonical_newlines(self):
        self.assertEqual(vofie.canonical_text("a\r\n b \r"), "a\n b\n")

    def test_utf8_bom_decode(self):
        text, encoding = vofie.decode_bytes("中文".encode("utf-8-sig"))
        self.assertEqual(text, "中文")
        self.assertEqual(encoding, "utf-8-sig")

    def test_fence_language_from_label(self):
        text, warnings = vofie.normalize_markdown_fences("**python**\n\n```\ndef demo(): pass\n```")
        self.assertIn("```python", text)
        self.assertTrue(warnings)

    def test_unclosed_fence_is_closed_in_candidate(self):
        text, warnings = vofie.normalize_markdown_fences("```js\nconst a = 1;")
        self.assertTrue(text.rstrip().endswith("```"))
        self.assertTrue(any("缺少" in item for item in warnings))

    def test_boilerplate_quarantine(self):
        source = vofie.SourceRecord("SRC-X", "x", "x.md", ".md", "markdown", "utf-8", 1, "a", "b", "", True, {})
        clean, items = vofie.quarantine_boilerplate(source, "keep\nsvg\n請謹慎使用程式碼。\n", True)
        self.assertIn("keep", clean)
        self.assertEqual(len(items), 2)

    def test_html_heading_to_markdown(self):
        parser = vofie.SemanticHTMLParser()
        parser.feed("<h1>Title</h1><p>Body</p>")
        self.assertIn("# Title", parser.markdown())

    def test_html_list_to_markdown(self):
        parser = vofie.SemanticHTMLParser()
        parser.feed("<ul><li>One</li><li>Two</li></ul>")
        result = parser.markdown()
        self.assertIn("- One", result)
        self.assertIn("- Two", result)

    def test_html_script_is_captured_not_content(self):
        parser = vofie.SemanticHTMLParser()
        parser.feed("<p>Safe</p><script>danger()</script>")
        self.assertIn("Safe", parser.markdown())
        self.assertNotIn("danger", parser.markdown())
        self.assertIn("danger()", "".join(parser.scripts))

    def test_python_ast_units(self):
        units = vofie._python_units("class A:\n    pass\n\ndef demo(x):\n    return x\n", 1)
        self.assertEqual({unit.symbol for unit in units}, {"A", "demo"})
        self.assertTrue(all(unit.syntax_status == "PASS" for unit in units))

    def test_python_syntax_error_is_structured(self):
        units = vofie._python_units("def broken(:\n pass", 1)
        self.assertEqual(units[0].symbol, "<module>")
        self.assertTrue(units[0].syntax_status.startswith("SYNTAX_ERROR"))

    def test_javascript_symbol_extraction(self):
        content = "```javascript\nfunction choose(id) { return id; }\n```"
        units = vofie.extract_code_units(content, 1)
        self.assertTrue(any(unit.symbol == "choose" for unit in units))

    def test_chunk_topic_bound(self):
        chunks = vofie.chunk_topic("a" * 25, 10)
        self.assertTrue(all(len(item) <= 10 for item in chunks))

    def test_classification(self):
        category, tags = vofie.classify_topic("HTML UI", "responsive CSS component dashboard")
        self.assertEqual(category, "ui_specification")
        self.assertTrue(tags)

    def test_duplicates_are_marked_not_removed(self):
        topics = [
            vofie.TopicBlock("TOP-A", "SRC", "A", 1, 0, 1, 2, "general", [], "same", "hash"),
            vofie.TopicBlock("TOP-B", "SRC", "B", 1, 1, 3, 4, "general", [], "same", "hash"),
        ]
        self.assertEqual(vofie.mark_duplicates(topics), 1)
        self.assertEqual(len(topics), 2)
        self.assertEqual(topics[1].duplicate_of, "TOP-A")

    def test_ui_security_finding(self):
        source = vofie.SourceRecord("SRC-X", "x.html", "x.html", ".html", "html", "utf-8", 1, "a", "b", "", True, {"html_source": "<script>eval('x')</script>"})
        spec = vofie.build_ui_spec([source])
        self.assertTrue(any(item["rule"] == "eval_usage" for item in spec["security_findings"]))
        self.assertFalse(spec["source_scripts_executed"])

    def test_registry_overlay_add_only(self):
        result = vofie.load_registry_overlay(ROOT)
        self.assertEqual(result["status"], "PASS")
        self.assertIn("TOOL-VOFIE-STDLIB-001", result["enabled_tools"])

    def test_failure_catalog_has_eight_stages_and_160_failures(self):
        catalog = vofie.load_failure_catalog(ROOT)
        self.assertEqual(catalog["stage_count"], 8)
        self.assertEqual(catalog["failure_count"], 160)
        self.assertTrue(all(len(stage["failures"]) == 20 for stage in catalog["stages"]))

    def test_every_failure_has_multiple_implemented_solutions(self):
        catalog = vofie.load_failure_catalog(ROOT)
        for stage in catalog["stages"]:
            for failure in stage["failures"]:
                self.assertGreaterEqual(len(failure["handlers"]), 2)
                self.assertTrue(all(handler in vofie.RECOVERY_HANDLERS for handler in failure["handlers"]))

    def test_hydra_catalog_has_exact_top_twenty(self):
        catalog = vofie.load_hydra_risk_catalog(ROOT)
        self.assertEqual(len(catalog["risks"]), 20)
        self.assertEqual([row["rank"] for row in catalog["risks"]], list(range(1, 21)))

    def test_hydra_schema_matches_catalog_contract(self):
        catalog = vofie.load_hydra_risk_catalog(ROOT)
        schema = json.loads((ROOT / "schemas" / "HydraRiskCatalog.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["contract"]["const"], catalog["contract"])
        self.assertEqual(schema["properties"]["version"]["const"], catalog["version"])

    def test_hydra_catalog_has_multiple_solutions_and_breakers(self):
        catalog = vofie.load_hydra_risk_catalog(ROOT)
        for risk in catalog["risks"]:
            self.assertGreaterEqual(len(risk["solutions"]), 3)
            self.assertGreaterEqual(len(risk["breakers"]), 2)
            self.assertEqual(risk["default_action"], "HOLD")

    def test_hydra_contract_is_three_round_read_only(self):
        report = vofie.hydra_risk_audit(ROOT)
        self.assertEqual(report["gate"], "PASS")
        self.assertEqual(len(report["round_plan"]), 3)
        self.assertFalse(report["source_mutated"])
        self.assertFalse(report["real_write_performed"])
        self.assertTrue(all(row["post_scan_complete"] for row in report["round_plan"]))

    def test_hash_state_machine_is_deterministic(self):
        cases = [
            (None, "MISSING", "APPLY"),
            ("proposed", "PROPOSED", "SKIP"),
            ("original", "ORIGINAL", "BACKUP_APPLY"),
            ("unknown", "OTHER", "FAIL_CLOSED"),
        ]
        for current, state, action in cases:
            with self.subTest(current=current):
                result = vofie.hash_state_decision(current, "original", "proposed")
                self.assertEqual((result["state"], result["action"]), (state, action))
                self.assertFalse(result["canonical_mutation_allowed"])

    def test_runtime_copy_requires_explicit_approval(self):
        report = vofie.create_runtime_copy((ROOT / "README.md",), ROOT / "qa-denied", "")
        self.assertEqual(report["gate"], "HOLD")
        self.assertFalse(report["runtime_copy_created"])

    def test_runtime_copy_and_rollback_preserve_canonical(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            source = root / "canonical.txt"
            source.write_text("canonical\n", encoding="utf-8")
            before = vofie.file_snapshot(source)
            report = vofie.create_runtime_copy((source,), root / "runtime", vofie.RUNTIME_COPY_APPROVAL_TOKEN)
            self.assertEqual(report["gate"], "PASS")
            self.assertEqual(report["rollback_dry_run"]["gate"], "PASS")
            self.assertFalse(report["promotion_performed"])
            self.assertEqual(before, vofie.file_snapshot(source))

    def test_hydra_marker_holds_without_mutation(self):
        with tempfile.TemporaryDirectory() as name:
            target = Path(name) / "risk.py"
            target.write_text("# HYDRA:RISK=HYDRA-F05\n", encoding="utf-8")
            before = vofie.file_snapshot(target)
            report = vofie.hydra_risk_audit(ROOT, (target,))
            self.assertEqual(report["gate"], "HOLD")
            self.assertFalse(report["activation_allowed"])
            self.assertEqual(report["findings"][0]["risk_id"], "HYDRA-F05")
            self.assertEqual(before, vofie.file_snapshot(target))

    def test_recovery_handlers_are_safe_in_dry_run(self):
        report = vofie.exercise_recovery_handlers(ROOT)
        self.assertEqual(report["gate"], "PASS")
        self.assertTrue(all(not row["source_mutated"] for row in report["handlers"]))

    def test_simple_contract_is_exactly_five(self):
        self.assertEqual(len(vofie.SIMPLE_PRIMARY_OUTPUTS), 5)
        self.assertEqual(set(vofie.SIMPLE_PRIMARY_OUTPUTS), set(vofie.SIMPLE_PRIMARY_FILENAMES))

    def test_gui_input_normalizer_deduplicates_and_limits(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            paths = []
            for index in range(6):
                path = root / f"{index}.txt"
                path.write_text(str(index), encoding="utf-8")
                paths.append(path)
            self.assertEqual(len(vofie.normalize_gui_inputs([paths[0], paths[0], paths[1]])), 2)
            with self.assertRaises(vofie.VOFIEError):
                vofie.normalize_gui_inputs(paths)

    def test_polyglot_catalog_has_exact_top_twenty_each(self):
        catalog = vofie.load_polyglot_tool_catalog(ROOT)
        self.assertEqual(len(catalog["javascript_top20"]), 20)
        self.assertEqual(len(catalog["powershell_top20"]), 20)

    def test_polyglot_catalog_schema_matches_v12_shape(self):
        schema = json.loads((ROOT / "schemas" / "PolyglotToolCatalog.schema.json").read_text(encoding="utf-8"))
        catalog = vofie.load_polyglot_tool_catalog(ROOT)
        self.assertEqual(schema["properties"]["contract"]["const"], catalog["contract"])
        self.assertEqual(schema["properties"]["version"]["const"], catalog["version"])
        self.assertEqual(len(catalog["capability_matrix_functions"]), 10)

    def test_polyglot_catalog_ids_are_unique(self):
        catalog = vofie.load_polyglot_tool_catalog(ROOT)
        rows = [*catalog["javascript_top20"], *catalog["powershell_top20"]]
        self.assertEqual(len(rows), len({row["tool_id"] for row in rows}))

    def test_polyglot_catalog_is_free_cpu_and_has_fallbacks(self):
        catalog = vofie.load_polyglot_tool_catalog(ROOT)
        rows = [*catalog["javascript_top20"], *catalog["powershell_top20"]]
        self.assertTrue(all(row["license"] and row["cpu_supported"] and row["fallback"] for row in rows))

    def test_polyglot_routes_do_not_pollute_base(self):
        catalog = vofie.load_polyglot_tool_catalog(ROOT)
        self.assertTrue(all(row["route"] == "via-ui" for row in catalog["javascript_top20"]))
        self.assertTrue(all(row["route"] == "via-ps" for row in catalog["powershell_top20"]))
        self.assertEqual(catalog["policy"]["base_environment"], "NO_POLLUTION")

    def test_polyglot_audit_has_exact_thirty_matrix_rows(self):
        report = vofie.tool_audit(ROOT)
        self.assertEqual(report["gate"], "PASS")
        self.assertEqual(len(report["capability_matrix"]), 30)
        self.assertEqual(report["summary"]["uncovered_functions"], 0)

    def test_missing_polyglot_tools_are_nonblocking(self):
        report = vofie.tool_audit(ROOT)
        self.assertEqual(report["gate"], "PASS")
        self.assertTrue(all(row["status"] in {"AVAILABLE", "BUILTIN", "NOT_INSTALLED"} for row in report["tools"]))

    def test_powershell_structural_fallback_is_read_only(self):
        report = vofie.powershell_structure_check(ROOT / "Invoke-Veritas-VOFIE.ps1")
        self.assertEqual(report["gate"], "PASS")
        self.assertTrue(report["top_parameter_block"])
        self.assertFalse(report["source_mutated"])

    def test_javascript_bridge_self_test(self):
        node = os.environ.get("CODEX_PRIMARY_RUNTIME_NODE") or shutil.which("node")
        if not node:
            self.skipTest("Node runtime unavailable; Python fallback remains covered")
        result = subprocess.run(
            [node, str(ROOT / "adapters" / "vofie_polyglot_tool_probe.mjs"), "--self-test"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["gate"], "PASS")

    def test_javascript_safe_tool_dispatch_preserves_source(self):
        target = ROOT / "adapters" / "vofie_polyglot_tool_probe.mjs"
        before = vofie.file_snapshot(target)
        report = vofie.tool_plan(ROOT, target, ("syntax_parse",), execute_safe=True)
        self.assertEqual(report["gate"], "PASS")
        self.assertFalse(report["source_mutated"])
        self.assertEqual(vofie.file_snapshot(target), before)

    def test_powershell_safe_tool_dispatch_preserves_source(self):
        target = ROOT / "Invoke-Veritas-VOFIE.ps1"
        before = vofie.file_snapshot(target)
        report = vofie.tool_plan(ROOT, target, ("syntax_parse",), execute_safe=True)
        self.assertEqual(report["gate"], "PASS")
        self.assertFalse(report["source_mutated"])
        self.assertEqual(vofie.file_snapshot(target), before)

    def test_tool_dispatch_respects_requested_functions(self):
        target = ROOT / "adapters" / "vofie_polyglot_tool_probe.mjs"
        report = vofie.tool_plan(ROOT, target, ("static_analysis", "dependency_graph"))
        self.assertEqual(report["functions"], ["static_analysis", "dependency_graph"])
        self.assertEqual(len(report["plan"]), 2)


class VOFIEPipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "sample.md"
        self.source.write_text("# Title\n\nBody\n\n## Code\n\n```python\ndef demo(x):\n    return x\n```\n\nsvg\n", encoding="utf-8")
        self.before = vofie.file_snapshot(self.source)

    def tearDown(self):
        self.temp.cleanup()

    def engine(self, formats=("md", "json", "csv", "html", "css", "js")):
        return vofie.VeritasOmniFormatEngine(ROOT, vofie.EngineOptions(use_vsis=False, output_formats=formats))

    def test_load_source_preserves_hash(self):
        record = vofie.load_source(self.source, vofie.EngineOptions(use_vsis=False))
        self.assertEqual(record.source_hash, self.before[1])
        self.assertEqual(vofie.file_snapshot(self.source), self.before)

    def test_build_ir(self):
        ir, snapshots = self.engine().build_ir([self.source])
        self.assertGreaterEqual(len(ir.topics), 2)
        self.assertEqual(ir.quality["source_preservation"], "PASS")
        self.assertEqual(snapshots[ir.source_records[0].source_id], self.before)

    def test_original_text_embedded(self):
        ir, _ = self.engine().build_ir([self.source])
        self.assertIn("def demo", ir.source_records[0].extracted_text)

    def test_convert_core_outputs(self):
        ir = self.engine().convert([self.source], self.root / "output", "Test")
        for extension in ("md", "json", "csv", "html", "css", "js"):
            self.assertTrue(Path(ir.output_files[extension]).is_file(), extension)
        self.assertEqual(vofie.file_snapshot(self.source), self.before)

    def test_nonempty_output_directory_is_not_overwritten(self):
        output = self.root / "output"
        output.mkdir()
        sentinel = output / "keep.txt"
        sentinel.write_text("keep", encoding="utf-8")
        ir = self.engine(("json",)).convert([self.source], output, "Test")
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")
        self.assertNotEqual(Path(ir.output_files["json"]).parent, output)

    def test_markdown_contains_st_matrix(self):
        ir = self.engine(("md", "json")).convert([self.source], self.root / "output", "Test")
        content = Path(ir.output_files["md"]).read_text(encoding="utf-8")
        self.assertIn("ST 能力定位", content)
        self.assertIn("ST-FMT-001", content)

    def test_csv_has_bom(self):
        ir = self.engine(("csv", "json")).convert([self.source], self.root / "output", "Test")
        self.assertTrue(Path(ir.output_files["csv"]).read_bytes().startswith(b"\xef\xbb\xbf"))

    def test_web_template_is_local(self):
        ir = self.engine(("html", "css", "js", "json")).convert([self.source], self.root / "output", "Test")
        content = Path(ir.output_files["html"]).read_text(encoding="utf-8").casefold()
        self.assertNotIn("https://", content)
        self.assertNotIn("cdn", content)
        self.assertIn("veritas intelligence analytics", content)

    def test_web_template_javascript_syntax(self):
        ir = self.engine(("html", "css", "js", "json")).convert([self.source], self.root / "output", "Test")
        js_path = Path(ir.output_files["js"])
        content = js_path.read_text(encoding="utf-8")
        self.assertIn(r'/[",\n]/', content)
        self.assertIn(r".join('\n')", content)
        node = os.environ.get("CODEX_PRIMARY_RUNTIME_NODE") or shutil.which("node")
        if node:
            result = subprocess.run([node, "--check", str(js_path)], capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_audit_chain(self):
        ir = self.engine(("json",)).convert([self.source], self.root / "output", "Test")
        audit = Path(ir.output_files["json"]).parent / "Veritas_VOFIE_Audit_Chain.jsonl"
        rows = [json.loads(line) for line in audit.read_text(encoding="utf-8").splitlines()]
        self.assertGreaterEqual(len(rows), 2)
        self.assertEqual(rows[1]["previous_hash"], rows[0]["chain_hash"])

    def test_output_manifest_hashes_exist(self):
        ir = self.engine(("md", "json")).convert([self.source], self.root / "output", "Test")
        manifest = json.loads(Path(ir.output_files["manifest"]).read_text(encoding="utf-8"))
        self.assertIn("md", manifest["outputs"])
        self.assertEqual(len(manifest["outputs"]["md"]["hash"]), 64)

    def test_engine_self_test(self):
        report = vofie.self_test(ROOT)
        self.assertEqual(report["gate"], "PASS")
        self.assertEqual(report["failed"], 0)

    def test_simple_engine_role_writes_exact_five_primary_files(self):
        options = vofie.EngineOptions(use_vsis=False, run_role="ENGINE", operations=vofie.DEFAULT_OPERATIONS)
        ir = vofie.VeritasOmniFormatEngine(ROOT, options).convert_simple([self.source], self.root / "simple-engine", "Simple")
        output = Path(ir.quality["output_dir"])
        self.assertEqual(vofie.validate_simple_outputs(output)["gate"], "PASS")
        self.assertFalse((output / vofie.SYSTEM_SIDECAR_DIRECTORY).exists())
        self.assertEqual(set(ir.output_files), set(vofie.SIMPLE_PRIMARY_OUTPUTS))

    def test_simple_system_role_isolates_sidecars(self):
        options = vofie.EngineOptions(use_vsis=False, run_role="SYSTEM", operations=vofie.DEFAULT_OPERATIONS)
        ir = vofie.VeritasOmniFormatEngine(ROOT, options).convert_simple([self.source], self.root / "simple-system", "System")
        output = Path(ir.quality["output_dir"])
        self.assertEqual(vofie.validate_simple_outputs(output)["actual_count"], 5)
        self.assertTrue((output / vofie.SYSTEM_SIDECAR_DIRECTORY / "SystemManifest.json").is_file())
        self.assertTrue((output / vofie.SYSTEM_SIDECAR_DIRECTORY / "PolyglotToolAudit.json").is_file())

    def test_simple_component_json_contains_full_ir_and_failure_framework(self):
        options = vofie.EngineOptions(use_vsis=False, run_role="ENGINE")
        ir = vofie.VeritasOmniFormatEngine(ROOT, options).convert_simple([self.source], self.root / "simple-json", "JSON")
        payload = json.loads(Path(ir.output_files["component_json"]).read_text(encoding="utf-8"))
        self.assertEqual(payload["contract"], vofie.COMPONENT_SPEC_CONTRACT)
        self.assertEqual(payload["failure_framework"]["total_failures"], 160)
        self.assertEqual(payload["polyglot_tool_support"]["summary"]["total"], 40)
        self.assertEqual(payload["polyglot_tool_support"]["summary"]["matrix_rows"], 30)
        self.assertIn("universal_content_ir", payload)

    def test_simple_more_than_five_inputs_fails_preflight(self):
        paths = []
        for index in range(6):
            path = self.root / f"extra-{index}.txt"
            path.write_text(f"# {index}\n", encoding="utf-8")
            paths.append(path)
        options = vofie.EngineOptions(use_vsis=False, run_role="ENGINE")
        with self.assertRaises(vofie.VOFIEError):
            vofie.VeritasOmniFormatEngine(ROOT, options).convert_simple(paths, self.root / "too-many")

    def test_user_test_flow(self):
        report = vofie.user_test(ROOT)
        self.assertEqual(report["gate"], "PASS")
        self.assertEqual(report["failed"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
