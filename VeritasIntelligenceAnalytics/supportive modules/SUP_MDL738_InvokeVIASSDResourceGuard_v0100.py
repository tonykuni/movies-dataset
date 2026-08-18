#!/usr/bin/env python3
"""
Veritas Intelligence Analytics · SSD Resource Guard · v1.0.0

單檔、零外部相依的 Windows／Linux 前置資源管線：
1. 只清除本引擎擁有且有標記的上一輪 TEMP。
2. 以 SQLite 做低 DRAM、可續跑的檔案盤點。
3. 先比大小、再比頭尾快速指紋、最後串流 SHA-256。
4. 只自動隔離「同資料夾＋明確副本檔名＋內容完全相同」的檔案。
5. 等候 CPU／DRAM／SSD 空間通過 Gate 後，才啟動高負載工具。
6. 產生 JSON／CSV／HTML 稽核證據與可還原 manifest。

重要限制：
- 清理 SSD 空間本身不會直接降低 CPU／DRAM；真正減負來自分塊、續跑、
  磁碟暫存、執行緒上限與資源 Gate。
- 不會因為副檔名是 .log／.bak／.tmp 就刪除一般資料。
- 隔離區與來源若在同一磁碟，隔離本身不會立即釋放容量；須在保留期後
  自動清除，或使用 --purge-quarantine-now。
"""

from __future__ import annotations

# =============================================================================
# def 00 · 全部可調參數（集中於程式頂部）
# =============================================================================

import argparse
import csv
import ctypes
import hashlib
import html
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time
import traceback
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence


ENGINE_NAME = "VIA_SSD_RESOURCE_GUARD"
ENGINE_VERSION = "1.0.0"

# 掃描範圍：空白代表執行時的目前資料夾；也可用 --scan-root 重複指定。
DEFAULT_SCAN_ROOTS: tuple[str, ...] = tuple(
    value for value in (os.environ.get("VIA_CLEANUP_ROOT", ""),) if value
)

# 建議放在 SSD。未設定時，Windows 使用 LOCALAPPDATA，其他系統使用 ~/.cache。
DEFAULT_TEMP_ROOT = os.environ.get("VIA_TEMP_ROOT", "")
DEFAULT_STATE_ROOT = os.environ.get("VIA_GUARD_STATE_ROOT", "")
DEFAULT_QUARANTINE_ROOT = os.environ.get("VIA_QUARANTINE_ROOT", "")

# 去重參數。
MIN_DUPLICATE_BYTES = 4 * 1024
HASH_BLOCK_BYTES = 1024 * 1024
QUICK_FINGERPRINT_BYTES = 64 * 1024
AUTO_QUARANTINE_EXACT_DUPLICATES = True
SAFE_DUPLICATE_POLICY = "SAME_DIRECTORY_COPY_NAME_ONLY"
COPY_NAME_PATTERN = re.compile(
    r"(?i)(?:\s*\(\d+\)|[\s_-]+copy(?:[\s_-]+\d+)?|"
    r"[\s_-]+duplicate(?:[\s_-]+\d+)?|[\s_-]*副本(?:\s*\(\d+\))?)$"
)

# 隔離與永久清除：7 天內可還原；設為 0 可停用自動永久清除。
QUARANTINE_RETENTION_DAYS = 7
AUTO_PURGE_EXPIRED_QUARANTINE = True

# 資源 Gate。
MAX_CPU_PERCENT = 75.0
MAX_MEMORY_USED_PERCENT = 80.0
MIN_AVAILABLE_MEMORY_GIB = 4.0
MIN_TEMP_DISK_FREE_GIB = 15.0
MIN_TEMP_DISK_FREE_PERCENT = 10.0
RESOURCE_GATE_TIMEOUT_SECONDS = 300
RESOURCE_GATE_SAMPLE_SECONDS = 2
RESOURCE_GATE_REQUIRED_CONSECUTIVE_PASSES = 2

# 高負載工具的並行與啟動參數。也可用 --workload 後接完整命令覆寫。
MAX_WORKER_THREADS = max(1, min(8, (os.cpu_count() or 2) - 1))
MAX_CPU_CORES_FOR_WORKLOAD = max(1, min(8, (os.cpu_count() or 2) - 1))
WORKLOAD_COMMAND: tuple[str, ...] = tuple()
WAIT_FOR_WORKLOAD = True
LOWER_WORKLOAD_PRIORITY = True
WORKLOAD_MONITOR_INTERVAL_SECONDS = 5

# 可續跑 Batch Fetching。命令中的 {item} 會替換為每一筆代碼／網址／ID。
# 範例：("python", "fetcher.py", "--ticker", "{item}")
BATCH_ITEMS_FILE = os.environ.get("VIA_BATCH_ITEMS_FILE", "")
BATCH_ITEM_COLUMN = os.environ.get("VIA_BATCH_ITEM_COLUMN", "Ticker")
BATCH_FETCH_COMMAND_TEMPLATE: tuple[str, ...] = tuple()
BATCH_MAX_RETRIES = 3
BATCH_RETRY_BASE_DELAY_SECONDS = 5
BATCH_ITEM_TIMEOUT_SECONDS = 30 * 60
BATCH_CONTINUE_AFTER_FINAL_FAILURE = True
BATCH_RESET_FAILED_ON_NEXT_RUN = True

# 嚴重記憶體壓力時終止目前批次項目，寫回 checkpoint，等待後重試。
CRITICAL_MEMORY_USED_PERCENT = 92.0
CRITICAL_MIN_AVAILABLE_MEMORY_GIB = 1.5
CRITICAL_MEMORY_CONSECUTIVE_SAMPLES = 2
AUTO_ABORT_BATCH_ITEM_ON_CRITICAL_MEMORY = True

# 掃描安全與排除。
FOLLOW_SYMLINKS = False
ALLOW_BROAD_FILESYSTEM_ROOT = False
MAX_SCAN_ERRORS_BEFORE_FAIL = 1000
EXCLUDED_DIRECTORY_NAMES = frozenset(
    {
        "$RECYCLE.BIN",
        "System Volume Information",
        ".git",
        ".svn",
        ".hg",
        "node_modules",
        "__pycache__",
        ".venv",
        "venv",
        ".mypy_cache",
        ".pytest_cache",
    }
)

# SQLite 與輸出。
SQLITE_BUSY_TIMEOUT_MS = 30_000
SQLITE_COMMIT_EVERY_FILES = 500
REPORT_ENCODING = "utf-8-sig"
LOCK_STALE_SECONDS = 24 * 60 * 60


# =============================================================================
# def 01 · 資料結構與共用工具
# =============================================================================


@dataclass(frozen=True)
class RuntimePaths:
    scan_roots: tuple[Path, ...]
    temp_root: Path
    state_root: Path
    quarantine_root: Path
    report_root: Path
    database_path: Path
    lock_path: Path


@dataclass
class RunMetrics:
    run_id: str
    started_at: str
    finished_at: str = ""
    status: str = "RUNNING"
    files_scanned: int = 0
    bytes_scanned: int = 0
    scan_errors: int = 0
    quick_hashes_computed: int = 0
    full_hashes_computed: int = 0
    duplicate_groups: int = 0
    exact_duplicate_files: int = 0
    duplicate_bytes_identified: int = 0
    files_quarantined: int = 0
    bytes_quarantined: int = 0
    prior_temp_runs_deleted: int = 0
    prior_temp_bytes_deleted: int = 0
    expired_quarantine_files_purged: int = 0
    expired_quarantine_bytes_purged: int = 0
    workload_started: bool = False
    workload_return_code: int | None = None
    resource_samples: int = 0
    peak_cpu_percent: float = 0.0
    peak_memory_used_percent: float = 0.0
    minimum_available_memory_gib: float | None = None
    batch_job_id: str = ""
    batch_items_total: int = 0
    batch_items_resumed: int = 0
    batch_items_recovered_after_interruption: int = 0
    batch_items_completed: int = 0
    batch_items_failed: int = 0
    batch_retries: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DuplicateRecord:
    group_id: str
    keeper_path: str
    duplicate_path: str
    size_bytes: int
    sha256: str
    decision: str
    reason: str
    quarantine_path: str = ""


@dataclass(frozen=True)
class ResourceSnapshot:
    cpu_percent: float
    memory_used_percent: float
    available_memory_gib: float
    disk_free_gib: float
    disk_free_percent: float


