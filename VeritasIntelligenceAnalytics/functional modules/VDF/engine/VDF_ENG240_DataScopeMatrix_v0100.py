#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG240_DataScopeMatrix v0100 — VDF 已抓資料「分類範圍矩陣」(只讀):抓多了沒有、多在哪裡。

操作員令(2026-11-14):「資料好像抓他多了 分類用矩陣檢視一下」+「APPLY OMNIROUTE GRAPHIFY」。
VDF 自有、單檔、只讀(不出網、不寫庫、不刪資料);期望範圍一律以 VDF 自己的冊為準:
  VDF_FetchGroups_SSOT 尾版(大類 → 族群 → 引擎 → 來源表 · 成員規則 · 大類起始日)
  + 成員帳本 / AkShare 選單 / 輸入矩陣(與 FetchGroups 同一套解析)。
每張實體表一列,量:
  列數 · 起訖日 · 範圍起始日(大類起始日與 --start 取早)· 起始日前的列(PRE_START)
  · (鍵, 日期) 重複列(DUP;無鍵 / 無日期 = 整列重複)· 名單外的列(OVER_MEMBERS:成員規則有名單時)
  · 範圍內保留列 → 多餘列 = 列數 − 保留列 · 多餘 %。
另外三面:
  UNMAPPED   庫裡有、冊上沒有任何族群要的表 / VAKE 序列(= 多抓)
  CONTROL    監控快照 / 執行紀錄 / 名單表(fg_status 等)被當資料入湖
  COPIES     同一份資料的實體副本(DuckDB 表 · Parquet · CSV · 日期快照 · 湖分片)與佔用
輸出(VIA_Reports/vdf/datamatrix/):VDF_DataScope_latest.json · .csv · .parquet · .html(VCGC 鎖站色票)
  · VDF_DataLineage_latest.json(Graphify 用:大類 → 族群 → 引擎 → 表 → 湖 VIEW)。
燈:GREEN 範圍內無多餘 · YELLOW 有多餘 / 未分類 / 控制表入湖 · RED 讀不到(壞檔)· NODATA 來源還沒抓 · LOCKED 擷取中被鎖。
rc:0 全綠 · 2 有黃(或全 NODATA)· 1 有紅。
用法:py VDF_ENG240_DataScopeMatrix_v0100.py run [--home <擷取夾>] [--lake <湖夾>] [--start 2022-01-01] [--json] [--no-html]
      py VDF_ENG240_DataScopeMatrix_v0100.py --selftest
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
# 本引擎只讀本機檔,不出網;網路橋照全樹令備著(graceful 未用)

import csv
import datetime as _dt
import html
import json
import os
import re
import sys
import tempfile
from pathlib import Path

STEM = "VDF_ENG240_DataScopeMatrix"
VERSION = "v0100"
TAG = f"{STEM} {VERSION}"
HERE = Path(__file__).resolve().parent
VDF = HERE.parent if HERE.name == "engine" else HERE


def _via_root() -> Path:
    for q in [HERE] + list(HERE.parents):
        if (q / "functional modules").is_dir() and (q / "supportive modules").is_dir():
            return q
    return HERE.parents[2]


VIA = _via_root()
BOOK_GLOB = "VDF_FetchGroups_SSOT_v*.json"
FETCH_GLOB = "VDF_FetchSystem_SSOT_v*.json"
SEL_GLOB = "VDF_AkshareSelection_MacroShipping_v*.json"
MATRIX_GLOB = "VDF_Input_Interface_Matrix_v*.json"
LEDGER = VDF / "VDF_FetchGroups_MemberLedger_v0100.jsonl"
DEFAULT_START = "2022-01-01"
CONTROL_TABLES = {"fg_status", "fg_runs", "fg_groups", "fg_members", "vake_manifest", "tw_stock_list", "tw_active_etf_list",
                  "universe_list", "active_tw_etf_universe"}
CONTROL_DBS = {"VDF_FetchGroups.duckdb", "VDF_catalog.duckdb", "vake.duckdb"}
SKIP_PARTS = ("_quarantine", "_tmp", "selftest", ".probe-")
RC = {"GREEN": 0, "YELLOW": 2, "NODATA": 2, "RED": 1}


# ───────── 冊 · 尾版 ─────────
def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d+)$", p.stem)
    return int(m.group(1)) if m else -1


def tail(glob: str, folder: Path = VDF) -> Path | None:
    hits = sorted((p for p in folder.glob(glob) if _vnum(p) >= 0), key=_vnum)
    return hits[-1] if hits else None


def _json(p: Path) -> dict:
    return json.loads(Path(p).read_text(encoding="utf-8-sig"))


def read_ledger(path: Path = LEDGER) -> list:
    if not Path(path).is_file():
        return []
    out = []
    for ln in Path(path).read_text(encoding="utf-8").splitlines():
        if not ln.strip():
            continue
        try:
            out.append(json.loads(ln))
        except ValueError as exc:
            out.append({"kind": "_bad_line", "error": str(exc)[:80]})   # 壞列照實留著(成員解析不採用)
    return out


def _apply_ops(base: list, ops: list) -> list:
    cur = list(dict.fromkeys(str(b) for b in base))
    for r in ops:
        v = str(r.get("value"))
        if r.get("op") == "add" and v not in cur:
            cur.append(v)
        elif r.get("op") == "remove" and v in cur:
            cur.remove(v)
    return cur


def _selection_base(g: dict, sel: dict) -> list:
    base = list((sel.get("groups") or {}).get(g.get("selection_group"), []))
    if sel.get("fns"):
        base = [f for f in base if f in set(sel["fns"])]
    if g.get("include"):
        base = [f for f in base if re.search(g["include"], f)]
    if g.get("exclude"):
        base = [f for f in base if not re.search(g["exclude"], f)]
    return base


def effective_members(g: dict, ledger: list, sel: dict, matrix: dict) -> dict:
    """與 FetchGroups(v0100 + v0103 EDITABLE_DEFAULT)同一套成員解析;members=None 代表全部不篩。"""
    kind = g.get("membership")
    ops = [r for r in ledger if r.get("kind") == "member" and r.get("group") == g["id"]]
    sec = ((matrix or {}).get("sections") or {}).get(g.get("matrix_section", ""), {})
    if kind == "FIXED_ALL":
        return {"members": None, "origin": g.get("members_from", "全部")}
    if kind == "EDITABLE_MATRIX":
        return {"members": [str(t) for t in sec.get("tickers", [])], "origin": f"輸入矩陣 {g.get('matrix_section')}"}
    if kind == "EDITABLE_SELECTION":
        return {"members": _apply_ops(_selection_base(g, sel or {}), ops), "origin": f"AkShare 選單 {g.get('selection_group')}"}
    if kind == "EDITABLE_DEFAULT":
        base = [str(x) for x in g.get("default_members", [])] + [str(t) for t in sec.get("tickers", []) if str(t) not in g.get("default_members", [])]
        return {"members": _apply_ops(base, ops), "origin": "預設 " + " ".join(g.get("default_members", []))}
    adds = _apply_ops([], ops)
    return {"members": adds or None, "origin": f"帳本 {len(ops)} 筆" if ops else "全部"}


