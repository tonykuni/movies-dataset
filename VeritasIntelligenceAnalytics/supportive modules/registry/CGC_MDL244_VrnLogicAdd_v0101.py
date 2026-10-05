#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL244_VrnLogicAdd v0101 — 薄尾:派 VRN 引擎自測改走家族境 python(修全景 SYSEXE)

via_precheck(CGC_MDL263)④ 全景 AST 稽核 PC-174:v0100 check() 以 sys.executable 派 VRN 引擎
(functional modules/VRN/VIA_VRNLogic_AllInOne_v0201.py)自測 → 該走 VRN 家族境(via_vrn_312)。
本版:把 v0100 模組裡的 subprocess 換成家族版(argv[0] 為目前解譯器且 argv[1] 為 .py 引擎時,
改用 CGC_MDL157 family_python / child_env 解出的家族境 python);其餘一字照 v0100。只收 VCGC 呼叫。零網路。
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

import importlib.util
import os
import subprocess as _subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def family_of(engine) -> str:
    """引擎路徑 → 家族(vrn / vdf / vap);不在三家族 = core(照目前解譯器)。"""
    p = str(engine).replace("\\", "/")
    for fam in ("VRN", "VDF", "VAP"):
        if f"functional modules/{fam}/" in p:
            return fam.lower()
    return "core"


_UEC = None


def family_python(engine) -> tuple:
    """(python, 來源, env):走 CGC_MDL157 唯一入口的 family_python / child_env(env 明給 > 匯流排 > 目前解譯器)。"""
    global _UEC
    fam = family_of(engine)
    if fam == "core":
        return sys.executable, "core:目前解譯器", None
    try:
        if _UEC is None:
            _UEC = _load(sorted(HERE.glob("CGC_MDL157_VIAUniqueEntryControl_v*.py"))[-1], "CGC_MDL157_for_" + Path(__file__).stem)
        py, src = _UEC.family_python(fam)
        return py, src, _UEC.child_env(fam)
    except Exception as exc:                      # 入口模組缺 = 照實退回目前解譯器,不假裝有家族境
        return sys.executable, f"退路:{type(exc).__name__}", None


def _no_direct_sysexe(path) -> bool:
    """AST:沒有 subprocess.run([sys.executable, …]) / _subprocess.run([sys.executable, …]) 這種直派(全景 SYSEXE 同法)。"""
    import ast as _ast
    tree = _ast.parse(Path(path).read_text(encoding="utf-8"))
    for n in _ast.walk(tree):
        if (isinstance(n, _ast.Call) and isinstance(n.func, _ast.Attribute) and n.func.attr in ("run", "Popen", "call", "check_output")
                and isinstance(n.func.value, _ast.Name) and n.func.value.id in ("subprocess", "_subprocess") and n.args
                and isinstance(n.args[0], _ast.List) and n.args[0].elts and isinstance(n.args[0].elts[0], _ast.Attribute)
                and n.args[0].elts[0].attr == "executable"):
            return False
    return True


ROUTED: list = []


def family_run(argv, **kw):
    """subprocess.run 的家族版:argv[0] 是目前解譯器、argv[1] 是 .py 引擎 → 換成該引擎家族境的 python。"""
    a = list(argv)
    if len(a) >= 2 and a[0] == sys.executable and str(a[1]).endswith(".py"):
        py, src, env = family_python(a[1])
        a[0] = py
        if env is not None and "env" not in kw:
            kw["env"] = env
        ROUTED.append({"engine": Path(str(a[1])).name, "python": py, "source": src})
    return _subprocess.run(a, **kw)


PRIOR = _load(HERE / "CGC_MDL244_VrnLogicAdd_v0100.py", "CGC_MDL244_VrnLogicAdd_v0100_for_v0101")


class _FamilySubprocess:
    """v0100 只用到 subprocess.run;其餘屬性照原模組。"""
    run = staticmethod(family_run)

    def __getattr__(self, name):
        return getattr(_subprocess, name)


PRIOR.subprocess = _FamilySubprocess()


def __getattr__(name: str):
    return getattr(PRIOR, name)


def selftest() -> int:
    rc = PRIOR.selftest()
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {note}" if note and not cond else ""))

    chk("① 前版自測照過(check 經家族路由)", rc == 0)
    r = [x for x in ROUTED if x["engine"] == PRIOR.ENGINE.name]
    chk("② VRN 引擎自測改走家族境 python(不是目前解譯器,除非照實退路)",
        r and (r[-1]["python"] != sys.executable or r[-1]["source"].startswith(("退路", "sys.executable"))), r[-1:] if r else "沒派")
    chk("③ 家族判定:VRN / VDF / VAP / core", family_of("functional modules/VRN/x.py") == "vrn" and family_of("functional modules/VDF/e/x.py") == "vdf"
        and family_of("supportive modules/registry/x.py") == "core")
    src = Path(__file__).read_text(encoding="utf-8")
    chk("④ 加速器橋在 · 本檔沒有 subprocess 以 sys.executable 直派(AST)", "[VIA:ACCEL-BRIDGE:v0100]" in src and _no_direct_sysexe(__file__))
    passed = all(ok)
    print(f"[計] CGC_MDL244_VrnLogicAdd v0101 本版 {sum(ok)}/{len(ok)} · 家族境 {r[-1]['python'] if r else '-'} · {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


def main() -> int:
    return PRIOR.main()


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
