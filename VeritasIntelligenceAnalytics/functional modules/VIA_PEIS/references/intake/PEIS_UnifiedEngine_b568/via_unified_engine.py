#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA Unified Engine (VUE) — 單一引擎，可掛入系統也可獨立運作。

一個行程走完整條治理鏈：

    INTAKE 尋找輸入 → SCAN AST 正規化 → CLUSTER 聚眾（同功能分群）
    → TEST 影子對照 → LOCK 測試成功才封印 → EVIDENCE 沙箱證據
    → POOL 引擎版本池 → HYDRA 全景衝突分析 → MAP CME v2.0 能力表
    → ANNOTATE 能力卡 → STORE 資料庫最佳化

整合目標是**節省 AI token**：封印後的能力以「能力卡」標註，AI 只讀卡就能呼叫能力，
不必讀全文原始碼；對上游一律只暴露 `RUN(capability, params)`，引擎名稱、版本與策略
永不出現在回傳值裡（黑盒原則，由 `def_assert_blackbox` 把關）。
第二個目標是**資料庫最佳化**：能力庫用內容定址與 stat 增量，省掉重複下載、
重複讀取與重複建構。卡片與 capsule 遵守 Root SSOT
`config/ssot/VIA_SystemMaster.via#/token_governance/capsule_policy` 的
`REFERENCE_FIRST_DELTA_ONLY` 契約；找不到 SSOT 時用本檔內建上限，因此同一支引擎
在系統內（plugin）與離線單機（independent）行為一致。

治理邊界：
  * 純標準庫、不連網、不安裝、不改動來源檔（掃描一律唯讀）。
  * CME 能力表預設 **AUDIT 不寫**，`--apply` 才寫，且 append-only 永不盲目覆寫。
  * Zero-Hydra：版本池碰撞／策略改寫／函式所有權漂移／相依環一律 fail-closed
    轉成 SEQUENTIAL_FIX 修復計畫，不動能力表。
  * 未封印的能力禁止 RUN；capsule 永不夾帶原始碼全文。
  * 只產生 candidate 證據；Root SSOT 仍只由 CGC-PROMOTE-WORKER-001 寫入。
  * 測試沙箱：無 import、無 while、受限 builtins、行數預算、常數上限。
  * 全流程決定性：AST 型別 id 與嵌入向量都取自名稱雜湊（blake2b／FNV），
    跨行程、跨平台一致，不用 `hash()` 也不量時間。

前身（全部整合進本檔，不再需要各自獨立存在）：
  VIA CANON CPU（AST α-rename 指紋、能力命名、封印帳）、
  VIA Engine Standardizer（工具家族、風險稽核）、
  VIA Engine Unifier（同義詞聚眾、variant 保留）、
  VIA PEIS 引擎（EngineLocker、CapabilityExtractor、CME v2.0 能力表、
  Zero-Hydra 全景分析、FastAccessLayer 黑盒 RUN、八階段全景擴充管線）、
  engine/governance_engine.py 的唯讀 AST 盤點。

與 CANON CPU 原型相比的修正：type id 改為與行程無關的穩定雜湊，
指紋因此不再受掃描順序影響，封印帳與資料庫才能跨執行沿用。

用法（獨立）：
    python engine/via_unified_engine.py selftest
    python engine/via_unified_engine.py ingest  --src <dir> --db <file>
    python engine/via_unified_engine.py govern  --src <dir> --db <file> --root <repo> [--apply]
    python engine/via_unified_engine.py expand  --root <repo> [--apply]
    python engine/via_unified_engine.py lock    --root <repo> --engine-path <py> \
        --engine-id <id> --engine-version <v> --evidence <json> [--apply]
    python engine/via_unified_engine.py capsule --db <file> --audience upstream --budget-tokens 3000
    python engine/via_unified_engine.py run     --db <file> --capability compute.mean --args "[[1,2,3]]"
    python engine/via_unified_engine.py run     --root <repo> --capability math --params "{\"values\":[1,2]}"
    python engine/via_unified_engine.py query   --db <file> --columns cap,eng,sig
    python engine/via_unified_engine.py manifest --root .
    python engine/via_unified_engine.py report  --db <file> --root .
兩支前身的旗標式呼叫仍可用：`--selftest`、`--scan <path>`、`--mode expand|lock|run|report`。

用法（掛入系統，Python）：
    from engine.via_unified_engine import def_govern, def_plugin_invoke
    report = def_govern([Path("engine")], database=Path("vue.db"), root=Path("."))
    answer = def_plugin_invoke({"p": "VIA-ENGINE-1.0", "c": "compute.mean",
                                "a": "RUN", "r": "RESULT_ONLY"},
                               arguments=[[1, 2, 3]], database=Path("vue.db"))
"""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import importlib.util
import json
import math
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
import time
import zipfile
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from html import escape
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence


PARAM_ENGINE_ID = "VIA-VIA-ENG996"
PARAM_ENGINE_NAME = "VIA Unified Engine"
PARAM_ENGINE_VERSION = "v0200"
# v0100 的能力表與治理參數仍讀得進來（只增不減）；寫出時一律正規化成 v0200。
PARAM_ENGINE_VERSION_COMPAT = ("v0100",)
PARAM_PROTOCOL = "VIA-ENGINE-1.0"
PARAM_ENGINE_RELATIVE = "engine/via_unified_engine.py"
PARAM_CME_VERSION = "2.0"
PARAM_CAPABILITY_MAP_RELATIVE = Path("config/ssot/VIA_PEISCapabilityMap.via")
PARAM_GOVERNANCE_RELATIVE = Path("config/ssot/central_governance_parameters.json")
PARAM_PARAMETER_BLOCK = "unified_engine"
PARAM_PARAMETER_BLOCK_ALIAS = "peis_engine"
PARAM_SANDBOX_GATE = "VUE-SANDBOX-PROBE"
PARAM_STRATEGIES = ("best-performance", "most-stable", "latest-version")
PARAM_MODULE_GATE = "VUE-MODULE-ISOLATED"
PARAM_MODULE_TIMEOUT_SECONDS = 20
PARAM_MODULE_OUTPUT_LIMIT = 1 << 20
PARAM_MODULE_JOB_LIMIT = 400
PARAM_DEFAULT_HANDOFF = "default"
# capsule 的 header 是固定成本；語料小於 header 的這個倍數時，token 帳本來就會倒賠，
# 那不是失敗，是語料還沒大到值得做 capsule。verify 在這種情況報 SKIPPED 並給出損益兩平點。
PARAM_TOKEN_GATE_MULTIPLIER = 4
PARAM_TOKEN_GATE_FLOOR_PERCENT = 50.0
PARAM_EXPORT_BUNDLE = "via-unified-engine-independent"
PARAM_EXPORT_README = """# VIA Unified Engine — 獨立成品

這份是 `{engine_id}` {version} 的自帶成品：**一支 .py、純標準庫、不連網、不安裝**，
不需要 VIA 庫也能運作。

```bash
python via_unified_engine.py selftest                      # {selftest} 項不變式
python via_unified_engine.py version --json                # 引擎身份卡
python via_unified_engine.py ingest  --src <dir> --db vue.db --root <dir>
python via_unified_engine.py govern  --src <dir> --db vue.db --root . # 需要能力表時
python via_unified_engine.py capsule --db vue.db --handoff ai-1       # 只送變更
python via_unified_engine.py run     --db vue.db --capability <cap> --args "[[1,2,3]]"
python via_unified_engine.py verify  --root .              # 一鍵閘門
```

## 沒有 SSOT 時會怎樣

capsule 上限改用引擎內建值（`policy.source = engine-default`）；
`govern` 需要 CME 能力表時，`{map_name}` 就放在這份成品裡，
指定 `--root` 到它的上層目錄即可。

## 邊界（跟在庫內完全一樣）

* 來源檔永不改動，每份報告都帶 `source_mutation: false`。
* 能力表預設 AUDIT 不寫，`--apply` 才寫，且 append-only。
* 只有 `SEALED` 能力可以 RUN；對上游一律黑盒（不回引擎 id、路徑或策略）。
* 模組級隔離補測會真的 import 來源模組，預設關閉（`--allow-module-exec`）。
* `benchmark_score` 只能來自外部證據（`--evidence`），引擎自己的通道恆為 0.0。

