"""Tests for the local CPU-friendly knowledge extraction stack."""

from __future__ import annotations

import unittest

from knowledge_extraction_engine import ExtractionConfig, KnowledgeExtractionEngine
from local_knowledge_engine import CPUSettings, LocalKnowledgePipeline, library_status


class KnowledgeExtractionEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = KnowledgeExtractionEngine()
        self.parsed = {
            "text": "2026年Q1，受房地產市場波動影響，其 NPL Ratio 攀升至 1.85%。為防範風險，金管會要求將備抵呆賬覆蓋率提升至150%。",
            "sentences": [
                "2026年Q1，受房地產市場波動影響，其 NPL Ratio 攀升至 1.85%。",
                "為防範風險，金管會要求將備抵呆賬覆蓋率提升至150%。",
            ],
            "entities": [
                {"text": "房地產市場波動", "label": "CONCEPT"},
                {"text": "NPL Ratio", "label": "INDICATOR"},
                {"text": "金管會", "label": "POLICY_ORG"},
                {"text": "備抵呆賬覆蓋率", "label": "INDICATOR"},
            ],
        }

    def test_extracts_metric_causation_and_policy_action(self) -> None:
        triples = self.engine.extract(self.parsed)
        keys = {(item["subject"], item["predicate"], item["object"]) for item in triples}
        self.assertIn(("NPL Ratio", "攀升至", "1.85%"), keys)
        self.assertIn(("房地產市場波動", "causes (受影響)", "其 NPL Ratio 攀升至 1.85%"), keys)
        self.assertIn(("金管會", "要求", "備抵呆賬覆蓋率提升至150%"), keys)

        metric = next(item for item in triples if item["subject"] == "NPL Ratio")
        self.assertEqual(metric["attributes"]["trend"], "UP")
        self.assertAlmostEqual(metric["attributes"]["value_meta"]["numeric"], 0.0185)

    def test_enriches_numeric_entities_and_aliases(self) -> None:
        parsed = {
            "text": "不良贷款率为 2.5%，金额为 3.2億元。",
            "sentences": ["不良贷款率为 2.5%，金额为 3.2億元。"],
            "entities": [{"text": "不良贷款率", "label": "INDICATOR"}],
        }
        enriched = self.engine.enrich_entities(parsed["text"], parsed["entities"])
        by_label = {item["label"]: item for item in enriched}
        self.assertEqual(by_label["INDICATOR"]["attributes"]["canonical"], "不良貸款率")
        self.assertAlmostEqual(by_label["PERCENT"]["attributes"]["value_meta"]["percent"], 2.5)
        self.assertAlmostEqual(by_label["MONEY"]["attributes"]["value_meta"]["numeric"], 320000000)

    def test_respects_span_limits_and_deduplicates(self) -> None:
        constrained = KnowledgeExtractionEngine(ExtractionConfig(max_cause_chars=2))
        self.assertEqual(constrained._extract_causation("受房地產影響，其風險上升。"), [])
        self.assertEqual(
            len(self.engine.extract({"sentences": ["金管會要求加強監管。"], "entities": []})),
            1,
        )

    def test_graph_and_keyword_exports_are_local(self) -> None:
        triples = self.engine.extract(self.parsed)
        graph = self.engine.to_graph(triples)
        if isinstance(graph, dict):
            self.assertGreaterEqual(len(graph["nodes"]), 2)
            self.assertTrue(graph["edges"])
        else:
            self.assertGreaterEqual(graph.number_of_nodes(), 2)
            self.assertGreaterEqual(graph.number_of_edges(), 1)
        keywords = self.engine.rank_keywords(["信用風險 資產品質", "信用風險 NPL"], top_k=3)
        self.assertTrue(keywords)


class LocalPipelineTests(unittest.TestCase):
    def test_cpu_settings_are_conservative(self) -> None:
        settings = CPUSettings()
        self.assertEqual(settings.threads, 1)
        self.assertEqual(settings.n_process, 1)
        with self.assertRaises(ValueError):
            CPUSettings(threads=0)

    def test_regex_segmentation_needs_no_optional_dependency(self) -> None:
        result = LocalKnowledgePipeline.segment("NPL Ratio 1.85% 風險", backend="regex")
        self.assertIn("NPL", result)
        self.assertIn("1.85", result)
        self.assertIn("風險", result)

    def test_library_status_has_exactly_ten_entries(self) -> None:
        status = library_status()
        self.assertEqual(len(status), 10)
        self.assertEqual({item["requirement"] for item in status}, {"required", "optional"})

    def test_end_to_end_pipeline_when_local_model_is_available(self) -> None:
        try:
            pipeline = LocalKnowledgePipeline()
        except RuntimeError as exc:
            raise unittest.SkipTest(str(exc))
        result = pipeline.analyze("受房地產市場波動影響，NPL Ratio 攀升至 1.85%。")
        self.assertEqual(result["normalized_text"], "受房地產市場波動影響,NPL Ratio 攀升至 1.85%。")
        self.assertTrue(result["parsed"]["entities"])
        self.assertTrue(result["triples"])
        self.assertIn("nodes", result["graph"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
