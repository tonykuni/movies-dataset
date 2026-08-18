#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
via_support_import_audit_v0100 — 功能性引擎 × 支援性模組導入稽核(唯讀)
=========================================================================
令:「確定所有功能性引擎都有導入支援性模組」。
掃描 VDF/VRN/VAP 功能引擎 .py,檢測支援模組導入(四型合法態),誠實分級:
  BRIDGE   : VRN_SupportBridge 橋接(統一導入 SSOT/Aegis/Celeritas/super)或
             [VIA:ANCHOR:SUPPORT:BOOTSTRAP] 錨點在檔 — 規範完整態
  DIRECT   : 靜態 import ≥1 個支援核心模組(未走橋)
  DYNAMIC  : importlib 插件載入(核心模組名以字串出現 + importlib/spec_from_file
             — MDL004/005 §5 Plugin Loader 型)
  SSOT-DATA: SSOT 資料層整合(讀 spec/ssot/vap_spec.json 等 — VAP 唯一真相型)
  NONE     : 四型皆無(候接橋;誠實列名,不假綠)
支援核心 7 模組(與 VDF_DataHub_Orchestrator EXPECTED 對齊)+ 橋:
  VIA_SSOT_Unified · VeritasAegisNexus · VeritasCeleritas · VIA_EnvManager ·
  VIA_RegistryCore_v1 · VIA_Panorama_AST_RuntimeInjector · VIA_Runtime_Bridge_All_in_One
  橋:VRN_SupportBridge / super_engine
唯讀:不改任何引擎;報表落 supportive modules/audit_tools/(追蹤存證)。
用法:py via_support_import_audit_v0100.py [--json] [--out-dir DIR]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent  # VeritasIntelligenceAnalytics

CORE = [
    "VIA_SSOT_Unified", "VeritasAegisNexus", "VeritasCeleritas", "VIA_EnvManager",
    "VIA_RegistryCore_v1", "VIA_Panorama_AST_RuntimeInjector", "VIA_Runtime_Bridge_All_in_One",
]
BRIDGE_MARKS = ["VRN_SupportBridge", "super_engine"]
ANCHOR = "[VIA:ANCHOR:SUPPORT:BOOTSTRAP"

SCAN_AREAS = [
    ("VDF",        "functional modules/VDF",        "*.py", "現役"),
    ("VDF/engine", "functional modules/VDF/engine", "*.py", "原件保存區"),
    ("VRN",        "functional modules/VRN",        "*.py", "現役"),
    ("VAP/engine", "functional modules/VAP/engine", "*.py", "現役"),
]
EXCLUDE_DIRS = {"__pycache__", "_superseded", "_rebuilds_superseded", "_bytecode_originals", "candidates"}
IMPORT_RE = re.compile(r"^\s*(?:import|from)\s+([A-Za-z_][A-Za-z0-9_]*)", re.M)


