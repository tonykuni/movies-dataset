#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_MDL013_ActivateVDF v0102 — 薄尾:工作站實測(2026-10-18)三處修正

工作站(8 核 · 可用 4.4 GB · Python 3.12 · 雙閘開)跑 v0101:② 兩張清單 GREEN(依序跑,沒撞寫入鎖);③ 擷取與引擎並行、
資料庫流程等擷取;心跳每 30 秒一段。看到三個問題:
  ① 自測 ⑩ FAIL(兩次都是):(db−fetch 2.21 · engine−fetch 1.43 · 三條 GREEN)。⑩ 要 engine launch 在擷取起跑後 0.55 秒內起,
     但引擎流程要先起一支 engine list 子行程拿名單、再起 engine launch;Windows 起一支 Python 約 1 秒,兩支疊起來必超過。
     這是 ⑩ 的門檻寫錯(把 Linux 起行程的快當前提),不是流程錯:工作站真跑擷取 15:25 起、引擎 15:26 起,兩條確實並行。
     也不能把 engine list 挪到清單階段先跑:v0100 ⑤ 釘住「兩張清單跑完驗收過,三條流程(含 engine list)才起」(操作員令)。
     → 本版 ⑫ 換掉 ⑩:同一個性質(引擎與擷取並行 · 資料庫等擷取 · 清單依序),假擷取拉長到 3 秒、子行程起慢 0.8 秒照樣要過;
       委派前版自測時只容 v0101 的 ⑩ 一條失敗(照印「由 ⑫ 取代」),其餘任何一條失敗照判 FAIL,並補跑 v0100 自測。
     另:engine list 在 v0100 是 subprocess.run(沒登記),心跳看不到、Ctrl+C 收不到(最多再跑 600 秒)
     → 改 Popen 登記在跑:心跳列得到 engine_list、Ctrl+C 一起收、引擎流程記 INTERRUPTED(不是紅);完成印一行。
  ② SyntaxWarning:v0101 第 635 行自測正則少了 r 前綴(`\]` `\s`),Python 3.12 每次載入都印。v0101 已發佈不改;
     本版載入前版時把 SyntaxWarning / DeprecationWarning 擋在載入那一刻(只擋編譯警告,執行期警告照常)。
     心跳的「日誌最後一行」略過 SyntaxWarning / DeprecationWarning / `<unknown>:N:` 這種編譯雜訊,改顯示真正的進度行。
  ③ `Error. nthreads cannot be larger than environment variable "NUMEXPR_MAX_THREADS" (2)`:v0100 把 NUMEXPR_MAX_THREADS
     設成每條執行緒數(2);子行程裡的加速器(Celeritas apply_thread_limits)再把 NUMEXPR_NUM_THREADS 拉高 → numexpr 拒絕。
     → NUMEXPR_NUM_THREADS = 每條執行緒數(真正用量照舊受限);NUMEXPR_MAX_THREADS = 核數 × 2(只是上限天花板,不再比
       加速器設的用量小)。其餘執行緒上限(OMP / MKL / OPENBLAS / POLARS / VIA_DUCKDB_THREADS)不動。
