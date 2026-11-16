#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_MDL020_DataPlane v0101 — 薄尾:一本冊控管輸入 / 輸出 · 分批增量(中斷 temp 留得住)· 2022-01-01 起輸出 · 輸出檢視頁

操作員 2026-11-15:「四個子系統名稱字不可空格 VeritasDataForge … 整合好 VDF 輸入參數輸出 DATAFRAME 先控管一本 · 輸出資料庫到
via_database\vdf_database(tw__ / gl__ 21 檔 · output_hub · temp)· 以增量擷取 BATCH FETCHING 中斷 TEMP 也會存一部分不全部丟失 ·
然後輸出 2022-01-01~最新的資料 輸出檢視顯示」;原則:「已成功的現況下若修改則用模塊下新增紀錄更正版本號更新」→ 本版只增,v0100 一字不動。

本版多的(其餘照 v0100;__getattr__ 轉接):
  ① 一本冊:VDF_DataPlane_SSOT_v0101.json 的 outputs(21 個輸出 DataFrame:檔名 · 庫 · 表 · 鍵 · 寫入引擎)與 inputs。
     冊上釘了鍵的表照冊(「冊上鍵」優先於宣告主鍵 / 協定 / 內容鍵);沒釘的照 v0100 鍵律推。
  ② parquet sync 分批:有日期欄的表按月一批 —— 每批只取「來源有、parquet 沒有」的鍵,寫成 <家>/temp/vdf_parquet_sync/<檔>.parts/<YYYYMM>.parquet,
     每批寫完立刻追一行檢查點(<檔>.journal.jsonl)。中斷 → 已完成的月份留在 temp;重跑從下一個月接(該月來源列數變了才重做)。
     全部月份做完才合併:既有 parquet ∪ 各批 → 暫存新檔 → 驗列數 / 重複鍵 → 原子替換 → 清掉該檔的批與檢查點。沒日期欄的表照 v0100 一次做。
     --start 2022-01-01(預設取冊上 params.fetch.start):只輸出起始月以後的列;不刪 parquet 裡更早的列。
  ③ parquet backfill [--start] [--end] [--skip-fetch]:清單閘(紅就停)→ VDF 自己的回補引擎 VDF_ENG064_HistoryBackfill 尾版
     `run --start --end`(每批抓完立刻落庫 + checkpoint;出網要操作員的兩道同意閘,本支不代設;閘沒開照實記「擷取被閘擋」,
     仍用庫內現有資料續做)→ 分批 sync → 輸出檢視頁。
  ④ parquet view [--start]:輸出檢視頁 VIA_Reports/vdf/VDF_PARQUET_VIEW_latest.html —— 卡片(每個輸出 DataFrame 一張:列 · 起訖 · 缺月)
     + 矩陣(DataFrame × 月份,每格是該月列數;沒資料的月份看得出來)。冊上有、資料家沒有的檔照列「還沒有」。
零網路(擷取由 ENG064 經網路工具)· 不碰 TA-Lib · 不讀寫同意閘 · 不刪使用者的檔。
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。本支零外呼。"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from datetime import date, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAG = "VDF_MDL020_DataPlane v" + Path(__file__).stem.rsplit("_v", 1)[-1]
PRIOR_NAME = "VDF_MDL020_DataPlane_v0100.py"
BOOK_NAME = "VDF_DataPlane_SSOT_v0101.json"           # 本版讀的冊(只增:inputs · outputs · fetch);更新版冊照 glob 取尾版
SYNC_DIR = Path("temp") / "vdf_parquet_sync"
VIEW_NAME = "VDF_PARQUET_VIEW_latest"


def _load_prior():
    spec = importlib.util.spec_from_file_location("vdf_mdl020_v0100_for_v0101", HERE / PRIOR_NAME)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


P = _load_prior()
P.TAG = TAG                                              # 報告與頁面記本版
_PAGE_V0100 = P.page


def _page_v0101(sc, sync_res=None):
    """管理範圍頁:子系統名稱不空格(操作員 2026-11-15「四個子系統名稱字不可空格 VeritasDataForge」);v0100 本體不改,這裡換掉它的頁首。"""
    return _PAGE_V0100(sc, sync_res).replace("Veritas DataForge", "VeritasDataForge")


P.page = _page_v0101


def __getattr__(name):
    """尾版律 TAILAPI:前版公開名稱經本檔轉接。"""
    return getattr(P, name)


# ---------------------------------------------------------------- ① 一本冊
def book() -> dict:
    b = P._tail(HERE, "VDF_DataPlane_SSOT_v*.json")
    try:
        return json.loads(b.read_text(encoding="utf-8")) if b else {}
    except (OSError, ValueError):
        return {}


def book_keys(bk: dict | None = None) -> dict:
    """冊上釘了鍵的輸出:表名 → 鍵欄。"""
    bk = book() if bk is None else bk
    return {o["table"]: list(o["key"]) for o in bk.get("outputs") or [] if o.get("key")}


_DECLARED_V0100 = P._declared_key


def _declared_key_v0101(con, alias, table):
    """冊上鍵優先;冊上沒釘才看來源表宣告的主鍵(v0100)。冊上鍵欄不在來源 = 不用(照 v0100 推)。"""
    k = book_keys().get(table)
    if k:
        try:
            cols = [r[0] for r in con.execute("DESCRIBE %s.main.%s" % (alias, P._q(table))).fetchall()]
        except Exception:  # noqa: BLE001 — 表不在 / 舊 DuckDB:照前版
            cols = []
        if all(c in cols for c in k):
            return k
    return _DECLARED_V0100(con, alias, table)


P._declared_key = _declared_key_v0101


def start_month(start: str | None) -> str | None:
    if not start:
        return None
    d = P.norm_day(start)
    return d[:4] + d[5:7] if d else None


