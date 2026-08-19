#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VIA Summarizer Engine
=====================

CPU-first, local-only multilingual summarization engine for Traditional Chinese,
Simplified Chinese and English.  It preserves raw evidence, builds a governed
keyword library, produces exactly four evidence-linked bullets, and degrades
gracefully when optional NLP/LLM packages are unavailable.

Governance defaults
-------------------
* No network calls.  Ollama is accepted only on loopback.
* Raw text and normalized text are stored separately.
* SQLite records are append-only; completed work is resumed by content hash.
* Generated numbers must be traceable to the source evidence.
* Candidate terms never enter the approved registry automatically unless the
  explicit --auto-promote flag is supplied.
* No component activation or canonical VIA mutation is performed.

Python: 3.10+
License of this file: MIT
"""

from __future__ import annotations

# =============================================================================
# def 00 PARAMETERS — all user-adjustable values are kept in this section
# =============================================================================

ENGINE_NAME = "VIA_SummarizerEngine"
ENGINE_VERSION = "1.2.0"
ENGINE_CLASSIFICATION = "ENGINE"
ENGINE_OWNER = "VIA_SSOT_MANAGER"
ENGINE_GOVERNANCE = "APPEND_ONLY_NO_DELETE_NO_OVERWRITE"
DEFAULT_LANGUAGE = "zh-TW"
SUPPORTED_LANGUAGES = ("auto", "zh-TW", "zh-CN", "en", "mixed")
DEFAULT_ENCODING = "utf-8-sig"
DEFAULT_DB_PATH = "VIA_Summarizer_SSOT.sqlite"
DEFAULT_OUTPUT_DIR = "VIA_Summarizer_Output"
DEFAULT_TEMP_ROOT = "VIA_Summarizer_TEMP"
DEFAULT_INPUT_GLOB = "**/*"
DEFAULT_OUTPUT_FORMATS = ("json", "md", "csv")
SUPPORTED_INPUT_SUFFIXES = (
    ".txt", ".md", ".markdown", ".json", ".jsonl", ".csv", ".tsv",
    ".html", ".htm", ".xml", ".yaml", ".yml", ".log", ".sql",
    ".py", ".ps1", ".js", ".c", ".h", ".ipynb", ".pdf", ".docx",
    ".eml", ".xlsx",
)
DEFAULT_SUMMARY_BULLETS = 4
DEFAULT_BULLET_CHAR_LIMIT_ZH = 70
DEFAULT_BULLET_WORD_LIMIT_EN = 35
DEFAULT_KEYWORD_LIMIT = 20
DEFAULT_CANDIDATE_SENTENCES = 16
DEFAULT_CHUNK_CHARACTERS = 12_000
DEFAULT_CHUNK_OVERLAP_SENTENCES = 2
DEFAULT_LLM_CONTEXT = 4_096
DEFAULT_LLM_MAX_TOKENS = 900
DEFAULT_LLM_TEMPERATURE = 0.1
DEFAULT_LLM_MODEL_PATH = ""
DEFAULT_OLLAMA_MODEL = ""
DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
DEFAULT_EMBEDDING_MODEL_PATH = ""
DEFAULT_FASTTEXT_MODEL_PATH = ""
DEFAULT_SPACY_ZH_MODEL = "zh_core_web_sm"
DEFAULT_SPACY_EN_MODEL = "en_core_web_sm"
DEFAULT_CPU_RESERVE_CORES = 1
DEFAULT_MAX_CPU_PERCENT = 88.0
DEFAULT_MAX_MEMORY_PERCENT = 85.0
DEFAULT_MIN_FREE_MEMORY_MB = 1_024
DEFAULT_MIN_FREE_DISK_MB = 2_048
DEFAULT_BATCH_SIZE = 8
DEFAULT_BUSY_RETRY_SECONDS = 1.0
DEFAULT_BUSY_RETRIES = 5
DEFAULT_TERM_MIN_DOCUMENTS = 3
DEFAULT_TERM_MIN_EXTRACTORS = 2
DEFAULT_TERM_ALIAS_SIMILARITY = 92.0
DEFAULT_PROMOTION_THRESHOLD = 0.62
DEFAULT_AUTO_PROMOTE = False
DEFAULT_RESUME = True
DEFAULT_STRICT_NUMERIC_EVIDENCE = True
DEFAULT_USE_LLM = False
DEFAULT_LLM_BACKEND = "auto"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_RANDOM_SEED = 42
DEFAULT_KEEP_TEMP = False
DEFAULT_PARQUET_COMPRESSION = "zstd"
DEFAULT_SQLITE_BUSY_TIMEOUT_MS = 30_000
DEFAULT_WAL_AUTOCHECKPOINT = 1_000

ENVIRONMENT_THREAD_KEYS = (
    "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
    "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "BLIS_NUM_THREADS",
    "TOKENIZERS_PARALLELISM",
)

SUMMARY_ROLES = (
    ("core_conclusion", "核心結論", "Core Conclusion"),
    ("facts_and_numbers", "重要事實或數據", "Key Facts Or Data"),
    ("impact_risk_opportunity", "影響、風險或機會", "Impact, Risk Or Opportunity"),
    ("next_step_or_gap", "下一步或待驗證事項", "Next Step Or Information Gap"),
)

PROMOTION_WEIGHTS = {
    "document_frequency": 0.35,
    "mean_keyword_score": 0.30,
    "entity_confidence": 0.20,
    "recency_score": 0.15,
}

KNOWN_ACRONYMS = frozenset({
    "AI", "API", "AUM", "BERT", "CAPEX", "CPU", "CSV", "DRAM", "EPS", "ETF",
    "GB", "GDP", "GGUF", "GPU", "HTML", "JSON", "KV", "LLM", "MB", "NER",
    "NLP", "OCR", "ONNX", "PDF", "PMI", "POS", "Q4", "RAM", "RAG", "REST",
    "SQL", "SSOT", "TF-IDF", "TWSE", "TPEX", "UI", "URL", "UTF", "XML",
})

KNOWN_BRAND_CASE = {
    "fasttext": "fastText", "gensim": "Gensim", "hanlp": "HanLP", "jieba": "jieba",
    "keybert": "KeyBERT", "llama.cpp": "llama.cpp", "ollama": "Ollama",
    "opencc": "OpenCC", "pytextrank": "PyTextRank", "spacy": "spaCy",
    "summa": "summa", "sumy": "Sumy", "yake": "YAKE",
}

STOPWORDS_ZH = frozenset(
    "的 了 是 在 與 和 及 或 而 被 把 將 由 對 於 中 之 這 那 一個 我們 你們 他們 "
    "可以 需要 使用 進行 已經 沒有 不是 以及 其中 目前 相關 內容 資料 問題 方法 "
    "如果 因此 但是 同時 可能 主要 其 也 都 更 最 來 去 上 下 後 前".split()
)
STOPWORDS_EN = frozenset(
    "a an and are as at be been being but by can could did do does for from had "
    "has have he her hers him his how i if in into is it its may might more most "
    "not of on or our ours she should so than that the their theirs them then there "
    "these they this those to us was we were what when where which who why will with "
    "would you your yours text texts best primary function functions use used using word words "
    "sentence sentences document documents like based run runs practice https http www main uses".split()
)

CJK_BOUNDARY_TERMS = tuple(sorted({
    "下一步", "待確認", "待驗證", "主要", "目前", "其中", "因此", "但是", "同時",
    "可以", "需要", "必須", "應該", "可能", "已經", "沒有", "不是", "進行", "使用",
    "公布", "表示", "指出", "認為", "建議", "確認", "核對", "關於", "由於", "因為",
    "以及", "或者", "如果", "透過", "針對", "根據", "包含", "提供", "保留", "建立",
    "一個", "我們", "你們", "他們", "這些", "那些", "這個", "那個", "其餘",
    "的", "了", "是", "在", "與", "和", "及", "或", "而", "被", "把", "將", "由",
    "對", "於", "中", "之", "其", "也", "都", "更", "最", "後", "前",
}, key=len, reverse=True))

BOILERPLATE_PATTERNS = (
    r"^if you tell me\b", r"^would you like\b", r"^do you want\b", r"^請告訴我",
    r"^是否要我", r"^https?://", r"^from\s+\w+\s+import\b", r"^import\s+\w+",
    r"tokens?kv cache ram required", r"請謹慎使用程式碼", r"^sources?:$",
)

ACTION_PATTERNS = (
    r"下一步", r"待確認", r"待驗證", r"建議", r"應(?:該)?", r"必須", r"需要",
    r"follow[- ]?up", r"next step", r"action", r"must", r"should", r"need to",
)
RISK_PATTERNS = (
    r"風險", r"影響", r"機會", r"警告", r"失敗", r"異常", r"不足", r"缺失",
    r"risk", r"impact", r"opportunit", r"warning", r"fail", r"error", r"gap",
)
NUMBER_PATTERN = r"(?<![A-Za-z0-9_])[-+]?\d[\d,]*(?:\.\d+)?(?:%|％|bps?|BP|億|萬|元|美元|年|月|日|GB|MB|KB|x)?"
DATE_PATTERN = r"\b(?:19|20)\d{2}[-/]\d{1,2}[-/]\d{1,2}\b|\b(?:19|20)\d{2}年\d{1,2}月\d{1,2}日\b"
TICKER_PATTERN = r"(?:\b\d{4}[A-Z]?\.(?:TW|TWO)\b|(?<!\w)\^[A-Z0-9]+\b)"

LIBRARY_PORTFOLIO = {
    # Summarization, parsing and local inference (Top 20 family)
    "llama.cpp": ("llama_cpp", "local_llm", "GGUF local inference"),
    "Ollama": (None, "local_llm", "Loopback REST runtime"),
    "Transformers": ("transformers", "local_llm", "Local transformer pipelines"),
    "Optimum": ("optimum", "optimization", "ONNX/Intel optimization"),
    "ONNX Runtime": ("onnxruntime", "optimization", "CPU inference runtime"),
    "CTranslate2": ("ctranslate2", "local_llm", "Efficient transformer runtime"),
    "ctransformers": ("ctransformers", "local_llm", "GGML/GGUF adapter"),
    "llama-cpp-python": ("llama_cpp", "local_llm", "Python llama.cpp binding"),
    "Sumy": ("sumy", "extractive_summary", "LexRank/LSA/Luhn"),
    "summa": ("summa", "extractive_summary", "TextRank summary/keywords"),
    "Gensim": ("gensim", "semantic", "TF-IDF/topics/similarity"),
    "spaCy": ("spacy", "nlp", "Sentence/NER/PhraseMatcher"),
    "Stanza": ("stanza", "nlp", "Multilingual NLP"),
    "HanLP": ("hanlp", "nlp", "Chinese NLP"),
    "LTP": ("ltp", "nlp", "Chinese structural NLP"),
    "jieba": ("jieba", "tokenizer", "Chinese tokenization"),
    "pkuseg": ("pkuseg", "tokenizer", "Chinese domain tokenization"),
    "THULAC": ("thulac", "tokenizer", "Chinese segmentation/POS"),
    "PyICU": ("icu", "unicode", "Unicode boundaries"),
    "ftfy": ("ftfy", "cleaning", "Unicode/mojibake repair"),
    # Keyword extraction and governed vocabulary (Top 20 family)
    "KeyBERT": ("keybert", "keyword", "Embedding keywords"),
    "YAKE": ("yake", "keyword", "Unsupervised keywords"),
    "pke": ("pke", "keyword", "Keyphrase algorithms"),
    "RAKE-NLTK": ("rake_nltk", "keyword", "RAKE phrases"),
    "rake-keyword": ("rake_keyword", "keyword", "Lightweight RAKE"),
    "Kex": ("kex", "keyword", "Keyword benchmark"),
    "KeyphraseVectorizers": ("keyphrase_vectorizers", "keyword", "Phrase candidates"),
    "PyTextRank": ("pytextrank", "keyword", "Graph rank"),
    "FlashText": ("flashtext", "dictionary", "Fast term matching"),
    "RapidFuzz": ("rapidfuzz", "deduplication", "Alias/fuzzy matching"),
    "dedupe": ("dedupe", "deduplication", "Entity deduplication"),
    "jellyfish": ("jellyfish", "deduplication", "String/phonetic similarity"),
    "pyahocorasick": ("ahocorasick", "dictionary", "Multi-pattern search"),
    "marisa-trie": ("marisa_trie", "dictionary", "Compressed trie"),
    "DAWG": ("dawg_python", "dictionary", "Compressed dictionary"),
    "wordfreq": ("wordfreq", "quality", "Word frequency filter"),
    "wordninja": ("wordninja", "cleaning", "Joined English word split"),
    "LangDetect": ("langdetect", "language", "Language detection"),
    "fastText": ("fasttext", "language", "Language/classification runtime"),
    "Sentence-Transformers": ("sentence_transformers", "semantic", "Multilingual embeddings"),
    # Additional local baselines named in the attached source
    "NLTK": ("nltk", "nlp", "Tokenization/stopwords"),
    "BERT Extractive Summarizer": ("summarizer", "extractive_summary", "BERT clustering"),
    "SummerTime": ("summertime", "benchmark", "Summarization evaluation"),
    "pyAutoSummarizer": ("pysummarization", "benchmark", "Summary/evaluation"),
    "Flair": ("flair", "nlp", "Contextual embeddings"),
    "OpenCC": ("opencc", "normalization", "Traditional/Simplified conversion"),
    "pypdf": ("pypdf", "input", "PDF text layer extraction"),
    "pdfplumber": ("pdfplumber", "input", "PDF text/table-aware extraction"),
    "python-docx": ("docx", "input", "DOCX paragraphs and tables"),
    "openpyxl": ("openpyxl", "input", "XLSX cell text extraction"),
}


# =============================================================================
# def 01 STANDARD LIBRARY IMPORTS AND CPU SAFETY
# =============================================================================

import argparse
import contextlib
import csv
import dataclasses
import datetime as dt
import hashlib
import html
import importlib
import importlib.util
import json
import logging
import math
import os
import pathlib
import platform
import re
import shutil
import sqlite3
import statistics
import sys
import tempfile
import threading
import time
import traceback
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from email import policy as email_policy
from email.parser import BytesParser
from typing import Any, Callable, Iterable, Iterator, Mapping, Optional, Sequence


_OPTIONAL_MODULE_CACHE: dict[str, Optional[Any]] = {}
_SPACY_PIPELINE_CACHE: dict[str, Any] = {}
_FASTTEXT_MODEL_CACHE: dict[str, Any] = {}
_KEYBERT_MODEL_CACHE: dict[str, Any] = {}
_LLAMA_MODEL_CACHE: dict[tuple[str, int, int], Any] = {}
_GENERATION_MODEL_CACHE: dict[tuple[str, ...], Any] = {}
_TOKENIZER_MODEL_CACHE: dict[str, Any] = {}
_RUNTIME_CACHE_LOCK = threading.RLock()


def def_configure_thread_environment(cpu_threads: Optional[int] = None) -> int:
    """Cap native numeric/tokenizer pools before optional heavy imports."""
    detected = os.cpu_count() or 2
    selected = cpu_threads or max(1, detected - DEFAULT_CPU_RESERVE_CORES)
    selected = max(1, min(selected, detected))
    for key in ENVIRONMENT_THREAD_KEYS:
        if key == "TOKENIZERS_PARALLELISM":
            os.environ.setdefault(key, "false")
        else:
            os.environ.setdefault(key, str(selected))
    return selected


CPU_THREADS = def_configure_thread_environment()


# =============================================================================
# def 02 DATA CONTRACTS
# =============================================================================

@dataclass(frozen=True)
class EngineConfig:
    db_path: str = DEFAULT_DB_PATH
    output_dir: str = DEFAULT_OUTPUT_DIR
    temp_root: str = DEFAULT_TEMP_ROOT
    language: str = DEFAULT_LANGUAGE
    output_formats: tuple[str, ...] = DEFAULT_OUTPUT_FORMATS
    summary_bullets: int = DEFAULT_SUMMARY_BULLETS
    bullet_char_limit_zh: int = DEFAULT_BULLET_CHAR_LIMIT_ZH
    bullet_word_limit_en: int = DEFAULT_BULLET_WORD_LIMIT_EN
    keyword_limit: int = DEFAULT_KEYWORD_LIMIT
    candidate_sentences: int = DEFAULT_CANDIDATE_SENTENCES
    chunk_characters: int = DEFAULT_CHUNK_CHARACTERS
    chunk_overlap_sentences: int = DEFAULT_CHUNK_OVERLAP_SENTENCES
    cpu_threads: int = CPU_THREADS
    max_cpu_percent: float = DEFAULT_MAX_CPU_PERCENT
    max_memory_percent: float = DEFAULT_MAX_MEMORY_PERCENT
    min_free_memory_mb: int = DEFAULT_MIN_FREE_MEMORY_MB
    min_free_disk_mb: int = DEFAULT_MIN_FREE_DISK_MB
    batch_size: int = DEFAULT_BATCH_SIZE
    resume: bool = DEFAULT_RESUME
    strict_numeric_evidence: bool = DEFAULT_STRICT_NUMERIC_EVIDENCE
    use_llm: bool = DEFAULT_USE_LLM
    llm_backend: str = DEFAULT_LLM_BACKEND
    llm_model_path: str = DEFAULT_LLM_MODEL_PATH
    ollama_model: str = DEFAULT_OLLAMA_MODEL
    ollama_url: str = DEFAULT_OLLAMA_URL
    embedding_model_path: str = DEFAULT_EMBEDDING_MODEL_PATH
    fasttext_model_path: str = DEFAULT_FASTTEXT_MODEL_PATH
    llm_context: int = DEFAULT_LLM_CONTEXT
    llm_max_tokens: int = DEFAULT_LLM_MAX_TOKENS
    llm_temperature: float = DEFAULT_LLM_TEMPERATURE
    term_min_documents: int = DEFAULT_TERM_MIN_DOCUMENTS
    term_min_extractors: int = DEFAULT_TERM_MIN_EXTRACTORS
    term_alias_similarity: float = DEFAULT_TERM_ALIAS_SIMILARITY
    promotion_threshold: float = DEFAULT_PROMOTION_THRESHOLD
    auto_promote: bool = DEFAULT_AUTO_PROMOTE
    keep_temp: bool = DEFAULT_KEEP_TEMP
    random_seed: int = DEFAULT_RANDOM_SEED


@dataclass(frozen=True)
class ResourceSnapshot:
    cpu_percent: float
    memory_percent: float
    available_memory_mb: float
    free_disk_mb: float
    source: str
    observed_at: str


@dataclass(frozen=True)
class SentenceRecord:
    sentence_id: int
    text: str
    paragraph_id: int
    position: int
    language: str
    score: float = 0.0
    extractors: tuple[str, ...] = ()


@dataclass(frozen=True)
class KeywordRecord:
    term: str
    canonical_term: str
    language: str
    term_type: str
    score: float
    extractors: tuple[str, ...]
    evidence_sentence_ids: tuple[int, ...]
    status: str = "CANDIDATE"


@dataclass(frozen=True)
class SummaryBullet:
    role: str
    headline: str
    detail: str
    evidence_sentence_ids: tuple[int, ...]
    validation_status: str


@dataclass(frozen=True)
class SummaryResult:
    schema_version: str
    engine: str
    engine_version: str
    run_id: str
    document_id: str
    content_sha256: str
    source_name: str
    source_language: str
    requested_language: str
    language: str
    raw_text: str
    normalized_text: str
    summary_bullets: tuple[SummaryBullet, ...]
    keywords: tuple[KeywordRecord, ...]
    entities: tuple[KeywordRecord, ...]
    vocabulary_delta: tuple[KeywordRecord, ...]
    warnings: tuple[str, ...]
    capabilities_used: tuple[str, ...]
    resource_snapshot: ResourceSnapshot
    created_at: str
    status: str = "PASS"

    def to_dict(self, include_text: bool = True) -> dict[str, Any]:
        payload = dataclasses.asdict(self)
        if not include_text:
            payload.pop("raw_text", None)
            payload.pop("normalized_text", None)
        return payload


# =============================================================================
# def 03 GENERIC UTILITIES
# =============================================================================

def def_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def def_sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def def_sha256_file(path: pathlib.Path, block_size: int = 1_048_576) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(block_size), b""):
            digest.update(block)
    return digest.hexdigest()


def def_json_dumps(value: Any, indent: Optional[int] = 2) -> str:
    return json.dumps(value, ensure_ascii=False, indent=indent, sort_keys=False)


def def_atomic_write_text(path: pathlib.Path, text: str, encoding: str = "utf-8") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding=encoding, newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except Exception:
        with contextlib.suppress(OSError):
            os.unlink(temporary_name)
        raise


def def_optional_module(module_name: Optional[str]) -> Optional[Any]:
    if not module_name:
        return None
    with _RUNTIME_CACHE_LOCK:
        if module_name in _OPTIONAL_MODULE_CACHE:
            return _OPTIONAL_MODULE_CACHE[module_name]
        try:
            if importlib.util.find_spec(module_name) is None:
                _OPTIONAL_MODULE_CACHE[module_name] = None
            else:
                _OPTIONAL_MODULE_CACHE[module_name] = importlib.import_module(module_name)
        except Exception:
            _OPTIONAL_MODULE_CACHE[module_name] = None
        return _OPTIONAL_MODULE_CACHE[module_name]


def def_spacy_pipeline(model_name: str) -> Optional[Any]:
    with _RUNTIME_CACHE_LOCK:
        if model_name in _SPACY_PIPELINE_CACHE:
            return _SPACY_PIPELINE_CACHE[model_name]
        spacy = def_optional_module("spacy")
        if spacy is None:
            return None
        try:
            nlp = spacy.load(model_name)
            if "parser" not in nlp.pipe_names and "sentencizer" not in nlp.pipe_names:
                nlp.add_pipe("sentencizer")
            _SPACY_PIPELINE_CACHE[model_name] = nlp
            return nlp
        except Exception:
            return None


def def_capability_report() -> list[dict[str, Any]]:
    report: list[dict[str, Any]] = []
    for display_name, (module_name, category, purpose) in LIBRARY_PORTFOLIO.items():
        if display_name == "Ollama":
            available = shutil.which("ollama") is not None
        else:
            try:
                available = bool(module_name and importlib.util.find_spec(module_name))
            except (ImportError, ModuleNotFoundError, ValueError):
                available = False
        report.append({
            "library": display_name,
            "module": module_name or "external_runtime",
            "category": category,
            "purpose": purpose,
            "available": available,
        })
    return report


def def_normalize_number_token(token: str) -> str:
    return unicodedata.normalize("NFKC", token).replace(",", "").strip().casefold()


def def_extract_number_tokens(text: str) -> tuple[str, ...]:
    return tuple(def_normalize_number_token(item) for item in re.findall(NUMBER_PATTERN, text, flags=re.I))


def def_extract_factual_number_tokens(text: str) -> tuple[str, ...]:
    clean = re.sub(r"^\s*(?:[-*+]\s*)?\d+[.)、]\s*", "", text)
    clean = re.sub(r"https?://\S+|\[\[?\d+\]?\]\([^)]*\)", "", clean, flags=re.I)
    return def_extract_number_tokens(clean)


def def_truncate_sentence(text: str, language: str, zh_chars: int, en_words: int) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    if language == "en":
        words = clean.split()
        return " ".join(words[:en_words]).rstrip(" ,;:")
    return clean[:zh_chars].rstrip("，,；;：:")


def def_logging(level: str = DEFAULT_LOG_LEVEL) -> logging.Logger:
    logger = logging.getLogger(ENGINE_NAME)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter("def [%(asctime)s] [%(levelname)s] %(message)s"))
        logger.addHandler(handler)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    return logger


LOGGER = def_logging()


# =============================================================================
# def 04 RESOURCE GATE, BATCH CONTROL AND ENGINE-OWNED TEMP
# =============================================================================

def def_resource_snapshot(path: str | pathlib.Path = ".") -> ResourceSnapshot:
    observed_at = def_now_iso()
    probe_path = pathlib.Path(path).expanduser().resolve()
    while not probe_path.exists() and probe_path.parent != probe_path:
        probe_path = probe_path.parent
    psutil = def_optional_module("psutil")
    if psutil is not None:
        virtual = psutil.virtual_memory()
        disk = psutil.disk_usage(str(probe_path))
        return ResourceSnapshot(
            cpu_percent=float(psutil.cpu_percent(interval=0.15)),
            memory_percent=float(virtual.percent),
            available_memory_mb=float(virtual.available / 1_048_576),
            free_disk_mb=float(disk.free / 1_048_576),
            source="psutil",
            observed_at=observed_at,
        )
    disk = shutil.disk_usage(probe_path)
    available_mb = 0.0
    memory_percent = 0.0
    if hasattr(os, "sysconf"):
        with contextlib.suppress(ValueError, OSError, AttributeError):
            pages = os.sysconf("SC_AVPHYS_PAGES")
            page_size = os.sysconf("SC_PAGE_SIZE")
            available_mb = float(pages * page_size / 1_048_576)
    return ResourceSnapshot(
        cpu_percent=0.0,
        memory_percent=memory_percent,
        available_memory_mb=available_mb,
        free_disk_mb=float(disk.free / 1_048_576),
        source="stdlib_fallback",
        observed_at=observed_at,
    )


def def_resource_gate(config: EngineConfig, path: str | pathlib.Path = ".") -> tuple[bool, ResourceSnapshot, tuple[str, ...]]:
    snapshot = def_resource_snapshot(path)
    reasons: list[str] = []
    if snapshot.cpu_percent > config.max_cpu_percent:
        reasons.append(f"CPU_PRESSURE:{snapshot.cpu_percent:.1f}%")
    if snapshot.memory_percent and snapshot.memory_percent > config.max_memory_percent:
        reasons.append(f"MEMORY_PRESSURE:{snapshot.memory_percent:.1f}%")
    if snapshot.available_memory_mb and snapshot.available_memory_mb < config.min_free_memory_mb:
        reasons.append(f"LOW_AVAILABLE_MEMORY:{snapshot.available_memory_mb:.0f}MB")
    if snapshot.free_disk_mb < config.min_free_disk_mb:
        reasons.append(f"LOW_FREE_DISK:{snapshot.free_disk_mb:.0f}MB")
    return not reasons, snapshot, tuple(reasons)


def def_adaptive_batch_size(config: EngineConfig, snapshot: ResourceSnapshot) -> int:
    size = max(1, config.batch_size)
    if snapshot.memory_percent >= config.max_memory_percent - 5:
        return 1
    if snapshot.cpu_percent >= config.max_cpu_percent - 10:
        return max(1, size // 4)
    if snapshot.memory_percent >= config.max_memory_percent - 15:
        return max(1, size // 2)
    return size


@contextlib.contextmanager
def def_owned_temp_directory(config: EngineConfig, run_id: str) -> Iterator[pathlib.Path]:
    root = pathlib.Path(config.temp_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    marker = root / ".via_summarizer_owned"
    if not marker.exists():
        def_atomic_write_text(marker, f"{ENGINE_NAME}\n")
    run_dir = pathlib.Path(tempfile.mkdtemp(prefix=f"RUN_{run_id}_", dir=str(root)))
    try:
        yield run_dir
    finally:
        if not config.keep_temp and marker.exists() and run_dir.parent == root:
            shutil.rmtree(run_dir, ignore_errors=True)


# =============================================================================
# def 05 TEXT INPUT, REPAIR, NORMALIZATION AND LANGUAGE ROUTING
# =============================================================================

def def_decode_bytes(data: bytes) -> tuple[str, str]:
    for encoding in ("utf-8-sig", "utf-8", "big5", "cp950", "gb18030", "utf-16", "latin-1"):
        try:
            return data.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace"), "utf-8-replace"


def def_strip_html(raw: str) -> str:
    bs4 = def_optional_module("bs4")
    if bs4 is not None:
        try:
            return bs4.BeautifulSoup(raw, "html.parser").get_text("\n")
        except Exception:
            pass
    without_blocks = re.sub(r"(?is)<(?:script|style|noscript).*?>.*?</(?:script|style|noscript)>", " ", raw)
    return html.unescape(re.sub(r"(?s)<[^>]+>", " ", without_blocks))


def def_flatten_json(value: Any, prefix: str = "") -> list[str]:
    output: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            child = f"{prefix}.{key}" if prefix else str(key)
            output.extend(def_flatten_json(item, child))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            output.extend(def_flatten_json(item, f"{prefix}[{index}]"))
    elif value is not None:
        output.append(f"{prefix}: {value}" if prefix else str(value))
    return output


def def_extract_pdf_text(file_path: pathlib.Path) -> tuple[str, str]:
    pypdf = def_optional_module("pypdf")
    if pypdf is not None:
        try:
            reader = pypdf.PdfReader(str(file_path), strict=False)
            pages = [page.extract_text() or "" for page in reader.pages]
            text = "\n\n".join(pages).strip()
            if text:
                return text, "pypdf"
        except Exception:
            pass
    pdfplumber = def_optional_module("pdfplumber")
    if pdfplumber is not None:
        try:
            with pdfplumber.open(str(file_path)) as document:
                text = "\n\n".join((page.extract_text() or "") for page in document.pages).strip()
            if text:
                return text, "pdfplumber"
        except Exception:
            pass
    raise RuntimeError("PDF_TEXT_LAYER_UNAVAILABLE: install pypdf or pdfplumber; OCR belongs to the governed extraction engine")


def def_extract_docx_text(file_path: pathlib.Path) -> tuple[str, str]:
    docx = def_optional_module("docx")
    if docx is None:
        raise RuntimeError("DOCX_READER_UNAVAILABLE: install python-docx")
    document = docx.Document(str(file_path))
    lines = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
    for table in document.tables:
        for row in table.rows:
            values = [cell.text.strip() for cell in row.cells]
            if any(values):
                lines.append("\t".join(values))
    return "\n".join(lines), "python-docx"


def def_extract_eml_text(data: bytes) -> tuple[str, str]:
    message = BytesParser(policy=email_policy.default).parsebytes(data)
    parts: list[str] = []
    subject = str(message.get("subject", "")).strip()
    if subject:
        parts.append(f"Subject: {subject}")
    iterable = message.walk() if message.is_multipart() else (message,)
    for part in iterable:
        content_type = part.get_content_type()
        if content_type not in ("text/plain", "text/html"):
            continue
        try:
            content = part.get_content()
        except Exception:
            payload = part.get_payload(decode=True) or b""
            content, _ = def_decode_bytes(payload)
        content = str(content)
        parts.append(def_strip_html(content) if content_type == "text/html" else content)
    return "\n\n".join(parts), "stdlib-email"


def def_extract_xlsx_text(file_path: pathlib.Path) -> tuple[str, str]:
    openpyxl = def_optional_module("openpyxl")
    if openpyxl is None:
        raise RuntimeError("XLSX_READER_UNAVAILABLE: install openpyxl")
    workbook = openpyxl.load_workbook(str(file_path), read_only=True, data_only=True)
    lines: list[str] = []
    try:
        for worksheet in workbook.worksheets:
            lines.append(f"Sheet: {worksheet.title}")
            for row in worksheet.iter_rows(values_only=True):
                values = ["" if value is None else str(value) for value in row]
                if any(values):
                    lines.append("\t".join(values))
    finally:
        workbook.close()
    return "\n".join(lines), "openpyxl"


def def_read_input(path: str | pathlib.Path) -> tuple[str, dict[str, Any]]:
    file_path = pathlib.Path(path).expanduser().resolve()
    if not file_path.is_file():
        raise FileNotFoundError(f"Input file not found: {file_path}")
    data = file_path.read_bytes()
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        text, encoding = def_extract_pdf_text(file_path)
    elif suffix == ".docx":
        text, encoding = def_extract_docx_text(file_path)
    elif suffix == ".eml":
        text, encoding = def_extract_eml_text(data)
    elif suffix == ".xlsx":
        text, encoding = def_extract_xlsx_text(file_path)
    else:
        text, encoding = def_decode_bytes(data)
    if suffix in (".html", ".htm", ".xml"):
        text = def_strip_html(text)
    elif suffix == ".ipynb":
        try:
            notebook = json.loads(text)
            cells = notebook.get("cells", [])
            text = "\n\n".join("".join(cell.get("source", [])) for cell in cells)
        except (json.JSONDecodeError, AttributeError):
            pass
    elif suffix in (".json", ".jsonl"):
        try:
            if suffix == ".jsonl":
                rows = [json.loads(line) for line in text.splitlines() if line.strip()]
                text = "\n".join(def_flatten_json(rows))
            else:
                text = "\n".join(def_flatten_json(json.loads(text)))
        except json.JSONDecodeError:
            pass
    return text, {
        "path": str(file_path),
        "source_name": file_path.name,
        "source_sha256": def_sha256_file(file_path),
        "encoding": encoding,
        "bytes": len(data),
    }


def def_repair_text(raw_text: str) -> tuple[str, tuple[str, ...]]:
    warnings: list[str] = []
    text = raw_text.replace("\x00", "")
    ftfy = def_optional_module("ftfy")
    if ftfy is not None:
        try:
            text = ftfy.fix_text(text)
        except Exception as exc:
            warnings.append(f"FTFY_SKIPPED:{type(exc).__name__}")
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)
    text = re.sub(r"[\t\v\f]+", " ", text)
    text = re.sub(r"[ ]{2,}", " ", text)
    text = re.sub(r"\n[ ]+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if "�" in text:
        warnings.append("REPLACEMENT_CHARACTER_PRESENT")
    return text, tuple(warnings)


def def_opencc_convert(text: str, target_language: str) -> tuple[str, str]:
    opencc = def_optional_module("opencc")
    if opencc is None or target_language not in ("zh-TW", "zh-CN"):
        return text, "identity"
    candidates = ("s2twp", "s2tw") if target_language == "zh-TW" else ("t2s",)
    for profile in candidates:
        try:
            return opencc.OpenCC(profile).convert(text), f"opencc:{profile}"
        except Exception:
            continue
    return text, "identity"


def def_language_heuristic(text: str) -> str:
    sample = text[:20_000]
    han = len(re.findall(r"[\u3400-\u9fff]", sample))
    latin = len(re.findall(r"[A-Za-z]", sample))
    traditional_markers = len(re.findall(r"[臺灣與為這個們體關係後裡網資料檔總彙億萬]", sample))
    simplified_markers = len(re.findall(r"[湾与为这个们体关系统后里网数据档总汇亿万]", sample))
    if han and latin:
        if min(han, latin) / max(han, latin) > 0.12:
            return "mixed"
        if latin > han:
            return "en"
    if han:
        return "zh-TW" if traditional_markers >= simplified_markers else "zh-CN"
    return "en" if latin else DEFAULT_LANGUAGE


def def_detect_language(text: str, config: EngineConfig) -> tuple[str, str]:
    if config.fasttext_model_path:
        fasttext = def_optional_module("fasttext")
        model_path = pathlib.Path(config.fasttext_model_path)
        if fasttext is not None and model_path.is_file():
            try:
                model_key = str(model_path.resolve())
                with _RUNTIME_CACHE_LOCK:
                    model = _FASTTEXT_MODEL_CACHE.get(model_key)
                    if model is None:
                        model = fasttext.load_model(model_key)
                        _FASTTEXT_MODEL_CACHE[model_key] = model
                labels, _ = model.predict(re.sub(r"\s+", " ", text[:10_000]))
                label = labels[0].replace("__label__", "")
                return {"zh": "zh-TW", "en": "en"}.get(label, "mixed"), "fastText"
            except Exception:
                pass
    langdetect = def_optional_module("langdetect")
    if langdetect is not None:
        try:
            detected = langdetect.detect(text[:10_000])
            if detected.startswith("zh"):
                return def_language_heuristic(text), "LangDetect+heuristic"
            if detected.startswith("en"):
                return "en", "LangDetect"
        except Exception:
            pass
    return def_language_heuristic(text), "heuristic"


def def_normalize_text(raw_text: str, config: EngineConfig) -> tuple[str, str, str, tuple[str, ...], tuple[str, ...]]:
    repaired, warnings = def_repair_text(raw_text)
    language, detector = def_detect_language(repaired, config)
    target = config.language if config.language in ("zh-TW", "zh-CN", "en") else ("zh-TW" if language.startswith("zh") else language)
    normalized, converter = def_opencc_convert(repaired, target)
    effective_language = target if language.startswith("zh") and target.startswith("zh") else language
    warning_list = list(warnings)
    if language.startswith("zh") and target.startswith("zh") and language != target and converter == "identity":
        warning_list.append("OPENCC_UNAVAILABLE_FOR_REQUESTED_VARIANT")
    if target in ("zh-TW", "zh-CN", "en") and not language.startswith("zh") and target != language and not config.use_llm:
        warning_list.append("CROSS_LANGUAGE_TRANSLATION_REQUIRES_LOCAL_LLM")
    used = [f"language:{detector}"]
    if converter != "identity":
        used.append(converter)
    return normalized, effective_language, language, tuple(warning_list), tuple(used)


# =============================================================================
# def 06 SENTENCE SPLITTING, TOKENIZATION AND EVIDENCE INDEX
# =============================================================================

def def_split_sentences_rule(text: str) -> list[tuple[int, str]]:
    results: list[tuple[int, str]] = []
    paragraphs = re.split(r"\n\s*\n|\n(?=[#*\-•\d])", text)
    for paragraph_id, paragraph in enumerate(paragraphs, start=1):
        paragraph = re.sub(r"\s+", " ", paragraph).strip()
        if not paragraph:
            continue
        pieces = re.split(r"(?<=[。！？!?])\s*|(?<=[.!?])\s+(?=[A-Z0-9])|(?<=；)\s*", paragraph)
        for piece in pieces:
            clean = piece.strip(" •\t")
            if clean:
                results.append((paragraph_id, clean))
    return results


def def_split_sentences(text: str, language: str) -> tuple[list[SentenceRecord], tuple[str, ...]]:
    used: list[str] = []
    raw_sentences: list[tuple[int, str]] = []
    model_name = DEFAULT_SPACY_EN_MODEL if language == "en" else DEFAULT_SPACY_ZH_MODEL
    nlp = def_spacy_pipeline(model_name)
    if nlp is not None:
        try:
            nlp.max_length = max(nlp.max_length, len(text) + 1)
            doc = nlp(text)
            raw_sentences = [(1, span.text.strip()) for span in doc.sents if span.text.strip()]
            used.append(f"spaCy:{model_name}")
        except Exception:
            raw_sentences = []
    if not raw_sentences:
        raw_sentences = def_split_sentences_rule(text)
        used.append("rule_sentence_splitter")
    records = [
        SentenceRecord(
            sentence_id=index,
            text=sentence,
            paragraph_id=paragraph_id,
            position=index,
            language=def_language_heuristic(sentence),
        )
        for index, (paragraph_id, sentence) in enumerate(raw_sentences, start=1)
    ]
    return records, tuple(used)


def def_tokenize(text: str, language: str) -> list[str]:
    tickers = re.findall(TICKER_PATTERN, text)
    token_text = re.sub(TICKER_PATTERN, " ", text)
    token_text = re.sub(NUMBER_PATTERN, " ", token_text, flags=re.I)
    if language.startswith("zh") or language == "mixed":
        jieba = def_optional_module("jieba")
        if jieba is not None:
            try:
                return tickers + [token.strip() for token in jieba.cut(token_text, cut_all=False) if token.strip()]
            except Exception:
                pass
        pkuseg = def_optional_module("pkuseg")
        if pkuseg is not None:
            try:
                with _RUNTIME_CACHE_LOCK:
                    segmenter = _TOKENIZER_MODEL_CACHE.get("pkuseg:default")
                    if segmenter is None:
                        segmenter = pkuseg.pkuseg()
                        _TOKENIZER_MODEL_CACHE["pkuseg:default"] = segmenter
                return tickers + [token.strip() for token in segmenter.cut(token_text) if token.strip()]
            except Exception:
                pass
        thulac = def_optional_module("thulac")
        if thulac is not None:
            try:
                with _RUNTIME_CACHE_LOCK:
                    segmenter = _TOKENIZER_MODEL_CACHE.get("thulac:seg_only")
                    if segmenter is None:
                        segmenter = thulac.thulac(seg_only=True)
                        _TOKENIZER_MODEL_CACHE["thulac:seg_only"] = segmenter
                return tickers + [token.strip() for token in segmenter.cut(token_text, text=True).split() if token.strip()]
            except Exception:
                pass
        tokens = re.findall(r"[A-Za-z][A-Za-z0-9._+\-/]{1,}|[\u3400-\u9fff]+|\d+(?:\.\d+)?%?", token_text)
        output: list[str] = list(tickers)
        boundary_pattern = "(" + "|".join(re.escape(item) for item in CJK_BOUNDARY_TERMS) + ")"
        for token in tokens:
            if not re.fullmatch(r"[\u3400-\u9fff]+", token):
                output.append(token)
                continue
            pieces = [piece for piece in re.split(boundary_pattern, token) if piece and piece not in CJK_BOUNDARY_TERMS]
            for piece in pieces:
                if len(piece) <= 8:
                    output.append(piece)
                else:
                    output.extend(piece[index:index + 4] for index in range(0, len(piece), 4) if len(piece[index:index + 4]) >= 2)
        return output
    english_tokens = re.findall(r"[A-Za-z][A-Za-z0-9'._+\-/]{1,}|\d+(?:\.\d+)?%?", token_text)
    wordninja = def_optional_module("wordninja")
    if wordninja is not None:
        expanded: list[str] = []
        for token in english_tokens:
            if len(token) >= 20 and token.isalpha():
                with contextlib.suppress(Exception):
                    pieces = wordninja.split(token)
                    if len(pieces) > 1:
                        expanded.extend(pieces)
                        continue
            expanded.append(token)
        english_tokens = expanded
    return tickers + english_tokens


def def_meaningful_tokens(text: str, language: str) -> list[str]:
    tokens = def_tokenize(text, language)
    output: list[str] = []
    for token in tokens:
        if re.fullmatch(TICKER_PATTERN, token):
            output.append(token.upper())
            continue
        normalized = token.casefold().strip("_./-+")
        if len(normalized) < 2 or normalized in STOPWORDS_ZH or normalized in STOPWORDS_EN:
            continue
        if re.fullmatch(r"\d+(?:\.\d+)?%?", normalized):
            continue
        output.append(normalized)
    return output


def def_chunk_sentences(sentences: Sequence[SentenceRecord], max_characters: int, overlap: int) -> list[list[SentenceRecord]]:
    chunks: list[list[SentenceRecord]] = []
    current: list[SentenceRecord] = []
    current_size = 0
    for sentence in sentences:
        size = len(sentence.text)
        if current and current_size + size > max_characters:
            chunks.append(current)
            current = current[-max(0, overlap):] if overlap else []
            current_size = sum(len(item.text) for item in current)
        current.append(sentence)
        current_size += size
    if current:
        chunks.append(current)
    return chunks


# =============================================================================
# def 07 EXTRACTIVE ENSEMBLE
# =============================================================================

def def_frequency_sentence_scores(sentences: Sequence[SentenceRecord], language: str) -> dict[int, float]:
    document_frequency: Counter[str] = Counter()
    sentence_tokens: dict[int, list[str]] = {}
    for sentence in sentences:
        tokens = def_meaningful_tokens(sentence.text, language)
        sentence_tokens[sentence.sentence_id] = tokens
        document_frequency.update(set(tokens))
    total_sentences = max(1, len(sentences))
    scores: dict[int, float] = {}
    for sentence in sentences:
        tokens = sentence_tokens[sentence.sentence_id]
        if not tokens:
            scores[sentence.sentence_id] = 0.0
            continue
        tf = Counter(tokens)
        weighted = sum((1 + math.log(count)) * math.log((1 + total_sentences) / (1 + document_frequency[token])) for token, count in tf.items())
        length_penalty = max(1.0, math.sqrt(len(tokens)))
        position_bonus = 0.35 / math.sqrt(sentence.position)
        numeric_bonus = min(0.35, 0.08 * len(def_extract_number_tokens(sentence.text)))
        ticker_bonus = 0.12 if re.search(TICKER_PATTERN, sentence.text) else 0.0
        boilerplate_penalty = 0.75 if def_contains_any(sentence.text.strip(), BOILERPLATE_PATTERNS) else 0.0
        question_penalty = 0.25 if sentence.text.rstrip().endswith(("?", "？")) else 0.0
        table_penalty = 0.30 if sentence.text.count("|") >= 3 else 0.0
        scores[sentence.sentence_id] = max(
            0.0,
            weighted / length_penalty + position_bonus + numeric_bonus + ticker_bonus
            - boilerplate_penalty - question_penalty - table_penalty,
        )
    return def_minmax_scores(scores)


def def_minmax_scores(scores: Mapping[int, float]) -> dict[int, float]:
    if not scores:
        return {}
    low, high = min(scores.values()), max(scores.values())
    if math.isclose(low, high):
        return {key: 1.0 if value else 0.0 for key, value in scores.items()}
    return {key: (value - low) / (high - low) for key, value in scores.items()}


def def_sumy_sentence_ids(sentences: Sequence[SentenceRecord], language: str, limit: int) -> list[int]:
    if def_optional_module("sumy") is None:
        return []
    try:
        from sumy.nlp.tokenizers import Tokenizer
        from sumy.parsers.plaintext import PlaintextParser
        from sumy.summarizers.lex_rank import LexRankSummarizer
        joined = "\n".join(item.text for item in sentences)
        tokenizer_language = "english" if language == "en" else "chinese"
        parser = PlaintextParser.from_string(joined, Tokenizer(tokenizer_language))
        selected = [str(item).strip() for item in LexRankSummarizer()(parser.document, limit)]
        return def_match_selected_sentence_ids(selected, sentences)
    except Exception:
        return []


def def_summa_sentence_ids(sentences: Sequence[SentenceRecord], limit: int) -> list[int]:
    summa = def_optional_module("summa")
    if summa is None:
        return []
    try:
        selected_text = summa.summarizer.summarize("\n".join(item.text for item in sentences), words=max(80, limit * 45))
        return def_match_selected_sentence_ids(selected_text.splitlines(), sentences)[:limit]
    except Exception:
        return []


def def_bert_sentence_ids(sentences: Sequence[SentenceRecord], limit: int) -> list[int]:
    summarizer_module = def_optional_module("summarizer")
    if summarizer_module is None:
        return []
    try:
        model = summarizer_module.Summarizer()
        output = model(" ".join(item.text for item in sentences), num_sentences=limit)
        return def_match_selected_sentence_ids(str(output).splitlines(), sentences)
    except Exception:
        return []


def def_match_selected_sentence_ids(selected: Sequence[str], sentences: Sequence[SentenceRecord]) -> list[int]:
    compact_map = {re.sub(r"\s+", "", item.text): item.sentence_id for item in sentences}
    results: list[int] = []
    for text in selected:
        compact = re.sub(r"\s+", "", str(text).strip())
        if compact in compact_map:
            results.append(compact_map[compact])
            continue
        best_id, best_ratio = 0, 0.0
        for candidate, sentence_id in compact_map.items():
            ratio = def_similarity(compact, candidate)
            if ratio > best_ratio:
                best_id, best_ratio = sentence_id, ratio
        if best_id and best_ratio >= 80:
            results.append(best_id)
    return list(dict.fromkeys(results))


def def_rank_sentences(sentences: Sequence[SentenceRecord], language: str, config: EngineConfig) -> tuple[list[SentenceRecord], tuple[str, ...]]:
    if not sentences:
        return [], ("empty",)
    ensemble: dict[int, list[float]] = defaultdict(list)
    extractors: dict[int, list[str]] = defaultdict(list)
    frequency_scores = def_frequency_sentence_scores(sentences, language)
    for sentence_id, score in frequency_scores.items():
        ensemble[sentence_id].append(score)
        extractors[sentence_id].append("TF-IDF+position")
    used = ["TF-IDF+position"]
    optional_runs: tuple[tuple[str, Callable[[], list[int]]], ...] = (
        ("Sumy-LexRank", lambda: def_sumy_sentence_ids(sentences, language, config.candidate_sentences)),
        ("summa-TextRank", lambda: def_summa_sentence_ids(sentences, config.candidate_sentences)),
        ("BERT-Extractive", lambda: def_bert_sentence_ids(sentences, config.candidate_sentences)),
    )
    for extractor_name, runner in optional_runs:
        selected = runner()
        if not selected:
            continue
        used.append(extractor_name)
        denominator = max(1, len(selected))
        for rank, sentence_id in enumerate(selected):
            ensemble[sentence_id].append(1.0 - (rank / denominator) * 0.35)
            extractors[sentence_id].append(extractor_name)
    ranked: list[SentenceRecord] = []
    for sentence in sentences:
        scores = ensemble.get(sentence.sentence_id, [0.0])
        final_score = statistics.fmean(scores) + min(0.12, 0.03 * (len(extractors[sentence.sentence_id]) - 1))
        ranked.append(dataclasses.replace(
            sentence,
            score=round(final_score, 6),
            extractors=tuple(extractors[sentence.sentence_id]),
        ))
    ranked.sort(key=lambda item: (-item.score, item.position))
    return ranked, tuple(used)


# =============================================================================
# def 08 KEYWORD, ENTITY, ALIAS AND VOCABULARY CANDIDATES
# =============================================================================

def def_similarity(left: str, right: str) -> float:
    rapidfuzz = def_optional_module("rapidfuzz")
    if rapidfuzz is not None:
        try:
            return float(rapidfuzz.fuzz.ratio(left, right))
        except Exception:
            pass
    jellyfish = def_optional_module("jellyfish")
    if jellyfish is not None:
        try:
            return 100.0 * float(jellyfish.jaro_winkler_similarity(left.casefold(), right.casefold()))
        except Exception:
            pass
    import difflib
    return 100.0 * difflib.SequenceMatcher(None, left.casefold(), right.casefold()).ratio()


def def_canonical_term(term: str, language: str) -> str:
    cleaned = unicodedata.normalize("NFKC", term).strip(" \t\n\r,.;:，。；：（）()[]{}\"'")
    if language.startswith("zh") or re.search(r"[\u3400-\u9fff]", cleaned):
        converted, _ = def_opencc_convert(cleaned, "zh-TW")
        return converted
    if re.fullmatch(TICKER_PATTERN, cleaned):
        return cleaned.upper()
    if cleaned.casefold() in KNOWN_BRAND_CASE:
        return KNOWN_BRAND_CASE[cleaned.casefold()]
    if cleaned.upper() in KNOWN_ACRONYMS:
        return cleaned.upper()
    return cleaned.title()


def def_term_type(term: str) -> str:
    if re.fullmatch(TICKER_PATTERN, term):
        return "ticker"
    if re.search(r"(?:率|指數|收益|營收|毛利|EPS|PMI|CAPEX|AUM|GDP|CPI|bps?)$", term, flags=re.I):
        return "metric"
    if re.fullmatch(r"[A-Z]{2,10}", term):
        return "abbreviation"
    if re.search(r"公司|銀行|集團|Corp|Inc|Ltd|ETF$", term, flags=re.I):
        return "organization"
    return "term"


def def_keyword_fallback(sentences: Sequence[SentenceRecord], language: str, limit: int) -> dict[str, tuple[float, set[str], set[int]]]:
    occurrences: dict[str, set[int]] = defaultdict(set)
    term_frequency: Counter[str] = Counter()
    total = 0
    for sentence in sentences:
        tokens = def_meaningful_tokens(sentence.text, language)
        total += len(tokens)
        for token in tokens:
            if 2 <= len(token) <= 40:
                term_frequency[token] += 1
                occurrences[token].add(sentence.sentence_id)
        for ticker in re.findall(TICKER_PATTERN, sentence.text):
            term_frequency[ticker] += 2
            occurrences[ticker].add(sentence.sentence_id)
        for phrase in re.findall(r"(?:[A-Za-z][A-Za-z0-9+./-]*\s+){1,3}[A-Za-z][A-Za-z0-9+./-]*|[\u3400-\u9fff]{2,8}(?:率|指數|引擎|系統|模型|資料庫|風險|摘要|字庫)", sentence.text):
            phrase = phrase.strip()
            if len(phrase) <= 60:
                term_frequency[phrase] += 1
                occurrences[phrase].add(sentence.sentence_id)
    maximum = max(term_frequency.values(), default=1)
    output: dict[str, tuple[float, set[str], set[int]]] = {}
    for term, count in term_frequency.most_common(limit * 4):
        score = min(1.0, (count / maximum) * 0.7 + (len(occurrences[term]) / max(1, len(sentences))) * 0.3)
        output[term] = (score, {"frequency"}, occurrences[term])
    return output


def def_yake_keywords(text: str, language: str, limit: int) -> list[tuple[str, float]]:
    yake = def_optional_module("yake")
    if yake is None:
        return []
    try:
        lang = "en" if language == "en" else "zh"
        extractor = yake.KeywordExtractor(lan=lang, n=3, top=limit, dedupLim=0.9)
        return [(term, max(0.0, 1.0 - float(score))) for term, score in extractor.extract_keywords(text)]
    except Exception:
        return []


def def_summa_keywords(text: str, limit: int) -> list[tuple[str, float]]:
    summa = def_optional_module("summa")
    if summa is None:
        return []
    try:
        values = summa.keywords.keywords(text, scores=True)
        return [(str(term), float(score)) for term, score in values[:limit]]
    except Exception:
        return []


def def_rake_keywords(text: str, limit: int) -> list[tuple[str, float]]:
    rake_nltk = def_optional_module("rake_nltk")
    if rake_nltk is None:
        return []
    try:
        extractor = rake_nltk.Rake()
        extractor.extract_keywords_from_text(text)
        pairs = extractor.get_ranked_phrases_with_scores()[:limit]
        maximum = max((score for score, _ in pairs), default=1.0)
        return [(phrase, float(score / maximum)) for score, phrase in pairs]
    except Exception:
        return []


def def_pke_keywords(text: str, language: str, limit: int) -> list[tuple[str, float]]:
    pke = def_optional_module("pke")
    if pke is None:
        return []
    try:
        extractor = pke.unsupervised.MultipartiteRank()
        extractor.load_document(input=text, language="en" if language == "en" else "zh")
        extractor.candidate_selection(pos={"NOUN", "PROPN", "ADJ"})
        extractor.candidate_weighting(alpha=1.1, threshold=0.74, method="average")
        pairs = extractor.get_n_best(n=limit, stemming=False)
        maximum = max((float(score) for _, score in pairs), default=1.0)
        return [(str(term), float(score) / maximum) for term, score in pairs]
    except Exception:
        return []


def def_pytextrank_keywords(text: str, language: str, limit: int) -> list[tuple[str, float]]:
    if def_optional_module("pytextrank") is None:
        return []
    model_name = DEFAULT_SPACY_EN_MODEL if language == "en" else DEFAULT_SPACY_ZH_MODEL
    nlp = def_spacy_pipeline(model_name)
    if nlp is None:
        return []
    try:
        with _RUNTIME_CACHE_LOCK:
            if "textrank" not in nlp.pipe_names:
                nlp.add_pipe("textrank")
        doc = nlp(text)
        phrases = list(doc._.phrases)[:limit]
        maximum = max((float(item.rank) for item in phrases), default=1.0)
        return [(str(item.text), float(item.rank) / maximum) for item in phrases]
    except Exception:
        return []


def def_keybert_keywords(text: str, config: EngineConfig, limit: int) -> list[tuple[str, float]]:
    if not config.embedding_model_path or not pathlib.Path(config.embedding_model_path).exists():
        return []
    keybert = def_optional_module("keybert")
    if keybert is None:
        return []
    try:
        model_key = str(pathlib.Path(config.embedding_model_path).resolve())
        with _RUNTIME_CACHE_LOCK:
            model = _KEYBERT_MODEL_CACHE.get(model_key)
            if model is None:
                model = keybert.KeyBERT(model=model_key)
                _KEYBERT_MODEL_CACHE[model_key] = model
        kwargs: dict[str, Any] = {
            "keyphrase_ngram_range": (1, 3), "stop_words": None,
            "use_mmr": True, "diversity": 0.45, "top_n": limit,
        }
        vectorizers = def_optional_module("keyphrase_vectorizers")
        if vectorizers is not None:
            with contextlib.suppress(Exception):
                kwargs["vectorizer"] = vectorizers.KeyphraseCountVectorizer()
        return [(term, float(score)) for term, score in model.extract_keywords(text, **kwargs)]
    except Exception:
        return []


def def_find_evidence_ids(term: str, sentences: Sequence[SentenceRecord]) -> set[int]:
    folded = term.casefold()
    return {sentence.sentence_id for sentence in sentences if folded in sentence.text.casefold()}


def def_clean_keyword_term(term: str) -> str:
    clean = unicodedata.normalize("NFKC", term).strip(" \t\n\r,.;:，。；：（）()[]{}\"'")
    if not clean or re.search(r"[\u3400-\u9fff]", clean):
        return clean
    words = clean.split()
    while words and words[0].casefold().strip("-_/.") in STOPWORDS_EN:
        words.pop(0)
    while words and words[-1].casefold().strip("-_/.") in STOPWORDS_EN:
        words.pop()
    return " ".join(words)


def def_extract_keywords(sentences: Sequence[SentenceRecord], language: str, config: EngineConfig) -> tuple[list[KeywordRecord], tuple[str, ...]]:
    text = "\n".join(item.text for item in sentences)
    aggregate = def_keyword_fallback(sentences, language, config.keyword_limit)
    used = ["frequency"]
    optional_extractors = (
        ("YAKE", def_yake_keywords(text, language, config.keyword_limit * 2)),
        ("summa-TextRank", def_summa_keywords(text, config.keyword_limit * 2)),
        ("RAKE-NLTK", def_rake_keywords(text, config.keyword_limit * 2)),
        ("pke-MultipartiteRank", def_pke_keywords(text, language, config.keyword_limit * 2)),
        ("PyTextRank", def_pytextrank_keywords(text, language, config.keyword_limit * 2)),
        ("KeyBERT", def_keybert_keywords(text, config, config.keyword_limit * 2)),
    )
    mutable: dict[str, dict[str, Any]] = {}
    for term, (score, extractors, evidence_ids) in aggregate.items():
        clean = def_clean_keyword_term(term)
        if not clean:
            continue
        key = clean.casefold()
        item = mutable.setdefault(key, {"term": clean, "scores": [], "extractors": set(), "evidence": set()})
        item["scores"].append(score)
        item["extractors"].update(extractors)
        item["evidence"].update(evidence_ids)
    for extractor, pairs in optional_extractors:
        if not pairs:
            continue
        used.append(extractor)
        for term, score in pairs:
            clean = def_clean_keyword_term(term)
            if not clean or len(clean) > 80:
                continue
            if not def_meaningful_tokens(clean, def_language_heuristic(clean)):
                continue
            key = clean.casefold()
            item = mutable.setdefault(key, {"term": clean, "scores": [], "extractors": set(), "evidence": set()})
            item["scores"].append(max(0.0, min(1.0, score)))
            item["extractors"].add(extractor)
            item["evidence"].update(def_find_evidence_ids(clean, sentences))
    records: list[KeywordRecord] = []
    for item in mutable.values():
        term = item["term"]
        if not def_meaningful_tokens(term, def_language_heuristic(term)):
            continue
        if re.search(r"[\u3400-\u9fff]", term) and any(boundary in term for boundary in CJK_BOUNDARY_TERMS):
            continue
        canonical = def_canonical_term(term, language)
        if canonical.casefold() in STOPWORDS_ZH or canonical.casefold() in STOPWORDS_EN:
            continue
        agreement_bonus = min(0.15, 0.04 * (len(item["extractors"]) - 1))
        score = min(1.0, statistics.fmean(item["scores"]) + agreement_bonus)
        records.append(KeywordRecord(
            term=term,
            canonical_term=canonical,
            language=def_language_heuristic(term),
            term_type=def_term_type(canonical),
            score=round(score, 6),
            extractors=tuple(sorted(item["extractors"])),
            evidence_sentence_ids=tuple(sorted(item["evidence"])),
        ))
    records.sort(key=lambda item: (-len(item.extractors), -item.score, item.canonical_term.casefold()))
    deduplicated: list[KeywordRecord] = []
    for candidate in records:
        if any(def_similarity(candidate.canonical_term, existing.canonical_term) >= config.term_alias_similarity for existing in deduplicated):
            continue
        deduplicated.append(candidate)
        if len(deduplicated) >= config.keyword_limit:
            break
    return deduplicated, tuple(used)


def def_extract_entities(sentences: Sequence[SentenceRecord], language: str) -> tuple[list[KeywordRecord], tuple[str, ...]]:
    entities: dict[str, dict[str, Any]] = {}
    used = ["regex_entities"]
    for sentence in sentences:
        for value in re.findall(TICKER_PATTERN, sentence.text):
            item = entities.setdefault(value, {"type": "ticker", "score": 0.98, "ids": set(), "extractors": {"regex"}})
            item["ids"].add(sentence.sentence_id)
        for value in re.findall(r"\b[A-Z][A-Za-z0-9&.\-]{1,20}(?:\s+[A-Z][A-Za-z0-9&.\-]{1,20}){0,3}\b", sentence.text):
            if value.casefold() in STOPWORDS_EN:
                continue
            item = entities.setdefault(value, {"type": def_term_type(value), "score": 0.65, "ids": set(), "extractors": {"regex"}})
            item["ids"].add(sentence.sentence_id)
    model_name = DEFAULT_SPACY_EN_MODEL if language == "en" else DEFAULT_SPACY_ZH_MODEL
    nlp = def_spacy_pipeline(model_name)
    if nlp is not None:
        try:
            doc = nlp("\n".join(item.text for item in sentences))
            used.append(f"spaCy-NER:{model_name}")
            for entity in doc.ents:
                value = entity.text.strip()
                if not value:
                    continue
                evidence = def_find_evidence_ids(value, sentences)
                item = entities.setdefault(value, {"type": entity.label_.casefold(), "score": 0.85, "ids": set(), "extractors": set()})
                item["ids"].update(evidence)
                item["extractors"].add("spaCy-NER")
        except Exception:
            pass
    results = [KeywordRecord(
        term=term,
        canonical_term=def_canonical_term(term, language),
        language=def_language_heuristic(term),
        term_type=item["type"],
        score=item["score"],
        extractors=tuple(sorted(item["extractors"])),
        evidence_sentence_ids=tuple(sorted(item["ids"])),
    ) for term, item in entities.items()]
    results.sort(key=lambda item: (-item.score, item.canonical_term))
    return results[:50], tuple(used)


def def_match_approved_terms(sentences: Sequence[SentenceRecord], registry: Mapping[str, sqlite3.Row], language: str) -> tuple[list[KeywordRecord], str]:
    if not registry:
        return [], "approved_registry_empty"
    hits: dict[str, set[int]] = defaultdict(set)
    canonical_by_key = {key: str(row["canonical_term"]) for key, row in registry.items() if row["status"] == "APPROVED"}
    flashtext = def_optional_module("flashtext")
    if flashtext is not None:
        try:
            processor = flashtext.KeywordProcessor(case_sensitive=False)
            for key, canonical in canonical_by_key.items():
                processor.add_keyword(canonical, key)
            for sentence in sentences:
                for key in processor.extract_keywords(sentence.text):
                    hits[key].add(sentence.sentence_id)
            adapter = "FlashText-approved-registry"
        except Exception:
            hits.clear()
            adapter = "regex-approved-registry"
    else:
        adapter = "regex-approved-registry"
    if not hits:
        for key, canonical in canonical_by_key.items():
            pattern = re.escape(canonical)
            if re.fullmatch(r"[A-Za-z0-9_.+\-]+", canonical):
                pattern = rf"(?<![\w]){pattern}(?![\w])"
            for sentence in sentences:
                if re.search(pattern, sentence.text, flags=re.I):
                    hits[key].add(sentence.sentence_id)
    records = [KeywordRecord(
        term=canonical_by_key[key],
        canonical_term=canonical_by_key[key],
        language=def_language_heuristic(canonical_by_key[key]),
        term_type=str(registry[key]["category"]),
        score=1.0,
        extractors=(adapter,),
        evidence_sentence_ids=tuple(sorted(sentence_ids)),
        status="APPROVED",
    ) for key, sentence_ids in hits.items()]
    return records, adapter


def def_merge_keywords(candidates: Sequence[KeywordRecord], approved_hits: Sequence[KeywordRecord], limit: int) -> list[KeywordRecord]:
    merged: dict[str, KeywordRecord] = {item.canonical_term.casefold(): item for item in candidates}
    for approved in approved_hits:
        key = approved.canonical_term.casefold()
        existing = merged.get(key)
        if existing is None:
            merged[key] = approved
            continue
        merged[key] = dataclasses.replace(
            existing,
            score=max(existing.score, approved.score),
            extractors=tuple(sorted(set(existing.extractors) | set(approved.extractors))),
            evidence_sentence_ids=tuple(sorted(set(existing.evidence_sentence_ids) | set(approved.evidence_sentence_ids))),
            status="APPROVED",
        )
    rows = list(merged.values())
    rows.sort(key=lambda item: (item.status != "APPROVED", -len(item.extractors), -item.score, item.canonical_term.casefold()))
    return rows[:limit]


# =============================================================================
# def 09 EXACTLY-FOUR SUMMARY SYNTHESIS AND LOCAL LLM ADAPTERS
# =============================================================================

def def_contains_any(text: str, patterns: Sequence[str]) -> bool:
    return any(re.search(pattern, text, flags=re.I) for pattern in patterns)


def def_is_summary_quality_sentence(sentence: SentenceRecord) -> bool:
    text = sentence.text.strip()
    if def_contains_any(text, BOILERPLATE_PATTERNS):
        return False
    if re.search(r"https?://|\[\[?\d+\]?\]\(", text, flags=re.I):
        return False
    if re.search(r"requests?\.post|json\s*=|pip install|ollama run|llama\.cpp\s+via|^```|^\|", text, flags=re.I):
        return False
    if text.count("|") >= 3 or text.rstrip().endswith(("?", "？")):
        return False
    return True


def def_select_role_sentence(role: str, ranked: Sequence[SentenceRecord], used_ids: set[int]) -> Optional[SentenceRecord]:
    quality_ranked = [item for item in ranked if def_is_summary_quality_sentence(item)] or list(ranked)
    available = [item for item in quality_ranked if item.sentence_id not in used_ids]
    if role == "core_conclusion":
        substantial = [item for item in available if len(item.text.strip()) >= 18]
        role_scope = substantial or available
    else:
        role_scope = quality_ranked
    if not role_scope:
        return None
    if role == "facts_and_numbers":
        matches = [item for item in role_scope if def_extract_factual_number_tokens(item.text) or re.search(DATE_PATTERN, item.text)]
    elif role == "impact_risk_opportunity":
        matches = [item for item in role_scope if def_contains_any(item.text, RISK_PATTERNS)]
    elif role == "next_step_or_gap":
        matches = [item for item in role_scope if def_contains_any(item.text, ACTION_PATTERNS)]
    else:
        matches = role_scope
    if role != "core_conclusion" and not matches:
        return None
    return (matches or available)[0]


def def_extractive_four_bullets(ranked: Sequence[SentenceRecord], language: str, config: EngineConfig) -> list[SummaryBullet]:
    bullets: list[SummaryBullet] = []
    used_ids: set[int] = set()
    for role, headline_zh, headline_en in SUMMARY_ROLES:
        sentence = def_select_role_sentence(role, ranked, used_ids)
        headline = headline_en if language == "en" else headline_zh
        if sentence is None:
            detail = "Not Provided / To Be Confirmed" if language == "en" else "未提供／待確認"
            evidence_ids: tuple[int, ...] = ()
            validation = "INFORMATION_GAP"
        else:
            detail = def_truncate_sentence(sentence.text, sentence.language, config.bullet_char_limit_zh, config.bullet_word_limit_en)
            evidence_ids = (sentence.sentence_id,)
            validation = "EVIDENCE_LINKED"
            used_ids.add(sentence.sentence_id)
        bullets.append(SummaryBullet(role, headline, detail, evidence_ids, validation))
    return bullets


def def_llm_prompt(evidence: Sequence[SentenceRecord], language: str) -> str:
    output_language = {"en": "English", "zh-CN": "Simplified Chinese", "zh-TW": "Traditional Chinese"}.get(language, "Traditional Chinese")
    evidence_text = "\n".join(f"[S{item.sentence_id}] {item.text}" for item in evidence)
    schema = {
        "summary_bullets": [
            {"role": role, "headline": zh if language != "en" else en, "detail": "...", "evidence_sentence_ids": [1]}
            for role, zh, en in SUMMARY_ROLES
        ]
    }
    return (
        "You are a local evidence-bound summarizer. Return JSON only. "
        f"Write in {output_language}. Produce exactly four bullets in the supplied role order. "
        "Never invent numbers, dates, names, causality, or recommendations. Every non-gap bullet must cite valid sentence IDs. "
        "If evidence is absent, write 未提供／待確認 or Not Provided / To Be Confirmed and use an empty ID list. "
        f"Schema: {def_json_dumps(schema, indent=None)}\nEvidence:\n{evidence_text}"
    )


def def_parse_json_object(text: str) -> dict[str, Any]:
    clean = text.strip()
    clean = re.sub(r"^```(?:json)?\s*|\s*```$", "", clean, flags=re.I)
    try:
        value = json.loads(clean)
        return value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        start, end = clean.find("{"), clean.rfind("}")
        if start >= 0 and end > start:
            try:
                value = json.loads(clean[start:end + 1])
                return value if isinstance(value, dict) else {}
            except json.JSONDecodeError:
                return {}
    return {}


def def_call_ollama(prompt: str, config: EngineConfig) -> str:
    parsed = urllib.parse.urlparse(config.ollama_url)
    if parsed.hostname not in ("127.0.0.1", "localhost", "::1"):
        raise ValueError("OLLAMA_URL_MUST_BE_LOOPBACK")
    if not config.ollama_model:
        raise ValueError("OLLAMA_MODEL_NOT_CONFIGURED")
    payload = {
        "model": config.ollama_model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "num_thread": config.cpu_threads,
            "num_ctx": config.llm_context,
            "num_predict": config.llm_max_tokens,
            "temperature": config.llm_temperature,
            "seed": config.random_seed,
        },
    }
    request = urllib.request.Request(
        config.ollama_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        decoded = json.loads(response.read().decode("utf-8"))
    return str(decoded.get("response", ""))


def def_call_llama_cpp(prompt: str, config: EngineConfig) -> str:
    llama_cpp = def_optional_module("llama_cpp")
    model_path = pathlib.Path(config.llm_model_path)
    if llama_cpp is None or not model_path.is_file():
        raise RuntimeError("LLAMA_CPP_MODEL_UNAVAILABLE")
    model_key = (str(model_path.resolve()), config.llm_context, config.cpu_threads)
    with _RUNTIME_CACHE_LOCK:
        model = _LLAMA_MODEL_CACHE.get(model_key)
        if model is None:
            model = llama_cpp.Llama(
                model_path=model_key[0],
                n_ctx=config.llm_context,
                n_threads=config.cpu_threads,
                n_threads_batch=max(1, config.cpu_threads // 2),
                verbose=False,
            )
            _LLAMA_MODEL_CACHE[model_key] = model
    response = model.create_chat_completion(
        messages=[{"role": "user", "content": prompt}],
        temperature=config.llm_temperature,
        max_tokens=config.llm_max_tokens,
        response_format={"type": "json_object"},
        seed=config.random_seed,
    )
    return str(response["choices"][0]["message"]["content"])


def def_hf_tokenizer(model_path: pathlib.Path) -> Any:
    transformers = def_optional_module("transformers")
    if transformers is None:
        raise RuntimeError("TRANSFORMERS_UNAVAILABLE")
    key = ("tokenizer", str(model_path.resolve()))
    with _RUNTIME_CACHE_LOCK:
        tokenizer = _GENERATION_MODEL_CACHE.get(key)
        if tokenizer is None:
            tokenizer = transformers.AutoTokenizer.from_pretrained(str(model_path), local_files_only=True)
            _GENERATION_MODEL_CACHE[key] = tokenizer
    return tokenizer


def def_hf_generate(model: Any, tokenizer: Any, prompt: str, config: EngineConfig, causal: bool) -> str:
    torch = def_optional_module("torch")
    if torch is not None:
        with contextlib.suppress(Exception):
            torch.set_num_threads(config.cpu_threads)
    maximum_input = max(256, config.llm_context - config.llm_max_tokens)
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=maximum_input)
    output_ids = model.generate(
        **inputs,
        max_new_tokens=config.llm_max_tokens,
        do_sample=False,
        num_beams=1,
    )
    tokens = output_ids[0][inputs["input_ids"].shape[-1]:] if causal else output_ids[0]
    return str(tokenizer.decode(tokens, skip_special_tokens=True))


def def_call_transformers(prompt: str, config: EngineConfig) -> str:
    transformers = def_optional_module("transformers")
    model_path = pathlib.Path(config.llm_model_path)
    if transformers is None or not model_path.exists():
        raise RuntimeError("LOCAL_TRANSFORMERS_MODEL_UNAVAILABLE")
    tokenizer = def_hf_tokenizer(model_path)
    for architecture, model_class, causal in (
        ("seq2seq", transformers.AutoModelForSeq2SeqLM, False),
        ("causal", transformers.AutoModelForCausalLM, True),
    ):
        key = ("transformers", architecture, str(model_path.resolve()))
        try:
            with _RUNTIME_CACHE_LOCK:
                model = _GENERATION_MODEL_CACHE.get(key)
                if model is None:
                    model = model_class.from_pretrained(str(model_path), local_files_only=True)
                    model.eval()
                    _GENERATION_MODEL_CACHE[key] = model
            return def_hf_generate(model, tokenizer, prompt, config, causal)
        except Exception:
            continue
    raise RuntimeError("LOCAL_TRANSFORMERS_MODEL_LOAD_FAILED")


def def_call_onnx(prompt: str, config: EngineConfig) -> str:
    model_path = pathlib.Path(config.llm_model_path)
    if not model_path.exists() or def_optional_module("onnxruntime") is None or def_optional_module("optimum") is None:
        raise RuntimeError("LOCAL_ONNX_MODEL_UNAVAILABLE")
    optimum_ort = importlib.import_module("optimum.onnxruntime")
    tokenizer = def_hf_tokenizer(model_path)
    key = ("onnx", "seq2seq", str(model_path.resolve()))
    with _RUNTIME_CACHE_LOCK:
        model = _GENERATION_MODEL_CACHE.get(key)
        if model is None:
            model = optimum_ort.ORTModelForSeq2SeqLM.from_pretrained(
                str(model_path), local_files_only=True, provider="CPUExecutionProvider"
            )
            _GENERATION_MODEL_CACHE[key] = model
    return def_hf_generate(model, tokenizer, prompt, config, causal=False)


def def_call_ctranslate2(prompt: str, config: EngineConfig) -> str:
    ctranslate2 = def_optional_module("ctranslate2")
    model_path = pathlib.Path(config.llm_model_path)
    if ctranslate2 is None or not model_path.is_dir():
        raise RuntimeError("LOCAL_CTRANSLATE2_MODEL_UNAVAILABLE")
    tokenizer = def_hf_tokenizer(model_path)
    key = ("ctranslate2", str(model_path.resolve()), str(config.cpu_threads))
    with _RUNTIME_CACHE_LOCK:
        translator = _GENERATION_MODEL_CACHE.get(key)
        if translator is None:
            translator = ctranslate2.Translator(
                str(model_path), device="cpu", inter_threads=1, intra_threads=config.cpu_threads
            )
            _GENERATION_MODEL_CACHE[key] = translator
    source_ids = tokenizer.encode(prompt, truncation=True, max_length=max(256, config.llm_context - config.llm_max_tokens))
    source_tokens = tokenizer.convert_ids_to_tokens(source_ids)
    result = translator.translate_batch(
        [source_tokens], beam_size=1, max_decoding_length=config.llm_max_tokens
    )[0]
    return str(tokenizer.convert_tokens_to_string(result.hypotheses[0]))


def def_infer_ctransformers_type(model_path: pathlib.Path) -> str:
    name = model_path.name.casefold()
    for model_type in ("qwen2", "mistral", "llama", "falcon", "gpt2", "starcoder"):
        if model_type in name:
            return model_type
    return "llama"


def def_call_ctransformers(prompt: str, config: EngineConfig) -> str:
    ctransformers = def_optional_module("ctransformers")
    model_path = pathlib.Path(config.llm_model_path)
    if ctransformers is None or not model_path.is_file():
        raise RuntimeError("LOCAL_CTRANSFORMERS_MODEL_UNAVAILABLE")
    key = ("ctransformers", str(model_path.resolve()), str(config.cpu_threads))
    with _RUNTIME_CACHE_LOCK:
        model = _GENERATION_MODEL_CACHE.get(key)
        if model is None:
            model = ctransformers.AutoModelForCausalLM.from_pretrained(
                str(model_path.parent), model_file=model_path.name,
                model_type=def_infer_ctransformers_type(model_path),
                context_length=config.llm_context, threads=config.cpu_threads,
            )
            _GENERATION_MODEL_CACHE[key] = model
    return str(model(
        prompt, max_new_tokens=config.llm_max_tokens,
        temperature=config.llm_temperature, seed=config.random_seed,
    ))


def def_llm_bullets(ranked: Sequence[SentenceRecord], language: str, config: EngineConfig) -> tuple[Optional[list[SummaryBullet]], str]:
    if not config.use_llm:
        return None, "disabled"
    evidence = list(ranked[:config.candidate_sentences])
    prompt = def_llm_prompt(evidence, language)
    backend = config.llm_backend
    try:
        if backend == "ollama" or (backend == "auto" and config.ollama_model):
            raw = def_call_ollama(prompt, config)
            backend_used = "Ollama"
        elif backend in ("llama_cpp", "auto"):
            raw = def_call_llama_cpp(prompt, config)
            backend_used = "llama.cpp"
        elif backend == "transformers":
            raw = def_call_transformers(prompt, config)
            backend_used = "Transformers"
        elif backend == "onnx":
            raw = def_call_onnx(prompt, config)
            backend_used = "Optimum+ONNX Runtime"
        elif backend == "ctranslate2":
            raw = def_call_ctranslate2(prompt, config)
            backend_used = "CTranslate2"
        elif backend == "ctransformers":
            raw = def_call_ctransformers(prompt, config)
            backend_used = "ctransformers"
        else:
            return None, f"unsupported:{backend}"
        parsed = def_parse_json_object(raw)
        rows = parsed.get("summary_bullets", [])
        if not isinstance(rows, list) or len(rows) != DEFAULT_SUMMARY_BULLETS:
            return None, f"{backend_used}:invalid_schema"
        output: list[SummaryBullet] = []
        valid_ids = {item.sentence_id for item in evidence}
        for index, row in enumerate(rows):
            if not isinstance(row, Mapping):
                return None, f"{backend_used}:invalid_row"
            role, default_zh, default_en = SUMMARY_ROLES[index]
            ids = tuple(sorted({int(item) for item in row.get("evidence_sentence_ids", []) if str(item).isdigit() and int(item) in valid_ids}))
            output.append(SummaryBullet(
                role=role,
                headline=str(row.get("headline") or (default_en if language == "en" else default_zh)),
                detail=str(row.get("detail", "")).strip(),
                evidence_sentence_ids=ids,
                validation_status="PENDING_VALIDATION",
            ))
        return output, backend_used
    except Exception as exc:
        return None, f"failed:{type(exc).__name__}"


def def_validate_bullets(bullets: Sequence[SummaryBullet], sentences: Sequence[SentenceRecord], language: str, config: EngineConfig) -> tuple[list[SummaryBullet], tuple[str, ...]]:
    warnings: list[str] = []
    sentence_map = {item.sentence_id: item.text for item in sentences}
    validated: list[SummaryBullet] = []
    for index, expected in enumerate(SUMMARY_ROLES):
        if index >= len(bullets):
            role, zh, en = expected
            validated.append(SummaryBullet(role, en if language == "en" else zh, "Not Provided / To Be Confirmed" if language == "en" else "未提供／待確認", (), "INFORMATION_GAP"))
            warnings.append(f"BULLET_{index + 1}_MISSING")
            continue
        bullet = bullets[index]
        valid_ids = tuple(item for item in bullet.evidence_sentence_ids if item in sentence_map)
        evidence_text = " ".join(sentence_map[item] for item in valid_ids)
        generated_numbers = set(def_extract_number_tokens(bullet.detail))
        evidence_numbers = set(def_extract_number_tokens(evidence_text))
        numeric_ok = not generated_numbers or generated_numbers.issubset(evidence_numbers)
        detail_language = def_language_heuristic(bullet.detail)
        detail = def_truncate_sentence(bullet.detail, detail_language, config.bullet_char_limit_zh, config.bullet_word_limit_en)
        if config.strict_numeric_evidence and not numeric_ok:
            warnings.append(f"BULLET_{index + 1}_UNSUPPORTED_NUMBER")
            if valid_ids:
                evidence_language = def_language_heuristic(sentence_map[valid_ids[0]])
                detail = def_truncate_sentence(sentence_map[valid_ids[0]], evidence_language, config.bullet_char_limit_zh, config.bullet_word_limit_en)
                numeric_ok = True
            else:
                detail = "Not Provided / To Be Confirmed" if language == "en" else "未提供／待確認"
        if not valid_ids and detail not in ("未提供／待確認", "Not Provided / To Be Confirmed"):
            warnings.append(f"BULLET_{index + 1}_NO_EVIDENCE")
            detail = "Not Provided / To Be Confirmed" if language == "en" else "未提供／待確認"
        status = "EVIDENCE_LINKED" if valid_ids and numeric_ok else "INFORMATION_GAP"
        validated.append(dataclasses.replace(bullet, detail=detail, evidence_sentence_ids=valid_ids, validation_status=status))
    return validated[:DEFAULT_SUMMARY_BULLETS], tuple(warnings)


# =============================================================================
# def 10 SQLITE SSOT, APPEND-ONLY EVIDENCE AND CHECKPOINTS
# =============================================================================

SCHEMA_SQL = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS engine_registry_events (
  event_id TEXT PRIMARY KEY, engine_name TEXT NOT NULL, engine_version TEXT NOT NULL,
  classification TEXT NOT NULL, owner TEXT NOT NULL, governance TEXT NOT NULL,
  event_type TEXT NOT NULL, payload_json TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS documents (
  document_id TEXT PRIMARY KEY, content_sha256 TEXT NOT NULL, source_name TEXT NOT NULL,
  raw_text TEXT NOT NULL, normalized_text TEXT NOT NULL, language TEXT NOT NULL,
  source_metadata_json TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_documents_hash ON documents(content_sha256);
CREATE TABLE IF NOT EXISTS runs (
  run_id TEXT PRIMARY KEY, document_id TEXT NOT NULL, config_sha256 TEXT NOT NULL,
  status TEXT NOT NULL, warnings_json TEXT NOT NULL, capabilities_json TEXT NOT NULL,
  resource_json TEXT NOT NULL, result_json TEXT NOT NULL, created_at TEXT NOT NULL,
  FOREIGN KEY(document_id) REFERENCES documents(document_id)
);
CREATE INDEX IF NOT EXISTS idx_runs_resume ON runs(document_id, config_sha256, status);
CREATE TABLE IF NOT EXISTS process_log (
  event_id TEXT PRIMARY KEY, run_id TEXT NOT NULL, stage TEXT NOT NULL,
  status TEXT NOT NULL, message TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sentence_evidence (
  evidence_id TEXT PRIMARY KEY, run_id TEXT NOT NULL, sentence_id INTEGER NOT NULL,
  paragraph_id INTEGER NOT NULL, position_index INTEGER NOT NULL, language TEXT NOT NULL,
  sentence_text TEXT NOT NULL, score REAL NOT NULL, extractors_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS summary_bullets (
  bullet_id TEXT PRIMARY KEY, run_id TEXT NOT NULL, bullet_index INTEGER NOT NULL,
  role TEXT NOT NULL, headline TEXT NOT NULL, detail TEXT NOT NULL,
  evidence_sentence_ids_json TEXT NOT NULL, validation_status TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS term_candidates (
  candidate_id TEXT PRIMARY KEY, run_id TEXT NOT NULL, document_id TEXT NOT NULL,
  term TEXT NOT NULL, normalized_term TEXT NOT NULL, canonical_term TEXT NOT NULL,
  language TEXT NOT NULL, term_type TEXT NOT NULL, score REAL NOT NULL,
  extractors_json TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_term_candidates_canonical ON term_candidates(canonical_term);
CREATE TABLE IF NOT EXISTS term_evidence (
  evidence_id TEXT PRIMARY KEY, candidate_id TEXT NOT NULL, document_id TEXT NOT NULL,
  sentence_id INTEGER NOT NULL, context TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS term_registry_events (
  event_id TEXT PRIMARY KEY, canonical_term TEXT NOT NULL, category TEXT NOT NULL,
  language TEXT NOT NULL, status TEXT NOT NULL, promotion_score REAL NOT NULL,
  reason TEXT NOT NULL, source_candidate_id TEXT, created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_term_registry_term ON term_registry_events(canonical_term, created_at);
CREATE TABLE IF NOT EXISTS term_aliases (
  alias_id TEXT PRIMARY KEY, alias TEXT NOT NULL, canonical_term TEXT NOT NULL,
  alias_type TEXT NOT NULL, evidence TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS term_metrics (
  metric_id TEXT PRIMARY KEY, canonical_term TEXT NOT NULL, document_frequency INTEGER NOT NULL,
  mean_keyword_score REAL NOT NULL, entity_confidence REAL NOT NULL, recency_score REAL NOT NULL,
  promotion_score REAL NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS term_blacklist_events (
  event_id TEXT PRIMARY KEY, term TEXT NOT NULL, reason TEXT NOT NULL,
  scope TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL
);
"""


