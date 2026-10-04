from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from via_nlp_engine import ProcessRequest, VIAEngine
from via_nlp_engine.audit import AuditLogger
from via_nlp_engine.ingest import read_local_document
from via_nlp_engine.jobs import JobQueue
from via_nlp_engine.text_ops import TextProcessor, chunk_text


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "config" / "default.json"
LEXICON_PATH = PROJECT_ROOT / "data" / "lexicon" / "ssot_lexicon.json"


class TextProcessorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.processor = TextProcessor(LEXICON_PATH)

    def test_repair_is_high_confidence_and_preserves_original(self) -> None:
        output = self.processor.repair("今天討論機械學習。。結果很好")
        self.assertEqual(output["original_text"], "今天討論機械學習。。結果很好")
        self.assertEqual(output["repaired_text"], "今天討論機器學習。結果很好。")
        self.assertFalse(output["semantic_rewrite_applied"])

    def test_any_article_scope_and_document_type(self) -> None:
        output = self.processor.analyze("記者今日報導，市場利率下降，股票成交量回升。")
        self.assertEqual(output["document_type"], "news")
        self.assertEqual(output["classification"]["label"], "finance")

    def test_mixed_language(self) -> None:
        self.assertEqual(self.processor.detect_language("台積電 revenue growth is strong"), "mixed")

    def test_entities_do_not_misclassify_year_as_ticker(self) -> None:
        entities = self.processor.entities("2330.TW 在 2026/08/27 上漲 10%。")
        values = {(item["text"], item["label"]) for item in entities}
        self.assertIn(("2330.TW", "TICKER"), values)
        self.assertIn(("2026/08/27", "DATE"), values)
        self.assertNotIn(("2026", "TICKER"), values)

    def test_chunk_text_overlap_and_termination(self) -> None:
        chunks = list(chunk_text("甲" * 1000, max_chars=200, overlap=20))
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(0 < len(item) <= 200 for item in chunks))


class EngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        overrides = {
            "engine": {"data_dir": self.temp.name, "max_concurrency": 1},
            "jobs": {"enabled": False},
            "cache": {"enabled": True},
        }
        self.engine = VIAEngine(CONFIG_PATH, overrides=overrides)

    def tearDown(self) -> None:
        self.engine.close()
        self.temp.cleanup()

    def test_auto_route_analyzes_general_article(self) -> None:
        result = self.engine.process(ProcessRequest(text="這是一篇一般文章，包含清楚的說明。"))
        self.assertEqual(result.task, "analyze")
        self.assertEqual(result.output["document_type"], "general_article")

    def test_cache_hit_on_second_identical_request(self) -> None:
        request = {"text": "市場營收成長。", "task": "keywords", "options": {"top_k": 3}}
        first = self.engine.process(request)
        second = self.engine.process(request)
        self.assertFalse(first.cache_hit)
        self.assertTrue(second.cache_hit)

    def test_batch_checkpoint_resume(self) -> None:
        requests = [{"text": "第一篇文章。", "task": "repair"}, {"text": "第二篇文章。", "task": "repair"}]
        first = self.engine.process_batch(requests, job_id="resume-test")
        second = self.engine.process_batch(requests, job_id="resume-test")
        self.assertEqual(first, second)

    def test_feedback_is_recorded_and_evolution_is_gated(self) -> None:
        saved = self.engine.submit_feedback(
            {"request_id": "r1", "task": "classify", "text": "股票上漲", "corrected_label": "finance"}
        )
        self.assertGreater(saved["feedback_id"], 0)
        report = self.engine.evolve(promote=True)
        self.assertEqual(report["status"], "insufficient_data")
        self.assertFalse(report["promoted"])

    def test_heavy_tier_is_opt_in(self) -> None:
        with self.assertRaises(RuntimeError):
            self.engine.process({"text": "semantic text", "task": "embed"})
        with self.assertRaises(RuntimeError):
            self.engine.process({"text": "跳題對話", "task": "knowledge", "quality": "deep"})

    def test_health_reports_any_article_scope(self) -> None:
        health = self.engine.health()
        self.assertEqual(health["capabilities"]["document_scope"], "any_article_or_text")
        self.assertEqual(health["capabilities"]["mind_map_schema"], "VIA_MIND_MAP_JSON/3.0")
        self.assertEqual(
            health["capabilities"]["instruction_reconstruction_schema"],
            "VIA_INSTRUCTION_RECONSTRUCTION/1.0",
        )
        self.assertEqual(
            health["capabilities"]["mind_map_evolution_schema"],
            "VIA_MIND_MAP_EVOLUTION/1.0",
        )
        self.assertTrue(health["audit"]["valid"])


class PersistenceTests(unittest.TestCase):
    def test_dashboard_contains_resource_and_article_controls(self) -> None:
        html = (PROJECT_ROOT / "dashboard" / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="ram"', html)
        self.assertIn('id="article"', html)
        self.assertIn('id="knowledge-summary"', html)
        self.assertIn("/v1/process", html)

    def test_audit_hash_chain_detects_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "audit.jsonl"
            audit = AuditLogger(path)
            audit.append("one", {"value": 1})
            audit.append("two", {"value": 2})
            self.assertTrue(audit.verify()["valid"])
            lines = path.read_text(encoding="utf-8").splitlines()
            record = json.loads(lines[0])
            record["payload"]["value"] = 999
            lines[0] = json.dumps(record)
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            self.assertFalse(audit.verify()["valid"])

    def test_queue_atomic_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            queue = JobQueue(Path(temp))
            job_id = queue.submit({"text": "文章", "task": "repair"})
            claimed = queue.claim_next()
            self.assertEqual(claimed["job_id"], job_id)
            queue.complete(job_id, {"ok": True})
            self.assertEqual(queue.status(job_id)["status"], "completed")

    def test_text_ingest_with_big5_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "article.txt"
            path.write_bytes("繁體中文文章".encode("big5"))
            value = read_local_document(path)
            self.assertEqual(value["text"], "繁體中文文章")
            self.assertEqual(value["metadata"]["encoding"], "big5")


if __name__ == "__main__":
    unittest.main()
