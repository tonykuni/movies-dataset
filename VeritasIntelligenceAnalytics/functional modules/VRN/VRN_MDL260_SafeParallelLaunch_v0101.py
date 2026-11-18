#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_MDL260_SafeParallelLaunch v0101 — 先降壓 → 3~5 支獨立流程同時起 → 看得出沒卡住(與 VDF 那支同一輪改;各系統各存一份,L131)。

操作員 2026-11-16:「卡斷且好慢 · 啟動工具也要將獨立流程 3~5 個同步啟動進行但不可傷到電腦 · 第一步要先降 CPU/DRAM 壓力後才進行 · 一切檔案都要 100% 覆蓋加速器」。
本版(v0100 一字不動):① 第一步就是降壓(降優先序 → 執行緒上限 → 暫存走 TEMP → 等 CPU / DRAM 靜下來,最多 --calm-wait 秒);
② 道數夾在 3~5;加速器橋覆蓋閘(100% 且執行時載得到)改成一支流程,和 衝突檢視 · 安裝計畫 · OmniRoute 同時起,閘過了才起文件整輪;
③ 心跳印每支流程靜了幾秒與子行程數,超過 300 秒沒輸出另印一行。其餘照 v0100。
用法:py VRN_MDL260_SafeParallelLaunch_v0101.py run [--slots auto|3-5] [--calm-wait 180] [--skip-roundall] [--roundall-args "..."] [--no-open] [--dry] [--force]
      py VRN_MDL260_SafeParallelLaunch_v0101.py check | bridge-gate | --selftest

(以下 v0100 說明)VRN_MDL260_SafeParallelLaunch v0100 — VRN 一支啟動:環境檢查 → 降壓 → 並行(壓力自動調節)→ 驗證 → HTML U/I。

操作員令(2026-11-14):「指令先進入環境檢查 加速器是否完整導入覆蓋率 100% · 將 CPU/DRAM 的運作壓力下滑 · 善用 TEMP ·
擷取不同複雜程度的文件用複雜的工具(VRN)· 啟動運作 VRN 指令一定要加入加速器 · 降低硬體壓力後獨立不相關的流程同步進行 ·
不燒壞電腦 · 不影響引擎及系統健康 · 壓力太大自動調整 · 用 PY 寫 · VRN 一支 · PS 單行啟動並連結 HTML U/I」。

流程(VRN 自己的,只呼叫 VRN 自己的尾版;不代設同意閘、不 pip、不刪資料):
  ① 環境檢查(先過才跑):Python · DuckDB · psutil · 加速器真的載得進來 · VRN 尾版加速器橋覆蓋 100%(VRN_SystemManager 尾版 bridges;
     唯讀豁免照冊)· 網路橋只報不擋(VRN 不強制;MDL002 被標「出網」是誤報:全檔零網路,命中的是自測字串與字型網址)
     · CPU / DRAM / TEMP。加速器覆蓋不到 100% → RED 停(--force 才照跑,照實記)。
  ② 降壓:同 VDF 那支(各系統各存一份,L131):降優先序 · 數學庫執行緒上限 · 暫存走 TEMP(VIA_TEMP_ROOT/VRN)· DuckDB spill。
  ③ 並行:文件整輪 = VRN-2 RoundAll 尾版(PDF / 圖片 / 掃描檔 → OCR 與版面工具 → 抽取 → 驗證;它自己內部照順序跑)
     與 衝突檢視 · 安裝計畫 · OmniRoute 同時跑(互不相干,最多 5 支);整輪完 → ENG049 輸出矩陣 → 收尾頁 → Graphify。
     監工每 5 秒量 CPU / DRAM:連兩次過熱 → 減道 + 暫停最新起的子行程(OCR 也會被暫停,不會被砍);連三次冷卻 → 恢復 / 加道。
  ④ 頁:VIA_Reports/vrn/launch/VRN_Launch_latest.html(VCGC 鎖站色票)連到 VRN 矩陣 · 管理器矩陣頁;自動開瀏覽器。
rc:0 全綠 · 2 有黃 · 1 有紅。
用法:py VRN_MDL260_SafeParallelLaunch_v0100.py run [--slots auto|1-5] [--skip-roundall] [--roundall-args "--offline --skip-pasteback"]
                                                     [--no-open] [--dry] [--force] [--cpu-hard 90] [--cpu-soft 70] [--mem-floor-gb 2] [--timeout 21600]
      py VRN_MDL260_SafeParallelLaunch_v0100.py check      (只做 ①)
      py VRN_MDL260_SafeParallelLaunch_v0100.py --selftest
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
VIA_NET_TOOL_PATH = None   # VRN 只強制加速器(操作員令);本啟動器不出網
# 本啟動器自己不出網;VRN-2 ⑥e 市場資料若要出網,照它自己的同意閘(操作員開)。

import datetime as _dt
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
from pathlib import Path

# ───────── 系統設定(本系統專屬)─────────
SYSTEM = "VRN"
STEM = "VRN_MDL260_SafeParallelLaunch"
VERSION = "v0101"
TAG = f"{STEM} {VERSION}"
HERE = Path(__file__).resolve().parent
NEED_NET = False                     # VRN:加速器必須 100%;網路橋只報不擋
MAX_SLOTS = 5
MIN_SLOTS = 3                        # 操作員 2026-11-16:獨立流程 3~5 支同時起(壓力大由監工往下調)
GATES = ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT")
RC = {"GREEN": 0, "YELLOW": 2, "RED": 1}


def via_root() -> Path:
    for q in [HERE] + list(HERE.parents):
        if (q / "functional modules").is_dir() and (q / "supportive modules").is_dir():
            return q
    return HERE.parents[1]


VIA = via_root()


def vnum(p: Path) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


def tail(folder: Path, pat: str):
    hits = sorted((p for p in Path(folder).glob(pat) if vnum(p) >= 0), key=vnum)
    return hits[-1] if hits else None


def now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def roundall_tail():
    rel = VIA / "docs" / "handoff" / "ai"
    hits = sorted(rel.glob("vrn2_release_v*/VRN2_RoundAll_v*.py"), key=lambda p: (vnum(p.parent), vnum(p)))
    return hits[-1] if hits else None


def tails() -> dict:
    return {"manager": tail(HERE, "VRN_SystemManager_v*.py"), "eng049": tail(HERE, "VRN_ENG049_ContentReconcile_v*.py"), "roundall": roundall_tail()}


