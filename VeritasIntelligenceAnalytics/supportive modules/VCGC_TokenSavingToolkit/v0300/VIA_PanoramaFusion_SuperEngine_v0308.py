#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VIA_PanoramaFusion_SuperEngine v0308 — 薄尾(v0300–v0307 一字不動):第七輪(PR #782 Codex P2)同名同層模組不再悄悄拿錯

v0307 讓調度器把目標模組所在夾放進 sys.path,但 sys.modules 是整個行程共用:one/helper.py 先載入後,
  two/action.py 的 `import helper` 會拿到 one 的 helper(Codex 重現 `1 1` 而不是 `1 2`,rc 0,沒人發現)。
本版選擇拒絕模稜兩可(fail-closed):調度器 import 目標前,看目標所在夾的每個同層 .py;若 sys.modules 已有同名模組、
  而且它的檔案不是這一個同層檔 → ImportError("AMBIGUOUS_SIBLING_IMPORT:<名字>"),不呼叫。不會再悄悄回錯的值。
只動 FACADE_SOURCE 範本裡 v0307 加的那兩行之後(再加三行檢查);其餘照 v0307 → v0300。文件與 toolkit.index 改指 v0308。
自測零網路 · 暫存夾 · 不碰 TA-Lib · 不設同意閘。
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
except Exception:  # noqa: BLE001
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
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

VERSION = "v0308"
STEM = "VIA_PanoramaFusion_SuperEngine"
TAG = f"{STEM} {VERSION}"
HERE = Path(__file__).resolve().parent


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)                 # v0307
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V300 = PRIOR.V300


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


ANCHOR = PRIOR.NEW_LINES                                       # v0307 加進範本的那幾行
CHECK = ('    for _via_sib in path.resolve().parent.glob("*.py"):\n'
         '        _via_mod=sys.modules.get(_via_sib.stem)\n'
         '        if _via_mod is not None and getattr(_via_mod,"__file__",None) and Path(_via_mod.__file__).resolve()!=_via_sib.resolve():raise ImportError("AMBIGUOUS_SIBLING_IMPORT:"+_via_sib.stem)\n')
_ORIG = {k: getattr(V300, k) for k in ("FACADE_SOURCE", "ENGINE_FILE", "__file__")}
if _ORIG["FACADE_SOURCE"].count(ANCHOR) != 1:
    raise RuntimeError("FACADE_TEMPLATE_DRIFT")


def install() -> None:
    V300.FACADE_SOURCE = _ORIG["FACADE_SOURCE"].replace(ANCHOR, ANCHOR + CHECK, 1)
    V300.ENGINE_FILE = Path(__file__).name
    V300.__file__ = str(Path(__file__).resolve())


def uninstall() -> None:
    for k, v in _ORIG.items():
        setattr(V300, k, v)


install()


def two_actions(facade_source: str) -> subprocess.CompletedProcess:
    """one/helper 回 1、two/helper 回 2,同一行程依序叫 act1、act2。"""
    root = Path(tempfile.mkdtemp(prefix="pf308_"))
    (root / V300.BRIDGE_FILE).write_text("def accel_env():\n    return {}\n", encoding="utf-8")
    (root / "VIA_FNC_LIB_v0300.py").write_text(facade_source, encoding="utf-8")
    acts = {}
    for d, v in (("one", 1), ("two", 2)):
        (root / d).mkdir()
        (root / d / "helper.py").write_text(f"def val():\n    return {v}\n", encoding="utf-8")
        (root / d / "action.py").write_text("import helper\n\n\ndef run():\n    return helper.val()\n", encoding="utf-8")
        acts["act" + str(v)] = {"path": f"{d}/action.py", "symbol": "run"}
    (root / "VIA_FNC_REGISTRY_v0300.json").write_text(json.dumps({"actions": acts}), encoding="utf-8")
    code = (f"import sys;sys.path.insert(0,{str(root)!r});import VIA_FNC_LIB_v0300 as F\n"
            "out=[F.trigger('act1')]\n"
            "try:\n    out.append(F.trigger('act2'))\nexcept ImportError as e:\n    out.append(str(e))\n"
            "print(out)")
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    return subprocess.run([sys.executable, "-I", "-c", code], cwd=tempfile.gettempdir(), capture_output=True, text=True, env=env, timeout=60)


def selftest() -> int:
    ok = []

    def chk(label, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + label + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print(f"[計] {TAG} 自測開始(本版 4 項 + 前版 {PRIOR_PATH.name} 自測 · 暫存夾 · 零網路)", flush=True)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T1 加速器真的載到 · 第 3 行標記 · 網路工具橋", VIA_ACCEL is not None and src.splitlines()[2] == "# [VIA:ACCEL-BRIDGE:v0111]"
        and VIA_NET_TOOL_PATH is not None)
    old, new = two_actions(_ORIG["FACADE_SOURCE"]), two_actions(V300.FACADE_SOURCE)
    chk("T2 (P2)兩個夾各有自己的 helper,同一行程依序叫:前版悄悄回 [1, 1];本版 [1, 'AMBIGUOUS_SIBLING_IMPORT:helper'](不回錯值)",
        old.stdout.strip() == "[1, 1]" and new.stdout.strip() == "[1, 'AMBIGUOUS_SIBLING_IMPORT:helper']",
        (old.stdout, old.stderr[-120:], new.stdout, new.stderr[-120:]))
    single = PRIOR.facade_call(V300.FACADE_SOURCE)
    chk("T3 單一巢狀模組 import 同層 helper(v0307 的情境)本版照樣回 42", single.returncode == 0 and single.stdout.strip() == "42",
        (single.returncode, single.stderr[-160:]))
    chk("T4 綁定 / 子行程指本檔", V300.ENGINE_FILE == Path(__file__).name and Path(V300.__file__).resolve() == Path(__file__).resolve())
    uninstall()
    try:
        rc = PRIOR.selftest()
    finally:
        install()
    chk("T5 前版 v0307 自測照過(含 v0306 → v0300 原有 107 項)", rc == 0, rc)
    print(f"[計] {TAG} 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(a)


if __name__ == "__main__":
    raise SystemExit(main())
