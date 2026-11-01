#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_ENG237_DataExport v0100 — 使用者經 VDF 進資料庫取「範圍內的特定資料」→ 轉格式 → 存本機或雲端硬碟同步夾

操作員令(2026-11-01):「使用者可透過系統進入資料庫擷取所需範圍內特定資料 · 提供使用者轉換格式儲存在雲端硬碟能力」。
(前一支 VDF_ENG118_ExportDesk 只出每表一小段樣本,不能依期間 / 代號取。)
  tables  :列出資料庫家底下每本庫 · 每張表 · 欄位 · 認得的日期欄 / 代號欄(唯讀)。
  export  :--table T [--db 庫名] [--from YYYY-MM-DD] [--to YYYY-MM-DD] [--codes 2330,2317] [--cols a,b,c]
            [--format csv|parquet|json|xlsx|md] [--dest onedrive|gdrive|<夾>] [--home 資料庫家] [--limit N] [--name 檔名]
    ① 唯讀:DuckDB 記憶體連線 ATTACH 庫檔 (READ_ONLY);庫檔前後位元組不變(自測驗)。
    ② 安全:表名 / 欄名先對 information_schema 驗(沒有的照實報錯,不拼字串);期間 · 代號一律參數化。
    ③ 期間:日期欄照族群冊 detect 清單認(date · trade_date · period · ym …);'YYYY-MM-DD' · DATE · TIMESTAMP · 'YYYYMMDD' 都認。
       代號:代號欄照同一份清單;2330 也對得到 2330.TW / 2330.TWO。
    ④ 格式:csv(UTF-8 BOM,Excel 開中文不亂碼)· parquet(zstd)· json(陣列)· xlsx(上限 1,048,575 列)· md(前 2000 列)。
    ⑤ 存放:onedrive = %OneDrive%\VDF_Export · gdrive = VIA_GDRIVE_DIR > G:\My Drive > G:\我的雲端硬碟 > ~/Google Drive/My Drive 底下 VDF_Export;
       其他 = 照給的夾;沒給 = VIA_Reports/vdf/export。找不到同步夾照實報錯(不亂建在別處)。
    ⑥ 收據:列數 · 檔 · 位元組 · SHA-256 · 秒 · 參數化 SQL;每次一行記進 VIA_Reports/vdf/export/EXPORT_runs.jsonl。
資料庫家:--home > VIA_VDF_DB_HOME > VDF_DataHome_SSOT 尾版第一個在這台機器存在的家 > 倉內 VDF/output_hub;同名庫取法同 VDF db check。
VDF 自己的模組:零網路;不匯入他系統程式;同意閘不讀不寫;不碰 TA-Lib;不裝套件(xlsx 要 openpyxl,沒有照實報錯)。
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
    """統包唯一網路工具惰性載入;本檔的連網全經 MDL008 子行程改道。"""
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


import datetime
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF = HERE.parent if HERE.name == "engine" else HERE
VIA = VDF.parents[1]
TAG = "VDF_ENG237_DataExport v" + Path(__file__).stem.rsplit("_v", 1)[-1]
FORMATS = ("csv", "parquet", "json", "xlsx", "md")
DATE_COLS = ["date", "trade_date", "Date", "日期", "period", "month", "ym", "report_date", "data_date", "as_of", "asof_date", "portfolio_date"]
KEY_COLS = ["ticker", "code", "stock_id", "symbol", "index_code", "series", "etf_code", "stock_code", "series_id", "證券代號", "etf_ticker", "holding_ticker"]
XLSX_MAX = 1_048_575
MD_MAX = 2000


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _tail(folder: Path, glob: str):
    hits = [p for p in Path(folder).glob(glob) if _vnum(p) >= 0]
    return max(hits, key=_vnum) if hits else None


def detect_lists(vdf: Path = VDF) -> tuple:
    """族群冊 detect 的日期欄 / 代號欄清單(冊在就用冊,不在用內建);內建多的幾個欄名排在後面。"""
    p = _tail(vdf, "VDF_FetchGroups_SSOT_v*.json")
    try:
        d = json.loads(p.read_text(encoding="utf-8")).get("detect") or {} if p else {}
    except (OSError, ValueError):
        d = {}
    dc = list(dict.fromkeys(list(d.get("date_cols") or []) + DATE_COLS))
    kc = list(dict.fromkeys(list(d.get("key_cols") or []) + KEY_COLS))
    return dc, kc


