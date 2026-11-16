#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_NetFetch v0101 — 薄尾(v0100 一字不動):補標準網路工具橋(L103 最高政策 · VIA_ListsFirstDAG 覆蓋實測)

緣由(2026-11-16 · 操作員桌機 VIA_ListsFirstDAG v0101 ① 覆蓋表 + 本倉同一量尺重跑):前版下載經 SUP_MDL740_NetUnified 動態載入(本身就是網路工具的使用者),但檔面沒有標準網路工具橋塊;清掃器 v0105 活樹量尺判網路缺 2 支之一。
本版只加橋塊;其餘全部原樣交前版:
  · 以腳本執行(任何參數,含前版自己的動詞)→ runpy 以 __main__ 跑前版,sys.argv 原封不動(行為 = 前版)。
  · 被 import → 公開名稱經 __getattr__ 轉接前版(尾版不少名字 · TAILAPI)。
  · `--selftest` → 先驗本版(橋塊在 · 前版 SHA 沒變),再以乾淨子行程跑前版自測(rc 照前版)。
所屬:VCGC 自己的檔(L123:VCGC 自己出新版;他系統不代改)。零網路 · 不用 TA-Lib · 不寫同意閘 · 不裝套件。
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
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import hashlib
import importlib.util
import re
import runpy
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "VIA_NetFetch"
VERSION = "v0101"
PRIOR_NAME = "VIA_NetFetch_v0100.py"
PRIOR_PATH = HERE / PRIOR_NAME
PRIOR_SHA256 = "e7048d3f5ba8e0edfce8f10e66521f9a267aaa8aeb45fc338eaeedf73cc79d1f"                       # 前版(LF 正規化後)· 前版一字不動的證據
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

    print("=== %s %s · 薄尾自測(補標準網路工具橋)===" % (STEM, VERSION), flush=True)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("① 本檔帶標準加速器橋塊(import VIA_SuperAccel_Module)", "# ===== [VIA:ACCEL-BRIDGE:v0100]" in src and "import VIA_SuperAccel_Module" in src)
    chk("② 網路工具橋:本檔帶標準網路橋塊(VIA_NET_TOOL_PATH · def _via_net)", "# ===== [VIA:NET-BRIDGE:v0100]" in src and "VIA_NET_TOOL_PATH" in src and "def _via_net" in src)
    sha = hashlib.sha256(PRIOR_PATH.read_bytes().replace(b"\r\n", b"\n")).hexdigest() if PRIOR_PATH.exists() else ""
    chk("③ 前版 %s 一字不動(SHA = 出版時記的)" % PRIOR_NAME, sha == PRIOR_SHA256, sha[:16])
    chk("④ 零 TA-Lib · 本檔不連網", not re.search(r"^\s*(import|from)\s+(talib|requests|yfinance)\b", src, re.M))
    rc = subprocess.run([sys.executable, str(PRIOR_PATH)] + ["--selftest"], cwd=str(HERE), timeout=1800).returncode
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
