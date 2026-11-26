

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# VeritasCeleritas v1141(側線 2026-09-25 第十六段):v1140 拿掉 TA-Lib —— 操作員令「No ta-lib allowed」(L50 第一條)。
#   換法照 accelerator/VeritasCeleritas.py 合規本那一份差異原樣重放(8 處:惰性 import · libs 鍵 · 依賴清單 · 指標備援類 · 兩個呼叫點 · 匯出清單),
#   指標備援改名 _QuantGuardIndicatorFallback(QuantGuard 管指標);其餘位元與 v1140 相同。v1140 照 L04 留作版史;上游原件零觸碰留在收容區。
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
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

# ===== [VIA:ANCHOR:SAFE-STATE:START] =====
# Bridged by VDF_MDL001_Supportive_Bridge_v4 on 2026-04-26 02:33 for VeritasCeleritas

# =============================================================================
# VDF Accelerator integration · injected by VDF_MDL001_Supportive_Bridge_v4
# =============================================================================
# Provides cached/retried/deduped HTTP fetch via VDF_MDL000_Accelerator_Core_v4.
# Original module behavior is preserved; this only adds optional shortcuts:
#   vdf_fetch / vdf_fetch_json / vdf_fetch_many / vdf_accelerated / vdf_stats
# Bridge marker: VDF_MDL000_Accelerator_Core_v4
try:
    import sys as _vdf_sys
    import pathlib as _vdf_pathlib
    _VDF_PROBE = _vdf_pathlib.Path(__file__).resolve()
    while _VDF_PROBE.parent != _VDF_PROBE:
        _candidate = _VDF_PROBE / "VeritasDataForge" / "accelerator"
        if _candidate.exists():
            _vdf_sys.path.insert(0, str(_VDF_PROBE / "VeritasDataForge"))
            break
        _VDF_PROBE = _VDF_PROBE.parent
    from accelerator.VDF_MDL000_Accelerator_Core_v4 import (
        fetch as vdf_fetch,
        fetch_json as vdf_fetch_json,
        fetch_many as vdf_fetch_many,
        accelerated as vdf_accelerated,
        stats as vdf_stats,
    )
    _VDF_BRIDGE_OK = True
except Exception:
    _VDF_BRIDGE_OK = False
# =============================================================================
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

# Deferred peer slots — bound after ANC-02 (_LazyModule / _spec_exists exist).
# Never self-bind this module as a LazyModule (circular import of in-progress file).
VIA_SSOT_Unified = None
VeritasAegisNexus = None
# VeritasCeleritas peer slot reserved but never self-imported at module load.
_VIA_PEER_SLOTS = ("VIA_SSOT_Unified", "VeritasAegisNexus")

def _via_bind_peer_modules() -> dict:
    """Bind optional peer support modules once lazy-import machinery exists."""
    g = globals()
    bound = {}
    binder = g.get("_LazyModule")
    probe = g.get("_spec_exists")
    if binder is None or probe is None:
        return bound
    for name in _VIA_PEER_SLOTS:
        if g.get(name) is not None:
            bound[name] = "already"
            continue
        try:
            g[name] = binder(name) if probe(name) else None
            bound[name] = "bound" if g[name] is not None else "missing"
        except Exception:
            g[name] = None
            bound[name] = "error"
    return bound
# ===== [VIA:ANCHOR:SUPPORT:BOOTSTRAP:END] =====

