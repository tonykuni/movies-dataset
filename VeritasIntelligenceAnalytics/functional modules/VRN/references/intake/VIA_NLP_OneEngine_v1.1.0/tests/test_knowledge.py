from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from via_nlp_engine.knowledge import KnowledgeBuilder
from via_nlp_engine.text_ops import TextProcessor
from via_nlp_engine.translation import TranslationMemory, TranslationService


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEXICON_PATH = PROJECT_ROOT / "data" / "lexicon" / "ssot_lexicon.json"
GOVERNANCE_PATH = PROJECT_ROOT / "config" / "governance.json"


JUMPY_TEXT = """17:05 Tony
今天先談股票市場與資金流。
18:32 Alice
突然切換到 NLP 與自然語言處理 (Natural Language Processing)。
## 程式規格
```python
MAX_BATCH = 32
def run_engine(text):
    return text
```
19:10 Tony
回到大盤與 ETF，SSOT 必須保留來源。
"""


class KnowledgeTests(unittest.TestCase):
    def setUp(self) -> None:
        processor = TextProcessor(LEXICON_PATH)
        self.builder = KnowledgeBuilder(processor, GOVERNANCE_PATH)

    def test_lossless_reorganization_and_mind_map(self) -> None:
        result = self.builder.reorganize(JUMPY_TEXT)
        self.assertTrue(result["completeness"]["exact_reconstruction"])
        reconstructed = "".join(item["text"] for item in result["source_ledger"])
        self.assertEqual(reconstructed, JUMPY_TEXT)
        self.assertEqual(result["mind_map"]["format"], "VIA_MIND_MAP_JSON/2.0")
        self.assertEqual(result["mind_map"]["ai_view"]["schema"], "VIA_KNOWLEDGE_GRAPH/2.0")
        self.assertGreaterEqual(len(result["body_of_knowledge"]["topics"]), 2)
        self.assertEqual(result["dialogue_flow"]["metrics"]["topic_returns"], 1)
        self.assertEqual(result["completeness"]["refined_segment_coverage"], 1.0)
        self.assertEqual(result["code_registry"][0]["language"], "python")
        self.assertEqual(result["code_registry"][0]["syntax"]["status"], "valid")
        self.assertEqual(result["code_registry"][0]["engine_spec"]["parameters"]["MAX_BATCH"], 32)
        self.assertEqual(result["code_integration_blueprint"]["parameters"]["MAX_BATCH"], 32)
        self.assertEqual(result["code_integration_blueprint"]["schema"], "VIA_ENGINE_BLUEPRINT/2.0")
        self.assertEqual(result["code_integration_blueprint"]["interface_contracts"][0]["arguments"][0]["name"], "text")
        self.assertFalse(result["code_integration_blueprint"]["execution_authorized"])
        covered = {segment_id for section in result["body_of_knowledge"]["organized_sections"] for segment_id in section["segment_ids"]}
        self.assertEqual(covered, {item["segment_id"] for item in result["source_ledger"]})

    def test_optional_deep_semantic_edges_do_not_persist_vectors(self) -> None:
        result = self.builder.knowledge(JUMPY_TEXT)
        vectors = [[1.0, 0.0] for _ in result["body_of_knowledge"]["topics"]]
        enriched = self.builder.enrich_semantic_graph(result, vectors, threshold=0.9)
        semantic = enriched["mind_map"]["ai_view"]["semantic_enrichment"]
        self.assertTrue(semantic["deep_model_loaded"])
        self.assertFalse(semantic["vectors_persisted"])
        self.assertTrue(any(item["relation"] == "deep_semantic_related" for item in enriched["mind_map"]["ai_view"]["edges"]))

    def test_code_blueprint_builds_dependency_topology(self) -> None:
        text = """```python
def helper(value: str) -> str:
    return value.strip()
```
```python
def run(value: str) -> str:
    return helper(value)
```
"""
        result = self.builder.knowledge(text)["code_integration_blueprint"]
        self.assertTrue(result["dependency_graph"]["topology_complete"])
        self.assertEqual(result["dependency_graph"]["topological_order"], ["CODE-00001", "CODE-00002"])
        self.assertEqual(result["dependency_graph"]["edges"][0]["symbol"], "helper")

    def test_ssot_candidates_and_via_keywords(self) -> None:
        result = self.builder.knowledge(JUMPY_TEXT)
        canonicals = {item["canonical"] for item in result["ssot_dictionary"]["entries"]}
        self.assertIn("Natural Language Processing", canonicals)
        keywords = {item["keyword"].lower() for item in result["via_keywords"]}
        self.assertIn("ssot", keywords)

    def test_governance_is_three_round_and_never_executes_code(self) -> None:
        text = """# Unsafe candidate
```python
def broken(:
    pass
```
"""
        result = self.builder.govern(text)
        self.assertEqual(len(result["rounds"]), 3)
        self.assertEqual(len(result["pipelines"]), 6)
        self.assertTrue(result["issues"])
        self.assertFalse(result["governance_policy"]["non_negotiable"]["execute_extracted_code"])


class TranslationTests(unittest.TestCase):
    def test_chunked_translation_memory_and_code_preservation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            memory = TranslationMemory(Path(temp) / "translation.sqlite3")
            config = {
                "enabled": True,
                "default_backend": "ollama",
                "source_language": "zh",
                "target_language": "en",
                "max_chunk_chars": 100,
                "preserve_code": True,
                "google_cloud_location": "global",
                "google_cloud_project_env": "GOOGLE_CLOUD_PROJECT",
            }
            service = TranslationService(config, memory)
            calls: list[str] = []

            def provider(value: str, source: str, target: str) -> str:
                calls.append(value)
                return f"[{source}->{target}]{value.strip()}"

            text = "第一段中文。\n```python\nprint('不翻譯')\n```\n第二段中文。"
            first = service.translate(text, backend="ollama", ollama_provider=provider)
            second = service.translate(text, backend="ollama", ollama_provider=provider)
            self.assertTrue(first["completeness"]["exact_source_reconstruction"])
            self.assertIn("print('不翻譯')", first["translated_text"])
            self.assertIn("。\n```python", first["translated_text"])
            self.assertIn("```\n", first["translated_text"])
            self.assertTrue(any(item["status"] == "preserved_code" for item in first["chunks"]))
            self.assertTrue(any(item["cache_hit"] for item in second["chunks"] if item["status"] == "translated"))
            self.assertEqual(len(calls), sum(item["status"] == "translated" for item in first["chunks"]))
            memory.close()

    def test_google_web_backend_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            memory = TranslationMemory(Path(temp) / "translation.sqlite3")
            config = {
                "enabled": True,
                "default_backend": "argos",
                "source_language": "zh",
                "target_language": "en",
                "max_chunk_chars": 4500,
                "preserve_code": True,
                "google_cloud_location": "global",
                "google_cloud_project_env": "GOOGLE_CLOUD_PROJECT",
            }
            service = TranslationService(config, memory)
            with self.assertRaises(RuntimeError):
                service.translate("測試", backend="google_web")
            memory.close()


if __name__ == "__main__":
    unittest.main()
