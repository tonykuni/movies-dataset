#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF_MDL020_DataPlane v0104 — 薄尾(v0100–v0103 一字不動):parquet align —— 資料家 parquet 對齊輸出 DataFrame

操作員 2026-11-24:「via_database\vdf_database 對齊 PARQUET 與輸出 DATAFRAME」(同一則:「2018起」)。
讀碼確認的缺口:
  · 輸出 DataFrame 的正本 = DataPlane 冊尾版 outputs(22 個:檔名 · 庫 · 表 · 鍵 · 寫入引擎);每個 DataFrame 的欄位 = 正典 DuckDB 那張表。
  · v0100 parquet status 只比 列 · 鍵 · 重複 · 日期;不比欄位。
  · v0100 / v0101 parquet sync 在既有 parquet 上用 UNION ALL BY NAME 補新鍵:來源新加的欄接在最後(欄序跟 DataFrame 不同)、
    型別照舊 parquet、來源已刪的欄留在 parquet → parquet 會慢慢跟輸出 DataFrame 對不上,而且沒有任何檢查會亮。
    冊外多出來的 parquet 也沒人點名。
本版加 parquet align(其餘動詞照前版):
  parquet align             唯讀:冊上 22 個輸出 ∪ 資料家實有的 tw__ / gl__ parquet,逐檔:
                              冊上有、parquet 沒有(還沒有 → parquet sync 會建)· parquet 有、冊上沒有(冊外 · 只點名不刪)·
                              欄位對 DataFrame:缺欄 · 多欄(有沒有資料)· 型別不同 · 欄序不同 · 鍵欄在不在 · 起始日前的列(--start,預設冊上 2018-01-01)。
  parquet align --apply     要 VDF 入口旗標(VIA_FROM_VDFSM=YES)或 VCGC:只重寫「欄位對不上」的檔 ——
                              欄序與型別照 DataFrame(TRY_CAST;有任何一列轉不過 = 這檔不動)· 缺的欄補 NULL ·
                              parquet 才有、全是 NULL 的欄拿掉 · parquet 才有、有資料的欄保留在最後(不丟資料,照實點名)·
                              暫存檔驗 列數相同 · 重複鍵不增 → 原子替換;不刪列、不刪檔、不碰正典庫(唯讀開)。
資料不離開本機;本檔零網路 · 不碰 TA-Lib · 不讀寫同意閘。
用法:VDF_SystemManager parquet align [--apply] [--home <資料家>] [--pq-dir <夾>] [--start YYYY-MM-DD] [--only a,b] [--json]
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

import importlib.util
import json
import re
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAMILY = "VDF_MDL020_DataPlane"
TAG = "VDF_MDL020_DataPlane v0104"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0104", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
P = PRIOR.P                                               # v0100:資料家 · 正典庫 · 鍵律 · 原子替換
V1 = PRIOR.V1                                             # v0101:一本冊(outputs)
DEFAULT_START = "2018-01-01"                              # 操作員 2026-11-22 裁定、2026-11-24 再確認「2018 起」;冊上有值照冊


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def book_outputs() -> list:
    return list((V1.book() or {}).get("outputs") or [])


def book_start() -> str:
    return ((V1.book() or {}).get("params") or {}).get("fetch", {}).get("start") or DEFAULT_START


def _norm_t(t: str) -> str:
    return re.sub(r"\s+", " ", str(t or "").upper()).strip()


def schema_diff(src: list, pq: list) -> dict:
    """src / pq = [(欄, 型別)];回 缺欄 · 多欄 · 型別不同 · 欄序不同。"""
    s, q = dict(src), dict(pq)
    common = [c for c, _ in src if c in q]
    return {"missing": [c for c, _ in src if c not in q], "extra": [c for c, _ in pq if c not in s],
            "types": [(c, q[c], s[c]) for c in common if _norm_t(q[c]) != _norm_t(s[c])],
            "order": [c for c, _ in pq if c in s] != common}


