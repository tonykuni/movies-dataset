#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL230_ToolCoverageProbe v0107 — 薄尾(v0100–v0106 一字不動):覆蓋矩陣提速(逐檔結果快取 + 多核並行)

操作員 2026-11-25:「出新版 覆蓋矩陣更快」。先量:
  容器 cProfile(v0106 matrix --no-pwsh)51.4s:py_ast(1782 檔逐檔 ast.parse + 全樹 walk)33.6s · catalog/describe(744 檔再剖一次)12.7s。
  工作站實跑(VIA_GovernanceApply v0101 心跳):一次 225–350s。
本版判法一字不改(py_ast / describe 仍是 v0102 / v0103 那兩支純函式,結果只取決於檔案內容 + 設定),只改怎麼算:
  ① 逐檔結果快取:鍵 = 檔案內容 sha1 + 設定(ssot["ast"] / 分類表)+ 判法本體檔的 sha1(判法一改快取自動失效)。
     快取在 TEMP\\VIA_token_cache\\MDL230_v0107.json(本機產物;每輪只留本輪用到的鍵,不會越長越大)。
  ② 沒命中的檔先在多核上並行算好(行程池,道數 = CPU 核數,上限 8),矩陣主流程再照原順序取用 → 冷跑也快。
     行程池起不來(例:被當成函式庫 import、Windows spawn 拿不到主模組)就照原樣逐檔算,結果相同。
  ③ 報告加「快取命中 / 並行算 / 逐檔算」三個數。
用法照前版:VIA_FROM_VCGC=YES python CGC_MDL230_ToolCoverageProbe_v0107.py matrix [--no-pwsh] [--json] · --selftest
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

import hashlib
import importlib.util
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAMILY = "CGC_MDL230_ToolCoverageProbe"
ENGINE_TAG = "CGC_MDL230_ToolCoverageProbe v0107"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0107", PRIOR_PATH)
_PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _PRIOR
_spec.loader.exec_module(_PRIOR)


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(_PRIOR, name)


def _owner(fn_name: str):
    """沿前版鏈找「自己定義這支函式」的模組(py_ast 在 v0102、describe / catalog / matrix 在 v0103)。"""
    m = _PRIOR
    while m is not None:
        f = vars(m).get(fn_name)
        if f is not None and getattr(f, "__module__", None) == m.__name__:
            return m
        m = vars(m).get("_PRIOR")
    return None


M_AST = _owner("py_ast")
M_DESC = _owner("describe")
_ORIG_PY_AST = M_AST.py_ast
_ORIG_DESCRIBE = M_DESC.describe
_ORIG_MATRIX = M_DESC.matrix
_JUDGE_SHA = hashlib.sha1(Path(M_AST.__file__).read_bytes() + Path(M_DESC.__file__).read_bytes()).hexdigest()[:12]
CACHE_PATH = Path(tempfile.gettempdir()) / "VIA_token_cache" / "MDL230_v0107.json"
MAX_LANES = 8
STATS = {"hit": 0, "par": 0, "serial": 0, "lanes": 0, "warm_s": 0.0}
_CACHE: dict = {}
_USED: set = set()


def _cfg_key(kind: str, cfg) -> str:
    return hashlib.sha1((kind + _JUDGE_SHA + json.dumps(cfg, sort_keys=True, ensure_ascii=False, default=str)).encode("utf-8")).hexdigest()[:12]


def _key(cfgk: str, text: str) -> str:
    return cfgk + hashlib.sha1(text.encode("utf-8", "surrogatepass")).hexdigest()