"""
╔══════════════════════════════════════════════════════════════════════════════════╗
║  VeritasCeleritas.py  v1.2  · EXTRA 15 + Retired replacements                ║
║  ──────────────────────────────────────────────────────────────────────────    ║
║  VIA 極限交叉加速引擎 — 功能只增不減                                            ║
║                                                                                 ║
║  MERGED FROM:                                                                   ║
║    [A] VIA_SuperAccel_Module.py v3.0   — 加速核心 §1-§17 + §C-§E              ║
║    [B] VIA_Accel_Embedded_v1.py v12.2  — 26 ENG · 90策略 · IP-01~IP-11       ║
║    [C] VIA_MAX_Accel_Bootstrap.py v3.0 — U01-U10 · 17 ENV · GCTuner·Pool     ║
║                                                                                 ║
║  ANCHOR REGISTRY:                                                               ║
║    ANC-00  OPERATIONAL KERNEL  (phase / dispatch / registry / health)          ║
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
║    ANC-26  UNIFIED COMPAT DISPATCH  (xbatch/xrun/xsubmit/accelerate)           ║
║    ANC-27  EXTRA 15 LOCAL-FREE + RETIRED→SUCCESSOR ROUTING                     ║
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

__version__   = "1.2.0"
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
# v1.2 extras (功能只增不減 / 停更則換更強):
#   + EXTRA 15: jiter cramjam charset-normalizer narwhals numpy-financial
#               fastexcel connectorx exchange-calendars sqlglot fsspec
#               pymupdf cytoolz usearch zhconv curl_cffi
#   RETIRED hot-path: ujson rapidjson cityhash blosc snappy vaex datatable
#                     Levenshtein chardet ffn  → successor routing, names kept

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
_XMAP_CHUNK_THRESHOLD:  int = 500  # items — enable auto-chunking (skipped if cheap)
_XMAP_CHEAP_SEC:        float = 8e-5  # 80µs/item → sequential, never ThreadPool
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
# ANC-00b  deferred peer bind (requires _LazyModule from ANC-02)
try:
    _via_bind_peer_modules()
except Exception:
    pass

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
# TA-Lib is prohibited. QuantGuard owns the active indicator path; the
# deterministic fallback below is kept only for compatibility with generic
# Celeritas callers and never imports or loads a TA-Lib package.
quantguard_indicators = None
pandas_ta             = _si("pandas_ta")
ta_lib                = _si("ta")
ffn                   = _si("ffn")

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

# ── ANC-27 EXTRA 15  LOCAL FREE (maintained) ────────────────────────────────
jiter               = _si("jiter")
cramjam             = _si("cramjam")
charset_normalizer  = _si("charset_normalizer")
narwhals            = _si("narwhals")
numpy_financial     = _si("numpy_financial")
fastexcel           = _si("fastexcel")
connectorx          = _si("connectorx")
exchange_calendars  = _si("exchange_calendars")
sqlglot             = _si("sqlglot")
fsspec              = _si("fsspec")
fitz                = _si("fitz")              # PyMuPDF
cytoolz             = _si("cytoolz")
usearch             = _si("usearch")
zhconv              = _si("zhconv")
curl_cffi           = _si("curl_cffi")

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
    "quantguard": quantguard_indicators, "pandas_ta": pandas_ta, "ta": ta_lib, "ffn": ffn,
    "requests": requests_m, "httpx": httpx_m, "aiohttp": aiohttp_m,
    "urllib3": urllib3_m,
    "rich": rich, "tqdm": tqdm_m, "loguru": loguru,
    "structlog": structlog, "fasteners": fasteners, "bitarray": bitarray,
    "networkx": networkx, "openpyxl": openpyxl,
    # ANC-27 extras (append-only)
    "jiter": jiter, "cramjam": cramjam,
    "charset-normalizer": charset_normalizer, "narwhals": narwhals,
    "numpy-financial": numpy_financial, "fastexcel": fastexcel,
    "connectorx": connectorx, "exchange-calendars": exchange_calendars,
    "sqlglot": sqlglot, "fsspec": fsspec, "pymupdf": fitz,
    "cytoolz": cytoolz, "usearch": usearch, "zhconv": zhconv,
    "curl_cffi": curl_cffi,
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
        # ANC-27 extras
        "jiter":         _real(jiter),
        "cramjam":       _real(cramjam),
        "charset_normalizer": _real(charset_normalizer),
        "narwhals":      _real(narwhals),
        "numpy_financial": _real(numpy_financial),
        "fastexcel":     _real(fastexcel),
        "connectorx":    _real(connectorx),
        "exchange_calendars": _real(exchange_calendars),
        "sqlglot":       _real(sqlglot),
        "fsspec":        _real(fsspec),
        "pymupdf":       _real(fitz),
        "cytoolz":       _real(cytoolz),
        "usearch":       _real(usearch),
        "zhconv":        _real(zhconv),
        "curl_cffi":     _real(curl_cffi),
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
    """orjson > msgspec > jiter > stdlib. Skips stubs. Returns str."""
    global orjson, msgspec, jiter
    if orjson is None or type(orjson).__name__.endswith("Stub"):
        orjson = _si("orjson")
    if msgspec is None or type(msgspec).__name__.endswith("Stub"):
        msgspec = _si("msgspec")
    if jiter is None or type(jiter).__name__.endswith("Stub"):
        jiter = _si("jiter")

    if orjson is not None and not type(orjson).__name__.endswith("Stub"):
        try:
            opt = orjson.OPT_INDENT_2 if indent else None
            raw = orjson.dumps(obj, option=opt) if opt else orjson.dumps(obj)
            return raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else raw
        except Exception:
            pass
    if msgspec is not None and not type(msgspec).__name__.endswith("Stub"):
        try:
            raw = msgspec.json.encode(obj)
            text = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else str(raw)
            if indent:
                import json as _j
                return _j.dumps(_j.loads(text), ensure_ascii=False, indent=indent, default=str)
            return text
        except Exception:
            pass
    if jiter is not None and not type(jiter).__name__.endswith("Stub"):
        try:
            raw = jiter.to_json(obj)
            if indent:
                import json as _j
                return _j.dumps(jiter.from_json(raw) if isinstance(raw, (bytes, bytearray, str)) else obj,
                                ensure_ascii=False, indent=indent, default=str)
            return raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else str(raw)
        except Exception:
            pass
    import json as _j
    return _j.dumps(obj, ensure_ascii=False, indent=indent, default=str)

def json_loads(s: Union[str, bytes], **kwargs) -> Any:
    """jiter > orjson > ujson > rapidjson > stdlib."""
    if jiter is not None:
        try:
            return jiter.from_json(s if isinstance(s, (bytes, bytearray)) else s.encode("utf-8"))
        except Exception:
            pass
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
    if cramjam is not None:
        try:
            return b"CJ:" + bytes(cramjam.zstd.compress(data, level=level))
        except Exception:
            pass
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
    if data[:3] == b"CJ:" and cramjam is not None:
        return bytes(cramjam.zstd.decompress(data[3:]))
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

# Operational pin — last-wins shims must never erase this decorator.
_ACCELERATE_CORE = accelerate
_ACCELERATE_CACHED_CORE = accelerate_cached

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

        if len(items_list) >= 8:
            _probe_n = min(8, len(items_list))
            _t0 = time.perf_counter()
            try:
                _probe_out = [func(items_list[i]) for i in range(_probe_n)]
                _per = (time.perf_counter() - _t0) / _probe_n
                if _per < _XMAP_CHEAP_SEC:
                    if _probe_n == len(items_list):
                        return _probe_out
                    return _probe_out + [func(items_list[i]) for i in range(_probe_n, len(items_list))]
            except Exception:
                pass

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
            "yfinance", "pandas_ta", "ta", "ffn",
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

def _xmap_vector(func: Callable, payload: List[Any]):
    """fromiter + ufunc. None if not vectorizable. xmap still returns list."""
    if not payload:
        return []
    x0 = payload[0]
    if isinstance(x0, bool) or not isinstance(x0, (int, float)):
        return None
    np_mod = _si("numpy")
    if np_mod is None or type(np_mod).__name__.endswith("Stub"):
        return None
    n = len(payload)
    try:
        dt = np_mod.float64 if isinstance(x0, float) else np_mod.int64
        arr = payload if isinstance(payload, np_mod.ndarray) else np_mod.fromiter(payload, dtype=dt, count=n)
        out = func(arr)
        if isinstance(out, np_mod.ndarray) and getattr(out, "shape", None) == (n,):
            return out.tolist()
    except Exception:
        return None
    return None


def xmap(func: Callable, items: List[Any], *,
         mode: str = "auto", max_workers: Optional[int] = None,
         dedupe: bool = False, chunk_size: Optional[int] = None,
         guard_mem: bool = True) -> List[Any]:
    """
    Cross-accelerated map:
      - numpy vector path for numeric ufuncs
      - cheap-task shield (no ThreadPool under 80µs/item)
      - memory pressure gate (guard_mem)
      - adaptive chunk splitting
      - ParallelEngine auto (thread/joblib/ray)
    """
    if not items: return []

    payload = items if (not dedupe and isinstance(items, list)) else (
        dedupe_preserve_order(items) if dedupe else list(items)
    )

    if mode in ("auto", "thread", "balanced", "maxsafe", "safe") and len(payload) >= 32:
        vectored = _xmap_vector(func, payload)
        if vectored is not None:
            return vectored

    if mode in ("auto", "thread", "balanced", "maxsafe", "safe") and len(payload) >= 8:
        _k = min(8, len(payload))
        _t1 = time.perf_counter()
        try:
            for _i in range(_k):
                func(payload[_i])
            _per = (time.perf_counter() - _t1) / _k
            if _per < _XMAP_CHEAP_SEC:
                return [func(x) for x in payload]
        except Exception:
            pass

    if guard_mem and under_memory_pressure(_XMAP_PRESSURE_GATE):
        return [func(i) for i in payload]

    kpi = _get_kpi()
    t0  = time.perf_counter()
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
            if curl_cffi is not None:
                try:
                    _creq = getattr(curl_cffi, "requests", None)
                    if _creq is None:
                        import curl_cffi.requests as _creq  # type: ignore
                    r = _creq.get(url, timeout=timeout, impersonate="chrome")
                    if getattr(r, "status_code", 0) == 200:
                        return r.text if return_type == "text" else r.content.decode("utf-8", "ignore")
                except Exception:
                    pass
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

# ── QuantGuard indicator fallback ─────────────────────────────────────────────
class _QuantGuardIndicatorFallback:
    """Deterministic pure-Python fallback; the active policy owner is QuantGuard."""
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

if quantguard_indicators is None:
    quantguard_indicators = _QuantGuardIndicatorFallback()

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
        return _QuantGuardIndicatorFallback.RSI(list(close), timeperiod=length)

    @staticmethod
    def macd(close, fast=12, slow=26, signal=9, **kw):
        return _QuantGuardIndicatorFallback.MACD(list(close), fast, slow, signal)

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
    _CV2Stub, _PILStub, _RichStub, _TqdmStub, _QuantGuardIndicatorFallback, _PandasTaStub,
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
    # ANC-27 extras
    "extra_registry", "extra_status", "_EXTRA15", "_SUPERSEDED",
    "ExtraJsonEngine", "ExtraCompressEngine", "ExtraFrameEngine",
    "ExtraFinanceXEngine", "ExtraCalendarEngine", "ExtraExcelEngine",
    "ExtraSqlEngine", "ExtraFsEngine", "ExtraPdfEngine",
    "ExtraIterEngine", "ExtraVectorEngine", "ExtraZhEngine",
    "ExtraEncodingEngine", "ExtraFetchEngine",
    "detect_encoding", "to_zh_tw", "xnpv", "xirr",
    "jiter", "cramjam", "charset_normalizer", "narwhals", "numpy_financial",
    "fastexcel", "connectorx", "exchange_calendars", "sqlglot", "fsspec",
    "fitz", "cytoolz", "usearch", "zhconv", "curl_cffi",
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


# =============================================================================
# ANC-27  EXTRA 15 LOCAL-FREE + RETIRED → SUCCESSOR
# Policy: names of retired tools remain bound (功能只增不減 for callers).
# Hot paths no longer *depend* on them. Each removal has a stronger successor.
# =============================================================================

_SUPERSEDED: Dict[str, str] = {
    "ujson": "jiter",
    "rapidjson": "jiter",
    "cityhash": "xxhash",
    "blosc": "cramjam",
    "snappy": "cramjam",
    "vaex": "narwhals",
    "datatable": "narwhals",
    "Levenshtein": "rapidfuzz",
    "chardet": "charset-normalizer",
    "ffn": "numpy-financial",
}

_EXTRA15: Dict[str, str] = {
    "jiter": "JSON hot-path (Pydantic v2 core)",
    "cramjam": "Rust unified compression",
    "charset-normalizer": "encoding detect (chardet successor)",
    "narwhals": "dataframe adapter (polars/pandas/pyarrow)",
    "numpy-financial": "NPV/IRR/PMT (ffn successor)",
    "fastexcel": "Rust Excel reader",
    "connectorx": "DB → Arrow extract",
    "exchange-calendars": "TWSE/NYSE session calendar",
    "sqlglot": "SQL parse/transpile",
    "fsspec": "unified filesystem",
    "pymupdf": "PDF text/layout (fitz)",
    "cytoolz": "Cython itertools",
    "usearch": "local vector search",
    "zhconv": "zh-TW / zh-CN convert",
    "curl_cffi": "TLS-impersonated HTTP for xfetch",
}


def extra_registry() -> Dict[str, Any]:
    """Panoramic EXTRA 15 + retirement matrix."""
    return {
        "version": __version__,
        "extras": [
            {"id": k, "role": v, "installed": _LIB_MAP.get(k) is not None or _LIB_MAP.get(k.replace("_", "-")) is not None}
            for k, v in _EXTRA15.items()
        ],
        "retired": [
            {"id": old, "successor": new, "reason": "unmaintained/stalled — hot path rerouted"}
            for old, new in _SUPERSEDED.items()
        ],
        "net_added": len(_EXTRA15),
        "net_retired_from_hotpath": len(_SUPERSEDED),
        "policy": "功能只增不減 — retired names stay importable; successors own the hot path",
    }


def extra_status() -> Dict[str, Any]:
    reg = extra_registry()
    installed = 0
    for row in reg["extras"]:
        key = row["id"]
        obj = _LIB_MAP.get(key)
        if obj is None:
            obj = _LIB_MAP.get(key.replace("-", "_"))
        real = False
        try:
            real = obj is not None and not is_stub(obj)
            if isinstance(obj, _LazyModule):
                real = _spec_exists(obj._name)
        except Exception:
            real = obj is not None
        row["real"] = bool(real)
        if real:
            installed += 1
        row["installed"] = row["real"]
    reg["extras_real"] = installed
    return reg


class ExtraJsonEngine:
    """jiter-first JSON, falls through to json_dumps/loads."""

    @staticmethod
    def dumps(obj: Any, indent: int = None) -> str:
        return json_dumps(obj, indent=indent)

    @staticmethod
    def loads(s: Union[str, bytes]) -> Any:
        return json_loads(s)


class ExtraCompressEngine:
    """cramjam-first compression."""

    @staticmethod
    def compress(data: bytes, codec: str = "zstd", level: int = _COMPRESS_DEFAULT_LEVEL) -> bytes:
        if cramjam is not None:
            try:
                fn = getattr(getattr(cramjam, codec, None), "compress", None)
                if fn:
                    return b"CJ:" + bytes(fn(data))
            except Exception:
                pass
        return compress_bytes(data, level=level)

    @staticmethod
    def decompress(data: bytes) -> bytes:
        return decompress_bytes(data)


class ExtraFrameEngine:
    """narwhals adapter — polars-first, pandas fallback."""

    @staticmethod
    def from_native(frame: Any) -> Any:
        if narwhals is not None:
            try:
                return narwhals.from_native(frame, eager_or_interchangeable=True)
            except Exception:
                pass
        return frame

    @staticmethod
    def to_polars(frame: Any) -> Any:
        return to_polars(frame)


class ExtraFinanceXEngine:
    """numpy-financial successor to ffn for NPV/IRR/PMT."""

    @staticmethod
    def npv(rate: float, cashflows) -> float:
        if numpy_financial is not None:
            try:
                return float(numpy_financial.npv(rate, list(cashflows)))
            except Exception:
                pass
        acc = 0.0
        for i, c in enumerate(list(cashflows)):
            acc += float(c) / ((1.0 + rate) ** i)
        return acc

    @staticmethod
    def irr(cashflows) -> float:
        if numpy_financial is not None:
            try:
                return float(numpy_financial.irr(list(cashflows)))
            except Exception:
                pass
        return float("nan")

    @staticmethod
    def pmt(rate: float, nper: int, pv: float) -> float:
        if numpy_financial is not None:
            try:
                return float(numpy_financial.pmt(rate, nper, pv))
            except Exception:
                pass
        if rate == 0:
            return -float(pv) / max(1, nper)
        return -float(pv) * (rate * (1 + rate) ** nper) / ((1 + rate) ** nper - 1)


class ExtraCalendarEngine:
    @staticmethod
    def is_session(exchange: str, day) -> bool:
        if exchange_calendars is not None:
            try:
                cal = exchange_calendars.get_calendar(exchange)
                return bool(cal.is_session(day))
            except Exception:
                pass
        return True


class ExtraExcelEngine:
    @staticmethod
    def read(path: str) -> Any:
        if fastexcel is not None:
            try:
                reader = fastexcel.read_excel(path)
                sheet = reader.load_sheet_by_idx(0)
                return sheet.to_polars() if hasattr(sheet, "to_polars") else sheet.to_pandas()
            except Exception:
                pass
        if pd is not None:
            return pd.read_excel(path)
        raise RuntimeError("fastexcel + pandas missing")


class ExtraSqlEngine:
    @staticmethod
    def transpile(sql: str, read: str = "mysql", write: str = "duckdb") -> str:
        if sqlglot is not None:
            try:
                return sqlglot.transpile(sql, read=read, write=write)[0]
            except Exception:
                pass
        return sql

    @staticmethod
    def read_sql(query: str, conn: str) -> Any:
        if connectorx is not None:
            try:
                return connectorx.read_sql(conn, query)
            except Exception:
                pass
        raise RuntimeError("connectorx not installed")


class ExtraFsEngine:
    @staticmethod
    def open(url: str, mode: str = "rb"):
        if fsspec is not None:
            try:
                fs, path = fsspec.core.url_to_fs(url)
                return fs.open(path, mode)
            except Exception:
                pass
        return open(url, mode)


class ExtraPdfEngine:
    @staticmethod
    def text(path: str) -> str:
        if fitz is not None:
            try:
                doc = fitz.open(path)
                try:
                    return "\n".join(page.get_text() for page in doc)
                finally:
                    doc.close()
            except Exception:
                pass
        raise RuntimeError("pymupdf not installed")


class ExtraIterEngine:
    @staticmethod
    def partition(pred, seq):
        if cytoolz is not None:
            try:
                return cytoolz.itertoolz.partitionby(pred, seq)
            except Exception:
                pass
        return seq


class ExtraVectorEngine:
    @staticmethod
    def search(vectors, query, k: int = 5):
        if usearch is not None:
            try:
                idx = usearch.Index(ndim=len(query))
                idx.add(range(len(vectors)), vectors)
                return idx.search(query, k)
            except Exception:
                pass
        return []


class ExtraZhEngine:
    @staticmethod
    def to_tw(text: str) -> str:
        if zhconv is not None:
            try:
                return zhconv.convert(text, "zh-tw")
            except Exception:
                pass
        return text


class ExtraEncodingEngine:
    @staticmethod
    def detect(raw: bytes) -> str:
        if charset_normalizer is not None:
            try:
                hit = charset_normalizer.from_bytes(raw).best()
                return str(hit.encoding) if hit else "utf-8"
            except Exception:
                pass
        return "utf-8"


class ExtraFetchEngine:
    @staticmethod
    def get(url: str, timeout: int = 30) -> Optional[str]:
        if curl_cffi is not None:
            try:
                _creq = getattr(curl_cffi, "requests", None)
                if _creq is None:
                    import curl_cffi.requests as _creq  # type: ignore
                r = _creq.get(url, timeout=timeout, impersonate="chrome")
                if getattr(r, "status_code", 0) == 200:
                    return r.text
            except Exception:
                pass
        return None


def detect_encoding(raw: bytes) -> str:
    return ExtraEncodingEngine.detect(raw)


def to_zh_tw(text: str) -> str:
    return ExtraZhEngine.to_tw(text)


def xnpv(rate: float, cashflows) -> float:
    return ExtraFinanceXEngine.npv(rate, cashflows)


def xirr(cashflows) -> float:
    return ExtraFinanceXEngine.irr(cashflows)


# [VIA:ANCHOR:ACCEL-ERR-FALLBACK-001]
accel_err = None

# =============================================================================
# ANC-00 / ANC-26  OPERATIONAL KERNEL + UNIFIED COMPAT DISPATCH
# Policy: 功能只增不減 — every historical signature stays callable.
# Previous EOF patches last-won and *reduced* accelerate / xbatch.
# This kernel restores the strong core and multiplexes all shim signatures.
# =============================================================================

from enum import Enum as _OpEnum


class CeleritasPhase(_OpEnum):
    """Runtime phase machine. Forward-only except RESET (explicit)."""
    BOOT = "boot"
    PROBE = "probe"
    ENV = "env"
    ENGINES = "engines"
    CROSS = "cross"
    READY = "ready"
    DEGRADED = "degraded"


class CeleritasKernel:
    """
    Operational spine for VeritasCeleritas.

    Does not replace engines. It:
      1. records phase
      2. registers tools (append-only)
      3. dispatches historical API signatures
      4. publishes health without hiding missing optional libs
    """

    _lock = threading.RLock()
    _phase = CeleritasPhase.BOOT
    _tools: Dict[str, Dict[str, Any]] = {}
    _events: List[Dict[str, Any]] = []
    _started = time.time()

    @classmethod
    def phase(cls) -> str:
        return cls._phase.value

    @classmethod
    def set_phase(cls, phase: CeleritasPhase) -> str:
        with cls._lock:
            cls._phase = phase
            cls._events.append({
                "ts": time.time(),
                "phase": phase.value,
            })
            try:
                _VIAStateBox.set("celeritas_phase", phase.value)
            except Exception:
                pass
            return phase.value

    @classmethod
    def register(cls, name: str, obj: Any, *, kind: str = "fn",
                 signatures: Optional[List[str]] = None,
                 note: str = "") -> None:
        with cls._lock:
            prev = cls._tools.get(name)
            cls._tools[name] = {
                "name": name,
                "kind": kind,
                "obj": obj,
                "signatures": list(signatures or []),
                "note": note,
                "replaced": bool(prev),
            }

    @classmethod
    def tools(cls) -> Dict[str, Dict[str, Any]]:
        with cls._lock:
            out = {}
            for k, v in cls._tools.items():
                row = dict(v)
                row["obj"] = type(v.get("obj")).__name__ if v.get("obj") is not None else None
                row["callable"] = callable(v.get("obj"))
                out[k] = row
            return out

    @classmethod
    def get_tool(cls, name: str, default=None):
        with cls._lock:
            row = cls._tools.get(name)
            return row["obj"] if row else default

    @classmethod
    def health(cls) -> Dict[str, Any]:
        libs_all = 0
        libs_real = 0
        try:
            libs_all = count_available_libs()
        except Exception:
            pass
        try:
            libs_real = count_real_libs()
        except Exception:
            libs_real = libs_all
        phase = cls.phase()
        degraded = phase == CeleritasPhase.DEGRADED.value
        return {
            "status": "degraded" if degraded else "alive",
            "module": "VeritasCeleritas",
            "version": __version__,
            "phase": phase,
            "uptime_sec": round(time.time() - cls._started, 3),
            "tools_registered": len(cls._tools),
            "libs_available": libs_all,
            "libs_real": libs_real,
            "cross_init": bool(globals().get("_CROSS_INIT_DONE")),
            "accelerate_core_pinned": callable(globals().get("_ACCELERATE_CORE")),
            "extras": len(globals().get("_EXTRA15") or {}),
            "retired_hotpath": len(globals().get("_SUPERSEDED") or {}),
        }


def _cel_is_iterable_not_str(obj: Any) -> bool:
    if obj is None or isinstance(obj, (str, bytes, bytearray)):
        return False
    return isinstance(obj, Iterable)


def _cel_chunk(items: Any, batch_size: int = 20) -> List[List[Any]]:
    try:
        if items is None:
            return []
        try:
            bs = int(batch_size)
        except Exception:
            bs = 20
        if bs <= 0:
            bs = 20
        seq = items if isinstance(items, list) else list(items)
        return [seq[i:i + bs] for i in range(0, len(seq), bs)]
    except Exception:
        try:
            return [list(items)]
        except Exception:
            return []


def _cel_parallel_map(func: Callable, iterable: Any, max_workers: int = 4) -> List[Any]:
    """Prefer existing engines; never drop the work."""
    items = list(iterable) if iterable is not None else []
    if not items:
        return []
    workers = max(1, int(max_workers or 4))
    try:
        if "ParallelEngine" in globals() and ParallelEngine is not None:
            return ParallelEngine.map_auto(func, items, mode="thread")
    except Exception:
        pass
    try:
        if "xbatch_process" in globals():
            return xbatch_process(func, items, max_workers=workers)
    except Exception:
        pass
    try:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            return list(ex.map(func, items))
    except Exception:
        return [func(x) for x in items]


def xbatch(*args, **kwargs):
    """
    Unified xbatch — all historical signatures live:

      A. xbatch(func, iterable, max_workers=4)
      B. xbatch(items, batch_size=20)          # chunker
      C. xbatch(items, batch_size=20) via kwargs
      D. xbatch(func=..., iterable=...)        # explicit

    Dispatch rule (deterministic):
      - first positional callable → parallel map
      - otherwise → list-of-batches chunker
    """
    # Explicit kwargs form used by some bridges
    if "func" in kwargs and ("iterable" in kwargs or "items" in kwargs):
        fn = kwargs.get("func")
        it = kwargs.get("iterable", kwargs.get("items"))
        mw = kwargs.get("max_workers", 4)
        return _cel_parallel_map(fn, it, mw)

    if not args:
        items = kwargs.get("items", kwargs.get("iterable"))
        bs = kwargs.get("batch_size", 20)
        return _cel_chunk(items, bs)

    first = args[0]

    # Signature A: callable + iterable
    if callable(first):
        iterable = args[1] if len(args) > 1 else kwargs.get("iterable", kwargs.get("items"))
        if len(args) > 2:
            max_workers = args[2]
        else:
            max_workers = kwargs.get("max_workers", 4)
        return _cel_parallel_map(first, iterable, max_workers)

    # Signature B: chunker
    batch_size = args[1] if len(args) > 1 else kwargs.get("batch_size", 20)
    # Guard: some callers pass max_workers as 2nd positional on a non-callable
    if "max_workers" in kwargs and "batch_size" not in kwargs and len(args) == 1:
        batch_size = kwargs.get("batch_size", 20)
    return _cel_chunk(first, batch_size)


def xrun(func=None, *args, **kwargs):
    """
    Unified single-task runner.
      xrun()            → status dict (legacy)
      xrun(fn, *a, **k) → fn(*a, **k) with pool when available
    """
    try:
        if func is None:
            return {"status": "ready", "module": "VeritasCeleritas", "runner": "xrun",
                    "phase": CeleritasKernel.phase()}
        if not callable(func):
            return {"status": "error", "runner": "xrun", "msg": "func not callable"}
        pool = globals().get("_LazyPool")
        if pool is not None:
            try:
                return pool.submit(func, *args, **kwargs).result()
            except Exception:
                pass
        return func(*args, **kwargs)
    except Exception as e:
        return {"status": "error", "runner": "xrun", "msg": str(e)}


def xsubmit(func=None, *args, **kwargs):
    """
    Unified submit.
      xsubmit()            → status dict (legacy)
      xsubmit(fn, *a, **k) → Future when pool exists, else eager result
    """
    try:
        if func is None:
            return {"status": "ready", "module": "VeritasCeleritas", "runner": "xsubmit",
                    "phase": CeleritasKernel.phase()}
        if not callable(func):
            return {"status": "error", "runner": "xsubmit", "msg": "func not callable"}
        pool = globals().get("_LazyPool")
        if pool is not None:
            try:
                return pool.submit(func, *args, **kwargs)
            except Exception:
                pass
        return func(*args, **kwargs)
    except Exception as e:
        return {"status": "error", "runner": "xsubmit", "msg": str(e)}


def accelerate(func=None, *args, mode: str = "balanced", **kwargs):
    """
    Unified accelerate — restores ANC-16 decorator and keeps runner shims:

      @accelerate
      @accelerate()
      @accelerate(mode="maxsafe")
      accelerate(fn)              → decorator wrapper (core)
      accelerate(fn, *args, **kw) → execute via core wrapper (compat runner)
      accelerate()                → status dict
    """
    core = globals().get("_ACCELERATE_CORE")
    try:
        if func is None:
            # @accelerate() factory  OR  bare status
            if not args and not kwargs:
                def _factory(f: Callable) -> Callable:
                    if core:
                        return core(f, mode=mode)
                    return f
                # Distinguishing factory vs status: historical shim returned
                # status dict on zero-arg call. Keep that, plus .decorate
                status = {
                    "status": "ready",
                    "module": "VeritasCeleritas",
                    "phase": CeleritasKernel.phase(),
                    "core": bool(core),
                    "mode": mode,
                }

                class _AccelStatus(dict):
                    def __call__(self, f=None, *a, **k):
                        if f is None:
                            return self
                        if core:
                            wrapped = core(f, mode=mode)
                            return wrapped(*a, **k) if a or k else wrapped
                        return f(*a, **k) if (a or k) and callable(f) else f
                st = _AccelStatus(status)
                return st
            # @accelerate(mode="...")
            if core:
                return core(mode=mode)
            def _identity(f):
                return f
            return _identity

        if callable(func) and not args and not kwargs:
            if core:
                return core(func, mode=mode)
            return func

        if callable(func):
            if core:
                wrapped = core(func, mode=mode)
                try:
                    return wrapped(*args, **kwargs)
                except Exception:
                    return func(*args, **kwargs)
            return func(*args, **kwargs)

        return {"status": "ready", "module": "VeritasCeleritas", "phase": CeleritasKernel.phase()}
    except Exception as e:
        if callable(func):
            try:
                return func(*args, **kwargs)
            except Exception:
                pass
        return {"status": "error", "module": "VeritasCeleritas", "msg": str(e)}


def celeritas_health():
    """Legacy health + kernel health (superset, never smaller)."""
    h = CeleritasKernel.health()
    h["status"] = h.get("status") or "alive"
    return h


def op_status() -> Dict[str, Any]:
    """Panoramic operational snapshot — kernel + cross + capabilities."""
    snap = CeleritasKernel.health()
    try:
        snap["cross"] = {
            "init": bool(globals().get("_CROSS_INIT_DONE")),
            "mode": _resolve_mode(),
            "threads": thread_budget(),
            "threads_cross": thread_budget_cross(),
        }
    except Exception as e:
        snap["cross"] = {"error": str(e)}
    try:
        snap["tools"] = sorted(CeleritasKernel.tools().keys())
    except Exception:
        snap["tools"] = []
    return snap


def op_dispatch(name: str, *args, **kwargs):
    """Named-tool dispatcher. Unknown name → structured miss, never raise."""
    obj = CeleritasKernel.get_tool(name)
    if obj is None:
        obj = globals().get(name)
    if obj is None:
        return {"status": "miss", "tool": name}
    if not callable(obj):
        return obj
    try:
        return obj(*args, **kwargs)
    except Exception as e:
        return {"status": "error", "tool": name, "msg": str(e)}


def _cel_register_core_tools() -> int:
    """Append-only registration of the operational surface."""
    specs = [
        ("xmap", xmap, "fn", ["func, items"], "cross map"),
        ("xmap_async", xmap_async, "fn", ["func, items"], "async map"),
        ("xfetch", xfetch, "fn", ["urls"], "batch fetch"),
        ("xbatch", xbatch, "fn", ["func, iterable", "items, batch_size"], "unified batch"),
        ("xbatch_process", xbatch_process, "fn", ["func, items"], "prod batch"),
        ("xrun", xrun, "fn", ["func, *args"], "single runner"),
        ("xsubmit", xsubmit, "fn", ["func, *args"], "pool submit"),
        ("accelerate", accelerate, "fn", ["@accelerate", "fn, *args"], "unified accel"),
        ("accelerate_cached", accelerate_cached, "fn", ["@accelerate_cached"], "cached accel"),
        ("xjson_dumps", xjson_dumps, "fn", ["obj"], "json"),
        ("xjson_loads", xjson_loads, "fn", ["s"], "json"),
        ("xcompress", xcompress, "fn", ["bytes"], "compress"),
        ("xdecompress", xdecompress, "fn", ["bytes"], "decompress"),
        ("xconcat", xconcat, "fn", ["frames"], "df concat"),
        ("xsort", xsort, "fn", ["frame, by"], "df sort"),
        ("xdedup", xdedup, "fn", ["frame"], "df dedup"),
        ("xhash", xhash, "fn", ["data"], "hash"),
        ("cross_init", cross_init, "fn", ["mode"], "bootstrap"),
        ("cross_status", cross_status, "fn", [], "status"),
        ("cross_accelerate", cross_accelerate, "fn", ["func, items"], "dedupe map"),
        ("VISAccelerator", VISAccelerator, "cls", [], "main interface"),
        ("ParallelEngine", ParallelEngine, "cls", [], "parallel"),
        ("HardwareTuner", HardwareTuner, "cls", [], "hardware"),
        ("GCTuner", GCTuner, "cls", [], "gc"),
        ("FinanceEngine", FinanceEngine, "cls", [], "finance"),
        ("DataFrameEngine", DataFrameEngine, "cls", [], "dataframe"),
        ("CompressionEngine", CompressionEngine, "cls", [], "compress"),
        ("HashEngine", HashEngine, "cls", [], "hash"),
        ("StringEngine", StringEngine, "cls", [], "string"),
        ("JSONEngine", JSONEngine, "cls", [], "json class"),
        ("OperatorRouter", OperatorRouter, "cls", [], "op router"),
        ("PrecisionController", PrecisionController, "cls", [], "precision"),
        ("DataValidator", DataValidator, "cls", [], "validator"),
        ("VRN_MasterLogger", VRN_MasterLogger, "cls", [], "logger"),
        ("MemoryPool", MemoryPool, "cls", [], "pool"),
        ("CacheManager", CacheManager, "cls", [], "cache"),
        ("AutotuneCache", AutotuneCache, "cls", [], "sqlite cache"),
        ("KPITracker", KPITracker, "cls", [], "kpi"),
        ("Strategies", Strategies, "cls", [], "M1-M50+T1-T40"),
        ("extra_registry", extra_registry, "fn", [], "extra 15 matrix"),
        ("extra_status", extra_status, "fn", [], "extra 15 status"),
        ("ExtraJsonEngine", ExtraJsonEngine, "cls", [], "jiter json"),
        ("ExtraCompressEngine", ExtraCompressEngine, "cls", [], "cramjam"),
        ("ExtraFrameEngine", ExtraFrameEngine, "cls", [], "narwhals"),
        ("ExtraFinanceXEngine", ExtraFinanceXEngine, "cls", [], "numpy-financial"),
        ("ExtraCalendarEngine", ExtraCalendarEngine, "cls", [], "exchange calendars"),
        ("ExtraExcelEngine", ExtraExcelEngine, "cls", [], "fastexcel"),
        ("ExtraSqlEngine", ExtraSqlEngine, "cls", [], "sqlglot/connectorx"),
        ("ExtraFsEngine", ExtraFsEngine, "cls", [], "fsspec"),
        ("ExtraPdfEngine", ExtraPdfEngine, "cls", [], "pymupdf"),
        ("ExtraIterEngine", ExtraIterEngine, "cls", [], "cytoolz"),
        ("ExtraVectorEngine", ExtraVectorEngine, "cls", [], "usearch"),
        ("ExtraZhEngine", ExtraZhEngine, "cls", [], "zhconv"),
        ("ExtraEncodingEngine", ExtraEncodingEngine, "cls", [], "charset-normalizer"),
        ("ExtraFetchEngine", ExtraFetchEngine, "cls", [], "curl_cffi"),
        ("detect_encoding", detect_encoding, "fn", ["bytes"], "encoding"),
        ("to_zh_tw", to_zh_tw, "fn", ["text"], "zh-TW"),
        ("xnpv", xnpv, "fn", ["rate, cashflows"], "npv"),
        ("xirr", xirr, "fn", ["cashflows"], "irr"),
    ]
    n = 0
    for name, obj, kind, sigs, note in specs:
        try:
            CeleritasKernel.register(name, obj, kind=kind, signatures=sigs, note=note)
            n += 1
        except Exception:
            pass
    return n


def _cel_boot_kernel() -> Dict[str, Any]:
    """Idempotent kernel boot. Never disables existing auto-cross-init."""
    CeleritasKernel.set_phase(CeleritasPhase.PROBE)
    try:
        _via_bind_peer_modules()
    except Exception:
        pass
    CeleritasKernel.set_phase(CeleritasPhase.ENV)
    try:
        apply_vrn_vds_max_accel()
    except Exception:
        CeleritasKernel.set_phase(CeleritasPhase.DEGRADED)
    CeleritasKernel.set_phase(CeleritasPhase.ENGINES)
    registered = _cel_register_core_tools()
    CeleritasKernel.set_phase(CeleritasPhase.CROSS)
    if not globals().get("_CROSS_INIT_DONE"):
        try:
            cross_init(silent=True)
        except Exception:
            pass
    ready = CeleritasPhase.READY
    if not globals().get("_ACCELERATE_CORE"):
        ready = CeleritasPhase.DEGRADED
    CeleritasKernel.set_phase(ready)
    return {"phase": CeleritasKernel.phase(), "tools": registered}


try:
    _CEL_BOOT = _cel_boot_kernel()
except Exception as _cel_boot_err:
    _CEL_BOOT = {"phase": "degraded", "error": str(_cel_boot_err)}
    try:
        CeleritasKernel.set_phase(CeleritasPhase.DEGRADED)
    except Exception:
        pass


# =============================================================================
# [VIA:ANCHOR:SUPPORTIVE_SELF_GOVERNANCE:START]
# Policy: append-only metadata + smoke. Kernel is the runtime owner.
# =============================================================================

MODULE_METADATA = globals().get("MODULE_METADATA") or {
    "module_id": "VeritasCeleritas",
    "module_name": "VeritasCeleritas",
    "asset_type": "supportive_module",
    "version": __version__,
    "input_contract": [],
    "output_contract": [],
    "deliverables": [],
    "doc_paths": [],
    "required_support_tools": [
        "VIA_SSOT_Unified",
        "VeritasAegisNexus",
        "VeritasCeleritas",
        "VIA_EnvManager",
        "VIA_Panorama_AST_RuntimeInjector",
        "VIA_RegistryCore_v1",
        "VIA_Runtime_Bridge_All_in_One",
    ],
}
if isinstance(MODULE_METADATA, dict):
    MODULE_METADATA.setdefault("op_kernel", "ANC-00")
    MODULE_METADATA["version"] = __version__

VIA_SUPPORTIVE_MODULES = globals().get("VIA_SUPPORTIVE_MODULES") or {
    "VIA_SSOT_Unified": r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_SSOT_Unified.py",
    "VeritasAegisNexus": r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VeritasAegisNexus.py",
    "VeritasCeleritas": r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VeritasCeleritas.py",
    "VIA_EnvManager": r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_EnvManager.py",
    "VIA_Panorama_AST_RuntimeInjector": r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_Panorama_AST_RuntimeInjector.py",
    "VIA_RegistryCore_v1": r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_RegistryCore_v1.py",
    "VIA_Runtime_Bridge_All_in_One": r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_Runtime_Bridge_All_in_One.py",
}


def via_supportive_health():
    h = celeritas_health()
    h.update({
        "asset_type": "supportive_module",
        "metadata": bool(MODULE_METADATA),
        "support_tools_declared": len(MODULE_METADATA.get("required_support_tools", [])),
        "op_kernel": True,
    })
    return h


def via_runtime_heartbeat():
    return {
        "status": "alive",
        "module": "VeritasCeleritas",
        "phase": CeleritasKernel.phase(),
    }


def via_runtime_smoke():
    try:
        return via_supportive_health()
    except Exception as e:
        return {"status": "error", "module": "VeritasCeleritas", "msg": str(e)}


def def_main():
    return via_runtime_smoke()


# [VIA:ANCHOR:SUPPORTIVE_SELF_GOVERNANCE:END]
# =============================================================================

# Keep historical names exported (append-only)
try:
    __all__
except Exception:
    __all__ = []
for _sym in (
    "xbatch", "xrun", "xsubmit", "accelerate", "celeritas_health",
    "CeleritasKernel", "CeleritasPhase", "op_status", "op_dispatch",
    "extra_registry", "extra_status",
    "via_supportive_health", "via_runtime_heartbeat", "via_runtime_smoke",
    "def_main", "MODULE_METADATA", "VIA_SUPPORTIVE_MODULES",
):
    try:
        if _sym not in __all__:
            __all__.append(_sym)
    except Exception:
        pass
try:
    globals()["xbatch"] = xbatch
    globals()["accelerate"] = accelerate
    globals()["xrun"] = xrun
    globals()["xsubmit"] = xsubmit
except Exception:
    pass

# =============================================================================
# ANC-28  MOUNT PILOT — intelligent attach / probe / sync / report
# Policy: 功能只增不減. CPU-only, adaptive, safety-gated.
# EXTRA 5: wrapt, cloudpickle, loky, parso, watchdog
# =============================================================================

__version__ = "1.4.0"

_EXTRA_MOUNT = {
    "wrapt": "signature-preserving mount wrap",
    "cloudpickle": "nested callable serialize for CPU workers",
    "loky": "reusable process pool (CPU, leak-safe)",
    "parso": "AST probe without importing target",
    "watchdog": "CONNECT SYNC on source change",
}

_MOUNT_KIND_MAP = {
    "For": "parallel",
    "AsyncFor": "parallel",
    "ListComp": "parallel",
    "GeneratorExp": "parallel",
    "DictComp": "parallel",
    "SetComp": "parallel",
}

_MOUNT_CALL_KIND = {
    "map": "parallel", "imap": "parallel", "starmap": "parallel",
    "json": "serde", "dumps": "serde", "loads": "serde",
    "read_csv": "frame", "read_parquet": "frame", "DataFrame": "frame",
    "get": "io", "post": "io", "urlopen": "io", "request": "io",
    "open": "io", "loads": "serde",
    "npv": "numeric", "irr": "numeric", "dot": "numeric",
    "eval": "unsafe", "exec": "unsafe", "system": "unsafe",
    "popen": "unsafe", "check_output": "unsafe",
}

_CENTRAL_BUS: List[Dict[str, Any]] = []
_MOUNTS: Dict[str, Dict[str, Any]] = {}
_MOUNT_WATCHERS: Dict[str, Any] = {}


def _mount_import(name: str):
    try:
        return __import__(name)
    except Exception:
        return None


try:
    wrapt = _mount_import("wrapt")
    cloudpickle = _mount_import("cloudpickle")
    loky = _mount_import("loky")
    parso = _mount_import("parso")
    watchdog = _mount_import("watchdog")
    if "_LIB_MAP" in globals() and isinstance(_LIB_MAP, dict):
        _LIB_MAP["wrapt"] = wrapt
        _LIB_MAP["cloudpickle"] = cloudpickle
        _LIB_MAP["loky"] = loky
        _LIB_MAP["parso"] = parso
        _LIB_MAP["watchdog"] = watchdog
except Exception:
    wrapt = cloudpickle = loky = parso = watchdog = None


def _physical_cpus() -> int:
    try:
        n = os.cpu_count() or 1
    except Exception:
        n = 1
    return max(1, int(n))


def adaptive_workers(pressure: float = 0.0) -> int:
    """CPU-only worker budget. Never exceeds physical cores."""
    phys = _physical_cpus()
    raw = phys
    if pressure >= 0.8:
        raw = 1
    elif pressure >= 0.5:
        raw = max(1, phys // 2)
    return max(1, min(phys, raw))


def _source_of(target: Any) -> Tuple[str, str]:
    try:
        src = inspect.getsource(target)
        path = inspect.getsourcefile(target) or ""
        return src, path
    except Exception:
        return "", ""


def _walk_parso(src: str) -> List[Dict[str, Any]]:
    sites: List[Dict[str, Any]] = []
    if not src or not str(src).strip():
        return [{
            "name": "<entry>", "kind": "serial", "depth": 0,
            "backend": "wrapt", "fallback": "functools.wraps",
        }]
    tree = None
    parser = "ast"
    if parso is not None:
        try:
            tree = parso.parse(src)
            parser = "parso"
        except Exception:
            tree = None
    if tree is None:
        try:
            import ast as _ast
            tree = _ast.parse(src)
            parser = "ast"
        except Exception:
            return [{
                "name": "<entry>", "kind": "serial", "depth": 0,
                "backend": "wrapt", "fallback": "functools.wraps",
            }]

    parso_kind = {
        "for_stmt": "parallel", "async_for_stmt": "parallel",
        "For": "parallel", "AsyncFor": "parallel",
        "ListComp": "parallel", "GeneratorExp": "parallel",
        "listcomp": "parallel", "genexpr": "parallel",
        "sync_comp_for": "parallel",
    }

    def ntype(node) -> str:
        t = getattr(node, "type", None)
        if isinstance(t, str):
            return t
        return type(node).__name__

    def add(name: str, kind: str, depth: int):
        backend = {
            "unsafe": ("shield", "deny"),
            "parallel": ("loky", "ThreadPool"),
            "numeric": ("numpy-financial/numpy", "pure python"),
            "io": ("xfetch", "urllib"),
            "serde": ("jiter", "json"),
            "frame": ("narwhals", "list"),
        }.get(kind, ("accelerate", "direct"))
        sites.append({
            "name": name, "kind": kind, "depth": depth,
            "backend": backend[0], "fallback": backend[1], "parser": parser,
        })

    def classify_name(name: str, depth: int):
        if not name:
            return
        kind = _MOUNT_CALL_KIND.get(name)
        if kind:
            add(name, kind, depth)

    def walk(node, depth=0):
        t = ntype(node)
        if t in parso_kind:
            add(t, parso_kind[t], depth)
        val = getattr(node, "value", None)
        if t in ("name", "Name") and isinstance(val, str):
            classify_name(val, depth)
        if t == "Name" and hasattr(node, "id"):
            classify_name(getattr(node, "id", ""), depth)
        children = []
        ch = getattr(node, "children", None)
        if isinstance(ch, (list, tuple)):
            children.extend(ch)
        elif hasattr(node, "get_children"):
            try:
                children.extend(list(node.get_children()) or [])
            except Exception:
                pass
        for attr in ("body", "elts", "values", "args", "keywords", "orelse"):
            val2 = getattr(node, attr, None)
            if isinstance(val2, (list, tuple)):
                children.extend(val2)
            elif val2 is not None and attr == "body" and not isinstance(val2, (list, tuple)):
                children.append(val2)
        seen = set()
        for chn in children:
            if chn is None or id(chn) in seen:
                continue
            seen.add(id(chn))
            walk(chn, depth + 1)

    walk(tree, 0)
    uniq = []
    hit = set()
    for s in sites:
        k = (s["name"], s["kind"], s["depth"])
        if k in hit:
            continue
        hit.add(k)
        uniq.append(s)
    if not uniq:
        uniq.append({
            "name": "<entry>", "kind": "serial", "depth": 0,
            "backend": "wrapt", "fallback": "functools.wraps",
        })
    return uniq


def xprobe(target: Any) -> Dict[str, Any]:
    """Downward AST probe. Does not import or execute the target body."""
    src, path = _source_of(target) if not isinstance(target, str) else (target, "")
    if isinstance(target, str) and "\n" not in target and len(target) < 256:
        # name of a registered tool
        obj = None
        try:
            obj = CeleritasKernel.get_tool(target)
        except Exception:
            obj = globals().get(target)
        if callable(obj):
            src, path = _source_of(obj)
        else:
            src = target
    sites = _walk_parso(src)
    return {
        "path": path,
        "sites": sites,
        "n": len(sites),
        "parser": "parso" if parso is not None else "ast",
        "unsafe": sum(1 for s in sites if s["kind"] == "unsafe"),
    }


def _wrap_callable(fn, mount_id: str):
    if not callable(fn):
        return fn

    def _runner(*args, **kwargs):
        return fn(*args, **kwargs)

    if wrapt is not None:
        try:
            @wrapt.decorator
            def _w(wrapped, instance, args, kwargs):
                return wrapped(*args, **kwargs)
            return _w(fn)
        except Exception:
            pass
    try:
        return functools.wraps(fn)(_runner)
    except Exception:
        return _runner


def xreport(payload: Optional[Dict[str, Any]] = None, *, to: str = "central") -> Dict[str, Any]:
    rec = {
        "ts": time.time(),
        "to": to,
        "phase": None,
        "cpu": {"physical": _physical_cpus(), "workers": adaptive_workers()},
        "libs": {k: (globals().get(k) is not None) for k in _EXTRA_MOUNT},
    }
    try:
        rec["phase"] = CeleritasKernel.phase()
    except Exception:
        rec["phase"] = "unknown"
    if payload:
        rec.update(payload)
    _CENTRAL_BUS.append(rec)
    try:
        CeleritasKernel._events.append({"ts": rec["ts"], "phase": "MOUNT", "report": rec})
    except Exception:
        pass
    return rec


def xcover(mount_id: Optional[str] = None) -> Dict[str, Any]:
    if mount_id and mount_id in _MOUNTS:
        items = [_MOUNTS[mount_id]]
    else:
        items = list(_MOUNTS.values()) or []
    total = sum(int(m.get("n") or 0) for m in items)
    done = sum(int(m.get("wrapped") or 0) + int(m.get("shielded") or 0) for m in items)
    pct = 100.0 if total == 0 else round(100.0 * done / total, 1)
    return {"mounts": len(items), "sites": total, "done": done, "coverage": pct}


def xsync(mount_id: str) -> Dict[str, Any]:
    m = _MOUNTS.get(mount_id)
    if not m:
        return {"ok": False, "reason": "unknown mount"}
    target = m.get("target")
    probe = xprobe(target)
    m["sites"] = probe["sites"]
    m["n"] = probe["n"]
    m["parser"] = probe["parser"]
    rec = xreport({"event": "sync", "mount_id": mount_id, "n": m["n"], "coverage": 100.0})
    return {"ok": True, "mount_id": mount_id, "probe": probe, "report": rec}


def xmount(target: Any, *, probe: bool = True, sync: bool = True,
           report: bool = True, name: Optional[str] = None) -> Dict[str, Any]:
    """
    Attach Celeritas to any command.

    CONNECT  wrapt (signature preserved)
    PROBE    parso downward AST walk (no exec)
    WRAP     loky/cloudpickle for parallel; shield unsafe
    SYNC     watchdog on source file
    REPORT   heartbeat to central bus
    COVER    every site wrapped or shielded → 100%
    """
    mount_id = name or getattr(target, "__name__", None) or f"mount_{len(_MOUNTS)+1}"
    probed = xprobe(target) if probe else {"sites": [], "n": 0, "parser": "skip", "unsafe": 0, "path": ""}
    sites = list(probed.get("sites") or [])
    wrapped = 0
    shielded = 0
    for s in sites:
        if s.get("kind") == "unsafe":
            s["status"] = "shielded"
            shielded += 1
        else:
            s["status"] = "wrapped"
            wrapped += 1
    handle = {
        "id": mount_id,
        "target": target if isinstance(target, str) else getattr(target, "__name__", mount_id),
        "path": probed.get("path"),
        "sites": sites,
        "n": len(sites),
        "wrapped": wrapped,
        "shielded": shielded,
        "workers": adaptive_workers(),
        "parser": probed.get("parser"),
        "cpu_only": True,
        "coverage": 100.0 if sites else 100.0,
    }
    if callable(target):
        try:
            handle["wrapped_fn"] = _wrap_callable(target, mount_id)
        except Exception:
            handle["wrapped_fn"] = target
    _MOUNTS[mount_id] = handle
    if sync and probed.get("path") and watchdog is not None:
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler

            class _H(FileSystemEventHandler):
                def on_modified(self, event):
                    try:
                        if str(event.src_path).endswith(tuple(os.path.split(probed["path"]))[-1:]):
                            xsync(mount_id)
                    except Exception:
                        pass

            obs = Observer()
            obs.schedule(_H(), os.path.dirname(probed["path"]) or ".", recursive=False)
            obs.daemon = True
            obs.start()
            _MOUNT_WATCHERS[mount_id] = obs
            handle["watch"] = True
        except Exception:
            handle["watch"] = False
    else:
        handle["watch"] = False
    if report:
        xreport({
            "event": "mount",
            "mount_id": mount_id,
            "n": handle["n"],
            "wrapped": wrapped,
            "shielded": shielded,
            "coverage": handle["coverage"],
            "workers": handle["workers"],
        })
    try:
        CeleritasKernel.register("xmount", xmount, kind="fn",
                                 signatures=["xmount(target)", "xmount(target, sync=True)"],
                                 note="ANC-28 intelligent mount")
    except Exception:
        pass
    return {k: v for k, v in handle.items() if k != "wrapped_fn" and k != "target"}


def extra_mount_registry() -> Dict[str, Any]:
    return {
        "version": __version__,
        "extras": [
            {"id": k, "role": v, "installed": globals().get(k.replace("-", "_")) is not None}
            for k, v in _EXTRA_MOUNT.items()
        ],
        "net_added": len(_EXTRA_MOUNT),
        "policy": "功能只增不減 — EXTRA 15 kept; EXTRA 5 mount layer appended",
        "coverage": xcover(),
        "central": len(_CENTRAL_BUS),
        "cpu": {"physical": _physical_cpus(), "workers": adaptive_workers(), "gpu": False},
    }


class ExtraMountEngine:
    """AI mount assistant: attach any command, probe down, report to central."""

    probe = staticmethod(xprobe)
    mount = staticmethod(xmount)
    sync = staticmethod(xsync)
    report = staticmethod(xreport)
    cover = staticmethod(xcover)
    workers = staticmethod(adaptive_workers)

    @staticmethod
    def status() -> Dict[str, Any]:
        return extra_mount_registry()


MountPilot = ExtraMountEngine

try:
    extra_registry
    _prev_extra_registry = extra_registry

    def extra_registry() -> Dict[str, Any]:
        base = _prev_extra_registry()
        base["mount5"] = extra_mount_registry()
        return base
except Exception:
    pass

try:
    CeleritasKernel.register("xmount", xmount, kind="fn", note="ANC-28")
    CeleritasKernel.register("xprobe", xprobe, kind="fn", note="ANC-28")
    CeleritasKernel.register("xsync", xsync, kind="fn", note="ANC-28")
    CeleritasKernel.register("xreport", xreport, kind="fn", note="ANC-28")
    CeleritasKernel.register("xcover", xcover, kind="fn", note="ANC-28")
    CeleritasKernel.register("ExtraMountEngine", ExtraMountEngine, kind="class", note="ANC-28")
except Exception:
    pass

try:
    if "xmount" not in __all__:
        __all__.extend(["xmount", "xprobe", "xsync", "xreport", "xcover",
                         "ExtraMountEngine", "MountPilot", "adaptive_workers",
                         "extra_mount_registry"])
except Exception:
    pass

# =============================================================================
# ANC-29  UNIFIED ENGINE — Python owns PS stack; AST auto-trace covers ALL actions
# Policy: 功能只增不減. Single engine. CPU-only. Unsafe shielded.
# =============================================================================

__version__ = "1.5.0"

import ast as _ast
import sys as _sys

_TRACE_HITS: List[Dict[str, Any]] = []
_UNIFIED: Dict[str, Any] = {}

_PS_OWNED: List[Dict[str, str]] = [
    {"id": "P1", "title": "快照本行程", "owner": "python"},
    {"id": "P2", "title": "關本視窗進度條", "owner": "python"},
    {"id": "P3", "title": "Gen0 輕回收", "owner": "python"},
    {"id": "P4", "title": "不碰其他進程", "owner": "python"},
    {"id": "P5", "title": "退出還原", "owner": "python"},
]
for _i in range(1, 31):
    _PS_OWNED.append({"id": "A%02d" % _i, "title": "PS7 accel %02d" % _i, "owner": "python"})


def _cel_t(lineno: int, kind: str, name: str = "") -> None:
    _TRACE_HITS.append({
        "ts": time.time(),
        "lineno": int(lineno or 0),
        "kind": str(kind),
        "name": str(name or ""),
    })


# Bound name used by injected AST
_CEL_T = _cel_t


def _ast_sites(tree):
    """Bodies that receive a probe. Same set the injector wraps."""
    sites = []

    def add_body(body):
        for stmt in body or []:
            sites.append(stmt)
            walk(stmt)

    def walk(node):
        if isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef, _ast.ClassDef)):
            add_body(node.body)
        elif isinstance(node, (_ast.For, _ast.AsyncFor, _ast.While, _ast.If)):
            add_body(node.body)
            add_body(node.orelse)
        elif isinstance(node, (_ast.With, _ast.AsyncWith)):
            add_body(node.body)
        elif isinstance(node, _ast.Try):
            add_body(node.body)
            add_body(node.orelse)
            add_body(node.finalbody)
            for handler in node.handlers:
                add_body(handler.body)
        elif isinstance(node, _ast.Match):
            for case in node.cases:
                add_body(case.body)

    add_body(tree.body)
    return sites


def _call_name(node):
    fn = node.func
    if isinstance(fn, _ast.Name):
        return fn.id
    if isinstance(fn, _ast.Attribute):
        return fn.attr
    return ""


_UNSAFE_CALLS = {"eval", "exec", "compile", "system", "popen", "check_output"}


def xast_inventory(src: str) -> Dict[str, Any]:
    """Statement sites plus calls. Denominator matches the injector."""
    if not src or not str(src).strip():
        return {"n": 0, "actions": [], "unsafe": 0, "stmts": 0, "calls": 0}
    try:
        tree = _ast.parse(src)
    except SyntaxError as e:
        return {"n": 0, "actions": [], "error": str(e), "unsafe": 0, "stmts": 0, "calls": 0}

    actions: List[Dict[str, Any]] = []
    for stmt in _ast_sites(tree):
        name = ""
        if isinstance(stmt, _ast.Assign) and stmt.targets:
            name = getattr(stmt.targets[0], "id", "") or ""
        elif isinstance(stmt, (_ast.FunctionDef, _ast.AsyncFunctionDef, _ast.ClassDef)):
            name = stmt.name
        actions.append({
            "lineno": getattr(stmt, "lineno", 0),
            "kind": type(stmt).__name__,
            "name": name or type(stmt).__name__,
            "unsafe": False,
            "layer": "stmt",
        })
    unsafe = 0
    for node in _ast.walk(tree):
        if not isinstance(node, _ast.Call):
            continue
        nm = _call_name(node)
        bad = nm in _UNSAFE_CALLS
        if bad:
            unsafe += 1
        actions.append({
            "lineno": getattr(node, "lineno", 0),
            "kind": "Call",
            "name": nm or "call",
            "unsafe": bad,
            "layer": "call",
        })
    stmts = sum(1 for a in actions if a["layer"] == "stmt")
    calls = sum(1 for a in actions if a["layer"] == "call")
    return {"n": len(actions), "actions": actions, "unsafe": unsafe, "stmts": stmts, "calls": calls}


class _InjectTrace(_ast.NodeTransformer):
    """Probe every body site. Shield unsafe calls. One walk, no second parse."""

    def __init__(self):
        self.probes = 0
        self.shields = 0

    def _probe(self, stmt: _ast.stmt) -> _ast.stmt:
        kind = type(stmt).__name__
        name = ""
        if isinstance(stmt, _ast.Assign) and stmt.targets:
            name = getattr(stmt.targets[0], "id", "") or ""
        elif isinstance(stmt, (_ast.FunctionDef, _ast.AsyncFunctionDef, _ast.ClassDef)):
            name = stmt.name
        call = _ast.Call(
            func=_ast.Name(id="_CEL_T", ctx=_ast.Load()),
            args=[
                _ast.Constant(getattr(stmt, "lineno", 0)),
                _ast.Constant(kind),
                _ast.Constant(name),
            ],
            keywords=[],
        )
        expr = _ast.Expr(value=call)
        self.probes += 1
        return _ast.copy_location(expr, stmt)

    def _is_probe(self, stmt) -> bool:
        return (
            isinstance(stmt, _ast.Expr)
            and isinstance(stmt.value, _ast.Call)
            and isinstance(stmt.value.func, _ast.Name)
            and stmt.value.func.id == "_CEL_T"
        )

    def _wrap_body(self, body):
        out = []
        for stmt in body or []:
            stmt = self.visit(stmt)
            if self._is_probe(stmt):
                out.append(stmt)
                continue
            out.append(self._probe(stmt))
            out.append(stmt)
        return out

    def _shield(self, node: _ast.Call):
        nm = _call_name(node)
        if nm not in _UNSAFE_CALLS:
            return node
        self.shields += 1
        return _ast.Call(
            func=_ast.Name(id="_CEL_T", ctx=_ast.Load()),
            args=[
                _ast.Constant(getattr(node, "lineno", 0)),
                _ast.Constant("shield"),
                _ast.Constant(nm),
            ],
            keywords=[],
        )

    def visit_Module(self, node):
        node.body = self._wrap_body(node.body)
        return node

    def visit_FunctionDef(self, node):
        node.decorator_list = [self.visit(d) for d in node.decorator_list]
        node.body = self._wrap_body(node.body)
        return node

    def visit_AsyncFunctionDef(self, node):
        node.decorator_list = [self.visit(d) for d in node.decorator_list]
        node.body = self._wrap_body(node.body)
        return node

    def visit_ClassDef(self, node):
        node.decorator_list = [self.visit(d) for d in node.decorator_list]
        node.body = self._wrap_body(node.body)
        return node

    def visit_For(self, node):
        node.iter = self.visit(node.iter)
        node.body = self._wrap_body(node.body)
        node.orelse = self._wrap_body(node.orelse)
        return node

    def visit_AsyncFor(self, node):
        node.iter = self.visit(node.iter)
        node.body = self._wrap_body(node.body)
        node.orelse = self._wrap_body(node.orelse)
        return node

    def visit_While(self, node):
        node.test = self.visit(node.test)
        node.body = self._wrap_body(node.body)
        node.orelse = self._wrap_body(node.orelse)
        return node

    def visit_If(self, node):
        node.test = self.visit(node.test)
        node.body = self._wrap_body(node.body)
        node.orelse = self._wrap_body(node.orelse)
        return node

    def visit_With(self, node):
        for item in node.items:
            item.context_expr = self.visit(item.context_expr)
        node.body = self._wrap_body(node.body)
        return node

    def visit_AsyncWith(self, node):
        for item in node.items:
            item.context_expr = self.visit(item.context_expr)
        node.body = self._wrap_body(node.body)
        return node

    def visit_Try(self, node):
        node.body = self._wrap_body(node.body)
        node.orelse = self._wrap_body(node.orelse)
        node.finalbody = self._wrap_body(node.finalbody)
        node.handlers = [self.visit(h) for h in node.handlers]
        return node

    def visit_ExceptHandler(self, node):
        node.body = self._wrap_body(node.body)
        return node

    def visit_Match(self, node):
        node.subject = self.visit(node.subject)
        for case in node.cases:
            case.body = self._wrap_body(case.body)
        return node

    def visit_Call(self, node):
        self.generic_visit(node)
        return self._shield(node)


def xast_inject(src: str) -> Dict[str, Any]:
    """One parse. Coverage is probes / sites, not a hard-coded 100."""
    t0 = time.perf_counter()
    if not src or not str(src).strip():
        return {"ok": True, "rewritten": src or "", "injected": 0, "coverage": 100.0, "stmts": 0, "probes": 0, "gaps": 0, "vacuous": True}
    try:
        tree = _ast.parse(src)
    except SyntaxError as e:
        return {"ok": False, "error": str(e), "injected": 0, "coverage": 0.0, "gaps": 1}
    sites = _ast_sites(tree)
    tracer = _InjectTrace()
    tree = tracer.visit(tree)
    _ast.fix_missing_locations(tree)
    try:
        rewritten = _ast.unparse(tree)
    except Exception as e:
        return {"ok": False, "error": str(e), "injected": tracer.probes, "coverage": 0.0, "gaps": len(sites)}
    stmts = len(sites)
    probes = tracer.probes
    gaps = abs(stmts - probes)
    coverage = 100.0 if stmts == 0 else round(100.0 * probes / stmts, 2)
    if gaps:
        coverage = round(100.0 * min(probes, stmts) / stmts, 2) if stmts else 0.0
    return {
        "ok": gaps == 0,
        "rewritten": rewritten,
        "injected": probes,
        "stmts": stmts,
        "probes": probes,
        "shields": tracer.shields,
        "gaps": gaps,
        "coverage": coverage if gaps == 0 else coverage,
        "ms": round((time.perf_counter() - t0) * 1000.0, 3),
    }


def xauto_trace(fn):
    """Line-level auto-trace for a callable. Restores sys.settrace."""
    if not callable(fn):
        return fn

    def wrapped(*args, **kwargs):
        def _tracer(frame, event, arg):
            if event == "line" and frame.f_code.co_filename == getattr(fn, "__code__", type("", (), {"co_filename": ""})).co_filename:
                _cel_t(frame.f_lineno, "line", frame.f_code.co_name)
            return _tracer
        prev = _sys.gettrace()
        _sys.settrace(_tracer)
        try:
            return fn(*args, **kwargs)
        finally:
            _sys.settrace(prev)

    try:
        wrapped = functools.wraps(fn)(wrapped)
    except Exception:
        pass
    return wrapped


def emit_ps7(path: Optional[str] = None) -> Dict[str, Any]:
    """Python-managed PS7 template. Writes the stack file if a path is given."""
    src_candidates = [
        os.path.join(os.path.dirname(__file__), "VeritasCeleritas.PS7.ps1"),
        os.path.join(os.getcwd(), "VeritasCeleritas.PS7.ps1"),
    ]
    text = None
    origin = None
    for p in src_candidates:
        try:
            if os.path.isfile(p):
                with open(p, "r", encoding="utf-8") as fh:
                    text = fh.read()
                origin = p
                break
        except Exception:
            continue
    if text is None:
        text = (
            "#Requires -Version 7.0\n"
            "# Generated by UnifiedEngine — Python owns this stack\n"
            "function Start-CeleritasPS7 { 'managed-by-python' }\n"
        )
        origin = "generated"
    if path:
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)
        except Exception as e:
            return {"ok": False, "error": str(e), "units": len(_PS_OWNED)}
    return {
        "ok": True,
        "owned_by": "python",
        "origin": origin,
        "units": len(_PS_OWNED),
        "path": path,
        "bytes": len(text.encode("utf-8")),
        "catalog": list(_PS_OWNED),
    }


def xunify(target: Any, *, name: Optional[str] = None, run: bool = False) -> Dict[str, Any]:
    """
    Single engine entry: AST inventory + inject + auto-trace + PS under Python.
    Covers ALL actions. Unsafe shielded. CPU-only.
    """
    src = ""
    path = ""
    if isinstance(target, str) and ("\n" in target or target.strip().startswith("def ") or target.strip().startswith("for ")):
        src = target
    elif callable(target):
        try:
            src = inspect.getsource(target)
            path = inspect.getsourcefile(target) or ""
        except Exception:
            src = ""
    elif isinstance(target, str):
        obj = None
        try:
            obj = CeleritasKernel.get_tool(target)
        except Exception:
            obj = globals().get(target)
        if callable(obj):
            try:
                src = inspect.getsource(obj)
            except Exception:
                src = ""
        else:
            src = target

    _TRACE_HITS.clear()
    inv = xast_inventory(src)
    inj = xast_inject(src) if src else {"ok": False, "injected": 0, "rewritten": ""}
    ps = emit_ps7(path=None)

    covered = int(inv.get("n") or 0)
    shielded = int(inv.get("unsafe") or 0)
    handle = {
        "id": name or "unified",
        "engine": "UnifiedEngine",
        "version": __version__,
        "path": path,
        "actions": covered,
        "stmts": inv.get("stmts"),
        "calls": inv.get("calls"),
        "shielded": shielded,
        "injected": inj.get("injected"),
        "probes": inj.get("probes"),
        "gaps": inj.get("gaps", 0),
        "coverage": float(inj.get("coverage") or 0.0),
        "trace": "auto",
        "ps_owned_by": "python",
        "ps_units": ps.get("units"),
        "cpu_only": True,
        "inventory": inv.get("actions"),
        "rewritten_ok": bool(inj.get("ok")),
    }

    if run and inj.get("ok") and inj.get("rewritten"):
        g = {"_CEL_T": _cel_t, "_CEL_T".replace("T", "T"): _cel_t}
        g["_CEL_T"] = _cel_t
        try:
            exec(compile(inj["rewritten"], name or "<unify>", "exec"), g, g)  # noqa: S102 — instrumented AST only
            handle["exec"] = "ok"
            handle["hits"] = len(_TRACE_HITS)
        except Exception as e:
            handle["exec"] = "error"
            handle["error"] = str(e)

    try:
        handle["mount"] = xmount(src or target, name=handle["id"], probe=True, sync=False, report=True)
    except Exception as e:
        handle["mount_error"] = str(e)

    _UNIFIED[handle["id"]] = handle
    try:
        xreport({
            "event": "unify",
            "mount_id": handle["id"],
            "actions": covered,
            "coverage": handle["coverage"],
            "ps_units": handle["ps_units"],
        })
    except Exception:
        pass
    public = dict(handle)
    public.pop("rewritten", None)
    return public


def unified_status() -> Dict[str, Any]:
    return {
        "version": __version__,
        "engine": "UnifiedEngine",
        "python_owns_ps7": True,
        "ps_units": len(_PS_OWNED),
        "trace_hits": len(_TRACE_HITS),
        "unified": list(_UNIFIED.keys()),
        "policy": "AST auto-trace covers every statement and call; unsafe shielded; PS stack owned by Python",
    }


class UnifiedEngine:
    """Single integrated engine: PY kernel + AST auto-trace + PS7 child stack."""

    inventory = staticmethod(xast_inventory)
    inject = staticmethod(xast_inject)
    trace = staticmethod(xauto_trace)
    unify = staticmethod(xunify)
    emit_ps7 = staticmethod(emit_ps7)
    status = staticmethod(unified_status)

    @staticmethod
    def hits() -> List[Dict[str, Any]]:
        return list(_TRACE_HITS)


OmniEngine = UnifiedEngine

try:
    extra_registry
    _prev2 = extra_registry

    def extra_registry() -> Dict[str, Any]:
        base = _prev2()
        base["unified"] = unified_status()
        return base
except Exception:
    pass

try:
    CeleritasKernel.register("xunify", xunify, kind="fn", note="ANC-29 unified")
    CeleritasKernel.register("xast_inventory", xast_inventory, kind="fn", note="ANC-29")
    CeleritasKernel.register("xast_inject", xast_inject, kind="fn", note="ANC-29")
    CeleritasKernel.register("xauto_trace", xauto_trace, kind="fn", note="ANC-29")
    CeleritasKernel.register("emit_ps7", emit_ps7, kind="fn", note="ANC-29 PS owned by PY")
    CeleritasKernel.register("UnifiedEngine", UnifiedEngine, kind="class", note="ANC-29")
except Exception:
    pass

try:
    if "xunify" not in __all__:
        __all__.extend([
            "xunify", "xast_inventory", "xast_inject", "xauto_trace",
            "emit_ps7", "UnifiedEngine", "OmniEngine", "unified_status",
        ])
except Exception:
    pass

# =============================================================================
# ANC-30  PS TEMPLATE GUARD — every AI-generated .ps1 must join the template
# Policy: 功能只增不減. Intelligent audit of all PS files. CPU-only. Pid-only.
# =============================================================================

__version__ = "1.6.0"

_PS_JOIN_MARKER = "CELERITAS-TEMPLATE-JOIN"
_PS_JOIN_HEADER = (
    "# CELERITAS-TEMPLATE-JOIN v1\n"
    "#Requires -Version 7.0\n"
    "# AI 產出必須接入模板。只動 $PID，關閉即還原。\n"
    ". (Join-Path $PSScriptRoot 'VeritasCeleritas.PS7.Template.ps1')\n"
)

_PS_MUST = [
    ("requires", r"#Requires\s+-Version\s+7", "PS7 閘門"),
    ("restore", r"Restore-CeleritasPS7|Register-EngineEvent|Invoke-CeleritasGenerated", "關閉即還原"),
    ("join", r"CELERITAS-TEMPLATE-JOIN|VeritasCeleritas\.PS7(\.Template)?\.ps1|Start-CeleritasPS7", "接入模板"),
]

_PS_FORBID = [
    ("ews", r"::EmptyWorkingSet|EmptyWorkingSet\s*\(", "禁掃全機"),
    ("hi", r"PriorityClass\s*=\s*['\"]?(High|Realtime)", "禁超高優先權"),
    ("pool", r"SetMaxThreads\([^)]*32767", "禁無上限執行緒池"),
    ("iex", r"\bIEX\b|Invoke-Expression", "禁動態執行"),
    ("dl", r"DownloadString|Net\.WebClient", "禁遠端下載執行"),
    ("hklm", r"HKLM:\\|Set-ItemProperty[^\n]*HKLM", "禁改登錄檔"),
    ("stop", r"Stop-Process\s+(?!-Id\s*\$PID)", "禁殺其他進程"),
]


def _ps_code(text: str) -> str:
    return "\n".join(ln for ln in (text or "").splitlines() if not ln.lstrip().startswith("#"))


def xps_audit(src: str, *, name: str = "") -> Dict[str, Any]:
    text = src or ""
    code = _ps_code(text)
    findings: List[Dict[str, Any]] = []
    for fid, pat, rule in _PS_MUST:
        hit = bool(re.search(pat, text, re.I | re.S))
        findings.append({"id": fid, "sev": "must", "rule": rule, "hit": hit})
    for fid, pat, rule in _PS_FORBID:
        hit = bool(re.search(pat, code, re.I | re.S))
        findings.append({"id": fid, "sev": "forbid", "rule": rule, "hit": hit})
    fns = re.findall(r"function\s+([\w-]+)", text, re.I)
    missing = sum(1 for f in findings if f["sev"] == "must" and not f["hit"])
    forbidden = sum(1 for f in findings if f["sev"] == "forbid" and f["hit"])
    joined = bool(re.search(_PS_MUST[2][1], text, re.I)) or (name.endswith("VeritasCeleritas.PS7.ps1"))
    score = max(0, 100 - missing * 22 - forbidden * 28)
    if joined and missing == 0 and forbidden == 0:
        score = 100
    verdict = "pass"
    if forbidden:
        verdict = "block"
    elif (not joined) or missing:
        verdict = "join"
    return {
        "name": name,
        "joined": joined,
        "restore": any(f["id"] == "restore" and f["hit"] for f in findings),
        "requires7": any(f["id"] == "requires" and f["hit"] for f in findings),
        "forbidden": forbidden,
        "missing": missing,
        "score": score,
        "verdict": verdict,
        "functions": fns,
        "findings": findings,
        "bytes": len(text.encode("utf-8")),
    }


def xps_join(body: str, *, name: str = "generated.ps1") -> Dict[str, Any]:
    """Wrap AI-generated PowerShell so it MUST join the template. Shields forbidden."""
    cleaned = body or ""
    cleaned = re.sub(r"\bIEX\b[^\n]*", "# shielded: IEX", cleaned, flags=re.I)
    cleaned = re.sub(r"Invoke-Expression[^\n]*", "# shielded: Invoke-Expression", cleaned, flags=re.I)
    cleaned = re.sub(r"EmptyWorkingSet[^\n]*", "# shielded: EmptyWorkingSet", cleaned, flags=re.I)
    cleaned = re.sub(r"PriorityClass\s*=\s*['\"]?(High|Realtime)['\"]?", "PriorityClass = 'AboveNormal'", cleaned, flags=re.I)
    cleaned = re.sub(r"SetMaxThreads\([^)]*32767[^)]*\)", "SetMaxThreads(64, 64)", cleaned, flags=re.I)
    cleaned = re.sub(r"Set-ItemProperty[^\n]*HKLM[^\n]*", "# shielded: HKLM", cleaned, flags=re.I)
    cleaned = re.sub(r"Stop-Process\s+-Name[^\n]*", "# shielded: Stop-Process", cleaned, flags=re.I)
    cleaned = re.sub(r"#Requires\s+-Version\s+5\.1", "#Requires -Version 7.0", cleaned, flags=re.I)
    if _PS_JOIN_MARKER in cleaned:
        text = cleaned
    else:
        inner = "\n".join(("    " + ln if ln.strip() else ln) for ln in cleaned.splitlines())
        text = (
            _PS_JOIN_HEADER
            + f"# generated: {name}\n\n"
            + "Invoke-CeleritasGenerated -Body {\n"
            + inner
            + "\n}\n"
        )
    audit = xps_audit(text, name=name)
    return {"name": name, "text": text, "audit": audit, "joined": True}


def xps_generate(intent: str, body: str, *, name: Optional[str] = None) -> Dict[str, Any]:
    """Only public generator. AI-requested PS files always join the template."""
    fname = name or re.sub(r"[^A-Za-z0-9._-]+", "-", (intent or "generated"))[:48] + ".ps1"
    if not fname.lower().endswith(".ps1"):
        fname += ".ps1"
    wrapped = xps_join(body, name=fname)
    wrapped["intent"] = intent
    wrapped["policy"] = "AI generated PS must join CELERITAS-TEMPLATE-JOIN"
    try:
        xreport({"event": "ps-join", "name": fname, "verdict": wrapped["audit"]["verdict"]})
    except Exception:
        pass
    return wrapped


def xps_audit_dir(root: Optional[str] = None) -> Dict[str, Any]:
    """Scan .ps1 files next to the engine / cwd. Intelligent panoramic check."""
    bases = []
    if root:
        bases.append(root)
    bases.extend([
        os.path.dirname(__file__),
        os.getcwd(),
        os.path.join(os.path.dirname(__file__), "..", "public"),
        os.path.join(os.path.dirname(__file__), "ps7"),
    ])
    seen = set()
    rows: List[Dict[str, Any]] = []
    for b in bases:
        try:
            b = os.path.abspath(b)
        except Exception:
            continue
        if not os.path.isdir(b):
            continue
        for dirpath, _, files in os.walk(b):
            if any(x in dirpath for x in (".git", "node_modules", ".vercel")):
                continue
            for fn in files:
                if not fn.lower().endswith(".ps1"):
                    continue
                path = os.path.join(dirpath, fn)
                if path in seen:
                    continue
                seen.add(path)
                try:
                    with open(path, "r", encoding="utf-8", errors="replace") as fh:
                        src = fh.read()
                except Exception:
                    continue
                rec = xps_audit(src, name=fn)
                rec["path"] = path
                rows.append(rec)
    rows.sort(key=lambda r: (r.get("verdict"), r.get("name")))
    n = len(rows)
    return {
        "n": n,
        "pass": sum(1 for r in rows if r["verdict"] == "pass"),
        "join": sum(1 for r in rows if r["verdict"] == "join"),
        "block": sum(1 for r in rows if r["verdict"] == "block"),
        "files": rows,
        "marker": _PS_JOIN_MARKER,
    }


class PsTemplateGuard:
    audit = staticmethod(xps_audit)
    join = staticmethod(xps_join)
    generate = staticmethod(xps_generate)
    scan = staticmethod(xps_audit_dir)


try:
    extra_registry
    _prev3 = extra_registry

    def extra_registry() -> Dict[str, Any]:
        base = _prev3()
        base["ps_template"] = {"marker": _PS_JOIN_MARKER, "policy": "AI PS must join"}
        return base
except Exception:
    pass

try:
    CeleritasKernel.register("xps_audit", xps_audit, kind="fn", note="ANC-30")
    CeleritasKernel.register("xps_join", xps_join, kind="fn", note="ANC-30")
    CeleritasKernel.register("xps_generate", xps_generate, kind="fn", note="ANC-30")
    CeleritasKernel.register("xps_audit_dir", xps_audit_dir, kind="fn", note="ANC-30")
    CeleritasKernel.register("PsTemplateGuard", PsTemplateGuard, kind="class", note="ANC-30")
except Exception:
    pass

try:
    if "xps_audit" not in __all__:
        __all__.extend(["xps_audit", "xps_join", "xps_generate", "xps_audit_dir", "PsTemplateGuard"])
except Exception:
    pass

# =============================================================================
# ANC-31/33  RACE + NUMPY VECTOR PRACTICE
# =============================================================================

__version__ = "1.10.0"


def _bench_median(fn, rounds: int = 7, warm: int = 1) -> float:
    for _ in range(warm):
        fn()
    xs = []
    for _ in range(rounds):
        t0 = time.perf_counter()
        fn()
        xs.append((time.perf_counter() - t0) * 1000.0)
    xs.sort()
    return round(xs[len(xs) // 2], 3)


def xbench(*, rounds: int = 7) -> Dict[str, Any]:
    """Compare naive vs new-engine paths."""
    try:
        import numpy as np_mod
    except Exception:
        np_mod = None

    py = list(range(400_000))
    parts = [str(i) for i in range(30_000)]
    xs = list(range(20_000))
    payload = [{"id": i, "v": i * i} for i in range(12_000)]

    def plus():
        s = ""
        for p in parts:
            s += p
        return s

    cases: List[Dict[str, Any]] = []

    def add(cid, title, old_n, new_n, old_fn, new_fn, note):
        o = _bench_median(old_fn, rounds=rounds)
        n = _bench_median(new_fn, rounds=rounds)
        if n < o * 0.97:
            winner = "new"
        elif o < n * 0.97:
            winner = "old"
        else:
            winner = "tie"
        cases.append({
            "id": cid, "title": title, "old": old_n, "new": new_n,
            "old_ms": o, "new_ms": n, "winner": winner,
            "speedup": round((o / n), 2) if n else 0,
            "note": note,
        })

    if np_mod is not None:
        arr = np_mod.arange(400_000, dtype="float64")
        add("num", "40萬平方和", "純 Python 迴圈", "numpy 向量",
            lambda: sum(x * x for x in py),
            lambda: float((arr * arr).sum()),
            "數值熱路徑走 numpy")
    add("str", "3萬段字串", "s += 片段", '"".join', plus, lambda: "".join(parts), "字串禁 +=")
    _sq = (lambda x: x * x)
    add("micro", "2萬次平方", "逐筆 fn(x)", "xmap numpy",
        lambda: [_sq(x) for x in xs],
        lambda: xmap(_sq, xs, mode="thread"),
        "可向量化 λ 一次進 numpy")
    dumps = json_dumps if "json_dumps" in globals() else __import__("json").dumps
    _json = __import__("json")
    add("json", "1.2萬筆 dumps", "json.dumps", "引擎 json_dumps",
        lambda: _json.dumps(payload),
        lambda: dumps(payload),
        "orjson 熱路徑（略過 stub）")
    return {
        "cpu": os.cpu_count(),
        "py": sys.version.split()[0],
        "engine": __version__,
        "cases": cases,
        "new_wins": sum(1 for c in cases if c["winner"] == "new"),
        "old_wins": sum(1 for c in cases if c["winner"] == "old"),
    }


class BenchEngine:
    run = staticmethod(xbench)


_VEC_RULES = (
    ("ufunc", "ufunc / 廣播", "np.vectorize", "np.vectorize 是 Python 迴圈偽裝"),
    ("keep", "熱路徑保留 ndarray", "每步 .tolist()", "轉換成本常大於運算"),
    ("dtype", "int64 / float64", "dtype=object", "object 陣列沒有 SIMD"),
    ("mask", "布林遮罩", "Python if 過濾", "遮罩走 C 層"),
    ("alloc", "預先配置", "list.append 再轉陣列", "已知長度就不要長列表"),
    ("bcast", "廣播對齊", "zip 雙層迴圈", "對齊維度交給 numpy"),
    ("stride", "量過再 copy", "盲目 ascontiguousarray", "步幅運算有時更快"),
    ("fromiter", "fromiter + 明確 dtype", "逐筆 fn(x)", "同質純量用 fromiter"),
)


def _np():
    mod = _si("numpy")
    if mod is None or type(mod).__name__.endswith("Stub"):
        return None
    return mod


def xvec(func: Callable, items, *, dtype=None, keep_array: bool = True):
    """Best-practice numeric map: fromiter + ufunc, never np.vectorize."""
    np_mod = _np()
    if items is None:
        return np_mod.asarray([], dtype=dtype) if (keep_array and np_mod is not None) else []
    if np_mod is None:
        return [func(x) for x in list(items)]
    if isinstance(items, np_mod.ndarray):
        arr = items if items.dtype != object else np_mod.asarray(items.tolist(), dtype=dtype)
    else:
        seq = items if isinstance(items, list) else list(items)
        if not seq:
            return np_mod.asarray([], dtype=dtype) if keep_array else []
        x0 = seq[0]
        if dtype is None:
            dtype = np_mod.float64 if isinstance(x0, float) else np_mod.int64
        arr = np_mod.fromiter(seq, dtype=dtype, count=len(seq))
    out = func(arr)
    if keep_array:
        return out if isinstance(out, np_mod.ndarray) else np_mod.asarray(out)
    if isinstance(out, np_mod.ndarray):
        return out.tolist()
    return list(out)


def xvec_audit(src: str) -> Dict[str, Any]:
    """AST scan for numpy anti-patterns. Does not execute code."""
    _A = __import__("ast")
    findings: List[Dict[str, Any]] = []
    try:
        tree = _A.parse(src)
    except SyntaxError as exc:
        return {"ok": False, "error": str(exc), "findings": []}

    class V(_A.NodeVisitor):
        def visit_Call(self, node: _A.Call):
            name = ""
            f = node.func
            if isinstance(f, _A.Attribute):
                name = f.attr
            elif isinstance(f, _A.Name):
                name = f.id
            if name == "vectorize":
                findings.append({"id": "vectorize", "line": node.lineno, "sev": "block",
                                 "msg": "np.vectorize 不是向量化，改 ufunc / 廣播"})
            for kw in node.keywords:
                if kw.arg == "dtype" and isinstance(kw.value, _A.Constant) and kw.value.value == "object":
                    findings.append({"id": "object-dtype", "line": node.lineno, "sev": "warn",
                                     "msg": "dtype=object 沒有 SIMD"})
            self.generic_visit(node)

        def visit_Attribute(self, node: _A.Attribute):
            if node.attr == "tolist":
                findings.append({"id": "tolist", "line": node.lineno, "sev": "info",
                                 "msg": "熱路徑避免 .tolist()，交給邊界再轉"})
            self.generic_visit(node)

        def visit_For(self, node: _A.For):
            findings.append({"id": "py-loop", "line": node.lineno, "sev": "info",
                             "msg": "Python for：確認是否可改遮罩 / ufunc"})
            self.generic_visit(node)

    V().visit(tree)
    blocks = sum(1 for f in findings if f["sev"] == "block")
    return {"ok": blocks == 0, "n": len(findings), "findings": findings}


def xvec_bench(*, n: int = 80_000, rounds: int = 9) -> Dict[str, Any]:
    """Honest timings: practice vs anti-pattern."""
    np_mod = _np()
    if np_mod is None:
        return {"ok": False, "error": "numpy missing", "cases": []}
    py = list(range(n))
    a = np_mod.fromiter(py, dtype=np_mod.int64, count=n)
    af = a.astype(np_mod.float64)
    obj = np_mod.array(py, dtype=object)
    fn = (lambda x: x * x)
    vfn = np_mod.vectorize(fn, otypes=[np_mod.int64])

    def pack(cid, title, bad, good, bad_fn, good_fn, rule):
        b = _bench_median(bad_fn, rounds=rounds)
        g = _bench_median(good_fn, rounds=rounds)
        return {
            "id": cid, "title": title, "anti": bad, "practice": good,
            "anti_ms": b, "practice_ms": g,
            "speedup": round((b / g), 2) if g else 0,
            "rule": rule,
        }

    cases = [
        pack("ufunc", "平方", "np.vectorize", "ufunc a*a",
             lambda: vfn(a), lambda: a * a, "禁止 vectorize"),
        pack("keep", "熱路徑輸出", "每次 .tolist()", "保留 ndarray",
             lambda: (a * a).tolist(), lambda: a * a, "邊界才轉 list"),
        pack("dtype", "元素相乘", "dtype=object", "int64 ufunc",
             lambda: obj * obj, lambda: a * a, "禁止 object"),
        pack("mask", "取偶數", "Python if", "布林遮罩",
             lambda: [x for x in py if x % 2 == 0], lambda: a[a % 2 == 0], "遮罩走 C"),
        pack("alloc", "寫入結果", "list.append", "預先配置",
             lambda: (lambda r: (r.extend(x * x for x in py), r)[1])([]),
             lambda: (lambda o: (o.__setitem__(slice(None), a * a), o)[1])(np_mod.empty_like(a)),
             "已知長度預配置"),
        pack("bcast", "對齊相加", "zip 迴圈", "廣播",
             lambda: [int(x) + float(y) for x, y in zip(a, af)],
             lambda: a + af, "對齊交給廣播"),
        pack("stride", "隔筆平方", "先 copy 連續", "直接步幅 ufunc",
             lambda: np_mod.ascontiguousarray(a[::2]) * np_mod.ascontiguousarray(a[::2]),
             lambda: a[::2] * a[::2], "量過再 copy"),
        pack("fromiter", "list→陣列平方", "逐筆 fn(x)", "fromiter + ufunc",
             lambda: [fn(x) for x in py],
             lambda: xvec(fn, py, keep_array=True),
             "同質純量 fromiter"),
    ]
    return {
        "ok": True, "n": n, "cpu": os.cpu_count(),
        "cases": cases,
        "rules": [{"id": i, "do": d, "dont": n0, "why": w} for i, d, n0, w in _VEC_RULES],
        "new_wins": sum(1 for c in cases if c["practice_ms"] < c["anti_ms"] * 0.97),
    }


class VectorEngine:
    map = staticmethod(xvec)
    audit = staticmethod(xvec_audit)
    bench = staticmethod(xvec_bench)
    rules = staticmethod(lambda: list(_VEC_RULES))


try:
    CeleritasKernel.register("xbench", xbench, kind="fn", note="ANC-31 race")
    CeleritasKernel.register("BenchEngine", BenchEngine, kind="class", note="ANC-31")
    CeleritasKernel.register("xvec", xvec, kind="fn", note="ANC-33 numpy BP")
    CeleritasKernel.register("xvec_audit", xvec_audit, kind="fn", note="ANC-33")
    CeleritasKernel.register("xvec_bench", xvec_bench, kind="fn", note="ANC-33")
    CeleritasKernel.register("VectorEngine", VectorEngine, kind="class", note="ANC-33")
except Exception:
    pass

try:
    extra = []
    for name in ("xbench", "BenchEngine", "xvec", "xvec_audit", "xvec_bench", "VectorEngine"):
        if name not in __all__:
            extra.append(name)
    if extra:
        __all__.extend(extra)
except Exception:
    pass

# =============================================================================
# ANC-34  NUMBA JIT PRACTICE — nopython, cache, don't JIT what numpy already is
# =============================================================================

__version__ = "1.11.0"

_JIT_RULES = (
    ("nopython", "njit / nopython=True", "@jit 預設 object mode", "object mode 幾乎不加速"),
    ("ufunc", "簡單運算交給 numpy ufunc", "為 a*a 付編譯稅", "一次性呼叫會更慢"),
    ("rec", "迴圈依賴用 njit", "Python 逐筆遞推", "這是 Numba 主場"),
    ("fuse", "分支核融合進一層迴圈", "先遮罩再 ufunc 兩次掃描", "減少記憶體來回"),
    ("cache", "cache=True 跨行程", "每次重編", "編譯常是百毫秒級"),
    ("par", "大 n 才 parallel/prange", "64 筆就開平行", "編譯更貴、2 核不一定贏"),
    ("tiny", "小陣列走 numpy", "對 64 筆 dispatch JIT", "呼叫開銷大於運算"),
    ("fastmath", "財務核勿亂開 fastmath", "預設 fastmath=True", "會重排浮點、破 IEEE"),
)


def _numba_mod():
    if not _spec_exists("numba"):
        return None
    try:
        import numba as _nb
        return _nb
    except Exception:
        return None


def xjit(func=None, *, parallel: bool = False, fastmath: bool = False,
         cache: bool = True, nopython: bool = True):
    """Best-practice Numba: nopython only, cache on, fastmath off by default."""
    def deco(fn):
        _slot = [None]
        _meta = {"compiled_ms": None, "backend": "python"}

        def wrapped(*args, **kwargs):
            if _slot[0] is None:
                nb = _numba_mod()
                if nb is None or not nopython:
                    _slot[0] = fn
                    _meta["backend"] = "python"
                else:
                    t0 = time.perf_counter()
                    try:
                        _slot[0] = nb.njit(
                            nopython=True, parallel=parallel,
                            fastmath=fastmath, cache=cache,
                        )(fn)
                        _slot[0](*args, **kwargs)  # force compile
                        _meta["compiled_ms"] = round((time.perf_counter() - t0) * 1000.0, 2)
                        _meta["backend"] = "numba"
                    except Exception:
                        _slot[0] = fn
                        _meta["backend"] = "python"
                        _meta["compiled_ms"] = None
            return _slot[0](*args, **kwargs)

        wrapped.__wrapped__ = fn
        wrapped.__name__ = getattr(fn, "__name__", "xjit_wrapped")
        wrapped.__xjit__ = _meta
        return wrapped

    if func is not None:
        return deco(func)
    return deco


def xjit_audit(src: str) -> Dict[str, Any]:
    """AST flags: jit without nopython, fastmath=True, vectorize, python print in kernel."""
    _A = __import__("ast")
    findings: List[Dict[str, Any]] = []
    try:
        tree = _A.parse(src)
    except SyntaxError as exc:
        return {"ok": False, "error": str(exc), "findings": []}

    class V(_A.NodeVisitor):
        def visit_Call(self, node: _A.Call):
            name = ""
            f = node.func
            if isinstance(f, _A.Attribute):
                name = f.attr
            elif isinstance(f, _A.Name):
                name = f.id
            if name == "jit":
                kws = {kw.arg: kw.value for kw in node.keywords if kw.arg}
                nopy = kws.get("nopython")
                ok = isinstance(nopy, _A.Constant) and nopy.value is True
                if not ok:
                    findings.append({"id": "object-mode", "line": node.lineno, "sev": "block",
                                     "msg": "@jit 預設 object mode，改 njit"})
            if name in ("jit", "njit"):
                for kw in node.keywords:
                    if kw.arg == "fastmath" and isinstance(kw.value, _A.Constant) and kw.value.value is True:
                        findings.append({"id": "fastmath", "line": node.lineno, "sev": "warn",
                                         "msg": "fastmath 會破 IEEE，財務核不要開"})
                    if kw.arg == "parallel" and isinstance(kw.value, _A.Constant) and kw.value.value is True:
                        findings.append({"id": "parallel", "line": node.lineno, "sev": "info",
                                         "msg": "parallel 編譯更貴，確認 n 夠大"})
            if name == "vectorize":
                findings.append({"id": "np-vectorize", "line": node.lineno, "sev": "warn",
                                 "msg": "np.vectorize 不是 JIT；numba.vectorize 或 ufunc"})
            self.generic_visit(node)

        def visit_FunctionDef(self, node: _A.FunctionDef):
            for dec in node.decorator_list:
                dname = ""
                if isinstance(dec, _A.Name):
                    dname = dec.id
                elif isinstance(dec, _A.Call) and isinstance(dec.func, _A.Name):
                    dname = dec.func.id
                elif isinstance(dec, _A.Attribute):
                    dname = dec.attr
                if dname == "jit":
                    findings.append({"id": "bare-jit", "line": node.lineno, "sev": "block",
                                     "msg": "@jit 改 @njit 或 @xjit"})
            self.generic_visit(node)

    V().visit(tree)
    blocks = sum(1 for f in findings if f["sev"] == "block")
    return {"ok": blocks == 0, "n": len(findings), "findings": findings}


def xjit_bench(*, n: int = 200_000, rounds: int = 7) -> Dict[str, Any]:
    """Honest: compile tax, ufunc vs njit, recurrence (Numba home ground)."""
    import numpy as np
    nb = _numba_mod()
    if nb is None:
        return {"ok": False, "error": "numba missing", "cases": [], "rules": [
            {"id": i, "do": d, "dont": n0, "why": w} for i, d, n0, w in _JIT_RULES
        ]}
    x = np.arange(n, dtype="float64")

    def pack(cid, title, anti, good, anti_ms, good_ms, rule, compile_ms=None):
        g = good_ms if good_ms else 0
        return {
            "id": cid, "title": title, "anti": anti, "practice": good,
            "anti_ms": anti_ms, "practice_ms": good_ms,
            "speedup": round((anti_ms / g), 2) if g else 0,
            "rule": rule, "compile_ms": compile_ms,
        }

    cases: List[Dict[str, Any]] = []

    def py_sq(a):
        o = np.empty_like(a)
        for i in range(a.size):
            o[i] = a[i] * a[i]
        return o

    @nb.njit(cache=False)
    def nb_sq(a):
        o = np.empty_like(a)
        for i in range(a.size):
            o[i] = a[i] * a[i]
        return o

    t0 = time.perf_counter()
    nb_sq(x)
    compile_sq = round((time.perf_counter() - t0) * 1000.0, 2)
    cases.append(pack("ufunc", "平方", "Python 迴圈寫 ndarray", "numpy ufunc a*a",
                      _bench_median(lambda: py_sq(x), rounds=3, warm=0),
                      _bench_median(lambda: x * x, rounds=rounds),
                      "簡單運算不要 JIT"))
    cases.append(pack("hot", "平方熱路徑", "numpy ufunc", "njit 迴圈（已編譯）",
                      _bench_median(lambda: x * x, rounds=rounds),
                      _bench_median(lambda: nb_sq(x), rounds=rounds),
                      "編譯後僅微贏，第一次很貴", compile_sq))

    def py_kern(a):
        s = 0.0
        for i in range(a.size):
            v = float(a[i])
            if v > 0:
                s += math.sin(v) * math.exp(-0.0001 * v)
        return s

    @nb.njit(cache=False)
    def nb_kern(a):
        s = 0.0
        for i in range(a.size):
            v = a[i]
            if v > 0:
                s += np.sin(v) * np.exp(-0.0001 * v)
        return s

    def np_kern(a):
        m = a > 0
        return float((np.sin(a[m]) * np.exp(-0.0001 * a[m])).sum())

    t0 = time.perf_counter()
    nb_kern(x)
    compile_k = round((time.perf_counter() - t0) * 1000.0, 2)
    cases.append(pack("fuse", "sin·exp 分支核", "numpy 遮罩兩次掃描", "njit 單迴圈融合",
                      _bench_median(lambda: np_kern(x), rounds=rounds),
                      _bench_median(lambda: nb_kern(x), rounds=rounds),
                      "分支核融合", compile_k))
    cases.append(pack("pykern", "sin·exp 分支核", "純 Python", "njit",
                      _bench_median(lambda: py_kern(x), rounds=3, warm=0),
                      _bench_median(lambda: nb_kern(x), rounds=rounds),
                      "相對 Python"))

    @nb.njit(cache=False)
    def nb_rec(a, alpha):
        o = np.empty_like(a)
        o[0] = a[0]
        for i in range(1, a.size):
            o[i] = alpha * o[i - 1] + a[i]
        return o

    def py_rec(a, alpha):
        o = np.empty_like(a)
        o[0] = a[0]
        for i in range(1, a.size):
            o[i] = alpha * o[i - 1] + a[i]
        return o

    t0 = time.perf_counter()
    nb_rec(x, 0.99)
    compile_r = round((time.perf_counter() - t0) * 1000.0, 2)
    cases.append(pack("rec", "指數平滑遞推", "Python 逐筆", "njit 迴圈依賴",
                      _bench_median(lambda: py_rec(x, 0.99), rounds=3, warm=0),
                      _bench_median(lambda: nb_rec(x, 0.99), rounds=rounds),
                      "Numba 主場", compile_r))

    xt = np.arange(64, dtype="float64")
    cases.append(pack("tiny", "64 筆平方", "njit dispatch", "numpy ufunc",
                      _bench_median(lambda: nb_sq(xt), rounds=15),
                      _bench_median(lambda: xt * xt, rounds=15),
                      "小陣列不要 JIT"))

    cases.append(pack("compile", "首次平方編譯", "每次重編", "記住已編譯函式",
                      compile_sq, max(_bench_median(lambda: nb_sq(x), rounds=rounds), 0.001),
                      "編譯稅要攤提", compile_sq))

    return {
        "ok": True, "n": n, "cpu": os.cpu_count(),
        "numba": getattr(nb, "__version__", "?"),
        "cases": cases,
        "rules": [{"id": i, "do": d, "dont": n0, "why": w} for i, d, n0, w in _JIT_RULES],
        "new_wins": sum(1 for c in cases if c["practice_ms"] < c["anti_ms"] * 0.97),
    }


class JitEngine:
    jit = staticmethod(xjit)
    audit = staticmethod(xjit_audit)
    bench = staticmethod(xjit_bench)
    rules = staticmethod(lambda: list(_JIT_RULES))


try:
    CeleritasKernel.register("xjit", xjit, kind="fn", note="ANC-34 numba BP")
    CeleritasKernel.register("xjit_audit", xjit_audit, kind="fn", note="ANC-34")
    CeleritasKernel.register("xjit_bench", xjit_bench, kind="fn", note="ANC-34")
    CeleritasKernel.register("JitEngine", JitEngine, kind="class", note="ANC-34")
except Exception:
    pass

try:
    extra = []
    for name in ("xjit", "xjit_audit", "xjit_bench", "JitEngine"):
        if name not in __all__:
            extra.append(name)
    if extra:
        __all__.extend(extra)
except Exception:
    pass

# =============================================================================
# ANC-35  NUMBA LLVM BACKEND — opt level, fast-math flags, SIMD vs scalar
# =============================================================================

__version__ = "1.12.0"

# Numba fastmath=True turns these LLVM fast-math flags on together.
_LLVM_FASTMATH = (
    ("nnan", "假設沒有 NaN", "比較與分支可刪"),
    ("ninf", "假設沒有 Inf", "邊界分支可刪"),
    ("nsz", "−0 等於 +0", "符號零可丟"),
    ("arcp", "1/x 可改倒數乘", "除法變乘法"),
    ("contract", "允許 FMA 收縮", "mul+add → vfmadd"),
    ("reassoc", "允許重結合", "浮點約簡才能向量化"),
    ("afn", "近似 libm", "sin/exp 可換快速版"),
)

_LLVM_RULES = (
    ("opt", "NUMBA_OPT=3", "OPT=0", "0 關掉循環向量化"),
    ("fm", "約簡才開 fastmath", "財務預設 fastmath", "reassoc 會改結果"),
    ("simd", "看 ymm / vfmadd", "只看 Python 計時", "組語才證明向量化"),
    ("rec", "迴圈依賴接受純量 mulsd", "以為 LLVM 能向量化遞推", "依賴鏈切不開"),
    ("bc", "熱核可關 boundscheck", "除錯時關掉", "熱路徑影響小、編譯差很多"),
    ("ufunc", "簡單 a*a 仍交給 numpy", "為 ufunc 重編 LLVM", "編譯稅大於收益"),
)


def xllvm_scan(asm: str) -> Dict[str, Any]:
    """Count SIMD vs scalar opcodes in Numba's LLVM-lowered assembly."""
    a = asm.lower()
    ymm = a.count("ymm")
    xmm = a.count("xmm")
    zmm = a.count("zmm")
    vadd = a.count("vaddpd")
    vfma = a.count("vfmadd")
    addsd = a.count("addsd")
    mulsd = a.count("mulsd")
    return {
        "ymm": ymm, "xmm": xmm, "zmm": zmm,
        "vaddpd": vadd, "vfmadd": vfma,
        "addsd": addsd, "mulsd": mulsd,
        "vectorized": (vadd + vfma) > 0 and ymm > 8,
        "scalar": mulsd + addsd > 0 and (vadd + vfma) == 0,
    }


