#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL149_VeritasCentralGovernanceConsole v0196 — 薄尾(v0195 一字不動):Agent OS + Graphify 併入 VCGC 主控台

操作員 2026-11-12:「把 Agent OS 的全部功能併進 VCGC 成為一個系統 · 登錄助手 / SSOT / regex / 同義字 / 27 個工具 · Graphify 也併進 VCGC ·
全部啟用」。四系統(VRN-1 · VRN-2 · VDF · VCGC)對等獨立不變(L123);Agent OS 與 Graphify 是 VCGC 自己的支援工具。
本版只加兩扇門,其餘一律原樣轉交前版 v0195(子行程 · 參數 / 環境 / rc 不變;只增不減):
  agentos inventory | register [--apply] | activate [--out D]   → CGC_MDL280_VCGCAgentOSHub(盤點 27 工具 · 登錄整合冊 + 中央正則 / 同義字冊 · 逐項真跑)
  agentos <Agent OS 自己的動詞 …>                              → Agent OS 尾版(selftest · status · skills · mcp · context · policy · sdd · scan …)
  graphify status | run [--system S|--path P]                    → CGC_MDL280(隔離環境 · code-only · 一個系統一張圖)
  help 先印前版 help,再補這兩扇門。
對等:不 import 他系統;不設他系統旗標(只補自己的 VIA_FROM_VCGC);零網路([VIA:NET-BRIDGE] 留名);不碰 TA-Lib;不讀寫同意閘。
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
import os
import re
import subprocess
import sys
from pathlib import Path

VERSION = "v0196"
FAMILY = "CGC_MDL149_VeritasCentralGovernanceConsole"
TAG = FAMILY + " " + VERSION
HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
OWN_FLAG = "VIA_FROM_VCGC"
HUB_STEM = "CGC_MDL280_VCGCAgentOSHub"
AOS_DIR = VIA / "supportive modules" / "agent_os"
HUB_VERBS = ("inventory", "register", "activate")


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _prior_path():
    cands = [p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)]
    return max(cands, key=_vnum) if cands else None


def _tail(d: Path, stem: str):
    hits = [p for p in d.glob(stem + "_v*.py") if _vnum(p) >= 0]
    return max(hits, key=_vnum) if hits else None


def _env() -> dict:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    env.setdefault(OWN_FLAG, "YES")                     # 只補本系統自己的入口旗標
    return env


def _call(path, args: list) -> int:
    if path is None:
        print("[%s] ABSENT · 要轉交的檔不在(動詞 %s)" % (TAG, args[:1]))
        return 3
    return subprocess.run([sys.executable, str(path), *args], env=_env()).returncode


def forward(args: list) -> int:
    """前版其餘功能原樣轉交 v0195(子行程 · rc 不變)。"""
    return _call(_prior_path(), args)


_PRIOR = None


def _prior_module():
    global _PRIOR
    if _PRIOR is None:
        pp = _prior_path()
        if pp is None:
            raise AttributeError("前版不在")
        spec = importlib.util.spec_from_file_location(FAMILY + "_prior_for_" + Path(__file__).stem, pp)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        _PRIOR = mod
    return _PRIOR


def __getattr__(name):
    """尾版律 TAILAPI:前版公開名稱經本檔轉接(要用才載)。"""
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(_prior_module(), name)


def agentos(args: list) -> int:
    if not args:
        args = ["inventory"]
    if args[0] in HUB_VERBS:
        return _call(_tail(HERE, HUB_STEM), args)
    return _call(_tail(AOS_DIR, "VIA_AgentOS"), args)    # Agent OS 自己的動詞原樣交給它


def graphify(args: list) -> int:
    return _call(_tail(HERE, HUB_STEM), ["graphify", *(args or ["status"])])


def help_extra() -> None:
    print("  ── v0196 併入(Agent OS + Graphify 是 VCGC 的支援工具;四系統對等獨立不變)──")
    print("  agentos inventory | register [--apply] | activate [--out D]   盤點 27 工具(8 Skill + 9 MCP + 10 slash)· 登錄 · 逐項真跑 → 矩陣")
    print("  agentos <selftest|status|skills list|skills test|mcp serve|context|policy|sdd …>   Agent OS 自己的動詞原樣轉交")
    print("  graphify status | run [--system VRN|VRN_Shared|VDF|VCGC|VQG|AOS] [--path P]   隔離環境 · code-only · 一個系統一張圖")


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""), flush=True)

    print("=== %s 自測(薄尾 · 兩扇門 + 原樣轉交)===" % TAG, flush=True)
    pp = _prior_path()
    chk("① 前版 v0195 在且是本家族上一版", pp is not None and _vnum(pp) == _vnum(__file__) - 1, pp.name if pp else None)
    cp = subprocess.run([sys.executable, str(pp), "version"], env=_env(), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    chk("② 其餘動詞原樣轉交(version → v0195 rc 0)", cp.returncode == 0 and "v0195" in cp.stdout, (cp.stdout.strip().splitlines() or ["?"])[-1][:80])
    hub = _tail(HERE, HUB_STEM)
    chk("③ agentos / graphify 門的正主 CGC_MDL280 在", hub is not None, hub.name if hub else None)
    cp = subprocess.run([sys.executable, str(hub), "inventory"], env=_env(), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    last = (cp.stdout.strip().splitlines() or ["?"])[-1]
    chk("④ agentos inventory → 27 工具", cp.returncode == 0 and "工具 27" in last, last[:120])
    aos = _tail(AOS_DIR, "VIA_AgentOS")
    cp = subprocess.run([sys.executable, str(aos), "skills", "list"], env=_env(), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    chk("⑤ agentos <Agent OS 動詞> 原樣轉交(skills list rc 0)", aos is not None and cp.returncode == 0, aos.name if aos else None)
    cp = subprocess.run([sys.executable, str(hub), "graphify", "status"], env=_env(), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    chk("⑥ graphify status 照實(0 READY / 3 ABSENT)", cp.returncode in (0, 3), (cp.stdout.strip().splitlines() or ["?"])[-1][:100])
    names = [n for n in dir(_prior_module()) if not n.startswith("_") and callable(getattr(_prior_module(), n, None))]
    chk("⑦ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in names), "%d 支" % len(names))
    env = _env()
    chk("⑧ 只補自己的旗標(不設 VDF / VRN 旗標)", env.get(OWN_FLAG) and not any(k in env and k not in os.environ for k in ("VIA_FROM_VDFSM", "VIA_FROM_VRN")))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑨ 零網路 · 不用 TA-Lib · 不 import 他系統 · 不寫同意閘",
        not re.search(r"^\s*(?:import|from)\s+(talib|requests|urllib|VDF_|VRN_|VIA_AgentOS)", src, re.M)
        and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", src))
    n = sum(ok)
    print("[%s] %s selftest · %d/%d" % ("PASS" if n == len(ok) else "FAIL", TAG, n, len(ok)), flush=True)
    return 0 if n == len(ok) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] in ("--selftest", "selftest") and "--legacy" not in args:
        return selftest()
    if args and args[0] == "agentos":
        return agentos(args[1:])
    if args and args[0] == "graphify":
        return graphify(args[1:])
    if not args or args[0] == "help":
        rc = forward(args or ["help"])
        help_extra()
        return rc
    return forward([a for a in args if a != "--legacy"] if args[0] in ("selftest", "--selftest") else args)


if __name__ == "__main__":
    sys.exit(main())
