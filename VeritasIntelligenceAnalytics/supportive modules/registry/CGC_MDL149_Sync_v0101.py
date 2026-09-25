#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One VCGC pass over stock reports. VDF supplies the name. VRN reads the page."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
POLICY = HERE / "VIA_VCGC_Sync_Policy_v0101.json"
LOCK = HERE / "VIA_SourceLaneLock_v0100.json"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _sample() -> Path:
    spec = HERE / "VIA_InputConsole_Spec_v0100.json"
    chosen = ""
    if spec.is_file():
        data = json.loads(spec.read_text(encoding="utf-8"))
        chosen = str(((data.get("user") or {}).get("vrn_dir") or "")).strip()
    return Path(chosen or r"C:\測試樣本報告")


def _prices() -> dict:
    if not LOCK.is_file():
        return {}
    data = json.loads(LOCK.read_text(encoding="utf-8"))
    return {row["code"]: row["exchange_close"] for row in data.get("rows") or []}


def _annual(path: Path, core: str) -> dict:
    try:
        import fitz
    except Exception:
        return {"state": "ABSENT"}
    try:
        with fitz.open(str(path)) as doc:
            for index, page in enumerate(doc):
                if index == 0 or index > 8:
                    continue
                text = page.get_text("text") or ""
                if any(key in text for key in ("基本每股盈餘", "稀釋每股盈餘", "合併綜合損益")):
                    return {"state": "SEEN", "page": index + 1, "ticker_seen": core in text}
    except Exception as exc:
        return {"state": f"FAIL {type(exc).__name__}"}
    return {"state": "NODATA"}


