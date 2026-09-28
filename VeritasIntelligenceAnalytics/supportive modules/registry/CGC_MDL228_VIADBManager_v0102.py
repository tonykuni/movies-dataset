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
v0101→v0102(側線 2026-09-28;操作員令「PowerShell 面板 + 詳細摘要 + 錯誤矩陣(含 AST 與說明)+ 存政策 + 台股/主動 ETF 清單」):
  ① 核對修 Codex #333 P1:冊上 db_scope=all_home 的表(L14 政策同步表)每一本正庫逐本檢查,缺 / 讀不動 / 低於冊下限 = RED;
     v0101 只看「已經在的那幾份」而且一律 GREEN,少一本庫看不出來。冊上沒標 db_scope 才退回寫入者 VRN_ENG082 推定。
  ② 新動詞 panel(唯讀):目錄 → 總覽 → 核對 → 三項計畫 → 兩張清單(VDF_ENG087 v0105+ 正主載入器)→ AST 矩陣(CGC_MDL158
     panorama read_file 看 DB/清單/主控台鏈尾版 + 面板 PowerShell;每筆帶類別說明、嚴重度、建議處置)→ 錯誤矩陣(嚴重度 · 來源 ·
     項目 · 狀態 · 說明 · 處置)→ 摘要。印 @@PROGRESS 進度協定與 BEGIN_PASTE/END_PASTE 貼回塊;寫 VIA_Reports/dbmanager/
     DBM_PANEL_latest.json + .md(再生件)。PowerShell 面板 Invoke-VIA-DBPanel-v0100.ps1 讀這份 JSON 分區上色。

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
  python CGC_MDL228_VIADBManager_v0102.py panel [--json] [--quiet]       # v0102 唯讀面板(摘要 · 清單 · 錯誤矩陣 · AST 矩陣)
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
    """正主尾版:datahome(CGC_MDL123)· bus(CGC_MDL148)· hub(VDF_ENG045)· panorama(CGC_MDL158)· lists(VDF_ENG087)。載不到回 None(照實,不自己補一份)。"""
    if key in _MODS:
        return _MODS[key]
    where = {"datahome": (HERE, "CGC_MDL123_DataHome_v*.py"), "bus": (HERE, "CGC_MDL148_EngineBus_v*.py"),
             "hub": (VIA / "functional modules" / "VDF", "VDF_ENG045_OutputHub_v*.py"),
             "panorama": (HERE, "CGC_MDL158_VIAPanoramaAuditRepair_v*.py"),                          # v0102 AST 矩陣
             "lists": (VIA / "functional modules" / "VDF" / "engine", "VDF_ENG087_MarketListGovernance_v*.py")}[key]
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
    # v0102(Codex #333 P1):冊上 db_scope=all_home 的表,每一本正庫都該有一份 → 逐本 × 逐表檢查(缺 / 讀不動 / 低於下限 = RED),
    # 不再只看「已經在的那幾份」、也不再一律 GREEN。冊上沒標 db_scope 時退回寫入者 VRN_ENG082 推定(照實註明)。
    scoped = {b.get("table"): b for b in book if b.get("db_scope") == "all_home"}
    basis = "冊上 db_scope=all_home"
    if not scoped:
        scoped = {b.get("table"): b for b in book if any("VRN_ENG082" in str(w) for w in (b.get("writers") or []))}
        basis = "冊上沒標 db_scope,依寫入者 VRN_ENG082 推定"
    main_dbs = sorted(d["name"] for d in ov.get("dbs") or [] if d["role"] == "正庫")
    for t, b in sorted(scoped.items()):
        exp_min = int(b.get("min_rows") or 0)
        for dbn in main_dbs:
            key = (dbn, t)
            if key in seen:
                continue                                   # 冊上登的那一本已在上面比過
            seen.add(key)
            r = have.get(key)
            if r is None:
                st, why, n = "RED", f"L14 每本庫都該有一份({basis}),這本沒有", None
            else:
                n = r["rows"]
                st, why = (("RED", "讀不動") if n < 0 else ("RED", f"低於冊下限 {exp_min}(L14 同步表)") if n < exp_min
                           else ("GREEN", f"L14 全庫政策同步表({basis})"))
            out.append({"db": dbn, "table": t, "expected_min": exp_min, "rows_seen": None, "rows_now": n, "state": st, "why": why})
    for key, r in have.items():
        if key not in seen:
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


