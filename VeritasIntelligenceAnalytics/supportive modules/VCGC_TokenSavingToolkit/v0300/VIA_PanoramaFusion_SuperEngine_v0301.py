#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VIA_PanoramaFusion_SuperEngine v0301 — 薄尾(v0300 一字不動):補上 VIA 加速器橋與網路工具橋(CLAUDE.md REQ266)

v0300(PR #778 交付的凍結工具)三支 .py 第 3 行沒有 `[VIA:ACCEL-BRIDGE]` 標記,語法樹裡也沒有匯入 VIA_SuperAccel_Module;
  引擎有對外擷取能力(http_json · urllib.request),也沒有經語法樹導入鎖冊上的網路工具。
本版只做這件事:
  · 掛加速器橋(載到 → VIA_ACCEL is not None)與網路工具橋(惰性:import 時零網路,閘照舊由網路工具自己管)。
  · 其餘全部轉給 v0300:`__getattr__` 轉接公開名稱;CLI(含內部工作行程 _contracts / _bridgeprobe)原樣交給 v0300。
  · v0300 用自己的檔名(ENGINE_FILE · VIA_Runtime_Bridge_v0300 · *_v0300.json)產生與讀取檔案,本版不改名、不改行為。
  · `--selftest`:T1 雙橋載到 · T2 前版公開名稱照轉 · T3 跑 v0301 兩支測試(它們各自跑 v0300 原有測試再加載入檢查)。
零網路(自測)· 不碰 TA-Lib · 不設同意閘。
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
import re
import subprocess
import sys
from pathlib import Path

VERSION = "v0301"
STEM = "VIA_PanoramaFusion_SuperEngine"
TAG = f"{STEM} {VERSION}"
HERE = Path(__file__).resolve().parent
TESTS = ("test_panorama_fusion_v0301.py", "test_v0301_workflow.py")


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)                 # v0300
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def run_suite(name: str) -> dict:
    p = HERE / name
    try:
        cp = subprocess.run([sys.executable, "-B", str(p)], cwd=str(HERE), capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=1800, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return {"file": name, "rc": 124, "passed": False, "reason": "TIMEOUT"}
    try:
        v = json.loads(cp.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        v = {"passed": False, "reason": "NON_JSON_TEST_RESULT", "tail": (cp.stdout + cp.stderr)[-300:]}
    return {"file": name, "rc": cp.returncode, **v}


def selftest() -> int:
    ok = []

    def chk(label, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + label + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print(f"[計] {TAG} 自測開始(本版 3 項 · 前版 {PRIOR_PATH.name} 的測試由 v0301 兩支測試在子行程實跑)", flush=True)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T1 加速器真的載到(VIA_ACCEL is not None)· 第 3 行標記 · 網路工具橋找到鎖冊工具",
        VIA_ACCEL is not None and src.splitlines()[2] == "# [VIA:ACCEL-BRIDGE:v0111]" and VIA_NET_TOOL_PATH is not None,
        (VIA_ACCEL, VIA_NET_TOOL_PATH))
    chk("T2 前版公開名稱照轉(VERSION · main · selftest · http_json)",
        PRIOR.VERSION == "v0300" and all(callable(getattr(PRIOR, n, None)) for n in ("main", "selftest", "http_json")))
    suites = [run_suite(n) for n in TESTS]
    chk("T3 v0301 兩支測試都過(各含 v0300 原有測試 + 本版載入檢查)",
        all(s.get("passed") and s.get("rc") == 0 for s in suites),
        [(s["file"], s.get("rc"), s.get("tests"), s.get("reason")) for s in suites])
    for s in suites:
        print(f"  [計] {s['file']} · tests {s.get('tests')} · prior {s.get('prior_tests')} · rc {s.get('rc')}", flush=True)
    print(f"[計] {TAG} 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    if len(a) == 5 and a[0] == "_contracts":
        return PRIOR.contract_worker(*(PRIOR.absolute(x) for x in a[1:]))
    if len(a) == 4 and a[0] == "_bridgeprobe":
        return PRIOR.bridge_probe_worker(*(PRIOR.absolute(x) for x in a[1:]))
    try:
        return PRIOR.main(a)
    except (OSError, ValueError, SyntaxError, RuntimeError, KeyError, TypeError, ImportError,
            PRIOR.sqlite3.Error, subprocess.SubprocessError) as error:      # 照 v0300 __main__ 的收法
        PRIOR.log("BLOCKED " + type(error).__name__)
        PRIOR.emit({"status": "BLOCKED", "reason": type(error).__name__, "detail": str(error)[:350]})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
