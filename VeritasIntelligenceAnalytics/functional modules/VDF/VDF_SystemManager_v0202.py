#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF SystemManager v0202 — 薄尾(v0201 以前一字不動):vv / diag 的引擎自測一律在隔離環境跑

2026-11-28 主機 diag(5 個家族 · 每一版)對容器重現:主機獨有的紅,大多是自測吃到「操作員工作階段的環境」——
  · Register-VIA-Commands 設的 VIA_CENTRAL_ENTRY / VIA_ENTRY_CONTROL:MDL008 v0110 只設這兩個就紅(容器重現)
  · 這台機器真的有資料家(VDF_DataHome_SSOT 冊上的 db_home 存在):MDL008 v0110 只設 VIA_VDF_DB_HOME 指到真夾也紅;
    MDL022 v0110 同樣情況卡到逾時(容器重現)
  CLAUDE.md「自測不吃本機狀態」:單元自測要跟在容器跑一樣;真資料的驗證交給 outputs / db verify。
本版:vv 與 diag 交給引擎自測的子行程環境 ——
  拿掉 VIA_CENTRAL_ENTRY · VIA_ENTRY_CONTROL;VIA_VDF_DB_HOME 指到一個不存在的暫存路徑(resolve_home 照「env 指的家不在」回沒有家,
  不再往冊上找到真的資料家);VDF 自己的入口旗標照帶。要用操作員原本的環境跑:加 --host-env(照實標「主機環境」)。
  開跑時印一行「[自測環境] …」說清楚用了哪一種。其餘照 v0201。零網路 · 不碰 TA-Lib · 不設同意閘 · 不 import VCGC。
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
from pathlib import Path

VERSION = "v0202"
STEM = "VDF_SystemManager"
TAG = f"VDF_SystemManager {VERSION}"
HERE = Path(__file__).resolve().parent
DROP = ("VIA_CENTRAL_ENTRY", "VIA_ENTRY_CONTROL")
HOST_ENV = {"on": False}


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)                 # v0201
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


V199 = PRIOR.PRIOR.PRIOR                                       # v0201 → v0200 → v0199
V198 = V199.V198
V194 = V198.V194
NO_HOME = str(Path(tempfile.gettempdir()) / "via_vdf_selftest_no_home")


def isolate(env: dict) -> dict:
    """引擎自測用的環境:拿掉他系統入口標記;資料家指到不存在的路徑。--host-env 時原樣回。"""
    if HOST_ENV["on"]:
        return dict(env)
    e = {k: v for k, v in env.items() if k not in DROP}
    e["VIA_VDF_DB_HOME"] = NO_HOME
    return e


_ORIG_RUN_ENGINES = V194.run_engines                           # = v0197 的 run_engines(並行 + 逾時重跑)


def run_engines(items, lanes, timeout, env, rc_map, missing_lib, beat=None, guard=None):
    kw = {"beat": beat} if guard is None else {"beat": beat, "guard": guard}
    return _ORIG_RUN_ENGINES(items, lanes, timeout, isolate(env), rc_map, missing_lib, **kw)


V194.run_engines = run_engines
_ORIG_DIAG = V199.diag


def diag(root, fams, lanes: int = 3, env=None):
    return _ORIG_DIAG(root, fams, lanes, isolate(env or V194._p("sm_child_env")()))


V199.diag = diag


def banner() -> str:
    if HOST_ENV["on"]:
        return "[自測環境] 主機環境(--host-env:操作員工作階段的變數與真的資料家原樣帶進自測)"
    return f"[自測環境] 隔離(同容器):拿掉 {' · '.join(DROP)};資料家指到不存在的 {NO_HOME}(要用主機環境加 --host-env)"


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:240]) if note and not cond else ""), flush=True)

    print(f"[計] {TAG} 自測開始(本版 4 項 + 前版 {PRIOR_PATH.name} 自測 · 暫存夾 · 零網路)", flush=True)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T1 加速器真的載到 · 第 3 行標記 · 網路橋在", VIA_ACCEL is not None and src.splitlines()[2] == "# [VIA:ACCEL-BRIDGE:v0111]"
        and VIA_NET_TOOL_PATH is not None)
    host = {"VIA_CENTRAL_ENTRY": "1", "VIA_ENTRY_CONTROL": "CGC_MDL157_VIAUniqueEntryControl_v0109", "VIA_VDF_DB_HOME": "/real/home",
            "VIA_FROM_VDFSM": "YES", "PATH": "x"}
    e = isolate(host)
    chk("T2 隔離:入口標記拿掉 · 資料家指到不存在的路徑 · VDF 自己的旗標與其他變數照留",
        "VIA_CENTRAL_ENTRY" not in e and "VIA_ENTRY_CONTROL" not in e and e["VIA_VDF_DB_HOME"] == NO_HOME and not Path(NO_HOME).exists()
        and e["VIA_FROM_VDFSM"] == "YES" and e["PATH"] == "x", e)
    HOST_ENV["on"] = True
    e2, b_on = isolate(host), banner()
    HOST_ENV["on"] = False
    chk("T3 --host-env:原樣帶 · 開跑那行照實標「主機環境」;沒帶時標「隔離」",
        e2 == host and b_on.startswith("[自測環境] 主機環境") and banner().startswith("[自測環境] 隔離"), (b_on, banner()))
    with tempfile.TemporaryDirectory(prefix="vdf_sm202_") as td:
        p = Path(td) / "FX_env_v0100.py"
        p.write_text("import os,sys\nprint(os.environ.get('VIA_ENTRY_CONTROL','-'), os.environ.get('VIA_VDF_DB_HOME','-'))\n"
                     "sys.exit(0 if 'VIA_ENTRY_CONTROL' not in os.environ else 1)\n# --selftest\n", encoding="utf-8")
        r = run_engines([("FX_env", p)], 1, 30, {**os.environ, **host}, {0: "PASS", 2: "NODATA", 3: "ABSENT", 4: "GATED"},
                        lambda t: "", guard=lambda: False)
    chk("T4 vv 真的用隔離環境起引擎子行程(帶著主機標記進來,子行程看不到)", r["rows"][0]["result"] == "PASS", r["rows"])
    V194.run_engines, V199.diag = _ORIG_RUN_ENGINES, _ORIG_DIAG       # 前版自測看它自己的裝法
    try:
        rc = PRIOR.selftest() if callable(getattr(PRIOR, "selftest", None)) else 1
    finally:
        V194.run_engines, V199.diag = run_engines, diag
    chk("T5 前版 v0201 自測照過(含整條前版鏈)", rc == 0, rc)
    print(f"[計] {TAG} 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    if "--host-env" in a:
        a.remove("--host-env")
        HOST_ENV["on"] = True
    if a[:1] in (["vv"], ["diag"]):
        print(banner(), file=sys.stderr if "--json" in a else sys.stdout, flush=True)
    return PRIOR.main(a)


if __name__ == "__main__":
    raise SystemExit(main())
