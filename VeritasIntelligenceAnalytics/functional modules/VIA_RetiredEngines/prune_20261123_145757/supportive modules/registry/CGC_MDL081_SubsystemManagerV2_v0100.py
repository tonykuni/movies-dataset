#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL081_SubsystemManagerV2 — VAP/VDF/VRN 子系統治理器 · 整合轉接版
====================================================================
批126 操作員送達 VIA_SubsystemManager.py v001(1061 行/14 classes;
三輪治理+合約矩陣+證據鏈帳;稽核 compile_ok+空模擬閘擋=預期)。
原件原樣收容:new modules engines/VIA_SubsystemManager_v001.py
(sha256 首 16=3a98c1177a040124;audit 同收)。
本件=動態載入原件之整合轉接(原件零改寫):
  ① 根修 — 原件 DEFAULT_VIA_BASE 寫死 C:\\Users\\tonyk\\Downloads
     (壞環境黑名單根)+run root 落 Downloads:轉接一律動態 _via_root()
     +run root=VIA_Reports/subsysmgr2_runs。
  ② Owner 定位 — 原件候選檔名(VRN.py/VDF.py/VAP.py)不在本樹:
     轉接 OwnerLocator 以動態 glob 取各子系統代表主檔最新版
     (嚴禁寫死版號):VRN=vrn_report_digest_v* /
     VDF=engine/VDF_ENG050_OrderFetch* / VAP=engine/VAP_ENG005_TemplateRunner_v*。
  ③ 政策 fail-closed 原樣 — allow_import/execute/network 預設 False
     (同意閘永不代設紅線一致);三輪治理/Hydra/合約/hash 漂移全承。
角色鏈:VIA_CentralGovernment(候件)→ SupportiveToolkit_Manager →
本器(子系統註冊/合約/依賴序/參數治理/路由/健檢)。
用法:
  via-sysman2               → 三輪治理實跑(run)
  via-sysman2 --order       → 依賴序
  via-sysman2 --contracts   → 合約矩陣
  via-sysman2 --selftest    → 八檢(零網路零執行)
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
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent            # supportive modules/registry
VIA = HERE.parent.parent
ORIGINAL = VIA / "new modules engines" / "VIA_SubsystemManager_v001.py"
RUN_ROOT = VIA / "VIA_Reports" / "subsysmgr2_runs"

OWNER_GLOBS = {  # 子系統代表主檔(動態最新;嚴禁寫死版號)
    "VRN": "functional modules/VRN/vrn_report_digest_v*.py",
    "VDF": "functional modules/VDF/engine/VDF_ENG050_OrderFetch*.py",
    "VAP": "functional modules/VAP/engine/VAP_ENG005_TemplateRunner_v*.py",
}


def load_original():
    """動態載入原件(原件零改寫=version-forward 外包裝)"""
    if not ORIGINAL.exists():
        return None
    spec = importlib.util.spec_from_file_location("via_subsysmgr_v001", ORIGINAL)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["via_subsysmgr_v001"] = mod
    spec.loader.exec_module(mod)
    return mod


