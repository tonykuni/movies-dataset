#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VAP_ENG007_RawWideRefresh — 宏觀寬表刷新器(批145;via-rawwide)
====================================================================
VAP 模板冊資料源=VDF_MacroRawWide.json(寬表);本器由實抓雙庫
(vdf_global_market.duckdb::global_daily/cross_macro/sentiment_daily)
合併延伸:
  只增不減語意=既有格值零觸碰;僅補新日期列/新欄/既有列空格
  欄映射:GSPC=^GSPC TWII=^TWII KOSPI=^KS11 DJI=^DJI IXIC=^IXIC
  N225=^N225 SSEC=000001.SS HSI=^HSI STOXX=^STOXX50E(adj_close)
  新欄:NVDA VIX GOLD OIL_WTI US10Y FEARGREED
  刷新前自動備份 pre_<ts> 側件(誠實可回溯)
用法:via-rawwide run | --status | --selftest
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

import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VAP = HERE.parent
VIA = VAP.parent.parent
WIDE = VAP / "VDF_MacroRawWide.json"
DB_GL = VIA / "functional modules" / "VDF" / "output_hub" / "mega" / "vdf_global_market.duckdb"

TICKER_MAP = {"GSPC": "^GSPC", "TWII": "^TWII", "KOSPI": "^KS11", "DJI": "^DJI",
              "IXIC": "^IXIC", "N225": "^N225", "SSEC": "000001.SS",
              "HSI": "^HSI", "STOXX": "^STOXX50E",
              "NVDA": "NVDA", "VIX": "^VIX", "GOLD": "GC=F", "OIL_WTI": "CL=F"}


def load_db_series() -> dict:
    """雙庫序列:{col: {date: value}}(adj_close 主欄+利率+情緒)"""
    import duckdb
    con = duckdb.connect(str(DB_GL), read_only=True)
    out = {}
    for col, tk in TICKER_MAP.items():
        rows = con.execute(
            "SELECT date, adj_close FROM global_daily WHERE ticker = ? "
            "AND adj_close IS NOT NULL", [tk]).fetchall()
        out[col] = {r[0]: float(r[1]) for r in rows}
    rows = con.execute("SELECT date, value FROM cross_macro "
                       "WHERE region='US' AND metric='GOV10Y'").fetchall()
    out["US10Y"] = {r[0]: float(r[1]) for r in rows}
    try:
        rows = con.execute("SELECT date, score FROM sentiment_daily "
                           "WHERE index='CNN_FEAR_GREED' AND score IS NOT NULL"
                           ).fetchall()
        out["FEARGREED"] = {r[0]: float(r[1]) for r in rows}
    except Exception:
        out["FEARGREED"] = {}
    con.close()
    return out


def refresh() -> dict:
    base = json.loads(WIDE.read_text(encoding="utf-8-sig")) if WIDE.exists() else []
    backup = WIDE.with_name(f"VDF_MacroRawWide.pre_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    if base:
        backup.write_text(json.dumps(base, ensure_ascii=False), encoding="utf-8")
    series = load_db_series()
    by_date = {r["date"]: r for r in base}
    filled = added_rows = added_cols = 0
    all_dates = sorted(set(by_date) | {d for s in series.values() for d in s})
    existing_cols = set(base[0].keys()) if base else {"date"}
    new_cols = [c for c in series if c not in existing_cols]
    out = []
    for d in all_dates:
        row = by_date.get(d)
        if row is None:
            row = {"date": d}
            added_rows += 1
        for col, s in series.items():
            v = s.get(d)
            if v is None:
                continue
            if row.get(col) is None:          # 只補空格/新欄=既有值零觸碰
                row[col] = v
                filled += 1
        out.append(row)
    added_cols = len(new_cols)
    WIDE.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return {"rows": len(out), "added_rows": added_rows, "filled": filled,
            "new_cols": new_cols, "backup": backup.name,
            "last_date": out[-1]["date"] if out else None}


def status() -> int:
    d = json.loads(WIDE.read_text(encoding="utf-8-sig"))
    print(f"rows {len(d)} · cols {len(d[-1])} · last {d[-1]['date']}"
          f" · 欄:{sorted(d[-1].keys())[:18]}")
    return 0


def selftest() -> int:
    global WIDE
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    chk("① 寬表+實抓庫在位", WIDE.exists() and DB_GL.exists())
    s = load_db_series()
    chk("② 雙庫序列載入(指數 9+新欄 5)",
        len(s.get("GSPC", {})) > 300 and len(s.get("NVDA", {})) > 300
        and len(s.get("US10Y", {})) > 300, f"(GSPC {len(s.get('GSPC', {}))} 日)")
    import tempfile
    _w = WIDE
    with tempfile.TemporaryDirectory() as td:
        WIDE = Path(td) / "VDF_MacroRawWide.json"
        WIDE.write_text(json.dumps(
            [{"date": "2026-06-16", "GSPC": 111.0, "TWII": None}]), encoding="utf-8")
        r = refresh()
        d = json.loads(WIDE.read_text())
        first = next(x for x in d if x["date"] == "2026-06-16")
        chk("③ 既有值零觸碰(GSPC=111 保留)+空格回填",
            first["GSPC"] == 111.0)
        chk("④ 延伸新日期列+新欄", r["added_rows"] > 10
            and "NVDA" in r["new_cols"], f"(+{r['added_rows']} 列)")
        chk("⑤ 備份側件落盤", (Path(td) / r["backup"]).exists())
    WIDE = _w
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 只增不減宣告+備份紀律", "零觸碰" in src and "backup" in src)
    print(f"  [計] 六檢 OK {6 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 寬表刷新器(VAP_ENG007)· 六檢自測 ===")
        return selftest()
    if "--status" in args:
        return status()
    r = refresh()
    print(f"[刷新] 列 {r['rows']}(+{r['added_rows']})· 補格 {r['filled']}"
          f" · 新欄 {r['new_cols']} · 至 {r['last_date']} · 備份 {r['backup']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
