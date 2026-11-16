#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL245_SDDValidator v0108 — 薄尾:VIA 樹外的正主(倉根 VIA_MCP_Engine)不再讓 SDD 整支炸

實錄(2026-11-14 容器;main 9ed1bb13):via-vcgc sdd check 與 ssot panorama「上下連結@VCGC」都炸
  ValueError: '<倉>/VIA_MCP_Engine/VIA_MCP_Engine_v0103.py' is not in the subpath of '<倉>/VeritasIntelligenceAnalytics'
  根因:本體 v0100 rel(p) 寫死 p.relative_to(VIA);VCGC v0192 起工作流的 mcp 步正主是倉根 VIA_MCP_Engine
  (VCGC-REQ184:刻意放在 VIA 樹外的獨立工具),exemption() / check_engines / real 一碰就丟例外,整組 X-* 列出不來(假紅)。
本版只換一格(v0100 … v0107 一字不動):本體 rel() 換成「在 VIA 樹內照舊回 VIA 相對路徑;樹外回相對於 VIA 的 ../ 路徑」
  —— 樹外的正主照樣受檢(加速器橋 · 網路橋 · 編號),不豁免、不漂白;樹內結果一字不差。
其餘整支照 v0107。只讀,不寫冊。
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
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL245_SDDValidator"
ENGINE = Path(__file__).stem


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location("_sdd_prior_v0108", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR
while "PRIOR" in vars(BASE):
    BASE = vars(BASE)["PRIOR"]
_V0100_REL = BASE.rel


def rel(p) -> str:
    """VIA 樹內:同 v0100(VIA 相對路徑);樹外(倉根 VIA_MCP_Engine 等):相對於 VIA 的 ../ 路徑,不丟例外。"""
    try:
        return _V0100_REL(Path(p))
    except ValueError:
        return Path(os.path.relpath(Path(p).resolve(), BASE.VIA.resolve())).as_posix()


BASE.rel = rel                                  # 本體 exemption / check_engines / real / closeout 以模組全域叫 rel()


def __getattr__(name: str):
    return getattr(PRIOR, name)


def main(argv=None):
    return PRIOR.main(argv)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:300]) if note and not cond else ''}")

    print(f"=== {ENGINE} · 薄尾自測(VIA 樹外正主不炸)===")
    inside = BASE.VIA / "supportive modules" / "registry" / "x.py"
    outside = BASE.VIA.parent / "VIA_MCP_Engine" / "VIA_MCP_Engine_v0103.py"
    raised = ""
    try:
        _V0100_REL(outside)
    except ValueError as exc:
        raised = str(exc)
    chk("① 本體 rel 對樹外正主丟 ValueError(本版要修的那個)· 本版回 ../VIA_MCP_Engine/… · 樹內一字不差",
        raised and rel(outside) == "../VIA_MCP_Engine/VIA_MCP_Engine_v0103.py" and rel(inside) == _V0100_REL(inside) == "supportive modules/registry/x.py",
        (raised[:80], rel(outside)))
    chk("② 換裝在位:本體模組全域 rel = 本版(exemption / check_engines / real 都走這支)", BASE.rel is rel)
    try:
        why = BASE.exemption(outside)
        crashed = ""
    except Exception as exc:  # noqa: BLE001
        why, crashed = None, repr(exc)
    chk("③ 樹外正主進 exemption 不炸,也不被當成正本豁免(照樣受檢)", not crashed and not str(why or "").startswith("正本唯讀"), crashed or why)
    try:
        rep = BASE.check(write=False)
        rows = rep.get("rows") or []
        crashed = ""
    except Exception as exc:  # noqa: BLE001
        rows, crashed = [], repr(exc)
    rules = sorted({r.get("rule") for r in rows})
    chk("④ 實樹:本體 check(write=False) 整輪跑完不炸 · X-* 列都出來(%d 條規則)" % len(rules),
        not crashed and {"X-COL", "X-ENGINE"} <= set(rules), crashed or rules)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑤ 加速器橋 · 網路橋在;不碰 TA-Lib;只讀(本檔不寫檔)", "VIA:ACCEL-BRIDGE" in src and "VIA:NET-BRIDGE" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M) and ".write_text(" not in src.split("def selftest", 1)[0])
    print(f"  [{ENGINE}] 薄尾 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    rc = PRIOR.selftest()
    return rc if all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if sys.argv[1:] == ["--selftest"] else main())
