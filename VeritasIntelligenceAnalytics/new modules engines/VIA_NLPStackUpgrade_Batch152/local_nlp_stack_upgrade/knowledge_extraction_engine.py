"""CPU-friendly local knowledge extraction for Chinese financial text.

The engine is deliberately deterministic and works without a cloud model. Optional
libraries are used when installed, but every feature has a standard-library fallback.
The public contract remains compatible with the original ``extract(parsed_data)``
method and returns ``subject / predicate / object / attributes`` triples.
"""

from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import json
import logging
import re as stdlib_re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Mapping, Sequence

try:
    import regex as regex_engine  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - optional dependency
    regex_engine = stdlib_re

try:
    from rapidfuzz import fuzz, process as rapid_process  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - optional dependency
    fuzz = None
    rapid_process = None

try:
    import dateparser  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - optional dependency
    dateparser = None

try:
    from quantulum3 import parser as quantity_parser  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - optional dependency
    quantity_parser = None


LOGGER = logging.getLogger(__name__)

_PERCENT_RE = regex_engine.compile(r"(?P<number>[+-]?\d[\d,]*(?:\.\d+)?)\s*(?P<symbol>%|％)")
_MONEY_RE = regex_engine.compile(
    r"(?P<number>[+-]?\d[\d,]*(?:\.\d+)?)\s*"
    r"(?P<unit>兆|億|万|萬|千)?\s*"
    r"(?P<currency>元|美元|美金|人民幣|人民币|新台幣|新台币|NT\$|USD|TWD)"
)
_NUMBER_RE = regex_engine.compile(r"[+-]?\d[\d,]*(?:\.\d+)?")
_SENTENCE_END_RE = regex_engine.compile(r"(?<=[。！？!?])\s*|\n+")


@dataclass(frozen=True, slots=True)
class ExtractionConfig:
    """Runtime limits and confidence controls for deterministic extraction."""

    max_cause_chars: int = 80
    max_effect_chars: int = 160
    high_confidence_threshold: float = 0.70
    fuzzy_threshold: float = 88.0
    add_numeric_entities: bool = True
    use_optional_enrichment: bool = True

    def __post_init__(self) -> None:
        if self.max_cause_chars < 1 or self.max_effect_chars < 1:
            raise ValueError("Span length limits must be positive")
        if not 0 <= self.high_confidence_threshold <= 1:
            raise ValueError("high_confidence_threshold must be between 0 and 1")
        if not 0 <= self.fuzzy_threshold <= 100:
            raise ValueError("fuzzy_threshold must be between 0 and 100")