def def_now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def def_write_progress(percent: int, message: str, status: str = "INFO") -> None:
    filled = max(0, min(20, round(percent / 5)))
    bar = "█" * filled + "░" * (20 - filled)
    print(f"def [{percent:3d}%] [{bar}] [{status}] {message}", flush=True)


def def_human_bytes(value: int) -> str:
    amount = float(value)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if amount < 1024.0 or unit == "TiB":
            return f"{amount:.2f} {unit}"
        amount /= 1024.0
    return f"{amount:.2f} TiB"


def def_default_data_root(name: str) -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    return base / "VeritasIntelligenceAnalytics" / name


def def_resolve_path(raw: str | Path) -> Path:
    return Path(raw).expanduser().resolve(strict=False)


def def_is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def def_assert_not_filesystem_root(path: Path) -> None:
    if ALLOW_BROAD_FILESYSTEM_ROOT:
        return
    if path == Path(path.anchor):
        raise ValueError(f"拒絕掃描整個磁碟根目錄：{path}")
    if path == Path.home().resolve(strict=False):
        raise ValueError(f"拒絕直接掃描整個使用者家目錄：{path}")


def def_resolve_runtime_paths(args: argparse.Namespace) -> RuntimePaths:
    scan_raw = args.scan_root or list(DEFAULT_SCAN_ROOTS) or [str(Path.cwd())]
    scan_roots = tuple(dict.fromkeys(def_resolve_path(item) for item in scan_raw))
    for root in scan_roots:
        if not root.is_dir():
            raise FileNotFoundError(f"掃描資料夾不存在：{root}")
        def_assert_not_filesystem_root(root)

    temp_root = def_resolve_path(
        args.temp_root or DEFAULT_TEMP_ROOT or def_default_data_root("ManagedTemp")
    )
    state_root = def_resolve_path(
        args.state_root or DEFAULT_STATE_ROOT or def_default_data_root("ResourceGuardState")
    )
    quarantine_root = def_resolve_path(
        args.quarantine_root
        or DEFAULT_QUARANTINE_ROOT
        or def_default_data_root("DuplicateQuarantine")
    )
    report_root = state_root / "reports" / args.run_id
    return RuntimePaths(
        scan_roots=scan_roots,
        temp_root=temp_root,
        state_root=state_root,
        quarantine_root=quarantine_root,
        report_root=report_root,
        database_path=state_root / "resource_guard.sqlite3",
        lock_path=state_root / ".resource_guard.lock",
    )


def def_write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def def_append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def def_directory_size(root: Path) -> int:
    total = 0
    if not root.exists() or root.is_symlink():
        return 0
    for current_root, directory_names, file_names in os.walk(root, followlinks=False):
        directory_names[:] = [
            name for name in directory_names if not (Path(current_root) / name).is_symlink()
        ]
        for name in file_names:
            try:
                total += (Path(current_root) / name).stat(follow_symlinks=False).st_size
            except OSError:
                continue
    return total


def def_process_is_running(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except PermissionError:
        return True
    except OSError:
        return False


@contextmanager
def def_engine_lock(lock_path: Path) -> Iterator[None]:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"pid": os.getpid(), "created_at": def_now_utc(), "engine": ENGINE_NAME}
    for attempt in range(2):
        try:
            descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False)
            break
        except FileExistsError:
            try:
                existing = json.loads(lock_path.read_text(encoding="utf-8"))
                age = time.time() - lock_path.stat().st_mtime
                pid = int(existing.get("pid", 0))
            except (OSError, ValueError, json.JSONDecodeError):
                age, pid = LOCK_STALE_SECONDS + 1, 0
            if attempt == 0 and age > LOCK_STALE_SECONDS and not def_process_is_running(pid):
                lock_path.unlink(missing_ok=True)
                continue
            raise RuntimeError(f"已有 Resource Guard 執行中或鎖定狀態未確認：{lock_path}")
    try:
        yield
    finally:
        try:
            current = json.loads(lock_path.read_text(encoding="utf-8"))
            if int(current.get("pid", -1)) == os.getpid():
                lock_path.unlink(missing_ok=True)
        except (OSError, ValueError, json.JSONDecodeError):
            pass


# =============================================================================
# def 02 · 受管 TEMP 生命週期
# =============================================================================


def def_marker_payload(kind: str, run_id: str = "") -> dict[str, Any]:
    return {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "kind": kind,
        "run_id": run_id,
        "created_at": def_now_utc(),
    }


def def_prepare_managed_root(root: Path, marker_name: str, kind: str) -> None:
    marker = root / marker_name
    if root.exists() and root.is_symlink():
        raise RuntimeError(f"受管目錄不可為符號連結：{root}")
    if root.exists() and not marker.exists():
        entries = list(root.iterdir())
        if entries:
            raise RuntimeError(f"目錄內已有資料但缺少擁有權標記，拒絕接管：{root}")
    root.mkdir(parents=True, exist_ok=True)
    if marker.exists():
        try:
            payload = json.loads(marker.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"擁有權標記無法驗證：{marker}") from exc
        if payload.get("engine") != ENGINE_NAME or payload.get("kind") != kind:
            raise RuntimeError(f"擁有權標記不屬於本引擎：{marker}")
    else:
        def_write_json_atomic(marker, def_marker_payload(kind))


