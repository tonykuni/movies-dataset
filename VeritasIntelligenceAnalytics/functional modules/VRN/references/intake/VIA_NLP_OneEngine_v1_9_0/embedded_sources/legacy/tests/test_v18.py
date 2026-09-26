from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from via_nlp_engine.engine import VIAEngine
from via_nlp_engine.bundle_ops import _write_deterministic_zip
from via_nlp_engine.knowledge import KnowledgeBuilder
from via_nlp_engine.summarization import SUMMARY_SCHEMA
from via_nlp_engine.text_ops import TextProcessor


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEXICON_PATH = PROJECT_ROOT / "data" / "lexicon" / "ssot_lexicon.json"
GOVERNANCE_PATH = PROJECT_ROOT / "config" / "governance.json"
CONFIG_PATH = PROJECT_ROOT / "config" / "default.json"


class V18EvidenceSummarizerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.processor = TextProcessor(LEXICON_PATH)

    def test_backward_contract_is_preserved_additively(self) -> None:
        result = self.processor.summarize_complete("第一點。\nSecond point.")
        self.assertTrue({"summary", "key_points", "backend", "chunks", "coverage"}.issubset(result))
        self.assertEqual(result["schema"], SUMMARY_SCHEMA)
        self.assertIn("evidence_points", result)
        self.assertIn("quality", result)

    def test_every_point_has_exact_span_and_hash(self) -> None:
        text = "結論：營收成長 20%。\nRisk: demand may decline.\n建議：持續監測。"
        result = self.processor.summarize_complete(text, max_points=6)
        for point in result["evidence_points"]:
            span = point["source_span"]
            source_text = text[span["start"]:span["end"]]
            self.assertEqual(source_text, point["source_text"])
            self.assertEqual(
                hashlib.sha256(source_text.encode("utf-8")).hexdigest(),
                point["source_sha256"],
            )
        self.assertTrue(result["quality"]["evidence_spans_valid"])
        self.assertTrue(result["quality"]["evidence_hashes_valid"])

    def test_long_unpunctuated_input_produces_bounded_points(self) -> None:
        text = ("中英混合NLP資料與parameter123 " * 1200).strip()
        result = self.processor.summarize_complete(
            text,
            max_points=8,
            max_chunk_chars=2000,
            max_unit_chars=300,
        )
        self.assertTrue(result["coverage"]["all_input_consumed"])
        self.assertLessEqual(result["quality"]["max_observed_point_characters"], 300)
        self.assertTrue(result["quality"]["key_points_bounded"])

    def test_each_eligible_chunk_is_represented_when_budget_allows(self) -> None:
        text = "".join(
            f"Chunk section {index}: 結論 {index} 的營收成長 {index}%。\n" + ("x" * 1150) + "\n"
            for index in range(5)
        )
        result = self.processor.summarize_complete(
            text,
            max_points=10,
            max_chunk_chars=1400,
            max_unit_chars=500,
        )
        self.assertGreater(result["coverage"]["chunk_count"], 2)
        self.assertEqual(
            result["quality"]["eligible_chunks"],
            result["quality"]["represented_chunks"],
        )
        self.assertTrue(result["quality"]["all_eligible_chunks_represented_when_budget_allows"])

    def test_repeated_units_are_not_repeated_in_summary(self) -> None:
        text = ("結論：保留完整資料。\n" * 30) + "風險：不可靜默刪除。\n"
        result = self.processor.summarize_complete(text, max_points=10)
        self.assertEqual(result["quality"]["duplicate_points"], 0)
        self.assertEqual(len(result["key_points"]), len(set(result["key_points"])))

    def test_output_is_deterministic(self) -> None:
        text = "結論 A。\n結論 B。\nRisk C.\n" * 40
        first = self.processor.summarize_complete(text, max_points=7, max_chunk_chars=1200)
        second = self.processor.summarize_complete(text, max_points=7, max_chunk_chars=1200)
        self.assertEqual(first, second)

    def test_atomic_package_cleans_only_its_stale_temporary_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source.json"
            source.write_text("{}\n", encoding="utf-8")
            archive = root / "result.zip"
            stale = root / ".result.zip.interrupted.tmp"
            unrelated = root / ".another.zip.interrupted.tmp"
            stale.write_bytes(b"partial")
            unrelated.write_bytes(b"keep")
            _write_deterministic_zip(archive, [source])
            self.assertTrue(archive.is_file())
            self.assertFalse(stale.exists())
            self.assertTrue(unrelated.exists())


class V18ContentAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        processor = TextProcessor(LEXICON_PATH)
        self.builder = KnowledgeBuilder(
            processor,
            GOVERNANCE_PATH,
            {"cpu_tools": {"use_available_providers": False}},
        )

    def test_region_transitions_and_exclusion_policy_are_auditable(self) -> None:
        text = (
            "HTML\nMD+1\n本文區(修復)\n結論：保留完整資料。\n"
            "右資訊區\n延伸閱讀\n"
        )
        result = self.builder.knowledge(text)["content_role_analysis"]
        reasons = {item["reason"] for item in result["section_transitions"]}
        self.assertIn("explicit_main_region", reasons)
        self.assertIn("explicit_sidebar_region", reasons)
        self.assertEqual(
            result["classification_policy"]["uncertain_content_default"],
            "include_and_review",
        )
        self.assertGreater(result["statistics"]["high_confidence_excluded_blocks"], 0)
        self.assertTrue(result["quality_gates"]["summary_evidence_integrity"])
        self.assertTrue(result["quality_gates"]["summary_points_bounded"])

    def test_full_and_body_summaries_have_evidence_contracts(self) -> None:
        text = "# Report\n本文營收增加 12%。\n首頁\n廣告：立即訂閱\n"
        result = self.builder.knowledge(text)["content_role_analysis"]
        summaries = result["summarizer"]
        self.assertEqual(summaries["body_summary"]["schema"], SUMMARY_SCHEMA)
        self.assertEqual(summaries["full_input_summary"]["schema"], SUMMARY_SCHEMA)
        self.assertNotIn("立即訂閱", summaries["body_summary"]["summary"])
        self.assertIn("立即訂閱", result["non_body_register"][1]["source_text"])

    def test_engine_advertises_v18_evidence_summarizer(self) -> None:
        with VIAEngine(
            config_path=CONFIG_PATH,
            overrides={"knowledge": {"cpu_tools": {"use_available_providers": False}}},
            auto_start=False,
        ) as engine:
            health = engine.health()
        self.assertEqual(health["engine"]["version"], "1.8.0")
        self.assertEqual(health["capabilities"]["evidence_summarizer_schema"], SUMMARY_SCHEMA)
        nlp_core = next(
            item for item in health["system_manager"]["modules"]
            if item["module_id"] == "NLP-CORE"
        )
        self.assertIn("evidence_summarizer", nlp_core["bound_operations"])


if __name__ == "__main__":
    unittest.main()
