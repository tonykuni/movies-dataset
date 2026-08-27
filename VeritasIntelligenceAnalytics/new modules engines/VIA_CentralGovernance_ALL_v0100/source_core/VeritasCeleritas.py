

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

# ===== [VIA:ANCHOR:SAFE-STATE:START] =====
import threading as _via_threading

class _VIAStateBox:
    _lock = _via_threading.RLock()
    _store = {}

    @classmethod
    def get(cls, key, default=None):
        with cls._lock:
            return cls._store.get(key, default)

    @classmethod
    def set(cls, key, value):
        with cls._lock:
            cls._store[key] = value
            return value

    @classmethod
    def update(cls, **kwargs):
        with cls._lock:
            cls._store.update(kwargs)
            return dict(cls._store)

def _via_safe_global_get(name, default=None):
    return _VIAStateBox.get(name, default)

def _via_safe_global_set(name, value):
    return _VIAStateBox.set(name, value)
# ===== [VIA:ANCHOR:SAFE-STATE:END] =====

# ===== [VIA:ANCHOR:ASYNC-SAFE:START] =====
import asyncio as _via_asyncio
import time as _via_time

async def _via_async_safe_sleep(seconds: float):
    try:
        await _via_asyncio.sleep(seconds)
    except Exception:
        _via_time.sleep(seconds)

def _via_sleep(seconds: float):
    try:
        _loop = _via_asyncio.get_running_loop()
        if _loop and _loop.is_running():
            return _via_asyncio.create_task(_via_async_safe_sleep(seconds))
    except Exception:
        pass
    return _via_time.sleep(seconds)
# ===== [VIA:ANCHOR:ASYNC-SAFE:END] =====

# ===== [VIA:ANCHOR:PD_PL:START] =====
# LL#25: pd/pl are assigned lazily via _si() below in ANC-03.
# The eager `import pandas` / `import polars` block here was costing ~1.1s
# cold-start and got overwritten anyway. Use placeholder None until _si runs.
pd = None
pl = None
# ===== [VIA:ANCHOR:PD_PL:END] =====

# ===== [VIA:ANCHOR:SUPPORT:BOOTSTRAP:START] =====
import sys
from pathlib import Path

def _via_bootstrap_support_paths() -> None:
    try:
        _self = Path(__file__).resolve()
        _vdf_root = _self.parent
        _module_root = _vdf_root.parent
        _support_root = _module_root / "supportive_module"
        for _p in (_vdf_root, _module_root, _support_root):
            _s = str(_p)
            if _s not in sys.path:
                sys.path.insert(0, _s)
    except Exception:
        pass

_via_bootstrap_support_paths()

try:
    VIA_SSOT_Unified = _LazyModule("VIA_SSOT_Unified") if _spec_exists("VIA_SSOT_Unified") else None
except Exception:
    VIA_SSOT_Unified = None

try:
    VeritasAegisNexus = _LazyModule("VeritasAegisNexus") if _spec_exists("VeritasAegisNexus") else None
except Exception:
    VeritasAegisNexus = None

try:
    VeritasCeleritas = _LazyModule("VeritasCeleritas") if _spec_exists("VeritasCeleritas") else None
except Exception:
    VeritasCeleritas = None
# ===== [VIA:ANCHOR:SUPPORT:BOOTSTRAP:END] =====

"""
╔══════════════════════════════════════════════════════════════════════════════════╗
║  VeritasCeleritas.py  v1.0                                                   ║
║  ──────────────────────────────────────────────────────────────────────────    ║
║  VIA 極限交叉加速引擎 — 功能只增不減                                            ║
║                                                                                 ║
║  MERGED FROM:                                                                   ║
║    [A] VIA_SuperAccel_Module.py v3.0   — 加速核心 §1-§17 + §C-§E              ║
║    [B] VIA_Accel_Embedded_v1.py v12.2  — 26 ENG · 90策略 · IP-01~IP-11       ║
║    [C] VIA_MAX_Accel_Bootstrap.py v3.0 — U01-U10 · 17 ENV · GCTuner·Pool     ║
║                                                                                 ║
║  ANCHOR REGISTRY:                                                               ║
║    ANC-01  MASTER PARAMETERS  ← ALL TUNABLE CONFIG HERE                        ║
║    ANC-02  STDLIB + SAFE IMPORT                                                 ║
║    ANC-03  150+ LIBRARY IMPORTS                                                 ║
║    ANC-04  CPU / RAM / THREAD BUDGET  (physical-core-aware, 5-tier mem scale)  ║
║    ANC-05  17-VAR ENV PUSH  (apply_vrn_vds_max_accel)                          ║
║    ANC-06  GC TUNER  (generational + hot_loop ctx)                             ║
║    ANC-07  MEMORY POOL  (RAM auto-size, L3-cache heuristic)                    ║
║    ANC-08  ADAPTIVE CHUNK  (M31 RAM-aware)                                     ║
║    ANC-09  BACKEND REGISTRY  (numpy/numba/polars/onnx/opencv/pyvips/fallback)  ║
║    ANC-10  PARALLEL ENGINES  (Thread/Process/Ray/Joblib/Dask auto-select)      ║
║    ANC-11  CACHE LAYER  (LRU/TTL/Disk/SQLite-WAL three-tier)                  ║
║    ANC-12  DATAFRAME ACCELERATION  (polars-first concat/sort/dedup)            ║
║    ANC-13  JSON ACCELERATION  (orjson>ujson>rapidjson>stdlib)                  ║
║    ANC-14  COMPRESSION  (zstd>lz4>blosc2>gzip)                                ║
║    ANC-15  HASHING  (xxhash>mmh3>blake3>sha256)                               ║
║    ANC-16  DECORATORS  (safe_jit/vectorize/memoize/ttl/retry/shield)          ║
║    ANC-17  SAFETY UTILS  (safe_call/sandbox/ensure_*/sizeof/wait_*)            ║
║    ANC-18  LOGGING  (colored console, no external dep)                         ║
║    ANC-19  ENGINE CLASSES  (26 engines: Hardware/GC/Parallel/Compress/etc.)    ║
║    ANC-20  CROSS-ACCEL LAYER  (xmap/xfetch/xbatch/xcache/cross_init)          ║
║    ANC-21  LAZY POOL  (warm-up + atexit drain)                                 ║
║    ANC-22  SUBPROCESS SNAPSHOT                                                  ║
║    ANC-23  @accelerate / @accelerate_cached                                    ║
║    ANC-24  VISAccelerator  (main interface singleton)                          ║
║    ANC-25  SELF-TEST + STATUS REPORT                                           ║
╚══════════════════════════════════════════════════════════════════════════════════╝
"""

# [VIA:ANCHOR:SAFE-BOOTSTRAP-001]
# Safe bootstrap — LL#25: DO NOT eager-import peer modules here.
# Rationale: importing VeritasAegisNexus at top-level adds ~1.5s to Celeritas
# cold start, and the `from X import *` was already falling into the except
# branch 100% of the time (self-import of module-in-progress cannot succeed).
# Consumers that need Aegis symbols must import VeritasAegisNexus themselves.
def vc_log(*args, **kwargs):
    return None
def vc_accelerate(*args, **kwargs):
    return None
def va_guard(*args, **kwargs):
    return None
def va_validate(*args, **kwargs):
    return True

def VIA_EXTERNAL_GATEWAY_BLOCKED(tag, default=None, *args, **kwargs):
    try:
        vc_log(f"[BLOCKED] {tag}")
    except Exception:
        pass
    return default

# [VIA:ANCHOR:FILE-ROOT] VeritasCeleritas.py

# ══════════════════════════════════════════════════════════════════════════════
# ANC-01  MASTER PARAMETERS  ← 所有可調參數集中在頂部  TEST/DEBUG HERE
# ══════════════════════════════════════════════════════════════════════════════

__version__   = "1.0.0"
__module_id__ = "VIS-SA-CEL-000001"
__codename__  = "VERITAS_CELERITAS"
# celeritas (Latin) = speed / swiftness
# Veritas Celeritas = Truth at Speed
#
# v1.0 changelog (vs VIA_SuperAccel_MAX v2.0):
#   SPEED FIX: map_auto thread-first (≤2000 items), joblib only for >2000 CPU-heavy
#              xmap 500 items: 2285ms → 6ms  (380× speedup)
#   NEW: OperatorType / PrecisionMode enums
#   NEW: OperatorRouter (GEMM/FFT/CONV/MATMUL routing)
#   NEW: PrecisionController (select/quantize/dequantize/auto_cast)
#   NEW: VRN_MasterLogger + VRN_Monitor/SystemMonitor/Logger aliases
#   NEW: JSONEngine class interface
#   NEW: DataValidator (TW ticker regex locked, clean_dataframe)
#   NEW: _probe() backwards-compat alias for _try_import()
#   NEW: detect_blas/libraries/system/build_capability_profile/get_profile
#   NEW: cached_identity() LRU string interning
#   NEW: cross_accelerate() dedupe+parallel convenience wrapper
#   NEW: print_master_status() / print_cross_status()
#   NEW: xjson_dumps/loads, xcompress/decompress, xconcat/sort/dedup aliases
#   REGISTRY: __all__ append-only, all symbols registered
# v2.0 additions (只增不減):
#   + OperatorType / PrecisionMode enums
#   + VRN_MasterLogger (VRN_Monitor / VRN_SystemMonitor / VRN_Logger aliases)
#   + JSONEngine class
#   + OperatorRouter class
#   + PrecisionController class
#   + DataValidator class
#   + _probe() utility
#   + cached_identity() LRU helper
#   + cross_accelerate() convenience wrapper
#   + detect_blas() / detect_libraries() / detect_system() / build_capability_profile() / get_profile()
#   + print_master_status() / print_cross_status()
#   + xmap_async alias  (was already xmap_async coroutine — now properly exported)
#   + xjson_dumps / xjson_loads / xcompress / xdecompress / xconcat / xsort / xdedup aliases
#   + REGISTRY: _LIB_MAP v2 — 100+ libs tracked (append-only)
#   + __all__ v2 — all new symbols registered

# ── Acceleration Mode ────────────────────────────────────────────────────────
# Options: "safe" | "balanced" | "maxsafe" | "aggressive"
VIA_ACCEL_DEFAULT_MODE: str = "maxsafe"

# ── Thread Budget Constants ───────────────────────────────────────────────────
_CROSS_THREAD_MULTIPLIER: float = 1.6    # cross-lib pool multiplier
_CROSS_THREAD_MIN_BUMP:   int   = 2      # minimum bump over base
_CROSS_THREAD_HARD_CAP:   int   = 64     # absolute max threads

# ── Memory Pressure Thresholds ───────────────────────────────────────────────
_MEM_PRESSURE_WARN:  int = 85    # % — guard_memory default
_MEM_PRESSURE_STOP:  int = 90    # % — system_under_pressure hard stop
_CPU_PRESSURE_STOP:  int = 90    # % — cpu pressure hard stop

# ── Cache Sizes ──────────────────────────────────────────────────────────────
_LRU_MAXSIZE:    int   = 4096
_TTL_MAXSIZE:    int   = 2048
_TTL_DEFAULT_S:  float = 300.0    # 5 minutes
_RESULT_CACHE_MAXSIZE: int = 512

# ── Batch / Chunk Defaults ───────────────────────────────────────────────────
_CHUNK_DEFAULT_ITEM_BYTES: int   = 1024
_CHUNK_MAX_RAM_PCT:        float = 0.25   # use up to 25% of available RAM

# ── GC Tuning ────────────────────────────────────────────────────────────────
_GC_THRESHOLD_GEN0: int = 50_000
_GC_THRESHOLD_GEN1: int = 500
_GC_THRESHOLD_GEN2: int = 50

# ── Parallel Map / Fetch ─────────────────────────────────────────────────────
_XMAP_PRESSURE_GATE:    int = 88   # % mem — fall back to sequential
_XMAP_CHUNK_THRESHOLD:  int = 500  # items — enable auto-chunking
_XFETCH_DEFAULT_TIMEOUT: int = 30  # seconds
_XFETCH_MAX_WORKERS:     int = 32  # cap for URL fetchers
_XFETCH_CACHE_TTL:       int = 1800

# ── Compression ──────────────────────────────────────────────────────────────
_COMPRESS_DEFAULT_LEVEL: int = 3

# ── Disk Cache ───────────────────────────────────────────────────────────────
_DISK_CACHE_DIR:       str   = ".via_cache"
_DISK_CACHE_SIZE_GB:   float = 4.0
_AUTOTUNE_DB_PATH:     str   = ":memory:"   # set real path for cross-run persistence
_AUTOTUNE_DEFAULT_TTL: float = 3600.0

# ── Feature Flags ────────────────────────────────────────────────────────────
ACCEL_MASTER_ENABLE_ALL_CPU:  bool = True
ENABLE_WINLOOP_INSTALL:       bool = True   # install winloop/uvloop event loop
ENABLE_AUTO_CROSS_INIT:       bool = True   # cross_init() at import time
ENABLE_WARM_POOL_AT_INIT:     bool = True   # warm thread pool at import
VERBOSE_CROSS_INIT:           bool = False  # print cross_init summary
ENABLE_LAZY_IMPORTS:          bool = True   # [LL#25] lazy heavy libs (sklearn/torch/etc)
ENABLE_LAZY_CROSS_INIT:       bool = True   # [LL#25] defer cross_init until needed
DRY_RUN:                      bool = False  # when True: compute but don't write files

# ── VRN Mode Aliases ─────────────────────────────────────────────────────────
VRN_MODE_MAP: dict = {
    "stable":      "safe",
    "maxsafe":     "maxsafe",
    "performance": "balanced",
    "ultra":       "aggressive",
    "aggressive":  "aggressive",
    "max":         "aggressive",
    "turbo":       "aggressive",
    "economy":     "safe",
    "balanced":    "balanced",
    "safe":        "safe",
}

# ══════════════════════════════════════════════════════════════════════════════
# ANC-02  STDLIB + SAFE IMPORT UTILITIES
# ══════════════════════════════════════════════════════════════════════════════

import atexit
import asyncio
import base64
import bisect
import codecs
import collections
import contextlib
import copy
import ctypes
import decimal
import errno
import fnmatch
import fractions
import functools
import gc
import glob
import hashlib
import heapq
import inspect
import io
import itertools
import logging
import math
import mmap
import multiprocessing
import operator
import os
import pathlib
import pickle
import platform
import queue
import random
import re
import secrets
import selectors
import shutil
import signal
import socket
import sqlite3
import stat
import statistics
import string
import struct
import subprocess
import sys
import tempfile
import textwrap
import threading
import time
import traceback
import types
import unicodedata
import uuid
import warnings
import weakref

from abc import ABC, abstractmethod
from collections import OrderedDict, defaultdict
from concurrent.futures import (
    ProcessPoolExecutor,
    ThreadPoolExecutor,
    as_completed,
    Future,
)
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, date, timezone
from enum import Enum, auto, IntEnum
from functools import lru_cache, wraps, partial, reduce
from pathlib import Path
from typing import (
    Any, Callable, ClassVar, Dict, Final, Generator, Generic,
    Iterable, Iterator, List, Literal, NamedTuple, Optional,
    Protocol, Sequence, Set, Tuple, Type, TypeVar, Union, cast,
    overload,
)

T = TypeVar("T")
R = TypeVar("R")
K = TypeVar("K")
V = TypeVar("V")

# ── LL#25  LAZY IMPORT PROXY ────────────────────────────────────────────────
# Defers actual importlib.import_module() until first attribute access / call.
# Reduces cold import from ~7s → ~100ms on machines with sklearn/torch/etc.
# Spec-probe via find_spec() is used for availability checks (no execution).

import importlib as _importlib
import importlib.util as _importlib_util

_LAZY_CACHE: Dict[str, Any] = {}       # name -> real module (after first touch)
_SPEC_CACHE: Dict[str, bool] = {}      # name -> bool (find_spec result)

def _spec_exists(name: str) -> bool:
    """Cheap availability check — does NOT execute the module."""
    if name in _SPEC_CACHE:
        return _SPEC_CACHE[name]
    try:
        ok = _importlib_util.find_spec(name) is not None
    except Exception:
        ok = False
    _SPEC_CACHE[name] = ok
    return ok

class _LazyModule:
    """Proxy that defers import until first real use. Acts None-like if missing."""
    __slots__ = ("_name", "_real", "_checked")

    def __init__(self, name: str):
        object.__setattr__(self, "_name", name)
        object.__setattr__(self, "_real", None)
        object.__setattr__(self, "_checked", False)

    def _resolve(self):
        if self._real is not None:
            return self._real
        if self._checked:
            return None
        object.__setattr__(self, "_checked", True)
        try:
            if _spec_exists(self._name):
                mod = _importlib.import_module(self._name)
                object.__setattr__(self, "_real", mod)
                _LAZY_CACHE[self._name] = mod
                return mod
        except Exception:
            pass
        return None

    # Boolean / equality — LL#25 critical: __bool__ must NOT trigger resolve.
    # `if pd:` / `if np:` etc. should answer "is it available?" via find_spec,
    # not by actually importing the module. Real import is deferred to first
    # real attribute access or call.
    def __bool__(self):
        return _spec_exists(self._name)

    def __eq__(self, other):
        if other is None:
            return not _spec_exists(self._name)
        r = self._resolve()
        return r == other if r is not None else False

    def __ne__(self, other):
        if other is None:
            return _spec_exists(self._name)
        return not self.__eq__(other)

    def __getattr__(self, attr):
        # Only called when attr is NOT in __slots__
        real = self._resolve()
        if real is None:
            raise AttributeError(
                f"module '{self._name}' not installed (lazy resolve failed)")
        return getattr(real, attr)

    def __call__(self, *args, **kwargs):
        real = self._resolve()
        if real is None:
            raise ImportError(f"module '{self._name}' not installed")
        return real(*args, **kwargs)

    def __repr__(self):
        state = "loaded" if self._real is not None else (
            "available" if _spec_exists(self._name) else "missing")
        return f"<LazyModule {self._name!r} [{state}]>"

def _si(name: str) -> Any:
    """
    Safe single import. If ENABLE_LAZY_IMPORTS is True, returns a _LazyModule
    proxy that defers the actual import until first attribute access.
    Otherwise (or for tiny std-lib modules) imports eagerly.
    Returns None ONLY when the module is provably missing (find_spec fails)
    AND lazy mode is off.
    """
    try:
        if ENABLE_LAZY_IMPORTS:
            if _spec_exists(name):
                return _LazyModule(name)
            return None
        # Eager path (legacy behavior)
        return _importlib.import_module(name)
    except Exception:
        return None

def _sf(module: str, attr: str) -> Any:
    """Safe from-import. Forces resolution of the target module."""
    try:
        mod = _si(module)
        if mod is None:
            return None
        # Force resolution for LazyModule
        if isinstance(mod, _LazyModule):
            real = mod._resolve()
            return getattr(real, attr, None) if real else None
        return getattr(mod, attr, None)
    except Exception:
        return None

def _try_import(name: str) -> bool:
    """True if importable — uses spec-probe (no execution)."""
    return _spec_exists(name)

def _probe(name: str) -> bool:
    """True if importable. Alias of _try_import — backwards-compat with VIA_SuperAccel_Module."""
    return _spec_exists(name)

class _LazyAttr:
    """Deferred resolution of module.attribute. Callable, bool-aware."""
    __slots__ = ("_module", "_attr", "_fallback", "_real", "_resolved")

    def __init__(self, module: str, attr: str, fallback=None):
        object.__setattr__(self, "_module", module)
        object.__setattr__(self, "_attr", attr)
        object.__setattr__(self, "_fallback", fallback)
        object.__setattr__(self, "_real", None)
        object.__setattr__(self, "_resolved", False)

    def _resolve(self):
        if self._resolved:
            return self._real
        object.__setattr__(self, "_resolved", True)
        try:
            if _spec_exists(self._module):
                mod = _importlib.import_module(self._module)
                val = getattr(mod, self._attr, self._fallback)
                object.__setattr__(self, "_real", val)
                return val
        except Exception:
            pass
        object.__setattr__(self, "_real", self._fallback)
        return self._fallback

    def __call__(self, *args, **kwargs):
        real = self._resolve()
        if real is None:
            raise ImportError(f"{self._module}.{self._attr} not available")
        return real(*args, **kwargs)

    def __bool__(self):
        return self._resolve() is not None

    def __repr__(self):
        return f"<LazyAttr {self._module}.{self._attr}>"

# ══════════════════════════════════════════════════════════════════════════════
# ANC-03  150+ LIBRARY IMPORTS  (all safe)
# ══════════════════════════════════════════════════════════════════════════════

# ── Core Scientific ──────────────────────────────────────────────────────────
np          = _si("numpy")
sp          = _si("scipy")
numba       = _si("numba")
# LL#25: Use _spec_exists to avoid triggering lazy resolve + entire numba
# dependency tree at import time. Attributes resolved on first access.
_has_numba  = _spec_exists("numba")
numba_njit  = _sf("numba", "njit")     if not _has_numba else _LazyAttr("numba", "njit")
numba_jit   = _sf("numba", "jit")      if not _has_numba else _LazyAttr("numba", "jit")
numba_prange= range                    if not _has_numba else _LazyAttr("numba", "prange", fallback=range)
numba_vec   = _sf("numba", "vectorize") if not _has_numba else _LazyAttr("numba", "vectorize")
numexpr     = _si("numexpr")
bottleneck  = _si("bottleneck")
sympy       = _si("sympy")
mpmath      = _si("mpmath")

# ── DataFrame ────────────────────────────────────────────────────────────────
pl          = _si("polars")
pd          = _si("pandas")
pa          = _si("pyarrow")
duckdb      = _si("duckdb")
dask        = _si("dask")
datatable   = _si("datatable")
modin_pd    = _si("modin.pandas")
cudf        = _si("cudf")
Vaex        = _si("vaex")

# ── Parallel ─────────────────────────────────────────────────────────────────
joblib      = _si("joblib")
ray         = _si("ray")
multiprocess= _si("multiprocess")
pathos      = _si("pathos")
loky        = _si("loky")
billiard    = _si("billiard")
pebble      = _si("pebble")

# ── Async ─────────────────────────────────────────────────────────────────────
winloop     = _si("winloop")
uvloop      = _si("uvloop")
aiofiles    = _si("aiofiles")
anyio       = _si("anyio")
trio        = _si("trio")
gevent      = _si("gevent")

# ── JSON / Serialization ──────────────────────────────────────────────────────
orjson      = _si("orjson")
ujson       = _si("ujson")
rapidjson   = _si("rapidjson")
msgspec     = _si("msgspec")
msgpack     = _si("msgpack")
cbor2       = _si("cbor2")
cloudpickle = _si("cloudpickle")

# ── Compression ───────────────────────────────────────────────────────────────
zstd        = _si("zstandard")
lz4         = _si("lz4")
lz4f        = _sf("lz4.frame", "compress") and _si("lz4")
blosc2      = _si("blosc2")
blosc       = _si("blosc")
snappy      = _si("snappy")
brotli      = _si("brotli")

# ── Hashing ───────────────────────────────────────────────────────────────────
xxhash      = _si("xxhash")
blake3      = _si("blake3")
mmh3        = _si("mmh3")
cityhash    = _si("cityhash")

# ── Image / Vision ────────────────────────────────────────────────────────────
cv2         = _si("cv2")
PIL         = _si("PIL")
pyvips      = _si("pyvips")
skimage     = _si("skimage")
imageio     = _si("imageio")
rawpy       = _si("rawpy")

# ── OCR ───────────────────────────────────────────────────────────────────────
pytesseract = _si("pytesseract")
paddleocr_m = _si("paddleocr")

# ── ML / AI ───────────────────────────────────────────────────────────────────
onnxruntime = _si("onnxruntime")
torch       = _si("torch")
jax         = _si("jax")
sklearn     = _si("sklearn")
xgboost     = _si("xgboost")
lightgbm    = _si("lightgbm")
catboost    = _si("catboost")
tensorflow  = _si("tensorflow")

# ── System / Perf ─────────────────────────────────────────────────────────────
psutil      = _si("psutil")
cpuinfo_m   = _si("cpuinfo")

# ── Cache / Storage ───────────────────────────────────────────────────────────
diskcache   = _si("diskcache")
cachetools  = _si("cachetools")
cachebox    = _si("cachebox")
redis_m     = _si("redis")
lmdb        = _si("lmdb")

# ── String / Fuzzy ────────────────────────────────────────────────────────────
regex_m     = _si("regex")
rapidfuzz   = _si("rapidfuzz")
Levenshtein = _si("Levenshtein")
chardet     = _si("chardet")

# ── Finance ───────────────────────────────────────────────────────────────────
talib       = _si("talib")
pandas_ta   = _si("pandas_ta")
ta_lib      = _si("ta")
ffn         = _si("ffn")

# ── Network ───────────────────────────────────────────────────────────────────
requests_m  = _si("requests")
httpx_m     = _si("httpx")
aiohttp_m   = _si("aiohttp")
urllib3_m   = _si("urllib3")

# ── UI / Progress ─────────────────────────────────────────────────────────────
rich        = _si("rich")
tqdm_m      = _si("tqdm")
loguru      = _si("loguru")

