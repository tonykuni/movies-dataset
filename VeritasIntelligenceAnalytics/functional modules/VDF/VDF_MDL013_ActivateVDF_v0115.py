#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_MDL013_ActivateVDF v0115 — 薄尾:全部用記憶體 · 每支子行程掛最新加速器 + 網路工具(鎖驗證 · 收據)· 引擎並行 · 對照只讀本輪的家 · 記憶體誤報

操作員令(2026-10-22):「A 1234 全做 為何指令跑不完 全部用記憶體 全部加入最新的加速器及網路工具」。
疊在 v0114 之上;v0100 … v0114 一字不動。本版(只在本版的一輪裡生效;前版自測照舊):
  ① 全部用記憶體:每條流程 DuckDB 預算 (可用 − 保留 1 GB) × 0.6 ÷ 條數 → × 0.9(VIA_ACT_MEM_FRACTION 可調 0.3–0.95)。
     工作站實例:可用 6680 MB · 3 條 → 每條 1131 MB → 1696 MB。引擎流程另給並行工作數與每支預算(見 ⑤)。
  ② 「記憶體 沒生效」誤報:DuckDB 把 memory_limit 顯示成一位小數(1131 MB 顯示「1.0 GiB」→ 差 5.1% > 5%)→ 判沒生效。
     容許差改成 max(5%, 顯示精度一整格):DuckDB 是捨去到一位小數(GiB 一格 0.1 GiB · MiB 一格 0.1 MiB)。真的沒生效(差很多)照舊黃。
  ③ 加速器 + 網路工具(L103:PY 導入加速器 · VDF 導入網路工具):本輪鉤(<本輪 temp>/pyhook/sitecustomize.py,經 PYTHONPATH 帶進
     每個子行程與孫行程)多一段 —— 起跑先載最新 VeritasCeleritas(加速器,立即載入)並把 VeritasAegisNexus(網路工具)綁到最新那支
     (LazyLoader:sys.modules 已是鎖定那支,第一次用到才執行;立即載入會連帶 import pandas → numexpr,改變 numexpr 初始化順序,
     實測讓 v0103 ⑰ 由綠轉紅)。路徑由本檔起跑時定:鎖冊 VIA_ToolVersion_Lock 尾版指的那支,在就用它,否則 glob 尾版。
     載完環境變數全數還原成 VDF 給的(加速器 import 會改 OMP / MKL / POLARS … 17 個變數成全核,並行時互搶)。工具先載、DuckDB 鉤
     後裝(加速器會用 find_spec("duckdb") 探套件,先裝的鉤會被這一探吃掉 → 實測「鉤 無」)。每個行程一行收據(本輪 temp/tools_receipts.jsonl)。
     起跑印「[鎖驗證] accelerator=… · network=…」(EXACT · EOL_BOM_EQUIVALENT · MISMATCH · NOLOCK);收尾印「已掛 N 個子行程 ·
     加速器 a/N · 網路工具 b/N · 失敗 …」並寫進總覽 JSON(tools)。VIA_VDF_TOOLS=0 = 不掛(回前版行為)。
  ④ 跨來源對照 / 日期體檢 / 結果驗證只讀本輪的資料庫家(opt.db_home > VIA_VDF_DB_HOME):不再把倉內 output_hub · 擷取家的 .duckdb
     一起掃(工作站實錄:db check 在 via_01_vdf 找 0 本、對照卻從倉內 output_hub 讀到 11 萬筆 → 同一頁兩個說法)。同名檔取法同
     VDF db check(mega / active_tw_etf 優先 · 再比大小)。
  ⑤ 引擎流程:VIA_VDF_LAUNCH_JOBS = min(核 − 1, (可用 − 1 GB) ÷ 700 MB) · VIA_VDF_LAUNCH_MEM_MB = 總預算 ÷ (工作數 + 其他流程)·
     VIA_VDF_LAUNCH_THREADS = 1 → VDF_SystemManager v0162 並行跑自測、逐支印進度(心跳看得到)、逾時照實。操作員自己設了就照用。
VDF 自己的模組:不匯入他系統程式(鎖冊只讀資料);同意閘不讀不寫(只原樣傳);不碰 TA-Lib;不裝套件、不寫環境(只寫子行程 env)。
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


import hashlib
import importlib.util
import json
import os
import re
import sys
import types
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_MDL013_ActivateVDF"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
SCHEMA_V0115 = "VDF_ActivateVDF_v0115"
HOOK_TAG_V0115 = "vdf-activate-v0115"
MEM_FRACTION_V0115 = 0.9
PER_JOB_MB_V0115 = 700
TOOL_KINDS_V0115 = (("accelerator", "VeritasCeleritas", "", "VIA_VDF_ACCEL_PATH"), ("network", "VeritasAegisNexus", "network", "VIA_VDF_NET_PATH"))


