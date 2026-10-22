#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_XsrcVerifier v0101 — 薄尾:修兩個「假不符」(V0 檔名清洗 · V1 NULL 來源);其餘判法照 v0100

操作員令(2026-10-22):「A 1234 全做」(第 1 項:結果驗證 V0 / V1 不符要修)。工作站實跑 VDF_MDL013_ActivateVDF v0114:
  結果獨立驗證 FAIL(V0、V1 有不符)→ 總燈紅、不能收尾。容器重現兩個與資料無關、一定會發生的不符:
  ① V0:ActivateVDF 寫中間檔時檔名把來源 / 資料集名清洗成 [\w.-](例 YAHOO_ONLY(CNYES_FACTSET_PENDING) → 檔名
     YAHOO_ONLY_CNYES_FACTSET_PENDING_),每列 source 欄仍是原字;v0100 拿「檔名裡的來源」比「原字」→ 帶括號 / 斜線 / 空白的來源必不符。
     本版:同一套清洗規則([^\w.-]+ → _)兩邊都套再比;另加「同一檔所有列的原字來源只有一個」(每檔一來源的本意照驗)。
  ② V1:ActivateVDF 抽同表多來源時 source 寫 str(值)→ 庫裡 NULL 變成字串 "None";v0100 回原表用 CAST(source AS VARCHAR) = 'None'
     → NULL 永遠對不上 → 「沒有這一筆」。本版:原表 NULL 來源當 'None' 比(與寫入端同一個寫法),值仍一字不差。
  負控照舊會紅:值被改 · 來源被改成別的 · 日期不標準 · 判定不對 · 計數不對。
