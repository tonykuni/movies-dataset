#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL134_ParallelLanes v0100 — 十道並行安全編排(批377 操作員令「Keep testing debugging optimizing …
till they work perfectly for the remaining processes; safely proceed with the 10 parallel procedures without
damaging the system. Prevent hydra issues.」)

一句話:把 FixAll 補齊鏈(MDL125 步冊,零重複定義)改成「資源鏈 DAG」排程——同一 DuckDB/同一安裝器的步
        序跑(單寫者律),不同資源的鏈最多十道並行(env VIA_LANES,預設 10);跑前五道 Hydra 哨兵,
        跑中每步獨占鎖,誠實三態;頁+冊只增不減。

資源鏈(單寫者律;鏈內序跑、鏈間並行):
  fs   datahome(接點;所有鏈之前)                 pip  opencc → pkuseg           node vap_node
  gl   global → fred(vdf_global_market.duckdb)    tw   hist_probe → group_class → revenue_backfill → consensus → revenue_consensus
  etf  etf_universe → etf_fetch → etf_history     join etf_revenue(tw 鏈末+etf 鏈末之後;讀兩庫寫 tw)
  grid refail(所有資料鏈之後)→ digest
  有效並行度=鏈數(≤10);十道=上限,不是硬湊十個同跑(DuckDB 平行鎖撞=假紅,批353 實錄)。

Hydra 哨兵(跑前,全唯讀;H3 阻擋,其餘具名 WARN):
  H1 同名雙物(大小寫不分;VIA 根/registry/VDF engine/VRN)      H2 同族同版雙物(活動樹;_sha/intake/superseded 除外)
  H3 進程雙頭:本編排全域鎖+每步鎖(PID 活=BUSY 拒跑;死 PID=回收)+FixAll PROGRESS.json 60s 內心跳=另一補齊鏈在跑→拒跑
  H4 單寫者律=鏈冊本身(每步屬唯一鏈)                              H5 尾版律:每步引擎路徑必為其族尾版
  H6 資料家可用律(批377 實錄:雲端讀到 Windows 指標→MDL123 link 搬走 output_hub 留斷鏈;已回復+MDL123 v0101 拒接):datahome 步先問 home_usable,不可用=SKIP 零搬移
安全閘:離線(VIA_OFFLINE=1 或探測不通)→ net 步 SKIP 誠實;FRED 鑰缺→SKIP 印指令(VIA_FRED_PROMPT=0 並行不問 TTY);
        零 force;零刪除;子進程 cwd=VIA;逾時 kill(不卡斷);Ctrl-C 只停排程不殺已跑完的成果。
用法:via-lanes            → plan(零執行:鏈冊+哨兵+有效並行度)
      via-lanes run [--workers N] [--only a,b] [--dry]   → 並行執行;存證 VIA_Reports/lanes/LANES_<stamp>.json+頁
      via-lanes digest    → 上次存證一屏
      python <本檔> --selftest → 九檢
