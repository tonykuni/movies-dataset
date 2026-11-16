#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_MDL020_DataPlane v0100 — VDF 資料平面:管理範圍總表 · 清單輸入閘 · 資料家 parquet 增量庫 · 不重複擷取計畫 · 增量匯出(PC / 雲端同步夾 / MCP 清單)

操作員 2026-11-15:「用 VCGC 節省工具啟動 將每個系統 SYSTEM MANAGER 該控管的項目範圍 VDF SYSTEM MANAGER 都要有 輸出 PARQUET 增量資料庫
可出到各類雲端硬碟 MCP TO THEM AND PC FILE · VDF 重點在於輸入輸出多且複雜 結果也需要整合 · 台股及主動式台股 ETF 清單也要被驗證有效作為輸入 ·
輸出 PARQUET 增量維護資料庫不重複擷取 ·(資料家 C:\Users\tonyk\OneDrive\Documents\VeritasIntelligenceAnalytics\via_database\vdf_database
底下 tw__*.parquet / gl__*.parquet 21 檔 · output_hub · temp)· 整理清簡優化再輸出更新快速」。

一支五個動詞(VDF 自己的模組;由 VDF_SystemManager 轉來,也可直接跑):
  scope                 管理範圍總表:輸入清單 → 擷取 → DuckDB 正典庫 → parquet 增量庫 → 匯出 → 整合,每項一燈 + 證據 + 下一步指令;寫一頁 U/I。
  inputs                清單輸入閘:台股清單(MDL009)· 主動式台股 ETF 清單(MDL010)· 合格判定(VDF-REQ026)獨立重驗 —— 有紅就不該拿去擷取。
  parquet status        資料家 <tw|gl>__<表>.parquet(ENG065 檔名協定)逐檔:列 · 欄 · 鍵 · 重複鍵 · 日期範圍 · 頻率 · 落後;來源正典庫同表對列。
  parquet sync          正典 DuckDB(vdf_tw_market → tw__ · vdf_global_market → gl__)→ parquet:只寫來源有、parquet 沒有的鍵;
                        沒有新鍵 = 不動檔(雲端不重傳);有新鍵 = 暫存夾寫新檔 → 驗列數 / 重複鍵 → 原子替換。另寫清單與 DuckDB 目錄(每檔一個 VIEW)。
  parquet plan          不重複擷取:每表比「該到的日期」—— 正典庫已有 → 只要 sync(不重抓);正典庫也沒有 → 才列寫入引擎去擷取。
  parquet export --to   增量匯出:<夾> | onedrive | gdrive | dropbox(同步夾 = 雲端硬碟);只複製 sha256 變了的檔;寫目的地清單 +
                        MCP 交接清單(VDF_PARQUET_MCP_HANDOFF.json:哪些檔要上傳 · sha256 · 大小 · 表 · 日期範圍 —— 給 MCP 雲端硬碟工具照單上傳後比 sha)。

鍵律(同一份,status / sync / plan 共用):① 來源表宣告的 PRIMARY KEY / UNIQUE ② ENG064 / ENG065 協定:date + ticker(+ kind)
③ 內容鍵:全部欄扣掉擷取時間類欄(fetched_at 等)—— 重抓同一筆只因時間戳不同,不算新列。鍵比對一律轉字串且 NULL 視為相等。
資料家:--home > env VIA_VDF_DB_HOME > VDF_DataHome_SSOT 尾版冊上第一個在這台機器存在的 db_home;都沒有 = 照實 GRAY,不寫任何檔。
寫入動詞(sync / export)要 VDF System Manager 入口旗標(VIA_FROM_VDFSM=YES)或 VCGC(VIA_FROM_VCGC=YES)。
DuckDB 正典庫一律唯讀開;被引擎鎖住 = 照實記、這輪跳過。零網路 · 不碰 TA-Lib · 不讀寫同意閘 · 不刪使用者的檔(只原子替換本模組管的 parquet)。
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

import csv
import hashlib
import html
import json
import os
import re
import shutil
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent                 # functional modules/VDF
VIA = HERE.parent.parent                               # VeritasIntelligenceAnalytics
TAG = "VDF_MDL020_DataPlane v" + Path(__file__).stem.rsplit("_v", 1)[-1]
OUT_REL = Path("VIA_Reports") / "vdf"
PROTO = {"vdf_tw_market.duckdb": "tw", "vdf_global_market.duckdb": "gl"}      # ENG065 檔名協定(批389;ENG079 PROTOCOL_RX 同一條)
PROTO_RX = re.compile(r"^(tw|gl)__(.+)\.parquet$")
VOLATILE = {"fetched_at", "fetch_ts", "ingested_at", "ingest_ts", "_ingest_ts", "updated_at", "created_at", "inserted_at",
            "loaded_at", "run_id", "_run_id", "batch_id", "source_file", "_src_file", "_src"}
DATE_CANDS = ("date", "trade_date", "data_date", "as_of", "asof", "snapshot_date", "report_date", "period", "ym", "month", "dt", "日期")
SKIP_DIRS = ("_repo_", "stash", "selftest", "backup", "VIA_spill", "__pycache__")
MANIFEST, MCP_NAME, CATALOG = "VDF_PARQUET_MANIFEST.json", "VDF_PARQUET_MCP_HANDOFF.json", "VDF_ParquetDB.duckdb"
MCP_DONE = "VDF_PARQUET_MCP_DONE.json"          # MCP 端上傳完寫回 {檔: sha256};下次匯出這些檔就不再列待上傳
SPEC_GLOB = "VDF_UI_VisualSpec_SSOT_v*.json"
LAMP_RANK = {"RED": 4, "YELLOW": 3, "GRAY": 2, "GREEN": 1, "INFO": 0, "SKIP": 0}
WRITE_VERBS = ("sync", "export")
PARAMS_GLOB = "VDF_DataPlane_SSOT_v*.json"           # 本模組的輸入輸出參數冊(VDF 自己留存;操作員 2026-11-15「輸入輸出參數各自子系統留存」)
# 代碼律不在本支另寫:讀共用的那一份(AST 讀字面,不執行原檔)—— 台股 = MDL009 的 SSOT_STOCK_RX(MDL001 鎖定律)· 主動式 ETF = ENG077 的 A_CODE
SHARED_RX = {"stock": ("VDF_MDL009_TWStockList_v*.py", "SSOT_STOCK_RX", r"^(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})$"),
             "etf": ("engine/VDF_ENG077_ActiveETFUniverse_v*.py", "A_CODE", r"^\d{5}A$")}


def _vn(p: Path) -> int:
    m = re.search(r"_v(\d{4})", p.stem)
    return int(m.group(1)) if m else -1


def shared_rx(kind: str, here: Path = HERE) -> tuple:
    """共用代碼律:從原定義檔(版號由高到低,第一支字面定義它的)用 AST 讀出 re.compile 的字串;都讀不到 = 同文後備(照實標來源)。"""
    import ast
    glob, name, fallback = SHARED_RX[kind]
    for f in sorted(here.glob(glob), key=_vn, reverse=True):
        try:
            tree = ast.parse(f.read_text(encoding="utf-8", errors="replace"))
        except (OSError, SyntaxError):
            continue
        for node in tree.body:
            if (isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets)
                    and isinstance(node.value, ast.Call) and node.value.args and isinstance(node.value.args[0], ast.Constant)):
                return re.compile(node.value.args[0].value), "%s · %s" % (f.name, name)
    return re.compile(fallback), "後備(同文 · %s 讀不到)" % name


DEFAULT_PARAMS = {"protocol": dict(PROTO), "volatile_columns": sorted(VOLATILE), "date_candidates": list(DATE_CANDS),
                  "list_fresh_days": {"green": 7, "yellow": 30}, "manifest": MANIFEST, "mcp_handoff": MCP_NAME, "catalog": CATALOG}


def load_params(here: Path = HERE) -> tuple:
    """VDF 自己的參數冊尾版;不在 / 讀壞 = 內建預設(同值),照實回來源。"""
    book = _tail(here, PARAMS_GLOB)
    if not book:
        return dict(DEFAULT_PARAMS), "內建預設(%s 不在)" % PARAMS_GLOB
    try:
        d = json.loads(book.read_text(encoding="utf-8"))
        return {**DEFAULT_PARAMS, **(d.get("params") or {})}, book.name
    except (OSError, ValueError) as exc:
        return dict(DEFAULT_PARAMS), "內建預設(%s 讀不了:%s)" % (book.name, exc)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def worst(lamps) -> str:
    ls = [x for x in lamps if x]
    return max(ls, key=lambda x: LAMP_RANK.get(x, 0)) if ls else "GRAY"


def entry_ok() -> bool:
    return os.environ.get("VIA_FROM_VDFSM") == "YES" or os.environ.get("VIA_FROM_VCGC") == "YES"


def _duck():
    import duckdb
    return duckdb


def _q(name: str) -> str:
    return '"%s"' % str(name).replace('"', '""')


def _lit(p) -> str:
    return "'%s'" % str(Path(p).as_posix() if isinstance(p, Path) else p).replace("'", "''")


def _tail(folder: Path, glob: str) -> Path | None:
    def vn(p):
        m = re.search(r"_v(\d{4})", p.stem)
        return int(m.group(1)) if m else -1
    hits = [p for p in folder.glob(glob) if vn(p) >= 0]
    return max(hits, key=vn) if hits else None


# ---------------------------------------------------------------- 資料家
def resolve_home(home=None, env=None) -> tuple:
    """--home > env VIA_VDF_DB_HOME > VDF_DataHome_SSOT 尾版冊上第一個存在的 db_home。→ (Path | None, 為什麼)"""
    env = os.environ if env is None else env
    if home:
        return (Path(home), "--home 指定") if Path(home).is_dir() else (None, "--home %s 不在" % home)
    if env.get("VIA_VDF_DB_HOME"):
        p = Path(env["VIA_VDF_DB_HOME"])
        return (p, "env VIA_VDF_DB_HOME") if p.is_dir() else (None, "env VIA_VDF_DB_HOME=%s 不在" % p)
    book = _tail(HERE, "VDF_DataHome_SSOT_v*.json")
    if book:
        try:
            for h in json.loads(book.read_text(encoding="utf-8")).get("homes") or []:
                if h.get("db_home") and Path(h["db_home"]).is_dir():
                    return Path(h["db_home"]), "%s · %s" % (book.name, h.get("id"))
        except (OSError, ValueError) as exc:
            return None, "資料家冊讀不了:%s" % exc
    return None, "沒有資料家(給 --home 或設 VIA_VDF_DB_HOME;冊上的 db_home 這台機器都沒有)"


