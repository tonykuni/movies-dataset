"""財務驗證閘門 + 成本結構 + 校準 + 同業比較。

核心治理：季/半年/年報自動擷取的數據「先未驗證、通過會計恆等式檢查才可用」。
  - verify_report：資產=負債+權益、損益逐層加總、CF 相符…全過才 usable=True。
  - cost_structure：單位變動成本/固定成本 → 貢獻邊際、損益兩平、安全邊際、營運槓桿。
  - calibrate：由下而上估算 vs 由上而下實際，算差異、判斷是否在容忍內（努力趨近）。
  - peer_table：同業各指標正規化比較 + 排名。
全部確定性、離線、可測。
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


def _close(a, b, tol_abs=1.0, tol_rel=0.01):
    if a is None or b is None:
        return True
    return abs(a - b) <= max(tol_abs, tol_rel * max(abs(a), abs(b)))


def verify_report(d: dict) -> dict:
    """會計恆等式驗證。回傳 {usable, checks[]}；全部硬檢查過才 usable=True。

    d 需含（缺者略過該檢查）：revenue,cogs,grossProfit,opex,opInc,pretax,tax,netInc,
    cash,ar,inventory,otherCA,ca,ppe,otherNCA,ta,ap,otherCL,cl,longDebt,tl,equity,
    cfo,cfi,cff,netCF。
    """
    checks = []

    def chk(name, cond, detail, hard=True):
        checks.append({"name": name, "ok": bool(cond), "detail": detail, "hard": hard})

    g = d.get
    # 1) 資產負債表平衡（最重要）
    if g("ta") is not None and g("tl") is not None and g("equity") is not None:
        chk("資產=負債+權益", _close(g("ta"), g("tl") + g("equity")),
            f"資產 {g('ta')} vs 負債+權益 {round(g('tl') + g('equity'), 1)}")
    # 2) 流動資產加總
    if all(g(k) is not None for k in ("ca", "cash", "ar", "inventory", "otherCA")):
        chk("流動資產加總", _close(g("ca"), g("cash") + g("ar") + g("inventory") + g("otherCA")),
            "cash+ar+inventory+otherCA = ca")
    # 3) 損益逐層
    if g("grossProfit") is not None and g("revenue") is not None and g("cogs") is not None:
        chk("毛利=營收-成本", _close(g("grossProfit"), g("revenue") - g("cogs")), "revenue-cogs")
    if g("opInc") is not None and g("grossProfit") is not None and g("opex") is not None:
        chk("營益=毛利-費用", _close(g("opInc"), g("grossProfit") - g("opex")), "grossProfit-opex")
    if g("netInc") is not None and g("pretax") is not None and g("tax") is not None:
        chk("淨利=稅前-稅", _close(g("netInc"), g("pretax") - g("tax")), "pretax-tax")
    # 4) 現金流量加總
    if all(g(k) is not None for k in ("netCF", "cfo", "cfi", "cff")):
        chk("淨現金=CFO+CFI+CFF", _close(g("netCF"), g("cfo") + g("cfi") + g("cff")), "cfo+cfi+cff")
    # 5) 正負號合理（軟檢查）
    if g("revenue") is not None:
        chk("營收為正", g("revenue") >= 0, "revenue >= 0", hard=False)
    if g("ta") is not None:
        chk("資產為正", g("ta") > 0, "total assets > 0", hard=False)
    if g("equity") is not None and g("ta"):
        chk("負債比 < 1", (g("tl", 0) / g("ta")) < 1.0 if g("ta") else True,
            "debt ratio sane", hard=False)

    hard_fail = [c for c in checks if c["hard"] and not c["ok"]]
    return {"usable": len(hard_fail) == 0, "checks": checks,
            "hard_failed": len(hard_fail), "status": "VERIFIED" if not hard_fail else "UNVERIFIED"}


def cost_structure(unit_variable: float, fixed_cost: float, price: float,
                   volume: float = 0) -> dict:
    """單位變動成本 / 固定成本 → 貢獻邊際、損益兩平、安全邊際、營運槓桿。"""
    cm = price - unit_variable                     # 單位貢獻邊際
    cm_ratio = (cm / price) if price else 0
    be_units = (fixed_cost / cm) if cm > 0 else float("inf")
    be_revenue = (fixed_cost / cm_ratio) if cm_ratio > 0 else float("inf")
    cm_total = cm * volume
    op_income = cm_total - fixed_cost
    mos = ((volume - be_units) / volume) if volume else None    # 安全邊際
    dol = (cm_total / op_income) if op_income else None          # 營運槓桿
    return {
        "unit_contribution": round(cm, 2), "cm_ratio": round(cm_ratio, 4),
        "breakeven_units": round(be_units, 1) if be_units != float("inf") else None,
        "breakeven_revenue": round(be_revenue, 1) if be_revenue != float("inf") else None,
        "operating_income": round(op_income, 1),
        "margin_of_safety": round(mos, 4) if mos is not None else None,
        "operating_leverage": round(dol, 2) if dol else None,
    }


def calibrate(bottom_up: float, reported: float, tol_rel: float = 0.05) -> dict:
    """由下而上估算 vs 由上而下實際。回傳差異與是否在容忍內（努力趨近）。"""
    if reported == 0:
        return {"variance": None, "variance_pct": None, "within": None}
    var = bottom_up - reported
    pct = var / reported
    return {"bottom_up": bottom_up, "reported": reported,
            "variance": round(var, 1), "variance_pct": round(pct, 4),
            "within_tolerance": abs(pct) <= tol_rel, "tolerance": tol_rel}


def peer_table(companies: list, metrics: list) -> dict:
    """同業比較：每個指標排名 + 相對中位數。companies=[{name, <metric>:val,...}]。"""
    out_rows = []
    stats = {}
    for m in metrics:
        vals = [c.get(m) for c in companies if isinstance(c.get(m), (int, float))]
        vals_sorted = sorted(vals)
        med = vals_sorted[len(vals_sorted) // 2] if vals_sorted else None
        stats[m] = {"median": med, "max": max(vals) if vals else None,
                    "min": min(vals) if vals else None}
    for c in companies:
        row = {"name": c["name"]}
        for m in metrics:
            v = c.get(m)
            rank = None
            if isinstance(v, (int, float)):
                higher = sum(1 for c2 in companies if isinstance(c2.get(m), (int, float)) and c2[m] > v)
                rank = higher + 1
            row[m] = v
            row[m + "_rank"] = rank
        out_rows.append(row)
    return {"rows": out_rows, "stats": stats, "n": len(companies)}
