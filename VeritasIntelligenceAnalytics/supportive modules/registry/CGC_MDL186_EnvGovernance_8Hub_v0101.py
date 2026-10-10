#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL186_EnvGovernance_8Hub v0101 — thin tail: _apply_green passes bootstrap_prechecked only when MDL135 still accepts it.

MDL135 tools_apply had a bootstrap_prechecked keyword only in v0114; v0116 and v0117 dropped it, so
`via-envgov eight-hub --execute` raised TypeError at the install step (found 2026-10-10 while mapping the
VCGC install lane for the docs tools). This tail checks the live signature: keyword accepted -> same call as v0100;
not accepted -> call without it (MDL135 then applies its own uv precheck, so nothing is skipped). Everything else is v0100.
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
import inspect
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL186_EnvGovernance_8Hub"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_v0101", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
for _k, _v in vars(PRIOR).items():
    if not _k.startswith("__") and _k not in globals():
        globals()[_k] = _v


def __getattr__(name):
    return getattr(PRIOR, name)


def _accepts(fn, kw: str) -> bool:
    try:
        ps = inspect.signature(fn).parameters
    except (TypeError, ValueError):
        return False
    return kw in ps or any(p.kind == p.VAR_KEYWORD for p in ps.values())


def _apply_green(core, rows, dry, plan, bootstrap_prechecked: bool = False) -> dict:
    allowed = {r["env"] for r in rows if r["state"] == "PASS"}
    allowed.intersection_update(d["env"] for d in dry if d["state"] == "PASS")
    stages = [dict(s) for s in plan.get("stages", []) if s["env"] in allowed and s["kind"] in ("INSTALL_TOOLS", "VERIFY_TOOLS")]
    ids = {s["id"] for s in stages}
    stages = [s for s in stages if all(d in ids for d in s.get("deps", []))]
    filtered = {"stages": stages, "state": "PLAN"}
    if _accepts(core.tools_apply, "bootstrap_prechecked"):
        summary = core.tools_apply(filtered, approve=True, bootstrap_prechecked=bootstrap_prechecked)
    else:
        summary = core.tools_apply(filtered, approve=True)
    return {"summary": summary, "stages": stages, "state": filtered["state"]}


PRIOR._apply_green = _apply_green          # v0100 run/execute paths call the module global


def selftest() -> int:
    ok = []

    def chk(name, cond):
        ok.append(bool(cond))
        print("  [%s] %s" % ("OK" if cond else "FAIL", name))

    seen = {}

    class NewCore:
        @staticmethod
        def tools_apply(plan, approve, ensure_env=False):
            seen["new"] = (len(plan["stages"]), approve)
            return {"ran": len(plan["stages"])}

    class OldCore:
        @staticmethod
        def tools_apply(plan, approve, ensure_env=False, bootstrap_prechecked=False):
            seen["old"] = bootstrap_prechecked
            return {"ran": len(plan["stages"])}

    rows = [{"env": "a", "state": "PASS"}, {"env": "b", "state": "FAIL"}]
    dry = [{"env": "a", "state": "PASS"}, {"env": "b", "state": "PASS"}]
    plan = {"stages": [{"id": "T1", "env": "a", "kind": "INSTALL_TOOLS"}, {"id": "T2", "env": "b", "kind": "INSTALL_TOOLS"},
                       {"id": "T3", "env": "a", "kind": "REPAIR_TOOLS"}]}
    r1 = _apply_green(NewCore, rows, dry, plan, bootstrap_prechecked=True)
    chk("① MDL135 v0116+ (no keyword): no TypeError · only PASS env INSTALL stage · no repair", seen.get("new") == (1, True) and r1["summary"]["ran"] == 1)
    _apply_green(OldCore, rows, dry, plan, bootstrap_prechecked=True)
    chk("② MDL135 v0114 (keyword): passed through unchanged", seen.get("old") is True)
    chk("③ v0100 module global replaced (run/execute use the tail)", PRIOR._apply_green is _apply_green)
    print("  -- v0100 selftest --")
    prc = PRIOR.selftest() if hasattr(PRIOR, "selftest") else 0
    chk("④ v0100 selftest rc 0", prc == 0)
    print("[計] CGC_MDL186_EnvGovernance_8Hub_v0101 %d/%d · %s" % (sum(ok), len(ok), "PASS" if all(ok) else "FAIL"))
    return 0 if all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else (PRIOR.main() if hasattr(PRIOR, "main") else 0))
