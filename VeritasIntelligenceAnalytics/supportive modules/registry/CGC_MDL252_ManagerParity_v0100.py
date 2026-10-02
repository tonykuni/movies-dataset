#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL252_ManagerParity v0100 — VDF / VRN 兩個 SYSTEM MANAGER 能力互比(只讀;一份共用,兩邊都呼叫)

操作員(R50 2026-10-02):「兩方的SYSTEM MANAGER工應互比要依樣強大」。
兩個子系統不互相匯入(VDF ↔ VRN 獨立性),互比放在中央這一支:
  ① 動詞盤點:讀兩個管理員整條版本鏈(VDF_SystemManager_v* · VRN_SystemManager_v*)的 AST,收 main 分派的動詞
     (args[0] / verb / cmd 比對的字串)與輸出命名空間(VDF universe · VRN outputs)底下的子動詞(sub 比對的字串)。
     只增律下動詞不會被拿掉,所以整鏈聯集 = 現役動詞。
  ② 能力表(CAPS):輸出表頭 · 表頭 → DataFrame · 輸出驗證 · 順序 · 三方對照 · Parquet(DuckDB 管)· 版號 + 時間鎖,
     加上尾版自測 · 只收 VCGC · 加速器橋 · 網路橋。兩邊都有 = GREEN;任一邊缺 = YELLOW(列缺哪邊、缺什麼)。
  ④ parquet_incremental:兩邊共用的 Parquet 步(寫手 CGC_MDL238;目錄列數沒變略過 = 增量)。
  ③ frame_from_spec:中央表頭冊(VIA_Output_Header_SSOT)一張表的 spec → pandas DataFrame(欄名 / 欄序 / 型別照冊);
     VRN 管理員的 outputs frame 用它,和 VDF 的 universe frame 同一套轉型律。
不寫冊、不跑被讀的檔(只做 ast.parse)、零網路、不用 TA-Lib。報告寫 VIA_Reports/vcgc/parity/PARITY_latest.json(再生件)。

用法:經 VCGC(via-vcgc run --family core CGC_MDL252_ManagerParity parity [--json]);--selftest 例外。
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

import ast
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
ENGINE_TAG = "CGC_MDL252_ManagerParity_v" + Path(__file__).stem.rsplit("_v", 1)[-1]
OUT = VIA / "VIA_Reports" / "vcgc" / "parity"
SIDES = {
    "VDF": {"dir": VIA / "functional modules" / "VDF", "stem": "VDF_SystemManager", "ns": "universe"},
    "VRN": {"dir": VIA / "functional modules" / "VRN", "stem": "VRN_SystemManager", "ns": "outputs"},
}
CAPS = [
    ("headers", "輸出表頭(中文表頭 · 欄位)", "ns"),
    ("frame", "表頭 → DataFrame", "ns"),
    ("validate", "輸出驗證(CGC_MDL249 check_table)", "ns"),
    ("loop", "順序(工作流冊)", "ns"),
    ("xcheck", "相同資料不同來源三方對照", "ns"),
    ("parquet", "輸出 Parquet 由 DuckDB 管(CGC_MDL238)", "ns"),
    ("lock", "引擎版號 + 時間鎖(VIA_LampLock)", "ns"),
    ("selftest", "尾版自測", "src"),
    ("vcgc_only", "只收 VCGC 呼叫(VIA_FROM_VCGC)", "src"),
    ("accel", "加速器橋", "src"),
    ("net", "網路橋", "src"),
]
TOP_NAMES = {"verb", "cmd", "action"}
VERB_RX = re.compile(r"^[a-z][a-z0-9_-]{1,24}$")


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def chain(side: dict) -> list:
    return sorted(Path(side["dir"]).glob(side["stem"] + "_v[0-9][0-9][0-9][0-9].py"), key=_vnum)


def _strs(node) -> list:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return [x for e in node.elts for x in _strs(e)]
    return []


def _kind(left) -> str | None:
    """比對左邊是哪一種:top(args[0] / verb / cmd)· sub(sub)· None(別的比對)。"""
    if isinstance(left, ast.Name):
        return "top" if left.id in TOP_NAMES else ("sub" if left.id == "sub" else None)
    if isinstance(left, ast.Subscript) and isinstance(left.value, ast.Name):
        s = left.slice
        if isinstance(s, ast.Constant) and s.value == 0:
            return "top"
        if isinstance(s, ast.Slice) and s.lower is None and isinstance(s.upper, ast.Constant) and s.upper.value == 1:
            return "top"
    return None


