from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from via_nlp_engine.bundle_ops import PACKAGE_FILENAMES, export_reconstruction_package, read_document_bundle
from via_nlp_engine.code_restoration import CodeRestorer
from via_nlp_engine.context_reconstruction import ContextReconstructor
from via_nlp_engine.engine import VIAEngine
from via_nlp_engine.function_classifier import FunctionClassifier
from via_nlp_engine.ingest import _read_with_markitdown
from via_nlp_engine.knowledge import KnowledgeBuilder, LosslessSegmenter
from via_nlp_engine.layout_analysis import MarkdownLayoutAnalyzer
from via_nlp_engine.provider_registry import LocalProviderRegistry
from via_nlp_engine.template_reconstruction import StandardTemplateReconstructor
from via_nlp_engine.text_ops import TextProcessor


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEXICON_PATH = PROJECT_ROOT / "data" / "lexicon" / "ssot_lexicon.json"
GOVERNANCE_PATH = PROJECT_ROOT / "config" / "governance.json"


class V15ReconstructionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.processor = TextProcessor(LEXICON_PATH)
        self.builder = KnowledgeBuilder(self.processor, GOVERNANCE_PATH)

    def test_local_provider_registry_contains_twenty_requested_groups_plus_markitdown(self) -> None:
        result = LocalProviderRegistry(PROJECT_ROOT).status()
        identifiers = {item["provider_id"] for item in result["groups"]}
        self.assertEqual(result["schema"], "VIA_LOCAL_PROVIDER_REGISTRY/1.0")
        self.assertEqual(result["provider_group_count"], 21)
        self.assertTrue({f"PY{index:02d}" for index in range(1, 11)}.issubset(identifiers))
        self.assertTrue({f"JS{index:02d}" for index in range(1, 11)}.issubset(identifiers))
        self.assertIn("MS01", identifiers)
        self.assertFalse(result["policy"]["auto_install"])
        self.assertFalse(result["policy"]["auto_execute"])
        self.assertFalse(result["policy"]["captcha_bypass"])

    def test_markdown_layout_classifies_all_common_blocks_losslessly(self) -> None:
        text = (
            "---\ntitle: VIA\n---\n# 標題\n\n段落含 [連結](https://example.test)、`code` 與 **粗體**。\n"
            "- [x] 完成\n- 項目\n1. 步驟\n> 引用\n\n| 欄位 | 值 |\n|---|---|\n| A | 1 |\n\n"
            "```python\ndef run():\n    return 1\n```\n\n$$\nx=1\n$$\n\n<div>HTML</div>\n"
        )
        segmentation = LosslessSegmenter().segment(text)
        refinement = []
        for item in segmentation["segments"]:
            refinement.append({"segment_id": item["segment_id"], "changes": []})
        result = MarkdownLayoutAnalyzer().build(text, segmentation["segments"], refinement)
        types = {item["block_type"] for item in result["blocks"]}
        self.assertTrue(result["completeness"]["exact_reconstruction"])
        self.assertTrue({"front_matter", "heading", "paragraph", "task_list", "unordered_list", "ordered_list", "blockquote", "table", "fenced_code", "math_block", "html_block"}.issubset(types))
        self.assertGreater(result["statistics"]["inline_marks"], 2)

    def test_plain_text_layout_fallback_never_drops_unknown_content(self) -> None:
        text = "無標記第一行\n仍是原文\n"
        segments = LosslessSegmenter().segment(text)["segments"]
        result = MarkdownLayoutAnalyzer().build(text, segments, [])
        self.assertEqual("".join(item["source_text"] for item in result["blocks"]), text)
        self.assertEqual(result["blocks"][0]["block_type"], "paragraph")

    def test_disordered_dialogue_builds_reply_candidate_and_topic_threads(self) -> None:
        text = "User: 如何重建程式？\nAssistant: 請先用 AST 擷取函式，再驗證。\nUser: 股票先放旁邊。\nUser: 回到程式，需要保留原文。\n"
        result = self.builder.knowledge(text)["context_reconstruction"]
        self.assertIn(result["document_mode"]["value"], {"dialogue", "mixed"})
        self.assertGreaterEqual(result["statistics"]["reply_links"], 1)
        self.assertGreaterEqual(result["statistics"]["topic_threads"], 1)
        self.assertEqual(result["quality_gates"]["source_traceability"], "pass")
        self.assertFalse(result["quality_gates"]["invented_bridge_text"])

    def test_unanswered_question_is_explicit_review_item(self) -> None:
        text = "User: 是否已完成驗證？\n"
        result = self.builder.knowledge(text)["context_reconstruction"]
        self.assertGreaterEqual(result["statistics"]["unanswered_questions"], 1)
        self.assertTrue(any(item["type"] == "unanswered_question" for item in result["review_queue"]["context_issues"]))

    def test_function_classifier_uses_names_calls_and_imports_as_evidence(self) -> None:
        text = "```python\nimport requests\ndef fetch_and_validate(url):\n    response = requests.get(url)\n    return response.json()\n```\n"
        result = self.builder.knowledge(text)["function_classification"]
        record = next(item for item in result["records"] if item["symbol_name"] == "fetch_and_validate")
        categories = {item["category"] for item in record["categories"]}
        self.assertEqual(record["primary_category"], "network")
        self.assertIn("validation", categories)
        self.assertFalse(result["quality_gates"]["code_execution_authorized"])

    def test_code_block_without_function_is_classified_but_requires_review(self) -> None:
        text = "```json\n{\"MAX_BATCH\": 32}\n```\n"
        result = self.builder.knowledge(text)["function_classification"]
        self.assertEqual(result["statistics"]["code_blocks_without_functions"], 1)
        self.assertTrue(result["records"][0]["review_required"])

    def test_python_set_constant_is_deterministic_json_array(self) -> None:
        text = "```python\nSUPPORTED = {'.py', '.js', '.ts'}\n```\n"
        result = self.builder.knowledge(text)
        value = result["code_registry"][0]["engine_spec"]["parameters"]["SUPPORTED"]
        self.assertEqual(value, [".js", ".py", ".ts"])

    def test_code_restoration_builds_non_executing_module_templates(self) -> None:
        text = "```python\ndef render_dashboard(data):\n    return str(data)\n```\n"
        result = self.builder.knowledge(text)["code_restoration"]
        self.assertEqual(result["schema"], "VIA_CODE_RESTORATION/1.0")
        self.assertEqual(result["statistics"]["module_templates"], 1)
        self.assertIn("render_dashboard", result["modules"][0]["structure"]["functions"])
        self.assertFalse(result["quality_gates"]["automatic_file_write"])
        self.assertFalse(result["quality_gates"]["code_execution_authorized"])

    def test_article_standard_template_is_source_filled_and_derivative(self) -> None:
        text = "# 系統說明\n背景：保留原文。\n結果：輸出逐字帳本。\n"
        result = self.builder.knowledge(text)["template_reconstruction"]
        self.assertEqual(result["selected_template"]["template_schema"], "VIA_ARTICLE_TEMPLATE/1.0")
        self.assertTrue(all(item["filled_from_source"] for item in result["slots"]))
        self.assertFalse(result["quality_gates"]["automatic_slot_fill"])
        self.assertFalse(result["source_integrity"]["template_slots_replace_source_ledger"])

    def test_knowledge_output_enriches_mind_map_with_layout_template_and_functions(self) -> None:
        text = "# 規格\n必須驗證。\n```python\ndef validate_input(value):\n    return bool(value)\n```\n"
        result = self.builder.knowledge(text)
        node_types = {item["node_type"] for item in result["mind_map"]["ai_view"]["nodes"]}
        self.assertEqual(result["layout_analysis"]["schema"], "VIA_MARKDOWN_LAYOUT_ANALYSIS/1.0")
        self.assertEqual(result["context_reconstruction"]["schema"], "VIA_CONTEXT_RECONSTRUCTION/1.0")
        self.assertEqual(result["template_reconstruction"]["schema"], "VIA_TEMPLATE_RECONSTRUCTION/1.0")
        self.assertTrue({"layout_analysis", "standard_template", "function"}.issubset(node_types))

    def test_export_package_includes_all_v15_review_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "discussion.md"
            source.write_text("# 規格\nUser: 如何測試？\nAssistant: 執行驗證。\n", encoding="utf-8")
            bundle = read_document_bundle([source])
            process_result = {
                "request_id": "V15-TEST", "task": "knowledge", "language": "mixed",
                "output": self.builder.knowledge(bundle["text"]), "route": {}, "resources_before": {},
                "resources_after": {}, "elapsed_ms": 1.0, "cache_hit": False, "warnings": [],
                "engine_version": "1.5.0",
            }
            package = export_reconstruction_package(root / "output", bundle, process_result)
            names = {Path(item).name for item in package["files"]}
            for key in (
                "function_classification", "code_restoration", "context_reconstruction",
                "template_reconstruction", "layout_analysis", "local_provider_registry",
            ):
                self.assertIn(PACKAGE_FILENAMES[key], names)

    def test_markitdown_missing_dependency_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            selected = Path(temp) / "sample.pptx"
            selected.write_bytes(b"not-a-pptx")
            with patch("via_nlp_engine.ingest.importlib.util.find_spec", return_value=None):
                with self.assertRaisesRegex(RuntimeError, "markitdown"):
                    _read_with_markitdown(selected)

    def test_default_bundle_does_not_silently_include_image_without_markitdown(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "source.md").write_text("# source\n", encoding="utf-8")
            (root / "image.png").write_bytes(b"png")
            bundle = read_document_bundle([root], use_markitdown=False)
            self.assertEqual(bundle["completeness"]["file_count"], 1)

    def test_health_advertises_v15_schemas(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            config = PROJECT_ROOT / "config" / "default.json"
            with VIAEngine(config_path=config, auto_start=False) as engine:
                health = engine.health()
            self.assertEqual(health["engine"]["version"], "1.5.0")
            self.assertEqual(health["capabilities"]["markdown_layout_schema"], "VIA_MARKDOWN_LAYOUT_ANALYSIS/1.0")
            self.assertEqual(health["capabilities"]["code_restoration_schema"], "VIA_CODE_RESTORATION/1.0")


if __name__ == "__main__":
    unittest.main()
