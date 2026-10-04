from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from via_nlp_engine.bundle_ops import read_document_bundle
from via_nlp_engine.instruction_ops import InstructionReconstructor
from via_nlp_engine.knowledge import KnowledgeBuilder
from via_nlp_engine.mindmap_evolution import build_mind_map_evolution, load_previous_reconstruction
from via_nlp_engine.text_ops import TextProcessor


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEXICON_PATH = PROJECT_ROOT / "data" / "lexicon" / "ssot_lexicon.json"
GOVERNANCE_PATH = PROJECT_ROOT / "config" / "governance.json"


class V14ReconstructionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.builder = KnowledgeBuilder(TextProcessor(LEXICON_PATH), GOVERNANCE_PATH)

    def test_fragmented_command_reconstruction_is_balanced_and_never_executed(self) -> None:
        text = """User: 前置條件：必須先安裝 Python。
Assistant: 接著執行重建。
```powershell
python -m via_nlp_engine `
  health
```
User: 最後測試輸出是否包含 Mind Map。
"""
        result = self.builder.knowledge(text)["instruction_reconstruction"]
        self.assertEqual(result["schema"], "VIA_INSTRUCTION_RECONSTRUCTION/1.0")
        self.assertEqual(result["statistics"]["command_count"], 1)
        command = result["command_units"][0]
        self.assertEqual(command["verbatim_lines"], ["python -m via_nlp_engine `", "  health"])
        self.assertTrue(command["completeness"]["continuation_balanced"])
        self.assertFalse(command["execution_authorized"])
        self.assertFalse(result["quality_gates"]["command_execution_authorized"])

    def test_incomplete_command_fails_closed(self) -> None:
        reconstructor = InstructionReconstructor()
        result = reconstructor.build(
            [{"segment_id": "SEG-000001", "sha256": "a"}],
            [{"segment_id": "SEG-000001", "semantic_units": []}],
            [
                {
                    "code_id": "CODE-00001",
                    "language": "powershell",
                    "code": "python -m via_nlp_engine `",
                    "source_segments": ["SEG-000001"],
                    "source_span": {"start": 0, "end": 30},
                }
            ],
            "python -m via_nlp_engine `",
        )
        self.assertEqual(result["statistics"]["incomplete_commands"], 1)
        self.assertEqual(result["command_units"][0]["confidence"], 0.45)
        self.assertFalse(result["quality_gates"]["command_execution_authorized"])

    def test_bilingual_mind_map_has_two_human_views_and_honest_fallback(self) -> None:
        result = self.builder.knowledge("User: 建立知識體 (Knowledge Body) 與動態心智圖。")
        mind_map = result["mind_map"]
        self.assertEqual(mind_map["format"], "VIA_MIND_MAP_JSON/3.0")
        self.assertIn("zh", mind_map["human_view"])
        self.assertIn("en", mind_map["human_view"])
        self.assertTrue(mind_map["bilingual_contract"]["structural_labels_complete"])
        self.assertFalse(mind_map["bilingual_contract"]["automatic_fabricated_translation"])
        self.assertTrue(all("bilingual_label" in node for node in mind_map["ai_view"]["nodes"]))

    def test_bilingual_knowledge_body_links_instructions_topics_and_code(self) -> None:
        result = self.builder.knowledge(
            "User: 必須重建知識體。\n```python\ndef run(text):\n    return text\n```\n"
        )
        body = result["bilingual_knowledge_body"]
        self.assertEqual(body["schema"], "VIA_BILINGUAL_KNOWLEDGE_BODY/1.0")
        self.assertEqual(body["languages"], ["zh", "en"])
        self.assertTrue(body["instruction_ids"])
        self.assertTrue(body["code_family_ids"])
        self.assertTrue(body["topics"])

    def test_dynamic_mind_map_is_versioned_and_never_silently_deletes(self) -> None:
        first = self.builder.knowledge("User: 必須保留不可變來源。")
        second = self.builder.knowledge("User: 必須保留不可變來源。\nAssistant: 新增驗證步驟。")
        previous = {
            "mind_map": first["mind_map"],
            "mind_map_evolution": first["mind_map_evolution"],
        }
        evolution = build_mind_map_evolution(
            second["mind_map"],
            previous=previous,
            conflict_register=second["knowledge_object_registry"]["conflict_register"],
        )
        self.assertEqual(evolution["version"]["sequence"], 2)
        self.assertEqual(evolution["version"]["chain_status"], "linked_to_previous_snapshot")
        self.assertTrue(evolution["delta"]["nodes"]["added"])
        self.assertFalse(evolution["quality_gates"]["silent_node_deletion"])
        self.assertTrue(
            all(
                not item["applied_to_previous_snapshot"]
                for item in evolution["correction_proposals"]
            )
        )

    def test_source_record_identity_is_stable_when_an_earlier_file_is_added(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            original = root / "b.md"
            original.write_text("User: 保留來源。", encoding="utf-8")
            first = read_document_bundle([original])
            original_id = first["source_record_ledger"][0]["record_id"]
            (root / "a.md").write_text("User: 新增資料。", encoding="utf-8")
            second = read_document_bundle([root])
            retained = next(item for item in second["source_record_ledger"] if item["source_name"] == "b.md")
            self.assertEqual(retained["record_id"], original_id)
            self.assertEqual(retained["source_order"], 2)

    def test_previous_full_package_loader_rejects_unknown_shape(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            invalid = Path(temp) / "invalid.json"
            invalid.write_text('{"schema":"unknown"}', encoding="utf-8")
            with self.assertRaises(ValueError):
                load_previous_reconstruction(invalid)


if __name__ == "__main__":
    unittest.main()
