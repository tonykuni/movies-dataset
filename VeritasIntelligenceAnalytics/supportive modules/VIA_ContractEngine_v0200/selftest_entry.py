#!/usr/bin/env python3
# 契約介面引擎自測入口(自測矩陣站用):pytest 缺=rc3 誠實(env 類→SKIP)
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
try:
    import pytest  # noqa: F401
    import pydantic  # noqa: F401
except ImportError as exc:
    print(f"[SKIP] 依賴缺({exc.name})——via-install pytest pydantic 後重跑")
    sys.exit(3)
env = dict(os.environ, PYTHONPATH=str(HERE / "src"))
r = subprocess.run([sys.executable, "-m", "pytest", str(HERE / "tests"), "-q"],
                   env=env, stdin=subprocess.DEVNULL)
sys.exit(r.returncode)