def resolve_home(home: str | None = None, env: dict | None = None, vdf: Path = VDF) -> tuple:
    env = os.environ if env is None else env
    if home:
        return Path(home), "--home"
    if env.get("VIA_VDF_DB_HOME"):
        return Path(env["VIA_VDF_DB_HOME"]), "VIA_VDF_DB_HOME"
    p = _tail(vdf, "VDF_DataHome_SSOT_v*.json")
    try:
        homes = json.loads(p.read_text(encoding="utf-8")).get("homes") or [] if p else []
    except (OSError, ValueError):
        homes = []
    for h in homes:
        if h.get("db_home") and Path(h["db_home"]).is_dir():
            return Path(h["db_home"]), "冊 %s(%s)" % (h.get("id"), p.name)
    return vdf / "output_hub", "倉內 output_hub(退路)"


def db_files(home: Path) -> list:
    """家底下的 .duckdb(同名取法同 VDF db check:mega / active_tw_etf 優先 · 再比大小;略過 _repo_ · stash · selftest)。"""
    best = {}
    for f in Path(home).rglob("*.duckdb"):
        low = str(f).lower()
        if f.name.endswith(".wal") or "_repo_" in f.name or "stash" in low or "selftest" in low:
            continue
        try:
            rank = (("mega" in f.parts) or ("active_tw_etf" in str(f)), f.stat().st_size)
        except OSError:
            continue
        k = f.name.lower()
        if k not in best or rank > best[k][0]:
            best[k] = (rank, f)
    return [best[k][1] for k in sorted(best)]


def _duck():
    import duckdb
    return duckdb


def _attach(con, path: Path, alias: str = "src") -> None:
    con.execute("ATTACH '%s' AS %s (READ_ONLY)" % (str(path).replace("'", "''"), alias))


def _qi(name: str) -> str:
    return '"' + str(name).replace('"', '""') + '"'


def columns_of(con, alias: str, table: str) -> list:
    return [(r[0], r[1]) for r in con.execute(
        "SELECT column_name, data_type FROM information_schema.columns WHERE table_catalog = ? AND table_schema = 'main' AND table_name = ? ORDER BY ordinal_position",
        [alias, table]).fetchall()]


def list_tables(home: Path) -> list:
    duckdb = _duck()
    dc, kc = detect_lists()
    out = []
    for f in db_files(home):
        con = duckdb.connect()
        try:
            _attach(con, f)
            tabs = [r[0] for r in con.execute("SELECT table_name FROM information_schema.tables WHERE table_catalog = 'src' AND table_schema = 'main' ORDER BY 1").fetchall()]
            for t in tabs:
                cols = columns_of(con, "src", t)
                names = [c for c, _ in cols]
                out.append({"db": f.name, "path": str(f), "table": t, "columns": names,
                            "date_col": next((c for c in dc if c in names), None), "key_col": next((c for c in kc if c in names), None)})
        except Exception as exc:  # noqa: BLE001 — 一本庫打不開(被鎖 / 壞)照實記,其他照列
            out.append({"db": f.name, "path": str(f), "error": "%s: %s" % (type(exc).__name__, str(exc)[:120])})
        finally:
            con.close()
    return out


def find_table(home: Path, table: str, db: str | None = None) -> Path | None:
    duckdb = _duck()
    for f in db_files(home):
        if db and f.name.lower() != db.lower():
            continue
        con = duckdb.connect()
        try:
            _attach(con, f)
            if con.execute("SELECT count(*) FROM information_schema.tables WHERE table_catalog = 'src' AND table_schema = 'main' AND table_name = ?",
                           [table]).fetchall()[0][0]:
                return f
        except Exception:  # noqa: BLE001 — 打不開的庫跳過(list_tables 會照實列)
            continue
        finally:
            con.close()
    return None


