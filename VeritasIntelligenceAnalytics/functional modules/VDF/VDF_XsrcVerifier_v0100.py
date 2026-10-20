#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_XsrcVerifier v0100 — 跨來源對照結果的獨立驗證器(VDF 自己的;不匯入 ActivateVDF 的程式 · 自己的日期解析 · 自己的判定寫法)

操作員令(2026-10-20):「GO ON TO RESULTS VERIFIED 100% CORRECT AND HTML U/I · 收尾變成功」。
ActivateVDF v0110 擷取後寫中間檔(本輪 temp/xsrc/<資料集>/<資料集>__<來源>.csv)與對照結果(__對照結果.csv)→ 本支逐項核對:
  V0 中間檔欄位與來源標註:每檔一個來源 · 每列 source / dataset 欄 = 檔名
  V1 每一筆回資料庫原表整批比對:同(原寫法日期 · 代號 · 來源 · 欄位)原表值的 str() 與中間檔一字不差(同來源多次抓取 → 最新那次)
  V2 日期:中間檔一律 YYYY / YYYY-MM / YYYY-MM-DD,且等於原寫法的獨立重算(逐種格式 strptime + 明列民國)
  V3 判定獨立重算(Decimal):兩個以上來源相同 = 成功(VERIFIED · 一致的來源 · 離群)· 有兩個以上來源但沒有任兩個相同 = 衝突 · 一個來源 = 單一;
     結果每列的判定 / 來源 / 一致 / 離群 / 每個來源的值都要對;結果多一列或少一列都算不符
  V4 計數:總覽 / 頁面上的成功 · 衝突 · 單一 · 可對照 · 每資料集 = 重算
  V5 日期格式體檢重掃:每個列出的欄 → 不標準筆數 · 是否標準 = 重掃
  指紋:對照結果每列排序後 SHA-256 —— U/I 頁與本報告各自算,相同才把判決套到頁上。
判決:全部不符 0 = PASS(結果 100% 正確)· 任一項有不符 = FAIL(結果不可信 → ActivateVDF 總燈紅)· 沒有可對照資料 = EMPTY。
用法:python VDF_XsrcVerifier_v0100.py <xsrc 夾> [--summary ACTIVATE_VDF_*.json] [--db <庫.duckdb> …] · --selftest
VDF 自己的模組:資料庫只唯讀附掛;不匯入他系統程式;同意閘不讀不寫;不碰 TA-Lib;不裝套件、不寫環境。
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

import csv
import hashlib
import json
import re
import sys
import tempfile
import unicodedata
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

TAG = "VDF_XsrcVerifier v" + Path(__file__).stem.rsplit("_v", 1)[-1]
_PRICE = {"close", "open", "high", "low"}
_KEYS = {"code", "ticker", "symbol", "stock_id", "series", "series_id", "isin", "代號", "證券代號", "股票代號"}
_STD_RE = re.compile(r"^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?$")
_HDR_SRC = ["dataset", "source", "key", "date", "field", "value", "date_raw", "origin"]
_HDR_RES = ["dataset", "key", "date", "field", "status", "sources", "agree", "outliers", "values"]


# ---------------------------------------------------------------- 日期(獨立寫法:逐種格式 strptime / 明列民國;不共用 ActivateVDF 的程式)
def _valid(y: int, m: int = 1, d: int = 1) -> bool:
    try:
        date(y, m, d)
        return 1900 <= y <= 2100
    except ValueError:
        return False


def is_standard(s: str) -> bool:
    """標準 = YYYY / YYYY-MM / YYYY-MM-DD 而且是真的日期。"""
    g = _STD_RE.match(str(s or ""))
    if not g:
        return False
    y, m, d = int(g.group(1)), int(g.group(2) or 1), int(g.group(3) or 1)
    return _valid(y, m, d)


_MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]


