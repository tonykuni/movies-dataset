#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:MODULE_SPEC:START]
# MODULE_NAME:       vdf_bridge
# MODULE_VERSION:    1.0.0
# MODULE_ROLE:       Bridge layer that ACTUALLY USES the 7 supportive modules.
#                    Provides graceful fallback when modules are absent (sandbox),
#                    but ACTIVATES them on Tony's machine where they exist.
# MODULE_ZONE:       D5
# DEPENDENCIES:      stdlib
# OPTIONAL_DEPENDENCIES:
#   - VIA_Runtime_Bridge_All_in_One (orchestrator that bootstraps the rest)
#   - VeritasCeleritas              (HTTP cache/retry/dedup + thread budget + accel)
#   - VeritasAegisNexus             (resilient HTTP client w/ UA rotation, CB)
#   - VIA_RegistryCore_v1           (module registry / ID / version tracking)
#   - VIA_SSOT_Unified              (single source of truth / pattern matching)
#   - VIA_EnvManager                (env health / pip planning)
#   - VIA_Panorama_AST_RuntimeInjector (AST analysis / runtime injection)
# ERROR_POLICY:      RETURN_SAFE_DEFAULT
# SAFE_SKIP:         True
# MERGE_UNIT_ID:     VDF-D5-BRIDGE-001
# [VIA:MODULE_SPEC:END]
"""
Bridge layer for VDF <-> Supportive Modules.

The 7 supportive modules each provide capabilities VDF can use:

| Supportive module                | Capability VDF uses               |
|----------------------------------|-----------------------------------|
| VIA_Runtime_Bridge_All_in_One    | Bootstraps all others as one ctx  |
| VeritasCeleritas                 | vdf_fetch_json (cached HTTP)      |
|                                  | accelerated_concat / drop_dup     |
|                                  | thread_budget (parallelism)       |
| VeritasAegisNexus                | ResilientHTTPClient.get_json      |
|                                  | fetch_twse_list / fetch_tpex_list |
| VIA_RegistryCore_v1              | Record VDF module versions        |
| VIA_SSOT_Unified                 | Pattern matching for parsing      |
| VIA_EnvManager                   | Detect missing deps               |
| VIA_Panorama_AST_RuntimeInjector | Module health probing             |

When absent (sandbox), every call falls back to stdlib equivalents.
The user-visible behaviour is identical; on Tony's machine you get caching,
retries, accelerated dataframes, UA rotation, etc.
"""

# [VIA:ANCHOR:D5_BRIDGE:START]

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

log = logging.getLogger("VDF.bridge")


# =========================================================================
# Bridge context (singleton)
# =========================================================================

class BridgeContext:
    """Single object holding handles to all loaded supportive modules."""
    def __init__(self):
        # raw module handles
        self.celeritas: Any = None
        self.aegis: Any = None
        self.registry: Any = None
        self.ssot: Any = None
        self.env: Any = None
        self.ast_injector: Any = None
        self.runtime_bridge: Any = None
        # via_runtime_context returned by runtime_bridge.def_bootstrap_runtime()
        self.runtime_ctx: Any = None
        # capability flags
        self.has_cached_fetch = False
        self.has_resilient_http = False
        self.has_accelerated_df = False
        self.has_thread_budget = False
        self.has_registry = False
        self.has_ssot = False
        self.has_env = False

    def summary(self) -> Dict[str, Any]:
        return {
            "celeritas": self.celeritas is not None,
            "aegis": self.aegis is not None,
            "registry": self.registry is not None,
            "ssot": self.ssot is not None,
            "env": self.env is not None,
            "ast_injector": self.ast_injector is not None,
            "runtime_bridge": self.runtime_bridge is not None,
            "capabilities": {
                "cached_fetch": self.has_cached_fetch,
                "resilient_http": self.has_resilient_http,
                "accelerated_df": self.has_accelerated_df,
                "thread_budget": self.has_thread_budget,
                "registry": self.has_registry,
                "ssot": self.has_ssot,
                "env": self.has_env,
            },
        }


_CTX: Optional[BridgeContext] = None


def get_bridge() -> BridgeContext:
    """Lazily build the bridge context. Safe to call repeatedly."""
    global _CTX
    if _CTX is not None:
        return _CTX
    _CTX = BridgeContext()
    _try_bootstrap(_CTX)
    return _CTX


# =========================================================================
# Bootstrap: try the orchestrator first, then individual modules
# =========================================================================

