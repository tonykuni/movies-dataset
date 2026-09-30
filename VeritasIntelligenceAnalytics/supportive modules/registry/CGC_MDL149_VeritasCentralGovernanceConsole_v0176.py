"""VCGC v0176 — recognize both canonical thin-module declaration styles.

The existing v0174 registry writer and v0172 AST inventory remain authoritative.
STEM and _STEM wrappers both forward their predecessor definitions; only missing
inherited definitions are added. No extraction, consent, workflow execution,
number allocator or successful source lock is replaced. Help retains v0175's
SSOT-driven capabilities and displays this active version. Exact command dispatch
keeps nested --selftest arguments attached to the requested child engine.
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
_STEM = "CGC_MDL149_VeritasCentralGovernanceConsole"


def _vnum(path):
    found = re.search(r"_v(\d+)$", Path(path).stem)
    return int(found.group(1)) if found else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py")
                  if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
_ORIGINAL_CATALOG = PRIOR.help_catalog


def is_thin(stem, source):
    return "exec_module" in source and bool(
        re.search(re.escape(stem) + r"(?:_v\d{3,4}\.py|_v\*|['\"]\s*\+)", source)
        or re.search(r"(?m)^\s*_?STEM\s*=\s*['\"]" + re.escape(stem) + r"['\"]", source))


for _module in PRIOR._chain_mods():
    if "is_thin" in vars(_module):
        _module.is_thin = is_thin


def help_catalog():
    card = _ORIGINAL_CATALOG()
    card.update(entry=Path(__file__).name, previous=PRIOR_PATH.name)
    return card


PRIOR.help_catalog = help_catalog


def __getattr__(name):
    return getattr(PRIOR, name)


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        return PRIOR.main(args)
    return PRIOR.main(args)


def entrypoint(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    return selftest() if args == ["--selftest"] else main(args)


def selftest():
    import tempfile
    from unittest.mock import Mock, patch
    failures = 0

    def check(name, ok):
        nonlocal failures
        failures += not ok
        print(("[OK] " if ok else "[FAIL] ") + name)

    check("STEM 薄尾", is_thin("Demo", 'STEM = "Demo"\nloader.exec_module(mod)'))
    check("_STEM 舊格式", is_thin("Demo", '_STEM = "Demo"\nloader.exec_module(mod)'))
    check("其他家族不誤認", not is_thin("Demo", 'STEM = "Other"\nloader.exec_module(mod)'))
    check("不是載入器不誤認", not is_thin("Demo", 'STEM = "Demo"'))
    check("非全域 STEM 名稱不誤認", not is_thin("Demo", 'OTHER_STEM = "Demo"\nloader.exec_module(mod)'))
    with tempfile.TemporaryDirectory(prefix="vcgc_thin_inventory_") as tmp:
        root = Path(tmp)
        (root / "Demo_v0100.py").write_text("class Reader:\n    def read(self): pass\n", encoding="utf-8")
        (root / "Demo_v0101.py").write_text('STEM = "Demo"\nloader.exec_module(mod)\ndef collect(): pass\n', encoding="utf-8")
        tail = root / "Demo_v0102.py"
        tail.write_text('_STEM = "Demo"\nloader.exec_module(mod)\n', encoding="utf-8")
        reader = PRIOR.forwarded_defs
        with patch.dict(reader.__globals__, {"VIA": root}):
            found = reader([("Demo", tail)])
        check("兩層薄尾的 class、方法與函數完整盤點",
              {"class|Demo:Reader", "function|Demo:Reader.read", "function|Demo:collect"} <= set(found))
    check("目前說明頁版本", help_catalog()["entry"] == Path(__file__).name)
    delegated, own = Mock(return_value=17), Mock(return_value=19)
    with patch.dict(globals(), {"main": delegated, "selftest": own}):
        nested = entrypoint(["run", "VDF_SystemManager", "--selftest"])
        child_args = delegated.call_args.args[0]
        layout = entrypoint(["layout", "--selftest"])
        layout_args = delegated.call_args.args[0]
        central = entrypoint(["--selftest"])
    check("子引擎自測不被中央入口攔截", nested == 17 and child_args == ["run", "VDF_SystemManager", "--selftest"])
    check("Layout 自測參數送回原路由", layout == 17 and layout_args == ["layout", "--selftest"])
    check("只有獨立 --selftest 執行中央自測", central == 19 and own.call_count == 1)
    inherited = PRIOR.selftest()
    failures += bool(inherited)
    print("[薄尾補強] 10 checks; inherited selftest rc=" + str(inherited) + "; fail=" + str(failures))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(entrypoint())
