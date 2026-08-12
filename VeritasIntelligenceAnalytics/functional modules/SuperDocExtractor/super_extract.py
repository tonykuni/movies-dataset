#!/usr/bin/env python3
"""Entry point:  python super_extract.py <command> ...

See `python super_extract.py --help` (or the README) for the commands:
doctor / extract / validate / compare / crosscheck / selftest.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from superextract.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
