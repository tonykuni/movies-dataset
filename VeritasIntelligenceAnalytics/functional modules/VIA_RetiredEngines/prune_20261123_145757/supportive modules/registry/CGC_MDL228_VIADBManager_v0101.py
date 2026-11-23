#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL228_VIADBManager v0100 — VIA 資料庫中央管控(VCGC 內;現況總覽 · 數量核對 · 選取式匯出 · 儲存最佳化計畫)
v0100→v0101(側線 2026-09-28;工作站首跑實量後修):
  ① 匯出 --cols 在 PowerShell 被拆:`--cols date,ticker,close` 不加引號 = 陣列 → 傳成三個參數,v0100 只讀第一個,
     默默只匯 1 欄(實錄「353,827 列 × 1 欄」)。現在 --cols 收到下一個 -- 旗標前的所有字(逗號或空白都行);
     其他旗標後面多出來的字、不認得的旗標一律 BAD_PARAM 擋下,不再默默吞掉。
  ② 核對:政策同步表(冊上寫入者 VRN_ENG082 的表 = via_handover / via_policy_* / vrn_extraction_logic)依 L14 每本庫都該有一份,
     別的庫出現時判 GREEN「L14 全庫政策同步表」,不再報冊外(實錄 31 條 AMBER 裡 16 條是這個)。
  ③ plan 除了寫 JSON,另印精簡摘要(每項幾行),貼回就看得到內容,不用開檔。
  ④ 新動詞 ui:以同一份目錄重建主控台藍圖(委派 CGC_MDL227 尾版 build),印全頁位置。

操作員 2026-09-28 令(規劃見 docs/VIA_DBManager_Plan_20260928.md):
  P1+P2 開工;優化目標先做三項(壞檔清單 · mega 合併計畫 · _raw 定位),都只出計畫;
  資料家裡的 `_repo_` 庫 = 對帳檢查用的副本(不是殘留,不算重疊)。

這一支是門面,不是第二套:
  · 現況只讀 DataHome 一頁目錄(CGC_MDL123 catalog 寫的 DATAHOME_CATALOG_latest.json;token_saving_rules:不掃湖、不逐表 COUNT);
    表的三態用 EngineBus 普查同一把尺(CENSUS_THIN_DAYS · _span_days),與 via-census 同判。
  · 核對的「冊上期望」讀 VIA_DB_Table_SSOT(min_rows / rows_seen)。
  · 匯出:csv(utf-8-sig)與 Google Sheet 相容 csv 委派 VDF_ENG045 OutputHub.write_all(回讀核對);
    本支只補它沒有的 Big5(cp950,放不下的字逐字報數,不偷換)· Markdown(小範圍)· JSON · parquet(DuckDB COPY zstd)。
    讀庫一律 read_only;欄名、表名只收目錄與 PRAGMA 認得的(不拼使用者字串進 SQL);匯出只寫 VIA_Reports(L90 單向派生)。
  · 三項計畫:只量、只寫計畫檔,不刪、不搬、不改正庫(L10:刪與搬是操作員的手)。

用法:
  python CGC_MDL228_VIADBManager_v0100.py overview [--json]
  python CGC_MDL228_VIADBManager_v0100.py reconcile
  python CGC_MDL228_VIADBManager_v0100.py plan [bad|mega|raw|all]      # 寫 JSON 並印精簡摘要
  python CGC_MDL228_VIADBManager_v0100.py ui                            # 以同一份目錄重建主控台藍圖
  python CGC_MDL228_VIADBManager_v0100.py export --db <庫名> --table <表> [--cols a,b] [--start YYYY-MM-DD] [--end YYYY-MM-DD]
                                         [--format csv|big5|gsheet|md|json|parquet] [--limit N] [--dry]
  python CGC_MDL228_VIADBManager_v0100.py --selftest
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

import csv as _csv
import importlib.util
import json
import os
import re
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]
ENGINE_TAG = "CGC_MDL228_VIADBManager v" + VERSION
TABLE_BOOK = HERE / "VIA_DB_Table_SSOT_v0100.json"
OUT = VIA / "VIA_Reports" / "dbmanager"
REPLICA_RX = re.compile(r"_repo_[0-9a-f]{6,}", re.I)      # 操作員 2026-09-28:對帳檢查用的副本
MEGA_TS_RX = re.compile(r"^(?P<stem>.+?)_(?P<ts>\d{8}(?:_\d{4,6})?|\d{14})$")
ISO_RX = re.compile(r"^\d{4}-\d{2}-\d{2}")
FORMATS = ("csv", "big5", "gsheet", "md", "json", "parquet")
#: 每種格式一次匯出的列數上限(大範圍請用 parquet / csv;MD 只給人看小表)
CAP = {"csv": 1_000_000, "big5": 1_000_000, "gsheet": 1_000_000, "md": 2_000, "json": 200_000, "parquet": 50_000_000}
CATALOG_STALE_H = 48


# ---------------------------------------------------------------- 正主載入(唯讀用途)
def _tail(folder: Path, glob: str):
    try:
        hits = sorted(p for p in Path(folder).glob(glob) if p.is_file())
    except OSError:
        return None
    return hits[-1] if hits else None


_MODS: dict = {}


def _mod(key: str):
    """正主尾版:datahome(CGC_MDL123)· bus(CGC_MDL148)· hub(VDF_ENG045)。載不到回 None(照實,不自己補一份)。"""
    if key in _MODS:
        return _MODS[key]
    where = {"datahome": (HERE, "CGC_MDL123_DataHome_v*.py"), "bus": (HERE, "CGC_MDL148_EngineBus_v*.py"),
             "hub": (VIA / "functional modules" / "VDF", "VDF_ENG045_OutputHub_v*.py")}[key]
    p = _tail(*where)
    m = None
    if p is not None:
        try:
            spec = importlib.util.spec_from_file_location(f"vdbm_{key}", str(p))
            m = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = m
            spec.loader.exec_module(m)
        except Exception:
            m = None
    _MODS[key] = m
    return m


def catalog_path() -> Path:
    m = _mod("datahome")
    return Path(getattr(m, "CATALOG", VIA / "VIA_Reports" / "datahome" / "DATAHOME_CATALOG_latest.json"))


def load_catalog(path: Path | None = None) -> tuple:
    """回 (目錄, 狀態, 原因)。狀態:OK · ABSENT(沒跑過)· UNREADABLE。"""
    p = Path(path or catalog_path())
    try:
        return json.loads(p.read_text(encoding="utf-8")), "OK", ""
    except FileNotFoundError:
        return None, "ABSENT", f"目錄頁不在:{p}(工作站先跑 via-datahome catalog -Tables)"
    except (OSError, ValueError) as exc:
        return None, "UNREADABLE", f"目錄頁讀不動:{type(exc).__name__}"


def _book(path: Path = TABLE_BOOK) -> list:
    try:
        return list(json.loads(Path(path).read_text(encoding="utf-8")).get("tables") or [])
    except (OSError, ValueError):
        return []


