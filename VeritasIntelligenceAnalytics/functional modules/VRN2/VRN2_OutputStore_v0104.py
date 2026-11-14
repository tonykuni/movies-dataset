#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_OutputStore v0104 — v0103 薄尾(v0103 / v0102 / v0101 / v0100 留著一字不改):四點去開頭符號 · 主題與摘要新格式後增量庫不重複追加 · 舊列就地整理。

操作員 2026-11-03:「四點摘要前面出現任何標點符號如 ➢ 則刪除」「第一點通常為評價,採取每日更新後的 ADJ 目標價 · ADJ CLOSE 來計算上漲空間」
「標題格式 Name(YFinance Ticker, 評等) - 原文標題」。VRN2_BookSource v0101 在 ⑬a 把 Summary 冊的四點 / 標題去掉開頭符號、把 Combined 冊的
「TOPIC & SUMMARY」改成新格式。v0103 的列內容雜湊會把這些列都當成「內容變了」再追加一次(Summary · Combined 倍增)。本版:
  ① 列內容雜湊:Summary 列(有 POINT_1 ~ POINT_4 的列)的 TITLE / 四點先去開頭符號再算;Combined 的 TOPIC & SUMMARY 不算(它由 Summary 的四點與
     Combined 同列的名稱 · 代號 · 評等 · 調整後目標價 · 調整後收盤組出來 · 那些欄照算)。SOURCE / BROKER_EN 照 v0103 不算。其他冊照 v0103。
     既有列另外用同一套規則重算一次放進「已有」集合 → 舊庫的列(還帶 ➢ · 舊格式)也認得出來,不追加。
  ② 舊列就地整理(sync 後自動做 · 也可單獨 tidy-summary [--apply]):庫裡 Summary 的 TITLE / 四點去開頭符號;Combined 的 TOPIC & SUMMARY 用
     BookSource v0101 同一支 compose 重組(用該列自己那一輪的調整後目標價 / 調整後收盤 · 同一原檔最新一輪的 Summary)。
     先整個庫檔複製到 <輸出夾>/VRN2/_summary_tidy_<時間>/(SHA-256)→ 依 rowid 只改有變的欄(+ row_sha 用 ① 的規則重算)→ 受影響的
     parquet/<冊>/run=<id>.parquet 搬進備份夾、從庫重寫回原處;pyarrow 備援:受影響分檔先複製進備份夾再寫回。FILL_MANIFEST.json 記逐冊列數 · 備份雜湊 ·
     怎麼還原(restore-fill --folder <夾> 與 v0103 同一個還原動詞)。再跑 = 0 列(不再備份)。不刪列。
  ③ 收據 VRN2_OutputStore_latest.json 多 summary_tidy{lamp, why, changed{Summary, Combined}, partitions, folder}。整理失敗只黃 · 不擋 ⑬。
     VIA_VRN2_NO_BOOKSOURCE=1(⑬a 關掉)→ 不整理(GRAY)。同夾沒有 BookSource v0101 以上 → 雜湊照 v0103 + 不整理。
動詞:sync · fill-source · restore-fill · purge-mops / restore-purge(同 v0103)· tidy-summary [--v2] [--output-dir] [--apply] · --selftest
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

TAG = "v0104"
DISPLAY_NAME = "VRN2_OutputStore"
PRIOR_NAME = "VRN2_OutputStore_v0103.py"
HERE = Path(__file__).resolve().parent
POINTS = ("POINT_1", "POINT_2", "POINT_3", "POINT_4")
TEXT = ("TITLE",) + POINTS
TOPIC = "TOPIC & SUMMARY"
TIDY_PREFIX = "_summary_tidy_"


