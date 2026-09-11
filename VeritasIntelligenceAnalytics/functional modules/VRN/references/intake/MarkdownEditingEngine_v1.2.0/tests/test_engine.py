from __future__ import annotations

import importlib.util
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from engine import semantic_reconstruction as RECON


ENGINE_ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = ENGINE_ROOT / "engine" / "markdown_engine.py"
SPEC = importlib.util.spec_from_file_location("markdown_engine", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class MarkdownEditingEngineTests(unittest.TestCase):
    def test_basic_normalize_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "sample.md"
            target.write_bytes(b"\xef\xbb\xbf# Title\r\n\r\nText\r\n")
            MODULE.def_basic_normalize(target, True)
            first = target.read_bytes()
            MODULE.def_basic_normalize(target, True)
            self.assertEqual(first, target.read_bytes())
            self.assertFalse(first.startswith(b"\xef\xbb\xbf"))
            self.assertNotIn(b"\r", first)

    def test_basic_normalize_repairs_invalid_utf8(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "invalid.md"
            target.write_bytes(b"# Title\n\nbad:\xff\n")
            MODULE.def_basic_normalize(target, True)
            repaired = target.read_text(encoding="utf-8")
            self.assertIn("\ufffd", repaired)
            self.assertTrue(repaired.endswith("\n"))

    def test_config_schema_rejects_invalid_worker_count(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = MODULE.def_load_json(ENGINE_ROOT / "config" / "engine.json")
            config["pipeline"]["max_workers"] = 0
            target = Path(directory) / "engine.json"
            target.write_text(json.dumps(config), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "max_workers"):
                MODULE.def_load_config(target)

    def test_python_signature_detects_core_structure(self) -> None:
        signature = MODULE.def_python_signature(ENGINE_ROOT / "tests" / "fixtures" / "broken.md")
        self.assertGreaterEqual(len(signature["headings"]), 2)
        self.assertEqual(signature["links"][0]["url"], "missing.md")
        self.assertEqual(signature["codeBlocks"][0]["lang"], "python")

    def test_semantic_guard_detects_link_change(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            before_path = Path(directory) / "before.md"
            after_path = Path(directory) / "after.md"
            before_path.write_text("# A\n\n[x](a.md)\n", encoding="utf-8")
            after_path.write_text("# A\n\n[x](b.md)\n", encoding="utf-8")
            before = MODULE.def_python_signature(before_path)
            after = MODULE.def_python_signature(after_path)
            equal, differences = MODULE.def_signatures_equal(before, after)
            self.assertFalse(equal)
            self.assertIn("links", differences)

    def test_discovery_excludes_generated_directories(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "a.md").write_text("# A\n", encoding="utf-8")
            (root / "node_modules").mkdir()
            (root / "node_modules" / "b.md").write_text("# B\n", encoding="utf-8")
            files = MODULE.def_discover_markdown_files(root, True)
            self.assertEqual([path.name for path in files], ["a.md"])

    def test_atomic_replace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            destination = root / "destination.md"
            source.write_text("new\n", encoding="utf-8")
            destination.write_text("old\n", encoding="utf-8")
            MODULE.def_atomic_replace(source, destination)
            self.assertEqual(destination.read_text(encoding="utf-8"), "new\n")

    def test_markdown_it_plugin_stack_parses_gfm_and_frontmatter(self) -> None:
        result = MODULE.def_run_markdown_it_validator(
            ENGINE_ROOT / "tests" / "fixtures" / "frontmatter_gfm.md"
        )
        self.assertEqual(result.status, "ok", result.stderr)
        payload = json.loads(result.stdout)
        self.assertGreater(payload["tokens"], 0)

    def test_report_bundle_writes_json_html_and_utf8_csv(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / "nested" / "run.json"
            report = {
                "run_id": "unit",
                "action": "check",
                "summary": {"files": 1, "failed": 0},
                "doctor": {"tools": []},
                "files": [
                    {
                        "path": "sample.md",
                        "status": "ok",
                        "changed": False,
                        "semantic_guard": "passed",
                        "warnings": [],
                        "errors": [],
                        "tool_results": [],
                    }
                ],
            }
            MODULE.def_write_report_bundle(
                report,
                report_path,
                {"reporting": {"html": True, "csv": True}},
            )
            self.assertTrue(report_path.is_file())
            self.assertTrue(report_path.with_suffix(".html").is_file())
            self.assertTrue(report_path.with_suffix(".csv").read_bytes().startswith(b"\xef\xbb\xbf"))

    def test_backup_hash_chain_is_verifiable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            chain_path = MODULE.def_write_backup_hash_chain(
                [
                    {
                        "path": "a.md",
                        "backup_path": "backup/a.md",
                        "before_sha256": "a" * 64,
                        "after_sha256": "b" * 64,
                    },
                    {
                        "path": "b.md",
                        "backup_path": "backup/b.md",
                        "before_sha256": "c" * 64,
                        "after_sha256": "d" * 64,
                    },
                ],
                Path(directory),
                "unit",
            )
            self.assertIsNotNone(chain_path)
            previous_hash = "0" * 64
            for line in chain_path.read_text(encoding="utf-8").splitlines():
                entry = json.loads(line)
                entry_hash = entry.pop("entry_hash")
                canonical = json.dumps(entry, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                expected = hashlib.sha256((previous_hash + canonical).encode("utf-8")).hexdigest()
                self.assertEqual(entry_hash, expected)
                self.assertEqual(entry["previous_hash"], previous_hash)
                previous_hash = entry_hash

    def test_failure_injection_quarantines_and_preserves_original(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "input" / "nested" / "source.md"
            source.parent.mkdir(parents=True)
            original = "# Title\n\n[x](a.md)\n"
            source.write_text(original, encoding="utf-8")

            def inject_link_change(staged: Path, *_args, **_kwargs):
                staged.write_text("# Title\n\n[x](b.md)\n", encoding="utf-8")
                return []

            config = {
                "normalization": {"final_newline": True},
                "mutators": {
                    "lint_md_chinese_typography": False,
                    "markdown_table_fixer": False,
                    "markdownlint_fix": False,
                },
                "validators": {},
                "safety": {
                    "backup_before_replace": True,
                    "fail_on_missing_selected_mutator": True,
                },
            }
            quarantine_root = root / "quarantine"
            with mock.patch.object(MODULE, "def_apply_mutators", side_effect=inject_link_change):
                result = MODULE.def_process_file(
                    source=source,
                    input_root=root / "input",
                    action="fix",
                    formatter="none",
                    add_toc=False,
                    dry_run=False,
                    strict=False,
                    config=config,
                    registry=MODULE.def_tool_registry(),
                    backup_root=root / "backup",
                    quarantine_root=quarantine_root,
                    timeout_seconds=10,
                )
            self.assertEqual(result.status, "failed")
            self.assertIn("links", result.semantic_guard)
            self.assertEqual(source.read_text(encoding="utf-8"), original)
            self.assertEqual(Path(result.quarantine_path), quarantine_root / "nested" / "source.md")
            self.assertTrue((quarantine_root / "nested" / "source.md").is_file())

    def test_reconstruction_catalog_has_twenty_unique_factors_per_domain(self) -> None:
        catalog = json.loads((ENGINE_ROOT / "config" / "reconstruction_rules.json").read_text(encoding="utf-8"))
        for key, prefix in (("text_failures", "T"), ("table_failures", "B")):
            codes = [item["code"] for item in catalog[key]]
            self.assertEqual(len(codes), 20)
            self.assertEqual(len(set(codes)), 20)
            self.assertTrue(all(code.startswith(prefix) for code in codes))

    def test_sentence_splitter_protects_version_decimal_and_abbreviation(self) -> None:
        analysis = RECON.def_analyze_markdown_text(
            "# Release\n\nVersion 1.2.3 is stable. Dr. Chen approved it.\n"
        )
        self.assertEqual([item["text"] for item in analysis["sentences"]], [
            "Version 1.2.3 is stable.",
            "Dr. Chen approved it.",
        ])

    def test_callout_marker_is_not_split_as_a_sentence(self) -> None:
        analysis = RECON.def_analyze_markdown_text(
            "> [!NOTE]\n> 這是完整的警告內容。\n"
        )
        self.assertEqual(len(analysis["sentences"]), 1)
        self.assertEqual(analysis["sentences"][0]["text"], "這是完整的警告內容。")

    def test_safe_repair_inserts_boundaries_but_never_merges(self) -> None:
        source = "前一段。\n# 標題\n下一段。\n"
        repaired, audit = RECON.def_safe_repair_markdown_text(source)
        second, second_audit = RECON.def_safe_repair_markdown_text(repaired)
        self.assertEqual(repaired, "前一段。\n\n# 標題\n\n下一段。\n")
        self.assertEqual(audit["merge_operations"], 0)
        self.assertEqual(audit["fabricated_cells"], 0)
        self.assertEqual(repaired, second)
        self.assertFalse(second_audit["changed"])

    def test_table_parser_protects_inline_code_pipe(self) -> None:
        analysis = RECON.def_analyze_markdown_text(
            "| Code | Value |\n| --- | ---: |\n| `a|b` | 1 |\n"
        )
        self.assertEqual(analysis["gate"], "PASS")
        self.assertEqual(analysis["tables"][0]["expected_columns"], 2)
        self.assertEqual(analysis["tables"][0]["rows"][0], ["`a|b`", "1"])

    def test_table_shape_failure_is_blocked(self) -> None:
        analysis = RECON.def_analyze_markdown_text(
            "| A | B |\n| --- | --- |\n| 1 | 2 | 3 |\n"
        )
        codes = {item["code"] for item in analysis["findings"]}
        self.assertEqual(analysis["gate"], "FAIL")
        self.assertIn("B003", codes)

    def test_process_gate_preserves_original_malformed_table(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "malformed.md"
            original = "# Table\n\n| A | B |\n| --- | --- |\n| 1 | 2 | 3 |\n"
            source.write_text(original, encoding="utf-8")
            config = {
                "normalization": {"final_newline": True},
                "mutators": {
                    "lint_md_chinese_typography": False,
                    "markdown_table_fixer": False,
                    "markdownlint_fix": False,
                },
                "validators": {},
                "safety": {
                    "backup_before_replace": True,
                    "fail_on_missing_selected_mutator": True,
                },
                "reconstruction": {
                    "safe_structure_repair": True,
                    "fail_on_fail": True,
                    "fail_on_review_in_strict": True,
                },
            }
            result = MODULE.def_process_file(
                source=source,
                input_root=source,
                action="fix",
                formatter="none",
                add_toc=False,
                dry_run=False,
                strict=True,
                config=config,
                registry=MODULE.def_tool_registry(),
                backup_root=root / "backup",
                quarantine_root=root / "quarantine",
                timeout_seconds=10,
            )
            self.assertEqual(result.status, "failed")
            self.assertEqual(result.reconstruction_source_gate, "FAIL")
            self.assertIn("Reconstruction source gate failed", result.errors)
            self.assertEqual(source.read_text(encoding="utf-8"), original)

    def test_missing_table_delimiter_requires_review_without_fabrication(self) -> None:
        source = "| A | B |\n| 1 | 2 |\n"
        analysis = RECON.def_analyze_markdown_text(source)
        repaired, audit = RECON.def_safe_repair_markdown_text(source)
        self.assertEqual(analysis["gate"], "REVIEW")
        self.assertIn("B001", {item["code"] for item in analysis["findings"]})
        self.assertEqual(source, repaired)
        self.assertEqual(audit["fabricated_cells"], 0)

    def test_short_table_delimiter_is_expanded_without_cell_fabrication(self) -> None:
        source = "| 名稱 | 數值 |\n| -- | :-: |\n| A | 1 |\n"
        repaired, audit = RECON.def_safe_repair_markdown_text(source)
        analysis = RECON.def_analyze_markdown_text(repaired)
        self.assertEqual(repaired, "| 名稱 | 數值 |\n| --- | :---: |\n| A | 1 |\n")
        self.assertEqual(audit["expanded_delimiters"], 1)
        self.assertEqual(audit["fabricated_cells"], 0)
        self.assertEqual(analysis["gate"], "PASS")

    def test_staged_validation_preserves_existing_relative_link_context(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            target = root / "target.md"
            source.write_text("# Source\n\n[Target](target.md)\n", encoding="utf-8")
            target.write_text("# Target\n", encoding="utf-8")
            stage_root = root / "stage"
            stage_root.mkdir()
            staged = stage_root / "source.md"
            staged.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            copied = MODULE.def_stage_local_link_targets(source, staged, stage_root)
            self.assertEqual(copied, ["target.md"])
            self.assertEqual((stage_root / "target.md").read_text(encoding="utf-8"), "# Target\n")

    def test_staged_validation_supports_reference_and_html_targets(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            source.write_text(
                "# Source\n\n[Doc][guide]\n\n[guide]: docs/guide.md\n\n<img src=\"images/a.png\">\n",
                encoding="utf-8",
            )
            (root / "docs").mkdir()
            (root / "images").mkdir()
            (root / "docs" / "guide.md").write_text("# Guide\n", encoding="utf-8")
            (root / "images" / "a.png").write_bytes(b"png")
            stage_root = root / "stage"
            stage_root.mkdir()
            staged = stage_root / "source.md"
            staged.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            copied = MODULE.def_stage_local_link_targets(source, staged, stage_root)
            self.assertEqual(copied, ["docs/guide.md", "images/a.png"])
            self.assertTrue((stage_root / "docs" / "guide.md").is_file())
            self.assertEqual((stage_root / "images" / "a.png").read_bytes(), b"png")

    def test_data_is_classified_into_information_units_with_lineage(self) -> None:
        analysis = RECON.def_analyze_markdown_text(
            "# 財務\n\n營收：123 億元。\n\n必須驗證來源。\n\n| 年度 | EPS |\n| --- | ---: |\n| 2026 | 12.5 |\n",
            "sample.md",
        )
        kinds = {item["kind"] for item in analysis["information_units"]}
        self.assertTrue({"key_value", "action", "table_record"}.issubset(kinds))
        self.assertTrue(all(item["source_sha256"] == analysis["source_sha256"] for item in analysis["information_units"]))
        self.assertTrue(all(item["heading_path"] == ["財務"] for item in analysis["information_units"]))

    def test_reconstruction_guard_detects_sentence_and_table_changes(self) -> None:
        before = RECON.def_analyze_markdown_text(
            "# A\n\nFirst sentence. Second sentence.\n\n| X | Y |\n| --- | --- |\n| 1 | 2 |\n"
        )
        after = RECON.def_analyze_markdown_text(
            "# A\n\nFirst sentence Second sentence.\n\n| X | Y |\n| --- | --- |\n| 1 | 9 |\n"
        )
        comparison = RECON.def_compare_reconstruction(before, after)
        self.assertFalse(comparison["passed"])
        self.assertIn("sentences", comparison["differences"])
        self.assertIn("tables", comparison["differences"])

    def test_reconstruction_indexes_write_three_utf8_bom_csv_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            analysis = RECON.def_analyze_markdown_text(
                "# A\n\nValue: 1.\n\n| X | Y |\n| --- | --- |\n| 1 | 2 |\n",
                "sample.md",
            )
            sidecar = root / "sample.md.structure.json"
            RECON.def_write_structure_sidecar(
                sidecar,
                {"source_path": "sample.md", "analysis": analysis},
            )
            artifacts = RECON.def_write_reconstruction_indexes(root)
            self.assertEqual(set(artifacts), {"sentence_ssot", "information_ssot", "table_ssot"})
            self.assertTrue(all(Path(path).read_bytes().startswith(b"\xef\xbb\xbf") for path in artifacts.values()))


if __name__ == "__main__":
    unittest.main()