# ---------------------------------------------------------------- P1 現況總覽
def _span(lo: str, hi: str):
    bus = _mod("bus")
    if bus is not None and hasattr(bus, "_span_days"):
        try:
            return bus._span_days(lo, hi)
        except Exception:
            return None
    try:
        return (datetime.fromisoformat(hi[:10]) - datetime.fromisoformat(lo[:10])).days + 1
    except Exception:
        return None


def _thin_days() -> int:
    return int(getattr(_mod("bus"), "CENSUS_THIN_DAYS", 30))


def table_state(t: dict) -> str:
    """與 EngineBus 普查同判:0 列 = NODATA;讀不動 = RED;跨度 < 門檻天 = AMBER;其餘 GREEN。"""
    n = int(t.get("rows", -1))
    if n < 0:
        return "RED"
    if n == 0:
        return "NODATA"
    if t.get("date_col") and t.get("lo") and t.get("hi"):
        sp = _span(t["lo"], t["hi"])
        if sp is not None and sp < _thin_days():
            return "AMBER"
    return "GREEN"


def _role(name: str) -> str:
    return "對帳副本" if REPLICA_RX.search(name or "") else "正庫"


def overview(cat: dict | None = None, cat_state: str = "OK", cat_why: str = "", now: datetime | None = None) -> dict:
    """一頁目錄 → 固定欄位總表(庫 / 表 / 湖)。目錄缺 = NODATA 並講怎麼補,不自己去掃庫。"""
    now = now or datetime.now()
    ov = {"engine": ENGINE_TAG, "built_at": now.strftime("%Y-%m-%d %H:%M:%S"), "catalog_state": cat_state,
          "catalog_why": cat_why, "catalog_ts": "", "stale": False, "dbs": [], "tables": [], "lakes": [], "kpi": {}}
    if cat is None:
        ov["state"] = "NODATA"
        return ov
    ov["catalog_ts"] = str(cat.get("ts") or "")
    ov["home"] = str(cat.get("home") or "")
    try:
        age_h = (now - datetime.strptime(ov["catalog_ts"][:19], "%Y-%m-%d %H:%M:%S")).total_seconds() / 3600
        ov["age_hours"] = round(age_h, 1)
        ov["stale"] = age_h > CATALOG_STALE_H
    except ValueError:
        ov["age_hours"] = None
    for db in cat.get("dbs") or []:
        role = _role(db.get("name", ""))
        tabs = []
        for t in db.get("tables") or []:
            st = table_state(t)
            row = {"db": db.get("name"), "role": role, "table": t.get("table"), "rows": int(t.get("rows", -1)),
                   "date_col": t.get("date_col") or "", "lo": (t.get("lo") or "")[:10], "hi": (t.get("hi") or "")[:10],
                   "sentinel": int(t.get("sentinel") or 0), "state": st,
                   "iso_dates": bool(ISO_RX.match(t.get("lo") or "")) if t.get("lo") else None}
            tabs.append(row)
            ov["tables"].append(row)
        cnt = {}
        for r in tabs:
            cnt[r["state"]] = cnt.get(r["state"], 0) + 1
        his = [r["hi"] for r in tabs if ISO_RX.match(r["hi"] or "")]
        ov["dbs"].append({"name": db.get("name"), "role": role, "rel": db.get("rel") or "", "mb": db.get("mb"),
                          "mtime": db.get("mtime"), "state": db.get("state"), "why": db.get("why", ""),
                          "tables": len(tabs), "rows": sum(max(r["rows"], 0) for r in tabs),
                          "latest": max(his) if his else "", "counts": cnt})
    for lk in cat.get("lake") or []:
        name = str(lk.get("dataset") or "")
        kind = ("raw" if "year=_raw" in name else "snap" if "year=_snap" in name else
                "year" if re.search(r"year=\d{4}", name) else "mega" if name == "mega" else "set")
        ov["lakes"].append({"dataset": name, "kind": kind, "files": lk.get("files"), "mb": lk.get("mb"),
                            "rows": lk.get("rows"), "lo": (lk.get("lo") or "")[:10], "hi": (lk.get("hi") or "")[:10],
                            "iso_dates": bool(ISO_RX.match(lk.get("lo") or "")) if lk.get("lo") else None,
                            "bad": len(lk.get("bad") or []), "state": lk.get("state"), "mixed": bool(lk.get("mixed"))})
    main = [d for d in ov["dbs"] if d["role"] == "正庫"]
    cnt = {}
    for r in ov["tables"]:
        if r["role"] == "正庫":
            cnt[r["state"]] = cnt.get(r["state"], 0) + 1
    ov["kpi"] = {"dbs": len(main), "replicas": len(ov["dbs"]) - len(main), "tables": sum(d["tables"] for d in main),
                 "rows": sum(d["rows"] for d in main), "latest": max((d["latest"] for d in main if d["latest"]), default=""),
                 "lakes": len(ov["lakes"]), "lake_files": sum(int(x.get("files") or 0) for x in ov["lakes"]),
                 "bad_files": sum(x["bad"] for x in ov["lakes"]), "states": cnt}
    ov["state"] = "AMBER" if ov["stale"] else "OK"
    return ov


def reconcile(ov: dict, book: list | None = None) -> list:
    """冊上期望 vs 目錄實量。只增不減律下「比上次量少」要有人解釋(AMBER),低於冊下限才是 RED。"""
    book = _book() if book is None else book
    have = {(r["db"], r["table"]): r for r in ov.get("tables") or [] if r["role"] == "正庫"}
    dbs = {d["name"] for d in ov.get("dbs") or []}
    out, seen = [], set()
    for b in book:
        key = (b.get("db"), b.get("table"))
        seen.add(key)
        exp_min, seen_n = int(b.get("min_rows") or 0), b.get("rows_seen")
        r = have.get(key)
        if b.get("db") not in dbs:
            st, why, n = "ABSENT", "整本庫不在目錄", None
        elif r is None:
            st, why, n = "RED", "冊上宣告,庫裡沒有這張表", None
        else:
            n = r["rows"]
            if n < 0:
                st, why = "RED", "讀不動"
            elif n < exp_min:
                st, why = "RED", f"低於冊下限 {exp_min}"
            elif n == 0:
                st, why = "NODATA", "0 列(冊下限 0)"
            elif isinstance(seen_n, int) and n < seen_n:
                st, why = "AMBER", f"比冊上次量少 {seen_n - n:,}(只增不減:要有人說明)"
            else:
                st, why = "GREEN", (f"+{n - seen_n:,}" if isinstance(seen_n, int) else "")
        out.append({"db": b.get("db"), "table": b.get("table"), "expected_min": exp_min, "rows_seen": seen_n,
                    "rows_now": n, "state": st, "why": why})
    policy_sync = {b.get("table") for b in book if any("VRN_ENG082" in str(w) for w in (b.get("writers") or []))}
    for key, r in have.items():
        if key not in seen:
            if key[1] in policy_sync:
                out.append({"db": key[0], "table": key[1], "expected_min": None, "rows_seen": None, "rows_now": r["rows"],
                            "state": "GREEN", "why": "L14 全庫政策同步表(每本庫同一份;冊上登在寫入者 VRN_ENG082 那本)"})
                continue
            out.append({"db": key[0], "table": key[1], "expected_min": None, "rows_seen": None, "rows_now": r["rows"],
                        "state": "AMBER", "why": "冊外:庫裡有、冊上沒登(請入冊)"})
    # 對帳副本 vs 正庫(操作員令:副本是對帳用的 → 列出同名表的列數差)
    main_by = {}
    for r in ov.get("tables") or []:
        if r["role"] == "正庫":
            main_by.setdefault(r["table"], []).append(r)
    for r in ov.get("tables") or []:
        if r["role"] != "對帳副本":
            continue
        base = REPLICA_RX.sub("", r["db"] or "")
        m = next((x for x in main_by.get(r["table"], []) if x["db"] == base), None)
        if m is None:
            st, why = "AMBER", f"正庫 {base} 沒有同名表"
        elif m["rows"] == r["rows"]:
            st, why = "GREEN", "副本與正庫列數一致"
        else:
            st, why = "AMBER", f"副本 {r['rows']:,} vs 正庫 {m['rows']:,}(差 {r['rows'] - m['rows']:+,})"
        out.append({"db": r["db"], "table": r["table"], "expected_min": None, "rows_seen": m["rows"] if m else None,
                    "rows_now": r["rows"], "state": st, "why": "對帳副本 · " + why})
    order = {"RED": 0, "ABSENT": 1, "AMBER": 2, "NODATA": 3, "GREEN": 4}
    out.sort(key=lambda x: (order.get(x["state"], 9), str(x["db"]), str(x["table"])))
    return out