def _load(name: str, alias: str):
    path = HERE / name
    if not path.is_file():
        raise FileNotFoundError("前版 %s 不在 %s" % (name, HERE))
    spec = importlib.util.spec_from_file_location(alias, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PRIOR = _load(PRIOR_NAME, "vrn2_outputstore_prior_v0103")       # v0103(它再載 v0102 → v0101 → v0100)
V0102 = PRIOR.PRIOR
V0101 = PRIOR.V0101
V0100 = PRIOR.V0100
for _name in dir(PRIOR):
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = getattr(PRIOR, _name)
V0100.TAG = V0101.TAG = V0102.TAG = PRIOR.TAG = TAG + "(v0103 / v0102 / v0101 / v0100 薄尾)"
_v0103_take = PRIOR._take
_v0101_have = V0101._have_from_rows
_v0103_sync = PRIOR.sync
DERIVED = PRIOR.DERIVED
FILL_MANIFEST = PRIOR.FILL_MANIFEST

_BS: dict = {}


def _bs():
    """同夾最高版 BookSource(v0101 以上才有 strip_lead / compose);載不起來 → None。只載一次。"""
    if "m" not in _BS:
        try:
            _BS["m"] = PRIOR._booksource()
        except Exception:  # noqa: BLE001
            _BS["m"] = None
    m = _BS["m"]
    return m if (m is not None and hasattr(m, "strip_lead") and hasattr(m, "compose")) else None


def _s(v) -> str:
    return "" if v is None else str(v)


# ── ① 雜湊 ────────────────────────────────────────────────────────────────────────────────────────────
def norm(flat: dict) -> dict:
    """算雜湊前的樣子:去 SOURCE / BROKER_EN 與 TOPIC & SUMMARY;Summary 列(有四點欄)的 TITLE / 四點去開頭符號。"""
    d = {k: v for k, v in flat.items() if k not in DERIVED and k != TOPIC}
    bs = _bs()
    if bs is not None and any(k in d for k in POINTS):
        for k in TEXT:
            if isinstance(d.get(k), str):
                d[k] = bs.strip_lead(d[k])
    return d


def row_hash104(flat: dict) -> str:
    return V0101.row_hash(norm(flat))


def _take(rows: list, shas: dict, have: set, run_id: str) -> list:
    """同 v0103 _take,只差列內容雜湊用 ① 的規則。"""
    out, seen = [], set()
    for r in rows:
        sha = shas.get(r.get("FILENAME", ""), "")
        if not sha:
            continue
        flat = V0100._flat(r)
        key = (sha, row_hash104(flat))
        if key in have or key in seen:
            continue
        seen.add(key)
        out.append(dict(flat, run_id=run_id, file_sha=sha, row_sha=key[1]))
    return out


def _have_from_rows(rows) -> set:
    """既有列 → {(file_sha, row_sha)}(同 v0101)+ Summary / Combined 列再用 ① 的規則重算一次(舊庫的 ➢ / 舊格式也認得)。"""
    have = set()
    for r in rows:
        r = {k: _s(v) for k, v in r.items()}
        fs = r.get("file_sha", "")
        have.add((fs, r.get("row_sha") or V0101.row_hash(r)))
        if TOPIC in r or any(k in r for k in POINTS):
            have.add((fs, row_hash104(r)))
    return have


V0101._take = _take
V0101._have_from_rows = _have_from_rows


# ── ② 舊列就地整理 ────────────────────────────────────────────────────────────────────────────────────
def _latest(rows: list) -> dict:
    """[(id, row)] → {file_sha: 最新一輪那列}(run_id 字串大者為新)。"""
    out = {}
    for _i, r in rows:
        k = r.get("file_sha", "")
        if k and (k not in out or _s(r.get("run_id")) >= _s(out[k].get("run_id"))):
            out[k] = r
    return out


def plan(bs, summ_rows: list, comb_rows: list, basic_rows: list) -> tuple:
    """[(id, row)] × 3 → ({id: 新的 Summary 列}, {id: 新的 Combined 列});只收有變的列。"""
    s_new = {}
    for i, r in summ_rows:
        n = dict(r)
        for k in TEXT:
            if k in n:
                n[k] = bs.strip_lead(n[k])
        if any(n[k] != r[k] for k in TEXT if k in r):
            n["row_sha"] = row_hash104(n)
            s_new[i] = n
    summ = _latest([(i, s_new.get(i, r)) for i, r in summ_rows])
    basic = _latest(basic_rows)
    c_new = {}
    for i, r in comb_rows:
        if TOPIC not in r:
            continue
        fs = r.get("file_sha", "")
        s, b = summ.get(fs, {}), basic.get(fs, {})
        if not (s or b):
            continue
        text, _redone = bs.compose(r, b, s)
        if text != r.get(TOPIC):
            n = dict(r)
            n[TOPIC] = text
            n["row_sha"] = row_hash104(n)
            c_new[i] = n
    return s_new, c_new


def _new_folder(base: Path) -> Path:
    name, n = TIDY_PREFIX + datetime.datetime.now().strftime("%Y%m%d_%H%M%S"), 1
    target = base / name
    while target.exists():
        n += 1
        target = base / ("%s_%d" % (name, n))
    target.mkdir(parents=True)
    return target


def _q(c: str) -> str:
    return '"%s"' % c.replace('"', '""')


BOOKS3 = (("Summary", "book_summary"), ("Combined", "book_combined"), ("BasicInfo", "book_basicinfo"))


def _tidy_duckdb(duckdb, db: Path, pq_dir: Path, base: Path, bs, apply: bool) -> dict:
    got = {}
    con = duckdb.connect(str(db), read_only=True)
    try:
        for book, tbl in BOOKS3:
            if not con.execute("SELECT count(*) FROM information_schema.tables WHERE table_name=?", [tbl]).fetchone()[0]:
                got[book] = []
                continue
            cur = con.execute("SELECT rowid AS _vrn2_rid, * FROM %s" % tbl)
            names = [d[0] for d in cur.description][1:]
            got[book] = [(r[0], {n: _s(v) for n, v in zip(names, r[1:])}) for r in cur.fetchall()]
    finally:
        con.close()
    s_new, c_new = plan(bs, got["Summary"], got["Combined"], got["BasicInfo"])
    changed = {"Summary": len(s_new), "Combined": len(c_new)}
    if not (s_new or c_new):
        return {"lamp": "GREEN", "why": "增量庫的 Summary 四點 / Combined 主題與摘要都已是新格式", "changed": changed, "partitions": 0}
    if not apply:
        return {"lamp": "YELLOW", "why": "增量庫有 Summary %d · Combined %d 列待整理(只算沒動 · --apply 才改 · 先備份)" % (len(s_new), len(c_new)),
                "changed": changed, "partitions": 0}
    folder = _new_folder(base)
    backup = folder / "vrn2_store.duckdb.bak"
    shutil.copy2(str(db), str(backup))
    wal = db.with_name(db.name + ".wal")
    if wal.is_file():
        shutil.copy2(str(wal), str(folder / (wal.name + ".bak")))
    old = {"Summary": dict(got["Summary"]), "Combined": dict(got["Combined"])}
    moved, rewritten = [], []
    con = duckdb.connect(str(db))
    try:
        for book, tbl, new in (("Summary", "book_summary", s_new), ("Combined", "book_combined", c_new)):
            if not new:
                continue
            for rid, n in new.items():
                was = old[book][rid]
                cols = [c for c in n if c != "row_sha" and n[c] != was.get(c)] + (["row_sha"] if "row_sha" in was else [])
                con.execute("UPDATE %s SET %s WHERE rowid = ?" % (tbl, ", ".join("%s = ?" % _q(c) for c in cols)), [n[c] for c in cols] + [rid])
            for run in sorted({_s(n.get("run_id")) for n in new.values()}):
                src = pq_dir / book / ("run=%s.parquet" % run)
                if not src.is_file():
                    continue
                dest = folder / "parquet" / book / src.name
                dest.parent.mkdir(parents=True, exist_ok=True)
                src.replace(dest)
                moved.append("%s/%s" % (book, src.name))
                con.execute("COPY (SELECT * FROM %s WHERE run_id=?) TO '%s' (FORMAT PARQUET)" % (tbl, str(src).replace("'", "''")), [run])
                rewritten.append("%s/%s" % (book, src.name))
        con.execute("CHECKPOINT")
    finally:
        con.close()
    man = {"engine": "%s %s" % (DISPLAY_NAME, TAG), "at": V0100.now(), "kind": "summary_tidy", "store_engine": "duckdb", "store": str(db), "changed": changed,
           "backup": backup.name, "backup_sha256": V0100.sha256_file(backup), "moved_parquet": moved, "rewritten_parquet": rewritten,
           "rule": "Summary TITLE / 四點去開頭符號 · Combined TOPIC & SUMMARY 由 %s compose 重組(該列自己那一輪的調整後目標價 / 調整後收盤)· row_sha 依 v0104 規則重算 · 不刪列"
                   % ("%s %s" % (getattr(bs, "DISPLAY_NAME", "VRN2_BookSource"), getattr(bs, "VERSION", ""))),
           "restore": "VRN2_OutputStore_v0104.py restore-fill --folder \"%s\"" % folder}
    (folder / FILL_MANIFEST).write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"lamp": "GREEN", "why": "整理 Summary %d · Combined %d 列(分檔重寫 %d · 備份 %s · 可 restore-fill)" % (len(s_new), len(c_new), len(rewritten), folder.name),
            "changed": changed, "partitions": len(rewritten), "folder": str(folder)}


