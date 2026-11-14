#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_OutputStore v0103 — v0102 薄尾(v0102 / v0101 / v0100 留著一字不改):增量庫實體加 SOURCE 與 BROKER_EN 兩欄 · 不重複追加。

操作員 2026-11-03:「輸出冊和增量庫也實體加 Source 欄」「BROKER 一律用英文縮寫」。
VRN2_BookSource v0100 把兩欄寫進輸出冊後,v0102 的列內容雜湊會把每一列都當成「內容變了」再追加一次(庫倍增)。本版:
  ① 列內容雜湊不算 SOURCE / BROKER_EN(它們由其他欄位推得)→ 已在庫裡的列不再追加;新列照舊追加(帶兩欄)。
     MarketConsensus 的 SOURCE 是原文來源欄(不是推得的)→ 照 v0102 算進雜湊,不受影響。
  ② 補欄(sync 後自動做 · 也可單獨 fill-source [--apply]):報告冊(BookSource 那七本)裡 SOURCE 是空的舊列,
     用 BookSource 同一套規則從該列自己的欄位算出兩欄填上。DuckDB:先整個庫檔複製到 <輸出夾>/VRN2/_source_fill_<時間>/(SHA-256)
     → 欄位不在就 ALTER TABLE 加 → 依 (BROKER, PERIOD, REPORT_DATE, VALUE_SOURCE) 對照表一次 UPDATE → 受影響的 parquet/<冊>/run=<id>.parquet
     搬進備份夾、從庫重寫回原處;pyarrow 備援:受影響的分檔先搬進備份夾再寫回帶兩欄的版本。FILL_MANIFEST.json 記逐冊列數、備份雜湊、怎麼還原。
     再跑 = 0 列(不再備份)。restore-fill --folder <夾> 換回補欄前(現在的先搬到 restore_replaced/ · 不刪)。
  ③ 收據 VRN2_OutputStore_latest.json 多 derived_fill{lamp, why, filled{冊: 列數}, partitions, folder}。補欄失敗只黃 · 不擋 ⑬。
