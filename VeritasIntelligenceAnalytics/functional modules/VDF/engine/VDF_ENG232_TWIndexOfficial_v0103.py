#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VDF_ENG232_TWIndexOfficial v0103 — 薄尾:寫庫前先確保欄型 · 加權某個月來源回空就停在那裡(不跳過、不留洞)。

2026-11-18 v0102 經 VDF 擷取系統在空湖庫上真跑,露出兩件:
  ① ConversionException: Unimplemented type for cast (DOUBLE -> "NULL") … inst_foreign_net
     表是第一批列建的;第一批的三大法人欄剛好全是空值,DuckDB 把欄型推成 NULL,之後有數字的列就寫不進去。
     (ENG054 v0106 修過同一類:日價表第一批全空 → 欄型推錯。)
  ② 加權 2023-10 整個月來源回空(剛打完櫃買 94 次請求,疑似限流)→ v0102 把 EMPTY 當成「沒有交易日」繼續抓下一個月
     → 中間留一個月的洞,而且增量起點只看最新日,之後永遠不會回補。
本版(v0102 一字不動):
  ① 寫庫前 ensure_schema():表不在 → 照 OUT-05 明示欄型建空表(數字欄 DOUBLE);表在但數字欄型是 NULL → 改成 DOUBLE
     (那一欄本來就全是空值,不動任何資料)。其他欄型一律不碰。
  ② 加權逐段抓時,某一段整段在過去、跨 5 天以上卻回空 → 狀態 GAP、停在那一段(rc 2);下一次從同一天接著抓。
     兩三天的空段(連假 / 週末)與迄日附近的空段照舊當成沒有交易日。
其餘(櫃買現行端點 · 各自接續 · 按月寫庫 · 舊端點自動停打)全照 v0102。不代設同意閘。
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。本檔自己不連網,連網的是回補本體。"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG232_TWIndexOfficial"
ENGINE_TAG = Path(__file__).stem
GAP_MIN_DAYS = 5          # 整段在過去、跨這麼多天還回空 = 來源沒回,不是沒有交易日
GAP_SETTLE_DAYS = 3       # 迄日往前這幾天內的空段不算洞(資料可能還沒出)
TEXT_COLS = ("date", "index_code", "index_name", "source", "note")
NUM_COLS = ("open", "low", "high", "close", "volume", "turnover", "inst_foreign_net", "inst_trust_net", "inst_dealer_net")


def _vnum(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location("_vdf_eng232_prior_for_" + ENGINE_TAG, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.BASE                        # v0100
_V2_RUN = PRIOR.run                      # v0102 的 run(櫃買先 · 加權按月)
_TAIEX_INNER = PRIOR._PRIOR_RUN          # v0101 的 run(加權一段)


def __getattr__(name):
    return getattr(PRIOR, name)


def ddl() -> str:
    cols = ["date VARCHAR", "index_code VARCHAR", "index_name VARCHAR"] + [c + " DOUBLE" for c in NUM_COLS] + ["source VARCHAR", "note VARCHAR"]
    return "CREATE TABLE IF NOT EXISTS %s (%s)" % (BASE.TABLE, ", ".join(cols))


def ensure_schema(db) -> dict:
    """表不在 → 明示欄型建空表;數字欄型是 NULL(整欄空值推出來的)→ 改 DOUBLE。回 {created, fixed}。其他一律不碰。"""
    import duckdb
    db = Path(db)
    db.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db))
    try:
        had = BASE.TABLE in {t for (t,) in con.execute("SHOW TABLES").fetchall()}
        con.execute(ddl())
        fixed = []
        for _cid, name, typ, *_rest in con.execute("PRAGMA table_info('%s')" % BASE.TABLE).fetchall():
            if name in NUM_COLS and str(typ).strip('"').upper() == "NULL":
                con.execute('ALTER TABLE %s ALTER COLUMN "%s" TYPE DOUBLE' % (BASE.TABLE, name))
                fixed.append(name)
        return {"created": not had, "fixed": fixed}
    finally:
        con.close()


def is_gap(a: str, b: str, end: str, state: str) -> bool:
    """這一段回空算不算洞:整段在迄日前 GAP_SETTLE_DAYS 天以前,而且跨 GAP_MIN_DAYS 天以上。"""
    if state != "EMPTY":
        return False
    da, db_, de = date.fromisoformat(a), date.fromisoformat(b), date.fromisoformat(end)
    return (db_ - da).days + 1 >= GAP_MIN_DAYS and db_ <= de - timedelta(days=GAP_SETTLE_DAYS)


