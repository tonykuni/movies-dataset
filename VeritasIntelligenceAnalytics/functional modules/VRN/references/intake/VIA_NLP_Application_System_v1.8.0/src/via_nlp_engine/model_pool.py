"""Lazy model pool with TTL, LRU eviction and memory estimates."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Callable

from .resources import ResourceMonitor


@dataclass(slots=True)
class ModelEntry:
    name: str
    value: Any
    estimated_mb: float
    loaded_at: float
    last_used: float
    unload: Callable[[Any], None] | None = None


class LazyModelPool:
    def __init__(self, config: dict[str, Any], monitor: ResourceMonitor) -> None:
        self.config = config
        self.monitor = monitor
        self._entries: OrderedDict[str, ModelEntry] = OrderedDict()
        self._load_locks: dict[str, threading.Lock] = {}
        self._lock = threading.RLock()

    def get_or_load(
        self,
        name: str,
        loader: Callable[[], Any],
        estimated_mb: float,
        unload: Callable[[Any], None] | None = None,
        heavy: bool = False,
    ) -> Any:
        with self._lock:
            entry = self._entries.get(name)
            if entry is not None:
                entry.last_used = time.monotonic()
                self._entries.move_to_end(name)
                return entry.value
            load_lock = self._load_locks.setdefault(name, threading.Lock())

        with load_lock:
            with self._lock:
                entry = self._entries.get(name)
                if entry is not None:
                    entry.last_used = time.monotonic()
                    return entry.value

            self.monitor.admit(estimated_mb=estimated_mb, heavy=heavy)
            self._make_room(estimated_mb)
            value = loader()
            now = time.monotonic()
            with self._lock:
                self._entries[name] = ModelEntry(name, value, estimated_mb, now, now, unload)
                self._entries.move_to_end(name)
            return value

    def _make_room(self, incoming_mb: float) -> None:
        max_items = int(self.config["model_pool_max_items"])
        max_mb = float(self.config["model_pool_max_estimated_mb"])
        with self._lock:
            while self._entries and (
                len(self._entries) >= max_items or self.estimated_mb + incoming_mb > max_mb
            ):
                name = next(iter(self._entries))
                self._evict_locked(name)

    @property
    def estimated_mb(self) -> float:
        return sum(entry.estimated_mb for entry in self._entries.values())

    def evict_idle(self, force: bool = False) -> list[str]:
        now = time.monotonic()
        ttl = float(self.config["model_idle_ttl_seconds"])
        removed: list[str] = []
        with self._lock:
            for name, entry in list(self._entries.items()):
                if force or now - entry.last_used >= ttl:
                    self._evict_locked(name)
                    removed.append(name)
        if removed:
            self.monitor.release_memory()
        return removed

    def _evict_locked(self, name: str) -> None:
        entry = self._entries.pop(name, None)
        if entry is None:
            return
        if entry.unload:
            try:
                entry.unload(entry.value)
            except Exception:
                pass
        del entry.value

    def status(self) -> list[dict[str, Any]]:
        now = time.monotonic()
        with self._lock:
            return [
                {
                    "name": entry.name,
                    "estimated_mb": entry.estimated_mb,
                    "age_seconds": round(now - entry.loaded_at, 2),
                    "idle_seconds": round(now - entry.last_used, 2),
                }
                for entry in self._entries.values()
            ]