# ---------------------------------------------------------------- 三項計畫(只量、只寫計畫,不動正庫)
def plan_bad(cat: dict) -> list:
    """優化目標 5:湖裡讀不動的 parquet 逐檔列出(目錄已記在 bad)。處置 = 操作員移到隔離夾,本支不動檔。"""
    out = []
    for lk in (cat or {}).get("lake") or []:
        for b in lk.get("bad") or []:
            f, _, err = str(b).partition(":")
            out.append({"dataset": lk.get("dataset"), "dir": lk.get("dir") or lk.get("rel"), "file": f, "error": err.strip()[:160],
                        "action": "移到隔離夾(操作員);目錄與掃描不再讀它;若是寫到一半的檔,查寫入引擎是否該原子換名"})
    return out


def plan_mega(cat: dict) -> list:
    """優化目標 4:mega 夾「每跑一次一個時間戳檔」→ 同表按年合併成 part-YYYY.parquet 的計畫(含 SQL 與回讀核對)。"""
    groups: dict = {}
    for lk in (cat or {}).get("lake") or []:
        if str(lk.get("dataset")) != "mega":
            continue
        base = lk.get("dir") or ""
        for m in lk.get("members") or []:
            mm = MEGA_TS_RX.match(str(m.get("table") or ""))
            stem = mm.group("stem") if mm else str(m.get("table"))
            g = groups.setdefault(stem, {"stem": stem, "files": [], "rows": 0, "lo": "", "hi": "", "date_col": "", "dir": base})
            g["files"].append(m.get("file"))
            g["rows"] += int(m.get("rows") or 0)
            g["date_col"] = g["date_col"] or (m.get("date_col") or "")
            lo, hi = str(m.get("lo") or ""), str(m.get("hi") or "")
            if lo and (not g["lo"] or lo < g["lo"]):
                g["lo"] = lo
            if hi and hi > g["hi"]:
                g["hi"] = hi
    out = []
    for g in sorted(groups.values(), key=lambda x: -len(x["files"])):
        files = [str(Path(g["dir"]) / f) if g["dir"] else f for f in g["files"]]
        src = "read_parquet([" + ", ".join("'" + f.replace("'", "''") + "'" for f in files) + "], union_by_name=true)"
        iso = bool(ISO_RX.match(g["lo"])) and bool(ISO_RX.match(g["hi"]))
        years = list(range(int(g["lo"][:4]), int(g["hi"][:4]) + 1)) if iso else []
        target = f"mega/{g['stem']}/part-YYYY.parquet" if years else f"mega/{g['stem']}/part-all.parquet"
        dc = g["date_col"]
        sql = ([f"COPY (SELECT DISTINCT * FROM {src} WHERE year(CAST(\"{dc}\" AS DATE)) = {y} ORDER BY \"{dc}\") "
                f"TO 'mega/{g['stem']}/part-{y}.parquet' (FORMAT PARQUET, COMPRESSION ZSTD);" for y in years]
               if years else [f"COPY (SELECT DISTINCT * FROM {src}) TO 'mega/{g['stem']}/part-all.parquet' (FORMAT PARQUET, COMPRESSION ZSTD);"])
        out.append({"stem": g["stem"], "files": len(g["files"]), "rows_in": g["rows"], "date_col": dc, "lo": g["lo"][:10],
                    "hi": g["hi"][:10], "target": target, "target_files": max(len(years), 1),
                    "note": ("只出計畫;DISTINCT 會去掉重跑重疊,合併後列數要量;回讀列數 = 計畫列數才換上,舊檔由操作員移走"
                             if len(g["files"]) > 1 else "只有 1 檔,不需合併"),
                    "sql": sql})
    return out


def plan_raw(cat: dict) -> list:
    """優化目標 2:湖的 _raw 與年檔對照 → 判定整份重複 / _raw 多出 / _raw 較少,給出定位建議(不動檔)。"""
    fam: dict = {}
    for lk in (cat or {}).get("lake") or []:
        name = str(lk.get("dataset") or "")
        m = re.match(r"^(?P<fam>.+?)/year=(?P<y>\d{4}|_raw|_snap)$", name)
        if not m:
            continue
        f = fam.setdefault(m.group("fam"), {"years": [], "raw": None, "snap": None})
        if m.group("y") == "_raw":
            f["raw"] = lk
        elif m.group("y") == "_snap":
            f["snap"] = lk
        else:
            f["years"].append(lk)
    out = []
    for name, f in sorted(fam.items()):
        if f["raw"] is None:
            continue
        yrows = sum(int(x.get("rows") or 0) for x in f["years"])
        raw = int(f["raw"].get("rows") or 0)
        ylo = min((str(x.get("lo") or "") for x in f["years"] if x.get("lo")), default="")
        yhi = max((str(x.get("hi") or "") for x in f["years"] if x.get("hi")), default="")
        rlo, rhi = str(f["raw"].get("lo") or ""), str(f["raw"].get("hi") or "")
        comparable = all(ISO_RX.match(v) for v in (ylo, yhi, rlo, rhi) if v)
        if not f["years"]:
            verdict, advice = "RAW_ONLY", "只有 _raw 沒有年檔:先按年分片(ENG073 optimize_plan)再談歸檔"
        elif raw == yrows and (not comparable or (rlo >= ylo and rhi <= yhi)):
            verdict, advice = "FULL_DUP", "與年檔整份重複:_raw 定為只讀歸檔,目錄與引擎掃描跳過(移夾由操作員)"
        elif raw > yrows:
            extra = []
            if comparable and rlo and ylo and rlo < ylo:
                extra.append(f"_raw 早於年檔的區段 {rlo[:10]} → {ylo[:10]}(含哨兵列要先標)")
            verdict = "RAW_SUPERSET"
            advice = (f"_raw 比年檔多 {raw - yrows:,} 列:" + ("; ".join(extra) if extra else "多出的部分要逐年核對")
                      + " → 先把要留的區段補成年檔、哨兵列標出,再歸檔 _raw")
        else:
            verdict, advice = "RAW_SUBSET", f"年檔比 _raw 多 {yrows - raw:,} 列:_raw 是較舊快照,可歸檔"
        if not comparable:
            advice += "(日期格式非西元,範圍比較停用,只比列數)"
        out.append({"family": name, "year_files": sum(int(x.get("files") or 0) for x in f["years"]), "year_rows": yrows,
                    "year_lo": ylo[:10], "year_hi": yhi[:10], "raw_rows": raw, "raw_lo": rlo[:10], "raw_hi": rhi[:10],
                    "verdict": verdict, "advice": advice})
    return out


