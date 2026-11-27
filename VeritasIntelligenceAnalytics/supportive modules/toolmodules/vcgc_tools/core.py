#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""Bounded, read-only inputs and exclusive run-local outputs. [VIA:ACCEL-BRIDGE]"""
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

VERSION = "v0100"
MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_FILES = 30000
MAX_WORKERS = 6
MAX_CONTEXT_CHARS = 12000
MAX_JSON_BYTES = 128 * 1024 * 1024
VERBS = ("panorama", "catalog", "context", "module-check", "skills", "metrics", "schema", "compare", "registration-plan", "graph")
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", "site-packages", "_toolmodules_runs"}
SOURCE_SUFFIXES = {".py", ".ps1", ".psm1", ".json", ".md"}

import hashlib
import json
import os
import stat
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data if isinstance(data, bytes) else encode(data)).hexdigest()


def encode(data):
    return json.dumps(data, ensure_ascii=False, sort_keys=True, allow_nan=False, separators=(",", ":")).encode("utf-8")


def strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("DUPLICATE_JSON_KEY: " + key)
            result[key] = value
        return result
    def reject_constant(value):
        raise ValueError("NONFINITE_JSON: " + value)
    return json.loads(text, object_pairs_hook=pairs, parse_constant=reject_constant)


def is_link(path):
    info = Path(path).lstat()
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400)


def read_bytes(path, limit=MAX_FILE_BYTES):
    path = Path(path)
    if is_link(path):
        raise ValueError("LINK_INPUT_REJECTED")
    before = path.stat()
    if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
        raise ValueError("INPUT_SIZE_OR_TYPE_LIMIT")
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    after = path.stat()
    if len(raw) > limit or (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError("INPUT_CHANGED_DURING_READ")
    return raw


def load_json(path):
    return strict_json(read_bytes(path, MAX_JSON_BYTES).decode("utf-8-sig"))


def within(path, root):
    return Path(path).resolve().is_relative_to(Path(root).resolve())


def node_id(namespace, path, qualified):
    return "VTM-N-" + uuid.uuid5(uuid.NAMESPACE_URL, namespace + "/" + path + "#" + qualified).hex[:24]


def new_run(output, roots):
    output = Path(output).expanduser().resolve()
    for root in roots:
        if within(output, root):
            raise ValueError("OUTPUT_MUST_BE_OUTSIDE_INPUT_ROOTS")
    output.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(output).free < 64 * 1024 * 1024:
        raise ValueError("INSUFFICIENT_FREE_DISK")
    run = output / (datetime.now(timezone.utc).strftime("RUN_%Y%m%dT%H%M%S_") + uuid.uuid4().hex[:12])
    run.mkdir(exist_ok=False)
    return run


def write_new(path, data):
    """original(absent) -> apply / proposed(equal) -> skip / other -> fail."""
    path = Path(path)
    raw = data if isinstance(data, bytes) else (data.encode("utf-8") if isinstance(data, str) else encode(data) + b"\n")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        return "APPLIED_NEW"
    except FileExistsError:
        if read_bytes(path, max(MAX_FILE_BYTES, len(raw))) == raw:
            return "SKIPPED_IDENTICAL"
        raise ValueError("HASH_STATE_CONFLICT: " + str(path))


def event(run, kind, payload, previous="0" * 64):
    row = {"at": now(), "kind": kind, "payload": payload, "previous_sha256": previous}
    row["sha256"] = digest(row)
    write_new(Path(run) / "events" / (row["sha256"] + ".json"), row)
    return row["sha256"]


def budget(workers=MAX_WORKERS):
    cpu = os.cpu_count() or 1
    return {"workers": max(1, min(workers, MAX_WORKERS, cpu)), "cpu_count": cpu,
            "global_cpu_memory_mutation": False, "celeritas": "NOT_ACTIVATED",
            "reason": "Read-only inspection does not import target accelerator or network modules."}