VDF 自己的模組:資料庫只唯讀附掛;不匯入他系統程式;同意閘不讀不寫;不碰 TA-Lib;不裝套件、不寫環境。
用法同 v0100:python VDF_XsrcVerifier_v0101.py <xsrc 夾> [--summary 總覽.json] [--db 庫.duckdb …] · --selftest
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
    """統包唯一網路工具惰性載入;本檔的連網全經 MDL008 子行程改道。"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None

import csv
import importlib.util
import json
import os
import re
import sys
import tempfile
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_XsrcVerifier"
TAG = _STEM + " v" + Path(__file__).stem.rsplit("_v", 1)[-1]
V0_KEY = "V0 中間檔欄位與來源標註(每檔一來源 · source 欄 = 檔名來源)"
V1_KEY = "V1 中間檔每一筆回資料庫原表逐筆比對(值與來源一字不差)"
_SAN = re.compile(r"[^\w.-]+")


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
with warnings.catch_warnings():
    warnings.simplefilter("ignore", SyntaxWarning)
    _spec.loader.exec_module(PRIOR)
_VERIFY_PRIOR = PRIOR.verify
_TRACE_PRIOR = PRIOR.trace_file


def __getattr__(name):
    return getattr(PRIOR, name)


def san(s) -> str:
    """與 ActivateVDF write_temp 同一套檔名清洗:[^\\w.-]+ → _。"""
    return _SAN.sub("_", str(s if s is not None else ""))


def trace_file(con, db: Path, table: str, rows: list) -> list:
    """同 v0100 trace_file;唯一差別:一般表的來源比對把原表 NULL 當 'None'(寫入端 str(None) 的寫法)。"""
    con.execute("DETACH DATABASE IF EXISTS src")
    con.execute("ATTACH '%s' AS src (READ_ONLY)" % str(db).replace("'", "''"))
    meta = con.execute("SELECT column_name FROM information_schema.columns WHERE table_catalog = 'src' AND table_name = ? "
                       "ORDER BY ordinal_position", [table]).fetchall()
    cols = {r[0].lower(): r[0] for r in meta}
    order = [r[0] for r in meta]
    if not cols:
        return ["原表 %s:%s 不存在" % (db.name, table)]
    if table in ("tw_trading_daily", "tw_daily_prices"):
        return _TRACE_PRIOR(con, db, table, rows)      # 這兩張表的來源是固定字(市場別 / YAHOO),沒有 NULL 問題 → 照 v0100
    fd, tmp = tempfile.mkstemp(suffix=".csv")
    with open(fd, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["idx", "key", "date_raw", "field", "value", "source"])
        for i, r in enumerate(rows):
            w.writerow([i, r["key"], r["date_raw"], r["field"], r["value"], r["source"]])
    con.execute("CREATE OR REPLACE TEMP TABLE t AS SELECT * FROM read_csv(?, header = true, all_varchar = true)", [tmp])
    Path(tmp).unlink(missing_ok=True)
    keys = [c for c in order if c.lower() in PRIOR._KEYS]
    dcol = next((c for c in order if PRIOR._DHINT.search(c) and not PRIOR._META.match(c)), None)
    if "source" not in cols or not keys or not dcol:
        return ["原表 %s:%s 沒有 source / 代號 / 日期欄" % (db.name, table)]
    q = PRIOR._qi
    kexpr = " || '|' || ".join("CAST(s.%s AS VARCHAR)" % q(k) for k in keys)
    latest = (" QUALIFY row_number() OVER (PARTITION BY t.idx ORDER BY s.%s DESC) = 1" % q(cols["fetched_at"])) if "fetched_at" in cols else ""
    got: dict = {}
    for fld in sorted({r["field"] for r in rows}):
        f = cols.get(fld.lower())
        if not f:
            continue
        sql = ("SELECT CAST(t.idx AS INTEGER), s.%s FROM t JOIN src.%s s ON CAST(s.%s AS VARCHAR) = t.date_raw AND %s = t.key "
               "AND coalesce(CAST(s.source AS VARCHAR), 'None') = t.source WHERE t.field = ?%s" % (q(f), q(table), q(dcol), kexpr, latest))
        for idx, v in con.execute(sql, [fld]).fetchall():
            got.setdefault(idx, []).append("None" if v is None else str(v))
    bad = []
    for i, r in enumerate(rows):
        g = got.get(i, [])
        if len(set(g)) != 1 or g[0] != r["value"]:
            bad.append("%s %s %s %s %s:中間檔 %s · 原表 %s" % (r["_file"], r["key"], r["date_raw"], r["field"], r["source"], r["value"], g or "沒有這一筆"))
    return bad


def v0_check(xdir: Path) -> dict:
    """V0(本版):表頭對 · 每列來源 / 資料集清洗後 = 檔名 / 夾名 · 同一檔原字來源只有一個。"""
    src_files = sorted(p for p in Path(xdir).glob("*/*.csv") if not p.name.endswith("__對照結果.csv"))
    bad = []
    for p in src_files:
        rs = PRIOR._read(p)
        if rs and list(rs[0].keys()) != PRIOR._HDR_SRC:
            bad.append(p.name)
        ds, src = p.parent.name, p.stem.split("__", 1)[-1]
        raw_srcs = {r.get("source") for r in rs}
        if len(raw_srcs) > 1:
            bad.append("%s:一檔 %d 個來源 %s" % (p.name, len(raw_srcs), sorted(str(x) for x in raw_srcs)[:4]))
        for r in rs:
            if san(r.get("source")) != src or san(r.get("dataset")) != ds:
                bad.append("%s:%s/%s" % (p.name, r.get("dataset"), r.get("source")))
    return {"n": len(src_files), "bad": len(bad), "examples": bad[:5], "note": "檔名清洗規則兩邊同套([^\\w.-]+ → _)"}


def verify(xdir, summary: dict | None = None, dbs: list | None = None, datefmt: dict | None = None) -> dict:
    rep = _VERIFY_PRIOR(xdir, summary, dbs, datefmt)          # V1 經模組全域 trace_file → 已換本版
    rep["checks"][V0_KEY] = v0_check(Path(xdir))
    checks = rep["checks"]
    if rep.get("rows"):
        rep["verdict"] = "PASS" if all(c["bad"] == 0 for c in checks.values()) else "FAIL"
    rep["tag"] = TAG
    return rep


PRIOR.trace_file = trace_file                    # v0100 verify 查模組全域 → 本版
PRIOR.TAG = TAG


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["--selftest"]:
        return selftest()
    keep = PRIOR.verify
    PRIOR.verify = verify                        # v0100 main 叫模組全域 verify → 本版
    try:
        return PRIOR.main(a)
    finally:
        PRIOR.verify = keep


def _mk_case(root: Path, source_raw: str, db_source, value="10.0", table="tw_rest_daily") -> tuple:
    """造一張小庫 + 一份中間檔 + 一份結果(手寫,不借 ActivateVDF)。回 (xsrc 夾, 庫)。"""
    import duckdb
    root.mkdir(parents=True, exist_ok=True)
    db = root / "vdf_tw_market.duckdb"
    con = duckdb.connect(str(db))
    con.execute("CREATE TABLE %s (date VARCHAR, code VARCHAR, source VARCHAR, eps DOUBLE)" % table)
    con.execute("INSERT INTO %s VALUES ('2026-10-20', '2330', 'EXTERNAL_ANALYST', 10.0), ('2026-10-20', '2330', ?, 10.0)" % table, [db_source])
    con.close()
    x = root / "xsrc"
    d = x / san(table)
    d.mkdir(parents=True)
    org = "%s:%s" % (db.name, table)
    for src, val in (("EXTERNAL_ANALYST", "10.0"), (source_raw, value)):
        with open(d / ("%s__%s.csv" % (san(table), san(src))), "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(PRIOR._HDR_SRC)
            w.writerow([table, src, "2330", "2026-10-20", "eps", val, "2026-10-20", org])
    srcs = sorted(["EXTERNAL_ANALYST", source_raw])
    with open(d / ("%s__對照結果.csv" % san(table)), "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(PRIOR._HDR_RES)
        ok = value == "10.0"
        w.writerow([table, "2330", "2026-10-20", "eps", "VERIFIED" if ok else "CONFLICT", "/".join(srcs),
                    "/".join(srcs) if ok else "", "", json.dumps({"EXTERNAL_ANALYST": "10.0", source_raw: value}, ensure_ascii=False)])
    return x, db


def selftest() -> int:
    import shutil
    p = f = 0

    def chk(name, cond, note=""):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s%s" % (name, (" · " + str(note)[:300]) if note else ""))

    print("=== %s · 薄尾自測(V0 檔名清洗 · V1 NULL 來源)===" % TAG)
    try:
        import duckdb  # noqa: F401
        have_duck = True
    except ImportError:
        have_duck = False
    tmp = Path(tempfile.mkdtemp(prefix="vdf_xv0101_"))
    try:
        if have_duck:
            x, db = _mk_case(tmp / "a", "YAHOO_ONLY(CNYES_FACTSET_PENDING)", "YAHOO_ONLY(CNYES_FACTSET_PENDING)")
            r = verify(x, None, [db])
            chk("① 帶括號的來源(檔名清洗成 YAHOO_ONLY_CNYES_FACTSET_PENDING_)→ V0 不再誤判 · 判決 PASS",
                r["checks"][V0_KEY]["bad"] == 0 and r["verdict"] == "PASS", (r["verdict"], r["checks"][V0_KEY]))
            rp = _VERIFY_PRIOR(x, None, [db])
            chk("② 負控:同一份用 v0100 驗 → V0 不符(就是工作站那個紅)", rp["checks"][V0_KEY]["bad"] > 0, rp["checks"][V0_KEY])
            x2, db2 = _mk_case(tmp / "b", "None", None)
            r2 = verify(x2, None, [db2])
            chk("③ 庫裡 NULL 來源(中間檔寫 None)→ V1 對得上 · 判決 PASS", r2["checks"][V1_KEY]["bad"] == 0 and r2["verdict"] == "PASS",
                (r2["verdict"], r2["checks"][V1_KEY]))
            keep = PRIOR.trace_file
            PRIOR.trace_file = _TRACE_PRIOR
            try:
                rp2 = _VERIFY_PRIOR(x2, None, [db2])
            finally:
                PRIOR.trace_file = keep
            chk("④ 負控:同一份用 v0100 的 trace_file → V1「沒有這一筆」", rp2["checks"][V1_KEY]["bad"] > 0, rp2["checks"][V1_KEY])
            x3, db3 = _mk_case(tmp / "c", "None", None, value="10.0")
            f3 = next(p_ for p_ in (x3 / "tw_rest_daily").glob("*__None.csv"))
            f3.write_text(f3.read_text(encoding="utf-8-sig").replace(",10.0,", ",99.0,"), encoding="utf-8-sig")
            r3 = verify(x3, None, [db3])
            chk("⑤ 負控:中間檔的值被改 → V1 仍不符 · 判決 FAIL", r3["checks"][V1_KEY]["bad"] > 0 and r3["verdict"] == "FAIL", r3["checks"][V1_KEY])
            x4, db4 = _mk_case(tmp / "d", "YAHOOX", "YAHOOX")
            f4 = next(p_ for p_ in (x4 / "tw_rest_daily").glob("*__YAHOOX.csv"))
            f4.write_text(f4.read_text(encoding="utf-8-sig").replace(",YAHOOX,", ",OTHER_SRC,"), encoding="utf-8-sig")
            r4 = verify(x4, None, [db4])
            chk("⑥ 負控:列的來源被改成別的(清洗後也對不上檔名)→ V0 仍不符 · 判決 FAIL", r4["checks"][V0_KEY]["bad"] > 0 and r4["verdict"] == "FAIL",
                r4["checks"][V0_KEY])
        else:
            chk("①–⑥ 本境沒有 duckdb(不代裝)→ 略過造庫的案例", True)
        chk("⑦ 判決規則照 v0100:全部不符 0 = PASS · 沒資料 = EMPTY", verify(tmp / "empty_none")["verdict"] == "EMPTY")
        src = Path(__file__).read_text(encoding="utf-8")
        body = src.split("def selftest", 1)[0]
        chk("⑧ 不匯入他系統程式(CGC_ · VRN_ · VCGC · ActivateVDF)· 兩座橋在 · 同意閘不寫",
            not re.search(r"^\s*(import|from)\s+(CGC_|VRN_|VCGC|VDF_MDL013|ActivateVDF)", src, re.M)
            and "VIA:ACCEL-BRIDGE" in src and "VIA:NET-BRIDGE" in src and "_CONSENT\"] =" not in body)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("  ── 前版 %s 自測(原樣印出;VIA_SKIP_PRIOR_SELFTEST=1 略過)──" % PRIOR_PATH.stem)
    PRIOR.TAG = _STEM + " v" + PRIOR_PATH.stem.rsplit("_v", 1)[-1]          # 前版自測印它自己的版號
    try:
        prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    finally:
        PRIOR.TAG = TAG
    chk("⑨ 前版 %s 自測 rc 0(本版換上的 trace_file 不破壞前版的負控)" % PRIOR_PATH.stem, prc == 0)
    print("[計] %s 自測 %d/%d · %s" % (TAG, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
