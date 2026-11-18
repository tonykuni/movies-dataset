#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VDF_MDL022_SafeParallelLaunch v0103 — 同時跑的獨立流程上限 5 → 6(操作員 2026-11-18:「道數改成 3~6」)。

本版(v0102 一字不動;薄尾):只在執行期間把道數上限設成 6,跑完還原。下限仍是 3。
順序不變:第一步先降 CPU / DRAM 壓力並等系統靜下來 → 依這台機器的核心數與可用記憶體算道數(夾在 3~6)→
監工每 5 秒量一次,連續過熱就減道並暫停最新起的子行程,冷卻後恢復 / 加道,至少留一支在跑。
結果併燈、同意閘開著時補擷取,照 v0102。不設同意閘、不安裝、本檔不出網。
用法同 v0102:run [--slots auto|1-6] [--refill-apply] … · check · --selftest
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
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(本啟動器零連線,橋只為全樹契約齊備) =====
VIA_NET_TOOL_PATH = None


def _via_net():
    """本啟動器**零連線**:出網的是它起的擷取引擎(各自帶網路橋與雙閘);本函式永遠回 None。"""
    return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import subprocess
import sys
from pathlib import Path

SYSTEM = "VDF"
STEM = "VDF_MDL022_SafeParallelLaunch"
VERSION = "v0103"
TAG = f"{STEM} {VERSION}"
HERE = Path(__file__).resolve().parent
PRIOR_PATH = HERE / f"{STEM}_v0102.py"
MIN_SLOTS, MAX_SLOTS = 3, 6


def _load(path: Path, name: str):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


P = _load(PRIOR_PATH, "vdf_launch_prior_for_" + VERSION)      # v0102(結果併燈);它的 B = v0101(降壓 · 監工 · 道數)
B = P.B


def __getattr__(name):
    """尾版律 TAILAPI:前版公開名稱經本檔轉接。"""
    return getattr(P, name)


def cmd_run(argv: list, check_only=False) -> int:
    old = (B.MIN_SLOTS, B.MAX_SLOTS)
    B.MIN_SLOTS, B.MAX_SLOTS = MIN_SLOTS, MAX_SLOTS
    try:
        return P.cmd_run(argv, check_only=check_only)
    finally:
        B.MIN_SLOTS, B.MAX_SLOTS = old


def selftest() -> int:
    ok = []

    def ck(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:240]) if note and not cond else ""), flush=True)
    print(f"[計] {TAG} 自測開始(本版 + 前版 {PRIOR_PATH.name} 另起行程)", flush=True)
    big = {"cpus": 16, "mem_avail_gb": 48.0, "mem_total_gb": 64.0, "cpu_pct": 5.0}
    small = {"cpus": 2, "mem_avail_gb": 3.0, "mem_total_gb": 8.0, "cpu_pct": 5.0}
    old = (B.MIN_SLOTS, B.MAX_SLOTS)
    before = B.plan_slots("auto", big)
    B.MIN_SLOTS, B.MAX_SLOTS = MIN_SLOTS, MAX_SLOTS
    try:
        got = (B.plan_slots("auto", big), B.plan_slots("auto", small), B.plan_slots("6", big), B.plan_slots("9", big), B.plan_slots("1", big))
    finally:
        B.MIN_SLOTS, B.MAX_SLOTS = old
    ck("L1 道數夾在 3~6:大機器自動可到 6(前版最多 5)· 小機器不低於 3 · 指定 9 壓回 6 · 指定 1 抬到 3",
       before <= 5 and got[0] == 6 and got[1] == 3 and got[2] == 6 and got[3] == 6 and got[4] == 3, (before, got))
    ck("L2 跑完還原:前版的道數上下限是原件", (B.MIN_SLOTS, B.MAX_SLOTS) == old == (3, 5), (B.MIN_SLOTS, B.MAX_SLOTS))
    text = Path(__file__).read_text(encoding="utf-8")
    ck("L3 檔面:加速器橋與網路橋標記 · 不寫同意閘 · 沒有本機路徑",
       "[VIA:ACCEL-BRIDGE:v0100]" in text and "[VIA:NET-BRIDGE:v0100]" in text and "_CONSENT\"] " + "=" not in text
       and "\\" + "Users" not in text and "/" + "home/" not in text)
    pr = subprocess.run([sys.executable, "-B", str(PRIOR_PATH), "--selftest"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    ck("L4 前版 %s 自測照過(另起行程)" % PRIOR_PATH.name, pr.returncode == 0, (pr.stdout or "")[-240:])
    n = sum(ok)
    print(f"[計] {STEM} {VERSION} 自測 {n}/{len(ok)} {'PASS' if n == len(ok) else 'FAIL'}", flush=True)
    return 0 if n == len(ok) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    if args[0] in ("--selftest", "selftest"):
        return selftest()
    if args[0] == "bridge-gate":
        return B.cmd_bridge_gate()
    if args[0] == "check":
        return cmd_run(args[1:] + ["--no-open"], check_only=True)
    if args[0] == "run":
        return cmd_run(args[1:])
    print(f"[{TAG}] 未知動詞 {args[0]}(run · check · bridge-gate · --selftest)")
    return 2


if __name__ == "__main__":
    sys.exit(main())
