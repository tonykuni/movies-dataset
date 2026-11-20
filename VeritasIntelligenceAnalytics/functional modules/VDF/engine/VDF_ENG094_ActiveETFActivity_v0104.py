#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VDF_ENG094_ActiveETFActivity v0104 — 薄尾:補上統包網路工具橋(v0102 / v0103 的薄尾漏帶)。

2026-11-20 VCGC 稽核實錄(CGC_MDL156 v0115 · CGC_MDL230 v0106):批115 VDF 全導入令要求每一支 VDF 活件尾版都掛統包網路工具橋;
  v0101 有 [VIA:NET-BRIDGE] 區塊,v0102 / v0103 是薄尾、沒帶 → VDF 網路橋 137/139,這支是缺的兩支之一。
操作員 2026-11-20 同意補橋。本版只做一件事:掛上與 v0101 同一塊網路橋(惰性載入、缺席回 None,零行為變更)。
v0103 一字不動(SHA-256 釘在 PRIOR_SHA256;它在成功鎖定帳 VIA-VDF-ENG378)。
v0103 的接法原樣保留:本檔自己放 analyze 與 build,在尾版上替換 analyze,build 會用到(CI test_via_etf_activity 的斷言)。
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
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import hashlib
import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG094_ActiveETFActivity"
VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]
PRIOR_SHA256 = "d2724a42cb89516192b8c5fcaf3eae7a596acadf9401497394a61145264272f9"   # v0103(LF 正規化)


def _vnum(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
PRIOR_SHA_OK = hashlib.sha256(PRIOR_PATH.read_bytes().replace(b"\r\n", b"\n")).hexdigest() == PRIOR_SHA256
_spec = importlib.util.spec_from_file_location("eng094_prior_for_v" + VERSION, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)          # v0103
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BODY = PRIOR.BODY                                       # v0101(它的 build 會呼叫自己那一格 analyze)


def __getattr__(name: str):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


# 同 v0103:build 內部叫的 analyze 走本模組這一格(CI 取家族尾版後 patch 這裡)
analyze = BODY.analyze


def build(*args, **kwargs):
    """本體 build 原樣;只把它呼叫的 analyze 換成本模組當下的 analyze(可被測試替換),跑完還原。"""
    orig = BODY.analyze
    BODY.analyze = globals()["analyze"]
    try:
        return BODY.build(*args, **kwargs)
    finally:
        BODY.analyze = orig


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a or "selftest" in a:
        return selftest()
    return PRIOR.main(argv)


def selftest() -> int:
    import ast
    from unittest import mock
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""))

    print("=== %s v%s 薄尾自測(補網路橋;零網路)===" % (_STEM, VERSION))
    chk("① 前版 v0103 位元沒變(SHA-256 與釘的值相同)", PRIOR_SHA_OK, PRIOR_PATH.name)
    src = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    defs = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
    chk("② 本檔有網路橋區塊與 _via_net;前版沒有(所以才出這一版)",
        "[VIA:NET-BRIDGE:v0100]" in src and "[VIA:NET-BRIDGE:END]" in src and "_via_net" in defs
        and "[VIA:NET-BRIDGE" not in PRIOR_PATH.read_text(encoding="utf-8"))
    chk("③ 網路工具在這台找得到(以生效計:路徑真的存在)", VIA_NET_TOOL_PATH is not None and Path(VIA_NET_TOOL_PATH).is_file(), VIA_NET_TOOL_PATH)
    chk("④ 加速器橋語法樹裡真的匯入", any(isinstance(n, ast.Import) and any(a.name == "VIA_SuperAccel_Module" for a in n.names) for n in ast.walk(tree)))
    me = sys.modules[__name__]
    calls = []
    saved_build, saved_an = BODY.build, BODY.analyze
    BODY.build = lambda *a, **k: ("built", BODY.analyze("x"))
    try:
        with mock.patch.object(me, "analyze", side_effect=lambda v: calls.append(v) or "patched"):
            got = build()
        mid = BODY.analyze
    finally:
        BODY.build = saved_build
    chk("⑤ 在尾版上替換 analyze → build 用到的就是替換後那一支(v0103 的 CI 斷言照過)", got == ("built", "patched") and calls == ["x"], got)
    chk("⑥ build 跑完本體的 analyze 還原", mid is saved_an and BODY.analyze is saved_an)
    chk("⑦ 其他公開名稱原樣轉交(inspect_database · fetch · read_metrics · ruler · vdf_gate_open)",
        all(callable(getattr(me, n, None)) for n in ("inspect_database", "fetch", "read_metrics", "ruler", "vdf_gate_open")))
    chk("⑧ 不含本機路徑 · 不碰 TA-Lib · 不寫同意值",
        ("C:" + "\\Users") not in src and ("import " + "talib") not in src and ("_CONSENT\"] " + "=") not in src)
    rc = PRIOR.selftest()
    chk("⑨ 前版(v0103 → v0102 → v0101)自測照過", rc == 0, "rc %s" % rc)
    good = all(ok)
    print("[計] %s v%s 本版 %d/%d · %s" % (_STEM, VERSION, sum(ok), len(ok), "PASS" if good else "FAIL"))
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
