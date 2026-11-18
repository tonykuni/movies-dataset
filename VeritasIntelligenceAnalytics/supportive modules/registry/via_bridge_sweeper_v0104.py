#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""via_bridge_sweeper v0104 — v0103 薄尾(v0103 一字不動):兩支量尺範圍對齊(去重 · 不衝突)。

操作員 2026-11-10:「用 VCGC 節省 TOKEN 工具去完成全景式全面性除錯 · 注入 AST 加速器 · 加入深透到全部覆蓋率 100% · 網路工具合併後只增不減 · 去重不衝突」。

量測(2026-11-10 容器):VCGC 正式量尺 CGC_MDL124_BridgeSweeper v0111 --subsystems 報四系統 ALL/accel 1807/1807 · VDF/net 149/149 = 100%;
本清掃器 v0103 --audit 卻報 加速缺 33 · 網路缺 8 —— 同一棵樹兩支尺兩種說法(批538 的老問題又來了)。逐件查:
  · 7 件是真缺(活樹 · AI 可負責)→ 本輪已用 v0103 的 inject_one 補(只插標記塊 · 原碼一字不動 · 注入前後雙 ast.parse;自測 / 回傳碼與原檔一致)。
  · 其餘 34 件都在「原件收容 / 凍結發行 / 不進倉」三類 —— v0103 的 EXEMPT_INTAKE 漏列了這幾個夾,所以被當活樹算缺:
      supportive modules/intake/        外部包原件(AzureFlow QA · MotherInspector …)· 正本不就地修改
      functional modules/VRN/intake/    VRN v0108 年度交接包原件(handover pack)· 正本不就地修改
      docs/handoff/ai/vrn2_release_     VRN-2 已發行的凍結發行包副本 · 改了就和發行雜湊對不上
      functional modules/VRN2/          VRN-2 桌機私有 runtime(不進倉 · 本倉規則 never-commit)
另:成功鎖(交接冊 frozen_sources)上的檔改列 EXEMPT_FROZEN —— 鎖住的正本零觸碰優先(就地注入會觸發 SUCCESS_LOCK_CHANGED;
  2026-11-10 實錄:VRN_ENG112 v0100 · 非個股引擎 v0310 注入後被交接閘抓到 → 已還原原檔一字不差)。
本版只把這四個夾補進 EXEMPT_INTAKE(誠實列示 · 計數照算 · 不從清單消失),其他判準、注入、undo 全照 v0103。
只增不減:豁免清單只加不減;不刪任何橋、不改任何檔。不用 TA-Lib。
自測:python via_bridge_sweeper_v0104.py --selftest(前版 v0103 自測於乾淨子行程 + 本版 5 項)。
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
import os
import subprocess
import sys
from pathlib import Path

VERSION = "v0104"
HERE = Path(__file__).resolve().parent
_PRIOR = HERE / "via_bridge_sweeper_v0103.py"
_spec = importlib.util.spec_from_file_location("via_bridge_sweeper_v0103_for_v0104", _PRIOR)
P = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = P
_spec.loader.exec_module(P)

ADDED_EXEMPT_INTAKE = ("supportive modules/intake/", "functional modules/VRN/intake/",
                       "docs/handoff/ai/vrn2_release_", "functional modules/VRN2/")
P.EXEMPT_INTAKE = tuple(P.EXEMPT_INTAKE) + tuple(x for x in ADDED_EXEMPT_INTAKE if x not in P.EXEMPT_INTAKE)
EXEMPT_INTAKE = P.EXEMPT_INTAKE


