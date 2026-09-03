#!/usr/bin/env python3
"""Small cross-platform atomic I/O and transaction-lock helpers for VAP."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Mapping


_THREAD_LOCKS: dict[str, threading.RLock] = {}
_THREAD_LOCKS_GUARD = threading.Lock()
_LOCK_DEPTH = threading.local()


def _canonical_key(path: str | Path) -> str:
    return os.path.normcase(str(Path(path).expanduser().resolve()))


def _thread_lock(key: str) -> threading.RLock:
    with _THREAD_LOCKS_GUARD:
        return _THREAD_LOCKS.setdefault(key, threading.RLock())


def _lock_file_path(key: str) -> Path:
    digest = hashlib.sha256(key.encode("utf-8", errors="surrogatepass")).hexdigest()
    root = Path(tempfile.gettempdir()) / "vap-seaborn-locks"
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    return root / f"{digest}.lock"


def _acquire_os_lock(handle: Any) -> None:
    if os.name == "nt":
        import msvcrt

        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"\0")
            handle.flush()
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        return
    import fcntl

    fcntl.flock(handle.fileno(), fcntl.LOCK_EX)


def _release_os_lock(handle: Any) -> None:
    if os.name == "nt":
        import msvcrt

        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        return
    import fcntl

    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


@contextmanager
def file_transaction_lock(path: str | Path) -> Iterator[None]:
    """Serialize a complete read-modify-write transaction across threads/processes.

    Lock files live in the operating-system temporary directory, so a user's
    chart/config directory is not cluttered.  Nested calls on the same thread
    are re-entrant and acquire the operating-system lock only once.
    """

    key = _canonical_key(path)
    lock = _thread_lock(key)
    with lock:
        depths = getattr(_LOCK_DEPTH, "values", None)
        if depths is None:
            depths = {}
            _LOCK_DEPTH.values = depths
        if depths.get(key, 0):
            depths[key] += 1
            try:
                yield
            finally:
                depths[key] -= 1
            return

        lock_path = _lock_file_path(key)
        with lock_path.open("a+b") as handle:
            _acquire_os_lock(handle)
            depths[key] = 1
            try:
                yield
            finally:
                depths.pop(key, None)
                _release_os_lock(handle)


def atomic_write_json(
    path: str | Path,
    value: Mapping[str, Any],
    *,
    allow_nan: bool = False,
) -> None:
    """Write UTF-8 JSON to a unique sibling temp file and atomically replace."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    cleanup_stale_temporary_files(destination)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=destination.parent,
        prefix=f".{destination.name}.",
        suffix=".tmp",
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(
                value,
                handle,
                ensure_ascii=False,
                indent=2,
                allow_nan=allow_nan,
            )
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, destination)
        if os.name != "nt":
            directory_fd = os.open(destination.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
    finally:
        temporary_path.unlink(missing_ok=True)


def atomic_write_text(
    path: str | Path,
    text: str,
    *,
    encoding: str = "utf-8",
) -> None:
    """Write text through a unique sibling temp file and clean up on failure."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    cleanup_stale_temporary_files(destination)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=destination.parent,
        prefix=f".{destination.name}.",
        suffix=".tmp",
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding=encoding, newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, destination)
        if os.name != "nt":
            directory_fd = os.open(destination.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
    finally:
        temporary_path.unlink(missing_ok=True)


def cleanup_stale_temporary_files(
    destination: str | Path,
    *,
    minimum_age_seconds: float = 3600.0,
) -> int:
    """Remove abandoned unique sibling temps left by a terminated process."""

    target = Path(destination)
    parent = target.parent
    if not parent.exists():
        return 0
    prefix = f".{target.name}."
    now = time.time()
    removed = 0
    for candidate in parent.iterdir():
        if not candidate.name.startswith(prefix) or not candidate.name.endswith(".tmp"):
            continue
        try:
            age = now - candidate.stat().st_mtime
            if age < max(0.0, float(minimum_age_seconds)):
                continue
            candidate.unlink(missing_ok=True)
            removed += 1
        except FileNotFoundError:
            continue
    return removed


__all__ = [
    "atomic_write_json",
    "atomic_write_text",
    "cleanup_stale_temporary_files",
    "file_transaction_lock",
]