# ---------------------------------------------------------------- v0102 面板:一次看完(總覽 · 核對 · 計畫 · 兩張清單 · 錯誤矩陣 · AST 矩陣)
PANEL_JSON = "DBM_PANEL_latest.json"
PANEL_MD = "DBM_PANEL_latest.md"
SEV_ORDER = {"HIGH": 0, "MED": 1, "LOW": 2, "INFO": 3}
#: panorama 字典沒收的兩類(說明寫在 CGC_MDL158 v0114 檔頭)
AST_EXTRA_DESC = {
    "COMPILE": "ast.parse 過、compile 不過(例:加速橋注在 from __future__ 前,Z226)",
    "TAILAPI": "尾版比前版少了公開名稱又沒轉接(呼叫端一叫就 AttributeError,Z229)",
}
AST_ACTION = {
    "SYNTAX": "必修:照行號修語法(本器不猜改)", "COMPILE": "把 from __future__ 移回檔頭第一個陳述式",
    "TAILAPI": "尾版補模組層 __getattr__ 轉接前版,或把少掉的名稱補回",
    "DUPDEF": "刪掉或改名前一個同名定義(後者默默蓋掉前者)", "UNREACH": "刪掉 return/raise 之後那幾行,或改寫流程",
    "BAREEXC": "改 except Exception:(不吞 KeyboardInterrupt / SystemExit)", "PSDUPFN": "PowerShell 同名 function 只留一個",
    "PSDOCSTR": "把函式開頭的三引號字串改成 # 註解或 <# #> 說明塊", "MUTDEF": "預設值改 None,函式內再建新物件",
    "SWALLOW": "graceful 設計可保留;不是刻意的就記一行或回報狀態",
}
AST_SEVERE_EXTRA = ("COMPILE", "TAILAPI")
AST_MED = ("HARDIMP", "PINVER", "SYSEXE", "TALIB", "MUTDEF")
#: AST 矩陣看哪幾支:DB/清單/主控台這條鏈的尾版 + 面板 PowerShell 本身(都用 glob 取尾版)
AST_CHAIN = (
    ("supportive modules/registry", "CGC_MDL228_VIADBManager_v*.py"),
    ("supportive modules/registry", "CGC_MDL227_ConsoleBlueprint_v*.py"),
    ("supportive modules/registry", "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py"),
    ("supportive modules/registry", "CGC_MDL123_DataHome_v*.py"),
    ("functional modules/VDF/engine", "VDF_ENG087_MarketListGovernance_v*.py"),
    ("functional modules/VDF/engine", "VDF_ENG055_OmniFetch_v*.py"),
    ("functional modules/VDF/engine", "VDF_ENG077_ActiveETFUniverse_v*.py"),
    ("functional modules/VDF/engine", "VDF_ENG078_ActiveETFHoldingsHistory_v*.py"),
    ("functional modules/VDF/engine", "VDF_ENG081_UniverseAlign_v*.py"),
    ("", "Invoke-VIA-DBPanel-v*.ps1"),
)


def panel_policy(folder: Path = HERE) -> dict:
    """政策附冊 VIA_Policy_DBPanel(尾版)。只讀;另核對它釘的正本 sha(正本鎖冊一個位元不動)。"""
    import hashlib
    p = _tail(folder, "VIA_Policy_DBPanel_v*.json")
    if p is None:
        return {"state": "ABSENT", "file": None, "id": None, "why": "政策附冊 VIA_Policy_DBPanel 不在"}
    try:
        pol = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {"state": "RED", "file": p.name, "id": None, "why": f"政策附冊讀不動 {type(exc).__name__}"}
    book = folder / str(pol.get("book") or "")
    sha = hashlib.sha256(book.read_bytes()).hexdigest()[:16] if book.is_file() else None
    ok = bool(pol.get("book_sha256_16")) and sha == pol.get("book_sha256_16") and pol.get("book_edited") is False
    return {"state": "GREEN" if ok and pol.get("status") == "ACTIVE" else "AMBER", "file": p.name, "id": pol.get("id"),
            "status": pol.get("status"), "book": pol.get("book"), "book_sha_ok": ok,
            "why": "附冊在、正本 sha 與附冊所釘一致" if ok else f"正本 sha {sha} ≠ 附冊所釘 {pol.get('book_sha256_16')}(或 book_edited 不是 false)"}


def _p(pct: float, msg: str, on: bool = True) -> None:
    """動態進度條協定(與 CGC_MDL158 同):PowerShell 端把 @@PROGRESS|<pct>|<msg> 轉成 Write-Progress。"""
    if on:
        print(f"@@PROGRESS|{max(0.0, min(100.0, pct)):.1f}|{msg}", flush=True)