def make_manager(mod, rounds: int = 3):
    """轉接工廠:動態根+VIA_Reports run root+glob Owner 定位"""
    class OwnerLocatorVIA(mod.OwnerLocator):
        def locate(self, key, candidates):
            pat = OWNER_GLOBS.get(key)
            if pat:
                hits = sorted(VIA.glob(pat))
                hits = [h for h in hits if "_sha" not in h.stem]
                if hits:
                    return hits[-1], [f"glob_latest:{hits[-1].name}"]
            return super().locate(key, candidates)

    policy = mod.Policy(max_rounds=rounds)   # fail-closed 預設全 False 原樣
    mgr = mod.VIASubsystemManager(via_base=VIA, run_root=RUN_ROOT, policy=policy)
    mgr.locator = OwnerLocatorVIA(VIA)
    return mgr


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    mod = load_original()
    chk("① 原件收容在位+動態載入", mod is not None
        and mod.VERSION == "v001" and len(mod.SUBSYSTEMS) == 3)
    if mod is None:
        return 1
    mgr = make_manager(mod)
    rows = mgr.discover_subsystems()
    by = {r.key: r for r in rows}
    chk("② Owner 定位 3/3(glob 最新版,非寫死)",
        all(by[k].owner_status == "STATIC_OK" for k in ("VRN", "VDF", "VAP"))
        and "vrn_report_digest" in by["VRN"].owner_file
        and "VDF_ENG050" in by["VDF"].owner_file
        and "VAP_ENG005" in by["VAP"].owner_file)
    chk("③ 依賴序 VRN→VDF→VAP", mgr.dependency_order() == ["VRN", "VDF", "VAP"])
    route = mgr.route_matrix()
    vdf_vap = next(x for x in route if x["producer"] == "VDF" and x["consumer"] == "VAP")
    chk("④ 合約矩陣(VDF→VAP 交集非空)", vdf_vap["allowed"]
        and "market_data" in vdf_vap["payloads"])
    env = mgr.route_payload("VDF", "VAP", "market_data", "parquet", {"x": 1})
    chk("⑤ 路由封包(13 欄齊+NOT_EXECUTED)", env["accepted"]
        and env["execution"] == "NOT_EXECUTED"
        and not env["missing_fields"]
        and env["envelope"]["parameters"]["parallel_read_lanes"] <= 6)
    bad = mgr.route_payload("VAP", "VDF", "plot", "html", {})
    imp = mgr.controlled_import("VDF")
    chk("⑥ fail-closed(未宣告路由拒+import 未授權拒)",
        not bad["accepted"] and not imp["ok"]
        and imp["reason"] == "IMPORT_NOT_AUTHORIZED")
    result = mgr.run()
    chk("⑦ 三輪治理(gate≠BLOCKED·零回歸)",
        result["final_gate"] in ("VIA_SUBSYSTEM_MANAGER_READY",
                                 "VIA_SUBSYSTEM_MANAGER_READY_WITH_WARNINGS",
                                 "VIA_SUBSYSTEM_MANAGER_REVIEW_REQUIRED")
        and len(result["rounds"]) == 3
        and not any(r["regression"] for r in result["rounds"]),
        f"({result['final_gate']})")
    led = Path(result["run_dir"]) / "VIA_SUBSYSTEM_MANAGER_EVIDENCE.jsonl"
    ok8 = led.exists()
    if ok8:
        lines = [json.loads(x) for x in led.read_text(encoding="utf-8").splitlines() if x.strip()]
        ok8 = len(lines) >= 5 and all("current_hash" in x for x in lines) \
            and lines[1]["previous_hash"] != ""
    chk("⑧ 證據鏈帳(hash 鏈相扣)", ok8)
    n = 8 - len(fails)
    print(f"  [計] 八檢 OK {n} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 子系統治理器 V2(CGC_MDL081)· 八檢自測(零網路零執行)===")
        return selftest()
    mod = load_original()
    if mod is None:
        print("[FAIL] 原件缺:new modules engines/VIA_SubsystemManager_v001.py")
        return 1
    mgr = make_manager(mod)
    if "--order" in args:
        mgr.discover_subsystems()
        print(json.dumps({"order": mgr.dependency_order()}, ensure_ascii=False))
        return 0
    if "--contracts" in args:
        mgr.discover_subsystems()
        print(json.dumps(mgr.route_matrix(), ensure_ascii=False, indent=1))
        return 0
    result = mgr.run()
    print(f"=== 子系統治理器 V2 · 三輪治理(批126)===")
    print(f"  gate={result['final_gate']} · 依賴序 {result['dependency_order']}"
          f" · run={result['run_id']}")
    return 0 if result["final_gate"] != "VIA_SUBSYSTEM_MANAGER_BLOCKED" else 2


if __name__ == "__main__":
    sys.exit(main())
