#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_OutputStore v0101 — v0100 薄尾(v0100 留著一字不改):長線 Parquet 庫多收三本新冊 + 依「冊 × 原檔」補缺。

操作員令(2026-10-29):「左邊要有一格輸出檔案夾來存長線資料庫 · 增量維護一律用 PARQUET 儲存」。
v0146 的 ⑥f / ⑬b 產出 Combined(共識合併)· FinancialAligned(歷史對齊)· Deleted(刪除區),但 v0100 只收四本冊,而且只追加「catalog 沒見過的原檔」的列
→ 桌機已知 52 份,新冊永遠 0 列。v0101:
  ① BOOKS = 四本 + Combined · FinancialAligned · Deleted(鏡像到 <輸出夾>/VRN2/latest 也一起)。
  ② 追加規則從「原檔是新的」改成「這本冊裡還沒有 (原檔 SHA-256, 列內容雜湊) 這一列」:同內容再跑 0 列;新冊把已知原檔補進來一次;
     已知原檔的列內容變了(例:Combined 的還原價 / 共識隔天更新、擷取改版)→ 只追加變了的列(帶 run_id · 舊列保留 · 同名不同內容不覆寫)。
     列內容雜湊 = 扁平後非空欄位(不含 run_id / file_sha / row_sha)排序後的 SHA-256 前 32 碼 → 欄位 row_sha;v0100 的舊庫沒有 row_sha 時從既有列重算。
     catalog(新檔 / 已知檔)照舊記;收據多 backfilled{冊: 已知原檔追加的列數}。DuckDB 正式路徑與 pyarrow 備援兩邊同規則。
動詞同 v0100:sync [--v2] [--output-dir] · --selftest
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

TAG = "v0101"
DISPLAY_NAME = "VRN2_OutputStore"
PRIOR_NAME = "VRN2_OutputStore_v0100.py"
HERE = Path(__file__).resolve().parent
NEW_BOOKS = ("Combined", "FinancialAligned", "Deleted")


