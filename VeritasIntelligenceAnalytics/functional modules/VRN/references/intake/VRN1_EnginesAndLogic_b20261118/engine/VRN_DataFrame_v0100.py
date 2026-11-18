#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===== [VRN:ID:v0100] VRN-ENG012 · VRN_DataFrame_v0100 v0100 · ENGINE =====
# AST 注入（只加註解，AST 不變）：類別 0 · 函式 11；逐一編號在 ssot/VRN_ID_SSOT_v0100.json
# ===== [VRN:ID:END] =====
"""
VRN_DataFrame v0100 -- every VRN output as a pandas DataFrame, checked against its header book, written out.

Operator 2026-10-11: 「範圍限縮獨立系統VRN 輸出DATAFRAME 請確認完成」.

  book   ssot/VRN_Output_Header_SSOT_v0101.json -- 18 tables (v0100's 13 untouched + the five G17 / G18 tables of 2026-10-11),
         the same shape as the mother's VIA_Output_Header_SSOT; v0102 (2026-10-11 G19) adds vrn_focus_files = 19 tables; v0103 (real run 2026-10-12) turns two 'required' flags off
         (column name / dtype / required / key; table source / min_rows / extra_ok), plus zh and display names; v0104
         (2026-10-12) adds vrn_ticker_record = 20 tables; v0105 (real run 2026-10-15, one industry report -> N rows)
         makes vrn_basic_info's primary key (ReportID, TW_TICKER); v0106 (2026-10-15) adds vrn_focus_files.process;
         v0107 (2026-10-16 一標題四重點) adds vrn_summary_points = 21 tables; v0108 (2026-10-19 操作員「相互對照兩個以上
         相同即算對照成功」) adds vrn_trim_parts.agree -- the number of agreeing source groups behind the value taken.
  check  the mother's CGC_MDL249_DataFrameLock check_table, byte copy in engine/mother/ (one rule set, not a second copy):
         a required column missing = RED · a column the book does not list = YELLOW (header not settled) · a value that does
         not parse as its dtype = RED · a required value empty = RED · a repeated primary key = RED · fewer rows than
         min_rows = RED · the source absent = NODATA (said, never passed off as green).
  write  each checked DataFrame to <out>/dataframes/<table>.parquet (typed: int -> Int64, float -> float64, others text) and
         <table>.csv (UTF-8 with BOM for Excel), and VRN_DataFrame_Lock_v0100.json with every table's lamp.

Only reads the outputs it checks; writes only under <out>/dataframes/.  The per-table work goes through the caller's
accelerator lane (pandas reads and writes release the GIL).  No network.
"""

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

import argparse
import importlib.util
import json
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

DATAFRAME_VERSION = "v0100"
VRN_ROOT = Path(__file__).resolve().parents[1]
HEADER_BOOK = VRN_ROOT / "ssot" / "VRN_Output_Header_SSOT_v0111.json"
LOCK_FILE = VRN_ROOT / "engine" / "mother" / "CGC_MDL249_DataFrameLock_v0100.py"
OUT_DIRNAME = "dataframes"
REPORT_NAME = "VRN_DataFrame_Lock_v0100.json"


# [VRN-ID] VRN-ENG012-FNC001 · IO
def load_book(path=HEADER_BOOK):
    book = json.loads(Path(path).read_text(encoding="utf-8"))
    book["_path"] = Path(path).name
    return book


_LOCK = None


# [VRN-ID] VRN-ENG012-FNC002 · IO
def load_lock():
    """The mother's DataFrame lock, loaded by path (check_table only; it writes nothing when given a frame)."""
    global _LOCK
    if _LOCK is None:
        spec = importlib.util.spec_from_file_location("vrn_dataframe_cgc_mdl249", LOCK_FILE)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        _LOCK = module
    return _LOCK