def _one(path: Path, row: dict, market: str | None, name: str, page, texteng, rate, prices: dict, lanes, restorer) -> dict:
    code = row["ticker"]["code"]
    checked = page.confirm_codes(code, market)
    info = body = ""
    zone = None
    if path.suffix.lower() == ".pdf":
        laid = texteng.extract_page1_zones(path)
        plum = texteng.extract_page1_plumber(path)
        joins = 0
        if restorer is not None:
            for side in (laid, plum):
                if not side:
                    continue
                for key in ("header", "right", "body"):
                    fixed = restorer.restore(side.get(key) or "")
                    side[key] = fixed["text"]
                    joins += fixed["joins"]
        if laid and plum:
            zone = {
                "body": lanes.judge(laid.get("body"), plum.get("body")),
                "right": lanes.judge(laid.get("right"), plum.get("right")),
                "joins": joins,
            }
            info = "\n".join(x for x in (laid.get("header"), laid.get("right")) if x)
            body = laid.get("body") or ""
        elif laid:
            info = "\n".join(x for x in (laid.get("header"), laid.get("right")) if x)
            body = laid.get("body") or ""
            zone = {"state": "PLUMBER_EMPTY"}
        elif plum:
            info = "\n".join(x for x in (plum.get("header"), plum.get("right")) if x)
            body = plum.get("body") or ""
            zone = {"state": "LAYOUT_EMPTY"}
    rating = target = None
    if rate is not None and (info or body):
        try:
            rating = (rate.safe_rating(info or body) or {}).get("canonical")
        except Exception:
            rating = None
        try:
            target, _how = rate.safe_target_price(info or body, exclude_code=code)
        except Exception:
            target = None
    price = prices.get(code)
    analyst = None
    if info or body:
        try:
            hub = page._hub()
            for addr in hub.emails_of(info + "\n" + body) or []:
                found = hub.analyst_from_email(addr) or {}
                if found.get("name_guess"):
                    analyst = found.get("name_guess")
                    break
        except Exception:
            analyst = None
    return {
        "file": path.name,
        "ticker": code,
        "name": name or None,
        "market": market,
        "broker": (row.get("broker") or {}).get("canon"),
        "report_date": (row.get("date") or {}).get("iso"),
        "analyst": analyst,
        "yfinance_ticker": checked.get("yfinance_ticker"),
        "bloomberg_ticker": checked.get("bloomberg_ticker"),
        "three_ok": checked["ok"],
        "rating": rating,
        "target_price_adj": target,
        "upside_pct": page.upside(target, price) if target is not None else None,
        "yfinance_target_median": None,
        "factset_target_median": None,
        "zone": zone,
        "annual": _annual(path, code) if path.suffix.lower() == ".pdf" else {"state": "SKIP"},
    }


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VRN] 拒絕。只能經 via-vcgc。")
        return 2
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    cut = _load(VIA / "functional modules" / "VRN" / "VRN_ENG104_FilenameCut_v0100.py", "cut104")
    page = _load(VIA / "functional modules" / "VRN" / "VRN_ENG105_PageCrosscheck_v0100.py", "page105")
    lanes = _load(VIA / "functional modules" / "VRN" / "VRN_ENG106_ReadLanes_v0100.py", "lanes106")
    restorer = _load(VIA / "functional modules" / "VRN" / "VRN_ENG107_TextRestore_v0100.py", "restore107")
    texteng = _load(sorted((VIA / "functional modules" / "VRN").glob("VRN_ENG072_FirstPageText_v*.py"))[-1], "text072")
    try:
        rate = _load(sorted((VIA / "functional modules" / "VRN").glob("VRN_ENG086_FirstPageLogicBridge_v*.py"))[-1], "rate086")
    except Exception:
        rate = None
    folder = _sample()
    picked = []
    if folder.is_dir():
        for item in sorted(folder.iterdir()):
            if not item.is_file():
                continue
            row = cut.read_name(item.name)
            if row.get("ticker"):
                picked.append((item, row))
    codes = sorted({row["ticker"]["code"] for _item, row in picked})
    markets, names = {}, {}
    name_state = "SKIP"
    if codes:
        net = _load(sorted((VIA / "supportive modules" / "network").glob("via_net_unified_v*.py"))[-1], "net")
        got = _load(VIA / "functional modules" / "VDF" / "engine" / "VDF_ENG103_ListingName_v0100.py", "names").names_for(net, codes)
        if any((got.get("per") or {}).get(mkt, {}).get("state") == "OK" for mkt in ("TWSE", "TPEX")):
            name_state = "OK"
            for code, item in got["names"].items():
                markets[code] = item.get("market")
                names[code] = item.get("name")
        else:
            name_state = "DENY"
    prices = _prices()
    done, fails = [], []
    for item, row in picked:
        try:
            done.append(_one(item, row, markets.get(row["ticker"]["code"]), names.get(row["ticker"]["code"]), page, texteng, rate, prices, lanes, restorer))
        except Exception as exc:
            fails.append({"file": item.name, "why": type(exc).__name__})
    zone_counts = {}
    for row in done:
        zone = row.get("zone") or {}
        if "body" in zone and isinstance(zone["body"], dict):
            verdict = zone["body"].get("state") or zone["body"].get("verdict")
        else:
            verdict = zone.get("state") or "NO_TEXT"
        zone_counts[verdict] = zone_counts.get(verdict, 0) + 1
    example = next((row for row in done if row["ticker"] == "2330"), done[0] if done else None)
    out_dir = VIA / "VIA_Reports" / "vrn" / "sync"
    out_dir.mkdir(parents=True, exist_ok=True)
    report = out_dir / "SYNC_latest.json"
    body = {
        "via": "vcgc",
        "policy": policy["id"],
        "order": policy["order"],
        "folder": str(folder),
        "stock": len(picked),
        "opened": sum(1 for row in done if row.get("zone")),
        "names": name_state,
        "three_ok": sum(1 for row in done if row["three_ok"]),
        "joins": sum(int((row.get("zone") or {}).get("joins") or 0) for row in done),
        "rating_n": sum(1 for row in done if row["rating"]),
        "target_n": sum(1 for row in done if row["target_price_adj"] is not None),
        "annual_n": sum(1 for row in done if (row.get("annual") or {}).get("state") == "SEEN"),
        "zone": zone_counts,
        "paddle": "ABSENT",
        "fails": fails[:8],
        "example": example,
        "report": str(report),
        "do_not": ["run paddle", "guess a market", "full-market price fetch"],
        "next": "none",
        "logged_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    report.write_text(json.dumps({"summary": body, "rows": done}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("BEGIN_PASTE")
    print(json.dumps(body, ensure_ascii=False, indent=1))
    print("END_PASTE")
    return 0 if done else 2


if __name__ == "__main__":
    sys.exit(main())
