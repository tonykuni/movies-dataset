#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_ENG079_LocalDbConsolidate v0100 — 本機三庫整併入正典 DuckDB 引擎(批383)
====================================================================
操作員令(批383):「vdf 要將資料庫存入;之前有的資料庫能把它整理好,抓過的資料不必再抓」
本機三庫:C:\\新增資料夾\\新增資料夾\\VIA_db_part1_prices(價量)/VIA_db_part2_chips(籌碼)/
VIA_db_part3_rest(其餘;鍵 kind,ticker,obs_date)。
機制(Zero-Hydra=全複用正主 ENG064/ENG065 的鍵律與 anti-join 律):
  ① scan   唯讀盤點:三庫檔(parquet/csv/tsv/duckdb/sqlite;xlsx 誠實列「未支援→轉 csv」)→ 欄位偵測
           (date/ticker/OHLCV/kind 別名表)→ 路由計畫(目標表·鍵·票代碼風格·預估列·新增列=anti-join
           計數不寫)→ VIA_Reports/vdf/local_db/RUN_latest.json(mode=scan)
  ② run    預設 dry-run(=scan);--apply 才 INSERT:COPY_ONLY(原件不刪不搬)+ anti-join 只補缺鍵
           (既有列零觸碰=正本律;重跑冪等 0 新增)+ 台帳 via_ingest_ledger(檔指紋已入冊=跳過,
           「抓過/整併過的不再做」)
  ③ 路由律:px  date+ticker+close → tw_daily_prices(ENG064 鍵 (date,ticker);date VARCHAR 'YYYY-MM-DD';
                ticker=yahoo 風格 1101.TW/.TWO(批307 鍵律);裸碼經 tw_listings(表/mega csv)對映;
                對不到=誠實入 local_px_daily 暫存(--assume-twse 才視為 .TW);非台股碼 → global_daily)
           chip date+ticker → tw_chips_daily(鍵 date,ticker[,kind];欄位聯集只增)
           rest date+ticker → tw_rest_daily(鍵 date,ticker,kind;kind 缺=以檔名 stem 補)
           其餘無鍵 → local_<part>__<stem>(EXCEPT 集合 anti-join;ENG065 律)
           ENG065 檔名協定(批389 工作站實錄:part3_rest 的 tw__tw_listings/gl__us_macro 等曾落 local_rest__<stem>):
                stem tw__<table> → vdf_tw_market 同名正典表;gl__<table> → vdf_global_market 同名正典表(跨庫經臨時 parquet 搬運);
                零改名零轉型(同 ENG065 律)· 共同欄交集 · 表缺=依來源建 · date+ticker 皆在=鍵 anti-join(ENG064 律)否則 EXCEPT;
                台帳鍵=指紋|單元|目標表 → 改路由後同檔自動重做(舊 local_rest__* 表只增不減留存;不需 --force)
  ⑦ 資料家接點燈(批389;MDL123 正本):正典庫在倉內 output_hub 且接點非 LINKED → YELLOW「庫困在 worktree」
           → via-datahome link 後重跑 run --apply(冪等只補缺鍵);--db 自訂路徑=不適用
  ④ ckpt   ENG064 --rebuild-ckpt(段內有列即 done)=整併後歷史回補引擎不再重抓已有年段/檔
  ⑤ need   覆蓋缺口(月粒度:(ticker,月) 有列=已抓;缺=待抓;只列缺的)→ NEED_latest.json;抓取只抓缺口
  ⑥ coverage 每表 ticker×年覆蓋摘要 → COVERAGE_latest.json
紀律:只增不減;原件零觸碰;誠實三態(GREEN/YELLOW/RED;缺 src/缺 duckdb 誠實 RED 不假綠);零網路;
      尾版律(ENG064 glob 尾版);正典庫=ENG064/ENG065 同路徑 output_hub/mega(MDL123 接點→本機資料家)。
用法:python3 VDF_ENG079_LocalDbConsolidate_v0100.py scan [--src DIR] [--db PATH] [--only px,chip,rest] [--json]
      | run [--apply] [--src DIR] [--db PATH] [--only …] [--assume-twse] [--force]
      | ckpt | need [--table T] [--start S] [--end E] [--tickers a,b] [--json] | coverage [--json] | --selftest
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

import datetime as _dt
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent.parent
MEGA = VIA / "functional modules" / "VDF" / "output_hub" / "mega"
DB_TW = MEGA / "vdf_tw_market.duckdb"
DB_GL = MEGA / "vdf_global_market.duckdb"
REPORTS = VIA / "VIA_Reports" / "vdf" / "local_db"
LOG = VIA / "logs" / "vdf_local_db.log"
SRC_DEFAULT = r"C:\新增資料夾\新增資料夾"
PARTS = (("px", "VIA_db_part1_prices"), ("chip", "VIA_db_part2_chips"), ("rest", "VIA_db_part3_rest"))
LEDGER = "via_ingest_ledger"
TARGETS = {"px": "tw_daily_prices", "chip": "tw_chips_daily", "rest": "tw_rest_daily", "px_unmapped": "local_px_daily", "gl": "global_daily"}
PROTOCOL_RX = re.compile(r"^(tw|gl)__(.+)$")   # ENG065 檔名協定(批389):tw__<table>/gl__<table>
OUTPUT_HUB = VIA / "functional modules" / "VDF" / "output_hub"
PRICE_COLS = ["date", "ticker", "open", "high", "low", "close", "adj_close", "volume"]

# 欄位別名表(小寫比對;零發明:ENG064 鍵 date/ticker;Grok 湖鍵 obs_date;台股常見中文欄)
ALIASES = {
    "date": ["date", "obs_date", "trade_date", "tradedate", "as_of", "asof", "datetime", "dt", "time", "日期", "交易日"],
    "ticker": ["ticker", "symbol", "code", "stock_id", "stockid", "stock_code", "sid", "yf_ticker", "證券代號", "股票代號", "代號", "股票代碼"],
    "open": ["open", "開盤價", "開盤"],
    "high": ["high", "最高價", "最高"],
    "low": ["low", "最低價", "最低"],
    "close": ["close", "收盤價", "收盤", "price"],
    "adj_close": ["adj_close", "adj close", "adjclose", "adjusted_close", "adjusted", "還原價", "還原收盤價"],
    "volume": ["volume", "vol", "成交量", "成交股數", "成交量(股)", "turnover_shares"],
    "kind": ["kind", "type", "item", "category", "field", "項目", "類別"],
}
TW_CODE = re.compile(r"^\d{4}[A-Z0-9]{0,2}$")
YF_TW = re.compile(r"^\d{4}[A-Z0-9]{0,2}\.(TW|TWO)$")


# ---------------------------------------------------------------- 基礎
def _ts() -> str:
    return _dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def _q(s: str) -> str:
    return "'" + str(s).replace("'", "''") + "'"


def _qi(c: str) -> str:
    return '"' + str(c).replace('"', '""') + '"'


def _u(p) -> str:
    return str(p).replace("\\", "/")


def log_event(kind: str, msg: str, **kw) -> None:
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": _dt.datetime.now().isoformat(timespec="seconds"), "kind": kind, "msg": msg, **kw}, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _write_json(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, p)


def _duckdb():
    try:
        import duckdb
        return duckdb
    except Exception:
        return None


def _connect(db: Path, read_only: bool = False, retries: int = 6, wait: float = 3.0):
    """讓庫律(ENG064 v0105):單寫者鎖=短等重試;逾額誠實 RuntimeError"""
    duckdb = _duckdb()
    if duckdb is None:
        raise RuntimeError("duckdb 缺(於 via_vdf_312 境跑:via-vdfdb;或 via-envgov apply --approve --only-kind REPAIR_BASE)")
    if read_only and not db.exists():
        raise RuntimeError(f"庫缺 {db}")
    db.parent.mkdir(parents=True, exist_ok=True)
    last = ""
    for i in range(retries):
        try:
            return duckdb.connect(str(db), read_only=read_only)
        except duckdb.IOException as exc:
            last = str(exc)
            if "lock" not in last.lower() and "already open" not in last and "Cannot open" not in last:
                raise
            print(f"  [庫忙] {i + 1}/{retries}:{last.splitlines()[-1][:90]} → 等 {wait}s", flush=True)
            time.sleep(wait)
    raise RuntimeError(f"庫忙逾 {retries}×{wait}s:{last[:200]}")