def _mk(col: str, alias: str = "") -> str:
    """任意日期欄 → 'YYYYMM'(去掉非數字取前 6 碼:2026-11-05 · 20261105 · 2026-11 · 202611 · TIMESTAMP 都通)。"""
    return "substr(regexp_replace(CAST(%s%s AS VARCHAR), '[^0-9]', '', 'g'), 1, 6)" % (alias, P._q(col))


# ---------------------------------------------------------------- ② 分批 sync(月批 · 檢查點)
def _projection(con, src: str, dst: Path | None) -> tuple:
    """來源欄 → 要寫的投影;既有 parquet 欄型不同就 TRY_CAST 成 parquet 的型(轉不過的列數 > 0 = 錯)。"""
    scols = P._cols(con, src)
    if dst is None or not dst.is_file():
        return ["s.%s" % P._q(c) for c, _t in scols], None
    dcols = dict(P._cols(con, "read_parquet(%s)" % P._lit(dst)))
    sel = []
    for c, t in scols:
        if c in dcols and dcols[c] != t:
            bad = con.execute("SELECT COUNT(*) FROM %s WHERE %s IS NOT NULL AND TRY_CAST(%s AS %s) IS NULL" % (src, P._q(c), P._q(c), dcols[c])).fetchone()[0]
            if bad:
                return None, "欄 %s 型別 %s → parquet 的 %s 轉不過 %d 列" % (c, t, dcols[c], bad)
            sel.append("TRY_CAST(s.%s AS %s) AS %s" % (P._q(c), dcols[c], P._q(c)))
        else:
            sel.append("s.%s" % P._q(c))
    return sel, None


def _journal(path: Path) -> dict:
    """檢查點:月 → 那一批的紀錄。中斷在寫一半的最後一行讀不出來 → 記進 _bad_lines(那個月下次重做,安全)。"""
    done, bad = {}, 0
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                j = json.loads(line)
                done[j["month"]] = j
            except (ValueError, KeyError):
                bad += 1
    if bad:
        done["_bad_lines"] = {"month": "_bad_lines", "count": bad}
    return done


def sync_table_batched(con, alias: str, table: str, dst: Path, work: Path, start: str | None = None, stop_after: int | None = None) -> dict:
    src = "%s.main.%s" % (alias, P._q(table))
    names = [c for c, _t in P._cols(con, src)]
    dc = P.date_col(names)
    keys, rule = P.pick_key(names, _declared_key_v0101(con, alias, table))
    res = {"table": table, "file": dst.name, "key": keys, "key_rule": rule, "added": 0, "action": None, "error": None, "batches": 0, "resumed": 0}
    if not dc:
        r = P.sync_table(con, alias, table, dst, work)          # 沒日期欄:一次做(v0100)
        r["batches"] = 1
        return r
    if dst.is_file():
        miss = [k for k in keys if k not in dict(P._cols(con, "read_parquet(%s)" % P._lit(dst)))]
        if miss:
            res.update(action="略過", error="鍵欄 %s 不在既有 parquet(欄位改過?先人工看)" % miss)
            return res
    sel, err = _projection(con, src, dst)
    if err:
        res.update(action="略過", error=err)
        return res
    sm = start_month(start)
    q = "SELECT DISTINCT %s m FROM %s s WHERE %s IS NOT NULL ORDER BY m" % (_mk(dc, "s."), src, _mk(dc, "s."))
    months = [r[0] for r in con.execute(q).fetchall() if r[0] and len(r[0]) == 6 and (sm is None or r[0] >= sm)]
    parts = work / (dst.name + ".parts")
    jpath = work / (dst.name + ".journal.jsonl")
    parts.mkdir(parents=True, exist_ok=True)
    done = _journal(jpath)
    kq = ", ".join(P._q(k) for k in keys)
    vol = [c for c in names if c.lower() in P.VOLATILE]
    order_new = ", ".join([P._q(k) for k in keys] + ["%s DESC NULLS LAST" % P._q(v) for v in vol])
    cond = " AND ".join("CAST(s.%s AS VARCHAR) IS NOT DISTINCT FROM CAST(d.%s AS VARCHAR)" % (P._q(k), P._q(k)) for k in keys)
    rel = "read_parquet(%s)" % P._lit(dst) if dst.is_file() else None
    n_batches = 0
    for m in months:
        src_n = con.execute("SELECT COUNT(*) FROM %s s WHERE %s = ?" % (src, _mk(dc, "s.")), [m]).fetchone()[0]
        j = done.get(m)
        if j and j.get("src_n") == src_n and (j.get("rows", 0) == 0 or (parts / ("%s.parquet" % m)).is_file()):
            res["resumed"] += 1
            continue
        anti = (" AND NOT EXISTS (SELECT 1 FROM %s d WHERE %s = ? AND %s)" % (rel, _mk(dc, "d."), cond)) if rel else ""
        params = [m, m] if rel else [m]
        con.execute("CREATE OR REPLACE TEMP TABLE _b AS SELECT DISTINCT ON (%s) * FROM (SELECT %s FROM %s s WHERE %s = ?%s) ORDER BY %s"
                    % (kq, ", ".join(sel), src, _mk(dc, "s."), anti, order_new), params)
        n = con.execute("SELECT COUNT(*) FROM _b").fetchone()[0]
        pf = parts / ("%s.parquet" % m)
        if n:
            tmp = parts / ("%s.parquet.tmp" % m)
            con.execute("COPY _b TO %s (FORMAT PARQUET, COMPRESSION ZSTD)" % P._lit(tmp))
            os.replace(tmp, pf)
        elif pf.exists():
            pf.unlink()
        with open(jpath, "a", encoding="utf-8") as fh:               # 檢查點:這一批做完了(中斷也留得住)
            fh.write(json.dumps({"month": m, "rows": n, "src_n": src_n, "at": P.utc_now()}, ensure_ascii=False) + "\n")
        res["batches"] += 1
        n_batches += 1
        if stop_after and n_batches >= stop_after:
            raise KeyboardInterrupt("模擬中斷(自測):已做 %d 批" % n_batches)
    part_files = sorted(parts.glob("*.parquet"))
    add = sum(con.execute("SELECT COUNT(*) FROM read_parquet(%s)" % P._lit(f)).fetchone()[0] for f in part_files) if part_files else 0
    if not add:
        jpath.unlink(missing_ok=True)
        for f in parts.glob("*"):
            f.unlink()
        parts.rmdir()
        res.update(action="沒新鍵 · 不動檔", existing=(con.execute("SELECT COUNT(*) FROM %s" % rel).fetchone()[0] if rel else 0))
        return res
    old_n = con.execute("SELECT COUNT(*) FROM %s" % rel).fetchone()[0] if rel else 0
    lst = "[%s]" % ", ".join(P._lit(f) for f in part_files)
    body = ("SELECT * FROM %s UNION ALL BY NAME SELECT * FROM read_parquet(%s, union_by_name = true)" % (rel, lst)) if rel else \
           ("SELECT * FROM read_parquet(%s, union_by_name = true)" % lst)
    tmp = work / (dst.name + ".vdfsync.tmp")
    tmp.unlink(missing_ok=True)
    con.execute("COPY (SELECT * FROM (%s) ORDER BY %s) TO %s (FORMAT PARQUET, COMPRESSION ZSTD)" % (body, P._q(dc), P._lit(tmp)))
    chk = "read_parquet(%s)" % P._lit(tmp)
    got = con.execute("SELECT COUNT(*) FROM %s" % chk).fetchone()[0]
    old_d = con.execute("SELECT COALESCE(SUM(c - 1), 0) FROM (SELECT COUNT(*) c FROM %s GROUP BY %s HAVING COUNT(*) > 1)" % (rel, kq)).fetchone()[0] if rel else 0
    got_d = con.execute("SELECT COALESCE(SUM(c - 1), 0) FROM (SELECT COUNT(*) c FROM %s GROUP BY %s HAVING COUNT(*) > 1)" % (chk, kq)).fetchone()[0]
    if got != old_n + add or got_d != old_d:
        tmp.unlink(missing_ok=True)
        res.update(action="略過", error="合併新檔驗不過:列 %d(該 %d)· 重複鍵 %d(該 %d)→ 原檔不動 · 批留在 temp" % (got, old_n + add, got_d, old_d))
        return res
    e = P._replace(tmp, dst)
    if e:
        tmp.unlink(missing_ok=True)
        res.update(action="略過", error=e + " · 批留在 temp,下次接著合併")
        return res
    jpath.unlink(missing_ok=True)
    for f in parts.glob("*"):
        f.unlink()
    parts.rmdir()
    res.update(action=("新建" if not rel else "補新鍵") + "(分批 %d 月)" % len(months), added=add, rows=got, dups=got_d)
    return res