def plan_summary(plans: dict, top: int = 8) -> list:
    """三項計畫的精簡摘要(貼回看得懂、不用開檔)。"""
    lines = []
    if "bad" in plans:
        by = {}
        for b in plans["bad"]:
            by[b["dataset"]] = by.get(b["dataset"], 0) + 1
        lines.append(f"[計畫 5 壞檔] {len(plans['bad'])} 檔 · " + " · ".join(f"{k} {v}" for k, v in sorted(by.items(), key=lambda x: -x[1])))
        for b in plans["bad"][:3]:
            lines.append(f"    {b['dataset']}/{b['file']} · {b['error'][:70]}")
    if "mega" in plans:
        many = [m for m in plans["mega"] if m["files"] > 1]
        lines.append(f"[計畫 4 mega 合併] {len(plans['mega'])} 表 · 要合併 {len(many)} 表 · {sum(m['files'] for m in many)} 檔 → "
                     f"{sum(m['target_files'] for m in many)} 檔")
        for m in many[:top]:
            lines.append(f"    {m['stem'][:34]:34s} {m['files']:4d} 檔 · {m['rows_in']:>11,} 列 · {m['lo'] or '—'} → {m['hi'] or '—'} → {m['target']}")
    if "raw" in plans:
        lines.append(f"[計畫 2 _raw 定位] {len(plans['raw'])} 族")
        for x in plans["raw"]:
            lines.append(f"    {x['family']:10s} {x['verdict']:13s} 年檔 {x['year_rows']:>11,} · _raw {x['raw_rows']:>11,} · {x['advice'][:90]}")
    return lines


def write_plans(cat: dict, which: str = "all", out: Path = OUT) -> dict:
    res = {}
    for k, fn in (("bad", plan_bad), ("mega", plan_mega), ("raw", plan_raw)):
        if which in (k, "all"):
            res[k] = fn(cat)
    out.mkdir(parents=True, exist_ok=True)
    p = out / "DBM_PLANS_latest.json"
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps({"engine": ENGINE_TAG, "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                               "catalog_ts": (cat or {}).get("ts"), "plans": res,
                               "rule": "只出計畫;刪、搬、改正庫一律操作員(L10)"}, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, p)
    return {"path": str(p), **{k: len(v) for k, v in res.items()}, "summary": plan_summary(res)}


# ---------------------------------------------------------------- P2 選取式匯出
def _db_path(cat: dict, db: str):
    for d in (cat or {}).get("dbs") or []:
        if d.get("name") == db:
            return Path(d["path"]), d
    return None, None


def _q(ident: str) -> str:
    return '"' + str(ident).replace('"', '""') + '"'