def find_dbs(home: Path) -> dict:
    """家底下的正典庫(vdf_tw_market / vdf_global_market):路徑有 mega 的優先,再比大小;略過備份 / 自測 / 暫存。"""
    out = {}
    for name in PROTO:
        cands = []
        for pat in (name, "*/" + name, "*/*/" + name, "*/*/*/" + name):
            for p in home.glob(pat):
                if not any(x in p.parts for x in SKIP_DIRS) and "temp" not in [s.lower() for s in p.relative_to(home).parts[:-1]]:
                    cands.append(p)
        if cands:
            out[name] = sorted(set(cands), key=lambda p: ("mega" not in p.parts, -p.stat().st_size))[0]
    return out


# ---------------------------------------------------------------- 鍵律 · 日期
def pick_key(cols: list, declared: list | None = None) -> tuple:
    """① 宣告的主鍵 ② ENG064 / ENG065 協定 date + ticker(+ kind)③ 內容鍵(扣擷取時間類欄)。→ (鍵欄, 律名)"""
    low = {c.lower(): c for c in cols}
    if declared and all(k in cols for k in declared):
        return list(declared), "宣告主鍵"
    if "date" in low and "ticker" in low:
        return [low["date"], low["ticker"]] + ([low["kind"]] if "kind" in low else []), "協定 date+ticker"
    keys = [c for c in cols if c.lower() not in VOLATILE]
    return (keys or list(cols)), "內容鍵(扣 %d 個擷取時間欄)" % (len(cols) - len(keys)) if keys and len(keys) < len(cols) else "內容鍵(整列)"


def date_col(cols: list) -> str | None:
    low = {c.lower(): c for c in cols}
    return next((low[c] for c in DATE_CANDS if c in low), None)


def norm_day(v) -> str | None:
    """日期值 → 'YYYY-MM-DD'(YYYYMMDD · YYYY-MM-DD · YYYYMM / YYYY-MM 取月初 · DATE / TIMESTAMP);1990 前當哨兵不算。"""
    if v is None:
        return None
    s = str(v).strip()
    m = re.match(r"^(\d{4})-?(\d{2})-?(\d{2})", s)
    if m:
        d = "%s-%s-%s" % m.groups()
    else:
        m = re.match(r"^(\d{4})-?(\d{2})$", s)
        if not m:
            return None
        d = "%s-%s-01" % m.groups()
    return d if d >= "1990-01-01" else None


def cadence(dmin: str | None, dmax: str | None, ndates: int | None) -> str:
    if not dmin or not dmax or not ndates or ndates < 2:
        return "快照"
    span = (date.fromisoformat(dmax) - date.fromisoformat(dmin)).days
    gap = span / max(ndates - 1, 1)
    return "日" if gap <= 3.5 else "週" if gap <= 10 else "月" if gap <= 45 else "季" if gap <= 120 else "不定期"


def last_weekday(d: date) -> date:
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d


def due_day(cad: str, today: date) -> str | None:
    """該有的最新日期:日 = 前一個平日 · 週 = 10 天內 · 月 = 兩個月內(月營收次月 10 日前才公布)· 季 = 200 天內 · 快照 / 不定期 = 不判。"""
    if cad == "日":
        return last_weekday(today - timedelta(days=1)).isoformat()
    if cad == "週":
        return (today - timedelta(days=10)).isoformat()
    if cad == "月":
        y, m = today.year, today.month - 2
        while m <= 0:
            y, m = y - 1, m + 12
        return date(y, m, 1).isoformat()
    if cad == "季":
        return (today - timedelta(days=200)).isoformat()
    return None


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# ---------------------------------------------------------------- 表的統計(parquet 或來源表都用這支)
def rel_stats(con, rel: str, cols: list, keys: list, dups: bool = True) -> dict:
    n = con.execute("SELECT COUNT(*) FROM %s" % rel).fetchone()[0]
    st = {"rows": n, "cols": len(cols), "date_col": date_col(cols), "dmin": None, "dmax": None, "ndates": None, "dups": None}
    dc = st["date_col"]
    if dc and n:
        vals = [norm_day(r[0]) for r in con.execute("SELECT DISTINCT CAST(%s AS VARCHAR) FROM %s" % (_q(dc), rel)).fetchall()]
        vals = sorted(v for v in vals if v)
        if vals:
            st.update(dmin=vals[0], dmax=vals[-1], ndates=len(vals))
    if dups and n:
        kq = ", ".join(_q(k) for k in keys)
        st["dups"] = con.execute("SELECT COALESCE(SUM(c - 1), 0) FROM (SELECT COUNT(*) c FROM %s GROUP BY %s HAVING COUNT(*) > 1)" % (rel, kq)).fetchone()[0]
    elif dups:
        st["dups"] = 0
    st["cadence"] = cadence(st["dmin"], st["dmax"], st["ndates"])
    return st


def _cols(con, rel: str) -> list:
    return [(r[0], r[1]) for r in con.execute("DESCRIBE SELECT * FROM %s" % rel).fetchall()]


def _declared_key(con, alias: str, table: str) -> list:
    try:
        rows = con.execute("SELECT constraint_type, constraint_column_names FROM duckdb_constraints() WHERE database_name = ? AND table_name = ? "
                           "AND constraint_type IN ('PRIMARY KEY', 'UNIQUE') ORDER BY constraint_type", [alias, table]).fetchall()
    except Exception:  # noqa: BLE001 — 舊版 DuckDB 沒這張系統表:當沒宣告
        return []
    return list(rows[0][1]) if rows else []


def _attach(con, dbs: dict) -> dict:
    """唯讀掛上正典庫;被別的行程鎖住 / 壞檔照實回。→ {庫名: alias | 錯誤字串}"""
    out = {}
    for i, (name, path) in enumerate(sorted(dbs.items())):
        alias = "src%d" % i
        try:
            con.execute("ATTACH %s AS %s (READ_ONLY)" % (_lit(path), alias))
            out[name] = alias
        except Exception as exc:  # noqa: BLE001 — 鎖住 / 壞檔:這輪跳過那本
            out[name] = "ERR:%s: %s" % (type(exc).__name__, str(exc)[:140])
    return out


def _src_tables(con, alias: str) -> list:
    return [r[0] for r in con.execute("SELECT table_name FROM information_schema.tables WHERE table_catalog = ? AND table_schema = 'main' "
                                      "AND table_type = 'BASE TABLE' ORDER BY 1", [alias]).fetchall()]


# ---------------------------------------------------------------- parquet status
def status(home: Path, pq_dir: Path | None = None, today: date | None = None, dups: bool = True) -> dict:
    """資料家協定 parquet 逐檔 + 來源正典庫同表(唯讀):列 · 鍵 · 重複 · 日期 · 頻率 · 該到的日期 · 落後。"""
    duckdb = _duck()
    today = today or date.today()
    pq_dir = Path(pq_dir or home)
    dbs = find_dbs(home)
    con = duckdb.connect()
    att = _attach(con, dbs)
    rows, seen = [], set()
    srcmap = {}
    for name, alias in att.items():
        if not alias.startswith("ERR"):
            for t in _src_tables(con, alias):
                srcmap[(PROTO[name], t)] = (name, alias)
    names = {(m.group(1), m.group(2)) for p in pq_dir.glob("*.parquet") for m in [PROTO_RX.match(p.name)] if m}
    for tag, table in sorted(names | set(srcmap)):
        f = pq_dir / ("%s__%s.parquet" % (tag, table))
        r = {"file": f.name, "tag": tag, "table": table, "db": next((k for k, v in PROTO.items() if v == tag), None), "pq": None, "src": None,
             "key": None, "key_rule": None, "lamp": "GREEN", "notes": []}
        seen.add(f.name)
        src = srcmap.get((tag, table))
        try:
            if f.is_file():
                rel = "read_parquet(%s)" % _lit(f)
                cols = [c for c, _t in _cols(con, rel)]
                decl = _declared_key(con, src[1], table) if src else []
                r["key"], r["key_rule"] = pick_key(cols, decl)
                r["pq"] = rel_stats(con, rel, cols, r["key"], dups)
                r["pq"].update(bytes=f.stat().st_size, mtime=datetime.fromtimestamp(f.stat().st_mtime).isoformat(timespec="seconds"))
            if src:
                rel = "%s.main.%s" % (src[1], _q(table))
                cols = [c for c, _t in _cols(con, rel)]
                if not r["key"]:
                    r["key"], r["key_rule"] = pick_key(cols, _declared_key(con, src[1], table))
                skeys = [k for k in r["key"] if k in cols] or cols
                r["src"] = rel_stats(con, rel, cols, skeys, dups=False)
                r["src"]["keys"] = con.execute("SELECT COUNT(*) FROM (SELECT DISTINCT %s FROM %s)" % (", ".join(_q(k) for k in skeys), rel)).fetchone()[0]
        except Exception as exc:  # noqa: BLE001 — 壞檔 / 型別怪:照實記這一檔,不擋全表
            r["lamp"] = "RED"
            r["notes"].append("讀不了:%s: %s" % (type(exc).__name__, str(exc)[:140]))
        base = r["pq"] or r["src"] or {}
        due = due_day(base.get("cadence") or "快照", today)
        r["due"] = due
        if r["pq"] is None and r["src"] is not None:
            r["lamp"] = "YELLOW"
            r["notes"].append("parquet 還沒有 → parquet sync 會建")
        if r["pq"] and r["pq"].get("dups"):
            r["lamp"] = worst([r["lamp"], "YELLOW"])
            r["notes"].append("重複鍵 %d 列 → parquet sync --dedup" % r["pq"]["dups"])
        if r["pq"] and r["src"] and r["src"].get("keys", r["src"]["rows"]) > r["pq"]["rows"] - (r["pq"].get("dups") or 0):
            r["lamp"] = worst([r["lamp"], "YELLOW"])
            r["notes"].append("正典庫比 parquet 多 %d 個鍵 → parquet sync" % (r["src"]["keys"] - r["pq"]["rows"] + (r["pq"].get("dups") or 0)))
        elif r["pq"] and r["src"] and r["src"]["rows"] > r["src"].get("keys", r["src"]["rows"]):
            r["notes"].append("正典庫自己有 %d 列同鍵重抓(只差擷取時間 / 改值)· parquet 只收一次" % (r["src"]["rows"] - r["src"]["keys"]))
        dmax = max([x for x in ((r["pq"] or {}).get("dmax"), (r["src"] or {}).get("dmax")) if x] or [None]) if base else None
        r["dmax_any"] = dmax
        if due and dmax and dmax < due:
            r["lamp"] = worst([r["lamp"], "YELLOW"])
            r["notes"].append("落後:最新 %s · 該到 %s" % (dmax, due))
        rows.append(r)
    con.close()
    lamps = [r["lamp"] for r in rows]
    return {"tag": TAG, "ts": utc_now(), "home": str(home), "pq_dir": str(pq_dir), "dbs": {k: str(v) for k, v in dbs.items()},
            "attach": {k: v for k, v in att.items() if v.startswith("ERR")}, "rows": rows,
            "lamp": worst(lamps) if rows else "GRAY", "counts": {lp: lamps.count(lp) for lp in ("GREEN", "YELLOW", "RED")}}


