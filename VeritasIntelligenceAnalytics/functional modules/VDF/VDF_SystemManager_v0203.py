#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF SystemManager v0203 — 薄尾(v0202 以前一字不動):隔離要連「中央啟動鉤」一起關,才真的隔離

2026-11-28 主機實跑 v0202:自己的 T4 不過 —— 子行程照樣看到 VIA_ENTRY_CONTROL=CGC_MDL157_VIAUniqueEntryControl_v0100。
  根因:Register-VIA-Commands 讓本視窗起的每支 python 起跑就載 <VIA>/supportive modules/bootstrap/sitecustomize.py,
  它用 setdefault 補回入口標記、設 VIA_DATA_HOME 與每本庫的 VIA_DB_*,再套加速器快取的十幾個執行緒預算變數。
  v0202 只從環境拿掉變數,子行程一起跑就被這支鉤補回來;另外父行程(vv 自己)也是在鉤下起的,那些變數已經在環境裡。
  這支鉤自己有開關:VIA_BOOT=0 → 整段不跑。
本版的隔離(交給引擎自測的子行程):
  · VIA_BOOT=0(中央啟動鉤不跑;各檔自己的加速器橋照常載 —— 自測驗的就是橋)
  · 拿掉鉤會設的:VIA_CENTRAL_ENTRY · VIA_ENTRY_CONTROL · VIA_ACCELERATOR_ROSTER / CONTROL · VIA_DATA_HOME · VIA_DB_* ·
    VIA_*_BOOT · VIA_TOOLS_MOUNT · VIA_BOOT_CHAINED · VIA_PYTHONHOME_SCRUBBED,以及加速器快取(VIA_Reports/accel_activation
    最新 ACCEL_ACTIVATION_*.json 的 applied)套上的那些執行緒變數
  · VIA_VDF_DB_HOME 照 v0202 指到不存在的路徑
  自測直接拿倉裡那支真的 sitecustomize.py 重現主機:沒關鉤 → 子行程有入口標記;本版隔離 → 沒有。
--host-env 照舊原樣帶。其餘照 v0202。零網路 · 不碰 TA-Lib · 不設同意閘 · 不 import VCGC(只讀它的快取 JSON)。
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

import glob
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

VERSION = "v0203"
STEM = "VDF_SystemManager"
TAG = f"VDF_SystemManager {VERSION}"
HERE = Path(__file__).resolve().parent
HOOK_KEYS = ("VIA_CENTRAL_ENTRY", "VIA_ENTRY_CONTROL", "VIA_ACCELERATOR_ROSTER", "VIA_ACCELERATOR_CONTROL", "VIA_DATA_HOME",
             "VIA_TOOLS_MOUNT", "VIA_BOOT_CHAINED", "VIA_PYTHONHOME_SCRUBBED")
THREAD_KEYS = ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS", "NUMEXPR_MAX_THREADS",
               "VECLIB_MAXIMUM_THREADS", "NUMBA_NUM_THREADS", "POLARS_MAX_THREADS", "RAYON_NUM_THREADS", "BLIS_NUM_THREADS",
               "GOTO_NUM_THREADS", "TBB_NUM_THREADS", "OMP_DYNAMIC", "MKL_DYNAMIC")


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)                 # v0202
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


V202 = PRIOR
_ORIG_ISOLATE = V202.isolate


def cache_keys(root: Path | None = None) -> set:
    """加速器快取套上的變數名(只讀 JSON;找不到 = 空集合)。"""
    root = root or V202.V194._p("sm_via_root")()
    hits = sorted(glob.glob(str(Path(root) / "VIA_Reports" / "accel_activation" / "ACCEL_ACTIVATION_*.json")))
    if not hits:
        return set()
    try:
        j = json.loads(Path(hits[-1]).read_text(encoding="utf-8"))
        return {k for k in (j.get("applied") or {}) if isinstance(k, str) and k.isupper() and not k.startswith("PYTHON")}
    except (OSError, ValueError):
        return set()


_CACHE: dict = {}


def isolate(env: dict) -> dict:
    if V202.HOST_ENV["on"]:
        return dict(env)
    if "keys" not in _CACHE:
        try:
            _CACHE["keys"] = cache_keys()
        except Exception:  # noqa: BLE001 — 讀不到快取不擋隔離
            _CACHE["keys"] = set()
    drop = set(HOOK_KEYS) | set(THREAD_KEYS) | _CACHE["keys"]
    e = {k: v for k, v in _ORIG_ISOLATE(env).items()
         if k.upper() not in drop and not k.upper().startswith("VIA_DB_") and not (k.upper().startswith("VIA_") and k.upper().endswith("_BOOT"))}
    e["VIA_BOOT"] = "0"
    return e


V202.isolate = isolate                                         # v0202 的 run_engines / diag 讀模組層 isolate


