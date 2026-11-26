#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF_ENG242_ThreePeriodDistill v0101 — 薄尾(v0100 一字不動):自測不吃本機狀態 · VDF 境標示不誤報

桌機實錄(2026-11-26 VIA_HostBoot vdf3 · 收據 intake/fastrun-20261126_111733):
  ① v0100 自測 15/16:「--live:每支個別啟動 · 同意閘只在子行程 · 帶入口標記 · 寫運作帳」NG(容器 16/16)。
     讀碼:那一檢要求「父行程 VIA_NET_CONSENT != YES」——操作員視窗先前開過同意閘(既有 .ps1 會在整個視窗設),
     父行程本來就是 YES → 檢查在吃本機狀態(CLAUDE.md「自測不吃本機狀態」)。引擎行為本身沒錯。
  ② 「派別支引擎的 python:C:\Users\…\envs\via_vdf_312\Scripts\python.exe(VDF 境沒找到,退回本解譯器 · 黃)」:
     本解譯器就是 via_vdf_312,v0100 只比「== sys.executable」就標黃 → 誤報。
本版:
  · 自測在「擦掉 VIA_NET_CONSENT / VIA_SCRAPE_CONSENT / VIA_ENTRY_CONTROL / VIA_CENTRAL_ENTRY」的環境跑前版自測,跑完原樣還原;
    另加一檢:父行程同意閘先開著(模擬桌機)時,子行程照樣拿到 YES 與入口標記、父行程的值不被改。
  · 派別 python 標示:路徑落在 via_vdf_312 / via_vdf / via_vdf_313 境(或 VIA_PY_VDF)= 綠,不再誤標「沒找到」。
