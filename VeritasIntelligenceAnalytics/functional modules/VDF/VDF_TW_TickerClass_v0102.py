#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF_TW_TickerClass v0102 — v0101 薄尾:補上統包網路工具橋(v0100 / v0101 都沒有)。

2026-11-20 VCGC 稽核實錄(CGC_MDL156 v0115 · CGC_MDL230 v0106):批115 VDF 全導入令要求每一支 VDF 活件尾版都掛統包網路工具橋;
  這支是缺的兩支之一(VDF 網路橋 137/139)。操作員 2026-11-20 同意補橋。
本版只做一件事:掛上 VDF 統一那一塊網路橋(惰性載入、缺席回 None;本檔照舊不連網,零行為變更)。
v0101 一字不動(SHA-256 釘在 PRIOR_SHA256;它在成功鎖定帳 VIA-VDF-MDL295)。前版取法改成 glob(不再把前版名稱寫死)。
公開名稱、main、selftest 全部原樣轉給前版。
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

import ast
import hashlib
import importlib.util
import re
import sys
from pathlib import Path

VERSION_TAIL = "v0102"
HERE = Path(__file__).resolve().parent
_STEM = "VDF_TW_TickerClass"
PRIOR_SHA256 = "8bb5ae7fa1db8fec9336b53897c423c74808473f22ceb1d4ba62442790a2f30c"   # v0101(LF 正規化)


def _vnum(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
PRIOR_SHA_OK = hashlib.sha256(PRIOR_PATH.read_bytes().replace(b"\r\n", b"\n")).hexdigest() == PRIOR_SHA256
_spec = importlib.util.spec_from_file_location("vdf_tickerclass_prior_for_" + VERSION_TAIL, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""))

    print("=== %s %s 薄尾自測(補網路橋;本檔零網路)===" % (_STEM, VERSION_TAIL))
    chk("① 前版 v0101 位元沒變(SHA-256 與釘的值相同)", PRIOR_SHA_OK, PRIOR_PATH.name)
    src = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    defs = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
    chk("② 本檔有網路橋區塊與 _via_net;前版沒有(所以才出這一版)",
        "[VIA:NET-BRIDGE:v0100]" in src and "[VIA:NET-BRIDGE:END]" in src and "_via_net" in defs
        and "[VIA:NET-BRIDGE" not in PRIOR_PATH.read_text(encoding="utf-8"))
    chk("③ 網路工具在這台找得到(以生效計:路徑真的存在)", VIA_NET_TOOL_PATH is not None and Path(VIA_NET_TOOL_PATH).is_file(), VIA_NET_TOOL_PATH)
    chk("④ 加速器橋語法樹裡真的匯入", PRIOR.accel_imported(Path(__file__)))
    me = sys.modules[__name__]
    pub = [n for n in vars(PRIOR.PRIOR) if not n.startswith("_") and callable(getattr(PRIOR.PRIOR, n))]
    chk("⑤ 本體(v0100)公開名稱經本檔都拿得到", all(callable(getattr(me, n, None)) for n in pub) and len(pub) > 3, "%d 個" % len(pub))
    chk("⑥ 不含本機路徑 · 不碰 TA-Lib · 本檔不直接連網(只留惰性橋)",
        ("C:" + "\\Users") not in src and ("import " + "talib") not in src and ("url" + "open(") not in src and ("import req" + "uests") not in src)
    rc = PRIOR.selftest()
    chk("⑦ 前版(v0101 → v0100)自測照過", rc == 0, "rc %s" % rc)
    good = all(ok)
    print("[計] %s %s 本版 %d/%d · %s" % (_STEM, VERSION_TAIL, sum(ok), len(ok), "PASS" if good else "FAIL"))
    return 0 if good else 1


def main(argv=None) -> int:
    """同前版:不帶參數或 --selftest 都跑自測;分類函式用匯入的方式取用。"""
    return selftest()


if __name__ == "__main__":
    raise SystemExit(main())