class SSOTStore:
    def __init__(self, path: str | pathlib.Path):
        self.path = pathlib.Path(path).expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.connection = sqlite3.connect(str(self.path), timeout=DEFAULT_SQLITE_BUSY_TIMEOUT_MS / 1000, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute(f"PRAGMA busy_timeout={DEFAULT_SQLITE_BUSY_TIMEOUT_MS}")
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=NORMAL")
        self.connection.execute(f"PRAGMA wal_autocheckpoint={DEFAULT_WAL_AUTOCHECKPOINT}")
        self.connection.executescript(SCHEMA_SQL)
        self.connection.commit()
        self.def_register_engine_event()

    def __enter__(self) -> "SSOTStore":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()

    def close(self) -> None:
        with self._lock:
            self.connection.commit()
            self.connection.close()

    def def_register_engine_event(self) -> None:
        payload = {"activation": False, "runtime": "local", "network": "prohibited_except_loopback_ollama"}
        with self._lock:
            self.connection.execute(
                "INSERT OR IGNORE INTO engine_registry_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (def_sha256_text(f"{ENGINE_NAME}:{ENGINE_VERSION}"), ENGINE_NAME, ENGINE_VERSION,
                 ENGINE_CLASSIFICATION, ENGINE_OWNER, ENGINE_GOVERNANCE, "APPEND_REGISTERED",
                 def_json_dumps(payload, indent=None), def_now_iso()),
            )
            self.connection.commit()

    def def_log(self, run_id: str, stage: str, status: str, message: str) -> None:
        with self._lock:
            self.connection.execute(
                "INSERT INTO process_log VALUES (?, ?, ?, ?, ?, ?)",
                (uuid.uuid4().hex, run_id, stage, status, message[:4_000], def_now_iso()),
            )
            self.connection.commit()

    def def_config_sha(self, config: EngineConfig) -> str:
        material = dataclasses.asdict(config)
        material["_engine_name"] = ENGINE_NAME
        material["_engine_version"] = ENGINE_VERSION
        material.pop("output_dir", None)
        material.pop("temp_root", None)
        material.pop("db_path", None)
        return def_sha256_text(def_json_dumps(material, indent=None))

    def def_resume_result(self, content_sha256: str, config: EngineConfig) -> Optional[dict[str, Any]]:
        config_sha = self.def_config_sha(config)
        row = self.connection.execute(
            "SELECT r.result_json, d.normalized_text FROM runs r JOIN documents d ON d.document_id=r.document_id "
            "WHERE d.content_sha256=? AND r.config_sha256=? AND r.status='PASS' ORDER BY r.created_at DESC LIMIT 1",
            (content_sha256, config_sha),
        ).fetchone()
        if not row:
            return None
        payload = json.loads(row["result_json"])
        payload["normalized_text"] = row["normalized_text"]
        return payload

    def def_insert_document(self, document_id: str, content_sha256: str, source_name: str, raw_text: str, normalized_text: str, language: str, metadata: Mapping[str, Any]) -> None:
        with self._lock:
            self.connection.execute(
                "INSERT OR IGNORE INTO documents VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (document_id, content_sha256, source_name, raw_text, normalized_text, language,
                 def_json_dumps(metadata, indent=None), def_now_iso()),
            )
            self.connection.commit()

    def def_insert_run(self, result: SummaryResult, config: EngineConfig, ranked: Sequence[SentenceRecord]) -> None:
        with self._lock:
            now = result.created_at
            self.connection.execute("BEGIN IMMEDIATE")
            try:
                self.connection.execute(
                    "INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (result.run_id, result.document_id, self.def_config_sha(config), result.status,
                     def_json_dumps(result.warnings, indent=None), def_json_dumps(result.capabilities_used, indent=None),
                     def_json_dumps(dataclasses.asdict(result.resource_snapshot), indent=None),
                     def_json_dumps(result.to_dict(include_text=False), indent=None), now),
                )
                for sentence in ranked:
                    self.connection.execute(
                        "INSERT INTO sentence_evidence VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (uuid.uuid4().hex, result.run_id, sentence.sentence_id, sentence.paragraph_id,
                         sentence.position, sentence.language, sentence.text, sentence.score,
                         def_json_dumps(sentence.extractors, indent=None), now),
                    )
                for index, bullet in enumerate(result.summary_bullets, start=1):
                    self.connection.execute(
                        "INSERT INTO summary_bullets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (uuid.uuid4().hex, result.run_id, index, bullet.role, bullet.headline, bullet.detail,
                         def_json_dumps(bullet.evidence_sentence_ids, indent=None), bullet.validation_status, now),
                    )
                for keyword in result.keywords:
                    candidate_id = uuid.uuid4().hex
                    self.connection.execute(
                        "INSERT INTO term_candidates VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (candidate_id, result.run_id, result.document_id, keyword.term, keyword.term.casefold(),
                         keyword.canonical_term, keyword.language, keyword.term_type, keyword.score,
                         def_json_dumps(keyword.extractors, indent=None), keyword.status, now),
                    )
                    for sentence_id in keyword.evidence_sentence_ids:
                        context = next((item.text for item in ranked if item.sentence_id == sentence_id), "")
                        self.connection.execute(
                            "INSERT INTO term_evidence VALUES (?, ?, ?, ?, ?, ?)",
                            (uuid.uuid4().hex, candidate_id, result.document_id, sentence_id, context, now),
                        )
                self.connection.commit()
            except Exception:
                self.connection.rollback()
                raise

    def def_latest_registry_terms(self) -> dict[str, sqlite3.Row]:
        rows = self.connection.execute(
            "SELECT e.* FROM term_registry_events e JOIN "
            "(SELECT canonical_term, MAX(created_at) latest FROM term_registry_events GROUP BY canonical_term) x "
            "ON x.canonical_term=e.canonical_term AND x.latest=e.created_at"
        ).fetchall()
        return {row["canonical_term"].casefold(): row for row in rows}

    def def_active_blacklist(self) -> set[str]:
        rows = self.connection.execute(
            "SELECT term FROM term_blacklist_events WHERE status='ACTIVE'"
        ).fetchall()
        return {str(row["term"]).casefold() for row in rows}

    def def_calculate_term_metrics(self, canonical_term: str, min_documents: int = DEFAULT_TERM_MIN_DOCUMENTS) -> dict[str, float]:
        rows = self.connection.execute(
            "SELECT document_id, score, extractors_json, term_type, created_at FROM term_candidates WHERE canonical_term=?",
            (canonical_term,),
        ).fetchall()
        documents = len({row["document_id"] for row in rows})
        mean_score = statistics.fmean([float(row["score"]) for row in rows]) if rows else 0.0
        entity_confidence = max((0.9 if row["term_type"] in ("ticker", "organization") else 0.55 for row in rows), default=0.0)
        recency = 1.0 if rows else 0.0
        document_score = min(1.0, documents / max(1, min_documents))
        promotion = (
            PROMOTION_WEIGHTS["document_frequency"] * document_score
            + PROMOTION_WEIGHTS["mean_keyword_score"] * mean_score
            + PROMOTION_WEIGHTS["entity_confidence"] * entity_confidence
            + PROMOTION_WEIGHTS["recency_score"] * recency
        )
        return {
            "document_frequency": float(documents),
            "mean_keyword_score": mean_score,
            "entity_confidence": entity_confidence,
            "recency_score": recency,
            "promotion_score": promotion,
        }

    def def_append_term_metrics_and_aliases(self, keywords: Sequence[KeywordRecord], config: EngineConfig) -> list[str]:
        """Append metric snapshots and alias evidence without changing approved terms."""
        latest = self.def_latest_registry_terms()
        inserted_aliases: list[str] = []
        now = def_now_iso()
        with self._lock:
            self.connection.execute("BEGIN IMMEDIATE")
            try:
                for keyword in keywords:
                    metrics = self.def_calculate_term_metrics(keyword.canonical_term, config.term_min_documents)
                    self.connection.execute(
                        "INSERT INTO term_metrics VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (uuid.uuid4().hex, keyword.canonical_term, int(metrics["document_frequency"]),
                         metrics["mean_keyword_score"], metrics["entity_confidence"],
                         metrics["recency_score"], metrics["promotion_score"], now),
                    )
                    if keyword.term.casefold() != keyword.canonical_term.casefold():
                        self.connection.execute(
                            "INSERT INTO term_aliases VALUES (?, ?, ?, ?, ?, ?)",
                            (uuid.uuid4().hex, keyword.term, keyword.canonical_term,
                             "NORMALIZATION_ALIAS", "OPENCC_OR_CASE_NORMALIZATION", now),
                        )
                        inserted_aliases.append(f"{keyword.term}->{keyword.canonical_term}")
                    best_term = ""
                    best_score = 0.0
                    for approved_key, approved_row in latest.items():
                        similarity = def_similarity(keyword.canonical_term.casefold(), approved_key)
                        if similarity > best_score:
                            best_term, best_score = approved_row["canonical_term"], similarity
                    if best_term and best_term.casefold() != keyword.canonical_term.casefold() and best_score >= config.term_alias_similarity:
                        self.connection.execute(
                            "INSERT INTO term_aliases VALUES (?, ?, ?, ?, ?, ?)",
                            (uuid.uuid4().hex, keyword.canonical_term, best_term,
                             "FUZZY_APPROVED_ALIAS", f"RapidFuzzOrFallback={best_score:.2f}", now),
                        )
                        inserted_aliases.append(f"{keyword.canonical_term}->{best_term}")
                self.connection.commit()
            except Exception:
                self.connection.rollback()
                raise
        return inserted_aliases

    def def_promote_eligible_terms(self, config: EngineConfig) -> list[str]:
        if not config.auto_promote:
            return []
        promoted: list[str] = []
        candidates = self.connection.execute("SELECT DISTINCT canonical_term FROM term_candidates").fetchall()
        latest = self.def_latest_registry_terms()
        with self._lock:
            self.connection.execute("BEGIN IMMEDIATE")
            try:
                for row in candidates:
                    term = row["canonical_term"]
                    if term.casefold() in latest:
                        continue
                    metrics = self.def_calculate_term_metrics(term, config.term_min_documents)
                    extractor_rows = self.connection.execute(
                        "SELECT extractors_json FROM term_candidates WHERE canonical_term=?", (term,)
                    ).fetchall()
                    extractors = set()
                    for extractor_row in extractor_rows:
                        extractors.update(json.loads(extractor_row["extractors_json"]))
                    if metrics["document_frequency"] < config.term_min_documents:
                        continue
                    if len(extractors) < config.term_min_extractors:
                        continue
                    if metrics["promotion_score"] < config.promotion_threshold:
                        continue
                    term_row = self.connection.execute(
                        "SELECT candidate_id, term_type, language FROM term_candidates WHERE canonical_term=? ORDER BY score DESC LIMIT 1", (term,)
                    ).fetchone()
                    metric_id = uuid.uuid4().hex
                    self.connection.execute(
                        "INSERT INTO term_metrics VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (metric_id, term, int(metrics["document_frequency"]), metrics["mean_keyword_score"],
                         metrics["entity_confidence"], metrics["recency_score"], metrics["promotion_score"], def_now_iso()),
                    )
                    self.connection.execute(
                        "INSERT INTO term_registry_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (uuid.uuid4().hex, term, term_row["term_type"], term_row["language"], "APPROVED",
                         metrics["promotion_score"], "AUTO_PROMOTION_EXPLICITLY_ENABLED", term_row["candidate_id"], def_now_iso()),
                    )
                    promoted.append(term)
                self.connection.commit()
            except Exception:
                self.connection.rollback()
                raise
        return promoted

    def def_list_vocabulary_candidates(self, limit: int = 100) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT canonical_term, COUNT(DISTINCT document_id) AS document_frequency, "
            "AVG(score) AS mean_score, MAX(created_at) AS latest_at "
            "FROM term_candidates GROUP BY canonical_term "
            "ORDER BY document_frequency DESC, mean_score DESC, canonical_term LIMIT ?",
            (max(1, min(limit, 10_000)),),
        ).fetchall()
        latest = self.def_latest_registry_terms()
        status_by_term = {key: str(row["status"]) for key, row in latest.items()}
        return [{
            "canonical_term": row["canonical_term"],
            "document_frequency": int(row["document_frequency"]),
            "mean_score": round(float(row["mean_score"]), 6),
            "latest_at": row["latest_at"],
            "registry_status": status_by_term.get(row["canonical_term"].casefold(), "CANDIDATE"),
        } for row in rows]

    def def_review_term(self, term: str, decision: str, reason: str) -> dict[str, Any]:
        decision = decision.upper()
        if decision not in ("APPROVED", "REJECTED", "BLACKLISTED"):
            raise ValueError("INVALID_VOCABULARY_DECISION")
        candidate = self.connection.execute(
            "SELECT candidate_id, canonical_term, term_type, language FROM term_candidates "
            "WHERE canonical_term=? COLLATE NOCASE OR term=? COLLATE NOCASE ORDER BY score DESC LIMIT 1",
            (term, term),
        ).fetchone()
        if candidate is None:
            raise ValueError(f"TERM_NOT_FOUND:{term}")
        metrics = self.def_calculate_term_metrics(candidate["canonical_term"])
        now = def_now_iso()
        with self._lock:
            self.connection.execute("BEGIN IMMEDIATE")
            try:
                self.connection.execute(
                    "INSERT INTO term_registry_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (uuid.uuid4().hex, candidate["canonical_term"], candidate["term_type"], candidate["language"],
                     decision, metrics["promotion_score"], reason or "EXPLICIT_USER_REVIEW",
                     candidate["candidate_id"], now),
                )
                if decision == "BLACKLISTED":
                    self.connection.execute(
                        "INSERT INTO term_blacklist_events VALUES (?, ?, ?, ?, ?, ?)",
                        (uuid.uuid4().hex, candidate["canonical_term"], reason or "EXPLICIT_USER_REVIEW", "GLOBAL", "ACTIVE", now),
                    )
                self.connection.commit()
            except Exception:
                self.connection.rollback()
                raise
        return {"canonical_term": candidate["canonical_term"], "decision": decision, "reason": reason, "created_at": now}


