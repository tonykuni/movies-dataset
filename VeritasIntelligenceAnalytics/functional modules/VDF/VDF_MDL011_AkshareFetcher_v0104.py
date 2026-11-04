#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL011_AkshareFetcher v0104 — 薄尾:文件爬取 _get 由直連 requests.get 改經 VIA 網路工具(http_text · L103)

操作員 2026-11-04 令「開始 VDF / VCGC CLOSE OUT」;收尾規格 §8 第 3 項「外連動詞 100% 經網路工具」。
全景 AST 稽核:v0100 的 _get(AkShare 文件索引 / 文件頁)直接 requests.get;v0100 檔頭寫的「live 模式 requests 經鎖版網路工具」
  在程式裡找不到對應接線(只有一行說明)→ 實際是直連。
本版只改這一件(v0100 … v0103 一字不動):
  · 沿前版鏈找到定義 _get 的那一支(v0100),把它換成經網路工具 http_text 的版本(雙閘先行 · 永不代設);
    成功回文字、失敗照原樣丟 RuntimeError("GET failed …")(discover_pages 原本就會退回內建清單)· 不退回直連。
  · 其他(動詞 · deep-macro · 缺套件 NODATA · 自測鏈)照 v0103。
不代裝套件、不讀寫同意閘、不碰 TA-Lib。VDF 自己的模組(網路工具 = 全樹統包工具)。
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
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import os
import re
import subprocess
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_MDL011_AkshareFetcher"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
_NET_OVERRIDE = None                              # 自測用假網路工具;正式執行 = None


def _vnum_v0104(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0104(p) < _vnum_v0104(__file__)), key=_vnum_v0104)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)                  # v0103 自己接缺套件(PRIOR.PRIOR = None → NODATA)


def __getattr__(name):
    return getattr(PRIOR, name)


def _chain_v0104() -> list:
    out, m = [], PRIOR
    while isinstance(m, types.ModuleType) and m not in out:
        out.append(m)
        m = getattr(m, "PRIOR", None)
    return out


def _owner_v0104(name: str):
    for m in _chain_v0104():
        if name in vars(m) and callable(vars(m)[name]):
            return m
    return None


def _net():
    net = _NET_OVERRIDE if _NET_OVERRIDE is not None else _via_net()
    if net is None:
        raise RuntimeError("VIA 網路工具不在(supportive modules/network/via_net_unified_v*.py)· 不直連")
    return net


def _get_net(url, retries=3, timeout=25):
    """v0100 _get 的同一介面:成功回文字;失敗丟 RuntimeError("GET failed …")(網路工具自己重試 · 雙閘先行)。"""
    r = _net().http_text(url, timeout=timeout)
    if not isinstance(r, dict) or r.get("state") != "OK" or not isinstance(r.get("data"), str):
        r = r if isinstance(r, dict) else {}
        raise RuntimeError("GET failed %s: 網路工具 %s %s" % (url, r.get("state"), (r.get("note") or "")[:160]))
    return r["data"]


OWNER_GET = _owner_v0104("_get")
if OWNER_GET is not None:
    OWNER_GET._get = _get_net


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    return PRIOR.main(args)


def selftest() -> int:
    global _NET_OVERRIDE
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}", flush=True)

    print(f"=== {TAG} · 薄尾自測(_get 改經 VIA 網路工具;零網路 · 假網路工具)===", flush=True)
    p = subprocess.run([sys.executable, str(PRIOR_PATH), "--selftest"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    last = (p.stdout.strip().splitlines() or ["(無輸出)"])[-1]
    print("  ── 前版自測(末行)── " + last, flush=True)
    if OWNER_GET is None:
        chk("① 前版鏈載不起來(缺套件)→ 照 v0103 NODATA · 沒有 _get 可換", p.returncode == 2, "rc %s" % p.returncode)
        print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · 前版鏈 NODATA · 合計 NODATA rc 2", flush=True)
        return 2
    chk("① 前版 %s 自測 rc 0" % PRIOR_PATH.stem, p.returncode == 0, "rc %s" % p.returncode)
    calls = []

    class FakeNet:
        def __init__(self, state):
            self.state = state

        def http_text(self, url, timeout=30):
            calls.append((url, timeout))
            if self.state == "OK":
                return {"state": "OK", "data": '<a href="macro/macro_china.html">x</a>'}
            return {"state": self.state, "note": "fail-closed:閘一未開"}

    import requests as _rq
    real_get = _rq.get

    def no_direct(*a, **k):
        raise AssertionError("直連 requests.get 被呼叫")

    _rq.get = no_direct
    try:
        _NET_OVERRIDE = FakeNet("OK")
        txt = OWNER_GET._get("https://akshare.akfamily.xyz/data/index.html")
        chk("② 改道:前版鏈的 _get 經假網路工具拿到文字 · 直連 requests.get 0 次", "macro_china" in txt and calls and OWNER_GET._get is _get_net)
        _NET_OVERRIDE = FakeNet("DENY")
        try:
            OWNER_GET._get("https://x.invalid/a")
            denied = False
        except RuntimeError as exc:
            denied = "GET failed" in str(exc) and "DENY" in str(exc)
        chk("③ 同意閘沒開 → 照原樣丟 RuntimeError(GET failed … DENY)· 不退直連", denied)
        own_dp = _owner_v0104("discover_pages")
        pages = own_dp.discover_pages() if own_dp is not None else None
        chk("④ 回歸:discover_pages 在 DENY 下照舊退回內建清單(不崩)", isinstance(pages, list) and len(pages) > 0, len(pages or []))
        _NET_OVERRIDE = None
        saved = globals()["_via_net"]
        globals()["_via_net"] = lambda: None
        try:
            _get_net("https://x.invalid/b")
            missing = False
        except RuntimeError as exc:
            missing = "不直連" in str(exc)
        finally:
            globals()["_via_net"] = saved
        chk("⑤ 網路工具不在 → 照實拒絕(不退回直連)", missing)
    finally:
        _rq.get = real_get
        _NET_OVERRIDE = None
    src = Path(__file__).read_text(encoding="utf-8")
    head = src.split("def selftest", 1)[0]
    chk("⑥ 加速器橋 · 網路工具橋在;本檔(自測以外)沒有直連 requests / urlopen;不代設同意閘;不碰 TA-Lib",
        "[VIA:ACCEL-BRIDGE" in src and "[VIA:NET-BRIDGE" in src and "requests.get(" not in head and ".urlopen(" not in head
        and "CONSENT\"] =" not in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M))
    good = all(ok)
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · 前版 {'PASS' if p.returncode == 0 else 'rc ' + str(p.returncode)} · 合計 {'PASS' if good else 'FAIL'}", flush=True)
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
