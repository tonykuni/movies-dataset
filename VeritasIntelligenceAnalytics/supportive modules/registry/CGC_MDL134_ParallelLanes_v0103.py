#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""CGC_MDL134_ParallelLanes v0103 — 薄尾:cmd 動詞 — 舊短指令背後改走 Python(先降壓 → 3~6 道 → 監工)

操作員令(2026-11-18):「一些舊的短指令背後指令全部要改為 PY 指令,且依照規定也要安裝加速器 × 3~5 步驟同步進行安全進行機制」
「跑完後回報燈號,接著列短指令清單分批改成 PY」;道數已統一 3~6(CLAUDE.md 2026-11-18 操作員令)。
本版只加一個動詞,前版 plan / run / digest / 鏈冊 / 哨兵 / 頁 一字不動:
  cmd list                     短指令盤點(路由冊;應掃 / 已掃 / 略過 三數對不上 = 紅)
  cmd check [短指令…]           每條 Python 路由:尾版在不在 · ast.parse · compile · 加速器橋(語法樹裡真的匯入)
  cmd plan <短指令> [參數…]     只印要跑的步與道數(零子行程)
  cmd run  <短指令> [參數…]     先降壓 → 依機器能力 3~6 道同時跑互不相干的步 → 監工過熱減道、暫停最新子行程、冷卻恢復
      選項:--slots N|auto · --calm-wait 秒 · --dry(零子行程)· --timeout 秒(每步)
路由冊正本:VIA_ShortCommand_PyRoute_SSOT_v*.json 尾版(同夾;只讀)。
邊界:本檔是 VCGC 自己的工具。別的系統(VDF / VRN)的短指令在 Register 尾版直接呼叫該系統自己的 Python 入口,不經本檔;
      本檔對它們只做 list / check(唯讀)。PS 只負責進環境與轉呼叫。
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

import ast
import datetime
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA_ROOT = HERE.parent.parent
_STEM = "CGC_MDL134_ParallelLanes"
TAG = "v0103"
ROUTE_BOOK_PAT = "VIA_ShortCommand_PyRoute_SSOT_v*.json"
MIN_SLOTS, MAX_SLOTS = 3, 6          # 道數統一 3~6(操作員 2026-11-18)
HEARTBEAT_S = 25                     # 每 30 秒內至少一行
HOT = {"cpu": 92.0, "mem": 90.0}     # 過熱:減道 + 暫停最新子行程
COOL = {"cpu": 75.0, "mem": 80.0}    # 冷卻:恢復一支 + 加道
CALM = {"cpu": 60.0, "mem": 80.0}    # 起跑前要靜到這裡(或等到 --calm-wait)
ACCEL_SELF = ("SUP_MDL737_SuperAccelModule", "VIA_SuperAccel_Module")   # 加速器本身不必再匯入自己
THREAD_CAPS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "POLARS_MAX_THREADS")


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + TAG, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


def now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── 路由冊 ────────────────────────────────────────────────────────────────
def book_path(folder: Path | None = None) -> Path | None:
    hits = sorted((folder or HERE).glob(ROUTE_BOOK_PAT), key=_vnum)
    return hits[-1] if hits else None


def load_book(path: Path | None = None) -> dict:
    p = path or book_path()
    if p is None:
        return {"_path": None, "routes": [], "inventory": {}}
    data = json.loads(Path(p).read_text(encoding="utf-8-sig"))
    data["_path"] = str(p)
    return data


def find_route(book: dict, name: str) -> dict | None:
    key = name.strip().lower()
    for r in book.get("routes", []):
        if r.get("name", "").lower() == key or key in [a.lower() for a in r.get("aliases", [])]:
            return r
    return None


def three_numbers(book: dict) -> dict:
    """應掃 / 已掃 / 略過:對不上 = 紅(省 Token 只能壓形式,不能縮範圍)。"""
    inv = book.get("inventory", {})
    should = int(inv.get("should_scan", 0))
    routes = book.get("routes", [])
    skipped = inv.get("skipped", [])
    done = len(routes)
    ok = should > 0 and should == done + len(skipped)
    return {"should": should, "scanned": done, "skipped": len(skipped), "skipped_list": skipped, "lamp": "GREEN" if ok else "RED"}


def tail_of(step: dict, root: Path | None = None) -> Path | None:
    folder = (root or VIA_ROOT) / step.get("dir", "")
    pat = step.get("glob", "")
    if not pat:
        return None
    if "*" not in pat:                                   # 沒有版號的固定檔名
        return (folder / pat) if (folder / pat).is_file() else None
    hits = [p for p in folder.glob(pat) if _vnum(p) >= 0]
    return max(hits, key=_vnum) if hits else None


def accel_in_ast(path: Path) -> tuple[bool, str]:
    """語法樹裡真的匯入加速器才算(只有標記不算);同時過 ast.parse 與 compile。"""
    if Path(path).stem.startswith(ACCEL_SELF):
        return True, "本身就是加速器"
    try:
        src = Path(path).read_text(encoding="utf-8-sig")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")              # 別人檔裡的跳脫字警告不是這裡要報的
            tree = ast.parse(src)
            compile(src, str(path), "exec")
    except Exception as exc:  # 語法 / 編譯不過照實回報
        return False, "AST/compile 不過:" + type(exc).__name__
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(a.name == "VIA_SuperAccel_Module" for a in node.names):
            return True, "匯入在"
        if isinstance(node, ast.ImportFrom) and node.module == "VIA_SuperAccel_Module":
            return True, "匯入在"
    return False, "語法樹裡沒有匯入 VIA_SuperAccel_Module"