def export(cat: dict, db: str, table: str, cols=None, start: str = "", end: str = "", fmt: str = "csv",
           limit: int | None = None, dry: bool = False, out: Path = OUT) -> dict:
    """選取式匯出:庫 → 表 → 欄 → 期間 → 格式。唯讀連線;先數再寫;寫完回讀核對。"""
    t0 = time.time()
    res = {"db": db, "table": table, "columns": [], "range": f"{start or '…'} → {end or '…'}", "format": fmt,
           "encoding": "", "rows": None, "lossy_chars": 0, "output_path": "", "readback_rows": None, "state": "", "why": ""}

    def done(state, why=""):
        res.update(state=state, why=why, secs=round(time.time() - t0, 2))
        return res

    if fmt not in FORMATS:
        return done("BAD_PARAM", f"格式只收 {', '.join(FORMATS)}")
    path, dent = _db_path(cat, db)
    if path is None:
        return done("ABSENT", f"目錄上沒有這本庫:{db}")
    tent = next((t for t in dent.get("tables") or [] if t.get("table") == table), None)
    if tent is None:
        return done("ABSENT", f"{db} 目錄上沒有這張表:{table}")
    for v in (start, end):
        if v and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
            return done("BAD_PARAM", f"日期要 YYYY-MM-DD:{v}")
    dcol = tent.get("date_col") or ""
    if (start or end) and not dcol:
        return done("NO_DATE_COL", "這張表沒有日期欄:期間篩選停用(可不給期間整表匯出)")
    if (start or end) and tent.get("lo") and not ISO_RX.match(str(tent.get("lo"))):
        return done("NO_DATE_COL", f"日期欄 {dcol} 不是西元日期(例 {tent.get('lo')}):期間篩選停用")
    try:
        import duckdb
    except Exception:
        return done("NODUCKDB", "本環境沒有 duckdb")
    try:
        con = duckdb.connect(str(path), read_only=True)
    except Exception as exc:
        s = str(exc)
        return done("BUSY" if "lock" in s.lower() or "being used" in s else "FAIL", s[:160])
    try:
        real = [str(r[1]) for r in con.execute(f"PRAGMA table_info({_q(table)})").fetchall()]
        want = [c.strip() for c in (cols.split(",") if isinstance(cols, str) else (cols or [])) if c and c.strip()] or real
        bad = [c for c in want if c not in real]
        if bad:
            return done("BAD_PARAM", f"表上沒有這些欄:{bad}")
        res["columns"] = want
        where, args = "", []
        if start or end:
            cond = []
            if start:
                cond.append(f"CAST({_q(dcol)} AS VARCHAR) >= ?")
                args.append(start)
            if end:
                cond.append(f"CAST({_q(dcol)} AS VARCHAR) <= ?")
                args.append(end + "\uffff")                 # 含當天(時間戳也收)
            where = " WHERE " + " AND ".join(cond)
        n = int(con.execute(f"SELECT COUNT(*) FROM {_q(table)}{where}", args).fetchone()[0])
        cap = min(CAP[fmt], int(limit)) if limit else CAP[fmt]
        take = min(n, cap)
        res["rows"] = take
        order = f" ORDER BY {_q(dcol)}" if dcol and dcol in real else ""
        sql = f"SELECT {', '.join(_q(c) for c in want)} FROM {_q(table)}{where}{order} LIMIT {int(take)}"
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = re.sub(r"[^\w.-]", "_", f"{Path(db).stem}__{table}__{start or 'all'}_{end or 'all'}_{stamp}")
        ext = {"csv": ".csv", "big5": ".big5.csv", "gsheet": ".gsheet.csv", "md": ".md", "json": ".json", "parquet": ".parquet"}[fmt]
        target = Path(out) / "exports" / (stem + ext)
        res["output_path"] = str(target)
        if n > cap:
            res["why"] = f"符合 {n:,} 列,超過 {fmt} 上限 {cap:,}:只取前 {cap:,} 列(依日期排序);全量請用 parquet"
        if dry:
            return done("PLAN", res["why"] or f"將匯出 {take:,} 列 × {len(want)} 欄")
        target.parent.mkdir(parents=True, exist_ok=True)
        if fmt == "parquet":
            tmp = target.with_suffix(".tmp.parquet")
            con.execute(f"COPY ({sql}) TO '{str(tmp).replace(chr(39), chr(39) * 2)}' (FORMAT PARQUET, COMPRESSION ZSTD)", args)
            os.replace(tmp, target)
            rb = int(duckdb.connect().execute(f"SELECT SUM(num_rows) FROM parquet_file_metadata('{str(target).replace(chr(39), chr(39) * 2)}')").fetchone()[0] or 0)
            res.update(encoding="parquet zstd", readback_rows=rb)
            return done("OK" if rb == take else "READBACK_MISMATCH", res["why"])
        cur = con.execute(sql, args)
        rows = [dict(zip(want, [("" if v is None else v if isinstance(v, (int, float, str)) else str(v)) for v in r]))
                for r in cur.fetchall()]
    finally:
        con.close()
    if fmt in ("csv", "gsheet"):
        hub = _mod("hub")
        if hub is None or not hasattr(hub, "write_all"):
            return done("ABSENT", "VDF_ENG045 OutputHub 載不到:csv / gsheet 不另寫一份")
        tmpdir = target.parent / ("_hub_" + stem)
        mat = hub.write_all(rows, stem, [fmt], tmpdir)
        rec = mat[0] if mat else {}
        produced = tmpdir / (rec.get("file") or "")
        if produced.is_file():
            os.replace(produced, target)
        for leftover in tmpdir.glob("*"):
            leftover.unlink()
        tmpdir.rmdir()
        res.update(encoding="utf-8-sig(Excel 直開)" if fmt == "csv" else "utf-8(Sheets 匯入)", readback_rows=rec.get("rows"))
        ok = str(rec.get("status", "")).startswith(("OK", "COMPAT_CSV")) and rec.get("rows") == take
        return done("OK" if ok else "READBACK_MISMATCH", res["why"] or str(rec.get("note") or ""))
    if fmt == "big5":
        lossy, sample = 0, []

        def enc(v):
            nonlocal lossy
            s = str(v)
            try:
                s.encode("cp950")
                return s
            except UnicodeEncodeError:
                out_ = []
                for ch in s:
                    try:
                        ch.encode("cp950")
                        out_.append(ch)
                    except UnicodeEncodeError:
                        lossy += 1
                        if len(sample) < 8 and ch not in sample:
                            sample.append(ch)
                        out_.append("?")
                return "".join(out_)
        with open(target, "w", encoding="cp950", newline="") as fh:
            w = _csv.writer(fh)
            w.writerow([enc(c) for c in want])
            for r in rows:
                w.writerow([enc(r[c]) for c in want])
        with open(target, encoding="cp950", newline="") as fh:
            rb = sum(1 for _ in _csv.reader(fh)) - 1
        res.update(encoding="Big5(cp950)", lossy_chars=lossy, readback_rows=rb)
        why = res["why"]
        if lossy:
            why = (why + ";" if why else "") + f"Big5 放不下 {lossy} 個字(例 {''.join(sample)})已寫成 ?;要原字請用 csv(utf-8-sig)"
        return done("LOSSY" if lossy else ("OK" if rb == take else "READBACK_MISMATCH"), why)
    if fmt == "md":
        def cell(v):
            return str(v).replace("|", "\\|").replace("\r", " ").replace("\n", " ")
        lines = [f"# {db} · {table}", "", f"期間:{res['range']} · 列數:{take:,}" + (f" · {res['why']}" if res["why"] else ""), "",
                 "| " + " | ".join(cell(c) for c in want) + " |", "|" + "---|" * len(want)]
        lines += ["| " + " | ".join(cell(r[c]) for c in want) + " |" for r in rows]
        target.write_text("\n".join(lines) + "\n", encoding="utf-8")
        rb = sum(1 for ln in target.read_text(encoding="utf-8").splitlines() if ln.startswith("| ")) - 1
        res.update(encoding="utf-8 markdown", readback_rows=rb)
        return done("OK" if rb == take else "READBACK_MISMATCH", res["why"])
    target.write_text(json.dumps({"db": db, "table": table, "columns": want, "range": res["range"], "rows": rows},
                                 ensure_ascii=False, default=str), encoding="utf-8")
    rb = len(json.loads(target.read_text(encoding="utf-8"))["rows"])
    res.update(encoding="utf-8 json", readback_rows=rb)
    return done("OK" if rb == take else "READBACK_MISMATCH", res["why"])


def ui_payload(cat=None, cat_state="OK", cat_why="") -> dict:
    """給主控台藍圖(CGC_MDL227)的統一輸出:總覽 + 核對 + 三項計畫摘要。"""
    if cat is None and cat_state == "OK":
        cat, cat_state, cat_why = load_catalog()
    ov = overview(cat, cat_state, cat_why)
    return {"overview": ov, "reconcile": reconcile(ov) if cat else [],
            "plans": {"bad": plan_bad(cat), "mega": plan_mega(cat), "raw": plan_raw(cat)} if cat else {},
            "formats": list(FORMATS), "caps": CAP, "cmd": f'python "{Path(__file__).relative_to(VIA).as_posix()}"'}


