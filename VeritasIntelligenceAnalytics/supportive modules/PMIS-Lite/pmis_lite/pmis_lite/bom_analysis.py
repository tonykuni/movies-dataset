"""超詳細 BOM 分析引擎（對齊 M01_ItemMaster / M02_AML / M03_BOM_Structure）。

純 stdlib 實作 Gemini 計畫的遞迴展開與替代料成本滾算（等價於 DuckDB Recursive CTE
+ Polars group_by().first()），可測、離線：
  - explode：多階遞迴展開，累計用量 Accumulated_Qty + 路徑 Path + 階層 Level，防環。
  - cost_rollup：替代料(Alt_Group)決策（preference/lowest）→ 延伸成本 → 總機成本。
  - where_used：反查某料號被哪些父階使用。
  - compliance_rollup：RoHS 向上滾算（任一子件不合規 → 整機不合規）。
  - lead_time：關鍵採購交期（最長單件 lead）。
  - analyze：一次產出完整分析報告。
資料模型：
  item_master = {Item_ID: {desc, uom, state, rohs(bool), lead_days, std_cost}}
  aml         = [{item, maker, mpn, rank, price}]   # 同一 item 多筆＝替代供應商
  bom         = [{parent, child, qty, ref, alt}]     # alt＝替代群組（空＝必備料）
"""
from __future__ import annotations


def explode(bom, top, qty=1.0, _path=None, _level=1, _seen=None):
    """多階遞迴展開。回傳攤平清單，每列含 level/accumulated_qty/path。"""
    _path = _path or top
    _seen = _seen or {top}
    children = [r for r in bom if r["parent"] == top]
    out = []
    for r in children:
        c = r["child"]
        acc = qty * float(r.get("qty", 1))
        path = f"{_path} -> {c}"
        line = {"level": _level, "parent": top, "child": c,
                "qty_per": float(r.get("qty", 1)), "accumulated_qty": acc,
                "path": path, "alt": r.get("alt", ""), "ref": r.get("ref", "")}
        out.append(line)
        if c in _seen:                          # 防環：不再往下展
            line["cycle"] = True
            continue
        out.extend(explode(bom, c, acc, path, _level + 1, _seen | {c}))
    return out


def _decision_group(line):
    return line["alt"] or line["child"]         # 無替代群組 → 自身即群組


def cost_rollup(exploded, aml, item_master=None, strategy="preference"):
    """替代料決策 + 成本滾算。strategy: 'preference'(採購優先) 或 'lowest'(最低價)。"""
    price_by_item = {}
    for a in aml:
        price_by_item.setdefault(a["item"], []).append(a)
    chosen_lines, seen_groups = [], set()
    for ln in exploded:
        key = (ln["parent"], _decision_group(ln))
        if key in seen_groups:                  # 同群組已決策 → 跳過替代料
            continue
        seen_groups.add(key)
        cands = price_by_item.get(ln["child"], [])
        if item_master and ln["child"] in item_master and not cands:
            cands = [{"item": ln["child"], "maker": "STD", "mpn": "",
                      "rank": 1, "price": item_master[ln["child"]].get("std_cost", 0)}]
        if cands:
            pick = (min(cands, key=lambda x: x.get("rank", 99))
                    if strategy == "preference"
                    else min(cands, key=lambda x: x.get("price", 1e18)))
        else:
            pick = {"maker": "?", "mpn": "", "price": 0.0}
        ext = ln["accumulated_qty"] * float(pick.get("price", 0))
        chosen_lines.append({**ln, "maker": pick.get("maker", ""),
                             "unit_price": float(pick.get("price", 0)),
                             "extended_cost": round(ext, 4),
                             "alt_count": len(cands)})
    total = round(sum(l["extended_cost"] for l in chosen_lines), 2)
    return {"lines": chosen_lines, "total_cost": total, "strategy": strategy}


def where_used(bom, item):
    """反查：某料號被哪些父階直接使用。"""
    return sorted({r["parent"] for r in bom if r["child"] == item})


def compliance_rollup(exploded, item_master, field="rohs"):
    """RoHS 向上滾算：任一子件不合規 → 整機不合規。"""
    non = []
    for ln in exploded:
        im = item_master.get(ln["child"], {})
        if field in im and not im[field]:
            non.append(ln["child"])
    return {"compliant": len(non) == 0, "non_compliant": sorted(set(non)),
            "field": field}


def lead_time(exploded, item_master):
    """關鍵採購交期＝所有需求料件中最長單件 lead（平行採購假設）。"""
    leads = [(ln["child"], item_master.get(ln["child"], {}).get("lead_days", 0))
             for ln in exploded]
    if not leads:
        return {"critical_days": 0, "critical_item": None}
    item, days = max(leads, key=lambda x: x[1])
    return {"critical_days": days, "critical_item": item}


def analyze(bom, top, item_master, aml, strategy="preference"):
    """一次產出完整超詳細分析。"""
    ex = explode(bom, top)
    roll = cost_rollup(ex, aml, item_master, strategy)
    roll_low = cost_rollup(ex, aml, item_master, "lowest")
    comp = compliance_rollup(ex, item_master)
    lead = lead_time(ex, item_master)
    depth = max((l["level"] for l in ex), default=0)
    unique = sorted({l["child"] for l in ex})
    cycles = [l["child"] for l in ex if l.get("cycle")]
    # 品類/來源分佈（用 description 首字或 maker）
    return {
        "top": top, "total_lines": len(ex), "unique_parts": len(unique),
        "max_depth": depth,
        "total_cost_preference": roll["total_cost"],
        "total_cost_lowest": roll_low["total_cost"],
        "second_source_saving": round(roll["total_cost"] - roll_low["total_cost"], 2),
        "compliance": comp, "lead_time": lead,
        "cycles": cycles, "exploded": ex, "cost_lines": roll["lines"],
    }
