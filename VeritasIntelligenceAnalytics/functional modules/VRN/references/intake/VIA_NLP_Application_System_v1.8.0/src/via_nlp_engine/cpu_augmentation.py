"""Optional CPU-first NLP augmentation with deterministic safe fallbacks.

All results are derivative candidates.  This module never installs packages,
downloads models, mutates source text, deletes segments, or rewrites the Mind
Map.  Optional providers are imported only while an enabled knowledge task is
running; the engine remains dependency-free by default.
"""

from __future__ import annotations

import bisect
import difflib
import hashlib
import importlib.util
import json
import re
import unicodedata
from collections import defaultdict
from typing import Any, Iterable


CPU_AUGMENTATION_SCHEMA = "VIA_CPU_NLP_AUGMENTATION/1.0"
CPU_PROVIDER_REGISTRY_SCHEMA = "VIA_CPU_NLP_PROVIDER_REGISTRY/1.0"
ENGLISH_ALIAS_STOPWORDS = {
    "a", "am", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "in", "is", "it", "of", "on", "or", "that", "the", "this", "to", "was", "were", "with",
}
PURE_LAYOUT_MARKER_RE = re.compile(
    r"(?is)^\s*(?:HTML|MD\+\s*\d*|本文區(?:\s*[（(]修復[）)])?|右資訊區|"
    r"=====\s+(?:BEGIN|END)\s+(?:VIA SOURCE RECORD|EXTRACTED CONTENT)[^\r\n]*=====)\s*$"
)

DEFAULT_CPU_TOOL_CONFIG: dict[str, Any] = {
    "enabled": True,
    "use_available_providers": True,
    "max_text_chars": 250_000,
    "max_segments": 2_000,
    "max_sentence_samples": 60,
    "max_exact_matches": 10_000,
    "max_fuzzy_candidates": 100,
    "fuzzy_threshold": 88.0,
    "max_duplicate_pairs": 200,
    "near_duplicate_threshold": 0.88,
    "min_encoding_confidence": 0.40,
    "max_graph_issues": 500,
    "min_alias_chars": 2,
}

CPU_PROVIDER_GROUPS: tuple[dict[str, Any], ...] = (
    {
        "provider_id": "CPU01",
        "label": "ftfy",
        "scope": "text_repair_optional",
        "capabilities": ["unicode_repair", "mojibake_candidate"],
        "python": [("ftfy", "ftfy")],
        "official_urls": ["https://github.com/rspeer/python-ftfy"],
        "safety": "Repair is derivative-only and rejected when protected facts change.",
    },
    {
        "provider_id": "CPU02",
        "label": "charset-normalizer",
        "scope": "document_intake_optional",
        "capabilities": ["encoding_detection", "lossless_decode_candidate"],
        "python": [("charset-normalizer", "charset_normalizer")],
        "official_urls": ["https://charset-normalizer.readthedocs.io/"],
        "safety": "Low-confidence guesses fall back to the deterministic decoder chain.",
    },
    {
        "provider_id": "CPU03",
        "label": "Microsoft BlingFire",
        "scope": "segmentation_optional",
        "capabilities": ["sentence_breaking", "tokenization"],
        "python": [("blingfire", "blingfire")],
        "official_urls": ["https://github.com/microsoft/BlingFire"],
        "safety": "Local CPU inference only; no model or network download is performed.",
    },
    {
        "provider_id": "CPU04",
        "label": "Lingua",
        "scope": "language_routing_optional",
        "capabilities": ["language_detection", "zh_en_routing"],
        "python": [("lingua-language-detector", "lingua")],
        "official_urls": ["https://github.com/pemistahl/lingua-py"],
        "notes": ["Python 3.11 environments must keep lingua-language-detector below 2.3."],
        "safety": "Language output is advisory and never translates or rewrites source text.",
    },
    {
        "provider_id": "CPU05",
        "label": "RapidFuzz",
        "scope": "ssot_matching_optional",
        "capabilities": ["fuzzy_alias_candidates", "string_similarity"],
        "python": [("RapidFuzz", "rapidfuzz")],
        "official_urls": ["https://rapidfuzz.github.io/RapidFuzz/"],
        "safety": "Fuzzy matches remain reviewable candidates and cannot promote SSOT terms.",
    },
    {
        "provider_id": "CPU06",
        "label": "pyahocorasick",
        "scope": "keyword_matching_optional",
        "capabilities": ["multi_pattern_search", "exact_alias_matching"],
        "python": [("pyahocorasick", "ahocorasick")],
        "official_urls": ["https://github.com/WojciechMula/pyahocorasick"],
        "safety": "Exact matching is read-only and bounded by configured result limits.",
    },
    {
        "provider_id": "CPU07",
        "label": "datasketch",
        "scope": "deduplication_optional",
        "capabilities": ["minhash", "lsh_near_duplicate_candidates"],
        "python": [("datasketch", "datasketch")],
        "official_urls": ["https://ekzhu.com/datasketch/lsh.html"],
        "safety": "Approximate results never delete, merge, or hide source segments.",
    },
    {
        "provider_id": "CPU08",
        "label": "NetworkX",
        "scope": "knowledge_graph_optional",
        "capabilities": ["graph_validation", "cycle_and_orphan_detection"],
        "python": [("networkx", "networkx")],
        "official_urls": ["https://networkx.org/documentation/stable/reference/index.html"],
        "safety": "Validation reports issues but never mutates graph nodes or edges.",
    },
    {
        "provider_id": "CPU09",
        "label": "msgspec",
        "scope": "contract_serialization_optional",
        "capabilities": ["json_round_trip", "typed_contract_acceleration"],
        "python": [("msgspec", "msgspec")],
        "official_urls": ["https://github.com/jcrist/msgspec"],
        "safety": "Serialization is verified by round-trip equality before acceptance.",
    },
    {
        "provider_id": "CPU10",
        "label": "marisa-trie",
        "scope": "lexicon_index_optional",
        "capabilities": ["compact_trie", "prefix_lookup"],
        "python": [("marisa-trie", "marisa_trie")],
        "official_urls": ["https://github.com/pytries/marisa-trie"],
        "safety": "The index is derived, immutable, and rebuildable from SSOT candidates.",
    },
)

