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
        self.assertEqual(result["mind_map"]["format"], "VIA_MIND_MAP_JSON/3.0")
        self.assertEqual(result["mind_map"]["ai_view"]["schema"], "VIA_KNOWLEDGE_GRAPH/3.0")
        self.assertGreaterEqual(len(result["body_of_knowledge"]["topics"]), 2)
        self.assertEqual(result["dialogue_flow"]["metrics"]["topic_returns"], 1)
        self.assertEqual(result["completeness"]["refined_segment_coverage"], 1.0)
        self.assertEqual(result["code_registry"][0]["language"], "python")
        self.assertEqual(result["code_registry"][0]["syntax"]["status"], "valid")
        self.assertEqual(result["code_registry"][0]["engine_spec"]["parameters"]["MAX_BATCH"], 32)
        self.assertEqual(result["code_integration_blueprint"]["parameters"]["MAX_BATCH"], 32)
        self.assertEqual(result["code_integration_blueprint"]["schema"], "VIA_ENGINE_BLUEPRINT/3.0")
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

    def test_ticker_anchor_returns_without_cross_company_merge(self) -> None:
        text = """User: 台積電 2330 討論先進製程與營收。
Assistant: 鴻海 2317 討論伺服器組裝與出貨。
User: 回到台積電 2330，繼續討論先進製程。
"""
        result = self.builder.reorganize(text)
        labels = {
            segment_id: topic["topic_id"]
            for topic in result["body_of_knowledge"]["topics"]
            for segment_id in topic["segment_ids"]
        }
        self.assertEqual(labels["SEG-000001"], labels["SEG-000003"])
        self.assertNotEqual(labels["SEG-000001"], labels["SEG-000002"])
        self.assertEqual(result["dialogue_flow"]["metrics"]["topic_returns"], 1)
        link = result["dialogue_flow"]["return_links"][0]
        self.assertEqual(link["previous_segment"], "SEG-000001")
        self.assertIn("ticker:2330", link["anchor_evidence"])

    def test_fact_integrity_fails_closed_to_source(self) -> None:
        class MutatingProcessor(TextProcessor):
            def repair(self, text: str):
                output = super().repair(text)
                output["repaired_text"] = output["repaired_text"].replace("2330", "2317")
                return output

        builder = KnowledgeBuilder(MutatingProcessor(LEXICON_PATH), GOVERNANCE_PATH)
        result = builder.reorganize("User: 台積電 2330 目標價為 NT$1,000。")
        refined = result["refinement_ledger"][0]
        self.assertEqual(refined["optimized_text"], result["source_ledger"][0]["text"])
        self.assertEqual(refined["fact_integrity"]["status"], "failed_closed")
        self.assertEqual(refined["fact_integrity"]["fallback"], "source_text_restored")
        self.assertEqual(result["quality_gates"]["fact_integrity"], "pass_with_source_fallback")

    def test_structured_table_is_verbatim_and_graph_linked(self) -> None:
        text = """# 財務摘要
| 年度 | EPS | 目標價 |
|---|---:|---:|
| 2025 | 12.5 | 800 |
| 2026 | 15.0 | 950 |
"""
        result = self.builder.knowledge(text)
        tables = result["body_of_knowledge"]["structured_tables"]
        self.assertEqual(len(tables), 1)
        self.assertEqual(tables[0]["headers"], ["年度", "EPS", "目標價"])
        self.assertEqual(tables[0]["rows"][0], ["2025", "12.5", "800"])
        self.assertEqual(tables[0]["cell_policy"], "verbatim_only_no_silent_fill")
        table_nodes = [
            item for item in result["mind_map"]["ai_view"]["nodes"] if item["node_type"] == "structured_table"
        ]
        self.assertEqual(len(table_nodes), 1)
        self.assertFalse(result["quality_gates"]["silent_table_fill"])

    def test_discussion_registry_deduplicates_and_exposes_parameter_conflict(self) -> None:
        text = """User: 決定採用 MAX_BATCH = 32。
Assistant: 請保留逐字來源與雜湊。
User: 決定採用 MAX_BATCH = 32。
User: 更新為 MAX_BATCH = 64，以此為準。
"""
        result = self.builder.knowledge(text)
        registry = result["knowledge_object_registry"]
        self.assertEqual(registry["schema"], "VIA_KNOWLEDGE_OBJECT_REGISTRY/1.0")
        self.assertGreaterEqual(registry["statistics"]["collapsed_duplicate_occurrences"], 1)
        self.assertIn("MAX_BATCH", registry["parameter_register"])
        conflict = registry["conflict_register"][0]
        self.assertEqual(conflict["parameter"], "MAX_BATCH")
        self.assertEqual(conflict["status"], "explicit_supersession_review")
        self.assertEqual(conflict["resolution"], "human_required")
        self.assertTrue(registry["supersession_links"])
        self.assertFalse(registry["quality_gates"]["automatic_supersession"])
        unit_nodes = [
            item for item in result["mind_map"]["ai_view"]["nodes"] if item["node_type"] == "knowledge_unit"
        ]
        self.assertTrue(unit_nodes)

    def test_code_revision_families_and_interface_graph(self) -> None:
        text = """```python
def load_data(path: str) -> str:
    return path
```
```python
def load_data(path: str) -> str:
    return path
```
```python
def load_data(path: str) -> str:
    return path.strip()
```
```python
def run(path: str) -> str:
    return load_data(path)
```
"""
        result = self.builder.knowledge(text)
        package = result["code_reconstruction_package"]
        self.assertEqual(package["schema"], "VIA_CODE_RECONSTRUCTION/3.0")
        load_family = next(item for item in package["families"] if "load_data" in item["signature"])
        self.assertEqual(load_family["revision_count"], 3)
        self.assertEqual(load_family["distinct_revision_count"], 2)
        self.assertEqual(load_family["exact_duplicate_count"], 1)
        self.assertFalse(load_family["candidate_applied"])
        self.assertTrue(package["interface_graph"]["edges"])
        blueprint = result["code_integration_blueprint"]
        self.assertEqual(blueprint["schema"], "VIA_ENGINE_BLUEPRINT/3.0")
        self.assertTrue(blueprint["dependency_graph"]["topology_complete"])
        self.assertFalse(blueprint["automatic_revision_merge"])
        family_nodes = [
            item for item in result["mind_map"]["ai_view"]["nodes"] if item["node_type"] == "code_family"
        ]
        self.assertEqual(len(family_nodes), 2)

    def test_additional_programming_languages_are_statically_reconstructed(self) -> None:
        text = """```sql
SELECT ticker, close FROM prices WHERE date >= :start_date;
```
```html
<div id="app">Dashboard</div>
```
```css
:root { --brand-red: #a11; }
```
```yaml
engine: via_nlp
offline: true
```
```toml
name = "via_nlp"
version = "1.3.0"
```
```bash
#!/usr/bin/env bash
run_engine() {
  python -m via_nlp_engine
}
```
"""
        result = self.builder.knowledge(text)
        languages = {item["language"] for item in result["code_registry"]}
        self.assertTrue({"sql", "html", "css", "yaml", "toml", "bash"}.issubset(languages))
        sql = next(item for item in result["code_registry"] if item["language"] == "sql")
        self.assertEqual(sql["engine_spec"]["reads"], ["prices"])
        self.assertIn("start_date", sql["engine_spec"]["parameters"])
        self.assertTrue(all(item["execution_policy"] == "never_execute_from_untrusted_text" for item in result["code_registry"]))


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