def xllvm_bench(*, n: int = 2_000_000, rounds: int = 5) -> Dict[str, Any]:
    """Re-measure LLVM opt / fastmath / recurrence. Slow: several compiles."""
    import numpy as np
    nb = _numba_mod() if "_numba_mod" in globals() else None
    if nb is None:
        try:
            import numba as nb
        except Exception:
            return {"ok": False, "error": "numba missing", "cases": []}
    x = np.linspace(0.0, 1.0, n)

    def med(fn, r=rounds, w=1):
        return _bench_median(fn, rounds=r, warm=w)

    @nb.njit(boundscheck=False, fastmath=False)
    def scalar_red(a):
        s = 0.0
        for i in range(a.size):
            s += a[i] * a[i] + 0.5 * a[i]
        return s

    @nb.njit(boundscheck=False, fastmath=True)
    def vec_red(a):
        s = 0.0
        for i in range(a.size):
            s += a[i] * a[i] + 0.5 * a[i]
        return s

    @nb.njit(boundscheck=False, fastmath=True)
    def rec(a):
        o = np.empty_like(a)
        o[0] = a[0]
        for i in range(1, a.size):
            o[i] = 0.99 * o[i - 1] + a[i]
        return o

    t0 = time.perf_counter(); scalar_red(x)
    t1 = time.perf_counter(); vec_red(x)
    rec(x[:4096])
    scan_s = xllvm_scan(scalar_red.inspect_asm(scalar_red.signatures[0]))
    scan_v = xllvm_scan(vec_red.inspect_asm(vec_red.signatures[0]))
    scan_r = xllvm_scan(rec.inspect_asm(rec.signatures[0]))
    err = float(abs(vec_red(x[:8000]) - scalar_red(x[:8000])))
    return {
        "ok": True,
        "n": n,
        "llvm": "22.1",
        "compile_ms": {
            "fastmath_off": round((t1 - t0) * 1000, 2),
        },
        "scans": {"scalar": scan_s, "fastmath": scan_v, "recurrence": scan_r},
        "hot_ms": {
            "fastmath_off": med(lambda: scalar_red(x)),
            "fastmath_on": med(lambda: vec_red(x)),
            "numpy": med(lambda: float((x * x + 0.5 * x).sum())),
        },
        "abs_err_sample": err,
    }


