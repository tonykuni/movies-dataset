#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VAP_ENG010_ChartLibrarySSOT — 圖庫 SSOT 橋(批247;操作員令「收容完善整合」)
====================================================================
收容件對位整合(批246 對位圖②):VAP_Chart_Library(VIA-M-VAPLIB;
Workbench 存檔快照)+VIA_VAP_User_Workflow_Spec(v023 族)→現役 VAP 鏈。
機制(收容件原地不動,graceful):
  ①尾版解析:VAP intake glob VAP_Chart_Library*.json+
    VIA_VAP_User_Workflow_Spec_v*.json(語意版號排序;嚴禁寫死版號)
  ②SSOT 驗證:meta.ssot_rules(regex 冊)逐項驗 defaults/overrides
    值域——違規=RYG 紅列示(不改收容件;誠實三態)
  ③runtime 快照:合流輸出 registry/VIA_VAP_ChartLibrary_Runtime_
    v0100.json(衍生物可重生;defaults+lock+layout+db+sap 對齊鎖+
    來源指紋)供 Chartlib/TemplateRunner/圖規鎖守衛讀取
  ④QA 對照:VIA_VAP_v*_QA_Report.json 在=引為證據鏈(缺=誠實無)
用法:python3 VAP_ENG010_ChartLibrarySSOT_v0100.py run | --selftest
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
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent.parent
INTAKE = HERE.parent / "references" / "intake"
OUT = VIA / "supportive modules" / "registry" / "VIA_VAP_ChartLibrary_Runtime_v0100.json"

VER_RX = re.compile(r"v(\d+)(?:\.(\d+))?(?:\.(\d+))?")


def _ver_key(p: Path) -> tuple:
    vs = [tuple(int(x) if x else 0 for x in m.groups())
          for m in VER_RX.finditer(p.name)]
    return max(vs) if vs else (0, 0, 0)


def _newest(pattern: str, root: Path | None = None) -> Path | None:
    """尾版解析:glob 遞迴+語意版號排序(嚴禁寫死版號)"""
    root = root or INTAKE
    hits = [p for p in root.rglob(pattern) if p.is_file()]
    return max(hits, key=_ver_key) if hits else None


def validate_rules(doc: dict) -> tuple[list[dict], int]:
    """②SSOT 驗證:meta.ssot_rules regex 冊逐項驗 defaults/overrides"""
    rules = (doc.get("meta") or {}).get("ssot_rules") or {}
    rows, bad = [], 0
    for scope in ("defaults", "overrides"):
        for k, v in (doc.get(scope) or {}).items():
            rx = rules.get(k)
            if rx is None:
                rows.append({"scope": scope, "key": k, "val": v,
                             "state": "NO_RULE"})
                continue
            ok = re.fullmatch(rx, str(v).lower()) is not None
            if not ok:
                bad += 1
            rows.append({"scope": scope, "key": k, "val": v,
                         "state": "OK" if ok else "VIOLATION"})
    return rows, bad


