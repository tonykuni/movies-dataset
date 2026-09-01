"""Chunked translation with local memory and explicit, supported backends."""

from __future__ import annotations

import hashlib
import importlib.util
import os
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Callable, Iterable

from .knowledge import FENCED_CODE_RE


SUPPORTED_BACKENDS = {"argos", "google_cloud", "ollama"}


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class TranslationMemory:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(str(path), check_same_thread=False, timeout=30)
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS translations (
                cache_key TEXT PRIMARY KEY,
                backend TEXT NOT NULL,
                source_language TEXT NOT NULL,
                target_language TEXT NOT NULL,
                source_sha256 TEXT NOT NULL,
                translated_text TEXT NOT NULL,
                created REAL NOT NULL,
                accessed REAL NOT NULL
            )
            """
        )
        self._connection.commit()
        self._lock = threading.RLock()

    @staticmethod
    def key(backend: str, source: str, target: str, text: str) -> str:
        return _hash("\0".join((backend, source, target, text)))

    def get(self, key: str) -> str | None:
        with self._lock:
            row = self._connection.execute("SELECT translated_text FROM translations WHERE cache_key=?", (key,)).fetchone()
            if row:
                self._connection.execute("UPDATE translations SET accessed=? WHERE cache_key=?", (time.time(), key))
                self._connection.commit()
        return str(row[0]) if row else None

    def set(self, key: str, backend: str, source: str, target: str, text: str, translated: str) -> None:
        now = time.time()
        with self._lock:
            self._connection.execute(
                "INSERT OR REPLACE INTO translations VALUES(?,?,?,?,?,?,?,?)",
                (key, backend, source, target, _hash(text), translated, now, now),
            )
            self._connection.commit()

    def close(self) -> None:
        with self._lock:
            self._connection.close()


def _chunk_exact(text: str, maximum: int) -> Iterable[tuple[int, int, str]]:
    start = 0
    while start < len(text):
        end = min(len(text), start + maximum)
        if end < len(text):
            candidates = [text.rfind(mark, start + maximum // 2, end) for mark in ("\n", "。", "！", "？", ". ", "! ", "? ")]
            boundary = max(candidates)
            if boundary > start:
                end = boundary + 1
        yield start, end, text[start:end]
        start = end


def _prose_and_code_parts(text: str, preserve_code: bool) -> Iterable[tuple[int, int, str, bool]]:
    if not preserve_code:
        yield 0, len(text), text, False
        return
    cursor = 0
    for match in FENCED_CODE_RE.finditer(text):
        if match.start() > cursor:
            yield cursor, match.start(), text[cursor : match.start()], False
        yield match.start(), match.end(), text[match.start() : match.end()], True
        cursor = match.end()
    if cursor < len(text):
        yield cursor, len(text), text[cursor:], False


class TranslationService:
    def __init__(self, config: dict[str, Any], memory: TranslationMemory) -> None:
        self.config = config
        self.memory = memory

    def translate(
        self,
        text: str,
        backend: str | None = None,
        source_language: str | None = None,
        target_language: str | None = None,
        ollama_provider: Callable[[str, str, str], str] | None = None,
        max_chunk_chars: int | None = None,
    ) -> dict[str, Any]:
        if not self.config["enabled"]:
            raise RuntimeError("Translation is disabled; set translation.enabled=true in a copied config")
        backend = backend or str(self.config["default_backend"])
        if backend == "google_web":
            raise RuntimeError("Automating the free Google Translate website is intentionally unsupported; use google_cloud or a local backend")
        if backend not in SUPPORTED_BACKENDS:
            raise ValueError(f"Unsupported translation backend: {backend}")
        source = source_language or str(self.config["source_language"])
        target = target_language or str(self.config["target_language"])
        maximum = int(max_chunk_chars or self.config["max_chunk_chars"])
        if not (100 <= maximum <= 30_000):
            raise ValueError("max_chunk_chars must be between 100 and 30000")

        provider = self._provider(backend, source, target, ollama_provider)
        chunks: list[dict[str, Any]] = []
        translated_parts: list[str] = []
        chunk_index = 0
        for part_start, _, part_text, is_code in _prose_and_code_parts(text, bool(self.config["preserve_code"])):
            for local_start, local_end, chunk in _chunk_exact(part_text, maximum):
                chunk_index += 1
                absolute_start = part_start + local_start
                absolute_end = part_start + local_end
                if is_code or not chunk.strip():
                    translated = chunk
                    cached = False
                    status = "preserved_code" if is_code else "preserved_whitespace"
                else:
                    key = self.memory.key(backend, source, target, chunk)
                    previous = self.memory.get(key)
                    if previous is not None:
                        translated = previous
                        cached = True
                    else:
                        # Translation backends commonly trim leading/trailing newlines.
                        # Preserve those separators locally so independently translated
                        # chunks cannot be concatenated into a different structure.
                        leading_size = len(chunk) - len(chunk.lstrip())
                        trailing_size = len(chunk) - len(chunk.rstrip())
                        core_end = len(chunk) - trailing_size if trailing_size else len(chunk)
                        leading = chunk[:leading_size]
                        trailing = chunk[core_end:]
                        core = chunk[leading_size:core_end]
                        translated = leading + provider(core) + trailing
                        self.memory.set(key, backend, source, target, chunk, translated)
                        cached = False
                    status = "translated"
                translated_parts.append(translated)
                chunks.append(
                    {
                        "chunk_id": f"TR-{chunk_index:06d}",
                        "source_span": {"start": absolute_start, "end": absolute_end},
                        "source_text": chunk,
                        "source_sha256": _hash(chunk),
                        "translated_text": translated,
                        "translated_sha256": _hash(translated),
                        "status": status,
                        "cache_hit": cached,
                    }
                )
        source_reconstructed = "".join(item["source_text"] for item in chunks)
        return {
            "backend": backend,
            "source_language": source,
            "target_language": target,
            "translated_text": "".join(translated_parts),
            "chunks": chunks,
            "completeness": {
                "source_characters": len(text),
                "chunk_source_characters": len(source_reconstructed),
                "exact_source_reconstruction": source_reconstructed == text,
                "source_sha256": _hash(text),
                "chunk_source_sha256": _hash(source_reconstructed),
            },
        }

    def _provider(
        self,
        backend: str,
        source: str,
        target: str,
        ollama_provider: Callable[[str, str, str], str] | None,
    ) -> Callable[[str], str]:
        if backend == "argos":
            if importlib.util.find_spec("argostranslate") is None:
                raise RuntimeError("Install the 'translate' extra and a local Argos language package")
            from argostranslate import translate

            languages = translate.get_installed_languages()
            source_language = next((item for item in languages if item.code.lower() == source.lower()), None)
            target_language = next((item for item in languages if item.code.lower() == target.lower()), None)
            if source_language is None or target_language is None:
                raise RuntimeError(f"Argos language package is not installed for {source}->{target}")
            translation = source_language.get_translation(target_language)
            return translation.translate
        if backend == "ollama":
            if ollama_provider is None:
                raise RuntimeError("Ollama translation provider is unavailable")
            return lambda value: ollama_provider(value, source, target)
        try:
            google_translate_spec = importlib.util.find_spec("google.cloud.translate_v3")
        except (ImportError, ModuleNotFoundError):
            google_translate_spec = None
        if google_translate_spec is None:
            raise RuntimeError("Install the 'translate' extra to use Google Cloud Translation")
        project = os.environ.get(str(self.config["google_cloud_project_env"]), "")
        if not project:
            raise RuntimeError(f"Missing project environment variable: {self.config['google_cloud_project_env']}")
        from google.cloud import translate_v3

        client = translate_v3.TranslationServiceClient()
        parent = f"projects/{project}/locations/{self.config['google_cloud_location']}"

        def google_translate(value: str) -> str:
            response = client.translate_text(
                request={
                    "parent": parent,
                    "contents": [value],
                    "mime_type": "text/plain",
                    "source_language_code": source,
                    "target_language_code": target,
                }
            )
            return str(response.translations[0].translated_text)

        return google_translate
