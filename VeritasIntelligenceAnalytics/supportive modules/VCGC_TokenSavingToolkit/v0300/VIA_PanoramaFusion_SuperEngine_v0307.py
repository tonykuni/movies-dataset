#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VIA_PanoramaFusion_SuperEngine v0307 — 薄尾(v0300–v0306 一字不動):第六輪(PR #782 Codex P2)產生的 FNC 調度器載得到同層模組

v0300 產生的 VIA_FNC_LIB(FACADE_SOURCE 範本)裡的 trigger() 直接 import 目標模組,沒做 contract_worker 做的路徑設定
  (候選根 + 目標模組所在夾放進 sys.path);巢狀夾裡 `import helper` 這種同層匯入,契約照過、正式從調度器呼叫卻 ModuleNotFoundError。
本版只換 FACADE_SOURCE 範本的 trigger():import 前把調度器所在的根與目標模組所在夾放進 sys.path(同 contract_worker),
  其餘一字不動(仍核對模組來源路徑、仍先 bind 參數)。fusion 寫出調度器時讀的是 v0300 模組全域的 FACADE_SOURCE,所以換範本即生效。
文件與 toolkit.index 改指 v0307。其餘照 v0306 → v0300。自測零網路 · 暫存夾 · 不碰 TA-Lib · 不設同意閘。
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

VERSION = "v0307"
STEM = "VIA_PanoramaFusion_SuperEngine"
TAG = f"{STEM} {VERSION}"
HERE = Path(__file__).resolve().parent


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)                 # v0306
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V300 = PRIOR.V300


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


OLD_LINE = '    target=REGISTRY["actions"][action];path=Path(__file__).parent/target["path"]\n'
NEW_LINES = (OLD_LINE
             + '    for _via_dir in (str(Path(__file__).resolve().parent),str(path.resolve().parent)):\n'
             + '        if _via_dir not in sys.path:sys.path.insert(0,_via_dir)\n')
_ORIG = {k: getattr(V300, k) for k in ("FACADE_SOURCE", "ENGINE_FILE", "__file__")}
if _ORIG["FACADE_SOURCE"].count(OLD_LINE) != 1:
    raise RuntimeError("FACADE_TEMPLATE_DRIFT")                # v0300 範本變了就不猜,照實停


def install() -> None:
    V300.FACADE_SOURCE = _ORIG["FACADE_SOURCE"].replace(OLD_LINE, NEW_LINES, 1)
    V300.ENGINE_FILE = Path(__file__).name
    V300.__file__ = str(Path(__file__).resolve())


def uninstall() -> None:
    for k, v in _ORIG.items():
        setattr(V300, k, v)


install()


def facade_call(facade_source: str) -> subprocess.CompletedProcess:
    """暫存候選根:放產生的調度器 + 註冊冊 + 橋 stub + 巢狀模組(同層 import helper),從調度器呼叫。"""
    td = tempfile.mkdtemp(prefix="pf307_")
    root = Path(td)
    (root / V300.BRIDGE_FILE).write_text("def accel_env():\n    return {}\n", encoding="utf-8")
    (root / "VIA_FNC_LIB_v0300.py").write_text(facade_source, encoding="utf-8")
    (root / "VIA_FNC_REGISTRY_v0300.json").write_text(json.dumps({"actions": {"act": {"path": "nested/action.py", "symbol": "run"}}}), encoding="utf-8")
    (root / "nested").mkdir()
    (root / "nested" / "helper.py").write_text("def plus(x):\n    return x + 1\n", encoding="utf-8")
    (root / "nested" / "action.py").write_text("import helper\n\n\ndef run(x):\n    return helper.plus(x)\n", encoding="utf-8")
    code = f"import sys;sys.path.insert(0,{str(root)!r});import VIA_FNC_LIB_v0300 as F;print(F.trigger('act',[41]))"
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
    old, new = facade_call(_ORIG["FACADE_SOURCE"]), facade_call(V300.FACADE_SOURCE)
    chk("T2 (P2)從產生的調度器呼叫巢狀模組(它 import 同層 helper):前版 ModuleNotFoundError;本版回 42",
        old.returncode != 0 and "ModuleNotFoundError" in old.stderr and new.returncode == 0 and new.stdout.strip() == "42",
        (old.returncode, old.stderr[-160:], new.returncode, new.stdout, new.stderr[-160:]))
    diff = [ln for ln in V300.FACADE_SOURCE.splitlines() if ln not in _ORIG["FACADE_SOURCE"].splitlines()]
    chk("T3 範本只多兩行路徑設定,其餘(來源路徑核對 · 先 bind 參數)原樣", len(diff) == 2 and all("_via_dir" in ln for ln in diff)
        and 'raise ImportError("module origin mismatch")' in V300.FACADE_SOURCE, diff)
    chk("T4 綁定 / 子行程指本檔", V300.ENGINE_FILE == Path(__file__).name and Path(V300.__file__).resolve() == Path(__file__).resolve())
    uninstall()
    try:
        rc = PRIOR.selftest()
    finally:
        install()
    chk("T5 前版 v0306 自測照過(含文件指家族最新尾版的檢查 · v0305 → v0300 原有 107 項)", rc == 0, rc)
    print(f"[計] {TAG} 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(a)


if __name__ == "__main__":
    raise SystemExit(main())
