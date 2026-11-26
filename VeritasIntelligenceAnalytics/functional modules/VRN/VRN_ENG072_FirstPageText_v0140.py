#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_ENG072_FirstPageText v0140 — 薄尾(v0139 以前一字不動):nlp_hub / gle_hub 改走 NLP · layout · markdown 唯一入口 SUP_MDL866(v0110 起)

操作員 2026-11-25「NLP layout markdown 在倉內整合成一支 · 不衝突 · 不會沒人維護 · 只增不減 · 用 VCGC 工具完成」。
VCGC 語法樹掃描:本家族的 nlp_hub / gle_hub 會繞過入口直接掛收容件。本版把前版鏈上每一支定義了這些名字的模組換成
「先問 SUP_MDL866 唯一入口,入口不在或回空 → 照前版原路」(只增不減;收容件原地不動;其餘一字不動)。
用法同前版 | --selftest(本版三檢 + 前版自測)
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_ENG072_FirstPageText"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


def _entry():
    """NLP · layout · markdown 唯一入口(SUP_MDL866 v0110 以上的尾版);找不到 = None(各函式照前版原路)。"""
    if "_VIA_NLP_ENTRY" in globals():
        return globals()["_VIA_NLP_ENTRY"]
    mod = None
    p = Path(__file__).resolve()
    while p.parent != p:
        d = p / "supportive modules" / "70_VRN_Rules"
        if d.is_dir():
            hits = sorted(d.glob("SUP_MDL866_VIAUnifiedNLPOrchestrator_v*.py"), key=_vnum)
            if hits and _vnum(hits[-1]) >= 110:
                name = hits[-1].stem
                mod = sys.modules.get(name)
                if mod is None:
                    try:
                        sp = importlib.util.spec_from_file_location(name, hits[-1])
                        mod = importlib.util.module_from_spec(sp)
                        sys.modules[name] = mod
                        sp.loader.exec_module(mod)
                    except Exception:  # noqa: BLE001
                        sys.modules.pop(name, None)
                        mod = None
            break
        p = p.parent
    globals()["_VIA_NLP_ENTRY"] = mod
    return mod


def _chain():
    m, seen = PRIOR, []
    while m is not None and m not in seen:
        seen.append(m)
        nxt = vars(m).get("PRIOR")
        m = nxt if hasattr(nxt, "__dict__") and not isinstance(nxt, (str, Path)) else None
    return seen


ROUTES = {'nlp_hub': 'nlp_hub', 'gle_hub': 'layout_hub'}
_ORIG = {}


def _make(name, entry_fn, fallback):
    def routed(*a, **k):
        e = _entry()
        if e is not None:
            try:
                r = getattr(e, entry_fn)(*a, **k)
                if r is not None:
                    return r
            except Exception:  # noqa: BLE001
                pass
        return fallback(*a, **k)
    routed.__name__ = name
    routed.__doc__ = f"{name}:先走唯一入口 SUP_MDL866.{entry_fn},入口不在 / 回空 → 前版原路"
    routed._via_routed = True
    return routed


PATCHED = []
for _m in _chain():
    for _name, _efn in ROUTES.items():
        _f = vars(_m).get(_name)
        if callable(_f) and not getattr(_f, "_via_routed", False):
            _ORIG[(_m.__name__, _name)] = _f
            setattr(_m, _name, _make(_name, _efn, _f))
            PATCHED.append(f"{_m.__name__}.{_name}")


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    sys.argv = [sys.argv[0]] + a
    return PRIOR.main()


def selftest() -> int:
    ok = bad = 0

    def chk(n, c, note=""):
        nonlocal ok, bad
        ok += bool(c)
        bad += not c
        print(f"  [{'OK' if c else 'FAIL'}] {n} {note}", flush=True)

    e = _entry()
    chk("① 找到唯一入口 SUP_MDL866(v0110 以上)", e is not None, f"({getattr(e, '__name__', None)})")
    chk("② 前版鏈上要改道的名字都換了", all(any(p.endswith("." + n) for p in PATCHED) for n in ROUTES), f"({len(PATCHED)} 處)")
    chk("③ nlp_hub / gle_hub 拿到的是入口給的同一支後端", PRIOR.nlp_hub() is e.nlp_hub() and PRIOR.gle_hub() is e.layout_hub())
    rc = PRIOR.selftest() if hasattr(PRIOR, "selftest") else 0
    print(f"  [..] 前版自測 rc {rc}(只增不減:本版不改前版判準)")
    print(f"  [計] {_STEM} v0140 自測 OK {ok} · FAIL {bad} · 前版 rc {rc}")
    return 1 if bad else (rc or 0)


if __name__ == "__main__":
    sys.exit(main())
