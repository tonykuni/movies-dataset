#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL012_FetchGroups v0100 — 擷取大族群:名單增減 · 全族群同一 as-of 日 · DuckDB 管理監控 · 庫最佳化

操作員 2026-10-04:「將輸入輸出分為大族群;國際股市每日行情及財報、國內選定股票的財報可以增減,其他大部分也可以增減;
  日期固定在同一天,但族群可以更改;結果可以用 DuckDB 管理監控;資料庫要最佳化」
  「台股每日資訊、台股股價指數、台股主動式 ETF 是抓全部,也要固定顯示全部」。
正本:同夾 VDF_FetchGroups_SSOT_v*.json(取尾版)。本檔只讀冊、不改冊。
  groups                        列族群:名單種類 · 引擎 · 有效成員數 · 目前 as-of
  members <族群>                列有效成員(FIXED_ALL = 全部,給總數)
  add|remove <族群> <值…> [--apply]   增減成員(預設只列計畫;FIXED_ALL 拒絕 rc 2)
      · EDITABLE_MATRIX → 既有 VDF_Input_Interface_Matrix(同一份名單,軟移除可找回)
      · EDITABLE_SELECTION / EDITABLE_LEDGER → 成員帳本 VDF_FetchGroups_MemberLedger_v0100.jsonl(只增)
  asof [--set YYYY-MM-DD|latest --apply]   全族群共用的 as-of 日(latest = 台北最近已收盤交易日)
  run --groups A,B [--as-of D] [--home H] [--mode live|fixture|block] [--dry]
      經 MDL008 尾版跑族群的引擎(相依只留選到的);支援日期旗標的引擎帶 asof_args;AkShare 族群產生有效選單交 011d。
      live 要本行程環境已開雙閘(VIA_NET_CONSENT=YES · VIA_SCRAPE_CONSENT);本檔只檢查、永不代設。沒開 = rc 4、零子行程。
  monitor [--groups …] [--as-of D] [--home H] [--json]
      逐族群逐表:≤ as-of 的筆數 · 最早 / 最晚日 · 落後天數(依 cadence 容忍)· 可增減族群的缺成員 · 燈;
      寫進 <輸出根>/VDF_FetchGroups.duckdb(fg_status 只增 + fg_status_latest 視圖)與 _reports/groups_*.json。
  query "<SQL>" [--as-of D] [--home H] [--sql-out F]
      來源庫唯讀 ATTACH → TEMP 視圖 g_<族群>__<表>(date <= as-of;可增減族群再篩成員)後跑 SQL;--sql-out 另存同一套視圖腳本。
  optimize [--home H] [--apply] [--compact]
      預設只列計畫(零寫);--apply = 每個庫 CHECKPOINT + ANALYZE(別的行程鎖著 = LOCKED 跳過,不搶鎖);
      --compact = VAKE 小分片合併(走 MDL011 compact,舊分片歸檔、只增)。大表依日期 + 代號重排交給 ENG073 --optimize。
  --selftest                    沙盤自測(零網路、零寫倉)
