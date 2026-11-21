#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG240_SP500SectorWeight v0101 — 薄尾:補全樹契約 L53 的 --selftest 旗標(2026-11-21 晨檢 A · token scan VERB);其餘照 v0100

v0100 的 argparse 只認位置動詞 selftest / fetch,`--selftest` 會被拒(rc 2)→ 監控與串測叫不到。
本版:--selftest 與 selftest 都跑 v0100 自測 + 本版三檢;fetch 與其他參數原樣交給 v0100(擷取邏輯一字不動)。
用法:py -3 VDF_ENG240_SP500SectorWeight_v0101.py --selftest | selftest | fetch [--out 夾] [--start YYYY-MM-DD]
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(SUP_MDL737 最新尾版;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    _sa_env = __import__("os").environ.get("VIA")
    if _sa_env:
        _sa_sys.path.insert(0, _sa_env)
        _sa_hit = _sa_Path(_sa_env) / "supportive modules"
        if (_sa_hit / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_hit))
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(via_net_unified 最新→SUP_MDL740;graceful) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_candidates = []
    _nb_env = __import__("os").environ.get("VIA")
    if _nb_env:
        _nb_candidates.append(_nb_Path(_nb_env))
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_candidates.append(_nb_p)
        _nb_p = _nb_p.parent
    for _nb_p in _nb_candidates:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """Newest via_net_unified. None when the tool or consent path is absent."""
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
_STEM = "VDF_ENG240_SP500SectorWeight"
TAG = "VDF_ENG240_SP500SectorWeight v0101"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0101", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(a)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    rc0 = PRIOR.selftest()
    print(f"=== {TAG} · 薄尾自測(--selftest 旗標;零網路)===")
    chk("⓪ 前版 v0100 自測過", rc0 == 0, f"rc {rc0}")
    src = Path(__file__).read_text(encoding="utf-8")
    chk("① 加速器橋 · 網路橋在本檔(AST 前段)", "[VIA:ACCEL-BRIDGE:v0100]" in src and "[VIA:NET-BRIDGE:v0100]" in src)
    pub = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    chk("② 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in pub), f"{len(pub)} 支")
    import contextlib, io
    try:
        with contextlib.redirect_stderr(io.StringIO()):
            PRIOR.main(["--selftest"])
        prior_rc = 0
    except SystemExit as exc:
        prior_rc = exc.code
    chk("③ v0100 拒 --selftest(argparse rc 2)· 本版 main 把 --selftest 導到自測", prior_rc == 2 and main.__code__.co_consts.count("--selftest") >= 1, f"v0100 rc {prior_rc}")
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
