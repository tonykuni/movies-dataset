#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL249_DataFrameLock v0101 — 薄尾:表頭全面覆蓋檢查 + json 型別 + 一次跑完(check → coverage → lock)

操作員 2026-10-14:「VDF VRN 輸出 HEADER 還要檢查全面」「輸出 HEADER 完整確認然後 DATAFRAME 固定」。v0100 只核冊上那幾張表,
冊外的輸出表看不見;本版只加三件,其餘(plan / check / lock / 判法 / 鎖帳)全部照 v0100:
  json 型別        冊候選區(CGC_MDL269)用的 json 欄型(值是 list / dict,或可解析的 JSON 字串)v0100 判成「冊上型別不在」→ 補進型別表
  coverage         掃 VDF / VRN 全部輸出庫(與 CGC_MDL277 AiOps 庫卡同一份清單 output_dbs)的每張表,對照表頭冊的 source(庫 + 表):
                   有表頭 = COVERED · 冊外 = UNCOVERED(黃,列出 → 下一版冊照寫入程式補欄位)· 冊有庫沒有 = BOOK_ONLY(照實)
                   → VIA_Reports/dataframe_lock/DFCOVER_latest.json
  all [--apply]    check + coverage + lock(預設乾跑;--apply 才寫鎖帳)一次跑完,一個判決 → DFLOCK_ALL_latest.json
只收 VCGC 呼叫;庫一律 read_only;不改冊(改表頭照舊先出冊新版);不用 TA-Lib。
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
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
ENGINE = Path(__file__).stem
_STEM = "CGC_MDL249_DataFrameLock"


def _vn(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vn(p) < _vn(__file__)), key=_vn)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + ENGINE, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(PRIOR)

DTYPES = tuple(PRIOR.DTYPES) + ("json",)
OUT = PRIOR.OUT
LEDGER = PRIOR.LEDGER
_PRIOR_CASTABLE = PRIOR._castable


def _castable(series, dtype: str) -> int:
    """v0100 + json: a value counts when it is a list / dict, or a string that parses as JSON."""
    if dtype != "json":
        return _PRIOR_CASTABLE(series, dtype)
    bad = 0
    for v in series.dropna():
        if isinstance(v, (list, dict)):
            continue
        try:
            json.loads(str(v))
        except ValueError:
            bad += 1
    return bad


PRIOR.DTYPES = DTYPES          # v0100 的 check_table 讀模組層 DTYPES / _castable:本版的私載實例換成本版的
PRIOR._castable = _castable
load_book, check, lock, plan, read_ledger, resolve_source = (PRIOR.load_book, PRIOR.check, PRIOR.lock, PRIOR.plan,
                                                             PRIOR.read_ledger, PRIOR.resolve_source)
# 前版公開面照轉(TAILAPI):VDF / VRN 管理器與 VRN_ENG393 取尾版後直呼 check_table 等;沒列到的名稱由 __getattr__ 轉給前版
check_table, header_sha, load_frame, book_path = PRIOR.check_table, PRIOR.header_sha, PRIOR.load_frame, PRIOR.book_path
BOOK_GLOB, VIA_ROOT = PRIOR.BOOK_GLOB, PRIOR.VIA


def __getattr__(name):
    return getattr(PRIOR, name)


def _output_dbs(via: Path) -> tuple:
    hits = sorted((p for p in HERE.glob("CGC_MDL277_AiOps_v*.py")), key=_vn)
    if not hits:
        return ()
    spec = importlib.util.spec_from_file_location("CGC_MDL277_for_" + ENGINE, hits[-1])
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.output_dbs(via)


def coverage(book: dict | None = None, via: Path = VIA, dbs: tuple | None = None) -> dict:
    """Every table in every VDF / VRN output database vs the header book's (db, table) sources."""
    via = Path(via)
    book = book or load_book()
    dbs = _output_dbs(via) if dbs is None else dbs
    booked = {}
    for tid, spec in (book.get("tables") or {}).items():
        src = spec.get("source") or {}
        if src.get("kind") == "duckdb" and src.get("path"):
            booked.setdefault((Path(str(src["path"])).name, str(src.get("table") or "")), []).append(tid)
    rows, seen = [], set()
    try:
        import duckdb
    except ImportError:
        return {"engine": ENGINE, "verdict": "YELLOW", "why": "duckdb 未裝", "rows": []}
    for rel in dbs:
        try:
            con = duckdb.connect(str(via / rel), read_only=True)
        except Exception as exc:  # noqa: BLE001 — 鎖住 / 壞檔照實記
            rows.append({"db": rel, "table": None, "state": "UNREADABLE", "why": str(exc)[:120]})
            continue
        try:
            tabs = [t for (t,) in con.execute("select table_name from information_schema.tables where table_schema='main' order by 1").fetchall()]
            for t in tabs:
                key = (Path(rel).name, t)
                seen.add(key)
                n = con.execute(f'select count(*) from "{t}"').fetchone()[0]
                rows.append({"db": rel, "table": t, "rows": n, "state": "COVERED" if key in booked else "UNCOVERED",
                             "book_ids": booked.get(key, [])})
        finally:
            con.close()
    for key, ids in sorted(booked.items()):
        if key not in seen and any(Path(r).name == key[0] for r in dbs):
            rows.append({"db": key[0], "table": key[1], "state": "BOOK_ONLY", "book_ids": ids})
    unc = [r for r in rows if r["state"] == "UNCOVERED" and r.get("rows")]
    rep = {"engine": ENGINE, "book": book.get("_path"), "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "dbs": len(dbs), "tables": sum(1 for r in rows if r.get("table") and r["state"] != "BOOK_ONLY"),
           "covered": sum(1 for r in rows if r["state"] == "COVERED"), "uncovered_nonempty": len(unc),
           "uncovered_empty": sum(1 for r in rows if r["state"] == "UNCOVERED" and not r.get("rows")),
           "verdict": "YELLOW" if unc else "GREEN", "rows": rows}
    return rep


