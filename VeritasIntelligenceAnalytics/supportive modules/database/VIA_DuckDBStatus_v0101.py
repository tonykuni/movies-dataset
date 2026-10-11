#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_DuckDBStatus v0101 — DuckDB 資料庫管理與現況清單引擎(操作員 2026-10-10)。
  v0101(v0100 不動):① 正本加速器 shield 先探測行為才套(v0100 直接套,實機 rc 1 無輸出)· 任何例外印成一行 [計] 失敗 · 型別 · 檔:行
                    ② 代號名冊:四碼代號去資料庫找名稱 / 市場別 / 產業(依欄裡的值認欄,不靠欄名)→ _status\\LISTING_INDEX.json · names <代號…> 動詞
                    ③ 啟動先印一行(python · duckdb 版本 · 根)
  目的:任何 AI 用最少 token 讀懂 via_database 現況;擷取與增量寫入仍由 VDF 引擎負責(本引擎對 parquet 只讀)。
  status(預設)  掃 via_database 下所有 parquet(預設 vdf_database):列數 · 欄位 · 日期欄起迄 · 頻率 · 代號數 · 最新日列數 · 落後交易日 · 缺日 · 重複鍵 · 與上次快照的變化
                 增量掃描:mtime + 大小沒變就沿用上次快照(只重掃有變的檔)
                 產出(via_database\\\\_status\\\\):DB_STATUS_AI.md(AI 現況卡,一表一行)· DB_STATUS_latest.html(矩陣)· DB_STATUS_latest.json
                        VDF_IncrementalPlan_latest.json(給 VDF:每表最後日 · 下次從哪天補 · 缺哪幾天 · 去重鍵)· DB_SNAPSHOT_Ledger.jsonl(只增)
                        via_catalog.duckdb(每張 parquet 一個視圖 + _vdb_status 表;任何引擎唯讀連線就能查)
  schema <表>    精簡列出欄位與型別
  sql "<查詢>"   對目錄唯讀查詢(最多印 30 列)
  plan           印給 VDF 的增量計畫
  燈:綠 = 新鮮 · 黃 = 落後 / 有缺日 / 有重複鍵 · 紅 = 讀不了或空表 · 灰 = 無日期欄(清單類)
  正本:加速器 VeritasCeleritas_v1141 · 網路工具 VeritasAegisNexus_v1652(本引擎不出網,只留接口)
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0110] 正本加速器 VeritasCeleritas_v1141 · 正本網路工具 VeritasAegisNexus_v1652(找不到 = 不改任何行為) =====
import sys as _cb_sys
from pathlib import Path as _cb_Path
_cb_p = _cb_Path(__file__).resolve()
while _cb_p.parent != _cb_p:
    if (_cb_p / "supportive modules").is_dir():
        _cb_sup = _cb_p / "supportive modules"
        for _cb_d in [_cb_sup] + [x.parent for x in list(_cb_sup.glob("*/VeritasAegisNexus_v1652.py"))[:1]]:
            if str(_cb_d) not in _cb_sys.path:
                _cb_sys.path.insert(0, str(_cb_d))
        break
    _cb_p = _cb_p.parent
try:
    import VeritasCeleritas_v1141 as _ACCEL  # noqa: F401  正本加速器
except Exception:  # noqa: BLE001
    _ACCEL = None


def _net():
    """正本網路工具(只在需要出網時載入;本引擎不出網)。"""
    try:
        import VeritasAegisNexus_v1652 as _NET  # noqa: WPS433
        return _NET
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import datetime
import hashlib
import html
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

PARAMS = {"engine": "VIA_DuckDBStatus", "version": "v0101", "default_root": r"C:\Users\tonyk\OneDrive\Documents\VeritasIntelligenceAnalytics\via_database",
          "date_cols": ("date", "trade_date", "trading_date", "asof", "as_of", "report_date", "period", "month", "ym", "yyyymm", "year_month", "datetime", "time", "dt", "日期", "資料日期", "年月", "year"),
          "ticker_cols": ("ticker", "stock_id", "code", "symbol", "stock_code", "sid", "證券代號", "股票代號", "代號", "series", "series_id", "index_code"),
          "dup_scan_max_rows": 30_000_000, "gap_window_days": 60, "status_dir": "_status"}


_SHIELD = {"note": "未探測"}


def _shield_probe():
    """正本 shield 的用法不靠猜:拿回傳 0 的假函式包一次再呼叫,行為正常(可呼叫 · 回 0 或 None · 不 exit)才採用。"""
    if _SHIELD.get("done"):
        return _SHIELD.get("fn")
    _SHIELD["done"] = True
    s = getattr(_ACCEL, "shield", None) if _ACCEL else None
    if not callable(s):
        _SHIELD.update(fn=None, note="正本加速器無 shield")
        return None
    try:
        probe = s(lambda *a, **k: 0)
        ok = callable(probe) and probe() in (0, None)
        _SHIELD.update(fn=s if ok else None, note="shield 可用" if ok else "shield 行為不符(回 %r)→ 不套" % (probe() if callable(probe) else probe,))
    except BaseException as exc:  # noqa: BLE001
        _SHIELD.update(fn=None, note="shield 探測失敗 %s → 不套" % type(exc).__name__)
    return _SHIELD.get("fn")


def db_root() -> Path:
    return Path(os.environ.get("VIA_DB_ROOT") or PARAMS["default_root"])


def _repo_reports() -> Path | None:
    here = Path(__file__).resolve()
    for p in here.parents:
        if (p / "supportive modules").is_dir() and (p / "functional modules").is_dir():
            return p / "VIA_Reports" / "db"
    return None


