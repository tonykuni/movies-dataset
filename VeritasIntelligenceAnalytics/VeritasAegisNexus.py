#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Canonical seat. The network tool is the one the lock book names; this file does not copy it.

Operator 2026-10-03:「鎖定這兩個 其他刪除 避免一直錯」「改掉」. Up to today this seat held an old 5,186-line body
(no ENGINE_VERSION; sha256 f5f81f04479d…), so every `import VeritasAegisNexus` / `_via_load("VeritasAegisNexus")`
ran a different network core than the lock book (VIA_ToolVersion_Lock 'network' = VeritasAegisNexus_v1652 on the
1.65.1 body). All 158 public names of the old body exist in the locked one. Same pattern as
supportive modules/accelerator/VeritasCeleritas.py (accelerator seat → VeritasCeleritas_v1141).
Only VCGC `tools activate network … --apply` moves the lock; no lock or its file gone = ImportError (honest).
"""
from __future__ import annotations

import importlib.util as _ilu
import json as _json
import sys as _sys
from pathlib import Path as _Path


def _locked_network_path() -> _Path:
    p = _Path(__file__).resolve().parent
    while p.parent != p:
        locks = sorted((p / "supportive modules" / "registry").glob("VIA_ToolVersion_Lock_v*.json"))
        if locks:
            rel = (_json.loads(locks[-1].read_text(encoding="utf-8")).get("network") or {}).get("path")
            if not rel:
                raise ImportError("VeritasAegisNexus seat: lock book has no 'network' entry")
            hit = p.parent / rel
            if not hit.is_file():
                raise ImportError(f"VeritasAegisNexus seat: locked file missing: {rel}")
            return hit
        p = p.parent
    raise ImportError("VeritasAegisNexus seat: VIA_ToolVersion_Lock_v*.json not found")


LOCKED_PATH = _locked_network_path()
_spec = _ilu.spec_from_file_location("VeritasAegisNexus_locked", LOCKED_PATH)
_locked = _ilu.module_from_spec(_spec)
_sys.modules[_spec.name] = _locked
_spec.loader.exec_module(_locked)
globals().update({_k: _v for _k, _v in vars(_locked).items() if not _k.startswith("__")})

if __name__ == "__main__":
    import runpy
    _sys.argv[0] = str(LOCKED_PATH)
    runpy.run_path(str(LOCKED_PATH), run_name="__main__")
