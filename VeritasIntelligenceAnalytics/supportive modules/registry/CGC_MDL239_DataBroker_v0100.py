#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL239_DataBroker v0100 — VCGC 資料中介:VRN 要料 → VCGC 先讀庫 → 不夠才轉交 VDF 擷取 → 經 VCGC 回 VRN

操作員 2026-09-28 R25:「VRN 他需要擷取資料透過 VCGC 進入資料庫或轉交 VDF 擷取透過 VCGC 返回 VRN」。
量過(R25 盤點):樹內沒有 VRN→VCGC→VDF 的中介;VRN 尾版約 15 支直接開 VDF 的 .duckdb。本支是那條中介:

  要料契約  {requester, table, codes[], start, end, cols[], grace_days}   (VRN 引擎名 · 表名 · 代號 · 區間 · 欄)
  ① 路由    表 → 哪本庫 · 哪幾個 VDF 項能產它 —— **只從兩本冊推**(L05 不另立尺):
            InputConsole 規格冊 vdf 項的 outputs(裸表名 / `庫.duckdb::表`)+ VIA_DB_Table_SSOT 尾版(表 → 庫)。
            冊上沒有路由的表 = ABSENT(零發明:不猜哪支引擎會產它)。
  ② 讀庫    資料家(CGC_MDL238 → CGC_MDL123 同一把尺)裡的**來源庫唯讀**;開不了(寫者持鎖 / 不在)才讀
            Parquet 目錄 VIEW(VIA_Parquet_Catalog.duckdb)。代號欄、日期欄從表的欄位認(不寫死每張表)。
  ③ 夠不夠  每個代號都在、最新日期不落後目標(end 或今天)超過 grace_days = 夠(GREEN)。
  ④ 轉交    不夠 → 路由上第一個非寫庫動詞的 VDF 項,參數只帶該項冊上宣告的(start/end/codes…),經 EngineBus
            `call()`(CGC_MDL148 尾版,統一呼叫契約)。預設乾跑 = PLAN;`--apply` 才真跑。
            需網路的項:同意閘(VIA_NET_CONSENT)未開 = GATED,不起子行程;**本支只讀那個開關,永不代設**(L07/L08)。
  ⑤ 回 VRN  真跑回綠 → 重讀庫 → 結果寫成 Parquet(VIA_Reports/data_broker/out/<requester>/…)+ 帳本一行
            (LEDGER.jsonl · BROKER_latest.json;VIA_Reports 再生件不入版控)。VRN 用 `fetch()` 拿到路徑與列數。
  另:bypass() 量 VRN 尾版仍直開 VDF 庫的支數(操作台一盞燈;舊引擎不動,L04 換版才遷)。
     build() = VCGC→VDF 建庫計畫:冊上「正庫」表逐張量在不在 / 新不新,缺的排 VDF 項(預設乾跑)。

只收 VCGC 呼叫(CLI 要 VIA_FROM_VCGC=YES;函式由 VCGC 引擎與 VRN 新版引擎匯入)。本支零網路;網路只在被轉交的
VDF 引擎裡,且由它自己的同意閘管。來源庫只開 read_only。用法:
  python3 CGC_MDL239_DataBroker_v0100.py routes | status | bypass | build [--apply] [--home <夾>]
  python3 CGC_MDL239_DataBroker_v0100.py request --table tw_daily_prices --codes 2330,2317 --start 2024-01-01 \
          [--end …] [--cols date,close] [--requester VRN_ENG068] [--no-handoff] [--apply] [--home <夾>]
  python3 CGC_MDL239_DataBroker_v0100.py --selftest
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

import hashlib
import importlib.util
import json
import os
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REPORTS = VIA / "VIA_Reports" / "data_broker"
SPEC_GLOB = "VIA_InputConsole_Spec_v*.json"
DBSSOT_GLOB = "VIA_DB_Table_SSOT_v*.json"
VRN_DIR = VIA / "functional modules" / "VRN"
ENGINE = Path(__file__).stem
VERSION = "0100"
CATALOG = "VIA_Parquet_Catalog.duckdb"
CODE_COLS = ("ticker", "code", "stock_id", "symbol", "series", "series_id", "etf_ticker", "holding_ticker")
DATE_COLS = ("date", "trade_date", "portfolio_date", "report_date", "ym", "period", "dt")
CODE_RX = re.compile(r"^[\^A-Za-z0-9_.=\-]{1,24}$")
WHEN_RX = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")
IDENT_RX = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
TABLE_RX = re.compile(r"^[a-z][a-z0-9_]*$")
REQ_RX = re.compile(r"^[A-Za-z0-9_.\-]{1,64}$")
PARAM_MAP = {"start": "start", "since": "start", "end": "end", "since_ym": "start_ym", "codes": "codes", "tickers": "codes"}
DEFAULT_TIMEOUT = 1800


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", path.stem)
    return int(m.group(1)) if m else -1


def _newest(folder: Path, pattern: str) -> Path | None:
    hits = sorted(folder.glob(pattern), key=_vnum)
    return hits[-1] if hits else None


_MODS: dict = {}


def mod(stem: str):
    """Newest registry engine by stem, loaded once (MDL148 EngineBus · MDL238 operator console)."""
    if stem not in _MODS:
        p = _newest(HERE, stem + "_v*.py")
        m = None
        if p is not None:
            spec = importlib.util.spec_from_file_location(stem + "_for_" + ENGINE, p)
            m = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = m
            spec.loader.exec_module(m)
        _MODS[stem] = m
    return _MODS[stem]


def _duckdb():
    try:
        import duckdb
        return duckdb
    except Exception:
        return None


def _q(name: str) -> str:
    return '"' + str(name).replace('"', '""') + '"'


def _lit(s: str) -> str:
    return "'" + str(s).replace("'", "''") + "'"


