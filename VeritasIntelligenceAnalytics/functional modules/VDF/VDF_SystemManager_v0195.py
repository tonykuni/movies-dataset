#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF SystemManager v0195 — 薄尾(v0194 以前一字不動):輸出的驗證 + 確認(對表頭冊)併進 vv,另有獨立動詞 outputs

操作員 2026-11-27(手機):「Ensure output should pass verification and validation」。驗收定義(CLAUDE.md):輸出要對表頭冊驗過。
v0194 的 vv 沒有看輸出本身。本版:
  outputs [--home 夾] [--json]          VDF 資料平面冊上的每個輸出(MDL020 尾版 book_outputs,22 個)逐一:
     ① 契約(哪台都跑):表頭冊(VIA_Output_Header_SSOT 尾版,共用 SSOT,只讀)有沒有這張表的表頭 —— 依 (庫檔名, 表名) / parquet 檔名對。
     ② 實測(找得到資料家才跑 = 主機):唯讀開輸出庫(duckdb read_only)→ DESCRIBE + 列數,對表頭:
          缺必填欄 / 缺鍵欄 = 紅 · 型別不合 / 列數 < min_rows / 庫或表還沒擷取 = 黃 · 全對 = 綠。
          沒有表頭的表:照實際欄位寫一份表頭草稿(只含 schema:欄名 · 型別 · 是否鍵;不含任何資料值)到
          VIA_Reports/vdf/manager/HEADER_PROPOSALS_latest.json,交 VCGC 收進表頭冊(VDF 不寫 VCGC 的冊)。
     資料家照 MDL020 的 resolve_home(--home > env VIA_VDF_DB_HOME > VDF_DataHome_SSOT);找不到 = 實測灰(容器就是這樣),不假綠。
  vv                                     ② 結構確認多一格「outputs」(就是上面這個),其餘照 v0194(三流程同時跑)。
系統獨立:不 import 任何 VCGC 程式;表頭冊讀不到 = 契約灰(照實),VDF 照常跑。資料不離開本機;零網路;不碰 TA-Lib;不設同意閘。
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(VDF 全導入令;惰性載入=import 時零網路、零行為變更) =====
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
except Exception:  # noqa: BLE001
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT;網路只認 AegisNexus);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

VERSION = "v0195"
STEM = "VDF_SystemManager"
TAG = f"VDF_SystemManager {VERSION}"
HERE = Path(__file__).resolve().parent


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)                 # v0194(vv · 三流程)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


# ── 型別:DuckDB → 表頭冊六類 ─────────────────────────────────────────────
def h_type(duck: str) -> str:
    t = (duck or "").upper()
    if t.startswith(("VARCHAR", "TEXT", "STRING", "CHAR", "UUID", "BPCHAR")):
        return "str"
    if t.startswith("TIMESTAMP") or t == "DATETIME":
        return "datetime"
    if t == "DATE":
        return "date"
    if t.startswith("BOOL"):
        return "bool"
    if any(x in t for x in ("DOUBLE", "FLOAT", "REAL", "DECIMAL", "NUMERIC")):
        return "float"
    if "INT" in t:
        return "int"
    return "json"


COMPAT = {"float": {"float", "int"}, "datetime": {"datetime", "date"}, "date": {"date", "datetime"}}


def type_ok(want: str, got: str) -> bool:
    return got == want or got in COMPAT.get(want, set())


# ── 冊 ──────────────────────────────────────────────────────────────────
def _tail(folder: Path, pattern: str) -> Path | None:
    hits = [p for p in folder.glob(pattern) if _vnum(p.with_suffix("")) >= 0]
    return max(hits, key=lambda p: _vnum(p.with_suffix(""))) if hits else None


def header_book(root: Path) -> tuple:
    p = _tail(root / "supportive modules" / "registry", "VIA_Output_Header_SSOT_v*.json")
    if p is None:
        return {}, "表頭冊不在(VIA_Output_Header_SSOT_v*)"
    try:
        return json.loads(p.read_text(encoding="utf-8")).get("tables") or {}, p.name
    except (OSError, ValueError) as exc:
        return {}, f"表頭冊讀不了:{type(exc).__name__}"


def dataplane(root: Path):
    """VDF 自己的資料平面模組(MDL020 尾版):book_outputs · P.resolve_home。"""
    d = root / "functional modules" / "VDF"
    p = _tail(d, "VDF_MDL020_DataPlane_v*.py")
    s = importlib.util.spec_from_file_location("vdf_dp_for_v0195", p)
    m = importlib.util.module_from_spec(s)
    sys.modules[s.name] = m
    s.loader.exec_module(m)
    return m


