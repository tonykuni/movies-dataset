#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF_MDL013_ActivateVDF v0120 — 薄尾(v0100–v0119 一字不動):v0118 自測 ③ 用牆鐘判「不等」→ 慢的主機假紅

2026-11-28 主機 vv(3 道並行):v0118 ③「本版:指揮行程認得出 → 不等(1.02 秒)」不過 —— 條件是子行程總牆鐘 < 1.0 秒,
  但牆鐘含 python 起動 + 載鉤,負載高的主機差一點就超過;同一檢的收據寫得清清楚楚:boss=True、argv 對(認得出指揮行程)。
  ③ 真正要驗的是「指揮行程不排隊」,而收據本來就記了等多久(wait_s,v0117 起每筆都有)。
本版只做一件事:在子行程實跑 v0119 自測;不過的若只有那一行 ③,就用同一個夾具(v0118 本輪鉤 · 中央鉤 runpy 接力)
  實跑一次指揮行程,改看收據:boss=True · argv = 「VDF_SystemManager_v9999.py engine list」 · wait_s ≤ 0.2 秒(沒排隊)。
  都對才算過;有任何別的一行不過 → 照實紅。其餘照 v0119(main 原樣轉交)。
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
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "VDF_MDL013_ActivateVDF"
TAG = "VDF_MDL013_ActivateVDF v0120"
STALE_SIG = "③ 本版:指揮行程認得出 → 不等"
BOSS_WAIT_MAX = 0.2


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(STEM + "_prior_for_v0120", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)                 # v0119
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V0118 = PRIOR.PRIOR


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def boss_receipt(tmp: Path) -> dict:
    """照 v0118 ③ 的夾具跑一次指揮行程,回收據第一列(boss · argv · wait_s)。"""
    hook = tmp / "pyhook"
    hook.mkdir(parents=True)
    (hook / "sitecustomize.py").write_text(V0118.HOOK_SRC_V0118, encoding="utf-8")
    central = tmp / "central"
    central.mkdir()
    (central / "sitecustomize.py").write_text(
        "import runpy\nrunpy.run_path(%r, run_name='sitecustomize_after_vdf')\n" % str(hook / "sitecustomize.py"), encoding="utf-8")
    log = tmp / "mem.jsonl"
    base = {k: v for k, v in os.environ.items() if not k.startswith(("VIA_VDF_", "VIA_DUCK"))}
    base.update(PYTHONPATH=str(central), VIA_VDF_MEM_LOG=str(log), VIA_VDF_TOOLS="0", VIA_DUCK_TEMP="0", PYTHONIOENCODING="utf-8",
                VIA_VDF_MEM_FLOOR_MB=str(10 ** 9), VIA_VDF_MEM_ADMIT_MAX_S="1.2")
    boss = tmp / "VDF_SystemManager_v9999.py"
    boss.write_text("print('boss')\n", encoding="utf-8")
    subprocess.run([sys.executable, str(boss), "engine", "list"], env=base, capture_output=True, text=True, timeout=120)
    rows = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines() if x.strip()] if log.is_file() else []
    return rows[0] if rows else {}


def boss_ok(r: dict) -> bool:
    return bool(r.get("boss")) and r.get("argv") == "VDF_SystemManager_v9999.py engine list" and float(r.get("wait_s", 99)) <= BOSS_WAIT_MAX


def prior_fails() -> tuple:
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    for k in ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT"):
        env.pop(k, None)
    try:
        cp = subprocess.run([sys.executable, str(PRIOR_PATH), "--selftest"], capture_output=True, text=True, encoding="utf-8",
                            errors="replace", timeout=1500, stdin=subprocess.DEVNULL, env=env, cwd=str(HERE))
    except subprocess.TimeoutExpired:
        return 124, ["v0119 自測逾時"], []
    lines = (cp.stdout + cp.stderr).splitlines()
    fails = [ln.strip() for ln in lines if "[FAIL]" in ln or "[NG]" in ln]
    stale = [ln for ln in fails if STALE_SIG in ln]
    wrap = [ln for ln in fails if STALE_SIG not in ln and re.search(r"前版.{0,40}(自測|鏈)", ln)]
    other = [ln for ln in fails if ln not in stale and ln not in wrap]
    return cp.returncode, other, stale


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:240]) if note and not cond else ""), flush=True)

    print(f"[計] {TAG} 自測開始(本版 4 項 · 前版 {PRIOR_PATH.name} 自測在子行程實跑 · 零網路)", flush=True)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T1 加速器真的載到(VIA_ACCEL is not None)· 第 3 行標記 · 網路橋在 __future__ 之下",
        VIA_ACCEL is not None and src.splitlines()[2] == "# [VIA:ACCEL-BRIDGE:v0111]" and VIA_NET_TOOL_PATH is not None)
    with tempfile.TemporaryDirectory(prefix="mdl013_120_") as td:
        r = boss_receipt(Path(td))
    chk("T2 收據判法:指揮行程 boss=True · argv 認得出 · 沒排隊(wait_s ≤ %.1f 秒)" % BOSS_WAIT_MAX, boss_ok(r), r)
    chk("T3 判法的負控:排隊的(wait_s 1.0)/ 沒認出指揮行程的 → 不過",
        not boss_ok({**r, "wait_s": 1.0}) and not boss_ok({**r, "boss": False}) and not boss_ok({}))
    rc, other, stale = prior_fails()
    chk("T4 v0119 自測:綠;或不過的只有 ③ 牆鐘那一行(與包著它的前版行)且 T2 收據判法過",
        rc == 0 or (not other and bool(stale) and boss_ok(r)), (rc, other[:3]))
    print(f"[計] {TAG} 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--selftest"]:
        return selftest()
    return PRIOR.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
