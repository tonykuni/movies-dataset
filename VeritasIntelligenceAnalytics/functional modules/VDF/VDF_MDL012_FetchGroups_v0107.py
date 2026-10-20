#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [接線 2026-10-20] 本檔 = 工作站分支 workstation-20261020 的同號原文(main 沒有此版,不撞號)。工作站 v0106(自測鏈隔離活資料樞)不搬:
#   main v0106 已在前版鏈自測期間封倉(_SEAL_REPO_HUB),同一目的;本檔前版照 glob 取 main v0106。
"""VDF_MDL012_FetchGroups v0107 — 薄尾:清單引擎先跑 → 依 DuckDB 庫分道 3~5 流程並行擷取(CPU · DRAM · TEMP 守門)· 頁「並行擷取 · USER-TEST」· usertest 功能鍵實測

操作員令(2026-10-12 原話):「找到自動更新台股所有個股清單引擎 及主動式台股ETF清單生成引擎先跑後 後面的擷取動作所有動作都要被PS加速器100%覆蓋
  在CPU可容忍 記憶體有限 TEMP強力支援下進行3~5流程同步引擎其跑的動作要考量CPU DRAM+TEMP的能力上限 … 然後實測修復成功後立刻跳出HTML U/I上面有驗證成功後的結果 VDF完美收工」
  「下一步一糗收尾VDF VCGC 自動跳出HTNL U/I最佳畫面結構 功能鍵USER-TEST 都有了正常功能」
實錄(v0100 cmd_run):族群引擎經 MDL008 run 一支接一支的子行程(一條龍);擷取冊上每支擷取引擎都 needs 009 · 010:
  009 = VDF_MDL009_TWStockList(自動更新台股所有個股清單)· 010 = VDF_MDL010_ActiveETFList(主動式台股 ETF 清單)。
本版(v0100–v0106 一字不動):
  run(預設就走並行;--serial = 前版一條龍):
    ① 清單引擎 009 · 010 先跑(--no-lists-first 關;紅就停 rc 5,清單是全部引擎的前提)
    ② 其餘族群分道:同 DuckDB 庫 · 同類(vake / parquet)· 同引擎 · 引擎相依 → 同一道;道內照 needs 拓撲一支支跑;不同道同時跑(--jobs 1~5,auto = CPU 數 − 1)
    ③ 守門:起每支子行程前量 CPU% · DRAM 可用 · TEMP 可用(psutil 有就用,沒有退 stdlib);超限就等(--cpu-max · --mem-min-gb · --temp-min-gb · --govern-wait 上限)
    ④ TEMP 為主:子行程環境補 VIA_TEMP_ROOT · VIA_DUCKDB_TEMP_DIR(CGC_MDL262 DuckTempHook 的規則)· VIA_DUCKDB_MEM_PCT = 50 ÷ 流程數(記憶體有限 → 落 TEMP)
    ⑤ 子行程直接從 MDL008 尾版起(同 run_v0107 的 _child 契約與列上 timeout_s 規則);不經 run_v0107 的模組 __file__ 換裝 —— 那不是執行緒安全的
    ⑥ 一筆 fg_runs + sync_catalog(同 v0100);_fetch_groups/PARALLEL_latest.json(+ PARALLEL_runs.jsonl 只增)
  ui:頁多一頁「並行擷取 · USER-TEST」(結果掛頁);左面板多「並行流程」選項與「並行跑族群」「USER-TEST」鈕(頁不執行指令,只出可貼的指令)
  usertest:建頁(預設在報告夾 VIA_Reports/vdf/ui,不碰已追蹤的正式頁)→ 靜態驗(每個功能鍵有處理分支 · 每頁籤有頁 · 快照可解析 · 輸入 id 唯一)
    → 瀏覽器實測(找得到 Chromium / Chrome / Edge 就 headless 逐鍵點、讀 #cmd、切頁籤、全選 / 清除;找不到照實說)
    → 報告夾 VDF_FetchGroups_USERTEST_latest.json → 重建頁(結果掛在頁上;之後 ui 重建正式頁也掛同一份)
只收 VCGC 呼叫;零網路(連網全在 MDL008 子行程、live 要雙閘);不碰 TA-Lib。
交接案:vdf_fetch_groups_v0100–v0105 六案的標記(v0106 的 [計] 行)在本版前版鏈裡照印(TAG 不蓋);新案 vdf_fetch_groups_v0107 釘本版 [計] 行。
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

import concurrent.futures
import contextlib
import html
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REG = HERE.parents[1] / "supportive modules" / "registry"
TAG_V0107 = f"VDF_MDL012_FetchGroups v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
LIST_ENGINES_V0107 = ("009", "010")       # 009 = MDL009 台股全市場清單(自動更新)· 010 = MDL010 主動式台股 ETF 清單;全部擷取引擎的前提
JOBS_RANGE_V0107 = (1, 5)                 # 操作員令 3~5 流程;auto = clamp(CPU 數 − 1, 1, 5)
LIMITS_V0107 = {"cpu_max": 85.0, "mem_min_gb": 2.0, "temp_min_gb": 5.0, "interval_s": 5.0, "max_wait_s": 600.0}
PARALLEL_LATEST = "PARALLEL_latest.json"
PARALLEL_RUNS = "PARALLEL_runs.jsonl"
USERTEST_LATEST = "VDF_FetchGroups_USERTEST_latest.json"
PAGE_ID_V0107 = "pg-par"
PAGE_TITLE_V0107 = "並行擷取 · USER-TEST"


def _vnum_v0107(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _prior_path() -> Path:
    """前版 = 同家族比本檔小的最大版號(不釘名,避免 PINVER)。"""
    me = _vnum_v0107(__file__)
    hits = [p for p in HERE.glob("VDF_MDL012_FetchGroups_v*.py") if 0 <= _vnum_v0107(p) < me]
    return max(hits, key=_vnum_v0107)


PRIOR_PATH = _prior_path()
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0107", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    """薄尾轉接:本版沒蓋的公開名稱照前版(TAILAPI)。"""
    return getattr(PRIOR, name)


def _chain() -> list:
    mods, m = [], PRIOR
    while m is not None and m not in mods:
        mods.append(m)
        m = vars(m).get("PRIOR")
    return mods


def _owner(*names):
    """沿前版鏈找「這些名稱都定義在自己模組裡」的那一版(後版抄進全域或換裝的不算)。"""
    for m in _chain():
        if all(callable(vars(m).get(n)) and getattr(vars(m).get(n), "__module__", None) == m.__name__ for n in names):
            return m
    return None


V0100 = _owner("cmd_run", "_ctx", "_con_catalog")          # 擷取 · 目錄 · 守門(gates_open)本體
V0101 = _owner("build_page", "_nav_links", "workflow_svg")  # 頁產生器本體(render · gather 已被後版換裝 → 用沒被換的名字找)
V0105 = _owner("relayout", "left_panel", "backup_info")     # 左面板輸入控制 · 收尾備份
_RENDER_V0105 = vars(V0105)["render_v0105"] if V0105 is not None else None
_RENDER_V0101 = vars(V0105)["_RENDER_V0101"] if V0105 is not None else None

for _n in dir(PRIOR):
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = getattr(PRIOR, _n)
USERTEST_DIR = Path(str(getattr(PRIOR, "OUT_DIR"))) if getattr(PRIOR, "OUT_DIR", None) else None   # v0102 報告夾(VIA_Reports/vdf/ui,對接快照也在那);沒有就放頁旁


def usertest_path(out: Path) -> Path:
    return (USERTEST_DIR / USERTEST_LATEST) if USERTEST_DIR is not None else Path(out).with_name(USERTEST_LATEST)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(p: Path) -> dict:
    try:
        return json.loads(Path(p).read_text(encoding="utf-8")) if Path(p).is_file() else {}
    except (OSError, ValueError):
        return {}


# ---------------------------------------------------------------- 資源 · TEMP · 守門
def temp_plan() -> dict:
    """TEMP 根 · DuckDB 暫存根:照 CGC_MDL262 DuckTempHook 的規則(VIA_TEMP_ROOT · VIA_DUCKDB_TEMP_DIR);鉤有沒有裝進境由 via-vcgc run CGC_MDL262_DuckTempHook status 報。"""
    info = {"mdl262": None, "temp_root": None, "duck_temp_base": None}
    hits = sorted(REG.glob("CGC_MDL262_DuckTempHook_v*.py"), key=_vnum_v0107)
    if hits:
        try:
            spec = importlib.util.spec_from_file_location("mdl262_for_mdl012_v0107", hits[-1])
            m = importlib.util.module_from_spec(spec)
            with contextlib.redirect_stdout(io.StringIO()):
                spec.loader.exec_module(m)
            info.update(mdl262=hits[-1].name, temp_root=str(m.temp_root()), duck_temp_base=str(m.duck_temp_base()))
        except Exception as exc:                                        # 鉤載不進來照實記,規則退本檔內建(同一條)
            info["mdl262"] = f"{hits[-1].name} 載入失敗 {type(exc).__name__}"
    if not info["temp_root"]:
        root = os.environ.get("VIA_TEMP_ROOT") or str(Path(os.environ.get("LOCALAPPDATA") or tempfile.gettempdir()) / "Temp" / "VIA_progress")
        info["temp_root"] = root
        info["duck_temp_base"] = os.environ.get("VIA_DUCKDB_TEMP_DIR") or str(Path(root) / "duckdb")
    return info


def resources(temp_base=None) -> dict:
    """CPU% · DRAM 可用 / 總量 GB · TEMP 可用 GB。psutil 有就用;沒有退 os.getloadavg / proc meminfo;量不到的回 None(不擋)。"""
    r = {"ts": _now_iso(), "cpus": os.cpu_count(), "cpu_pct": None, "mem_avail_gb": None, "mem_total_gb": None,
         "temp_free_gb": None, "temp_base": str(temp_base) if temp_base else None, "via": "stdlib"}
    try:
        import psutil
        r["cpu_pct"] = float(psutil.cpu_percent(interval=0.2))
        vm = psutil.virtual_memory()
        r["mem_avail_gb"], r["mem_total_gb"] = round(vm.available / 2 ** 30, 2), round(vm.total / 2 ** 30, 2)
        r["via"] = "psutil " + str(getattr(psutil, "__version__", ""))
    except Exception:
        try:
            if hasattr(os, "getloadavg"):
                r["cpu_pct"] = round(100.0 * os.getloadavg()[0] / max(1, os.cpu_count() or 1), 1)
            mi = Path("/proc/meminfo")
            if mi.is_file():
                kv = {}
                for ln in mi.read_text(encoding="utf-8").splitlines():
                    parts = ln.replace(":", " ").split()
                    if len(parts) >= 2 and parts[1].isdigit():
                        kv[parts[0]] = int(parts[1])
                r["mem_avail_gb"] = round(kv.get("MemAvailable", 0) / 2 ** 20, 2)
                r["mem_total_gb"] = round(kv.get("MemTotal", 0) / 2 ** 20, 2)
        except Exception:
            pass
    if temp_base:
        try:
            p = Path(temp_base)
            while not p.exists() and p.parent != p:
                p = p.parent
            r["temp_free_gb"] = round(shutil.disk_usage(p).free / 2 ** 30, 2)
        except Exception:
            pass
    return r


def over_limits(sample: dict, limits: dict) -> list:
    why = []
    c, m, t = sample.get("cpu_pct"), sample.get("mem_avail_gb"), sample.get("temp_free_gb")
    if c is not None and limits.get("cpu_max") is not None and c > limits["cpu_max"]:
        why.append(f"CPU {c:.0f}% > {limits['cpu_max']:.0f}%")
    if m is not None and limits.get("mem_min_gb") is not None and m < limits["mem_min_gb"]:
        why.append(f"DRAM 可用 {m} GB < {limits['mem_min_gb']} GB")
    if t is not None and limits.get("temp_min_gb") is not None and t < limits["temp_min_gb"]:
        why.append(f"TEMP 可用 {t} GB < {limits['temp_min_gb']} GB")
    return why


def governor_wait(limits: dict, sampler=None, sleeper=None, temp_base=None, log=None) -> dict:
    """起下一支子行程前守門:超限就等 interval_s 再量,最多 max_wait_s(到了照跑、記 forced)。回 waited_s · forced · reasons · sample。"""
    sampler = sampler or (lambda: resources(temp_base))
    sleeper = sleeper or time.sleep
    log = log or (lambda s: print(s, flush=True))
    waited, forced, reasons = 0.0, False, []
    s = sampler()
    while True:
        why = over_limits(s, limits)
        if not why:
            break
        if waited >= float(limits.get("max_wait_s", LIMITS_V0107["max_wait_s"])):
            forced = True
            log(f"  [守門] 等了 {waited:.0f}s 仍超限({' · '.join(why)})→ 照跑(--govern-wait 上限)")
            break
        if not reasons or reasons[-1] != " · ".join(why):
            log(f"  [守門] 等:{' · '.join(why)}")
        reasons.append(" · ".join(why))
        step = float(limits.get("interval_s", LIMITS_V0107["interval_s"]))
        sleeper(step)
        waited += step
        s = sampler()
    return {"waited_s": round(waited, 1), "forced": forced, "reasons": reasons[:20], "sample": s}


# ---------------------------------------------------------------- 分道
def _group_dbs(g: dict) -> list:
    return sorted({s["db"] for s in (g.get("sources") or []) if s.get("type") == "duckdb" and s.get("db")})


def _group_kind(g: dict) -> str:
    types = [s.get("type") for s in (g.get("sources") or [])]
    return "duckdb" if "duckdb" in types else ("vake" if "vake" in types else ("parquet" if "parquet" in types else "misc"))


def ordered_v0107(rows: list) -> list:
    """同 MDL008 ordered:依 needs 拓撲(同層照冊序);有環 = ValueError(冊錯,不猜)。不在列裡的 needs(清單引擎已先跑)當已滿足。"""
    by = {r["id"]: r for r in rows}
    done, out, pending = set(), [], list(rows)
    while pending:
        progressed = False
        for r in list(pending):
            if all(n in done or n not in by for n in (r.get("needs") or [])):
                out.append(r)
                done.add(r["id"])
                pending.remove(r)
                progressed = True
        if not progressed:
            raise ValueError("FETCH_BOOK_CYCLE: " + ",".join(r["id"] for r in pending))
    return out


def plan_lanes(book: dict, fb: dict, gids: list, as_of: str, sel_path) -> dict:
    """族群分道(不起子行程、不寫檔):同 DuckDB 庫 · 同類(vake / parquet)· 同引擎 · 引擎相依 → 同一道。
    回 {lists: 清單引擎列, lanes: [{id, groups, dbs, rows}], missing: 冊上沒有的引擎, merged: 併道理由}。"""
    parent = {g: g for g in gids}
    merged = []

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b, why):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra
            merged.append(f"{a}+{b}:{why}")

    by_db, by_kind, by_eng = {}, {}, {}
    for gid in gids:
        g = V0100.group_of(book, gid)
        dbs = _group_dbs(g)
        for db in dbs:
            by_db.setdefault(db, []).append(gid)
        if not dbs:
            by_kind.setdefault(_group_kind(g), []).append(gid)
        for e in g.get("engines") or []:
            if e not in LIST_ENGINES_V0107:
                by_eng.setdefault(e, []).append(gid)
    for db, gs in by_db.items():
        for o in gs[1:]:
            union(gs[0], o, f"同庫 {db}")
    for k, gs in by_kind.items():
        for o in gs[1:]:
            union(gs[0], o, f"同類 {k}")
    for e, gs in by_eng.items():
        for o in gs[1:]:
            union(gs[0], o, f"同引擎 {e}")
    by_id = {r["id"]: r for r in fb.get("engines", [])}
    for e, gs in by_eng.items():
        for n in (by_id.get(e) or {}).get("needs") or []:
            if n in by_eng and n not in LIST_ENGINES_V0107:
                union(gs[0], by_eng[n][0], f"{e} 需 {n}")
    lanes = {}
    for gid in gids:
        lanes.setdefault(find(gid), []).append(gid)
    rows_all = V0100.plan_rows(book, fb, gids, as_of, sel_path)
    lists = [r for r in rows_all if r["id"] in LIST_ENGINES_V0107 and not r.get("missing")]
    missing = [r["id"] for r in rows_all if r.get("missing")]
    out, names = [], {}
    for gs in lanes.values():
        rows = [r for r in V0100.plan_rows(book, fb, gs, as_of, sel_path) if not r.get("missing") and r["id"] not in LIST_ENGINES_V0107]
        dbs = {}
        for gid in gs:
            for db in _group_dbs(V0100.group_of(book, gid)):
                dbs[db] = dbs.get(db, 0) + 1
        base = max(sorted(dbs), key=lambda d: dbs[d]).rsplit(".", 1)[0] if dbs else _group_kind(V0100.group_of(book, gs[0]))
        names[base] = names.get(base, 0) + 1
        out.append({"id": base if names[base] == 1 else f"{base}#{names[base]}", "groups": gs, "dbs": sorted(dbs), "rows": rows})
    out.sort(key=lambda L: (-len(L["rows"]), L["id"]))          # 大道先起,排程較平均
    return {"lists": lists, "lanes": out, "missing": missing, "merged": merged}


# ---------------------------------------------------------------- 子行程 · 並行
def child_env(jobs: int, tp: dict, lane: str | None = None) -> dict:
    """子行程環境:同 MDL008(VIA_FROM_VCGC · PYTHONIOENCODING)+ TEMP 為主(MDL262 規則;操作員已設的不覆蓋)+ 記憶體上限按流程數分。"""
    env = dict(os.environ, VIA_FROM_VCGC="YES", PYTHONIOENCODING="utf-8", VIA_FG_JOBS=str(jobs))
    env.setdefault("VIA_TEMP_ROOT", str(tp.get("temp_root") or ""))
    env.setdefault("VIA_DUCKDB_TEMP_DIR", str(tp.get("duck_temp_base") or ""))
    env.setdefault("VIA_DUCKDB_MEM_PCT", str(max(5, 50 // max(1, int(jobs)))))
    if lane:
        env["VIA_FG_LANE"] = lane
    return env


def launch_child(mdl008: Path, r: dict, mode: str, home: Path, logs: Path, timeout: int, env: dict) -> dict:
    """同 MDL008 v0100 run 的子行程契約(_child id home mode -- args),從 MDL008 尾版起;冊列 timeout_s 比上限長就用列的(同 run_v0107)。"""
    log = logs / f"{r['id']}_{mode}.log"
    want = int(r.get("timeout_s") or 0)
    t_out = max(int(timeout), want) if want else int(timeout)
    t0 = time.time()
    try:
        p = subprocess.run([sys.executable, "-X", "utf8", str(mdl008), "_child", r["id"], str(home), mode, "--", *r.get("run_args", [])],
                           stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                           errors="replace", timeout=t_out, env=env, cwd=str(home.parent))
        rc, txt = p.returncode, p.stdout
    except subprocess.TimeoutExpired as e:
        rc, txt = 124, (e.stdout or "") if isinstance(e.stdout, str) else ""
    except OSError as e:
        rc, txt = 127, f"{type(e).__name__}: {e}"
    log.write_text(txt or "", encoding="utf-8")
    tail = [ln for ln in (txt or "").splitlines() if ln.strip()][-3:]
    return {"id": r["id"], "mdl": r.get("mdl"), "rc": rc, "sec": round(time.time() - t0, 1), "log": str(log), "tail": tail, "timeout_s": t_out}


LAUNCH = launch_child                                           # 自測換成替身(不起真子行程)


def run_parallel(plan: dict, mdl008: Path, mode: str, home: Path, logs: Path, timeout: int, jobs: int, limits, order_fn, tp: dict,
                 lists_first: bool = True, log=None) -> dict:
    """① 清單引擎先跑(紅就停)② 各道同時跑(每道一支接一支;起每支前守門)。回 lists · lanes · aborted · wall_s · events。"""
    log = log or (lambda s: print(s, flush=True))
    logs.mkdir(parents=True, exist_ok=True)
    t0, lock, events = time.time(), threading.Lock(), []
    launch = globals()["LAUNCH"]

    def one(r, lane_id, env):
        gov = governor_wait(limits, temp_base=tp.get("duck_temp_base"), log=log) if limits else None
        res = launch(mdl008, r, mode, home, logs, timeout, env)
        res["lane"] = lane_id
        res["governor"] = {k: v for k, v in gov.items() if k != "sample"} if gov else None
        with lock:
            events.append({"t": round(time.time() - t0, 1), "lane": lane_id, "id": r["id"], "rc": res.get("rc"), "sec": res.get("sec")})
            log(f"  [{lane_id}] {r['id']:<8} rc {res.get('rc')} · {float(res.get('sec') or 0):.0f}s"
                + (f" · 守門等 {gov['waited_s']:.0f}s" if gov and gov["waited_s"] else ""))
        return res

    out = {"lists": [], "lanes": [], "aborted": False, "wall_s": 0.0, "events": events}
    if lists_first:
        env0 = child_env(jobs, tp, "lists")
        for r in order_fn(plan.get("lists") or []):
            out["lists"].append(one(r, "lists", env0))
            if out["lists"][-1].get("rc") not in (0, None):     # 第一支清單引擎紅就停(後面的清單與擷取都不起)
                break
        bad = [x["id"] for x in out["lists"] if x.get("rc") not in (0, None)]
        if bad:
            out["aborted"] = True
            out["wall_s"] = round(time.time() - t0, 1)
            log(f"[停] 清單引擎失敗 {bad} → 後面的擷取不起(清單是全部引擎的前提)")
            return out

    def lane_run(L):
        t1 = time.time()
        env = child_env(jobs, tp, L["id"])
        res = [one(r, L["id"], env) for r in order_fn(L["rows"])]
        return {"id": L["id"], "groups": L["groups"], "dbs": L.get("dbs") or [], "engines": res, "sec": round(time.time() - t1, 1),
                "failed": [x["id"] for x in res if x.get("rc") not in (0, None)]}

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, int(jobs)), thread_name_prefix="fg-lane") as ex:
        futs = [ex.submit(lane_run, L) for L in plan["lanes"] if L.get("rows")]
        for f in futs:
            out["lanes"].append(f.result())
    out["wall_s"] = round(time.time() - t0, 1)
    return out


def _auto_jobs() -> int:
    lo, hi = JOBS_RANGE_V0107
    return max(lo, min(hi, (os.cpu_count() or 2) - 1))


def _clamp_jobs(n) -> int:
    lo, hi = JOBS_RANGE_V0107
    return max(lo, min(hi, int(n)))


def _slim(x: dict) -> dict:
    return {k: x.get(k) for k in ("id", "mdl", "rc", "sec", "log", "tail", "timeout_s", "lane", "governor")}


def cmd_run_v0107(argv: list) -> int:
    import argparse
    ap = argparse.ArgumentParser(prog=f"{TAG_V0107} run", description="清單引擎先跑 → 依 DuckDB 庫分道並行擷取(CPU · DRAM · TEMP 守門)")
    ap.add_argument("--groups", required=True); ap.add_argument("--as-of"); ap.add_argument("--home")
    ap.add_argument("--mode", default="live", choices=["live", "fixture", "block"]); ap.add_argument("--dry", action="store_true")
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--jobs", default="auto", help="同時跑的道數 1~5(auto = CPU 數 − 1,夾在 1~5)")
    ap.add_argument("--no-lists-first", action="store_true", help="不先跑清單引擎 009 · 010(清單剛更新過才用)")
    ap.add_argument("--cpu-max", type=float, default=LIMITS_V0107["cpu_max"])
    ap.add_argument("--mem-min-gb", type=float, default=LIMITS_V0107["mem_min_gb"])
    ap.add_argument("--temp-min-gb", type=float, default=LIMITS_V0107["temp_min_gb"])
    ap.add_argument("--govern-wait", type=float, default=LIMITS_V0107["max_wait_s"])
    ap.add_argument("--no-governor", action="store_true")
    a = ap.parse_args(argv)
    book, fb, ledger, sel, matrix, sel_p, mat_p, home = V0100._ctx(a)
    gids = V0100._gids(book, a.groups)
    as_of = V0100.resolve_asof(a.as_of or V0100.current_asof_setting(book, ledger))
    jobs = _auto_jobs() if str(a.jobs).lower() == "auto" else _clamp_jobs(a.jobs)
    limits = None if a.no_governor else {"cpu_max": a.cpu_max, "mem_min_gb": a.mem_min_gb, "temp_min_gb": a.temp_min_gb,
                                         "interval_s": LIMITS_V0107["interval_s"], "max_wait_s": a.govern_wait}
    work = home.parent / "_fetch_groups"
    eff_sel = None
    if any(V0100.group_of(book, x)["membership"] == "EDITABLE_SELECTION" for x in gids):
        eff_sel = work / f"selection_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
        if not a.dry:
            work.mkdir(parents=True, exist_ok=True)
            eff_sel.write_text(json.dumps(V0100.effective_selection(book, gids, ledger, sel), ensure_ascii=False, indent=1), encoding="utf-8")
    plan = plan_lanes(book, fb, gids, as_of, str(eff_sel) if eff_sel else None)
    lists_first = not a.no_lists_first
    if lists_first:                                             # 勾的族群沒列到的清單引擎也先跑(009 · 010 都是全部引擎的前提)
        by_id = {r["id"]: r for r in fb.get("engines", [])}
        have = {r["id"] for r in plan["lists"]}
        plan["lists"] += [dict(by_id[e], run_args=list(by_id[e].get("run_args") or []), as_of=as_of, needs=[]) for e in LIST_ENGINES_V0107
                          if e in by_id and e not in have]
        plan["lists"].sort(key=lambda r: LIST_ENGINES_V0107.index(r["id"]) if r["id"] in LIST_ENGINES_V0107 else 99)
    tp = temp_plan()
    res0 = resources(tp["duck_temp_base"])
    n_eng = sum(len(L["rows"]) for L in plan["lanes"])
    print(f"[run · 並行] 族群 {','.join(gids)} · as-of {as_of} · 道 {len(plan['lanes'])} · 引擎 {n_eng} · 清單先跑 "
          f"{'是' if lists_first else '否'}({'+'.join(r['id'] for r in plan['lists']) or '—'}) · 流程 {jobs} · 模式 {a.mode} · 輸出根 {home}"
          + (f" · 冊上沒有 {plan['missing']}" if plan["missing"] else ""))
    for L in plan["lanes"]:
        print(f"  道 {L['id']:<22} 族群 {','.join(L['groups'])} · 庫 {','.join(L['dbs']) or '—'} · 引擎 {' → '.join(r['id'] for r in ordered_v0107(L['rows'])) or '—'}")
    if plan["merged"]:
        print(f"  併道 {len(plan['merged'])}:{' ; '.join(plan['merged'][:8])}")
    print(f"  資源 CPU {res0['cpu_pct']}% · DRAM 可用 {res0['mem_avail_gb']}/{res0['mem_total_gb']} GB · TEMP 可用 {res0['temp_free_gb']} GB"
          f"({tp['duck_temp_base']})· 量測 {res0['via']} · 守門 "
          + ("關" if not limits else f"CPU ≤ {limits['cpu_max']:.0f}% · DRAM ≥ {limits['mem_min_gb']} GB · TEMP ≥ {limits['temp_min_gb']} GB · 最多等 {limits['max_wait_s']:.0f}s"))
    if a.dry:
        print("  (--dry:只列,不起子行程、不寫檔)")
        return 0
    if a.mode == "live" and not V0100.gates_open():
        print("[GATED] 雙閘沒開 —— 零子行程、零出網、零寫檔。本行程環境開閘(操作員的手,本檔永不代設):VIA_NET_CONSENT=YES VIA_SCRAPE_CONSENT=YES")
        return 4
    mp = V0100.tail(V0100.MDL008_GLOB)
    if mp is None:
        print("[錯] 找不到 VDF_MDL008_FetchSystem 尾版")
        return 2
    try:
        Path(tp["duck_temp_base"]).mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    started = datetime.now()
    out = run_parallel(plan, mp, a.mode, home, home.parent / "_logs", a.timeout, jobs, limits, ordered_v0107, tp, lists_first)
    res1 = resources(tp["duck_temp_base"])
    all_res = list(out["lists"]) + [x for L in out["lanes"] for x in L["engines"]]
    rc_map = {x["id"]: x.get("rc") for x in all_res}
    run_id = f"FG_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    cat_note = "ok"
    try:
        con = V0100._con_catalog(home)
        try:
            con.execute("INSERT INTO fg_runs VALUES (?,?,?,?,?,?,?,?)",
                        [run_id, started, datetime.now(), as_of, a.mode, ",".join(gids), ",".join(rc_map), json.dumps(rc_map)])
            V0100.sync_catalog(con, book, ledger, sel, matrix)
        finally:
            con.close()
    except Exception as exc:                                    # 目錄沒寫成照實記(擷取結果不受影響)
        cat_note = f"目錄沒寫成 {type(exc).__name__}: {exc}"
        print(f"  [警] {cat_note}")
    bad = [k for k, v in rc_map.items() if v not in (0, None)]
    sum_sec = round(sum(float(x.get("sec") or 0) for x in all_res), 1)
    report = {"run_id": run_id, "page_tool": TAG_V0107, "started": started.isoformat(timespec="seconds"),
              "finished": datetime.now().isoformat(timespec="seconds"), "wall_s": out["wall_s"], "sum_engine_s": sum_sec, "as_of": as_of,
              "mode": a.mode, "jobs": jobs, "groups": gids, "lists_first": lists_first, "aborted": out["aborted"],
              "lists": [_slim(x) for x in out["lists"]], "lanes": [dict(L, engines=[_slim(x) for x in L["engines"]]) for L in out["lanes"]],
              "failed": bad, "merged": plan["merged"], "missing": plan["missing"], "limits": limits, "resources_before": res0,
              "resources_after": res1, "temp": tp, "mdl008": mp.name, "catalog": cat_note, "events": out["events"]}
    work.mkdir(parents=True, exist_ok=True)
    (work / PARALLEL_LATEST).write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    with (work / PARALLEL_RUNS).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({k: report[k] for k in ("run_id", "started", "finished", "wall_s", "sum_engine_s", "as_of", "mode", "jobs",
                                                     "groups", "aborted", "failed")}, ensure_ascii=False) + "\n")
    for L in out["lanes"]:
        print(f"  道 {L['id']:<22} {L['sec']:.0f}s · 引擎 {len(L['engines'])} · 失敗 {len(L['failed'])}" + (f" {L['failed']}" if L["failed"] else ""))
    print(f"[run · 並行] 結束 · 失敗 {len(bad)}/{len(rc_map)} · 牆鐘 {out['wall_s']:.0f}s(引擎合計 {sum_sec:.0f}s)· 經 {mp.name} · 目錄 {cat_note}"
          f" · 報告 {work / PARALLEL_LATEST}" + (f" · {bad}" if bad else ""))
    if out["aborted"]:
        return 5
    return 0 if not bad else 1


# ---------------------------------------------------------------- 頁:並行擷取 · USER-TEST
_CSS_V0107 = (".par-h{display:flex;gap:12px;flex-wrap:wrap;margin:6px 0}.par-h span{white-space:nowrap}"
              ".ut-ok{color:#1a7f37;font-weight:600}.ut-bad{color:#c62828;font-weight:700}.ut-warn{color:#b26a00;font-weight:600}.ut-mut{opacity:.7}")

_JS_V0107 = r"""
(function () {
  const prev = cmdOf;
  cmdOf = function (verb) {
    if (verb === 'run_par' || verb === 'usertest') {
      const base = prev('run');
      if (verb === 'run_par' && typeof base === 'string' && base.startsWith('# 族群已清除')) return base;
      const gs = $$('.gsel:checked').map(x => x.value).join(',');
      const asof = $('#asof').value || 'latest', mode = $('#mode').value, home = $('#home').value;
      const jobs = ($('#jobs') && $('#jobs').value) || 'auto';
      const H = home ? ` --home "${home}"` : '';
      const a = verb === 'run_par' ? `run --groups ${gs || 'ALL'} --as-of ${asof} --mode ${mode} --jobs ${jobs}` + H : 'usertest' + H;
      const bash = `VIA_FROM_VCGC=YES python3 "${PY}" ${a}`;
      const ps = `$env:VIA_FROM_VCGC='YES'; python ".\\${PY.replace(/\//g, '\\')}" ${a}`;
      const gate = (verb === 'run_par' && mode === 'live') ? "\n# live 先在本視窗開雙閘(操作員的手,頁與產生器永不代設):VIA_NET_CONSENT=YES · VIA_SCRAPE_CONSENT=YES" : '';
      const what = verb === 'run_par' ? '清單引擎 009 · 010 先跑 → 依 DuckDB 庫分道 ' + jobs + ' 流程同時跑(CPU · DRAM · TEMP 守門)' : '建頁 → 逐功能鍵實測(有瀏覽器就 headless 點)→ 結果回頁「並行擷取 · USER-TEST」';
      return `# ${verb}:${what}\n${bash}\n${ps}${gate}`;
    }
    return prev(verb);
  };
  const j = $('#jobs');
  if (j) j.addEventListener('input', () => { if (st.verb) $('#cmd').textContent = cmdOf(st.verb); });
})();
"""

_HARNESS_JS = r"""
window.addEventListener('load', function () { setTimeout(function () {
  var R = {fn: [], pg: [], sel: {}, errors: [], snapshot: false};
  window.addEventListener('error', function (e) { R.errors.push(String(e.message || e)); });
  try { R.snapshot = (typeof S === 'object') && Array.isArray(S.groups); } catch (e) { R.errors.push('S: ' + e); }
  var cmd = document.querySelector('#cmd');
  Array.prototype.slice.call(document.querySelectorAll('[data-fn]')).forEach(function (b) {
    var before = cmd ? cmd.textContent : '';
    try { b.click(); } catch (e) { R.errors.push(b.dataset.fn + ': ' + e); }
    var after = cmd ? cmd.textContent : '';
    R.fn.push({fn: b.dataset.fn, ok: !!after && after.trim().length > 0 && after !== 'undefined' && after !== before, head: after.slice(0, 90)});
  });
  var seen = {};
  Array.prototype.slice.call(document.querySelectorAll('[data-pg]')).forEach(function (b) {
    var id = b.dataset.pg; if (seen[id]) return; seen[id] = 1;
    try { b.click(); } catch (e) { R.errors.push(id + ': ' + e); }
    var el = document.getElementById(id);
    R.pg.push({pg: id, ok: !!el && el.classList.contains('on')});
  });
  var boxes = function () { return Array.prototype.slice.call(document.querySelectorAll('.gsel')); };
  var ga = document.getElementById('gall'), gn = document.getElementById('gnone');
  if (ga) { ga.click(); R.sel.all = boxes().length > 0 && boxes().every(function (x) { return x.checked; }); }
  if (gn) { gn.click(); R.sel.none = boxes().every(function (x) { return !x.checked; }); }
  var pre = document.createElement('pre'); pre.id = 'VIA_UT'; pre.textContent = JSON.stringify(R); document.body.appendChild(pre);
}, 50); });
"""


def _esc(v) -> str:
    return html.escape("" if v is None else str(v))


def _lamp_html(lamp) -> str:
    cls = {"GREEN": "ok", "RED": "bad", "YELLOW": "warn"}.get(str(lamp), "mut")
    return f'<span class="ut-{cls}">{_esc(lamp)}</span>'


def section_v0107(snap: dict) -> str:
    """頁「並行擷取 · USER-TEST」:PARALLEL_latest.json(各道 · 各引擎 rc / 秒 / 守門)+ USERTEST_latest.json(功能鍵逐項燈)。純顯示,不執行。"""
    par, ut = snap.get("parallel") or {}, snap.get("usertest") or {}
    h = [f'<section class="pg" id="{PAGE_ID_V0107}"><div class="card"><h2>{PAGE_TITLE_V0107}</h2>',
         '<div class="mut">清單引擎(009 台股全市場清單 · 010 主動式 ETF 清單)先跑 → 其餘族群依 DuckDB 庫分道同時跑(3~5 流程;CPU · DRAM · TEMP 守門,'
         'DuckDB 暫存走 TEMP)。本頁只顯示結果;指令在左面板「並行跑族群」「USER-TEST」。</div>']
    if par:
        lamp = "RED" if par.get("aborted") or par.get("failed") else "GREEN"
        head = [("run", par.get("run_id")), ("as-of", par.get("as_of")), ("模式", par.get("mode")), ("流程", par.get("jobs")),
                ("牆鐘", f"{par.get('wall_s')}s"), ("引擎合計", f"{par.get('sum_engine_s')}s"), ("失敗", len(par.get("failed") or [])),
                ("清單先跑", "是" if par.get("lists_first") else "否"), ("目錄", par.get("catalog")), ("MDL008", par.get("mdl008")), ("時間", par.get("finished"))]
        h.append(f"<h3>並行擷取 {_lamp_html(lamp)}</h3><div class=\"par-h\">" + "".join(f"<span>{_esc(k)} {_esc(v)}</span>" for k, v in head) + "</div>")
        rows = [("lists", "—", x) for x in par.get("lists") or []] + \
               [(L.get("id"), ",".join(L.get("groups") or []), x) for L in par.get("lanes") or [] for x in L.get("engines") or []]
        h.append("<table><thead><tr><th>燈</th><th>道</th><th>族群</th><th>引擎</th><th>rc</th><th>秒</th><th>守門等(s)</th><th>日誌尾</th></tr></thead><tbody>"
                 + "".join(f"<tr><td>{_lamp_html('GREEN' if x.get('rc') == 0 else 'RED')}</td><td>{_esc(lane)}</td><td>{_esc(gs)}</td>"
                           f"<td>{_esc(x.get('id'))} {_esc(x.get('mdl') or '')}</td><td>{_esc(x.get('rc'))}</td><td>{_esc(x.get('sec'))}</td>"
                           f"<td>{_esc((x.get('governor') or {}).get('waited_s', 0))}</td><td class=\"mut\">{_esc((x.get('tail') or [''])[-1][:110])}</td></tr>"
                           for lane, gs, x in rows) + "</tbody></table>")
        rb, ra, tpl = par.get("resources_before") or {}, par.get("resources_after") or {}, par.get("temp") or {}
        h.append(f'<div class="mut">資源 前 CPU {_esc(rb.get("cpu_pct"))}% · DRAM 可用 {_esc(rb.get("mem_avail_gb"))} GB · TEMP 可用 {_esc(rb.get("temp_free_gb"))} GB'
                 f' → 後 CPU {_esc(ra.get("cpu_pct"))}% · DRAM {_esc(ra.get("mem_avail_gb"))} GB · TEMP {_esc(ra.get("temp_free_gb"))} GB'
                 f' · 暫存 {_esc(tpl.get("duck_temp_base"))} · 量測 {_esc(rb.get("via"))}</div>')
    else:
        h.append('<div class="mut">尚未跑並行擷取:左面板「並行跑族群」→ 貼指令跑(live 要雙閘)。</div>')
    if ut:
        bad = [r for r in ut.get("rows") or [] if r.get("lamp") == "RED"]
        h.append(f'<h3>USER-TEST 功能鍵 {_lamp_html("RED" if bad else "GREEN")} · 綠 {_esc(ut.get("n_green"))} · 紅 {_esc(len(bad))} · {_esc(ut.get("built"))}'
                 f' · 驗法 {_esc(ut.get("mode"))}</h3><div class="mut">{_esc(ut.get("note") or "")}</div>'
                 "<table><thead><tr><th>燈</th><th>項</th><th>說明</th></tr></thead><tbody>"
                 + "".join(f"<tr><td>{_lamp_html(r.get('lamp'))}</td><td>{_esc(r.get('key'))}</td><td class=\"mut\">{_esc(r.get('note'))}</td></tr>"
                           for r in ut.get("rows") or []) + "</tbody></table>")
    else:
        h.append('<div class="mut">尚未 USER-TEST:左面板「USER-TEST」→ 貼指令跑(建頁 → 逐鍵驗 → 結果回這裡)。</div>')
    h.append("</div></section>")
    return "".join(h)


def inject_section_v0107(page: str, snap: dict) -> str:
    """v0101 頁(relayout 前):參考頁(pg-ref)前面插一個頁籤與一頁;relayout 會把頁籤抄進左面板「頁」。"""
    t = page.find('<div class="tabs">')                          # v0101 的左面板「頁」也有同樣的鈕(在前面)→ 只插進頁籤列;relayout 會重做左面板
    i = page.find('<button data-pg="pg-ref">', t) if t >= 0 else -1
    j = page.find('<section class="pg" id="pg-ref">')
    if t < 0 or i < 0 or j < 0:
        raise V0105.LayoutError("v0101 頁找不到頁籤列或參考頁(pg-ref)")
    page = page[:i] + f'<button data-pg="{PAGE_ID_V0107}">{PAGE_TITLE_V0107}</button>' + page[i:]
    j = page.find('<section class="pg" id="pg-ref">')
    return page[:j] + section_v0107(snap) + page[j:]


def inject_left_v0107(page: str) -> str:
    """relayout 後:左面板補「並行流程」選項(① 輸入控制尾)與「並行跑族群」「USER-TEST」鈕(② 功能尾);頁尾補樣式與指令。"""
    sel = ('<div class="lf"><span class="lb">並行流程(3~5;auto = CPU 數 − 1)</span><select id="jobs">'
           '<option>auto</option><option>3</option><option>4</option><option>5</option></select></div>')
    if "<h3>② 功能</h3>" not in page:
        raise V0105.LayoutError("左面板找不到「② 功能」")
    page = page.replace("<h3>② 功能</h3>", sel + "<h3>② 功能</h3>", 1)
    i = page.find('data-fn="refill"')
    j = page.find("</button>", i) if i >= 0 else -1
    if i < 0 or j < 0:
        raise V0105.LayoutError("左面板找不到 refill 鈕")
    btns = (V0105._btn("run_par", "並行跑族群(3~5 流程)", "清單引擎 009 · 010 先跑 → 依 DuckDB 庫分道同時跑;CPU · DRAM · TEMP 守門;live 要雙閘")
            + V0105._btn("usertest", "USER-TEST 功能鍵", "建頁 → 逐功能鍵實測(有瀏覽器就 headless 點;沒有就靜態驗)→ 結果回頁「並行擷取 · USER-TEST」"))
    page = page[:j + 9] + btns + page[j + 9:]
    k = page.rfind("</body>")
    tail = f"<style>{_CSS_V0107}</style><script>{_JS_V0107}</script>"
    return page[:k] + tail + page[k:] if k >= 0 else page + tail


def render_v0107(snap: dict, out: Path) -> str:
    snap = dict(snap)
    snap["backup"] = V0105.backup_info()
    snap["page_tool"] = TAG_V0107
    snap["parallel"] = _read_json(Path(str(snap["home"])).parent / "_fetch_groups" / PARALLEL_LATEST) if snap.get("home") else {}
    snap["usertest"] = _read_json(usertest_path(out))
    page = inject_section_v0107(_RENDER_V0101(snap, out), snap)
    return inject_left_v0107(V0105.relayout(page, snap, out))


V0101.render = render_v0107                                    # build_page → 模組全域 render → 本版頁(ui 真路徑)


# ---------------------------------------------------------------- usertest:功能鍵實測
def usertest_static(page: str) -> list:
    """靜態驗:每個 data-fn 鈕在頁內程式有處理分支 · 每個頁籤有頁 · 快照可解析 · 輸入 id 全頁唯一。"""
    rows = []
    for fn in dict.fromkeys(re.findall(r'data-fn="([^"]+)"', page)):
        has = re.search(r"(?:[{,]\s*|\n\s*)%s\s*:" % re.escape(fn), page) is not None or re.search(r"verb\s*===\s*'%s'" % re.escape(fn), page) is not None
        rows.append({"key": f"fn:{fn}", "lamp": "GREEN" if has else "RED", "note": "頁內程式有處理分支" if has else "頁內程式沒有這個鍵的分支"})
    secs = set(re.findall(r'<section class="pg" id="([^"]+)"', page))
    for pg in dict.fromkeys(re.findall(r'data-pg="([^"]+)"', page)):
        rows.append({"key": f"pg:{pg}", "lamp": "GREEN" if pg in secs else "RED", "note": "頁籤有頁" if pg in secs else "頁籤沒有對應的頁"})
    m = re.search(r'<script type="application/json" id="SNAPSHOT">(.*?)</script>', page, re.S)
    try:
        emb = json.loads(m.group(1).replace("<\\/", "</")) if m else None
    except ValueError:
        emb = None
    rows.append({"key": "snapshot", "lamp": "GREEN" if isinstance(emb, dict) and emb.get("groups") else "RED",
                 "note": f"內嵌快照 族群 {len(emb.get('groups') or [])} · 頁工具 {emb.get('page_tool')}" if isinstance(emb, dict) else "內嵌快照解析不了"})
    dup = [x for x in ("asof", "mode", "home", "gsel", "mgroup", "mvals", "cat", "catdate", "rfapply", "jobs", "cmd", "eng", "res") if page.count(f'id="{x}"') != 1]
    rows.append({"key": "ids", "lamp": "GREEN" if not dup else "RED", "note": "輸入 / 結果元素 id 全頁唯一" if not dup else f"id 不唯一或缺:{dup}"})
    return rows


def find_browser():
    """headless 用的瀏覽器:VIA_BROWSER_EXE → Playwright 瀏覽器夾 → PATH → Windows 預設安裝位。找不到回 None(照實)。"""
    cands = []
    if os.environ.get("VIA_BROWSER_EXE"):
        cands.append(os.environ["VIA_BROWSER_EXE"])
    pw = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    if pw and Path(pw).is_dir():
        for pat in ("chromium-*/chrome-linux/chrome", "chromium_headless_shell-*/chrome-linux/headless_shell", "chromium-*/chrome-win/chrome.exe",
                    "chromium-*/chrome-mac/Chromium.app/Contents/MacOS/Chromium"):
            cands += [str(p) for p in sorted(Path(pw).glob(pat))]
    for n in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable", "chrome", "msedge"):
        w = shutil.which(n)
        if w:
            cands.append(w)
    for env_key, rel in (("PROGRAMFILES", "Google/Chrome/Application/chrome.exe"), ("PROGRAMFILES(X86)", "Google/Chrome/Application/chrome.exe"),
                         ("PROGRAMFILES(X86)", "Microsoft/Edge/Application/msedge.exe"), ("PROGRAMFILES", "Microsoft/Edge/Application/msedge.exe"),
                         ("LOCALAPPDATA", "Google/Chrome/Application/chrome.exe")):
        if os.environ.get(env_key):
            cands.append(str(Path(os.environ[env_key]) / rel))
    for c in cands:
        if Path(c).is_file():
            return Path(c)
    return None


def usertest_browser(page_path: Path, timeout: int = 120):
    """瀏覽器實測:頁的副本尾端掛測試程式(逐鍵點、讀 #cmd、切頁籤、全選 / 清除)→ headless --dump-dom → 讀回 <pre id=VIA_UT>。沒瀏覽器回 None。"""
    exe = find_browser()
    if exe is None:
        return None
    page = page_path.read_text(encoding="utf-8")
    k = page.rfind("</body>")
    harness = page_path.with_name(page_path.stem + "_usertest_harness.html")
    harness.write_text((page[:k] + f"<script>{_HARNESS_JS}</script>" + page[k:]) if k >= 0 else page + f"<script>{_HARNESS_JS}</script>", encoding="utf-8")
    try:
        with tempfile.TemporaryDirectory() as prof:
            cmd = [str(exe), "--headless", "--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage", "--allow-file-access-from-files",
                   f"--user-data-dir={prof}", "--virtual-time-budget=8000", "--dump-dom", harness.resolve().as_uri()]
            try:
                p = subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8",
                                   errors="replace", timeout=timeout)
            except Exception as exc:
                return {"exe": str(exe), "error": f"{type(exc).__name__}: {exc}"}
    finally:
        with contextlib.suppress(OSError):
            harness.unlink()
    m = re.search(r'<pre id="VIA_UT">(.*?)</pre>', p.stdout, re.S)
    if not m:
        return {"exe": str(exe), "error": f"瀏覽器沒回 VIA_UT(rc {p.returncode});stderr 尾:{p.stderr[-240:].strip()}"}
    try:
        data = json.loads(html.unescape(m.group(1)))
    except ValueError as exc:
        return {"exe": str(exe), "error": f"VIA_UT 解析失敗 {exc}"}
    data["exe"] = str(exe)
    return data