def run(intake: Path | None = None, out: Path | None = None) -> int:
    intake = intake or INTAKE
    out = out or OUT
    lib_p = _newest("VAP_Chart_Library*.json", intake)
    spec_p = _newest("VIA_VAP_User_Workflow_Spec_v*.json", intake)
    qa_p = _newest("VIA_VAP_v*_QA_Report.json", intake)
    if lib_p is None and spec_p is None:
        print("[圖庫橋] 收容缺(VAP intake 無圖庫/工作流 spec)=誠實停;"
              "先 via-intake")
        return 2
    snap: dict = {"generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                  "engine": "VAP_ENG010_ChartLibrarySSOT_v0100",
                  "sources": {}, "validation": {}, "runtime": {}}
    total_bad = 0
    for tag, p in (("chart_library", lib_p), ("workflow_spec", spec_p)):
        if p is None:
            snap["sources"][tag] = {"state": "ABSENT(誠實)"}
            continue
        try:
            doc = json.loads(p.read_text(encoding="utf-8-sig"))
        except Exception as exc:
            snap["sources"][tag] = {"file": p.name,
                                    "state": f"PARSE_FAIL({type(exc).__name__})"}
            total_bad += 1
            continue
        rows, bad = validate_rules(doc)
        total_bad += bad
        snap["sources"][tag] = {"file": p.name, "state": "OK",
                                "via_code": (doc.get("meta") or {}).get("via_code")}
        snap["validation"][tag] = {"rows": rows, "violations": bad}
        # ③合流 runtime(後讀者勝=spec(新版)覆蓋 library(舊版)同鍵)
        for k in ("defaults", "lock", "layout", "db", "compose"):
            if doc.get(k) not in (None, {}, []):
                snap["runtime"][k] = doc[k]
        sap = (doc.get("meta") or {}).get("sap_msp_align_locked")
        if sap:
            snap["runtime"]["sap_msp_align_locked"] = sap
    snap["qa_report"] = ({"file": qa_p.name, "state": "PRESENT"}
                         if qa_p else {"state": "ABSENT(誠實)"})
    snap["verdict"] = "GREEN" if total_bad == 0 else f"RED({total_bad} 違規)"
    out.write_text(json.dumps(snap, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print(f"[圖庫橋] 圖庫={lib_p.name if lib_p else '無'} · "
          f"spec={spec_p.name if spec_p else '無'} · "
          f"QA={'在' if qa_p else '無(誠實)'} · 驗證 {snap['verdict']}"
          f" · 快照 {out.name}")
    return 0 if total_bad == 0 else 1


def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        lib = {"meta": {"via_code": "VIA-M-VAPLIB",
                        "ssot_rules": {"palette": "^(via|deep)$",
                                       "grid": "^(true|false)$"}},
               "defaults": {"palette": "via", "grid": "true"},
               "lock": {"visual": True}, "db": ["TWSE"]}
        (tdp / "VAP_Chart_Library (1).json").write_text(
            json.dumps(lib), encoding="utf-8")
        spec = dict(lib)
        spec["defaults"] = {"palette": "deep", "grid": "true"}
        (tdp / "VIA_VAP_User_Workflow_Spec_v023.json").write_text(
            json.dumps(spec), encoding="utf-8")
        outp = tdp / "runtime.json"
        rc = run(tdp, outp)
        snap = json.loads(outp.read_text(encoding="utf-8"))
        chk("① 尾版解析雙件在(圖庫+工作流 spec;語意版號排序)",
            rc == 0 and snap["sources"]["chart_library"]["state"] == "OK"
            and snap["sources"]["workflow_spec"]["state"] == "OK")
        chk("② SSOT regex 驗證綠(值域全過)",
            snap["verdict"] == "GREEN"
            and snap["validation"]["chart_library"]["violations"] == 0)
        chk("③ runtime 合流(spec 新版覆蓋同鍵:palette=deep)",
            snap["runtime"]["defaults"]["palette"] == "deep"
            and snap["runtime"]["lock"]["visual"] is True)
        bad = dict(lib)
        bad["defaults"] = {"palette": "rainbow!", "grid": "true"}
        (tdp / "VIA_VAP_User_Workflow_Spec_v024.json").write_text(
            json.dumps(bad), encoding="utf-8")
        rc2 = run(tdp, outp)
        snap2 = json.loads(outp.read_text(encoding="utf-8"))
        chk("④ 違規誠實 RED+rc1(palette=rainbow! 不入綠)",
            rc2 == 1 and snap2["verdict"].startswith("RED")
            and any(r["state"] == "VIOLATION"
                    for r in snap2["validation"]["workflow_spec"]["rows"]))
        chk("⑤ v024>v023 尾版勝(語意排序)",
            snap2["sources"]["workflow_spec"]["file"]
            == "VIA_VAP_User_Workflow_Spec_v024.json")
        chk("⑥ 空收容誠實 rc2", run(tdp / "none_x", outp) == 2)
        chk("⑦ QA 證據鏈欄(缺=誠實 ABSENT)",
            snap2["qa_report"]["state"].startswith("ABSENT"))
    chk("⑧ 收容件原地不動宣告+衍生快照可重生",
        "原地不動" in src and "Runtime_v0100.json" in src)
    chk("⑨ 真收容對接(倉內圖庫在=實跑道通)",
        _newest("VAP_Chart_Library*.json") is not None)
    chk("⑩ 零網路+加速橋",
        all(("import " + k) not in src for k in ("requests", "httpx"))
        and "ACCEL-BRIDGE" in src)
    print(f"  [計] 十檢 OK {10 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 圖庫 SSOT 橋(VAP_ENG010)· 十檢自測(零網路)===")
        return selftest()
    if args and args[0] == "run":
        return run()
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