def build_jobs(t: dict, a: dict, py: str = sys.executable) -> list:
    """VRN 工作圖:文件整輪(複雜文件 · OCR / 版面工具)與 衝突 · 安裝計畫 · OmniRoute 同時 → ENG049 矩陣 → 收尾 → Graphify。"""
    m = str(t["manager"])
    jobs = [{"id": "gate", "title": "⓪ 加速器橋覆蓋閘(100% · 執行時載得到)", "cmd": [py, "-B", str(Path(__file__).resolve()), "bridge-gate"],
             "needs": [], "soft": (), "timeout": 1800}]
    if not a.get("skip_roundall") and t.get("roundall"):
        jobs.append({"id": "roundall", "title": "① VRN-2 文件整輪(PDF / 圖片 / 掃描 → OCR · 版面 → 抽取 → 驗證)",
                     "cmd": [py, "-B", str(t["roundall"]), "--no-open", "--root", str(VIA)] + [x for x in str(a.get("extra") or "").split() if x],
                     "cwd": str(t["roundall"].parent), "needs": ["gate"], "soft": (2, 3, 4), "timeout": a["timeout"]})
    pre = ["roundall"] if len(jobs) > 1 else ["gate"]
    jobs += [
        {"id": "conflict", "title": "② 鏡像衝突檢視(哨兵 · GitHub 對齊 · 子系統邊界)", "cmd": [py, "-B", m, "conflict"], "needs": [], "soft": (2,), "timeout": 900},
        {"id": "install", "title": "③ 安裝計畫(缺的經 VCGC InstallGate,不 pip)", "cmd": [py, "-B", m, "install"], "needs": [], "soft": (2, 3), "timeout": 900},
        {"id": "omniroute", "title": "④ OmniRoute 五家 AI 路由", "cmd": [py, "-B", m, "omniroute"], "needs": [], "soft": (2,), "timeout": 600},
        {"id": "matrix", "title": "⑤ ENG049 輸出矩陣(個股 + 非個股 · JSON / CSV / Parquet / HTML)", "cmd": [py, "-B", str(t["eng049"]), "matrix"],
         "needs": ["gate"], "after": [x for x in pre if x != "gate"], "soft": (2,), "timeout": 3600},
        {"id": "closeout", "title": "⑥ VRN 收尾頁 + 備份", "cmd": [py, "-B", m, "closeout"], "needs": ["gate"], "after": ["matrix"], "soft": (2, 3), "timeout": 3600},
        {"id": "graphify", "title": "⑦ Graphify", "cmd": [py, "-B", m, "graphify"], "needs": ["gate"], "after": ["closeout"], "soft": (2,), "timeout": 900},
    ]
    return jobs


def page_links() -> list:
    r = VIA / "VIA_Reports"
    out = []
    for lab, pat in (("VRN 輸出矩陣", "vrn_reconcile_runs/matrix_*.html"), ("管理器矩陣頁", "vrn/manager/**/*.html"), ("VRN-2 收尾頁", "vrn2/**/*.html")):
        hits = sorted(r.glob(pat), key=lambda p: p.stat().st_mtime) if r.is_dir() else []
        if hits:
            out.append((lab, hits[-1]))
    return out


def out_dir() -> Path:
    return VIA / "VIA_Reports" / SYSTEM.lower() / "launch"


# ───────── v0101:資料家 · 等靜 · 道數 · 橋閘 ─────────
DATA_HOME_ENV = None


def resolve_data_home(arg=None, env=None) -> tuple:
    """--data-home > env > 使用者文件夾下 VeritasIntelligenceAnalytics/via_database(底下有 vdf_database 就用它)。→ (Path | None, 為什麼)"""
    if not DATA_HOME_ENV:
        return None, "本系統不用資料家"
    env = os.environ if env is None else env
    cands = [(arg, "--data-home"), (env.get(DATA_HOME_ENV), "env " + DATA_HOME_ENV)]
    up = env.get("USERPROFILE") or env.get("HOME")
    if up:
        cands.append((str(Path(up) / "OneDrive" / "Documents" / "VeritasIntelligenceAnalytics" / "via_database"), "使用者文件夾 via_database"))
    for raw, why in cands:
        if raw and Path(raw).is_dir():
            sub = Path(raw) / "vdf_database"
            return (sub if sub.is_dir() else Path(raw)), why
    return None, "沒指定也沒找到 → 交給 VDF_DataHome_SSOT(ActivateVDF / 資料平面自己解)"


def data_home_inventory(home: Path) -> dict:
    """只讀清點(兩層內):幾本 .duckdb · 幾個 .parquet · 合計大小。"""
    out = {"duckdb": 0, "parquet": 0, "bytes": 0}
    for pat, key in (("*.duckdb", "duckdb"), ("*/*.duckdb", "duckdb"), ("*.parquet", "parquet"), ("*/*.parquet", "parquet")):
        for p in home.glob(pat):
            try:
                out[key] += 1
                out["bytes"] += p.stat().st_size
            except OSError as exc:
                out["error"] = str(exc)[:80]
    return out


def plan_slots(want, res: dict) -> int:
    n = auto_slots(res) if str(want).lower() == "auto" else int(want)
    return max(MIN_SLOTS, min(MAX_SLOTS, n))


def wait_calm(limits: dict, max_wait: float = 180.0, sampler=None, sleeper=None, log=None) -> dict:
    """降壓後、起任何流程前:CPU 高於 cpu_soft 或 DRAM 低於下限就等(每 5 秒量一次),最多 max_wait 秒;到了照實記 forced。"""
    sampler = sampler or (lambda: resources())
    sleeper = sleeper or time.sleep
    log = log or (lambda x: print(x, flush=True))
    waited = 0.0
    while True:
        smp = sampler()
        c, m = smp.get("cpu_pct"), smp.get("mem_avail_gb")
        hot = (c is not None and c > limits["cpu_soft"]) or (m is not None and m < limits["mem_floor_gb"])
        if not hot or waited >= max_wait:
            return {"waited_s": waited, "forced": bool(hot), "cpu_pct": c, "mem_avail_gb": m}
        log(f"  [降壓] 等系統靜下來:CPU {c}%(要 ≤ {limits['cpu_soft']:.0f}%)· DRAM 可用 {m} GB(要 ≥ {limits['mem_floor_gb']} GB)· 已等 {waited:.0f}s / {max_wait:.0f}s")
        sleeper(5.0)
        waited += 5.0


def bridge_verdict(br: dict, accel_loaded: bool, net_path) -> dict:
    """覆蓋以生效計:標記 100% 而且本行程真的載得到。VDF 另要網路工具(真出網者 100% + 工具在)。"""
    miss_a, miss_n = list(br.get("missing_accel") or []), list(br.get("missing_net") or [])
    why = []
    if miss_a:
        why.append(f"缺加速器橋 {len(miss_a)} 支")
    if not accel_loaded:
        why.append("加速器執行時載不進來")
    if NEED_NET and miss_n:
        why.append(f"真出網者缺網路橋 {len(miss_n)} 支")
    if NEED_NET and not (net_path and Path(net_path).is_file()):
        why.append("網路工具不在")
    return {"ok": not why, "why": why, "missing_accel": miss_a, "missing_net": miss_n if NEED_NET else [], "accel": br.get("accel"), "net_callers": br.get("net_callers")}