def cmd_usertest(argv: list) -> int:
    import argparse
    ap = argparse.ArgumentParser(prog=f"{TAG_V0107} usertest", description="建頁 → 靜態驗 → 瀏覽器逐鍵實測 → 結果掛頁")
    ap.add_argument("--home"); ap.add_argument("--out"); ap.add_argument("--as-of")
    ap.add_argument("--browser", default="auto", choices=["auto", "on", "off"])
    a = ap.parse_args(argv)
    home = V0100._ctx(a)[-1]
    out = Path(a.out) if a.out else ((USERTEST_DIR / "VDF_FetchGroups_USERTEST_latest.html") if USERTEST_DIR is not None else V0101.UI_PAGE)
    out.parent.mkdir(parents=True, exist_ok=True)               # 預設建在報告夾(不寫已追蹤的正式頁;正式頁由 ui 動詞重建,結果一樣掛上)
    t0 = time.time()
    V0101.build_page(home, out, a.as_of)                        # ① 建頁(真路徑:模組全域 render = 本版)
    rows = usertest_static(out.read_text(encoding="utf-8"))     # ② 靜態驗
    mode, note = "static", "瀏覽器實測:--browser off(只做靜態驗)"
    br = None if a.browser == "off" else usertest_browser(out)  # ③ 瀏覽器實測
    if br is None and a.browser != "off":
        note = "瀏覽器實測:找不到 Chromium / Chrome / Edge(VIA_BROWSER_EXE 可指定)→ 只做靜態驗"
        if a.browser == "on":
            rows.append({"key": "browser", "lamp": "RED", "note": note})
    elif br is not None and br.get("error"):
        note = f"瀏覽器實測失敗({br['exe']}):{br['error']}"
        rows.append({"key": "browser", "lamp": "RED", "note": note})
    elif br is not None:
        mode, note = "browser", f"瀏覽器 {br['exe']} headless 逐鍵點過(--dump-dom)"
        for f in br.get("fn") or []:
            rows.append({"key": f"click:{f.get('fn')}", "lamp": "GREEN" if f.get("ok") else "RED", "note": (f.get("head") or "(#cmd 沒變)").replace("\n", " ⏎ ")})
        for pg in br.get("pg") or []:
            rows.append({"key": f"page:{pg.get('pg')}", "lamp": "GREEN" if pg.get("ok") else "RED", "note": "頁籤切換 → 該頁 .on"})
        rows.append({"key": "select:gall", "lamp": "GREEN" if (br.get("sel") or {}).get("all") else "RED", "note": "全選 → 族群全勾"})
        rows.append({"key": "select:gnone", "lamp": "GREEN" if (br.get("sel") or {}).get("none") else "RED", "note": "清除 → 族群全不勾"})
        rows.append({"key": "snapshot:S", "lamp": "GREEN" if br.get("snapshot") else "RED", "note": "頁內快照 S.groups 可用"})
        for e in br.get("errors") or []:
            rows.append({"key": "js-error", "lamp": "RED", "note": str(e)[:200]})
    bad = [r for r in rows if r["lamp"] == "RED"]
    rep = {"page_tool": TAG_V0107, "built": _now_iso(), "page": str(out), "mode": mode, "note": note, "rows": rows,
           "n_green": len(rows) - len(bad), "n_red": len(bad), "sec": round(time.time() - t0, 1)}
    up = usertest_path(out)
    up.parent.mkdir(parents=True, exist_ok=True)
    up.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    V0101.build_page(home, out, a.as_of)                        # ④ 重建:結果掛在頁「並行擷取 · USER-TEST」
    print(f"[usertest] {out} · 驗法 {mode} · 綠 {rep['n_green']} · 紅 {len(bad)} · {rep['sec']}s · {note} · 結果 {up}")
    for r in bad:
        print(f"  [RED] {r['key']} · {r['note']}")
    print(f"  [計] {TAG_V0107} usertest · 綠 {rep['n_green']} · 紅 {len(bad)} · 驗法 {mode}")
    return 0 if not bad else 1