# [VRN-ID] VRN-ENG012-FNC003 · IO
def load_frame(out_dir, spec):
    """(DataFrame, "") or (None, why) for one table of one run."""
    import pandas as pd
    src = spec.get("source") or {}
    path = Path(out_dir) / str(src.get("path") or "")
    if not path.is_file():
        return None, f"來源不在：{path}"
    kind = src.get("kind")
    try:
        if kind == "parquet":
            return pd.read_parquet(path), ""
        if kind == "csv":
            return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig"), ""
        if kind == "sqlite":
            con = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
            try:
                return pd.read_sql_query(f'SELECT * FROM "{src.get("table")}"', con), ""
            finally:
                con.close()
        if kind == "json":
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, list) and not data:          # no rows: the header is the book's (a JSON list carries none)
                return pd.DataFrame(columns=[c["name"] for c in spec.get("columns") or []], dtype=str), ""
            return pd.DataFrame(data if isinstance(data, list) else []), ""
    except Exception as error:  # noqa: BLE001
        return None, f"載不進 DataFrame：{error.__class__.__name__}: {error}"[:300]
    return None, f"不認得的來源種類 {kind!r}"


# [VRN-ID] VRN-ENG012-FNC004 · LOGIC
def typed(frame, spec):
    """The DataFrame as written: the book's dtypes (int -> Int64, float -> float64, the rest text with '' for empty)."""
    import pandas as pd
    out = frame.copy()
    for c in spec.get("columns") or []:
        name, dtype = c.get("name"), c.get("dtype")
        if name not in out.columns:
            continue
        if dtype == "int":
            out[name] = pd.to_numeric(out[name], errors="coerce").round().astype("Int64")
        elif dtype == "float":
            out[name] = pd.to_numeric(out[name], errors="coerce").astype("float64")
        else:
            # pandas' own missing marks (pd.NA from a nullable parquet column, NaT) are empty too, never the text "<NA>";
            # read as objects first: mapping a nullable Int64 column with a gap turns 1 into 1.0
            out[name] = out[name].astype(object).map(lambda v: "" if v is None or v is pd.NA or v is pd.NaT or (isinstance(v, float) and v != v) else str(v)).astype("string")
    return out


# [VRN-ID] VRN-ENG012-FNC009 · LOGIC
def iso_dates(frame, spec):
    """Real run 2026-10-12: a date column whose values are written two ways ('2025-08-18' / '2025/08/18') fails a column-wide parse
    (pandas takes the first value's format).  Every value is read on its own and written ISO; what cannot be read stays as it is
    (and is still RED).  -> (frame, how many values were rewritten)."""
    import pandas as pd
    changed = 0
    out = frame
    for c in spec.get("columns") or []:
        if c.get("dtype") not in ("date", "datetime") or c["name"] not in frame.columns:
            continue

        # [VRN-ID] VRN-ENG012-FNC010 · LOGIC
        def one(v, dtype=c["dtype"]):
            nonlocal changed
            if v is None or (isinstance(v, float) and v != v) or str(v).strip() == "":
                return v
            try:
                ts = pd.Timestamp(str(v).strip())
            except (ValueError, TypeError):
                return v
            if ts is pd.NaT:
                return v
            text = ts.strftime("%Y-%m-%d") if dtype == "date" else ts.isoformat()
            if text != str(v):
                changed += 1
            return text
        if out is frame:
            out = frame.copy()
        out[c["name"]] = frame[c["name"]].map(one)
    return out, changed


# [VRN-ID] VRN-ENG012-FNC011 · LOGIC
def table_bad_samples(frame, spec, limit=3):
    """For a RED type problem: the first values that do not read as their dtype (shown, so the next fix starts from the data)."""
    import pandas as pd
    out = []
    for c in spec.get("columns") or []:
        name, dtype = c["name"], c.get("dtype")
        if name not in frame.columns or dtype not in ("int", "float", "date", "datetime"):
            continue
        s = frame[name]
        s = s[s.notna() & (s.astype(str).str.strip() != "")]
        if s.empty:
            continue
        if dtype in ("int", "float"):
            bad = s[pd.to_numeric(s, errors="coerce").isna()]
        else:
            bad = s[[pd.isna(pd.to_datetime(str(v), errors="coerce")) for v in s]]
        if len(bad):
            out.append(f"{name} 樣本 {list(map(str, bad.head(limit)))}")
    return out


