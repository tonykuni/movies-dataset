"""VRN_SystemManager v0111 — 薄尾:輸出管理動詞 outputs(與 VDF 管理員 universe 同一套能力;R50 互比補弱)

操作員(R50 2026-10-02):「兩方的SYSTEM MANAGER工應互比要依樣強大」「輸出PARQUET由DUCKDB管理 增量擷取 輸出後相同資料不同來源
三個重複齊對照」「引擎時測成功就鎖住含版號及時間都要註冊」。CGC_MDL252 互比量出 VRN 缺 7 項,本版補齊,只接既有正主、不另寫擷取:
  outputs headers [--json]         中央表頭冊(VIA_Output_Header_SSOT 尾版)subsystem=VRN 的表:欄位 · 型別 · 主鍵 · 來源
  outputs frame <表>               表頭 → pandas DataFrame(CGC_MDL252.frame_from_spec;與 VDF 同一套轉型律)
  outputs validate [<表>] [--file <csv|parquet>]  CGC_MDL249 check_table(必填 · 型別 · 主鍵 · 最少列;來源不在 = NODATA)
  outputs loop                     VRN 工作流冊尾版的工作流 / 步順序 · 每步引擎尾版在不在
  outputs xcheck                   相同資料不同來源三方對照 = VRN_ENG393 的 XCHECK_latest(文字 · 表格兩法 · 乘積三重)逐份燈號彙總
  outputs parquet [--apply] [--home <dir>]  VRN DuckDB 表出 Parquet(CGC_MDL252.parquet_incremental;寫手 CGC_MDL238;沒變略過)
  outputs lock                     VIA_LampLock 尾版上 VRN-WKF* 的鎖(locked_at + 版號);沒鎖的列出、怎麼鎖
其餘動詞全照前版(provenance 等)。不抓網、不代設同意閘、不碰 TA-Lib。只收 VCGC 呼叫(VIA_FROM_VCGC=YES)。
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
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
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
REG = VIA / "supportive modules" / "registry"
_STEM = "VRN_SystemManager"
ENGINE_TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def _vnum(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _import_file(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
PRIOR = _import_file(_PRIOR_PATH, f"_vrn_manager_prior_v{_vnum(__file__):04d}")


def __getattr__(name):
    return getattr(PRIOR, name)


def _tail(folder: Path, pattern: str) -> Path | None:
    hits = sorted(Path(folder).glob(pattern), key=_vnum)
    return hits[-1] if hits else None


def _mdl(stem: str):
    return _import_file(_tail(REG, stem + "_v*.py"), f"_{stem.lower()}_for_vrn_outputs")


def header_tables() -> dict:
    """中央表頭冊尾版裡 subsystem = VRN 的表(不抄第二份)。"""
    hb = _tail(REG, "VIA_Output_Header_SSOT_v[0-9][0-9][0-9][0-9].json")
    tabs = json.loads(hb.read_text(encoding="utf-8")).get("tables") or {}
    return {k: v for k, v in tabs.items() if v.get("subsystem") == "VRN"}, hb.name


def spec_of(tid: str) -> dict:
    tabs, _ = header_tables()
    if tid not in tabs:
        raise KeyError(f"中央表頭冊沒有 VRN 表 {tid}(有:{', '.join(tabs)})")
    return tabs[tid]


def frame(tid: str, rows: list | None = None):
    return _mdl("CGC_MDL252_ManagerParity").frame_from_spec(spec_of(tid), rows)


def validate(tid: str, df=None) -> dict:
    m = _mdl("CGC_MDL249_DataFrameLock")
    spec = spec_of(tid)
    return m.check_table(tid, spec, frame=df) if df is not None else m.check_table(tid, spec)


def loop_plan() -> list:
    wb = _tail(REG, "VIA_Workflow_VRN_SSOT_v[0-9][0-9][0-9][0-9].json")
    out = []
    for w in json.loads(wb.read_text(encoding="utf-8")).get("workflows") or []:
        for st in w.get("steps") or []:
            pat = st.get("engine") or ""
            pats = pat if isinstance(pat, list) else [pat]
            tails = [_tail(VIA / Path(p).parent, Path(p).name) for p in pats if "*" in p]
            state = "ITEM" if st.get("item") else ("EVIDENCE" if st.get("evidence") or st.get("station") else
                                                    ("OK" if tails and all(tails) else ("ABSENT" if tails else "REF")))
            out.append({"wkf": w["code"], "step": st["code"], "alias": st.get("alias") or "", "state": state,
                        "engine": ", ".join(t.name for t in tails if t) or st.get("item") or st.get("evidence") or st.get("station") or ""})
    return out


def xcheck(path: Path | None = None) -> dict:
    """VRN_ENG393 三重對照(文字 · 表格兩法 · 乘積)逐份燈號彙總;報告不在 = NODATA。"""
    src = (spec_of("vrn_firstpage_xcheck").get("source") or {})
    p = Path(path) if path else VIA / src.get("path", "VIA_Reports/vrn/doc_class/XCHECK_latest.json")
    if not p.is_file():
        return {"verdict": "NODATA", "rows": 0, "tally": {}, "why": f"報告不在:{p.name}(先跑 VRN_ENG393 verify)"}
    d = json.loads(p.read_text(encoding="utf-8"))
    rows = d.get(src.get("table") or "rows") or []
    tally = {v: sum(1 for r in rows if r.get("verdict") == v) for v in ("GREEN", "YELLOW", "RED")}
    verdict = "NODATA" if not rows else ("RED" if tally["RED"] else ("YELLOW" if tally["YELLOW"] else "GREEN"))
    bad = [f"{r.get('report_file')} · {str(r.get('verdict_why') or '')[:80]}" for r in rows if r.get("verdict") != "GREEN"][:5]
    return {"verdict": verdict, "rows": len(rows), "tally": tally, "worst": bad, "report": str(p)}


def parquet(apply: bool = False, home: str | None = None, m238=None) -> dict:
    tabs, _ = header_tables()
    want = sorted({(v.get("source") or {}).get("table") for v in tabs.values() if (v.get("source") or {}).get("kind") == "duckdb"} - {None, ""})
    return _mdl("CGC_MDL252_ManagerParity").parquet_incremental(m238 or _mdl("CGC_MDL238_OperatorConsole"), want, apply, home)


def lock_view() -> dict:
    wb = _tail(REG, "VIA_Workflow_VRN_SSOT_v[0-9][0-9][0-9][0-9].json")
    codes = [w["code"] for w in json.loads(wb.read_text(encoding="utf-8")).get("workflows") or []]
    ll = _tail(REG, "VIA_LampLock_v[0-9][0-9][0-9][0-9].json")
    wk = (json.loads(ll.read_text(encoding="utf-8")).get("wkf") or {}) if ll else {}
    rows = [{"wkf": c, "locked_at": (wk.get(c) or {}).get("locked_at"), "level": (wk.get(c) or {}).get("level"),
             "versions": len((wk.get(c) or {}).get("versions") or {})} for c in codes]
    n = sum(1 for r in rows if r["locked_at"])
    return {"book": wb.name, "lamplock": ll.name if ll else None, "rows": rows, "locked": n,
            "state": "LOCKED" if n == len(rows) else ("PARTIAL" if n else "OPEN")}


def _arg(a: list, k: str):
    return a[a.index(k) + 1] if k in a and a.index(k) + 1 < len(a) else None


def outputs(args: list) -> int:
    sub = args[0] if args else "headers"
    if sub == "headers":
        tabs, hb = header_tables()
        if "--json" in args:
            print(json.dumps(tabs, ensure_ascii=False, indent=1))
            return 0
        print(f"[VRN 輸出表頭] 中央表頭冊 {hb} · VRN 表 {len(tabs)}")
        for k, v in tabs.items():
            cols = v.get("columns") or []
            print(f"  {k}({v.get('owner')} · {len(cols)} 欄 · 主鍵 {[c['name'] for c in cols if c.get('key')]} · 來源 {(v.get('source') or {}).get('kind')})")
        return 0
    if sub == "frame" and len(args) >= 2:
        df = frame(args[1])
        print(f"[VRN 表頭 → DataFrame] {args[1]} · {len(df.columns)} 欄")
        print(df.dtypes.to_string())
        return 0
    if sub == "validate":
        tabs, _ = header_tables()
        ids = [a for a in args[1:] if a in tabs] or list(tabs)
        worst = 0
        for tid in ids:
            df = None
            if "--file" in args:
                import pandas as pd
                fp = _arg(args, "--file")
                df = pd.read_parquet(fp) if fp.endswith(".parquet") else pd.read_csv(fp, encoding="utf-8-sig", dtype=str)
            r = validate(tid, df)
            lamp = r.get("lamp")
            worst = max(worst, {"GREEN": 0, "YELLOW": 0, "NODATA": 0}.get(lamp, 1))
            print(f"  [{lamp}] {tid} · 列 {r.get('rows')} · " + " ; ".join(r.get("problems") or []))
        return worst
    if sub == "loop":
        lp = loop_plan()
        print(f"[VRN 順序] 步 {len(lp)} · 缺引擎 {sum(1 for s in lp if s['state'] == 'ABSENT')}")
        for s in lp:
            print(f"  {s['step']:<20} {s['alias']:<22} {s['state']:<9} {s['engine'][:70]}")
        return 0 if not any(s["state"] == "ABSENT" for s in lp) else 1
    if sub == "xcheck":
        r = xcheck()
        print(f"[VRN 三方對照] {r['verdict']} · 份 {r['rows']} · " + " · ".join(f"{k} {v}" for k, v in r["tally"].items()) + (f" · {r['why']}" if r.get("why") else ""))
        for x in r.get("worst") or []:
            print("  · " + x)
        return {"GREEN": 0, "YELLOW": 2, "NODATA": 2}.get(r["verdict"], 1)
    if sub == "parquet":
        r = parquet("--apply" in args, _arg(args, "--home"))
        print(f"[VRN Parquet] {r['state']} · " + (f"資料家 {r.get('home')} · 表 {r['plan']} · 要寫 {len(r['todo'])} · 沒變略過 {r.get('skip', 0)}"
                                                   if r.get("home") else r.get("why", "")))
        return {"OK": 0, "NODATA": 2}.get(r["state"], 1)
    if sub == "lock":
        v = lock_view()
        print(f"[VRN 鎖] {v['state']} · 已鎖 {v['locked']}/{len(v['rows'])} · 冊 {v['book']} · 鎖帳 {v['lamplock']}")
        for r in v["rows"]:
            print(f"  {r['wkf']:<12} {r['locked_at'] or '未鎖':<20} {r['level'] or '':<10} 版號 {r['versions']}")
        if v["state"] != "LOCKED":
            print("  → via-vcgc sdd selftests → sdd real → run CGC_MDL245_SDDValidator lock --apply(版號 + 時間寫 VIA_LampLock)")
        return 0 if v["state"] == "LOCKED" else 2
    print(f"[VRN outputs] 不認得:{sub}(headers / frame / validate / loop / xcheck / parquet / lock)")
    return 2


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[DENY] VCGC entry required")
        return 2
    if args and args[0] == "outputs":
        return outputs(args[1:])
    return PRIOR.main(args)


def selftest():
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {ENGINE_TAG} · 薄尾自測(outputs:表頭 · DataFrame · 驗證 · 順序 · 三方對照 · Parquet · 鎖)===")
    tabs, hb = header_tables()
    chk("① 表頭只讀中央表頭冊的 VRN 表(不抄)", len(tabs) >= 8 and "vrn_firstpage_xcheck" in tabs, (hb, len(tabs)))
    df = frame("vrn_doc_class")
    chk("② 表頭 → DataFrame:欄序照冊 · bool / float 照型別", list(df.columns) == [c["name"] for c in tabs["vrn_doc_class"]["columns"]]
        and str(df.dtypes["needs_review"]) == "boolean" and str(df.dtypes["class_confidence"]) == "Float64")
    rows = [{c["name"]: ("x" if c["dtype"] == "str" else (0.5 if c["dtype"] == "float" else (True if c["dtype"] == "bool" else 1)))
             for c in tabs["vrn_doc_class"]["columns"]}] * 2
    v = validate("vrn_doc_class", frame("vrn_doc_class", rows))
    chk("③ 驗證走 CGC_MDL249:主鍵 report_file 重複抓得到", v["lamp"] == "RED" and any("主鍵" in p for p in v.get("problems") or []), v.get("problems"))
    lp = loop_plan()
    chk("④ 順序:VRN 工作流冊每一步都列出(引擎 / 項 / 證據)", lp and all(s["step"].startswith("VRN-WKF") for s in lp), len(lp))
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "x.json"
        p.write_text(json.dumps({"rows": [{"report_file": "a", "verdict": "GREEN"}, {"report_file": "b", "verdict": "RED", "verdict_why": "乘積不符"}]}),
                     encoding="utf-8")
        x = xcheck(p)
        chk("⑤ 三方對照彙總:有一份 RED = RED,列最差的", x["verdict"] == "RED" and x["tally"] == {"GREEN": 1, "YELLOW": 0, "RED": 1}
            and "乘積不符" in x["worst"][0], x)
        chk("⑥ 報告不在 = NODATA(不假綠)", xcheck(Path(td) / "none.json")["verdict"] == "NODATA")

    class FakeM238:
        def data_home(self, override=None):
            return None, "資料家不可用"

    chk("⑦ Parquet:資料家不可用 = NODATA(寫手 CGC_MDL238 · 增量在 CGC_MDL252)", parquet(True, None, FakeM238())["state"] == "NODATA")
    lv = lock_view()
    chk("⑧ 鎖:VRN-WKF* 每條在鎖帳上的 locked_at 讀得到", lv["rows"] and lv["state"] in ("LOCKED", "PARTIAL", "OPEN"), (lv["state"], lv["locked"]))
    pr = _mdl("CGC_MDL252_ManagerParity").side_report("VRN")
    chk("⑨ 互比(CGC_MDL252):VRN outputs 七項能力全在(與 VDF universe 一樣強)",
        all(pr["have"][k] for k in ("headers", "frame", "validate", "loop", "xcheck", "parquet", "lock")), {k: v for k, v in pr["have"].items() if not v})
    keep = os.environ.pop("VIA_FROM_VCGC", None)
    try:
        chk("⑩ 不經 VCGC 拒跑", main(["outputs", "headers"]) == 2)
    finally:
        if keep is not None:
            os.environ["VIA_FROM_VCGC"] = keep
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑪ 加速器橋 · 網路橋在;不碰 TA-Lib;不代設同意閘", "VIA:ACCEL-BRIDGE" in src and "VIA:NET-BRIDGE" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M) and "VIA_NET_CONSENT\"] =" not in src)
    prior = PRIOR.selftest()
    good = all(ok)
    print(f"  [計] {ENGINE_TAG} 薄尾 {sum(ok)}/{len(ok)} · 前版 {'PASS' if not prior else 'FAIL'} · 合計 {'PASS' if good and not prior else 'FAIL'}")
    return 0 if good and not prior else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if sys.argv[1:] == ["--selftest"] else main())
