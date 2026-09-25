"""CPU-first discourse reconstruction for fragmented conversations and articles."""

from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from typing import Any

from .text_ops import TextProcessor


DEFAULT_TOPIC_THRESHOLD = 0.18
DEFAULT_TOPIC_MERGE_THRESHOLD = 0.31
DEFAULT_MAX_TOPICS = 40
DEFAULT_MAX_FEATURES_PER_SEGMENT = 96
DEFAULT_MAX_TOPIC_KEYWORDS = 12
MAX_SEMANTIC_UNITS_PER_SEGMENT = 12
CODE_IDENTIFIER_RE = re.compile(r"(?<![A-Za-z0-9_])(?:[A-Za-z_][A-Za-z0-9_]{2,}|[A-Z][A-Z0-9_-]{1,15})(?![A-Za-z0-9_])")
QUESTION_RE = re.compile(r"(?:[?？]|如何|怎麼|是否|能否|可否|what|how|why|can\s+we)", re.I)
REQUIREMENT_RE = re.compile(r"(?:必須|需要|請|要將|應該|不得|不可|must|should|required?|need\s+to)", re.I)
DECISION_RE = re.compile(r"(?:決定|確定|採用|鎖定|結論|同意|approved?|decided?|use\s+this)", re.I)
ISSUE_RE = re.compile(r"(?:錯誤|失敗|異常|問題|風險|衝突|OOM|bug|error|failed?|risk|conflict)", re.I)
ACTION_RE = re.compile(r"(?:執行|建立|產生|修正|優化|測試|部署|整合|更新|完成|implement|build|fix|test|deploy|update)", re.I)
PARAMETER_RE = re.compile(r"(?:參數|門檻|設定|config|parameter|threshold|[A-Z][A-Z0-9_]{2,}\s*=)", re.I)
CATEGORY_MARKERS = {
    "finance": ("股票", "市場", "資金", "營收", "財報", "ETF", "利率", "匯率", "投資", "stock", "market"),
    "nlp": ("NLP", "斷詞", "摘要", "語意", "翻譯", "關鍵字", "embedding", "RAG", "LLM", "mind map"),
    "engineering": ("Python", "PowerShell", "JavaScript", "API", "AST", "JSON", "程式", "引擎", "engine", "code"),
    "governance": ("SSOT", "Regex", "治理", "Hydra", "稽核", "版本", "回滾", "contract", "governance"),
    "workflow": ("流程", "任務", "路由", "測試", "修復", "部署", "整合", "pipeline", "monitor"),
}


def _counter_cosine(left: Counter[str], right: Counter[str]) -> float:
    shared = left.keys() & right.keys()
    numerator = sum(float(left[key]) * float(right[key]) for key in shared)
    left_norm = math.sqrt(sum(float(value) ** 2 for value in left.values()))
    right_norm = math.sqrt(sum(float(value) ** 2 for value in right.values()))
    return numerator / (left_norm * right_norm) if left_norm and right_norm else 0.0


def _weighted_similarity(left: Counter[str], right: Counter[str]) -> float:
    left_keys = set(left)
    right_keys = set(right)
    union = left_keys | right_keys
    jaccard = len(left_keys & right_keys) / max(1, len(union))
    category_left = {key for key in left_keys if key.startswith("__category_")}
    category_right = {key for key in right_keys if key.startswith("__category_")}
    category_boost = 1.0 if category_left & category_right else 0.0
    return min(1.0, 0.68 * _counter_cosine(left, right) + 0.22 * jaccard + 0.10 * category_boost)


def infer_content_roles(text: str, kind: str) -> list[str]:
    if "code" in kind:
        return ["code"]
    roles: list[str] = []
    for name, pattern in (
        ("question", QUESTION_RE),
        ("requirement", REQUIREMENT_RE),
        ("decision", DECISION_RE),
        ("issue", ISSUE_RE),
        ("action", ACTION_RE),
        ("parameter", PARAMETER_RE),
    ):
        if pattern.search(text):
            roles.append(name)
    return roles or ["context"]


