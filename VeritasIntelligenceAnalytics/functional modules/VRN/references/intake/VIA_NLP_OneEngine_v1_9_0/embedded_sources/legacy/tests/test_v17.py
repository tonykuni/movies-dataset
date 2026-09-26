from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from via_nlp_engine.bundle_ops import PACKAGE_FILENAMES, export_reconstruction_package, read_document_bundle
from via_nlp_engine.engine import VIAEngine
from via_nlp_engine.knowledge import KnowledgeBuilder
from via_nlp_engine.system_manager import build_default_system_manager
from via_nlp_engine.text_ops import TextProcessor


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEXICON_PATH = PROJECT_ROOT / "data" / "lexicon" / "ssot_lexicon.json"
GOVERNANCE_PATH = PROJECT_ROOT / "config" / "governance.json"
CONFIG_PATH = PROJECT_ROOT / "config" / "default.json"


class V17ModuleCompositionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.processor = TextProcessor(LEXICON_PATH)
        self.builder = KnowledgeBuilder(
            self.processor,
            GOVERNANCE_PATH,
            {"cpu_tools": {"use_available_providers": False}, "max_ai_graph_edges": 12000},
        )

    def test_class_function_parameter_and_library_become_scoped_components(self) -> None:
        text = (
            "```python\n"
            "import json\n"
            "MAX_BATCH = 32\n"
            "class Worker:\n"
            "    def run(self, payload: str, retries=2) -> dict:\n"
            "        return json.loads(payload)\n"
            "def build_report(data, top_k=5):\n"
            "    return len(data)\n"
            "```\n"
        )
        result = self.builder.knowledge(text)["module_composition_registry"]
        kinds = {item["component_kind"] for item in result["component_registry"]}
        self.assertTrue({"class", "function", "parameter", "library", "code_fragment"}.issubset(kinds))
        class_component = next(item for item in result["component_registry"] if item["component_kind"] == "class")
        self.assertEqual(class_component["name"], "Worker")
        self.assertEqual(class_component["contract"]["methods"][0]["name"], "run")
        self.assertEqual(result["library_registry"][0]["library_kind"], "standard_library")
        self.assertEqual(result["quality_gates"]["component_source_traceability"], "pass")
        self.assertFalse(result["quality_gates"]["code_execution_authorized"])

    def test_parameter_conflicts_stay_scoped_and_generate_decision_card(self) -> None:
        text = (
            "```python\nLIMIT = 10\ndef run(value=1):\n    return value\n```\n"
            "```python\nLIMIT = 20\ndef run(value=2):\n    return value\n```\n"
        )
        result = self.builder.knowledge(text)["module_composition_registry"]
        names = {item["name"] for item in result["parameter_registry"]["conflicts"]}
        card_kinds = {item["kind"] for item in result["decision_cards"]}
        self.assertIn("LIMIT", names)
        self.assertIn("PARAMETER_CONFLICT", card_kinds)
        self.assertFalse(result["quality_gates"]["conflicting_values_silently_resolved"])

    def test_same_parameter_name_in_distinct_scopes_is_not_a_blocking_conflict(self) -> None:
        text = (
            "```python\ndef first(limit=10):\n    return limit\n```\n"
            "```python\ndef second(limit=20):\n    return limit\n```\n"
        )
        result = self.builder.knowledge(text)["module_composition_registry"]["parameter_registry"]
        self.assertEqual(result["conflicts"], [])
        self.assertTrue(any(item["name"] == "limit" for item in result["cross_scope_name_collisions"]))

    def test_dependency_graph_orders_provider_before_consumer(self) -> None:
        text = (
            "```python\ndef provide(value):\n    return value\n```\n"
            "```python\ndef consume(value):\n    return provide(value)\n```\n"
        )
        result = self.builder.knowledge(text)["module_composition_registry"]
        edge = next(item for item in result["dependency_graph"]["edges"] if item["symbol"] == "provide")
        order = result["dependency_graph"]["topological_order"]
        self.assertLess(order.index(edge["from"]), order.index(edge["to"]))
        self.assertTrue(result["dependency_graph"]["topology_complete"])

    def test_incomplete_fragment_remains_isolated_and_blocked(self) -> None:
        text = "f_M = 1.0\nelif margin_ratio < 1.6:\nf_M = -1.0\n"
        result = self.builder.knowledge(text)["module_composition_registry"]
        self.assertEqual(result["statistics"]["modules"], 1)
        self.assertEqual(result["modules"][0]["status"], "blocked")
        self.assertEqual(result["modules"][0]["automatic_merge_applied"], False)
        self.assertFalse(result["quality_gates"]["incomplete_fragments_auto_stitched"])
        self.assertTrue(result["decision_cards"])

    def test_macro_architecture_keeps_nlp_independent_under_system_manager(self) -> None:
        result = self.builder.knowledge("User: 建立完整 NLP 摘要。\n")["module_composition_registry"]
        architecture = result["macro_architecture"]
        modules = {item["module_id"]: item for item in architecture["macro_modules"]}
        self.assertEqual(len(modules), 7)
        self.assertTrue(modules["NLP-CORE"]["independent"])
        self.assertEqual(modules["NLP-CORE"]["dependencies"], [])
        self.assertFalse(architecture["system_manager"]["contains_domain_logic"])

    def test_mind_map_exposes_system_manager_and_macro_modules(self) -> None:
        result = self.builder.knowledge("# 需求\n建立 NLP Application System。\n")
        nodes = {item["node_id"]: item for item in result["mind_map"]["ai_view"]["nodes"]}
        self.assertIn("SYSTEM-MANAGER", nodes)
        self.assertIn("NLP-CORE", nodes)
        self.assertEqual(nodes["NLP-CORE"]["node_type"], "macro_module")
        self.assertTrue(result["quality_gates"]["cpu_graph_endpoints_valid"])


class V17ContentRoleAndSummarizerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.processor = TextProcessor(LEXICON_PATH)
        self.builder = KnowledgeBuilder(
            self.processor,
            GOVERNANCE_PATH,
            {"cpu_tools": {"use_available_providers": False}},
        )

    def test_non_body_lines_are_isolated_without_dropping_body(self) -> None:
        text = (
            "# 市場報告\n"
            "公司營收成長 20%，這是本文。\n"
            "首頁\n"
            "廣告：立即訂閱\n"
            "```python\nprint('specialized code')\n```\n"
            "© 2026 Example. All rights reserved.\n"
        )
        result = self.builder.knowledge(text)["content_role_analysis"]
        roles = {item["role"] for item in result["non_body_register"]}
        self.assertTrue({"navigation", "advertisement", "code_evidence", "header_footer"}.issubset(roles))
        self.assertIn("公司營收成長 20%", result["body_projection"]["text"])
        self.assertNotIn("立即訂閱", result["body_projection"]["text"])
        self.assertTrue(result["quality_gates"]["all_source_characters_classified"])

    def test_repeated_short_content_is_retained_conservatively(self) -> None:
        text = "公司抬頭\n\n公司抬頭\n\n公司抬頭\n"
        result = self.builder.knowledge(text)["content_role_analysis"]
        candidates = [item for item in result["records"] if "repeated_short_content_retained" in item["reason_codes"]]
        self.assertTrue(candidates)
        self.assertTrue(all(item["include_in_body_summary"] for item in candidates))
        self.assertTrue(all(not item["review_required"] for item in candidates))
        self.assertFalse(result["quality_gates"]["low_confidence_content_silently_excluded"])

    def test_financial_advertising_terms_inside_body_are_not_misclassified(self) -> None:
        text = "電子紙廣告看板營收成長。\n廣告支出與實質可支配所得同時增加。\n"
        result = self.builder.knowledge(text)["content_role_analysis"]
        self.assertIn("電子紙廣告看板", result["body_projection"]["text"])
        self.assertIn("廣告支出", result["body_projection"]["text"])
        self.assertFalse(any(item["role"] == "advertisement" for item in result["records"]))

    def test_layout_dump_artifacts_require_document_level_context(self) -> None:
        dump_text = "HTML\nMD+1\n本文區(修復)\n真正本文。\n右資訊區\n側欄資料。\n"
        dump_result = self.builder.knowledge(dump_text)["content_role_analysis"]
        artifacts = [item for item in dump_result["records"] if "layout_dump_artifact" in item["reason_codes"]]
        self.assertGreaterEqual(len(artifacts), 3)
        self.assertNotIn("右資訊區", dump_result["body_projection"]["text"])
        sidebar = [item for item in dump_result["records"] if "explicit_sidebar_region" in item["reason_codes"]]
        self.assertTrue(sidebar)
        self.assertTrue(all(not item["include_in_body_summary"] for item in sidebar))
        self.assertIn("真正本文", dump_result["body_projection"]["text"])
        normal_result = self.builder.knowledge("我們要解析 HTML 並建立本文。\n")["content_role_analysis"]
        self.assertIn("HTML", normal_result["body_projection"]["text"])

    def test_standalone_financial_values_are_not_treated_as_page_numbers(self) -> None:
        text = "EPS (NT$)\n38\n120\n12/25\n3/26\n1,234.5\nPage 7 of 20\n- 8 -\n"
        result = self.builder.knowledge(text)["content_role_analysis"]
        self.assertIn("38\n", result["body_projection"]["text"])
        self.assertIn("120\n", result["body_projection"]["text"])
        self.assertIn("12/25\n", result["body_projection"]["text"])
        self.assertIn("3/26\n", result["body_projection"]["text"])
        page_items = [item for item in result["records"] if "page_number_marker" in item["reason_codes"]]
        self.assertEqual(len(page_items), 2)

    def test_new_document_boundary_closes_sidebar_region(self) -> None:
        text = (
            "HTML\nMD+1\n本文區(修復)\n本文 A。\n右資訊區\n側欄 A。\n"
            "report.docxDOCX_HEAD · 20 字\n新文件本文 B。\n"
        )
        result = self.builder.knowledge(text)["content_role_analysis"]
        self.assertNotIn("側欄 A", result["body_projection"]["text"])
        self.assertIn("新文件本文 B", result["body_projection"]["text"])

    def test_repair_projection_preserves_fact_tokens_and_never_writes_back(self) -> None:
        text = "營收為 1,234.5 億元，年增 ２０％，季度值為 0 0 0。\n"
        result = self.builder.knowledge(text)["content_role_analysis"]
        repair = result["repair_projection"]
        self.assertTrue(repair["fact_tokens_preserved"])
        self.assertTrue(repair["selected_for_body_summary"])
        self.assertIn("0 0 0", repair["candidate_text"])
        self.assertFalse(repair["semantic_rewrite_applied"])
        self.assertFalse(repair["source_writeback_applied"])

    def test_complete_summarizer_consumes_every_character_in_multiple_chunks(self) -> None:
        text = "".join(f"第 {index} 段資料顯示營收成長 {index % 20}%。\n" for index in range(4000))
        result = self.processor.summarize_complete(text, max_points=8, max_chunk_chars=5000)
        self.assertGreater(result["coverage"]["chunk_count"], 2)
        self.assertEqual(result["coverage"]["source_characters"], len(text))
        self.assertEqual(result["coverage"]["consumed_characters"], len(text))
        self.assertTrue(result["coverage"]["all_input_consumed"])
        self.assertFalse(result["coverage"]["silent_truncation"])

    def test_default_summary_uses_body_but_full_input_summary_is_also_kept(self) -> None:
        text = "# 研究\n本文結論是保留完整資料。\n首頁\n廣告：立即購買\n"
        result = self.builder.knowledge(text)
        roles = result["content_role_analysis"]
        self.assertEqual(roles["summarizer"]["default_projection"], "body_summary")
        self.assertTrue(roles["summarizer"]["full_input_was_also_processed"])
        self.assertIn("完整資料", result["body_of_knowledge"]["executive_summary"])
        self.assertTrue(result["quality_gates"]["summarizer_complete_input_consumed"])


