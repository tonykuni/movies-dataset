"""Super BOM 模板 · 供電+散熱供應鏈（台達/康舒/雙鴻/奇鋐/健策/三集瑞各事業部各產品）。

在通用電子 BOM（bom_template.py）之上加三件事：
  1. 三維：Company / Business_Unit / Product_Family —— 一套模板跨公司、跨事業部、跨產品。
  2. 散熱品類擴充：熱導管/均溫板/均熱片/水冷板/微流道/分歧管/CDU/快接頭/水冷頭/水泵/風扇/鰭片/TIM/機殼/導線架/冷卻液。
  3. 公開產品家族登錄：各公司公開在做什麼（產品家族）——非機密 BOM。

安全界線（同前）：產品家族與品類骨架是公開產業知識；各公司實際 BOM/成本/供應商為機密，
留各自本機主權 SSOT。奇鋐與雙鴻是競爭對手——實際 BOM 絕不共池，只共用公開骨架。
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

from .bom_template import (FIELD_DICTIONARY, REQUIRED, COMMODITY_TAXONOMY,
                           validate_bom, build_tree, where_used, cost_rollup,
                           diff_bom, template_header)

# ── 公司 / 事業部 / 產品家族（公開資訊）────────────────────────
COMPANY_PROFILES = {
    "台達電 Delta": {
        "電源及零組件 Power & Components": ["PSU 電源", "adapter 變壓器", "DC-DC/brick", "CRPS 伺服器電源"],
        "散熱 Thermal (Fans & Thermal)": ["系統風扇", "散熱模組", "熱導管/均溫板"],
        "資料中心 Datacenter": ["PowerShelf/busbar", "UPS", "伺服器電源"],
        "電動車 EV": ["OBC 車載充電", "DC-DC", "牽引逆變器 traction inverter"],
        "工業自動化 Industrial Automation": ["變頻器 drive", "伺服 servo", "PLC"],
        "能源基礎設施 Energy Infra": ["PV inverter", "ESS 儲能"],
    },
    "康舒 AcBel": {
        "電源解決方案 Power Solutions": ["伺服器/雲端電源 CRPS", "33kW PowerShelf", "工業電源", "電信電源", "消費電源", "adapter"],
        "智慧綠能 Smart Green Energy": ["PV 太陽能", "智慧電表", "microgrid", "ESS"],
        "電動車電控 EV Powertrain": ["OBC", "DC-DC", "EV power module"],
    },
    "雙鴻 Auras": {
        "氣冷 Air Cooling": ["熱導管 heat pipe", "均溫板 vapor chamber", "散熱片 heatsink", "散熱模組"],
        "液冷 Liquid Cooling": ["水冷板 cold plate", "分歧管 manifold", "CDU", "快接頭 quick disconnect"],
        "消費 PC Thermal": ["PC 散熱器", "顯卡散熱"],
    },
    "奇鋐 AVC": {
        "氣冷 / 3D VC": ["3D 均溫板 3D VC", "熱導管", "散熱片"],
        "液冷 Liquid Cooling": ["水冷板 cold plate", "水冷頭 water block", "分歧管", "CDU", "雙向式水冷 dual-flow"],
        "風扇 Fan": ["高階風扇 fan"],
        "機殼 Chassis": ["伺服器機殼 server chassis", "機殼+散熱整合"],
    },
    "健策 Jentech (建策)": {
        "均熱片 Heat Spreader": ["均熱片 IHS", "CPU/GPU 均熱片"],
        "導線架 Leadframe": ["導線架 leadframe"],
        "微流道 MLCP": ["微流道冷板 microchannel", "MLCP"],
        "精密件 Precision": ["精密沖壓件"],
    },
    "建準 Sunon (若指建準)": {
        "風扇 Fan": ["DC 風扇", "鼓風機 blower", "風扇背牆 fan wall"],
        "液冷輔助 Liquid Assist": ["RPU", "水泵 pump", "氣冷輔助液冷櫃"],
    },
    "三集瑞-KY": {
        "電子零組件/散熱結構件 (公開細節有限)": ["散熱結構件", "電子零組件"],
    },
}

# ── 散熱品類擴充（通用工程知識，補在電子 BOM 品類骨架之上）──────
THERMAL_COMMODITY_TAXONOMY = {
    "散熱-氣冷 Thermal-Air": {
        "熱導管 Heat Pipe": ["熱導管", "heat pipe", "hp"],
        "均溫板 Vapor Chamber": ["均溫板", "vapor chamber", "3d vc", "vc"],
        "散熱片/鰭片 Heatsink/Fin": ["散熱片", "heatsink", "鰭片", "fin", "擠型"],
        "風扇 Fan": ["風扇", "fan", "blower", "鼓風機", "風扇背牆"],
    },
    "散熱-液冷 Thermal-Liquid": {
        "水冷板 Cold Plate": ["水冷板", "cold plate", "冷板"],
        "微流道 MLCP": ["微流道", "microchannel", "mlcp", "mccp", "mcl"],
        "分歧管 Manifold": ["分歧管", "manifold"],
        "CDU": ["cdu", "冷卻液分配", "coolant distribution"],
        "快接頭 Quick Disconnect": ["快接頭", "quick disconnect", "qd", "快拆"],
        "水冷頭 Water Block": ["水冷頭", "water block", "冷卻頭"],
        "水泵 Pump/RPU": ["水泵", "pump", "rpu", "幫浦"],
        "冷卻液 Coolant": ["冷卻液", "coolant", "工作流體"],
    },
    "散熱-界面/結構 Thermal-Interface/Struct": {
        "均熱片 Heat Spreader": ["均熱片", "heat spreader", "ihs"],
        "導熱介面 TIM": ["tim", "散熱膏", "導熱", "thermal interface", "導熱墊"],
        "導線架 Leadframe": ["導線架", "leadframe"],
        "機殼 Chassis": ["機殼", "chassis", "鈑金機構"],
    },
}


def merged_commodity_taxonomy() -> dict:
    """電子（通用）+ 散熱 兩套品類合併，供 super BOM 歸類。"""
    m = {**COMMODITY_TAXONOMY, **THERMAL_COMMODITY_TAXONOMY}
    return m


def classify_commodity_super(text: str) -> str:
    """跨電子+散熱兩域歸類。找不到回 '未分類'。"""
    t = (text or "").lower()
    for major, subs in merged_commodity_taxonomy().items():
        for sub, kws in subs.items():
            if any(k in t for k in kws):
                return f"{major} / {sub}"
    return "未分類 Unclassified"


# ── Super BOM 表頭 = 三維 + 通用 BOM 欄位 ─────────────────────
SUPER_DIMENSIONS = ["Company", "Business_Unit", "Product_Family"]
SUPER_REQUIRED = SUPER_DIMENSIONS + REQUIRED


def super_bom_header() -> list:
    return SUPER_DIMENSIONS + template_header()


def validate_super_bom(rows: list[dict]) -> dict:
    """先跑通用 BOM 驗證，再檢查三維必填。"""
    base = validate_bom(rows)
    issues = list(base["issues"])
    for i, r in enumerate(rows, 1):
        for f in SUPER_DIMENSIONS:
            if not str(r.get(f, "")).strip():
                issues.append({"row": i, "type": "缺維度", "field": f,
                               "pn": r.get("Item_PN", ""), "reason": f"{f} 為空"})
    hard = [x for x in issues if x.get("level") != "warn"]
    return {"pass": len(hard) == 0, "issues": issues,
            "stats": {**base["stats"], "errors": len(hard),
                      "warnings": len(issues) - len(hard)}}


def list_company_products() -> list:
    out = []
    for co, bus in COMPANY_PROFILES.items():
        for bu, fams in bus.items():
            out.append({"company": co, "business_unit": bu, "product_families": fams})
    return out


def coverage() -> dict:
    return {
        "companies": len(COMPANY_PROFILES),
        "business_units": sum(len(b) for b in COMPANY_PROFILES.values()),
        "product_families": sum(len(f) for b in COMPANY_PROFILES.values() for f in b.values()),
        "commodity_majors": len(merged_commodity_taxonomy()),
        "commodity_subs": sum(len(s) for s in merged_commodity_taxonomy().values()),
    }
