#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===== [VRN:ID:v0100] VRN-ENG019 · VRN_RunCache_v0100 v0100 · ENGINE =====
# AST 注入（只加註解，AST 不變）：類別 2 · 函式 36；逐一編號在 ssot/VRN_ID_SSOT_v0100.json
# ===== [VRN:ID:END] =====
"""
VRN_RunCache v0100 -- what a run already read is kept in TEMP and used again until its inputs change.

Operator 2026-10-13: 「上面指令執行速度太慢 確認所有PS都有加速器 善用TEMP強力支援不足的記憶體 過去跑過的資料在輸入還沒換之前
不要刪除 TEMP 避免重跑 再進行前檢視一下CPU/記憶體/TEMP加總的能力 在不影響指令系統不產生九頭龍風險下進行六個獨立步驟同時跑」

What is cached (each is a pure function of its key; the answer is the same bytes the engine gave last time):
  focus       G19 聚焦副本與清單          key: every original (relative name + SHA-256) · VRN_Focus / TitleTrim / PageRegions / mother engines (AST)
  batch       G06 入庫、G08 冪等（資料夾）  key: input files (name + SHA) · output folder before the call (out path masked) · arguments ·
                                            database / first-page / evidence-core / local-DB / ticker-master code (AST) · books · local DB file
  first_page  G07 首頁引擎（逐檔）          key: file name + SHA · first-page / evidence-core / ticker-master code · books
  regions     G15 版面還原（逐檔）          key: file name + SHA · PageRegions + mother engines code · books
  sample_sha  P07 樣本 SHA-256             key: path + size + modified time (the git index rule): a file not touched is not read again

The key also carries the Python and library versions (PyMuPDF, pdfplumber, pdfminer, pandas, pyarrow, numpy, python-docx, duckdb)
and the VRN / VIA environment variables that steer an engine (local SSOT, local DB, network).  Code is fingerprinted by its AST, so
the ID comments injected by build do not invalidate anything; books by canonical JSON (CRLF and key order do not count).

Books: a step depends on every file under ssot/, knowledge/ and references/ except the books it does not read (measured
2026-10-13 by tracking every file opened during a run): the per-round generated books (IDs, index, engine lock, regex, synonym,
ticker record, output headers, TEMP policy) and, for G06 入庫 and G07 首頁, the TitleTrim book
(G15 版面還原 does read it: focus_book() takes doc_class_policy from there).  A book outside that list
changing invalidates the step: slower, never stale.

Where: <TEMP 根>/VRN_Main/cache (TEMP 根 = VIA_TEMP_ROOT, else %LOCALAPPDATA%\\Temp\\VIA_progress -- the same root as
VRN_TempStore); the TEMP sweep only ever deletes run_* folders, so the cache outlives runs.  VRN_CACHE_HOME overrides; a home
inside the VRN tree is refused.  One run at a time holds the cache (file lock); a second run at the same time runs uncached.

Deletion (ssot/VRN_TEMP_POLICY_v0100.json "cache"): an entry stays while its inputs are the current inputs.  When the samples
change, the entries and focus copies of all but the newest previous sample set are deleted; within the current sample set, the
entries a step did not use this run (an older engine version) are deleted; over the budget (25% of the free TEMP disk, at most
VIA_CACHE_MAX_GB, default 10) the least recently used go first.  Every deletion is a line in <cache>/purge_ledger.jsonl.

Resources (cache_resources): CPU cores, memory total / available, TEMP free space and the cache size, and from them the number of
worker processes (one core left free; about 0.6 GB per worker; at most 8) and the cache budget.
"""

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

import argparse
import gzip
import hashlib
import importlib.util
import io
import json
import os
import pickle
import platform
import shutil
import sys
import tempfile
import threading
import time
import zipfile
from pathlib import Path

CACHE_VERSION = "v0100"
VRN_ROOT = Path(__file__).resolve().parents[1]
CODE = {
    "focus": ["engine/VRN_Focus_v0100.py", "engine/VRN_TitleTrim_v0100.py", "engine/VRN_PageRegions_v0100.py", "engine/mother/*.py"],
    "batch": ["engine/VRN_Integrated_ReportDatabase_Engine.py", "engine/VIA_VRN_FirstPageEngine.py", "engine/VRN_Evidence_Core.py",
              "engine/VRN_LocalDB_v0100.py", "engine/VIA_TW_Ticker_Master_v0210.py"],
    "first_page": ["engine/VIA_VRN_FirstPageEngine.py", "engine/VRN_Evidence_Core.py", "engine/VIA_TW_Ticker_Master_v0210.py"],
    "regions": ["engine/VRN_PageRegions_v0100.py", "engine/mother/*.py"],
}
DATA_DIRS = ("ssot", "knowledge", "references")
DATA_NOT_READ = {                       # generated every round, read by none of the cached steps (measured 2026-10-13)
    "ssot/VRN_ID_SSOT_v0100.json", "ssot/VRN_SSOT_INDEX_v0100.json", "ssot/VRN_EngineLock_SSOT_v0100.json",
    "ssot/VRN_REGEX_SSOT_v0100.json", "ssot/VRN_SYNONYM_SSOT_v0100.json", "ssot/VRN_TickerRecord_SSOT_v0100.json",
    "ssot/VRN_TEMP_POLICY_v0100.json", "ssot/VRN_Output_Header_SSOT_v0100.json", "ssot/VRN_Output_Header_SSOT_v0101.json",
    "ssot/VRN_Output_Header_SSOT_v0102.json", "ssot/VRN_Output_Header_SSOT_v0103.json", "ssot/VRN_Output_Header_SSOT_v0104.json",
    "ssot/VRN_Output_Header_SSOT_v0105.json",
}
# 實測 2026-10-20：`regions` 原本也列在這裡，說它不讀 TitleTrim 冊 —— 但 `VRN_PageRegions_v0100.py` 的
# `focus_book()` 讀的就是它，而那裡住著 `doc_class_policy`：決定一份報告走 FULL／COVERAGE／REGISTER／SKIP，
# 也就是到底要不要處理。把 INDUSTRY_OUTLOOK 從 COVERAGE 改成 SKIP，focus 的鑰匙變了、regions 的一個字沒變 ——
# 改冊之後 regions 會 serve 舊答案。batch（ENG002）與 first_page（FPE）真的沒讀這本，照舊跳過。
DATA_NOT_READ_BY = {"batch": {"ssot/VRN_TitleTrim_SSOT_v0100.json"}, "first_page": {"ssot/VRN_TitleTrim_SSOT_v0100.json"},
                    "regions": set(), "focus": set()}
