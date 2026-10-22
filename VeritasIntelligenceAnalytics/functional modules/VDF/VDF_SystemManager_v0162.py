#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_SystemManager v0162 — 薄尾:engine launch 並行 + 逐支進度 + 逾時照實 + 最慢先跑 + 紅燈序跑複驗 + 每支記憶體 / 執行緒預算

操作員令(2026-10-22):「為何指令跑不完 全部用記憶體 全部加入最新的加速器及網路工具」。
量測(改前):engine launch 96 支逐支序跑(每支 load_probe ≤120 s + --selftest ≤600 s),一次只用一核;整段跑完才印 →
  ActivateVDF 心跳一直「還沒有輸出」。工作站上一輪 2881 s;這一輪 23 分鐘被 Ctrl+C。逾時那支 tail 是空的(看不出是逾時)。
本版(判法 · 結果檔 · 合併規則照 v0150 launch_paths / save_launch):
  ① 並行:工作數 = VIA_VDF_LAUNCH_JOBS(ActivateVDF v0115 依核數 / 可用記憶體給)> 自算 min(核 − 1, (可用 − 保留 1 GB) ÷ 每支 700 MB),至少 1。
  ② 每支跑完立刻印一行「[n/N] 燈 秒 家族」(flush)→ 外層心跳看得到進度;最後照前版 _print_launch 總結。
  ③ 逾時照實:rc TIMEOUT → tail 第一行「逾時 N 秒(VIA_VDF_LAUNCH_TIMEOUT 可調)」+ 逾時前印出的最後幾行;燈 RED 不變。
  ④ 最慢先跑:照上一輪 RESULT_engine_launch_latest.json 各支秒數排序(沒紀錄的排前面)→ 牆鐘最短。
  ⑤ 並行時紅(非逾時)的那幾支 → 序跑複驗一次(排除並行搶同一個庫檔):複驗轉綠 / 缺料 → 照複驗,記 parallel;仍紅 → 紅。
  ⑥ 每支子行程環境:VIA_DUCKDB_MEM = VIA_VDF_LAUNCH_MEM_MB(沒給 = (可用 − 1 GB) × 0.9 ÷ 工作數)· 執行緒 = VIA_VDF_LAUNCH_THREADS(沒給 = 1);
     其餘照 v0149 run_path(VIA_FROM_VCGC=YES 啟動器標記 · 同意閘不加不減)。加速器 / 網路工具由 ActivateVDF 本輪鉤(PYTHONPATH)隨環境帶進每支。
不匯入他系統程式;零網路;同意閘不讀不寫;不碰 TA-Lib。
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

import concurrent.futures as cf
import datetime
import importlib.util
import json
import os
import re
import subprocess
import sys
import threading
import time
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA_ROOT = HERE.parents[1]
_STEM = "VDF_SystemManager"
TAG = "v" + Path(__file__).stem.rsplit("_v", 1)[-1]
RESERVE_MB_V0162 = 1024
PER_JOB_MB_V0162 = 700
THREAD_KEYS_V0162 = ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS", "NUMEXPR_MAX_THREADS",
                     "VECLIB_MAXIMUM_THREADS", "NUMBA_NUM_THREADS", "POLARS_MAX_THREADS", "RAYON_NUM_THREADS", "VIA_DUCKDB_THREADS")


