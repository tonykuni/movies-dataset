#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
via_subsys_manager_v0100 — 三子系統管理模組(TOOL-099,批95/97)
====================================================================
操作員令:批95「三個子系統管理模組建立同步進行」+批97 焦點四柱
(母系統中央+支援性模組+VRN/VDF/VAP,其他凍結待令)。

單一參數化管理引擎管三子系統(VSM 遞迴原則:每個 S1 子系統自身是
可存活系統,管理者對「單元可存活」負責):
  · 憲章對讀   讀 {SUB}_Subsystem_Manifest.json(收容回歸件)之
               role/integration_state/governance,對照現況
  · 盤點      引擎(py)/啟動器(ps1)/知識冊(json)/介面(html)四類件數
  · 健康      AST 通過率(py 全掃,_sha 鏡像除外)→RYG 燈
  · S1-S5 迷你報 S1 引擎群/S2 介面契約件/S3 註冊台帳覆蓋/
               S3* selftest 掛站/S4 knowledge 冊/S5 憲章在位
  · 矩陣輸出   console 矩陣+JSON 存證 VIA_Reports/subsys_runs/
全唯讀;動碼一律版本前進候令。
用法:
  via-subsys --sub VRN|VDF|VAP|ALL   → 管理報(預設 ALL)
  via-subsys --selftest              → 十檢(沙盒零網路)
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL
except Exception:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import ast
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
RUNS = VIA / "VIA_Reports" / "subsys_runs"
SUBS = ("VRN", "VDF", "VAP")
SKIP = ("_sha", "__pycache__", ".venv", "site-packages", "quarantine", "rollback",
        "_vdf_envs", "webscraping_dualengine")
NOW = datetime.now().strftime("%Y%m%d_%H%M%S")


def _files(root: Path, suffix: str):
    for p in root.rglob(f"*{suffix}"):
        if any(f in str(p) for f in SKIP):
            continue
        yield p


def manage(sub: str, via: Path = VIA) -> dict:
    root = via / "functional modules" / sub
    r = {"sub": sub, "root_ok": root.is_dir()}
    if not r["root_ok"]:
        r["light"] = "RED"
        r["note"] = "子系統根目錄不存在"
        return r
    mf_path = root / f"{sub}_Subsystem_Manifest.json"
    manifest = {}
    if mf_path.exists():
        try:
            manifest = json.loads(mf_path.read_text(encoding="utf-8-sig"))
        except ValueError:
            manifest = {"_parse_error": True}
    r["charter"] = {"present": bool(manifest) and "_parse_error" not in manifest,
                    "role": str(manifest.get("role", "—"))[:80],
                    "integration_state": str(manifest.get("integration_state", "—"))[:40],
                    "governance": bool(manifest.get("governance"))}
    py = list(_files(root, ".py"))
    ps1 = list(_files(root, ".ps1"))
    kn = list(_files(root, ".json"))
    ui = list(_files(root, ".html"))
    ok = bad = 0
    bad_list = []
    for p in py:
        try:
            ast.parse(p.read_text(encoding="utf-8", errors="ignore"))
            ok += 1
        except (SyntaxError, ValueError, RecursionError):
            bad += 1
            bad_list.append(p.name)
    rate = round(ok / max(1, ok + bad) * 100, 1)
    r["inventory"] = {"py": len(py), "ps1": len(ps1), "knowledge_json": len(kn), "ui_html": len(ui)}
    r["health"] = {"ast_ok": ok, "ast_bad": bad, "rate": rate, "bad_top": bad_list[:8]}
    r["light"] = "GREEN" if bad == 0 else ("YELLOW" if bad <= 3 else "RED")
    # VSM 迷你報(遞迴:子系統自身的五系統)
    grid = sorted((via / "supportive modules" / "registry").glob("CGC_MDL064_SelftestGrid_v0*.py"))
    gtxt = grid[-1].read_text(encoding="utf-8", errors="ignore") if grid else ""
    r["vsm"] = {
        "S1_engines": len(py),
        "S2_contracts": sum(1 for k in kn if "SSOT" in k.name or "Registry" in k.name
                            or "Manifest" in k.name or "Params" in k.name),
        "S3_ledger_hook": bool((via / "supportive modules" / "registry"
                                / "VIA_AutoCode_Registry_v0100.json").exists()),
        "S3star_grid_hook": (sub in gtxt) or (sub.lower() in gtxt),
        "S4_knowledge": len([k for k in kn if "knowledge" in str(k).lower()
                             or "SSOT" in k.name]) ,
        "S5_charter": r["charter"]["present"],
    }
    return r


