#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL134_ParallelLanes v0103 — 薄尾:引擎子行程跟編排同生共死(Windows Job Object)· 子行程 PID 記帳 · 前一趟孤兒偵測 · DuckDB 鎖持有者印在道上

R78 工作站實錄(RUN_20261013_235304):revenue_backfill(ENG075)與 consensus 都在 duckdb.connect(vdf_tw_market.duckdb) 倒下 ——
「程序無法存取檔案,因為檔案正由另一個程序使用 · File is already open in …python.exe (PID 372)」。同鏈序跑律沒破(tw 鏈 hist_2023 → … → consensus 本來就序跑);
持鎖的是**前一趟**(20:32 那趟被 Invoke-VIAPython 1800 秒天花板殺掉)留下的引擎子行程:外層只殺到 MDL134 本體,_exec 的 p.kill() 來不及跑,
引擎孤兒繼續抓著 DuckDB。Hydra 律 H3 只看 FixAll 心跳與步鎖(鎖記的是本體 PID,本體死了鎖就被回收),看不到孤兒。
v0103(本體 v0101 / 薄尾 v0102 不動;只換 _exec · preflight · make_runner 三個名字,沿前版鏈找本體換):
  ① _exec:Windows 子行程起在 Job Object(KILL_ON_JOB_CLOSE;編排被殺 → 子樹一起死;逾時改殺整個 job);配不上(巢狀不准)照舊跑、note 記黃。
     Linux 照舊(preexec 在多執行緒不安全,不加)。
  ② 子行程 PID 記進該趟 CHILDREN.json(step · pid · started · ended);preflight 加 H3b:前幾趟還沒 ended 且 PID 仍活 = 孤兒,列 pid 與步名(WARN,不代殺:零 force)。
  ③ 步 log 尾端出現 DuckDB 鎖訊息 → 道上那列 note 前綴 DB_BUSY pid N 持 <庫名>(狀態仍 FAIL,誠實),操作員不用翻 log。
其餘(清單先行 · 鏈冊 · 排程 · 離線 SKIP · 鑰缺 SKIP)全沿用 v0102。不碰 TA-Lib;本檔零網路;同意閘只傳不設。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 全導入令;graceful 零行為變更) =====
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
    """統包唯一網路工具惰性載入;本檔零網路,橋只為全樹一致。"""
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
import subprocess
import sys
import threading
import time
import types
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL134_ParallelLanes"
TAG = "v" + Path(__file__).stem.rsplit("_v", 1)[-1]


def _vnum_v0103(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0103(p) < _vnum_v0103(__file__)), key=_vnum_v0103)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


def _chain_v0103() -> list:
    out, m = [], PRIOR
    while isinstance(m, types.ModuleType) and m not in out:
        out.append(m)
        m = getattr(m, "PRIOR", None)
    return out


def _owner_v0103(name: str):
    for m in _chain_v0103():
        if name in vars(m):
            return m
    return None


OWNER_RUN = _owner_v0103("run")                          # v0101:run 讀它自己的 preflight / make_runner
_PREV_PREFLIGHT = OWNER_RUN.preflight
_PREV_MAKE_RUNNER = OWNER_RUN.make_runner                # 目前是 v0102 的(清單步帶入口標記)
_CHILD_LOCK = threading.Lock()
CHILDREN_V0103 = "CHILDREN.json"
_DB_BUSY_RX = re.compile(r'Cannot open file "([^"]+)"[\s\S]{0,400}?File is already open in\s*([^\n]*?)\s*\(PID (\d+)\)', re.I)
_DB_BUSY_RX2 = re.compile(r"(?:正由另一個程序使用|being used by another process)[\s\S]{0,400}?\(PID (\d+)\)", re.I)