def sync(home: Path, pq_dir: Path | None = None, only: list | None = None, dedup: bool = False, start: str | None = None,
         stop_after: int | None = None) -> dict:
    """分批版 sync;--dedup 走 v0100 一次做(去重要看整檔)。"""
    if dedup:
        return P.sync(home, pq_dir, only, dedup=True)
    duckdb = P._duck()
    pq_dir = Path(pq_dir or home)
    work = home / SYNC_DIR
    work.mkdir(parents=True, exist_ok=True)
    dbs = P.find_dbs(home)
    con = duckdb.connect()
    con.execute("SET temp_directory = %s" % P._lit(work))
    att = P._attach(con, dbs)
    out = []
    try:
        for name, alias in sorted(att.items()):
            if alias.startswith("ERR"):
                out.append({"table": "*", "file": name, "action": "略過", "error": "正典庫開不了(被引擎鎖住?):" + alias[4:]})
                continue
            for t in P._src_tables(con, alias):
                if only and t not in only:
                    continue
                dst = pq_dir / ("%s__%s.parquet" % (P.PROTO[name], t))
                try:
                    out.append(sync_table_batched(con, alias, t, dst, work, start, stop_after))
                except KeyboardInterrupt:
                    raise
                except Exception as exc:  # noqa: BLE001 — 一張表壞不擋其他表
                    out.append({"table": t, "file": dst.name, "action": "略過", "error": "%s: %s" % (type(exc).__name__, str(exc)[:160])})
    finally:
        con.close()
    files = sorted(p.name for p in pq_dir.glob("*.parquet") if P.PROTO_RX.match(p.name))
    man = P.update_manifest(pq_dir, files, out)
    cat_err = P.write_catalog(pq_dir, work, files) if files else None
    errs = [r for r in out if r.get("error")]
    return {"tag": TAG, "ts": P.utc_now(), "home": str(home), "pq_dir": str(pq_dir), "dbs": {k: str(v) for k, v in dbs.items()}, "start": start,
            "results": out, "written": sum(1 for r in out if str(r.get("action", "")).startswith(("新建", "補新鍵"))),
            "unchanged": sum(1 for r in out if r.get("action") == "沒新鍵 · 不動檔"), "added_rows": sum(r.get("added") or 0 for r in out),
            "resumed": sum(r.get("resumed") or 0 for r in out), "batches": sum(r.get("batches") or 0 for r in out),
            "errors": len(errs), "catalog": (str(pq_dir / P.CATALOG) if not cat_err else "沒寫:" + cat_err), "manifest": man,
            "lamp": "RED" if errs else ("GRAY" if not dbs else "GREEN")}


