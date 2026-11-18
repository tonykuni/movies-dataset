#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VDF_MDL022_SafeParallelLaunch v0104 — VDF 自己的啟動器就是入口(子行程帶入口標記)· 總結行印本版版本。

2026-11-18 容器開閘實測(純 Python 啟動,沒經 PowerShell 的 Invoke-VIAPython):
  e116 AAII · e115 情緒 兩支回 {"state": "DENY", "why": "only via-aaii through Invoke-VIAPython"} —— 引擎只認
  VIA_CENTRAL_ENTRY=1(只有中央 PS 入口會設)。VDF 從自己的 Python 入口啟動就被自己的引擎拒絕,
  等於 VDF 要靠另一個系統的入口才跑得全;那個入口一改,VDF 就少兩支。這違反系統獨立(L123)。
本版(v0103 一字不動;薄尾)只做兩件:
  ① 執行期間,交給各工作的環境多帶 VIA_CENTRAL_ENTRY=1 與 VIA_ENTRY_CONTROL=<本檔檔名>(原本就有設的不蓋):
     VDF 的啟動器是 VDF 這個系統的受控入口;標記寫的是真正的入口名,不冒用別人的。只在子行程環境裡,不寫任何檔、不改本行程環境。
  ② 總結行與收據的引擎版本印本版(v0103 跑完印的是 v0102)。
順序不變:先降 CPU / DRAM 壓力並等系統靜下來 → 依機器能力 3~6 道 → 監工過熱減道、暫停最新子行程、冷卻恢復。
不設同意閘、不安裝、本檔不出網。用法同 v0103:run [--slots auto|3-6] [--refill-apply] … · check · bridge-gate · --selftest
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
import os
import subprocess
import sys
from pathlib import Path

SYSTEM = "VDF"
STEM = "VDF_MDL022_SafeParallelLaunch"
VERSION = "v0104"
TAG = f"{STEM} {VERSION}"
HERE = Path(__file__).resolve().parent
PRIOR_PATH = HERE / f"{STEM}_v0103.py"
MIN_SLOTS, MAX_SLOTS = 3, 6


def _load(path: Path, name: str):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


P = _load(PRIOR_PATH, "vdf_launch_prior_for_" + VERSION)      # v0103(道數 3~6);往下 v0102(結果併燈)· v0101(降壓 · 監工)
B = P.B
ENTRY_ENV = {"VIA_CENTRAL_ENTRY": "1", "VIA_ENTRY_CONTROL": Path(__file__).stem}


def __getattr__(name):
    """尾版律 TAILAPI:前版公開名稱經本檔轉接。"""
    return getattr(P, name)


def _chain() -> list:
    out, m = [], P
    while m is not None and m not in out:
        out.append(m)
        m = vars(m).get("P") or (vars(m).get("B") if vars(m).get("B") is not m else None)
    return out


def with_entry(env: dict) -> dict:
    """子行程環境補入口標記;已經有的不蓋(經 PS 入口進來時保留它設的值)。"""
    out = dict(env)
    for k, v in ENTRY_ENV.items():
        out.setdefault(k, v)
    return out


def cmd_run(argv: list, check_only=False) -> int:
    owners = [m for m in _chain() if "calm_env" in vars(m)]
    tagged = [m for m in _chain() if "TAG" in vars(m) and "VERSION" in vars(m)]
    saved_env = [(m, m.calm_env) for m in owners]
    saved_tag = [(m, m.TAG, m.VERSION) for m in tagged]

    def make(orig):
        def calm_env(slots, tr, base=None):
            return with_entry(orig(slots, tr, base))
        return calm_env

    for m, orig in saved_env:
        m.calm_env = make(orig)
    for m, _t, _v in saved_tag:
        if m is not B:                 # v0101 的 TAG 由 v0102 在執行期間換 / 還原;這裡換 v0102 · v0103 自己的
            m.TAG, m.VERSION = TAG, VERSION
    try:
        return P.cmd_run(argv, check_only=check_only)
    finally:
        for m, orig in saved_env:
            m.calm_env = orig
        for m, t, v in saved_tag:
            m.TAG, m.VERSION = t, v


def selftest() -> int:
    ok = []

    def ck(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:240]) if note and not cond else ""), flush=True)
    print(f"[計] {TAG} 自測開始(本版 + 前版 {PRIOR_PATH.name} 另起行程)", flush=True)
    import tempfile
    owners = [m for m in _chain() if "calm_env" in vars(m)]
    before = [m.calm_env for m in owners]
    seen = {}

    def fake_run(argv, check_only=False):
        with tempfile.TemporaryDirectory(prefix="vdf_launch_v0104_") as td:
            seen["env"] = B.calm_env(4, Path(td), base={})
            seen["env_set"] = B.calm_env(4, Path(td), base={"VIA_CENTRAL_ENTRY": "1", "VIA_ENTRY_CONTROL": "CGC_MDL157_VIAUniqueEntryControl_v0100"})
        seen["tags"] = [m.TAG for m in _chain() if "TAG" in vars(m) and m is not B]
        return 0

    real = P.cmd_run
    P.cmd_run = fake_run
    mine_before = {k: os.environ.get(k) for k in ENTRY_ENV}
    try:
        rc = cmd_run([])
    finally:
        P.cmd_run = real
    ck("E1 執行期間子行程環境帶入口標記:VIA_CENTRAL_ENTRY=1 · VIA_ENTRY_CONTROL = 本檔檔名",
       rc == 0 and seen["env"].get("VIA_CENTRAL_ENTRY") == "1" and seen["env"].get("VIA_ENTRY_CONTROL") == Path(__file__).stem, seen.get("env", {}).get("VIA_ENTRY_CONTROL"))
    ck("E2 已經有入口標記的不蓋(經 PS 入口進來時保留它的值)", seen["env_set"].get("VIA_ENTRY_CONTROL") == "CGC_MDL157_VIAUniqueEntryControl_v0100")
    ck("E3 降壓的執行緒上限 · TEMP 仍在(前版 calm_env 的內容沒掉)", "OMP_NUM_THREADS" in seen["env"] and "TMP" in seen["env"] and seen["env"].get("PYTHONUTF8") == "1")
    ck("E4 跑完還原:前版 calm_env 是原件 · 本行程環境沒被改", [m.calm_env for m in owners] == before and {k: os.environ.get(k) for k in ENTRY_ENV} == mine_before and bool(owners))
    ck("E5 執行期間前版印的版本是本版;跑完還原", all(t == TAG for t in seen["tags"]) and bool(seen["tags"]) and P.TAG.endswith("v0103"), seen.get("tags"))
    old = (B.MIN_SLOTS, B.MAX_SLOTS)
    ck("E6 道數 3~6 照前版(本版不改)", (P.MIN_SLOTS, P.MAX_SLOTS) == (3, 6) and (B.MIN_SLOTS, B.MAX_SLOTS) == old)
    text = Path(__file__).read_text(encoding="utf-8")
    ck("E7 檔面:加速器橋與網路橋標記 · 不寫同意閘 · 沒有本機路徑 · 不改本行程 environ",
       "[VIA:ACCEL-BRIDGE:v0100]" in text and "[VIA:NET-BRIDGE:v0100]" in text and "_CONSENT\"] " + "=" not in text
       and "\\" + "Users" not in text and "/" + "home/" not in text and "os.environ[" + "\"VIA_CENTRAL" not in text)
    pr = subprocess.run([sys.executable, "-B", str(PRIOR_PATH), "--selftest"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    ck("E8 前版 %s 自測照過(另起行程)" % PRIOR_PATH.name, pr.returncode == 0, (pr.stdout or "")[-240:])
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
