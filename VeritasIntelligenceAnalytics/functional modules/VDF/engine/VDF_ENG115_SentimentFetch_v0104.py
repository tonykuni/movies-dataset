#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_ENG115_SentimentFetch v0104 — 薄尾:補 v0103 的轉接漏洞(前版鏈的公開名稱取不到)

PR #589 Codex 審查 P2(本機重現屬實):v0103 的 __getattr__ 只看 v0101 / v0102 的 vars(),
  v0102 靠它自己的 __getattr__ 從 v0100 轉來的名稱(allowed · cnn · AAII_URL …)在 v0103 變成 AttributeError;
  v0103 自測只列 vars(fwd),漏掉動態轉接的名稱。
本版只改這一件(v0100 … v0103 一字不動):
  · 轉接順序 = v0103 認得的 → 改道後的 v0100(網路函數照 v0103 走網路工具)→ v0102 自己的動態轉接;找不到照實 AttributeError。
  · 自測改用 v0102 的 public_names()(含 v0100)逐一取,另驗經本版取到的網路函數仍走網路工具。
其餘(直接執行 = v0101 的 main · 同意閘不讀不寫 · 不碰 TA-Lib)照 v0103。
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
    """統包唯一網路工具惰性載入;本檔的連網全經 MDL008 子行程改道。"""
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

import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG115_SentimentFetch"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
PRIOR_PATH = HERE / (_STEM + "_v0103.py")        # 前版(改經網路工具的那一版)
FWD_PATH = HERE / (_STEM + "_v0102.py")          # 公開名稱轉接層(它自己的 __getattr__ 沿 v0101 → v0100 找)


def _load(p: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


PRIOR = _load(PRIOR_PATH, _STEM + "_prior_for_v0104")
_PATCHED = None
_FWD = None


def _patched_v0100():
    """v0100 一份(已把直連函數換成經網路工具的版本 · v0103 的 _prior_net)· 只取一次。"""
    global _PATCHED
    if _PATCHED is None:
        _PATCHED = PRIOR._prior_net()
    return _PATCHED


def __getattr__(name):
    """轉接順序:v0103 認得的 → 改道後的 v0100(網路函數走網路工具)→ v0102 自己的動態轉接(最後一道)。雙底線不轉。"""
    global _FWD
    if name.startswith("__"):
        raise AttributeError(name)
    try:
        return getattr(PRIOR, name)
    except AttributeError:
        pass
    m = _patched_v0100()
    if name in vars(m):
        return vars(m)[name]
    if _FWD is None:
        _FWD = _load(FWD_PATH, _STEM + "_fwd_v0102_from_v0104")
    return getattr(_FWD, name)                    # 找不到 → 照實 AttributeError


def main() -> int:
    return PRIOR.main()


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""), flush=True)

    print("=== %s · 薄尾自測(補轉接:前版鏈每個公開名稱都取得到 · 網路函數仍走網路工具)===" % TAG, flush=True)
    p = subprocess.run([sys.executable, str(PRIOR_PATH), "--selftest"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    last = [ln for ln in p.stdout.splitlines() if "[計]" in ln]
    print("  ── 前版 " + (last[-1].strip() if last else "(沒有總行)"), flush=True)
    chk("① 前版 %s 自測 rc 0(改道 · DENY · 工具不在 · 前版 v0102 自測)" % PRIOR_PATH.stem, p.returncode == 0, "rc %s" % p.returncode)
    fwd = _load(FWD_PATH, _STEM + "_fwd_names_v0104")
    names = list(fwd.public_names())
    miss = []
    for n in names:
        try:
            __getattr__(n) if n not in globals() else globals()[n]
        except AttributeError:
            miss.append(n)
    chk("② 前版鏈每個公開名稱(v0102 public_names · %d 個 · 含 v0100 的)本版都取得到" % len(names), names and not miss, miss[:8])
    calls = []

    class FakeNet:
        def http_json(self, url, timeout=30):
            calls.append(url)
            return {"state": "DENY", "note": "fail-closed:閘一未開"}

        def http_bytes(self, url, timeout=30, retries=3, backoff=1.0, headers=None):
            calls.append(url)
            return {"state": "DENY", "note": "fail-closed:閘一未開"}

    import urllib.request
    real = urllib.request.urlopen

    def no_direct(*a, **k):
        raise AssertionError("直連 urlopen 被呼叫")

    urllib.request.urlopen = no_direct
    try:
        PRIOR._NET_OVERRIDE = FakeNet()
        fn = __getattr__(NET_NAME)
        try:
            NET_CALL(fn)
            raised = None
        except Exception as exc:                     # noqa: BLE001 — 自測要看到任何例外
            raised = exc
        routed = bool(calls) and not isinstance(raised, AssertionError)
    finally:
        urllib.request.urlopen = real
        PRIOR._NET_OVERRIDE = None
    chk("③ 經本版取到的 %s 走網路工具(假工具回 DENY · 直連 urlopen 0 次)" % NET_NAME, routed, "calls %d · %s" % (len(calls), type(raised).__name__ if raised else "-"))
    try:
        __getattr__("via_no_such_name_v0104")
        honest = False
    except AttributeError:
        honest = True
    chk("④ 不存在的名稱照實 AttributeError(不吞)", honest)
    src = Path(__file__).read_text(encoding="utf-8")
    head = src.split("def selftest", 1)[0]
    chk("⑤ 加速器橋 · 網路工具橋在;本檔(自測以外)沒有直連;不代設同意閘;不碰 TA-Lib",
        "[VIA:ACCEL-BRIDGE" in src and "[VIA:NET-BRIDGE" in src and ".urlopen(" not in head and "requests." not in head
        and "CONSENT\"] =" not in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M))
    good = all(ok)
    print("[計] %s 本版 %d/%d · 前版 %s · %s" % (TAG, sum(ok), len(ok), "PASS" if p.returncode == 0 else "FAIL", "PASS" if good else "FAIL"), flush=True)
    return 0 if good else 1


NET_NAME = 'cnn'
NET_CALL = lambda f: f()


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv[1:] else main())

