#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_MDL013_ActivateVDF v0101 — 薄尾:跑的時候看得到(心跳 · 每步完成一行)· Ctrl+C 收得乾淨(停整棵子行程樹 · 照寫總覽)

工作站實測(2026-10-16,8 核 · 可用 7.7 GB · 雙閘開):② 兩張清單 GREEN(本輪產出且驗收過);③ 三條流程起跑後
v0100 一行都不印(擷取冊 34 列、單列上限可到 4 小時),操作員看成「卡斷」按 Ctrl+C →
  ① 主執行緒 KeyboardInterrupt 直接丟 traceback,總覽沒寫(讀到的是更早那輪的舊 JSON);
  ② 子行程(管理員 → 引擎)沒被收,可能還在背景跑、還握著 DuckDB 檔鎖。
本版:
  · 心跳:每 VIA_ACT_HEARTBEAT_S 秒(預設 30)印一段「進行中」:每支在跑的步 · 已跑多久 · 它日誌的最後一行 · 可用記憶體;
    每步一結束就印一行「完成」(燈 · rc · 秒 · 摘要)。子行程帶 PYTHONUNBUFFERED=1,日誌即時落檔,心跳讀得到。
  · 中斷:任何階段(清單 / 三條流程 / U/I)按 Ctrl+C → 停止旗標 → 收掉整棵子行程樹(Windows taskkill /T /F;
    POSIX 整個行程組 SIGTERM → SIGKILL)→ 還沒起的步不再起(回 INTERRUPTED,零子行程)→ 照寫總覽,燈 INTERRUPTED、rc 130。
    子行程自成行程組,Ctrl+C 只到本行程,由本行程統一收,不會半套。
  · 資料庫寫入鎖(容器實測重現,3 次中 2 次):兩支清單引擎都寫同一個 vdf_master_lists.duckdb,v0100 讓它們同時跑 →
    `IO Error: Could not set lock on file ".../vdf_master_lists.duckdb": Conflicting lock is held`(DuckDB 一檔一次只准一個
    行程寫;工作站那輪 GREEN 是時機剛好錯開)。同一個病也在三流程之間:擷取與 db check / refill 碰同一批 DuckDB 檔。
    → 兩張清單改依序跑;資料庫流程等擷取流程寫完才起(也才量得到擷取後的庫);引擎流程(自測都在沙盒)照樣與擷取並行。
  · 其餘(CPU/DRAM · 三流程內容 · U/I · 總覽頁)全照 v0100(薄尾;前版不動)。
VDF 自己的模組:只起 VDF 管理員尾版,不匯入他系統程式;同意閘不讀不寫;不碰 TA-Lib。
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

import importlib.util
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import webbrowser
import datetime as _dt
from concurrent.futures import ThreadPoolExecutor, TimeoutError as _FutTimeout
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_MDL013_ActivateVDF"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def _vnum_v0101(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0101(p) < _vnum_v0101(__file__)), key=_vnum_v0101)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


HEARTBEAT_S = float(os.environ.get("VIA_ACT_HEARTBEAT_S") or 30)
STOP = threading.Event()                 # 中斷旗標:設了之後不再起新步
_LOCK = threading.RLock()                # 可重入:SIGINT 處理器在主執行緒持鎖時進來也不自鎖
RUNNING: dict = {}                       # 步名 → {t0, log, proc}
_HB = {"thread": None, "stop": threading.Event(), "out": None}


def _say(msg: str) -> None:
    out = _HB["out"] or sys.stdout
    try:
        print(msg, file=out, flush=True)
    except (OSError, ValueError):
        pass


def _last_line(log: Path) -> str:
    try:
        with open(log, "rb") as fh:
            fh.seek(0, 2)
            n = fh.tell()
            fh.seek(max(0, n - 4096))
            tail = fh.read().decode("utf-8", "replace")
    except OSError:
        return ""
    lines = [ln.strip() for ln in tail.splitlines() if ln.strip()]
    return lines[-1][:110] if lines else ""


def _fmt(secs: float) -> str:
    secs = int(secs)
    return f"{secs // 3600:d}:{secs % 3600 // 60:02d}:{secs % 60:02d}" if secs >= 3600 else f"{secs // 60:02d}:{secs % 60:02d}"