不碰 TA-Lib;不讀寫同意閘;燈誠實:沒有庫 / 表 = NODATA,不是綠。
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。本檔的連網全經 MDL008 子行程改道。"""
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

import contextlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
TAG = f"VDF_MDL012_FetchGroups v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
BOOK_GLOB = "VDF_FetchGroups_SSOT_v*.json"
FETCH_GLOB = "VDF_FetchSystem_SSOT_v*.json"
SEL_GLOB = "VDF_AkshareSelection_MacroShipping_v*.json"
MATRIX_GLOB = "VDF_Input_Interface_Matrix_v*.json"
MDL008_GLOB = "VDF_MDL008_FetchSystem_v*.py"
MDL011_GLOB = "VDF_MDL011_AkshareFetcher_v*.py"
LEDGER = HERE / "VDF_FetchGroups_MemberLedger_v0100.jsonl"
CATALOG = "VDF_FetchGroups.duckdb"
TPE = timezone(timedelta(hours=8))
SMALL_PART = 64 * 1024
LAMP_ORDER = {"GREEN": 0, "NODATE": 1, "YELLOW": 2, "LOCKED": 3, "NODATA": 4, "RED": 5}


# ---------- 冊 · 尾版 ----------
def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d+)$", p.stem)
    return int(m.group(1)) if m else -1


def tail(glob: str, folder: Path = HERE) -> Path | None:
    hits = sorted((p for p in folder.glob(glob) if _vnum(p) >= 0), key=_vnum)
    return hits[-1] if hits else None


def _json(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def load_book(path: Path | None = None) -> dict:
    p = path or tail(BOOK_GLOB)
    if not p:
        raise FileNotFoundError(f"{BOOK_GLOB} 不在 {HERE}")
    book = _json(p)
    book["_path"] = str(p)
    return book


def group_of(book: dict, gid: str) -> dict:
    for g in book["groups"]:
        if g["id"].upper() == str(gid).upper():
            return g
    raise KeyError(f"無此族群:{gid}(有效:{' / '.join(x['id'] for x in book['groups'])})")


def default_home(fetch_book: dict | None = None) -> Path:
    env = os.environ.get("VIA_VDF_FETCH_HOME")
    if env:
        return Path(env)
    rel = (fetch_book or {}).get("home_default") or "VIA_Reports/vdf_fetch/dict"
    return VIA / rel


# ---------- 帳本(只增) ----------
def read_ledger(path: Path = LEDGER) -> list:
    if not Path(path).is_file():
        return []
    out = []
    for ln in Path(path).read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if ln:
            try:
                out.append(json.loads(ln))
            except ValueError:
                continue
    return out


def append_ledger(rec: dict, path: Path = LEDGER) -> dict:
    rec = dict(rec, ts=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), by=TAG)
    with Path(path).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


# ---------- as-of ----------
def latest_trading_day(now: datetime | None = None) -> date:
    t = (now or datetime.now(timezone.utc)).astimezone(TPE)
    d = t.date()
    if t.hour < 15:
        d -= timedelta(days=1)
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d


def resolve_asof(value: str | None, now: datetime | None = None) -> str:
    v = (value or "latest").strip()
    if v.lower() == "latest":
        return latest_trading_day(now).isoformat()
    return datetime.strptime(v, "%Y-%m-%d").date().isoformat()


def current_asof_setting(book: dict, ledger: list) -> str:
    val = (book.get("as_of") or {}).get("default", "latest")
    for rec in ledger:
        if rec.get("kind") == "asof":
            val = rec.get("value") or val
    return val


# ---------- 成員 ----------
def _ledger_ops(ledger: list, gid: str) -> list:
    return [r for r in ledger if r.get("kind") == "member" and r.get("group") == gid]


def _apply_ops(base: list, ops: list) -> list:
    cur = list(dict.fromkeys(base))
    for r in ops:
        v = str(r.get("value"))
        if r.get("op") == "add" and v not in cur:
            cur.append(v)
        elif r.get("op") == "remove" and v in cur:
            cur.remove(v)
    return cur


def selection_base(g: dict, sel: dict) -> list:
    """選單組 ∩ 選單 fns(選單刻意不列的,例 NBS 分省 = 只在 full tier,不進基底)。"""
    base = list((sel.get("groups") or {}).get(g.get("selection_group"), []))
    if sel.get("fns"):
        allowed = set(sel["fns"])
        base = [f for f in base if f in allowed]
    if g.get("include"):
        base = [f for f in base if re.search(g["include"], f)]
    if g.get("exclude"):
        base = [f for f in base if not re.search(g["exclude"], f)]
    return base


def effective_members(g: dict, ledger: list, sel: dict | None = None, matrix: dict | None = None) -> dict:
    """{'members': list|None(None=全部不篩), 'exclude': list, 'filter': bool, 'origin': str}"""
    kind = g["membership"]
    if kind == "FIXED_ALL":
        return {"members": None, "exclude": [], "filter": False, "origin": g.get("members_from", "ALL")}
    if kind == "EDITABLE_MATRIX":
        sec = ((matrix or {}).get("sections") or {}).get(g["matrix_section"], {})
        return {"members": list(sec.get("tickers", [])), "exclude": list(sec.get("removed_tickers", [])),
                "filter": True, "origin": f"Input_Interface_Matrix.{g['matrix_section']}"}
    ops = _ledger_ops(ledger, g["id"])
    if kind == "EDITABLE_SELECTION":
        return {"members": _apply_ops(selection_base(g, sel or {}), ops), "exclude": [],
                "filter": True, "origin": f"AkShare 選單 {g.get('selection_group')} + 帳本 {len(ops)} 筆"}
    adds = _apply_ops([], ops)
    removes = [str(r["value"]) for r in ops if r.get("op") == "remove" and str(r["value"]) not in adds]
    if adds:
        return {"members": adds, "exclude": removes, "filter": True, "origin": f"帳本 {len(ops)} 筆"}
    return {"members": None, "exclude": removes, "filter": bool(removes), "origin": "全部(帳本只有排除)" if removes else "全部"}


def load_inputs(book: dict) -> tuple:
    sel_p, mat_p = tail(SEL_GLOB), tail(MATRIX_GLOB)
    return (_json(sel_p) if sel_p else {}), (_json(mat_p) if mat_p else {}), sel_p, mat_p


def plan_edit(book: dict, gid: str, op: str, values: list, ledger: list, sel: dict, matrix: dict) -> dict:
    g = group_of(book, gid)
    if g["membership"] == "FIXED_ALL":
        return {"rc": 2, "group": g["id"], "why": f"{g['zh']} = FIXED_ALL(抓全部、固定顯示全部),不給增減"}
    bad = [v for v in values if not re.fullmatch(r"[A-Za-z0-9_.\-^=:]+", str(v))]
    if bad:
        return {"rc": 2, "group": g["id"], "why": f"值不合格:{bad}"}
    eff = effective_members(g, ledger, sel, matrix)
    cur = set(eff["members"] or [])
    lines = []
    for v in values:
        if op == "add":
            lines.append(("SKIP" if v in cur else "OK", v, "已在名單" if v in cur else "加入"))
        else:
            lines.append(("OK" if v in cur or eff["members"] is None else "SKIP", v,
                          "移出" if v in cur else ("排除(目前全部)" if eff["members"] is None else "不在名單")))
    if g["membership"] == "EDITABLE_SELECTION" and op == "add":
        known = set(sel.get("fns") or [])
        lines = [(s, v, n + ("" if v in known or s == "SKIP" else " · 選單沒列這支(照加;跑時 MDL011 註冊表沒有會照列 skipped)")) for s, v, n in lines]
    return {"rc": 0, "group": g["id"], "kind": g["membership"], "op": op, "lines": lines}


def apply_edit(book: dict, plan: dict, mat_p: Path | None, ledger_path: Path = LEDGER) -> list:
    g = group_of(book, plan["group"])
    done = []
    todo = [v for s, v, _ in plan["lines"] if s == "OK"]
    if not todo:
        return done
    if g["membership"] == "EDITABLE_MATRIX":
        spec = importlib.util.spec_from_file_location("vdf_input_matrix_for_mdl012", HERE / "vdf_input_matrix_v0100.py")
        mx = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mx)
        d = mx.load(mat_p)
        fn = mx.add_ticker if plan["op"] == "add" else mx.rm_ticker
        for v in todo:
            done.append(fn(d, g["matrix_section"], v))
        mx.save(d, mat_p, op=f"MDL012 {plan['op']} {g['matrix_section']}", note=",".join(todo))
        return done
    for v in todo:
        append_ledger({"kind": "member", "group": g["id"], "op": plan["op"], "value": v}, ledger_path)
        done.append(f"OK:{v} {plan['op']} → 帳本")
    return done


# ---------- run ----------
def effective_selection(book: dict, gids: list, ledger: list, sel: dict) -> dict:
    out = {k: v for k, v in sel.items() if k not in ("groups", "fns")}
    groups = {}
    for gid in gids:
        g = group_of(book, gid)
        if g["membership"] == "EDITABLE_SELECTION":
            groups[g["id"]] = effective_members(g, ledger, sel)["members"]
    out["groups"] = groups
    out["fns"] = sorted({f for fs in groups.values() for f in fs})
    out["_from"] = f"{TAG} 有效選單(基底 {sel.get('version', '?')} + 成員帳本)"
    return out


def plan_rows(book: dict, fetch_book: dict, gids: list, as_of: str, sel_path: str | None) -> list:
    by_id = {r["id"]: r for r in fetch_book.get("engines", [])}
    picked, extra = [], {}
    sel_groups = []
    for gid in gids:
        g = group_of(book, gid)
        for eid in g.get("engines", []):
            if eid not in picked:
                picked.append(eid)
            for k, v in (g.get("asof_args") or {}).items():
                extra[k] = [str(x).replace("{as_of}", as_of) for x in v]
        if g["membership"] == "EDITABLE_SELECTION":
            sel_groups.append(g["id"])
    rows = []
    for eid in picked:
        if eid not in by_id:
            rows.append({"id": eid, "missing": True})
            continue
        r = dict(by_id[eid])
        r["needs"] = [n for n in r.get("needs", []) if n in picked]
        args = list(r.get("run_args") or [])
        if eid in extra:
            args += extra[eid]
        if r.get("selection") is not None or eid == "011d":
            args = [a for a in args if a not in ("--selection",)]
            if sel_path:
                args += ["--selection", sel_path]
            if sel_groups:
                args += ["--group", ",".join(sel_groups)]
        r["run_args"] = args
        r["as_of"] = as_of
        rows.append(r)
    return rows


def _load_mdl008():
    p = tail(MDL008_GLOB)
    spec = importlib.util.spec_from_file_location("mdl008_for_mdl012", p)
    m = importlib.util.module_from_spec(spec)
    sys.modules["mdl008_for_mdl012"] = m
    with contextlib.redirect_stdout(io.StringIO()):
        spec.loader.exec_module(m)
    return m, p


def gates_open() -> bool:
    return os.environ.get("VIA_NET_CONSENT") == "YES" and os.environ.get("VIA_SCRAPE_CONSENT", "OFF") not in ("", "OFF")


# ---------- DuckDB:來源 · 統計 ----------
def _duck():
    import duckdb
    return duckdb


def find_db(name: str, roots: list) -> Path | None:
    hits = []
    for root in roots:
        root = Path(root)
        if not root.is_dir():
            continue
        for p in root.rglob(name):
            if p.is_file() and "_quarantine" not in str(p) and "selftest" not in p.name:
                hits.append(p)
    if not hits:
        return None
    hits.sort(key=lambda p: ("output_hub" not in p.parts, -p.stat().st_size))
    return hits[0]


def _busy(exc: Exception) -> bool:
    """別的行程寫鎖(IOException lock)或同行程已開同一檔(Unique file handle conflict)= 忙,照實 LOCKED、不搶。"""
    t = str(exc).lower()
    return "lock" in t or "conflict" in t


def _q(ident: str) -> str:
    return '"' + str(ident).replace('"', '""') + '"'


def _date_expr(col: str, dtype: str) -> str:
    c = _q(col)
    t = (dtype or "").upper()
    if t == "DATE":
        return c
    if t.startswith("TIMESTAMP"):
        return f"CAST({c} AS DATE)"
    if t in ("INTEGER", "BIGINT", "HUGEINT", "INT", "UBIGINT"):
        return (f"COALESCE(TRY_CAST(try_strptime(CAST({c} AS VARCHAR), '%Y%m%d') AS DATE), "
                f"TRY_CAST(try_strptime(CAST({c} AS VARCHAR), '%Y%m') AS DATE))")
    return (f"COALESCE(TRY_CAST({c} AS DATE), TRY_CAST(try_strptime(CAST({c} AS VARCHAR), '%Y%m') AS DATE), "
            f"TRY_CAST(try_strptime(CAST({c} AS VARCHAR), '%Y-%m') AS DATE), TRY_CAST(try_strptime(CAST({c} AS VARCHAR), '%Y/%m/%d') AS DATE))")


def _pick(cols: dict, declared: str | None, candidates: list, types: tuple = ()) -> str | None:
    if declared and declared in cols:
        return declared
    for c in candidates:
        if c in cols:
            return c
    for c, t in cols.items():
        if types and str(t).upper().startswith(types):
            return c
    return None


def tolerance(cadence: str, tol: dict, gap: float | None) -> int:
    """容忍天數 = 冊上 cadence 容忍 與 資料本身更新間隔 × 1.5 取大(週資料不因 daily 族群被判紅)。"""
    t = int(tol.get(cadence, 0))
    if gap:
        t = max(t, int(-(-float(gap) * 1.5 // 1)))
    return t


def lamp(lag: int | None, cadence: str, tol: dict, missing: int = 0, gap: float | None = None) -> str:
    if lag is None:
        return "NODATE"
    t = tolerance(cadence, tol, gap)
    if lag <= t:
        st = "GREEN"
    elif lag <= max(3 * t, t + 4):
        st = "YELLOW"
    else:
        st = "RED"
    if missing and st == "GREEN":
        st = "YELLOW"
    return st


def _gap(con, dsql: str) -> float | None:
    """最近 13 個不同日期的相鄰間隔中位數(天);資料不足回 None。dsql = 產生欄 d 的子查詢。"""
    r = con.execute(f"SELECT median(g) FROM (SELECT d - lag(d) OVER (ORDER BY d) AS g FROM "
                    f"(SELECT DISTINCT d FROM ({dsql}) WHERE d IS NOT NULL ORDER BY d DESC LIMIT 13)) WHERE g IS NOT NULL").fetchone()
    return float(r[0]) if r and r[0] is not None else None


def _stats_relation(con, rel: str, cols: dict, src: dict, book: dict, as_of: str, eff: dict) -> dict:
    det = book.get("detect", {})
    dcol = _pick(cols, src.get("date_col"), det.get("date_cols", []), ("DATE", "TIMESTAMP"))
    kcol = _pick(cols, src.get("key_col"), det.get("key_cols", []))
    out = {"date_col": dcol, "key_col": kcol}
    out["rows_total"] = con.execute(f"SELECT count(*) FROM {rel}").fetchone()[0]
    if not dcol:
        out.update(rows_asof=out["rows_total"], min_date=None, max_date=None, keys_seen=None, gap_days=None)
    else:
        dx = _date_expr(dcol, cols[dcol])
        r = con.execute(f"SELECT count(*), min(d), max(d) FROM (SELECT {dx} AS d FROM {rel}) WHERE d <= DATE '{as_of}'").fetchone()
        out.update(rows_asof=r[0], min_date=str(r[1]) if r[1] else None, max_date=str(r[2]) if r[2] else None)
        out["gap_days"] = _gap(con, f"SELECT {dx} AS d FROM {rel} WHERE {dx} <= DATE '{as_of}'")
        out["keys_seen"] = (con.execute(f"SELECT count(DISTINCT {_q(kcol)}) FROM {rel} WHERE {dx} = DATE '{as_of}'").fetchone()[0]
                            if kcol else None)
    out["members_expected"], out["members_missing"] = None, None
    if eff.get("members") is not None and kcol:
        mem = [str(m) for m in eff["members"]]
        out["members_expected"] = len(mem)
        if mem:
            con.execute("CREATE OR REPLACE TEMP TABLE _fg_mem(m VARCHAR)")
            con.executemany("INSERT INTO _fg_mem VALUES (?)", [(m,) for m in mem])
            out["members_missing"] = con.execute(
                f"SELECT count(*) FROM _fg_mem WHERE m NOT IN (SELECT DISTINCT CAST({_q(kcol)} AS VARCHAR) FROM {rel})").fetchone()[0]
        else:
            out["members_missing"] = 0
    return out


def _lag(as_of: str, max_date: str | None) -> int | None:
    if not max_date:
        return None
    return (date.fromisoformat(as_of) - date.fromisoformat(max_date[:10])).days


def source_status(src: dict, g: dict, book: dict, as_of: str, eff: dict, roots: list, home: Path) -> list:
    duckdb = _duck()
    tol = book.get("cadence_tolerance_days", {})
    base = {"group_id": g["id"], "source": src["type"], "cadence": g.get("cadence", "daily")}
    if src["type"] == "vake":
        return vake_status(g, book, as_of, eff, home)
    con = duckdb.connect()
    try:
        if src["type"] == "duckdb":
            db = find_db(src["db"], roots)
            row = dict(base, db_path=str(db) if db else src["db"], table_name=src["table"])
            if not db:
                return [dict(row, state="NODATA", note=f"找不到 {src['db']}")]
            try:
                con.execute(f"ATTACH '{db.as_posix()}' AS s (READ_ONLY)")
            except Exception as exc:
                st = "LOCKED" if _busy(exc) else "NODATA"
                return [dict(row, state=st, note=f"{type(exc).__name__}: {str(exc)[:120]}")]
            cols = dict(con.execute("SELECT column_name, data_type FROM information_schema.columns "
                                    "WHERE table_catalog='s' AND table_name=? ORDER BY ordinal_position", [src["table"]]).fetchall())
            if not cols:
                return [dict(row, state="NODATA", note="庫在、表不在")]
            rel = f"s.{_q(src['table'])}"
        else:
            files = sorted(home.glob(src["glob"]))
            row = dict(base, db_path=str(home / src["glob"]), table_name=Path(src["glob"]).stem)
            if not files:
                return [dict(row, state="NODATA", note="parquet 不在")]
            lst = ", ".join("'" + f.as_posix() + "'" for f in files)
            con.execute(f"CREATE TEMP VIEW _p AS SELECT * FROM read_parquet([{lst}], union_by_name=true)")
            cols = dict(con.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='_p'").fetchall())
            rel = "_p"
        st = _stats_relation(con, rel, cols, src, book, as_of, eff)
        lag = _lag(as_of, st.get("max_date"))
        state = "RED" if st["rows_asof"] == 0 else lamp(lag, base["cadence"], tol, st.get("members_missing") or 0, st.get("gap_days"))
        return [dict(row, **st, lag_days=lag, state=state, note="")]
    except Exception as exc:
        return [dict(base, db_path=src.get("db") or src.get("glob"), table_name=src.get("table", ""), state="RED",
                     note=f"{type(exc).__name__}: {str(exc)[:160]}")]
    finally:
        con.close()


_PERIOD = re.compile(r"^(\d{4})年(?:(\d{1,2})月|第([1-4])季度)?$")


def _period_cols_max(cols: list) -> str | None:
    """NBS 寬表:期別在欄名(2026年8月 / 2026年第2季度 / 2025年)→ 取最晚一期的月初。"""
    best = None
    for c in cols:
        m = _PERIOD.match(str(c))
        if not m:
            continue
        y, mo, q = int(m.group(1)), m.group(2), m.group(3)
        d = date(y, int(mo), 1) if mo else (date(y, 3 * int(q) - 2, 1) if q else date(y, 1, 1))
        best = d if best is None or d > best else best
    return best.isoformat() if best else None


def vake_status(g: dict, book: dict, as_of: str, eff: dict, home: Path) -> list:
    """VAKE 族群:逐支讀僅增 parquet(_vake_date)截到 as-of;目錄庫 manifest 只拿狀態 / 錯誤(被鎖也照讀 parquet)。"""
    duckdb = _duck()
    tol = book.get("cadence_tolerance_days", {})
    cad = g.get("cadence", "macro")
    root = home / "vake"
    db = root / "db" / "vake.duckdb"
    store = root / "store"
    fns = list(eff.get("members") or [])
    base = {"group_id": g["id"], "source": "vake", "cadence": cad}
    man, man_note = {}, ""
    con = duckdb.connect()
    try:
        if db.is_file():
            try:
                con.execute(f"ATTACH '{db.as_posix()}' AS v (READ_ONLY)")
                for fn, stt, err in con.execute("SELECT fn, string_agg(DISTINCT last_status, ','), max(last_error) "
                                                "FROM v.vake_manifest GROUP BY fn").fetchall():
                    man[fn] = (stt or "", err or "")
                con.execute("DETACH v")
            except Exception as exc:
                man_note = ("目錄庫被鎖(擷取進行中)· " if _busy(exc) else "目錄庫讀不到 · ") + type(exc).__name__
        else:
            man_note = "vake.duckdb 不在"
        det = book.get("detect", {}).get("date_cols", [])
        out = []
        for fn in fns:
            glob = (store / "*" / fn / "*" / "*.parquet").as_posix()
            row = dict(base, db_path=glob, table_name=fn)
            stt, err = man.get(fn, ("", ""))
            note = " · ".join(x for x in (stt, err[:80], man_note) if x)
            if not list(store.glob(f"*/{fn}/*/*.parquet")):
                out.append(dict(row, state="RED" if "FAIL" in stt.upper() else "NODATA", note=note or "還沒抓過"))
                continue
            try:
                rel = f"read_parquet('{glob}', union_by_name=true)"
                cols = {r[0]: r[1] for r in con.execute(f"DESCRIBE SELECT * FROM {rel}").fetchall()}
                total = con.execute(f"SELECT count(*) FROM {rel}").fetchone()[0]
                dcol = None
                if "_vake_date" in cols and con.execute(f"SELECT count(_vake_date) FROM {rel}").fetchone()[0]:
                    dcol = "_vake_date"
                else:                                                   # _vake_date 全空 → 找資料本身的日期欄(不含 _vake_ 中繼欄)
                    dcol = _pick({k: v for k, v in cols.items() if not k.startswith("_vake_")}, None, det, ("DATE", "TIMESTAMP"))
                if dcol:
                    dx = _date_expr(dcol, cols[dcol])
                    n, mn, mx = con.execute(f"SELECT count(*) FILTER (WHERE d <= DATE '{as_of}'), min(d) FILTER (WHERE d <= DATE '{as_of}'), "
                                            f"max(d) FILTER (WHERE d <= DATE '{as_of}') FROM (SELECT {dx} AS d FROM {rel})").fetchone()
                    mn, mx = (str(mn) if mn else None), (str(mx) if mx else None)
                    gap = _gap(con, f"SELECT {dx} AS d FROM {rel} WHERE {dx} <= DATE '{as_of}'")
                else:
                    n, mn, gap = total, None, None
                    mx = _period_cols_max(list(cols))
                    if mx and mx > as_of:
                        mx = as_of
                    dcol = "期別欄(寬表)" if mx else None
                    if mx:
                        gap = 30.0
                lag = _lag(as_of, mx)
                state = "RED" if (dcol and not n) else lamp(lag, cad, tol, 0, gap)
                out.append(dict(row, date_col=dcol, rows_total=int(total), rows_asof=int(n or 0), min_date=mn, max_date=mx,
                                lag_days=lag, gap_days=gap, state=state, note=note))
            except Exception as exc:
                out.append(dict(row, state="RED", note=f"{type(exc).__name__}: {str(exc)[:120]}"))
        return out
    finally:
        con.close()


def monitor(book: dict, gids: list, as_of: str, home: Path, ledger: list, sel: dict, matrix: dict) -> list:
    roots = [home, HERE / "output_hub"]
    rows = []
    for gid in gids:
        g = group_of(book, gid)
        eff = effective_members(g, ledger, sel, matrix)
        for src in g.get("sources", []):
            for r in source_status(src, g, book, as_of, eff, roots, home):
                r.setdefault("rows_total", None)
                rows.append(r)
    return rows


def _con_catalog(home: Path):
    duckdb = _duck()
    home.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(home / CATALOG))
    con.execute("SET preserve_insertion_order=false")
    con.execute(f"SET temp_directory='{(home / '_duck_tmp').as_posix()}'")
    con.execute("""