_FACT_RE = re.compile(
    r"https?://[^\s<>]+|\b[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}\b|"
    r"(?:NT\$|US\$|USD|TWD|RMB|¥|￥|\$)\s?[\d,.]+|"
    r"(?<!\w)[+\-]?\d+(?:\.\d+)?\s?%|"
    r"\b(?:19|20|21)\d{2}[-/]\d{1,2}[-/]\d{1,2}\b|"
    r"(?<![A-Za-z0-9_])\d+(?:\.\d+)?(?![A-Za-z0-9_])",
    re.I,
)
_TERM_RE = re.compile(r"[A-Za-z][A-Za-z0-9_+.#\-]{1,}|[\u3400-\u9fff]{2,12}")
_SENTENCE_RE = re.compile(r"(?<=[。！？!?])\s*|(?<=[.;])\s+(?=[A-Z0-9\u3400-\u9fff])")


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _available(module: str) -> bool:
    try:
        return importlib.util.find_spec(module) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False


def _merged_config(config: dict[str, Any] | None) -> dict[str, Any]:
    result = dict(DEFAULT_CPU_TOOL_CONFIG)
    if config:
        result.update(config)
    return result


def _fact_signature(text: str) -> list[str]:
    return sorted(match.group(0) for match in _FACT_RE.finditer(text))


def decode_bytes_with_cpu_detector(
    raw: bytes,
    min_confidence: float = 0.40,
    use_available_provider: bool = True,
) -> dict[str, Any]:
    """Decode bytes losslessly, accepting charset-normalizer only at high confidence."""

    if use_available_provider and _available("charset_normalizer"):
        try:
            from charset_normalizer import from_bytes

            best = from_bytes(raw).best()
            if best is not None and best.encoding:
                candidate = str(best)
                coherence = float(getattr(best, "percent_coherence", 0.0) or 0.0) / 100.0
                if coherence >= min_confidence and candidate.encode(best.encoding) == raw:
                    return {
                        "text": candidate,
                        "encoding": str(best.encoding),
                        "backend": "charset_normalizer",
                        "confidence": round(coherence, 6),
                        "round_trip_exact": True,
                    }
        except (ImportError, LookupError, UnicodeError, ValueError):
            pass
    for encoding in ("utf-8-sig", "utf-8", "big5", "cp950", "gb18030"):
        try:
            candidate = raw.decode(encoding)
            round_trip = candidate.encode(encoding) == raw
            if round_trip:
                return {
                    "text": candidate,
                    "encoding": encoding,
                    "backend": "deterministic_decoder_chain",
                    "confidence": 1.0,
                    "round_trip_exact": True,
                }
        except (LookupError, UnicodeError):
            continue
    return {
        "text": raw.decode("utf-8", errors="replace"),
        "encoding": "utf-8-replace",
        "backend": "lossy_last_resort",
        "confidence": 0.0,
        "round_trip_exact": False,
    }


