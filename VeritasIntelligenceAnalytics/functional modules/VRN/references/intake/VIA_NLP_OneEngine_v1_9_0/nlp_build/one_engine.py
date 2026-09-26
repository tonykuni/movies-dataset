#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA NLP OneEngine 1.9.0 — local, evidence-preserving integration.

All user settings are in DEFAULTS. Optional model files are never downloaded.
The embedded, hash-verified v1.8.0 source remains available via `legacy`.
Original documents are never overwritten. New functions are complete def units.
"""
from __future__ import annotations

# ==================== 01 / PARAMETERS AND REGISTRY ====================
VERSION = "1.9.0"
DEFAULTS = {
    "encoding": "utf-8-sig", "max_chars": 1_000_000,
    "max_record_bytes": 8_000_000, "chunk_chars": 800, "overlap_chars": 80,
    "unwrap": False, "unwrap_min_line": 28, "spacing": False,
    "quotes": True, "redact": False, "s2twp": False,
    "punc_model": "", "sat_model": "", "ckip_model": "", "spell_model": "",
    "model_min_available_mb": 3072,
    "tokenizer": "rules", "workers": 2, "batch_size": 16,
    "text_key": "text", "csv_cols": ["text", "content", "title"],
    "threshold": 0.88, "ngram": 3, "num_perm": 64, "bands": 16,
    "seed": 20260927, "min_near_chars": 40, "candidate_limit": 1000,
    "keep": "first", "near_action": "review", "sqlite_cache_kib": 8192, "progress_every": 100,
}
PROVIDERS = {
    "funasr": ("funasr", "Chinese/English punctuation; local ct-punc required"),
    "wtpsplit_lite": ("wtpsplit-lite", "SaT sentence boundaries; local ONNX model required"),
    "ckip_transformers": ("ckip-transformers", "Traditional Chinese word segmentation; local WS model required"),
    "opencc": ("opencc-python-reimplemented", "s2twp projection; never rewrites original"),
    "jieba": ("jieba", "optional word segmentation"),
    "pycorrector": ("pycorrector", "MacBERT correction suggestions only; local checkpoint required"),
    "datasketch": ("datasketch", "legacy candidate discovery; integrated disk index uses deterministic stdlib MinHash"),
}
ABBREVIATIONS = r"(?:Mr|Mrs|Ms|Dr|Prof|Sr|Jr|vs|etc|Fig|Vol|No|St|Ave|Co|Inc|Ltd|Corp)\."
TW_ID_CODES = dict(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ", (10,11,12,13,14,15,16,17,34,18,19,20,21,22,35,23,24,25,26,27,28,29,32,30,31,33)))
SOURCES = {
    "legacy": "VIA_NLP_Application_System_v1.8.0.zip / 2026-09-08",
    "markdown": "MarkdownEditingEngine_v1.4.0_FINAL.zip / 2026-09-12",
    "brief": "貼上的文字 (1).txt / 2026-09-27 Asia/Taipei",
}
PAYLOAD_SHA256 = "__PAYLOAD_SHA256__"
PAYLOAD_B85 = """__PAYLOAD_B85__"""

import argparse
import ast
import base64
import concurrent.futures
import contextlib
import csv
import datetime as dt
import hashlib
import html
import importlib
import importlib.metadata
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import unicodedata
import uuid
import zipfile

_MODEL_CACHE = {}
_MODEL_LOCK = threading.RLock()
_FULLWIDTH = str.maketrans({chr(i): chr(i-0xFEE0) for i in list(range(0xFF10,0xFF1A))+list(range(0xFF21,0xFF3B))+list(range(0xFF41,0xFF5B))})
_CJK = re.compile(r"[\u3400-\u9fff\U00020000-\U0002EBEF]")
_NUMBER = re.compile(r"[+\-−]?[0-9０-９]+(?:[,，.．。:/：／\-−][0-9０-９]+)*(?:[%％]|[eE][+\-]?[0-9]+)?")
_TOKEN = re.compile(
    r"`+[^`\n]*`+|!?\[[^\]\n]*\]\([^\n]*?\)|<[^>\n]+>|"
    r"(?:https?://|www\.)[^\s<>\u3000-\u303f\uff00-\uffef]+|"
    r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}|"
    r"[A-Za-z]:[\\/][^\s<>]+|"
    r"(?<![A-Za-z0-9])(?:[1-9]\d{3}|00\d{3}[ABD]|009[A-Z]\d{2})(?:\.(?:TW|TWO)|\s+TT)(?![A-Za-z0-9])|"
    r"(?i:\b(?:e\.g\.|i\.e\.|U\.S\.|U\.K\.|"+ABBREVIATIONS+r"))|"
    r"[+\-−]?[0-9０-９]+(?:[,，.．。:/：／\-−][0-9０-９]+)*(?:[%％]|[eE][+\-]?[0-9]+)?"
)


def def_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def def_sha(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode("utf-8")).hexdigest()


def def_config(overrides=None):
    cfg = json.loads(def_json(DEFAULTS))
    if overrides:
        unknown = set(overrides)-set(cfg)
        if unknown:
            raise ValueError("Unknown settings: " + ", ".join(sorted(unknown)))
        cfg.update(overrides)
    if not 0 <= cfg["overlap_chars"] < cfg["chunk_chars"]:
        raise ValueError("Require 0 <= overlap_chars < chunk_chars")
    for key in ("max_chars", "max_record_bytes", "workers", "batch_size", "num_perm", "bands", "ngram", "candidate_limit", "progress_every"):
        if not isinstance(cfg[key], int) or cfg[key] < 1:
            raise ValueError(key + " must be a positive integer")
    if cfg["num_perm"] % cfg["bands"] or not 0 < cfg["threshold"] <= 1:
        raise ValueError("Invalid MinHash bands or threshold")
    if cfg["keep"] not in ("first", "longest") or cfg["tokenizer"] not in ("rules", "jieba"):
        raise ValueError("Invalid keep or tokenizer")
    if cfg["near_action"] not in ("review", "project"):
        raise ValueError("near_action must be review or project")
    return cfg


def def_atomic_write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = data if isinstance(data, bytes) else data.encode("utf-8")
    fd, name = tempfile.mkstemp(prefix=path.name+".", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


@contextlib.contextmanager
def def_writer_lock(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "writer.lock").open("a+b") as lock:
        lock.seek(0, 2)
        if not lock.tell():
            lock.write(b"0")
            lock.flush()
        lock.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise RuntimeError("Another VIA NLP writer is using this output directory") from exc
        try:
            yield
        finally:
            lock.seek(0)
            if os.name == "nt":
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def def_database(path, cfg):
    con = sqlite3.connect(str(path), timeout=30)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=FULL")
    con.execute("PRAGMA temp_store=FILE")
    con.execute("PRAGMA cache_size=-%d" % cfg["sqlite_cache_kib"])
    return con


def def_runtime(directory):
    """Materialize only the bundled source; verify every byte before import."""
    raw = base64.b85decode("".join(PAYLOAD_B85.split()).encode("ascii"))
    if def_sha(raw) != PAYLOAD_SHA256:
        raise RuntimeError("Embedded payload hash mismatch")
    root = Path(directory).resolve() / ("runtime_" + PAYLOAD_SHA256[:16])
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        for item in archive.infolist():
            dest = (root / item.filename).resolve()
            if not dest.is_relative_to(root) or item.is_dir():
                if item.is_dir():
                    continue
                raise RuntimeError("Invalid payload path")
            content = archive.read(item.filename)
            if dest.exists():
                if def_sha(dest.read_bytes()) != def_sha(content):
                    raise RuntimeError("Changed embedded runtime: " + str(dest))
            else:
                def_atomic_write(dest, content)
    return root


def def_legacy(argv, directory):
    root = def_runtime(directory) / "legacy"
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root / "src")
    return subprocess.run([sys.executable, "-m", "via_nlp_engine", *argv], cwd=root, env=env, check=False).returncode


def def_legacy_analysis(text, directory, task="analyze"):
    """One facade: call the preserved v1.8 pipeline against source evidence."""
    root = def_runtime(directory) / "legacy"
    src = str(root / "src")
    if "via_nlp_engine" in sys.modules:
        existing = Path(sys.modules["via_nlp_engine"].__file__).resolve()
        if not existing.is_relative_to(root):
            raise RuntimeError("Another via_nlp_engine is already loaded; use a clean process")
    if src not in sys.path:
        sys.path.insert(0,src)
    from via_nlp_engine import ProcessRequest, VIAEngine
    engine = VIAEngine(root/"config"/"default.json",overrides={
        "engine":{"offline":True}, "jobs":{"enabled":False},
        "ml":{"enabled":False},
        "routing":{"allow_tiers":[1,2],"allow_deep_models":False,"allow_llm":False},
        "translation":{"enabled":False}
    },auto_start=False)
    effective = engine.config
    if (not effective["engine"]["offline"] or effective["routing"]["allow_deep_models"] or
        effective["routing"]["allow_llm"] or effective["translation"]["enabled"]):
        engine.close()
        raise ValueError("Inherited VIA_NLP settings conflict with the integrated offline analysis profile")
    with engine:
        return engine.process(ProcessRequest(text=text,task=task,quality="fast")).to_dict()


def def_markdown_analysis(text, directory):
    root = def_runtime(directory)
    path = root / "markdown" / "semantic_reconstruction.py"
    name = "via_nlp_bundled_markdown_140"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name].def_analyze_markdown_text(text)


# ==================== 02 / STRUCTURE AND FINANCIAL FACT PROTECTION ====================
def def_structural_ranges(text):
    ranges, offset, fence, start, front = [], 0, None, 0, False
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines):
        stripped = line.strip()
        if i == 0 and stripped in ("---", "+++"):
            front, fence, start = True, stripped, offset
        elif front:
            if stripped in (fence, "..."):
                ranges.append((start, offset+len(line), "frontmatter"))
                front, fence = False, None
        elif fence:
            if re.fullmatch(r"[ \t]*"+re.escape(fence[0])+"{"+str(len(fence))+r",}[ \t]*\r?\n?", line):
                ranges.append((start, offset+len(line), "code"))
                fence = None
        else:
            found = re.match(r"^[ \t]*(`{3,}|~{3,})", line)
            if found:
                fence, start = found[1], offset
            elif (stripped.startswith(("|", "<", "<!--")) or "|" in line or
                  re.match(r"^(?:\s{4}|\t)\S", line) or
                  re.match(r"^(?:def |class |from \w.* import |import \w|if __name__|[A-Za-z_]\w*\s*=|(?:print|text|image)\()",line) or
                  ("|" in line and i+1 < len(lines) and re.match(r"^[\s|:\-]+$", lines[i+1]))):
                ranges.append((offset, offset+len(line), "structure"))
        offset += len(line)
    if fence:
        ranges.append((start, len(text), "unclosed_structure"))
    for match in re.finditer(r"<(script|style|pre|code|table|div|section|article)\b[^>]*>(?:[\s\S]*?</\1\s*>|[\s\S]*\Z)",text,re.I):
        ranges.append((match.start(),match.end(),"html_block"))
    ranges.sort()
    merged = []
    for a,b,kind in ranges:
        if merged and a < merged[-1][1]:
            merged[-1] = (merged[-1][0],max(b,merged[-1][1]),merged[-1][2])
        else:
            merged.append((a,b,kind))
    return merged


def def_mask(text):
    """Private Unicode sentinels do not resemble words or financial values."""
    ranges = def_structural_ranges(text)
    ranges += [(m.start(), m.end(), "token") for m in _TOKEN.finditer(text)]
    ranges.sort(key=lambda x:(x[0], -(x[1]-x[0])))
    merged = []
    for a, b, kind in ranges:
        if merged and a < merged[-1][1]:
            if b > merged[-1][1]:
                merged[-1] = (merged[-1][0], b, merged[-1][2])
        else:
            merged.append((a,b,kind))
    protected, pieces, cursor = {}, [], 0
    for i, (a,b,kind) in enumerate(merged):
        token = "\ue000" + chr(0xF0000+i) + "\ue001"
        if token in text:
            raise ValueError("Input collides with protection sentinel")
        protected[token] = text[a:b]
        pieces.extend((text[cursor:a], token))
        cursor = b
    pieces.append(text[cursor:])
    return "".join(pieces), protected


def def_unmask(text, protected):
    for token, original in protected.items():
        if text.count(token) != 1:
            raise ValueError("Protected span changed, omitted or duplicated")
        text = text.replace(token, original)
    return text


def def_facts(text):
    return [m[0].translate(_FULLWIDTH) for m in _NUMBER.finditer(text)]


def def_clean_controls(text):
    # Preserve emoji ZWJ, variation selectors, and user-defined private glyphs.
    return "".join(ch for ch in text if ch in "\n\r\t\u200c\u200d" or
                   (unicodedata.category(ch) not in ("Cc", "Cs") and
                    ch not in "\ufeff\u200b\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069"))


def def_quotes(text):
    stack, replacements = [], {}
    opener = {"“": "”", "‘": "’", '"': '"', "'": "'"}
    for i, ch in enumerate(text):
        before = text[i-1] if i else ""
        after = text[i+1] if i+1 < len(text) else ""
        if ch in "'’" and re.fullmatch(r"[A-Za-z]", before) and re.fullmatch(r"[A-Za-z]", after):
            continue
        if ch in "\"'" and before.isdigit():
            continue
        if stack and ch == stack[-1][1]:
            a, _, depth = stack.pop()
            if _CJK.search(text[a+1:i]):
                replacements[a] = "「" if depth % 2 == 0 else "『"
                replacements[i] = "」" if depth % 2 == 0 else "』"
        elif ch in opener:
            stack.append((i, opener[ch], len(stack)))
    return "".join(replacements.get(i,ch) for i,ch in enumerate(text)), bool(stack)


def def_unwrap(text, cfg):
    lines = text.splitlines(keepends=True)
    out = []
    for line in lines:
        if out and out[-1].endswith(("\n", "\r")):
            a, b = out[-1].rstrip("\r\n"), line.lstrip(" \t")
            structural = re.compile(r"^(?:\s*$|[#>|*+\-]|\d+[.)、]|[一二三四五六七八九十]+[、．.])")
            if (len(a.strip()) >= cfg["unwrap_min_line"] and len(b.strip()) >= cfg["unwrap_min_line"]
                and not structural.match(a) and not structural.match(b)
                and not re.search(r"[。！？!?;；:：.\-]\s*$", a)
                and "\ue000" not in a+b):
                if _CJK.search(a[-1:]) and _CJK.match(b):
                    out[-1] = a+b
                    continue
                if re.search(r"[A-Za-z,]$", a) and re.match(r"[a-z]", b):
                    out[-1] = a+" "+b
                    continue
        out.append(line)
    return "".join(out)


def def_normalize(text, cfg):
    masked, protected = def_mask(text)
    masked = def_clean_controls(masked).translate(_FULLWIDTH).replace("\u00a0", " ")
    reviews = []
    if cfg["unwrap"]:
        masked = def_unwrap(masked, cfg)
    if cfg["quotes"]:
        masked, unmatched = def_quotes(masked)
        if unmatched:
            reviews.append("UNBALANCED_QUOTES_PRESERVED")
    for half, full in ((",","，"),(";","；"),("?","？"),("!","！"),(":","：")):
        masked = re.sub(r"(?<=[\u3400-\u9fff])[ \t]*"+re.escape(half)+r"[ \t]*",full,masked)
        masked = re.sub(r"[ \t]*"+re.escape(half)+r"[ \t]*(?=[\u3400-\u9fff])",full,masked)
    masked = re.sub(r"(?<=[\u3400-\u9fff])\.(?!\.)", "。", masked)
    masked = re.sub(r"[ \t]*([，。！？；：])[ \t]*", r"\1", masked)
    if cfg["spacing"]:
        masked = re.sub(r"([\u3400-\u9fff])([A-Za-z0-9])", r"\1 \2", masked)
        masked = re.sub(r"([A-Za-z0-9])([\u3400-\u9fff])", r"\1 \2", masked)
    value = def_unmask(masked, protected)
    if re.search(r"[0-9０-９][。．，：][0-9０-９]", text):
        reviews.append("AMBIGUOUS_NUMERIC_PUNCTUATION_PRESERVED")
    if def_facts(value) != def_facts(text):
        reviews.append("FACT_GATE_ROLLBACK")
        value = text
    return value, reviews


# ==================== 03 / LOCAL MODELS; NO IMPLICIT DOWNLOAD ====================
def def_health():
    rows = []
    for module, (distribution, purpose) in PROVIDERS.items():
        try:
            available = importlib.util.find_spec(module) is not None
            version = importlib.metadata.version(distribution) if available else ""
        except (ImportError, ValueError, importlib.metadata.PackageNotFoundError):
            available, version = False, ""
        rows.append({"provider":module,"installed":available,"version":version,
                     "inference_tested":False,"purpose":purpose,
                     "status":"INSTALLED_NOT_VALIDATED" if available else "MISSING_OPTIONAL"})
    return {"engine":VERSION,"core":"STDLIB","providers":rows,"models_auto_download":False,
            "legacy_version":"1.8.0","sources":SOURCES}


def def_local_model(kind, path):
    local = Path(path).expanduser().resolve()
    if not local.is_dir():
        raise FileNotFoundError("A complete local model directory is required: "+str(local))
    key = (kind, str(local))
    with _MODEL_LOCK:
        if key not in _MODEL_CACHE:
            os.environ["HF_HUB_OFFLINE"] = "1"
            os.environ["TRANSFORMERS_OFFLINE"] = "1"
            if kind == "punc":
                from funasr import AutoModel
                model = AutoModel(model=str(local), device="cpu", disable_update=True,
                                  trust_remote_code=False)
            elif kind == "sat":
                from wtpsplit_lite import SaT
                model = SaT(str(local))
            elif kind == "ckip":
                from ckip_transformers.nlp import CkipWordSegmenter
                model = CkipWordSegmenter(model_name=str(local), tokenizer_name=str(local), device=-1)
            elif kind == "spell":
                from pycorrector import MacBertCorrector
                model = MacBertCorrector(str(local))
            else:
                raise ValueError("Unsupported model kind")
            _MODEL_CACHE[key] = model
    return _MODEL_CACHE[key]


def def_model_memory_gate(cfg):
    try:
        import psutil
        available = psutil.virtual_memory().available / (1024*1024)
    except ImportError:
        if hasattr(os,"sysconf") and "SC_AVPHYS_PAGES" in os.sysconf_names:
            available = os.sysconf("SC_AVPHYS_PAGES")*os.sysconf("SC_PAGE_SIZE")/(1024*1024)
        else:
            raise RuntimeError("Install psutil to verify available model RAM on this platform")
    if available < cfg["model_min_available_mb"]:
        raise RuntimeError("Insufficient available RAM for optional model")


def def_predict_prose(model,text,cfg):
    """Use whole prose lines as context; validate protected tokens after inference."""
    ranges = def_structural_ranges(text)
    ranges.append((len(text),len(text),"end"))
    output, cursor, reviews = [], 0, []
    for a,b,_ in ranges:
        for line in text[cursor:a].splitlines(keepends=True):
            if not line.strip():
                output.append(line)
                continue
            if len(line) > cfg["chunk_chars"]:
                reviews.append("PUNC_LONG_BLOCK_REVIEW")
                output.append(line)
                continue
            content = line.strip()
            candidate = model.generate(input=content)[0]["text"]
            tokens = set(m[0] for m in _TOKEN.finditer(content))
            preserved = all(candidate.count(token)==content.count(token) for token in tokens)
            if (not preserved or def_content_signature(candidate)!=def_content_signature(content)
                or def_facts(candidate)!=def_facts(content)):
                reviews.append("PUNC_CONTENT_CHANGE_REJECTED")
                output.append(line)
            else:
                left = line[:len(line)-len(line.lstrip())]
                right = line[len(line.rstrip()):]
                output.append(left+candidate+right)
        output.append(text[a:b])
        cursor = b
    return "".join(output),reviews


def def_content_signature(text):
    return "".join(ch for ch in text if not ch.isspace() and not unicodedata.category(ch).startswith("P"))


def def_model_projection(text, cfg):
    reviews, usage, suggestions = [], [], []
    output = text
    if cfg["s2twp"]:
        try:
            from opencc import OpenCC
            masked, protected = def_mask(output)
            candidate = def_unmask(OpenCC("s2twp").convert(masked), protected)
            if def_facts(candidate) != def_facts(output):
                raise ValueError("OpenCC changed facts")
            output = candidate
            usage.append("opencc:s2twp")
        except Exception as exc:
            reviews.append("OPENCC_UNAVAILABLE:"+type(exc).__name__)
    if cfg["punc_model"]:
        try:
            def_model_memory_gate(cfg)
            model = def_local_model("punc", cfg["punc_model"])
            candidate,issues = def_predict_prose(model,output,cfg)
            reviews.extend(issues)
            if def_facts(candidate) != def_facts(output):
                raise ValueError("Punctuation model changed facts")
            output = candidate
            usage.append("funasr:local")
        except Exception as exc:
            reviews.append("PUNC_UNAVAILABLE:"+type(exc).__name__)
    if cfg["spell_model"]:
        try:
            def_model_memory_gate(cfg)
            model = def_local_model("spell", cfg["spell_model"])
            if len(output) <= cfg["chunk_chars"]:
                candidate = model.correct(output)
                suggestions.append({"type":"spell","candidate":candidate,"applied":False})
                usage.append("pycorrector:review_only")
            else:
                reviews.append("SPELL_LONG_BLOCK_REVIEW")
        except Exception as exc:
            reviews.append("SPELL_UNAVAILABLE:"+type(exc).__name__)
    return output, reviews, usage, suggestions


def def_valid_tw_id(value):
    if not re.fullmatch(r"[A-Z][12]\d{8}", value):
        return False
    code = TW_ID_CODES[value[0]]
    digits = [code//10, code%10] + [int(c) for c in value[1:]]
    return sum(a*b for a,b in zip(digits, (1,9,8,7,6,5,4,3,2,1,1))) % 10 == 0


def def_redact(text):
    text = re.sub(r"(?<![A-Za-z0-9])[A-Z][12]\d{8}(?![A-Za-z0-9])",
                  lambda m:"[TW_ID_REDACTED]" if def_valid_tw_id(m[0]) else m[0],text)
    text = re.sub(r"(?<!\d)(?:09\d{2}[ \-]?\d{3}[ \-]?\d{3}|\+886[ \-]?9\d{2}[ \-]?\d{3}[ \-]?\d{3})(?!\d)","[PHONE_REDACTED]",text)
    return re.sub(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}","[EMAIL_REDACTED]",text)


# ==================== 04 / SENTENCES, CHUNKS, TRACEABLE SINGLE-DOCUMENT API ====================
def def_sentence_spans(text):
    intervals = [(m.start(),m.end()) for m in _TOKEN.finditer(text)] + def_structural_ranges(text)
    intervals = sorted((x[0],x[1]) for x in intervals)
    spans, start, i, j = [], 0, 0, 0
    while i < len(text):
        while j < len(intervals) and intervals[j][1] <= i:
            j += 1
        if j < len(intervals) and intervals[j][0] <= i < intervals[j][1]:
            i = intervals[j][1]
            continue
        char = text[i]
        boundary = char in "。！？!?\n" or (char == "." and (i+1 == len(text) or text[i+1].isspace()))
        i += 1
        if boundary:
            while i < len(text) and text[i] in "」』”’\"')]}。！？!?":
                i += 1
            while i < len(text) and text[i] in " \t\r":
                i += 1
            spans.append((start,i))
            start = i
    if start < len(text):
        spans.append((start,len(text)))
    return [{"start":a,"end":b,"text":text[a:b]} for a,b in spans]


def def_chunks(text, cfg, sentences=None):
    if not text:
        return []
    sentences = sentences or def_sentence_spans(text)
    ends = [s["end"] for s in sentences]
    protected = def_structural_ranges(text) + [(m.start(),m.end(),"token") for m in _TOKEN.finditer(text)]
    chunks, start = [], 0
    while start < len(text):
        limit = min(start+cfg["chunk_chars"],len(text))
        eligible = [e for e in ends if start < e <= limit]
        end = max(eligible) if eligible else limit
        for a,b,_ in protected:
            if a < end < b:
                end = a if a > start else b
                break
        if end <= start:
            raise RuntimeError("Chunker failed to advance")
        chunks.append({"start":start,"end":end,"text":text[start:end],
                       "sha256":def_sha(text[start:end]),"coordinate_space":"processed_text",
                       "oversize_protected_span":end-start > cfg["chunk_chars"]})
        if end == len(text):
            break
        next_start = max(start+1, end-cfg["overlap_chars"])
        for a,b,_ in protected:
            if a < next_start < b:
                next_start = b
                break
        start = min(next_start,end)
    return chunks


def def_process(text, cfg=None, source=""):
    cfg = def_config(cfg)
    if not isinstance(text,str):
        raise TypeError("Input text must be a string")
    if len(text) > cfg["max_chars"]:
        raise ValueError("Document exceeds max_chars; no truncation was performed")
    value, reviews = def_normalize(text,cfg)
    value, model_reviews, usage, suggestions = def_model_projection(value,cfg)
    reviews.extend(model_reviews)
    facts_ok = def_facts(value) == def_facts(text)
    if not facts_ok:
        value = text
        reviews.append("FACT_GATE_ROLLBACK")
    if cfg["redact"]:
        value = def_redact(value)
        suggestions = []  # correction candidates may still contain original identifiers
    sentences = def_sentence_spans(value)
    if cfg["sat_model"]:
        try:
            def_model_memory_gate(cfg)
            model = def_local_model("sat",cfg["sat_model"])
            proposal = list(model.split(value))
            if "".join(proposal) != value:
                raise ValueError("SaT output does not preserve exact text")
            sentences, offset = [], 0
            for item in proposal:
                sentences.append({"start":offset,"end":offset+len(item),"text":item})
                offset += len(item)
            usage.append("wtpsplit_lite:local")
        except Exception as exc:
            reviews.append("SAT_UNAVAILABLE:"+type(exc).__name__)
    tokens = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?|\d+(?:\.\d+)?|[\u3400-\u9fff]",value)
    tokenizer_used = "unicode_rules_not_linguistic_ws"
    try:
        if cfg["ckip_model"]:
            def_model_memory_gate(cfg)
            tokens = list(def_local_model("ckip",cfg["ckip_model"])([value])[0])
            tokenizer_used = "ckip:local"
        elif cfg["tokenizer"] == "jieba":
            import jieba
            tokens = list(jieba.cut(value))
            tokenizer_used = "jieba"
    except Exception as exc:
        reviews.append("TOKENIZER_UNAVAILABLE:"+type(exc).__name__)
    result = {"schema":"VIA_NLP_ONEENGINE/1.9","version":VERSION,"source":source,
              "source_sha256":def_sha(text),"processed_sha256":def_sha(value),
              "processed_text":value,"sentences":sentences,"chunks":def_chunks(value,cfg,sentences),
              "tokens":tokens,"tokenizer":tokenizer_used,"providers_used":usage,
              "fact_gate_before_redaction":facts_ok,"privacy_projection":cfg["redact"],
              "status":"REVIEW" if reviews else "PASS","reviews":sorted(set(reviews)),
              "suggestions":suggestions,"source_mapping":"whole_document_sha256; offsets address processed_text"}
    if not cfg["redact"]:
        result["original_text"] = text
    return result


# ==================== 05 / BATCH, CHECKPOINTS, SINGLE WRITER ====================
def def_read_records(path, cfg):
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in (".jsonl", ".ndjson"):
        with path.open("rb") as stream:
            line_no = 0
            while True:
                raw = stream.readline(cfg["max_record_bytes"]+1)
                if not raw:
                    break
                line_no += 1
                if len(raw) > cfg["max_record_bytes"]:
                    raise ValueError("Oversized JSONL line "+str(line_no))
                if not raw.strip():
                    continue
                try:
                    row = json.loads(raw.decode(cfg["encoding"]))
                    value = row[cfg["text_key"]]
                    if not isinstance(row,dict) or not isinstance(value,str):
                        raise ValueError("JSONL text must be a string")
                    yield {"id":str(path.resolve())+":"+str(line_no),"text":value,"metadata":row}
                except (ValueError,KeyError,TypeError,UnicodeError) as exc:
                    yield {"id":str(path.resolve())+":"+str(line_no),"error":type(exc).__name__,"raw_sha256":def_sha(raw)}
    elif suffix in (".csv", ".tsv"):
        csv.field_size_limit(cfg["max_record_bytes"])
        with path.open("r",encoding=cfg["encoding"],newline="") as stream:
            reader = csv.DictReader(stream, delimiter="\t" if suffix == ".tsv" else ",")
            selected = [c for c in cfg["csv_cols"] if c in (reader.fieldnames or [])]
            if not selected:
                raise ValueError("No configured CSV text columns matched")
            for i,row in enumerate(reader,2):
                for col in selected:
                    if not isinstance(row[col],str):
                        yield {"id":str(path.resolve())+f":{i}:{col}","error":"MISSING_CSV_VALUE"}
                    else:
                        yield {"id":str(path.resolve())+f":{i}:{col}","text":row[col],"metadata":{"row":i,"column":col,"record":row}}
    elif suffix in (".txt", ".md", ".markdown"):
        if path.stat().st_size > cfg["max_record_bytes"]:
            raise ValueError("Text file exceeds max_record_bytes; use record-based JSONL")
        yield {"id":str(path.resolve()),"text":path.read_bytes().decode(cfg["encoding"]),"metadata":{}}
    else:
        raise ValueError("Unsupported extension for batch; use legacy ingest for PDF/DOCX")


def def_work_record(record, cfg):
    if "error" in record:
        return {"status":"ERROR","source":record["id"],"error":record["error"],"raw_sha256":record.get("raw_sha256","")}
    try:
        result = def_process(record["text"],cfg,record["id"])
        if not cfg["redact"]:
            result["metadata"] = record["metadata"]
        return result
    except Exception as exc:
        return {"status":"ERROR","source":record["id"],"error":type(exc).__name__+": "+str(exc)}


def def_run_dir(output):
    target = Path(output) / (dt.datetime.now(dt.timezone.utc).strftime("run_%Y%m%dT%H%M%S_")+uuid.uuid4().hex[:8])
    target.mkdir(parents=True)
    return target


def def_progress(done, total=None):
    label = str(done) if total is None else f"{done}/{total}"
    print("\rVIA NLP · 已處理 "+label, end="",file=sys.stderr,flush=True)


def def_batch(input_path, output, cfg):
    cfg = def_config(cfg)
    source, output = Path(input_path).resolve(), Path(output).resolve()
    if not source.exists():
        raise FileNotFoundError(source)
    if source == output or (source.is_dir() and output.is_relative_to(source)):
        raise ValueError("Output must be outside input directory")
    files = sorted(p for p in source.rglob("*") if p.is_file() and p.suffix.lower() in (".txt",".md",".markdown",".jsonl",".ndjson",".csv",".tsv")) if source.is_dir() else [source]
    if not files:
        raise ValueError("No supported input files")
    with def_writer_lock(output):
        con = def_database(output/"checkpoint.sqlite3",cfg)
        try:
            con.executescript("CREATE TABLE IF NOT EXISTS results(key TEXT PRIMARY KEY,payload TEXT NOT NULL); CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY,previous TEXT,digest TEXT,payload TEXT);")
            run = def_run_dir(output)
            counts = {"PASS":0,"REVIEW":0,"ERROR":0,"cached":0,"processed":0}
            cfg_hash = def_sha(def_json({"version":VERSION,"config":cfg}))
            workers = 1 if any(cfg[k] for k in ("punc_model","sat_model","ckip_model","spell_model")) else cfg["workers"]
            pending = []
            with (run/"records.jsonl").open("w",encoding="utf-8") as out, concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
                for path in files:
                    try:
                        for record in def_read_records(path,cfg):
                            pending.append(record)
                            if len(pending) >= cfg["batch_size"]:
                                def_flush_records(pending,cfg,cfg_hash,con,out,pool,counts)
                                pending = []
                    except (ValueError,UnicodeError,OSError,csv.Error) as exc:
                        pending.append({"id":str(path),"error":type(exc).__name__+": "+str(exc)})
                if pending:
                    def_flush_records(pending,cfg,cfg_hash,con,out,pool,counts)
                out.flush()
                os.fsync(out.fileno())
            print(file=sys.stderr)
            summary = {"version":VERSION,"kind":"batch","counts":counts,"input_files":len(files),"workers":workers,
                       "status":"ERROR" if counts["ERROR"] else "REVIEW" if counts["REVIEW"] else "PASS",
                       "output":str(run),"resume":"Record content + metadata + config hash; strict input rescan", "health":def_health()}
            def_atomic_write(run/"summary.json",def_json(summary))
            def_report(summary,run/"matrix.html")
            return summary
        finally:
            con.close()


def def_flush_records(records,cfg,cfg_hash,con,out,pool,counts):
    tasks = []
    for record in records:
        key = def_sha(cfg_hash+def_json(record))
        cached = con.execute("SELECT payload FROM results WHERE key=?",(key,)).fetchone()
        tasks.append((key,cached[0] if cached else None,None if cached else pool.submit(def_work_record,record,cfg)))
    for key,payload,future in tasks:
        if payload is not None:
            result = json.loads(payload)
            counts["cached"] += 1
        else:
            result = future.result()
            payload = def_json(result)
            with con:
                con.execute("INSERT OR IGNORE INTO results VALUES(?,?)",(key,payload))
                previous = con.execute("SELECT digest FROM events ORDER BY seq DESC LIMIT 1").fetchone()
                previous = previous[0] if previous else "0"*64
                event = def_json({"result_key":key,"status":result["status"]})
                con.execute("INSERT INTO events(previous,digest,payload) VALUES(?,?,?)",(previous,def_sha(previous+event),event))
        out.write(payload+"\n")
        counts[result["status"]] += 1
        counts["processed"] += 1
        def_progress(counts["processed"])


# ==================== 06 / DISK MINHASH + EXACT JACCARD; NO TRANSITIVE MERGE ====================
def def_shingles(text,cfg):
    normalized = " ".join(unicodedata.normalize("NFC",text).casefold().split())
    n = cfg["ngram"]
    return {normalized[i:i+n] for i in range(max(0,len(normalized)-n+1))} or ({normalized} if normalized else set())


def def_jaccard(left,right):
    return len(left & right)/len(left | right) if left or right else 1.0


def def_minhash_bands(shingles,cfg):
    if not shingles:
        return []
    # Deterministic keyed BLAKE2 per permutation, fixed byte order on all platforms.
    values = [s.encode("utf-8") for s in shingles]
    minima = []
    for i in range(cfg["num_perm"]):
        key = (str(cfg["seed"])+":"+str(i)).encode("ascii")
        minima.append(min(hashlib.blake2b(s,key=key,digest_size=8).digest() for s in values))
    rows = cfg["num_perm"]//cfg["bands"]
    return [def_sha(b"".join(minima[i:i+rows])) for i in range(0,len(minima),rows)]


def def_file_sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""):
            digest.update(block)
    return digest.hexdigest()


def def_dedup(input_path,output,cfg):
    cfg = def_config(cfg)
    source, output = Path(input_path).resolve(), Path(output).resolve()
    if not source.is_file():
        raise ValueError("dedup input must be one UTF-8 JSONL file")
    with def_writer_lock(output):
        before = source.stat()
        source_sha = def_file_sha(source)
        fingerprint = def_sha(VERSION+source_sha+def_json({k:cfg[k] for k in ("threshold","ngram","num_perm","bands","seed","min_near_chars","candidate_limit","keep","near_action","text_key","max_chars","max_record_bytes")}))
        con = def_database(output/("dedup_"+fingerprint[:20]+".sqlite3"),cfg)
        try:
            con.executescript("""
            CREATE TABLE IF NOT EXISTS docs(id INTEGER PRIMARY KEY,raw BLOB NOT NULL,text TEXT,
                sha TEXT,facts TEXT,length INTEGER,status TEXT,canonical INTEGER,similarity REAL,error TEXT);
            CREATE INDEX IF NOT EXISTS docs_sha ON docs(sha,status);
            CREATE TABLE IF NOT EXISTS bands(band INTEGER,hash TEXT,doc INTEGER,PRIMARY KEY(band,hash,doc));
            CREATE INDEX IF NOT EXISTS bands_lookup ON bands(band,hash);
            """)
            with source.open("rb") as stream:
                i = 0
                while True:
                    raw = stream.readline(cfg["max_record_bytes"]+1)
                    if not raw:
                        break
                    i += 1
                    if len(raw) > cfg["max_record_bytes"]:
                        raise ValueError(f"JSONL line {i} exceeds max_record_bytes; run stopped without dropping it")
                    if con.execute("SELECT 1 FROM docs WHERE id=?",(i,)).fetchone():
                        continue
                    try:
                        record = json.loads(raw.decode("utf-8-sig"))
                        value = record[cfg["text_key"]]
                        if not isinstance(value,str):
                            raise ValueError("text field is not a string")
                        if len(value) > cfg["max_chars"]:
                            raise ValueError("max_chars exceeded")
                        row = (i,raw,value,def_sha(value),def_json(def_facts(value)),len(value),"PENDING",None,None,None)
                    except (ValueError,KeyError,TypeError,UnicodeError) as exc:
                        row = (i,raw,None,None,None,0,"ERROR",None,None,type(exc).__name__+": "+str(exc))
                    with con:
                        con.execute("INSERT INTO docs VALUES(?,?,?,?,?,?,?,?,?,?)",row)
            if source.stat().st_mtime_ns != before.st_mtime_ns or source.stat().st_size != before.st_size:
                raise RuntimeError("Input changed during scan; retry against a stable snapshot")
            order = "length DESC,id" if cfg["keep"] == "longest" else "id"
            done = 0
            for doc_id,text,digest,facts,length in con.execute("SELECT id,text,sha,facts,length FROM docs WHERE status='PENDING' ORDER BY "+order):
                exact = con.execute("SELECT id,text FROM docs WHERE sha=? AND status IN ('KEEP','KEEP_REVIEW','NEAR_REVIEW') ORDER BY id",(digest,)).fetchall()
                duplicate = next((x[0] for x in exact if x[1]==text),None)
                is_exact = duplicate is not None
                similarity, status, error, bands = (1.0 if duplicate is not None else None),"KEEP",None,[]
                if duplicate is None and length >= cfg["min_near_chars"]:
                    shingles = def_shingles(text,cfg)
                    bands = def_minhash_bands(shingles,cfg)
                    terms, params = [], []
                    for band,h in enumerate(bands):
                        terms.append("(band=? AND hash=?)")
                        params.extend((band,h))
                    query = "SELECT DISTINCT doc FROM bands WHERE "+" OR ".join(terms)+" ORDER BY doc LIMIT ?"
                    candidates = con.execute(query,params+[cfg["candidate_limit"]+1]).fetchall() if terms else []
                    if len(candidates) > cfg["candidate_limit"]:
                        status, error = "KEEP_REVIEW","CANDIDATE_LIMIT_REACHED; recall incomplete"
                    for candidate_id, in candidates[:cfg["candidate_limit"]]:
                        old = con.execute("SELECT text,facts FROM docs WHERE id=?",(candidate_id,)).fetchone()
                        if old[1] != facts:
                            continue
                        score = def_jaccard(shingles,def_shingles(old[0],cfg))
                        if score >= cfg["threshold"]:
                            duplicate,similarity = candidate_id,score
                            break
                if duplicate is not None:
                    status = "DUPLICATE" if is_exact or cfg["near_action"] == "project" else "NEAR_REVIEW"
                with con:
                    con.execute("UPDATE docs SET status=?,canonical=?,similarity=?,error=? WHERE id=?",(status,duplicate,similarity,error,doc_id))
                    if status != "DUPLICATE":
                        con.executemany("INSERT OR IGNORE INTO bands VALUES(?,?,?)",[(n,h,doc_id) for n,h in enumerate(bands)])
                done += 1
                if done % cfg["progress_every"] == 0:
                    def_progress(done)
            run = def_run_dir(output)
            counts = dict(con.execute("SELECT status,count(*) FROM docs GROUP BY status").fetchall())
            with (run/"retained.jsonl").open("wb") as keep, (run/"duplicates.jsonl").open("wb") as dup, (run/"errors.jsonl").open("wb") as errors, (run/"duplicate_links.jsonl").open("w",encoding="utf-8") as links:
                for doc_id,raw,status,canonical,similarity,error in con.execute("SELECT id,raw,status,canonical,similarity,error FROM docs ORDER BY id"):
                    target = dup if status == "DUPLICATE" else errors if status == "ERROR" else keep
                    target.write(raw if raw.endswith(b"\n") else raw+b"\n")
                    if status in ("DUPLICATE","NEAR_REVIEW","KEEP_REVIEW","ERROR"):
                        links.write(def_json({"line":doc_id,"status":status,"canonical_line":canonical,"exact_jaccard":similarity,"error":error})+"\n")
            summary = {"version":VERSION,"kind":"dedup","status":"REVIEW" if counts.get("ERROR",0) or counts.get("KEEP_REVIEW",0) or counts.get("NEAR_REVIEW",0) else "PASS",
                       "counts":counts,"newly_indexed":done,"source_sha256":source_sha,"output":str(run),
                       "algorithm":"SQLite disk bands + deterministic 64-bit MinHash + exact original-shingle Jaccard; numerical facts equal",
                       "policy":"No original deletions; exact duplicates separated; near matches retained for review by default; no transitive union",
                       "near_action":cfg["near_action"],
                       "limitations":"LSH has probabilistic recall; no 50GB benchmark; disk grows with corpus; first pass stores input bytes",
                       "health":def_health()}
            def_atomic_write(run/"summary.json",def_json(summary))
            def_report(summary,run/"matrix.html")
            return summary
        finally:
            con.close()


# ==================== 07 / SMALL-TYPE WARM-WHITE MATRIX AND EXPORT ====================
def def_report(data,path):
    safe_json = def_json(data).replace("<","\\u003c").replace("&","\\u0026")
    rows = "".join("<tr><th>"+html.escape(str(k))+"</th><td>"+html.escape(str(v))+"</td></tr>" for k,v in data.get("counts",{}).items())
    providers = data.get("health",def_health()).get("providers",[])
    table = "".join("<tr><td>"+html.escape(p["provider"])+"</td><td>"+html.escape(p["status"])+"</td><td>"+html.escape(p["purpose"])+"</td></tr>" for p in providers)
    tests = "".join("<tr><td>"+html.escape(t["name"])+"</td><td>"+html.escape(t["status"])+"</td><td>"+html.escape(t.get("detail",""))+"</td></tr>" for t in data.get("tests",[]))
    page = """<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>VIA NLP OneEngine</title>
    <style>body{background:#faf8f3;color:#29332f;font:13px/1.6 system-ui;margin:0}main{max-width:1120px;margin:auto;padding:26px}header{border-bottom:2px solid #913d32;padding-bottom:16px}h1{font-size:22px;margin:6px 0}small{letter-spacing:.08em}button,select{font:inherit;padding:7px 12px;border:1px solid #cbc5ba;border-radius:5px;background:white;cursor:pointer}nav{float:right}section{background:white;border:1px solid #ded9cf;padding:16px;margin:16px 0;border-radius:8px}table{border-collapse:collapse;width:100%;text-align:left}td,th{border-bottom:1px solid #eee9e0;padding:7px;vertical-align:top}th{width:32%}.badge{padding:4px 10px;background:#ece5d4;border-radius:20px}.tab{display:none}.tab.active{display:block}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:12px/1.5 monospace}@media(max-width:620px){main{padding:12px}h1{font-size:18px}nav{float:none}td{overflow-wrap:anywhere}}</style>
    <main><nav><select id="format"><option value="json">JSON</option><option value="md">Markdown</option></select> <button onclick="saveReport()">匯出</button></nav><header><b>VERITAS INTELLIGENCE ANALYTICS</b><br><small>DISCIPLINA • PRUDENTIA • INTEGRITAS</small><br><b>AI-Powered Research &amp; Decision Intelligence Platform</b><h1>VIA NLP OneEngine · 1.9.0</h1><span class="badge">__STATUS__</span></header>
    <p><button onclick="showTab('overview')">處理矩陣</button> <button onclick="showTab('providers')">模型能力</button> <button onclick="showTab('evidence')">完整證據</button></p>
    <section id="overview" class="tab active"><table>__ROWS__</table><table>__TESTS__</table><p>來源原檔保留。REVIEW 表示需人工檢查；選配模型需在本機完成推論驗證。</p></section>
    <section id="providers" class="tab"><table><tr><th>Provider</th><th>狀態</th><th>用途</th></tr>__PROVIDERS__</table></section><section id="evidence" class="tab"><pre id="detail"></pre></section></main>
    <script id="data" type="application/json">__DATA__</script><script>
    const report=JSON.parse(document.getElementById('data').textContent);document.getElementById('detail').textContent=JSON.stringify(report,null,2);
    function showTab(id){document.querySelectorAll('.tab').forEach(e=>e.classList.toggle('active',e.id===id));}
    function saveReport(){const f=document.getElementById('format').value;const body=f==='json'?JSON.stringify(report,null,2):'# VIA NLP OneEngine\\n\\n```json\\n'+JSON.stringify(report,null,2)+'\\n```\\n';const u=URL.createObjectURL(new Blob([body],{type:'text/plain;charset=utf-8'}));const a=document.createElement('a');a.href=u;a.download='VIA_NLP_Report.'+f;a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);}
    </script></html>"""
    for token,value in (("__STATUS__",html.escape(data.get("status","UNKNOWN"))),("__ROWS__",rows),("__TESTS__",tests),("__PROVIDERS__",table),("__DATA__",safe_json)):
        page = page.replace(token,value)
    def_atomic_write(path,page)


# ==================== 08 / VALIDATION AND CLI ====================
def def_self_test(output):
    tests = []
    cfg = def_config()
    def check(name,condition,detail=""):
        tests.append({"name":name,"status":"PASS" if condition else "FAIL","detail":detail})
    original = '台積電2330.TW, EPS 12.50元,目標價1,250元! Dr. Smith said: don\'t change it.\n'
    result = def_process(original,cfg)
    check("facts_preserved",def_facts(result["processed_text"])==def_facts(original))
    check("cjk_punctuation",def_process("你好,世界!",cfg)["processed_text"]=="你好，世界！")
    code = '```python\nx = "你好,世界"\n```\n正文,正常!'
    check("code_fence_protected",def_process(code,cfg)["processed_text"].startswith(code.split("正文")[0]))
    incomplete = '```python\nx = "你好,世界"\n下一段,仍是程式'
    check("unclosed_fence_protected",def_process(incomplete,cfg)["processed_text"]==incomplete)
    table = '| 公司 | EPS |\n|---|---:|\n| 台積電 | 12.50 |\n'
    check("table_values_and_layout",def_process(table,cfg)["processed_text"]==table)
    url = "https://example.test/a?b=1&c=2"
    check("url_query_protected",url in def_process("網址:"+url,cfg)["processed_text"])
    check("apostrophe",def_process("don't change user's text",cfg)["processed_text"]=="don't change user's text")
    check("nested_quotes",def_process('他說:"這是\'測試\'資料"',cfg)["processed_text"]=='他說：「這是『測試』資料」')
    check("financial_decimal_review",def_process("EPS 3。14",cfg)["status"]=="REVIEW")
    check("emoji_zwj_preserved",def_process("👩‍💻",cfg)["processed_text"]=="👩‍💻")
    check("tw_checksum_valid",def_valid_tw_id("A123456789"))
    check("tw_checksum_invalid",not def_valid_tw_id("A123456788"))
    red = def_process("證號A123456789，手機0912-345-678，信箱a@example.test",{**cfg,"redact":True})
    check("pii_masked","A123456789" not in def_json(red) and "0912-345-678" not in def_json(red) and "a@example.test" not in def_json(red))
    check("privacy_original_omitted","original_text" not in red)
    split = def_sentence_spans("Dr. Smith measured 3.14. Next sentence。下一句！")
    check("abbreviation_decimal_boundaries",len(split)==3,str(len(split)))
    check("sentences_lossless","".join(s["text"] for s in split)=="Dr. Smith measured 3.14. Next sentence。下一句！")
    long = "無標點長句"*1000
    chunks = def_chunks(long,cfg)
    covered = set()
    for c in chunks:
        covered.update(range(c["start"],c["end"]))
    check("long_chunk_bound",all(len(c["text"])<=cfg["chunk_chars"] for c in chunks))
    check("chunk_coverage",len(covered)==len(long))
    check("empty_input",def_process("",cfg)["chunks"]==[])
    check("idempotence",def_process(result["processed_text"],cfg)["processed_text"]==result["processed_text"])
    check("short_heading_preserved",def_process("投資摘要\n這是一段重要內容",{**cfg,"unwrap":True})["processed_text"].startswith("投資摘要\n"))
    check("missing_model_honest",def_process("需要補標點的文字",{**cfg,"punc_model":"/missing-via-model"})["status"]=="REVIEW")
    check("true_jaccard",def_jaccard({"a","b"},{"b","c"})==1/3)
    check("minhash_deterministic",def_minhash_bands({"abc","bcd"},cfg)==def_minhash_bands({"bcd","abc"},cfg))
    with tempfile.TemporaryDirectory(prefix="via_nlp_tests_") as tmp:
        root = Path(tmp)
        raw = root/"raw"
        raw.mkdir()
        (raw/"sample.txt").write_text("你好,世界!",encoding="utf-8")
        (raw/"sample.jsonl").write_text('{"text":"EPS 12.5元","id":1}\n{broken}\n',encoding="utf-8")
        one = def_batch(raw,root/"out",cfg)
        two = def_batch(raw,root/"out",cfg)
        check("batch_error_not_dropped",one["counts"]["ERROR"]==1)
        check("checkpoint_resume",two["counts"]["cached"]==3)
        check("input_not_overwritten",(raw/"sample.txt").read_text(encoding="utf-8")=="你好,世界!")
        docs = root/"dedup.jsonl"
        a = "這是研究報告中的共同背景敘述，市場持續關注半導體產業發展與長期競爭優勢，EPS 12.50元。"
        docs.write_text("\n".join(def_json({"id":i,"text":t}) for i,t in enumerate((a,a,a.replace("12.50","12.51"),a+"新增觀察。")))+"\n{bad}\n",encoding="utf-8")
        d = def_dedup(docs,root/"dedup",cfg)
        check("dedup_exact",d["counts"].get("DUPLICATE",0)>=1)
        check("changed_eps_preserved","12.51" in (Path(d["output"])/"retained.jsonl").read_text(encoding="utf-8"))
        check("dedup_invalid_retained",d["counts"].get("ERROR")==1 and (Path(d["output"])/"errors.jsonl").read_bytes()==b"{bad}\n")
        check("dedup_all_rows_accounted",sum(d["counts"].values())==5)
        d2 = def_dedup(docs,root/"dedup",cfg)
        check("dedup_resume",d2["newly_indexed"]==0)
        longest = def_dedup(docs,root/"longest",{**cfg,"keep":"longest"})
        check("longest_mode_accounted",sum(longest["counts"].values())==5)
    compile(Path(__file__).read_text(encoding="utf-8"),str(__file__),"exec")
    ast.parse(Path(__file__).read_text(encoding="utf-8"))
    check("ast_compile",True)
    summary = {"version":VERSION,"kind":"self-test","status":"PASS" if all(t["status"]=="PASS" for t in tests) else "FAIL",
               "counts":{"PASS":sum(t["status"]=="PASS" for t in tests),"FAIL":sum(t["status"]=="FAIL" for t in tests)},
               "tests":tests,"health":def_health(),"limitations":["Optional model inference is not included","Windows acceptance and 50GB benchmark are not included"]}
    output = Path(output)
    output.mkdir(parents=True,exist_ok=True)
    def_atomic_write(output/"selftest.json",def_json(summary))
    def_report(summary,output/"matrix.html")
    return summary


def def_main(argv=None):
    parser = argparse.ArgumentParser(description="VIA NLP OneEngine 1.9.0 / local integration")
    parser.add_argument("--config",type=Path,help="JSON overrides for DEFAULTS")
    sub = parser.add_subparsers(dest="command",required=True)
    sub.add_parser("health")
    test = sub.add_parser("self-test")
    test.add_argument("--output",type=Path,default=Path("VIA_NLP_SelfTest"))
    process = sub.add_parser("process")
    selection = process.add_mutually_exclusive_group(required=True)
    selection.add_argument("--text")
    selection.add_argument("--file",type=Path)
    process.add_argument("--output",type=Path,default=Path("VIA_NLP_Output"))
    process.add_argument("--markdown-analysis",action="store_true")
    process.add_argument("--analysis-task",choices=["none","analyze","knowledge","govern"],default="analyze",help="Preserved v1.8 source analysis; default analyze")
    for name in ("batch","dedup"):
        p = sub.add_parser(name)
        p.add_argument("--input",type=Path,required=True)
        p.add_argument("--output",type=Path,required=True)
    legacy = sub.add_parser("legacy")
    legacy.add_argument("--runtime",type=Path,default=Path("VIA_NLP_Runtime"))
    legacy.add_argument("args",nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    cfg = def_config(json.loads(args.config.read_text(encoding="utf-8-sig")) if args.config else None)
    if args.command == "legacy":
        rest = args.args[1:] if args.args and args.args[0]=="--" else args.args
        return def_legacy(rest,args.runtime)
    if args.command == "health":
        result = def_health()
    elif args.command == "self-test":
        result = def_self_test(args.output)
    elif args.command == "process":
        if args.file and args.file.stat().st_size > cfg["max_record_bytes"]:
            raise ValueError("Input file too large; use JSONL batches")
        text = args.text if args.text is not None else args.file.read_bytes().decode(cfg["encoding"])
        result = def_process(text,cfg,str(args.file or "inline"))
        if args.analysis_task != "none":
            analysis_text = result["processed_text"] if cfg["redact"] else text
            result["legacy_analysis"] = def_legacy_analysis(analysis_text,args.output/"bundled",args.analysis_task)
            result["legacy_analysis_source"] = "redacted_projection" if cfg["redact"] else "original_source"
        if args.markdown_analysis:
            result["markdown_analysis"] = def_markdown_analysis(result["processed_text"],args.output/"bundled")
        with def_writer_lock(args.output):
            run = def_run_dir(args.output)
            def_atomic_write(run/"result.json",def_json(result))
            def_atomic_write(run/"processed.txt",result["processed_text"])
            def_report({"status":result["status"],"counts":{"sentences":len(result["sentences"]),"chunks":len(result["chunks"]),"reviews":len(result["reviews"])},"reviews":result["reviews"],"health":def_health()},run/"matrix.html")
            result = {"status":result["status"],"output":str(run),"reviews":result["reviews"]}
    elif args.command == "batch":
        result = def_batch(args.input,args.output,cfg)
    else:
        result = def_dedup(args.input,args.output,cfg)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 1 if result.get("status") in ("ERROR","FAIL") else 0


if __name__ == "__main__":
    try:
        raise SystemExit(def_main())
    except KeyboardInterrupt:
        print("\n已中止；已提交的檢查點保留。",file=sys.stderr)
        raise SystemExit(130)
    except Exception as exc:
        print(type(exc).__name__+": "+str(exc),file=sys.stderr)
        raise SystemExit(1)