# ---------------------------------------------------------------- parquet sync(增量 · 原子替換)
def _replace(tmp: Path, dst: Path, tries: int = 4) -> str | None:
    for i in range(tries):
        try:
            os.replace(tmp, dst)
            return None
        except PermissionError as exc:          # Windows:別的程式(雲端同步 / 讀者)正開著這檔
            if i == tries - 1:
                return "替換不了(檔被佔用):%s" % exc
            time.sleep(0.5 * (2 ** i))
    return "替換不了"


def sync_table(con, alias: str, table: str, dst: Path, tmp_dir: Path, dedup: bool = False) -> dict:
    """一張表:來源有、parquet 沒有的鍵才寫;沒新鍵 = 不動檔。寫新檔先到暫存夾,驗列數與重複鍵後原子替換。"""
    src = "%s.main.%s" % (alias, _q(table))
    scols = _cols(con, src)
    names = [c for c, _t in scols]
    keys, rule = pick_key(names, _declared_key(con, alias, table))
    kq = ", ".join(_q(k) for k in keys)
    vol = [c for c in names if c.lower() in VOLATILE]
    order_new = ", ".join([_q(k) for k in keys] + ["%s DESC NULLS LAST" % _q(v) for v in vol])
    dc = date_col(names)
    tmp = tmp_dir / (dst.name + ".vdfsync.tmp")
    res = {"table": table, "file": dst.name, "key": keys, "key_rule": rule, "added": 0, "action": None, "error": None}
    if tmp.exists():
        tmp.unlink()
    if not dst.is_file():
        con.execute("CREATE OR REPLACE TEMP TABLE _new AS SELECT DISTINCT ON (%s) * FROM %s ORDER BY %s" % (kq, src, order_new))
        n = con.execute("SELECT COUNT(*) FROM _new").fetchone()[0]
        con.execute("COPY (SELECT * FROM _new%s) TO %s (FORMAT PARQUET, COMPRESSION ZSTD)" % ((" ORDER BY %s" % _q(dc)) if dc else "", _lit(tmp)))
        old_n, old_d = 0, 0
        res["action"], res["added"] = "新建", n
    else:
        rel = "read_parquet(%s)" % _lit(dst)
        dcols = dict(_cols(con, rel))
        miss = [k for k in keys if k not in dcols]
        if miss:
            res.update(action="略過", error="鍵欄 %s 不在既有 parquet(欄位改過?先人工看)" % miss)
            return res
        sel = []
        for c, t in scols:
            if c in dcols and dcols[c] != t:
                bad = con.execute("SELECT COUNT(*) FROM %s WHERE %s IS NOT NULL AND TRY_CAST(%s AS %s) IS NULL" % (src, _q(c), _q(c), dcols[c])).fetchone()[0]
                if bad:
                    res.update(action="略過", error="欄 %s 型別 %s → parquet 的 %s 轉不過 %d 列" % (c, t, dcols[c], bad))
                    return res
                sel.append("TRY_CAST(s.%s AS %s) AS %s" % (_q(c), dcols[c], _q(c)))
            else:
                sel.append("s.%s" % _q(c))
        cond = " AND ".join("CAST(s.%s AS VARCHAR) IS NOT DISTINCT FROM CAST(d.%s AS VARCHAR)" % (_q(k), _q(k)) for k in keys)
        con.execute("CREATE OR REPLACE TEMP TABLE _new AS SELECT DISTINCT ON (%s) * FROM (SELECT %s FROM %s s WHERE NOT EXISTS "
                    "(SELECT 1 FROM %s d WHERE %s)) ORDER BY %s" % (kq, ", ".join(sel), src, rel, cond, order_new))
        n = con.execute("SELECT COUNT(*) FROM _new").fetchone()[0]
        old_n = con.execute("SELECT COUNT(*) FROM %s" % rel).fetchone()[0]
        old_d = con.execute("SELECT COALESCE(SUM(c - 1), 0) FROM (SELECT COUNT(*) c FROM %s GROUP BY %s HAVING COUNT(*) > 1)" % (rel, kq)).fetchone()[0]
        if n == 0 and not (dedup and old_d):
            res.update(action="沒新鍵 · 不動檔", existing=old_n, existing_dups=old_d)
            return res
        body = "SELECT * FROM %s UNION ALL BY NAME SELECT * FROM _new" % rel
        if dedup and old_d:
            body = "SELECT DISTINCT ON (%s) * FROM (%s) ORDER BY %s" % (kq, body, order_new)
        con.execute("COPY (SELECT * FROM (%s)%s) TO %s (FORMAT PARQUET, COMPRESSION ZSTD)" % (body, (" ORDER BY %s" % _q(dc)) if dc else "", _lit(tmp)))
        res["action"], res["added"] = ("補新鍵" + (" + 去重" if dedup and old_d else "")), n
    chk = "read_parquet(%s)" % _lit(tmp)
    got = con.execute("SELECT COUNT(*) FROM %s" % chk).fetchone()[0]
    got_d = con.execute("SELECT COALESCE(SUM(c - 1), 0) FROM (SELECT COUNT(*) c FROM %s GROUP BY %s HAVING COUNT(*) > 1)" % (chk, kq)).fetchone()[0]
    want = (old_n + n - old_d) if (dedup and old_d) else (old_n + n)
    want_d = 0 if (dedup or not old_d) else old_d
    if got != want or got_d != want_d:
        tmp.unlink(missing_ok=True)
        res.update(action="略過", error="新檔驗不過:列 %d(該 %d)· 重複鍵 %d(該 %d)→ 原檔不動" % (got, want, got_d, want_d))
        return res
    err = _replace(tmp, dst)
    if err:
        tmp.unlink(missing_ok=True)
        res.update(action="略過", error=err)
        return res
    res.update(rows=got, dups=got_d, removed_dups=(old_d if dedup else 0))
    return res


def write_catalog(pq_dir: Path, tmp_dir: Path, files: list) -> str | None:
    """整合:一個 DuckDB 目錄,每個協定 parquet 一個 VIEW(同名 tw__表 / gl__表)—— 一處查全部,不複製資料。"""
    duckdb = _duck()
    cat, tmp = pq_dir / CATALOG, tmp_dir / (CATALOG + ".tmp")
    tmp.unlink(missing_ok=True)
    con = duckdb.connect(str(tmp))
    try:
        for f in files:
            con.execute("CREATE OR REPLACE VIEW %s AS SELECT * FROM read_parquet(%s)" % (_q(Path(f).stem), _lit(pq_dir / f)))
    finally:
        con.close()
    return _replace(tmp, cat)


def sync(home: Path, pq_dir: Path | None = None, only: list | None = None, dedup: bool = False) -> dict:
    duckdb = _duck()
    pq_dir = Path(pq_dir or home)
    tmp_dir = home / "temp" / "vdf_parquet_sync"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    dbs = find_dbs(home)
    con = duckdb.connect()
    con.execute("SET temp_directory = %s" % _lit(tmp_dir))
    att = _attach(con, dbs)
    out = []
    for name, alias in sorted(att.items()):
        if alias.startswith("ERR"):
            out.append({"table": "*", "file": name, "action": "略過", "error": "正典庫開不了(被引擎鎖住?):" + alias[4:]})
            continue
        for t in _src_tables(con, alias):
            if only and t not in only:
                continue
            dst = pq_dir / ("%s__%s.parquet" % (PROTO[name], t))
            try:
                r = sync_table(con, alias, t, dst, tmp_dir, dedup)
            except Exception as exc:  # noqa: BLE001 — 一張表壞不擋其他表
                r = {"table": t, "file": dst.name, "action": "略過", "error": "%s: %s" % (type(exc).__name__, str(exc)[:160])}
            out.append(r)
    con.close()
    files = sorted(p.name for p in pq_dir.glob("*.parquet") if PROTO_RX.match(p.name))
    man = update_manifest(pq_dir, files, out)
    cat_err = write_catalog(pq_dir, tmp_dir, files) if files else None
    errs = [r for r in out if r.get("error")]
    return {"tag": TAG, "ts": utc_now(), "home": str(home), "pq_dir": str(pq_dir), "dbs": {k: str(v) for k, v in dbs.items()},
            "results": out, "written": sum(1 for r in out if r.get("action") in ("新建",) or str(r.get("action", "")).startswith("補新鍵")),
            "unchanged": sum(1 for r in out if r.get("action") == "沒新鍵 · 不動檔"), "added_rows": sum(r.get("added") or 0 for r in out),
            "errors": len(errs), "catalog": (str(pq_dir / CATALOG) if not cat_err else "沒寫:" + cat_err), "manifest": man,
            "lamp": "RED" if errs else ("GRAY" if not dbs else "GREEN")}