def _vnum_v0162(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0162(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0162(p) < _vnum_v0162(__file__)), key=_vnum_v0162)
PRIOR = _load_v0162(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def _chain_v0162() -> list:
    out, m = [], PRIOR
    while isinstance(m, types.ModuleType) and m not in out:
        out.append(m)
        m = getattr(m, "PRIOR", None)
    return out


def _owner_v0162(name: str):
    for m in _chain_v0162():
        if name in vars(m):
            return m
    return None


_OWN_LP = _owner_v0162("launch_paths")          # v0150:engine launch 本體(main 叫模組全域 launch_paths)
_OWN_RP = _owner_v0162("run_path")              # v0149:_python · _LOAD_PROBE · run_path
_ORIG_LAUNCH_PATHS = _OWN_LP.launch_paths if _OWN_LP else None


# ---------------------------------------------------------------- 資源
def mem_avail_mb() -> int | None:
    try:
        import psutil
        return int(psutil.virtual_memory().available // 2**20)
    except Exception:  # noqa: BLE001 — psutil 缺 → /proc → 量不到照實 None
        pass
    try:
        for ln in Path("/proc/meminfo").read_text().splitlines():
            if ln.startswith("MemAvailable:"):
                return int(ln.split()[1]) // 1024
    except OSError:
        pass
    return None


def plan_jobs(n: int, env: dict | None = None, cores: int | None = None, avail: int | None = -1) -> dict:
    """→ {jobs, mem_mb, threads, why}:工作數 · 每支 DuckDB 記憶體 · 每支執行緒。"""
    env = os.environ if env is None else env
    cores = cores or os.cpu_count() or 1
    avail = mem_avail_mb() if avail == -1 else avail
    why = []
    try:
        want = int(env.get("VIA_VDF_LAUNCH_JOBS") or 0)
    except ValueError:
        want = 0
    if want > 0:
        jobs, src = want, "VIA_VDF_LAUNCH_JOBS"
    else:
        by_mem = (cores - 1) if avail is None else max(1, (avail - RESERVE_MB_V0162) // PER_JOB_MB_V0162)
        jobs, src = max(1, min(cores - 1, by_mem)), "自算(核 %d − 1 · 可用 %s MB ÷ %d)" % (cores, avail, PER_JOB_MB_V0162)
    jobs = max(1, min(jobs, max(1, n)))
    try:
        mem_mb = int(env.get("VIA_VDF_LAUNCH_MEM_MB") or 0)
    except ValueError:
        mem_mb = 0
    if mem_mb <= 0:
        mem_mb = 1024 if avail is None else max(256, int((avail - RESERVE_MB_V0162) * 0.9) // jobs)
    try:
        threads = max(1, int(env.get("VIA_VDF_LAUNCH_THREADS") or 1))
    except ValueError:
        threads = 1
    why.append(src)
    return {"jobs": jobs, "mem_mb": mem_mb, "threads": threads, "cores": cores, "avail_mb": avail, "why": why}


def child_env(plan: dict, base: dict | None = None) -> dict:
    env = dict(os.environ if base is None else base, VIA_FROM_VCGC="YES")
    env["VIA_DUCKDB_MEM"] = "%dMB" % plan["mem_mb"]
    for k in THREAD_KEYS_V0162:
        env[k] = str(plan["threads"])
    env["PYTHONIOENCODING"] = "utf-8"
    return env


# ---------------------------------------------------------------- 單支(子行程)
def _tail(out: str, n: int = 3) -> list:
    return [ln for ln in (out or "").splitlines() if ln.strip()][-n:]


def run_cmd(cmd: list, cwd: str, env: dict, timeout: float | None) -> dict:
    t0 = time.time()
    try:
        r = subprocess.run(cmd, cwd=cwd, env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout)
        rc, out = r.returncode, (r.stdout or "") + (r.stderr or "")
        tail = _tail(out)
    except subprocess.TimeoutExpired as exc:
        part = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", "replace")
        rc = "TIMEOUT"
        tail = ["逾時 %d 秒(VIA_VDF_LAUNCH_TIMEOUT 可調)" % int(timeout or 0)] + _tail(part, 2)
    return {"rc": rc, "secs": round(time.time() - t0, 1), "tail": tail}


def launch_one(item: dict, py: str, py_src: str, env: dict, timeout: float, probe_code: str) -> dict:
    """同 v0150 一支的判法:閘紅 → 不起;load_probe(import 不跑 main)→ 有 --selftest 就跑自測。"""
    r, path, g = item["row"], Path(item["abs"]), item["gate"]
    if g.get("lamp") == "RED":
        ld = {"rc": "GATE", "secs": 0, "tail": g.get("block") or []}
    else:
        ld = run_cmd([py, "-c", probe_code, str(path)], str(path.parent), env, min(120.0, timeout))
    st = None
    if ld["rc"] == 0 and "--selftest" in (r.get("flags") or []):
        st = run_cmd([py, str(path), "--selftest"], str(path.parent), env, timeout)
        st.update(python=py, python_src=py_src)
    lamp = "—" if st is None else ("GREEN" if st["rc"] == 0 else "NODATA" if st["rc"] == 2 else "RED")
    return {"eid": r.get("eid"), "family": r.get("family"), "path": item["path"], "gate": g.get("lamp"), "launchable": ld["rc"] == 0,
            "load": ld, "selftest": st, "selftest_lamp": lamp}


def _prev_secs() -> dict:
    try:
        f = PRIOR._out() / "RESULT_engine_launch_latest.json"
        prev = json.loads(f.read_text(encoding="utf-8"))
        return {p["path"]: float((p.get("selftest") or {}).get("secs") or 0) + float((p.get("load") or {}).get("secs") or 0)
                for p in prev.get("per") or [] if p.get("path")}
    except (OSError, ValueError, TypeError, AttributeError):
        return {}


def run_items(items: list, plan: dict, timeout: float, py: str, py_src: str, probe_code: str, out=print, recheck: bool = True) -> dict:
    """items:[{row, path, abs, gate}] → per(照 items 原順序)。並行跑、逐支印、紅的序跑複驗。"""
    env = child_env(plan)
    n = len(items)
    prev = _prev_secs()
    order = sorted(range(n), key=lambda i: -(prev.get(items[i]["path"], 10**9)))     # 沒紀錄的(10**9)最先 → 再照上一輪秒數由長到短
    res: dict = {}
    done = [0]
    lock = threading.Lock()
    t0 = time.time()

    def _job(i):
        return i, launch_one(items[i], py, py_src, env, timeout, probe_code)

    out("  [並行] 引擎 %d 支 · 工作 %d · 每支 DuckDB %d MB · 執行緒 %d · 逾時 %d 秒 · %s" % (
        n, plan["jobs"], plan["mem_mb"], plan["threads"], int(timeout), " · ".join(plan.get("why") or [])), flush=True)
    with cf.ThreadPoolExecutor(max_workers=plan["jobs"]) as ex:
        futs = [ex.submit(_job, i) for i in order]
        for fu in cf.as_completed(futs):
            i, p = fu.result()
            res[i] = p
            with lock:
                done[0] += 1
                secs = ((p.get("selftest") or {}).get("secs") or 0) + (p["load"].get("secs") or 0)
                lamp = p["selftest_lamp"] if p["launchable"] else "不能起"
                extra = ""
                if (p.get("selftest") or {}).get("rc") == "TIMEOUT" or p["load"].get("rc") == "TIMEOUT":
                    extra = " · 逾時"
                out("  [%d/%d] %-6s %6.1fs  %s%s" % (done[0], n, lamp, secs, p["family"], extra), flush=True)
    wall = round(time.time() - t0, 1)
    rechecked = []
    if recheck and plan["jobs"] > 1:
        redo = [i for i in range(n) if res[i]["selftest_lamp"] == "RED" and (res[i].get("selftest") or {}).get("rc") != "TIMEOUT"]
        if redo:
            out("  [複驗] 並行紅 %d 支 → 序跑一次(排除並行搶同一個庫檔)" % len(redo), flush=True)
            solo = dict(plan, jobs=1, mem_mb=max(plan["mem_mb"], int(plan["mem_mb"] * plan["jobs"] * 0.5)))
            env1 = child_env(solo)
            for i in redo:
                p2 = launch_one(items[i], py, py_src, env1, timeout, probe_code)
                was = res[i]
                if p2["selftest_lamp"] in ("GREEN", "NODATA"):
                    p2["parallel"] = {"selftest_lamp": was["selftest_lamp"], "rc": (was.get("selftest") or {}).get("rc"), "tail": (was.get("selftest") or {}).get("tail")}
                    res[i] = p2
                else:
                    was["recheck"] = {"selftest_lamp": p2["selftest_lamp"], "rc": (p2.get("selftest") or {}).get("rc")}
                rechecked.append({"family": res[i]["family"], "parallel": was["selftest_lamp"], "solo": p2["selftest_lamp"]})
                out("  [複驗] %-6s → %-6s %s" % (was["selftest_lamp"], p2["selftest_lamp"], res[i]["family"]), flush=True)
    per = [res[i] for i in range(n)]
    busy = round(sum(((p.get("selftest") or {}).get("secs") or 0) + (p["load"].get("secs") or 0) for p in per), 1)
    return {"per": per, "wall_secs": wall, "busy_secs": busy, "rechecked": rechecked}


# ---------------------------------------------------------------- engine launch(換 v0150 模組全域)
def launch_paths(paths: list) -> dict:
    inv = PRIOR._inv()
    by = {r["path"]: r for r in inv.engines("VDF")}
    per_fixed, items = {}, []
    for k, path in enumerate(paths):
        r = by.get(path)
        if r is None:
            per_fixed[k] = {"eid": "?", "family": Path(path).stem, "path": path, "gate": "ABSENT", "launchable": False,
                            "load": {"rc": "ABSENT", "secs": 0, "tail": ["不在引擎冊"]}, "selftest": None, "selftest_lamp": "—"}
            continue
        items.append({"k": k, "row": r, "path": path, "abs": str(VIA_ROOT / path), "gate": inv.gate(r, "VDF")})
    plan = plan_jobs(len(items))
    timeout = float(os.environ.get("VIA_VDF_LAUNCH_TIMEOUT") or 600)
    py, py_src = _OWN_RP._python()
    run = run_items(items, plan, timeout, py, py_src, _OWN_RP._LOAD_PROBE)
    for it, p in zip(items, run["per"]):
        per_fixed[it["k"]] = p
    per = [per_fixed[k] for k in sorted(per_fixed)]
    o = {"via": "vdf", "verb": "engine launch", "tag": "%s %s" % (_STEM, TAG), "ts": datetime.datetime.now().isoformat(timespec="seconds"),
         "n": len(per), "launchable": sum(1 for p in per if p["launchable"]),
         "selftest": {k: sum(1 for p in per if p["selftest_lamp"] == k) for k in ("GREEN", "NODATA", "RED", "—")}, "missing": [], "per": per,
         "jobs": plan["jobs"], "mem_mb": plan["mem_mb"], "wall_secs": run["wall_secs"], "busy_secs": run["busy_secs"], "rechecked": run["rechecked"],
         "timeouts": [p["family"] for p in per if (p.get("selftest") or {}).get("rc") == "TIMEOUT" or p["load"].get("rc") == "TIMEOUT"]}
    o["lamp"] = "RED" if o["launchable"] < o["n"] else ("GREEN" if not (o["selftest"]["RED"] or o["selftest"]["NODATA"]) else "YELLOW")
    o["result"] = _OWN_LP.save_launch(o)
    print("  [並行] 牆鐘 %.1f 秒 · 各支合計 %.1f 秒(省 %.0f%%)· 逾時 %d 支%s" % (
        o["wall_secs"], o["busy_secs"], 100.0 * (1 - o["wall_secs"] / o["busy_secs"]) if o["busy_secs"] else 0.0, len(o["timeouts"]),
        (":" + ", ".join(o["timeouts"][:8])) if o["timeouts"] else ""), flush=True)
    return o


def _patch_v0162() -> bool:
    if _OWN_LP is None:
        return False
    _OWN_LP.launch_paths = launch_paths
    return True


def _unpatch_v0162() -> None:
    if _OWN_LP is not None and _ORIG_LAUNCH_PATHS is not None:
        _OWN_LP.launch_paths = _ORIG_LAUNCH_PATHS


PATCHED_V0162 = _patch_v0162()


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args[:2]:
        return selftest()
    return PRIOR.main(args)


_FAKE = {"green": "import sys,time\nif '--selftest' in sys.argv:\n    time.sleep(1.0); print('[計] ok'); sys.exit(0)\n",
         "nodata": "import sys\nif '--selftest' in sys.argv:\n    print('缺料'); sys.exit(2)\n",
         "red": "import sys\nif '--selftest' in sys.argv:\n    print('[FAIL] x'); sys.exit(1)\n",
         "slow": "import sys,time\nif '--selftest' in sys.argv:\n    print('起跑', flush=True); time.sleep(30); sys.exit(0)\n",
         "flaky": "import os,sys\nif '--selftest' in sys.argv:\n    sys.exit(0 if os.environ.get('VIA_DUCKDB_MEM','').startswith(os.environ.get('_SOLO_MARK','x')) else 1)\n"}


def selftest() -> int:
    import io
    import shutil
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

    print("=== %s %s · 薄尾自測(engine launch 並行 · 進度 · 逾時 · 複驗)===" % (_STEM, TAG))
    pl = plan_jobs(96, env={}, cores=8, avail=6680)
    chk("① 工作數自算:8 核 · 可用 6680 MB → min(7, (6680−1024)÷700=8) = 7 · 每支 DuckDB (6680−1024)×0.9÷7 = %d MB · 執行緒 1" % pl["mem_mb"],
        pl["jobs"] == 7 and pl["mem_mb"] == int((6680 - 1024) * 0.9) // 7 and pl["threads"] == 1, pl)
    pl2 = plan_jobs(96, env={"VIA_VDF_LAUNCH_JOBS": "3", "VIA_VDF_LAUNCH_MEM_MB": "900", "VIA_VDF_LAUNCH_THREADS": "2"}, cores=8, avail=6680)
    pl3 = plan_jobs(2, env={}, cores=8, avail=None)
    chk("② ActivateVDF 給的工作數 / 每支記憶體 / 執行緒優先;引擎比工作數少 → 工作數 = 引擎數;量不到記憶體 → 照核數",
        (pl2["jobs"], pl2["mem_mb"], pl2["threads"]) == (3, 900, 2) and pl3["jobs"] == 2, (pl2, pl3))
    env = child_env(pl2, base={"VIA_NET_CONSENT": "sentinel"})
    chk("③ 子行程環境:VIA_DUCKDB_MEM 900MB · 執行緒鍵 = 2 · VIA_FROM_VCGC=YES · 同意閘原樣(不加不減)",
        env["VIA_DUCKDB_MEM"] == "900MB" and env["OMP_NUM_THREADS"] == "2" and env["VIA_FROM_VCGC"] == "YES" and env["VIA_NET_CONSENT"] == "sentinel")
    tmp = Path(tempfile.mkdtemp(prefix="vdf_sm0162_"))
    try:
        items = []
        for name in ("green", "green2", "green3", "green4", "nodata", "red", "slow", "flaky"):
            src = _FAKE[name.rstrip("234")]
            fp = tmp / ("VDF_ENG9%02d_Fake_%s_v0100.py" % (len(items), name))
            fp.write_text(src, encoding="utf-8")
            items.append({"row": {"eid": "ENG9%02d" % len(items), "family": fp.stem.rsplit("_v", 1)[0], "flags": ["--selftest"]},
                          "path": fp.name, "abs": str(fp), "gate": {"lamp": "GREEN"}})
        items.append({"row": {"eid": "ENG999", "family": "VDF_ENG999_Gated", "flags": ["--selftest"]}, "path": "gated.py", "abs": str(tmp / "gated.py"),
                      "gate": {"lamp": "RED", "block": ["閘紅"]}})
        buf = io.StringIO()
        os.environ["_SOLO_MARK"] = "10000"                 # 序跑複驗給較大的記憶體(5000 × 4 工作 × 0.5)→ flaky 只有複驗時過
        lines = []

        def _out(s, flush=True):
            lines.append(s)
        plan = {"jobs": 4, "mem_mb": 5000, "threads": 1, "why": ["自測"]}
        t0 = time.time()
        r = run_items(items, plan, 4.0, sys.executable, "自測", _OWN_RP._LOAD_PROBE if _OWN_RP else "print('LOADED')", out=_out)
        wall = time.time() - t0
        lamp = {pp["family"].split("_Fake_")[-1] if "_Fake_" in pp["family"] else pp["family"]: pp["selftest_lamp"] for pp in r["per"]}
        chk("④ 判法同 v0150:綠 rc0 · 缺料 rc2 = NODATA · rc1 = RED · 閘紅不起(—)", lamp.get("green") == "GREEN" and lamp.get("nodata") == "NODATA"
            and lamp.get("red") == "RED" and lamp.get("VDF_ENG999_Gated") == "—" and not r["per"][-1]["launchable"], lamp)
        slow = next(pp for pp in r["per"] if pp["family"].endswith("_slow"))
        chk("⑤ 逾時照實:rc TIMEOUT · tail 第一行「逾時 4 秒」· 逾時前印的「起跑」也留著 · 燈 RED",
            slow["selftest"]["rc"] == "TIMEOUT" and slow["selftest"]["tail"][0].startswith("逾時 4 秒") and "起跑" in " ".join(slow["selftest"]["tail"])
            and slow["selftest_lamp"] == "RED", slow["selftest"])
        chk("⑥ 逐支進度:每支跑完印一行 [n/N](共 %d 行)· 開頭印並行計畫" % sum(1 for s in lines if re.match(r"\s*\[\d+/\d+\]", s)),
            sum(1 for s in lines if re.match(r"\s*\[\d+/9\]", s)) == 9 and lines[0].lstrip().startswith("[並行]"), lines[:3])
        chk("⑦ 並行真的省時:4 支各睡 1 秒 + 逾時 4 秒的那支,牆鐘 %.1f 秒 < 序跑合計 %.1f 秒" % (r["wall_secs"], r["busy_secs"]),
            r["wall_secs"] < r["busy_secs"] * 0.8, (r["wall_secs"], r["busy_secs"], wall))
        fl = next(pp for pp in r["per"] if pp["family"].endswith("_flaky"))
        chk("⑧ 並行紅的序跑複驗一次:flaky 並行紅 → 複驗綠(記 parallel)· 真紅的 red 仍紅(記 recheck)· 逾時的不複驗",
            fl["selftest_lamp"] == "GREEN" and fl.get("parallel", {}).get("selftest_lamp") == "RED"
            and next(pp for pp in r["per"] if pp["family"].endswith("_red")).get("recheck", {}).get("selftest_lamp") == "RED"
            and not any(x["family"].endswith("_slow") for x in r["rechecked"]), r["rechecked"])
        chk("⑨ 結果照 items 原順序回(合併 / 寫檔照 v0150 save_launch)", [pp["path"] for pp in r["per"]] == [it["path"] for it in items])
    finally:
        os.environ.pop("_SOLO_MARK", None)
        shutil.rmtree(tmp, ignore_errors=True)
    chk("⑩ engine launch 已換本版(v0150 模組全域 launch_paths;main 走它)", PATCHED_V0162 and _OWN_LP is not None and _OWN_LP.launch_paths is launch_paths)
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("⑪ 不匯入他系統程式 · 兩座橋在 · 同意閘不寫 · 零網路(不 import 抓取套件)",
        not re.search(r"^\s*(import|from)\s+(CGC_|VRN_|VCGC)", src, re.M) and "VIA:ACCEL-BRIDGE" in src and "VIA:NET-BRIDGE" in src
        and "_CONSENT\"] =" not in body and not re.search(r"^\s*import\s+(requests|httpx|urllib\.request)", body, re.M))
    print("  ── 前版鏈自測(原樣印出;VIA_SKIP_PRIOR_SELFTEST=1 略過)──")
    _unpatch_v0162()
    try:
        prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    finally:
        _patch_v0162()
    chk("⑫ 前版鏈 %s 自測 rc 0 · 跑完本版又換上" % PRIOR_PATH.stem, prc == 0 and _OWN_LP.launch_paths is launch_paths)
    print("[計] %s_%s 自測 %d/%d · %s" % (_STEM, TAG, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
