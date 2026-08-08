"""台灣電子零組件業 · 通用 BOM 模板引擎（純 Python、離線、可驗證）。

設計目標：一套模板通吃電子業各廠——多階 BOM、替代料、AVL、位號、合規、變更控制，
且接得上 AUTO SSOT（料號原始不動 + 系統自動編碼、append-only、ECN 串接）。

不遺漏不出包：validate_bom 沿用完整性哲學——每個缺口都要有原因，缺必填就 FAIL。
"""
from __future__ import annotations

from collections import defaultdict

# ── A. BOM 欄位字典（分九群；★=必填）──────────────────────────
FIELD_DICTIONARY = {
    "階層 Hierarchy": {
        "Level": "階層層級（0=成品，往下遞增）★",
        "Parent_PN": "母件料號（頂層可空）",
        "Find_No": "項次序號",
    },
    "品項識別 Identity": {
        "Item_PN": "內部料號（原始不動，系統另編）★",
        "Description": "品名說明 ★",
        "Mfr": "製造商",
        "Mfr_PN": "原廠料號 MPN",
        "Commodity": "品類（見 COMMODITY_TAXONOMY）★",
    },
    "用量 Usage": {
        "Qty": "用量 ★",
        "UOM": "單位（PC/M/KG…）★",
        "Ref_Des": "位號/位置參考（如 R1,R2,C5）",
    },
    "採購供應 Sourcing": {
        "Vendor": "供應商",
        "AVL": "合格供應商清單",
        "Alt_Group": "替代料群組碼（同群可互換）",
        "Sourcing_Status": "單一源/雙源/多源",
        "Lead_Time": "交期（天）",
    },
    "技術規格 Spec": {
        "Value": "規格值（如 10k、100uF）",
        "Tolerance": "公差（如 ±1%）",
        "Package": "封裝（0402/QFN…）",
        "Rating": "額定（電壓/電流/功率）",
        "Temp_Grade": "溫度等級",
    },
    "生命週期 Lifecycle": {
        "Item_Status": "Active/NRND/EOL/Obsolete ★",
        "RoHS": "RoHS 符合 ★(外銷)",
        "REACH": "REACH 符合",
        "Halogen_Free": "無鹵",
        "MSL": "濕敏等級",
    },
    "成本 Cost": {
        "Unit_Cost": "單價",
        "Currency": "幣別",
        "Cost_Roll": "累計成本（子件滾算到母件）",
    },
    "變更控制 Change": {
        "Rev": "版次 ★",
        "ECN_No": "工程變更單號（為什麼改，串 PLM）",
        "Eff_From": "生效日",
        "Eff_To": "失效日",
    },
    "追溯 Trace": {
        "Where_Used": "被用於（反查，系統自算）",
        "Created_By": "建立者",
        "Created_At": "建立時間",
    },
}

REQUIRED = ["Level", "Item_PN", "Description", "Commodity", "Qty", "UOM",
            "Item_Status", "RoHS", "Rev"]

# ── B. 品類骨架（台灣電子業通用）──────────────────────────────
COMMODITY_TAXONOMY = {
    "主動元件 Active": {
        "IC": ["mcu", "mpu", "memory", "flash", "analog ic", "power ic", "pmic", "opamp"],
        "電晶體 Transistor": ["mosfet", "bjt", "igbt", "gan", "sic"],
        "二極體 Diode": ["diode", "schottky", "zener", "tvs", "rectifier"],
    },
    "被動元件 Passive": {
        "電阻 Resistor": ["resistor", "電阻", "chip r", "0402", "0603"],
        "電容 Capacitor": ["mlcc", "電容", "電解", "tantalum", "film cap", "陶瓷"],
        "電感 Inductor": ["inductor", "電感", "bead", "磁珠", "choke", "扼流"],
        "晶振 Crystal": ["crystal", "晶振", "oscillator", "石英"],
    },
    "電磁機構 Electromechanical": {
        "連接器 Connector": ["connector", "連接器", "端子", "header", "socket"],
        "繼電器 Relay": ["relay", "繼電器"],
        "開關 Switch": ["switch", "開關", "按鍵"],
        "變壓器 Transformer": ["transformer", "變壓器", "磁性"],
    },
    "機構件 Mechanical": {
        "外殼 Housing": ["housing", "外殼", "機殼", "鈑金", "塑膠件"],
        "散熱 Thermal": ["heatsink", "散熱片", "tim", "導熱", "風扇"],
        "緊固 Fastener": ["screw", "螺絲", "螺帽", "墊片"],
        "標籤 Label": ["label", "標籤", "貼紙"],
    },
    "板類 Board": {
        "PCB": ["pcb", "電路板", "裸板", "多層板"],
        "軟板 FPC": ["fpc", "軟板", "flex"],
    },
    "線材 Cable": {
        "線束 Harness": ["harness", "線束", "wire"],
        "排線 FFC": ["ffc", "排線", "cable"],
    },
    "其他 Others": {
        "原材料 Raw": ["raw", "原料", "膠", "焊錫"],
        "包材 Packaging": ["packaging", "包材", "紙箱", "泡棉"],
        "軟韌體 Firmware": ["firmware", "韌體", "sw", "software"],
    },
}