def verbs_of(src: str) -> dict:
    """一支檔的 {'top': set, 'sub': {函式名: set}}(只 ast.parse,不執行)。"""
    out = {"top": set(), "sub": {}}
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return out

    def walk(node, fn):
        for ch in ast.iter_child_nodes(node):
            name = ch.name if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef)) else fn
            if isinstance(ch, ast.Compare) and all(isinstance(o, (ast.Eq, ast.In)) for o in ch.ops):
                k = _kind(ch.left)
                if k:
                    vals = [v for c in ch.comparators for v in _strs(c) if VERB_RX.match(v)]
                    if k == "top":
                        out["top"].update(vals)
                    else:
                        out["sub"].setdefault(fn or "?", set()).update(vals)
            walk(ch, name)

    walk(tree, None)
    return out


def side_report(name: str, side: dict | None = None) -> dict:
    side = side or SIDES[name]
    files = chain(side)
    top, sub = set(), {}
    for p in files:
        v = verbs_of(p.read_text(encoding="utf-8", errors="replace"))
        top |= v["top"]
        for fn, s in v["sub"].items():
            sub.setdefault(fn, set()).update(s)
    tail = files[-1] if files else None
    src = tail.read_text(encoding="utf-8", errors="replace") if tail else ""
    ns = sub.get(side["ns"], set())
    have = {}
    for cap, _zh, how in CAPS:
        if how == "ns":
            have[cap] = side["ns"] in top and cap in ns
        elif cap == "selftest":
            have[cap] = "def selftest" in src
        elif cap == "vcgc_only":
            have[cap] = "VIA_FROM_VCGC" in src
        elif cap == "accel":
            have[cap] = "VIA:ACCEL-BRIDGE" in src
        elif cap == "net":
            have[cap] = "VIA:NET-BRIDGE" in src
    return {"side": name, "tail": tail.name if tail else None, "versions": len(files), "ns": side["ns"],
            "top": sorted(top), "ns_verbs": sorted(ns), "have": have}


def parity(sides: dict | None = None) -> dict:
    sides = sides or SIDES
    reps = {n: side_report(n, s) for n, s in sides.items()}
    a, b = list(reps)[:2]
    rows = []
    for cap, zh, _how in CAPS:
        ha, hb = reps[a]["have"][cap], reps[b]["have"][cap]
        rows.append({"cap": cap, "zh": zh, a: ha, b: hb, "lamp": "GREEN" if ha and hb else ("YELLOW" if ha or hb else "RED"),
                     "gap": "" if ha and hb else (f"{b} 缺" if ha else (f"{a} 缺" if hb else "兩邊都缺"))})
    only = {a: sorted(set(reps[a]["top"]) - set(reps[b]["top"])), b: sorted(set(reps[b]["top"]) - set(reps[a]["top"]))}
    lamps = [r["lamp"] for r in rows]
    verdict = "GREEN" if all(x == "GREEN" for x in lamps) else ("RED" if "RED" in lamps else "YELLOW")
    return {"schema": "VIA.ManagerParity.v1", "engine": ENGINE_TAG, "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "verdict": verdict, "sides": reps, "caps": rows, "only_top_verbs": only,
            "rule": "能力表兩邊都有 = GREEN;一邊缺 = YELLOW(補弱的一邊);兩邊都缺 = RED。只在一邊的一般動詞照列(資訊,不計燈)"}


