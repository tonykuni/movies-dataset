#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_OutputStore v0100 — VRN-2 輸出位置 + 增量 Parquet 庫(操作員 2026-10-29:「輸出位置可用 Windows I/O 拖曳式或連接雲端 · 輸出 Parquet 增量擷取 · 增量擷取用 DuckDB 管理」)。
輸出位置 = U/I「選擇輸出夾」(vrn2://pick?kind=outdir · Windows 對話框)寫的 VIA_Reports/vrn2/VRN2_Output_Config.json;
選 OneDrive / Google Drive / Dropbox 的同步夾 = 連接雲端(本機寫、同步軟體上傳;本版不直接打雲端 API)。
做的事(只讀本輪輸出冊 · 只寫輸出夾與 VIA_Reports/vrn2 的收據):
  ① 鏡像:四本輸出冊(json / csv / parquet)+ Workbench 頁 + 收尾 / 完成 / 冪等 / 四點原文收據 → <輸出夾>/VRN2/latest/
  ② 增量庫:<輸出夾>/VRN2/vrn2_store.duckdb(DuckDB)—— catalog(檔名 · SHA-256 · 首見 / 末見輪次)+ 四本冊的列(帶 run_id · file_sha);
     只追加「這一輪才出現的檔(SHA-256 不在 catalog)」的列 = 增量擷取;同檔同 SHA 再跑一輪 → 0 列新增(冪等);檔改了(SHA 變)→ 當新檔追加、舊列保留
     匯出 Parquet 分割:<輸出夾>/VRN2/parquet/<冊>/run=<run_id>.parquet + catalog.parquet(DuckDB 原生寫 · 不需 pandas)
     沒有 duckdb 套件 → 備援:pyarrow 寫同一套 parquet 分割 + catalog.json(收據 engine = pyarrow;功能同,少 SQL 查詢)
  收據:VIA_Reports/vrn2/VRN2_OutputStore_latest.json(output_dir · engine · run_id · 新檔 / 已知檔 · 各冊追加列 · parquet 清單)
  --selftest(兩個引擎都驗:有 duckdb 驗 duckdb,沒有驗 pyarrow;都沒有 → 跳過並說明)
"""
from __future__ import annotations
import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path
TAG = "v0100"
DISPLAY_NAME = "VRN2_OutputStore"
HERE = Path(__file__).resolve().parent
CONFIG_NAME = "VRN2_Output_Config.json"
RECEIPT_NAME = "VRN2_OutputStore_latest.json"
BOOKS = ("BasicInfo", "FinancialData", "Summary", "Rejected")
MIRROR = ("VRN2_Workbench_latest.html", "VRN2_Completion_latest.json", "IDEMPOTENCE_latest.json", "VRN2_VerbatimVerify_latest.json", "VRN2_Acceptance_latest.json", "VRN2_Input_latest.json")
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass


def say(line: str) -> None:
    print(line, flush=True)


def now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_config(v2: Path) -> dict:
    try:
        return json.loads((Path(v2) / CONFIG_NAME).read_text(encoding="utf-8-sig"))
    except Exception:  # noqa: BLE001
        return {}


def write_config(v2: Path, output_dir: str, how: str) -> dict:
    cfg = {"output_dir": str(output_dir), "how": how, "ts": now(), "cloud_hint": _cloud_hint(output_dir)}
    Path(v2).mkdir(parents=True, exist_ok=True)
    (Path(v2) / CONFIG_NAME).write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")
    return cfg


def _cloud_hint(path) -> str:
    s = str(path).lower()
    for k, name in (("onedrive", "OneDrive"), ("google drive", "Google Drive"), ("googledrive", "Google Drive"), ("dropbox", "Dropbox"), ("icloud", "iCloud"), ("box\\", "Box")):
        if k in s:
            return "%s 同步夾(本機寫入 · 由同步軟體上雲)" % name
    return "本機夾(要上雲就選 OneDrive / Google Drive / Dropbox 的同步夾)"


def _engine():
    try:
        import duckdb  # noqa: WPS433
        return "duckdb", duckdb
    except Exception:  # noqa: BLE001
        pass
    try:
        import pyarrow  # noqa: WPS433,F401
        import pyarrow.parquet  # noqa: WPS433,F401
        return "pyarrow", None
    except Exception:  # noqa: BLE001
        return "none", None


def _rows(v2: Path, book: str) -> list:
    p = Path(v2) / "output" / ("VRN2_%s_latest.json" % book)
    try:
        rows = json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:  # noqa: BLE001
        return []
    return [r for r in rows if isinstance(r, dict)] if isinstance(rows, list) else []


def _file_shas(v2: Path, names: set) -> dict:
    """FILENAME → SHA-256(scope_in 裡的原檔;找不到 → 以檔名雜湊代替並標 nofile)。"""
    out = {}
    scope = Path(v2) / "scope_in"
    for n in names:
        p = scope / n
        if p.is_file():
            out[n] = sha256_file(p)
        else:
            out[n] = "nofile:" + hashlib.sha256(n.encode("utf-8")).hexdigest()[:48]
    return out


def _flat(r: dict) -> dict:
    return {k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else ("" if v is None else str(v))) for k, v in r.items()}


def mirror(v2: Path, dest: Path) -> list:
    dest.mkdir(parents=True, exist_ok=True)
    done = []
    for book in BOOKS:
        for ext in ("json", "csv", "parquet"):
            p = Path(v2) / "output" / ("VRN2_%s_latest.%s" % (book, ext))
            if p.is_file():
                shutil.copy2(str(p), str(dest / p.name))
                done.append(p.name)
    for n in MIRROR:
        p = Path(v2) / n
        if p.is_file():
            shutil.copy2(str(p), str(dest / n))
            done.append(n)
    return done


def _append_duckdb(duckdb, db: Path, pq_dir: Path, run_id: str, books_rows: dict, shas: dict) -> dict:
    con = duckdb.connect(str(db))
    con.execute("CREATE TABLE IF NOT EXISTS catalog(file_sha VARCHAR PRIMARY KEY, filename VARCHAR, first_run VARCHAR, last_run VARCHAR, runs INTEGER)")
    known = {r[0] for r in con.execute("SELECT file_sha FROM catalog").fetchall()}
    new_files = sorted(n for n, s in shas.items() if s not in known)
    seen_files = sorted(n for n, s in shas.items() if s in known)
    for n in seen_files:
        con.execute("UPDATE catalog SET last_run=?, runs=runs+1 WHERE file_sha=?", [run_id, shas[n]])
    for n in new_files:
        con.execute("INSERT INTO catalog VALUES (?, ?, ?, ?, 1)", [shas[n], n, run_id, run_id])
    appended = {}
    new_shas = {shas[n] for n in new_files}
    for book, rows in books_rows.items():
        tbl = "book_" + book.lower()
        take = [dict(_flat(r), run_id=run_id, file_sha=shas.get(r.get("FILENAME", ""), "")) for r in rows if shas.get(r.get("FILENAME", ""), "") in new_shas]
        appended[book] = len(take)
        if not take:
            continue
        cols = list(dict.fromkeys(k for r in take for k in r))
        exists = con.execute("SELECT count(*) FROM information_schema.tables WHERE table_name=?", [tbl]).fetchone()[0]
        if not exists:
            con.execute("CREATE TABLE %s(%s)" % (tbl, ", ".join('"%s" VARCHAR' % c for c in cols)))
        else:
            have = {r[0] for r in con.execute("SELECT column_name FROM information_schema.columns WHERE table_name=?", [tbl]).fetchall()}
            for c in cols:
                if c not in have:
                    con.execute('ALTER TABLE %s ADD COLUMN "%s" VARCHAR' % (tbl, c))
        con.executemany("INSERT INTO %s(%s) VALUES (%s)" % (tbl, ", ".join('"%s"' % c for c in cols), ", ".join("?" * len(cols))), [[r.get(c, "") for c in cols] for r in take])
        out = pq_dir / book
        out.mkdir(parents=True, exist_ok=True)
        con.execute("COPY (SELECT * FROM %s WHERE run_id=?) TO '%s' (FORMAT PARQUET)" % (tbl, str(out / ("run=%s.parquet" % run_id)).replace("'", "''")), [run_id])
    con.execute("COPY (SELECT * FROM catalog) TO '%s' (FORMAT PARQUET)" % str(pq_dir / "catalog.parquet").replace("'", "''"))
    totals = {}
    for book in books_rows:
        tbl = "book_" + book.lower()
        if con.execute("SELECT count(*) FROM information_schema.tables WHERE table_name=?", [tbl]).fetchone()[0]:
            totals[book] = con.execute("SELECT count(*) FROM %s" % tbl).fetchone()[0]
    cat_n = con.execute("SELECT count(*) FROM catalog").fetchone()[0]
    con.close()
    return {"new_files": new_files, "known_files": seen_files, "appended": appended, "totals": totals, "catalog_files": cat_n}


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
    appended, totals = {}, {}
    for book, rows in books_rows.items():
        take = [dict(_flat(r), run_id=run_id, file_sha=shas.get(r.get("FILENAME", ""), "")) for r in rows if shas.get(r.get("FILENAME", ""), "") in new_shas]
        appended[book] = len(take)
        out = pq_dir / book
        if take:
            out.mkdir(parents=True, exist_ok=True)
            cols = list(dict.fromkeys(k for r in take for k in r))
            pq.write_table(pa.table({c: [r.get(c, "") for r in take] for c in cols}), str(out / ("run=%s.parquet" % run_id)))
        totals[book] = sum(pq.read_metadata(str(f)).num_rows for f in out.glob("run=*.parquet")) if out.is_dir() else 0
    pq.write_table(pa.table({"file_sha": list(cat.keys()), "filename": [v["filename"] for v in cat.values()], "first_run": [v["first_run"] for v in cat.values()],
                             "last_run": [v["last_run"] for v in cat.values()], "runs": [int(v["runs"]) for v in cat.values()]}), str(pq_dir / "catalog.parquet"))
    return {"new_files": new_files, "known_files": seen_files, "appended": appended, "totals": totals, "catalog_files": len(cat)}


def sync(v2: Path, output_dir: Path | None = None, run_id: str | None = None) -> dict:
    v2 = Path(v2)
    cfg = read_config(v2)
    out_dir = Path(output_dir) if output_dir else (Path(cfg["output_dir"]) if cfg.get("output_dir") else None)
    rec = {"engine": "%s %s" % (DISPLAY_NAME, TAG), "verb": "sync", "at": now(), "run_id": run_id or datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}
    if not out_dir:
        rec.update(lamp="GRAY", why="未設定輸出位置(U/I「選擇輸出夾」或 --output-dir)· 輸出留在 %s" % (v2 / "output"))
        _write_receipt(v2, rec)
        return rec
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        rec.update(lamp="RED", why="輸出夾開不了:%s %s" % (out_dir, exc.__class__.__name__))
        _write_receipt(v2, rec)
        return rec
    rec["output_dir"] = str(out_dir)
    rec["cloud_hint"] = cfg.get("cloud_hint") or _cloud_hint(out_dir)
    base = out_dir / "VRN2"
    rec["mirrored"] = mirror(v2, base / "latest")
    books_rows = {b: _rows(v2, b) for b in BOOKS}
    names = {r.get("FILENAME", "") for rows in books_rows.values() for r in rows if r.get("FILENAME")}
    shas = _file_shas(v2, names)
    eng, duckdb = _engine()
    rec["store_engine"] = eng
    pq_dir = base / "parquet"
    try:
        if eng == "duckdb":
            rec["store"] = str(base / "vrn2_store.duckdb")
            rec.update(_append_duckdb(duckdb, base / "vrn2_store.duckdb", pq_dir, rec["run_id"], books_rows, shas))
        elif eng == "pyarrow":
            rec["store"] = str(base / "store_pyarrow")
            rec.update(_append_pyarrow(base / "store_pyarrow", pq_dir, rec["run_id"], books_rows, shas))
        else:
            rec.update(lamp="YELLOW", why="沒有 duckdb 也沒有 pyarrow:只鏡像,沒有增量庫", store="", new_files=[], known_files=[], appended={}, totals={}, catalog_files=0)
    except Exception as exc:  # noqa: BLE001
        rec.update(lamp="RED", why="增量庫寫入失敗:%s: %s" % (type(exc).__name__, str(exc)[:200]))
        _write_receipt(v2, rec)
        return rec
    rec["parquet_files"] = sorted(p.relative_to(pq_dir).as_posix() for p in pq_dir.rglob("*.parquet")) if pq_dir.is_dir() else []
    if "lamp" not in rec:
        rec["lamp"] = "GREEN" if eng == "duckdb" else "YELLOW"
        if eng == "pyarrow":
            rec["why"] = "沒有 duckdb 套件 → pyarrow 備援(功能同 · 沒有 SQL 查詢;桌機裝 duckdb 即走正式路徑)"
    _write_receipt(v2, rec)
    return rec


def _write_receipt(v2: Path, rec: dict) -> None:
    try:
        Path(v2).mkdir(parents=True, exist_ok=True)
        (Path(v2) / RECEIPT_NAME).write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        pass


def print_result(r: dict) -> None:
    if r.get("lamp") in ("GRAY", "RED") or "store_engine" not in r:
        say("[計] %s · %s · %s" % (r["engine"], r["lamp"], r.get("why", "")))
        return
    ap = r.get("appended") or {}
    say("[計] %s · %s · 輸出夾 %s(%s)· 鏡像 %d 檔 · 增量庫 %s(%s)· 本輪新檔 %d · 已知檔 %d · 追加列 %s · 累計 %s · parquet %d 檔%s" % (
        r["engine"], r["lamp"], r["output_dir"], r.get("cloud_hint", ""), len(r.get("mirrored") or []), r.get("store_engine"), r.get("store", ""), len(r.get("new_files") or []), len(r.get("known_files") or []),
        " / ".join("%s %d" % (k, v) for k, v in ap.items()), " / ".join("%s %d" % (k, v) for k, v in (r.get("totals") or {}).items()), len(r.get("parquet_files") or []), (" · " + r["why"]) if r.get("why") else ""))


# ===== selftest =====
def _fixture(v2: Path, files: dict) -> None:
    (v2 / "output").mkdir(parents=True, exist_ok=True)
    (v2 / "scope_in").mkdir(parents=True, exist_ok=True)
    for n, body in files.items():
        (v2 / "scope_in" / n).write_bytes(body)
    basic = [{"FILENAME": n, "TICKER": "23%02d" % i, "NAME": "公司%d" % i, "RATING": {"v": "BUY"}} for i, n in enumerate(files)]
    fin = [{"FILENAME": n, "METRIC": "Revenue", "PERIOD": "2025", "VALUE": "%d" % (100 + i), "EXTRA": None} for i, n in enumerate(files) for _ in range(2)]
    summ = [{"FILENAME": n, "TITLE": "T", "POINT_1": "p1"} for n in files]
    for book, rows in (("BasicInfo", basic), ("FinancialData", fin), ("Summary", summ), ("Rejected", [])):
        (v2 / "output" / ("VRN2_%s_latest.json" % book)).write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
        (v2 / "output" / ("VRN2_%s_latest.csv" % book)).write_text("x\n", encoding="utf-8")
    (v2 / "VRN2_Workbench_latest.html").write_text("<html></html>", encoding="utf-8")
    (v2 / "VRN2_Completion_latest.json").write_text("{}", encoding="utf-8")


def selftest() -> int:
    oks, fails = [], []

    def chk(label, cond):
        (oks if cond else fails).append(label)
        say("  [%s] %s" % ("OK" if cond else "FAIL", label))
    eng, _ = _engine()
    say("  引擎:%s" % eng)
    if eng == "none":
        say("[計] %s %s --selftest · 跳過(沒有 duckdb / pyarrow)" % (DISPLAY_NAME, TAG))
        return 0
    with tempfile.TemporaryDirectory() as td:
        v2 = Path(td) / "VIA_Reports" / "vrn2"
        out = Path(td) / "OneDrive" / "VRN2_out"
        _fixture(v2, {"a.pdf": b"AAA", "b.pdf": b"BBB"})
        r0 = sync(v2)
        chk("① 未設定輸出位置 → GRAY 不動作 · 收據仍寫", r0["lamp"] == "GRAY" and (v2 / RECEIPT_NAME).is_file())
        cfg = write_config(v2, str(out), "測試")
        chk("② 設定冊:路徑 · 雲端判讀(OneDrive 同步夾)", cfg["output_dir"] == str(out) and "OneDrive" in cfg["cloud_hint"])
        r1 = sync(v2, run_id="r1")
        chk("③ 第一輪:鏡像 冊 + 收據 · 2 新檔 · 追加 BasicInfo 2 / FinancialData 4 / Summary 2 · catalog 2", r1["lamp"] in ("GREEN", "YELLOW") and r1["store_engine"] == eng and len(r1["new_files"]) == 2 and r1["appended"] == {"BasicInfo": 2, "FinancialData": 4, "Summary": 2, "Rejected": 0}
            and r1["catalog_files"] == 2 and (out / "VRN2" / "latest" / "VRN2_BasicInfo_latest.json").is_file() and (out / "VRN2" / "latest" / "VRN2_Workbench_latest.html").is_file())
        chk("③b parquet 分割:BasicInfo/run=r1 · FinancialData/run=r1 · Summary/run=r1 · catalog", {"BasicInfo/run=r1.parquet", "FinancialData/run=r1.parquet", "Summary/run=r1.parquet", "catalog.parquet"} <= set(r1["parquet_files"]))
        r2 = sync(v2, run_id="r2")
        chk("④ 同檔同 SHA 再跑一輪:新檔 0 · 追加 0(冪等)· catalog 仍 2 · 累計不變", r2["new_files"] == [] and sum(r2["appended"].values()) == 0 and r2["catalog_files"] == 2 and r2["totals"] == r1["totals"])
        (v2 / "scope_in" / "b.pdf").write_bytes(b"BBB2")
        _fixture(v2, {"a.pdf": b"AAA", "b.pdf": b"BBB2", "c.pdf": b"CCC"})
        r3 = sync(v2, run_id="r3")
        chk("⑤ b 改了(SHA 變)+ 新檔 c:新檔 2(b 當新檔)· a 已知 · 追加 BasicInfo 2 · 舊列保留 累計 BasicInfo 4", sorted(r3["new_files"]) == ["b.pdf", "c.pdf"] and r3["known_files"] == ["a.pdf"] and r3["appended"]["BasicInfo"] == 2 and r3["totals"]["BasicInfo"] == 4 and r3["catalog_files"] == 4)
        if eng == "duckdb":
            import duckdb  # noqa: WPS433
            con = duckdb.connect(str(out / "VRN2" / "vrn2_store.duckdb"), read_only=True)
            n = con.execute("SELECT count(*) FROM book_financialdata WHERE run_id='r3'").fetchone()[0]
            cat = con.execute("SELECT filename, runs FROM catalog ORDER BY filename").fetchall()
            con.close()
            chk("⑥ DuckDB 可查:r3 財務列 4 · catalog a 跑 3 次", n == 4 and ("a.pdf", 3) in cat)
        else:
            import pyarrow.parquet as pq  # noqa: WPS433
            chk("⑥ pyarrow 備援:catalog.parquet 4 檔 · 收據標 YELLOW 並說明", pq.read_metadata(str(out / "VRN2" / "parquet" / "catalog.parquet")).num_rows == 4 and r3["lamp"] == "YELLOW" and "duckdb" in r3["why"])
        r4 = sync(v2, output_dir=Path(td) / "elsewhere", run_id="r4")
        chk("⑦ --output-dir 覆蓋設定冊 · 新庫從頭(3 新檔)", r4["output_dir"].endswith("elsewhere") and len(r4["new_files"]) == 3)
        bad = Path(td) / "file_not_dir"
        bad.write_text("x", encoding="utf-8")
        r5 = sync(v2, output_dir=bad / "sub", run_id="r5")
        chk("⑧ 輸出夾開不了 → RED 說原因", r5["lamp"] == "RED" and "開不了" in r5["why"])
    say("[計] %s %s --selftest · OK %d · FAIL %d" % (DISPLAY_NAME, TAG, len(oks), len(fails)))
    return 0 if not fails else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="VRN2_OutputStore_%s" % TAG)
    ap.add_argument("verb", nargs="?", choices=["sync", "set", "show"], default="sync")
    ap.add_argument("--v2", default=None, help="VIA_Reports/vrn2(預設 = 本檔往上找 VIA 根)")
    ap.add_argument("--output-dir", default=None, help="sync:這一次用的輸出夾(覆蓋設定冊);set:寫進設定冊")
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    v2 = Path(a.v2).resolve() if a.v2 else next((p / "VIA_Reports" / "vrn2" for p in [HERE] + list(HERE.parents) if (p / "VIA_Reports").is_dir()), HERE / "VIA_Reports" / "vrn2")
    if a.verb == "set":
        if not a.output_dir:
            say("[RED] set 要 --output-dir")
            return 2
        cfg = write_config(v2, a.output_dir, "命令列")
        say("[GREEN] 輸出位置 · %s · %s" % (cfg["output_dir"], cfg["cloud_hint"]))
        return 0
    if a.verb == "show":
        say(json.dumps(read_config(v2), ensure_ascii=False))
        return 0
    r = sync(v2, Path(a.output_dir) if a.output_dir else None, a.run_id)
    print_result(r)
    return {"GREEN": 0, "YELLOW": 2, "GRAY": 0, "RED": 1}.get(r.get("lamp"), 1)


if __name__ == "__main__":
    sys.exit(main())