def ast_targets() -> list:
    out = []
    for sub, glob in AST_CHAIN:
        p = _tail(VIA / sub if sub else VIA, glob)
        if p is not None:
            out.append(p)
    return out


def _ast_sev(cls: str, pano) -> str:
    severe = set(getattr(pano, "_READ_SEVERE", ())) | set(AST_SEVERE_EXTRA)
    if cls in severe:
        return "HIGH"
    if cls in AST_MED:
        return "MED"
    return "LOW"


def _ast_desc(cls: str, pano) -> tuple:
    cats = getattr(pano, "CATEGORIES", {}) or {}
    reads = getattr(pano, "READ_CHECKS", {}) or {}
    if cls in cats:
        title, _mode, how = cats[cls]
        return title, AST_ACTION.get(cls) or how
    if cls in reads:
        return reads[cls], AST_ACTION.get(cls, "照行號看")
    return AST_EXTRA_DESC.get(cls, "(panorama 未收錄的類)"), AST_ACTION.get(cls, "照行號看")


def ast_matrix(targets: list | None = None) -> dict:
    """AST 矩陣:每支檔跑 panorama read_file(唯讀,只 ast.parse;.ps1 只做文字剖析)→ 每筆問題帶類別說明、嚴重度、建議處置。"""
    pano = _mod("panorama")
    files = [Path(t) for t in (ast_targets() if targets is None else targets)]
    res = {"state": "OK", "files": [], "issues": [], "by_class": {}, "by_sev": {}}
    if pano is None:
        res.update(state="ABSENT", why="CGC_MDL158 panorama 尾版不在或載不動")
        return res
    for f in files:
        try:
            card = pano.read_file(f)
        except Exception as exc:      # 讀不動照實列一行,不中斷整張矩陣
            res["files"].append({"file": f.name, "lang": f.suffix.lstrip("."), "lines": None, "defs": None,
                                 "issues": None, "high": None, "state": "UNREADABLE", "why": f"{type(exc).__name__}: {exc}"[:120]})
            continue
        rows = []
        for i in card.get("issues") or []:
            desc, action = _ast_desc(i["cls"], pano)
            sev = _ast_sev(i["cls"], pano)
            rows.append({"file": f.name, "line": int(i.get("line") or 0), "cls": i["cls"], "sev": sev,
                         "desc": desc, "detail": str(i.get("detail") or "")[:160], "action": action})
            res["by_class"][i["cls"]] = res["by_class"].get(i["cls"], 0) + 1
            res["by_sev"][sev] = res["by_sev"].get(sev, 0) + 1
        res["issues"] += rows
        high = sum(1 for r in rows if r["sev"] == "HIGH")
        res["files"].append({"file": f.name, "lang": card.get("lang"), "lines": card.get("lines"),
                             "defs": len(card.get("defs") or []), "issues": len(rows), "high": high,
                             "state": "RED" if high else ("AMBER" if any(r["sev"] == "MED" for r in rows) else "GREEN")})
    res["issues"].sort(key=lambda r: (SEV_ORDER.get(r["sev"], 9), r["file"], r["line"]))
    res["legend"] = {c: _ast_desc(c, pano)[0] for c in sorted(set(res["by_class"]) | set(AST_EXTRA_DESC)
                                                                | set(getattr(pano, "READ_CHECKS", {})) | set(getattr(pano, "CATEGORIES", {})))}
    return res


def _reconcile_action(r: dict) -> str:
    why = r.get("why") or ""
    if why.startswith("對帳副本"):
        return "副本是對帳用;差多少照記,不動檔(要換新副本是操作員的手)"
    if "L14" in why:
        return "跑政策同步(VRN_ENG082 寫入者)讓這本庫也有一份"
    if "冊外" in why:
        return "入冊:VIA_DB_Table_SSOT 補這張表(db · min_rows · writers)"
    if "比冊上次量少" in why:
        return "查寫入引擎有沒有刪列;說明後更新冊上 rows_seen"
    if "整本庫不在" in why:
        return "確認資料家接點(via-datahome status)或冊上庫名"
    if "沒有這張表" in why or "低於冊下限" in why:
        return "補跑寫入這張表的引擎(冊上 writers),或冊上改期望"
    if "讀不動" in why:
        return "庫可能被鎖或損壞:關掉寫入中的程序後重跑目錄"
    return "照 why 處理"