class CPUHierarchicalTopicOrganizer:
    """Bounded sparse feature clustering with a second merge pass."""

    def __init__(
        self,
        processor: TextProcessor,
        threshold: float = DEFAULT_TOPIC_THRESHOLD,
        merge_threshold: float = DEFAULT_TOPIC_MERGE_THRESHOLD,
        max_topics: int = DEFAULT_MAX_TOPICS,
        max_features: int = DEFAULT_MAX_FEATURES_PER_SEGMENT,
        max_keywords: int = DEFAULT_MAX_TOPIC_KEYWORDS,
    ) -> None:
        self.processor = processor
        self.threshold = threshold
        self.merge_threshold = merge_threshold
        self.max_topics = max_topics
        self.max_features = max_features
        self.max_keywords = max_keywords

    def _features(self, text: str) -> Counter[str]:
        features: Counter[str] = Counter()
        for item in self.processor.keywords(text, top_k=min(32, self.max_features)):
            term = str(item["term"]).lower()
            features[term] += max(1, int(item.get("count", 1)))
        for identifier in CODE_IDENTIFIER_RE.findall(text)[: self.max_features]:
            features[identifier.lower()] += 2
        lower = text.lower()
        for category, markers in CATEGORY_MARKERS.items():
            hits = sum(lower.count(marker.lower()) for marker in markers)
            if hits:
                features[f"__category_{category}"] += min(8, hits * 2)
        return Counter(dict(features.most_common(self.max_features))) or Counter({"uncategorized": 1})

    @staticmethod
    def _new_cluster(segment: dict[str, Any], features: Counter[str], source_order: int) -> dict[str, Any]:
        return {
            "features": Counter(features),
            "segment_ids": [segment["segment_id"]],
            "characters": len(segment["text"]),
            "source_orders": [source_order],
            "speakers": Counter([segment["speaker"]] if segment.get("speaker") else []),
            "kinds": Counter([segment["kind"]]),
        }

    @staticmethod
    def _merge_into(cluster: dict[str, Any], segment: dict[str, Any], features: Counter[str], source_order: int) -> None:
        cluster["features"].update(features)
        cluster["segment_ids"].append(segment["segment_id"])
        cluster["characters"] += len(segment["text"])
        cluster["source_orders"].append(source_order)
        if segment.get("speaker"):
            cluster["speakers"].update([segment["speaker"]])
        cluster["kinds"].update([segment["kind"]])

    @staticmethod
    def _merge_clusters(target: dict[str, Any], source: dict[str, Any]) -> None:
        target["features"].update(source["features"])
        target["segment_ids"].extend(source["segment_ids"])
        target["characters"] += source["characters"]
        target["source_orders"].extend(source["source_orders"])
        target["speakers"].update(source["speakers"])
        target["kinds"].update(source["kinds"])

    def _consolidate(self, clusters: list[dict[str, Any]]) -> list[dict[str, Any]]:
        changed = True
        while changed and len(clusters) > 1:
            changed = False
            best_pair: tuple[int, int] | None = None
            best_score = self.merge_threshold
            for left_index in range(len(clusters)):
                for right_index in range(left_index + 1, len(clusters)):
                    score = _weighted_similarity(clusters[left_index]["features"], clusters[right_index]["features"])
                    if score >= best_score:
                        best_pair = (left_index, right_index)
                        best_score = score
            if best_pair:
                left_index, right_index = best_pair
                self._merge_clusters(clusters[left_index], clusters[right_index])
                clusters.pop(right_index)
                changed = True
        return clusters

    def organize(self, segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        clusters: list[dict[str, Any]] = []
        for source_order, segment in enumerate(segments, start=1):
            features = self._features(segment["text"])
            scored = [(_weighted_similarity(features, cluster["features"]), index) for index, cluster in enumerate(clusters)]
            best_score, best_index = max(scored, default=(0.0, -1))
            if best_index >= 0 and (best_score >= self.threshold or len(clusters) >= self.max_topics):
                self._merge_into(clusters[best_index], segment, features, source_order)
            else:
                clusters.append(self._new_cluster(segment, features, source_order))
        clusters = self._consolidate(clusters)

        ordered = sorted(clusters, key=lambda item: min(item["source_orders"]))
        output: list[dict[str, Any]] = []
        for index, cluster in enumerate(ordered, start=1):
            ordinary = [(term, count) for term, count in cluster["features"].most_common() if not term.startswith("__category_")]
            keywords = [term for term, _ in ordinary[: self.max_keywords]] or ["uncategorized"]
            source_orders = sorted(cluster["source_orders"])
            runs = 1 + sum(current != previous + 1 for previous, current in zip(source_orders, source_orders[1:]))
            segment_order = sorted(zip(cluster["source_orders"], cluster["segment_ids"]))
            episodes: list[dict[str, Any]] = []
            for source_order, segment_id in segment_order:
                if not episodes or source_order != episodes[-1]["last_source_order"] + 1:
                    episodes.append(
                        {
                            "episode_id": "",
                            "first_source_order": source_order,
                            "last_source_order": source_order,
                            "segment_ids": [segment_id],
                        }
                    )
                else:
                    episodes[-1]["last_source_order"] = source_order
                    episodes[-1]["segment_ids"].append(segment_id)
            for episode_index, episode in enumerate(episodes, start=1):
                episode["episode_id"] = f"TOPIC-{index:04d}-EP-{episode_index:03d}"
            categories = [
                term.removeprefix("__category_")
                for term, _ in cluster["features"].most_common()
                if term.startswith("__category_")
            ]
            output.append(
                {
                    "topic_id": f"TOPIC-{index:04d}",
                    "title": " · ".join(keywords[:3]),
                    "keywords": keywords,
                    "segment_ids": [segment_id for _, segment_id in segment_order],
                    "segment_count": len(cluster["segment_ids"]),
                    "characters": cluster["characters"],
                    "first_source_order": min(source_orders),
                    "last_source_order": max(source_orders),
                    "recurrence_count": max(0, runs - 1),
                    "episodes": episodes,
                    "categories": categories,
                    "speakers": [name for name, _ in cluster["speakers"].most_common()],
                    "content_kinds": dict(cluster["kinds"]),
                    "semantic_backend": "cpu_sparse_hierarchical",
                }
            )
        return output


def build_refinement_ledger(processor: TextProcessor, segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for segment in segments:
        if "code" in segment["kind"]:
            repaired = {
                "repaired_text": segment["text"],
                "changes": [],
                "semantic_rewrite_applied": False,
            }
        else:
            repaired = processor.repair(segment["text"])
        optimized = str(repaired["repaired_text"])
        units = [item for item in processor.split_sentences(processor.normalize(optimized)) if item]
        output.append(
            {
                "segment_id": segment["segment_id"],
                "source_sha256": segment["sha256"],
                "optimized_text": optimized,
                "optimized_sha256": hashlib.sha256(optimized.encode("utf-8")).hexdigest(),
                "roles": infer_content_roles(optimized, segment["kind"]),
                "keywords": [item["term"] for item in processor.keywords(optimized, top_k=10)],
                "semantic_units": units[:MAX_SEMANTIC_UNITS_PER_SEGMENT],
                "semantic_units_truncated": len(units) > MAX_SEMANTIC_UNITS_PER_SEGMENT,
                "changes": repaired.get("changes", []),
                "semantic_rewrite_applied": bool(repaired.get("semantic_rewrite_applied", False)),
                "derivative_only": True,
            }
        )
    return output


def build_dialogue_flow(topics: list[dict[str, Any]], segments: list[dict[str, Any]]) -> dict[str, Any]:
    topic_for_segment = {segment_id: topic["topic_id"] for topic in topics for segment_id in topic["segment_ids"]}
    timeline: list[dict[str, Any]] = []
    transition_counts: Counter[tuple[str, str]] = Counter()
    last_seen: dict[str, int] = {}
    return_links: list[dict[str, Any]] = []
    previous_topic: str | None = None
    for source_order, segment in enumerate(segments, start=1):
        topic_id = topic_for_segment[segment["segment_id"]]
        if previous_topic and previous_topic != topic_id:
            transition_counts[(previous_topic, topic_id)] += 1
        if topic_id in last_seen and previous_topic != topic_id:
            return_links.append(
                {
                    "relation": "returns_to_topic",
                    "topic_id": topic_id,
                    "from_source_order": last_seen[topic_id],
                    "to_source_order": source_order,
                    "gap_segments": source_order - last_seen[topic_id] - 1,
                    "source_segment": segment["segment_id"],
                }
            )
        timeline.append(
            {
                "source_order": source_order,
                "segment_id": segment["segment_id"],
                "topic_id": topic_id,
                "speaker": segment.get("speaker"),
                "timestamp": segment.get("timestamp"),
            }
        )
        last_seen[topic_id] = source_order
        previous_topic = topic_id
    transitions = [
        {"from_topic": left, "to_topic": right, "count": count}
        for (left, right), count in transition_counts.most_common()
    ]
    return {
        "timeline": timeline,
        "transitions": transitions,
        "return_links": return_links,
        "metrics": {
            "topic_switches": sum(transition_counts.values()),
            "topic_returns": len(return_links),
            "jumpiness_ratio": round(sum(transition_counts.values()) / max(1, len(segments) - 1), 6),
        },
    }