def _json(path: Path | None):
    if path is None or not Path(path).exists():
        return None
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return None


# ───────────────────────── ① routes: two books, no second ruler ─────────────────────────

def _table_of(out: str):
    """One spec `outputs` entry → (db stem or '', table), or None when it is a report / file, not a table."""
    s = str(out).strip()
    if "::" in s:
        db, t = s.split("::", 1)
        return (Path(db).stem, t) if TABLE_RX.match(t) else None
    return ("", s) if TABLE_RX.match(s) else None


def routes(spec: dict | None = None, ssot: dict | None = None) -> list:
    spec = spec if spec is not None else (_json(_newest(HERE, SPEC_GLOB)) or {})
    ssot = ssot if ssot is not None else (_json(_newest(HERE, DBSSOT_GLOB)) or {})
    out: dict = {}
    for g in ((spec.get("families") or {}).get("vdf") or {}).get("groups") or []:
        for it in g.get("items") or []:
            eng = it.get("engine") or {}
            verb = list(it.get("verb") or eng.get("verb") or [])
            for o in it.get("outputs") or []:
                hit = _table_of(o)
                if not hit:
                    continue
                db, t = hit
                r = out.setdefault(t, {"table": t, "dbs": [], "items": [], "in_ssot": False, "role": "", "min_rows": 0})
                if db and db not in r["dbs"]:
                    r["dbs"].append(db)
                if not any(x["id"] == it["id"] for x in r["items"]):
                    params = [p if isinstance(p, str) else p.get("name", "") for p in (it.get("params") or [])]
                    r["items"].append({"id": it["id"], "zh": it.get("zh", ""), "group": g.get("id", ""), "params": params,
                                       "net": bool(it.get("net")), "write": "--apply" in verb})
    for row in ssot.get("tables") or []:
        r = out.get(row.get("table"))
        if r is None:
            continue
        db = Path(row.get("db", "")).stem
        if db and db not in r["dbs"]:
            r["dbs"].append(db)
        r["in_ssot"] = True
        r["role"] = r["role"] or row.get("role", "")
        r["min_rows"] = max(r["min_rows"], int(row.get("min_rows") or 0))
    return [out[k] for k in sorted(out)]


def unrouted(ssot: dict | None = None, rts: list | None = None) -> list:
    """Tables the table book knows but no VDF item declares as output (honest list; the broker cannot fetch them)."""
    ssot = ssot if ssot is not None else (_json(_newest(HERE, DBSSOT_GLOB)) or {})
    have = {r["table"] for r in (rts if rts is not None else routes(ssot=ssot))}
    return sorted({f"{Path(r.get('db', '')).stem}::{r.get('table')}" for r in ssot.get("tables") or [] if r.get("table") not in have})


# ───────────────────────── ② read the store (read-only) ─────────────────────────

def data_home(override: str | None = None):
    """Same home as the store scanner: EngineBus data_home (env VIA_DATA_HOME > catalog page > CGC_MDL123)."""
    if override:
        return Path(override), "--home"
    bus = mod("CGC_MDL148_EngineBus")
    if bus is None:
        return None, "CGC_MDL148 EngineBus 尾版不在"
    return bus.data_home()


def _skip(p: Path) -> bool:
    sp = str(p).replace("\\", "/")
    return p.name == CATALOG or "/parquet/" in sp or "/references/" in sp or "SCOPE_COPY" in sp


def _stores(home: Path | None, explicit: bool = False) -> list:
    """Which .duckdb files to look in. No folder named = EngineBus db_files() (the one scanner: repo + data home);
    a folder named (--home / fixture) = that folder only."""
    if not explicit:
        bus = mod("CGC_MDL148_EngineBus")
        if bus is not None:
            return [p for p in bus.db_files() if not _skip(p)]
    if home is None or not Path(home).exists():
        return []
    return sorted(p for p in Path(home).rglob("*.duckdb") if not _skip(p))


def locate(home: Path | None, table: str, dbs: list, explicit: bool = False, stores: list | None = None) -> list:
    """Where the table can be read: source stores first (freshest truth), then the Parquet catalog VIEW."""
    duckdb = _duckdb()
    found = []
    if duckdb is None:
        return found
    for p in (stores if stores is not None else _stores(home, explicit)):
        if dbs and p.stem not in dbs:
            continue
        try:
            con = duckdb.connect(str(p), read_only=True)
        except Exception as exc:                     # a writer holds the lock: say so, try the catalog next
            found.append({"kind": "duckdb", "path": str(p), "rel": table, "ok": False, "why": f"開不了:{type(exc).__name__}"})
            continue
        try:
            n = con.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='main' AND table_name=?",
                            [table]).fetchone()[0]
        finally:
            con.close()
        if n:
            found.append({"kind": "duckdb", "path": str(p), "rel": table, "ok": True, "why": ""})
    cat = Path(home) / CATALOG if home is not None else None
    if cat is not None and cat.exists():
        con = duckdb.connect(str(cat), read_only=True)
        try:
            rows = con.execute("SELECT view, db, parquet FROM _via_catalog WHERE tbl=? ORDER BY 1", [table]).fetchall()
        except Exception:
            rows = []
        finally:
            con.close()
        for view, db, pq in rows:
            if dbs and db not in dbs:
                continue
            found.append({"kind": "parquet", "path": str(cat), "rel": view, "ok": Path(pq).exists(),
                          "why": "" if Path(pq).exists() else "VIEW 底下的 parquet 不在"})
    return found


def _norm_codes(codes) -> tuple:
    if isinstance(codes, str):
        codes = re.split(r"[\s,;]+", codes)
    ok, bad = [], []
    for c in codes or []:
        c = str(c).strip()
        if not c:
            continue
        (ok if CODE_RX.match(c) else bad).append(c)
    return list(dict.fromkeys(ok)), bad


