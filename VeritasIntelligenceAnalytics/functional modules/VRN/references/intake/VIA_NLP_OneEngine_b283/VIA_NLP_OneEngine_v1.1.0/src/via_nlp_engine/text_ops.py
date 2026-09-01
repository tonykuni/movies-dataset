"""Deterministic bilingual text repair and analysis for arbitrary articles."""

from __future__ import annotations

import difflib
import importlib.util
import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
SPACE_RE = re.compile(r"[ \t\u00a0\u3000]+")
BLANK_LINES_RE = re.compile(r"\n{3,}")
REPEATED_PUNCT_RE = re.compile(r"([，。！？；：,.!?;:])\1+")
CHINESE_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
ENGLISH_RE = re.compile(r"[A-Za-z]")
WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_'-]{1,}|[\u3400-\u9fff]{2,6}")
MONEY_RE = re.compile(r"(?:NT\$|US\$|USD|TWD|RMB|¥|￥|\$)\s?[\d,.]+(?:億|萬|千|m|bn|million|billion)?", re.I)
PERCENT_RE = re.compile(r"(?<!\w)[+-]?\d+(?:\.\d+)?\s?%")
DATE_RE = re.compile(r"(?:20\d{2}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}(?:[-/]20\d{2})?)")
TICKER_RE = re.compile(r"(?<![A-Z0-9])(?:\d{4}(?:\.TW|\.TWO)?|[A-Z]{1,5})(?![A-Z0-9])")
URL_RE = re.compile(r"https?://[^\s<>]+")
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[。！？!?])\s*|(?<=[.;])\s+(?=[A-Z0-9\u3400-\u9fff])")

FINANCE_TERMS = {"股票", "投資", "營收", "獲利", "財報", "市場", "利率", "通膨", "資金", "ETF", "stock", "revenue", "market"}
TECH_TERMS = {"AI", "人工智慧", "軟體", "硬體", "模型", "演算法", "資料庫", "API", "Python", "technology", "software"}
OPERATIONS_TERMS = {"專案", "流程", "供應鏈", "交付", "會議", "待辦", "決策", "排程", "project", "operation", "delivery"}
TRANSCRIPT_MARKERS = {"發言人", "主持人", "逐字稿", "會議", "speaker", "transcript", "action item"}
RESEARCH_MARKERS = {"摘要", "方法", "結果", "結論", "研究", "假設", "abstract", "methodology", "results", "conclusion"}
NEWS_MARKERS = {"記者", "報導", "消息", "今日", "昨日", "新聞", "reported", "according to", "news"}
REPORT_MARKERS = {"執行摘要", "分析", "風險", "建議", "附錄", "report", "executive summary", "recommendation"}