def report(subs, via: Path = VIA, save: bool = True) -> dict:
    out = {"schema": "VIA.SubsysManager.v1", "ts": NOW, "subs": []}
    for s in subs:
        m = manage(s, via)
        out["subs"].append(m)
        if not m["root_ok"]:
            print(f"  [{s}] RED · {m['note']}")
            continue
        c, h, v = m["charter"], m["health"], m["vsm"]
        print(f"  [{s}] {m['light']} · 憲章={'在位' if c['present'] else '缺'}"
              f"({c['integration_state']}) · 引擎 py {m['inventory']['py']}"
              f"/ps1 {m['inventory']['ps1']}/冊 {m['inventory']['knowledge_json']}"
              f"/UI {m['inventory']['ui_html']} · AST {h['rate']}%(壞 {h['ast_bad']})")
        print(f"        VSM:S1 引擎 {v['S1_engines']} · S2 契約 {v['S2_contracts']}"
              f" · S3 台帳 {'✓' if v['S3_ledger_hook'] else '✗'}"
              f" · S3* grid {'✓' if v['S3star_grid_hook'] else '✗'}"
              f" · S4 知識 {v['S4_knowledge']} · S5 憲章 {'✓' if v['S5_charter'] else '✗'}")
        if h["ast_bad"]:
            print(f"        壞件候修:{h['bad_top']}")
    lights = [m.get("light", "RED") for m in out["subs"]]
    out["overall"] = "RED" if "RED" in lights else ("YELLOW" if "YELLOW" in lights else "GREEN")
    if save:
        RUNS.mkdir(parents=True, exist_ok=True)
        ev = RUNS / f"SUBSYS_{NOW}.json"
        ev.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  [計] 三子系統總燈 {out['overall']} · 存證 {ev.name}")
    return out


def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        if not cond:
            fails.append(name)
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")

    with tempfile.TemporaryDirectory() as td:
        via = Path(td)
        (via / "supportive modules" / "registry").mkdir(parents=True)
        (via / "supportive modules" / "registry" / "VIA_AutoCode_Registry_v0100.json").write_text("{}", encoding="utf-8")
        (via / "supportive modules" / "registry" / "CGC_MDL064_SelftestGrid_v0999.py").write_text(
            "# VRN VDF stations", encoding="utf-8")
        for s, good in (("VRN", True), ("VDF", False)):
            d = via / "functional modules" / s
            d.mkdir(parents=True)
            (d / f"{s}_Subsystem_Manifest.json").write_text(json.dumps(
                {"subsystem": s, "role": "測試子系統", "integration_state": "ACTIVE",
                 "governance": {"g": 1}}), encoding="utf-8")
            (d / "engine_a.py").write_text("def a():\n pass\n", encoding="utf-8")
            (d / "K_SSOT.json").write_text("{}", encoding="utf-8")
            if not good:
                (d / "broken.py").write_text("def broken(:\n", encoding="utf-8")
        # ① 憲章對讀
        m = manage("VRN", via)
        chk("憲章對讀", m["charter"]["present"] and m["charter"]["integration_state"] == "ACTIVE"
            and m["charter"]["governance"])
        # ② 盤點四類
        chk("盤點四類", m["inventory"]["py"] == 1 and m["inventory"]["knowledge_json"] == 2)
        # ③ 健康綠燈
        chk("健康綠燈", m["light"] == "GREEN" and m["health"]["rate"] == 100.0)
        # ④ 壞件黃燈+候修清單
        m2 = manage("VDF", via)
        chk("壞件黃燈", m2["light"] == "YELLOW" and m2["health"]["bad_top"] == ["broken.py"])
        # ⑤ VSM 六欄
        chk("VSM 迷你報", m["vsm"]["S1_engines"] == 1 and m["vsm"]["S2_contracts"] == 2
            and m["vsm"]["S3_ledger_hook"] and m["vsm"]["S5_charter"])
        # ⑥ S3* grid 掛站偵測
        chk("grid 掛站偵測", m["vsm"]["S3star_grid_hook"] and m2["vsm"]["S3star_grid_hook"])
        # ⑦ 缺根=RED 誠實
        m3 = manage("VAP", via)
        chk("缺根 RED", m3["light"] == "RED" and not m3["root_ok"])
        # ⑧ 總報+總燈(RED 傳播)
        global RUNS
        _r = RUNS
        RUNS = via / "runs"
        try:
            out = report(["VRN", "VDF", "VAP"], via)
        finally:
            RUNS = _r
        chk("總燈傳播", out["overall"] == "RED")
        # ⑨ 存證落檔
        chk("存證落檔", len(list((via / "runs").glob("SUBSYS_*.json"))) == 1)
        # ⑩ 憲章缺=誠實(拔掉 manifest)
        (via / "functional modules" / "VRN" / "VRN_Subsystem_Manifest.json").unlink()
        m4 = manage("VRN", via)
        chk("憲章缺誠實", not m4["charter"]["present"] and not m4["vsm"]["S5_charter"])
    n = 10 - len(fails)
    print(f"  [計] 十檢 OK {n} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 三子系統管理模組 v0100 · 十檢(沙盒零網路)===")
        return selftest()
    subs = list(SUBS)
    if "--sub" in a:
        i = a.index("--sub")
        v = a[i + 1].upper() if i + 1 < len(a) else "ALL"
        if v != "ALL":
            if v not in SUBS:
                print(f"[用法] --sub VRN|VDF|VAP|ALL(收到 {v})")
                return 2
            subs = [v]
    print("=== 三子系統管理模組(TOOL-099)· VSM 遞迴管理報 ===")
    report(subs)
    return 0


if __name__ == "__main__":
    sys.exit(main())