本成品由 `python engine/via_unified_engine.py export` 產生；
`MANIFEST.json` 記著每個檔案的 sha256 與產生時的自測結果。
"""
PARAM_DEFAULT_STRATEGY = "best-performance"
PARAM_STABILITY_RUNS = 3
PARAM_AUDIENCES = ("upstream", "governance")
PARAM_UNIFIED_STAGES = (
    "INTAKE", "SCAN", "CLUSTER", "TEST", "LOCK", "EVIDENCE", "POOL", "HYDRA",
    "MAP", "ANNOTATE", "STORE",
)
PARAM_MAP_SCHEMA = "VIA.PEISCapabilityMap"
PARAM_MAP_SCHEMA_VERSION = "2.1.0"
PARAM_MAP_SCHEMA_VERSION_COMPAT = ("2.0.0",)
PARAM_AUTHORITY = "VIA-SYS-MGR-001"

PARAM_ENGINE_SCAN_PREFIXES = ("engine/", "functional modules/", "public/via/")
PARAM_SCAN_EXCLUDED_NAMES = ("__init__.py",)
PARAM_EMBEDDING_DIMENSIONS = 64
PARAM_EMBEDDING_PRECISION = 12
PARAM_SIMILARITY_PRECISION = 4
PARAM_MAX_SOURCE_BYTES = 8 * 1024 * 1024
PARAM_STANDARD_LOCK_KEYS = ("engine_id", "locked", "version", "capability", "performance")
PARAM_CAPSULE_SCHEMA = "VIA.CapabilityCapsule"
PARAM_PLUGIN_SCHEMA = "VIA.EnginePlugin"
PARAM_REPORT_SCHEMA = "VIA.UnifiedEngineReport"
PARAM_STORE_SCHEMA_VERSION = "1"
PARAM_TOKEN_ESTIMATOR = "vue-alnum4-v1"

PARAM_ROOT_SSOT_RELATIVE = Path("config/ssot/VIA_SystemMaster.via")
PARAM_ROOT_MARKERS = ("VIA_CentralGovernance.py", "config/ssot/VIA_SystemMaster.via")
PARAM_CAPSULE_PROTOCOL = "REFERENCE_FIRST_DELTA_ONLY"
PARAM_CAPSULE_MAX_CHARS = 12000
PARAM_CAPSULE_MAX_ITEMS = 24

PARAM_NEAR_DUPLICATE_THRESHOLD = 0.82
PARAM_DOC_LIMIT = 140
PARAM_RESULT_LIMIT = 240
PARAM_EXECUTION_LINE_BUDGET = 20000
PARAM_EXECUTION_MAX_NODES = 600
PARAM_EXECUTION_MAX_CONSTANT = 10**6
PARAM_EXECUTION_MAX_ARITY = 4

PARAM_SKIP_DIRECTORIES = frozenset({
    ".git", ".hg", ".svn", "__pycache__", ".mypy_cache", ".pytest_cache", ".tox",
    ".venv", "venv", "env", "envs", "site-packages", "node_modules", "dist",
    "build", ".vercel", ".idea", ".vscode", "_to_delete",
})

PARAM_PY_BUILTINS = frozenset({
    "abs", "all", "any", "bin", "bool", "bytearray", "bytes", "callable", "chr",
    "complex", "dict", "dir", "divmod", "enumerate", "filter", "float", "format",
    "frozenset", "getattr", "hasattr", "hash", "help", "hex", "id", "input", "int",
    "isinstance", "issubclass", "iter", "len", "list", "map", "max", "min", "next",
    "oct", "open", "ord", "pow", "print", "range", "repr", "reversed", "round",
    "set", "setattr", "slice", "sorted", "str", "sum", "super", "tuple", "type",
    "vars", "zip",
})

# 能力命名同義詞：CANON CPU 的動詞／物件表併入 Unifier 與 Standardizer 的擴充。
# 衝突裁決：average 歸 mean（沿用 CANON CPU），ma 只收 ma/sma/moving/movingaverage。
PARAM_VERBS: dict[str, tuple[str, ...]] = {
    "compute": ("calc", "calculate", "compute", "comp", "eval", "evaluate",
                "estimate", "measure", "aggregate", "agg", "summarize"),
    "load": ("load", "fetch", "get", "read", "download", "pull", "grab", "query",
             "retrieve", "crawl", "collect", "import"),
    "save": ("save", "write", "dump", "export", "store", "persist", "put",
             "upsert", "emit", "flush"),
    "parse": ("parse", "extract", "scrape", "decode", "tokenize", "unpack",
              "deserialize"),
    "clean": ("clean", "normalize", "normalise", "sanitize", "sanitise", "tidy",
              "fix", "strip", "dedupe", "dedup"),
    "validate": ("validate", "check", "verify", "assert", "audit", "ensure",
                 "gate", "lint", "selftest", "test"),
    "convert": ("convert", "transform", "cast", "encode", "reshape", "serialize"),
    "score": ("score", "rank", "rate", "grade"),
    "detect": ("detect", "scan", "find", "search", "match", "signal", "screen",
               "locate", "lookup", "classify", "cluster"),
    "filter": ("filter", "select", "pick", "drop", "exclude", "unique",
               "distinct", "group"),
    "merge": ("merge", "join", "combine", "concat", "union", "unify",
              "consolidate", "integrate", "sync", "register"),
    "build": ("build", "create", "make", "generate", "gen", "init", "new"),
    "render": ("render", "draw", "plot", "chart", "report", "show", "display",
               "dashboard"),
    "compress": ("compress", "pack", "zip", "zstd"),
    "encrypt": ("encrypt", "hash", "digest", "aes"),
    "run": ("run", "main", "execute", "exec", "start", "launch", "invoke",
            "process", "apply"),
    "log": ("log", "print", "trace", "notify"),
}
PARAM_OBJECTS: dict[str, tuple[str, ...]] = {
    "mean": ("mean", "avg", "average"),
    "rsi": ("rsi",),
    "sharpe": ("sharpe",),
    "beta": ("beta",),
    "price": ("px", "price", "prices", "close", "closes"),
    "volume": ("vol", "volume", "volumes", "qty"),
    "ma": ("ma", "sma", "moving", "movingaverage"),
    "signal": ("signal", "momentum"),
    "vector": ("vector", "flow"),
    "frame": ("df", "frame", "dataframe", "table"),
    "html": ("html",),
    "json": ("json", "js"),
    "path": ("path", "paths", "file", "files", "fp"),
}
PARAM_STOPWORDS = frozenset({
    "a", "an", "the", "of", "and", "or", "to", "for", "in", "on", "by", "with",
    "from", "into", "data", "all", "my", "v", "new", "old", "tmp", "temp",
    "helper", "util", "utils", "func", "fn", "impl", "internal",
    # VIA 全庫慣例前綴：def_xxx 的 def 不帶語意，留著只會污染能力 id 並多花 token。
    "def",
})

PARAM_TOOL_FAMILIES: dict[str, tuple[str, ...]] = {
    "pandas": ("pandas", "pd"),
    "polars": ("polars", "pl"),
    "duckdb": ("duckdb",),
    "pyarrow": ("pyarrow", "pa"),
    "numpy": ("numpy", "np"),
    "sqlite": ("sqlite3",),
    "sqlalchemy": ("sqlalchemy",),
    "requests": ("requests",),
    "httpx": ("httpx",),
    "urllib": ("urllib", "urllib2"),
    "aiohttp": ("aiohttp",),
    "yfinance": ("yfinance", "yf"),
    "bs4": ("bs4", "BeautifulSoup"),
    "lxml": ("lxml",),
    "selenium": ("selenium",),
    "playwright": ("playwright",),
    "openpyxl": ("openpyxl",),
    "xlsxwriter": ("xlsxwriter",),
    "pymupdf": ("fitz", "pymupdf"),
    "pdfplumber": ("pdfplumber",),
    "pypdf": ("pypdf", "PyPDF2"),
    "tesseract": ("pytesseract",),
    "talib": ("talib",),
    "matplotlib": ("matplotlib", "plt"),
    "plotly": ("plotly",),
    "subprocess": ("subprocess",),
    "socket": ("socket", "ssl", "http", "ftplib", "smtplib", "telnetlib"),
    "filesystem": ("os", "shutil", "pathlib", "tempfile", "glob"),
    "serialize": ("json", "csv", "pickle", "marshal", "shelve"),
    "concurrency": ("threading", "multiprocessing", "concurrent", "asyncio"),
    "logging": ("logging", "loguru"),
    "regex": ("re", "regex"),
    "datetime": ("datetime", "dateutil", "time"),
    "numba": ("numba",),
    "joblib": ("joblib",),
}
PARAM_NETWORK_FAMILIES = frozenset({
    "requests", "httpx", "urllib", "aiohttp", "yfinance", "bs4", "lxml",
    "selenium", "playwright", "socket",
})
PARAM_ALIAS_TO_FAMILY: dict[str, str] = {
    alias: family for family, aliases in PARAM_TOOL_FAMILIES.items() for alias in aliases
}

PARAM_RISK_TABLE: dict[str, tuple[str, str]] = {
    "R01": ("LOW", "無回傳型別註記"),
    "R02": ("LOW", "參數未註記型別"),
    "R03": ("MED", "裸 except 或吞例外"),
    "R04": ("HIGH", "可變預設引數"),
    "R05": ("LOW", "無 docstring"),
    "R06": ("HIGH", "使用網路工具"),
    "R07": ("HIGH", "寫入檔案系統"),
    "R08": ("HIGH", "呼叫子程序"),
    "R09": ("HIGH", "動態執行（eval/exec/compile）"),
    "R10": ("MED", "改寫模組層狀態"),
    "R11": ("MED", "參數面過寬（>5 或 *args/**kwargs）"),
    "R12": ("MED", "巢狀過深（>4）"),
    "R13": ("MED", "函式過長（>60 敘述）"),
    "R14": ("MED", "while 迴圈（無界風險）"),
    "R15": ("MED", "浮點等值比較"),
    "R16": ("LOW", "print 旁通道"),
    # v0200 新增，全部由同一次 AST 走訪判定，不做字串猜測
    "R17": ("MED", "用 assert 當驗證（-O 會被移除）"),
    "R18": ("LOW", "參數遮蔽 builtin 名稱"),
    "R19": ("MED", "自我遞迴且無深度保護"),
    "R20": ("MED", "非決定性時間來源"),
    "R21": ("HIGH", "硬編絕對路徑字面值"),
    "R22": ("HIGH", "疑似機密字面值"),
    "R23": ("HIGH", "網址字面值"),
    "R24": ("MED", "非決定性隨機來源"),
}
PARAM_SECRET_NAME_RE = re.compile(
    r"(?i)(secret|password|passwd|api[_-]?key|apikey|access[_-]?key|private[_-]?key|credential)"
)
PARAM_ABSOLUTE_PATH_RE = re.compile(r"^(?:[A-Za-z]:[\\/]|/(?:home|usr|var|etc|root|opt)/)")
PARAM_NONDETERMINISTIC_TIME = frozenset({
    "time", "monotonic", "perf_counter", "now", "utcnow", "today", "time_ns",
})
PARAM_NONDETERMINISTIC_RANDOM = frozenset({
    "random", "randint", "randrange", "uniform", "shuffle", "choice", "sample",
    "urandom", "uuid1", "uuid4", "getrandbits",
})

PARAM_FORBIDDEN_EXEC_NAMES = frozenset({
    "open", "exec", "eval", "compile", "__import__", "input", "globals",
    "locals", "vars", "getattr", "setattr", "delattr", "breakpoint", "help",
    "memoryview", "exit", "quit", "super", "staticmethod", "classmethod",
    "property", "print", "id", "dir",
})
PARAM_FORBIDDEN_EXEC_ATTRIBUTES = frozenset({
    "write", "writelines", "system", "popen", "communicate", "connect", "send",
    "sendall", "recv", "urlopen", "request", "unlink", "rmdir", "remove",
    "rename", "mkdir", "chmod", "kill", "terminate", "spawn", "fork",
    "read_text", "write_text", "read_bytes", "write_bytes",
})
PARAM_SAFE_BUILTIN_NAMES = (
    "abs", "all", "any", "bin", "bool", "bytes", "callable", "chr", "complex",
    "dict", "divmod", "enumerate", "filter", "float", "format", "frozenset",
    "hash", "hex", "int", "isinstance", "issubclass", "iter", "len", "list",
    "map", "max", "min", "next", "oct", "ord", "pow", "range", "repr",
    "reversed", "round", "set", "slice", "sorted", "str", "sum", "tuple",
    "type", "zip", "ArithmeticError", "AssertionError", "AttributeError",
    "Exception", "IndexError", "KeyError", "OverflowError", "RuntimeError",
    "StopIteration", "TypeError", "ValueError", "ZeroDivisionError", "True",
    "False", "None",
)
PARAM_PROBE_VECTORS: tuple[tuple[str, tuple[Any, ...]], ...] = (
    ("sequence", ([1.0, 2.0, 3.0, 4.0],)),
    ("number", (2.0,)),
    ("text", ("via",)),
    # 真實程式碼常見的輸入：合法 JSON 文字。少了它，凡是 json.loads 開頭的函式
    # 都拿不到可用探針（"via" 不是合法 JSON）。
    ("json_text", ('[1, 2, 3]',)),
    ("mapping", ({"a": 1, "b": 2},)),
    ("pair", (2.0, 3.0)),
    ("sequence_number", ([1.0, 2.0, 3.0, 4.0], 2)),
    ("text_text", ("via", "vue")),
    ("sequence_sequence", ([1.0, 2.0, 3.0], [4.0, 5.0, 6.0])),
    ("empty", ()),
)
PARAM_FLOAT_TOLERANCE = 1e-9

# 說明本身也要省 token：每個鍵只給最短可辨識的中文。空欄位一律省略。
PARAM_CARD_LEGEND: dict[str, str] = {
    "cap": "能力id",
    "eng": "引擎id",
    "st": "封印狀態",
    "fp": "AST指紋",
    "sig": "簽章",
    "at": "原始碼位置",
    "ret": "回傳型別",
    "doc": "首行說明",
    "tools": "工具家族",
    "risk": "風險碼",
    "alt": "實作數",
    "dup": "折疊份數",
    "test": "探針 in→out",
    "tok": "body/card token",
}
PARAM_CAPSULE_LOAD_ORDER = (
    "先讀卡：簽章與探針足以呼叫能力",
    "卡不足才讀 at 指向的那一段原始碼",
    "呼叫走 envelope，回 RESULT_ONLY",
)

PARAM_PANORAMIC_STAGES = (
    "EngineScanner",
    "SemanticExtractor",
    "EmbeddingGenerator",
    "SimilarityMatrixBuilder",
    "PanoramicClusterer",
    "CapabilityAbstractor",
    "CapabilityMapUpdater",
    "PanoramicAbstractExpander",
)

PARAM_NOISE_TOKENS = frozenset((
    "def", "via", "vdf", "vrn", "vap", "peis", "param", "self", "cls",
    "impl", "internal", "py",
))
PARAM_WEAK_TOKENS = frozenset((
    "helper", "util", "utils", "main", "run", "value", "item", "obj", "tmp",
))
PARAM_UNCLASSIFIED = "unclassified"
PARAM_CANDIDATE_CLUSTER_MIN = 3
PARAM_VERB_TOKENS = frozenset((
    "predict", "forecast", "calc", "calculate", "compute", "eval", "evaluate",
    "gen", "generate", "build", "make", "create", "load", "read", "write",
    "save", "fetch", "download", "parse", "render", "emit", "export",
    "publish", "scan", "discover", "probe", "check", "verify", "validate",
    "audit", "extract", "update", "sync", "lock", "route", "select", "resolve",
    "normalize", "summarize", "estimate", "infer", "install", "promote",
    "approve", "optimize", "accelerate", "ingest", "locate", "search",
))
PARAM_CAPABILITY_DICTIONARY: dict[str, tuple[str, ...]] = {
    "math": (
        "math", "calc", "calculate", "calculation", "compute", "computation",
        "arithmetic", "eval", "evaluate", "sum", "mean", "ratio", "vector",
        "numeric", "scalar",
    ),
    "signal": (
        "signal", "momentum", "trend", "indicator", "oscillator", "crossover",
        "factor", "alpha",
    ),
    "predict": (
        "predict", "forecast", "projection", "project", "estimate", "infer",
        "inference", "consensus", "valuation",
    ),
    "govern": (
        "govern", "governance", "audit", "gate", "policy", "compliance",
        "verify", "validate", "guard", "lock", "approve", "promote", "lease",
    ),
    "accelerate": (
        "accelerate", "accelerator", "parallel", "concurrency", "throughput",
        "speedup", "optimize", "cache", "worker", "lane",
    ),
    "data": (
        "data", "load", "read", "ingest", "parse", "fetch", "download",
        "normalize", "dataset", "price", "prices", "csv", "json", "registry",
        "schema", "row",
    ),
    "report": (
        "report", "render", "emit", "publish", "export", "summarize",
        "summary", "html", "matrix", "dashboard", "lamp", "evidence",
    ),
    "risk": ("risk", "exposure", "drawdown", "volatility", "stress", "limit"),
    "scan": ("scan", "discover", "inventory", "index", "search", "locate", "probe"),
    "env": (
        "env", "environment", "package", "dependency", "install", "venv",
        "toolchain", "mirror",
    ),
    # v0200 新增：以本庫實測的未分類 token 分佈為依據（capability 29、store 21、
    # engine 16、conflict 12、lkgc 10 …），不是憑空取名。
    "capability": (
        "capability", "capabilities", "card", "capsule", "seal", "sealed",
        "variant", "annotate", "abstraction",
    ),
    "store": (
        "store", "storage", "database", "db", "sqlite", "blob", "dedup",
        "column", "incremental",
    ),
    "engine": (
        "engine", "engines", "module", "runtime", "entrypoint", "dispatch",
        "plugin",
    ),
    "conflict": (
        "conflict", "conflicts", "hydra", "drift", "collision", "cycle",
        "ownership", "sequential", "fixplan",
    ),
    "identity": (
        "identity", "identifier", "urn", "slug", "fingerprint", "sha",
        "hash", "digest", "blake",
    ),
    "filesystem": (
        "path", "paths", "file", "files", "directory", "descriptor", "handle",
        "posix", "symlink", "reparse", "junction",
    ),
    "platform": ("windows", "linux", "unix", "platform", "arch", "python"),
    "git": ("git", "commit", "branch", "clone", "repository", "worktree", "tracked"),
    "time": ("time", "iso", "stamp", "timestamp", "now", "clock", "date", "elapsed"),
    "text": ("text", "string", "token", "tokens", "bounded", "escape", "unicode"),
    "plan": ("plan", "planning", "lkgc", "baseline", "checkpoint", "staged"),
    "test": ("test", "tests", "selftest", "fixture", "assertion", "invariant"),
    "access": ("access", "layer", "route", "router", "strategy", "envelope"),
    "progress": ("progress", "bar", "percent", "heartbeat"),
    "function": ("function", "symbol", "callable", "signature", "arity"),
    "version": ("version", "versions", "semver", "revision", "pool"),
}

PARAM_SIMILARITY_WEIGHTS: dict[str, float] = {
    "embedding_cosine": 0.20,
    "token_jaccard": 0.30,
    "capability_agreement": 0.50,
}
PARAM_CLUSTER_LABEL_SEPARATOR = "#"

PARAM_DEFAULT_THRESHOLDS: dict[str, float] = {
    "similarity_threshold": 0.55,
    "abstraction_threshold": 0.80,
    "performance_floor": 0.70,
    "stability_floor": 0.95,
    "coverage_floor_percent": 100.0,
    "token_reduction_floor_percent": 70.0,
    "token_reduction_ceiling_percent": 90.0,
}

PARAM_LEAK_FIELDS = (
    "engine_id", "engines", "version", "version_pool", "strategy", "strategies",
    "sha256", "lock_seal", "entrypoint", "source_path", "performance_matrix",
)
PARAM_LEAK_MIN_VALUE_LENGTH = 8


PARAM_GUARANTEES = (
    "read-only-sources",
    "no-network",
    "stdlib-only",
    "fail-closed",
    "sealed-only-run",
    "no-raw-source-in-capsule",
    "candidate-only-writes",
    "blackbox-upstream",
    "audit-by-default",
    "append-only-capability-map",
)


class def_EngineError(RuntimeError):
    """引擎治理層錯誤：一律 fail-closed，不做隱性降級。"""


class def_ExecutionBudgetError(def_EngineError):
    """沙箱行數預算耗盡。"""


class def_LockRefused(def_EngineError):
    """沙盒驗證或性能基準未通過，拒絕鎖定。"""


class def_BlackBoxViolation(def_EngineError):
    """對上游 AI 的回傳值洩漏了引擎名稱、版本或策略。"""


# PEIS 前身的錯誤基底名稱保留為別名，舊呼叫端與舊測試不必改。
def_PeisError = def_EngineError


# --------------------------------------------------------------------------
# 0. 基礎工具：token 估算、雜湊、時間
# --------------------------------------------------------------------------
def def_token_estimate(text: str) -> int:
    """估算 LLM token 數：英數字每 4 字元 1 token，換行與符號各 1 token。

    只求跨執行完全一致且與長度單調，用來比較「讀全文」與「讀能力卡」的成本。
    """
    if not text:
        return 0
    total = 0
    run = 0
    for char in text:
        if char.isalnum() or char == "_":
            run += 1
            continue
        if run:
            total += (run + 3) // 4
            run = 0
        if char == "\n" or not char.isspace():
            total += 1
    if run:
        total += (run + 3) // 4
    return total


def def_compact_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=False,
                       default=str)


def def_sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def def_iso_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def def_bounded_text(value: Any, limit: int) -> str:
    text = " ".join(str(value).split())
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)] + "…"

def def_lamp(color: str, layer: str, message: str) -> None:
    """治理燈號走 stderr：`--json` 的 stdout 必須是單一份可解析的 JSON。"""
    print(f"{color:<7} {layer:<18} {message}", file=sys.stderr, flush=True)


@dataclass
class def_ProgressBar:
    """動態進度條：每個階段即時輸出百分比與情境說明。"""

    total: int
    label: str = "PEIS-PIPE"
    width: int = 20
    quiet: bool = False
    completed: int = 0
    lines: list[str] = field(default_factory=list)

    def def_advance(self, stage: str, detail: str, color: str = "GREEN") -> str:
        self.completed = min(self.completed + 1, self.total)
        return self.def_render(stage, detail, color)

    def def_render(self, stage: str, detail: str, color: str = "GREEN") -> str:
        ratio = 0.0 if self.total <= 0 else self.completed / self.total
        filled = int(round(ratio * self.width))
        bar = "█" * filled + "░" * (self.width - filled)
        layer = f"{self.label}-{self.completed:02d}/{self.total:02d}"
        message = f"[{bar}] {int(round(ratio * 100)):3d}% · {stage} · {detail}"
        line = f"{color:<7} {layer:<18} {message}"
        self.lines.append(line)
        if not self.quiet:
            print(line, file=sys.stderr, flush=True)
        return line

    def def_snapshot(self) -> dict[str, Any]:
        ratio = 0.0 if self.total <= 0 else self.completed / self.total
        return {
            "label": self.label,
            "completed": self.completed,
            "total": self.total,
            "percent": round(ratio * 100, 2),
            "lines": list(self.lines),
        }


def def_assert_inside_root(root: Path, path: Path) -> Path:
    resolved_root = root.resolve()
    resolved = path.resolve()
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise def_EngineError(f"路徑逸出治理根目錄：{path}")
    return resolved


def def_read_source(root: Path, path: Path) -> bytes:
    resolved = def_assert_inside_root(root, path)
    if path.is_symlink():
        raise def_EngineError(f"拒絕讀取 symlink：{path}")
    if not resolved.is_file():
        raise def_EngineError(f"來源檔不存在：{path}")
    size = resolved.stat().st_size
    if size > PARAM_MAX_SOURCE_BYTES:
        raise def_EngineError(f"來源檔超過上限 {PARAM_MAX_SOURCE_BYTES} bytes：{path}")
    return resolved.read_bytes()


def def_sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def def_write_atomic(path: Path, payload: str | bytes) -> Path:
    """原子寫檔。`bytes` 走二進位、不動換行；`str` 一律以 UTF-8＋LF 寫出。

    匯出引擎本體必須走 bytes：來源在 Windows 上是 CRLF，用文字讀寫會把它換成 LF，
    「逐位元組複製」就成了假話，MANIFEST 的 sha256 也對不上 `Get-FileHash`。
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    binary = isinstance(payload, bytes)
    handle, temporary_name = tempfile.mkstemp(dir=str(path.parent), prefix=".peis-", suffix=".tmp")
    temporary = Path(temporary_name)
    try:
        if binary:
            with os.fdopen(handle, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
        else:
            with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()
    return path


# ---------------------------------------------------------------------------
# SemanticExtractor / EmbeddingGenerator / SimilarityMatrixBuilder
# ---------------------------------------------------------------------------



def def_repo_root(start: Path | None = None) -> Path | None:
    """往上找同時具備 VIA_CentralGovernance.py 與 Root SSOT 的庫根；找不到回 None。"""
    current = (start or Path(__file__).resolve().parent).resolve()
    for candidate in (current, *current.parents):
        if all((candidate / marker).exists() for marker in PARAM_ROOT_MARKERS):
            return candidate
    return None


def def_git_root(start: Path | None = None) -> Path | None:
    """往上找 .git；獨立模式掃描任意 repo 時用得到。"""
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def def_resolve_root(start: Path | None = None) -> Path:
    """治理根目錄：VIA 庫根優先，其次 git 根，最後就用給定路徑（獨立模式）。"""
    given = (start or Path.cwd()).resolve()
    return def_repo_root(given) or def_git_root(given) or given


def def_payload_token_estimate(payload: Any) -> int:
    """PEIS 的 payload 估算：標準化 JSON 長度 / 4（與模型無關的保守下界）。

    與 `def_token_estimate`（原始碼文字）是兩套估算，用途不同、名稱分開，
    報表一律標明 estimator，不混用。
    """
    rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return max(1, math.ceil(len(rendered) / 4))


def def_token_jaccard(left: Iterable[str], right: Iterable[str]) -> float:
    """語意 token 的 Jaccard：兩邊皆空回 0.0（沒有證據就不給分）。

    與 `def_jaccard`（AST shingle，兩邊皆空視為相同）刻意不同語意。
    """
    first, second = set(left), set(right)
    if not first and not second:
        return 0.0
    union = first | second
    return len(first & second) / len(union) if union else 0.0


def def_capsule_policy(root: Path | None = None) -> dict[str, Any]:
    """讀 Root SSOT 的 capsule_policy；沒有 SSOT 就用內建上限（獨立模式）。"""
    policy = {
        "protocol": PARAM_CAPSULE_PROTOCOL,
        "max_chars": PARAM_CAPSULE_MAX_CHARS,
        "max_items": PARAM_CAPSULE_MAX_ITEMS,
        "source": "engine-default",
    }
    resolved = root if root is not None else def_repo_root()
    if resolved is None:
        return policy
    ssot = Path(resolved) / PARAM_ROOT_SSOT_RELATIVE
    if not ssot.is_file():
        return policy
    try:
        document = json.loads(ssot.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return policy
    declared = (document.get("token_governance") or {}).get("capsule_policy") or {}
    protocol = str(declared.get("protocol") or policy["protocol"])
    max_chars = declared.get("max_chars", policy["max_chars"])
    max_items = declared.get("max_items", policy["max_items"])
    if not isinstance(max_chars, int) or not isinstance(max_items, int):
        raise def_EngineError("capsule_policy 上限必須是整數（SSOT 漂移）")
    return {
        "protocol": protocol,
        "max_chars": max(1200, min(50000, max_chars)),
        "max_items": max(4, min(100, max_items)),
        "source": PARAM_ROOT_SSOT_RELATIVE.as_posix(),
    }


# --------------------------------------------------------------------------
# 1. 能力命名（聚眾的語意軸）
# --------------------------------------------------------------------------_
def def_build_alias_lookup(table: Mapping[str, Sequence[str]], label: str) -> dict[str, str]:
    """別名 → 分類；同一個別名被兩個分類宣告就 fail-closed。

    v0100 用 dict comprehension 建表，重複別名會被後者靜默覆蓋，字典本身就成了
    漂移來源；v0200 起與 SSOT 領域字典同一個規格：重複即拒絕。
    """
    lookup: dict[str, str] = {}
    for name in sorted(table):
        for alias in table[name]:
            token = str(alias).casefold()
            owner = lookup.get(token)
            if owner is not None and owner != name:
                raise def_EngineError(f"{label} 別名重複：{token} → {owner} / {name}")
            lookup[token] = name
    return lookup


PARAM_VERB_LOOKUP: dict[str, str] = def_build_alias_lookup(PARAM_VERBS, "verb")
PARAM_OBJECT_LOOKUP: dict[str, str] = def_build_alias_lookup(PARAM_OBJECTS, "object")


def def_split_identifier(name: str) -> list[str]:
    """camelCase 與 snake_case 一起拆成小寫詞元。"""
    tokens: list[str] = []
    buffer = ""
    for char in name:
        if char in "_-":
            if buffer:
                tokens.append(buffer.lower())
                buffer = ""
            continue
        if char.isupper() and buffer and not buffer[-1].isupper():
            tokens.append(buffer.lower())
            buffer = char
            continue
        buffer += char
    if buffer:
        tokens.append(buffer.lower())
    return [token for token in tokens if token and not token.isdigit()]


@lru_cache(maxsize=8192)
def def_capability_of(name: str) -> str:
    """把函式名收斂成 `verb.object` 能力 id；認不出動詞時歸 misc。"""
    tokens = [t for t in def_split_identifier(name) if t not in PARAM_STOPWORDS]
    verb: str | None = None
    rest: list[str] = []
    for token in tokens:
        if verb is None and token in PARAM_VERB_LOOKUP:
            verb = PARAM_VERB_LOOKUP[token]
            continue
        rest.append(PARAM_OBJECT_LOOKUP.get(token, token))
    deduped: list[str] = []
    for token in rest:
        if not deduped or deduped[-1] != token:
            deduped.append(token)
    return f"{verb or 'misc'}.{'_'.join(deduped) if deduped else 'any'}"

# --------------------------------------------------------------------------
# 1B. 語意層（SSOT 字典領域、決定性嵌入、相似度、單鏈聚類）
# --------------------------------------------------------------------------

def def_build_synonym_index(
    dictionary: dict[str, Sequence[str]] | None = None,
) -> dict[str, str]:
    """同義詞 → 能力名稱；重複定義 fail-closed，避免字典本身成為漂移來源。"""
    source = dictionary if dictionary is not None else PARAM_CAPABILITY_DICTIONARY
    index: dict[str, str] = {}
    for capability in sorted(source):
        for synonym in source[capability]:
            token = str(synonym).casefold()
            owner = index.get(token)
            if owner is not None and owner != capability:
                raise def_EngineError(f"SSOT 字典同義詞重複：{token} → {owner} / {capability}")
            index[token] = capability
    return index


PARAM_SYNONYM_INDEX = def_build_synonym_index()


def def_tokenize(name: str) -> tuple[str, ...]:
    """把 snake_case／camelCase／數字混合的符號拆成穩定的小寫語義 token。"""
    parts = re.findall(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+", str(name))
    tokens = [part.casefold() for part in parts if part]
    kept = [token for token in tokens if token not in PARAM_NOISE_TOKENS]
    strong = [token for token in kept if token not in PARAM_WEAK_TOKENS]
    return tuple(strong or kept or tokens)


def def_normalize_symbol(name: str) -> str:
    """語義標準化：去除雜訊前綴並把動詞提前（`trend_predict` → `predict_trend`）。"""
    tokens = list(def_tokenize(name))
    if not tokens:
        return str(name).casefold()
    for position, token in enumerate(tokens):
        if token in PARAM_VERB_TOKENS:
            if position:
                tokens.insert(0, tokens.pop(position))
            break
    return "_".join(tokens)


def def_expand_tokens(name: str, index: dict[str, str] | None = None) -> tuple[str, ...]:
    """token 集合加上其能力投影，讓同義詞在 Jaccard 上可以對齊。"""
    synonyms = PARAM_SYNONYM_INDEX if index is None else index
    tokens = def_tokenize(name)
    expanded = set(tokens)
    for token in tokens:
        capability = synonyms.get(token)
        if capability:
            expanded.add(capability)
    return tuple(sorted(expanded))


def def_capability_for_symbol(name: str, index: dict[str, str] | None = None) -> str:
    """能力歸屬：領域名詞優先於通用動詞（`calc_momentum` → signal，而非 math）。

    字典沒有命中就回傳 `unclassified`：PEIS 不用不認識的 token 自行捏造能力名稱，
    那種名稱會直接污染 CME 能力表。未分類符號走候選流程等待字典登錄。
    """
    synonyms = PARAM_SYNONYM_INDEX if index is None else index
    tokens = def_tokenize(name)
    verb_hit = ""
    for token in tokens:
        capability = synonyms.get(token)
        if not capability:
            continue
        if token not in PARAM_VERB_TOKENS:
            return capability
        verb_hit = verb_hit or capability
    return verb_hit or PARAM_UNCLASSIFIED


def def_embed(text: str, dimensions: int = PARAM_EMBEDDING_DIMENSIONS) -> tuple[float, ...]:
    """決定性特徵雜湊向量：blake2b 簽名雜湊，跨平台與跨行程完全一致。"""
    if dimensions <= 0:
        raise def_EngineError("embedding 維度必須為正整數")
    vector = [0.0] * dimensions
    normalized = def_normalize_symbol(text)
    features = list(def_expand_tokens(text))
    padded = f"^{normalized}$"
    features.extend(padded[offset:offset + 3] for offset in range(max(len(padded) - 2, 1)))
    for feature in features:
        digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
        value = int.from_bytes(digest, "big")
        vector[value % dimensions] += 1.0 if value & 1 else -1.0
    norm = math.sqrt(sum(component * component for component in vector))
    if norm == 0.0:
        return tuple(vector)
    return tuple(round(component / norm, PARAM_EMBEDDING_PRECISION) for component in vector)


def def_centroid(vectors: Sequence[Sequence[float]]) -> tuple[float, ...]:
    if not vectors:
        return ()
    dimensions = len(vectors[0])
    total = [0.0] * dimensions
    for vector in vectors:
        if len(vector) != dimensions:
            raise def_EngineError("centroid 維度不一致")
        for position, component in enumerate(vector):
            total[position] += component
    norm = math.sqrt(sum(component * component for component in total))
    if norm == 0.0:
        return tuple(total)
    return tuple(round(component / norm, PARAM_EMBEDDING_PRECISION) for component in total)


def def_cosine(left: Sequence[float], right: Sequence[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    product = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return product / (left_norm * right_norm)



def def_similarity(left: str, right: str, index: dict[str, str] | None = None) -> float:
    """語義距離 = 能力一致性 0.50 + token Jaccard 0.30 + 向量餘弦 0.20。

    能力一致性權重最高：PEIS 要的是「同一件事的不同說法」（`calc` / `compute` /
    `calculate`）收斂到同一格，而不是字面拼寫相近。
    """
    if left == right:
        return 1.0
    weights = PARAM_SIMILARITY_WEIGHTS
    cosine = def_cosine(def_embed(left), def_embed(right))
    overlap = def_token_jaccard(def_expand_tokens(left, index), def_expand_tokens(right, index))
    left_capability = def_capability_for_symbol(left, index)
    right_capability = def_capability_for_symbol(right, index)
    lexical = weights["embedding_cosine"] * max(cosine, 0.0) + weights["token_jaccard"] * overlap
    if left_capability == right_capability != PARAM_UNCLASSIFIED:
        score = lexical + weights["capability_agreement"]
    elif left_capability == right_capability == PARAM_UNCLASSIFIED:
        # 兩邊都沒有字典證據：能力一致性這條證據通道缺席，對可得證據重新歸一化，
        # 否則未分類符號永遠到不了門檻，候選能力就永遠不會被發現。
        divisor = weights["embedding_cosine"] + weights["token_jaccard"]
        score = lexical / divisor if divisor else 0.0
    else:
        # 一邊有字典能力、一邊沒有（或分屬不同能力）：不給任何能力一致性分數。
        score = lexical
    return round(min(max(score, 0.0), 1.0), PARAM_SIMILARITY_PRECISION)


def def_build_similarity_matrix(
    names: Sequence[str],
    index: dict[str, str] | None = None,
) -> dict[str, dict[str, float]]:
    """全域相似度矩陣：名稱排序後計算，任何執行順序都得到同一份矩陣。"""
    ordered = sorted({def_normalize_symbol(name) for name in names})
    matrix: dict[str, dict[str, float]] = {name: {} for name in ordered}
    for first_position, first in enumerate(ordered):
        for second in ordered[first_position + 1:]:
            score = def_similarity(first, second, index)
            matrix[first][second] = score
            matrix[second][first] = score
    return matrix


def def_cluster(
    names: Sequence[str],
    threshold: float,
    index: dict[str, str] | None = None,
    matrix: dict[str, dict[str, float]] | None = None,
) -> dict[str, tuple[str, ...]]:
    """單鏈聚類：以能力標籤命名群組，`signal → [gen_signal, calc_momentum, ...]`。"""
    ordered = sorted({def_normalize_symbol(name) for name in names})
    if not ordered:
        return {}
    scores = matrix if matrix is not None else def_build_similarity_matrix(ordered, index)
    parent = {name: name for name in ordered}

    def def_find(name: str) -> str:
        while parent[name] != name:
            parent[name] = parent[parent[name]]
            name = parent[name]
        return name

    for first_position, first in enumerate(ordered):
        for second in ordered[first_position + 1:]:
            if scores.get(first, {}).get(second, 0.0) >= threshold:
                first_root, second_root = def_find(first), def_find(second)
                if first_root != second_root:
                    parent[max(first_root, second_root)] = min(first_root, second_root)

    groups: dict[str, list[str]] = {}
    for name in ordered:
        groups.setdefault(def_find(name), []).append(name)

    clusters: dict[str, tuple[str, ...]] = {}
    for members in sorted(groups.values(), key=lambda values: values[0]):
        counts: dict[str, int] = {}
        for member in members:
            capability = def_capability_for_symbol(member, index)
            counts[capability] = counts.get(capability, 0) + 1
        base = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]
        label, suffix = base, 1
        while label in clusters:
            suffix += 1
            label = f"{base}{PARAM_CLUSTER_LABEL_SEPARATOR}{suffix}"
        clusters[label] = tuple(sorted(members))
    return dict(sorted(clusters.items()))


def def_cluster_base(label: str) -> str:
    """群組標籤還原成能力名稱（`data#2` → `data`）。"""
    return str(label).split(PARAM_CLUSTER_LABEL_SEPARATOR, 1)[0]


# ---------------------------------------------------------------------------
# EngineScanner + AST 雙模定位
# ---------------------------------------------------------------------------




# --------------------------------------------------------------------------
# 2. AST α-rename Merkle 指紋（跨執行穩定）
# --------------------------------------------------------------------------
PARAM_MASK64 = (1 << 64) - 1
PARAM_MIX_C1 = 0x9E3779B97F4A7C15
PARAM_MIX_C2 = 0xBF58476D1CE4E5B9
PARAM_FNV_PRIME = 0x100000001B3
PARAM_FNV_OFFSET = 0xCBF29CE484222325


def def_hash_text(text: str) -> int:
    digest = PARAM_FNV_OFFSET
    for byte in text.encode("utf-8"):
        digest ^= byte
        digest = (digest * PARAM_FNV_PRIME) & PARAM_MASK64
    return digest


def def_rotate_left(value: int, bits: int) -> int:
    return ((value << bits) | (value >> (64 - bits))) & PARAM_MASK64


def def_mix(digest: int, value: int) -> int:
    digest ^= value & PARAM_MASK64
    digest = (digest * PARAM_MIX_C2) & PARAM_MASK64
    digest = def_rotate_left(digest, 31)
    return (digest * PARAM_MIX_C1) & PARAM_MASK64


@lru_cache(maxsize=512)
def def_type_id(class_name: str) -> int:
    """節點型別 id 取自名稱雜湊，與掃描順序及行程無關（原型的序號配發已修正）。"""
    return def_hash_text(f"ast:{class_name}")


def def_shingles(type_ids: Sequence[int]) -> tuple[int, ...]:
    if not type_ids:
        return ()
    window: set[int] = set()
    total = len(type_ids)
    for index in range(max(1, total - 2)):
        first = type_ids[index]
        second = type_ids[index + 1] if index + 1 < total else 0
        third = type_ids[index + 2] if index + 2 < total else 0
        window.add(def_mix(def_mix(first, second), third))
    return tuple(sorted(window))


def def_jaccard(left: Iterable[int], right: Iterable[int]) -> float:
    first, second = set(left), set(right)
    if not first and not second:
        return 1.0
    return len(first & second) / max(1, len(first | second))


def def_normalize_function(
    node: ast.AST, module_functions: Sequence[str]
) -> tuple[str, list[str], list[int], tuple[int, ...]]:
    """α-rename 後的 Merkle 指紋：一次走訪，不比字串、不雜湊原文。"""
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        raise def_EngineError("只接受函式節點")
    module_set = set(module_functions)
    module_set.discard(node.name)
    bound: dict[str, int] = {}
    module_refs: list[str] = []
    type_ids: list[int] = []

    def bind(name: str) -> int:
        value = bound.get(name)
        if value is None:
            value = def_hash_text(f"v{len(bound)}")
            bound[name] = value
        return value

    def walk(current: ast.AST) -> int:
        type_id = def_type_id(current.__class__.__name__)
        type_ids.append(type_id)
        if isinstance(current, ast.Name):
            identifier = current.id
            if isinstance(current.ctx, ast.Store):
                payload = (
                    def_hash_text("self")
                    if identifier in ("self", "cls")
                    else bind(identifier)
                )
            elif identifier in bound:
                payload = bound[identifier]
            elif identifier == node.name:
                payload = def_hash_text("_F")
            elif identifier in module_set:
                if identifier not in module_refs:
                    module_refs.append(identifier)
                payload = def_hash_text(f"mod_{module_refs.index(identifier)}")
            elif identifier in PARAM_PY_BUILTINS:
                payload = def_hash_text(identifier)
            else:
                payload = def_hash_text(f"ext_{identifier}")
            return def_mix(type_id, payload)
        if isinstance(current, ast.Constant):
            payload = (
                def_hash_text("S")
                if isinstance(current.value, str)
                else def_hash_text(repr(current.value))
            )
            return def_mix(type_id, payload)
        if isinstance(current, ast.Attribute):
            digest = def_mix(type_id, walk(current.value))
            return def_mix(digest, def_hash_text(current.attr))
        if isinstance(current, ast.AnnAssign):
            digest = def_mix(type_id, walk(current.target))
            if current.value is not None:
                digest = def_mix(digest, walk(current.value))
            return digest
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return def_mix(type_id, def_hash_text("NESTED"))
        digest = type_id
        for child in ast.iter_child_nodes(current):
            digest = def_mix(digest, walk(child))
        return digest

    root_id = def_type_id(node.__class__.__name__)
    type_ids.append(root_id)
    digest = def_mix(root_id, def_hash_text("_F"))
    arguments = node.args
    for argument in (*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs):
        if argument.arg in ("self", "cls"):
            continue
        digest = def_mix(digest, bind(argument.arg))
    if arguments.vararg:
        digest = def_mix(digest, bind(arguments.vararg.arg))
    if arguments.kwarg:
        digest = def_mix(digest, bind(arguments.kwarg.arg))
    body = list(node.body)
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(getattr(body[0], "value", None), ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        body = body[1:]
    for statement in body:
        digest = def_mix(digest, walk(statement))
    tail = def_mix(digest ^ PARAM_MIX_C1, len(type_ids))
    fingerprint = f"{digest:016x}{tail:016x}"
    if module_refs:
        fingerprint = f"{def_mix(digest, def_hash_text(','.join(module_refs))):016x}{tail:016x}"
    return fingerprint, module_refs, type_ids, def_shingles(type_ids)


# --------------------------------------------------------------------------
# 3. 記錄結構
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class def_FunctionRecord:
    path: str
    name: str
    qualname: str
    lineno: int
    end_lineno: int
    capability: str
    fingerprint: str
    signature: str
    returns: str
    doc: str
    tools: tuple[str, ...]
    risks: tuple[str, ...]
    nodes: int
    arity: int
    shingles: tuple[int, ...]
    vendorable: bool
    executable: bool
    skip_reason: str
    is_method: bool
    is_async: bool
    module_executable: bool
    body_tokens: int
    body_sha256: str
    source: str = field(default="", repr=False, compare=False)

    @property
    def anchor(self) -> str:
        return f"{self.path}#L{self.lineno}"

    @property
    def member(self) -> str:
        return f"{self.path}:{self.qualname}"


@dataclass(frozen=True)
class def_Variant:
    variant: str
    fingerprint: str
    canonical: str
    members: tuple[str, ...]
    vendorable: bool
    executable: bool
    near: tuple[str, ...] = ()


@dataclass(frozen=True)
class def_Capability:
    capability: str
    default_variant: str
    variants: tuple[def_Variant, ...]

    @property
    def member_count(self) -> int:
        return sum(len(variant.members) for variant in self.variants)

    @property
    def collapsed(self) -> int:
        return sum(max(0, len(variant.members) - 1) for variant in self.variants)

    def variant_of(self, variant_id: str) -> def_Variant:
        for variant in self.variants:
            if variant.variant == variant_id:
                return variant
        raise def_EngineError(f"variant 不存在：{self.capability}/{variant_id}")


@dataclass(frozen=True)
class def_TestOutcome:
    capability: str
    status: str
    probe: str
    arguments: str
    result: str
    equivalent: tuple[str, ...]
    divergent: tuple[str, ...]
    detail: str
    gate: str = PARAM_SANDBOX_GATE
    runs: int = 0
    run_failures: int = 0
    coverage_percent: float = 0.0


@dataclass(frozen=True)
class def_LockEntry:
    capability: str
    engine_id: str
    status: str
    variant: str
    fingerprint: str
    kind: str
    sealed_at: str


@dataclass
class def_Plan:
    capabilities: dict[str, def_Capability] = field(default_factory=dict)
    records: list[def_FunctionRecord] = field(default_factory=list)
    mode: str = "independent"
    intake: dict[str, int] = field(default_factory=dict)

    @property
    def collapsed(self) -> int:
        return sum(capability.collapsed for capability in self.capabilities.values())

    @property
    def near_duplicates(self) -> int:
        return sum(
            len(variant.near)
            for capability in self.capabilities.values()
            for variant in capability.variants
        )

    def records_by_fingerprint(self, fingerprint: str) -> list[def_FunctionRecord]:
        return [record for record in self.records if record.fingerprint == fingerprint]


# --------------------------------------------------------------------------
# 4. 掃描：簽章、工具家族、風險稽核、沙箱可執行性
# --------------------------------------------------------------------------
def def_signature_text(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    arguments = node.args
    parts: list[str] = [argument.arg for argument in arguments.posonlyargs]
    if arguments.posonlyargs:
        parts.append("/")
    parts.extend(argument.arg for argument in arguments.args)
    if arguments.vararg:
        parts.append(f"*{arguments.vararg.arg}")
    elif arguments.kwonlyargs:
        parts.append("*")
    parts.extend(argument.arg for argument in arguments.kwonlyargs)
    if arguments.kwarg:
        parts.append(f"**{arguments.kwarg.arg}")
    return f"{node.name}({', '.join(parts)})"


def def_return_annotation(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    if node.returns is None:
        return ""
    try:
        return def_bounded_text(ast.unparse(node.returns), 60)
    except (AttributeError, ValueError):
        return ""


def def_alias_families(tree: ast.Module) -> dict[str, str]:
    """模組匯入的 alias → 工具家族。"""
    families: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                local = (alias.asname or root).split(".")[0]
                family = PARAM_ALIAS_TO_FAMILY.get(root) or PARAM_ALIAS_TO_FAMILY.get(local)
                if family:
                    families[local] = family
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            family = PARAM_ALIAS_TO_FAMILY.get(root)
            for alias in node.names:
                local = alias.asname or alias.name
                resolved = family or PARAM_ALIAS_TO_FAMILY.get(alias.name)
                if resolved:
                    families[local] = resolved
    return families


def def_name_roots(node: ast.AST) -> set[str]:
    roots: set[str] = set()
    for current in ast.walk(node):
        if isinstance(current, ast.Name):
            roots.add(current.id)
    return roots


def def_detect_tools(
    node: ast.FunctionDef | ast.AsyncFunctionDef, families: Mapping[str, str]
) -> tuple[str, ...]:
    used: set[str] = set()
    for identifier in def_name_roots(node):
        family = families.get(identifier)
        if family:
            used.add(family)
    return tuple(sorted(used))


def def_statement_count(node: ast.AST) -> int:
    return sum(1 for child in ast.walk(node) if isinstance(child, ast.stmt))


def def_max_depth(node: ast.AST, depth: int = 0) -> int:
    children = [
        child
        for child in ast.iter_child_nodes(node)
        if isinstance(child, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.With,
                              ast.AsyncWith, ast.Try))
    ]
    if not children:
        return depth
    return max(def_max_depth(child, depth + 1) for child in children)


def def_audit_risks(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    tools: Sequence[str],
    arity: int,
    has_star: bool,
) -> tuple[str, ...]:
    risks: set[str] = set()
    if node.returns is None:
        risks.add("R01")
    annotated = sum(
        1
        for argument in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs)
        if argument.annotation is not None
    )
    declared = len(node.args.posonlyargs) + len(node.args.args) + len(node.args.kwonlyargs)
    if declared and annotated < declared:
        risks.add("R02")
    if ast.get_docstring(node) is None:
        risks.add("R05")
    if any(family in PARAM_NETWORK_FAMILIES for family in tools):
        risks.add("R06")
    if "subprocess" in tools:
        risks.add("R08")
    if arity > 5 or has_star:
        risks.add("R11")
    if def_max_depth(node) > 4:
        risks.add("R12")
    if def_statement_count(node) > 60:
        risks.add("R13")
    for default in (*node.args.defaults, *[d for d in node.args.kw_defaults if d]):
        if isinstance(default, (ast.List, ast.Dict, ast.Set, ast.Call)):
            risks.add("R04")
    own_name = node.name
    for argument in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs):
        if argument.arg in PARAM_PY_BUILTINS:
            risks.add("R18")
    for current in ast.walk(node):
        if isinstance(current, ast.Assert):
            risks.add("R17")
        elif isinstance(current, ast.Name) and isinstance(current.ctx, ast.Load):
            if current.id == own_name:
                risks.add("R19")
            if current.id in PARAM_NONDETERMINISTIC_TIME:
                risks.add("R20")
            if current.id in PARAM_NONDETERMINISTIC_RANDOM:
                risks.add("R24")
        elif isinstance(current, ast.Attribute):
            if current.attr in PARAM_NONDETERMINISTIC_TIME:
                risks.add("R20")
            if current.attr in PARAM_NONDETERMINISTIC_RANDOM:
                risks.add("R24")
        if isinstance(current, ast.Constant) and isinstance(current.value, str):
            if PARAM_ABSOLUTE_PATH_RE.match(current.value):
                risks.add("R21")
            if "http://" in current.value or "https://" in current.value:
                risks.add("R23")
        if isinstance(current, (ast.Assign, ast.AnnAssign)):
            targets = current.targets if isinstance(current, ast.Assign) else [current.target]
            labels = [
                target.id for target in targets if isinstance(target, ast.Name)
            ] + [
                target.attr for target in targets if isinstance(target, ast.Attribute)
            ]
            value = current.value
            if (
                any(PARAM_SECRET_NAME_RE.search(label) for label in labels)
                and isinstance(value, ast.Constant)
                and isinstance(value.value, str)
                and value.value
            ):
                risks.add("R22")
        if isinstance(current, ast.Call):
            for keyword in current.keywords:
                if (
                    keyword.arg
                    and PARAM_SECRET_NAME_RE.search(keyword.arg)
                    and isinstance(keyword.value, ast.Constant)
                    and isinstance(keyword.value.value, str)
                    and keyword.value.value
                ):
                    risks.add("R22")
        if isinstance(current, ast.ExceptHandler) and current.type is None:
            risks.add("R03")
        elif isinstance(current, ast.ExceptHandler) and any(
            isinstance(statement, ast.Pass) for statement in current.body
        ):
            risks.add("R03")
        elif isinstance(current, (ast.Global, ast.Nonlocal)):
            risks.add("R10")
        elif isinstance(current, ast.While):
            risks.add("R14")
        elif isinstance(current, ast.Compare) and any(
            isinstance(operator, (ast.Eq, ast.NotEq)) for operator in current.ops
        ):
            if any(
                isinstance(comparator, ast.Constant) and isinstance(comparator.value, float)
                for comparator in current.comparators
            ):
                risks.add("R15")
        elif isinstance(current, ast.Call):
            target = current.func
            if isinstance(target, ast.Name):
                if target.id in ("eval", "exec", "compile", "__import__"):
                    risks.add("R09")
                elif target.id == "print":
                    risks.add("R16")
                elif target.id == "open":
                    risks.add("R07")
            elif isinstance(target, ast.Attribute):
                if target.attr in ("write", "writelines", "write_text", "write_bytes"):
                    risks.add("R07")
                elif target.attr in ("system", "popen", "run", "Popen", "check_output"):
                    if "subprocess" in tools or "filesystem" in tools:
                        risks.add("R08")
    return tuple(sorted(risks))


def def_execution_audit(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    vendorable: bool,
    is_method: bool,
    arity: int,
    has_star: bool,
    nodes: int,
) -> str:
    """回傳空字串代表可進沙箱測試；否則回傳拒絕原因（fail-closed）。"""
    if is_method:
        return "method"
    if isinstance(node, ast.AsyncFunctionDef):
        return "async"
    if not vendorable:
        return "not-vendorable"
    if node.decorator_list:
        return "decorated"
    if has_star or arity > PARAM_EXECUTION_MAX_ARITY:
        return "arity"
    if nodes > PARAM_EXECUTION_MAX_NODES:
        return "too-large"
    if any(default is not None for default in node.args.kw_defaults) or node.args.kwonlyargs:
        return "keyword-only"
    for current in ast.walk(node):
        if isinstance(current, (ast.Import, ast.ImportFrom)):
            return "import"
        if isinstance(current, ast.While):
            return "while"
        if isinstance(current, (ast.Global, ast.Nonlocal)):
            return "global"
        if isinstance(current, (ast.Yield, ast.YieldFrom, ast.Await)):
            return "generator"
        if isinstance(current, (ast.With, ast.AsyncWith)):
            return "context-manager"
        if isinstance(current, ast.Name) and current.id in PARAM_FORBIDDEN_EXEC_NAMES:
            return f"forbidden-name:{current.id}"
        if isinstance(current, ast.Attribute):
            if current.attr.startswith("__") or current.attr in PARAM_FORBIDDEN_EXEC_ATTRIBUTES:
                return f"forbidden-attribute:{current.attr}"
        if isinstance(current, ast.Constant):
            if isinstance(current.value, bool):
                continue
            if isinstance(current.value, (int, float)) and abs(current.value) > PARAM_EXECUTION_MAX_CONSTANT:
                return "constant-too-large"
            if isinstance(current.value, str) and len(current.value) > 4096:
                return "constant-too-large"
    return ""


def def_source_segment(lines: Sequence[str], node: ast.AST) -> str:
    start = max(0, getattr(node, "lineno", 1) - 1)
    end = getattr(node, "end_lineno", start + 1) or start + 1
    return "".join(lines[start:end])


def def_scan_source(text: str, path: str = "<memory>") -> list[def_FunctionRecord]:
    """唯讀掃描一份原始碼；語法錯誤隔離成空結果，不改寫來源。"""
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return []
    lines = text.splitlines(True)
    families = def_alias_families(tree)
    module_functions = [
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    targets: list[tuple[ast.FunctionDef | ast.AsyncFunctionDef, str, bool]] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            targets.append((node, node.name, False))
        elif isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    targets.append((child, f"{node.name}.{child.name}", True))
    records: list[def_FunctionRecord] = []
    for node, qualname, is_method in targets:
        fingerprint, module_refs, type_ids, shingles = def_normalize_function(
            node, module_functions
        )
        arguments = node.args
        declared = [
            argument.arg
            for argument in (*arguments.posonlyargs, *arguments.args)
            if argument.arg not in ("self", "cls")
        ]
        has_star = bool(arguments.vararg or arguments.kwarg)
        arity = len(declared)
        tools = def_detect_tools(node, families)
        risks = def_audit_risks(node, tools, arity, has_star)
        vendorable = (not node.decorator_list) and (not module_refs)
        skip_reason = def_execution_audit(
            node, vendorable, is_method, arity, has_star, len(type_ids)
        )
        body = def_source_segment(lines, node)
        docstring = ast.get_docstring(node) or ""
        records.append(
            def_FunctionRecord(
                path=path,
                name=node.name,
                qualname=qualname,
                lineno=getattr(node, "lineno", 0),
                end_lineno=getattr(node, "end_lineno", 0) or 0,
                capability=def_capability_of(node.name),
                fingerprint=fingerprint,
                signature=def_signature_text(node),
                returns=def_return_annotation(node),
                doc=def_bounded_text(docstring.splitlines()[0] if docstring else "", PARAM_DOC_LIMIT),
                tools=tools,
                risks=risks,
                nodes=len(type_ids),
                arity=arity,
                shingles=shingles,
                vendorable=vendorable,
                executable=not skip_reason,
                skip_reason=skip_reason,
                is_method=is_method,
                is_async=isinstance(node, ast.AsyncFunctionDef),
                module_executable=(
                    not is_method
                    and not isinstance(node, ast.AsyncFunctionDef)
                    and not has_star
                    and 0 < arity <= PARAM_EXECUTION_MAX_ARITY
                    and not node.name.startswith("_")
                ),
                body_tokens=def_token_estimate(body),
                body_sha256=def_sha256_text(body),
                source=body,
            )
        )
    return records



# --------------------------------------------------------------------------
# 4B. 引擎級掃描（公開符號、呼叫圖、AST 雙模定位；Git tracked 唯讀）
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class def_SymbolSite:
    symbol: str
    kind: str
    lineno: int
    col_offset: int


@dataclass(frozen=True)
class def_EngineCandidate:
    source_path: str
    sha256: str
    ast_status: str
    ast_error: str
    symbols: tuple[str, ...]
    normalized: tuple[str, ...]
    calls: tuple[tuple[str, str], ...]


def def_git_tracked_python(root: Path) -> tuple[Path, ...]:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--", "*.py"],
            capture_output=True,
            text=True,
            check=True,
            timeout=120,
        )
        names = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    except (OSError, subprocess.SubprocessError):
        names = [
            path.relative_to(root).as_posix()
            for path in sorted(root.rglob("*.py"))
            if path.is_file()
        ]
    return tuple(root / name for name in sorted(names))


def def_public_symbols(tree: ast.AST) -> tuple[def_SymbolSite, ...]:
    """SYMBOL 模式定位：模組層函式／類別與類別公開方法。"""
    sites: list[def_SymbolSite] = []
    for node in getattr(tree, "body", []):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                sites.append(def_SymbolSite(node.name, "function", node.lineno, node.col_offset))
        elif isinstance(node, ast.ClassDef):
            if node.name.startswith("_"):
                continue
            sites.append(def_SymbolSite(node.name, "class", node.lineno, node.col_offset))
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and not child.name.startswith("_"):
                    sites.append(
                        def_SymbolSite(
                            f"{node.name}.{child.name}", "method", child.lineno, child.col_offset
                        )
                    )
    return tuple(sorted(sites, key=lambda site: (site.lineno, site.col_offset, site.symbol)))


def def_call_edges(tree: ast.AST) -> tuple[tuple[str, str], ...]:
    """CALL 模式定位：呼叫圖邊（呼叫者 → 被呼叫符號），供全景相依分析使用。"""
    edges: list[tuple[str, str]] = []

    class def_CallVisitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.scope: list[str] = []

        def def_enter(self, name: str, node: ast.AST) -> None:
            self.scope.append(name)
            self.generic_visit(node)
            self.scope.pop()

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
            self.def_enter(node.name, node)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
            self.def_enter(node.name, node)

        def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: N802
            self.def_enter(node.name, node)

        def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
            caller = self.scope[-1] if self.scope else "<module>"
            target = ""
            if isinstance(node.func, ast.Name):
                target = node.func.id
            elif isinstance(node.func, ast.Attribute):
                target = node.func.attr
            if target:
                edges.append((caller, target))
            self.generic_visit(node)

    def_CallVisitor().visit(tree)
    return tuple(sorted(set(edges)))


def def_locate_symbol(source: str, symbol: str) -> dict[str, tuple[dict[str, int], ...]]:
    """AST 雙模定位：同時回報定義點（SYMBOL）與呼叫點（CALL）。"""
    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        raise def_EngineError(f"AST 解析失敗：line {error.lineno}: {error.msg}") from error
    leaf = symbol.split(".")[-1]
    definitions: list[dict[str, int]] = []
    calls: list[dict[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == leaf:
            definitions.append({"lineno": node.lineno, "col_offset": node.col_offset})
        elif isinstance(node, ast.Call):
            target = ""
            if isinstance(node.func, ast.Name):
                target = node.func.id
            elif isinstance(node.func, ast.Attribute):
                target = node.func.attr
            if target == leaf:
                calls.append({"lineno": node.lineno, "col_offset": node.col_offset})
    key = lambda site: (site["lineno"], site["col_offset"])  # noqa: E731
    return {
        "symbol_mode": tuple(sorted(definitions, key=key)),
        "call_mode": tuple(sorted(calls, key=key)),
    }


def def_scan_engine_file(root: Path, path: Path) -> def_EngineCandidate:
    relative = path.resolve().relative_to(root.resolve()).as_posix()
    payload = def_read_source(root, path)
    source = payload.decode("utf-8-sig", errors="replace")
    ast_status, ast_error = "PASS", ""
    symbols: tuple[str, ...] = ()
    calls: tuple[tuple[str, str], ...] = ()
    try:
        tree = ast.parse(source, filename=relative)
    except SyntaxError as error:
        ast_status = "FAIL"
        ast_error = f"line {error.lineno}: {error.msg}"
    else:
        symbols = tuple(site.symbol for site in def_public_symbols(tree))
        calls = def_call_edges(tree)
    return def_EngineCandidate(
        source_path=relative,
        sha256=def_sha256_bytes(payload),
        ast_status=ast_status,
        ast_error=ast_error,
        symbols=symbols,
        normalized=tuple(sorted({def_normalize_symbol(symbol) for symbol in symbols})),
        calls=calls,
    )


def def_scan_engines(
    root: Path,
    prefixes: Sequence[str] = PARAM_ENGINE_SCAN_PREFIXES,
) -> tuple[def_EngineCandidate, ...]:
    """步驟 1 EngineScanner：定位新引擎、新檔案與新版本（Git tracked，只讀）。"""
    candidates: list[def_EngineCandidate] = []
    for path in def_git_tracked_python(root):
        relative = path.relative_to(root).as_posix()
        if not relative.startswith(tuple(prefixes)):
            continue
        if path.name in PARAM_SCAN_EXCLUDED_NAMES or path.name.startswith("test_"):
            continue
        if not path.is_file() or path.is_symlink():
            continue
        candidates.append(def_scan_engine_file(root, path))
    return tuple(sorted(candidates, key=lambda candidate: candidate.source_path))


# ---------------------------------------------------------------------------
# EngineLocker
# ---------------------------------------------------------------------------



def def_iter_python_files(targets: Sequence[Path]) -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()
    for target in targets:
        resolved = Path(target)
        if not resolved.exists():
            raise def_EngineError(f"輸入不存在：{resolved}")
        if resolved.is_file():
            candidates = [resolved] if resolved.suffix == ".py" else []
        else:
            candidates = [
                path
                for path in sorted(resolved.rglob("*.py"))
                if path.is_file()
                and not any(part in PARAM_SKIP_DIRECTORIES for part in path.parts)
            ]
        for candidate in candidates:
            key = candidate.resolve()
            if key in seen:
                continue
            seen.add(key)
            files.append(candidate)
    return files


# --------------------------------------------------------------------------
# 5. 聚眾：同能力分群、exact 指紋合併、近似變體標註
# --------------------------------------------------------------------------
def def_unify(
    records: Sequence[def_FunctionRecord],
    mode: str = "independent",
    threshold: float = PARAM_NEAR_DUPLICATE_THRESHOLD,
) -> def_Plan:
    by_fingerprint: dict[str, list[def_FunctionRecord]] = defaultdict(list)
    for record in records:
        by_fingerprint[record.fingerprint].append(record)
    grouped: dict[str, dict[str, list[def_FunctionRecord]]] = defaultdict(dict)
    for fingerprint, members in by_fingerprint.items():
        votes: dict[str, int] = defaultdict(int)
        for member in members:
            votes[member.capability] += 1
        capability = sorted(votes.items(), key=lambda item: (-item[1], item[0]))[0][0]
        grouped[capability][fingerprint] = members
    capabilities: dict[str, def_Capability] = {}
    for capability, fingerprints in sorted(grouped.items()):
        ordered = sorted(
            fingerprints.items(), key=lambda item: (-len(item[1]), item[0])
        )
        variants: list[def_Variant] = []
        for index, (fingerprint, members) in enumerate(ordered, start=1):
            canonical = sorted(members, key=lambda record: (record.path, record.lineno))[0]
            variants.append(
                def_Variant(
                    variant=f"v{index}",
                    fingerprint=fingerprint,
                    canonical=canonical.qualname,
                    members=tuple(
                        sorted(member.member for member in members)
                    ),
                    vendorable=canonical.vendorable,
                    executable=canonical.executable,
                )
            )
        linked: list[def_Variant] = []
        for index, variant in enumerate(variants):
            canonical = by_fingerprint[variant.fingerprint][0]
            near: list[str] = []
            for other_index, other in enumerate(variants):
                if other_index == index:
                    continue
                other_canonical = by_fingerprint[other.fingerprint][0]
                score = def_jaccard(canonical.shingles, other_canonical.shingles)
                if score >= threshold:
                    near.append(other.variant)
            linked.append(
                def_Variant(
                    variant=variant.variant,
                    fingerprint=variant.fingerprint,
                    canonical=variant.canonical,
                    members=variant.members,
                    vendorable=variant.vendorable,
                    executable=variant.executable,
                    near=tuple(near),
                )
            )
        capabilities[capability] = def_Capability(
            capability=capability,
            default_variant="v1",
            variants=tuple(linked),
        )
    return def_Plan(
        capabilities=capabilities,
        records=list(records),
        mode=mode,
    )


def def_needs_consolidation(plan: def_Plan) -> bool:
    if plan.collapsed > 0:
        return True
    return any(
        len(capability.variants) > 1 for capability in plan.capabilities.values()
    )


# --------------------------------------------------------------------------
# 6. 測試：受限沙箱 + 影子對照
# --------------------------------------------------------------------------
def def_safe_builtins() -> dict[str, Any]:
    import builtins as _builtins

    table: dict[str, Any] = {}
    for name in PARAM_SAFE_BUILTIN_NAMES:
        if hasattr(_builtins, name):
            table[name] = getattr(_builtins, name)
    return table


def def_execute_guarded(
    source: str,
    name: str,
    arguments: Sequence[Any],
    line_budget: int = PARAM_EXECUTION_LINE_BUDGET,
) -> Any:
    """在受限命名空間執行單一純函式：無 import、無檔案、行數有預算。"""
    namespace: dict[str, Any] = {"__builtins__": def_safe_builtins()}
    compiled = compile(source, f"<vue:{name}>", "exec")
    exec(compiled, namespace, namespace)  # noqa: S102 - 受限 builtins、AST 已審核
    target = namespace.get(name)
    if not callable(target):
        raise def_EngineError(f"沙箱找不到可呼叫的 {name}")
    counter = [0]

    def tracer(frame: Any, event: str, argument: Any):
        if event == "line":
            counter[0] += 1
            if counter[0] > line_budget:
                raise def_ExecutionBudgetError(f"{name} 超出行數預算 {line_budget}")
        return tracer

    previous = sys.gettrace()
    sys.settrace(tracer)
    try:
        return target(*arguments)
    finally:
        sys.settrace(previous)


def def_probe_candidates(record: def_FunctionRecord) -> list[tuple[str, tuple[Any, ...]]]:
    return [
        (name, vector)
        for name, vector in PARAM_PROBE_VECTORS
        if len(vector) == record.arity
    ]


def def_values_equal(left: Any, right: Any, tolerance: float = PARAM_FLOAT_TOLERANCE) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return left is right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return abs(float(left) - float(right)) <= tolerance
    if isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)):
        if len(left) != len(right):
            return False
        return all(def_values_equal(a, b, tolerance) for a, b in zip(left, right))
    if isinstance(left, dict) and isinstance(right, dict):
        if set(left) != set(right):
            return False
        return all(def_values_equal(left[key], right[key], tolerance) for key in left)
    return left == right


PARAM_MODULE_BOOTSTRAP = r"""
import importlib.util, json, sys
payload = json.loads(sys.stdin.read())
spec = importlib.util.spec_from_file_location("vue_probe_target", payload["path"])
answers = []
if spec is None or spec.loader is None:
    print(json.dumps({"ok": False, "error": "SPEC_MISSING", "answers": []}))
    raise SystemExit(0)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
try:
    spec.loader.exec_module(module)
except BaseException as error:
    print(json.dumps({"ok": False, "error": "IMPORT_%s" % type(error).__name__,
                      "answers": []}))
    raise SystemExit(0)
for job in payload["jobs"]:
    target = module
    for part in job["symbol"].split("."):
        target = getattr(target, part, None)
        if target is None:
            break
    if not callable(target):
        answers.append({"id": job["id"], "ok": False, "error": "SYMBOL_MISSING"})
        continue
    try:
        value = target(*job["args"])
    except BaseException as error:
        answers.append({"id": job["id"], "ok": False,
                        "error": type(error).__name__})
        continue
    try:
        json.dumps(value)
    except (TypeError, ValueError):
        answers.append({"id": job["id"], "ok": False, "error": "UNSERIALISABLE"})
        continue
    answers.append({"id": job["id"], "ok": True, "value": value})
print(json.dumps({"ok": True, "error": "", "answers": answers}))
"""


def def_module_probe_batch(
    root: Path,
    relative_path: str,
    jobs: Sequence[Mapping[str, Any]],
    timeout: int = PARAM_MODULE_TIMEOUT_SECONDS,
) -> dict[str, dict[str, Any]]:
    """模組級隔離探測：一個檔案一個子行程，import 一次跑完該檔所有 job。

    受限沙箱擋掉的函式（有 import、有裝飾器、要第三方套件）在這裡還有一次機會，
    代價是**真的 import 該模組**（會執行它的 module-level 程式碼），所以：
      * 預設關閉，要 `--allow-module-exec` 才啟用；
      * 子行程獨立、`VIA_NET=0`／`VIA_LIVE=0`、有逾時與輸出上限；
      * 每個檔案只付一次 Python 啟動與 import 成本（不是每個探針一個行程）。
    回傳 job id → {"ok", "value"／"error"}。
    """
    if not jobs:
        return {}
    if len(jobs) > PARAM_MODULE_JOB_LIMIT:
        raise def_EngineError(f"模組探測 job 超過上限 {PARAM_MODULE_JOB_LIMIT}")
    resolved = def_assert_inside_root(Path(root), Path(root) / relative_path)
    if resolved.is_symlink() or not resolved.is_file():
        return {str(job["id"]): {"ok": False, "error": "SOURCE_MISSING"} for job in jobs}
    payload = {
        "path": str(resolved),
        "jobs": [
            {"id": str(job["id"]), "symbol": str(job["symbol"]), "args": list(job["args"])}
            for job in jobs
        ],
    }
    environment = dict(os.environ)
    environment.update({
        "VIA_NET": "0", "VIA_LIVE": "0", "VIA_OPEN_ATTACH": "0",
        "PYTHONNOUSERSITE": "1", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1",
    })
    try:
        completed = subprocess.run(
            [sys.executable, "-I", "-c", PARAM_MODULE_BOOTSTRAP],
            input=def_compact_json(payload),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            cwd=str(Path(root).resolve()),
            env=environment,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {str(job["id"]): {"ok": False, "error": "TIMEOUT"} for job in jobs}
    except OSError as error:
        return {
            str(job["id"]): {"ok": False, "error": f"SPAWN_{error.__class__.__name__}"}
            for job in jobs
        }
    text = (completed.stdout or "")[-PARAM_MODULE_OUTPUT_LIMIT:]
    line = next(
        (item for item in reversed(text.splitlines()) if item.strip().startswith("{")),
        "",
    )
    try:
        answer = json.loads(line) if line else {}
    except ValueError:
        answer = {}
    if not answer.get("ok"):
        reason = str(answer.get("error") or "NO_OUTPUT")
        return {str(job["id"]): {"ok": False, "error": reason} for job in jobs}
    results = {str(item.get("id")): dict(item) for item in answer.get("answers", [])}
    return {
        str(job["id"]): results.get(str(job["id"]), {"ok": False, "error": "NO_ANSWER"})
        for job in jobs
    }


def def_test_capability(
    plan: def_Plan, capability: def_Capability
) -> def_TestOutcome:
    """對 default variant 找到可用探針即 PASS；其餘 variant 做影子對照。"""
    default = capability.variant_of(capability.default_variant)
    candidates = [
        variant for variant in capability.variants if variant.executable
    ]
    coverage = (
        100.0 * len(candidates) / len(capability.variants) if capability.variants else 0.0
    )
    if not candidates:
        reasons = sorted(
            {
                record.skip_reason
                for variant in capability.variants
                for record in plan.records_by_fingerprint(variant.fingerprint)
                if record.skip_reason
            }
        )
        return def_TestOutcome(
            capability=capability.capability,
            status="SKIPPED",
            probe="",
            arguments="",
            result="",
            equivalent=(),
            divergent=(),
            detail=def_bounded_text("沙箱拒絕：" + ",".join(reasons or ["unknown"]), 160),
            coverage_percent=round(coverage, 2),
        )
    primary = default if default.executable else candidates[0]
    primary_record = plan.records_by_fingerprint(primary.fingerprint)[0]
    chosen: tuple[str, tuple[Any, ...]] | None = None
    value: Any = None
    failures: list[str] = []
    for probe_name, vector in def_probe_candidates(primary_record):
        try:
            value = def_execute_guarded(primary_record.source, primary_record.name, vector)
        except def_ExecutionBudgetError as error:
            failures.append(f"{probe_name}:budget")
            continue
        except Exception as error:  # noqa: BLE001 - 探針失敗是資料，不是引擎錯誤
            failures.append(f"{probe_name}:{error.__class__.__name__}")
            continue
        chosen = (probe_name, vector)
        break
    if chosen is None:
        return def_TestOutcome(
            capability=capability.capability,
            status="SKIPPED",
            probe="",
            arguments="",
            result="",
            equivalent=(),
            divergent=(),
            detail=def_bounded_text("無可用探針：" + ",".join(failures[:6]), 160),
            coverage_percent=round(coverage, 2),
        )
    probe_name, vector = chosen
    equivalent: list[str] = [primary.variant]
    divergent: list[str] = []
    for variant in candidates:
        if variant.variant == primary.variant:
            continue
        record = plan.records_by_fingerprint(variant.fingerprint)[0]
        try:
            shadow = def_execute_guarded(record.source, record.name, vector)
        except Exception:  # noqa: BLE001 - 影子跑不起來就不算等價
            divergent.append(variant.variant)
            continue
        if def_values_equal(value, shadow):
            equivalent.append(variant.variant)
        else:
            divergent.append(variant.variant)
    # 穩定度在這裡量：同一組輸入重跑，結果不一致或丟例外就記一次失敗。
    run_failures = 0
    for index in range(PARAM_STABILITY_RUNS):
        try:
            repeat = def_execute_guarded(primary_record.source, primary_record.name, vector)
        except Exception:  # noqa: BLE001 - 重跑失敗是穩定度證據
            run_failures += 1
            continue
        if not def_values_equal(value, repeat):
            run_failures += 1
    return def_TestOutcome(
        capability=capability.capability,
        status="PASS",
        probe=probe_name,
        arguments=def_bounded_text(def_compact_json(list(vector)), PARAM_RESULT_LIMIT),
        result=def_bounded_text(def_compact_json(value), PARAM_RESULT_LIMIT),
        equivalent=tuple(equivalent),
        divergent=tuple(divergent),
        detail=f"探針 {probe_name}；影子等價 {len(equivalent)}／分歧 {len(divergent)}",
        gate=PARAM_SANDBOX_GATE,
        runs=PARAM_STABILITY_RUNS,
        run_failures=run_failures,
        coverage_percent=round(coverage, 2),
    )


def def_module_test_capability(
    plan: def_Plan,
    capability: def_Capability,
    answers: Mapping[str, dict[str, Any]],
) -> def_TestOutcome | None:
    """把一批模組級探測結果收斂成該能力的測試結論；沒有成功的探針就回 None。"""
    variants = [
        variant for variant in capability.variants
        if any(
            record.module_executable
            for record in plan.records_by_fingerprint(variant.fingerprint)
        )
    ]
    if not variants:
        return None
    primary = variants[0]
    for probe_name, vector in PARAM_PROBE_VECTORS:
        key = f"{capability.capability}|{primary.variant}|{probe_name}|0"
        answer = answers.get(key)
        if answer is None or not answer.get("ok"):
            continue
        value = answer.get("value")
        run_failures = 0
        runs = 0
        for index in range(1, PARAM_STABILITY_RUNS + 1):
            repeat = answers.get(
                f"{capability.capability}|{primary.variant}|{probe_name}|{index}"
            )
            if repeat is None:
                continue
            runs += 1
            if not repeat.get("ok") or not def_values_equal(value, repeat.get("value")):
                run_failures += 1
        equivalent = [primary.variant]
        divergent: list[str] = []
        for variant in variants[1:]:
            shadow = answers.get(
                f"{capability.capability}|{variant.variant}|{probe_name}|0"
            )
            if shadow is None:
                continue
            if shadow.get("ok") and def_values_equal(value, shadow.get("value")):
                equivalent.append(variant.variant)
            else:
                divergent.append(variant.variant)
        coverage = 100.0 * len(variants) / len(capability.variants)
        return def_TestOutcome(
            capability=capability.capability,
            status="PASS",
            probe=probe_name,
            arguments=def_bounded_text(def_compact_json(list(vector)), PARAM_RESULT_LIMIT),
            result=def_bounded_text(def_compact_json(value), PARAM_RESULT_LIMIT),
            equivalent=tuple(equivalent),
            divergent=tuple(divergent),
            detail=(
                f"模組級隔離探針 {probe_name}；影子等價 {len(equivalent)}"
                f"／分歧 {len(divergent)}"
            ),
            gate=PARAM_MODULE_GATE,
            runs=runs,
            run_failures=run_failures,
            coverage_percent=round(coverage, 2),
        )
    return None


def def_module_test_plan(
    plan: def_Plan,
    outcomes: Mapping[str, def_TestOutcome],
    root: Path,
) -> tuple[dict[str, def_TestOutcome], dict[str, Any]]:
    """對沙箱沒過的能力做模組級隔離補測；一個來源檔一個子行程。"""
    pending = [
        capability for capability_id, capability in sorted(plan.capabilities.items())
        if outcomes.get(capability_id) is None
        or outcomes[capability_id].status != "PASS"
    ]
    jobs_by_file: dict[str, list[dict[str, Any]]] = defaultdict(list)
    owner: dict[str, str] = {}
    for capability in pending:
        for variant in capability.variants:
            records = [
                record for record in plan.records_by_fingerprint(variant.fingerprint)
                if record.module_executable
            ]
            if not records:
                continue
            record = sorted(records, key=lambda item: (item.path, item.lineno))[0]
            owner[f"{capability.capability}|{variant.variant}"] = record.path
            for probe_name, vector in PARAM_PROBE_VECTORS:
                if len(vector) != record.arity:
                    continue
                repeats = (
                    PARAM_STABILITY_RUNS + 1
                    if variant.variant == capability.variants[0].variant
                    else 1
                )
                for index in range(repeats):
                    jobs_by_file[record.path].append({
                        "id": f"{capability.capability}|{variant.variant}|{probe_name}|{index}",
                        "symbol": record.qualname,
                        "args": list(vector),
                    })
    answers: dict[str, dict[str, Any]] = {}
    statistics = {
        "files": 0, "jobs": 0, "batches": 0, "import_failures": 0,
        "candidates": len(jobs_by_file),
    }
    for path in sorted(jobs_by_file):
        jobs = sorted(jobs_by_file[path], key=lambda job: job["id"])
        statistics["files"] += 1
        statistics["jobs"] += len(jobs)
        # 超過單批上限就分批，不截斷：截斷等於靜默漏測。
        failed_import = False
        for offset in range(0, len(jobs), PARAM_MODULE_JOB_LIMIT):
            chunk = jobs[offset:offset + PARAM_MODULE_JOB_LIMIT]
            statistics["batches"] += 1
            batch = def_module_probe_batch(root, path, chunk)
            if batch and all(
                not item.get("ok") and str(item.get("error", "")).startswith("IMPORT_")
                for item in batch.values()
            ):
                failed_import = True
            answers.update(batch)
        if failed_import:
            statistics["import_failures"] += 1
    upgraded: dict[str, def_TestOutcome] = {}
    for capability in pending:
        outcome = def_module_test_capability(plan, capability, answers)
        if outcome is not None:
            upgraded[capability.capability] = outcome
    statistics["upgraded"] = len(upgraded)
    return upgraded, statistics


def def_test_plan(
    plan: def_Plan,
    root: Path | None = None,
    allow_module_exec: bool = False,
) -> tuple[dict[str, def_TestOutcome], dict[str, Any]]:
    """沙箱測試全部能力；`allow_module_exec` 時對沒過的再做模組級隔離補測。

    回傳 (outcomes, module 統計)。模組級補測預設關閉，因為它會真的 import 來源模組。
    """
    outcomes = {
        capability_id: def_test_capability(plan, capability)
        for capability_id, capability in sorted(plan.capabilities.items())
    }
    module_statistics: dict[str, Any] = {
        "enabled": bool(allow_module_exec and root is not None),
        "gate": PARAM_MODULE_GATE,
        "upgraded": 0,
        "candidates": sum(
            1 for capability_id, capability in plan.capabilities.items()
            if outcomes[capability_id].status != "PASS"
            and any(
                record.module_executable
                for variant in capability.variants
                for record in plan.records_by_fingerprint(variant.fingerprint)
            )
        ),
    }
    if allow_module_exec and root is not None:
        upgraded, statistics = def_module_test_plan(plan, outcomes, Path(root))
        outcomes.update(upgraded)
        module_statistics.update(statistics)
        module_statistics["enabled"] = True
    return outcomes, module_statistics


# --------------------------------------------------------------------------
# 7. 封印：測試成功才鎖住，已封印永不解封
# --------------------------------------------------------------------------
def def_engine_id_for(capability: str, variant: str) -> str:
    return f"E-{capability.replace('.', '-').replace('_', '-').upper()}-{variant.upper()}"

# --------------------------------------------------------------------------
# 7B. 沙盒證據、引擎鎖與能力抽象（PEIS EngineLocker／CapabilityExtractor）
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class def_VerificationEvidence:
    """沙盒驗證與性能基準證據。PEIS 只消費證據，不自行捏造分數。"""

    sandbox_gate: str
    ast_pass: bool
    tests_total: int
    tests_passed: int
    coverage_percent: float
    stability_runs: int
    stability_failures: int
    benchmark_score: float

    @staticmethod
    def def_from_dict(payload: dict[str, Any]) -> "def_VerificationEvidence":
        missing = [
            key for key in (
                "sandbox_gate", "ast_pass", "tests_total", "tests_passed",
                "coverage_percent", "stability_runs", "stability_failures",
                "benchmark_score",
            )
            if key not in payload
        ]
        if missing:
            raise def_LockRefused(f"驗證證據缺少欄位：{sorted(missing)}")
        return def_VerificationEvidence(
            sandbox_gate=str(payload["sandbox_gate"]),
            ast_pass=bool(payload["ast_pass"]),
            tests_total=int(payload["tests_total"]),
            tests_passed=int(payload["tests_passed"]),
            coverage_percent=float(payload["coverage_percent"]),
            stability_runs=int(payload["stability_runs"]),
            stability_failures=int(payload["stability_failures"]),
            benchmark_score=float(payload["benchmark_score"]),
        )

    def def_correctness(self) -> float:
        if self.tests_total <= 0:
            return 0.0
        return max(0.0, min(1.0, self.tests_passed / self.tests_total))

    def def_stability(self) -> float:
        if self.stability_runs <= 0:
            return 0.0
        survived = self.stability_runs - self.stability_failures
        return max(0.0, min(1.0, survived / self.stability_runs))

    def def_coverage(self) -> float:
        return max(0.0, min(1.0, self.coverage_percent / 100.0))

    def def_performance(self) -> float:
        """性能分數 = 0.40 正確性 + 0.30 覆蓋率 + 0.20 穩定度 + 0.10 基準分。"""
        score = (
            0.40 * self.def_correctness()
            + 0.30 * self.def_coverage()
            + 0.20 * self.def_stability()
            + 0.10 * max(0.0, min(1.0, self.benchmark_score))
        )
        return round(score, 2)

    def def_gate(self, thresholds: dict[str, float]) -> tuple[bool, tuple[str, ...]]:
        reasons: list[str] = []
        if not self.sandbox_gate:
            reasons.append("缺少沙盒 gate 名稱")
        if not self.ast_pass:
            reasons.append("AST 未通過")
        if self.tests_total <= 0:
            reasons.append("沒有任何測試證據")
        elif self.tests_passed != self.tests_total:
            reasons.append(f"測試未全綠 {self.tests_passed}/{self.tests_total}")
        if self.coverage_percent < thresholds["coverage_floor_percent"]:
            reasons.append(
                f"覆蓋率 {self.coverage_percent} < {thresholds['coverage_floor_percent']}"
            )
        if self.def_stability() < thresholds["stability_floor"]:
            reasons.append(f"穩定度 {self.def_stability():.2f} < {thresholds['stability_floor']}")
        if self.def_performance() < thresholds["performance_floor"]:
            reasons.append(f"性能分數 {self.def_performance()} < {thresholds['performance_floor']}")
        return (not reasons, tuple(reasons))


@dataclass(frozen=True)
class def_EngineLock:
    engine_id: str
    locked: bool
    version: str
    capability: str
    performance: float
    stability: float
    strategy: str
    source_path: str
    sha256: str
    entrypoint: str
    functions: tuple[str, ...]
    evidence: dict[str, Any]
    lock_seal: str

    def def_standard_output(self) -> dict[str, Any]:
        """規範輸出：engine_id / locked / version / capability / performance。"""
        payload = {
            "engine_id": self.engine_id,
            "locked": self.locked,
            "version": self.version,
            "capability": self.capability,
            "performance": self.performance,
        }
        return {key: payload[key] for key in PARAM_STANDARD_LOCK_KEYS}

    def def_pool_record(self) -> dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "version": self.version,
            "performance": self.performance,
            "stability": self.stability,
            "strategy": self.strategy,
            "source_path": self.source_path,
            "sha256": self.sha256,
            "entrypoint": self.entrypoint,
            "functions": list(self.functions),
            "locked": self.locked,
            "lock_seal": self.lock_seal,
            "evidence": dict(sorted(self.evidence.items())),
        }


def def_lock_seal(engine_id: str, version: str, sha256: str, performance: float) -> str:
    """鎖封印：凍結「引擎身份 + 版本 + 內容雜湊 + 性能分數」的決定性指紋。"""
    material = f"{PARAM_ENGINE_ID}|{engine_id}|{version}|{sha256}|{performance:.2f}"
    return hashlib.blake2b(material.encode("utf-8"), digest_size=16).hexdigest()


def def_lock_engine(
    root: Path,
    source_path: str,
    engine_id: str,
    version: str,
    evidence: def_VerificationEvidence | dict[str, Any],
    entrypoint_symbol: str | None = None,
    strategy: str = "best-performance",
    thresholds: dict[str, float] | None = None,
    capability: str | None = None,
    functions: Sequence[str] | None = None,
) -> def_EngineLock:
    """模組 1 EngineLocker：通過沙盒驗證與性能基準才鎖定，否則 fail-closed。

    `functions` 省略時宣告整個來源檔的公開符號（PEIS 原本的「一檔一引擎」granularity）；
    統一引擎的自動鎖定會傳入該能力實際擁有的函式，否則同一個檔案裡的多個能力
    會互相宣告對方的函式，在全景分析被判成 FUNCTION_OWNERSHIP_DRIFT。
    """
    limits = dict(PARAM_DEFAULT_THRESHOLDS if thresholds is None else thresholds)
    record = (
        evidence
        if isinstance(evidence, def_VerificationEvidence)
        else def_VerificationEvidence.def_from_dict(evidence)
    )
    passed, reasons = record.def_gate(limits)
    if not passed:
        raise def_LockRefused(f"{engine_id} 未通過鎖定條件：{'；'.join(reasons)}")
    candidate = def_scan_engine_file(root, root / source_path)
    if candidate.ast_status != "PASS":
        raise def_LockRefused(f"{engine_id} AST 失敗：{candidate.ast_error}")
    if not candidate.symbols:
        raise def_LockRefused(f"{engine_id} 沒有可截取的公開函式")
    symbol = entrypoint_symbol or candidate.symbols[0]
    if symbol not in candidate.symbols:
        raise def_LockRefused(f"{engine_id} entrypoint 不存在：{symbol}")
    performance = record.def_performance()
    resolved_capability = capability or def_extract_capability(candidate.symbols)
    if resolved_capability == PARAM_UNCLASSIFIED:
        raise def_LockRefused(
            f"{engine_id} 的函式無法對應任何 SSOT 能力；請先登錄字典或以 --capability 指定"
        )
    return def_EngineLock(
        engine_id=engine_id,
        locked=True,
        version=version,
        capability=resolved_capability,
        performance=performance,
        stability=round(record.def_stability(), 2),
        strategy=strategy,
        source_path=candidate.source_path,
        sha256=candidate.sha256,
        entrypoint=f"{candidate.source_path}#{symbol}",
        functions=(
            tuple(sorted({def_normalize_symbol(name) for name in functions}))
            if functions is not None
            else candidate.normalized
        ),
        evidence=asdict(record),
        lock_seal=def_lock_seal(engine_id, version, candidate.sha256, performance),
    )


# ---------------------------------------------------------------------------
# CapabilityExtractor
# ---------------------------------------------------------------------------


def def_extract_capability(symbols: Sequence[str], index: dict[str, str] | None = None) -> str:
    """模組 2 CapabilityExtractor：把一組函式聚類抽象成單一能力名稱。

    未分類符號不參與投票；整組都未分類時才回傳 `unclassified`。
    """
    if not symbols:
        return PARAM_UNCLASSIFIED
    normalized = sorted({def_normalize_symbol(symbol) for symbol in symbols})
    counts: dict[str, int] = {}
    for name in normalized:
        capability = def_capability_for_symbol(name, index)
        if capability == PARAM_UNCLASSIFIED:
            continue
        counts[capability] = counts.get(capability, 0) + 1
    if not counts:
        return PARAM_UNCLASSIFIED
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


def def_extract_capabilities(
    candidates: Sequence[def_EngineCandidate],
    index: dict[str, str] | None = None,
) -> dict[str, tuple[str, ...]]:
    """語義化去重：全庫函式 → 正規化名稱 → 能力分組（能力名稱 → 函式集合）。"""
    grouped: dict[str, set[str]] = {}
    for candidate in candidates:
        for name in candidate.normalized:
            grouped.setdefault(def_capability_for_symbol(name, index), set()).add(name)
    return {capability: tuple(sorted(names)) for capability, names in sorted(grouped.items())}


def def_dominant_token(names: Sequence[str]) -> str:
    """候選能力命名：取群組內出現最多次的強 token（決定性 tie-break）。"""
    counts: dict[str, int] = {}
    for name in names:
        for token in def_tokenize(name):
            if token in PARAM_WEAK_TOKENS or token.isdigit():
                continue
            counts[token] = counts.get(token, 0) + 1
    if not counts:
        return PARAM_UNCLASSIFIED
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


# ---------------------------------------------------------------------------
# CME v2.0 能力表
# ---------------------------------------------------------------------------


def def_abstract_capabilities(
    document: dict[str, Any],
    clusters: dict[str, Sequence[str]],
    thresholds: dict[str, float] | None = None,
) -> tuple[def_CapabilityProposal, ...]:
    """步驟 6 CapabilityAbstractor：判斷新增全新能力或擴充既有能力。"""
    limits = dict(PARAM_DEFAULT_THRESHOLDS if thresholds is None else thresholds)
    existing = {
        record["capability"]: def_capability_centroid(record)
        for record in document.get("capabilities", [])
    }
    proposals: list[def_CapabilityProposal] = []
    for label, members in sorted(clusters.items()):
        base = def_cluster_base(label)
        centroid = def_centroid([def_embed(name) for name in members])
        best_name, best_score = "", 0.0
        for capability, vector in sorted(existing.items()):
            score = round(def_cosine(centroid, vector), PARAM_SIMILARITY_PRECISION)
            if score > best_score:
                best_name, best_score = capability, score
        if base == PARAM_UNCLASSIFIED:
            if best_name and best_score >= limits["abstraction_threshold"]:
                proposals.append(def_CapabilityProposal(
                    capability=best_name,
                    action="EXTEND_CAPABILITY",
                    cluster=label,
                    functions=tuple(sorted(members)),
                    similarity=best_score,
                ))
            elif len(members) >= PARAM_CANDIDATE_CLUSTER_MIN:
                proposals.append(def_CapabilityProposal(
                    capability=def_dominant_token(members),
                    action="CANDIDATE_CAPABILITY",
                    cluster=label,
                    functions=tuple(sorted(members)),
                    similarity=best_score,
                ))
            continue
        if base in existing:
            proposals.append(def_CapabilityProposal(
                capability=base,
                action="EXTEND_CAPABILITY",
                cluster=label,
                functions=tuple(sorted(members)),
                similarity=round(def_cosine(centroid, existing[base]), PARAM_SIMILARITY_PRECISION),
            ))
        elif best_name and best_score >= limits["abstraction_threshold"]:
            proposals.append(def_CapabilityProposal(
                capability=best_name,
                action="EXTEND_CAPABILITY",
                cluster=label,
                functions=tuple(sorted(members)),
                similarity=best_score,
            ))
        else:
            proposals.append(def_CapabilityProposal(
                capability=base,
                action="NEW_CAPABILITY",
                cluster=label,
                functions=tuple(sorted(members)),
                similarity=best_score,
            ))
    return tuple(proposals)



def def_lock_plan(
    plan: def_Plan,
    outcomes: Mapping[str, def_TestOutcome],
    previous: Sequence[def_LockEntry] | None = None,
    stamp: str | None = None,
) -> list[def_LockEntry]:
    sealed_before = {
        entry.capability: entry
        for entry in (previous or ())
        if entry.status == "SEALED"
    }
    moment = stamp or def_iso_now()
    entries: list[def_LockEntry] = []
    seen: set[str] = set()
    for capability_id, capability in sorted(plan.capabilities.items()):
        seen.add(capability_id)
        earlier = sealed_before.get(capability_id)
        if earlier is not None:
            entries.append(earlier)
            continue
        outcome = outcomes.get(capability_id)
        passed = outcome is not None and outcome.status == "PASS"
        variant_id = capability.default_variant
        if passed and outcome is not None and outcome.equivalent:
            variant_id = outcome.equivalent[0]
        variant = capability.variant_of(variant_id)
        entries.append(
            def_LockEntry(
                capability=capability_id,
                engine_id=def_engine_id_for(capability_id, variant.variant),
                status="SEALED" if passed else "PENDING",
                variant=variant.variant,
                fingerprint=variant.fingerprint,
                kind="vendor" if variant.vendorable else "reference",
                sealed_at=moment if passed else "",
            )
        )
    for capability_id, earlier in sorted(sealed_before.items()):
        if capability_id not in seen:
            entries.append(
                def_LockEntry(
                    capability=earlier.capability,
                    engine_id=earlier.engine_id,
                    status="DORMANT",
                    variant=earlier.variant,
                    fingerprint=earlier.fingerprint,
                    kind=earlier.kind,
                    sealed_at=earlier.sealed_at,
                )
            )
    return entries


# --------------------------------------------------------------------------
# 8. 標註：能力卡與 capsule（AI 只讀卡，不讀全文）
# --------------------------------------------------------------------------
def def_capability_card(
    plan: def_Plan,
    capability: def_Capability,
    outcome: def_TestOutcome | None,
    lock: def_LockEntry,
    audience: str = "governance",
) -> dict[str, Any]:
    """能力卡。

    `audience="upstream"`（對 AI）遵守 PEIS 黑盒原則：不帶引擎 id、指紋或原始碼位置，
    只留呼叫能力真正需要的欄位，並由 `def_assert_blackbox` 把關。
    `audience="governance"`（對操作者／稽核）才帶 eng／fp／at，供 reference-first 追查。
    """
    if audience not in PARAM_AUDIENCES:
        raise def_EngineError(f"未知 audience：{audience}")
    canonical = plan.records_by_fingerprint(lock.fingerprint)
    if not canonical:
        raise def_EngineError(f"封印指紋沒有對應記錄：{lock.capability}")
    record = sorted(canonical, key=lambda item: (item.path, item.lineno))[0]
    body_tokens = sum(
        member.body_tokens
        for member in plan.records
        if member.capability == capability.capability
    )
    card: dict[str, Any] = {"cap": capability.capability, "st": lock.status}
    domain = def_capability_for_symbol(def_normalize_symbol(record.name))
    if domain != PARAM_UNCLASSIFIED:
        card["dom"] = domain
    if audience == "governance":
        card["eng"] = lock.engine_id
        card["fp"] = lock.fingerprint[:16]
    card["sig"] = record.signature
    if audience == "governance":
        card["at"] = record.anchor
    # 空欄位一律省略：卡片每一個 token 都要換得到資訊。
    if record.returns:
        card["ret"] = record.returns
    if record.doc:
        card["doc"] = record.doc
    if record.tools:
        card["tools"] = list(record.tools)
    if record.risks:
        card["risk"] = list(record.risks)
    if len(capability.variants) > 1:
        card["alt"] = len(capability.variants)
    if capability.collapsed:
        card["dup"] = capability.collapsed
    if outcome is not None and outcome.status == "PASS":
        card["test"] = {
            "probe": outcome.probe,
            "in": outcome.arguments,
            "out": outcome.result,
            "eqv": len(outcome.equivalent),
            "div": len(outcome.divergent),
        }
    else:
        card["test"] = {
            "probe": "",
            "status": outcome.status if outcome else "SKIPPED",
            "why": outcome.detail if outcome else "",
        }
    card["tok"] = {"body": body_tokens, "card": def_token_estimate(def_compact_json(card))}
    return card


def def_redact_for_upstream(
    card: Mapping[str, Any], private_values: Sequence[str] = ()
) -> dict[str, Any]:
    """upstream 卡片消毒。

    模組級隔離探測會回傳**真實物件**：`def_plugin_manifest` 的探針輸出就含
    `engine/via_unified_engine.py` 與 engine_id。這在對上游的卡片上就是洩漏，
    所以命中私有字串或洩漏欄位名的探針輸入／輸出／說明一律換成形狀描述，
    而不是整張卡丟掉——AI 仍拿得到簽章與能力名稱，只是看不到那個值。
    """
    clean = {
        key: value for key, value in card.items()
        if key not in ("eng", "fp", "at")
    }

    def def_tainted(text: str) -> bool:
        if any(value and value in text for value in private_values):
            return True
        return any(field in text for field in PARAM_LEAK_FIELDS)

    if isinstance(clean.get("doc"), str) and def_tainted(clean["doc"]):
        clean["doc"] = "<redacted>"
    test = dict(clean.get("test") or {})
    for key in ("in", "out"):
        text = test.get(key)
        if isinstance(text, str) and def_tainted(text):
            test[key] = f"<redacted:{len(text)}chars>"
            test["redacted"] = True
    if test:
        clean["test"] = test
    return clean


def def_capability_cards(
    plan: def_Plan,
    outcomes: Mapping[str, def_TestOutcome],
    locks: Sequence[def_LockEntry],
    audience: str = "governance",
) -> list[dict[str, Any]]:
    """所有能力卡，已封印優先、節省越多越前面（DORMANT 不發卡）。"""
    cards: list[dict[str, Any]] = []
    for lock in locks:
        if lock.status == "DORMANT":
            continue
        capability = plan.capabilities.get(lock.capability)
        if capability is None:
            continue
        cards.append(
            def_capability_card(
                plan, capability, outcomes.get(lock.capability), lock, audience
            )
        )
    cards.sort(
        key=lambda card: (
            0 if card["st"] == "SEALED" else 1,
            -(card["tok"]["body"] - card["tok"]["card"]),
            card["cap"],
        )
    )
    return cards


def def_capability_delta(
    cards: Sequence[Mapping[str, Any]],
    baseline: Mapping[str, Mapping[str, str]],
) -> dict[str, Any]:
    """比對本次卡片與上次交棒基線，分成 new／changed／same／retired。

    這就是 `REFERENCE_FIRST_DELTA_ONLY` 真正的 delta：同一個 AI 第二次要能力時，
    沒變的能力只值一行 digest，不值一張卡。
    """
    new: list[str] = []
    changed: list[str] = []
    same: list[str] = []
    for card in cards:
        capability = str(card["cap"])
        previous = baseline.get(capability)
        if previous is None:
            new.append(capability)
            continue
        if def_sha256_text(def_compact_json(card)) == previous.get("sha"):
            same.append(capability)
        else:
            changed.append(capability)
    retired = sorted(set(baseline) - {str(card["cap"]) for card in cards})
    digest_material = "|".join(
        f"{capability}:{baseline[capability].get('sha', '')}" for capability in sorted(same)
    )
    return {
        "new": sorted(new),
        "changed": sorted(changed),
        "same": sorted(same),
        "retired": retired,
        "digest": def_sha256_text(digest_material)[:16] if same else "",
    }


def def_capability_capsule(
    plan: def_Plan,
    outcomes: Mapping[str, def_TestOutcome],
    locks: Sequence[def_LockEntry],
    policy: Mapping[str, Any] | None = None,
    budget_tokens: int | None = None,
    cards: Sequence[Mapping[str, Any]] | None = None,
    audience: str = "governance",
    document: Mapping[str, Any] | None = None,
    baseline: Mapping[str, Mapping[str, str]] | None = None,
    handoff: str | None = None,
) -> dict[str, Any]:
    """組出 REFERENCE_FIRST_DELTA_ONLY 能力 capsule，並附 token 節省帳。

    卡片完整清單留在能力庫（本機、零 token 成本）；capsule 只帶上限內的子集。
    """
    active = policy or def_capsule_policy()
    max_items = int(active.get("max_items", PARAM_CAPSULE_MAX_ITEMS))
    max_chars = int(active.get("max_chars", PARAM_CAPSULE_MAX_CHARS))
    if audience not in PARAM_AUDIENCES:
        raise def_EngineError(f"未知 audience：{audience}")
    cards = (
        list(cards) if cards is not None
        else def_capability_cards(plan, outcomes, locks, audience)
    )
    if audience == "upstream":
        private = def_collect_private_values(dict(document or {}))
        cards = [def_redact_for_upstream(card, private) for card in cards]
    full_cards = list(cards)
    delta: dict[str, Any] | None = None
    if baseline is not None:
        delta = def_capability_delta(full_cards, baseline)
        # 只送新增與變更；沒變的留在 digest 裡，退役的只給名字。
        emit = set(delta["new"]) | set(delta["changed"])
        cards = [card for card in full_cards if str(card["cap"]) in emit]
    total_cards = len(cards)
    selected: list[dict[str, Any]] = []
    used_chars = 0
    used_tokens = 0
    truncated_reason = ""
    for card in cards:
        if len(selected) >= max_items:
            truncated_reason = "max_items"
            break
        encoded = len(def_compact_json(card))
        if used_chars + encoded > max_chars:
            truncated_reason = "max_chars"
            break
        if budget_tokens is not None and used_tokens + card["tok"]["card"] > budget_tokens:
            truncated_reason = "budget_tokens"
            break
        selected.append(card)
        used_chars += encoded
        used_tokens += card["tok"]["card"]
    risk_codes = sorted({code for card in selected for code in (card.get("risk") or [])})
    source_tokens = sum(record.body_tokens for record in plan.records)
    sealed_capabilities = {
        lock.capability for lock in locks if lock.status == "SEALED"
    }
    sealed_source_tokens = sum(
        record.body_tokens
        for record in plan.records
        if record.capability in sealed_capabilities
    )
    capsule: dict[str, Any] = {
        "schema": PARAM_CAPSULE_SCHEMA,
        "schema_version": "1.0.0",
        "audience": audience,
        "policy": {
            "protocol": active.get("protocol", PARAM_CAPSULE_PROTOCOL),
            "max_chars": max_chars,
            "max_items": max_items,
            "source": active.get("source", "engine-default"),
        },
        "load_order": list(PARAM_CAPSULE_LOAD_ORDER),
        "legend": {
            key: value for key, value in PARAM_CARD_LEGEND.items()
            if audience == "governance" or key not in ("eng", "fp", "at")
        },
        "risk_legend": {
            code: {"level": PARAM_RISK_TABLE[code][0], "why": PARAM_RISK_TABLE[code][1]}
            for code in risk_codes
            if code in PARAM_RISK_TABLE
        },
        "counts": {
            "cards_known": len(full_cards),
            "files": plan.intake.get("files", 0),
            "functions": len(plan.records),
            "capabilities": len(plan.capabilities),
            "sealed": len(sealed_capabilities),
            "pending": sum(1 for lock in locks if lock.status == "PENDING"),
            "dormant": sum(1 for lock in locks if lock.status == "DORMANT"),
            "collapsed": plan.collapsed,
            "near_duplicates": plan.near_duplicates,
            "cards_total": total_cards,
            "cards_emitted": len(selected),
        },
        # 黑盒：對上游只給 envelope 與介面，不給引擎檔案路徑（那是 source_path 洩漏）。
        "call": {
            "envelope": {
                "p": PARAM_PROTOCOL,
                "c": "<cap>",
                "a": "RUN",
                "r": "RESULT_ONLY",
            },
            "interface": "RUN(capability, params)",
            "rule": "只有 SEALED 能力可 RUN；PENDING 一律拒絕",
            **(
                {"command": f"python {PARAM_ENGINE_RELATIVE} run --capability <cap> --args '[...]'"}
                if audience == "governance" else {}
            ),
        },
        "cards": selected,
    }
    if delta is not None:
        capsule["delta"] = {
            "protocol": PARAM_CAPSULE_PROTOCOL,
            "handoff": handoff or PARAM_DEFAULT_HANDOFF,
            "new": delta["new"],
            "changed": delta["changed"],
            "retired": delta["retired"],
            "unchanged": {"count": len(delta["same"]), "digest": delta["digest"]},
            "rule": "沒列在 new／changed 的能力＝上次那張卡仍然有效",
        }
    if audience == "governance":
        capsule["engine"] = {
            "id": PARAM_ENGINE_ID,
            "name": PARAM_ENGINE_NAME,
            "version": PARAM_ENGINE_VERSION,
            "protocol": PARAM_PROTOCOL,
            "mode": plan.mode,
        }
    else:
        capsule["protocol"] = PARAM_PROTOCOL
        capsule["cme_version"] = PARAM_CME_VERSION
    if truncated_reason:
        capsule["truncated"] = {
            "reason": truncated_reason,
            "omitted": total_cards - len(selected),
        }
    card_tokens = sum(int(card["tok"]["card"]) for card in selected)
    full_card_tokens = sum(int(card["tok"]["card"]) for card in full_cards)
    ledger_placeholder = {
        "estimator": PARAM_TOKEN_ESTIMATOR,
        "source_tokens": source_tokens,
        "sealed_source_tokens": sealed_source_tokens,
        "card_tokens": card_tokens,
        "known_card_tokens": full_card_tokens,
        "header_tokens": 0,
        "capsule_tokens": 0,
        "saved_tokens": 0,
        "saved_percent": 0.0,
        "note": "capsule_tokens 於填入前估算，誤差 ≤ 3 token；header 為固定成本，語料越大越攤平",
    }
    capsule["token_ledger"] = ledger_placeholder
    capsule_tokens = def_token_estimate(def_compact_json(capsule))
    saved = source_tokens - capsule_tokens
    capsule["token_ledger"] = {
        **ledger_placeholder,
        "header_tokens": max(0, capsule_tokens - card_tokens),
        "capsule_tokens": capsule_tokens,
        "saved_tokens": saved,
        "saved_percent": round(100.0 * saved / source_tokens, 2) if source_tokens else 0.0,
    }
    if audience == "upstream":
        # 黑盒守門員：對上游的 capsule 不得帶引擎欄位或引擎身份字串。
        def_assert_blackbox(capsule, dict(document or {}))
    return capsule


# --------------------------------------------------------------------------
# 9. 資料庫最佳化：內容定址、增量、投影
# --------------------------------------------------------------------------

# --------------------------------------------------------------------------
# 8B. CME v2.0 能力表、Zero-Hydra 全景分析與黑盒 FastAccessLayer
# --------------------------------------------------------------------------

def def_blank_document() -> dict[str, Any]:
    return {
        "schema": PARAM_MAP_SCHEMA,
        "schema_version": PARAM_MAP_SCHEMA_VERSION,
        "authority": PARAM_AUTHORITY,
        "engine_id": PARAM_ENGINE_ID,
        "engine_version": PARAM_ENGINE_VERSION,
        "cme_version": PARAM_CME_VERSION,
        "registration_state": "CANDIDATE_PENDING_CGC_PROMOTION",
        "parent_ssot": "config/ssot/VIA_SystemMaster.via",
        "governance": {
            "single_writer": "CGC-PROMOTE-WORKER-001",
            "default_mode": "AUDIT",
            "apply_default": False,
            "default_strategy": PARAM_DEFAULT_STRATEGY,
            "strategies": list(PARAM_STRATEGIES),
            "source_mutation_policy": "forbidden",
            "network_default": False,
            "blackbox_policy": "capability-names-only",
            "hydra_risk_policy": "panoramic-ast-dual-mode-fail-closed",
            "overwrite_policy": "APPEND_ONLY_NEVER_BLIND_OVERWRITE",
            "projection_policy": "GENERATED_PROJECTIONS_ARE_NEVER_AUTHORITATIVE",
        },
        "thresholds": dict(PARAM_DEFAULT_THRESHOLDS),
        "similarity_weights": dict(PARAM_SIMILARITY_WEIGHTS),
        "embedding": {
            "algorithm": "blake2b-signed-feature-hashing",
            "dimensions": PARAM_EMBEDDING_DIMENSIONS,
            "features": "normalized-tokens + capability-projection + char-trigrams",
        },
        "ssot_dictionary": {key: list(value) for key, value in PARAM_CAPABILITY_DICTIONARY.items()},
        "verbs": sorted(PARAM_VERB_TOKENS),
        "noise_tokens": sorted(PARAM_NOISE_TOKENS),
        "capabilities": [],
        "pae": {},
    }


def def_validate_document(document: dict[str, Any]) -> dict[str, Any]:
    """能力表 fail-closed 驗證：schema／authority／引擎身份漂移一律拒絕。"""
    if document.get("schema") != PARAM_MAP_SCHEMA:
        raise def_EngineError("PEIS 能力表 schema 不符")
    if document.get("schema_version") not in (
        PARAM_MAP_SCHEMA_VERSION, *PARAM_MAP_SCHEMA_VERSION_COMPAT
    ):
        raise def_EngineError("能力表 schema_version 漂移")
    if document.get("authority") != PARAM_AUTHORITY:
        raise def_EngineError("PEIS 能力表 authority 不符")
    if document.get("engine_id") != PARAM_ENGINE_ID:
        raise def_EngineError("PEIS 能力表 engine_id 漂移")
    if document.get("engine_version") not in (
        PARAM_ENGINE_VERSION, *PARAM_ENGINE_VERSION_COMPAT
    ):
        raise def_EngineError("能力表 engine_version 漂移")
    if str(document.get("cme_version")) != PARAM_CME_VERSION:
        raise def_EngineError("CME 版本必須為 2.0")
    capabilities = document.get("capabilities")
    if not isinstance(capabilities, list):
        raise def_EngineError("PEIS 能力表 capabilities 必須是清單")
    thresholds = document.get("thresholds")
    if not isinstance(thresholds, dict):
        raise def_EngineError("PEIS 能力表缺少 thresholds")
    for key in PARAM_DEFAULT_THRESHOLDS:
        value = thresholds.get(key)
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise def_EngineError(f"PEIS 能力表 thresholds.{key} 型別錯誤")
    seen: set[str] = set()
    for record in capabilities:
        name = record.get("capability")
        if not isinstance(name, str) or not name:
            raise def_EngineError("能力記錄缺少 capability 名稱")
        if name in seen:
            raise def_EngineError(f"能力重複定義：{name}")
        seen.add(name)
        pool = record.get("engines")
        if not isinstance(pool, list):
            raise def_EngineError(f"{name} 缺少版本池 engines")
        for engine in pool:
            for key in ("engine_id", "version", "sha256", "entrypoint"):
                if not isinstance(engine.get(key), str) or not engine.get(key):
                    raise def_EngineError(f"{name} 版本池欄位缺失：{key}")
            performance = engine.get("performance")
            if not isinstance(performance, (int, float)) or isinstance(performance, bool):
                raise def_EngineError(f"{name} 版本池 performance 型別錯誤")
    return document


def def_load_capability_map(root: Path, create_if_missing: bool = False) -> dict[str, Any]:
    path = root / PARAM_CAPABILITY_MAP_RELATIVE
    if not path.is_file():
        if not create_if_missing:
            raise def_EngineError(f"找不到 PEIS 能力表：{PARAM_CAPABILITY_MAP_RELATIVE.as_posix()}")
        return def_blank_document()
    document = json.loads(path.read_text(encoding="utf-8"))
    return def_validate_document(document)


def def_thresholds(document: dict[str, Any]) -> dict[str, float]:
    limits = dict(PARAM_DEFAULT_THRESHOLDS)
    limits.update({
        key: float(value)
        for key, value in document.get("thresholds", {}).items()
        if key in PARAM_DEFAULT_THRESHOLDS
    })
    return limits


def def_default_strategy(document: Mapping[str, Any]) -> str:
    """版本池策略的唯一來源：能力表 governance.default_strategy；未宣告才用引擎預設。"""
    declared = (document.get("governance") or {}).get("default_strategy")
    if declared is None:
        return PARAM_DEFAULT_STRATEGY
    if declared not in PARAM_STRATEGIES:
        raise def_EngineError(f"能力表宣告了未知策略：{declared}")
    return str(declared)


def def_capability_record(document: dict[str, Any], capability: str) -> dict[str, Any] | None:
    for record in document.get("capabilities", []):
        if record.get("capability") == capability:
            return record
    return None


def def_capability_centroid(record: dict[str, Any]) -> tuple[float, ...]:
    functions = record.get("functions", [])
    if not functions:
        return ()
    return def_centroid([def_embed(name) for name in functions])


def def_performance_matrix(document: dict[str, Any]) -> dict[str, dict[str, float]]:
    """性能矩陣投影（能力 × 引擎版本），由版本池推導，永遠不是權威狀態。"""
    matrix: dict[str, dict[str, float]] = {}
    for record in document.get("capabilities", []):
        row: dict[str, float] = {}
        for engine in record.get("engines", []):
            row[f"{engine['engine_id']}@{engine['version']}"] = float(engine.get("performance", 0.0))
        matrix[record["capability"]] = dict(sorted(row.items()))
    return dict(sorted(matrix.items()))


def def_version_pool(document: dict[str, Any]) -> dict[str, list[str]]:
    pool: dict[str, list[str]] = {}
    for record in document.get("capabilities", []):
        for engine in record.get("engines", []):
            pool.setdefault(engine["engine_id"], []).append(engine["version"])
    return {key: sorted(set(value)) for key, value in sorted(pool.items())}


def def_build_pae(document: dict[str, Any]) -> dict[str, Any]:
    """步驟 8 PAE：把能力掛進對應的大引擎插槽（`E-Signal → predict_trend`）。"""
    slots: dict[str, Any] = {}
    for record in document.get("capabilities", []):
        capability = record["capability"]
        slot_name = f"E-{capability[:1].upper()}{capability[1:]}"
        slots[slot_name] = {
            "capability": capability,
            "slots": sorted(record.get("functions", [])),
            "engine_count": len(record.get("engines", [])),
            "locked_engine_count": sum(
                1 for engine in record.get("engines", []) if engine.get("locked")
            ),
        }
    return dict(sorted(slots.items()))


# ---------------------------------------------------------------------------
# Fail-Safe：全景式分析 + AST 雙模定位（Zero-Hydra）
# ---------------------------------------------------------------------------



@dataclass(frozen=True)
class def_Conflict:
    kind: str
    capability: str
    severity: str
    detail: str
    ast_symbol_sites: tuple[dict[str, int], ...] = ()
    ast_call_sites: tuple[dict[str, int], ...] = ()
    dependents: tuple[str, ...] = ()


@dataclass(frozen=True)
class def_CapabilityProposal:
    capability: str
    action: str
    cluster: str
    functions: tuple[str, ...]
    similarity: float
    engine_id: str = ""
    version: str = ""


def def_capability_dependencies(
    document: dict[str, Any],
    candidates: Sequence[def_EngineCandidate],
) -> dict[str, tuple[str, ...]]:
    """從呼叫圖推導「能力 → 能力」相依，作為全景式反向相依分析的底稿。"""
    owner: dict[str, str] = {}
    for record in document.get("capabilities", []):
        for name in record.get("functions", []):
            owner[name] = record["capability"]
    edges: dict[str, set[str]] = {}
    for candidate in candidates:
        for caller, callee in candidate.calls:
            caller_name = def_normalize_symbol(caller)
            callee_name = def_normalize_symbol(callee)
            source = owner.get(caller_name) or def_capability_for_symbol(caller_name)
            target = owner.get(callee_name)
            if target is None or source == target:
                continue
            edges.setdefault(source, set()).add(target)
    return {key: tuple(sorted(value)) for key, value in sorted(edges.items())}


def def_detect_cycle(edges: dict[str, Sequence[str]]) -> tuple[str, ...]:
    """回傳第一個偵測到的環（決定性：節點與鄰居皆排序後 DFS）。"""
    colors: dict[str, int] = {}
    stack: list[str] = []

    def def_visit(node: str) -> tuple[str, ...]:
        colors[node] = 1
        stack.append(node)
        for neighbour in sorted(edges.get(node, ())):
            state = colors.get(neighbour, 0)
            if state == 1:
                start = stack.index(neighbour)
                return tuple(stack[start:] + [neighbour])
            if state == 0:
                found = def_visit(neighbour)
                if found:
                    return found
        colors[node] = 2
        stack.pop()
        return ()

    for node in sorted(edges):
        if colors.get(node, 0) == 0:
            cycle = def_visit(node)
            if cycle:
                return cycle
    return ()


def def_panoramic_analysis(
    root: Path,
    document: dict[str, Any],
    locks: Sequence[def_EngineLock],
    proposals: Sequence[def_CapabilityProposal],
    candidates: Sequence[def_EngineCandidate] = (),
) -> dict[str, Any]:
    """Fail-Safe：判斷『可同步修正』或『需順序修正』，永不盲目覆寫能力表。"""
    conflicts: list[def_Conflict] = []
    owner: dict[str, str] = {}
    for record in document.get("capabilities", []):
        for name in record.get("functions", []):
            owner[name] = record["capability"]
    dependencies = def_capability_dependencies(document, candidates)
    reverse: dict[str, list[str]] = {}
    for source, targets in dependencies.items():
        for target in targets:
            reverse.setdefault(target, []).append(source)

    for lock in locks:
        record = def_capability_record(document, lock.capability)
        if record is None:
            continue
        for engine in record.get("engines", []):
            if engine["engine_id"] != lock.engine_id:
                continue
            if engine["version"] == lock.version and engine["sha256"] != lock.sha256:
                located = def_locate_symbol(
                    def_read_source(root, root / lock.source_path).decode("utf-8-sig", "replace"),
                    lock.entrypoint.split("#", 1)[-1],
                )
                conflicts.append(def_Conflict(
                    kind="VERSION_POOL_COLLISION",
                    capability=lock.capability,
                    severity="SEQUENTIAL",
                    detail=(
                        f"{lock.engine_id}@{lock.version} 已登錄且內容雜湊不同："
                        f"{engine['sha256'][:12]} → {lock.sha256[:12]}"
                    ),
                    ast_symbol_sites=located["symbol_mode"],
                    ast_call_sites=located["call_mode"],
                    dependents=tuple(sorted(reverse.get(lock.capability, ()))),
                ))
            elif engine["version"] == lock.version and engine.get("strategy") != lock.strategy:
                conflicts.append(def_Conflict(
                    kind="STRATEGY_REDEFINITION",
                    capability=lock.capability,
                    severity="SEQUENTIAL",
                    detail=(
                        f"{lock.engine_id}@{lock.version} 策略改寫："
                        f"{engine.get('strategy')} → {lock.strategy}"
                    ),
                    dependents=tuple(sorted(reverse.get(lock.capability, ()))),
                ))

    for proposal in proposals:
        if proposal.action == "CANDIDATE_CAPABILITY":
            continue
        for name in proposal.functions:
            existing = owner.get(name)
            if existing and existing != proposal.capability:
                conflicts.append(def_Conflict(
                    kind="FUNCTION_OWNERSHIP_DRIFT",
                    capability=proposal.capability,
                    severity="SEQUENTIAL",
                    detail=f"函式 {name} 已屬於能力 {existing}，改掛會造成連鎖破壞",
                    dependents=tuple(sorted(reverse.get(existing, ()))),
                ))

    projected = {key: set(value) for key, value in dependencies.items()}
    for proposal in proposals:
        if proposal.action != "NEW_CAPABILITY":
            continue
        projected.setdefault(proposal.capability, set())
    cycle = def_detect_cycle({key: sorted(value) for key, value in projected.items()})
    if cycle:
        conflicts.append(def_Conflict(
            kind="DEPENDENCY_CYCLE",
            capability=cycle[0],
            severity="SEQUENTIAL",
            detail="能力相依出現環：" + " → ".join(cycle),
            dependents=cycle,
        ))

    sequential = [conflict for conflict in conflicts if conflict.severity == "SEQUENTIAL"]
    verdict = "SEQUENTIAL_FIX" if sequential else "SYNC_FIXABLE"
    fix_plan: list[str] = []
    for position, conflict in enumerate(sequential, start=1):
        fix_plan.append(
            f"{position}. [{conflict.kind}] 能力 {conflict.capability}：{conflict.detail}"
            + (f"；下游相依 {list(conflict.dependents)}" if conflict.dependents else "")
        )
    if sequential:
        fix_plan.append(
            f"{len(sequential) + 1}. 逐項人工裁決後，重跑 `--mode expand --apply` 才會寫入能力表"
        )
    return {
        "verdict": verdict,
        "hydra_risk": "ISOLATED" if not sequential else "BLOCKED",
        "conflicts": [asdict(conflict) for conflict in conflicts],
        "fix_plan": tuple(fix_plan),
        "dependencies": dependencies,
        "reverse_dependencies": {key: tuple(sorted(value)) for key, value in sorted(reverse.items())},
    }


# ---------------------------------------------------------------------------
# CapabilityMapUpdater
# ---------------------------------------------------------------------------


def def_update_capability_map(
    root: Path,
    document: dict[str, Any],
    locks: Sequence[def_EngineLock] = (),
    proposals: Sequence[def_CapabilityProposal] = (),
    analysis: dict[str, Any] | None = None,
    apply: bool = False,
) -> dict[str, Any]:
    """模組 3 CapabilityMapUpdater：append-only 寫入 CME v2.0，順序修正時拒絕寫入。"""
    verdict = (analysis or {}).get("verdict", "SYNC_FIXABLE")
    if verdict != "SYNC_FIXABLE":
        return {
            "applied": False,
            "staged": False,
            "verdict": verdict,
            "document": document,
            "written": "",
            "reason": "偵測到需順序修正的相依衝突，fail-closed 不覆寫能力表",
        }
    staged = copy.deepcopy(document)
    records = {record["capability"]: record for record in staged.get("capabilities", [])}

    for proposal in proposals:
        if proposal.action == "CANDIDATE_CAPABILITY":
            continue
        record = records.get(proposal.capability)
        if record is None:
            record = {
                "capability": proposal.capability,
                "abstracted_from": proposal.cluster,
                "functions": [],
                "engines": [],
                "strategy": def_default_strategy(staged),
            }
            records[proposal.capability] = record
        merged = sorted(set(record.get("functions", [])) | set(proposal.functions))
        record["functions"] = merged

    for lock in locks:
        record = records.get(lock.capability)
        if record is None:
            record = {
                "capability": lock.capability,
                "abstracted_from": lock.capability,
                "functions": [],
                "engines": [],
                "strategy": lock.strategy,
            }
            records[lock.capability] = record
        record["functions"] = sorted(set(record.get("functions", [])) | set(lock.functions))
        pool = [
            engine for engine in record.get("engines", [])
            if not (engine["engine_id"] == lock.engine_id and engine["version"] == lock.version)
        ]
        pool.append(lock.def_pool_record())
        record["engines"] = sorted(
            pool, key=lambda engine: (engine["engine_id"], engine["version"])
        )

    staged["capabilities"] = [records[name] for name in sorted(records)]
    # 讀得進 v0100，寫出一律正規化成當前身份（只增不減，不改既有能力內容）
    staged["engine_version"] = PARAM_ENGINE_VERSION
    staged["schema_version"] = PARAM_MAP_SCHEMA_VERSION
    staged["pae"] = def_build_pae(staged)
    def_validate_document(staged)
    payload = json.dumps(staged, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    written = ""
    if apply:
        target = root / PARAM_CAPABILITY_MAP_RELATIVE
        def_write_atomic(target, payload)
        written = PARAM_CAPABILITY_MAP_RELATIVE.as_posix()
    return {
        "applied": bool(apply),
        "staged": True,
        "verdict": verdict,
        "document": staged,
        "written": written,
        "reason": "",
    }


# ---------------------------------------------------------------------------
# FastAccessLayer（黑盒 RUN 介面）
# ---------------------------------------------------------------------------


def def_collect_private_values(document: dict[str, Any]) -> tuple[str, ...]:
    """所有嚴禁外洩到上游 AI 的字串：引擎名稱、版本、策略、路徑與雜湊。"""
    values: set[str] = set()
    for record in document.get("capabilities", []):
        strategy = record.get("strategy")
        if isinstance(strategy, str) and strategy:
            values.add(strategy)
        for engine in record.get("engines", []):
            for key in PARAM_LEAK_FIELDS:
                value = engine.get(key)
                if isinstance(value, str) and value:
                    values.add(value)
    return tuple(sorted(values))


def def_assert_blackbox(payload: Any, document: dict[str, Any]) -> Any:
    """黑盒原則守門員：回傳值出現引擎欄位或引擎身份字串即 fail-closed。

    兩道檢查：結構性（任何 `engine_id` / `version` / `strategy` … 欄位名）與
    字面性（長度 >= 8 的私有字串，如 engine_id、entrypoint、sha256、策略名）。
    版本號這類短字串靠結構性檢查擋下，避免把 `"3.3"` 這種巧合誤判成洩漏。
    """
    def def_walk(node: Any) -> None:
        if isinstance(node, dict):
            leaked = sorted(set(node) & set(PARAM_LEAK_FIELDS))
            if leaked:
                raise def_BlackBoxViolation(f"回傳值含底層引擎欄位：{leaked}")
            for value in node.values():
                def_walk(value)
        elif isinstance(node, (list, tuple)):
            for value in node:
                def_walk(value)

    def_walk(payload)
    private = [
        value for value in def_collect_private_values(document)
        if len(value) >= PARAM_LEAK_MIN_VALUE_LENGTH
    ]
    if not private:
        return payload
    rendered = json.dumps(payload, ensure_ascii=False, default=str)
    for value in private:
        if value in rendered:
            raise def_BlackBoxViolation(f"回傳值洩漏底層引擎資訊：{value}")
    return payload


def def_best_engine_for(document: dict[str, Any], capability: str) -> dict[str, Any]:
    """Router：能力 → 最佳引擎。只挑已鎖定引擎，決定性 tie-break，不對外暴露。"""
    record = def_capability_record(document, capability)
    if record is None:
        raise def_EngineError(f"能力不存在：{capability}")
    strategy = record.get("strategy", "best-performance")
    pool = [engine for engine in record.get("engines", []) if engine.get("locked")]
    if not pool:
        raise def_EngineError(f"能力 {capability} 沒有任何已鎖定引擎")
    if strategy == "latest-version":
        key: Callable[[dict[str, Any]], Any] = lambda engine: (  # noqa: E731
            engine["version"], engine.get("performance", 0.0), engine["engine_id"]
        )
    elif strategy == "most-stable":
        key = lambda engine: (  # noqa: E731
            engine.get("stability", 0.0), engine.get("performance", 0.0),
            engine["version"], engine["engine_id"],
        )
    else:
        key = lambda engine: (  # noqa: E731
            engine.get("performance", 0.0), engine.get("stability", 0.0),
            engine["version"], engine["engine_id"],
        )
    return sorted(pool, key=lambda engine: (key(engine), engine["engine_id"]), reverse=True)[0]



def def_token_reduction(
    document: dict[str, Any],
    capability: str,
    params: Any = None,
    thresholds: dict[str, float] | None = None,
) -> dict[str, Any]:
    """量測「上游 AI 自行推理引擎差異」與「只發 RUN()」之間的實際差距。

    baseline 是上游若要自己選引擎必須讀進上下文的東西：該能力的版本池、性能矩陣、
    策略與驗證證據；fast 是 `RUN(capability, params)` 這一行。兩者都用同一套
    決定性估算（標準化 JSON 長度 / 4）換算 token，所以數字是量出來的，不是宣稱的。
    `routing_workload_reduction_percent` 則是路由候選數的縮減比例，是 CPU／RAM
    開銷的代理指標，不是機器層級的實測值。
    """
    limits = dict(PARAM_DEFAULT_THRESHOLDS if thresholds is None else thresholds)
    record = def_capability_record(document, capability)
    if record is None:
        raise def_EngineError(f"能力不存在：{capability}")
    baseline_context = {
        "capability": capability,
        "strategy": record.get("strategy"),
        "functions": record.get("functions", []),
        "engines": record.get("engines", []),
        "performance_matrix": def_performance_matrix(document).get(capability, {}),
        "version_pool": def_version_pool(document),
    }
    fast_context = {"RUN": [capability, params]}
    baseline_tokens = def_payload_token_estimate(baseline_context)
    fast_tokens = def_payload_token_estimate(fast_context)
    reduction = round(100.0 * (1.0 - fast_tokens / baseline_tokens), 2)
    engines_before = sum(
        len(row.get("engines", [])) for row in document.get("capabilities", [])
    )
    routing_reduction = (
        round(100.0 * (1.0 - 1.0 / engines_before), 2) if engines_before else 0.0
    )
    return {
        "capability": capability,
        "baseline_tokens": baseline_tokens,
        "fast_access_tokens": fast_tokens,
        "token_reduction_percent": reduction,
        "target_floor_percent": limits["token_reduction_floor_percent"],
        "target_ceiling_percent": limits["token_reduction_ceiling_percent"],
        "within_target": reduction >= limits["token_reduction_floor_percent"],
        "band": (
            "BELOW_FLOOR" if reduction < limits["token_reduction_floor_percent"]
            else "IN_TARGET" if reduction <= limits["token_reduction_ceiling_percent"]
            else "ABOVE_TARGET"
        ),
        "routing_candidates_before": engines_before,
        "routing_candidates_after": 1,
        "routing_workload_reduction_percent": routing_reduction,
    }


class def_FastAccessLayer:
    """模組 4 FastAccessLayer：上游 AI 只能呼叫 `RUN(capability, params)`。"""

    def __init__(
        self,
        root: Path,
        document: dict[str, Any],
        allow_execution: bool = True,
    ) -> None:
        self.root = Path(root).resolve()
        self.document = def_validate_document(document)
        self.allow_execution = bool(allow_execution)
        self._modules: dict[str, Any] = {}

    def def_capabilities(self) -> tuple[str, ...]:
        """唯一對上游公開的目錄：能力名稱，沒有引擎、版本或策略。"""
        return tuple(sorted(
            record["capability"]
            for record in self.document.get("capabilities", [])
            if any(engine.get("locked") for engine in record.get("engines", []))
        ))

    def def_describe(self) -> dict[str, Any]:
        surface = {
            "cme_version": self.document.get("cme_version"),
            "capabilities": list(self.def_capabilities()),
            "interface": "RUN(capability, params)",
        }
        return def_assert_blackbox(surface, self.document)

    def _def_resolve(self, engine: dict[str, Any]) -> Callable[..., Any]:
        source_path, _, symbol = engine["entrypoint"].partition("#")
        if not symbol:
            raise def_EngineError("ENTRYPOINT_MISSING")
        path = def_assert_inside_root(self.root, self.root / source_path)
        payload = def_read_source(self.root, path)
        if def_sha256_bytes(payload) != engine["sha256"]:
            raise def_EngineError("ENGINE_SEAL_DRIFT")
        expected_seal = def_lock_seal(
            engine["engine_id"], engine["version"], engine["sha256"],
            float(engine.get("performance", 0.0)),
        )
        if engine.get("lock_seal") and engine["lock_seal"] != expected_seal:
            raise def_EngineError("ENGINE_SEAL_DRIFT")
        module_key = f"{engine['engine_id']}@{engine['version']}"
        module = self._modules.get(module_key)
        if module is None:
            spec = importlib.util.spec_from_file_location(
                f"peis_locked_{hashlib.blake2b(module_key.encode(), digest_size=8).hexdigest()}",
                str(path),
            )
            if spec is None or spec.loader is None:
                raise def_EngineError("ENTRYPOINT_MISSING")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self._modules[module_key] = module
        target: Any = module
        for part in symbol.split("."):
            target = getattr(target, part, None)
            if target is None:
                raise def_EngineError("ENTRYPOINT_MISSING")
        if not callable(target):
            raise def_EngineError("ENTRYPOINT_MISSING")
        return target

    def def_run(self, capability: str, params: Any = None) -> dict[str, Any]:
        """`RUN(capability, params)`：唯一對上游開放的呼叫面。"""
        started = time.monotonic()
        trace = hashlib.blake2b(
            json.dumps([capability, params], ensure_ascii=False, sort_keys=True, default=str).encode("utf-8"),
            digest_size=8,
        ).hexdigest()
        result: Any = None
        status, reason = "GREEN", ""
        try:
            engine = def_best_engine_for(self.document, capability)
            if not self.allow_execution:
                status, reason = "AMBER", "EXECUTION_DISABLED"
            else:
                callable_target = self._def_resolve(engine)
                if params is None:
                    result = callable_target()
                elif isinstance(params, dict):
                    result = callable_target(**params)
                elif isinstance(params, (list, tuple)):
                    result = callable_target(*params)
                else:
                    result = callable_target(params)
        except def_EngineError as error:
            status, reason = "RED", str(error)
        except Exception as error:  # noqa: BLE001 - 上游只拿到型別，不拿到引擎細節
            status, reason = "RED", f"EXECUTION_ERROR:{type(error).__name__}"
        payload = {
            "c": capability,
            "status": status,
            "reason": reason,
            "result": result if status == "GREEN" else None,
            "elapsed_ms": int((time.monotonic() - started) * 1000),
            "trace_id": trace,
        }
        return def_assert_blackbox(payload, self.document)

    RUN = def_run



PARAM_STORE_DDL = (
    "CREATE TABLE IF NOT EXISTS vue_meta("
    " key TEXT PRIMARY KEY, value TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS vue_blob("
    " body_sha256 TEXT PRIMARY KEY, tokens INTEGER NOT NULL, body TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS vue_file("
    " path TEXT PRIMARY KEY, sha256 TEXT NOT NULL, size INTEGER NOT NULL,"
    " mtime_ns INTEGER NOT NULL, tokens INTEGER NOT NULL, functions INTEGER NOT NULL,"
    " scanned_at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS vue_function("
    " path TEXT NOT NULL, qualname TEXT NOT NULL, name TEXT NOT NULL,"
    " lineno INTEGER NOT NULL, end_lineno INTEGER NOT NULL, capability TEXT NOT NULL,"
    " fingerprint TEXT NOT NULL, signature TEXT NOT NULL, returns TEXT NOT NULL,"
    " doc TEXT NOT NULL, tools TEXT NOT NULL, risks TEXT NOT NULL,"
    " nodes INTEGER NOT NULL, arity INTEGER NOT NULL, shingles TEXT NOT NULL,"
    " vendorable INTEGER NOT NULL, executable INTEGER NOT NULL, skip_reason TEXT NOT NULL,"
    " is_method INTEGER NOT NULL, is_async INTEGER NOT NULL,"
    " module_executable INTEGER NOT NULL DEFAULT 0, body_tokens INTEGER NOT NULL,"
    " body_sha256 TEXT NOT NULL, PRIMARY KEY(path, qualname, lineno))",
    "CREATE TABLE IF NOT EXISTS vue_capability("
    " capability TEXT PRIMARY KEY, default_variant TEXT NOT NULL,"
    " variants INTEGER NOT NULL, members INTEGER NOT NULL, collapsed INTEGER NOT NULL,"
    " test_status TEXT NOT NULL, sealed INTEGER NOT NULL)",
    "CREATE TABLE IF NOT EXISTS vue_variant("
    " capability TEXT NOT NULL, variant TEXT NOT NULL, fingerprint TEXT NOT NULL,"
    " canonical TEXT NOT NULL, members INTEGER NOT NULL, vendorable INTEGER NOT NULL,"
    " executable INTEGER NOT NULL, near TEXT NOT NULL,"
    " PRIMARY KEY(capability, variant))",
    "CREATE TABLE IF NOT EXISTS vue_lock("
    " capability TEXT PRIMARY KEY, engine_id TEXT NOT NULL, status TEXT NOT NULL,"
    " variant TEXT NOT NULL, fingerprint TEXT NOT NULL, kind TEXT NOT NULL,"
    " sealed_at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS vue_handoff("
    " handoff TEXT NOT NULL, audience TEXT NOT NULL, capability TEXT NOT NULL,"
    " fingerprint TEXT NOT NULL, status TEXT NOT NULL, card_sha256 TEXT NOT NULL,"
    " emitted_at TEXT NOT NULL, PRIMARY KEY(handoff, audience, capability))",
    "CREATE TABLE IF NOT EXISTS vue_card("
    " capability TEXT PRIMARY KEY, status TEXT NOT NULL, tokens INTEGER NOT NULL,"
    " source_tokens INTEGER NOT NULL, saved_tokens INTEGER NOT NULL, card TEXT NOT NULL)",
    "CREATE INDEX IF NOT EXISTS vue_function_capability ON vue_function(capability)",
    "CREATE INDEX IF NOT EXISTS vue_function_fingerprint ON vue_function(fingerprint)",
    "CREATE INDEX IF NOT EXISTS vue_card_saved ON vue_card(saved_tokens DESC)",
)
PARAM_CARD_COLUMNS = ("cap", "eng", "st", "fp", "sig", "ret", "doc", "at", "tools",
                      "risk", "alt", "dup", "test", "tok")


class def_CapabilityStore:
    """能力庫：內容定址去重、stat 增量、欄位投影，把下載／讀取／建構成本壓到最小。"""

    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path is not None else None
        target = str(self.path) if self.path is not None else ":memory:"
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(target)
        self.connection.row_factory = sqlite3.Row
        if self.path is not None:
            self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=NORMAL")
        self.connection.execute("PRAGMA temp_store=MEMORY")
        self.ensure_schema()

    def __enter__(self) -> "def_CapabilityStore":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def close(self) -> None:
        self.connection.commit()
        self.connection.close()

    def ensure_schema(self) -> None:
        for statement in PARAM_STORE_DDL:
            self.connection.execute(statement)
        self.connection.execute(
            "INSERT INTO vue_meta(key, value) VALUES(?, ?)"
            " ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            ("schema_version", PARAM_STORE_SCHEMA_VERSION),
        )
        self.connection.execute(
            "INSERT INTO vue_meta(key, value) VALUES(?, ?)"
            " ON CONFLICT(key) DO NOTHING",
            ("engine", f"{PARAM_ENGINE_ID} {PARAM_ENGINE_VERSION}"),
        )
        self.connection.commit()

    # -- 增量快取 ---------------------------------------------------------
    def file_row(self, path: str) -> sqlite3.Row | None:
        cursor = self.connection.execute(
            "SELECT path, sha256, size, mtime_ns, tokens, functions FROM vue_file WHERE path=?",
            (path,),
        )
        return cursor.fetchone()

    def records_for(self, path: str, with_source: bool = True) -> list[def_FunctionRecord]:
        query = (
            "SELECT f.*, b.body AS body FROM vue_function AS f"
            " LEFT JOIN vue_blob AS b ON b.body_sha256 = f.body_sha256"
            " WHERE f.path=? ORDER BY f.lineno"
        )
        records: list[def_FunctionRecord] = []
        for row in self.connection.execute(query, (path,)):
            records.append(
                def_FunctionRecord(
                    path=row["path"],
                    name=row["name"],
                    qualname=row["qualname"],
                    lineno=row["lineno"],
                    end_lineno=row["end_lineno"],
                    capability=row["capability"],
                    fingerprint=row["fingerprint"],
                    signature=row["signature"],
                    returns=row["returns"],
                    doc=row["doc"],
                    tools=tuple(json.loads(row["tools"])),
                    risks=tuple(json.loads(row["risks"])),
                    nodes=row["nodes"],
                    arity=row["arity"],
                    shingles=tuple(json.loads(row["shingles"])),
                    vendorable=bool(row["vendorable"]),
                    executable=bool(row["executable"]),
                    skip_reason=row["skip_reason"],
                    is_method=bool(row["is_method"]),
                    is_async=bool(row["is_async"]),
                    module_executable=bool(row["module_executable"]),
                    body_tokens=row["body_tokens"],
                    body_sha256=row["body_sha256"],
                    source=(row["body"] or "") if with_source else "",
                )
            )
        return records

    def write_file(
        self,
        path: str,
        sha256: str,
        size: int,
        mtime_ns: int,
        tokens: int,
        records: Sequence[def_FunctionRecord],
    ) -> int:
        """寫入一個檔案的函式列；相同 body_sha256 的原文只存一份。回傳新增 blob 數。"""
        self.connection.execute("DELETE FROM vue_function WHERE path=?", (path,))
        inserted = 0
        for record in records:
            cursor = self.connection.execute(
                "INSERT INTO vue_blob(body_sha256, tokens, body) VALUES(?, ?, ?)"
                " ON CONFLICT(body_sha256) DO NOTHING",
                (record.body_sha256, record.body_tokens, record.source),
            )
            inserted += cursor.rowcount if cursor.rowcount > 0 else 0
            self.connection.execute(
                "INSERT INTO vue_function(path, qualname, name, lineno, end_lineno,"
                " capability, fingerprint, signature, returns, doc, tools, risks, nodes,"
                " arity, shingles, vendorable, executable, skip_reason, is_method,"
                " is_async, module_executable, body_tokens, body_sha256)"
                " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
                " ON CONFLICT(path, qualname, lineno) DO UPDATE SET"
                " fingerprint=excluded.fingerprint, capability=excluded.capability,"
                " body_sha256=excluded.body_sha256",
                (
                    record.path, record.qualname, record.name, record.lineno,
                    record.end_lineno, record.capability, record.fingerprint,
                    record.signature, record.returns, record.doc,
                    def_compact_json(list(record.tools)),
                    def_compact_json(list(record.risks)), record.nodes, record.arity,
                    def_compact_json(list(record.shingles)),
                    int(record.vendorable), int(record.executable), record.skip_reason,
                    int(record.is_method), int(record.is_async),
                    int(record.module_executable), record.body_tokens,
                    record.body_sha256,
                ),
            )
        self.connection.execute(
            "INSERT INTO vue_file(path, sha256, size, mtime_ns, tokens, functions, scanned_at)"
            " VALUES(?,?,?,?,?,?,?)"
            " ON CONFLICT(path) DO UPDATE SET sha256=excluded.sha256, size=excluded.size,"
            " mtime_ns=excluded.mtime_ns, tokens=excluded.tokens,"
            " functions=excluded.functions, scanned_at=excluded.scanned_at",
            (path, sha256, size, mtime_ns, tokens, len(records), def_iso_now()),
        )
        self.connection.commit()
        return inserted

    def forget_missing(self, present: Iterable[str]) -> int:
        keep = set(present)
        stored = {row["path"] for row in self.connection.execute("SELECT path FROM vue_file")}
        gone = sorted(stored - keep)
        for path in gone:
            self.connection.execute("DELETE FROM vue_function WHERE path=?", (path,))
            self.connection.execute("DELETE FROM vue_file WHERE path=?", (path,))
        self.connection.commit()
        return len(gone)

    # -- 計畫、封印與卡片 -------------------------------------------------
    def previous_locks(self) -> list[def_LockEntry]:
        return [
            def_LockEntry(
                capability=row["capability"],
                engine_id=row["engine_id"],
                status=row["status"],
                variant=row["variant"],
                fingerprint=row["fingerprint"],
                kind=row["kind"],
                sealed_at=row["sealed_at"],
            )
            for row in self.connection.execute(
                "SELECT * FROM vue_lock ORDER BY capability"
            )
        ]

    def write_plan(
        self,
        plan: def_Plan,
        outcomes: Mapping[str, def_TestOutcome],
        locks: Sequence[def_LockEntry],
        cards: Sequence[Mapping[str, Any]],
    ) -> None:
        self.connection.execute("DELETE FROM vue_capability")
        self.connection.execute("DELETE FROM vue_variant")
        for capability_id, capability in sorted(plan.capabilities.items()):
            outcome = outcomes.get(capability_id)
            lock = next((entry for entry in locks if entry.capability == capability_id), None)
            self.connection.execute(
                "INSERT INTO vue_capability(capability, default_variant, variants, members,"
                " collapsed, test_status, sealed) VALUES(?,?,?,?,?,?,?)",
                (
                    capability_id, capability.default_variant, len(capability.variants),
                    capability.member_count, capability.collapsed,
                    outcome.status if outcome else "SKIPPED",
                    int(bool(lock and lock.status == "SEALED")),
                ),
            )
            for variant in capability.variants:
                self.connection.execute(
                    "INSERT INTO vue_variant(capability, variant, fingerprint, canonical,"
                    " members, vendorable, executable, near) VALUES(?,?,?,?,?,?,?,?)",
                    (
                        capability_id, variant.variant, variant.fingerprint,
                        variant.canonical, len(variant.members), int(variant.vendorable),
                        int(variant.executable), def_compact_json(list(variant.near)),
                    ),
                )
        for lock in locks:
            self.connection.execute(
                "INSERT INTO vue_lock(capability, engine_id, status, variant, fingerprint,"
                " kind, sealed_at) VALUES(?,?,?,?,?,?,?)"
                " ON CONFLICT(capability) DO UPDATE SET engine_id=excluded.engine_id,"
                " status=excluded.status, variant=excluded.variant,"
                " fingerprint=excluded.fingerprint, kind=excluded.kind,"
                " sealed_at=excluded.sealed_at",
                (
                    lock.capability, lock.engine_id, lock.status, lock.variant,
                    lock.fingerprint, lock.kind, lock.sealed_at,
                ),
            )
        self.connection.execute("DELETE FROM vue_card")
        for card in cards:
            body_tokens = int(card["tok"]["body"])
            card_tokens = int(card["tok"]["card"])
            self.connection.execute(
                "INSERT INTO vue_card(capability, status, tokens, source_tokens, saved_tokens,"
                " card) VALUES(?,?,?,?,?,?)",
                (
                    card["cap"], card["st"], card_tokens, body_tokens,
                    max(0, body_tokens - card_tokens), def_compact_json(card),
                ),
            )
        self.connection.commit()

    def cards(
        self,
        capability: str | None = None,
        columns: Sequence[str] | None = None,
        limit: int | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        """投影查詢：只回傳指定欄位，讓呼叫端不必拉整張卡。"""
        query = "SELECT capability, card FROM vue_card"
        clauses: list[str] = []
        parameters: list[Any] = []
        if capability:
            clauses.append("capability=?")
            parameters.append(capability)
        if status:
            clauses.append("status=?")
            parameters.append(status)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY saved_tokens DESC, capability"
        if limit is not None:
            query += " LIMIT ?"
            parameters.append(int(limit))
        selected = list(columns) if columns else None
        if selected:
            unknown = [name for name in selected if name not in PARAM_CARD_COLUMNS]
            if unknown:
                raise def_EngineError(f"未知欄位：{','.join(unknown)}")
        rows: list[dict[str, Any]] = []
        for row in self.connection.execute(query, parameters):
            card = json.loads(row["card"])
            rows.append({name: card.get(name) for name in selected} if selected else card)
        return rows

    # -- 交棒基線（delta capsule 用） -------------------------------------
    def handoff_baseline(
        self, handoff: str = PARAM_DEFAULT_HANDOFF, audience: str = "upstream"
    ) -> dict[str, dict[str, str]]:
        """上次交給這個 handoff 的卡片指紋；沒有紀錄就回空字典（等於全新）。"""
        rows = self.connection.execute(
            "SELECT capability, fingerprint, status, card_sha256, emitted_at"
            " FROM vue_handoff WHERE handoff=? AND audience=? ORDER BY capability",
            (handoff, audience),
        )
        return {
            row["capability"]: {
                "fp": row["fingerprint"],
                "st": row["status"],
                "sha": row["card_sha256"],
                "at": row["emitted_at"],
            }
            for row in rows
        }

    def write_handoff(
        self,
        cards: Sequence[Mapping[str, Any]],
        handoff: str = PARAM_DEFAULT_HANDOFF,
        audience: str = "upstream",
        stamp: str | None = None,
    ) -> int:
        """記下這次交出去的完整卡片集合，作為下次 delta 的基線。"""
        moment = stamp or def_iso_now()
        self.connection.execute(
            "DELETE FROM vue_handoff WHERE handoff=? AND audience=?", (handoff, audience)
        )
        for card in cards:
            self.connection.execute(
                "INSERT INTO vue_handoff(handoff, audience, capability, fingerprint,"
                " status, card_sha256, emitted_at) VALUES(?,?,?,?,?,?,?)",
                (
                    handoff, audience, str(card["cap"]), str(card.get("fp") or ""),
                    str(card.get("st") or ""), def_sha256_text(def_compact_json(card)),
                    moment,
                ),
            )
        self.connection.commit()
        return len(cards)

    def handoff_index(self, audience: str | None = None) -> list[dict[str, Any]]:
        """交棒基線索引：每個 handoff 記了幾個能力、最後一次交棒時間。"""
        query = (
            "SELECT handoff, audience, COUNT(*) AS capabilities,"
            " MAX(emitted_at) AS emitted_at FROM vue_handoff"
        )
        parameters: list[Any] = []
        if audience is not None:
            query += " WHERE audience=?"
            parameters.append(audience)
        query += " GROUP BY handoff, audience ORDER BY handoff, audience"
        return [
            {
                "handoff": row["handoff"],
                "audience": row["audience"],
                "capabilities": int(row["capabilities"]),
                "emitted_at": row["emitted_at"],
            }
            for row in self.connection.execute(query, parameters)
        ]

    def forget_handoff(self, handoff: str, audience: str | None = None) -> int:
        """清掉一條交棒基線；下次那個 handoff 會拿到完整 capsule。"""
        if audience is None:
            cursor = self.connection.execute(
                "DELETE FROM vue_handoff WHERE handoff=?", (handoff,)
            )
        else:
            cursor = self.connection.execute(
                "DELETE FROM vue_handoff WHERE handoff=? AND audience=?",
                (handoff, audience),
            )
        self.connection.commit()
        return int(cursor.rowcount or 0)

    def sealed_capabilities(self) -> list[dict[str, str]]:
        return [
            {
                "capability": row["capability"],
                "engine_id": row["engine_id"],
                "fingerprint": row["fingerprint"],
            }
            for row in self.connection.execute(
                "SELECT capability, engine_id, fingerprint FROM vue_lock"
                " WHERE status='SEALED' ORDER BY capability"
            )
        ]

    def body_for(self, fingerprint: str) -> tuple[str, str] | None:
        cursor = self.connection.execute(
            "SELECT f.name AS name, b.body AS body FROM vue_function AS f"
            " JOIN vue_blob AS b ON b.body_sha256 = f.body_sha256"
            " WHERE f.fingerprint=? ORDER BY f.path, f.lineno LIMIT 1",
            (fingerprint,),
        )
        row = cursor.fetchone()
        if row is None or not row["body"]:
            return None
        return row["name"], row["body"]

    def statistics(self) -> dict[str, Any]:
        def scalar(sql: str) -> int:
            row = self.connection.execute(sql).fetchone()
            return int(row[0] or 0)

        functions = scalar("SELECT COUNT(*) FROM vue_function")
        blobs = scalar("SELECT COUNT(*) FROM vue_blob")
        blob_tokens = scalar("SELECT COALESCE(SUM(tokens),0) FROM vue_blob")
        function_tokens = scalar("SELECT COALESCE(SUM(body_tokens),0) FROM vue_function")
        return {
            "files": scalar("SELECT COUNT(*) FROM vue_file"),
            "functions": functions,
            "capabilities": scalar("SELECT COUNT(*) FROM vue_capability"),
            "sealed": scalar("SELECT COUNT(*) FROM vue_lock WHERE status='SEALED'"),
            "pending": scalar("SELECT COUNT(*) FROM vue_lock WHERE status='PENDING'"),
            "dormant": scalar("SELECT COUNT(*) FROM vue_lock WHERE status='DORMANT'"),
            "cards": scalar("SELECT COUNT(*) FROM vue_card"),
            "card_tokens": scalar("SELECT COALESCE(SUM(tokens),0) FROM vue_card"),
            "card_saved_tokens": scalar("SELECT COALESCE(SUM(saved_tokens),0) FROM vue_card"),
            "unique_bodies": blobs,
            "duplicate_bodies": max(0, functions - blobs),
            "dedup_tokens": max(0, function_tokens - blob_tokens),
        }


# --------------------------------------------------------------------------
# 10. 管線：ingest（INTAKE → … → STORE）
# --------------------------------------------------------------------------

# --------------------------------------------------------------------------
# 9B. 證據橋：沙箱測試結果 → VerificationEvidence → 引擎鎖
# --------------------------------------------------------------------------
def def_evidence_from_outcome(
    plan: def_Plan,
    capability: def_Capability,
    outcome: def_TestOutcome | None,
    lock: def_LockEntry,
) -> def_VerificationEvidence:
    """把測試結論翻成 PEIS 證據。只翻譯 TEST 階段量到的東西，不再自己執行。

    * `tests_total` = 進得了測試通道的 variant 數；`tests_passed` = 影子對照一致的數。
      **分歧的 variant 算不通過**：同一個能力名稱底下有兩種行為，就不該用能力名稱路由。
    * `coverage_percent` = 該通道覆蓋到的 variant 比例（被守衛擋下的算沒覆蓋）。
    * `stability_runs/failures` = TEST 階段重跑的實測值（沙箱在行程內重跑，
      模組級在同一個子行程批次裡重跑）。
    * `benchmark_score` 恆為 0.0：本引擎不量時間（量了就破壞決定性），
      那 0.10 權重要靠外部 benchmark 證據（`--evidence`）才拿得到。
    * `sandbox_gate` 標明是哪一條通道過的（沙箱或模組級隔離）。
    """
    total = len(capability.variants)
    if outcome is None or outcome.status != "PASS":
        passed = 0
        coverage = outcome.coverage_percent if outcome is not None else 0.0
        counted = 0
        runs = 0
        failures = 0
        gate = outcome.gate if outcome is not None else PARAM_SANDBOX_GATE
    else:
        counted = max(1, round(outcome.coverage_percent * total / 100.0)) if total else 0
        passed = len(outcome.equivalent)
        coverage = outcome.coverage_percent
        runs = outcome.runs
        failures = outcome.run_failures
        gate = outcome.gate
    return def_VerificationEvidence(
        sandbox_gate=gate,
        ast_pass=True,
        tests_total=counted,
        tests_passed=passed,
        coverage_percent=round(coverage, 2),
        stability_runs=runs,
        stability_failures=failures,
        benchmark_score=0.0,
    )


def def_load_external_evidence(path: Path) -> dict[str, def_VerificationEvidence]:
    """讀外部沙盒／benchmark 證據：`{"<capability>": {...}}` 或
    `{"default": {...}, "capabilities": {"<capability>": {...}}}`。

    這是 `benchmark_score` 唯一的合法來源；格式錯誤或欄位缺失一律 fail-closed。
    """
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise def_EngineError("外部證據必須是物件")
    rows = document.get("capabilities") if "capabilities" in document else document
    if not isinstance(rows, dict):
        raise def_EngineError("外部證據的 capabilities 必須是物件")
    default = document.get("default")
    evidence: dict[str, def_VerificationEvidence] = {}
    for capability, payload in sorted(rows.items()):
        if capability in ("default", "capabilities"):
            continue
        merged = dict(default or {})
        if not isinstance(payload, dict):
            raise def_EngineError(f"外部證據 {capability} 必須是物件")
        merged.update(payload)
        evidence[str(capability)] = def_VerificationEvidence.def_from_dict(merged)
    if not evidence:
        raise def_EngineError("外部證據沒有任何能力記錄")
    return evidence


def def_auto_engine_identity(path: str, sha256: str) -> tuple[str, str]:
    """自動鎖定的引擎身份 = 來源模組；版本 = 內容雜湊前綴。

    版本帶內容雜湊，版本池天然 append-only：同一個版本永遠對應同一份內容，
    `VERSION_POOL_COLLISION` 不會假報，內容一改就是新版本進池。
    治理指派的正式身份仍可用 `lock --engine-id/--engine-version` 覆寫。
    """
    slug = re.sub(r"[^A-Za-z0-9]+", "-", str(path)).strip("-").upper()
    return f"VUE-{slug}", f"c{sha256[:12]}"


def def_engine_locks_from_plan(
    root: Path,
    plan: def_Plan,
    outcomes: Mapping[str, def_TestOutcome],
    locks: Sequence[def_LockEntry],
    thresholds: Mapping[str, float] | None = None,
    strategy: str = PARAM_DEFAULT_STRATEGY,
    external: Mapping[str, def_VerificationEvidence] | None = None,
) -> tuple[list[def_EngineLock], list[dict[str, Any]]]:
    """已封印能力 → CME 版本池條目；沒過門檻的記下拒絕理由，不進能力表。

    `external` 是外部沙盒／benchmark 證據（`--evidence`），有就優先於本引擎的
    測試結論——那是唯一能讓 `benchmark_score` 非零的途徑。
    """
    limits = dict(PARAM_DEFAULT_THRESHOLDS if thresholds is None else thresholds)
    engine_locks: list[def_EngineLock] = []
    refused: list[dict[str, Any]] = []
    for lock in locks:
        if lock.status != "SEALED":
            continue
        capability = plan.capabilities.get(lock.capability)
        if capability is None:
            continue
        records = plan.records_by_fingerprint(lock.fingerprint)
        if not records:
            continue
        primary = sorted(records, key=lambda item: (item.path, item.lineno))[0]
        evidence = external.get(lock.capability) if external else None
        if evidence is None:
            evidence = def_evidence_from_outcome(
                plan, capability, outcomes.get(lock.capability), lock
            )
        engine_id, version = def_auto_engine_identity(primary.path, primary.body_sha256)
        members = sorted({
            record.name
            for record in plan.records
            if record.capability == lock.capability
        })
        try:
            engine_locks.append(def_lock_engine(
                root=root,
                source_path=primary.path,
                engine_id=engine_id,
                version=version,
                evidence=evidence,
                entrypoint_symbol=primary.name,
                strategy=strategy,
                thresholds=limits,
                capability=lock.capability,
                functions=members,
            ))
        except def_EngineError as error:
            refused.append({
                "capability": lock.capability,
                "engine_id": engine_id,
                "reason": def_bounded_text(error, 220),
                "evidence": asdict(evidence),
            })
    return engine_locks, refused


# --------------------------------------------------------------------------
# 10B. 全景自動擴充管線、JSON／CSV／HTML UI Matrix 報表與中央治理參數綁定
# --------------------------------------------------------------------------

def def_auto_expand(
    root: Path,
    document: dict[str, Any] | None = None,
    locks: Sequence[def_EngineLock] = (),
    prefixes: Sequence[str] = PARAM_ENGINE_SCAN_PREFIXES,
    apply: bool = False,
    quiet: bool = False,
) -> dict[str, Any]:
    """自動擴充管線：掃描 → 語義 → 向量 → 相似度 → 聚類 → 抽象 → CME → PAE。

    上游 AI 邏輯、引擎路由器與抽象層都不需要改動；新引擎自己走完這八步。
    """
    started = time.monotonic()
    root = Path(root).resolve()
    base_document = def_load_capability_map(root, create_if_missing=True) if document is None else def_validate_document(document)
    limits = def_thresholds(base_document)
    progress = def_ProgressBar(total=len(PARAM_PANORAMIC_STAGES), label="PEIS-PIPE", quiet=quiet)
    stages: list[dict[str, Any]] = []

    def def_stage(name: str, detail: str, payload: dict[str, Any], color: str = "GREEN") -> None:
        line = progress.def_advance(name, detail, color)
        stages.append({"stage": name, "detail": detail, "line": line, **payload})

    candidates = def_scan_engines(root, prefixes)
    ast_failures = [item.source_path for item in candidates if item.ast_status != "PASS"]
    def_stage(
        PARAM_PANORAMIC_STAGES[0],
        f"engines={len(candidates)} · ast_fail={len(ast_failures)}",
        {"engines": [item.source_path for item in candidates], "ast_failures": ast_failures},
        "GREEN" if not ast_failures else "YELLOW",
    )

    symbols = sorted({symbol for item in candidates for symbol in item.symbols})
    normalized = sorted({def_normalize_symbol(symbol) for symbol in symbols})
    def_stage(
        PARAM_PANORAMIC_STAGES[1],
        f"symbols={len(symbols)} · normalized={len(normalized)}",
        {"normalized": normalized},
    )

    vectors = {name: def_embed(name) for name in normalized}
    def_stage(
        PARAM_PANORAMIC_STAGES[2],
        f"vectors={len(vectors)} · dim={PARAM_EMBEDDING_DIMENSIONS}",
        {"embedding_dimensions": PARAM_EMBEDDING_DIMENSIONS},
    )

    matrix = def_build_similarity_matrix(normalized)
    pairs = sorted(
        (
            {"left": left, "right": right, "similarity": score}
            for left, row in matrix.items()
            for right, score in row.items()
            if left < right and score >= limits["similarity_threshold"]
        ),
        key=lambda item: (-item["similarity"], item["left"], item["right"]),
    )
    def_stage(
        PARAM_PANORAMIC_STAGES[3],
        f"pairs>=threshold={len(pairs)} · threshold={limits['similarity_threshold']}",
        {"top_pairs": pairs[:25]},
    )

    clusters = def_cluster(normalized, limits["similarity_threshold"], matrix=matrix)
    def_stage(
        PARAM_PANORAMIC_STAGES[4],
        f"clusters={len(clusters)}",
        {"clusters": {key: list(value) for key, value in clusters.items()}},
    )

    proposals = def_abstract_capabilities(base_document, clusters, limits)
    new_count = sum(1 for item in proposals if item.action == "NEW_CAPABILITY")
    extend_count = sum(1 for item in proposals if item.action == "EXTEND_CAPABILITY")
    pending = [item for item in proposals if item.action == "CANDIDATE_CAPABILITY"]
    unclassified = sorted({
        name for name in normalized
        if def_capability_for_symbol(name) == PARAM_UNCLASSIFIED
    })
    def_stage(
        PARAM_PANORAMIC_STAGES[5],
        f"new={new_count} · extend={extend_count} · candidate={len(pending)}",
        {
            "proposals": [asdict(item) for item in proposals],
            "candidates_pending_dictionary": [asdict(item) for item in pending],
            "unclassified_symbols": unclassified,
        },
        "GREEN" if not pending else "YELLOW",
    )

    analysis = def_panoramic_analysis(root, base_document, locks, proposals, candidates)
    update = def_update_capability_map(root, base_document, locks, proposals, analysis, apply)
    def_stage(
        PARAM_PANORAMIC_STAGES[6],
        f"verdict={analysis['verdict']} · applied={update['applied']}",
        {"analysis": analysis, "applied": update["applied"], "written": update["written"]},
        "GREEN" if analysis["verdict"] == "SYNC_FIXABLE" else "RED",
    )

    staged_document = update["document"]
    pae = def_build_pae(staged_document)
    def_stage(
        PARAM_PANORAMIC_STAGES[7],
        f"big_engines={len(pae)}",
        {"pae": pae},
    )

    capability_names = sorted(record["capability"] for record in staged_document.get("capabilities", []))
    savings = [
        def_token_reduction(staged_document, name, {"demo": True}, limits)
        for name in capability_names
    ]
    gate = "PASS" if analysis["verdict"] == "SYNC_FIXABLE" and not ast_failures else "FAIL"
    report: dict[str, Any] = {
        "schema": "VIA.PEISAutoExpansion",
        "schema_version": "1.0.0",
        "authority": PARAM_AUTHORITY,
        "engine_id": PARAM_ENGINE_ID,
        "engine_version": PARAM_ENGINE_VERSION,
        "cme_version": PARAM_CME_VERSION,
        "gate": gate,
        "mode": "APPLY" if apply else "AUDIT",
        "root": str(root),
        "elapsed_ms": int((time.monotonic() - started) * 1000),
        "stages": stages,
        "progress": progress.def_snapshot(),
        "verdict": analysis["verdict"],
        "hydra_risk": analysis["hydra_risk"],
        "conflicts": analysis["conflicts"],
        "fix_plan": list(analysis["fix_plan"]),
        "dependencies": analysis["dependencies"],
        "reverse_dependencies": analysis["reverse_dependencies"],
        "applied": update["applied"],
        "written": update["written"],
        "capabilities": capability_names,
        "candidates_pending_dictionary": [asdict(item) for item in pending],
        "unclassified_symbols": unclassified,
        "capability_map": staged_document,
        "performance_matrix": def_performance_matrix(staged_document),
        "version_pool": def_version_pool(staged_document),
        "pae": pae,
        "fast_access": {
            "interface": "RUN(capability, params)",
            "exposed": capability_names,
            "savings": savings,
        },
        "locks": [lock.def_standard_output() for lock in locks],
    }
    def_lamp(
        "GREEN" if gate == "PASS" else "RED",
        "PEIS-FINAL",
        f"{gate} · verdict={analysis['verdict']} · capabilities={len(capability_names)} "
        f"· candidates={len(pending)} · hydra={analysis['hydra_risk']} · mode={report['mode']}",
    )
    return report


# ---------------------------------------------------------------------------
# 報告：JSON / CSV / 自適應 HTML UI Matrix
# ---------------------------------------------------------------------------



def def_matrix_rows(report: dict[str, Any]) -> tuple[tuple[str, ...], ...]:
    rows: list[tuple[str, ...]] = []
    for record in report.get("capability_map", {}).get("capabilities", []):
        capability = record["capability"]
        engines = record.get("engines", [])
        if not engines:
            rows.append((capability, "", "", "", "", "UNLOCKED", str(len(record.get("functions", [])))))
            continue
        for engine in engines:
            rows.append((
                capability,
                engine["engine_id"],
                engine["version"],
                f"{float(engine.get('performance', 0.0)):.2f}",
                f"{float(engine.get('stability', 0.0)):.2f}",
                "LOCKED" if engine.get("locked") else "UNLOCKED",
                str(len(record.get("functions", []))),
            ))
    return tuple(rows)


def def_render_html_matrix(report: dict[str, Any]) -> str:
    """自適應 HTML UI Matrix：離線自足、深淺色自動切換、手機寬度可讀。"""
    gate = report.get("gate", "FAIL")
    verdict = report.get("verdict", "UNKNOWN")
    rows = def_matrix_rows(report)
    progress = report.get("progress", {})
    savings = report.get("fast_access", {}).get("savings", [])
    average_saving = (
        round(sum(item["token_reduction_percent"] for item in savings) / len(savings), 2)
        if savings else 0.0
    )
    stage_cards = "".join(
        "<li><span class=\"stage\">{stage}</span><span class=\"detail\">{detail}</span></li>".format(
            stage=escape(str(item.get("stage", ""))),
            detail=escape(str(item.get("detail", ""))),
        )
        for item in report.get("stages", [])
    )
    matrix_rows = "".join(
        "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td class=\"num\">{3}</td>"
        "<td class=\"num\">{4}</td><td><span class=\"pill {5}\">{6}</span></td>"
        "<td class=\"num\">{7}</td></tr>".format(
            escape(row[0]), escape(row[1] or "—"), escape(row[2] or "—"),
            escape(row[3] or "—"), escape(row[4] or "—"),
            "ok" if row[5] == "LOCKED" else "warn", escape(row[5]), escape(row[6]),
        )
        for row in rows
    ) or "<tr><td colspan=\"7\">尚無能力登錄</td></tr>"
    conflict_rows = "".join(
        "<li><b>{kind}</b> · {capability} · {detail}</li>".format(
            kind=escape(str(item.get("kind", ""))),
            capability=escape(str(item.get("capability", ""))),
            detail=escape(str(item.get("detail", ""))),
        )
        for item in report.get("conflicts", [])
    ) or "<li>無衝突，Zero-Hydra 風險隔離。</li>"
    saving_rows = "".join(
        "<tr><td>{0}</td><td class=\"num\">{1}</td><td class=\"num\">{2}</td>"
        "<td class=\"num\">{3}%</td><td><span class=\"pill {4}\">{5}</span></td></tr>".format(
            escape(item["capability"]), item["baseline_tokens"], item["fast_access_tokens"],
            item["token_reduction_percent"],
            "ok" if item["within_target"] else "warn",
            escape(str(item.get("band", "")).replace("_", "-")),
        )
        for item in savings
    ) or "<tr><td colspan=\"5\">尚無能力可量測</td></tr>"
    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PEIS UI Matrix · {escape(PARAM_ENGINE_ID)}</title>
<style>
:root {{
  color-scheme: light dark;
  --bg: #f6f7f9; --card: #ffffff; --ink: #14181f; --muted: #5b6474;
  --line: #d8dde6; --ok: #0f7b4f; --warn: #a65b00; --bad: #b3261e; --accent: #2b5cff;
}}
@media (prefers-color-scheme: dark) {{
  :root {{
    --bg: #0d1017; --card: #151a23; --ink: #e8ecf4; --muted: #9aa5b8;
    --line: #262e3b; --ok: #4ade80; --warn: #fbbf24; --bad: #f87171; --accent: #7aa2ff;
  }}
}}
* {{ box-sizing: border-box; }}
body {{ margin: 0; padding: 24px 16px 48px; background: var(--bg); color: var(--ink);
  font: 15px/1.6 -apple-system, "Segoe UI", "Noto Sans TC", system-ui, sans-serif; }}
main {{ max-width: 1080px; margin: 0 auto; }}
h1 {{ font-size: 22px; margin: 0 0 4px; }}
h2 {{ font-size: 15px; margin: 28px 0 10px; color: var(--muted); letter-spacing: .06em; }}
.sub {{ color: var(--muted); margin: 0 0 20px; font-size: 13px; }}
.card {{ background: var(--card); border: 1px solid var(--line); border-radius: 12px;
  padding: 16px; margin-bottom: 14px; }}
.grid {{ display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); }}
.kpi b {{ display: block; font-size: 24px; }}
.kpi span {{ color: var(--muted); font-size: 12px; }}
.bar {{ height: 10px; border-radius: 999px; background: var(--line); overflow: hidden; }}
.bar > i {{ display: block; height: 100%; width: {progress.get('percent', 0)}%; background: var(--accent); }}
table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
th, td {{ padding: 8px 10px; border-bottom: 1px solid var(--line); text-align: left; }}
th {{ color: var(--muted); font-weight: 600; font-size: 12px; text-transform: uppercase; }}
td.num, th.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
.pill {{ padding: 2px 8px; border-radius: 999px; font-size: 12px; border: 1px solid currentColor; }}
.pill.ok {{ color: var(--ok); }} .pill.warn {{ color: var(--warn); }} .pill.bad {{ color: var(--bad); }}
ul {{ margin: 0; padding-left: 18px; }}
li .stage {{ font-weight: 600; margin-right: 8px; }}
li .detail {{ color: var(--muted); }}
.scroll {{ overflow-x: auto; }}
</style>
</head>
<body>
<main>
<h1>PEIS 引擎鎖定與能力截取 · UI Matrix</h1>
<p class="sub">{escape(PARAM_ENGINE_ID)} {escape(PARAM_ENGINE_VERSION)} · CME v{escape(str(report.get('cme_version', '')))}
 · 模式 {escape(str(report.get('mode', '')))} · {escape(str(report.get('elapsed_ms', 0)))} ms</p>

<div class="grid">
  <div class="card kpi"><b><span class="pill {'ok' if gate == 'PASS' else 'bad'}">{escape(gate)}</span></b><span>Gate</span></div>
  <div class="card kpi"><b><span class="pill {'ok' if verdict == 'SYNC_FIXABLE' else 'warn'}">{escape(verdict)}</span></b><span>Fail-Safe 裁決</span></div>
  <div class="card kpi"><b>{len(report.get('capabilities', []))}</b><span>已抽象能力</span></div>
  <div class="card kpi"><b>{average_saving}%</b><span>平均 Token 下降</span></div>
</div>

<div class="card">
  <div class="bar"><i></i></div>
  <p class="sub" style="margin:8px 0 0">進度 {progress.get('completed', 0)}/{progress.get('total', 0)}
   · {progress.get('percent', 0)}% · Hydra 風險 {escape(str(report.get('hydra_risk', '')))}</p>
</div>

<h2>能力 × 引擎矩陣</h2>
<div class="card scroll"><table>
<thead><tr><th>能力</th><th>引擎</th><th>版本</th><th class="num">性能</th>
<th class="num">穩定度</th><th>鎖定</th><th class="num">函式數</th></tr></thead>
<tbody>{matrix_rows}</tbody></table></div>

<h2>FastAccessLayer Token 量測</h2>
<div class="card scroll"><table>
<thead><tr><th>能力</th><th class="num">基準 tokens</th><th class="num">RUN tokens</th>
<th class="num">下降</th><th>目標帶</th></tr></thead>
<tbody>{saving_rows}</tbody></table></div>

<h2>管線階段</h2>
<div class="card"><ul>{stage_cards}</ul></div>

<h2>Fail-Safe 衝突與修復計畫</h2>
<div class="card"><ul>{conflict_rows}</ul></div>
</main>
</body>
</html>
"""


def def_write_reports(output: Path, report: dict[str, Any]) -> dict[str, str]:
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "via-peis-report.json"
    csv_path = output / "via-peis-matrix.csv"
    html_path = output / "via-peis-ui-matrix.html"
    def_write_atomic(json_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    header = "capability,engine_id,version,performance,stability,locked,function_count"
    lines = [header]
    lines.extend(",".join(cell.replace(",", " ") for cell in row) for row in def_matrix_rows(report))
    def_write_atomic(csv_path, "\n".join(lines) + "\n")
    def_write_atomic(html_path, def_render_html_matrix(report))
    return {
        "json_report": str(json_path),
        "csv_report": str(csv_path),
        "html_report": str(html_path),
    }



def def_load_parameters(root: Path) -> dict[str, Any]:
    """讀取中央治理參數的 `unified_engine` 區塊；身份或路徑漂移一律 fail-closed。"""
    path = root / PARAM_GOVERNANCE_RELATIVE
    document = json.loads(path.read_text(encoding="utf-8"))
    parameters = document.get(PARAM_PARAMETER_BLOCK)
    if not isinstance(parameters, dict):
        # PEIS 前身用 peis_engine 當鍵；舊檔仍可讀，新檔一律寫 unified_engine。
        parameters = document.get(PARAM_PARAMETER_BLOCK_ALIAS)
    if not isinstance(parameters, dict):
        raise def_EngineError(
            f"中央治理缺少 {PARAM_PARAMETER_BLOCK} 參數"
        )
    if parameters.get("engine_id") != PARAM_ENGINE_ID:
        raise def_EngineError("中央治理 PEIS engine_id 漂移")
    if parameters.get("engine_version") not in (
        PARAM_ENGINE_VERSION, *PARAM_ENGINE_VERSION_COMPAT
    ):
        raise def_EngineError("中央治理 engine_version 漂移")
    if parameters.get("capability_map") != PARAM_CAPABILITY_MAP_RELATIVE.as_posix():
        raise def_EngineError("中央治理 PEIS capability_map 路徑漂移")
    if str(parameters.get("cme_version")) != PARAM_CME_VERSION:
        raise def_EngineError("中央治理 PEIS cme_version 漂移")
    for key in PARAM_DEFAULT_THRESHOLDS:
        value = parameters.get(key)
        if value is None:
            continue
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise def_EngineError(f"中央治理 PEIS {key} 型別錯誤")
    return parameters


def def_effective_thresholds(root: Path, document: dict[str, Any]) -> dict[str, float]:
    """中央治理參數可以收緊能力表門檻，但不能放寬安全閘門。"""
    limits = def_thresholds(document)
    try:
        parameters = def_load_parameters(root)
    except (OSError, ValueError, def_EngineError):
        return limits
    for key, value in parameters.items():
        if key not in limits or not isinstance(value, (int, float)) or isinstance(value, bool):
            continue
        if key == "token_reduction_ceiling_percent":
            limits[key] = float(value)
        elif key.endswith("_floor") or key.endswith("_floor_percent") or key.endswith("_threshold"):
            limits[key] = max(limits[key], float(value))
        else:
            limits[key] = float(value)
    return limits


def def_run_lock(
    root: Path,
    source_path: str,
    engine_id: str,
    version: str,
    evidence_path: Path,
    entrypoint_symbol: str | None,
    strategy: str,
    apply: bool,
    quiet: bool = False,
    capability: str | None = None,
) -> dict[str, Any]:
    document = def_load_capability_map(root, create_if_missing=True)
    limits = def_effective_thresholds(root, document)
    evidence = json.loads(Path(evidence_path).read_text(encoding="utf-8"))
    progress = def_ProgressBar(total=4, label="PEIS-LOCK", quiet=quiet)
    progress.def_advance("EvidenceIntake", f"gate={evidence.get('sandbox_gate', '')}")
    lock = def_lock_engine(
        root=root,
        source_path=source_path,
        engine_id=engine_id,
        version=version,
        evidence=evidence,
        entrypoint_symbol=entrypoint_symbol,
        strategy=strategy,
        thresholds=limits,
        capability=capability,
    )
    progress.def_advance("EngineLocker", f"{lock.engine_id}@{lock.version} · perf={lock.performance}")
    progress.def_advance("CapabilityExtractor", f"capability={lock.capability} · funcs={len(lock.functions)}")
    analysis = def_panoramic_analysis(root, document, [lock], (), def_scan_engines(root))
    update = def_update_capability_map(root, document, [lock], (), analysis, apply)
    progress.def_advance(
        "CapabilityMapUpdater",
        f"verdict={analysis['verdict']} · applied={update['applied']}",
        "GREEN" if analysis["verdict"] == "SYNC_FIXABLE" else "RED",
    )
    gate = "PASS" if analysis["verdict"] == "SYNC_FIXABLE" else "FAIL"
    def_lamp(
        "GREEN" if gate == "PASS" else "RED",
        "PEIS-LOCK",
        f"{gate} · {lock.engine_id}@{lock.version} → {lock.capability} · applied={update['applied']}",
    )
    return {
        "schema": "VIA.PEISEngineLock",
        "schema_version": "1.0.0",
        "engine_id": PARAM_ENGINE_ID,
        "engine_version": PARAM_ENGINE_VERSION,
        "gate": gate,
        "mode": "APPLY" if apply else "AUDIT",
        "lock": lock.def_standard_output(),
        "lock_detail": lock.def_pool_record(),
        "verdict": analysis["verdict"],
        "conflicts": analysis["conflicts"],
        "fix_plan": list(analysis["fix_plan"]),
        "applied": update["applied"],
        "written": update["written"],
        "capability_map": update["document"],
        "progress": progress.def_snapshot(),
        "capabilities": sorted(
            record["capability"] for record in update["document"].get("capabilities", [])
        ),
    }



def def_scan_paths(
    targets: Sequence[Path],
    store: def_CapabilityStore | None = None,
    root: Path | None = None,
) -> tuple[list[def_FunctionRecord], dict[str, int]]:
    """唯讀掃描；有資料庫時以 stat／sha256 增量跳過未變檔案（不重讀、不重解析）。"""
    files = def_iter_python_files(targets)
    records: list[def_FunctionRecord] = []
    intake = {
        "files": 0,
        "parsed_files": 0,
        "reused_files": 0,
        "reused_bytes": 0,
        "reused_tokens": 0,
        "unreadable_files": 0,
        "new_bodies": 0,
    }
    relative_root = Path(root).resolve() if root is not None else None
    present: list[str] = []
    for path in files:
        try:
            status = path.stat()
        except OSError:
            intake["unreadable_files"] += 1
            continue
        key = path.as_posix()
        if relative_root is not None:
            try:
                key = path.resolve().relative_to(relative_root).as_posix()
            except ValueError:
                key = path.as_posix()
        present.append(key)
        intake["files"] += 1
        cached = store.file_row(key) if store is not None else None
        if (
            cached is not None
            and cached["size"] == status.st_size
            and cached["mtime_ns"] == status.st_mtime_ns
        ):
            reused = store.records_for(key) if store is not None else []
            records.extend(reused)
            intake["reused_files"] += 1
            intake["reused_bytes"] += int(status.st_size)
            intake["reused_tokens"] += int(cached["tokens"])
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            intake["unreadable_files"] += 1
            continue
        digest = def_sha256_text(text)
        if cached is not None and cached["sha256"] == digest:
            reused = store.records_for(key) if store is not None else []
            records.extend(reused)
            intake["reused_files"] += 1
            intake["reused_tokens"] += int(cached["tokens"])
            if store is not None:
                store.write_file(
                    key, digest, status.st_size, status.st_mtime_ns,
                    int(cached["tokens"]), reused,
                )
            continue
        scanned = def_scan_source(text, key)
        records.extend(scanned)
        intake["parsed_files"] += 1
        if store is not None:
            intake["new_bodies"] += store.write_file(
                key, digest, status.st_size, status.st_mtime_ns,
                def_token_estimate(text), scanned,
            )
    if store is not None:
        intake["forgotten_files"] = store.forget_missing(present)
    return records, intake


def def_run_chain(
    targets: Sequence[Path],
    store: def_CapabilityStore,
    root: Path | None = None,
    mode: str = "independent",
    threshold: float = PARAM_NEAR_DUPLICATE_THRESHOLD,
    stage: Callable[[str, str], None] | None = None,
    allow_module_exec: bool = False,
) -> tuple[def_Plan, dict[str, def_TestOutcome], list[def_LockEntry], dict[str, Any]]:
    """統一鏈的前五階段：INTAKE → SCAN → CLUSTER → TEST → LOCK。

    治理半邊（EVIDENCE → POOL → HYDRA → MAP）由 `def_govern` 接手，
    標註與入庫（ANNOTATE／STORE）由呼叫端決定 audience 後再做。
    `stage` 是階段回報的單一匯流點：進度條與結構化階段紀錄都從這裡出去，
    否則報表只會拿到治理半邊的六個階段。
    """
    records, intake = def_scan_paths(targets, store, root=root)
    if stage is not None:
        stage(
            PARAM_UNIFIED_STAGES[0],
            f"files={intake['files']} · reused={intake['reused_files']}",
        )
        stage(
            PARAM_UNIFIED_STAGES[1],
            f"functions={len(records)} · parsed={intake['parsed_files']}",
        )
    plan = def_unify(records, mode=mode, threshold=threshold)
    plan.intake = intake
    if stage is not None:
        stage(
            PARAM_UNIFIED_STAGES[2],
            f"capabilities={len(plan.capabilities)} · collapsed={plan.collapsed}",
        )
    outcomes, module_statistics = def_test_plan(plan, root, allow_module_exec)
    passed = sum(1 for item in outcomes.values() if item.status == "PASS")
    if stage is not None:
        detail = f"probe_pass={passed}/{len(outcomes)}"
        if module_statistics["enabled"]:
            detail += f" · module_upgraded={module_statistics['upgraded']}"
        else:
            detail += f" · module_candidates={module_statistics['candidates']}"
        stage(PARAM_UNIFIED_STAGES[3], detail)
    locks = def_lock_plan(plan, outcomes, previous=store.previous_locks())
    sealed = sum(1 for entry in locks if entry.status == "SEALED")
    if stage is not None:
        stage(PARAM_UNIFIED_STAGES[4], f"sealed={sealed}/{len(locks)}")
    return plan, outcomes, locks, module_statistics


def def_ingest(
    targets: Sequence[Path],
    database: Path | None = None,
    mode: str = "independent",
    threshold: float = PARAM_NEAR_DUPLICATE_THRESHOLD,
    root: Path | None = None,
    budget_tokens: int | None = None,
    store: def_CapabilityStore | None = None,
    audience: str = "governance",
    allow_module_exec: bool = False,
    handoff: str | None = None,
) -> dict[str, Any]:
    """統一鏈（不含 CME 治理半邊）並回傳 candidate 證據（含 token 節省帳）。

    給了 `handoff` 就輸出 delta capsule（只送新增與變更），並把這次的卡片集合
    記成該 handoff 的下一次基線。
    """
    owned = store is None
    active = store if store is not None else def_CapabilityStore(database)
    try:
        plan, outcomes, locks, module_statistics = def_run_chain(
            targets, active, root, mode, threshold, allow_module_exec=allow_module_exec
        )
        policy = def_capsule_policy(root)
        cards = def_capability_cards(plan, outcomes, locks, audience)
        baseline = (
            active.handoff_baseline(handoff, audience) if handoff is not None else None
        )
        capsule = def_capability_capsule(
            plan, outcomes, locks, policy, budget_tokens, cards=cards,
            audience=audience, baseline=baseline, handoff=handoff,
        )
        if handoff is not None:
            active.write_handoff(
                [def_redact_for_upstream(card) if audience == "upstream" else card
                 for card in cards],
                handoff, audience,
            )
        active.write_plan(
            plan, outcomes, locks,
            def_capability_cards(plan, outcomes, locks, "governance"),
        )
        statistics = active.statistics()
    finally:
        if owned:
            active.close()
    return {
        "schema": PARAM_REPORT_SCHEMA,
        "schema_version": "1.0.0",
        "engine": {
            "id": PARAM_ENGINE_ID,
            "name": PARAM_ENGINE_NAME,
            "version": PARAM_ENGINE_VERSION,
            "protocol": PARAM_PROTOCOL,
            "mode": mode,
        },
        "mode": "READ_ONLY_SOURCES",
        "source_mutation": False,
        "intake": plan.intake,
        "module_exec": module_statistics,
        "consolidate": def_needs_consolidation(plan),
        "counts": capsule["counts"],
        "token_ledger": capsule["token_ledger"],
        "store": statistics,
        "locks": [asdict(entry) for entry in locks],
        "capsule": capsule,
        "verdict": "PASS" if plan.intake["files"] else "EMPTY",
    }




def def_govern(
    targets: Sequence[Path],
    database: Path | None = None,
    root: Path | None = None,
    mode: str = "plugin",
    threshold: float = PARAM_NEAR_DUPLICATE_THRESHOLD,
    budget_tokens: int | None = None,
    audience: str = "upstream",
    apply_map: bool = False,
    output: Path | None = None,
    quiet: bool = True,
    store: def_CapabilityStore | None = None,
    allow_module_exec: bool = False,
    evidence: Path | None = None,
    handoff: str | None = None,
) -> dict[str, Any]:
    """完整治理循環：統一鏈 + 沙箱證據 + 引擎鎖 + Zero-Hydra + CME v2.0 能力表。

    能力表預設 **AUDIT 不寫**（`apply_map=True` 才寫），偵測到需順序修正的衝突
    一律 fail-closed 不覆寫。來源檔全程唯讀。
    """
    started = time.monotonic()
    resolved = (
        Path(root).resolve() if root is not None
        else def_resolve_root(Path(targets[0]) if targets else None)
    )
    external_evidence = (
        def_load_external_evidence(Path(evidence)) if evidence is not None else None
    )
    owned = store is None
    active = store if store is not None else def_CapabilityStore(database)
    progress = def_ProgressBar(
        total=len(PARAM_UNIFIED_STAGES), label="VUE-CHAIN", quiet=quiet
    )
    stages: list[dict[str, Any]] = []

    def stage(name: str, detail: str, color: str = "GREEN") -> None:
        line = progress.def_advance(name, detail, color)
        stages.append({"stage": name, "detail": detail, "line": line})

    try:
        document = def_load_capability_map(resolved, create_if_missing=True)
        limits = def_effective_thresholds(resolved, document)
        plan, outcomes, locks, module_statistics = def_run_chain(
            targets, active, resolved, mode, threshold, stage, allow_module_exec
        )
        engine_locks, refused = def_engine_locks_from_plan(
            resolved, plan, outcomes, locks, limits,
            def_default_strategy(document), external_evidence,
        )
        stage(
            PARAM_UNIFIED_STAGES[5],
            f"evidence={len(engine_locks) + len(refused)} · gate={PARAM_SANDBOX_GATE}",
        )
        stage(
            PARAM_UNIFIED_STAGES[6],
            f"pool_entries={len(engine_locks)} · refused={len(refused)}",
            "GREEN" if engine_locks else "YELLOW",
        )
        try:
            candidates = def_scan_engines(resolved)
        except (OSError, def_EngineError):
            candidates = ()
        analysis = def_panoramic_analysis(
            resolved, document, engine_locks, (), candidates
        )
        stage(
            PARAM_UNIFIED_STAGES[7],
            f"verdict={analysis['verdict']} · conflicts={len(analysis['conflicts'])}",
            "GREEN" if analysis["verdict"] == "SYNC_FIXABLE" else "RED",
        )
        update = def_update_capability_map(
            resolved, document, engine_locks, (), analysis, apply_map
        )
        stage(
            PARAM_UNIFIED_STAGES[8],
            f"applied={update['applied']} · written={update['written'] or 'AUDIT'}",
            "GREEN" if update["staged"] else "RED",
        )
        staged = update["document"]
        policy = def_capsule_policy(resolved)
        cards = def_capability_cards(plan, outcomes, locks, audience)
        baseline = (
            active.handoff_baseline(handoff, audience) if handoff is not None else None
        )
        capsule = def_capability_capsule(
            plan, outcomes, locks, policy, budget_tokens,
            cards=cards, audience=audience, document=staged,
            baseline=baseline, handoff=handoff,
        )
        stage(
            PARAM_UNIFIED_STAGES[9],
            f"cards={len(capsule['cards'])}/{capsule['counts']['cards_total']} "
            f"· saved={capsule['token_ledger']['saved_percent']}%"
            + (f" · delta={handoff}" if handoff is not None else ""),
        )
        if handoff is not None:
            active.write_handoff(
                [def_redact_for_upstream(card) if audience == "upstream" else card
                 for card in cards],
                handoff, audience,
            )
        active.write_plan(
            plan, outcomes, locks,
            def_capability_cards(plan, outcomes, locks, "governance"),
        )
        statistics = active.statistics()
        stage(
            PARAM_UNIFIED_STAGES[10],
            f"cards_stored={statistics['cards']} · dedup={statistics['dedup_tokens']}",
        )
    finally:
        if owned:
            active.close()
    capability_names = sorted(
        record["capability"] for record in staged.get("capabilities", [])
    )
    savings = [
        def_token_reduction(staged, name, {"demo": True}, limits)
        for name in capability_names
    ]
    gate = "PASS" if analysis["verdict"] == "SYNC_FIXABLE" else "FAIL"
    report: dict[str, Any] = {
        "schema": "VIA.UnifiedGovernanceReport",
        "schema_version": "1.0.0",
        "authority": PARAM_AUTHORITY,
        "engine_id": PARAM_ENGINE_ID,
        "engine_version": PARAM_ENGINE_VERSION,
        "cme_version": PARAM_CME_VERSION,
        "gate": gate,
        "mode": "APPLY" if apply_map else "AUDIT",
        "source_mutation": False,
        "root": str(resolved),
        "elapsed_ms": int((time.monotonic() - started) * 1000),
        "stages": stages,
        "stage_names": list(PARAM_UNIFIED_STAGES),
        "progress": progress.def_snapshot(),
        "intake": plan.intake,
        "module_exec": module_statistics,
        "external_evidence": sorted(external_evidence) if external_evidence else [],
        "counts": capsule["counts"],
        "token_ledger": capsule["token_ledger"],
        "store": statistics,
        "capability_seals": [asdict(entry) for entry in locks],
        "domain_index": {
            domain: list(names)
            for domain, names in def_extract_capabilities(candidates).items()
        },
        "engine_pool": [lock.def_standard_output() for lock in engine_locks],
        "pool_refused": refused,
        "verdict": analysis["verdict"],
        "hydra_risk": analysis["hydra_risk"],
        "conflicts": analysis["conflicts"],
        "fix_plan": list(analysis["fix_plan"]),
        "dependencies": analysis["dependencies"],
        "reverse_dependencies": analysis["reverse_dependencies"],
        "applied": update["applied"],
        "written": update["written"],
        "capabilities": capability_names,
        "capability_map": staged,
        "performance_matrix": def_performance_matrix(staged),
        "version_pool": def_version_pool(staged),
        "pae": def_build_pae(staged),
        "fast_access": {
            "interface": "RUN(capability, params)",
            "exposed": capability_names,
            "savings": savings,
        },
        "capsule": capsule,
    }
    if output is not None:
        report.update(def_write_reports(Path(output), report))
    def_lamp(
        "GREEN" if gate == "PASS" else "RED",
        "VUE-FINAL",
        f"{gate} · sealed={capsule['counts']['sealed']} · pool={len(engine_locks)} "
        f"· hydra={analysis['hydra_risk']} · mode={report['mode']} "
        f"· saved={capsule['token_ledger']['saved_percent']}%",
    )
    return report


def def_run_capability(
    capability: str,
    arguments: Sequence[Any] | None = None,
    database: Path | None = None,
    store: def_CapabilityStore | None = None,
    *,
    root: Path | None = None,
    document: Mapping[str, Any] | None = None,
    params: Any = None,
    audience: str = "upstream",
    allow_execution: bool = True,
) -> dict[str, Any]:
    """RESULT_ONLY 執行。兩條路徑，都 fail-closed，回傳都不含原始碼：

    1. **CME 版本池**：能力表裡有已鎖引擎 → FastAccessLayer 依策略選版本，
       驗 sha256 與 lock_seal 後 importlib 載入（真實引擎會 import 第三方套件）。
    2. **能力庫沙箱**：只有 `SEALED` 的純函式能力 → 受限 builtins 沙箱執行。

    `audience="upstream"`（預設）走黑盒：不回傳引擎 id、指紋或策略。
    """
    if audience not in PARAM_AUDIENCES:
        raise def_EngineError(f"未知 audience：{audience}")
    payload = params if arguments is None else list(arguments)
    resolved_document: dict[str, Any] | None = None
    if document is not None:
        resolved_document = def_validate_document(dict(document))
    elif root is not None:
        try:
            resolved_document = def_load_capability_map(Path(root))
        except (OSError, ValueError, def_EngineError):
            resolved_document = None
    if resolved_document is not None:
        record = def_capability_record(resolved_document, capability)
        if record is not None and any(
            engine.get("locked") for engine in record.get("engines", [])
        ):
            layer = def_FastAccessLayer(
                Path(root) if root is not None else def_resolve_root(),
                resolved_document,
                allow_execution=allow_execution,
            )
            answer = layer.def_run(capability, payload)
            answer.update({"p": PARAM_PROTOCOL, "a": "RUN", "r": "RESULT_ONLY",
                           "path": "capability-map"})
            return answer
    owned = store is None
    active = store if store is not None else def_CapabilityStore(database)
    try:
        row = active.connection.execute(
            "SELECT * FROM vue_lock WHERE capability=?", (capability,)
        ).fetchone()
        if row is None:
            raise def_EngineError(f"能力未登錄：{capability}")
        if row["status"] != "SEALED":
            raise def_EngineError(
                f"能力未封印（{row['status']}），fail-closed 拒絕 RUN：{capability}"
            )
        body = active.body_for(row["fingerprint"])
        if body is None:
            raise def_EngineError(f"封印指紋缺少原文：{capability}")
        name, source = body
        if not allow_execution:
            return {"p": PARAM_PROTOCOL, "c": capability, "a": "RUN",
                    "r": "RESULT_ONLY", "status": "AMBER",
                    "reason": "EXECUTION_DISABLED", "result": None,
                    "path": "sandbox"}
        value = def_execute_guarded(source, name, list(payload or []))
        engine_id = row["engine_id"]
        fingerprint = row["fingerprint"]
    finally:
        if owned:
            active.close()
    answer: dict[str, Any] = {
        "p": PARAM_PROTOCOL,
        "c": capability,
        "a": "RUN",
        "r": "RESULT_ONLY",
        "status": "GREEN",
        "reason": "",
        "result": value,
        "path": "sandbox",
    }
    if audience == "governance":
        answer["eng"] = engine_id
        answer["fp"] = fingerprint[:16]
    else:
        def_assert_blackbox(answer, dict(resolved_document or {}))
    return answer


# --------------------------------------------------------------------------
# 11. Plugin 介面（掛入系統）
# --------------------------------------------------------------------------
def def_plugin_manifest(
    root: Path | None = None, database: Path | None = None
) -> dict[str, Any]:
    """回傳可掛入 Root SSOT engine_registry 的 candidate 描述（本函式不寫檔）。"""
    policy = def_capsule_policy(root)
    manifest: dict[str, Any] = {
        "schema": PARAM_PLUGIN_SCHEMA,
        "schema_version": "1.0.0",
        "engine": {
            "id": PARAM_ENGINE_ID,
            "name": PARAM_ENGINE_NAME,
            "version": PARAM_ENGINE_VERSION,
            "path": PARAM_ENGINE_RELATIVE,
            "role": "capability unification, sealing and token-minimal annotation",
            "writer": False,
        },
        "protocol": PARAM_PROTOCOL,
        "modes": ["independent", "plugin"],
        "authority": {
            "root_ssot": f"{PARAM_ROOT_SSOT_RELATIVE.as_posix()}#/engine_registry",
            "library_registry": "config/ssot/VIA_LibraryRegistry.candidate.via#/records",
            "canonical_writer": "CGC-PROMOTE-WORKER-001",
            "state": "CANDIDATE",
        },
        "guarantees": list(PARAM_GUARANTEES),
        "capsule_policy": policy,
        "parameter_block": PARAM_PARAMETER_BLOCK,
        "stages": list(PARAM_UNIFIED_STAGES),
        "panoramic_stages": list(PARAM_PANORAMIC_STAGES),
        "capability_map": {
            "path": PARAM_CAPABILITY_MAP_RELATIVE.as_posix(),
            "cme_version": PARAM_CME_VERSION,
            "default_mode": "AUDIT",
            "apply_default": False,
            "overwrite_policy": "APPEND_ONLY_NEVER_BLIND_OVERWRITE",
        },
        "blackbox": {
            "policy": "capability-names-only",
            "audiences": list(PARAM_AUDIENCES),
            "upstream_interface": "RUN(capability, params)",
            "envelope_actions": ["RUN", "CARD", "DESCRIBE"],
            "leak_fields": list(PARAM_LEAK_FIELDS),
        },
        "evidence": {
            "sandbox_gate": PARAM_SANDBOX_GATE,
            "stability_runs": PARAM_STABILITY_RUNS,
            "benchmark_score": "外部 benchmark 證據才有；沙箱一律 0.0，不自己補分",
            "thresholds": dict(PARAM_DEFAULT_THRESHOLDS),
        },
        "estimators": {
            "source_text": PARAM_TOKEN_ESTIMATOR,
            "payload_json": "peis-json4-v1",
        },
        "entry_points": {
            "ingest": "def_ingest(targets, database, mode='plugin')",
            "capsule": "def_capability_capsule(plan, outcomes, locks, policy)",
            "invoke": "def_plugin_invoke(envelope, arguments, database)",
            "cli": f"python {PARAM_ENGINE_RELATIVE} <selftest|ingest|capsule|run|query|manifest|report>",
        },
        "risk_legend": {
            code: {"level": level, "why": why}
            for code, (level, why) in PARAM_RISK_TABLE.items()
        },
    }
    if database is not None:
        with def_CapabilityStore(database) as store:
            manifest["capabilities"] = store.sealed_capabilities()
            manifest["store"] = store.statistics()
    return manifest


def def_plugin_invoke(
    envelope: Mapping[str, Any],
    arguments: Sequence[Any] | None = None,
    database: Path | None = None,
    store: def_CapabilityStore | None = None,
    *,
    root: Path | None = None,
    document: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """短卡 envelope 介面：`{"p","c","a","r"}`；未知協定或動作一律拒絕。

    動作：`RUN`（RESULT_ONLY）、`CARD`（單張能力卡）、`DESCRIBE`（只給能力名稱目錄）。
    """
    if str(envelope.get("p")) != PARAM_PROTOCOL:
        raise def_EngineError(f"協定不符：{envelope.get('p')}")
    action = str(envelope.get("a") or "RUN").upper()
    capability = str(envelope.get("c") or "")
    if not capability and action != "DESCRIBE":
        raise def_EngineError("envelope 缺少能力 id")
    if action == "RUN":
        return def_run_capability(
            capability, arguments or [], database, store, root=root, document=document
        )
    if action == "DESCRIBE":
        resolved = document if document is not None else None
        if resolved is None and root is not None:
            resolved = def_load_capability_map(Path(root))
        if resolved is None:
            raise def_EngineError("DESCRIBE 需要 --root 或 document（能力表）")
        layer = def_FastAccessLayer(
            Path(root) if root is not None else def_resolve_root(),
            dict(resolved),
            allow_execution=False,
        )
        surface = layer.def_describe()
        surface.update({"p": PARAM_PROTOCOL, "a": "DESCRIBE", "r": "CAPABILITY_NAMES_ONLY"})
        return surface
    if action == "CARD":
        owned = store is None
        active = store if store is not None else def_CapabilityStore(database)
        try:
            cards = active.cards(capability=capability)
        finally:
            if owned:
                active.close()
        if not cards:
            raise def_EngineError(f"能力未登錄：{capability}")
        return {"p": PARAM_PROTOCOL, "c": capability, "a": "CARD", "r": "CARD_ONLY",
                "card": cards[0]}
    raise def_EngineError(f"不支援的動作：{action}")


# --------------------------------------------------------------------------
# 12. 自測（不需要庫、不需要網路）
# --------------------------------------------------------------------------
PARAM_SELFTEST_MEAN_A = '''
def calc_mean(xs):
    return sum(xs) / len(xs)
'''
PARAM_SELFTEST_MEAN_B = '''
def calculate_mean(values: list) -> float:
    """平均值"""
    return sum(values) / len(values)
'''
PARAM_SELFTEST_MEAN_C = '''
def calculate_average(xs):
    total = 0.0
    count = 0
    for item in xs:
        total = total + item
        count = count + 1
    return total / count
'''
PARAM_SELFTEST_PORTFOLIO = '''
def compute_portfolio_score(prices, weights):
    """以權重加總報酬並回傳分數；缺值以前一筆補齊。"""
    cleaned = []
    previous = 0.0
    for value in prices:
        if value is None:
            cleaned.append(previous)
        else:
            cleaned.append(float(value))
            previous = float(value)
    if not cleaned:
        return 0.0
    total = 0.0
    index = 0
    for value in cleaned:
        weight = weights[index] if index < len(weights) else 0.0
        total = total + value * weight
        index = index + 1
    average = total / len(cleaned)
    spread = max(cleaned) - min(cleaned)
    return round(average + spread / 100.0, 6)
'''
PARAM_SELFTEST_PORTFOLIO_CLONE = '''
def calculate_portfolio_score(px, ws):
    """同一功能、不同命名與變數名（AST 等價，應被聚眾折疊）。"""
    rows = []
    last = 0.0
    for item in px:
        if item is None:
            rows.append(last)
        else:
            rows.append(float(item))
            last = float(item)
    if not rows:
        return 0.0
    accumulated = 0.0
    position = 0
    for item in rows:
        share = ws[position] if position < len(ws) else 0.0
        accumulated = accumulated + item * share
        position = position + 1
    mean_value = accumulated / len(rows)
    width = max(rows) - min(rows)
    return round(mean_value + width / 100.0, 6)
'''
PARAM_SELFTEST_UNSAFE = '''
def load_price_file(path):
    with open(path) as handle:
        return handle.read()
'''
PARAM_SELFTEST_WHILE = '''
def compute_spin(n):
    total = 0
    while True:
        total = total + n
    return total
'''


def def_selftest_raises(callable_target: Any, *arguments: Any) -> bool:
    """自測輔助：目標必須丟出 def_EngineError，否則視為不變式破了。"""
    try:
        callable_target(*arguments)
    except def_EngineError:
        return True
    except Exception:  # noqa: BLE001 - 丟別的錯也算沒守住契約
        return False
    return False


def def_selftest() -> list[tuple[str, bool]]:
    """回傳 (檢查名稱, 是否通過)；CLI 與 tests/ 共用同一組不變式。"""
    import tempfile

    rows: list[tuple[str, bool]] = []

    def push(name: str, ok: bool) -> None:
        rows.append((name, bool(ok)))

    first = def_scan_source(PARAM_SELFTEST_MEAN_A, "<selftest:mean-a>")[0]
    second = def_scan_source(PARAM_SELFTEST_MEAN_B, "<selftest:mean-b>")[0]
    third = def_scan_source(PARAM_SELFTEST_MEAN_C, "<selftest:mean-loop>")[0]
    push("α-rename 等價：calc_mean ≡ calculate_mean", first.fingerprint == second.fingerprint)
    push("迴圈版平均指紋不同", first.fingerprint != third.fingerprint)
    push("能力命名 compute.mean", {first.capability, second.capability, third.capability} == {"compute.mean"})
    push("Jaccard 自身為 1", def_jaccard(first.shingles, first.shingles) == 1.0)
    push("指紋與掃描順序無關", def_scan_source(PARAM_SELFTEST_MEAN_C, "<selftest:mean-loop>")[0].fingerprint == third.fingerprint)
    push("token 估算單調且確定", def_token_estimate("abcd") == def_token_estimate("abcd") == 1
         and def_token_estimate("abcd abcd") > def_token_estimate("abcd"))

    plan = def_unify([first, second, third])
    mean = plan.capabilities["compute.mean"]
    push("compute.mean 有 2 個 variant", len(mean.variants) == 2)
    push("v1 折疊 2 份重複實作", len(mean.variants[0].members) == 2)
    push("有重複才需要整合", def_needs_consolidation(plan) is True)
    push("單一函式不需要整合",
         def_needs_consolidation(def_unify(def_scan_source("def ping():\n    return 1\n", "<selftest:ping>"))) is False)

    outcomes, module_statistics = def_test_plan(plan)
    outcome = outcomes["compute.mean"]
    push("探針測試 PASS", outcome.status == "PASS")
    push("影子對照證明兩種實作等價", len(outcome.equivalent) == 2 and not outcome.divergent)

    locks = def_lock_plan(plan, outcomes, stamp="2026-01-01T00:00:00Z")
    sealed = next(entry for entry in locks if entry.capability == "compute.mean")
    push("測試成功才封印 SEALED", sealed.status == "SEALED")
    push("engine_id 穩定", sealed.engine_id == def_engine_id_for("compute.mean", "v1"))

    unsafe_records = def_scan_source(PARAM_SELFTEST_UNSAFE, "<selftest:unsafe-open>")
    push("open() 函式不得進沙箱", unsafe_records[0].executable is False)
    while_records = def_scan_source(PARAM_SELFTEST_WHILE, "<selftest:unsafe-while>")
    push("while 函式不得進沙箱", while_records[0].executable is False)
    unsafe_plan = def_unify(unsafe_records + while_records)
    unsafe_outcomes, _ = def_test_plan(unsafe_plan)
    push("沙箱拒絕即 SKIPPED",
         all(item.status == "SKIPPED" for item in unsafe_outcomes.values()))
    unsafe_locks = def_lock_plan(unsafe_plan, unsafe_outcomes, stamp="2026-01-01T00:00:00Z")
    push("未通過測試不封印",
         all(entry.status == "PENDING" for entry in unsafe_locks))

    relocked = def_lock_plan(plan, {"compute.mean": def_TestOutcome(
        capability="compute.mean", status="SKIPPED", probe="", arguments="", result="",
        equivalent=(), divergent=(), detail="forced")}, previous=locks,
        stamp="2026-02-02T00:00:00Z")
    push("已封印永不解封",
         next(e for e in relocked if e.capability == "compute.mean").status == "SEALED")

    policy = {"protocol": PARAM_CAPSULE_PROTOCOL, "max_chars": 12000, "max_items": 24,
              "source": "selftest"}
    plan.intake = {"files": 3}
    capsule = def_capability_capsule(plan, outcomes, locks, policy)
    card = capsule["cards"][0]
    encoded = def_compact_json(capsule)
    push("capsule 不夾帶原始碼全文",
         "sum(xs) / len(xs)" not in encoded and "def calc_mean" not in encoded)
    push("卡片自帶簽章與探針結果",
         card["sig"] == "calc_mean(xs)" and card["test"]["out"] == "2.5")
    ledger = capsule["token_ledger"]
    push("token 帳自洽（省下 = 全文 − capsule；小語料可能為負）",
         ledger["estimator"] == PARAM_TOKEN_ESTIMATOR
         and ledger["saved_tokens"] == ledger["source_tokens"] - ledger["capsule_tokens"]
         and ledger["capsule_tokens"] == ledger["header_tokens"] + ledger["card_tokens"])

    # 真實尺寸的函式才是 token 節省的對象：兩份 AST 等價實作應折成一張卡。
    portfolio = def_scan_source(PARAM_SELFTEST_PORTFOLIO, "<selftest:portfolio>")
    portfolio_clone = def_scan_source(PARAM_SELFTEST_PORTFOLIO_CLONE, "<selftest:portfolio-clone>")
    push("不同命名的同一實作指紋相同",
         portfolio[0].fingerprint == portfolio_clone[0].fingerprint)
    portfolio_plan = def_unify([*portfolio, *portfolio_clone])
    portfolio_plan.intake = {"files": 2}
    portfolio_outcomes, _ = def_test_plan(portfolio_plan)
    portfolio_locks = def_lock_plan(portfolio_plan, portfolio_outcomes,
                                    stamp="2026-01-01T00:00:00Z")
    portfolio_capsule = def_capability_capsule(
        portfolio_plan, portfolio_outcomes, portfolio_locks, policy)
    portfolio_card = portfolio_capsule["cards"][0]
    push("真實尺寸函式：一張卡取代兩份原始碼",
         portfolio_card["dup"] == 1
         and portfolio_card["tok"]["card"] < portfolio_card["tok"]["body"])
    push("真實尺寸語料：卡片合計遠小於全文",
         portfolio_capsule["token_ledger"]["card_tokens"]
         < portfolio_capsule["token_ledger"]["source_tokens"])

    # 拿本引擎自己當語料：capsule 的固定 header 在真實規模下必須被攤平。
    own_records = def_scan_source(
        Path(__file__).read_text(encoding="utf-8"), PARAM_ENGINE_RELATIVE)
    own_plan = def_unify(own_records, mode="plugin")
    own_plan.intake = {"files": 1}
    own_outcomes, _ = def_test_plan(own_plan)
    own_locks = def_lock_plan(own_plan, own_outcomes, stamp="2026-01-01T00:00:00Z")
    own_capsule = def_capability_capsule(own_plan, own_outcomes, own_locks, policy)
    own_ledger = own_capsule["token_ledger"]
    push("掃描本引擎自身：capsule 比讀全文省 50% 以上 token",
         own_ledger["saved_percent"] >= 50.0 and own_ledger["saved_tokens"] > 0)
    push("本引擎自身的沙箱拒絕理由可稽核",
         any(record.skip_reason for record in own_records)
         and all(record.skip_reason or record.executable for record in own_records))
    mixed_records = list(def_scan_source("def ping():\n    return 1\n", "<selftest:ping>"))
    mixed_plan = def_unify([first, second, third, *mixed_records])
    mixed_plan.intake = {"files": 4}
    mixed_outcomes, _ = def_test_plan(mixed_plan)
    mixed_locks = def_lock_plan(mixed_plan, mixed_outcomes, stamp="2026-01-01T00:00:00Z")
    tight = def_capability_capsule(mixed_plan, mixed_outcomes, mixed_locks,
                                   {**policy, "max_items": 1})
    push("capsule 服從 max_items 上限",
         len(tight["cards"]) == 1 and tight["truncated"]["reason"] == "max_items"
         and tight["truncated"]["omitted"] == 1)

    with tempfile.TemporaryDirectory(prefix="vue-selftest-") as temporary:
        workspace = Path(temporary)
        corpus = workspace / "pkg"
        corpus.mkdir()
        # 檔名一律組出來，不在原始碼留裸檔名字面值（見上面的 callgraph 註解）。
        for stem, text in (
            ("mean_a", PARAM_SELFTEST_MEAN_A),
            ("mean_b", PARAM_SELFTEST_MEAN_B),
            ("mean_loop", PARAM_SELFTEST_MEAN_C),
            ("mean_twin", PARAM_SELFTEST_MEAN_A),
            ("portfolio", PARAM_SELFTEST_PORTFOLIO),
            ("portfolio_clone", PARAM_SELFTEST_PORTFOLIO_CLONE),
        ):
            (corpus / f"{stem}.py").write_text(text, encoding="utf-8")
        database = workspace / "vue.db"
        first_report = def_ingest([corpus], database=database, root=workspace)
        push("首輪全部解析", first_report["intake"]["parsed_files"] == 6
             and first_report["intake"]["reused_files"] == 0)
        push("相同函式原文只存一份",
             first_report["store"]["duplicate_bodies"] >= 1
             and first_report["store"]["unique_bodies"] < first_report["store"]["functions"])
        second_report = def_ingest([corpus], database=database, root=workspace)
        push("次輪走增量：不重讀也不重解析",
             second_report["intake"]["reused_files"] == 6
             and second_report["intake"]["parsed_files"] == 0
             and second_report["intake"]["reused_tokens"] > 0)
        push("封印跨執行沿用",
             second_report["counts"]["sealed"] == first_report["counts"]["sealed"]
             and second_report["counts"]["sealed"] >= 1)
        answer = def_run_capability("compute.mean", [[1, 2, 3]], database=database)
        push("RESULT_ONLY 執行封印能力",
             answer["result"] == 2 and answer["r"] == "RESULT_ONLY"
             and "eng" not in answer)
        refused = False
        try:
            def_run_capability("misc.any", [], database=database)
        except def_EngineError:
            refused = True
        push("未封印能力拒絕 RUN", refused)
        with def_CapabilityStore(database) as store:
            projected = store.cards(columns=["cap", "sig"])
            push("投影查詢只回傳指定欄位",
                 bool(projected) and set(projected[0]) == {"cap", "sig"})
            unknown_rejected = False
            try:
                store.cards(columns=["body"])
            except def_EngineError:
                unknown_rejected = True
            push("未知欄位一律拒絕", unknown_rejected)
            statistics = store.statistics()
            push("能力卡整體比原始碼省 token",
                 statistics["card_saved_tokens"] > 0)
        manifest = def_plugin_manifest(root=workspace, database=database)
        push("plugin manifest 非 writer 且不連網",
             manifest["engine"]["writer"] is False
             and "no-network" in manifest["guarantees"])
        push("沒有 SSOT 時用內建 capsule 上限",
             manifest["capsule_policy"]["source"] == "engine-default")
        envelope_answer = def_plugin_invoke(
            {"p": PARAM_PROTOCOL, "c": "compute.mean", "a": "RUN", "r": "RESULT_ONLY"},
            arguments=[[2, 4]], database=database)
        push("envelope 呼叫回傳 RESULT_ONLY", envelope_answer["result"] == 3)
        bad_protocol = False
        try:
            def_plugin_invoke({"p": "OTHER", "c": "compute.mean"}, [], database=database)
        except def_EngineError:
            bad_protocol = True
        push("協定不符一律拒絕", bad_protocol)

        # ---- 合併後的完整治理循環：統一鏈 → 證據 → 版本池 → Zero-Hydra → CME 能力表
        (workspace / "config" / "ssot").mkdir(parents=True, exist_ok=True)
        (workspace / "config" / "ssot" / PARAM_CAPABILITY_MAP_RELATIVE.name).write_text(
            json.dumps(def_blank_document(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        audit = def_govern(
            [corpus], database=workspace / "gov.db", root=workspace, apply_map=False
        )
        push("治理循環通過且 Zero-Hydra 隔離",
             audit["gate"] == "PASS" and audit["verdict"] == "SYNC_FIXABLE"
             and audit["hydra_risk"] == "ISOLATED")
        push("AUDIT 預設不寫能力表",
             audit["applied"] is False and audit["written"] == ""
             and json.loads(
                 (workspace / "config" / "ssot" / PARAM_CAPABILITY_MAP_RELATIVE.name)
                 .read_text(encoding="utf-8"))["capabilities"] == [])
        push("沙箱證據進了版本池且基準分為 0",
             bool(audit["engine_pool"])
             and all(entry["performance"] == 0.9 for entry in audit["engine_pool"]))
        applied = def_govern(
            [corpus], database=workspace / "gov.db", root=workspace, apply_map=True
        )
        written = json.loads(
            (workspace / "config" / "ssot" / PARAM_CAPABILITY_MAP_RELATIVE.name)
            .read_text(encoding="utf-8"))
        push("--apply 才寫入能力表（append-only）",
             applied["applied"] is True and written["capabilities"]
             and all(record["engines"] for record in written["capabilities"]))
        mapped = def_run_capability(
            "compute.mean", params=[[1, 2, 3, 4]], root=workspace, document=written
        )
        push("能力表路徑 RUN 走 FastAccessLayer 並黑盒",
             mapped["result"] == 2.5 and mapped["path"] == "capability-map"
             and not (set(mapped) & set(PARAM_LEAK_FIELDS)))
        drifted = json.loads(json.dumps(written))
        drifted["capabilities"][0]["engines"][0]["sha256"] = "0" * 64
        push("封印漂移在派工點被拒絕",
             def_run_capability("compute.mean", params=[[1, 2]], root=workspace,
                                document=drifted)["reason"] == "ENGINE_SEAL_DRIFT")

    # ---------------- 治理半邊（PEIS 併入部分）的不變式 ----------------
    push("同義詞字典重複定義 fail-closed",
         def_selftest_raises(def_build_synonym_index,
                             {"math": ("calc",), "signal": ("calc",)}))
    push("calc／compute／calculate 收斂到 math 領域",
         {def_capability_for_symbol(name) for name in ("calc_sum", "compute_ratio", "calculate_mean")}
         == {"math"})
    push("字典沒命中就不捏造能力",
         def_capability_for_symbol("frobnicate_widget") == PARAM_UNCLASSIFIED)
    push("嵌入決定性且已正規化",
         def_embed("calc_mean") == def_embed("calc_mean")
         and abs(sum(v * v for v in def_embed("calc_mean")) - 1.0) < 1e-6)
    push("相似度對稱、有界、自身最大",
         def_similarity("calc_mean", "compute_mean") == def_similarity("compute_mean", "calc_mean")
         and 0.0 <= def_similarity("calc_mean", "gen_signal") <= 1.0
         and def_similarity("calc_mean", "calc_mean") == 1.0)
    push("相似度矩陣與輸入順序無關",
         def_build_similarity_matrix(["calc_sum", "gen_signal", "compute_mean"])
         == def_build_similarity_matrix(["compute_mean", "calc_sum", "gen_signal"]))

    good_evidence = {
        "sandbox_gate": "SELFTEST", "ast_pass": True, "tests_total": 8,
        "tests_passed": 8, "coverage_percent": 100.0, "stability_runs": 5,
        "stability_failures": 0, "benchmark_score": 0.9,
    }
    record = def_VerificationEvidence.def_from_dict(good_evidence)
    push("性能分數是證據的加權合成",
         record.def_performance() == round(0.40 + 0.30 + 0.20 + 0.10 * 0.9, 2))
    passed, reasons = record.def_gate(PARAM_DEFAULT_THRESHOLDS)
    push("全綠證據過門檻", passed and not reasons)
    weak = def_VerificationEvidence.def_from_dict({**good_evidence, "tests_passed": 5})
    push("測試未全綠不過門檻", weak.def_gate(PARAM_DEFAULT_THRESHOLDS)[0] is False)
    push("證據缺欄位 fail-closed",
         def_selftest_raises(def_VerificationEvidence.def_from_dict, {"sandbox_gate": "X"}))
    push("lock_seal 綁身份＋版本＋雜湊＋效能",
         def_lock_seal("E-A", "1.0", "a" * 64, 0.9) != def_lock_seal("E-A", "1.0", "a" * 64, 0.8)
         and def_lock_seal("E-A", "1.0", "a" * 64, 0.9) == def_lock_seal("E-A", "1.0", "a" * 64, 0.9))

    blank = def_blank_document()
    push("空白能力表驗證得過且能力為空",
         def_validate_document(blank)["capabilities"] == [])
    push("能力表 schema 漂移一律拒絕",
         def_selftest_raises(def_validate_document, {**blank, "cme_version": "1.0"}))
    push("能力表門檻型別錯誤一律拒絕",
         def_selftest_raises(
             def_validate_document,
             {**blank, "thresholds": {**blank["thresholds"], "performance_floor": "0.7"}}))
    push("相依環決定性偵測",
         def_detect_cycle({"a": ["b"], "b": ["c"], "c": ["a"]})[0] in ("a", "b", "c")
         and def_detect_cycle({"a": ["b"], "b": []}) == ())
    push("黑盒守門員擋結構性洩漏",
         def_selftest_raises(def_assert_blackbox, {"engine_id": "E-A"}, {}))
    push("黑盒守門員擋字面洩漏",
         def_selftest_raises(
             def_assert_blackbox,
             {"note": "engine/demo_engine.py"},
             {"capabilities": [{"capability": "x", "engines": [
                 {"source_path": "engine/demo_engine.py"}]}]}))
    upstream = def_capability_capsule(
        plan, outcomes, locks, policy, audience="upstream")
    push("upstream capsule 不帶引擎身份",
         "engine" not in upstream and all(
             key not in card for card in upstream["cards"] for key in ("eng", "fp", "at")))
    push("governance capsule 才帶引擎身份與錨點",
         "engine" in capsule and "at" in capsule["cards"][0])
    push("兩套 token 估算並存且各自穩定",
         def_payload_token_estimate({"a": 1}) >= 1
         and def_token_estimate("abcd") == 1
         and def_token_jaccard([], []) == 0.0 and def_jaccard([], []) == 1.0)

    own_source = Path(__file__).read_text(encoding="utf-8")
    own_tree = ast.parse(own_source)
    imported = {
        node.names[0].name.split(".")[0]
        for node in ast.walk(own_tree)
        if isinstance(node, ast.Import)
    } | {
        (node.module or "").split(".")[0]
        for node in ast.walk(own_tree)
        if isinstance(node, ast.ImportFrom)
    }
    push("本引擎不匯入任何網路套件",
         not (imported & {"requests", "httpx", "aiohttp", "urllib", "socket", "yfinance"}))
    push("本引擎只用標準庫",
         imported <= {
             "argparse", "ast", "builtins", "collections", "copy", "dataclasses",
             "functools", "hashlib", "html", "importlib", "json", "math", "os",
             "pathlib", "re", "sqlite3", "subprocess", "sys", "tempfile", "time",
             "typing", "unittest", "zipfile", "", "__future__",
         })
    return rows


# --------------------------------------------------------------------------
# 13. CLI
# --------------------------------------------------------------------------
PARAM_SUBCOMMANDS = (
    "selftest", "verify", "version", "export", "handoff", "ingest", "govern",
    "expand", "lock", "capsule", "run", "query", "manifest", "report",
)
PARAM_LEGACY_MODES = ("expand", "lock", "run", "report")


def def_build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="via_unified_engine",
        description=f"{PARAM_ENGINE_NAME} {PARAM_ENGINE_VERSION}（{PARAM_ENGINE_ID}）",
    )
    parser.add_argument("--json", action="store_true", help="以 JSON 輸出（單行）")
    sub = parser.add_subparsers(dest="command")

    def add(name: str, help_text: str) -> argparse.ArgumentParser:
        """每個子指令都吃 --json，放前放後都一樣。"""
        child = sub.add_parser(name, help=help_text)
        child.add_argument(
            "--json", action="store_true", default=argparse.SUPPRESS,
            help="以 JSON 輸出（單行）",
        )
        child.add_argument(
            "--quiet", action="store_true", default=argparse.SUPPRESS,
            help="關閉進度條與燈號輸出（燈號本來就走 stderr）",
        )
        return child

    add("selftest", "離線自測，不需要庫也不需要網路")

    verify = add("verify", "一鍵閘門：自測 → 治理循環（AUDIT）→ 逐條斷言")
    verify.add_argument("--src", action="append", help="檔案或資料夾，可重複（預設 engine/）")
    verify.add_argument("--root", help="治理根目錄（省略則自動解析）")
    verify.add_argument("--db", help="能力庫（省略則只在記憶體）")

    add("version", "引擎身份卡：規格、估算器、字典與門檻")

    export = add("export", "輸出可離開本庫獨立運作的成品（引擎＋README＋空白能力表＋MANIFEST）")
    export.add_argument("--out", required=True, help="輸出目錄")
    export.add_argument("--zip", action="store_true", help="另外打包成 .zip")
    export.add_argument(
        "--no-verify", action="store_true",
        help="不在輸出目錄實跑一次匯出後的自測（預設會跑，證明它自己跑得起來）",
    )

    handoff = add("handoff", "列出或清掉 delta capsule 的交棒基線")
    handoff.add_argument("--db", required=True)
    handoff.add_argument("--forget", help="清掉這個交棒 id 的基線")
    handoff.add_argument("--audience", choices=PARAM_AUDIENCES, default="upstream")

    ingest = add("ingest", "INTAKE→SCAN→CLUSTER→TEST→LOCK→ANNOTATE→STORE")
    ingest.add_argument("--src", action="append", required=True, help="檔案或資料夾，可重複")
    ingest.add_argument("--db", help="能力庫（省略則只在記憶體）")
    ingest.add_argument("--root", help="路徑相對化與 SSOT capsule policy 的庫根")
    ingest.add_argument("--mode", choices=("independent", "plugin"), default="independent")
    ingest.add_argument("--threshold", type=float, default=PARAM_NEAR_DUPLICATE_THRESHOLD)
    ingest.add_argument("--budget-tokens", type=int, default=None)
    ingest.add_argument("--audience", choices=PARAM_AUDIENCES, default="governance")
    ingest.add_argument("--handoff", help="以這個交棒 id 輸出 delta capsule（只送新增與變更）")
    ingest.add_argument("--capsule-only", action="store_true", help="只輸出能力 capsule")
    ingest.add_argument(
        "--allow-module-exec", action="store_true",
        help="沙箱沒過的能力再做模組級隔離補測（會真的 import 來源模組，預設關閉）",
    )

    govern = add("govern", "統一鏈 + 沙箱證據 + 引擎鎖 + Zero-Hydra + CME 能力表")
    govern.add_argument("--src", action="append", required=True, help="檔案或資料夾，可重複")
    govern.add_argument("--db", help="能力庫（省略則只在記憶體）")
    govern.add_argument("--root", help="治理根目錄（省略則自動解析）")
    govern.add_argument("--mode", choices=("independent", "plugin"), default="plugin")
    govern.add_argument("--threshold", type=float, default=PARAM_NEAR_DUPLICATE_THRESHOLD)
    govern.add_argument("--budget-tokens", type=int, default=None)
    govern.add_argument("--audience", choices=PARAM_AUDIENCES, default="upstream")
    govern.add_argument("--apply", action="store_true", help="寫入 CME 能力表（預設 AUDIT 不寫）")
    govern.add_argument(
        "--allow-module-exec", action="store_true",
        help="沙箱沒過的能力再做模組級隔離補測（會真的 import 來源模組，預設關閉）",
    )
    govern.add_argument("--evidence", help="外部沙盒／benchmark 證據 JSON（唯一能給 benchmark_score 的來源）")
    govern.add_argument("--handoff", help="以這個交棒 id 輸出 delta capsule（只送新增與變更）")
    govern.add_argument("--output", help="JSON／CSV／HTML UI Matrix 報告輸出目錄")

    expand = add("expand", "全景八階段自動擴充（掃描→語意→向量→相似度→聚類→抽象→CME→PAE）")
    expand.add_argument("--root", help="治理根目錄（省略則自動解析）")
    expand.add_argument("--apply", action="store_true", help="寫入 CME 能力表（預設 AUDIT 不寫）")
    expand.add_argument("--output", help="報告輸出目錄")

    lock = add("lock", "以外部沙盒證據鎖定一支引擎並登錄版本池")
    lock.add_argument("--root", help="治理根目錄（省略則自動解析）")
    # 這四個是必填，但由 def_main 手動驗證：治理契約要的是「缺參數 → RED + 回 1」，
    # 不是 argparse 的 exit 2。
    lock.add_argument("--engine-path", default="", help="引擎來源相對路徑")
    lock.add_argument("--engine-id", default="")
    lock.add_argument("--engine-version", default="")
    lock.add_argument("--evidence", default="", help="沙盒驗證證據 JSON 路徑")
    lock.add_argument("--entrypoint", default="", help="公開符號名稱")
    lock.add_argument("--capability", default="", help="明確指定能力（略過自動抽象）")
    lock.add_argument("--strategy", default="best-performance",
                      choices=("best-performance", "most-stable", "latest-version"))
    lock.add_argument("--apply", action="store_true", help="寫入 CME 能力表（預設 AUDIT 不寫）")
    lock.add_argument("--output", help="報告輸出目錄")

    capsule = add("capsule", "從能力庫輸出能力卡 capsule")
    capsule.add_argument("--db", required=True)
    capsule.add_argument("--root")
    capsule.add_argument("--capability")
    capsule.add_argument("--status", choices=("SEALED", "PENDING", "DORMANT"))
    capsule.add_argument("--budget-tokens", type=int, default=None)
    capsule.add_argument("--limit", type=int, default=None)
    capsule.add_argument("--audience", choices=PARAM_AUDIENCES, default="upstream")
    capsule.add_argument("--handoff", help="交棒 id：只輸出相對上次的 delta")
    capsule.add_argument("--diff", action="store_true", help="只輸出 delta 摘要，不帶卡片")
    capsule.add_argument(
        "--no-record", action="store_true",
        help="輸出 delta 但不更新基線（給稽核／預覽用）",
    )

    run = add("run", "RESULT_ONLY 執行已封印能力（能力表版本池優先，其次能力庫沙箱）")
    run.add_argument("--db", help="能力庫（走沙箱路徑時需要）")
    run.add_argument("--root", help="治理根目錄（讀 CME 能力表）")
    run.add_argument("--capability", required=True)
    run.add_argument("--args", default="", help="JSON 陣列（沙箱位置引數）")
    run.add_argument("--params", default="", help="JSON（能力表路徑的參數，dict/list/純值）")
    run.add_argument("--audience", choices=PARAM_AUDIENCES, default="upstream")
    run.add_argument("--no-execute", action="store_true", help="只解析不執行（稽核用）")
    run.add_argument("--output", help="把 RESULT_ONLY envelope 也寫成證據檔的目錄")

    query = add("query", "投影查詢能力卡欄位")
    query.add_argument("--db", required=True)
    query.add_argument("--capability")
    query.add_argument("--columns", default="cap,eng,st,sig")
    query.add_argument("--limit", type=int, default=None)

    manifest = add("manifest", "輸出可掛入系統的 plugin candidate 描述")
    manifest.add_argument("--root")
    manifest.add_argument("--db")

    report = add("report", "能力庫 token 節省帳與 CME 能力表現況")
    report.add_argument("--db", help="能力庫（省略則只報 CME 能力表）")
    report.add_argument("--root", help="一併輸出 CME 能力表、性能矩陣與版本池")
    report.add_argument("--output", help="報告輸出目錄")
    return parser


def def_translate_legacy(argv: Sequence[str]) -> list[str]:
    """相容兩支前身的旗標式呼叫。

    * CANON CPU：`--selftest`、`--scan <path>`。
    * PEIS：`--mode expand|lock|run|report`（出現在任何位置都會轉成子指令）。
    """
    rest = list(argv)
    for index, token in enumerate(rest):
        if token != "--mode" or index + 1 >= len(rest):
            continue
        if rest[index + 1] not in PARAM_LEGACY_MODES:
            break
        return [rest[index + 1], *rest[:index], *rest[index + 2:]]
    translated: list[str] = []
    if "--selftest" in rest:
        rest.remove("--selftest")
        translated.append("selftest")
        if "--json" in rest:
            rest.remove("--json")
            translated.insert(0, "--json")
        return translated + rest
    if "--scan" in rest:
        index = rest.index("--scan")
        target = rest[index + 1] if index + 1 < len(rest) else ""
        del rest[index : index + 2]
        translated = ["ingest", "--src", target]
        if "--json" in rest:
            rest.remove("--json")
        return translated + rest
    return list(argv)


def def_verify(
    targets: Sequence[Path] | None = None,
    root: Path | None = None,
    database: Path | None = None,
    quiet: bool = True,
) -> dict[str, Any]:
    """一鍵閘門：自測 → 治理循環（AUDIT）→ 逐條斷言，回傳單一裁決。

    操作者與 CI 走同一個入口，不必記住五條指令的參數。
    """
    resolved = Path(root).resolve() if root is not None else def_resolve_root()
    sources = [Path(item) for item in (targets or [resolved / "engine"])]
    rows: list[dict[str, Any]] = []

    def record(code: str, ok: bool, detail: str, skipped: bool = False) -> None:
        status = "SKIPPED" if skipped else ("PASS" if ok else "FAIL")
        rows.append({"code": code, "status": status, "detail": detail})
        def_lamp(
            "YELLOW" if skipped else ("GREEN" if ok else "RED"), code, detail
        )

    selftest_rows = def_selftest()
    failed = [name for name, ok in selftest_rows if not ok]
    record(
        "VUE-SELFTEST",
        not failed,
        f"{len(selftest_rows) - len(failed)}/{len(selftest_rows)} 不變式"
        + (f" · 失敗 {failed[:3]}" if failed else ""),
    )
    map_path = resolved / PARAM_CAPABILITY_MAP_RELATIVE
    before = def_sha256_text(map_path.read_text(encoding="utf-8")) if map_path.is_file() else ""
    report = def_govern(
        sources, database=database, root=resolved, quiet=quiet, apply_map=False
    )
    after = def_sha256_text(map_path.read_text(encoding="utf-8")) if map_path.is_file() else ""
    record("VUE-GATE", report["gate"] == "PASS", f"govern gate {report['gate']}")
    record(
        "VUE-HYDRA",
        report["verdict"] == "SYNC_FIXABLE" and report["hydra_risk"] == "ISOLATED",
        f"{report['verdict']} · {report['hydra_risk']} · 衝突 {len(report['conflicts'])}",
    )
    record(
        "VUE-AUDIT",
        report["applied"] is False and before == after,
        "AUDIT 沒有寫入能力表" if before == after else "能力表被改動了",
    )
    record(
        "VUE-READONLY",
        report["source_mutation"] is False,
        f"source_mutation={report['source_mutation']}",
    )
    record(
        "VUE-SEAL",
        report["counts"]["sealed"] >= 1,
        f"封印 {report['counts']['sealed']}／能力 {report['counts']['capabilities']}"
        f" · 版本池 {len(report['engine_pool'])}",
    )
    ledger = report["token_ledger"]
    break_even = int(ledger["header_tokens"]) * PARAM_TOKEN_GATE_MULTIPLIER
    amortised = int(ledger["source_tokens"]) >= break_even
    record(
        "VUE-TOKEN",
        ledger["saved_percent"] >= PARAM_TOKEN_GATE_FLOOR_PERCENT,
        (
            f"省 {ledger['saved_percent']}%"
            f"（{ledger['source_tokens']} → {ledger['capsule_tokens']}）"
            if amortised
            else f"語料 {ledger['source_tokens']} token 還沒攤平 header"
                 f"（損益兩平約 {break_even}）；實測 {ledger['saved_percent']}%"
        ),
        skipped=not amortised,
    )
    verdict = "FAIL" if any(row["status"] == "FAIL" for row in rows) else "PASS"
    def_lamp("GREEN" if verdict == "PASS" else "RED", "VUE-VERIFY",
             f"{verdict} · {len(rows)} 道閘門")
    return {
        "schema": "VIA.UnifiedEngineVerify",
        "schema_version": "1.0.0",
        "engine_id": PARAM_ENGINE_ID,
        "engine_version": PARAM_ENGINE_VERSION,
        "gate": verdict,
        "rows": rows,
        "counts": report["counts"],
        "token_ledger": ledger,
        "module_exec": report["module_exec"],
    }


def def_version_card() -> dict[str, Any]:
    """引擎身份卡：規格、估算器、階段數、字典與門檻，本身就是省 token 的一張卡。"""
    return {
        "schema": "VIA.UnifiedEngineVersion",
        "engine_id": PARAM_ENGINE_ID,
        "name": PARAM_ENGINE_NAME,
        "version": PARAM_ENGINE_VERSION,
        "version_compat": list(PARAM_ENGINE_VERSION_COMPAT),
        "protocol": PARAM_PROTOCOL,
        "cme_version": PARAM_CME_VERSION,
        "map_schema_version": PARAM_MAP_SCHEMA_VERSION,
        "unified_stages": len(PARAM_UNIFIED_STAGES),
        "panoramic_stages": len(PARAM_PANORAMIC_STAGES),
        "domains": len(PARAM_CAPABILITY_DICTIONARY),
        "risk_codes": len(PARAM_RISK_TABLE),
        "probe_vectors": [name for name, _ in PARAM_PROBE_VECTORS],
        "gates": {"sandbox": PARAM_SANDBOX_GATE, "module": PARAM_MODULE_GATE},
        "estimators": {"source_text": PARAM_TOKEN_ESTIMATOR, "payload_json": "peis-json4-v1"},
        "thresholds": dict(PARAM_DEFAULT_THRESHOLDS),
        "audiences": list(PARAM_AUDIENCES),
        "capsule_protocol": PARAM_CAPSULE_PROTOCOL,
    }


def def_export_bundle(
    output: Path,
    archive: bool = False,
    verify: bool = True,
    source: Path | None = None,
) -> dict[str, Any]:
    """把引擎輸出成一份可離開本庫獨立運作的成品。

    內容：引擎本體（逐位元組複製）＋ README ＋ 空白 CME 能力表 ＋ MANIFEST。
    `verify` 會在輸出目錄以子行程跑一次匯出後的自測——證明那份複製品真的自己跑得起來，
    而不是只複製成功。
    """
    target = Path(output).resolve()
    bundle = target / PARAM_EXPORT_BUNDLE
    bundle.mkdir(parents=True, exist_ok=True)
    origin = Path(source).resolve() if source is not None else Path(__file__).resolve()
    selftest_rows = len(def_selftest())
    files: dict[str, str | bytes] = {
        # 引擎本體是位元組，不是文字：來源的換行照原樣搬過去。
        origin.name: origin.read_bytes(),
        PARAM_CAPABILITY_MAP_RELATIVE.name: (
            json.dumps(def_blank_document(), ensure_ascii=False, indent=2) + "\n"
        ),
        "README.md": PARAM_EXPORT_README.format(
            engine_id=PARAM_ENGINE_ID,
            version=PARAM_ENGINE_VERSION,
            selftest=selftest_rows,
            map_name=PARAM_CAPABILITY_MAP_RELATIVE.name,
        ),
    }
    written: list[dict[str, Any]] = []
    for name, payload in sorted(files.items()):
        def_write_atomic(bundle / name, payload)
        landed = (bundle / name).read_bytes()
        written.append({
            "name": name,
            "bytes": len(landed),
            # 雜湊實際落地的位元組，才驗得過 sha256sum／Get-FileHash
            "sha256": hashlib.sha256(landed).hexdigest(),
        })
    manifest: dict[str, Any] = {
        "schema": "VIA.UnifiedEngineBundle",
        "schema_version": "1.0.0",
        "bundle": PARAM_EXPORT_BUNDLE,
        "created_at": def_iso_now(),
        "engine": def_version_card(),
        "files": written,
        "guarantees": list(PARAM_GUARANTEES),
        "selftest": {"total": selftest_rows},
    }
    if verify:
        completed = subprocess.run(
            [sys.executable, "-I", str(bundle / origin.name), "selftest", "--json"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=PARAM_MODULE_TIMEOUT_SECONDS * 6, cwd=str(bundle), check=False,
        )
        answer: dict[str, Any] = {}
        for line in reversed((completed.stdout or "").splitlines()):
            if line.strip().startswith("{"):
                try:
                    answer = json.loads(line)
                except ValueError:
                    answer = {}
                break
        manifest["selftest"] = {
            "total": int(answer.get("total") or 0),
            "passed": int(answer.get("passed") or 0),
            "failed": list(answer.get("failed") or []),
            "exit_code": completed.returncode,
            "independent": completed.returncode == 0 and not answer.get("failed"),
        }
        if not manifest["selftest"]["independent"]:
            raise def_EngineError(
                "匯出的成品自己跑不起來："
                f"exit={completed.returncode} failed={manifest['selftest']['failed'][:3]}"
            )
    def_write_atomic(
        bundle / "MANIFEST.json",
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
    )
    manifest["path"] = str(bundle)
    if archive:
        zip_path = target / f"{PARAM_EXPORT_BUNDLE}.zip"
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as handle:
            for name in sorted([*files, "MANIFEST.json"]):
                handle.write(bundle / name, f"{PARAM_EXPORT_BUNDLE}/{name}")
        manifest["archive"] = str(zip_path)
        manifest["archive_sha256"] = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    def_lamp(
        "GREEN", "VUE-EXPORT",
        f"{len(written) + 1} 個檔案 → {bundle}"
        + (f" · selftest {manifest['selftest'].get('passed')}/"
           f"{manifest['selftest'].get('total')}" if verify else ""),
    )
    return manifest


def def_summary(report: Mapping[str, Any]) -> dict[str, Any]:
    """治理報告的精簡摘要：只留裁決、封印數與證據路徑，本身也是省 token 的一步。"""
    keys = (
        "schema", "gate", "mode", "verdict", "hydra_risk", "applied", "written",
        "capabilities", "fix_plan", "elapsed_ms", "json_report", "csv_report",
        "html_report", "lock", "status", "c", "result", "trace_id",
        "candidates_pending_dictionary", "counts", "token_ledger", "intake",
        "engine_pool", "pool_refused", "module_exec", "external_evidence",
        "rows", "delta",
    )
    return {key: report[key] for key in keys if key in report}


def def_emit(payload: Any, as_json: bool) -> None:
    if as_json:
        print(def_compact_json(payload))
        return
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))


def def_main(argv: Sequence[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    if raw and raw[0] not in PARAM_SUBCOMMANDS and raw[0].startswith("-"):
        raw = def_translate_legacy(raw)
    parser = def_build_parser()
    args = parser.parse_args(raw)
    if not args.command:
        parser.print_help()
        return 2
    try:
        if args.command == "selftest":
            rows = def_selftest()
            failed = [name for name, ok in rows if not ok]
            if args.json:
                def_emit(
                    {
                        "engine": PARAM_ENGINE_ID,
                        "passed": len(rows) - len(failed),
                        "total": len(rows),
                        "failed": failed,
                    },
                    True,
                )
            else:
                for name, ok in rows:
                    print(("PASS" if ok else "FAIL"), name)
                print(f"{len(rows) - len(failed)}/{len(rows)}")
            return 1 if failed else 0

        if args.command == "verify":
            report = def_verify(
                [Path(item) for item in args.src] if args.src else None,
                root=Path(args.root) if args.root else None,
                database=Path(args.db) if args.db else None,
                quiet=getattr(args, "quiet", False) or args.json,
            )
            def_emit(def_summary(report) if args.json else report, args.json)
            return 0 if report["gate"] == "PASS" else 1

        if args.command == "version":
            def_emit(def_version_card(), args.json)
            return 0

        if args.command == "export":
            manifest = def_export_bundle(
                Path(args.out), archive=args.zip, verify=not args.no_verify
            )
            def_emit(manifest, args.json)
            return 0

        if args.command == "handoff":
            with def_CapabilityStore(Path(args.db)) as store:
                if args.forget:
                    removed = store.forget_handoff(args.forget, args.audience)
                    def_emit(
                        {"handoff": args.forget, "audience": args.audience,
                         "forgotten": removed},
                        args.json,
                    )
                    return 0
                def_emit(
                    {
                        "audience": args.audience,
                        "handoffs": store.handoff_index(args.audience),
                    },
                    args.json,
                )
            return 0

        if args.command == "ingest":
            report = def_ingest(
                [Path(item) for item in args.src],
                database=Path(args.db) if args.db else None,
                mode=args.mode,
                threshold=args.threshold,
                root=Path(args.root) if args.root else None,
                budget_tokens=args.budget_tokens,
                audience=args.audience,
                allow_module_exec=args.allow_module_exec,
                handoff=args.handoff,
            )
            def_emit(report["capsule"] if args.capsule_only else report, args.json)
            return 0 if report["verdict"] == "PASS" else 1

        if args.command == "govern":
            report = def_govern(
                [Path(item) for item in args.src],
                database=Path(args.db) if args.db else None,
                root=Path(args.root) if args.root else None,
                mode=args.mode,
                threshold=args.threshold,
                budget_tokens=args.budget_tokens,
                audience=args.audience,
                apply_map=args.apply,
                output=Path(args.output) if args.output else None,
                quiet=getattr(args, "quiet", False) or args.json,
                allow_module_exec=args.allow_module_exec,
                evidence=Path(args.evidence) if args.evidence else None,
                handoff=args.handoff,
            )
            def_emit(def_summary(report) if args.json else report, args.json)
            return 0 if report["gate"] == "PASS" else 1

        if args.command == "expand":
            root = def_resolve_root(Path(args.root) if args.root else None)
            report = def_auto_expand(
                root=root, apply=args.apply, quiet=getattr(args, "quiet", False) or args.json
            )
            if args.output:
                report.update(def_write_reports(Path(args.output), report))
            def_emit(def_summary(report) if args.json else report, args.json)
            return 0 if report["gate"] == "PASS" else 1

        if args.command == "lock":
            missing = [
                name for name, value in (
                    ("--engine-path", args.engine_path),
                    ("--engine-id", args.engine_id),
                    ("--engine-version", args.engine_version),
                    ("--evidence", args.evidence),
                )
                if not value
            ]
            if missing:
                raise def_EngineError(f"lock 缺少參數：{missing}")
            root = def_resolve_root(Path(args.root) if args.root else None)
            report = def_run_lock(
                root=root,
                source_path=args.engine_path,
                engine_id=args.engine_id,
                version=args.engine_version,
                evidence_path=Path(args.evidence),
                entrypoint_symbol=args.entrypoint or None,
                strategy=args.strategy,
                apply=args.apply,
                quiet=getattr(args, "quiet", False) or args.json,
                capability=args.capability or None,
            )
            if args.output:
                report.update(def_write_reports(Path(args.output), report))
            def_emit(def_summary(report) if args.json else report, args.json)
            return 0 if report["gate"] == "PASS" else 1

        if args.command == "capsule":
            with def_CapabilityStore(Path(args.db)) as store:
                cards = store.cards(
                    capability=args.capability, limit=args.limit, status=args.status
                )
                statistics = store.statistics()
            delta: dict[str, Any] | None = None
            if args.handoff:
                with def_CapabilityStore(Path(args.db)) as store:
                    baseline = store.handoff_baseline(args.handoff, args.audience)
            if args.audience == "upstream":
                private: tuple[str, ...] = ()
                if args.root:
                    try:
                        private = def_collect_private_values(
                            def_load_capability_map(Path(args.root), create_if_missing=True)
                        )
                    except (OSError, ValueError, def_EngineError):
                        private = ()
                cards = [def_redact_for_upstream(card, private) for card in cards]
            if args.handoff:
                delta = def_capability_delta(cards, baseline)
                emit = set(delta["new"]) | set(delta["changed"])
                if not args.no_record:
                    with def_CapabilityStore(Path(args.db)) as store:
                        store.write_handoff(cards, args.handoff, args.audience)
                cards = [card for card in cards if str(card["cap"]) in emit]
            policy = def_capsule_policy(Path(args.root) if args.root else None)
            selected: list[dict[str, Any]] = []
            used_chars = 0
            used_tokens = 0
            truncated = ""
            for card in cards:
                if len(selected) >= int(policy["max_items"]):
                    truncated = "max_items"
                    break
                encoded = len(def_compact_json(card))
                if used_chars + encoded > int(policy["max_chars"]):
                    truncated = "max_chars"
                    break
                if args.budget_tokens is not None and used_tokens + int(
                    card["tok"]["card"]
                ) > args.budget_tokens:
                    truncated = "budget_tokens"
                    break
                selected.append(card)
                used_chars += encoded
                used_tokens += int(card["tok"]["card"])
            payload: dict[str, Any] = {
                "schema": PARAM_CAPSULE_SCHEMA,
                "schema_version": "1.0.0",
                "audience": args.audience,
                "policy": policy,
                "load_order": list(PARAM_CAPSULE_LOAD_ORDER),
                "legend": {
                    key: value for key, value in PARAM_CARD_LEGEND.items()
                    if args.audience == "governance" or key not in ("eng", "fp", "at")
                },
                "risk_legend": {
                    code: {"level": PARAM_RISK_TABLE[code][0],
                           "why": PARAM_RISK_TABLE[code][1]}
                    for code in sorted(
                        {code for card in selected for code in (card.get("risk") or [])}
                    )
                    if code in PARAM_RISK_TABLE
                },
                "counts": {"cards_total": len(cards), "cards_emitted": len(selected)},
                "store": statistics,
                "cards": selected,
                "token_ledger": {
                    "estimator": PARAM_TOKEN_ESTIMATOR,
                    "card_tokens": used_tokens,
                    "source_tokens": statistics["card_tokens"] + statistics["card_saved_tokens"],
                    "saved_tokens": statistics["card_saved_tokens"],
                },
            }
            if truncated:
                payload["truncated"] = {
                    "reason": truncated,
                    "omitted": len(cards) - len(selected),
                }
            if delta is not None:
                payload["delta"] = {
                    "protocol": PARAM_CAPSULE_PROTOCOL,
                    "handoff": args.handoff,
                    "new": delta["new"],
                    "changed": delta["changed"],
                    "retired": delta["retired"],
                    "unchanged": {
                        "count": len(delta["same"]), "digest": delta["digest"]
                    },
                    "recorded": not args.no_record,
                    "rule": "沒列在 new／changed 的能力＝上次那張卡仍然有效",
                }
                if args.diff:
                    payload.pop("cards", None)
                    payload.pop("legend", None)
                    payload.pop("risk_legend", None)
            if args.audience == "governance":
                payload["engine"] = {
                    "id": PARAM_ENGINE_ID,
                    "name": PARAM_ENGINE_NAME,
                    "version": PARAM_ENGINE_VERSION,
                    "protocol": PARAM_PROTOCOL,
                    "mode": "plugin" if args.root else "independent",
                }
            else:
                payload["protocol"] = PARAM_PROTOCOL
                payload["cme_version"] = PARAM_CME_VERSION
                def_assert_blackbox(payload, {})
            def_emit(payload, args.json)
            return 0

        if args.command == "run":
            if not args.db and not args.root:
                raise def_EngineError("run 需要 --db（沙箱）或 --root（能力表）其中之一")
            arguments = None
            if args.args:
                arguments = json.loads(args.args)
                if not isinstance(arguments, list):
                    arguments = [arguments]
            answer = def_run_capability(
                args.capability,
                arguments,
                database=Path(args.db) if args.db else None,
                root=Path(args.root) if args.root else None,
                params=json.loads(args.params) if args.params else None,
                audience=args.audience,
                allow_execution=not args.no_execute,
            )
            if getattr(args, "output", None):
                target = Path(args.output)
                target.mkdir(parents=True, exist_ok=True)
                def_write_atomic(
                    target / "via-unified-run.json",
                    json.dumps(answer, ensure_ascii=False, indent=2, default=str) + "\n",
                )
            def_emit(answer, args.json)
            return 0 if answer.get("status", "GREEN") == "GREEN" else 1

        if args.command == "query":
            columns = [item.strip() for item in args.columns.split(",") if item.strip()]
            with def_CapabilityStore(Path(args.db)) as store:
                rows = store.cards(
                    capability=args.capability, columns=columns, limit=args.limit
                )
            def_emit({"columns": columns, "rows": rows, "count": len(rows)}, args.json)
            return 0

        if args.command == "manifest":
            def_emit(
                def_plugin_manifest(
                    root=Path(args.root) if args.root else None,
                    database=Path(args.db) if args.db else None,
                ),
                args.json,
            )
            return 0

        if args.command == "report":
            if not args.db and not args.root:
                raise def_EngineError("report 需要 --db（能力庫）或 --root（能力表）其中之一")
            statistics: dict[str, Any] = {}
            sealed: list[dict[str, str]] = []
            if args.db:
                with def_CapabilityStore(Path(args.db)) as store:
                    statistics = store.statistics()
                    sealed = store.sealed_capabilities()
            source_tokens = (
                statistics.get("card_tokens", 0) + statistics.get("card_saved_tokens", 0)
            )
            capability_map: dict[str, Any] = {}
            if args.root:
                document = def_load_capability_map(Path(args.root), create_if_missing=True)
                capability_map = {
                    "cme_version": document.get("cme_version"),
                    "capabilities": sorted(
                        record["capability"]
                        for record in document.get("capabilities", [])
                    ),
                    "performance_matrix": def_performance_matrix(document),
                    "version_pool": def_version_pool(document),
                    "pae": def_build_pae(document),
                }
            def_emit(
                {
                    **({"capability_map": capability_map} if capability_map else {}),
                    "schema": PARAM_REPORT_SCHEMA,
                    "schema_version": "1.0.0",
                    "engine": PARAM_ENGINE_ID,
                    "store": statistics,
                    "sealed": sealed,
                    "token_ledger": {
                        "estimator": PARAM_TOKEN_ESTIMATOR,
                        "source_tokens": source_tokens,
                        "card_tokens": statistics.get("card_tokens", 0),
                        "saved_tokens": statistics.get("card_saved_tokens", 0),
                        "saved_percent": (
                            round(
                                100.0 * statistics.get("card_saved_tokens", 0) / source_tokens, 2
                            )
                            if source_tokens
                            else 0.0
                        ),
                        "dedup_tokens": statistics.get("dedup_tokens", 0),
                    },
                },
                args.json,
            )
            return 0
    except def_EngineError as error:
        print(f"RED {error}", file=sys.stderr)
        return 1
    except (OSError, ValueError) as error:
        print(f"RED {error.__class__.__name__}: {error}", file=sys.stderr)
        return 1
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(def_main())
