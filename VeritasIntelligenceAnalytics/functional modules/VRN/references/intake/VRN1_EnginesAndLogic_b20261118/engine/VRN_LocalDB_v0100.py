#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===== [VRN:ID:v0100] VRN-ENG010 · VRN_LocalDB_v0100 v0100 · ENGINE =====
# AST 注入（只加註解，AST 不變）：類別 1 · 函式 22；逐一編號在 ssot/VRN_ID_SSOT_v0100.json
# ===== [VRN:ID:END] =====
"""
VRN_LocalDB v0100 -- company NAME and ADJ CLOSE from the operator's local VDF database, read-only.

Operator 2026-10-10: 「從DATABASE擷取資料NAME ADJ CLOSE」 with
  C:\\Users\\tonyk\\OneDrive\\Documents\\VeritasIntelligenceAnalytics\\via_database\\
      _status \\  vdf_database \\  VIA_HANDOVER_LATEST.md  VIA_Parquet_Catalog.duckdb

Where the data is (VDF writer ENG079 / ENG054, readers ENG073 v0138 and CGC_MDL142, handover rules L10 / L99 / L104):
  vdf_tw_market.duckdb (vdf_database\\output_hub\\mega\\ ...)
    tw_listings_industry(code, name, market, industry_name, yf_ticker)   -- the short Chinese name, first choice
    tw_listings(code, name, market, yf_ticker, ...)                      -- only for codes the first one lacks
    tw_daily_prices(date, ticker '2330.TW' / '6488.TWO', open, high, low, close, adj_close, volume)
  VIA_Parquet_Catalog.duckdb is used when it exposes the same tables or views (checked at run time, never assumed).

Rules kept (handover L99 / L104):
  * adj_close is never replaced by close; a missing adj_close is missing (honest NODATA);
  * factor = adj_close / close of the same row (same source, same day);
  * report-date basis = the last trading day strictly before the report date (ENG073 _prev_basis);
  * target price adjusted = target price x factor(report basis) / factor(latest); upside = (tp_adj - latest adj) / latest adj;
  * freshness: basis within 14 days before the report, latest within 30 days of today -- otherwise the values are
    kept and the state says STALE.

Only reads: duckdb.connect(read_only=True); spills to the TEMP run (VRN_TEMP_POLICY) with a memory limit.  No network.
Adds new BasicInfo columns only; no existing field is touched.

2026-10-13 operator「公司名稱價格一率至DATABASE去取」 with via_database\vdf_database\tw__tw_listings.parquet,
tw__tw_listings_industry.parquet, tw__tw_daily_prices.parquet (and the rest of the VDF exports): the parquet folder is read
first (an in-memory duckdb with read-only views over the files; nothing is copied or written), the duckdb files after it.
Columns are found by name -- the VDF names first, the usual other spellings after (stock_id, trade_date as 20260518, Close,
Adj Close, 證券代號 ...); what was found is in describe().  closes(code, report date) gives the raw close of the last trading
day before the report and of the report day itself (the price a report prints is a raw close, never adjusted).
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

import argparse
import datetime
import json
import os
import sys
from pathlib import Path

LOCALDB_VERSION = "v0100"
DB_NAME = "vdf_tw_market.duckdb"
CATALOG_NAME = "VIA_Parquet_Catalog.duckdb"
SKIP_PARTS = ("_repo_", "_from_old_", "SCOPE_COPY", "selftest", "stash")
NAME_TABLES = ("tw_listings_industry", "tw_listings")
PRICE_TABLE = "tw_daily_prices"
PARQUET_DIR = "vdf_database"
PARQUET_FILES = {"tw_listings_industry": "tw__tw_listings_industry.parquet", "tw_listings": "tw__tw_listings.parquet",
                 "tw_daily_prices": "tw__tw_daily_prices.parquet"}
PARQUET_COLUMNS = {                       # the VDF writer's names first; spellings seen in other exports after
    "code": ("code", "stock_id", "stock_code", "證券代號", "股票代號", "代號"),
    "name": ("name", "stock_name", "short_name", "company_name", "證券名稱", "股票名稱", "公司簡稱", "名稱"),
    "name_en": ("name_en", "english_name", "en_name", "name_english", "英文簡稱", "英文名稱"),
    "market": ("market", "exchange", "market_type", "市場別"),
    "industry_name": ("industry_name", "industry", "產業別"),
    "yf_ticker": ("yf_ticker", "yahoo_ticker", "yf"),
    "date": ("date", "trade_date", "trading_date", "日期"),
    "ticker": ("ticker", "yf_ticker", "symbol", "code", "stock_id"),
    "close": ("close", "close_price", "收盤價"),
    "adj_close": ("adj_close", "adjclose", "adj close", "adjusted_close", "調整收盤價"),
}
PRICE_FRESH_DAYS = 14
LATEST_FRESH_DAYS = 30
# new BasicInfo columns, appended after every existing one
COLUMNS = ("NameDB", "NameDBSource", "AdjCloseReportDate", "AdjCloseReport", "AdjFactorReport", "AdjCloseLatestDate",
           "AdjCloseLatest", "AdjFactorLatest", "TargetPriceAdj", "UpsideAdjPct", "LocalDBStatus", "LocalDBPath")
NUMERIC = ("AdjCloseReport", "AdjFactorReport", "AdjCloseLatest", "AdjFactorLatest", "TargetPriceAdj", "UpsideAdjPct")


# [VRN-ID] VRN-ENG010-FNC001 · LOGIC
def data_home():
    """VIA_DATA_HOME, else the operator's default data home (when it exists)."""
    env = os.environ.get("VIA_DATA_HOME")
    if env:
        return Path(env)
    home = Path(os.environ.get("USERPROFILE") or Path.home()) / "OneDrive" / "Documents" / "VeritasIntelligenceAnalytics" / "via_database"
    return home if home.is_dir() else None