動詞:sync [--v2] [--output-dir] [--run-id] · fill-source [--v2] [--output-dir] [--apply] · restore-fill --folder <夾> · purge-mops / restore-purge(同 v0102)· --selftest
"""
from __future__ import annotations

import datetime
import importlib.util
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

TAG = "v0103"
DISPLAY_NAME = "VRN2_OutputStore"
PRIOR_NAME = "VRN2_OutputStore_v0102.py"
HERE = Path(__file__).resolve().parent
DERIVED = ("BROKER_EN", "SOURCE")
REPORT_BOOKS = ("BasicInfo", "FinancialData", "Summary", "Combined", "Rejected", "FinancialAligned", "Deleted")
KEYS = ("BROKER", "PERIOD", "REPORT_DATE", "VALUE_SOURCE")
FILL_PREFIX = "_source_fill_"
FILL_MANIFEST = "FILL_MANIFEST.json"


def _load(name: str, alias: str):
    path = HERE / name
    if not path.is_file():
        raise FileNotFoundError("前版 %s 不在 %s" % (name, HERE))
    spec = importlib.util.spec_from_file_location(alias, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PRIOR = _load(PRIOR_NAME, "vrn2_outputstore_prior_v0102")       # v0102(它再載 v0101 → v0100)
V0101 = PRIOR.PRIOR
V0100 = PRIOR.V0100
for _name in dir(PRIOR):
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = getattr(PRIOR, _name)
V0100.TAG = V0101.TAG = PRIOR.TAG = TAG + "(v0102 / v0101 / v0100 薄尾)"
_v0101_take = V0101._take
_v0102_sync = PRIOR.sync


# ── ① 雜湊不算推得欄 ──────────────────────────────────────────────────────────────────────────────────
def row_hash103(flat: dict) -> str:
    return V0101.row_hash({k: v for k, v in flat.items() if k not in DERIVED})


def _take(rows: list, shas: dict, have: set, run_id: str) -> list:
    """同 v0101 _take,只差列內容雜湊不算 SOURCE / BROKER_EN(報告冊專用 · MarketConsensus 走 v0102 自己的路)。"""
    out, seen = [], set()
    for r in rows:
        sha = shas.get(r.get("FILENAME", ""), "")
        if not sha:
            continue
        flat = V0100._flat(r)
        key = (sha, row_hash103(flat))
        if key in have or key in seen:
            continue
        seen.add(key)
        out.append(dict(flat, run_id=run_id, file_sha=sha, row_sha=key[1]))
    return out


V0101._take = _take


# ── ② 補欄 ────────────────────────────────────────────────────────────────────────────────────────────
def _booksource():
    """同夾最高版 VRN2_BookSource_v*.py(規則的正本);沒有 → None。"""
    cands = sorted(HERE.glob("VRN2_BookSource_v[0-9][0-9][0-9][0-9].py"))
    if not cands:
        return None
    return _load(cands[-1].name, "vrn2_booksource_for_store_" + cands[-1].stem[-5:])


def _s(v) -> str:
    return "" if v is None else str(v)


def _new_folder(base: Path) -> Path:
    name, n = FILL_PREFIX + datetime.datetime.now().strftime("%Y%m%d_%H%M%S"), 1
    target = base / name
    while target.exists():
        n += 1
        target = base / ("%s_%d" % (name, n))
    target.mkdir(parents=True)
    return target


def _q(c: str) -> str:
    return '"%s"' % c.replace('"', '""')


def _fill_duckdb(duckdb, db: Path, pq_dir: Path, base: Path, bs, apply: bool) -> dict:
    todo = {}
    con = duckdb.connect(str(db), read_only=True)
    try:
        for book in REPORT_BOOKS:
            tbl = "book_" + book.lower()
            if not con.execute("SELECT count(*) FROM information_schema.tables WHERE table_name=?", [tbl]).fetchone()[0]:
                continue
            have = {r[0] for r in con.execute("SELECT column_name FROM information_schema.columns WHERE table_name=?", [tbl]).fetchall()}
            keys = [k for k in KEYS if k in have]
            cond = '"SOURCE" IS NULL OR "SOURCE" = \'\'' if "SOURCE" in have else "TRUE"
            sel = ", ".join(["COALESCE(%s, '')" % _q(k) for k in keys] + ["count(*)"]) if keys else "count(*)"
            grp = (" GROUP BY " + ", ".join(str(i + 1) for i in range(len(keys)))) if keys else ""
            combos = con.execute("SELECT %s FROM %s WHERE %s%s" % (sel, tbl, cond, grp)).fetchall()
            n = sum(int(c[-1]) for c in combos)
            if not n:
                continue
            runs = [r[0] for r in con.execute("SELECT DISTINCT run_id FROM %s WHERE %s" % (tbl, cond)).fetchall()]
            todo[book] = {"tbl": tbl, "have": have, "keys": keys, "cond": cond, "n": n, "runs": sorted(_s(r) for r in runs),
                          "map": [list(c[:-1]) + list(bs.derive(book, dict(zip(keys, c[:-1])))) for c in combos]}
    finally:
        con.close()
    filled = {b: t["n"] for b, t in todo.items()}
    total = sum(filled.values())
    if not total:
        return {"lamp": "GREEN", "why": "增量庫的報告冊都已帶 SOURCE / BROKER_EN", "filled": {}, "partitions": 0}
    if not apply:
        return {"lamp": "YELLOW", "why": "增量庫有 %d 列還沒有 SOURCE / BROKER_EN(只算沒動 · --apply 才補 · 先備份)" % total, "filled": filled, "partitions": 0}
    folder = _new_folder(base)
    backup = folder / "vrn2_store.duckdb.bak"
    shutil.copy2(str(db), str(backup))
    wal = db.with_name(db.name + ".wal")
    if wal.is_file():
        shutil.copy2(str(wal), str(folder / (wal.name + ".bak")))
    moved, rewritten = [], []
    con = duckdb.connect(str(db))
    try:
        for book, t in todo.items():
            tbl, keys = t["tbl"], t["keys"]
            for c in DERIVED:
                if c not in t["have"]:
                    con.execute("ALTER TABLE %s ADD COLUMN %s VARCHAR" % (tbl, _q(c)))
            cols = ["k%d" % i for i in range(len(keys))]
            con.execute("CREATE OR REPLACE TEMP TABLE _fill(%s)" % ", ".join(["%s VARCHAR" % c for c in cols] + ["br VARCHAR", "src VARCHAR"]))
            con.executemany("INSERT INTO _fill VALUES (%s)" % ", ".join("?" * (len(keys) + 2)), t["map"])
            on = " AND ".join("COALESCE(%s.%s, '') = _fill.%s" % (tbl, _q(k), cols[i]) for i, k in enumerate(keys)) or "TRUE"
            con.execute('UPDATE %s SET "BROKER_EN" = _fill.br, "SOURCE" = _fill.src FROM _fill WHERE %s AND (%s."SOURCE" IS NULL OR %s."SOURCE" = \'\')' % (tbl, on, tbl, tbl))
            for rid in t["runs"]:
                src = pq_dir / book / ("run=%s.parquet" % rid)
                if not src.is_file():
                    continue
                dest = folder / "parquet" / book / src.name
                dest.parent.mkdir(parents=True, exist_ok=True)
                src.replace(dest)
                moved.append("%s/%s" % (book, src.name))
                con.execute("COPY (SELECT * FROM %s WHERE run_id=?) TO '%s' (FORMAT PARQUET)" % (tbl, str(src).replace("'", "''")), [rid])
                rewritten.append("%s/%s" % (book, src.name))
        con.execute("CHECKPOINT")
        left = {b: con.execute('SELECT count(*) FROM %s WHERE "SOURCE" IS NULL OR "SOURCE" = \'\'' % t["tbl"]).fetchone()[0] for b, t in todo.items()}
    finally:
        con.close()
    man = {"engine": "%s %s" % (DISPLAY_NAME, TAG), "at": V0100.now(), "store_engine": "duckdb", "store": str(db), "filled": filled, "left_empty": left,
           "backup": backup.name, "backup_sha256": V0100.sha256_file(backup), "moved_parquet": moved, "rewritten_parquet": rewritten,
           "rule": "SOURCE / BROKER_EN 由 %s 從該列自己的 %s 算出" % (getattr(bs, "DISPLAY_NAME", "VRN2_BookSource") + " " + getattr(bs, "VERSION", ""), " / ".join(KEYS)),
           "restore": "VRN2_OutputStore_v0103.py restore-fill --folder \"%s\"" % folder}
    (folder / FILL_MANIFEST).write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    lamp = "GREEN" if not any(left.values()) else "YELLOW"
    return {"lamp": lamp, "why": "補欄 %s 列(分檔重寫 %d · 備份 %s · 可 restore-fill)" % (json.dumps(filled, ensure_ascii=False), len(rewritten), folder.name),
            "filled": filled, "partitions": len(rewritten), "folder": str(folder), "left_empty": left}


def _fill_pyarrow(pq_dir: Path, base: Path, bs, apply: bool) -> dict:
    import pyarrow as pa  # noqa: WPS433
    import pyarrow.parquet as pq  # noqa: WPS433
    plan = []
    for book in REPORT_BOOKS:
        for f in sorted((pq_dir / book).glob("run=*.parquet")) if (pq_dir / book).is_dir() else []:
            rows = pq.read_table(str(f)).to_pylist()
            idx = [i for i, r in enumerate(rows) if not _s(r.get("SOURCE"))]
            if idx:
                plan.append((book, f, rows, idx))
    filled = {}
    for book, _f, _r, idx in plan:
        filled[book] = filled.get(book, 0) + len(idx)
    total = sum(filled.values())
    if not total:
        return {"lamp": "GREEN", "why": "增量庫(pyarrow)的報告冊都已帶 SOURCE / BROKER_EN", "filled": {}, "partitions": 0}
    if not apply:
        return {"lamp": "YELLOW", "why": "增量庫(pyarrow)有 %d 列還沒有 SOURCE / BROKER_EN(只算沒動 · --apply 才補)" % total, "filled": filled, "partitions": 0}
    folder = _new_folder(base)
    moved = []
    for book, f, rows, idx in plan:
        dest = folder / "parquet" / book / f.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(f), str(dest))
        moved.append("%s/%s" % (book, f.name))
        for i in idx:
            rows[i]["BROKER_EN"], rows[i]["SOURCE"] = bs.derive(book, {k: _s(rows[i].get(k)) for k in KEYS})
        cols = list(dict.fromkeys(k for r in rows for k in r if k not in DERIVED)) + list(DERIVED)
        tmp = f.with_name(f.name + ".tmp")
        pq.write_table(pa.table({c: [_s(r.get(c)) for r in rows] for c in cols}), str(tmp))
        os.replace(str(tmp), str(f))
    man = {"engine": "%s %s" % (DISPLAY_NAME, TAG), "at": V0100.now(), "store_engine": "pyarrow", "store": str(pq_dir), "filled": filled, "moved_parquet": moved,
           "restore": "VRN2_OutputStore_v0103.py restore-fill --folder \"%s\"" % folder}
    (folder / FILL_MANIFEST).write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"lamp": "GREEN", "why": "補欄 %s 列(分檔重寫 %d · 原分檔在 %s · 可 restore-fill)" % (json.dumps(filled, ensure_ascii=False), len(moved), folder.name),
            "filled": filled, "partitions": len(moved), "folder": str(folder)}


def fill_source(v2: Path, output_dir=None, apply: bool = True) -> dict:
    """② 舊列補 SOURCE / BROKER_EN(apply=False 只算)。回結果 dict(不另寫收據 · sync 併進 VRN2_OutputStore_latest.json)。"""
    base = PRIOR._base(Path(v2), output_dir)
    if not base:
        return {"lamp": "GRAY", "why": "未設定輸出位置 · 沒有增量庫", "filled": {}, "partitions": 0}
    try:
        bs = _booksource()
    except Exception as error:  # noqa: BLE001
        return {"lamp": "YELLOW", "why": "BookSource 載不起來(%s)· 不補欄" % type(error).__name__, "filled": {}, "partitions": 0}
    if bs is None:
        return {"lamp": "GRAY", "why": "同夾沒有 VRN2_BookSource_v*.py · 不補欄", "filled": {}, "partitions": 0}
    eng, duckdb = V0100._engine()
    db, pq_dir = base / "vrn2_store.duckdb", base / "parquet"
    try:
        if eng == "duckdb" and db.is_file():
            return _fill_duckdb(duckdb, db, pq_dir, base, bs, apply)
        if pq_dir.is_dir() and eng in ("duckdb", "pyarrow") and not db.is_file():
            return _fill_pyarrow(pq_dir, base, bs, apply)
        if db.is_file():
            return {"lamp": "YELLOW", "why": "庫是 DuckDB 但這個 Python 沒有 duckdb · 補不了(交 VCGC 裝 duckdb)", "filled": {}, "partitions": 0}
        return {"lamp": "GRAY", "why": "還沒有增量庫(%s)" % base, "filled": {}, "partitions": 0}
    except Exception as error:  # noqa: BLE001
        return {"lamp": "YELLOW", "why": "補欄失敗:%s: %s(庫備份在 %s* 夾 · 可 restore-fill)" % (type(error).__name__, str(error)[:200], FILL_PREFIX), "filled": {}, "partitions": 0}


def restore_fill(v2: Path, folder, output_dir=None) -> dict:
    folder = Path(folder)
    try:
        man = json.loads((folder / FILL_MANIFEST).read_text(encoding="utf-8"))
    except Exception as error:  # noqa: BLE001
        return {"lamp": "RED", "why": "讀不到 %s 的 %s(%s)" % (folder, FILL_MANIFEST, type(error).__name__)}
    base = folder.parent
    pq_dir, repl = base / "parquet", folder / "restore_replaced" / datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    restored = []
    if man.get("store_engine") == "duckdb":
        db, backup = base / "vrn2_store.duckdb", folder / man.get("backup", "vrn2_store.duckdb.bak")
        if not backup.is_file() or V0100.sha256_file(backup) != man.get("backup_sha256"):
            return {"lamp": "RED", "why": "備份 %s 不在或雜湊對不上 · 不還原" % backup.name}
        repl.mkdir(parents=True, exist_ok=True)
        if db.is_file():
            db.replace(repl / db.name)
        wal = db.with_name(db.name + ".wal")
        if wal.is_file():
            wal.replace(repl / wal.name)
        shutil.copy2(str(backup), str(db))
        if (folder / (wal.name + ".bak")).is_file():
            shutil.copy2(str(folder / (wal.name + ".bak")), str(wal))
        restored.append(db.name)
    for rel in man.get("moved_parquet") or []:
        src, dst = folder / "parquet" / rel, pq_dir / rel
        if not src.is_file():
            continue
        if dst.is_file():
            (repl / "parquet" / Path(rel).parent).mkdir(parents=True, exist_ok=True)
            dst.replace(repl / "parquet" / rel)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src), str(dst))
        restored.append(rel)
    man["restored_at"] = V0100.now()
    (folder / FILL_MANIFEST).write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"lamp": "GREEN", "why": "已還原 %d 個檔(現在的搬到 %s)" % (len(restored), repl), "restored": restored}


# ── sync = v0102 的 sync(清 MOPS · 追加:雜湊不算推得欄)→ 補欄 ──────────────────────────────────────────────
def sync(v2: Path, output_dir: Path | None = None, run_id: str | None = None) -> dict:
    rec = _v0102_sync(v2, output_dir, run_id)
    if rec.get("lamp") in ("GREEN", "YELLOW") and rec.get("store_engine") in ("duckdb", "pyarrow"):
        fill = fill_source(v2, output_dir, apply=True)
        rec["derived_fill"] = fill
        if fill.get("filled"):
            rec["why"] = ("%s · " % rec["why"] if rec.get("why") else "") + "SOURCE / BROKER_EN:" + str(fill.get("why", ""))
        if fill.get("lamp") in ("YELLOW", "RED") and rec.get("lamp") == "GREEN":
            rec["lamp"] = "YELLOW"
        if rec.get("store_engine") == "duckdb" or (rec.get("output_dir") and Path(rec["output_dir"]).is_dir()):
            base = Path(rec["output_dir"]) / "VRN2" / "parquet"
            if base.is_dir():
                rec["parquet_files"] = sorted(p.relative_to(base).as_posix() for p in base.rglob("*.parquet"))
        V0100._write_receipt(Path(v2), rec)
    return rec


V0100.sync = V0101.sync = PRIOR.sync = sync
read_config = V0100.read_config
write_config = V0100.write_config


# ── 自測 ──────────────────────────────────────────────────────────────────────────────────────────────
def _books(v2: Path, with_cols: bool, extra: bool = False) -> None:
    fin = [{"REPORT_DATE": "2026-05-20", "FILENAME": "a.pdf", "TICKER": "1560", "BROKER": "Macquarie", "ITEM": "EPS", "PERIOD": "2026E", "VALUE": "5.1"},
           {"REPORT_DATE": "2026-05-20", "FILENAME": "a.pdf", "TICKER": "1560", "BROKER": "Macquarie", "ITEM": "EPS", "PERIOD": "2025", "VALUE": "4.0"},
           {"REPORT_DATE": "2026-10-01", "FILENAME": "b.pdf", "TICKER": "2330", "BROKER": "中信", "ITEM": "EPS", "PERIOD": "2027F", "VALUE": "70"}]
    if extra:
        fin.append({"REPORT_DATE": "2026-10-01", "FILENAME": "b.pdf", "TICKER": "2330", "BROKER": "中信", "ITEM": "Revenue", "PERIOD": "2027F", "VALUE": "9,999"})
    basic = [{"REPORT_DATE": "2026-05-20", "FILENAME": "a.pdf", "TICKER": "1560", "BROKER": "Macquarie"}, {"REPORT_DATE": "2026-10-01", "FILENAME": "b.pdf", "TICKER": "2330", "BROKER": "中信"}]
    mc = [{"DATE": "2026-11-03", "TICKER": "2330", "ADJ_CLOSE": "1500.00", "SOURCE": "TWSE / TPEX(VDF)+ cnyes FactSet + Yahoo Finance"}]
    data = {"BasicInfo": basic, "FinancialData": fin, "Summary": [], "Rejected": [], "Combined": [], "FinancialAligned": [], "Deleted": [], "MarketConsensus": mc}
    for k, rows in data.items():
        if with_cols and k != "MarketConsensus":
            rows = [dict({a: b for a, b in r.items() if a not in DERIVED}, BROKER_EN={"Macquarie": "MQ", "中信": "CTBC"}.get(r.get("BROKER"), ""),
                         SOURCE=("報告預估" if str(r.get("PERIOD", "")).endswith(("E", "F")) else "報告實際") if k == "FinancialData" else "報告") for r in rows]
        (v2 / "output" / ("VRN2_%s_latest.json" % k)).write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")


def _rows_of(out: Path, eng: str, book: str) -> list:
    base = out / "VRN2"
    if eng == "duckdb":
        import duckdb  # noqa: WPS433
        con = duckdb.connect(str(base / "vrn2_store.duckdb"), read_only=True)
        try:
            cur = con.execute("SELECT * FROM book_%s" % book.lower())
            names = [d[0] for d in cur.description]
            return [dict(zip(names, r)) for r in cur.fetchall()]
        finally:
            con.close()
    import pyarrow.parquet as pq  # noqa: WPS433
    return [r for f in sorted((base / "parquet" / book).glob("run=*.parquet")) for r in pq.read_table(str(f)).to_pylist()]


def _scenario(eng: str, chk) -> None:
    real_engine = V0100._engine
    if eng == "pyarrow":
        V0100._engine = lambda: ("pyarrow", None)
    try:
        with tempfile.TemporaryDirectory(prefix="vrn2-store103-%s-" % eng) as td:
            root = Path(td)
            v2 = root / "VIA_Reports" / "vrn2"
            (v2 / "output").mkdir(parents=True)
            (v2 / "scope_in").mkdir()
            for n, b in (("a.pdf", b"A"), ("b.pdf", b"B")):
                (v2 / "scope_in" / n).write_bytes(b)
            out = root / "OneDrive" / "out"
            V0100.write_config(v2, str(out), "selftest")
            _books(v2, False)
            V0101._take = _v0101_take                                          # 舊庫:v0102 收(沒有兩欄 · 重現桌機)
            try:
                _v0102_sync(v2, None, "r1")
            finally:
                V0101._take = _take
            n0 = len(_rows_of(out, eng, "FinancialData"))
            _books(v2, True)                                                   # BookSource 寫了兩欄
            r2 = sync(v2, None, "r2")
            fd = _rows_of(out, eng, "FinancialData")
            fill = r2.get("derived_fill") or {}
            chk("%s ① 輸出冊多了兩欄 → 報告冊 0 列追加(不倍增 · FinancialData 仍 %d 列)· 舊列補欄 BasicInfo 2 / FinancialData 3 · SOURCE 預估 / 實際 / 預估 · BROKER_EN MQ / CTBC"
                % (eng, n0), sum(v for k, v in r2["appended"].items() if k != "MarketConsensus") == 0 and len(fd) == n0 == 3
                and fill.get("filled") == {"BasicInfo": 2, "FinancialData": 3} and sorted(_s(r["SOURCE"]) for r in fd) == ["報告實際", "報告預估", "報告預估"]
                and sorted(_s(r["BROKER_EN"]) for r in fd) == ["CTBC", "MQ", "MQ"] and fill.get("lamp") == "GREEN")
            folder = Path(fill.get("folder", "."))
            man = json.loads((folder / FILL_MANIFEST).read_text(encoding="utf-8")) if (folder / FILL_MANIFEST).is_file() else {}
            import pyarrow.parquet as pq  # noqa: WPS433
            part = out / "VRN2" / "parquet" / "FinancialData" / "run=r1.parquet"
            chk("%s ② 補欄前先備份(%s)· 受影響分檔重寫後帶兩欄 · 收據有 derived_fill" % (eng, "DuckDB 檔 + SHA-256" if eng == "duckdb" else "原分檔"),
                man.get("moved_parquet") and (folder / "parquet" / "FinancialData" / "run=r1.parquet").is_file() and part.is_file()
                and set(DERIVED) <= set(pq.read_table(str(part)).column_names) and (eng != "duckdb" or (man.get("backup_sha256") and (folder / man["backup"]).is_file()))
                and json.loads((v2 / "VRN2_OutputStore_latest.json").read_text(encoding="utf-8")).get("derived_fill", {}).get("filled") == fill.get("filled"))
            r3 = sync(v2, None, "r3")
            chk("%s ③ 再跑:0 列追加 · 0 列補欄 · 不再備份(冪等)" % eng, sum(r3["appended"].values()) == 0 and not (r3.get("derived_fill") or {}).get("filled")
                and len(list((out / "VRN2").glob(FILL_PREFIX + "*"))) == 1)
            _books(v2, True, extra=True)
            r4 = sync(v2, None, "r4")
            new = [r for r in _rows_of(out, eng, "FinancialData") if _s(r.get("run_id")) == "r4"]
            chk("%s ④ 新內容列照追加(1 列 · 帶 SOURCE 報告預估 / BROKER_EN CTBC)· MarketConsensus 原文 SOURCE 照 v0102(不重複 · 不補)" % eng,
                r4["appended"].get("FinancialData") == 1 and len(new) == 1 and _s(new[0]["SOURCE"]) == "報告預估" and _s(new[0]["BROKER_EN"]) == "CTBC"
                and r4["appended"].get("MarketConsensus") == 0 and len(_rows_of(out, eng, "MarketConsensus")) == 1)
            back = restore_fill(v2, folder)
            fd_b = _rows_of(out, eng, "FinancialData")
            chk("%s ⑤ restore-fill:換回補欄前(舊三列沒有 SOURCE)· 現在的搬到 restore_replaced/(不刪)" % eng,
                back["lamp"] == "GREEN" and any((folder / "restore_replaced").rglob("*"))
                and sum(1 for r in fd_b if _s(r.get("run_id")) == "r1" and not _s(r.get("SOURCE"))) == 3)
    finally:
        V0100._engine = real_engine


def selftest() -> int:
    bad = []

    def chk(label, cond):
        print(("[PASS] " if cond else "[FAIL] ") + label, flush=True)
        if not cond:
            bad.append(label)
    saved = (V0101._take, V0100.sync, V0101.sync, PRIOR.sync)
    V0101._take = _v0101_take
    V0100.sync = V0101.sync = PRIOR.sync = _v0102_sync
    try:
        rc = PRIOR.selftest()                                                   # 前版自測照前版自己的接線跑
    finally:
        V0101._take, V0100.sync, V0101.sync, PRIOR.sync = saved
    chk("⓪ v0102 自測(含 v0101 / v0100 的接線)照過", rc == 0)
    chk("⑥ 薄尾:v0101 的 _take 與 v0100 / v0101 / v0102 的 sync 都指本版 · 雜湊不算 SOURCE / BROKER_EN · 其他欄照算",
        V0101._take is _take and V0100.sync is sync and PRIOR.sync is sync
        and row_hash103({"A": "1", "SOURCE": "報告", "BROKER_EN": "MQ"}) == V0101.row_hash({"A": "1"}) and row_hash103({"A": "1"}) != row_hash103({"A": "2"}))
    eng, _mod = V0100._engine()
    engines = ["duckdb"] if eng == "duckdb" else []
    try:
        import pyarrow.parquet  # noqa: F401,WPS433
    except ImportError as error:
        print("[SKIP] 這個 Python 的 pyarrow 用不了(%s)· 情境 ①–⑤ 要 pyarrow 讀分檔 · 不驗" % type(error).__name__, flush=True)
        engines = []
    else:
        engines.append("pyarrow")
    try:
        if _booksource() is None:
            print("[SKIP] 同夾沒有 VRN2_BookSource_v*.py · 情境 ①–⑤ 不驗", flush=True)
            engines = []
    except Exception as error:  # noqa: BLE001
        print("[SKIP] BookSource 載不起來(%s)· 情境不驗" % type(error).__name__, flush=True)
        engines = []
    for e in engines:
        _scenario(e, chk)
    print("[%s] %s %s --selftest · 引擎 %s · 不過 %d" % ("PASS" if not bad else "FAIL", DISPLAY_NAME, TAG, "+".join(engines) or "none", len(bad)), flush=True)
    return 0 if not bad else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    def opt(k, d=None):
        return argv[argv.index(k) + 1] if k in argv and argv.index(k) + 1 < len(argv) else d
    if "--selftest" in argv:
        return selftest()
    verb = argv[0] if argv else ""
    if verb in ("fill-source", "restore-fill"):
        v2 = Path(opt("--v2") or (Path(os.environ["VIA_ROOT"]) / "VIA_Reports" / "vrn2" if os.environ.get("VIA_ROOT") else HERE.parent.parent / "VIA_Reports" / "vrn2"))
        if verb == "fill-source":
            r = fill_source(v2, opt("--output-dir"), apply="--apply" in argv)
        else:
            if not opt("--folder"):
                print("[RED] restore-fill 需要 --folder <%s 夾>" % FILL_PREFIX, flush=True)
                return 2
            r = restore_fill(v2, opt("--folder"), opt("--output-dir"))
        print("[%s] %s %s · %s · %s" % (r.get("lamp"), DISPLAY_NAME, TAG, verb, r.get("why")), flush=True)
        return 0 if r.get("lamp") in ("GREEN", "YELLOW", "GRAY") else 1
    return PRIOR.main(argv)


if __name__ == "__main__":
    sys.exit(main())
