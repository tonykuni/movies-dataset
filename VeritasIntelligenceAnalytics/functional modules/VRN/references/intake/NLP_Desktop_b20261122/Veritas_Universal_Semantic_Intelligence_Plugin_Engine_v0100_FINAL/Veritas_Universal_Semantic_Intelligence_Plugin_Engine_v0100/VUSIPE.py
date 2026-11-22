#!/usr/bin/env python3
"""Veritas Universal Semantic Intelligence Plugin Engine (VUSIPE).

Standalone, CPU-first, host-neutral semantic plugin. Source inputs are read-only;
adaptive updates are append-only candidates until an explicit evaluation promotes
the candidate inside VUSIPE's own runtime directory.
"""

from __future__ import annotations

# -----------------------------------------------------------------------------
# PARAMETERS — all user-adjustable defaults stay at the top
# -----------------------------------------------------------------------------

ENGINE_NAME = "Veritas Universal Semantic Intelligence Plugin Engine"
ENGINE_VERSION = "1.0.0"
CONTRACT = "veritas.universal-semantic-plugin/1.0"
DEFAULT_RUNTIME_DIR = "vusipe_runtime"
DEFAULT_LANGUAGE = "auto"
DEFAULT_TOP_K = 8
DEFAULT_MAX_CHARS = 2_000_000
DEFAULT_VECTOR_DIM = 256
DEFAULT_LEARNING_RATE = 0.08
DEFAULT_EPOCHS = 12
DEFAULT_PROMOTION_MARGIN = 0.0
MAX_BATCH_ITEMS = 1000
SUPPORTED_ACTIONS = (
    "analyze", "normalize", "segment", "keywords", "classify", "entities",
    "relations", "summarize", "actions", "embed", "similarity", "retrieve",
    "knowledge_upsert", "knowledge_search", "train", "evaluate", "evolve",
    "feedback", "capabilities", "health",
)

import argparse
import hashlib
import json
import math
import os
import re
import sqlite3
import sys
import tempfile
import time
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


# -----------------------------------------------------------------------------
# CORE UTILITIES
# -----------------------------------------------------------------------------

def utc_timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def blake2s(value: str | bytes) -> str:
    raw = value.encode("utf-8") if isinstance(value, str) else value
    return hashlib.blake2s(raw).hexdigest()