# =============================================================================
# def 11 ENGINE ORCHESTRATION
# =============================================================================

class VIASummarizerEngine:
    def __init__(self, config: Optional[EngineConfig] = None):
        self.config = config or EngineConfig()
        def_configure_thread_environment(self.config.cpu_threads)
        self.store = SSOTStore(self.config.db_path)

    def close(self) -> None:
        self.store.close()

    def __enter__(self) -> "VIASummarizerEngine":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()

    def def_summarize_text(self, raw_text: str, source_name: str = "direct_text", metadata: Optional[Mapping[str, Any]] = None) -> SummaryResult:
        if not raw_text or not raw_text.strip():
            raise ValueError("EMPTY_INPUT_TEXT")
        run_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
        content_sha = def_sha256_text(raw_text)
        if self.config.resume:
            cached = self.store.def_resume_result(content_sha, self.config)
            if cached:
                LOGGER.info("Resume hit · %s", source_name)
                return def_result_from_dict(cached, raw_text=raw_text)
        gate_ok, snapshot, gate_reasons = def_resource_gate(self.config, self.config.output_dir)
        if not gate_ok and any(reason.startswith(("MEMORY_PRESSURE", "LOW_AVAILABLE_MEMORY", "LOW_FREE_DISK")) for reason in gate_reasons):
            raise RuntimeError("RESOURCE_GATE_HOLD:" + ",".join(gate_reasons))
        self.store.def_log(run_id, "PREFLIGHT", "PASS" if gate_ok else "DEGRADED", ",".join(gate_reasons) or "RESOURCE_GATE_PASS")
        with def_owned_temp_directory(self.config, run_id):
            normalized, language, source_language, normalization_warnings, normalization_used = def_normalize_text(raw_text, self.config)
            document_id = def_sha256_text(f"{content_sha}:{source_name}")[:32]
            source_metadata = dict(metadata or {})
            source_metadata.update({"source_language": source_language, "requested_language": self.config.language})
            self.store.def_insert_document(document_id, content_sha, source_name, raw_text, normalized, language, source_metadata)
            sentences, split_used = def_split_sentences(normalized, language)
            if not sentences:
                raise RuntimeError("NO_SENTENCES_EXTRACTED")
            ranked, rank_used = def_rank_sentences(sentences, language, self.config)
            keywords, keyword_used = def_extract_keywords(sentences, language, self.config)
            blacklist = self.store.def_active_blacklist()
            keywords = [item for item in keywords if item.canonical_term.casefold() not in blacklist]
            approved_hits, registry_used = def_match_approved_terms(
                sentences, self.store.def_latest_registry_terms(), language
            )
            keywords = def_merge_keywords(keywords, approved_hits, self.config.keyword_limit)
            entities, entity_used = def_extract_entities(sentences, language)
            requested_summary_language = self.config.language if self.config.language in ("zh-TW", "zh-CN", "en") else language
            llm_bullets, llm_status = def_llm_bullets(ranked, requested_summary_language, self.config)
            actual_summary_language = requested_summary_language if llm_bullets is not None else language
            base_bullets = llm_bullets or def_extractive_four_bullets(ranked, language, self.config)
            validated_bullets, validation_warnings = def_validate_bullets(
                base_bullets, sentences, actual_summary_language, self.config
            )
            capabilities = tuple(dict.fromkeys(
                normalization_used + split_used + rank_used + keyword_used + ("SSOT-blacklist-filter", registry_used) + entity_used
                + ((llm_status,) if self.config.use_llm else ())
            ))
            llm_warnings: tuple[str, ...] = ()
            if self.config.use_llm and llm_bullets is None:
                llm_warnings = (f"LLM_FALLBACK_TO_EXTRACTIVE:{llm_status}",)
                if self.config.language in ("zh-TW", "zh-CN", "en") and self.config.language != source_language:
                    llm_warnings += ("REQUESTED_TRANSLATION_NOT_COMPLETED",)
            warnings = tuple(normalization_warnings) + tuple(gate_reasons) + validation_warnings + llm_warnings
            result = SummaryResult(
                schema_version="1.0",
                engine=ENGINE_NAME,
                engine_version=ENGINE_VERSION,
                run_id=run_id,
                document_id=document_id,
                content_sha256=content_sha,
                source_name=source_name,
                source_language=source_language,
                requested_language=self.config.language,
                language=actual_summary_language,
                raw_text=raw_text,
                normalized_text=normalized,
                summary_bullets=tuple(validated_bullets),
                keywords=tuple(keywords),
                entities=tuple(entities),
                vocabulary_delta=tuple(keywords),
                warnings=warnings,
                capabilities_used=capabilities,
                resource_snapshot=snapshot,
                created_at=def_now_iso(),
                status="PASS",
            )
            self.store.def_insert_run(result, self.config, ranked)
            aliases = self.store.def_append_term_metrics_and_aliases(result.keywords, self.config)
            if aliases:
                self.store.def_log(run_id, "VOCABULARY_ALIASES", "PASS", def_json_dumps(aliases, indent=None))
            promoted = self.store.def_promote_eligible_terms(self.config)
            if promoted:
                self.store.def_log(run_id, "VOCABULARY_PROMOTION", "PASS", def_json_dumps(promoted, indent=None))
            self.store.def_log(run_id, "FINAL", "PASS", "FOUR_BULLETS_VALIDATED")
            return result

    def def_summarize_file(self, path: str | pathlib.Path) -> SummaryResult:
        text, metadata = def_read_input(path)
        return self.def_summarize_text(text, metadata["source_name"], metadata)

    def def_batch(self, input_dir: str | pathlib.Path, pattern: str = DEFAULT_INPUT_GLOB) -> list[SummaryResult]:
        root = pathlib.Path(input_dir).expanduser().resolve()
        paths = [path for path in root.glob(pattern) if path.is_file() and path.suffix.lower() in SUPPORTED_INPUT_SUFFIXES]
        paths.sort(key=lambda item: str(item).casefold())
        results: list[SummaryResult] = []
        index = 0
        while index < len(paths):
            _, snapshot, _ = def_resource_gate(self.config, root)
            batch_size = def_adaptive_batch_size(self.config, snapshot)
            for path in paths[index:index + batch_size]:
                try:
                    results.append(self.def_summarize_file(path))
                except Exception as exc:
                    LOGGER.error("%s · %s", path.name, exc)
                    self.store.def_log("BATCH", "DOCUMENT", "FAILED", f"{path}:{type(exc).__name__}:{exc}")
            index += batch_size
        return results