class KnowledgeExtractionEngine:
    """Extract metric, causation, policy-action, and influence triples locally."""

    DEFAULT_ALIASES: Mapping[str, Mapping[str, str]] = {
        "INDICATOR": {
            "npl": "NPL Ratio",
            "npl ratio": "NPL Ratio",
            "不良贷款率": "不良貸款率",
            "備抵呆賬覆蓋率": "備抵呆帳覆蓋率",
        }
    }

    def __init__(
        self,
        config: ExtractionConfig | None = None,
        *,
        trend_matrix: Mapping[str, Sequence[str]] | None = None,
        aliases: Mapping[str, Mapping[str, str]] | None = None,
    ) -> None:
        self.config = config or ExtractionConfig()
        self.trend_matrix = {
            key: tuple(words)
            for key, words in (
                trend_matrix
                or {
                    "UP": ("升", "增", "高", "漲", "擴大", "攀升", "上升", "提高", "提升", "上揚", "走高"),
                    "DOWN": ("降", "減", "低", "跌", "縮小", "下滑", "下降", "降低", "減少", "走低"),
                    "FLAT": ("持平", "維持", "不變", "穩定", "持穩", "持守"),
                }
            ).items()
        }
        self.aliases = {
            label: dict(values)
            for label, values in (aliases or self.DEFAULT_ALIASES).items()
        }

        # Ordered by specificity. Named groups make extraction independent of
        # positional capture changes when new patterns are added.
        self.causation_patterns = (
            (regex_engine.compile(r"受(?P<cause>[^。！？!?]+?)影響[，,、:：]\s*(?P<effect>[^。！？!?]+)"), "受影響"),
            (regex_engine.compile(r"(?:因為|由于|由於)(?P<cause>[^。！？!?]+?)[，,、:：]\s*(?P<effect>[^。！？!?]+)"), "因為"),
            (regex_engine.compile(r"(?:鑑於|鉴于)(?P<cause>[^。！？!?]+?)[，,、:：]\s*(?P<effect>[^。！？!?]+)"), "鑑於"),
            (regex_engine.compile(r"(?P<cause>[^。！？!?]+?)(?:導致|导致|造成|引發|引发|致使)(?P<effect>[^。！？!?]+)"), "導致"),
        )
        self.policy_cue_re = regex_engine.compile(
            r"(?P<cue>要求|決議|决议|命令|指示|規定|规定)\s*(?:將|将|把)?\s*(?P<action>[^。！？!?]+)"
        )
        self._negated_trend_re = regex_engine.compile(
            r"(?:未|無|没有|沒有|不|尚未)\s*(?P<word>[^，,。！？!?\s]{1,8})"
        )

    # ------------------------------------------------------------------
    # Optional-library helpers
    # ------------------------------------------------------------------
    def _canonical_entity(self, text: str, label: str) -> tuple[str, float | None]:
        """Resolve an alias with RapidFuzz when available, otherwise exact-match."""

        label_aliases = self.aliases.get(label, {})
        if not label_aliases:
            return text, None
        lowered = text.casefold()
        exact = label_aliases.get(lowered) or label_aliases.get(text)
        if exact:
            return exact, 100.0
        if rapid_process is None or fuzz is None:
            return text, None
        match = rapid_process.extractOne(
            text,
            list(label_aliases.keys()),
            scorer=fuzz.WRatio,
            score_cutoff=self.config.fuzzy_threshold,
        )
        if not match:
            return text, None
        matched_text, score, _ = match
        return label_aliases[matched_text], float(score)

    @staticmethod
    def _parse_decimal(raw: str) -> float | None:
        try:
            return float(Decimal(raw.replace(",", "")))
        except (InvalidOperation, ValueError):
            return None

    def _normalize_value(self, raw: str, label: str) -> dict[str, Any]:
        """Attach a stable numeric interpretation while retaining the raw value."""

        meta: dict[str, Any] = {"raw": raw, "label": label}
        if label == "PERCENT":
            match = _PERCENT_RE.search(raw)
            if match:
                number = self._parse_decimal(match.group("number"))
                if number is not None:
                    meta["numeric"] = number / 100.0
                    meta["percent"] = number
                    meta["unit"] = "%"
        elif label in {"MONEY", "CARDINAL", "QUANTITY"}:
            match = _MONEY_RE.search(raw)
            if match:
                number = self._parse_decimal(match.group("number"))
                if number is not None:
                    multiplier = {
                        "兆": 1e12,
                        "億": 1e8,
                        "万": 1e4,
                        "萬": 1e4,
                        "千": 1e3,
                    }.get(match.group("unit") or "", 1.0)
                    meta["numeric"] = number * multiplier
                    meta["unit"] = match.group("unit") or None
                    meta["currency"] = match.group("currency")
            elif label == "CARDINAL":
                number_match = _NUMBER_RE.search(raw)
                if number_match:
                    number = self._parse_decimal(number_match.group(0))
                    if number is not None:
                        meta["numeric"] = number
        return meta

    def _optional_entity_attributes(self, entity: Mapping[str, Any]) -> dict[str, Any]:
        attributes: dict[str, Any] = {}
        text = str(entity.get("text", ""))
        label = str(entity.get("label", ""))
        canonical, score = self._canonical_entity(text, label)
        if canonical != text:
            attributes["canonical"] = canonical
            attributes["alias_score"] = score
        if label in {"PERCENT", "MONEY", "CARDINAL", "QUANTITY"}:
            attributes["value_meta"] = self._normalize_value(text, label)
        if label == "DATE" and self.config.use_optional_enrichment and dateparser is not None:
            try:
                parsed = dateparser.parse(text, settings={"RETURN_AS_TIMEZONE_AWARE": False})
            except (TypeError, ValueError, OverflowError):
                parsed = None
            if parsed is not None:
                attributes["iso_date"] = parsed.date().isoformat()
        if self.config.use_optional_enrichment and quantity_parser is not None:
            try:
                quantities = quantity_parser.parse(text)
            except (TypeError, ValueError, IndexError):
                quantities = []
            if quantities:
                quantity = quantities[0]
                unit = getattr(getattr(quantity, "unit", None), "name", None)
                attributes["quantity"] = {
                    "value": getattr(quantity, "value", None),
                    "unit": unit,
                }
        return attributes

    def enrich_entities(
        self,
        text: str,
        entities: Iterable[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        """Add numeric entities and optional metadata without mutating input."""

        enriched: list[dict[str, Any]] = []
        seen: set[tuple[str, str, int, int]] = set()
        for source in entities:
            item = dict(source)
            item.setdefault("text", "")
            item.setdefault("label", "")
            key = (
                str(item["text"]),
                str(item["label"]),
                int(item.get("start_char", -1)),
                int(item.get("end_char", -1)),
            )
            if key in seen:
                continue
            seen.add(key)
            attributes = self._optional_entity_attributes(item)
            if attributes:
                item["attributes"] = attributes
            enriched.append(item)

        if self.config.add_numeric_entities:
            for match in _PERCENT_RE.finditer(text):
                self._append_numeric_entity(enriched, seen, match.group(0), "PERCENT", match.start(), match.end())
            for match in _MONEY_RE.finditer(text):
                self._append_numeric_entity(enriched, seen, match.group(0), "MONEY", match.start(), match.end())
        return enriched

    def _append_numeric_entity(
        self,
        entities: list[dict[str, Any]],
        seen: set[tuple[str, str, int, int]],
        value: str,
        label: str,
        start: int,
        end: int,
    ) -> None:
        if any(
            int(entity.get("start_char", -1)) < end
            and int(entity.get("end_char", -1)) > start
            for entity in entities
        ):
            return
        key = (value, label, start, end)
        if key in seen:
            return
        seen.add(key)
        item = {
            "text": value,
            "label": label,
            "start_char": start,
            "end_char": end,
            "attributes": {"value_meta": self._normalize_value(value, label)},
        }
        entities.append(item)

    # ------------------------------------------------------------------
    # Core extraction helpers
    # ------------------------------------------------------------------
    def _detect_trend(self, text: str) -> str:
        negated_words = {
            match.group("word") for match in self._negated_trend_re.finditer(text)
        }
        hits: list[tuple[int, str]] = []
        for trend, words in self.trend_matrix.items():
            for word in words:
                if word in negated_words:
                    continue
                index = text.find(word)
                if index >= 0:
                    hits.append((index, trend))
        return min(hits)[1] if hits else "UNKNOWN"

    @staticmethod
    def _clean_span(text: str) -> str:
        return regex_engine.sub(r"^[，,、：:\s]+|[，,、：:\s]+$", "", text).strip()

    @staticmethod
    def _find_in_order(sentence: str, left: str, right: str) -> tuple[int, int, str | None]:
        left_index = sentence.find(left)
        if left_index < 0:
            return -1, -1, None
        right_index = sentence.find(right, left_index + len(left))
        if right_index < 0 or right_index <= left_index:
            return left_index, right_index, None
        relation = KnowledgeExtractionEngine._clean_span(
            sentence[left_index + len(left) : right_index]
        )
        return left_index, right_index, relation or None

    def _entities_in_sentence(
        self, sentence: str, entities: Sequence[Mapping[str, Any]]
    ) -> list[dict[str, Any]]:
        """Return sentence entities in stable source order, using text fallback."""

        found: list[dict[str, Any]] = []
        for entity in entities:
            text = str(entity.get("text", ""))
            if text and text in sentence:
                found.append(dict(entity))
        return found

    # ------------------------------------------------------------------
    # Extraction stages
    # ------------------------------------------------------------------
    def _extract_metrics(
        self, sentence: str, entities: Sequence[Mapping[str, Any]]
    ) -> list[dict[str, Any]]:
        triples: list[dict[str, Any]] = []
        indicators = [e for e in entities if e.get("label") == "INDICATOR"]
        values = [
            e for e in entities if e.get("label") in {"PERCENT", "MONEY", "CARDINAL", "QUANTITY"}
        ]
        for indicator in indicators:
            indicator_text = str(indicator.get("text", ""))
            for value in values:
                value_text = str(value.get("text", ""))
                idx_indicator, idx_value, relation = self._find_in_order(
                    sentence, indicator_text, value_text
                )
                if idx_indicator < 0 or idx_value < 0:
                    continue
                trend = self._detect_trend(relation or "")
                if trend == "UNKNOWN":
                    trend = self._detect_trend(sentence[idx_value : idx_value + 40])
                value_meta = self._normalize_value(value_text, str(value.get("label", "")))
                confidence = 0.88 if trend != "UNKNOWN" else 0.68
                triples.append(
                    {
                        "subject": indicator_text,
                        "predicate": relation or "is",
                        "object": value_text,
                        "attributes": {
                            "type": "metric_change",
                            "trend": trend,
                            "value_meta": value_meta,
                            "confidence": confidence,
                            "subject_start_char": idx_indicator,
                            "object_start_char": idx_value,
                        },
                    }
                )
        return triples

    def _extract_causation(self, sentence: str) -> list[dict[str, Any]]:
        for pattern, relation_label in self.causation_patterns:
            match = pattern.search(sentence)
            if not match:
                continue
            cause = self._clean_span(match.group("cause"))
            effect = self._clean_span(match.group("effect"))
            if not cause or not effect:
                continue
            if len(cause) > self.config.max_cause_chars or len(effect) > self.config.max_effect_chars:
                continue
            return [
                {
                    "subject": cause,
                    "predicate": f"causes ({relation_label})",
                    "object": effect,
                    "attributes": {
                        "type": "causation",
                        "pattern": relation_label,
                        "confidence": 0.82,
                    },
                }
            ]
        return []

    def _extract_policy_actions(
        self, sentence: str, entities: Sequence[Mapping[str, Any]]
    ) -> list[dict[str, Any]]:
        orgs = [
            str(entity.get("text", ""))
            for entity in entities
            if entity.get("label") in {"POLICY_ORG", "ORG", "ORGANIZATION"}
            and entity.get("text")
        ]
        # Prefer a known organization entity. This avoids treating a preceding
        # purpose clause such as 「為防範風險」 as the actor.
        for actor in sorted(set(orgs), key=len, reverse=True):
            match = regex_engine.search(
                regex_engine.escape(actor) + r"\s*" + self.policy_cue_re.pattern,
                sentence,
            )
            if match:
                action = self._clean_span(match.group("action"))
                return [self._policy_triple(actor, action, match.group("cue"))]

        match = self.policy_cue_re.search(sentence)
        if not match:
            return []
        prefix = self._clean_span(sentence[: match.start()])
        actor = prefix.split("，")[-1].split(",")[-1].strip() or "未指定機構"
        action = self._clean_span(match.group("action"))
        return [self._policy_triple(actor, action, match.group("cue"))]

    @staticmethod
    def _policy_triple(actor: str, action: str, cue: str) -> dict[str, Any]:
        return {
            "subject": actor,
            "predicate": cue,
            "object": action,
            "attributes": {
                "type": "policy_action",
                "confidence": 0.78,
            },
        }

    def _extract_entity_cooccurrence(
        self, sentence: str, entities: Sequence[Mapping[str, Any]]
    ) -> list[dict[str, Any]]:
        concepts = [
            entity
            for entity in entities
            if entity.get("label") in {"CONCEPT", "EVENT", "FACTOR"}
        ]
        indicators = [entity for entity in entities if entity.get("label") == "INDICATOR"]
        influence_cues = ("影響", "衝擊", "推升", "導致", "造成", "加劇", "影响")
        if not concepts or not indicators or not any(cue in sentence for cue in influence_cues):
            return []
        return [
            {
                "subject": str(concept["text"]),
                "predicate": "influences",
                "object": str(indicator["text"]),
                "attributes": {"type": "influence", "confidence": 0.55},
            }
            for concept in concepts
            for indicator in indicators
        ]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def extract(self, parsed_data: Mapping[str, Any]) -> list[dict[str, Any]]:
        """Extract deterministic triples from preprocessor output."""

        sentences = [str(sentence) for sentence in parsed_data.get("sentences", [])]
        source_text = str(parsed_data.get("text") or "\n".join(sentences))
        entities = self.enrich_entities(
            source_text,
            parsed_data.get("entities", []),
        )
        knowledge_triples: list[dict[str, Any]] = []

        for sentence in sentences:
            if not sentence.strip():
                continue
            sentence_entities = self._entities_in_sentence(sentence, entities)
            stage_a = self._extract_metrics(sentence, sentence_entities)
            stage_b = self._extract_causation(sentence)
            stage_c = self._extract_policy_actions(sentence, sentence_entities)
            knowledge_triples.extend(stage_a)
            knowledge_triples.extend(stage_b)
            knowledge_triples.extend(stage_c)
            high_confidence_count = sum(
                triple.get("attributes", {}).get("confidence", 0)
                >= self.config.high_confidence_threshold
                for triple in stage_a + stage_b + stage_c
            )
            if high_confidence_count < 2:
                knowledge_triples.extend(
                    self._extract_entity_cooccurrence(sentence, sentence_entities)
                )

        unique: list[dict[str, Any]] = []
        seen: set[tuple[str, str, str]] = set()
        for triple in knowledge_triples:
            key = (
                str(triple.get("subject", "")),
                str(triple.get("predicate", "")),
                str(triple.get("object", "")),
            )
            if key not in seen:
                seen.add(key)
                unique.append(triple)
        return unique

    @staticmethod
    def rank_keywords(texts: Sequence[str], top_k: int = 20) -> list[tuple[str, float]]:
        """Rank terms with scikit-learn TF-IDF when available, else local counts."""

        if top_k < 1:
            raise ValueError("top_k must be positive")
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore[import-not-found]
        except ImportError:
            counts: dict[str, int] = {}
            for text in texts:
                for term in regex_engine.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z][A-Za-z0-9_-]+", text):
                    counts[term] = counts.get(term, 0) + 1
            return [(term, float(score)) for term, score in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:top_k]]

        clean_texts = [text.strip() for text in texts if text and text.strip()]
        if not clean_texts:
            return []
        vectorizer = TfidfVectorizer(token_pattern=r"(?u)[\u4e00-\u9fff]{2,}|[A-Za-z][A-Za-z0-9_-]+")
        matrix = vectorizer.fit_transform(clean_texts)
        scores = matrix.mean(axis=0).A1
        terms = vectorizer.get_feature_names_out()
        ranked = sorted(zip(terms, scores), key=lambda item: (-float(item[1]), item[0]))
        return [(str(term), float(score)) for term, score in ranked[:top_k]]

    @staticmethod
    def to_graph(triples: Sequence[Mapping[str, Any]]) -> Any:
        """Return a NetworkX graph when installed, or a JSON-safe graph fallback."""

        try:
            import networkx as nx  # type: ignore[import-not-found]
        except ImportError:
            nodes = sorted(
                {
                    str(value)
                    for triple in triples
                    for value in (triple.get("subject"), triple.get("object"))
                    if value is not None
                }
            )
            edges = [
                {
                    "source": str(triple.get("subject", "")),
                    "target": str(triple.get("object", "")),
                    "predicate": str(triple.get("predicate", "")),
                    "attributes": dict(triple.get("attributes", {})),
                }
                for triple in triples
            ]
            return {"nodes": nodes, "edges": edges}

        graph = nx.DiGraph()
        for triple in triples:
            subject = str(triple.get("subject", ""))
            object_ = str(triple.get("object", ""))
            graph.add_node(subject)
            graph.add_node(object_)
            graph.add_edge(
                subject,
                object_,
                predicate=str(triple.get("predicate", "")),
                **dict(triple.get("attributes", {})),
            )
        return graph


__all__ = ["ExtractionConfig", "KnowledgeExtractionEngine"]


if __name__ == "__main__":
    demo = {
        "text": "2026年Q1，受房地產市場波動影響，其 NPL Ratio 攀升至 1.85%。為防範風險，金管會要求將備抵呆賬覆蓋率提升至150%。",
        "sentences": [
            "2026年Q1，受房地產市場波動影響，其 NPL Ratio 攀升至 1.85%。",
            "為防範風險，金管會要求將備抵呆賬覆蓋率提升至150%。",
        ],
        "entities": [
            {"text": "房地產市場波動", "label": "CONCEPT"},
            {"text": "NPL Ratio", "label": "INDICATOR"},
            {"text": "金管會", "label": "POLICY_ORG"},
            {"text": "備抵呆賬覆蓋率", "label": "INDICATOR"},
        ],
    }
    print(json.dumps(KnowledgeExtractionEngine().extract(demo), ensure_ascii=False, indent=2))