def check_routes(book: dict, names: list | None = None, root: Path | None = None) -> list:
    rows = []
    want = [n.lower() for n in (names or [])]
    for r in book.get("routes", []):
        if want and r.get("name", "").lower() not in want:
            continue
        steps = r.get("steps", [])
        if r.get("state") not in ("PY", "PY_ALREADY"):
            lamp = "GRAY" if r.get("state") in ("PS_NATIVE", "FORWARD") else "YELLOW"
            rows.append({"name": r["name"], "owner": r.get("owner", ""), "state": r.get("state", ""), "batch": r.get("batch"), "lamp": lamp,
                         "detail": r.get("reason", "還沒改(待下一批)")})
            continue
        bad, notes = [], []
        for s in steps:
            t = tail_of(s, root)
            if t is None:
                bad.append(s["id"] + " 尾版不在(" + s.get("glob", "") + ")")
                continue
            ok, why = accel_in_ast(t)
            notes.append(s["id"] + "=" + t.name + (" · 加速器橋 " + why))
            if not ok:
                bad.append(s["id"] + " " + why)
        rows.append({"name": r["name"], "owner": r.get("owner", ""), "state": r["state"], "batch": r.get("batch"),
                     "lamp": "RED" if bad or not steps else "GREEN", "detail": ";".join(bad) if bad else ";".join(notes)})
    return rows


# ── 參數(PS 舊寫法 → Python 寫法;在 Python 端做才測得到)────────────────
def map_args(route: dict, user_args: list) -> list:
    amap = {k.lower(): v for k, v in route.get("arg_map", {}).items()}
    out = []
    for a in user_args:
        s = str(a)
        if s.lower() in amap:
            v = amap[s.lower()]
            if v:
                out.append(v)
        else:
            out.append(s)
    return out


def step_argv(route: dict, step: dict, user_args: list, py: str, root: Path | None = None) -> list | None:
    t = tail_of(step, root)
    if t is None:
        return None
    args = list(step.get("args", []))
    mapped = map_args(route, user_args)
    if step.get("pass_args"):
        args += mapped
    for rule in step.get("default_unless", []):          # 例:沒給 --no-open 才補 --open
        if rule.get("unless") not in mapped and rule.get("add") not in args:
            args.append(rule["add"])
    args = [a for a in args if a not in step.get("strip", [])]
    return [py, str(t)] + args


# ── 機器能力 / 降壓 / 監工 ────────────────────────────────────────────────
def _psutil():
    try:
        import psutil  # type: ignore
        return psutil
    except Exception:
        return None


def resources() -> dict:
    ps = _psutil()
    cpu_n = os.cpu_count() or 1
    if ps is None:
        return {"cpu_n": cpu_n, "mem_avail_gb": None, "cpu": None, "mem": None, "probe": "沒有 psutil(只憑核數)"}
    vm = ps.virtual_memory()
    return {"cpu_n": cpu_n, "mem_avail_gb": round(vm.available / 2 ** 30, 2), "cpu": ps.cpu_percent(interval=0.3), "mem": vm.percent, "probe": "psutil"}