# ---------------------------------------------------------------- ① Job Object(Windows)
def _job_v0103():
    """Windows:建 Job Object 並設 KILL_ON_JOB_CLOSE;其他 OS / 失敗回 None(照舊跑)。"""
    if os.name != "nt":
        return None
    try:
        import ctypes
        from ctypes import wintypes as w
        k = ctypes.windll.kernel32

        class _BASIC(ctypes.Structure):
            _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64), ("LimitFlags", w.DWORD),
                        ("MinimumWorkingSetSize", ctypes.c_size_t), ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", w.DWORD),
                        ("Affinity", ctypes.c_size_t), ("PriorityClass", w.DWORD), ("SchedulingClass", w.DWORD)]

        class _IO(ctypes.Structure):
            _fields_ = [(n, ctypes.c_uint64) for n in ("ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                                                       "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]

        class _EXT(ctypes.Structure):
            _fields_ = [("BasicLimitInformation", _BASIC), ("IoInfo", _IO), ("ProcessMemoryLimit", ctypes.c_size_t),
                        ("JobMemoryLimit", ctypes.c_size_t), ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]
        job = k.CreateJobObjectW(None, None)
        if not job:
            return None
        info = _EXT()
        info.BasicLimitInformation.LimitFlags = 0x2000          # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not k.SetInformationJobObject(job, 9, ctypes.byref(info), ctypes.sizeof(info)):   # 9 = JobObjectExtendedLimitInformation
            k.CloseHandle(job)
            return None
        return job
    except Exception:
        return None


def _job_assign_v0103(job, p) -> bool:
    try:
        import ctypes
        return bool(ctypes.windll.kernel32.AssignProcessToJobObject(job, int(p._handle)))
    except Exception:
        return False


def _job_kill_v0103(job, p) -> None:
    """逾時:有 job 殺整個 job(子樹);沒有就照舊 p.kill()。"""
    try:
        if job is not None:
            import ctypes
            ctypes.windll.kernel32.TerminateJobObject(job, 1)
    except Exception:
        pass
    try:
        p.kill()
    except Exception:
        pass


def _job_close_v0103(job) -> None:
    try:
        if job is not None:
            import ctypes
            ctypes.windll.kernel32.CloseHandle(job)
    except Exception:
        pass


# ---------------------------------------------------------------- ② 子行程 PID 記帳 · 孤兒偵測
def record_child_v0103(logdir: Path, step_id: str, pid: int, ended: bool = False) -> None:
    """該趟 CHILDREN.json:step → {pid, started, ended};多道同跑,鎖住讀改寫。"""
    fp = Path(logdir) / CHILDREN_V0103
    with _CHILD_LOCK:
        try:
            d = json.loads(fp.read_text(encoding="utf-8")) if fp.exists() else {}
        except Exception:
            d = {}
        e = d.get(step_id) or {}
        e["pid"] = int(pid)
        e.setdefault("started", datetime.now().isoformat(timespec="seconds"))
        if ended:
            e["ended"] = datetime.now().isoformat(timespec="seconds")
        d[step_id] = e
        try:
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        except Exception:
            pass


def orphans_v0103(rep: Path | None = None, current: Path | None = None) -> list:
    """前幾趟 RUN_*/CHILDREN.json 裡沒 ended 且 PID 仍活的子行程(孤兒,多半抓著 DuckDB)。"""
    rep = Path(rep or OWNER_RUN.REP)
    out = []
    if not rep.is_dir():
        return out
    for fp in sorted(rep.glob("RUN_*/" + CHILDREN_V0103)):
        if current is not None and fp.parent.resolve() == Path(current).resolve():
            continue
        try:
            d = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            continue
        for sid, e in d.items():
            pid = int(e.get("pid") or 0)
            if pid and not e.get("ended") and pid != os.getpid() and OWNER_RUN.pid_alive(pid):
                out.append({"run": fp.parent.name, "step": sid, "pid": pid, "started": e.get("started", "")})
    return out


def preflight_v0103(steps: list) -> dict:
    """前版 preflight(H1–H5)+ H3b 孤兒:只列不殺(零 force);run 不因 H3b 阻擋,道上結果會印 DB_BUSY。"""
    pf = _PREV_PREFLIGHT(steps)
    orph = orphans_v0103()
    pf["H3b"] = {"state": "WARN" if orph else "OK",
                 "items": [o["run"] + " " + o["step"] + " pid " + str(o["pid"]) + "(可能抓著 DuckDB;Stop-Process -Id " + str(o["pid"]) + " 或等它跑完)" for o in orph]}
    if orph:
        print("[道] H3b 前一趟引擎子行程仍活(孤兒):" + "; ".join(pf["H3b"]["items"]), flush=True)
    return pf


# ---------------------------------------------------------------- ① _exec(Job + 記帳)
def _exec_v0103(step: dict, env: dict, logpath: Path) -> tuple:
    """同 v0101 _exec(單步子進程 · 逾時 kill · 特殊步委派 MDL125),加 Job Object 與 PID 記帳。"""
    m = OWNER_RUN.m125()
    t0 = time.time()
    logpath = Path(logpath)
    with open(logpath, "w", encoding="utf-8", errors="ignore") as lf:
        if str(step["argv"][0]).startswith("__"):
            return (m._run_special(step, lf, env) if m else -2), "special"
        job = _job_v0103()
        p = subprocess.Popen(list(step["argv"]), stdout=lf, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, env=env, cwd=str(OWNER_RUN.VIA))
        jnote = ""
        if job is not None and not _job_assign_v0103(job, p):
            jnote = " · job 配不上(巢狀不准;照舊跑)"
        record_child_v0103(logpath.parent, str(step.get("id", "?")), p.pid)
        try:
            p.wait(timeout=step["to"])
        except subprocess.TimeoutExpired:
            _job_kill_v0103(job, p)
            try:
                p.wait(timeout=10)
            except Exception:
                pass
            record_child_v0103(logpath.parent, str(step.get("id", "?")), p.pid, ended=True)
            _job_close_v0103(job)
            return -1, "逾時 " + str(step["to"]) + "s 終止(連子樹)" + jnote
        _job_close_v0103(job)
    record_child_v0103(logpath.parent, str(step.get("id", "?")), p.pid, ended=True)
    return p.returncode, str(round(time.time() - t0, 1)) + "s" + jnote


# ---------------------------------------------------------------- ③ DuckDB 鎖持有者
def db_busy_v0103(text: str):
    """log 尾端的 DuckDB 鎖訊息 → (庫名, 持有者 exe, pid);沒有回 None。"""
    m = _DB_BUSY_RX.search(text or "")
    if m:
        return Path(m.group(1).replace("\\", "/")).name, Path(m.group(2).strip().replace("\\", "/")).name, int(m.group(3))
    m2 = _DB_BUSY_RX2.search(text or "")
    if m2:
        return "?", "?", int(m2.group(1))
    return None


def annotate_v0103(ent: dict, logpath: Path) -> dict:
    try:
        tail = Path(logpath).read_text(encoding="utf-8", errors="ignore")[-6000:]
    except Exception:
        return ent
    hit = db_busy_v0103(tail)
    if hit:
        db, exe, pid = hit
        ent["db_busy"] = {"db": db, "holder": exe, "pid": pid}
        ent["note"] = "DB_BUSY pid " + str(pid) + " 持 " + db + "(" + exe + ";前一趟孤兒?見 H3b)· " + str(ent.get("note") or "")
    return ent


def make_runner_v0103(logdir: Path, dry: bool, net_ok: bool, exec_fn=None):
    inner = _PREV_MAKE_RUNNER(logdir, dry, net_ok, exec_fn or _exec_v0103)

    def runner(s: dict) -> dict:
        ent = inner(s)
        if ent.get("state") == "FAIL":
            annotate_v0103(ent, Path(logdir) / (str(s.get("id", "?")) + ".log"))
        return ent
    return runner


def _install_v0103() -> None:
    OWNER_RUN.preflight = preflight_v0103
    OWNER_RUN.make_runner = make_runner_v0103


def _restore_v0102() -> None:
    OWNER_RUN.preflight = _PREV_PREFLIGHT
    OWNER_RUN.make_runner = _PREV_MAKE_RUNNER


_install_v0103()


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        print("=== 十道並行安全編排(" + _STEM + " " + TAG + ")· 薄尾自測(子行程同生共死 · 孤兒偵測 · DB_BUSY)===")
        return selftest()
    return PRIOR.main()


def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print("  [" + ("OK" if cond else "FAIL") + "] " + name + " " + str(note))
        if not cond:
            fails.append(name)
    chk("① 本體找得到(run 的主人 " + Path(OWNER_RUN.__file__).stem[-5:] + ")· preflight / make_runner 已換成本版 · 前版 make_runner 保留在鏈上",
        OWNER_RUN is not None and Path(OWNER_RUN.__file__).stem.endswith("_v0101") and OWNER_RUN.preflight is preflight_v0103
        and OWNER_RUN.make_runner is make_runner_v0103 and callable(_PREV_MAKE_RUNNER))
    with tempfile.TemporaryDirectory() as td:
        logdir = Path(td) / "RUN_test"
        logdir.mkdir()
        rc, note = _exec_v0103({"id": "s_ok", "argv": [sys.executable, "-c", "print('hi')"], "to": 30}, dict(os.environ), logdir / "s_ok.log")
        ch = json.loads((logdir / CHILDREN_V0103).read_text(encoding="utf-8"))
        chk("② _exec:子行程 rc 0 · PID 記進 CHILDREN.json(started · ended)· log 有輸出",
            rc == 0 and ch.get("s_ok", {}).get("pid") and ch["s_ok"].get("ended") and "hi" in (logdir / "s_ok.log").read_text(encoding="utf-8"), note)
        t0 = time.time()
        rc2, note2 = _exec_v0103({"id": "s_slow", "argv": [sys.executable, "-c", "import time; time.sleep(60)"], "to": 1}, dict(os.environ), logdir / "s_slow.log")
        ch2 = json.loads((logdir / CHILDREN_V0103).read_text(encoding="utf-8"))
        pid2 = int(ch2.get("s_slow", {}).get("pid") or 0)
        time.sleep(0.3)
        chk("③ 逾時:rc -1 · note 逾時(連子樹)· 子行程已死 · ended 已記 · 不卡(< 20s)",
            rc2 == -1 and "逾時" in note2 and pid2 and not OWNER_RUN.pid_alive(pid2) and ch2["s_slow"].get("ended") and time.time() - t0 < 20, note2)
        txt = ('Traceback (most recent call last):\n  File "x.py", line 292, in rebuild_view\n    con = duckdb.connect(str(DB_TW))\n'
               '_duckdb.IOException: IO Error: Cannot open file "C:\\Users\\t\\via_database\\output_hub\\mega\\vdf_tw_market.duckdb": 程序無法存取檔案,因為檔案正由另一個程序使用。\n\n\n'
               'File is already open in\nC:\\Users\\t\\AppData\\Roaming\\uv\\python\\cpython-3.12.12-windows-x86_64-none\\python.exe (PID 372)\n')
        (logdir / "revenue_backfill.log").write_text(txt, encoding="utf-8")
        ent = annotate_v0103({"id": "revenue_backfill", "state": "FAIL", "note": "3.2s"}, logdir / "revenue_backfill.log")
        chk("④ DB_BUSY:工作站那段 DuckDB 鎖訊息 → 庫名 vdf_tw_market.duckdb · 持有者 python.exe · pid 372 進 note 與 db_busy",
            ent.get("db_busy") == {"db": "vdf_tw_market.duckdb", "holder": "python.exe", "pid": 372} and ent["note"].startswith("DB_BUSY pid 372 持 vdf_tw_market.duckdb")
            and db_busy_v0103("all good") is None, ent.get("note", "")[:60])
        rep = Path(td) / "lanes"
        (rep / "RUN_old").mkdir(parents=True)
        ghost = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            (rep / "RUN_old" / CHILDREN_V0103).write_text(json.dumps({"consensus": {"pid": ghost.pid, "started": "x"}, "dead": {"pid": 999999, "started": "y"},
                                                                      "done": {"pid": ghost.pid, "started": "z", "ended": "z"}}), encoding="utf-8")
            orph = orphans_v0103(rep)
            chk("⑤ 孤兒偵測:沒 ended 且 PID 活(用替身子行程)→ 列;死 PID 回收不列;已 ended 不列;本趟不列",
                len(orph) == 1 and orph[0]["step"] == "consensus" and orph[0]["pid"] == ghost.pid
                and orphans_v0103(rep, current=rep / "RUN_old") == [], orph)
            keep_rep = OWNER_RUN.REP
            OWNER_RUN.REP = rep
            try:
                pf = preflight_v0103([{"id": "datahome", "chain": "fs", "argv": ["__fs__"], "after": []}])
            finally:
                OWNER_RUN.REP = keep_rep
            chk("⑥ preflight:前版 H1–H5 照回 + H3b WARN 列孤兒 pid(不阻擋:H3 / H5 仍由前版判)",
                all(k in pf for k in ("H1", "H2", "H3", "H4", "H5", "H3b")) and pf["H3b"]["state"] == "WARN" and "consensus pid " + str(ghost.pid) in pf["H3b"]["items"][0], pf["H3b"]["items"][:1])
        finally:
            ghost.kill()
            ghost.wait(timeout=10)
        seen = {}

        def fake_exec(s, env, lp):
            seen[s["id"]] = env.get("VIA_FROM_VCGC")
            Path(lp).write_text("ok", encoding="utf-8")
            return 0, "ok"
        r = make_runner_v0103(logdir, False, True, fake_exec)
        e1 = r({"id": "tw_list", "zh": "tw_list", "chain": "lists", "engine_ok": True, "net": False, "to": 5, "argv": ["x", "y"], "after": []})
        chk("⑦ make_runner:包著前版(v0102 清單步仍帶 VIA_FROM_VCGC=YES)· 傳入的 exec_fn 照用 · OK 列不加註",
            seen.get("tw_list") == "YES" and e1.get("state") == "OK" and "db_busy" not in e1, (e1.get("state"), e1.get("note")))
    body = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 檔頭:加速器橋 · 網路橋在(__future__ 之後)· 不碰 TA-Lib · 不代設同意閘 · 零網路",
        "[VIA:ACCEL-BRIDGE:" in body and "[VIA:NET-BRIDGE:" in body and body.index("from __future__") < body.index("[VIA:ACCEL-BRIDGE:")
        and "import " + "talib" not in body and 'env["VIA_NET_' + 'CONSENT"]' not in body and "url" + "open" not in body)
    print("  ── 前版自測(本版先還原前版綁定,跑完再裝回)──")
    _restore_v0102()
    try:
        prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    finally:
        _install_v0103()
    chk("⑨ 前版 " + PRIOR_PATH.stem + " 自測 rc 0;跑完本版綁定裝回", prc == 0 and OWNER_RUN.make_runner is make_runner_v0103 and OWNER_RUN.preflight is preflight_v0103)
    print("  [計] " + _STEM + " " + TAG + " 薄尾 " + str(9 - len(fails)) + "/9 · " + ("PASS" if not fails else "FAIL"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