def category_start(book: dict, ledger: list, cat_id: str | None) -> str | None:
    c = next((c for c in book.get("categories", []) if c.get("id") == cat_id), None)
    if not c:
        return None
    val = c.get("default_start")
    for r in ledger:
        if r.get("kind") == "start" and r.get("category") == cat_id:
            val = c.get("default_start") if r.get("value") == "default" else r.get("value")
    return val


def default_home() -> Path:
    env = os.environ.get("VIA_VDF_FETCH_HOME")
    if env:
        return Path(env)
    fb = tail(FETCH_GLOB)
    rel = (_json(fb).get("home_default") if fb else None) or "VIA_Reports/vdf_fetch/dict"
    return VIA / rel


def _skip(p: Path) -> bool:
    s = str(p)
    return any(x in s for x in SKIP_PARTS)


def find_db(name: str, roots: list) -> Path | None:
    hits = [p for r in roots if Path(r).is_dir() for p in Path(r).rglob(name) if p.is_file() and not _skip(p)]
    hits.sort(key=lambda p: ("output_hub" not in p.parts, -p.stat().st_size))
    return hits[0] if hits else None


# ───────── SQL 小工具 ─────────
def _q(ident: str) -> str:
    return '"' + str(ident).replace('"', '""') + '"'


def _lit(v: str) -> str:
    return "'" + str(v).replace("'", "''") + "'"


def date_expr(col: str, dtype: str) -> str:
    c, t = _q(col), (dtype or "").upper()
    if t == "DATE":
        return c
    if t.startswith("TIMESTAMP"):
        return f"CAST({c} AS DATE)"
    if t in ("INTEGER", "BIGINT", "HUGEINT", "INT", "UBIGINT"):
        return (f"COALESCE(TRY_CAST(try_strptime(CAST({c} AS VARCHAR), '%Y%m%d') AS DATE), "
                f"TRY_CAST(try_strptime(CAST({c} AS VARCHAR), '%Y%m') AS DATE))")
    return (f"COALESCE(TRY_CAST({c} AS DATE), TRY_CAST(try_strptime(CAST({c} AS VARCHAR), '%Y%m') AS DATE), "
            f"TRY_CAST(try_strptime(CAST({c} AS VARCHAR), '%Y-%m') AS DATE), TRY_CAST(try_strptime(CAST({c} AS VARCHAR), '%Y/%m/%d') AS DATE))")


def pick(cols: dict, declared: str | None, candidates: list, types: tuple = ()) -> str | None:
    if declared and declared in cols:
        return declared
    low = {c.lower(): c for c in cols}
    for c in candidates:
        if c in cols:
            return c
        if c.lower() in low:
            return low[c.lower()]
    for c, t in cols.items():
        if types and str(t).upper().startswith(types):
            return c
    return None


def _busy(exc: Exception) -> bool:
    t = str(exc).lower()
    return "lock" in t or "conflict" in t


def measure(con, rel: str, cols: dict, dcol: str | None, kcol: str | None, start: str | None, members: list | None) -> dict:
    """一張表(或一個 VIEW)的範圍量測;保留列 = 範圍內不重複的 (鍵, 日期)(無鍵 / 無日期 = 不重複整列)。"""
    rows = con.execute(f"SELECT count(*) FROM {rel}").fetchone()[0]
    out = {"rows": rows, "date_col": dcol, "key_col": kcol, "min_date": None, "max_date": None, "keys": None,
           "pre_start": 0, "dup_rows": 0, "over_members": 0, "members_expected": len(members) if members is not None else None,
           "members_missing": None}
    if not rows:
        out.update(kept=0, excess=0)
        return out
    dx = date_expr(dcol, cols[dcol]) if dcol else None
    kx = f"CAST({_q(kcol)} AS VARCHAR)" if kcol else None
    conds = []
    if dx:
        lo, hi = con.execute(f"SELECT min({dx}), max({dx}) FROM {rel}").fetchone()
        out.update(min_date=str(lo) if lo else None, max_date=str(hi) if hi else None)
        if start:
            out["pre_start"] = con.execute(f"SELECT count(*) FROM {rel} WHERE {dx} < DATE {_lit(start)}").fetchone()[0]
            conds.append(f"({dx} IS NULL OR {dx} >= DATE {_lit(start)})")
    if kx:
        out["keys"] = con.execute(f"SELECT count(DISTINCT {kx}) FROM {rel}").fetchone()[0]
        if members is not None:
            con.execute("CREATE OR REPLACE TEMP TABLE _m(m VARCHAR)")
            if members:
                con.executemany("INSERT INTO _m VALUES (?)", [(str(m),) for m in members])
            inm = f"({kx} IN (SELECT m FROM _m) OR split_part({kx}, '.', 1) IN (SELECT m FROM _m))"
            out["over_members"] = con.execute(f"SELECT count(*) FROM {rel} WHERE NOT {inm}").fetchone()[0]
            out["members_missing"] = con.execute(
                f"SELECT count(*) FROM _m WHERE m NOT IN (SELECT DISTINCT split_part({kx}, '.', 1) FROM {rel}) "
                f"AND m NOT IN (SELECT DISTINCT {kx} FROM {rel})").fetchone()[0]
            conds.append(inm)
    where = (" WHERE " + " AND ".join(conds)) if conds else ""
    if dx and kx:
        out["dup_rows"] = rows - con.execute(f"SELECT count(*) FROM (SELECT DISTINCT {kx}, {dx} FROM {rel})").fetchone()[0]
        kept = con.execute(f"SELECT count(*) FROM (SELECT DISTINCT {kx}, {dx} FROM {rel}{where})").fetchone()[0]
    else:
        out["dup_rows"] = rows - con.execute(f"SELECT count(*) FROM (SELECT DISTINCT * FROM {rel})").fetchone()[0]
        kept = con.execute(f"SELECT count(*) FROM (SELECT DISTINCT * FROM {rel}{where})").fetchone()[0]
    out.update(kept=kept, excess=rows - kept)
    return out


def _lamp(r: dict) -> str:
    if r.get("state") in ("RED", "NODATA", "LOCKED"):
        return r["state"]
    if r.get("kind") in ("UNMAPPED", "CONTROL_IN_LAKE") or (r.get("excess") or 0) > 0:
        return "YELLOW"
    return "GREEN"


def _flags(r: dict) -> list:
    f = []
    if r.get("kind") == "UNMAPPED":
        f.append("UNMAPPED")
    if r.get("kind") == "CONTROL_IN_LAKE":
        f.append("CONTROL_IN_LAKE")
    for k, name in (("pre_start", "PRE_START"), ("dup_rows", "DUP"), ("over_members", "OVER_MEMBERS")):
        if (r.get(k) or 0) > 0:
            f.append(name)
    return f