def fingerprint(p: Path) -> str:
    """檔指紋=大小+mtime+頭尾各 4MB sha256(大 parquet 秒級;同檔重跑=已入冊跳過)"""
    st = p.stat()
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        h.update(fh.read(4 << 20))
        if st.st_size > (8 << 20):
            fh.seek(-(4 << 20), os.SEEK_END)
            h.update(fh.read(4 << 20))
    return f"{st.st_size}:{int(st.st_mtime)}:{h.hexdigest()[:24]}"


# ---------------------------------------------------------------- 欄位偵測/正規化
def _alias(cols: list, key: str) -> str | None:
    low = {c.lower().strip(): c for c in cols}
    for a in ALIASES[key]:
        if a in low:
            return low[a]
    return None


def detect(cols: list) -> dict:
    return {k: _alias(cols, k) for k in ALIASES}


def date_expr(col: str, dtype: str) -> str:
    """任意日期型 → 'YYYY-MM-DD' VARCHAR(DATE/TIMESTAMP 直轉;VARCHAR 多格式;整數 20230105)"""
    c = _qi(col)
    t = (dtype or "").upper()
    if t.startswith("DATE") or t.startswith("TIMESTAMP"):
        return f"strftime(TRY_CAST({c} AS DATE), '%Y-%m-%d')"
    if any(x in t for x in ("INT", "BIGINT", "HUGEINT", "DOUBLE", "DECIMAL", "FLOAT")):
        return f"strftime(TRY_STRPTIME(CAST(CAST({c} AS BIGINT) AS VARCHAR), '%Y%m%d'), '%Y-%m-%d')"
    return (f"strftime(COALESCE(TRY_CAST({c} AS DATE), TRY_CAST(TRY_CAST({c} AS TIMESTAMP) AS DATE), "
            f"TRY_STRPTIME(CAST({c} AS VARCHAR), '%Y%m%d'), TRY_STRPTIME(CAST({c} AS VARCHAR), '%Y/%m/%d')), '%Y-%m-%d')")


def ticker_expr(col: str) -> str:
    c = _qi(col)
    return f"upper(regexp_replace(trim(CAST({c} AS VARCHAR)), '\\.0$', ''))"


# ---------------------------------------------------------------- 來源列舉
def enumerate_sources(src_root: Path, only: set | None = None) -> tuple[list, list]:
    """三庫檔 → 來源單元(檔或庫內表);回 (units, notes)"""
    units, notes = [], []
    for part, folder in PARTS:
        if only and part not in only:
            continue
        d = src_root / folder
        if not d.exists():
            notes.append({"part": part, "lamp": "RED", "note": f"缺 {d}"})
            continue
        files = sorted(p for p in d.rglob("*") if p.is_file())
        n_x = 0
        for f in files:
            ext = f.suffix.lower()
            if ext in (".parquet", ".pq"):
                units.append({"part": part, "path": str(f), "unit": f.name, "kind": "parquet", "src": f"read_parquet({_q(_u(f))})"})
            elif ext in (".csv", ".tsv"):
                units.append({"part": part, "path": str(f), "unit": f.name, "kind": "csv",
                              "src": f"read_csv_auto({_q(_u(f))}, header=true, all_varchar=false)"})
            elif ext in (".duckdb", ".db", ".sqlite", ".sqlite3"):
                units.append({"part": part, "path": str(f), "unit": f.name, "kind": "duckdb" if ext in (".duckdb", ".db") else "sqlite", "src": ""})
            elif ext in (".xlsx", ".xls"):
                n_x += 1
        if n_x:
            notes.append({"part": part, "lamp": "YELLOW", "note": f"xlsx {n_x} 檔未支援(誠實;請另存 csv 後再 scan)"})
        notes.append({"part": part, "lamp": "GREEN", "note": f"{d.name}:檔 {len(files)} · 單元 {sum(1 for u in units if u['part'] == part)}"})
    return units, notes


def expand_db_units(con, units: list) -> list:
    """duckdb/sqlite 檔 → 逐表單元(ATTACH 唯讀;sqlite 需擴充,缺=誠實 SKIP)"""
    out = []
    for i, u in enumerate(units):
        if u["kind"] not in ("duckdb", "sqlite"):
            out.append(u)
            continue
        alias = f"src{i}"
        try:
            if u["kind"] == "sqlite":
                con.execute(f"ATTACH {_q(_u(u['path']))} AS {alias} (TYPE SQLITE, READ_ONLY)")
            else:
                con.execute(f"ATTACH {_q(_u(u['path']))} AS {alias} (READ_ONLY)")
            tabs = [r[0] for r in con.execute(f"SELECT table_name FROM information_schema.tables WHERE table_catalog = {_q(alias)} AND table_schema = 'main'").fetchall()]
            for t in tabs:
                out.append({**u, "unit": f"{u['unit']}::{t}", "src": f"{alias}.main.{_qi(t)}", "attached": alias})
            if not tabs:
                out.append({**u, "state": "SKIP", "note": "庫內無表"})
        except Exception as exc:
            out.append({**u, "state": "SKIP", "note": f"ATTACH 失敗(sqlite 擴充缺?):{str(exc)[:80]}"})
    return out


def _ledger_ensure(con) -> None:
    con.execute(f"CREATE TABLE IF NOT EXISTS {LEDGER}(run_id VARCHAR, ts VARCHAR, part VARCHAR, unit VARCHAR, path VARCHAR, fingerprint VARCHAR, "
                f"target_table VARCHAR, rows_src BIGINT, rows_new BIGINT, note VARCHAR)")


def _ledger_done(con) -> set:
    """已入冊鍵=指紋|單元|目標表(批389:改路由後同檔自動重做;舊路由入冊不擋新目標表)"""
    try:
        return {r[0] for r in con.execute(f"SELECT DISTINCT fingerprint || '|' || unit || '|' || COALESCE(target_table, '') FROM {LEDGER} WHERE rows_new IS NOT NULL").fetchall()}
    except Exception:
        return set()


def listings_map(con, mega: Path) -> dict:
    """裸碼 → yahoo 票(批307 鍵律):tw_listings 表 > tw_listings_industry(code,market)> mega/tw_listings_*.csv;零發明"""
    m = {}
    have = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
    try:
        if "tw_listings" in have:
            cols = [r[0].lower() for r in con.execute('DESCRIBE "tw_listings"').fetchall()]
            if "code" in cols and "yf_ticker" in cols:
                m.update({str(r[0]): str(r[1]) for r in con.execute('SELECT code, yf_ticker FROM "tw_listings" WHERE yf_ticker IS NOT NULL').fetchall()})
            elif "code" in cols and "market" in cols:
                m.update({str(r[0]): str(r[0]) + (".TW" if str(r[1]).upper() == "TWSE" else ".TWO") for r in con.execute('SELECT code, market FROM "tw_listings"').fetchall()})
        if not m and "tw_listings_industry" in have:
            m.update({str(r[0]): str(r[0]) + (".TW" if str(r[1]).upper() == "TWSE" else ".TWO") for r in con.execute('SELECT code, market FROM "tw_listings_industry"').fetchall()})
    except Exception:
        pass
    if not m and mega.exists():
        hits = sorted(mega.glob("tw_listings_*.csv"))
        if hits:
            try:
                rows = con.execute(f"SELECT code, market, yf_ticker FROM read_csv_auto({_q(_u(hits[-1]))}, header=true, all_varchar=true)").fetchall()
                m.update({str(r[0]).lstrip("\ufeff"): (str(r[2]) if r[2] else str(r[0]) + (".TW" if str(r[1]).upper() == "TWSE" else ".TWO")) for r in rows})
            except Exception:
                pass
    return m


def target_style(con, table: str) -> str:
    """既有目標表票風格偵測(yahoo=1101.TW/.TWO;bare=1101;none=表缺/空)"""
    have = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
    if table not in have:
        return "none"
    rows = con.execute(f"SELECT ticker FROM {_qi(table)} WHERE ticker IS NOT NULL AND ticker <> '_NOOP_' LIMIT 200").fetchall()
    if not rows:
        return "none"
    yf = sum(1 for r in rows if YF_TW.match(str(r[0])))
    return "yahoo" if yf * 2 >= len(rows) else "bare"


