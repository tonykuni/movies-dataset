from __future__ import annotations

import unittest
from pathlib import Path

from via_nlp_engine.evaluation import TopicThresholdCalibrator, bcubed_scores, precision_recall_f1
from via_nlp_engine.knowledge import LosslessSegmenter
from via_nlp_engine.text_ops import TextProcessor


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEXICON_PATH = PROJECT_ROOT / "data" / "lexicon" / "ssot_lexicon.json"


class QualityMetricTests(unittest.TestCase):
    def test_bcubed_perfect_and_split_penalty(self) -> None:
        expected = {"S1": "A", "S2": "B", "S3": "A"}
        perfect = bcubed_scores({"S1": "X", "S2": "Y", "S3": "X"}, expected)
        split = bcubed_scores({"S1": "X", "S2": "Y", "S3": "Z"}, expected)
        self.assertEqual(perfect["f1"], 1.0)
        self.assertLess(split["f1"], 1.0)

    def test_precision_recall_f1(self) -> None:
        metrics = precision_recall_f1({("S1", "S3"), ("S2", "S4")}, {("S1", "S3")})
        self.assertEqual(metrics, {"precision": 0.5, "recall": 1.0, "f1": 0.666667})

    def test_calibration_is_candidate_only(self) -> None:
        text = """User: 台積電 2330 討論先進製程。
Assistant: 鴻海 2317 討論伺服器。
User: 回到台積電 2330 討論先進製程。
"""
        segments = LosslessSegmenter().segment(text)["segments"]
        case = {
            "segments": segments,
            "gold_topic_labels": {
                "SEG-000001": "TSMC",
                "SEG-000002": "HONHAI",
                "SEG-000003": "TSMC",
            },
            "gold_return_pairs": [("SEG-000001", "SEG-000003")],
        }
        calibrator = TopicThresholdCalibrator(
            TextProcessor(LEXICON_PATH),
            thresholds=(0.14, 0.18),
            merge_thresholds=(0.31, 0.38),
        )
        result = calibrator.calibrate([case])
        self.assertEqual(result["status"], "candidate_ready")
        self.assertFalse(result["automatic_apply"])
        self.assertEqual(result["promotion_gate"], "locked_test_and_human_approval_required")
        self.assertEqual(result["selected"]["mean_score"], 1.0)


if __name__ == "__main__":
    unittest.main()