# ---------------------------------------------------------------- 自測 · 入口
def selftest() -> int:
    import argparse
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    print(f"=== {TAG_V0107} · 薄尾自測(清單先跑 · 分道並行 · 守門 · 頁 USER-TEST)===")
    chk("① 沿鏈找到 v0100(cmd_run · _ctx)· v0101(build_page)· v0105(relayout)本體;render 已換上本版;TAG 不蓋(六案標記照印)",
        V0100 is not None and "v0100" in V0100.__name__ and V0101 is not None and "v0101" in V0101.__name__ and V0105 is not None
        and "v0105" in V0105.__name__ and V0101.render is render_v0107 and PRIOR.TAG.endswith("v0106"),
        (getattr(V0100, "__name__", None), getattr(V0101, "__name__", None), getattr(V0105, "__name__", None), getattr(PRIOR, "TAG", None)))
    book = V0100.load_book()
    fb_p = V0100.tail(V0100.FETCH_GLOB)
    fb = V0100._json(fb_p) if fb_p else {}
    gids = V0100._gids(book, "ALL")
    plan = plan_lanes(book, fb, gids, "2026-10-10", None)
    lane_of = {r["id"]: L["id"] for L in plan["lanes"] for r in L["rows"]}
    n_rows = sum(len(L["rows"]) for L in plan["lanes"])
    by_id = {r["id"]: r for r in fb.get("engines", [])}
    cross = [(r["id"], n) for L in plan["lanes"] for r in L["rows"] for n in (by_id.get(r["id"]) or {}).get("needs") or []
             if n in lane_of and lane_of[n] != L["id"]]
    vake = [L for L in plan["lanes"] if any(_group_kind(V0100.group_of(book, g)) == "vake" for g in L["groups"])]
    tw = [L for L in plan["lanes"] if "vdf_tw_market.duckdb" in L["dbs"]]
    chk("② 真冊分道:清單 = 009+010 · 每支引擎只在一道 · 相依不跨道 · vake 四族群一道一列(011d)· 台股四族群同庫一道 · 道 ≥ 4",
        [r["id"] for r in plan["lists"]] == list(LIST_ENGINES_V0107) and len(lane_of) == n_rows and not cross and not plan["missing"]
        and len(vake) == 1 and len(vake[0]["groups"]) == 4 and [r["id"] for r in vake[0]["rows"]] == ["011d"]
        and len(tw) == 1 and {"TW_PRICE_VOL", "TW_CHIP", "TW_MONTHLY_REV", "TW_FIN"} <= set(tw[0]["groups"]) and len(plan["lanes"]) >= 4,
        ([r["id"] for r in plan["lists"]], [(L["id"], L["groups"], [r["id"] for r in L["rows"]]) for L in plan["lanes"]], cross, plan["missing"]))
    recs, rlock = [], threading.Lock()

    def stub(mdl008, r, mode, home, logs, timeout, env, rc_of=None):
        t0 = time.time()
        time.sleep(0.25)
        rec = {"lane": env.get("VIA_FG_LANE"), "id": r["id"], "t0": t0, "t1": time.time(), "env_ok": env.get("VIA_FROM_VCGC") == "YES"
               and bool(env.get("VIA_DUCKDB_TEMP_DIR")) and env.get("VIA_FG_JOBS") is not None}
        with rlock:
            recs.append(rec)
        return {"id": r["id"], "mdl": r.get("mdl"), "rc": (rc_of or {}).get(r["id"], 0), "sec": round(time.time() - t0, 2), "log": "", "tail": []}

    def overlaps(a, b):
        return a["t0"] < b["t1"] and b["t0"] < a["t1"]

    fake = {"lists": [{"id": "009", "mdl": "MDL009", "needs": []}, {"id": "010", "mdl": "MDL010", "needs": []}],
            "lanes": [{"id": "A", "groups": ["G1", "G2"], "dbs": ["a.duckdb"], "rows": [{"id": "a2", "needs": ["a1"]}, {"id": "a1", "needs": []}]},
                      {"id": "B", "groups": ["G3"], "dbs": [], "rows": [{"id": "b1", "needs": []}]},
                      {"id": "C", "groups": ["G4"], "dbs": [], "rows": [{"id": "c1", "needs": []}]}], "missing": [], "merged": []}
    tp = {"temp_root": tempfile.gettempdir(), "duck_temp_base": str(Path(tempfile.gettempdir()) / "VIA_selftest_duck")}
    quiet = lambda s: None
    keep_launch = globals()["LAUNCH"]
    with tempfile.TemporaryDirectory() as td:
        home, logs = Path(td) / "home", Path(td) / "_logs"
        home.mkdir()
        globals()["LAUNCH"] = stub
        try:
            o2 = run_parallel(fake, Path("x"), "block", home, logs, 60, 2, None, ordered_v0107, tp, True, log=quiet)
            recs2, recs[:] = list(recs), []
            o1 = run_parallel(fake, Path("x"), "block", home, logs, 60, 1, None, ordered_v0107, tp, True, log=quiet)
            recs1, recs[:] = list(recs), []
            globals()["LAUNCH"] = lambda *a, **k: stub(*a, **k, rc_of={"009": 1})
            o_abort = run_parallel(fake, Path("x"), "block", home, logs, 60, 2, None, ordered_v0107, tp, True, log=quiet)
            recs_abort, recs[:] = list(recs), []
        finally:
            globals()["LAUNCH"] = keep_launch
    lists_first_ok = all(x["lane"] == "lists" for x in recs2[:2]) and [x["id"] for x in recs2[:2]] == ["009", "010"] \
        and all(x["t1"] <= min(y["t0"] for y in recs2[2:]) + 1e-9 for x in recs2[:2])
    lanes2 = [x for x in recs2 if x["lane"] != "lists"]
    a_rows = [x for x in lanes2 if x["lane"] == "A"]
    cross2 = any(overlaps(x, y) for x in lanes2 for y in lanes2 if x["lane"] != y["lane"])
    in_lane_seq = len(a_rows) == 2 and a_rows[0]["id"] == "a1" and a_rows[0]["t1"] <= a_rows[1]["t0"] + 1e-9
    lanes1 = [x for x in recs1 if x["lane"] != "lists"]
    none1 = not any(overlaps(x, y) for i, x in enumerate(lanes1) for y in lanes1[i + 1:])
    chk("③ 替身並行:清單 009 → 010 先跑完才起道;jobs 2 不同道有重疊 · 同道 a1 → a2 不重疊;jobs 1 全無重疊;子行程環境帶 VIA_FROM_VCGC · TEMP · 流程數",
        lists_first_ok and cross2 and in_lane_seq and none1 and all(x["env_ok"] for x in recs2) and not o2["aborted"] and not o1["aborted"]
        and len(o2["lanes"]) == 3 and o2["wall_s"] < o1["wall_s"],
        (lists_first_ok, cross2, in_lane_seq, none1, o2["wall_s"], o1["wall_s"]))
    chk("④ 清單引擎紅就停:009 rc 1 → aborted · 道一支都沒起", o_abort["aborted"] and not o_abort["lanes"] and all(x["lane"] == "lists" for x in recs_abort)
        and [x["id"] for x in recs_abort] == ["009"], recs_abort)
    seq = iter([99.0, 99.0, 10.0])
    slept = []
    g1 = governor_wait({"cpu_max": 85, "mem_min_gb": 2, "temp_min_gb": 5, "interval_s": 1, "max_wait_s": 10},
                       sampler=lambda: {"cpu_pct": next(seq), "mem_avail_gb": 8, "temp_free_gb": 50}, sleeper=slept.append, log=quiet)
    g2 = governor_wait({"cpu_max": 85, "mem_min_gb": 2, "temp_min_gb": 5, "interval_s": 2, "max_wait_s": 6},
                       sampler=lambda: {"cpu_pct": 50, "mem_avail_gb": 1, "temp_free_gb": 50}, sleeper=lambda s: None, log=quiet)
    g3 = governor_wait({"cpu_max": 85, "mem_min_gb": 2, "temp_min_gb": 5, "interval_s": 1, "max_wait_s": 10},
                       sampler=lambda: {"cpu_pct": None, "mem_avail_gb": None, "temp_free_gb": None}, sleeper=slept.append, log=quiet)
    live = resources(tp["duck_temp_base"])
    chk("⑤ 守門:CPU 99 → 99 → 10 等兩輪(2s)後放行;DRAM 1 GB < 2 GB 等到上限 6s 照跑(forced);量不到(None)不擋;真量測有 CPU / DRAM / TEMP 數",
        g1["waited_s"] == 2 and not g1["forced"] and slept == [1, 1] and g1["reasons"] and "CPU" in g1["reasons"][0]
        and g2["forced"] and g2["waited_s"] == 6 and "DRAM" in g2["reasons"][0] and g3["waited_s"] == 0 and not g3["forced"]
        and live["cpu_pct"] is not None and live["mem_avail_gb"] is not None and live["temp_free_gb"] is not None,
        (g1, g2["waited_s"], g2["forced"], g3, live))
    with tempfile.TemporaryDirectory() as td:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc_dry = main(["run", "--groups", "ALL", "--dry", "--jobs", "9", "--home", str(Path(td) / "home")])
        txt = buf.getvalue()
        wrote = (Path(td) / "_fetch_groups").exists() or (Path(td) / "_logs").exists()
    chk("⑥ run --dry:走本版並行路徑、流程夾到 5、列道與資源、不起子行程不寫檔 rc 0",
        rc_dry == 0 and "[run · 並行]" in txt and "流程 5" in txt and "--dry" in txt and "守門" in txt and not wrote, (rc_dry, wrote, txt[:300]))
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "VDF_FetchGroups_selftest.html"
        home = V0100._ctx(argparse.Namespace(home=None))[-1]
        V0101.build_page(home, out)                              # ui 真路徑(build_page → 模組全域 render = 本版)
        page = out.read_text(encoding="utf-8")
        st_rows = usertest_static(page)
    aside = re.search(r'<aside class="fg-left fg-left-v0105">.*?</aside>', page, re.S)
    left = aside.group(0) if aside else ""
    m = re.search(r'<script type="application/json" id="SNAPSHOT">(.*?)</script>', page, re.S)
    try:
        emb = json.loads(m.group(1).replace("<\\/", "</")) if m else {}
    except ValueError:
        emb = {}
    want_ids = ("asof", "mode", "home", "gsel", "mgroup", "mvals", "cat", "catdate", "rfapply", "jobs")
    chk("⑦ 頁:多一頁「並行擷取 · USER-TEST」(頁籤在上也在左面板「頁」)· 左面板有並行流程選項與並行 / USER-TEST 鈕 · 指令 cmdOf 有分支 · 輸入 id 唯一 · 快照頁工具 = 本版 · 靜態驗全綠",
        page.count(f'<section class="pg" id="{PAGE_ID_V0107}">') == 1 and page.count(f'data-pg="{PAGE_ID_V0107}"') >= 2
        and all(f'data-fn="{v}"' in left for v in ("run_par", "usertest")) and 'id="jobs"' in left and "verb === 'run_par'" in page
        and all(page.count(f'id="{x}"') == 1 for x in want_ids) and emb.get("page_tool") == TAG_V0107
        and not [r for r in st_rows if r["lamp"] == "RED"],
        ([r for r in st_rows if r["lamp"] == "RED"], emb.get("page_tool"), page.count(f'data-pg="{PAGE_ID_V0107}"')))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 加速器橋 · 網路橋在;前版不動(薄尾);不碰 TA-Lib;頁與指令不執行任何東西(無 fetch / XMLHttpRequest)",
        "VIA:ACCEL-BRIDGE" in src and "VIA:NET-BRIDGE" in src and PRIOR_PATH.is_file() and "import " + "talib" not in src
        and "fetch(" not in _JS_V0107 and "XMLHttpRequest" not in _JS_V0107 and "fetch(" not in _HARNESS_JS)
    good = all(ok)
    if not good:
        print(f"  [計] {TAG_V0107} 本版 {sum(ok)}/{len(ok)} · FAIL")
        return 1
    V0101.render = _RENDER_V0105                                 # 前版鏈驗的是前版版面(v0105 ① 要 render 是它的)→ 跑鏈期間換回,跑完換上本版
    try:
        rc = PRIOR.selftest()
    finally:
        V0101.render = render_v0107
    chk("⑨ 前版鏈自測(v0106 → … → v0100)rc 0;跑完 render 已換回本版", rc == 0 and V0101.render is render_v0107, f"rc {rc}")
    good = all(ok)
    print(f"  [計] {TAG_V0107} 本版 {sum(ok)}/{len(ok)} · 前版鏈 {'PASS' if rc == 0 else 'FAIL'} · 合計 {'PASS' if good else 'FAIL'}")
    return 0 if good else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--selftest"]:
        return selftest()
    if argv and argv[0] == "run":
        if "--serial" in argv:                                  # 前版一條龍(v0100 cmd_run)
            return PRIOR.main([x for x in argv if x != "--serial"])
        return cmd_run_v0107(argv[1:])
    if argv and argv[0] == "usertest":
        return cmd_usertest(argv[1:])
    return PRIOR.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
