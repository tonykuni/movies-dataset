#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_SystemManager v0158 — 薄尾:all 的 ask 步燈號照問參數啟動器的真 rc(逾時沒決定 = 2 黃,不再被 pwsh 吃成 0 綠)

工作站實錄(2026-10-14 02:xx activate_vdf):問參數頁 15 分鐘沒收到決定 → 啟動器印「逾時沒收到決定 → 不啟動(NODATA,rc 2)」,
但 all 的 ask 步記 rc 0 · GREEN。根因:v0155 用 `pwsh -Command ". '<Open-VIA-VDF 尾版>'"` 起啟動器;啟動器只設 $global:LASTEXITCODE
(Stop-VIAOpenVdf),沒有 exit → pwsh 行程回 0,不管裡面是 0 / 2 / 1。
本版:把 ask 那條 -Command 補成 `. '<opener>'; exit $LASTEXITCODE`(只改交給 pwsh 的字串;.ps1 一字不動,L70),
  其餘命令原樣交給前版 run_cmd;燈號對照不變(v0155 _lamp:0 綠 · 2 黃 · 其他紅)。
其餘(all · 問參數頁 · 子行程 · 不代設同意閘 · 零網路 · 不碰 TA-Lib · 1c 視覺)照 v0157 → v0155。
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。本檔零網路。"""
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
import re
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA_ROOT = HERE.parents[1]
_STEM = "VDF_SystemManager"
TAG = "v0158"
SELF_ID = "VDF"
EXIT_SUFFIX_V0158 = "; exit $LASTEXITCODE"


def _vnum_v0158(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0158(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0158(p) < _vnum_v0158(__file__)), key=_vnum_v0158)
PRIOR = _load_v0158(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def _chain_v0158() -> list:
    """前版鏈(只收真模組;某版把 PRIOR 包成替身就停在它前面)。"""
    out, m = [], PRIOR
    while isinstance(m, types.ModuleType) and m not in out:
        out.append(m)
        m = getattr(m, "PRIOR", None)
    return out


def _owner_v0158(name: str):
    """沿前版鏈找第一個真正定義 name 的那一版(本體);找不到回 None。"""
    for m in _chain_v0158():
        if name in vars(m):
            return m
    return None


_OWN_CMD = _owner_v0158("RUN_CMD")                     # v0155:all 的 ask 步用 RUN_CMD 起 pwsh
_PREV_RUN_CMD = getattr(_OWN_CMD, "RUN_CMD", None)
# 本檔可能被載入兩次(MDL012 v0108 也按尾版 glob 載 VDF_SystemManager_v*.py;前版鏈在 sys.modules 共用):
# 第二份看到本體的 RUN_CMD 已是本版替身 → 取它記下的本體,不疊兩層。
_ORIG_RUN_CMD = getattr(_PREV_RUN_CMD, "_orig_v0158", None) or _PREV_RUN_CMD


def ask_cmd_v0158(cmd) -> list:
    """啟動器那條 pwsh -Command ". '<opener>'" 補 `; exit $LASTEXITCODE`;不是這個形狀的命令原樣回(純函式,自測用)。"""
    cmd = [str(c) for c in cmd]
    if (len(cmd) >= 3 and Path(cmd[0]).stem.lower() == "pwsh" and cmd[-2] == "-Command"
            and cmd[-1].lstrip().startswith(". '") and "exit" not in cmd[-1]):
        cmd[-1] = cmd[-1].rstrip().rstrip(";") + EXIT_SUFFIX_V0158
    return cmd


def run_cmd_v0158(cmd: list, timeout=None) -> dict:
    """同 v0155 run_cmd(stdout 直通 · env 只加 VIA_FROM_VCGC · 同意閘不加不減),只把 ask 的 -Command 字串補上 exit。"""
    return _ORIG_RUN_CMD(ask_cmd_v0158(cmd), timeout=timeout)


run_cmd_v0158._orig_v0158 = _ORIG_RUN_CMD              # 給再載入的那一份認本體(冪等,不疊層)
if _OWN_CMD is not None and _ORIG_RUN_CMD is not None:
    _OWN_CMD.RUN_CMD = run_cmd_v0158


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args[:2]:
        return selftest()
    return PRIOR.main(args)


def selftest() -> int:
    global _ORIG_RUN_CMD
    import contextlib
    import io
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)
    print(f"=== VDF_SystemManager {TAG} · 薄尾自測(ask 步燈號照啟動器真 rc)===")
    chk("① 前版鏈 · RUN_CMD 本體找得到(v0155)", _OWN_CMD is not None and Path(_OWN_CMD.__file__).stem.endswith("_v0155") and callable(_ORIG_RUN_CMD),
        Path(_OWN_CMD.__file__).stem if _OWN_CMD else "—")
    chk("② 本體的 RUN_CMD 已換成本版(all 的 ask 步走本版)", _OWN_CMD is not None and _OWN_CMD.RUN_CMD is run_cmd_v0158)
    ask = ["pwsh", "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ". 'C:\\VIA\\Open-VIA-VDF-v0103.ps1'"]
    out = ask_cmd_v0158(ask)
    chk("③ ask 那條 -Command 補 exit $LASTEXITCODE(路徑與其餘參數不動)", out[:-1] == ask[:-1] and out[-1] == ask[-1] + EXIT_SUFFIX_V0158, out[-1])
    chk("④ 已帶 exit 的、不是點源形狀的、非 pwsh 的命令原樣回",
        ask_cmd_v0158(out) == out and ask_cmd_v0158(["pwsh", "-Command", "Get-Date"]) == ["pwsh", "-Command", "Get-Date"]
        and ask_cmd_v0158(["python", "-c", ". 'x'"]) == ["python", "-c", ". 'x'"])
    seen = {}

    def fake_orig(cmd, timeout=None):
        seen["cmd"], seen["timeout"] = list(cmd), timeout
        return {"rc": 2, "secs": 0.1}
    keep = _ORIG_RUN_CMD
    _ORIG_RUN_CMD = fake_orig
    try:
        r = run_cmd_v0158(ask, timeout=5)
    finally:
        _ORIG_RUN_CMD = keep
    chk("⑤ run_cmd:補完交給前版本體,rc 原樣回(2 → _lamp 黃)· timeout 照傳",
        r == {"rc": 2, "secs": 0.1} and seen["cmd"][-1].endswith(EXIT_SUFFIX_V0158) and seen["timeout"] == 5 and PRIOR._lamp(2, yellow=(2,)) == "YELLOW" and PRIOR._lamp(0, yellow=(2,)) == "GREEN")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc_prior = PRIOR.selftest()
    txt = buf.getvalue()
    chk("⑥ 前版自測照過(v0157 → v0155 鏈)", rc_prior == 0, f"rc={rc_prior}")
    now = getattr(_OWN_CMD, "RUN_CMD", None)
    chk("⑦ 前版自測跑完本體的 RUN_CMD 仍是本版且只包一層(v0155 自測還原;MDL012 再載本檔不疊層)",
        _OWN_CMD is not None and now is not None and now.__name__ == "run_cmd_v0158"
        and getattr(now, "_orig_v0158", None) is _ORIG_RUN_CMD and getattr(_ORIG_RUN_CMD, "_orig_v0158", None) is None,
        f"{getattr(now, '__name__', now)} → {getattr(_ORIG_RUN_CMD, '__name__', _ORIG_RUN_CMD)}")
    n = 7
    print(f"  [計] VDF_SystemManager_{TAG} 自測 {n - len(fails)}/{n} · {'PASS' if not fails else 'FAIL ' + ', '.join(fails)}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