def align_rows(home: Path, pq_dir: Path | None = None, start: str | None = None, only: list | None = None) -> dict:
    duckdb = P._duck()
    pq_dir = Path(pq_dir or home)
    start = start or book_start()
    outs = {o["file"]: o for o in book_outputs() if o.get("file")}
    have = {p.name for p in pq_dir.glob("*.parquet") if P.PROTO_RX.match(p.name)}
    con = duckdb.connect()
    att = P._attach(con, P.find_dbs(home))
    alias_of = {name: a for name, a in att.items() if not str(a).startswith("ERR")}
    rows = []
    for f in sorted(set(outs) | have):
        if only and not any(x in f for x in only):
            continue
        o = outs.get(f) or {}
        m = P.PROTO_RX.match(f)
        table = o.get("table") or (m.group(2) if m else None)
        db = o.get("db") or next((k for k, v in P.PROTO.items() if m and v == m.group(1)), None)
        r = {"file": f, "id": o.get("id"), "in_book": f in outs, "exists": f in have, "table": table, "db": db, "lamp": "GREEN", "notes": [],
             "diff": None, "src_cols": None, "pq_cols": None, "key": o.get("key"), "pre_start": None}
        alias = alias_of.get(Path(db).stem if db else None) or alias_of.get(db) if db else None
        try:
            src_cols = None
            if alias and table and table in P._src_tables(con, alias):
                src_cols = P._cols(con, "%s.main.%s" % (alias, P._q(table)))
            if f in have:
                rel = "read_parquet(%s)" % P._lit(pq_dir / f)
                pq_cols = P._cols(con, rel)
                r["pq_cols"] = len(pq_cols)
                names = [c for c, _ in pq_cols]
                dc = P.date_col(names)
                if dc:
                    r["pre_start"] = con.execute("SELECT COUNT(*) FROM %s WHERE TRY_CAST(%s AS DATE) < DATE %s" % (rel, P._q(dc), P._lit(start))).fetchone()[0]
                key = r["key"] or P.pick_key(names, P._declared_key(con, alias, table) if alias and src_cols else [])[0]
                r["key"] = key
                if any(k not in names for k in key or []):
                    r["lamp"] = "RED"
                    r["notes"].append("鍵欄 %s 不在 parquet" % [k for k in key if k not in names])
                if src_cols is not None:
                    r["src_cols"] = len(src_cols)
                    d = schema_diff(src_cols, pq_cols)
                    if d["extra"]:
                        d["extra_nonnull"] = {c: con.execute("SELECT COUNT(%s) FROM %s" % (P._q(c), rel)).fetchone()[0] for c in d["extra"]}
                    r["diff"] = d
                    if d["missing"] or d["extra"] or d["types"] or d["order"]:
                        r["lamp"] = P.worst([r["lamp"], "YELLOW"])
                        r["notes"].append("欄位對不上:缺 %d · 多 %d · 型別 %d · 欄序%s → parquet align --apply" % (
                            len(d["missing"]), len(d["extra"]), len(d["types"]), "不同" if d["order"] else "同"))
                elif db:
                    r["notes"].append("正典庫 %s 沒有這張表(只比存在與鍵)" % db)
                else:
                    r["notes"].append("衍生輸出(冊上沒有來源庫)· 只比存在與鍵")
            elif src_cols is not None or f in outs:
                r["lamp"] = "YELLOW"
                r["notes"].append("冊上有、parquet 還沒有 → parquet sync 會建" if src_cols is not None else "冊上有、parquet 還沒有、正典庫也沒有這張表 → 先擷取")
            if f in have and f not in outs:
                r["lamp"] = P.worst([r["lamp"], "YELLOW"])
                r["notes"].append("冊外 parquet(不在 DataPlane 冊 outputs)· 只點名不刪")
        except Exception as exc:  # noqa: BLE001 — 壞檔:照實記這一檔,不擋全表
            r["lamp"] = "RED"
            r["notes"].append("讀不了:%s: %s" % (type(exc).__name__, str(exc)[:140]))
        rows.append(r)
    con.close()
    lamps = [r["lamp"] for r in rows]
    return {"tag": TAG, "ts": P.utc_now(), "home": str(home), "pq_dir": str(pq_dir), "start": start, "book_outputs": len(outs),
            "parquet_files": len(have), "rows": rows, "lamp": P.worst(lamps) if rows else "GRAY",
            "counts": {lp: lamps.count(lp) for lp in ("GREEN", "YELLOW", "RED")}}


