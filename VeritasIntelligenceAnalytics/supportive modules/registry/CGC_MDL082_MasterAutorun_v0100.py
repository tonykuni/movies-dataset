#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL082_MasterAutorun — 母系統自動總跑器(批127;via-auto)
====================================================================
操作員令(批127,2026-08-24):「complete all mother system + supportive
+ subsystem manager and test…test all functions…till they work…
make it consolidated, make it automatic」。
本器=單一自動入口,五站連跑(全部動態解析最新版,嚴禁寫死版號):
  S1 雙橋覆蓋稽核 — via_bridge_sweeper --audit(每引擎掛加速器;
     凡外呼 API 走網路統包;GREEN=網路缺 0 且加速覆蓋≥99%)
  S2 全站棋盤 — CGC_MDL064_SelftestGrid(89 站誠實三態;FAIL 0=GREEN)
  S3 子系統治理器 V2 — CGC_MDL081(三輪治理;BLOCKED=RED)
  S4 系統總管 — CGC_MDL069_SystemManager(三輪 AUDIT_ONLY;
     GREEN/YELLOW 具名 gate)
  S5 子系統健檢 — via_subsys_manager(VDF/VRN 雙子系統)
輸出:VIA_Reports/autorun_runs/AUTORUN_<ts>/summary.json+逐站 log;
總 RYG:任一 RED/FAIL=rc1;YELLOW 容忍(誠實列示)。
用法:
  via-auto              → 五站全跑
  via-auto --skip S4    → 跳站(逗號分隔)
  via-auto --selftest   → 六檢(替身站,零長跑)
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

import importlib.util
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
RUNS = VIA / "VIA_Reports" / "autorun_runs"


def newest(pattern: str, root: Path = None) -> Path | None:
    hits = sorted((root or HERE).glob(pattern))
    hits = [h for h in hits if "_sha" not in h.stem]
    return hits[-1] if hits else None