# ───────── 掃描 ─────────
def scan(home: Path, lake: Path, start: str = DEFAULT_START, book: dict | None = None, ledger: list | None = None,
         sel: dict | None = None, matrix: dict | None = None, roots_extra: list | None = None) -> dict:
    import duckdb
    if book is None:
        bp = tail(BOOK_GLOB)
        book = _json(bp) if bp else {"groups": [], "categories": []}
        book["_path"] = str(bp) if bp else None
    ledger = read_ledger() if ledger is None else ledger
    if sel is None:
        sp = tail(SEL_GLOB)
        sel = _json(sp) if sp else {}
    if matrix is None:
        mp = tail(MATRIX_GLOB)
        matrix = _json(mp) if mp else {}
    det = book.get("detect", {})
    dcands, kcands = det.get("date_cols", []), det.get("key_cols", [])
    roots = [home] + list(roots_extra if roots_extra is not None else [VDF / "output_hub"])
    cats = {c["id"]: c for c in book.get("categories", [])}
    eng_use = {}
    for g in book.get("groups", []):
        for e in str(g.get("engines") or "").split(",") if isinstance(g.get("engines"), str) else (g.get("engines") or []):
            eng_use.setdefault(e.strip(), []).append(g["id"])
    rows, mapped = [], set()
    pmap, ddir = {}, {}     # 冊上 parquet 來源:檔名 → 族群;資料夾 → [(族群, 檔名)](同庫附帶產出判讀)
    con = duckdb.connect()
    attached = {}

    def attach(db: Path) -> str:
        if str(db) not in attached:
            al = f"s{len(attached)}"
            con.execute(f"ATTACH {_lit(db.as_posix())} AS {al} (READ_ONLY)")
            attached[str(db)] = al
        return attached[str(db)]

    def cols_of(sql_from: str, catalog: str | None = None, table: str | None = None) -> dict:
        if catalog:
            return dict(con.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_catalog=? AND table_name=? "
                                    "ORDER BY ordinal_position", [catalog, table]).fetchall())
        return {r[0]: r[1] for r in con.execute(f"DESCRIBE SELECT * FROM {sql_from}").fetchall()}

    def one(base: dict, rel: str, cols: dict, declared_d=None, declared_k=None, rstart=None, members=None) -> dict:
        d = pick(cols, declared_d, dcands, ("DATE", "TIMESTAMP"))
        k = pick(cols, declared_k, kcands)
        r = dict(base, **measure(con, rel, cols, d, k, rstart, members), state="OK")
        return r

    try:
        # ① 冊上每個族群的來源
        for g in book.get("groups", []):
            cat = g.get("category") or next((c["id"] for c in cats.values() if g["id"] in c.get("groups", [])), None)
            cstart = category_start(book, ledger, cat)
            rstart = min(x for x in (cstart, start) if x) if (cstart or start) else None
            eff = effective_members(g, ledger, sel, matrix)
            engines = g.get("engines") or ",".join(e for rf in g.get("refill", []) for e in rf.get("engines", []))
            base0 = {"category": cat, "category_zh": (cats.get(cat) or {}).get("zh", cat), "group": g["id"], "group_zh": g.get("zh", ""),
                     "engines": engines, "membership": g.get("membership"), "member_origin": eff["origin"],
                     "fetch_follows_members": g.get("fetch_follows_members"), "category_start": cstart, "scope_start": rstart, "kind": "MAPPED"}
            for src in g.get("sources", []):
                if src["type"] == "vake":
                    store = home / "vake" / "store"
                    for fn in eff["members"] or []:
                        mapped.add(("vake", fn))
                        base = dict(base0, source="vake", db="vake/store", table=fn, members_expected=None)
                        files = [p for p in store.glob(f"*/{fn}/*/*.parquet") if not _skip(p)]
                        if not files:
                            rows.append(dict(base, state="NODATA", note="序列還沒抓(store 無分片)", rows=0, bytes=0, files=0))
                            continue
                        rel = f"read_parquet({_lit((store / '*' / fn / '*' / '*.parquet').as_posix())}, union_by_name=true)"
                        try:
                            c = cols_of(rel)
                            d = pick(c, "_vake_date" if "_vake_date" in c else None, dcands, ("DATE", "TIMESTAMP"))
                            r = dict(base, **measure(con, rel, c, d, None, rstart, None), state="OK",
                                     bytes=sum(p.stat().st_size for p in files), files=len(files))
                        except Exception as exc:  # noqa: BLE001 — 壞檔照實記
                            r = dict(base, state="RED", note=f"{type(exc).__name__}: {str(exc)[:120]}", rows=0, bytes=0, files=len(files))
                        rows.append(r)
                    continue
                if src["type"] == "duckdb":
                    db = find_db(src["db"], roots)
                    base = dict(base0, source="duckdb", db=src["db"], table=src["table"])
                    mapped.add((src["db"], src["table"]))
                    if not db:
                        rows.append(dict(base, state="NODATA", note=f"找不到 {src['db']}", rows=0))
                        continue
                    try:
                        al = attach(db)
                        c = cols_of("", al, src["table"])
                        if not c:
                            rows.append(dict(base, state="NODATA", note="庫在、表不在", rows=0))
                            continue
                        r = one(base, f"{al}.{_q(src['table'])}", c, src.get("date_col"), src.get("key_col"), rstart, eff["members"])
                        r["db_path"] = str(db)
                        rows.append(r)
                    except Exception as exc:  # noqa: BLE001
                        rows.append(dict(base, state="LOCKED" if _busy(exc) else "RED", note=f"{type(exc).__name__}: {str(exc)[:120]}", rows=0))
                    continue
                files = sorted(p for p in home.glob(src["glob"]) if not _skip(p))
                base = dict(base0, source="parquet", db=str(Path(src["glob"]).parent), table=Path(src["glob"]).stem)
                mapped.add(("parquet", Path(src["glob"]).stem))
                pmap[Path(src["glob"]).stem] = base0
                ddir.setdefault(str(Path(src["glob"]).parent), []).append((g["id"], Path(src["glob"]).stem))
                if not files:
                    rows.append(dict(base, state="NODATA", note="parquet 不在", rows=0))
                    continue
                rel = "read_parquet([" + ", ".join(_lit(f.as_posix()) for f in files) + "], union_by_name=true)"
                try:
                    rows.append(one(base, rel, cols_of(rel), src.get("date_col"), src.get("key_col"), rstart, eff["members"]))
                except Exception as exc:  # noqa: BLE001
                    rows.append(dict(base, state="RED", note=f"{type(exc).__name__}: {str(exc)[:120]}", rows=0))

        # ② 庫裡有、冊上沒有(未分類)· 控制表
        dbs = sorted({p for r in roots if Path(r).is_dir() for p in Path(r).rglob("*.duckdb") if not _skip(p)})
        for db in dbs:
            if lake in db.parents or db.parent == lake:
                continue
            try:
                al = attach(db)
                tables = [t for (t,) in con.execute("SELECT table_name FROM information_schema.tables WHERE table_catalog=? "
                                                    "AND table_type='BASE TABLE'", [al]).fetchall()]
            except Exception as exc:  # noqa: BLE001
                rows.append({"category": None, "category_zh": "未分類", "group": "—", "source": "duckdb", "db": db.name, "table": "*",
                             "kind": "UNMAPPED", "state": "LOCKED" if _busy(exc) else "RED", "note": str(exc)[:120], "rows": 0})
                continue
            for t in tables:
                if (db.name, t) in mapped:
                    continue
                ctl = db.name in CONTROL_DBS or t in CONTROL_TABLES
                base = {"category": "CONTROL" if ctl else "UNMAPPED", "category_zh": "控制 / 名單 / 紀錄" if ctl else "未分類(冊上無族群要)",
                        "group": "—", "engines": "", "source": "duckdb", "db": db.name, "table": t, "kind": "CONTROL" if ctl else "UNMAPPED",
                        "scope_start": None, "db_path": str(db)}
                rel_dir = str(db.parent.relative_to(home)) if home in db.parents else ""
                if not ctl and t in pmap:
                    base.update({k: pmap[t][k] for k in ("category", "category_zh", "group", "group_zh", "engines", "scope_start")},
                                kind="COPY", note=f"同一份資料的 DuckDB 副本(冊上族群 {pmap[t]['group']} 讀 {t}.parquet);不算多抓,列在 ③ 副本")
                elif not ctl and rel_dir in ddir:
                    users = ddir[rel_dir]
                    base.update(note=f"同庫附帶產出:族群 {' · '.join(sorted({u[0] for u in users}))} 只用 "
                                     f"{' · '.join(sorted({u[1] for u in users}))};這張表冊上沒人要 = 引擎多抓")
                try:
                    rows.append(one(base, f"{al}.{_q(t)}", cols_of("", al, t)))
                except Exception as exc:  # noqa: BLE001
                    rows.append(dict(base, state="RED", note=f"{type(exc).__name__}: {str(exc)[:120]}", rows=0))
        store = home / "vake" / "store"
        if store.is_dir():
            fns = sorted({p.parts[-3] for p in store.glob("*/*/*/*.parquet") if not _skip(p)})
            for fn in fns:
                if ("vake", fn) in mapped:
                    continue
                files = list(store.glob(f"*/{fn}/*/*.parquet"))
                rel = f"read_parquet({_lit((store / '*' / fn / '*' / '*.parquet').as_posix())}, union_by_name=true)"
                base = {"category": "UNMAPPED", "category_zh": "未分類(冊上無族群要)", "group": "—", "engines": "011d", "source": "vake",
                        "db": "vake/store", "table": fn, "kind": "UNMAPPED", "scope_start": None,
                        "bytes": sum(p.stat().st_size for p in files), "files": len(files)}
                try:
                    rows.append(one(base, rel, cols_of(rel)))
                except Exception as exc:  # noqa: BLE001
                    rows.append(dict(base, state="RED", note=str(exc)[:120], rows=0))

        # ③ 湖(ENG239):每個 VIEW 也量一次;控制表入湖 = 黃
        lake_rows = []
        cat_db = lake / "VDF_catalog.duckdb"
        if cat_db.is_file():
            try:
                al = attach(cat_db)
                views = [v for (v,) in con.execute("SELECT view_name FROM duckdb_views() WHERE database_name=? AND NOT internal", [al]).fetchall()]
                for v in views:
                    dbn, _, t = v[2:].partition("__")
                    parts = sorted((lake / dbn / t).glob("part-*.parquet"))
                    ctl = t in CONTROL_TABLES or f"{dbn}.duckdb" in CONTROL_DBS
                    base = {"category": "LAKE", "category_zh": "Parquet 湖(ENG239)", "group": "—", "source": "lake", "db": dbn, "table": t,
                            "kind": "CONTROL_IN_LAKE" if ctl else "LAKE", "scope_start": start, "parts": len(parts),
                            "bytes": sum(p.stat().st_size for p in parts), "view": v}
                    rel = "read_parquet([" + ", ".join(_lit(p.as_posix()) for p in parts) + "], union_by_name=true)" if parts else None
                    if not rel:
                        lake_rows.append(dict(base, state="NODATA", rows=0))
                        continue
                    try:
                        c = cols_of(rel)
                        d = pick(c, None, dcands + ["period_end", "snap_ts"], ("DATE", "TIMESTAMP"))
                        k = pick(c, None, kcands)
                        lake_rows.append(dict(base, **measure(con, rel, c, d, k, start if not ctl else None, None), state="OK"))
                        if ctl and t == "fg_status" and "snap_id" in c:
                            snaps = con.execute(f"SELECT count(DISTINCT snap_id) FROM {rel}").fetchone()[0]
                            latest = con.execute(f"SELECT count(*) FROM {rel} WHERE snap_id = (SELECT max(snap_id) FROM {rel})").fetchone()[0]
                            lake_rows[-1].update(snapshots=snaps, excess=lake_rows[-1]["rows"] - latest, kept=latest,
                                                 note=f"監控快照 {snaps} 次 × 每次約 {latest} 列;資料只需最新一次")
                    except Exception as exc:  # noqa: BLE001
                        lake_rows.append(dict(base, state="RED", note=str(exc)[:120], rows=0))
            except Exception as exc:  # noqa: BLE001
                lake_rows.append({"category": "LAKE", "category_zh": "Parquet 湖(ENG239)", "table": "*", "source": "lake",
                                  "state": "LOCKED" if _busy(exc) else "RED", "note": str(exc)[:120], "rows": 0})
        rows += lake_rows
    finally:
        con.close()

    # ④ 副本(同名資料的實體檔)
    copies = {}
    for p in [q for q in home.rglob("*") if q.is_file() and q.suffix.lower() in (".parquet", ".csv") and not _skip(q)
              and "vake" not in q.parts]:
        stem = re.sub(r"(_latest|_\d{4}-\d{2}-\d{2}|_\d{8}(T\d+Z?)?)$", "", p.stem)
        copies.setdefault(stem, []).append({"path": str(p.relative_to(home)), "fmt": p.suffix[1:], "bytes": p.stat().st_size})
    for r in rows:
        if r.get("source") == "duckdb" and r.get("table") in copies:
            copies[r["table"]].append({"path": f"{r['db']}::{r['table']}", "fmt": "duckdb", "bytes": None})
        if r.get("source") == "lake" and r.get("table") in copies:
            copies[r["table"]].append({"path": f"vdf_lake/{r['db']}/{r['table']}", "fmt": "lake", "bytes": r.get("bytes")})
    copy_rows = sorted(({"name": k, "n": len(v), "formats": sorted({x["fmt"] for x in v}), "bytes": sum(x["bytes"] or 0 for x in v),
                         "where": [x["path"] for x in v]} for k, v in copies.items() if len(v) > 1), key=lambda x: -x["n"])

    for r in rows:
        r["lamp"] = _lamp(r)
        r["flags"] = _flags(r)
        n = r.get("rows") or 0
        r["excess_pct"] = round(100.0 * (r.get("excess") or 0) / n, 1) if n else 0.0
    # 大類彙總
    summ = {}
    for r in rows:
        s = summ.setdefault(r.get("category") or "—", {"category": r.get("category") or "—", "zh": r.get("category_zh") or "—", "tables": 0,
                                                      "rows": 0, "excess": 0, "pre_start": 0, "dup_rows": 0, "over_members": 0,
                                                      "nodata": 0, "bytes": 0, "lamps": {}})
        s["tables"] += 1
        for k in ("rows", "excess", "pre_start", "dup_rows", "over_members", "bytes"):
            s[k] += r.get(k) or 0
        s["nodata"] += r["lamp"] == "NODATA"
        s["lamps"][r["lamp"]] = s["lamps"].get(r["lamp"], 0) + 1
    for s in summ.values():
        s["excess_pct"] = round(100.0 * s["excess"] / s["rows"], 1) if s["rows"] else 0.0
        s["lamp"] = "RED" if s["lamps"].get("RED") else "YELLOW" if s["lamps"].get("YELLOW") else "GREEN" if s["lamps"].get("GREEN") else "NODATA"
    lamps = [r["lamp"] for r in rows]
    overall = "RED" if "RED" in lamps else "YELLOW" if "YELLOW" in lamps else "GREEN" if "GREEN" in lamps else "NODATA"
    overlap = {e: gs for e, gs in eng_use.items() if len(gs) > 1}
    data_rows = [r for r in rows if r.get("source") != "lake" and r.get("kind") not in ("CONTROL", "COPY")]   # 資料列(控制表 / 副本另計)
    tot_rows = sum(r.get("rows") or 0 for r in data_rows)
    tot_ex = sum(r.get("excess") or 0 for r in data_rows)
    return {"engine": TAG, "at": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "lamp": overall,
            "home": str(home), "lake": str(lake), "book": book.get("_path"), "start": start,
            "totals": {"tables": len(rows), "rows_fetch": tot_rows, "excess_fetch": tot_ex,
                       "excess_pct_fetch": round(100.0 * tot_ex / tot_rows, 1) if tot_rows else 0.0,
                       "rows_lake": sum(r.get("rows") or 0 for r in rows if r.get("source") == "lake"),
                       "excess_lake": sum(r.get("excess") or 0 for r in rows if r.get("source") == "lake"),
                       "rows_control": sum(r.get("rows") or 0 for r in rows if r.get("kind") == "CONTROL"),
                       "unmapped": sum(r.get("kind") == "UNMAPPED" for r in rows),
                       "control_in_lake": sum(r.get("kind") == "CONTROL_IN_LAKE" for r in rows),
                       "nodata": lamps.count("NODATA"), "copies_multi": len(copy_rows)},
            "categories": sorted(summ.values(), key=lambda s: s["category"]), "rows": rows, "copies": copy_rows,
            "engine_overlap": overlap}


