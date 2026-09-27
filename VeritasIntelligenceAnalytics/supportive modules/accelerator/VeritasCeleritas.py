#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Canonical seat. The body stays VeritasCeleritas_v1141.py. This file does not copy it."""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

BODY = Path(__file__).resolve().parent.parent / "VeritasCeleritas_v1141.py"


def main() -> int:
    if not BODY.is_file():
        print("ABSENT " + BODY.name)
        return 2
    sys.argv[0] = str(BODY)
    runpy.run_path(str(BODY), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