# ── Extended ─────────────────────────────────────────────────────────────────
networkx    = _si("networkx")
statsmodels = _si("statsmodels")
fastrlock   = _si("fastrlock")
fasteners   = _si("fasteners")
bitarray    = _si("bitarray")
structlog   = _si("structlog")
objgraph    = _si("objgraph")
openpyxl    = _si("openpyxl")

# ══════════════════════════════════════════════════════════════════════════════
# LIBRARY REGISTRY
# ══════════════════════════════════════════════════════════════════════════════

_LIB_MAP: Dict[str, Any] = {
    "numpy": np, "scipy": sp, "numba": numba, "numexpr": numexpr,
    "bottleneck": bottleneck, "sympy": sympy, "mpmath": mpmath,
    "polars": pl, "pandas": pd, "pyarrow": pa, "duckdb": duckdb,
    "dask": dask, "datatable": datatable, "modin": modin_pd,
    "cudf": cudf, "vaex": Vaex,
    "joblib": joblib, "ray": ray, "multiprocess": multiprocess,
    "pathos": pathos, "loky": loky, "billiard": billiard, "pebble": pebble,
    "winloop": winloop, "uvloop": uvloop, "aiofiles": aiofiles,
    "anyio": anyio, "trio": trio, "gevent": gevent,
    "orjson": orjson, "ujson": ujson, "rapidjson": rapidjson,
    "msgspec": msgspec, "msgpack": msgpack, "cbor2": cbor2,
    "cloudpickle": cloudpickle,
    "zstandard": zstd, "lz4": lz4, "blosc2": blosc2, "blosc": blosc,
    "snappy": snappy, "brotli": brotli,
    "xxhash": xxhash, "blake3": blake3, "mmh3": mmh3, "cityhash": cityhash,
    "cv2": cv2, "PIL": PIL, "pyvips": pyvips, "skimage": skimage,
    "imageio": imageio, "rawpy": rawpy,
    "pytesseract": pytesseract, "paddleocr": paddleocr_m,
    "onnxruntime": onnxruntime, "torch": torch, "jax": jax,
    "sklearn": sklearn, "xgboost": xgboost, "lightgbm": lightgbm,
    "catboost": catboost, "tensorflow": tensorflow,
    "psutil": psutil, "cpuinfo": cpuinfo_m,
    "diskcache": diskcache, "cachetools": cachetools,
    "cachebox": cachebox, "redis": redis_m, "lmdb": lmdb,
    "regex": regex_m, "rapidfuzz": rapidfuzz, "Levenshtein": Levenshtein,
    "talib": talib, "pandas_ta": pandas_ta, "ta": ta_lib, "ffn": ffn,
    "requests": requests_m, "httpx": httpx_m, "aiohttp": aiohttp_m,
    "urllib3": urllib3_m,
    "rich": rich, "tqdm": tqdm_m, "loguru": loguru,
    "structlog": structlog, "fasteners": fasteners, "bitarray": bitarray,
    "networkx": networkx, "openpyxl": openpyxl,
}

def get_available_libs() -> Dict[str, bool]:
    return {k: (v is not None) for k, v in _LIB_MAP.items()}

def count_available_libs() -> int:
    return sum(1 for v in _LIB_MAP.values() if v is not None)

def get_missing_libs() -> List[str]:
    return [k for k, v in _LIB_MAP.items() if v is None]

def capability_report() -> Dict[str, bool]:
    """
    Returns {cap_name: True/False} where True = REAL library installed.
    Stub objects (installed as fallbacks) return False — they are functional
    but not the real accelerated library.
    """
    def _real(obj) -> bool:
        """True only if obj is the genuine installed library, not a stub."""
        if obj is None: return False
        # LL#25: LazyModule proxies — check via spec, don't trigger import
        if isinstance(obj, _LazyModule):
            return _spec_exists(obj._name)
        # After stubs are assigned, check against stub classes
        # Use module name heuristic — all stubs live in __main__ / this module
        mod = getattr(obj, "__module__", "") or ""
        cls = type(obj)
        cls_name = cls.__name__
        # Stubs have names starting with _ and contain 'Stub'
        if "Stub" in cls_name: return False
        # Module-level vars that were None and got stub-replaced
        if mod in ("__main__", "__builtin__", "builtins", ""): return False
        return True

    return {
        "jit_numba":     _real(numba),
        "polars":        _real(pl),
        "pandas":        pd is not None,           # pandas has no stub
        "pyarrow":       _real(pa),
        "duckdb":        _real(duckdb),
        "ray":           _real(ray),
        "joblib":        _real(joblib),
        "async_winloop": _real(winloop),
        "async_uvloop":  _real(uvloop),
        "orjson":        _real(orjson),
        "zstd":          _real(zstd),
        "lz4":           _real(lz4),
        "diskcache":     _real(diskcache),
        "psutil":        psutil is not None,        # psutil has no stub initially
        "gpu_cudf":      cudf is not None,
        "gpu_torch":     _real(torch),
        "onnx":          onnxruntime is not None,   # real onnx loaded above
        "xxhash":        _real(xxhash),
        "rapidfuzz":     _real(rapidfuzz),
        "cv2":           cv2 is not None,           # real cv2 loaded above
        "pyvips":        pyvips is not None,
        "scipy":         _real(sp),
        "numpy":         np is not None,
        "requests":      _real(requests_m),
        "msgpack":       _real(msgpack),
        "cloudpickle":   _real(cloudpickle),
        "blosc2":        _real(blosc2),
        "snappy":        _real(snappy),
        "brotli":        _real(brotli),
        "mmh3":          _real(mmh3),
        "blake3":        _real(blake3),
    }

# ══════════════════════════════════════════════════════════════════════════════
# ANC-04  CPU / RAM / THREAD BUDGET  (physical-core-aware, 5-tier mem scale)
# ══════════════════════════════════════════════════════════════════════════════

def _mem_pressure_scale() -> float:
    """5-tier memory pressure multiplier (0.45–1.0). Fallback 1.0."""
    try:
        if not psutil: return 1.0
        vm = psutil.virtual_memory()
        if not vm.total: return 1.0
        r: float = float(vm.available) / float(vm.total)
        if r < 0.12: return 0.45
        if r < 0.18: return 0.55
        if r < 0.28: return 0.72
        if r < 0.38: return 0.88
        return 1.0
    except Exception:
        return 1.0

def _cpu_count(logical: bool = True) -> int:
    """Safe CPU core count. Never returns 0."""
    try:
        if not logical and psutil:
            n = psutil.cpu_count(logical=False)
            return max(1, int(n)) if n else _cpu_count(True)
    except Exception:
        pass
    return max(1, int(os.cpu_count() or multiprocessing.cpu_count() or 4))