# ───────── 血緣圖(Graphify)─────────
def lineage(res: dict) -> dict:
    nodes, edges = {}, set()

    def node(i, kind, label):
        nodes.setdefault(i, {"id": i, "kind": kind, "label": label})
    for r in res["rows"]:
        cat = r.get("category") or "—"
        node(f"cat:{cat}", "category", r.get("category_zh") or cat)
        t = f"tbl:{r.get('db')}::{r.get('table')}"
        node(t, "table", f"{r.get('table')} ({r.get('rows') or 0:,})")
        nodes[t]["lamp"] = r["lamp"]
        if r.get("group") and r["group"] != "—":
            g = f"grp:{r['group']}"
            node(g, "group", r.get("group_zh") or r["group"])
            edges.add((f"cat:{cat}", g))
            edges.add((g, t))
            for e in [x for x in str(r.get("engines") or "").split(",") if x]:
                node(f"eng:{e}", "engine", e)
                edges.add((g, f"eng:{e}"))
                edges.add((f"eng:{e}", t))
        else:
            edges.add((f"cat:{cat}", t))
        if r.get("source") == "lake":
            src = next((f"tbl:{x.get('db')}::{x.get('table')}" for x in res["rows"]
                        if x.get("source") != "lake" and x.get("table") == r.get("table")), None)
            if src:
                edges.add((src, t))
    return {"system": "VDF", "graph": "data_lineage", "at": res["at"], "engine": TAG, "nodes": list(nodes.values()),
            "edges": [{"from": a, "to": b} for a, b in sorted(edges)]}