def _tidy_pyarrow(pq_dir: Path, base: Path, bs, apply: bool) -> dict:
    import pyarrow as pa  # noqa: WPS433
    import pyarrow.parquet as pq  # noqa: WPS433
    got, cols_of = {}, {}
    for book, _tbl in BOOKS3:
        got[book] = []
        for f in sorted((pq_dir / book).glob("run=*.parquet")) if (pq_dir / book).is_dir() else []:
            table = pq.read_table(str(f))
            cols_of[str(f)] = table.column_names
            got[book] += [((str(f), i), {k: _s(v) for k, v in r.items()}) for i, r in enumerate(table.to_pylist())]
    s_new, c_new = plan(bs, got["Summary"], got["Combined"], got["BasicInfo"])
    changed = {"Summary": len(s_new), "Combined": len(c_new)}
    if not (s_new or c_new):
        return {"lamp": "GREEN", "why": "增量庫(pyarrow)的 Summary 四點 / Combined 主題與摘要都已是新格式", "changed": changed, "partitions": 0}
    if not apply:
        return {"lamp": "YELLOW", "why": "增量庫(pyarrow)有 Summary %d · Combined %d 列待整理(只算沒動 · --apply 才改)" % (len(s_new), len(c_new)), "changed": changed, "partitions": 0}
    folder = _new_folder(base)
    moved = []
    for book, new in (("Summary", s_new), ("Combined", c_new)):
        for fpath in sorted({k[0] for k in new}):
            f = Path(fpath)
            dest = folder / "parquet" / book / f.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(f), str(dest))
            moved.append("%s/%s" % (book, f.name))
            rows = [r for (fp, _i), r in got[book] if fp == fpath]
            rows = [new.get((fpath, i), r) for i, r in enumerate(rows)]
            cols = list(cols_of[fpath]) + [c for c in dict.fromkeys(k for r in rows for k in r) if c not in cols_of[fpath]]
            tmp = f.with_name(f.name + ".tmp")
            pq.write_table(pa.table({c: [_s(r.get(c)) for r in rows] for c in cols}), str(tmp))
            os.replace(str(tmp), str(f))
    man = {"engine": "%s %s" % (DISPLAY_NAME, TAG), "at": V0100.now(), "kind": "summary_tidy", "store_engine": "pyarrow", "store": str(pq_dir), "changed": changed,
           "moved_parquet": moved, "restore": "VRN2_OutputStore_v0104.py restore-fill --folder \"%s\"" % folder}
    (folder / FILL_MANIFEST).write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"lamp": "GREEN", "why": "整理 Summary %d · Combined %d 列(分檔重寫 %d · 原分檔在 %s · 可 restore-fill)" % (len(s_new), len(c_new), len(moved), folder.name),
            "changed": changed, "partitions": len(moved), "folder": str(folder)}


