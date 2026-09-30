#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL237_NumberingSystem v0103 — 薄尾:編號系統自己的產出不算 SSOT 內容指紋(Codex #356 P2 · Z282③)

v0102 的 ssot_items() 給每本 SSOT 冊算 content_sha;但 VIA_Numbering_SSOT_v*.json 就是 build(--apply) 這一次要重寫的那本 ——
先讀舊檔算指紋、再把指紋寫進新檔,寫完當下那一列就對不上,而且每跑一次都變。本尾版:編號系統自己的產出
(VIA_Numbering_SSOT_v* · VIA_NumberBooks/*)那幾列不帶 content_sha / declared_version(列本身與號碼照舊,只增律不動)。
其餘整支照 v0102(thin tail;__getattr__ 轉接)。只收 VCGC 呼叫(VIA_FROM_VCGC=YES)的規矩照前一版。
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

STEM = "CGC_MDL237_NumberingSystem"

import importlib.util
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", path.stem)
    return int(m.group(1)) if m else -1


PRIOR = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(STEM + "_prior_for_" + Path(__file__).stem, PRIOR)
_PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _PRIOR
_spec.loader.exec_module(_PRIOR)
ENGINE = Path(__file__).stem


def __getattr__(name: str):
    return getattr(_PRIOR, name)

OWN_OUTPUT = re.compile(r"(^|/)VIA_Numbering_SSOT_v\d+\.json$|(^|/)VIA_NumberBooks/")
_BASE = _PRIOR._BASE
_V0102_SSOT = _BASE.ssot_items


def ssot_items() -> list:
    out = _V0102_SSOT()
    for it in out:
        if OWN_OUTPUT.search(str(it.get("source") or "")):
            it.pop("content_sha", None)
            it.pop("declared_version", None)
    return out


_BASE.ssot_items = ssot_items


def main(argv=None) -> int:
    if "--selftest" in (sys.argv[1:] if argv is None else argv):
        return selftest()
    return _PRIOR.main(argv)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    ss = ssot_items()
    own = [it for it in ss if OWN_OUTPUT.search(str(it.get("source") or ""))]
    chk("Z282③ 編號系統自己的產出不帶 content_sha(寫完就對不上的那一列)", own and all("content_sha" not in it for it in own), f"{len(own)} 列")
    chk("其他 SSOT 冊照舊帶內容指紋", all(it.get("content_sha") for it in ss if it not in own), f"{len(ss) - len(own)} 本")
    if not all(ok):
        return 1
    return _PRIOR.selftest()


if __name__ == "__main__":
    raise SystemExit(main())