def error_matrix(ov: dict, rec: list, lists_sum: list, lists_plan: list, ast: dict, pol: dict | None = None) -> list:
    """所有來源的問題收成一張表:嚴重度 · 來源 · 項目 · 狀態 · 說明 · 建議處置。"""
    rows = []

    def add(sev, src, item, state, desc, action):
        rows.append({"sev": sev, "source": src, "item": item, "state": state, "desc": desc, "action": action})

    if ov.get("catalog_state") != "OK":
        add("HIGH", "目錄", "DATAHOME_CATALOG_latest.json", ov.get("catalog_state") or "NODATA",
            ov.get("catalog_why") or "目錄頁不在", "via-datahome catalog -Tables")
    elif ov.get("stale"):
        add("MED", "目錄", ov.get("catalog_ts", ""), "AMBER", f"目錄已 {ov.get('age_hours')} 小時(> {CATALOG_STALE_H})",
            "via-datahome catalog -Tables")
    for d in ov.get("dbs") or []:
        if str(d.get("state") or "OK").upper() not in ("OK", "GREEN"):
            add("HIGH", "資料庫", d["name"], d.get("state"), d.get("why") or "目錄記這本庫不正常", "via-datahome status;庫被鎖就等寫入完再跑")
    sev_of = {"RED": "HIGH", "ABSENT": "HIGH", "AMBER": "MED", "NODATA": "LOW"}
    for r in rec:
        if r["state"] == "GREEN":
            continue
        add(sev_of.get(r["state"], "LOW"), "核對", f"{r['db']} · {r['table']}", r["state"],
            f"{r['why']}(冊下限 {r['expected_min']} · 上次 {r['rows_seen']} · 現在 {r['rows_now']})", _reconcile_action(r))
    bad_by = {}
    for lk in ov.get("lakes") or []:
        if lk.get("bad"):
            bad_by[lk["dataset"]] = bad_by.get(lk["dataset"], 0) + int(lk["bad"])
    for ds, n in sorted(bad_by.items(), key=lambda x: -x[1]):
        add("MED", "湖", ds, "BAD", f"讀不動的 parquet {n} 檔", "計畫 5:via-vcgc dbm plan bad → 操作員移到隔離夾(L10)")
    step = {s["step"]: s["cmd"] for s in lists_plan}
    for it in lists_sum:
        if it["state"] == "GREEN":
            continue
        if it["list"] == "tw_stock":
            act = step.get(1, "")
        elif it["state"] == "AMBER":
            act = step.get(3, "")
        else:
            act = step.get(2, "")
        add({"AMBER": "MED", "NODATA": "MED"}.get(it["state"], "HIGH"), "清單", it["list"], it["state"], it["why"],
            act + "(要網路:操作員親開閘,見 via-gates;面板不代跑)" if act else "看 ENG087 refresh --plan")
    if pol is not None and pol.get("state") != "GREEN":
        add("MED", "政策", str(pol.get("file") or "VIA_Policy_DBPanel_v*.json"), pol.get("state"), pol.get("why", ""),
            "附冊不在就從倉拉回(git pull);正本 sha 不符 = 停,請 via 審核誰動了正本")
    if ast.get("state") != "OK":
        add("MED", "AST", "panorama", ast.get("state"), ast.get("why", ""), "確認 CGC_MDL158 尾版在")
    low = 0
    for i in ast.get("issues") or []:
        if i["sev"] == "LOW":
            low += 1
            continue
        add(i["sev"], "AST", f"{i['cls']} {i['file']}:{i['line']}", i["cls"], f"{i['desc']} · {i['detail']}"[:200], i["action"])
    if low:
        add("LOW", "AST", f"{low} 筆低嚴重度(SWALLOW / 橋缺席等)", "LOW", "graceful 設計常見,不影響結果", "看 JSON ast.issues 或 via-panorama read <檔>")
    rows.sort(key=lambda r: (SEV_ORDER.get(r["sev"], 9), r["source"], r["item"]))
    return rows