# [VRN-ID] VRN-ENG012-FNC005 · LOGIC
def check(out_dir, book=None, mapper=None, write=True):
    """Every table of the header book against one run's outputs -> report; the DataFrames under <out_dir>/dataframes/."""
    lock = load_lock()
    book = book or load_book()
    target = Path(out_dir) / OUT_DIRNAME
    if write:
        target.mkdir(parents=True, exist_ok=True)
    try:
        import pyarrow  # noqa: F401
        have_parquet = True
    except Exception:  # noqa: BLE001
        have_parquet = False
    started = time.perf_counter()

    # [VRN-ID] VRN-ENG012-FNC006 · LOGIC
    def one(item):
        tid, spec = item
        frame, why = load_frame(out_dir, spec)
        if frame is None:
            return {"table": tid, "zh": spec.get("zh", ""), "lamp": "NODATA", "problems": [why], "rows": None,
                    "header_sha": lock.header_sha(spec), "owner": spec.get("owner")}
        frame, iso_changed = iso_dates(frame, spec)
        row = lock.check_table(tid, spec, frame=frame)
        row.update(zh=spec.get("zh", ""), columns=len(frame.columns))
        if iso_changed:
            row["iso_dates"] = iso_changed
        if row.get("lamp") == "RED":
            samples = table_bad_samples(frame, spec)
            if samples:
                row["problems"] = list(row.get("problems") or []) + samples
        if write:
            out = typed(frame, spec)
            csv_path = target / f"{tid}.csv"
            out.to_csv(csv_path, index=False, encoding="utf-8-sig")
            row["csv"] = str(csv_path)
            if have_parquet:
                pq = target / f"{tid}.parquet"
                out.to_parquet(pq, index=False)
                row["parquet"] = str(pq)
        return row

    items = sorted((book.get("tables") or {}).items())
    rows = (mapper or (lambda fn, xs, action: [fn(x) for x in xs]))(one, items, "G16 DataFrame：逐表載入、驗表頭、寫出")
    lamps = {r["lamp"] for r in rows}
    verdict = "RED" if "RED" in lamps else ("YELLOW" if lamps & {"YELLOW", "NODATA"} or not rows else "GREEN")
    report = {"engine": "VRN_DataFrame " + DATAFRAME_VERSION, "book": book.get("_path"), "lock": LOCK_FILE.name, "out": str(out_dir),
              "verdict": verdict, "seconds": round(time.perf_counter() - started, 3),
              "parquet": have_parquet, "tables": rows}
    if write:
        (target / REPORT_NAME).write_text(json.dumps(report, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
        report["path"] = str(target / REPORT_NAME)
    return report


# =====================================================================
# SELF-TEST AND CLI
# =====================================================================
# [VRN-ID] VRN-ENG012-FNC007 · ENTRY
def selftest():
    try:
        import pandas as pd
    except Exception:  # noqa: BLE001
        print("  [SKIP] pandas 沒有安裝：pip install pandas pyarrow（安裝是操作員的手）")
        return 0
    lock = load_lock()
    book = load_book()
    checks = [("表頭冊 21 張表", len(book["tables"]) == 21, str(len(book["tables"])))]
    spec = {"source": {"kind": "csv", "path": "t.csv"}, "min_rows": 1, "extra_ok": False,
            "columns": [{"name": "id", "dtype": "str", "required": True, "key": True}, {"name": "v", "dtype": "float", "required": True},
                        {"name": "n", "dtype": "int"}]}
    with tempfile.TemporaryDirectory(prefix="vrn_df_selftest_") as tmp:
        cases = {
            "全對 = GREEN": (pd.DataFrame({"id": ["a", "b"], "v": ["1.5", "2"], "n": ["1", ""]}), "GREEN"),
            "缺必填欄 = RED": (pd.DataFrame({"id": ["a"], "n": ["1"]}), "RED"),
            "多出冊上沒有的欄 = YELLOW": (pd.DataFrame({"id": ["a"], "v": ["1"], "n": ["1"], "x": ["?"]}), "YELLOW"),
            "主鍵重複 = RED": (pd.DataFrame({"id": ["a", "a"], "v": ["1", "2"], "n": ["1", "2"]}), "RED"),
            "型別不對 = RED": (pd.DataFrame({"id": ["a"], "v": ["一點五"], "n": ["1"]}), "RED"),
            "必填空 = RED": (pd.DataFrame({"id": ["a"], "v": [""], "n": ["1"]}), "RED"),
            "整數欄有小數 = RED": (pd.DataFrame({"id": ["a"], "v": ["1"], "n": ["1.5"]}), "RED"),
        }
        for name, (frame, want) in cases.items():
            got = lock.check_table("t", spec, frame=frame)["lamp"]
            checks.append((name, got == want, got))
        pd.DataFrame({"id": ["a"], "v": ["1"], "n": ["2"]}).to_csv(Path(tmp) / "t.csv", index=False, encoding="utf-8-sig")
        rep = check(tmp, book={"tables": {"t": spec, "absent": dict(spec, source={"kind": "csv", "path": "none.csv"})}, "_path": "test"})
        lamps = {r["table"]: r["lamp"] for r in rep["tables"]}
        checks.append(("來源不在 = NODATA，有的照驗", lamps == {"t": "GREEN", "absent": "NODATA"}, str(lamps)))
        (Path(tmp) / "empty.json").write_text("[]", encoding="utf-8")
        rep0 = check(tmp, book={"tables": {"e": dict(spec, source={"kind": "json", "path": "empty.json"}, min_rows=0)}, "_path": "test"},
                     write=False)
        checks.append(("空的 JSON 來源 = 0 列、表頭照冊（min_rows 0 = GREEN）", rep0["tables"][0]["lamp"] == "GREEN", str(rep0["tables"][0])[:200]))
        dspec = {"source": {"kind": "json", "path": "d.json"}, "min_rows": 1, "extra_ok": False,
                 "columns": [{"name": "id", "dtype": "str", "required": True, "key": True}, {"name": "d", "dtype": "date"}]}
        (Path(tmp) / "d.json").write_text(json.dumps([{"id": "a", "d": "2025-08-18"}, {"id": "b", "d": "2025/08/19"}, {"id": "c", "d": ""}]),
                                          encoding="utf-8")
        repd = check(tmp, book={"tables": {"d": dspec}, "_path": "test"}, write=False)["tables"][0]
        checks.append(("日期兩種寫法（2025-08-18／2025/08/19）逐筆讀 = GREEN，統一寫成 ISO", repd["lamp"] == "GREEN" and repd.get("iso_dates") == 1,
                       str(repd)[:200]))
        (Path(tmp) / "d.json").write_text(json.dumps([{"id": "a", "d": "2025-08-18"}, {"id": "b", "d": "不是日期"}]), encoding="utf-8")
        repd = check(tmp, book={"tables": {"d": dspec}, "_path": "test"}, write=False)["tables"][0]
        checks.append(("真的不是日期 = RED，並印出樣本", repd["lamp"] == "RED" and any("不是日期" in x for x in repd["problems"]), str(repd)[:200]))
        na = typed(pd.DataFrame({"id": pd.array(["a", None], dtype="string"), "v": [1.0, None], "n": pd.array([1, None], dtype="Int64")}),
                   {"columns": [{"name": "id", "dtype": "str"}, {"name": "v", "dtype": "float"}, {"name": "n", "dtype": "str"}]})
        checks.append(("pandas 的缺值（pd.NA／可空整數欄）寫成空字串，不會變成 \"<NA>\"", list(na["id"]) == ["a", ""] and list(na["n"]) == ["1", ""],
                       (list(na["id"]), list(na["n"]))))
        written = Path(tmp) / OUT_DIRNAME / "t.csv"
        checks.append(("驗過的 DataFrame 寫出", written.is_file() and pd.read_csv(written, encoding="utf-8-sig").shape == (1, 3), str(written)))
    for name, ok, detail in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + ("" if ok else f" · {detail}"))
    failed = sum(1 for _n, ok, _d in checks if not ok)
    print(f"[DATAFRAME] VRN_DataFrame {DATAFRAME_VERSION} · {len(checks) - failed}/{len(checks)}")
    return 1 if failed else 0


# [VRN-ID] VRN-ENG012-FNC008 · ENTRY
def main(argv=None):
    parser = argparse.ArgumentParser(description="VRN DataFrame: every output as a checked pandas DataFrame")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("selftest")
    run = sub.add_parser("check")
    run.add_argument("out", help="一輪的輸出夾（AutoTestLoop 的 round 夾）")
    args = parser.parse_args(argv)
    if args.command == "check":
        rep = check(args.out)
        for r in rep["tables"]:
            print(f"  [{r['lamp']:6}] {r['table']:26} rows={r.get('rows')} " + "; ".join(r.get("problems") or [])[:200])
        print(f"[DATAFRAME] {rep['verdict']} · {rep.get('path', '')}")
        return {"GREEN": 0, "RED": 1}.get(rep["verdict"], 2)
    return selftest()


if __name__ == "__main__":
    sys.exit(main())