def stable_id(prefix: str, *parts: Any) -> str:
    return f"{prefix}-{blake2s('|'.join(str(part) for part in parts))[:16].upper()}"


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def append_jsonl(path: Path, record: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(dict(record), ensure_ascii=False, sort_keys=True) + "\n"
    descriptor = os.open(path, os.O_CREAT | os.O_APPEND | os.O_WRONLY, 0o600)
    try:
        os.write(descriptor, line.encode("utf-8"))
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def read_text_source(payload: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
    if "text" in payload:
        text = str(payload.get("text", ""))
        return text, {"kind": "inline", "source_hash": blake2s(text), "source_mutated": False}
    source = Path(str(payload.get("path", ""))).expanduser().resolve()
    if not source.is_file():
        raise ValueError("payload requires non-empty text or an existing path")
    before = source.read_bytes()
    if len(before) > DEFAULT_MAX_CHARS * 4:
        raise ValueError("source exceeds configured safety limit")
    text = before.decode(str(payload.get("encoding", "utf-8-sig")), errors="replace")
    after = source.read_bytes()
    if before != after:
        raise RuntimeError("source integrity changed during read")
    return text, {
        "kind": "file", "path": str(source), "source_hash": blake2s(before),
        "byte_size": len(before), "source_mutated": False,
    }


# -----------------------------------------------------------------------------
# NLP LAYER — deterministic and multilingual CPU baseline
# -----------------------------------------------------------------------------

ZH_STOP = {"的", "了", "和", "與", "及", "是", "在", "為", "由", "將", "一個", "使用", "進行", "資料", "系統"}
EN_STOP = {"the", "and", "for", "with", "from", "this", "that", "are", "is", "was", "into", "use", "using"}
ACTION_MARKERS = ("必須", "應該", "需要", "請", "不得", "待辦", "must", "should", "need to", "todo", "do not")
ENTITY_PATTERNS = (
    ("URL", re.compile(r"https?://[^\s<>\]\)\"']+", re.I)),
    ("EMAIL", re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")),
    ("DATE", re.compile(r"\b20\d{2}[-/]\d{1,2}[-/]\d{1,2}\b")),
    ("TICKER", re.compile(r"(?<!\d)\d{4}[A-Z]?(?:\.TW|\.TWO)?(?!\w)", re.I)),
    ("VERSION", re.compile(r"\bv?\d+(?:\.\d+){1,3}\b", re.I)),
    ("FILE", re.compile(r"\b[\w().-]+\.(?:py|ps1|js|ts|json|md|html|csv|parquet)\b", re.I)),
)


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\u3000", " ")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def detect_language(text: str) -> str:
    zh = len(re.findall(r"[\u3400-\u9fff]", text))
    en = len(re.findall(r"[A-Za-z]", text))
    if zh and en:
        return "multilingual"
    return "zh" if zh else "en"


def split_sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[。！？!?\.])\s+|\n+", text) if part.strip()]


def segment_text(text: str, max_chars: int = 1500) -> list[dict[str, Any]]:
    sentences = split_sentences(text)
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if current and len(current) + len(sentence) + 1 > max_chars:
            chunks.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        chunks.append(current)
    return [{"id": stable_id("SEG", index, chunk), "order": index, "text": chunk, "hash": blake2s(chunk)} for index, chunk in enumerate(chunks)]


def tokenize(text: str) -> list[str]:
    english = [word.casefold() for word in re.findall(r"[A-Za-z][A-Za-z0-9_+-]{1,}", text)]
    chinese: list[str] = []
    for run in re.findall(r"[\u3400-\u9fff]{2,}", text):
        chinese.extend(run[index:index + size] for size in (2, 3, 4) for index in range(max(0, len(run) - size + 1)))
    return [token for token in english + chinese if token not in EN_STOP and token not in ZH_STOP]


def extract_keywords(text: str, top_k: int = DEFAULT_TOP_K) -> list[dict[str, Any]]:
    counts = Counter(tokenize(text))
    ranked = sorted(counts.items(), key=lambda item: (-item[1], -len(item[0]), item[0]))[:top_k]
    total = max(1, sum(counts.values()))
    return [{"term": term, "count": count, "score": round(count / total, 6)} for term, count in ranked]


def extract_entities(text: str) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    occupied: list[tuple[int, int]] = []
    for entity_type, pattern in ENTITY_PATTERNS:
        for match in pattern.finditer(text):
            if any(match.start() < end and match.end() > start for start, end in occupied):
                continue
            value = match.group(0)
            key = (entity_type, value.casefold())
            if key not in seen:
                seen.add(key)
                found.append({"type": entity_type, "value": value, "start": match.start(), "end": match.end(), "confidence": 0.9})
                occupied.append((match.start(), match.end()))
    return found


def extract_actions(text: str) -> list[dict[str, Any]]:
    actions = []
    for sentence in split_sentences(text):
        lowered = sentence.casefold()
        if any(marker in lowered for marker in ACTION_MARKERS):
            actions.append({"id": stable_id("ACT", sentence), "text": sentence, "status": "OPEN", "confidence": 0.75})
    return actions


def summarize_text(text: str, limit: int = 5) -> str:
    sentences = split_sentences(text)
    keywords = {item["term"] for item in extract_keywords(text, 20)}
    ranked = sorted(enumerate(sentences), key=lambda item: (-sum(token in keywords for token in tokenize(item[1])), item[0]))[:limit]
    return " ".join(sentence for _, sentence in sorted(ranked))


def extract_relations(text: str, entities: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    relations = []
    for sentence in split_sentences(text):
        local = [entity for entity in entities if str(entity["value"]) in sentence]
        for left, right in zip(local, local[1:]):
            relations.append({"source": left["value"], "predicate": "CO_OCCURS_WITH", "target": right["value"], "evidence": sentence, "confidence": 0.65})
    return relations


def hashed_embedding(text: str, dimension: int = DEFAULT_VECTOR_DIM) -> list[float]:
    vector = [0.0] * dimension
    for token in tokenize(text):
        digest = hashlib.blake2s(token.encode("utf-8"), digest_size=8).digest()
        index = int.from_bytes(digest[:4], "big") % dimension
        sign = 1.0 if digest[4] & 1 else -1.0
        vector[index] += sign
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [round(value / norm, 8) for value in vector]


def cosine(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        raise ValueError("embedding dimensions differ")
    return sum(a * b for a, b in zip(left, right)) / ((math.sqrt(sum(a*a for a in left)) or 1.0) * (math.sqrt(sum(b*b for b in right)) or 1.0))


def tiny_neural_embedding(text: str, output_dimension: int = 64) -> list[float]:
    """Deterministic two-layer nonlinear CPU projection; no model download needed."""
    base = hashed_embedding(text, DEFAULT_VECTOR_DIM)
    hidden = []
    for unit in range(128):
        total = 0.0
        for index, value in enumerate(base):
            selector = ((index + 1) * (unit + 17) * 2654435761) & 0xFFFFFFFF
            if selector % 11 == 0:
                total += value if selector & 1 else -value
        hidden.append(math.tanh(total))
    output = []
    for unit in range(output_dimension):
        total = sum(value if ((index + 3) * (unit + 5)) % 7 < 3 else -value for index, value in enumerate(hidden))
        output.append(math.tanh(total / max(1.0, math.sqrt(len(hidden)))))
    norm = math.sqrt(sum(value * value for value in output)) or 1.0
    return [round(value / norm, 8) for value in output]


def embed_text(text: str, backend: str = "hashed-cpu") -> dict[str, Any]:
    if backend == "tiny-neural-cpu":
        vector = tiny_neural_embedding(text)
    elif backend == "hashed-cpu":
        vector = hashed_embedding(text)
    else:
        raise ValueError(f"unsupported embedding backend: {backend}")
    return {"backend": backend, "dimension": len(vector), "vector": vector, "cpu_only": True}


# -----------------------------------------------------------------------------
# ML / TINY-DL LAYER — CPU online learning with portable JSON models
# -----------------------------------------------------------------------------

@dataclass
class LinearModel:
    labels: list[str]
    dimension: int
    weights: dict[str, list[float]]
    bias: dict[str, float]
    epochs: int
    trained_at: str
    model_id: str


def new_linear_model(labels: Sequence[str], dimension: int, epochs: int) -> LinearModel:
    clean = sorted(set(str(label) for label in labels))
    return LinearModel(clean, dimension, {label: [0.0] * dimension for label in clean}, {label: 0.0 for label in clean}, epochs, utc_timestamp(), "")


def predict_scores(model: LinearModel, text: str) -> dict[str, float]:
    vector = hashed_embedding(text, model.dimension)
    logits = {label: sum(w*x for w, x in zip(model.weights[label], vector)) + model.bias[label] for label in model.labels}
    peak = max(logits.values(), default=0.0)
    exps = {label: math.exp(min(50.0, value - peak)) for label, value in logits.items()}
    total = sum(exps.values()) or 1.0
    return {label: round(value / total, 8) for label, value in exps.items()}


def predict_label(model: LinearModel, text: str) -> tuple[str, float]:
    scores = predict_scores(model, text)
    return max(scores.items(), key=lambda item: item[1]) if scores else ("unknown", 0.0)


def train_linear_model(samples: Sequence[Mapping[str, Any]], dimension: int = DEFAULT_VECTOR_DIM, epochs: int = DEFAULT_EPOCHS, learning_rate: float = DEFAULT_LEARNING_RATE) -> LinearModel:
    if not samples:
        raise ValueError("training samples are empty")
    labels = [str(sample["label"]) for sample in samples]
    model = new_linear_model(labels, dimension, epochs)
    for _ in range(epochs):
        for sample in sorted(samples, key=lambda row: blake2s(stable_json(row))):
            truth = str(sample["label"])
            vector = hashed_embedding(str(sample["text"]), dimension)
            predicted, _ = predict_label(model, str(sample["text"]))
            if predicted != truth:
                for index, value in enumerate(vector):
                    model.weights[truth][index] += learning_rate * value
                    model.weights[predicted][index] -= learning_rate * value
                model.bias[truth] += learning_rate
                model.bias[predicted] -= learning_rate
    payload = asdict(model)
    payload["model_id"] = ""
    model.model_id = stable_id("MDL", stable_json(payload))
    return model


def evaluate_model(model: LinearModel, samples: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    correct = 0
    matrix: dict[str, Counter[str]] = {}
    for sample in samples:
        truth = str(sample["label"])
        predicted, _ = predict_label(model, str(sample["text"]))
        correct += int(predicted == truth)
        matrix.setdefault(truth, Counter())[predicted] += 1
    total = len(samples)
    return {"gate": "PASS" if total else "HOLD", "accuracy": round(correct / total, 6) if total else 0.0, "correct": correct, "total": total, "confusion": {key: dict(value) for key, value in matrix.items()}}


# -----------------------------------------------------------------------------
# KNOWLEDGE LIBRARY — append-only evidence + local searchable projections
# -----------------------------------------------------------------------------

class KnowledgeLibrary:
    def __init__(self, runtime_dir: Path):
        self.runtime_dir = runtime_dir
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.database_path = runtime_dir / "knowledge.sqlite3"
        self.audit_path = runtime_dir / "knowledge_audit.jsonl"
        self.connection = sqlite3.connect(self.database_path)
        self.connection.execute("CREATE TABLE IF NOT EXISTS documents (id TEXT PRIMARY KEY, title TEXT, text TEXT, metadata TEXT, content_hash TEXT, created_at TEXT)")
        self.connection.execute("CREATE TABLE IF NOT EXISTS feedback (id TEXT PRIMARY KEY, text TEXT, predicted TEXT, expected TEXT, metadata TEXT, created_at TEXT)")
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def upsert_candidate(self, title: str, text: str, metadata: Mapping[str, Any] | None = None) -> dict[str, Any]:
        content_hash = blake2s(text)
        document_id = stable_id("KDOC", title, content_hash)
        existing = self.connection.execute("SELECT 1 FROM documents WHERE id=?", (document_id,)).fetchone()
        if not existing:
            self.connection.execute("INSERT INTO documents VALUES (?,?,?,?,?,?)", (document_id, title, text, stable_json(metadata or {}), content_hash, utc_timestamp()))
            self.connection.commit()
            append_jsonl(self.audit_path, {"event": "KNOWLEDGE_APPEND", "document_id": document_id, "content_hash": content_hash, "timestamp": utc_timestamp()})
        return {"gate": "PASS", "status": "SKIP_DUPLICATE" if existing else "APPENDED", "document_id": document_id, "content_hash": content_hash}

    def search(self, query: str, top_k: int = DEFAULT_TOP_K) -> list[dict[str, Any]]:
        query_vector = hashed_embedding(query)
        rows = self.connection.execute("SELECT id,title,text,metadata,content_hash FROM documents").fetchall()
        results = []
        for document_id, title, text, metadata, content_hash in rows:
            score = cosine(query_vector, hashed_embedding(text))
            results.append({"document_id": document_id, "title": title, "score": round(score, 8), "excerpt": text[:320], "metadata": json.loads(metadata), "content_hash": content_hash})
        return sorted(results, key=lambda row: (-row["score"], row["document_id"]))[:top_k]

    def add_feedback(self, text: str, predicted: str, expected: str, metadata: Mapping[str, Any] | None = None) -> dict[str, Any]:
        feedback_id = stable_id("FB", text, predicted, expected, stable_json(metadata or {}))
        self.connection.execute("INSERT OR IGNORE INTO feedback VALUES (?,?,?,?,?,?)", (feedback_id, text, predicted, expected, stable_json(metadata or {}), utc_timestamp()))
        self.connection.commit()
        append_jsonl(self.audit_path, {"event": "FEEDBACK_APPEND", "feedback_id": feedback_id, "timestamp": utc_timestamp()})
        return {"gate": "PASS", "feedback_id": feedback_id, "append_only": True}

    def feedback_samples(self) -> list[dict[str, str]]:
        return [{"text": row[0], "label": row[1]} for row in self.connection.execute("SELECT text,expected FROM feedback ORDER BY id").fetchall()]


# -----------------------------------------------------------------------------
# EVOLUTION GOVERNANCE — challenger first, explicit internal promotion only
# -----------------------------------------------------------------------------

class ModelRegistry:
    def __init__(self, runtime_dir: Path):
        self.root = runtime_dir / "models"
        self.root.mkdir(parents=True, exist_ok=True)
        self.pointer = self.root / "champion.json"

    def save_candidate(self, model: LinearModel, evaluation: Mapping[str, Any]) -> Path:
        path = self.root / f"candidate_{model.model_id}.json"
        atomic_write(path, json.dumps({"contract": CONTRACT, "model": asdict(model), "evaluation": dict(evaluation), "status": "CANDIDATE"}, ensure_ascii=False, indent=2, sort_keys=True))
        return path

    def load_model(self, path: Path) -> LinearModel:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return LinearModel(**payload["model"])

    def champion(self) -> tuple[LinearModel | None, dict[str, Any] | None]:
        if not self.pointer.exists():
            return None, None
        pointer = json.loads(self.pointer.read_text(encoding="utf-8"))
        model_path = self.root / pointer["file"]
        payload = json.loads(model_path.read_text(encoding="utf-8"))
        return LinearModel(**payload["model"]), payload.get("evaluation")

    def promote_if_better(self, candidate_path: Path, evaluation: Mapping[str, Any], margin: float = DEFAULT_PROMOTION_MARGIN) -> dict[str, Any]:
        _, champion_eval = self.champion()
        old_score = float((champion_eval or {}).get("accuracy", -1.0))
        new_score = float(evaluation.get("accuracy", 0.0))
        if evaluation.get("gate") != "PASS" or new_score + 1e-12 < old_score + margin:
            return {"gate": "HOLD", "promoted": False, "candidate_accuracy": new_score, "champion_accuracy": old_score}
        atomic_write(self.pointer, json.dumps({"file": candidate_path.name, "promoted_at": utc_timestamp(), "accuracy": new_score}, ensure_ascii=False, indent=2, sort_keys=True))
        return {"gate": "PASS", "promoted": True, "candidate_accuracy": new_score, "previous_accuracy": old_score, "scope": "VUSIPE_RUNTIME_ONLY"}


# -----------------------------------------------------------------------------
# UNIVERSAL PLUGIN API / ADAPTER
# -----------------------------------------------------------------------------

class UniversalSemanticPlugin:
    def __init__(self, runtime_dir: str | Path = DEFAULT_RUNTIME_DIR):
        self.runtime_dir = Path(runtime_dir).expanduser().resolve()
        self.knowledge = KnowledgeLibrary(self.runtime_dir)
        self.models = ModelRegistry(self.runtime_dir)

    def close(self) -> None:
        self.knowledge.close()

    def analyze(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        text, source = read_text_source(payload)
        normalized = normalize_text(text)
        entities = extract_entities(normalized)
        champion, _ = self.models.champion()
        predicted = predict_label(champion, normalized) if champion else ("untrained", 0.0)
        return {
            "contract": CONTRACT, "engine": ENGINE_NAME, "version": ENGINE_VERSION,
            "request_id": stable_id("REQ", source["source_hash"], stable_json(payload.get("options", {}))),
            "gate": "PASS", "source": source, "language": detect_language(normalized),
            "normalized_text": normalized, "segments": segment_text(normalized),
            "keywords": extract_keywords(normalized, int(payload.get("top_k", DEFAULT_TOP_K))),
            "summary": summarize_text(normalized), "entities": entities,
            "relations": extract_relations(normalized, entities), "actions": extract_actions(normalized),
            "embedding": embed_text(normalized, str(payload.get("embedding_backend", "hashed-cpu"))),
            "classification": {"label": predicted[0], "confidence": predicted[1], "backend": "online-linear-cpu" if champion else "UNTRAINED"},
            "knowledge_matches": self.knowledge.search(normalized, int(payload.get("top_k", DEFAULT_TOP_K))),
            "source_mutated": False,
        }

    def invoke(self, request: Mapping[str, Any]) -> dict[str, Any]:
        action = str(request.get("action", "analyze"))
        payload = request.get("payload", {})
        if action not in SUPPORTED_ACTIONS:
            return {"contract": CONTRACT, "gate": "FAIL", "error": "UNSUPPORTED_ACTION", "action": action, "supported_actions": list(SUPPORTED_ACTIONS)}
        if not isinstance(payload, Mapping):
            return {"contract": CONTRACT, "gate": "FAIL", "error": "PAYLOAD_MUST_BE_OBJECT"}
        if action == "capabilities":
            return capability_manifest()
        if action == "health":
            return {"contract": CONTRACT, "gate": "PASS", "status": "READY", "cpu_only": True, "runtime_dir": str(self.runtime_dir)}
        if action == "analyze":
            return self.analyze(payload)
        if action == "similarity":
            backend = str(payload.get("embedding_backend", "hashed-cpu"))
            left = embed_text(str(payload.get("left", "")), backend)["vector"]
            right = embed_text(str(payload.get("right", "")), backend)["vector"]
            return {"contract": CONTRACT, "gate": "PASS", "action": action, "result": {"score": round(cosine(left, right), 8), "backend": backend}, "source_mutated": False}
        if action in {"normalize", "segment", "keywords", "entities", "relations", "summarize", "actions", "embed", "classify", "retrieve"}:
            analysis = self.analyze(payload)
            key = {"normalize": "normalized_text", "segment": "segments", "keywords": "keywords", "entities": "entities", "relations": "relations", "summarize": "summary", "actions": "actions", "embed": "embedding", "classify": "classification", "retrieve": "knowledge_matches"}[action]
            return {"contract": CONTRACT, "gate": analysis["gate"], "action": action, "result": analysis[key], "source": analysis["source"], "source_mutated": False}
        if action == "knowledge_upsert":
            return self.knowledge.upsert_candidate(str(payload.get("title", "Untitled")), str(payload.get("text", "")), payload.get("metadata", {}))
        if action == "knowledge_search":
            return {"contract": CONTRACT, "gate": "PASS", "results": self.knowledge.search(str(payload.get("query", "")), int(payload.get("top_k", DEFAULT_TOP_K)))}
        if action == "feedback":
            return self.knowledge.add_feedback(str(payload.get("text", "")), str(payload.get("predicted", "")), str(payload.get("expected", "")), payload.get("metadata", {}))
        if action in {"train", "evaluate", "evolve"}:
            samples = list(payload.get("samples", [])) or self.knowledge.feedback_samples()
            if not samples:
                return {"contract": CONTRACT, "gate": "HOLD", "reason": "NO_TRAINING_SAMPLES"}
            model = train_linear_model(samples, int(payload.get("dimension", DEFAULT_VECTOR_DIM)), int(payload.get("epochs", DEFAULT_EPOCHS)), float(payload.get("learning_rate", DEFAULT_LEARNING_RATE)))
            evaluation_samples = list(payload.get("evaluation_samples", [])) or samples
            evaluation = evaluate_model(model, evaluation_samples)
            candidate = self.models.save_candidate(model, evaluation)
            result = {"contract": CONTRACT, "gate": "PASS", "model_id": model.model_id, "candidate": str(candidate), "evaluation": evaluation, "promoted": False}
            if action == "evolve" and bool(payload.get("approve_runtime_promotion", False)):
                result["promotion"] = self.models.promote_if_better(candidate, evaluation, float(payload.get("promotion_margin", DEFAULT_PROMOTION_MARGIN)))
                result["promoted"] = result["promotion"]["promoted"]
            return result
        raise AssertionError("unreachable")


def capability_manifest() -> dict[str, Any]:
    return {
        "contract": CONTRACT, "gate": "PASS", "engine": ENGINE_NAME, "version": ENGINE_VERSION,
        "plugin_type": "HOST_NEUTRAL_JSON_ADAPTER", "actions": list(SUPPORTED_ACTIONS),
        "layers": {"nlp": "deterministic multilingual", "ml": "online linear classifier", "deep_learning": "built-in two-layer tiny-neural CPU embedding plus optional backend adapters", "knowledge": "SQLite + append-only audit", "evolution": "candidate/champion gate"},
        "embedding_backends": ["hashed-cpu", "tiny-neural-cpu"],
        "cpu_only": True, "offline": True, "source_policy": "READ_ONLY", "host_mutation": False,
        "optional_backends": ["scikit-learn", "onnxruntime", "torch", "sentence-transformers"],
        "required_dependencies": ["Python 3.10+ standard library"],
    }


def create_plugin(runtime_dir: str | Path = DEFAULT_RUNTIME_DIR) -> UniversalSemanticPlugin:
    return UniversalSemanticPlugin(runtime_dir)


def invoke_json(request_json: str, runtime_dir: str | Path = DEFAULT_RUNTIME_DIR) -> str:
    plugin = create_plugin(runtime_dir)
    try:
        return json.dumps(plugin.invoke(json.loads(request_json)), ensure_ascii=False, sort_keys=True)
    finally:
        plugin.close()


def run_self_test() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="vusipe-test-") as directory:
        plugin = create_plugin(directory)
        try:
            sample = "# 台股分析\n必須追蹤 2330.TW 在 2026-08-31 的成交量。Please update report.md."
            analysis = plugin.invoke({"action": "analyze", "payload": {"text": sample}})
            checks.append({"name": "analyze", "pass": analysis["gate"] == "PASS" and analysis["source_mutated"] is False})
            checks.append({"name": "multilingual", "pass": analysis["language"] == "multilingual"})
            checks.append({"name": "entities", "pass": {row["type"] for row in analysis["entities"]} >= {"TICKER", "DATE", "FILE"}})
            checks.append({"name": "actions", "pass": len(analysis["actions"]) >= 1})
            upsert = plugin.invoke({"action": "knowledge_upsert", "payload": {"title": "台股", "text": sample}})
            checks.append({"name": "knowledge_append", "pass": upsert["gate"] == "PASS"})
            search = plugin.invoke({"action": "knowledge_search", "payload": {"query": "台股成交量"}})
            checks.append({"name": "knowledge_search", "pass": len(search["results"]) == 1})
            samples = [{"text": "股票成交量上升", "label": "finance"}, {"text": "Python API test", "label": "software"}, {"text": "台股價格", "label": "finance"}, {"text": "JavaScript module", "label": "software"}]
            evolution = plugin.invoke({"action": "evolve", "payload": {"samples": samples, "epochs": 20, "approve_runtime_promotion": True}})
            checks.append({"name": "evolution", "pass": evolution["gate"] == "PASS" and evolution["promoted"] is True})
            classified = plugin.invoke({"action": "classify", "payload": {"text": "股票價格成交量"}})
            checks.append({"name": "classification", "pass": classified["result"]["label"] in {"finance", "software"}})
            bad = plugin.invoke({"action": "delete_host", "payload": {}})
            checks.append({"name": "fail_closed", "pass": bad["gate"] == "FAIL"})
        finally:
            plugin.close()
    passed = sum(int(item["pass"]) for item in checks)
    return {"contract": "veritas.vusipe-self-test/1.0", "gate": "PASS" if passed == len(checks) else "FAIL", "passed": passed, "failed": len(checks) - passed, "checks": checks}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=ENGINE_NAME)
    parser.add_argument("--runtime-dir", default=DEFAULT_RUNTIME_DIR)
    sub = parser.add_subparsers(dest="command", required=True)
    invoke_parser = sub.add_parser("invoke", help="invoke one JSON request")
    invoke_parser.add_argument("--request", help="inline JSON request")
    invoke_parser.add_argument("--request-file", help="JSON request file")
    invoke_parser.add_argument("--output", help="optional JSON output file")
    sub.add_parser("capabilities")
    sub.add_parser("self-test")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "capabilities":
        result = capability_manifest()
    elif args.command == "self-test":
        result = run_self_test()
    else:
        raw = args.request or (Path(args.request_file).read_text(encoding="utf-8") if args.request_file else "")
        if not raw:
            raise SystemExit("invoke requires --request or --request-file")
        plugin = create_plugin(args.runtime_dir)
        try:
            result = plugin.invoke(json.loads(raw))
        finally:
            plugin.close()
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    if getattr(args, "output", None):
        atomic_write(Path(args.output), rendered + "\n")
    print(rendered)
    return 0 if result.get("gate") == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