_ORIG_BANNER = V202.banner


def banner() -> str:
    if V202.HOST_ENV["on"]:
        return _ORIG_BANNER()
    return ("[自測環境] 隔離(同容器):中央啟動鉤關掉(VIA_BOOT=0)· 拿掉入口標記 / 資料家 / VIA_DB_* / 加速器快取的執行緒變數;"
            f"資料家指到不存在的 {V202.NO_HOME}(要用主機環境加 --host-env)")


V202.banner = banner


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:240]) if note and not cond else ""), flush=True)

    print(f"[計] {TAG} 自測開始(本版 4 項 + 前版 {PRIOR_PATH.name} 自測 · 倉裡真的啟動鉤 · 零網路)", flush=True)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T1 加速器真的載到 · 第 3 行標記 · 網路橋在", VIA_ACCEL is not None and src.splitlines()[2] == "# [VIA:ACCEL-BRIDGE:v0111]"
        and VIA_NET_TOOL_PATH is not None)
    host = {"VIA_CENTRAL_ENTRY": "1", "VIA_ENTRY_CONTROL": "x", "VIA_DATA_HOME": "/h", "VIA_DB_VDF_TW_MARKET": "/h/a.duckdb",
            "VIA_DATAHOME_BOOT": "y", "VIA_ACCEL_BOOT": "z", "OMP_NUM_THREADS": "4", "NUMEXPR_MAX_THREADS": "4", "VIA_FROM_VDFSM": "YES", "PATH": "p"}
    e = isolate(host)
    chk("T2 隔離:VIA_BOOT=0 · 鉤設的入口標記 / 資料家 / VIA_DB_* / *_BOOT / 執行緒變數全拿掉 · 自己的旗標與 PATH 照留",
        e.get("VIA_BOOT") == "0" and not any(k in e for k in ("VIA_CENTRAL_ENTRY", "VIA_ENTRY_CONTROL", "VIA_DATA_HOME", "VIA_DB_VDF_TW_MARKET",
                                                               "VIA_DATAHOME_BOOT", "VIA_ACCEL_BOOT", "OMP_NUM_THREADS", "NUMEXPR_MAX_THREADS"))
        and e["VIA_FROM_VDFSM"] == "YES" and e["PATH"] == "p" and e["VIA_VDF_DB_HOME"] == V202.NO_HOME, e)
    hook = V202.V194._p("sm_via_root")() / "supportive modules" / "bootstrap"
    probe = "import os;print(os.environ.get('VIA_ENTRY_CONTROL','-'))"
    base = {k: v for k, v in os.environ.items() if k not in HOOK_KEYS and k != "VIA_BOOT"}   # 在 vv 隔離下跑本自測時,先還原「鉤會跑」
    with tempfile.TemporaryDirectory(prefix="vdf_sm203_") as td:
        raw = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True, timeout=120, cwd=td,
                             env={**base, "PYTHONPATH": str(hook)}).stdout.strip()
        iso = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True, timeout=120, cwd=td,
                             env={**isolate(base), "PYTHONPATH": str(hook)}).stdout.strip()
    chk("T3 拿倉裡真的 bootstrap/sitecustomize.py 重現主機:沒關鉤 → 子行程有入口標記;本版隔離 → 沒有",
        hook.is_dir() and raw.startswith("CGC_MDL157_") and iso == "-", (raw, iso))
    with tempfile.TemporaryDirectory(prefix="vdf_sm203b_") as td:
        p = Path(td) / "FX_env_v0100.py"
        p.write_text("import os,sys\nprint(os.environ.get('VIA_ENTRY_CONTROL','-'))\nsys.exit(0 if 'VIA_ENTRY_CONTROL' not in os.environ else 1)\n"
                     "# --selftest\n", encoding="utf-8")
        r = V202.run_engines([("FX_env", p)], 1, 60, {**base, "PYTHONPATH": str(hook), "VIA_ENTRY_CONTROL": "x"},
                             {0: "PASS", 2: "NODATA", 3: "ABSENT", 4: "GATED"}, lambda t: "", guard=lambda: False)
    chk("T4 vv 起的引擎子行程:就算 PYTHONPATH 掛著中央啟動鉤,也看不到入口標記", r["rows"][0]["result"] == "PASS", r["rows"])
    V202.isolate, V202.banner = _ORIG_ISOLATE, _ORIG_BANNER    # 前版自測看它自己的判法
    try:
        rc = PRIOR.selftest() if callable(getattr(PRIOR, "selftest", None)) else 1
    finally:
        V202.isolate, V202.banner = isolate, banner
    chk("T5 前版 v0202 自測照過(含整條前版鏈)", rc == 0, rc)
    print(f"[計] {TAG} 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(a)


if __name__ == "__main__":
    raise SystemExit(main())