# ---------------------------------------------------------------- 自測(沙盒;L17 零污染)
def _mk_home(root: Path):
    import duckdb
    home = root / "via_database"
    (home / "mega").mkdir(parents=True)
    con = duckdb.connect(str(home / "vdf_tw_market.duckdb"))
    con.execute("CREATE TABLE tw_daily_prices AS SELECT DATE '2024-01-01' + INTERVAL (i) DAY AS date, "
                "(2330 + i % 3)::VARCHAR AS ticker, 100.0 + i AS close, '台積電' || CASE WHEN i = 5 THEN '𠮷' ELSE '' END AS name "
                "FROM range(60) t(i)")
    con.execute("CREATE TABLE tw_listings AS SELECT '2330' AS ticker, '台積電' AS name")
    con.execute("CREATE TABLE empty_t (date DATE)")
    con.execute("CREATE TABLE extra_t AS SELECT 1 AS x")
    con.close()
    con = duckdb.connect(str(home / "vdf_tw_market_repo_a7752b3d.duckdb"))
    con.execute("CREATE TABLE tw_daily_prices AS SELECT DATE '2024-01-01' + INTERVAL (i) DAY AS date FROM range(58) t(i)")
    con.close()
    c = duckdb.connect()
    for y, n in ((2024, 30), (2025, 20)):
        (home / "chip" / f"year={y}").mkdir(parents=True)
        c.execute(f"COPY (SELECT DATE '{y}-01-01' + INTERVAL (i) DAY AS date, i AS v FROM range({n}) t(i)) "
                  f"TO '{home}/chip/year={y}/part-{y}.parquet' (FORMAT PARQUET)")
    (home / "chip" / "year=_raw").mkdir(parents=True)
    c.execute(f"COPY (SELECT * FROM read_parquet('{home}/chip/year=2*/*.parquet')) TO '{home}/chip/year=_raw/chip_raw.parquet' (FORMAT PARQUET)")
    (home / "px" / "year=2024").mkdir(parents=True)
    (home / "px" / "year=_raw").mkdir(parents=True)
    c.execute(f"COPY (SELECT DATE '2024-01-01' + INTERVAL (i) DAY AS date FROM range(10) t(i)) TO '{home}/px/year=2024/part-2024.parquet' (FORMAT PARQUET)")
    c.execute(f"COPY (SELECT DATE '1900-01-01' AS date UNION ALL SELECT DATE '2024-01-01' + INTERVAL (i) DAY FROM range(10) t(i)) "
              f"TO '{home}/px/year=_raw/px_raw.parquet' (FORMAT PARQUET)")
    for k, (d0, n) in enumerate((("2026-08-25", 5), ("2026-08-26", 5), ("2026-09-01", 4))):
        c.execute(f"COPY (SELECT DATE '{d0}' + INTERVAL (i) DAY AS date, i AS v FROM range({n}) t(i)) "
                  f"TO '{home}/mega/tw_daily_prices_2026090{k + 1}_1200.parquet' (FORMAT PARQUET)")
    c.execute(f"COPY (SELECT DATE '2026-09-01' AS date) TO '{home}/mega/tw_universe_20260911_0900.parquet' (FORMAT PARQUET)")
    c.close()
    (home / "fiveday").mkdir()
    (home / "fiveday" / "FIVEDAY_20260903_224732.parquet").write_bytes(b"PAR1 not really a parquet")
    c = duckdb.connect()
    c.execute(f"COPY (SELECT 1 AS x) TO '{home}/fiveday/FIVEDAY_20260904_100000.parquet' (FORMAT PARQUET)")
    c.close()
    return home


