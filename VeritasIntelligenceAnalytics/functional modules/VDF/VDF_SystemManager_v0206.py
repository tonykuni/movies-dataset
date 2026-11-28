#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF SystemManager v0206 — 薄尾(v0205 以前一字不動):重複副本也要過「目的地不在 OneDrive」那道關(PR #777 Codex P2)

v0205 把「與保留那份逐檔相同」的副本改成 ok=True 時,蓋掉了 v0198 另外判的「目的地在 OneDrive 裡 → 拒絕」;
  隔離區(VIA_TIDY_QUARANTINE)設在 OneDrive 裡時,apply_plan 會真的把副本搬進 OneDrive(容器夾具重現)。
  主機預設隔離區在 %LOCALAPPDATA%(不在 OneDrive),所以這次主機計畫不受影響;但兩道關要各自成立。
本版:組完計畫後,temp / backup 每一項只要目的地在 OneDrive 裡,一律改回不搬並寫明(內容證明不能抵銷目的地檢查)。其餘照 v0205。
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
import sys
import tempfile
import time
from pathlib import Path

VERSION = "v0206"
STEM = "VDF_SystemManager"
TAG = f"VDF_SystemManager {VERSION}"
HERE = Path(__file__).resolve().parent
VETO = "目的地在 OneDrive 裡 → 拒絕"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)                 # v0205
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


V198 = PRIOR.V198
_ORIG_BUILD = V198.build_plan                                  # = v0205 的 build_plan


def build_plan(home: Path, via: Path, code_dir: Path, tails_text: str, stamp: str) -> dict:
    plan = _ORIG_BUILD(home, via, code_dir, tails_text, stamp)
    for i in plan["items"]:
        if i["cat"] in ("temp", "backup") and V198.in_onedrive(Path(i["dst"])):
            i["ok"] = False
            if VETO not in i["note"]:
                i["note"] = (VETO + " · " + i["note"]).rstrip(" ·")
    return plan


V198.build_plan = build_plan


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:240]) if note and not cond else ""), flush=True)

    print(f"[計] {TAG} 自測開始(本版 3 項 + 前版 {PRIOR_PATH.name} 自測 · 暫存夾 · 零網路)", flush=True)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T1 加速器真的載到 · 第 3 行標記 · 網路橋在", VIA_ACCEL is not None and src.splitlines()[2] == "# [VIA:ACCEL-BRIDGE:v0111]"
        and VIA_NET_TOOL_PATH is not None)
    with tempfile.TemporaryDirectory(prefix="vdf_sm206_") as td:
        d = Path(td)
        home, via = d / "home", d / "via"
        code = via / "functional modules" / "VDF"
        code.mkdir(parents=True)
        base = home / "temp" / "VDF_Manager_v0104"
        t0 = time.time() - 86400
        for n, name in enumerate(("setup_a", "setup_b")):
            p = base / name / "via_01_vdf"
            p.mkdir(parents=True)
            (p / "only_here.py").write_text("y = 2\n", encoding="utf-8")
            for f in p.iterdir():
                os.utime(f, (t0 + n * 60, t0 + n * 60))
        keep = os.environ.get("VIA_TIDY_QUARANTINE")
        os.environ["VIA_TIDY_QUARANTINE"] = str(d / "OneDrive" / "VIA_quarantine")
        try:
            plan = V198.build_plan(home, via, code, "", "T206")
            r = V198.apply_plan(plan, {"temp"}, d / "L.jsonl")
            os.environ["VIA_TIDY_QUARANTINE"] = str(d / "local" / "VIA_quarantine")
            plan2 = V198.build_plan(home, via, code, "", "T206b")
        finally:
            if keep is None:
                os.environ.pop("VIA_TIDY_QUARANTINE", None)
            else:
                os.environ["VIA_TIDY_QUARANTINE"] = keep
        it = [i for i in plan["items"] if i["cat"] == "temp"]
        it2 = [i for i in plan2["items"] if i["cat"] == "temp"]
    chk("T2 (Codex P2)隔離區在 OneDrive 裡:重複副本照樣拒絕 · 寫明原因 · apply 零搬移",
        len(it) == 1 and not it[0]["ok"] and VETO in it[0]["note"] and not r["moved"], (it, r))
    chk("T3 隔離區不在 OneDrive:同一份重複副本照 v0205 可搬", len(it2) == 1 and it2[0]["ok"] and "重複副本" in it2[0]["note"], it2)
    V198.build_plan = _ORIG_BUILD                              # 前版自測看它自己的判法
    try:
        rc = PRIOR.selftest() if callable(getattr(PRIOR, "selftest", None)) else 1
    finally:
        V198.build_plan = build_plan
    chk("T4 前版 v0205 自測照過(含整條前版鏈)", rc == 0, rc)
    print(f"[計] {TAG} 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(a)


if __name__ == "__main__":
    raise SystemExit(main())