def header_index(tables: dict) -> dict:
    idx = {}
    for tid, s in tables.items():
        src = s.get("source") or {}
        base = os.path.basename(str(src.get("path") or ""))
        if src.get("kind") == "duckdb":
            idx[("db", base, src.get("table"))] = (tid, s)
        elif src.get("kind") == "parquet":
            idx[("file", base, None)] = (tid, s)
    return idx


def match(o: dict, idx: dict):
    if o.get("db"):
        return idx.get(("db", o["db"], o.get("table")))
    return idx.get(("file", o.get("file"), None))


# ── 實測 ────────────────────────────────────────────────────────────────
def measure(o: dict, home: Path) -> dict:
    """唯讀:DESCRIBE + 列數。回 {exists, columns:[(名, 表頭型別, 原型別)], rows} 或 {exists: False, why}。"""
    import duckdb
    try:
        if o.get("db"):
            db = home / o["db"]
            if not db.is_file():
                return {"exists": False, "why": f"庫 {o['db']} 還沒有(未擷取)"}
            con = duckdb.connect(str(db), read_only=True)
            try:
                names = {r[0] for r in con.execute("SELECT table_name FROM information_schema.tables").fetchall()}
                if o["table"] not in names:
                    return {"exists": False, "why": f"表 {o['table']} 還沒有(未擷取)"}
                cols = con.execute(f'DESCRIBE "{o["table"]}"').fetchall()
                rows = con.execute(f'SELECT COUNT(*) FROM "{o["table"]}"').fetchone()[0]
            finally:
                con.close()
        else:
            f = home / str(o.get("file") or "")
            if not f.is_file():
                return {"exists": False, "why": f"檔 {o.get('file')} 還沒有(未擷取)"}
            con = duckdb.connect()
            try:
                lit = "'" + str(f).replace("'", "''") + "'"
                cols = con.execute(f"DESCRIBE SELECT * FROM read_parquet({lit})").fetchall()
                rows = con.execute(f"SELECT COUNT(*) FROM read_parquet({lit})").fetchone()[0]
            finally:
                con.close()
    except Exception as exc:  # noqa: BLE001 — 庫被占用 / 壞檔:照實記,不吞
        return {"exists": None, "why": f"讀不了:{type(exc).__name__}: {str(exc)[:120]}"}
    return {"exists": True, "columns": [(c[0], h_type(c[1]), c[1]) for c in cols], "rows": rows}


def judge(spec: dict, m: dict) -> tuple:
    got = {n: t for n, t, _raw in m["columns"]}
    red, yellow = [], []
    for c in spec.get("columns") or []:
        n = c["name"]
        if n not in got:
            (red if (c.get("required") or c.get("key")) else yellow).append(f"缺{'鍵' if c.get('key') else '必填' if c.get('required') else ''}欄 {n}")
        elif not type_ok(c.get("dtype", "str"), got[n]):
            yellow.append(f"{n} 型別 {got[n]}≠{c.get('dtype')}")
    mr = spec.get("min_rows")
    if isinstance(mr, int) and m["rows"] < mr:
        yellow.append(f"列 {m['rows']} < min_rows {mr}")
    return ("RED" if red else "YELLOW" if yellow else "GREEN"), red + yellow


def proposal(o: dict, m: dict) -> dict:
    keys = set(o.get("key") or [])
    return {"table": o["table"], "subsystem": "VDF", "owner": (o.get("writers") or [None])[0],
            "source": {"kind": "duckdb" if o.get("db") else "parquet", "path": "<VDF 資料家>/" + str(o.get("db") or o.get("file")),
                       **({"table": o["table"]} if o.get("db") else {})},
            "columns": [{"name": n, "dtype": t, "required": n in keys, "key": n in keys} for n, t, _raw in m["columns"]],
            "min_rows": None, "evidence": f"DESCRIBE(唯讀,只取 schema)· 資料平面冊 {o.get('id')} · 待 VCGC 核定必填與 min_rows"}