def selftest() -> int:
    print(f"=== {ENGINE_TAG} · 資料庫中央管控自測(沙盒家;零網路;不碰真庫 L17)===")
    res = []

    def chk(name, ok, note=""):
        res.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}" + (f" ({note})" if note else ""))

    saved = {k: os.environ.pop(k) for k in list(os.environ) if k.startswith("VIA_DB_") or k == "VIA_DATA_HOME"}
    try:
        import duckdb  # noqa: F401
    except Exception:
        print("  [SKIP] 本環境沒有 duckdb:匯出與沙盒家驗不了(誠實 SKIP,不當綠)")
        return 0
    dh = _mod("datahome")
    try:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            home = _mk_home(root)
            snap = {p: p.stat().st_mtime_ns for p in home.rglob("*") if p.is_file()}
            cat = dh.catalog(via=root, home=str(home), tables=False, do_print=False, write=False)
            chk("① 現況只讀正主 CGC_MDL123 catalog 的一頁目錄(沙盒家:2 本庫 + 湖)", cat.get("state") == "OK" and len(cat["dbs"]) == 2,
                f"庫 {len(cat['dbs'])} · 湖 {len(cat['lake'])}")
            ov = overview(cat, now=datetime.strptime(cat["ts"], "%Y-%m-%d %H:%M:%S"))
            roles = {d["name"]: d["role"] for d in ov["dbs"]}
            st = {(r["db"], r["table"]): r["state"] for r in ov["tables"]}
            chk("② `_repo_` 庫 = 對帳副本(操作員令),不算正庫;表三態與普查同判(0 列 NODATA · 跨度<30 天 AMBER · 其餘 GREEN)",
                roles.get("vdf_tw_market_repo_a7752b3d.duckdb") == "對帳副本" and ov["kpi"]["dbs"] == 1 and ov["kpi"]["replicas"] == 1
                and st[("vdf_tw_market.duckdb", "empty_t")] == "NODATA" and st[("vdf_tw_market.duckdb", "tw_daily_prices")] == "GREEN",
                f"{roles} · {ov['kpi']['states']}")
            old = overview(cat, now=datetime.strptime(cat["ts"], "%Y-%m-%d %H:%M:%S").replace(year=2027))
            none = overview(None, "ABSENT", "目錄頁不在")
            chk("③ 目錄過期(>48h)= AMBER 並標 stale;目錄不在 = NODATA 並講怎麼補(不自己去掃庫)",
                old["stale"] and old["state"] == "AMBER" and none["state"] == "NODATA" and none["catalog_state"] == "ABSENT")
            book = [{"db": "vdf_tw_market.duckdb", "table": "tw_daily_prices", "min_rows": 1, "rows_seen": 80},
                    {"db": "vdf_tw_market.duckdb", "table": "tw_listings", "min_rows": 1, "rows_seen": 1},
                    {"db": "vdf_tw_market.duckdb", "table": "tw_financial_mops", "min_rows": 0, "rows_seen": 0},
                    {"db": "vdf_tw_market.duckdb", "table": "empty_t", "min_rows": 5, "rows_seen": 0},
                    {"db": "nope.duckdb", "table": "x", "min_rows": 0}]
            rc = {(r["db"], r["table"], r["why"][:4]): r["state"] for r in reconcile(ov, book)}
            rcl = reconcile(ov, book)
            g = lambda t, pre="": next(r for r in rcl if r["table"] == t and r["db"].startswith(pre or "vdf_tw_market.duckdb"))
            chk("④ 數量核對:比冊上次量少 = AMBER(只增不減要說明)· 冊上有庫裡沒有 = RED · 低於冊下限 = RED · 整本庫不在 = ABSENT · 冊外表 = AMBER 請入冊",
                g("tw_daily_prices")["state"] == "AMBER" and g("tw_financial_mops")["state"] == "RED" and g("empty_t")["state"] == "RED"
                and next(r for r in rcl if r["table"] == "x")["state"] == "ABSENT" and "冊外" in g("extra_t")["why"] and g("tw_listings")["state"] == "GREEN",
                f"{len(rc)} 列")
            rep = next(r for r in rcl if r["db"].endswith("repo_a7752b3d.duckdb"))
            chk("⑤ 對帳副本 vs 正庫:同名表列數差照列(副本 58 vs 正庫 60)", rep["state"] == "AMBER" and "差 -2" in rep["why"], rep["why"])
            bad = plan_bad(cat)
            chk("⑥ 計畫 5:壞 parquet 逐檔列出(好檔不列),只建議移隔離夾、不動檔",
                len(bad) == 1 and bad[0]["file"] == "FIVEDAY_20260903_224732.parquet", str([b["file"] for b in bad]))
            mg = plan_mega(cat)
            tdp = next(x for x in mg if x["stem"] == "tw_daily_prices")
            chk("⑦ 計畫 4:mega 時間戳檔按表歸組 → 按年 part-YYYY 合併 SQL(DISTINCT + ZSTD + 回讀核對);單檔的不合併",
                tdp["files"] == 3 and tdp["rows_in"] == 14 and tdp["target"].endswith("part-YYYY.parquet") and "DISTINCT" in tdp["sql"][0]
                and next(x for x in mg if x["stem"] == "tw_universe")["files"] == 1, f"{[(x['stem'], x['files']) for x in mg]}")
            rw = {x["family"]: x for x in plan_raw(cat)}
            chk("⑧ 計畫 2:_raw 定位 — chip 與年檔整份重複 = FULL_DUP;px 的 _raw 多出早於年檔的區段(含 1900 哨兵)= RAW_SUPERSET",
                rw["chip"]["verdict"] == "FULL_DUP" and rw["px"]["verdict"] == "RAW_SUPERSET" and "1900" in rw["px"]["advice"],
                f"chip {rw['chip']['verdict']} · px {rw['px']['verdict']}")
            out = root / "out"
            e_csv = export(cat, "vdf_tw_market.duckdb", "tw_daily_prices", "date,ticker,close", "2024-01-10", "2024-01-19", "csv", out=out)
            head = Path(e_csv["output_path"]).read_bytes()[:3] if e_csv["output_path"] else b""
            chk("⑨ 匯出 csv:期間篩選(含迄日)· 只選欄 · 委派 ENG045 utf-8-sig(BOM)· 回讀列數 = 匯出列數",
                e_csv["state"] == "OK" and e_csv["rows"] == 10 and e_csv["readback_rows"] == 10 and head == b"\xef\xbb\xbf", f"{e_csv['state']} {e_csv['rows']}")
            e_b5 = export(cat, "vdf_tw_market.duckdb", "tw_daily_prices", "date,name", "", "", "big5", out=out)
            chk("⑩ 匯出 Big5:放不下的字逐字報數(𠮷)、狀態 LOSSY,不當 OK",
                e_b5["state"] == "LOSSY" and e_b5["lossy_chars"] == 1 and e_b5["readback_rows"] == 60, e_b5["why"][:60])
            e_md = export(cat, "vdf_tw_market.duckdb", "tw_daily_prices", "", "", "", "md", limit=5, out=out)
            e_js = export(cat, "vdf_tw_market.duckdb", "tw_listings", "", "", "", "json", out=out)
            e_pq = export(cat, "vdf_tw_market.duckdb", "tw_daily_prices", "", "2024-02-01", "", "parquet", out=out)
            e_gs = export(cat, "vdf_tw_market.duckdb", "tw_listings", "", "", "", "gsheet", out=out)
            chk("⑪ 匯出 MD(上限照給並說明)· JSON · parquet(COPY zstd)· Google Sheet 相容 csv:四種都回讀核對 OK",
                e_md["state"] == "OK" and e_md["rows"] == 5 and e_js["state"] == "OK" and e_pq["state"] == "OK" and e_pq["rows"] == 29
                and e_gs["state"] == "OK", f"md {e_md['rows']} · json {e_js['rows']} · pq {e_pq['rows']} · gs {e_gs['state']}")
            e_inj = export(cat, "vdf_tw_market.duckdb", "tw_daily_prices", 'date,"x" FROM t; --', "", "", "csv", out=out)
            e_tb = export(cat, "vdf_tw_market.duckdb", "tw_daily_prices; DROP TABLE x", "", "", "", "csv", out=out)
            e_nd = export(cat, "vdf_tw_market.duckdb", "tw_listings", "", "2024-01-01", "", "csv", out=out)
            e_dry = export(cat, "vdf_tw_market.duckdb", "tw_daily_prices", "", "", "", "csv", dry=True, out=out)
            chk("⑫ 反面控制:欄名 / 表名只收目錄與 PRAGMA 認得的(注入字串擋掉)· 無日期欄給期間 = NO_DATE_COL · --dry 只數不寫",
                e_inj["state"] == "BAD_PARAM" and e_tb["state"] == "ABSENT" and e_nd["state"] == "NO_DATE_COL"
                and e_dry["state"] == "PLAN" and not Path(e_dry["output_path"]).exists(), f"{e_inj['state']} · {e_tb['state']} · {e_nd['state']} · {e_dry['state']}")
            chk("⑬ 正庫零改動:資料家每個檔的修改時間在全部操作(目錄 · 核對 · 計畫 · 匯出)前後一致(唯讀連線)",
                snap == {p: p.stat().st_mtime_ns for p in home.rglob("*") if p.is_file()})
            wp = write_plans(cat, "all", out)
            chk("⑭ 計畫檔只寫 VIA_Reports/dbmanager(沙盒 out),含三項與規則聲明", Path(wp["path"]).is_file() and wp["bad"] == 1,
                str({k: v for k, v in wp.items() if k != "path"}))
            # v0101 ①②③
            f1, e1 = parse_flags(["--db", "x.duckdb", "--cols", "date", "ticker", "close", "--start", "2026-01-01", "--dry"])
            f2, e2 = parse_flags(["--cols", "date,ticker,", "close", "--format", "csv"])
            _, e3 = parse_flags(["--table", "a", "b"])
            _, e4 = parse_flags(["--db", "x", "stray"])
            _, e6 = parse_flags(["stray", "--db", "x"])
            _, e5 = parse_flags(["--colz", "a"])
            chk("⑯ v0101 PowerShell 把 --cols a,b,c 拆成三個參數也收齊;逗號與空白混用照收;其他旗標多值 / 多出來的字 / 不認得的旗標一律擋下(不再默默只匯 1 欄)",
                f1.get("--cols") == "date,ticker,close" and f1.get("--dry") is True and not e1 and f2.get("--cols") == "date,ticker,close"
                and "只收一個值" in e3 and "只收一個值" in e4 and "多出來的字" in e6 and "不認得的旗標" in e5, f"{f1.get('--cols')} · {e3[:20]} · {e4[:20]} · {e5[:20]}")
            with duckdb.connect(str(home / "vdf_hub.duckdb")) as con_:
                con_.execute("CREATE TABLE via_policy_sync AS SELECT 1 AS x")
                con_.execute("CREATE TABLE digest_vdf_rows AS SELECT 1 AS x")
            cat2 = dh.catalog(via=root, home=str(home), tables=False, do_print=False, write=False)
            book2 = book + [{"db": "vdf_tw_market.duckdb", "table": "via_policy_sync", "min_rows": 0, "writers": ["VRN_ENG082"]}]
            rc2 = reconcile(overview(cat2, now=datetime.strptime(cat2["ts"], "%Y-%m-%d %H:%M:%S")), book2)
            ps = next(r for r in rc2 if r["db"] == "vdf_hub.duckdb" and r["table"] == "via_policy_sync")
            dg = next(r for r in rc2 if r["db"] == "vdf_hub.duckdb" and r["table"] == "digest_vdf_rows")
            chk("⑰ v0101 政策同步表(冊上寫入者 VRN_ENG082)出現在別的庫 = GREEN L14;真的冊外表照樣 AMBER 請入冊",
                ps["state"] == "GREEN" and "L14" in ps["why"] and dg["state"] == "AMBER", f"{ps['state']} · {dg['state']}")
            sm = plan_summary({"bad": plan_bad(cat), "mega": plan_mega(cat), "raw": plan_raw(cat)})
            chk("⑱ v0101 plan 印精簡摘要:三項各有標題行,mega 只列要合併的,_raw 逐族一行", any(x.startswith("[計畫 5") for x in sm)
                and any(x.startswith("[計畫 4") and "要合併 1 表" in x for x in sm) and sum(1 for x in sm if "FULL_DUP" in x or "RAW_SUPERSET" in x) == 2,
                f"{len(sm)} 行")
        live, lst, lwhy = load_catalog()
        chk("⑮ 活樹唯讀:讀目錄頁不寫任何檔;目錄不在就照實 ABSENT 並講工作站指令", (live is not None) or (lst == "ABSENT" and "via-datahome" in lwhy),
            f"{lst} {lwhy[:50]}")
    finally:
        os.environ.update(saved)
    ok = sum(res)
    print(f"  [計] {len(res)} 檢 OK {ok} · FAIL {len(res) - ok}")
    return 0 if ok == len(res) else 1


