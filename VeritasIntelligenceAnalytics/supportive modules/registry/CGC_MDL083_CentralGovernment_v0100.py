#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL083_CentralGovernment — 中央治理引擎 · 整合轉接版(批132;via-cg)
====================================================================
批132 送達 VIA_CentralGovernance_ALL_v0100.zip=候件鏈到貨:
AdaptiveDownstream v0100 主引擎(2,635 行;三輪治理/六車道/15 加速器
A01-A15/安全修白名單/斷路器/證據鏈帳)+能力冊+驗證證據+沙盒修補件。
原件 byte-exact 收容:new modules engines/VIA_CentralGovernance_ALL_v0100/。
本件=記憶體級相容轉接(原件零觸碰):
  ① 3.11 相容 — 原件 L1948 巢狀 f-string 引號重用=PEP 701(3.12+);
     轉接載入時對「該單行」做等價文本改寫(先取變數再入 f-string),
     compile 於記憶體,磁碟原件零改動;3.12+ 環境原文即通。
  ② 根修 — def_PARAM_DEFAULT_ROOT 寫死 Downloads(黑名單根)僅為預設:
     轉接一律 --root=_via_root() 動態+--output-root=VIA_Reports/
     centralgov_runs。
  ③ 政策冊對齊 — VIA_CentralGovernment_AdaptivePolicy_v0100.json
     (批131 已收)之 15 加速器/閘序/禁令與引擎 capabilities 對勘。
角色鏈:本器(最終治理權威)→ SupportiveToolkit_Manager(候件)→
CGC_MDL081 SubsystemManagerV2(在役)。
用法:
  via-cg --capabilities      → 能力契約
  via-cg --audit             → AUDIT 模式三輪實跑(唯讀)
  via-cg --selftest          → 轉接四檢+原引擎自測 8 檢(零網路)
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

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
ORIGINAL = (VIA / "new modules engines" / "VIA_CentralGovernance_ALL_v0100"
            / "bundle" / "VIA_CentralGovernment_AdaptiveDownstream_v0100_Bundle"
            / "VIA_CentralGovernment_AdaptiveDownstream_v0100.py")
RUN_ROOT = VIA / "VIA_Reports" / "centralgov_runs"
POLICY_GLOB = "VIA_CentralGovernment_AdaptivePolicy_v*.json"

PEP701_LINE_FRag = 'f"$e=$null;$t=$null;[System.Management.Automation.Language.Parser]::ParseFile(\'{str(path_value).replace("\'", "\'\'")}\''
COMPAT_OLD = ('command = [powershell, "-NoProfile", "-NonInteractive", "-Command", '
              'f"$e=$null;$t=$null;[System.Management.Automation.Language.Parser]::'
              'ParseFile(\'{str(path_value).replace("\'", "\'\'")}\'')
COMPAT_NEW = ('_pv_esc = str(path_value).replace(chr(39), chr(39) * 2)\n'
              '                command = [powershell, "-NoProfile", "-NonInteractive", "-Command", '
              'f"$e=$null;$t=$null;[System.Management.Automation.Language.Parser]::'
              'ParseFile(\'{_pv_esc}\'')


def load_engine():
    """記憶體級載入(3.11 相容單行改寫;原件零觸碰;3.12+ 原文直通)"""
    if not ORIGINAL.exists():
        return None, "原件缺"
    src = ORIGINAL.read_text(encoding="utf-8", errors="replace")
    try:
        compile(src, str(ORIGINAL), "exec")
        text = src                                     # 3.12+:原文即通
        note = "原文直通"
    except SyntaxError:
        text = src.replace(COMPAT_OLD, COMPAT_NEW, 1)  # 3.11:等價單行改寫
        note = "PEP701 單行相容改寫(記憶體級)"
        try:
            compile(text, str(ORIGINAL), "exec")
        except SyntaxError as exc:
            return None, f"相容改寫後仍不通:{exc}"
    import types
    mod = types.ModuleType("via_centralgov_dyn")
    mod.__file__ = str(ORIGINAL)
    sys.modules["via_centralgov_dyn"] = mod
    exec(compile(text, str(ORIGINAL), "exec"), mod.__dict__)
    return mod, note


def load_policy() -> dict | None:
    hits = sorted((VIA / "new modules engines").glob(POLICY_GLOB))
    return json.loads(hits[-1].read_text(encoding="utf-8-sig")) if hits else None


def run_audit(rounds: int = 3) -> int:
    mod, note = load_engine()
    if mod is None:
        print(f"[FAIL] 引擎載入敗:{note}")
        return 1
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    print(f"=== 中央治理引擎 · AUDIT 三輪(批132;{note})===")
    rc = mod.def_main(["run", "--root", str(VIA), "--output-root", str(RUN_ROOT),
                       "--mode", "AUDIT", "--rounds", str(rounds)])
    return rc


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    mod, note = load_engine()
    chk("① 原件收容在位+記憶體級載入", mod is not None, f"({note})")
    if mod is None:
        return 1
    caps = mod.def_capabilities()
    chk("② 能力契約(三輪/六車道/15 加速器)",
        caps["rounds"] == 3 and len(caps["lanes"]) == 6
        and len(caps["accelerators"]) == 15
        and "canonical mutation" in caps["forbidden"])
    pol = load_policy()
    chk("③ 政策冊對勘(批131 收容冊 A01-A15 與引擎一致)",
        pol is not None and pol["accelerators"] == caps["accelerators"]
        and pol["round_limit"] == 3)
    r = mod.def_run_self_tests()
    chk("④ 原引擎自測 8/8", r["ok"] and r["total"] == 8 and not r["failed"],
        f"(passed {len(r['passed'])})")
    n = 4 - len(fails)
    print(f"  [計] 轉接四檢(含原 8 檢)OK {n} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 中央治理引擎轉接(CGC_MDL083)· 四檢自測(零網路)===")
        return selftest()
    if "--capabilities" in args:
        mod, _ = load_engine()
        if mod is None:
            return 1
        print(json.dumps(mod.def_capabilities(), ensure_ascii=False, indent=1))
        return 0
    if "--audit" in args:
        return run_audit()
    print(__doc__.split("用法:")[1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