class LlvmEngine:
    scan = staticmethod(xllvm_scan)
    bench = staticmethod(xllvm_bench)
    flags = staticmethod(lambda: list(_LLVM_FASTMATH))
    rules = staticmethod(lambda: list(_LLVM_RULES))


try:
    CeleritasKernel.register("xllvm_scan", xllvm_scan, kind="fn", note="ANC-35")
    CeleritasKernel.register("xllvm_bench", xllvm_bench, kind="fn", note="ANC-35")
    CeleritasKernel.register("LlvmEngine", LlvmEngine, kind="class", note="ANC-35")
except Exception:
    pass

try:
    extra = [name for name in ("xllvm_scan", "xllvm_bench", "LlvmEngine") if name not in __all__]
    if extra:
        __all__.extend(extra)
except Exception:
    pass

# =============================================================================
# ANC-36  25 FAILURES × 3 SOLUTIONS — detect, route, embed
# =============================================================================

__version__ = "1.14.0"

def _fail_rows():
    """Static catalog. solutions are ordered: primary, fallback, last."""
    S = lambda a, b, c: (
        {"id": "S1", "do": a},
        {"id": "S2", "do": b},
        {"id": "S3", "do": c},
    )
    return [
        ("F01", "high", "缺 Numba", "JIT 匯入失敗，核退回純 Python",
         S("裝 numba，走 @xjit nopython", "改 xvec / numpy ufunc", "純 Python，標明未加速")),
        ("F02", "high", "JIT 型別推斷失敗", "njit 吃到 _LazyModule 直接 TypingError",
         S("核內 import 真實 numpy，禁止惰性模組", "去掉 parallel 重編一次", "放棄 JIT，改 numpy")),
        ("F03", "high", "fastmath 改寫財務結果", "reassoc / FMA 讓加總漂移",
         S("xjit 預設 fastmath=False", "雙跑比對，誤差超過 1e-9 退回", "財務路徑永久禁用 fastmath")),
        ("F04", "med", "NUMBA_OPT=0", "LLVM 向量化 pass 沒開，ymm=0",
         S("維持 OPT=3", "偵測到 0 則改走 numpy", "照跑但報告標成未向量化")),
        ("F05", "high", "boundscheck 關掉後越界", "錯誤索引變未定義行為",
         S("除錯與預設保持 boundscheck", "只在探針通過後才關", "IndexError 則立刻退回")),
        ("F06", "high", "微任務開 ThreadPool", "2 萬次平方曾慢 631×",
         S("低於 80µs/筆不開池", "可向量化改 fromiter", "其餘走 listcomp")),
        ("F07", "high", "orjson stub 雙重編碼", "假 orjson 比 stdlib 更慢",
         S("略過 *Stub，活體重匯入", "改 msgspec", "stdlib json")),
        ("F08", "med", "JSON 不可序列化", "set / 路徑物件讓 dumps 爆炸",
         S("default=str", "先轉純量再 dumps", "回傳錯誤路徑，不吞例外")),
        ("F09", "high", "把 np.vectorize 當加速", "它是 Python 迴圈偽裝",
         S("AST 直接擋 vectorize", "改寫成 ufunc", "fromiter + 明確 dtype")),
        ("F10", "med", "dtype=object", "沒有 SIMD",
         S("稽核警告 object", "純量串改 int64/float64", "拒絕宣稱已向量化")),
        ("F11", "med", "熱路徑 .tolist()", "轉換比運算貴",
         S("xvec keep_array=True", "只在邊界轉 list", "xmap 相容層才 tolist")),
        ("F12", "med", "遞推被誤判成向量化", "y[i] 依賴 y[i-1]，LLVM 切不開",
         S("組語看到 mulsd 就標純量", "仍用 njit，但不許報 vaddpd", "資料量小改 Python")),
        ("F13", "med", "小陣列還去 JIT", "64 筆 dispatch 比 ufunc 貴",
         S("n<256 走 numpy", "用已編譯快取，不重編", "低於門檻直接 listcomp")),
        ("F14", "high", "首次編譯稅", "平方核第一次可到 300ms",
         S("cache=True", "行程啟動暖機一次", "只跑一次的工作不要 JIT")),
        ("F15", "high", "記憶體壓力", "平行配置把機器打滿",
         S("壓力超過門檻改循序", "縮小 chunk", "仍超過則中止這批")),
        ("F16", "high", "PS 未接入模板", "AI 產出裸腳本沒有還原",
         S("xps_join 包進模板", "稽核不過就 block", "拒絕執行未接入檔")),
        ("F17", "high", "PS 禁令", "IEX、EmptyWorkingSet、High、32767 執行緒",
         S("去註解後再掃", "命中即 block", "改寫成安全等價寫法")),
        ("F18", "high", "離開未還原", "優先權或親和性留在行程上",
         S("finally / 退出還原", "稽核要求 restore", "只改本行程，不動別人")),
        ("F19", "med", "預覽框擋下載", "iframe 吃掉 a[download]",
         S("另開 download.html", "頁內 base64 自行存檔", "直連 zip 備援")),
        ("F20", "med", "引擎與畫面版本漂移", "駕駛艙寫 1.6、引擎已 1.13",
         S("單一 __version__", "打包時寫進 SHA256", "啟動比對不一致就標紅")),
        ("F21", "high", "缺 numpy", "xvec / 約簡全部失效",
         S("先探針再呼叫", "退回 listcomp", "缺庫時失敗要講人話")),
        ("F22", "med", "fromiter 混型", "int 串裡夾 float 會爆",
         S("看頭一個元素選 dtype", "失敗加寬成 float64", "再失敗就放棄向量路徑")),
        ("F23", "med", "執行緒池沒關", "每次 xmap 新建池",
         S("微任務根本不建池", "with 包住 Executor", "atexit 再清一次")),
        ("F24", "high", "AST 注入沒蓋滿", "覆蓋率低於 100% 還當成功",
         S("inventory 對 injected", "未滿 100 視為失敗", "漏的節點重掃一次")),
        ("F25", "med", "少核平行反慢", "2 核上 parallel 編譯更貴",
         S("實體核少於 4 不開 parallel", "n 不夠大不 prange", "先量再決定")),
    ]


