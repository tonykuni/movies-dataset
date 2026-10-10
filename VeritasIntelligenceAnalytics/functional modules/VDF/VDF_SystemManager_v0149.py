#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_SystemManager v0149 — 薄尾:管理員自己單引擎啟動(操作員令 2026-10-10:「VDF 單獨可被 VDF SystemManager 可啟動就成功」)。
  engine run <引擎> [參數…]           管理員直接起一支引擎(不經 VCGC 主控台):MDL253 解析 + 啟動前閘(紅 = 拒)→ 家族境 python(MDL148 EngineBus)
                                      → 子行程 cwd = 引擎夾 · env 帶 VIA_FROM_VCGC=YES;同意閘照操作員視窗原樣傳,AI 不代設;rc = 引擎 rc
  engine launch [<引擎>… | --sources] [--json]
                                      啟動驗收:每支 ① 載入(子行程 import,不跑 main)② 有 --selftest 就經 engine run 跑一次
                                      可啟動 = ① rc0(驗收線);自測 GREEN rc0 · NODATA rc2(缺件不是壞)· RED 其他 · — 沒自測;結果 VIA_Reports/vdf/RESULT_engine_launch_latest.json
  engine sources [--json]             TWSE / TPEx / yfinance 來源引擎冊(整條版本鏈合併判定:twse.com.tw · tpex.org.tw · import yfinance / yf.download / yf.Ticker;
                                      _rebuilds_superseded 不收;同名異夾照路徑各列一支)
<引擎> 解析同 v0123(229 · ENG229 · MDL002 · 全名 · 片段;同號異名回候選不猜)。其餘動詞照前版鏈。只收 VIA_FROM_VCGC=YES。不碰 TA-Lib。
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
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: F401
except ImportError:
    VIA_ACCEL = None
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

# ===== [VIA:LIB-BRIDGE:v0100] 三庫正典橋(批597;缺席大聲拋,不 graceful) =====
import sys as _lb_sys
from pathlib import Path as _lb_Path
_lb_p = _lb_Path(__file__).resolve()
while _lb_p.parent != _lb_p:
    if (_lb_p / "supportive modules").is_dir():
        _lb_sys.path.insert(0, str(_lb_p / "supportive modules"))
        break
    _lb_p = _lb_p.parent
import VIA_LibCanon as _LIB          # 正典缺席=大聲拋,不假裝有(LL151)
# ===== [VIA:LIB-BRIDGE:END] =====

import datetime
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
_STEM = "VDF_SystemManager"
TAG = "v0149"
SOURCES = ("TWSE", "TPEx", "yfinance")
_SRC_RX = {
    "TWSE": re.compile(r"twse\.com\.tw", re.I),
    "TPEx": re.compile(r"tpex\.org\.tw", re.I),
    "yfinance": re.compile(r"^\s*(?:import yfinance|from yfinance)|import_module\(\s*[\"']yfinance|\byf\.(?:download|Ticker)\(", re.M),
}
_SUPERSEDED = "_rebuilds_superseded"
_LOAD_PROBE = ("import importlib.util,sys;p=sys.argv[1];s=importlib.util.spec_from_file_location('_vdf_launch_probe',p);"
               "m=importlib.util.module_from_spec(s);sys.modules['_vdf_launch_probe']=m;s.loader.exec_module(m);print('LOADED')")


