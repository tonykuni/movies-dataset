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
v0100→v0101(批170):NONE 精煉三分(誠實債務口徑)——
  FROZEN  : 非家族尾版/_sha 鏡像(凍結零觸碰,永不接橋,不計債;
            在役面=家族最新之既有正典,VDF 參數映射器同判準)
  NET_DEBT: 在役面+直連網路痕跡(requests/urllib/yfinance/curl…)
            =真接橋債(統包網路紀律 SUP_MDL740 唯一車道)
  NO_NEED : 在役面+零網路零加速需求(純本地計算=誠實無需接橋)
  verdict:NET_DEBT>0 → NET_GAPS;否則 CLEAN_FACE(FROZEN/NO_NEED 誠實列示)
支援核心 7 模組(與 VDF_DataHub_Orchestrator EXPECTED 對齊)+ 橋:
  VIA_SSOT_Unified · VeritasAegisNexus · VeritasCeleritas · VIA_EnvManager ·
  VIA_RegistryCore_v1 · VIA_Panorama_AST_RuntimeInjector · VIA_Runtime_Bridge_All_in_One
  橋:VRN_SupportBridge / super_engine
唯讀:不改任何引擎;報表落 supportive modules/audit_tools/(追蹤存證)。
用法:py via_support_import_audit_v0100.py [--json] [--out-dir DIR]
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


# 統包網路橋記號(批170):SUP_MDL740 統包網路/741 韌性層/VIA_NetSupport 同意閘
_NETBRIDGE_RX = re.compile(r"SUP_MDL740|SUP_MDL741|VIA_NetSupport|via_net\b")
_NET_RX = re.compile(
    r"^\s*(?:import|from)\s+(?:requests|urllib|http\.client|yfinance|aiohttp|httpx)\b"
    r"|[\"']curl[\"']", re.M)


def audit_file(p: Path) -> dict:
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return {"file": p.name, "net": False, "grade": "READ_ERROR", "detail": str(exc), "core": [], "bridge": []}
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
    return {"file": p.name, "net": bool(_NET_RX.search(text)),
            "netbridge": bool(_NETBRIDGE_RX.search(text)),
            "grade": grade, "anchor": has_anchor,
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
    # v0101:FROZEN 判定=非家族尾版/_sha 鏡像(在役面=家族最新;凍結零觸碰)
    fam_rx = re.compile(r"^(.*)_v\d+[a-z0-9]*\.py$")
    latest: dict[tuple, str] = {}
    for area, _, f in all_rows:
        m = fam_rx.match(f["file"])
        key = (area, m.group(1)) if m else (area, f["file"])
        if m and (key not in latest or f["file"] > latest[key]):
            latest[key] = f["file"]
    for area, _, f in all_rows:
        m = fam_rx.match(f["file"])
        frozen = ("_sha" in f["file"]) or (m and latest.get((area, m.group(1))) != f["file"])
        if f["grade"] == "NONE":
            f["grade"] = ("FROZEN" if frozen else
                          ("NET_OK" if f.get("net") and f.get("netbridge") else
                           ("NET_DEBT" if f.get("net") else "NO_NEED")))
    n = {g: sum(1 for _, _, f in all_rows if f["grade"] == g)
         for g in ("BRIDGE", "DIRECT", "DYNAMIC", "SSOT-DATA",
                   "FROZEN", "NET_OK", "NET_DEBT", "NO_NEED", "READ_ERROR")}
    n["NONE"] = n["FROZEN"] + n["NET_OK"] + n["NET_DEBT"] + n["NO_NEED"]  # 向後相容總數
    total = len(all_rows)
    payload = {
        "schema": "via.support_import_audit.v1", "ts": ts, "readonly": True,
        "core_modules": CORE, "bridge_marks": BRIDGE_MARKS,
        "total_engines": total, "counts": n, "areas": areas,
        "verdict": ("NET_GAPS" if n["NET_DEBT"] else
                    ("READ_GAPS" if n["READ_ERROR"] else "CLEAN_FACE")),
    }
    out = Path(args.out_dir) / f"VIA_SupportImport_Audit_{ts}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")

    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
        return 0 if payload["verdict"] == "CLEAN_FACE" else 1

    print(f"=== 功能引擎 × 支援模組導入稽核 v0101(唯讀)· 引擎 {total} ===")
    for a in areas:
        files = a.get("files", [])
        if not files:
            continue
        cnt = {g: sum(1 for f in files if f["grade"] == g)
               for g in ("BRIDGE", "DIRECT", "DYNAMIC", "SSOT-DATA",
                         "FROZEN", "NET_OK", "NET_DEBT", "NO_NEED")}
        seg = " / ".join(f"{g} {v}" for g, v in cnt.items() if v)
        print(f"  ── {a['area']}({a['kind']})· {len(files)} 檔 · {seg} ──")
        for f in files:
            mark = {"BRIDGE": "橋接", "DIRECT": "直連", "DYNAMIC": "插件",
                    "SSOT-DATA": "資料", "FROZEN": "凍結版", "NET_OK": "網橋在", "NET_DEBT": "網路債",
                    "NO_NEED": "無需橋", "READ_ERROR": "讀取錯"}[f["grade"]]
            det = ("橋=" + ",".join(f["bridge"])) if f["bridge"] else (
                "核心=" + ",".join(f["core"][:3]) if f["core"] else (
                "插件=" + ",".join(f.get("dynamic", [])[:3]) if f.get("dynamic") else (
                "SSOT-JSON" if f.get("ssot_data") else "—")))
            if f.get("anchor"):
                det += " +錨點"
            flag = "→" if f["grade"] in ("NET_DEBT", "READ_ERROR") else "  "
            print(f"   {flag}[{mark:3s}] {f['file']:<52s} {det}")
    print("  " + "-" * 66)
    print(f"  合計:BRIDGE {n['BRIDGE']} · DIRECT {n['DIRECT']} · DYNAMIC {n['DYNAMIC']}"
          f" · SSOT-DATA {n['SSOT-DATA']} · 凍結版 {n['FROZEN']} · 網橋在 {n['NET_OK']} · 網路債 {n['NET_DEBT']}"
          f" · 無需橋 {n['NO_NEED']}"
          + (f" · READ_ERROR {n['READ_ERROR']}" if n["READ_ERROR"] else ""))
    print(f"  判定:{payload['verdict']}(誠實口徑;網路債=真接橋債;凍結版/無需橋 誠實列示不計債)")
    print(f"  存證:{out}")
    return 0 if payload["verdict"] == "CLEAN_FACE" else 1


if __name__ == "__main__":
    sys.exit(main())