def run(start=None, end=None, net=None, db=None, dry: bool = False, inner=None, http=None, echo=print, sleep=None) -> dict:
    db = db or BASE.DB_IDX
    end_s = end or date.today().isoformat()
    base_inner = inner or _TAIEX_INNER
    schema = {"created": False, "fixed": []} if dry else ensure_schema(db)
    if schema["fixed"]:
        echo("  [TW 指數] 欄型修正:%s 由 NULL 改 DOUBLE(整欄原本是空值,資料沒動)" % "、".join(schema["fixed"]), flush=True)

    def guard(a, b, net=None, db=None, dry=False):
        r = base_inner(a, b, net=net, db=db, dry=dry)
        if is_gap(a, b, end_s, r.get("state")):
            r = dict(r, state="GAP", note="這一段(%s → %s)來源回空;停在這裡,下次從同一天接著抓(不跳過)" % (a, b))
        return r

    res = _V2_RUN(start, end, net=net, db=db, dry=dry, inner=guard, http=http, echo=echo, sleep=sleep)
    res["schema"] = schema
    return res


PRIOR.run = run          # v0102 的 main 以模組全域叫 run()


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    if not BASE._allowed():
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "只經 VCGC(VIA_FROM_VCGC=YES)"}, ensure_ascii=False))
        return 2
    verb = next((x for x in a if not x.startswith("-")), "status")
    if verb == "run":
        import time as _time
        r = run(BASE._arg(a, "--start"), BASE._arg(a, "--end"), dry="--dry" in a, sleep=_time.sleep)
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return {"OK": 0, "UP_TO_DATE": 0, "DENY": 4, "EMPTY": 2, "GAP": 2}.get(r["state"], 1)
    return PRIOR.main(argv)