def apply_one(con, alias: str, table: str, dst: Path, key: list, tmp_dir: Path) -> dict:
    src = "%s.main.%s" % (alias, P._q(table))
    rel = "read_parquet(%s)" % P._lit(dst)
    scols, qcols = P._cols(con, src), P._cols(con, rel)
    q = dict(qcols)
    d = schema_diff(scols, qcols)
    sel = []
    for c, t in scols:
        if c in q:
            if _norm_t(q[c]) != _norm_t(t):
                bad = con.execute("SELECT COUNT(*) FROM %s WHERE %s IS NOT NULL AND TRY_CAST(%s AS %s) IS NULL" % (rel, P._q(c), P._q(c), t)).fetchone()[0]
                if bad:
                    return {"file": dst.name, "action": "略過", "error": "欄 %s 型別 %s → DataFrame 的 %s 轉不過 %d 列(這檔不動)" % (c, q[c], t, bad)}
                sel.append("TRY_CAST(%s AS %s) AS %s" % (P._q(c), t, P._q(c)))
            else:
                sel.append(P._q(c))
        else:
            sel.append("CAST(NULL AS %s) AS %s" % (t, P._q(c)))
    kept, dropped = [], []
    for c in d["extra"]:
        nn = con.execute("SELECT COUNT(%s) FROM %s" % (P._q(c), rel)).fetchone()[0]
        (kept if nn else dropped).append(c)
        if nn:
            sel.append(P._q(c))
    n0 = con.execute("SELECT COUNT(*) FROM %s" % rel).fetchone()[0]
    kq = ", ".join(P._q(k) for k in key if k in q) if key else ""
    d0 = con.execute("SELECT COALESCE(SUM(c - 1), 0) FROM (SELECT COUNT(*) c FROM %s GROUP BY %s HAVING COUNT(*) > 1)" % (rel, kq)).fetchone()[0] if kq else 0
    tmp = tmp_dir / (dst.name + ".vdfalign.tmp")
    tmp.unlink(missing_ok=True)
    con.execute("COPY (SELECT %s FROM %s) TO %s (FORMAT PARQUET, COMPRESSION ZSTD)" % (", ".join(sel), rel, P._lit(tmp)))
    chk = "read_parquet(%s)" % P._lit(tmp)
    n1 = con.execute("SELECT COUNT(*) FROM %s" % chk).fetchone()[0]
    d1 = con.execute("SELECT COALESCE(SUM(c - 1), 0) FROM (SELECT COUNT(*) c FROM %s GROUP BY %s HAVING COUNT(*) > 1)" % (chk, kq)).fetchone()[0] if kq else 0
    if n1 != n0 or d1 > d0:
        tmp.unlink(missing_ok=True)
        return {"file": dst.name, "action": "略過", "error": "新檔驗不過:列 %d(該 %d)· 重複鍵 %d(原 %d)→ 原檔不動" % (n1, n0, d1, d0)}
    err = P._replace(tmp, dst)
    if err:
        tmp.unlink(missing_ok=True)
        return {"file": dst.name, "action": "略過", "error": err}
    return {"file": dst.name, "action": "對齊", "rows": n1, "added_cols": d["missing"], "dropped_null_cols": dropped,
            "kept_extra_cols": kept, "retyped": [c for c, _a, _b in d["types"]], "reordered": d["order"]}