# ---------------------------------------------------------------- 路由/正規化視圖
def _norm_view(con, u: dict, det: dict, types: dict, lst: dict, assume_twse: bool, style: str, proto: bool = False) -> tuple[str, list]:
    """建臨時正規化視圖 _src_norm(date 'YYYY-MM-DD' VARCHAR;ticker 正規;其餘欄小寫);回 (視圖名, 欄清單)
    proto=True(ENG065 協定檔):零改名零轉型原樣物化(同 ENG065 律;欄名/欄型與正典表一致)"""
    if proto:
        con.execute(f"CREATE OR REPLACE TEMP TABLE _src_norm AS SELECT * FROM {u['src']}")
        return "_src_norm", [r[0] for r in con.execute("DESCRIBE _src_norm").fetchall()]
    sel = []
    used = set()
    if det.get("date"):
        sel.append(f"{date_expr(det['date'], types.get(det['date'], ''))} AS date")
        used.add(det["date"])
    if det.get("ticker"):
        t = ticker_expr(det["ticker"])
        if u["part"] == "px" and style != "bare":
            con.execute("CREATE OR REPLACE TEMP TABLE _lst(code VARCHAR, yf VARCHAR)")
            if lst:
                con.executemany("INSERT INTO _lst VALUES (?, ?)", list(lst.items()))
            # 裸台股碼 → 對映 yahoo;已 yahoo 風格保留;對不到=NULL 標記(--assume-twse 視為 .TW)
            fallback = f"{t} || '.TW'" if assume_twse else "NULL"
            sel.append(f"CASE WHEN regexp_matches({t}, '^[0-9]{{4}}[A-Z0-9]{{0,2}}\\.(TW|TWO)$') THEN {t} "
                       f"WHEN regexp_matches({t}, '^[0-9]{{4}}[A-Z0-9]{{0,2}}$') THEN COALESCE((SELECT yf FROM _lst WHERE code = {t} LIMIT 1), {fallback}) "
                       f"ELSE {t} END AS ticker")
            sel.append(f"{t} AS ticker_raw")
        else:
            sel.append(f"{t} AS ticker")
        used.add(det["ticker"])
    for k in ("open", "high", "low", "close", "adj_close", "volume"):
        if det.get(k) and u["part"] == "px":
            sel.append(f"TRY_CAST({_qi(det[k])} AS DOUBLE) AS {k}")
            used.add(det[k])
    if det.get("kind") and u["part"] in ("rest", "chip"):
        sel.append(f"CAST({_qi(det['kind'])} AS VARCHAR) AS kind")
        used.add(det["kind"])
    elif u["part"] == "rest":
        sel.append(f"{_q(Path(u['unit']).stem.split('::')[-1])} AS kind")
    for c in types:
        if c in used:
            continue
        cn = re.sub(r"[^0-9a-zA-Z_\u4e00-\u9fff]+", "_", c.strip().lower()).strip("_") or "col"
        if cn in ("date", "ticker", "kind", "ticker_raw") or any(s.endswith(f" AS {cn}") for s in sel):
            cn = cn + "_src"
        if u["part"] == "px" and cn not in PRICE_COLS:
            continue  # 價表只入 ENG064 八欄(其餘欄不污染正典價表)
        sel.append(f"{_qi(c)} AS {_qi(cn)}")
    # 物化為臨時表(一次掃來源;anti-join 計數+寫入共用;視圖遞迴綁定之忌)
    con.execute(f"CREATE OR REPLACE TEMP TABLE _src_norm AS SELECT {', '.join(sel)} FROM {u['src']}")
    cols = [r[0] for r in con.execute("DESCRIBE _src_norm").fetchall()]
    return "_src_norm", cols


def protocol_target(u: dict) -> tuple[str, str] | None:
    """ENG065 檔名協定(批389):檔 stem tw__<table>/gl__<table> → (庫, 表);庫內表單元/不合協定=None"""
    if "::" in u.get("unit", ""):
        return None
    m = PROTOCOL_RX.match(Path(u["unit"]).stem)
    if not m or not m.group(2).strip():
        return None
    return m.group(1), m.group(2).strip()


def protocol_keys(cols: list) -> list:
    """協定表鍵律:date+ticker 皆在=鍵 anti-join(ENG064 律;kind 在則併入);否則 []=EXCEPT 集合 anti-join(ENG065 律)"""
    if "date" in cols and "ticker" in cols:
        return ["date", "ticker"] + (["kind"] if "kind" in cols else [])
    return []


def _xfer(con_src, con_dst, select_sql: str, name: str = "_src_norm") -> int:
    """跨庫搬運(DuckDB 臨時表不可跨連線):來源庫 COPY → 臨時 parquet → 目標庫臨時表(任意欄型;零 pyarrow 依賴;用畢即刪)"""
    import tempfile
    fd, tmp = tempfile.mkstemp(prefix="via_eng079_xfer_", suffix=".parquet")
    os.close(fd)
    try:
        os.unlink(tmp)
        con_src.execute(f"COPY ({select_sql}) TO {_q(_u(tmp))} (FORMAT PARQUET)")
        con_dst.execute(f"CREATE OR REPLACE TEMP TABLE {name} AS SELECT * FROM read_parquet({_q(_u(tmp))})")
        return con_dst.execute(f"SELECT count(*) FROM {name}").fetchone()[0]
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def datahome_note(db_tw: Path) -> dict | None:
    """資料家接點燈(批389;MDL123 正本 resolve_home/_is_link):正典庫在倉內 output_hub 且接點非 LINKED=YELLOW(庫困在 worktree);
    LINKED=GREEN;--db 自訂路徑或 MDL123 缺=None(不適用)"""
    try:
        if not os.path.normcase(str(db_tw)).startswith(os.path.normcase(str(OUTPUT_HUB))):
            return None
        hits = sorted((VIA / "supportive modules" / "registry").glob("CGC_MDL123_DataHome_v0*.py"))
        if not hits:
            return None
        import importlib.util
        spec = importlib.util.spec_from_file_location("datahome_e079", hits[-1])
        m = importlib.util.module_from_spec(spec)
        sys.modules["datahome_e079"] = m
        spec.loader.exec_module(m)
        home, src = m.resolve_home(VIA)
        rel = "functional modules/VDF/output_hub"
        rp, tgt = VIA / rel, Path(home) / VIA.name / rel
        if m._is_link(rp):
            state = "LINKED" if tgt.exists() else "LINKED_ELSEWHERE"
        else:
            state = "REAL_DIR" if rp.is_dir() else "MISSING"
        if state == "LINKED":
            return {"lamp": "GREEN", "part": "home", "state": state, "home": str(home), "note": f"資料家接點 LINKED → 正典庫寫入本機資料家 {home}({src})"}
        return {"lamp": "YELLOW", "part": "home", "state": state, "home": str(home),
                "note": f"資料家接點 {state}:正典庫落在倉內 output_hub(非資料家 {home};各 worktree 各一份)→ via-datahome status → via-datahome link(倉內庫併入家後接點)→ 重跑 via-vdfdb run --apply(冪等只補缺鍵)"}
    except Exception:
        return None


def route(u: dict, det: dict) -> tuple[str, list]:
    """(目標表, 鍵);ENG065 協定檔另走 protocol_target(批389)"""
    has_dt = bool(det.get("date") and det.get("ticker"))
    if u["part"] == "px" and has_dt and det.get("close"):
        return TARGETS["px"], ["date", "ticker"]
    if u["part"] == "chip" and has_dt:
        return TARGETS["chip"], ["date", "ticker"] + (["kind"] if det.get("kind") else [])
    if u["part"] == "rest" and has_dt:
        return TARGETS["rest"], ["date", "ticker", "kind"]
    stem = re.sub(r"[^0-9a-zA-Z_]+", "_", Path(u["unit"]).stem.split("::")[-1]).strip("_").lower() or "unit"
    return f"local_{u['part']}__{stem}", []