def run_all(apply: bool = False) -> dict:
    book = load_book()
    rep = check(book=book)
    cov = coverage(book)
    lk = lock(apply=apply, rep=rep, book=book)
    lamps = [rep["verdict"], cov["verdict"], "RED" if lk["refused"] else "GREEN"]
    verdict = "RED" if "RED" in lamps else ("YELLOW" if "YELLOW" in lamps else "GREEN")
    out = {"engine": ENGINE, "at": rep["at"], "verdict": verdict, "book": book.get("_path"),
           "check": {k: sum(1 for r in rep["tables"] if r["lamp"] == k) for k in ("GREEN", "YELLOW", "NODATA", "RED")},
           "coverage": {k: cov.get(k) for k in ("dbs", "tables", "covered", "uncovered_nonempty", "uncovered_empty")},
           "lock": {"new": len(lk["new"]), "refused": lk["refused"], "applied": lk["applied"]},
           "red_tables": [r["table"] for r in rep["tables"] if r["lamp"] == "RED"],
           "uncovered": [f"{Path(r['db']).name}::{r['table']}" for r in cov["rows"] if r["state"] == "UNCOVERED" and r.get("rows")]}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "DFCOVER_latest.json").write_text(json.dumps(cov, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    (OUT / "DFLOCK_ALL_latest.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return out


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["--selftest"]:
        return selftest()
    verb = a[0] if a else "check"
    if verb not in ("coverage", "all"):
        PRIOR.ENGINE = ENGINE
        return PRIOR.main(a)
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc(VIA_FROM_VCGC=YES)"}, ensure_ascii=False))
        return 2
    if verb == "coverage":
        cov = coverage()
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "DFCOVER_latest.json").write_text(json.dumps(cov, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
        for r in cov["rows"]:
            if r["state"] != "COVERED":
                print(f"  {r['state']:<10} {Path(str(r['db'])).name}::{r['table']}  列 {r.get('rows', '-')}")
        print(f"[表頭覆蓋] {cov['verdict']} · 庫 {cov['dbs']} · 表 {cov['tables']} · 有表頭 {cov['covered']} · "
              f"冊外有資料 {cov['uncovered_nonempty']} · 冊外空表 {cov['uncovered_empty']}")
        return 0 if cov["verdict"] == "GREEN" else 2
    out = run_all("--apply" in a)
    print(f"[DataFrame 鎖 · all] {out['verdict']} · check {out['check']} · 覆蓋 {out['coverage']} · "
          f"鎖 新 {out['lock']['new']} 拒 {len(out['lock']['refused'])} {'已寫' if out['lock']['applied'] else '乾跑'}")
    for t in out["red_tables"]:
        print(f"  RED        {t}")
    for t in out["uncovered"]:
        print(f"  UNCOVERED  {t}")
    return {"GREEN": 0, "YELLOW": 2, "RED": 1}[out["verdict"]]


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print("  — v0100 自測(繼承)—")
    prior_rc = PRIOR.selftest()
    chk("① 前版自測全過(判法 · 鎖帳 · 三種來源照舊)", prior_rc == 0, prior_rc)
    import pandas as pd
    s = pd.Series([[1, 2], {"a": 1}, '{"b": 2}', "[3]", "not json", None])
    chk("② json 型別:list / dict / JSON 字串算過 · 壞字串算 1 筆 · 空值不算", _castable(s, "json") == 1 and "json" in PRIOR.DTYPES)
    with tempfile.TemporaryDirectory() as tmp:
        via = Path(tmp)
        import duckdb
        (via / "o").mkdir()
        con = duckdb.connect(str(via / "o" / "x.duckdb"))
        con.execute("create table a(k varchar)")
        con.execute("insert into a values ('1')")
        con.execute("create table b(k varchar)")
        con.execute("insert into b values ('1')")
        con.execute("create table e(k varchar)")
        con.close()
        book = {"tables": {"ta": {"source": {"kind": "duckdb", "path": "o/x.duckdb", "table": "a"}},
                           "tz": {"source": {"kind": "duckdb", "path": "o/x.duckdb", "table": "zz"}}}}
        cov = coverage(book, via, ("o/x.duckdb",))
        st = {r["table"]: r["state"] for r in cov["rows"]}
        chk("③ 覆蓋:冊上有 = COVERED · 冊外有資料 = UNCOVERED(黃)· 冊外空表另計 · 冊有庫沒有 = BOOK_ONLY",
            st == {"a": "COVERED", "b": "UNCOVERED", "e": "UNCOVERED", "zz": "BOOK_ONLY"} and cov["uncovered_nonempty"] == 1
            and cov["uncovered_empty"] == 1 and cov["verdict"] == "YELLOW", st)
    real = _output_dbs(VIA)
    src = Path(__file__).read_text(encoding="utf-8")
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main(["coverage"]) == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    chk("④ 實樹輸出庫清單與 AiOps 庫卡同一份 · 只收 VCGC · 加速器橋在 · 不碰 TA-Lib",
        isinstance(real, tuple) and denied and "VIA:ACCEL-BRIDGE" in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M),
        f"輸出庫 {len(real)}")
    names = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n)) and getattr(getattr(PRIOR, n), "__module__", "") == PRIOR.__name__]
    me = sys.modules[__name__]
    chk("⑤ 前版公開函式全部可從尾版取用(check_table 等;TAILAPI 轉接)", all(callable(getattr(me, n, None)) for n in names)
        and check_table is PRIOR.check_table, f"{len(names)} 個")
    print(f"  {ENGINE} selftest {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
