#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===== [VRN:ID:v0100] VRN-ENG022 · VRN_PivotDB_v0100 v0100 · ENGINE =====
# AST 注入（只加註解，AST 不變）：類別 0 · 函式 31；逐一編號在 ssot/VRN_ID_SSOT_v0100.json
# ===== [VRN:ID:END] =====
"""
VRN_PivotDB v0100 -- 驗證過的還原表格 → 資料庫形式（事實表 + PIVOT）。

Operator 2026-10-20: 「VRN-1 VRN-2 工具可相互取用 · 可驗證性高精準度還原後表格可改為資料庫形式 PIVOT ·
兩個系統元主體邏輯不變但各式可以找缺少的工具 · 獨立系統兩個 MAIN」.

  input    facts：一筆一格的長表（FACT_COLS）。VRN-1 用 facts_from_vrn1（G21 驗證過的年度數據）；
           別的系統（VRN-2）照 FACT_COLS 自己對好欄位再交進來 —— 本支只認這個契約，不讀別的系統的冊。
           還原後的整張表（restored：每張表的欄名 + 格）另外攤成一格一列（restored_cells），不經驗證、照實標燈號。
  pivot    只收 status 是 VERIFIED / CORRECTED、有期間、有數值的格：
             pivot_annual / pivot_quarterly          一張表一列科目（表 × 科目 × 年 / 季）
             pivot_report_annual / pivot_report_quarterly  同一份報告跨表合併（報告 × 科目 × 年 / 季）
           同一格兩個以上不同的證實值 → 格子留空、寫進 conflicts（不挑一個）。
  write    <out>/VRN_Pivot_v0100.sqlite（stdlib，永遠寫得出）· VRN_Pivot_v0100.duckdb（有 duckdb 才寫；
           另有 v_* 檢視，用 DuckDB 原生 PIVOT … ON period_key IN (…) 算，和實體表逐格比對）·
           每張表 .csv（UTF-8 BOM）＋ .parquet（有 pandas / pyarrow）· VRN_Pivot_v0100.json · VRN_Pivot_v0100.html。

可被別的系統借用：只 import 標準庫（duckdb / pandas 有就用、沒有就略過）、不 import VRN-1 其他程式、
不讀環境變數以外的設定、只寫進呼叫端給的輸出夾。不連網。
"""

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

import csv
import hashlib
import html
import json
import math
import os
import re
import sqlite3
import sys
import tempfile
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

VERSION = "VRN_PivotDB v0100"
CONTRACT = "VIA_PivotFacts/1"
DB_NAME = "VRN_Pivot_v0100.sqlite"
DUCK_NAME = "VRN_Pivot_v0100.duckdb"
HTML_NAME = "VRN_Pivot_v0100.html"
JSON_NAME = "VRN_Pivot_v0100.json"
FACT_COLS = ("system", "file", "ticker", "broker", "report_date", "page", "table_id", "metric", "metric_raw", "unit", "period_key",
             "period_label", "period_type", "fiscal_year", "fiscal_quarter", "estimate_flag", "value", "value_raw", "status", "note", "source_id")
KEEP_STATUS = ("VERIFIED", "CORRECTED")
TABLE_KEY = ("system", "file", "ticker", "table_id", "metric", "metric_raw", "unit")
# 報告層跨表合併只合「印的科目字一樣」的列：EPS (NT$)** 與 EPS (NT$)§（自家 / 共識）、reported / adjusted / diluted、
# 千元表與百萬元表是不同的量，不能因為歸到同一個科目就併成一格（MS / Daiwa / KGI 實測）
REPORT_KEY = ("system", "file", "ticker", "metric", "metric_raw", "unit")
RESTORED_COLS = ("system", "file", "page", "table_id", "title", "verdict", "row_index", "col_index", "row_label", "col_header", "cell", "value")
CONFLICT_COLS = ("level", "kind", "system", "file", "ticker", "metric", "metric_raw", "unit", "period_key", "values", "tables", "facts")
MERGE_COLS = ("level", "system", "file", "ticker", "metric", "metric_raw", "unit", "period_key", "kept", "values", "tables", "facts")
FACT_DERIVED = ("half_ulp",)   # 由 value_raw 算出：印的最後一位的一半（不是契約欄，借用端不用給）
QUARTER_RX = re.compile(r"^(\d{4})-(03|06|09|12)$")
YEAR_RX = re.compile(r"^\d{4}$")


# =====================================================================
# 1 . 欄位與期間
# =====================================================================
# [VRN-ID] VRN-ENG022-FNC001 · LOGIC
def nf(s: Any) -> str:
    return unicodedata.normalize("NFKC", "" if s is None else str(s)).strip()


# [VRN-ID] VRN-ENG022-FNC031 · LOGIC
def raw(s: Any) -> str:
    """原字（只去頭尾空白）：檔名照磁碟上的字 —— 全形「？」NFKC 會變成「?」，那就不是那個檔了。"""
    return "" if s is None else str(s).strip()


RAW_COLS = ("file",)


# [VRN-ID] VRN-ENG022-FNC002 · LOGIC
def present(v: Any) -> bool:
    return v is not None and nf(v) not in ("", "nan", "None", "NaN", "<NA>")


# [VRN-ID] VRN-ENG022-FNC003 · LOGIC
def to_float(v: Any) -> Optional[float]:
    if not present(v):
        return None
    t = nf(v).replace("−", "-").replace("–", "-").replace(",", "")
    neg = t.startswith("(") and t.rstrip("%").endswith(")")
    t = t.strip("()%xX ")
    try:
        x = float(t)
    except ValueError:
        return None
    return -abs(x) if neg else x