# ---------------------------------------------------------------- ③ backfill(擷取 → 分批 sync → 檢視)
def fetch(start: str, end: str, limit: int | None = None) -> dict:
    eng = P._tail(HERE / "engine", "VDF_ENG064_HistoryBackfill_v*.py")
    if not eng:
        return {"state": "ABSENT", "note": "找不到 VDF_ENG064_HistoryBackfill"}
    args = [sys.executable, str(eng), "run", "--start", start, "--end", end] + (["--limit", str(limit)] if limit else [])
    env = dict(os.environ, VIA_FROM_VDFSM="YES")              # VDF 自己的總控旗標;同意閘照呼叫端原樣(不代設)
    t0 = time.time()
    try:
        cp = subprocess.run(args, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=None)
    except KeyboardInterrupt:
        return {"state": "INTERRUPTED", "engine": eng.name, "note": "被中斷;ENG064 每批抓完已落庫 + checkpoint,重跑接著補"}
    tail_txt = (cp.stdout + cp.stderr).strip().splitlines()[-6:]
    gated = any(("同意" in x or "CONSENT" in x.upper() or "閘" in x) for x in tail_txt)
    state = "OK" if cp.returncode == 0 else ("GATED" if gated or cp.returncode == 4 else "FAIL")
    return {"state": state, "rc": cp.returncode, "engine": eng.name, "secs": round(time.time() - t0, 1), "tail": tail_txt}


def backfill(home: Path, start: str, end: str, skip_fetch: bool = False, lists_arg: str | None = None, limit: int | None = None) -> dict:
    gate = P.inputs(home, lists_arg)
    if gate["lamp"] == "RED":
        return {"lamp": "RED", "why": "清單輸入閘紅 → 不擷取(先 VDF_SystemManager inputs 看哪一項)", "inputs": gate}
    f = {"state": "SKIPPED", "note": "--skip-fetch"} if skip_fetch else fetch(start, end, limit)
    s = sync(home, start=start)
    v = view(home, start=start)
    lamp = P.worst([gate["lamp"], s["lamp"], "YELLOW" if f["state"] in ("GATED", "FAIL", "ABSENT", "INTERRUPTED") else None])
    return {"lamp": lamp, "inputs": gate["lamp"], "fetch": f, "sync": s, "view": v}


# ---------------------------------------------------------------- ④ 輸出檢視頁
def coverage(home: Path, pq_dir: Path | None = None, start: str | None = None, today: date | None = None) -> dict:
    duckdb = P._duck()
    pq_dir = Path(pq_dir or home)
    today = today or date.today()
    sm = start_month(start) or "202201"
    em = today.strftime("%Y%m")
    months = []
    y, m = int(sm[:4]), int(sm[4:])
    while "%04d%02d" % (y, m) <= em:
        months.append("%04d%02d" % (y, m))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    bk = book()
    planned = [o["file"] for o in bk.get("outputs") or []]
    have = sorted(p.name for p in pq_dir.glob("*.parquet") if P.PROTO_RX.match(p.name))
    con = duckdb.connect()
    rows = []
    for f in sorted(set(planned) | set(have), key=lambda x: (x[:2] != "tw", x)):
        fp = pq_dir / f
        o = next((x for x in bk.get("outputs") or [] if x["file"] == f), {})
        r = {"file": f, "id": o.get("id"), "in_book": bool(o), "exists": fp.is_file(), "rows": None, "rows_from_start": None, "dmin": None, "dmax": None,
             "date_col": None, "by_month": {}, "missing_months": None, "lamp": "GRAY", "sample_cols": [], "sample": []}
        if fp.is_file():
            rel = "read_parquet(%s)" % P._lit(fp)
            cols = [c for c, _t in P._cols(con, rel)]
            dc = P.date_col(cols)
            r["rows"] = con.execute("SELECT COUNT(*) FROM %s" % rel).fetchone()[0]
            r["date_col"] = dc
            if dc:
                bm = dict(con.execute("SELECT %s m, COUNT(*) FROM %s s GROUP BY m" % (_mk(dc, "s."), rel)).fetchall())
                r["by_month"] = {k: v for k, v in bm.items() if k in months}
                r["rows_from_start"] = sum(r["by_month"].values())
                days = sorted(d for d in (P.norm_day(x[0]) for x in con.execute("SELECT DISTINCT CAST(%s AS VARCHAR) FROM %s" % (P._q(dc), rel)).fetchall()) if d)
                r["dmin"], r["dmax"] = (days[0], days[-1]) if days else (None, None)
                have_m = [k for k in months if r["by_month"].get(k)]
                if have_m:
                    first = have_m[0]
                    r["missing_months"] = [k for k in months if k >= first and not r["by_month"].get(k)]
                    cad = P.cadence(r["dmin"], r["dmax"], len(days))
                    r["lamp"] = "GREEN" if not r["missing_months"] or cad not in ("日", "週", "月") else "YELLOW"
                else:
                    r["missing_months"], r["lamp"] = list(months), "YELLOW"
            else:
                r["rows_from_start"], r["lamp"] = r["rows"], "GREEN" if r["rows"] else "YELLOW"
            r["sample_cols"] = cols[:8]
            order = (" ORDER BY %s DESC" % P._q(dc)) if dc else ""
            r["sample"] = [[P._e(v)[:36] for v in x] for x in con.execute("SELECT %s FROM %s%s LIMIT 3" % (", ".join(P._q(c) for c in cols[:8]), rel, order)).fetchall()]
        else:
            r["lamp"] = "YELLOW"
        rows.append(r)
    con.close()
    return {"tag": TAG, "ts": P.utc_now(), "pq_dir": str(pq_dir), "start": sm, "end": em, "months": months, "rows": rows,
            "lamp": P.worst([r["lamp"] for r in rows]) if rows else "GRAY",
            "counts": {"book": len(planned), "exists": sum(1 for r in rows if r["exists"]), "missing": [r["file"] for r in rows if r["in_book"] and not r["exists"]]}}


