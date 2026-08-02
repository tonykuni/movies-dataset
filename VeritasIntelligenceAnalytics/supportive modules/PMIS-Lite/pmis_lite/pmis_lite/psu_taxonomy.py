"""電源供應器(PSU)行業標準骨架 — 公開通用知識，非任何一家機密 BOM。

用途：當工具面對任一台灣電源廠（台達/康舒/海韻/全漢/光寶/群電/新巨/曜越…）時，
先載入這套「行業辭典」，冷啟動就已經懂電源業 → 歸類率高、不遺漏。

安全界線（重要）：
  - 這裡只有『公開的產業分類骨架』（產品類別、標準電路結構、通用零組件類別）。
  - 任何一家的『實際 BOM / 料號 / 供應商價格』都是機密，留在各自本機主權 SSOT。
  - 龍頭(台達)先拆出標準骨架 → 次龍頭套同一骨架 → 各家實際資料各自增量。
  - append-only：新出現的類別/零組件只增不減，行業骨架持續長大。
"""
from __future__ import annotations

# 產品類別（依應用分）— 跨公司高度重疊
PSU_PRODUCT_CATEGORIES = {
    "消費PC電源 Consumer PC PSU": ["atx", "sfx", "80 plus", "modular", "桌機電源"],
    "電競電源 Gaming PSU": ["rgb", "gaming", "電競", "全模組", "白金牌", "鈦金牌"],
    "伺服器電源 Server CRPS": ["crps", "server", "伺服器", "冗餘", "redundant", "hot swap", "熱插拔"],
    "資料中心電源 Datacenter / PowerShelf": ["power shelf", "powershelf", "rack", "機櫃", "33kw", "5.5kw", "busbar"],
    "工業電源 Industrial PSU": ["din rail", "工業", "industrial", "導軌"],
    "醫療電源 Medical PSU": ["medical", "醫療", "2moopp", "iec 60601"],
    "電信整流 Telecom Rectifier": ["-48v", "telecom", "基地台", "電信電源"],
    "外接變壓器 Adapter": ["adapter", "notebook", "筆電充電", "筆電變壓器"],
    "電動車電源 EV Power": ["obc", "on-board charger", "車載充電", "dc-dc", "ev", "電動車"],
    "LED驅動 LED Driver": ["led driver", "led 驅動", "恆流"],
}

# 標準電路結構 / 子組件（BOM 層級）— 電源設計通用，跨公司幾乎一致
PSU_STRUCTURE = {
    "輸入EMI濾波 EMI Filter": ["emi", "共模", "common mode", "x cap", "y cap", "突波", "mov"],
    "輸入整流 Input Rectifier": ["橋式整流", "bridge rectifier", "整流橋"],
    "功率因數校正 PFC": ["pfc", "功因", "boost", "升壓"],
    "主轉換 Main Converter": ["llc", "諧振", "resonant", "flyback", "返馳", "forward", "phase shift", "全橋"],
    "主變壓器 Main Transformer": ["transformer", "變壓器", "磁性元件", "magnetics", "繞線"],
    "同步整流 Sync Rectification": ["同步整流", "sync rect", "sr", "二次側"],
    "輸出濾波 Output Filter": ["輸出電容", "output cap", "扼流圈", "inductor", "漣波", "ripple"],
    "控制IC Control": ["pwm", "控制ic", "controller", "dsp", "回授", "feedback", "opto", "光耦"],
    "保護電路 Protection": ["ovp", "ocp", "otp", "scp", "過壓", "過流", "過溫", "短路保護"],
    "散熱 Thermal": ["散熱片", "heatsink", "風扇", "fan", "散熱", "溫度"],
    "待機電源 Standby": ["5vsb", "待機", "standby", "輔助電源"],
    "機構 Mechanical": ["外殼", "housing", "機構", "pcb", "連接器", "connector", "線材", "harness"],
}

# 關鍵零組件類別 — 採購/BOM 常見，跨公司重疊最高（成本與交期風險集中處）
PSU_COMPONENTS = {
    "功率開關 Power Switch": ["mosfet", "gan", "sic", "igbt", "功率晶體"],
    "功率二極體 Power Diode": ["sbr", "sic diode", "蕭特基", "快恢復"],
    "磁性元件 Magnetics": ["transformer", "inductor", "choke", "變壓器", "電感", "扼流圈"],
    "電容 Capacitor": ["電解電容", "electrolytic", "薄膜電容", "film cap", "陶瓷電容", "mlcc", "bulk cap"],
    "控制IC Control IC": ["pwm ic", "pfc controller", "controller", "微控制器", "mcu"],
    "光耦 Optocoupler": ["光耦", "optocoupler", "隔離"],
    "散熱件 Thermal Part": ["散熱片", "heatsink", "導熱", "風扇", "fan"],
    "連接器 Connector": ["連接器", "connector", "端子", "線材"],
    "PCB": ["pcb", "電路板", "基板", "多層板"],
    "被動保護 Passive/Protect": ["ntc", "mov", "fuse", "保險絲", "突波吸收"],
}


def build_psu_seed():
    """把行業骨架轉成分類種子（product/topic/component 三維），供 seed 冷啟動。"""
    return {
        "product": {k: v for k, v in PSU_PRODUCT_CATEGORIES.items()},
        "topic": {k: v for k, v in PSU_STRUCTURE.items()},
        "component": {k: v for k, v in PSU_COMPONENTS.items()},
    }


def coverage_summary():
    return {
        "product_categories": len(PSU_PRODUCT_CATEGORIES),
        "structure_stages": len(PSU_STRUCTURE),
        "component_classes": len(PSU_COMPONENTS),
        "total_seed_terms": sum(len(v) for d in (PSU_PRODUCT_CATEGORIES, PSU_STRUCTURE, PSU_COMPONENTS) for v in d.values()),
    }