# [VRN-ID] VRN-ENG022-FNC004 · LOGIC
def period_key(fiscal_year: Any, fiscal_quarter: Any, period_type: Any) -> str:
    """期間鍵：季 = 季末月 YYYY-MM（FiscalQuarter 已是這個形）· 全年 = YYYY · 其他（TTM / 期間不明）= ""（不進 PIVOT）。"""
    fq = nf(fiscal_quarter)
    if QUARTER_RX.match(fq):
        return fq
    fy = to_float(fiscal_year)
    if fy is not None and nf(period_type) in ("FY", "") and 1990 <= fy <= 2099 and float(fy).is_integer():
        return "%d" % int(fy)
    return ""


# [VRN-ID] VRN-ENG022-FNC005 · LOGIC
def period_order(key: str) -> Tuple[int, int]:
    m = QUARTER_RX.match(key)
    if m:
        return int(m.group(1)), int(m.group(2))
    return (int(key), 13) if YEAR_RX.match(key) else (9999, 99)


# [VRN-ID] VRN-ENG022-FNC006 · LOGIC
def half_ulp(value_raw: Any, value: Optional[float]) -> float:
    """印的精度的一半：「4,458」→ 0.5 · 「4,457.8」→ 0.05。原字和值對不上（換算過單位）或科學記號 → 0（只認完全相同）。"""
    x = to_float(value_raw)
    if x is None or value is None or not _same(x, value):
        return 0.0
    t = nf(value_raw).replace(",", "").strip("()%xX ")
    if "e" in t.lower():
        return 0.0
    m = re.search(r"\.(\d+)$", t)
    return 0.5 * 10.0 ** -(len(m.group(1)) if m else 0)


