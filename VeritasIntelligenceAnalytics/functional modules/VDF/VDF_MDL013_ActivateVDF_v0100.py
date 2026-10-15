#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_MDL013_ActivateVDF v0100 — VDF 獨立啟動:一個指令啟動一切並連到 HTML U/I(入口 = 同夾 ActivateVDF.py)

操作員 2026-10-15:「範圍限縮在 VDF · ActivateVDF.py 啟動一切並連結 html u/i · 在開始指令前第一個動作為優化 cpu dram ·
  在 cpu/dram 允許範圍內三個獨立流程同步進行 · 善用 temp 支援不足的記憶體 · 先掌握生成台股個股清單及主動式台股 etf 清單引擎
  順利產出所有清單作為重要輸入之二後逐一啟動檢查修復各引擎 · 檢視現在資料庫現況補不足」;「他是獨立系統有自己的 main 跟其他相關
  跟其他系統互不干擾」。
  ① CPU / DRAM(第一個動作):量核數 · 負載 · 可用記憶體(psutil > /proc/meminfo > GlobalMemoryStatusEx;量不到照實 None)
     → gc 回收 → 並行條數 = min(3, 可用核 − 1, (可用 − 保留 1 GB) ÷ 每條 1 GB),至少 1(照順序跑)
     → 每條執行緒上限(OMP / MKL / OPENBLAS / NUMEXPR / POLARS / VIA_DUCKDB_THREADS)· DuckDB 記憶體上限 VIA_DUCKDB_MEM
     → temp 溢寫:TMP / TEMP / TMPDIR / POLARS_TEMP_DIR / VIA_DUCKDB_TEMP_DIR 指本輪夾(VIA_TEMP_ROOT > %LOCALAPPDATA%\VIA_TEMP
       > 系統 temp;不在 OneDrive)· 記憶體不夠三條時 VIA_SPILL_TO_DISK=1 · 只留最近 5 輪(只清本工具自己建的夾)
     → 記憶體壓力閘:背景每 2 秒量;可用 < 總量 10% 時新步驟先等,解除才放行。
  ② 兩張清單(所有擷取的開頭):VDF 管理員 fetch run 009 · 010(全台股 MDL009 · 主動式台股 ETF MDL010;兩支同時跑)→ fetch verify。
     本輪產出且驗收過 = GREEN;閘關但既有清單驗收過 = YELLOW 照用;都沒有 = 擷取流程 BLOCKED(其餘兩條照跑)。
  ③ 三條獨立流程同時跑(條數 = ①;一條紅不擋另兩條):
       擷取      fetch run <擷取冊其餘全部列> --mode live --apply(live 要操作員雙閘;閘關 = GATED 不是壞)
       引擎      engine list → engine launch <全部>(逐一:載入 + 自測;結果 RESULT_engine_launch_latest.json)
       資料庫    db check(缺庫 · 缺表 · 空表 · 過舊)→ refill(補不足;預設只列計畫,--refill-apply 才真跑)
  ④ U/I:管理員 ui → VIA_Reports/vdf/VDF_UI_latest.html;本檔寫總覽 VIA_Reports/vdf/activate/ACTIVATE_VDF_latest.{html,json}
     (燈 · 資源卡 · 每步一列 · 連 VDF 操作頁 / 資料庫閘 / 引擎矩陣)並開瀏覽器(--no-open 不開)。
  只起 VDF 自己的管理員尾版(VDF_SystemManager_v*.py)當子行程,不匯入 VCGC / VRN 程式、不改他系統的檔。
  用法:python ActivateVDF.py [run|plan|resources] [--mode live|fixture|block] [--dry] [--fetch-home D] [--db-home D]
        [--flows fetch,engines,db] [--refill-apply] [--timeout S] [--no-ui] [--no-open] | --selftest
  rc:0 全綠 · 2 有黃 / 閘關 / 擋下(誠實,不算綠)· 1 有紅。同意閘(VIA_NET_CONSENT / VIA_SCRAPE_CONSENT)是操作員的手:
  本檔不讀值、不寫,只照本視窗原樣傳給子行程。不碰 TA-Lib。不裝套件。
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
# ===== [VIA:NET-BRIDGE:END] =====

import argparse
import datetime as _dt
import gc
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
TAG = f"VDF_MDL013_ActivateVDF v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
MANAGER_GLOB = "VDF_SystemManager_v*.py"
FETCH_BOOK_GLOB = "VDF_FetchSystem_SSOT_v*.json"
REPORT_DIR = VIA / "VIA_Reports" / "vdf" / "activate"
UI_LINKS = (("VDF 操作頁(U/I)", "VDF_UI_latest.html"), ("資料庫閘(db check)", "DB_CHECK_latest.html"),
            ("引擎矩陣", "ENGINE_MATRIX_latest.html"), ("引擎啟動結果(JSON)", "RESULT_engine_launch_latest.json"))
CONSENT_KEYS = ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT")   # 只照原樣傳給子行程;本檔永不寫
THREAD_KEYS = ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_MAX_THREADS",
               "POLARS_MAX_THREADS", "VIA_DUCKDB_THREADS")
FLOWS = ("fetch", "engines", "db")
FLOW_ZH = {"fetch": "流程一 · 擷取(清單以外的全部擷取引擎)", "engines": "流程二 · 引擎逐一啟動檢查(載入 + 自測)",
           "db": "流程三 · 資料庫現況 + 補不足(db check → refill)"}
PER_FLOW_MB = 1024          # 一條流程最少要的可用記憶體(DuckDB / polars 子行程 + 餘裕)
RESERVE_MB = 1024           # 留給作業系統與其他程式
PRESSURE_FRACTION = 0.10    # 可用記憶體 < 總量 10% = 壓力:新步驟先等
KEEP_RUNS = 5               # temp 只留最近 5 輪(只清本工具自己建的夾)


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def tail(folder: Path, glob: str) -> Path | None:
    hits = [p for p in Path(folder).glob(glob) if _vnum(p) >= 0]
    return max(hits, key=_vnum) if hits else None