def heartbeat_once(now: float | None = None) -> str:
    """→ 一段「進行中」文字(沒有在跑的步 = 空字串)。"""
    now = now or time.time()
    with _LOCK:
        items = sorted(RUNNING.items(), key=lambda kv: kv[1]["t0"])
    if not items:
        return ""
    m = PRIOR.mem_info()
    avail = f"{m['avail_mb'] / 1024:.1f} GB" if m.get("avail_mb") else "—"
    head = f"  [進行中 {_dt.datetime.now():%H:%M:%S}] {len(items)} 步在跑 · 可用記憶體 {avail}"
    rows = [f"     · {name} {_fmt(now - r['t0'])} · {_last_line(r['log']) or '(還沒有輸出)'}" for name, r in items]
    return "\n".join([head] + rows)


def _hb_loop():
    while not _HB["stop"].wait(HEARTBEAT_S):
        txt = heartbeat_once()
        if txt:
            _say(txt)


def _hb_start():
    with _LOCK:
        if _HB["thread"] is None or not _HB["thread"].is_alive():
            _HB["stop"].clear()
            _HB["thread"] = threading.Thread(target=_hb_loop, daemon=True)
            _HB["thread"].start()


def _hb_stop():
    _HB["stop"].set()
    t = _HB["thread"]
    if t is not None:
        t.join(timeout=2)
    _HB["thread"] = None


def _kill_tree(p) -> None:
    """收掉整棵子行程樹:Windows taskkill /T /F;POSIX 整個行程組 SIGTERM → 3 秒後 SIGKILL。"""
    if p is None or p.poll() is not None:
        return
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True, timeout=30)
        else:
            os.killpg(p.pid, signal.SIGTERM)
            try:
                p.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(p.pid, signal.SIGKILL)
    except (OSError, subprocess.SubprocessError):
        try:
            p.kill()
        except OSError:
            pass


def interrupt(reason: str = "Ctrl+C") -> int:
    """設停止旗標並收掉所有在跑的子行程樹;回收掉幾支。"""
    STOP.set()
    with _LOCK:
        procs = [(n, r.get("proc")) for n, r in RUNNING.items()]
    for _, p in procs:
        _kill_tree(p)
    return len(procs)


def gate_wait(gate, who: str, max_wait: float = 600.0) -> float:
    """同 v0100 MemGate.wait(壓力時新步驟先等,最多 max_wait 秒),但每 0.5 秒看一次停止旗標:
    Ctrl+C 時卡在記憶體閘的步立刻放手(它還沒有子行程,interrupt() 收不到它)。PR #527 Codex P1。"""
    if gate is None:
        return 0.0
    t0 = time.time()
    if not gate.ok.is_set():
        while not gate.ok.wait(0.5):
            if STOP.is_set() or time.time() - t0 >= max_wait:
                break
        gate.waits.append({"who": who, "secs": round(time.time() - t0, 1)})
    return time.time() - t0


def _on_sigint(signum, frame):
    """Ctrl+C 一到就先收子行程樹、設停止旗標,再丟 KeyboardInterrupt:
    清單階段 v0100 的 with ThreadPoolExecutor 離開時會等 worker,worker 要看到停止旗標才會收手 —— 先設旗標才不會互等。"""
    interrupt()
    raise KeyboardInterrupt


