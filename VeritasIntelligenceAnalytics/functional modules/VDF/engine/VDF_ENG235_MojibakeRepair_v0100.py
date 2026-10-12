#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG235_MojibakeRepair v0100 — VDF 資料庫亂碼修復引擎(parquet 單元檔 · DuckDB 表;掃描 / 修復;備份只增;零網路)

操作員令(2026-10-12):「先把它修正為非亂碼 再回朔到擷取他的工具加上亂碼問題解碼器 解取實用一次 輸出實用一次」
  對象:via_database\vdf_database\tw__*.parquet · gl__*.parquet(ENG065 檔名協定的「原始表」單元)與它們匯入的 DuckDB 表。
判準 = 亂碼問題解碼器 SUP_MDL756_SmartDecode(demojibake / plan_values):一欄一種轉換(多數決),只有可信度明顯變好、
  結果沒有壞字、常用字命中才採用;含 U+FFFD 的值誠實列「不可逆」(位元組已丟,要回源重抓),不猜。
用法:
  scan <路徑>                       路徑 = 檔(.parquet / .duckdb)或資料夾(遞迴);只讀,出報告(燈:GREEN 乾淨 · YELLOW 可修 · RED 有不可逆)
  fix  <路徑> [--apply] [--backup-dir <夾>] [--no-db-backup] [--units-only]
       乾跑 = 只列計畫;--apply 才改:parquet 原檔先備份到 <夾>/_pre_mojibake/(同名已在 = 不覆蓋),再用 DuckDB 重寫
       (欄序 · 型別不變 · ZSTD · 列數核對);DuckDB 表先整檔備份(--no-db-backup 略過)再 UPDATE … FROM 對應表。
       --units-only 只動 <前綴>__<表>.parquet 單元檔(匯入引擎用)。
  --selftest