# ───────── 輸出 ─────────
def tokens() -> dict:
    t = {"bg": "#f2f1ec", "panel": "#ffffff", "fg": "#33403f", "muted": "#6b6860", "accent": "#1b1a17", "line": "#dbd9d3", "row": "#ebe9e3",
         "green": "#3d7a52", "yellow": "#6f5c31", "red": "#9e2b25", "g_bg": "#e6efec", "y_bg": "#f2ecdd", "r_bg": "#f3e7e6"}
    kit_map = {"--bg": "bg", "--white": "panel", "--ink": "fg", "--muted": "muted", "--title": "accent", "--line": "line", "--row": "row",
               "--green": "green", "--y-ink": "yellow", "--r-ink": "red", "--g-bg": "g_bg", "--y-bg": "y_bg", "--r-bg": "r_bg"}
    p = VIA / "docs" / "handoff" / "ai" / "VIA_WorkbenchLock_kit_latest.json"
    try:
        k = json.loads(p.read_text(encoding="utf-8"))
        for key, val in (k.get("tokens") or {}).items():
            if key in kit_map and isinstance(val, str) and val.startswith("#"):
                t[kit_map[key]] = val
        t["_source"] = f"{p.name}(契約 {k.get('ui_contract_version', '—')})"
    except (OSError, ValueError):
        t["_source"] = "預設(kit 不在)"
    return t


def _n(v) -> str:
    return "—" if v is None else f"{v:,}" if isinstance(v, int) else str(v)


