#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF SystemManager v0187 — 薄尾(v0186 一字不動):短指令動詞 yf-global → VDF 自己的安全並行啟動器。

操作員 2026-11-20:「給我一個快但安全的擷取指令用 PY 寫用短指令啟動」。
  via-vdf yf-global          = py VDF_MDL022_SafeParallelLaunch 尾版 yf-global(先全面檢查 → 降壓 → 3~5 道 → 合併 → 覆蓋)
  yf-global [參數…]          參數原樣轉交(--slots · --start · --data-home · --dry · --force …;見啟動器說明)
其餘動詞一律交給 v0186(參數 / rc 不變;只增不減)。不設同意閘、不安裝、本檔不出網;子行程照前版的子行程環境
(v0186 child_env:VIA_NO_OPEN=1;VDF 是獨立系統,不多設 VIA_FROM_VCGC 等他系統入口旗標)。
自測:python VDF_SystemManager_v0187.py --selftest
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。本版兩扇門都不出網。"""
    return None if VIA_NET_TOOL_PATH is None else VIA_NET_TOOL_PATH
# ===== [VIA:NET-BRIDGE:END] =====
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAG = "v0187"
SYSTEM = "VDF"
FAMILY = "VDF_SystemManager"
LAUNCH_FAMILY = "VDF_MDL022_SafeParallelLaunch"


def _vnum(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load(path: Path, name: str):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
PRIOR = _load(PRIOR_PATH, "vdf_manager_prior_for_" + TAG)


def __getattr__(name):
    """尾版律 TAILAPI:前版公開名稱經本檔轉接。"""
    return getattr(PRIOR, name)


def launcher() -> Path:
    hits = [p for p in HERE.glob(LAUNCH_FAMILY + "_v*.py") if _vnum(p) >= 0]
    return max(hits, key=_vnum)


PEER_FLAGS = ("VIA_FROM_VCGC", "VIA_FROM_VDFSM", "VIA_FROM_VRN", "VIA_VCGC_PUSH")   # 他系統入口旗標:子行程不多設(同 v0186 自測 ⑦)


def child_env() -> dict:
    """子行程環境沿用前版鏈:v0186 child_env(VIA_NO_OPEN=1 · 只補本系統自己的入口旗標)> sm_child_env > 原環境。"""
    import os
    for name in ("child_env", "sm_child_env"):
        fn = getattr(PRIOR, name, None)
        if callable(fn):
            return fn()
    return dict(os.environ)


def added_peer_flags(env: dict) -> list:
    import os
    own = (getattr(PRIOR, "SM_CONFIG", None) or {}).get("own_entry_flag")
    return [k for k in PEER_FLAGS if k in env and k not in os.environ and k != own]


def yf_global(args: list, run=subprocess.run) -> int:
    lp = launcher()
    print(f"  ===== [VDF SystemManager {TAG}] yf-global → {lp.name}(VDF 自己的啟動器)=====", flush=True)
    return run([sys.executable, "-B", str(lp), "yf-global", *args], env=child_env(), cwd=str(HERE)).returncode


def help_extra() -> None:
    print("  ── %s yf-global(全球指數與商品自 2018 起 · 先全面檢查 → 降壓 → 3~5 道 → 合併 → 覆蓋)──" % TAG)
    print("  yf-global [--slots auto|3|4|5] [--start 2018-01-01] [--data-home <夾>] [--dry] [--force]   → %s 尾版" % LAUNCH_FAMILY)


def selftest() -> int:
    ok = []

    def ck(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:240]) if note and not cond else ''}", flush=True)
    print(f"=== VDF SystemManager {TAG} 自測(本版 + 前版另起行程)===", flush=True)
    seen = {}

    class R:
        returncode = 2

    def fake(cmd, env=None, cwd=None):
        seen.update(cmd=cmd, env=env, cwd=cwd)
        return R()
    rc = yf_global(["--dry", "--slots", "4"], run=fake)
    ck("S1 yf-global 轉給啟動器尾版、參數原樣、rc 原樣", rc == 2 and seen["cmd"][2] == str(launcher()) and seen["cmd"][3:] == ["yf-global", "--dry", "--slots", "4"]
       and launcher().name.startswith(LAUNCH_FAMILY), seen.get("cmd"))
    ck("S2 啟動器取尾版(不釘死版號)", _vnum(launcher()) == max(_vnum(p) for p in HERE.glob(LAUNCH_FAMILY + "_v*.py")))
    ck("S3 子行程環境用前版的(child_env)· 不在本檔寫同意閘", isinstance(seen.get("env"), dict)
       and "_CONSENT\"] " + "=" not in Path(__file__).read_text(encoding="utf-8"))
    text = Path(__file__).read_text(encoding="utf-8")
    ck("S4 檔面:加速器橋 · 網路橋 · 沒有本機路徑", "[VIA:ACCEL-BRIDGE:v0100]" in text and "[VIA:NET-BRIDGE:v0100]" in text and "\\" + "Users" not in text)
    env = child_env()
    ck("S6 yf-global 子行程環境:VIA_NO_OPEN=1 · 不多設他系統入口旗標(VIA_FROM_VCGC 等)", env.get("VIA_NO_OPEN") == "1" and not added_peer_flags(env), added_peer_flags(env))
    pr = subprocess.run([sys.executable, "-B", str(PRIOR_PATH), "--selftest"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    ck(f"S5 前版 {PRIOR_PATH.name} 自測照過(另起行程)", pr.returncode == 0, (pr.stdout or "")[-240:])
    n = sum(ok)
    print(f"[計] VDF SystemManager {TAG} 本版 {n}/{len(ok)} · {'PASS' if n == len(ok) else 'FAIL'}", flush=True)
    return 0 if n == len(ok) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"] or "--selftest" in args[:1]:
        return selftest()
    if args[:1] == ["yf-global"]:
        return yf_global(args[1:])
    rc = PRIOR.main(args)
    if not args or args[:1] == ["help"]:
        help_extra()
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
