#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG229_CNNFearGreedHistory v0101 — 薄尾:+`dedupe` 清 sentiment_daily 既有重複列(掉球 Z297;操作員 2026-10-14「繼續修 Z297」)。

實錄:vdf_global_market.duckdb · sentiment_daily 256 列、相異 252 列(2026-09-23 / 09-24 各 3 筆一模一樣)。
寫入端的根因在 VDF_ENG055 L11(同批重鍵沒先去重)→ ENG055 v0123 已修;本支只清庫裡已經在的重複,VDF 自己的引擎(L120)。

  dedupe            唯讀乾跑:列數 · 相異鍵 · 整列重複多出的列 · 同鍵不同值(CONFLICT)
  dedupe --apply    刪整列重複多出的列(每個 date+index 留一筆;同一筆內容,留哪一筆都一樣);只增帳 sentiment_dedupe_ledger.jsonl
  dedupe --apply --keep-last   連 CONFLICT 也處理:同鍵留最後寫入的那一筆(rowid 最大;與 ENG055 v0123「同日留最後一筆」同判準)
  不帶 --keep-last 時 CONFLICT 只報不刪(不替操作員挑值)。其餘動詞(status / run / --selftest 鏈)照前版。
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
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG229_CNNFearGreedHistory"
ENGINE_TAG = _STEM + "_v" + Path(__file__).stem.rsplit("_v", 1)[-1]