def _try_bootstrap(ctx: BridgeContext) -> None:
    """Attempt to load supportive modules. Each step independently graceful."""

    # 1. Try the runtime bridge orchestrator first - it wires up everything
    try:
        import VIA_Runtime_Bridge_All_in_One as rb  # type: ignore
        ctx.runtime_bridge = rb
        if hasattr(rb, "def_bootstrap_runtime"):
            try:
                via_ctx = rb.def_bootstrap_runtime()
                ctx.runtime_ctx = via_ctx
                log.info("[bridge] runtime_bridge bootstrapped via def_bootstrap_runtime()")
                # The ctx returned has attrs like .celeritas, .aegis, .registry, .ssot, .env
                if hasattr(via_ctx, "celeritas") and via_ctx.celeritas is not None:
                    ctx.celeritas = via_ctx.celeritas
                if hasattr(via_ctx, "aegis") and via_ctx.aegis is not None:
                    ctx.aegis = via_ctx.aegis
                if hasattr(via_ctx, "registry") and via_ctx.registry is not None:
                    ctx.registry = via_ctx.registry
                if hasattr(via_ctx, "ssot") and via_ctx.ssot is not None:
                    ctx.ssot = via_ctx.ssot
                if hasattr(via_ctx, "env") and via_ctx.env is not None:
                    ctx.env = via_ctx.env
            except Exception as e:
                log.warning("[bridge] runtime_bridge.bootstrap failed: %s", e)
    except ImportError as e:
        log.info("[bridge] runtime_bridge absent: %s", e)

    # 2. If orchestrator didn't load Celeritas, try direct
    if ctx.celeritas is None:
        try:
            import VeritasCeleritas as vc  # type: ignore
            ctx.celeritas = vc
            log.info("[bridge] VeritasCeleritas loaded directly")
        except ImportError as e:
            log.info("[bridge] VeritasCeleritas absent: %s", e)

    # 3. If orchestrator didn't load Aegis, try direct
    if ctx.aegis is None:
        try:
            import VeritasAegisNexus as van  # type: ignore
            ctx.aegis = van
            log.info("[bridge] VeritasAegisNexus loaded directly")
        except ImportError as e:
            log.info("[bridge] VeritasAegisNexus absent: %s", e)

    # 4. Registry
    if ctx.registry is None:
        try:
            import VIA_RegistryCore_v1 as rc  # type: ignore
            ctx.registry = rc
            log.info("[bridge] VIA_RegistryCore loaded directly")
        except ImportError as e:
            log.info("[bridge] VIA_RegistryCore absent: %s", e)

    # 5. SSOT
    if ctx.ssot is None:
        try:
            import VIA_SSOT_Unified as ssot_mod  # type: ignore
            ctx.ssot = ssot_mod
            log.info("[bridge] VIA_SSOT_Unified loaded directly")
        except ImportError as e:
            log.info("[bridge] VIA_SSOT_Unified absent: %s", e)

    # 6. EnvManager
    if ctx.env is None:
        try:
            import VIA_EnvManager as envmgr  # type: ignore
            ctx.env = envmgr
            log.info("[bridge] VIA_EnvManager loaded directly")
        except ImportError as e:
            log.info("[bridge] VIA_EnvManager absent: %s", e)

    # 7. AST injector
    try:
        import VIA_Panorama_AST_RuntimeInjector as ast_inj  # type: ignore
        ctx.ast_injector = ast_inj
        log.info("[bridge] VIA_Panorama_AST_RuntimeInjector loaded")
    except ImportError as e:
        log.info("[bridge] VIA_Panorama_AST absent: %s", e)

    # ---- Set capability flags based on what loaded ----

    if ctx.celeritas is not None:
        if hasattr(ctx.celeritas, "vdf_fetch_json"):
            ctx.has_cached_fetch = True
        if hasattr(ctx.celeritas, "accelerated_concat") and hasattr(ctx.celeritas, "accelerated_drop_duplicates"):
            ctx.has_accelerated_df = True
        if hasattr(ctx.celeritas, "thread_budget"):
            ctx.has_thread_budget = True

    if ctx.aegis is not None:
        if hasattr(ctx.aegis, "ResilientHTTPClient"):
            ctx.has_resilient_http = True

    if ctx.registry is not None:
        ctx.has_registry = True
    if ctx.ssot is not None:
        ctx.has_ssot = True
    if ctx.env is not None:
        ctx.has_env = True

    log.info("[bridge] capabilities: %s", ctx.summary()["capabilities"])


# =========================================================================
# CAPABILITY: HTTP GET JSON (used by all TWSE/TPEX fetchers)
# =========================================================================