def _load_cache() -> None:
    _CACHE.clear()
    _USED.clear()
    try:
        _CACHE.update(json.loads(CACHE_PATH.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        pass


def _save_cache() -> None:
    try:
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        keep = {k: v for k, v in _CACHE.items() if k in _USED}
        tmp = CACHE_PATH.with_name(CACHE_PATH.name + f".{os.getpid()}.tmp")
        tmp.write_text(json.dumps(keep, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, CACHE_PATH)
    except OSError:
        pass                                              # 快取寫不進去不影響結果


def py_ast(text: str, ssot: dict) -> dict:
    k = _key(_cfg_key("ast", ssot.get("ast")), text)
    _USED.add(k)
    if k in _CACHE:
        STATS["hit"] += 1
        return dict(_CACHE[k])
    STATS["serial"] += 1
    r = _ORIG_PY_AST(text, ssot)
    _CACHE[k] = r
    return dict(r)


def describe(text: str, cats: list) -> dict:
    k = _key(_cfg_key("desc", cats), text)
    _USED.add(k)
    if k in _CACHE:
        STATS["hit"] += 1
        return dict(_CACHE[k])
    STATS["serial"] += 1
    r = _ORIG_DESCRIBE(text, cats)
    _CACHE[k] = r
    return dict(r)


def _work(job):
    """行程池工人:job = (種類, 鍵, 原文, 設定)。只呼叫原判法,回 (鍵, 結果)。"""
    kind, k, text, cfg = job
    return k, (_ORIG_PY_AST(text, cfg) if kind == "ast" else _ORIG_DESCRIBE(text, cfg))


def _can_pool() -> bool:
    if os.environ.get("VIA_MDL230_SERIAL") == "1":
        return False
    import multiprocessing as mp
    if mp.get_start_method(allow_none=True) in (None, "fork") and sys.platform != "win32":
        return True                                       # fork:子行程直接繼承已載入的判法
    main = sys.modules.get("__main__")
    return bool(main and getattr(main, "__file__", None) and Path(main.__file__).resolve() == Path(__file__).resolve())


def warm(root: Path, ssot: dict) -> None:
    """跟 v0102 matrix / v0103 catalog 同一套篩法挑出要算的檔,沒命中快取的先並行算好。"""
    t0 = time.time()
    m102 = M_AST
    sw, _ = m102._tail_module(m102.HERE, "via_bridge_sweeper_v*.py", "_mdl230_sweeper_warm")
    if sw is None:
        return
    live, _how = sw._live_set(root)
    cats = M_DESC.categories()
    groups = set(ssot["catalog"]["groups"])
    ka, kd = _cfg_key("ast", ssot.get("ast")), _cfg_key("desc", cats)
    jobs, seen = [], set()
    for p in sorted(root.rglob("*.py")):
        rel = str(p.relative_to(root)).replace("\\", "/")
        if sw.classify(rel) == "SKIP" or (live is not None and str(p) not in live):
            continue
        try:
            t = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        k = _key(ka, t)
        if k not in _CACHE and k not in seen:
            jobs.append(("ast", k, t, ssot))
            seen.add(k)
        if m102.group_of(rel, ssot) in groups:
            k2 = _key(kd, t)
            if k2 not in _CACHE and k2 not in seen:
                jobs.append(("desc", k2, t, cats))
                seen.add(k2)
    lanes = max(1, min(MAX_LANES, os.cpu_count() or 1))
    if len(jobs) >= 40 and lanes > 1 and _can_pool():
        try:
            from concurrent.futures import ProcessPoolExecutor
            with ProcessPoolExecutor(max_workers=lanes) as ex:
                for k, r in ex.map(_work, jobs, chunksize=max(8, len(jobs) // (lanes * 8))):
                    _CACHE[k] = r
            STATS["par"] += len(jobs)
            STATS["lanes"] = lanes
        except Exception as exc:                          # noqa: BLE001 — 起不來就照原樣逐檔算(結果相同)
            print(f"  [{ENGINE_TAG}] 行程池沒起來({type(exc).__name__});照原樣逐檔算", flush=True)
    STATS["warm_s"] = round(time.time() - t0, 1)


def matrix(root=None, ssot: dict | None = None, no_pwsh: bool = False) -> dict:
    root = Path(root) if root is not None else M_DESC.VIA
    given = ssot
    if ssot is None:
        ssot, _name = M_AST.load_ssot()
    _load_cache()
    for k in STATS:
        STATS[k] = 0 if k != "warm_s" else 0.0
    warm(root, ssot)
    rep = _ORIG_MATRIX(root, ssot=given, no_pwsh=no_pwsh)    # 沒給就照前版自己讀(報告的 ssot 冊名照前版寫)
    _save_cache()
    rep["speed"] = {"cache_hit": STATS["hit"], "parallel": STATS["par"], "serial": STATS["serial"], "lanes": STATS["lanes"],
                    "warm_s": STATS["warm_s"], "engine": ENGINE_TAG}
    print(f"  [{ENGINE_TAG}] 逐檔判讀:快取命中 {STATS['hit']} · 並行算 {STATS['par']}({STATS['lanes']} 道 · {STATS['warm_s']}s)· 逐檔算 {STATS['serial']}", flush=True)
    return rep


M_AST.py_ast = py_ast
M_DESC.describe = describe
M_DESC.matrix = matrix


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:240]) if note and not cond else ""), flush=True)

    print(f"[計] {ENGINE_TAG} 自測開始(本版 5 項 + 前版自測 · 暫存夾 · 零網路)", flush=True)
    import contextlib
    import io
    import subprocess

    def verdicts(txt: str) -> list:
        return [ln.strip().split(" · ")[0] for ln in txt.splitlines() if ln.strip().startswith(("[OK]", "[FAIL]"))]
    base = subprocess.run([sys.executable, str(PRIOR_PATH), "--selftest"], capture_output=True, text=True, encoding="utf-8",
                          errors="replace", cwd=str(HERE), timeout=1200)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc_new = _PRIOR.main(["--selftest"])               # 換上本版快取 / 並行判讀後,前版鏈自測再跑一次
    vb, vn = verdicts(base.stdout), verdicts(buf.getvalue())
    diff = [x for x in vn if x not in vb] + [x for x in vb if x not in vn]
    print(f"  (前版 {PRIOR_PATH.name} 單跑 rc {base.returncode} · 判定 {len(vb)} 行;容器真樹檢查本來就有 FAIL,照實不改)", flush=True)
    chk("T1 換上本版後,前版鏈自測每一行判定與單跑前版相同(rc 相同)", vb and vb == vn and base.returncode == rc_new, diff[:4])
    ssot, _n = M_AST.load_ssot()
    cats = M_DESC.categories()
    samples = ['"""d."""\nimport requests\nVIA_ACCEL.x()\n', "x = 1\n", "def f(:\n", '"""doc."""\ndef fetch_data():\n    pass\nclass Repo:\n    pass\n']
    global CACHE_PATH
    old_path = CACHE_PATH
    with tempfile.TemporaryDirectory(prefix="mdl230_107_") as td:
        CACHE_PATH = Path(td) / "c.json"
        _load_cache()
        a1 = [py_ast(s, ssot) for s in samples]
        d1 = [describe(s, cats) for s in samples]
        _save_cache()
        _load_cache()
        hits0 = STATS["hit"]
        a2 = [py_ast(s, ssot) for s in samples]
        d2 = [describe(s, cats) for s in samples]
        chk("T2 結果與原判法逐字相同(py_ast · describe;含剖析不過的檔)",
            a1 == [_ORIG_PY_AST(s, ssot) for s in samples] and d1 == [_ORIG_DESCRIBE(s, cats) for s in samples], (a1, d1))
        chk("T3 第二次全由快取取(命中 8)且結果相同", STATS["hit"] - hits0 == 8 and a2 == a1 and d2 == d1, STATS)
        cfg2 = dict(ssot, ast=dict(ssot["ast"], py_net_need_mods=list(ssot["ast"]["py_net_need_mods"]) + ["zzz_fx"]))
        chk("T4 設定一改鍵就變(不拿舊設定的結果)", _key(_cfg_key("ast", cfg2["ast"]), samples[0]) != _key(_cfg_key("ast", ssot["ast"]), samples[0]))
        jobs = [("ast", "k%d" % i, samples[i % 4] + f"# {i}\n", ssot) for i in range(48)]
        t0 = time.time()
        if _can_pool():
            from concurrent.futures import ProcessPoolExecutor
            with ProcessPoolExecutor(max_workers=2) as ex:
                par = dict(ex.map(_work, jobs, chunksize=8))
        else:
            par = dict(map(_work, jobs))
        ser = {k: _ORIG_PY_AST(t, c) for _kind, k, t, c in jobs}
        chk("T5 並行算的結果與逐檔算相同(48 檔)", par == ser, round(time.time() - t0, 2))
    CACHE_PATH = old_path
    _load_cache()
    print(f"[計] {ENGINE_TAG} 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    return _PRIOR.main(a)


if __name__ == "__main__":
    raise SystemExit(main())