其餘全照 v0101(薄尾;前版不動)。VDF 自己的模組:不匯入他系統程式;同意閘不讀不寫;不碰 TA-Lib。
"""
from __future__ import annotations
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

import importlib.util
import json
import os
import re
import subprocess
import sys
import threading
import time
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_MDL013_ActivateVDF"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def _vnum_v0102(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0102(p) < _vnum_v0102(__file__)), key=_vnum_v0102)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
with warnings.catch_warnings():                    # 只擋載入那一刻的編譯警告(v0101 第 635 行少 r 前綴;已發佈不改)
    warnings.simplefilter("ignore", SyntaxWarning)
    warnings.simplefilter("ignore", DeprecationWarning)
    _spec.loader.exec_module(PRIOR)
V0100 = PRIOR.PRIOR                                # 前版鏈的流程函式讀 v0100 模組全域 → 本版換在那裡


def __getattr__(name):
    return getattr(PRIOR, name)


# ---------------------------------------------------------------- ③ numexpr 執行緒上限
_FLOW_ENV_V0100 = V0100.flow_env


def flow_env(res: dict, flow: str, base_env: dict | None = None) -> dict:
    """同 v0100 flow_env;numexpr 用量 = 每條執行緒數,上限天花板 = 核數 × 2(加速器拉高用量時不再被 numexpr 拒絕)。"""
    env = _FLOW_ENV_V0100(res, flow, base_env)
    th = int(res["plan"]["threads_per_flow"])
    env["NUMEXPR_NUM_THREADS"] = str(th)
    env["NUMEXPR_MAX_THREADS"] = str(max(th, 2 * (os.cpu_count() or 1)))
    return env


# ---------------------------------------------------------------- ② 心跳略過編譯雜訊
_NOISE = re.compile(r"SyntaxWarning|DeprecationWarning|^<unknown>:\d+:|^\S+\.py:\d+: \w*Warning")


def _last_line(log: Path) -> str:
    """同 v0101 _last_line(日誌最後一行,最多 110 字),但略過編譯警告這類雜訊行。"""
    try:
        with open(log, "rb") as fh:
            fh.seek(0, 2)
            n = fh.tell()
            fh.seek(max(0, n - 8192))
            tail = fh.read().decode("utf-8", "replace")
    except OSError:
        return ""
    lines = [ln.strip() for ln in tail.splitlines() if ln.strip() and not _NOISE.search(ln.strip())]
    return lines[-1][:110] if lines else ""


# ---------------------------------------------------------------- ① engine list 登記在跑
_ENGINE_LIST_CARD: dict = {}


def engine_ids(env: dict, log_dir: Path, manager: Path | None = None, py: str | None = None) -> tuple:
    """同 v0100 engine_ids(→ 要啟動的家族全名, 跳過的 [{eid, family, path}]),改 Popen 登記在跑:心跳看得到 · Ctrl+C 收得到;
    stdout 只收 JSON(stderr 另檔,警告不混進來);完成印一行(不印 JSON 全文)。"""
    name = "engine_list"
    mgr = manager or V0100.manager_path()
    if mgr is None or PRIOR.STOP.is_set():
        return [], []
    log = Path(log_dir) / f"{name}.log"
    err = Path(log_dir) / f"{name}.err.log"
    kw = {"creationflags": getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)} if os.name == "nt" else {"start_new_session": True}
    t0 = time.time()
    note = ""
    with open(log, "w", encoding="utf-8", errors="replace") as fo, open(err, "w", encoding="utf-8", errors="replace") as fe:
        p = subprocess.Popen([py or sys.executable, str(mgr), "engine", "list", "--json"], cwd=str(mgr.parent),
                             env=dict(env, PYTHONUNBUFFERED="1"), stdout=fo, stderr=fe, **kw)
        with PRIOR._LOCK:
            PRIOR.RUNNING[name] = {"t0": t0, "log": err, "proc": p}      # 心跳讀 stderr 那份(stdout 要到最後才吐 JSON)
        PRIOR._hb_start()
        try:
            while True:
                try:
                    p.wait(timeout=0.5)
                    break
                except subprocess.TimeoutExpired:
                    if PRIOR.STOP.is_set():
                        PRIOR._kill_tree(p)
                        note = "已中斷:子行程樹已收"
                        break
                    if time.time() - t0 > 600:
                        PRIOR._kill_tree(p)
                        note = "逾時 600s(子行程樹已收)"
                        break
        finally:
            with PRIOR._LOCK:
                PRIOR.RUNNING.pop(name, None)
    if not note and PRIOR.STOP.is_set() and p.returncode not in (0, None):
        note = "已中斷:子行程樹已收"
    secs = round(time.time() - t0, 1)
    keep, skip = [], []
    if not note:
        try:
            txt = log.read_text(encoding="utf-8", errors="replace")
            rows = json.JSONDecoder().raw_decode(txt[txt.find("{"):])[0].get("engines", [])
        except (ValueError, OSError):
            rows = []
            note = f"engine list 回 rc {p.returncode},讀不到 JSON"
        for r in rows:
            fam = r.get("family") or r.get("eid")
            if not fam:
                continue
            parts = set(Path(str(r.get("path", ""))).parts)
            (skip.append({"eid": r.get("eid"), "family": fam, "path": r.get("path")}) if parts & set(V0100.SUPERSEDED_DIRS)
             else keep.append(fam))
    keep = list(dict.fromkeys(keep))
    lamp = "INTERRUPTED" if note.startswith("已中斷") else ("GREEN" if keep else "RED")
    _ENGINE_LIST_CARD.clear()
    _ENGINE_LIST_CARD.update({"step": name, "lamp": lamp, "rc": p.returncode, "secs": secs, "n": len(keep),
                              "skipped": len(skip), "note": note})
    PRIOR._say(f"  [完成] {name} · {lamp} · rc {p.returncode} · {secs}s · "
               + (note or f"{len(keep)} 支要啟動 · {len(skip)} 支已被取代(不啟動)"))
    return keep, skip


_FLOW_ENGINES_V0100 = V0100.flow_engines


def flow_engines(opt, res, gate, log_dir, manager=None, py=None) -> dict:
    """同 v0100 引擎流程;拿名單時被 Ctrl+C 打斷記 INTERRUPTED(不是紅);總覽多記 engine_list 那一步。"""
    out = _FLOW_ENGINES_V0100(opt, res, gate, log_dir, manager, py)
    if PRIOR.STOP.is_set() and out.get("lamp") == "RED" and not out.get("steps"):
        out = dict(out, lamp="INTERRUPTED", note="拿引擎名單時被中斷")
    if _ENGINE_LIST_CARD:
        out["engine_list"] = dict(_ENGINE_LIST_CARD)
    return out


# ---------------------------------------------------------------- 換上本版(前版鏈讀模組全域)
_ACTIVATE_V0101 = PRIOR.activate
_WRITE_REPORT_V0100 = V0100.write_report
_IN_RUN = threading.Event()


def write_report(card: dict, ui_dir: Path | None = None) -> dict:
    if _IN_RUN.is_set():
        card["schema"], card["tag"] = "VDF_ActivateVDF_v0102", TAG
    return _WRITE_REPORT_V0100(card, ui_dir) if ui_dir is not None else _WRITE_REPORT_V0100(card)


def activate(opt, manager: Path | None = None, py: str | None = None, temp: Path | None = None) -> dict:
    """同 v0101 activate(標頭與總覽標本版)。"""
    keep_tag = PRIOR.TAG
    PRIOR.TAG = TAG
    _IN_RUN.set()
    _ENGINE_LIST_CARD.clear()
    try:
        return _ACTIVATE_V0101(opt, manager, py, temp)
    finally:
        _IN_RUN.clear()
        PRIOR.TAG = keep_tag


for _m in (V0100, PRIOR):
    _m.flow_env, _m.engine_ids, _m.flow_engines = flow_env, engine_ids, flow_engines
V0100.write_report = write_report
PRIOR._last_line = _last_line
for _n in dir(PRIOR):
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = getattr(PRIOR, _n)


# ---------------------------------------------------------------- 自測
_SITE_SLOW = "import os, time\ntime.sleep(float(os.environ.get('ACT_SLOW_START') or 0))\n"   # 模擬 Windows 起一支 Python 的慢
_SLOW_LIST_MANAGER = r"""
import os, sys, time
args = sys.argv[1:]
if args[:2] == ["engine", "list"]:
    time.sleep(float(os.environ.get("ACT_LIST_SLEEP", "30")))
    print('{"engines": [{"eid": "ENG001", "family": "VDF_ENG001_X", "path": "functional modules/VDF/engine/VDF_ENG001_X_v0100.py"}]}')
    sys.exit(0)