def def_result_from_dict(payload: Mapping[str, Any], raw_text: str = "") -> SummaryResult:
    bullets = tuple(SummaryBullet(
        role=item["role"], headline=item["headline"], detail=item["detail"],
        evidence_sentence_ids=tuple(item.get("evidence_sentence_ids", [])),
        validation_status=item["validation_status"],
    ) for item in payload.get("summary_bullets", []))

    def def_restore_keyword(item: Mapping[str, Any]) -> KeywordRecord:
        return KeywordRecord(
            term=item["term"], canonical_term=item["canonical_term"], language=item["language"],
            term_type=item["term_type"], score=float(item["score"]),
            extractors=tuple(item.get("extractors", [])),
            evidence_sentence_ids=tuple(item.get("evidence_sentence_ids", [])),
            status=item.get("status", "CANDIDATE"),
        )

    keywords = tuple(def_restore_keyword(item) for item in payload.get("keywords", []))
    entities = tuple(def_restore_keyword(item) for item in payload.get("entities", []))
    vocabulary = tuple(def_restore_keyword(item) for item in payload.get("vocabulary_delta", []))
    resource = ResourceSnapshot(**payload["resource_snapshot"])
    return SummaryResult(
        schema_version=payload["schema_version"], engine=payload["engine"], engine_version=payload["engine_version"],
        run_id=payload["run_id"], document_id=payload["document_id"], content_sha256=payload["content_sha256"],
        source_name=payload["source_name"], source_language=payload.get("source_language", payload["language"]),
        requested_language=payload.get("requested_language", payload["language"]),
        language=payload["language"], raw_text=raw_text,
        normalized_text=payload.get("normalized_text", ""), summary_bullets=bullets, keywords=keywords,
        entities=entities, vocabulary_delta=vocabulary, warnings=tuple(payload.get("warnings", [])),
        capabilities_used=tuple(payload.get("capabilities_used", [])), resource_snapshot=resource,
        created_at=payload["created_at"], status=payload.get("status", "PASS"),
    )


