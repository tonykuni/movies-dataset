#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL256_SubsystemBundle v0101 — 薄尾:下載包冊取尾版(VIA_SubsystemBundle_SSOT_v*.json 最大版號)

v0100 把冊釘在 VIA_SubsystemBundle_SSOT_v0100.json(預設參數在定義時就綁死),新測過的指令要進包只能改舊冊(違 L4)。
本版只換「冊從哪來」:取 registry 下版號最大的那本;build / verify / preflight / list 與 MANIFEST · README · requirements
寫法全照 v0100。冊 v0101(VCGC-REQ144)= v0100 全部檔案 + 前版在包裡的新版(MDL009 v0101 · MDL008 v0102 · 擷取冊 v0102 ·
本支 / 本冊)+ MDL009 v0101 自測比對用的官方 t187ap03_L 快照。不連網;不改被打包的檔;不碰 TA-Lib;不代設同意閘。
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

import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL256_SubsystemBundle"
ENGINE = Path(__file__).stem


def _vnum_v0101(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0101(p) < _vnum_v0101(__file__)), key=_vnum_v0101)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


def book_tail_v0101() -> Path:
    return max(HERE.glob("VIA_SubsystemBundle_SSOT_v*.json"), key=_vnum_v0101)


BOOK = book_tail_v0101()


def load_book_v0101(path: Path | None = None) -> dict:
    return json.loads(Path(path or book_tail_v0101()).read_text(encoding="utf-8"))


_ENGINE_V0100 = PRIOR.ENGINE
PRIOR.load_book, PRIOR.BOOK, PRIOR.ENGINE = load_book_v0101, BOOK, ENGINE


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    return PRIOR.main(args)


def selftest() -> int:
    PRIOR.ENGINE = _ENGINE_V0100                       # v0100 自測行照記它自己的名字(交接案 bundle_tool 認這行);冊已是尾版
    try:
        rc0 = PRIOR.selftest()
    finally:
        PRIOR.ENGINE = ENGINE
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {ENGINE} · 薄尾自測(冊取尾版)===")
    chk("① v0100 自測照過(用的是尾版冊:build · verify · preflight · 只放鎖版網路 / 加速器)", rc0 == 0, f"rc {rc0}")
    tail = book_tail_v0101()
    cur, old = load_book_v0101(), load_book_v0101(HERE / "VIA_SubsystemBundle_SSOT_v0100.json")
    lost = {n: [f for f in s["files"] if f not in cur["bundles"].get(n, {}).get("files", [])] for n, s in old["bundles"].items()}
    chk("② 冊 = registry 下最大版號那本;舊冊每包的檔全在(只增)", tail.name == f"VIA_SubsystemBundle_SSOT_v{max(_vnum_v0101(p) for p in HERE.glob('VIA_SubsystemBundle_SSOT_v*.json')):04d}.json"
        and not any(lost.values()), (tail.name, {k: len(v) for k, v in lost.items()}))
    vdf = cur["bundles"]["via_01_vdf"]["files"]
    want = ["functional modules/VDF/VDF_MDL009_TWStockList_v0101.py", "functional modules/VDF/VDF_MDL008_FetchSystem_v0102.py",
            "functional modules/VDF/VDF_FetchSystem_SSOT_v0102.json"]
    chk("③ via_01_vdf 帶新測過的 MDL009 v0101 · MDL008 v0102 · 擷取冊 v0102,且檔在樹上", all(w in vdf and (PRIOR.VIA / w).is_file() for w in want))
    text = Path(__file__).read_text(encoding="utf-8")
    chk("④ 加速器橋 · 網路橋在;不碰 TA-Lib", "[VIA:ACCEL-BRIDGE" in text and "[VIA:NET-BRIDGE" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M))
    print(f"  [計] {ENGINE} 本版 {sum(ok)}/{len(ok)} · v0100 {'PASS' if rc0 == 0 else 'FAIL'} · 合計 {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
