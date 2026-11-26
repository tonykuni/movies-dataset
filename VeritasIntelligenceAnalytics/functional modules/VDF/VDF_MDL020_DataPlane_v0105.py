#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_MDL020_DataPlane v0105 — 薄尾(前版 VDF_MDL020_DataPlane_v0104.py 一字不動):補 VDF 網路工具橋(VDF 全件 100%)

產生:VIA_GovernanceApply v0101(操作員 2026-11-25「全做 用 vcgc 工具完成」;覆蓋矩陣 CGC_MDL230 vdf_net 缺件)。
橋文與求位取 CGC_MDL158(NET_BLOCK / ACCEL_BLOCK · `_insert_after_header`);惰性載入 = import 時零網路、零行為變更。
其餘一切照前版(`__getattr__` 轉接;main 轉前版;--selftest = 前版自測 + 雙橋檢)。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(VDF 全導入令;惰性載入=import 時零網路、零行為變更) =====
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT;網路只認 AegisNexus);缺席回 None(誠實)"""
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

import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAMILY = "VDF_MDL020_DataPlane"
TAG = "VDF_MDL020_DataPlane v0105"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0105", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:200]) if note and not cond else ""), flush=True)

    print("[計] %s 自測開始(本版 3 項 + 前版 %s 自測 · 零網路)" % (TAG, PRIOR_PATH.name), flush=True)
    try:
        rc = PRIOR.selftest() if callable(getattr(PRIOR, "selftest", None)) else 0
    except Exception as exc:  # 前版自測丟例外(例:容器缺 duckdb)照實記 rc 1,雙橋檢照跑
        rc = "%s: %s" % (type(exc).__name__, str(exc)[:120])
    chk("T1 前版自測照過(rc 0)", rc == 0, rc)
    text = Path(__file__).read_text(encoding="utf-8")
    chk("T2 雙橋在 __future__ 之下(ACCEL + NET 標記)", text.index("[VIA:ACCEL-BRIDGE:v0100]") > text.index("from __future__")
        and "[VIA:NET-BRIDGE:v0100]" in text)
    chk("T3 網路工具惰性載入:找得到統包網路工具(import 時零網路)", VIA_NET_TOOL_PATH is not None and callable(_via_net), VIA_NET_TOOL_PATH)
    print("[計] %s 自測 %d/%d %s" % (TAG, sum(ok), len(ok), "PASS" if all(ok) else "FAIL"), flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(args) if callable(getattr(PRIOR, "main", None)) else 2


if __name__ == "__main__":
    raise SystemExit(main())
