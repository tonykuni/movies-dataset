#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VCGC_StartupEngine v0200 — 薄尾(v0100 / v0101 一字不動):boot · audit · backup · remote · scan · lanes(啟動器缺口表第 2 批)

操作員 2026-11-28 裁定 14「照附件、保守版」+ 裁定 11(OmniRoute 只探測)+ 裁定 13(環境只稽核、AI 出計畫)。新增動詞(其餘照 v0101 → v0100):
  boot     先降壓(執行緒上限 · 本行程降優先權 · Windows 防休眠且結束還原 · 只清本引擎自己記過 PID 的過期子行程)
           → 三道獨立子行程(各自 PID · 日誌 · 健康收據)→ 一行就緒摘要 + boot_status.json
             第 1 道:Hub `via-health`(環境,零安裝)+ `via-bak`(備份)+ 環境指紋快讀(沒變 → 304)
             第 2 道:Graphify 圖新舊 · MCP 伺服器尾版可編譯 · VDF 管理器尾版可編譯 · OmniRoute 探測(只記 ONLINE / OFFLINE,不分流)
             第 3 道:遠端控制只檢查並記錄狀態(VCGC_REMOTE_STATUS_CMD 給的檢查指令),不代按同意、不自己拉起
           總燈:三道都 PASS / ONLINE 才 ONLINE(rc 0);有一道沒達標 = DEGRADED(rc 2);沒交收據 / 逾時 = RED(rc 1)
  audit    只跑第 1 道的環境部分;補裝計畫一行交操作員(via-health → via-install --plan-check → --from-plan --yes)
  backup   Hub `via-bak`        remote  只跑第 3 道        scan  Hub `via-pano`        lanes  印最近一次 boot 收據
每個動詞第一步 accel_env():加速器橋真的載到(VIA_ACCEL is not None)才算,不然照實回報。
收據放 VIA_Reports/vcgc/startup_v0200/(可用 VCGC_STARTUP_WORK 改);容器跑的一律標「容器」。不碰 TA-Lib · 不設同意閘 · 不 import 他系統。
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

import ast
import atexit
import importlib.util
import json
import os
import platform
import re
import shlex
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

VERSION = "v0200"
FAMILY = "VCGC_StartupEngine"
TAG = f"{FAMILY} {VERSION}"
HERE = Path(__file__).resolve()
VIA = HERE.parents[2]
THREAD_VARS = ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS", "POLARS_MAX_THREADS")
NEW_VERBS = ("boot", "audit", "backup", "remote", "scan", "lanes")
OMNI_URL = os.environ.get("VCGC_OMNIROUTE_URL", "http://localhost:20128/v1")


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.parent.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(HERE)), key=_vnum)
if PRIOR_PATH.stem in sys.modules:
    PRIOR = sys.modules[PRIOR_PATH.stem]
else:
    _spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem, PRIOR_PATH)
    PRIOR = importlib.util.module_from_spec(_spec)
    sys.modules[PRIOR_PATH.stem] = PRIOR
    _spec.loader.exec_module(PRIOR)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def work_dir() -> Path:
    w = Path(os.environ.get("VCGC_STARTUP_WORK") or VIA / "VIA_Reports" / "vcgc" / "startup_v0200")
    w.mkdir(parents=True, exist_ok=True)
    return w


def where() -> str:
    return "主機" if os.name == "nt" else "容器"


def save(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex[:8]}.sdd_tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, path)


def tail(folder: Path, family: str) -> Path | None:
    hits = [p for p in folder.glob(family + "_v*.py") if _vnum(p) >= 0]
    return max(hits, key=_vnum) if hits else None


# ---------------------------------------------------------------- 加速器 · 降壓
_AWAKE = {"set": False}