def tidy_summary(v2: Path, output_dir=None, apply: bool = True) -> dict:
    """② 舊列整理(apply=False 只算)。回結果 dict(sync 併進 VRN2_OutputStore_latest.json)。"""
    if os.environ.get("VIA_VRN2_NO_BOOKSOURCE") == "1":
        return {"lamp": "GRAY", "why": "VIA_VRN2_NO_BOOKSOURCE=1 · ⑬a 關掉 · 不整理", "changed": {}, "partitions": 0}
    base = V0102._base(Path(v2), output_dir)
    if not base:
        return {"lamp": "GRAY", "why": "未設定輸出位置 · 沒有增量庫", "changed": {}, "partitions": 0}
    bs = _bs()
    if bs is None:
        return {"lamp": "GRAY", "why": "同夾沒有 VRN2_BookSource v0101 以上(沒有 strip_lead / compose)· 不整理", "changed": {}, "partitions": 0}
    eng, duckdb = V0100._engine()
    db, pq_dir = base / "vrn2_store.duckdb", base / "parquet"
    try:
        if eng == "duckdb" and db.is_file():
            return _tidy_duckdb(duckdb, db, pq_dir, base, bs, apply)
        if pq_dir.is_dir() and eng in ("duckdb", "pyarrow") and not db.is_file():
            return _tidy_pyarrow(pq_dir, base, bs, apply)
        if db.is_file():
            return {"lamp": "YELLOW", "why": "庫是 DuckDB 但這個 Python 沒有 duckdb · 整理不了(交 VCGC 裝 duckdb)", "changed": {}, "partitions": 0}
        return {"lamp": "GRAY", "why": "還沒有增量庫(%s)" % base, "changed": {}, "partitions": 0}
    except Exception as error:  # noqa: BLE001
        return {"lamp": "YELLOW", "why": "整理失敗:%s: %s(庫備份在 %s* 夾 · 可 restore-fill)" % (type(error).__name__, str(error)[:200], TIDY_PREFIX), "changed": {}, "partitions": 0}


