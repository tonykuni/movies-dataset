#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF manager tail. Read a command register through its dot-source chain.

v0257 only adds one command and loads v0256. The gate must see that chain.
Direct start stays refused. v0104 and v0106 are not rewritten.
"""
from __future__ import annotations

import importlib.util
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR = HERE / "VDF_SystemManager_v0106.py"
_body = None


def _follow(path: Path, seen: set) -> str:
    if path in seen or not path.is_file():
        return ""
    seen.add(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    parts = [text]
    for name in re.findall(r"Register-VIA-Commands-v\d+\.ps1", text):
        parts.append(_follow(path.parent / name, seen))
    return "\n".join(parts)


def _load():
    global _body
    if _body is None:
        spec = importlib.util.spec_from_file_location("vdf_manager_v0106_for_v0107", PRIOR)
        prior = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(prior)
        body = prior._load()
        plain = body._src
        original = body.scrape_gate_split

        def _src(p):
            text = plain(p)
            path = Path(str(p)) if p else None
            if path is not None and path.name.startswith("Register-VIA-Commands-"):
                return _follow(path, set())
            return text

        def scrape_gate_split(environ=None):
            body._src = _src
            try:
                return original(environ)
            finally:
                body._src = plain

        body.scrape_gate_split = scrape_gate_split
        _body = body
    return _body


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VDF] 拒絕。只能經 via-vcgc。")
        return 2
    return _load().main()


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    ok = main() == 2
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
