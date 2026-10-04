from __future__ import annotations

import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from via_nlp_engine.bundle_ops import PACKAGE_FILENAMES, export_reconstruction_package, read_document_bundle
from via_nlp_engine.config import load_config
from via_nlp_engine.cpu_augmentation import CPUNLPAugmentor, decode_bytes_with_cpu_detector
from via_nlp_engine.engine import VIAEngine
from via_nlp_engine.knowledge import KnowledgeBuilder
from via_nlp_engine.provider_registry import LocalProviderRegistry
from via_nlp_engine.text_ops import TextProcessor


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEXICON_PATH = PROJECT_ROOT / "data" / "lexicon" / "ssot_lexicon.json"
GOVERNANCE_PATH = PROJECT_ROOT / "config" / "governance.json"
CONFIG_PATH = PROJECT_ROOT / "config" / "default.json"


def sample_ssot() -> dict:
    return {
        "entries": [
            {"canonical": "NLP", "aliases": ["NLP", "自然語言處理"]},
            {"canonical": "Mind Map", "aliases": ["Mind Map", "心智圖"]},
        ]
    }


def sample_map(missing_endpoint: bool = False) -> dict:
    edges = [{"from": "ROOT", "to": "S1", "relation": "grounded_by"}]
    if missing_endpoint:
        edges.append({"from": "S1", "to": "MISSING", "relation": "invalid"})
    return {
        "ai_view": {
            "nodes": [
                {"node_id": "ROOT", "node_type": "knowledge_root"},
                {"node_id": "S1", "node_type": "source_segment"},
            ],
            "edges": edges,
        }
    }


class V16CPUAugmentationTests(unittest.TestCase):
    def test_registry_adds_ten_cpu_groups_without_removing_v15_groups(self) -> None:
        result = LocalProviderRegistry(PROJECT_ROOT).status()
        cpu = result["cpu_nlp_provider_registry"]
        self.assertEqual(result["provider_group_count"], 21)
        self.assertEqual(cpu["provider_group_count"], 10)
        self.assertEqual(result["total_provider_group_count"], 31)
        self.assertEqual({item["provider_id"] for item in cpu["groups"]}, {f"CPU{index:02d}" for index in range(1, 11)})

    def test_decoder_is_round_trip_exact_for_utf8(self) -> None:
        raw = "中文 English 2026".encode("utf-8")
        result = decode_bytes_with_cpu_detector(raw)
        self.assertEqual(result["text"], "中文 English 2026")
        self.assertTrue(result["round_trip_exact"])

    def test_unicode_repair_rejects_changed_number(self) -> None:
        augmentor = CPUNLPAugmentor()
        fake_ftfy = types.SimpleNamespace(fix_text=lambda value: value.replace("10%", "11%"))
        with patch.object(augmentor, "_use", side_effect=lambda module: module == "ftfy"):
            with patch.dict(sys.modules, {"ftfy": fake_ftfy}):
                result = augmentor._repair_candidate("成長 10%")
        self.assertEqual(result["status"], "rejected_fact_change")
        self.assertIsNone(result["candidate_text"])
        self.assertFalse(result["auto_applied"])

    def test_unicode_repair_candidate_never_auto_applies(self) -> None:
        augmentor = CPUNLPAugmentor()
        fake_ftfy = types.SimpleNamespace(fix_text=lambda value: value.replace("FranÃ§ais", "Français"))
        with patch.object(augmentor, "_use", side_effect=lambda module: module == "ftfy"):
            with patch.dict(sys.modules, {"ftfy": fake_ftfy}):
                result = augmentor._repair_candidate("FranÃ§ais")
        self.assertEqual(result["status"], "candidate_review_required")
        self.assertEqual(result["candidate_text"], "Français")
        self.assertFalse(result["auto_applied"])

    def test_sentence_fallback_supports_chinese_and_english(self) -> None:
        result = CPUNLPAugmentor({"use_available_providers": False})._sentence_analysis("第一句。Second sentence! 第三句？")
        self.assertEqual(result["sentence_count"], 3)
        self.assertEqual(result["backend"], "deterministic_unicode_regex")

    def test_language_route_preserves_mixed_classification(self) -> None:
        result = CPUNLPAugmentor({"use_available_providers": False})._language_analysis("中文 NLP English 心智圖")
        self.assertEqual(result["routing_decision"], "mixed")
        self.assertFalse(result["provider_may_override_routing"])

    def test_fuzzy_aliases_are_candidates_only(self) -> None:
        result = CPUNLPAugmentor({"use_available_providers": False, "fuzzy_threshold": 60})._fuzzy_alias_candidates("NPL", ["NLP"])
        self.assertGreaterEqual(result["candidate_count"], 1)
        self.assertFalse(result["auto_promoted"])

    def test_exact_alias_match_reports_source_offsets(self) -> None:
        result = CPUNLPAugmentor({"use_available_providers": False})._exact_alias_matches("建立 NLP 心智圖", ["NLP", "心智圖"])
        self.assertEqual({item["term"] for item in result["matches"]}, {"NLP", "心智圖"})
        self.assertTrue(all(item["end"] > item["start"] for item in result["matches"]))

    def test_near_duplicate_detection_never_merges_or_deletes(self) -> None:
        segments = [
            {"segment_id": "S1", "text": "必須 保留 原文 並 建立 知識體"},
            {"segment_id": "S2", "text": "必須 保留 原文 並 建立 知識體"},
        ]
        result = CPUNLPAugmentor({"use_available_providers": False})._near_duplicate_candidates(segments)
        self.assertEqual(result["pair_count"], 1)
        self.assertFalse(result["automatic_merge_or_delete"])

    def test_graph_validation_fails_closed_on_missing_endpoint(self) -> None:
        result = CPUNLPAugmentor({"use_available_providers": False})._validate_graph(sample_map(missing_endpoint=True))
        self.assertEqual(result["status"], "review_required")
        self.assertEqual(result["missing_endpoint_count"], 1)
        self.assertFalse(result["graph_mutated"])

    def test_contract_round_trip_and_trie_fallback(self) -> None:
        augmentor = CPUNLPAugmentor({"use_available_providers": False})
        contract = augmentor._validate_contract({"中文": [1, 2], "ok": True})
        index = augmentor._lexicon_index(["NLP", "自然語言處理", "心智圖"])
        self.assertTrue(contract["round_trip_equal"])
        self.assertTrue(index["derived_index"])
        self.assertTrue(index["rebuildable"])

    def test_full_augmentation_has_ten_tools_and_keeps_source_hash(self) -> None:
        text = "User: 建立 NLP。\nAssistant: 保留原文。\n"
        segments = [
            {"segment_id": "S1", "text": text, "sha256": "unused"},
        ]
        result = CPUNLPAugmentor({"use_available_providers": False}).build(text, segments, sample_ssot(), sample_map())
        self.assertEqual(result["schema"], "VIA_CPU_NLP_AUGMENTATION/1.0")
        self.assertEqual(result["quality_gates"]["provider_count"], 10)
        self.assertFalse(result["quality_gates"]["source_text_mutated"])
        self.assertFalse(result["quality_gates"]["automatic_segment_merge_or_deletion"])