# ── sync = v0103 的 sync(清 MOPS · 追加 · 補欄)→ 整理 ─────────────────────────────────────────────────────
def sync(v2: Path, output_dir: Path | None = None, run_id: str | None = None) -> dict:
    rec = _v0103_sync(v2, output_dir, run_id)
    if rec.get("lamp") in ("GREEN", "YELLOW") and rec.get("store_engine") in ("duckdb", "pyarrow"):
        tidy = tidy_summary(v2, output_dir, apply=True)
        rec["summary_tidy"] = tidy
        if any((tidy.get("changed") or {}).values()):
            rec["why"] = ("%s · " % rec["why"] if rec.get("why") else "") + "四點 / 主題與摘要:" + str(tidy.get("why", ""))
        if tidy.get("lamp") in ("YELLOW", "RED") and rec.get("lamp") == "GREEN":
            rec["lamp"] = "YELLOW"
        if rec.get("output_dir"):
            base = Path(rec["output_dir"]) / "VRN2" / "parquet"
            if base.is_dir():
                rec["parquet_files"] = sorted(p.relative_to(base).as_posix() for p in base.rglob("*.parquet"))
        V0100._write_receipt(Path(v2), rec)
    return rec


V0100.sync = V0101.sync = V0102.sync = PRIOR.sync = sync
read_config = V0100.read_config
write_config = V0100.write_config


# ── 自測 ──────────────────────────────────────────────────────────────────────────────────────────────
SUMM_OLD = {"REPORT_DATE": "2026-05-20", "FILENAME": "a.pdf", "TICKER": "9999", "BROKER": "凱基", "TITLE": "- 標題甲",
            "POINT_1": "➢ 營收成長", "POINT_2": "• 目標價 120 元,上漲空間 20%", "POINT_3": "⚫ 毛利率回升", "POINT_4": "下半年出貨"}