CREATE TABLE IF NOT EXISTS fg_groups (group_id VARCHAR PRIMARY KEY, zh VARCHAR, en VARCHAR, membership VARCHAR,
  engines VARCHAR, cadence VARCHAR, n_members INTEGER, member_filter BOOLEAN, origin VARCHAR, updated_at TIMESTAMP);
CREATE TABLE IF NOT EXISTS fg_members (group_id VARCHAR, member VARCHAR, PRIMARY KEY (group_id, member));
CREATE TABLE IF NOT EXISTS fg_runs (run_id VARCHAR PRIMARY KEY, started TIMESTAMP, finished TIMESTAMP, as_of DATE,
  mode VARCHAR, groups VARCHAR, engines VARCHAR, rc_json VARCHAR);
CREATE TABLE IF NOT EXISTS fg_status (snap_id VARCHAR, snap_ts TIMESTAMP, as_of DATE, group_id VARCHAR, source VARCHAR,
  db_path VARCHAR, table_name VARCHAR, date_col VARCHAR, key_col VARCHAR, rows_total BIGINT, rows_asof BIGINT,
  keys_seen INTEGER, members_expected INTEGER, members_missing INTEGER, min_date DATE, max_date DATE, lag_days INTEGER,
  state VARCHAR, note VARCHAR);