def _load(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem + "_dyn", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def stage_bridges() -> dict:
    """S1 雙橋覆蓋稽核(in-process;GREEN=net 缺 0∧accel 覆蓋≥99%)"""
    eng = newest("via_bridge_sweeper_v*.py")
    if eng is None:
        return {"stage": "S1_BRIDGES", "state": "RED", "note": "清掃器缺"}
    a = _load(eng).audit()
    cov = a["accel_have"] / max(a["active"], 1)
    ok = not a["net_miss"] and cov >= 0.99
    return {"stage": "S1_BRIDGES", "state": "GREEN" if ok else "RED",
            "note": f"活動 {a['active']} · 加速覆蓋 {a['accel_have']}({cov:.1%})"
                    f" · 加速殘 {len(a['accel_miss'])}(不可解析原件)"
                    f" · 外呼 {a['net_need']} 網路缺 {len(a['net_miss'])}",
            "accel_residual": a["accel_miss"]}


def _run_cmd(eng: Path, args: list[str], timeout: int, log: Path) -> tuple[int, str]:
    r = subprocess.run([sys.executable, str(eng)] + args, capture_output=True,
                       text=True, timeout=timeout)
    log.write_text((r.stdout or "") + "\n--- stderr ---\n" + (r.stderr or ""),
                   encoding="utf-8")
    return r.returncode, r.stdout or ""


def stage_grid(run_dir: Path, runner=None) -> dict:
    eng = newest("CGC_MDL064_SelftestGrid_v*.py")
    if eng is None:
        return {"stage": "S2_GRID", "state": "RED", "note": "棋盤缺"}
    rc, out = (runner or _run_cmd)(eng, [], 1800, run_dir / "S2_grid.log")
    m = re.search(r"OK (\d+) · FAIL (\d+) · SKIP (\d+)", out)
    if m and m.group(2) == "0":
        return {"stage": "S2_GRID", "state": "GREEN",
                "note": f"OK {m.group(1)} · FAIL 0 · SKIP {m.group(3)}({eng.name})"}
    return {"stage": "S2_GRID", "state": "RED",
            "note": f"rc={rc} · {m.group(0) if m else '無計數行'}"}


def stage_subsysv2(run_dir: Path, runner=None) -> dict:
    eng = newest("CGC_MDL081_SubsystemManagerV2_v*.py")
    if eng is None:
        return {"stage": "S3_SUBSYS_V2", "state": "RED", "note": "治理器 V2 缺"}
    rc, out = (runner or _run_cmd)(eng, [], 600, run_dir / "S3_subsysv2.log")
    m = re.search(r"gate=(\S+)", out)
    gate = m.group(1) if m else "?"
    state = ("GREEN" if gate.endswith("_READY")
             else "YELLOW" if ("WARNINGS" in gate or "REVIEW" in gate)
             else "RED")
    if rc != 0:
        state = "RED"
    return {"stage": "S3_SUBSYS_V2", "state": state, "note": f"{gate}({eng.name})"}


def stage_sysman(run_dir: Path, runner=None) -> dict:
    eng = newest("CGC_MDL069_SystemManager_v*.py")
    if eng is None:
        return {"stage": "S4_SYSMAN", "state": "RED", "note": "系統總管缺"}
    rc, out = (runner or _run_cmd)(eng, ["--rounds", "3"], 1800, run_dir / "S4_sysman.log")
    if "GREEN" in out:
        return {"stage": "S4_SYSMAN", "state": "GREEN", "note": f"Gate GREEN({eng.name})"}
    if "YELLOW" in out:
        return {"stage": "S4_SYSMAN", "state": "YELLOW", "note": f"Gate YELLOW({eng.name})"}
    return {"stage": "S4_SYSMAN", "state": "RED", "note": f"rc={rc} 無 GREEN/YELLOW 字樣"}


def stage_subsys(run_dir: Path, runner=None) -> dict:
    eng = newest("via_subsys_manager_v*.py")
    if eng is None:
        return {"stage": "S5_SUBSYS", "state": "RED", "note": "子系統健檢缺"}
    rc, out = (runner or _run_cmd)(eng, [], 600, run_dir / "S5_subsys.log")
    greens = out.count("GREEN")
    if rc == 0 and greens >= 2:
        return {"stage": "S5_SUBSYS", "state": "GREEN", "note": f"GREEN×{greens}({eng.name})"}
    return {"stage": "S5_SUBSYS", "state": "RED" if rc else "YELLOW",
            "note": f"rc={rc} · GREEN×{greens}"}


STAGES = {"S1": lambda rd, rn: stage_bridges(),
          "S2": stage_grid, "S3": stage_subsysv2, "S4": stage_sysman, "S5": stage_subsys}


def autorun(skip: set[str] | None = None, runner=None, out_root: Path | None = None) -> tuple[int, dict]:
    skip = skip or set()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = (out_root or RUNS) / f"AUTORUN_{ts}"
    run_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for sid, fn in STAGES.items():
        if sid in skip:
            results.append({"stage": sid, "state": "SKIP", "note": "操作員跳站"})
            print(f"  [SKIP  ] {sid} 跳站")
            continue
        try:
            r = fn(run_dir, runner) if sid != "S1" else fn(run_dir, runner)
        except Exception as exc:
            r = {"stage": sid, "state": "RED", "note": f"例外:{str(exc)[:100]}"}
        results.append(r)
        print(f"  [{r['state']:<6}] {r['stage']:<14} {r['note'][:100]}")
    n_red = sum(1 for r in results if r["state"] == "RED")
    n_yel = sum(1 for r in results if r["state"] == "YELLOW")
    summary = {"schema": "via.autorun.v1", "ts": ts, "results": results,
               "red": n_red, "yellow": n_yel,
               "final": "RED" if n_red else ("YELLOW" if n_yel else "GREEN")}
    (run_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1),
                                          encoding="utf-8")
    print(f"  [計] 總態 {summary['final']} · RED {n_red} · YELLOW {n_yel} · 存 {run_dir}")
    return (1 if n_red else 0), summary