def update_manifest(pq_dir: Path, files: list, results: list | None = None) -> str:
    """資料家清單:每檔 列 · 欄 · 鍵 · 日期範圍 · 大小 · sha256(大小 / 時間沒變就沿用,不重算)· 最近一次同步補了幾列。"""
    duckdb = _duck()
    p = pq_dir / MANIFEST
    try:
        old = json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}
    except (OSError, ValueError):
        old = {}
    prev = old.get("files") or {}
    last = {r["file"]: r for r in results or [] if r.get("file")}
    con = duckdb.connect()
    files_out = {}
    for f in files:
        fp = pq_dir / f
        stt = fp.stat()
        o = prev.get(f) or {}
        same = o.get("bytes") == stt.st_size and o.get("mtime_ns") == stt.st_mtime_ns
        if same and o.get("sha256"):
            rec = dict(o)
        else:
            rel = "read_parquet(%s)" % _lit(fp)
            cols = [c for c, _t in _cols(con, rel)]
            key, rule = pick_key(cols)
            st = rel_stats(con, rel, cols, key, dups=False)
            m = PROTO_RX.match(f)
            rec = {"db": next((k for k, v in PROTO.items() if v == m.group(1)), None), "table": m.group(2), "rows": st["rows"], "cols": st["cols"],
                   "key": key, "key_rule": rule, "date_col": st["date_col"], "date_min": st["dmin"], "date_max": st["dmax"], "cadence": st["cadence"],
                   "bytes": stt.st_size, "mtime_ns": stt.st_mtime_ns, "sha256": _sha256(fp)}
        if f in last:
            rec["last_sync"] = {"at": utc_now(), "action": last[f].get("action"), "added": last[f].get("added", 0), "error": last[f].get("error")}
        files_out[f] = rec
    con.close()
    man = {"schema": "VDF.ParquetDB.Manifest.v1", "engine": TAG, "updated_at": utc_now(), "pq_dir": str(pq_dir), "files": files_out,
           "exports": old.get("exports") or {}}
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text(json.dumps(man, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, p)
    return str(p)


# ---------------------------------------------------------------- 不重複擷取計畫
def writers_book() -> dict:
    """VIA_DB_Table_SSOT 尾版:(庫, 表) → 寫入引擎(只讀)。"""
    book = _tail(VIA / "supportive modules" / "registry", "VIA_DB_Table_SSOT_v*.json")
    if not book:
        return {}
    try:
        rows = json.loads(book.read_text(encoding="utf-8")).get("tables") or []
    except (OSError, ValueError):
        return {}
    return {(r.get("db"), r.get("table")): list(r.get("writers") or []) for r in rows}


def engine_file(code: str) -> str:
    hit = _tail(HERE / "engine", "%s_*_v*.py" % code) or _tail(HERE, "%s_*_v*.py" % code)
    return re.sub(r"_v\d{4}$", "", hit.stem) if hit else code


def plan(st: dict, wb: dict | None = None) -> dict:
    """每表:正典庫已到該到的日期 → 不擷取(parquet 落後就只要 sync);正典庫也沒到 → 列寫入引擎去擷取;快照表不判。"""
    wb = writers_book() if wb is None else wb
    items = []
    for r in st.get("rows") or []:
        src, pq, due = r.get("src") or {}, r.get("pq") or {}, r.get("due")
        smax, pmax = src.get("dmax"), pq.get("dmax")
        writers = wb.get((r.get("db"), r["table"])) or []
        behind = bool(src) and (not pq or pq.get("rows", 0) < src.get("keys", src.get("rows", 0)) or (pmax or "") < (smax or ""))
        if not due:
            act, why = (("只要 sync", "正典庫有、parquet 還沒跟上(%s表不判擷取)" % (src.get("cadence") or "快照")) if behind
                        else ("不判", "%s表(沒有固定頻率)" % ((src or pq).get("cadence") or "快照")))
        elif smax and smax >= due:
            act, why = ("只要 sync" if not pmax or pmax < smax else "已最新 · 跳過"), "正典庫最新 %s ≥ 該到 %s" % (smax, due)
        elif pmax and pmax >= due and not src:
            act, why = "已最新 · 跳過", "parquet 最新 %s ≥ 該到 %s(正典庫不在這台)" % (pmax, due)
        else:
            act, why = "要擷取", "最新 %s < 該到 %s" % (max([x for x in (smax, pmax) if x] or ["—"]), due)
        items.append({"file": r["file"], "table": r["table"], "action": act, "why": why, "from": (max([x for x in (smax, pmax) if x] or [None]) or None),
                      "writers": [engine_file(w) for w in writers]})
    fetch = sorted({w for i in items if i["action"] == "要擷取" for w in i["writers"]})
    orphan = [i["table"] for i in items if i["action"] == "要擷取" and not i["writers"]]
    return {"items": items, "fetch_engines": fetch, "no_writer": orphan,
            "counts": {a: sum(1 for i in items if i["action"] == a) for a in ("要擷取", "只要 sync", "已最新 · 跳過", "不判")}}


# ---------------------------------------------------------------- 增量匯出
def resolve_dest(dest: str, env=None, home_dir: Path | None = None) -> tuple:
    """<夾> | onedrive | gdrive | dropbox → (目的地夾, 說明)。OneDrive / Google 的候選照 VDF_ENG237 resolve_dest 同一套。"""
    env = os.environ if env is None else env
    home_dir = Path(home_dir or Path.home())
    d = (dest or "").strip()
    low = d.lower()
    if low == "onedrive":
        for k in ("OneDrive", "OneDriveConsumer", "OneDriveCommercial"):
            if env.get(k) and Path(env[k]).is_dir():
                return Path(env[k]) / "VDF_ParquetDB", "OneDrive(%s)" % k
        return ((home_dir / "OneDrive" / "VDF_ParquetDB", "OneDrive(家目錄)") if (home_dir / "OneDrive").is_dir()
                else (None, "找不到 OneDrive 同步夾"))
    if low in ("gdrive", "googledrive", "google"):
        for c in (env.get("VIA_GDRIVE_DIR"), "G:\\My Drive", "G:\\我的雲端硬碟", str(home_dir / "Google Drive" / "My Drive"),
                  str(home_dir / "Google Drive"), str(home_dir / "My Drive")):
            if c and Path(c).is_dir():
                return Path(c) / "VDF_ParquetDB", "Google 雲端硬碟(%s)" % c
        return None, "找不到 Google 雲端硬碟同步夾(設 VIA_GDRIVE_DIR)"
    if low == "dropbox":
        for c in (env.get("VIA_DROPBOX_DIR"), str(home_dir / "Dropbox")):
            if c and Path(c).is_dir():
                return Path(c) / "VDF_ParquetDB", "Dropbox(%s)" % c
        return None, "找不到 Dropbox 同步夾(設 VIA_DROPBOX_DIR)"
    if not d:
        return None, "沒給 --to(<夾> | onedrive | gdrive | dropbox)"
    return Path(d), "指定夾"


def export(pq_dir: Path, dest: str, env=None, home_dir: Path | None = None) -> dict:
    """只複製 sha256 跟目的地清單不同的檔(暫存名寫完再原子改名);寫目的地清單 + MCP 交接清單;來源清單記這次匯出。"""
    man_p = Path(pq_dir) / MANIFEST
    if not man_p.is_file():
        return {"lamp": "GRAY", "why": "資料家還沒有 %s → 先 parquet sync" % MANIFEST}
    src_man = json.loads(man_p.read_text(encoding="utf-8"))
    to, why = resolve_dest(dest, env, home_dir)
    if to is None:
        return {"lamp": "RED", "why": why}
    if Path(to).resolve() == Path(pq_dir).resolve():
        return {"lamp": "RED", "why": "目的地就是資料家本身"}
    to.mkdir(parents=True, exist_ok=True)
    dm_p = to / MANIFEST
    try:
        dst_files = (json.loads(dm_p.read_text(encoding="utf-8")).get("files") or {}) if dm_p.is_file() else {}
    except (OSError, ValueError):
        dst_files = {}
    copied, skipped, errs, mcp = [], [], [], []
    try:
        done = json.loads((to / MCP_DONE).read_text(encoding="utf-8")) if (to / MCP_DONE).is_file() else {}
    except (OSError, ValueError):
        done = {}
    for f, rec in sorted(src_man.get("files", {}).items()):
        sp, dp = Path(pq_dir) / f, to / f
        if not sp.is_file():
            errs.append("%s 不在資料家" % f)
            continue
        same = dp.is_file() and (dst_files.get(f) or {}).get("sha256") == rec.get("sha256") and dp.stat().st_size == rec.get("bytes")
        if same:
            skipped.append(f)
        else:
            tmp = to / (f + ".vdfexport.tmp")
            shutil.copyfile(sp, tmp)
            if _sha256(tmp) != rec.get("sha256"):
                tmp.unlink(missing_ok=True)
                errs.append("%s 複製後 sha256 對不上(來源在寫?)→ 這次不換" % f)
                continue
            e = _replace(tmp, dp)
            if e:
                tmp.unlink(missing_ok=True)
                errs.append("%s:%s" % (f, e))
                continue
            copied.append(f)
        mcp.append({"file": f, "path": str(dp), "upload": done.get(f) != rec.get("sha256"),
                    "sha256": rec.get("sha256"), "bytes": rec.get("bytes"), "mime": "application/vnd.apache.parquet",
                    "db": rec.get("db"), "table": rec.get("table"), "rows": rec.get("rows"), "date_min": rec.get("date_min"), "date_max": rec.get("date_max")})
    dman = dict(src_man, exported_at=utc_now(), source=str(pq_dir), exports=None)
    dman.pop("exports", None)
    tmp = to / (MANIFEST + ".tmp")
    tmp.write_text(json.dumps(dman, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, dm_p)
    handoff = {"schema": "VDF.ParquetDB.MCPHandoff.v1", "engine": TAG, "made_at": utc_now(), "folder": str(to), "dest": dest, "dest_why": why,
               "how": "給 MCP 雲端硬碟工具:只上傳 upload=true 的檔到同名路徑(覆蓋同名舊檔);上傳後以 sha256 比對;"
                      "比對過的檔把 {檔名: sha256} 寫進同夾 %s,下次匯出就不再列。本檔不含任何金鑰;VDF 不代登入雲端。" % MCP_DONE,
               "files": mcp, "to_upload": sum(1 for x in mcp if x["upload"])}
    (to / MCP_NAME).write_text(json.dumps(handoff, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    src_man.setdefault("exports", {})[str(to)] = {"at": utc_now(), "dest": dest, "copied": len(copied), "skipped": len(skipped), "errors": len(errs)}
    tmp = man_p.with_name(man_p.name + ".tmp")
    tmp.write_text(json.dumps(src_man, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, man_p)
    return {"lamp": "RED" if errs else "GREEN", "to": str(to), "why": why, "copied": copied, "skipped": skipped, "errors": errs,
            "mcp": str(to / MCP_NAME), "to_upload": handoff["to_upload"]}


# ---------------------------------------------------------------- 清單輸入閘
def lists_home(home: Path | None, arg: str | None = None, env=None) -> tuple:
    env = os.environ if env is None else env
    cands = [(arg, "--lists-home"), (env.get("VIA_VDF_FETCH_HOME"), "env VIA_VDF_FETCH_HOME")]
    if home:
        cands += [(str(home / "output_hub"), "資料家/output_hub"), (str(home), "資料家")]
    cands += [(str(VIA / "VIA_Reports" / "vdf_fetch" / "dict"), "倉內 VIA_Reports/vdf_fetch/dict"), (str(HERE / "output_hub"), "倉內 VDF/output_hub")]
    for c, why in cands:
        if c and (Path(c) / "0-1-TWStockList").is_dir():
            return Path(c), why
    return None, "找不到 0-1-TWStockList(先 VDF_SystemManager fetch run 009 010)"


def _read_pq(con, p: Path) -> list:
    cur = con.execute("SELECT * FROM read_parquet(%s)" % _lit(p))
    names = [d[0] for d in cur.description]
    return [dict(zip(names, r)) for r in cur.fetchall()]


def _ck(cid: str, name: str, lamp: str, note: str) -> dict:
    return {"id": cid, "name": name, "lamp": lamp, "note": note}


def _list_checks(rows: list, kind: str, today: date, module_v2: str | None = None, fresh: dict | None = None) -> list:
    rx, src = shared_rx(kind)
    fresh = fresh or DEFAULT_PARAMS["list_fresh_days"]
    out = []
    live = [r for r in rows if str(r.get("status") or "").upper() != "DELISTED"]
    bad = [r.get("ticker") for r in rows if not rx.match(str(r.get("ticker") or ""))]
    if bad and kind == "stock" and module_v2 == "GREEN" and all(re.match(r"^\d{4}$", str(t)) for t in bad):
        out.append(_ck("C1", "共用代碼律 %s(%s)" % (rx.pattern, src), "GREEN",
                       "擋區 %d 檔經 MDL009 名稱核對保留(模組 V2 綠):%s" % (len(bad), bad[:5])))
    else:
        out.append(_ck("C1", "共用代碼律 %s(%s)" % (rx.pattern, src), "RED" if bad else "GREEN", "違律 %d %s" % (len(bad), bad[:5])))
    tk = [str(r.get("ticker")) for r in rows]
    dup = sorted({t for t in tk if tk.count(t) > 1})
    out.append(_ck("C2", "不重號", "RED" if dup else "GREEN", "重號 %s" % dup[:5]))
    suf = {"TWSE": ".TW", "TPEX": ".TWO", "TPEx": ".TWO", "OTC": ".TWO"}
    wrong = [r.get("ticker") for r in rows if suf.get(str(r.get("market"))) and str(r.get("yf_ticker")) != str(r.get("ticker")) + suf[str(r.get("market"))]]
    unk = [r.get("ticker") for r in rows if not suf.get(str(r.get("market")))]
    out.append(_ck("C3", "Yahoo 後綴對市場(上市 .TW · 上櫃 .TWO)", "RED" if wrong else ("YELLOW" if unk else "GREEN"),
                   "不合 %s · 市場不明 %s" % (wrong[:5], unk[:5])))
    days = sorted({str(r.get("date"))[:10] for r in rows if r.get("date")})
    age = (today - date.fromisoformat(days[-1])).days if days else None
    out.append(_ck("C4", "清單日期新鮮(%d 天內綠 · %d 天內黃)" % (fresh["green"], fresh["yellow"]),
                   "RED" if age is None or age > fresh["yellow"] else ("YELLOW" if age > fresh["green"] else "GREEN"),
                   "清單日 %s · %s 天前" % (days[-1] if days else "—", age)))
    out.append(_ck("C5", "在市檔數 > 0", "GREEN" if live else "RED", "在市 %d / 全部 %d" % (len(live), len(rows))))
    return out


def inputs(home: Path | None = None, lists_arg: str | None = None, today: date | None = None, env=None) -> dict:
    """台股清單 · 主動式台股 ETF 清單 · 合格判定(VDF-REQ026):模組自報的驗證燈 + 本閘獨立重驗。有紅 = 不該拿去當擷取輸入。"""
    duckdb = _duck()
    today = today or date.today()
    lh, why = lists_home(home, lists_arg, env)
    res = {"tag": TAG, "ts": utc_now(), "lists_home": str(lh) if lh else None, "why": why, "lists": {}, "lamp": "RED"}
    if lh is None:
        return res
    con = duckdb.connect()
    for kind, sub, stem in (("stock", "0-1-TWStockList", "tw_stock_list"), ("etf", "0-2-ActiveETFList", "active_etf_list")):
        d = lh / sub
        p = d / ("%s_latest.parquet" % stem)
        it = {"file": str(p), "checks": []}
        if not p.is_file():
            it["checks"].append(_ck("C0", "清單檔在", "RED", "%s 不在" % p.name))
        else:
            rows = _read_pq(con, p)
            it["rows"] = len(rows)
            vr = d / "verify_report.json"
            try:
                v = json.loads(vr.read_text(encoding="utf-8")) if vr.is_file() else None
            except (OSError, ValueError):
                v = None
            v2 = next((c.get("lamp") for c in (v or {}).get("checks") or [] if c.get("id") == "V2"), None)
            it["checks"] += _list_checks(rows, kind, today, v2, load_params()[0]["list_fresh_days"])
            it["checks"].append(_ck("M0", "模組自己的驗證(%s)" % ((v or {}).get("engine") or "verify_report.json"),
                                    (v or {}).get("lamp") or "RED", "%s · %s" % (((v or {}).get("date") or "沒有 verify_report.json"),
                                                                                  " · ".join("%s %s" % (c.get("id"), c.get("lamp")) for c in (v or {}).get("checks") or [] if c.get("lamp") != "GREEN") or "全綠")))
            if kind == "etf":
                q = d / "active_etf_qualified_latest.csv"
                if not q.is_file():
                    it["checks"].append(_ck("Q1", "合格判定(VDF-REQ026)在", "RED", "active_etf_qualified_latest.csv 不在 → fetch run 010 / MDL010 qualify"))
                else:
                    with open(q, encoding="utf-8-sig", newline="") as fh:
                        qs = list(csv.DictReader(fh))
                    yes = [r["ticker"] for r in qs if str(r.get("qualified")).lower() in ("true", "1", "yes")]
                    no = [r["ticker"] for r in qs if str(r.get("qualified")).lower() in ("false", "0", "no")]
                    und = [r["ticker"] for r in qs if r["ticker"] not in yes + no]
                    miss = sorted({str(r.get("ticker")) for r in rows} - {r["ticker"] for r in qs})
                    it["qualified"], it["not_qualified"], it["undetermined"] = yes, no, und
                    it["checks"].append(_ck("Q1", "合格判定(每日持股抓得到才合格)", "RED" if miss else ("YELLOW" if und else "GREEN"),
                                            "合格 %d · 不合格 %d · 未判 %d · 清單有判定沒有 %s" % (len(yes), len(no), len(und), miss[:5])))
        it["lamp"] = worst([c["lamp"] for c in it["checks"]])
        res["lists"][kind] = it
    con.close()
    res["lamp"] = worst([x["lamp"] for x in res["lists"].values()])
    return res


# ---------------------------------------------------------------- 管理範圍總表
def _read_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None
    except (OSError, ValueError):
        return None


def scope(home=None, lists_arg=None, today=None, root: Path = VIA, env=None) -> dict:
    """VDF System Manager 管的範圍(輸入 → 擷取 → 正典庫 → parquet 增量庫 → 匯出 → 整合),每項一燈 + 證據 + 下一步。"""
    out_dir = root / OUT_REL
    hm, hwhy = resolve_home(home, env)
    inp = inputs(hm, lists_arg, today, env)
    st = status(hm, today=today) if hm else None
    pl = plan(st) if st else None
    chk, ver = _read_json(out_dir / "DB_CHECK_latest.json"), _read_json(out_dir / "VERIFY_latest.json")
    fm = _read_json(out_dir / "FETCH_MATRIX_latest.json")
    share = _read_json(out_dir / "universe_share" / "VDF_UniverseShare_latest.json")
    man = _read_json(Path(st["pq_dir"]) / MANIFEST) if st else None
    M = "VDF_SystemManager"
    items = [
        {"id": "S1", "name": "輸入清單(台股 · 主動式台股 ETF · 合格判定)", "lamp": inp["lamp"],
         "evidence": "清單家 %s(%s)" % (inp.get("lists_home") or "—", inp["why"]), "next": "%s inputs" % M},
        {"id": "S2", "name": "擷取(擷取系統 MDL008 · 不重複擷取計畫)", "lamp": ("YELLOW" if pl and pl["counts"].get("要擷取") else ("GREEN" if pl else "GRAY")),
         "evidence": ("計畫:要擷取 %d · 只要 sync %d · 已最新 %d · 不判 %d" % tuple(pl["counts"].get(k, 0) for k in ("要擷取", "只要 sync", "已最新 · 跳過", "不判")) if pl else hwhy)
         + (" · 擷取矩陣 %s" % fm.get("ts") if fm else ""), "next": "%s parquet plan → 只跑列出的寫入引擎" % M},
        {"id": "S3", "name": "DuckDB 正典庫(清點 · 獨立核對)", "lamp": worst([(chk or {}).get("lamp"), "GREEN" if (ver or {}).get("lamp") == "PASS" else ("RED" if ver else None)]) if chk else "GRAY",
         "evidence": "清點 %s %s · 核對 %s" % ((chk or {}).get("lamp", "—"), (chk or {}).get("ts", ""), (ver or {}).get("lamp", "—")), "next": "%s db check · db verify" % M},
        {"id": "S4", "name": "Parquet 增量庫(資料家 tw__ / gl__)", "lamp": st["lamp"] if st else "GRAY",
         "evidence": ("%s · %d 檔 · 綠 %d 黃 %d 紅 %d" % (st["pq_dir"], len(st["rows"]), st["counts"]["GREEN"], st["counts"]["YELLOW"], st["counts"]["RED"]) if st else hwhy),
         "next": "%s parquet sync(沒新鍵不動檔)" % M},
        {"id": "S5", "name": "匯出(PC 夾 · 雲端同步夾 · MCP 交接清單)", "lamp": ("GREEN" if man and man.get("exports") else ("YELLOW" if man else "GRAY")),
         "evidence": (" · ".join("%s %s(複製 %s · 沿用 %s)" % (k, v.get("at"), v.get("copied"), v.get("skipped")) for k, v in (man.get("exports") or {}).items()) or "還沒匯出過") if man else "資料家還沒有清單",
         "next": "%s parquet export --to <夾|onedrive|gdrive|dropbox>" % M},
        {"id": "S6", "name": "整合(主清單分享 · 資料庫狀態頁 · parquet 目錄)", "lamp": worst([
            ("GREEN" if share and share.get("content_sha256") else "YELLOW"), ("GREEN" if (out_dir / "DB_STATUS_MATRIX_latest.html").is_file() else "YELLOW"),
            ("GREEN" if st and (Path(st["pq_dir"]) / CATALOG).is_file() else "YELLOW")]),
         "evidence": "分享 %s · 矩陣頁 %s · 目錄 %s" % ((share or {}).get("version", "—"), "有" if (out_dir / "DB_STATUS_MATRIX_latest.html").is_file() else "沒有",
                                                   "有" if st and (Path(st["pq_dir"]) / CATALOG).is_file() else "沒有"),
         "next": "%s engine run VDF_MDL018_UniverseShare · parquet sync(建目錄)" % M},
    ]
    return {"tag": TAG, "ts": utc_now(), "home": str(hm) if hm else None, "home_why": hwhy, "items": items, "inputs": inp, "status": st, "plan": pl,
            "lamp": worst([i["lamp"] for i in items])}


# ---------------------------------------------------------------- U/I
EXTRA_CSS = (
    "body{background:#f8f7f2;max-width:1320px;margin:0 auto;padding:18px 16px}.dp-head{margin:0 0 14px}"
    ".dp-r1{font-size:10.5px;letter-spacing:.14em;color:#6b7468}.dp-r2{font-size:21px;font-weight:600;margin:2px 0}.dp-r3{font-size:11.5px;color:#55605a}"
    ".dp-sec{background:#fffefb;border:1px solid #dedfd5;border-radius:8px;padding:14px 16px;margin:0 0 14px}"
    ".dp-kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(136px,1fr));gap:10px;margin:0 0 14px}"
    ".dp-kpi{background:#fffefb;border:1px solid #dedfd5;border-radius:8px;padding:10px 12px;min-width:0}"
    ".dp-kpi .k{font-size:10.5px;color:#6b7468}.dp-kpi .v{font-size:19px;font-weight:600;margin-top:2px;word-break:break-word}"
    ".dp-lamp{display:inline-block;border-radius:5px;padding:0 6px;font-size:10.5px;color:#fff;white-space:nowrap}"
    ".dp-RED{background:#dc2626}.dp-YELLOW{background:#f59e0b}.dp-GREEN{background:#16a34a}.dp-INFO,.dp-GRAY,.dp-SKIP{background:#9ca3af}"
    ".dp-scroll{overflow-x:auto;max-width:100%}table.dp{border-collapse:collapse;width:100%;font-size:11.5px}"
    "table.dp th,table.dp td{border-bottom:1px solid #e1e4dc;padding:6px 8px;text-align:left;vertical-align:top}"
    "table.dp th{background:#eeeee7;font-weight:600;font-size:10.5px;white-space:nowrap}td.n{text-align:right;font-variant-numeric:tabular-nums}"
    ".dp-small{font-size:10.5px;color:#6b7468}code{background:#eeeee7;border-radius:4px;padding:0 4px;word-break:break-all}")


def _spec_css() -> tuple:
    book = _tail(HERE, SPEC_GLOB)
    if not book:
        return "", "規格冊不在 → 無樣式(照實)"
    s = json.loads(book.read_text(encoding="utf-8"))
    css = s.get("css") or ""
    if hashlib.sha256(css.encode("utf-8")).hexdigest() != s.get("css_sha256"):
        return "", "規格冊 css 對不上鎖 → 不套(照實黃)"
    return css, "%s · %s · sha256 驗過" % (book.name, s.get("style_id"))


def _e(x) -> str:
    return html.escape("" if x is None else str(x))


def _chip(lp) -> str:
    return '<span class="dp-lamp dp-%s">%s</span>' % (_e(lp), _e(lp))


def _tbl(head: list, rows: list) -> str:
    return '<div class="dp-scroll"><table class="dp"><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (
        "".join("<th>%s</th>" % _e(h) for h in head), "".join("<tr>%s</tr>" % "".join(r) for r in rows) or
        '<tr><td colspan="%d" class="dp-small">沒有</td></tr>' % len(head))


def page(sc: dict, sync_res: dict | None = None) -> str:
    css, note = _spec_css()
    st, pl, inp = sc.get("status"), sc.get("plan"), sc["inputs"]
    p = ['<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="via-page" content="VDF_SCOPE">'
         '<meta name="viewport" content="width=device-width,initial-scale=1"><title>VDF 管理範圍</title><style>%s</style><style>%s</style></head><body>' % (css, EXTRA_CSS),
         '<header class="dp-head"><div class="dp-r1">VERITAS INTELLIGENCE ANALYTICS</div><div class="dp-r2">Veritas DataForge</div>'
         '<div class="dp-r3">管理範圍 · 輸入清單 → 擷取 → DuckDB 正典庫 → Parquet 增量庫 → 匯出(PC · 雲端 · MCP)→ 整合</div></header>']
    hp = Path(sc["home"]).parts[-2:] if sc.get("home") else []
    kp = [("總燈", _chip(sc["lamp"])), ("資料家", ('<span title="%s" style="font-size:14px">…/%s</span>' % (_e(sc["home"]), _e("/".join(hp)))) if hp else "—"),
          ("清單閘", _chip(inp["lamp"])),
          ("Parquet 檔", str(len(st["rows"])) if st else "—"), ("要擷取", str(pl["counts"].get("要擷取", 0)) if pl else "—"),
          ("只要 sync", str(pl["counts"].get("只要 sync", 0)) if pl else "—"), ("產生", _e(sc["ts"].replace("T", " ")[:16]) + " UTC")]
    p.append('<div class="dp-kpis">%s</div>' % "".join('<div class="dp-kpi"><div class="k">%s</div><div class="v">%s</div></div>' % (_e(k), v) for k, v in kp))
    p.append('<section class="dp-sec"><h2>管理範圍(VDF System Manager 管的六件事)</h2>%s</section>' % _tbl(
        ["項", "燈", "範圍", "證據", "下一步"], [['<td style="white-space:nowrap">%s</td>' % _e(i["id"]), "<td>%s</td>" % _chip(i["lamp"]), "<td><b>%s</b></td>" % _e(i["name"]),
                                             '<td class="dp-small">%s</td>' % _e(i["evidence"]), "<td><code>%s</code></td>" % _e(i["next"])] for i in sc["items"]]))
    ck = []
    for kind, it in inp.get("lists", {}).items():
        for c in it["checks"]:
            ck.append(["<td>%s</td>" % ("台股清單" if kind == "stock" else "主動式 ETF"), "<td>%s</td>" % _e(c["id"]), "<td>%s</td>" % _chip(c["lamp"]),
                       "<td>%s</td>" % _e(c["name"]), '<td class="dp-small">%s</td>' % _e(c["note"])])
    p.append('<section class="dp-sec"><h2>清單輸入閘 %s</h2><p class="dp-small">清單家:%s(%s)· 有紅 = 不拿去擷取</p>%s</section>' % (
        _chip(inp["lamp"]), _e(inp.get("lists_home") or "—"), _e(inp["why"]), _tbl(["清單", "檢", "燈", "規則", "結果"], ck)))
    if st:
        pa = {i["file"]: i for i in (pl or {}).get("items", [])}
        sy = {r["file"]: r for r in (sync_res or {}).get("results", [])}
        rows = []
        for r in st["rows"]:
            pq, src = r.get("pq") or {}, r.get("src") or {}
            rows.append(["<td><b>%s</b></td>" % _e(r["file"]), "<td>%s</td>" % _chip(r["lamp"]), '<td class="n">%s</td>' % _e(format(pq["rows"], ",") if pq else "—"),
                         '<td class="n">%s</td>' % _e(format(src["rows"], ",") if src else "—"), "<td>%s ~ %s</td>" % (_e(pq.get("dmin") or src.get("dmin") or "—"), _e(r.get("dmax_any") or "—")),
                         "<td>%s</td>" % _e(pq.get("cadence") or src.get("cadence") or "—"), '<td class="n">%s</td>' % _e(pq.get("dups") if pq else "—"),
                         '<td class="dp-small">%s</td>' % _e(r.get("key_rule")), "<td>%s</td>" % _e((pa.get(r["file"]) or {}).get("action", "—")),
                         "<td>%s</td>" % _e(("%s +%s" % (sy[r["file"]]["action"], sy[r["file"]].get("added", 0))) if r["file"] in sy else "—"),
                         '<td class="dp-small">%s</td>' % _e(" · ".join(r["notes"]))])
        p.append('<section class="dp-sec"><h2>Parquet 增量庫 %s</h2><p class="dp-small">%s · 正典庫 %s</p>%s</section>' % (
            _chip(st["lamp"]), _e(st["pq_dir"]), _e(" · ".join("%s" % Path(v).name for v in st["dbs"].values()) or "這台沒有(只看 parquet)"),
            _tbl(["檔", "燈", "parquet 列", "正典庫列", "日期範圍", "頻率", "重複鍵", "鍵律", "擷取計畫", "這輪同步", "說明"], rows)))
    if pl and pl.get("fetch_engines"):
        p.append('<section class="dp-sec"><h2>只擷取缺的(不重複擷取)</h2><p>%s</p></section>' % " · ".join(
            "<code>VDF_SystemManager engine run %s</code>" % _e(w) for w in pl["fetch_engines"]))
    p.append('<p class="dp-small">%s · 樣式 %s</p></body></html>' % (_e(TAG), _e(note)))
    return "".join(p)


def write_reports(sc: dict, sync_res: dict | None = None, root: Path = VIA) -> dict:
    out = root / OUT_REL
    out.mkdir(parents=True, exist_ok=True)
    pj, ph = out / "VDF_SCOPE_latest.json", out / "VDF_SCOPE_latest.html"
    data = dict(sc, sync=sync_res)
    pj.write_text(json.dumps(data, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8")
    ph.write_text(page(sc, sync_res), encoding="utf-8")
    return {"json": str(pj), "html": str(ph)}


# ---------------------------------------------------------------- CLI
def _opt(args: list, k: str):
    return args[args.index(k) + 1] if k in args and args.index(k) + 1 < len(args) else None


USAGE = ("動詞:scope | inputs | parquet status | parquet sync [--only 表,表] [--dedup] | parquet plan | parquet export --to <夾|onedrive|gdrive|dropbox>"
         " · 共用 [--home 資料家] [--pq-dir 夾] [--lists-home 夾] | --selftest")


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    verb = args[0] if args else ""
    sub = args[1] if verb == "parquet" and len(args) > 1 else None
    if verb not in ("scope", "inputs", "parquet") or (verb == "parquet" and sub not in ("status", "sync", "plan", "export")):
        print("[%s] %s" % (TAG, USAGE))
        return 2
    if sub in WRITE_VERBS and not entry_ok():
        print("[%s] 拒絕寫入:由 VDF System Manager 總控(VIA_FROM_VDFSM=YES)或 VCGC" % TAG)
        return 2
    home, hwhy = resolve_home(_opt(args, "--home"))
    pq_dir = Path(_opt(args, "--pq-dir")) if _opt(args, "--pq-dir") else None
    if verb == "inputs":
        r = inputs(home, _opt(args, "--lists-home"))
        print("[%s] 清單輸入閘 %s · 清單家 %s(%s)" % (TAG, r["lamp"], r.get("lists_home") or "—", r["why"]))
        for kind, it in r["lists"].items():
            print("  [%s] %s · %s 列" % (it["lamp"], "台股清單" if kind == "stock" else "主動式 ETF 清單", it.get("rows", "—")))
            for c in it["checks"]:
                if c["lamp"] != "GREEN":
                    print("      %s %s %s · %s" % (c["lamp"], c["id"], c["name"], c["note"][:150]))
        return {"GREEN": 0, "YELLOW": 2}.get(r["lamp"], 1)
    if verb == "scope":
        sc = scope(_opt(args, "--home"), _opt(args, "--lists-home"))
        rp = write_reports(sc)
        print("[%s] 管理範圍 %s · 資料家 %s(%s)" % (TAG, sc["lamp"], sc.get("home") or "—", sc["home_why"]))
        for i in sc["items"]:
            print("  [%-6s] %s %s · %s → %s" % (i["lamp"], i["id"], i["name"], i["evidence"][:110], i["next"]))
        print("  [頁] %s" % rp["html"])
        return {"GREEN": 0, "YELLOW": 2, "GRAY": 2}.get(sc["lamp"], 1)
    if home is None:
        print("[%s] GRAY · %s" % (TAG, hwhy))
        return 2
    if sub == "status":
        st = status(home, pq_dir)
        print("[%s] parquet status %s · %s · %d 檔 · 綠 %d 黃 %d 紅 %d" % (TAG, st["lamp"], st["pq_dir"], len(st["rows"]), st["counts"]["GREEN"],
                                                                         st["counts"]["YELLOW"], st["counts"]["RED"]))
        for r in st["rows"]:
            pq = r.get("pq") or {}
            print("  [%-6s] %-34s 列 %-10s 最新 %-10s 重複 %-4s %s %s" % (r["lamp"], r["file"], pq.get("rows", "—"), r.get("dmax_any") or "—",
                                                                     pq.get("dups", "—"), r.get("key_rule") or "", " · ".join(r["notes"])[:90]))
        return {"GREEN": 0, "YELLOW": 2, "GRAY": 2}.get(st["lamp"], 1)
    if sub == "plan":
        st = status(home, pq_dir)
        pl = plan(st)
        print("[%s] 不重複擷取計畫 · 要擷取 %d · 只要 sync %d · 已最新 %d · 不判 %d" % ((TAG,) + tuple(pl["counts"].get(k, 0) for k in ("要擷取", "只要 sync", "已最新 · 跳過", "不判"))))
        for i in pl["items"]:
            if i["action"] != "已最新 · 跳過":
                print("  %-10s %-34s %s · 寫入 %s" % (i["action"], i["file"], i["why"], " ".join(i["writers"]) or "冊上沒登"))
        for w in pl["fetch_engines"]:
            print("  → VDF_SystemManager engine run %s" % w)
        return 0
    if sub == "sync":
        only = (_opt(args, "--only") or "").split(",") if _opt(args, "--only") else None
        t0 = time.time()
        r = sync(home, pq_dir, [x for x in only or [] if x] or None, "--dedup" in args)
        print("[%s] parquet sync %s · %.1fs · 寫 %d 檔 · 沒新鍵不動 %d 檔 · 補 %d 列 · 錯 %d · 目錄 %s" % (
            TAG, r["lamp"], time.time() - t0, r["written"], r["unchanged"], r["added_rows"], r["errors"], r["catalog"]))
        for x in r["results"]:
            if x.get("action") != "沒新鍵 · 不動檔":
                print("  %-12s %-34s +%-8s %s %s" % (x.get("action"), x.get("file"), x.get("added", 0), x.get("key_rule") or "", x.get("error") or ""))
        if not r["dbs"]:
            print("  [GRAY] 資料家底下沒有正典庫 vdf_tw_market / vdf_global_market(這台只看 parquet)")
        return {"GREEN": 0, "GRAY": 2}.get(r["lamp"], 1)
    r = export(pq_dir or home, _opt(args, "--to") or "")
    print("[%s] parquet export %s · %s(%s)· 複製 %d · 沿用 %d · 錯 %d · MCP 待上傳 %s" % (
        TAG, r["lamp"], r.get("to", "—"), r.get("why"), len(r.get("copied", [])), len(r.get("skipped", [])), len(r.get("errors", [])), r.get("to_upload", "—")))
    for e in r.get("errors", []):
        print("  [錯] %s" % e)
    return {"GREEN": 0, "GRAY": 2}.get(r["lamp"], 1)


# ---------------------------------------------------------------- 自測(暫存夾 · 假正典庫 · 零網路)
def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    duckdb = _duck()
    with tempfile.TemporaryDirectory() as td:
        h = Path(td) / "vdf_database"
        (h / "output_hub" / "mega").mkdir(parents=True)
        tw, gl = h / "output_hub" / "mega" / "vdf_tw_market.duckdb", h / "output_hub" / "mega" / "vdf_global_market.duckdb"
        c = duckdb.connect(str(tw))
        c.execute("CREATE TABLE tw_daily_prices AS SELECT strftime(DATE '2026-11-02' + INTERVAL (i // 3) DAY, '%Y-%m-%d') AS date, "
                  "['2330', '2317', '6488'][i % 3 + 1] AS ticker, 100.0 + i AS close FROM range(12) t(i)")
        c.execute("INSERT INTO tw_daily_prices VALUES ('2026-11-02', '2330', 100.0)")          # 來源自己重複一列
        c.execute("CREATE TABLE tw_monthly_revenue(code VARCHAR, ym VARCHAR, revenue BIGINT, fetched_at TIMESTAMP)")
        c.execute("INSERT INTO tw_monthly_revenue VALUES ('2330', '2026-09', 10, TIMESTAMP '2026-10-10 00:00:00'), ('2330', '2026-10', 11, TIMESTAMP '2026-11-10 00:00:00'),"
                  " ('2317', '2026-10', NULL, TIMESTAMP '2026-11-10 00:00:00')")
        c.execute("CREATE TABLE tw_listings(code VARCHAR PRIMARY KEY, name VARCHAR)")
        c.execute("INSERT INTO tw_listings VALUES ('2330', '台積電'), ('6488', '環球晶')")
        c.close()
        c = duckdb.connect(str(gl))
        c.execute("CREATE TABLE us_macro(date DATE, series VARCHAR, value DOUBLE, fetched_at TIMESTAMP)")
        c.execute("INSERT INTO us_macro VALUES (DATE '2026-11-03', 'DGS10', 4.1, now()), (DATE '2026-11-04', 'DGS10', 4.2, now())")
        c.close()
        chk("① 資料家:--home > env > 冊;找到正典庫(mega 下的 vdf_tw_market / vdf_global_market)",
            resolve_home(str(h))[0] == h and resolve_home(None, {"VIA_VDF_DB_HOME": str(h)})[0] == h and set(find_dbs(h)) == set(PROTO))
        k1, r1 = pick_key(["date", "ticker", "close"])
        k2, r2 = pick_key(["code", "ym", "revenue", "fetched_at"])
        k3, _r3 = pick_key(["code", "name"], ["code"])
        chk("② 鍵律:協定 date+ticker · 內容鍵扣 fetched_at · 宣告主鍵優先", k1 == ["date", "ticker"] and k2 == ["code", "ym", "revenue"] and k3 == ["code"], (k1, k2, k3))
        r = sync(h)
        res = {x["table"]: x for x in r["results"]}
        con = duckdb.connect()
        n_px = con.execute("SELECT COUNT(*) FROM read_parquet(%s)" % _lit(h / "tw__tw_daily_prices.parquet")).fetchone()[0]
        chk("③ 第一次 sync:四表新建 tw__ / gl__ 檔 · 來源重複列只收一次(12 列)· 清單 + DuckDB 目錄寫好",
            r["lamp"] == "GREEN" and r["written"] == 4 and n_px == 12 and (h / MANIFEST).is_file() and (h / CATALOG).is_file()
            and all((h / f).is_file() for f in ("tw__tw_daily_prices.parquet", "tw__tw_monthly_revenue.parquet", "tw__tw_listings.parquet", "gl__us_macro.parquet")), r)
        m1 = {f: (h / f).stat().st_mtime_ns for f in os.listdir(h) if f.endswith(".parquet")}
        r = sync(h)
        m2 = {f: (h / f).stat().st_mtime_ns for f in os.listdir(h) if f.endswith(".parquet")}
        chk("④ 重跑 sync:沒新鍵 = 4 檔都不動(修改時間不變 · 雲端不重傳)", r["written"] == 0 and r["unchanged"] == 4 and m1 == m2, r["results"])
        c = duckdb.connect(str(tw))
        c.execute("INSERT INTO tw_daily_prices VALUES ('2026-11-06', '2330', 200.0), ('2026-11-06', '2317', 201.0), ('2026-11-02', '2330', 999.0)")
        c.execute("INSERT INTO tw_monthly_revenue VALUES ('2330', '2026-10', 11, TIMESTAMP '2026-11-12 00:00:00'), ('2317', '2026-10', NULL, TIMESTAMP '2026-11-12 00:00:00')")
        c.close()
        c = duckdb.connect(str(gl))
        c.execute("INSERT INTO us_macro VALUES (DATE '2026-11-04', 'DGS10', 4.2, now())")
        c.close()
        r = sync(h)
        res = {x["table"]: x for x in r["results"]}
        n_px = con.execute("SELECT COUNT(*) FROM read_parquet(%s)" % _lit(h / "tw__tw_daily_prices.parquet")).fetchone()[0]
        n_rv = con.execute("SELECT COUNT(*) FROM read_parquet(%s)" % _lit(h / "tw__tw_monthly_revenue.parquet")).fetchone()[0]
        chk("⑤ 增量:只補 2 個新鍵(同鍵改值不重複寫)· 月營收重抓(只差 fetched_at · NULL 值)不算新列 · 美國總經同列重抓不寫",
            res["tw_daily_prices"]["added"] == 2 and n_px == 14 and res["tw_monthly_revenue"]["action"] == "沒新鍵 · 不動檔" and n_rv == 3
            and res["us_macro"]["action"] == "沒新鍵 · 不動檔", res)
        st = status(h, today=date(2026, 11, 9))
        sr = {x["file"]: x for x in st["rows"]}
        chk("⑥ status:列 · 重複 0 · 日期範圍 · 頻率(日 / 月)· 正典庫同表對列(16 = 含來源自己的重複 + 改值列)· 該到日 = 前一個平日",
            sr["tw__tw_daily_prices.parquet"]["pq"]["rows"] == 14 and sr["tw__tw_daily_prices.parquet"]["pq"]["dups"] == 0
            and sr["tw__tw_daily_prices.parquet"]["pq"]["cadence"] == "日" and sr["tw__tw_monthly_revenue.parquet"]["pq"]["cadence"] == "月"
            and sr["tw__tw_daily_prices.parquet"]["src"]["rows"] == 16 and sr["tw__tw_daily_prices.parquet"]["due"] == "2026-11-06", sr["tw__tw_daily_prices.parquet"])
        st2 = status(h, today=date(2026, 11, 12))
        pl = plan(st2, {("vdf_tw_market.duckdb", "tw_daily_prices"): ["VDF_ENG073"], ("vdf_global_market.duckdb", "us_macro"): []})
        pa = {i["table"]: i for i in pl["items"]}
        chk("⑦ 不重複擷取計畫:日價落後 → 要擷取(列寫入引擎)· 月營收 2026-10 已到 → 跳過 · 主檔快照 → 不判 · 沒登寫入者照列",
            pa["tw_daily_prices"]["action"] == "要擷取" and pa["tw_daily_prices"]["writers"] and pa["tw_monthly_revenue"]["action"] == "已最新 · 跳過"
            and pa["tw_listings"]["action"] == "不判" and "us_macro" in pl["no_writer"], pl)
        c = duckdb.connect(str(tw))
        c.execute("CREATE TABLE tw_chip_inst AS SELECT DATE '2026-11-05' AS date, '2330' AS code, 5 AS net")
        c.close()
        c = duckdb.connect(str(tw), read_only=True)
        st3 = status(h, today=date(2026, 11, 9))
        pl3 = plan(st3, {})
        c.close()
        chk("⑧ 正典庫有新表 parquet 還沒有 → 黃『parquet sync 會建』· 計畫『只要 sync』不重抓",
            any(x["file"] == "tw__tw_chip_inst.parquet" and x["lamp"] == "YELLOW" and x["pq"] is None for x in st3["rows"])
            and {i["table"]: i for i in pl3["items"]}["tw_chip_inst"]["action"] == "只要 sync", [x for x in st3["rows"] if x["table"] == "tw_chip_inst"])
        # 既有 parquet 帶重複鍵 → --dedup 收掉
        con.execute("COPY (SELECT * FROM read_parquet(%s) UNION ALL SELECT * FROM read_parquet(%s) WHERE ticker = '2330') TO %s (FORMAT PARQUET)" % (
            _lit(h / "tw__tw_daily_prices.parquet"), _lit(h / "tw__tw_daily_prices.parquet"), _lit(h / "dup.parquet")))
        os.replace(h / "dup.parquet", h / "tw__tw_daily_prices.parquet")
        dn = status(h, today=date(2026, 11, 9))
        d1 = {x["file"]: x for x in dn["rows"]}["tw__tw_daily_prices.parquet"]["pq"]["dups"]
        r = sync(h, only=["tw_daily_prices"], dedup=True)
        d2 = {x["file"]: x for x in status(h, today=date(2026, 11, 9))["rows"]}["tw__tw_daily_prices.parquet"]["pq"]
        chk("⑨ 既有檔有重複鍵 → status 黃 · sync --dedup 收掉(14 列 · 重複 0)", d1 > 0 and d2["dups"] == 0 and d2["rows"] == 14, (d1, d2, r["results"]))
        # 匯出:PC 夾 + 假 Google 同步夾;第二次只複製變了的
        r = sync(h)
        pc, gd = Path(td) / "pc_out", Path(td) / "gdrive"
        gd.mkdir()
        e1 = export(h, str(pc))
        e2 = export(h, "gdrive", env={"VIA_GDRIVE_DIR": str(gd)})
        e3 = export(h, str(pc))
        mcp = json.loads((pc / MCP_NAME).read_text(encoding="utf-8"))
        sha_ok = all(_sha256(pc / f["file"]) == f["sha256"] for f in mcp["files"])
        (pc / MCP_DONE).write_text(json.dumps({f["file"]: f["sha256"] for f in mcp["files"]}), encoding="utf-8")
        e4 = export(h, str(pc))
        c = duckdb.connect(str(tw))
        c.execute("INSERT INTO tw_daily_prices VALUES ('2026-11-09', '2330', 300.0)")
        c.close()
        sync(h)
        e5 = export(h, str(pc))
        mcp5 = json.loads((pc / MCP_NAME).read_text(encoding="utf-8"))
        chk("⑩ 匯出:PC 夾 / Google 同步夾各複製 5 檔 + 清單 + MCP 交接清單 · 再匯出 0 複製 5 沿用 · sha256 一致 ·"
            " MCP 端寫回已上傳 → 待上傳 0 · 之後只改 1 檔 → 只複製 1 檔、只列 1 檔待上傳",
            len(e1["copied"]) == 5 and len(e2["copied"]) == 5 and (gd / "VDF_ParquetDB" / MCP_NAME).is_file() and not e3["copied"] and len(e3["skipped"]) == 5
            and sha_ok and "金鑰" in mcp["how"] and e4["to_upload"] == 0
            and e5["copied"] == ["tw__tw_daily_prices.parquet"] and [f["file"] for f in mcp5["files"] if f["upload"]] == ["tw__tw_daily_prices.parquet"],
            (len(e1["copied"]), len(e2["copied"]), e3["copied"], e4["to_upload"], e5["copied"], [f["file"] for f in mcp5["files"] if f["upload"]]))
        chk("⑪ 匯出防呆:沒給目的地 / 找不到同步夾 / 目的地 = 資料家 → 不寫",
            export(h, "")["lamp"] == "RED" and export(h, "dropbox", env={}, home_dir=Path(td) / "nohome")["lamp"] == "RED" and export(h, str(h))["lamp"] == "RED")
        # 清單輸入閘
        lh = Path(td) / "fetch"
        (lh / "0-1-TWStockList").mkdir(parents=True)
        (lh / "0-2-ActiveETFList").mkdir(parents=True)
        con.execute("COPY (SELECT * FROM (VALUES ('2026-11-14', '2330', '2330.TW', 'TWSE', 'ACTIVE'), ('2026-11-14', '6488', '6488.TWO', 'TPEx', 'ACTIVE')) "
                    "t(date, ticker, yf_ticker, market, status)) TO %s (FORMAT PARQUET)" % _lit(lh / "0-1-TWStockList" / "tw_stock_list_latest.parquet"))
        con.execute("COPY (SELECT * FROM (VALUES ('2026-11-14', '00981A', '00981A.TW', 'TWSE', 'ACTIVE', true)) t(date, ticker, yf_ticker, market, status, domestic)) "
                    "TO %s (FORMAT PARQUET)" % _lit(lh / "0-2-ActiveETFList" / "active_etf_list_latest.parquet"))
        for sub in ("0-1-TWStockList", "0-2-ActiveETFList"):
            (lh / sub / "verify_report.json").write_text(json.dumps({"engine": "fixture", "date": "2026-11-14", "lamp": "GREEN", "checks": []}), encoding="utf-8")
        (lh / "0-2-ActiveETFList" / "active_etf_qualified_latest.csv").write_text("date,ticker,qualified,reason\n2026-11-14,00981A,True,ok\n", encoding="utf-8")
        g1 = inputs(None, str(lh), date(2026, 11, 15))
        con.execute("COPY (SELECT * FROM (VALUES ('2026-11-14', '6488', '6488.TW', 'TPEx', 'ACTIVE'), ('2026-11-14', '6488', '6488.TWO', 'TPEx', 'ACTIVE')) "
                    "t(date, ticker, yf_ticker, market, status)) TO %s (FORMAT PARQUET)" % _lit(lh / "0-1-TWStockList" / "tw_stock_list_latest.parquet"))
        (lh / "0-2-ActiveETFList" / "active_etf_qualified_latest.csv").unlink()
        g2 = inputs(None, str(lh), date(2026, 11, 15))
        bad = {c["id"] for c in g2["lists"]["stock"]["checks"] if c["lamp"] == "RED"} | {"Q1" for c in g2["lists"]["etf"]["checks"] if c["id"] == "Q1" and c["lamp"] == "RED"}
        g3 = inputs(None, str(lh), date(2026, 12, 30))
        chk("⑫ 清單輸入閘:乾淨清單 GREEN · 上櫃配 .TW / 重號 / 合格判定不在 → RED · 清單 46 天前 → C4 RED",
            g1["lamp"] == "GREEN" and g2["lamp"] == "RED" and {"C2", "C3", "Q1"} <= bad
            and any(c["id"] == "C4" and c["lamp"] == "RED" for c in g3["lists"]["etf"]["checks"]), (g1["lamp"], bad))
        rxs, rxs_src = shared_rx("stock")
        rxe, rxe_src = shared_rx("etf")
        pm, pm_src = load_params()
        chk("⑯ 共用代碼律從原定義檔 AST 讀(台股 MDL009 SSOT_STOCK_RX · 主動式 ETF ENG077 A_CODE · 不另寫)· 參數冊 VDF 自己留存且與內建同值",
            "SSOT_STOCK_RX" in rxs_src and "A_CODE" in rxe_src and rxs.match("2330") and not rxs.match("0050") and rxe.match("00981A")
            and pm["protocol"] == PROTO and sorted(pm["volatile_columns"]) == sorted(VOLATILE) and pm_src.startswith("VDF_DataPlane_SSOT_v"), (rxs_src, rxe_src, pm_src))
        sc = scope(str(h), str(lh), date(2026, 11, 15), root=Path(td) / "via", env={})
        rp = write_reports(sc, None, root=Path(td) / "via")
        pg = Path(rp["html"]).read_text(encoding="utf-8")
        chk("⑬ 管理範圍:六項(輸入 · 擷取 · 正典庫 · parquet · 匯出 · 整合)各一燈 · 匯出看得到 PC / Google 兩處 · 頁面三行標頭 · 不載外部腳本",
            [i["id"] for i in sc["items"]] == ["S1", "S2", "S3", "S4", "S5", "S6"] and sc["items"][4]["lamp"] == "GREEN" and "gdrive" in sc["items"][4]["evidence"]
            and "VERITAS INTELLIGENCE ANALYTICS" in pg and 'content="VDF_SCOPE"' in pg[:300] and "<script" not in pg.lower(), [(i["id"], i["lamp"]) for i in sc["items"]])
        os.environ.pop("VIA_FROM_VDFSM", None)
        keep = os.environ.pop("VIA_FROM_VCGC", None)
        try:
            rc_w = main(["parquet", "sync", "--home", str(h)])
        finally:
            if keep is not None:
                os.environ["VIA_FROM_VCGC"] = keep
        chk("⑭ 寫入動詞沒入口旗標 → 拒絕(rc 2)· 給的資料家不在 → 不寫(照實說不在)",
            rc_w == 2 and resolve_home(str(Path(td) / "nope"))[0] is None and "不在" in resolve_home(str(Path(td) / "nope"))[1], rc_w)
        con.close()
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑮ 獨立:不匯入他系統 · 不碰 TA-Lib · 不讀寫同意閘 · 正典庫只唯讀掛 · 兩座橋在",
        not re.search(r"^\s*(import|from)\s+(talib|CGC_|VRN_|VRN2_|VQG_|VAP_|VCGC)", text, re.M) and "(READ_ONLY)" in text
        and "[VIA:ACCEL-BRIDGE:v0100]" in text and "[VIA:NET-BRIDGE:v0100]" in text and "os.environ[\"VIA_NET_CONSENT\"]" not in text)
    n = sum(ok)
    print("[計] %s 自測 %d/%d · %s" % (TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    return 0 if n == len(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