class CPUNLPAugmentor:
    """Build bounded, reviewable CPU NLP candidates for a knowledge package."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = _merged_config(config)

    def build(
        self,
        text: str,
        segments: list[dict[str, Any]],
        ssot_dictionary: dict[str, Any],
        mind_map: dict[str, Any],
    ) -> dict[str, Any]:
        if not bool(self.config["enabled"]):
            return self._disabled(text)
        bounded_text = text[: int(self.config["max_text_chars"])]
        bounded_segments = segments[: int(self.config["max_segments"])]
        aliases = self._aliases(ssot_dictionary)
        repair = self._repair_candidate(bounded_text)
        sentence_analysis = self._sentence_analysis(bounded_text)
        language_analysis = self._language_analysis(bounded_text)
        fuzzy_candidates = self._fuzzy_alias_candidates(bounded_text, aliases)
        exact_matches = self._exact_alias_matches(bounded_text, aliases)
        duplicate_candidates = self._near_duplicate_candidates(bounded_segments)
        graph_validation = self._validate_graph(mind_map)
        contract_validation = self._validate_contract(
            {
                "schema": CPU_AUGMENTATION_SCHEMA,
                "source_sha256": _sha256_text(text),
                "segment_count": len(segments),
                "alias_count": len(aliases),
            }
        )
        lexicon_index = self._lexicon_index(aliases)
        provider_status = self._provider_status()
        return {
            "schema": CPU_AUGMENTATION_SCHEMA,
            "enabled": True,
            "source": {
                "sha256": _sha256_text(text),
                "characters": len(text),
                "analyzed_characters": len(bounded_text),
                "segments": len(segments),
                "analyzed_segments": len(bounded_segments),
                "source_text_mutated": False,
            },
            "provider_registry": provider_status,
            "unicode_repair": repair,
            "encoding_detection": {
                "status": "available_during_byte_intake",
                "provider_id": "CPU02",
                "already_decoded_text_rewritten": False,
                "fallback": "utf8_big5_cp950_gb18030_then_explicit_lossy_status",
            },
            "sentence_analysis": sentence_analysis,
            "language_analysis": language_analysis,
            "fuzzy_alias_candidates": fuzzy_candidates,
            "exact_alias_matches": exact_matches,
            "near_duplicate_candidates": duplicate_candidates,
            "graph_validation": graph_validation,
            "contract_validation": contract_validation,
            "lexicon_index": lexicon_index,
            "quality_gates": {
                "source_sha256_preserved": True,
                "source_text_mutated": False,
                "automatic_text_repair": False,
                "automatic_ssot_promotion": False,
                "automatic_segment_merge_or_deletion": False,
                "automatic_graph_mutation": False,
                "provider_count": len(CPU_PROVIDER_GROUPS),
                "graph_endpoints_valid": graph_validation["missing_endpoint_count"] == 0,
                "contract_round_trip": contract_validation["round_trip_equal"],
            },
            "policy": {
                "outputs": "derivative_candidates_only",
                "missing_provider": "deterministic_cpu_fallback",
                "provider_import": "knowledge_task_only_when_enabled",
                "network_access": False,
                "model_download": False,
                "source_write": False,
            },
        }

    def _disabled(self, text: str) -> dict[str, Any]:
        return {
            "schema": CPU_AUGMENTATION_SCHEMA,
            "enabled": False,
            "source": {"sha256": _sha256_text(text), "characters": len(text), "source_text_mutated": False},
            "provider_registry": self._provider_status(),
            "quality_gates": {"source_sha256_preserved": True, "source_text_mutated": False},
            "policy": {"outputs": "disabled", "source_write": False},
        }

    def _provider_status(self) -> dict[str, Any]:
        groups = []
        for definition in CPU_PROVIDER_GROUPS:
            distribution, module = definition["python"][0]
            found = _available(module)
            groups.append(
                {
                    "provider_id": definition["provider_id"],
                    "label": definition["label"],
                    "module": module,
                    "distribution": distribution,
                    "available": found,
                    "selected": found and bool(self.config["use_available_providers"]),
                    "fallback_available": True,
                }
            )
        return {
            "schema": CPU_PROVIDER_REGISTRY_SCHEMA,
            "provider_group_count": len(groups),
            "available": sum(item["available"] for item in groups),
            "selected": sum(item["selected"] for item in groups),
            "groups": groups,
        }

    def _use(self, module: str) -> bool:
        return bool(self.config["use_available_providers"]) and _available(module)

    @staticmethod
    def _aliases(ssot_dictionary: dict[str, Any]) -> list[str]:
        values = {
            str(alias).strip()
            for entry in ssot_dictionary.get("entries", [])
            for alias in entry.get("aliases", [])
            if str(alias).strip()
        }
        return sorted(values, key=lambda item: (item.casefold(), item))

    def _repair_candidate(self, text: str) -> dict[str, Any]:
        backend = "stdlib_unicode_normalize"
        candidate = unicodedata.normalize("NFC", text)
        if self._use("ftfy"):
            try:
                import ftfy

                candidate = ftfy.fix_text(text)
                backend = "ftfy"
            except (ImportError, UnicodeError, ValueError):
                candidate = unicodedata.normalize("NFC", text)
                backend = "stdlib_unicode_normalize_fallback"
        changed = candidate != text
        facts_preserved = _fact_signature(candidate) == _fact_signature(text)
        accepted = changed and facts_preserved
        return {
            "provider_id": "CPU01",
            "backend": backend,
            "status": "candidate_review_required" if accepted else "no_change" if not changed else "rejected_fact_change",
            "changed": changed,
            "facts_preserved": facts_preserved,
            "candidate_text": candidate if accepted else None,
            "candidate_sha256": _sha256_text(candidate),
            "source_sha256": _sha256_text(text),
            "auto_applied": False,
        }

    def _sentence_analysis(self, text: str) -> dict[str, Any]:
        backend = "deterministic_unicode_regex"
        sentences: list[str]
        if self._use("blingfire"):
            try:
                from blingfire import text_to_sentences

                sentences = [item.strip() for item in text_to_sentences(text).splitlines() if item.strip()]
                backend = "blingfire"
            except (ImportError, RuntimeError, UnicodeError, ValueError):
                sentences = self._fallback_sentences(text)
                backend = "deterministic_unicode_regex_fallback"
        else:
            sentences = self._fallback_sentences(text)
        maximum = int(self.config["max_sentence_samples"])
        return {
            "provider_id": "CPU03",
            "backend": backend,
            "sentence_count": len(sentences),
            "samples": sentences[:maximum],
            "sample_truncated": len(sentences) > maximum,
            "source_text_mutated": False,
        }

    @staticmethod
    def _fallback_sentences(text: str) -> list[str]:
        output: list[str] = []
        for line in text.splitlines():
            output.extend(item.strip() for item in _SENTENCE_RE.split(line) if item.strip())
        return output or ([text] if text else [])

    def _language_analysis(self, text: str) -> dict[str, Any]:
        cjk = len(re.findall(r"[\u3400-\u9fff]", text))
        latin = len(re.findall(r"[A-Za-z]", text))
        total = cjk + latin
        deterministic = "unknown" if total == 0 else "zh" if cjk / total >= 0.9 else "en" if latin / total >= 0.9 else "mixed"
        candidate = deterministic
        confidence: float | None = None
        backend = "deterministic_script_ratio"
        if self._use("lingua") and text.strip():
            try:
                from lingua import Language, LanguageDetectorBuilder

                detector = LanguageDetectorBuilder.from_languages(Language.CHINESE, Language.ENGLISH).build()
                detected = detector.detect_language_of(text[:20_000])
                if detected is not None:
                    candidate = "zh" if detected == Language.CHINESE else "en"
                    confidence = float(detector.compute_language_confidence(text[:20_000], detected))
                    backend = "lingua"
            except (AttributeError, ImportError, RuntimeError, TypeError, ValueError):
                backend = "deterministic_script_ratio_fallback"
        return {
            "provider_id": "CPU04",
            "backend": backend,
            "deterministic_language": deterministic,
            "provider_candidate": candidate,
            "provider_confidence": confidence,
            "mixed_script_ratio": round(min(cjk, latin) / max(1, total), 6),
            "routing_decision": deterministic,
            "provider_may_override_routing": False,
        }

    def _fuzzy_alias_candidates(self, text: str, aliases: list[str]) -> dict[str, Any]:
        queries = sorted(set(_TERM_RE.findall(text)), key=lambda item: (-len(item), item.casefold()))[:200]
        threshold = float(self.config["fuzzy_threshold"])
        maximum = int(self.config["max_fuzzy_candidates"])
        candidates: list[dict[str, Any]] = []
        backend = "difflib_bounded"
        if aliases and self._use("rapidfuzz"):
            try:
                from rapidfuzz import fuzz, process

                backend = "rapidfuzz"
                for query in queries:
                    for alias, score, _ in process.extract(query, aliases, scorer=fuzz.WRatio, limit=2, score_cutoff=threshold):
                        if query.casefold() != str(alias).casefold():
                            candidates.append({"query": query, "alias": str(alias), "score": round(float(score), 3), "status": "review_required"})
                            if len(candidates) >= maximum:
                                break
                    if len(candidates) >= maximum:
                        break
            except (ImportError, RuntimeError, TypeError, ValueError):
                backend = "difflib_bounded_fallback"
        if not candidates and aliases:
            bounded_aliases = aliases[:500]
            for query in queries:
                matches = difflib.get_close_matches(query, bounded_aliases, n=2, cutoff=threshold / 100.0)
                for alias in matches:
                    if query.casefold() == alias.casefold():
                        continue
                    score = difflib.SequenceMatcher(None, query.casefold(), alias.casefold()).ratio() * 100.0
                    candidates.append({"query": query, "alias": alias, "score": round(score, 3), "status": "review_required"})
                    if len(candidates) >= maximum:
                        break
                if len(candidates) >= maximum:
                    break
        return {
            "provider_id": "CPU05",
            "backend": backend,
            "threshold": threshold,
            "candidates": candidates,
            "candidate_count": len(candidates),
            "auto_promoted": False,
        }

    def _exact_alias_matches(self, text: str, aliases: list[str]) -> dict[str, Any]:
        minimum = int(self.config["min_alias_chars"])
        terms = [
            item
            for item in aliases
            if len(item) >= minimum
            and item.casefold() not in ENGLISH_ALIAS_STOPWORDS
            and (len(item) >= 3 or not item.isascii() or item.isupper())
        ]
        maximum = int(self.config["max_exact_matches"])
        matches: list[dict[str, Any]] = []
        backend = "bounded_literal_search"
        if terms and self._use("ahocorasick"):
            try:
                import ahocorasick

                automaton = ahocorasick.Automaton()
                for index, term in enumerate(terms):
                    automaton.add_word(term, (index, term))
                automaton.make_automaton()
                for end, (_, term) in automaton.iter(text):
                    start = end - len(term) + 1
                    if not self._alias_boundary_ok(text, start, end + 1, term):
                        continue
                    matches.append({"term": term, "start": start, "end": end + 1})
                    if len(matches) >= maximum:
                        break
                backend = "pyahocorasick"
            except (ImportError, RuntimeError, TypeError, ValueError):
                backend = "bounded_literal_search_fallback"
        if not matches:
            for term in terms[:500]:
                start = text.find(term)
                while start >= 0:
                    end = start + len(term)
                    if self._alias_boundary_ok(text, start, end, term):
                        matches.append({"term": term, "start": start, "end": end})
                    if len(matches) >= maximum:
                        break
                    start = text.find(term, start + max(1, len(term)))
                if len(matches) >= maximum:
                    break
            matches.sort(key=lambda item: (item["start"], item["end"], item["term"]))
        return {
            "provider_id": "CPU06",
            "backend": backend,
            "matches": matches,
            "match_count": len(matches),
            "truncated": len(matches) >= maximum,
        }

    @staticmethod
    def _alias_boundary_ok(text: str, start: int, end: int, term: str) -> bool:
        if not term.isascii() or not any(char.isalnum() for char in term):
            return True
        left_ok = start == 0 or not (text[start - 1].isalnum() or text[start - 1] == "_")
        right_ok = end == len(text) or not (text[end].isalnum() or text[end] == "_")
        return left_ok and right_ok

    @staticmethod
    def _shingles(text: str) -> set[str]:
        normalized = re.sub(r"\s+", " ", text.casefold()).strip()
        tokens = _TERM_RE.findall(normalized)
        if len(tokens) < 3:
            return set(tokens) or ({normalized} if normalized else set())
        return {"\x1f".join(tokens[index : index + 3]) for index in range(len(tokens) - 2)}

    def _near_duplicate_candidates(self, segments: list[dict[str, Any]]) -> dict[str, Any]:
        threshold = float(self.config["near_duplicate_threshold"])
        maximum = int(self.config["max_duplicate_pairs"])
        records = [
            (str(item["segment_id"]), self._shingles(str(item["text"])))
            for item in segments
            if not PURE_LAYOUT_MARKER_RE.fullmatch(str(item["text"]))
        ]
        records = [(segment_id, shingles) for segment_id, shingles in records if shingles]
        pairs: list[dict[str, Any]] = []
        backend = "bounded_shingle_index"
        if records and self._use("datasketch"):
            try:
                from datasketch import MinHash, MinHashLSH

                lsh = MinHashLSH(threshold=threshold, num_perm=64)
                stored: dict[str, tuple[Any, set[str]]] = {}
                for segment_id, shingles in records:
                    fingerprint = MinHash(num_perm=64)
                    for shingle in sorted(shingles):
                        fingerprint.update(shingle.encode("utf-8"))
                    for prior_id in sorted(lsh.query(fingerprint)):
                        prior_shingles = stored[prior_id][1]
                        score = len(shingles & prior_shingles) / max(1, len(shingles | prior_shingles))
                        if score >= threshold:
                            pairs.append({"left": prior_id, "right": segment_id, "similarity": round(score, 6), "status": "review_required"})
                            if len(pairs) >= maximum:
                                break
                    lsh.insert(segment_id, fingerprint)
                    stored[segment_id] = (fingerprint, shingles)
                    if len(pairs) >= maximum:
                        break
                backend = "datasketch_minhash_lsh_exact_jaccard_gate"
            except (ImportError, RuntimeError, TypeError, ValueError):
                backend = "bounded_shingle_index_fallback"
        if not pairs:
            buckets: dict[tuple[int, str], list[tuple[str, set[str]]]] = defaultdict(list)
            for segment_id, shingles in records:
                anchor = min(shingles)[:24]
                key = (min(20, len(shingles) // 5), anchor)
                for prior_id, prior_shingles in buckets[key][-40:]:
                    score = len(shingles & prior_shingles) / max(1, len(shingles | prior_shingles))
                    if score >= threshold:
                        pairs.append({"left": prior_id, "right": segment_id, "similarity": round(score, 6), "status": "review_required"})
                        if len(pairs) >= maximum:
                            break
                buckets[key].append((segment_id, shingles))
                if len(pairs) >= maximum:
                    break
        return {
            "provider_id": "CPU07",
            "backend": backend,
            "threshold": threshold,
            "pairs": pairs,
            "pair_count": len(pairs),
            "truncated": len(pairs) >= maximum,
            "approximate_candidates_verified_by_exact_jaccard": True,
            "automatic_merge_or_delete": False,
        }

    def _validate_graph(self, mind_map: dict[str, Any]) -> dict[str, Any]:
        ai_view = mind_map.get("ai_view", {})
        nodes = ai_view.get("nodes", [])
        edges = ai_view.get("edges", [])
        node_ids = {str(item.get("node_id")) for item in nodes}
        maximum = int(self.config["max_graph_issues"])
        missing = [
            {"edge": index, "from": edge.get("from"), "to": edge.get("to")}
            for index, edge in enumerate(edges)
            if str(edge.get("from")) not in node_ids or str(edge.get("to")) not in node_ids
        ][:maximum]
        self_loops = [
            {"edge": index, "node": edge.get("from")}
            for index, edge in enumerate(edges)
            if edge.get("from") == edge.get("to")
        ][:maximum]
        backend = "deterministic_directed_graph_validator"
        degrees = {node_id: 0 for node_id in node_ids}
        adjacency: dict[str, set[str]] = {node_id: set() for node_id in node_ids}
        indegree = {node_id: 0 for node_id in node_ids}
        for edge in edges:
            left, right = str(edge.get("from")), str(edge.get("to"))
            if left in node_ids and right in node_ids:
                degrees[left] += 1
                degrees[right] += 1
                if right not in adjacency[left]:
                    adjacency[left].add(right)
                    indegree[right] += 1
        cycles: list[list[str]] = []
        if self._use("networkx"):
            try:
                import networkx as nx

                graph = nx.DiGraph()
                graph.add_nodes_from(sorted(node_ids))
                graph.add_edges_from((str(item.get("from")), str(item.get("to"))) for item in edges if str(item.get("from")) in node_ids and str(item.get("to")) in node_ids)
                try:
                    cycle_edges = nx.find_cycle(graph, orientation="original")
                    cycle_nodes = [str(item[0]) for item in cycle_edges]
                    if cycle_edges:
                        cycle_nodes.append(str(cycle_edges[-1][1]))
                    cycles = [cycle_nodes[:maximum]] if cycle_nodes else []
                except nx.NetworkXNoCycle:
                    cycles = []
                backend = "networkx"
            except (ImportError, RuntimeError, TypeError, ValueError):
                backend = "deterministic_directed_graph_validator_fallback"
        if not cycles:
            remaining = dict(indegree)
            ready = sorted(node_id for node_id, degree in remaining.items() if degree == 0)
            consumed = 0
            while ready:
                node_id = ready.pop(0)
                consumed += 1
                for target in sorted(adjacency[node_id]):
                    remaining[target] -= 1
                    if remaining[target] == 0:
                        bisect.insort(ready, target)
            cyclic_nodes = sorted(node_id for node_id, degree in remaining.items() if degree > 0)
            if cyclic_nodes:
                cycles = [cyclic_nodes[:maximum]]
        orphan_nodes = sorted(node_id for node_id, degree in degrees.items() if degree == 0 and node_id != "ROOT")[:maximum]
        return {
            "provider_id": "CPU08",
            "backend": backend,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "missing_endpoints": missing,
            "missing_endpoint_count": len(missing),
            "self_loops": self_loops,
            "orphan_nodes": orphan_nodes,
            "cycles": cycles,
            "status": "pass" if not missing else "review_required",
            "graph_mutated": False,
        }

    def _validate_contract(self, value: dict[str, Any]) -> dict[str, Any]:
        backend = "stdlib_json"
        encoded: bytes
        decoded: Any
        if self._use("msgspec"):
            try:
                import msgspec

                encoded = msgspec.json.encode(value)
                decoded = msgspec.json.decode(encoded)
                backend = "msgspec"
            except (ImportError, RuntimeError, TypeError, ValueError):
                encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
                decoded = json.loads(encoded)
                backend = "stdlib_json_fallback"
        else:
            encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
            decoded = json.loads(encoded)
        return {
            "provider_id": "CPU09",
            "backend": backend,
            "encoded_bytes": len(encoded),
            "round_trip_equal": decoded == value,
            "status": "pass" if decoded == value else "fail",
        }

    def _lexicon_index(self, aliases: list[str]) -> dict[str, Any]:
        backend = "sorted_bisect_index"
        ordered = sorted(set(aliases))
        prefix_queries = sorted({item[: min(3, len(item))] for item in ordered if item})[:20]
        results: dict[str, list[str]] = {}
        if ordered and self._use("marisa_trie"):
            try:
                import marisa_trie

                trie = marisa_trie.Trie(ordered)
                results = {prefix: list(trie.keys(prefix))[:20] for prefix in prefix_queries}
                backend = "marisa_trie"
            except (ImportError, RuntimeError, TypeError, ValueError):
                backend = "sorted_bisect_index_fallback"
        if not results:
            for prefix in prefix_queries:
                start = bisect.bisect_left(ordered, prefix)
                results[prefix] = [item for item in ordered[start : start + 20] if item.startswith(prefix)]
        return {
            "provider_id": "CPU10",
            "backend": backend,
            "terms": len(ordered),
            "prefix_samples": results,
            "derived_index": True,
            "rebuildable": True,
        }


def provider_groups() -> tuple[dict[str, Any], ...]:
    """Return immutable provider definitions for read-only registry reporting."""

    return CPU_PROVIDER_GROUPS