VIEW_CSS = (".cv-cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px;margin:0 0 14px}"
            ".cv-card{background:#fffefb;border:1px solid #dedfd5;border-radius:8px;padding:10px 12px;min-width:0}"
            ".cv-card .n{font-weight:600;font-size:12.5px;word-break:break-all}.cv-card .s{font-size:11px;color:#55605a;margin-top:4px}"
            "table.cv{border-collapse:collapse!important;font-size:10px!important;width:auto!important}"
            "table.cv th,table.cv td{border:1px solid #fff!important;padding:0!important;text-align:center;vertical-align:middle}"   # 鎖定樣式的格距 8px 10px 對小格太大,只在本矩陣蓋掉
            "table.cv th{font-weight:600;white-space:nowrap;font-size:9.5px!important}"
            "table.cv th.f,table.cv td.f{text-align:left;padding:2px 6px!important;white-space:nowrap;background:#fffefb;position:sticky;left:0;z-index:2}"
            "table.cv td.c,table.cv th.m{width:13px;min-width:13px;max-width:13px;height:16px}table.cv th.y{border-left:2px solid #9ca3af}table.cv td.y{border-left:2px solid #d4d6cc}")


def view_page(cv: dict) -> str:
    css, note = P._spec_css()
    mx = max([v for r in cv["rows"] for v in r["by_month"].values()] + [1])
    p = ['<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="via-page" content="VDF_PARQUET_VIEW">'
         '<meta name="viewport" content="width=device-width,initial-scale=1"><title>VDF 輸出檢視</title><style>%s</style><style>%s%s</style></head><body>' % (css, P.EXTRA_CSS, VIEW_CSS),
         '<header class="dp-head"><div class="dp-r1">VERITAS INTELLIGENCE ANALYTICS</div><div class="dp-r2">VeritasDataForge</div>'
         '<div class="dp-r3">輸出檢視 · %s-%s ~ %s-%s · 卡片看每個輸出 DataFrame 的大概 · 矩陣看每個月有沒有資料</div></header>' % (
             cv["start"][:4], cv["start"][4:], cv["end"][:4], cv["end"][4:])]
    kp = [("總燈", P._chip(cv["lamp"])), ("冊上輸出", str(cv["counts"]["book"])), ("資料家已有", str(cv["counts"]["exists"])),
          ("還沒有", str(len(cv["counts"]["missing"]))), ("起始以後總列數", format(sum(r["rows_from_start"] or 0 for r in cv["rows"]), ",")),
          ("產生", P._e(cv["ts"].replace("T", " ")[:16]) + " UTC")]
    p.append('<div class="dp-kpis">%s</div>' % "".join('<div class="dp-kpi"><div class="k">%s</div><div class="v">%s</div></div>' % (P._e(k), v) for k, v in kp))
    cards = []
    for r in cv["rows"]:
        if r["exists"]:
            s = "%s 列(起始以後 %s)· %s ~ %s" % (format(r["rows"], ","), format(r["rows_from_start"] or 0, ","), r["dmin"] or "—", r["dmax"] or "—")
            if r["missing_months"]:
                s += " · 缺 %d 個月" % len(r["missing_months"])
            if not r["date_col"]:
                s += " · 快照表(沒日期欄)"
        else:
            s = "資料家還沒有這個檔 → parquet sync / backfill 會建" if r["in_book"] else "冊上沒登"
        cards.append('<div class="cv-card"><div>%s <span class="dp-small">%s</span></div><div class="n">%s</div><div class="s">%s</div></div>' % (
            P._chip(r["lamp"]), P._e(r["id"] or "冊外"), P._e(r["file"]), P._e(s)))
    p.append('<section class="dp-sec"><h2>輸出 DataFrame(卡片 · 簡單看)</h2><div class="cv-cards">%s</div></section>' % "".join(cards))
    head = "".join('<th class="m%s" title="%s-%s">%s</th>' % (" y" if m.endswith("01") else "", m[:4], m[4:], ("'" + m[2:4]) if m.endswith("01") else "")
                   for m in cv["months"])
    body = []
    for r in cv["rows"]:
        cells = []
        for m in cv["months"]:
            v = r["by_month"].get(m, 0)
            y = " y" if m.endswith("01") else ""
            if v:
                a = 0.18 + 0.72 * (v / mx) ** 0.5
                cells.append('<td class="c%s" title="%s-%s · %s 列" style="background:rgba(22,163,74,%.2f)"></td>' % (y, m[:4], m[4:], format(v, ","), a))
            elif r["exists"] and r["date_col"] and r["missing_months"] is not None and m in r["missing_months"]:
                cells.append('<td class="c%s" title="%s-%s · 缺" style="background:#fde2e2"></td>' % (y, m[:4], m[4:]))
            else:
                cells.append('<td class="c%s" title="%s-%s" style="background:#f1f1ec"></td>' % (y, m[:4], m[4:]))
        body.append('<tr><td class="f">%s %s</td>%s</tr>' % (P._chip(r["lamp"]), P._e(r["file"]), "".join(cells)))
    p.append('<section class="dp-sec"><h2>矩陣(DataFrame × 月 · 詳細)</h2><p class="dp-small">綠越深 = 該月列數越多 · 淺紅 = 第一筆以後缺的月 · 灰 = 沒資料或快照表;'
             '游標停在格子上看月份與列數</p><div class="dp-scroll"><table class="cv"><thead><tr><th class="f">輸出(年份標在一月)</th>%s</tr></thead><tbody>%s</tbody></table></div></section>' % (head, "".join(body)))
    det = []
    for r in cv["rows"]:
        if r["sample"]:
            det.append('<details class="mx-db"><summary>%s · 最新 3 列</summary><div class="dp-scroll"><table class="dp"><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div></details>' % (
                P._e(r["file"]), "".join("<th>%s</th>" % P._e(c) for c in r["sample_cols"]),
                "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % c for c in x) for x in r["sample"])))
    if det:
        p.append('<section class="dp-sec"><h2>最新幾列</h2>%s</section>' % "".join(det))
    p.append('<p class="dp-small">%s · 資料家 %s · 冊 %s · 樣式 %s</p></body></html>' % (P._e(TAG), P._e(cv["pq_dir"]), P._e(BOOK_NAME), P._e(note)))
    return "".join(p)


def view(home: Path, pq_dir: Path | None = None, start: str | None = None, root: Path | None = None, today: date | None = None) -> dict:
    cv = coverage(home, pq_dir, start, today)
    out = Path(root or P.VIA) / P.OUT_REL
    out.mkdir(parents=True, exist_ok=True)
    (out / (VIEW_NAME + ".json")).write_text(json.dumps(cv, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8")
    (out / (VIEW_NAME + ".html")).write_text(view_page(cv), encoding="utf-8")
    return {"lamp": cv["lamp"], "html": str(out / (VIEW_NAME + ".html")), "counts": cv["counts"], "months": len(cv["months"])}


# ---------------------------------------------------------------- CLI
USAGE = ("動詞(v0101 多的):parquet sync [--start 2022-01-01] · parquet backfill [--start] [--end] [--skip-fetch] · parquet view [--start];"
         "其餘照 v0100:" + P.USAGE)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    sub = args[1] if args[:1] == ["parquet"] and len(args) > 1 else None
    if sub not in ("sync", "backfill", "view"):
        return P.main(args)
    if sub in ("sync", "backfill") and not P.entry_ok():
        print("[%s] 拒絕寫入:由 VDF System Manager 總控(VIA_FROM_VDFSM=YES)或 VCGC" % TAG)
        return 2
    home, hwhy = P.resolve_home(P._opt(args, "--home"))
    if home is None:
        print("[%s] GRAY · %s" % (TAG, hwhy))
        return 2
    fetch_cfg = (book().get("params") or {}).get("fetch") or {}
    start = P._opt(args, "--start") or fetch_cfg.get("start") or "2022-01-01"
    pq_dir = Path(P._opt(args, "--pq-dir")) if P._opt(args, "--pq-dir") else None
    if sub == "view":
        v = view(home, pq_dir, start)
        print("[%s] 輸出檢視 %s · %d 個月 · 冊上 %d · 已有 %d · 還沒有 %s · %s" % (TAG, v["lamp"], v["months"], v["counts"]["book"], v["counts"]["exists"],
                                                                    len(v["counts"]["missing"]), v["html"]))
        return {"GREEN": 0, "YELLOW": 2, "GRAY": 2}.get(v["lamp"], 1)
    if sub == "sync":
        if "--dedup" in args:
            return P.main(args)
        only = [x for x in (P._opt(args, "--only") or "").split(",") if x] or None
        t0 = time.time()
        try:
            r = sync(home, pq_dir, only, False, start)
        except KeyboardInterrupt:
            print("[%s] 中斷 · 已完成的批留在 %s(檢查點 *.journal.jsonl)· 重跑從下一批接" % (TAG, home / SYNC_DIR))
            return 130
        print("[%s] parquet sync(分批 · 起 %s)%s · %.1fs · 寫 %d 檔 · 沒新鍵不動 %d 檔 · 補 %d 列 · 批 %d · 接續 %d · 錯 %d" % (
            TAG, start, r["lamp"], time.time() - t0, r["written"], r["unchanged"], r["added_rows"], r["batches"], r["resumed"], r["errors"]))
        for x in r["results"]:
            if x.get("action") != "沒新鍵 · 不動檔":
                print("  %-18s %-34s +%-8s %s %s" % (x.get("action"), x.get("file"), x.get("added", 0), x.get("key_rule") or "", x.get("error") or ""))
        return {"GREEN": 0, "GRAY": 2}.get(r["lamp"], 1)
    end = P._opt(args, "--end") or date.today().isoformat()
    lim = int(P._opt(args, "--limit")) if P._opt(args, "--limit") else None
    try:
        r = backfill(home, start, end, "--skip-fetch" in args, P._opt(args, "--lists-home"), lim)
    except KeyboardInterrupt:
        print("[%s] 中斷 · 擷取已落庫的批與 sync 已完成的批都留著 · 重跑接著做" % TAG)
        return 130
    if "sync" not in r:
        print("[%s] backfill %s · %s" % (TAG, r["lamp"], r["why"]))
        return 1
    f = r["fetch"]
    print("[%s] backfill %s · %s ~ %s · 清單閘 %s · 擷取 %s%s · sync 寫 %d 檔補 %d 列 · 檢視 %s" % (
        TAG, r["lamp"], start, end, r["inputs"], f["state"], (" rc %s %.0fs" % (f.get("rc"), f.get("secs", 0))) if "rc" in f else "",
        r["sync"]["written"], r["sync"]["added_rows"], r["view"]["html"]))
    for x in f.get("tail") or []:
        print("    ENG064 │ %s" % x[:160])
    return {"GREEN": 0, "YELLOW": 2}.get(r["lamp"], 1)


# ---------------------------------------------------------------- 自測(暫存夾 · 假正典庫 · 零網路)
def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    duckdb = P._duck()
    bk = book()
    chk("① 一本冊(%s):輸入 7 項 · 輸出 21 個 DataFrame(檔名合協定 · 庫對 · 寫入引擎照表冊)· 擷取起日 2022-01-01 · 前版冊不動" % BOOK_NAME,
        len(bk.get("inputs") or []) == 7 and len(bk.get("outputs") or []) == 21 and all(P.PROTO_RX.match(o["file"]) for o in bk["outputs"])
        and all(P.PROTO[o["db"]] == o["file"][:2] for o in bk["outputs"]) and bk["params"]["fetch"]["start"] == "2022-01-01"
        and (HERE / "VDF_DataPlane_SSOT_v0100.json").is_file(), (len(bk.get("inputs") or []), len(bk.get("outputs") or [])))
    with tempfile.TemporaryDirectory() as td:
        h = Path(td) / "vdf_database"
        (h / "output_hub" / "mega").mkdir(parents=True)
        tw = h / "output_hub" / "mega" / "vdf_tw_market.duckdb"
        gl = h / "output_hub" / "mega" / "vdf_global_market.duckdb"
        c = duckdb.connect(str(tw))
        c.execute("CREATE TABLE tw_daily_prices AS SELECT strftime(DATE '2021-11-01' + INTERVAL (i * 7) DAY, '%Y-%m-%d') AS date, ['2330', '6488'][i % 2 + 1] AS ticker, "
                  "100.0 + i AS close FROM range(60) t(i)")
        c.execute("CREATE TABLE tw_monthly_revenue AS SELECT strftime(DATE '2021-06-01' + INTERVAL (i) MONTH, '%Y%m') AS ym, '2330' AS code, 10 + i AS revenue FROM range(20) t(i)")
        c.execute("CREATE TABLE tw_listings(code VARCHAR, name VARCHAR)")
        c.execute("INSERT INTO tw_listings VALUES ('2330', '台積電')")
        c.close()
        c = duckdb.connect(str(gl))
        c.execute("CREATE TABLE us_macro(date DATE, series VARCHAR, value DOUBLE, fetched_at TIMESTAMP)")
        c.execute("INSERT INTO us_macro SELECT DATE '2022-01-03' + INTERVAL (i * 10) DAY, 'DGS10', 4.0 + i / 100, now() FROM range(30) t(i)")
        c.execute("INSERT INTO us_macro SELECT DATE '2022-01-03' + INTERVAL (i * 10) DAY, 'DGS10', 9.9, now() FROM range(3) t(i)")    # 同鍵改值:冊上鍵 date+series → 不重寫
        c.close()
        con = duckdb.connect()
        cnt = lambda f, w="": con.execute("SELECT COUNT(*) FROM read_parquet(%s)%s" % (P._lit(h / f), w)).fetchone()[0]   # noqa: E731
        try:
            sync(h, only=["tw_daily_prices"], start="2022-01-01", stop_after=3)
            interrupted = False
        except KeyboardInterrupt:
            interrupted = True
        work = h / SYNC_DIR
        j = _journal(work / "tw__tw_daily_prices.parquet.journal.jsonl")
        parts_left = sorted(p.name for p in (work / "tw__tw_daily_prices.parquet.parts").glob("*.parquet"))
        chk("② 分批 + 中斷:做完 3 批(月)就斷 → temp 留 3 行檢查點 + 3 個批檔 · parquet 還沒寫(不半套)",
            interrupted and len(j) == 3 and len(parts_left) == 3 and not (h / "tw__tw_daily_prices.parquet").exists(), (interrupted, j, parts_left))
        r = sync(h, start="2022-01-01")
        res = {x["table"]: x for x in r["results"]}
        n_px = cnt("tw__tw_daily_prices.parquet")
        want_px = con.execute("SELECT COUNT(*) FROM (SELECT DISTINCT date, ticker FROM read_parquet(%s))" % P._lit(h / "tw__tw_daily_prices.parquet")).fetchone()[0]
        src_px = duckdb.connect(str(tw), read_only=True)
        want_src = src_px.execute("SELECT COUNT(*) FROM tw_daily_prices WHERE date >= '2022-01-01'").fetchone()[0]
        src_px.close()
        chk("③ 重跑接續:前 3 批不重做(接續 3)· 合併後 = 來源 2022-01-01 起全部(%d 列)· 重複鍵 0 · 2021 的列沒輸出 · temp 批與檢查點清掉" % want_src,
            res["tw_daily_prices"]["resumed"] == 3 and n_px == want_src == want_px and cnt("tw__tw_daily_prices.parquet", " WHERE date < '2022-01-01'") == 0
            and not (work / "tw__tw_daily_prices.parquet.journal.jsonl").exists() and not (work / "tw__tw_daily_prices.parquet.parts").exists(), res["tw_daily_prices"])
        chk("④ 月表(ym = YYYYMM · 來源 2021-06 ~ 2023-01)只輸出 2022-01 起 13 個月 · 快照表照 v0100 一次做 · 冊上鍵 us_macro date+series:同日同序列改值不重寫(30 列)",
            cnt("tw__tw_monthly_revenue.parquet") == 13 and cnt("tw__tw_listings.parquet") == 1 and cnt("gl__us_macro.parquet") == 30
            and res["us_macro"]["key"] == ["date", "series"], (cnt("tw__tw_monthly_revenue.parquet"), res["us_macro"]["key"]))
        m1 = {f.name: f.stat().st_mtime_ns for f in h.glob("*.parquet")}
        r2 = sync(h, start="2022-01-01")
        m2 = {f.name: f.stat().st_mtime_ns for f in h.glob("*.parquet")}
        c = duckdb.connect(str(tw))
        c.execute("INSERT INTO tw_daily_prices VALUES ('2026-11-13', '2330', 999.0), ('2026-11-13', '6488', 998.0), ('2022-03-07', '9999', 1.0)")
        c.close()
        r3 = sync(h, start="2022-01-01")
        res3 = {x["table"]: x for x in r3["results"]}
        chk("⑤ 再跑:沒新鍵 → 4 檔都不動(修改時間不變)· 之後補 2026-11 兩列 + 晚到的 2022-03 一列 → 只補 3 列(晚到的舊日期也收)",
            r2["written"] == 0 and m1 == m2 and res3["tw_daily_prices"]["added"] == 3 and cnt("tw__tw_daily_prices.parquet") == want_src + 3, (r2["written"], res3["tw_daily_prices"]))
        v = view(h, start="2022-01-01", root=Path(td) / "via", today=date(2026, 11, 15))
        cv = json.loads((Path(td) / "via" / P.OUT_REL / (VIEW_NAME + ".json")).read_text(encoding="utf-8"))
        rows = {x["file"]: x for x in cv["rows"]}
        pg = Path(v["html"]).read_text(encoding="utf-8")
        chk("⑥ 輸出檢視:2022-01 ~ 2026-11 共 59 個月 · 冊上 21 個 + 資料家已有 4 個 · 冊上有沒建的照列「還沒有」· 日價有缺月看得出來 · 頁面卡片 + 矩陣 · VeritasDataForge 不空格",
            len(cv["months"]) == 59 and cv["counts"]["book"] == 21 and cv["counts"]["exists"] == 4 and "tw__tw_chip_inst.parquet" in cv["counts"]["missing"]
            and rows["tw__tw_daily_prices.parquet"]["missing_months"] and "矩陣(DataFrame × 月" in pg and "卡片" in pg and "VeritasDataForge" in pg
            and "Veritas DataForge" not in pg and "<script" not in pg.lower(), (len(cv["months"]), cv["counts"]))
        r4 = backfill(h, "2022-01-01", "2026-11-15", skip_fetch=True, lists_arg=str(Path(td) / "nolists"))
        sc = P.scope(str(h), None, date(2026, 11, 15), root=Path(td) / "via", env={})
        pg2 = Path(P.write_reports(sc, None, root=Path(td) / "via")["html"]).read_text(encoding="utf-8")
        chk("⑥b 管理範圍頁(v0100 的頁經本版換頁首):VeritasDataForge 不空格", "VeritasDataForge" in pg2 and "Veritas DataForge" not in pg2)
        chk("⑦ backfill:清單閘紅(找不到清單)→ 不擷取不同步 · 照實說先看 inputs", r4["lamp"] == "RED" and "sync" not in r4 and "inputs" in r4["why"], r4.get("why"))
        lh = Path(td) / "fetch"
        (lh / "0-1-TWStockList").mkdir(parents=True)
        (lh / "0-2-ActiveETFList").mkdir(parents=True)
        con.execute("COPY (SELECT * FROM (VALUES ('2026-11-14', '2330', '2330.TW', 'TWSE', 'ACTIVE')) t(date, ticker, yf_ticker, market, status)) TO %s (FORMAT PARQUET)"
                    % P._lit(lh / "0-1-TWStockList" / "tw_stock_list_latest.parquet"))
        con.execute("COPY (SELECT * FROM (VALUES ('2026-11-14', '00981A', '00981A.TW', 'TWSE', 'ACTIVE', true)) t(date, ticker, yf_ticker, market, status, domestic)) TO %s (FORMAT PARQUET)"
                    % P._lit(lh / "0-2-ActiveETFList" / "active_etf_list_latest.parquet"))
        for sub in ("0-1-TWStockList", "0-2-ActiveETFList"):
            (lh / sub / "verify_report.json").write_text(json.dumps({"engine": "fixture", "date": "2026-11-14", "lamp": "GREEN", "checks": []}), encoding="utf-8")
        (lh / "0-2-ActiveETFList" / "active_etf_qualified_latest.csv").write_text("date,ticker,qualified,reason\n2026-11-14,00981A,True,ok\n", encoding="utf-8")
        r5 = backfill(h, "2022-01-01", "2026-11-15", skip_fetch=True, lists_arg=str(lh))
        chk("⑧ backfill(--skip-fetch):清單閘過 → 分批 sync(沒新鍵不動)→ 檢視頁 · 擷取照實記 SKIPPED", r5.get("sync") and r5["fetch"]["state"] == "SKIPPED"
            and r5["sync"]["written"] == 0 and Path(r5["view"]["html"]).is_file(), {k: r5.get(k) for k in ("lamp", "inputs")})
        con.close()
    cp = subprocess.run([sys.executable, str(HERE / PRIOR_NAME), "--selftest"], env=dict(os.environ, VIA_FROM_VDFSM="YES"),
                        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
    last = [x for x in (cp.stdout or "").splitlines() if x.startswith("[計]")]
    chk("⑩ 前版 v0100 自測照過(%s)" % (last[-1][4:] if last else "沒有計數行"), cp.returncode == 0 and last and "PASS" in last[-1], (cp.stdout or cp.stderr)[-300:])
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑨ 薄尾:前版 v0100 一字不動(載入不改檔)· 前版公開名稱經 __getattr__ 轉接 · 不碰 TA-Lib / 同意閘 · 兩座橋在",
        (HERE / PRIOR_NAME).is_file() and callable(__getattr__("status")) and "[VIA:ACCEL-BRIDGE:v0100]" in text and "[VIA:NET-BRIDGE:v0100]" in text
        and not re.search(r"^\s*(import|from)\s+(talib|CGC_|VRN_|VQG_|VAP_)", text, re.M) and ("environ[" + '"VIA_NET_' + 'CONSENT"]') not in text)
    n = sum(ok)
    print("[計] %s 自測 %d/%d · %s" % (TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    return 0 if n == len(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
