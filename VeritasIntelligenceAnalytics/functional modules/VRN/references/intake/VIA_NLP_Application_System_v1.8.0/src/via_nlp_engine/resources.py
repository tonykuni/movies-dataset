"""Cross-platform resource monitoring and admission control."""

from __future__ import annotations

import gc
import importlib.util
import os
import platform
import threading
import time
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Callable

from .schemas import ResourceSnapshot


MB = 1024 * 1024
PSUTIL_AVAILABLE = importlib.util.find_spec("psutil") is not None


class ResourcePressureError(RuntimeError):
    """Raised when a task would make the host unsafe."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fallback_memory() -> tuple[float, float, float]:
    """Return ram_percent, available_mb, process_rss_mb without psutil."""
    process_rss_mb = 0.0
    available_mb = 0.0
    ram_percent = 0.0
    try:
        import resource

        raw = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        process_rss_mb = raw / MB if platform.system() == "Darwin" else raw / 1024.0
    except (ImportError, OSError, ValueError):
        pass

    if platform.system() == "Windows":
        try:
            import ctypes

            class MemoryStatusEx(ctypes.Structure):
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

            status = MemoryStatusEx()
            status.dwLength = ctypes.sizeof(status)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                ram_percent = float(status.dwMemoryLoad)
                available_mb = float(status.ullAvailPhys / MB)
        except (AttributeError, OSError, ValueError):
            pass
    elif platform.system() == "Linux":
        try:
            values: dict[str, int] = {}
            with open("/proc/meminfo", "r", encoding="utf-8") as handle:
                for line in handle:
                    key, raw = line.split(":", 1)
                    values[key] = int(raw.strip().split()[0])
            total_kb = values.get("MemTotal", 0)
            available_kb = values.get("MemAvailable", values.get("MemFree", 0))
            available_mb = available_kb / 1024.0
            if total_kb:
                ram_percent = 100.0 * (1.0 - available_kb / total_kb)
        except (OSError, ValueError):
            pass
    return ram_percent, available_mb, process_rss_mb


class ResourceMonitor:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self._last_cpu = 0.0
        self._lock = threading.RLock()
        self._psutil = None
        if PSUTIL_AVAILABLE:
            import psutil

            self._psutil = psutil
            self._process = psutil.Process(os.getpid())
            self._process.cpu_percent(interval=None)

    def snapshot(self) -> ResourceSnapshot:
        with self._lock:
            if self._psutil:
                virtual = self._psutil.virtual_memory()
                ram_percent = float(virtual.percent)
                available_mb = float(virtual.available / MB)
                process_rss_mb = float(self._process.memory_info().rss / MB)
                cpu_percent = float(self._psutil.cpu_percent(interval=None))
                source = "psutil"
            else:
                ram_percent, available_mb, process_rss_mb = _fallback_memory()
                cpu_percent = self._last_cpu
                source = "stdlib_fallback"

            pressure = self._pressure(ram_percent, available_mb, cpu_percent)
            return ResourceSnapshot(
                timestamp=_utc_now(),
                ram_percent=round(ram_percent, 2),
                available_ram_mb=round(available_mb, 2),
                process_rss_mb=round(process_rss_mb, 2),
                cpu_percent=round(cpu_percent, 2),
                pressure=pressure,
                source=source,
            )

    def _pressure(self, ram: float, available_mb: float, cpu: float) -> str:
        cfg = self.config
        if ram <= 0 and available_mb <= 0:
            return "unknown"
        if ram >= float(cfg["critical_ram_percent"]) or cpu >= float(cfg["critical_cpu_percent"]):
            return "critical"
        if ram >= float(cfg["shed_ram_percent"]) or available_mb < float(cfg["min_available_ram_mb"]):
            return "shed"
        if ram >= float(cfg["warning_ram_percent"]) or cpu >= float(cfg["warning_cpu_percent"]):
            return "warning"
        return "normal"

    def admit(self, estimated_mb: float = 0.0, heavy: bool = False) -> ResourceSnapshot:
        snapshot = self.snapshot()
        projected_available = snapshot.available_ram_mb - estimated_mb
        if snapshot.pressure == "critical":
            self.release_memory()
            raise ResourcePressureError("Critical host pressure: request rejected safely")
        if heavy and snapshot.pressure in {"warning", "shed"}:
            raise ResourcePressureError("Heavy task rejected under current host pressure")
        if projected_available > 0 and projected_available < float(self.config["min_available_ram_mb"]):
            raise ResourcePressureError("Estimated task memory would cross the safety reserve")
        return snapshot

    def adaptive_batch_size(self, preferred: int) -> int:
        snapshot = self.snapshot()
        minimum = int(self.config["adaptive_batch_min"])
        maximum = int(self.config["adaptive_batch_max"])
        target = max(minimum, min(preferred, maximum))
        factor = {"normal": 1.0, "warning": 0.5, "shed": 0.25, "critical": 0.0, "unknown": 0.5}[
            snapshot.pressure
        ]
        return max(minimum, int(target * factor)) if factor else 0

    @staticmethod
    def release_memory() -> None:
        gc.collect()
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.ipc_collect()
        except (ImportError, RuntimeError):
            pass

    def health(self) -> dict[str, Any]:
        snapshot = self.snapshot()
        return {
            "status": "ok" if snapshot.pressure in {"normal", "warning", "unknown"} else "degraded",
            "snapshot": asdict(snapshot),
            "psutil_available": bool(self._psutil),
        }


class ResourceWatchdog:
    """Background monitor that can evict idle models on pressure."""

    def __init__(self, monitor: ResourceMonitor, on_pressure: Callable[[str], None]) -> None:
        self.monitor = monitor
        self.on_pressure = on_pressure
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="via-resource-watchdog", daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 5.0) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=timeout)

    def _run(self) -> None:
        interval = max(0.25, float(self.monitor.config["poll_interval_seconds"]))
        while not self._stop.wait(interval):
            pressure = self.monitor.snapshot().pressure
            if pressure in {"shed", "critical"}:
                self.on_pressure(pressure)
