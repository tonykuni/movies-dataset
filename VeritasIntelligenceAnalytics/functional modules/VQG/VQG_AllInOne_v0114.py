#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VQG_AllInOne v0114 — 薄尾(v0113 一字不動):補標準加速器橋(L103 最高政策 · VIA_ListsFirstDAG 覆蓋實測)

緣由(2026-11-16 · 操作員桌機 VIA_ListsFirstDAG v0101 ① 覆蓋表 + 本倉同一量尺重跑):前版只有一行 [VIA:ACCEL-BRIDGE] 註記,沒有標準橋塊(量尺判缺)。
本版只加橋塊;其餘全部原樣交前版:
  · 以腳本執行(任何參數,含前版自己的動詞)→ runpy 以 __main__ 跑前版,sys.argv 原封不動(行為 = 前版)。
  · 被 import → 公開名稱經 __getattr__ 轉接前版(尾版不少名字 · TAILAPI)。
  · `--selftest` → 先驗本版(橋塊在 · 前版 SHA 沒變),再以乾淨子行程跑前版自測(rc 照前版;只因缺 polars 失敗 = SKIP_ENV · rc 2 黃)。
所屬:VQG 自己的檔(L123:VQG 自己出新版;他系統不代改)。零網路 · 不用 TA-Lib · 不寫同意閘 · 不裝套件。
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
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import hashlib
import importlib.util
import re
import runpy
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "VQG_AllInOne"
VERSION = "v0114"
PRIOR_NAME = "VQG_AllInOne_v0113.py"
PRIOR_PATH = HERE / PRIOR_NAME
PRIOR_SHA256 = "df07c5c9f1e9c958ccca9890e15418ab953e65e1a30f79da88452e89f2444fe4"                       # 前版(LF 正規化後)· 前版一字不動的證據
_PRIOR = None


def _prior():
    """前版模組(用到才載入,腳本執行時不重複跑前版的模組層)。"""
    global _PRIOR
    if _PRIOR is None:
        spec = importlib.util.spec_from_file_location(STEM + "_prior_for_" + VERSION, PRIOR_PATH)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        _PRIOR = mod
    return _PRIOR


def __getattr__(name: str):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(_prior(), name)


def selftest() -> int:
    ok = []

    def chk(label, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", label, (" · " + str(note)[:200]) if note and not cond else ""), flush=True)

    print("=== %s %s · 薄尾自測(補標準加速器橋)===" % (STEM, VERSION), flush=True)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("① 本檔帶標準加速器橋塊(import VIA_SuperAccel_Module)", "# ===== [VIA:ACCEL-BRIDGE:v0100]" in src and "import VIA_SuperAccel_Module" in src)
    chk("② 網路工具橋:本檔不呼叫網路(不需要;網路呼叫照前版)", not re.search(r"^\s*(import|from)\s+(requests|urllib\.request|http\.client|yfinance)\b", src, re.M))
    sha = hashlib.sha256(PRIOR_PATH.read_bytes().replace(b"\r\n", b"\n")).hexdigest() if PRIOR_PATH.exists() else ""
    chk("③ 前版 %s 一字不動(SHA = 出版時記的)" % PRIOR_NAME, sha == PRIOR_SHA256, sha[:16])
    chk("④ 零 TA-Lib · 本檔不連網", not re.search(r"^\s*(import|from)\s+(talib|requests|yfinance)\b", src, re.M))
    cp = subprocess.run([sys.executable, str(PRIOR_PATH)] + ["--selftest"], cwd=str(HERE), timeout=1800, capture_output=True, text=True)
    sys.stdout.write(cp.stdout[-4000:])
    rc = cp.returncode
    if rc != 0 and "缺少 polars" in (cp.stdout + cp.stderr):
        print("  [SKIP_ENV] ⑤ 前版自測要 polars(VQG 全鏈依賴);這台沒有 → 照實黃,不代裝(L19)", flush=True)
        n = sum(ok)
        print("[計] %s %s 薄尾 本版 %d/%d · 前版自測 SKIP_ENV(缺 polars)· YELLOW" % (STEM, VERSION, n, len(ok)), flush=True)
        return 2 if n == len(ok) else 1
    chk("⑤ 前版自測(乾淨子行程)rc 0", rc == 0, "rc %s" % rc)
    n = sum(ok)
    print("[計] %s %s 薄尾 %d/%d %s" % (STEM, VERSION, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    return 0 if n == len(ok) else 1


def main() -> int:
    if sys.argv[1:] == ["--selftest"]:
        return selftest()
    sys.argv[0] = str(PRIOR_PATH)
    runpy.run_path(str(PRIOR_PATH), run_name="__main__")   # 前版自己 sys.exit;沒 exit 就回 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