def output_check(root: Path, outputs: list | None = None, tables: dict | None = None, home=None, book_name: str = "",
                 out_dir: Path | None = None) -> dict:
    t0 = time.time()
    if outputs is None or tables is None or home is None:
        dp = dataplane(root)
        outputs = outputs if outputs is not None else list(dp.book_outputs())
        if tables is None:
            tables, book_name = header_book(root)
        if home is None:
            h, why = dp.P.resolve_home(None)
            home = h if h is not None else why
    idx = header_index(tables)
    rows, props = [], []
    have_home = isinstance(home, Path)
    for o in outputs:
        hit = match(o, idx) if tables else None
        r = {"id": o.get("id"), "db": o.get("db"), "table": o.get("table") or o.get("file"), "header": hit[0] if hit else None}
        if not tables:
            r.update(contract="GRAY", lamp="GRAY", why=book_name)
        elif not hit:
            r.update(contract="YELLOW", why="表頭冊沒有這張表")
        else:
            r.update(contract="GREEN")
        if not have_home:
            r["measure"] = "GRAY"
        else:
            m = measure(o, home)
            if m["exists"] is True:
                r["rows"] = m["rows"]
                if hit:
                    r["measure"], r["problems"] = judge(hit[1], m)
                else:
                    r["measure"], r["problems"] = "YELLOW", ["沒有表頭 → 已寫表頭草稿"]
                    props.append(proposal(o, m))
            else:
                r["measure"], r["problems"] = "YELLOW", [m["why"]]
        if "lamp" not in r:
            r["lamp"] = PRIOR.worst([r["contract"], r["measure"]])
        rows.append(r)
    if have_home and props:
        out = out_dir or PRIOR._p("v73_out")(root)
        (out / "HEADER_PROPOSALS_latest.json").write_text(json.dumps({"from": TAG, "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                                                     "for": "VCGC 表頭冊(VIA_Output_Header_SSOT)新版", "tables": props},
                                                                    ensure_ascii=False, indent=1), encoding="utf-8")
    lamp = PRIOR.worst(r["lamp"] for r in rows) if rows else "GRAY"
    return {"lamp": lamp, "header_book": book_name, "outputs": len(outputs), "checked": len(rows), "skipped": 0,
            "contract_ok": sum(1 for r in rows if r["contract"] == "GREEN"), "no_header": [r["table"] for r in rows if r["contract"] == "YELLOW"],
            "measured": have_home, "home": "找到資料家" if have_home else str(home), "measure_ok": sum(1 for r in rows if r.get("measure") == "GREEN"),
            "red": [(r["table"], r.get("problems")) for r in rows if r["lamp"] == "RED"], "proposals": len(props),
            "secs": round(time.time() - t0, 1), "rows": rows}


_ORIG_STRUCTURE = PRIOR.proc_structure


def proc_structure(root: Path) -> dict:
    r = _ORIG_STRUCTURE(root)
    try:
        oc = output_check(root)
    except Exception as exc:  # noqa: BLE001
        oc = {"lamp": "RED", "error": f"{type(exc).__name__}: {str(exc)[:160]}"}
    r["parts"]["outputs"] = oc["lamp"]
    r["outputs"] = {k: v for k, v in oc.items() if k != "rows"}
    r["lamp"] = PRIOR.worst(r["parts"].values())
    return r


PRIOR.proc_structure = proc_structure


def cmd_outputs(args: list) -> int:
    root = PRIOR._p("sm_via_root")()
    home = None
    if "--home" in args:
        hp = Path(args[args.index("--home") + 1])
        home = hp if hp.is_dir() else f"--home {hp} 不在"
    oc = output_check(root, home=home)
    if "--json" in args:
        print(json.dumps(oc, ensure_ascii=False, indent=1, default=str))
    else:
        print(f"[{TAG}] outputs {oc['lamp']} · 表頭冊 {oc['header_book']} · 應核 {oc['outputs']} · 已核 {oc['checked']} · 略過 {oc['skipped']} · "
              f"契約有表頭 {oc['contract_ok']} · 實測 {'綠 ' + str(oc['measure_ok']) if oc['measured'] else '灰(' + oc['home'] + ')'}")
        for r in oc["rows"]:
            if r["lamp"] != "GREEN":
                print(f"  {r['lamp']:<6} {r['id']} {r['table']:<28} 契約 {r['contract']} · 實測 {r.get('measure')} · {'; '.join(r.get('problems') or [r.get('why', '')])[:150]}")
        if oc["proposals"]:
            print(f"  [表頭草稿] {oc['proposals']} 張 → VIA_Reports/vdf/manager/HEADER_PROPOSALS_latest.json(交 VCGC 收進表頭冊)")
    return PRIOR._p("SM_RC").get(oc["lamp"], 2)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:240]) if note and not cond else ""), flush=True)

    print(f"[計] {TAG} 自測開始(本版 6 項 + 前版 {PRIOR_PATH.name} 自測 · 暫存資料家 · 零網路)", flush=True)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T1 加速器真的載到 · 第 3 行標記 · 網路橋在", VIA_ACCEL is not None and src.splitlines()[2] == "# [VIA:ACCEL-BRIDGE:v0111]"
        and VIA_NET_TOOL_PATH is not None)
    import duckdb
    with tempfile.TemporaryDirectory(prefix="vdf_out_") as td:
        home, out = Path(td) / "home", Path(td) / "out"
        home.mkdir()
        out.mkdir()
        c = duckdb.connect(str(home / "fx.duckdb"))
        c.execute("CREATE TABLE t_ok(date DATE, code VARCHAR, v DOUBLE)")
        c.execute("INSERT INTO t_ok VALUES ('2026-01-02','2330',1.5),('2026-01-03','2330',2)")
        c.execute("CREATE TABLE t_bad(date DATE, v VARCHAR)")
        c.execute("INSERT INTO t_bad VALUES ('2026-01-02','x')")
        c.execute("CREATE TABLE t_nohdr(date DATE, series VARCHAR, value DOUBLE)")
        c.execute("INSERT INTO t_nohdr VALUES ('2026-01-02','CPI',1.0)")
        c.close()
        spec = lambda t, cols, mr=None, db="fx.duckdb": {"subsystem": "VDF", "source": {"kind": "duckdb", "path": "x/" + db, "table": t},  # noqa: E731
                                         "columns": cols, "min_rows": mr}
        tables = {"t_ok": spec("t_ok", [{"name": "date", "dtype": "date", "key": True}, {"name": "code", "dtype": "str", "key": True},
                                        {"name": "v", "dtype": "float", "required": True}], 1),
                  "t_bad": spec("t_bad", [{"name": "date", "dtype": "date", "key": True}, {"name": "code", "dtype": "str", "key": True},
                                          {"name": "v", "dtype": "float"}]),
                  "t_few": spec("t_few", [{"name": "a", "dtype": "int"}], 5, "missing.duckdb")}
        outs = [{"id": "O1", "db": "fx.duckdb", "table": "t_ok"}, {"id": "O2", "db": "fx.duckdb", "table": "t_bad"},
                {"id": "O3", "db": "fx.duckdb", "table": "t_nohdr", "key": ["date", "series"], "writers": ["VDF_ENGFX"]},
                {"id": "O4", "db": "missing.duckdb", "table": "t_few"}]
        r = output_check(Path(td), outs, tables, home, "fx_book", out)
        by = {x["id"]: x for x in r["rows"]}
        chk("T2 全對 = 綠(DATE / VARCHAR / DOUBLE 對 date / str / float)", by["O1"]["lamp"] == "GREEN", by["O1"])
        chk("T3 缺鍵欄 = 紅;型別不合 = 記問題", by["O2"]["lamp"] == "RED" and any("缺鍵欄 code" in p for p in by["O2"]["problems"])
            and any("型別" in p for p in by["O2"]["problems"]), by["O2"])
        prop = json.loads((out / "HEADER_PROPOSALS_latest.json").read_text(encoding="utf-8"))["tables"][0]
        chk("T4 沒有表頭 = 黃 + 表頭草稿只含 schema(欄 · 型別 · 鍵),路徑不含本機目錄",
            by["O3"]["lamp"] == "YELLOW" and [c["name"] for c in prop["columns"]] == ["date", "series", "value"]
            and [c["key"] for c in prop["columns"]] == [True, True, False] and td not in json.dumps(prop) and "CPI" not in json.dumps(prop), prop)
        chk("T5 庫還沒擷取 = 黃(未擷取),不假綠也不當壞", by["O4"]["lamp"] == "YELLOW" and "未擷取" in by["O4"]["problems"][0], by["O4"])
        r2 = output_check(Path(td), outs, tables, "沒有資料家(容器)", "fx_book", out)
        chk("T6 沒有資料家:契約照核、實測灰;總燈不會因此變綠", all(x["measure"] == "GRAY" for x in r2["rows"]) and r2["contract_ok"] == 3
            and r2["lamp"] == "YELLOW" and r2["no_header"] == ["t_nohdr"], r2)
    rc = PRIOR.selftest() if callable(getattr(PRIOR, "selftest", None)) else 1
    chk("T7 前版 v0194 自測照過(含整條前版鏈)", rc == 0, rc)
    print(f"[計] {TAG} 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    if a[:1] == ["outputs"]:
        return cmd_outputs(a[1:])
    if a[:1] == ["vv"]:
        return PRIOR.cmd_vv(a[1:])
    return PRIOR.main(a)


if __name__ == "__main__":
    raise SystemExit(main())
