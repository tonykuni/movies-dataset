"""One-process, offline orchestration for the local NLP/knowledge stack.

The adapter exposes ten free local libraries as optional capabilities. The core
pipeline only requires spaCy, a local Chinese model, and OpenCC. Optional
capabilities are detected at runtime and fall back to deterministic local logic.
No network call is made by this module.
"""

from __future__ import annotations

import importlib.util
import os
import re
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from knowledge_extraction_engine import ExtractionConfig, KnowledgeExtractionEngine
from npl_preprocessor import (
    LanguageNormalizer,
    NLPConfig,
    NLPPreprocessor,
    NormalizationConfig,
)


LOCAL_LIBRARIES: tuple[tuple[str, str, str], ...] = (
    ("spacy", "Pipeline, POS, dependency parsing, NER and EntityRuler", "required"),
    ("opencc", "Simplified/Traditional Chinese conversion", "required"),
    ("pkuseg", "Domain-aware Chinese segmentation", "optional"),
    ("jieba", "Lightweight segmentation fallback", "optional"),
    ("regex", "Unicode-aware local regular expressions", "optional"),
    ("rapidfuzz", "Fast fuzzy alias/entity matching", "optional"),
    ("dateparser", "Local date normalization", "optional"),
    ("quantulum3", "Local quantity/unit parsing", "optional"),
    ("sklearn", "CPU TF-IDF keyword ranking", "optional"),
    ("networkx", "In-process graph representation", "optional"),
)


@dataclass(frozen=True, slots=True)
class CPUSettings:
    """Conservative defaults for a small local CPU host."""

    threads: int = 1
    n_process: int = 1
    batch_size: int = 32
    disable_components: tuple[str, ...] = ("transformer",)

    def __post_init__(self) -> None:
        if self.threads < 1 or self.n_process < 1 or self.batch_size < 1:
            raise ValueError("threads, n_process and batch_size must be positive")


def configure_cpu(settings: CPUSettings | None = None) -> CPUSettings:
    """Set common BLAS/OpenMP limits before model work begins."""

    active = settings or CPUSettings()
    value = str(active.threads)
    for name in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
        "TOKENIZERS_PARALLELISM",
    ):
        os.environ[name] = "false" if name == "TOKENIZERS_PARALLELISM" else value
    return active


def library_status() -> list[dict[str, str | bool]]:
    """Return dependency availability without importing optional libraries."""

    result: list[dict[str, str | bool]] = []
    for module_name, role, requirement in LOCAL_LIBRARIES:
        available = importlib.util.find_spec(module_name) is not None
        result.append(
            {
                "library": module_name,
                "role": role,
                "requirement": requirement,
                "installed": available,
                "mode": "native" if available else "fallback",
            }
        )
    return result


class LocalKnowledgePipeline:
    """CPU-first local pipeline combining normalization, NLP and extraction."""

    def __init__(
        self,
        *,
        model_name: str = "zh_core_web_sm",
        opencc_config: str = "s2twp",
        cpu: CPUSettings | None = None,
        punctuation_style: str = "preserve",
        preserve_newlines: bool = False,
        domain_patterns: Sequence[Mapping[str, Any]] | None = None,
    ) -> None:
        self.cpu = configure_cpu(cpu)
        self.normalizer = LanguageNormalizer(
            NormalizationConfig(
                opencc_config=opencc_config,
                punctuation_style=punctuation_style,
                preserve_newlines=preserve_newlines,
            )
        )
        self.preprocessor = NLPPreprocessor(
            NLPConfig(
                model_name=model_name,
                batch_size=self.cpu.batch_size,
                n_process=self.cpu.n_process,
                disable_components=self.cpu.disable_components,
            ),
            domain_patterns=domain_patterns,
        )
        self.extractor = KnowledgeExtractionEngine()

    def analyze(self, text: str | None) -> dict[str, Any]:
        """Normalize, parse, extract triples and return a JSON-safe graph payload."""

        normalized = self.normalizer.normalize(text)
        parsed = self.preprocessor.process(normalized)
        triples = self.extractor.extract(parsed)
        return {
            "normalized_text": normalized,
            "parsed": parsed,
            "triples": triples,
            "graph": self.graph_payload(triples),
        }

    def analyze_many(self, texts: Iterable[str | None]) -> list[dict[str, Any]]:
        """Batch normalize and parse while preserving input order."""

        raw_items = list(texts)
        normalized_items = [self.normalizer.normalize(text) for text in raw_items]
        parsed_items = self.preprocessor.process_many(
            normalized_items,
            batch_size=self.cpu.batch_size,
            n_process=self.cpu.n_process,
        )
        results: list[dict[str, Any]] = []
        for normalized, parsed in zip(normalized_items, parsed_items):
            triples = self.extractor.extract(parsed)
            results.append(
                {
                    "normalized_text": normalized,
                    "parsed": parsed,
                    "triples": triples,
                    "graph": self.graph_payload(triples),
                }
            )
        return results

    @staticmethod
    def graph_payload(triples: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
        """Serialize either NetworkX or the engine's graph fallback to plain JSON."""

        graph = KnowledgeExtractionEngine.to_graph(triples)
        if isinstance(graph, dict):
            return graph
        return {
            "nodes": sorted(str(node) for node in graph.nodes),
            "edges": [
                {
                    "source": str(source),
                    "target": str(target),
                    "attributes": dict(attributes),
                }
                for source, target, attributes in graph.edges(data=True)
            ],
        }

    @staticmethod
    def rank_keywords(texts: Sequence[str], top_k: int = 20) -> list[tuple[str, float]]:
        return KnowledgeExtractionEngine.rank_keywords(texts, top_k=top_k)

    @staticmethod
    def segment(text: str, backend: str = "auto") -> list[str]:
        """Segment text using pkuseg, jieba, or a deterministic regex fallback."""

        if not isinstance(text, str):
            raise TypeError("text must be a string")
        if backend not in {"auto", "pkuseg", "jieba", "regex"}:
            raise ValueError("backend must be auto, pkuseg, jieba or regex")

        if backend in {"auto", "pkuseg"} and importlib.util.find_spec("pkuseg"):
            import pkuseg  # type: ignore[import-not-found]

            return [token for token in pkuseg.pkuseg().cut(text) if token.strip()]
        if backend in {"auto", "jieba"} and importlib.util.find_spec("jieba"):
            import jieba  # type: ignore[import-not-found]

            return [token for token in jieba.cut(text, cut_all=False) if token.strip()]
        if backend in {"pkuseg", "jieba"}:
            raise RuntimeError(f"Requested segmenter '{backend}' is not installed")
        return re.findall(r"[\u4e00-\u9fff]+|[A-Za-z]+(?:[A-Za-z0-9_-]+)?|\d+(?:\.\d+)?|[^\w\s]", text)


__all__ = [
    "CPUSettings",
    "LOCAL_LIBRARIES",
    "LocalKnowledgePipeline",
    "configure_cpu",
    "library_status",
]