# ---------------------------------------------------------------- CLI
def _arg(a: list, flag: str, default=None):
    return a[a.index(flag) + 1] if flag in a and a.index(flag) + 1 < len(a) else default


FLAGS = {"--db": 1, "--table": 1, "--cols": "*", "--start": 1, "--end": 1, "--format": 1, "--limit": 1, "--dry": 0, "--json": 0}


def parse_flags(tokens: list) -> tuple:
    """旗標 → 值。--cols 收到下一個 -- 旗標前的所有字(PowerShell 會把 a,b,c 拆成三個參數;逗號或空白都收)。
    其他旗標只收一個值;多出來的字、不認得的旗標回錯誤(不默默吞掉)。回 (dict, 錯誤或 "")。"""
    out, i, extra = {}, 0, []
    while i < len(tokens):
        t = str(tokens[i])
        if t.startswith("--"):
            if t not in FLAGS:
                return out, f"不認得的旗標:{t}"
            want = FLAGS[t]
            if want == 0:
                out[t] = True
                i += 1
                continue
            vals = []
            i += 1
            while i < len(tokens) and not str(tokens[i]).startswith("--"):
                vals.append(str(tokens[i]))
                i += 1
            if not vals:
                return out, f"{t} 後面缺值"
            if want == 1 and len(vals) > 1:
                return out, f"{t} 只收一個值,多了:{vals[1:]}(有空白請加引號)"
            out[t] = ",".join(v.strip(",") for v in vals if v.strip(",")) if want == "*" else vals[0]
        else:
            extra.append(t)
            i += 1
    if extra:
        return out, f"多出來的字:{extra}"
    return out, ""


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if not a or a[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    if "--selftest" in a or a[0] == "selftest":
        return selftest()
    verb = a[0]
    cat, cst, cwhy = load_catalog()
    if verb == "overview":
        ov = overview(cat, cst, cwhy)
        if "--json" in a:
            print(json.dumps(ov, ensure_ascii=False, indent=1))
            return 0
        if cat is None:
            print(f"[DBM] NODATA · {cwhy}")
            return 2
        k = ov["kpi"]
        print(f"[DBM] 目錄 {ov['catalog_ts']}" + (f"(已 {ov['age_hours']} 小時,過期)" if ov["stale"] else "")
              + f" · 正庫 {k['dbs']} 本 · 對帳副本 {k['replicas']} · {k['tables']} 表 · {k['rows']:,} 列 · 最新 {k['latest']}"
              + f" · 湖 {k['lakes']} 夾 {k['lake_files']} 檔 · 壞檔 {k['bad_files']} · {k['states']}")
        for d in ov["dbs"]:
            print(f"  [{d['role']}] {d['name']:36s} {d['tables']:3d} 表 · {d['rows']:>12,} 列 · 最新 {d['latest'] or '—'} · {d['counts']}")
        return 0
    if verb == "ui":
        p = _tail(HERE, "CGC_MDL227_ConsoleBlueprint_v*.py")
        if p is None:
            print("[DBM ui] 主控台藍圖 CGC_MDL227 尾版不在")
            return 2
        spec = importlib.util.spec_from_file_location("vdbm_blueprint", str(p))
        m = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = m
        spec.loader.exec_module(m)
        r = m.build()
        page = Path(r.get("out", "")) / "ui" / getattr(m, "PAGE_NAME", "VIA-Console-Blueprint.html")
        print(f"[DBM ui] 主控台重建 {r.get('state')} · 對接 {(r.get('dock') or {}).get('state', '—')} · 全頁 {page}")
        return int(r.get("rc", 0))
    if cat is None:
        print(f"[DBM] NODATA · {cwhy}")
        return 2
    if verb == "reconcile":
        rows = reconcile(overview(cat, cst, cwhy))
        for r in rows:
            if r["state"] != "GREEN":
                print(f"  [{r['state']}] {r['db']} · {r['table']} · 冊上次 {r['rows_seen']} · 現在 {r['rows_now']} · {r['why']}")
        cnt = {}
        for r in rows:
            cnt[r["state"]] = cnt.get(r["state"], 0) + 1
        print(f"[DBM 核對] {len(rows)} 列 · {cnt}")
        return 0 if not cnt.get("RED") else 1
    if verb == "plan":
        which = a[1] if len(a) > 1 and not a[1].startswith("--") else "all"
        r = write_plans(cat, which)
        print(f"[DBM 計畫] 只出計畫,不動庫 · {r['path']}")
        for ln in r["summary"]:
            print("  " + ln)
        return 0
    if verb == "export":
        f, err = parse_flags(a[1:])
        if err:
            print(json.dumps({"state": "BAD_PARAM", "why": err}, ensure_ascii=False))
            return 2
        r = export(cat, f.get("--db", ""), f.get("--table", ""), f.get("--cols", ""), f.get("--start", ""),
                   f.get("--end", ""), f.get("--format", "csv"), int(f.get("--limit", 0) or 0) or None, bool(f.get("--dry")))
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0 if r["state"] in ("OK", "PLAN") else 1
    print(f"不認得的動詞:{verb}(overview / reconcile / plan / export / ui / --selftest)")
    return 2


if __name__ == "__main__":
    sys.exit(main())