def run_step(name: str, args: list, env: dict, log_dir: Path, gate=None,
             timeout: float | None = None, manager: Path | None = None, py: str | None = None) -> dict:
    """同 v0100 run_step(介面 · 回傳欄位相同),改 Popen:登記在跑 · 心跳讀日誌 · 停止旗標 · 整棵樹可收。"""
    mgr = manager or PRIOR.manager_path()
    rec = {"step": name, "args": args, "manager": mgr.name if mgr else None}
    if mgr is None:
        return dict(rec, rc=None, lamp="RED", secs=0, note=f"{PRIOR.MANAGER_GLOB} 不在 {HERE}")
    if STOP.is_set():
        return dict(rec, rc=None, lamp="INTERRUPTED", secs=0, note="已中斷:這一步沒起")
    waited = gate_wait(gate, name)
    if STOP.is_set():
        return dict(rec, rc=None, lamp="INTERRUPTED", secs=0, note="已中斷:這一步沒起")
    log = Path(log_dir) / (re.sub(r"[^A-Za-z0-9_.-]+", "_", name) + ".log")
    env = dict(env, PYTHONUNBUFFERED="1")
    kw = {"creationflags": getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)} if os.name == "nt" else {"start_new_session": True}
    t0 = time.time()
    note = ""
    with open(log, "w", encoding="utf-8", errors="replace") as fh:
        p = subprocess.Popen([py or sys.executable, str(mgr), *args], cwd=str(mgr.parent), env=env,
                             stdout=fh, stderr=subprocess.STDOUT, **kw)
        with _LOCK:
            RUNNING[name] = {"t0": t0, "log": log, "proc": p}
        _hb_start()
        try:
            while True:
                try:
                    p.wait(timeout=0.5)
                    break
                except subprocess.TimeoutExpired:
                    if STOP.is_set():
                        _kill_tree(p)
                        note = "已中斷:子行程樹已收"
                        break
                    if timeout and time.time() - t0 > timeout:
                        _kill_tree(p)
                        note = f"逾時 {timeout}s(子行程樹已收)"
                        break
        finally:
            with _LOCK:
                RUNNING.pop(name, None)
    if not note and STOP.is_set() and p.returncode not in (0, None):
        note = "已中斷:子行程樹已收"          # 別的執行緒先收掉了它(rc 是訊號值,不是引擎紅)
    rc = p.returncode if not note else None
    secs = round(time.time() - t0, 1)
    try:
        lines = [ln for ln in log.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()]
    except OSError:
        lines = []
    summ = next((ln.strip() for ln in reversed(lines) if "[計]" in ln or "GATED" in ln or "[驗收]" in ln), lines[-1].strip() if lines else "")
    lamp = "INTERRUPTED" if note.startswith("已中斷") else PRIOR.lamp_of(rc)
    _say(f"  [完成] {name} · {lamp} · rc {rc} · {secs}s · {summ[:120] or note}")
    return dict(rec, rc=rc, lamp=lamp, secs=secs, waited=round(waited, 1), log=str(log), summary=summ[:240], note=note)


def run_flows(opt, res, gate, log_dir, lists, manager=None, py=None) -> list:
    """同 v0100(三條獨立流程並行);主執行緒每 0.5 秒醒一次,Ctrl+C 立刻收,沒跑完的流程記 INTERRUPTED。"""
    jobs = {"fetch": lambda: flow_fetch(opt, res, gate, log_dir, lists, manager, py),
            "engines": lambda: PRIOR.flow_engines(opt, res, gate, log_dir, manager, py),
            "db": lambda: flow_db(opt, res, gate, log_dir, manager, py)}
    pick = [f for f in PRIOR.FLOWS if f in opt.flows]
    (FETCH_DONE.clear() if "fetch" in pick else FETCH_DONE.set())
    out = {}
    ex = ThreadPoolExecutor(max_workers=max(1, res["plan"]["slots"]))
    futs = {f: ex.submit(PRIOR._timed, f, jobs[f]) for f in pick}
    try:
        for f in pick:
            while True:
                try:
                    out[f] = futs[f].result(timeout=0.5)
                    break
                except _FutTimeout:
                    continue
                except Exception as exc:  # noqa: BLE001 — 一條流程炸了照記紅,不拖垮另兩條
                    out[f] = {"flow": f, "lamp": "RED", "steps": [], "note": f"{type(exc).__name__}: {exc}"}
                    break
    except KeyboardInterrupt:
        n = interrupt()
        _say(f"  [中斷] Ctrl+C:收掉 {n} 支在跑的子行程樹;還沒起的步不再起;照寫總覽")
        deadline = time.time() + 60             # 全部流程共用一個收尾期限(不是每條各等 60 秒)
        for f in pick:
            if f in out:
                continue
            try:
                out[f] = futs[f].result(timeout=max(0.1, deadline - time.time()))
            except Exception:  # noqa: BLE001 — 收尾中拿不到結果就照實記中斷
                out[f] = {"flow": f, "lamp": "INTERRUPTED", "steps": [], "note": "已中斷"}
            if out[f].get("lamp") not in ("RED",) and any(s.get("lamp") == "INTERRUPTED" for s in out[f].get("steps", [])):
                out[f]["lamp"] = "INTERRUPTED"
        ex.shutdown(wait=False, cancel_futures=True)
        return [out[f] for f in pick]
    ex.shutdown(wait=True)
    return [out[f] for f in pick]