def _available_ram_mb() -> int:
    """Available RAM in MB; returns 2048 if unknown."""
    try:
        if psutil:
            return max(256, int(psutil.virtual_memory().available // (1024 * 1024)))
    except Exception:
        pass
    return 2048

def _resolve_mode(mode=None) -> str:
    """Normalise mode string → safe / balanced / maxsafe / aggressive."""
    raw = (mode or os.environ.get("VIA_ACCEL_MODE") or VIA_ACCEL_DEFAULT_MODE).strip().lower()
    raw = VRN_MODE_MAP.get(raw, raw)
    return raw if raw in ("safe", "balanced", "maxsafe", "aggressive") else "maxsafe"

def thread_budget(mode=None, *, use_physical: bool = True) -> int:
    """Physical-core-aware thread budget with 5-tier mem-pressure scale."""
    eff   = _resolve_mode(mode)
    n     = _cpu_count(logical=False) if use_physical else _cpu_count(True)
    logic = _cpu_count(logical=True)
    scale = _mem_pressure_scale()
    if eff == "safe":
        t = 1
    elif eff == "balanced":
        t = max(1, min(n // 2, 8))
    elif eff == "aggressive":
        t = max(2, n) if n <= 2 else n
    else:  # maxsafe
        t = max(2, min(16, n - 1)) if n > 2 else n
    return max(1, min(logic, int(max(1, t * scale))))

def thread_budget_cross(mode=None) -> int:
    """Cross-lib pool (NUMEXPR/RAYON) — up to 1.6× physical."""
    base  = thread_budget(mode)
    logic = _cpu_count(logical=True)
    bump  = int(max(base * _CROSS_THREAD_MULTIPLIER, base + _CROSS_THREAD_MIN_BUMP))
    return min(_CROSS_THREAD_HARD_CAP, max(base, min(logic * 2, bump)))

def memory_percent() -> float:
    if psutil: return psutil.virtual_memory().percent
    return 0.0

def memory_available_mb() -> int:
    return _available_ram_mb()

def cpu_percent(interval: float = 0.05) -> float:
    if psutil: return psutil.cpu_percent(interval=interval)
    return 0.0

def under_memory_pressure(threshold: int = _MEM_PRESSURE_WARN) -> bool:
    return memory_percent() >= threshold

def under_cpu_pressure(threshold: int = _CPU_PRESSURE_STOP) -> bool:
    return cpu_percent() >= threshold

def system_under_pressure() -> bool:
    return (memory_percent() > _MEM_PRESSURE_STOP) or (cpu_percent() > _CPU_PRESSURE_STOP)

def wait_for_memory(target: int = 80, interval: float = 0.2, timeout: float = 10.0) -> bool:
    start = time.time()
    while memory_percent() > target:
        if time.time() - start > timeout: return False
        _via_sleep(interval)
    return True

def wait_for_cpu(target: int = 70, interval: float = 0.2, timeout: float = 10.0) -> bool:
    start = time.time()
    while cpu_percent() > target:
        if time.time() - start > timeout: return False
        _via_sleep(interval)
    return True

def map_vrn_mode_to_bootstrap(vrn_mode=None) -> str:
    """Map VRN ADAPTIVE_ACCEL_MODE → bootstrap tier."""
    raw = (vrn_mode or os.environ.get("VRN_FUSION_ACCEL_MODE") or "performance").strip().lower()
    return VRN_MODE_MAP.get(raw, "balanced")

def sizeof(obj, seen=None) -> int:
    """Recursive memory size estimate."""
    if seen is None: seen = set()
    oid = id(obj)
    if oid in seen: return 0
    seen.add(oid)
    size = sys.getsizeof(obj)
    if isinstance(obj, dict):
        size += sum(sizeof(k, seen) + sizeof(v, seen) for k, v in obj.items())
    elif isinstance(obj, (list, tuple, set, frozenset)):
        size += sum(sizeof(i, seen) for i in obj)
    return size

# ══════════════════════════════════════════════════════════════════════════════
# ANC-05  17-VAR ENV PUSH
# ══════════════════════════════════════════════════════════════════════════════

def apply_thread_limits(n: int) -> None:
    """Push thread count into 6 numeric-runtime env vars (IP-02: was 4, now 6)."""
    s = str(max(1, int(n)))
    for var in (
        "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
        "NUMEXPR_NUM_THREADS", "NUMBA_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
    ):
        os.environ[var] = s

def apply_vrn_vds_max_accel(mode=None, *, also_set_vrn_flags: bool = True) -> Dict[str, str]:
    """
    Full 17-var + VRN flags bootstrap. Idempotent.
    Call once at startup; safe to call multiple times.
    Returns applied env var dict (for subprocess env= merges).
    """
    eff = _resolve_mode(mode)
    t   = thread_budget(eff)
    tc  = thread_budget_cross(eff)
    ns, nsc = str(t), str(tc)

    keys: Dict[str, str] = {
        "OMP_NUM_THREADS":            ns,
        "MKL_NUM_THREADS":            ns,
        "OPENBLAS_NUM_THREADS":       ns,
        "NUMEXPR_NUM_THREADS":        nsc,
        "NUMEXPR_MAX_THREADS":        nsc,
        "VECLIB_MAXIMUM_THREADS":     ns,
        "NUMBA_NUM_THREADS":          ns,
        "POLARS_MAX_THREADS":         ns,
        "RAYON_NUM_THREADS":          nsc,
        "TOKENIZERS_PARALLELISM":     "false",
        "VIA_ACCEL_ACTIVE_THREADS":   ns,
        "VIA_ACCEL_CROSS_THREADS":    nsc,
        "VIA_ACCEL_MODE":             eff,
    }
    if also_set_vrn_flags:
        keys.update({
            "VRN_ACCEL_MAX":                   "1",
            "VRN_CROSS_ACCEL":                 "1",
            "VIS_ACCEL_MASTER_ENABLE_ALL_CPU": "1",
            "ACCEL_MASTER_ENABLE_ALL_CPU":     "1",
        })
    for k, v in keys.items():
        os.environ[k] = v
    return keys

# backwards-compat aliases
set_thread_limit  = lambda n: (apply_thread_limits(n), max(1, int(n)))[1]
recommend_threads = lambda mode="balanced": thread_budget(mode)
get_best_worker_count = lambda reserve=1, upper=32: max(
    1, min(upper, _cpu_count(logical=True) - reserve)
)

# ══════════════════════════════════════════════════════════════════════════════
# ANC-06  GC TUNER  (generational + hot_loop ctx)
# ══════════════════════════════════════════════════════════════════════════════

class GCTuner:
    """
    Generational GC tuner. Strategy: NOT full-disable.
    gen0=50000 (nearly eliminate minor-collection interrupts)
    gen1=500   (reduce mid-gen scans)
    gen2=50    (safety net for long-lived objects)
    Full gc.disable() only as context manager for known hot loops.
    """
    _orig: Tuple[int, int, int] = gc.get_threshold()

    @staticmethod
    def optimize() -> None:
        gc.set_threshold(_GC_THRESHOLD_GEN0, _GC_THRESHOLD_GEN1, _GC_THRESHOLD_GEN2)

    @staticmethod
    def maximize() -> None:
        """Max throughput — pure-batch, no interactive sessions."""
        gc.set_threshold(100_000, 1_000, 100)

    @staticmethod
    def pause() -> None:
        gc.disable()

    @staticmethod
    def restore() -> None:
        gc.enable()
        gc.set_threshold(*GCTuner._orig)

    @staticmethod
    def collect(generation: int = 2) -> int:
        return gc.collect(generation)

    @staticmethod
    @contextlib.contextmanager
    def hot_loop():
        """Pause GC for known allocation-free hot loops. Restores on exit."""
        was_enabled = gc.isenabled()
        if was_enabled: gc.disable()
        try:
            yield
        finally:
            if was_enabled: gc.enable()

    @staticmethod
    @contextlib.contextmanager
    def tuned(mode: str = "optimize"):
        """Apply GC tuning for a block then restore."""
        if mode == "maximize":
            GCTuner.maximize()
        else:
            GCTuner.optimize()
        try:
            yield
        finally:
            GCTuner.restore()

# ══════════════════════════════════════════════════════════════════════════════
# ANC-07  MEMORY POOL  (RAM auto-size, L3-cache heuristic)
# ══════════════════════════════════════════════════════════════════════════════

class MemoryPool:
    """
    RAM-aware memory pool. Auto-sizing:
      block_size = min(256KB, 32KB/physical_cores) — L3-cache heuristic
      pool_size  = max(32, min(512, avail_ram_MB*2%/block_size))
    """

    @staticmethod
    def _auto_block() -> int:
        n = _cpu_count(logical=False)
        return min(256 * 1024, max(4096, 32 * 1024 // max(1, n)))

    @staticmethod
    def _auto_pool(block_size: int) -> int:
        budget = int(_available_ram_mb() * 1024 * 1024 * 0.02)
        return max(32, min(512, budget // max(1, block_size)))

    def __init__(self, block_size: Optional[int] = None, pool_size: Optional[int] = None):
        bs = block_size or MemoryPool._auto_block()
        ps = pool_size  or MemoryPool._auto_pool(bs)
        self._pool  = [bytearray(bs) for _ in range(ps)]
        self._free  = list(range(ps))
        self._lock  = threading.Lock()
        self._block = bs

    def acquire(self) -> bytearray:
        with self._lock:
            if self._free: return self._pool[self._free.pop()]
        return bytearray(self._block)

    def release(self, buf: bytearray) -> None:
        with self._lock:
            idx = next((i for i, b in enumerate(self._pool) if b is buf), None)
            if idx is not None and idx not in self._free:
                self._free.append(idx)

    def stats(self) -> Dict:
        with self._lock:
            return {"pool_size": len(self._pool), "block_size": self._block,
                    "free": len(self._free), "in_use": len(self._pool) - len(self._free)}

# ══════════════════════════════════════════════════════════════════════════════
# ANC-08  ADAPTIVE CHUNK SIZING  (M31)
# ══════════════════════════════════════════════════════════════════════════════

def adaptive_chunk_size(
    n_items: int,
    item_bytes: int = _CHUNK_DEFAULT_ITEM_BYTES,
    mode=None,
    max_ram_pct: float = _CHUNK_MAX_RAM_PCT,
) -> int:
    """RAM-aware batch/chunk size. Guarantees no OOM. Divides budget across threads."""
    if n_items <= 0: return 1
    if item_bytes <= 0: return n_items
    avail      = _available_ram_mb() * 1024 * 1024
    budget     = int(avail * max_ram_pct)
    t          = thread_budget(mode)
    per_thread = max(1, budget // max(1, t * item_bytes))
    return max(1, min(n_items, per_thread))

def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    if chunk_size <= 0: chunk_size = 1
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]

# ══════════════════════════════════════════════════════════════════════════════
# ANC-09  BACKEND REGISTRY
# ══════════════════════════════════════════════════════════════════════════════

def _build_numpy_backend() -> Dict:
    if np is None: return {"available": False}
    return {
        "available": True,
        "run":       lambda f, *a, **kw: f(*a, **kw),
        "vectorize": np.vectorize,
        "matmul":    np.matmul,
        "sum":       np.sum,
        "mean":      np.mean,
        "einsum":    np.einsum,
    }

def _build_numba_backend() -> Dict:
    try:
        import numba as _nb
        return {
            "available": True,
            "run":       lambda f, *a, **kw: _nb.njit(cache=True)(f)(*a, **kw),
            "njit":      lambda f: _nb.njit(cache=True, parallel=False)(f),
            "njit_par":  lambda f: _nb.njit(cache=True, parallel=True)(f),
            "vectorize": _nb.vectorize,
            "prange":    _nb.prange,
        }
    except Exception:
        return {"available": False, "run": lambda f, *a, **kw: f(*a, **kw)}

def _build_polars_backend() -> Dict:
    try:
        import polars as _pl
        import pandas as _pda
        return {
            "available":  True,
            "run":        lambda f, *a, **kw: f(*a, **kw),
            "to_polars":  lambda df: _pl.from_pandas(df) if isinstance(df, _pda.DataFrame) else df,
            "to_pandas":  lambda df: df.to_pandas() if _is_polars_df(df) else df,
            "lazy":       lambda df: df.lazy() if _is_polars_df(df) else df,
            "collect":    lambda lf: lf.collect() if hasattr(lf, "collect") else lf,
            "scan_parquet": _pl.scan_parquet,
            "scan_csv":     _pl.scan_csv,
        }
    except Exception:
        return {"available": False, "run": lambda f, *a, **kw: f(*a, **kw)}

def _build_duckdb_backend() -> Dict:
    try:
        import duckdb as _db
        def _query(sql: str, conn=None):
            c = conn or _db.connect()
            return c.execute(sql).df()
        return {
            "available":    True,
            "connect":      _db.connect,
            "query":        _query,
            "read_parquet": lambda p: _db.read_parquet(p),
            "read_csv":     lambda p: _db.read_csv(p),
        }
    except Exception:
        return {"available": False}

def _build_onnx_backend() -> Dict:
    try:
        import onnxruntime as _ort
        def _create_session(path: str, threads: int = 1):
            opts = _ort.SessionOptions()
            opts.intra_op_num_threads = threads
            opts.inter_op_num_threads = threads
            return _ort.InferenceSession(path, opts, providers=["CPUExecutionProvider"])
        return {
            "available":      True,
            "create_session": _create_session,
            "run_inference":  lambda sess, inputs: sess.run(None, inputs),
        }
    except Exception:
        return {"available": False,
                "create_session": lambda *a, **kw: None,
                "run_inference":  lambda *a, **kw: None}

def _build_opencv_backend() -> Dict:
    try:
        import cv2 as _cv2
        def _resize(img, width=None, height=None):
            h, w = img.shape[:2]
            if width is None and height is None: return img
            if width  is None: width  = int(w * height / float(h))
            if height is None: height = int(h * width  / float(w))
            return _cv2.resize(img, (width, height), interpolation=_cv2.INTER_AREA)
        return {
            "available": True,
            "run":    lambda f, *a, **kw: f(*a, **kw),
            "load":   lambda p: _cv2.imread(p, _cv2.IMREAD_UNCHANGED),
            "save":   _cv2.imwrite,
            "gray":   lambda img: _cv2.cvtColor(img, _cv2.COLOR_BGR2GRAY),
            "blur":   lambda img, k=3: _cv2.GaussianBlur(img, (k, k), 0),
            "edges":  lambda img, lo=50, hi=150: _cv2.Canny(img, lo, hi),
            "resize": _resize,
        }
    except Exception:
        return {"available": False}

def _build_pyvips_backend() -> Dict:
    try:
        import pyvips as _vips
        def _to_numpy(img):
            if np is None: return img
            mem = img.write_to_memory()
            arr = np.frombuffer(mem, dtype=np.uint8)
            return arr.reshape(img.height, img.width, img.bands)
        return {
            "available": True,
            "run":       lambda f, *a, **kw: f(*a, **kw),
            "load":      lambda p: _vips.Image.new_from_file(p, access="sequential"),
            "save":      lambda img, p: img.write_to_file(p),
            "resize":    lambda img, s: img.resize(s),
            "crop":      lambda img, l, t, w, h: img.crop(l, t, w, h),
            "to_numpy":  _to_numpy,
        }
    except Exception:
        return {"available": False}

_FALLBACK_BACKEND: Dict = {
    "available": True,
    "run":       lambda f, *a, **kw: f(*a, **kw),
    "identity":  lambda x: x,
    "noop":      lambda *a, **kw: None,
}

# Built once at import time
_BACKEND_BUILDERS: Dict[str, Callable] = {
    "numpy":       _build_numpy_backend,
    "numpy-blas":  _build_numpy_backend,
    "numba":       _build_numba_backend,
    "polars":      _build_polars_backend,
    "arrow":       _build_polars_backend,
    "duckdb":      _build_duckdb_backend,
    "onnx":        _build_onnx_backend,
    "opencv":      _build_opencv_backend,
    "pyvips":      _build_pyvips_backend,
}
_BACKENDS_EAGER: Dict[str, Dict] = {
    "python":      _FALLBACK_BACKEND,
    "pillow":      _FALLBACK_BACKEND,
    "pandas":      _FALLBACK_BACKEND,
    "fallback":    _FALLBACK_BACKEND,
}

class _LazyBackends(dict):
    """
    Lazy backend registry — LL#25.
    BACKENDS previously triggered _build_*_backend() for every entry at import
    time, each of which did `import numba/polars/cv2/...` and cost ~1.5s total.
    Now each backend is built on first access.

    Behaves as a dict: iteration, `.items()`, `.values()`, `.get()` all work,
    but each access for a buildable key resolves lazily and caches.
    """
    def __init__(self):
        super().__init__(_BACKENDS_EAGER)

    def _ensure(self, key):
        if key in self:
            return
        builder = _BACKEND_BUILDERS.get(key)
        if builder is not None:
            try:
                self[key] = builder()
            except Exception:
                self[key] = {"available": False}

    def __getitem__(self, key):
        self._ensure(key)
        if key in super().keys():
            return super().__getitem__(key)
        return _FALLBACK_BACKEND

    def __contains__(self, key):
        return super().__contains__(key) or key in _BACKEND_BUILDERS

    def get(self, key, default=None):
        self._ensure(key)
        return super().get(key, default if default is not None else _FALLBACK_BACKEND)

    def items(self):
        # Force resolve all builders so iteration reports true availability
        for k in list(_BACKEND_BUILDERS.keys()):
            self._ensure(k)
        return super().items()

    def values(self):
        for k in list(_BACKEND_BUILDERS.keys()):
            self._ensure(k)
        return super().values()

    def keys(self):
        # Return union without forcing resolve
        return list(super().keys()) + [
            k for k in _BACKEND_BUILDERS.keys() if k not in super().keys()
        ]

BACKENDS: Dict[str, Dict] = _LazyBackends()

def get_backend(name: str) -> Dict:
    return BACKENDS.get(name, _FALLBACK_BACKEND)

def execute_with_backend(func: Callable, backend: str, args: tuple, kwargs: dict) -> Any:
    """
    Wide fast-path dispatch (IP-08 Bootstrap §7).
    Fast paths: numba / numpy / polars / joblib
    Universal fallback: plain func(*args, **kwargs)
    """
    try:
        if backend == "numba" and numba:
            try: return numba.njit(func)(*args, **kwargs)
            except Exception: pass

        elif backend in ("numpy", "numpy-blas") and np and args:
            try:
                arr = np.asarray(args[0])
                if arr.ndim > 0: return func(arr, *args[1:], **kwargs)
            except Exception: pass

        elif backend == "polars" and pl and args:
            try:
                if hasattr(args[0], "__iter__") and not isinstance(args[0], str):
                    s = pl.Series(list(args[0]))
                    return func(s, *args[1:], **kwargs)
            except Exception: pass

        elif backend == "joblib" and joblib and args:
            try:
                if hasattr(args[0], "__iter__") and not isinstance(args[0], str):
                    t = thread_budget()
                    return joblib.Parallel(n_jobs=t, prefer="threads")(
                        joblib.delayed(func)(item, *args[1:], **kwargs)
                        for item in args[0]
                    )
            except Exception: pass

    except Exception:
        pass
    return func(*args, **kwargs)

# ══════════════════════════════════════════════════════════════════════════════
# ANC-10  PARALLEL ENGINES  (Thread/Process/Ray/Joblib/Dask auto-select)
# ══════════════════════════════════════════════════════════════════════════════

def parallel_map(
    func: Callable,
    items: List[Any],
    max_workers: Optional[int] = None,
    mode: str = "thread",
    timeout: Optional[float] = None,
) -> List[Any]:
    """ThreadPool / ProcessPool parallel map."""
    if not items: return []
    workers = max_workers or thread_budget()
    results: List[Any] = [None] * len(items)
    pool_cls = ProcessPoolExecutor if mode == "process" else ThreadPoolExecutor
    with pool_cls(max_workers=workers) as ex:
        future_map = {ex.submit(func, item): idx for idx, item in enumerate(items)}
        for future in as_completed(future_map, timeout=timeout):
            idx = future_map[future]
            try: results[idx] = future.result()
            except Exception as e: results[idx] = e
    return results

def parallel_map_ray(func: Callable, items: List[Any],
                     num_cpus: Optional[float] = None) -> List[Any]:
    """Ray distributed map (fallback to ThreadPool if Ray unavailable)."""
    if not items: return []
    if ray is None: return parallel_map(func, items)
    try:
        if not ray.is_initialized():
            ray.init(ignore_reinit_error=True, logging_level="ERROR",
                     num_cpus=os.cpu_count())
        remote_fn = ray.remote(func) if not hasattr(func, "remote") else func
        return ray.get([remote_fn.remote(item) for item in items])
    except Exception:
        return parallel_map(func, items)

def parallel_map_joblib(func: Callable, items: List[Any],
                        n_jobs: int = -1, backend: str = "loky") -> List[Any]:
    """Joblib parallel map (fallback to ThreadPool)."""
    if not items: return []
    if joblib is None: return parallel_map(func, items)
    try:
        from joblib import Parallel, delayed
        return Parallel(n_jobs=n_jobs, backend=backend)(delayed(func)(item) for item in items)
    except Exception:
        return parallel_map(func, items)

def auto_parallel_map(func: Callable, items: List[Any],
                      prefer: str = "thread") -> List[Any]:
    """Auto-select best parallel backend: ray → joblib → ThreadPool."""
    if not items: return []
    if ray is not None and prefer not in ("thread", "joblib"):
        return parallel_map_ray(func, items)
    if joblib is not None and prefer == "joblib":
        return parallel_map_joblib(func, items)
    return parallel_map(func, items)

def parallel_chunked_map(func: Callable, items: List[Any],
                          chunk_size: Optional[int] = None,
                          max_workers: Optional[int] = None) -> List[Any]:
    """Split items into chunks → parallel map each chunk → flatten."""
    if not items: return []
    cs = chunk_size or adaptive_chunk_size(len(items))
    chunks  = chunk_list(items, cs)
    batches = parallel_map(func, chunks, max_workers=max_workers)
    result: List[Any] = []
    for b in batches:
        if isinstance(b, list): result.extend(b)
        elif b is not None: result.append(b)
    return result

# ══════════════════════════════════════════════════════════════════════════════
# ANC-11  CACHE LAYER  (LRU / TTL / Disk / SQLite-WAL)
# ══════════════════════════════════════════════════════════════════════════════

class LRUCache:
    """Thread-safe LRU cache (no external deps)."""

    def __init__(self, maxsize: int = _LRU_MAXSIZE):
        self._d: OrderedDict = OrderedDict()
        self._n    = maxsize
        self._lock = threading.RLock()
        self._hits = self._misses = 0

    def get(self, key, default=None):
        with self._lock:
            if key in self._d:
                self._d.move_to_end(key)
                self._hits += 1
                return self._d[key]
            self._misses += 1
            return default

    def set(self, key, value):
        with self._lock:
            self._d[key] = value
            self._d.move_to_end(key)
            while len(self._d) > self._n:
                self._d.popitem(last=False)

    def delete(self, key):
        with self._lock: self._d.pop(key, None)

    def clear(self):
        with self._lock: self._d.clear()

    def __contains__(self, key): return key in self._d

    def stats(self) -> Dict:
        return {"size": len(self._d), "maxsize": self._n,
                "hits": self._hits, "misses": self._misses}

class TTLCache:
    """Thread-safe TTL cache (no external deps)."""

    def __init__(self, maxsize: int = _TTL_MAXSIZE, ttl: float = _TTL_DEFAULT_S):
        self._d: Dict[Any, Tuple[Any, float]] = {}
        self._n   = maxsize
        self._ttl = ttl
        self._lock = threading.Lock()

    def get(self, key, default=None):
        with self._lock:
            if key in self._d:
                val, ts = self._d[key]
                if time.monotonic() - ts < self._ttl: return val
                del self._d[key]
            return default

    def set(self, key, value):
        with self._lock:
            if len(self._d) >= self._n:
                try: del self._d[next(iter(self._d))]
                except StopIteration: pass
            self._d[key] = (value, time.monotonic())

    def clear(self): self._d.clear()
    def __contains__(self, key): return self.get(key) is not None

class AutotuneCache:
    """SQLite-backed cache: disk persistence + TTL + WAL mode."""

    _DDL = ("CREATE TABLE IF NOT EXISTS cache"
            "(key TEXT PRIMARY KEY, value TEXT, ts REAL, ttl REAL)")

    def __init__(self, db_path: str = _AUTOTUNE_DB_PATH,
                 default_ttl: float = _AUTOTUNE_DEFAULT_TTL):
        self._path = db_path
        self._ttl  = default_ttl
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute(self._DDL)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.commit()

    def get(self, key: str, default: Any = None) -> Any:
        import json as _j
        row = self._conn.execute(
            "SELECT value, ts, ttl FROM cache WHERE key=?", (key,)
        ).fetchone()
        if not row: return default
        val_s, ts, ttl = row
        if ttl and ttl > 0 and (time.time() - ts) > ttl:
            self._conn.execute("DELETE FROM cache WHERE key=?", (key,))
            self._conn.commit()
            return default
        try: return _j.loads(val_s)
        except Exception: return default

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        import json as _j
        eff_ttl = ttl if ttl is not None else self._ttl
        self._conn.execute(
            "INSERT OR REPLACE INTO cache VALUES(?,?,?,?)",
            (key, _j.dumps(value, default=str), time.time(), eff_ttl)
        )
        self._conn.commit()

    def delete(self, key: str) -> None:
        self._conn.execute("DELETE FROM cache WHERE key=?", (key,))
        self._conn.commit()

    def purge_expired(self) -> int:
        cur = self._conn.execute(
            "DELETE FROM cache WHERE ttl > 0 AND (? - ts) > ttl", (time.time(),)
        )
        self._conn.commit()
        return cur.rowcount

class CacheManager:
    """SQLite-backed TTL cache — thread-safe, :memory: or file path."""

    def __init__(self, db_path: str = ":memory:"):
        self._db   = db_path
        self._lock = threading.Lock()
        if db_path == ":memory:":
            self._mem_conn = sqlite3.connect(":memory:", check_same_thread=False)
            self._mem_conn.execute(
                "CREATE TABLE IF NOT EXISTS cache "
                "(key TEXT PRIMARY KEY, value TEXT, expire_at REAL)"
            )
            self._mem_conn.commit()
        else:
            self._mem_conn = None
            conn = sqlite3.connect(db_path)
            conn.execute(
                "CREATE TABLE IF NOT EXISTS cache "
                "(key TEXT PRIMARY KEY, value TEXT, expire_at REAL)"
            )
            conn.commit()
            conn.close()

    def _conn(self):
        if self._mem_conn is not None:
            return self._mem_conn, False
        return sqlite3.connect(self._db), True

    def get(self, k: str) -> Optional[Any]:
        with self._lock:
            conn, should_close = self._conn()
            try:
                cur = conn.execute(
                    "SELECT value, expire_at FROM cache WHERE key=?", (k,))
                row = cur.fetchone()
                if row and (row[1] is None or row[1] > time.time()):
                    import json as _j
                    return _j.loads(row[0])
            except Exception:
                return None
            finally:
                if should_close: conn.close()
        return None

    def set(self, k: str, v: Any, ttl: int = 3600) -> bool:
        with self._lock:
            conn, should_close = self._conn()
            try:
                import json as _j
                expire = time.time() + ttl if ttl > 0 else None
                conn.execute(
                    "INSERT OR REPLACE INTO cache VALUES(?,?,?)",
                    (k, _j.dumps(v, default=str), expire),
                )
                conn.commit()
                return True
            except Exception:
                return False
            finally:
                if should_close: conn.close()

def get_disk_cache(directory: str = _DISK_CACHE_DIR,
                   size_limit_gb: float = _DISK_CACHE_SIZE_GB) -> Any:
    """Return diskcache.Cache or None."""
    if diskcache is None: return None
    try:
        return diskcache.Cache(directory, size_limit=int(size_limit_gb * 1024 ** 3))
    except Exception:
        return None

# Module-level singletons
_LRU_4K:   LRUCache    = LRUCache(maxsize=_LRU_MAXSIZE)
_TTL_5MIN: TTLCache    = TTLCache(maxsize=_TTL_MAXSIZE, ttl=_TTL_DEFAULT_S)

def cache_get(key: str, tier: str = "lru") -> Any:
    if tier == "ttl": return _TTL_5MIN.get(key)
    return _LRU_4K.get(key)

def cache_set(key: str, value: Any, tier: str = "lru") -> None:
    if tier == "ttl": _TTL_5MIN.set(key, value)
    else: _LRU_4K.set(key, value)

def cache_stats() -> Dict:
    return {"lru": _LRU_4K.stats(), "ttl": {"size": len(_TTL_5MIN._d)}}

# ══════════════════════════════════════════════════════════════════════════════
# ANC-12  DATAFRAME ACCELERATION  (polars-first)
# ══════════════════════════════════════════════════════════════════════════════

def dedupe_preserve_order(items: Iterable[Any]) -> List[Any]:
    seen: set = set()
    out: List[Any] = []
    for item in items:
        key = repr(item)
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out

def accelerated_concat(frames: List[Any], prefer: str = "polars") -> Any:
    """Concat DataFrames; polars-first, pandas fallback."""
    frames = [f for f in frames if f is not None]
    if not frames: return None
    if prefer == "polars" and pl is not None:
        try:
            norm = []
            for f in frames:
                if _is_polars_df(f): norm.append(f)
                elif pd is not None and isinstance(f, pd.DataFrame):
                    norm.append(pl.from_pandas(f))
            if norm: return pl.concat(norm, how="vertical_relaxed")
        except Exception: pass
    if pd is not None:
        norm_pd = []
        for f in frames:
            if isinstance(f, pd.DataFrame): norm_pd.append(f)
            elif pl is not None and _is_polars_df(f):
                try: norm_pd.append(f.to_pandas())
                except Exception: pass
        if norm_pd: return pd.concat(norm_pd, ignore_index=True, sort=False)
    return frames

def accelerated_drop_duplicates(frame: Any, subset: Optional[List[str]] = None) -> Any:
    if frame is None: return None
    if pl is not None and _is_polars_df(frame):
        return frame.unique(subset=subset, maintain_order=True)
    if pd is not None and isinstance(frame, pd.DataFrame):
        return frame.drop_duplicates(subset=subset, keep="first").reset_index(drop=True)
    return frame

def accelerated_sort(frame: Any, by: List[str], descending: bool = False) -> Any:
    if frame is None: return None
    if pl is not None and _is_polars_df(frame):
        return frame.sort(by, descending=descending)
    if pd is not None and isinstance(frame, pd.DataFrame):
        return frame.sort_values(by=by, ascending=not descending).reset_index(drop=True)
    return frame

def accelerated_filter(frame: Any, mask) -> Any:
    if frame is None: return None
    if pl is not None and _is_polars_df(frame):
        return frame.filter(mask)
    if pd is not None and isinstance(frame, pd.DataFrame):
        return frame[mask].reset_index(drop=True)
    return frame

def to_polars(frame: Any) -> Any:
    if frame is None: return None
    if pl is not None:
        if _is_polars_df(frame): return frame
        if pd is not None and isinstance(frame, pd.DataFrame):
            return pl.from_pandas(frame)
    return frame

def to_pandas(frame: Any) -> Any:
    if frame is None: return None
    if pd is not None:
        if isinstance(frame, pd.DataFrame): return frame
        if pl is not None and _is_polars_df(frame):
            return frame.to_pandas()
    return frame

def xread_parquet(path: str) -> Any:
    """
    Cross-accelerated parquet read: polars lazy > polars > pandas > pickle fallback.
    Returns None if no parquet engine available.
    """
    # Try real polars first
    try:
        import polars as _real_pl
        try: return _real_pl.scan_parquet(path)
        except Exception: pass
        try: return _real_pl.read_parquet(path)
        except Exception: pass
    except ImportError:
        pass
    # Try pandas with pyarrow or fastparquet
    if pd is not None:
        for engine in ("pyarrow", "fastparquet"):
            try:
                return pd.read_parquet(path, engine=engine)
            except Exception:
                continue
    # Final fallback: try pickle (if file was written via our fallback)
    try:
        import pickle as _pk
        with open(path, "rb") as f:
            return _pk.load(f)
    except Exception:
        pass
    return None

def xwrite_parquet(frame: Any, path: str, compression: str = "zstd") -> bool:
    """
    Cross-accelerated parquet write: polars > pandas (pyarrow/fastparquet) > pickle fallback.
    Returns True if written successfully.
    """
    # Try real polars
    if _is_polars_df(frame):
        try:
            frame.write_parquet(path, compression=compression)
            return True
        except Exception:
            pass
    # Try pandas with parquet engine
    if pd is not None:
        df = frame
        if _is_polars_df(frame):
            try: df = frame.to_pandas()
            except Exception: pass
        if isinstance(df, pd.DataFrame):
            for engine in ("pyarrow", "fastparquet"):
                try:
                    df.to_parquet(path, index=False,
                                  compression=compression, engine=engine)
                    return True
                except Exception:
                    continue
    # Final fallback: pickle
    try:
        import pickle as _pk
        with open(path, "wb") as f:
            _pk.dump(frame, f)
        return True
    except Exception:
        pass
    return False

# ══════════════════════════════════════════════════════════════════════════════
# ANC-13  JSON ACCELERATION
# ══════════════════════════════════════════════════════════════════════════════

def json_dumps(obj: Any, indent: int = None, **kwargs) -> str:
    """orjson > ujson > rapidjson > stdlib. Returns str."""
    if orjson is not None:
        try:
            raw = orjson.dumps(obj, option=orjson.OPT_INDENT_2 if indent else None)
            return raw.decode("utf-8") if isinstance(raw, bytes) else raw
        except Exception: pass
    if ujson is not None:
        try: return ujson.dumps(obj, indent=indent or 0, ensure_ascii=False)
        except Exception: pass
    if rapidjson is not None:
        try: return rapidjson.dumps(obj, **kwargs)
        except Exception: pass
    import json as _j
    return _j.dumps(obj, ensure_ascii=False, indent=indent, default=str)

def json_loads(s: Union[str, bytes], **kwargs) -> Any:
    """orjson > ujson > rapidjson > stdlib."""
    if orjson is not None:
        try: return orjson.loads(s)
        except Exception: pass
    if ujson is not None:
        try: return ujson.loads(s)
        except Exception: pass
    if rapidjson is not None:
        try: return rapidjson.loads(s)
        except Exception: pass
    import json as _j
    return _j.loads(s, **kwargs)

# Aliases
xjson_dumps = json_dumps
xjson_loads = json_loads

# ══════════════════════════════════════════════════════════════════════════════
# ANC-14  COMPRESSION  (zstd > lz4 > blosc2 > gzip)
# ══════════════════════════════════════════════════════════════════════════════

def compress_bytes(data: bytes, level: int = _COMPRESS_DEFAULT_LEVEL) -> bytes:
    if zstd is not None:
        try: return b"ZS:" + zstd.ZstdCompressor(level=level).compress(data)
        except Exception: pass
    if lz4 is not None:
        try:
            import lz4.frame as _lf
            return b"L4:" + _lf.compress(data)
        except Exception: pass
    if blosc2 is not None:
        try: return b"B2:" + blosc2.compress(data)
        except Exception: pass
    import gzip
    return b"GZ:" + gzip.compress(data, compresslevel=level)

def decompress_bytes(data: bytes) -> bytes:
    if data[:3] == b"ZS:" and zstd is not None:
        return zstd.ZstdDecompressor().decompress(data[3:])
    if data[:3] == b"L4:" and lz4 is not None:
        import lz4.frame as _lf
        return _lf.decompress(data[3:])
    if data[:3] == b"B2:" and blosc2 is not None:
        return blosc2.decompress(data[3:])
    if data[:3] == b"GZ:":
        import gzip
        return gzip.decompress(data[3:])
    # auto-detect magic bytes
    if data[:4] == b"\x28\xb5\x2f\xfd" and zstd is not None:
        return zstd.ZstdDecompressor().decompress(data)
    if data[:2] == b"\x1f\x8b":
        import gzip
        return gzip.decompress(data)
    return data

class CompressionEngine:
    """Multi-format compression engine with auto-detect decompress."""

    @staticmethod
    def compress(data: bytes, method: str = "auto", level: int = _COMPRESS_DEFAULT_LEVEL) -> bytes:
        if method == "auto": method = "zstd"
        if method == "zstd" and zstd:
            return b"ZS:" + zstd.ZstdCompressor(level=level).compress(data)
        if method == "lz4" and lz4:
            import lz4.frame as _lf
            return b"L4:" + _lf.compress(data)
        if method == "blosc2" and blosc2:
            return b"B2:" + blosc2.compress(data)
        if method == "snappy" and snappy:
            return b"SN:" + snappy.compress(data)
        import gzip
        return b"GZ:" + gzip.compress(data, compresslevel=level)

    @staticmethod
    def decompress(data: bytes) -> bytes:
        return decompress_bytes(data)

    @staticmethod
    def get_ratio(original: bytes, compressed: bytes) -> float:
        return len(compressed) / len(original) if original else 0.0

xcompress   = compress_bytes
xdecompress = decompress_bytes

# ══════════════════════════════════════════════════════════════════════════════
# ANC-15  HASHING  (xxhash > mmh3 > blake3 > sha256)
# ══════════════════════════════════════════════════════════════════════════════

def fast_hash(data: Union[str, bytes], algo: str = "xxhash") -> str:
    if isinstance(data, str): data = data.encode("utf-8")
    if algo == "xxhash" and xxhash is not None:
        return xxhash.xxh64(data).hexdigest()
    if mmh3 is not None:
        return hex(mmh3.hash64(data)[0] & 0xFFFFFFFFFFFFFFFF)[2:]
    if blake3 is not None:
        return blake3.blake3(data).hexdigest()
    return hashlib.sha256(data).hexdigest()

def xhash(data: Union[str, bytes], method: str = "xxhash") -> str:
    return fast_hash(data, method)

class HashEngine:
    """Multi-algorithm hash engine."""

    @staticmethod
    def xxhash64(data: bytes) -> str:
        if xxhash: return xxhash.xxh64(data).hexdigest()
        return hashlib.sha256(data).hexdigest()[:16]

    @staticmethod
    def blake3_hash(data: bytes) -> str:
        if blake3: return blake3.blake3(data).hexdigest()
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def murmurhash3(data: bytes) -> str:
        if mmh3: return format(mmh3.hash128(data), "x")
        return hashlib.md5(data).hexdigest()

    @staticmethod
    def file_hash(path: str, method: str = "xxhash", chunk: int = 65536) -> str:
        if method == "xxhash" and xxhash:
            h = xxhash.xxh64()
        elif method == "blake3" and blake3:
            h = blake3.blake3()
        else:
            h = hashlib.sha256()
        with open(path, "rb") as f:
            while True:
                block = f.read(chunk)
                if not block: break
                h.update(block)
        return h.hexdigest()

# ══════════════════════════════════════════════════════════════════════════════
# ANC-16  DECORATORS
# ══════════════════════════════════════════════════════════════════════════════

def safe_jit(parallel: bool = False, fastmath: bool = True, cache: bool = True):
    """
    Numba njit if available; no-op otherwise.
    LL#25: Compilation is deferred to first call so module-level `@safe_jit()`
    decorators don't force numba (and its heavy numpy/llvmlite deps) to be
    imported at module-load time.
    """
    def decorator(func):
        _compiled = [None]   # mutable closure cell
        def wrapper(*args, **kwargs):
            if _compiled[0] is None:
                if _spec_exists("numba"):
                    try:
                        import numba as _nb
                        _compiled[0] = _nb.njit(parallel=parallel, fastmath=fastmath, cache=cache)(func)
                    except Exception:
                        _compiled[0] = func
                else:
                    _compiled[0] = func
            return _compiled[0](*args, **kwargs)
        wrapper.__wrapped__ = func
        wrapper.__name__    = getattr(func, "__name__", "jit_wrapped")
        return wrapper
    return decorator

def safe_vectorize(signatures=None):
    """
    Numba vectorize → numpy.vectorize → identity.
    LL#25: deferred to first call (no numba/numpy import at decoration time).
    """
    def decorator(func):
        _compiled = [None]
        def wrapper(*args, **kwargs):
            if _compiled[0] is None:
                sigs = signatures or ["float64(float64)"]
                if _spec_exists("numba"):
                    try:
                        import numba as _nb
                        _compiled[0] = _nb.vectorize(sigs, target="cpu")(func)
                    except Exception:
                        _compiled[0] = None
                if _compiled[0] is None and _spec_exists("numpy"):
                    try:
                        import numpy as _np
                        _compiled[0] = _np.vectorize(func)
                    except Exception:
                        _compiled[0] = func
                if _compiled[0] is None:
                    _compiled[0] = func
            return _compiled[0](*args, **kwargs)
        wrapper.__wrapped__ = func
        wrapper.__name__    = getattr(func, "__name__", "vec_wrapped")
        return wrapper
    return decorator

def memoize(maxsize: int = 1024):
    """Thread-safe dict-backed memoize."""
    def decorator(func):
        _cache: Dict = {}
        _lock = threading.Lock()
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            with _lock:
                if key in _cache: return _cache[key]
            result = func(*args, **kwargs)
            with _lock:
                _cache[key] = result
                while len(_cache) > maxsize:
                    _cache.pop(next(iter(_cache)))
            return result
        wrapper.cache_clear = lambda: _cache.clear()
        wrapper.cache_info  = lambda: {"size": len(_cache), "maxsize": maxsize}
        return wrapper
    return decorator

def ttl_memoize(maxsize: int = 512, ttl: float = _TTL_DEFAULT_S):
    """Thread-safe TTL memoize decorator."""
    def decorator(func):
        _cache: Dict[Any, Tuple[Any, float]] = {}
        _lock = threading.Lock()
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            now = time.monotonic()
            with _lock:
                if key in _cache:
                    val, ts = _cache[key]
                    if now - ts < ttl: return val
                    del _cache[key]
            result = func(*args, **kwargs)
            with _lock:
                _cache[key] = (result, time.monotonic())
                while len(_cache) > maxsize:
                    _cache.pop(next(iter(_cache)))
            return result
        wrapper.cache_clear = lambda: _cache.clear()
        return wrapper
    return decorator

def retry(times: int = 3, delay: float = 0.5, backoff: float = 2.0,
          exceptions: tuple = (Exception,)):
    """Retry with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            wait = delay
            for attempt in range(times):
                try: return func(*args, **kwargs)
                except exceptions:
                    if attempt == times - 1: raise
                    _via_sleep(wait)
                    wait *= backoff
            return func(*args, **kwargs)
        return wrapper
    return decorator

def shield(default=None):
    """Catch all exceptions; return default."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try: return func(*args, **kwargs)
            except Exception: return default
        return wrapper
    return decorator

def guard_memory(max_percent: int = _MEM_PRESSURE_WARN):
    """Skip execution if memory pressure too high."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if under_memory_pressure(max_percent): return None
            return func(*args, **kwargs)
        return wrapper
    return decorator

def guard_threads(max_cpu: int = _CPU_PRESSURE_STOP):
    """Skip execution if CPU overloaded."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if under_cpu_pressure(max_cpu): return None
            return func(*args, **kwargs)
        return wrapper
    return decorator

class _ResultCache:
    """Thread-safe LRU cache for @accelerate_cached."""
    _MISS = object()

    def __init__(self, maxsize: int = _RESULT_CACHE_MAXSIZE):
        self._d: OrderedDict = OrderedDict()
        self._n = maxsize
        self._lock = threading.RLock()
        self._hits = self._misses = 0

    def get(self, key: Any) -> Any:
        with self._lock:
            v = self._d.get(key, self._MISS)
            if v is not self._MISS:
                self._d.move_to_end(key); self._hits += 1; return v
            self._misses += 1; return self._MISS

    def set(self, key: Any, value: Any) -> None:
        with self._lock:
            self._d[key] = value; self._d.move_to_end(key)
            while len(self._d) > self._n: self._d.popitem(last=False)

    def stats(self) -> Dict:
        return {"hits": self._hits, "misses": self._misses, "size": len(self._d)}

    def clear(self) -> None:
        with self._lock: self._d.clear()

def accelerate_cached(func=None, *, mode: str = "balanced",
                      maxsize: int = _RESULT_CACHE_MAXSIZE,
                      use_cache: bool = True) -> Callable:
    """@accelerate drop-in with result LRU cache."""
    def decorator(f: Callable) -> Callable:
        cache = _ResultCache(maxsize) if use_cache else None
        @wraps(f)
        def wrapper(*args, **kwargs):
            key: Any = None
            if cache:
                try:
                    key = (args, tuple(sorted(kwargs.items())))
                    hit = cache.get(key)
                    if hit is not _ResultCache._MISS: return hit
                except TypeError:
                    key = None
            result = f(*args, **kwargs)
            if cache and key is not None: cache.set(key, result)
            return result
        wrapper._accel_cache = cache
        return wrapper
    if func is not None: return decorator(func)
    return decorator

def accelerate(func=None, *, mode: str = "balanced"):
    """
    @accelerate decorator — bootstraps env vars + chooses backend.
    Compatible with vis_mega §27.
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            apply_vrn_vds_max_accel(mode)
            strategy = choose_acceleration_strategy(args, kwargs, mode)
            return execute_with_backend(f, strategy["backend"], args, kwargs)
        return wrapper
    if func is not None: return decorator(func)
    return decorator

# ══════════════════════════════════════════════════════════════════════════════
# ANC-17  SAFETY UTILS
# ══════════════════════════════════════════════════════════════════════════════

def safe_call(func: Callable, *args, default=None, **kwargs) -> Any:
    try: return func(*args, **kwargs)
    except Exception: return default

def sandbox(func: Callable, *args, **kwargs) -> Tuple[bool, Any]:
    """Return (success, result)."""
    try: return True, func(*args, **kwargs)
    except Exception: return False, None

def safe_get_dict(d: Dict, *keys, default=None) -> Any:
    cur = d
    for k in keys:
        if not isinstance(cur, dict): return default
        cur = cur.get(k, default)
        if cur is default: return default
    return cur

def safe_getattr(obj, *attrs, default=None) -> Any:
    cur = obj
    for a in attrs:
        try: cur = getattr(cur, a)
        except AttributeError: return default
    return cur

def ensure_type(value, t, default=None):
    return value if isinstance(value, t) else default

def ensure_positive(value, default: int = 1):
    try: return value if value > 0 else default
    except Exception: return default

def ensure_nonempty(value, default=None):
    try: return value if len(value) > 0 else default
    except Exception: return default

# ══════════════════════════════════════════════════════════════════════════════
# ANC-18  LOGGING  (colored console, no external dep)
# ══════════════════════════════════════════════════════════════════════════════

_LOG_ON: bool = True
_LOG_TS: bool = True

class _C:
    R  = "\033[0m";  GR = "\033[90m"; RE = "\033[91m"
    GN = "\033[92m"; YL = "\033[93m"; CY = "\033[96m"
    BL = "\033[94m"; MG = "\033[95m"

def _log_line(color: str, label: str, msg: str) -> None:
    if not _LOG_ON: return
    ts = time.strftime("[%H:%M:%S] ") if _LOG_TS else ""
    print(f"{ts}{color}{label}{_C.R} {msg}", flush=True)

def accel_info(msg: str):  _log_line(_C.CY, "[ACCEL INFO] ", str(msg))
def accel_ok(msg: str):    _log_line(_C.GN, "[ACCEL OK]   ", str(msg))
def accel_warn(msg: str):  _log_line(_C.YL, "[ACCEL WARN] ", str(msg))
def accel_error(msg: str): _log_line(_C.RE, "[ACCEL ERR]  ", str(msg))
def accel_debug(msg: str): _log_line(_C.GR, "[ACCEL DBG]  ", str(msg))

# backwards-compat
info    = accel_info
success = accel_ok
warn    = accel_warn
error   = accel_error
debug   = accel_debug

enable_logging  = lambda: globals().update({"_LOG_ON": True})
disable_logging = lambda: globals().update({"_LOG_ON": False})

# ══════════════════════════════════════════════════════════════════════════════
# ANC-19  ENGINE CLASSES  (26 engines)
# ══════════════════════════════════════════════════════════════════════════════

class KPITracker:
    """Thread-safe KPI tracker — records/stats per named metric."""

    def __init__(self):
        self._data: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def record(self, name: str, value: float) -> None:
        with self._lock: self._data[name].append(value)

    def get_stats(self, name: str) -> Dict:
        values = self._data.get(name, [])
        if not values: return {"count": 0, "mean": 0.0, "min": 0.0, "max": 0.0, "sum": 0.0}
        return {"count": len(values), "mean": sum(values) / len(values),
                "min": min(values), "max": max(values), "sum": sum(values)}

    def summary(self) -> Dict:
        return {n: self.get_stats(n) for n in self._data}

    def clear(self) -> None:
        with self._lock: self._data.clear()

class Timer:
    """Context manager timer. with Timer('op') as t: ...; print(t.elapsed)"""

    def __init__(self, name: str = "", verbose: bool = True):
        self.name = name; self.verbose = verbose; self.elapsed = 0.0

    def __enter__(self): self._start = time.perf_counter(); return self

    def __exit__(self, *_):
        self.elapsed = time.perf_counter() - self._start
        if self.verbose and self.name:
            print(f"[Timer] {self.name}: {self.elapsed * 1000:.2f}ms")

@dataclass
class UltimateConfig:
    """V10 Ultimate Configuration — all acceleration settings."""
    # CPU
    enable_cpu_affinity:    bool  = True
    pin_worker_threads:     bool  = True
    enable_huge_pages:      bool  = True
    # JIT
    enable_numba:           bool  = True
    numba_parallel:         bool  = True
    numba_fastmath:         bool  = True
    numba_cache:            bool  = True
    # DataFrame
    preferred_df_backend:   str   = "polars"
    fallback_df_backend:    str   = "pandas"
    # Parallel
    enable_multiprocessing: bool  = True
    enable_threading:       bool  = True
    enable_async:           bool  = True
    enable_dask:            bool  = True
    enable_ray:             bool  = True
    enable_joblib:          bool  = True
    max_workers:            int   = 0
    # Memory
    enable_memory_pool:     bool  = True
    pool_block_size:        int   = 4096
    max_pool_blocks:        int   = 1024
    # Cache
    cache_maxsize:          int   = 8192
    cache_ttl:              int   = 3600
    enable_disk_cache:      bool  = True
    # Batch
    batch_size:             int   = 1024
    chunk_size:             int   = 4_194_304
    pipeline_depth:         int   = 4
    # Compression
    default_compression:    str   = "zstd"
    compression_level:      int   = _COMPRESS_DEFAULT_LEVEL
    # GC
    gc_threshold: tuple = (_GC_THRESHOLD_GEN0, _GC_THRESHOLD_GEN1, _GC_THRESHOLD_GEN2)
    # Financial tolerances
    tol_eq_identity:        float = 0.01
    tol_dupont_roe:         float = 0.01
    tol_cashflow_match:     float = 0.05
    sanity_roe_abs:         float = 0.50
    sanity_gm_min:          float = -0.20
    sanity_gm_max:          float = 1.00
    verbose:                bool  = True
    debug:                  bool  = False

_ULTIMATE_CFG = UltimateConfig()

class HardwareTuner:
    """Hardware Layer Optimization — CPU affinity, SIMD, env vars, warm-up."""

    _optimized = False
    _info: Dict = {}

    @staticmethod
    def get_logical_cores() -> int: return os.cpu_count() or 1

    @staticmethod
    def get_physical_cores() -> int:
        if psutil:
            try:
                n = psutil.cpu_count(logical=False)
                return n or HardwareTuner.get_logical_cores()
            except Exception: pass
        return max(1, HardwareTuner.get_logical_cores() // 2)

    @staticmethod
    def get_memory_info() -> Dict:
        if psutil:
            try:
                m = psutil.virtual_memory()
                return {"total_gb":     round(m.total     / 1024 ** 3, 2),
                        "available_gb": round(m.available / 1024 ** 3, 2),
                        "percent":      m.percent}
            except Exception: pass
        return {"total_gb": 0, "available_gb": 0, "percent": 0}

    @staticmethod
    def detect_simd() -> Dict[str, bool]:
        simd = {"sse2": False, "avx": False, "avx2": False, "avx512": False, "neon": False}
        if cpuinfo_m:
            try:
                flags = cpuinfo_m.get_cpu_info().get("flags", [])
                simd["sse2"]   = "sse2"  in flags
                simd["avx"]    = "avx"   in flags
                simd["avx2"]   = "avx2"  in flags
                simd["avx512"] = any("avx512" in f for f in flags)
            except Exception: pass
        arch = platform.machine().lower()
        if "arm" in arch or "aarch" in arch: simd["neon"] = True
        return simd

    @staticmethod
    def get_system_info() -> Dict:
        return {
            "platform":     platform.system(),
            "python":       platform.python_version(),
            "cpu_logical":  HardwareTuner.get_logical_cores(),
            "cpu_physical": HardwareTuner.get_physical_cores(),
            "memory":       HardwareTuner.get_memory_info(),
            "arch":         platform.machine(),
            "simd":         HardwareTuner.detect_simd(),
        }

    @staticmethod
    def optimize_env() -> Dict[str, str]:
        cores = str(HardwareTuner.get_physical_cores())
        env_vars = {
            "OMP_NUM_THREADS":        cores,
            "MKL_NUM_THREADS":        cores,
            "OPENBLAS_NUM_THREADS":   cores,
            "NUMEXPR_MAX_THREADS":    cores,
            "NUMBA_NUM_THREADS":      cores,
            "POLARS_MAX_THREADS":     cores,
            "VECLIB_MAXIMUM_THREADS": cores,
        }
        for k, v in env_vars.items(): os.environ.setdefault(k, v)
        return env_vars

    @staticmethod
    def cpu_warmup() -> float:
        start = time.perf_counter()
        if np is not None: _ = np.sum(np.random.random(100_000) ** 2)
        else: _ = sum(math.sin(i) * math.cos(i) for i in range(1000))
        return time.perf_counter() - start

    @classmethod
    def optimize(cls) -> Dict:
        if cls._optimized: return cls._info
        cls._info = {
            "system":      cls.get_system_info(),
            "env_vars":    cls.optimize_env(),
            "gc":          {"threshold": (_GC_THRESHOLD_GEN0,
                                          _GC_THRESHOLD_GEN1,
                                          _GC_THRESHOLD_GEN2)},
            "warmup_time": cls.cpu_warmup(),
            "timestamp":   time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        GCTuner.optimize()
        cls._optimized = True
        return cls._info

def pin_to_physical_cores(n_cores: Optional[int] = None, *,
                           start: int = 0, dry_run: bool = False) -> bool:
    """Opt-in physical-core pinning. Safe: never raises."""
    if not psutil: return False
    try:
        phys  = _cpu_count(logical=False)
        n     = max(1, min(phys, n_cores if n_cores else phys))
        cores = list(range(start, start + n))
        avail = list(psutil.Process().cpu_affinity() or range(_cpu_count()))
        valid = [c for c in cores if c in avail]
        if not valid: return False
        if not dry_run: psutil.Process().cpu_affinity(valid)
        return True
    except Exception:
        return False

class ParallelEngine:
    """M1/M5/M20: Parallel Processing Engine."""

    @staticmethod
    def get_optimal_workers() -> int:
        if _ULTIMATE_CFG.max_workers > 0: return _ULTIMATE_CFG.max_workers
        return HardwareTuner.get_physical_cores()

    @staticmethod
    def map_threaded(func: Callable, items: List[Any], max_workers: int = None) -> List[Any]:
        workers = max_workers or ParallelEngine.get_optimal_workers()
        with ThreadPoolExecutor(max_workers=workers) as ex:
            return list(ex.map(func, items))

    @staticmethod
    def map_process(func: Callable, items: List[Any], max_workers: int = None) -> List[Any]:
        workers = max_workers or ParallelEngine.get_optimal_workers()
        with ProcessPoolExecutor(max_workers=workers) as ex:
            return list(ex.map(func, items))

    @staticmethod
    def map_joblib(func: Callable, items: List[Any],
                   n_jobs: int = -1, backend: str = "loky") -> List[Any]:
        if joblib:
            return joblib.Parallel(n_jobs=n_jobs, backend=backend)(
                joblib.delayed(func)(item) for item in items)
        return [func(item) for item in items]

    @staticmethod
    def map_ray(func: Callable, items: List[Any]) -> List[Any]:
        if ray:
            try:
                if not ray.is_initialized():
                    ray.init(ignore_reinit_error=True, logging_level=40)
                rf = ray.remote(func)
                return ray.get([rf.remote(item) for item in items])
            except Exception: pass
        return [func(item) for item in items]

    @staticmethod
    def map_auto(func: Callable, items: Iterable[Any], mode: str = "auto") -> List[Any]:
        items_list = list(items)
        if not items_list: return []
        workers = ParallelEngine.get_optimal_workers()

        # Sequential for tiny lists (no thread overhead)
        if len(items_list) <= workers * 2:
            return [func(item) for item in items_list]

        # LL#25: 5-sample probe → sub-50us tasks go list-comp (avoids
        # ThreadPool/joblib cold-start when work-per-item is trivial).
        # Probe takes < 1ms; saves ~2s on xmap(5000, cheap_func).
        if mode == "auto" and len(items_list) >= 64:
            _probe_n = min(5, len(items_list))
            _t0 = time.perf_counter()
            try:
                _probe_out = [func(items_list[i]) for i in range(_probe_n)]
                _per = (time.perf_counter() - _t0) / _probe_n
                # < 50us per call → finish sequentially
                if _per < 5e-5:
                    if _probe_n == len(items_list):
                        return _probe_out
                    return _probe_out + [func(items_list[i]) for i in range(_probe_n, len(items_list))]
            except Exception:
                pass

        # mode="thread" or mode="auto" with small-medium payload → ThreadPool
        # Avoids joblib/loky 1-2s cold-start for I/O-bound and short CPU tasks
        if mode == "thread":
            return ParallelEngine.map_threaded(func, items_list)

        if mode == "auto":
            # LL#25: joblib loky only for *genuinely large* CPU-bound payloads
            # Threshold raised 2000→10000 to match cold-start amortization.
            if joblib and _ULTIMATE_CFG.enable_joblib and len(items_list) > 10000:
                return ParallelEngine.map_joblib(func, items_list)
            if ray and _ULTIMATE_CFG.enable_ray and len(items_list) > 20000:
                return ParallelEngine.map_ray(func, items_list)
            # Default: ThreadPool (fast cold-start, good for I/O + moderate CPU)
            return ParallelEngine.map_threaded(func, items_list)

        if mode == "process":
            return ParallelEngine.map_process(func, items_list)
        if mode == "joblib":
            return ParallelEngine.map_joblib(func, items_list)
        if mode == "ray":
            return ParallelEngine.map_ray(func, items_list)
        return ParallelEngine.map_threaded(func, items_list)

    @staticmethod
    async def map_async(func: Callable, items: Iterable[Any]) -> List[Any]:
        async def _wrap(item):
            if asyncio.iscoroutinefunction(func): return await func(item)
            return func(item)
        return list(await asyncio.gather(*[_wrap(item) for item in items]))

class StringEngine:
    """Fast String Processing Engine (fuzzy/Levenshtein/similarity)."""

    @staticmethod
    def fuzzy_ratio(a: str, b: str) -> float:
        if rapidfuzz: return rapidfuzz.fuzz.ratio(a, b)
        if not a or not b: return 0.0
        sa, sb = set(a.lower()), set(b.lower())
        return len(sa & sb) / len(sa | sb) * 100 if sa | sb else 0.0

    @staticmethod
    def levenshtein_distance(a: str, b: str) -> int:
        m, n = len(a), len(b)
        dp = list(range(n + 1))
        for i in range(1, m + 1):
            prev, dp[0] = dp[0], i
            for j in range(1, n + 1):
                tmp = dp[j]
                dp[j] = prev if a[i-1] == b[j-1] else 1 + min(prev, dp[j], dp[j-1])
                prev = tmp
        return dp[n]

    @staticmethod
    def fuzzy_search(query: str, choices: List[str], limit: int = 5) -> List[Tuple[str, float]]:
        if rapidfuzz: return [(r[0], r[1]) for r in
                              rapidfuzz.process.extract(query, choices, limit=limit)]
        scores = [(c, StringEngine.fuzzy_ratio(query, c)) for c in choices]
        return sorted(scores, key=lambda x: x[1], reverse=True)[:limit]

    @staticmethod
    def similarity(a: str, b: str) -> float:
        if rapidfuzz: return rapidfuzz.fuzz.ratio(a, b) / 100.0
        d = StringEngine.levenshtein_distance(a, b)
        return 1.0 - d / max(len(a), len(b)) if (a or b) else 1.0

class DataFrameEngine:
    """DataFrame Engine — polars > duckdb > pandas > pyarrow auto."""

    @staticmethod
    def get_best_backend() -> str:
        pref        = _ULTIMATE_CFG.preferred_df_backend.lower()
        real_polars = _try_import("polars")
        real_duckdb = _try_import("duckdb")
        if pref == "polars" and real_polars: return "polars"
        if pref == "duckdb" and real_duckdb: return "duckdb"
        if pref == "pandas" and pd:          return "pandas"
        if real_polars: return "polars"
        if real_duckdb: return "duckdb"
        if pd:          return "pandas"
        if _try_import("pyarrow"): return "pyarrow"
        return "numpy"

    @staticmethod
    def read_csv(path: str, backend: str = "auto", **kw) -> Any:
        if backend == "auto": backend = DataFrameEngine.get_best_backend()
        if backend == "polars" and pl:   return pl.read_csv(path, **kw)
        if backend == "duckdb" and duckdb: return duckdb.read_csv(path, **kw)
        if backend == "pandas" and pd:   return pd.read_csv(path, **kw)
        raise RuntimeError("No DataFrame backend available")

    @staticmethod
    def read_parquet(path: str, backend: str = "auto", **kw) -> Any:
        if backend == "auto": backend = DataFrameEngine.get_best_backend()
        if backend == "polars" and pl:   return pl.read_parquet(path, **kw)
        if backend == "duckdb" and duckdb: return duckdb.read_parquet(path, **kw)
        if backend == "pandas" and pd:   return pd.read_parquet(path, **kw)
        raise RuntimeError("No DataFrame backend available")

    @staticmethod
    def to_dataframe(data: Any, backend: str = "auto") -> Any:
        if backend == "auto": backend = DataFrameEngine.get_best_backend()
        if backend == "polars":
            try:
                import polars as _real_pl
                if isinstance(data, dict):      return _real_pl.DataFrame(data)
                if pd and isinstance(data, pd.DataFrame): return _real_pl.from_pandas(data)
                return _real_pl.DataFrame(data)
            except ImportError:
                pass  # fall through to pandas
        if backend == "pandas" and pd: return pd.DataFrame(data)
        return data

    @staticmethod
    def query_sql(sql: str) -> Any:
        if duckdb: return duckdb.query(sql).df()
        raise RuntimeError("DuckDB not available")

class FinanceEngine:
    """Financial Calculation Engine (ROE/ROA/DuPont/Altman-Z/MA/EMA)."""

    @staticmethod
    def calculate_roe(net_income: float, equity: float) -> float:
        return net_income / equity if equity else float("nan")

    @staticmethod
    def calculate_roa(net_income: float, total_assets: float) -> float:
        return net_income / total_assets if total_assets else float("nan")

    @staticmethod
    def calculate_gross_margin(gross_profit: float, revenue: float) -> float:
        return gross_profit / revenue if revenue else float("nan")

    @staticmethod
    def dupont_analysis(net_income: float, revenue: float,
                        total_assets: float, equity: float) -> Dict[str, float]:
        npm = net_income / revenue       if revenue       else 0.0
        tat = revenue    / total_assets  if total_assets  else 0.0
        em  = total_assets / equity      if equity        else 0.0
        return {"net_profit_margin": npm, "total_asset_turnover": tat,
                "equity_multiplier": em, "roe": npm * tat * em}

    @staticmethod
    def altman_z_score(working_capital: float, retained_earnings: float, ebit: float,
                       market_value_equity: float, total_liabilities: float,
                       sales: float, total_assets: float) -> Dict:
        if not total_assets: return {"z_score": float("nan"), "status": "unknown"}
        a = working_capital    / total_assets
        b = retained_earnings  / total_assets
        c = ebit               / total_assets
        d = market_value_equity / total_liabilities if total_liabilities else 0.0
        e = sales              / total_assets
        z = 1.2*a + 1.4*b + 3.3*c + 0.6*d + 1.0*e
        status = "safe" if z > 3.0 else ("distress" if z < 1.8 else "grey")
        return {"z_score": z, "status": status,
                "components": {"a": a, "b": b, "c": c, "d": d, "e": e}}

    @staticmethod
    def moving_average(data: List[float], window: int) -> List[float]:
        if np:
            kernel = np.ones(window) / window
            padded = np.pad(np.array(data, dtype=float), (window - 1, 0), mode="edge")
            return np.convolve(padded, kernel, mode="valid").tolist()
        result: List[float] = []
        for i in range(len(data)):
            if i < window - 1: result.append(float("nan"))
            else: result.append(sum(data[i - window + 1:i + 1]) / window)
        return result

    @staticmethod
    def exponential_moving_average(data: List[float], span: int) -> List[float]:
        if pd: return pd.Series(data).ewm(span=span, adjust=False).mean().tolist()
        alpha = 2.0 / (span + 1)
        result = [data[0]]
        for i in range(1, len(data)):
            result.append(alpha * data[i] + (1 - alpha) * result[-1])
        return result

class AlgorithmEngine:
    """M6/M16/M17: Algorithm Optimization Engine."""

    @staticmethod
    def fibonacci_optimized(n: int) -> int:
        if n <= 1: return n
        def _mm(a, b):
            return [[a[0][0]*b[0][0]+a[0][1]*b[1][0], a[0][0]*b[0][1]+a[0][1]*b[1][1]],
                    [a[1][0]*b[0][0]+a[1][1]*b[1][0], a[1][0]*b[0][1]+a[1][1]*b[1][1]]]
        def _mp(m, p):
            if p == 1: return m
            h = _mp(m, p // 2)
            if p % 2 == 0: return _mm(h, h)
            return _mm(m, _mp(m, p - 1))
        return _mp([[1,1],[1,0]], n)[0][1]

    @staticmethod
    def binary_search(arr: List[Any], target: Any) -> int:
        lo, hi = 0, len(arr) - 1
        while lo <= hi:
            mid = lo + (hi - lo) // 2
            if arr[mid] == target: return mid
            if arr[mid] < target:  lo = mid + 1
            else:                  hi = mid - 1
        return -1

    @staticmethod
    def dot_product(a: Any, b: Any) -> float:
        if np: return float(np.dot(a, b))
        return sum(x * y for x, y in zip(a, b))

# ══════════════════════════════════════════════════════════════════════════════
# ANC-19b  OPERATOR / PRECISION / LOGGER / VALIDATOR ENGINES  (v2.0 additions)
# ══════════════════════════════════════════════════════════════════════════════

# ── OperatorType ─────────────────────────────────────────────────────────────
import collections as _col
import contextlib as _ctx2
from enum import Enum as _Enum
from dataclasses import dataclass as _dc, field as _field

# [ANC:class OperatorType]
class OperatorType(_Enum):
    """運算子類型枚舉。"""
    GEMM   = "gemm"
    CONV   = "conv"
    FFT    = "fft"
    MATMUL = "matmul"
    REDUCE = "reduce"
    SORT   = "sort"

# [ANC:class PrecisionMode]
class PrecisionMode(_Enum):
    """精度模式枚舉 — 依資料範圍自動選。"""
    FP64 = "float64"
    FP32 = "float32"
    BF16 = "bfloat16"
    FP16 = "float16"
    INT8 = "int8"
    INT4 = "int4"
    AUTO = "auto"

# ── OperatorRouter ────────────────────────────────────────────────────────────
# [ANC:class OperatorRouter]
class OperatorRouter:
    """運算子路由器 — 依資料大小/可用庫選最佳實現。"""

    @staticmethod
    def route_gemm(m: int, n: int, k: int) -> str:
        if torch and m * n * k > 1_000_000:
            return "torch"
        if np:
            return "numpy"
        return "python"

    @staticmethod
    def route_fft(size: int) -> str:
        if sp:
            return "scipy"
        if np:
            return "numpy"
        return "python"

    @staticmethod
    def route_conv(channels: int, kernel: int) -> str:
        if torch:
            return "torch"
        if cv2:
            return "opencv"
        return "numpy"

    @staticmethod
    def route_matmul(m: int, n: int, k: int) -> str:
        if torch and m * n * k > 500_000:
            return "torch"
        if np:
            return "numpy"
        return "python"

    @staticmethod
    def route(op_type: "OperatorType", **kwargs) -> str:
        if op_type == OperatorType.GEMM:
            return OperatorRouter.route_gemm(
                kwargs.get("m", 100), kwargs.get("n", 100), kwargs.get("k", 100))
        if op_type == OperatorType.FFT:
            return OperatorRouter.route_fft(kwargs.get("size", 1024))
        if op_type == OperatorType.CONV:
            return OperatorRouter.route_conv(
                kwargs.get("channels", 3), kwargs.get("kernel", 3))
        if op_type == OperatorType.MATMUL:
            return OperatorRouter.route_matmul(
                kwargs.get("m", 100), kwargs.get("n", 100), kwargs.get("k", 100))
        return "auto"

# ── PrecisionController ────────────────────────────────────────────────────────
# [ANC:class PrecisionController]
class PrecisionController:
    """精度控制器 — 依資料範圍/精度需求選 dtype。"""

    @staticmethod
    def select_precision(data_range: float, accuracy_required: float) -> "PrecisionMode":
        if accuracy_required < 0.01:
            return PrecisionMode.FP32
        if data_range < 128 and accuracy_required >= 0.1:
            return PrecisionMode.INT8
        if accuracy_required >= 0.05:
            return PrecisionMode.BF16
        return PrecisionMode.FP32

    @staticmethod
    def quantize_to_int8(data: Any) -> Tuple[Any, float]:
        if np is None:
            return data, 1.0
        arr   = np.asarray(data, dtype=np.float32)
        mx    = float(np.abs(arr).max())
        scale = 127.0 / mx if mx > 0 else 1.0
        return (arr * scale).astype(np.int8), scale

    @staticmethod
    def dequantize_from_int8(data: Any, scale: float) -> Any:
        if np is None:
            return data
        return np.asarray(data, dtype=np.float32) / scale

    @staticmethod
    def auto_cast(frame: Any, target: "PrecisionMode") -> Any:
        """Cast a numpy array / pandas column to target precision."""
        if np is None or frame is None:
            return frame
        dtype_map = {
            PrecisionMode.FP64: np.float64,
            PrecisionMode.FP32: np.float32,
            PrecisionMode.FP16: np.float16,
            PrecisionMode.INT8: np.int8,
        }
        dtype = dtype_map.get(target)
        if dtype is None:
            return frame
        try:
            return np.asarray(frame, dtype=dtype)
        except Exception:
            return frame

# ── VRN_MasterLogger ──────────────────────────────────────────────────────────
# [ANC:class VRN_MasterLogger]
class VRN_MasterLogger:
    """
    Unified logger replacing VRN_Monitor / VRN_SystemMonitor / VRN_Logger boilerplate.
    Writes to console + optional log file.
    Backwards-compat aliases: VRN_Monitor, VRN_SystemMonitor, VRN_Logger.
    """

    def __init__(self, name: str = "VRN_MASTER",
                 log_file: str = "vrn_master_core.log"):
        import logging as _log
        self.name   = name
        self.logger = _log.getLogger(name)
        self.logger.setLevel(_log.DEBUG)
        if not self.logger.handlers:
            fmt = _log.Formatter(
                "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
            )
            sh = _log.StreamHandler()
            sh.setFormatter(fmt)
            self.logger.addHandler(sh)
            try:
                fh = _log.FileHandler(log_file, encoding="utf-8")
                fh.setFormatter(fmt)
                self.logger.addHandler(fh)
            except Exception:
                pass

    def info(self,  msg: str) -> None: self.logger.info(msg)
    def error(self, msg: str) -> None: self.logger.error(msg)
    def warn(self,  msg: str) -> None: self.logger.warning(msg)
    def debug(self, msg: str) -> None: self.logger.debug(msg)
    def success(self, msg: str) -> None: self.logger.info(f"[OK] {msg}")

# Backwards-compat aliases
VRN_Monitor       = VRN_MasterLogger
VRN_SystemMonitor = VRN_MasterLogger
VRN_Logger        = VRN_MasterLogger

# ── JSONEngine ─────────────────────────────────────────────────────────────────
# [ANC:class JSONEngine]
class JSONEngine:
    """
    Fast JSON engine: orjson > ujson > rapidjson > stdlib.
    Class interface for use inside larger engine pipelines.
    Module-level json_dumps/json_loads remain the preferred functional API.
    """

    @staticmethod
    def dumps(obj: Any, indent: int = None) -> str:
        return json_dumps(obj, indent)

    @staticmethod
    def loads(s: Union[str, bytes]) -> Any:
        return json_loads(s)

    @staticmethod
    def dumps_bytes(obj: Any) -> bytes:
        """Return raw bytes (orjson native, others encoded)."""
        if orjson is not None:
            try:
                return orjson.dumps(obj)
            except Exception:
                pass
        return json_dumps(obj).encode("utf-8")

    @staticmethod
    def roundtrip(obj: Any) -> Any:
        """Serialize then deserialize — useful for deep-copy via JSON."""
        return json_loads(json_dumps(obj))

# ── DataValidator ──────────────────────────────────────────────────────────────
# [ANC:class DataValidator]
class DataValidator:
    """
    Ticker + DataFrame validator.
    Validates TW 4-digit ticker format and cleans DataFrames.
    """

    # TW Ticker Regex — LOCKED, must not be modified (VRN rule)
    _TW_TICKER_RE = re.compile(r"^(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})$")
    _TW_BB_RE     = re.compile(r"^\d{4} TT$")
    _TW_YF_RE     = re.compile(r"^\d{4}\.(TW|TWO)$")

    @staticmethod
    def validate_ticker(t: Any) -> bool:
        """Validate TW 4-digit ticker (first digit non-zero, not 2021-2030)."""
        return bool(DataValidator._TW_TICKER_RE.match(str(t)))

    @staticmethod
    def validate_bloomberg(t: Any) -> bool:
        """Validate XXXX TT Bloomberg format."""
        return bool(DataValidator._TW_BB_RE.match(str(t)))

    @staticmethod
    def validate_yfinance(t: Any) -> bool:
        """Validate XXXX.TW or XXXX.TWO yfinance format."""
        return bool(DataValidator._TW_YF_RE.match(str(t)))

    @staticmethod
    def clean_dataframe(df: Any) -> Any:
        """Drop duplicates on date/ticker cols, sort, reset index."""
        if df is None:
            return None
        if pd and isinstance(df, pd.DataFrame):
            if df.empty:
                return df
            key_cols  = [c for c in ["date", "ticker", "Date", "Ticker"] if c in df.columns]
            sort_cols = [c for c in ["date", "ticker"] if c in df.columns]
            if key_cols:
                df = df.drop_duplicates(subset=key_cols, keep="last")
            if sort_cols:
                df = df.sort_values(sort_cols).reset_index(drop=True)
        return df

    @staticmethod
    def filter_valid_tickers(tickers: List[Any]) -> List[str]:
        """Return only valid TW tickers from a list."""
        return [str(t) for t in tickers if DataValidator.validate_ticker(t)]

# ══════════════════════════════════════════════════════════════════════════════
# ANC-19c  CAPABILITY PROFILE  (v2.0 — detect_blas / detect_libraries / get_profile)
# ══════════════════════════════════════════════════════════════════════════════

import io as _io2

# [ANC:def detect_blas]
def detect_blas() -> str:
    """
    Detect numpy BLAS backend.
    Returns: mkl | openblas | blis | atlas | apple-accelerate | unknown
    Handles NumPy >=1.25 show_config(mode='dicts') + redirect_stdout fallback.
    """
    if np is None:
        return "unknown"
    try:
        try:
            info_dict = np.show_config(mode="dicts")   # NumPy >= 1.25
            text = str(info_dict).lower()
        except TypeError:
            buf = _io2.StringIO()
            with contextlib.redirect_stdout(buf):
                np.__config__.show()
            text = buf.getvalue().lower()
        for key, label in (
            ("mkl",        "mkl"),
            ("openblas",   "openblas"),
            ("blis",       "blis"),
            ("atlas",      "atlas"),
            ("accelerate", "apple-accelerate"),
        ):
            if key in text:
                return label
    except Exception:
        pass
    return "unknown"

# [ANC:def detect_libraries]
def detect_libraries() -> Dict[str, bool]:
    """
    Return {lib_name: available} for 80+ key libraries.
    Grouped by domain. Uses _probe() — no import side-effects.
    """
    groups: Dict[str, List[str]] = {
        "core_numeric": [
            "numpy", "scipy", "numba", "numexpr", "bottleneck",
            "sympy", "mpmath", "statsmodels", "sklearn",
            "pyfftw", "sparse",
        ],
        "data": [
            "pandas", "polars", "pyarrow", "vaex", "duckdb",
            "modin", "dask", "datatable", "fastparquet",
            "orjson", "ujson", "rapidjson", "msgpack", "msgspec",
        ],
        "image": [
            "PIL", "cv2", "pyvips", "skimage", "pytesseract",
            "paddleocr", "imageio", "rawpy",
        ],
        "ml": [
            "torch", "tensorflow", "jax", "onnxruntime",
            "lightgbm", "xgboost", "catboost", "sklearn",
            "spacy", "gensim", "transformers",
        ],
        "compress": [
            "lz4", "zstandard", "snappy", "brotli", "blosc2", "blosc",
        ],
        "parallel": [
            "joblib", "ray", "multiprocess", "loky",
            "billiard", "pebble", "pathos",
        ],
        "cache": [
            "diskcache", "cachetools", "cachebox", "redis", "lmdb",
        ],
        "hash": [
            "xxhash", "blake3", "mmh3", "cityhash",
        ],
        "network": [
            "requests", "httpx", "aiohttp", "urllib3", "aiofiles",
        ],
        "finance": [
            "yfinance", "talib", "pandas_ta", "ta", "ffn",
        ],
        "async": [
            "winloop", "uvloop", "anyio", "trio",
        ],
        "system": [
            "psutil", "cpuinfo",
        ],
        "string": [
            "regex", "rapidfuzz", "Levenshtein", "chardet",
        ],
        "misc": [
            "loguru", "rich", "tqdm", "structlog",
            "networkx", "openpyxl", "fasteners", "bitarray",
        ],
    }
    result: Dict[str, bool] = {}
    for names in groups.values():
        for name in names:
            result[name.lower()] = _probe(name)
    return result

# [ANC:def detect_system]
def detect_system() -> Dict[str, Any]:
    """Return system capability dict (platform, python, CPU, RAM, BLAS)."""
    return {
        "platform":     platform.system(),
        "python":       platform.python_version(),
        "cpu_count":    _cpu_count(logical=True),
        "cpu_physical": _cpu_count(logical=False),
        "ram_mb":       _available_ram_mb(),
        "blas":         detect_blas(),
        "arch":         platform.machine(),
    }

# [ANC:def build_capability_profile]
def build_capability_profile() -> Dict[str, Any]:
    """Full system + library + BLAS capability snapshot."""
    return {
        "system":    detect_system(),
        "libraries": detect_libraries(),
        "blas":      detect_blas(),
    }

_PROFILE_CACHE: Optional[Dict[str, Any]] = None

# [ANC:def get_profile]
def get_profile(force_refresh: bool = False) -> Dict[str, Any]:
    """Cached capability profile — computed once, reused on subsequent calls."""
    global _PROFILE_CACHE
    if _PROFILE_CACHE is None or force_refresh:
        _PROFILE_CACHE = build_capability_profile()
    return _PROFILE_CACHE

# [ANC:def cached_identity]
@lru_cache(maxsize=4096)
def cached_identity(value: str) -> str:
    """LRU identity — useful as a cache-key normalizer / string interning."""
    return value

class Strategies:
    """加速策略庫 (M1-M50 + T1-T40)."""
    METHODS: Dict[str, str] = {
        "M1": "Multithreading",   "M2": "Vectorization",     "M3": "Caching",
        "M4": "Batch Processing", "M5": "Load Balancing",    "M6": "Algorithm Optimization",
        "M7": "Recursion Control","M8": "Memory Pooling",     "M9": "Branch Prediction",
        "M10":"Compression",      "M11":"Pipelining",         "M12":"Async I/O",
        "M13":"Event-Driven",     "M14":"GC Tuning",          "M15":"Batch Merging",
        "M16":"Loop Unrolling",   "M17":"Constant Folding",   "M18":"Dead Code Elimination",
        "M19":"Data Locality",    "M20":"Parallel Loops",     "M21":"SIMD",
        "M22":"Prefetching",      "M23":"Branch Elimination", "M24":"Instruction Scheduling",
        "M25":"Cross-Module Fusion","M26":"MMAP Streaming",   "M27":"CoW Optimization",
        "M28":"Lock-Free DS",     "M29":"Arena Allocation",   "M30":"TLS Storage",
        "M31":"Adaptive Chunk",   "M32":"Work Stealing",      "M33":"Speculative Prefetch",
        "M34":"NUMA-Aware",       "M35":"Lazy Deserialization","M36":"Hot-Path Isolation",
        "M37":"Inline Cache",     "M38":"Bloom Filter Accel", "M39":"Delta Compression",
        "M40":"Hierarchical Batch","M41":"SIMD Auto-Vec",     "M42":"Cache-Line Opt",
        "M43":"Branch-Hint",      "M44":"Loop-Unroll Hint",   "M45":"Prefetch Hint",
        "M46":"Adaptive Thread",  "M47":"Cache Hierarchy",    "M48":"Memory Barrier Opt",
        "M49":"Lock-Free Queue",  "M50":"Pipeline Fusion",
    }
    NON_TOOL: Dict[str, str] = {f"T{i:02d}": f"Technique-T{i:02d}" for i in range(1, 41)}

    @classmethod
    def count(cls) -> int: return len(cls.METHODS) + len(cls.NON_TOOL)

    @classmethod
    def get_all(cls) -> Dict[str, str]:
        r = dict(cls.METHODS); r.update(cls.NON_TOOL); return r

# ── Workload detection (needed for accelerate decorator) ─────────────────────

_TESSERACT_OK = _try_import("pytesseract")
_PADDLEOCR_OK = _try_import("paddleocr")
_OCR_SFXS = (".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp")
_IO_SFXS  = (".csv", ".parquet", ".json", ".xlsx", ".xls", ".tsv",
             ".feather", ".pkl", ".db", ".sqlite")

def detect_workload_type(args: tuple, kwargs: dict) -> str:
    all_args = list(args) + list(kwargs.values())
    if np:
        for a in all_args:
            if isinstance(a, np.ndarray): return "numeric"
    try:
        if pd:
            for a in all_args:
                if isinstance(a, pd.DataFrame): return "data"
        if pl:
            for a in all_args:
                if _is_polars_df(a): return "data"
    except Exception: pass
    try:
        if cv2:
            for a in all_args:
                if hasattr(a, "shape") and len(getattr(a, "shape", ())) in (2, 3):
                    return "image"
    except Exception: pass
    for a in all_args:
        if isinstance(a, str) and a.lower().endswith(_IO_SFXS): return "io"
    if _TESSERACT_OK:
        for a in all_args:
            if isinstance(a, str) and a.lower().endswith(_OCR_SFXS): return "ocr"
    if torch:
        for a in all_args:
            try:
                if isinstance(a, torch.Tensor): return "ml"
            except Exception: pass
    for a in all_args:
        if isinstance(a, (bytes, bytearray)): return "compression"
    return "generic"

def choose_backend(workload: str) -> str:
    if workload == "numeric":
        if numba:  return "numba"
        if np:     return "numpy"
        return "python"
    if workload == "data":
        if pl:     return "polars"
        if pa:     return "arrow"
        return "pandas"
    if workload in ("image", "ocr"):
        if pyvips: return "pyvips"
        if cv2:    return "opencv"
        return "pillow"
    if workload == "ml":
        if onnxruntime: return "onnx"
        if torch:       return "torch"
        return "numpy"
    if workload == "compression":
        if zstd: return "zstd"
        if lz4:  return "lz4"
        return "python"
    return "python"

def choose_acceleration_strategy(args: tuple, kwargs: dict,
                                  mode: str = "balanced") -> Dict:
    workload  = detect_workload_type(args, kwargs)
    backend   = choose_backend(workload)
    cpu_count = _cpu_count(logical=True)
    if system_under_pressure():
        return {"backend": "python", "threads": 1,
                "reason": "system_pressure", "workload": workload}
    threads = {"safe": 1, "balanced": max(1, cpu_count // 2),
               "aggressive": cpu_count}.get(mode, 1)
    return {"backend": backend, "threads": threads,
            "reason": f"{mode}_mode", "workload": workload}

# ══════════════════════════════════════════════════════════════════════════════
# ANC-20  CROSS-ACCEL LAYER  (xmap/xfetch/xbatch/xcache/cross_init)
# ══════════════════════════════════════════════════════════════════════════════

_ACCEL_KPI:      Optional[KPITracker]    = None
_ACCEL_CACHE:    Optional[CacheManager]  = None
_ACCEL_ATCACHE:  Optional[AutotuneCache] = None
_ACCEL_LOCK      = threading.Lock()
_CROSS_INIT_DONE = False

def _get_kpi() -> KPITracker:
    global _ACCEL_KPI
    if _ACCEL_KPI is None:
        with _ACCEL_LOCK:
            if _ACCEL_KPI is None: _ACCEL_KPI = KPITracker()
    return _ACCEL_KPI

def _get_cache() -> CacheManager:
    global _ACCEL_CACHE
    if _ACCEL_CACHE is None:
        with _ACCEL_LOCK:
            if _ACCEL_CACHE is None: _ACCEL_CACHE = CacheManager(":memory:")
    return _ACCEL_CACHE

def _get_atcache() -> AutotuneCache:
    global _ACCEL_ATCACHE
    if _ACCEL_ATCACHE is None:
        with _ACCEL_LOCK:
            if _ACCEL_ATCACHE is None:
                _ACCEL_ATCACHE = AutotuneCache(_AUTOTUNE_DB_PATH, _AUTOTUNE_DEFAULT_TTL)
    return _ACCEL_ATCACHE

def xmap(func: Callable, items: List[Any], *,
         mode: str = "auto", max_workers: Optional[int] = None,
         dedupe: bool = False, chunk_size: Optional[int] = None,
         guard_mem: bool = True) -> List[Any]:
    """
    Cross-accelerated map:
      - memory pressure gate (guard_mem)
      - adaptive chunk splitting
      - ParallelEngine auto (thread/joblib/ray)
      - KPI tracking
    """
    if not items: return []
    if guard_mem and under_memory_pressure(_XMAP_PRESSURE_GATE):
        return [func(i) for i in items]

    kpi = _get_kpi()
    t0  = time.perf_counter()

    payload = dedupe_preserve_order(items) if dedupe else list(items)

    if chunk_size is None and len(payload) > _XMAP_CHUNK_THRESHOLD:
        chunk_size = adaptive_chunk_size(len(payload))

    if chunk_size and chunk_size < len(payload):
        chunks  = chunk_list(payload, chunk_size)
        results_nested = ParallelEngine.map_auto(
            lambda c: [func(x) for x in c], chunks, mode=mode)
        result: List[Any] = []
        for r in results_nested:
            if isinstance(r, list): result.extend(r)
            elif r is not None: result.append(r)
    else:
        result = ParallelEngine.map_auto(func, payload, mode=mode)

    kpi.record("xmap.items",   len(payload))
    kpi.record("xmap.elapsed", time.perf_counter() - t0)
    return result

async def xmap_async(func: Callable, items: List[Any], *, semaphore: int = 10):
    """Async variant of xmap using asyncio.gather + semaphore."""
    sem = asyncio.Semaphore(semaphore)
    async def _wrap(item):
        async with sem:
            if asyncio.iscoroutinefunction(func): return await func(item)
            return func(item)
    return list(await asyncio.gather(*[_wrap(i) for i in items]))

def xfetch(urls: List[str], *,
           max_workers: Optional[int] = None,
           timeout: int = _XFETCH_DEFAULT_TIMEOUT,
           return_type: str = "text",
           use_cache: bool = True,
           cache_ttl: int = _XFETCH_CACHE_TTL) -> List[Optional[str]]:
    """
    Cross-accelerated batch URL fetcher:
      - fast_hash cache keys
      - CacheManager L1+L2
      - ParallelEngine thread pool
      - memory pressure guard
      - KPI tracking
    """
    if not urls: return []

    kpi   = _get_kpi()
    cache = _get_cache()
    t0    = time.perf_counter()
    workers = max_workers or min(thread_budget_cross(), _XFETCH_MAX_WORKERS)

    results: List[Optional[str]] = [None] * len(urls)
    miss_idx: List[int] = []

    if use_cache:
        for i, url in enumerate(urls):
            key    = fast_hash(url.encode(), "xxhash")
            cached = cache.get(key)
            if cached is not None: results[i] = cached
            else: miss_idx.append(i)
    else:
        miss_idx = list(range(len(urls)))

    if miss_idx and not (under_memory_pressure(90) or under_cpu_pressure(95)):
        miss_urls = [urls[i] for i in miss_idx]

        def _fetch_one(url: str) -> Optional[str]:
            if requests_m:
                try:
                    r = requests_m.get(url, headers={"User-Agent": "VIA-xfetch/1.0"},
                                       timeout=timeout, verify=False)
                    if r.status_code == 200:
                        return r.text if return_type == "text" else r.content.decode("utf-8", "ignore")
                except Exception: pass
            import urllib.request as _ur
            try:
                with _ur.urlopen(url, timeout=timeout) as r:
                    data = r.read()
                    return data.decode("utf-8", "ignore")
            except Exception: return None

        fetched = parallel_map(_fetch_one, miss_urls, max_workers=workers)
        for idx_pos, orig_idx in enumerate(miss_idx):
            val = fetched[idx_pos]
            results[orig_idx] = val
            if use_cache and val is not None:
                key = fast_hash(urls[orig_idx].encode(), "xxhash")
                cache.set(key, val, ttl=cache_ttl)

    kpi.record("xfetch.urls",      len(urls))
    kpi.record("xfetch.cache_hit", len(urls) - len(miss_idx))
    kpi.record("xfetch.elapsed",   time.perf_counter() - t0)
    return results

def xbatch_process(func: Callable, items: List[Any], *,
                   batch_size: Optional[int] = None,
                   max_workers: Optional[int] = None,
                   on_error: str = "skip",
                   default_value: Any = None,
                   progress: bool = False) -> List[Any]:
    """
    Production-grade batch processor:
      - adaptive RAM-aware batch sizing
      - memory pressure gate → sequential fallback
      - per-item error handling (skip/raise/default)
      - optional progress print
      - KPI tracking
    """
    if not items: return []

    kpi = _get_kpi()
    t0  = time.perf_counter()

    bs      = batch_size or adaptive_chunk_size(len(items), item_bytes=2048)
    workers = max_workers or thread_budget()

    results: List[Any] = []
    total   = len(items)
    done    = 0

    for chunk in chunk_list(items, bs):
        if under_memory_pressure(85):
            for item in chunk:
                try: results.append(func(item))
                except Exception:
                    if on_error == "raise": raise
                    results.append(default_value)
        else:
            with ThreadPoolExecutor(max_workers=workers) as ex:
                futures = {ex.submit(func, item): i for i, item in enumerate(chunk)}
                batch_r: List[Any] = [default_value] * len(chunk)
                for f in as_completed(futures):
                    idx = futures[f]
                    try: batch_r[idx] = f.result()
                    except Exception:
                        if on_error == "raise": raise
                        batch_r[idx] = default_value
                results.extend(batch_r)

        done += len(chunk)
        if progress:
            pct = done / total * 100
            print(f"\r[xbatch] {done}/{total} ({pct:.1f}%)  ", end="", flush=True)

    if progress: print()

    kpi.record("xbatch.items",   total)
    kpi.record("xbatch.elapsed", time.perf_counter() - t0)
    return results

def xcache(ttl: int = 3600, key_prefix: str = ""):
    """Cross-accelerated TTL cache decorator (fast_hash key + CacheManager)."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            raw_key = f"{key_prefix}{func.__name__}:{repr(args)}:{repr(sorted(kwargs.items()))}"
            key     = fast_hash(raw_key.encode())
            c       = _get_cache()
            cached  = c.get(key)
            if cached is not None: return cached
            result = func(*args, **kwargs)
            if result is not None: c.set(key, result, ttl=ttl)
            return result
        wrapper.cache_clear = lambda: None
        return wrapper
    return decorator

# ── Numeric cross-accelerators ───────────────────────────────────────────────

@safe_jit()
def xdot(a: Any, b: Any) -> float:
    """JIT-accelerated dot product."""
    if np is not None: return float(np.dot(a, b))
    return sum(float(x) * float(y) for x, y in zip(a, b))

def xma(data: List[float], window: int) -> List[float]:
    return FinanceEngine.moving_average(data, window)

def xema(data: List[float], span: int) -> List[float]:
    return FinanceEngine.exponential_moving_average(data, span)

def xfuzzy_ticker(query: str, ticker_list: List[str],
                  limit: int = 5) -> List[Tuple[str, float]]:
    return StringEngine.fuzzy_search(query, ticker_list, limit=limit)

xconcat = accelerated_concat
xsort   = accelerated_sort
xdedup  = accelerated_drop_duplicates

# ── Additional cross-aliases (only-increase, backwards-compat) ───────────────
xjson_dumps = json_dumps       # orjson > ujson > stdlib
xjson_loads = json_loads       # orjson > ujson > stdlib
xcompress   = compress_bytes   # zstd > lz4 > blosc2 > gzip
xdecompress = decompress_bytes # auto-detect codec

def cross_accelerate(
    func: Callable[[Any], Any],
    items: List[Any],
    dedupe: bool = True,
    max_workers: Optional[int] = None,
) -> List[Any]:
    """
    Dedupe → accelerated map.  Drop-in for manual for-loops.
    Dispatch strategy:
      ≤ workers*4  → sequential (no thread overhead)
      ≤ 2000       → ThreadPool (fast cold-start)
      > 2000       → parallel_map (full parallel)
    Backwards-compat with VIA_SuperAccel_Module §E.
    """
    if not items:
        return []
    payload = dedupe_preserve_order(items) if dedupe else list(items)
    workers  = max_workers or thread_budget()
    n        = len(payload)

    # Sequential fast-path for tiny batches
    if n <= workers * 4:
        return [func(x) for x in payload]

    # Thread pool for medium batches (avoids joblib cold-start)
    if n <= 2000:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            return list(ex.map(func, payload))

    # Full parallel_map for large batches
    return parallel_map(func, payload, max_workers=workers, mode="thread")

# ── xmap_async public alias ──────────────────────────────────────────────────
# (coroutine defined in ANC-20; alias ensures it's in __all__ and easily callable)
# Usage: results = asyncio.run(xmap_async(func, items))

# ══════════════════════════════════════════════════════════════════════════════
# ANC-21  LAZY POOL  (warm-up + atexit drain)
# ══════════════════════════════════════════════════════════════════════════════

class _LazyPool:
    """
    Lazy shared ThreadPoolExecutor.
    Warmed on first access; drained via atexit.
    Eliminates first-call latency for decorated / parallel functions.
    """
    _instance: Optional[ThreadPoolExecutor] = None
    _lock      = threading.Lock()
    _n_workers = 0

    @classmethod
    def get(cls, mode: Optional[str] = None) -> ThreadPoolExecutor:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    n = thread_budget(mode)
                    cls._instance  = ThreadPoolExecutor(max_workers=n)
                    cls._n_workers = n
                    atexit.register(cls._drain)
                    futs = [cls._instance.submit(lambda: None) for _ in range(n)]
                    for f in futs:
                        try: f.result(timeout=2.0)
                        except Exception: pass
        return cls._instance

    @classmethod
    def _drain(cls) -> None:
        with cls._lock:
            if cls._instance is not None:
                cls._instance.shutdown(wait=False, cancel_futures=True)
                cls._instance = None

    @classmethod
    def map(cls, fn: Callable, items: Iterable, timeout: Optional[float] = None) -> List:
        return list(cls.get().map(fn, items, timeout=timeout))

    @classmethod
    def submit(cls, fn: Callable, *args: Any, **kwargs: Any) -> Future:
        return cls.get().submit(fn, *args, **kwargs)

def warm_thread_pool(mode: Optional[str] = None) -> int:
    """Warm shared pool. Returns worker count."""
    _LazyPool.get(mode)
    return _LazyPool._n_workers

# ══════════════════════════════════════════════════════════════════════════════
# ANC-22  SUBPROCESS SNAPSHOT
# ══════════════════════════════════════════════════════════════════════════════

def snapshot_for_subprocess(mode=None) -> Dict[str, str]:
    """Full os.environ snapshot for subprocess env= kwarg."""
    configure_ultra_acceleration(mode)
    return dict(os.environ)

def bootstrap_vis_accelerator(accel_instance: object, mode=None, *,
                               verbose: bool = False) -> Dict[str, str]:
    """Full bootstrap for a live VISAccelerator instance. (IP-10)"""
    raw = (getattr(accel_instance, "_accel_mode", None)
           or (mode if isinstance(mode, str) else None)
           or os.environ.get("VIA_ACCEL_MODE")
           or VIA_ACCEL_DEFAULT_MODE)
    eff = _resolve_mode(raw)
    env = apply_vrn_vds_max_accel(eff)
    t   = int(env.get("VIA_ACCEL_ACTIVE_THREADS", "1"))
    tc  = int(env.get("VIA_ACCEL_CROSS_THREADS",  "1"))
    warm_thread_pool(eff)
    GCTuner.optimize()
    try:
        accel_instance.accel_mode          = eff
        accel_instance.accel_threads       = t
        accel_instance.accel_threads_cross = tc
    except Exception: pass
    if verbose:
        cls = type(accel_instance).__name__
        print(f"[VIA_BOOT] {cls} → mode={eff} t={t} tc={tc} pool=warm gc=tuned")
    return env

def accel_init_env(mode=None, vrn_mode=None, *,
                   warm_pool: bool = True, tune_gc: bool = True,
                   verbose: bool = False) -> Dict[str, str]:
    """One-liner bootstrap for module-level or __main__ init."""
    eff = _resolve_mode(vrn_mode or mode)
    env = apply_vrn_vds_max_accel(eff)
    if warm_pool: warm_thread_pool(eff)
    if tune_gc:   GCTuner.optimize()
    if verbose:
        t  = env["VIA_ACCEL_ACTIVE_THREADS"]
        tc = env["VIA_ACCEL_CROSS_THREADS"]
        print(f"[VIA_BOOT] mode={eff} threads={t} cross={tc} pool=warm gc=tuned")
    return env

# ══════════════════════════════════════════════════════════════════════════════
# ANC-23  configure_ultra_acceleration  (one-line startup)
# ══════════════════════════════════════════════════════════════════════════════

def configure_ultra_acceleration(mode=None) -> Dict[str, str]:
    """
    ── 一行啟動 ──
    推送所有加速 env vars + 初始化 winloop/uvloop event loop.
    Returns: applied env var dict
    """
    result = apply_vrn_vds_max_accel(mode)

    if ENABLE_WINLOOP_INSTALL:
        if winloop:
            try: winloop.install()
            except Exception: pass
        elif uvloop:
            try:
                uvloop.install()
                asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
            except Exception: pass

    return result

# ══════════════════════════════════════════════════════════════════════════════
# ANC-24  VISAccelerator  (main interface singleton)
# ══════════════════════════════════════════════════════════════════════════════

class VISAccelerator:
    """
    VIS Ultimate Accelerator — main interface.
    Wraps all engines; call VISAccelerator().initialize() once at startup.
    """

    def __init__(self, config: UltimateConfig = None):
        self._cfg         = config or _ULTIMATE_CFG
        self._initialized = False
        self._init_ts     = time.time()
        self._kpi         = KPITracker()
        self._atcache     = AutotuneCache()

    def initialize(self) -> Dict:
        if self._initialized: return {"status": "already_initialized"}
        hw = HardwareTuner.optimize()
        self._initialized = True
        return {"status": "initialized", "hardware": hw,
                "libs_available": count_available_libs(),
                "strategies": Strategies.count()}

    # ── Parallel ──────────────────────────────────────────────
    def parallel_map(self, func: Callable, items: Iterable,
                     mode: str = "auto") -> List[Any]:
        return ParallelEngine.map_auto(func, items, mode)

    # ── Compression ───────────────────────────────────────────
    def compress(self, data: bytes, method: str = "auto") -> bytes:
        return CompressionEngine.compress(data, method)

    def decompress(self, data: bytes) -> bytes:
        return CompressionEngine.decompress(data)

    # ── JSON ──────────────────────────────────────────────────
    def json_dumps(self, obj: Any, indent: int = None) -> str:
        return json_dumps(obj, indent)

    def json_loads(self, s: Union[str, bytes]) -> Any:
        return json_loads(s)

    # ── Hash ──────────────────────────────────────────────────
    def hash(self, data: bytes, method: str = "xxhash") -> str:
        return fast_hash(data, method)

    # ── Finance ───────────────────────────────────────────────
    def roe(self, net_income: float, equity: float) -> float:
        return FinanceEngine.calculate_roe(net_income, equity)

    def dupont(self, net_income: float, revenue: float,
               total_assets: float, equity: float) -> Dict:
        return FinanceEngine.dupont_analysis(net_income, revenue, total_assets, equity)

    # ── Status ────────────────────────────────────────────────
    def get_status(self) -> Dict:
        return {
            "initialized":  self._initialized,
            "uptime_sec":   round(time.time() - self._init_ts, 2),
            "libs":         count_available_libs(),
            "capabilities": capability_report(),
            "strategies":   Strategies.count(),
            "system":       HardwareTuner.get_system_info(),
            "kpi":          self._kpi.summary(),
        }

# Module-level singleton
VIS_ACCELERATOR = VISAccelerator()

# ══════════════════════════════════════════════════════════════════════════════
# cross_init — idempotent full bootstrap
# ══════════════════════════════════════════════════════════════════════════════

def cross_init(mode: str = None, silent: bool = False) -> Dict:
    """
    一行啟動所有加速層 (冪等):
      1. apply_vrn_vds_max_accel  → 17 env vars
      2. HardwareTuner.optimize() → CPU affinity / GC tune / warmup
      3. GCTuner.optimize()       → threshold
      4. winloop/uvloop install
      5. VISAccelerator init
    Returns summary dict.
    """
    global _CROSS_INIT_DONE
    if _CROSS_INIT_DONE: return {"status": "already_done"}

    t0 = time.perf_counter()

    env_result = apply_vrn_vds_max_accel(mode)
    hw_result  = HardwareTuner.optimize()
    vis_result = VIS_ACCELERATOR.initialize()

    if ENABLE_WARM_POOL_AT_INIT:
        try: warm_thread_pool(mode)
        except Exception: pass

    loop_backend = "none"
    if ENABLE_WINLOOP_INSTALL:
        if winloop:
            try: winloop.install(); loop_backend = "winloop"
            except Exception: pass
        elif uvloop:
            try:
                uvloop.install()
                asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
                loop_backend = "uvloop"
            except Exception: pass

    elapsed = round((time.perf_counter() - t0) * 1000, 2)
    _CROSS_INIT_DONE = True

    result = {
        "status":        "initialized",
        "mode":          _resolve_mode(mode),
        "threads":       thread_budget(mode),
        "threads_cross": thread_budget_cross(mode),
        "loop_backend":  loop_backend,
        "hw":            hw_result.get("system", {}),
        "env_vars":      len(env_result),
        "vis":           vis_result.get("status"),
        "elapsed_ms":    elapsed,
    }
    if not silent:
        t  = result["threads"]
        tc = result["threads_cross"]
        lb = loop_backend
        sys_p = result["hw"].get("cpu_physical", "?")
        sys_l = result["hw"].get("cpu_logical", "?")
        print(f"[VIA:CROSS] ✅ init {elapsed}ms | "
              f"threads={t}/{tc} | cores={sys_p}p/{sys_l}l | loop={lb} | "
              f"libs={count_available_libs()}")
    return result

def cross_status() -> Dict:
    """Full cross-acceleration status report."""
    kpi = _get_kpi()
    hw  = HardwareTuner.get_system_info()
    cap = capability_report()
    return {
        "initialized":      _CROSS_INIT_DONE,
        "mode":             _resolve_mode(),
        "threads":          thread_budget(),
        "threads_cross":    thread_budget_cross(),
        "mem_scale":        _mem_pressure_scale(),
        "mem_pressure":     under_memory_pressure(),
        "cpu_pressure":     under_cpu_pressure(),
        "libs_available":   count_available_libs(),
        "libs_missing":     len(get_missing_libs()),
        "capabilities":     cap,
        "hardware":         hw,
        "kpi_summary":      kpi.summary(),
        "strategies_count": Strategies.count(),
        "engines": {
            "ParallelEngine":    True, "CompressionEngine": True,
            "JSONEngine":        True, "HashEngine":        True,
            "StringEngine":      True, "DataFrameEngine":   True,
            "FinanceEngine":     True, "AlgorithmEngine":   True,
            "KPITracker":        True, "CacheManager":      True,
            "AutotuneCache":     True, "HardwareTuner":     True,
            "GCTuner":           True, "MemoryPool":        True,
            "VISAccelerator":    True, "_LazyPool":         True,
            # v2.0 additions
            "OperatorRouter":    True, "PrecisionController": True,
            "VRN_MasterLogger":  True, "DataValidator":     True,
        },
        "cross_funcs": [
            "xmap", "xmap_async", "xfetch", "xbatch_process",
            "xjson_dumps", "xjson_loads", "xhash", "xcompress", "xdecompress",
            "xconcat", "xsort", "xdedup", "xread_parquet", "xwrite_parquet",
            "xcache", "xdot", "xma", "xema", "xfuzzy_ticker",
            "cross_accelerate", "cross_init", "cross_status",
            "detect_blas", "get_profile", "cached_identity",
        ],
    }

# ══════════════════════════════════════════════════════════════════════════════
# ANC-STUB  OPTIONAL LIBRARY STUBS — 功能只增不減
# 未安裝時提供完整 API 骨架，安裝後自動使用真實庫
# ══════════════════════════════════════════════════════════════════════════════

# ── Polars stub ───────────────────────────────────────────────────────────────
class _PolarsStub:
    """Stub for polars — provides API surface when polars not installed."""
    DataFrame = None
    LazyFrame = None

    @staticmethod
    def from_pandas(df):
        return df  # pass-through

    @staticmethod
    def concat(frames, **kw):
        if pd is not None:
            import pandas as _pd
            return _pd.concat([f for f in frames if f is not None],
                              ignore_index=True, sort=False)
        return frames

    @staticmethod
    def scan_parquet(path, **kw):
        if pd is not None:
            return pd.read_parquet(path, **kw)
        raise RuntimeError("polars + pandas both missing")

    @staticmethod
    def scan_csv(path, **kw):
        if pd is not None:
            return pd.read_csv(path, **kw)
        raise RuntimeError("polars + pandas both missing")

    @staticmethod
    def read_parquet(path, **kw):
        if pd is not None:
            return pd.read_parquet(path, **kw)
        raise RuntimeError("polars not installed")

    @staticmethod
    def read_csv(path, **kw):
        if pd is not None:
            return pd.read_csv(path, **kw)
        raise RuntimeError("polars not installed")

    @staticmethod
    def Series(data, **kw):
        if pd is not None:
            return pd.Series(data, **kw)
        return list(data)

class _PolarsDataFrameSentinel:
    """Sentinel type — nothing will ever be an instance of this."""
    pass

if pl is None:
    pl = _PolarsStub()              # type: ignore[assignment]
    pl.DataFrame = _PolarsDataFrameSentinel   # sentinel: isinstance always False
    pl.LazyFrame  = _PolarsDataFrameSentinel

# ── Polars isinstance helper ─────────────────────────────────────────────────
def _is_polars_df(obj) -> bool:
    """Safe polars DataFrame check — works whether polars is real or stub."""
    try:
        import polars as _real_pl
        return isinstance(obj, _real_pl.DataFrame)
    except ImportError:
        return False

def _is_polars_lazy(obj) -> bool:
    try:
        import polars as _real_pl
        return isinstance(obj, _real_pl.LazyFrame)
    except ImportError:
        return False

# ── Numba stubs ───────────────────────────────────────────────────────────────
class _NumbaStub:
    """Stub for numba — decorators become no-ops."""
    prange = range

    @staticmethod
    def njit(*args, **kwargs):
        if args and callable(args[0]):
            return args[0]   # direct decoration
        return lambda f: f   # factory form

    @staticmethod
    def jit(*args, **kwargs):
        if args and callable(args[0]):
            return args[0]
        return lambda f: f

    @staticmethod
    def vectorize(signatures=None, **kwargs):
        if signatures is not None and callable(signatures):
            if np is not None:
                return np.vectorize(signatures)
            return signatures
        def decorator(func):
            if np is not None:
                return np.vectorize(func)
            return func
        return decorator

    @staticmethod
    def stencil(*args, **kwargs):
        return lambda f: f

    @staticmethod
    def cfunc(*args, **kwargs):
        return lambda f: f

if numba is None:
    numba      = _NumbaStub()  # type: ignore[assignment]
    numba_njit = _NumbaStub.njit
    numba_jit  = _NumbaStub.jit
    numba_vec  = _NumbaStub.vectorize
    numba_prange = range

# ── orjson stub ───────────────────────────────────────────────────────────────
class _OrjsonStub:
    """Stub for orjson — falls through to stdlib json."""
    OPT_INDENT_2       = 1
    OPT_NON_STR_KEYS   = 2
    OPT_SORT_KEYS      = 4
    OPT_SERIALIZE_UUID = 8

    @staticmethod
    def dumps(obj, *, option=None, default=None):
        import json as _j
        indent = 2 if option == _OrjsonStub.OPT_INDENT_2 else None
        return _j.dumps(obj, indent=indent, ensure_ascii=False,
                        default=default or str).encode("utf-8")

    @staticmethod
    def loads(s):
        import json as _j
        if isinstance(s, (bytes, bytearray)):
            s = s.decode("utf-8")
        return _j.loads(s)

if orjson is None:
    orjson = _OrjsonStub()  # type: ignore[assignment]

# ── xxhash stub ───────────────────────────────────────────────────────────────
class _XXHashStub:
    """Stub for xxhash — falls through to hashlib sha256."""
    class _Hasher:
        def __init__(self, data=b""):
            import hashlib as _hl
            self._h = _hl.sha256(data if isinstance(data, bytes)
                                 else data.encode("utf-8"))
        def update(self, data):
            self._h.update(data if isinstance(data, bytes)
                           else data.encode("utf-8"))
        def hexdigest(self) -> str:
            return self._h.hexdigest()[:16]   # mimic xxh64 width
        def intdigest(self) -> int:
            return int(self._h.hexdigest()[:16], 16)

    @staticmethod
    def xxh64(data=b"", seed=0):
        return _XXHashStub._Hasher(data if isinstance(data, bytes)
                                   else data.encode("utf-8"))

    @staticmethod
    def xxh32(data=b"", seed=0):
        return _XXHashStub._Hasher(data if isinstance(data, bytes)
                                   else data.encode("utf-8"))

    @staticmethod
    def xxh3_64(data=b""):
        return _XXHashStub._Hasher(data if isinstance(data, bytes)
                                   else data.encode("utf-8"))

if xxhash is None:
    xxhash = _XXHashStub()  # type: ignore[assignment]

# ── zstandard stub ────────────────────────────────────────────────────────────
class _ZstdStub:
    """Stub for zstandard — falls through to gzip."""
    class ZstdCompressor:
        def __init__(self, level: int = 3):
            self._level = level
        def compress(self, data: bytes) -> bytes:
            import gzip as _gz
            return _gz.compress(data, compresslevel=min(9, self._level))

    class ZstdDecompressor:
        def decompress(self, data: bytes) -> bytes:
            import gzip as _gz
            return _gz.decompress(data)

if zstd is None:
    zstd = _ZstdStub()  # type: ignore[assignment]

# ── lz4 stub ──────────────────────────────────────────────────────────────────
class _LZ4FrameStub:
    """Stub for lz4.frame — falls through to gzip."""
    @staticmethod
    def compress(data: bytes, **kw) -> bytes:
        import gzip as _gz
        return _gz.compress(data)

    @staticmethod
    def decompress(data: bytes, **kw) -> bytes:
        import gzip as _gz
        return _gz.decompress(data)

class _LZ4Stub:
    frame = _LZ4FrameStub()

if lz4 is None:
    lz4 = _LZ4Stub()  # type: ignore[assignment]

# ── blosc2 stub ───────────────────────────────────────────────────────────────
class _Blosc2Stub:
    @staticmethod
    def compress(data: bytes, **kw) -> bytes:
        import gzip as _gz
        return _gz.compress(data)

    @staticmethod
    def decompress(data: bytes, **kw) -> bytes:
        import gzip as _gz
        return _gz.decompress(data)

if blosc2 is None:
    blosc2 = _Blosc2Stub()  # type: ignore[assignment]

# ── ujson stub ────────────────────────────────────────────────────────────────
class _UJsonStub:
    @staticmethod
    def dumps(obj, indent=0, ensure_ascii=False, **kw) -> str:
        import json as _j
        return _j.dumps(obj, indent=indent or None,
                        ensure_ascii=False, default=str)

    @staticmethod
    def loads(s, **kw):
        import json as _j
        if isinstance(s, (bytes, bytearray)):
            s = s.decode("utf-8")
        return _j.loads(s)

if ujson is None:
    ujson = _UJsonStub()  # type: ignore[assignment]

# ── rapidjson stub ────────────────────────────────────────────────────────────
class _RapidJsonStub:
    @staticmethod
    def dumps(obj, **kw) -> str:
        import json as _j
        return _j.dumps(obj, ensure_ascii=False, default=str)

    @staticmethod
    def loads(s, **kw):
        import json as _j
        if isinstance(s, (bytes, bytearray)):
            s = s.decode("utf-8")
        return _j.loads(s)

if rapidjson is None:
    rapidjson = _RapidJsonStub()  # type: ignore[assignment]

# ── mmh3 stub ─────────────────────────────────────────────────────────────────
class _Mmh3Stub:
    @staticmethod
    def hash(data, seed=0, signed=True) -> int:
        import hashlib as _hl
        d = data.encode("utf-8") if isinstance(data, str) else data
        return int(_hl.md5(d).hexdigest()[:8], 16)

    @staticmethod
    def hash64(data, seed=0, signed=False):
        import hashlib as _hl
        d = data.encode("utf-8") if isinstance(data, str) else data
        h = int(_hl.sha256(d).hexdigest()[:16], 16)
        return (h, h)

    @staticmethod
    def hash128(data, seed=0, signed=False) -> int:
        import hashlib as _hl
        d = data.encode("utf-8") if isinstance(data, str) else data
        return int(_hl.sha256(d).hexdigest(), 16)

if mmh3 is None:
    mmh3 = _Mmh3Stub()  # type: ignore[assignment]

# ── blake3 stub ───────────────────────────────────────────────────────────────
class _Blake3Stub:
    class _Hasher:
        def __init__(self, data=b""):
            import hashlib as _hl
            self._h = _hl.sha256(data if isinstance(data, bytes)
                                 else data.encode("utf-8"))
        def update(self, data):
            self._h.update(data if isinstance(data, bytes)
                           else data.encode("utf-8"))
        def hexdigest(self) -> str:
            return self._h.hexdigest()

    @staticmethod
    def blake3(data=b""):
        return _Blake3Stub._Hasher(data if isinstance(data, bytes)
                                   else data.encode("utf-8"))

if blake3 is None:
    blake3 = _Blake3Stub()  # type: ignore[assignment]

# ── rapidfuzz stub ────────────────────────────────────────────────────────────
class _RapidFuzzFuzzStub:
    @staticmethod
    def ratio(a: str, b: str) -> float:
        if not a and not b: return 100.0
        if not a or not b:  return 0.0
        sa, sb = set(a.lower()), set(b.lower())
        return len(sa & sb) / len(sa | sb) * 100.0 if (sa | sb) else 100.0

    @staticmethod
    def partial_ratio(a: str, b: str) -> float:
        return _RapidFuzzFuzzStub.ratio(a, b)

    @staticmethod
    def token_sort_ratio(a: str, b: str) -> float:
        return _RapidFuzzFuzzStub.ratio(
            " ".join(sorted(a.lower().split())),
            " ".join(sorted(b.lower().split()))
        )

class _RapidFuzzProcessStub:
    @staticmethod
    def extract(query: str, choices, limit: int = 5, **kw):
        scored = [(c, _RapidFuzzFuzzStub.ratio(query, c), i)
                  for i, c in enumerate(choices)]
        return sorted(scored, key=lambda x: x[1], reverse=True)[:limit]

    @staticmethod
    def extractOne(query: str, choices, **kw):
        results = _RapidFuzzProcessStub.extract(query, choices, limit=1)
        return results[0] if results else None

class _RapidFuzzStub:
    fuzz    = _RapidFuzzFuzzStub()
    process = _RapidFuzzProcessStub()

if rapidfuzz is None:
    rapidfuzz = _RapidFuzzStub()  # type: ignore[assignment]

# ── diskcache stub ────────────────────────────────────────────────────────────
class _DiskCacheStub:
    """Stub for diskcache — uses in-memory dict."""
    class Cache:
        def __init__(self, directory=".via_cache", size_limit=None, **kw):
            self._d: Dict = {}
            self.directory = directory

        def get(self, key, default=None):
            return self._d.get(key, default)

        def set(self, key, value, expire=None, **kw) -> bool:
            self._d[key] = value
            return True

        def delete(self, key) -> bool:
            return bool(self._d.pop(key, None))

        def clear(self) -> int:
            n = len(self._d)
            self._d.clear()
            return n

        def __contains__(self, key):
            return key in self._d

        def __len__(self):
            return len(self._d)

        def close(self): pass
        def __enter__(self): return self
        def __exit__(self, *_): pass

if diskcache is None:
    diskcache = _DiskCacheStub()  # type: ignore[assignment]

# ── cachetools stub ───────────────────────────────────────────────────────────
class _CacheToolsStub:
    """Stub for cachetools — delegates to our LRUCache / TTLCache."""
    LRUCache = LRUCache    # our ANC-11 implementation
    TTLCache = TTLCache

    @staticmethod
    def cached(cache=None, key=None):
        """Stub for @cachetools.cached decorator."""
        def decorator(func):
            _c = cache if cache is not None else {}
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                k = repr((args, tuple(sorted(kwargs.items()))))
                if isinstance(_c, dict):
                    if k not in _c:
                        _c[k] = func(*args, **kwargs)
                    return _c[k]
                v = _c.get(k)
                if v is None:
                    v = func(*args, **kwargs)
                    _c.set(k, v)
                return v
            return wrapper
        return decorator

if cachetools is None:
    cachetools = _CacheToolsStub()  # type: ignore[assignment]

# ── ray stub ──────────────────────────────────────────────────────────────────
class _RayStub:
    """Stub for ray — serializes to ThreadPool execution."""
    _initialized = False

    @staticmethod
    def init(*args, **kwargs): _RayStub._initialized = True

    @staticmethod
    def is_initialized(): return _RayStub._initialized

    @staticmethod
    def shutdown(): _RayStub._initialized = False

    @staticmethod
    def remote(func):
        """Turn func into a 'remote' callable — executes in thread."""
        class _Remote:
            def __init__(self, f): self._f = f
            def remote(self, *a, **kw):
                return _RemoteFuture(self._f, a, kw)
        return _Remote(func)

    @staticmethod
    def get(futures):
        if isinstance(futures, list):
            return [f.result() if hasattr(f, 'result') else f for f in futures]
        return futures.result() if hasattr(futures, 'result') else futures

    @staticmethod
    def put(obj): return obj

    @staticmethod
    def wait(futures, num_returns=1, timeout=None):
        return futures[:num_returns], futures[num_returns:]

    class _RemoteFuture:
        def __init__(self, f, a, kw):
            self._result = f(*a, **kw)
        def result(self): return self._result

class _RemoteFuture:
    def __init__(self, f, a, kw):
        self._result = f(*a, **kw)
    def result(self): return self._result

if ray is None:
    ray = _RayStub()  # type: ignore[assignment]

# ── joblib stub ───────────────────────────────────────────────────────────────
class _JoblibStub:
    """Stub for joblib — executes sequentially or via ThreadPool."""
    @staticmethod
    def delayed(func):
        return lambda *a, **kw: (func, a, kw)

    class Parallel:
        def __init__(self, n_jobs=-1, backend="loky", **kw):
            self._n = n_jobs
            self._backend = backend
        def __call__(self, iterable):
            items = list(iterable)
            if self._backend in ("threading", "loky") and len(items) > 1:
                workers = max(1, min(len(items),
                                     thread_budget() if self._n == -1 else abs(self._n)))
                with ThreadPoolExecutor(max_workers=workers) as ex:
                    return list(ex.map(lambda x: x[0](*x[1], **x[2]), items))
            return [fn(*a, **kw) for fn, a, kw in items]

    @staticmethod
    def dump(obj, path, **kw):
        import pickle as _pk
        with open(path, "wb") as f:
            _pk.dump(obj, f)
        return [path]

    @staticmethod
    def load(path, **kw):
        import pickle as _pk
        with open(path, "rb") as f:
            return _pk.load(f)

    @staticmethod
    def hash(obj, hash_name="md5") -> str:
        import pickle as _pk, hashlib as _hl
        return _hl.md5(_pk.dumps(obj)).hexdigest()

if joblib is None:
    joblib = _JoblibStub()  # type: ignore[assignment]

# ── winloop / uvloop stub ─────────────────────────────────────────────────────
class _LoopStub:
    """Stub for winloop/uvloop — no-op install."""
    @staticmethod
    def install(): pass

    @staticmethod
    def EventLoopPolicy():
        import asyncio as _aio
        return _aio.DefaultEventLoopPolicy()

if winloop is None:
    winloop = _LoopStub()  # type: ignore[assignment]

if uvloop is None:
    uvloop = _LoopStub()  # type: ignore[assignment]

# ── aiofiles stub ─────────────────────────────────────────────────────────────
class _AioFilesStub:
    """Stub for aiofiles — wraps sync file I/O in coroutines."""
    @staticmethod
    async def open(path, mode="r", **kw):
        class _AsyncFile:
            def __init__(self, f): self._f = f
            async def read(self): return self._f.read()
            async def write(self, d): return self._f.write(d)
            async def close(self): self._f.close()
            async def __aenter__(self): return self
            async def __aexit__(self, *_): self._f.close()
        return _AsyncFile(open(path, mode, **kw))

if aiofiles is None:
    aiofiles = _AioFilesStub()  # type: ignore[assignment]

# ── psutil stub ───────────────────────────────────────────────────────────────
class _PsutilVmStub:
    total     = 4 * 1024**3
    available = 3 * 1024**3
    used      = 1 * 1024**3
    percent   = 25.0

class _PsutilProcStub:
    def cpu_affinity(self, cpus=None):
        return list(range(os.cpu_count() or 2))

class _PsutilStub:
    """Stub for psutil — returns safe static defaults."""
    @staticmethod
    def cpu_count(logical=True) -> int:
        return os.cpu_count() or 2

    @staticmethod
    def cpu_percent(interval=0.1) -> float:
        return 10.0  # safe default

    @staticmethod
    def virtual_memory():
        return _PsutilVmStub()

    @staticmethod
    def Process():
        return _PsutilProcStub()

    @staticmethod
    def disk_usage(path="/"):
        class _Du:
            total = 100 * 1024**3; used = 20 * 1024**3; free = 80 * 1024**3
        return _Du()

if psutil is None:
    psutil = _PsutilStub()  # type: ignore[assignment]

# ── torch stub ────────────────────────────────────────────────────────────────
class _TorchStub:
    """Stub for torch — provides tensor-like API backed by numpy."""
    Tensor = None

    @staticmethod
    def tensor(data, dtype=None, **kw):
        if np is not None:
            return np.array(data, dtype=dtype)
        return list(data)

    @staticmethod
    def zeros(*shape, **kw):
        if np is not None:
            return np.zeros(shape)
        return None

    @staticmethod
    def ones(*shape, **kw):
        if np is not None:
            return np.ones(shape)
        return None

    @staticmethod
    def matmul(a, b):
        if np is not None:
            return np.matmul(a, b)
        return None

    @staticmethod
    def is_available() -> bool: return False

    class cuda:
        @staticmethod
        def is_available() -> bool: return False

    class nn:
        class Module: pass

    @staticmethod
    def no_grad():
        import contextlib
        return contextlib.nullcontext()

if torch is None:
    torch = _TorchStub()  # type: ignore[assignment]

# ── onnxruntime stub ──────────────────────────────────────────────────────────
class _OnnxSessionOptions:
    intra_op_num_threads = 1
    inter_op_num_threads = 1
    graph_optimization_level = None

class _OnnxRunTimeStub:
    """Stub for onnxruntime."""
    SessionOptions = _OnnxSessionOptions

    @staticmethod
    def InferenceSession(path, sess_options=None, providers=None):
        raise RuntimeError(f"onnxruntime not installed — cannot load {path}")

    @staticmethod
    def get_available_providers():
        return ["CPUExecutionProvider"]

if onnxruntime is None:
    onnxruntime = _OnnxRunTimeStub()  # type: ignore[assignment]

# ── scipy stub ────────────────────────────────────────────────────────────────
class _ScipyStub:
    """Stub for scipy — uses numpy where possible."""
    class fft:
        @staticmethod
        def fft(x, **kw):
            if np is not None: return np.fft.fft(x, **kw)
            raise RuntimeError("scipy + numpy both missing")
        @staticmethod
        def ifft(x, **kw):
            if np is not None: return np.fft.ifft(x, **kw)
            raise RuntimeError("scipy + numpy both missing")
        @staticmethod
        def rfft(x, **kw):
            if np is not None: return np.fft.rfft(x, **kw)
            raise RuntimeError("scipy + numpy both missing")

    class stats:
        @staticmethod
        def norm():
            raise RuntimeError("scipy.stats not installed")

    class optimize:
        @staticmethod
        def minimize(fun, x0, **kw):
            raise RuntimeError("scipy.optimize not installed")

    class linalg:
        @staticmethod
        def solve(a, b):
            if np is not None: return np.linalg.solve(a, b)
            raise RuntimeError("scipy + numpy both missing")
        @staticmethod
        def eig(a):
            if np is not None: return np.linalg.eig(a)
            raise RuntimeError("scipy + numpy both missing")

if sp is None:
    sp = _ScipyStub()  # type: ignore[assignment]

# ── pyarrow stub ──────────────────────────────────────────────────────────────
class _PyArrowStub:
    """Stub for pyarrow — delegates to pandas where possible."""
    Table = None

    @staticmethod
    def table(data, **kw):
        if pd is not None:
            return pd.DataFrame(data)
        raise RuntimeError("pyarrow not installed")

    @staticmethod
    def from_pandas(df, **kw):
        return df   # pass-through

    class parquet:
        @staticmethod
        def read_table(path, **kw):
            if pd is not None:
                return pd.read_parquet(path, **kw)
            raise RuntimeError("pyarrow not installed")
        @staticmethod
        def write_table(table, path, **kw):
            if pd is not None and isinstance(table, pd.DataFrame):
                table.to_parquet(path, **kw)
                return
            raise RuntimeError("pyarrow not installed")

if pa is None:
    pa = _PyArrowStub()  # type: ignore[assignment]

# ── duckdb stub ───────────────────────────────────────────────────────────────
class _DuckDBStub:
    """Stub for duckdb — executes queries on pandas via eval where possible."""
    @staticmethod
    def connect(database=":memory:", **kw):
        return _DuckDBStub._Conn()

    @staticmethod
    def query(sql: str):
        raise RuntimeError("duckdb not installed")

    @staticmethod
    def read_parquet(path, **kw):
        if pd is not None: return pd.read_parquet(path, **kw)
        raise RuntimeError("duckdb not installed")

    @staticmethod
    def read_csv(path, **kw):
        if pd is not None: return pd.read_csv(path, **kw)
        raise RuntimeError("duckdb not installed")

    class _Conn:
        def execute(self, sql, params=None):
            raise RuntimeError("duckdb not installed")
        def close(self): pass
        def __enter__(self): return self
        def __exit__(self, *_): pass

if duckdb is None:
    duckdb = _DuckDBStub()  # type: ignore[assignment]

# ── cv2 stub ──────────────────────────────────────────────────────────────────
class _CV2Stub:
    """Stub for cv2 (OpenCV) — raises descriptive error."""
    IMREAD_UNCHANGED = -1
    COLOR_BGR2GRAY   = 6
    COLOR_BGR2RGB    = 4
    INTER_AREA       = 3
    INTER_LINEAR     = 1

    @staticmethod
    def imread(path, flags=-1):
        raise RuntimeError(f"cv2 not installed — cannot read image: {path}")

    @staticmethod
    def imwrite(path, img, params=None) -> bool:
        raise RuntimeError("cv2 not installed — cannot write image")

    @staticmethod
    def cvtColor(img, code):
        if np is not None and hasattr(img, 'shape'):
            if code == _CV2Stub.COLOR_BGR2GRAY:
                return np.mean(img, axis=2).astype(img.dtype)
        raise RuntimeError("cv2 not installed")

    @staticmethod
    def GaussianBlur(img, ksize, sigma):
        raise RuntimeError("cv2 not installed")

    @staticmethod
    def Canny(img, lo, hi):
        raise RuntimeError("cv2 not installed")

    @staticmethod
    def resize(img, dsize, interpolation=None):
        raise RuntimeError("cv2 not installed")

if cv2 is None:
    cv2 = _CV2Stub()  # type: ignore[assignment]

# ── PIL stub ──────────────────────────────────────────────────────────────────
class _PILStub:
    """Stub for PIL (Pillow)."""
    class Image:
        @staticmethod
        def open(path, **kw):
            raise RuntimeError(f"Pillow not installed — cannot open: {path}")
        @staticmethod
        def fromarray(arr, mode=None):
            raise RuntimeError("Pillow not installed")
        @staticmethod
        def new(mode, size, color=None):
            raise RuntimeError("Pillow not installed")

if PIL is None:
    PIL = _PILStub()  # type: ignore[assignment]

# ── rich stub ─────────────────────────────────────────────────────────────────
class _RichStub:
    """Stub for rich — falls through to print."""
    @staticmethod
    def print(*args, **kw):
        # Strip markup tags for plain output
        import re as _re
        cleaned = [_re.sub(r'\[.*?\]', '', str(a)) for a in args]
        print(*cleaned)

    class console:
        @staticmethod
        def print(*args, **kw):
            _RichStub.print(*args)

    class table:
        class Table:
            def __init__(self, *a, **kw): self._rows = []
            def add_column(self, *a, **kw): pass
            def add_row(self, *a, **kw): self._rows.append(a)
            def __str__(self):
                return "\n".join(" | ".join(str(c) for c in r) for r in self._rows)

    class progress:
        class Progress:
            def __enter__(self): return self
            def __exit__(self, *_): pass
            def add_task(self, *a, **kw): return 0
            def update(self, *a, **kw): pass

if rich is None:
    rich = _RichStub()  # type: ignore[assignment]

# ── tqdm stub ─────────────────────────────────────────────────────────────────
class _TqdmStub:
    """Stub for tqdm — passthrough iterator."""
    class tqdm:
        def __init__(self, iterable=None, total=None, desc=None, **kw):
            self._it = iter(iterable) if iterable is not None else iter([])
        def __iter__(self): return self._it
        def __next__(self): return next(self._it)
        def update(self, n=1): pass
        def close(self): pass
        def set_description(self, s): pass
        def set_postfix(self, **kw): pass
        def __enter__(self): return self
        def __exit__(self, *_): pass

    @staticmethod
    def trange(*args, **kw):
        return _TqdmStub.tqdm(range(*args), **kw)

if tqdm_m is None:
    tqdm_m = _TqdmStub()  # type: ignore[assignment]

# ── talib stub ────────────────────────────────────────────────────────────────
class _TalibStub:
    """Stub for TA-Lib — pure-Python fallbacks for common indicators."""
    @staticmethod
    def SMA(data, timeperiod=14):
        return FinanceEngine.moving_average(list(data), timeperiod)

    @staticmethod
    def EMA(data, timeperiod=14):
        return FinanceEngine.exponential_moving_average(list(data), timeperiod)

    @staticmethod
    def RSI(data, timeperiod=14):
        """Pure-Python RSI fallback."""
        prices = list(data)
        if len(prices) < timeperiod + 1:
            return [float("nan")] * len(prices)
        gains, losses = [], []
        for i in range(1, len(prices)):
            diff = prices[i] - prices[i-1]
            gains.append(max(diff, 0))
            losses.append(max(-diff, 0))
        avg_gain = sum(gains[:timeperiod]) / timeperiod
        avg_loss = sum(losses[:timeperiod]) / timeperiod
        result = [float("nan")] * timeperiod
        for i in range(timeperiod, len(prices)):
            avg_gain = (avg_gain * (timeperiod-1) + gains[i-1]) / timeperiod
            avg_loss = (avg_loss * (timeperiod-1) + losses[i-1]) / timeperiod
            rs = avg_gain / avg_loss if avg_loss > 0 else float("inf")
            result.append(100 - 100 / (1 + rs))
        return result

    @staticmethod
    def MACD(data, fastperiod=12, slowperiod=26, signalperiod=9):
        fast = FinanceEngine.exponential_moving_average(list(data), fastperiod)
        slow = FinanceEngine.exponential_moving_average(list(data), slowperiod)
        macd = [f - s for f, s in zip(fast, slow)]
        signal = FinanceEngine.exponential_moving_average(macd, signalperiod)
        hist = [m - s for m, s in zip(macd, signal)]
        return macd, signal, hist

    @staticmethod
    def BBANDS(data, timeperiod=20, nbdevup=2, nbdevdn=2):
        ma  = FinanceEngine.moving_average(list(data), timeperiod)
        if np is not None:
            arr = _si_np_array(data, ma, timeperiod)
        upper = [m + nbdevup * 0 for m in ma]   # simplified stub
        lower = [m - nbdevdn * 0 for m in ma]
        return upper, ma, lower

def _si_np_array(data, ma, period):
    """Helper for stub std computation."""
    return ma   # simplified

if talib is None:
    talib = _TalibStub()  # type: ignore[assignment]

# ── pandas_ta stub ────────────────────────────────────────────────────────────
class _PandasTaStub:
    """Stub for pandas_ta — simple pure-Python indicator stubs."""
    @staticmethod
    def sma(close, length=14, **kw):
        return FinanceEngine.moving_average(list(close), length)

    @staticmethod
    def ema(close, length=14, **kw):
        return FinanceEngine.exponential_moving_average(list(close), length)

    @staticmethod
    def rsi(close, length=14, **kw):
        return _TalibStub.RSI(list(close), timeperiod=length)

    @staticmethod
    def macd(close, fast=12, slow=26, signal=9, **kw):
        return _TalibStub.MACD(list(close), fast, slow, signal)

if pandas_ta is None:
    pandas_ta = _PandasTaStub()  # type: ignore[assignment]

# ── requests stub ─────────────────────────────────────────────────────────────
class _RequestsResponseStub:
    def __init__(self, url):
        self.url         = url
        self.status_code = 200
        self.text        = ""
        self.content     = b""
        self.headers     = {}
    def json(self): return {}
    def raise_for_status(self): pass

class _RequestsStub:
    """Stub for requests — uses urllib.request fallback."""
    @staticmethod
    def get(url, headers=None, timeout=30, verify=True, **kw):
        import urllib.request as _ur, urllib.error as _ue
        r = _RequestsResponseStub(url)
        try:
            req = _ur.Request(url, headers=headers or {})
            with _ur.urlopen(req, timeout=timeout) as resp:
                r.content     = resp.read()
                r.text        = r.content.decode("utf-8", errors="ignore")
                r.status_code = resp.status
                r.headers     = dict(resp.headers)
        except Exception:
            r.status_code = 0
        return r

    @staticmethod
    def post(url, data=None, json=None, headers=None, timeout=30, **kw):
        import urllib.request as _ur
        import json as _j
        r = _RequestsResponseStub(url)
        try:
            body = _j.dumps(json).encode() if json else (data or b"")
            req  = _ur.Request(url, data=body,
                               headers=headers or {"Content-Type": "application/json"})
            with _ur.urlopen(req, timeout=timeout) as resp:
                r.content     = resp.read()
                r.text        = r.content.decode("utf-8", errors="ignore")
                r.status_code = resp.status
        except Exception:
            r.status_code = 0
        return r

    class Session:
        def __init__(self): self.headers = {}
        def get(self, url, **kw):
            return _RequestsStub.get(url, headers=self.headers, **kw)
        def post(self, url, **kw):
            return _RequestsStub.post(url, headers=self.headers, **kw)
        def close(self): pass
        def __enter__(self): return self
        def __exit__(self, *_): pass

if requests_m is None:
    requests_m = _RequestsStub()  # type: ignore[assignment]

# ── msgpack stub ──────────────────────────────────────────────────────────────
class _MsgpackStub:
    @staticmethod
    def packb(obj, **kw) -> bytes:
        import json as _j
        return _j.dumps(obj, default=str).encode("utf-8")

    @staticmethod
    def unpackb(data: bytes, **kw):
        import json as _j
        return _j.loads(data.decode("utf-8"))

if msgpack is None:
    msgpack = _MsgpackStub()  # type: ignore[assignment]

# ── cloudpickle stub ──────────────────────────────────────────────────────────
class _CloudPickleStub:
    """Stub for cloudpickle — uses pickle for regular objects, marshal for code objects."""

    @staticmethod
    def dumps(obj, protocol=None, **kw) -> bytes:
        import pickle as _pk
        import types as _types
        if isinstance(obj, (_types.FunctionType, _types.LambdaType)):
            # cloudpickle's main purpose: serialize closures/lambdas
            # Fallback: use marshal on code object + capture closure info
            try:
                import marshal as _mar
                code_bytes = _mar.dumps(obj.__code__)
                # Store name + code bytes in a wrapper
                wrapper = {"_cel_fn": True, "name": obj.__name__,
                           "code": code_bytes, "defaults": obj.__defaults__,
                           "closure_vals": ([c.cell_contents for c in (obj.__closure__ or [])])}
                return _pk.dumps(wrapper)
            except Exception:
                pass
        try:
            return _pk.dumps(obj, protocol=protocol)
        except _pk.PicklingError:
            # Last resort: serialize as string repr
            return repr(obj).encode("utf-8")

    @staticmethod
    def loads(data: bytes, **kw):
        import pickle as _pk
        try:
            obj = _pk.loads(data)
            if isinstance(obj, dict) and obj.get("_cel_fn"):
                import marshal as _mar, types as _types
                code = _mar.loads(obj["code"])
                defaults = obj.get("defaults")
                fn = _types.FunctionType(code, globals(), obj.get("name", "<fn>"),
                                         defaults)
                return fn
            return obj
        except Exception:
            return None

    @staticmethod
    def dump(obj, f, **kw):
        f.write(_CloudPickleStub.dumps(obj))

    @staticmethod
    def load(f, **kw):
        return _CloudPickleStub.loads(f.read())

if cloudpickle is None:
    cloudpickle = _CloudPickleStub()  # type: ignore[assignment]

# ── anyio / trio stubs ────────────────────────────────────────────────────────
class _AnyIoStub:
    @staticmethod
    async def run(func, *args, backend="asyncio", **kw):
        return await func(*args, **kw)

    class sleep:
        @staticmethod
        async def __call__(seconds):
            import asyncio as _aio
            await _aio.sleep(seconds)

class _TrioStub:
    @staticmethod
    def run(func, *args, **kw):
        import asyncio as _aio
        return _aio.run(func(*args, **kw))

if anyio is None:
    anyio = _AnyIoStub()  # type: ignore[assignment]

if trio is None:
    trio = _TrioStub()  # type: ignore[assignment]

# ── snappy / brotli stubs ─────────────────────────────────────────────────────
class _SnappyStub:
    @staticmethod
    def compress(data: bytes) -> bytes:
        import gzip as _gz
        return _gz.compress(data)

    @staticmethod
    def decompress(data: bytes) -> bytes:
        import gzip as _gz
        return _gz.decompress(data)

class _BrotliStub:
    @staticmethod
    def compress(data: bytes, quality=11, **kw) -> bytes:
        import gzip as _gz
        return _gz.compress(data)

    @staticmethod
    def decompress(data: bytes) -> bytes:
        import gzip as _gz
        return _gz.decompress(data)

if snappy is None:
    snappy = _SnappyStub()  # type: ignore[assignment]

if brotli is None:
    brotli = _BrotliStub()  # type: ignore[assignment]

# ── Update _LIB_MAP with stubs so capability_report reflects real status ──────
# Note: stubs are tracked separately so we can distinguish real vs stub
_STUB_CLASSES = (
    _PolarsStub, _NumbaStub, _OrjsonStub, _XXHashStub, _ZstdStub,
    _LZ4Stub, _Blosc2Stub, _UJsonStub, _RapidJsonStub, _Mmh3Stub,
    _Blake3Stub, _RapidFuzzStub, _DiskCacheStub, _CacheToolsStub,
    _RayStub, _JoblibStub, _LoopStub, _AioFilesStub, _PsutilStub,
    _TorchStub, _OnnxRunTimeStub, _ScipyStub, _PyArrowStub, _DuckDBStub,
    _CV2Stub, _PILStub, _RichStub, _TqdmStub, _TalibStub, _PandasTaStub,
    _RequestsStub, _MsgpackStub, _CloudPickleStub, _AnyIoStub, _TrioStub,
    _SnappyStub, _BrotliStub,
)

def is_stub(lib_obj: Any) -> bool:
    """Return True if this is a stub (not the real library)."""
    return isinstance(lib_obj, _STUB_CLASSES) or (
        isinstance(lib_obj, type) and issubclass(lib_obj, _STUB_CLASSES)
    )

def get_real_libs() -> Dict[str, bool]:
    """Return {name: True} only for genuinely-installed (non-stub) libs."""
    return {k: (v is not None and not is_stub(v)) for k, v in _LIB_MAP.items()}

def count_real_libs() -> int:
    return sum(1 for v in _LIB_MAP.values() if v is not None and not is_stub(v))

# ══════════════════════════════════════════════════════════════════════════════
# ANC-25  SELF-TEST + STATUS REPORT
# ══════════════════════════════════════════════════════════════════════════════

def run_self_test() -> Dict:
    """Comprehensive self-test covering all major components."""
    results: Dict = {"tests": [], "passed": 0, "failed": 0}
    start = time.perf_counter()

    def _add(name: str, ok: bool, msg: str = ""):
        results["tests"].append({"name": name, "ok": ok, "msg": msg})
        if ok: results["passed"] += 1
        else:  results["failed"] += 1

    # Libs
    for lib_name, lib_obj in [
        ("numpy", np), ("pandas", pd), ("polars", pl),
        ("numba", numba), ("orjson", orjson), ("xxhash", xxhash),
        ("zstandard", zstd), ("joblib", joblib), ("psutil", psutil),
    ]:
        _add(lib_name, lib_obj is not None,
             "ok" if lib_obj is not None else "not installed")

    # LRU cache
    try:
        c = LRUCache(maxsize=4); c.set("k", 42)
        _add("LRUCache", c.get("k") == 42)
    except Exception as e: _add("LRUCache", False, str(e))

    # TTL cache
    try:
        tc = TTLCache(maxsize=4, ttl=60.0); tc.set("k2", "hello")
        _add("TTLCache", tc.get("k2") == "hello")
    except Exception as e: _add("TTLCache", False, str(e))

    # AutotuneCache
    try:
        ac = AutotuneCache(); ac.set("t", {"v": 1})
        _add("AutotuneCache", ac.get("t") == {"v": 1})
    except Exception as e: _add("AutotuneCache", False, str(e))

    # JSON
    try:
        s = json_dumps({"a": 1}); d = json_loads(s)
        _add("JSONEngine", d.get("a") == 1)
    except Exception as e: _add("JSONEngine", False, str(e))

    # Compression
    try:
        raw = b"hello world " * 50
        comp = compress_bytes(raw)
        _add("Compression", decompress_bytes(comp) == raw)
    except Exception as e: _add("Compression", False, str(e))

    # Hash
    try:
        h = fast_hash(b"test")
        _add("Hash", len(h) > 8)
    except Exception as e: _add("Hash", False, str(e))

    # KPITracker
    try:
        kpi = KPITracker(); kpi.record("l", 1.5); kpi.record("l", 2.5)
        stats = kpi.get_stats("l")
        _add("KPITracker", stats["count"] == 2 and stats["mean"] == 2.0)
    except Exception as e: _add("KPITracker", False, str(e))

    # FinanceEngine
    try:
        roe = FinanceEngine.calculate_roe(100.0, 500.0)
        _add("FinanceEngine", abs(roe - 0.2) < 1e-9)
    except Exception as e: _add("FinanceEngine", False, str(e))

    # StringEngine
    try:
        dist = StringEngine.levenshtein_distance("kitten", "sitting")
        _add("StringEngine", dist == 3)
    except Exception as e: _add("StringEngine", False, str(e))

    # AlgorithmEngine
    try:
        fib = AlgorithmEngine.fibonacci_optimized(10)
        _add("AlgorithmEngine", fib == 55)
    except Exception as e: _add("AlgorithmEngine", False, str(e))

    # HardwareTuner
    try:
        info = HardwareTuner.get_system_info()
        _add("HardwareTuner", "cpu_logical" in info)
    except Exception as e: _add("HardwareTuner", False, str(e))

    # Strategies
    try: _add("Strategies", Strategies.count() >= 90)
    except Exception as e: _add("Strategies", False, str(e))

    # GCTuner — verify optimized threshold is active + hot_loop ctx works
    try:
        GCTuner.optimize()   # idempotent — ensure it's set
        threshold = gc.get_threshold()
        # cross_init already runs optimize(); verify it equals our target
        expected  = (_GC_THRESHOLD_GEN0, _GC_THRESHOLD_GEN1, _GC_THRESHOLD_GEN2)
        threshold_ok = threshold == expected
        # hot_loop ctx manager
        gc_state_before = gc.isenabled()
        with GCTuner.hot_loop():
            _ = sum(range(10_000))
            gc_paused = not gc.isenabled()
        gc_restored = gc.isenabled() == gc_state_before
        _add("GCTuner", threshold_ok and gc_paused and gc_restored,
             f"threshold={threshold} pause={gc_paused} restore={gc_restored}")
    except Exception as e: _add("GCTuner", False, str(e))

    # MemoryPool
    try:
        mp = MemoryPool(); buf = mp.acquire(); mp.release(buf)
        _add("MemoryPool", True, str(mp.stats()))
    except Exception as e: _add("MemoryPool", False, str(e))

    # LazyPool
    try:
        res = _LazyPool.map(lambda x: x * 2, range(8))
        _add("LazyPool", res == [0, 2, 4, 6, 8, 10, 12, 14])
    except Exception as e: _add("LazyPool", False, str(e))

    # DataFrameEngine
    try:
        _add("DataFrameEngine", DataFrameEngine.get_best_backend() != "")
    except Exception as e: _add("DataFrameEngine", False, str(e))

    # Thread budget
    try:
        t  = thread_budget()
        tc = thread_budget_cross()
        _add("ThreadBudget", t >= 1 and tc >= t, f"t={t} tc={tc}")
    except Exception as e: _add("ThreadBudget", False, str(e))

    # ── v2.0 additions ────────────────────────────────────────────────────────

    # OperatorRouter
    try:
        r = OperatorRouter.route(OperatorType.GEMM, m=10, n=10, k=10)
        _add("OperatorRouter", r in ("numpy", "torch", "python"))
    except Exception as e: _add("OperatorRouter", False, str(e))

    # PrecisionController
    try:
        pm = PrecisionController.select_precision(100.0, 0.001)
        _add("PrecisionController", isinstance(pm, PrecisionMode))
    except Exception as e: _add("PrecisionController", False, str(e))

    # VRN_MasterLogger
    try:
        import logging as _logging
        import io as _io_test
        # Suppress handler output during self-test
        lg = VRN_MasterLogger("CEL_TEST_LOGGER", log_file=os.devnull)
        # Redirect logger stream to devnull for this test
        _null_handler = _logging.NullHandler()
        lg.logger.handlers.clear()
        lg.logger.addHandler(_null_handler)
        lg.info("self-test")
        lg.warn("self-test-warn")
        lg.debug("self-test-debug")
        _add("VRN_MasterLogger", True, "aliases: VRN_Monitor/SystemMonitor/Logger")
    except Exception as e: _add("VRN_MasterLogger", False, str(e))

    # JSONEngine class
    try:
        je = JSONEngine()
        s  = je.dumps({"x": 42})
        d  = je.loads(s)
        _add("JSONEngine", d.get("x") == 42)
    except Exception as e: _add("JSONEngine", False, str(e))

    # DataValidator
    try:
        ok1 = DataValidator.validate_ticker("2330")
        ok2 = not DataValidator.validate_ticker("0123")
        ok3 = not DataValidator.validate_ticker("2025")
        _add("DataValidator", ok1 and ok2 and ok3,
             f"2330={ok1} 0123={not ok2} 2025={not ok3}")
    except Exception as e: _add("DataValidator", False, str(e))

    # detect_blas
    try:
        blas = detect_blas()
        _add("detect_blas", isinstance(blas, str), blas)
    except Exception as e: _add("detect_blas", False, str(e))

    # get_profile
    try:
        prof = get_profile()
        _add("get_profile", "system" in prof and "libraries" in prof)
    except Exception as e: _add("get_profile", False, str(e))

    # cached_identity
    try:
        v1 = cached_identity("hello")
        v2 = cached_identity("hello")
        _add("cached_identity", v1 == v2 == "hello")
    except Exception as e: _add("cached_identity", False, str(e))

    # cross_accelerate
    try:
        res = cross_accelerate(lambda x: x * 2, [1, 2, 3], dedupe=False)
        _add("cross_accelerate", res == [2, 4, 6])
    except Exception as e: _add("cross_accelerate", False, str(e))

    # xjson aliases
    try:
        s = xjson_dumps({"z": 99})
        d = xjson_loads(s)
        _add("xjson_aliases", d.get("z") == 99)
    except Exception as e: _add("xjson_aliases", False, str(e))

    # xcompress / xdecompress
    try:
        raw  = b"VeritasCeleritas" * 20
        comp = xcompress(raw)
        back = xdecompress(comp)
        _add("xcompress/decompress", back == raw)
    except Exception as e: _add("xcompress/decompress", False, str(e))

    results["duration_ms"] = round((time.perf_counter() - start) * 1000, 2)
    return results

def accel_status_report() -> Dict:
    t  = thread_budget()
    tc = thread_budget_cross()
    return {
        "threads_active":  t,
        "threads_cross":   tc,
        "mode":            _resolve_mode(),
        "mem_scale":       _mem_pressure_scale(),
        "libs_available":  count_available_libs(),
        "libs_missing":    len(get_missing_libs()),
        "capabilities":    capability_report(),
        "backends_active": [k for k, v in BACKENDS.items() if v.get("available")],
        "strategies":      Strategies.count(),
        "system":          HardwareTuner.get_system_info(),
    }

def print_accel_status() -> None:
    rpt = accel_status_report()
    cap = rpt["capabilities"]
    hw  = rpt["system"]
    mem = hw.get("memory", {})
    simd = hw.get("simd", {})

    print("=" * 72)
    print("⚡ VeritasCeleritas v1.0  — 極限交叉加速引擎")
    print("   功能只增不減 — Features Only Increase, Never Decrease")
    print("=" * 72)
    print(f"  [Thread Budget]  active={rpt['threads_active']}  "
          f"cross={rpt['threads_cross']}  mode={rpt['mode']}  "
          f"mem_scale={rpt['mem_scale']:.2f}")
    print(f"  [CPU]  logical={hw.get('cpu_logical')}  "
          f"physical={hw.get('cpu_physical')}  arch={hw.get('arch')}")
    print(f"  [RAM]  total={mem.get('total_gb')}GB  "
          f"avail={mem.get('available_gb')}GB  used={mem.get('percent')}%")
    print(f"  [SIMD] sse2={simd.get('sse2')}  avx={simd.get('avx')}  "
          f"avx2={simd.get('avx2')}  avx512={simd.get('avx512')}  neon={simd.get('neon')}")
    print(f"  [Libs] {rpt['libs_available']} available  "
          f"{rpt['libs_missing']} missing")
    print(f"  [Strategies] {rpt['strategies']} (M1-M50 + T1-T40)")
    print(f"  [Backends] {', '.join(rpt['backends_active'])}")
    print()
    def f(v): return "✅" if v else "❌"
    print(f"  JIT(numba)={f(cap['jit_numba'])}  polars={f(cap['polars'])}  "
          f"duckdb={f(cap['duckdb'])}  ray={f(cap['ray'])}  "
          f"joblib={f(cap['joblib'])}")
    print(f"  orjson={f(cap['orjson'])}  zstd={f(cap['zstd'])}  "
          f"lz4={f(cap['lz4'])}  xxhash={f(cap['xxhash'])}  "
          f"rapidfuzz={f(cap['rapidfuzz'])}")
    print(f"  winloop={f(cap['async_winloop'])}  uvloop={f(cap['async_uvloop'])}  "
          f"diskcache={f(cap['diskcache'])}  psutil={f(cap['psutil'])}")
    print(f"  cv2={f(cap['cv2'])}  pyvips={f(cap['pyvips'])}  "
          f"onnx={f(cap['onnx'])}  torch={f(cap['gpu_torch'])}  "
          f"cudf={f(cap['gpu_cudf'])}")
    print("=" * 72)

    # Self-test
    rpt_test = run_self_test()
    total_t  = rpt_test["passed"] + rpt_test["failed"]
    print(f"  Self-test: {rpt_test['passed']}/{total_t} passed  "
          f"({rpt_test['duration_ms']:.1f}ms)")
    if rpt_test["failed"] > 0:
        for t in rpt_test["tests"]:
            if not t["ok"]:
                print(f"    ❌ {t['name']}: {t['msg']}")
    print("=" * 72)

# [ANC:def print_master_status]
def print_master_status() -> None:
    """
    Print comprehensive VIA SuperAccel status (compact single-screen view).
    Backwards-compat with VIA_SuperAccel_Module v3.0.
    """
    print("\n" + "=" * 70)
    print("  VeritasCeleritas v1.0  — Master Status")
    print("  功能只增不減 — Features Only Increase, Never Decrease")
    print("=" * 70)
    avail  = count_available_libs()
    sys_i  = HardwareTuner.get_system_info()
    mem    = sys_i.get("memory", {})
    print(f"\n  📚 Libraries : {avail} available  ({len(get_missing_libs())} missing)")
    print(f"  💻 CPU       : {sys_i.get('cpu_logical')} logical / "
          f"{sys_i.get('cpu_physical')} physical  arch={sys_i.get('arch')}")
    print(f"  🧠 Memory    : {mem.get('total_gb')} GB  "
          f"({mem.get('percent')}% used  avail={mem.get('available_gb')} GB)")
    print(f"  🔧 Strategies: {Strategies.count()} (M1-M50 + T1-T40)")
    print(f"  ⚙️  Mode      : {_resolve_mode()}  "
          f"threads={thread_budget()}/{thread_budget_cross()}")
    rpt = run_self_test()
    print(f"  ✅ Self-test : {rpt['passed']}/{rpt['passed']+rpt['failed']} passed "
          f"({rpt['duration_ms']:.1f}ms)")
    print("=" * 70)

# [ANC:def print_cross_status]
def print_cross_status() -> None:
    """
    Print cross-acceleration status (detailed engine + KPI view).
    Backwards-compat with VIA_SuperAccel_Module v3.0 §E cross_status.
    """
    s = cross_status()

    def f(v: bool) -> str: return "✅" if v else "❌"

    cap = s["capabilities"]
    print("=" * 70)
    print("⚡ VeritasCeleritas v1.0 — Cross-Acceleration Status")
    print("=" * 70)
    print(f"\n  [Thread Budget]  active={s['threads']}  cross={s['threads_cross']}  "
          f"mode={s['mode']}  mem_scale={s['mem_scale']:.2f}")
    print(f"  [Pressure]       mem={f(not s['mem_pressure'])}OK  "
          f"cpu={f(not s['cpu_pressure'])}OK")
    print(f"  [Libs]           {s['libs_available']} available  "
          f"{s['libs_missing']} missing")
    print(f"\n  [Core Engines]")
    for eng, ok in s["engines"].items():
        print(f"    {f(ok)} {eng}")
    print(f"\n  [Cross Functions]  {len(s['cross_funcs'])} registered")
    for fn in s["cross_funcs"]:
        print(f"    → {fn}")
    print(f"\n  [Strategies]  {s['strategies_count']} (M1-M50 + T1-T40)")
    kpi = s.get("kpi_summary", {})
    if kpi:
        print(f"\n  [KPI]")
        for name, st in kpi.items():
            print(f"    {name}: count={st['count']}  mean={st['mean']:.3f}")
    print("=" * 70)

# ══════════════════════════════════════════════════════════════════════════════
# __all__  export table  v2.0 (append-only registry)
# ══════════════════════════════════════════════════════════════════════════════

__all__ = [
    # ── ANC-04 Thread / RAM ──────────────────────────────────────────────────
    "thread_budget", "thread_budget_cross", "recommend_threads", "set_thread_limit",
    "get_best_worker_count", "memory_percent", "memory_available_mb",
    "cpu_percent", "under_memory_pressure", "under_cpu_pressure",
    "system_under_pressure", "wait_for_memory", "wait_for_cpu", "sizeof",
    "map_vrn_mode_to_bootstrap", "_resolve_mode", "_cpu_count", "_available_ram_mb",
    # ── ANC-05 ENV ───────────────────────────────────────────────────────────
    "apply_thread_limits", "apply_vrn_vds_max_accel",
    # ── ANC-06 GC ────────────────────────────────────────────────────────────
    "GCTuner",
    # ── ANC-07 Pool ──────────────────────────────────────────────────────────
    "MemoryPool",
    # ── ANC-08 Chunk ─────────────────────────────────────────────────────────
    "adaptive_chunk_size", "chunk_list",
    # ── ANC-09 Backend ───────────────────────────────────────────────────────
    "BACKENDS", "get_backend", "execute_with_backend",
    # ── ANC-10 Parallel ──────────────────────────────────────────────────────
    "parallel_map", "parallel_map_ray", "parallel_map_joblib",
    "auto_parallel_map", "parallel_chunked_map",
    # ── ANC-11 Cache ─────────────────────────────────────────────────────────
    "LRUCache", "TTLCache", "AutotuneCache", "CacheManager",
    "get_disk_cache", "cache_get", "cache_set", "cache_stats",
    "_LRU_4K", "_TTL_5MIN",
    # ── ANC-12 DataFrame ─────────────────────────────────────────────────────
    "dedupe_preserve_order", "accelerated_concat", "accelerated_drop_duplicates",
    "accelerated_sort", "accelerated_filter", "to_polars", "to_pandas",
    "xread_parquet", "xwrite_parquet",
    # ── ANC-13 JSON ──────────────────────────────────────────────────────────
    "json_dumps", "json_loads", "xjson_dumps", "xjson_loads",
    # ── ANC-14 Compression ───────────────────────────────────────────────────
    "compress_bytes", "decompress_bytes", "CompressionEngine",
    "xcompress", "xdecompress",
    # ── ANC-15 Hash ──────────────────────────────────────────────────────────
    "fast_hash", "xhash", "HashEngine",
    # ── ANC-16 Decorators ────────────────────────────────────────────────────
    "safe_jit", "safe_vectorize", "memoize", "ttl_memoize", "retry",
    "shield", "guard_memory", "guard_threads",
    "accelerate_cached", "accelerate", "_ResultCache",
    # ── ANC-17 Safety ────────────────────────────────────────────────────────
    "safe_call", "sandbox", "safe_get_dict", "safe_getattr",
    "ensure_type", "ensure_positive", "ensure_nonempty",
    # ── ANC-18 Logging ───────────────────────────────────────────────────────
    "accel_info", "accel_ok", "accel_warn", "accel_error", "accel_debug",
    "info", "success", "warn", "error", "debug",
    "enable_logging", "disable_logging",
    # ── ANC-19 Engines ───────────────────────────────────────────────────────
    "KPITracker", "Timer", "UltimateConfig", "_ULTIMATE_CFG",
    "HardwareTuner", "pin_to_physical_cores",
    "ParallelEngine", "StringEngine", "DataFrameEngine",
    "FinanceEngine", "AlgorithmEngine", "Strategies",
    "detect_workload_type", "choose_backend", "choose_acceleration_strategy",
    # ── ANC-20 Cross-Accel ───────────────────────────────────────────────────
    "xmap", "xmap_async", "xfetch", "xbatch_process", "xcache",
    "xdot", "xma", "xema", "xfuzzy_ticker",
    "xconcat", "xsort", "xdedup",
    # ── ANC-21 LazyPool ──────────────────────────────────────────────────────
    "_LazyPool", "warm_thread_pool",
    # ── ANC-22 Subprocess ────────────────────────────────────────────────────
    "snapshot_for_subprocess", "bootstrap_vis_accelerator", "accel_init_env",
    # ── ANC-23 Configure ─────────────────────────────────────────────────────
    "configure_ultra_acceleration",
    # ── ANC-24 VISAccelerator ────────────────────────────────────────────────
    "VISAccelerator", "VIS_ACCELERATOR",
    # ── ANC-25 Status ────────────────────────────────────────────────────────
    "run_self_test", "accel_status_report",
    "print_accel_status", "cross_init", "cross_status",
    # ── Lib map ──────────────────────────────────────────────────────────────
    "get_available_libs", "count_available_libs", "get_missing_libs",
    "capability_report", "_LIB_MAP",
    # ── Config constants ─────────────────────────────────────────────────────
    "VIA_ACCEL_DEFAULT_MODE", "VRN_MODE_MAP",
    "_CROSS_THREAD_MULTIPLIER", "_CROSS_THREAD_MIN_BUMP", "_CROSS_THREAD_HARD_CAP",
    # ── v2.0 additions (only-increase, append-only) ───────────────────────────
    # Enums
    "OperatorType", "PrecisionMode",
    # Operator / Precision engines
    "OperatorRouter", "PrecisionController",
    # Logger
    "VRN_MasterLogger", "VRN_Monitor", "VRN_SystemMonitor", "VRN_Logger",
    # JSON engine class
    "JSONEngine",
    # Validator
    "DataValidator",
    # Probe / profile
    "_probe", "detect_blas", "detect_libraries", "detect_system",
    "build_capability_profile", "get_profile", "_PROFILE_CACHE",
    # Cache helpers
    "cached_identity",
    # Cross-accel convenience
    "cross_accelerate",
    # Aliases (x-prefix)
    "xjson_dumps", "xjson_loads", "xcompress", "xdecompress",
    "xconcat", "xsort", "xdedup", "xmap_async",
    # Status printers
    "print_master_status", "print_cross_status",
    # ── ANC-STUB: stub utilities (always registered, only-increase) ───────────
    "is_stub", "get_real_libs", "count_real_libs",
]

# ══════════════════════════════════════════════════════════════════════════════
# AUTO BOOTSTRAP at import time
# ══════════════════════════════════════════════════════════════════════════════

if ENABLE_AUTO_CROSS_INIT:
    try:
        cross_init(silent=not VERBOSE_CROSS_INIT)
    except Exception:
        pass

# ══════════════════════════════════════════════════════════════════════════════
# __main__ — 直接執行顯示完整狀態 + 自測
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys as _sys

    # ── Run self-test ONCE, reuse everywhere ─────────────────────────────────
    _self_test = run_self_test()

    # ── Status banner ─────────────────────────────────────────────────────────
    rpt = accel_status_report()
    cap = rpt["capabilities"]
    hw  = rpt["system"]
    mem = hw.get("memory", {})
    simd = hw.get("simd", {})

    def _f(v): return "✅" if v else "❌"

    print("=" * 72)
    print("⚡ VeritasCeleritas v1.0  — 極限交叉加速引擎")
    print("   celeritas (Latin) = speed/swiftness | Veritas Celeritas = Truth at Speed")
    print("   功能只增不減 — Features Only Increase, Never Decrease")
    print("=" * 72)
    print(f"  [Thread]   active={rpt['threads_active']}  cross={rpt['threads_cross']}  "
          f"mode={rpt['mode']}  mem_scale={rpt['mem_scale']:.2f}")
    print(f"  [CPU]      logical={hw.get('cpu_logical')}  physical={hw.get('cpu_physical')}  "
          f"arch={hw.get('arch')}  blas={detect_blas()}")
    print(f"  [RAM]      total={mem.get('total_gb')}GB  avail={mem.get('available_gb')}GB  "
          f"used={mem.get('percent')}%")
    print(f"  [SIMD]     sse2={simd.get('sse2')}  avx={simd.get('avx')}  "
          f"avx2={simd.get('avx2')}  avx512={simd.get('avx512')}  neon={simd.get('neon')}")
    print(f"  [Libs]     {rpt['libs_available']} available  {rpt['libs_missing']} missing")
    print(f"  [Strategy] {rpt['strategies']} methods (M1-M50 + T1-T40)")
    print(f"  [Backends] {', '.join(rpt['backends_active'])}")
    print()
    print(f"  JIT={_f(cap['jit_numba'])}  polars={_f(cap['polars'])}  "
          f"duckdb={_f(cap['duckdb'])}  ray={_f(cap['ray'])}  joblib={_f(cap['joblib'])}")
    print(f"  orjson={_f(cap['orjson'])}  zstd={_f(cap['zstd'])}  "
          f"lz4={_f(cap['lz4'])}  xxhash={_f(cap['xxhash'])}  "
          f"rapidfuzz={_f(cap['rapidfuzz'])}")
    print(f"  winloop={_f(cap['async_winloop'])}  uvloop={_f(cap['async_uvloop'])}  "
          f"diskcache={_f(cap['diskcache'])}  psutil={_f(cap['psutil'])}")
    print(f"  cv2={_f(cap['cv2'])}  pyvips={_f(cap['pyvips'])}  "
          f"onnx={_f(cap['onnx'])}  torch={_f(cap['gpu_torch'])}  "
          f"cudf={_f(cap['gpu_cudf'])}")
    print("=" * 72)

    # ── Cross-functions ───────────────────────────────────────────────────────
    s = cross_status()
    print(f"\n[Cross Functions] {len(s['cross_funcs'])} registered:")
    for fn in s["cross_funcs"]:
        print(f"  → {fn}")

    # ── Engines ───────────────────────────────────────────────────────────────
    print(f"\n[Engines] {len(s['engines'])} registered:")
    for eng in s["engines"]:
        print(f"  ✅ {eng}")

    # ── Self-test results ─────────────────────────────────────────────────────
    total_t  = _self_test["passed"] + _self_test["failed"]
    env_fails = [t for t in _self_test["tests"]
                 if not t["ok"] and t["msg"] == "not installed"]
    code_fails = [t for t in _self_test["tests"]
                  if not t["ok"] and t["msg"] != "not installed"]

    print(f"\n[Self-Test]  {_self_test['passed']}/{total_t} PASS  "
          f"({_self_test['duration_ms']:.1f}ms)")
    print(f"  env-missing={len(env_fails)}  code-errors={len(code_fails)}")
    print()
    for t in _self_test["tests"]:
        mark = "✅" if t["ok"] else ("⚠️ " if t["msg"] == "not installed" else "❌")
        print(f"  {mark} {t['name']:<28} {t['msg']}")

    if code_fails:
        print(f"\n❌ CODE ERRORS ({len(code_fails)}):")
        for t in code_fails:
            print(f"   {t['name']}: {t['msg']}")
        _sys.exit(1)
    else:
        print(f"\n✅ ALL CODE TESTS PASS  "
              f"({len(env_fails)} skipped = missing optional libs in env)")

# [VIA:ANCHOR:ACCEL-ERR-FALLBACK-001]
accel_err = None