def frame_from_spec(spec: dict, rows: list | None = None):
    """中央表頭冊一張表的 spec → pandas DataFrame(欄名 / 欄序照冊;型別 str/int/float/date/datetime/bool;空表也帶正確欄)。"""
    import pandas as pd
    names = [c["name"] for c in spec.get("columns") or []]
    df = pd.DataFrame(rows or [], columns=names)
    conv = {"str": "string", "int": "Int64", "float": "Float64", "bool": "boolean"}
    truth = {"true": True, "1": True, "t": True, "yes": True, "false": False, "0": False, "f": False, "no": False}
    for c in spec.get("columns") or []:
        n, dt = c["name"], c.get("dtype") or "str"
        if dt in ("date", "datetime"):
            df[n] = pd.to_datetime(df[n], errors="coerce")
            if dt == "date":
                df[n] = df[n].dt.normalize()
        elif dt in ("int", "float"):
            df[n] = pd.to_numeric(df[n], errors="coerce").astype(conv[dt])
        elif dt == "bool":
            df[n] = df[n].map(lambda v: v if isinstance(v, bool) else truth.get(str(v).strip().lower(), pd.NA)).astype("boolean")
        else:
            df[n] = df[n].astype("string")
    return df


def catalog_rows(home) -> dict:
    """資料家 Parquet 目錄(VIA_Parquet_Catalog.duckdb::_via_catalog)的 {view: 列數};不在 = {}。唯讀開。"""
    cat = Path(home) / "VIA_Parquet_Catalog.duckdb"
    if not cat.is_file():
        return {}
    import duckdb
    con = duckdb.connect(str(cat), read_only=True)
    try:
        if "_via_catalog" not in {t for (t,) in con.execute("SHOW TABLES").fetchall()}:
            return {}
        return {v: n for v, n in con.execute("SELECT view, rows FROM _via_catalog").fetchall()}
    finally:
        con.close()


def parquet_incremental(m238, tables, apply: bool = False, home: str | None = None) -> dict:
    """兩個管理員共用的 Parquet 步:寫手 = CGC_MDL238(parquet_plan / parquet_apply;來源唯讀、讀回列數驗)。
    只挑 tables 裡的表;目錄列數沒變且檔在 = 略過(增量);apply=False 乾跑。資料家不可用 / 一張都沒有 = NODATA。"""
    h, src = m238.data_home(home)
    if h is None:
        return {"state": "NODATA", "why": src, "plan": 0, "todo": []}
    want = set(tables)
    plan = [r for r in m238.parquet_plan(h) if r["table"] in want]
    cat = catalog_rows(h)
    todo = [r for r in plan if not (r["exists"] and cat.get(r["view"]) == r["rows"])]
    res = {"state": "OK" if plan else "NODATA", "home": str(h), "src": src, "plan": len(plan), "todo": [r["view"] for r in todo],
           "skip": len(plan) - len(todo), "applied": False}
    if apply and todo:
        out = m238.parquet_apply(h, todo)
        res.update(applied=True, written=out["written"], failed=[f["view"] for f in out["failed"]], catalog=out["catalog"])
        if out["failed"]:
            res["state"] = "RED"
    return res


def write(rep: dict, out: Path = OUT) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    p = out / "PARITY_latest.json"
    p.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    return p