def _vnum_v0149(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0149(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0149(p) < _vnum_v0149(__file__)), key=_vnum_v0149)
PRIOR = _load_v0149(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def _inv():
    return PRIOR._inventory_v0123()          # VCGC 檢視本體 CGC_MDL253(兩個管理員共用一份,不另抄)


def _python() -> tuple:
    """家族境 python:MDL148 EngineBus.python_for('vdf');缺席退本行程並講明(同 VCGC run 的取法)。"""
    reg = VIA / "supportive modules" / "registry"
    hits = sorted(reg.glob("CGC_MDL148_EngineBus_v*.py"), key=_vnum_v0149)
    if hits:
        try:
            r = _load_v0149(hits[-1], "_vdf_mgr_v0149_bus").python_for("vdf") or {}
            if r.get("python"):
                return r["python"], r.get("source") or r.get("state") or "EngineBus"
        except Exception as exc:
            return sys.executable, "本行程退路(EngineBus %s)" % type(exc).__name__
    return sys.executable, "本行程退路(EngineBus 不在)"


def _pick(key: str, rows: list | None = None) -> tuple:
    """→ (row, candidates, rows);找不到 row=None 且 candidates=[];同號異名 row=None 且 candidates 有料。"""
    inv = _inv()
    rows = rows if rows is not None else inv.engines("VDF")
    one, cands = inv.resolve(rows, key)
    return one, ([] if one else list(cands or [])), rows


def run_path(path: Path, args: list, timeout: float | None = None, capture: bool = False) -> dict:
    """單引擎子行程(本版唯一起子行程的地方)。env 只加 VIA_FROM_VCGC=YES;同意閘不加不減。"""
    py, why = _python()
    env = dict(os.environ, VIA_FROM_VCGC="YES")
    t0 = time.time()
    try:
        r = subprocess.run([py, str(path)] + [str(a) for a in args], cwd=str(path.parent), env=env, stdin=subprocess.DEVNULL,
                           capture_output=capture, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        rc, out = r.returncode, ((r.stdout or "") + (r.stderr or "")) if capture else ""
    except subprocess.TimeoutExpired:
        rc, out = "TIMEOUT", ""
    return {"rc": rc, "secs": round(time.time() - t0, 1), "python": py, "python_src": why, "tail": [ln for ln in out.splitlines() if ln.strip()][-3:]}


def load_probe(path: Path, timeout: float = 120) -> dict:
    """可啟動 ①:子行程 import 引擎(不跑 main / __main__ 區),看頂層匯入與橋是否站得住。"""
    py, _why = _python()
    env = dict(os.environ, VIA_FROM_VCGC="YES")
    t0 = time.time()
    try:
        r = subprocess.run([py, "-c", _LOAD_PROBE, str(path)], cwd=str(path.parent), env=env, stdin=subprocess.DEVNULL,
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        rc, out = r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        rc, out = "TIMEOUT", ""
    return {"rc": rc, "secs": round(time.time() - t0, 1), "tail": [ln for ln in out.splitlines() if ln.strip()][-3:]}


def engine_run(args: list) -> int:
    if not args:
        print("  用法:engine run <引擎> [參數…]")
        return 2
    try:
        one, cands, _rows = _pick(args[0])
    except RuntimeError as e:
        print("[%s %s] 啟動冊 ABSENT:%s" % (_STEM, TAG, e))
        return 3
    if one is None:
        print("[%s %s] %s:%s" % (_STEM, TAG, "同號異名,請用全名" if cands else "找不到引擎", args[0]))
        for c in cands:
            print("    候選 %s · %s" % (c.get("eid"), c.get("family")))
        return 3
    g = _inv().gate(one, "VDF")
    if g.get("lamp") == "RED":
        print("[%s %s] 啟動前閘 RED,不准啟動 %s:%s" % (_STEM, TAG, one["family"], "; ".join(g.get("block") or [])))
        return 2
    path = VIA / one["path"]
    print("  [VDF engine run] %s %s · 閘 %s · %s" % (one["eid"], one["family"], g.get("lamp"), path.name))
    sys.stdout.flush()
    r = run_path(path, args[1:])
    print("  [VDF engine run] %s rc=%s · %ss · python %s" % (one["family"], r["rc"], r["secs"], r["python_src"]))
    return r["rc"] if isinstance(r["rc"], int) else 1


def _family_files(row: dict) -> list:
    tail = VIA / row["path"]
    rx = re.compile(r"^" + re.escape(row["family"]) + r"(?:_v\d{4})?\.py$")
    return sorted(p for p in tail.parent.glob(row["family"] + "*.py") if rx.match(p.name)) or [tail]


def sources(rows: list | None = None) -> list:
    """來源引擎冊:整條版本鏈合併(薄尾只寫差異,本體的網址算在家族上)。"""
    rows = rows if rows is not None else _inv().engines("VDF")
    out = []
    for r in rows:
        if _SUPERSEDED in r["path"]:
            continue                         # 已被取代的重建版不算活引擎(冊上照列,本冊不收)
        hit, unread = set(), []
        for p in _family_files(r):
            try:
                t = p.read_text(encoding="utf-8", errors="replace")
            except OSError as e:
                unread.append("%s:%s" % (p.name, type(e).__name__))          # 讀不到照列,不默吞
                t = ""
            hit |= {k for k, rx in _SRC_RX.items() if rx.search(t)}
        if hit or unread:
            out.append({"eid": r["eid"], "family": r["family"], "path": r["path"], "version": r.get("version"),
                        "code": r.get("code"), "sources": [k for k in SOURCES if k in hit], "flags": r.get("flags") or [], "unread": unread})
    return sorted(out, key=lambda x: (x["eid"], x["family"]))


def launch(keys: list, use_sources: bool = False) -> dict:
    inv = _inv()
    rows = inv.engines("VDF")
    targets, missing = [], []
    if use_sources:
        want = {s["path"] for s in sources(rows)}
        targets = [r for r in rows if r["path"] in want]
    for k in keys:
        one, cands = inv.resolve(rows, k)
        (targets.append(one) if one else missing.append({"key": k, "candidates": [c.get("family") for c in (cands or [])]}))
    per = []
    for r in targets:
        path = VIA / r["path"]
        g = inv.gate(r, "VDF")
        ld = load_probe(path) if g.get("lamp") != "RED" else {"rc": "GATE", "secs": 0, "tail": g.get("block") or []}
        st = None
        if ld["rc"] == 0 and "--selftest" in (r.get("flags") or []):
            st = run_path(path, ["--selftest"], timeout=float(os.environ.get("VIA_VDF_LAUNCH_TIMEOUT") or 600), capture=True)
        st_lamp = "—" if st is None else ("GREEN" if st["rc"] == 0 else "NODATA" if st["rc"] == 2 else "RED")
        per.append({"eid": r["eid"], "family": r["family"], "path": r["path"], "gate": g.get("lamp"),
                    "launchable": ld["rc"] == 0, "load": ld, "selftest": st, "selftest_lamp": st_lamp})
    n_ok = sum(1 for p in per if p["launchable"])
    cnt = {k: sum(1 for p in per if p["selftest_lamp"] == k) for k in ("GREEN", "NODATA", "RED", "—")}
    lamp = "RED" if (missing or n_ok < len(per) or not per) else ("GREEN" if cnt["RED"] == 0 and cnt["NODATA"] == 0 else "YELLOW")
    o = {"via": "vdf", "verb": "engine launch", "tag": "%s %s" % (_STEM, TAG), "ts": datetime.datetime.now().isoformat(timespec="seconds"),
         "n": len(per), "launchable": n_ok, "selftest": cnt, "missing": missing, "lamp": lamp, "per": per}
    try:
        out = PRIOR._out()
        out.mkdir(parents=True, exist_ok=True)
        (out / "RESULT_engine_launch_latest.json").write_text(json.dumps(o, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
        o["result"] = str(out / "RESULT_engine_launch_latest.json")
    except OSError as e:
        o["result"] = "寫不出:%s" % e
    return o


def _print_launch(o: dict) -> None:
    for p in o["per"]:
        st = p["selftest"] or {}
        print("  [%s] %-6s %-44s 載入 rc=%s · 自測 %s%s" % ("可啟動" if p["launchable"] else "不能起", p["eid"], p["family"][:44], p["load"]["rc"],
                                                       p["selftest_lamp"], (" rc=%s" % st.get("rc")) if st else ""))
        if not p["launchable"] or p["selftest_lamp"] == "RED":
            for ln in (st.get("tail") if p["launchable"] else p["load"]["tail"]) or []:
                print("        │ %s" % ln[:160])
    for m in o["missing"]:
        print("  [找不到] %s%s" % (m["key"], (" · 候選 " + ", ".join(m["candidates"])) if m["candidates"] else ""))
    c = o["selftest"]
    print("[計] VDF 單引擎啟動 %d/%d 可啟動 · 自測 GREEN %d · NODATA %d · RED %d · 沒自測 %d · %s · %s"
          % (o["launchable"], o["n"], c["GREEN"], c["NODATA"], c["RED"], c["—"], o["lamp"], o.get("result")))


def _print_sources(rows: list) -> None:
    for s in rows:
        print("  %-6s %-44s %-6s %-14s %s" % (s["eid"], s["family"][:44], s.get("version") or "—", s.get("code") or "未編號", "+".join(s["sources"])))
    print("[計] 來源引擎 %d 支 · TWSE %d · TPEx %d · yfinance %d" % (len(rows), *(sum(1 for s in rows if k in s["sources"]) for k in SOURCES)))


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["engine"] and args[1:2] and args[1] in ("run", "launch", "sources"):
        if os.environ.get("VIA_FROM_VCGC") != "YES":
            print("[VDF] 拒絕。只能經 via-vcgc / VDF 啟動器(VIA_FROM_VCGC=YES)。")
            return 2
        sub, rest = args[1], args[2:]
        if sub == "run":
            return engine_run(rest)
        as_json = "--json" in rest
        if sub == "sources":
            rows = sources()
            print(json.dumps(rows, ensure_ascii=False, indent=1)) if as_json else _print_sources(rows)
            return 0 if rows else 1
        o = launch([a for a in rest if not a.startswith("--")], use_sources="--sources" in rest)
        print(json.dumps(o, ensure_ascii=False, indent=1, default=str)) if as_json else _print_launch(o)
        return 0 if o["lamp"] in ("GREEN", "YELLOW") else 1
    return PRIOR.main(args)


def selftest() -> int:
    import shutil
    import tempfile
    p = f = 0

    def chk(name, cond, note=""):
        nonlocal p, f
        if cond:
            p += 1
        else:
            f += 1
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · %s" % (note,)) if note != "" else ""))

    keep = {k: os.environ.get(k) for k in ("VIA_FROM_VCGC", "VIA_VDF_HEALTH_OUT")}
    td = Path(tempfile.mkdtemp(prefix="vdfsm149-"))
    os.environ["VIA_VDF_HEALTH_OUT"] = str(td / "out")
    try:
        os.environ.pop("VIA_FROM_VCGC", None)
        chk("① 未經 VCGC / 啟動器 → engine run 拒(rc2)", main(["engine", "run", "ENG056"]) == 2)
        os.environ["VIA_FROM_VCGC"] = "YES"
        rows = _inv().engines("VDF")
        src = sources(rows)
        by = {s["family"]: s["sources"] for s in src}
        chk("② sources:真樹 ≥25 支 · ENG055 = TWSE+TPEx · MDL002 = yfinance · ENG082 三源 · 不收 _rebuilds_superseded · 路徑不重複", len(src) >= 25
            and not any(_SUPERSEDED in s["path"] for s in src) and len({s["path"] for s in src}) == len(src)
            and by.get("VDF_ENG055_OmniFetch") == ["TWSE", "TPEx"] and by.get("VDF_MDL002_YFinanceFetchingEngine") == ["yfinance"]
            and by.get("VDF_ENG082_FinStatements") == list(SOURCES), len(src))
        fake = td / "VDF_ENG999_LaunchFixture.py"
        fake.write_text("import os,sys\nprint('FROM', os.environ.get('VIA_FROM_VCGC'), 'NET', os.environ.get('VIA_NET_CONSENT', '-'))\n"
                        "sys.exit(int(sys.argv[1]) if len(sys.argv) > 1 else 0)\n", encoding="utf-8")
        net_keep = os.environ.pop("VIA_NET_CONSENT", None)
        r0, r7 = run_path(fake, [], capture=True), run_path(fake, ["7"], capture=True)
        if net_keep is not None:
            os.environ["VIA_NET_CONSENT"] = net_keep
        chk("③ run_path:子行程帶 VIA_FROM_VCGC=YES · 同意閘不代設 · rc 照傳(0 / 7)",
            r0["rc"] == 0 and r7["rc"] == 7 and any("FROM YES NET -" in ln for ln in r0["tail"]), (r0["rc"], r7["rc"], r0["tail"]))
        bad = td / "VDF_ENG998_Broken.py"
        bad.write_text("from x import (\n", encoding="utf-8")
        good = td / "VDF_ENG997_Loadable.py"
        good.write_text("def main():\n    return 0\n\nif __name__ == '__main__':\n    raise SystemExit(1)\n", encoding="utf-8")
        chk("④ load_probe:能載入 = rc0(不跑 __main__ 區)· 語法壞 = 非 0(不能起)", load_probe(good)["rc"] == 0 and load_probe(bad)["rc"] != 0)
        chk("⑤ engine run 找不到的引擎回 3(不猜)", main(["engine", "run", "NO_SUCH_ENGINE_ZZZ"]) == 3)
        o = launch(["ENG056"])
        one = (o["per"] or [{}])[0]
        chk("⑥ launch 真樹 ENG056:可啟動 · 自測 GREEN · 結果檔寫到 VIA_VDF_HEALTH_OUT", o["launchable"] == 1 and one.get("selftest_lamp") == "GREEN"
            and (td / "out" / "RESULT_engine_launch_latest.json").exists(), (o["launchable"], one.get("selftest_lamp")))
        chk("⑦ launch 找不到的鍵 → missing · 總燈 RED", launch(["NO_SUCH_ENGINE_ZZZ"])["lamp"] == "RED")
        body = Path(__file__).read_text(encoding="utf-8")
        chk("⑧ 三橋 · 不碰 TA-Lib · 不代設同意閘", all(t in body for t in ("[VIA:ACCEL-BRIDGE:v0100]", "[VIA:NET-BRIDGE:v0100]", "[VIA:LIB-BRIDGE:v0100]"))
            and "import " + "talib" not in body and 'environ["VIA_NET_' + 'CONSENT"] = "' not in body)
        print("  ── 前版鏈自測(原樣印出)──")
        prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
        chk("⑨ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    finally:
        for k, v in keep.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(td, ignore_errors=True)
    print("[計] VDF_SystemManager_v0149 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
