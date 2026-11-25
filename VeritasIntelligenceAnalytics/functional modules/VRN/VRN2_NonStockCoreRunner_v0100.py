#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN2_NonStockCoreRunner v0100 — 非個股核心 v0400 的加速器入口(VRN-2;操作員原件一位元都不動)

PR #722 Codex P1:nonstock_core_v0400/NON_STOCK_CORE_v0400.py 用 lru_cache 與一行註解代替既有的加速器橋,
  直接跑 --health / --selftest / --legacy-core 時不載入共用加速器;test_nonstock_v0400.py 也沒有橋。
為什麼不直接在原件裡插橋:兩支都是操作員上傳的原件(逐位元入倉),RELEASE_MANIFEST.json 記了 SHA,
  核心自己的測試(test_nonstock_v0400 逐檔比 manifest)與 VRN2_NonStockSummarizer v0101 的 CORE_SHA 都會因此變紅。
本檔:帶標準 [VIA:ACCEL-BRIDGE:v0100](先載入共用加速器),再把參數原樣交給核心的 def_main(同一個行程)。
  python VRN2_NonStockCoreRunner_v0100.py --health | --doctor | --selftest | --legacy-core <檔> | <檔或夾…> [核心其他旗標]
  python VRN2_NonStockCoreRunner_v0100.py --core-tests        # 在帶橋的行程裡跑操作員的 test_nonstock_v0400(41 條)
  python VRN2_NonStockCoreRunner_v0100.py --runner-selftest   # 本檔自測(零網路 · 不寫倉)
不改核心、不改測試、不改 manifest;不 import VCGC / VDF;零 TA-Lib;零網路。
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
import hashlib
import importlib.util
import json
import re
import sys
import unittest
from pathlib import Path

ENGINE = "VRN2_NonStockCoreRunner v0100"
HERE = Path(__file__).resolve().parent
CORE_DIR = HERE / "nonstock_core_v0400"
CORE_FILE = CORE_DIR / "NON_STOCK_CORE_v0400.py"
TEST_FILE = CORE_DIR / "test_nonstock_v0400.py"
MANIFEST = CORE_DIR / "RELEASE_MANIFEST.json"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pinned(name: str) -> str | None:
    """操作員 RELEASE_MANIFEST 記的 SHA(核心與測試都在冊上)。"""
    try:
        return json.loads(MANIFEST.read_text(encoding="utf-8"))["files"][name]["sha256"]
    except (OSError, ValueError, KeyError):
        return None


def load_core():
    """以一般模組載入核心(不是 __main__),同一行程、加速器已先載入。"""
    spec = importlib.util.spec_from_file_location("nonstock_core_v0400_via_runner", CORE_FILE)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def run_core(argv: list) -> int:
    return int(load_core().def_main(list(argv)))


def core_tests(verbosity: int = 1) -> int:
    sys.path.insert(0, str(CORE_DIR))
    try:
        suite = unittest.defaultTestLoader.loadTestsFromName(TEST_FILE.stem)
        result = unittest.TextTestRunner(verbosity=verbosity, stream=sys.stderr).run(suite)
    finally:
        sys.path.remove(str(CORE_DIR))
    return 0 if result.wasSuccessful() else 1


def selftest() -> int:
    import contextlib
    import io
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("=== %s 自測(零網路 · 不寫倉;核心與測試是操作員原件,不改)===" % ENGINE, flush=True)
    chk("① 加速器橋在本檔,而且這個行程真的載入了共用加速器(樹上)", "[VIA:ACCEL-BRIDGE:v0100]" in Path(__file__).read_text(encoding="utf-8")
        and VIA_ACCEL is not None and "VIA_SuperAccel_Module" in sys.modules, VIA_ACCEL)
    core_pin, test_pin = pinned(CORE_FILE.name), pinned(TEST_FILE.name)
    chk("② 核心與測試 = 操作員 manifest 的 SHA(原件一位元都沒動)", core_pin and _sha(CORE_FILE) == core_pin and test_pin and _sha(TEST_FILE) == test_pin,
        (core_pin and core_pin[:12], test_pin and test_pin[:12]))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc_h = run_core(["--health"])
    try:
        health = json.loads(buf.getvalue())
    except ValueError:
        health = {}
    chk("③ --health 經本入口交給核心 def_main(同一行程 · 加速器已載入)· rc 0 · 回核心自己的 JSON", rc_h == 0 and bool(health)
        and "VIA_SuperAccel_Module" in sys.modules, (rc_h, buf.getvalue()[-200:]))
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        rc_t = core_tests(verbosity=0)
    chk("④ 操作員的 test_nonstock_v0400 在帶橋的行程裡照過", rc_t == 0, err.getvalue()[-300:])
    body = Path(__file__).read_text(encoding="utf-8").split("def selftest", 1)[0]
    chk("⑤ 零網路 · 零 TA-Lib · 不 import VCGC / VDF · 不寫檔",
        not re.search(r"^\s*(?:import|from)\s+(talib|requests|urllib|socket|http|CGC_|VDF_)", body, re.M)
        and ".write_text(" not in body and ".write_bytes(" not in body)
    n = sum(ok)
    print("[%s] %s selftest · %d/%d" % ("PASS" if n == len(ok) else "FAIL", ENGINE, n, len(ok)), flush=True)
    return 0 if n == len(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["--runner-selftest"]:
        return selftest()
    if a[:1] == ["--core-tests"]:
        return core_tests()
    return run_core(a)


if __name__ == "__main__":
    sys.exit(main())