def _ensure_table(con, table: str, cols: list, keys: list, src: str = "_src_norm", union_cols: bool = True) -> list:
    """表缺=依正規化視圖建(價表用 ENG064 八欄);表在=欄位聯集只增(ALTER ADD COLUMN;union_cols=False=只取交集,ENG065 協定律);回可寫欄"""
    have = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
    if table not in have:
        if table in (TARGETS["px"], TARGETS["gl"], TARGETS["px_unmapped"]):
            con.execute(f"CREATE TABLE {_qi(table)}(date VARCHAR, ticker VARCHAR, open DOUBLE, high DOUBLE, low DOUBLE, close DOUBLE, adj_close DOUBLE, volume DOUBLE)")
        else:
            con.execute(f"CREATE TABLE {_qi(table)} AS SELECT * FROM {src} WHERE 1=0")
            if "ticker_raw" in cols:
                con.execute(f"ALTER TABLE {_qi(table)} DROP COLUMN ticker_raw")
    tcols = {r[0]: r[1] for r in con.execute(f"DESCRIBE {_qi(table)}").fetchall()}
    if union_cols and table not in (TARGETS["px"], TARGETS["gl"], TARGETS["px_unmapped"]):
        for c, ty in [(r[0], r[1]) for r in con.execute(f"DESCRIBE {src}").fetchall()]:
            if c not in tcols and c != "ticker_raw":
                con.execute(f"ALTER TABLE {_qi(table)} ADD COLUMN {_qi(c)} {ty}")
                tcols[c] = ty
    writable = [c for c in cols if c in tcols]
    missing_keys = [k for k in keys if k not in tcols]
    if missing_keys:
        raise RuntimeError(f"目標表 {table} 缺鍵欄 {missing_keys}")
    return writable


def _count_new(con, table: str, cols: list, keys: list, where: str = "", src: str = "_src_norm") -> int:
    have = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
    w = f" WHERE {where}" if where else ""
    if table not in have:
        return con.execute(f"SELECT count(*) FROM (SELECT DISTINCT {', '.join(_qi(k) for k in keys) if keys else '*'} FROM {src}{w})").fetchone()[0]
    if keys:
        cond = " AND ".join(f"t.{_qi(k)} IS NOT DISTINCT FROM s.{_qi(k)}" for k in keys)
        return con.execute(f"SELECT count(*) FROM (SELECT DISTINCT {', '.join(_qi(k) for k in keys)} FROM {src}{w}) s "
                           f"WHERE NOT EXISTS (SELECT 1 FROM {_qi(table)} t WHERE {cond})").fetchone()[0]
    sel = ", ".join(_qi(c) for c in cols)
    return con.execute(f"SELECT count(*) FROM (SELECT {sel} FROM {src}{w} EXCEPT SELECT {sel} FROM {_qi(table)})").fetchone()[0]


def _insert_new(con, table: str, cols: list, keys: list, where: str = "", src: str = "_src_norm") -> int:
    before = con.execute(f"SELECT count(*) FROM {_qi(table)}").fetchone()[0]
    sel = ", ".join(_qi(c) for c in cols)
    w = f" WHERE {where}" if where else ""
    if keys:
        pk = ", ".join(_qi(k) for k in keys)
        cond = " AND ".join(f"t.{_qi(k)} IS NOT DISTINCT FROM s.{_qi(k)}" for k in keys)
        # 來源自去重(鍵首列)→ anti-join 只補缺鍵(既有列零觸碰;NULL 安全)
        con.execute(f"INSERT INTO {_qi(table)} ({sel}) SELECT {sel} FROM (SELECT * FROM {src}{w} QUALIFY row_number() OVER (PARTITION BY {pk}) = 1) s "
                    f"WHERE NOT EXISTS (SELECT 1 FROM {_qi(table)} t WHERE {cond})")
    else:
        con.execute(f"INSERT INTO {_qi(table)} ({sel}) (SELECT {sel} FROM {src}{w} EXCEPT SELECT {sel} FROM {_qi(table)})")
    return con.execute(f"SELECT count(*) FROM {_qi(table)}").fetchone()[0] - before


