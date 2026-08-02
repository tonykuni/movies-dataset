"""全景式分析（數個月來回的跨時間視圖）。

把幾個月的事件攤成全景：
  - 每產品/主題的事件量、時間跨度
  - 按週的活動量（看出忙閒、爆量週）
  - 最後活動日 + 停滯偵測（超過 N 天沒動靜 → 可能卡住/被遺忘）
  - 未結案數（status != 已結）

這是幫你「一眼看完幾個月」的層，回應降低人為整理、避免遺漏。
"""
from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime


def _parse_date(s: str):
    s = (s or "").strip()[:10]
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def _week(d: datetime) -> str:
    iso = d.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def build_panorama(records, stalled_days: int = 14) -> dict:
    dated = []
    for r in records:
        d = _parse_date(getattr(r, "event_time", ""))
        if d:
            dated.append((d, r))
    if not dated:
        return {"span": None, "products": {}, "weekly": {}, "stalled": []}

    ref = max(d for d, _ in dated)
    span = (min(d for d, _ in dated), ref)

    products = defaultdict(lambda: {"count": 0, "open": 0, "last": None,
                                    "first": None, "weeks": defaultdict(int)})
    weekly_total = defaultdict(int)

    for d, r in dated:
        key = getattr(r, "product", "") or "未分類"
        p = products[key]
        p["count"] += 1
        if getattr(r, "status", "") != "已結":
            p["open"] += 1
        p["last"] = d if p["last"] is None else max(p["last"], d)
        p["first"] = d if p["first"] is None else min(p["first"], d)
        p["weeks"][_week(d)] += 1
        weekly_total[_week(d)] += 1

    stalled = []
    for key, p in products.items():
        idle = (ref - p["last"]).days if p["last"] else 0
        if idle >= stalled_days and p["open"] > 0:
            stalled.append({"product": key, "idle_days": idle,
                            "last": p["last"].strftime("%Y-%m-%d"), "open": p["open"]})
    stalled.sort(key=lambda x: -x["idle_days"])

    prod_out = {}
    for key, p in products.items():
        prod_out[key] = {
            "count": p["count"], "open": p["open"],
            "first": p["first"].strftime("%Y-%m-%d") if p["first"] else "",
            "last": p["last"].strftime("%Y-%m-%d") if p["last"] else "",
            "weeks": dict(sorted(p["weeks"].items())),
        }

    return {
        "span": (span[0].strftime("%Y-%m-%d"), span[1].strftime("%Y-%m-%d")),
        "products": prod_out,
        "weekly": dict(sorted(weekly_total.items())),
        "stalled": stalled,
    }


def panorama_markdown(pan: dict) -> str:
    if not pan.get("span"):
        return ""
    L = [f"## 全景分析（{pan['span'][0]} → {pan['span'][1]}）"]
    L.append("| 產品 | 事件 | 未結 | 首次 | 最後 |")
    L.append("|---|---|---|---|---|")
    for k, p in sorted(pan["products"].items(), key=lambda x: -x[1]["count"]):
        L.append(f"| {k} | {p['count']} | {p['open']} | {p['first']} | {p['last']} |")
    if pan["weekly"]:
        L.append("\n**每週活動量**")
        mx = max(pan["weekly"].values())
        for wk, n in pan["weekly"].items():
            bar = "█" * max(1, round(12 * n / mx))
            L.append(f"- {wk}　{bar} {n}")
    if pan["stalled"]:
        L.append("\n### ⚠ 停滯提示（久未動靜且未結案）")
        for s in pan["stalled"]:
            L.append(f"- **{s['product']}**：已 {s['idle_days']} 天無活動（最後 {s['last']}，未結 {s['open']} 件）")
    return "\n".join(L)