def _lists_block(cat: dict | None, db_tw=None, db_etf=None) -> dict:
    eng = _mod("lists")
    if eng is None or not hasattr(eng, "build_lists"):
        return {"state": "ABSENT", "why": "VDF_ENG087 尾版不在或沒有 build_lists(需要 v0105+)", "summary": [], "plan": [], "crosscheck": {}}
    if db_tw is None:
        db_tw = _db_path(cat, "vdf_tw_market.duckdb")[0] if cat else None
    if db_etf is None:
        db_etf = _db_path(cat, "ActiveTWETF.duckdb")[0] if cat else None
    try:
        payload = eng.build_lists(db_tw, db_etf)
    except Exception as exc:
        return {"state": "RED", "why": f"清單讀取失敗 {type(exc).__name__}: {exc}"[:160], "summary": [], "plan": eng.refresh_plan(), "crosscheck": {}}
    return {"state": payload["verdict"], "engine": payload["engine"], "rules": payload["rules"], "summary": eng.summary(payload),
            "crosscheck": payload["crosscheck"], "plan": eng.refresh_plan(),
            "sample": {"stock": [r["code"] for r in payload["stock"]["rows"][:10]],
                       "active_etf": [r["ticker"] for r in payload["active_etf"]["rows"][:20]]}}


def paste_block(pan: dict) -> list:
    """給操作員貼回的精簡塊(BEGIN_PASTE / END_PASTE 之間,約 30 行內)。"""
    ov, k = pan["overview"], pan["overview"].get("kpi") or {}
    rc = pan["reconcile"]["counts"]
    em = pan["errors"]
    sev = {s: sum(1 for r in em if r["sev"] == s) for s in ("HIGH", "MED", "LOW")}
    pol = pan.get("policy") or {}
    lines = [f"[DBM 面板] {pan['verdict']} · {pan['engine']} · {pan['ts']} · 政策 {pol.get('id') or '—'} {pol.get('state', '—')}",
             f"  目錄 {ov.get('catalog_state')} {ov.get('catalog_ts') or '—'}" + (f"(已 {ov.get('age_hours')} 小時,過期)" if ov.get("stale") else ""),
             f"  正庫 {k.get('dbs', 0)} · 副本 {k.get('replicas', 0)} · {k.get('tables', 0)} 表 · {k.get('rows', 0):,} 列 · 最新 {k.get('latest') or '—'}"
             f" · 湖 {k.get('lakes', 0)} 夾 {k.get('lake_files', 0)} 檔 · 壞 {k.get('bad_files', 0)}",
             f"  核對 {sum(rc.values())} 列 · " + (" · ".join(f"{s} {n}" for s, n in sorted(rc.items())) or "—"),
             f"  計畫 壞檔 {pan['plans'].get('bad', 0)} · mega {pan['plans'].get('mega', 0)} · _raw {pan['plans'].get('raw', 0)}(只出計畫)"]
    for it in pan["lists"].get("summary") or []:
        lines.append(f"  清單 {it['list']:13s} {it['state']:6s} {it['why']}")
    if not pan["lists"].get("summary"):
        lines.append(f"  清單 {pan['lists'].get('state')} · {pan['lists'].get('why', '')}")
    a = pan["ast"]
    lines.append(f"  AST {len(a.get('files') or [])} 檔 · {len(a.get('issues') or [])} 筆 · " + " · ".join(f"{c} {n}" for c, n in sorted((a.get("by_class") or {}).items())))
    lines.append(f"  錯誤矩陣 HIGH {sev['HIGH']} · MED {sev['MED']} · LOW {sev['LOW']}")
    for r in em[:12]:
        lines.append(f"   {r['sev']:4s} {r['source']:4s} {str(r['item'])[:48]:48s} {str(r['desc'])[:60]}")
    if len(em) > 12:
        lines.append(f"   … 另 {len(em) - 12} 列(全表在 {PANEL_JSON})")
    return lines


