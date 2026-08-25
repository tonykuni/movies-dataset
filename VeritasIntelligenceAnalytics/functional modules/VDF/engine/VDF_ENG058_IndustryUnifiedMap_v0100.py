#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_ENG058_IndustryUnifiedMap — 雙所產業混合分類編號冊(批155;via-industry)
====================================================================
操作員令:證交所×櫃買產業分類「大多一樣、少部分差異」→混合分類法+
編號方便觀察;電子/金融/傳產三大類。
生成法(全由庫內 tw_listings_industry 實資料導出,零發明):
  同碼同名=合併一條 VIA-IND-{碼};單所限定=保留原碼+market_scope 註記
  三大類 rollup 規則(冊上明示,市場慣例):
    ELEC 電子=產業碼 24-31(半導體/電腦週邊/光電/通信網路/電子零組件/
                電子通路/資訊服務/其他電子)
    FIN  金融=17(金融保險)
    TRAD 傳產=其餘全部(含綠能環保/數位雲端/生技等非金電)
產出:supportive modules/registry/VIA_IndustryUnifiedMap_v0100.json
  (冊=可版控;含逐碼統計+個股歸屬計數+雙所差異清單)
用法:via-industry build | --status | --selftest
"""
from __future__ import annotations
import json
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF = HERE.parent
VIA = VDF.parent.parent
DB_TW = VDF / "output_hub" / "mega" / "vdf_tw_market.duckdb"
REG = VIA / "supportive modules" / "registry"
OUT_JSON = REG / "VIA_IndustryUnifiedMap_v0100.json"
ELEC_CODES = {f"{i:02d}" for i in range(24, 32)}
FIN_CODES = {"17"}


def rollup(code: str) -> str:
    if code in ELEC_CODES:
        return "ELEC"
    if code in FIN_CODES:
        return "FIN"
    return "TRAD"


def build() -> dict:
    import duckdb
    con = duckdb.connect(str(DB_TW), read_only=True)
    rows = con.execute(
        "SELECT market, industry_code, industry_name, COUNT(*) n "
        "FROM tw_listings_industry GROUP BY 1,2,3 ORDER BY industry_code, market"
    ).fetchall()
    con.close()
    by_code: dict[str, dict] = {}
    for market, code, name, n in rows:
        e = by_code.setdefault(code, {"names": {}, "counts": {}})
        e["names"][market] = name
        e["counts"][market] = n
    items, diffs = [], []
    for code in sorted(by_code):
        e = by_code[code]
        names = e["names"]
        twse, tpex = names.get("TWSE"), names.get("TPEX")
        scope = ("BOTH" if twse and tpex else "TWSE_ONLY" if twse else "TPEX_ONLY")
        unified_name = twse or tpex
        if twse and tpex and twse != tpex:
            scope = "BOTH_NAME_DIFF"
            diffs.append({"code": code, "twse": twse, "tpex": tpex,
                          "resolution": "採 TWSE 名為統一名;TPEX 名列別名"})
        items.append({
            "via_id": f"VIA-IND-{code}",
            "industry_code": code,
            "unified_name": unified_name,
            "market_scope": scope,
            "aliases": {k: v for k, v in names.items() if v != unified_name},
            "sector3": rollup(code),
            "stock_counts": e["counts"],
        })
    book = {
        "schema": "VIA_INDUSTRY_UNIFIED_MAP_V1",
        "generated": str(date.today()),
        "source": "tw_listings_industry(雙所官方冊實抓;零發明)",
        "sector3_rule": {"ELEC": "產業碼 24-31", "FIN": "17 金融保險",
                          "TRAD": "其餘全部(非金電)"},
        "items": items,
        "cross_market_name_diffs": diffs,
        "totals": {
            "codes": len(items),
            "both": sum(1 for i in items if i["market_scope"].startswith("BOTH")),
            "twse_only": sum(1 for i in items if i["market_scope"] == "TWSE_ONLY"),
            "tpex_only": sum(1 for i in items if i["market_scope"] == "TPEX_ONLY"),
            "sector3_stock_counts": {
                s: sum(sum(i["stock_counts"].values()) for i in items
                       if i["sector3"] == s) for s in ("ELEC", "FIN", "TRAD")},
        },
    }
    OUT_JSON.write_text(json.dumps(book, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    return book


def status() -> int:
    if not OUT_JSON.exists():
        print("冊未建(先 build)")
        return 1
    b = json.loads(OUT_JSON.read_text(encoding="utf-8"))
    print(f"{b['generated']} · 碼 {b['totals']['codes']}(雙所 {b['totals']['both']}"
          f"/上市限 {b['totals']['twse_only']}/上櫃限 {b['totals']['tpex_only']})"
          f" · 三大類個股 {b['totals']['sector3_stock_counts']}")
    return 0


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    chk("① 三大類規則(24-31 電子/17 金融/餘傳產)",
        rollup("24") == "ELEC" and rollup("31") == "ELEC"
        and rollup("17") == "FIN" and rollup("01") == "TRAD" and rollup("35") == "TRAD")
    chk("② 產業庫在位", DB_TW.exists())
    b = build()
    chk("③ 冊生成(雙所合併+編號)", b["totals"]["codes"] >= 30
        and all(i["via_id"].startswith("VIA-IND-") for i in b["items"]),
        f"({b['totals']['codes']} 碼)")
    chk("④ 單所限定誠實列(上市限定≥5;上櫃限定≥1)",
        b["totals"]["twse_only"] >= 5 and b["totals"]["tpex_only"] >= 1,
        f"(TWSE_ONLY {b['totals']['twse_only']}·TPEX_ONLY {b['totals']['tpex_only']})")
    s3 = b["totals"]["sector3_stock_counts"]
    chk("⑤ 三大類個股計數全出值(電子>金融)",
        s3["ELEC"] > 500 and s3["FIN"] > 20 and s3["TRAD"] > 400, f"({s3})")
    chk("⑥ 冊落盤可版控", OUT_JSON.exists() and OUT_JSON.stat().st_size > 3000)
    print(f"  [計] 六檢 OK {6 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 產業混合分類冊(VDF_ENG058)· 六檢自測 ===")
        return selftest()
    if "--status" in args:
        return status()
    if "build" in args:
        b = build()
        print(f"[冊] {OUT_JSON.name} · {b['totals']}")
        return 0
    print(__doc__.split("用法:")[1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