def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""))

    quiet = lambda *x, **k: None  # noqa: E731
    print("=== %s 薄尾自測(欄型 · 不留洞;零網路;庫只在暫存夾)===" % ENGINE_TAG)
    chk("① 洞的判法:過去的整個月回空 = 洞;兩天的空段(連假)不是;迄日附近的空段不是;有資料不是",
        is_gap("2023-10-01", "2023-10-31", "2026-11-18", "EMPTY") and not is_gap("2023-09-29", "2023-09-30", "2026-11-18", "EMPTY")
        and not is_gap("2026-11-01", "2026-11-18", "2026-11-18", "EMPTY") and not is_gap("2023-10-01", "2023-10-31", "2026-11-18", "OK"))
    try:
        import duckdb
        import pandas as pd
    except ImportError:
        duckdb = pd = None
    if duckdb is None:
        chk("② duckdb / pandas 在(不在就量不到欄型)", False, "缺件:SKIP 不是綠")
    else:
        row = lambda d, code, inst: {"date": d, "index_code": code, "index_name": "x", "open": 1.0, "low": 1.0, "high": 1.0, "close": 1.0, "volume": 1.0, "turnover": 1.0,  # noqa: E731
                                     "inst_foreign_net": inst, "inst_trust_net": inst, "inst_dealer_net": inst, "source": "s", "note": ""}
        with tempfile.TemporaryDirectory(prefix="eng232_v0103_") as td:
            bad = Path(td) / "bad.duckdb"
            con = duckdb.connect(str(bad))
            df = pd.DataFrame([row("2023-01-03", "TAIEX", None)])   # noqa: F841
            con.execute("CREATE TABLE %s AS SELECT * FROM df" % BASE.TABLE)
            typ0 = {n: str(t) for _c, n, t, *_ in con.execute("PRAGMA table_info('%s')" % BASE.TABLE).fetchall()}["inst_foreign_net"]
            err = ""
            try:
                con.execute("INSERT INTO %s (date, index_code, inst_foreign_net) VALUES ('2023-11-01', 'TAIEX', 12.5)" % BASE.TABLE)
            except Exception as exc:
                err = type(exc).__name__
            con.close()
            chk("② 負控:第一批法人欄全空 → 欄型被推成不能放數字的型,寫數字就倒(就是實測那個錯)", typ0.strip('"').upper() in ("NULL", "INTEGER") and bool(err), typ0 + " · " + err)
            sch = ensure_schema(bad)
            n_new = PRIOR._write(bad, [row("2023-11-01", "TAIEX", 12.5)])
            con = duckdb.connect(str(bad), read_only=True)
            typ1 = {n: str(t) for _c, n, t, *_ in con.execute("PRAGMA table_info('%s')" % BASE.TABLE).fetchall()}
            vals = con.execute("SELECT date, inst_foreign_net FROM %s ORDER BY date" % BASE.TABLE).fetchall()
            con.close()
            chk("③ ensure_schema:空值推出來的欄改 DOUBLE,原列不動,數字寫得進去", ("inst_foreign_net" in sch["fixed"] or typ0.strip('"').upper() != "NULL") and typ1["inst_foreign_net"] == "DOUBLE"
                and n_new == 1 and vals == [("2023-01-03", None), ("2023-11-01", 12.5)], "%s → %s · 修 %d 欄" % (typ0, typ1["inst_foreign_net"], len(sch["fixed"])))
            fresh = Path(td) / "fresh.duckdb"
            s1, s2 = ensure_schema(fresh), ensure_schema(fresh)
            con = duckdb.connect(str(fresh), read_only=True)
            types = {n: str(t) for _c, n, t, *_ in con.execute("PRAGMA table_info('%s')" % BASE.TABLE).fetchall()}
            con.close()
            chk("④ 表不在 → 明示欄型建空表(數字欄 DOUBLE · 文字欄 VARCHAR);再叫一次零動作", s1 == {"created": True, "fixed": []} and s2 == {"created": False, "fixed": []}
                and all(types[c] == "DOUBLE" for c in NUM_COLS) and all(types[c] == "VARCHAR" for c in TEXT_COLS) and len(types) == 14)
            calls = []

            def fake(a, b, net=None, db=None, dry=False):
                calls.append(a)
                if a.startswith("2023-10"):
                    return {"state": "EMPTY", "fetched": 0, "added": 0, "calls": 1}
                n = PRIOR._write(db, [row(b, "TAIEX", None if a < "2023-11" else 5.0)])
                return {"state": "OK", "fetched": 1, "added": n, "calls": 1}

            class NoTpex:
                def get_json(self, url, params=None, timeout=30):
                    return {}

            gapdb = Path(td) / "gap.duckdb"
            r = run("2023-08-01", "2023-12-31", inner=fake, http=NoTpex(), db=gapdb, echo=quiet)
            chk("⑤ 加權 10 月回空 → 停在 10 月(GAP),11、12 月沒被叫到;8、9 月已寫庫", r["state"] == "GAP" and calls == ["2023-08-01", "2023-09-01", "2023-10-01"]
                and BASE.count(gapdb).get("TAIEX", (0,))[0] == 2 and "2023-10-01" in str(r.get("stopped_at")), "%s · 停在 %s" % (r["state"], r.get("stopped_at")))
            chk("⑥ 下一次的加權增量起點仍在洞之前(會從 10 月接著抓,不會跳過)", PRIOR.starts(gapdb)["TAIEX"] == "2023-10-01", PRIOR.starts(gapdb)["TAIEX"])
            calls.clear()
            r2 = run("2023-08-01", "2023-12-31", inner=lambda a, b, **k: (calls.append(a), {"state": "OK", "fetched": 1, "added": PRIOR._write(k["db"], [row(b, "TAIEX", 7.0)]), "calls": 1})[1],
                     http=NoTpex(), db=Path(td) / "ok.duckdb", echo=quiet)
            chk("⑦ 沒有洞:五個月照常抓完,法人欄有數字也寫得進去", r2["state"] == "OK" and len(calls) == 5 and BASE.count(Path(td) / "ok.duckdb")["TAIEX"][0] == 5)
    chk("⑧ 裝進前版:v0102 的 main 叫到的就是本版的 run", PRIOR.run is run and callable(_V2_RUN) and callable(_TAIEX_INNER))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑨ 加速器橋真的匯入 · 網路工具橋在 · 不含本機路徑 · 不寫同意值 · 不刪列", "import VIA_SuperAccel_Module as VIA_ACCEL" in src and "via_net_unified_v*.py" in src
        and ("C:" + "\\Users") not in src and ("_CONSENT\"] " + "=") not in src and ("DELETE " + "FROM") not in src and ("DROP " + "TABLE") not in src)
    PRIOR.run = _V2_RUN
    try:
        rc = PRIOR.selftest()
    finally:
        PRIOR.run = run
    chk("⑩ 前版自測照過", rc == 0, "rc %s" % rc)
    good = all(ok)
    print("[計] %s 本版 %d/%d · %s" % (ENGINE_TAG, sum(ok), len(ok), "PASS" if good else "FAIL"))
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
