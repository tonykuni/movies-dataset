"""
vdf_supportive_bridge.py — Integration shim for VeritasAegisNexus + VeritasCeleritas

Provides a unified API that ALL VDF fetchers should use:
  bridge.http_get(url, headers=None, timeout=30) -> str | None
  bridge.http_get_json(url, headers=None, timeout=30) -> dict | None
  bridge.parallel_map(fn, items, max_workers=None) -> list
  bridge.cache_get(key) / bridge.cache_set(key, value, ttl_sec=3600)
  bridge.is_alive() -> dict (capability report)

Falls back to plain urllib/threadpool if the supportive modules are unavailable.
This keeps tests/CI working in environments without the Veritas modules.
"""

from __future__ import annotations
import sys
import os
import json
import urllib.request
import urllib.error
import time
import threading
import datetime as _dt
from pathlib import Path
from typing import Any, Callable, Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed

# ============================================================
# Locate supportive_module directory
# ============================================================

_THIS = Path(__file__).resolve()
_CANDIDATE_PATHS = [
    _THIS.parent.parent / "supportive_module",         # /home/claude/VDF_final/supportive_module
    _THIS.parent.parent.parent / "supportive_module",
    Path("C:/Users/tonyk/OneDrive/VeritasIntelligenceAnalytics/module/supportive_module"),
    Path("/mnt/user-data/uploads"),
]


def _bootstrap_paths() -> list[str]:
    added: list[str] = []
    for p in _CANDIDATE_PATHS:
        try:
            if p.exists() and str(p) not in sys.path:
                sys.path.insert(0, str(p))
                added.append(str(p))
        except (OSError, PermissionError):
            continue
    return added


_added = _bootstrap_paths()

# ============================================================
# Try to import Veritas modules (graceful failure)
# ============================================================

_aegis = None
_celeritas = None
_envmanager = None
_aegis_err = ""
_celeritas_err = ""
_envmanager_err = ""

try:
    import VeritasAegisNexus as _aegis_mod  # type: ignore
    _aegis = _aegis_mod
except Exception as e:
    _aegis_err = f"{type(e).__name__}: {e}"

try:
    import VeritasCeleritas as _cel_mod  # type: ignore
    _celeritas = _cel_mod
except Exception as e:
    _celeritas_err = f"{type(e).__name__}: {e}"

try:
    import VIA_EnvManager as _env_mod  # type: ignore
    _envmanager = _env_mod
except Exception as e:
    _envmanager_err = f"{type(e).__name__}: {e}"


# ============================================================
# HTTP layer (wraps Aegis ResilientHTTPClient when available)
# ============================================================

_aegis_client = None
_aegis_client_lock = threading.Lock()


def _get_aegis_client() -> Any:
    """Lazy-init the Aegis ResilientHTTPClient (thread-safe singleton)."""
    global _aegis_client
    if _aegis_client is not None or _aegis is None:
        return _aegis_client
    with _aegis_client_lock:
        if _aegis_client is None:
            try:
                Cls = getattr(_aegis, "ResilientHTTPClient", None)
                Cfg = getattr(_aegis, "HttpConfig", None)
                if Cls and Cfg:
                    _aegis_client = Cls(config=Cfg())
            except Exception:
                _aegis_client = False  # mark failed; don't retry
    return _aegis_client