def _books(v2: Path, adj_close: str = "100.00", old: bool = True) -> None:
    """舊樣子的冊(v0175 ⑬a 之後:有 BROKER_EN / SOURCE · 四點帶符號 · 主題與摘要 = 標題 · 四點)。"""
    summ = dict(SUMM_OLD, BROKER_EN="KGI", SOURCE="報告")
    topic = " · ".join([SUMM_OLD["TITLE"]] + [SUMM_OLD[k] for k in POINTS])
    comb = {"REPORT_DATE": "2026-05-20", "FILENAME": "a.pdf", "TICKER": "9999", "YFINANCE_TICKER": "9999.TW", "NAME": "示例公司", "BROKER": "凱基", "RATING": "買進",
            "TARGET_PRICE": "120", "TARGET_PRICE(ADJ)": "118.00", "ADJ_CLOSE": adj_close, TOPIC: topic, "STATUS": "x", "BROKER_EN": "KGI", "SOURCE": "報告"}
    basic = {"REPORT_DATE": "2026-05-20", "FILENAME": "a.pdf", "TICKER": "9999", "NAME": "示例公司", "BROKER": "凱基", "TITLE": "- 標題甲", "BROKER_EN": "KGI", "SOURCE": "報告"}
    mc = [{"DATE": "2026-11-03", "TICKER": "9999", "ADJ_CLOSE": adj_close, "SOURCE": "TWSE / TPEX(VDF)+ cnyes FactSet + Yahoo Finance"}]
    data = {"BasicInfo": [basic], "FinancialData": [], "Summary": [summ], "Rejected": [], "Combined": [comb], "FinancialAligned": [], "Deleted": [], "MarketConsensus": mc}
    for k, rows in data.items():
        (v2 / "output" / ("VRN2_%s_latest.json" % k)).write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")


def _wire(new: bool) -> None:
    if new:
        V0101._take, V0101._have_from_rows = _take, _have_from_rows
        V0100.sync = V0101.sync = V0102.sync = PRIOR.sync = sync
    else:
        V0101._take, V0101._have_from_rows = _v0103_take, _v0101_have
        V0100.sync = V0101.sync = V0102.sync = PRIOR.sync = _v0103_sync