def indep_iso(raw: str):
    """獨立重算原寫法 → 標準日期;認不出 → None。"""
    s = str(raw).strip()
    if not s:
        return None
    s = re.sub(r"[T ]\d{1,2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:?\d{2})?$", "", s)
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y%m%d"):
        try:
            v = datetime.strptime(s, fmt).date()
        except ValueError:
            continue
        if _valid(v.year) and len(s) >= 8:            # 1150824 會被 %Y%m%d 讀成 1150 年 → 不收,往下試民國
            return v.isoformat()
    roc = re.fullmatch(r"(?:民國)?\s*(\d{2,3})(?:[/.-]|年)\s*(\d{1,2})(?:[/.-]|月)\s*(\d{1,2})日?", s) or re.fullmatch(r"(\d{3})(\d{2})(\d{2})", s)
    if roc:
        y, m, d = int(roc.group(1)) + 1911, int(roc.group(2)), int(roc.group(3))
        return "%04d-%02d-%02d" % (y, m, d) if _valid(y, m, d) else None
    cj = re.fullmatch(r"(\d{4})年\s*(\d{1,2})月\s*(\d{1,2})日?", s)
    if cj:
        y, m, d = (int(x) for x in cj.groups())
        return "%04d-%02d-%02d" % (y, m, d) if _valid(y, m, d) else None
    for fmt in ("%d %b %Y", "%b %d, %Y", "%B %d, %Y", "%d-%b-%Y", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            v = datetime.strptime(s, fmt).date()
            return v.isoformat() if _valid(v.year) else None
        except ValueError:
            pass
    for fmt in ("%Y-%m", "%Y/%m", "%Y.%m", "%Y%m"):
        try:
            v = datetime.strptime(s, fmt)
            if len(s) >= 6 and _valid(v.year, v.month):
                return "%04d-%02d" % (v.year, v.month)
        except ValueError:
            pass
    rym = re.fullmatch(r"(?:民國)?\s*(\d{2,3})(?:[/.-]|年)\s*(\d{1,2})月?份?", s) or re.fullmatch(r"(\d{3})(\d{2})", s)
    if rym:
        y, m = int(rym.group(1)) + 1911, int(rym.group(2))
        return "%04d-%02d" % (y, m) if _valid(y, m) else None
    cym = re.fullmatch(r"(\d{4})年\s*(\d{1,2})月份?", s)
    if cym:
        y, m = int(cym.group(1)), int(cym.group(2))
        return "%04d-%02d" % (y, m) if _valid(y, m) else None
    q = re.fullmatch(r"(?i)(\d{4})\s*-?\s*Q([1-4])", s)
    if q:
        return "%s-%02d" % (q.group(1), int(q.group(2)) * 3)
    if re.fullmatch(r"\d{4}", s) and _valid(int(s)):
        return s
    return None


# ---------------------------------------------------------------- 相同(獨立寫法:Decimal 算差距;規格同操作員令:兩個以上來源相同)
def _dec_places(t: str) -> int:
    t = t.strip().replace(",", "").strip("()").rstrip("%")
    if "e" in t.lower() or "." not in t:
        return 6
    return min(len(t.split(".", 1)[1]), 6)


def _to_dec(t):
    if t is None:
        return None
    u = str(t).strip().replace(",", "")
    neg = u.startswith("(") and u.endswith(")")
    u = u.strip("()").rstrip("%")
    try:
        v = Decimal(u)
    except InvalidOperation:
        return None
    return -v if neg else v


def agree(a: str, b: str, field: str) -> bool:
    da, db = _to_dec(a), _to_dec(b)
    if da is None or db is None:
        ta, tb = (re.sub(r"\s+", "", unicodedata.normalize("NFKC", str(x))).casefold() for x in (a, b))
        return da is None and db is None and bool(ta) and ta == tb
    places = 2 if field.lower() in _PRICE else (0 if field.lower() == "revenue" else min(_dec_places(str(a)), _dec_places(str(b))))
    return abs(da - db) <= Decimal("0.5") * (Decimal(10) ** -places)


def judge(values: dict, field: str) -> tuple:
    """回(判定, 一致的來源, 離群)。最大的一致群 ≥ 2 → VERIFIED;多個來源但沒有兩兩一致 → CONFLICT;一個來源 → SINGLE。"""
    srcs = sorted(values)
    if len(srcs) == 1:
        return "SINGLE", srcs, []
    groups = []
    for i, s in enumerate(srcs):
        groups.append([s] + [t for t in srcs[i + 1:] if agree(values[s], values[t], field)])
    best = max(groups, key=len)                    # max 回第一個最大的(來源字母序在前的那一群)
    if len(best) < 2:
        return "CONFLICT", [], []
    return "VERIFIED", best, [s for s in srcs if s not in best]


# ---------------------------------------------------------------- 讀中間檔 / 結果
def _read(p: Path) -> list:
    with open(p, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def result_rows(xdir: Path) -> list:
    out = []
    for p in sorted(Path(xdir).glob("*/*__對照結果.csv")):
        out += _read(p)
    return out


def fingerprint(rows: list) -> str:
    """結果指紋:對照結果每列(固定欄序)排序後 SHA-256;U/I 頁與驗證報告各自算,相同才套用判決。"""
    lines = sorted("\t".join(str(r.get(k, "")) for k in _HDR_RES) for r in rows)
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------- 回資料庫整批核對(一個來源檔 · 一個欄位 · 一個查詢)
_DHINT = re.compile(r"(?i)date|period|month|year|quarter|timestamp|(^|_)(dt|day|time|ts|ym|yyyymm|yr|qtr|asof)($|_)|日期|年月|年度|年份|月份|季別|期間|期別|時間|交易日|資料日")
_META = re.compile(r"(?i)^(fetched_at|updated_at|created_at|inserted_at|loaded_at|ingested_at|_?ts|run_ts|write_ts)$")


def _qi(c: str) -> str:
    return '"' + str(c).replace('"', '""') + '"'


def trace_file(con, db: Path, table: str, rows: list) -> list:
    """一個來源檔(同一原表)的每一列回原表取值;回不符清單。值比對 = 原表值的 str() 與中間檔那格一字不差。"""
    con.execute("DETACH DATABASE IF EXISTS src")
    con.execute("ATTACH '%s' AS src (READ_ONLY)" % str(db).replace("'", "''"))
    cols = {r[0].lower(): r[0] for r in con.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_catalog = 'src' AND table_name = ? ORDER BY ordinal_position", [table]).fetchall()}
    order = [r[0] for r in con.execute("SELECT column_name FROM information_schema.columns WHERE table_catalog = 'src' AND table_name = ? "
                                       "ORDER BY ordinal_position", [table]).fetchall()]
    if not cols:
        return ["原表 %s:%s 不存在" % (db.name, table)]
    fd, tmp = tempfile.mkstemp(suffix=".csv")
    with open(fd, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["idx", "key", "date_raw", "field", "value", "source"])
        for i, r in enumerate(rows):
            w.writerow([i, r["key"], r["date_raw"], r["field"], r["value"], r["source"]])
    con.execute("CREATE OR REPLACE TEMP TABLE t AS SELECT * FROM read_csv(?, header = true, all_varchar = true)", [tmp])
    Path(tmp).unlink(missing_ok=True)
    got: dict = {}
    for fld in sorted({r["field"] for r in rows}):
        f = cols.get(fld.lower())
        if not f:
            continue
        if table == "tw_trading_daily":
            sql = ("SELECT CAST(t.idx AS INTEGER), s.%s FROM t JOIN src.tw_trading_daily s ON CAST(s.%s AS VARCHAR) = t.date_raw "
                   "AND trim(CAST(s.%s AS VARCHAR)) = t.key AND upper(CAST(s.%s AS VARCHAR)) = t.source WHERE t.field = ?"
                   % (_qi(f), _qi(cols["date"]), _qi(cols["code"]), _qi(cols.get("market", "market"))))
        elif table == "tw_daily_prices":
            sql = ("SELECT CAST(t.idx AS INTEGER), s.%s FROM t JOIN src.tw_daily_prices s ON CAST(s.%s AS VARCHAR) = t.date_raw "
                   "AND trim(split_part(CAST(s.%s AS VARCHAR), '.', 1)) = t.key AND t.source = 'YAHOO' WHERE t.field = ?"
                   % (_qi(f), _qi(cols["date"]), _qi(cols["ticker"])))
        else:
            keys = [c for c in order if c.lower() in _KEYS]
            dcol = next((c for c in order if _DHINT.search(c) and not _META.match(c)), None)
            if "source" not in cols or not keys or not dcol:
                return ["原表 %s:%s 沒有 source / 代號 / 日期欄" % (db.name, table)]
            kexpr = " || '|' || ".join("CAST(s.%s AS VARCHAR)" % _qi(k) for k in keys)
            latest = (" QUALIFY row_number() OVER (PARTITION BY t.idx ORDER BY s.%s DESC) = 1" % _qi(cols["fetched_at"])) if "fetched_at" in cols else ""
            sql = ("SELECT CAST(t.idx AS INTEGER), s.%s FROM t JOIN src.%s s ON CAST(s.%s AS VARCHAR) = t.date_raw AND %s = t.key "
                   "AND CAST(s.source AS VARCHAR) = t.source WHERE t.field = ?%s" % (_qi(f), _qi(table), _qi(dcol), kexpr, latest))
        for idx, v in con.execute(sql, [fld]).fetchall():
            got.setdefault(idx, []).append("None" if v is None else str(v))
    bad = []
    for i, r in enumerate(rows):
        g = got.get(i, [])
        if len(set(g)) != 1 or g[0] != r["value"]:
            bad.append("%s %s %s %s %s:中間檔 %s · 原表 %s" % (r["_file"], r["key"], r["date_raw"], r["field"], r["source"], r["value"], g or "沒有這一筆"))
    return bad


def verify(xdir, summary: dict | None = None, dbs: list | None = None, datefmt: dict | None = None) -> dict:
    """六項獨立核對 → {verdict PASS / FAIL, checks, fingerprint, rows}。任何一項有不符 = FAIL(結果不可信)。"""
    xdir = Path(xdir)
    checks = {}

    def put(name, n, bad, ex, note=""):
        checks[name] = {"n": n, "bad": len(bad) if isinstance(bad, list) else bad, "examples": (bad[:5] if isinstance(bad, list) else ex)[:5], "note": note}

    src_files = sorted(p for p in xdir.glob("*/*.csv") if not p.name.endswith("__對照結果.csv"))
    rows = []
    hdr_bad = []
    for p in src_files:
        rs = _read(p)
        if rs and list(rs[0].keys()) != _HDR_SRC:
            hdr_bad.append(p.name)
        ds, src = p.parent.name, p.stem.split("__", 1)[-1]
        for r in rs:
            r["_file"] = p.name
            if r.get("source") != src or r.get("dataset") != ds:
                hdr_bad.append("%s:%s/%s" % (p.name, r.get("dataset"), r.get("source")))
            rows.append(r)
    put("V0 中間檔欄位與來源標註(每檔一來源 · source 欄 = 檔名來源)", len(src_files), hdr_bad, [])
    # V1 回資料庫逐筆
    by_name = {Path(f).name: Path(f) for f in (dbs or [])}
    bad1, n1 = [], 0
    try:
        import duckdb
    except ImportError:
        duckdb = None
    if duckdb is None:
        put("V1 中間檔每一筆回資料庫原表逐筆比對(值與來源一字不差)", 0, [], [], "沒有 duckdb(不代裝)→ 不驗")
    else:
        con = duckdb.connect()
        try:
            grp: dict = {}
            for r in rows:
                grp.setdefault(r.get("origin", ""), []).append(r)
            for origin, rs in sorted(grp.items()):
                n1 += len(rs)
                db, _, table = origin.partition(":")
                if db not in by_name:
                    bad1 += ["%s 原庫 %s 不在清單" % (r["_file"], db) for r in rs]
                    continue
                bad1 += trace_file(con, by_name[db], table, rs)
        finally:
            con.close()
        put("V1 中間檔每一筆回資料庫原表逐筆比對(值與來源一字不差)", n1, bad1, [])
    # V2 日期
    bad2 = [("%s %s:%s → %s(獨立重算 %s)" % (r["_file"], r["key"], r["date_raw"], r["date"], indep_iso(r["date_raw"])))
            for r in rows if not is_standard(r["date"]) or indep_iso(r["date_raw"]) != r["date"]]
    put("V2 日期:中間檔一律 YYYY / YYYY-MM / YYYY-MM-DD,且等於原寫法的獨立重算", len(rows), bad2, [])
    # V3 判定重算(同一來源同一筆有兩列 → 第一列生效,同 ActivateVDF;值不同另列提醒)
    groups, dup = {}, []
    for r in rows:
        k = (r["dataset"], r["key"], r["date"], r["field"])
        g = groups.setdefault(k, {})
        if r["source"] in g:
            if g[r["source"]] != r["value"]:
                dup.append("%s %s %s %s %s:%s / %s" % (r["dataset"], r["key"], r["date"], r["field"], r["source"], g[r["source"]], r["value"]))
            continue
        g[r["source"]] = r["value"]
    res = result_rows(xdir)
    res_by = {(r["dataset"], r["key"], r["date"], r["field"]): r for r in res}
    bad3 = []
    cnt = {"VERIFIED": 0, "CONFLICT": 0, "SINGLE": 0}
    per: dict = {}
    for k, vals in groups.items():
        st, ag, out = judge(vals, k[3])
        cnt[st] += 1
        pd_ = per.setdefault(k[0], {"VERIFIED": 0, "CONFLICT": 0, "SINGLE": 0})
        pd_[st] += 1
        r = res_by.get(k)
        want = (st, "/".join(sorted(vals)), "/".join(ag) if st == "VERIFIED" else "", "/".join(out) if st == "VERIFIED" else "")
        have = (r["status"], r["sources"], r["agree"], r["outliers"]) if r else None
        if have != want:
            bad3.append("%s %s %s %s:結果 %s · 重算 %s" % (k[0], k[1], k[2], k[3], have, want))
        elif {s: str(v) for s, v in json.loads(r["values"]).items()} != {s: vals[s] for s in vals}:
            bad3.append("%s %s %s %s:結果的值 %s ≠ 中間檔 %s" % (k[0], k[1], k[2], k[3], r["values"], vals))
    extra = [k for k in res_by if k not in groups]
    bad3 += ["結果多一列(中間檔沒有):%s" % "/".join(k) for k in extra]
    put("V3 判定獨立重算(兩個以上來源相同 = 成功 · 衝突 · 單一;一致的來源 · 離群 · 每個來源的值)", len(groups), bad3, [],
        ("同一來源同一筆兩個值 %d 處(第一列生效)" % len(dup)) if dup else "")
    # V4 計數
    bad4 = []
    if summary:
        if summary.get("counts") != cnt:
            bad4.append("總計 %s ≠ 重算 %s" % (summary.get("counts"), cnt))
        for ds, c in (summary.get("datasets") or {}).items():
            if {k: c.get(k) for k in cnt} != per.get(ds, {}):
                bad4.append("%s:%s ≠ 重算 %s" % (ds, {k: c.get(k) for k in cnt}, per.get(ds)))
        comp = cnt["VERIFIED"] + cnt["CONFLICT"]
        if summary.get("comparable") != comp:
            bad4.append("可對照 %s ≠ 重算 %s" % (summary.get("comparable"), comp))
    put("V4 計數(總覽 / 頁面上的成功 · 衝突 · 單一 · 每資料集)= 重算", 1 if summary else 0, bad4, [], "" if summary else "沒給總覽 → 不驗")
    # V5 日期體檢重掃
    bad5, n5 = [], 0
    if datefmt and duckdb is not None:
        con = duckdb.connect()
        try:
            for c in datefmt.get("items") or []:
                if c.get("db") not in by_name or c.get("standard") is None:
                    continue
                n5 += 1
                con.execute("DETACH DATABASE IF EXISTS d5")
                con.execute("ATTACH '%s' AS d5 (READ_ONLY)" % str(by_name[c["db"]]).replace("'", "''"))
                tb = c["table"].split(".", 1)
                ref = ("d5.%s.%s" % tuple('"%s"' % x.replace('"', '""') for x in tb)) if len(tb) == 2 else 'd5."%s"' % tb[0].replace('"', '""')
                col = '"%s"' % c["column"].replace('"', '""')
                typ = str(c.get("type", "")).upper()
                seen = None
                if typ == "DATE":
                    ok_ = c.get("standard") is True
                elif typ.startswith("TIMESTAMP"):
                    n_t = con.execute("SELECT count(*) FROM %s WHERE %s IS NOT NULL AND CAST(%s AS TIME) <> TIME '00:00:00'" % (ref, col, col)).fetchone()[0]
                    seen = n_t
                    ok_ = (c.get("nonstd") == n_t) and (c.get("standard") == (n_t == 0))
                else:
                    vals = [v[0] for v in con.execute("SELECT DISTINCT CAST(%s AS VARCHAR) FROM %s WHERE %s IS NOT NULL LIMIT 20000" % (col, ref, col)).fetchall()]
                    seen = sum(1 for v in vals if not is_standard(v))
                    ok_ = c.get("nonstd") == seen and c.get("standard") == (seen == 0)
                if not ok_:
                    bad5.append("%s %s.%s:體檢 不標準 %s · 重掃 %s" % (c["db"], c["table"], c["column"], c.get("nonstd"), seen))
        finally:
            con.close()
    put("V5 日期格式體檢重掃(每個列出的欄:不標準筆數 · 是否標準)", n5, bad5, [], "" if datefmt else "沒給體檢 → 不驗")
    fp = fingerprint(res)
    verdict = "PASS" if all(c["bad"] == 0 for c in checks.values()) and rows else ("EMPTY" if not rows else "FAIL")
    return {"tag": TAG, "verdict": verdict, "checks": checks, "fingerprint": fp, "rows": len(rows), "items": len(res),
            "dup_values": dup[:20], "dup_count": len(dup)}


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["--selftest"]:
        return selftest()
    if not a:
        print("用法:%s <xsrc 夾> [--summary 總覽.json] [--db 庫.duckdb …]" % Path(__file__).name)
        return 2
    xdir, summary, datefmt, dbs = Path(a[0]), None, None, []
    i = 1
    while i < len(a):
        if a[i] == "--summary":
            card = json.loads(Path(a[i + 1]).read_text(encoding="utf-8"))
            summary, datefmt = card.get("xsrc", card), card.get("datefmt")
            i += 2
        elif a[i] == "--db":
            dbs.append(Path(a[i + 1]))
            i += 2
        else:
            i += 1
    rep = verify(xdir, summary, dbs, datefmt)
    for name, c in rep["checks"].items():
        print("  [%s] %s · %s 筆 · 不符 %s%s" % ("OK" if c["bad"] == 0 else "FAIL", name, c["n"], c["bad"], (" · " + c["note"]) if c["note"] else ""))
        for e in c["examples"]:
            print("       - " + str(e))
    print("[計] %s 判決 %s · 中間檔 %d 筆 · 結果 %d 列 · 指紋 %s" % (TAG, rep["verdict"], rep["rows"], rep["items"], rep["fingerprint"][:16]))
    return 0 if rep["verdict"] == "PASS" else 1


# ---------------------------------------------------------------- 自測(自己造庫、手寫中間檔與結果;不借用 ActivateVDF 的程式)
def _fixture(root: Path) -> tuple:
    import duckdb
    root.mkdir(parents=True, exist_ok=True)
    db = root / "vdf_tw_market.duckdb"
    c = duckdb.connect(str(db))
    c.execute("CREATE TABLE tw_trading_daily(date VARCHAR, code VARCHAR, market VARCHAR, close DOUBLE)")
    c.execute("INSERT INTO tw_trading_daily VALUES ('1150824','2330','TWSE',1045.0),('1150824','2317','TWSE',200.0)")
    c.execute("CREATE TABLE tw_daily_prices(date DATE, ticker VARCHAR, close DOUBLE)")
    c.execute("INSERT INTO tw_daily_prices VALUES ('2026-08-24','2330.TW',1044.9999389648438),('2026-08-24','2317.TW',201.0)")
    c.execute("CREATE TABLE tw_monthly_revenue(code VARCHAR, ym VARCHAR, revenue BIGINT, source VARCHAR, fetched_at TIMESTAMP)")
    c.execute("INSERT INTO tw_monthly_revenue VALUES ('2330','202607',100,'MOPS_OFFICIAL','2026-08-10 09:00'),"
              "('2330','202607',90,'CNYES','2026-08-09 09:00'),('2330','202607',100,'CNYES','2026-08-11 09:00')")
    c.close()
    x = root / "xsrc"
    o = "vdf_tw_market.duckdb:"
    files = {
        "tw_daily_close/tw_daily_close__TWSE.csv": [_HDR_SRC, ["tw_daily_close", "TWSE", "2317", "2026-08-24", "close", "200.0", "1150824", o + "tw_trading_daily"],
                                                   ["tw_daily_close", "TWSE", "2330", "2026-08-24", "close", "1045.0", "1150824", o + "tw_trading_daily"]],
        "tw_daily_close/tw_daily_close__YAHOO.csv": [_HDR_SRC, ["tw_daily_close", "YAHOO", "2317", "2026-08-24", "close", "201.0", "2026-08-24", o + "tw_daily_prices"],
                                                    ["tw_daily_close", "YAHOO", "2330", "2026-08-24", "close", "1044.9999389648438", "2026-08-24", o + "tw_daily_prices"]],
        "tw_daily_close/tw_daily_close__對照結果.csv": [_HDR_RES,
            ["tw_daily_close", "2317", "2026-08-24", "close", "CONFLICT", "TWSE/YAHOO", "", "", json.dumps({"TWSE": 200.0, "YAHOO": 201.0})],
            ["tw_daily_close", "2330", "2026-08-24", "close", "VERIFIED", "TWSE/YAHOO", "TWSE/YAHOO", "", json.dumps({"TWSE": 1045.0, "YAHOO": 1044.9999389648438})]],
        "tw_monthly_revenue/tw_monthly_revenue__CNYES.csv": [_HDR_SRC, ["tw_monthly_revenue", "CNYES", "2330", "2026-07", "revenue", "100", "202607", o + "tw_monthly_revenue"]],
        "tw_monthly_revenue/tw_monthly_revenue__MOPS_OFFICIAL.csv": [_HDR_SRC, ["tw_monthly_revenue", "MOPS_OFFICIAL", "2330", "2026-07", "revenue", "100", "202607",
                                                                                o + "tw_monthly_revenue"]],
        "tw_monthly_revenue/tw_monthly_revenue__對照結果.csv": [_HDR_RES,
            ["tw_monthly_revenue", "2330", "2026-07", "revenue", "VERIFIED", "CNYES/MOPS_OFFICIAL", "CNYES/MOPS_OFFICIAL", "", json.dumps({"CNYES": 100, "MOPS_OFFICIAL": 100})]],
    }
    for rel, rs in files.items():
        p = x / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8-sig", newline="") as fh:
            csv.writer(fh).writerows(rs)
    summary = {"counts": {"VERIFIED": 2, "CONFLICT": 1, "SINGLE": 0}, "comparable": 3,
               "datasets": {"tw_daily_close": {"VERIFIED": 1, "CONFLICT": 1, "SINGLE": 0}, "tw_monthly_revenue": {"VERIFIED": 1, "CONFLICT": 0, "SINGLE": 0}}}
    datefmt = {"items": [{"db": db.name, "table": "tw_trading_daily", "column": "date", "type": "VARCHAR", "standard": False, "nonstd": 1},
                         {"db": db.name, "table": "tw_daily_prices", "column": "date", "type": "DATE", "standard": True, "nonstd": 0},
                         {"db": db.name, "table": "tw_monthly_revenue", "column": "ym", "type": "VARCHAR", "standard": False, "nonstd": 1}]}
    return x, summary, datefmt, [db]


def _edit(p: Path, fn) -> None:
    with open(p, encoding="utf-8-sig", newline="") as fh:
        rs = list(csv.reader(fh))
    rs = fn(rs)
    with open(p, "w", encoding="utf-8-sig", newline="") as fh:
        csv.writer(fh).writerows(rs)


def selftest() -> int:
    import shutil
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note != "" else ""), flush=True)
    print("=== %s · 自測(自己造庫 · 手寫中間檔與結果 · 不借用 ActivateVDF 的程式;零網路)===" % TAG, flush=True)
    cases = [("1150824", "2026-08-24"), ("2026-08-24 00:00:00", "2026-08-24"), ("202607", "2026-07"), ("11507", "2026-07"), ("113/10/01", "2024-10-01"),
             ("114年09月12日", "2025-09-12"), ("2024年10月", "2024-10"), ("2024Q3", "2024-09"), ("20241001", "2024-10-01"), ("2024", "2024"), ("2024-02-30", None)]
    chk("① 獨立日期重算(逐種格式 strptime + 明列民國)· 標準判斷(YYYY / YYYY-MM / YYYY-MM-DD 且是真日期)",
        all(indep_iso(a) == b for a, b in cases) and is_standard("2026-08-24") and is_standard("2026-07") and is_standard("2026")
        and not is_standard("2026-02-30") and not is_standard("1150824") and not is_standard("202607"), [(a, indep_iso(a), b) for a, b in cases if indep_iso(a) != b])
    chk("② 獨立判定(Decimal):價格到 0.01(1044.99994 = 1045.0 · 200 ≠ 201)· 營收整數 · 三個來源兩個相同 = 成功 + 離群 · 都不同 = 衝突 · 一個 = 單一",
        judge({"TWSE": "1045.0", "YAHOO": "1044.9999389648438"}, "close")[0] == "VERIFIED" and judge({"TWSE": "200.0", "YAHOO": "201.0"}, "close")[0] == "CONFLICT"
        and judge({"A": "10.3", "B": "10.35"}, "close")[0] == "CONFLICT" and judge({"A": "100", "B": "100.0", "C": "90"}, "revenue") == ("VERIFIED", ["A", "B"], ["C"])
        and judge({"A": "1"}, "close")[0] == "SINGLE")
    try:
        import duckdb  # noqa: F401
        have = True
    except ImportError:
        have = False
    if not have:
        chk("③ duckdb 不在本境 → 回資料庫核對不驗(不代裝)", True)
    else:
        with tempfile.TemporaryDirectory(prefix="xsrcverify_") as td:
            base = Path(td) / "base"
            x, summ, dfm, dbs = _fixture(base)
            rep = verify(x, summ, dbs, dfm)
            chk("③ 正確的中間檔 + 結果 → PASS(六項全過 · 回原表逐筆一字不差 · 同來源多次抓取取最新)", rep["verdict"] == "PASS",
                {k: v["bad"] for k, v in rep["checks"].items()})
            fp = rep["fingerprint"]
            muts = {
                "中間檔的值被改(1045.0 → 1046.0)": ("tw_daily_close/tw_daily_close__TWSE.csv", lambda rs: [r if r[2] != "2330" else r[:5] + ["1046.0"] + r[6:] for r in rs], None),
                "中間檔的日期被改(2026-08-24 → 2026-08-25)": ("tw_daily_close/tw_daily_close__YAHOO.csv", lambda rs: [r if r[2] != "2317" else r[:3] + ["2026-08-25"] + r[4:] for r in rs], None),
                "判定翻轉(VERIFIED → CONFLICT)": ("tw_daily_close/tw_daily_close__對照結果.csv", lambda rs: [r if r[1] != "2330" else r[:4] + ["CONFLICT", r[5], "", "", r[8]] for r in rs], None),
                "來源標錯(YAHOO 的列寫成 TWSE)": ("tw_daily_close/tw_daily_close__YAHOO.csv", lambda rs: [r if r[2] != "2330" else [r[0], "TWSE"] + r[2:] for r in rs], None),
                "結果少一列": ("tw_daily_close/tw_daily_close__對照結果.csv", lambda rs: [r for r in rs if r[1] != "2317"], None),
                "拿到舊的那次抓取(CNYES 100 → 90)": ("tw_monthly_revenue/tw_monthly_revenue__CNYES.csv", lambda rs: [r if r[2] != "2330" else r[:5] + ["90"] + r[6:] for r in rs], None),
                "總覽計數不符(成功 +1)": (None, None, {"counts": {"VERIFIED": 3, "CONFLICT": 1, "SINGLE": 0}}),
                "日期體檢筆數不符(不標準 1 → 0)": (None, None, "datefmt"),
            }
            caught = {}
            for name, (rel, fn, alt) in muts.items():
                mdir = Path(td) / ("m%d" % len(caught))
                shutil.copytree(x, mdir)
                s2, d2 = dict(summ), {"items": [dict(i) for i in dfm["items"]]}
                if rel:
                    _edit(mdir / rel, fn)
                elif alt == "datefmt":
                    d2["items"][0]["nonstd"] = 0
                else:
                    s2.update(alt)
                r2 = verify(mdir, s2, dbs, d2)
                caught[name] = (r2["verdict"], [k.split(" ")[0] for k, v in r2["checks"].items() if v["bad"]])
            missed = [k for k, v in caught.items() if v[0] != "FAIL"]
            chk("④ 反向測試 %d 種錯 → 全部 FAIL(漏抓 0)" % len(muts), not missed, {k: v[1] for k, v in caught.items()} if not missed else missed)
            rows = result_rows(x)
            chk("⑤ 結果指紋:列的順序不影響 · 改一個字就變", fingerprint(list(reversed(rows))) == fp
                and fingerprint([dict(rows[0], status="SINGLE")] + rows[1:]) != fp, fp[:16])
    src = Path(__file__).read_text(encoding="utf-8")
    imports = re.findall(r"^\s*(?:import|from)\s+([A-Za-z_][\w.]*)", src, re.M)
    chk("⑥ 獨立:不匯入 ActivateVDF / 他系統程式;加速器橋 · 網路橋在;不碰 TA-Lib;同意閘不寫;資料庫只唯讀附掛",
        not [m for m in imports if m.startswith(("VDF_MDL013", "ActivateVDF", "CGC_", "VRN_", "VCGC"))] and "VIA:ACCEL-BRIDGE" in src and "VIA:NET-BRIDGE" in src
        and not re.search(r"^\s*(import|from)\s+" + "talib", src, re.M) and not re.search(r"\[[\"']VIA_(NET|SCRAPE)_" + r"CONSENT[\"']\]\s*=(?!=)", src)
        and "(READ_ONLY)" in src)
    n = sum(ok)
    print("  [計] %s 自測 %d/%d · %s" % (TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    return 0 if n == len(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