def _vnum_v0115(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0115(p) < _vnum_v0115(__file__)), key=_vnum_v0115)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
with warnings.catch_warnings():
    warnings.simplefilter("ignore", SyntaxWarning)
    warnings.simplefilter("ignore", DeprecationWarning)
    _spec.loader.exec_module(PRIOR)
V0100 = PRIOR.V0100
DBM, FLM = PRIOR.DBM, PRIOR.FLM


def __getattr__(name):
    return getattr(PRIOR, name)


def _chain_v0115() -> list:
    out, m = [], PRIOR
    while isinstance(m, types.ModuleType) and m not in out:
        out.append(m)
        m = vars(m).get("PRIOR")
    return out


def _owner_v0115(name: str):
    for m in _chain_v0115():
        if name in vars(m):
            return m
    return None


_V0107_G = PRIOR.hook_dir.__globals__            # 本輪鉤 · 起跑實測的「本體」模組全域(鏈上有幾版把這些名字抄進自己的全域,換那份不生效)
_V0113 = _owner_v0115("_DB_FILES_V0111")          # 對照的庫清單(換在 v0111 模組全域)
_V0111_G = _V0113._DB_FILES_V0111.__globals__
_DB_FILES_V0113 = _V0113.db_files
_PLAN_SLOTS_ORIG = V0100.plan_slots
_PROBE_ORIG = _V0107_G["probe_memtemp"]
_FLOW_ENV_PRIOR = V0100.flow_env                   # = v0107 的(已換在鏈上各模組)
_ACTIVATE_V0114 = PRIOR.activate
_WRITE_ORIG = DBM._WRITE_REPORT_V0100
_RUN15 = {"on": False, "tools": None, "temp_run": None}
_FLOW_ENV_OWNERS = [m for m in [*_chain_v0115(), V0100] if "flow_env" in vars(m)]
_FLOW_ENV_SAVED = {id(m): m.flow_env for m in _FLOW_ENV_OWNERS}


# ---------------------------------------------------------------- ① 全部用記憶體
def mem_fraction() -> float:
    try:
        v = float(os.environ.get("VIA_ACT_MEM_FRACTION") or MEM_FRACTION_V0115)
    except ValueError:
        v = MEM_FRACTION_V0115
    return min(0.95, max(0.3, v))