def _as_day(s: str):
    s = str(s or "")[:10]
    for fmt, n in (("%Y-%m-%d", 10), ("%Y-%m", 7), ("%Y", 4)):
        try:
            return datetime.strptime(s[:n], fmt).date()
        except ValueError:
            continue
    return None


def validate(req: dict) -> tuple:
    """Request contract → (clean request, problems). Anything that would reach SQL is checked here."""
    probs = []
    t = str(req.get("table") or "")
    if not TABLE_RX.match(t):
        probs.append(f"表名不合格:{t!r}")
    codes, bad = _norm_codes(req.get("codes"))
    if bad:
        probs.append("代號不合格:" + ", ".join(bad[:5]))
    for k in ("start", "end"):
        v = str(req.get(k) or "")
        if v and not WHEN_RX.match(v):
            probs.append(f"{k} 不是日期:{v!r}")
    cols = [c for c in (req.get("cols") or []) if c]
    if isinstance(req.get("cols"), str):
        cols = [c for c in re.split(r"[\s,]+", req["cols"]) if c]
    for c in cols:
        if not IDENT_RX.match(c):
            probs.append(f"欄名不合格:{c!r}")
    who = str(req.get("requester") or "VRN")
    if not REQ_RX.match(who):
        probs.append(f"requester 不合格:{who!r}")
    clean = {"requester": who, "table": t, "codes": codes, "start": str(req.get("start") or ""),
             "end": str(req.get("end") or ""), "cols": cols, "grace_days": int(req.get("grace_days") or 5)}
    return clean, probs


def _open(src: dict):
    duckdb = _duckdb()
    return duckdb.connect(src["path"], read_only=True)


def read(src: dict, req: dict, out: Path | None = None) -> dict:
    """Filter the table by codes / date range / columns; coverage per code; optional Parquet copy of the result."""
    con = _open(src)
    try:
        cols = [r[0] for r in con.execute(f"DESCRIBE {_q(src['rel'])}").fetchall()]
        low = {c.lower(): c for c in cols}
        ccol = next((low[c] for c in CODE_COLS if c in low), "")
        dcol = next((low[c] for c in DATE_COLS if c in low), "")
        want = [low[c.lower()] for c in req["cols"] if c.lower() in low]
        unknown = [c for c in req["cols"] if c.lower() not in low]
        pick = list(dict.fromkeys(([ccol] if ccol and want else []) + ([dcol] if dcol and want else []) + want)) or cols
        where = []
        if req["codes"] and ccol:
            where.append(f"CAST({_q(ccol)} AS VARCHAR) IN (" + ",".join(_lit(c) for c in req["codes"]) + ")")
        dv = f"CAST({_q(dcol)} AS VARCHAR)" if dcol else ""
        if req["start"] and dcol:
            where.append(f"{dv} >= LEFT({_lit(req['start'])}, LENGTH({dv}))")
        if req["end"] and dcol:
            where.append(f"{dv} <= {_lit(req['end'])}")
        sql = f"SELECT {', '.join(_q(c) for c in pick)} FROM {_q(src['rel'])}" + (" WHERE " + " AND ".join(where) if where else "")
        rows = con.execute(f"SELECT COUNT(*) FROM ({sql})").fetchone()[0]
        per = []
        if ccol and dcol:
            per = con.execute(f"SELECT CAST({_q(ccol)} AS VARCHAR), COUNT(*), MIN({dv}), MAX({dv}) FROM {_q(src['rel'])}"
                              + (" WHERE " + " AND ".join(where) if where else "") + " GROUP BY 1 ORDER BY 1").fetchall()
        elif dcol:
            per = [("*",) + tuple(con.execute(f"SELECT COUNT(*), MIN({dv}), MAX({dv}) FROM ({sql})").fetchone())]
        written = ""
        if out is not None and rows:
            out.parent.mkdir(parents=True, exist_ok=True)
            tmp = out.with_suffix(".parquet.part")
            con.execute(f"COPY ({sql}) TO {_lit(tmp.as_posix())} (FORMAT PARQUET, COMPRESSION ZSTD)")
            os.replace(tmp, out)
            written = str(out)
    finally:
        con.close()
    return {"source": src, "code_col": ccol, "date_col": dcol, "cols": pick, "unknown_cols": unknown, "rows": rows,
            "per_code": [{"code": c, "rows": n, "lo": lo, "hi": hi} for c, n, lo, hi in per], "parquet": written}


def coverage(res: dict, req: dict, today: date | None = None) -> dict:
    """Enough = rows exist, every requested code is present, and the newest date is within grace of the target."""
    today = today or date.today()
    target = _as_day(req["end"]) or today
    got = {p["code"]: p for p in res["per_code"]}
    missing = [c for c in req["codes"] if c not in got] if res["code_col"] else []
    stale = []
    for p in res["per_code"]:
        hi = _as_day(p["hi"])
        grace = req["grace_days"] if len(str(p["hi"] or "")) >= 10 else max(req["grace_days"], 62)
        if hi is None or (target - hi).days > grace:
            stale.append({"code": p["code"], "hi": p["hi"], "behind_days": (target - hi).days if hi else None})
    notes = []
    if req["codes"] and not res["code_col"]:
        notes.append("這張表認不出代號欄;代號條件沒套上")
    if (req["start"] or req["end"]) and not res["date_col"]:
        notes.append("這張表認不出日期欄;區間條件沒套上")
    if res["unknown_cols"]:
        notes.append("表上沒有的欄:" + ", ".join(res["unknown_cols"]))
    enough = res["rows"] > 0 and not missing and not stale
    return {"enough": enough, "missing": missing, "stale": stale, "target": str(target), "notes": notes}


# ───────────────────────── ④ hand off to VDF through EngineBus ─────────────────────────