# ---------------------------------------------------------------- ① CPU / DRAM
def mem_info() -> dict:
    """→ {total_mb, avail_mb, how}。psutil > /proc/meminfo > Windows GlobalMemoryStatusEx;都拿不到 = None(誠實,不猜)。"""
    try:
        import psutil  # type: ignore
        vm = psutil.virtual_memory()
        return {"total_mb": vm.total // 2**20, "avail_mb": vm.available // 2**20, "how": "psutil"}
    except Exception:
        pass
    try:
        txt = Path("/proc/meminfo").read_text()
        kv = {k: int(v.split()[0]) for k, v in (ln.split(":", 1) for ln in txt.splitlines() if ":" in ln)}
        return {"total_mb": kv["MemTotal"] // 1024, "avail_mb": kv.get("MemAvailable", kv.get("MemFree", 0)) // 1024,
                "how": "/proc/meminfo"}
    except Exception:
        pass
    if os.name == "nt":
        try:
            import ctypes

            class _MS(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            ms = _MS()
            ms.dwLength = ctypes.sizeof(_MS)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms)):
                return {"total_mb": ms.ullTotalPhys // 2**20, "avail_mb": ms.ullAvailPhys // 2**20, "how": "GlobalMemoryStatusEx"}
        except Exception:
            pass
    return {"total_mb": None, "avail_mb": None, "how": "none"}


def cpu_info() -> dict:
    n = os.cpu_count() or 1
    try:
        usable = len(os.sched_getaffinity(0))          # Linux:真的能用的核
    except (AttributeError, OSError):
        usable = n
    try:
        load1 = os.getloadavg()[0]
    except (AttributeError, OSError):
        load1 = None
    return {"logical": n, "usable": usable, "load1": load1}


def plan_slots(cpu: dict, mem: dict, want: int = 3, per_flow_mb: int = PER_FLOW_MB, reserve_mb: int = RESERVE_MB) -> dict:
    """同時跑幾條流程:min(要的 3 條, 可用核 - 1(至少 1), (可用記憶體 - 保留) // 每條所需);至少 1(照順序跑,不放棄)。"""
    cores = max(1, (cpu.get("usable") or 1) - 1)
    if cpu.get("load1") is not None and cpu["load1"] > cpu.get("usable", 1):
        cores = max(1, cores - int(cpu["load1"] - cpu.get("usable", 1)))          # 機器已滿載:讓出
    avail = mem.get("avail_mb")
    by_mem = want if avail is None else max(1, (avail - reserve_mb) // max(1, per_flow_mb))
    slots = int(max(1, min(want, cores, by_mem)))
    threads = max(1, (cpu.get("usable") or 1) // slots)
    if avail is None:
        duck_mb = 2048
    else:
        duck_mb = max(256, int((avail - reserve_mb) * 0.6) // slots)
    why = []
    if slots < want:
        why.append(f"核 {cpu.get('usable')}(留 1)→ {cores}" if cores < want else "")
        why.append(f"可用記憶體 {avail} MB(保留 {reserve_mb} · 每條 {per_flow_mb})→ {by_mem}" if avail is not None and by_mem < want else "")
    return {"slots": slots, "threads_per_flow": threads, "duckdb_mem_mb": duck_mb,
            "spill": avail is None or avail < (reserve_mb + per_flow_mb * want),
            "why": [w for w in why if w] or ["資源足夠:三條流程同時跑"]}


def temp_root() -> Path:
    """temp 根:VIA_TEMP_ROOT > Windows %LOCALAPPDATA%\\VIA_TEMP(不在 OneDrive)> 系統 temp/VIA_TEMP。"""
    if os.environ.get("VIA_TEMP_ROOT"):
        return Path(os.environ["VIA_TEMP_ROOT"])
    if os.name == "nt" and os.environ.get("LOCALAPPDATA"):
        return Path(os.environ["LOCALAPPDATA"]) / "VIA_TEMP"
    return Path(tempfile.gettempdir()) / "VIA_TEMP"


def purge_runs(base: Path, keep: int = KEEP_RUNS) -> list:
    """只清 <temp 根>/ActivateVDF/ 底下本工具建的輪夾(名 = run_YYYYmmdd_HHMMSS);留最近 keep 輪。"""
    if not base.is_dir() or base.name != "ActivateVDF":
        return []
    runs = sorted(p for p in base.iterdir() if p.is_dir() and re.fullmatch(r"run_\d{8}_\d{6}(_\d+)?", p.name))
    gone = []
    for p in runs[:-keep] if keep > 0 else runs:
        shutil.rmtree(p, ignore_errors=True)
        gone.append(p.name)
    return gone


def optimize_resources(want: int = 3, stamp: str | None = None, root: Path | None = None) -> dict:
    """第一個動作:量 CPU / DRAM → 回收本行程記憶體 → 決定並行條數 · 每條執行緒 / DuckDB 記憶體上限 → 開 temp 溢寫夾。"""
    before = mem_info()
    gc.collect()
    after = mem_info()
    cpu = cpu_info()
    plan = plan_slots(cpu, after, want)
    stamp = stamp or _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    base = Path(root or temp_root()) / "ActivateVDF"
    run_dir = base / f"run_{stamp}"
    n = 1
    while run_dir.exists():
        run_dir = base / f"run_{stamp}_{n}"
        n += 1
    run_dir.mkdir(parents=True, exist_ok=True)
    purged = purge_runs(base)
    try:
        free_mb = shutil.disk_usage(run_dir).free // 2**20
    except OSError:
        free_mb = None
    return {"cpu": cpu, "mem_before": before, "mem": after, "plan": plan, "temp_run": str(run_dir),
            "temp_free_mb": free_mb, "temp_low": free_mb is not None and free_mb < 2048, "purged": purged}


def flow_env(res: dict, flow: str, base_env: dict | None = None) -> dict:
    """子行程環境:VDF 自己的啟動標記 + 執行緒上限 + temp 溢寫 + DuckDB 記憶體上限;同意閘照原樣(不讀值、不寫)。"""
    env = dict(os.environ if base_env is None else base_env)
    plan = res["plan"]
    tdir = Path(res["temp_run"]) / flow
    tdir.mkdir(parents=True, exist_ok=True)
    th = str(plan["threads_per_flow"])
    for k in THREAD_KEYS:
        env[k] = th
    for k in ("TMP", "TEMP", "TMPDIR", "POLARS_TEMP_DIR", "VIA_DUCKDB_TEMP_DIR"):
        env[k] = str(tdir)
    env["VIA_TEMP_ROOT"] = str(Path(res["temp_run"]).parent.parent)
    env["VIA_DUCKDB_MEM"] = f"{plan['duckdb_mem_mb']}MB"
    if plan.get("spill"):
        env["VIA_SPILL_TO_DISK"] = "1"
    env["VIA_FROM_VCGC"] = "YES"        # 舊名 = 經任一系統自己的 manager / 啟動器啟動(L120 ⑥ 甲);VDF 管理員的入口標記
    env["VIA_FROM_VDFSM"] = "YES"       # VDF System Manager 總控標記(MDL008 / MDL009 / MDL010 認它)
    env["PYTHONIOENCODING"] = "utf-8"
    return env


class MemGate:
    """記憶體壓力閘:背景每 interval 秒量一次;可用 < 總量 × fraction(或 < 保留)= 壓力,新步驟先等(最多 max_wait 秒)。"""

    def __init__(self, reader=mem_info, fraction: float = PRESSURE_FRACTION, floor_mb: int = RESERVE_MB // 2, interval: float = 2.0):
        self.reader, self.fraction, self.floor_mb, self.interval = reader, fraction, floor_mb, interval
        self.ok = threading.Event()
        self.ok.set()
        self.stop = threading.Event()
        self.samples, self.waits = [], []
        self._t = None

    def pressured(self, m: dict) -> bool:
        if m.get("avail_mb") is None or not m.get("total_mb"):
            return False
        return m["avail_mb"] < max(self.floor_mb, m["total_mb"] * self.fraction)

    def tick(self):
        m = self.reader()
        self.samples.append(m.get("avail_mb"))
        (self.ok.clear() if self.pressured(m) else self.ok.set())

    def _loop(self):
        while not self.stop.is_set():
            self.tick()
            self.stop.wait(self.interval)

    def start(self):
        self.tick()
        self._t = threading.Thread(target=self._loop, daemon=True)
        self._t.start()
        return self

    def close(self):
        self.stop.set()
        if self._t:
            self._t.join(timeout=5)

    def wait(self, who: str, max_wait: float = 600.0) -> float:
        t0 = time.time()
        if not self.ok.is_set():
            self.ok.wait(max_wait)
            self.waits.append({"who": who, "secs": round(time.time() - t0, 1)})
        return time.time() - t0

    def card(self) -> dict:
        s = [x for x in self.samples if x is not None]
        return {"samples": len(self.samples), "min_avail_mb": min(s) if s else None, "waits": self.waits}


# ---------------------------------------------------------------- 執行(只起 VDF 自己的管理員)
def manager_path(folder: Path = HERE) -> Path | None:
    return tail(folder, MANAGER_GLOB)


def run_step(name: str, args: list, env: dict, log_dir: Path, gate: MemGate | None = None,
             timeout: float | None = None, manager: Path | None = None, py: str | None = None) -> dict:
    mgr = manager or manager_path()
    rec = {"step": name, "args": args, "manager": mgr.name if mgr else None}
    if mgr is None:
        return dict(rec, rc=None, lamp="RED", secs=0, note=f"{MANAGER_GLOB} 不在 {HERE}")
    waited = gate.wait(name) if gate else 0.0
    log = log_dir / (re.sub(r"[^A-Za-z0-9_.-]+", "_", name) + ".log")
    t0 = time.time()
    try:
        with open(log, "w", encoding="utf-8", errors="replace") as fh:
            p = subprocess.run([py or sys.executable, str(mgr), *args], cwd=str(mgr.parent), env=env,
                               stdout=fh, stderr=subprocess.STDOUT, timeout=timeout)
        rc = p.returncode
        note = ""
    except subprocess.TimeoutExpired:
        rc, note = None, f"逾時 {timeout}s"
    secs = round(time.time() - t0, 1)
    try:
        lines = [ln for ln in log.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()]
    except OSError:
        lines = []
    summ = next((ln.strip() for ln in reversed(lines) if "[計]" in ln or "GATED" in ln or "[驗收]" in ln), lines[-1].strip() if lines else "")
    return dict(rec, rc=rc, lamp=lamp_of(rc), secs=secs, waited=round(waited, 1), log=str(log), summary=summ[:240], note=note)


def lamp_of(rc) -> str:
    return {0: "GREEN", 2: "YELLOW", 3: "YELLOW", 4: "GATED"}.get(rc, "RED")


def fetch_ids(book_dir: Path = HERE) -> tuple:
    """→ (清單步 ids, 其他擷取 ids, 冊名)。讀 VDF 自己的擷取冊尾版(只讀)。"""
    b = tail(book_dir, FETCH_BOOK_GLOB)
    if b is None:
        return ["009", "010"], [], None
    d = json.loads(b.read_text(encoding="utf-8"))
    first = list(d.get("first_step") or ["009", "010"])
    rest = [e["id"] for e in d.get("engines", []) if e.get("id") and e["id"] not in first]
    return first, rest, b.name


def engine_ids(env: dict, log_dir: Path, manager: Path | None = None, py: str | None = None) -> list:
    mgr = manager or manager_path()
    if mgr is None:
        return []
    try:
        p = subprocess.run([py or sys.executable, str(mgr), "engine", "list", "--json"], cwd=str(mgr.parent), env=env,
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
        txt = p.stdout[p.stdout.find("{"):]
        rows = json.JSONDecoder().raw_decode(txt)[0].get("engines", [])
    except (subprocess.TimeoutExpired, ValueError, OSError):
        return []
    return [r["eid"] for r in rows if r.get("eid")]


def fetch_args(verb: str, ids: list, opt) -> list:
    a = ["fetch", verb, *ids]
    if verb == "run":
        a += ["--mode", opt.mode] + ([] if opt.dry else ["--apply"])
    if opt.fetch_home:
        a += ["--home", opt.fetch_home]
    return a


def phase_lists(opt, res: dict, gate: MemGate, log_dir: Path, manager=None, py=None) -> dict:
    """先掌握兩張清單(全台股 · 主動式台股 ETF):兩支同時跑(資源允許時)→ 驗收輸出;沒產出就看既有清單在不在。"""
    first, _, book = fetch_ids()
    env = flow_env(res, "lists")
    workers = max(1, min(len(first), res["plan"]["slots"]))
    with ThreadPoolExecutor(max_workers=workers) as ex:
        runs = list(ex.map(lambda i: run_step(f"lists_run_{i}", fetch_args("run", [i], opt), env, log_dir, gate,
                                              opt.timeout, manager, py), first))
    ver = run_step("lists_verify", fetch_args("verify", first, opt), env, log_dir, gate, 600, manager, py)
    ok = ver["rc"] == 0
    lamp = "GREEN" if ok and all(r["rc"] == 0 for r in runs) else ("YELLOW" if ok else
                                                                     "GATED" if any(r["rc"] == 4 for r in runs) else "RED")
    return {"ids": first, "book": book, "runs": runs, "verify": ver, "lists_ready": ok, "lamp": lamp,
            "note": ("兩張清單本輪產出且驗收過" if lamp == "GREEN" else
                     "本輪沒重產,但既有清單驗收過 → 照用" if ok else
                     "同意閘沒開(操作員的手)且沒有既有清單 → 擷取流程停,其餘兩條照跑" if lamp == "GATED" else
                     "清單沒產出也沒有既有清單 → 擷取流程停,其餘兩條照跑")}


def flow_fetch(opt, res, gate, log_dir, lists: dict, manager=None, py=None) -> dict:
    if not lists["lists_ready"]:
        return {"flow": "fetch", "lamp": "BLOCKED", "steps": [], "note": "兩張清單不在 → 不擷取(清單是所有擷取的開頭)"}
    _, rest, _ = fetch_ids()
    st = run_step("fetch_run_all", fetch_args("run", rest, opt), flow_env(res, "fetch"), log_dir, gate, opt.timeout, manager, py)
    return {"flow": "fetch", "lamp": st["lamp"], "steps": [st], "n_ids": len(rest)}


def flow_engines(opt, res, gate, log_dir, manager=None, py=None) -> dict:
    env = flow_env(res, "engines")
    ids = engine_ids(env, log_dir, manager, py)
    if not ids:
        return {"flow": "engines", "lamp": "RED", "steps": [], "note": "engine list 拿不到引擎"}
    st = run_step("engine_launch", ["engine", "launch", *ids], env, log_dir, gate, opt.timeout, manager, py)
    out = {"flow": "engines", "lamp": st["lamp"], "steps": [st], "n_engines": len(ids)}
    rj = VIA / "VIA_Reports" / "vdf" / "RESULT_engine_launch_latest.json"
    if rj.is_file() and manager is None:
        try:
            o = json.loads(rj.read_text(encoding="utf-8"))
            out.update(launchable=o.get("launchable"), n=o.get("n"), selftest=o.get("selftest"), launch_lamp=o.get("lamp"),
                       red=[p["family"] for p in o.get("per", []) if p.get("selftest_lamp") == "RED" or not p.get("launchable")][:40])
        except (ValueError, OSError):
            pass
    return out


def flow_db(opt, res, gate, log_dir, manager=None, py=None) -> dict:
    env = flow_env(res, "db")
    home = ["--home", opt.db_home] if opt.db_home else []
    s1 = run_step("db_check", ["db", "check", *home], env, log_dir, gate, 1800, manager, py)
    refill = ["refill", *home] + (["--apply"] if (opt.refill_apply and not opt.dry) else [])
    s2 = run_step("db_refill", refill, env, log_dir, gate, opt.timeout, manager, py)
    worst = max((s1["lamp"], s2["lamp"]), key=lambda x: ["GREEN", "YELLOW", "GATED", "RED"].index(x) if x in
                ("GREEN", "YELLOW", "GATED", "RED") else 3)
    return {"flow": "db", "lamp": worst, "steps": [s1, s2],
            "note": "refill 沒帶 --refill-apply = 只列補擷取計畫" if not opt.refill_apply else ""}


def run_flows(opt, res, gate, log_dir, lists, manager=None, py=None) -> list:
    """三條獨立流程同時跑(條數 = 資源計畫 slots;slots 1 = 照順序)。一條紅不擋另兩條。"""
    jobs = {"fetch": lambda: flow_fetch(opt, res, gate, log_dir, lists, manager, py),
            "engines": lambda: flow_engines(opt, res, gate, log_dir, manager, py),
            "db": lambda: flow_db(opt, res, gate, log_dir, manager, py)}
    pick = [f for f in FLOWS if f in opt.flows]
    out = {}
    with ThreadPoolExecutor(max_workers=max(1, res["plan"]["slots"])) as ex:
        futs = {f: ex.submit(_timed, f, jobs[f]) for f in pick}
        for f in pick:
            try:
                out[f] = futs[f].result()
            except Exception as exc:  # noqa: BLE001 — 一條流程炸了照記紅,不拖垮另兩條
                out[f] = {"flow": f, "lamp": "RED", "steps": [], "note": f"{type(exc).__name__}: {exc}"}
    return [out[f] for f in pick]


def _timed(name, fn):
    t0 = time.time()
    r = fn()
    r["t0"], r["t1"] = round(t0, 3), round(time.time(), 3)
    return r


def phase_ui(opt, res, log_dir, manager=None, py=None) -> dict:
    env = flow_env(res, "ui")
    env["VIA_NO_OPEN"] = "1"                  # 管理員的 ui 不自己開;套完版面後由本檔開總覽頁(總覽頁連 VDF 操作頁)
    return run_step("ui", ["ui"], env, log_dir, None, 900, manager, py)


# ---------------------------------------------------------------- 報告 + U/I
def overall(lists: dict, flows: list) -> str:
    lamps = [lists["lamp"]] + [f["lamp"] for f in flows]
    if "RED" in lamps:
        return "RED"
    if any(x in ("GATED", "BLOCKED", "YELLOW") for x in lamps):
        return "YELLOW"
    return "GREEN"


def render_html(card: dict, ui_dir: Path) -> str:
    def lamp(x):
        c = {"GREEN": "#1a7f37", "YELLOW": "#9a6700", "GATED": "#0969da", "BLOCKED": "#6e7781"}.get(x, "#cf222e")
        return f'<span class="lamp" style="background:{c}">{html.escape(str(x))}</span>'

    def rel(name):
        p = ui_dir / name
        return (os.path.relpath(p, REPORT_DIR) if p.exists() else None)
    r = card["resources"]
    rows = []
    for st in card["lists"]["runs"] + [card["lists"]["verify"]]:
        rows.append(f"<tr><td>{lamp(st['lamp'])}</td><td>清單</td><td>{html.escape(st['step'])}</td><td>{st['rc']}</td>"
                    f"<td>{st['secs']}</td><td>{html.escape(st.get('summary') or st.get('note') or '—')}</td></tr>")
    for f in card["flows"]:
        for st in f["steps"] or [{"lamp": f["lamp"], "step": "—", "rc": "—", "secs": "—", "summary": f.get("note", "")}]:
            rows.append(f"<tr><td>{lamp(st['lamp'])}</td><td>{html.escape(FLOW_ZH.get(f['flow'], f['flow']))}</td>"
                        f"<td>{html.escape(st['step'])}</td><td>{st['rc']}</td><td>{st['secs']}</td>"
                        f"<td>{html.escape(st.get('summary') or st.get('note') or '—')}</td></tr>")
    links = "".join(f'<li><a href="{html.escape(h)}">{html.escape(z)}</a></li>' if (h := rel(n)) else
                    f"<li>{html.escape(z)} — 還沒產生</li>" for z, n in UI_LINKS)
    eng = next((f for f in card["flows"] if f["flow"] == "engines"), {})
    red = "".join(f"<li>{html.escape(x)}</li>" for x in eng.get("red") or []) or "<li>—</li>"
    return f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VDF 啟動總覽</title><style>
:root{{--bg:#fff;--fg:#1f2328;--mut:#59636e;--bd:#d1d9e0}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0d1117;--fg:#e6edf3;--mut:#9198a1;--bd:#3d444d}}}}
body{{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,"Microsoft JhengHei",sans-serif;margin:0;padding:16px;max-width:1100px}}
h1{{font-size:20px;margin:0 0 4px}}.mut{{color:var(--mut)}}table{{border-collapse:collapse;width:100%;font-size:13px}}
td,th{{border-bottom:1px solid var(--bd);padding:6px 8px;text-align:left;vertical-align:top}}
.lamp{{color:#fff;border-radius:10px;padding:1px 8px;font-size:12px;white-space:nowrap}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;margin:12px 0}}
.card{{border:1px solid var(--bd);border-radius:8px;padding:10px 12px}}.wrap{{overflow-x:auto}}a{{color:#0969da}}
</style></head><body>
<h1>VDF 啟動總覽 {lamp(card['lamp'])}</h1>
<div class="mut">{html.escape(card['tag'])} · {html.escape(card['ts'])} · 管理員 {html.escape(str(card.get('manager')))} · VDF 獨立系統(不載入他系統程式)</div>
<div class="grid">
<div class="card"><b>① CPU / DRAM</b><br>核 {r['cpu']['usable']}/{r['cpu']['logical']} · 負載 {r['cpu']['load1']}<br>
可用記憶體 {r['mem']['avail_mb']} / {r['mem']['total_mb']} MB({html.escape(r['mem']['how'])})<br>
並行 {r['plan']['slots']} 條 · 每條 {r['plan']['threads_per_flow']} 執行緒 · DuckDB {r['plan']['duckdb_mem_mb']} MB<br>
<span class="mut">{html.escape(' · '.join(r['plan']['why']))}</span></div>
<div class="card"><b>temp 溢寫</b><br>{html.escape(r['temp_run'])}<br>剩 {r['temp_free_mb']} MB{' · <b>偏低</b>' if r['temp_low'] else ''}
· 溢寫 {'開' if r['plan']['spill'] else '待命'}<br><span class="mut">記憶體閘:最低可用 {card['memgate']['min_avail_mb']} MB · 等待 {len(card['memgate']['waits'])} 次</span></div>
<div class="card"><b>② 兩張清單</b> {lamp(card['lists']['lamp'])}<br>{html.escape(card['lists']['note'])}</div>
<div class="card"><b>U/I</b><ul>{links}</ul></div>
</div>
<div class="wrap"><table><tr><th>燈</th><th>流程</th><th>步</th><th>rc</th><th>秒</th><th>結果</th></tr>{''.join(rows)}</table></div>
<h3>引擎啟動紅 / 不可啟動</h3><ul>{red}</ul>
<p class="mut">同意閘(VIA_NET_CONSENT / VIA_SCRAPE_CONSENT)是操作員的手:本頁與 ActivateVDF 不讀值、不寫;閘關 = GATED(不是壞掉)。</p>
</body></html>"""


def write_report(card: dict, ui_dir: Path | None = None) -> dict:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ui_dir = ui_dir or (VIA / "VIA_Reports" / "vdf")
    stamp = card["stamp"]
    j = REPORT_DIR / f"ACTIVATE_VDF_{stamp}.json"
    j.write_text(json.dumps(card, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    (REPORT_DIR / "ACTIVATE_VDF_latest.json").write_text(j.read_text(encoding="utf-8"), encoding="utf-8")
    h = REPORT_DIR / "ACTIVATE_VDF_latest.html"
    h.write_text(render_html(card, ui_dir), encoding="utf-8")
    return {"json": str(j), "html": str(h)}


# ---------------------------------------------------------------- 主流程
def activate(opt, manager: Path | None = None, py: str | None = None, temp: Path | None = None) -> dict:
    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"=== {TAG} · VDF 獨立啟動 ===")
    res = optimize_resources(want=len(opt.flows) or 1, stamp=stamp, root=temp)
    p = res["plan"]
    print(f"  ① CPU/DRAM:核 {res['cpu']['usable']} · 可用 {res['mem']['avail_mb']}/{res['mem']['total_mb']} MB → "
          f"並行 {p['slots']} 條 · 每條 {p['threads_per_flow']} 執行緒 · DuckDB {p['duckdb_mem_mb']} MB · temp {res['temp_run']}")
    log_dir = Path(res["temp_run"]) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    gate = MemGate().start()
    try:
        lists = phase_lists(opt, res, gate, log_dir, manager, py)
        print(f"  ② 清單 {lists['lamp']}:{lists['note']}")
        flows = run_flows(opt, res, gate, log_dir, lists, manager, py)
        for f in flows:
            print(f"  ③ {FLOW_ZH[f['flow']]} → {f['lamp']}" + (f" · {f.get('note')}" if f.get("note") else ""))
        ui = phase_ui(opt, res, log_dir, manager, py) if not opt.no_ui else None
    finally:
        gate.close()
    card = {"schema": "VDF_ActivateVDF_v0100", "tag": TAG, "stamp": stamp, "ts": _dt.datetime.now().isoformat(timespec="seconds"),
            "manager": (manager or manager_path() or Path("—")).name, "mode": opt.mode, "dry": opt.dry,
            "resources": res, "memgate": gate.card(), "lists": lists, "flows": flows, "ui": ui,
            "consent_passthrough": {k: (k in os.environ) for k in CONSENT_KEYS}}
    card["lamp"] = overall(lists, flows)
    card["report"] = write_report(card)
    keep_logs = REPORT_DIR / "logs" / stamp
    try:
        shutil.copytree(log_dir, keep_logs, dirs_exist_ok=True)
        card["logs"] = str(keep_logs)
    except OSError:
        card["logs"] = str(log_dir)
    print(f"  [計] {TAG} · {card['lamp']} · 頁 {card['report']['html']}")
    if not opt.no_open:
        try:
            webbrowser.open(Path(card["report"]["html"]).resolve().as_uri())
        except Exception:  # noqa: BLE001 — 開不了瀏覽器不算失敗,頁照樣在
            pass
    return card


def parse(argv: list):
    ap = argparse.ArgumentParser(prog="ActivateVDF", description="VDF 獨立啟動:CPU/DRAM 最佳化 → 兩張清單 → 三條流程並行 → U/I")
    ap.add_argument("verb", nargs="?", default="run", choices=("run", "plan", "resources"))
    ap.add_argument("--mode", default="live", choices=("live", "fixture", "block"), help="擷取模式(live 要操作員開閘)")
    ap.add_argument("--dry", action="store_true", help="擷取只列計畫(不 --apply)")
    ap.add_argument("--fetch-home", default=None, help="擷取輸出根(預設照擷取冊 / VIA_VDF_FETCH_HOME)")
    ap.add_argument("--db-home", default=None, help="資料庫家(預設 --home > VIA_VDF_DB_HOME > 倉內 output_hub)")
    ap.add_argument("--flows", default="fetch,engines,db", help="要跑的流程(逗號分隔:fetch,engines,db)")
    ap.add_argument("--refill-apply", action="store_true", help="資料庫補不足真跑(要雙閘);預設只列計畫")
    ap.add_argument("--timeout", type=float, default=None, help="單步上限秒(預設不設;擷取各列有自己的上限)")
    ap.add_argument("--no-ui", action="store_true")
    ap.add_argument("--no-open", action="store_true")
    o = ap.parse_args(argv)
    o.flows = [f.strip() for f in o.flows.split(",") if f.strip() in FLOWS]
    return o


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--selftest"]:
        return selftest()
    opt = parse(argv)
    if opt.verb == "resources":
        res = optimize_resources(want=len(opt.flows) or 1)
        print(json.dumps(res, ensure_ascii=False, indent=1))
        return 0
    if opt.verb == "plan":
        first, rest, book = fetch_ids()
        res = optimize_resources(want=len(opt.flows) or 1)
        print(f"[{TAG} · 計畫] 管理員 {getattr(manager_path(), 'name', None)} · 擷取冊 {book}")
        print(f"  ① CPU/DRAM → 並行 {res['plan']['slots']} 條 · {' · '.join(res['plan']['why'])}")
        print(f"  ② 清單 {first}(fetch run → fetch verify)")
        print(f"  ③ 流程 {opt.flows}:擷取 {len(rest)} 列 · engine launch 全部 · db check → refill")
        print("  ④ ui → VIA_Reports/vdf/VDF_UI_latest.html · 總覽 VIA_Reports/vdf/activate/ACTIVATE_VDF_latest.html")
        return 0
    card = activate(opt)
    return {"GREEN": 0, "YELLOW": 2}.get(card["lamp"], 1)


# ---------------------------------------------------------------- 自測(沙盒 · 零網路 · 不碰倉內真庫)
_FAKE_MANAGER = r'''
import json, os, sys, time
from pathlib import Path
args = sys.argv[1:]
log = Path(os.environ["ACT_FAKE_LOG"])
with open(log, "a", encoding="utf-8") as fh:
    fh.write(json.dumps({"args": args, "t0": time.time(), "thr": os.environ.get("OMP_NUM_THREADS"),
                         "tmp": os.environ.get("TMPDIR"), "vdfsm": os.environ.get("VIA_FROM_VDFSM"),
                         "consent": os.environ.get("VIA_NET_CONSENT")}) + "\n")
if args[:2] == ["engine", "list"]:
    print(json.dumps({"engines": [{"eid": "ENG001"}, {"eid": "MDL009"}]}))
    sys.exit(0)
time.sleep(float(os.environ.get("ACT_FAKE_SLEEP", "0.6")))
if args[:2] == ["fetch", "run"]:
    gated = os.environ.get("ACT_FAKE_GATED") == "1"
    print("[GATED] fake" if gated else "[計] fake run OK")
    sys.exit(4 if gated else 0)
if args[:2] == ["fetch", "verify"]:
    ok = os.environ.get("ACT_FAKE_LISTS", "1") == "1"
    print("[驗收] 輸出 4/4" if ok else "[驗收] 缺")
    sys.exit(0 if ok else 1)
print("[計] fake " + " ".join(args[:2]))
sys.exit(0)
'''


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {TAG} · 自測(沙盒 · 假管理員 · 零網路)===")
    big = plan_slots({"usable": 8, "logical": 8, "load1": 1.0}, {"avail_mb": 14000, "total_mb": 16000})
    low = plan_slots({"usable": 8, "logical": 8, "load1": 0.5}, {"avail_mb": 2500, "total_mb": 4000})
    one = plan_slots({"usable": 1, "logical": 1, "load1": None}, {"avail_mb": None, "total_mb": None})
    chk("① CPU/DRAM 計畫:資源夠 = 3 條;記憶體緊 = 1 條且開溢寫;單核 / 量不到 = 1 條(照順序,不放棄)",
        big["slots"] == 3 and low["slots"] == 1 and low["spill"] and one["slots"] == 1 and big["threads_per_flow"] == 2,
        (big["slots"], low["slots"], one["slots"]))
    m = mem_info()
    c = cpu_info()
    chk("② 量測誠實:核數 ≥ 1;記憶體有值就 0 < 可用 ≤ 總量,量不到 = None(不猜)", c["logical"] >= 1 and (
        m["avail_mb"] is None or 0 < m["avail_mb"] <= m["total_mb"]), (c, m["how"]))
    with tempfile.TemporaryDirectory(prefix="activatevdf_") as td:
        t = Path(td)
        base = t / "ActivateVDF"
        for i in range(7):
            (base / f"run_20261015_10000{i}").mkdir(parents=True)
        (base / "keep_me").mkdir()
        gone = purge_runs(base, keep=5)
        chk("③ temp 滾動:只清本工具的輪夾、留最近 5 輪;別的夾不碰;不是 ActivateVDF 夾一律不清",
            len(gone) == 2 and (base / "keep_me").is_dir() and purge_runs(t, keep=0) == [], gone)
        res = optimize_resources(want=3, stamp="20261015_120000", root=t)
        keep_c = {k: os.environ.get(k) for k in CONSENT_KEYS}
        env = flow_env(res, "fetch", base_env={CONSENT_KEYS[0]: "sentinel-untouched", "PATH": os.environ.get("PATH", "")})
        chk("④ 子行程環境:執行緒上限 · temp 指本輪夾 · DuckDB 上限 · VDF 總控標記;同意閘原樣傳(不改值)、本行程環境不動",
            env["OMP_NUM_THREADS"] == str(res["plan"]["threads_per_flow"]) and env["TMPDIR"].startswith(res["temp_run"])
            and env["VIA_DUCKDB_MEM"].endswith("MB") and env["VIA_FROM_VDFSM"] == "YES" and env[CONSENT_KEYS[0]] == "sentinel-untouched"
            and "VIA_SCRAPE_CONSENT" not in env and {k: os.environ.get(k) for k in CONSENT_KEYS} == keep_c)
        mgr = t / "mgr" / "VDF_SystemManager_v9999.py"
        mgr.parent.mkdir()
        mgr.write_text(_FAKE_MANAGER, encoding="utf-8")
        flog = t / "calls.jsonl"
        os.environ["ACT_FAKE_LOG"] = str(flog)
        saved_env = {k: os.environ.get(k) for k in ("ACT_FAKE_SLEEP", "ACT_FAKE_GATED", "ACT_FAKE_LISTS")}
        try:
            opt = parse(["run", "--no-open", "--no-ui"])
            res3 = dict(res, plan=dict(res["plan"], slots=3))
            gate = MemGate(reader=lambda: {"avail_mb": 9000, "total_mb": 16000}, interval=0.05).start()
            logs = t / "logs"
            logs.mkdir()
            lists = phase_lists(opt, res3, gate, logs, mgr)
            t_lists = time.time()
            flows = run_flows(opt, res3, gate, logs, lists, mgr)
            gate.close()
            calls = [json.loads(x) for x in flog.read_text(encoding="utf-8").splitlines()]
            first_flow = min(cl["t0"] for cl in calls if cl["args"][:1] in (["engine"], ["db"], ["refill"])
                             or cl["args"][:2] == ["fetch", "run"] and len(cl["args"]) > 2 and cl["args"][2] not in ("009", "010"))
            chk("⑤ 先清單後流程:兩張清單(009 · 010)跑完驗收過,三條流程才起跑", lists["lists_ready"] and lists["lamp"] == "GREEN"
                and first_flow >= t_lists - 0.05 and [r["args"][2] for r in lists["runs"]] == ["009", "010"])
            spans = sorted((f["t0"], f["t1"]) for f in flows)
            overlap = spans[1][0] < spans[0][1] and spans[2][0] < spans[0][1]
            chk("⑥ 三條流程同時跑(slots 3:起跑時間互相重疊);每條都 GREEN", overlap and all(f["lamp"] == "GREEN" for f in flows),
                [f["lamp"] for f in flows])
            chk("⑦ 子行程拿到流程環境(VDF 總控標記 · 執行緒上限 · 本輪 temp);同意閘照本視窗原樣(沒設就沒有)",
                all(cl["vdfsm"] == "YES" and cl["thr"] and cl["tmp"] for cl in calls)
                and all(cl["consent"] == os.environ.get("VIA_NET_CONSENT") for cl in calls))
            flog.write_text("", encoding="utf-8")
            res1 = dict(res, plan=dict(res["plan"], slots=1))
            os.environ["ACT_FAKE_SLEEP"] = "0.2"
            g1 = MemGate(reader=lambda: {"avail_mb": 9000, "total_mb": 16000}, interval=0.05).start()
            f1 = run_flows(opt, res1, g1, logs, lists, mgr)
            g1.close()
            s1 = sorted((f["t0"], f["t1"]) for f in f1)
            chk("⑧ 資源只夠 1 條 → 三條照順序跑(不重疊、不放棄)", all(s1[i + 1][0] >= s1[i][1] - 0.01 for i in range(2)))
            os.environ["ACT_FAKE_GATED"], os.environ["ACT_FAKE_LISTS"] = "1", "0"
            g2 = MemGate(reader=lambda: {"avail_mb": 9000, "total_mb": 16000}, interval=0.05).start()
            l2 = phase_lists(opt, res3, g2, logs, mgr)
            f2 = {f["flow"]: f for f in run_flows(opt, res3, g2, logs, l2, mgr)}
            g2.close()
            chk("⑨ 閘關又沒既有清單 → 清單 GATED · 擷取流程 BLOCKED(不硬跑);引擎 / 資料庫兩條照跑",
                l2["lamp"] == "GATED" and f2["fetch"]["lamp"] == "BLOCKED" and f2["engines"]["lamp"] == "GREEN"
                and f2["db"]["lamp"] == "GREEN" and overall(l2, list(f2.values())) == "YELLOW")
            os.environ["ACT_FAKE_LISTS"] = "1"
            g3 = MemGate(reader=lambda: {"avail_mb": 9000, "total_mb": 16000}, interval=0.05).start()
            l3 = phase_lists(opt, res3, g3, logs, mgr)
            g3.close()
            chk("⑩ 閘關但既有清單驗收過 → 照用既有清單(YELLOW,擷取流程放行)", l3["lamp"] == "YELLOW" and l3["lists_ready"])
        finally:
            for k, v in saved_env.items():
                (os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v))
            os.environ.pop("ACT_FAKE_LOG", None)
        state = {"m": {"avail_mb": 100, "total_mb": 16000}}
        mg = MemGate(reader=lambda: state["m"], interval=0.05).start()
        threading.Timer(0.3, lambda: state.update(m={"avail_mb": 9000, "total_mb": 16000})).start()
        w = mg.wait("probe", max_wait=5)
        mg.close()
        chk("⑪ 記憶體壓力閘:可用過低時新步驟先等,壓力解除才放行(有記等待)", 0.2 <= w < 5 and mg.card()["waits"], round(w, 2))
        card = {"tag": TAG, "ts": "t", "stamp": "x", "manager": "VDF_SystemManager_v9999.py", "lamp": "YELLOW",
                "resources": res, "memgate": {"min_avail_mb": 1, "waits": []}, "lists": l2, "flows": list(f2.values())}
        page = render_html(card, t / "nope")
        chk("⑫ 總覽頁:燈 · CPU/DRAM 卡 · 清單卡 · 三流程每步一列 · 連 VDF 操作頁(沒產生照實寫)· 深色模式",
            "VDF 啟動總覽" in page and "BLOCKED" in page and "VDF 操作頁" in page and "還沒產生" in page
            and "prefers-color-scheme:dark" in page and page.count("<tr>") >= 5)
    src = Path(__file__).read_text(encoding="utf-8")
    imports = re.findall(r"^\s*(?:import|from)\s+([A-Za-z_][\w.]*)", src, re.M)
    chk("⑬ VDF 獨立:不匯入他系統程式(CGC_ · VRN_ · VCGC);只起 VDF 自己的管理員尾版",
        not [x for x in imports if x.startswith(("CGC_", "VRN_", "VIA_VRN", "VCGC"))] and MANAGER_GLOB.startswith("VDF_SystemManager"))
    chk("⑭ 加速器橋 · 網路橋在;不碰 TA-Lib;同意閘不寫(只原樣傳)",
        "VIA:ACCEL-BRIDGE" in src and "VIA:NET-BRIDGE" in src and "def _via_net" in src
        and not re.search(r"^\s*(import|from)\s+" + "talib", src, re.M)
        and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_" + "CONSENT[\"']\\]\\s*=(?!=)", src)
        and not re.search(r"\[[\"']VIA_(NET|SCRAPE)_" + "CONSENT[\"']\\]\\s*=(?!=)", src))
    n = sum(ok)
    print(f"  [計] {TAG} {n}/{len(ok)} · {'PASS' if n == len(ok) else 'FAIL'}")
    return 0 if n == len(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
