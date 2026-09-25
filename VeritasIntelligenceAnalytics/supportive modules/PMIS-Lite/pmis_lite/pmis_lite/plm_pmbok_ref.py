"""PLM 與 PMBOK 知識（同步進 SSOT，錨到唯一 canonical）。

PLM：生命週期、ECO/ECN、EBOM/MBOM、版次規則、料號主檔。
PMBOK：10 知識領域 + 5 流程群組。
每項附對應的 SSOT canonical，供同義字引擎對齊。
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

# ── PLM ────────────────────────────────────────────────
PLM_LIFECYCLE = ["Development 開發", "Growth 成長", "Maturity 成熟", "Decline 衰退/EOL"]

PLM_CONCEPTS = {
    "PLM-BOM-E": {"name": "EBOM 工程 BOM", "canon": "SSOT-BOM",
                  "note": "研發視角，依設計結構（電路/機構）"},
    "PLM-BOM-M": {"name": "MBOM 製造 BOM", "canon": "SSOT-BOM",
                  "note": "生產視角，含製程/替代料/包裝"},
    "PLM-ECO": {"name": "ECO 工程變更單", "canon": "SSOT-CHANGE",
                "note": "核准後的變更；SAP=AENR/Change Number"},
    "PLM-ECR": {"name": "ECR 工程變更請求", "canon": "SSOT-CHANGE",
                "note": "變更提案，核准後轉 ECO"},
    "PLM-REV": {"name": "Revision 版次控制", "canon": "SSOT-REVISION",
                "note": "只增不減：A→B→C，舊版存歷史"},
    "PLM-ITEM": {"name": "Item Master 料號主檔", "canon": "SSOT-ITEM",
                 "note": "CPN 廠內料號 + AML/AVL 供應商對應"},
    "PLM-STATE": {"name": "Lifecycle State", "canon": "SSOT-LIFECYCLE",
                  "note": "Active / EOL / Deprecated"},
}

# ── PMBOK：10 知識領域 ──────────────────────────────────
PMBOK_AREAS = {
    "PMBOK-INT": {"name": "Integration 整合管理", "canon": "SSOT-INTEGRATION"},
    "PMBOK-SCO": {"name": "Scope 範疇管理", "canon": "SSOT-SCOPE"},
    "PMBOK-SCH": {"name": "Schedule 時程管理", "canon": "SSOT-SCHEDULE"},
    "PMBOK-CST": {"name": "Cost 成本管理", "canon": "SSOT-COST"},
    "PMBOK-QUA": {"name": "Quality 品質管理", "canon": "SSOT-QUALITY"},
    "PMBOK-RES": {"name": "Resource 資源管理", "canon": "SSOT-RESOURCE"},
    "PMBOK-COM": {"name": "Communications 溝通管理", "canon": "SSOT-COMMS"},
    "PMBOK-RSK": {"name": "Risk 風險管理", "canon": "SSOT-RISK"},
    "PMBOK-PRO": {"name": "Procurement 採購管理", "canon": "SSOT-PROCUREMENT"},
    "PMBOK-STK": {"name": "Stakeholder 利害關係人管理", "canon": "SSOT-STAKEHOLDER"},
}

# ── PMBOK：5 流程群組 ───────────────────────────────────
PMBOK_PROCESS = ["Initiating 起始", "Planning 規劃", "Executing 執行",
                 "Monitoring & Controlling 監控", "Closing 結束"]

# ── MS Project 概念 → canonical（同步橋）──────────────────
MSPROJECT_MAP = {
    "Task": "SSOT-SCHEDULE", "Timeline": "SSOT-SCHEDULE", "Predecessor": "SSOT-SCHEDULE",
    "Resource": "SSOT-RESOURCE", "Assignment": "SSOT-RESOURCE",
    "Cost": "SSOT-COST", "Baseline": "SSOT-INTEGRATION", "WBS": "SSOT-SCOPE",
}


def sync_frameworks(syn) -> dict:
    """把 PLM/PMBOK/MSProject 的每個概念，透過其 canonical 對齊到唯一 SSOT。
    回傳對齊報告（哪些已錨定、哪些 canonical 不存在需補）。"""
    aligned, missing = [], []
    for src, table in (("PLM", PLM_CONCEPTS), ("PMBOK", PMBOK_AREAS)):
        for code, meta in table.items():
            canon = meta["canon"]
            if canon in syn.canonical:
                syn.add_synonym(meta["name"], canon)
                aligned.append({"src": src, "code": code, "canonical": canon})
            else:
                missing.append({"src": src, "code": code, "canonical": canon})
    for term, canon in MSPROJECT_MAP.items():
        if canon in syn.canonical:
            syn.add_synonym(term, canon)
            aligned.append({"src": "MSPROJECT", "code": term, "canonical": canon})
        else:
            missing.append({"src": "MSPROJECT", "code": term, "canonical": canon})
    return {"aligned": len(aligned), "missing": len(missing),
            "detail": aligned, "gaps": missing,
            "usable": len(missing) == 0}