def apply(home: Path, pq_dir: Path | None = None, only: list | None = None) -> dict:
    st = align_rows(home, pq_dir, None, only)
    todo = [r for r in st["rows"] if r["exists"] and r["diff"] and (r["diff"]["missing"] or r["diff"]["extra"] or r["diff"]["types"] or r["diff"]["order"])]
    duckdb = P._duck()
    pq_dir = Path(pq_dir or home)
    con = duckdb.connect()
    att = P._attach(con, P.find_dbs(home))
    res = []
    with tempfile.TemporaryDirectory(prefix="vdf_align_", dir=str(pq_dir)) as td:
        for r in todo:
            alias = att.get(Path(r["db"]).stem) or att.get(r["db"])
            try:
                res.append(apply_one(con, alias, r["table"], pq_dir / r["file"], r["key"] or [], Path(td)))
            except Exception as exc:  # noqa: BLE001
                res.append({"file": r["file"], "action": "略過", "error": "%s: %s" % (type(exc).__name__, str(exc)[:140])})
    con.close()
    after = align_rows(home, pq_dir, None, only)
    return {"before": st, "results": res, "after": after}


def _print(st: dict, as_json: bool = False) -> None:
    if as_json:
        print(json.dumps(st, ensure_ascii=False, indent=1, default=str))
        return
    print("[%s] parquet align %s · 冊上輸出 %d · 資料家 parquet %d · 起始日 %s · 綠 %d 黃 %d 紅 %d" % (
        TAG, st["lamp"], st["book_outputs"], st["parquet_files"], st["start"], st["counts"]["GREEN"], st["counts"]["YELLOW"], st["counts"]["RED"]))
    for r in st["rows"]:
        d = r.get("diff") or {}
        extra = ""
        if d:
            extra = " · 缺 %s · 多 %s · 型別 %s%s" % (",".join(d["missing"][:4]) or "—", ",".join("%s(%d)" % (c, n) for c, n in (d.get("extra_nonnull") or {}).items())[:80] or "—",
                                                  ",".join("%s %s→%s" % x for x in d["types"][:3]) or "—", " · 欄序不同" if d["order"] else "")
        pre = " · 起始日前 %d 列" % r["pre_start"] if r.get("pre_start") else ""
        print("  %-6s %-6s %-38s 欄 %s/%s%s%s %s" % (r["lamp"], r.get("id") or "冊外", r["file"], r.get("pq_cols") or "—", r.get("src_cols") or "—",
                                                 extra, pre, ("· " + " · ".join(r["notes"])) if r["notes"] else ""))


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    if args[:2] != ["parquet", "align"]:
        return PRIOR.main(args)
    home, why = P.resolve_home(P._opt(args, "--home"))
    if home is None:
        print("[%s] GRAY · %s" % (TAG, why))
        return 2
    pq_dir = Path(P._opt(args, "--pq-dir")) if P._opt(args, "--pq-dir") else None
    only = [x for x in (P._opt(args, "--only") or "").split(",") if x] or None
    if "--apply" not in args:
        st = align_rows(home, pq_dir, P._opt(args, "--start"), only)
        _print(st, "--json" in args)
        return {"GREEN": 0, "YELLOW": 2, "GRAY": 2}.get(st["lamp"], 1)
    if not P.entry_ok():
        print("[%s] 拒絕寫入:由 VDF System Manager 總控(VIA_FROM_VDFSM=YES)或 VCGC" % TAG)
        return 2
    t0 = time.time()
    r = apply(home, pq_dir, only)
    print("[%s] parquet align --apply · %.1fs · 對齊 %d 檔 · 略過 %d" % (TAG, time.time() - t0, sum(1 for x in r["results"] if x["action"] == "對齊"),
                                                                 sum(1 for x in r["results"] if x["action"] != "對齊")))
    for x in r["results"]:
        print("  %-4s %-38s %s" % (x["action"], x["file"], x.get("error") or "列 %d · 補欄 %s · 去全空欄 %s · 保留有資料的多欄 %s · 改型別 %s%s" % (
            x["rows"], x["added_cols"] or "—", x["dropped_null_cols"] or "—", x["kept_extra_cols"] or "—", x["retyped"] or "—", " · 欄序照 DataFrame" if x["reordered"] else "")))
    _print(r["after"])
    return {"GREEN": 0, "YELLOW": 2, "GRAY": 2}.get(r["after"]["lamp"], 1)