class _StdlibHttp:
    """Stdlib fallback when no supportive HTTP client is available."""
    def __init__(self):
        try:
            import requests
            self.session = requests.Session()
            self.session.headers.update({
                "User-Agent": "Mozilla/5.0 (VDF/2.0)",
                "Accept": "application/json,text/html,*/*",
            })
            self._kind = "requests"
        except ImportError:
            self.session = None
            self._kind = "urllib"

    def get_json(self, url: str, params: Optional[dict] = None, timeout: int = 30):
        if self._kind == "requests":
            try:
                r = self.session.get(url, params=params, timeout=timeout)
                if r.status_code != 200:
                    return None
                try:
                    return r.json()
                except Exception:
                    return None
            except Exception as e:
                log.debug("[bridge.http] requests GET %s failed: %s", url, e)
                return None
        # urllib fallback
        try:
            import json as _json
            from urllib import request as _ur, parse as _up
            qs = ""
            if params:
                qs = "?" + _up.urlencode(params)
            req = _ur.Request(url + qs, headers={"User-Agent": "VDF/2.0"})
            with _ur.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                try:
                    return _json.loads(body)
                except Exception:
                    return None
        except Exception as e:
            log.debug("[bridge.http] urllib GET %s failed: %s", url, e)
            return None


def http_get_json(url: str, params: Optional[dict] = None, timeout: int = 30) -> Any:
    """
    Drop-in HTTP-GET-JSON. Tries (in priority order):
      1. VeritasCeleritas.vdf_fetch_json   (cached + retried + deduped)
      2. VeritasAegisNexus.ResilientHTTPClient  (UA rotation + circuit breaker)
      3. requests.Session                  (stdlib fallback)
      4. urllib.request                    (final fallback)

    Returns parsed JSON dict/list, or None on failure.
    """
    ctx = get_bridge()

    # 1. VeritasCeleritas accelerated fetch
    if ctx.has_cached_fetch:
        try:
            # vdf_fetch_json signature can be (url, params=, timeout=)
            result = ctx.celeritas.vdf_fetch_json(url, params=params, timeout=timeout)
            if result is not None:
                return result
        except TypeError:
            # different signature - try positional
            try:
                result = ctx.celeritas.vdf_fetch_json(url)
                if result is not None:
                    return result
            except Exception as e:
                log.debug("[bridge.http] celeritas.vdf_fetch_json fallback positional failed: %s", e)
        except Exception as e:
            log.debug("[bridge.http] celeritas.vdf_fetch_json failed: %s", e)

    # 2. VeritasAegisNexus ResilientHTTPClient
    if ctx.has_resilient_http:
        try:
            client = _get_aegis_http_client(ctx)
            if client is not None:
                full_url = url
                if params:
                    from urllib.parse import urlencode
                    sep = "&" if "?" in url else "?"
                    full_url = url + sep + urlencode(params)
                result = client.get_json(full_url, timeout=timeout)
                if result is not None:
                    return result
        except Exception as e:
            log.debug("[bridge.http] aegis.get_json failed: %s", e)

    # 3 + 4. Stdlib fallback
    return _get_stdlib_http().get_json(url, params=params, timeout=timeout)


_AEGIS_CLIENT_CACHE: Any = None
def _get_aegis_http_client(ctx: BridgeContext):
    """Singleton ResilientHTTPClient instance."""
    global _AEGIS_CLIENT_CACHE
    if _AEGIS_CLIENT_CACHE is not None:
        return _AEGIS_CLIENT_CACHE
    try:
        cls = ctx.aegis.ResilientHTTPClient
        # Try default constructor first
        try:
            _AEGIS_CLIENT_CACHE = cls()
        except TypeError:
            # might need an HttpConfig
            try:
                cfg = ctx.aegis.HttpConfig()
                _AEGIS_CLIENT_CACHE = cls(cfg)
            except Exception as e:
                log.debug("[bridge.http] aegis client config init failed: %s", e)
                return None
        return _AEGIS_CLIENT_CACHE
    except Exception as e:
        log.debug("[bridge.http] aegis client init failed: %s", e)
        return None


_STDLIB_HTTP_CACHE: Optional[_StdlibHttp] = None
def _get_stdlib_http() -> _StdlibHttp:
    global _STDLIB_HTTP_CACHE
    if _STDLIB_HTTP_CACHE is None:
        _STDLIB_HTTP_CACHE = _StdlibHttp()
    return _STDLIB_HTTP_CACHE


# =========================================================================
# CAPABILITY: Accelerated DataFrame ops (used by ParquetStore)
# =========================================================================