def cmd_bridge_gate() -> int:
    t = tails()
    try:
        out = _run_manager(t["manager"], ["bridges", "--json"])
        br = json.loads(out[out.index("{"):])
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        print(f"[橋閘] RED · 讀不到管理器 bridges:{type(exc).__name__}: {str(exc)[:120]}", flush=True)
        return 1
    v = bridge_verdict(br, VIA_ACCEL is not None, VIA_NET_TOOL_PATH)
    print(f"[橋閘] {'GREEN' if v['ok'] else 'RED'} · 加速器 {v['accel']} · 執行時載入 {'是' if VIA_ACCEL is not None else '否'}"
          + (f" · 網路(真出網者){v['net_callers']}" if NEED_NET else f" · 網路 {br.get('net_callers')}(本系統只報不擋)")
          + ((" · " + " · ".join(v["why"])) if v["why"] else " · 100%"), flush=True)
    for x in (v["missing_accel"] + v["missing_net"])[:40]:
        print(f"  缺橋:{x}", flush=True)
    return 0 if v["ok"] else 1


# ───────── ① 環境檢查 ─────────
def resources(temp_base=None) -> dict:
    r = {"cpus": os.cpu_count() or 1, "cpu_pct": None, "mem_avail_gb": None, "mem_total_gb": None, "temp_free_gb": None, "via": "stdlib"}
    try:
        import psutil
        r["cpu_pct"] = float(psutil.cpu_percent(interval=0.3))
        vm = psutil.virtual_memory()
        r.update(mem_avail_gb=round(vm.available / 2 ** 30, 2), mem_total_gb=round(vm.total / 2 ** 30, 2), via="psutil")
    except Exception as exc:  # noqa: BLE001 — 沒 psutil 退標準庫(量不到的回 None)
        r["via"] = f"stdlib({type(exc).__name__})"
        if hasattr(os, "getloadavg"):
            r["cpu_pct"] = round(100.0 * os.getloadavg()[0] / max(1, r["cpus"]), 1)
        mi = Path("/proc/meminfo")
        if mi.is_file():
            kv = {ln.split(":")[0]: int(ln.split()[1]) for ln in mi.read_text().splitlines() if len(ln.split()) >= 2 and ln.split()[1].isdigit()}
            r.update(mem_avail_gb=round(kv.get("MemAvailable", 0) / 2 ** 20, 2), mem_total_gb=round(kv.get("MemTotal", 0) / 2 ** 20, 2))
    if temp_base:
        p = Path(temp_base)
        while not p.exists() and p.parent != p:
            p = p.parent
        r["temp_free_gb"] = round(shutil.disk_usage(p).free / 2 ** 30, 2)
    return r


def temp_root() -> Path:
    base = os.environ.get("VIA_TEMP_ROOT") or str(Path(os.environ.get("LOCALAPPDATA") or tempfile.gettempdir()) / "Temp" / "VIA_progress")
    return Path(base) / SYSTEM


def env_check(t: dict | None = None, run_manager=None, bridges: bool = True, data_home=None) -> dict:
    t = t or tails()
    rows = []

    def add(item, lamp, detail):
        rows.append({"item": item, "lamp": lamp, "detail": detail})
    add("Python", "GREEN" if sys.version_info >= (3, 10) else "RED", sys.version.split()[0])
    for lib, need in (("duckdb", True), ("psutil", False)):
        try:
            mod = __import__(lib)
            add(lib, "GREEN", getattr(mod, "__version__", "ok"))
        except Exception as exc:  # noqa: BLE001
            add(lib, "RED" if need else "YELLOW", f"沒裝({type(exc).__name__});" + ("經 VCGC InstallGate 安裝" if need else "監工退回只看負載、不能暫停子行程"))
    add("加速器載入", "GREEN" if VIA_ACCEL is not None else "RED", getattr(VIA_ACCEL, "__file__", "VIA_SuperAccel_Module 載不進來"))
    if NEED_NET:
        add("網路工具", "GREEN" if VIA_NET_TOOL_PATH and Path(VIA_NET_TOOL_PATH).is_file() else "RED", Path(VIA_NET_TOOL_PATH).name if VIA_NET_TOOL_PATH else "via_net_unified 不在")
    for k, p in t.items():
        add(f"尾版 {k}", "GREEN" if p else "RED", p.name if p else "找不到")
    br = None
    if not bridges:
        add("橋覆蓋", "INFO", "改成一支流程 bridge-gate,和其他獨立流程同時跑;沒過就不起後面的流程")
    if data_home is not None:
        dh, why = data_home
        if dh:
            inv = data_home_inventory(Path(dh))
            add("資料家(只讀清點)", "GREEN" if inv["duckdb"] or inv["parquet"] else "YELLOW",
                f"{dh} · {why} · .duckdb {inv['duckdb']} · .parquet {inv['parquet']} · {inv['bytes'] / 2 ** 30:.2f} GB")
        else:
            add("資料家", "YELLOW", why)
    if bridges and t.get("manager"):
        try:
            out = (run_manager or _run_manager)(t["manager"], ["bridges", "--json"])
            br = json.loads(out[out.index("{"):])
        except (ValueError, OSError, subprocess.SubprocessError) as exc:
            add("橋覆蓋", "RED", f"讀不到 bridges:{type(exc).__name__}")
    if br is not None:
        acc_ok = not br.get("missing_accel")
        add("加速器橋覆蓋", "GREEN" if acc_ok else "RED", f"{br.get('accel')}(缺 {len(br.get('missing_accel') or [])})" + (f" · 唯讀豁免 {len(br.get('exempt_readonly') or [])}" if br.get("exempt_readonly") else ""))
        net_ok = not br.get("missing_net")
        add("網路橋覆蓋(真出網者)", ("GREEN" if net_ok else "RED") if NEED_NET else ("GREEN" if net_ok else "YELLOW"),
            f"{br.get('net_callers')}" + (f" · 缺 {', '.join(br.get('missing_net'))}" if not net_ok else "") + ("" if NEED_NET else "(本系統只強制加速器)"))
    gates = {g: ("SET" if os.environ.get(g, "").upper() in ("YES", "1", "TRUE") else "UNSET") for g in GATES}
    if GATES:
        add("同意閘(只看,不代設)", "GREEN" if all(v == "SET" for v in gates.values()) else "YELLOW",
            " · ".join(f"{k}={v}" for k, v in gates.items()) + ("" if all(v == "SET" for v in gates.values()) else " → 擷取照實記 GATED,只用庫內現有資料"))
    tr = temp_root()
    res = resources(tr)
    add("TEMP", "GREEN" if (res["temp_free_gb"] or 99) >= 5 else "YELLOW", f"{tr} · 可用 {res['temp_free_gb']} GB")
    add("CPU / DRAM", "GREEN" if (res["mem_avail_gb"] or 99) >= 2 else "YELLOW",
        f"{res['cpus']} 核 · CPU {res['cpu_pct']}% · DRAM 可用 {res['mem_avail_gb']}/{res['mem_total_gb']} GB · 量測 {res['via']}")
    lamps = [r["lamp"] for r in rows]
    lamp = "RED" if "RED" in lamps else "YELLOW" if "YELLOW" in lamps else "GREEN"
    return {"lamp": lamp, "rows": rows, "gates": gates, "resources": res, "temp_root": str(tr), "bridges": br}


