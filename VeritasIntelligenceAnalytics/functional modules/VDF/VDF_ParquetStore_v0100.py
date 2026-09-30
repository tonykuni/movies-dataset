"""受管日價庫：CSV → 停用商品 → 啟用 → 鎖型 DataFrame → Parquet / DuckDB。

正式行情只走 ENG054 已有網路橋與同意閘；沒有 LLM 呼叫。
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


import argparse
import calendar
from contextlib import contextmanager
import csv
from datetime import date, datetime, timedelta, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shutil
import sys
import time
from zoneinfo import ZoneInfo

# def 01_PARAMETERS: 唯一可調參數與固定資料契約
HERE = Path(__file__).resolve().parent
VERSION = "v0100"
SCHEMA = "VIA.VDF.ManagedPrices.v1"
START_DATE = "2022-07-01"
OVERLAP_DAYS = 3
INTERVAL_SECONDS = 3600
MAX_CSV_ROWS = 100000
MAX_CSV_BYTES = 16 * 1024 * 1024
MEMORY_LIMIT = "512MB"
THREADS = 2
COLUMNS = ["Date", "Ticker", "YFinance_Ticker", "Bloomberg_Ticker", "Name",
           "Open", "Low", "High", "Close", "Adj_Open", "Adj_Low", "Adj_High",
           "Adj_Close", "Volume", "Turnover", "Market_Cap"]
SQL_TYPES = ["DATE"] + ["VARCHAR"] * 4 + ["DOUBLE"] * 8 + ["BIGINT", "DOUBLE", "DOUBLE"]
RAW_MAP = {"open": "Open", "low": "Low", "high": "High", "close": "Close", "adj_close": "Adj_Close", "volume": "Volume"}
RAW_KEYS = {"date", "ticker", *RAW_MAP}
MARKER = ".vdf-managed.json"
CATALOG = "vdf_catalog.duckdb"


def _module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    body = importlib.util.module_from_spec(spec)
    sys.modules[name] = body
    spec.loader.exec_module(body)
    return body


def engine():
    return _module(max((HERE / "engine").glob("VDF_ENG054_TWDailyBackfill_v*.py")), "vdf_store_engine")


def contract():
    return {"schema": SCHEMA, "headers": dict(zip(COLUMNS, SQL_TYPES)),
            "primary_key": ["Date", "Ticker"], "null_source_fields": ["Bloomberg_Ticker", "Adj_Open", "Adj_Low", "Adj_High", "Turnover", "Market_Cap"],
            "csv_header": ["TICKER", "NAME"], "new_product_active": False,
            "name_verification": "local conflict check; no external identity verification",
            "storage": "ZSTD Parquet per ticker; DuckDB catalog and prices view",
            "overlap_days": OVERLAP_DAYS, "start_date": START_DATE,
            "existing_keys": "preserve; report conflicts", "llm_calls": 0,
            "scope": "managed daily prices only; legacy databases are not migrated/deleted",
            "production_verified": False}


def ticker(value):
    text = str(value).strip().upper()
    if not re.fullmatch(r"[A-Z0-9^][A-Z0-9.^=\-]{0,31}", text) or ".." in text:
        raise ValueError("非法 TICKER: " + text)
    if text.isdigit():
        raise ValueError("數字代號須明示市場，例如 2330.TW / 6488.TWO；不猜市場")
    return text


def csv_rows(path):
    path = Path(path)
    if path.stat().st_size > MAX_CSV_BYTES:
        raise ValueError("CSV 超過 16 MiB")
    errors, rows, seen = [], [], {}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != ["TICKER", "NAME"]:
            raise ValueError("CSV 表頭必須依序為 TICKER,NAME (UTF-8 / UTF-8 BOM)")
        for number, row in enumerate(reader, 2):
            if number > MAX_CSV_ROWS + 1:
                raise ValueError("CSV 超過 100000 筆")
            try:
                if None in row or any(v is None for v in row.values()):
                    raise ValueError("欄數不符")
                symbol, name = ticker(row["TICKER"]), row["NAME"].strip()
                if not name or len(name) > 200 or any(ord(c) < 32 for c in name):
                    raise ValueError("名稱空白、過長或含控制字元")
                if name.startswith(("=", "+", "-", "@")):
                    raise ValueError("名稱不可為試算表公式")
                if symbol in seen:
                    raise ValueError("重複代號，首次在列 " + str(seen[symbol]))
                seen[symbol] = number
                rows.append((symbol, name))
            except ValueError as exc:
                errors.append({"row": number, "error": str(exc)})
    if errors:
        raise ValueError(json.dumps({"csv_errors": errors[:100], "error_count": len(errors)}, ensure_ascii=False))
    if not rows:
        raise ValueError("CSV 無商品")
    return rows


def _root(explicit=None):
    if explicit:
        return Path(explicit).expanduser().absolute()
    return engine()._database()[0].parent / "vdf_managed"


def _safe_path(root):
    if any(p.is_symlink() for p in [root, *root.parents]):
        raise ValueError("受管路徑不可含符號連結")


def _owned(root):
    _safe_path(root)
    if not (root / MARKER).is_file():
        raise ValueError("尚未初始化受管庫；先執行 store init")
    marker = json.loads((root / MARKER).read_text(encoding="utf-8"))
    if marker.get("schema") != SCHEMA or marker.get("headers") != dict(zip(COLUMNS, SQL_TYPES)):
        raise ValueError("受管庫版本不符")
    for p in root.rglob("*"):
        if p.is_symlink():
            raise ValueError("受管庫內含符號連結")


@contextmanager
def _lock(root):
    _owned(root)
    path = root / ".writer.lock"
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise ValueError("BUSY: writer.lock 存在；先確認原程序已停止，不自動搶鎖") from exc
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump({"pid": os.getpid(), "at": datetime.now(timezone.utc).isoformat()}, stream)
        yield
    finally:
        path.unlink()


def _connect(root, read_only=False):
    import duckdb
    return duckdb.connect(str(root / CATALOG), read_only=read_only,
                          config={"memory_limit": MEMORY_LIMIT, "threads": THREADS})


def _sql(text):
    return "'" + str(text).replace("'", "''") + "'"


def _product_dir(root, symbol):
    # 不把外部 ticker 當路徑；識別字不以同值跨來源合併。
    return root / "prices" / hashlib.sha256(symbol.encode()).hexdigest()


def _refresh_view(con, root):
    columns = ", ".join('CAST(NULL AS ' + kind + ') AS "' + name + '"' for name, kind in zip(COLUMNS, SQL_TYPES))
    files = list((root / "prices").glob("*/data.parquet"))
    query = "SELECT " + columns + " WHERE FALSE"
    if files:
        query = "SELECT " + ",".join('p."' + c + '"' for c in COLUMNS) + " FROM read_parquet(" + _sql((root / "prices" / "*" / "data.parquet").as_posix()) + ", hive_partitioning=false) p JOIN products c ON p.Ticker=c.ticker WHERE c.state <> 'deleting'"
    con.execute("CREATE OR REPLACE VIEW prices AS " + query)


def initialize(root):
    _safe_path(root)
    if (root / MARKER).exists():
        _owned(root)
    else:
        root.mkdir(parents=True, exist_ok=True)
        if any(root.iterdir()):
            raise ValueError("init 僅接受空目錄；不接管既有庫")
        (root / MARKER).write_text(json.dumps({"schema": SCHEMA, "headers": dict(zip(COLUMNS, SQL_TYPES))}), encoding="utf-8")
    with _lock(root), _connect(root) as con:
        (root / "prices").mkdir(exist_ok=True)
        con.execute("CREATE TABLE IF NOT EXISTS products(ticker VARCHAR PRIMARY KEY, name VARCHAR NOT NULL, active BOOLEAN NOT NULL DEFAULT FALSE, state VARCHAR NOT NULL DEFAULT 'ready', checked_through DATE, last_success TIMESTAMPTZ, last_error VARCHAR, row_count BIGINT DEFAULT 0, max_date DATE)")
        _refresh_view(con, root)
    return {"state": "READY", "root": str(root), "contract": contract()}


def import_csv(root, path):
    rows = csv_rows(path)
    with _lock(root), _connect(root) as con:
        existing = dict(con.execute("SELECT ticker,name FROM products").fetchall())
        conflicts = [t for t, n in rows if t in existing and existing[t] != n]
        if conflicts:
            raise ValueError("名稱與已匯入商品衝突: " + ",".join(conflicts))
        con.execute("BEGIN")
        try:
            con.executemany("INSERT INTO products(ticker,name) VALUES (?,?) ON CONFLICT DO NOTHING", rows)
            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK")
            raise
    return {"state": "IMPORTED", "added": sum(t not in existing for t, _ in rows), "existing": sum(t in existing for t, _ in rows), "new_product_active": False, "network_calls": 0, "name_verified": False}


def _selection(con, symbols, csv_path=None):
    requested = csv_rows(csv_path) if csv_path else [(ticker(t), None) for t in symbols]
    if not requested:
        raise ValueError("請指定 --ticker (可重複) 或 --csv")
    known = {t: (n, state) for t, n, state in con.execute("SELECT ticker,name,state FROM products").fetchall()}
    for t, name in requested:
        if t not in known or (name is not None and name != known[t][0]):
            raise ValueError("商品不存在或名稱不符: " + t)
    return sorted({t for t, _ in requested})


def activate(root, symbols, active, csv_path=None):
    with _lock(root), _connect(root) as con:
        selected = _selection(con, symbols, csv_path)
        if any(con.execute("SELECT state FROM products WHERE ticker=?", [t]).fetchone()[0] != "ready" for t in selected):
            raise ValueError("刪除中的商品不能啟用；先完成刪除")
        con.execute("BEGIN")
        try:
            con.executemany("UPDATE products SET active=? WHERE ticker=?", [(active, t) for t in selected])
            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK")
            raise
    return {"state": "ACTIVE" if active else "INACTIVE", "tickers": selected, "network_calls": 0}


def delete_products(root, symbols, csv_path=None):
    with _lock(root), _connect(root) as con:
        selected = _selection(con, symbols, csv_path)
        # 持久化 tombstone；中斷可重跑刪除，不能被背景更新復活。
        con.executemany("UPDATE products SET active=FALSE,state='deleting' WHERE ticker=?", [(t,) for t in selected])
        for symbol in selected:
            folder = _product_dir(root, symbol)
            if folder.exists():
                shutil.rmtree(folder)
            con.execute("DELETE FROM products WHERE ticker=?", [symbol])
        _refresh_view(con, root)
    return {"state": "DELETED", "tickers": selected, "scope": "all files and catalog rows in managed product namespace; legacy databases unchanged"}


def frame(rows, symbol, name, start=None, end=None):
    import polars as pl
    schema = dict(zip(COLUMNS, [pl.Date] + [pl.String] * 4 + [pl.Float64] * 8 + [pl.Int64, pl.Float64, pl.Float64]))
    clean, seen = [], {}
    for raw in rows:
        unknown = set(raw) - RAW_KEYS
        if unknown:
            raise ValueError("HEADER 漂移，未映射欄位: " + ",".join(sorted(unknown)))
        if ticker(raw.get("ticker", "")) != symbol:
            raise ValueError("來源回傳不同商品")
        day = date.fromisoformat(str(raw.get("date", ""))[:10])
        if start and day < date.fromisoformat(start) or end and day > date.fromisoformat(end):
            raise ValueError("來源日期超出請求區間")
        item = dict.fromkeys(COLUMNS)
        item.update(Date=day, Ticker=symbol, YFinance_Ticker=symbol, Name=name)
        for key, dest in RAW_MAP.items():
            value = raw.get(key)
            if value is not None:
                if isinstance(value, bool):
                    raise ValueError("數值不可為 bool")
                numeric = float(value)
                if not math.isfinite(numeric):
                    raise ValueError("數值不可為 NaN/Infinity")
                if key == "volume":
                    if numeric < 0 or numeric != int(numeric) or numeric > 2**53:
                        raise ValueError("Volume 不可負值、小數或超過精確整數範圍")
                    value = int(numeric)
                else:
                    value = numeric
            item[dest] = value
        if item["Close"] is None:
            raise ValueError("Close 缺值")
        if day in seen and seen[day] != item:
            raise ValueError("同日來源重複且數值不同")
        if day not in seen:
            clean.append(item)
            seen[day] = item
    return pl.DataFrame(clean, schema=schema, strict=True).sort("Date")


def _commit_frame(con, root, symbol, df):
    folder = _product_dir(root, symbol)
    folder.mkdir(exist_ok=True)
    current, incoming, merged = (folder / p for p in ("data.parquet", "incoming.tmp", "merged.tmp"))
    df.write_parquet(incoming, compression="zstd", statistics=True)
    try:
        con.execute("CREATE OR REPLACE TEMP VIEW incoming AS SELECT * FROM read_parquet(" + _sql(incoming) + ")")
        query, added, conflicts = "SELECT * FROM incoming", df.height, 0
        if current.exists():
            description = con.execute("DESCRIBE SELECT * FROM read_parquet(?)", [str(current)]).fetchall()
            if [(r[0], r[1]) for r in description] != list(zip(COLUMNS, SQL_TYPES)):
                raise ValueError("既有 Parquet HEADER 不符鎖定契約")
            con.execute("CREATE OR REPLACE TEMP VIEW previous AS SELECT * FROM read_parquet(" + _sql(current) + ")")
            changed = " OR ".join('a."'+c+'" IS DISTINCT FROM b."'+c+'"' for c in COLUMNS[5:])
            conflicts = con.execute("SELECT count(*) FROM previous a JOIN incoming b USING(Date,Ticker) WHERE " + changed).fetchone()[0]
            new = "SELECT b.* FROM incoming b ANTI JOIN previous a USING(Date,Ticker)"
            added = con.execute("SELECT count(*) FROM (" + new + ")").fetchone()[0]
            query = "SELECT * FROM previous UNION ALL " + new
        if added:
            con.execute("COPY (" + query + ' ORDER BY "Date") TO ' + _sql(merged) + " (FORMAT PARQUET, COMPRESSION ZSTD)")
            os.replace(merged, current)
        count, maximum = con.execute("SELECT count(*),max(Date) FROM read_parquet(?)", [str(current)]).fetchone()
        _refresh_view(con, root)
        return {"added": added, "conflicts": conflicts, "rows": count, "max_date": maximum}
    finally:
        incoming.unlink(missing_ok=True)
        merged.unlink(missing_ok=True)


def target_date():
    now = datetime.now(ZoneInfo("Asia/Taipei"))
    day = now.date() - timedelta(days=1 if now.hour < 16 else 0)
    while day.weekday() >= 5:
        day -= timedelta(days=1)
    return day.isoformat()


def _fetch(symbol, start, end):
    body = engine().PRIOR._load()
    if not body.gate_open():
        raise ValueError("GATED: 原網路同意閘未開")
    net = body._net_or_none()
    if net is None:
        raise ValueError("NET_UNAVAILABLE")
    exclusive = date.fromisoformat(end) + timedelta(days=1)
    result = body._fetch_group(net, [symbol], start, calendar.timegm(exclusive.timetuple()))
    if result.get("failed"):
        raise ValueError("SOURCE_PARTIAL: " + json.dumps(result["failed"], ensure_ascii=False))
    return result.get("rows") or []


def update(root, end=None):
    end = end or target_date()
    date.fromisoformat(end)
    if end > target_date() or end < START_DATE:
        raise ValueError("end 必須介於起始日及已收盤日期")
    results = []
    with _lock(root), _connect(root) as con:
        products = con.execute("SELECT ticker,name,checked_through FROM products WHERE active AND state='ready' ORDER BY ticker").fetchall()
        for symbol, name, checked in products:
            path = _product_dir(root, symbol) / "data.parquet"
            if checked and checked.isoformat() >= end and path.exists():
                results.append({"ticker": symbol, "state": "SKIPPED", "reason": "checked_through", "added": 0})
                continue
            maximum = con.execute("SELECT max(Date) FROM read_parquet(?)", [str(path)]).fetchone()[0] if path.exists() else None
            start = max(START_DATE, (maximum - timedelta(days=OVERLAP_DAYS)).isoformat()) if maximum else START_DATE
            try:
                rows = _fetch(symbol, start, end)
                df = frame(rows, symbol, name, start, end)
                if df.is_empty():
                    raise ValueError("NO_DATA: 不推進檢查點，下次重試")
                outcome = _commit_frame(con, root, symbol, df)
                # 空交易日/資料源延遲不能把尚缺目標日標成完成。
                complete = outcome["max_date"].isoformat() >= end and outcome["conflicts"] == 0
                con.execute("UPDATE products SET checked_through=?,last_success=current_timestamp,last_error=?,row_count=?,max_date=? WHERE ticker=?",
                            [end if complete else None, None if complete else "PARTIAL: overlap conflict or target not reached", outcome["rows"], outcome["max_date"], symbol])
                results.append(dict(ticker=symbol, state="UPDATED" if complete else "PARTIAL", start=start, end=end, **outcome))
            except Exception as exc:
                error = type(exc).__name__ + ": " + str(exc)[:500]
                con.execute("UPDATE products SET last_error=? WHERE ticker=?", [error, symbol])
                results.append({"ticker": symbol, "state": "FAILED", "error": error})
    failed = sum(r["state"] in ("FAILED", "PARTIAL") for r in results)
    return {"state": "PARTIAL" if failed else "OK", "end": end, "products": results, "failed": failed,
            "api_jobs": sum(r["state"] != "SKIPPED" for r in results), "llm_calls": 0}


def status(root, full=False):
    _owned(root)
    with _connect(root, read_only=True) as con:
        cursor = con.execute("SELECT ticker,name,active,state,checked_through,last_success,last_error,row_count,max_date FROM products ORDER BY ticker")
        names = [c[0] for c in cursor.description]
        products = [dict(zip(names, row)) for row in cursor.fetchall()]
    files = list((root / "prices").glob("*/data.parquet"))
    active = sum(p["active"] for p in products)
    return {"state": "ATTENTION" if any(p["last_error"] or p["state"] == "deleting" for p in products) else "READY",
            "root": str(root), "catalog": str(root / CATALOG), "products_count": len(products), "active": active,
            "parquet_files": len(files), "parquet_bytes": sum(p.stat().st_size for p in files),
            "writer_lock": (root / ".writer.lock").exists(), "llm_calls": 0,
            "counts_source": "catalog checkpoints; use inspect for actual parquet verification",
            **({"products": products} if full else {})}


def inspect(root):
    _owned(root)
    with _connect(root, read_only=True) as con:
        actual = con.execute("SELECT Ticker,count(*),min(Date),max(Date) FROM prices GROUP BY Ticker ORDER BY Ticker").fetchall()
        types = [(r[0], r[1]) for r in con.execute("DESCRIBE prices").fetchall()]
        catalog = {t: n for t, n in con.execute("SELECT ticker,row_count FROM products").fetchall()}
    mismatch = [t for t, count, _, _ in actual if catalog.get(t) != count]
    present = {row[0] for row in actual}
    mismatch += [t for t, count in catalog.items() if count and t not in present]
    ok = types == list(zip(COLUMNS, SQL_TYPES)) and not mismatch
    return {"state": "VERIFIED" if ok else "MISMATCH", "actual_headers": types, "actual_data": actual, "count_mismatch": mismatch, "root": str(root), "scope": "this managed store only"}


def migrate_legacy(root, db):
    """明示來源的唯讀複製；僅轉入已登錄商品，不刪舊庫或改啟用狀態。"""
    import duckdb
    source = Path(db).expanduser().resolve()
    if not source.is_file() or source == (root / CATALOG).resolve():
        raise ValueError("請指定既有日價來源 DuckDB")
    results = []
    with _lock(root), _connect(root) as con, duckdb.connect(str(source), read_only=True) as old:
        description = old.execute("DESCRIBE tw_daily_prices").fetchall()
        if not RAW_KEYS.issubset({r[0] for r in description}):
            raise ValueError("舊庫 tw_daily_prices 缺少原始 8 欄")
        for symbol, name in con.execute("SELECT ticker,name FROM products WHERE state='ready' ORDER BY ticker").fetchall():
            cursor = old.execute("SELECT date,ticker,open,low,high,close,adj_close,volume FROM tw_daily_prices WHERE ticker=? ORDER BY date", [symbol])
            keys = [r[0] for r in cursor.description]
            count, conflicts = 0, 0
            while True:
                batch = cursor.fetchmany(10000)
                if not batch:
                    break
                outcome = _commit_frame(con, root, symbol, frame([dict(zip(keys, r)) for r in batch], symbol, name))
                count += outcome["added"]
                conflicts += outcome["conflicts"]
                con.execute("UPDATE products SET row_count=?,max_date=?,checked_through=NULL WHERE ticker=?", [outcome["rows"], outcome["max_date"], symbol])
            results.append({"ticker": symbol, "added": count, "conflicts": conflicts})
    return {"state": "PARTIAL" if any(r["conflicts"] for r in results) else "MIGRATED", "source_read_only": True, "legacy_deleted": False, "products": results, "network_calls": 0}


def sample(root, symbol, limit=10):
    if not 1 <= limit <= 1000:
        raise ValueError("limit 必須為 1..1000")
    _owned(root)
    with _connect(root, read_only=True) as con:
        cursor = con.execute('SELECT * FROM prices WHERE Ticker=? ORDER BY "Date" DESC LIMIT ?', [ticker(symbol), limit])
        return {"state": "READ", "headers": [c[0] for c in cursor.description], "rows": cursor.fetchall()}


def start(root, interval=INTERVAL_SECONDS, cycles=None):
    if interval < 60 or cycles is not None and cycles < 1:
        raise ValueError("interval 至少 60 秒；cycles 至少 1")
    count, rc = 0, 0
    try:
        while True:
            report = update(root)
            print(json.dumps(report, ensure_ascii=False, default=str), flush=True)
            rc = max(rc, 2 if report["failed"] else 0)
            count += 1
            if cycles is not None and count >= cycles:
                return rc
            time.sleep(interval)
    except KeyboardInterrupt:
        print('[STOPPED] 已停止自動更新；資料保留', flush=True)
        return rc


def main(argv=None):
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[DENY] 只能經 VCGC")
        return 2
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--selftest"]:
        argv = ["selftest"]
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--root")
    sub = parser.add_subparsers(dest="verb", required=True)
    for verb in ("contract", "init", "inspect", "selftest"):
        sub.add_parser(verb, allow_abbrev=False)
    p = sub.add_parser("status", allow_abbrev=False)
    p.add_argument("--full", action="store_true")
    for verb in ("validate-csv", "import-csv"):
        p = sub.add_parser(verb, allow_abbrev=False)
        p.add_argument("--csv", required=True)
    for verb in ("activate", "deactivate", "delete"):
        p = sub.add_parser(verb, allow_abbrev=False)
        selection = p.add_mutually_exclusive_group(required=True)
        selection.add_argument("--ticker", action="append")
        selection.add_argument("--csv")
    p = sub.add_parser("update", allow_abbrev=False)
    p.add_argument("--end")
    p = sub.add_parser("migrate-legacy", allow_abbrev=False)
    p.add_argument("--db", required=True)
    p = sub.add_parser("sample", allow_abbrev=False)
    p.add_argument("--ticker", required=True)
    p.add_argument("--limit", type=int, default=10)
    p = sub.add_parser("start", allow_abbrev=False)
    p.add_argument("--interval", type=int, default=INTERVAL_SECONDS)
    p.add_argument("--cycles", type=int)
    args = parser.parse_args(argv)
    try:
        if args.verb == "selftest":
            return _module(HERE / "tests" / "test_managed_store_v0100.py", "vdf_store_tests").run_tests(sys.modules[__name__])
        if args.verb == "contract":
            result = contract()
        elif args.verb == "validate-csv":
            rows = csv_rows(args.csv)
            result = {"state": "VALID", "rows": len(rows), "preview": rows[:10], "name_verified": False, "network_calls": 0}
        else:
            root = _root(args.root)
            if args.verb == "init":
                result = initialize(root)
            elif args.verb == "import-csv":
                result = import_csv(root, args.csv)
            elif args.verb in ("activate", "deactivate"):
                result = activate(root, args.ticker, args.verb == "activate", args.csv)
            elif args.verb == "delete":
                result = delete_products(root, args.ticker, args.csv)
            elif args.verb == "update":
                result = update(root, args.end)
            elif args.verb == "start":
                return start(root, args.interval, args.cycles)
            elif args.verb == "inspect":
                result = inspect(root)
            elif args.verb == "migrate-legacy":
                result = migrate_legacy(root, args.db)
            elif args.verb == "sample":
                result = sample(root, args.ticker, args.limit)
            else:
                result = status(root, args.full)
        print(json.dumps(result, ensure_ascii=False, default=str, indent=1))
        return 2 if result.get("state") in ("PARTIAL", "ATTENTION", "MISMATCH") else 0
    except Exception as exc:
        print(json.dumps({"state": "FAILED", "error": type(exc).__name__ + ": " + str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