def _scenario(eng: str, chk, bs) -> None:
    real_engine = V0100._engine
    if eng == "pyarrow":
        V0100._engine = lambda: ("pyarrow", None)
    try:
        with tempfile.TemporaryDirectory(prefix="vrn2-store104-%s-" % eng) as td:
            root = Path(td)
            v2 = root / "VIA_Reports" / "vrn2"
            (v2 / "output").mkdir(parents=True)
            (v2 / "scope_in").mkdir()
            (v2 / "scope_in" / "a.pdf").write_bytes(b"A")
            out = root / "OneDrive" / "out"
            V0100.write_config(v2, str(out), "selftest")
            _books(v2)
            _wire(False)                                                       # 舊庫:v0103 收(四點帶 ➢ · 舊格式主題)
            try:
                _v0103_sync(v2, None, "r1")
            finally:
                _wire(True)
            n_s, n_c = len(PRIOR._rows_of(out, eng, "Summary")), len(PRIOR._rows_of(out, eng, "Combined"))
            br = bs.apply(v2)                                                  # ⑬a BookSource v0101 改冊
            comb_book = json.loads((v2 / "output" / "VRN2_Combined_latest.json").read_text(encoding="utf-8"))[0]
            summ_book = json.loads((v2 / "output" / "VRN2_Summary_latest.json").read_text(encoding="utf-8"))[0]
            r2 = sync(v2, None, "r2")
            s_rows, c_rows = PRIOR._rows_of(out, eng, "Summary"), PRIOR._rows_of(out, eng, "Combined")
            tidy = r2.get("summary_tidy") or {}
            chk("%s ① 冊被 BookSource v0101 改過(四點去 ➢ · 主題新格式)→ Summary / Combined 0 列追加(仍 %d / %d 列 · 不倍增)· 舊列就地整理 Summary 1 · Combined 1"
                % (eng, n_s, n_c), summ_book["POINT_1"] == "營收成長" and comb_book[TOPIC].startswith("示例公司(9999.TW, 買進) - 標題甲 · ")
                and r2["appended"].get("Summary") == 0 and r2["appended"].get("Combined") == 0 and len(s_rows) == n_s == 1 and len(c_rows) == n_c == 1
                and tidy.get("changed") == {"Summary": 1, "Combined": 1} and tidy.get("lamp") == "GREEN" and br.get("summary_cleanup", {}).get("upside_rows") == 1)
            chk("%s ② 庫裡舊列 = 冊上新列(四點去符號 · 主題與摘要同一段字 · 上漲空間 = 118 ÷ 100 − 1 = 18.0%%)· row_sha 依新規則"
                % eng, _s(s_rows[0]["POINT_1"]) == "營收成長" and _s(s_rows[0]["TITLE"]) == "標題甲" and _s(c_rows[0][TOPIC]) == comb_book[TOPIC]
                and "上漲空間 18.0%" in comb_book[TOPIC] and _s(s_rows[0]["row_sha"]) == row_hash104({k: _s(v) for k, v in s_rows[0].items()}))
            folder = Path(tidy.get("folder", "."))
            man = json.loads((folder / FILL_MANIFEST).read_text(encoding="utf-8")) if (folder / FILL_MANIFEST).is_file() else {}
            chk("%s ③ 整理前先備份(%s)· 受影響分檔 Summary / Combined 重寫 · 收據有 summary_tidy" % (eng, "DuckDB 檔 + SHA-256" if eng == "duckdb" else "原分檔"),
                sorted(man.get("moved_parquet") or []) == ["Combined/run=r1.parquet", "Summary/run=r1.parquet"]
                and (eng != "duckdb" or (man.get("backup_sha256") and (folder / man["backup"]).is_file()))
                and json.loads((v2 / "VRN2_OutputStore_latest.json").read_text(encoding="utf-8")).get("summary_tidy", {}).get("changed") == tidy.get("changed"))
            bs.apply(v2)
            r3 = sync(v2, None, "r3")
            chk("%s ④ 再跑:0 列追加 · 0 列整理 · 不再備份(冪等)" % eng, sum(r3["appended"].values()) == 0 and not any(((r3.get("summary_tidy") or {}).get("changed") or {}).values())
                and len(list((out / "VRN2").glob(TIDY_PREFIX + "*"))) == 1)
            _books(v2, adj_close="110.00")                                     # 每日更新:調整後收盤變了
            bs.apply(v2)
            r4 = sync(v2, None, "r4")
            c4 = PRIOR._rows_of(out, eng, "Combined")
            new4 = [r for r in c4 if _s(r.get("run_id")) == "r4"]
            old4 = [r for r in c4 if _s(r.get("run_id")) == "r1"]
            chk("%s ⑤ 調整後收盤 100 → 110:Combined 追加 1 列(上漲空間 7.3%%)· Summary 0 · 舊列保留那一輪的 18.0%% · 不再整理"
                % eng, r4["appended"].get("Combined") == 1 and r4["appended"].get("Summary") == 0 and len(new4) == 1 and "上漲空間 7.3%" in _s(new4[0][TOPIC])
                and len(old4) == 1 and "上漲空間 18.0%" in _s(old4[0][TOPIC]) and not any(((r4.get("summary_tidy") or {}).get("changed") or {}).values()))
            back = PRIOR.restore_fill(v2, folder)
            s_b = PRIOR._rows_of(out, eng, "Summary")
            chk("%s ⑥ restore-fill --folder <整理夾>:換回整理前(四點又帶 ➢)· 現在的搬到 restore_replaced/(不刪)" % eng,
                back["lamp"] == "GREEN" and any((folder / "restore_replaced").rglob("*")) and any(_s(r.get("POINT_1")).startswith("➢") for r in s_b))
    finally:
        V0100._engine = real_engine