FETCH_DONE = threading.Event()           # 擷取流程結束(或本輪沒有擷取流程)= 資料庫流程才可以開庫


def phase_lists(opt, res: dict, gate, log_dir: Path, manager=None, py=None) -> dict:
    """同 v0100,但兩張清單依序跑:兩支都寫 vdf_master_lists.duckdb,同時跑會撞 DuckDB 寫入鎖。"""
    first, _, book = PRIOR.fetch_ids()
    env = PRIOR.flow_env(res, "lists")
    runs = [run_step(f"lists_run_{i}", PRIOR.fetch_args("run", [i], opt), env, log_dir, gate, opt.timeout, manager, py)
            for i in first]
    ver = run_step("lists_verify", PRIOR.fetch_args("verify", first, opt), env, log_dir, gate, 600, manager, py)
    ok = ver["rc"] == 0
    if STOP.is_set():
        lamp = "INTERRUPTED"
    else:
        lamp = "GREEN" if ok and all(r["rc"] == 0 for r in runs) else ("YELLOW" if ok else
                                                                         "GATED" if any(r["rc"] == 4 for r in runs) else "RED")
    return {"ids": first, "book": book, "runs": runs, "verify": ver, "lists_ready": ok and lamp != "INTERRUPTED", "lamp": lamp,
            "note": ("兩張清單本輪產出且驗收過(依序跑,不撞寫入鎖)" if lamp == "GREEN" else
                     "清單階段被中斷(Ctrl+C);不算有清單" if lamp == "INTERRUPTED" else
                     "本輪沒重產,但既有清單驗收過 → 照用" if ok else
                     "同意閘沒開(操作員的手)且沒有既有清單 → 擷取流程停,其餘兩條照跑" if lamp == "GATED" else
                     "清單沒產出也沒有既有清單 → 擷取流程停,其餘兩條照跑")}


def flow_fetch(opt, res, gate, log_dir, lists: dict, manager=None, py=None) -> dict:
    try:
        return _FLOW_FETCH_V0100(opt, res, gate, log_dir, lists, manager, py)
    finally:
        FETCH_DONE.set()


def flow_db(opt, res, gate, log_dir, manager=None, py=None) -> dict:
    """同 v0100 資料庫流程,但等擷取流程寫完才開庫(同一批 DuckDB 檔一次只能一個行程寫;也才量得到擷取後的庫)。"""
    if not FETCH_DONE.is_set():
        _say("  [等候] 資料庫流程等擷取流程寫完才開庫(DuckDB 一檔一次只准一個行程寫)")
        while not FETCH_DONE.wait(0.5):
            if STOP.is_set():
                return {"flow": "db", "lamp": "INTERRUPTED", "steps": [], "note": "等擷取時被中斷"}
    return _FLOW_DB_V0100(opt, res, gate, log_dir, manager, py)


_FLOW_FETCH_V0100, _FLOW_DB_V0100 = PRIOR.flow_fetch, PRIOR.flow_db


def overall(lists: dict, flows: list) -> str:
    lamps = [lists.get("lamp")] + [f.get("lamp") for f in flows]
    if "INTERRUPTED" in lamps or STOP.is_set():
        return "INTERRUPTED"
    return _OVERALL_V0100(lists, flows)


_OVERALL_V0100 = PRIOR.overall
_LISTS_INTERRUPTED = {"lamp": "INTERRUPTED", "runs": [], "lists_ready": False, "ids": [], "book": None,
                      "verify": {"step": "lists_verify", "lamp": "INTERRUPTED", "rc": None, "secs": 0, "note": "已中斷"},
                      "note": "清單階段被中斷(Ctrl+C);沒驗收,不算有清單"}


