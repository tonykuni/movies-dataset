import json
import tempfile
import unittest
from pathlib import Path

from VUSIPE import (
    CONTRACT, SUPPORTED_ACTIONS, UniversalSemanticPlugin, capability_manifest,
    cosine, detect_language, embed_text, evaluate_model, extract_actions, extract_entities,
    extract_keywords, hashed_embedding, invoke_json, normalize_text,
    run_self_test, segment_text, summarize_text, train_linear_model,
)


class VUSIPETests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.plugin = UniversalSemanticPlugin(self.temp.name)

    def tearDown(self):
        self.plugin.close()
        self.temp.cleanup()

    def test_manifest(self):
        data = capability_manifest()
        self.assertEqual(data["contract"], CONTRACT)
        self.assertTrue(data["cpu_only"])
        self.assertEqual(set(data["actions"]), set(SUPPORTED_ACTIONS))

    def test_normalize(self):
        self.assertEqual(normalize_text(" a  b\r\n\r\nc "), "a b\nc")

    def test_language(self):
        self.assertEqual(detect_language("中文 English"), "multilingual")

    def test_segments(self):
        self.assertGreaterEqual(len(segment_text("第一句。 第二句。", 5)), 2)

    def test_keywords(self):
        self.assertTrue(extract_keywords("股票 股票 成交量", 3))

    def test_entities(self):
        entities = extract_entities("2330.TW 2026-08-31 a@b.com report.md")
        types = {row["type"] for row in entities}
        self.assertTrue({"TICKER", "DATE", "EMAIL", "FILE"} <= types)
        self.assertFalse(any(row["type"] == "TICKER" and row["value"] == "2026" for row in entities))

    def test_actions(self):
        self.assertEqual(len(extract_actions("必須更新報告。 一般說明。")), 1)

    def test_summary(self):
        self.assertTrue(summarize_text("股票上漲。成交量增加。一般句子。", 2))

    def test_embedding(self):
        vector = hashed_embedding("台股分析")
        self.assertEqual(len(vector), 256)
        self.assertAlmostEqual(cosine(vector, vector), 1.0, places=5)

    def test_tiny_neural_cpu_embedding(self):
        result = embed_text("台股分析", "tiny-neural-cpu")
        self.assertEqual(result["dimension"], 64)
        self.assertTrue(result["cpu_only"])

    def test_similarity_action(self):
        result = self.plugin.invoke({"action": "similarity", "payload": {"left": "台股成交量", "right": "台股成交量", "embedding_backend": "tiny-neural-cpu"}})
        self.assertEqual(result["gate"], "PASS")
        self.assertAlmostEqual(result["result"]["score"], 1.0, places=5)

    def test_inline_analysis(self):
        result = self.plugin.invoke({"action": "analyze", "payload": {"text": "必須分析 2330.TW。"}})
        self.assertEqual(result["gate"], "PASS")
        self.assertFalse(result["source_mutated"])

    def test_file_source_read_only(self):
        path = Path(self.temp.name) / "source.md"
        path.write_text("必須更新。", encoding="utf-8")
        before = path.read_bytes()
        result = self.plugin.invoke({"action": "analyze", "payload": {"path": str(path)}})
        self.assertEqual(result["gate"], "PASS")
        self.assertEqual(path.read_bytes(), before)

    def test_all_projection_actions(self):
        for action in ("normalize", "segment", "keywords", "entities", "relations", "summarize", "actions", "embed", "classify", "retrieve"):
            result = self.plugin.invoke({"action": action, "payload": {"text": "必須分析 2330.TW。"}})
            self.assertEqual(result["gate"], "PASS", action)

    def test_unsupported_fail_closed(self):
        self.assertEqual(self.plugin.invoke({"action": "delete", "payload": {}})["gate"], "FAIL")

    def test_knowledge_append_and_dedup(self):
        request = {"action": "knowledge_upsert", "payload": {"title": "A", "text": "台股成交量"}}
        self.assertEqual(self.plugin.invoke(request)["status"], "APPENDED")
        self.assertEqual(self.plugin.invoke(request)["status"], "SKIP_DUPLICATE")

    def test_knowledge_search(self):
        self.plugin.invoke({"action": "knowledge_upsert", "payload": {"title": "A", "text": "台股成交量"}})
        result = self.plugin.invoke({"action": "knowledge_search", "payload": {"query": "台股"}})
        self.assertEqual(len(result["results"]), 1)

    def test_feedback_append(self):
        result = self.plugin.invoke({"action": "feedback", "payload": {"text": "股票", "predicted": "x", "expected": "finance"}})
        self.assertTrue(result["append_only"])

    def test_model_training(self):
        samples = [{"text": "股票成交量", "label": "finance"}, {"text": "Python API", "label": "software"}]
        model = train_linear_model(samples, epochs=5)
        self.assertEqual(set(model.labels), {"finance", "software"})
        self.assertEqual(evaluate_model(model, samples)["gate"], "PASS")

    def test_train_candidate_only(self):
        samples = [{"text": "股票成交量", "label": "finance"}, {"text": "Python API", "label": "software"}]
        result = self.plugin.invoke({"action": "train", "payload": {"samples": samples}})
        self.assertFalse(result["promoted"])

    def test_evolve_requires_explicit_promotion(self):
        samples = [{"text": "股票成交量", "label": "finance"}, {"text": "Python API", "label": "software"}]
        result = self.plugin.invoke({"action": "evolve", "payload": {"samples": samples}})
        self.assertFalse(result["promoted"])

    def test_evolve_promotes_runtime_only(self):
        samples = [{"text": "股票成交量", "label": "finance"}, {"text": "Python API", "label": "software"}]
        result = self.plugin.invoke({"action": "evolve", "payload": {"samples": samples, "approve_runtime_promotion": True}})
        self.assertTrue(result["promoted"])
        self.assertEqual(result["promotion"]["scope"], "VUSIPE_RUNTIME_ONLY")

    def test_feedback_can_train(self):
        self.plugin.invoke({"action": "feedback", "payload": {"text": "股票", "predicted": "x", "expected": "finance"}})
        self.plugin.invoke({"action": "feedback", "payload": {"text": "Python", "predicted": "x", "expected": "software"}})
        self.assertEqual(self.plugin.invoke({"action": "train", "payload": {}})["gate"], "PASS")

    def test_empty_training_holds(self):
        self.assertEqual(self.plugin.invoke({"action": "train", "payload": {}})["gate"], "HOLD")

    def test_invoke_json_adapter(self):
        raw = invoke_json(json.dumps({"action": "health", "payload": {}}), self.temp.name)
        self.assertEqual(json.loads(raw)["status"], "READY")

    def test_self_test(self):
        self.assertEqual(run_self_test()["gate"], "PASS")


if __name__ == "__main__":
    unittest.main()