def accel_env() -> dict:
    cap = int(os.environ.get("VCGC_THREAD_CAP") or max(1, min(4, (os.cpu_count() or 2) // 2)))
    for k in THREAD_VARS:
        os.environ[k] = str(cap)
    awake = "N/A(非 Windows)"
    if os.name == "nt" and not _AWAKE["set"]:
        try:
            import ctypes
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)   # ES_CONTINUOUS | ES_SYSTEM_REQUIRED
            atexit.register(lambda: ctypes.windll.kernel32.SetThreadExecutionState(0x80000000))
            _AWAKE["set"], awake = True, "SET(結束時還原)"
        except (OSError, AttributeError) as exc:
            awake = f"FAILED:{type(exc).__name__}"
    elif _AWAKE["set"]:
        awake = "SET(結束時還原)"
    return {"accel_loaded": VIA_ACCEL is not None, "thread_cap": cap, "keep_awake": awake}


def lower_priority() -> dict:
    if os.name == "nt":
        try:
            import ctypes
            k = ctypes.windll.kernel32
            ok = bool(k.SetPriorityClass(k.GetCurrentProcess(), 0x00004000))          # BELOW_NORMAL_PRIORITY_CLASS
            return {"priority_lowered": ok, "how": "BELOW_NORMAL_PRIORITY_CLASS"}
        except (OSError, AttributeError) as exc:
            return {"priority_lowered": False, "how": f"FAILED:{type(exc).__name__}"}
    try:
        before = os.nice(0)
        after = os.nice(5) if before < 5 else before
        return {"priority_lowered": after >= 5, "how": f"nice {before} → {after}"}
    except OSError as exc:
        return {"priority_lowered": False, "how": f"FAILED:{type(exc).__name__}"}


def pressure() -> dict:
    cpus = os.cpu_count() or 1
    try:
        import psutil  # noqa: PLC0415 — 有就用,沒有照實寫 UNKNOWN
        cpu = psutil.cpu_percent(interval=0.5) / 100.0
        mem = psutil.virtual_memory().percent / 100.0
        return {"cpu": round(cpu, 3), "mem": round(mem, 3), "source": "psutil"}
    except ImportError:
        pass
    if hasattr(os, "getloadavg"):
        return {"cpu": round(os.getloadavg()[0] / cpus, 3), "mem": None, "source": "loadavg"}
    return {"cpu": None, "mem": None, "source": "UNKNOWN"}


def calm(max_cpu: float, wait: float) -> dict:
    t0, p = time.time(), pressure()
    while p["cpu"] is not None and p["cpu"] > max_cpu and time.time() - t0 < wait:
        time.sleep(2)
        p = pressure()
    known = p["cpu"] is not None
    return {**p, "within_threshold": (p["cpu"] <= max_cpu) if known else None, "limit": max_cpu, "waited_s": round(time.time() - t0, 1)}


def _cmdline(pid: int) -> str:
    try:
        import psutil  # noqa: PLC0415
        return " ".join(psutil.Process(pid).cmdline())
    except ImportError:
        pass
    except Exception:  # noqa: BLE001 — 行程不在 / 沒權限 = 不認得,不砍
        return ""
    f = Path(f"/proc/{pid}/cmdline")
    try:
        return f.read_bytes().replace(b"\0", b" ").decode("utf-8", "replace") if f.exists() else ""
    except OSError:
        return ""


def _kill(pid: int) -> bool:
    try:
        if os.name == "nt":
            return subprocess.run(["taskkill", "/T", "/F", "/PID", str(pid)], capture_output=True, timeout=30).returncode == 0
        os.kill(pid, 9)
        return True
    except (OSError, subprocess.SubprocessError):
        return False


def de_pressure(work: Path) -> dict:
    """只清本引擎記過、已過期、而且命令列仍是本引擎三道的子行程;別的行程一律不碰。"""
    killed, kept = [], []
    for sj in sorted((work / "sessions").glob("*/session.json")):
        try:
            s = json.loads(sj.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if s.get("expires", 0) > time.time():
            continue
        for rec in s.get("processes", []):
            pid = int(rec.get("pid", 0) or 0)
            cl = _cmdline(pid) if pid else ""
            if pid and HERE.name in cl and "_lane" in cl:
                (killed if _kill(pid) else kept).append(pid)
    return {"stale_killed": killed, "stale_kept": kept}


# ---------------------------------------------------------------- 第 1 道:環境 · 備份
def hub() -> Path | None:
    return tail(VIA, "VCGC_CommandHub")


def run_hub(short: str, *args: str, timeout: float = 900) -> dict:
    h = hub()
    if h is None:
        return {"short": short, "rc": None, "status": "ABSENT", "tail": "找不到 VCGC_CommandHub 尾版"}
    env = dict(os.environ, VIA_FROM_VCGC="YES", PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    for k in ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT"):
        env.pop(k, None)
    try:
        cp = subprocess.run([sys.executable, str(h), "x", short, *args], cwd=str(VIA), capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=timeout, env=env, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return {"short": short, "rc": 124, "status": "RED", "tail": f"逾時 {timeout}s"}
    lamp = {0: "PASS", 2: "DEGRADED"}.get(cp.returncode, "RED")
    out = [ln for ln in (cp.stdout + cp.stderr).splitlines() if ln.strip()][-6:]
    return {"short": short, "rc": cp.returncode, "status": lamp, "tail": " | ".join(out)[-600:]}


def site_dirs() -> list:
    import site  # noqa: PLC0415
    dirs = set(site.getsitepackages() if hasattr(site, "getsitepackages") else [])
    us = site.getusersitepackages() if hasattr(site, "getusersitepackages") else None
    if us:
        dirs.add(us)
    return sorted(d for d in dirs if Path(d).is_dir())


def env_fingerprint(work: Path, dirs: list | None = None) -> dict:
    """各 site 夾 .dist-info / .egg-info 名單的 SHA-256;跟上一輪一樣 → 304_NOT_MODIFIED(不重掃)。"""
    import hashlib  # noqa: PLC0415
    dirs = site_dirs() if dirs is None else dirs
    names = sorted(f"{d}::{p.name}" for d in dirs for p in Path(d).iterdir() if p.name.endswith((".dist-info", ".egg-info")))
    fp = hashlib.sha256("\n".join(names).encode("utf-8")).hexdigest()
    cache = work / "env_fingerprint.json"
    try:
        old = json.loads(cache.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        old = {}
    status = "304_NOT_MODIFIED" if old.get("sha256") == fp else "CHANGED" if old else "FIRST"
    save(cache, {"sha256": fp, "packages": len(names), "dirs": dirs, "python": sys.version.split()[0], "at": time.strftime("%Y-%m-%dT%H:%M:%S")})
    return {"status": status, "sha256": fp, "packages": len(names)}


INSTALL_PLAN = "via-health  →  via-install --plan-check  →  via-install --from-plan --yes(操作員在主機下;重建環境仍是 via-envgov apply --approve)"


def lane1(fake: bool) -> dict:
    work = work_dir()
    fp = env_fingerprint(work)
    if fake:
        return {"status": "PASS", "env": {"status": "PASS", "fake": True}, "backup": {"status": "PASS", "fake": True}, "fingerprint": fp}
    env = run_hub("via-health")
    bak = run_hub("via-bak")
    ok = env["status"] == "PASS" and bak["status"] == "PASS"
    return {"status": "PASS" if ok else "DEGRADED", "env": env, "backup": bak, "fingerprint": fp,
            "install_plan": None if env["status"] == "PASS" else INSTALL_PLAN}


# ---------------------------------------------------------------- 第 2 道:Graphify · MCP · VDF · OmniRoute(只探測)
def compiles(p: Path | None) -> str:
    if p is None:
        return "ABSENT"
    try:
        s = p.read_text(encoding="utf-8")
        compile(ast.parse(s), str(p), "exec")
        return "READY"
    except (OSError, SyntaxError, ValueError):
        return "BROKEN"


def graph_status(repo: Path) -> dict:
    g = repo / "graphify-out" / "graph.json"
    if not g.is_file():
        return {"status": "ABSENT", "path": "graphify-out/graph.json", "fix": "via-graph build(只跑本機 AST)"}
    try:
        head_t = int(subprocess.run(["git", "-C", str(repo), "log", "-1", "--format=%ct"], capture_output=True, text=True, timeout=30).stdout.strip() or 0)
    except (OSError, ValueError, subprocess.SubprocessError):
        head_t = 0
    fresh = g.stat().st_mtime >= head_t
    return {"status": "FRESH" if fresh else "STALE", "path": "graphify-out/graph.json"}


def omniroute_probe(url: str = OMNI_URL, timeout: float = 3.0) -> dict:
    req = urllib.request.Request(url.rstrip("/") + "/models", headers={"User-Agent": "VCGC-StartupEngine-probe"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:                       # noqa: S310 — 只探本機閘道
            return {"status": "ONLINE", "http": r.status, "url": url}
    except urllib.error.HTTPError as e:
        return {"status": "ONLINE_AUTH_REQUIRED" if e.code in (401, 403) else "DEGRADED", "http": e.code, "url": url}
    except (urllib.error.URLError, OSError, ValueError) as e:
        return {"status": "OFFLINE", "http": None, "url": url, "why": type(e).__name__}


def lane2(fake: bool) -> dict:
    if fake:
        return {"status": "PASS", "fake": True, "omniroute": omniroute_probe()}
    repo = VIA.parent
    g = graph_status(repo)
    mcp = compiles(tail(VIA / "supportive modules" / "registry", "CGC_MDL279_MCPServer"))
    vdf = compiles(tail(VIA / "functional modules" / "VDF", "VDF_SystemManager"))
    omni = omniroute_probe()
    ok = g["status"] == "FRESH" and mcp == "READY" and vdf == "READY" and omni["status"] in ("ONLINE", "ONLINE_AUTH_REQUIRED")
    return {"status": "PASS" if ok else "DEGRADED", "graphify": g, "mcp": mcp, "vdf_manager": vdf, "omniroute": omni,
            "note": "OmniRoute 只探測、不分流(裁定 11)"}


# ---------------------------------------------------------------- 第 3 道:遠端控制(只檢查 · 記錄)
def lane3(fake: bool = False) -> dict:
    cmd = os.environ.get("VCGC_REMOTE_STATUS_CMD", "").strip()
    if not cmd:
        r = {"status": "UNVERIFIED", "why": "沒有設定 VCGC_REMOTE_STATUS_CMD;遠端控制要在主機檢查", "where": where()}
    else:
        try:
            cp = subprocess.run(shlex.split(cmd, posix=os.name != "nt"), capture_output=True, text=True, timeout=30, stdin=subprocess.DEVNULL)
            text = (cp.stdout + cp.stderr).upper()
            r = {"status": "ONLINE" if cp.returncode == 0 and "ONLINE" in text and "OFFLINE" not in text else "OFFLINE",
                 "rc": cp.returncode, "where": where()}
        except (OSError, ValueError, subprocess.SubprocessError) as e:
            r = {"status": "OFFLINE", "why": type(e).__name__, "where": where()}
    r["checked_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    r["note"] = "只檢查並記錄,不代按同意、不自己拉起(裁定 14)"
    save(work_dir() / "remote_control_status.json", r)
    return r


LANES = {1: lane1, 2: lane2, 3: lane3}


def run_lane(n: int, session: Path) -> int:
    accel = accel_env()
    fake = os.environ.get("VCGC_BOOT_FAKE_LANES") == "1"
    path = session / f"lane{n}_health.json"
    save(path, {"lane": n, "pid": os.getpid(), "status": "STARTING", "accelerator": accel})
    try:
        res = LANES[n](fake)
    except Exception as exc:  # noqa: BLE001 — 這一道壞了寫成 RED 收據,不拖垮另兩道
        res = {"status": "RED", "why": f"{type(exc).__name__}: {exc}"[:300]}
    save(path, {"lane": n, "pid": os.getpid(), "accelerator": accel, "at": time.strftime("%Y-%m-%dT%H:%M:%S"), **res})
    return 0


# ---------------------------------------------------------------- boot
def boot(seconds: float = 900.0, max_cpu: float | None = None, wait: float | None = None) -> dict:
    accel = accel_env()
    work = work_dir()
    stale = de_pressure(work)
    prio = lower_priority()
    cal = calm(float(max_cpu if max_cpu is not None else os.environ.get("VCGC_PRESSURE_MAX", 0.85)),
               float(wait if wait is not None else os.environ.get("VCGC_CALM_WAIT", 30)))
    session = work / "sessions" / f"{time.strftime('%Y%m%dT%H%M%S')}-{uuid.uuid4().hex[:6]}"
    session.mkdir(parents=True)
    procs, logs = {}, []
    for n in (1, 2, 3):
        log = (session / f"lane{n}.log").open("ab")
        logs.append(log)
        kw = {"creationflags": 0x00004000} if os.name == "nt" else {"start_new_session": True}
        procs[n] = subprocess.Popen([sys.executable, str(HERE), "_lane", str(n), str(session)], cwd=str(VIA), stdout=log, stderr=log,
                                    stdin=subprocess.DEVNULL, env=dict(os.environ), **kw)
    save(session / "session.json", {"engine": TAG, "expires": time.time() + seconds + 60,
                                     "processes": [{"lane": n, "pid": p.pid} for n, p in procs.items()]})
    deadline = time.time() + seconds
    codes = {}
    for n, p in procs.items():
        try:
            codes[n] = p.wait(timeout=max(1.0, deadline - time.time()))
        except subprocess.TimeoutExpired:
            PRIOR_KILL = _kill(p.pid)
            codes[n] = 124 if PRIOR_KILL else 125
    for log in logs:
        log.close()
    lanes = {}
    for n in (1, 2, 3):
        f = session / f"lane{n}_health.json"
        try:
            lanes[n] = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            lanes[n] = {"lane": n, "status": "RED", "why": "沒有收據"}
        lanes[n]["exit_code"] = codes[n]
    want = {1: ("PASS",), 2: ("PASS",), 3: ("ONLINE",)}
    missing = [n for n in (1, 2, 3) if lanes[n].get("status") in ("STARTING", "RED") or codes[n] != 0]
    online = not missing and all(lanes[n].get("status") in want[n] for n in (1, 2, 3))
    status = "ONLINE" if online else "RED" if missing else "DEGRADED"
    summary = " · ".join(f"L{n}={lanes[n].get('status')}(pid {lanes[n].get('pid')})" for n in (1, 2, 3))
    result = {"engine": TAG, "where": where(), "status": status, "summary": summary, "accelerator": accel, "phase0": {**prio, **cal, **stale},
              "session": str(session), "lanes": lanes, "at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    save(work / "boot_status.json", result)
    return result


def print_boot(r: dict) -> int:
    p0 = r["phase0"]
    print(f"[boot] {TAG} · {r['where']} · 降壓 {p0.get('how')} · 壓力 cpu={p0.get('cpu')} 門檻 {p0.get('limit')} → {p0.get('within_threshold')}"
          f" · 清掉本引擎過期子行程 {len(p0.get('stale_killed', []))}", flush=True)
    print(f"[boot] 加速器 {'載到' if r['accelerator']['accel_loaded'] else '沒載到(假加速 = 黃)'} · 執行緒上限 {r['accelerator']['thread_cap']}"
          f" · 防休眠 {r['accelerator']['keep_awake']}", flush=True)
    for n in ("1", "2", "3"):
        lane = r["lanes"].get(n) or r["lanes"].get(int(n), {})
        print(f"[boot] 第 {n} 道 · pid {lane.get('pid')} · exit {lane.get('exit_code')} · {lane.get('status')}", flush=True)
    print(f"[boot] 總燈 {r['status']} · {r['summary']} · 收據 {work_dir() / 'boot_status.json'}", flush=True)
    return {"ONLINE": 0, "DEGRADED": 2}.get(r["status"], 1)


def cmd(a: list) -> int:
    verb = a[0]
    accel = accel_env()
    if not accel["accel_loaded"]:
        print("[accel] 加速器橋沒載到(假加速 = 黃),照實往下跑", flush=True)
    if verb == "boot":
        sec = float(a[a.index("--seconds") + 1]) if "--seconds" in a else 900.0
        return print_boot(boot(sec))
    if verb == "audit":
        r = lane1(False)
        print(f"[audit] 環境 {r['env']['status']} · 指紋 {r['fingerprint']['status']}({r['fingerprint']['packages']} 套件)"
              + (f" · 補裝計畫:{r['install_plan']}" if r.get("install_plan") else ""), flush=True)
        return {"PASS": 0}.get(r["env"]["status"], 2)
    if verb == "backup":
        r = run_hub("via-bak")
        print(f"[backup] {r['status']} · rc {r['rc']} · {r['tail'][-200:]}", flush=True)
        return 0 if r["status"] == "PASS" else 2
    if verb == "remote":
        r = lane3()
        print(f"[remote] {r['status']} · {r.get('why', '')} · 收據 {work_dir() / 'remote_control_status.json'}", flush=True)
        return 0 if r["status"] == "ONLINE" else 2
    if verb == "scan":
        r = run_hub("via-pano")
        print(f"[scan] {r['status']} · rc {r['rc']} · {r['tail'][-200:]}", flush=True)
        return 0 if r["status"] == "PASS" else 2
    if verb == "lanes":
        f = work_dir() / "boot_status.json"
        if not f.is_file():
            print("[lanes] 還沒有 boot 收據", flush=True)
            return 2
        return print_boot(json.loads(f.read_text(encoding="utf-8")))
    return 2


# ---------------------------------------------------------------- 自測
def selftest() -> list:
    rows = list(PRIOR.selftest())
    mine = []

    def chk(name, ok, detail=""):
        mine.append({"name": name, "ok": bool(ok), "detail": str(detail)[:300]})

    src = HERE.read_text(encoding="utf-8")
    acc = accel_env()
    chk("v0200 T1 加速器真的載到 · 第 3 行標記 · 網路橋 · 執行緒上限寫進環境變數",
        VIA_ACCEL is not None and src.splitlines()[2] == "# [VIA:ACCEL-BRIDGE:v0111]" and VIA_NET_TOOL_PATH is not None
        and all(os.environ.get(k) == str(acc["thread_cap"]) for k in THREAD_VARS), acc)
    probe = subprocess.run([sys.executable, str(HERE), "_probe_priority"], capture_output=True, text=True, timeout=60)
    chk("v0200 T2 降壓:子行程裡降優先權(POSIX nice ≥ 5 / Windows BELOW_NORMAL);本行程不受影響",
        probe.returncode == 0 and json.loads(probe.stdout.strip().splitlines()[-1]).get("priority_lowered") is True, probe.stdout[-200:])
    with tempfile.TemporaryDirectory(prefix="vcgc_se200_") as td:
        os.environ["VCGC_STARTUP_WORK"] = td
        os.environ["VCGC_BOOT_FAKE_LANES"] = "1"
        os.environ.pop("VCGC_REMOTE_STATUS_CMD", None)
        try:
            r1 = boot(120, max_cpu=1e9, wait=0)
            os.environ["VCGC_REMOTE_STATUS_CMD"] = f'"{sys.executable}" -c "print(\'ONLINE\')"'
            r2 = boot(120, max_cpu=1e9, wait=0)
        finally:
            os.environ.pop("VCGC_BOOT_FAKE_LANES", None)
            os.environ.pop("VCGC_REMOTE_STATUS_CMD", None)
        pids = {r1["lanes"][n]["pid"] for n in (1, 2, 3)}
        chk("v0200 T3 boot:三道各是獨立子行程(3 個不同 PID、都不是本行程、exit 0、各有收據);遠端沒有檢查指令 → UNVERIFIED → 總燈 DEGRADED",
            len(pids) == 3 and os.getpid() not in pids and all(r1["lanes"][n]["exit_code"] == 0 for n in (1, 2, 3))
            and r1["lanes"][3]["status"] == "UNVERIFIED" and r1["status"] == "DEGRADED", r1["summary"])
        chk("v0200 T4 遠端檢查指令回 ONLINE、另兩道 PASS → 總燈 ONLINE;remote_control_status.json 有寫",
            r2["status"] == "ONLINE" and json.loads((Path(td) / "remote_control_status.json").read_text(encoding="utf-8"))["status"] == "ONLINE", r2["summary"])
        site, fpw = Path(td) / "site", Path(td) / "fp_work"
        site.mkdir()
        fpw.mkdir()
        (site / "a-1.0.dist-info").mkdir()
        f1 = env_fingerprint(fpw, [str(site)])
        f2 = env_fingerprint(fpw, [str(site)])
        (site / "b-2.0.dist-info").mkdir()
        f3 = env_fingerprint(fpw, [str(site)])
        chk("v0200 T5 環境指紋:第一次算、沒變 → 304_NOT_MODIFIED、多一個套件 → CHANGED", (f1["status"], f2["status"], f3["status"]) == ("FIRST", "304_NOT_MODIFIED", "CHANGED"),
            (f1["status"], f2["status"], f3["status"]))
        mine_sleep = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(60)", HERE.name, "_lane", "9"])
        other_sleep = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(60)"])
        old = Path(td) / "sessions" / "old"
        old.mkdir(parents=True)
        save(old / "session.json", {"expires": time.time() - 5, "processes": [{"pid": mine_sleep.pid}, {"pid": other_sleep.pid}]})
        dp = de_pressure(Path(td))
        time.sleep(0.5)
        mine_dead, other_alive = mine_sleep.poll() is not None, other_sleep.poll() is None
        other_sleep.kill()
        mine_sleep.kill()
        os.environ.pop("VCGC_STARTUP_WORK", None)
    chk("v0200 T6 降壓清程序:只砍本引擎記過、已過期、命令列是本引擎三道的;同一份紀錄裡別的行程不碰",
        mine_dead and other_alive and dp["stale_killed"] == [mine_sleep.pid], dp)
    import http.server
    import threading
    srv = http.server.HTTPServer(("127.0.0.1", 0), type("H", (http.server.BaseHTTPRequestHandler,), {
        "do_GET": lambda s: (s.send_response(200), s.end_headers(), s.wfile.write(b"{}")), "log_message": lambda *a: None}))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    on = omniroute_probe(f"http://127.0.0.1:{srv.server_address[1]}/v1")
    srv.shutdown()
    off = omniroute_probe("http://127.0.0.1:9/v1", timeout=1)
    chk("v0200 T7 OmniRoute 只探測:本機假閘道 → ONLINE;關著的埠 → OFFLINE(不分流、不拉起)", on["status"] == "ONLINE" and off["status"] == "OFFLINE", (on, off))
    tree = ast.parse(src)
    chk("v0200 T8 本檔不 import 他系統(VDF / VRN / VQG / VAP)· 不用 eval / exec · 零 TA-Lib",
        not any(isinstance(n, (ast.Import, ast.ImportFrom)) and any(x in ast.unparse(n) for x in ("VDF_", "VRN", "VQG_", "VAP_", "talib")) for n in ast.walk(tree))
        and not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in {"eval", "exec"} for n in ast.walk(tree)))
    return rows + mine


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["_lane"]:
        return run_lane(int(a[1]), Path(a[2]))
    if a[:1] == ["_probe_priority"]:
        print(json.dumps(lower_priority()))
        return 0
    if a[:1] in (["selftest"], ["test"], ["--selftest"]):
        rows = selftest()
        failed = [r for r in rows if not r["ok"]]
        mine = [r for r in rows if r["name"].startswith("v0200 ")]
        for row in rows:
            if row in mine or not row["ok"]:
                print(f"[{'PASS' if row['ok'] else 'FAIL'}] {row['name']} — {row['detail']}", flush=True)
        print(f"[計] {TAG} 本版 {sum(r['ok'] for r in mine)}/{len(mine)} · 前版 {PRIOR_PATH.stem} {sum(r['ok'] for r in rows if r not in mine)}/{len(rows) - len(mine)}", flush=True)
        print(f"{len(rows) - len(failed)}/{len(rows)}", flush=True)
        return 1 if failed else 0
    if a[:1] and a[0] in NEW_VERBS:
        return cmd(a)
    if a[:1] in (["help"], []):
        print(f"{TAG} 新動詞:" + " · ".join(NEW_VERBS) + "(其餘照前版:" + " · ".join(PRIOR.VERBS) + ")", flush=True)
    return PRIOR.main(a)


if __name__ == "__main__":
    raise SystemExit(main())