def _vnum(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _prior_path() -> Path:
    """同族版號小於自己的最新一支(尾版律;不釘版號)。"""
    me = _vnum(__file__)
    olds = sorted((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < me), key=_vnum)
    if not olds:
        raise FileNotFoundError(f"{_STEM}:版號小於 v{me:04d} 的前版不在")
    return olds[-1]


def _load(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR = _load(_prior_path(), "_vdf_eng229_prior_for_" + Path(__file__).stem)
TABLE, KEYS, DB_GL, OUT = PRIOR.TABLE, PRIOR.KEYS, PRIOR.DB_GL, PRIOR.OUT
LEDGER_NAME = "sentiment_dedupe_ledger.jsonl"


def __getattr__(name):
    """前版公開面照轉(TAILAPI:尾版不少名字)。"""
    return getattr(PRIOR, name)


def _q(c: str) -> str:
    return '"' + c.replace('"', '""') + '"'


def dup_report(con) -> dict:
    """唯讀:列數 · 相異鍵 · 整列重複多出的列 · 同鍵不同值的鍵(CONFLICT,最多列 20 個)。"""
    cols = [r[0] for r in con.execute(f"DESCRIBE {_q(TABLE)}").fetchall()]
    keys = ", ".join(_q(k) for k in KEYS)
    rest = [c for c in cols if c not in KEYS]
    vals = "(" + ", ".join(_q(c) for c in rest) + ")" if rest else "1"
    n, k = con.execute(f"SELECT COUNT(*), COUNT(DISTINCT ({keys})) FROM {_q(TABLE)}").fetchone()
    grp = con.execute(f"SELECT {keys}, COUNT(*) AS n, COUNT(DISTINCT {vals}) AS v FROM {_q(TABLE)} "
                      f"GROUP BY {keys} HAVING COUNT(*) > 1 ORDER BY {keys}").fetchall()
    exact = [g for g in grp if g[-1] == 1]
    conflict = [g for g in grp if g[-1] > 1]
    return {"rows": int(n), "distinct_keys": int(k), "dup_keys": len(grp),
            "exact_extra": sum(int(g[-2]) - 1 for g in exact), "exact_keys": [list(map(str, g[:-2])) for g in exact][:20],
            "conflict_keys": len(conflict), "conflict_extra": sum(int(g[-2]) - 1 for g in conflict),
            "conflict_list": [list(map(str, g[:-2])) for g in conflict][:20]}


def dedupe(db: Path = DB_GL, apply: bool = False, keep_last: bool = False, ledger: Path | None = None) -> dict:
    """乾跑回報告;--apply 刪整列重複多出的列(keep_last 再加同鍵不同值留最後寫入)。只增帳。"""
    db = Path(db)
    if not db.is_file():
        return {"state": "NODB", "db": str(db)}
    import duckdb
    con = duckdb.connect(str(db), read_only=not apply)
    try:
        if TABLE not in {r[0] for r in con.execute("SHOW TABLES").fetchall()}:
            return {"state": "NOTABLE", "db": str(db), "table": TABLE}
        before = dup_report(con)
        out = {"engine": ENGINE_TAG, "db": str(db), "table": TABLE, "keys": KEYS, "apply": apply,
               "keep_last": keep_last, "before": before, "deleted": 0}
        if not apply or not before["dup_keys"]:
            out["state"] = "CLEAN" if not before["dup_keys"] else "DRY"
            return out
        cols = [r[0] for r in con.execute(f"DESCRIBE {_q(TABLE)}").fetchall()]
        keys = ", ".join(_q(k) for k in KEYS)
        rest = [c for c in cols if c not in KEYS]
        vals = "(" + ", ".join(_q(c) for c in rest) + ")" if rest else "1"
        having = "" if keep_last else f" AND COUNT(DISTINCT {vals}) = 1"
        on = " AND ".join(f"e.{_q(k)} = x.{_q(k)}" for k in KEYS)
        con.execute("BEGIN TRANSACTION")
        try:
            con.execute(f"CREATE TEMP TABLE _dd_keys AS SELECT {keys} FROM {_q(TABLE)} GROUP BY {keys} HAVING COUNT(*) > 1{having}")
            con.execute(f"DELETE FROM {_q(TABLE)} WHERE rowid IN (SELECT x.rid FROM (SELECT rowid AS rid, {keys}, "
                        f"row_number() OVER (PARTITION BY {keys} ORDER BY rowid DESC) AS rn FROM {_q(TABLE)}) AS x "
                        f"WHERE x.rn > 1 AND EXISTS (SELECT 1 FROM _dd_keys AS e WHERE {on}))")
            con.execute("DROP TABLE _dd_keys")
            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK")
            raise
        after = dup_report(con)
        out.update(after=after, deleted=before["rows"] - after["rows"],
                   state="OK" if not after["dup_keys"] else ("CONFLICT" if after["conflict_keys"] else "PARTIAL"))
    finally:
        con.close()
    led = Path(ledger) if ledger else db.parent / LEDGER_NAME
    rec = {"utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "engine": ENGINE_TAG, "db": db.name,
           "table": TABLE, "keep_last": keep_last, "rows_before": out["before"]["rows"], "deleted": out["deleted"],
           "rows_after": out["after"]["rows"], "state": out["state"], "removed_keys": out["before"]["exact_keys"]
           + (out["before"]["conflict_list"] if keep_last else [])}
    with led.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    out["ledger"] = str(led)
    return out


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["dedupe"]:
        if os.environ.get("VIA_FROM_VCGC") != "YES":
            print(json.dumps({"via": "vcgc", "state": "DENY", "why": "只經 VCGC(VIA_FROM_VCGC=YES)"}, ensure_ascii=False))
            return 2
        r = dedupe(apply="--apply" in a, keep_last="--keep-last" in a)
        print(json.dumps(r, ensure_ascii=False, indent=1))
        b = r.get("before") or {}
        print(f"  [sentiment 去重] {r['state']} · {TABLE} 列 {b.get('rows', '—')} · 相異鍵 {b.get('distinct_keys', '—')} · "
              f"整列重複多 {b.get('exact_extra', '—')} · 同鍵不同值 {b.get('conflict_keys', '—')} 鍵 · 刪 {r.get('deleted', 0)}")
        return {"OK": 0, "CLEAN": 0, "DRY": 2, "CONFLICT": 2, "PARTIAL": 2}.get(r["state"], 1)
    if "--selftest" in a:
        return selftest()
    return PRIOR.main(a)


# ---------------------------------------------------------------- 自測(暫存庫;零外呼)
def selftest() -> int:
    import tempfile
    import duckdb
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "gl.duckdb"
        con = duckdb.connect(str(db))
        con.execute(f'CREATE TABLE {TABLE} (date VARCHAR, "index" VARCHAR, score DOUBLE, rating VARCHAR)')
        rows = [("2026-09-22", "CNN_FEAR_GREED", 40.0, "fear")] + [("2026-09-23", "CNN_FEAR_GREED", 35.9, "fear")] * 3 \
            + [("2026-09-24", "CNN_FEAR_GREED", 36.1, "fear")] * 3 + [("2026-09-25", "CNN_FEAR_GREED", 50.0, "neutral"),
                                                                      ("2026-09-25", "CNN_FEAR_GREED", 51.0, "neutral"),
                                                                      ("2026-09-26", "CNN_FEAR_GREED", None, None),
                                                                      ("2026-09-26", "CNN_FEAR_GREED", None, None)]
        con.executemany(f"INSERT INTO {TABLE} VALUES (?, ?, ?, ?)", rows)
        con.close()
        dry = dedupe(db)
        b = dry["before"]
        chk("① 乾跑只報:11 列 · 相異鍵 5 · 整列重複多 5(含全 NULL 值列)· 同鍵不同值 1 鍵", dry["state"] == "DRY" and b["rows"] == 11
            and b["distinct_keys"] == 5 and b["exact_extra"] == 5 and b["conflict_keys"] == 1 and not (Path(td) / LEDGER_NAME).exists(), str(b))
        r = dedupe(db, apply=True)
        chk("② --apply 刪整列重複 5 列;CONFLICT 不替操作員挑值(只報)", r["deleted"] == 5 and r["state"] == "CONFLICT"
            and r["after"]["rows"] == 6 and r["after"]["conflict_keys"] == 1, f"{r['state']} · 刪 {r['deleted']}")
        r2 = dedupe(db, apply=True, keep_last=True)
        con = duckdb.connect(str(db), read_only=True)
        v25 = con.execute(f"SELECT score FROM {TABLE} WHERE date = '2026-09-25'").fetchall()
        con.close()
        chk("③ --keep-last 同鍵留最後寫入的那一筆(51.0)→ CLEAN", r2["state"] == "OK" and r2["deleted"] == 1 and v25 == [(51.0,)], str(v25))
        r3 = dedupe(db, apply=True)
        led = (Path(td) / LEDGER_NAME).read_text(encoding="utf-8").splitlines()
        chk("④ 冪等:再跑 CLEAN 刪 0;帳只增(2 筆 apply)", r3["state"] == "CLEAN" and r3["deleted"] == 0 and len(led) == 2, f"帳 {len(led)} 筆")
        chk("⑤ 庫 / 表不在照實回", dedupe(Path(td) / "none.duckdb")["state"] == "NODB")
    keep = os.environ.pop("VIA_FROM_VCGC", None)
    denied = main(["dedupe"]) == 2
    if keep is not None:
        os.environ["VIA_FROM_VCGC"] = keep
    chk("⑥ dedupe 不經 VCGC 就拒跑", denied)
    print("  -- 前版自測 --")
    prior_ok = PRIOR.selftest() == 0
    chk("⑦ 前版自測鏈", prior_ok, _prior_path().name)
    ok = all(results)
    print(f"  [計] {ENGINE_TAG} 自測 {sum(results)}/{len(results)} · {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