def selftest() -> int:
    import os
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("[計] %s 自測開始(本版 6 項 · 前版 %s · 暫存資料家 · 零網路)" % (TAG, PRIOR_PATH.name), flush=True)
    chk("T1 鏈:前版 v0103 · 冊上輸出 22 個 · 冊上起始日 2018-01-01", PRIOR_PATH.name == "VDF_MDL020_DataPlane_v0103.py"
        and len(book_outputs()) == 22 and book_start() == "2018-01-01", (len(book_outputs()), book_start()))
    duckdb = P._duck()
    with tempfile.TemporaryDirectory(prefix="dp104_") as td:
        home = Path(td)
        db = home / "vdf_tw_market.duckdb"
        c = duckdb.connect(str(db))
        c.execute("CREATE TABLE tw_daily_prices(date DATE, ticker VARCHAR, close DOUBLE, volume BIGINT, adj DOUBLE)")
        c.execute("INSERT INTO tw_daily_prices VALUES ('2017-12-29','2330',100.5,10,NULL),('2018-01-02','2330',101,11,NULL),('2018-01-02','2317',90,12,NULL)")
        c.close()
        c = duckdb.connect()
        # 舊 parquet:欄序不同 · close 是字串 · 少 adj · 多一個全空欄與一個有資料的欄
        c.execute("COPY (SELECT ticker, date, CAST(close AS VARCHAR) AS close, CAST(volume AS BIGINT) AS volume, CAST(NULL AS VARCHAR) AS junk, 'x' AS legacy "
                  "FROM (VALUES ('2017-12-29'::DATE,'2330',100.5,10),('2018-01-02'::DATE,'2330',101.0,11),('2018-01-02'::DATE,'2317',90.0,12)) t(date,ticker,close,volume)) "
                  "TO %s (FORMAT PARQUET)" % P._lit(home / "tw__tw_daily_prices.parquet"))
        c.execute("COPY (SELECT 1 AS a) TO %s (FORMAT PARQUET)" % P._lit(home / "tw__stray_table.parquet"))
        c.close()
        st = align_rows(home, start="2018-01-01")
        by = {r["file"]: r for r in st["rows"]}
        p = by["tw__tw_daily_prices.parquet"]
        d = p["diff"] or {}
        chk("T2 唯讀檢:缺 adj · 多 junk(0)/ legacy(3)· close 型別不同 · 欄序不同 · 起始日前 1 列 · 黃",
            d.get("missing") == ["adj"] and d.get("extra_nonnull") == {"junk": 0, "legacy": 3} and [x[0] for x in d.get("types", [])] == ["close"]
            and d.get("order") is True and p["pre_start"] == 1 and p["lamp"] == "YELLOW", p)
        chk("T3 冊外 parquet 點名(不刪)· 冊上有但還沒有 parquet 的照列 · 衍生輸出只比存在",
            by["tw__stray_table.parquet"]["in_book"] is False and "冊外" in " ".join(by["tw__stray_table.parquet"]["notes"])
            and by["tw__tw_listings.parquet"]["exists"] is False and st["book_outputs"] == 22, [(k, v["notes"]) for k, v in list(by.items())[:3]])
        keep = os.environ.get("VIA_FROM_VDFSM")
        os.environ["VIA_FROM_VDFSM"] = "YES"                # 入口旗標(不是同意閘):自測在暫存資料家寫
        try:
            r = apply(home, only=["tw__tw_daily_prices"])
        finally:
            os.environ.pop("VIA_FROM_VDFSM", None) if keep is None else os.environ.__setitem__("VIA_FROM_VDFSM", keep)
        x = r["results"][0] if r["results"] else {}
        c = duckdb.connect()
        cols = c.execute("DESCRIBE SELECT * FROM read_parquet(%s)" % P._lit(home / "tw__tw_daily_prices.parquet")).fetchall()
        vals = c.execute("SELECT close, legacy FROM read_parquet(%s) ORDER BY date, ticker" % P._lit(home / "tw__tw_daily_prices.parquet")).fetchall()
        c.close()
        chk("T4 --apply:欄序與型別照 DataFrame · 補 adj · 去全空 junk · 有資料的 legacy 留在最後 · 列數不變 · 值沒變",
            x.get("action") == "對齊" and [cc[0] for cc in cols] == ["date", "ticker", "close", "volume", "adj", "legacy"]
            and cols[2][1] == "DOUBLE" and x["rows"] == 3 and vals[0] == (100.5, "x") and x["dropped_null_cols"] == ["junk"], (x, cols, vals))
        after = {rr["file"]: rr for rr in r["after"]["rows"]}["tw__tw_daily_prices.parquet"]
        chk("T5 對齊後再檢:只剩保留的 legacy(有資料不刪)· 型別 / 欄序 / 缺欄都清掉 · 正典庫沒被改",
            after["diff"]["missing"] == [] and after["diff"]["types"] == [] and after["diff"]["order"] is False and after["diff"]["extra"] == ["legacy"]
            and duckdb.connect(str(db), read_only=True).execute("SELECT COUNT(*) FROM tw_daily_prices").fetchone()[0] == 3, after["diff"])
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T6 檔面:加速器橋 · 零 TA-Lib · 不出網 · 不設同意閘",
        "[VIA:ACCEL-BRIDGE:v0100]" in src and not re.search(r"^\s*(import|from)\s+(talib|requests|urllib)", src, re.M)
        and not re.search(r"os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", src))
    n = sum(ok)
    print("[計] %s 自測 %d/%d · %s" % (TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    print("[前版] %s 自測(子行程)" % PRIOR_PATH.name, flush=True)
    import subprocess
    cp = subprocess.run([sys.executable, str(PRIOR_PATH), "--selftest"], capture_output=True, text=True, encoding="utf-8", errors="replace",
                        timeout=1800, stdin=subprocess.DEVNULL)
    out = cp.stdout + cp.stderr
    fails = [ln.strip() for ln in out.splitlines() if "[FAIL]" in ln]
    stale = [ln for ln in fails if any(sig in ln for sig in STALE_SIGS)]
    other = [ln for ln in fails if ln not in stale]
    for ln in fails:
        print("   %s %s" % ("[已知 · 前版釘舊冊]" if ln in stale else "[前版紅]", ln[:220]), flush=True)
    rc_prior = 0 if cp.returncode == 0 or (fails and not other) else cp.returncode
    print("[計] %s 自測 OK %d · FAIL %d · 前版 rc=%s(前版紅 %d 行 · 其中釘舊冊 %d 行)" % (TAG, n, len(ok) - n, rc_prior, len(fails), len(stale)), flush=True)
    return 0 if n == len(ok) and rc_prior == 0 else 1


# 前版 v0101 自測寫死「冊 = v0101」:輸出 21 個、起日 2022-01-01、2022-01 起 59 個月。冊尾版已是 v0104(22 個輸出 · 2018-01-01,
# 操作員 2026-11-22 / 11-24 裁定)→ 這幾行在現在的冊上必紅,而且 v0103 的「前版自測照過」兩檢跟著紅。只認這幾個字樣,其他紅照紅。
STALE_SIGS = ("輸出 21 個 DataFrame", "擷取起日 2022-01-01", "2022-01 ~ ", "v0101 自測照過(VDF_MDL020_DataPlane v0101 自測 9/11",
              "前版 0101 自測在隔離下照過(VDF_MDL020_DataPlane v0101 自測 9/11")


if __name__ == "__main__":
    sys.exit(main())