def _prior():
    for path in (HERE / PRIOR_NAME, HERE.parent / "v144" / "new" / PRIOR_NAME):
        if path.is_file():
            spec = importlib.util.spec_from_file_location("vrn2_outputstore_prior_v0100", path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            return module
    raise FileNotFoundError("前版 %s 不在 %s" % (PRIOR_NAME, HERE))


PRIOR = _prior()
for _name in dir(PRIOR):
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = getattr(PRIOR, _name)
BOOKS = tuple(PRIOR.BOOKS) + tuple(b for b in NEW_BOOKS if b not in PRIOR.BOOKS)
PRIOR.BOOKS = BOOKS                                  # v0100 的 mirror() / sync() 讀它自己 globals 的 BOOKS
PRIOR.TAG = TAG + "(v0100 薄尾)"


META = ("run_id", "file_sha", "row_sha")


def row_hash(flat: dict) -> str:
    """列內容雜湊:非空欄位(不含 META)排序後 JSON 的 SHA-256 前 32 碼(空值與沒有這欄視為相同)。"""
    body = {k: v for k, v in flat.items() if k not in META and v not in (None, "")}
    return hashlib.sha256(json.dumps(body, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:32]


def _take(rows: list, shas: dict, have: set, run_id: str) -> list:
    """這本冊裡還沒有的 (原檔 SHA, 列內容雜湊) → 它的列(扁平字串 · 帶 run_id / file_sha / row_sha)· 同一輪重複的列只收一次。"""
    out, seen = [], set()
    for r in rows:
        sha = shas.get(r.get("FILENAME", ""), "")
        if not sha:
            continue
        flat = PRIOR._flat(r)
        key = (sha, row_hash(flat))
        if key in have or key in seen:
            continue
        seen.add(key)
        out.append(dict(flat, run_id=run_id, file_sha=sha, row_sha=key[1]))
    return out


def _have_from_rows(rows) -> set:
    """既有列 → {(file_sha, row_sha)};沒有 row_sha(v0100 的舊庫)就重算。"""
    have = set()
    for r in rows:
        r = {k: ("" if v is None else str(v)) for k, v in r.items()}
        have.add((r.get("file_sha", ""), r.get("row_sha") or row_hash(r)))
    return have


def _append_duckdb(duckdb, db: Path, pq_dir: Path, run_id: str, books_rows: dict, shas: dict) -> dict:
    con = duckdb.connect(str(db))
    try:
        con.execute("CREATE TABLE IF NOT EXISTS catalog(file_sha VARCHAR PRIMARY KEY, filename VARCHAR, first_run VARCHAR, last_run VARCHAR, runs INTEGER)")
        known = {r[0] for r in con.execute("SELECT file_sha FROM catalog").fetchall()}
        new_files = sorted(n for n, s in shas.items() if s not in known)
        seen_files = sorted(n for n, s in shas.items() if s in known)
        for n in seen_files:
            con.execute("UPDATE catalog SET last_run=?, runs=runs+1 WHERE file_sha=?", [run_id, shas[n]])
        for n in new_files:
            con.execute("INSERT INTO catalog VALUES (?, ?, ?, ?, 1)", [shas[n], n, run_id, run_id])
        appended, backfilled, totals = {}, {}, {}
        new_shas = {shas[n] for n in new_files}
        for book, rows in books_rows.items():
            tbl = "book_" + book.lower()
            exists = con.execute("SELECT count(*) FROM information_schema.tables WHERE table_name=?", [tbl]).fetchone()[0]
            have = set()
            if exists:
                cur = con.execute("SELECT * FROM %s" % tbl)
                names = [d[0] for d in cur.description]
                have = _have_from_rows(dict(zip(names, row)) for row in cur.fetchall())
            take = _take(rows, shas, have, run_id)
            appended[book] = len(take)
            backfilled[book] = sum(1 for r in take if r["file_sha"] not in new_shas)
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
        pq_dir.mkdir(parents=True, exist_ok=True)
        con.execute("COPY (SELECT * FROM catalog) TO '%s' (FORMAT PARQUET)" % str(pq_dir / "catalog.parquet").replace("'", "''"))
        cat_n = con.execute("SELECT count(*) FROM catalog").fetchone()[0]
    finally:
        con.close()
    return {"new_files": new_files, "known_files": seen_files, "appended": appended, "backfilled": backfilled, "totals": totals, "catalog_files": cat_n}


def _append_pyarrow(db_dir: Path, pq_dir: Path, run_id: str, books_rows: dict, shas: dict) -> dict:
    import pyarrow as pa  # noqa: WPS433
    import pyarrow.parquet as pq  # noqa: WPS433
    cat_p = db_dir / "catalog.json"
    try:
        cat = json.loads(cat_p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        cat = {}
    new_files = sorted(n for n, s in shas.items() if s not in cat)
    seen_files = sorted(n for n, s in shas.items() if s in cat)
    for n in seen_files:
        cat[shas[n]]["last_run"] = run_id
        cat[shas[n]]["runs"] = int(cat[shas[n]].get("runs", 1)) + 1
    for n in new_files:
        cat[shas[n]] = {"filename": n, "first_run": run_id, "last_run": run_id, "runs": 1}
    cat_p.parent.mkdir(parents=True, exist_ok=True)
    cat_p.write_text(json.dumps(cat, ensure_ascii=False, indent=1), encoding="utf-8")
    new_shas = {shas[n] for n in new_files}
    appended, backfilled, totals = {}, {}, {}
    for book, rows in books_rows.items():
        out = pq_dir / book
        have = set()
        if out.is_dir():
            for f in out.glob("run=*.parquet"):
                try:
                    have |= _have_from_rows(pq.read_table(str(f)).to_pylist())
                except Exception:  # noqa: BLE001
                    continue
        take = _take(rows, shas, have, run_id)
        appended[book] = len(take)
        backfilled[book] = sum(1 for r in take if r["file_sha"] not in new_shas)
        if take:
            out.mkdir(parents=True, exist_ok=True)
            cols = list(dict.fromkeys(k for r in take for k in r))
            pq.write_table(pa.table({c: [r.get(c, "") for r in take] for c in cols}), str(out / ("run=%s.parquet" % run_id)))
        totals[book] = sum(pq.read_metadata(str(f)).num_rows for f in out.glob("run=*.parquet")) if out.is_dir() else 0
    pq_dir.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.table({"file_sha": list(cat.keys()), "filename": [v["filename"] for v in cat.values()], "first_run": [v["first_run"] for v in cat.values()],
                             "last_run": [v["last_run"] for v in cat.values()], "runs": [int(v["runs"]) for v in cat.values()]}), str(pq_dir / "catalog.parquet"))
    return {"new_files": new_files, "known_files": seen_files, "appended": appended, "backfilled": backfilled, "totals": totals, "catalog_files": len(cat)}


PRIOR._append_duckdb = _append_duckdb
PRIOR._append_pyarrow = _append_pyarrow
sync = PRIOR.sync
read_config = PRIOR.read_config
write_config = PRIOR.write_config


def selftest() -> int:
    bad = []

    def chk(label, cond):
        print(("[PASS] " if cond else "[FAIL] ") + label, flush=True)
        if not cond:
            bad.append(label)

    eng, _mod = PRIOR._engine()
    chk("① 薄尾:v0100 載入 · BOOKS 七本(四本 + Combined / FinancialAligned / Deleted)· v0100 的 sync 走本版的追加函式", BOOKS[-3:] == NEW_BOOKS and PRIOR.BOOKS == BOOKS and PRIOR._append_pyarrow is _append_pyarrow and PRIOR._append_duckdb is _append_duckdb)
    if eng == "none":
        print("[SKIP] 沒有 duckdb / pyarrow · 只驗 ①", flush=True)
        print("[%s] %s %s --selftest · 不過 %d" % ("PASS" if not bad else "FAIL", DISPLAY_NAME, TAG, len(bad)))
        return 0 if not bad else 1
    with tempfile.TemporaryDirectory(prefix="vrn2-store101-") as td:
        root = Path(td)
        v2 = root / "VIA_Reports" / "vrn2"
        (v2 / "output").mkdir(parents=True)
        (v2 / "scope_in").mkdir()
        for n, b in (("a.pdf", b"A"), ("b.pdf", b"B")):
            (v2 / "scope_in" / n).write_bytes(b)

        def books(with_new: bool):
            data = {"BasicInfo": [{"FILENAME": "a.pdf", "TICKER": "2330"}, {"FILENAME": "b.pdf", "TICKER": "2454"}],
                    "FinancialData": [{"FILENAME": "a.pdf", "ITEM": "Revenue", "PERIOD": "2025A", "VALUE": "1,000"}], "Summary": [], "Rejected": []}
            if with_new:
                data["Combined"] = [{"FILENAME": "a.pdf", "TARGET_PRICE": "100", "TARGET_PRICE(ADJ)": "98.00", "TOPIC & SUMMARY": "t", "2026_DILUTED_EPS_FACTSET": "5.00"}, {"FILENAME": "b.pdf", "TARGET_PRICE": ""}]
                data["FinancialAligned"] = [{"FILENAME": "a.pdf", "ITEM": "Revenue", "VALUE_FINAL": 1000.0, "VALUE_SOURCE": "HISTORY"}]
                data["Deleted"] = [{"FILENAME": "a.pdf", "ITEM": "Net income", "DELETED_REASON": "差 > 3%"}]
            for k, rows in data.items():
                (v2 / "output" / ("VRN2_%s_latest.json" % k)).write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
        out = root / "OneDrive" / "out"
        books(False)
        r1 = sync(v2, out, "r1")
        chk("② 第一輪(只有舊四冊):新檔 2 · BasicInfo 2 · FinancialData 1 · 新冊 0", r1["lamp"] in ("GREEN", "YELLOW") and len(r1["new_files"]) == 2 and r1["appended"]["BasicInfo"] == 2 and r1["appended"]["FinancialData"] == 1 and r1["appended"].get("Combined", 0) == 0)
        books(True)
        r2 = sync(v2, out, "r2")
        chk("③ 第二輪(原檔都已知 · 新冊出現):新檔 0 / 已知 2 · 舊冊 0 列 · Combined 補 2 · FinancialAligned 補 1 · Deleted 補 1(backfilled)",
            len(r2["new_files"]) == 0 and len(r2["known_files"]) == 2 and r2["appended"]["BasicInfo"] == 0 and r2["appended"]["Combined"] == 2 and r2["backfilled"]["Combined"] == 2 and r2["appended"]["FinancialAligned"] == 1 and r2["appended"]["Deleted"] == 1)
        r3 = sync(v2, out, "r3")
        chk("④ 第三輪同輸入:全部 0 列(冪等)· 累計 Combined 2", sum(r3["appended"].values()) == 0 and r3["totals"]["Combined"] == 2)
        comb = json.loads((v2 / "output" / "VRN2_Combined_latest.json").read_text(encoding="utf-8"))
        comb[0]["TARGET_PRICE(ADJ)"] = "99.50"
        (v2 / "output" / "VRN2_Combined_latest.json").write_text(json.dumps(comb, ensure_ascii=False), encoding="utf-8")
        r3b = sync(v2, out, "r3b")
        r3c = sync(v2, out, "r3c")
        chk("④b 已知原檔的列內容變了(Combined 調整後目標價隔天更新)→ 只追加那 1 列 · 舊列保留(累計 3)· 再跑 0 列", r3b["appended"]["Combined"] == 1 and r3b["backfilled"]["Combined"] == 1 and sum(v for k, v in r3b["appended"].items() if k != "Combined") == 0 and r3b["totals"]["Combined"] == 3 and sum(r3c["appended"].values()) == 0)
        chk("⑤ 鏡像:latest 夾有 Combined / FinancialAligned / Deleted json · parquet 有 Combined/run=r2", all((out / "VRN2" / "latest" / ("VRN2_%s_latest.json" % b)).is_file() for b in NEW_BOOKS) and (out / "VRN2" / "parquet" / "Combined" / "run=r2.parquet").is_file())
        (v2 / "scope_in" / "a.pdf").write_bytes(b"A2")
        r4 = sync(v2, out, "r4")
        chk("⑥ 原檔內容變了(同名不同 sha)→ 當新檔:a.pdf 的各冊列再追加一次 · 舊列保留", "a.pdf" in r4["new_files"] and r4["appended"]["BasicInfo"] == 1 and r4["appended"]["Combined"] == 1 and r4["totals"]["BasicInfo"] == 3)
        chk("⑦ 列內容雜湊:空值與沒有這欄相同 · META 欄不算 · 欄序不影響", row_hash({"A": "1", "B": ""}) == row_hash({"A": "1"}) == row_hash({"A": "1", "run_id": "x", "file_sha": "y"}) and row_hash({"A": "1", "C": "2"}) == row_hash({"C": "2", "A": "1"}) and row_hash({"A": "1"}) != row_hash({"A": "2"}))
    print("[%s] %s %s --selftest · 引擎 %s · 8 項 · 不過 %d" % ("PASS" if not bad else "FAIL", DISPLAY_NAME, TAG, eng, len(bad)), flush=True)
    return 0 if not bad else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        return selftest()
    return PRIOR.main(argv)


if __name__ == "__main__":
    sys.exit(main())