def pick_item(route: dict, req: dict) -> dict | None:
    """First VDF item on the route that is not a write-verb item; one that can take the codes wins when codes are asked."""
    cands = [i for i in route["items"] if not i["write"]]
    if req["codes"]:
        takes = [i for i in cands if any(PARAM_MAP.get(p) == "codes" for p in i["params"])]
        cands = takes or cands
    return cands[0] if cands else None


def item_params(item: dict, req: dict) -> dict:
    """Only the parameters the item's own contract declares (spec params); nothing invented."""
    out = {}
    for p in item["params"]:
        k = PARAM_MAP.get(p)
        if k == "start" and req["start"]:
            out[p] = req["start"]
        elif k == "start_ym" and req["start"]:
            out[p] = req["start"][:7]
        elif k == "end" and req["end"]:
            out[p] = req["end"]
        elif k == "codes" and req["codes"]:
            out[p] = ",".join(req["codes"])
    return out


_CAT: dict = {}


def handoff(route: dict, req: dict, apply: bool = False, bus=None, timeout: int = DEFAULT_TIMEOUT) -> dict:
    item = pick_item(route, req)
    if item is None:
        return {"state": "ABSENT", "item": "", "why": "路由上沒有可代跑的 VDF 項(只有寫庫動詞項;要人指名點)"}
    params = item_params(item, req)
    base = {"item": item["id"], "zh": item["zh"], "params": params, "net": item["net"]}
    if item["net"] and os.environ.get("VIA_NET_CONSENT") != "YES":
        return {**base, "state": "GATED",
                "why": "同意閘未開(VIA_NET_CONSENT≠YES):需網路的 VDF 項不起子行程;要跑=操作員自己開閘,本支不代設"}
    bus = bus if bus is not None else mod("CGC_MDL148_EngineBus")
    if bus is None:
        return {**base, "state": "ABSENT", "why": "CGC_MDL148 EngineBus 尾版不在"}
    if bus is mod("CGC_MDL148_EngineBus"):              # the real bus: resolve its catalog once per process
        if "rows" not in _CAT:
            _CAT["rows"] = bus.catalog()
        r = bus.call(item["id"], params, timeout=timeout, apply=apply, catalog_rows=_CAT["rows"])
    else:
        r = bus.call(item["id"], params, timeout=timeout, apply=apply)
    return {**base, "state": r.get("state", "RED"), "rc": r.get("rc"), "argv": r.get("argv", []),
            "why": r.get("why", ""), "seconds": r.get("seconds", 0), "log": r.get("stdout_log", "")}


# ───────────────────────── ⑤ the request, end to end ─────────────────────────

def _rid(req: dict) -> str:
    key = json.dumps({k: req[k] for k in ("requester", "table", "codes", "start", "end", "cols")}, sort_keys=True)
    return datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + hashlib.sha1(key.encode()).hexdigest()[:8]


def _read_best(home, route: dict, req: dict, out: Path | None, explicit: bool = False, stores: list | None = None) -> tuple:
    tried = []
    for src in locate(home, req["table"], route["dbs"] if route else [], explicit, stores):
        if not src["ok"]:
            tried.append(src)
            continue
        try:
            return read(src, req, out), tried
        except Exception as exc:
            tried.append({**src, "ok": False, "why": f"讀不動:{type(exc).__name__}: {str(exc)[:80]}"})
    return None, tried


def request(req: dict, home=None, apply: bool = False, allow_handoff: bool = True, bus=None, outdir: Path | None = None,
            rts: list | None = None, today: date | None = None, write: bool = True) -> dict:
    outdir = Path(outdir or REPORTS)
    clean, probs = validate(req)
    t0 = datetime.now()
    res = {"engine": ENGINE, "ts": t0.strftime("%Y-%m-%d %H:%M:%S"), "request": clean, "state": "", "why": "",
           "route": None, "read": None, "coverage": None, "handoff": None, "parquet": "", "tried": []}
    if probs:
        res.update(state="RED", why="要料契約不合格:" + " · ".join(probs))
        return _ledger(res, outdir, write)
    if _duckdb() is None:
        res.update(state="ABSENT", why="duckdb 套件不在(本境缺件;不裝套件)")
        return _ledger(res, outdir, write)
    route = next((r for r in (rts if rts is not None else routes()) if r["table"] == clean["table"]), None)
    if route is None:
        res.update(state="ABSENT", why=f"兩本冊上都沒有產 {clean['table']} 的 VDF 項(零發明:不猜)")
        return _ledger(res, outdir, write)
    res["route"] = {"dbs": route["dbs"], "items": [i["id"] for i in route["items"]]}
    explicit = bool(home)
    home, why_home = (Path(home), "--home") if home else data_home(None)
    rid = _rid(clean)
    out = outdir / "out" / clean["requester"] / f"{clean['table']}_{rid}.parquet" if write else None
    got, tried = _read_best(home, route, clean, None, explicit)
    res["tried"] = tried
    cov = coverage(got, clean, today) if got else None
    if got and cov["enough"]:
        got, _ = _read_best(home, route, clean, out, explicit)
        res.update(state="AMBER" if cov["notes"] else "GREEN", read=_slim(got), coverage=cov, parquet=got["parquet"],
                   why=f"庫裡夠:{got['rows']} 列 · 來源 {got['source']['kind']}" + ("(" + ";".join(cov["notes"]) + ")" if cov["notes"] else ""))
        return _ledger(res, outdir, write, rid)
    res.update(read=_slim(got) if got else None, coverage=cov)
    short = "庫裡沒有這張表" if not got else ("缺代號 " + ",".join(cov["missing"][:6]) if cov["missing"] else
                                                ("最新日落後 " + ",".join(s["code"] for s in cov["stale"][:6]) if cov["stale"] else "0 列"))
    if home is None and not got:
        short += f"(資料家不可用:{why_home})"
    if not allow_handoff:
        res.update(state="NODATA" if not got or not got["rows"] else "AMBER", why=short + " · 未轉交(--no-handoff)")
        if got and got["rows"] and write:
            res["parquet"] = _read_best(home, route, clean, out, explicit)[0]["parquet"]
        return _ledger(res, outdir, write, rid)
    h = handoff(route, clean, apply=apply, bus=bus)
    res["handoff"] = h
    if h["state"] == "GREEN" and apply:
        again, tried2 = _read_best(home, route, clean, out, explicit)
        cov2 = coverage(again, clean, today) if again else None
        res.update(read=_slim(again) if again else None, coverage=cov2, tried=tried + tried2,
                   parquet=(again or {}).get("parquet", ""))
        if again and cov2["enough"]:
            res.update(state="GREEN", why=f"{short} → 轉交 VDF {h['item']} 綠 → 重讀夠了({again['rows']} 列)")
        else:
            res.update(state="AMBER" if again and again["rows"] else "NODATA",
                       why=f"{short} → 轉交 VDF {h['item']} 綠,但重讀仍不夠(上游沒料或冊宣告不實,照實報)")
        return _ledger(res, outdir, write, rid)
    res.update(state=h["state"], why=f"{short} → 轉交 VDF {h.get('item') or '—'}:{h['state']}"
               + (f"({h['why'][:120]})" if h.get("why") else ""))
    if got and got["rows"] and write:                      # hand back what exists, clearly marked as not enough
        res["parquet"] = _read_best(home, route, clean, out, explicit)[0]["parquet"]
    return _ledger(res, outdir, write, rid)