def auto_slots(res: dict, n_steps: int | None = None) -> int:
    """依機器能力取道數,夾在 3~6;步數比道數少就用步數(不空轉)。"""
    by_cpu = max(1, int(res.get("cpu_n") or 1) - 1)
    by_mem = MAX_SLOTS if res.get("mem_avail_gb") is None else max(1, int(float(res["mem_avail_gb"]) // 1.5))
    slots = max(MIN_SLOTS, min(MAX_SLOTS, by_cpu, by_mem))
    return max(1, min(slots, n_steps)) if n_steps else slots


def clamp_slots(value, res: dict, n_steps: int | None = None) -> int:
    if str(value).lower() in ("", "auto", "none"):
        return auto_slots(res, n_steps)
    slots = max(MIN_SLOTS, min(MAX_SLOTS, int(value)))
    return max(1, min(slots, n_steps)) if n_steps else slots


def calm_env(base: dict | None = None, per_child_threads: int = 1) -> dict:
    env = dict(base if base is not None else os.environ)
    for k in THREAD_CAPS:
        env.setdefault(k, str(per_child_threads))
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    env["VIA_FROM_VCGC"] = "YES"
    return env


def lower_priority() -> str:
    ps = _psutil()
    try:
        if ps is not None and os.name == "nt":
            ps.Process().nice(ps.BELOW_NORMAL_PRIORITY_CLASS)
            return "BELOW_NORMAL"
        os.nice(5)
        return "nice +5"
    except Exception as exc:
        return "沒降(" + type(exc).__name__ + ")"


def wait_calm(max_wait: float, sampler=None, sleep=time.sleep, echo=print, step: float = 3.0) -> dict:
    """第一步:等系統靜下來(連兩次取樣都在 CALM 內)或等到上限;沒有量測工具就照實說。"""
    sampler = sampler or (lambda: resources())
    waited, good, last = 0.0, 0, {}
    while True:
        last = sampler()
        if last.get("cpu") is None:
            return {"calm": None, "waited": waited, "note": "沒有量測工具,略過等待(黃)", "last": last}
        good = good + 1 if (last["cpu"] <= CALM["cpu"] and last["mem"] <= CALM["mem"]) else 0
        if good >= 2:
            return {"calm": True, "waited": waited, "note": "已靜", "last": last}
        if waited >= max_wait:
            return {"calm": False, "waited": waited, "note": "等到上限還沒靜(照跑,道數從下限起)", "last": last}
        echo("[降壓] 等系統靜下來 · CPU " + str(last["cpu"]) + "% · DRAM " + str(last["mem"]) + "% · 已等 " + str(int(waited)) + "s")
        sleep(step)
        waited += step


class ProcCtl:
    """暫停 / 恢復子行程(psutil);沒有 psutil 就只減道不暫停,照實記。"""

    def __init__(self):
        self.paused = []

    def pause(self, pid: int) -> bool:
        ps = _psutil()
        if ps is None:
            return False
        try:
            proc = ps.Process(pid)
            for child in proc.children(recursive=True):
                child.suspend()
            proc.suspend()
            self.paused.append(pid)
            return True
        except Exception:
            return False

    def resume_one(self):
        ps = _psutil()
        if ps is None or not self.paused:
            return None
        pid = self.paused.pop()
        try:
            proc = ps.Process(pid)
            proc.resume()
            for child in proc.children(recursive=True):
                child.resume()
        except Exception:
            return None
        return pid

    def resume_all(self):
        while self.paused:
            if self.resume_one() is None:
                break

    def kill(self, pid: int):
        ps = _psutil()
        try:
            if ps is not None:
                proc = ps.Process(pid)
                for child in proc.children(recursive=True):
                    child.kill()
                proc.kill()
            else:
                os.kill(pid, 9)
        except Exception:
            return


class Supervisor:
    """最多 slots 支同時跑;依 needs 起跑;過熱減道並暫停最新子行程;冷卻恢復;至少留一支在跑;30 秒內必有一行。"""

    def __init__(self, jobs: list, slots: int, env: dict, logs: Path, sampler=None, ctl=None, interval: float = 2.0,
                 timeout: float | None = None, echo=print, popen=subprocess.Popen, clock=time.time, sleep=time.sleep):
        self.jobs = {j["id"]: j for j in jobs}
        self.order = [j["id"] for j in jobs]
        self.slots, self.ceiling = slots, slots
        self.env, self.logs = env, logs
        self.sampler = sampler or (lambda: resources())
        self.ctl = ctl or ProcCtl()
        self.interval, self.timeout = interval, timeout
        self.echo, self.popen, self.clock, self.sleep = echo, popen, clock, sleep
        self.running, self.done, self.started_at = {}, {}, {}
        self.reduced, self.peak = 0, 0

    def _ready(self, jid: str) -> bool:
        return all(n in self.done for n in self.jobs[jid].get("needs", []))

    def _blocked(self, jid: str) -> bool:
        return any(self.done.get(n, {}).get("lamp") == "RED" for n in self.jobs[jid].get("needs", []))

    def _start(self, jid: str):
        job = self.jobs[jid]
        self.logs.mkdir(parents=True, exist_ok=True)
        logp = self.logs / (jid + ".log")
        fh = open(logp, "w", encoding="utf-8", errors="replace")
        proc = self.popen(job["argv"], stdout=fh, stderr=subprocess.STDOUT, env=self.env, cwd=str(job.get("cwd") or VIA_ROOT))
        self.running[jid] = (proc, fh, logp)
        self.started_at[jid] = self.clock()
        self.peak = max(self.peak, len(self.running))
        self.echo("[起] " + jid + " · pid " + str(getattr(proc, "pid", "?")) + " · 同時 " + str(len(self.running)) + "/" + str(self.slots))

    def _finish(self, jid: str, rc: int, note: str = ""):
        proc, fh, logp = self.running.pop(jid)
        fh.close()
        sec = round(self.clock() - self.started_at[jid], 1)
        lamp = "GREEN" if rc == 0 else ("YELLOW" if rc in self.jobs[jid].get("yellow_rc", []) else "RED")
        self.done[jid] = {"id": jid, "rc": rc, "lamp": lamp, "sec": sec, "log": str(logp), "note": note}
        self.echo("[完] " + jid + " rc " + str(rc) + " · " + lamp + " · " + str(sec) + "s" + (" · " + note if note else ""))

    def _pressure(self):
        s = self.sampler()
        if s.get("cpu") is None:
            return
        active = [j for j in self.running if getattr(self.running[j][0], "pid", None) not in self.ctl.paused]
        if s["cpu"] >= HOT["cpu"] or s["mem"] >= HOT["mem"]:
            if self.slots > 1:
                self.slots -= 1
            if len(active) > 1:                      # 至少留一支在跑
                newest = max(active, key=lambda j: self.started_at[j])
                if self.ctl.pause(self.running[newest][0].pid):
                    self.echo("[監工] 過熱(CPU " + str(s["cpu"]) + "% · DRAM " + str(s["mem"]) + "%)→ 道數 " + str(self.slots) + " · 暫停 " + newest)
            self.reduced += 1
        elif s["cpu"] <= COOL["cpu"] and s["mem"] <= COOL["mem"]:
            pid = self.ctl.resume_one()
            if pid is not None:
                self.echo("[監工] 冷卻 → 恢復 pid " + str(pid))
            elif self.slots < self.ceiling:
                self.slots += 1

    def run(self) -> dict:
        t0, last_beat = self.clock(), self.clock()
        try:
            while len(self.done) < len(self.jobs):
                for jid in self.order:
                    if jid in self.done or jid in self.running:
                        continue
                    if self._blocked(jid):
                        self.done[jid] = {"id": jid, "rc": None, "lamp": "GRAY", "sec": 0, "log": "", "note": "前一步紅,沒跑"}
                        self.echo("[略] " + jid + " · 前一步紅,沒跑")
                    elif self._ready(jid) and len(self.running) < self.slots:
                        self._start(jid)
                for jid in list(self.running):
                    proc = self.running[jid][0]
                    rc = proc.poll()
                    if rc is not None:
                        self._finish(jid, rc)
                    elif self.timeout and self.clock() - self.started_at[jid] > self.timeout:
                        self.ctl.kill(proc.pid)
                        self._finish(jid, 124, "逾時 " + str(int(self.timeout)) + "s 收掉")
                if len(self.done) >= len(self.jobs):
                    break
                self._pressure()
                if self.clock() - last_beat >= HEARTBEAT_S:
                    last_beat = self.clock()
                    self.echo("[心跳] 在跑 " + ",".join(self.running) + " · 道數 " + str(self.slots) + " · 暫停 " + str(len(self.ctl.paused)) + " · 已完 " + str(len(self.done)) + "/" + str(len(self.jobs)))
                self.sleep(self.interval)
        finally:
            self.ctl.resume_all()
            for jid in list(self.running):
                self.ctl.kill(self.running[jid][0].pid)
                self._finish(jid, 130, "中斷收掉")
        return {"rows": [self.done[j] for j in self.order], "sec": round(self.clock() - t0, 1), "peak": self.peak, "reduced": self.reduced}


def fold(rows: list) -> str:
    lamps = [r["lamp"] for r in rows]
    if not lamps or "RED" in lamps or "GRAY" in lamps:
        return "RED"
    return "YELLOW" if "YELLOW" in lamps else "GREEN"


# ── 動詞 ──────────────────────────────────────────────────────────────────
def _opt(a: list, name: str, default=None):
    if name in a:
        i = a.index(name)
        val = a[i + 1] if i + 1 < len(a) else default
        del a[i:i + 2]
        return val
    return default


def cmd_list(book: dict, echo=print) -> int:
    tn = three_numbers(book)
    echo("[短指令 → Python 路由] 冊 " + str(Path(book["_path"]).name if book.get("_path") else "不在") + " · 應掃 " + str(tn["should"]) + " · 已掃 " + str(tn["scanned"]) + " · 略過 " + str(tn["skipped"]) + " · " + tn["lamp"])
    by = {}
    for r in book.get("routes", []):
        by.setdefault(r.get("state", "?"), []).append(r)
    for state in sorted(by):
        echo("  " + state + " " + str(len(by[state])) + " 支")
    for r in book.get("routes", []):
        if r.get("state") in ("PY",) or r.get("backing") in ("PS1", "PY+PS1"):
            echo("  " + r["name"].ljust(20) + " 批 " + str(r.get("batch", "-")).ljust(3) + r.get("state", "").ljust(10) + r.get("owner", "").ljust(5) + " " + (r.get("to") or r.get("reason") or ""))
    if tn["skipped_list"]:
        echo("  略過:" + "、".join(tn["skipped_list"]))
    return 0 if tn["lamp"] == "GREEN" else 1


def cmd_check(book: dict, names: list, echo=print, root: Path | None = None) -> int:
    rows = check_routes(book, names, root)
    if names and not rows:
        echo("[cmd check] 冊上沒有:" + "、".join(names))
        return 2
    py_rows = [r for r in rows if r["state"] == "PY"]
    old_rows = [r for r in rows if r["state"] == "PY_ALREADY"]
    for r in rows:
        if r["state"] == "PY" or names or (r["state"] == "PY_ALREADY" and r["lamp"] == "RED"):
            echo("  " + r["lamp"].ljust(7) + r["name"].ljust(20) + r["owner"].ljust(5) + " " + r["detail"][:200])
    red = [r["name"] for r in py_rows + old_rows if r["lamp"] == "RED"]
    todo = [r["name"] for r in rows if r["lamp"] == "YELLOW"]
    gray = [r["name"] for r in rows if r["lamp"] == "GRAY"]
    lamp = "RED" if red else ("YELLOW" if todo else "GREEN")
    echo("[cmd check] " + lamp + " · 應查 " + str(len(rows)) + " · 這輪改成 Python " + str(len(py_rows)) + "(綠 " + str(sum(1 for r in py_rows if r["lamp"] == "GREEN")) + ")· 原本就是 Python " + str(len(old_rows))
         + "(綠 " + str(sum(1 for r in old_rows if r["lamp"] == "GREEN")) + " · 紅 " + str(sum(1 for r in old_rows if r["lamp"] == "RED")) + ")· 還沒改 " + str(len(todo)) + "(黃)· 轉呼叫 / PS 本職 " + str(len(gray)) + "(灰)")
    return 1 if red else (2 if todo else 0)


def build_jobs(route: dict, user_args: list, py: str, root: Path | None = None) -> tuple[list, list]:
    jobs, missing = [], []
    for s in route.get("steps", []):
        argv = step_argv(route, s, user_args, py, root)
        if argv is None:
            missing.append(s["id"])
            continue
        jobs.append({"id": s["id"], "argv": argv, "needs": list(s.get("needs", [])), "yellow_rc": list(s.get("yellow_rc", []))})
    return jobs, missing


def cmd_run(book: dict, name: str, user_args: list, plan_only: bool = False, echo=print, root: Path | None = None,
            sampler=None, popen=subprocess.Popen, out_dir: Path | None = None, sleep=time.sleep) -> int:
    a = list(user_args)
    slots_opt = _opt(a, "--slots", "auto")
    calm_wait = float(_opt(a, "--calm-wait", "60"))
    timeout = _opt(a, "--timeout", None)
    dry = "--dry" in a
    a = [x for x in a if x != "--dry"]
    route = find_route(book, name)
    if route is None:
        echo("[cmd] 冊上沒有 " + name + "(零子行程)· 先 cmd list")
        return 2
    if route.get("state") != "PY":
        echo("[cmd] " + route["name"] + " 還沒有 Python 路由(" + route.get("state", "?") + ":" + (route.get("reason") or "待下一批") + ")· 零子行程")
        return 2
    jobs, missing = build_jobs(route, a, sys.executable, root)
    if missing:
        echo("[cmd] RED · " + route["name"] + " 缺尾版:" + "、".join(missing) + "(零子行程)")
        return 1
    res = (sampler or resources)()
    slots = clamp_slots(slots_opt, res, len(jobs))
    echo("[cmd " + ("plan" if plan_only or dry else "run") + "] " + route["name"] + " · " + route.get("owner", "") + " · 步 " + str(len(jobs)) + " · 道數 " + str(slots) + "(範圍 " + str(MIN_SLOTS) + "~" + str(MAX_SLOTS) + ";核 " + str(res.get("cpu_n")) + " · 可用記憶體 " + str(res.get("mem_avail_gb")) + " GB)")
    for j in jobs:
        echo("  步 " + j["id"] + (" ← " + ",".join(j["needs"]) if j["needs"] else "") + " · " + Path(j["argv"][1]).name + " " + " ".join(j["argv"][2:]))
    if plan_only or dry:
        return 0
    echo("[降壓] 本行程優先權 " + lower_priority() + " · 子行程執行緒上限 1(" + "/".join(k.split("_")[0] for k in THREAD_CAPS) + ")")
    calm = wait_calm(calm_wait, sampler=sampler, sleep=sleep, echo=echo)
    if calm["calm"] is False:
        slots = min(slots, max(1, min(MIN_SLOTS, len(jobs))))
    echo("[降壓] " + calm["note"] + " · 等了 " + str(int(calm["waited"])) + "s → 起跑道數 " + str(slots))
    out = out_dir or (VIA_ROOT / "VIA_Reports" / "lanes" / "cmd")
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    sup = Supervisor(jobs, slots, calm_env(), out / ("run_" + stamp), sampler=sampler, popen=popen,
                     timeout=float(timeout) if timeout else None, echo=echo, sleep=sleep)
    rep = sup.run()
    lamp = fold(rep["rows"])
    if calm["calm"] is None and lamp == "GREEN":
        lamp = "YELLOW"                                  # 沒量到壓力就起跑 = 黃,不寫綠
    rep.update({"engine": _STEM + " " + TAG, "command": route["name"], "owner": route.get("owner"), "lamp": lamp, "slots": slots,
                "calm": calm, "utc": now(), "host": "container" if os.name != "nt" else "host", "book": Path(book["_path"]).name if book.get("_path") else None})
    out.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^\w\-]", "_", route["name"])
    for target in (out / ("CMD_" + safe + "_latest.json"), out / ("CMD_" + safe + "_" + stamp + ".json")):
        tmp = target.with_suffix(".tmp" + str(os.getpid()))
        tmp.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(tmp, target)
    echo("[" + _STEM + " " + TAG + "] " + lamp + " · " + route["name"] + " · " + " · ".join(r["id"] + " " + r["lamp"] for r in rep["rows"]) + " · 同時最多 " + str(rep["peak"]) + " · 監工降壓 " + str(rep["reduced"]) + " 次 · " + str(rep["sec"]) + "s · 收據 " + str(out / ("CMD_" + safe + "_latest.json")))
    return 0 if lamp == "GREEN" else (2 if lamp == "YELLOW" else 1)


def cmd_main(a: list) -> int:
    book = load_book()
    verb = a[0] if a else "list"
    if book.get("_path") is None:
        print("[cmd] RED · 路由冊 " + ROUTE_BOOK_PAT + " 不在(零子行程)")
        return 1
    if verb == "list":
        return cmd_list(book)
    if verb == "check":
        return cmd_check(book, a[1:])
    if verb in ("plan", "run"):
        if len(a) < 2:
            print("[cmd] 用法:cmd " + verb + " <短指令> [參數…](零子行程)")
            return 2
        return cmd_run(book, a[1], a[2:], plan_only=(verb == "plan"))
    print("[cmd] 不認得的動詞 " + verb + ":list | check | plan | run(零子行程)")
    return 2


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 十道並行安全編排(" + _STEM + " " + TAG + ")· 薄尾自測(cmd 動詞 · 3~6 道 · 降壓 · 監工)===")
        return selftest()
    if a and a[0] == "cmd":
        return cmd_main(a[1:])
    return PRIOR.main()


# ── 自測(全在 TEMP;零真引擎、零出網)──────────────────────────────────
def selftest() -> int:
    n = {"ok": 0, "bad": 0}

    def chk(name, cond, note=""):
        n["ok" if cond else "bad"] += 1
        print("  " + ("✓" if cond else "✗") + " " + name + ((" · " + note) if note else ""))

    quiet = lambda *_a, **_k: None  # noqa: E731
    with tempfile.TemporaryDirectory(prefix="via_lanes_cmd_") as td:
        root = Path(td)
        eng = root / "eng"
        eng.mkdir()
        bridge = "try:\n    import VIA_SuperAccel_Module as VIA_ACCEL\nexcept Exception:\n    VIA_ACCEL = None\n"
        (eng / "OKA_v0100.py").write_text(bridge + "import sys,time\ntime.sleep(0.4)\nprint('a', sys.argv[1:])\n", encoding="utf-8")
        (eng / "OKA_v0101.py").write_text(bridge + "import sys,time\ntime.sleep(0.4)\nprint('a1', sys.argv[1:])\n", encoding="utf-8")
        (eng / "OKB_v0100.py").write_text(bridge + "import time\ntime.sleep(0.4)\nprint('b')\n", encoding="utf-8")
        (eng / "BAD_v0100.py").write_text(bridge + "import sys\nsys.exit(3)\n", encoding="utf-8")
        (eng / "NOBRIDGE_v0100.py").write_text("# [VIA:ACCEL-BRIDGE:v0111] 只有標記\nprint('x')\n", encoding="utf-8")
        (eng / "CRLF_v0100.py").write_bytes((bridge + "print('crlf')\n").replace("\n", "\r\n").encode("utf-8"))
        (eng / "SYN_v0100.py").write_text("def broken(:\n", encoding="utf-8")
        st = lambda i, g, **k: dict({"id": i, "dir": "eng", "glob": g}, **k)  # noqa: E731
        book = {"_path": str(root / "VIA_ShortCommand_PyRoute_SSOT_v0100.json"),
                "inventory": {"should_scan": 13, "skipped": ["via-skip"]},
                "routes": [
                    {"name": "via-one", "owner": "VCGC", "state": "PY", "batch": 1, "steps": [st("a", "OKA_v*.py", args=["all"], pass_args=True, default_unless=[{"unless": "--no-open", "add": "--open"}])],
                     "arg_map": {"-Apply": "--apply", "-NoOpen": "--no-open", "-SkipPull": ""}},
                    {"name": "via-two", "owner": "VCGC", "state": "PY", "batch": 1, "steps": [st("a", "OKA_v*.py"), st("b", "OKB_v*.py"), st("c", "OKA_v*.py", needs=["a", "b"])]},
                    {"name": "via-red", "owner": "VCGC", "state": "PY", "batch": 1, "steps": [st("x", "BAD_v*.py"), st("y", "OKB_v*.py", needs=["x"])]},
                    {"name": "via-gone", "owner": "VCGC", "state": "PY", "batch": 1, "steps": [st("g", "GONE_v*.py")]},
                    {"name": "via-mark", "owner": "VDF", "state": "PY", "batch": 1, "steps": [st("m", "NOBRIDGE_v*.py")]},
                    {"name": "via-crlf", "owner": "VRN", "state": "PY", "batch": 1, "steps": [st("m", "CRLF_v*.py")]},
                    {"name": "via-syn", "owner": "VCGC", "state": "PY", "batch": 1, "steps": [st("m", "SYN_v*.py")]},
                    {"name": "via-later", "owner": "VCGC", "state": "TODO", "batch": 2, "backing": "PS1", "reason": "待第二批"},
                    {"name": "via-was", "owner": "VCGC", "state": "PY_ALREADY", "steps": [st("e1", "OKB_v*.py")]},
                    {"name": "via-wasbad", "owner": "VCGC", "state": "PY_ALREADY", "steps": [st("e1", "NOBRIDGE_v*.py")]},
                    {"name": "via-fwd", "owner": "CORE", "state": "FORWARD", "reason": "只轉呼叫 via-one"},
                    {"name": "via-shell", "owner": "CORE", "state": "PS_NATIVE", "backing": "PS1", "reason": "重載設定檔是 PS 本職"},
                ]}
        Path(book["_path"]).write_text(json.dumps({k: v for k, v in book.items() if k != "_path"}, ensure_ascii=False), encoding="utf-8")
        calm_s = lambda: {"cpu_n": 8, "mem_avail_gb": 12.0, "cpu": 10.0, "mem": 30.0}  # noqa: E731

        tn = three_numbers(book)
        chk("三數對得上 = 綠", tn["lamp"] == "GREEN" and (tn["should"], tn["scanned"], tn["skipped"]) == (13, 12, 1), str(tn["should"]) + "/" + str(tn["scanned"]) + "/" + str(tn["skipped"]))
        bad_book = dict(book, inventory={"should_scan": 99, "skipped": []})
        chk("三數對不上 = 紅", three_numbers(bad_book)["lamp"] == "RED")
        chk("讀冊尾版(檔案)", load_book(book_path(root)).get("routes", [{}])[0].get("name") == "via-one")
        chk("取尾版 = 最大版號", tail_of(book["routes"][0]["steps"][0], root).name == "OKA_v0101.py")
        (eng / "plain.py").write_text("print(1)\n", encoding="utf-8")
        (eng / "SUP_MDL737_SuperAccelModule_v0100.py").write_text("print('accel')\n", encoding="utf-8")
        chk("沒版號的固定檔名也找得到;加速器本身不必匯入自己", tail_of(st("p", "plain.py"), root).name == "plain.py" and tail_of(st("p", "nope.py"), root) is None
            and accel_in_ast(eng / "SUP_MDL737_SuperAccelModule_v0100.py")[0])
        chk("道數下限 3(弱機)", clamp_slots("auto", {"cpu_n": 2, "mem_avail_gb": 2.0}) == 3)
        chk("道數上限 6(強機)", clamp_slots("auto", {"cpu_n": 32, "mem_avail_gb": 64.0}) == 6 and clamp_slots("10", {"cpu_n": 32}) == 6 and clamp_slots("1", {"cpu_n": 32}) == 3)
        chk("步數少於道數就用步數", clamp_slots("auto", {"cpu_n": 16, "mem_avail_gb": 32.0}, 2) == 2)
        argv = step_argv(book["routes"][0], book["routes"][0]["steps"][0], ["-Apply", "-SkipPull", "--fast"], "py", root)
        chk("PS 舊參數換成 Python 寫法 + 預設補 --open", argv[2:] == ["all", "--apply", "--fast", "--open"], " ".join(argv[2:]))
        argv2 = step_argv(book["routes"][0], book["routes"][0]["steps"][0], ["-noopen"], "py", root)
        chk("給了 -NoOpen 就不補 --open(不分大小寫)", argv2[2:] == ["all", "--no-open"], " ".join(argv2[2:]))

        rows = {r["name"]: r for r in check_routes(book, None, root)}
        chk("check:橋真的匯入 = 綠", rows["via-one"]["lamp"] == "GREEN" and rows["via-crlf"]["lamp"] == "GREEN")
        chk("check:只有標記沒有匯入 = 紅", rows["via-mark"]["lamp"] == "RED" and "沒有匯入" in rows["via-mark"]["detail"])
        chk("check:尾版不在 = 紅;語法不過 = 紅", rows["via-gone"]["lamp"] == "RED" and rows["via-syn"]["lamp"] == "RED")
        chk("check:還沒改 = 黃;PS 本職 / 轉呼叫 = 灰(都不是綠)", rows["via-later"]["lamp"] == "YELLOW" and rows["via-shell"]["lamp"] == "GRAY" and rows["via-fwd"]["lamp"] == "GRAY")
        chk("check:原本就是 Python 的也照查橋(綠 / 紅),但不給 run", rows["via-was"]["lamp"] == "GREEN" and rows["via-wasbad"]["lamp"] == "RED"
            and cmd_run(book, "via-was", [], echo=quiet, root=root, out_dir=root / "o0") == 2)
        chk("check 總燈有紅回 1", cmd_check(book, [], echo=quiet, root=root) == 1)

        spawned = []

        def spy(argv, **kw):
            spawned.append(argv)
            return subprocess.Popen(argv, **kw)

        out = root / "out"
        chk("冊上沒有的名字:rc 2 · 零子行程", cmd_run(book, "via-nope", [], echo=quiet, root=root, popen=spy, out_dir=out) == 2 and not spawned)
        chk("還沒改的指令:rc 2 · 零子行程", cmd_run(book, "via-later", [], echo=quiet, root=root, popen=spy, out_dir=out) == 2 and not spawned)
        chk("缺尾版:紅 · 零子行程", cmd_run(book, "via-gone", [], echo=quiet, root=root, popen=spy, out_dir=out) == 1 and not spawned)
        chk("plan / --dry:零子行程", cmd_run(book, "via-two", [], plan_only=True, echo=quiet, root=root, popen=spy, out_dir=out) == 0
            and cmd_run(book, "via-two", ["--dry"], echo=quiet, root=root, popen=spy, out_dir=out) == 0 and not spawned)

        lines = []
        rc = cmd_run(book, "via-two", ["--calm-wait", "0"], echo=lines.append, root=root, sampler=calm_s, popen=spy, out_dir=out)
        rep = json.loads((out / "CMD_via-two_latest.json").read_text(encoding="utf-8"))
        chk("實跑三步全綠 rc 0", rc == 0 and rep["lamp"] == "GREEN" and len(spawned) == 3, rep["lamp"])
        chk("互不相干的兩步同時跑;有相依的等前面", rep["peak"] == 2 and [r["id"] for r in rep["rows"]] == ["a", "b", "c"]
            and lines.index(next(x for x in lines if x.startswith("[起] c"))) > lines.index(next(x for x in lines if x.startswith("[完] b"))), "同時最多 " + str(rep["peak"]))
        chk("先降壓再起跑(降壓行在第一支起跑之前)", lines.index(next(x for x in lines if x.startswith("[降壓]"))) < lines.index(next(x for x in lines if x.startswith("[起]"))))
        chk("子行程帶執行緒上限與入口標記", calm_env({})["OMP_NUM_THREADS"] == "1" and calm_env({})["VIA_FROM_VCGC"] == "YES" and calm_env({"OMP_NUM_THREADS": "4"})["OMP_NUM_THREADS"] == "4")
        chk("收據寫在 out,帶引擎版本與 UTC", rep["engine"].endswith(TAG) and rep["utc"].endswith("Z") and rep["command"] == "via-two")

        rc = cmd_run(book, "via-red", ["--calm-wait", "0"], echo=quiet, root=root, sampler=calm_s, out_dir=out)
        rep = json.loads((out / "CMD_via-red_latest.json").read_text(encoding="utf-8"))
        chk("一步紅 → 總燈紅 rc 1;後面相依步沒跑記灰", rc == 1 and rep["rows"][0]["lamp"] == "RED" and rep["rows"][1]["lamp"] == "GRAY")

        rc = cmd_run(book, "via-one", ["--calm-wait", "0"], echo=quiet, root=root, sampler=lambda: {"cpu_n": 4, "mem_avail_gb": None, "cpu": None, "mem": None}, out_dir=out)
        chk("量不到壓力就起跑 = 黃(rc 2),不寫綠", rc == 2 and json.loads((out / "CMD_via-one_latest.json").read_text(encoding="utf-8"))["lamp"] == "YELLOW")

        seq = iter([{"cpu": 95.0, "mem": 50.0}] * 2 + [{"cpu": 20.0, "mem": 30.0}] * 400)
        w = wait_calm(30.0, sampler=lambda: next(seq), sleep=lambda _s: None, echo=quiet)
        chk("等靜:兩次熱之後連兩次靜才放行", w["calm"] is True and w["waited"] == 9.0, "等 " + str(w["waited"]) + "s")
        w2 = wait_calm(6.0, sampler=lambda: {"cpu": 99.0, "mem": 50.0}, sleep=lambda _s: None, echo=quiet)
        chk("等到上限還沒靜:照實回 False", w2["calm"] is False)

        class FakeCtl(ProcCtl):
            def __init__(self):
                super().__init__()
                self.log = []

            def pause(self, pid):
                self.paused.append(pid)
                self.log.append(("pause", pid))
                return True

            def resume_one(self):
                if not self.paused:
                    return None
                pid = self.paused.pop()
                self.log.append(("resume", pid))
                return pid

        hot = iter([{"cpu": 97.0, "mem": 50.0}] * 2 + [{"cpu": 30.0, "mem": 30.0}] * 4000)
        ctl = FakeCtl()
        jobs = [{"id": k, "argv": [sys.executable, str(eng / "OKB_v0100.py")], "needs": []} for k in ("j1", "j2", "j3", "j4")]
        sup = Supervisor(jobs, 4, calm_env(), root / "logs", sampler=lambda: next(hot), ctl=ctl, interval=0.05, echo=quiet)
        r = sup.run()
        chk("過熱:減道並暫停最新子行程;冷卻恢復;全部跑完", r["reduced"] >= 1 and ("pause" in [x[0] for x in ctl.log]) and ("resume" in [x[0] for x in ctl.log]) and fold(r["rows"]) == "GREEN", "降壓 " + str(r["reduced"]) + " 次")
        one = Supervisor(jobs[:1], 3, calm_env(), root / "logs1", sampler=lambda: {"cpu": 99.0, "mem": 99.0}, ctl=FakeCtl(), interval=0.05, echo=quiet)
        r1 = one.run()
        chk("只剩一支在跑時不暫停(至少留一支)", not one.ctl.log and fold(r1["rows"]) == "GREEN")

        beats = []
        clock = {"t": 0.0}

        class FakeProc:
            pid = 4242

            def __init__(self):
                self.left = 4

            def poll(self):
                self.left -= 1
                return 0 if self.left <= 0 else None

        hb = Supervisor([{"id": "slow", "argv": ["x"], "needs": []}], 3, {}, root / "logs2", sampler=lambda: {"cpu": None}, interval=20.0,
                        echo=beats.append, popen=lambda *_a, **_k: FakeProc(), clock=lambda: clock["t"], sleep=lambda s: clock.__setitem__("t", clock["t"] + s))
        hb.run()
        chk("長跑每 30 秒內有心跳", any(b.startswith("[心跳]") for b in beats), str(sum(1 for b in beats if b.startswith("[心跳]"))) + " 行")
        chk("逾時收掉 = rc 124 紅", (lambda s: (s.run()["rows"][0]["rc"] == 124))(Supervisor([{"id": "hang", "argv": [sys.executable, "-c", "import time; time.sleep(30)"], "needs": []}], 3, calm_env(), root / "logs3", sampler=calm_s, interval=0.1, timeout=0.5, echo=quiet)))
        chk("前版動詞仍在(plan / run / digest 轉給前版)", callable(getattr(PRIOR, "main", None)) and PRIOR_PATH.name < Path(__file__).name)
        chk("本檔語法樹裡真的匯入加速器;不含本機路徑", accel_in_ast(Path(__file__))[0] and ("C:" + "\\Users") not in Path(__file__).read_text(encoding="utf-8"))
    print("[" + _STEM + " " + TAG + "] 自測 " + ("GREEN" if n["bad"] == 0 else "RED") + " · " + str(n["ok"]) + "/" + str(n["ok"] + n["bad"]))
    return 0 if n["bad"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