def selftest() -> int:
    bad = []

    def chk(label, cond):
        print(("[PASS] " if cond else "[FAIL] ") + label, flush=True)
        if not cond:
            bad.append(label)
    _wire(False)
    try:
        rc = PRIOR.selftest()                                                   # 前版自測照前版自己的接線跑
    finally:
        _wire(True)
    chk("⓪ v0103 自測(含 v0102 / v0101 / v0100 的接線)照過", rc == 0)
    bs = _bs()
    a = {"TITLE": "- 標題", "POINT_1": "➢ a", "POINT_2": "• b"}
    chk("⑦ 薄尾:v0101 的 _take / _have_from_rows 與各版 sync 都指本版 · Summary 列去符號後同雜湊 · 主題與摘要不算 · BasicInfo 的 TITLE(沒有四點欄)照算",
        V0101._take is _take and V0101._have_from_rows is _have_from_rows and V0100.sync is sync and PRIOR.sync is sync and V0102.sync is sync
        and (bs is None or (row_hash104(a) == row_hash104({"TITLE": "標題", "POINT_1": "a", "POINT_2": "b"})
                            and row_hash104({"TITLE": "- 標題"}) != row_hash104({"TITLE": "標題"})))
        and row_hash104({"A": "1", TOPIC: "x", "SOURCE": "報告"}) == row_hash104({"A": "1", TOPIC: "y"}) and row_hash104({"A": "1"}) != row_hash104({"A": "2"}))
    if bs is None:
        print("[SKIP] 同夾沒有 VRN2_BookSource v0101 以上 · 情境 ①–⑥ 不驗", flush=True)
        engines = []
    else:
        eng, _mod = V0100._engine()
        engines = ["duckdb"] if eng == "duckdb" else []
        try:
            import pyarrow.parquet  # noqa: F401,WPS433
        except ImportError as error:
            print("[SKIP] 這個 Python 的 pyarrow 用不了(%s)· 情境 ①–⑥ 要 pyarrow 讀分檔 · 不驗" % type(error).__name__, flush=True)
            engines = []
        else:
            engines.append("pyarrow")
    for e in engines:
        _scenario(e, chk, bs)
    os.environ["VIA_VRN2_NO_BOOKSOURCE"] = "1"
    try:
        chk("⑧ VIA_VRN2_NO_BOOKSOURCE=1 → 不整理(GRAY)", tidy_summary(Path(tempfile.gettempdir()) / "vrn2-none")["lamp"] == "GRAY")
    finally:
        os.environ.pop("VIA_VRN2_NO_BOOKSOURCE", None)
    print("[%s] %s %s --selftest · 引擎 %s · 不過 %d" % ("PASS" if not bad else "FAIL", DISPLAY_NAME, TAG, "+".join(engines) or "none", len(bad)), flush=True)
    return 0 if not bad else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    def opt(k, d=None):
        return argv[argv.index(k) + 1] if k in argv and argv.index(k) + 1 < len(argv) else d
    if "--selftest" in argv:
        return selftest()
    verb = argv[0] if argv else ""
    if verb == "tidy-summary":
        v2 = Path(opt("--v2") or (Path(os.environ["VIA_ROOT"]) / "VIA_Reports" / "vrn2" if os.environ.get("VIA_ROOT") else HERE.parent.parent / "VIA_Reports" / "vrn2"))
        r = tidy_summary(v2, opt("--output-dir"), apply="--apply" in argv)
        print("[%s] %s %s · %s · %s" % (r.get("lamp"), DISPLAY_NAME, TAG, verb, r.get("why")), flush=True)
        return 0 if r.get("lamp") in ("GREEN", "YELLOW", "GRAY") else 1
    return PRIOR.main(argv)


if __name__ == "__main__":
    sys.exit(main())