def frozen_sources() -> set:
    """交接冊 frozen_sources(成功鎖:路徑 → sha)。鎖住的檔零觸碰優先於全樹導入令(注入會觸發 SUCCESS_LOCK_CHANGED)。"""
    import json as _json
    hits = sorted((HERE).glob("VIA_Handoff_Continuity_SSOT_v*.json"))
    if not hits:
        return set()
    try:
        d = _json.loads(hits[-1].read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return set()
    return {str(k).replace("\\", "/") for k in (d.get("frozen_sources") or {})}


FROZEN = frozen_sources()
_classify_0103 = P.classify


def classify(rp: str) -> str:
    r = rp.replace("\\", "/")
    if r in FROZEN:
        return "EXEMPT_FROZEN"
    return _classify_0103(rp)


P.classify = classify
_audit_0103 = P.audit


def audit(root=None) -> dict:
    _orig = P.classify
    seen = {"n": 0}

    def _cls(rp):
        c = _orig(rp)
        if c == "EXEMPT_FROZEN":
            seen["n"] += 1
            return "SKIP"                                   # v0103 的 exempt 計數表沒有這一格 → 走 SKIP 路徑,另計數
        return c
    P.classify = _cls
    try:
        a = _audit_0103(root) if root is not None else _audit_0103()
    finally:
        P.classify = _orig
    a.setdefault("exempt", {})["EXEMPT_FROZEN"] = seen["n"]
    return a


P.audit = audit


def __getattr__(name):
    return getattr(P, name)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""), flush=True)
    cp = subprocess.run([sys.executable, str(_PRIOR), "--selftest"], cwd=str(HERE), capture_output=True, text=True, encoding="utf-8",
                        errors="replace", timeout=900, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    prior_ok = cp.returncode == 0
    chk("① 豁免只增不減:v0103 原有項全在 + 新增 4 夾", all(x in EXEMPT_INTAKE for x in ADDED_EXEMPT_INTAKE) and len(EXEMPT_INTAKE) == len(set(EXEMPT_INTAKE))
        and all(x in EXEMPT_INTAKE for x in ("new modules engines", "references/intake", "_inbox_to_classify")))
    cases = {"supportive modules/intake/VIA_AzureFlow_QA_v0110/scripts/inspect_azureflow.py": "EXEMPT_INTAKE",
             "functional modules/VRN/intake/VRN_v0108_Annual/x/pack/VRN_AnnualAudit_v0108.py": "EXEMPT_INTAKE",
             "docs/handoff/ai/vrn2_release_v0156/VIA_FactSet_YFinance_Consensus_Matrix_Engine_v0112.py": "EXEMPT_INTAKE",
             "functional modules/VRN2/VIA_CNYES_FactSet_YFinance_Consensus_Fusion_Engine_v0122.py": "EXEMPT_INTAKE",
             "functional modules/VRN/VRN_SystemManager_v0262.py": "ACTIVE",
             "functional modules/VRN/VRN2_UIAction_v0107.py": "ACTIVE",
             "functional modules/VDF/engine/VDF_ENG054_TWDailyBackfill_v0110.py": "ACTIVE",
             "docs/handoff/ai/VIA_LakeConsole_v0101.py": "ACTIVE"}
    got = {k: P.classify(k) for k in cases}
    chk("② 新豁免只吃這四類夾 · VRN / VDF / docs 活檔照算 ACTIVE(不把活樹藏起來)", got == cases, {k.split("/")[-1]: v for k, v in got.items() if v != cases[k]})
    chk("②b 成功鎖上的檔(交接冊 frozen_sources)= EXEMPT_FROZEN · 零觸碰", bool(FROZEN) and all(classify(x) == "EXEMPT_FROZEN" for x in list(FROZEN)[:5])
        and classify("functional modules/VRN/VRN_SystemManager_v0262.py") == "ACTIVE", "鎖 %d 檔" % len(FROZEN))
    a = audit()
    chk("③ 真樹活樹:加速缺 0 · 網路缺 0(= 全覆蓋;豁免另列計數)", not a["accel_miss"] and not a["net_miss"],
        "加速 %d/%d · 網路 %d/%d · 豁免 %s" % (a["accel_have"], a["active"], a["net_have"], a["net_need"], a["exempt"]))
    chk("④ 前版 v0103 自測(乾淨子行程)", prior_ok, "rc %s" % cp.returncode)
    n = sum(ok)
    print("[%s] via_bridge_sweeper %s selftest · 本版 %d/%d · 前版鏈 v0103 %s" % ("PASS" if n == len(ok) else "FAIL", VERSION, n, len(ok), "PASS" if prior_ok else "FAIL"), flush=True)
    return 0 if n == len(ok) else 1


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return P.main()


if __name__ == "__main__":
    sys.exit(main())