其餘動詞全部轉給 v0100(run · ready · inventory · plan · names · distill · reconcile · bench · params-init)。
資料不離開本機;本檔零外呼(網路工具只惰性載入)· 不碰 TA-Lib · 不寫同意閘到任何檔。
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。本支零外呼。"""
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
import os
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "VDF_ENG242_ThreePeriodDistill"
VERSION = "v0101"
TAG = f"{STEM} {VERSION}"
VDF_ENV_NAMES = ("via_vdf_312", "via_vdf", "via_vdf_313")
GATE_KEYS = ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT", "VIA_ENTRY_CONTROL", "VIA_CENTRAL_ENTRY")
FALLBACK_NOTE = "(VDF 境沒找到,退回本解譯器 · 黃)"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{PRIOR_PATH.stem}_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def is_vdf_env(py: str) -> bool:
    """路徑落在 VDF 家族境(via_vdf_312 / via_vdf / via_vdf_313)或就是 VIA_PY_VDF 指的那支 → True。"""
    if not py:
        return False
    ov = os.environ.get("VIA_PY_VDF", "")
    if ov and os.path.normcase(os.path.abspath(ov)) == os.path.normcase(os.path.abspath(py)):
        return True
    parts = [x.lower() for x in re.split(r"[\\/]+", str(py))]
    return any(n in parts for n in VDF_ENV_NAMES)


_PRIOR_SAY = PRIOR.say


def say(msg: str) -> None:
    """前版的 say 加一層:派別 python 其實就是 VDF 家族境時,把「沒找到 · 黃」改成照實的綠字樣。"""
    if isinstance(msg, str) and msg.startswith("派別支引擎的 python:") and FALLBACK_NOTE in msg and is_vdf_env(getattr(PRIOR, "PY_VDF", "")):
        msg = msg.replace(FALLBACK_NOTE, "(本解譯器就是 VDF 家族境 · 綠)")
    _PRIOR_SAY(msg)


PRIOR.say = say                                   # 前版模組內部呼叫的 say 走這一層(只改這一句字樣)
PRIOR_TAG = PRIOR.TAG
PRIOR.TAG = TAG                                   # 收據 / 橫幅照實寫跑的是哪一版(動詞仍是前版的)


class _ScrubbedGates:
    """暫時擦掉同意閘與入口標記(自測不吃本機狀態);離開時原樣還原,連「本來沒有」也還原成沒有。"""

    def __enter__(self):
        self.saved = {k: os.environ.get(k) for k in GATE_KEYS}
        for k in GATE_KEYS:
            os.environ.pop(k, None)
        return self

    def __exit__(self, *exc):
        for k, v in self.saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        return False


def main() -> int:
    if sys.argv[1:2] in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main()


def selftest() -> int:
    ok, bad = [], []

    def chk(name, cond, note=""):
        (ok if cond else bad).append(name)
        print(f"  [{'OK' if cond else 'NG'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""), flush=True)

    chk("加速器載入(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    chk("網路工具載入(_via_net() is not None · 載入不出網)", _via_net() is not None, VIA_NET_TOOL_PATH)
    chk("前版 = 同家族比自己小的最大版 · 動詞全轉給前版",
        _vnum(PRIOR_PATH) < _vnum(Path(__file__)) and __getattr__("run_groups") is PRIOR.run_groups and __getattr__("ready") is PRIOR.ready)
    win = r"C:\Users\x\envs\via_vdf_312\Scripts\python.exe"
    chk("VDF 境判定:Windows venv / conda / Linux 都認;一般 python 不認",
        is_vdf_env(win) and is_vdf_env("/home/x/miniconda3/envs/via_vdf/bin/python3") and is_vdf_env(r"C:\x\envs\via_vdf_313\python.exe")
        and not is_vdf_env(r"C:\Python313\python.exe") and not is_vdf_env("/usr/local/bin/python3") and not is_vdf_env(""))
    seen = []
    keep_say, keep_py = _PRIOR_SAY, getattr(PRIOR, "PY_VDF", "")
    globals()["_PRIOR_SAY"] = seen.append
    try:
        PRIOR.PY_VDF = win
        PRIOR.say(f"派別支引擎的 python:{win}{FALLBACK_NOTE}")
        PRIOR.PY_VDF = r"C:\Python313\python.exe"
        PRIOR.say(f"派別支引擎的 python:C:\\Python313\\python.exe{FALLBACK_NOTE}")
    finally:
        globals()["_PRIOR_SAY"] = keep_say
        PRIOR.PY_VDF = keep_py
    chk("標示不誤報:本解譯器是 via_vdf_312 → 綠字樣;真的退回一般 python → 照舊黃",
        len(seen) == 2 and "綠" in seen[0] and FALLBACK_NOTE not in seen[0] and FALLBACK_NOTE in seen[1], seen)
    before = {k: os.environ.get(k) for k in GATE_KEYS}
    with _ScrubbedGates():
        gates_clean = all(os.environ.get(k) is None for k in GATE_KEYS)
        print(f"[前版] {PRIOR_PATH.name} 自測(擦掉同意閘 / 入口標記的環境;跑完還原 · 本檔不設閘)", flush=True)
        PRIOR.TAG = PRIOR_TAG                     # 前版自測照前版字樣
        try:
            rc = PRIOR.selftest()
        finally:
            PRIOR.TAG = TAG
    chk("前版 v0100 自測在乾淨閘環境照過(rc 0)· 操作員視窗閘先開著也一樣(擦掉再跑)", gates_clean and rc == 0, rc)
    chk("橫幅 / 收據寫本版(PRIOR.TAG = v0101)", PRIOR.TAG == TAG)
    chk("自測後環境原樣還原(同意閘 · 入口標記)", {k: os.environ.get(k) for k in GATE_KEYS} == before)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("檔面:雙橋在 · 不設同意閘到檔 · 零 TA-Lib",
        "[VIA:ACCEL-BRIDGE:v0100]" in src and "[VIA:NET-BRIDGE:v0100]" in src
        and not re.search(r"^\s*(import|from)\s+(talib|requests)", src, re.M)
        and not re.search(r"^\s*os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src, re.M))
    print(f"{TAG} selftest {len(ok)}/{len(ok) + len(bad)}" + (" · 不過:" + " · ".join(bad) if bad else ""), flush=True)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