LIBS = ("pymupdf", "PyMuPDF", "pdfplumber", "pdfminer.six", "pandas", "pyarrow", "numpy", "python-docx", "duckdb")
ENV_KEYS = ("VRN_LOCAL_SSOT", "VRN_LOCALDB", "VIA_DB_VDF_TW_MARKET", "VIA_DATA_HOME", "VIA_NET", "VIA_LIVE", "VIA_NET_CONSENT",
            "VIA_SCRAPE_CONSENT", "VRN_REGIONS_INPROC")
TEXT_SUFFIXES = (".json", ".jsonl", ".csv", ".html", ".htm", ".txt", ".md")
LEDGER = "purge_ledger.jsonl"
INDEX = "cache_index.json"
STAT_MEMO = "sample_sha_memo.json"
FOCUS_COPIES = "focus_copies"            # the focus copies of a sample set (not the "focus" step's entries, which live in "focus/")
_LOAD_LOCK = threading.RLock()


# =====================================================================
# 1 . WHERE, AND WHAT THE MACHINE CAN TAKE
# =====================================================================
# [VRN-ID] VRN-ENG019-FNC001 · LOGIC
def cache_temp_root():
    """The TEMP root VRN_TempStore uses (VIA_TEMP_ROOT, else %LOCALAPPDATA%\\Temp\\VIA_progress, else the system temp)."""
    r = os.environ.get("VIA_TEMP_ROOT")
    if r:
        return Path(r)
    if os.environ.get("LOCALAPPDATA"):
        return Path(os.environ["LOCALAPPDATA"]) / "Temp" / "VIA_progress"
    run = os.environ.get("VRN_TEMP_RUN")                 # a TEMP run is open: tempfile points into run_*, the root is two levels up
    if run and Path(run).name.startswith("run_"):
        return Path(run).parent.parent
    return Path(tempfile.gettempdir()) / "Temp" / "VIA_progress"


# [VRN-ID] VRN-ENG019-FNC002 · LOGIC
def cache_home(explicit=""):
    """(home, why).  explicit > VRN_CACHE_HOME > <TEMP 根>/VRN_Main/cache; inside the VRN tree -> (None, why)."""
    if explicit:
        home, why = Path(explicit), "--cache-home"
    elif os.environ.get("VRN_CACHE_HOME"):
        home, why = Path(os.environ["VRN_CACHE_HOME"]), "VRN_CACHE_HOME"
    else:
        home, why = cache_temp_root() / "VRN_Main" / "cache", "TEMP 根"
    try:
        home.resolve().relative_to(VRN_ROOT.resolve())
        return None, f"快取不放進 VRN 資料夾：{home}"
    except ValueError:
        pass
    return home, why


# [VRN-ID] VRN-ENG019-FNC003 · LOGIC
def cache_memory():
    """(total, available) bytes; psutil when present, else the OS (Windows GlobalMemoryStatusEx, Linux /proc/meminfo)."""
    try:
        import psutil  # type: ignore
        vm = psutil.virtual_memory()
        return int(vm.total), int(vm.available)
    except Exception:  # noqa: BLE001
        pass
    if os.name == "nt":
        try:
            import ctypes

            # [VRN-ID] VRN-ENG019-CLS001 · CLASS
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong), ("ullTotalPhys", ctypes.c_ulonglong),
                            ("ullAvailPhys", ctypes.c_ulonglong), ("ullTotalPageFile", ctypes.c_ulonglong),
                            ("ullAvailPageFile", ctypes.c_ulonglong), ("ullTotalVirtual", ctypes.c_ulonglong),
                            ("ullAvailVirtual", ctypes.c_ulonglong), ("sullAvailExtendedVirtual", ctypes.c_ulonglong)]
            st = MEMORYSTATUSEX()
            st.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st)):
                return int(st.ullTotalPhys), int(st.ullAvailPhys)
        except Exception:  # noqa: BLE001
            pass
    try:
        info = {}
        for line in Path("/proc/meminfo").read_text().splitlines():
            k, v = line.split(":", 1)
            info[k] = int(v.strip().split()[0]) * 1024
        return info.get("MemTotal", 0), info.get("MemAvailable", info.get("MemFree", 0))
    except Exception:  # noqa: BLE001
        return 0, 0


# [VRN-ID] VRN-ENG019-FNC004 · LOGIC
def cache_size(home):
    total = 0
    if home and Path(home).is_dir():
        for p in Path(home).rglob("*"):
            try:
                if p.is_file():
                    total += p.stat().st_size
            except OSError:
                pass
    return total