class V17SystemIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.processor = TextProcessor(LEXICON_PATH)
        self.builder = KnowledgeBuilder(
            self.processor,
            GOVERNANCE_PATH,
            {"cpu_tools": {"use_available_providers": False}},
        )

    def test_system_manager_routes_registered_nlp_and_fails_closed(self) -> None:
        manager = build_default_system_manager(self.processor, self.builder)
        manager.start()
        try:
            normalized = manager.dispatch("NLP-CORE", "normalize", text="  中文   NLP  ")
            self.assertEqual(normalized, "中文 NLP")
            with self.assertRaises(KeyError):
                manager.dispatch("NLP-CORE", "not_registered", text="x")
        finally:
            manager.stop()
        self.assertEqual(manager.health()["status"], "stopped")

    def test_v161_output_contract_is_preserved_additively(self) -> None:
        result = self.builder.knowledge("User: 保留原文並建立摘要。\n")
        old_keys = {
            "body_of_knowledge", "mind_map", "mind_map_evolution", "dialogue_flow",
            "ssot_dictionary", "via_keywords", "code_registry", "code_reconstruction_package",
            "function_classification", "code_restoration", "code_integration_blueprint",
            "context_reconstruction", "template_reconstruction", "layout_analysis",
            "local_provider_registry", "cpu_nlp_augmentation", "knowledge_object_registry",
            "instruction_reconstruction", "bilingual_knowledge_body", "source_ledger",
            "refinement_ledger", "completeness", "quality_gates", "reorganization_policy",
        }
        self.assertTrue(old_keys.issubset(result))
        self.assertIn("module_composition_registry", result)
        self.assertIn("content_role_analysis", result)

    def test_export_includes_composition_architecture_and_content_roles(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "discussion.md"
            source.write_text("# 本文\n需要建立摘要。\n首頁\n", encoding="utf-8")
            bundle = read_document_bundle([source])
            process_result = {
                "request_id": "V17-TEST", "task": "knowledge", "language": "mixed",
                "output": self.builder.knowledge(bundle["text"]), "route": {}, "resources_before": {},
                "resources_after": {}, "elapsed_ms": 1.0, "cache_hit": False, "warnings": [],
                "engine_version": "1.8.0",
            }
            package = export_reconstruction_package(root / "output", bundle, process_result)
            names = {Path(item).name for item in package["files"]}
            self.assertIn(PACKAGE_FILENAMES["module_composition"], names)
            self.assertIn(PACKAGE_FILENAMES["system_architecture"], names)
            self.assertIn(PACKAGE_FILENAMES["content_role_analysis"], names)

    def test_health_advertises_application_system_and_new_contracts(self) -> None:
        with VIAEngine(
            config_path=CONFIG_PATH,
            overrides={"knowledge": {"cpu_tools": {"use_available_providers": False}}},
            auto_start=False,
        ) as engine:
            health = engine.health()
        self.assertEqual(health["engine"]["version"], "1.8.0")
        self.assertEqual(health["engine"]["name"], "VIA NLP Application System")
        self.assertEqual(health["capabilities"]["module_composition_schema"], "VIA_MODULE_COMPOSITION_REGISTRY/1.0")
        self.assertEqual(health["capabilities"]["content_role_analysis_schema"], "VIA_CONTENT_ROLE_ANALYSIS/1.0")
        self.assertEqual(health["system_manager"]["status"], "ready")
        self.assertTrue(health["system_manager"]["quality_gates"]["nlp_core_is_independent"])


if __name__ == "__main__":
    unittest.main()
