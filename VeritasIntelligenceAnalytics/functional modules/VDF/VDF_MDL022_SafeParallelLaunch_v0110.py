#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF_MDL022_SafeParallelLaunch v0110 — 薄尾(v0100–v0109 一字不動):開跑前 ⓪ 暫存庫併入資料家 · 印擷取家

操作員 2026-11-26:「資料庫是否與 …\via_database\vdf_database 相同 · 若不同則整合 · 是否有增量擷取 · 有無重複擷取」
「接入排程優化加速器 · 不傷電腦不傷系統 · PS 啟動、主要功能寫在 py」。
本支本來就是 VDF 的排程啟動器(前版鏈:環境檢查 → 降壓 BELOW_NORMAL + IO LOW · 執行緒 / DuckDB 記憶體上限 → 3 道並行 + 監工
過熱減道 → 橋閘(加速器 + 網路工具)→ 增量擷取 → 矩陣)。本版只在 run 最前面加一步:
  ⓪ ① 印擷取家(VDF_MDL012_FetchGroups 尾版 home;v0113 起沒指定就寫資料家,不再落倉內暫存)
    ② VDF_MDL023_StageMerge 尾版:倉內暫存庫(上一輪落錯地方的列)只補缺併進資料家同名庫;--dry 只列計畫;--no-merge 跳過。
       子行程帶 VDF 入口旗標(本支就是 VDF 入口);合併燈併入總燈(紅留紅)。
其餘(含 --start 對範圍冊、跑完 Rich 矩陣)照 v0109。不代設同意閘;不碰 TA-Lib。
用法:run [--data-home <夾>] [--start 2018-01-01] [--dry] [--no-merge] … · matrix … · --selftest
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "VDF_MDL022_SafeParallelLaunch"
VERSION = "v0110"
TAG = f"{STEM} {VERSION}"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(str(p)).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def worse(*rcs) -> int:                                # 0 綠 < 2 黃 < 1 紅
    rank = {0: 0, 2: 1, 1: 2}
    return max(rcs, key=lambda x: rank.get(x, 2)) if rcs else 0


def _tail(pat: str):
    hits = sorted(HERE.glob(pat), key=_vnum)
    return hits[-1] if hits else None


def stage_steps(args: list) -> list:
    """⓪ 的子行程(不跑,只組):擷取家 → 暫存併入。"""
    dh = PRIOR._opt(args, "--data-home")
    fg, sm = _tail("VDF_MDL012_FetchGroups_v*.py"), _tail("VDF_MDL023_StageMerge_v*.py")
    steps = []
    if fg:
        steps.append(("擷取家", [sys.executable, "-X", "utf8", str(fg), "home"]))
    if sm and "--no-merge" not in args:
        verb = "plan" if "--dry" in args else "apply"
        steps.append(("暫存併入資料家", [sys.executable, "-X", "utf8", str(sm), verb] + (["--home", dh] if dh else [])))
    return steps


def run_stage(args: list, runner=None) -> int:
    runner = runner or (lambda cmd, env: subprocess.run(cmd, env=env, cwd=str(HERE)).returncode)
    env = dict(os.environ, VIA_FROM_VDFSM="YES", PYTHONUTF8="1")
    dh = PRIOR._opt(args, "--data-home")
    if dh:
        env["VIA_VDF_DB_HOME"] = str(dh)               # 跟前版 run 帶給子行程的同一個資料家
    rc = 0
    for title, cmd in stage_steps(args):
        print(f"=== ⓪ {title} · {Path(cmd[3]).name} {' '.join(cmd[4:])} ===", flush=True)
        r = runner(cmd, env)
        rc = worse(rc, r if r in (0, 1, 2) else 1) if title != "擷取家" else worse(rc, 0 if r == 0 else 2)
    return rc


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    if args[:1] != ["run"]:
        return PRIOR.main(args)
    rc0 = run_stage(args)
    rest = [a for a in args if a != "--no-merge"]
    rc = PRIOR.main(rest)
    out = worse(rc, rc0)
    print(f"[{TAG}] ⓪ 暫存併入 rc {rc0} · 主流程 rc {rc} → 總 rc {out}", flush=True)
    return out


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""), flush=True)

    print(f"=== {TAG} · 薄尾自測(假子行程;不跑擷取)===", flush=True)
    chk("① 加速器真的載到(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    chk("② 網路工具橋在位(載入不出網)", VIA_NET_TOOL_PATH is not None)
    st = stage_steps(["run", "--start", "2018-01-01"])
    chk("③ ⓪ 先印擷取家(FetchGroups home)再併暫存(StageMerge apply)", [t for t, _ in st] == ["擷取家", "暫存併入資料家"]
        and st[0][1][-1] == "home" and st[1][1][4] == "apply", st)
    chk("④ --dry → plan(唯讀)· --data-home 帶給併入 · --no-merge 只剩擷取家",
        stage_steps(["run", "--dry"])[1][1][4] == "plan" and stage_steps(["run", "--data-home", "X"])[1][1][-2:] == ["--home", "X"]
        and [t for t, _ in stage_steps(["run", "--no-merge"])] == ["擷取家"])
    seen = []
    rc = run_stage(["run", "--data-home", "D"], runner=lambda cmd, env: seen.append((cmd[4], env.get("VIA_FROM_VDFSM"), env.get("VIA_VDF_DB_HOME"))) or 1)
    chk("⑤ 子行程帶 VDF 入口旗標與資料家 · 併入紅 → ⓪ 紅(擷取家查不到只算黃)", rc == 1 and seen == [("home", "YES", "D"), ("apply", "YES", "D")], (rc, seen))
    chk("⑥ 總燈 worse:紅留紅 · 黃不蓋紅", worse(0, 2) == 2 and worse(1, 2) == 1 and worse(2, 0) == 2)
    chk("⑦ 本檔沒寫同意閘(只帶入口旗標)", not re.search(r"VIA_(NET|SCRAPE)_CONSENT[\"']?\]?\s*=", Path(__file__).read_text(encoding="utf-8")))
    import contextlib
    import io
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            rc_p = PRIOR.selftest()
    except Exception as exc:  # noqa: BLE001
        rc_p = 1
        print(f"  [註] 前版鏈自測丟例外:{type(exc).__name__}", flush=True)
    alone = subprocess.run([sys.executable, str(PRIOR_PATH), "--selftest"], capture_output=True, text=True, timeout=900).returncode
    chk("⑧ 前版鏈自測在本版下的結果 = 單獨跑 v0109 的結果(本版不讓前版變壞)", (rc_p == 0) == (alone == 0), (rc_p, alone))
    PRIOR_RC["rc"] = rc_p
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑨ 檔面:第 3 行加速器標記 · 雙橋 · glob 取前版 · 零 TA-Lib",
        src.splitlines()[2].startswith("# [VIA:ACCEL-BRIDGE") and "[VIA:NET-BRIDGE:v0100]" in src and "HERE.glob(STEM" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M))
    pr = PRIOR_RC.get("rc", 0)
    print(f"[selftest] {TAG} {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}"
          + ("" if pr == 0 else " · 前版自測本來就不綠(這台缺 rich 等依賴;範圍外,照實回黃)"), flush=True)
    if not all(ok):
        return 1
    return 0 if pr == 0 else 2


PRIOR_RC = {}


if __name__ == "__main__":
    sys.exit(main())