def page(res: dict, path: Path) -> Path:
    t = tokens()
    e = html.escape
    lampc = {"GREEN": ("g_bg", "green"), "YELLOW": ("y_bg", "yellow"), "RED": ("r_bg", "red"), "NODATA": ("row", "muted"), "LOCKED": ("y_bg", "yellow")}

    def chip(l):
        bgk, fgk = lampc.get(l, ("row", "muted"))
        return f'<span class="chip" style="background:{t[bgk]};color:{t[fgk]}">{e(l)}</span>'
    tot = res["totals"]
    cat_rows = "".join(f"<tr><td>{chip(s['lamp'])}</td><td>{e(s['zh'])}<br><small>{e(s['category'])}</small></td><td>{s['tables']}</td>"
                       f"<td>{_n(s['rows'])}</td><td>{_n(s['pre_start'])}</td><td>{_n(s['dup_rows'])}</td><td>{_n(s['over_members'])}</td>"
                       f"<td><b>{_n(s['excess'])}</b></td><td>{s['excess_pct']}%</td><td>{s['nodata']}</td><td>{s['bytes'] / 1e6:,.2f}</td></tr>"
                       for s in res["categories"])
    det = []
    for cat in res["categories"]:
        rs = [r for r in res["rows"] if (r.get("category") or "—") == cat["category"]]
        rs.sort(key=lambda r: (-(r.get("excess") or 0), str(r.get("group")), str(r.get("table"))))
        body = "".join(
            f"<tr><td>{chip(r['lamp'])}</td><td>{e(str(r.get('group') or '—'))}</td><td>{e(str(r.get('engines') or ''))}</td>"
            f"<td>{e(str(r.get('db') or ''))}</td><td>{e(str(r.get('table') or ''))}</td><td>{_n(r.get('rows'))}</td>"
            f"<td>{_n(r.get('keys'))}{'/' + _n(r.get('members_expected')) if r.get('members_expected') is not None else ''}</td>"
            f"<td>{e(str(r.get('min_date') or '—'))} ~ {e(str(r.get('max_date') or '—'))}</td><td>{e(str(r.get('scope_start') or '—'))}</td>"
            f"<td>{_n(r.get('pre_start'))}</td><td>{_n(r.get('dup_rows'))}</td><td>{_n(r.get('over_members'))}</td>"
            f"<td><b>{_n(r.get('excess'))}</b></td><td>{r.get('excess_pct', 0)}%</td><td>{e(' '.join(r.get('flags') or []))}</td>"
            f"<td class='note'>{e(str(r.get('note') or ''))}</td></tr>" for r in rs)
        det.append(f"<details{' open' if cat['excess'] or cat['lamp'] in ('RED', 'YELLOW') else ''}><summary>{chip(cat['lamp'])} {e(cat['zh'])} · "
                   f"{cat['tables']} 表 · 多餘 {_n(cat['excess'])} 列({cat['excess_pct']}%)</summary><div class='scroll'><table><thead><tr>"
                   "<th>燈</th><th>族群</th><th>引擎</th><th>庫</th><th>表</th><th>列數</th><th>鍵 / 名單</th><th>起訖日</th><th>範圍起</th>"
                   "<th>起始日前</th><th>重複</th><th>名單外</th><th>多餘</th><th>多餘%</th><th>旗標</th><th>說明</th></tr></thead>"
                   f"<tbody>{body}</tbody></table></div></details>")
    cp = "".join(f"<tr><td>{e(c['name'])}</td><td>{c['n']}</td><td>{e(' · '.join(c['formats']))}</td><td>{c['bytes'] / 1e6:,.2f}</td>"
                 f"<td class='note'>{e(' | '.join(c['where'][:8]))}</td></tr>" for c in res["copies"])
    ov = "".join(f"<tr><td>{e(k)}</td><td>{e(' · '.join(v))}</td></tr>" for k, v in sorted(res["engine_overlap"].items()))
    css = (f":root{{--bg:{t['bg']};--panel:{t['panel']};--fg:{t['fg']};--muted:{t['muted']};--accent:{t['accent']};--line:{t['line']};--row:{t['row']}}}"
           "body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.5 'Microsoft JhengHei','Segoe UI',sans-serif}"
           "main{max-width:1500px;margin:0 auto;padding-block:20px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}"
           "h1{color:var(--accent);font-size:22px;margin:0 0 4px}h2{color:var(--accent);font-size:16px;margin:22px 0 8px}"
           ".sub{color:var(--muted);font-size:12px}.kpis{display:flex;flex-wrap:wrap;gap:10px;margin:14px 0}"
           ".kpi{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:8px 14px;min-width:120px}.kpi b{display:block;font-size:20px;color:var(--accent)}"
           ".scroll{overflow-x:auto;background:var(--panel);border:1px solid var(--line);border-radius:8px}"
           "table{border-collapse:collapse;width:100%;font-size:12.5px}th,td{padding:5px 8px;border-bottom:1px solid var(--line);text-align:left;white-space:nowrap}"
           "th{background:var(--row);color:var(--accent);position:sticky;top:0}tbody tr:nth-child(even){background:var(--row)}"
           "td.note{white-space:normal;color:var(--muted);min-width:220px}.chip{display:inline-block;border-radius:10px;padding:0 8px;font-size:11px;font-weight:600}"
           "details{margin:8px 0}summary{cursor:pointer;padding:6px 0;color:var(--accent);font-weight:600}")
    doc = (f"<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
           f"<title>VDF 資料範圍矩陣</title><style>{css}</style></head><body><main>"
           f"<h1>VDF 資料範圍分類矩陣 {chip(res['lamp'])}</h1><div class='sub'>{e(TAG)} · {e(res['at'])} · 冊 {e(Path(res['book'] or '—').name)}"
           f" · 擷取夾 {e(res['home'])} · 色票 {e(t['_source'])}</div>"
           "<div class='kpis'>"
           f"<div class='kpi'>資料列數<b>{_n(tot['rows_fetch'])}</b>不含控制表 / 副本</div><div class='kpi'>多餘列<b>{_n(tot['excess_fetch'])}</b>{tot['excess_pct_fetch']}%</div>"
           f"<div class='kpi'>湖列數<b>{_n(tot['rows_lake'])}</b></div><div class='kpi'>湖多餘<b>{_n(tot['excess_lake'])}</b></div>"
           f"<div class='kpi'>未分類表<b>{tot['unmapped']}</b></div><div class='kpi'>控制表入湖<b>{tot['control_in_lake']}</b></div>"
           f"<div class='kpi'>還沒抓<b>{tot['nodata']}</b></div><div class='kpi'>多重副本<b>{tot['copies_multi']}</b></div></div>"
           "<p class='sub'>多餘 = 列數 − 範圍內保留列(保留 = 範圍起始日起、在名單內、(鍵, 日期) 不重複)。範圍起 = 大類起始日與操作員起始日取早。只讀,沒刪任何資料。</p>"
           "<h2>① 大類彙總</h2><div class='scroll'><table><thead><tr><th>燈</th><th>大類</th><th>表</th><th>列數</th><th>起始日前</th><th>重複</th>"
           f"<th>名單外</th><th>多餘</th><th>多餘%</th><th>還沒抓</th><th>MB</th></tr></thead><tbody>{cat_rows}</tbody></table></div>"
           "<h2>② 逐表矩陣(依大類)</h2>" + "".join(det) +
           "<h2>③ 同一份資料的多重副本</h2><div class='scroll'><table><thead><tr><th>名稱</th><th>份數</th><th>格式</th><th>MB</th><th>位置</th></tr></thead>"
           f"<tbody>{cp or '<tr><td colspan=5>無</td></tr>'}</tbody></table></div>"
           "<h2>④ 同一引擎掛在多個族群(擷取時可能重跑)</h2><div class='scroll'><table><thead><tr><th>引擎</th><th>族群</th></tr></thead>"
           f"<tbody>{ov or '<tr><td colspan=2>無</td></tr>'}</tbody></table></div></main></body></html>")
    path.write_text(doc, encoding="utf-8")
    return path


COLS = ["lamp", "category", "category_zh", "group", "group_zh", "engines", "source", "db", "table", "kind", "membership", "rows", "keys",
        "members_expected", "members_missing", "min_date", "max_date", "category_start", "scope_start", "pre_start", "dup_rows",
        "over_members", "kept", "excess", "excess_pct", "flags", "parts", "files", "bytes", "state", "note"]