# [VRN-ID] VRN-ENG010-FNC002 · LOGIC
def candidates():
    """Explicit paths first (VRN_LOCALDB, VIA_DB_VDF_TW_MARKET), then the catalog, then vdf_tw_market.duckdb under the data
    home (mega first, newest first; repo replicas, kept old copies, selftest and stash folders skipped)."""
    out = []
    for key in ("VRN_LOCALDB", "VIA_DB_VDF_TW_MARKET"):
        if os.environ.get(key):
            out.append(Path(os.environ[key]))
    home = data_home()
    for folder in ([Path(os.environ["VRN_LOCALDB_PARQUET"])] if os.environ.get("VRN_LOCALDB_PARQUET") else []) + \
            ([home / PARQUET_DIR] if home is not None else []):
        if parquet_folder_ok(folder):                      # 2026-10-13: the operator's vdf_database parquet files first
            out.append(folder)
    if home is not None and home.is_dir():
        if (home / CATALOG_NAME).is_file():
            out.append(home / CATALOG_NAME)
        found = [p for p in home.rglob(DB_NAME) if not any(part in str(p) for part in SKIP_PARTS)]
        found.sort(key=lambda p: (0 if "mega" in str(p).lower() else 1, -p.stat().st_mtime))
        out += found
    seen, unique = set(), []
    for p in out:
        key = str(p).casefold()
        if key not in seen and (p.is_file() or parquet_folder_ok(p)):
            seen.add(key)
            unique.append(p)
    return unique


# [VRN-ID] VRN-ENG010-FNC015 · LOGIC
def parquet_folder_ok(folder):
    """A folder with the price parquet and at least one listings parquet."""
    try:
        folder = Path(folder)
        return folder.is_dir() and (folder / PARQUET_FILES[PRICE_TABLE]).is_file() and \
            any((folder / PARQUET_FILES[t]).is_file() for t in NAME_TABLES)
    except OSError:
        return False


# [VRN-ID] VRN-ENG010-FNC016 · LOGIC
def parquet_pick(columns, role):
    """The file's column for a role (case and spacing do not count), or None."""
    folded = {str(c).casefold().replace(" ", "").replace("_", ""): c for c in columns}
    for want in PARQUET_COLUMNS[role]:
        hit = folded.get(want.casefold().replace(" ", "").replace("_", ""))
        if hit is not None:
            return hit
    return None


