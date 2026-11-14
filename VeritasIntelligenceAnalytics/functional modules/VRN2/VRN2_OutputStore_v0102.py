#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_OutputStore v0102 — v0101 薄尾(v0101 / v0100 留著一字不改):增量庫清掉 MOPS 算出來的列(先備份 · 可還原)· 以後不再收 · 多收一本 MarketConsensus。

操作員 2026-11-01:「增量庫 MOPS 資料清掉」(2026-10-31:「不可用 MOPS · 全部國內使用 TWSE TPEX」)。
2026-10-31 16:11 那輪 ⑥e 借的 VDF 引擎抓了 MOPS 財報 → ⑬b 歷史對齊用它覆蓋 / 對帳 → 增量庫追加了 FinancialAligned / Deleted 兩批由 MOPS 算出來的列。本版:
  ① 認列(精準 · 不靠時間):
       Deleted:每一列都是「被歷史數據否定」才進來(有 HISTORY_VALUE / 理由寫歷史)→ 全是 MOPS 算的。
       FinancialAligned:同一輪(run_id)同一份報告(file_sha)只要有一列帶歷史的記號 → 那一組整組是在有 MOPS 歷史時算的
         (記號 = VALUE_SOURCE 以 HISTORY 開頭 · REPORT(無歷史)· REPORT(未對齊)· REPORT(口徑不明 · 不覆蓋)· 有 RECON_RATIO);
         沒有歷史時算的組(只有 REPORT / REPORT(估)/ REPORT(非年度 …)/ REPORT(非數值))不動。
  ② purge-mops(預設只算不動;--apply 才動 · sync 也自動做):先整個庫檔複製到 <輸出夾>/VRN2/_mops_purge_<時間>/(DuckDB 檔 · 被改的 run 分檔)
     → 被清的列另存 removed/<冊>.parquet → 從庫裡刪 → 受影響的 parquet/<冊>/run=<id>.parquet 搬進備份夾、剩下的列重寫回原處 → PURGE_MANIFEST.json
     (條件 · 逐冊逐輪列數 · 備份 SHA-256 · 怎麼還原)· 收據 VIA_Reports\\vrn2\\VRN2_StorePurge_latest.json。再跑 = 0 列(不再備份)。
     restore-purge --folder <備份夾>:庫檔與分檔換回備份(現在的先搬到備份夾的 restore_replaced/ · 不刪)。
  ③ 以後不再收:sync 追加前同一條規則擋掉 FinancialAligned / Deleted 裡 MOPS 算的列(收據 mops_skipped)· catalog 照記。
  ④ 多收一本 MarketConsensus(ConsensusJoin v0105 的 output/VRN2_MarketConsensus_latest · TWSE / TPEX 日線 × 兩家共識):它不是報告冊(沒有 FILENAME)
     → 依 (DATE, TICKER) + 列內容雜湊去重 · 只追加新的一天或變了的列 · 同一套 run_id / row_sha · 不進 catalog(catalog 只記原檔)。