def _slim(r: dict | None) -> dict | None:
    if r is None:
        return None
    return {"source": r["source"]["kind"] + ":" + Path(r["source"]["path"]).name + "::" + r["source"]["rel"],
            "code_col": r["code_col"], "date_col": r["date_col"], "cols": r["cols"], "rows": r["rows"],
            "codes": len(r["per_code"]), "per_code": r["per_code"][:50]}


def _ledger(res: dict, outdir: Path, write: bool, rid: str = "") -> dict:
    res["id"] = rid or _rid({**res["request"], "codes": res["request"].get("codes") or [], "cols": res["request"].get("cols") or []})
    if not write:
        return res
    outdir.mkdir(parents=True, exist_ok=True)
    line = {k: res[k] for k in ("id", "ts", "state", "why", "parquet")}
    line.update(requester=res["request"]["requester"], table=res["request"]["table"],
                codes=len(res["request"]["codes"]), rows=(res["read"] or {}).get("rows", 0),
                handoff=(res["handoff"] or {}).get("item", ""), handoff_state=(res["handoff"] or {}).get("state", ""))
    with (outdir / "LEDGER.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")
    (outdir / "BROKER_latest.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return res


def fetch(table: str, codes=None, start: str = "", end: str = "", cols=None, requester: str = "VRN", apply: bool = False,
          home=None, handoff: bool = True) -> dict:
    """The VRN-side call: one line in a VRN engine instead of opening a VDF store directly.
    Returns the request record; `parquet` is the result file (empty when nothing could be read)."""
    return request({"table": table, "codes": codes or [], "start": start, "end": end, "cols": cols or [],
                    "requester": requester}, home=home, apply=apply, allow_handoff=handoff)


def fetch_rows(rec: dict) -> tuple:
    """(columns, rows) from a fetch() record's Parquet; ([], []) when there is none."""
    duckdb = _duckdb()
    pq = rec.get("parquet") or ""
    if duckdb is None or not pq or not Path(pq).exists():
        return [], []
    con = duckdb.connect()
    try:
        cur = con.execute(f"SELECT * FROM read_parquet({_lit(Path(pq).as_posix())})")
        return [d[0] for d in cur.description], cur.fetchall()
    finally:
        con.close()


# ───────────────────────── VCGC → VDF build plan · bypass lamp · status ─────────────────────────

def build(home=None, apply: bool = False, bus=None, rts: list | None = None, today: date | None = None) -> dict:
    """Every table the table book calls a primary store (role 正庫…): present and fresh? The missing ones get a VDF item."""
    rts = rts if rts is not None else routes()
    explicit = bool(home)
    home = Path(home) if home else data_home(None)[0]
    stores = _stores(home, explicit)                     # scan once per build, not once per table
    rows, planned = [], {}
    for r in rts:
        if not r["in_ssot"] or not str(r["role"]).startswith("正庫"):
            continue
        req = validate({"table": r["table"], "requester": "VCGC_BUILD"})[0]
        got, _ = _read_best(home, r, req, None, explicit, stores) if _duckdb() else (None, [])
        cov = coverage(got, req, today) if got else None
        if got and got["rows"] >= max(1, r["min_rows"]) and cov["enough"]:
            rows.append({"table": r["table"], "state": "GREEN", "rows": got["rows"], "item": "", "why": "在且新"})
            continue
        item = pick_item(r, req)
        if item is None:
            rows.append({"table": r["table"], "state": "ABSENT", "rows": 0, "item": "", "why": "只有寫庫動詞項(要人指名點)"})
            continue
        if item["id"] in planned:
            rows.append({"table": r["table"], "state": planned[item["id"]], "rows": (got or {}).get("rows", 0), "item": item["id"],
                         "why": f"同一項已排(一項產多表;該項 {planned[item['id']]})"})
            continue
        h = handoff(r, req, apply=apply, bus=bus)
        planned[item["id"]] = h["state"]
        rows.append({"table": r["table"], "state": h["state"], "rows": (got or {}).get("rows", 0), "item": item["id"],
                     "why": ("不在" if not got else "舊了/不足") + " → " + h["state"] + (":" + h["why"][:100] if h.get("why") else "")})
    if apply and any(v == "GREEN" for v in planned.values()):
        stores = _stores(home, explicit)                 # a VDF item may have created a new store: scan again
        for x in rows:
            if x["state"] != "GREEN" or not x["item"]:
                continue
            r = next(z for z in rts if z["table"] == x["table"])
            req = validate({"table": r["table"], "requester": "VCGC_BUILD"})[0]
            got, _ = _read_best(home, r, req, None, explicit, stores)
            cov = coverage(got, req, today) if got else None
            if got and got["rows"] >= max(1, r["min_rows"]) and cov["enough"]:
                x.update(rows=got["rows"], why=x["why"] + f" → 重量:在且新({got['rows']} 列)")
            else:                                        # rc 0 is not the table: an engine can print SKIP and exit 0
                x.update(state="NODATA", rows=(got or {}).get("rows", 0),
                         why=x["why"] + " → 重量:VDF 項回綠但表仍" + ("舊" if got else "不在") + "(看站紀錄;引擎可能自述 SKIP)")
    tally = {}
    for x in rows:
        tally[x["state"]] = tally.get(x["state"], 0) + 1
    return {"engine": ENGINE, "home": str(home) if home else "", "apply": apply, "rows": rows, "tally": tally}


STORE_RX_DEFAULT = ("ActiveTWETF.duckdb", "aaii_sentiment.duckdb", "vdf_global_market.duckdb", "vdf_hub.duckdb",
                    "vdf_tw_market.duckdb")


def bypass(vrn_dir: Path | None = None, stores: list | None = None, tables: list | None = None) -> dict:
    """VRN tail versions that open a VDF store directly AND read a VDF-produced (routed) table — that read should go
    through fetch(). Tails that only keep their own tables in the same store are listed apart (not a bypass)."""
    vrn_dir = Path(vrn_dir or VRN_DIR)
    if stores is None:
        ssot = _json(_newest(HERE, DBSSOT_GLOB)) or {}
        stores = sorted({r.get("db", "") for r in ssot.get("tables") or [] if r.get("db")}) or list(STORE_RX_DEFAULT)
    tables = tables if tables is not None else [r["table"] for r in routes()]
    rx = re.compile("|".join(re.escape(s) for s in stores))
    trx = re.compile(r"(?i)\b(?:FROM|JOIN)\s+\"?(" + "|".join(re.escape(t) for t in sorted(tables, key=len, reverse=True))
                     + r")\b") if tables else None
    tails: dict = {}
    for p in vrn_dir.rglob("*.py"):
        stem = re.sub(r"_v\d+$", "", p.stem)
        key = (str(p.parent), stem)
        if key not in tails or _vnum(p) > _vnum(tails[key]):
            tails[key] = p
    direct, brokered, own = [], [], []
    for p in sorted(tails.values()):
        try:
            txt = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "CGC_MDL239_DataBroker" in txt:
            brokered.append(p.name)
            continue
        if "duckdb.connect" not in txt or not rx.search(txt):
            continue
        reads = sorted(set(trx.findall(txt))) if trx else []
        (direct if reads else own).append({"file": p.name, "stores": sorted(set(rx.findall(txt))), "reads": reads})
    state = "GREEN" if not direct else "AMBER"
    return {"state": state, "direct": direct, "brokered": brokered, "own_tables": own, "tails": len(tails),
            "why": (f"VRN 尾版直讀 VDF 表 {len(direct)} 支(舊版不動;換版時改用 fetch())· 經中介 {len(brokered)} 支"
                    f" · 只存自己的表 {len(own)} 支(不算繞道)")}


def status() -> dict:
    rts = routes()
    led = REPORTS / "LEDGER.jsonl"
    last = []
    if led.exists():
        last = [json.loads(x) for x in led.read_text(encoding="utf-8").splitlines()[-200:] if x.strip()]
    tally = {}
    for x in last:
        tally[x["state"]] = tally.get(x["state"], 0) + 1
    bp = bypass()
    return {"engine": ENGINE, "routes": len(rts), "routed_tables": [r["table"] for r in rts],
            "unrouted": unrouted(rts=rts), "ledger_recent": tally, "bypass": {k: bp[k] for k in ("state", "why")},
            "bypass_direct": [d["file"] for d in bp["direct"]], "duckdb": _duckdb() is not None}


# ───────────────────────── CLI · selftest ─────────────────────────

def _arg(args, name, default=""):
    if name in args:
        i = args.index(name)
        return args[i + 1] if i + 1 < len(args) else default
    for a in args:
        if a.startswith(name + "="):
            return a.split("=", 1)[1]
    return default


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        return selftest()
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    verb = args[0] if args else "status"
    home = _arg(args, "--home") or None
    if verb == "routes":
        rts = routes()
        for r in rts:
            print(f"  {r['table']:<28} {','.join(r['dbs']) or '—':<34} ← " + " · ".join(
                i["id"] + ("(net)" if i["net"] else "") + ("(寫庫)" if i["write"] else "") for i in r["items"]))
        print(f"  [計] 路由 {len(rts)} 張表 · 表冊有而無路由 {len(unrouted(rts=rts))} 張")
        return 0
    if verb == "status":
        print(json.dumps(status(), ensure_ascii=False, indent=1))
        return 0
    if verb == "bypass":
        r = bypass()
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0
    if verb == "build":
        r = build(home, apply="--apply" in args)
        for x in r["rows"]:
            print(f"  {x['state']:<7} {x['table']:<28} {x['item'] or '—':<22} {x['why']}")
        print(f"  [計] " + " · ".join(f"{k} {v}" for k, v in sorted(r["tally"].items())) + f" · 家 {r['home'] or '—'}")
        return 0 if all(x["state"] in ("GREEN", "PLAN") for x in r["rows"]) else 2
    if verb == "request":
        r = request({"table": _arg(args, "--table"), "codes": _arg(args, "--codes"), "start": _arg(args, "--start"),
                     "end": _arg(args, "--end"), "cols": _arg(args, "--cols"), "requester": _arg(args, "--requester", "VRN"),
                     "grace_days": _arg(args, "--grace-days", "5")},
                    home=home, apply="--apply" in args, allow_handoff="--no-handoff" not in args)
        print(json.dumps(r, ensure_ascii=False, indent=1, default=str))
        return {"GREEN": 0, "PLAN": 0, "NODATA": 2, "AMBER": 2, "GATED": 2, "ABSENT": 2}.get(r["state"], 1)
    print("用法:routes | status | bypass | build [--apply] | request --table T [--codes …] [--start …] [--apply] | --selftest")
    return 2


def selftest() -> int:
    import tempfile
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {ENGINE} · 自測(零網路;夾具家,不碰真庫)===")
    rts = routes()
    by = {r["table"]: r for r in rts}
    tp = by.get("tw_daily_prices", {})
    chk("① 路由只從兩本冊推:tw_daily_prices → vdf_tw_market · tw_prices_inc / tw_history",
        "vdf_tw_market" in tp.get("dbs", []) and {"tw_prices_inc", "tw_history"} <= {i["id"] for i in tp.get("items", [])},
        f"{len(rts)} 張表")
    hd = by.get("holdings_daily", {})
    chk("② `庫.duckdb::表` 宣告也認:holdings_daily → ActiveTWETF · etf_holdings_daily",
        "ActiveTWETF" in hd.get("dbs", []) and any(i["id"] == "etf_holdings_daily" for i in hd.get("items", [])))
    chk("③ 報告檔 / parquet 路徑不當表(零發明)", not any("/" in r["table"] or "." in r["table"] for r in rts))
    duckdb = _duckdb()
    if duckdb is None:
        print("  [SKIP] ④–⑬ duckdb 不在(缺件,非本引擎缺陷)")
        ok = all(results)
        print(f"  [計] {len(results)} 檢 OK {sum(results)} · FAIL {len(results) - sum(results)} · SKIP 1")
        return 0 if ok else 1
    today = date(2026, 9, 28)
    with tempfile.TemporaryDirectory() as td:
        home, outdir = Path(td) / "home", Path(td) / "reports"
        home.mkdir()
        db = home / "vdf_tw_market.duckdb"
        con = duckdb.connect(str(db))
        con.execute("CREATE TABLE tw_daily_prices(date VARCHAR, ticker VARCHAR, close DOUBLE, volume BIGINT)")
        for tk in ("2330", "2317"):
            con.execute("INSERT INTO tw_daily_prices SELECT CAST(DATE '2026-06-01' + CAST(i AS INTEGER) AS VARCHAR), ?, 100 + i, 1000 "
                        "FROM range(0, 119) t(i)", [tk])                      # last day 2026-09-27
        con.execute("CREATE TABLE tw_chip_derived(date DATE, ticker VARCHAR, score DOUBLE)")
        con.execute("INSERT INTO tw_chip_derived VALUES (DATE '2026-08-01', '2330', 1.0)")
        con.close()
        sha = hashlib.sha256(db.read_bytes()).hexdigest()
        r = request({"table": "tw_daily_prices", "codes": "2330", "start": "2026-09-01", "cols": "close",
                     "requester": "VRN_ENG068"}, home=home, outdir=outdir, rts=rts, today=today)
        n_back = duckdb.connect().execute(f"SELECT COUNT(*), COUNT(DISTINCT ticker) FROM read_parquet({_lit(r['parquet'])})").fetchone() \
            if r["parquet"] else (0, 0)
        chk("④ 庫裡夠 → GREEN;代號 · 起日 · 欄都套上,結果回成 Parquet", r["state"] == "GREEN" and n_back == (27, 1)
            and r["read"]["cols"] == ["ticker", "date", "close"], f"{r['state']} · 讀回 {n_back}")
        chk("⑤ 來源庫只開 read_only:一個位元不動", hashlib.sha256(db.read_bytes()).hexdigest() == sha)
        ra = request({"table": "tw_daily_prices", "codes": "2330", "cols": "close,nope", "requester": "VRN_X"}, home=home,
                     outdir=outdir, rts=rts, today=today, write=False)
        chk("⑤b 要了表上沒有的欄 → AMBER 並寫明(不假綠)", ra["state"] == "AMBER" and "nope" in ra["why"], ra["why"][:80])
        r2 = request({"table": "tw_daily_prices", "codes": "2330,2454", "requester": "VRN_ENG068"}, home=home, outdir=outdir,
                     rts=rts, today=today)
        h2 = r2["handoff"] or {}
        chk("⑥ 缺代號 → 轉交 VDF;需網路項在閘未開時 = GATED(或閘開時乾跑 PLAN),不起子行程",
            r2["coverage"]["missing"] == ["2454"] and h2.get("item") in ("tw_prices_inc", "tw_history")
            and r2["state"] in ("GATED", "PLAN"), f"{r2['state']} · {h2.get('item')} · 參數 {h2.get('params')}")

        class FakeBus:
            calls = []

            def call(self, item_id, params, timeout=0, apply=False):
                self.calls.append((item_id, params, apply))
                if apply:
                    c = duckdb.connect(str(db))
                    c.execute("INSERT INTO tw_chip_derived VALUES (DATE '2026-09-26', '2330', 2.0)")
                    c.close()
                return {"state": "GREEN" if apply else "PLAN", "rc": 0 if apply else None, "argv": ["fake", item_id], "why": ""}

        fb = FakeBus()
        r3 = request({"table": "tw_chip_derived", "codes": "2330", "requester": "VRN_ENG067"}, home=home, outdir=outdir, rts=rts,
                     today=today, bus=fb)
        chk("⑦ 預設乾跑:舊料 → 轉交 PLAN(EngineBus apply=False,不動手)", r3["state"] == "PLAN" and fb.calls[-1][2] is False,
            f"{r3['state']} · {fb.calls[-1] if fb.calls else '—'}")
        r4 = request({"table": "tw_chip_derived", "codes": "2330", "requester": "VRN_ENG067"}, home=home, outdir=outdir, rts=rts,
                     today=today, bus=fb, apply=True)
        chk("⑧ --apply:VDF 項回綠 → 經 VCGC 重讀 → 夠了 GREEN,結果 Parquet 回 VRN",
            r4["state"] == "GREEN" and r4["read"]["rows"] == 2 and Path(r4["parquet"]).exists(), r4["why"][:90])
        r5 = request({"table": "no_such_table", "requester": "VRN_X"}, home=home, outdir=outdir, rts=rts, today=today)
        chk("⑨ 冊上沒有路由的表 = ABSENT(不猜引擎)", r5["state"] == "ABSENT")
        r6 = request({"table": "tw_daily_prices", "codes": "2330');DROP TABLE x;--", "requester": "VRN_X"}, home=home,
                     outdir=outdir, rts=rts, today=today)
        chk("⑩ 契約把關:不合格代號進不了 SQL(RED,不執行)", r6["state"] == "RED" and "代號不合格" in r6["why"])
        oc = mod("CGC_MDL238_OperatorConsole")
        cat_ok = False
        if oc is not None:
            home2 = Path(td) / "home2"
            home2.mkdir()
            (home2 / "vdf_tw_market.duckdb").write_bytes(db.read_bytes())
            oc.parquet_apply(home2, oc.parquet_plan(home2))
            (home2 / "vdf_tw_market.duckdb").unlink()
            r7 = request({"table": "tw_daily_prices", "codes": "2317", "start": "2026-09-20", "requester": "VRN_X"}, home=home2,
                         outdir=outdir, rts=rts, today=today)
            cat_ok = r7["state"] == "GREEN" and r7["read"]["source"].startswith("parquet:") and r7["read"]["rows"] == 8
        chk("⑪ 來源庫不在 → 讀 Parquet 目錄 VIEW(同一個操作台目錄)", cat_ok)
        led = [json.loads(x) for x in (outdir / "LEDGER.jsonl").read_text(encoding="utf-8").splitlines()]
        chk("⑫ 每筆要料記一行帳本 + BROKER_latest.json", len(led) == 7 and (outdir / "BROKER_latest.json").exists(),
            f"{len(led)} 行 · " + ",".join(x["state"] for x in led))
        vr = Path(td) / "VRN"
        vr.mkdir()
        (vr / "VRN_ENG900_A_v0100.py").write_text("import duckdb\nduckdb.connect('vdf_tw_market.duckdb')\n", encoding="utf-8")
        (vr / "VRN_ENG900_A_v0101.py").write_text("# uses CGC_MDL239_DataBroker fetch()\n", encoding="utf-8")
        (vr / "VRN_ENG901_B_v0100.py").write_text("import duckdb\ncon = duckdb.connect(str(HOME / 'ActiveTWETF.duckdb'))\n"
                                                   "con.execute('SELECT * FROM holdings_daily')\n",
                                                   encoding="utf-8")
        (vr / "VRN_ENG902_C_v0100.py").write_text("import duckdb\ncon = duckdb.connect('vdf_tw_market.duckdb')\n"
                                                   "con.execute('CREATE TABLE vrn_report_x(a INT)')\n", encoding="utf-8")
        bp = bypass(vr, list(STORE_RX_DEFAULT), ["holdings_daily", "tw_daily_prices"])
        chk("⑬ 繞道燈只看尾版、只算讀 VDF 表:A 已換用中介 · B 直讀 holdings_daily · C 只存自己的表 → 直讀 1 · AMBER",
            bp["state"] == "AMBER" and [d["file"] for d in bp["direct"]] == ["VRN_ENG901_B_v0100.py"] and len(bp["brokered"]) == 1
            and [d["file"] for d in bp["own_tables"]] == ["VRN_ENG902_C_v0100.py"], bp["why"])
        b = build(home, rts=rts, today=today, bus=fb)
        st = {x["table"]: x["state"] for x in b["rows"]}
        chk("⑭ VCGC→VDF 建庫計畫:正庫表逐張量,在且新 = GREEN,缺的排 VDF 項(預設乾跑)",
            st.get("tw_daily_prices") == "GREEN" and all(v in ("GREEN", "PLAN", "GATED", "ABSENT") for v in st.values()),
            " · ".join(f"{k} {v}" for k, v in sorted(b["tally"].items())))
        class LazyBus:
            def call(self, item_id, params, timeout=0, apply=False):
                return {"state": "GREEN" if apply else "PLAN", "rc": 0, "argv": [], "why": ""}

        b2 = build(home, apply=True, rts=[r for r in rts if r["table"] in ("tw_chip_derived", "etf_revenue_momentum")],
                   today=today, bus=LazyBus())
        st2 = {x["table"]: x["state"] for x in b2["rows"]}
        chk("⑮ 建庫 --apply 後重量:rc 0 不等於表在(引擎自述 SKIP 也回 0)→ 表仍缺 = NODATA,不記綠",
            st2.get("etf_revenue_momentum", "NODATA") == "NODATA" and all(v in ("GREEN", "NODATA") for v in st2.values()),
            " · ".join(f"{k} {v}" for k, v in sorted(st2.items())))
    keep = os.environ.pop("VIA_FROM_VCGC", None)
    try:
        chk("⑯ CLI 不經 VCGC 就拒跑", main(["status"]) == 2)
    finally:
        if keep is not None:
            os.environ["VIA_FROM_VCGC"] = keep
    ok = all(results)
    print(f"  [計] {len(results)} 檢 OK {sum(results)} · FAIL {len(results) - sum(results)}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