# [VRN-ID] VRN-ENG022-FNC007 · LOGIC
def facts_from_vrn1(rows: Sequence[Dict[str, Any]], system: str = "VRN-1", names: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
    """VRN-1 G21 驗證過的年度數據（vrn_verified_financial_data）→ 契約 FACT_COLS。names：FileID → 原檔名（基本資料表；沒有就用 FileID）。"""
    out = []
    names = names or {}
    for r in rows:
        fid = nf(r.get("FileID"))
        out.append({"system": system, "file": raw(r.get("VerifyFile")) or names.get(fid) or fid, "ticker": nf(r.get("TW_TICKER")), "broker": nf(r.get("Broker")),
                    "report_date": nf(r.get("ReportDate")), "page": nf(r.get("VerifyPage") or r.get("PageNumber")), "table_id": nf(r.get("TableID")),
                    "metric": nf(r.get("MetricName")), "metric_raw": nf(r.get("MetricNameRaw")), "unit": nf(r.get("Unit")),
                    "period_key": period_key(r.get("FiscalYear"), r.get("FiscalQuarter"), r.get("PeriodType")),
                    "period_label": nf(r.get("PeriodLabelRaw")), "period_type": nf(r.get("PeriodType")), "fiscal_year": nf(r.get("FiscalYear")),
                    "fiscal_quarter": nf(r.get("FiscalQuarter")), "estimate_flag": nf(r.get("EstimateFlag")), "value": to_float(r.get("Value")),
                    "value_raw": nf(r.get("ValueRaw")), "status": nf(r.get("VerifyStatus")) or "UNVERIFIED", "note": nf(r.get("VerifyNote")),
                    "source_id": nf(r.get("FinancialRowID"))})
    return out


# [VRN-ID] VRN-ENG022-FNC008 · LOGIC
def restored_from_vrn1_sqlite(path: Path, system: str = "VRN-1") -> List[Dict[str, Any]]:
    """VRN-1 G15 還原表（VRN_ReportRegions_v0100.sqlite 的 tables_：欄名 JSON + 格 JSON）→ 每張表一筆 {欄名, 格}。"""
    out = []
    if not Path(path).is_file():
        return out
    con = sqlite3.connect(str(path))
    try:
        for file, seq, page, anchor, title, verdict, columns, cells in con.execute(
                "SELECT file, seq, page, anchor, title, verdict, columns, cells FROM tables_ ORDER BY file, seq"):
            try:
                cols, grid = json.loads(columns or "[]"), json.loads(cells or "[]")
            except ValueError:
                continue
            out.append({"system": system, "file": file, "page": page, "table_id": "%s#%s" % (anchor or "", seq), "title": title or "",
                        "verdict": verdict or "", "columns": cols, "cells": grid})
    finally:
        con.close()
    return out


# [VRN-ID] VRN-ENG022-FNC009 · VALIDATE
def check_facts(facts: Sequence[Dict[str, Any]]) -> List[str]:
    """契約檢查：缺欄 / 多欄 → 回問題清單（空 = 合約相符）。"""
    issues = []
    for i, f in enumerate(facts):
        miss = [c for c in FACT_COLS if c not in f]
        if miss:
            issues.append("第 %d 筆缺欄：%s" % (i + 1, "、".join(miss)))
            if len(issues) >= 5:
                break
    return issues


# =====================================================================
# 2 . PIVOT（在 Python 裡算出實體表 → SQLite / DuckDB / CSV 都是同一份）
# =====================================================================
# [VRN-ID] VRN-ENG022-FNC010 · LOGIC
def _keep(facts: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [f for f in facts if nf(f.get("status")) in KEEP_STATUS and f.get("period_key") and f.get("value") is not None]


# [VRN-ID] VRN-ENG022-FNC011 · LOGIC
def _same(a: float, b: float) -> bool:
    return abs(a - b) <= 1e-9 * max(1.0, abs(a), abs(b))


# [VRN-ID] VRN-ENG022-FNC012 · LOGIC
def _tol(a: float, b: float) -> float:
    return 1e-9 * max(1.0, abs(a), abs(b))


# [VRN-ID] VRN-ENG022-FNC013 · LOGIC
def _resolve(hits: Sequence[Dict[str, Any]]) -> Optional[float]:
    """同一格的證實值 → 一個值或 None（衝突，不挑）。
    同一個數印的位數不同（4,458 與 4,457.8）不是衝突：取印得最細的那一個 s，其他每一個都必須是 s 照它自己的位數四捨五入
    （|v − s| ≤ 它的 half_ulp）；印得最細的那幾個彼此也要相同。DuckDB 檢視用同一條規則（write_duckdb）。"""
    hmin = min(h["half_ulp"] for h in hits)
    best = [h["value"] for h in hits if h["half_ulp"] == hmin]
    lo, hi = min(best), max(best)
    if hi - lo > _tol(lo, hi):
        return None
    if any(abs(h["value"] - lo) > h["half_ulp"] + _tol(h["value"], lo) for h in hits):
        return None
    return lo


# [VRN-ID] VRN-ENG022-FNC030 · LOGIC
def conflict_kind(vals: Sequence[float]) -> str:
    """衝突的樣子（只是標給人看，格子照樣留空）：sign = 絕對值相同、正負不同（各表的符號慣例）· scale = 差 10 的次方（單位不同）· value = 數真的不同。"""
    a = sorted({abs(v) for v in vals})
    if len(a) == 1:
        return "sign"
    if a[0] > 0 and all(abs(math.log10(x / a[0]) - round(math.log10(x / a[0]))) < 1e-6 and round(math.log10(x / a[0])) != 0 for x in a[1:]):
        return "scale"
    return "value"


# [VRN-ID] VRN-ENG022-FNC014 · LOGIC
def _pivot(facts: List[Dict[str, Any]], key_cols: Sequence[str], quarterly: bool,
           level: str = "") -> Tuple[List[Dict[str, Any]], List[str], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """(列, 期間欄, 衝突, 精度合併)：同一列同一期間兩個以上真的不同的值 → 格子 None + 衝突一筆；
    只是印的位數不同 → 取最細的、記一筆精度合併（level = table / report）。"""
    cells: Dict[Tuple, Dict[str, List[Dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for f in facts:
        q = bool(QUARTER_RX.match(f["period_key"]))
        if q != quarterly:
            continue
        cells[tuple(raw(f.get(k)) if k in RAW_COLS else nf(f.get(k)) for k in key_cols)][f["period_key"]].append(f)
    periods = sorted({p for d in cells.values() for p in d}, key=period_order)
    rows, conflicts, merges = [], [], []
    for key in sorted(cells):
        row = dict(zip(key_cols, key))
        for p in periods:
            hits = cells[key].get(p) or []
            if not hits:
                row[p] = None
                continue
            vals: List[float] = []
            for h in hits:
                if not any(_same(h["value"], v) for v in vals):
                    vals.append(h["value"])
            row[p] = _resolve(hits)
            if len(vals) > 1:
                rec = {"level": level, "system": row.get("system", ""), "file": row.get("file", ""), "ticker": row.get("ticker", ""),
                       "metric": row.get("metric", ""), "metric_raw": row.get("metric_raw", ""), "unit": row.get("unit", ""), "period_key": p,
                       "values": " | ".join(nf(h.get("value_raw")) or "%g" % h["value"] for h in hits),
                       "tables": " | ".join(sorted({nf(h.get("table_id")) for h in hits})),
                       "facts": " | ".join(nf(h.get("source_id")) for h in hits)}
                if row[p] is None:
                    conflicts.append(dict(rec, kind=conflict_kind(vals)))
                else:
                    merges.append(dict(rec, kept=row[p]))
        rows.append(row)
    return rows, periods, conflicts, merges


# [VRN-ID] VRN-ENG022-FNC015 · LOGIC
def restored_cells(restored: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """還原後的整張表 → 一格一列（欄名照表頭；第一欄當列名）。不驗證，燈號照還原端給的 verdict。"""
    out = []
    for t in restored or []:
        cols = list(t.get("columns") or [])
        for ri, r in enumerate(t.get("cells") or []):
            label = nf(r[0]) if r else ""
            for ci, cell in enumerate(r):
                if ci == 0 and len(r) > 1:
                    continue
                out.append({"system": nf(t.get("system")), "file": raw(t.get("file")), "page": nf(t.get("page")), "table_id": nf(t.get("table_id")),
                            "title": nf(t.get("title")), "verdict": nf(t.get("verdict")), "row_index": ri, "col_index": ci, "row_label": label,
                            "col_header": nf(cols[ci]) if ci < len(cols) else "", "cell": nf(cell), "value": to_float(cell)})
    return out


# [VRN-ID] VRN-ENG022-FNC016 · LOGIC
def pivot_tables(facts: Sequence[Dict[str, Any]], restored: Sequence[Dict[str, Any]] = ()) -> Dict[str, Any]:
    keep = _keep(facts)
    ann, ann_p, c1, m1 = _pivot(keep, TABLE_KEY, False, "table")
    qtr, qtr_p, c2, m2 = _pivot(keep, TABLE_KEY, True, "table")
    rann, rann_p, c3, m3 = _pivot(keep, REPORT_KEY, False, "report")
    rqtr, rqtr_p, c4, m4 = _pivot(keep, REPORT_KEY, True, "report")
    fcols = list(FACT_COLS) + list(FACT_DERIVED)
    tables = {"facts": [{c: f.get(c) for c in fcols} for f in facts],
              "pivot_annual": ann, "pivot_quarterly": qtr, "pivot_report_annual": rann, "pivot_report_quarterly": rqtr,
              "conflicts": c1 + c2 + c3 + c4, "precision_merges": m1 + m2 + m3 + m4, "restored_cells": restored_cells(restored)}
    columns = {"facts": fcols, "pivot_annual": list(TABLE_KEY) + ann_p, "pivot_quarterly": list(TABLE_KEY) + qtr_p,
               "pivot_report_annual": list(REPORT_KEY) + rann_p, "pivot_report_quarterly": list(REPORT_KEY) + rqtr_p,
               "conflicts": list(CONFLICT_COLS), "precision_merges": list(MERGE_COLS), "restored_cells": list(RESTORED_COLS)}
    periods = {"pivot_annual": ann_p, "pivot_quarterly": qtr_p, "pivot_report_annual": rann_p, "pivot_report_quarterly": rqtr_p}
    return {"tables": tables, "columns": columns, "periods": periods, "kept": len(keep)}


# =====================================================================
# 3 . 寫出
# =====================================================================
# [VRN-ID] VRN-ENG022-FNC017 · LOGIC
def _q(name: str) -> str:
    return '"%s"' % name.replace('"', '""')


# [VRN-ID] VRN-ENG022-FNC018 · LOGIC
def _sql_type(col: str, period_cols: Sequence[str]) -> str:
    if col in period_cols or col in ("value", "kept", "half_ulp"):
        return "REAL"
    if col in ("row_index", "col_index"):
        return "INTEGER"
    return "TEXT"


# [VRN-ID] VRN-ENG022-FNC019 · IO
def write_sqlite(path: Path, pv: Dict[str, Any]) -> None:
    tmp = path.with_suffix(".sqlite.tmp")
    if tmp.exists():
        tmp.unlink()
    con = sqlite3.connect(str(tmp))
    try:
        for name, rows in pv["tables"].items():
            cols = pv["columns"][name]
            pc = pv["periods"].get(name, [])
            con.execute("CREATE TABLE %s (%s)" % (_q(name), ", ".join("%s %s" % (_q(c), _sql_type(c, pc)) for c in cols)))
            con.executemany("INSERT INTO %s VALUES (%s)" % (_q(name), ", ".join("?" * len(cols))), [tuple(r.get(c) for c in cols) for r in rows])
        con.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")
        con.executemany("INSERT INTO meta VALUES (?, ?)", list(pv["meta"].items()))
        con.commit()
    finally:
        con.close()
    os.replace(str(tmp), str(path))


# [VRN-ID] VRN-ENG022-FNC020 · IO
def write_duckdb(path: Path, pv: Dict[str, Any]) -> Dict[str, Any]:
    """有 duckdb 才寫；實體表照 SQLite 那一份，另建 v_* 檢視用 DuckDB 原生 PIVOT 算，再和實體表逐格比對。"""
    try:
        import duckdb  # VRN-1 的相依（requirements-dev.txt）；借用端沒有就略過
    except Exception as error:  # noqa: BLE001
        path.unlink(missing_ok=True)                      # 同一夾上一次留下的 .duckdb 跟這一次的 SQLite 對不上 → 不留
        return {"written": False, "why": "沒有 duckdb（%s）" % error.__class__.__name__}
    tmp = path.with_suffix(".duckdb.tmp")
    for p in (tmp, Path(str(tmp) + ".wal")):
        if p.exists():
            p.unlink()
    con = duckdb.connect(str(tmp))
    mismatch = []
    try:
        for name, rows in pv["tables"].items():
            cols = pv["columns"][name]
            pc = pv["periods"].get(name, [])
            con.execute("CREATE TABLE %s (%s)" % (_q(name), ", ".join("%s %s" % (_q(c), "DOUBLE" if _sql_type(c, pc) == "REAL" else
                                                                                   ("BIGINT" if _sql_type(c, pc) == "INTEGER" else "VARCHAR")) for c in cols)))
            if rows:
                con.executemany("INSERT INTO %s VALUES (%s)" % (_q(name), ", ".join("?" * len(cols))), [tuple(r.get(c) for c in cols) for r in rows])
        keep = "status IN (%s) AND period_key <> '' AND value IS NOT NULL" % ", ".join("'%s'" % s for s in KEEP_STATUS)
        for name, key_cols, quarterly in (("pivot_annual", TABLE_KEY, False), ("pivot_quarterly", TABLE_KEY, True),
                                          ("pivot_report_annual", REPORT_KEY, False), ("pivot_report_quarterly", REPORT_KEY, True)):
            periods = pv["periods"][name]
            if not periods:
                continue
            cond = "regexp_matches(period_key, '^[0-9]{4}-(03|06|09|12)$')" if quarterly else "regexp_matches(period_key, '^[0-9]{4}$')"
            keys = ", ".join(_q(c) for c in key_cols)
            # 規則和 _resolve 一樣、在 SQL 裡另算一次：印得最細的那幾個值（min = max）→ s；每一個值都要在 s ± 它自己的 half_ulp 裡，
            # 否則 bad = 1 → 格子留空
            win = "WINDOW w AS (PARTITION BY %s, period_key)" % keys
            cells = ("SELECT %s, period_key, slo AS v, CASE WHEN shi - slo <= 1e-9 * greatest(1, abs(slo), abs(shi)) "
                     "AND abs(value - slo) <= half_ulp + 1e-9 * greatest(1, abs(value), abs(slo)) THEN 0 ELSE 1 END AS bad FROM ("
                     "SELECT *, min(CASE WHEN half_ulp = hmin THEN value END) OVER w AS slo, max(CASE WHEN half_ulp = hmin THEN value END) OVER w AS shi FROM ("
                     "SELECT %s, period_key, value, half_ulp, min(half_ulp) OVER w AS hmin FROM facts WHERE %s AND %s %s) %s)"
                     % (keys, keys, keep, cond, win, win))
            con.execute("CREATE VIEW %s AS SELECT %s, %s FROM (PIVOT (%s) ON period_key IN (%s) USING max(bad) AS bad, min(v) AS v GROUP BY %s)"
                        % (_q("v_" + name), keys,
                           ", ".join("CASE WHEN %s = 0 THEN %s END AS %s" % (_q(p + "_bad"), _q(p + "_v"), _q(p)) for p in periods),
                           cells, ", ".join("'%s'" % p for p in periods), keys))
            got = {tuple(r[:len(key_cols)]): r[len(key_cols):] for r in con.execute("SELECT * FROM %s" % _q("v_" + name)).fetchall()}
            for r in pv["tables"][name]:
                k = tuple(raw(r.get(c)) if c in RAW_COLS else nf(r.get(c)) for c in key_cols)
                v = got.get(k)
                if v is None or any(not ((a is None and r.get(p) is None) or (a is not None and r.get(p) is not None and _same(a, r[p])))
                                    for a, p in zip(v, periods)):
                    mismatch.append("%s %s" % (name, " · ".join(k)))
        con.execute("CREATE TABLE meta (key VARCHAR, value VARCHAR)")
        con.executemany("INSERT INTO meta VALUES (?, ?)", list(pv["meta"].items()))
    finally:
        con.close()
    os.replace(str(tmp), str(path))
    return {"written": True, "views": ["v_" + n for n in pv["periods"] if pv["periods"][n]], "pivot_check": "OK" if not mismatch else "MISMATCH",
            "mismatch": mismatch[:10]}


# [VRN-ID] VRN-ENG022-FNC021 · IO
def write_files(out: Path, pv: Dict[str, Any]) -> Dict[str, str]:
    done = {}
    try:
        import pandas as pd
    except Exception:  # noqa: BLE001 - 沒有 pandas：只寫 CSV
        pd = None
    for name, rows in pv["tables"].items():
        cols = pv["columns"][name]
        with open(out / (name + ".csv"), "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(cols)
            for r in rows:
                w.writerow(["" if r.get(c) is None else r.get(c) for c in cols])
        done[name] = str(out / (name + ".csv"))
        if pd is not None:
            try:
                df = pd.DataFrame([[r.get(c) for c in cols] for r in rows], columns=cols)
                for c in cols:
                    if df[c].dtype == object:
                        df[c] = df[c].astype("string")
                df.to_parquet(out / (name + ".parquet"), index=False)
            except Exception:  # noqa: BLE001 - 沒有 pyarrow：CSV 已寫
                (out / (name + ".parquet")).unlink(missing_ok=True)   # 上一次的 Parquet 跟這一次的 CSV 對不上 → 不留
    return done


# [VRN-ID] VRN-ENG022-FNC022 · LOGIC
def fingerprint(pv: Dict[str, Any]) -> str:
    h = hashlib.sha256()
    for name in sorted(pv["tables"]):
        cols = pv["columns"][name]
        h.update(("#%s\x1e%s\x1e" % (name, "\x1f".join(cols))).encode("utf-8"))
        for r in pv["tables"][name]:
            h.update(("\x1f".join("" if r.get(c) is None else (repr(r[c]) if isinstance(r[c], float) else str(r[c])) for c in cols) + "\x1e").encode("utf-8"))
    return h.hexdigest()[:16]


TAB_NAMES = (("pivot_report_annual", "年度 PIVOT（報告 × 科目）"), ("pivot_report_quarterly", "季度 PIVOT（報告 × 科目）"),
             ("pivot_annual", "年度 PIVOT（表 × 科目）"), ("pivot_quarterly", "季度 PIVOT（表 × 科目）"), ("conflicts", "衝突（同格兩個證實值）"),
             ("precision_merges", "精度合併（同一個數 · 印的位數不同）"),
             ("facts", "事實表（一格一列 · 含未收的）"), ("restored_cells", "還原表（一格一列 · 未驗證）"))


# [VRN-ID] VRN-ENG022-FNC023 · IO
def write_html(path: Path, summary: Dict[str, Any], pv: Dict[str, Any], title: str = "") -> None:
    data = {}
    for name, label in TAB_NAMES:
        cols = pv["columns"][name]
        data[name] = {"name": label, "cols": cols,
                      "rows": [["" if r.get(c) is None else ("%g" % r[c] if isinstance(r.get(c), float) else str(r.get(c))) for c in cols]
                               for r in pv["tables"][name]]}
    blob = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
    who = " / ".join(sorted({nf(f.get("system")) for f in pv["tables"]["facts"]} - {""})) or "（系統未標）"   # 分開寫 VRN-1 / VRN-2，不寫籠統的 VRN
    c = summary["counts"]
    cards = "".join('<div class="card"><div class="mut">%s</div><div class="big">%s</div><div class="mut">%s</div></div>' % (html.escape(a), html.escape(b), html.escape(d))
                    for a, b, d in (("事實（收進 PIVOT）", "%d / %d" % (c["kept"], c["facts"]), "只收 VERIFIED / CORRECTED · 有期間 · 有數值"),
                                    ("年度 PIVOT", "%d 列" % c["pivot_report_annual"], "報告 × 科目 · %d 個年度欄" % len(pv["periods"]["pivot_report_annual"])),
                                    ("季度 PIVOT", "%d 列" % c["pivot_report_quarterly"], "報告 × 科目 · %d 個季度欄" % len(pv["periods"]["pivot_report_quarterly"])),
                                    ("衝突", "%d" % c["conflicts"], "同一格兩個不同的證實值 → 留空不挑 · 精度合併 %d" % c["precision_merges"])))
    page = """<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s PIVOT 資料庫</title>
<style>
:root{--bg:#f7f7f5;--fg:#1d1d1f;--mut:#5f6368;--card:#fff;--line:#dedede;--acc:#0b57d0;--chip:#eef1f6}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#121314;--fg:#e8e8e8;--mut:#a0a4a8;--card:#1c1d1f;--line:#34363a;--acc:#8ab4f8;--chip:#26282c}}
:root[data-theme="dark"]{--bg:#121314;--fg:#e8e8e8;--mut:#a0a4a8;--card:#1c1d1f;--line:#34363a;--acc:#8ab4f8;--chip:#26282c}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.55 system-ui,-apple-system,"Segoe UI","Noto Sans TC","PingFang TC",sans-serif}
main{max-width:1200px;margin:0 auto;padding:20px 16px 60px}h1{font-size:24px;margin:4px 0}.mut{color:var(--mut)}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin-top:14px}.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px}
.big{font-size:26px;font-weight:650;font-variant-numeric:tabular-nums}
.note{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--acc);border-radius:8px;padding:10px 14px;margin:12px 0}
.tabs{display:flex;flex-wrap:wrap;gap:6px;margin:16px 0 8px}.tabs button{background:var(--card);color:var(--fg);border:1px solid var(--line);border-radius:99px;padding:5px 12px;font:inherit;cursor:pointer}
.tabs button[aria-selected="true"]{background:var(--acc);color:#fff;border-color:var(--acc)}
.bar{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0}.bar select,.bar input{flex:1 1 220px;min-width:0;font:inherit;padding:6px 8px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--fg)}
.bar button{font:inherit;padding:6px 12px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--fg);cursor:pointer}
.wrap{overflow-x:auto;border-radius:10px;border:1px solid var(--line)}table{width:100%%;border-collapse:collapse;background:var(--card)}
th,td{padding:6px 9px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top;font-size:13.5px}th{background:var(--chip);font-weight:600;white-space:nowrap}
td{max-width:420px;overflow-wrap:break-word}td.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}#tb td:nth-child(2){min-width:14em}
</style></head><body><main>
<h1>%s PIVOT 資料庫</h1>
<div class="mut">%s · %s · 指紋 <code>%s</code> · %s</div>
<div class="cards">%s</div>
<div class="note"><b>怎麼來的</b>：還原後的表格經驗證（VERIFIED / CORRECTED）的每一格 → 事實表（一格一列，附頁碼、表、原值、驗證說明）→ 依期間轉成 PIVOT（年度欄 YYYY、季度欄 YYYY-MM 季末月）。
同一格兩個不同的證實值不挑一個：格子留空、列進「衝突」；只是印的位數不同（4,458 與 4,457.8：粗的那個正是細的那個四捨五入）→ 取細的、列進「精度合併」。資料庫：<code>%s</code>%s。</div>
<div class="tabs" id="tabs" role="tablist"></div>
<div class="bar"><select id="ff"><option value="">全部檔案</option></select><input id="fq" placeholder="搜尋：科目 / 期間 / 值"></div>
<div class="bar"><button id="prev">上一頁</button><span class="mut" id="pg"></span><button id="next">下一頁</button></div>
<div class="wrap"><table><thead id="th"></thead><tbody id="tb"></tbody></table></div>
</main>
<script id="data" type="application/json">%s</script>
<script>
const D=JSON.parse(document.getElementById('data').textContent);const P=50;let tab=Object.keys(D)[0],page=0;const $=i=>document.getElementById(i);
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));const num=/^-?[0-9][0-9.,]*(e[-+]?[0-9]+)?$/i;
Object.entries(D).forEach(([k,v])=>{const b=document.createElement('button');b.textContent=v.name+' · '+v.rows.length;b.setAttribute('role','tab');b.dataset.k=k;b.onclick=()=>{tab=k;page=0;sync();draw()};$('tabs').appendChild(b)});
function fi(){return D[tab].cols.indexOf('file')}
function sync(){[...$('tabs').children].forEach(b=>b.setAttribute('aria-selected',b.dataset.k===tab));const t=D[tab],i=fi(),ff=$('ff'),keep=ff.value;ff.length=1;
 if(i>=0)[...new Set(t.rows.map(r=>r[i]))].sort().forEach(f=>ff.add(new Option(f,f)));ff.value=[...ff.options].some(o=>o.value===keep)?keep:'';}
function rows(){const t=D[tab],i=fi(),f=$('ff').value,q=$('fq').value.trim().toLowerCase();return t.rows.filter(r=>(!f||i<0||r[i]===f)&&(!q||r.join(' ').toLowerCase().includes(q)));}
function draw(){const t=D[tab],x=rows(),n=Math.max(1,Math.ceil(x.length/P));page=Math.min(page,n-1);
 $('th').innerHTML='<tr>'+t.cols.map(c=>'<th>'+esc(c)+'</th>').join('')+'</tr>';
 $('tb').innerHTML=x.slice(page*P,page*P+P).map(r=>'<tr>'+r.map(v=>'<td'+(num.test(v)?' class="n"':'')+'>'+esc(v)+'</td>').join('')+'</tr>').join('');
 $('pg').textContent='第 '+(page+1)+' / '+n+' 頁 · '+x.length+' 筆';}
$('ff').onchange=()=>{page=0;draw()};$('fq').oninput=()=>{page=0;draw()};$('prev').onclick=()=>{if(page>0){page--;draw()}};$('next').onclick=()=>{page++;draw()};sync();draw();
</script></body></html>
""" % (html.escape(who), html.escape(who), html.escape(title or ""), html.escape(VERSION), html.escape(summary["fingerprint"]), html.escape(summary["generated_by"]), cards,
       html.escape(Path(summary["sqlite"]).name), (" · " + html.escape(Path(summary["duckdb"]).name) + "（含 DuckDB 原生 PIVOT 檢視 v_*）") if summary.get("duckdb") else "", blob)
    path.write_text(page, encoding="utf-8")


# [VRN-ID] VRN-ENG022-FNC024 · BUILD
def build_pivot_db(facts: Sequence[Dict[str, Any]], out_dir: Any, restored: Sequence[Dict[str, Any]] = (), title: str = "",
                   generated_by: str = "") -> Dict[str, Any]:
    """契約入口（借用端呼叫這一支）：facts（FACT_COLS）＋ 可選的 restored（整張還原表）→ out_dir 裡的資料庫與檔。"""
    issues = check_facts(facts)
    if issues:
        raise ValueError("facts 不合契約 %s：%s" % (CONTRACT, "；".join(issues)))
    facts = [{c: (to_float(f.get(c)) if c == "value" else (raw(f.get(c)) if c in RAW_COLS else nf(f.get(c)))) for c in FACT_COLS}
             for f in facts]                                          # 文字 NFKC（檔名照原字）· 值一律 float / None
    for f in facts:
        f["half_ulp"] = half_ulp(f["value_raw"], f["value"])
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    pv = pivot_tables(facts, restored)
    fp = fingerprint(pv)
    pv["meta"] = {"version": VERSION, "contract": CONTRACT, "fingerprint": fp, "generated_by": generated_by or VERSION, "title": title,
                  "keep_status": ",".join(KEEP_STATUS), "facts": str(len(facts)), "kept": str(pv["kept"])}
    write_sqlite(out / DB_NAME, pv)
    duck = write_duckdb(out / DUCK_NAME, pv)
    files = write_files(out, pv)
    counts = {"facts": len(facts), "kept": pv["kept"], **{n: len(pv["tables"][n]) for n in pv["tables"] if n != "facts"}}
    summary = {"version": VERSION, "contract": CONTRACT, "generated_by": generated_by or VERSION, "fingerprint": fp, "counts": counts,
               "periods": pv["periods"], "sqlite": str(out / DB_NAME), "duckdb": str(out / DUCK_NAME) if duck.get("written") else "",
               "duckdb_check": duck, "files": files, "html": str(out / HTML_NAME), "json": str(out / JSON_NAME)}
    write_html(out / HTML_NAME, summary, pv, title)
    (out / JSON_NAME).write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    return summary


# [VRN-ID] VRN-ENG022-FNC025 · BUILD
def build_from_vrn1_round(round_dir: Any, out_dir: Any = None, title: str = "") -> Dict[str, Any]:
    """VRN-1 一輪的輸出夾 → <round>/pivot/：G21 驗證過的年度數據 + G15 還原表。"""
    rd = Path(round_dir)
    src = rd / "verified" / "vrn_verified_financial_data.csv"
    if not src.is_file():
        raise FileNotFoundError("沒有 G21 驗證過的年度數據：%s" % src)
    names: Dict[str, str] = {}
    basic = rd / "dataframes" / "vrn_basic_info.csv"
    if basic.is_file():                                   # FileID 是雜湊 · 人看的是原檔名（同一份基本資料表）
        with open(basic, encoding="utf-8-sig", newline="") as fh:
            names = {nf(b.get("FileID")): raw(b.get("SourceFileName")) for b in csv.DictReader(fh) if b.get("FileID") and b.get("SourceFileName")}
    with open(src, encoding="utf-8-sig", newline="") as fh:
        facts = facts_from_vrn1(list(csv.DictReader(fh)), names=names)
    restored = restored_from_vrn1_sqlite(rd / "VRN_ReportRegions_v0100.sqlite")
    return build_pivot_db(facts, Path(out_dir) if out_dir else rd / "pivot", restored, title=title, generated_by="VRN-1 G22")


# =====================================================================
# 4 . 自測（已知答案）
# =====================================================================
# [VRN-ID] VRN-ENG022-FNC026 · ENTRY
def selftest(verbose: bool = True) -> int:
    checks: List[Tuple[str, bool]] = []

    # [VRN-ID] VRN-ENG022-FNC027 · LOGIC
    def fact(file, metric, fy, fq, ptype, value, status="VERIFIED", table="T1", raw=None, sid="", mraw=None):
        return {"system": "TEST", "file": file, "ticker": "1234", "broker": "B", "report_date": "2026-01-01", "page": "1", "table_id": table,
                "metric": metric, "metric_raw": mraw or metric, "unit": "NT$", "period_key": period_key(fy, fq, ptype), "period_label": "", "period_type": ptype,
                "fiscal_year": str(fy or ""), "fiscal_quarter": fq, "estimate_flag": "", "value": value, "value_raw": raw or ("%g" % value if value is not None else ""),
                "status": status, "note": "", "source_id": sid}
    facts = [fact("a.pdf", "Revenue", 2025, "", "FY", 1200.0, sid="r1"), fact("a.pdf", "Revenue", 2024, "", "FY", 1000.0, sid="r2"),
             fact("a.pdf", "Revenue", 2025, "2025-03", "FQ", 280.0, sid="r3"), fact("a.pdf", "Revenue", 2026, "", "FY", 9999.0, status="REJECTED", sid="r4"),
             fact("a.pdf", "Revenue", 2025, "", "FY", 1200.0, table="T2", sid="r5"),                     # 另一張表同值 → 報告層合併
             fact("a.pdf", "EPS", 2025, "", "FY", 6.1, table="T1", sid="r6"), fact("a.pdf", "EPS", 2025, "", "FY", 6.3, table="T2", sid="r7"),  # 兩張表不同值 → 衝突
             fact("b.pdf", "Revenue", 2025, "", "FY", 50.0, status="CORRECTED", sid="r8"), fact("b.pdf", "Revenue", None, "", "TTM", 70.0, sid="r9"),
             fact("a.pdf", "EPS", 2025, "", "FY", 7.0, table="T3", sid="r10", mraw="EPS (NT$)§"),   # 印的字不同（共識）→ 自己一列、不算衝突
             fact("a.pdf", "NetIncome", 2025, "", "FY", 4458.0, table="T1", raw="4,458", sid="r11"),
             fact("a.pdf", "NetIncome", 2025, "", "FY", 4457.8, table="T2", raw="4,457.8", sid="r12"),   # 同一個數、位數不同 → 取 4457.8
             fact("a.pdf", "OpIncome", 2025, "", "FY", 4458.0, table="T1", raw="4,458", sid="r13"),
             fact("a.pdf", "OpIncome", 2025, "", "FY", 4457.4, table="T2", raw="4,457.4", sid="r14"),    # 4457.4 四捨五入是 4457 → 衝突
             fact("AI末日論？假的.pdf", "Revenue", 2025, "", "FY", 10.0, sid="r15")]                      # 檔名照原字（全形「？」不能變成「?」）
    with tempfile.TemporaryDirectory(prefix="vrn_pivotdb_") as td:
        restored = [{"system": "TEST", "file": "a.pdf", "page": 1, "table_id": "T1", "title": "x", "verdict": "GREEN", "columns": ["", "2024", "2025"],
                     "cells": [["Revenue", "1,000", "1,200"], ["EPS", "5.2", "6.1"]]}]
        s = build_pivot_db(facts, td, restored, title="已知答案")
        con = sqlite3.connect(s["sqlite"])
        q = lambda sql: con.execute(sql).fetchall()  # noqa: E731
        checks.append(("期間鍵：全年 YYYY · 季 YYYY-MM · TTM 不進", [f["period_key"] for f in facts[:3]] == ["2025", "2024", "2025-03"] and facts[8]["period_key"] == ""))
        checks.append(("只收 VERIFIED / CORRECTED（REJECTED 的 2026 = 9999 不進，連欄都沒有）",
                       "2026" not in s["periods"]["pivot_annual"] and "2026" not in s["periods"]["pivot_report_annual"]))
        checks.append(("年度欄依時間排序", s["periods"]["pivot_annual"] == ["2024", "2025"]))
        checks.append(("表層 PIVOT：a.pdf T1 Revenue 2024 = 1000 · 2025 = 1200",
                       q("SELECT \"2024\", \"2025\" FROM pivot_annual WHERE file='a.pdf' AND table_id='T1' AND metric='Revenue'") == [(1000.0, 1200.0)]))
        checks.append(("季度 PIVOT 另一張表：2025-03 = 280", q("SELECT \"2025-03\" FROM pivot_quarterly WHERE metric='Revenue'") == [(280.0,)]))
        checks.append(("報告層：兩張表同值 → 合併成一格 1200", q("SELECT \"2025\" FROM pivot_report_annual WHERE file='a.pdf' AND metric='Revenue'") == [(1200.0,)]))
        checks.append(("報告層：兩張表不同值 → 留空 + 衝突一筆（不挑）",
                       q("SELECT \"2025\" FROM pivot_report_annual WHERE file='a.pdf' AND metric_raw='EPS'") == [(None,)]
                       and q("SELECT level, kind, \"values\", tables FROM conflicts WHERE metric='EPS'") == [("report", "value", "6.1 | 6.3", "T1 | T2")]))
        checks.append(("衝突的樣子：絕對值相同正負不同 = sign · 差 10 的次方 = scale · 其他 = value",
                       (conflict_kind([1002.0, -1002.0]), conflict_kind([1234.0, 1.234]), conflict_kind([6.1, 6.3])) == ("sign", "scale", "value")))
        checks.append(("報告層只合印的字一樣的列：EPS (NT$)§ = 7 自己一列、不併進 EPS",
                       q("SELECT \"2025\" FROM pivot_report_annual WHERE file='a.pdf' AND metric_raw='EPS (NT$)§'") == [(7.0,)]
                       and q("SELECT count(*) FROM conflicts WHERE metric='EPS'") == [(1,)]))
        checks.append(("精度：4,458 與 4,457.8 是同一個數 → 取 4457.8、記一筆精度合併；4,458 與 4,457.4 不是 → 衝突",
                       q("SELECT \"2025\" FROM pivot_report_annual WHERE metric='NetIncome'") == [(4457.8,)]
                       and q("SELECT level, kept, \"values\" FROM precision_merges") == [("report", 4457.8, "4,458 | 4,457.8")]
                       and q("SELECT \"2025\" FROM pivot_report_annual WHERE metric='OpIncome'") == [(None,)]
                       and q("SELECT \"values\" FROM conflicts WHERE metric='OpIncome'") == [("4,458 | 4,457.4",)]))
        checks.append(("CORRECTED 也收（b.pdf 50）", q("SELECT \"2025\" FROM pivot_report_annual WHERE file='b.pdf'") == [(50.0,)]))
        checks.append(("事實表保留全部（含沒收的）", q("SELECT count(*) FROM facts") == [(15,)]))
        checks.append(("檔名照原字：全形「？」不被 NFKC 改成「?」", q("SELECT file FROM pivot_report_annual WHERE file LIKE 'AI%'") == [("AI末日論？假的.pdf",)]))
        checks.append(("還原表攤成一格一列：Revenue × 2025 = 1200", q("SELECT value FROM restored_cells WHERE row_label='Revenue' AND col_header='2025'") == [(1200.0,)]))
        con.close()
        if s["duckdb"]:
            checks.append(("DuckDB 原生 PIVOT 檢視和實體表逐格相同", s["duckdb_check"].get("pivot_check") == "OK"))
        page = Path(s["html"]).read_text(encoding="utf-8")
        checks.append(("HTML U/I：分頁 · 篩選 · 嵌入安全（</script> 只有兩個）", page.count("</script>") == 2 and 'id="ff"' in page and 'id="tabs"' in page))
        checks.append(("契約不符 → 不寫、說清楚缺哪一欄", _raises(lambda: build_pivot_db([{"file": "x"}], td))))
        checks.append(("同一份輸入 → 同一個指紋", build_pivot_db(facts, Path(td) / "again", restored)["fingerprint"] == s["fingerprint"]))
    for name, ok in checks:
        if verbose:
            print("  [%s] %s" % ("PASS" if ok else "FAIL", name))
    passed = sum(1 for _n, ok in checks if ok)
    print("[計] %s 自測 %d/%d · %s" % (VERSION, passed, len(checks), "PASS" if passed == len(checks) else "FAIL"))
    return 0 if passed == len(checks) else 1


# [VRN-ID] VRN-ENG022-FNC028 · LOGIC
def _raises(fn) -> bool:
    try:
        fn()
    except ValueError:
        return True
    return False


# [VRN-ID] VRN-ENG022-FNC029 · ENTRY
def main(argv: Optional[Sequence[str]] = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] == ["--selftest"]:
        return selftest()
    if not args:
        print("用法：python VRN_PivotDB_v0100.py <VRN-1 round 夾> [輸出夾] · 或 --selftest")
        return 2
    s = build_from_vrn1_round(args[0], args[1] if len(args) > 1 else None, title=Path(args[0]).name)
    print(json.dumps({k: s[k] for k in ("counts", "fingerprint", "sqlite", "duckdb", "html")}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