def audit_file(p: Path) -> dict:
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return {"file": p.name, "grade": "READ_ERROR", "detail": str(exc), "core": [], "bridge": []}
    imported = set(IMPORT_RE.findall(text))
    core_hits = [c for c in CORE if c in imported or re.search(rf"import\s+{re.escape(c)}\b", text)]
    bridge_hits = [b for b in BRIDGE_MARKS if re.search(rf"(?:import|from)\s+{re.escape(b)}\b", text)]
    has_anchor = ANCHOR in text
    # DYNAMIC:插件載入(核心名以字串現身 + importlib 機制在檔)— MDL004/005 §5 型
    has_importlib = ("importlib" in text) or ("spec_from_file_location" in text) or ("__import__" in text)
    dyn_hits = [c for c in CORE if c not in core_hits and c in text] if has_importlib else []
    # SSOT-DATA:SSOT 資料層(VAP 唯一真相型)
    ssot_data = bool(re.search(r"spec[/\\]ssot|vap_spec\.json|vap_chartlib\.json|ssot_dir", text))
    if bridge_hits or has_anchor:
        grade = "BRIDGE"
    elif core_hits:
        grade = "DIRECT"
    elif dyn_hits:
        grade = "DYNAMIC"
    elif ssot_data:
        grade = "SSOT-DATA"
    else:
        grade = "NONE"
    return {"file": p.name, "grade": grade, "anchor": has_anchor,
            "core": core_hits, "bridge": bridge_hits, "dynamic": dyn_hits,
            "ssot_data": ssot_data, "lines": text.count("\n") + 1}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true", help="只印 JSON(排程用)")
    ap.add_argument("--out-dir", default=str(VIA / "supportive modules" / "audit_tools"))
    args = ap.parse_args()

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    areas = []
    for name, rel, pat, kind in SCAN_AREAS:
        root = VIA / rel
        if not root.is_dir():
            areas.append({"area": name, "kind": kind, "missing_dir": True, "files": []})
            continue
        files = sorted(
            p for p in root.glob(pat)
            if p.is_file() and not any(part in EXCLUDE_DIRS for part in p.parts)
        )
        areas.append({"area": name, "kind": kind, "files": [audit_file(p) for p in files]})

    all_rows = [(a["area"], a["kind"], f) for a in areas for f in a.get("files", [])]
    n = {g: sum(1 for _, _, f in all_rows if f["grade"] == g)
         for g in ("BRIDGE", "DIRECT", "DYNAMIC", "SSOT-DATA", "NONE", "READ_ERROR")}
    total = len(all_rows)
    payload = {
        "schema": "via.support_import_audit.v1", "ts": ts, "readonly": True,
        "core_modules": CORE, "bridge_marks": BRIDGE_MARKS,
        "total_engines": total, "counts": n, "areas": areas,
        "verdict": "ALL_IMPORTED" if n["NONE"] == 0 and n["READ_ERROR"] == 0 else "GAPS_FOUND",
    }
    out = Path(args.out_dir) / f"VIA_SupportImport_Audit_{ts}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")

    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
        return 0 if payload["verdict"] == "ALL_IMPORTED" else 1

    print(f"=== 功能引擎 × 支援模組導入稽核 v0100(唯讀)· 引擎 {total} ===")
    for a in areas:
        files = a.get("files", [])
        if not files:
            continue
        cnt = {g: sum(1 for f in files if f["grade"] == g)
               for g in ("BRIDGE", "DIRECT", "DYNAMIC", "SSOT-DATA", "NONE")}
        seg = " / ".join(f"{g} {v}" for g, v in cnt.items() if v)
        print(f"  ── {a['area']}({a['kind']})· {len(files)} 檔 · {seg} ──")
        for f in files:
            mark = {"BRIDGE": "橋接", "DIRECT": "直連", "DYNAMIC": "插件",
                    "SSOT-DATA": "資料", "NONE": "未導入", "READ_ERROR": "讀取錯"}[f["grade"]]
            det = ("橋=" + ",".join(f["bridge"])) if f["bridge"] else (
                "核心=" + ",".join(f["core"][:3]) if f["core"] else (
                "插件=" + ",".join(f.get("dynamic", [])[:3]) if f.get("dynamic") else (
                "SSOT-JSON" if f.get("ssot_data") else "—")))
            if f.get("anchor"):
                det += " +錨點"
            flag = "→" if f["grade"] in ("NONE", "READ_ERROR") else "  "
            print(f"   {flag}[{mark:3s}] {f['file']:<52s} {det}")
    print("  " + "-" * 66)
    print(f"  合計:BRIDGE {n['BRIDGE']} · DIRECT {n['DIRECT']} · DYNAMIC {n['DYNAMIC']}"
          f" · SSOT-DATA {n['SSOT-DATA']} · NONE {n['NONE']}"
          + (f" · READ_ERROR {n['READ_ERROR']}" if n["READ_ERROR"] else ""))
    print(f"  判定:{payload['verdict']}(誠實口徑;NONE=候接橋,不假綠)")
    print(f"  存證:{out}")
    return 0 if payload["verdict"] == "ALL_IMPORTED" else 1


if __name__ == "__main__":
    sys.exit(main())