# =============================================================================
# def 12 EXPORTS — JSON, Markdown, UTF-8-SIG CSV, optional Parquet
# =============================================================================

def def_safe_stem(name: str) -> str:
    stem = pathlib.Path(name).stem or "summary"
    return re.sub(r"[^\w.\-\u3400-\u9fff]+", "_", stem).strip("_.")[:100] or "summary"


def def_markdown(result: SummaryResult) -> str:
    lines = [
        f"# {result.source_name} · 四點摘要",
        "",
        f"- Engine: `{result.engine} {result.engine_version}`",
        f"- Source Language: `{result.source_language}`",
        f"- Requested Language: `{result.requested_language}`",
        f"- Actual Output Language: `{result.language}`",
        f"- Content SHA-256: `{result.content_sha256}`",
        f"- Created: `{result.created_at}`",
        "",
        "## Summary",
        "",
    ]
    for bullet in result.summary_bullets:
        evidence = ", ".join(f"S{item}" for item in bullet.evidence_sentence_ids) or "—"
        lines.append(f"- **{bullet.headline}**：{bullet.detail}  \n  Evidence: `{evidence}` · `{bullet.validation_status}`")
    lines.extend(["", "## Keywords", ""])
    lines.extend(f"- {item.canonical_term} · {item.term_type} · {item.score:.3f} · {', '.join(item.extractors)}" for item in result.keywords)
    if result.warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- `{warning}`" for warning in result.warnings)
    return "\n".join(lines) + "\n"