# ---------------------------------------------------------------- 主流程
def consolidate(src_root: Path, db_tw: Path, db_gl: Path | None = None, apply: bool = False, only: set | None = None,
                assume_twse: bool = False, force: bool = False, reports: Path = REPORTS, mega: Path | None = None,
                do_print: bool = True) -> dict:
    run_id = _ts()
    mode = "apply" if apply else "scan"
    rep = {"schema": "VIA.LocalDbConsolidate.v1", "run_id": run_id, "ts": _dt.datetime.now().isoformat(timespec="seconds"), "mode": mode,
           "src_root": str(src_root), "db": str(db_tw), "db_global": str(db_gl) if db_gl else "", "verdict": "GREEN", "notes": [], "units": [],
           "summary": {"files": 0, "units": 0, "planned_new": 0, "rows_new": 0, "skipped_ledger": 0, "unmapped": 0, "failed": 0, "tables": {}}}

    def say(s):
        if do_print:
            print(s, flush=True)

    duckdb = _duckdb()
    if duckdb is None:
        rep["verdict"] = "RED"
        rep["notes"].append({"lamp": "RED", "note": "duckdb 缺=無法讀 parquet/寫正典庫(於 via_vdf_312 境:via-vdfdb;或 REPAIR_BASE)"})
        say("RED     duckdb 缺(via-vdfdb 以 via_vdf_312 python 跑;或 via-envgov apply --approve --only-kind REPAIR_BASE)")
        _finish(rep, reports, do_print)
        return rep
    if not src_root.exists():
        rep["verdict"] = "RED"
        rep["notes"].append({"lamp": "RED", "note": f"本機三庫根缺 {src_root}(--src DIR 或 env VIA_LOCAL_DB_ROOT)"})
        say(f"RED     本機三庫根缺 {src_root}(--src DIR 或 $env:VIA_LOCAL_DB_ROOT)")
        _finish(rep, reports, do_print)
        return rep
    units, notes = enumerate_sources(src_root, only)
    rep["notes"] += notes
    rep["summary"]["files"] = len(units)
    for n in notes:
        say(f"{n['lamp']:<7} {n['part']:<5} {n['note']}")
    dh = datahome_note(db_tw)
    if dh:
        rep["notes"].append(dh)
        say(f"{dh['lamp']:<7} HOME  {dh['note']}")
    say(f"--- [{mode}] COPY_ONLY(原件不刪不搬)· anti-join 只補缺鍵 · 正典 {db_tw.name} ---")
    con = _connect(db_tw, read_only=False)
    con_gl = None
    try:
        _ledger_ensure(con)
        done = set() if force else _ledger_done(con)
        lst = listings_map(con, mega or MEGA)
        style = target_style(con, TARGETS["px"])
        units = expand_db_units(con, units)
        rep["summary"]["units"] = len(units)
        rep["notes"].append({"lamp": "GREEN" if lst else "YELLOW", "note": f"票代碼對映冊 {len(lst)} 碼(tw_listings)· 價表既有風格 {style}" + ("" if lst else ";裸碼將入 local_px_daily 暫存(或 --assume-twse)")})
        say(f"{'GREEN' if lst else 'YELLOW':<7} MAP   票代碼對映 {len(lst)} 碼 · 價表既有風格 {style}")
        for u in units:
            row = {"part": u["part"], "unit": u["unit"], "kind": u["kind"], "path": u["path"], "target": "", "keys": [], "n_rows": 0, "planned_new": 0, "rows_new": 0, "state": "", "note": u.get("note", "")}
            rep["units"].append(row)
            if u.get("state") == "SKIP":
                row["state"] = "SKIP"
                say(f"GREY    {u['part']:<5} {u['unit']}:{row['note']}")
                continue
            try:
                fp = fingerprint(Path(u["path"]))
                row["fingerprint"] = fp
                types = {r[0]: r[1] for r in con.execute(f"DESCRIBE SELECT * FROM {u['src']}").fetchall()}
                det = detect(list(types))
                proto = protocol_target(u)
                if proto:
                    table, keys = proto[1], []   # ENG065 協定:同名正典表;鍵於交集後定(protocol_keys)
                    row["protocol"] = f"{proto[0]}__{proto[1]}"
                else:
                    table, keys = route(u, det)
                row["target"], row["keys"], row["detect"] = table, keys, {k: v for k, v in det.items() if v}
                if f"{fp}|{u['unit']}|{table}" in done:
                    row["state"] = "SKIP_LEDGER"
                    row["note"] = "檔指紋已入冊(整併過=不再做;--force 重做)"
                    rep["summary"]["skipped_ledger"] += 1
                    say(f"GREY    {u['part']:<5} {u['unit']}:已入冊跳過")
                    continue
                _norm_view(con, u, det, types, lst, assume_twse, style, proto=bool(proto))
                cols = [r[0] for r in con.execute("DESCRIBE _src_norm").fetchall()]
                row["n_rows"] = con.execute("SELECT count(*) FROM _src_norm").fetchone()[0]
                targets = []  # (庫連線, 表, 鍵, where, 來源臨時表)
                if proto:
                    if proto[0] == "gl":
                        if db_gl and con_gl is None:
                            con_gl = _connect(db_gl, read_only=False)
                        if con_gl is None:
                            row["state"], row["note"] = "SKIP", "gl 協定檔需全球庫連線(--db-global);無=略(誠實)"
                            say(f"GREY    {u['part']:<5} {u['unit']}:{row['note']}")
                            continue
                        _xfer(con, con_gl, "SELECT * FROM _src_norm")
                        targets.append((con_gl, table, None, "", "_src_norm"))
                    else:
                        targets.append((con, table, None, "", "_src_norm"))
                elif table == TARGETS["px"]:
                    unm = con.execute("SELECT count(*) FROM _src_norm WHERE ticker IS NULL").fetchone()[0]
                    gl = con.execute("SELECT count(*) FROM _src_norm WHERE ticker IS NOT NULL AND NOT regexp_matches(ticker, '^[0-9]{4}[A-Z0-9]{0,2}\\.(TW|TWO)$') AND NOT regexp_matches(ticker, '^[0-9]{4}[A-Z0-9]{0,2}$')").fetchone()[0]
                    row["unmapped"] = unm
                    rep["summary"]["unmapped"] += unm
                    targets.append((con, table, keys, "ticker IS NOT NULL AND regexp_matches(ticker, '^[0-9]{4}[A-Z0-9]{0,2}\\.(TW|TWO)$')", "_src_norm"))
                    if unm:
                        # 暫存表以裸碼為鍵(ticker_raw → ticker;誠實不猜 .TW/.TWO)
                        con.execute("CREATE OR REPLACE TEMP TABLE _src_unm AS SELECT ticker_raw AS ticker, * EXCLUDE (ticker, ticker_raw) FROM _src_norm WHERE ticker IS NULL")
                        targets.append((con, TARGETS["px_unmapped"], keys, "", "_src_unm"))
                    if gl:
                        if db_gl and con_gl is None:
                            con_gl = _connect(db_gl, read_only=False)
                        if con_gl is not None:
                            targets.append((con_gl, TARGETS["gl"], keys, "ticker IS NOT NULL AND NOT regexp_matches(ticker, '^[0-9]{4}[A-Z0-9]{0,2}(\\.(TW|TWO))?$')", "_src_norm"))
                        else:
                            row["note"] = f"非台股碼 {gl} 列(無全球庫連線=略)"
                else:
                    targets.append((con, table, keys, "", "_src_norm"))
                planned, done_n, tnames = 0, 0, []
                skip_note = ""
                for c2, t2, k2, w2, s2 in targets:
                    if c2 is not con and not proto:
                        # 全球庫(px 非台股碼):臨時表不可跨庫→臨時 parquet 搬運(只 ENG064 八欄)
                        pc = [c for c in PRICE_COLS if c in cols]
                        _xfer(con, c2, f"SELECT {', '.join(_qi(c) for c in pc)} FROM _src_norm WHERE {w2}")
                        w2, cols2 = "", pc
                    else:
                        cols2 = [r[0] for r in c2.execute(f"DESCRIBE {s2}").fetchall()]
                    if proto:
                        # ENG065 律:共同欄交集(不 ALTER 正典表);零共同欄=誠實跳過;鍵律 protocol_keys
                        wcols = _ensure_table(c2, t2, cols2, [], s2, union_cols=False)
                        if not wcols:
                            skip_note = f"與正典表 {t2} 零共同欄=誠實跳過(ENG065 律)"
                            break
                        k2 = protocol_keys(wcols)
                        row["keys"] = k2
                    else:
                        wcols = _ensure_table(c2, t2, [c for c in cols2 if c != "ticker_raw"], k2, s2)
                    n_new = _count_new(c2, t2, wcols, k2, w2, s2)
                    planned += n_new
                    if apply and n_new:
                        got = _insert_new(c2, t2, wcols, k2, w2, s2)
                        done_n += got
                        rep["summary"]["tables"][t2] = rep["summary"]["tables"].get(t2, 0) + got
                        log_event("INSERT", f"{u['unit']} → {t2} +{got}", run_id=run_id, part=u["part"])
                    tnames.append(f"{('gl:' if c2 is not con else '') + t2}+{n_new}")
                if skip_note:
                    row["state"], row["note"] = "SKIP", skip_note
                    say(f"GREY    {u['part']:<5} {u['unit']}:{skip_note}")
                    continue
                row["planned_new"], row["rows_new"] = planned, done_n
                rep["summary"]["planned_new"] += planned
                rep["summary"]["rows_new"] += done_n
                row["state"] = "OK" if apply else "PLAN"
                if apply:
                    con.execute(f"INSERT INTO {LEDGER} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                [run_id, rep["ts"], u["part"], u["unit"], u["path"], fp, table, row["n_rows"], done_n, "; ".join(tnames)])
                lampc = "GREEN" if not row.get("unmapped") else "YELLOW"
                say(f"{lampc:<7} {u['part']:<5} {u['unit']}:{row['n_rows']:,} 列 → {' '.join(tnames)}{'(已寫 +%d)' % done_n if apply else '(計畫;--apply 才寫)'}"
                    + (f" · ENG065 協定 {row['protocol']}(鍵 {'+'.join(row['keys']) if row['keys'] else 'EXCEPT'})" if proto else "")
                    + (f" · 裸碼對不到 {row['unmapped']} 列→{TARGETS['px_unmapped']}" if row.get("unmapped") else ""))
            except Exception as exc:
                row["state"], row["note"] = "FAIL", str(exc)[:200]
                rep["summary"]["failed"] += 1
                log_event("UNIT_FAIL", f"{u['unit']}: {str(exc)[:200]}", run_id=run_id)
                say(f"RED     {u['part']:<5} {u['unit']}:FAIL {str(exc)[:120]}")
        for u in units:
            if u.get("attached"):
                try:
                    con.execute(f"DETACH {u['attached']}")
                except Exception:
                    pass
    finally:
        con.close()
        if con_gl is not None:
            con_gl.close()
    s = rep["summary"]
    rep["verdict"] = "RED" if s["failed"] else ("YELLOW" if (s["unmapped"] or any(n["lamp"] == "YELLOW" for n in rep["notes"])) else "GREEN")
    rep["next"] = (["via-datahome link(接點後重跑 run --apply;冪等)"] if any(n.get("part") == "home" and n["lamp"] == "YELLOW" for n in rep["notes"]) else []) \
        + (["via-vdfdb run --apply(寫入;只補缺鍵)"] if not apply else []) + ["via-vdfdb ckpt(ENG064 checkpoint 重建=抓過不再抓)", "via-vdfdb need --start 2023-01-01(缺口清單)", "via-vdfdb coverage"]
    _finish(rep, reports, do_print)
    return rep


def _finish(rep: dict, reports: Path, do_print: bool) -> None:
    try:
        _write_json(reports / f"RUN_{rep['run_id']}.json", rep)
        _write_json(reports / "RUN_latest.json", rep)
    except Exception as exc:
        rep["notes"].append({"lamp": "YELLOW", "note": f"存證失敗 {str(exc)[:60]}"})
    log_event("RUN", f"{rep['mode']} {rep['verdict']}", run_id=rep["run_id"], summary=rep["summary"])
    if do_print:
        s = rep["summary"]
        print(f"[via-vdfdb {rep['mode']}] {rep['verdict']} · 單元 {s['units']} · 計畫新增 {s['planned_new']:,} · 已寫 {s['rows_new']:,} · 已入冊跳過 {s['skipped_ledger']} · 對不到 {s['unmapped']} · FAIL {s['failed']}"
              f" · 存證 {reports / 'RUN_latest.json'}")
        if rep.get("next"):
            print("  [次步] " + " → ".join(rep["next"]))


# ---------------------------------------------------------------- ④ ckpt / ⑤ need / ⑥ coverage
def ckpt_argv() -> list | None:
    hits = sorted(HERE.glob("VDF_ENG064_HistoryBackfill_v*.py"))
    return [sys.executable, str(hits[-1]), "--rebuild-ckpt"] if hits else None


def do_ckpt() -> int:
    argv = ckpt_argv()
    if not argv:
        print("[ckpt] ENG064 缺(誠實)")
        return 2
    print(f"[ckpt] {Path(argv[1]).name} --rebuild-ckpt(段內有列即 done=整併後不再重抓;終止段 2020/2021 不動)")
    r = subprocess.run(argv, cwd=str(HERE), stdin=subprocess.DEVNULL)
    if r.returncode == 0:
        subprocess.run([argv[0], argv[1], "--status"], cwd=str(HERE), stdin=subprocess.DEVNULL)
    return r.returncode


def _months(start: str, end: str) -> list:
    y, m = int(start[:4]), int(start[5:7])
    ye, me = int(end[:4]), int(end[5:7])
    out = []
    while (y, m) <= (ye, me):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m > 12:
            y, m = y + 1, 1
    return out


def need(db: Path, table: str = "tw_daily_prices", start: str = "2023-01-01", end: str | None = None, tickers: list | None = None,
         reports: Path = REPORTS, do_print: bool = True) -> dict:
    """覆蓋缺口(月粒度;只列缺的):(ticker,月) 有列=已抓;缺=待抓;連續缺月合併為區間"""
    end = end or _dt.date.today().isoformat()
    rep = {"schema": "VIA.LocalDbNeed.v1", "ts": _dt.datetime.now().isoformat(timespec="seconds"), "db": str(db), "table": table, "start": start, "end": end, "tickers": {}, "summary": {}}
    if not db.exists():
        rep["summary"] = {"verdict": "RED", "note": f"庫缺 {db}"}
        if do_print:
            print(f"RED     need  庫缺 {db}")
        return rep
    con = _connect(db, read_only=True)
    try:
        have = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
        if table not in have:
            rep["summary"] = {"verdict": "RED", "note": f"表缺 {table}"}
            if do_print:
                print(f"RED     need  表缺 {table}")
            return rep
        months = _months(start, end)
        rows = con.execute(f"SELECT ticker, substr(CAST(date AS VARCHAR), 1, 7) ym, count(*) FROM {_qi(table)} "
                           f"WHERE CAST(date AS VARCHAR) >= ? AND CAST(date AS VARCHAR) <= ? GROUP BY 1, 2", [start, end]).fetchall()
    finally:
        con.close()
    cov: dict = {}
    for t, ym, n in rows:
        cov.setdefault(str(t), set()).add(ym)
    univ = tickers or sorted(cov)
    total_gap_months, full = 0, 0
    for t in univ:
        got = cov.get(t, set())
        missing = [m for m in months if m not in got]
        total_gap_months += len(missing)
        if not missing:
            full += 1
            continue
        ranges, s0, prev = [], None, None
        for m in missing:
            if s0 is None:
                s0 = prev = m
            elif months.index(m) == months.index(prev) + 1:
                prev = m
            else:
                ranges.append(f"{s0}~{prev}")
                s0 = prev = m
        if s0:
            ranges.append(f"{s0}~{prev}")
        rep["tickers"][t] = {"missing_months": len(missing), "have_months": len(got), "gaps": ranges}
    rep["summary"] = {"verdict": "GREEN" if total_gap_months == 0 else "YELLOW", "tickers": len(univ), "full": full, "with_gaps": len(rep["tickers"]),
                      "gap_months": total_gap_months, "months": len(months), "note": "只列缺的;抓取引擎只抓缺口(ENG064 checkpoint 段律另計)"}
    try:
        _write_json(reports / "NEED_latest.json", rep)
    except Exception:
        pass
    if do_print:
        s = rep["summary"]
        print(f"[need] {table} {start}~{end}:票 {s['tickers']} · 齊 {s['full']} · 有缺口 {s['with_gaps']} · 缺月合計 {s['gap_months']}(月粒度)· 存證 {reports / 'NEED_latest.json'}")
        for t, v in list(sorted(rep["tickers"].items(), key=lambda kv: -kv[1]["missing_months"]))[:15]:
            print(f"  {t:<10} 缺 {v['missing_months']:>3} 月  {' '.join(v['gaps'][:4])}{' …' if len(v['gaps']) > 4 else ''}")
        if len(rep["tickers"]) > 15:
            print(f"  … 其餘 {len(rep['tickers']) - 15} 票見 NEED_latest.json")
    return rep


def coverage(db: Path, reports: Path = REPORTS, do_print: bool = True) -> dict:
    rep = {"schema": "VIA.LocalDbCoverage.v1", "ts": _dt.datetime.now().isoformat(timespec="seconds"), "db": str(db), "tables": {}}
    if not db.exists():
        rep["verdict"] = "RED"
        if do_print:
            print(f"RED     coverage 庫缺 {db}")
        return rep
    con = _connect(db, read_only=True)
    try:
        for t in [r[0] for r in con.execute("SHOW TABLES").fetchall()]:
            cols = {r[0].lower() for r in con.execute(f"DESCRIBE {_qi(t)}").fetchall()}
            if "date" not in cols:
                continue
            if "ticker" in cols:
                r = con.execute(f"SELECT count(*), count(DISTINCT ticker), min(CAST(date AS VARCHAR)), max(CAST(date AS VARCHAR)) FROM {_qi(t)}").fetchone()
                yrs = con.execute(f"SELECT substr(CAST(date AS VARCHAR), 1, 4) y, count(DISTINCT ticker), count(*) FROM {_qi(t)} GROUP BY 1 ORDER BY 1").fetchall()
                rep["tables"][t] = {"rows": r[0], "tickers": r[1], "min": r[2], "max": r[3], "years": {y: {"tickers": a, "rows": b} for y, a, b in yrs}}
            else:
                r = con.execute(f"SELECT count(*), min(CAST(date AS VARCHAR)), max(CAST(date AS VARCHAR)) FROM {_qi(t)}").fetchone()
                rep["tables"][t] = {"rows": r[0], "min": r[1], "max": r[2]}
    finally:
        con.close()
    rep["verdict"] = "GREEN" if rep["tables"] else "YELLOW"
    try:
        _write_json(reports / "COVERAGE_latest.json", rep)
    except Exception:
        pass
    if do_print:
        print(f"[coverage] {db.name}:{len(rep['tables'])} 表 · 存證 {reports / 'COVERAGE_latest.json'}")
        for t, v in rep["tables"].items():
            ys = " ".join(f"{y}:{d['tickers']}票/{d['rows']:,}" for y, d in (v.get("years") or {}).items())
            print(f"  {t:<24} 列 {v['rows']:>10,} 票 {v.get('tickers', '-'):>5} {v['min']}~{v['max']}  {ys}")
    return rep


# ---------------------------------------------------------------- 自測
def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    duckdb = _duckdb()
    if duckdb is None:
        print("  [FAIL] duckdb 缺=本引擎不可測(於 via_vdf_312 境跑;或 REPAIR_BASE)")
        return 1
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        src = root / "新增資料夾"
        px, chip, rest = src / "VIA_db_part1_prices", src / "VIA_db_part2_chips", src / "VIA_db_part3_rest"
        for d in (px / "year=2023", chip, rest):
            d.mkdir(parents=True)
        db, dbg, reports, mega = root / "vdf_tw_market.duckdb", root / "vdf_global_market.duckdb", root / "reports", root / "mega"
        mega.mkdir()
        (mega / "tw_listings_20260101_000000.csv").write_text("code,name,market,yf_ticker,industry,isin\n2330,台積電,TWSE,2330.TW,24,\n6488,環球晶,TPEX,6488.TWO,28,\n2454,聯發科,TWSE,2454.TW,24,\n", encoding="utf-8")
        w = duckdb.connect()
        # px parquet:DATE 型 obs_date、裸碼、含重複列與 9999 對不到碼
        w.execute("CREATE TABLE p AS SELECT * FROM (VALUES "
                  "(DATE '2023-01-05', '2330', 500.0, 505.0, 495.0, 501.0, 498.0, 1000.0), (DATE '2023-01-06', '2330', 501.0, 510.0, 500.0, 508.0, 505.0, 1100.0), "
                  "(DATE '2023-01-06', '2330', 501.0, 510.0, 500.0, 508.0, 505.0, 1100.0), (DATE '2023-02-01', '6488', 600.0, 610.0, 590.0, 605.0, 605.0, 500.0), "
                  "(DATE '2023-01-05', '9999', 1.0, 1.0, 1.0, 1.0, 1.0, 1.0), (DATE '2023-01-05', 'AAPL', 130.0, 131.0, 129.0, 130.5, 130.5, 9.0)"
                  ") t(obs_date, ticker, open, high, low, close, adj_close, volume)")
        w.execute(f"COPY p TO {_q(_u(px / 'year=2023' / 'part-000.parquet'))} (FORMAT PARQUET)")
        (px / "extra.csv").write_text("date,symbol,close,vol\n20230301,2454.TW,700,300\n2023/03/02,2454.TW,702,310\n", encoding="utf-8")
        w.execute("CREATE TABLE c AS SELECT * FROM (VALUES ('2023-01-05', '2330', 100, 5), ('2023-01-06', '2330', -50, 7)) t(date, ticker, foreign_net, trust_net)")
        w.execute(f"COPY c TO {_q(_u(chip / 'chips.parquet'))} (FORMAT PARQUET)")
        w.execute("CREATE TABLE r AS SELECT * FROM (VALUES (TIMESTAMP '2023-01-05 00:00:00', '2330', 'margin', 12.5), (TIMESTAMP '2023-01-06 00:00:00', '2330', 'margin', 13.0)) t(obs_date, ticker, kind, value)")
        w.execute(f"COPY r TO {_q(_u(rest / 'rest.parquet'))} (FORMAT PARQUET)")
        # ENG065 協定檔(批389 工作站實錄:part3_rest 的 tw__/gl__ 檔曾落 local_rest__*):tw__tw_listings(無日期鍵=EXCEPT)/gl__us_macro(全球庫)/tw__tw_chips_daily(date+ticker=鍵 anti-join)
        w.execute("CREATE TABLE l AS SELECT * FROM (VALUES ('2330', '台積電', 'TWSE', '2330.TW'), ('6488', '環球晶', 'TPEX', '6488.TWO'), ('2454', '聯發科', 'TWSE', '2454.TW')) t(code, name, market, yf_ticker)")
        w.execute(f"COPY l TO {_q(_u(rest / 'tw__tw_listings.parquet'))} (FORMAT PARQUET)")
        w.execute("CREATE TABLE gm AS SELECT * FROM (VALUES (DATE '2023-01-05', 'DGS10', 3.5), (DATE '2023-01-06', 'DGS10', 3.6)) t(date, series, value)")
        w.execute(f"COPY gm TO {_q(_u(rest / 'gl__us_macro.parquet'))} (FORMAT PARQUET)")
        w.execute("CREATE TABLE cp AS SELECT * FROM (VALUES ('2023-01-05', '2330', 100, 5), ('2023-01-09', '2330', 20, 3)) t(date, ticker, foreign_net, trust_net)")
        w.execute(f"COPY cp TO {_q(_u(chip / 'tw__tw_chips_daily.parquet'))} (FORMAT PARQUET)")
        w.close()
        # 內嵌 duckdb 檔(價表)
        e = duckdb.connect(str(px / "old_prices.duckdb"))
        e.execute("CREATE TABLE px_extra AS SELECT * FROM (VALUES ('2023-04-03', '2330.TW', 520.0, 521.0, 519.0, 520.5, 520.5, 900.0)) t(date, ticker, open, high, low, close, adj_close, volume)")
        e.close()
        # 正典庫預植:既有列(正本零觸碰驗)
        c0 = duckdb.connect(str(db))
        c0.execute("CREATE TABLE tw_daily_prices(date VARCHAR, ticker VARCHAR, open DOUBLE, high DOUBLE, low DOUBLE, close DOUBLE, adj_close DOUBLE, volume DOUBLE)")
        c0.execute("INSERT INTO tw_daily_prices VALUES ('2023-01-05', '2330.TW', 1, 1, 1, 9.9, 9.9, 1)")
        # 台帳預植舊路由(批389 前 gl__us_macro 曾入 local_rest__gl__us_macro):鍵含目標表 → 新目標 us_macro 不被舊冊擋
        _ledger_ensure(c0)
        c0.execute(f"INSERT INTO {LEDGER} VALUES ('seed', '2026-09-07', 'rest', 'gl__us_macro.parquet', ?, ?, 'local_rest__gl__us_macro', 2, 0, '批389 前舊路由')",
                   [str(rest / "gl__us_macro.parquet"), fingerprint(rest / "gl__us_macro.parquet")])
        c0.close()
        chk("① 日期正規化(DATE/TIMESTAMP/VARCHAR 多格式/整數 20230105 → 'YYYY-MM-DD')",
            all(duckdb.connect().execute(f"SELECT {date_expr('x', ty)} FROM (SELECT {v} AS x)").fetchone()[0] == "2023-01-05"
                for v, ty in (("DATE '2023-01-05'", "DATE"), ("TIMESTAMP '2023-01-05 10:00:00'", "TIMESTAMP"), ("'2023/01/05'", "VARCHAR"), ("'2023-01-05'", "VARCHAR"), ("20230105", "BIGINT"))))
        r1 = consolidate(src, db, dbg, apply=False, reports=reports, mega=mega, do_print=False)
        units = {u["unit"]: u for u in r1["units"]}
        chk("② scan 唯讀盤點(單元 8:parquet×6/csv/duckdb 表;路由 px→tw_daily_prices chip→tw_chips_daily rest→tw_rest_daily;ENG065 協定 tw__X→X gl__X→X)",
            r1["summary"]["units"] == 8 and units["part-000.parquet"]["target"] == "tw_daily_prices" and units["chips.parquet"]["target"] == "tw_chips_daily"
            and units["rest.parquet"]["target"] == "tw_rest_daily" and units["old_prices.duckdb::px_extra"]["target"] == "tw_daily_prices"
            and units["extra.csv"]["target"] == "tw_daily_prices" and units["tw__tw_listings.parquet"]["target"] == "tw_listings"
            and units["gl__us_macro.parquet"]["target"] == "us_macro" and units["tw__tw_chips_daily.parquet"]["target"] == "tw_chips_daily"
            and units["gl__us_macro.parquet"]["state"] == "PLAN", f"(單元 {r1['summary']['units']};{[(u['unit'], u['target'], u['state']) for u in r1['units']]})")
        c1 = duckdb.connect(str(db), read_only=True)
        n_scan = c1.execute("SELECT count(*) FROM tw_daily_prices").fetchone()[0]
        tabs_scan = {r[0] for r in c1.execute("SHOW TABLES").fetchall()}
        c1.close()
        chk("③ dry-run 零寫入(價表列數不變;計畫新增=裸碼對映 yahoo 後 anti-join:2330 01-06 +6488=2;既有 2330 01-05 不算;裸碼 9999 對不到→local_px_daily 1;AAPL→global_daily 1;csv 2;duckdb 表 1;協定 3+2+2)",
            n_scan == 1 and r1["summary"]["rows_new"] == 0 and units["part-000.parquet"]["planned_new"] == 4 and units["part-000.parquet"]["unmapped"] == 1
            and units["extra.csv"]["planned_new"] == 2 and units["old_prices.duckdb::px_extra"]["planned_new"] == 1 and r1["verdict"] == "YELLOW" and r1["summary"]["planned_new"] == 18
            and units["tw__tw_listings.parquet"]["planned_new"] == 3 and units["gl__us_macro.parquet"]["planned_new"] == 2 and units["tw__tw_chips_daily.parquet"]["planned_new"] == 2,
            f"(計畫 {r1['summary']['planned_new']};單元 {[(u['unit'], u['planned_new'], u.get('unmapped')) for u in r1['units']]})")
        r2 = consolidate(src, db, dbg, apply=True, reports=reports, mega=mega, do_print=False)
        c2 = duckdb.connect(str(db), read_only=True)
        rows = c2.execute("SELECT date, ticker, close FROM tw_daily_prices ORDER BY ticker, date").fetchall()
        keep = c2.execute("SELECT close FROM tw_daily_prices WHERE date='2023-01-05' AND ticker='2330.TW'").fetchone()[0]
        unm = c2.execute("SELECT ticker, close FROM local_px_daily").fetchall()
        chips = c2.execute("SELECT count(*) FROM tw_chips_daily").fetchone()[0]
        chips_rows = c2.execute("SELECT date, ticker, foreign_net FROM tw_chips_daily ORDER BY date").fetchall()
        restn = c2.execute("SELECT count(*), min(kind) FROM tw_rest_daily").fetchone()
        led = c2.execute(f"SELECT count(*) FROM {LEDGER}").fetchone()[0]
        lst_rows = c2.execute("SELECT code, yf_ticker FROM tw_listings ORDER BY code").fetchall()
        lst_cols = [r[0] for r in c2.execute("DESCRIBE tw_listings").fetchall()]
        tabs2 = {r[0] for r in c2.execute("SHOW TABLES").fetchall()}
        c2.close()
        cg = duckdb.connect(str(dbg), read_only=True)
        gl = cg.execute("SELECT ticker, close FROM global_daily").fetchall()
        usm = cg.execute("SELECT CAST(date AS VARCHAR), series, CAST(value AS DOUBLE) FROM us_macro ORDER BY 1").fetchall()
        cg.close()
        units2 = {u["unit"]: u for u in r2["units"]}
        chk("④ --apply anti-join 只補缺鍵(既有 2330.TW 01-05 close 9.9 零觸碰;來源重複列去重;裸碼→yahoo;csv 整數/斜線日期;duckdb 內表;籌碼/其餘表建立;全球碼入 global_daily;台帳 8+預植 1)",
            keep == 9.9 and len(rows) == 6 and [r[1] for r in rows] == ["2330.TW", "2330.TW", "2330.TW", "2454.TW", "2454.TW", "6488.TWO"]
            and unm == [("9999", 1.0)] and chips == 3 and restn == (2, "margin") and led == 9 and gl == [("AAPL", 130.5)] and r2["summary"]["rows_new"] == 6 + 1 + 2 + 2 + 1 - 1 + 3 + 2 + 1
            and r2["summary"]["tables"].get("tw_daily_prices") == 5,
            f"(價表 {rows};暫存 {unm};籌碼 {chips};其餘 {restn};全球 {gl};台帳 {led};寫 {r2['summary']['rows_new']} {r2['summary']['tables']})")
        chk("⑫ ENG065 協定回歸正典表(批389:tw__tw_listings→tw_listings 零改名 EXCEPT 3 列;gl__us_macro→全球庫 us_macro 2 列(臨時 parquet 跨庫);tw__tw_chips_daily→tw_chips_daily 鍵 date+ticker 只補 1;不落 local_rest__*;台帳鍵含目標表=舊路由預植不擋)",
            lst_rows == [("2330", "2330.TW"), ("2454", "2454.TW"), ("6488", "6488.TWO")] and lst_cols == ["code", "name", "market", "yf_ticker"]
            and usm == [("2023-01-05", "DGS10", 3.5), ("2023-01-06", "DGS10", 3.6)] and chips_rows[-1] == ("2023-01-09", "2330", 20)
            and units2["tw__tw_chips_daily.parquet"]["keys"] == ["date", "ticker"] and units2["tw__tw_chips_daily.parquet"]["rows_new"] == 1
            and units2["tw__tw_listings.parquet"]["keys"] == [] and units2["gl__us_macro.parquet"]["state"] == "OK" and units2["gl__us_macro.parquet"]["rows_new"] == 2
            and not any(t.startswith("local_rest__") for t in tabs2) and r2["summary"]["tables"].get("us_macro") == 2,
            f"(listings {lst_rows} {lst_cols};us_macro {usm};chips {chips_rows};單元 {[(u['unit'], u['keys'], u['state'], u['rows_new']) for u in r2['units'] if u.get('protocol')]};表 {sorted(tabs2)})")
        r3 = consolidate(src, db, dbg, apply=True, reports=reports, mega=mega, do_print=False)
        chk("⑤ 重跑冪等(檔指紋已入冊=8 單元全跳過;0 新增)", r3["summary"]["skipped_ledger"] == 8 and r3["summary"]["rows_new"] == 0 and r3["summary"]["planned_new"] == 0)
        r4 = consolidate(src, db, dbg, apply=True, reports=reports, mega=mega, force=True, do_print=False)
        chk("⑥ --force 重做仍 0 新增(anti-join 律;既有列零觸碰)", r4["summary"]["skipped_ledger"] == 0 and r4["summary"]["rows_new"] == 0)
        cv = coverage(db, reports=reports, do_print=False)
        chk("⑦ coverage(價表 3 票 2023;籌碼/其餘表列入;COVERAGE_latest.json)",
            cv["tables"]["tw_daily_prices"]["tickers"] == 3 and list(cv["tables"]["tw_daily_prices"]["years"]) == ["2023"] and "tw_chips_daily" in cv["tables"]
            and (reports / "COVERAGE_latest.json").exists())
        nd = need(db, "tw_daily_prices", "2023-01-01", "2023-06-30", reports=reports, do_print=False)
        t6488 = nd["tickers"].get("6488.TWO", {})
        chk("⑧ need 缺口(月粒度只列缺的:6488.TWO 只有 2 月→缺 01 與 03~06 兩區間;NEED_latest.json)",
            nd["summary"]["months"] == 6 and t6488.get("missing_months") == 5 and t6488.get("gaps") == ["2023-01~2023-01", "2023-03~2023-06"]
            and (reports / "NEED_latest.json").exists(), f"({t6488})")
        argv = ckpt_argv()
        chk("⑨ ckpt 交棒 ENG064 --rebuild-ckpt(尾版 glob;不在自測執行)", bool(argv) and argv[-1] == "--rebuild-ckpt" and "ENG064" in argv[1])
        miss = consolidate(root / "不存在", db, None, apply=False, reports=reports, mega=mega, do_print=False)
        chk("⑩ 缺 src 誠實 RED(不假綠;RUN_latest 落檔)", miss["verdict"] == "RED" and (reports / "RUN_latest.json").exists())
        src_txt = Path(__file__).read_text(encoding="utf-8")
        chk("⑪ 紀律宣告(只增不減/原件零觸碰/誠實三態/零網路/尾版律/COPY_ONLY/ACCEL-BRIDGE)",
            all(k in src_txt for k in ("只增不減", "原件零觸碰", "誠實三態", "零網路", "尾版律", "COPY_ONLY", "ACCEL-BRIDGE")))
        dn = datahome_note(DB_TW)
        chk("⑬ 資料家接點燈(批389:--db 自訂路徑=不適用 None;正典庫路徑=MDL123 正本判 LINKED 綠/其餘黃並指 via-datahome link 後冪等重跑)",
            datahome_note(db) is None and (dn is None or (dn["lamp"] in ("GREEN", "YELLOW") and dn["state"] in ("LINKED", "LINKED_ELSEWHERE", "REAL_DIR", "MISSING")
                                                          and (dn["lamp"] == "GREEN") == (dn["state"] == "LINKED") and (dn["lamp"] == "GREEN" or "via-datahome link" in dn["note"]))),
            f"({dn and (dn['lamp'], dn['state'])})")
    print(f"  [計] 十三檢 OK {13 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


# ---------------------------------------------------------------- CLI
def _arg(a: list, flag: str, default=None):
    if flag in a:
        i = a.index(flag)
        if i + 1 < len(a):
            return a[i + 1]
    return default


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 本機三庫整併引擎(VDF_ENG079_LocalDbConsolidate)· 十三檢自測(零網路;臨時庫)===")
        return selftest()
    verb = next((x for x in a if x in ("scan", "run", "ckpt", "need", "coverage")), "scan")   # 批387:動詞白名單(旗標值不得誤判為動詞)
    src = Path(_arg(a, "--src", os.environ.get("VIA_LOCAL_DB_ROOT", SRC_DEFAULT)))
    db = Path(_arg(a, "--db", str(DB_TW)))
    dbg = Path(_arg(a, "--db-global", str(DB_GL)))
    only = {x.strip() for x in (_arg(a, "--only") or "").split(",") if x.strip()} or None
    as_json = "--json" in a
    try:
        if verb in ("scan", "run"):
            apply = verb == "run" and "--apply" in a
            if verb == "run" and not apply:
                print("[via-vdfdb run] 未帶 --apply=dry-run(同 scan;計畫不寫)")
            rep = consolidate(src, db, dbg, apply=apply, only=only, assume_twse="--assume-twse" in a, force="--force" in a, do_print=not as_json)
            if as_json:
                print(json.dumps(rep, ensure_ascii=False, indent=1))
            return 0 if rep["verdict"] != "RED" else 2
        if verb == "ckpt":
            return do_ckpt()
        if verb == "need":
            rep = need(db, _arg(a, "--table", "tw_daily_prices"), _arg(a, "--start", "2023-01-01"), _arg(a, "--end"),
                       [x.strip() for x in (_arg(a, "--tickers") or "").split(",") if x.strip()] or None, do_print=not as_json)
            if as_json:
                print(json.dumps(rep, ensure_ascii=False, indent=1))
            return 0 if rep["summary"].get("verdict") != "RED" else 2
        if verb == "coverage":
            rep = coverage(db, do_print=not as_json)
            if as_json:
                print(json.dumps(rep, ensure_ascii=False, indent=1))
            return 0 if rep.get("verdict") != "RED" else 2
        print(__doc__)
        return 2
    except RuntimeError as exc:
        print(f"[FAIL] {exc}")
        return 3
    except BrokenPipeError:
        return 0


if __name__ == "__main__":
    sys.exit(main())