def resolve_dest(dest: str | None, env: dict | None = None, home_dir: Path | None = None) -> tuple:
    """存放夾:onedrive / gdrive / <夾> / 預設 VIA_Reports/vdf/export。→ (夾, 說明);找不到同步夾 → (None, 原因)。"""
    env = os.environ if env is None else env
    home_dir = Path(home_dir or Path.home())
    if not dest:
        return VIA / "VIA_Reports" / "vdf" / "export", "預設(VIA_Reports/vdf/export)"
    d = dest.strip()
    if d.lower() == "onedrive":
        for k in ("OneDrive", "OneDriveConsumer", "OneDriveCommercial"):
            if env.get(k) and Path(env[k]).is_dir():
                return Path(env[k]) / "VDF_Export", "OneDrive(%s)" % k
        if (home_dir / "OneDrive").is_dir():
            return home_dir / "OneDrive" / "VDF_Export", "OneDrive(家目錄)"
        return None, "找不到 OneDrive 同步夾(env OneDrive 沒設、家目錄沒有 OneDrive)"
    if d.lower() in ("gdrive", "googledrive", "google"):
        cands = [env.get("VIA_GDRIVE_DIR"), "G:\\My Drive", "G:\\我的雲端硬碟", str(home_dir / "Google Drive" / "My Drive"), str(home_dir / "Google Drive"),
                 str(home_dir / "My Drive")]
        for c in cands:
            if c and Path(c).is_dir():
                return Path(c) / "VDF_Export", "Google 雲端硬碟(%s)" % c
        return None, "找不到 Google 雲端硬碟同步夾(設 VIA_GDRIVE_DIR 指到它)"
    return Path(d), "指定夾"