def def_export_csv(result: SummaryResult, path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=[
                "Run Id", "Document Id", "Source Name", "Source Language", "Requested Language",
                "Actual Output Language", "Bullet Index", "Role",
                "Headline", "Detail", "Evidence Sentence Ids", "Validation Status", "Created At",
            ])
            writer.writeheader()
            for index, bullet in enumerate(result.summary_bullets, start=1):
                writer.writerow({
                    "Run Id": result.run_id, "Document Id": result.document_id, "Source Name": result.source_name,
                    "Source Language": result.source_language, "Requested Language": result.requested_language,
                    "Actual Output Language": result.language, "Bullet Index": index, "Role": bullet.role,
                    "Headline": bullet.headline, "Detail": bullet.detail,
                    "Evidence Sentence Ids": "|".join(map(str, bullet.evidence_sentence_ids)),
                    "Validation Status": bullet.validation_status, "Created At": result.created_at,
                })
        os.replace(temp_name, path)
    except Exception:
        with contextlib.suppress(OSError):
            os.unlink(temp_name)
        raise


def def_export_parquet(result: SummaryResult, path: pathlib.Path, compression: str = DEFAULT_PARQUET_COMPRESSION) -> bool:
    pyarrow = def_optional_module("pyarrow")
    if pyarrow is None:
        return False
    try:
        parquet = importlib.import_module("pyarrow.parquet")
        rows = [{
            "Run Id": result.run_id, "Document Id": result.document_id, "Source Name": result.source_name,
            "Source Language": result.source_language, "Requested Language": result.requested_language,
            "Actual Output Language": result.language, "Bullet Index": index, "Role": bullet.role,
            "Headline": bullet.headline, "Detail": bullet.detail,
            "Evidence Sentence Ids": list(bullet.evidence_sentence_ids),
            "Validation Status": bullet.validation_status, "Created At": result.created_at,
        } for index, bullet in enumerate(result.summary_bullets, start=1)]
        table = pyarrow.Table.from_pylist(rows)
        path.parent.mkdir(parents=True, exist_ok=True)
        parquet.write_table(table, path, compression=compression)
        return True
    except Exception:
        return False