def show(rep: dict) -> None:
    a, b = list(rep["sides"])[:2]
    print(f"[管理員互比] {rep['verdict']} · {a} {rep['sides'][a]['tail']}({rep['sides'][a]['versions']} 版)"
          f" vs {b} {rep['sides'][b]['tail']}({rep['sides'][b]['versions']} 版)")
    for r in rep["caps"]:
        print(f"  [{r['lamp']:<6}] {r['zh']:<28} {a} {'有' if r[a] else '缺'} · {b} {'有' if r[b] else '缺'}")
    for s, v in rep["only_top_verbs"].items():
        if v:
            print(f"  [資訊] 只在 {s} 的動詞:{', '.join(v[:20])}")


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "只經 VCGC(VIA_FROM_VCGC=YES)"}, ensure_ascii=False))
        return 2
    verb = next((x for x in a if not x.startswith("-")), "parity")
    if verb == "parity":
        rep = parity()
        p = write(rep)
        print(json.dumps(rep, ensure_ascii=False, indent=1)) if "--json" in a else show(rep)
        print(f"  記錄 {p}")
        return {"GREEN": 0, "YELLOW": 2}.get(rep["verdict"], 1)
    print(__doc__)
    return 2


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {ENGINE_TAG} · 自測(暫存兩個假管理員鏈;只 ast.parse)===")
    strong = ('import os\n# [VIA:ACCEL-BRIDGE] [VIA:NET-BRIDGE]\n'
              'def universe(args):\n    sub = args[0]\n'
              '    if sub in ("headers", "frame", "validate", "loop"):\n        return 0\n'
              '    if sub == "xcheck" or sub == "parquet" or sub == "lock":\n        return 0\n'
              'def main():\n    a = []\n    if os.environ.get("VIA_FROM_VCGC") != "YES":\n        return 2\n'
              '    if a[0] == "universe":\n        return universe(a[1:])\n    if a[:1] == ["status"]:\n        return 0\n'
              'def selftest():\n    return 0\n')
    weak = 'def main(argv=None):\n    args = argv\n    verb = args[0]\n    if verb == "status":\n        return 0\n    if args and args[0] == "provenance":\n        return 0\n'
    weak2 = weak + 'def outputs(args):\n    sub = args[0]\n    if sub in ("headers", "frame", "validate", "loop", "xcheck", "parquet", "lock"):\n        return 0\n' \
        + '# [VIA:ACCEL-BRIDGE] [VIA:NET-BRIDGE] VIA_FROM_VCGC\nif False:\n    if verb == "outputs":\n        pass\ndef selftest():\n    return 0\n'
    with tempfile.TemporaryDirectory() as td:
        A, B = Path(td) / "a", Path(td) / "b"
        A.mkdir()
        B.mkdir()
        (A / "X_SystemManager_v0100.py").write_text(strong, encoding="utf-8")
        (B / "Y_SystemManager_v0100.py").write_text(weak, encoding="utf-8")
        sides = {"VDF": {"dir": A, "stem": "X_SystemManager", "ns": "universe"}, "VRN": {"dir": B, "stem": "Y_SystemManager", "ns": "outputs"}}
        v = verbs_of(strong)
        chk("① AST 收 args[0] · args[:1] · sub 三種比對", {"universe", "status"} <= v["top"]
            and {"headers", "frame", "validate", "loop", "xcheck", "parquet", "lock"} <= v["sub"].get("universe", set()), v)
        r = parity(sides)
        chk("② 弱的一邊缺能力 = YELLOW,逐項列「VRN 缺」", r["verdict"] == "YELLOW" and all(x["gap"] == "VRN 缺" for x in r["caps"] if x["lamp"] != "GREEN"))
        chk("③ 只在一邊的一般動詞照列(provenance 只在 VRN)", "provenance" in r["only_top_verbs"]["VRN"])
        (B / "Y_SystemManager_v0101.py").write_text(weak2, encoding="utf-8")
        r2 = parity(sides)
        chk("④ 補上薄尾後整鏈聯集 = 兩邊一樣強 → GREEN", r2["verdict"] == "GREEN" and r2["sides"]["VRN"]["versions"] == 2, [x["cap"] for x in r2["caps"] if x["lamp"] != "GREEN"])
        p = write(r2, Path(td) / "out")
        chk("⑤ 報告寫得出、讀得回", json.loads(p.read_text(encoding="utf-8"))["verdict"] == "GREEN")
    try:
        df = frame_from_spec({"columns": [{"name": "d", "dtype": "date"}, {"name": "n", "dtype": "int"}, {"name": "b", "dtype": "bool"},
                                          {"name": "s", "dtype": "str"}]}, [{"d": "2026-10-01", "n": "3", "b": "true", "s": "x"}])
        chk("⑥ frame_from_spec:欄序照冊 · 型別照冊轉", list(df.columns) == ["d", "n", "b", "s"] and str(df.dtypes["n"]) == "Int64"
            and bool(df["b"].iloc[0]) is True and str(df.dtypes["d"]).startswith("datetime64"))
    except ImportError:
        chk("⑥ frame_from_spec(pandas 不在 = 照實略過)", True, "pandas 不在")
    real = parity()
    chk("⑦ 真實兩條鏈讀得到(VDF · VRN 尾版都在)", all(s["tail"] for s in real["sides"].values()), {k: s["tail"] for k, s in real["sides"].items()})
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 加速器橋在 · 不碰 TA-Lib · 不 import 子系統管理員", "VIA:ACCEL-BRIDGE" in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"^\s*(import|from)\s+V(DF|RN)_SystemManager", src, re.M))
    good = all(ok)
    print(f"  [計] {ENGINE_TAG} {sum(ok)}/{len(ok)} · {'PASS' if good else 'FAIL'}")
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
