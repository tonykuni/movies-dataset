#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL245_SDDValidator v0108 — 薄尾:倉根內、VIA 根外的引擎路徑(../VIA_MCP_Engine/…)不再讓 SDD 整支炸

2026-11-13 VCGC closeout 量到:SDD 檢查在 v0100 本體 rel() 丟 ValueError
  '/…/VIA_MCP_Engine/VIA_MCP_Engine_v0103.py' is not in the subpath of '/…/VeritasIntelligenceAnalytics'
——VCGC-WKF042-STP003(REQ222,2026-11-10)的引擎寫成 `../VIA_MCP_Engine/VIA_MCP_Engine_v0103.py`,在倉根、不在 VIA 根。
乾淨 main 上重現同一個例外:自那天起 SDD 一直跑不完 → closeout 停在 ⑥、沒有人能 checkpoint;v0107 自測 ⑧(實樹 check)也因此 FAIL。
修法只換本體的 rel()(其餘 7 處呼叫都在本體,經模組全域名查找,換一處即全換):
  VIA 根內 → 與 v0100 逐字相同;
  倉根內、VIA 根外 → 回 `../<相對倉根>`(與工作流冊寫法同形,下游 VIA / rel 解得回原檔);
  倉外 → 照舊丟 ValueError(真的越界不漂白)。
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


def rel(p: Path) -> str:
    """VIA 根內同 v0100;倉根內 VIA 根外回 ../<相對倉根>;倉外照舊丟 ValueError。"""
    try:
        return _V0100_REL(p)
    except ValueError:
        rp = Path(p).resolve()
        repo = BASE.VIA.resolve().parent
        if rp.is_relative_to(repo):
            return "../" + rp.relative_to(repo).as_posix()
        raise


BASE.rel = rel


def __getattr__(name: str):
    return getattr(PRIOR, name)


def main(argv=None):
    return PRIOR.main(argv)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:300]) if note else ''}")

    print(f"=== {ENGINE} · 薄尾自測(rel 倉根內 VIA 根外不炸 · 實樹 check 跑完)===")
    via = BASE.VIA.resolve()
    inside = via / "supportive modules" / "registry" / (Path(__file__).name)
    chk("① VIA 根內:與 v0100 逐字相同", rel(inside) == _V0100_REL(inside), rel(inside))
    sib = via.parent / "VIA_MCP_Engine" / "VIA_MCP_Engine_v0103.py"
    got = rel(sib)
    chk("② 倉根內 VIA 根外 → ../<相對倉根>,且 VIA / rel 解得回原檔", got == "../VIA_MCP_Engine/VIA_MCP_Engine_v0103.py"
        and (via / got).resolve() == sib.resolve(), got)
    try:
        rel(Path("/") / "definitely_outside_repo_x" / "a.py")
        outside = "沒丟"
    except ValueError:
        outside = "ValueError"
    chk("③ 倉外照舊丟 ValueError(真越界不漂白)", outside == "ValueError", outside)
    chk("④ 換的是本體那一支:BASE.rel is 本版 rel", BASE.rel is rel)
    try:
        rep = BASE.check(write=False)
        crashed, n = "", len(rep.get("rows") or [])
    except Exception as exc:  # noqa: BLE001
        crashed, n = repr(exc)[:200], 0
    chk("⑤ 實樹:本體 check(write=False) 整輪跑完不炸(2026-11-13 closeout ⑥ 的根因)· 有 X-* 列", not crashed and n > 0, crashed or f"列 {n}")
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 加速器橋 · 網路橋在;不碰 TA-Lib", "VIA:ACCEL-BRIDGE" in src and "VIA:NET-BRIDGE" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M))
    print(f"  [{ENGINE}] 薄尾 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    rc = PRIOR.selftest()
    return rc if all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if sys.argv[1:] == ["--selftest"] else main())