def def_export_result(result: SummaryResult, output_dir: str | pathlib.Path, formats: Sequence[str]) -> dict[str, str]:
    root = pathlib.Path(output_dir).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    base = root / f"{def_safe_stem(result.source_name)}_{result.run_id}"
    outputs: dict[str, str] = {}
    if "json" in formats:
        path = base.with_suffix(".json")
        def_atomic_write_text(path, def_json_dumps(result.to_dict(include_text=True)) + "\n")
        outputs["json"] = str(path)
    if "md" in formats:
        path = base.with_suffix(".md")
        def_atomic_write_text(path, def_markdown(result))
        outputs["md"] = str(path)
    if "csv" in formats:
        path = base.with_suffix(".csv")
        def_export_csv(result, path)
        outputs["csv"] = str(path)
    if "parquet" in formats:
        path = base.with_suffix(".parquet")
        if def_export_parquet(result, path):
            outputs["parquet"] = str(path)
        else:
            outputs["parquet"] = "SKIPPED:pyarrow_unavailable_or_write_failed"
    return outputs


# =============================================================================
# def 13 RAM ESTIMATION AND SELF-TEST
# =============================================================================

def def_estimate_ram(model_gb: float, context_tokens: int, parameter_billions: float = 3.0, kv_bits: int = 16, overhead_mb: int = 500) -> dict[str, float]:
    # Conservative heuristic; exact KV depends on architecture/layers/hidden size.
    kv_mb = context_tokens * max(1.0, parameter_billions / 3.0) * (kv_bits / 16.0) * 0.075
    total_gb = model_gb + (kv_mb + overhead_mb) / 1024
    recommended_gb = total_gb * 1.30
    return {
        "model_gb": round(model_gb, 3),
        "context_tokens": float(context_tokens),
        "estimated_kv_cache_mb": round(kv_mb, 1),
        "runtime_overhead_mb": float(overhead_mb),
        "estimated_total_gb": round(total_gb, 3),
        "recommended_physical_ram_gb_1_3x": round(recommended_gb, 3),
        "note": "Heuristic only; verify with the exact GGUF architecture and runtime telemetry.",
    }


