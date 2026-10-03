#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SUP_MDL737_SuperAccelModule_v0110 — tail: `import VeritasAegisNexus` / `import VeritasCeleritas` land on the lock book's tools.

Operator 2026-10-03: 「鎖定這兩個 其他刪除 避免一直錯」「改掉」. 244 live files import the network tool by its bare
name (`import VeritasAegisNexus`, `_via_load("VeritasAegisNexus")` → `__import__`). The first hit on sys.path is a
frozen 5,186-line body (supportive modules/VeritasAegisNexus.py · freeze seal + no_delete), not the lock book's
v1652. Rewriting the frozen files in place broke AGENTS.md L4 (修改開新版;已鎖成功來源維持原樣) and the v0116 tail,
which loads network/VeritasAegisNexus.py by path (PR #442 review). So the frozen files stay byte-for-byte and the
redirect lives here, in a new tail of the module every VIA process already loads first (the [VIA:ACCEL-BRIDGE] block
imports VIA_SuperAccel_Module → newest SUP_MDL737 tail):
  a sys.meta_path finder answers the two bare names from VIA_ToolVersion_Lock ('network' / 'accelerator' path).
  Only the bare import name is redirected; anything loaded by an explicit path (v0116, v1652's own body load,
  spec_from_file_location callers) is untouched. No lock, or the file it names is gone → the finder steps aside
  (normal import, honest). Only VCGC `tools activate … --apply` moves the lock. Nothing is fetched or installed.
"""
from __future__ import annotations

import importlib.abc
import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "SUP_MDL737_SuperAccelModule"
LOCKED_NAMES = {"VeritasAegisNexus": "network", "VeritasCeleritas": "accelerator"}


def _vnum(path: Path) -> int:
    match = re.search(r"_v(\d+)$", path.stem)
    return int(match.group(1)) if match else -1


def _prior() -> Path:
    mine = _vnum(Path(__file__))
    older = [p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < mine]
    if not older:
        raise ImportError(f"{STEM}: no version below v{mine:04d}")
    return max(older, key=_vnum)


PRIOR = _prior()
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_v{_vnum(Path(__file__)):04d}", PRIOR)
_PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _PRIOR
_spec.loader.exec_module(_PRIOR)


def locked_path(family: str) -> Path | None:
    """The lock book's file for a tool family; None = no lock / file gone (the finder then steps aside)."""
    p = HERE
    while p.parent != p:
        books = sorted((p / "registry").glob("VIA_ToolVersion_Lock_v*.json")) if p.name == "supportive modules" else []
        if books:
            try:
                rel = (json.loads(books[-1].read_text(encoding="utf-8")).get(family) or {}).get("path")
            except (OSError, ValueError):
                return None
            hit = p.parent.parent / rel if rel else None
            return hit if hit is not None and hit.is_file() else None
        p = p.parent
    return None


class LockedToolFinder(importlib.abc.MetaPathFinder):
    """Answers only the bare names in LOCKED_NAMES with the lock book's file."""
    tag = "VIA_LOCKED_TOOL_FINDER_v0110"

    def find_spec(self, fullname, path=None, target=None):
        fam = LOCKED_NAMES.get(fullname)
        if fam is None:
            return None
        hit = locked_path(fam)
        return importlib.util.spec_from_file_location(fullname, hit) if hit is not None else None


def install_finder() -> bool:
    """Idempotent: one finder, first in sys.meta_path."""
    if any(getattr(f, "tag", "") == LockedToolFinder.tag for f in sys.meta_path):
        return False
    sys.meta_path.insert(0, LockedToolFinder())
    return True


install_finder()

for _name, _value in vars(_PRIOR).items():
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = _value


def __getattr__(name: str):
    """Every public name of the prior version stays reachable here."""
    return getattr(_PRIOR, name)


def selftest() -> int:
    rc = _PRIOR.selftest()
    import subprocess
    sup = HERE
    probe = ("import sys; sys.path.insert(0, {s!r}); import VIA_SuperAccel_Module as A; import VeritasAegisNexus as N; "
             "import VeritasCeleritas as C; print(N.__file__); print(getattr(N, 'ENGINE_VERSION', '')); print(C.__file__)").format(s=str(sup))
    out = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True, timeout=300)
    lines = out.stdout.strip().splitlines()
    net, acc = locked_path("network"), locked_path("accelerator")
    frozen = sup / "VeritasAegisNexus.py"
    own = Path(__file__).read_text(encoding="utf-8")
    checks = [
        ("bare `import VeritasAegisNexus` (frozen copy first on sys.path) lands on the lock book's network tool",
         out.returncode == 0 and len(lines) >= 3 and net is not None and Path(lines[0]).name == net.name),
        ("network tool version is the locked one (1.65.2 on the 1.65.1 body)", len(lines) >= 2 and lines[1] == "1.65.2"),
        ("bare `import VeritasCeleritas` lands on the lock book's accelerator", len(lines) >= 3 and acc is not None and Path(lines[2]).name == acc.name),
        ("frozen copy is still the original body on disk (not a seat; only the bare-name import is redirected)",
         frozen.is_file() and "Canonical seat" not in frozen.read_text(encoding="utf-8", errors="ignore")[:4000]
         and frozen.stat().st_size > 100_000),
        ("finder installed once (idempotent)", not install_finder() and sum(getattr(f, "tag", "") == LockedToolFinder.tag for f in sys.meta_path) == 1),
        ("no tool file name is written into this tail", re.search(r"(VeritasAegisNexus|VeritasCeleritas)_v\d{4}\.py", own) is None),
        ("no TA-Lib import", re.search(r"^\s*(import|from)\s+talib", own, re.M) is None),
    ]
    for name, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print(f"  [註] v{_vnum(Path(__file__)):04d} 鎖版導向 network → {net.name if net else 'ABSENT'} · accelerator → {acc.name if acc else 'ABSENT'}"
          + ("" if out.returncode == 0 else f" · 探針 rc {out.returncode}: {out.stderr.strip()[-200:]}"))
    ok = rc == 0 and all(c for _n, c in checks)
    print(f"  [計] {STEM}_v{_vnum(Path(__file__)):04d} {sum(c for _n, c in checks)}/{len(checks)} {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    _a = sys.argv[1:]
    if "--modules" in _a:
        sys.exit(_PRIOR.cmd_modules())
    if "--activate" in _a:
        sys.exit(_PRIOR.cmd_activate())
    if "--libs" in _a:
        sys.exit(_PRIOR.cmd_libs())
    sys.exit(selftest())