def _parse_date(v):
    if v is None:
        return None
    if isinstance(v, datetime.datetime):
        return v.date()
    if isinstance(v, datetime.date):
        return v
    s = str(v).strip()
    for rx, f in ((r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", lambda m: (int(m[1]), int(m[2]), int(m[3]))), (r"^(\d{4})(\d{2})(\d{2})$", lambda m: (int(m[1]), int(m[2]), int(m[3]))),
                  (r"^(\d{4})[-/.](\d{1,2})$", lambda m: (int(m[1]), int(m[2]), 1)), (r"^(\d{4})(\d{2})$", lambda m: (int(m[1]), int(m[2]), 1)), (r"^(\d{4})$", lambda m: (int(m[1]), 12, 31)),
                  (r"^(1\d{2})[-/.](\d{1,2})[-/.](\d{1,2})$", lambda m: (int(m[1]) + 1911, int(m[2]), int(m[3])))):
        m = re.match(rx, s)
        if m:
            try:
                y, mo, d = f(m)
                if 1990 <= y <= 2100:
                    return datetime.date(y, mo, d)
            except ValueError:
                return None
    return None


def expected_day(now: datetime.datetime | None = None) -> datetime.date:
    """應有的最新交易日:收盤(16:00)後算今天,否則算前一個工作日(不含國定假日 → 只會偏嚴)。"""
    now = now or datetime.datetime.now()
    d = now.date() if now.hour >= 16 else now.date() - datetime.timedelta(days=1)
    while d.weekday() >= 5:
        d -= datetime.timedelta(days=1)
    return d


def _weekdays_between(a: datetime.date, b: datetime.date) -> int:
    if not a or not b or a >= b:
        return 0
    n, d = 0, a + datetime.timedelta(days=1)
    while d <= b:
        if d.weekday() < 5:
            n += 1
        d += datetime.timedelta(days=1)
    return n


def _freq(dates: list) -> str:
    ds = sorted({d for d in dates if d}, reverse=True)[:120]
    if len(ds) < 3:
        return "單期" if ds else "—"
    gaps = sorted((ds[i] - ds[i + 1]).days for i in range(len(ds) - 1))
    g = gaps[len(gaps) // 2]
    return "日" if g <= 4 else ("週" if g <= 9 else ("月" if g <= 40 else ("季" if g <= 120 else "年")))


def _next_start(last: datetime.date, freq: str) -> datetime.date | None:
    if not last:
        return None
    if freq == "日":
        d = last + datetime.timedelta(days=1)
        while d.weekday() >= 5:
            d += datetime.timedelta(days=1)
        return d
    if freq == "週":
        return last + datetime.timedelta(days=7)
    if freq in ("月", "季", "年"):
        months = {"月": 1, "季": 3, "年": 12}[freq]
        y, m = last.year + (last.month - 1 + months) // 12, (last.month - 1 + months) % 12 + 1
        return datetime.date(y, m, 1)
    return last + datetime.timedelta(days=1)


def _pick(cols: list, names: tuple) -> str | None:
    low = {c.lower(): c for c in cols}
    for n in names:
        if n.lower() in low:
            return low[n.lower()]
    return None


def scan_file(con, p: Path, prev: dict | None, calendar: set | None) -> dict:
    st = p.stat()
    if prev and prev.get("mtime") == st.st_mtime and prev.get("size") == st.st_size and not prev.get("error"):
        return dict(prev, reused=True, rows_delta=0, changed="")
    rel = "read_parquet('%s')" % str(p).replace("'", "''")
    r = {"table": p.stem, "file": str(p), "size": st.st_size, "mtime": st.st_mtime, "reused": False, "error": ""}
    try:
        desc = con.execute("describe select * from %s" % rel).fetchall()
        cols = [(d[0], d[1]) for d in desc]
        r["cols"] = cols
        r["ncols"] = len(cols)
        r["schema_hash"] = hashlib.sha256("|".join("%s:%s" % c for c in cols).encode("utf-8")).hexdigest()[:10]
        r["rows"] = con.execute("select count(*) from %s" % rel).fetchone()[0]
        names = [c[0] for c in cols]
        dcol, tcol = _pick(names, PARAMS["date_cols"]), _pick(names, PARAMS["ticker_cols"])
        r["date_col"], r["ticker_col"] = dcol, tcol
        if dcol and r["rows"]:
            mn, mx = con.execute('select min("%s"), max("%s") from %s' % (dcol, dcol, rel)).fetchone()
            r["min_date"], r["max_date"] = (str(_parse_date(mn) or mn), str(_parse_date(mx) or mx))
            recent = [_parse_date(x[0]) for x in con.execute('select distinct "%s" from %s order by 1 desc limit 400' % (dcol, rel)).fetchall()]
            r["freq"] = _freq(recent)
            r["rows_last"] = con.execute('select count(*) from %s where "%s" = (select max("%s") from %s)' % (rel, dcol, dcol, rel)).fetchone()[0]
            mxd = _parse_date(mx)
            same_market = p.stem.split("__")[0] == "tw"           # 台股日曆只套台股表(全球表跟別的市場日曆)
            if calendar and same_market and r["freq"] == "日" and mxd:
                lo = max(mxd - datetime.timedelta(days=PARAMS["gap_window_days"]), _parse_date(mn) or mxd)   # 不早於該表自己的起始日
                have = {d for d in recent if d and d >= lo}
                miss = sorted(d for d in calendar if lo <= d <= mxd and d not in have)
                r["gaps"] = [str(d) for d in miss]
        if tcol and r["rows"]:
            r["tickers"] = con.execute('select count(distinct "%s") from %s' % (tcol, rel)).fetchone()[0]
        if dcol and tcol and 0 < r["rows"] <= PARAMS["dup_scan_max_rows"]:
            r["dup_keys"] = con.execute('select count(*) from (select "%s", "%s", count(*) c from %s group by 1, 2 having c > 1)' % (dcol, tcol, rel)).fetchone()[0]
    except Exception as exc:  # noqa: BLE001
        r["error"] = "%s:%s" % (type(exc).__name__, str(exc)[:120])
    if prev and not r["error"]:
        r["rows_delta"] = (r.get("rows") or 0) - (prev.get("rows") or 0)
        ch = []
        if r["rows_delta"]:
            ch.append("%+d 列" % r["rows_delta"])
        if prev.get("max_date") != r.get("max_date") and r.get("max_date"):
            ch.append("迄 %s→%s" % (prev.get("max_date") or "—", r["max_date"]))
        if prev.get("schema_hash") and prev.get("schema_hash") != r.get("schema_hash"):
            ch.append("欄位變了")
        r["changed"] = " · ".join(ch) or "檔有更新、內容同"
    else:
        r["rows_delta"], r["changed"] = (0, "首次掃描") if not prev else (0, "")
    return r


def _lamp(r: dict, exp: datetime.date) -> tuple:
    if r.get("error"):
        return "RED", "讀不了:" + r["error"][:60]
    if not r.get("rows"):
        return "RED", "空表"
    if not r.get("date_col"):
        return "GRAY", "無日期欄(清單類)"
    mx = _parse_date(r.get("max_date"))
    f = r.get("freq", "—")
    notes = []
    if f == "日":
        lag = _weekdays_between(mx, exp)
        r["lag"] = "%d 交易日" % lag
        fresh = lag <= 1
    else:
        days = (exp - mx).days if mx else 9999
        r["lag"] = "%d 天" % days
        fresh = days <= {"週": 10, "月": 45, "季": 135, "年": 400}.get(f, 45)
    if not fresh:
        notes.append("落後 %s" % r["lag"])
    if r.get("gaps"):
        notes.append("近 %d 天缺 %d 日" % (PARAMS["gap_window_days"], len(r["gaps"])))
    if r.get("dup_keys"):
        notes.append("重複鍵 %d" % r["dup_keys"])
    return ("GREEN" if not notes else "YELLOW"), " · ".join(notes)


def _fmt_n(n) -> str:
    if n is None:
        return "—"
    n = float(n)
    return "%.2fM" % (n / 1e6) if n >= 1e6 else ("%.1fK" % (n / 1e3) if n >= 1e4 else "%d" % n)


def status(root: Path | None = None) -> dict:
    import duckdb  # noqa: WPS433
    root = root or db_root()
    sdir = root / PARAMS["status_dir"]
    sdir.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in root.rglob("*.parquet") if PARAMS["status_dir"] not in p.parts and not any(x.startswith(("_superseded", "_quarantine", ".")) for x in p.relative_to(root).parts))
    prev_all = {}
    lp = sdir / "DB_STATUS_latest.json"
    if lp.exists():
        try:
            prev_all = {r["file"]: r for r in json.loads(lp.read_text(encoding="utf-8")).get("tables", [])}
        except (OSError, ValueError):
            prev_all = {}
    con = duckdb.connect()
    try:
        con.execute("SET threads TO %d" % max(1, (os.cpu_count() or 2)))
    except Exception:  # noqa: BLE001
        pass
    cal = None
    cal_src = ""
    for p in files:
        if p.stem.endswith("tw_daily_prices"):
            try:
                rel = "read_parquet('%s')" % str(p).replace("'", "''")
                names = [d[0] for d in con.execute("describe select * from %s" % rel).fetchall()]
                dc = _pick(names, PARAMS["date_cols"])
                if dc:
                    cal = {_parse_date(x[0]) for x in con.execute('select distinct "%s" from %s' % (dc, rel)).fetchall()} - {None}
                    cal_src = p.stem
            except Exception:  # noqa: BLE001
                cal = None
            break
    exp = expected_day()
    tables = []
    for p in files:
        r = scan_file(con, p, prev_all.get(str(p)), cal)
        r["group"] = p.stem.split("__")[0] if "__" in p.stem else p.parent.name
        r["lamp"], r["note"] = _lamp(r, exp)
        tables.append(r)
    con.close()
    plan = []
    for r in tables:
        if r.get("date_col") and r.get("rows") and not r.get("error"):
            mx = _parse_date(r.get("max_date"))
            nxt = _next_start(mx, r.get("freq", ""))
            plan.append({"table": r["table"], "file": r["file"], "date_col": r["date_col"], "ticker_col": r.get("ticker_col"), "freq": r.get("freq"), "last": r.get("max_date"), "next_start": str(nxt) if nxt else None,
                         "until": str(exp), "behind": r["lamp"] == "YELLOW" and "落後" in r.get("note", ""), "gaps": r.get("gaps", [])[:30], "dedup_keys": [k for k in (r["date_col"], r.get("ticker_col")) if k], "mode": "append_dedup"})
    lamps = Counter(r["lamp"] for r in tables)
    summ = {"ts": datetime.datetime.now().isoformat(timespec="seconds"), "root": str(root), "tables": len(tables), "bytes": sum(r["size"] for r in tables), "lamps": dict(lamps), "expected_day": str(exp), "calendar": cal_src or "—",
            "rescanned": sum(1 for r in tables if not r.get("reused")), "reused": sum(1 for r in tables if r.get("reused")), "engine": "%s_%s" % (PARAMS["engine"], PARAMS["version"]),
            "accel": "VeritasCeleritas_v1141" if _ACCEL else "—(找不到正本加速器)"}
    out = {"summary": summ, "tables": tables}
    lp.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    (sdir / "VDF_IncrementalPlan_latest.json").write_text(json.dumps({"schema": "VIA.DB.IncrementalPlan.v1", "for": "VDF 擷取引擎(增量:從 next_start 補到 until,依 dedup_keys 去重後附加)", "ts": summ["ts"], "expected_day": summ["expected_day"], "plan": plan}, ensure_ascii=False, indent=1), encoding="utf-8")
    with (sdir / "DB_SNAPSHOT_Ledger.jsonl").open("a", encoding="utf-8") as fh:
        for r in tables:
            if not r.get("reused"):
                fh.write(json.dumps({"ts": summ["ts"], "table": r["table"], "size": r["size"], "mtime": r["mtime"], "rows": r.get("rows"), "max_date": r.get("max_date"), "schema_hash": r.get("schema_hash"), "error": r.get("error", "")}, ensure_ascii=False) + "\n")
    cat = catalog(root, tables)
    summ["catalog"] = cat
    try:
        li = listing_index(root)
        summ["listing"] = {"n": li.get("n", 0), "with_name": li.get("with_name", 0), "with_market": li.get("with_market", 0), "sources": [x.get("table") for x in li.get("sources", []) if x.get("rows")], "errors": [x for x in li.get("sources", []) if x.get("error")]}
    except Exception as exc:  # noqa: BLE001
        summ["listing"] = {"n": 0, "error": "%s:%s" % (type(exc).__name__, str(exc)[:80])}
    card = ai_card(summ, tables, plan)
    (sdir / "DB_STATUS_AI.md").write_text(card, encoding="utf-8")
    page = sdir / "DB_STATUS_latest.html"
    page.write_text(_html(summ, tables), encoding="utf-8")
    rr = _repo_reports()
    if rr:
        try:
            rr.mkdir(parents=True, exist_ok=True)
            (rr / "DB_STATUS_AI.md").write_text(card, encoding="utf-8")
            (rr / "DB_STATUS_latest.html").write_text(_html(summ, tables), encoding="utf-8")
        except OSError:
            pass
    out.update(plan=plan, card=card, card_path=str(sdir / "DB_STATUS_AI.md"), html=str(page))
    return out


def _mkt(v) -> str:
    t = str(v or "").strip().upper()
    if not t:
        return ""
    if "興櫃" in t or "ROTC" in t or t in ("ESB", "EMERGING"):
        return "ESB"
    if "上櫃" in t or "TPEX" in t or t in ("OTC", "TWO", ".TWO", "櫃"):
        return "TPEx"
    if "上市" in t or t in ("TWSE", "TSE", "SII", "TW", ".TW", "市", "LISTED"):
        return "TWSE"
    return ""


def _detect_listing(con, rel: str) -> dict:
    """依欄裡的值認欄:代號(≥80% 是 4–6 碼)· 名稱(中文短字串 · 幾乎不重複)· 市場別(上市 / 上櫃 / 興櫃 …)· 產業(中文 · 少數種類)· 英文名。"""
    names = [d[0] for d in con.execute("describe select * from %s" % rel).fetchall()]
    rows = con.execute("select * from %s limit 3000" % rel).fetchall()
    cols = list(zip(*rows)) if rows else [() for _ in names]
    st = {}
    for n, vals in zip(names, cols):
        vs = [str(v).strip() for v in vals if v is not None and str(v).strip()]
        if not vs:
            continue
        k = len(vs)
        st[n] = {"code": sum(1 for v in vs if re.fullmatch(r"\d{4,6}[A-Z]?(\.TWO?)?", v, re.I)) / k, "cjk": sum(1 for v in vs if re.search(r"[\u4e00-\u9fff]", v)) / k,
                 "avg": sum(len(v) for v in vs) / k, "uniq": len(set(vs)) / k, "nuniq": len(set(vs)), "mkt": sum(1 for v in vs if _mkt(v)) / k,
                 "ascii": sum(1 for v in vs if re.fullmatch(r"[A-Za-z][A-Za-z0-9 .,&'()\-]{2,}", v)) / k}
    hint = lambda n, ws: any(w in n.lower() for w in ws)  # noqa: E731
    code = max((n for n in st if st[n]["code"] >= 0.8), key=lambda n: (hint(n, ("code", "id", "代號", "代碼", "symbol", "ticker")), st[n]["code"]), default=None)
    mkt = max((n for n in st if n != code and st[n]["mkt"] >= 0.7 and st[n]["nuniq"] <= 12), key=lambda n: (hint(n, ("market", "市場", "board", "type")), st[n]["mkt"]), default=None)
    name = max((n for n in st if n not in (code, mkt) and st[n]["cjk"] >= 0.6 and st[n]["avg"] <= 12 and st[n]["uniq"] >= 0.5), key=lambda n: (hint(n, ("name", "名稱", "簡稱", "short")), -st[n]["avg"]), default=None)
    ind = max((n for n in st if n not in (code, mkt, name) and st[n]["cjk"] >= 0.6 and 3 <= st[n]["nuniq"] and st[n]["uniq"] <= 0.3), key=lambda n: (hint(n, ("industry", "產業", "sector", "類別")), -st[n]["nuniq"]), default=None)
    en = max((n for n in st if n not in (code, mkt, name, ind) and st[n]["ascii"] >= 0.7 and hint(n, ("en", "english", "name"))), key=lambda n: st[n]["ascii"], default=None)
    return {"code": code, "name": name, "market": mkt, "industry": ind, "en": en}


def listing_index(root: Path | None = None) -> dict:
    """四碼代號 → 名稱 / 市場別 / 產業 / 英文名(唯讀;來源 = 名稱含 listing 的 parquet,依 mtime 快取在 _status\\LISTING_INDEX.json)。"""
    import duckdb  # noqa: WPS433
    root = root or db_root()
    files = sorted(p for p in root.rglob("*.parquet") if PARAMS["status_dir"] not in p.parts and re.search(r"(?i)listing|stock_?list|company_?basic|universe", p.stem))
    cache = root / PARAMS["status_dir"] / "LISTING_INDEX.json"
    fp = [[str(p), p.stat().st_mtime, p.stat().st_size] for p in files]
    if cache.exists():
        try:
            c = json.loads(cache.read_text(encoding="utf-8"))
            if c.get("fingerprint") == fp:
                return c
        except (OSError, ValueError):
            pass
    out = {"codes": {}, "sources": [], "fingerprint": fp, "ts": datetime.datetime.now().isoformat(timespec="seconds")}
    con = duckdb.connect()
    for p in files:
        rel = "read_parquet('%s')" % str(p).replace("'", "''")
        try:
            cols = _detect_listing(con, rel)
        except Exception as exc:  # noqa: BLE001
            out["sources"].append({"table": p.stem, "error": "%s:%s" % (type(exc).__name__, str(exc)[:80])})
            continue
        if not cols["code"]:
            out["sources"].append({"table": p.stem, "cols": cols, "error": "認不出代號欄"})
            continue
        sel = [c for c in (cols["code"], cols["name"], cols["market"], cols["industry"], cols["en"])]
        q = "select %s from %s" % (", ".join(('"%s"' % c) if c else "null" for c in sel), rel)
        n = 0
        for code, nm, mk, ind, en in con.execute(q).fetchall():
            k = re.sub(r"\.TWO?$", "", str(code or "").strip().upper())
            if not re.fullmatch(r"\d{4,6}[A-Z]?", k):
                continue
            e = out["codes"].setdefault(k, {"name": "", "market": "", "industry": "", "en": ""})
            for key, v in (("name", nm), ("market", _mkt(mk)), ("industry", ind), ("en", en)):
                if v and not e[key]:
                    e[key] = str(v).strip()
            n += 1
        out["sources"].append({"table": p.stem, "cols": cols, "rows": n})
    con.close()
    out["n"] = len(out["codes"])
    out["with_name"] = sum(1 for v in out["codes"].values() if v["name"])
    out["with_market"] = sum(1 for v in out["codes"].values() if v["market"])
    try:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass
    return out


def catalog(root: Path, tables: list) -> dict:
    import duckdb  # noqa: WPS433
    path = root / PARAMS["status_dir"] / "via_catalog.duckdb"
    try:
        con = duckdb.connect(str(path))
        n = 0
        for r in tables:
            if r.get("error"):
                continue
            con.execute('create or replace view "%s" as select * from read_parquet(\'%s\')' % (r["table"].replace('"', ""), r["file"].replace("'", "''")))
            n += 1
        con.execute("create or replace table _vdb_status (tbl varchar, lamp varchar, rows bigint, ncols integer, date_col varchar, min_date varchar, max_date varchar, freq varchar, tickers bigint, note varchar, file varchar)")
        if tables:
            con.executemany("insert into _vdb_status values (?,?,?,?,?,?,?,?,?,?,?)", [(r["table"], r["lamp"], r.get("rows"), r.get("ncols"), r.get("date_col"), r.get("min_date"), r.get("max_date"), r.get("freq"), r.get("tickers"), r.get("note"), r["file"]) for r in tables])
        con.close()
        return {"path": str(path), "views": n, "ok": True}
    except Exception as exc:  # noqa: BLE001
        return {"path": str(path), "views": 0, "ok": False, "err": "%s:%s(多半是別的程式正開著目錄檔)" % (type(exc).__name__, str(exc)[:80])}


def ai_card(s: dict, tables: list, plan: list) -> str:
    L = {"GREEN": "G", "YELLOW": "Y", "RED": "R", "GRAY": "N"}
    lines = ["# VIA DB 現況 %s · 根 %s · %d 表 · %.2f GB · 應有交易日 %s(日曆:%s)" % (s["ts"][:16].replace("T", " "), s["root"], s["tables"], s["bytes"] / 1024 ** 3, s["expected_day"], s["calendar"]),
             "燈 G 新鮮 · Y 落後/缺日/重複 · R 壞或空 · N 無日期欄;擷取與增量寫入由 VDF 負責,本卡唯讀產生",
             "燈|表|列|欄|日期欄 起→迄|頻|代號數|落後|上次後變化"]
    order = {"RED": 0, "YELLOW": 1, "GREEN": 2, "GRAY": 3}
    for r in sorted(tables, key=lambda r: (order.get(r["lamp"], 9), r["table"])):
        lines.append("%s|%s|%s|%s|%s|%s|%s|%s|%s" % (L.get(r["lamp"], "?"), r["table"], _fmt_n(r.get("rows")), r.get("ncols", "—"), ("%s %s→%s" % (r["date_col"], r.get("min_date"), r.get("max_date"))) if r.get("date_col") else "—",
                                                   r.get("freq", "—"), _fmt_n(r.get("tickers")) if r.get("tickers") else "—", r.get("lag", "—") if r.get("date_col") else "—", r.get("changed") or ("沿用" if r.get("reused") else "—")))
    beh = [p for p in plan if p["behind"] or p["gaps"]]
    if beh:
        lines.append("增量(給 VDF):" + " · ".join("%s 從 %s%s" % (p["table"], p["next_start"], (" 缺%d日" % len(p["gaps"])) if p["gaps"] else "") for p in beh[:12]))
    bad = [r for r in tables if r["lamp"] == "RED"]
    if bad:
        lines.append("壞/空:" + " · ".join("%s(%s)" % (r["table"], r["note"]) for r in bad))
    li = s.get("listing") or {}
    if li.get("n"):
        lines.append("代號名冊:%d 碼(有名稱 %d · 有市場別 %d)來源 %s · 查名:python VIA_DuckDBStatus_v0101.py names 2330 2317" % (li["n"], li.get("with_name", 0), li.get("with_market", 0), "+".join(li.get("sources", [])) or "—"))
    lines.append("查詢:python VIA_DuckDBStatus_v0101.py sql \"select * from <表> limit 5\"(目錄 %s · 唯讀)" % Path(s.get("catalog", {}).get("path", "_status/via_catalog.duckdb")).name)
    return "\n".join(lines) + "\n"


def _html(s: dict, tables: list) -> str:
    e = html.escape
    Lc = {"GREEN": "var(--lamp-green,#16a34a)", "YELLOW": "var(--lamp-yellow,#eab308)", "RED": "var(--lamp-red,#dc2626)", "GRAY": "var(--lamp-gray,#9ca3af)"}
    order = {"RED": 0, "YELLOW": 1, "GREEN": 2, "GRAY": 3}
    css = ("body{font-family:'Microsoft JhengHei UI','Segoe UI',Arial;font-size:12px;color:#1f2937;background:#fafafa;margin:0;padding:12px}h1{font-size:15px;margin:0 0 4px}.meta{color:#6b7280;font-size:11px;margin-bottom:6px}"
           ".lp{display:inline-block;width:11px;height:11px;border-radius:50%;vertical-align:middle}.lp.RED{animation:bl 2.4s ease-in-out infinite}@keyframes bl{0%,100%{opacity:1}50%{opacity:.25}}"
           "table{border-collapse:collapse;width:100%;background:#fff;font-size:11.5px}th,td{border:1px solid #eceff3;padding:2px 5px;text-align:left;vertical-align:top}th{background:#111827;color:#fff;position:sticky;top:0}td.n{text-align:right}"
           "details summary{cursor:pointer;color:#2563eb}.wrap{overflow-x:auto}.bar button{font-size:11px;margin-right:4px;padding:2px 8px;border:1px solid #d1d5db;background:#fff;border-radius:6px;cursor:pointer}")
    js = "function f(l){document.querySelectorAll('tbody tr').forEach(function(t){t.style.display=(!l||t.dataset.l===l)?'':'none'})}"
    trs = "".join("<tr data-l='%s'><td><i class='lp %s' style='background:%s'></i></td><td>%s</td><td>%s</td><td class='n'>%s</td><td class='n'>%s</td><td class='n'>%.1f MB</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td class='n'>%s</td><td class='n'>%s</td><td>%s</td><td>%s</td><td>%s</td><td><details><summary>%d 欄</summary>%s</details></td></tr>" % (
        r["lamp"], r["lamp"], Lc[r["lamp"]], e(r["table"]), e(r.get("group", "")), _fmt_n(r.get("rows")), r.get("ncols", "—"), r["size"] / 1024 ** 2, e(r.get("date_col") or "—"), e(str(r.get("min_date") or "—")), e(str(r.get("max_date") or "—")), e(r.get("freq", "—")),
        e(r.get("ticker_col") or "—"), _fmt_n(r.get("tickers")) if r.get("tickers") else "—", _fmt_n(r.get("rows_last")) if r.get("rows_last") else "—", e(r.get("lag", "—")), e(r.get("note", "")), e(r.get("changed") or ("沿用快照" if r.get("reused") else "")),
        len(r.get("cols", [])), e(", ".join("%s:%s" % tuple(c) for c in r.get("cols", [])))) for r in sorted(tables, key=lambda r: (order.get(r["lamp"], 9), r["table"])))
    lamps = " · ".join("<i class='lp %s' style='background:%s'></i> %s %d" % (k, Lc[k], k, v) for k, v in sorted(s["lamps"].items(), key=lambda kv: order.get(kv[0], 9)))
    return ("<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>VIA DB 現況</title><style>" + css + "</style><script>" + js + "</script></head><body>"
            "<h1>VIA 資料庫現況(DuckDB 管理 · 唯讀)</h1><div class='meta'>" + e(s["ts"]) + " · " + e(s["root"]) + " · " + str(s["tables"]) + " 表 · %.2f GB" % (s["bytes"] / 1024 ** 3) + " · 應有交易日 " + e(s["expected_day"]) + "(日曆 " + e(s["calendar"]) + ")· 本次重掃 " + str(s["rescanned"]) + " · 沿用快照 " + str(s["reused"]) + " · 加速器 " + e(s["accel"]) + "</div>"
            "<div class='meta'>" + lamps + " · 目錄 " + e(s.get("catalog", {}).get("path", "")) + "(視圖 " + str(s.get("catalog", {}).get("views", 0)) + ")· 擷取與增量寫入由 VDF 負責;增量計畫給 VDF 讀:VDF_IncrementalPlan_latest.json</div>"
            "<div class='bar' style='margin:6px 0'><button onclick=\"f('')\">全部</button><button onclick=\"f('RED')\">紅</button><button onclick=\"f('YELLOW')\">黃</button><button onclick=\"f('GREEN')\">綠</button><button onclick=\"f('GRAY')\">灰</button></div>"
            "<div class='wrap'><table><thead><tr><th>燈</th><th>表</th><th>群</th><th>列</th><th>欄</th><th>大小</th><th>日期欄</th><th>起</th><th>迄</th><th>頻</th><th>代號欄</th><th>代號數</th><th>最新日列</th><th>落後</th><th>註</th><th>上次後變化</th><th>欄位</th></tr></thead><tbody>" + trs + "</tbody></table></div></body></html>")


def _print_status(o: dict) -> None:
    s = o["summary"]
    lam = s["lamps"]
    worst = "RED" if lam.get("RED") else ("YELLOW" if lam.get("YELLOW") else "GREEN")
    print("[計] VIA DB 現況 · %s · 表 %d · %.2f GB · 新鮮 %d · 落後/缺日 %d · 壞/空 %d · 無日期 %d · 應有交易日 %s · 重掃 %d(沿用快照 %d)· 加速器 %s · %s" % (s["root"], s["tables"], s["bytes"] / 1024 ** 3, lam.get("GREEN", 0), lam.get("YELLOW", 0), lam.get("RED", 0), lam.get("GRAY", 0), s["expected_day"], s["rescanned"], s["reused"], s["accel"], worst))
    for r in [r for r in o["tables"] if r["lamp"] in ("RED", "YELLOW")][:10]:
        print("[計] %s %s · 迄 %s · %s" % ("壞" if r["lamp"] == "RED" else "落後", r["table"], r.get("max_date") or "—", r.get("note", "")))
    ch = [r for r in o["tables"] if not r.get("reused") and r.get("changed") and r.get("changed") != "首次掃描"]
    for r in ch[:5]:
        print("[計] 異動 %s · %s" % (r["table"], r["changed"]))
    c = s.get("catalog", {})
    print("[計] AI 現況卡 %s(%d 字)· 目錄 %s(%s)· 增量計畫 VDF_IncrementalPlan_latest.json" % (o["card_path"], len(o["card"]), Path(c.get("path", "")).name, ("%d 視圖" % c.get("views", 0)) if c.get("ok") else c.get("err", "")))
    li = s.get("listing") or {}
    print("[計] 代號名冊 · %s 碼 · 有名稱 %s · 有市場別 %s · 來源 %s%s" % (li.get("n", 0), li.get("with_name", 0), li.get("with_market", 0), "+".join(li.get("sources", [])) or "—", (" · " + li["error"]) if li.get("error") else "".join(" · %s 認欄失敗" % e.get("table") for e in li.get("errors", []))))
    print("  [U/I] %s" % o["html"])
    print("NEXT: %s" % ("資料庫全新鮮" if worst == "GREEN" else "落後的表交給 VDF 依增量計畫補;壞/空表請 VDF 重抓"))


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args[:2]:
        return selftest()
    verb = args[0] if args else "status"
    if verb == "status":
        try:
            import duckdb as _d  # noqa: WPS433
            dv = _d.__version__
        except ImportError:
            dv = "沒裝"
        _shield_probe()
        print("[計] 啟動 VIA_DuckDBStatus_v0101 · python %s · duckdb %s · 根 %s(%s)· 正本加速器 %s · %s" % (sys.version.split()[0], dv, db_root(), "在" if db_root().is_dir() else "不在", "✓" if _ACCEL else "✗", _SHIELD.get("note")), flush=True)
        if dv == "沒裝":
            print("[計] 失敗 · 這個 python 沒有 duckdb → 請 VCGC 安裝 duckdb")
            return 1
        if not db_root().is_dir():
            print("[計] 失敗 · 資料庫根不在 %s(設 VIA_DB_ROOT 或確認 OneDrive 已同步)· RED" % db_root())
            return 1
        _print_status(status())
        return 0
    if verb == "names":
        li = listing_index()
        for c in args[1:]:
            e = li["codes"].get(c.upper().split(".")[0]) or {}
            print("%s|%s|%s|%s" % (c, e.get("name") or "—", e.get("market") or "—", e.get("industry") or "—"))
        return 0
    import duckdb  # noqa: WPS433
    cat = db_root() / PARAMS["status_dir"] / "via_catalog.duckdb"
    if not cat.exists():
        _print_status(status())
    if verb == "schema" and len(args) >= 2:
        con = duckdb.connect(str(cat), read_only=True)
        cols = con.execute('describe "%s"' % args[1].replace('"', "")).fetchall()
        con.close()
        print("%s:%s" % (args[1], ", ".join("%s %s" % (c[0], c[1]) for c in cols)))
        return 0
    if verb == "sql" and len(args) >= 2:
        con = duckdb.connect(str(cat), read_only=True)
        cur = con.execute(" ".join(args[1:]))
        names = [d[0] for d in cur.description]
        rows = cur.fetchmany(30)
        con.close()
        print("|".join(names))
        for r in rows:
            print("|".join("" if v is None else str(v) for v in r))
        return 0
    if verb == "plan":
        p = json.loads((db_root() / PARAMS["status_dir"] / "VDF_IncrementalPlan_latest.json").read_text(encoding="utf-8"))
        for x in p["plan"]:
            print("%s · %s · 迄 %s → 從 %s 補到 %s%s · 去重鍵 %s" % (x["table"], x["freq"], x["last"], x["next_start"], x["until"], (" · 缺 %d 日" % len(x["gaps"])) if x["gaps"] else "", "+".join(x["dedup_keys"])))
        return 0
    print("用法:status | names <代號…> | schema <表> | sql \"<查詢>\" | plan | --selftest")
    return 2


def selftest() -> int:
    import shutil
    import tempfile
    import duckdb  # noqa: WPS433
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)
    td = Path(tempfile.mkdtemp(prefix="viadb-"))
    root = td / "via_database"
    vdb = root / "vdf_database"
    vdb.mkdir(parents=True)
    saved = os.environ.get("VIA_DB_ROOT")
    os.environ["VIA_DB_ROOT"] = str(root)
    exp = expected_day()
    con = duckdb.connect()

    def weekdays(a, b):
        d, out = a, []
        while d <= b:
            if d.weekday() < 5:
                out.append(d)
            d += datetime.timedelta(days=1)
        return out
    cal = weekdays(datetime.date(2026, 7, 1), datetime.date(2026, 8, 25))
    rows = [(t, d, 100.0 + i, 99.0 + i) for i, d in enumerate(cal) for t in ("2330", "2317")]
    con.execute("create table px (ticker varchar, date date, close double, adj_close double)")
    con.executemany("insert into px values (?,?,?,?)", rows)
    con.execute("copy px to '%s' (format parquet)" % (vdb / "tw__tw_daily_prices.parquet"))
    chip = [(t, d, 1) for d in cal if d not in (cal[-3], cal[-5]) for t in ("2330",)] + [("2330", cal[0], 1)]
    con.execute("create table chip (stock_id varchar, date date, net bigint)")
    con.executemany("insert into chip values (?,?,?)", chip)
    con.execute("copy chip to '%s' (format parquet)" % (vdb / "tw__tw_chip_inst.parquet"))
    con.execute("create table rev as select '2330' stock_id, ym, 1000 revenue from (values ('2026-05'), ('2026-06'), ('2026-07'), ('2026-08')) t(ym)")
    con.execute("copy rev to '%s' (format parquet)" % (vdb / "tw__tw_monthly_revenue.parquet"))
    con.execute("create table lst as select * from (values ('2330', '台積電'), ('2317', '鴻海')) t(stock_id, name)")
    con.execute("copy lst to '%s' (format parquet)" % (vdb / "tw__tw_listings.parquet"))
    mac = [("CPI", d, 1.0) for d in weekdays(exp - datetime.timedelta(days=20), exp)]
    con.execute("create table mac (series varchar, date date, value double)")
    con.executemany("insert into mac values (?,?,?)", mac)
    con.execute("copy mac to '%s' (format parquet)" % (vdb / "gl__us_macro.parquet"))
    con.execute("copy (select * from px where false) to '%s' (format parquet)" % (vdb / "gl__empty.parquet"))
    o = status()
    T = {r["table"]: r for r in o["tables"]}
    chk("① 掃 6 表 · 綠 gl__us_macro(新鮮;台股日曆不套全球表)· 灰 listings(無日期)· 紅 empty(空表)", len(T) == 6 and T["gl__us_macro"]["lamp"] == "GREEN" and not T["gl__us_macro"].get("gaps") and T["tw__tw_listings"]["lamp"] == "GRAY" and T["gl__empty"]["lamp"] == "RED")
    px = T["tw__tw_daily_prices"]
    chk("② 日資料落後:迄 2026-08-25 · 頻率 日 · 代號 2 · 黃燈 · 增量計畫從 2026-08-26 補", px["lamp"] == "YELLOW" and px["max_date"] == "2026-08-25" and px["freq"] == "日" and px["tickers"] == 2 and any(x["table"] == "tw__tw_daily_prices" and x["next_start"] == "2026-08-26" for x in o["plan"]))
    ch = T["tw__tw_chip_inst"]
    chk("③ 以價格表當交易日曆:籌碼表近 60 天缺 2 日 · 重複鍵 1", len(ch.get("gaps", [])) == 2 and ch.get("dup_keys") == 1 and ch["lamp"] == "YELLOW")
    rv = T["tw__tw_monthly_revenue"]
    chk("④ 月資料:頻率 月 · 迄 2026-08-01 · 下次從 2026-09-01", rv["freq"] == "月" and any(x["table"] == "tw__tw_monthly_revenue" and x["next_start"] == "2026-09-01" for x in o["plan"]))
    card = o["card"]
    chk("⑤ AI 現況卡:一表一行 · 小於 2500 字 · 有增量提示與查詢方式", len(card) < 2500 and all(t in card for t in T) and "增量(給 VDF)" in card and "查詢:" in card)
    o2 = status()
    chk("⑥ 增量掃描:檔沒變 → 全部沿用快照(重掃 0)", o2["summary"]["rescanned"] == 0 and o2["summary"]["reused"] == 6)
    more = rows + [(t, datetime.date(2026, 8, 26), 200.0, 199.0) for t in ("2330", "2317")]
    con.execute("delete from px")
    con.executemany("insert into px values (?,?,?,?)", more)
    con.execute("copy px to '%s' (format parquet)" % (vdb / "tw__tw_daily_prices.parquet"))
    o3 = status()
    T3 = {r["table"]: r for r in o3["tables"]}
    chk("⑦ VDF 增量寫入後只重掃那一檔 · 變化 +2 列 · 迄 08-25→08-26", o3["summary"]["rescanned"] == 1 and T3["tw__tw_daily_prices"]["rows_delta"] == 2 and "2026-08-26" in T3["tw__tw_daily_prices"]["changed"])
    import io
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        main(["sql", "select count(*) n from tw__tw_daily_prices where ticker = '2330'"])
    chk("⑧ DuckDB 目錄:每表一個視圖 · 唯讀 sql 查得到(2330 有 %s 列)" % buf.getvalue().strip().splitlines()[-1], buf.getvalue().strip().splitlines()[-1] == str(len(cal) + 1) and o3["summary"]["catalog"]["views"] == 6)
    chk("⑨ 只讀 parquet(原檔沒被改)· 狀態全寫在 _status · 快照帳只增", (root / "_status" / "DB_SNAPSHOT_Ledger.jsonl").read_text(encoding="utf-8").count("\n") == 6 + 1 and all(p.parent == vdb for p in vdb.glob("*.parquet")))
    con.execute("copy (select * from (values ('2330','台積電','上市','半導體業'),('2317','鴻海','上市','其他電子業'),('6488','環球晶','上櫃','半導體業'),('3653','健策','上市','電子零組件業')) t(公司代號, 公司簡稱, 市場別, 產業別)) to '%s' (format parquet)" % (vdb / "tw__tw_listings.parquet"))
    li = listing_index(root)
    buf2 = io.StringIO()
    with contextlib.redirect_stdout(buf2):
        main(["names", "3653", "6488"])
    chk("⑪ 代號名冊:中文欄名也認得出(公司代號 / 公司簡稱 / 市場別 / 產業別)· names 3653 → 健策|TWSE · 6488 → 環球晶|TPEx", li["n"] == 4 and li["codes"]["3653"]["name"] == "健策" and li["codes"]["6488"]["market"] == "TPEx" and "3653|健策|TWSE" in buf2.getvalue() and "6488|環球晶|TPEx" in buf2.getvalue())
    global _ACCEL
    saved_acc = _ACCEL

    class _FakeFactory:
        @staticmethod
        def shield(name):
            def deco(fn):
                return fn
            return deco

    class _FakeGood:
        @staticmethod
        def shield(fn):
            def wrap(*a, **k):
                return fn(*a, **k)
            return wrap
    _ACCEL = _FakeFactory
    _SHIELD.clear()
    bad = _shield_probe()
    _ACCEL = _FakeGood
    _SHIELD.clear()
    good = _shield_probe()
    _ACCEL = saved_acc
    _SHIELD.clear()
    chk("⑫ 正本 shield 探測:工廠式(shield(名字) 回裝飾器)→ 不套 · 一般裝飾器 → 套用", bad is None and callable(good))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑩ 正本加速器 VeritasCeleritas_v1141 · 正本網路工具 VeritasAegisNexus_v1652(接口)· 本引擎不出網", "import VeritasCeleritas_v1141" in src and "import VeritasAegisNexus_v1652" in src and not re.search(r"^\s*import\s+(requests|httpx|urllib\.request)", src, re.M))
    con.close()
    if saved is None:
        os.environ.pop("VIA_DB_ROOT", None)
    else:
        os.environ["VIA_DB_ROOT"] = saved
    shutil.rmtree(td, ignore_errors=True)
    print("[計] VIA_DuckDBStatus_v0101 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


def _run() -> int:
    fn = _shield_probe()
    return (fn(main) if fn else main)() or 0


if __name__ == "__main__":
    try:
        _rc = _run()
    except SystemExit:
        raise
    except BaseException as _exc:  # noqa: BLE001
        import traceback
        _tb = traceback.extract_tb(_exc.__traceback__)
        _last = _tb[-1] if _tb else None
        print("[計] VIA_DuckDBStatus 失敗 · %s: %s · %s:%s" % (type(_exc).__name__, str(_exc)[:200], Path(_last.filename).name if _last else "?", _last.lineno if _last else "?"), flush=True)
        _rc = 1
    raise SystemExit(_rc)