def plan_slots(cpu: dict, mem: dict, want: int = 3, per_flow_mb: int = V0100.PER_FLOW_MB, reserve_mb: int = V0100.RESERVE_MB) -> dict:
    o = _PLAN_SLOTS_ORIG(cpu, mem, want, per_flow_mb, reserve_mb)
    if not _RUN15["on"]:
        return o
    avail, frac = mem.get("avail_mb"), mem_fraction()
    if avail is not None:
        o["duckdb_mem_mb"] = max(256, int((avail - reserve_mb) * frac) // o["slots"])
    o["mem_fraction"] = frac
    o["mem_note"] = f"全部用記憶體:(可用 {avail} − 保留 {reserve_mb} MB)× {frac} ÷ {o['slots']} 條 = 每條 {o['duckdb_mem_mb']} MB"
    return o


# ---------------------------------------------------------------- ② 記憶體誤報(DuckDB 顯示精度)
def mem_close(want_mb, got: str) -> bool:
    """DuckDB 把 memory_limit 捨去到一位小數的 GiB / MiB(1131 MB = 1.053 GiB → 「1.0 GiB」):容許差 max(5%, 一整格);
    want 是十進位 MB(DuckDB 的 MB = 1000²)。"""
    b = _V0107_G["_bytes"](got)
    if b is None or not want_mb:
        return False
    want = float(want_mb) * 1000 ** 2
    m = re.match(r"\s*[\d.]+\s*([KMGT])(i?)B", str(got), re.I)
    step = 0.1 * ((1024 if m and m.group(2) else 1000) ** ("KMGT".index(m.group(1).upper()) + 1)) if m else 0.0
    return abs(b - want) <= max(0.05 * want, step + 1)


def fix_memtemp(out: dict, res: dict) -> dict:
    if out.get("mem_ok") is not False or not mem_close((res.get("plan") or {}).get("duckdb_mem_mb"), out.get("memory_limit")):
        return out
    names_old = [k for k, ok in (("TEMP", out.get("temp_ok")), ("記憶體", False), ("執行緒", out.get("threads_ok"))) if not ok]
    names_new = [k for k in names_old if k != "記憶體"]
    old, new = "沒生效:" + " · ".join(names_old), ("沒生效:" + " · ".join(names_new)) if names_new else ""
    s = out.get("summary") or ""
    if new:
        s = s.replace(old, new)
    else:
        for pat in (";" + old, old + ";", " · " + old):
            if pat in s:
                s = s.replace(pat, "", 1)
                break
    out.update(mem_ok=True, summary=s + " · 記憶體 %s ≈ 預算(DuckDB 顯示一位小數)" % out.get("memory_limit"))
    other = "onedrive" in str(out.get("temp_root", "")).lower() or bool(res.get("temp_low"))
    if not names_new and not other and not out.get("why") and out.get("duckdb") is not None:
        out["lamp"] = "GREEN"
    return out


def probe_memtemp(res: dict, py: str | None = None, timeout: float = 60) -> dict:
    return fix_memtemp(_PROBE_ORIG(res, py, timeout), res)


# ---------------------------------------------------------------- ③ 加速器 + 網路工具(鎖驗證 · 本輪鉤 · 收據)
def lock_state(path: Path, sha: str | None) -> str:
    if not sha:
        return "NOLOCK"
    try:
        b = Path(path).read_bytes()
    except OSError:
        return "MISSING"
    if hashlib.sha256(b).hexdigest() == sha:
        return "EXACT"
    n = b[3:] if b.startswith(b"\xef\xbb\xbf") else b
    if hashlib.sha256(n.replace(b"\r\n", b"\n")).hexdigest() == sha:
        return "EOL_BOM_EQUIVALENT"
    return "MISMATCH"


def tools_resolve(via: Path | None = None) -> dict:
    """鎖冊尾版指的那支(在就用)> glob 尾版;回每件的路徑 · 版號 · 鎖狀態。只讀。"""
    via = Path(via or V0100.VIA)
    sup = via / "supportive modules"
    books = sorted((sup / "registry").glob("VIA_ToolVersion_Lock_v*.json"), key=_vnum_v0115)
    lock, book = {}, None
    if books:
        book = books[-1]
        try:
            lock = json.loads(book.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            lock = {}
    out = {"sup": str(sup), "book": book.name if book else None}
    for kind, stem, sub, _envk in TOOL_KINDS_V0115:
        hits = sorted((sup / sub).glob(stem + "_v*.py") if sub else sup.glob(stem + "_v*.py"), key=_vnum_v0115)
        tail = hits[-1] if hits else None
        ent = lock.get(kind) if isinstance(lock.get(kind), dict) else {}
        lp = (via.parent / ent["path"]) if ent.get("path") else None
        pick = lp if (lp is not None and lp.is_file()) else tail
        out[kind] = {"path": str(pick) if pick else None, "name": pick.name if pick else None, "tail": tail.name if tail else None,
                     "lock_version": ent.get("version"), "state": lock_state(pick, ent.get("sha256")) if pick else "MISSING",
                     "from": "鎖冊" if pick is not None and pick == lp else "glob 尾版"}
    return out


def tools_line(t: dict) -> str:
    a, n = t["accelerator"], t["network"]
    return ("[鎖驗證] accelerator=%s · network=%s(冊 %s)\n  [加速] %s · [網路] %s → 每個子行程(本輪鉤 %s;VIA_VDF_TOOLS=0 不掛)"
            % (a["state"], n["state"], t.get("book") or "—", a["name"] or "缺", n["name"] or "缺", HOOK_TAG_V0115))


TOOLS_SNIPPET_V0115 = r'''

def _vdf_tools():
    # v0115:每個子行程起跑先載最新加速器(VeritasCeleritas,立即載入)+ 網路工具(VeritasAegisNexus,LazyLoader 綁定最新那支、
    # 第一次用到才執行 —— 立即載入會連帶 import pandas → numexpr,改變 numexpr 初始化順序);載完環境變數全數還原成 VDF 給的;一行收據。
    if os.environ.get("VIA_VDF_TOOLS", "1") == "0" or getattr(sys, "_vdf_tools_tag", None):
        return
    sys._vdf_tools_tag = _TAG
    import time
    import importlib.util
    t0 = time.time()
    keep = dict(os.environ)
    rec = {"pid": os.getpid(), "argv": " ".join(str(a) for a in (getattr(sys, "argv", None) or [])[:2])[-160:], "tag": _TAG}
    sup = os.environ.get("VIA_VDF_SUP_DIR") or ""
    for d in (sup, os.path.join(sup, "network") if sup else ""):
        if d and os.path.isdir(d) and d not in sys.path:
            sys.path.append(d)
    for key, mod, envk, lazy in (("accel", "VeritasCeleritas", "VIA_VDF_ACCEL_PATH", False), ("net", "VeritasAegisNexus", "VIA_VDF_NET_PATH", True)):
        p = os.environ.get(envk) or ""
        try:
            if mod in sys.modules:
                rec[key] = os.path.basename(getattr(sys.modules[mod], "__spec__", None) and sys.modules[mod].__spec__.origin or mod)
                continue
            if not (p and os.path.isfile(p)):
                rec[key] = None
                rec[key + "_why"] = "路徑沒給 / 不在"
                continue
            spec = importlib.util.spec_from_file_location(mod, p)
            if lazy:
                spec.loader = importlib.util.LazyLoader(spec.loader)
            m = importlib.util.module_from_spec(spec)
            sys.modules[mod] = m
            spec.loader.exec_module(m)
            rec[key] = os.path.basename(p)
            rec[key + "_mode"] = "lazy" if lazy else "loaded"
        except BaseException as exc:  # noqa: BLE001 — 工具壞了不連累本行程(照實記)
            sys.modules.pop(mod, None)
            rec[key] = None
            rec[key + "_why"] = (type(exc).__name__ + ": " + str(exc))[:160]
        finally:
            changed = [k for k in set(os.environ) | set(keep) if os.environ.get(k) != keep.get(k)]
            for k in changed:                  # 加速器 import 會改 OMP / MKL / POLARS … 17 個變數 → 全數還原(VDF 的預算優先)
                if k in keep:
                    os.environ[k] = keep[k]
                else:
                    os.environ.pop(k, None)
            if changed:
                rec["restored"] = rec.get("restored", 0) + len(changed)
    try:
        n = int(keep.get("OMP_NUM_THREADS") or 0)
        if n > 0 and "numpy" in sys.modules:
            from threadpoolctl import threadpool_limits
            threadpool_limits(n)
            rec["pool"] = n
    except Exception:  # noqa: BLE001 — 沒有 threadpoolctl → 只靠環境變數
        pass
    rec.setdefault("restored", 0)
    rec["secs"] = round(time.time() - t0, 3)
    log = os.environ.get("VIA_VDF_TOOLS_LOG")
    if log:
        try:
            import json
            with open(log, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except Exception:  # noqa: BLE001
            pass


try:
    _vdf_tools()
except Exception:  # noqa: BLE001
    pass
'''


def hook_src_v0115() -> str:
    src = _V0107_G["HOOK_SRC"].replace(_V0107_G["HOOK_TAG"], HOOK_TAG_V0115).replace("v0107 每輪寫進", "v0115 每輪寫進")
    anchor = "try:\n    _install()"                # 工具先載、DuckDB 鉤後裝:加速器 import 會用 find_spec("duckdb") 探套件,先裝的鉤會被這一探吃掉
    if anchor not in src:
        raise RuntimeError("v0107 鉤原文對不上接點(_install)")
    return src.replace(anchor, TOOLS_SNIPPET_V0115.strip("\n") + "\n" + anchor, 1)


HOOK_SRC_V0115 = hook_src_v0115()


def tools_env(res: dict, t: dict | None = None) -> dict:
    t = t or _RUN15["tools"] or tools_resolve()
    env = {"VIA_VDF_SUP_DIR": t["sup"], "VIA_VDF_TOOLS_LOG": str(Path(res["temp_run"]) / "tools_receipts.jsonl")}
    for kind, _stem, _sub, envk in TOOL_KINDS_V0115:
        if t[kind]["path"]:
            env[envk] = t[kind]["path"]
    return env


def tools_summary(temp_run: str | None) -> dict:
    out = {"n": 0, "accel": 0, "net": 0, "fail": [], "restored": 0, "avg_secs": None}
    if not temp_run:
        return out
    f = Path(temp_run) / "tools_receipts.jsonl"
    rows = []
    if f.is_file():
        for ln in f.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                rows.append(json.loads(ln))
            except ValueError:
                continue
    out["n"] = len(rows)
    out["accel"] = sum(1 for r in rows if r.get("accel"))
    out["net"] = sum(1 for r in rows if r.get("net"))
    out["restored"] = sum(1 for r in rows if r.get("restored"))
    out["fail"] = [{"argv": r.get("argv"), "accel": r.get("accel_why"), "net": r.get("net_why")} for r in rows if not (r.get("accel") and r.get("net"))][:10]
    out["avg_secs"] = round(sum(float(r.get("secs") or 0) for r in rows) / len(rows), 3) if rows else None
    return out


def summary_line(s: dict) -> str:
    return ("[加速] 子行程 %d 個已掛 · 加速器 %d/%d · 網路工具 %d/%d · 執行緒預算套回 %d · 平均載入 %s 秒%s"
            % (s["n"], s["accel"], s["n"], s["net"], s["n"], s["restored"], s["avg_secs"],
               (" · 失敗 %d(例 %s)" % (len(s["fail"]), s["fail"][0])) if s["fail"] else ""))


def load_tools_here(t: dict) -> dict:
    """本行程(啟動器)也載一次;載完環境全還原(不讓加速器改的 17 個變數漏進子行程 —— 子行程由本輪鉤自己載、自己套預算)。"""
    keep = dict(os.environ)
    got = {}
    try:
        for kind, mod, sub, _envk in TOOL_KINDS_V0115:
            p = t[kind]["path"]
            if mod in sys.modules or not p:
                got[kind] = mod in sys.modules
                continue
            for d in (t["sup"], str(Path(t["sup"]) / "network")):
                if d not in sys.path:
                    sys.path.append(d)
            try:
                spec = importlib.util.spec_from_file_location(mod, p)
                if kind == "network":                 # 同本輪鉤:網路工具綁最新那支、第一次用到才執行
                    spec.loader = importlib.util.LazyLoader(spec.loader)
                m = importlib.util.module_from_spec(spec)
                sys.modules[mod] = m
                spec.loader.exec_module(m)
                got[kind] = "lazy" if kind == "network" else True
            except Exception as exc:  # noqa: BLE001
                sys.modules.pop(mod, None)
                got[kind] = "%s: %s" % (type(exc).__name__, str(exc)[:80])
    finally:
        os.environ.clear()
        os.environ.update(keep)
    return got


# ---------------------------------------------------------------- ④ 對照只讀本輪的家
def db_files(opt) -> list:
    home = getattr(opt, "db_home", None) or os.environ.get("VIA_VDF_DB_HOME")
    if not home or not Path(home).is_dir():
        return _DB_FILES_V0113(opt)
    best: dict = {}
    for f in Path(home).rglob("*.duckdb"):
        low = str(f).lower()
        if f.name.endswith(".wal") or "_repo_" in f.name or "stash" in low or "selftest" in low:
            continue
        try:
            rank = (("mega" in f.parts) or ("active_tw_etf" in str(f)), f.stat().st_size)
        except OSError:
            continue
        k = os.path.normcase(f.name)
        if k not in best or rank > best[k][0]:
            best[k] = (rank, f)
    return [best[k][1] for k in sorted(best)]


# ---------------------------------------------------------------- ⑤ 引擎流程的並行預算 · 子行程環境
def engine_jobs(res: dict, env: dict | None = None) -> dict:
    env = os.environ if env is None else env
    cpu, mem, plan = res.get("cpu") or {}, res.get("mem") or {}, res.get("plan") or {}
    usable = cpu.get("usable") or os.cpu_count() or 1
    avail = mem.get("avail_mb")
    jobs = max(1, min(usable - 1, ((avail - V0100.RESERVE_MB) // PER_JOB_MB_V0115) if avail else usable - 1))
    others = max(0, int(plan.get("slots") or 1) - 1)
    per = max(256, int(((avail if avail is not None else 4096) - V0100.RESERVE_MB) * mem_fraction()) // (jobs + others))
    out = {"VIA_VDF_LAUNCH_JOBS": str(jobs), "VIA_VDF_LAUNCH_MEM_MB": str(per), "VIA_VDF_LAUNCH_THREADS": "1"}
    return {k: env.get(k) or v for k, v in out.items()}       # 操作員自己設了就照用


def flow_env(res: dict, flow: str, base_env: dict | None = None) -> dict:
    env = _FLOW_ENV_PRIOR(res, flow, base_env)
    if not _RUN15["on"]:
        return env
    _RUN15["temp_run"] = res.get("temp_run")
    env.update(tools_env(res))
    if flow == "engines":
        env.update(engine_jobs(res, env))
    return env


# ---------------------------------------------------------------- 換裝 / 還原(前版自測看它自己的狀態)
def _patch_v0115() -> None:
    V0100.plan_slots = plan_slots
    _V0107_G["probe_memtemp"] = probe_memtemp
    _V0111_G["db_files"] = db_files
    for m in _FLOW_ENV_OWNERS:
        m.flow_env = flow_env
    PRIOR.activate = activate


def _unpatch_v0115() -> None:
    V0100.plan_slots = _PLAN_SLOTS_ORIG
    _V0107_G["probe_memtemp"] = _PROBE_ORIG
    _V0111_G["db_files"] = _DB_FILES_V0113
    for m in _FLOW_ENV_OWNERS:
        m.flow_env = _FLOW_ENV_SAVED[id(m)]
    PRIOR.activate = _ACTIVATE_V0114


def activate(opt, manager: Path | None = None, py: str | None = None, temp: Path | None = None) -> dict:
    """同 v0114 activate;本輪:記憶體 0.9 · 本輪鉤載工具 · 對照只讀本輪的家 · 引擎並行預算;收尾印工具收據。"""
    t = tools_resolve()
    _RUN15.update(on=True, tools=t, temp_run=None)
    print("  " + tools_line(t), flush=True)
    here = load_tools_here(t) if os.environ.get("VIA_VDF_TOOLS", "1") != "0" else {}
    keep = (_V0107_G["HOOK_SRC"], _V0107_G["HOOK_TAG"], PRIOR.TAG, DBM._WRITE_REPORT_V0100)

    def _stamp(c, u=None):
        c["schema"], c["tag"] = SCHEMA_V0115, TAG
        c["tools"] = {"resolve": t, "launcher": here, "children": tools_summary(_RUN15["temp_run"])}
        return _WRITE_ORIG(c, u) if u is not None else _WRITE_ORIG(c)
    if os.environ.get("VIA_VDF_TOOLS", "1") != "0":
        _V0107_G["HOOK_SRC"], _V0107_G["HOOK_TAG"] = HOOK_SRC_V0115, HOOK_TAG_V0115
    PRIOR.TAG = TAG
    DBM._WRITE_REPORT_V0100 = _stamp
    try:
        card = _ACTIVATE_V0114(opt, manager, py, temp)
    finally:
        _V0107_G["HOOK_SRC"], _V0107_G["HOOK_TAG"], PRIOR.TAG, DBM._WRITE_REPORT_V0100 = keep
        _RUN15["on"] = False
    s = tools_summary(_RUN15["temp_run"])
    print("  " + summary_line(s), flush=True)
    card.setdefault("tools", {})["children"] = s
    return card


_patch_v0115()


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--selftest"]:
        return selftest()
    return PRIOR.main(argv)                       # v0114 main 叫模組全域 activate → 已換本版


def selftest() -> int:
    import shutil
    import subprocess
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

    print("=== %s · 薄尾自測(全部用記憶體 · 加速器 + 網路工具 · 對照只讀本輪的家 · 引擎並行)===" % TAG)
    cpu, mem = {"usable": 8, "logical": 8, "load1": 0.5}, {"avail_mb": 6680}
    off = plan_slots(cpu, mem)
    _RUN15["on"] = True
    try:
        on = plan_slots(cpu, mem)
    finally:
        _RUN15["on"] = False
    chk("① 全部用記憶體:8 核 · 可用 6680 MB · 3 條 → 每條 %d MB(前版 %d MB · 公式 (6680 − 1024) × 0.9 ÷ 3)" % (on["duckdb_mem_mb"], off["duckdb_mem_mb"]),
        on["duckdb_mem_mb"] == int((6680 - 1024) * 0.9) // 3 and off["duckdb_mem_mb"] == int((6680 - 1024) * 0.6) // 3 and on["slots"] == 3, (on, off))
    chk("② 記憶體誤報:預算 1131 MB vs 顯示「1.0 GiB」= 生效 · 2818 vs「2.6 GiB」= 生效 · 1131 vs「3.9 GiB」/「500.0 MiB」= 沒生效",
        mem_close(1131, "1.0 GiB") and mem_close(2818, "2.6 GiB") and not mem_close(1131, "3.9 GiB") and not mem_close(1131, "500.0 MiB"))
    fake = {"duckdb": "2.0.0", "temp_ok": True, "mem_ok": False, "threads_ok": True, "memory_limit": "1.0 GiB", "temp_root": "/tmp/x", "lamp": "YELLOW",
            "summary": "DuckDB 溢寫 → /tmp/x · 記憶體 1.0 GiB(預算 1131 MB)· 執行緒 2 · 鉤 VDF 本輪鉤 · temp 剩 5 MB · 沒生效:記憶體"}
    fx = fix_memtemp(dict(fake), {"plan": {"duckdb_mem_mb": 1131}})
    fx2 = fix_memtemp(dict(fake, threads_ok=False, summary=fake["summary"].replace("沒生效:記憶體", "沒生效:記憶體 · 執行緒")), {"plan": {"duckdb_mem_mb": 1131}})
    chk("③ 起跑實測卡改判:只有記憶體誤報 → GREEN、拿掉「沒生效:記憶體」;還有執行緒沒生效 → 仍黃、只剩「沒生效:執行緒」",
        fx["lamp"] == "GREEN" and "沒生效" not in fx["summary"] and fx2["lamp"] == "YELLOW" and "沒生效:執行緒" in fx2["summary"]
        and "記憶體 ·" not in fx2["summary"].split("沒生效:")[-1], (fx["summary"], fx2["summary"]))
    tmp = Path(tempfile.mkdtemp(prefix="vdf_act0115_"))
    try:
        a = tmp / "tool.py"
        a.write_bytes(b"x = 1\n")
        sha = hashlib.sha256(b"x = 1\n").hexdigest()
        c = tmp / "tool_crlf.py"
        c.write_bytes(b"\xef\xbb\xbfx = 1\r\n")
        chk("④ 鎖驗證:原位元相同 = EXACT · CRLF + BOM = EOL_BOM_EQUIVALENT · 改過 = MISMATCH · 冊沒鎖 = NOLOCK",
            lock_state(a, sha) == "EXACT" and lock_state(c, sha) == "EOL_BOM_EQUIVALENT" and lock_state(a, "0" * 64) == "MISMATCH"
            and lock_state(a, None) == "NOLOCK")
        t = tools_resolve()
        chk("⑤ 本倉工具:加速器 %s(%s · %s)· 網路工具 %s(%s · %s)" % (t["accelerator"]["name"], t["accelerator"]["from"], t["accelerator"]["state"],
                                                                 t["network"]["name"], t["network"]["from"], t["network"]["state"]),
            (t["accelerator"]["name"] or "").startswith("VeritasCeleritas_v") and (t["network"]["name"] or "").startswith("VeritasAegisNexus_v")
            and t["accelerator"]["state"] in ("EXACT", "EOL_BOM_EQUIVALENT", "NOLOCK") and t["network"]["state"] in ("EXACT", "EOL_BOM_EQUIVALENT", "NOLOCK"), t)
        hd = tmp / "pyhook"
        hd.mkdir()
        (hd / "sitecustomize.py").write_text(HOOK_SRC_V0115, encoding="utf-8")
        log = tmp / "tools_receipts.jsonl"
        res = {"temp_run": str(tmp)}
        base = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "VIA_DUCK_TEMP", "VIA_VDF_DUCK_HOOK", "VIA_VDF_TOOLS")}
        env = dict(base, PYTHONPATH=str(hd), OMP_NUM_THREADS="1", POLARS_MAX_THREADS="1", VIA_DUCKDB_MEM="900MB", **tools_env(res, t))
        env.pop("NUMEXPR_MAX_THREADS", None)
        code = ("import os,sys,json;pre={'pandas':'pandas' in sys.modules,'nemx':os.environ.get('NUMEXPR_MAX_THREADS')};"
                "d=None\ntry:\n import duckdb;d=getattr(duckdb,'_via_duck_temp',None)\nexcept ImportError:\n d='no-duckdb'\n"
                "n=sys.modules.get('VeritasAegisNexus');k=len(dir(n)) if n is not None else 0;"
                "print('VDFT '+json.dumps(dict(pre,a='VeritasCeleritas' in sys.modules,n=n is not None,k=k,duck=d,"
                "omp=os.environ.get('OMP_NUM_THREADS'),pol=os.environ.get('POLARS_MAX_THREADS'),tag=getattr(sys,'_vdf_tools_tag',None))))")
        cp = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
        got = json.loads(next((ln[5:] for ln in cp.stdout.splitlines() if ln.startswith("VDFT ")), "{}"))
        rec = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines()] if log.is_file() else []
        chk("⑥ 本輪鉤真的掛上:子行程起跑就有 VeritasCeleritas(已載)+ VeritasAegisNexus(綁最新 · 用到才載 → 用到後 %s 個名字)·"
            " 起跑沒帶進 pandas · 環境原樣(OMP / POLARS = 1 · NUMEXPR_MAX_THREADS 沒被加)· DuckDB 鉤仍在 · 一行收據" % got.get("k"),
            got.get("a") and got.get("n") and (got.get("k") or 0) > 10 and got.get("pandas") is False and got.get("nemx") is None
            and got.get("omp") == "1" and got.get("pol") == "1" and got.get("tag") == HOOK_TAG_V0115 and got.get("duck") in (HOOK_TAG_V0115, "no-duckdb")
            and len(rec) == 1 and rec[0].get("accel") and rec[0].get("net") and rec[0].get("net_mode") == "lazy", (got, rec, cp.stderr[-300:]))
        cp2 = subprocess.run([sys.executable, "-c", code], env=dict(env, VIA_VDF_TOOLS="0"), capture_output=True, text=True, encoding="utf-8",
                             errors="replace", timeout=120)
        got2 = json.loads(next((ln[5:] for ln in cp2.stdout.splitlines() if ln.startswith("VDFT ")), "{}"))
        s = tools_summary(str(tmp))
        chk("⑦ VIA_VDF_TOOLS=0 → 不掛(回前版行為)· 收尾彙總 %s" % summary_line(s),
            got2.get("a") is False and got2.get("n") is False and s["n"] == 1 and s["accel"] == 1 and s["net"] == 1, (got2, s))
        keep_src = (_V0107_G["HOOK_SRC"], _V0107_G["HOOK_TAG"])
        _V0107_G["HOOK_SRC"], _V0107_G["HOOK_TAG"] = HOOK_SRC_V0115, HOOK_TAG_V0115
        try:
            hd2 = PRIOR.hook_dir({"temp_run": str(tmp / "run_x")})
            written = (Path(hd2) / "sitecustomize.py").read_text(encoding="utf-8")
        finally:
            _V0107_G["HOOK_SRC"], _V0107_G["HOOK_TAG"] = keep_src
        chk("⑦b 換在本體模組全域:v0107 hook_dir 真的寫出 v0115 鉤(含 _vdf_tools · 標籤 %s)—— 只換抄本的那份寫出來會是 v0107 舊鉤" % HOOK_TAG_V0115,
            "_vdf_tools()" in written and HOOK_TAG_V0115 in written and _V0107_G["HOOK_SRC"] == keep_src[0], written[:120])
        home, other = tmp / "home", tmp / "repo_hub"
        for d, name, size in ((home / "output_hub", "vdf_tw_market.duckdb", 10), (home / "output_hub" / "mega", "vdf_tw_market.duckdb", 99),
                              (home / "output_hub", "aaii_sentiment.duckdb", 5), (other, "vdf_tw_market.duckdb", 500), (other, "extra.duckdb", 5)):
            d.mkdir(parents=True, exist_ok=True)
            (d / name).write_bytes(b"0" * size)
        o = types.SimpleNamespace(db_home=str(home), fetch_home=str(other.parent))
        got_f = db_files(o)
        chk("⑧ 對照只讀本輪的家:只收家裡的庫(倉內 / 擷取家的不收)· 同名取 mega · 一名一檔",
            sorted(x.name for x in got_f) == ["aaii_sentiment.duckdb", "vdf_tw_market.duckdb"] and any("mega" in x.parts for x in got_f)
            and all(str(home) in str(x) for x in got_f), [str(x) for x in got_f])
        chk("⑨ 沒有家 → 照前版(v0113 db_files)", db_files(types.SimpleNamespace(db_home=None, fetch_home=None)) == _DB_FILES_V0113(
            types.SimpleNamespace(db_home=None, fetch_home=None)))
        bk, bh = PRIOR.data_home_book(HERE)
        chk("⑨b 本夾正本資料家冊尾版 %s:第一順位 = 操作員 2026-10-22 選的 via_database\\vdf_database(via_01_vdf 排第二)" % (bk.name if bk else None),
            bk is not None and bk.name == "VDF_DataHome_SSOT_v0101.json" and bh and str(bh[0].get("db_home", "")).endswith("vdf_database")
            and any(str(h.get("db_home", "")).endswith("via_01_vdf") for h in bh[1:]), (bk, bh))
        ej = engine_jobs({"cpu": cpu, "mem": mem, "plan": {"slots": 3}}, env={})
        ej2 = engine_jobs({"cpu": cpu, "mem": mem, "plan": {"slots": 3}}, env={"VIA_VDF_LAUNCH_JOBS": "2"})
        chk("⑩ 引擎流程預算:8 核 · 6680 MB → 工作 7 · 每支 (6680−1024)×0.9÷(7+2) = %s MB · 執行緒 1;操作員設了工作數照用" % ej["VIA_VDF_LAUNCH_MEM_MB"],
            ej["VIA_VDF_LAUNCH_JOBS"] == "7" and ej["VIA_VDF_LAUNCH_MEM_MB"] == str(int((6680 - 1024) * 0.9) // 9) and ej2["VIA_VDF_LAUNCH_JOBS"] == "2", (ej, ej2))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    chk("⑪ 換裝在位:plan_slots · probe_memtemp · 對照 db_files(v0111 全域)· flow_env(鏈上 %d 處)· v0114 activate → 本版" % len(_FLOW_ENV_OWNERS),
        V0100.plan_slots is plan_slots and _V0107_G["probe_memtemp"] is probe_memtemp and _V0111_G["db_files"] is db_files
        and all(m.flow_env is flow_env for m in _FLOW_ENV_OWNERS) and PRIOR.activate is activate)
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("⑫ VDF 獨立:不匯入他系統程式(CGC_ · VRN_ · VCGC)· 兩座橋在 · 同意閘不寫(只原樣傳)· 不碰 TA-Lib",
        not re.search(r"^\s*(import|from)\s+(CGC_|VRN_|VCGC)", src, re.M) and "VIA:ACCEL-BRIDGE" in src and "VIA:NET-BRIDGE" in src
        and "_CONSENT\"] =" not in body and "talib" not in body.lower().replace("ta-lib", ""))
    if f:
        print("[計] %s 自測 %d/%d · FAIL" % (TAG, p, p + f))
        return 1
    print("[計] %s 本版 %d/%d · PASS" % (TAG, p, p + f))
    if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1":
        return 0
    _unpatch_v0115()
    try:
        rc1 = PRIOR.selftest()
    finally:
        _patch_v0115()
    print("[計] %s 前版鏈 rc %s · %s" % (TAG, rc1, "PASS" if rc1 == 0 else "FAIL"))
    return rc1 if rc1 in (0, 1, 2, 3) else 1


if __name__ == "__main__":
    raise SystemExit(main())