def write_all(res: dict, out: Path, html_page: bool = True) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    stamp = res["at"].replace("-", "").replace(":", "")
    files = {}
    for name in (f"VDF_DataScope_{stamp}.json", "VDF_DataScope_latest.json"):
        (out / name).write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    files["json"] = out / "VDF_DataScope_latest.json"
    with (out / "VDF_DataScope_latest.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(COLS)
        for r in res["rows"]:
            w.writerow([" ".join(r.get(c) or []) if c == "flags" else r.get(c) for c in COLS])
    files["csv"] = out / "VDF_DataScope_latest.csv"
    try:
        import duckdb
        c = duckdb.connect()
        c.execute(f"COPY (SELECT * FROM read_csv_auto({_lit(files['csv'].as_posix())}, header=true, all_varchar=true)) TO "
                  f"{_lit((out / 'VDF_DataScope_latest.parquet').as_posix())} (FORMAT parquet, COMPRESSION zstd)")
        c.close()
        files["parquet"] = out / "VDF_DataScope_latest.parquet"
    except Exception as exc:  # noqa: BLE001 — 沒 duckdb 就少一份 parquet(json / csv 仍在)
        files["parquet_error"] = f"{type(exc).__name__}: {str(exc)[:120]}"
    (out / "VDF_DataLineage_latest.json").write_text(json.dumps(lineage(res), ensure_ascii=False, indent=1), encoding="utf-8")
    files["lineage"] = out / "VDF_DataLineage_latest.json"
    if html_page:
        files["html"] = page(res, out / "VDF_DataScope_latest.html")
    return files


def out_dir() -> Path:
    return VIA / "VIA_Reports" / "vdf" / "datamatrix"


def cmd_run(args: list) -> int:
    def opt(name, default=None):
        return args[args.index(name) + 1] if name in args and args.index(name) + 1 < len(args) else default
    home = Path(opt("--home") or default_home())
    lake = Path(opt("--lake") or (VIA / "VIA_Reports" / "vdf_lake"))
    start = opt("--start", DEFAULT_START)
    res = scan(home, lake, start)
    files = write_all(res, Path(opt("--out") or out_dir()), "--no-html" not in args)
    if "--json" in args:
        print(json.dumps({k: v for k, v in res.items() if k != "rows"}, ensure_ascii=False, indent=1, default=str)[:20000])
    else:
        tot = res["totals"]
        print(f"[{TAG}] {res['lamp']} · 表 {tot['tables']} · 擷取列 {tot['rows_fetch']:,} · 多餘 {tot['excess_fetch']:,}({tot['excess_pct_fetch']}%)"
              f" · 湖列 {tot['rows_lake']:,} · 湖多餘 {tot['excess_lake']:,} · 未分類 {tot['unmapped']} · 控制表入湖 {tot['control_in_lake']}"
              f" · 還沒抓 {tot['nodata']} · 多重副本 {tot['copies_multi']}")
        print(f"  {'燈':<7}{'大類':<30}{'表':>5}{'列數':>14}{'起始日前':>12}{'重複':>12}{'名單外':>12}{'多餘':>14}{'%':>7}")
        for s in res["categories"]:
            print(f"  {s['lamp']:<7}{s['zh'][:28]:<30}{s['tables']:>5}{s['rows']:>14,}{s['pre_start']:>12,}{s['dup_rows']:>12,}"
                  f"{s['over_members']:>12,}{s['excess']:>14,}{s['excess_pct']:>7}")
        top = sorted((r for r in res["rows"] if (r.get("excess") or 0) > 0 or r.get("kind") == "UNMAPPED"),
                     key=lambda r: -(r.get("excess") or r.get("rows") or 0))[:15]
        if top:
            print("  多餘最多(前 15):")
            for r in top:
                print(f"    {r['lamp']:<7}{str(r.get('group')):<14}{str(r.get('db'))[:26]:<27}{str(r.get('table'))[:34]:<35}"
                      f"列 {r.get('rows') or 0:>11,} 多餘 {r.get('excess') or 0:>11,} {' '.join(r['flags'])}")
        for k, p in files.items():
            print(f"  {k}: {p}")
    return RC.get(res["lamp"], 2)


# ───────── 自測 ─────────
def selftest() -> int:
    import duckdb
    ok = []

    def ck(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:300]) if note and not cond else ''}", flush=True)
    print(f"=== {TAG} 自測(合成夾具 · 只讀量測)===", flush=True)
    book = {"_path": "fixture", "detect": {"date_cols": ["date"], "key_cols": ["ticker", "series"]},
            "categories": [{"id": "TW_MARKET", "zh": "台股", "groups": ["TW_PRICE_VOL"], "default_start": "2022-07-01"},
                           {"id": "FIN", "zh": "財報", "groups": ["TW_FIN"], "default_start": "2021-01-01"},
                           {"id": "MACRO", "zh": "總經", "groups": ["CN_MACRO"], "default_start": "1990-01-01"}],
            "groups": [{"id": "TW_PRICE_VOL", "zh": "量價", "membership": "FIXED_ALL", "category": "TW_MARKET", "engines": "009,e054",
                        "sources": [{"type": "duckdb", "db": "vdf_tw_market.duckdb", "table": "tw_daily_prices", "date_col": "date"}]},
                       {"id": "TW_FIN", "zh": "財報", "membership": "EDITABLE_DEFAULT", "default_members": ["2330"], "category": "FIN",
                        "engines": "e082", "sources": [{"type": "duckdb", "db": "vdf_tw_market.duckdb", "table": "tw_financial"}]},
                       {"id": "INTL_FIN", "zh": "國際財報", "membership": "EDITABLE_DEFAULT", "default_members": ["NVDA"], "category": "FIN",
                        "engines": "006", "sources": [{"type": "parquet", "glob": "fm/income.parquet"}]},
                       {"id": "CN_MACRO", "zh": "中國", "membership": "EDITABLE_SELECTION", "selection_group": "china", "category": "MACRO",
                        "engines": "011d,009", "sources": [{"type": "vake"}]}]}
    sel = {"groups": {"china": ["macro_china_cpi", "macro_china_gdp"]}}
    with tempfile.TemporaryDirectory() as td:
        home, lake = Path(td) / "dict", Path(td) / "lake"
        home.mkdir()
        c = duckdb.connect(str(home / "vdf_tw_market.duckdb"))
        c.execute("CREATE TABLE tw_daily_prices(ticker VARCHAR, date DATE, close DOUBLE)")
        c.execute("INSERT INTO tw_daily_prices VALUES ('2330','2021-12-30',1),('2330','2022-01-03',1),('2330','2022-01-03',1),"
                  "('2317','2022-01-03',2),('2317','2022-01-04',2)")
        c.execute("CREATE TABLE tw_financial(ticker VARCHAR, date DATE, eps DOUBLE)")
        c.execute("INSERT INTO tw_financial VALUES ('2330','2023-03-31',1),('2317','2023-03-31',1),('9999','2023-03-31',1)")
        c.execute("CREATE TABLE tw_extra_junk(ticker VARCHAR, date DATE)")
        c.execute("INSERT INTO tw_extra_junk VALUES ('1','2023-01-01')")
        c.close()
        for fn, n in (("macro_china_cpi", 3), ("macro_china_bond", 2)):
            d = home / "vake" / "store" / "akshare" / fn / "2026"
            d.mkdir(parents=True)
            c = duckdb.connect()
            c.execute(f"COPY (SELECT DATE '1989-12-01' + INTERVAL (i) MONTH AS date, i AS v FROM range({n}) t(i)) TO {_lit((d / 'p1.parquet').as_posix())} (FORMAT parquet)")
            c.close()
        (home / "fm").mkdir()
        c = duckdb.connect(str(home / "fm" / "fm.duckdb"))
        c.execute("CREATE TABLE income(ticker VARCHAR, date DATE, rev DOUBLE)")
        c.execute("INSERT INTO income VALUES ('NVDA','2025-01-31',1)")
        c.execute(f"COPY income TO {_lit((home / 'fm' / 'income.parquet').as_posix())} (FORMAT parquet)")
        c.execute("CREATE TABLE ratios(ticker VARCHAR, date DATE, roe DOUBLE)")
        c.execute("INSERT INTO ratios VALUES ('NVDA','2025-01-31',1)")
        c.close()
        (home / "0-1").mkdir()
        for nm in ("tw_daily_prices_latest.csv", "tw_daily_prices_2026-11-09.parquet"):
            (home / "0-1" / nm).write_text("x\n1\n")
        (lake / "VDF_FetchGroups" / "fg_status").mkdir(parents=True)
        c = duckdb.connect()
        c.execute(f"COPY (SELECT 'S' || (i % 3) AS snap_id, DATE '2026-11-10' AS as_of, i AS v FROM range(6) t(i)) TO "
                  f"{_lit((lake / 'VDF_FetchGroups' / 'fg_status' / 'part-1.parquet').as_posix())} (FORMAT parquet)")
        c.close()
        c = duckdb.connect(str(lake / "VDF_catalog.duckdb"))
        c.execute(f"CREATE VIEW v_VDF_FetchGroups__fg_status AS SELECT * FROM read_parquet({_lit((lake / 'VDF_FetchGroups' / 'fg_status' / '*.parquet').as_posix())})")
        c.close()
        res = scan(home, lake, "2022-01-01", book=book, ledger=[], sel=sel, matrix={}, roots_extra=[])
        by = {(r.get("group"), r.get("table")): r for r in res["rows"]}
        px = by.get(("TW_PRICE_VOL", "tw_daily_prices"), {})
        ck("① 量價:起始日前 1 · (鍵,日期) 重複 1 · 多餘 2 / 5(範圍起 = min(2022-07-01, 2022-01-01))",
           px.get("pre_start") == 1 and px.get("dup_rows") == 1 and px.get("excess") == 2 and px.get("scope_start") == "2022-01-01", px)
        fin = by.get(("TW_FIN", "tw_financial"), {})
        ck("② 財報名單 2330:名單外 2 列 → OVER_MEMBERS · 多餘 2", fin.get("over_members") == 2 and fin.get("excess") == 2
           and "OVER_MEMBERS" in fin.get("flags", []), fin)
        cpi = by.get(("CN_MACRO", "macro_china_cpi"), {})
        ck("③ VAKE 選單內序列量得到(1990 前 1 列 = 多餘)", cpi.get("rows") == 3 and cpi.get("pre_start") == 1, cpi)
        gdp = by.get(("CN_MACRO", "macro_china_gdp"), {})
        ck("④ 選單有、store 沒有 → NODATA(不是多抓)", gdp.get("lamp") == "NODATA", gdp)
        un = {r["table"] for r in res["rows"] if r.get("kind") == "UNMAPPED"}
        ck("⑤ 冊上沒有的表 / 序列 → UNMAPPED(tw_extra_junk · macro_china_bond)", {"tw_extra_junk", "macro_china_bond"} <= un, un)
        lk = next((r for r in res["rows"] if r.get("source") == "lake" and r.get("table") == "fg_status"), {})
        ck("⑥ 湖內 fg_status = 控制表入湖 · 快照 3 次 · 多餘 4/6", lk.get("kind") == "CONTROL_IN_LAKE" and lk.get("snapshots") == 3
           and lk.get("excess") == 4, lk)
        cp = {x["name"]: x for x in res["copies"]}
        ck("⑦ 副本:tw_daily_prices = csv + parquet + duckdb 3 份", cp.get("tw_daily_prices", {}).get("n") == 3, cp)
        inc = next((r for r in res["rows"] if r.get("db") == "fm.duckdb" and r.get("table") == "income"), {})
        rat = next((r for r in res["rows"] if r.get("db") == "fm.duckdb" and r.get("table") == "ratios"), {})
        ck("⑦b 冊上 parquet 的 DuckDB 同名表 = COPY(綠)· 同庫其他表 = UNMAPPED 附帶產出(點名族群)",
           inc.get("kind") == "COPY" and inc.get("lamp") == "GREEN" and rat.get("kind") == "UNMAPPED" and "INTL_FIN" in str(rat.get("note")), (inc, rat))
        ck("⑧ 引擎重疊:009 掛在 2 個族群", res["engine_overlap"].get("009") == ["TW_PRICE_VOL", "CN_MACRO"], res["engine_overlap"])
        ck("⑨ 總燈 YELLOW(有多餘)· rc 2", res["lamp"] == "YELLOW" and RC[res["lamp"]] == 2)
        files = write_all(res, Path(td) / "out")
        htm = files["html"].read_text(encoding="utf-8")
        ck("⑩ 輸出 json · csv · parquet · lineage · html 都在", all(Path(p).is_file() for k, p in files.items() if not k.endswith("_error")) and {"json", "csv", "lineage", "html"} <= set(files))
        lg = json.loads(files["lineage"].read_text(encoding="utf-8"))
        ck("⑪ 血緣圖:大類 → 族群 → 引擎 → 表 都有邊", {"from": "grp:TW_PRICE_VOL", "to": "eng:009"} in lg["edges"]
           and {"from": "eng:009", "to": "tbl:vdf_tw_market.duckdb::tw_daily_prices"} in lg["edges"], lg["edges"][:6])
        ck("⑫ HTML 用鎖站色票 · 大類彙總 + 逐表 + 副本 + 引擎重疊四段", "--bg:" in htm and all(s in htm for s in ("① 大類彙總", "② 逐表矩陣", "③ 同一份資料", "④ 同一引擎")))
        before = sorted(str(p) for p in home.rglob("*"))
        scan(home, lake, "2022-01-01", book=book, ledger=[], sel=sel, matrix={}, roots_extra=[])
        ck("⑬ 只讀:再掃一次擷取夾檔案不變", before == sorted(str(p) for p in home.rglob("*")))
    src = Path(__file__).read_text(encoding="utf-8")
    ck("⑭ 無 TA-Lib · 不出網 · 不刪檔", ("ta" + "lib") not in src.lower() and ("requests" + ".get") not in src and (".unl" + "ink(") not in src)
    n = sum(ok)
    print(f"[計] {TAG} 自測 {n}/{len(ok)} {'PASS' if n == len(ok) else 'FAIL'}", flush=True)
    return 0 if n == len(ok) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    if args[0] in ("--selftest", "selftest"):
        return selftest()
    if args[0] == "run":
        return cmd_run(args[1:])
    print(f"[{TAG}] 未知動詞 {args[0]}(run · --selftest)")
    return 2


if __name__ == "__main__":
    sys.exit(main())