報告:VIA_Reports/vdf/mojibake/MOJIBAKE_SCAN_latest.json · MOJIBAKE_FIX_latest.json(+ *_runs.jsonl 只增);VIA_MOJIBAKE_OUT 可改報告夾。
零網路 · 不碰 TA-Lib · 不載 VCGC 程式(解碼器在 supportive modules/network,共用層)。
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。本檔零網路。"""
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
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import json
import os
import re
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA_ROOT = HERE.parents[2]
STEM = "VDF_ENG235_MojibakeRepair"
TAG = "v0100"
SCAN_LIMIT = 50000
FIX_LIMIT = 5000000
TEXT_TYPES = ("VARCHAR", "TEXT", "STRING", "CHAR", "BPCHAR")
_CODEC = {"mod": None, "why": None}


def _vnum(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _codec():
    """亂碼問題解碼器尾版(supportive modules/network/SUP_MDL756_SmartDecode_v*.py);缺 = None 並記原因。"""
    if _CODEC["mod"] is None and _CODEC["why"] is None:
        folder = VIA_ROOT / "supportive modules" / "network"
        hits = [p for p in folder.glob("SUP_MDL756_SmartDecode_v*.py") if _vnum(p) >= 0]
        if not hits:
            _CODEC["why"] = "SUP_MDL756_SmartDecode_v*.py 不在 %s" % folder
        else:
            try:
                p = max(hits, key=_vnum)
                spec = importlib.util.spec_from_file_location("smartdecode_for_" + STEM, p)
                mod = importlib.util.module_from_spec(spec)
                sys.modules["smartdecode_for_" + STEM] = mod
                spec.loader.exec_module(mod)
                _CODEC["mod"] = mod
            except Exception as exc:
                _CODEC["why"] = "解碼器載入炸 %s: %s" % (type(exc).__name__, str(exc)[:80])
    return _CODEC["mod"]


def _duckdb():
    try:
        import duckdb
        return duckdb
    except ImportError:
        return None


def _out_dir() -> Path:
    return Path(os.environ.get("VIA_MOJIBAKE_OUT") or (VIA_ROOT / "VIA_Reports" / "vdf" / "mojibake"))


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _q(name: str) -> str:
    return '"' + str(name).replace('"', '""') + '"'


def _esc(s: str) -> str:
    return str(s).replace("'", "''")


def targets(path, units_only: bool = False) -> list:
    """要看的對象:parquet 檔(kind parquet)· DuckDB 檔的每一張 BASE TABLE(kind duckdb);備份夾 _pre_mojibake 不算。"""
    p = Path(path)
    files = []
    if p.is_file():
        files = [p]
    elif p.is_dir():
        files = sorted(x for x in p.rglob("*") if x.is_file() and x.suffix.lower() in (".parquet", ".duckdb") and "_pre_mojibake" not in x.parts)
    out = []
    duckdb = _duckdb()
    for f in files:
        if f.suffix.lower() == ".parquet":
            if units_only and "__" not in f.stem:
                continue
            out.append({"kind": "parquet", "file": str(f), "table": None})
        elif f.suffix.lower() == ".duckdb" and duckdb is not None:
            try:
                con = duckdb.connect(str(f), read_only=True)
                try:
                    for (t,) in con.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='main' AND table_type='BASE TABLE' ORDER BY 1").fetchall():
                        out.append({"kind": "duckdb", "file": str(f), "table": t})
                finally:
                    con.close()
            except Exception as exc:
                out.append({"kind": "duckdb", "file": str(f), "table": None, "error": "%s: %s" % (type(exc).__name__, str(exc)[:100])})
    return out


def text_columns(con, rel: str) -> list:
    rows = con.execute("DESCRIBE SELECT * FROM %s" % rel).fetchall()
    return [(r[0], str(r[1])) for r in rows], [r[0] for r in rows if str(r[1]).upper().startswith(TEXT_TYPES)]


def _distinct(con, rel: str, col: str, limit: int) -> list:
    return [r[0] for r in con.execute("SELECT DISTINCT %s FROM %s WHERE %s IS NOT NULL LIMIT %d" % (_q(col), rel, _q(col), limit)).fetchall()]


def scan_rel(con, rel: str, limit: int) -> dict:
    """一個關係(parquet 檔 / 表)的欄計畫:只回有事的欄(可修或不可逆)。"""
    c = _codec()
    cols, text_cols = text_columns(con, rel)
    plans = []
    for col in text_cols:
        vals = _distinct(con, rel, col, limit)
        plan = c.plan_values(vals)
        if plan["kind"] or plan["n_unrecoverable"]:
            items = list(plan["map"].items())[:3]
            plans.append({"column": col, "distinct": len(vals), "kind": plan["kind"], "n_fix": plan["n_fix"], "n_unrecoverable": plan["n_unrecoverable"],
                          "kinds": plan["kinds"], "samples": [{"before": a, "after": b} for a, b in items], "map": plan["map"]})
    return {"columns": cols, "plans": plans}


def _lamp_of(plans: list) -> str:
    if any(p["n_unrecoverable"] for p in plans):
        return "RED"
    if any(p["n_fix"] for p in plans):
        return "YELLOW"
    return "GREEN"


def _write(report: dict, name: str, write: bool) -> Path | None:
    if not write:
        return None
    od = _out_dir()
    od.mkdir(parents=True, exist_ok=True)
    slim = json.loads(json.dumps(report, ensure_ascii=False, default=str))
    for t in slim.get("targets", []):
        for p in t.get("plans", []):
            p.pop("map", None)
    (od / ("%s_latest.json" % name)).write_text(json.dumps(slim, ensure_ascii=False, indent=1), encoding="utf-8")
    with (od / ("%s_runs.jsonl" % name)).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"ts": slim.get("ts"), "lamp": slim.get("lamp"), "targets": len(slim.get("targets", [])), "fixable": slim.get("fixable"),
                             "unrecoverable": slim.get("unrecoverable"), "changed_values": slim.get("changed_values"), "apply": slim.get("apply")}, ensure_ascii=False) + "\n")
    return od / ("%s_latest.json" % name)


def scan(path, limit: int = SCAN_LIMIT, units_only: bool = False, write: bool = True) -> dict:
    duckdb = _duckdb()
    rep = {"engine": "%s_%s" % (STEM, TAG), "verb": "scan", "ts": _now(), "path": str(path), "targets": [], "fixable": 0, "unrecoverable": 0, "lamp": "GREEN", "notes": []}
    if _codec() is None:
        rep.update(lamp="ABSENT", notes=[_CODEC["why"]])
        return rep
    if duckdb is None:
        rep.update(lamp="ABSENT", notes=["duckdb 不在家族境"])
        return rep
    for t in targets(path, units_only=units_only):
        row = dict(t)
        row.pop("map", None)
        if t.get("error"):
            row.update(lamp="RED", plans=[])
            rep["targets"].append(row)
            continue
        try:
            if t["kind"] == "parquet":
                con = duckdb.connect()
                rel = "read_parquet('%s')" % _esc(t["file"])
            else:
                con = duckdb.connect(t["file"], read_only=True)
                rel = _q(t["table"])
            try:
                r = scan_rel(con, rel, limit)
            finally:
                con.close()
        except Exception as exc:
            row.update(lamp="RED", plans=[], error="%s: %s" % (type(exc).__name__, str(exc)[:120]))
            rep["targets"].append(row)
            continue
        row["plans"] = r["plans"]
        row["lamp"] = _lamp_of(r["plans"])
        rep["fixable"] += sum(p["n_fix"] for p in r["plans"])
        rep["unrecoverable"] += sum(p["n_unrecoverable"] for p in r["plans"])
        rep["targets"].append(row)
    order = {"RED": 3, "YELLOW": 2, "GREEN": 1}
    rep["lamp"] = max((t.get("lamp", "GREEN") for t in rep["targets"]), key=lambda L: order.get(L, 0), default="GREEN")
    rep["report"] = str(_write(rep, "MOJIBAKE_SCAN", write) or "")
    return rep


def _rewrite_parquet(duckdb, file: Path, plans: list, backup_dir: Path) -> dict:
    """用對應表重寫 parquet:欄序 · 型別不變;先備份(同名已在 = 不覆蓋);列數核對後才換檔。"""
    con = duckdb.connect()
    try:
        rel = "read_parquet('%s')" % _esc(str(file))
        cols, _ = text_columns(con, rel)
        n0 = con.execute("SELECT COUNT(*) FROM %s" % rel).fetchone()[0]
        exprs, joins = [], []
        for i, p in enumerate(plans):
            if not p["map"]:
                continue
            con.execute("CREATE TEMP TABLE map_%d(orig VARCHAR, fixed VARCHAR)" % i)
            con.executemany("INSERT INTO map_%d VALUES (?, ?)" % i, list(p["map"].items()))
        by_col = {p["column"]: i for i, p in enumerate(plans) if p["map"]}
        for name, _typ in cols:
            if name in by_col:
                i = by_col[name]
                exprs.append("COALESCE(m%d.fixed, t.%s) AS %s" % (i, _q(name), _q(name)))
                joins.append("LEFT JOIN map_%d m%d ON t.%s = m%d.orig" % (i, i, _q(name), i))
            else:
                exprs.append("t.%s" % _q(name))
        tmp = file.with_suffix(".parquet.part")
        con.execute("COPY (SELECT %s FROM %s t %s) TO '%s' (FORMAT PARQUET, COMPRESSION ZSTD)" % (", ".join(exprs), rel, " ".join(joins), _esc(str(tmp))))
        n1 = con.execute("SELECT COUNT(*) FROM read_parquet('%s')" % _esc(str(tmp))).fetchone()[0]
        if n1 != n0:
            tmp.unlink(missing_ok=True)
            return {"ok": False, "why": "列數不同 %d → %d,不換檔" % (n0, n1)}
    finally:
        con.close()
    bk = backup_dir / "_pre_mojibake" / file.name
    bk.parent.mkdir(parents=True, exist_ok=True)
    if not bk.exists():
        shutil.copy2(file, bk)
    os.replace(tmp, file)
    return {"ok": True, "rows": n0, "backup": str(bk)}


def _update_duckdb(duckdb, file: Path, table: str, plans: list) -> dict:
    con = duckdb.connect(str(file))
    changed = 0
    try:
        for i, p in enumerate(plans):
            if not p["map"]:
                continue
            con.execute("CREATE TEMP TABLE map_%d(orig VARCHAR, fixed VARCHAR)" % i)
            con.executemany("INSERT INTO map_%d VALUES (?, ?)" % i, list(p["map"].items()))
            n = con.execute("SELECT COUNT(*) FROM %s WHERE %s IN (SELECT orig FROM map_%d)" % (_q(table), _q(p["column"]), i)).fetchone()[0]
            con.execute("UPDATE %s SET %s = m.fixed FROM map_%d m WHERE %s.%s = m.orig" % (_q(table), _q(p["column"]), i, _q(table), _q(p["column"])))
            changed += n
    finally:
        con.close()
    return {"ok": True, "changed_rows": changed}


def fix(path, apply: bool = False, backup_dir=None, db_backup: bool = True, units_only: bool = False, write: bool = True) -> dict:
    duckdb = _duckdb()
    rep = {"engine": "%s_%s" % (STEM, TAG), "verb": "fix", "ts": _now(), "path": str(path), "apply": apply, "targets": [], "fixable": 0, "unrecoverable": 0,
           "changed_values": 0, "files_rewritten": 0, "tables_updated": 0, "lamp": "GREEN", "notes": []}
    if _codec() is None or duckdb is None:
        rep.update(lamp="ABSENT", notes=[_CODEC["why"] or "duckdb 不在家族境"])
        return rep
    p0 = Path(path)
    bdir = Path(backup_dir) if backup_dir else (p0 if p0.is_dir() else p0.parent)
    db_backed = set()
    for t in targets(path, units_only=units_only):
        row = dict(t)
        if t.get("error"):
            row.update(lamp="RED", plans=[])
            rep["targets"].append(row)
            continue
        try:
            if t["kind"] == "parquet":
                con = duckdb.connect()
                rel = "read_parquet('%s')" % _esc(t["file"])
            else:
                con = duckdb.connect(t["file"], read_only=True)
                rel = _q(t["table"])
            try:
                r = scan_rel(con, rel, FIX_LIMIT)
            finally:
                con.close()
        except Exception as exc:
            row.update(lamp="RED", plans=[], error="%s: %s" % (type(exc).__name__, str(exc)[:120]))
            rep["targets"].append(row)
            continue
        plans = r["plans"]
        n_fix = sum(p["n_fix"] for p in plans)
        rep["fixable"] += n_fix
        rep["unrecoverable"] += sum(p["n_unrecoverable"] for p in plans)
        row["plans"] = [{k: v for k, v in p.items() if k != "map"} for p in plans]
        row["lamp"] = _lamp_of(plans)
        row["action"] = "NONE" if not n_fix else ("PLAN" if not apply else "")
        if n_fix and apply:
            try:
                if t["kind"] == "parquet":
                    res = _rewrite_parquet(duckdb, Path(t["file"]), plans, bdir)
                    row["action"] = "REWRITTEN" if res.get("ok") else "FAIL"
                    if res.get("ok"):
                        rep["files_rewritten"] += 1
                        rep["changed_values"] += n_fix
                        row["backup"] = res["backup"]
                    else:
                        row["why"] = res.get("why")
                else:
                    f = Path(t["file"])
                    if db_backup and str(f) not in db_backed:
                        bk = bdir / "_pre_mojibake" / f.name
                        bk.parent.mkdir(parents=True, exist_ok=True)
                        if not bk.exists():
                            shutil.copy2(f, bk)
                        row["backup"] = str(bk)
                        db_backed.add(str(f))
                    res = _update_duckdb(duckdb, f, t["table"], plans)
                    row["action"] = "UPDATED"
                    row["changed_rows"] = res["changed_rows"]
                    rep["tables_updated"] += 1
                    rep["changed_values"] += n_fix
            except Exception as exc:
                row.update(action="FAIL", why="%s: %s" % (type(exc).__name__, str(exc)[:160]))
        rep["targets"].append(row)
    order = {"RED": 3, "YELLOW": 2, "GREEN": 1}
    rep["lamp"] = max((t.get("lamp", "GREEN") for t in rep["targets"]), key=lambda L: order.get(L, 0), default="GREEN")
    if apply and rep["fixable"] and not any(t.get("action") == "FAIL" for t in rep["targets"]) and not rep["unrecoverable"]:
        rep["lamp"] = "GREEN"
    rep["report"] = str(_write(rep, "MOJIBAKE_FIX", write) or "")
    return rep


def _print(rep: dict) -> None:
    for t in rep.get("targets", []):
        name = Path(t["file"]).name + ((":" + t["table"]) if t.get("table") else "")
        if t.get("error"):
            print("  [RED  ] %s · %s" % (name, t["error"]))
            continue
        plans = t.get("plans", [])
        if not plans:
            print("  [GREEN] %s · 文字欄乾淨" % name)
            continue
        for p in plans:
            smp = " · ".join("%s→%s" % (s["before"][:12], s["after"][:12]) for s in p.get("samples", [])[:2])
            print("  [%-6s] %s.%s · 可修 %d(%s)· 不可逆 %d · %s %s" % (t.get("lamp", "?"), name, p["column"], p["n_fix"], p["kind"] or "-", p["n_unrecoverable"], t.get("action", ""), smp))
    print("[計] %s_%s %s · %s · 對象 %d · 可修值 %d · 不可逆 %d%s · 報告 %s" % (
        STEM, TAG, rep.get("verb"), rep.get("lamp"), len(rep.get("targets", [])), rep.get("fixable", 0), rep.get("unrecoverable", 0),
        (" · 已改 %d(檔 %d · 表 %d)" % (rep["changed_values"], rep["files_rewritten"], rep["tables_updated"])) if rep.get("apply") else " · 乾跑(加 --apply 才改)" if rep.get("verb") == "fix" else "",
        rep.get("report") or "-"))


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        return selftest()
    if not args or args[0] not in ("scan", "fix") or len(args) < 2:
        print(__doc__)
        return 2
    verb, path = args[0], args[1]
    apply = "--apply" in args
    units_only = "--units-only" in args
    db_backup = "--no-db-backup" not in args
    bdir = args[args.index("--backup-dir") + 1] if "--backup-dir" in args and args.index("--backup-dir") + 1 < len(args) else None
    rep = scan(path, units_only=units_only) if verb == "scan" else fix(path, apply=apply, backup_dir=bdir, db_backup=db_backup, units_only=units_only)
    _print(rep)
    return {"GREEN": 0, "YELLOW": 2, "RED": 1, "ABSENT": 3}.get(rep.get("lamp"), 1)


def selftest() -> int:
    import tempfile
    p = f = 0

    def chk(name, cond, note=""):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s%s" % (name, (" · " + str(note)[:300]) if note else ""))

    print("=== %s %s · 自測(暫存 parquet / DuckDB · 零網路)===" % (STEM, TAG))
    duckdb = _duckdb()
    c = _codec()
    chk("① 解碼器 SUP_MDL756 尾版 + duckdb 都在", c is not None and duckdb is not None, _CODEC["why"])
    if c is None or duckdb is None:
        print("[計] %s_%s 自測 %d/%d · FAIL" % (STEM, TAG, p, p + f))
        return 1
    td = Path(tempfile.mkdtemp(prefix="pv_vdf235_"))
    keep = os.environ.get("VIA_MOJIBAKE_OUT")
    os.environ["VIA_MOJIBAKE_OUT"] = str(td / "out")
    try:
        zh = ["台積電", "鴻海", "聯發科", "中華電"]
        moj_u = [s.encode("utf-8").decode("latin-1") for s in zh]
        moj_b = [s.encode("cp950").decode("latin-1") for s in ["半導體", "電子零組件", "電信"]]
        rows = [("2330", moj_u[0], moj_b[0], 1), ("2317", moj_u[1], moj_b[1], 2), ("2454", moj_u[2], moj_b[0], 3), ("2412", moj_u[3], moj_b[2], 4),
                ("2308", "台達電", "電子\ufffd壞", 5), ("TSMC", "TSMC ADR", "ascii only", 6)]
        unit = td / "tw__demo.parquet"
        con = duckdb.connect()
        con.execute("CREATE TABLE a(code VARCHAR, name VARCHAR, industry VARCHAR, n INTEGER)")
        con.executemany("INSERT INTO a VALUES (?, ?, ?, ?)", rows)
        con.execute("COPY a TO '%s' (FORMAT PARQUET, COMPRESSION ZSTD)" % _esc(str(unit)))
        other = td / "other.parquet"
        con.execute("COPY (SELECT code, name FROM a) TO '%s' (FORMAT PARQUET)" % _esc(str(other)))
        con.close()
        s1 = scan(td)
        pl = {(Path(t["file"]).name, q["column"]): q for t in s1["targets"] for q in t["plans"]}
        chk("② scan:name 欄 latin1->utf8 可修 4 · industry 欄 latin1->cp950 可修 3 + 不可逆 1 · 總燈 RED(有不可逆)· 報告寫出",
            s1["lamp"] == "RED" and pl.get(("tw__demo.parquet", "name"), {}).get("kind") == "latin1->utf8" and pl[("tw__demo.parquet", "name")]["n_fix"] == 4
            and pl.get(("tw__demo.parquet", "industry"), {}).get("kind") == "latin1->cp950" and pl[("tw__demo.parquet", "industry")]["n_fix"] == 3
            and pl[("tw__demo.parquet", "industry")]["n_unrecoverable"] == 1 and (td / "out" / "MOJIBAKE_SCAN_latest.json").is_file(), {k: (v["kind"], v["n_fix"], v["n_unrecoverable"]) for k, v in pl.items()})
        sha0 = unit.read_bytes()
        d1 = fix(td, apply=False)
        chk("③ fix 乾跑:只列計畫(PLAN)· 檔不動", d1["changed_values"] == 0 and all(t.get("action") in ("PLAN", "NONE") for t in d1["targets"]) and unit.read_bytes() == sha0)
        d2 = fix(td, apply=True, backup_dir=td / "bk")
        con = duckdb.connect()
        got = con.execute("SELECT code, name, industry, n FROM read_parquet('%s') ORDER BY n" % _esc(str(unit))).fetchall()
        typ = con.execute("DESCRIBE SELECT * FROM read_parquet('%s')" % _esc(str(unit))).fetchall()
        con.close()
        names = [r[1] for r in got]
        inds = [r[2] for r in got]
        chk("④ fix --apply:name 四值還原正字 · industry 三值還原、U+FFFD 那值原樣(不猜)· 非文字欄與欄序 / 型別不變 · 備份在 _pre_mojibake · 列數核對",
            names[:4] == zh and names[4:] == ["台達電", "TSMC ADR"] and inds[:4] == ["半導體", "電子零組件", "半導體", "電信"] and inds[4] == "電子\ufffd壞"
            and [r[3] for r in got] == [1, 2, 3, 4, 5, 6] and [t[0] for t in typ] == ["code", "name", "industry", "n"] and str(typ[3][1]).upper().startswith("INT")
            and (td / "bk" / "_pre_mojibake" / "tw__demo.parquet").read_bytes() == sha0 and d2["files_rewritten"] == 2 and d2["changed_values"] >= 7, (names, inds, d2.get("lamp")))
        d3 = fix(td, apply=True, backup_dir=td / "bk")
        chk("⑤ 冪等:再修 0 值 · 燈 RED(不可逆仍在,誠實)· 備份不覆蓋", d3["changed_values"] == 0 and d3["lamp"] == "RED" and (td / "bk" / "_pre_mojibake" / "tw__demo.parquet").read_bytes() == sha0, (d3["changed_values"], d3["lamp"]))
        db = td / "vdf_demo.duckdb"
        con = duckdb.connect(str(db))
        con.execute("CREATE TABLE tw_listings(code VARCHAR, name VARCHAR, n INTEGER)")
        con.executemany("INSERT INTO tw_listings VALUES (?, ?, ?)", [("2330", moj_u[0], 1), ("2317", moj_u[1], 2), ("2317", moj_u[1], 3), ("2308", "台達電", 4)])
        con.close()
        d4 = fix(db, apply=True, backup_dir=td / "bk")
        con = duckdb.connect(str(db), read_only=True)
        got2 = con.execute("SELECT name FROM tw_listings ORDER BY n").fetchall()
        con.close()
        t4 = [t for t in d4["targets"] if t.get("table") == "tw_listings"]
        chk("⑥ DuckDB 表:UPDATE … FROM 對應表(同值多列一起改)· 整檔備份 · 燈 GREEN",
            [r[0] for r in got2] == ["台積電", "鴻海", "鴻海", "台達電"] and t4 and t4[0].get("action") == "UPDATED" and t4[0].get("changed_rows") == 3
            and (td / "bk" / "_pre_mojibake" / "vdf_demo.duckdb").is_file() and d4["lamp"] == "GREEN", (got2, t4[:1], d4["lamp"]))
        other2 = td / "u2" / "other.parquet"
        other2.parent.mkdir()
        shutil.copy2(other, other2)
        shutil.copy2(td / "bk" / "_pre_mojibake" / "tw__demo.parquet", td / "u2" / "tw__demo.parquet")
        s_u = scan(td / "u2", units_only=True)
        s_all = scan(td / "u2", units_only=False)
        chk("⑦ --units-only 只看 <前綴>__<表>.parquet 單元檔", [Path(t["file"]).name for t in s_u["targets"]] == ["tw__demo.parquet"] and len(s_all["targets"]) == 2)
        body = Path(__file__).read_text(encoding="utf-8")
        chk("⑧ 橋在(ACCEL + NET,__future__ 之後)· 零網路 · 不碰 TA-Lib · 不載 VCGC 程式 · 不用 replace / ignore 解碼",
            all(x in body for x in ("[VIA:ACCEL-BRIDGE:v0100]", "[VIA:NET-BRIDGE:v0100]")) and body.index("from __future__") < body.index("[VIA:ACCEL-BRIDGE:v0100]")
            and all(x not in body for x in ("import " + "requests", "import " + "urllib", "import " + "talib", "CGC_MDL" + "1", "CGC_MDL" + "2"))
            and ', "rep' + 'lace")' not in body and 'errors="ign' + 'ore"' not in body)
    finally:
        if keep is None:
            os.environ.pop("VIA_MOJIBAKE_OUT", None)
        else:
            os.environ["VIA_MOJIBAKE_OUT"] = keep
        shutil.rmtree(td, ignore_errors=True)
    print("[計] %s_%s 自測 %d/%d · %s" % (STEM, TAG, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