class V16IntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.builder = KnowledgeBuilder(TextProcessor(LEXICON_PATH), GOVERNANCE_PATH, {"cpu_tools": {"use_available_providers": False}})

    def test_knowledge_and_mind_map_include_cpu_validation(self) -> None:
        result = self.builder.knowledge("User: 重建 NLP 程式。\nAssistant: Use AST and keep source.\n")
        self.assertIn("cpu_nlp_augmentation", result)
        self.assertIn("cpu_graph_validation", result["mind_map"]["ai_view"])
        self.assertEqual(result["quality_gates"]["cpu_nlp_provider_groups"], 10)
        self.assertFalse(result["quality_gates"]["cpu_nlp_source_mutation"])

    def test_v15_output_contract_is_a_subset_of_v16(self) -> None:
        result = self.builder.knowledge("User: 保留原文並建立 Mind Map。\n")
        v15_keys = {
            "body_of_knowledge", "mind_map", "mind_map_evolution", "dialogue_flow",
            "ssot_dictionary", "via_keywords", "code_registry", "code_reconstruction_package",
            "function_classification", "code_restoration", "code_integration_blueprint",
            "context_reconstruction", "template_reconstruction", "layout_analysis",
            "local_provider_registry", "knowledge_object_registry", "instruction_reconstruction",
            "bilingual_knowledge_body", "source_ledger", "refinement_ledger", "completeness",
            "quality_gates", "reorganization_policy",
        }
        self.assertTrue(v15_keys.issubset(result))
        self.assertIn("cpu_nlp_augmentation", result)

    def test_export_includes_cpu_augmentation_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "discussion.txt"
            source.write_text("User: 建立知識體。\nAssistant: Preserve source.\n", encoding="utf-8")
            bundle = read_document_bundle([source])
            process_result = {
                "request_id": "V16-TEST", "task": "knowledge", "language": "mixed",
                "output": self.builder.knowledge(bundle["text"]), "route": {}, "resources_before": {},
                "resources_after": {}, "elapsed_ms": 1.0, "cache_hit": False, "warnings": [],
                "engine_version": "1.8.0",
            }
            package = export_reconstruction_package(root / "output", bundle, process_result)
            names = {Path(item).name for item in package["files"]}
            self.assertIn(PACKAGE_FILENAMES["cpu_nlp_augmentation"], names)

    def test_config_rejects_automatic_duplicate_deletion(self) -> None:
        with self.assertRaisesRegex(ValueError, "automatic merge or delete"):
            load_config(CONFIG_PATH, {"knowledge": {"cpu_tools": {"automatic_merge_or_delete": True}}})

    def test_health_advertises_v16_cpu_contract(self) -> None:
        with VIAEngine(config_path=CONFIG_PATH, overrides={"knowledge": {"cpu_tools": {"use_available_providers": False}}}, auto_start=False) as engine:
            health = engine.health()
        self.assertEqual(health["engine"]["version"], "1.8.0")
        self.assertEqual(health["capabilities"]["cpu_nlp_optional_providers"], 10)
        self.assertEqual(health["capabilities"]["cpu_nlp_augmentation_schema"], "VIA_CPU_NLP_AUGMENTATION/1.0")
        self.assertFalse(health["capabilities"]["cpu_nlp_automatic_deduplication"])


if __name__ == "__main__":
    unittest.main()