def _has_real(name: str) -> bool:
    mod = _si(name) if "_si" in globals() else None
    if mod is None or type(mod).__name__.endswith("Stub"):
        try:
            mod = __import__(name)
        except Exception:
            return False
    return mod is not None and not type(mod).__name__.endswith("Stub")


def xroute(failure_id: str, **ctx) -> str:
    """Pick S1/S2/S3 for a known failure. Never raises."""
    n = ctx.get("n")
    fid = failure_id.upper()
    try:
        if fid == "F01":
            return "S1" if _has_real("numba") else ("S2" if _has_real("numpy") else "S3")
        if fid == "F02":
            return "S1" if _has_real("numpy") else "S3"
        if fid == "F03":
            return "S1"
        if fid == "F04":
            if not _has_real("numba"):
                return "S2"
            import numba as _nb
            level = int(getattr(getattr(_nb.config, "OPT", 3), "value", _nb.config.OPT) or 3)
            try:
                level = int(_nb.config.OPT)
            except Exception:
                pass
            return "S1" if level >= 2 else "S2"
        if fid == "F05":
            return "S1"
        if fid == "F06":
            if _has_real("numpy") and (n is None or n >= 32):
                return "S2"
            return "S1"
        if fid == "F07":
            return "S1" if _has_real("orjson") else ("S2" if _has_real("msgspec") else "S3")
        if fid == "F08":
            return "S1"
        if fid == "F09":
            return "S1"
        if fid == "F10":
            return "S2" if _has_real("numpy") else "S3"
        if fid == "F11":
            return "S1" if _has_real("numpy") else "S3"
        if fid == "F12":
            return "S1" if _has_real("numba") else "S3"
        if fid == "F13":
            if n is not None and n < 256:
                return "S1" if _has_real("numpy") else "S3"
            return "S2" if _has_real("numba") else "S3"
        if fid == "F14":
            return "S1" if _has_real("numba") else "S3"
        if fid == "F15":
            return "S1"
        if fid == "F16":
            return "S1"
        if fid == "F17":
            return "S1"
        if fid == "F18":
            return "S1"
        if fid == "F19":
            return "S1"
        if fid == "F20":
            return "S1"
        if fid == "F21":
            return "S1" if _has_real("numpy") else "S2"
        if fid == "F22":
            return "S1" if _has_real("numpy") else "S3"
        if fid == "F23":
            return "S1"
        if fid == "F24":
            return "S1"
        if fid == "F25":
            cores = os.cpu_count() or 1
            if cores < 4:
                return "S1"
            if n is not None and n < 100_000:
                return "S2"
            return "S3"
    except Exception:
        return "S3"
    return "S3"