def accelerated_concat(frames: List[Any], prefer: str = "polars") -> Any:
    """pandas.concat shim - uses Celeritas accelerated_concat when available."""
    ctx = get_bridge()
    if ctx.has_accelerated_df:
        try:
            return ctx.celeritas.accelerated_concat(frames, prefer=prefer)
        except Exception as e:
            log.debug("[bridge.df] accelerated_concat failed: %s, falling back", e)
    import pandas as pd
    return pd.concat(frames, ignore_index=True)


def accelerated_drop_duplicates(frame: Any, subset: Optional[List[str]] = None) -> Any:
    """pandas drop_duplicates shim - uses Celeritas accelerated_drop_duplicates."""
    ctx = get_bridge()
    if ctx.has_accelerated_df:
        try:
            return ctx.celeritas.accelerated_drop_duplicates(frame, subset=subset)
        except Exception as e:
            log.debug("[bridge.df] accelerated_drop_duplicates failed: %s", e)
    return frame.drop_duplicates(subset=subset, keep="last")


# =========================================================================
# CAPABILITY: Thread budget (used by TW chip parallel fetcher if added)
# =========================================================================

def thread_budget(mode: str = "balanced") -> int:
    """Returns a safe parallel thread count, considering CPU + RAM pressure."""
    ctx = get_bridge()
    if ctx.has_thread_budget:
        try:
            return int(ctx.celeritas.thread_budget(mode=mode))
        except Exception:
            pass
    # Fallback: half the logical CPU count, clamped to [1, 8]
    try:
        import os
        n = os.cpu_count() or 4
        return max(1, min(8, n // 2))
    except Exception:
        return 2


# =========================================================================
# CAPABILITY: Registry (record what VDF ran, when, version)
# =========================================================================

def registry_record(module_name: str, version: str, role: str = "PIPELINE_STEP",
                    extra: Optional[Dict[str, Any]] = None) -> bool:
    """Record this module's identity in the VIA registry."""
    ctx = get_bridge()
    if not ctx.has_registry:
        return False
    try:
        # Registry exposes def_ModuleIdentity / def_ModuleRecord / etc.
        if hasattr(ctx.registry, "def_now_utc_iso") and hasattr(ctx.registry, "def_append_jsonl"):
            # Write a JSONL record to whatever output path the registry uses
            ts = ctx.registry.def_now_utc_iso()
            entry = {
                "ts": ts,
                "module": module_name,
                "version": version,
                "role": role,
                "extra": extra or {},
            }
            # Try the registry's preferred output path
            try:
                output_dir = Path.home() / ".via" / "registry"
                output_dir.mkdir(parents=True, exist_ok=True)
                ctx.registry.def_append_jsonl(output_dir / "vdf_modules.jsonl", entry)
                return True
            except Exception:
                return False
    except Exception as e:
        log.debug("[bridge.registry] record failed: %s", e)
    return False


# =========================================================================
# CAPABILITY: SSOT (pattern matching for chip parsers)
# =========================================================================

def ssot_extract(rule: str, text: str) -> Optional[str]:
    """Single source of truth pattern extraction. Returns None if unavailable."""
    ctx = get_bridge()
    if not ctx.has_ssot:
        return None
    try:
        if hasattr(ctx.ssot, "extract"):
            return ctx.ssot.extract(rule, text)
    except Exception as e:
        log.debug("[bridge.ssot] extract failed: %s", e)
    return None


# =========================================================================
# CAPABILITY: Env health check (used at startup)
# =========================================================================

def env_health_check() -> Dict[str, Any]:
    """Returns env capability report. Always succeeds (returns {} if no env mgr)."""
    ctx = get_bridge()
    out: Dict[str, Any] = {"python_version": sys.version, "platform": sys.platform}
    if ctx.has_env and ctx.env:
        try:
            if hasattr(ctx.env, "def_get_hostname"):
                out["hostname"] = ctx.env.def_get_hostname()
        except Exception:
            pass
    # Also probe key Python deps directly
    for mod in ("pandas", "pyarrow", "yfinance", "fredapi", "duckdb", "akshare", "requests"):
        try:
            __import__(mod)
            out[f"has_{mod}"] = True
        except ImportError:
            out[f"has_{mod}"] = False
    return out


# =========================================================================
# Public API
# =========================================================================

__all__ = [
    "BridgeContext",
    "get_bridge",
    "http_get_json",
    "accelerated_concat",
    "accelerated_drop_duplicates",
    "thread_budget",
    "registry_record",
    "ssot_extract",
    "env_health_check",
]

# [VIA:ANCHOR:D5_BRIDGE:END]