def activate(opt, manager: Path | None = None, py: str | None = None, temp: Path | None = None) -> dict:
    """同 v0100 activate;任何階段 Ctrl+C → 收子行程樹 → 照寫總覽(燈 INTERRUPTED)。"""
    STOP.clear()
    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"=== {TAG} · VDF 獨立啟動 ===", flush=True)
    res = PRIOR.optimize_resources(want=len(opt.flows) or 1, stamp=stamp, root=temp)
    p = res["plan"]
    print(f"  ① CPU/DRAM:核 {res['cpu']['usable']} · 可用 {res['mem']['avail_mb']}/{res['mem']['total_mb']} MB → "
          f"並行 {p['slots']} 條 · 每條 {p['threads_per_flow']} 執行緒 · DuckDB {p['duckdb_mem_mb']} MB · temp {res['temp_run']}", flush=True)
    print(f"     心跳每 {int(HEARTBEAT_S)} 秒一段(VIA_ACT_HEARTBEAT_S 可改);Ctrl+C = 收掉子行程並照寫總覽", flush=True)
    log_dir = Path(res["temp_run"]) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    gate = PRIOR.MemGate().start()
    lists, flows, ui = dict(_LISTS_INTERRUPTED), [], None
    keep_sig = None
    if threading.current_thread() is threading.main_thread():
        keep_sig = signal.signal(signal.SIGINT, _on_sigint)
    try:
        lists = PRIOR.phase_lists(opt, res, gate, log_dir, manager, py)
        print(f"  ② 清單 {lists['lamp']}:{lists['note']}", flush=True)
        if not STOP.is_set():
            flows = run_flows(opt, res, gate, log_dir, lists, manager, py)
            for f in flows:
                print(f"  ③ {PRIOR.FLOW_ZH[f['flow']]} → {f['lamp']}" + (f" · {f.get('note')}" if f.get("note") else ""), flush=True)
        if not opt.no_ui and not STOP.is_set():
            ui = PRIOR.phase_ui(opt, res, log_dir, manager, py)
    except KeyboardInterrupt:
        n = interrupt()
        print(f"  [中斷] Ctrl+C:收掉 {n} 支在跑的子行程樹;照寫總覽", flush=True)
    finally:
        if keep_sig is not None:
            signal.signal(signal.SIGINT, keep_sig)
        gate.close()
        _hb_stop()
    card = {"schema": "VDF_ActivateVDF_v0101", "tag": TAG, "stamp": stamp, "ts": _dt.datetime.now().isoformat(timespec="seconds"),
            "manager": (manager or PRIOR.manager_path() or Path("—")).name, "mode": opt.mode, "dry": opt.dry,
            "resources": res, "memgate": gate.card(), "lists": lists, "flows": flows, "ui": ui,
            "interrupted": STOP.is_set(), "consent_passthrough": {k: (k in os.environ) for k in PRIOR.CONSENT_KEYS}}
    card["lamp"] = overall(lists, flows)
    card["report"] = PRIOR.write_report(card)
    keep_logs = PRIOR.REPORT_DIR / "logs" / stamp
    try:
        shutil.copytree(log_dir, keep_logs, dirs_exist_ok=True)
        card["logs"] = str(keep_logs)
    except OSError:
        card["logs"] = str(log_dir)
    print(f"  [計] {TAG} · {card['lamp']} · 頁 {card['report']['html']}", flush=True)
    if not opt.no_open and not card["interrupted"]:
        try:
            webbrowser.open(Path(card["report"]["html"]).resolve().as_uri())
        except Exception:  # noqa: BLE001 — 開不了瀏覽器不算失敗,頁照樣在
            pass
    return card


PRIOR.run_step, PRIOR.run_flows, PRIOR.overall, PRIOR.activate = run_step, run_flows, overall, activate
PRIOR.phase_lists, PRIOR.flow_fetch, PRIOR.flow_db = phase_lists, flow_fetch, flow_db   # 前版鏈的流程函式讀模組全域 → 換成本版
for _n in dir(PRIOR):
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = getattr(PRIOR, _n)


_SLOW_MANAGER = r"""
import os, sys, time
args = sys.argv[1:]
print("[步] 開始 " + " ".join(args[:2]), flush=True)
if args[:2] == ["engine", "list"]:
    print('{"engines": [{"eid": "ENG001", "family": "VDF_ENG001_X", "path": "functional modules/VDF/engine/VDF_ENG001_X_v0100.py"}]}')
    sys.exit(0)
if args[:2] == ["fetch", "verify"]:
    print("[驗收] 輸出 4/4"); sys.exit(0)
for i in range(int(float(os.environ.get("ACT_SLOW_S", "0.3")) * 10)):
    print(f"[步] 第 {i} 段", flush=True)
    time.sleep(0.1)
print("[計] slow done")
sys.exit(0)
"""