動詞:sync [--v2] [--output-dir] [--run-id] · purge-mops [--v2] [--output-dir] [--apply] · restore-purge --folder <夾> [--v2] [--output-dir] · --selftest
VIA_VRN2_NO_MOPS_PURGE=1 → sync 不自動清(只擋新的)。
"""
from __future__ import annotations

import datetime
import hashlib
import importlib.util
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

TAG = "v0102"
DISPLAY_NAME = "VRN2_OutputStore"
PRIOR_NAME = "VRN2_OutputStore_v0101.py"
HERE = Path(__file__).resolve().parent
DATASET_BOOKS = ("MarketConsensus",)
MOPS_BOOKS = ("FinancialAligned", "Deleted")
MOPS_SOURCES = ("REPORT(無歷史)", "REPORT(未對齊)", "REPORT(口徑不明 · 不覆蓋)")
PURGE_RECEIPT = "VRN2_StorePurge_latest.json"
DATASET_SHA = "dataset:tw_market_consensus"
CRITERIA = ("Deleted:全部(有 HISTORY_VALUE 或理由寫歷史 = 被 MOPS 歷史否定才進來)· FinancialAligned:同一 (run_id, file_sha) 組裡有任一列 VALUE_SOURCE 以 HISTORY 開頭 / "
            "REPORT(無歷史)/ REPORT(未對齊)/ REPORT(口徑不明 · 不覆蓋)/ 有 RECON_RATIO → 整組(在有 MOPS 歷史時算的)")


def _prior():
    for path in (HERE / PRIOR_NAME, HERE.parent / "v147" / "new" / PRIOR_NAME):
        if path.is_file():
            spec = importlib.util.spec_from_file_location("vrn2_outputstore_prior_v0101", path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            return module
    raise FileNotFoundError("前版 %s 不在 %s" % (PRIOR_NAME, HERE))


PRIOR = _prior()                                     # v0101(它再載 v0100)
V0100 = PRIOR.PRIOR
for _name in dir(PRIOR):
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = getattr(PRIOR, _name)
BOOKS = tuple(PRIOR.BOOKS) + tuple(b for b in DATASET_BOOKS if b not in PRIOR.BOOKS)
V0100.BOOKS = PRIOR.BOOKS = BOOKS                    # v0100 的 sync() / mirror() 讀它自己 globals 的 BOOKS
V0100.TAG = PRIOR.TAG = TAG + "(v0101 / v0100 薄尾)"
_v0101_append_duckdb = PRIOR._append_duckdb
_v0101_append_pyarrow = PRIOR._append_pyarrow
_v0100_sync = V0100.sync


# ── ① 認列 ────────────────────────────────────────────────────────────────────────────────────────────────
def _s(v) -> str:
    return "" if v is None else str(v).strip()


def mops_marked(book: str, r: dict) -> bool:
    if book == "Deleted":
        return bool(_s(r.get("HISTORY_VALUE"))) or "歷史" in _s(r.get("DELETED_REASON"))
    if book == "FinancialAligned":
        vs = _s(r.get("VALUE_SOURCE"))
        return vs.startswith("HISTORY") or vs in MOPS_SOURCES or _s(r.get("RECON_RATIO")) not in ("", "None", "nan")
    return False


def mops_index(book: str, rows: list, group=None) -> list:
    """rows 裡 MOPS 算的列號。group(row) = 組鍵(庫裡 = (run_id, file_sha) · 這輪輸出 = FILENAME)· Deleted 逐列判。"""
    if book not in MOPS_BOOKS:
        return []
    if book == "Deleted":
        return [i for i, r in enumerate(rows) if mops_marked(book, r)]
    group = group or (lambda r: (_s(r.get("run_id")), _s(r.get("file_sha"))))
    hit = {group(r) for r in rows if mops_marked(book, r)}
    return [i for i, r in enumerate(rows) if group(r) in hit]


def filter_mops(books_rows: dict) -> tuple:
    """③ 這輪要追加的列先擋 MOPS 算的(同一份報告整組)→ (剩下的, {冊: 擋掉幾列})。"""
    kept, skipped = {}, {}
    for book, rows in books_rows.items():
        drop = set(mops_index(book, rows, lambda r: _s(r.get("FILENAME"))))
        kept[book] = [r for i, r in enumerate(rows) if i not in drop]
        if drop:
            skipped[book] = len(drop)
    return kept, skipped


# ── ④ MarketConsensus(資料集冊 · 不進 catalog)───────────────────────────────────────────────────────────────
def _dataset_take(rows: list, have: set, run_id: str) -> list:
    out, seen = [], set()
    for r in rows:
        flat = V0100._flat(r)
        if not (flat.get("DATE") and flat.get("TICKER")):
            continue
        key = (DATASET_SHA, PRIOR.row_hash(flat))
        if key in have or key in seen:
            continue
        seen.add(key)
        out.append(dict(flat, run_id=run_id, file_sha=DATASET_SHA, row_sha=key[1]))
    return out


def _dataset_duckdb(duckdb, db: Path, pq_dir: Path, run_id: str, rows_by_book: dict) -> tuple:
    appended, totals = {}, {}
    con = duckdb.connect(str(db))
    try:
        for book, rows in rows_by_book.items():
            tbl = "book_" + book.lower()
            exists = con.execute("SELECT count(*) FROM information_schema.tables WHERE table_name=?", [tbl]).fetchone()[0]
            have = set()
            if exists:
                cur = con.execute("SELECT * FROM %s" % tbl)
                names = [d[0] for d in cur.description]
                have = PRIOR._have_from_rows(dict(zip(names, row)) for row in cur.fetchall())
            take = _dataset_take(rows, have, run_id)
            appended[book] = len(take)
            if take:
                cols = list(dict.fromkeys(k for r in take for k in r))
                if not exists:
                    con.execute("CREATE TABLE %s(%s)" % (tbl, ", ".join('"%s" VARCHAR' % c.replace('"', '""') for c in cols)))
                else:
                    have_cols = {r[0] for r in con.execute("SELECT column_name FROM information_schema.columns WHERE table_name=?", [tbl]).fetchall()}
                    for c in cols:
                        if c not in have_cols:
                            con.execute('ALTER TABLE %s ADD COLUMN "%s" VARCHAR' % (tbl, c.replace('"', '""')))
                con.executemany("INSERT INTO %s(%s) VALUES (%s)" % (tbl, ", ".join('"%s"' % c.replace('"', '""') for c in cols), ", ".join("?" * len(cols))), [[r.get(c, "") for c in cols] for r in take])
                out = pq_dir / book
                out.mkdir(parents=True, exist_ok=True)
                con.execute("COPY (SELECT * FROM %s WHERE run_id=?) TO '%s' (FORMAT PARQUET)" % (tbl, str(out / ("run=%s.parquet" % run_id)).replace("'", "''")), [run_id])
            if con.execute("SELECT count(*) FROM information_schema.tables WHERE table_name=?", [tbl]).fetchone()[0]:
                totals[book] = con.execute("SELECT count(*) FROM %s" % tbl).fetchone()[0]
    finally:
        con.close()
    return appended, totals


def _dataset_pyarrow(pq_dir: Path, run_id: str, rows_by_book: dict) -> tuple:
    import pyarrow as pa  # noqa: WPS433
    import pyarrow.parquet as pq  # noqa: WPS433
    appended, totals = {}, {}
    for book, rows in rows_by_book.items():
        out = pq_dir / book
        have = set()
        for f in sorted(out.glob("run=*.parquet")) if out.is_dir() else []:
            have |= PRIOR._have_from_rows(pq.read_table(str(f)).to_pylist())
        take = _dataset_take(rows, have, run_id)
        appended[book] = len(take)
        if take:
            out.mkdir(parents=True, exist_ok=True)
            cols = list(dict.fromkeys(k for r in take for k in r))
            pq.write_table(pa.table({c: [r.get(c, "") for r in take] for c in cols}), str(out / ("run=%s.parquet" % run_id)))
        totals[book] = sum(pq.read_metadata(str(f)).num_rows for f in out.glob("run=*.parquet")) if out.is_dir() else 0
    return appended, totals


def _split(books_rows: dict) -> tuple:
    report = {b: r for b, r in books_rows.items() if b not in DATASET_BOOKS}
    data = {b: r for b, r in books_rows.items() if b in DATASET_BOOKS}
    return report, data


def _append_duckdb(duckdb, db: Path, pq_dir: Path, run_id: str, books_rows: dict, shas: dict) -> dict:
    report, data = _split(books_rows)
    report, skipped = filter_mops(report)
    res = _v0101_append_duckdb(duckdb, db, pq_dir, run_id, report, shas)
    app, tot = _dataset_duckdb(duckdb, db, pq_dir, run_id, data)
    res["appended"].update(app)
    res["totals"].update(tot)
    res["backfilled"].update({b: 0 for b in app})
    res["mops_skipped"] = skipped
    return res


def _append_pyarrow(db_dir: Path, pq_dir: Path, run_id: str, books_rows: dict, shas: dict) -> dict:
    report, data = _split(books_rows)
    report, skipped = filter_mops(report)
    res = _v0101_append_pyarrow(db_dir, pq_dir, run_id, report, shas)
    app, tot = _dataset_pyarrow(pq_dir, run_id, data)
    res["appended"].update(app)
    res["totals"].update(tot)
    res["backfilled"].update({b: 0 for b in app})
    res["mops_skipped"] = skipped
    return res


V0100._append_duckdb = _append_duckdb
V0100._append_pyarrow = _append_pyarrow


# ── ② 清 / 還原 ───────────────────────────────────────────────────────────────────────────────────────────
def _base(v2: Path, output_dir=None):
    cfg = V0100.read_config(v2)
    out = Path(output_dir) if output_dir else (Path(cfg["output_dir"]) if cfg.get("output_dir") else None)
    return (out / "VRN2") if out else None


def _stamp() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def _new_folder(base: Path) -> Path:
    name, n = "_mops_purge_" + _stamp(), 1
    target = base / name
    while target.exists():                                                      # 同一秒第二次 → 加序號
        n += 1
        target = base / ("%s_%d" % (name, n))
    target.mkdir(parents=True)
    return target


def _receipt(v2: Path, rec: dict) -> dict:
    try:
        Path(v2).mkdir(parents=True, exist_ok=True)
        (Path(v2) / PURGE_RECEIPT).write_text(json.dumps(rec, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    except OSError as error:
        rec["receipt_error"] = type(error).__name__
    return rec


def _rows_by_run(rows: list, idx: list) -> dict:
    out = {}
    for i in idx:
        rid = _s(rows[i].get("run_id"))
        out[rid] = out.get(rid, 0) + 1
    return out


def _plan_duckdb(duckdb, db: Path) -> dict:
    """唯讀算 → {冊: {"rowids": [...], "by_run": {run: 列數}, "total": 冊列數}}。"""
    con = duckdb.connect(str(db), read_only=True)
    try:
        plan = {}
        for book in MOPS_BOOKS:
            tbl = "book_" + book.lower()
            if not con.execute("SELECT count(*) FROM information_schema.tables WHERE table_name=?", [tbl]).fetchone()[0]:
                continue
            cur = con.execute("SELECT rowid AS _rid, * FROM %s" % tbl)
            names = [d[0] for d in cur.description]
            rows = [dict(zip(names, r)) for r in cur.fetchall()]
            idx = mops_index(book, rows)
            plan[book] = {"rowids": [rows[i]["_rid"] for i in idx], "by_run": _rows_by_run(rows, idx), "total": len(rows)}
    finally:
        con.close()
    return plan


def _sha(p: Path) -> str:
    return V0100.sha256_file(p) if p.is_file() else ""


def purge_mops(v2: Path, output_dir=None, apply: bool = False) -> dict:
    """② 清掉增量庫裡 MOPS 算的列(apply=False 只算)。回收據(也寫 VRN2_StorePurge_latest.json)。"""
    v2 = Path(v2)
    rec = {"engine": "%s %s" % (DISPLAY_NAME, TAG), "verb": "purge-mops", "at": V0100.now(), "apply": bool(apply), "criteria": CRITERIA}
    base = _base(v2, output_dir)
    if not base:
        rec.update(lamp="GRAY", why="未設定輸出位置 · 沒有增量庫", removed={}, removed_total=0)
        return _receipt(v2, rec)
    eng, duckdb = V0100._engine()
    db, pa_dir, pq_dir = base / "vrn2_store.duckdb", base / "store_pyarrow", base / "parquet"
    rec.update(store=str(base), store_engine=eng)
    try:
        if eng == "duckdb" and db.is_file():
            got = _purge_duckdb(duckdb, db, pq_dir, base, apply)
        elif pq_dir.is_dir() and eng in ("duckdb", "pyarrow") and not db.is_file():
            got = _purge_pyarrow(pq_dir, base, apply)
        elif db.is_file():
            got = {"lamp": "YELLOW", "why": "庫是 DuckDB 但這個 Python 沒有 duckdb · 清不了(交 VCGC 裝 duckdb)", "removed": {}, "removed_total": 0}
        else:
            got = {"lamp": "GRAY", "why": "還沒有增量庫(%s)" % base, "removed": {}, "removed_total": 0}
    except Exception as error:  # noqa: BLE001
        got = {"lamp": "RED", "why": "清 MOPS 列失敗:%s: %s(庫備份在 purge 夾 · 可 restore-purge)" % (type(error).__name__, str(error)[:200]), "removed": {}, "removed_total": 0}
    rec.update(got)
    return _receipt(v2, rec)


def _purge_duckdb(duckdb, db: Path, pq_dir: Path, base: Path, apply: bool) -> dict:
    plan = _plan_duckdb(duckdb, db)
    removed = {b: len(p["rowids"]) for b, p in plan.items()}
    total = sum(removed.values())
    res = {"removed": removed, "removed_total": total, "by_run": {b: p["by_run"] for b, p in plan.items() if p["by_run"]}, "totals_before": {b: p["total"] for b, p in plan.items()}}
    if not total:
        return dict(res, lamp="GREEN", why="增量庫沒有 MOPS 算的列(FinancialAligned / Deleted 都乾淨)")
    if not apply:
        return dict(res, lamp="YELLOW", why="增量庫有 MOPS 算的列 %s(只算沒動 · --apply 才清 · 先備份)" % json.dumps(removed, ensure_ascii=False))
    folder = _new_folder(base)
    backup = folder / "vrn2_store.duckdb.bak"
    shutil.copy2(str(db), str(backup))
    wal = db.with_name(db.name + ".wal")
    if wal.is_file():
        shutil.copy2(str(wal), str(folder / (wal.name + ".bak")))
    moved, rewritten = [], []
    con = duckdb.connect(str(db))
    try:
        for book, p in plan.items():
            if not p["rowids"]:
                continue
            tbl = "book_" + book.lower()
            con.execute("CREATE OR REPLACE TEMP TABLE _purge(rid BIGINT)")
            con.executemany("INSERT INTO _purge VALUES (?)", [[int(r)] for r in p["rowids"]])
            (folder / "removed").mkdir(exist_ok=True)
            con.execute("COPY (SELECT * FROM %s WHERE rowid IN (SELECT rid FROM _purge)) TO '%s' (FORMAT PARQUET)" % (tbl, str(folder / "removed" / ("%s.parquet" % book)).replace("'", "''")))
            con.execute("DELETE FROM %s WHERE rowid IN (SELECT rid FROM _purge)" % tbl)
            for rid in sorted(p["by_run"]):
                src = pq_dir / book / ("run=%s.parquet" % rid)
                if src.is_file():
                    dest = folder / "parquet" / book / src.name
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    src.replace(dest)
                    moved.append("%s/%s" % (book, src.name))
                left = con.execute("SELECT count(*) FROM %s WHERE run_id=?" % tbl, [rid]).fetchone()[0]
                if left:
                    src.parent.mkdir(parents=True, exist_ok=True)
                    con.execute("COPY (SELECT * FROM %s WHERE run_id=?) TO '%s' (FORMAT PARQUET)" % (tbl, str(src).replace("'", "''")), [rid])
                    rewritten.append("%s/%s(留 %d 列)" % (book, src.name, left))
        con.execute("CHECKPOINT")
        after = {b: con.execute("SELECT count(*) FROM %s" % ("book_" + b.lower())).fetchone()[0] for b in plan}
    finally:
        con.close()
    manifest = {"engine": "%s %s" % (DISPLAY_NAME, TAG), "at": V0100.now(), "store_engine": "duckdb", "store": str(db), "criteria": CRITERIA, "removed": removed,
                "by_run": res["by_run"], "totals_before": res["totals_before"], "totals_after": after, "backup": backup.name, "backup_sha256": _sha(backup),
                "moved_parquet": moved, "rewritten_parquet": rewritten, "removed_rows": {b: "removed/%s.parquet" % b for b, n in removed.items() if n},
                "restore": "VRN2_OutputStore_v0102.py restore-purge --folder \"%s\"" % folder}
    (folder / "PURGE_MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    return dict(res, lamp="GREEN", folder=str(folder), totals_after=after, backup_sha256=manifest["backup_sha256"], moved_parquet=moved, rewritten_parquet=rewritten,
                why="清掉 MOPS 算的列 %s(備份 %s · 可 restore-purge)" % (json.dumps(removed, ensure_ascii=False), folder.name))


def _purge_pyarrow(pq_dir: Path, base: Path, apply: bool) -> dict:
    import pyarrow as pa  # noqa: WPS433
    import pyarrow.parquet as pq  # noqa: WPS433
    plan = {}
    for book in MOPS_BOOKS:
        for f in sorted((pq_dir / book).glob("run=*.parquet")) if (pq_dir / book).is_dir() else []:
            rows = pq.read_table(str(f)).to_pylist()
            idx = mops_index(book, rows)
            if idx:
                plan.setdefault(book, []).append((f, rows, idx))
    removed = {b: sum(len(i) for _, _, i in v) for b, v in plan.items()}
    total = sum(removed.values())
    res = {"removed": removed, "removed_total": total, "by_run": {b: {f.stem[4:]: len(i) for f, _, i in v} for b, v in plan.items()}}
    if not total:
        return dict(res, lamp="GREEN", why="增量庫(pyarrow)沒有 MOPS 算的列")
    if not apply:
        return dict(res, lamp="YELLOW", why="增量庫(pyarrow)有 MOPS 算的列 %s(只算沒動 · --apply 才清)" % json.dumps(removed, ensure_ascii=False))
    folder = _new_folder(base)
    moved, rewritten = [], []
    for book, items in plan.items():
        gone = []
        for f, rows, idx in items:
            dest = folder / "parquet" / book / f.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            f.replace(dest)
            moved.append("%s/%s" % (book, f.name))
            drop = set(idx)
            gone += [r for i, r in enumerate(rows) if i in drop]
            keep = [r for i, r in enumerate(rows) if i not in drop]
            if keep:
                cols = list(dict.fromkeys(k for r in keep for k in r))
                pq.write_table(pa.table({c: [r.get(c, "") for r in keep] for c in cols}), str(f))
                rewritten.append("%s/%s(留 %d 列)" % (book, f.name, len(keep)))
        if gone:
            (folder / "removed").mkdir(exist_ok=True)
            cols = list(dict.fromkeys(k for r in gone for k in r))
            pq.write_table(pa.table({c: [r.get(c, "") for r in gone] for c in cols}), str(folder / "removed" / ("%s.parquet" % book)))
    manifest = {"engine": "%s %s" % (DISPLAY_NAME, TAG), "at": V0100.now(), "store_engine": "pyarrow", "store": str(pq_dir), "criteria": CRITERIA, "removed": removed,
                "by_run": res["by_run"], "moved_parquet": moved, "rewritten_parquet": rewritten, "removed_rows": {b: "removed/%s.parquet" % b for b in removed},
                "restore": "VRN2_OutputStore_v0102.py restore-purge --folder \"%s\"" % folder}
    (folder / "PURGE_MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    return dict(res, lamp="GREEN", folder=str(folder), moved_parquet=moved, rewritten_parquet=rewritten,
                why="清掉 MOPS 算的列 %s(原分檔在 %s · 可 restore-purge)" % (json.dumps(removed, ensure_ascii=False), folder.name))


def restore_purge(v2: Path, folder, output_dir=None) -> dict:
    """把一次 purge 換回去:現在的庫檔 / 分檔先搬到 <備份夾>/restore_replaced/(不刪)→ 備份換回原處。"""
    v2, folder = Path(v2), Path(folder)
    rec = {"engine": "%s %s" % (DISPLAY_NAME, TAG), "verb": "restore-purge", "at": V0100.now(), "folder": str(folder)}
    try:
        man = json.loads((folder / "PURGE_MANIFEST.json").read_text(encoding="utf-8"))
    except Exception as error:  # noqa: BLE001
        rec.update(lamp="RED", why="讀不到 %s 的 PURGE_MANIFEST.json(%s)" % (folder, type(error).__name__))
        return _receipt(v2, rec)
    base = folder.parent
    pq_dir, repl = base / "parquet", folder / "restore_replaced" / _stamp()
    restored = []
    if man.get("store_engine") == "duckdb":
        db, backup = base / "vrn2_store.duckdb", folder / man.get("backup", "vrn2_store.duckdb.bak")
        if not backup.is_file() or (man.get("backup_sha256") and _sha(backup) != man["backup_sha256"]):
            rec.update(lamp="RED", why="備份 %s 不在或雜湊對不上 · 不還原" % backup.name)
            return _receipt(v2, rec)
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
    (folder / "PURGE_MANIFEST.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    rec.update(lamp="GREEN", restored=restored, replaced_to=str(repl), why="已還原 %d 個檔(現在的搬到 %s)" % (len(restored), repl))
    return _receipt(v2, rec)


# ── sync = 先清(備份)→ v0100 的 sync(本版的追加:擋 MOPS · 多一本資料集冊)───────────────────────────────────────
def sync(v2: Path, output_dir: Path | None = None, run_id: str | None = None) -> dict:
    pre = None
    if os.environ.get("VIA_VRN2_NO_MOPS_PURGE") != "1":
        pre = purge_mops(v2, output_dir, apply=True)
    rec = _v0100_sync(v2, output_dir, run_id)
    if pre is not None and pre.get("lamp") != "GRAY":
        rec["mops_purge"] = {k: pre.get(k) for k in ("lamp", "why", "removed", "removed_total", "folder") if k in pre}
        if pre.get("lamp") == "RED" and rec.get("lamp") == "GREEN":
            rec["lamp"] = "YELLOW"
        if pre.get("removed_total") or pre.get("lamp") == "RED":
            rec["why"] = ("%s · " % rec["why"] if rec.get("why") else "") + "MOPS 列:" + str(pre.get("why", ""))
        V0100._write_receipt(Path(v2), rec)
    return rec


V0100.sync = PRIOR.sync = sync
read_config = V0100.read_config
write_config = V0100.write_config


# ── 自測 ──────────────────────────────────────────────────────────────────────────────────────────────────
def _books(v2: Path, mops: bool, day: str = "2026-10-31") -> None:
    fa = [{"FILENAME": "a.pdf", "ITEM": "Revenue", "PERIOD": "2025A", "VALUE_FINAL": 1000.0, "VALUE_SOURCE": "REPORT"},
          {"FILENAME": "b.pdf", "ITEM": "EPS", "PERIOD": "2026E", "VALUE_FINAL": 5.0, "VALUE_SOURCE": "REPORT(估)"}]
    dl = []
    if mops:
        fa = [{"FILENAME": "a.pdf", "ITEM": "Revenue", "PERIOD": "2025A", "VALUE_FINAL": 1001.0, "VALUE_SOURCE": "HISTORY(MOPS / TWSE)", "RECON_RATIO": 0.999},
              {"FILENAME": "a.pdf", "ITEM": "EPS", "PERIOD": "2026E", "VALUE_FINAL": 5.5, "VALUE_SOURCE": "REPORT(估)", "SCALE": 0.001},
              {"FILENAME": "b.pdf", "ITEM": "EPS", "PERIOD": "2026E", "VALUE_FINAL": 5.0, "VALUE_SOURCE": "REPORT(估)"},
              {"FILENAME": "c.pdf", "ITEM": "Revenue", "PERIOD": "2026E", "VALUE_FINAL": 7.0, "VALUE_SOURCE": "REPORT(估)"}]
        dl = [{"FILENAME": "a.pdf", "ITEM": "Net income", "HISTORY_VALUE": 99.0, "DELETED_REASON": "與歷史數據差 > 3% → 歷史覆蓋"}]
    mc = [{"DATE": day, "TICKER": "2330", "NAME": "台積電", "ADJ_CLOSE": "1500.00", "FACTSET_TARGET_PRICE_MEDIAN": "1650.00", "YFINANCE_TARGET_PRICE_MEDIAN": "1700.00"}]
    data = {"BasicInfo": [{"FILENAME": "a.pdf", "TICKER": "2330"}, {"FILENAME": "b.pdf", "TICKER": "2454"}], "FinancialData": [], "Summary": [], "Rejected": [],
            "Combined": [{"FILENAME": "a.pdf", "TARGET_PRICE": "100"}], "FinancialAligned": fa, "Deleted": dl, "MarketConsensus": mc}
    for k, rows in data.items():
        (v2 / "output" / ("VRN2_%s_latest.json" % k)).write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")


def _count(out: Path, eng: str, book: str) -> int:
    base = out / "VRN2"
    if eng == "duckdb":
        import duckdb  # noqa: WPS433
        con = duckdb.connect(str(base / "vrn2_store.duckdb"), read_only=True)
        try:
            return con.execute("SELECT count(*) FROM book_%s" % book.lower()).fetchone()[0]
        finally:
            con.close()
    import pyarrow.parquet as pq  # noqa: WPS433
    return sum(pq.read_metadata(str(f)).num_rows for f in (base / "parquet" / book).glob("run=*.parquet"))


def _scenario(eng: str, chk) -> None:
    real_engine = V0100._engine
    if eng == "pyarrow":
        V0100._engine = lambda: ("pyarrow", None)
    try:
        with tempfile.TemporaryDirectory(prefix="vrn2-store102-%s-" % eng) as td:
            root = Path(td)
            v2 = root / "VIA_Reports" / "vrn2"
            (v2 / "output").mkdir(parents=True)
            (v2 / "scope_in").mkdir()
            for n, b in (("a.pdf", b"A"), ("b.pdf", b"B"), ("c.pdf", b"C")):
                (v2 / "scope_in" / n).write_bytes(b)
            out = root / "OneDrive" / "out"
            V0100.write_config(v2, str(out), "selftest")
            _books(v2, False)
            V0100._append_duckdb, V0100._append_pyarrow = _v0101_append_duckdb, _v0101_append_pyarrow     # 舊庫:照 v0101 收(收進 MOPS 列 · 重現桌機)
            try:
                _v0100_sync(v2, None, "r1")
                _books(v2, True)
                _v0100_sync(v2, None, "r2_mops")
            finally:
                V0100._append_duckdb, V0100._append_pyarrow = _append_duckdb, _append_pyarrow
            fa0, dl0 = _count(out, eng, "FinancialAligned"), _count(out, eng, "Deleted")
            plan = purge_mops(v2, None, apply=False)
            chk("%s ① 舊庫(v0101 收進 MOPS 列)· 只算:FinancialAligned 清 2(a.pdf 那組 · 含 REPORT(估) 那列)· b.pdf 不動 · Deleted 清 1 · 沒動庫" % eng,
                plan["removed"] == {"FinancialAligned": 2, "Deleted": 1} and plan["lamp"] == "YELLOW" and _count(out, eng, "FinancialAligned") == fa0 == 5 and dl0 == 1
                and not list((out / "VRN2").glob("_mops_purge_*")))
            done = purge_mops(v2, None, apply=True)
            folder = Path(done.get("folder", "."))
            man = json.loads((folder / "PURGE_MANIFEST.json").read_text(encoding="utf-8")) if (folder / "PURGE_MANIFEST.json").is_file() else {}
            chk("%s ② --apply:先備份(%s)· 被清的列另存 removed/ · FinancialAligned 5 → 3 · Deleted 1 → 0 · 受影響的 run 分檔搬進備份夾 · 剩的重寫"
                % (eng, "DuckDB 檔 + SHA-256" if eng == "duckdb" else "原分檔"),
                done["lamp"] == "GREEN" and _count(out, eng, "FinancialAligned") == 3 and _count(out, eng, "Deleted") == 0 and (folder / "removed" / "FinancialAligned.parquet").is_file()
                and (folder / "parquet" / "FinancialAligned" / "run=r2_mops.parquet").is_file() and (out / "VRN2" / "parquet" / "FinancialAligned" / "run=r2_mops.parquet").is_file()
                and not (out / "VRN2" / "parquet" / "Deleted" / "run=r2_mops.parquet").exists() and (eng != "duckdb" or (man.get("backup_sha256") and (folder / man["backup"]).is_file()))
                and json.loads((v2 / PURGE_RECEIPT).read_text(encoding="utf-8"))["removed_total"] == 3)
            again = purge_mops(v2, None, apply=True)
            chk("%s ③ 再清 = 0 列 · 不再備份(冪等)" % eng, again["removed_total"] == 0 and again["lamp"] == "GREEN" and len(list((out / "VRN2").glob("_mops_purge_*"))) == 1)
            r3 = sync(v2, None, "r3")
            chk("%s ④ sync 擋新的:輸出冊還帶 MOPS 列 → 擋 FinancialAligned 2 · Deleted 1(mops_skipped)· 庫不再收 · MarketConsensus 新冊 1 列" % eng,
                r3.get("mops_skipped") == {"FinancialAligned": 2, "Deleted": 1} and _count(out, eng, "FinancialAligned") == 3 and _count(out, eng, "Deleted") == 0
                and r3["appended"].get("MarketConsensus") == 1 and r3["totals"].get("MarketConsensus") == 1 and "@" not in json.dumps(r3.get("new_files")))
            _books(v2, False)
            r4 = sync(v2, None, "r4")
            _books(v2, False, "2026-11-01")
            r5 = sync(v2, None, "r5")
            chk("%s ⑤ MarketConsensus:同內容再跑 0 列 · 新的一天 +1(累計 2)· 不進 catalog(原檔仍 3 份)" % eng,
                r4["appended"].get("MarketConsensus") == 0 and r5["appended"].get("MarketConsensus") == 1 and r5["totals"].get("MarketConsensus") == 2 and r5.get("catalog_files") == 3
                and (out / "VRN2" / "latest" / "VRN2_MarketConsensus_latest.json").is_file())
            back = restore_purge(v2, folder)
            chk("%s ⑥ restore-purge:換回備份 → FinancialAligned / Deleted 回到清之前(%d / %d)· 現在的先搬到 restore_replaced/(不刪)" % (eng, fa0, dl0),
                back["lamp"] == "GREEN" and _count(out, eng, "Deleted") == dl0 and _count(out, eng, "FinancialAligned") == fa0
                and any((folder / "restore_replaced").rglob("*")))
    finally:
        V0100._engine = real_engine


def selftest() -> int:
    bad = []

    def chk(label, cond):
        print(("[PASS] " if cond else "[FAIL] ") + label, flush=True)
        if not cond:
            bad.append(label)
    saved = (V0100._append_duckdb, V0100._append_pyarrow, V0100.sync, V0100.BOOKS)
    V0100._append_duckdb, V0100._append_pyarrow, V0100.sync, V0100.BOOKS = _v0101_append_duckdb, _v0101_append_pyarrow, _v0100_sync, PRIOR.BOOKS[:7]
    PRIOR.BOOKS, PRIOR.sync = PRIOR.BOOKS[:7], _v0100_sync
    try:
        rc = PRIOR.selftest()                                                   # 前版自測照前版自己的接線跑
    finally:
        V0100._append_duckdb, V0100._append_pyarrow, V0100.sync, V0100.BOOKS = saved
        PRIOR.BOOKS, PRIOR.sync = BOOKS, sync
    chk("① v0101 自測(含 v0100 的接線)照過", rc == 0)
    chk("② 薄尾:BOOKS 八本(七本 + MarketConsensus)· v0100 的 sync / 追加函式都指本版", BOOKS[-1] == "MarketConsensus" and len(BOOKS) == 8 and V0100.BOOKS == BOOKS
        and V0100._append_duckdb is _append_duckdb and V0100._append_pyarrow is _append_pyarrow and V0100.sync is sync and PRIOR.sync is sync)
    chk("③ 認列:HISTORY / 無歷史 / 未對齊 / 口徑不明 / 有 RECON_RATIO 是記號 · REPORT / 估 / 非年度 / 非數值不是 · Deleted 有 HISTORY_VALUE 是",
        all(mops_marked("FinancialAligned", {"VALUE_SOURCE": v}) for v in ("HISTORY(MOPS / TWSE)", "HISTORY(覆蓋 · 報告值進刪除區)", "REPORT(無歷史)", "REPORT(未對齊)", "REPORT(口徑不明 · 不覆蓋)"))
        and mops_marked("FinancialAligned", {"VALUE_SOURCE": "REPORT", "RECON_RATIO": "0.98"})
        and not any(mops_marked("FinancialAligned", {"VALUE_SOURCE": v, "RECON_RATIO": ""}) for v in ("REPORT", "REPORT(估)", "REPORT(非年度 · 不對歷史)", "REPORT(非數值)"))
        and mops_marked("Deleted", {"HISTORY_VALUE": "1.0"}) and not mops_marked("Combined", {"VALUE_SOURCE": "HISTORY"}))
    rows = [{"run_id": "r", "file_sha": "x", "VALUE_SOURCE": "REPORT(估)"}, {"run_id": "r", "file_sha": "x", "VALUE_SOURCE": "HISTORY(MOPS / TWSE)"},
            {"run_id": "r", "file_sha": "y", "VALUE_SOURCE": "REPORT(估)"}, {"run_id": "q", "file_sha": "x", "VALUE_SOURCE": "REPORT(估)"}]
    chk("④ 整組:同 (run_id, file_sha) 有記號 → 整組(估那列也清)· 別輪 / 別檔不動", mops_index("FinancialAligned", rows) == [0, 1])
    eng, _mod = V0100._engine()
    engines = []
    if eng == "duckdb":
        engines.append("duckdb")
    try:
        import pyarrow.parquet  # noqa: F401,WPS433
    except ImportError as error:
        print("[SKIP] 這個 Python 的 pyarrow 用不了(%s)· pyarrow 備援那段不驗" % type(error).__name__, flush=True)
    else:
        engines.append("pyarrow")
    if not engines:
        print("[SKIP] 沒有 duckdb / pyarrow · 只驗 ① ~ ④", flush=True)
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
    if verb in ("purge-mops", "restore-purge"):
        v2 = Path(opt("--v2") or (Path(os.environ["VIA_ROOT"]) / "VIA_Reports" / "vrn2" if os.environ.get("VIA_ROOT") else HERE.parent.parent / "VIA_Reports" / "vrn2"))
        if verb == "purge-mops":
            r = purge_mops(v2, opt("--output-dir"), apply="--apply" in argv)
        else:
            if not opt("--folder"):
                print("[RED] restore-purge 需要 --folder <_mops_purge_ 夾>", flush=True)
                return 2
            r = restore_purge(v2, opt("--folder"), opt("--output-dir"))
        print("[%s] %s %s · %s · %s" % (r.get("lamp"), DISPLAY_NAME, TAG, verb, r.get("why")), flush=True)
        return 0 if r.get("lamp") in ("GREEN", "YELLOW", "GRAY") else 1
    return V0100.main(argv)


if __name__ == "__main__":
    sys.exit(main())