print("[計] ok")
sys.exit(0)
"""


def selftest() -> int:
    import ast
    import io
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {TAG} · 薄尾自測(並行判法不靠起行程快 · engine list 登記 · 編譯警告 · numexpr 上限;沙盒 · 假管理員 · 零網路)===")
    with tempfile.TemporaryDirectory(prefix="activatevdf102_pyc_") as td:
        probe = ("import importlib.util,sys\n"
                 "sp=importlib.util.spec_from_file_location('a102',sys.argv[1]);m=importlib.util.module_from_spec(sp);"
                 "sys.modules['a102']=m;sp.loader.exec_module(m);print('LOADED',m.TAG)\n")
        r = subprocess.run([sys.executable, "-X", f"pycache_prefix={td}", "-W", "always", "-c", probe, str(Path(__file__).resolve())],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    src = Path(__file__).read_text(encoding="utf-8")
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        ast.parse(src)
    own = [str(x.message) for x in w if "escape" in str(x.message)]
    chk("⑪ 載入本版(連帶前版鏈,重新編譯、警告全開)不印 invalid escape;本版原始碼自己沒有無效跳脫",
        r.returncode == 0 and "LOADED" in r.stdout and "invalid escape" not in r.stderr and not own,
        (r.returncode, [ln for ln in r.stderr.splitlines() if "escape" in ln][:2], own[:2]))

    with tempfile.TemporaryDirectory(prefix="activatevdf102_par_") as td:
        t = Path(td)
        mgr = t / "mgr" / "VDF_SystemManager_v9999.py"
        mgr.parent.mkdir()
        mgr.write_text(V0100._FAKE_MANAGER, encoding="utf-8")
        site = t / "site"
        site.mkdir()
        (site / "sitecustomize.py").write_text(_SITE_SLOW, encoding="utf-8")
        flog = t / "calls.jsonl"
        keys = ("ACT_FAKE_LOG", "ACT_FAKE_SLEEP", "ACT_SLOW_START", "PYTHONPATH")
        keep = {k: os.environ.get(k) for k in keys}
        sl = 3.0                                            # 每支假步驟跑 3 秒:並行與否看「起跑時對方還在跑」,不看起行程快不快
        os.environ.update(ACT_FAKE_LOG=str(flog), ACT_FAKE_SLEEP=str(sl), ACT_SLOW_START="0.8",
                          PYTHONPATH=os.pathsep.join([str(site)] + ([keep["PYTHONPATH"]] if keep["PYTHONPATH"] else [])))
        PRIOR._HB["out"] = io.StringIO()
        try:
            PRIOR.STOP.clear()
            res3 = V0100.optimize_resources(want=3, stamp="20261018_120000", root=t)
            res3 = dict(res3, plan=dict(res3["plan"], slots=3))
            logs = t / "logs"
            logs.mkdir()
            opt = V0100.parse(["run", "--no-open", "--no-ui"])
            g = V0100.MemGate(reader=lambda: {"avail_mb": 9000, "total_mb": 16000}, interval=0.05).start()
            lists = PRIOR.phase_lists(opt, res3, g, logs, mgr)
            t_lists = time.time()
            flows = PRIOR.run_flows(opt, res3, g, logs, lists, mgr)
            g.close()
            calls = [json.loads(x) for x in flog.read_text(encoding="utf-8").splitlines()]
            t009 = next(c["t0"] for c in calls if c["args"][:3] == ["fetch", "run", "009"])
            t010 = next(c["t0"] for c in calls if c["args"][:3] == ["fetch", "run", "010"])
            tl = [c["t0"] for c in calls if c["args"][:2] == ["engine", "list"]]
            tf = next(c["t0"] for c in calls if c["args"][:2] == ["fetch", "run"] and c["args"][2] not in ("009", "010"))
            te = next(c["t0"] for c in calls if c["args"][:2] == ["engine", "launch"])
            td_ = min(c["t0"] for c in calls if c["args"][:1] in (["db"], ["refill"]))
            eng = next(f for f in flows if f["flow"] == "engines")
            chk("⑫ 取代 v0101 ⑩(門檻 0.55 秒把 Linux 起行程快當前提,Windows 必 FAIL):子行程每支起慢 0.8 秒時 —— "
                "清單依序 · 清單跑完才起 engine list · engine launch 起跑時擷取還在跑(並行)· 資料庫等擷取跑完才起 · 三條 GREEN",
                t010 >= t009 + sl - 0.05 and len(tl) == 1 and tl[0] >= t_lists - 0.05 and te < tf + sl and td_ >= tf + sl - 0.05
                and all(f["lamp"] == "GREEN" for f in flows) and eng.get("engine_list", {}).get("lamp") == "GREEN",
                {"010-009": round(t010 - t009, 2), "engine-fetch": round(te - tf, 2), "db-fetch": round(td_ - tf, 2),
                 "flows": [f["lamp"] for f in flows]})
        finally:
            PRIOR._hb_stop()                     # 心跳執行緒收掉,前版自測(① 心跳 0.2 秒)才起得了新的
            PRIOR._HB["out"] = None
            for k, v in keep.items():
                (os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v))

    with tempfile.TemporaryDirectory(prefix="activatevdf102_stop_") as td:
        t = Path(td)
        mgr = t / "mgr" / "VDF_SystemManager_v9999.py"
        mgr.parent.mkdir()
        mgr.write_text(_SLOW_LIST_MANAGER, encoding="utf-8")
        logs = t / "logs"
        logs.mkdir()
        PRIOR._HB["out"] = io.StringIO()
        keep_ls = os.environ.get("ACT_LIST_SLEEP")
        os.environ["ACT_LIST_SLEEP"] = "30"
        try:
            PRIOR.STOP.clear()
            res1 = V0100.optimize_resources(want=1, stamp="20261018_120001", root=t)
            opt = V0100.parse(["run", "--no-open", "--no-ui", "--flows", "engines"])
            box: dict = {}
            th = threading.Thread(target=lambda: box.update(out=flow_engines(opt, res1, None, logs, mgr)), daemon=True)
            th.start()
            time.sleep(1.5)
            beat = PRIOR.heartbeat_once()
            t0 = time.time()
            n = PRIOR.interrupt()
            th.join(15)
            took = time.time() - t0
            out = box.get("out") or {}
            left = (subprocess.run(["pgrep", "-f", str(mgr)], capture_output=True, text=True).stdout.split()
                    if os.name != "nt" else [])
            chk("⑬ engine list 跑到一半按 Ctrl+C:心跳列得到 engine_list;子行程樹被收(不等滿 30 秒)· 引擎流程記 INTERRUPTED(不是紅)",
                "engine_list" in beat and n >= 1 and took < 10 and out.get("lamp") == "INTERRUPTED" and not left,
                (n, round(took, 1), out.get("lamp"), left))
        finally:
            PRIOR._hb_stop()
            PRIOR.STOP.clear()
            PRIOR._HB["out"] = None
            (os.environ.pop("ACT_LIST_SLEEP", None) if keep_ls is None else os.environ.__setitem__("ACT_LIST_SLEEP", keep_ls))

    with tempfile.TemporaryDirectory(prefix="activatevdf102_env_") as td:
        res = V0100.optimize_resources(want=3, stamp="20261018_120002", root=Path(td))
        th = res["plan"]["threads_per_flow"]
        env = V0100.flow_env(res, "fetch", base_env={})
        cel = 2 * (os.cpu_count() or 1)          # 加速器最多把 numexpr 用量拉到 ≈ 1.6 × 實體核
        ne_ok = True
        try:
            import numexpr  # noqa: F401  — 有裝才真測;沒裝只驗數字
            rr = subprocess.run([sys.executable, "-c", "import numexpr"], env=dict(os.environ, **{k: env[k] for k in env if k.startswith(
                ("NUMEXPR", "OMP"))}, NUMEXPR_NUM_THREADS=str(os.cpu_count() or 1)), capture_output=True, text=True, timeout=60)
            ne_ok = "nthreads cannot be larger" not in (rr.stdout + rr.stderr)
        except ImportError:
            pass
        chk("⑭ numexpr:用量 = 每條執行緒數;上限天花板 ≥ 加速器可能設的用量(不再印 nthreads cannot be larger);其餘上限不動",
            env["NUMEXPR_NUM_THREADS"] == str(th) and int(env["NUMEXPR_MAX_THREADS"]) >= max(th, cel - 1)
            and env["OMP_NUM_THREADS"] == str(th) and env["POLARS_MAX_THREADS"] == str(th) and ne_ok,
            (env["NUMEXPR_NUM_THREADS"], env["NUMEXPR_MAX_THREADS"], env["OMP_NUM_THREADS"]))
    with tempfile.TemporaryDirectory(prefix="activatevdf102_hb_") as td:
        lg = Path(td) / "x.log"
        lg.write_text("[步] 第 3 段 抓 0050\n<unknown>:3: SyntaxWarning: invalid escape sequence '\\*'\n"
                      "C:\\a\\b.py:635: SyntaxWarning: invalid escape sequence '\\]'\n", encoding="utf-8")
        chk("⑮ 心跳的「日誌最後一行」略過編譯警告雜訊,顯示真正的進度行", _last_line(lg) == "[步] 第 3 段 抓 0050", _last_line(lg))
    imports = re.findall(r"^\s*(?:import|from)\s+([A-Za-z_][\w.]*)", src, re.M)
    chk("⑯ 加速器橋 · 網路橋在;不匯入他系統程式;不碰 TA-Lib;同意閘不寫",
        "VIA:ACCEL-BRIDGE" in src and "def _via_net" in src
        and not [x for x in imports if x.startswith(("CGC_", "VRN_", "VCGC"))]
        and not re.search(r"^\s*(import|from)\s+" + "talib", src, re.M)
        and not re.search(r"\[[\"']VIA_(NET|SCRAPE)_" + r"CONSENT[\"']\]\s*=(?!=)", src))
    n = sum(ok)
    print(f"  [計] {TAG} 本版 {n}/{len(ok)} · {'PASS' if n == len(ok) else 'FAIL'}")
    if n != len(ok):
        return 1
    buf, keep_out = io.StringIO(), sys.stdout
    sys.stdout = _Tee(keep_out, buf)
    try:
        rc1 = PRIOR.selftest()
    finally:
        sys.stdout = keep_out
    failed = re.findall(r"^\s*\[FAIL\] (\S+)", buf.getvalue(), re.M)
    superseded = rc1 == 1 and failed == ["⑩"]          # 只容 v0101 ⑩ 這一條(本版 ⑫ 已用不靠起行程快的判法過了)
    if superseded:
        print("  [取代] v0101 ⑩(0.55 秒門檻,起行程慢的機器必 FAIL)由本版 ⑫ 取代;v0101 其餘 10 條照過。"
              "v0101 在 ⑩ 失敗時不往下委派 → 本版補跑 v0100 自測")
        rc1 = PRIOR.PRIOR.selftest()
    return 0 if rc1 == 0 else (rc1 if rc1 in (2, 3) else 2)


class _Tee:
    """同時寫到畫面與緩衝(委派前版自測時照常印出,同時收下來判哪幾條失敗)。"""

    def __init__(self, *outs):
        self.outs = outs

    def write(self, s):
        for o in self.outs:
            o.write(s)
        return len(s)

    def flush(self):
        for o in self.outs:
            o.flush()


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--selftest"]:
        return selftest()
    opt = V0100.parse(argv)
    if opt.verb != "run":
        return V0100.main(argv)
    card = activate(opt)
    return {"GREEN": 0, "YELLOW": 2, "INTERRUPTED": 130}.get(card["lamp"], 1)


if __name__ == "__main__":
    raise SystemExit(main())