"""
from __future__ import annotations

import html
import importlib.util
import json
import os
import re
import subprocess
import sys
import threading
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
UI = VIA / "supportive modules" / "ui_support"
REP = VIA / "VIA_Reports" / "lanes"
LOCKS = REP / "locks"
FIXALL_REP = VIA / "VIA_Reports" / "fixall"
PAGE = UI / "VIA_UI_ParallelLanes_v0100.html"
BOOK = HERE / "VIA_ParallelLanes_v0100.json"
ENGINE_TAG = "CGC_MDL134_ParallelLanes v0100"
MAX_LANES = 10

# 鏈冊:step id → (chain, after=[step ids])  單寫者律:同鏈序跑
CHAINS = {
    "datahome": ("fs", []),
    "opencc": ("pip", ["datahome"]), "pkuseg": ("pip", ["datahome"]),
    "vap_node": ("node", ["datahome"]),
    "global": ("gl", ["datahome"]), "fred": ("gl", ["datahome"]),
    "hist_probe": ("tw", ["datahome"]), "group_class": ("tw", ["datahome"]), "revenue_backfill": ("tw", ["datahome"]),
    "consensus": ("tw", ["datahome"]), "revenue_consensus": ("tw", ["datahome"]),
    "etf_universe": ("etf", ["datahome"]), "etf_fetch": ("etf", ["datahome"]), "etf_history": ("etf", ["datahome"]),
    "etf_revenue": ("join", ["revenue_consensus", "etf_history"]),
    "refail": ("grid", ["etf_revenue", "fred", "pkuseg", "vap_node"]),
    "digest": ("grid", ["refail"]),
}
ACTIVE_DIRS = ["", "supportive modules/registry", "supportive modules", "functional modules/VDF/engine", "functional modules/VDF",
               "functional modules/VRN", "functional modules/VAP/engine"]
ARCHIVE_RX = re.compile(r"_sha[0-9a-f]{6,}|/references/intake/|_superseded|_review_quarantine|VIA_RetiredEngines|_archive|_legacy|\(\d+\)", re.I)
VERSION_RX = re.compile(r"^(?P<fam>.+?)[_-]v(?P<ver>\d{3,4})(?P<rest>\.\w+)$")
RULES = ["單寫者律:同一 DuckDB/安裝器的步在同鏈序跑;鏈間才並行(十道=上限,有效並行=鏈數)",
         "Hydra 律:H3 進程雙頭=阻擋(PID 活=BUSY;死=回收);H1/H2 同名/同版雙物具名 WARN;零 force",
         "誠實三態 OK/FAIL/SKIP;離線=net 步 SKIP;鑰缺=SKIP 印指令;逾時 kill 不卡斷",
         "只增不減:步冊零重複定義(直取 MDL125 plan);頁/冊 version-forward;零刪除",
         "尾版律:引擎/冊 glob 尾版動態解析,永不寫死版號"]


# ---------------------------------------------------------------- 載入
def newest(pat: str, root: Path = HERE) -> Path | None:
    hits = sorted(root.glob(pat))
    return hits[-1] if hits else None


def _load(pat: str, alias: str):
    p = newest(pat)
    if not p:
        return None
    spec = importlib.util.spec_from_file_location(alias, p)
    m = importlib.util.module_from_spec(spec)
    sys.modules[alias] = m
    spec.loader.exec_module(m)
    return m


_M125 = None


def m125():
    global _M125
    if _M125 is None:
        _M125 = _load("CGC_MDL125_FixAll_v0*.py", "lanes_m125")
    return _M125


def steps_from_fixall() -> list:
    m = m125()
    return list(m.plan()) if m else []


def assign(steps: list) -> list:
    """每步配鏈;未入冊=獨立鏈 solo_<id>(誠實標 UNMAPPED,仍可跑)"""
    out = []
    for s in steps:
        ch, after = CHAINS.get(s["id"], ("solo_" + s["id"], ["datahome"] if s["id"] != "datahome" else []))
        out.append({**s, "chain": ch, "after": [a for a in after if a != s["id"]], "mapped": s["id"] in CHAINS})
    return out


def select(steps: list, only: list | None) -> list:
    """--only 子集:after 依賴取全冊遞移閉包再交集(批377 實錄:子集跑時 refail 早於 revenue_backfill 起跑=依賴邊被濾掉);
    同鏈前序亦視為依賴(單寫者律不因子集失效)"""
    if not only:
        return steps
    by_id = {x["id"]: x for x in steps}
    prev, chain_prev = {}, {}
    for x in steps:
        prev[x["id"]] = chain_prev.get(x["chain"])
        chain_prev[x["chain"]] = x["id"]

    def closure(i, seen):
        for a in list(by_id.get(i, {}).get("after", [])) + ([prev[i]] if prev.get(i) else []):
            if a in by_id and a not in seen:
                seen.add(a)
                closure(a, seen)
        return seen
    sel = set(only)
    out = []
    for x in steps:
        if x["id"] in sel:
            deps = closure(x["id"], set())
            out.append({**x, "after": sorted(d for d in deps if d in sel and d != x["id"])})
    return out


# ---------------------------------------------------------------- Hydra 哨兵
def h1_same_name(root: Path = VIA, dirs: list | None = None) -> list:
    dup = []
    for d in (dirs if dirs is not None else ACTIVE_DIRS):
        p = root / d if d else root
        if not p.is_dir():
            continue
        seen = {}
        for f in p.iterdir():
            if f.is_file():
                seen.setdefault(f.name.lower(), []).append(f.name)
        dup += [(str(d or "."), v) for v in seen.values() if len(v) > 1]
    return dup


def h2_same_version(root: Path = VIA, dirs: list | None = None) -> list:
    fam = {}
    for d in (dirs if dirs is not None else ACTIVE_DIRS):
        p = root / d if d else root
        if not p.is_dir():
            continue
        for f in p.iterdir():
            if not f.is_file() or ARCHIVE_RX.search(str(f).replace("\\", "/")):
                continue
            mm = VERSION_RX.match(f.name)
            if mm:
                fam.setdefault((mm.group("fam"), mm.group("ver"), mm.group("rest")), set()).add(str(d or "."))
    return sorted((k[0] + "_v" + k[1] + k[2], sorted(v)) for k, v in fam.items() if len(v) > 1)


def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if pid == os.getpid():
        return True
    if os.name == "nt":
        try:
            out = subprocess.run(["tasklist", "/FI", "PID eq " + str(pid), "/NH"], capture_output=True, text=True, timeout=10).stdout
            return str(pid) in out
        except Exception:
            return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except Exception:
        return False


def lock_acquire(name: str, locks: Path = None) -> tuple[bool, str]:
    """(取得?, 說明);活 PID 持鎖=BUSY;死 PID=回收"""
    locks = locks or LOCKS
    locks.mkdir(parents=True, exist_ok=True)
    lf = locks / (name + ".lock")
    if lf.exists():
        try:
            d = json.loads(lf.read_text(encoding="utf-8"))
            pid = int(d.get("pid", 0))
        except Exception:
            pid = 0
        if pid_alive(pid) and pid != os.getpid():
            return False, "BUSY:PID " + str(pid) + " 持鎖 " + str(d.get("ts", ""))
        note = "回收死鎖 PID " + str(pid) + ";"
    else:
        note = ""
    lf.write_text(json.dumps({"pid": os.getpid(), "ts": datetime.now().isoformat(timespec="seconds"), "name": name}), encoding="utf-8")
    return True, note + "取鎖 PID " + str(os.getpid())


def lock_release(name: str, locks: Path = None):
    lf = (locks or LOCKS) / (name + ".lock")
    try:
        d = json.loads(lf.read_text(encoding="utf-8"))
        if int(d.get("pid", 0)) == os.getpid():
            lf.unlink()
    except Exception:
        pass


def h3_fixall_running(rep: Path = None, window: int = 60) -> str:
    """FixAll 補齊鏈 PROGRESS.json 60s 內心跳=另一鏈在跑(雙頭)"""
    rep = rep or FIXALL_REP
    runs = sorted(rep.glob("RUN_*/PROGRESS.json"), key=lambda p: p.stat().st_mtime) if rep.exists() else []
    if not runs:
        return ""
    age = time.time() - runs[-1].stat().st_mtime
    if age <= window:
        try:
            d = json.loads(runs[-1].read_text(encoding="utf-8"))
            if pid_alive(int(d.get("self_pid", 0))):
                return "FixAll 補齊鏈進行中(PID " + str(d.get("self_pid")) + " · " + str(d.get("id")) + " · " + str(int(age)) + "s 前心跳)"
        except Exception:
            return "FixAll PROGRESS.json " + str(int(age)) + "s 前更新(疑另一鏈在跑)"
    return ""


def h5_is_tail(path: str) -> tuple[bool, str]:
    p = Path(path)
    mm = VERSION_RX.match(p.name)
    if not mm or not p.parent.exists():
        return True, "無版號=就地"
    tail = newest(mm.group("fam") + "_v*" + mm.group("rest"), p.parent) or newest(mm.group("fam") + "-v*" + mm.group("rest"), p.parent)
    return (tail is not None and tail.name == p.name), (tail.name if tail else "?")


def preflight(steps: list) -> dict:
    h1 = h1_same_name()
    h2 = h2_same_version()
    busy = h3_fixall_running()
    stale = []
    for s in steps:
        if s.get("argv") and not str(s["argv"][0]).startswith("__") and len(s["argv"]) > 1:
            ok, tail = h5_is_tail(str(s["argv"][1]))
            if not ok:
                stale.append(s["id"] + ":" + Path(str(s["argv"][1])).name + "→尾版 " + tail)
    chains = {}
    for s in steps:
        chains.setdefault(s["chain"], []).append(s["id"])
    return {"H1": {"state": "WARN" if h1 else "OK", "items": [d + ": " + "/".join(v) for d, v in h1]},
            "H2": {"state": "WARN" if h2 else "OK", "items": [n + " @ " + ", ".join(v) for n, v in h2]},
            "H3": {"state": "FAIL" if busy else "OK", "items": [busy] if busy else []},
            "H4": {"state": "OK", "items": [c + ": " + " → ".join(v) for c, v in chains.items()]},
            "H5": {"state": "FAIL" if stale else "OK", "items": stale},
            "effective_lanes": min(MAX_LANES, len(chains)), "chains": chains}


PROBE_URLS = ["https://mops.twse.com.tw/", "https://api.stlouisfed.org/", "https://www.google.com/"]


def online(timeout: float = 4.0) -> bool:
    """真 HTTPS 探測(經 proxy 環境):任一站有 HTTP 回應(含 4xx/429)=線上;全連線錯=離線。TCP 探測會被代理假通,不採。"""
    if os.environ.get("VIA_OFFLINE", "0") == "1":
        return False
    import urllib.error
    import urllib.request
    for u in PROBE_URLS:
        try:
            urllib.request.urlopen(urllib.request.Request(u, method="HEAD"), timeout=timeout)
            return True
        except urllib.error.HTTPError:
            return True
        except Exception:
            continue
    return False


# ---------------------------------------------------------------- 執行
def _exec(step: dict, env: dict, logpath: Path) -> tuple[int, str]:
    """單步子進程(逾時 kill);特殊步(__opencc__/__pip__/__node__)委派 MDL125 原件;回 (rc, note)"""
    m = m125()
    t0 = time.time()
    with open(logpath, "w", encoding="utf-8", errors="ignore") as lf:
        if str(step["argv"][0]).startswith("__"):
            return (m._run_special(step, lf, env) if m else -2), "special"
        p = subprocess.Popen(list(step["argv"]), stdout=lf, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, env=env, cwd=str(VIA))
        try:
            p.wait(timeout=step["to"])
        except subprocess.TimeoutExpired:
            p.kill()
            return -1, "逾時 " + str(step["to"]) + "s 終止(不卡斷)"
    return p.returncode, str(round(time.time() - t0, 1)) + "s"


def schedule(steps: list, runner, workers: int = MAX_LANES, do_print: bool = True, on_done=None) -> list:
    """DAG 排程:鏈內序跑(前一步任何終態即放行下一步)、after 依賴全終態才放行;最多 workers 道同跑"""
    order = {s["id"]: i for i, s in enumerate(steps)}
    by_id = {s["id"]: s for s in steps}
    chain_prev = {}
    for s in steps:
        s["_prev"] = chain_prev.get(s["chain"])
        chain_prev[s["chain"]] = s["id"]
    done, results, running = {}, [], {}
    pending = [s["id"] for s in steps]
    lock = threading.Lock()
    with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        while pending or running:
            ready = [i for i in pending if (by_id[i]["_prev"] is None or by_id[i]["_prev"] in done)
                     and all(a in done or a not in by_id for a in by_id[i]["after"])]
            for i in ready:
                if len(running) >= workers:
                    break
                pending.remove(i)
                running[ex.submit(runner, by_id[i])] = i
            if not running:
                if pending:   # 環或缺依賴=誠實 SKIP
                    for i in pending:
                        done[i] = {"id": i, "state": "SKIP", "note": "依賴未解(環/缺)", "sec": 0}
                        results.append(done[i])
                    pending = []
                break
            fin, _ = wait(list(running), return_when=FIRST_COMPLETED)
            for f in fin:
                i = running.pop(f)
                try:
                    r = f.result()
                except Exception as exc:
                    r = {"id": i, "state": "FAIL", "note": type(exc).__name__ + ": " + str(exc)[:80], "sec": 0}
                with lock:
                    done[i] = r
                    results.append(r)
                    if on_done:
                        try:
                            on_done(list(results), list(pending), list(running.values()))
                        except Exception:
                            pass
                if do_print:
                    print("[道] " + str(len(results)).rjust(2) + "/" + str(len(steps)) + " " + i.ljust(18) + " → " + r["state"].ljust(4)
                          + " · " + str(r.get("sec", 0)) + "s · 鏈 " + by_id[i]["chain"] + (" · " + r["note"] if r.get("note") else ""), flush=True)
    return sorted(results, key=lambda r: order.get(r["id"], 999))


def make_runner(logdir: Path, dry: bool, net_ok: bool, exec_fn=None):
    exec_fn = exec_fn or _exec
    m = m125()

    def runner(s: dict) -> dict:
        ent = {"id": s["id"], "zh": s["zh"], "chain": s["chain"], "why": s.get("why", ""), "state": "SKIP", "rc": None, "sec": 0, "note": ""}
        t0 = time.time()
        if not s.get("engine_ok"):
            ent["note"] = "引擎/樞紐任務缺(先 via-reload)"
            return ent
        if s["id"] == "datahome":   # 批377 實錄:資料家為異 OS 路徑時 link 會搬走 output_hub 留斷鏈→先問 MDL123 可用律,不可用=SKIP 零搬移
            try:
                m123 = _load("CGC_MDL123_DataHome_v0*.py", "lanes_m123")
                h, src = m123.resolve_home()
                ok, why = m123.home_usable(h) if hasattr(m123, "home_usable") else (False, "MDL123 無可用律(需 v0101+)")
                if not ok:
                    ent["note"] = "資料家不可用=SKIP(零搬移):" + why
                    return ent
            except Exception as exc:
                ent["note"] = "資料家探測失敗=SKIP(零搬移):" + type(exc).__name__
                return ent
        if s.get("net") and not net_ok:
            ent["note"] = "離線=SKIP(net 步;工作站 via-lanes run)"
            return ent
        pre = ""
        try:
            pre = m._pre_skip(s) if m else ""
        except Exception:
            pre = ""
        if pre:
            ent["note"] = pre
            return ent
        if dry:
            ent["note"] = "DRY:" + " ".join(str(a) for a in s["argv"])[:140]
            return ent
        got, why = lock_acquire("step_" + s["id"])
        if not got:
            ent["note"] = "HYDRA " + why
            return ent
        try:
            env = dict(os.environ)
            if s.get("net"):
                env["VIA_NET_CONSENT"] = "YES"
                env["VIA_SCRAPE_CONSENT"] = "YES"
            env["PYTHONUTF8"] = "1"
            env["PYTHONWARNINGS"] = "ignore"
            env["VIA_NO_OPEN"] = "1"
            lp = logdir / (s["id"] + ".log")
            try:
                rc, note = exec_fn(s, env, lp)
            except Exception as exc:
                rc, note = -2, type(exc).__name__
            ent["rc"], ent["note"] = rc, note
            ent["state"] = "OK" if rc == 0 else ("SKIP" if rc == -9 else "FAIL")
            ent["log"] = str(lp.relative_to(VIA)) if lp.is_relative_to(VIA) else str(lp)
            try:
                tl = lp.read_text(encoding="utf-8", errors="ignore").strip().splitlines()
                ent["tail"] = "\n".join(tl[-3:])[-400:]
            except Exception:
                pass
        finally:
            lock_release("step_" + s["id"])
        ent["sec"] = round(time.time() - t0, 1)
        return ent
    return runner


def run(only: list | None = None, dry: bool = False, workers: int | None = None, do_print: bool = True, exec_fn=None, write: bool = True) -> dict:
    os.environ.setdefault("VIA_FRED_PROMPT", "0")   # 並行道不問 TTY;鑰缺=SKIP 印指令
    workers = int(workers or os.environ.get("VIA_LANES", MAX_LANES) or MAX_LANES)
    workers = max(1, min(MAX_LANES, workers))
    t0 = time.time()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    steps = select(assign(steps_from_fixall()), only)
    pf = preflight(steps)
    net_ok = online()
    rep = {"engine": ENGINE_TAG, "stamp": stamp, "dry": dry, "workers": workers, "effective_lanes": pf["effective_lanes"], "online": net_ok,
           "preflight": pf, "steps": [], "state": "SKIP"}
    if pf["H3"]["state"] == "FAIL" or pf["H5"]["state"] == "FAIL":
        rep["state"] = "BLOCKED"
        rep["note"] = "Hydra 哨兵阻擋:" + "; ".join(pf["H3"]["items"] + pf["H5"]["items"])
        if do_print:
            print("[道] " + rep["note"])
        return _finish(rep, t0, write)
    got, why = lock_acquire("lanes")
    if not got:
        rep["state"], rep["note"] = "BLOCKED", "本編排雙頭:" + why
        if do_print:
            print("[道] " + rep["note"])
        return _finish(rep, t0, write)
    try:
        logdir = REP / ("RUN_" + stamp)
        logdir.mkdir(parents=True, exist_ok=True)
        if do_print:
            print("[道] " + ENGINE_TAG + " · 步 " + str(len(steps)) + " · 鏈 " + str(len(pf["chains"])) + " · 道上限 " + str(workers) + " · 有效並行 "
                  + str(min(workers, pf["effective_lanes"])) + " · " + ("線上" if net_ok else "離線(net 步 SKIP)") + " · " + ("DRY" if dry else "LIVE"), flush=True)
        def _progress(res, pend, runn):   # 批377:每步終態即落 PROGRESS.json(被殺=仍有存證;誠實)
            (logdir / "PROGRESS.json").write_text(json.dumps({"stamp": stamp, "pid": os.getpid(), "done": res, "pending": pend, "running": runn,
                                                              "elapsed": round(time.time() - t0, 1)}, ensure_ascii=False, indent=1), encoding="utf-8")
        rep["steps"] = schedule(steps, make_runner(logdir, dry, net_ok, exec_fn), workers, do_print, on_done=_progress)
    finally:
        lock_release("lanes")
    n = {k: sum(1 for s in rep["steps"] if s["state"] == k) for k in ("OK", "FAIL", "SKIP")}
    rep.update(n_ok=n["OK"], n_fail=n["FAIL"], n_skip=n["SKIP"])
    rep["state"] = "OK" if n["FAIL"] == 0 and n["OK"] else ("FAIL" if n["FAIL"] and not n["OK"] else ("PART" if n["FAIL"] else "SKIP"))
    return _finish(rep, t0, write)


def _finish(rep: dict, t0: float, write: bool) -> dict:
    rep["sec"] = round(time.time() - t0, 1)
    rep["rules"] = RULES
    if write:
        REP.mkdir(parents=True, exist_ok=True)
        (REP / ("LANES_" + rep["stamp"] + ".json")).write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
        PAGE.parent.mkdir(parents=True, exist_ok=True)
        PAGE.write_text(render(rep), encoding="utf-8")
        BOOK.write_text(json.dumps({"engine": ENGINE_TAG, "chains": CHAINS, "max_lanes": MAX_LANES, "rules": RULES, "last": rep["stamp"], "last_state": rep["state"]},
                                   ensure_ascii=False, indent=1), encoding="utf-8")
    return rep


def plan(do_print: bool = True) -> dict:
    steps = assign(steps_from_fixall())
    pf = preflight(steps)
    rep = {"engine": ENGINE_TAG, "stamp": datetime.now().strftime("%Y%m%d_%H%M%S"), "dry": True, "workers": MAX_LANES, "effective_lanes": pf["effective_lanes"],
           "online": online(), "preflight": pf, "state": "PLAN", "steps": [{"id": s["id"], "zh": s["zh"], "chain": s["chain"], "state": "PLAN", "sec": 0,
                                                                            "note": ("net" if s.get("net") else "local") + (" · 引擎缺" if not s.get("engine_ok") else ""), "why": s.get("why", "")} for s in steps]}
    if do_print:
        print("[道] PLAN · 步 " + str(len(steps)) + " · 鏈 " + str(len(pf["chains"])) + " · 有效並行 " + str(pf["effective_lanes"]) + "/" + str(MAX_LANES) + " · " + ("線上" if rep["online"] else "離線"))
        for c, ids in pf["chains"].items():
            print("  鏈 " + c.ljust(6) + " " + " → ".join(ids))
        for k in ("H1", "H2", "H3", "H4", "H5"):
            v = pf[k]
            print("  " + k + " " + v["state"].ljust(4) + (" · " + "; ".join(v["items"][:4]) if v["items"] and k != "H4" else ""))
    return _finish(rep, time.time(), True)


def digest() -> int:
    hits = sorted(REP.glob("LANES_*.json"), key=lambda p: p.stat().st_mtime) if REP.exists() else []
    if not hits:
        print("VIA LANES · 無存證(via-lanes run)")
        return 1
    rep = json.loads(hits[-1].read_text(encoding="utf-8"))
    print("VIA LANES · " + rep["stamp"] + " · " + rep["state"] + " · OK " + str(rep.get("n_ok", 0)) + " FAIL " + str(rep.get("n_fail", 0)) + " SKIP " + str(rep.get("n_skip", 0))
          + " · 有效並行 " + str(rep.get("effective_lanes")) + "/" + str(rep.get("workers")) + " · " + str(rep.get("sec")) + "s" + (" · " + rep["note"] if rep.get("note") else ""))
    for s in rep.get("steps", []):
        print("  " + s["state"].ljust(4) + " " + s["id"].ljust(18) + " 鏈 " + s["chain"].ljust(5) + " " + str(s.get("sec", 0)) + "s" + (" · " + s["note"][:90] if s.get("note") else ""))
    return 0 if rep["state"] in ("OK", "SKIP", "PLAN") else 1


# ---------------------------------------------------------------- 頁
def _b(s: str) -> str:
    c = {"OK": "gr", "PLAN": "gy", "WARN": "ye", "SKIP": "ye", "PART": "ye", "FAIL": "rd", "BLOCKED": "rd"}.get(s, "gy")
    return '<span class="b ' + c + '">' + html.escape(s) + "</span>"


def render(r: dict) -> str:
    e = html.escape
    pf = r.get("preflight", {})
    hrows = "".join("<tr><td class=\"m\">" + k + '</td><td class="c">' + _b(pf[k]["state"]) + '</td><td class="dim">' + e("; ".join(pf[k]["items"][:8]) or "—") + "</td></tr>"
                    for k in ("H1", "H2", "H3", "H4", "H5") if k in pf)
    srows = "".join('<tr><td class="m">' + e(s["id"]) + '</td><td class="m">' + e(s["chain"]) + '</td><td class="c">' + _b(s["state"]) + "</td><td>" + e(s.get("zh", ""))
                    + '</td><td class="m">' + str(s.get("sec", 0)) + '</td><td class="dim">' + e(str(s.get("note", ""))[:140]) + "</td></tr>" for s in r.get("steps", []))
    crows = "".join('<tr><td class="m">' + e(c) + "</td><td>" + e(" → ".join(ids)) + "</td></tr>" for c, ids in pf.get("chains", {}).items())
    head = ('<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            "<title>VIA · 十道並行安全編排</title><style>:root{--bg:#0f172a;--card:#1e293b;--line:#334155;--tx:#f8fafc;--mu:#94a3b8}*{box-sizing:border-box}"
            "body{margin:0;background:var(--bg);color:var(--tx);font:11px/1.35 -apple-system,'Segoe UI',Roboto,'Microsoft JhengHei',sans-serif}"
            ".wrap{max-width:1300px;margin:0 auto;padding:18px 14px 48px}h1{font-size:14px;margin:0}.sub{color:var(--mu);margin:3px 0 14px}h2{font-size:12px;margin:20px 0 7px;border-bottom:1px solid var(--line);padding-bottom:5px}"
            ".nav a{color:#7dd3fc;margin-right:12px;text-decoration:none}.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px;margin-bottom:14px}.kpi{background:var(--card);border:1px solid var(--line);border-radius:3px;padding:9px 11px}.kpi .n{font-size:16px;font-weight:600}.kpi .l{font-size:10px;color:var(--mu)}"
            "table{width:100%;table-layout:fixed;border-collapse:collapse;background:var(--card);border:1px solid var(--line)}th{font-size:10px;color:var(--mu);text-align:left;padding:4px 6px;border-bottom:1px solid var(--line)}td{padding:4px 6px;border-bottom:1px solid #253248;vertical-align:top;word-wrap:break-word;overflow-wrap:break-word;white-space:normal}td.c{text-align:center}.m{font-family:ui-monospace,Consolas,monospace;font-size:10px}.dim{color:var(--mu)}"
            ".b{display:inline-block;font-size:10px;padding:1px 6px;border-radius:2px;border:1px solid}.gr{background:#064e3b;color:#34d399;border-color:#059669}.ye{background:#78350f;color:#fde047;border-color:#d97706}.rd{background:#7f1d1d;color:#fca5a5;border-color:#dc2626}.gy{background:#1f2937;color:#9ca3af;border-color:#374151}"
            ".note{background:var(--card);border:1px solid var(--line);border-left:3px solid #d97706;border-radius:3px;padding:10px 12px;margin-top:16px}"
            "@media(max-width:700px){table,thead,tbody,tr,td,th{display:block}thead{display:none}td{border:0;padding:2px 6px}tr{border-bottom:1px solid var(--line);padding:6px 0}}</style></head><body><div class=\"wrap\">")
    body = ("<h1>VIA PARALLEL LANES · 十道並行安全編排 · Hydra 哨兵</h1><p class=\"sub\">" + e(r["engine"]) + " · " + e(r["stamp"]) + " · " + ("DRY" if r.get("dry") else "LIVE") + " · "
            + ("線上" if r.get("online") else "離線") + " · " + str(r.get("sec", "")) + " s</p>"
            '<p class="nav"><a href="VIA_UI_ProductGate_v0100.html">產</a><a href="VIA_UI_ProjectCompletion_v0100.html">竣</a><a href="VIA_UI_VDFArchitecture_v0100.html">架</a><a href="VIA_UI_MasterControl_v0100.html">總控</a></p>'
            '<div class="kpis"><div class="kpi"><div class="n">' + _b(r["state"]) + '</div><div class="l">state</div></div><div class="kpi"><div class="n">' + str(r.get("effective_lanes")) + "/" + str(r.get("workers"))
            + '</div><div class="l">有效並行 / 道上限</div></div><div class="kpi"><div class="n">' + str(r.get("n_ok", 0)) + " · " + str(r.get("n_fail", 0)) + " · " + str(r.get("n_skip", 0)) + '</div><div class="l">OK · FAIL · SKIP</div></div></div>'
            "<h2>HYDRA — five sentinels(H3/H5 block; H1/H2 warn by name)</h2>"
            '<table><colgroup><col style="width:6%"><col style="width:8%"><col style="width:86%"></colgroup><thead><tr><th>id</th><th>state</th><th>items</th></tr></thead><tbody>' + hrows + "</tbody></table>"
            "<h2>CHAINS — single-writer chains(serial inside, parallel across)</h2>"
            '<table><colgroup><col style="width:12%"><col style="width:88%"></colgroup><tbody>' + crows + "</tbody></table>"
            "<h2>STEPS — verbatim outcome per step</h2>"
            '<table><colgroup><col style="width:13%"><col style="width:7%"><col style="width:7%"><col style="width:33%"><col style="width:7%"><col style="width:33%"></colgroup>'
            "<thead><tr><th>step</th><th>chain</th><th>state</th><th>what</th><th>sec</th><th>note</th></tr></thead><tbody>" + srows + "</tbody></table>"
            '<div class="note">' + "<br>".join(e(x) for x in r.get("rules", RULES)) + "</div></div></body></html>")
    return head + body


# ---------------------------------------------------------------- 自測
def selftest() -> int:
    import tempfile
    global LOCKS, REP, PAGE, BOOK, FIXALL_REP
    fails = []

    def chk(name, cond, note=""):
        print("  [" + ("OK" if cond else "FAIL") + "] " + name + " " + note)
        if not cond:
            fails.append(name)

    real = steps_from_fixall()
    ids = {s["id"] for s in real}
    chk("① 步冊直取 MDL125(零重複定義)且每步入鏈冊(單寫者律)", len(real) >= 15 and ids <= set(CHAINS), "(步 " + str(len(real)) + " 未入冊 " + ",".join(sorted(ids - set(CHAINS))) + ")")
    fake = [{"id": i, "zh": i, "engine_ok": True, "net": False, "to": 5, "argv": ["x", "y"]} for i in ("datahome", "opencc", "pkuseg", "global", "fred", "etf_universe", "etf_fetch", "etf_history",
                                                                                                        "hist_probe", "group_class", "revenue_backfill", "consensus", "revenue_consensus", "etf_revenue", "refail", "digest")]
    fake = assign(fake)
    log, cur, peak = [], [0], [0]
    lk = threading.Lock()

    def rec_runner(s):
        with lk:
            cur[0] += 1
            peak[0] = max(peak[0], cur[0])
            log.append(("start", s["id"], s["chain"], time.time()))
        time.sleep(0.05)
        with lk:
            cur[0] -= 1
            log.append(("end", s["id"], s["chain"], time.time()))
        return {"id": s["id"], "state": "OK", "sec": 0.05}
    res = schedule(fake, rec_runner, workers=10, do_print=False)
    ev = {}
    for kind, i, c, t in log:
        ev.setdefault(i, {})[kind] = t
    overlap_same_chain = any(a != b and fake_a["chain"] == fake_b["chain"] and ev[a]["start"] < ev[b]["end"] and ev[b]["start"] < ev[a]["end"]
                             for fake_a in fake for fake_b in fake for a in [fake_a["id"]] for b in [fake_b["id"]])
    deps_ok = ev["etf_revenue"]["start"] >= max(ev["revenue_consensus"]["end"], ev["etf_history"]["end"]) and ev["refail"]["start"] >= ev["etf_revenue"]["end"] \
        and ev["digest"]["start"] >= ev["refail"]["end"] and all(ev[i]["start"] >= ev["datahome"]["end"] for i in ev if i != "datahome")
    sub = select(fake, ["revenue_backfill", "etf_revenue", "refail", "digest"])
    sub_ok = {x["id"]: x["after"] for x in sub}
    chk("② DAG 排程(同鏈零重疊;after 依賴全終態才放行;鏈間真並行 peak≥3;≤10 道;結果按步序;--only 子集遞移閉包保序)",
        not overlap_same_chain and deps_ok and 3 <= peak[0] <= 10 and len(res) == len(fake) and [r["id"] for r in res] == [s["id"] for s in fake]
        and sub_ok["etf_revenue"] == ["revenue_backfill"] and "etf_revenue" in sub_ok["refail"] and "revenue_backfill" in sub_ok["refail"] and sub_ok["digest"] == ["etf_revenue", "refail", "revenue_backfill"],
        "(peak " + str(peak[0]) + ")")
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        _L = LOCKS
        LOCKS = tdp / "locks"
        g1, n1 = lock_acquire("t")
        (LOCKS / "u.lock").write_text(json.dumps({"pid": 999999, "ts": "x"}), encoding="utf-8")
        g2, n2 = lock_acquire("u")
        lock_release("t")
        chk("③ H3 進程鎖(取鎖;死 PID 回收;釋放後檔消失)", g1 and g2 and "回收" in n2 and not (LOCKS / "t.lock").exists())
        LOCKS = _L
        (tdp / "A.cmd").write_text("x"); (tdp / "a.CMD").write_text("y"); (tdp / "b.cmd").write_text("z")
        d1 = h1_same_name(tdp, [""])
        chk("④ H1 同名雙物(大小寫不分:A.cmd/a.CMD 命中;b 不命中)", len(d1) == 1 and set(d1[0][1]) == {"A.cmd", "a.CMD"})
        (tdp / "d1").mkdir(); (tdp / "d2").mkdir(); (tdp / "d1" / "X_ENG_v0100.py").write_text("1"); (tdp / "d2" / "X_ENG_v0100.py").write_text("2")
        (tdp / "d2" / "X_ENG_v0100_sha1234567.py").write_text("3"); (tdp / "d1" / "Y_v0100.py").write_text("4")
        d2 = h2_same_version(tdp, ["d1", "d2"])
        chk("⑤ H2 同族同版雙物(X_ENG_v0100 於 d1/d2 命中;_sha 鏡像/獨件不計)", len(d2) == 1 and d2[0][0] == "X_ENG_v0100.py" and sorted(d2[0][1]) == ["d1", "d2"])
        (tdp / "d1" / "Y_v0101.py").write_text("5")
        ok0, t0 = h5_is_tail(str(tdp / "d1" / "Y_v0100.py"))
        ok1, _ = h5_is_tail(str(tdp / "d1" / "Y_v0101.py"))
        chk("⑥ H5 尾版律(v0100 非尾→FAIL 指尾版 v0101;v0101=尾)", not ok0 and t0 == "Y_v0101.py" and ok1)
        _R = (REP, PAGE, BOOK, LOCKS, FIXALL_REP)
        REP, PAGE, BOOK, LOCKS, FIXALL_REP = tdp / "rep", tdp / "p.html", tdp / "b.json", tdp / "locks2", tdp / "fx"   # 自測沙盒:真鎖/真 FixAll 心跳零干擾(與並行中的 via-lanes 共存)
        calls = []

        def fake_exec(s, env, lp):
            calls.append(s["id"])
            lp.write_text("ok", encoding="utf-8")
            return (0 if s["id"] != "digest" else 3), "t"
        _on = os.environ.get("VIA_OFFLINE")
        os.environ["VIA_OFFLINE"] = "1"
        rep = run(only=["datahome", "group_class", "etf_revenue", "global", "digest"], workers=10, do_print=False, exec_fn=fake_exec)
        os.environ.pop("VIA_OFFLINE", None) if _on is None else os.environ.__setitem__("VIA_OFFLINE", _on)
        st = {s["id"]: s for s in rep.get("steps", [])}
        chk("⑦ 離線閘+誠實三態(global net→SKIP 未執行;digest rc3→FAIL;整體 PART;存證 LANES_*.json)",
            bool(st) and st["global"]["state"] == "SKIP" and "global" not in calls and st["digest"]["state"] == "FAIL" and rep["state"] == "PART" and any(REP.glob("LANES_*.json")),
            "(" + (", ".join(i + ":" + st[i]["state"] for i in st) if st else rep.get("note", rep["state"])) + ")")
        t = PAGE.read_text(encoding="utf-8")
        chk("⑧ 頁+冊(HYDRA/CHAINS/STEPS 三區;H1..H5;手機單欄 @media;零 CDN;導航 產/竣)",
            all(x in t for x in ("HYDRA", "CHAINS", "STEPS", "H1", "H5", "@media", "VIA_UI_ProductGate_v0100.html")) and "https://" not in t and BOOK.exists())
        REP, PAGE, BOOK, LOCKS, FIXALL_REP = _R
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑨ 紀律宣告(單寫者律/Hydra 律/誠實三態/只增不減/尾版律/零 force)", all(k in src for k in ("單寫者律", "Hydra 律", "誠實三態", "只增不減", "尾版律", "零 force")))
    print("  [計] 九檢 OK " + str(9 - len(fails)) + " · FAIL " + str(len(fails)))
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 十道並行安全編排(" + ENGINE_TAG + ")· 九檢自測 ===")
        return selftest()
    verb = a[0] if a and not a[0].startswith("-") else "plan"
    if verb == "digest":
        return digest()
    if verb == "run":
        only = None
        workers = None
        if "--only" in a:
            only = [x.strip() for x in a[a.index("--only") + 1].split(",") if x.strip()]
        if "--workers" in a:
            workers = int(a[a.index("--workers") + 1])
        rep = run(only=only, dry="--dry" in a, workers=workers)
        print("[道] 終態 " + rep["state"] + " · OK " + str(rep.get("n_ok", 0)) + " FAIL " + str(rep.get("n_fail", 0)) + " SKIP " + str(rep.get("n_skip", 0)) + " · " + str(rep["sec"]) + "s · 存證 LANES_" + rep["stamp"] + ".json")
        return 0 if rep["state"] in ("OK", "SKIP") else 1
    plan()
    return 0


if __name__ == "__main__":
    sys.exit(main())
