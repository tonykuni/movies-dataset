"""SAP BOM 知識庫（由使用者上傳圖卡編入 SSOT，供 MS Project↔BOM 同步時對照）。

三塊：BOM T-codes、替代 BOM 選擇邏輯(Q/D/V)、BOM 不展開的條件。
純資料 + 查詢函式；append-only。
"""
from __future__ import annotations

# ── SAP BOM T-Codes ────────────────────────────────────
TCODES = {
    "CS01": "Create BOM 建立 BOM",
    "CS02": "Change BOM 變更 BOM",
    "CS03": "Display BOM 顯示 BOM（檢查有效性）",
    "CS11": "BOM Explosion (Single Level) 單階展開",
    "CS12": "BOM Explosion (Multi Level) 多階展開",
    "CS13": "Display BOM with History 含歷史顯示",
    "CS14": "BOM Comparison BOM 比較",
    "CS15": "Where-Used List 反查用途（哪些父階用到此料）",
    "MM02": "Material Master 變更（MRP4 頁選 Q/D/V 選擇法）",
    "C223": "Define Production Version 定義生產版本",
}

# ── 替代 BOM 選擇邏輯（MRP 只會選一張 BOM）Q / D / V ──────
ALT_BOM_SELECTION = {
    "Q": {"name": "Order Quantity (Lot Size) 數量/批量",
          "cue": "生產多少？", "logic": "批量落在哪張 BOM 的數量區間 → 選那張",
          "field": "MM02 · MRP4 · Selection method"},
    "D": {"name": "Explosion Date 展開日期",
          "cue": "何時生產？", "logic": "依計畫訂單日期，選當時有效的 BOM（標準包裝）",
          "field": "MM02 · MRP4 · Explosion date"},
    "V": {"name": "Production Version 生產版本",
          "cue": "鎖定哪種生產方法？", "logic": "由生產版本綁定 BOM+途程（C223 定義）",
          "field": "C223 · Production Version"},
}

STICKY = {"Q": "Quantity 批量", "D": "Date 展開日", "V": "Version 生產版本"}

# ── BOM 不展開的四種情況 ────────────────────────────────
NOT_EXPLODED = [
    {"stage": "無有效 BOM", "detail": "在需求展開日、或給定有效性參數下，沒有生效的 BOM"},
    {"stage": "BOM 有刪除指示", "detail": "BOM 被標記刪除/停用指示（deletion indicator）"},
    {"stage": "多 BOM 無適用替代", "detail": "多張 BOM 但沒有符合批量的替代 BOM"},
    {"stage": "BOM 不符應用準則", "detail": "BOM usage 不符、展開日無有效替代、狀態不滿足需求"},
]


def tcode(code: str) -> str:
    return TCODES.get(code.upper(), "未知 T-code")


def select_bom_method(has_pv: bool, lot_size_ranges: bool) -> str:
    """依情況建議 Q/D/V。有生產版本→V；有批量區間→Q；否則→D。"""
    if has_pv:
        return "V"
    if lot_size_ranges:
        return "Q"
    return "D"


def explode_blocked_reason(effective: bool, deletion: bool,
                           alt_matches_lot: bool, usage_ok: bool) -> dict:
    """判斷 BOM 是否會被展開；不展開時回傳阻擋原因。"""
    if not effective:
        return {"exploded": False, "reason": NOT_EXPLODED[0]}
    if deletion:
        return {"exploded": False, "reason": NOT_EXPLODED[1]}
    if not alt_matches_lot:
        return {"exploded": False, "reason": NOT_EXPLODED[2]}
    if not usage_ok:
        return {"exploded": False, "reason": NOT_EXPLODED[3]}
    return {"exploded": True, "reason": None}


def as_registry() -> list:
    """輸出成 SSOT 登錄列（append-only）。"""
    rows = []
    for c, d in TCODES.items():
        rows.append({"code": f"SAP-TCODE-{c}", "type": "tcode", "name": d})
    for k, v in ALT_BOM_SELECTION.items():
        rows.append({"code": f"SAP-ALTBOM-{k}", "type": "selection", "name": v["name"]})
    for i, n in enumerate(NOT_EXPLODED, 1):
        rows.append({"code": f"SAP-NOEXP-{i:02d}", "type": "not_exploded", "name": n["stage"]})
    return rows