ALTER TABLE fg_status ADD COLUMN IF NOT EXISTS gap_days DOUBLE;
CREATE OR REPLACE VIEW fg_status_latest AS SELECT * FROM fg_status WHERE snap_id = (SELECT max(snap_id) FROM fg_status);
CREATE OR REPLACE VIEW fg_group_lamp AS
  SELECT group_id, as_of, count(*) AS sources, sum(rows_asof) AS rows_asof, max(max_date) AS max_date,
         arg_max(state, CASE state WHEN 'RED' THEN 5 WHEN 'NODATA' THEN 4 WHEN 'LOCKED' THEN 3 WHEN 'YELLOW' THEN 2
                                   WHEN 'NODATE' THEN 1 ELSE 0 END) AS worst
  FROM fg_status_latest GROUP BY group_id, as_of;
""")
    return con


def sync_catalog(con, book: dict, ledger: list, sel: dict, matrix: dict) -> None:
    now = datetime.now()
    con.execute("BEGIN")
    con.execute("DELETE FROM fg_groups")
    con.execute("DELETE FROM fg_members")
    for g in book["groups"]:
        eff = effective_members(g, ledger, sel, matrix)
        mem = eff["members"] or []
        con.execute("INSERT INTO fg_groups VALUES (?,?,?,?,?,?,?,?,?,?)",
                    [g["id"], g["zh"], g["en"], g["membership"], ",".join(g.get("engines", [])), g.get("cadence"),
                     None if eff["members"] is None else len(mem), eff["filter"], eff["origin"], now])
        if mem:
            con.executemany("INSERT INTO fg_members VALUES (?,?)", [(g["id"], str(m)) for m in dict.fromkeys(mem)])
    con.execute("COMMIT")


_STATUS_COLS = ["group_id", "source", "db_path", "table_name", "date_col", "key_col", "rows_total", "rows_asof",
                "keys_seen", "members_expected", "members_missing", "min_date", "max_date", "lag_days", "state", "note", "gap_days"]


def write_status(con, rows: list, as_of: str) -> str:
    snap = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    ts = datetime.now()
    con.executemany("INSERT INTO fg_status (snap_id, snap_ts, as_of, " + ", ".join(_STATUS_COLS) + ") VALUES (?,?,?,"
                    + ",".join("?" * len(_STATUS_COLS)) + ")",
                    [[snap, ts, as_of] + [r.get(c) for c in _STATUS_COLS] for r in rows])
    return snap


def group_summary(rows: list) -> dict:
    out = {}
    for r in rows:
        s = out.setdefault(r["group_id"], {"sources": 0, "rows_asof": 0, "max_date": None, "worst": "GREEN", "states": {}})
        s["sources"] += 1
        s["rows_asof"] += int(r.get("rows_asof") or 0)
        if r.get("max_date") and (s["max_date"] is None or r["max_date"] > s["max_date"]):
            s["max_date"] = r["max_date"]
        s["states"][r["state"]] = s["states"].get(r["state"], 0) + 1
        if LAMP_ORDER.get(r["state"], 5) > LAMP_ORDER.get(s["worst"], 0):
            s["worst"] = r["state"]
    return out


# ---------- query 視圖 ----------
def _alias(name: str) -> str:
    return "db_" + re.sub(r"[^A-Za-z0-9]+", "_", Path(name).stem).lower()


def view_sql(book: dict, gids: list, as_of: str, home: Path, ledger: list, sel: dict, matrix: dict) -> list:
    duckdb = _duck()
    roots = [home, HERE / "output_hub"]
    stmts, attached = [], {}
    probe = duckdb.connect()
    try:
        for gid in gids:
            g = group_of(book, gid)
            eff = effective_members(g, ledger, sel, matrix)
            for src in g.get("sources", []):
                if src["type"] == "vake":
                    store = home / "vake" / "store"
                    for fn in eff.get("members") or []:
                        if list(store.glob(f"*/{fn}/*/*.parquet")):
                            stmts.append(f"CREATE OR REPLACE TEMP VIEW {_q('g_' + g['id'].lower() + '__' + fn)} AS "
                                         f"SELECT * FROM read_parquet('{(store / '*' / fn / '*' / '*.parquet').as_posix()}', union_by_name=true);")
                    continue
                if src["type"] != "duckdb":
                    continue
                db = find_db(src["db"], roots)
                if not db:
                    continue
                al = attached.get(str(db))
                if not al:
                    al = _alias(src["db"])
                    attached[str(db)] = al
                    stmts.append(f"ATTACH IF NOT EXISTS '{db.as_posix()}' AS {al} (READ_ONLY);")
                    probe.execute(f"ATTACH '{db.as_posix()}' AS {al} (READ_ONLY)")
                cols = dict(probe.execute("SELECT column_name, data_type FROM information_schema.columns "
                                          "WHERE table_catalog=? AND table_name=?", [al, src["table"]]).fetchall())
                if not cols:
                    continue
                det = book.get("detect", {})
                dcol = _pick(cols, src.get("date_col"), det.get("date_cols", []), ("DATE", "TIMESTAMP"))
                kcol = _pick(cols, src.get("key_col"), det.get("key_cols", []))
                where = [f"{_date_expr(dcol, cols[dcol])} <= DATE '{as_of}'"] if dcol else []
                if eff["filter"] and kcol:
                    if eff.get("members") is not None:
                        lst = ", ".join("'" + str(m).replace("'", "''") + "'" for m in eff["members"]) or "NULL"
                        where.append(f"CAST({_q(kcol)} AS VARCHAR) IN ({lst})")
                    if eff.get("exclude"):
                        lst = ", ".join("'" + str(m).replace("'", "''") + "'" for m in eff["exclude"])
                        where.append(f"CAST({_q(kcol)} AS VARCHAR) NOT IN ({lst})")
                name = _q(f"g_{g['id'].lower()}__{src['table']}")
                stmts.append(f"CREATE OR REPLACE TEMP VIEW {name} AS SELECT * FROM {al}.{_q(src['table'])}"
                             + (" WHERE " + " AND ".join(where) if where else "") + ";")
    finally:
        probe.close()
    return stmts


# ---------- optimize ----------
def _db_files(book: dict, home: Path) -> list:
    roots = [home, HERE / "output_hub"]
    seen = []
    for g in book["groups"]:
        for src in g.get("sources", []):
            if src["type"] == "duckdb":
                p = find_db(src["db"], roots)
                if p and p not in seen:
                    seen.append(p)
    for p in (home / "vake" / "db" / "vake.duckdb", home / CATALOG):
        if p.is_file() and p not in seen:
            seen.append(p)
    return seen


def optimize_plan(book: dict, home: Path) -> dict:
    duckdb = _duck()
    dbs = []
    for p in _db_files(book, home):
        wal = Path(str(p) + ".wal")
        rec = {"db": str(p), "mb": round(p.stat().st_size / 1e6, 2), "wal_mb": round(wal.stat().st_size / 1e6, 2) if wal.is_file() else 0,
               "tables": [], "advice": []}
        try:
            con = duckdb.connect()
            con.execute(f"ATTACH '{p.as_posix()}' AS s (READ_ONLY)")
            for t, est in con.execute("SELECT table_name, estimated_size FROM duckdb_tables() WHERE database_name='s' "
                                      "ORDER BY estimated_size DESC").fetchall():
                rec["tables"].append({"table": t, "est_rows": int(est or 0)})
            con.close()
        except Exception as exc:
            rec["state"] = "LOCKED" if _busy(exc) else "ERR"
            rec["advice"].append(f"{rec['state']}: {str(exc)[:100]}")
        if rec["wal_mb"]:
            rec["advice"].append("WAL 殘留 → CHECKPOINT")
        big = [t["table"] for t in rec["tables"] if t["est_rows"] >= 1_000_000]
        if big:
            rec["advice"].append("百萬列以上:" + ",".join(big) + " → 依 (日期, 代號) 重排可讓 zonemap 跳區(ENG073 --optimize)")
        rec["advice"].append("ANALYZE 更新統計(查詢計畫)")
        dbs.append(rec)
    store = home / "vake" / "store"
    vk = {"store": str(store), "fns": 0, "parts": 0, "small_parts": 0, "compact_fns": []}
    if store.is_dir():
        per = {}
        for f in store.glob("*/*/*/*.parquet"):
            fn = f.parts[-3]
            n, s = per.get(fn, (0, 0))
            per[fn] = (n + 1, s + (1 if f.stat().st_size < SMALL_PART else 0))
        vk.update(fns=len(per), parts=sum(n for n, _ in per.values()), small_parts=sum(s for _, s in per.values()),
                  compact_fns=sorted(fn for fn, (n, s) in per.items() if n >= 8))
    return {"dbs": dbs, "vake": vk}


def optimize_apply(book: dict, home: Path, compact: bool = False) -> list:
    duckdb = _duck()
    out = []
    for p in _db_files(book, home):
        before = p.stat().st_size
        try:
            con = duckdb.connect(str(p))
        except Exception as exc:
            out.append({"db": str(p), "state": "LOCKED" if _busy(exc) else "ERR", "note": str(exc)[:120]})
            continue
        try:
            con.execute("CHECKPOINT")
            con.execute("ANALYZE")
            con.execute("CHECKPOINT")
            out.append({"db": str(p), "state": "OK", "mb_before": round(before / 1e6, 2), "mb_after": round(p.stat().st_size / 1e6, 2)})
        except Exception as exc:
            out.append({"db": str(p), "state": "ERR", "note": str(exc)[:120]})
        finally:
            con.close()
    if compact and (home / "vake" / "store").is_dir():
        m11 = tail(MDL011_GLOB)
        env = dict(os.environ, VAKE_ROOT=str(home / "vake"), VIA_FROM_VDFSM="YES", PYTHONIOENCODING="utf-8")
        r = subprocess.run([sys.executable, str(m11), "compact"], capture_output=True, text=True, env=env, timeout=3600)
        out.append({"db": "vake compact", "state": "OK" if r.returncode == 0 else "ERR", "rc": r.returncode,
                    "note": (r.stdout or r.stderr).strip().splitlines()[-1:] if (r.stdout or r.stderr) else []})
    return out


# ---------- 顯示 ----------
_COLORS = {"GREEN": "green", "YELLOW": "yellow", "RED": "red", "NODATA": "magenta", "LOCKED": "cyan", "NODATE": "blue"}


def _print_table(title: str, header: list, rows: list, lamp_col: int | None = None) -> None:
    try:
        from rich.console import Console
        from rich.table import Table
        t = Table(title=title, show_lines=False)
        for h in header:
            t.add_column(h, overflow="fold")
        for r in rows:
            cells = ["" if c is None else str(c) for c in r]
            if lamp_col is not None:
                st = cells[lamp_col]
                cells[lamp_col] = f"[{_COLORS.get(st, 'white')}]{st}[/]"
            t.add_row(*cells)
        Console(width=max(120, int(os.environ.get("COLUMNS", "160")))).print(t)
    except Exception:
        print(title)
        print(" | ".join(header))
        for r in rows:
            print(" | ".join("" if c is None else str(c) for c in r))


def _ctx(args) -> tuple:
    book = load_book()
    fb_p = tail(FETCH_GLOB)
    fb = _json(fb_p) if fb_p else {}
    ledger = read_ledger()
    sel, matrix, sel_p, mat_p = load_inputs(book)
    home = Path(args.home) if getattr(args, "home", None) else default_home(fb)
    return book, fb, ledger, sel, matrix, sel_p, mat_p, home


def _gids(book: dict, arg: str | None) -> list:
    if not arg or arg.upper() == "ALL":
        return [g["id"] for g in book["groups"]]
    return [group_of(book, x.strip())["id"] for x in arg.split(",") if x.strip()]


def cmd_groups(args) -> int:
    book, fb, ledger, sel, matrix, *_ , home = _ctx(args)
    setting = current_asof_setting(book, ledger)
    rows = []
    for g in book["groups"]:
        eff = effective_members(g, ledger, sel, matrix)
        n = "全部" if eff["members"] is None else len(eff["members"])
        rows.append([g["id"], g["zh"], g["membership"], n, ",".join(g.get("engines", [])), g.get("cadence"), eff["origin"]])
    _print_table(f"{TAG} · 族群 {len(rows)} · as-of 設定 {setting} → {resolve_asof(setting)}",
                 ["族群", "名稱", "名單", "成員", "引擎", "頻率", "名單來源"], rows)
    return 0


def _master_count(home: Path) -> int | None:
    p = home / "0-1-TWStockList" / "tw_stock_list_latest.parquet"
    if not p.is_file():
        return None
    try:
        return _duck().connect().execute(f"SELECT count(*) FROM read_parquet('{p.as_posix()}')").fetchone()[0]
    except Exception:
        return None


def cmd_members(args) -> int:
    book, fb, ledger, sel, matrix, *_, home = _ctx(args)
    g = group_of(book, args.group)
    eff = effective_members(g, ledger, sel, matrix)
    if eff["members"] is None:
        n = _master_count(home) if g["id"] in ("TW_DAILY", "TW_MONTHLY_REV", "TW_FIN") else None
        print(f"[{g['id']}] {g['zh']} · {g['membership']} · 全部({eff['origin']})" + (f" · 目前清單 {n} 檔" if n else "")
              + (f" · 排除 {eff['exclude']}" if eff["exclude"] else ""))
        return 0
    print(f"[{g['id']}] {g['zh']} · {g['membership']} · {len(eff['members'])} 個 · {eff['origin']}")
    for m in eff["members"]:
        print("  " + str(m))
    return 0


def cmd_edit(args) -> int:
    book, fb, ledger, sel, matrix, sel_p, mat_p, home = _ctx(args)
    plan = plan_edit(book, args.group, args.cmd, args.values, ledger, sel, matrix)
    if plan["rc"]:
        print(f"[拒絕] {plan['why']}")
        return plan["rc"]
    for s, v, n in plan["lines"]:
        print(f"  [{s}] {v} · {n}")
    if not args.apply:
        print("  (只列計畫;加 --apply 才寫)")
        return 0
    for line in apply_edit(book, plan, mat_p):
        print("  " + line)
    return 0


def cmd_asof(args) -> int:
    book, fb, ledger, *_ = _ctx(args)
    cur = current_asof_setting(book, ledger)
    if not args.set:
        print(f"[as-of] 設定 {cur} → 解析 {resolve_asof(cur)}(全族群共用;{book['as_of']['latest_rule']})")
        return 0
    val = resolve_asof(args.set) if args.set.lower() != "latest" else "latest"
    if args.set.lower() != "latest":
        val = args.set
        resolve_asof(val)
    print(f"[as-of] {cur} → {val}(解析 {resolve_asof(val)})")
    if not args.apply:
        print("  (只列計畫;加 --apply 才寫進成員帳本)")
        return 0
    append_ledger({"kind": "asof", "value": val})
    print("  [OK] 已寫進帳本")
    return 0


def cmd_run(args) -> int:
    book, fb, ledger, sel, matrix, sel_p, mat_p, home = _ctx(args)
    gids = _gids(book, args.groups)
    as_of = resolve_asof(args.as_of or current_asof_setting(book, ledger))
    work = home.parent / "_fetch_groups"
    eff_sel = None
    if any(group_of(book, x)["membership"] == "EDITABLE_SELECTION" for x in gids):
        eff_sel = work / f"selection_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
        if not args.dry:
            work.mkdir(parents=True, exist_ok=True)
            eff_sel.write_text(json.dumps(effective_selection(book, gids, ledger, sel), ensure_ascii=False, indent=1), encoding="utf-8")
    rows = plan_rows(book, fb, gids, as_of, str(eff_sel) if eff_sel else None)
    miss = [r["id"] for r in rows if r.get("missing")]
    rows = [r for r in rows if not r.get("missing")]
    print(f"[run] 族群 {','.join(gids)} · as-of {as_of} · 引擎 {len(rows)}" + (f" · 冊上沒有 {miss}" if miss else "") + f" · 輸出根 {home}")
    for r in rows:
        print(f"  {r['id']:<8} {r['file'][:56]:<56} {' '.join(r['run_args'])}")
    if args.dry:
        print("  (--dry:只列,不起子行程、不寫檔)")
        return 0
    if args.mode == "live" and not gates_open():
        print("[GATED] 雙閘沒開 —— 零子行程、零出網、零寫檔。本行程環境開閘(操作員的手,本檔永不代設):"
              "VIA_NET_CONSENT=YES VIA_SCRAPE_CONSENT=YES")
        return 4
    m, mp = _load_mdl008()
    started = datetime.now()
    run = getattr(m, "run_v0107", None) or m.BASE.run
    res = run(rows, args.mode, home, logs=home.parent / "_logs", timeout=args.timeout)
    rc_map = {x["id"]: x.get("rc") for x in res}
    con = _con_catalog(home)
    try:
        run_id = f"FG_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
        con.execute("INSERT INTO fg_runs VALUES (?,?,?,?,?,?,?,?)",
                    [run_id, started, datetime.now(), as_of, args.mode, ",".join(gids), ",".join(rc_map), json.dumps(rc_map)])
        sync_catalog(con, book, ledger, sel, matrix)
    finally:
        con.close()
    for x in res:
        print(f"  {x['id']:<8} rc {x.get('rc')} · {x.get('sec', 0):.0f}s")
    bad = [k for k, v in rc_map.items() if v not in (0, None)]
    print(f"[run] 結束 · 失敗 {len(bad)}/{len(rc_map)} · 經 {mp.name}" + (f" · {bad}" if bad else ""))
    return 0 if not bad else 1


def cmd_monitor(args) -> int:
    book, fb, ledger, sel, matrix, sel_p, mat_p, home = _ctx(args)
    gids = _gids(book, args.groups)
    as_of = resolve_asof(args.as_of or current_asof_setting(book, ledger))
    t0 = time.time()
    rows = monitor(book, gids, as_of, home, ledger, sel, matrix)
    summ = group_summary(rows)
    snap = None
    if not args.no_write:
        con = _con_catalog(home)
        try:
            sync_catalog(con, book, ledger, sel, matrix)
            snap = write_status(con, rows, as_of)
        finally:
            con.close()
        rep = home.parent / "_reports"
        rep.mkdir(parents=True, exist_ok=True)
        body = {"tool": TAG, "as_of": as_of, "home": str(home), "snap_id": snap, "groups": summ, "rows": rows}
        txt = json.dumps(body, ensure_ascii=False, indent=1, default=str)
        (rep / f"groups_{snap}.json").write_text(txt, encoding="utf-8")
        (rep / "groups_latest.json").write_text(txt, encoding="utf-8")
    if args.json:
        print(json.dumps({"as_of": as_of, "groups": summ}, ensure_ascii=False, default=str))
        return 0
    zh = {g["id"]: g["zh"] for g in book["groups"]}
    _print_table(f"{TAG} · as-of {as_of}(全族群同一天)· {home}",
                 ["族群", "名稱", "來源", "≤as-of 筆數", "最晚", "燈", "分佈"],
                 [[gid, zh.get(gid), s["sources"], s["rows_asof"], s["max_date"], s["worst"],
                   " ".join(f"{k}{v}" for k, v in sorted(s["states"].items()))] for gid, s in summ.items()], lamp_col=5)
    detail = [r for r in rows if not (r["source"] == "vake" and r["state"] == "GREEN")]
    _print_table("明細(VAKE 綠燈逐支省略,全在 fg_status)",
                 ["族群", "表 / 函式", "日期欄", "代號欄", "≤as-of", "最早", "最晚", "落後天", "缺成員", "燈", "註"],
                 [[r["group_id"], r.get("table_name"), r.get("date_col"), r.get("key_col"), r.get("rows_asof"), r.get("min_date"),
                   r.get("max_date"), r.get("lag_days"), r.get("members_missing"), r["state"], (r.get("note") or "")[:60]]
                  for r in detail], lamp_col=9)
    print(f"[monitor] {len(rows)} 列 · {time.time() - t0:.1f}s" + (f" · 目錄 {home / CATALOG} snap {snap}" if snap else " · 未寫(--no-write)"))
    return 0


def cmd_query(args) -> int:
    book, fb, ledger, sel, matrix, sel_p, mat_p, home = _ctx(args)
    gids = _gids(book, args.groups)
    as_of = resolve_asof(args.as_of or current_asof_setting(book, ledger))
    stmts = view_sql(book, gids, as_of, home, ledger, sel, matrix)
    if args.sql_out:
        Path(args.sql_out).write_text(f"-- {TAG} · as-of {as_of}\n" + "\n".join(stmts) + "\n", encoding="utf-8")
        print(f"[query] 視圖腳本 {len(stmts)} 句 → {args.sql_out}")
    duckdb = _duck()
    con = duckdb.connect()
    for s in stmts:
        con.execute(s)
    if (home / CATALOG).is_file():
        con.execute(f"ATTACH '{(home / CATALOG).as_posix()}' AS cat (READ_ONLY)")
    if not args.sql:
        names = [r[0] for r in con.execute("SELECT view_name FROM duckdb_views() WHERE temporary ORDER BY 1").fetchall()]
        print(f"[query] as-of {as_of} · 視圖 {len(names)}:" + (" ".join(names[:80]) or "(無來源庫)"))
        return 0
    cur = con.execute(args.sql)
    head = [d[0] for d in cur.description or []]
    data = cur.fetchmany(args.limit)
    _print_table(f"[query] as-of {as_of}", head, [list(r) for r in data])
    return 0


def cmd_optimize(args) -> int:
    book, fb, ledger, sel, matrix, sel_p, mat_p, home = _ctx(args)
    plan = optimize_plan(book, home)
    _print_table(f"{TAG} · 最佳化計畫 · {home}", ["庫", "MB", "WAL MB", "表數", "最大表(估列)", "建議"],
                 [[Path(d["db"]).name, d["mb"], d["wal_mb"], len(d["tables"]),
                   (f"{d['tables'][0]['table']}({d['tables'][0]['est_rows']})" if d["tables"] else ""), " · ".join(d["advice"])]
                  for d in plan["dbs"]])
    vk = plan["vake"]
    print(f"[VAKE] 函式 {vk['fns']} · 分片 {vk['parts']} · <64KB 小分片 {vk['small_parts']} · 可合併(≥8 片){len(vk['compact_fns'])}")
    if not args.apply:
        print("  (只列計畫;--apply = CHECKPOINT + ANALYZE;再加 --compact = VAKE 小分片合併)")
        return 0
    res = optimize_apply(book, home, compact=args.compact)
    for r in res:
        print(f"  [{r['state']}] {Path(r['db']).name} " + (f"{r.get('mb_before')} → {r.get('mb_after')} MB" if r["state"] == "OK" and "mb_before" in r else str(r.get("note", ""))))
    return 0 if all(r["state"] in ("OK", "LOCKED") for r in res) else 1


# ---------- 自測 ----------
def selftest() -> int:
    import shutil
    import tempfile
    duckdb = _duck()
    res = []

    def chk(name, cond, note=""):
        res.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {note}" if note and not cond else ""))

    book = load_book()
    ids = [g["id"] for g in book["groups"]]
    fixed = sorted(g["id"] for g in book["groups"] if g["membership"] == "FIXED_ALL")
    chk("① 冊:族群 ≥ 12 · 台股每日 / 指數 / 主動式 ETF = FIXED_ALL", len(ids) >= 12 and {"TW_DAILY", "TW_INDEX", "TW_ACTIVE_ETF"} <= set(fixed), fixed)
    sel, matrix, sel_p, mat_p = load_inputs(book)
    p = plan_edit(book, "TW_INDEX", "add", ["XYZ"], [], sel, matrix)
    chk("② FIXED_ALL 拒絕增減(rc 2)", p["rc"] == 2)
    tmp = Path(tempfile.mkdtemp(prefix="mdl012_"))
    try:
        led = tmp / "ledger.jsonl"
        nbs = effective_members(group_of(book, "CN_NBS"), [], sel)["members"]
        cn = effective_members(group_of(book, "CN_MACRO"), [], sel)["members"]
        chk("③ 中國經濟 / NBS 由同一選單組切開、不重疊 · 選單刻意不列的(NBS 分省 full tier)不進基底", nbs and cn and all(f.startswith("macro_china_nbs") for f in nbs)
            and not set(nbs) & set(cn) and len(nbs) + len(cn) == len(set(sel["groups"]["china_macro"]) & set(sel["fns"]))
            and "macro_china_nbs_region" not in nbs, (len(nbs), len(cn)))
        pl = plan_edit(book, "SHIPPING", "remove", ["macro_shipping_bdi"], [], sel, matrix)
        apply_edit(book, pl, None, led)
        pl = plan_edit(book, "SHIPPING", "add", ["macro_shipping_xyz"], read_ledger(led), sel, matrix)
        apply_edit(book, pl, None, led)
        lg = read_ledger(led)
        ship = effective_members(group_of(book, "SHIPPING"), lg, sel)["members"]
        chk("④ 帳本增減:SHIPPING 移出 bdi、加入 xyz(只增帳本 2 列)", "macro_shipping_bdi" not in ship and "macro_shipping_xyz" in ship and len(lg) == 2)
        es = effective_selection(book, ["CN_NBS", "SHIPPING"], lg, sel)
        chk("⑤ 有效選單:只含選到的族群 · fns = 聯集 · overrides 保留", set(es["groups"]) == {"CN_NBS", "SHIPPING"}
            and set(es["fns"]) == set(nbs) | set(ship) and es.get("overrides") == sel.get("overrides"))
        ny = datetime(2026, 10, 4, 3, 0, tzinfo=timezone.utc)
        chk("⑥ as-of:週日 → 週五 · 固定日照用 · 15:00 前算前一交易日",
            resolve_asof("latest", ny) == "2026-10-02" and resolve_asof("2026-09-30") == "2026-09-30"
            and resolve_asof("latest", datetime(2026, 10, 6, 5, 0, tzinfo=timezone.utc)) == "2026-10-05")
        fb = _json(tail(FETCH_GLOB))
        rows = plan_rows(book, fb, ["TW_INDEX", "INTL_DAILY", "CN_NBS", "SHIPPING", "TW_DAILY"], "2026-10-02", "/x/sel.json")
        rm = {r["id"]: r for r in rows}
        chk("⑦ run 計畫:e232 帶 --start/--end as-of · e066 帶 --end · 011d 帶有效選單 + --group · 相依只留選到的",
            rm["e232"]["run_args"][-4:] == ["--start", "2026-10-02", "--end", "2026-10-02"]
            and rm["e066"]["run_args"][-2:] == ["--end", "2026-10-02"]
            and "--selection" in rm["011d"]["run_args"] and rm["011d"]["run_args"][-1] == "CN_NBS,SHIPPING"
            and rm["e054"]["needs"] == ["009"] and "010" not in rm, {k: v.get("run_args") for k, v in rm.items()})
        home = tmp / "home"
        (home / "output_hub" / "mega").mkdir(parents=True)
        (home / "output_hub" / "tw_index").mkdir(parents=True)
        c = duckdb.connect(str(home / "output_hub" / "mega" / "vdf_global_market.duckdb"))
        c.execute("CREATE TABLE global_daily(date DATE, ticker VARCHAR, close DOUBLE)")
        c.execute("INSERT INTO global_daily VALUES ('2026-09-30','AAPL',1),('2026-10-02','AAPL',2),('2026-10-05','AAPL',3),('2026-10-02','MSFT',4)")
        c.execute("CREATE TABLE us_macro(date DATE, series VARCHAR, value DOUBLE)")
        c.execute("INSERT INTO us_macro VALUES ('2026-08-01','CPI',1),('2026-09-01','CPI',2)")
        c.close()
        c = duckdb.connect(str(home / "output_hub" / "tw_index" / "VDF_TWIndex_Daily.duckdb"))
        c.execute("CREATE TABLE tw_index_daily(date VARCHAR, index_code VARCHAR, close DOUBLE)")
        c.execute("INSERT INTO tw_index_daily VALUES ('2026-10-01','TAIEX',1),('2026-10-01','TPEX',2)")
        c.close()
        mtx = {"sections": {"INTL_DAILY": {"tickers": ["AAPL", "TSLA"], "removed_tickers": []}}}
        st = monitor(book, ["INTL_DAILY", "TW_INDEX", "US_MACRO", "TW_FIN"], "2026-10-02", home, [], sel, mtx)
        by = {(r["group_id"], r["table_name"]): r for r in st}
        gd, ti, um, tf = by[("INTL_DAILY", "global_daily")], by[("TW_INDEX", "tw_index_daily")], by[("US_MACRO", "us_macro")], by[("TW_FIN", "tw_financial")]
        chk("⑧ 監控:≤ as-of 截齊(3 列,不含 10-05)· 到齊 GREEN · 缺成員 TSLA 計 1 → YELLOW",
            gd["rows_asof"] == 3 and gd["max_date"] == "2026-10-02" and gd["members_missing"] == 1 and gd["state"] == "YELLOW", gd)
        chk("⑨ 監控:VARCHAR 日期也能截齊 · 落後 1 天 = YELLOW · 月資料落後 31 天 = GREEN · 庫不在 = NODATA(不是綠)",
            ti["lag_days"] == 1 and ti["state"] == "YELLOW" and um["lag_days"] == 31 and um["state"] == "GREEN"
            and tf["state"] == "NODATA", (ti, um, tf))
        con = _con_catalog(home)
        sync_catalog(con, book, [], sel, mtx)
        snap1 = write_status(con, st, "2026-10-02")
        time.sleep(0.01)
        snap2 = write_status(con, st, "2026-10-02")
        n_all = con.execute("SELECT count(*) FROM fg_status").fetchone()[0]
        n_last = con.execute("SELECT count(*) FROM fg_status_latest").fetchone()[0]
        lampv = dict(con.execute("SELECT group_id, worst FROM fg_group_lamp").fetchall())
        ng = con.execute("SELECT count(*) FROM fg_groups").fetchone()[0]
        con.close()
        chk("⑩ DuckDB 目錄:fg_status 只增(兩次快照 2×)· latest 視圖只取最新 · 族群燈取最差 · fg_groups 全族群",
            n_all == 2 * len(st) and n_last == len(st) and snap2 > snap1 and lampv.get("TW_FIN") == "NODATA" and ng == len(ids), (n_all, n_last, lampv))
        stmts = view_sql(book, ["INTL_DAILY", "TW_INDEX"], "2026-10-02", home, [], sel, mtx)
        q = duckdb.connect()
        for s in stmts:
            q.execute(s)
        tick = q.execute('SELECT DISTINCT ticker FROM "g_intl_daily__global_daily" ORDER BY 1').fetchall()
        mx = q.execute('SELECT max(date) FROM "g_intl_daily__global_daily"').fetchone()[0]
        nidx = q.execute('SELECT count(*) FROM "g_tw_index__tw_index_daily"').fetchone()[0]
        q.close()
        chk("⑪ query 視圖:可增減族群只留成員(AAPL)· date <= as-of · FIXED_ALL 不篩成員", tick == [("AAPL",)] and str(mx) == "2026-10-02" and nidx == 2, (tick, mx, nidx))
        plan = optimize_plan(book, home)
        res_o = optimize_apply(book, home)
        chk("⑫ 最佳化:計畫列出全部庫(含目錄)· --apply CHECKPOINT + ANALYZE 全 OK", len(plan["dbs"]) == 3 and all(r["state"] == "OK" for r in res_o), (plan["dbs"], res_o))
        lk = duckdb.connect(str(home / "output_hub" / "mega" / "vdf_global_market.duckdb"))
        try:
            rows_l = source_status(group_of(book, "INTL_DAILY")["sources"][0], group_of(book, "INTL_DAILY"), book, "2026-10-02",
                                   {"members": None, "filter": False}, [home], home)
        finally:
            lk.close()
        chk("⑬ 同行程已開寫連線時仍能唯讀統計(或照實 LOCKED,不搶鎖)", rows_l[0]["state"] in ("GREEN", "YELLOW", "LOCKED"), rows_l)
        vs = home / "vake" / "store" / "macro"
        (vs / "drewry_wci_index" / "h1").mkdir(parents=True)
        (vs / "macro_china_nbs_nation" / "h2").mkdir(parents=True)
        w = duckdb.connect()
        w.execute(f"COPY (SELECT CAST(d AS DATE) AS _vake_date, 1.0 AS wci FROM range(DATE '2026-08-06', DATE '2026-10-09', INTERVAL 7 DAY) t(d)) "
                  f"TO '{(vs / 'drewry_wci_index' / 'h1' / 'part_1.parquet').as_posix()}' (FORMAT parquet)")
        w.execute(f"COPY (SELECT 'x' AS \"index\", 1.0 AS \"2026年8月\", 2.0 AS \"2026年7月\", CAST(NULL AS DATE) AS _vake_date) "
                  f"TO '{(vs / 'macro_china_nbs_nation' / 'h2' / 'part_1.parquet').as_posix()}' (FORMAT parquet)")
        w.close()
        vk = {r["table_name"]: r for r in vake_status(group_of(book, "SHIPPING"), book, "2026-10-02",
                                                      {"members": ["drewry_wci_index", "macro_shipping_bdi"]}, home)}
        nb = vake_status(group_of(book, "CN_NBS"), book, "2026-10-02", {"members": ["macro_china_nbs_nation"]}, home)[0]
        dw = vk["drewry_wci_index"]
        chk("⑭ VAKE:讀 parquet 截到 as-of(10-08 那筆不算)· 週資料依自身間隔容忍 = GREEN · 沒抓過 = NODATA · NBS 寬表由期別欄取最晚期",
            dw["rows_asof"] == 9 and dw["max_date"] == "2026-10-01" and dw["gap_days"] == 7 and dw["state"] == "GREEN"
            and vk["macro_shipping_bdi"]["state"] == "NODATA" and nb["max_date"] == "2026-08-01" and nb["state"] == "GREEN", (dw, vk["macro_shipping_bdi"], nb))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    ok = sum(res)
    print(f"[計] {TAG} 本版 {ok}/{len(res)} · 合計 {'PASS' if ok == len(res) else 'FAIL'}")
    return 0 if ok == len(res) else 1


def main(argv=None) -> int:
    import argparse
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--selftest"]:
        return selftest()
    ap = argparse.ArgumentParser(prog=TAG, description="擷取大族群:增減 · as-of · DuckDB 監控 · 最佳化")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("groups"); s.add_argument("--home")
    s = sub.add_parser("members"); s.add_argument("group"); s.add_argument("--home")
    for op in ("add", "remove"):
        s = sub.add_parser(op); s.add_argument("group"); s.add_argument("values", nargs="+"); s.add_argument("--apply", action="store_true"); s.add_argument("--home")
    s = sub.add_parser("asof"); s.add_argument("--set"); s.add_argument("--apply", action="store_true"); s.add_argument("--home")
    s = sub.add_parser("run"); s.add_argument("--groups", required=True); s.add_argument("--as-of"); s.add_argument("--home")
    s.add_argument("--mode", default="live", choices=["live", "fixture", "block"]); s.add_argument("--dry", action="store_true")
    s.add_argument("--timeout", type=int, default=1800)
    s = sub.add_parser("monitor"); s.add_argument("--groups"); s.add_argument("--as-of"); s.add_argument("--home")
    s.add_argument("--json", action="store_true"); s.add_argument("--no-write", action="store_true")
    s = sub.add_parser("query"); s.add_argument("sql", nargs="?"); s.add_argument("--groups"); s.add_argument("--as-of"); s.add_argument("--home")
    s.add_argument("--sql-out"); s.add_argument("--limit", type=int, default=50)
    s = sub.add_parser("optimize"); s.add_argument("--home"); s.add_argument("--apply", action="store_true"); s.add_argument("--compact", action="store_true")
    a = ap.parse_args(argv)
    fn = {"groups": cmd_groups, "members": cmd_members, "add": cmd_edit, "remove": cmd_edit, "asof": cmd_asof,
          "run": cmd_run, "monitor": cmd_monitor, "query": cmd_query, "optimize": cmd_optimize}[a.cmd]
    try:
        return fn(a)
    except KeyError as exc:
        print(f"[錯] {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