# [VRN-ID] VRN-ENG019-FNC005 · LOGIC
def cache_resources(home=None):
    """CPU, memory, TEMP disk and the cache -> how many worker processes and how big a cache this machine takes."""
    cpu = os.cpu_count() or 1
    mem_total, mem_avail = cache_memory()
    root = Path(home) if home else cache_temp_root()
    probe = root
    while not probe.exists() and probe.parent != probe:
        probe = probe.parent
    try:
        disk = shutil.disk_usage(str(probe))
        free, disk_total = disk.free, disk.total
    except OSError:
        free, disk_total = 0, 0
    # 2026-10-18：預算改成可調，而且要說出**誰是瓶頸** —— 操作員問「記憶體不夠時怎麼用 TEMP 補」，
    # 第一步是讓他看得到現在卡在哪一項，不然調哪個旋鈕都是猜的。不給環境變數時，數字與舊版完全相同。
    per_gb = cache_env_num("VIA_VRN_WORKER_GB", 0.6, 0.05, 64.0)
    per_worker = int(per_gb * (1 << 30))
    by_cpu = cpu - 1 if cpu > 2 else cpu            # 留一核給本行程與作業系統
    by_mem = int(max(1, mem_avail // per_worker)) if mem_avail else cpu
    ceiling = int(cache_env_num("VIA_VRN_WORKERS_MAX", 8, 1, 256))
    workers = int(max(1, min(by_cpu, by_mem, ceiling)))
    forced = int(cache_env_num("VIA_VRN_WORKERS", 0, 0, 256))
    if forced:
        workers = forced
        hold = f"VIA_VRN_WORKERS 指定 {forced}"
    else:
        hold = ("CPU" if by_cpu <= by_mem and by_cpu <= ceiling
                else ("記憶體" if by_mem <= ceiling else "上限"))
    share = cache_env_num("VIA_CACHE_SHARE", 0.25, 0.01, 0.9)
    cap = cache_env_num("VIA_CACHE_MAX_GB", 10, 0.1, 1024) * (1 << 30)
    budget = int(min(cap, share * free)) if free else int(cap)
    used = cache_size(home) if home else 0
    gb = lambda b: round(b / (1 << 30), 1)  # noqa: E731
    return {"cpu": cpu, "mem_total_gb": gb(mem_total), "mem_avail_gb": gb(mem_avail), "temp_free_gb": gb(free), "temp_total_gb": gb(disk_total),
            "cache_gb": gb(used), "workers": workers, "budget_gb": gb(budget), "budget_bytes": budget,
            "by_cpu": by_cpu, "by_mem": by_mem, "ceiling": ceiling, "per_worker_gb": per_gb, "bottleneck": hold,
            "why": f"子行程 {workers} 支，卡在{hold}（CPU 給 {by_cpu}、記憶體給 {by_mem} 支＝每支 {per_gb} GB、上限 {ceiling}）"
                   f" · 快取上限 = TEMP 剩餘的 {round(share * 100)}%（最多 {gb(cap)} GB）"
                   f" · 要調：VIA_VRN_WORKERS／VIA_VRN_WORKER_GB／VIA_VRN_WORKERS_MAX／VIA_CACHE_SHARE／VIA_CACHE_MAX_GB"}


# =====================================================================
# 2 . FINGERPRINTS
# =====================================================================
# [VRN-ID] VRN-ENG019-FNC036 · LOGIC
def cache_env_num(name, default, low, high):
    """環境變數讀成數字，夾在 [low, high] 之間；讀不懂或超出範圍就用預設，不讓一個打錯的值把整輪搞砸。"""
    raw = (os.environ.get(name) or "").strip()
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    if value != value or value in (float("inf"), float("-inf")):   # NaN／無限大
        return default
    return min(high, max(low, value))


# [VRN-ID] VRN-ENG019-FNC006 · LOGIC
def cache_file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


# [VRN-ID] VRN-ENG019-FNC007 · LOGIC
def cache_lock_module():
    with _LOAD_LOCK:
        name = "vrn_runcache_lock"
        if name in sys.modules:
            return sys.modules[name]
        spec = importlib.util.spec_from_file_location(name, VRN_ROOT / "engine" / "VRN_Lock_v0100.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        return mod


# [VRN-ID] VRN-ENG019-FNC008 · LOGIC
def cache_code_files(step):
    out = []
    for pat in CODE.get(step, []):
        if "*" in pat:
            out += sorted(p.relative_to(VRN_ROOT).as_posix() for p in VRN_ROOT.glob(pat) if p.is_file())
        else:
            out.append(pat)
    return out


# [VRN-ID] VRN-ENG019-FNC009 · LOGIC
def cache_data_files(step):
    skip = DATA_NOT_READ | DATA_NOT_READ_BY.get(step, set())
    out = []
    for d in DATA_DIRS:
        base = VRN_ROOT / d
        if base.is_dir():
            for p in sorted(base.rglob("*")):
                rel = p.relative_to(VRN_ROOT).as_posix()
                if p.is_file() and rel not in skip and "__pycache__" not in rel:
                    out.append(rel)
    return out


# [VRN-ID] VRN-ENG019-FNC010 · LOGIC
def cache_versions():
    try:
        from importlib import metadata
    except Exception:  # noqa: BLE001
        metadata = None
    libs = {}
    for name in LIBS:
        try:
            libs[name] = metadata.version(name) if metadata else ""
        except Exception:  # noqa: BLE001
            libs[name] = ""
    return {"python": platform.python_version(), "impl": platform.python_implementation(), "os": os.name, "libs": libs}


# [VRN-ID] VRN-ENG019-FNC011 · LOGIC
def cache_env():
    return {k: os.environ.get(k, "") for k in ENV_KEYS}


# [VRN-ID] VRN-ENG019-FNC012 · LOGIC
def cache_localdb_signature():
    """The local market DB the database engine would open (VRN_LocalDB.candidates()[0]): path, size, modified time."""
    try:
        with _LOAD_LOCK:
            name = "vrn_runcache_localdb"
            mod = sys.modules.get(name)
            if mod is None:
                spec = importlib.util.spec_from_file_location(name, VRN_ROOT / "engine" / "VRN_LocalDB_v0100.py")
                mod = importlib.util.module_from_spec(spec)
                sys.modules[name] = mod
                spec.loader.exec_module(mod)
        found = mod.candidates()
        if not found:
            return {"path": "", "size": 0, "mtime_ns": 0}
        if found[0].is_dir():                              # the vdf_database parquet folder: every file it reads
            files = {}
            for fname in sorted(getattr(mod, "PARQUET_FILES", {}).values()):
                p = found[0] / fname
                if p.is_file():
                    st = p.stat()
                    files[fname] = [st.st_size, st.st_mtime_ns]
            return {"path": str(found[0]), "files": files}
        st = found[0].stat()
        return {"path": str(found[0]), "size": st.st_size, "mtime_ns": st.st_mtime_ns}
    except Exception as error:  # noqa: BLE001
        return {"path": "", "error": error.__class__.__name__}


# =====================================================================
# 3 . THE CACHE
# =====================================================================
# [VRN-ID] VRN-ENG019-FNC013 · LOGIC
def cache_try_lock(handle):
    try:
        handle.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except OSError:
        return False


# [VRN-ID] VRN-ENG019-CLS002 · CLASS
class RunCache:
    """One run's view of the cache.  Every method is safe to call when the cache is disabled (it then misses)."""

    # [VRN-ID] VRN-ENG019-FNC014 · INIT
    def __init__(self, home=None, budget_bytes=None, enabled=True, why=""):
        self.home = Path(home) if home else None
        self.enabled = bool(enabled and self.home is not None)
        self.why = why
        self.stats = {}
        self.used = set()
        self.scope = ""
        self.handle = None
        self.budget = budget_bytes
        self.index = {}
        self._fp = {}
        self._steps = {}
        self._lock = threading.RLock()
        if self.enabled:
            try:
                self.home.mkdir(parents=True, exist_ok=True)
                self.handle = open(self.home / ".cache.lock", "a+b")
                if not cache_try_lock(self.handle):
                    self.enabled, self.why = False, "另一個 VRN 正在用快取：這一輪不用快取（照常全部重跑）"
                    self.handle.close()
                    self.handle = None
            except OSError as error:
                self.enabled, self.why = False, f"快取夾不能用：{error}"
        if self.enabled:
            try:
                self.index = json.loads((self.home / INDEX).read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                self.index = {}

    # -- keys ------------------------------------------------------------
    # [VRN-ID] VRN-ENG019-FNC015 · LOGIC
    def cache_fingerprint(self, rel):
        with self._lock:
            if rel not in self._fp:
                L = cache_lock_module()
                self._fp[rel] = L.fingerprint(rel).get("sha256", "")
            return self._fp[rel]

    # [VRN-ID] VRN-ENG019-FNC016 · LOGIC
    def cache_step_parts(self, step):
        """Everything a step's answer depends on besides its own input files."""
        with self._lock:
            if step not in self._steps:
                parts = {"code": {r: self.cache_fingerprint(r) for r in cache_code_files(step)},
                         "data": {r: self.cache_fingerprint(r) for r in cache_data_files(step)},
                         "versions": cache_versions(), "env": cache_env(), "cache": CACHE_VERSION}
                if step == "batch":
                    parts["localdb"] = cache_localdb_signature()
                self._steps[step] = hashlib.sha256(json.dumps(parts, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
            return self._steps[step]

    # [VRN-ID] VRN-ENG019-FNC017 · LOGIC
    def cache_key(self, step, parts):
        blob = json.dumps({"step": step, "deps": self.cache_step_parts(step), "parts": parts}, sort_keys=True, ensure_ascii=False, default=str)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    # -- entries ---------------------------------------------------------
    # [VRN-ID] VRN-ENG019-FNC018 · LOGIC
    def cache_path(self, step, key, suffix=".pkl.gz"):
        return self.home / step / key[:2] / (key + suffix)

    # [VRN-ID] VRN-ENG019-FNC019 · LOGIC
    def cache_count(self, step, what, seconds=0.0):
        with self._lock:
            s = self.stats.setdefault(step, {"hit": 0, "miss": 0, "saved_seconds": 0.0, "stored": 0})
            s[what] += 1
            if what == "hit":
                s["saved_seconds"] = round(s["saved_seconds"] + float(seconds or 0.0), 2)

    # [VRN-ID] VRN-ENG019-FNC020 · LOGIC
    def cache_get(self, step, key):
        if not self.enabled:
            return None
        path = self.cache_path(step, key)
        try:
            with gzip.open(path, "rb") as fh:
                obj = pickle.load(fh)
        except Exception:  # noqa: BLE001
            self.cache_count(step, "miss")
            return None
        meta = self.index.get(f"{step}/{key}") or {}
        self.cache_count(step, "hit", meta.get("seconds", 0.0))
        with self._lock:
            self.used.add(f"{step}/{key}")
            meta.update(used=time.time(), scope=meta.get("scope") or self.scope)
            self.index[f"{step}/{key}"] = meta
        return obj

    # [VRN-ID] VRN-ENG019-FNC021 · LOGIC
    def cache_put(self, step, key, obj, seconds=0.0):
        if not self.enabled:
            return False
        path = self.cache_path(step, key)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_name(path.name + f".{os.getpid()}.{threading.get_ident()}.tmp")
            with gzip.open(tmp, "wb", compresslevel=3) as fh:
                pickle.dump(obj, fh, protocol=4)
            os.replace(tmp, path)
        except Exception:  # noqa: BLE001
            return False
        with self._lock:
            self.used.add(f"{step}/{key}")
            self.index[f"{step}/{key}"] = {"scope": self.scope, "used": time.time(), "bytes": path.stat().st_size, "seconds": round(seconds, 2)}
            self.stats.setdefault(step, {"hit": 0, "miss": 0, "saved_seconds": 0.0, "stored": 0})["stored"] += 1
        return True

    # -- folders (G06 / G08: the database engine writes a folder) -----------
    # [VRN-ID] VRN-ENG019-FNC022 · LOGIC
    def cache_folder_digest(self, folder, mask=""):
        """name + SHA of every file; text files hashed with `mask` (the output path) replaced, so a run's own path does not count."""
        folder = Path(folder)
        rows = []
        if folder.is_dir():
            masks = cache_path_forms(mask) if mask else []
            for p in sorted(folder.rglob("*")):
                if not p.is_file():
                    continue
                rel = p.relative_to(folder).as_posix()
                if masks and p.suffix.lower() in TEXT_SUFFIXES:
                    text = p.read_bytes().decode("utf-8", errors="surrogateescape")
                    for m in masks:
                        text = text.replace(m, "<OUT>")
                    rows.append([rel, hashlib.sha256(text.encode("utf-8", errors="surrogateescape")).hexdigest()])
                else:
                    rows.append([rel, cache_file_sha256(p)])
        return rows

    # [VRN-ID] VRN-ENG019-FNC023 · LOGIC
    def cache_folder_store(self, step, key, folder, result, seconds=0.0):
        """Snapshot `folder` (zip) with the call's result; the folder's own path is remembered to rewrite on restore."""
        if not self.enabled:
            return False
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=3) as z:
            for p in sorted(Path(folder).rglob("*")):
                if p.is_file():
                    z.write(p, p.relative_to(folder).as_posix())
        return self.cache_put(step, key, {"zip": buf.getvalue(), "result": result, "root": str(Path(folder))}, seconds)

    # [VRN-ID] VRN-ENG019-FNC024 · LOGIC
    def cache_folder_restore(self, step, key, folder):
        """Put the snapshot back into `folder` (emptied first); the old path inside text files and the result becomes the new one."""
        got = self.cache_get(step, key)
        if got is None:
            return None
        folder = Path(folder)
        if folder.exists():
            shutil.rmtree(folder)
        folder.mkdir(parents=True)
        pairs = list(zip(cache_path_forms(got["root"]), cache_path_forms(str(folder))))
        with zipfile.ZipFile(io.BytesIO(got["zip"])) as z:
            for name in z.namelist():
                data = z.read(name)
                dst = folder / name
                dst.parent.mkdir(parents=True, exist_ok=True)
                if Path(name).suffix.lower() in TEXT_SUFFIXES:
                    text = data.decode("utf-8", errors="surrogateescape")
                    for old, new in pairs:
                        text = text.replace(old, new)
                    data = text.encode("utf-8", errors="surrogateescape")
                dst.write_bytes(data)
        result = got["result"]
        try:
            text = json.dumps(result, ensure_ascii=False)
            for old, new in pairs:
                text = text.replace(old, new)
            result = json.loads(text)
        except (TypeError, ValueError):
            pass
        return {"result": result}

    # -- sample SHA memo (P07, G19) ----------------------------------------
    # [VRN-ID] VRN-ENG019-FNC025 · LOGIC
    def cache_sample_sha(self, paths, mapper=None):
        """SHA-256 of each file; a file whose size and modified time are unchanged is not read again."""
        memo = {}
        if self.enabled:
            try:
                memo = json.loads((self.home / STAT_MEMO).read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                memo = {}
        out, todo = [None] * len(paths), []
        for i, p in enumerate(paths):
            try:
                st = Path(p).stat()
            except OSError:
                continue
            m = memo.get(str(p))
            if m and m[0] == st.st_size and m[1] == st.st_mtime_ns:
                out[i] = m[2]
            else:
                todo.append((i, p, st))
        if todo:
            shas = (mapper or (lambda fn, items: [fn(x) for x in items]))(cache_file_sha256, [p for _i, p, _st in todo])
            for (i, p, st), sha in zip(todo, shas):
                out[i] = sha
                memo[str(p)] = [st.st_size, st.st_mtime_ns, sha]
        self.cache_count("sample_sha", "hit" if not todo else "miss")
        with self._lock:
            s = self.stats.setdefault("sample_sha", {"hit": 0, "miss": 0, "saved_seconds": 0.0, "stored": 0})
            s.update(files=len(paths), reread=len(todo))
        if self.enabled:
            try:
                tmp = self.home / (STAT_MEMO + f".{os.getpid()}.tmp")
                tmp.write_text(json.dumps(memo, ensure_ascii=False), encoding="utf-8")
                os.replace(tmp, self.home / STAT_MEMO)
            except OSError:
                pass
        return out

    # [VRN-ID] VRN-ENG019-FNC026 · LOGIC
    def cache_scope_of(self, listing):
        """The sample set as one id: every (relative name, SHA)."""
        self.scope = hashlib.sha256(json.dumps(sorted(listing), ensure_ascii=False).encode("utf-8")).hexdigest()[:16]
        return self.scope

    # [VRN-ID] VRN-ENG019-FNC027 · LOGIC
    def cache_focus_folder(self):
        """Focus copies live with the cache under the sample set's id: the same path while the samples are the same."""
        return (self.home / FOCUS_COPIES / (self.scope or "none")) if self.enabled else None

    # -- deletion ------------------------------------------------------------
    # [VRN-ID] VRN-ENG019-FNC028 · LOGIC
    def cache_purge(self, path, rule):
        size = cache_size(path) if Path(path).is_dir() else (Path(path).stat().st_size if Path(path).exists() else 0)
        try:
            if Path(path).is_dir():
                shutil.rmtree(path)
            elif Path(path).exists():
                Path(path).unlink()
        except OSError:
            return 0
        try:
            with open(self.home / LEDGER, "a", encoding="utf-8") as fh:
                fh.write(json.dumps({"time": time.strftime("%Y-%m-%dT%H:%M:%S"), "path": str(path), "mb": round(size / (1 << 20), 2),
                                     "rule": rule}, ensure_ascii=False) + "\n")
        except OSError:
            pass
        return size

    # [VRN-ID] VRN-ENG019-FNC029 · LOGIC
    def cache_prune(self):
        """Keep the current sample set and the newest previous one; drop entries a step replaced this run; then the budget."""
        if not self.enabled:
            return {"deleted": 0, "mb": 0.0}
        deleted, freed = 0, 0
        scopes = {}
        for k, m in self.index.items():
            sc = m.get("scope") or ""
            scopes[sc] = max(scopes.get(sc, 0), m.get("used", 0))
        keep = {self.scope} | {s for s, _t in sorted(((s, t) for s, t in scopes.items() if s != self.scope), key=lambda st: -st[1])[:1]}
        touched = {k.split("/", 1)[0] for k in self.used}
        for k in list(self.index):
            m = self.index[k]
            step, key = k.split("/", 1)
            rule = ""
            if (m.get("scope") or "") not in keep:
                rule = "樣本換了（保留現在與上一組）"
            elif m.get("scope") == self.scope and step in touched and k not in self.used and step != "focus":
                rule = "同一組樣本、引擎或冊改了：舊答案用不到"
            if rule:
                freed += self.cache_purge(self.cache_path(step, key), rule)
                deleted += 1
                self.index.pop(k, None)
        focus_root = self.home / FOCUS_COPIES
        if focus_root.is_dir():
            for d in focus_root.iterdir():
                if d.is_dir() and d.name not in keep:
                    freed += self.cache_purge(d, "樣本換了：舊的聚焦副本")
                    deleted += 1
        if self.budget:
            total = cache_size(self.home)
            for k, m in sorted(self.index.items(), key=lambda kv: kv[1].get("used", 0)):
                if total <= self.budget:
                    break
                if k in self.used:
                    continue
                step, key = k.split("/", 1)
                got = self.cache_purge(self.cache_path(step, key), "超過快取上限：最久沒用的先刪")
                total -= got
                freed += got
                deleted += 1
                self.index.pop(k, None)
        return {"deleted": deleted, "mb": round(freed / (1 << 20), 1)}

    # [VRN-ID] VRN-ENG019-FNC030 · LOGIC
    def cache_close(self):
        pruned = self.cache_prune() if self.enabled else {"deleted": 0, "mb": 0.0}
        if self.enabled:
            try:
                tmp = self.home / (INDEX + f".{os.getpid()}.tmp")
                tmp.write_text(json.dumps(self.index, ensure_ascii=False), encoding="utf-8")
                os.replace(tmp, self.home / INDEX)
            except OSError:
                pass
        if self.handle is not None:
            try:
                self.handle.close()
            except OSError:
                pass
            self.handle = None
        return pruned

    # [VRN-ID] VRN-ENG019-FNC031 · LOGIC
    def cache_summary(self):
        saved = round(sum(s.get("saved_seconds", 0.0) for s in self.stats.values()), 1)
        return {"enabled": self.enabled, "home": str(self.home or ""), "why": self.why, "scope": self.scope, "steps": self.stats,
                "saved_seconds": saved, "entries": len(self.index)}


# [VRN-ID] VRN-ENG019-FNC032 · LOGIC
def cache_path_forms(path):
    """A path as it can appear inside a text file: as is, JSON-escaped (Windows backslashes doubled) and with forward slashes."""
    s = str(path)
    forms = [s, json.dumps(s, ensure_ascii=False)[1:-1], s.replace("\\", "/")]
    return list(dict.fromkeys(f for f in forms if f))


# [VRN-ID] VRN-ENG019-FNC033 · LOGIC
def cache_open(explicit="", enabled=True):
    """The run's cache, or a disabled one (with the reason) -- never an exception."""
    if not enabled:
        return RunCache(None, enabled=False, why="--no-cache：這一輪全部重跑")
    home, why = cache_home(explicit)
    if home is None:
        return RunCache(None, enabled=False, why=why)
    res = cache_resources(home)
    return RunCache(home, budget_bytes=res["budget_bytes"], why=why)


# =====================================================================
# 4 . SELFTEST / CLI
# =====================================================================
# [VRN-ID] VRN-ENG019-FNC034 · ENTRY
def selftest(verbose=True):
    checks = []
    with tempfile.TemporaryDirectory(prefix="vrn_cache_") as td:
        td = Path(td)
        c = RunCache(td / "cache", budget_bytes=50 << 20)
        checks.append(("開得起來、拿到鎖", c.enabled, c.why))
        c.cache_scope_of([["s0.pdf", "sha-of-the-current-samples"]])   # a run names its sample set before anything is stored
        second = RunCache(td / "cache")
        checks.append(("同時第二個 VRN：不用快取（照常重跑），不會互相蓋", not second.enabled and "另一個" in second.why, second.why))
        second.cache_close()
        k1 = c.cache_key("first_page", {"name": "a.pdf", "sha": "1"})
        k2 = c.cache_key("first_page", {"name": "a.pdf", "sha": "1"})
        k3 = c.cache_key("first_page", {"name": "a.pdf", "sha": "2"})
        checks.append(("鑰匙固定：同輸入同鑰匙，檔案一變就換", k1 == k2 and k1 != k3, (k1[:8], k3[:8])))
        checks.append(("不同步驟的鑰匙不同（程式與冊各算各的）", c.cache_key("regions", {"name": "a.pdf", "sha": "1"}) != k1, None))
        checks.append(("沒存過 = 沒命中", c.cache_get("first_page", k1) is None, None))
        c.cache_put("first_page", k1, {"out": {"ticker": "2330"}, "has_chars": True}, seconds=3.5)
        got = c.cache_get("first_page", k1)
        checks.append(("存了就拿得回來（同一份答案）；省下的秒數照算", got == {"out": {"ticker": "2330"}, "has_chars": True}
                       and c.stats["first_page"]["saved_seconds"] == 3.5, c.stats.get("first_page")))
        out_a = td / "runA" / "vrn_db"
        out_a.mkdir(parents=True)
        (out_a / "summary.json").write_text(json.dumps({"output": str(out_a), "rows": 3}, ensure_ascii=False), encoding="utf-8")
        (out_a / "data.parquet").write_bytes(b"PAR1\x00\x01")
        dig_a = c.cache_folder_digest(out_a, mask=str(out_a))
        kf = c.cache_key("batch", {"in": [["a.pdf", "1"]], "out_before": []})
        c.cache_folder_store("batch", kf, out_a, {"output": str(out_a), "files": 1}, seconds=9.0)
        out_b = td / "runB" / "vrn_db"
        back = c.cache_folder_restore("batch", kf, out_b)
        text = (out_b / "summary.json").read_text(encoding="utf-8")
        checks.append(("資料夾快取：還原到新的輸出夾，裡面寫的舊路徑換成新路徑；二進位檔原封不動",
                       back is not None and json.loads(text)["output"] == str(out_b) and "runA" not in text and back["result"]["output"] == str(out_b)
                       and (out_b / "data.parquet").read_bytes() == b"PAR1\x00\x01", text))
        checks.append(("輸出夾指紋不算自己的路徑（G08 在每一輪的新夾子裡也命中）", c.cache_folder_digest(out_b, mask=str(out_b)) == dig_a, None))
        files = []
        for i in range(3):
            p = td / f"s{i}.pdf"
            p.write_bytes(bytes([i]) * 100)
            files.append(p)
        shas = c.cache_sample_sha(files)
        again = c.cache_sample_sha(files)
        checks.append(("樣本 SHA：沒動過的檔不再讀（大小與修改時間相同）", shas == again and c.stats["sample_sha"]["reread"] == 0
                       and shas[0] == hashlib.sha256(bytes([0]) * 100).hexdigest(), c.stats.get("sample_sha")))
        time.sleep(0.01)
        files[1].write_bytes(b"changed")
        third = c.cache_sample_sha(files)
        checks.append(("改過的檔才重讀", third[1] != shas[1] and third[0] == shas[0] and c.stats["sample_sha"]["reread"] == 1, None))
        checks.append(("聚焦副本位置跟著樣本組（同一組樣本同一個夾），不跟步驟的快取項目混在一起", c.cache_focus_folder() == td / "cache" / FOCUS_COPIES / c.scope
                       and c.cache_scope_of([["s0.pdf", "sha-of-the-current-samples"]]) == c.scope, None))
        old_scope = c.scope
        c.index["regions/" + "ab" * 32] = {"scope": "old-1", "used": 1.0}
        c.index["regions/" + "cd" * 32] = {"scope": "old-2", "used": 2.0}
        c.cache_put("regions", "ef" * 32, {"x": 1})
        c.used.discard("regions/" + "ef" * 32)           # an older engine version's answer, not used this run
        c.cache_put("regions", "12" * 32, {"y": 2})       # the step ran this time
        pr = c.cache_prune()
        checks.append(("刪除：樣本換了只留上一組；同組被新版本取代的舊答案刪；用到的都留",
                       "regions/" + "ab" * 32 not in c.index and "regions/" + "cd" * 32 in c.index and f"first_page/{k1}" in c.index
                       and "regions/" + "ef" * 32 not in c.index and "regions/" + "12" * 32 in c.index and pr["deleted"] >= 2, (pr, sorted(c.index))))
        checks.append(("每一筆刪除都記在帳上", (td / "cache" / LEDGER).is_file(), None))
        c.cache_put("focus", "34" * 32, {"manifest": {}, "copies": {}})
        (td / "cache" / FOCUS_COPIES / c.scope).mkdir(parents=True, exist_ok=True)
        (td / "cache" / FOCUS_COPIES / "old-sample-set").mkdir(parents=True, exist_ok=True)
        c.cache_prune()
        checks.append(("清舊聚焦副本只動 focus_copies 裡別組樣本的夾；focus 步驟自己的項目不受影響",
                       c.cache_path("focus", "34" * 32).is_file() and (td / "cache" / FOCUS_COPIES / c.scope).is_dir()
                       and not (td / "cache" / FOCUS_COPIES / "old-sample-set").exists(), None))
        checks.append(("scope 不被 prune 改掉", c.scope == old_scope, None))
        c.cache_close()
        reopen = RunCache(td / "cache")
        checks.append(("跑完放開鎖；下一輪拿得到；索引留著", reopen.enabled and f"first_page/{k1}" in reopen.index, reopen.why))
        reopen.cache_close()
    saved = {k: os.environ.get(k) for k in ("VIA_TEMP_ROOT", "LOCALAPPDATA", "VRN_TEMP_RUN")}
    try:
        for k in saved:
            os.environ.pop(k, None)
        os.environ["VRN_TEMP_RUN"] = str(Path(tempfile.gettempdir()) / "X" / "Temp" / "VIA_progress" / "VRN_Main" / "run_1")
        root = cache_temp_root()
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    checks.append(("TEMP 店開著（tempfile 指到本輪 run_ 夾）時，快取仍在 TEMP 根下，不會跟著本輪被清掉",
                   root == Path(tempfile.gettempdir()) / "X" / "Temp" / "VIA_progress", str(root)))
    home, why = cache_home(str(VRN_ROOT / "ssot" / "cache"))
    checks.append(("快取不放進 VRN 資料夾", home is None and "不放進" in why, why))
    res = cache_resources()
    # 2026-10-18（Codex PR #61 P1，實測重現）：這一條本來驗「1 ≤ workers ≤ 8」。
    # 8 變成可調之後，那就不是不變式，是把一個設定值當常數驗 —— VIA_VRN_WORKERS=9 會讓這一條紅，
    # 於是 runcache 這組證明過不了、引擎鎖封不起來。**我給的旋鈕會把鎖弄紅，比旋鈕沒用更糟。**
    # 真正的不變式是「夾得住」：至少 1 支；沒有硬指定時不超過三條限制裡最小的那條；硬指定時照辦。
    checks.append(("資源：CPU、記憶體、TEMP 剩餘 → 子行程數夾得住、快取上限不為負",
                   res["cpu"] >= 1 and res["workers"] >= 1 and res["budget_gb"] >= 0
                   and res["workers"] <= max(1, min(res["by_cpu"], res["by_mem"], res["ceiling"]))
                   if "VIA_VRN_WORKERS" not in os.environ else
                   res["cpu"] >= 1 and res["workers"] >= 1 and res["budget_gb"] >= 0, res))
    # 旋鈕本身也要有已知答案，不然「可調」只是我說說：硬指定要照辦、壞值要退回預設、夾子要夾得住。
    _keep = {k: os.environ.get(k) for k in ("VIA_VRN_WORKERS", "VIA_VRN_WORKER_GB", "VIA_VRN_WORKERS_MAX")}
    try:
        for k in _keep:
            os.environ.pop(k, None)
        base = cache_resources()
        os.environ["VIA_VRN_WORKERS"] = "9"
        forced = cache_resources()
        os.environ.pop("VIA_VRN_WORKERS")
        os.environ["VIA_VRN_WORKER_GB"] = "4096"      # 每支要 4 TB：記憶體一定先到頂
        tight = cache_resources()
        os.environ["VIA_VRN_WORKER_GB"] = "這不是數字"
        junk = cache_resources()
        # 壞值那一條要驗**真正被用到的那個值**（per_worker_gb），不是驗 workers：
        # 退回 low(0.05) 時 by_mem 會變成 302，但 workers = min(3, 302, 8) 仍是 3，跟預設一樣 ——
        # 驗一個會塌掉的衍生值，等於沒驗（2026-10-18 自己紅隊時抓到）。
        checks.append(("旋鈕：硬指定照辦（9 支，不被 8 擋住）、記憶體緊降到 1 支、壞值退回預設值本身",
                       forced["workers"] == 9 and tight["workers"] == 1 and tight["bottleneck"] == "記憶體"
                       and junk["per_worker_gb"] == base["per_worker_gb"] == 0.6,
                       (base["workers"], forced["workers"], tight["workers"], junk["per_worker_gb"])))
    finally:
        for k, v in _keep.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    off = cache_open(enabled=False)
    checks.append(("--no-cache：關掉也不出錯，一律沒命中", not off.enabled and off.cache_get("x", "y") is None and off.cache_close()["deleted"] == 0, off.why))
    dd = cache_data_files("batch")
    checks.append(("入庫步驟不跟 TitleTrim 冊與每輪生成的冊綁在一起（改標題規則不會讓前面全部重跑）",
                   "ssot/VRN_TitleTrim_SSOT_v0100.json" not in dd and "ssot/VRN_REGEX_SSOT_v0100.json" not in dd and "ssot/VRN_Broker_Dict_v0100.json" in dd, None))
    checks.append(("聚焦步驟要算 TitleTrim 冊（聚焦規則寫在裡面）", "ssot/VRN_TitleTrim_SSOT_v0100.json" in cache_data_files("focus"), None))
    bad = [x for x in checks if not x[1]]
    if verbose:
        for name, ok, detail in checks:
            print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + ("" if ok else f" · {str(detail)[:300]}"))
        print(f"[RUNCACHE] {CACHE_VERSION} · {len(checks) - len(bad)}/{len(checks)}")
    return 0 if not bad else 1


# [VRN-ID] VRN-ENG019-FNC035 · ENTRY
def main(argv=None):
    parser = argparse.ArgumentParser(prog="VRN_RunCache_v0100.py", description="TEMP 裡的實測快取：輸入沒換就不重跑")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("resources", help="CPU／記憶體／TEMP／快取 → 子行程數與快取上限")
    p_s = sub.add_parser("status", help="快取在哪、多大、幾筆")
    p_s.add_argument("--cache-home", default="")
    p_c = sub.add_parser("clear", help="整個快取刪掉（下一輪全部重跑）")
    p_c.add_argument("--cache-home", default="")
    sub.add_parser("selftest")
    args = parser.parse_args(argv)
    if args.command == "resources":
        home, _why = cache_home()
        print(json.dumps(cache_resources(home), ensure_ascii=False, indent=1))
        return 0
    if args.command in ("status", "clear"):
        home, why = cache_home(args.cache_home)
        if home is None:
            print(f"[RUNCACHE] {why}")
            return 1
        if args.command == "clear":
            c = RunCache(home)
            if not c.enabled:
                print(f"[RUNCACHE] {c.why}")
                return 1
            gone = 0
            for p in list(home.iterdir()):
                if p.name not in (".cache.lock", LEDGER):
                    gone += c.cache_purge(p, "操作員清空")
            c.index = {}
            c.cache_close()
            print(f"[RUNCACHE] 清空 {home} · {round(gone / (1 << 20), 1)} MB")
            return 0
        try:
            index = json.loads((home / INDEX).read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            index = {}
        print(f"[RUNCACHE] {home}（{why}）· {len(index)} 筆 · {round(cache_size(home) / (1 << 20), 1)} MB")
        return 0
    return selftest()


if __name__ == "__main__":
    sys.exit(main())
