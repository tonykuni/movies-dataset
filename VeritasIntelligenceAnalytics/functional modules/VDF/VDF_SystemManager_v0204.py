#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF SystemManager v0204 — 薄尾(v0203 以前一字不動):前版鏈自測期間中央啟動鉤也要保持關閉(PR #777 Codex P2)

v0203 跑前版 v0202 自測時,把 v0202 自己的 isolate(不設 VIA_BOOT=0)換回去;在操作員 PS 視窗直接下 --selftest
  (PYTHONPATH 掛著 bootstrap、沒設 VIA_BOOT)時,v0202 的 T4 子行程被 sitecustomize.py 補回入口標記 → T4 紅 → v0203 T5 紅。
  容器用倉裡真的 bootstrap 重現(PYTHONPATH=bootstrap)。vv 裡不發作,因為 vv 本身就在 VIA_BOOT=0 下起本自測。
本版:跑前版鏈自測的期間,本行程環境暫時設 VIA_BOOT=0(子行程繼承 → 鉤不跑),結束原樣還原(原本沒設就拿掉)。其餘照 v0203。
零網路 · 不碰 TA-Lib · 不設同意閘 · 不 import VCGC。
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
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

VERSION = "v0204"
STEM = "VDF_SystemManager"
TAG = f"VDF_SystemManager {VERSION}"
HERE = Path(__file__).resolve().parent


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)                 # v0203
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


class boot_off:
    """期間內 os.environ['VIA_BOOT']='0',離開時還原(原本沒設就拿掉)。"""
    def __enter__(self):
        self.had, self.old = "VIA_BOOT" in os.environ, os.environ.get("VIA_BOOT")
        os.environ["VIA_BOOT"] = "0"
        return self

    def __exit__(self, *exc):
        if self.had:
            os.environ["VIA_BOOT"] = self.old
        else:
            os.environ.pop("VIA_BOOT", None)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:240]) if note and not cond else ""), flush=True)

    print(f"[計] {TAG} 自測開始(本版 3 項 + 前版 {PRIOR_PATH.name} 自測(中央鉤關著)· 零網路)", flush=True)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T1 加速器真的載到 · 第 3 行標記 · 網路橋在", VIA_ACCEL is not None and src.splitlines()[2] == "# [VIA:ACCEL-BRIDGE:v0111]"
        and VIA_NET_TOOL_PATH is not None)
    keep = os.environ.pop("VIA_BOOT", None)
    with boot_off():
        inside = os.environ.get("VIA_BOOT")
    after = os.environ.get("VIA_BOOT")
    os.environ["VIA_BOOT"] = "7"
    with boot_off():
        pass
    after2 = os.environ.get("VIA_BOOT")
    if keep is None:
        os.environ.pop("VIA_BOOT", None)
    else:
        os.environ["VIA_BOOT"] = keep
    chk("T2 期間內 VIA_BOOT=0 · 原本沒設 → 結束拿掉 · 原本有值 → 原樣還原", inside == "0" and after is None and after2 == "7", (inside, after, after2))
    hook = PRIOR.V202.V194._p("sm_via_root")() / "supportive modules" / "bootstrap"
    probe = "import os;print(os.environ.get('VIA_ENTRY_CONTROL','-'))"
    base = {k: v for k, v in os.environ.items() if k not in PRIOR.HOOK_KEYS and k != "VIA_BOOT"}
    with tempfile.TemporaryDirectory(prefix="vdf_sm204_") as td, boot_off():
        child = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True, timeout=120, cwd=td,
                               env={**base, "VIA_BOOT": os.environ["VIA_BOOT"], "PYTHONPATH": str(hook)}).stdout.strip()
    chk("T3 鉤關著時,掛著真的 bootstrap 起子行程也看不到入口標記(Codex 重現情境)", child == "-", child)
    with boot_off():
        rc = PRIOR.selftest() if callable(getattr(PRIOR, "selftest", None)) else 1
    chk("T4 前版 v0203 自測照過(含 v0202;PYTHONPATH 掛著中央鉤也照過)", rc == 0, rc)
    print(f"[計] {TAG} 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(a)


if __name__ == "__main__":
    raise SystemExit(main())