def classify_commodity(text: str) -> str:
    """依關鍵字把品項歸到品類（大類/子類）。找不到回 '未分類'。"""
    t = (text or "").lower()
    for major, subs in COMMODITY_TAXONOMY.items():
        for sub, kws in subs.items():
            if any(k in t for k in kws):
                return f"{major} / {sub}"
    return "未分類 Unclassified"


# ── C. 驗證（不遺漏不出包）───────────────────────────────────
def validate_bom(rows: list[dict]) -> dict:
    """回傳 {pass, issues, stats}。每個問題都有原因，缺必填就 FAIL。"""
    issues = []
    pns = set()
    parents = set()
    for i, r in enumerate(rows, 1):
        for f in REQUIRED:
            if not str(r.get(f, "")).strip():
                issues.append({"row": i, "type": "缺必填", "field": f,
                               "pn": r.get("Item_PN", ""), "reason": f"{f} 為空"})
        pn = r.get("Item_PN", "")
        if pn:
            pns.add(pn)
        if r.get("Parent_PN"):
            parents.add(r["Parent_PN"])
        # 位號數 vs 用量（有 Ref_Des 才檢）
        rd = r.get("Ref_Des", "")
        if rd and str(r.get("Qty", "")).strip():
            try:
                if len([x for x in rd.replace(" ", "").split(",") if x]) != int(float(r["Qty"])):
                    issues.append({"row": i, "type": "位號≠用量", "pn": pn,
                                   "reason": f"位號數與 Qty={r['Qty']} 不符"})
            except Exception:
                pass
        # 單一供應源風險（標記，非錯誤）
        if str(r.get("Sourcing_Status", "")).strip() in ("單一源", "single", "sole"):
            issues.append({"row": i, "type": "供應風險", "pn": pn, "level": "warn",
                           "reason": "單一供應源，建議尋二源"})
    # 孤兒母件：被引用為 parent 但自己不在料號集
    for p in parents:
        if p not in pns:
            issues.append({"type": "孤兒母件", "pn": p, "reason": f"母件 {p} 未定義"})
    hard = [x for x in issues if x.get("level") != "warn"]
    return {
        "pass": len(hard) == 0,
        "issues": issues,
        "stats": {"rows": len(rows), "items": len(pns),
                  "errors": len(hard), "warnings": len(issues) - len(hard)},
    }


# ── D. BOM 樹操作（純 Python）────────────────────────────────
def build_tree(rows: list[dict]) -> dict:
    """回傳 parent_pn -> [child rows]。頂層 parent 為 ''。"""
    tree = defaultdict(list)
    for r in rows:
        tree[r.get("Parent_PN", "") or ""].append(r)
    return dict(tree)


def where_used(rows: list[dict], target_pn: str) -> list:
    """反查：某料件被哪些母件使用（含間接，往上追）。"""
    child2parent = {}
    for r in rows:
        child2parent.setdefault(r.get("Item_PN"), r.get("Parent_PN", ""))
    chain, cur = [], target_pn
    while cur and child2parent.get(cur):
        p = child2parent[cur]
        if not p or p in chain:
            break
        chain.append(p)
        cur = p
    return chain


def cost_rollup(rows: list[dict]) -> dict:
    """子件成本 × 用量 累計到母件。回傳 pn -> 累計成本。"""
    tree = build_tree(rows)
    pn2row = {r.get("Item_PN"): r for r in rows}

    def roll(pn):
        total = 0.0
        for child in tree.get(pn, []):
            cpn = child.get("Item_PN")
            try:
                qty = float(child.get("Qty", 0) or 0)
                unit = float(child.get("Unit_Cost", 0) or 0)
            except Exception:
                qty, unit = 0, 0
            sub = roll(cpn) if tree.get(cpn) else 0.0
            total += (sub if sub else unit) * qty
        return total

    tops = [r.get("Item_PN") for r in tree.get("", [])]
    return {t: round(roll(t), 2) for t in tops}


def diff_bom(old_rows: list[dict], new_rows: list[dict]) -> dict:
    """比對兩版 BOM（給 ECN 用）：新增/刪除/用量變更。"""
    o = {r.get("Item_PN"): r for r in old_rows}
    n = {r.get("Item_PN"): r for r in new_rows}
    added = [k for k in n if k not in o]
    removed = [k for k in o if k not in n]
    changed = []
    for k in n:
        if k in o and str(o[k].get("Qty")) != str(n[k].get("Qty")):
            changed.append({"pn": k, "from": o[k].get("Qty"), "to": n[k].get("Qty")})
    return {"added": added, "removed": removed, "qty_changed": changed}


def template_header() -> list:
    """回傳所有欄位（扁平），供產生 CSV/Excel 模板表頭。"""
    return [f for grp in FIELD_DICTIONARY.values() for f in grp]
