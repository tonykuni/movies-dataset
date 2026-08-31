from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from via_nlp_engine.learning import FeedbackStore, GovernedClassifier, SKLEARN_AVAILABLE
from via_nlp_engine.schemas import FeedbackRecord


@unittest.skipUnless(SKLEARN_AVAILABLE, "scikit-learn is optional")
class GovernedMLTests(unittest.TestCase):
    def test_candidate_training_and_integrity_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            store = FeedbackStore(root / "feedback.sqlite3")
            config = {
                "enabled": True,
                "classes": ["finance", "technology", "operations", "general"],
                "n_features": 4096,
                "random_state": 42,
                "candidate_min_samples": 24,
                "validation_fraction": 0.25,
                "min_macro_f1": 0.0,
                "max_regression": 1.0,
                "auto_promote": False,
                "linear_epochs": 2,
                "training_batch_size": 16,
                "neural_challenger_enabled": True,
                "neural_min_samples": 24,
                "neural_n_features": 256,
                "neural_hidden_layers": [16, 8],
                "neural_max_iter": 20,
                "max_duplicate_ratio": 0.35,
                "candidate_retention": 2,
            }
            phrases = {
                "finance": "股票 營收 市場 投資",
                "technology": "軟體 模型 API 資料庫",
                "operations": "專案 流程 交付 排程",
                "general": "一般 文章 內容 說明",
            }
            counter = 0
            for label, phrase in phrases.items():
                for index in range(10):
                    counter += 1
                    store.add(
                        FeedbackRecord(
                            request_id=f"r{counter}", task="classify", text=f"{phrase} {index}", corrected_label=label
                        )
                    )
            classifier = GovernedClassifier(root / "models", config, store)
            self.assertEqual(classifier.fingerprint(), "rules_only")
            report = classifier.evolve(promote=True)
            self.assertEqual(report["status"], "promoted")
            self.assertEqual({item["backend"] for item in report["challengers"]}, {"linear_sgd", "tiny_neural_cpu"})
            self.assertTrue(classifier.status()["active_model"])
            self.assertEqual(classifier.fingerprint(), report["candidate_sha256"])
            prediction = classifier.predict("股票市場與公司營收")
            self.assertIsNotNone(prediction)
            store.close()

    def test_conflicting_labels_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            store = FeedbackStore(root / "feedback.sqlite3")
            config = {
                "enabled": True,
                "classes": ["finance", "technology"],
                "n_features": 256,
                "random_state": 42,
                "candidate_min_samples": 4,
                "validation_fraction": 0.25,
                "min_macro_f1": 0.0,
                "max_regression": 1.0,
                "auto_promote": False,
                "max_duplicate_ratio": 1.0,
            }
            samples = [
                ("同一段文字", "finance"),
                (" 同一段文字 ", "technology"),
                ("股票市場", "finance"),
                ("軟體模型", "technology"),
            ]
            for index, (text, label) in enumerate(samples):
                store.add(FeedbackRecord(request_id=f"c{index}", task="classify", text=text, corrected_label=label))
            report = GovernedClassifier(root / "models", config, store).evolve(promote=True)
            self.assertEqual(report["status"], "rejected")
            self.assertIn("Conflicting labels", report["reason"])
            store.close()


if __name__ == "__main__":
    unittest.main()