class TextProcessor:
    def __init__(self, lexicon_path: str | Path) -> None:
        with Path(lexicon_path).open("r", encoding="utf-8") as handle:
            self.lexicon = json.load(handle)
        self.stopwords = set(self.lexicon.get("stopwords_zh", [])) | set(self.lexicon.get("stopwords_en", []))

    def sanitize(self, text: str) -> str:
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        text = CONTROL_RE.sub("", text.replace("\r\n", "\n").replace("\r", "\n"))
        text = unicodedata.normalize("NFKC", text)
        lines = [SPACE_RE.sub(" ", line).strip() for line in text.split("\n")]
        return BLANK_LINES_RE.sub("\n\n", "\n".join(lines)).strip()

    def normalize(self, text: str) -> str:
        text = self.sanitize(text)
        text = REPEATED_PUNCT_RE.sub(r"\1", text)
        text = re.sub(r"%{2,}", "%", text)
        text = re.sub(r"\s+([，。！？；：,.!?;:])", r"\1", text)
        text = re.sub(r"([，。！？；：])(?=[A-Za-z0-9])", r"\1 ", text)
        text = re.sub(r"([,.!?;:])(?=[\u3400-\u9fff])", r"\1 ", text)
        return text.strip()

    def detect_language(self, text: str) -> str:
        zh = len(CHINESE_RE.findall(text))
        en = len(ENGLISH_RE.findall(text))
        total = zh + en
        if total == 0:
            return "unknown"
        if zh / total >= 0.9:
            return "zh"
        if en / total >= 0.9:
            return "en"
        return "mixed"

    def detect_document_type(self, text: str) -> tuple[str, float]:
        lower = text.lower()
        groups = {
            "transcript": TRANSCRIPT_MARKERS,
            "research": RESEARCH_MARKERS,
            "news": NEWS_MARKERS,
            "report": REPORT_MARKERS,
        }
        scores = {name: sum(1 for marker in markers if marker.lower() in lower) for name, markers in groups.items()}
        best = max(scores, key=scores.get)
        score = scores[best]
        if score == 0:
            return "general_article", 0.5
        return best, min(0.98, 0.55 + score * 0.1)

    def split_sentences(self, text: str) -> list[str]:
        normalized = self.normalize(text)
        parts = [part.strip() for part in SENTENCE_BOUNDARY_RE.split(normalized) if part.strip()]
        if len(parts) <= 1 and "\n" in normalized:
            parts = [part.strip() for part in normalized.split("\n") if part.strip()]
        return parts or ([normalized] if normalized else [])

    def _apply_lexicon(self, text: str) -> tuple[str, list[dict[str, Any]]]:
        result = text
        changes: list[dict[str, Any]] = []
        protected = sorted(self.lexicon.get("protected_terms", []), key=len, reverse=True)
        placeholders: dict[str, str] = {}
        for index, term in enumerate(protected):
            token = f"\uFFF0{index}\uFFF1"
            if term in result:
                result = result.replace(term, token)
                placeholders[token] = term
        for source, target in self.lexicon.get("replacements", {}).items():
            count = result.lower().count(source.lower())
            if not count:
                continue
            result = re.sub(re.escape(source), target, result, flags=re.IGNORECASE)
            changes.append({"type": "lexicon", "from": source, "to": target, "count": count, "confidence": 0.99})
        for token, term in placeholders.items():
            result = result.replace(token, term)
        return result, changes

    def repair(self, text: str) -> dict[str, Any]:
        original = text
        normalized = self.normalize(text)
        repaired, changes = self._apply_lexicon(normalized)
        repaired = re.sub(r"\b(\w+)(?:\s+\1){2,}\b", r"\1", repaired, flags=re.IGNORECASE)
        repaired = re.sub(r"([\u3400-\u9fff]{1,6})(?:\1){2,}", r"\1", repaired)

        suggestions: list[dict[str, Any]] = []
        for source, candidates in self.lexicon.get("confusions", {}).items():
            if source in repaired:
                suggestions.append(
                    {"source": source, "candidates": candidates, "reason": "context_required", "auto_applied": False}
                )

        if repaired and repaired[-1] not in "。！？.!?;；:：)]}」』":
            language = self.detect_language(repaired)
            repaired += "." if language == "en" else "。"
            changes.append({"type": "punctuation", "from": "", "to": repaired[-1], "count": 1, "confidence": 0.85})

        diff = [
            {"op": tag, "original": original[i1:i2], "repaired": repaired[j1:j2]}
            for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, original, repaired).get_opcodes()
            if tag != "equal"
        ]
        return {
            "original_text": original,
            "repaired_text": repaired,
            "changes": changes,
            "review_suggestions": suggestions,
            "diff": diff,
            "semantic_rewrite_applied": False,
            "policy": "deterministic_high_confidence_only",
        }

    def tokenize(self, text: str) -> list[str]:
        if importlib.util.find_spec("jieba") is not None and CHINESE_RE.search(text):
            import jieba

            tokens = [token.strip() for token in jieba.cut(text, cut_all=False)]
        else:
            tokens = WORD_RE.findall(text)
        return [token for token in tokens if len(token) > 1 and token.lower() not in self.stopwords]

    def keywords(self, text: str, top_k: int = 10) -> list[dict[str, Any]]:
        tokens = self.tokenize(text)
        counts = Counter(token.lower() for token in tokens)
        if not counts:
            return []
        maximum = max(counts.values())
        return [
            {"term": term, "count": count, "score": round(count / maximum, 4)}
            for term, count in counts.most_common(max(1, min(top_k, 100)))
        ]

    def classify_rules(self, text: str) -> dict[str, Any]:
        lower = text.lower()
        groups = {"finance": FINANCE_TERMS, "technology": TECH_TERMS, "operations": OPERATIONS_TERMS}
        scores = {name: sum(lower.count(term.lower()) for term in terms) for name, terms in groups.items()}
        best = max(scores, key=scores.get)
        if scores[best] == 0:
            best = "general"
        total = sum(scores.values()) or 1
        confidence = 0.5 if best == "general" else min(0.95, 0.5 + scores[best] / total * 0.45)
        return {"label": best, "confidence": round(confidence, 4), "scores": scores, "backend": "rules"}

    def entities(self, text: str) -> list[dict[str, Any]]:
        entities: list[dict[str, Any]] = []
        patterns = [("MONEY", MONEY_RE), ("PERCENT", PERCENT_RE), ("DATE", DATE_RE), ("URL", URL_RE), ("EMAIL", EMAIL_RE)]
        for label, pattern in patterns:
            for match in pattern.finditer(text):
                entities.append({"text": match.group(0), "label": label, "start": match.start(), "end": match.end()})
        for match in TICKER_RE.finditer(text):
            value = match.group(0)
            overlaps = any(match.start() < item["end"] and match.end() > item["start"] for item in entities)
            looks_like_year = value.isdigit() and 1900 <= int(value) <= 2100
            if not overlaps and not looks_like_year and (value.isdigit() or ".TW" in value or ".TWO" in value):
                entities.append({"text": value, "label": "TICKER", "start": match.start(), "end": match.end()})
        return sorted(entities, key=lambda item: (item["start"], item["end"]))

    def summarize(self, text: str, max_points: int = 4) -> dict[str, Any]:
        sentences = self.split_sentences(text)
        if not sentences:
            return {"summary": "", "key_points": [], "backend": "extractive"}
        frequencies = Counter(self.tokenize(text))
        scored: list[tuple[float, int, str]] = []
        for index, sentence in enumerate(sentences):
            tokens = self.tokenize(sentence)
            score = sum(math.log1p(frequencies[token]) for token in tokens) / max(1, math.sqrt(len(tokens)))
            position_bonus = 1.15 if index < max(1, len(sentences) // 5) else 1.0
            scored.append((score * position_bonus, index, sentence))
        chosen = sorted(sorted(scored, reverse=True)[: max(1, min(max_points, 10))], key=lambda row: row[1])
        points = [row[2] for row in chosen]
        return {"summary": " ".join(points), "key_points": points, "backend": "extractive"}

    def structure(self, text: str) -> dict[str, Any]:
        doc_type, type_confidence = self.detect_document_type(text)
        repair = self.repair(text)
        repaired = repair["repaired_text"]
        sentences = self.split_sentences(repaired)
        title = sentences[0][:120] if sentences else ""
        summary = self.summarize(repaired)
        action_markers = re.compile(r"(?:待辦|應|需要|必須|action item|todo|must|should)", re.I)
        decision_markers = re.compile(r"(?:決定|決議|結論|同意|decision|agreed|conclusion)", re.I)
        return {
            "document_type": doc_type,
            "document_type_confidence": type_confidence,
            "title": title,
            "language": self.detect_language(repaired),
            "clean_text": repaired,
            "summary": summary["summary"],
            "key_points": summary["key_points"],
            "keywords": self.keywords(repaired, top_k=10),
            "entities": self.entities(repaired),
            "action_items": [s for s in sentences if action_markers.search(s)][:20],
            "decisions": [s for s in sentences if decision_markers.search(s)][:20],
            "repair": repair,
        }

    def analyze(self, text: str) -> dict[str, Any]:
        structured = self.structure(text)
        structured["classification"] = self.classify_rules(structured["clean_text"])
        structured["statistics"] = {
            "characters": len(text),
            "sentences": len(self.split_sentences(structured["clean_text"])),
            "tokens": len(self.tokenize(structured["clean_text"])),
        }
        return structured


def chunk_text(text: str, max_chars: int, overlap: int = 200) -> Iterable[str]:
    if max_chars < 1 or overlap < 0 or overlap >= max_chars:
        raise ValueError("Require max_chars >= 1 and 0 <= overlap < max_chars")
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        if end < len(text):
            boundary = max(text.rfind("\n", start, end), text.rfind("。", start, end), text.rfind(". ", start, end))
            if boundary > start + max_chars // 2:
                end = boundary + 1
        yield text[start:end]
        if end >= len(text):
            break
        start = max(start + 1, end - overlap)