def http_get(url: str, headers: dict[str, str] | None = None, timeout: int = 30) -> str | None:
    """Robust GET that returns response body as text, or None on failure.

    Uses AegisNexus ResilientHTTPClient when available (retry / circuit-breaker /
    UA rotation / throttle), otherwise falls back to urllib.
    """
    client = _get_aegis_client()
    if client:
        try:
            resp = client.request("GET", url, headers=headers, timeout=timeout)
            if resp is None:
                return None
            # AegisNexus returns a requests.Response
            status = getattr(resp, "status_code", 200)
            if not (200 <= status < 400):
                return None
            text = getattr(resp, "text", None)
            if text is not None:
                return text
            content = getattr(resp, "content", b"")
            if isinstance(content, bytes):
                for enc in ("utf-8", "big5", "cp950"):
                    try:
                        return content.decode(enc)
                    except UnicodeDecodeError:
                        continue
                return content.decode("utf-8", errors="ignore")
        except Exception:
            pass  # fall through to urllib fallback

    # Fallback: plain urllib
    h = {"User-Agent": "VDF/4.0 (Veritas Data Forge)"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            for enc in ("utf-8", "big5", "cp950"):
                try:
                    return raw.decode(enc)
                except UnicodeDecodeError:
                    continue
            return raw.decode("utf-8", errors="ignore")
    except (urllib.error.URLError, TimeoutError, ConnectionError):
        return None


def http_get_json(url: str, headers: dict[str, str] | None = None, timeout: int = 30) -> Any:
    """GET + parse JSON. Returns parsed dict/list, or None on failure."""
    text = http_get(url, headers=headers, timeout=timeout)
    if text is None:
        return None
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None


def http_get_bytes(url: str, headers: dict[str, str] | None = None, timeout: int = 30) -> bytes | None:
    """Robust GET that returns raw bytes (for xls/binary downloads)."""
    client = _get_aegis_client()
    if client:
        try:
            resp = client.request("GET", url, headers=headers, timeout=timeout)
            if resp is None:
                return None
            content = getattr(resp, "content", None)
            if isinstance(content, bytes):
                return content
        except Exception:
            pass

    h = {"User-Agent": "VDF/4.0 (Veritas Data Forge)"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except (urllib.error.URLError, TimeoutError, ConnectionError):
        return None


# ============================================================
# Parallel execution (wraps Celeritas parallel_map when available)
# ============================================================

def parallel_map(
    fn: Callable[[Any], Any],
    items: Iterable[Any],
    max_workers: int | None = None,
) -> list[Any]:
    """Run fn(item) in parallel for each item. Uses Celeritas if available,
    falls back to ThreadPoolExecutor.

    Returns results in input order. Exceptions caught and returned as None.
    """
    items_list = list(items)
    if not items_list:
        return []

    # Determine worker count
    if max_workers is None:
        if _celeritas:
            try:
                tb = getattr(_celeritas, "thread_budget", None)
                if callable(tb):
                    max_workers = int(tb())
            except Exception:
                pass
        max_workers = max_workers or min(8, len(items_list))

    # Use Celeritas parallel_map if exposed
    if _celeritas:
        try:
            cm = getattr(_celeritas, "parallel_map", None)
            if callable(cm):
                return list(cm(fn, items_list, max_workers=max_workers))
        except Exception:
            pass

    # Fallback: ThreadPoolExecutor with order preservation
    results: list[Any] = [None] * len(items_list)
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        future_to_idx = {ex.submit(fn, item): i for i, item in enumerate(items_list)}
        for fut in as_completed(future_to_idx):
            idx = future_to_idx[fut]
            try:
                results[idx] = fut.result()
            except Exception:
                results[idx] = None
    return results


# ============================================================
# Cache layer (wraps Celeritas cache_get/set when available)
# ============================================================

_local_cache: dict[str, tuple[float, Any]] = {}
_local_cache_lock = threading.Lock()


def cache_get(key: str) -> Any:
    """Get cached value. Returns None on miss or expiry."""
    if _celeritas:
        try:
            cg = getattr(_celeritas, "cache_get", None)
            if callable(cg):
                return cg(key)
        except Exception:
            pass

    with _local_cache_lock:
        entry = _local_cache.get(key)
        if entry is None:
            return None
        expiry, value = entry
        if expiry > 0 and time.time() > expiry:
            del _local_cache[key]
            return None
        return value


def cache_set(key: str, value: Any, ttl_sec: int = 3600) -> bool:
    """Set cached value with TTL. Returns True on success."""
    if _celeritas:
        try:
            cs = getattr(_celeritas, "cache_set", None)
            if callable(cs):
                cs(key, value, ttl_sec)
                return True
        except Exception:
            pass

    with _local_cache_lock:
        expiry = time.time() + ttl_sec if ttl_sec > 0 else 0
        _local_cache[key] = (expiry, value)
    return True


# ============================================================
# Resource pressure detection (from Celeritas)
# ============================================================

def system_under_pressure() -> bool:
    """Check if memory/cpu is high. Returns False if Celeritas unavailable."""
    if _celeritas:
        try:
            fn = getattr(_celeritas, "system_under_pressure", None)
            if callable(fn):
                return bool(fn())
        except Exception:
            pass
    return False


def wait_for_resources(timeout_sec: float = 10.0) -> None:
    """Block until memory/CPU pressure subsides (or timeout)."""
    if not system_under_pressure():
        return
    if _celeritas:
        try:
            wm = getattr(_celeritas, "wait_for_memory", None)
            wc = getattr(_celeritas, "wait_for_cpu", None)
            if callable(wm):
                wm(target=80, timeout=timeout_sec)
            if callable(wc):
                wc(target=70, timeout=timeout_sec)
            return
        except Exception:
            pass
    time.sleep(min(timeout_sec, 2.0))


# ============================================================
# Environment health (from EnvManager)
# ============================================================

def env_health() -> dict[str, Any]:
    """Return current Python env health snapshot.

    Wraps VIA_EnvManager.env_health() when available; returns minimal
    fallback report otherwise.
    """
    if _envmanager:
        try:
            fn = getattr(_envmanager, "env_health", None)
            if callable(fn):
                result = fn()
                if isinstance(result, dict):
                    return result
        except Exception as e:
            return {"available": False, "error": f"{type(e).__name__}: {e}"}

    # Fallback: minimal report from stdlib
    return {
        "available":      False,
        "python_version": sys.version.split()[0],
        "executable":     sys.executable,
        "platform":       sys.platform,
    }


def detect_python() -> dict[str, Any]:
    """Return Python interpreter detection info (delegated to EnvManager)."""
    if _envmanager:
        try:
            fn = getattr(_envmanager, "detect_python", None)
            if callable(fn):
                r = fn()
                if isinstance(r, dict):
                    return r
        except Exception:
            pass
    return {
        "version":    sys.version.split()[0],
        "executable": sys.executable,
        "platform":   sys.platform,
    }


def via_supportive_health() -> dict[str, Any]:
    """Comprehensive health check (delegated to EnvManager when available)."""
    if _envmanager:
        try:
            fn = getattr(_envmanager, "via_supportive_health", None)
            if callable(fn):
                r = fn()
                if isinstance(r, dict):
                    return r
        except Exception:
            pass
    # Fallback: synthesize from is_alive()
    return is_alive()


# ============================================================
# Status & capability report
# ============================================================

def is_alive() -> dict[str, Any]:
    """Returns a capability report — which supportive modules loaded, what features."""
    report: dict[str, Any] = {
        "build_date":  _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "added_paths": _added,
        "aegis": {
            "loaded":              _aegis is not None,
            "error":               _aegis_err,
            "ResilientHTTPClient": _aegis is not None and hasattr(_aegis, "ResilientHTTPClient"),
            "yFinanceShield":      _aegis is not None and hasattr(_aegis, "yFinanceShield"),
            "TaiwanDataSources":   _aegis is not None and hasattr(_aegis, "TaiwanDataSources"),
            "CircuitBreaker":      _aegis is not None and hasattr(_aegis, "CircuitBreaker"),
            "QuotaSaverCache":     _aegis is not None and hasattr(_aegis, "QuotaSaverCache"),
        },
        "celeritas": {
            "loaded":               _celeritas is not None,
            "error":                _celeritas_err,
            "thread_budget":        _celeritas is not None and hasattr(_celeritas, "thread_budget"),
            "parallel_map":         _celeritas is not None and hasattr(_celeritas, "parallel_map"),
            "cache_get":            _celeritas is not None and hasattr(_celeritas, "cache_get"),
            "memory_pressure":      _celeritas is not None and hasattr(_celeritas, "system_under_pressure"),
        },
        "envmanager": {
            "loaded":               _envmanager is not None,
            "error":                _envmanager_err,
            "env_health":           _envmanager is not None and hasattr(_envmanager, "env_health"),
            "detect_python":        _envmanager is not None and hasattr(_envmanager, "detect_python"),
            "pip_check":            _envmanager is not None and hasattr(_envmanager, "pip_check"),
            "build_envmanager_state": _envmanager is not None and hasattr(_envmanager, "def_build_envmanager_state"),
        },
    }

    if _celeritas:
        try:
            tb_fn = getattr(_celeritas, "thread_budget", None)
            if callable(tb_fn):
                report["celeritas"]["recommended_threads"] = int(tb_fn())
        except Exception:
            pass

    return report


if __name__ == "__main__":
    print("=" * 60)
    print(" VDF Supportive Bridge — Capability Report")
    print("=" * 60)
    r = is_alive()
    print(json.dumps(r, indent=2, ensure_ascii=False))

    # Quick smoke
    print()
    print("=" * 60)
    print(" Smoke Tests")
    print("=" * 60)

    # Cache
    cache_set("test", "hello", ttl_sec=60)
    print(f"  cache: {cache_get('test')}")

    # Parallel map
    def slow_double(x):
        time.sleep(0.05)
        return x * 2

    t0 = time.time()
    results = parallel_map(slow_double, list(range(10)))
    print(f"  parallel_map: {results} (took {time.time()-t0:.2f}s)")