def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    # ① 動態解析五站引擎全在位
    engines = {"sweeper": newest("via_bridge_sweeper_v*.py"),
               "grid": newest("CGC_MDL064_SelftestGrid_v*.py"),
               "subsysv2": newest("CGC_MDL081_SubsystemManagerV2_v*.py"),
               "sysman": newest("CGC_MDL069_SystemManager_v*.py"),
               "subsys": newest("via_subsys_manager_v*.py")}
    chk("① 五站引擎動態在位", all(engines.values()),
        str({k: (v.name if v else None) for k, v in engines.items()}))
    # ② S1 實跑(in-process 快)
    r1 = stage_bridges()
    chk("② S1 雙橋稽核 GREEN(網路缺 0)", r1["state"] == "GREEN", r1["note"][:70])
    with tempfile.TemporaryDirectory() as td:
        sand = Path(td)
        # ③ 替身站:GREEN 路徑
        def fake_ok(eng, args, timeout, log):
            log.write_text("x", encoding="utf-8")
            if "SelftestGrid" in eng.name:
                return 0, "[計] OK 83 · FAIL 0 · SKIP 6"
            if "SubsystemManagerV2" in eng.name:
                return 0, "gate=VIA_SUBSYSTEM_MANAGER_READY"
            if "SystemManager" in eng.name:
                return 0, "Gate GREEN_SANDBOX_STABLE"
            return 0, "VDF GREEN\nVRN GREEN"
        rc, s = autorun(skip={"S1"}, runner=fake_ok, out_root=sand)
        chk("③ 替身全綠=rc0+summary GREEN", rc == 0 and s["final"] == "GREEN"
            and (sand / f"AUTORUN_{s['ts']}" / "summary.json").exists())
        # ④ RED 聚合(grid FAIL>0)
        def fake_bad(eng, args, timeout, log):
            log.write_text("x", encoding="utf-8")
            if "SelftestGrid" in eng.name:
                return 1, "[計] OK 80 · FAIL 3 · SKIP 6"
            return 0, "gate=VIA_SUBSYSTEM_MANAGER_READY GREEN VDF GREEN VRN GREEN"
        rc2, s2 = autorun(skip={"S1"}, runner=fake_bad, out_root=sand)
        chk("④ FAIL 站=rc1+總態 RED", rc2 == 1 and s2["final"] == "RED")
        # ⑤ YELLOW 容忍(warnings gate)
        def fake_warn(eng, args, timeout, log):
            log.write_text("x", encoding="utf-8")
            if "SubsystemManagerV2" in eng.name:
                return 0, "gate=VIA_SUBSYSTEM_MANAGER_READY_WITH_WARNINGS"
            if "SelftestGrid" in eng.name:
                return 0, "[計] OK 83 · FAIL 0 · SKIP 6"
            if "SystemManager" in eng.name:
                return 0, "Gate GREEN"
            return 0, "GREEN GREEN"
        rc3, s3 = autorun(skip={"S1"}, runner=fake_warn, out_root=sand)
        chk("⑤ YELLOW 容忍=rc0+總態 YELLOW", rc3 == 0 and s3["final"] == "YELLOW")
        # ⑥ 跳站誠實
        rc4, s4 = autorun(skip={"S1", "S2", "S3", "S4", "S5"}, runner=fake_ok, out_root=sand)
        chk("⑥ 全跳站=SKIP 誠實列示", rc4 == 0
            and all(x["state"] == "SKIP" for x in s4["results"]))
    n = 6 - len(fails)
    print(f"  [計] 六檢 OK {n} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 母系統自動總跑器 · 六檢自測(替身站零長跑)===")
        return selftest()
    skip = set()
    if "--skip" in args:
        i = args.index("--skip")
        skip = {x.strip() for x in args[i + 1].split(",") if x.strip()}
    print("=== 母系統自動總跑器(批127)· 五站連跑 ===")
    rc, _ = autorun(skip=skip)
    return rc


if __name__ == "__main__":
    sys.exit(main())