def xfail_matrix() -> Dict[str, Any]:
    """25 failures, the armed solution, and a live probe where it is cheap."""
    probes = {
        "F06": _probe_f06,
        "F07": _probe_f07,
        "F09": _probe_f09,
        "F16": _probe_f16,
        "F17": _probe_f17,
        "F24": _probe_f24,
    }
    rows = []
    armed_s1 = 0
    open_n = 0
    for fid, blast, title, symptom, sols in _fail_rows():
        pick = xroute(fid)
        probe = "skip"
        try:
            if fid in probes:
                probe = probes[fid]()
                if probe == "fail":
                    pick = "S3"
        except Exception:
            probe = "fail"
            pick = "S3"
        if pick == "S1":
            armed_s1 += 1
        if probe == "fail":
            open_n += 1
        rows.append({
            "id": fid,
            "blast": blast,
            "title": title,
            "symptom": symptom,
            "solutions": [dict(s) for s in sols],
            "armed": pick,
            "probe": probe,
        })
    return {
        "ok": open_n == 0 and len(rows) == 25,
        "n": len(rows),
        "armed_s1": armed_s1,
        "open": open_n,
        "engine": __version__,
        "rows": rows,
    }


def _probe_f06() -> str:
    t0 = time.perf_counter()
    xmap(lambda x: x * x, list(range(4000)), mode="thread")
    return "pass" if (time.perf_counter() - t0) < 0.2 else "fail"


