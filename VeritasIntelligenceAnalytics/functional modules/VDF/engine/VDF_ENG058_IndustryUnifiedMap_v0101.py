#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v0100→v0101(批690 Z92 誠實燈):`tw_listings_industry` 不在時 build() 直接丟 CatalogException,--selftest 連一行 FAIL 都印不出來
  (容器/新機沒有產業冊=缺料,不是引擎壞;L16 缺料≠壞掉;批584 ENG072 同律)。v0101:表不在 → build 回 NODATA 並指路,
  自測印 [NODATA] ② + ③–⑥ 誠實 SKIP,rc=2(不是紅);表在、數字不合才是 FAIL。六檢不變。
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
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====
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


def _missing_tables(db, need) -> list:
    """批690:表不在=缺料(NODATA rc2),不是壞掉(L16;批584/689B 同律)。回缺的表名;庫檔不在=全缺。"""
    if not db.exists():
        return list(need)
    import duckdb
    con = duckdb.connect(str(db), read_only=True)
    try:
        have = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
    finally:
        con.close()
    return [t for t in need if t not in have]

NEED_TABLES = ("tw_listings_industry",)
REMEDY = ("補料=`$env:VIA_NET_CONSENT='YES'; via-market-lists`(VDF_ENG087 雙所 openapi 產業冊;閘=操作員的手;"
          "容器三車道回非 JSON=固定缺)")


def build() -> dict:
    miss = _missing_tables(DB_TW, NEED_TABLES)
    if miss:
        return {"state": "NODATA", "missing_tables": miss,
                "why": f"表不在:{', '.join(miss)} —— {REMEDY}。缺料不是壞掉(L16)"}
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
    miss = _missing_tables(DB_TW, NEED_TABLES)
    if miss:                          # 批690:缺料誠實 NODATA,不炸不報紅
        print(f"  [NODATA] ② 產業庫/表不在:{', '.join(miss)}(庫 {'在' if DB_TW.exists() else '不在'})")
        print(f"           {REMEDY}")
        print("  [SKIP] ③–⑥ 冊生成/單所限定/三大類計數/落盤:上游沒料,誠實跳過(不是壞掉,也不假裝過)")
        print(f"  [計] 六檢 OK {1 - len(fails)} · FAIL {len(fails)} · NODATA 1 · SKIP 4(誠實多態)")
        return 1 if fails else 2
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
        if b.get("state") == "NODATA":
            print(f"[NODATA] {b['why']}")
            return 2
        print(f"[冊] {OUT_JSON.name} · {b['totals']}")
        return 0
    print(__doc__.split("用法:")[1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