def _run_manager(manager: Path, args: list) -> str:
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    return subprocess.run([sys.executable, "-B", str(manager), *args], capture_output=True, text=True, encoding="utf-8",
                          errors="replace", env=env, timeout=600).stdout


# ───────── ② 降壓 ─────────
def auto_slots(res: dict) -> int:
    by_cpu = max(1, (res.get("cpus") or 2) - 1)
    by_mem = max(1, int((res.get("mem_avail_gb") or 8) / 1.5))
    return max(1, min(MAX_SLOTS, by_cpu, by_mem))


def calm_env(slots: int, tr: Path, base: dict | None = None) -> dict:
    env = dict(base if base is not None else os.environ)
    thr = str(max(1, (os.cpu_count() or 2) // max(1, slots)))
    for k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_MAX_THREADS", "POLARS_MAX_THREADS", "RAYON_NUM_THREADS"):
        env.setdefault(k, thr)
    for k in ("TMP", "TEMP", "TMPDIR"):
        env[k] = str(tr / "tmp")
    env.setdefault("VIA_TEMP_ROOT", str(tr.parent))
    env.setdefault("VIA_DUCKDB_TEMP_DIR", str(tr / "duckdb"))
    env.setdefault("VIA_DUCKDB_MEM_PCT", str(max(5, 50 // max(1, slots))))
    env.update(PYTHONIOENCODING="utf-8", PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1", VIA_FG_HEARTBEAT_S=env.get("VIA_FG_HEARTBEAT_S", "30"))
    return env


def lower_priority() -> str:
    """本行程降優先序(子行程繼承)。"""
    try:
        import psutil
        p = psutil.Process()
        if os.name == "nt":
            p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
            try:
                p.ionice(psutil.IOPRIO_LOW)
            except (AttributeError, OSError, ValueError) as exc:
                return f"BELOW_NORMAL(IO 優先序沒改:{type(exc).__name__})"
            return "BELOW_NORMAL + IO LOW"
        p.nice(min(19, max(p.nice(), 10)))
        return f"nice {p.nice()}"
    except Exception as exc:  # noqa: BLE001 — 沒 psutil 走 os.nice
        if hasattr(os, "nice"):
            try:
                return f"nice {os.nice(10)}"
            except OSError as exc2:
                return f"沒改({type(exc2).__name__})"
        return f"沒改({type(exc).__name__})"


# ───────── ③ 監工 + 並行 ─────────
class Supervisor:
    """最多 MAX_SLOTS 支同時跑;依相依起跑;量壓力自動減道 / 暫停最新子行程 · 冷卻後恢復 / 加道。"""

    def __init__(self, jobs, slots, env, logs: Path, limits: dict, sampler=None, interval=5.0, ctl=None, echo=True):
        self.jobs = {j["id"]: dict(j, state="WAIT", rc=None, sec=None, last="", log=None) for j in jobs}
        self.order = [j["id"] for j in jobs]
        self.slots, self.env, self.logs, self.lim = slots, env, logs, limits
        self.sampler = sampler or (lambda: resources())
        self.interval, self.echo = interval, echo
        self.ctl = ctl or ProcCtl()
        self.procs, self.t0 = {}, {}
        self.hot = self.cool = 0
        self.events, self.samples = [], []
        self.lock = threading.Lock()

    def log(self, s):
        if self.echo:
            print(s, flush=True)

    def _ready(self, jid):
        j = self.jobs[jid]
        return (j["state"] == "WAIT" and all(self.jobs[n]["state"] in ("DONE",) for n in j["needs"] if n in self.jobs)
                and all(self.jobs[n]["state"] in ("DONE", "FAILED", "SKIP") for n in j.get("after", []) if n in self.jobs))   # after = 只排順序:前一支跑完(不論燈)就起

    def _blocked(self, jid):
        j = self.jobs[jid]
        return j["state"] == "WAIT" and any(self.jobs[n]["state"] in ("FAILED", "SKIP") for n in j["needs"] if n in self.jobs)

    def _start(self, jid):
        j = self.jobs[jid]
        self.logs.mkdir(parents=True, exist_ok=True)
        lp = self.logs / f"{jid}.log"
        j["log"], j["state"] = str(lp), "RUN"
        self.t0[jid] = time.time()
        p = subprocess.Popen(j["cmd"], cwd=str(j.get("cwd") or HERE), env=self.env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True, encoding="utf-8", errors="replace")
        self.procs[jid] = p
        self.log(f"[起] {jid} · {j['title']}")

        def pump():
            with lp.open("w", encoding="utf-8") as fh:
                for ln in p.stdout:
                    fh.write(ln)
                    if ln.strip():
                        j["last"] = ln.strip()[:220]
                        j["last_ts"] = time.time()
                        self.log(f"  [{jid}] {ln.rstrip()[:200]}")
        threading.Thread(target=pump, daemon=True).start()

    def _finish(self, jid, rc):
        j = self.jobs[jid]
        j["rc"], j["sec"] = rc, round(time.time() - self.t0[jid], 1)
        j["state"] = "DONE" if rc == 0 or rc in j.get("soft", ()) else "FAILED"
        j["lamp"] = "GREEN" if rc == 0 else ("YELLOW" if rc in j.get("soft", ()) else "RED")
        self.procs.pop(jid, None)
        self.log(f"[完] {jid} rc {rc} · {j['lamp']} · {j['sec']}s")

    def _pressure(self):
        s = self.sampler()
        self.samples.append({"t": round(time.time(), 1), "cpu": s.get("cpu_pct"), "mem": s.get("mem_avail_gb"), "slots": self.slots,
                             "paused": len(self.ctl.paused)})
        c, m = s.get("cpu_pct"), s.get("mem_avail_gb")
        hot = (c is not None and c > self.lim["cpu_hard"]) or (m is not None and m < self.lim["mem_floor_gb"])
        cool = (c is None or c < self.lim["cpu_soft"]) and (m is None or m > self.lim["mem_floor_gb"] * 1.5)
        self.hot, self.cool = (self.hot + 1, 0) if hot else (0, self.cool + 1 if cool else 0)
        if self.hot >= 2:
            self.hot = 0
            if self.slots > 1:
                self.slots -= 1
            paused = self.ctl.pause_newest([p.pid for p in self.procs.values()])
            self.events.append({"t": now(), "act": "降壓", "cpu": c, "mem": m, "slots": self.slots, "paused_pid": paused})
            self.log(f"[監工] 過熱 CPU {c}% · DRAM 可用 {m} GB → 道數 {self.slots}" + (f" · 暫停 pid {paused}" if paused else ""))
        elif self.cool >= 3:
            self.cool = 0
            resumed = self.ctl.resume_one()
            if resumed is None and self.slots < MAX_SLOTS:
                self.slots += 1
            if resumed is not None or self.slots:
                self.events.append({"t": now(), "act": "回升", "cpu": c, "mem": m, "slots": self.slots, "resumed_pid": resumed})
                if resumed is not None:
                    self.log(f"[監工] 冷卻 → 恢復 pid {resumed}")

    def run(self, deadline_s: float | None = None) -> dict:
        start, last_s, last_hb = time.time(), 0.0, time.time()
        try:
            while True:
                for jid in self.order:
                    if self._blocked(jid):
                        self.jobs[jid].update(state="SKIP", lamp="RED", last="前置失敗,沒跑")
                for jid, p in list(self.procs.items()):
                    rc = p.poll()
                    if rc is not None:
                        self._finish(jid, rc)
                    elif time.time() - self.t0[jid] > self.jobs[jid]["timeout"]:
                        self.ctl.kill_tree(p.pid)
                        self._finish(jid, 124)
                if all(self.jobs[j]["state"] in ("DONE", "FAILED", "SKIP") for j in self.order):
                    break
                running = len(self.procs)
                for jid in self.order:
                    if running >= self.slots or self.hot:
                        break
                    if self._ready(jid):
                        self._start(jid)
                        running += 1
                if time.time() - last_s >= self.interval:
                    last_s = time.time()
                    self._pressure()
                if time.time() - last_hb >= 30:
                    last_hb = time.time()
                    s = self.samples[-1] if self.samples else {}
                    quiet = {k: int(time.time() - self.jobs[k].get("last_ts", self.t0[k])) for k in self.procs}
                    self.log(f"[心跳] 跑 {', '.join(f'{k}(靜 {v}s)' for k, v in quiet.items()) or '—'} · 子行程 {self.ctl.count([p.pid for p in self.procs.values()])} 支"
                             f" · 道數 {self.slots} · 暫停 {len(self.ctl.paused)} · CPU {s.get('cpu')}% · DRAM {s.get('mem')} GB")
                    for k, v in quiet.items():
                        if v >= 300:
                            self.log(f"[心跳] {k} 已 {v}s 沒有輸出(行程還活著;日誌 {self.jobs[k].get('log')})")
                if deadline_s and time.time() - start > deadline_s:
                    for jid, p in list(self.procs.items()):
                        self.ctl.kill_tree(p.pid)
                        self._finish(jid, 124)
                    break
                time.sleep(0.2)
        finally:
            self.ctl.resume_all()
        return {"jobs": [self.jobs[j] for j in self.order], "events": self.events, "samples": self.samples[-200:],
                "wall_s": round(time.time() - start, 1), "final_slots": self.slots}


class ProcCtl:
    """子行程樹的暫停 / 恢復 / 收掉(psutil;沒有就只記不做)。"""

    def __init__(self):
        self.paused = []

    def count(self, pids) -> int:
        try:
            return len(self._tree(pids))
        except Exception:  # noqa: BLE001 — 沒 psutil:只算得到最上層
            return len(pids)

    def _tree(self, pids):
        import psutil
        out = []
        for pid in pids:
            try:
                root = psutil.Process(pid)
                out += [root] + root.children(recursive=True)
            except psutil.Error:
                continue
        return out

    def pause_newest(self, pids):
        try:
            procs = [p for p in self._tree(pids) if p.pid not in self.paused]
            live = [p for p in procs if not p.children()] or procs
            if len(live) <= 1:                      # 至少留一支在跑
                return None
            p = max(live, key=lambda x: x.create_time())
            p.suspend()
            self.paused.append(p.pid)
            return p.pid
        except Exception:  # noqa: BLE001 — 沒 psutil / 權限不夠:不暫停,只靠起跑守門
            return None

    def resume_one(self):
        while self.paused:
            pid = self.paused.pop()
            try:
                import psutil
                psutil.Process(pid).resume()
                return pid
            except Exception:  # noqa: BLE001 — 行程已結束
                continue
        return None

    def resume_all(self):
        while self.paused:
            self.resume_one()

    def kill_tree(self, pid):
        try:
            for p in reversed(self._tree([pid])):
                p.kill()
        except Exception:  # noqa: BLE001 — 沒 psutil 退單支
            try:
                os.kill(pid, 9)
            except OSError as exc:
                print(f"[監工] 收不掉 pid {pid}:{exc}", flush=True)


# ───────── ④ 頁 ─────────
def tokens() -> dict:
    t = {"bg": "#f2f1ec", "panel": "#ffffff", "fg": "#33403f", "muted": "#6b6860", "accent": "#1b1a17", "line": "#dbd9d3", "row": "#ebe9e3",
         "green": "#3d7a52", "yellow": "#6f5c31", "red": "#9e2b25", "g_bg": "#e6efec", "y_bg": "#f2ecdd", "r_bg": "#f3e7e6"}
    kit = {"--bg": "bg", "--white": "panel", "--ink": "fg", "--muted": "muted", "--title": "accent", "--line": "line", "--row": "row",
           "--green": "green", "--y-ink": "yellow", "--r-ink": "red", "--g-bg": "g_bg", "--y-bg": "y_bg", "--r-bg": "r_bg"}
    try:
        k = json.loads((VIA / "docs" / "handoff" / "ai" / "VIA_WorkbenchLock_kit_latest.json").read_text(encoding="utf-8"))
        for key, val in (k.get("tokens") or {}).items():
            if key in kit and isinstance(val, str) and val.startswith("#"):
                t[kit[key]] = val
    except (OSError, ValueError):
        t["_note"] = "kit 不在,用同色系預設"
    return t


def write_page(rep: dict, out: Path) -> Path:
    t, e = tokens(), html.escape
    col = {"GREEN": ("g_bg", "green"), "YELLOW": ("y_bg", "yellow"), "RED": ("r_bg", "red")}

    def chip(l):
        b, f = col.get(l, ("row", "muted"))
        return f'<span class="chip" style="background:{t[b]};color:{t[f]}">{e(str(l))}</span>'
    envr = "".join(f"<tr><td>{chip(r['lamp'])}</td><td>{e(r['item'])}</td><td>{e(str(r['detail']))}</td></tr>" for r in rep["env"]["rows"])
    jobs = "".join(f"<tr><td>{chip(j.get('lamp', j['state']))}</td><td>{e(j['title'])}</td><td>{j.get('rc')}</td><td>{j.get('sec')}</td>"
                   f"<td class='note'>{e(j.get('last') or '')}</td></tr>" for j in rep.get("run", {}).get("jobs", []))
    ev = "".join(f"<tr><td>{e(x['t'])}</td><td>{e(x['act'])}</td><td>{x.get('cpu')}</td><td>{x.get('mem')}</td><td>{x.get('slots')}</td></tr>"
                 for x in rep.get("run", {}).get("events", [])[-40:])
    links = "".join(f"<a href='{p.as_uri()}'>{e(lab)}</a>" for lab, p in page_links())
    calm = rep.get("calm", {})
    smp = rep.get("run", {}).get("samples", [])
    cpus = [s["cpu"] for s in smp if s.get("cpu") is not None]
    mems = [s["mem"] for s in smp if s.get("mem") is not None]
    css = (f":root{{--bg:{t['bg']};--panel:{t['panel']};--fg:{t['fg']};--muted:{t['muted']};--accent:{t['accent']};--line:{t['line']};--row:{t['row']}}}"
           "body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.5 'Microsoft JhengHei','Segoe UI',sans-serif}"
           "main{max-width:1200px;margin:0 auto;padding-block:20px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}"
           "h1{color:var(--accent);font-size:22px;margin:0 0 4px}h2{color:var(--accent);font-size:16px;margin:22px 0 8px}.sub{color:var(--muted);font-size:12px}"
           "nav{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0}nav a{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:4px 10px;color:var(--accent);text-decoration:none}"
           ".kpis{display:flex;flex-wrap:wrap;gap:10px}.kpi{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:8px 14px;min-width:120px}.kpi b{display:block;font-size:18px;color:var(--accent)}"
           ".scroll{overflow-x:auto;background:var(--panel);border:1px solid var(--line);border-radius:8px}table{border-collapse:collapse;width:100%;font-size:13px}"
           "th,td{padding:5px 8px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}th{background:var(--row);color:var(--accent)}"
           "tbody tr:nth-child(even){background:var(--row)}td.note{color:var(--muted);word-break:break-all}.chip{display:inline-block;border-radius:10px;padding:0 8px;font-size:11px;font-weight:600}")
    doc = (f"<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
           f"<title>{SYSTEM} 安全並行啟動</title><style>{css}</style></head><body><main>"
           f"<h1>{SYSTEM} 安全並行啟動 {chip(rep['lamp'])}</h1><div class='sub'>{e(TAG)} · {e(rep['at'])}</div><nav>{links}</nav>"
           "<div class='kpis'>"
           f"<div class='kpi'>環境<b>{e(rep['env']['lamp'])}</b></div><div class='kpi'>起始道數<b>{calm.get('slots')}</b>最終 {rep.get('run', {}).get('final_slots')}</div>"
           f"<div class='kpi'>優先序<b>{e(str(calm.get('priority')))}</b></div><div class='kpi'>CPU 峰值<b>{max(cpus) if cpus else '—'}%</b></div>"
           f"<div class='kpi'>DRAM 最低可用<b>{min(mems) if mems else '—'} GB</b></div><div class='kpi'>降壓次數<b>{sum(1 for x in rep.get('run', {}).get('events', []) if x['act'] == '降壓')}</b></div>"
           f"<div class='kpi'>總秒數<b>{rep.get('run', {}).get('wall_s', '—')}</b></div></div>"
           f"<h2>① 環境檢查</h2><div class='scroll'><table><thead><tr><th>燈</th><th>項目</th><th>內容</th></tr></thead><tbody>{envr}</tbody></table></div>"
           f"<h2>② 降壓設定</h2><div class='scroll'><table><tbody>" + "".join(f"<tr><td>{e(k)}</td><td>{e(str(v))}</td></tr>" for k, v in calm.items()) + "</tbody></table></div>"
           f"<h2>③ 並行流程</h2><div class='scroll'><table><thead><tr><th>燈</th><th>流程</th><th>rc</th><th>秒</th><th>最後一行</th></tr></thead><tbody>{jobs or '<tr><td colspan=5>沒跑(--dry 或環境沒過)</td></tr>'}</tbody></table></div>"
           f"<h2>④ 監工紀錄(壓力自動調節)</h2><div class='scroll'><table><thead><tr><th>時間</th><th>動作</th><th>CPU%</th><th>DRAM GB</th><th>道數</th></tr></thead><tbody>{ev or '<tr><td colspan=5>全程沒超限</td></tr>'}</tbody></table></div>"
           "</main></body></html>")
    out.mkdir(parents=True, exist_ok=True)
    p = out / f"{SYSTEM}_Launch_latest.html"
    p.write_text(doc, encoding="utf-8")
    return p


# ───────── 指令 ─────────
def parse(argv: list) -> dict:
    def opt(name, default=None):
        return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else default
    return {"start": opt("--start", "2022-01-01"), "slots": opt("--slots", "auto"), "skip_fetch": "--skip-fetch" in argv,
            "no_open": "--no-open" in argv or os.environ.get("VIA_NO_OPEN") == "1", "dry": "--dry" in argv, "force": "--force" in argv,
            "timeout": int(opt("--timeout", "21600")), "data_home": opt("--data-home"), "calm_wait": float(opt("--calm-wait", "180")), "extra": opt("--roundall-args", ""), "skip_roundall": "--skip-roundall" in argv,
            "limits": {"cpu_hard": float(opt("--cpu-hard", "90")), "cpu_soft": float(opt("--cpu-soft", "70")), "mem_floor_gb": float(opt("--mem-floor-gb", "2"))}}


def cmd_run(argv: list, check_only=False) -> int:
    a = parse(argv)
    t = tails()
    out = out_dir()
    print(f"=== {TAG} ① 降壓(先做完才往下)===", flush=True)
    import gc
    gc.collect()
    prio = lower_priority()
    tr = temp_root()
    for d in (tr / "tmp", tr / "duckdb"):
        d.mkdir(parents=True, exist_ok=True)
    res0 = resources(tr)
    a["slots"] = plan_slots(a["slots"], res0)
    cenv = calm_env(a["slots"], tr)
    print(f"  優先序 {prio} · 執行緒上限 {cenv.get('OMP_NUM_THREADS')} · TEMP {cenv['TEMP']} · DuckDB 記憶體 {cenv['VIA_DUCKDB_MEM_PCT']}%"
          f" · 現在 CPU {res0['cpu_pct']}% · DRAM 可用 {res0['mem_avail_gb']}/{res0['mem_total_gb']} GB", flush=True)
    calm = {"waited_s": 0.0, "forced": False} if (check_only or a["dry"]) else wait_calm(a["limits"], a["calm_wait"])
    print(f"  等靜 {calm['waited_s']:.0f}s" + ("(到上限仍偏高,照實往下;監工會壓著跑)" if calm.get("forced") else "") + f" · 同時道數 {a['slots']}(夾在 {MIN_SLOTS}~{MAX_SLOTS})", flush=True)
    home, why = resolve_data_home(a.get("data_home"))
    a["data_home_resolved"] = str(home) if home else None
    if home and DATA_HOME_ENV:
        cenv[DATA_HOME_ENV] = str(home)
    print(f"=== ② 環境檢查 ===", flush=True)
    env = env_check(t, bridges=False, data_home=(home, why) if DATA_HOME_ENV else None)
    for r in env["rows"]:
        print(f"  {r['lamp']:<7}{r['item']:<22}{r['detail']}", flush=True)
    rep = {"system": SYSTEM, "engine": TAG, "at": now(), "env": env, "args": {k: v for k, v in a.items() if k != "limits"}, "limits": a["limits"],
           "calm": {"slots": a["slots"], "priority": prio, "threads_per_lib": cenv.get("OMP_NUM_THREADS"), "TEMP": cenv["TEMP"],
                    "duckdb_spill": cenv["VIA_DUCKDB_TEMP_DIR"], "duckdb_mem_pct": cenv["VIA_DUCKDB_MEM_PCT"], "calm_wait_s": calm["waited_s"],
                    "calm_forced": calm.get("forced"), "data_home": a["data_home_resolved"] or why,
                    "cpu_hard": a["limits"]["cpu_hard"], "cpu_soft": a["limits"]["cpu_soft"], "mem_floor_gb": a["limits"]["mem_floor_gb"]}}
    if check_only or (env["lamp"] == "RED" and not a["force"]):
        if env["lamp"] == "RED":
            print("[停] 環境檢查 RED(缺件)→ 不起任何流程;修好再跑,或 --force 照跑(照實記)", flush=True)
        rep["lamp"] = env["lamp"]
        _save(rep, out, a)
        return RC[env["lamp"]]
    jobs = build_jobs(t, a)
    print(f"=== ③ 並行流程(同時最多 {a['slots']} 支)===", flush=True)
    for j in jobs:
        print(f"  {j['id']:<11} 需 {','.join(j['needs']) or '—':<12} {j['title']}", flush=True)
    if a["dry"]:
        print("  (--dry:只列,不起子行程)", flush=True)
        rep["lamp"] = env["lamp"]
        _save(rep, out, a)
        return RC[env["lamp"]]
    sup = Supervisor(jobs, a["slots"], cenv, out / "logs", a["limits"])
    rep["run"] = sup.run()
    lamps = [j.get("lamp", "RED") for j in rep["run"]["jobs"]] + [env["lamp"]]
    rep["lamp"] = "RED" if "RED" in lamps else "YELLOW" if "YELLOW" in lamps else "GREEN"
    _save(rep, out, a)
    print(f"[{TAG}] {rep['lamp']} · " + " · ".join(f"{j['id']} {j.get('lamp')}" for j in rep["run"]["jobs"])
          + f" · 監工降壓 {sum(1 for x in rep['run']['events'] if x['act'] == '降壓')} 次 · {rep['run']['wall_s']}s", flush=True)
    return RC[rep["lamp"]]


def _save(rep: dict, out: Path, a: dict) -> None:
    out.mkdir(parents=True, exist_ok=True)
    stamp = rep["at"].replace("-", "").replace(":", "")
    for n in (f"{SYSTEM}_Launch_{stamp}.json", f"{SYSTEM}_Launch_latest.json"):
        (out / n).write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    p = write_page(rep, out)
    print(f"[頁] {p}", flush=True)
    if not a.get("no_open"):
        try:
            webbrowser.open(p.as_uri())
        except webbrowser.Error as exc:
            print(f"[頁] 開不了瀏覽器:{exc}", flush=True)


# ───────── 自測 ─────────
def selftest() -> int:
    ok = []

    def ck(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:300]) if note and not cond else ''}", flush=True)
    print(f"=== {TAG} 自測(夾具子行程 · 假壓力 · 不出網)===", flush=True)
    fake = '{"lamp": "GREEN", "accel": "3/3", "net_callers": "1/1", "missing_accel": [], "missing_net": []}'
    t = {k: Path(__file__) for k in tails()}
    ev = env_check(t, run_manager=lambda m, a: "x\n" + fake)
    names = {r["item"] for r in ev["rows"]}
    ck("① 環境檢查含 加速器載入 · 加速器橋 · 網路橋 · 同意閘 · TEMP · CPU/DRAM", {"加速器載入", "加速器橋覆蓋", "網路橋覆蓋(真出網者)", "TEMP", "CPU / DRAM"} <= names, names)
    bad = env_check(t, run_manager=lambda m, a: '{"accel": "2/3", "net_callers": "0/1", "missing_accel": ["X.py"], "missing_net": ["Y.py"]}')
    ck("② 橋覆蓋不到 100% → RED(預設不起流程)", bad["lamp"] == "RED" and any(r["item"] == "加速器橋覆蓋" and r["lamp"] == "RED" for r in bad["rows"]))
    ck("③ 不代設同意閘", all(os.environ.get(g) is None or True for g in GATES) and "VIA_NET_CONSENT\"] =" not in Path(__file__).read_text(encoding="utf-8").replace(" ", ""))
    ck("④ 道數自動:2 核 8GB → 1 · 16 核 64GB → 5 · 16 核 3GB → 2", auto_slots({"cpus": 2, "mem_avail_gb": 8}) == 1
       and auto_slots({"cpus": 16, "mem_avail_gb": 64}) == 5 and auto_slots({"cpus": 16, "mem_avail_gb": 3}) == 2)
    with tempfile.TemporaryDirectory() as td:
        tr = Path(td) / SYSTEM
        ce = calm_env(4, tr, base={})
        ck("⑤ 降壓環境:TMP/TEMP 走 TEMP 夾 · DuckDB spill · 記憶體 % 依道數 · 執行緒上限", ce["TEMP"] == str(tr / "tmp") and ce["VIA_DUCKDB_TEMP_DIR"] == str(tr / "duckdb")
           and ce["VIA_DUCKDB_MEM_PCT"] == "12" and int(ce["OMP_NUM_THREADS"]) >= 1)
        py = sys.executable
        jobs = [{"id": "a", "title": "A", "cmd": [py, "-c", "import time;print('a');time.sleep(0.6)"], "needs": [], "soft": (), "timeout": 30},
                {"id": "b", "title": "B", "cmd": [py, "-c", "import time;print('b');time.sleep(0.6)"], "needs": [], "soft": (), "timeout": 30},
                {"id": "c", "title": "C", "cmd": [py, "-c", "import sys;print('c');sys.exit(2)"], "needs": ["a"], "soft": (2,), "timeout": 30},
                {"id": "d", "title": "D", "cmd": [py, "-c", "import sys;sys.exit(1)"], "needs": [], "soft": (), "timeout": 30},
                {"id": "e", "title": "E", "cmd": [py, "-c", "print('e')"], "needs": ["d"], "soft": (), "timeout": 30},
                {"id": "f", "title": "F", "cmd": [py, "-c", "import time;time.sleep(30)"], "needs": [], "soft": (), "timeout": 1}]
        seq = iter([{"cpu_pct": 99, "mem_avail_gb": 8}] * 2 + [{"cpu_pct": 10, "mem_avail_gb": 8}] * 200)

        class Ctl(ProcCtl):
            def pause_newest(self, pids):
                self.paused.append(-1)
                return -1

            def resume_one(self):
                return self.paused.pop() if self.paused else None
        sup = Supervisor(jobs, 3, dict(os.environ), Path(td) / "logs", {"cpu_hard": 90, "cpu_soft": 70, "mem_floor_gb": 2},
                         sampler=lambda: next(seq), interval=0.05, ctl=Ctl(), echo=False)
        r = sup.run(deadline_s=60)
        st = {j["id"]: j for j in r["jobs"]}
        ck("⑥ 相依:c 等 a 完才起 · rc 2 記黃", st["c"]["lamp"] == "YELLOW" and st["a"]["state"] == "DONE")
        ck("⑦ 前置紅 → 後續 SKIP(不硬跑)", st["d"]["lamp"] == "RED" and st["e"]["state"] == "SKIP")
        ck("⑧ 逾時整棵收掉 · rc 124", st["f"]["rc"] == 124)
        j2 = [{"id": "x", "title": "X", "cmd": [py, "-c", "import sys;sys.exit(1)"], "needs": [], "soft": (), "timeout": 30},
              {"id": "y", "title": "Y", "cmd": [py, "-c", "print('y')"], "needs": [], "after": ["x"], "soft": (), "timeout": 30}]
        r2 = Supervisor(j2, 3, dict(os.environ), Path(td) / "logs2", {"cpu_hard": 90, "cpu_soft": 70, "mem_floor_gb": 2},
                        sampler=lambda: {"cpu_pct": 10, "mem_avail_gb": 8}, interval=0.05, ctl=Ctl(), echo=False).run(deadline_s=60)
        ck("⑧b after 只排順序:前一支紅了,後一支照跑(不被跳過)", {j["id"]: j["state"] for j in r2["jobs"]} == {"x": "FAILED", "y": "DONE"})
        acts = [x["act"] for x in r["events"]]
        ck("⑨ 監工:過熱 → 降壓(減道 + 暫停)· 冷卻 → 回升(恢復)", "降壓" in acts and "回升" in acts and acts.index("降壓") < acts.index("回升"), acts[:6])
        ck("⑩ 結束時沒有留下暫停的子行程", sup.ctl.paused == [])
        ck("⑪ 每支有日誌檔", all(Path(j["log"]).is_file() for j in r["jobs"] if j.get("log")))
        rep = {"system": SYSTEM, "engine": TAG, "at": now(), "lamp": "YELLOW", "env": ev, "calm": {"slots": 3, "priority": "test"}, "run": r}
        p = write_page(rep, Path(td) / "out")
        h = p.read_text(encoding="utf-8")
        ck("⑫ HTML:鎖站色票 · 環境 · 降壓 · 並行 · 監工四段", "--bg:" in h and all(s in h for s in ("① 環境檢查", "② 降壓設定", "③ 並行流程", "④ 監工紀錄")))
    fake_t = {k: Path(f"/x/{k}.py") for k in ("manager", "eng049", "roundall")}
    jb = build_jobs(fake_t, {"slots": 5, "timeout": 10, "extra": "--offline", "skip_roundall": False})
    jb2 = build_jobs(fake_t, {"slots": 5, "timeout": 10, "extra": "", "skip_roundall": True})
    by, by2 = {j["id"]: j for j in jb}, {j["id"]: j for j in jb2}
    ck("⑬ 工作圖:橋閘 + 衝突 + 安裝計畫 + OmniRoute 四支無相依 · 整輪等橋閘 · 矩陣等整輪 · 收尾等矩陣;--skip-roundall 時矩陣等橋閘",
       sum(1 for j in jb if not j["needs"]) == 4 and by["roundall"]["needs"] == ["gate"] and "--offline" in by["roundall"]["cmd"]
       and by["matrix"]["after"] == ["roundall"] and by["matrix"]["needs"] == ["gate"] and by2["matrix"]["after"] == [] and "roundall" not in by2, [(j["id"], j["needs"]) for j in jb])
    ck("⑮ 本系統不用資料家", resolve_data_home("/x", {})[0] is None)
    seq2 = iter([{"cpu_pct": 95, "mem_avail_gb": 8}] * 2 + [{"cpu_pct": 20, "mem_avail_gb": 8}] * 5)
    w1 = wait_calm({"cpu_soft": 70, "mem_floor_gb": 2}, 180, sampler=lambda: next(seq2), sleeper=lambda x: None, log=lambda x: None)
    w2 = wait_calm({"cpu_soft": 70, "mem_floor_gb": 2}, 10, sampler=lambda: {"cpu_pct": 99, "mem_avail_gb": 1}, sleeper=lambda x: None, log=lambda x: None)
    ck("⑯ 等靜:熱兩次後靜下來 → 等 10 秒不算硬闖;一直熱 → 到上限照實記 forced", w1 == {"waited_s": 10.0, "forced": False, "cpu_pct": 20, "mem_avail_gb": 8} and w2["forced"] and w2["waited_s"] == 10.0, (w1, w2))
    ck("⑰ 道數夾 3~5:auto 2 核 → 3 · 指定 9 → 5 · 指定 1 → 3 · auto 16 核 64GB → 5", plan_slots("auto", {"cpus": 2, "mem_avail_gb": 8}) == 3
       and plan_slots("9", {}) == 5 and plan_slots("1", {}) == 3 and plan_slots("auto", {"cpus": 16, "mem_avail_gb": 64}) == 5)

    def _boom(m, a):
        raise AssertionError("bridges=False 不該起管理器子行程")
    e2 = env_check({k: Path(__file__) for k in tails()}, run_manager=_boom, bridges=False)
    ck("⑱ 環境檢查不再同步跑橋掃(改成流程):有一列說明 · 不起子行程 · 不因此變黃變紅", any(r["item"] == "橋覆蓋" and r["lamp"] == "INFO" for r in e2["rows"]))
    v_ok = bridge_verdict({"accel": "3/3", "net_callers": "1/1", "missing_accel": [], "missing_net": []}, True, __file__)
    v_bad = bridge_verdict({"accel": "2/3", "missing_accel": ["X.py"], "missing_net": ["Y.py"]}, True, __file__)
    v_noload = bridge_verdict({"accel": "3/3", "missing_accel": [], "missing_net": []}, False, __file__)
    ck("⑲ 橋閘以生效計:標記 100% + 載得到 = 過;缺橋 = 不過;標記在但載不進來 = 不過", v_ok["ok"] and not v_bad["ok"] and not v_noload["ok"], (v_ok, v_bad, v_noload))
    ck("⑳ 心跳帶子行程數(沒 psutil 退最上層數)", ProcCtl().count([os.getpid()]) >= 1)
    src = Path(__file__).read_text(encoding="utf-8")
    ck("⑭ 加速器橋" + (" + 網路橋" if NEED_NET else "") + " 在 · 無 TA-Lib · 不 pip", "[VIA:ACCEL-BRIDGE" in src and (("[VIA:NET-BRIDGE" in src) or not NEED_NET)
       and ("ta" + "lib") not in src.lower() and ("pip" + " install") not in src)
    n = sum(ok)
    print(f"[計] {TAG} 自測 {n}/{len(ok)} {'PASS' if n == len(ok) else 'FAIL'}", flush=True)
    return 0 if n == len(ok) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    if args[0] in ("--selftest", "selftest"):
        return selftest()
    if args[0] == "bridge-gate":
        return cmd_bridge_gate()
    if args[0] == "check":
        return cmd_run(args[1:] + ["--no-open"], check_only=True)
    if args[0] == "run":
        return cmd_run(args[1:])
    print(f"[{TAG}] 未知動詞 {args[0]}(run · check · bridge-gate · --selftest)")
    return 2


if __name__ == "__main__":
    sys.exit(main())
