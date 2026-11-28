#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF_MDL013_ActivateVDF v0122 — 薄尾(v0100–v0121 一字不動):「指揮行程沒排隊」的門檻 0.2 秒太緊

2026-11-28 主機 diag:v0120 / v0121 T2「boss=True · argv 認得出 · 沒排隊(wait_s ≤ 0.2 秒)」不過 ——
  收據 boss=True、argv 對,但負載高的主機上,鉤子量到的 wait_s 有零點幾秒(不是排隊,是起動時間)。
  真的排隊的(引擎自測)在同一個夾具裡要等滿 ADMIT 上限 1.2 秒才放行(v0118 ④ 斷言 ≥ 1.0)。
本版:門檻改 0.9 秒(< 排隊的下限 1.0,仍分得出「排隊」與「沒排隊」);判法掛在 v0120 模組層。其餘照 v0121。
零網路 · 不碰 TA-Lib · 不設同意閘 · 不裝套件。
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
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "VDF_MDL013_ActivateVDF"
TAG = "VDF_MDL013_ActivateVDF v0122"
BOSS_WAIT_MAX = 0.9


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(STEM + "_prior_for_v0122", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)                 # v0121
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V0120 = PRIOR.PRIOR


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


V0120.BOSS_WAIT_MAX = BOSS_WAIT_MAX                            # v0120 boss_ok 讀模組層門檻


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:240]) if note and not cond else ""), flush=True)

    print(f"[計] {TAG} 自測開始(本版 3 項 + 前版 {PRIOR_PATH.name} 自測 · 零網路)", flush=True)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T1 加速器真的載到(VIA_ACCEL is not None)· 第 3 行標記 · 網路橋在 __future__ 之下",
        VIA_ACCEL is not None and src.splitlines()[2] == "# [VIA:ACCEL-BRIDGE:v0111]" and VIA_NET_TOOL_PATH is not None)
    base = {"boss": True, "argv": "VDF_SystemManager_v9999.py engine list"}
    chk("T2 門檻:起動花 0.3 / 0.85 秒 → 算沒排隊;等滿 1.0 秒以上(排隊)→ 不過;沒認出指揮行程 → 不過",
        V0120.boss_ok({**base, "wait_s": 0.3}) and V0120.boss_ok({**base, "wait_s": 0.85}) and not V0120.boss_ok({**base, "wait_s": 1.0})
        and not V0120.boss_ok({**base, "boss": False, "wait_s": 0}))
    rc = PRIOR.selftest() if callable(getattr(PRIOR, "selftest", None)) else 1
    chk("T3 前版 v0121 自測照過(含 v0120 · 新門檻)", rc == 0, rc)
    print(f"[計] {TAG} 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--selftest"]:
        return selftest()
    return PRIOR.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
