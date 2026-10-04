#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL011_AkshareFetcher v0101 — 薄尾:參數矩陣在註冊表還沒建立時誠實回 NODATA(rc 2),不再 KeyError

容器裝上 akshare 1.19.1 後(操作員 2026-10-04「開閘授權一切」),MDL008 整合測試的 block 自測 `params` 從 ABSENT(rc 3)
變成 rc 1:新輸出根沒有 vake_registry.json,load_registry 回空殼 {"registry": {}, "tree": {}, "stats": {}},
params_report 讀 reg['generated_at'] → KeyError。本版只接手 cmd_params:註冊表沒有 generated_at = 還沒 scan
→ 印 NODATA 與下一步(scan),rc 2;有註冊表照 v0100 原樣出矩陣。其餘(scan · fetch · schedule-run · views ·
compact · universe)全部照 v0100(原件逐位元不動)。不碰 TA-Lib;不讀寫同意閘。
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
_STEM = "VDF_MDL011_AkshareFetcher"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def _vnum_v0101(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0101(p) < _vnum_v0101(__file__)), key=_vnum_v0101)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR                        # 原件以 sys.modules[__name__] 自我引用(C = K = … = 本模組)
_spec.loader.exec_module(PRIOR)
_CMD_PARAMS_V0100 = PRIOR.cmd_params


def __getattr__(name):
    return getattr(PRIOR, name)


def cmd_params_v0101(a):
    """註冊表沒有 generated_at(還沒 scan)→ NODATA rc 2;有就照 v0100。"""
    reg = PRIOR.load_registry()
    if not isinstance(reg, dict) or not reg.get("generated_at") or not isinstance(reg.get("stats"), dict):
        print(f"[{TAG}] NODATA:vake_registry.json 還沒建立({PRIOR.REGISTRY_JSON})—— 參數矩陣不出假表;先跑 scan", flush=True)
        return 2
    return _CMD_PARAMS_V0100(a)


PRIOR.cmd_params = cmd_params_v0101                    # v0100 main 從自己的 globals 找 cmd_params


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    return PRIOR.main(args)


def selftest() -> int:
    import contextlib
    import io
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {TAG} · 薄尾自測(params 無註冊表 = NODATA)===")
    keep_load, keep_rep = PRIOR.load_registry, PRIOR.params_report
    seen = []
    try:
        PRIOR.load_registry = lambda: {"registry": {}, "tree": {}, "stats": {}}
        PRIOR.params_report = lambda reg: seen.append(reg) or "never"
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc_empty = PRIOR.main(["params"])
        chk("① 空註冊表(還沒 scan)→ rc 2 · NODATA 一行 · 不呼叫 params_report(不出假表)",
            rc_empty == 2 and "NODATA" in buf.getvalue() and not seen, (rc_empty, buf.getvalue().strip()[:80]))
        reg = {"generated_at": "2026-10-04T00:00:00+00:00", "registry": {}, "tree": {}, "stats": {"total": 0}}
        PRIOR.load_registry = lambda: reg
        PRIOR.params_report = lambda r: seen.append(r) or "matrix.html"
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc_full = PRIOR.main(["params"])
        chk("② 有註冊表 → 照 v0100 cmd_params(params_report 被呼叫 · rc 0 · JSON 一行)",
            rc_full == 0 and seen == [reg] and '"matrix": "matrix.html"' in buf.getvalue(), rc_full)
    finally:
        PRIOR.load_registry, PRIOR.params_report = keep_load, keep_rep
    chk("③ 其餘動詞照 v0100(main 同一支 · 只換 cmd_params)", PRIOR.cmd_params is cmd_params_v0101 and callable(PRIOR.cmd_scan))
    import ast
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    names = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
    chk("④ L103:模組層加速器橋 + 網路工具橋(def _via_net)AST 真橋", "_via_net" in names and "VIA_ACCEL" in Path(__file__).read_text(encoding="utf-8"))
    n = sum(ok)
    print(f"  [計] {TAG} 本版 {n}/{len(ok)} · 合計 {'PASS' if n == len(ok) else 'FAIL'}")
    return 0 if n == len(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