def selftest() -> int:
    import contextlib
    import io
    import json
    import tempfile
    global HEARTBEAT_S
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {TAG} · 薄尾自測(心跳 · 每步完成 · Ctrl+C 收乾淨;沙盒 · 假管理員 · 零網路)===")
    keep_hb, keep_report, keep_env = HEARTBEAT_S, PRIOR.REPORT_DIR, os.environ.get("ACT_SLOW_S")
    with tempfile.TemporaryDirectory(prefix="activatevdf101_") as td:
        t = Path(td)
        mgr = t / "mgr" / "VDF_SystemManager_v9999.py"
        mgr.parent.mkdir()
        mgr.write_text(_SLOW_MANAGER, encoding="utf-8")
        logs = t / "logs"
        logs.mkdir()
        res = PRIOR.optimize_resources(want=3, stamp="20261016_120000", root=t)
        env = PRIOR.flow_env(res, "fetch", base_env={"PATH": os.environ.get("PATH", "")})
        try:
            HEARTBEAT_S = 0.2
            os.environ["ACT_SLOW_S"] = "1.2"
            buf = io.StringIO()
            _HB["out"] = buf
            STOP.clear()
            r = run_step("slow_fetch", ["fetch", "run", "001u"], dict(env, ACT_SLOW_S="1.2"), logs, None, None, mgr)
            _hb_stop()
            out = buf.getvalue()
            chk("① 心跳:步在跑時每段印「進行中」+ 步名 + 已跑時間 + 它日誌最後一行(子行程不緩衝,即時讀得到)",
                out.count("[進行中") >= 2 and r["secs"] >= 1.0 and "slow_fetch" in out and "[步] 第" in out and "可用記憶體" in out, out.splitlines()[:3])
            chk("② 每步完成印一行(燈 · rc · 秒 · 摘要);回傳欄位同 v0100", "[完成] slow_fetch · GREEN · rc 0" in out
                and r["lamp"] == "GREEN" and r["summary"].startswith("[計] slow done")
                and set(("step", "args", "manager", "rc", "lamp", "secs", "waited", "log", "summary", "note")) <= set(r))
            os.environ["ACT_SLOW_S"] = "30"
            buf2 = io.StringIO()
            _HB["out"] = buf2
            STOP.clear()
            box = {}
            th = threading.Thread(target=lambda: box.update(r=run_step("long_step", ["fetch", "run", "x"], dict(env, ACT_SLOW_S="30"),
                                                                       logs, None, None, mgr)))
            t0 = time.time()
            th.start()
            time.sleep(0.8)
            pid = next(iter(RUNNING.values()))["proc"].pid if RUNNING else None
            n = interrupt()
            th.join(timeout=20)
            took = time.time() - t0
            alive = False
            if pid:
                try:
                    os.kill(pid, 0)
                    alive = os.name != "nt" and Path(f"/proc/{pid}").exists() and "zombie" not in Path(f"/proc/{pid}/status").read_text()
                except OSError:
                    alive = False
            r2 = box.get("r") or {}
            chk("③ 中斷:在跑的子行程樹被收(不留背景行程)· 步回 INTERRUPTED · 不用等它跑完 30 秒",
                n == 1 and r2.get("lamp") == "INTERRUPTED" and took < 15 and not alive, (n, r2.get("lamp"), round(took, 1), alive))
            r3 = run_step("after_stop", ["db", "check"], env, logs, None, None, mgr)
            chk("④ 中斷後還沒起的步不再起(零子行程,回 INTERRUPTED)", r3["lamp"] == "INTERRUPTED" and r3["secs"] == 0
                and not (logs / "after_stop.log").exists())
            STOP.clear()
            pressured = PRIOR.MemGate(reader=lambda: {"avail_mb": 100, "total_mb": 16000}, interval=0.05).start()
            box2 = {}
            t1 = time.time()
            th2 = threading.Thread(target=lambda: box2.update(r=run_step("mem_wait", ["db", "check"], env, logs, pressured, None, mgr)))
            th2.start()
            time.sleep(0.6)
            interrupt()
            th2.join(timeout=10)
            pressured.close()
            r4 = box2.get("r") or {}
            chk("④b 卡在記憶體閘(壓力中、還沒起子行程)時 Ctrl+C:幾秒內放手回 INTERRUPTED,不等滿 600 秒、零子行程",
                r4.get("lamp") == "INTERRUPTED" and time.time() - t1 < 5 and not (logs / "mem_wait.log").exists(),
                (r4.get("lamp"), round(time.time() - t1, 1)))
            STOP.clear()
            chk("⑤ 總燈:有 INTERRUPTED = INTERRUPTED(不是綠);沒中斷照 v0100",
                overall({"lamp": "GREEN"}, [{"lamp": "INTERRUPTED"}]) == "INTERRUPTED"
                and overall({"lamp": "GREEN"}, [{"lamp": "GREEN"}]) == "GREEN"
                and overall({"lamp": "GATED"}, [{"lamp": "GREEN"}]) == "YELLOW")
            PRIOR.REPORT_DIR = t / "report"
            os.environ["ACT_SLOW_S"] = "30"
            _HB["out"] = io.StringIO()
            opt = PRIOR.parse(["run", "--no-open", "--no-ui"])
            timer = threading.Timer(1.5, interrupt)
            timer.start()
            with contextlib.redirect_stdout(io.StringIO()):
                card = activate(opt, manager=mgr, temp=t)
            timer.cancel()
            rep = json.loads((t / "report" / "ACTIVATE_VDF_latest.json").read_text(encoding="utf-8"))
            chk("⑥ 整輪跑到一半中斷:照寫總覽(JSON + HTML),燈 INTERRUPTED,interrupted=true;main rc 不是 0",
                card["lamp"] == "INTERRUPTED" and rep["interrupted"] is True and rep["lamp"] == "INTERRUPTED"
                and (t / "report" / "ACTIVATE_VDF_latest.html").exists() and {"GREEN": 0, "YELLOW": 2}.get(card["lamp"], 1) != 0,
                (card["lamp"], [f.get("lamp") for f in card["flows"]]))
        finally:
            HEARTBEAT_S = keep_hb
            PRIOR.REPORT_DIR = keep_report
            _HB["out"] = None
            STOP.clear()
            _hb_stop()
            (os.environ.pop("ACT_SLOW_S", None) if keep_env is None else os.environ.__setitem__("ACT_SLOW_S", keep_env))
    with tempfile.TemporaryDirectory(prefix="activatevdf101_lock_") as td:
        t = Path(td)
        mgr = t / "mgr" / "VDF_SystemManager_v9999.py"
        mgr.parent.mkdir()
        mgr.write_text(PRIOR._FAKE_MANAGER, encoding="utf-8")
        flog = t / "calls.jsonl"
        keep = {k: os.environ.get(k) for k in ("ACT_FAKE_LOG", "ACT_FAKE_SLEEP")}
        os.environ["ACT_FAKE_LOG"], os.environ["ACT_FAKE_SLEEP"] = str(flog), "0.6"
        _HB["out"] = io.StringIO()
        try:
            STOP.clear()
            res3 = PRIOR.optimize_resources(want=3, stamp="20261016_130000", root=t)
            res3 = dict(res3, plan=dict(res3["plan"], slots=3))
            logs = t / "logs"
            logs.mkdir()
            opt = PRIOR.parse(["run", "--no-open", "--no-ui"])
            g = PRIOR.MemGate(reader=lambda: {"avail_mb": 9000, "total_mb": 16000}, interval=0.05).start()
            lists = phase_lists(opt, res3, g, logs, mgr)
            flows = run_flows(opt, res3, g, logs, lists, mgr)
            g.close()
            calls = [json.loads(x) for x in flog.read_text(encoding="utf-8").splitlines()]
            t009 = next(c["t0"] for c in calls if c["args"][:3] == ["fetch", "run", "009"])
            t010 = next(c["t0"] for c in calls if c["args"][:3] == ["fetch", "run", "010"])
            chk("⑨ 兩張清單依序跑(010 等 009 跑完才起;同寫 vdf_master_lists.duckdb 不撞鎖)· 清單 GREEN",
                t010 >= t009 + 0.55 and lists["lamp"] == "GREEN", round(t010 - t009, 2))
            tf = next(c["t0"] for c in calls if c["args"][:2] == ["fetch", "run"] and c["args"][2] not in ("009", "010"))
            te = next(c["t0"] for c in calls if c["args"][:2] == ["engine", "launch"])
            td_ = min(c["t0"] for c in calls if c["args"][:1] in (["db"], ["refill"]))
            chk("⑩ 資料庫流程等擷取流程寫完才開庫;引擎流程照樣與擷取並行;三條都 GREEN",
                td_ >= tf + 0.55 and te < tf + 0.55 and all(f["lamp"] == "GREEN" for f in flows),
                (round(td_ - tf, 2), round(te - tf, 2), [f["lamp"] for f in flows]))
        finally:
            _HB["out"] = None
            for k, v in keep.items():
                (os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v))
    if os.name != "nt":
        probe = (
            "import importlib.util,sys,json,os;from pathlib import Path\n"
            "sp=importlib.util.spec_from_file_location('a101',sys.argv[1]);m=importlib.util.module_from_spec(sp);"
            "sys.modules['a101']=m;sp.loader.exec_module(m)\n"
            "t=Path(sys.argv[2]);m.PRIOR.REPORT_DIR=t/'rep'\n"
            "card=m.activate(m.PRIOR.parse(['run','--no-open','--no-ui']),manager=Path(sys.argv[3]),temp=t)\n"
            "print('CARD '+json.dumps({'lamp':card['lamp'],'interrupted':card['interrupted']}))\n")
        with tempfile.TemporaryDirectory(prefix="activatevdf101_sig_") as td:
            t = Path(td)
            mgr = t / "mgr" / "VDF_SystemManager_v9999.py"
            mgr.parent.mkdir()
            mgr.write_text(_SLOW_MANAGER, encoding="utf-8")
            pr = subprocess.Popen([sys.executable, "-c", probe, str(Path(__file__).resolve()), str(t), str(mgr)],
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                                  env=dict(os.environ, ACT_SLOW_S="60", VIA_ACT_HEARTBEAT_S="0.5"))
            time.sleep(4)
            t0 = time.time()
            pr.send_signal(signal.SIGINT)
            try:
                outp, _ = pr.communicate(timeout=30)
            except subprocess.TimeoutExpired:
                pr.kill()
                outp, _ = pr.communicate()
            took = time.time() - t0
            line = next((x for x in outp.splitlines() if x.startswith("CARD ")), "")
            got = json.loads(line[5:]) if line else {}
            left = subprocess.run(["pgrep", "-f", str(mgr)], capture_output=True, text=True).stdout.split()
        sig_ok = (got.get("lamp") == "INTERRUPTED" and got.get("interrupted") is True and took < 15 and not left
                  and "Traceback" not in outp)
        sig_note = (got, round(took, 1), left, outp.strip().splitlines()[-1:] if outp else "")
    else:
        sig_ok, sig_note = True, "Windows 不送 POSIX SIGINT;由 ③ ⑥ 涵蓋"
    chk("⑧ 端到端:清單階段真送 SIGINT(Ctrl+C)→ 數秒內收掉、不互等;照寫總覽(INTERRUPTED);沒有殘留子行程;沒有 traceback",
        sig_ok, sig_note)
    src = Path(__file__).read_text(encoding="utf-8")
    imports = re.findall(r"^\s*(?:import|from)\s+([A-Za-z_][\w.]*)", src, re.M)
    chk("⑦ 加速器橋 · 網路橋在;不匯入他系統程式;不碰 TA-Lib;同意閘不寫",
        "VIA:ACCEL-BRIDGE" in src and "def _via_net" in src
        and not [x for x in imports if x.startswith(("CGC_", "VRN_", "VCGC"))]
        and not re.search(r"^\s*(import|from)\s+" + "talib", src, re.M)
        and not re.search(r"\[[\"']VIA_(NET|SCRAPE)_" + "CONSENT[\"']\]\s*=(?!=)", src))
    n = sum(ok)
    print(f"  [計] {TAG} 本版 {n}/{len(ok)} · {'PASS' if n == len(ok) else 'FAIL'}")
    if n != len(ok):
        return 1
    rc0 = PRIOR.selftest()
    return 0 if rc0 == 0 else (rc0 if rc0 in (2, 3) else 2)


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--selftest"]:
        return selftest()
    opt = PRIOR.parse(argv)
    if opt.verb != "run":
        return PRIOR.main(argv)
    card = activate(opt)
    return {"GREEN": 0, "YELLOW": 2, "INTERRUPTED": 130}.get(card["lamp"], 1)


if __name__ == "__main__":
    raise SystemExit(main())