def def_self_test() -> dict[str, Any]:
    test_text = (
        "台積電（2330.TW）於2026年8月18日公布測試資料，營收成長12.5%。"
        "The local CPU pipeline preserves the original evidence and does not call cloud services. "
        "主要風險是來源欄位缺失，可能影響結論。"
        "下一步需要確認財報日期與調整後價格，並由兩種關鍵詞抽取器交叉驗證。"
        "系统也必须保留简体中文别名，不可覆盖原文。"
    )
    with tempfile.TemporaryDirectory(prefix="via_summarizer_selftest_") as directory:
        config = EngineConfig(
            db_path=str(pathlib.Path(directory) / "test.sqlite"),
            output_dir=str(pathlib.Path(directory) / "output"),
            temp_root=str(pathlib.Path(directory) / "temp"),
            language="mixed",
            use_llm=False,
            resume=True,
            min_free_disk_mb=1,
            min_free_memory_mb=1,
        )
        with VIASummarizerEngine(config) as engine:
            eml_text, eml_adapter = def_extract_eml_text(
                b"Subject: VIA Test\r\nContent-Type: text/plain; charset=utf-8\r\n\r\nLocal summary body."
            )
            first = engine.def_summarize_text(test_text, "self_test.txt", {"test": True})
            second = engine.def_summarize_text(test_text, "self_test.txt", {"test": True})
            exported = def_export_result(first, config.output_dir, ("json", "md", "csv", "parquet"))
            candidate_count = engine.store.connection.execute("SELECT COUNT(*) FROM term_candidates").fetchone()[0]
            metric_count = engine.store.connection.execute("SELECT COUNT(*) FROM term_metrics").fetchone()[0]
            run_count = engine.store.connection.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
            reviewed_term = first.keywords[0].canonical_term
            review_event = engine.store.def_review_term(reviewed_term, "APPROVED", "SELF_TEST_EXPLICIT_REVIEW")
            registry_result = engine.def_summarize_text(
                f"{reviewed_term} 已納入核准字庫。下一步需要確認詞義與來源。",
                "registry_test.txt",
                {"test": True},
            )
            blacklist_event = engine.store.def_review_term(reviewed_term, "BLACKLISTED", "SELF_TEST_EXPLICIT_BLACKLIST")
            blacklist_result = engine.def_summarize_text(
                f"{reviewed_term} 再次出現，但已列入停用字庫。",
                "blacklist_test.txt",
                {"test": True},
            )
            checks = {
                "exactly_four_bullets": len(first.summary_bullets) == 4,
                "roles_in_order": [item.role for item in first.summary_bullets] == [item[0] for item in SUMMARY_ROLES],
                "numeric_evidence": all(
                    not def_extract_number_tokens(item.detail)
                    or bool(item.evidence_sentence_ids)
                    for item in first.summary_bullets
                ),
                "keywords_present": bool(first.keywords),
                "raw_preserved": first.raw_text == test_text,
                "normalized_preserved_separately": bool(first.normalized_text),
                "language_contract_present": bool(first.source_language and first.requested_language and first.language),
                "resume_normalized_preserved": second.normalized_text == first.normalized_text,
                "resume_same_run": second.run_id == first.run_id,
                "resume_does_not_duplicate_run": run_count == 1,
                "candidate_vocabulary_written": candidate_count == len(first.keywords),
                "term_metrics_written": metric_count == len(first.keywords),
                "explicit_vocabulary_review": review_event["decision"] == "APPROVED",
                "approved_registry_match": any(
                    item.canonical_term == reviewed_term and item.status == "APPROVED"
                    for item in registry_result.keywords
                ),
                "explicit_blacklist_review": blacklist_event["decision"] == "BLACKLISTED",
                "blacklist_filter": all(
                    item.canonical_term != reviewed_term for item in blacklist_result.keywords
                ),
                "eml_stdlib_reader": "VIA Test" in eml_text and "Local summary body" in eml_text and eml_adapter == "stdlib-email",
                "json_export": pathlib.Path(exported["json"]).is_file(),
                "markdown_export": pathlib.Path(exported["md"]).is_file(),
                "csv_export": pathlib.Path(exported["csv"]).is_file(),
                "sqlite_created": pathlib.Path(config.db_path).is_file(),
            }
            return {
                "engine": ENGINE_NAME,
                "version": ENGINE_VERSION,
                "status": "PASS" if all(checks.values()) else "FAIL",
                "checks": checks,
                "capabilities_used": first.capabilities_used,
                "warnings": first.warnings,
                "available_libraries": sum(1 for item in def_capability_report() if item["available"]),
                "total_libraries_registered": len(LIBRARY_PORTFOLIO),
            }


# =============================================================================
# def 14 CLI
# =============================================================================

def def_build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="VIA CPU-first multilingual four-bullet summarizer")
    parser.add_argument("--version", action="version", version=f"%(prog)s {ENGINE_VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    summarize = subparsers.add_parser("summarize", help="Summarize one file or direct text")
    source = summarize.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", help="Local input file")
    source.add_argument("--text", help="Direct text")
    summarize.add_argument("--source-name", default="direct_text")
    def_add_common_arguments(summarize)

    batch = subparsers.add_parser("batch", help="Summarize a local directory with checkpoints")
    batch.add_argument("--input-dir", required=True)
    batch.add_argument("--glob", default=DEFAULT_INPUT_GLOB)
    def_add_common_arguments(batch)

    capability = subparsers.add_parser("capabilities", help="Show optional local library availability")
    capability.add_argument("--available-only", action="store_true")

    estimate = subparsers.add_parser("estimate-ram", help="Estimate local GGUF runtime RAM")
    estimate.add_argument("--model-gb", type=float, required=True)
    estimate.add_argument("--context", type=int, default=DEFAULT_LLM_CONTEXT)
    estimate.add_argument("--parameters-b", type=float, default=3.0)
    estimate.add_argument("--kv-bits", type=int, default=16)

    vocabulary = subparsers.add_parser("vocabulary", help="Review the governed candidate keyword library")
    vocabulary.add_argument("--db", default=DEFAULT_DB_PATH)
    action = vocabulary.add_mutually_exclusive_group(required=True)
    action.add_argument("--list", action="store_true", dest="list_terms", help="List candidate and registry status")
    action.add_argument("--approve", metavar="TERM", help="Append an APPROVED registry event")
    action.add_argument("--reject", metavar="TERM", help="Append a REJECTED registry event")
    action.add_argument("--blacklist", metavar="TERM", help="Append a BLACKLISTED registry event")
    vocabulary.add_argument("--reason", default="EXPLICIT_USER_REVIEW")
    vocabulary.add_argument("--limit", type=int, default=100)

    subparsers.add_parser("self-test", help="Run offline unit/integration/regression checks")
    return parser


def def_add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--db", default=DEFAULT_DB_PATH)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--temp-root", default=DEFAULT_TEMP_ROOT)
    parser.add_argument("--language", choices=SUPPORTED_LANGUAGES, default=DEFAULT_LANGUAGE)
    parser.add_argument("--formats", default=",".join(DEFAULT_OUTPUT_FORMATS), help="json,md,csv,parquet")
    parser.add_argument("--cpu-threads", type=int, default=CPU_THREADS)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--use-llm", action="store_true")
    parser.add_argument(
        "--llm-backend",
        choices=("auto", "ollama", "llama_cpp", "transformers", "onnx", "ctranslate2", "ctransformers"),
        default=DEFAULT_LLM_BACKEND,
    )
    parser.add_argument("--llm-model-path", default=DEFAULT_LLM_MODEL_PATH)
    parser.add_argument("--ollama-model", default=DEFAULT_OLLAMA_MODEL)
    parser.add_argument("--ollama-url", default=DEFAULT_OLLAMA_URL)
    parser.add_argument("--embedding-model-path", default=DEFAULT_EMBEDDING_MODEL_PATH)
    parser.add_argument("--fasttext-model-path", default=DEFAULT_FASTTEXT_MODEL_PATH)
    parser.add_argument("--auto-promote", action="store_true", help="Explicitly allow eligible candidate terms into approved registry")
    parser.add_argument("--keep-temp", action="store_true")


def def_config_from_args(args: argparse.Namespace) -> EngineConfig:
    formats = tuple(item.strip().lower() for item in args.formats.split(",") if item.strip())
    invalid = set(formats) - {"json", "md", "csv", "parquet"}
    if invalid:
        raise ValueError(f"UNSUPPORTED_OUTPUT_FORMATS:{','.join(sorted(invalid))}")
    return EngineConfig(
        db_path=args.db, output_dir=args.output_dir, temp_root=args.temp_root, language=args.language,
        output_formats=formats, cpu_threads=max(1, args.cpu_threads), batch_size=max(1, args.batch_size),
        resume=not args.no_resume, use_llm=args.use_llm, llm_backend=args.llm_backend,
        llm_model_path=args.llm_model_path, ollama_model=args.ollama_model, ollama_url=args.ollama_url,
        embedding_model_path=args.embedding_model_path, fasttext_model_path=args.fasttext_model_path,
        auto_promote=args.auto_promote, keep_temp=args.keep_temp,
    )


def def_main(argv: Optional[Sequence[str]] = None) -> int:
    parser = def_build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "capabilities":
            rows = def_capability_report()
            if args.available_only:
                rows = [row for row in rows if row["available"]]
            print(def_json_dumps({"engine": ENGINE_NAME, "version": ENGINE_VERSION, "libraries": rows}))
            return 0
        if args.command == "estimate-ram":
            print(def_json_dumps(def_estimate_ram(args.model_gb, args.context, args.parameters_b, args.kv_bits)))
            return 0
        if args.command == "vocabulary":
            with SSOTStore(args.db) as store:
                if args.list_terms:
                    print(def_json_dumps({"status": "PASS", "terms": store.def_list_vocabulary_candidates(args.limit)}))
                    return 0
                if args.approve:
                    result = store.def_review_term(args.approve, "APPROVED", args.reason)
                elif args.reject:
                    result = store.def_review_term(args.reject, "REJECTED", args.reason)
                else:
                    result = store.def_review_term(args.blacklist, "BLACKLISTED", args.reason)
                print(def_json_dumps({"status": "PASS", "review": result}))
                return 0
        if args.command == "self-test":
            result = def_self_test()
            print(def_json_dumps(result))
            return 0 if result["status"] == "PASS" else 2
        config = def_config_from_args(args)
        with VIASummarizerEngine(config) as engine:
            if args.command == "summarize":
                result = engine.def_summarize_file(args.input) if args.input else engine.def_summarize_text(args.text, args.source_name)
                outputs = def_export_result(result, config.output_dir, config.output_formats)
                print(def_json_dumps({
                    "status": result.status, "run_id": result.run_id,
                    "summary_bullets": [dataclasses.asdict(item) for item in result.summary_bullets],
                    "keywords": [dataclasses.asdict(item) for item in result.keywords],
                    "outputs": outputs, "warnings": result.warnings,
                }))
                return 0
            if args.command == "batch":
                results = engine.def_batch(args.input_dir, args.glob)
                outputs = [def_export_result(result, config.output_dir, config.output_formats) for result in results]
                print(def_json_dumps({"status": "PASS", "documents": len(results), "outputs": outputs}))
                return 0
        parser.error("Unknown command")
        return 2
    except KeyboardInterrupt:
        LOGGER.warning("Interrupted · checkpoints already committed are preserved")
        return 130
    except Exception as exc:
        LOGGER.error("%s: %s", type(exc).__name__, exc)
        if os.environ.get("VIA_DEBUG") == "1":
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(def_main())