# [VRN-ID] VRN-ENG010-FNC017 · LOGIC
def parquet_quote(s):
    return "'" + str(s).replace("'", "''") + "'"


# [VRN-ID] VRN-ENG010-FNC018 · LOGIC
def parquet_ident(s):
    return '"' + str(s).replace('"', '""') + '"'


# [VRN-ID] VRN-ENG010-FNC003 · LOGIC
def _num(value):
    try:
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return None


# [VRN-ID] VRN-ENG010-FNC004 · LOGIC
def _days(a, b):
    try:
        return (datetime.date.fromisoformat(str(b)[:10]) - datetime.date.fromisoformat(str(a)[:10])).days
    except ValueError:
        return None


# [VRN-ID] VRN-ENG010-CLS001 · CLASS
class LocalDB:
    """One read-only connection for a whole batch; names are read once, prices per (ticker, date)."""

    # [VRN-ID] VRN-ENG010-FNC005 · INIT
    def __init__(self, path=None, today=None):
        self.path, self.con, self.tables, self.status, self.why = None, None, {}, "ABSENT", ""
        self.source, self.columns, self._series, self._names_en = "", {}, {}, {}
        self.today = today or datetime.date.today().isoformat()
        self._names = None
        self._quotes = {}
        try:
            import duckdb  # noqa: F401
        except Exception:
            self.status, self.why = "DEPENDENCY_MISSING", "duckdb 沒有安裝（VRN 不代裝；pip install duckdb 是操作員的手）"
            return
        tried = []
        for cand in ([Path(path)] if path else candidates()):
            ok, why = self._open(cand)
            tried.append(f"{cand.name}: {why}")
            if ok:
                return
        self.why = "; ".join(tried) if tried else "找不到 vdf_tw_market.duckdb 或可用的 VIA_Parquet_Catalog.duckdb"

    # [VRN-ID] VRN-ENG010-FNC006 · LOGIC
    def _open(self, path):
        import duckdb
        if Path(path).is_dir():
            return self._open_parquet(path)
        try:
            con = duckdb.connect(str(path), read_only=True)
        except Exception as error:  # noqa: BLE001
            busy = "lock" in str(error).lower() or "being used" in str(error).lower()
            self.status = "DB_BUSY" if busy else self.status
            return False, ("DB_BUSY " if busy else "") + f"{error.__class__.__name__}: {error}"[:160]
        run = os.environ.get("VRN_TEMP_RUN")
        for sql in ([f"SET temp_directory='{run.replace(chr(39), chr(39) * 2)}'"] if run else []) + \
                   [f"SET memory_limit='{os.environ.get('VIA_DUCKDB_MEM') or '2GB'}'"]:
            try:
                con.execute(sql)
            except Exception:  # noqa: BLE001
                pass
        try:
            rows = con.execute("SELECT table_name, table_type FROM information_schema.tables").fetchall()
        except Exception as error:  # noqa: BLE001
            con.close()
            return False, f"{error.__class__.__name__}: {error}"[:160]
        tables = {str(n): str(t) for n, t in rows}
        if PRICE_TABLE not in tables or not any(t in tables for t in NAME_TABLES):
            con.close()
            return False, "沒有 tw_daily_prices / tw_listings_industry（表或視圖）"
        self.path, self.con, self.tables, self.status = path, con, tables, "OK"
        self.source = "duckdb"
        return True, "OK"

    # [VRN-ID] VRN-ENG010-FNC019 · LOGIC
    def _open_parquet(self, folder):
        """An in-memory duckdb with read-only views over the vdf_database parquet files, columns renamed to the VDF names."""
        import duckdb
        folder = Path(folder)
        con = duckdb.connect(":memory:")
        run = os.environ.get("VRN_TEMP_RUN")
        for sql in ([f"SET temp_directory={parquet_quote(run)}"] if run else []) + [f"SET memory_limit={parquet_quote(os.environ.get('VIA_DUCKDB_MEM') or '2GB')}"]:
            try:
                con.execute(sql)
            except Exception:  # noqa: BLE001
                pass
        found, tables = {}, {}
        for table, fname in PARQUET_FILES.items():
            path = folder / fname
            if not path.is_file():
                continue
            src = f"read_parquet({parquet_quote(path.as_posix())})"
            try:
                cols = {str(r[0]): str(r[1]) for r in con.execute(f"DESCRIBE SELECT * FROM {src}").fetchall()}
            except Exception as error:  # noqa: BLE001
                found[table] = f"讀不了：{error.__class__.__name__}: {str(error)[:120]}"
                continue
            if table == PRICE_TABLE:
                d, t, c, a = (parquet_pick(cols, r) for r in ("date", "ticker", "close", "adj_close"))
                if not (d and t and c):
                    found[table] = f"欄位對不到（要 date／ticker／close）：{', '.join(list(cols)[:12])}"
                    continue
                dt = cols[d].upper()
                if "DATE" in dt or "TIMESTAMP" in dt:
                    dexpr = f"CAST({parquet_ident(d)} AS DATE)"
                elif "INT" in dt:
                    dexpr = f"TRY_STRPTIME(CAST({parquet_ident(d)} AS VARCHAR), '%Y%m%d')::DATE"
                else:
                    dexpr = (f"COALESCE(TRY_CAST({parquet_ident(d)} AS DATE), TRY_STRPTIME(CAST({parquet_ident(d)} AS VARCHAR), '%Y%m%d')::DATE, "
                             f"TRY_STRPTIME(CAST({parquet_ident(d)} AS VARCHAR), '%Y/%m/%d')::DATE)")
                adj = f"CAST({parquet_ident(a)} AS DOUBLE)" if a else "CAST(NULL AS DOUBLE)"
                con.execute(f'CREATE VIEW "{table}" AS SELECT {dexpr} AS date, CAST({parquet_ident(t)} AS VARCHAR) AS ticker, '
                            f"CAST({parquet_ident(c)} AS DOUBLE) AS close, {adj} AS adj_close FROM {src}")
                found[table] = {"date": d, "ticker": t, "close": c, "adj_close": a or "（沒有：adj_close 誠實缺）"}
            else:
                code, name = parquet_pick(cols, "code"), parquet_pick(cols, "name")
                if not (code and name):
                    found[table] = f"欄位對不到（要 code／name）：{', '.join(list(cols)[:12])}"
                    continue
                extra = []
                for role in ("market", "yf_ticker", "industry_name", "name_en"):
                    col = parquet_pick(cols, role)
                    extra.append(f"CAST({parquet_ident(col)} AS VARCHAR) AS {role}" if col else f"CAST(NULL AS VARCHAR) AS {role}")
                con.execute(f'CREATE VIEW "{table}" AS SELECT CAST({parquet_ident(code)} AS VARCHAR) AS code, '
                            f"CAST({parquet_ident(name)} AS VARCHAR) AS name, {', '.join(extra)} FROM {src}")
                found[table] = {"code": code, "name": name, **{r: parquet_pick(cols, r) for r in ("market", "yf_ticker", "industry_name", "name_en")}}
            tables[table] = "VIEW"
        self.columns = found
        if PRICE_TABLE not in tables or not any(t in tables for t in NAME_TABLES):
            con.close()
            return False, "parquet 夾少了價格或名冊：" + json.dumps(found, ensure_ascii=False)[:200]
        self.path, self.con, self.tables, self.status, self.source = folder, con, tables, "OK", "parquet"
        return True, "OK"

    # [VRN-ID] VRN-ENG010-FNC007 · LOGIC
    def close(self):
        if self.con is not None:
            try:
                self.con.close()
            except Exception:  # noqa: BLE001
                pass
            self.con = None

    # [VRN-ID] VRN-ENG010-FNC008 · LOGIC
    def names(self):
        """{code: (name, market, yf_ticker, table)}: tw_listings_industry first, tw_listings only for codes it lacks."""
        if self._names is None:
            self._names = {}
            for table in NAME_TABLES:
                if self.con is None or table not in self.tables:
                    continue
                cols = {c for (c,) in self.con.execute(
                    "SELECT column_name FROM information_schema.columns WHERE table_name = ?", [table]).fetchall()}
                if not {"code", "name"} <= cols:
                    continue
                market = "market" if "market" in cols else "NULL"
                yf = "yf_ticker" if "yf_ticker" in cols else "NULL"
                if "name_en" in cols:                       # 2026-10-13: the English name when the listing carries one
                    for code, en in self.con.execute(f'SELECT CAST(code AS VARCHAR), CAST(name_en AS VARCHAR) FROM "{table}"').fetchall():
                        if code and en and str(en).strip() and str(code).strip() not in self._names_en:
                            self._names_en[str(code).strip()] = str(en).strip()
                for code, name, mk, yft in self.con.execute(
                        f'SELECT CAST(code AS VARCHAR), CAST(name AS VARCHAR), {market}, {yf} FROM "{table}"').fetchall():
                    code = (code or "").strip()
                    if code and name and code not in self._names:
                        self._names[code] = (str(name).strip(), mk, yft, table)
        return self._names

    # [VRN-ID] VRN-ENG010-FNC009 · LOGIC
    def _row(self, ticker, before=None):
        sql = (f'SELECT CAST(date AS VARCHAR) AS d, close, adj_close FROM "{PRICE_TABLE}" '
               "WHERE ticker = ? AND ticker <> '_NOOP_' AND adj_close IS NOT NULL AND close IS NOT NULL AND close <> 0")
        args = [ticker]
        if before:
            sql += " AND CAST(date AS VARCHAR) < ?"
            args.append(before)
        return self.con.execute(sql + " ORDER BY d DESC LIMIT 1", args).fetchone()

    # [VRN-ID] VRN-ENG010-FNC010 · LOGIC
    def quote(self, code, report_date):
        """(ticker, basis row, latest row) for the first ticker form that has prices: yf_ticker, .TW, .TWO, bare."""
        key = (code, report_date)
        if key in self._quotes:
            return self._quotes[key]
        res = (None, None, None)
        if self.con is not None and code:
            forms = []
            yf = (self.names().get(code) or (None, None, None, None))[2]
            for t in (yf, f"{code}.TW", f"{code}.TWO", code):
                if t and t not in forms:
                    forms.append(str(t))
            for t in forms:
                latest = self._row(t)
                if latest:
                    res = (t, self._row(t, report_date) if report_date else None, latest)
                    break
        self._quotes[key] = res
        return res

    # [VRN-ID] VRN-ENG010-FNC020 · LOGIC
    def series(self, ticker):
        """[(date, close, adj_close)] of one ticker, oldest first (read once per ticker)."""
        if ticker not in self._series:
            rows = []
            if self.con is not None:
                try:
                    rows = [(str(d)[:10], _num(c), _num(a)) for d, c, a in self.con.execute(
                        f'SELECT CAST(date AS VARCHAR) AS d, close, adj_close FROM "{PRICE_TABLE}" WHERE ticker = ? AND date IS NOT NULL ORDER BY d',
                        [ticker]).fetchall()]
                except Exception:  # noqa: BLE001
                    rows = []
            self._series[ticker] = rows
        return self._series[ticker]

    # [VRN-ID] VRN-ENG010-FNC021 · LOGIC
    def closes(self, code, report_date):
        """The raw close of the last trading day before the report and of the report day (a report prints a raw close),
        and the adj close of the same days plus the latest one (操作員 2026-10-16：現價以 adj close 為基準，動態更新).

        Raw and adjusted both travel: the printed price is compared against the raw close (that is what a report prints),
        while the value carried forward is the adjusted one.  adj_close missing stays missing -- never replaced by close
        (handover L99) -- so the *_adj keys are absent for a ticker the DB has no adj_close for.
        -> {"ticker", "basis"/"same": (date, close) | None, "latest": date,
            "basis_adj"/"same_adj"/"latest_adj": (date, adj_close) | None} or {} when the DB has no price."""
        if self.con is None or not code:
            return {}
        yf = (self.names().get(code) or (None, None, None, None))[2]
        forms = []
        for t in (yf, f"{code}.TW", f"{code}.TWO", code):
            if t and str(t) not in forms:
                forms.append(str(t))
        rd = str(report_date or "")[:10]
        for t in forms:
            rows = [r for r in self.series(t) if r[1] is not None and r[1] != 0]
            if not rows:
                continue
            basis = next((r for r in reversed(rows) if rd and r[0] < rd), None)
            same = next((r for r in rows if rd and r[0] == rd), None)
            adj = lambda r: (r[0], round(r[2], 4)) if r and len(r) > 2 and r[2] is not None else None
            return {"ticker": t, "basis": (basis[0], round(basis[1], 4)) if basis else None,
                    "same": (same[0], round(same[1], 4)) if same else None, "latest": rows[-1][0],
                    "basis_adj": adj(basis), "same_adj": adj(same), "latest_adj": adj(rows[-1])}
        return {}

    # [VRN-ID] VRN-ENG010-FNC022 · LOGIC
    def name_en(self, code):
        self.names()
        return self._names_en.get(str(code or "").strip(), "")

    # [VRN-ID] VRN-ENG010-FNC011 · LOGIC
    def fields(self, basic):
        """The new BasicInfo columns for one report row (never touches an existing column)."""
        out = {c: None for c in COLUMNS}
        out["LocalDBStatus"] = self.status
        out["LocalDBPath"] = str(self.path) if self.path else ""
        code = str(basic.get("TW_TICKER") or "").strip()
        if self.status != "OK":
            return out
        if not code:
            out["LocalDBStatus"] = "NO_TICKER"
            return out
        name = self.names().get(code)
        if name:
            out["NameDB"], out["NameDBSource"] = name[0], name[3]
        report_date = str(basic.get("ReportDate") or "")[:10]
        ticker, basis, latest = self.quote(code, report_date)
        if not latest:
            out["LocalDBStatus"] = "NO_PRICE" if not name else "NAME_ONLY"
            return out
        states = []
        out["AdjCloseLatestDate"], out["AdjCloseLatest"] = latest[0][:10], _num(latest[2])
        out["AdjFactorLatest"] = (_num(latest[2]) / _num(latest[1])) if _num(latest[1]) else None
        lag = _days(latest[0], self.today)
        if lag is not None and lag > LATEST_FRESH_DAYS:
            states.append("STALE_LATEST")
        if basis:
            out["AdjCloseReportDate"], out["AdjCloseReport"] = basis[0][:10], _num(basis[2])
            out["AdjFactorReport"] = (_num(basis[2]) / _num(basis[1])) if _num(basis[1]) else None
            gap = _days(basis[0], report_date)
            if gap is not None and gap > PRICE_FRESH_DAYS:
                states.append("STALE_REPORT_PRICE")
        elif report_date:
            states.append("NO_REPORT_PRICE")
        tp = _num(basic.get("TargetPrice"))
        if tp and out["AdjFactorReport"] and out["AdjFactorLatest"]:
            out["TargetPriceAdj"] = tp * out["AdjFactorReport"] / out["AdjFactorLatest"]
            if out["AdjCloseLatest"]:
                out["UpsideAdjPct"] = (out["TargetPriceAdj"] - out["AdjCloseLatest"]) / out["AdjCloseLatest"] * 100.0
        out["LocalDBStatus"] = "OK" if not states else "OK_" + "+".join(states)
        return out

    # [VRN-ID] VRN-ENG010-FNC012 · LOGIC
    def describe(self):
        counts = {}
        if self.con is not None:
            for t in (PRICE_TABLE,) + NAME_TABLES:
                if t in self.tables:
                    try:
                        counts[t] = self.con.execute(f'SELECT count(*) FROM "{t}"').fetchone()[0]
                    except Exception:  # noqa: BLE001
                        counts[t] = None
        latest = None
        if self.con is not None and PRICE_TABLE in self.tables:
            try:
                latest = str(self.con.execute(f'SELECT max(date) FROM "{PRICE_TABLE}"').fetchone()[0])[:10]
            except Exception:  # noqa: BLE001
                latest = None
        return {"status": self.status, "path": str(self.path) if self.path else "", "why": self.why, "source": self.source,
                "tables": {t: self.tables.get(t) for t in (PRICE_TABLE,) + NAME_TABLES if t in self.tables}, "rows": counts,
                "columns": self.columns, "latest_price_date": latest}


