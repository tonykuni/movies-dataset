"""Optional Tier 2-4 adapters, loaded only when invoked."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from .model_pool import LazyModelPool


class OptionalNLPAdapters:
    def __init__(self, config: dict[str, Any], pool: LazyModelPool) -> None:
        self.config = config
        self.pool = pool

    def spacy_entities(self, text: str, language: str) -> list[dict[str, Any]]:
        model_name = "zh_core_web_sm" if language in {"zh", "mixed"} else "en_core_web_sm"

        def loader() -> Any:
            try:
                import spacy
            except ImportError as exc:
                raise RuntimeError("Install the 'nlp' extra to enable spaCy NER") from exc
            try:
                return spacy.load(model_name, disable=["parser", "lemmatizer", "textcat"])
            except OSError as exc:
                raise RuntimeError(f"spaCy model is not installed locally: {model_name}") from exc

        nlp = self.pool.get_or_load(f"spacy:{model_name}", loader, estimated_mb=550, heavy=False)
        doc = nlp(text)
        return [
            {"text": ent.text, "label": ent.label_, "start": ent.start_char, "end": ent.end_char, "backend": model_name}
            for ent in doc.ents
        ]

    def embeddings(self, texts: list[str]) -> list[list[float]]:
        cfg = self.config["deep"]
        model_name = str(cfg["embedding_model"])

        def loader() -> Any:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise RuntimeError("Install the 'deep' extra to enable embeddings") from exc
            return SentenceTransformer(
                model_name,
                device=str(cfg["embedding_device"]),
                local_files_only=bool(cfg["local_files_only"]),
            )

        model = self.pool.get_or_load(
            f"embedding:{model_name}",
            loader,
            estimated_mb=2500 if "bge-m3" in model_name.lower() else 1200,
            heavy=True,
        )
        vectors = model.encode(texts, batch_size=min(16, len(texts)), normalize_embeddings=True, show_progress_bar=False)
        return vectors.tolist() if hasattr(vectors, "tolist") else [list(row) for row in vectors]

    def ollama_generate(self, prompt: str, system: str, json_mode: bool = False) -> dict[str, Any]:
        cfg = self.config["deep"]
        payload: dict[str, Any] = {
            "model": cfg["ollama_model"],
            "prompt": prompt,
            "system": system,
            "stream": False,
            "keep_alive": cfg["ollama_keep_alive"],
            "options": {"temperature": 0.1, "num_ctx": 4096},
        }
        if json_mode:
            payload["format"] = "json"
        request = urllib.request.Request(
            str(cfg["ollama_url"]).rstrip("/") + "/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=float(cfg["ollama_timeout_seconds"])) as response:
                result = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Local Ollama request failed: {exc}") from exc
        return result


def safe_extract_json(raw: str) -> dict[str, Any]:
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        raw = "\n".join(lines[1:-1]) if len(lines) >= 3 else raw
        if raw.lstrip().startswith("json"):
            raw = raw.lstrip()[4:].lstrip()
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("Model output is not valid JSON") from exc
    if not isinstance(value, dict):
        raise ValueError("Model JSON output must be an object")
    return value

