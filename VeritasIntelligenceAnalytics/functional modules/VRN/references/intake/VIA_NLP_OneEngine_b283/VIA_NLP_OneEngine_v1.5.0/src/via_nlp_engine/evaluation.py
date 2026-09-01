"""Gold-set quality metrics and candidate-only topic threshold calibration."""

from __future__ import annotations

import hashlib
import json
from statistics import mean
from typing import Any, Iterable

from .discourse import CPUHierarchicalTopicOrganizer, build_dialogue_flow
from .text_ops import TextProcessor


def _safe_div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def precision_recall_f1(predicted: Iterable[Any], expected: Iterable[Any]) -> dict[str, float]:
    predicted_set = set(predicted)
    expected_set = set(expected)
    true_positive = len(predicted_set & expected_set)
    precision = _safe_div(true_positive, len(predicted_set))
    recall = _safe_div(true_positive, len(expected_set))
    f1 = _safe_div(2 * precision * recall, precision + recall)
    return {
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "f1": round(f1, 6),
    }


def bcubed_scores(predicted: dict[str, str], expected: dict[str, str]) -> dict[str, float]:
    keys = sorted(set(predicted) & set(expected))
    if not keys:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0, "coverage": 0.0}
    predicted_groups: dict[str, set[str]] = {}
    expected_groups: dict[str, set[str]] = {}
    for key in keys:
        predicted_groups.setdefault(predicted[key], set()).add(key)
        expected_groups.setdefault(expected[key], set()).add(key)
    precisions: list[float] = []
    recalls: list[float] = []
    for key in keys:
        predicted_members = predicted_groups[predicted[key]]
        expected_members = expected_groups[expected[key]]
        shared = len(predicted_members & expected_members)
        precisions.append(_safe_div(shared, len(predicted_members)))
        recalls.append(_safe_div(shared, len(expected_members)))
    precision = mean(precisions)
    recall = mean(recalls)
    f1 = _safe_div(2 * precision * recall, precision + recall)
    return {
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "f1": round(f1, 6),
        "coverage": round(_safe_div(len(keys), len(expected)), 6),
    }


def topic_labels(topics: list[dict[str, Any]]) -> dict[str, str]:
    return {
        segment_id: str(topic["topic_id"])
        for topic in topics
        for segment_id in topic.get("segment_ids", [])
    }


def return_pairs(dialogue_flow: dict[str, Any]) -> set[tuple[str, str]]:
    return {
        (str(item.get("previous_segment", "")), str(item.get("source_segment", "")))
        for item in dialogue_flow.get("return_links", [])
        if item.get("previous_segment") and item.get("source_segment")
    }


def evaluate_topic_output(
    topics: list[dict[str, Any]],
    dialogue_flow: dict[str, Any],
    gold_topic_labels: dict[str, str],
    gold_return_pairs: Iterable[tuple[str, str]],
) -> dict[str, Any]:
    clustering = bcubed_scores(topic_labels(topics), gold_topic_labels)
    returns = precision_recall_f1(return_pairs(dialogue_flow), gold_return_pairs)
    score = 0.7 * clustering["f1"] + 0.3 * returns["f1"]
    return {
        "b_cubed": clustering,
        "topic_return": returns,
        "composite_score": round(score, 6),
    }


class TopicThresholdCalibrator:
    """Grid-search sparse topic settings; never applies a candidate automatically."""

    def __init__(
        self,
        processor: TextProcessor,
        thresholds: Iterable[float] = (0.14, 0.18, 0.22),
        merge_thresholds: Iterable[float] = (0.31, 0.38, 0.45),
        max_topics: int = 40,
        max_features: int = 96,
        max_keywords: int = 12,
        anchor_boost: float = 0.28,
        anchor_conflict_penalty: float = 0.22,
    ) -> None:
        self.processor = processor
        self.thresholds = sorted({float(value) for value in thresholds})
        self.merge_thresholds = sorted({float(value) for value in merge_thresholds})
        self.max_topics = int(max_topics)
        self.max_features = int(max_features)
        self.max_keywords = int(max_keywords)
        self.anchor_boost = float(anchor_boost)
        self.anchor_conflict_penalty = float(anchor_conflict_penalty)

    def calibrate(self, cases: list[dict[str, Any]]) -> dict[str, Any]:
        if not cases:
            return {
                "status": "insufficient_gold_cases",
                "automatic_apply": False,
                "candidates": [],
            }
        candidates: list[dict[str, Any]] = []
        for threshold in self.thresholds:
            for merge_threshold in self.merge_thresholds:
                organizer = CPUHierarchicalTopicOrganizer(
                    self.processor,
                    threshold=threshold,
                    merge_threshold=merge_threshold,
                    max_topics=self.max_topics,
                    max_features=self.max_features,
                    max_keywords=self.max_keywords,
                    anchor_boost=self.anchor_boost,
                    anchor_conflict_penalty=self.anchor_conflict_penalty,
                )
                case_scores: list[float] = []
                case_metrics: list[dict[str, Any]] = []
                for case in cases:
                    segments = list(case["segments"])
                    topics = organizer.organize(segments)
                    flow = build_dialogue_flow(topics, segments)
                    metrics = evaluate_topic_output(
                        topics,
                        flow,
                        dict(case["gold_topic_labels"]),
                        [tuple(item) for item in case.get("gold_return_pairs", [])],
                    )
                    case_metrics.append(metrics)
                    case_scores.append(float(metrics["composite_score"]))
                candidates.append(
                    {
                        "topic_threshold": threshold,
                        "topic_merge_threshold": merge_threshold,
                        "mean_score": round(mean(case_scores), 6),
                        "case_metrics": case_metrics,
                    }
                )
        ranked = sorted(
            candidates,
            key=lambda item: (-item["mean_score"], item["topic_threshold"], item["topic_merge_threshold"]),
        )
        selected = {key: ranked[0][key] for key in ("topic_threshold", "topic_merge_threshold", "mean_score")}
        fingerprint = hashlib.sha256(
            json.dumps(selected, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return {
            "status": "candidate_ready",
            "selected": selected,
            "candidate_sha256": fingerprint,
            "automatic_apply": False,
            "promotion_gate": "locked_test_and_human_approval_required",
            "candidates": ranked,
        }