def def_reset_previous_temp(paths: RuntimePaths, run_id: str, metrics: RunMetrics) -> Path:
    root_marker = ".via_managed_temp_root.json"
    run_marker = ".via_managed_temp_run.json"
    def_prepare_managed_root(paths.temp_root, root_marker, "managed_temp_root")
    for child in paths.temp_root.iterdir():
        if not child.is_dir() or child.is_symlink() or child.name == run_id:
            continue
        marker = child / run_marker
        try:
            payload = json.loads(marker.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            metrics.warnings.append(f"未清除無有效標記的 TEMP 子目錄：{child}")
            continue
        if (
            payload.get("engine") != ENGINE_NAME
            or payload.get("kind") != "managed_temp_run"
            or not def_is_relative_to(child.resolve(strict=False), paths.temp_root)
        ):
            metrics.warnings.append(f"TEMP 擁有權驗證失敗：{child}")
            continue
        byte_count = def_directory_size(child)
        shutil.rmtree(child)
        metrics.prior_temp_runs_deleted += 1
        metrics.prior_temp_bytes_deleted += byte_count

    current = paths.temp_root / run_id
    current.mkdir(parents=False, exist_ok=False)
    def_write_json_atomic(current / run_marker, def_marker_payload("managed_temp_run", run_id))
    for name in ("duckdb", "joblib", "dask", "matplotlib", "python_cache", "generic"):
        (current / name).mkdir(parents=False, exist_ok=False)
    return current


# =============================================================================
# def 03 · SQLite 增量索引與低 DRAM 盤點
# =============================================================================


def def_open_database(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=SQLITE_BUSY_TIMEOUT_MS / 1000)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA synchronous=NORMAL")
    connection.execute(f"PRAGMA busy_timeout={SQLITE_BUSY_TIMEOUT_MS}")
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS file_cache (
            path TEXT PRIMARY KEY,
            size_bytes INTEGER NOT NULL,
            mtime_ns INTEGER NOT NULL,
            quick_hash TEXT,
            full_hash TEXT,
            last_seen_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS run_files (
            run_id TEXT NOT NULL,
            path TEXT NOT NULL,
            root_key TEXT NOT NULL,
            relative_path TEXT NOT NULL,
            size_bytes INTEGER NOT NULL,
            mtime_ns INTEGER NOT NULL,
            quick_hash TEXT,
            full_hash TEXT,
            PRIMARY KEY (run_id, path)
        );
        CREATE INDEX IF NOT EXISTS idx_run_files_size
            ON run_files (run_id, size_bytes);
        CREATE INDEX IF NOT EXISTS idx_run_files_quick
            ON run_files (run_id, size_bytes, quick_hash);
        CREATE INDEX IF NOT EXISTS idx_run_files_full
            ON run_files (run_id, size_bytes, full_hash);
        CREATE TABLE IF NOT EXISTS batch_jobs (
            job_id TEXT PRIMARY KEY,
            items_file TEXT NOT NULL,
            command_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS batch_items (
            job_id TEXT NOT NULL,
            item_key TEXT NOT NULL,
            item_value TEXT NOT NULL,
            ordinal INTEGER NOT NULL,
            status TEXT NOT NULL,
            attempts INTEGER NOT NULL DEFAULT 0,
            last_return_code INTEGER,
            last_error TEXT,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (job_id, item_key)
        );
        CREATE INDEX IF NOT EXISTS idx_batch_items_status
            ON batch_items (job_id, status, ordinal);
        """
    )
    connection.commit()
    return connection


def def_excluded_absolute_roots(paths: RuntimePaths) -> tuple[Path, ...]:
    return tuple(
        item.resolve(strict=False)
        for item in (paths.temp_root, paths.state_root, paths.quarantine_root)
    )


def def_path_is_excluded(path: Path, excluded_roots: Sequence[Path]) -> bool:
    resolved = path.resolve(strict=False)
    return any(def_is_relative_to(resolved, root) for root in excluded_roots)


def def_iter_regular_files(root: Path, excluded_roots: Sequence[Path]) -> Iterator[Path]:
    for current_root, directory_names, file_names in os.walk(
        root, topdown=True, followlinks=FOLLOW_SYMLINKS
    ):
        current_path = Path(current_root)
        kept_directories: list[str] = []
        for name in directory_names:
            candidate = current_path / name
            if name in EXCLUDED_DIRECTORY_NAMES:
                continue
            if not FOLLOW_SYMLINKS and candidate.is_symlink():
                continue
            if def_path_is_excluded(candidate, excluded_roots):
                continue
            kept_directories.append(name)
        directory_names[:] = kept_directories
        for name in file_names:
            candidate = current_path / name
            if not FOLLOW_SYMLINKS and candidate.is_symlink():
                continue
            if def_path_is_excluded(candidate, excluded_roots):
                continue
            yield candidate


def def_inventory_files(
    connection: sqlite3.Connection,
    paths: RuntimePaths,
    run_id: str,
    metrics: RunMetrics,
) -> None:
    connection.execute("DELETE FROM run_files WHERE run_id = ?", (run_id,))
    now = def_now_utc()
    pending = 0
    for root_index, root in enumerate(paths.scan_roots, start=1):
        root_key = f"ROOT_{root_index:02d}"
        for file_path in def_iter_regular_files(root, def_excluded_absolute_roots(paths)):
            try:
                stat = file_path.stat(follow_symlinks=False)
                if not file_path.is_file():
                    continue
                relative = str(file_path.relative_to(root))
                cache = connection.execute(
                    "SELECT quick_hash, full_hash FROM file_cache "
                    "WHERE path = ? AND size_bytes = ? AND mtime_ns = ?",
                    (str(file_path), stat.st_size, stat.st_mtime_ns),
                ).fetchone()
                quick_hash, full_hash = cache if cache else (None, None)
                connection.execute(
                    "INSERT OR REPLACE INTO run_files "
                    "(run_id, path, root_key, relative_path, size_bytes, mtime_ns, "
                    " quick_hash, full_hash) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        run_id,
                        str(file_path),
                        root_key,
                        relative,
                        stat.st_size,
                        stat.st_mtime_ns,
                        quick_hash,
                        full_hash,
                    ),
                )
                connection.execute(
                    "INSERT OR REPLACE INTO file_cache "
                    "(path, size_bytes, mtime_ns, quick_hash, full_hash, last_seen_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        str(file_path),
                        stat.st_size,
                        stat.st_mtime_ns,
                        quick_hash,
                        full_hash,
                        now,
                    ),
                )
                metrics.files_scanned += 1
                metrics.bytes_scanned += stat.st_size
                pending += 1
                if pending >= SQLITE_COMMIT_EVERY_FILES:
                    connection.commit()
                    pending = 0
            except (OSError, sqlite3.Error) as exc:
                metrics.scan_errors += 1
                metrics.warnings.append(f"盤點略過：{file_path}：{exc}")
                if metrics.scan_errors > MAX_SCAN_ERRORS_BEFORE_FAIL:
                    raise RuntimeError("掃描錯誤超過安全上限，停止執行") from exc
    connection.commit()


def def_quick_fingerprint(path: Path, size_bytes: int) -> str:
    digest = hashlib.blake2b(digest_size=16)
    digest.update(size_bytes.to_bytes(16, byteorder="big", signed=False))
    with path.open("rb", buffering=0) as handle:
        digest.update(handle.read(QUICK_FINGERPRINT_BYTES))
        if size_bytes > QUICK_FINGERPRINT_BYTES:
            handle.seek(max(0, size_bytes - QUICK_FINGERPRINT_BYTES))
            digest.update(handle.read(QUICK_FINGERPRINT_BYTES))
    return digest.hexdigest()


def def_sha256_stream(path: Path) -> str:
    digest = hashlib.sha256()
    buffer = bytearray(HASH_BLOCK_BYTES)
    view = memoryview(buffer)
    with path.open("rb", buffering=0) as handle:
        while True:
            count = handle.readinto(buffer)
            if not count:
                break
            digest.update(view[:count])
    return digest.hexdigest()


def def_update_hash(
    connection: sqlite3.Connection,
    run_id: str,
    path_text: str,
    column: str,
    value: str,
) -> None:
    if column not in {"quick_hash", "full_hash"}:
        raise ValueError(f"不允許的 Hash 欄位：{column}")
    connection.execute(
        f"UPDATE run_files SET {column} = ? WHERE run_id = ? AND path = ?",
        (value, run_id, path_text),
    )
    row = connection.execute(
        "SELECT size_bytes, mtime_ns FROM run_files WHERE run_id = ? AND path = ?",
        (run_id, path_text),
    ).fetchone()
    if row:
        connection.execute(
            f"UPDATE file_cache SET {column} = ?, last_seen_at = ? "
            "WHERE path = ? AND size_bytes = ? AND mtime_ns = ?",
            (value, def_now_utc(), path_text, row[0], row[1]),
        )


def def_compute_candidate_hashes(
    connection: sqlite3.Connection, run_id: str, metrics: RunMetrics
) -> None:
    size_rows = connection.execute(
        "SELECT size_bytes FROM run_files WHERE run_id = ? AND size_bytes >= ? "
        "GROUP BY size_bytes HAVING COUNT(*) > 1 ORDER BY size_bytes",
        (run_id, MIN_DUPLICATE_BYTES),
    ).fetchall()
    for (size_bytes,) in size_rows:
        rows = connection.execute(
            "SELECT path, quick_hash FROM run_files "
            "WHERE run_id = ? AND size_bytes = ? ORDER BY path",
            (run_id, size_bytes),
        ).fetchall()
        for path_text, cached_hash in rows:
            if cached_hash:
                continue
            try:
                value = def_quick_fingerprint(Path(path_text), size_bytes)
                def_update_hash(connection, run_id, path_text, "quick_hash", value)
                metrics.quick_hashes_computed += 1
            except OSError as exc:
                metrics.warnings.append(f"快速指紋失敗：{path_text}：{exc}")
        connection.commit()

    quick_rows = connection.execute(
        "SELECT size_bytes, quick_hash FROM run_files "
        "WHERE run_id = ? AND quick_hash IS NOT NULL "
        "GROUP BY size_bytes, quick_hash HAVING COUNT(*) > 1",
        (run_id,),
    ).fetchall()
    for size_bytes, quick_hash in quick_rows:
        rows = connection.execute(
            "SELECT path, full_hash FROM run_files "
            "WHERE run_id = ? AND size_bytes = ? AND quick_hash = ? ORDER BY path",
            (run_id, size_bytes, quick_hash),
        ).fetchall()
        for path_text, cached_hash in rows:
            if cached_hash:
                continue
            try:
                value = def_sha256_stream(Path(path_text))
                def_update_hash(connection, run_id, path_text, "full_hash", value)
                metrics.full_hashes_computed += 1
            except OSError as exc:
                metrics.warnings.append(f"完整 SHA-256 失敗：{path_text}：{exc}")
        connection.commit()


# =============================================================================
# def 04 · 重複檔案決策、隔離、還原與到期清除
# =============================================================================


def def_copy_name_score(path: Path) -> int:
    return 1 if COPY_NAME_PATTERN.search(path.stem) else 0


def def_select_keeper(paths: Sequence[Path]) -> Path:
    return sorted(
        paths,
        key=lambda item: (
            def_copy_name_score(item),
            len(item.name),
            item.name.casefold(),
            str(item).casefold(),
        ),
    )[0]


def def_safe_duplicate_decision(keeper: Path, candidate: Path) -> tuple[str, str]:
    if SAFE_DUPLICATE_POLICY != "SAME_DIRECTORY_COPY_NAME_ONLY":
        return "REPORT_ONLY", "未知安全政策"
    try:
        same_parent = keeper.parent.resolve(strict=True) == candidate.parent.resolve(strict=True)
    except OSError:
        return "REPORT_ONLY", "父目錄無法驗證"
    if not same_parent:
        return "REPORT_ONLY", "相同內容位於不同目錄，可能具備不同用途"
    if def_copy_name_score(candidate) != 1 or def_copy_name_score(keeper) != 0:
        return "REPORT_ONLY", "檔名未明確顯示為副本"
    return "QUARANTINE", "同目錄、明確副本檔名、大小與 SHA-256 完全相同"


def def_unique_quarantine_path(base: Path, source: Path, root_key: str, relative: str) -> Path:
    target = base / root_key / relative
    if not target.exists():
        return target
    return target.with_name(f"{target.stem}.{uuid.uuid4().hex[:8]}{target.suffix}")


def def_move_to_quarantine(
    source: Path,
    destination: Path,
    expected_size: int,
    expected_sha256: str,
    manifest_path: Path,
    run_id: str,
) -> None:
    stat = source.stat(follow_symlinks=False)
    if not source.is_file() or source.is_symlink() or stat.st_size != expected_size:
        raise RuntimeError(f"隔離前檔案狀態已改變：{source}")
    if def_sha256_stream(source) != expected_sha256:
        raise RuntimeError(f"隔離前 SHA-256 已改變：{source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    prepared = {
        "event": "PREPARED",
        "run_id": run_id,
        "source": str(source),
        "destination": str(destination),
        "size_bytes": expected_size,
        "sha256": expected_sha256,
        "timestamp": def_now_utc(),
    }
    def_append_jsonl(manifest_path, prepared)

    same_volume = source.stat().st_dev == destination.parent.stat().st_dev
    if same_volume:
        os.replace(source, destination)
    else:
        temporary = destination.with_name(f".{destination.name}.{uuid.uuid4().hex}.partial")
        shutil.copy2(source, temporary)
        if temporary.stat().st_size != expected_size or def_sha256_stream(temporary) != expected_sha256:
            temporary.unlink(missing_ok=True)
            raise RuntimeError(f"跨磁碟隔離副本驗證失敗：{source}")
        os.replace(temporary, destination)
        source.unlink()

    def_append_jsonl(
        manifest_path,
        {
            **prepared,
            "event": "QUARANTINED",
            "timestamp": def_now_utc(),
        },
    )


def def_find_and_handle_duplicates(
    connection: sqlite3.Connection,
    paths: RuntimePaths,
    run_id: str,
    metrics: RunMetrics,
    report_only: bool,
) -> list[DuplicateRecord]:
    records: list[DuplicateRecord] = []
    quarantine_run = paths.quarantine_root / run_id
    manifest_path = quarantine_run / "quarantine_manifest.jsonl"
    groups = connection.execute(
        "SELECT size_bytes, full_hash FROM run_files "
        "WHERE run_id = ? AND full_hash IS NOT NULL "
        "GROUP BY size_bytes, full_hash HAVING COUNT(*) > 1 "
        "ORDER BY size_bytes DESC, full_hash",
        (run_id,),
    ).fetchall()
    for group_index, (size_bytes, full_hash) in enumerate(groups, start=1):
        rows = connection.execute(
            "SELECT path, root_key, relative_path FROM run_files "
            "WHERE run_id = ? AND size_bytes = ? AND full_hash = ? ORDER BY path",
            (run_id, size_bytes, full_hash),
        ).fetchall()
        existing = [(Path(row[0]), row[1], row[2]) for row in rows if Path(row[0]).is_file()]
        if len(existing) < 2:
            continue
        group_id = f"DUP_{group_index:06d}"
        keeper = def_select_keeper([item[0] for item in existing])
        metrics.duplicate_groups += 1
        for candidate, root_key, relative in existing:
            if candidate == keeper:
                continue
            metrics.exact_duplicate_files += 1
            metrics.duplicate_bytes_identified += size_bytes
            decision, reason = def_safe_duplicate_decision(keeper, candidate)
            quarantine_path = ""
            if report_only:
                decision, reason = "REPORT_ONLY", f"報告模式；原判定：{reason}"
            elif decision == "QUARANTINE" and AUTO_QUARANTINE_EXACT_DUPLICATES:
                target = def_unique_quarantine_path(
                    quarantine_run, candidate, root_key, relative
                )
                try:
                    keeper_stat = keeper.stat(follow_symlinks=False)
                    if (
                        not keeper.is_file()
                        or keeper.is_symlink()
                        or keeper_stat.st_size != size_bytes
                        or def_sha256_stream(keeper) != full_hash
                    ):
                        raise RuntimeError(f"保留檔在隔離前已改變：{keeper}")
                    def_move_to_quarantine(
                        candidate,
                        target,
                        size_bytes,
                        full_hash,
                        manifest_path,
                        run_id,
                    )
                    quarantine_path = str(target)
                    metrics.files_quarantined += 1
                    metrics.bytes_quarantined += size_bytes
                    decision = "QUARANTINED"
                except (OSError, RuntimeError) as exc:
                    decision = "QUARANTINE_FAILED"
                    reason = f"{reason}；{exc}"
                    metrics.warnings.append(f"隔離失敗：{candidate}：{exc}")
            records.append(
                DuplicateRecord(
                    group_id=group_id,
                    keeper_path=str(keeper),
                    duplicate_path=str(candidate),
                    size_bytes=size_bytes,
                    sha256=full_hash,
                    decision=decision,
                    reason=reason,
                    quarantine_path=quarantine_path,
                )
            )
    return records


def def_load_latest_manifest_events(manifest_path: Path) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    with manifest_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            event = json.loads(line)
            latest[str(event["destination"])] = event
    return latest


def def_restore_manifest(manifest_path: Path) -> int:
    events = def_load_latest_manifest_events(manifest_path)
    restored = 0
    for event in events.values():
        if event.get("event") != "QUARANTINED":
            continue
        source = Path(event["source"])
        destination = Path(event["destination"])
        if source.exists():
            print(f"def [WARN] 還原略過，原路徑已有檔案：{source}")
            continue
        if not destination.is_file() or destination.is_symlink():
            print(f"def [WARN] 還原來源不存在：{destination}")
            continue
        expected_size = int(event["size_bytes"])
        expected_hash = str(event["sha256"])
        if destination.stat().st_size != expected_size or def_sha256_stream(destination) != expected_hash:
            print(f"def [WARN] 還原來源驗證失敗：{destination}")
            continue
        source.parent.mkdir(parents=True, exist_ok=True)
        if source.parent.stat().st_dev == destination.stat().st_dev:
            os.replace(destination, source)
        else:
            temporary = source.with_name(f".{source.name}.{uuid.uuid4().hex}.partial")
            shutil.copy2(destination, temporary)
            if def_sha256_stream(temporary) != expected_hash:
                temporary.unlink(missing_ok=True)
                raise RuntimeError(f"還原複製驗證失敗：{destination}")
            os.replace(temporary, source)
            destination.unlink()
        def_append_jsonl(
            manifest_path,
            {**event, "event": "RESTORED", "timestamp": def_now_utc()},
        )
        restored += 1
    return restored


def def_purge_manifest_files(
    manifest_path: Path, metrics: RunMetrics, ignore_retention: bool = False
) -> None:
    run_folder = manifest_path.parent
    if not ignore_retention:
        age_days = (time.time() - run_folder.stat().st_mtime) / 86400
        if QUARANTINE_RETENTION_DAYS <= 0 or age_days < QUARANTINE_RETENTION_DAYS:
            return
    events = def_load_latest_manifest_events(manifest_path)
    for event in events.values():
        if event.get("event") != "QUARANTINED":
            continue
        destination = Path(event["destination"])
        expected_size = int(event["size_bytes"])
        expected_hash = str(event["sha256"])
        if not destination.is_file() or destination.is_symlink():
            continue
        if destination.stat().st_size != expected_size:
            metrics.warnings.append(f"到期隔離檔大小改變，拒絕清除：{destination}")
            continue
        if def_sha256_stream(destination) != expected_hash:
            metrics.warnings.append(f"到期隔離檔 SHA-256 改變，拒絕清除：{destination}")
            continue
        destination.unlink()
        def_append_jsonl(
            manifest_path,
            {**event, "event": "PURGED", "timestamp": def_now_utc()},
        )
        metrics.expired_quarantine_files_purged += 1
        metrics.expired_quarantine_bytes_purged += expected_size


def def_purge_expired_quarantines(
    paths: RuntimePaths, metrics: RunMetrics, purge_now: bool
) -> None:
    def_prepare_managed_root(
        paths.quarantine_root, ".via_quarantine_root.json", "quarantine_root"
    )
    if not AUTO_PURGE_EXPIRED_QUARANTINE and not purge_now:
        return
    for manifest in paths.quarantine_root.glob("*/quarantine_manifest.jsonl"):
        try:
            def_purge_manifest_files(manifest, metrics, ignore_retention=purge_now)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            metrics.warnings.append(f"隔離區清除略過：{manifest}：{exc}")


# =============================================================================
# def 05 · CPU／DRAM／磁碟資源 Gate
# =============================================================================


class def_MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def def_windows_memory() -> tuple[float, float]:
    status = def_MEMORYSTATUSEX()
    status.dwLength = ctypes.sizeof(status)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        raise OSError("GlobalMemoryStatusEx 失敗")
    return float(status.dwMemoryLoad), status.ullAvailPhys / (1024**3)


def def_linux_memory() -> tuple[float, float]:
    values: dict[str, int] = {}
    with Path("/proc/meminfo").open("r", encoding="ascii") as handle:
        for line in handle:
            key, raw = line.split(":", maxsplit=1)
            values[key] = int(raw.strip().split()[0]) * 1024
    total = values["MemTotal"]
    available = values.get("MemAvailable", values.get("MemFree", 0))
    return (100.0 * (total - available) / total), available / (1024**3)


def def_memory_snapshot() -> tuple[float, float]:
    try:
        import psutil  # type: ignore

        memory = psutil.virtual_memory()
        return float(memory.percent), memory.available / (1024**3)
    except ImportError:
        if os.name == "nt":
            return def_windows_memory()
        if Path("/proc/meminfo").exists():
            return def_linux_memory()
        raise RuntimeError("缺少 psutil，且作業系統沒有可用的記憶體備援介面")


def def_windows_cpu_percent(interval: float) -> float:
    class FILETIME(ctypes.Structure):
        _fields_ = [("low", ctypes.c_ulong), ("high", ctypes.c_ulong)]

    def def_snapshot() -> tuple[int, int, int]:
        idle, kernel, user = FILETIME(), FILETIME(), FILETIME()
        if not ctypes.windll.kernel32.GetSystemTimes(
            ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)
        ):
            raise OSError("GetSystemTimes 失敗")

        def def_combine(value: FILETIME) -> int:
            return (value.high << 32) | value.low

        return def_combine(idle), def_combine(kernel), def_combine(user)

    first = def_snapshot()
    time.sleep(interval)
    second = def_snapshot()
    idle_delta = second[0] - first[0]
    total_delta = (second[1] - first[1]) + (second[2] - first[2])
    return 0.0 if total_delta <= 0 else 100.0 * (1.0 - idle_delta / total_delta)


def def_posix_cpu_percent(interval: float) -> float:
    def def_snapshot() -> tuple[int, int]:
        fields = Path("/proc/stat").read_text(encoding="ascii").splitlines()[0].split()[1:]
        values = [int(value) for value in fields]
        idle = values[3] + (values[4] if len(values) > 4 else 0)
        return idle, sum(values)

    first_idle, first_total = def_snapshot()
    time.sleep(interval)
    second_idle, second_total = def_snapshot()
    total_delta = second_total - first_total
    return 0.0 if total_delta <= 0 else 100.0 * (
        1.0 - (second_idle - first_idle) / total_delta
    )


def def_cpu_percent(interval: float) -> float:
    try:
        import psutil  # type: ignore

        return float(psutil.cpu_percent(interval=interval))
    except ImportError:
        if os.name == "nt":
            return def_windows_cpu_percent(interval)
        if Path("/proc/stat").exists():
            return def_posix_cpu_percent(interval)
        raise RuntimeError("缺少 psutil，且作業系統沒有可用的 CPU 備援介面")


def def_resource_snapshot(temp_root: Path) -> ResourceSnapshot:
    cpu = def_cpu_percent(float(RESOURCE_GATE_SAMPLE_SECONDS))
    memory_used, available_gib = def_memory_snapshot()
    disk = shutil.disk_usage(temp_root)
    return ResourceSnapshot(
        cpu_percent=round(cpu, 2),
        memory_used_percent=round(memory_used, 2),
        available_memory_gib=round(available_gib, 2),
        disk_free_gib=round(disk.free / (1024**3), 2),
        disk_free_percent=round(100.0 * disk.free / disk.total, 2),
    )


def def_resource_gate_passes(snapshot: ResourceSnapshot) -> tuple[bool, list[str]]:
    failures: list[str] = []
    if snapshot.cpu_percent > MAX_CPU_PERCENT:
        failures.append(f"CPU {snapshot.cpu_percent:.1f}% > {MAX_CPU_PERCENT:.1f}%")
    if snapshot.memory_used_percent > MAX_MEMORY_USED_PERCENT:
        failures.append(
            f"DRAM {snapshot.memory_used_percent:.1f}% > {MAX_MEMORY_USED_PERCENT:.1f}%"
        )
    if snapshot.available_memory_gib < MIN_AVAILABLE_MEMORY_GIB:
        failures.append(
            f"可用 DRAM {snapshot.available_memory_gib:.1f} GiB < "
            f"{MIN_AVAILABLE_MEMORY_GIB:.1f} GiB"
        )
    if snapshot.disk_free_gib < MIN_TEMP_DISK_FREE_GIB:
        failures.append(
            f"TEMP SSD 可用 {snapshot.disk_free_gib:.1f} GiB < "
            f"{MIN_TEMP_DISK_FREE_GIB:.1f} GiB"
        )
    if snapshot.disk_free_percent < MIN_TEMP_DISK_FREE_PERCENT:
        failures.append(
            f"TEMP SSD 可用 {snapshot.disk_free_percent:.1f}% < "
            f"{MIN_TEMP_DISK_FREE_PERCENT:.1f}%"
        )
    return not failures, failures


def def_wait_for_resource_gate(temp_root: Path) -> ResourceSnapshot:
    started = time.monotonic()
    consecutive = 0
    last_snapshot: ResourceSnapshot | None = None
    while time.monotonic() - started <= RESOURCE_GATE_TIMEOUT_SECONDS:
        last_snapshot = def_resource_snapshot(temp_root)
        passed, failures = def_resource_gate_passes(last_snapshot)
        if passed:
            consecutive += 1
            print(
                "def Resource Gate PASS "
                f"({consecutive}/{RESOURCE_GATE_REQUIRED_CONSECUTIVE_PASSES}) · "
                f"CPU={last_snapshot.cpu_percent:.1f}% · "
                f"DRAM={last_snapshot.memory_used_percent:.1f}% · "
                f"Free={last_snapshot.available_memory_gib:.1f} GiB · "
                f"SSD={last_snapshot.disk_free_gib:.1f} GiB",
                flush=True,
            )
            if consecutive >= RESOURCE_GATE_REQUIRED_CONSECUTIVE_PASSES:
                return last_snapshot
        else:
            consecutive = 0
            print(f"def Resource Gate WAIT · {'；'.join(failures)}", flush=True)
        time.sleep(1)
    raise TimeoutError(f"資源 Gate 在 {RESOURCE_GATE_TIMEOUT_SECONDS} 秒內未通過：{last_snapshot}")


# =============================================================================
# def 06 · 高負載工具受控啟動
# =============================================================================


def def_workload_environment(current_temp: Path) -> dict[str, str]:
    environment = os.environ.copy()
    generic = str(current_temp / "generic")
    environment.update(
        {
            "TEMP": generic,
            "TMP": generic,
            "TMPDIR": generic,
            "DUCKDB_TEMP_DIRECTORY": str(current_temp / "duckdb"),
            "JOBLIB_TEMP_FOLDER": str(current_temp / "joblib"),
            "DASK_TEMPORARY_DIRECTORY": str(current_temp / "dask"),
            "MPLCONFIGDIR": str(current_temp / "matplotlib"),
            "PYTHONPYCACHEPREFIX": str(current_temp / "python_cache"),
            "OMP_NUM_THREADS": str(MAX_WORKER_THREADS),
            "MKL_NUM_THREADS": str(MAX_WORKER_THREADS),
            "OPENBLAS_NUM_THREADS": str(MAX_WORKER_THREADS),
            "NUMEXPR_MAX_THREADS": str(MAX_WORKER_THREADS),
            "POLARS_MAX_THREADS": str(MAX_WORKER_THREADS),
            "RAYON_NUM_THREADS": str(MAX_WORKER_THREADS),
            "TOKENIZERS_PARALLELISM": "false",
        }
    )
    return environment


def def_apply_affinity(process: subprocess.Popen[Any], metrics: RunMetrics) -> None:
    core_count = min(MAX_CPU_CORES_FOR_WORKLOAD, os.cpu_count() or 1)
    try:
        import psutil  # type: ignore

        target = psutil.Process(process.pid)
        target.cpu_affinity(list(range(core_count)))
    except ImportError:
        if hasattr(os, "sched_setaffinity"):
            os.sched_setaffinity(process.pid, set(range(core_count)))
        else:
            metrics.warnings.append("未安裝 psutil，無法套用 Windows CPU affinity")
    except (OSError, ValueError) as exc:
        metrics.warnings.append(f"CPU affinity 套用失敗：{exc}")


def def_record_resource_snapshot(
    snapshot: ResourceSnapshot,
    metrics: RunMetrics,
    log_path: Path,
    scope: str,
    item: str = "",
) -> None:
    metrics.resource_samples += 1
    metrics.peak_cpu_percent = max(metrics.peak_cpu_percent, snapshot.cpu_percent)
    metrics.peak_memory_used_percent = max(
        metrics.peak_memory_used_percent, snapshot.memory_used_percent
    )
    if metrics.minimum_available_memory_gib is None:
        metrics.minimum_available_memory_gib = snapshot.available_memory_gib
    else:
        metrics.minimum_available_memory_gib = min(
            metrics.minimum_available_memory_gib, snapshot.available_memory_gib
        )
    def_append_jsonl(
        log_path,
        {
            "timestamp": def_now_utc(),
            "scope": scope,
            "item": item,
            **asdict(snapshot),
        },
    )


def def_memory_is_critical(snapshot: ResourceSnapshot) -> bool:
    return (
        snapshot.memory_used_percent >= CRITICAL_MEMORY_USED_PERCENT
        or snapshot.available_memory_gib <= CRITICAL_MIN_AVAILABLE_MEMORY_GIB
    )


def def_terminate_process(process: subprocess.Popen[Any], grace_seconds: int = 10) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=grace_seconds)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=grace_seconds)


def def_monitor_process(
    process: subprocess.Popen[Any],
    metrics: RunMetrics,
    temp_root: Path,
    resource_log_path: Path,
    scope: str,
    item: str = "",
    abort_on_critical_memory: bool = False,
    max_runtime_seconds: int = 0,
) -> tuple[int, bool]:
    critical_samples = 0
    aborted_for_memory = False
    started = time.monotonic()
    try:
        while process.poll() is None:
            snapshot = def_resource_snapshot(temp_root)
            def_record_resource_snapshot(snapshot, metrics, resource_log_path, scope, item)
            print(
                f"def Monitor · Scope={scope} · CPU={snapshot.cpu_percent:.1f}% · "
                f"DRAM={snapshot.memory_used_percent:.1f}% · "
                f"Available={snapshot.available_memory_gib:.1f} GiB · "
                f"SSD={snapshot.disk_free_gib:.1f} GiB",
                flush=True,
            )
            if def_memory_is_critical(snapshot):
                critical_samples += 1
            else:
                critical_samples = 0
            if (
                abort_on_critical_memory
                and AUTO_ABORT_BATCH_ITEM_ON_CRITICAL_MEMORY
                and critical_samples >= CRITICAL_MEMORY_CONSECUTIVE_SAMPLES
            ):
                def_terminate_process(process)
                aborted_for_memory = True
                metrics.warnings.append(
                    f"批次項目因嚴重 DRAM 壓力中止並排入重試：{item}"
                )
                break
            if max_runtime_seconds > 0 and time.monotonic() - started >= max_runtime_seconds:
                def_terminate_process(process)
                metrics.warnings.append(
                    f"批次項目超過 {max_runtime_seconds} 秒，已中止並排入重試：{item}"
                )
                aborted_for_memory = True
                break
            remaining = max(
                0.0, WORKLOAD_MONITOR_INTERVAL_SECONDS - RESOURCE_GATE_SAMPLE_SECONDS
            )
            if remaining:
                time.sleep(remaining)
    except KeyboardInterrupt:
        def_terminate_process(process)
        raise
    return int(process.wait()), aborted_for_memory


def def_launch_workload(
    command: Sequence[str],
    current_temp: Path,
    metrics: RunMetrics,
    resource_log_path: Path,
    scope: str = "WORKLOAD",
    item: str = "",
    abort_on_critical_memory: bool = False,
    max_runtime_seconds: int = 0,
) -> int | None:
    if not command:
        metrics.warnings.append("未設定高負載工具命令；前置清理與資源準備已完成")
        return None
    executable = Path(command[0]).expanduser()
    if ("/" in command[0] or "\\" in command[0]) and not executable.exists():
        raise FileNotFoundError(f"高負載工具不存在：{executable}")
    creationflags = 0
    start_new_session = False
    if os.name == "nt" and LOWER_WORKLOAD_PRIORITY:
        creationflags |= getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0)
    elif os.name != "nt":
        start_new_session = True

    process = subprocess.Popen(
        list(command),
        env=def_workload_environment(current_temp),
        shell=False,
        creationflags=creationflags,
        start_new_session=start_new_session,
    )
    metrics.workload_started = True
    def_apply_affinity(process, metrics)
    if WAIT_FOR_WORKLOAD:
        return def_monitor_process(
            process,
            metrics,
            current_temp,
            resource_log_path,
            scope,
            item,
            abort_on_critical_memory,
            max_runtime_seconds,
        )[0]
    return None


# =============================================================================
# def 06A · 可續跑 Batch Fetching 控制層
# =============================================================================


def def_read_batch_items(items_file: Path, item_column: str) -> list[str]:
    suffix = items_file.suffix.casefold()
    items: list[str] = []
    if suffix == ".json":
        payload = json.loads(items_file.read_text(encoding="utf-8-sig"))
        if not isinstance(payload, list):
            raise ValueError("Batch JSON 必須是陣列")
        for row in payload:
            value = row.get(item_column) if isinstance(row, dict) else row
            if value is not None and str(value).strip():
                items.append(str(value).strip())
    elif suffix in {".jsonl", ".ndjson"}:
        with items_file.open("r", encoding="utf-8-sig") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                value = row.get(item_column) if isinstance(row, dict) else row
                if value is not None and str(value).strip():
                    items.append(str(value).strip())
    elif suffix in {".csv", ".tsv"}:
        delimiter = "\t" if suffix == ".tsv" else ","
        with items_file.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, delimiter=delimiter)
            if not reader.fieldnames or item_column not in reader.fieldnames:
                raise ValueError(
                    f"Batch 表格缺少欄位 {item_column!r}；現有欄位={reader.fieldnames}"
                )
            for row in reader:
                value = str(row.get(item_column, "")).strip()
                if value:
                    items.append(value)
    else:
        with items_file.open("r", encoding="utf-8-sig") as handle:
            items.extend(line.strip() for line in handle if line.strip())
    return list(dict.fromkeys(items))


def def_batch_job_id(
    items_file: Path, item_column: str, command_template: Sequence[str], explicit: str
) -> str:
    if explicit:
        if not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", explicit):
            raise ValueError("--batch-job-id 只允許英數、底線、句點與連字號")
        return explicit
    payload = json.dumps(
        {
            "items_file": str(items_file.resolve(strict=True)),
            "item_column": item_column,
            "command": list(command_template),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return "BATCH_" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def def_initialize_batch_job(
    connection: sqlite3.Connection,
    job_id: str,
    items_file: Path,
    command_template: Sequence[str],
    items: Sequence[str],
    metrics: RunMetrics,
) -> None:
    now = def_now_utc()
    interrupted_count = int(
        connection.execute(
            "SELECT COUNT(*) FROM batch_items WHERE job_id = ? AND status = 'RUNNING'",
            (job_id,),
        ).fetchone()[0]
    )
    metrics.batch_items_recovered_after_interruption = interrupted_count
    connection.execute(
        "INSERT OR IGNORE INTO batch_jobs "
        "(job_id, items_file, command_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (job_id, str(items_file), json.dumps(list(command_template)), now, now),
    )
    connection.execute(
        "UPDATE batch_jobs SET updated_at = ? WHERE job_id = ?", (now, job_id)
    )
    connection.execute(
        "UPDATE batch_items SET status = 'PENDING', last_error = ? "
        "WHERE job_id = ? AND status = 'RUNNING'",
        ("上一輪在 RUNNING 狀態中斷，已自動恢復為 PENDING", job_id),
    )
    if BATCH_RESET_FAILED_ON_NEXT_RUN:
        connection.execute(
            "UPDATE batch_items SET status = 'PENDING' "
            "WHERE job_id = ? AND status = 'FAILED' AND attempts < ?",
            (job_id, BATCH_MAX_RETRIES),
        )
    for ordinal, item in enumerate(items, start=1):
        item_key = hashlib.sha256(item.encode("utf-8")).hexdigest()
        connection.execute(
            "INSERT OR IGNORE INTO batch_items "
            "(job_id, item_key, item_value, ordinal, status, attempts, updated_at) "
            "VALUES (?, ?, ?, ?, 'PENDING', 0, ?)",
            (job_id, item_key, item, ordinal, now),
        )
    connection.commit()
    metrics.batch_job_id = job_id
    metrics.batch_items_total = int(
        connection.execute(
            "SELECT COUNT(*) FROM batch_items WHERE job_id = ?", (job_id,)
        ).fetchone()[0]
    )
    metrics.batch_items_resumed = int(
        connection.execute(
            "SELECT COUNT(*) FROM batch_items "
            "WHERE job_id = ? AND status = 'COMPLETED'",
            (job_id,),
        ).fetchone()[0]
    )


def def_expand_batch_command(template: Sequence[str], item: str, attempt: int) -> tuple[str, ...]:
    if not any("{item}" in part for part in template):
        raise ValueError("Batch 命令必須至少包含一個 {item} 佔位符")
    return tuple(
        part.replace("{item}", item).replace("{attempt}", str(attempt))
        for part in template
    )


def def_run_batch_fetching(
    connection: sqlite3.Connection,
    paths: RuntimePaths,
    current_temp: Path,
    metrics: RunMetrics,
    items_file: Path,
    item_column: str,
    command_template: Sequence[str],
    explicit_job_id: str,
) -> int:
    items = def_read_batch_items(items_file, item_column)
    if not items:
        raise ValueError(f"Batch 清單沒有可執行項目：{items_file}")
    job_id = def_batch_job_id(items_file, item_column, command_template, explicit_job_id)
    def_initialize_batch_job(
        connection, job_id, items_file, command_template, items, metrics
    )
    resource_log = paths.report_root / "resource_monitor.jsonl"

    while True:
        row = connection.execute(
            "SELECT item_key, item_value, attempts FROM batch_items "
            "WHERE job_id = ? AND status = 'PENDING' AND attempts < ? "
            "ORDER BY ordinal LIMIT 1",
            (job_id, BATCH_MAX_RETRIES),
        ).fetchone()
        if row is None:
            break
        item_key, item, previous_attempts = row
        attempt = int(previous_attempts) + 1
        if attempt > 1:
            metrics.batch_retries += 1
            delay = BATCH_RETRY_BASE_DELAY_SECONDS * (2 ** (attempt - 2))
            print(f"def Batch Retry · Item={item} · Attempt={attempt} · Delay={delay}s")
            time.sleep(delay)

        def_wait_for_resource_gate(current_temp)
        connection.execute(
            "UPDATE batch_items SET status = 'RUNNING', attempts = ?, updated_at = ? "
            "WHERE job_id = ? AND item_key = ?",
            (attempt, def_now_utc(), job_id, item_key),
        )
        connection.commit()
        command = def_expand_batch_command(command_template, item, attempt)
        print(
            f"def Batch Fetch · Job={job_id} · Item={item} · "
            f"Attempt={attempt}/{BATCH_MAX_RETRIES}",
            flush=True,
        )
        try:
            return_code = def_launch_workload(
                command,
                current_temp,
                metrics,
                resource_log,
                scope="BATCH_FETCH",
                item=item,
                abort_on_critical_memory=True,
                max_runtime_seconds=BATCH_ITEM_TIMEOUT_SECONDS,
            )
            success = return_code == 0
            last_error = "" if success else f"return_code={return_code}"
        except KeyboardInterrupt:
            metrics.status = "INTERRUPTED_RECOVERABLE"
            metrics.errors.append(
                "KeyboardInterrupt: 執行已中斷；Batch RUNNING 項目將於下次自動恢復"
            )
            return_code = 130
        except Exception as exc:
            return_code = None
            success = False
            last_error = f"{type(exc).__name__}: {exc}"

        final_failure = not success and attempt >= BATCH_MAX_RETRIES
        next_status = "COMPLETED" if success else ("FAILED" if final_failure else "PENDING")
        connection.execute(
            "UPDATE batch_items SET status = ?, last_return_code = ?, last_error = ?, "
            "updated_at = ? WHERE job_id = ? AND item_key = ?",
            (next_status, return_code, last_error, def_now_utc(), job_id, item_key),
        )
        connection.commit()
        if success:
            metrics.batch_items_completed += 1
        elif final_failure:
            metrics.batch_items_failed += 1
            metrics.warnings.append(f"Batch 最終失敗：{item}：{last_error}")
            if not BATCH_CONTINUE_AFTER_FINAL_FAILURE:
                break

    totals = dict(
        connection.execute(
            "SELECT status, COUNT(*) FROM batch_items WHERE job_id = ? GROUP BY status",
            (job_id,),
        ).fetchall()
    )
    def_write_json_atomic(
        paths.report_root / "batch_checkpoint_summary.json",
        {"job_id": job_id, "status_counts": totals, "updated_at": def_now_utc()},
    )
    with (paths.report_root / "batch_checkpoint_items.csv").open(
        "w", encoding=REPORT_ENCODING, newline=""
    ) as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "Job Id",
                "Ordinal",
                "Item",
                "Status",
                "Attempts",
                "Last Return Code",
                "Last Error",
                "Updated At",
            ]
        )
        writer.writerows(
            connection.execute(
                "SELECT job_id, ordinal, item_value, status, attempts, "
                "last_return_code, last_error, updated_at FROM batch_items "
                "WHERE job_id = ? ORDER BY ordinal",
                (job_id,),
            )
        )
    return 0 if int(totals.get("FAILED", 0)) == 0 else 3


# =============================================================================
# def 07 · 稽核報告
# =============================================================================


def def_write_csv_report(path: Path, records: Sequence[DuplicateRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding=REPORT_ENCODING, newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(asdict(records[0]).keys())
            if records
            else [
                "group_id",
                "keeper_path",
                "duplicate_path",
                "size_bytes",
                "sha256",
                "decision",
                "reason",
                "quarantine_path",
            ],
        )
        writer.writeheader()
        for record in records:
            writer.writerow(asdict(record))


def def_write_html_report(
    path: Path,
    metrics: RunMetrics,
    records: Sequence[DuplicateRecord],
    runtime_paths: RuntimePaths,
) -> None:
    summary_rows = "".join(
        f"<tr><th>{html.escape(str(key))}</th><td>{html.escape(str(value))}</td></tr>"
        for key, value in asdict(metrics).items()
        if key not in {"warnings", "errors"}
    )
    record_rows = "".join(
        "<tr>"
        f"<td>{html.escape(item.group_id)}</td>"
        f"<td>{html.escape(item.keeper_path)}</td>"
        f"<td>{html.escape(item.duplicate_path)}</td>"
        f"<td>{item.size_bytes:,}</td>"
        f"<td>{html.escape(item.decision)}</td>"
        f"<td>{html.escape(item.reason)}</td>"
        "</tr>"
        for item in records
    ) or "<tr><td colspan='6'>未發現符合條件的完全重複檔案</td></tr>"
    warnings = "".join(f"<li>{html.escape(item)}</li>" for item in metrics.warnings)
    errors = "".join(f"<li>{html.escape(item)}</li>" for item in metrics.errors)
    document = f"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA SSD Resource Guard</title>
<style>
:root{{--bg:#f5f8fb;--card:#fff;--ink:#203040;--muted:#61758a;--line:#d9e3ec;--blue:#4c78a8;--green:#72b7b2;--orange:#f2a65a;}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--ink);font-family:Inter,"Noto Sans TC",sans-serif}}
main{{max-width:1240px;margin:32px auto;padding:0 20px}} .card{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px;margin:16px 0;box-shadow:0 6px 18px rgba(48,75,96,.07)}}
h1{{margin:0 0 6px;font-size:25px}} h2{{font-size:18px}} p{{color:var(--muted)}} table{{width:100%;border-collapse:collapse;font-size:13px}} th,td{{padding:9px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top;word-break:break-word}} th{{color:#35556f;background:#edf4f8}} .scroll{{overflow:auto}} code{{color:#35556f}}</style></head>
<body><main><div class="card"><h1>Veritas Intelligence Analytics</h1><p>SSD Resource Guard · {html.escape(ENGINE_VERSION)} · {html.escape(metrics.status)}</p><p>Reports: <code>{html.escape(str(runtime_paths.report_root))}</code></p></div>
<div class="card"><h2>執行摘要</h2><table>{summary_rows}</table></div>
<div class="card"><h2>完全重複檔案決策</h2><div class="scroll"><table><thead><tr><th>Group</th><th>Keeper</th><th>Duplicate</th><th>Bytes</th><th>Decision</th><th>Reason</th></tr></thead><tbody>{record_rows}</tbody></table></div></div>
<div class="card"><h2>Warnings</h2><ul>{warnings or '<li>None</li>'}</ul><h2>Errors</h2><ul>{errors or '<li>None</li>'}</ul></div>
</main></body></html>"""
    path.write_text(document, encoding="utf-8")


def def_write_reports(
    paths: RuntimePaths,
    metrics: RunMetrics,
    records: Sequence[DuplicateRecord],
) -> None:
    paths.report_root.mkdir(parents=True, exist_ok=True)
    def_write_json_atomic(paths.report_root / "summary.json", asdict(metrics))
    def_write_json_atomic(
        paths.report_root / "duplicates.json", [asdict(item) for item in records]
    )
    def_write_csv_report(paths.report_root / "duplicates.csv", records)
    def_write_html_report(paths.report_root / "report.html", metrics, records, paths)


# =============================================================================
# def 08 · CLI、自動管線與主入口
# =============================================================================


def def_parse_arguments(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="VIA SSD Resource Guard：安全去重、受管 TEMP 與高負載工具資源 Gate"
    )
    parser.add_argument("--scan-root", action="append", help="掃描根目錄，可重複指定")
    parser.add_argument("--temp-root", help="受管 SSD TEMP 根目錄")
    parser.add_argument("--state-root", help="SQLite 與報告目錄")
    parser.add_argument("--quarantine-root", help="重複檔案隔離目錄")
    parser.add_argument("--report-only", action="store_true", help="只報告，不隔離")
    parser.add_argument(
        "--purge-quarantine-now",
        action="store_true",
        help="驗證 Hash 後，立即永久清除既有隔離檔",
    )
    parser.add_argument("--restore-manifest", help="依 manifest 還原隔離檔並結束")
    parser.add_argument("--batch-items", help="Batch 清單：TXT／CSV／TSV／JSON／JSONL")
    parser.add_argument(
        "--batch-item-column",
        default=BATCH_ITEM_COLUMN,
        help="CSV／TSV／JSON 物件中的項目欄位名稱",
    )
    parser.add_argument("--batch-job-id", default="", help="固定 checkpoint 工作 ID")
    parser.add_argument(
        "--batch-command",
        nargs=argparse.REMAINDER,
        help="每筆執行命令，必須包含 {item}；此參數必須放在最後",
    )
    parser.add_argument(
        "--workload",
        nargs=argparse.REMAINDER,
        help="資源 Gate 通過後啟動的完整命令；此參數必須放在最後",
    )
    parser.add_argument(
        "--run-id",
        default=datetime.now().strftime("RUN_%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8],
        help=argparse.SUPPRESS,
    )
    return parser.parse_args(argv)


def def_resolve_workload(args: argparse.Namespace) -> tuple[str, ...]:
    if args.workload:
        return tuple(args.workload)
    return WORKLOAD_COMMAND


def def_resolve_batch_configuration(
    args: argparse.Namespace,
) -> tuple[Path | None, tuple[str, ...]]:
    raw_file = args.batch_items or BATCH_ITEMS_FILE
    command = tuple(args.batch_command or BATCH_FETCH_COMMAND_TEMPLATE)
    if not raw_file and not command:
        return None, tuple()
    if not raw_file or not command:
        raise ValueError("Batch Fetching 必須同時設定清單檔與命令範本")
    items_file = def_resolve_path(raw_file)
    if not items_file.is_file():
        raise FileNotFoundError(f"Batch 清單不存在：{items_file}")
    return items_file, command


def def_run_pipeline(args: argparse.Namespace) -> tuple[int, RuntimePaths, RunMetrics]:
    paths = def_resolve_runtime_paths(args)
    metrics = RunMetrics(run_id=args.run_id, started_at=def_now_utc())
    records: list[DuplicateRecord] = []
    connection: sqlite3.Connection | None = None
    current_temp: Path | None = None
    paths.state_root.mkdir(parents=True, exist_ok=True)

    with def_engine_lock(paths.lock_path):
        try:
            def_write_progress(2, f"SSD Resource Guard v{ENGINE_VERSION}")
            def_write_progress(7, "驗證受管 TEMP 與隔離區")
            current_temp = def_reset_previous_temp(paths, args.run_id, metrics)
            def_purge_expired_quarantines(paths, metrics, args.purge_quarantine_now)

            def_write_progress(18, "開啟 SQLite 增量索引")
            connection = def_open_database(paths.database_path)
            def_write_progress(30, "低 DRAM 串流盤點檔案")
            def_inventory_files(connection, paths, args.run_id, metrics)

            def_write_progress(48, "大小分組與頭尾快速指紋")
            def_compute_candidate_hashes(connection, args.run_id, metrics)
            def_write_progress(64, "完整 SHA-256 驗證與保守決策")
            records = def_find_and_handle_duplicates(
                connection,
                paths,
                args.run_id,
                metrics,
                report_only=args.report_only,
            )

            def_write_progress(76, "等待 CPU／DRAM／SSD 資源 Gate")
            snapshot = def_wait_for_resource_gate(current_temp)
            def_write_json_atomic(paths.report_root / "resource_gate.json", asdict(snapshot))

            workload = def_resolve_workload(args)
            batch_items_file, batch_command = def_resolve_batch_configuration(args)
            if workload and batch_items_file:
                raise ValueError("單一 workload 與 Batch Fetching 不可同時啟動")
            if batch_items_file is not None:
                def_write_progress(88, "啟動可續跑 Batch Fetching")
                metrics.workload_return_code = def_run_batch_fetching(
                    connection,
                    paths,
                    current_temp,
                    metrics,
                    batch_items_file,
                    args.batch_item_column,
                    batch_command,
                    args.batch_job_id,
                )
            else:
                def_write_progress(
                    88,
                    "啟動受控高負載工具" if workload else "未設定工具，完成前置準備",
                )
                metrics.workload_return_code = def_launch_workload(
                    workload,
                    current_temp,
                    metrics,
                    paths.report_root / "resource_monitor.jsonl",
                )
            if metrics.workload_return_code not in (None, 0):
                raise RuntimeError(f"高負載工具回傳非零代碼：{metrics.workload_return_code}")
            metrics.status = "PASS"
            return_code = 0
        except Exception as exc:
            metrics.status = "FAIL_CLOSED"
            metrics.errors.append(f"{type(exc).__name__}: {exc}")
            metrics.errors.append(traceback.format_exc())
            return_code = 1
        finally:
            metrics.finished_at = def_now_utc()
            if connection is not None:
                connection.close()
            try:
                def_write_reports(paths, metrics, records)
            except Exception as report_exc:
                print(f"def [ERROR] 報告輸出失敗：{report_exc}", file=sys.stderr)
                return_code = 2

    def_write_progress(100, f"Gate={metrics.status} · Report={paths.report_root}", metrics.status)
    return return_code, paths, metrics


def def_main(argv: Sequence[str] | None = None) -> int:
    args = def_parse_arguments(argv)
    if args.restore_manifest:
        restored = def_restore_manifest(def_resolve_path(args.restore_manifest))
        print(f"def Restore PASS · Restored={restored}")
        return 0
    return_code, paths, metrics = def_run_pipeline(args)
    print(f"def Files Scanned       : {metrics.files_scanned:,}")
    print(f"def Duplicate Files     : {metrics.exact_duplicate_files:,}")
    print(f"def Quarantined         : {metrics.files_quarantined:,}")
    print(f"def Prior TEMP Deleted  : {def_human_bytes(metrics.prior_temp_bytes_deleted)}")
    print(f"def Report HTML         : {paths.report_root / 'report.html'}")
    if metrics.errors:
        print(f"def Error               : {metrics.errors[0]}", file=sys.stderr)
    return return_code


if __name__ == "__main__":
    raise SystemExit(def_main())