def build_query(con, table: str, cols: list | None, date_col: str | None, key_col: str | None, d_from: str | None, d_to: str | None,
                codes: list | None, limit: int | None) -> tuple:
    have = columns_of(con, "src", table)
    names = [c for c, _ in have]
    if not names:
        raise ValueError("表 %s 不在這本庫" % table)
    if cols:
        bad = [c for c in cols if c not in names]
        if bad:
            raise ValueError("欄位不在表裡:%s(有 %s)" % (bad, ", ".join(names[:30])))
    sel = ", ".join(_qi(c) for c in (cols or names))
    where, params = [], []
    if d_from or d_to:
        if not date_col:
            raise ValueError("表 %s 認不出日期欄(認得的:%s)→ 不能依期間取" % (table, ", ".join(DATE_COLS[:8])))
        expr = "coalesce(try_cast(%s AS DATE), try_strptime(CAST(%s AS VARCHAR), '%%Y%%m%%d')::DATE)" % (_qi(date_col), _qi(date_col))
        if d_from:
            where.append("%s >= CAST(? AS DATE)" % expr)
            params.append(d_from)
        if d_to:
            where.append("%s <= CAST(? AS DATE)" % expr)
            params.append(d_to)
    if codes:
        if not key_col:
            raise ValueError("表 %s 認不出代號欄 → 不能依代號取" % table)
        ph = ", ".join("?" for _ in codes)
        k = "CAST(%s AS VARCHAR)" % _qi(key_col)
        where.append("(%s IN (%s) OR split_part(%s, '.', 1) IN (%s))" % (k, ph, k, ph))
        params += list(codes) + list(codes)
    sql = "SELECT %s FROM src.main.%s" % (sel, _qi(table))
    if where:
        sql += " WHERE " + " AND ".join(where)
    if date_col:
        sql += " ORDER BY %s" % _qi(date_col)
    if limit:
        sql += " LIMIT %d" % int(limit)
    return sql, params


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def export(table: str, db: str | None = None, d_from: str | None = None, d_to: str | None = None, codes: list | None = None, cols: list | None = None,
           fmt: str = "csv", dest: str | None = None, home: str | None = None, limit: int | None = None, name: str | None = None,
           env: dict | None = None, ledger: Path | None = None) -> dict:
    t0 = time.time()
    fmt = (fmt or "csv").lower()
    if fmt not in FORMATS:
        raise ValueError("格式只收 %s" % " · ".join(FORMATS))
    for v in (d_from, d_to):
        if v and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
            raise ValueError("日期寫成 YYYY-MM-DD:%s" % v)
    h, h_why = resolve_home(home, env)
    f = find_table(h, table, db)
    if f is None:
        raise ValueError("資料庫家 %s(%s)底下找不到表 %s%s" % (h, h_why, table, (" · 庫 " + db) if db else ""))
    out_dir, d_why = resolve_dest(dest, env)
    if out_dir is None:
        raise ValueError(d_why)
    out_dir.mkdir(parents=True, exist_ok=True)
    dc, kc = detect_lists()
    duckdb = _duck()
    con = duckdb.connect()
    try:
        _attach(con, f)
        names = [c for c, _ in columns_of(con, "src", table)]
        date_col = next((c for c in dc if c in names), None)
        key_col = next((c for c in kc if c in names), None)
        sql, params = build_query(con, table, cols, date_col, key_col, d_from, d_to, codes, limit)
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        base = name or "%s_%s_%s_%s" % (table, d_from or "start", d_to or "end", stamp)
        base = re.sub(r"[^\w.\-]+", "_", base)
        target = out_dir / ("%s.%s" % (base, fmt))
        rows = con.execute("SELECT count(*) FROM (%s)" % sql, params).fetchall()[0][0]
        if fmt == "xlsx" and rows > XLSX_MAX:
            raise ValueError("xlsx 上限 %d 列,這次 %d 列 → 縮小範圍或改 csv / parquet" % (XLSX_MAX, rows))
        if fmt == "csv":
            tmp = target.with_suffix(".csv.part")
            con.execute("COPY (%s) TO '%s' (FORMAT CSV, HEADER TRUE)" % (sql, str(tmp).replace("'", "''")), params)
            with open(target, "wb") as out, open(tmp, "rb") as src:
                out.write(b"\xef\xbb\xbf")
                for chunk in iter(lambda: src.read(1 << 20), b""):
                    out.write(chunk)
            tmp.unlink(missing_ok=True)
        elif fmt == "parquet":
            con.execute("COPY (%s) TO '%s' (FORMAT PARQUET, COMPRESSION ZSTD)" % (sql, str(target).replace("'", "''")), params)
        elif fmt == "json":
            con.execute("COPY (%s) TO '%s' (FORMAT JSON, ARRAY TRUE)" % (sql, str(target).replace("'", "''")), params)
        elif fmt == "xlsx":
            try:
                import openpyxl  # noqa: F401
            except ImportError:
                raise ValueError("xlsx 要 openpyxl(本環境沒有;不代裝 → 改 csv,或經 VCGC 安裝閘補)") from None
            con.execute(sql, params).df().to_excel(target, index=False)
        else:
            df = con.execute(sql + ("" if limit else " LIMIT %d" % MD_MAX), params).df()
            cols_ = [str(c) for c in df.columns]
            lines = ["| " + " | ".join(cols_) + " |", "|" + "---|" * len(cols_)]
            for rec in df.itertuples(index=False):
                lines.append("| " + " | ".join(str(v).replace("|", "\\|") for v in rec) + " |")
            target.write_text("# %s(%s)\n\n%s\n" % (table, f.name, "\n".join(lines)), encoding="utf-8")
    finally:
        con.close()
    rec = {"ts": datetime.datetime.now().isoformat(timespec="seconds"), "tag": TAG, "table": table, "db": f.name, "db_path": str(f), "home": str(h), "home_from": h_why,
           "from": d_from, "to": d_to, "codes": codes or [], "cols": cols or [], "format": fmt, "rows": rows, "file": str(target), "dest": d_why,
           "bytes": target.stat().st_size, "sha256": _sha256(target), "secs": round(time.time() - t0, 2), "sql": sql, "params": params,
           "date_col": date_col, "key_col": key_col}
    led = Path(ledger or (VIA / "VIA_Reports" / "vdf" / "export" / "EXPORT_runs.jsonl"))
    try:
        led.parent.mkdir(parents=True, exist_ok=True)
        with open(led, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
    except OSError:
        pass
    return rec


def _opt(a: list, k: str):
    return a[a.index(k) + 1] if k in a and a.index(k) + 1 < len(a) else None


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["--selftest"]:
        return selftest()
    verb = a[0] if a else ""
    if verb == "tables":
        h, why = resolve_home(_opt(a, "--home"))
        rows = list_tables(h)
        if "--json" in a:
            print(json.dumps({"home": str(h), "from": why, "tables": rows}, ensure_ascii=False, indent=1))
        else:
            for r in rows:
                print("  %-28s %-34s %s" % (r["db"], r.get("table") or "(打不開)", r.get("error") or "日期欄 %s · 代號欄 %s · %d 欄" % (
                    r.get("date_col") or "—", r.get("key_col") or "—", len(r.get("columns") or []))))
            print("[計] VDF 資料庫表 %d 張 · 家 %s(%s)" % (sum(1 for r in rows if r.get("table")), h, why))
        return 0
    if verb == "export":
        try:
            codes = [x.strip() for x in (_opt(a, "--codes") or "").split(",") if x.strip()] or None
            cols = [x.strip() for x in (_opt(a, "--cols") or "").split(",") if x.strip()] or None
            lim = _opt(a, "--limit")
            r = export(_opt(a, "--table") or "", db=_opt(a, "--db"), d_from=_opt(a, "--from"), d_to=_opt(a, "--to"), codes=codes, cols=cols,
                       fmt=_opt(a, "--format") or "csv", dest=_opt(a, "--dest"), home=_opt(a, "--home"), limit=int(lim) if lim else None, name=_opt(a, "--name"))
        except ValueError as exc:
            print("[VDF 取資料] RED · %s" % exc)
            return 1
        print(json.dumps(r, ensure_ascii=False, indent=1, default=str) if "--json" in a else
              "[VDF 取資料] GREEN · %s.%s · %d 列 · %s · %s · %s 位元組 · sha256 %s · %.2f 秒" % (
                  r["db"], r["table"], r["rows"], r["format"], r["file"], r["bytes"], r["sha256"][:12], r["secs"]))
        return 0
    print("用法:python %s tables [--home 家] | export --table T [--db 庫] [--from YYYY-MM-DD] [--to YYYY-MM-DD] [--codes a,b] [--cols a,b] "
          "[--format csv|parquet|json|xlsx|md] [--dest onedrive|gdrive|夾] [--home 家] [--limit N] · --selftest" % Path(__file__).name)
    return 2


def selftest() -> int:
    import shutil
    import tempfile
    p = f = 0

    def chk(name, cond, note=""):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s%s" % (name, (" · " + str(note)[:300]) if note else ""))

    print("=== %s · 自測(唯讀附掛 · 範圍 · 代號 · 欄位 · 五種格式 · 雲端夾)===" % TAG)
    try:
        duckdb = _duck()
    except ImportError:
        print("  [NODATA] 本境沒有 duckdb(不代裝)")
        return 2
    tmp = Path(tempfile.mkdtemp(prefix="vdf_ex237_"))
    try:
        home = tmp / "home" / "output_hub"
        (home / "mega").mkdir(parents=True)
        db = home / "mega" / "vdf_tw_market.duckdb"
        con = duckdb.connect(str(db))
        con.execute("CREATE TABLE tw_daily_prices (date VARCHAR, ticker VARCHAR, close DOUBLE, volume BIGINT)")
        con.execute("INSERT INTO tw_daily_prices VALUES ('2026-01-02','2330.TW',1000,10),('2026-02-03','2330.TW',1010,11),('2026-03-04','2330.TW',1020,12),"
                    "('2026-02-03','2317.TW',200,20),('2026-02-03','6488.TWO',500,30)")
        con.execute("CREATE TABLE tw_monthly_revenue (ym VARCHAR, code VARCHAR, revenue BIGINT, \"名稱\" VARCHAR)")
        con.execute("INSERT INTO tw_monthly_revenue VALUES ('20260101','2330',100,'台積電'),('20260201','2330',110,'台積電')")
        con.close()
        before = _sha256(db)
        env = {"VIA_VDF_DB_HOME": str(home.parent)}
        led = tmp / "runs.jsonl"
        r = export("tw_daily_prices", d_from="2026-02-01", d_to="2026-02-28", codes=["2330", "2317"], cols=["date", "ticker", "close"], fmt="csv",
                   dest=str(tmp / "out"), env=env, ledger=led)
        txt = Path(r["file"]).read_bytes()
        chk("① 範圍 + 代號 + 欄位:2 月 · 2330 / 2317 · 三欄 → 2 列(2330.TW 對得到 2330)· CSV 有 UTF-8 BOM · 標頭只有三欄",
            r["rows"] == 2 and txt.startswith(b"\xef\xbb\xbf") and txt.decode("utf-8-sig").splitlines()[0] == "date,ticker,close", (r["rows"], txt[:80]))
        chk("② 唯讀:庫檔匯出前後 SHA-256 一樣 · 資料庫家由 VIA_VDF_DB_HOME 定 · 同名取 mega", _sha256(db) == before and r["home_from"] == "VIA_VDF_DB_HOME"
            and "mega" in r["db_path"])
        outs = {}
        for fm in ("parquet", "json", "xlsx", "md"):
            try:
                outs[fm] = export("tw_daily_prices", d_from="2026-02-03", d_to="2026-02-03", fmt=fm, dest=str(tmp / "out"), env=env, ledger=led)
            except ValueError as exc:
                outs[fm] = {"err": str(exc)}
        pq = duckdb.connect().execute("SELECT count(*) FROM read_parquet(?)", [outs["parquet"]["file"]]).fetchall()[0][0]
        js = json.loads(Path(outs["json"]["file"]).read_text(encoding="utf-8"))
        chk("③ 格式:parquet %s 列 · json %s 筆 · xlsx %s · md %s(同一天 3 檔)" % (pq, len(js), "ok" if outs["xlsx"].get("file") else outs["xlsx"].get("err"),
                                                                             "ok" if outs["md"].get("file") else outs["md"].get("err")),
            pq == 3 and len(js) == 3 and (outs["xlsx"].get("rows") == 3 or "openpyxl" in outs["xlsx"].get("err", "")) and outs["md"].get("rows") == 3)
        r2 = export("tw_monthly_revenue", d_from="2026-02-01", fmt="csv", dest=str(tmp / "out"), env=env, ledger=led)
        chk("④ 'YYYYMMDD' 期間也認(ym 20260201 ≥ 2026-02-01 → 1 列)· 中文欄名照帶", r2["rows"] == 1 and "名稱" in Path(r2["file"]).read_text(encoding="utf-8-sig"))
        errs = []
        for kw in ({"cols": ["close; DROP TABLE x"]}, {"table": "nope"}, {"d_from": "2026/01/01"}, {"fmt": "exe"}):
            try:
                export(**dict({"table": "tw_daily_prices", "env": env, "dest": str(tmp / "out"), "ledger": led}, **kw))
                errs.append("沒擋")
            except ValueError as exc:
                errs.append(str(exc)[:30])
        chk("⑤ 擋:欄位不在表裡(含注入字串)· 表不在 · 日期格式錯 · 格式不收 → 照實報錯,不拼字串 · %s" % errs, "沒擋" not in errs and _sha256(db) == before)
        od = tmp / "OneDriveX"
        od.mkdir()
        gd = tmp / "gd"
        gd.mkdir()
        chk("⑥ 雲端夾:onedrive → %OneDrive%\\VDF_Export · gdrive → VIA_GDRIVE_DIR\\VDF_Export · 找不到照實報(不亂建)",
            resolve_dest("onedrive", {"OneDrive": str(od)})[0] == od / "VDF_Export" and resolve_dest("gdrive", {"VIA_GDRIVE_DIR": str(gd)})[0] == gd / "VDF_Export"
            and resolve_dest("onedrive", {}, home_dir=tmp / "nohome")[0] is None and resolve_dest("gdrive", {}, home_dir=tmp / "nohome")[0] is None)
        rr = export("tw_daily_prices", fmt="csv", dest="onedrive", env=dict(env, OneDrive=str(od)), ledger=led)
        chk("⑦ 真的寫進雲端同步夾(%s · %d 列)" % (Path(rr["file"]).parent, rr["rows"]), Path(rr["file"]).parent == od / "VDF_Export" and rr["rows"] == 5)
        lines = [json.loads(x) for x in led.read_text(encoding="utf-8").splitlines()]
        chk("⑧ 收據:每次一行(%d 行)· 列數 · 檔 · SHA-256 · 參數化 SQL(值不進 SQL 字串)" % len(lines),
            len(lines) >= 7 and all(x.get("sha256") and x.get("rows") is not None for x in lines) and "2330" not in lines[0]["sql"] and "2330" in lines[0]["params"])
        tabs = list_tables(home.parent)
        tp = next((t for t in tabs if t.get("table") == "tw_daily_prices"), {})
        chk("⑨ tables:列出庫 · 表 · 欄位 · 認得的日期欄(date)/ 代號欄(ticker)", tp.get("date_col") == "date" and tp.get("key_col") == "ticker" and len(tabs) == 2)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("⑩ VDF 獨立:不匯入他系統程式 · 兩座橋在 · 零網路 · 同意閘不讀不寫 · 不碰 TA-Lib",
        not re.search(r"^\s*(import|from)\s+(CGC_|VRN_|VCGC|requests|httpx|urllib\.request)", src, re.M) and "VIA:ACCEL-BRIDGE" in src and "VIA:NET-BRIDGE" in src
        and "CONSENT" not in body and "talib" not in body.lower())
    print("[計] %s 自測 %d/%d · %s" % (TAG, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