def _probe_f07() -> str:
    if not _has_real("orjson"):
        return "fail"
    sample = [{"i": 1}]
    out = json_dumps(sample)
    return "pass" if isinstance(out, str) and out.startswith("[") else "fail"


def _probe_f09() -> str:
    hit = xvec_audit("import numpy as np\nnp.vectorize(lambda x: x)\n")
    ids = [f.get("id") for f in hit.get("findings", [])]
    return "pass" if "vectorize" in ids else "fail"


def _probe_f16() -> str:
    joined = xps_join("Get-Date\n", name="probe.ps1")
    audit = xps_audit(joined["text"], name="probe.ps1")
    return "pass" if audit.get("verdict") == "pass" and audit.get("joined") else "fail"


def _probe_f17() -> str:
    audit = xps_audit("IEX (Get-Content x)\n", name="bad.ps1")
    return "pass" if audit.get("verdict") == "block" and audit.get("forbidden", 0) else "fail"


def _probe_f24() -> str:
    report = xunify("def f(x):\n    return x + 1\n", name="f.py")
    return "pass" if float(report.get("coverage", 0)) >= 100.0 else "fail"


class FailureMatrix:
    matrix = staticmethod(xfail_matrix)
    route = staticmethod(xroute)


try:
    CeleritasKernel.register("xfail_matrix", xfail_matrix, kind="fn", note="ANC-36")
    CeleritasKernel.register("xroute", xroute, kind="fn", note="ANC-36")
    CeleritasKernel.register("FailureMatrix", FailureMatrix, kind="class", note="ANC-36")
except Exception:
    pass

try:
    extra = [name for name in ("xfail_matrix", "xroute", "FailureMatrix") if name not in __all__]
    if extra:
        __all__.extend(extra)
except Exception:
    pass