def render_panel_md(pan: dict) -> str:
    ov, k = pan["overview"], pan["overview"].get("kpi") or {}
    esc = lambda s: str(s if s is not None else "—").replace("|", "\\|").replace("\n", " ")
    md = [f"# VIA 資料庫面板 · {pan['verdict']}", "", f"{pan['engine']} · {pan['ts']} · 目錄 {ov.get('catalog_ts') or '—'}", "",
          "## 1 摘要", "", "| 區 | 狀態 | 重點 |", "|---|---|---|"]
    md += [f"| {esc(s['section'])} | {esc(s['state'])} | {esc(s['headline'])} |" for s in pan["summary"]]
    md += ["", "## 2 資料庫", "", "| 角色 | 庫 | 表 | 列 | 最新 | 三態 |", "|---|---|---:|---:|---|---|"]
    md += [f"| {esc(d['role'])} | {esc(d['name'])} | {d['tables']} | {d['rows']:,} | {esc(d['latest'])} | {esc(d['counts'])} |" for d in ov.get("dbs") or []]
    md += ["", "## 3 兩張清單", "", "| 清單 | 狀態 | 檔數 | 說明 |", "|---|---|---:|---|"]
    md += [f"| {esc(i['list'])} | {esc(i['state'])} | {i['n']} | {esc(i['why'])} |" for i in pan["lists"].get("summary") or []]
    for i in pan["lists"].get("summary") or []:
        md += [f"", f"**{i['list']} 檢查**", ""] + [f"- {'OK' if c['ok'] else 'NG'} {c['check']}:{esc(c['detail'])}" for c in i["checks"]]
    md += ["", "**更新順序(只列指令,不代跑)**", ""] + [f"{s['step']}. {s['what']} — `{s['cmd']}`(網路 {'要' if s['net'] else '不要'})"
                                                        for s in pan["lists"].get("plan") or []]
    md += ["", "## 4 錯誤矩陣", "", "| 嚴重度 | 來源 | 項目 | 狀態 | 說明 | 建議處置 |", "|---|---|---|---|---|---|"]
    md += [f"| {r['sev']} | {esc(r['source'])} | {esc(r['item'])} | {esc(r['state'])} | {esc(r['desc'])} | {esc(r['action'])} |" for r in pan["errors"]]
    a = pan["ast"]
    md += ["", "## 5 AST 矩陣", "", "| 檔 | 語言 | 行數 | 定義 | 問題 | HIGH | 狀態 |", "|---|---|---:|---:|---:|---:|---|"]
    md += [f"| {esc(f['file'])} | {esc(f['lang'])} | {esc(f['lines'])} | {esc(f['defs'])} | {esc(f['issues'])} | {esc(f['high'])} | {esc(f['state'])} |"
           for f in a.get("files") or []]
    md += ["", "| 嚴重度 | 檔:行 | 類 | 說明 | 細節 | 處置 |", "|---|---|---|---|---|---|"]
    md += [f"| {i['sev']} | {esc(i['file'])}:{i['line']} | {i['cls']} | {esc(i['desc'])} | {esc(i['detail'])} | {esc(i['action'])} |" for i in a.get("issues") or []]
    md += ["", "**類別說明**", ""] + [f"- `{c}` {esc(d)}" for c, d in (a.get("legend") or {}).items()]
    md += ["", "## 6 計畫摘要", "", "```"] + pan["plan_lines"] + ["```", "", "_唯讀:本頁不寫庫、不動檔;刪與搬是操作員的手(L10)。_", ""]
    return "\n".join(md)