# [VRN-ID] VRN-ENG010-FNC013 · ENTRY
def selftest():
    import tempfile
    checks = []
    try:
        import duckdb
    except Exception:
        print("  [SKIP] duckdb 沒有安裝：自測略過（誠實）")
        return 0
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "mega" / DB_NAME
        db.parent.mkdir()
        con = duckdb.connect(str(db))
        con.execute("CREATE TABLE tw_listings_industry(code VARCHAR, name VARCHAR, market VARCHAR, industry_name VARCHAR, yf_ticker VARCHAR)")
        con.execute("INSERT INTO tw_listings_industry VALUES ('2330','台積電','TWSE','半導體','2330.TW')")
        con.execute("CREATE TABLE tw_listings(code VARCHAR, name VARCHAR, market VARCHAR, yf_ticker VARCHAR)")
        con.execute("INSERT INTO tw_listings VALUES ('2330','台灣積體電路製造股份有限公司','TWSE','2330.TW'), ('6488','環球晶','TPEX','6488.TWO')")
        con.execute("CREATE TABLE tw_daily_prices(date VARCHAR, ticker VARCHAR, open DOUBLE, high DOUBLE, low DOUBLE, close DOUBLE, adj_close DOUBLE, volume DOUBLE)")
        con.execute("INSERT INTO tw_daily_prices VALUES ('2026-09-30','2330.TW',0,0,0,1000,900,1), ('2026-10-01','2330.TW',0,0,0,1010,1010,1),"
                    "('2026-10-08','2330.TW',0,0,0,1100,1100,1), ('1900-01-01','_NOOP_',0,0,0,1,1,0), ('2026-10-08','6488.TWO',0,0,0,500,NULL,1)")
        con.close()
        os.environ["VIA_DATA_HOME"] = td
        try:
            ldb = LocalDB(today="2026-10-10")
            f = ldb.fields({"TW_TICKER": "2330", "ReportDate": "2026-10-01", "TargetPrice": 1200})
            g = ldb.fields({"TW_TICKER": "6488", "ReportDate": "2026-10-01"})
            ldb.close()
        finally:
            os.environ.pop("VIA_DATA_HOME", None)
        checks += [("found under the data home (mega)", ldb.status == "OK" and ldb.path == db),
                   ("short name from tw_listings_industry", f["NameDB"] == "台積電" and f["NameDBSource"] == "tw_listings_industry"),
                   ("report basis = last day strictly before the report", f["AdjCloseReportDate"] == "2026-09-30" and f["AdjCloseReport"] == 900),
                   ("latest adj close", f["AdjCloseLatestDate"] == "2026-10-08" and f["AdjCloseLatest"] == 1100),
                   ("factor chain: 1200 x 0.9 / 1.0", abs(f["TargetPriceAdj"] - 1080.0) < 1e-9),
                   ("adj_close missing stays missing (never close)", g["AdjCloseLatest"] is None and g["NameDB"] == "環球晶"),
                   ("absent database is honest", LocalDB(path=Path(td) / "none.duckdb").status != "OK")]
    with tempfile.TemporaryDirectory() as td:            # 2026-10-13: the vdf_database parquet folder, other column spellings
        folder = Path(td) / PARQUET_DIR
        folder.mkdir()
        con = duckdb.connect(":memory:")
        con.execute("CREATE TABLE li(stock_id VARCHAR, stock_name VARCHAR, market VARCHAR, industry VARCHAR, yf_ticker VARCHAR, english_name VARCHAR)")
        con.execute("INSERT INTO li VALUES ('2637','慧洋-KY','TWSE','航運','2637.TW','Wisdom Marine'), ('6147','頎邦','TPEX','半導體','6147.TWO',NULL)")
        con.execute("CREATE TABLE px(trade_date INTEGER, symbol VARCHAR, \"Close\" DOUBLE, \"Adj Close\" DOUBLE)")
        con.execute("INSERT INTO px VALUES (20260914,'2637.TW',95.1,90.0), (20260915,'2637.TW',96.9,91.7), (20260512,'6147.TWO',80.0,NULL),"
                    "(20260518,'6147.TWO',81.5,NULL)")
        con.execute(f"COPY li TO {parquet_quote((folder / PARQUET_FILES['tw_listings_industry']).as_posix())} (FORMAT PARQUET)")
        con.execute(f"COPY px TO {parquet_quote((folder / PARQUET_FILES['tw_daily_prices']).as_posix())} (FORMAT PARQUET)")
        con.close()
        os.environ["VIA_DATA_HOME"] = td
        try:
            cands = candidates()
            pq = LocalDB(today="2026-09-20")
            n = pq.names().get("2637")
            c1 = pq.closes("2637", "2026-09-15")
            c2 = pq.closes("6147", "2026-05-19")
            en = pq.name_en("2637")
            f2 = pq.fields({"TW_TICKER": "2637", "ReportDate": "2026-09-15"})
            desc = pq.describe()
            pq.close()
        finally:
            os.environ.pop("VIA_DATA_HOME", None)
        checks += [("parquet 夾（vdf_database）排在 duckdb 前面", cands[:1] == [folder] and pq.source == "parquet" and pq.path == folder),
                   ("欄位別名對得到：stock_id／stock_name／trade_date 20260915／symbol／Close／Adj Close", n is not None and n[0] == "慧洋-KY"
                    and desc["columns"]["tw_daily_prices"]["date"] == "trade_date"),
                   ("原始收盤價：報告日前一交易日與報告當日", c1.get("basis") == ("2026-09-14", 95.1) and c1.get("same") == ("2026-09-15", 96.9)),
                   ("沒有 adj_close 的價格照樣有收盤價（現價比對用原始收盤價）", c2.get("basis") == ("2026-05-18", 81.5) and c2.get("same") is None),
                   ("英文名有就給", en == "Wisdom Marine"),
                   ("fields() 照舊（adj 規則不變）", f2["NameDB"] == "慧洋-KY" and f2["AdjCloseReport"] == 90.0 and f2["AdjCloseLatest"] == 91.7),
                   ("最新價格日期看得到", desc["latest_price_date"] == "2026-09-15")]
    for name, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    failed = sum(1 for _, ok in checks if not ok)
    print(f"[LOCALDB] {LOCALDB_VERSION} · {len(checks) - failed}/{len(checks)}")
    return 1 if failed else 0


# [VRN-ID] VRN-ENG010-FNC014 · ENTRY
def main(argv=None):
    parser = argparse.ArgumentParser(description="VRN local DB: company name and adj close, read-only")
    parser.add_argument("command", nargs="?", default="selftest", choices=("selftest", "probe"))
    parser.add_argument("--ticker", default="")
    parser.add_argument("--date", default="")
    args = parser.parse_args(argv)
    if args.command == "probe":
        ldb = LocalDB()
        info = ldb.describe()
        if args.ticker:
            info["fields"] = ldb.fields({"TW_TICKER": args.ticker, "ReportDate": args.date})
            info["name"] = (ldb.names().get(args.ticker) or [""])[0]
            info["closes"] = ldb.closes(args.ticker, args.date)
        ldb.close()
        print(json.dumps(info, ensure_ascii=False, indent=1, default=str))
        return 0 if info["status"] == "OK" else 1
    return selftest()


if __name__ == "__main__":
    sys.exit(main())