def panel(cat=None, cat_state="OK", cat_why="", out: Path = OUT, progress: bool = True, targets: list | None = None,
          db_tw=None, db_etf=None, now: datetime | None = None) -> dict:
    """一次看完:目錄 → 總覽 → 核對 → 計畫 → 兩張清單 → AST → 錯誤矩陣 → 摘要。只讀;只寫 out 裡兩個再生檔。"""
    _p(5, "讀資料家目錄", progress)
    if cat is None and cat_state == "OK":
        cat, cat_state, cat_why = load_catalog()
    ov = overview(cat, cat_state, cat_why, now=now)
    _p(20, "數量核對", progress)
    rec = reconcile(ov) if cat else []
    rc = {}
    for r in rec:
        rc[r["state"]] = rc.get(r["state"], 0) + 1
    _p(35, "三項計畫(只量)", progress)
    plans = {"bad": plan_bad(cat), "mega": plan_mega(cat), "raw": plan_raw(cat)} if cat else {}
    _p(50, "兩張清單(台股 · 主動式台股 ETF)", progress)
    lst = _lists_block(cat, db_tw, db_etf)
    _p(65, "AST 矩陣(panorama 唯讀)", progress)
    ast = ast_matrix(targets)
    _p(85, "錯誤矩陣", progress)
    pol = panel_policy()
    errs = error_matrix(ov, rec, lst.get("summary") or [], lst.get("plan") or [], ast, pol)
    k = ov.get("kpi") or {}
    summary = [
        {"section": "政策", "state": pol["state"], "headline": f"{pol.get('id') or '—'} · {pol.get('file') or '—'} · {pol['why']}"},
        {"section": "目錄", "state": ov.get("state"), "headline": f"{ov.get('catalog_ts') or '—'} · {ov.get('catalog_state')}"
         + (f" · 已 {ov.get('age_hours')} 小時" if ov.get("age_hours") is not None else "")},
        {"section": "資料庫", "state": "OK" if cat else "NODATA",
         "headline": f"正庫 {k.get('dbs', 0)} · 副本 {k.get('replicas', 0)} · {k.get('tables', 0)} 表 · {k.get('rows', 0):,} 列 · {k.get('states', {})}"},
        {"section": "核對", "state": "RED" if rc.get("RED") or rc.get("ABSENT") else ("AMBER" if rc.get("AMBER") else "GREEN"),
         "headline": " · ".join(f"{s} {n}" for s, n in sorted(rc.items())) or "—"},
        {"section": "湖", "state": "AMBER" if k.get("bad_files") else "GREEN",
         "headline": f"{k.get('lakes', 0)} 夾 · {k.get('lake_files', 0)} 檔 · 壞 {k.get('bad_files', 0)}"},
        {"section": "計畫", "state": "INFO", "headline": " · ".join(f"{n} {len(v)}" for n, v in plans.items()) or "—"},
    ]
    for it in lst.get("summary") or [{"list": "兩張清單", "state": lst.get("state"), "why": lst.get("why", "")}]:
        summary.append({"section": f"清單 {it['list']}", "state": it["state"], "headline": it["why"]})
    summary.append({"section": "AST", "state": "RED" if (ast.get("by_sev") or {}).get("HIGH") else ("AMBER" if (ast.get("by_sev") or {}).get("MED") else "GREEN"),
                    "headline": f"{len(ast.get('files') or [])} 檔 · " + " · ".join(f"{c} {n}" for c, n in sorted((ast.get("by_class") or {}).items()))})
    verdict = ("NODATA" if cat is None else "RED" if any(r["sev"] == "HIGH" for r in errs)
               else "AMBER" if any(r["sev"] == "MED" for r in errs) else "GREEN")
    pan = {"schema": "VIA.DBM.Panel.v1", "engine": ENGINE_TAG, "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
           "verdict": verdict, "summary": summary, "overview": ov,
           "reconcile": {"counts": rc, "rows": [r for r in rec if r["state"] != "GREEN"], "green": rc.get("GREEN", 0)},
           "plans": {n: len(v) for n, v in plans.items()}, "plan_lines": plan_summary(plans) if plans else [],
           "lists": lst, "ast": ast, "errors": errs, "policy": pol,
           "rule": "唯讀面板:不寫庫、不動檔、不抓網;錯誤矩陣只給建議處置,做不做是操作員決定(L10)"}
    pan["paste"] = paste_block(pan)
    _p(95, "寫面板 JSON / Markdown", progress)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for name, text in ((PANEL_JSON, json.dumps(pan, ensure_ascii=False, indent=1)), (PANEL_MD, render_panel_md(pan))):
        tmp = out / (name + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, out / name)
    pan["paths"] = {"json": str(out / PANEL_JSON), "md": str(out / PANEL_MD)}
    _p(100, "完成", progress)
    return pan


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
            # v0102 ①:冊上 db_scope=all_home 的表 → 每本正庫逐本檢查
            book3 = book + [{"db": "vdf_tw_market.duckdb", "table": "via_policy_sync", "min_rows": 1, "db_scope": "all_home"},
                            {"db": "vdf_tw_market.duckdb", "table": "via_handover", "min_rows": 1, "db_scope": "all_home"}]
            rc3 = reconcile(overview(cat2, now=datetime.strptime(cat2["ts"], "%Y-%m-%d %H:%M:%S")), book3)
            g3 = lambda d, t: next((r for r in rc3 if r["db"] == d and r["table"] == t), None)
            hub_ps, hub_ho, tw_ho = g3("vdf_hub.duckdb", "via_policy_sync"), g3("vdf_hub.duckdb", "via_handover"), g3("vdf_tw_market.duckdb", "via_handover")
            chk("⑲ v0102 Codex #333 P1:all_home 表每本正庫逐本查 — 有且達下限 = GREEN · 缺一本 = RED(不再只看已在的那幾份)· 副本不算",
                hub_ps and hub_ps["state"] == "GREEN" and hub_ho and hub_ho["state"] == "RED" and "L14" in hub_ho["why"]
                and tw_ho and tw_ho["state"] == "RED" and not any(r["db"].endswith("repo_a7752b3d.duckdb") and r["table"] == "via_handover" for r in rc3),
                f"{hub_ps and hub_ps['state']} · {hub_ho and hub_ho['state']} · {tw_ho and tw_ho['state']}")
            fx = root / "fixture_bad.py"
            fx.write_text("def a():\n    pass\n\n\ndef a():\n    try:\n        return 1\n        x = 2\n    except:\n        pass\n", encoding="utf-8")
            fp = root / "fixture_dup.ps1"
            fp.write_text("function Get-Foo { 1 }\nfunction Get-Foo { 2 }\n", encoding="utf-8")
            import contextlib
            import io
            buf = io.StringIO()
            pout = root / "panel_out"
            with contextlib.redirect_stdout(buf):
                pan = panel(cat2, out=pout, targets=[fx, fp], db_tw=home / "vdf_tw_market.duckdb", db_etf=root / "none.duckdb",
                            now=datetime.strptime(cat2["ts"], "%Y-%m-%d %H:%M:%S"))
            am = pan["ast"]
            cls_ = {i["cls"] for i in am["issues"]}
            be = next((i for i in am["issues"] if i["cls"] == "BAREEXC"), {})
            chk("⑳ v0102 AST 矩陣:panorama 唯讀判 DUPDEF/UNREACH/BAREEXC/PSDUPFN,每筆帶類別說明 + 嚴重度 HIGH + 建議處置",
                {"DUPDEF", "UNREACH", "BAREEXC", "PSDUPFN"} <= cls_ and be.get("sev") == "HIGH" and "裸 except" in be.get("desc", "")
                and be.get("action", "").startswith("改 except") and am["files"][0]["state"] == "RED", f"{sorted(cls_)}")
            em = pan["errors"]
            rec_hi = [r for r in em if r["source"] == "核對" and r["sev"] == "HIGH"]
            lst_rows = [r for r in em if r["source"] == "清單"]
            chk("㉑ v0102 錯誤矩陣:核對 RED → HIGH 帶處置 · 清單(沙盒股票表缺交易所欄 = RED、ETF 庫不在 = ABSENT)→ HIGH 指到 refresh 指令 · 依嚴重度排序",
                rec_hi and all(r["action"] for r in rec_hi) and len(lst_rows) == 2 and all(r["sev"] == "HIGH" for r in lst_rows)
                and any("macro_lanes" in r["action"] for r in lst_rows) and [SEV_ORDER[r["sev"]] for r in em] == sorted(SEV_ORDER[r["sev"]] for r in em),
                f"{len(em)} 列 · 清單 {[r['state'] for r in lst_rows]}")
            txt = buf.getvalue()
            chk("㉒ v0102 panel 印 @@PROGRESS 進度(0→100)· 貼回塊 ≤ 32 行 · JSON + MD 只寫到指定的 out · 判定 RED(有 HIGH)",
                txt.count("@@PROGRESS|") >= 7 and "@@PROGRESS|100.0|" in txt and len(pan["paste"]) <= 32
                and sorted(p.name for p in pout.iterdir()) == [PANEL_JSON, PANEL_MD] and pan["verdict"] == "RED"
                and "## 4 錯誤矩陣" in (pout / PANEL_MD).read_text(encoding="utf-8"), f"{txt.count('@@PROGRESS|')} 進度 · 貼 {len(pan['paste'])} 行 · {pan['verdict']}")
            pol = panel_policy()
            chk("㉔ v0102 政策附冊 VIA_Policy_DBPanel 在、ACTIVE、正本 sha 與附冊所釘一致(正本不動)· 面板摘要第一列就是政策",
                pol["state"] == "GREEN" and pol["book_sha_ok"] and pan["summary"][0]["section"] == "政策"
                and pan["policy"]["id"] == "DBPANEL-1", f"{pol['state']} · {pol['why']}")
            chk("㉓ v0102 正庫零改動:panel 前後資料家每個檔的修改時間一致",
                all(p.stat().st_mtime_ns == snap[p] for p in snap if p.exists()))
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
    if verb == "panel":                         # v0102:目錄不在也照跑(清單 · AST 照看,判定 NODATA)
        pan = panel(cat, cst, cwhy, progress="--quiet" not in a)
        if "--json" in a:
            print(json.dumps({k: pan[k] for k in ("verdict", "summary", "paths")}, ensure_ascii=False, indent=1))
        else:
            for s_ in pan["summary"]:
                print(f"  [{s_['state']}] {s_['section']}: {s_['headline']}")
            print(f"[DBM 面板] {pan['verdict']} · JSON {pan['paths']['json']} · MD {pan['paths']['md']}")
        print("BEGIN_PASTE")
        for ln in pan["paste"]:
            print(ln)
        print("END_PASTE")
        return {"GREEN": 0, "AMBER": 0, "RED": 1}.get(pan["verdict"], 2)
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
    print(f"不認得的動詞:{verb}(overview / reconcile / plan / export / ui / panel / --selftest)")
    return 2


if __name__ == "__main__":
    sys.exit(main())
