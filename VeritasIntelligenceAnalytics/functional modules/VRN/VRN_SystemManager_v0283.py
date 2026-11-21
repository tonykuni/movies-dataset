#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0283 — 薄尾(v0282 以前一字不動):launch --run 走 TEMP(記憶體不足溢寫)· 起跑前備份庫 · resources 動詞

操作員 2026-11-22:「善用TEMP支援記憶體不足 備份 GRAPHIFY OMNIROUTE AGENCY-MEM」。
量過再做(容器 2026-11-22):VDF 啟動器每輪有本輪鉤(DuckDB 溢寫 → TEMP · 記憶體上限 · 執行緒),桌機實跑 ①b GREEN;
VRN 的 `launch --run` 直接起 RoundAll,子行程沒有任何 DuckDB 溢寫 / 記憶體上限(VRN 現役尾版 95 支裡 20 支開 DuckDB);
VRN_MDL260 雖設了 VIA_DUCKDB_TEMP_DIR,但 VRN 沒有一支 Python 讀它 → 只有標記、沒生效(黃)。

  launch --run(其餘照 v0269 的 launch):
    ① TEMP:本輪夾 <VIA_TEMP_ROOT | %LOCALAPPDATA%\\VIA_TEMP>\\VRN\\run_<時戳>(在 OneDrive 底下就改用系統 TEMP);
       本輪鉤 sitecustomize.py 經 PYTHONPATH 帶進每個 Python 子行程:duckdb.connect 自動補 temp_directory(本輪夾 \\ p<pid>)·
       memory_limit(可用記憶體 × 0.5 ÷ 3 道 · 下限 256 MB)· threads;呼叫端自己給的照它的;TMP / TEMP / TMPDIR 也指本輪夾。
       起跑前用同一份環境實跑一支探針子行程,讀回 DuckDB 的 temp_directory / memory_limit —— 生效才算綠(標記不算)。
    ② 備份:輸出夾(VRN2_Output_Config.json 的 output_dir 或 VRN2_OUTPUT_DIR)底下的 *.duckdb(含 .wal)起跑前整檔複製到
       <VIA_BACKUP_ROOT | %LOCALAPPDATA%\\VIA_BACKUP>\\VRN\\<時戳>(本機磁碟、不進 OneDrive)· 逐檔 sha256 驗過 · MANIFEST.json · 只留最近 3 輪;
       空間不夠(< 2 倍)就不備份、照實黃,不硬寫。parquet 是只增分割檔,不複製,只把清單(路徑 · 大小)記進 MANIFEST 供事後對照。
    ③ 跑完:本輪溢寫夾刪掉(收據留在 VIA_Reports/vrn/launch/VRN_LAUNCH_RES_latest.json,不入倉);VRN 自己的舊輪(> 24 小時 · 行程不在)只留 5 輪。
  resources [--json](只讀 · 零寫入):TEMP · 記憶體預算 · 最近一次備份 · 最近一次 launch 的鉤生效 · Graphify 收據(VRN 那張圖)·
    OmniRoute 不在 VRN 執行路徑(語法樹掃 VRN 現役尾版)· agentmemory(VCGC-REQ185 決定不引入 → 灰)。
邊界:VRN 自己的入口與夾;不設他系統旗標;不出網;不起 Graphify / OmniRoute;不碰 TA-Lib;不寫契約檔 / 資產冊。自測:--selftest
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

import ast
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAMILY = "VRN_SystemManager"
TAG = "VRN_SystemManager v0283"
HOOK_TAG = "vrn-launch-v0283"
LANES = 3                      # VRN_MDL260 v0103 起固定 3 道
MEM_FRAC = 0.5
MEM_FLOOR_MB = 256
KEEP_BACKUPS = 3
KEEP_RUNS = 5
RUN_MAX_AGE_H = 24.0
STALE_H = 48.0


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0283", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def launch_modules() -> list:
    """前版鏈裡真的跑 launch 的模組(全域同時有 v268_launch 與 sm_child_env)。"""
    out = []
    for m in list(sys.modules.values()):
        f = str(getattr(m, "__file__", "") or "")
        if FAMILY in Path(f).name and Path(f).resolve().parent == HERE:
            d = vars(m)
            if "v268_launch" in d and "sm_child_env" in d and m not in out:
                out.append(m)
    return out


def via_root() -> Path:
    for m in launch_modules():
        if "sm_via_root" in vars(m):
            try:
                return Path(m.sm_via_root())
            except Exception:  # noqa: BLE001
                break
    return HERE.parents[1]


# ---------------------------------------------------------------- 記憶體 · TEMP
def mem_available_mb() -> tuple:
    """(可用 MB, 來源);量不到 = (None, 原因)。先試共用件 SUP_MDL755(鎖冊 frame),再 psutil · /proc · Windows API。"""
    try:
        lock = json.loads((via_root() / "supportive modules" / "registry" / "VIA_ToolVersion_Lock_v0100.json").read_text(encoding="utf-8"))
        p = Path(str((lock.get("frame") or {}).get("path") or ""))
        p = p if p.is_absolute() else via_root().parent / p
        if p.is_file():
            spec = importlib.util.spec_from_file_location("sup_mdl755_for_vrn_v0283", p)
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
            v = m.mem_available()
            if v:
                return int(v) // 2 ** 20, "SUP_MDL755"
    except Exception:  # noqa: BLE001 — 共用件不在 / 壞了 → 本檔自己量(系統獨立)
        pass
    try:
        import psutil
        return int(psutil.virtual_memory().available) // 2 ** 20, "psutil"
    except Exception:  # noqa: BLE001
        pass
    mi = Path("/proc/meminfo")
    if mi.is_file():
        for ln in mi.read_text().splitlines():
            if ln.startswith("MemAvailable:"):
                return int(ln.split()[1]) // 1024, "/proc/meminfo"
    if os.name == "nt":
        try:
            import ctypes

            class _MS(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong), ("ullTotalPhys", ctypes.c_ulonglong),
                            ("ullAvailPhys", ctypes.c_ulonglong), ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong), ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            st = _MS()
            st.dwLength = ctypes.sizeof(_MS)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st)):
                return int(st.ullAvailPhys) // 2 ** 20, "GlobalMemoryStatusEx"
        except Exception:  # noqa: BLE001
            pass
    return None, "量不到"


def budget_mb(avail_mb, lanes: int = LANES) -> int | None:
    if not avail_mb:
        return None
    return max(MEM_FLOOR_MB, int(avail_mb * MEM_FRAC / max(1, lanes)))


def _on_onedrive(p) -> bool:
    return "onedrive" in str(p).lower()


def temp_base(env=None) -> tuple:
    """(VRN 的 TEMP 根, 說明)。OneDrive 底下的一律不用(同步會拖慢、會把溢寫檔傳上雲)。"""
    env = os.environ if env is None else env
    for k, sub in (("VIA_TEMP_ROOT", ""), ("LOCALAPPDATA", "VIA_TEMP")):
        v = env.get(k)
        if v:
            b = Path(v) / sub if sub else Path(v)
            if not _on_onedrive(b):
                return b / "VRN", k
    return Path(tempfile.gettempdir()) / "VIA_TEMP" / "VRN", "系統 TEMP"


def backup_base(env=None) -> Path:
    env = os.environ if env is None else env
    for k, sub in (("VIA_BACKUP_ROOT", ""), ("LOCALAPPDATA", "VIA_BACKUP")):
        v = env.get(k)
        if v:
            b = Path(v) / sub if sub else Path(v)
            if not _on_onedrive(b):
                return b / "VRN"
    return Path.home() / ".via_backup" / "VRN"


def free_mb(p: Path) -> int | None:
    q = Path(p)
    while not q.exists() and q.parent != q:
        q = q.parent
    try:
        return shutil.disk_usage(q).free // 2 ** 20
    except OSError:
        return None


HOOK_SRC = r'''# VRN launch 本輪 DuckDB TEMP / 記憶體 / 執行緒掛鉤(VRN_SystemManager v0283 每輪寫進本輪 temp 夾;不在倉內、不進環境)
# 跑完往 sys.path 後面接力原有的 sitecustomize(不回頭、不遞迴)。VIA_DUCK_TEMP=0 不掛。
import os, sys
_TAG = "%(tag)s"


def _defaults():
    d = {}
    base = os.environ.get("VIA_DUCKDB_TEMP_DIR")
    if base:
        p = os.path.join(base, "p%%d" %% os.getpid())
        try:
            os.makedirs(p, exist_ok=True)
            d["temp_directory"] = p
        except OSError:
            pass
    if os.environ.get("VIA_DUCKDB_MEM"):
        d["memory_limit"] = os.environ["VIA_DUCKDB_MEM"]
    try:
        th = int(os.environ.get("VIA_DUCKDB_THREADS") or 0)
    except ValueError:
        th = 0
    if th > 0:
        d["threads"] = th
    return d


def _patch(mod, keys):
    if getattr(mod, "_via_vrn_duck", None):
        return mod
    orig = mod.connect

    def connect(*args, **kw):
        try:
            a = list(args)
            cfg = dict((a[2] if len(a) >= 3 else kw.get("config")) or {})
            for k, v in _defaults().items():
                if k in keys:
                    cfg.setdefault(k, v)
            if len(a) >= 3:
                a[2] = cfg
            else:
                kw["config"] = cfg
            return orig(*a, **kw)
        except TypeError:
            return orig(*args, **kw)

    connect.__doc__ = orig.__doc__
    connect.__wrapped__ = orig
    mod.connect = connect
    mod._via_vrn_duck = _TAG
    return mod


class _VrnDuckFinder:
    def __init__(self, keys):
        self.keys = keys

    def find_spec(self, name, path=None, target=None):
        if name != "duckdb":
            return None
        try:
            sys.meta_path.remove(self)
        except ValueError:
            pass
        import importlib.util
        spec = importlib.util.find_spec("duckdb")
        if spec is None or spec.loader is None or not hasattr(spec.loader, "exec_module"):
            return spec
        real = spec.loader.exec_module
        keys = self.keys

        def exec_module(module):
            real(module)
            try:
                _patch(module, keys)
            except Exception:  # noqa: BLE001 — 掛不上 = 原生 duckdb 照用
                return
        spec.loader.exec_module = exec_module
        return spec


def _install():
    if os.environ.get("VIA_DUCK_TEMP", "1") == "0":
        return
    keys = ("threads",) if "via_duck_temp" in sys.modules else ("temp_directory", "memory_limit", "threads")
    if "duckdb" in sys.modules:
        _patch(sys.modules["duckdb"], keys)
    elif not any(type(f).__name__ == "_VrnDuckFinder" for f in sys.meta_path):
        sys.meta_path.insert(0, _VrnDuckFinder(keys))


def _chain_after_me():
    here = os.path.dirname(os.path.abspath(__file__))
    seen = False
    for d in list(sys.path):
        if d and os.path.abspath(d) == here:
            seen = True
            continue
        if not seen or not d:
            continue
        cand = os.path.join(d, "sitecustomize.py")
        if os.path.isfile(cand):
            import runpy
            try:
                runpy.run_path(cand, run_name="sitecustomize_after_vrn")
            except Exception:  # noqa: BLE001
                return
            return


try:
    _install()
except Exception:  # noqa: BLE001
    pass
try:
    _chain_after_me()
except Exception:  # noqa: BLE001
    pass
''' % {"tag": HOOK_TAG}

PROBE = r'''
import json, sys
out = {"hook": None, "duckdb": None}
try:
    import duckdb
except ImportError:
    print("VRNPROBE " + json.dumps(out)); sys.exit(0)
out["duckdb"] = duckdb.__version__
out["hook"] = getattr(duckdb, "_via_vrn_duck", None)
c = duckdb.connect()
for k in ("temp_directory", "memory_limit", "threads"):
    try:
        out[k] = str(c.execute("select current_setting('%s')" % k).fetchone()[0])
    except Exception as exc:
        out[k] = "?" + type(exc).__name__
c.close()
print("VRNPROBE " + json.dumps(out))
'''


def prepare_temp(env=None, now=None, avail=None) -> dict:
    """建本輪夾 + 本輪鉤;回 {run, hook_dir, env_add, budget_mb, ...}(還沒驗生效)。"""
    env = dict(os.environ if env is None else env)
    base, why = temp_base(env)
    stamp = (now or datetime.now()).strftime("run_%Y%m%d_%H%M%S") + "_p%d" % os.getpid()
    run = base / stamp
    for d in (run / "pyhook", run / "duckdb", run / "tmp"):
        d.mkdir(parents=True, exist_ok=True)
    (run / "pyhook" / "sitecustomize.py").write_text(HOOK_SRC, encoding="utf-8")
    (run / ".vrn_run").write_text(json.dumps({"pid": os.getpid(), "tag": HOOK_TAG, "ts": time.time()}), encoding="utf-8")
    av, src = (avail, "給定") if avail is not None else mem_available_mb()
    bud = budget_mb(av)
    thr = max(1, (os.cpu_count() or 2) // LANES)
    pp = [str(run / "pyhook")] + [x for x in (env.get("PYTHONPATH") or "").split(os.pathsep) if x]
    add = {"PYTHONPATH": os.pathsep.join(pp), "VIA_DUCKDB_TEMP_DIR": str(run / "duckdb"), "VIA_DUCKDB_THREADS": str(thr),
           "TMP": str(run / "tmp"), "TEMP": str(run / "tmp"), "TMPDIR": str(run / "tmp"), "VIA_VRN_TEMP_RUN": str(run)}
    if bud:
        add["VIA_DUCKDB_MEM"] = f"{bud}MB"
    return {"run": str(run), "base": str(base), "base_from": why, "hook_dir": str(run / "pyhook"), "env_add": add,
            "avail_mb": av, "mem_source": src, "budget_mb": bud, "threads": thr, "free_mb": free_mb(run)}


def probe(env: dict, py: str | None = None, timeout: float = 60.0) -> dict:
    """用同一份環境實跑一支子行程,讀回 DuckDB 設定 —— 生效才算(標記不算)。"""
    try:
        r = subprocess.run([py or sys.executable, "-c", PROBE], env=env, capture_output=True, text=True, timeout=timeout,
                           encoding="utf-8", errors="replace")
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"lamp": "YELLOW", "why": f"探針起不來:{type(exc).__name__}"}
    line = next((ln for ln in (r.stdout or "").splitlines() if ln.startswith("VRNPROBE ")), "")
    try:
        got = json.loads(line[len("VRNPROBE "):]) if line else {}
    except ValueError:
        got = {}
    if not got:
        return {"lamp": "YELLOW", "why": "探針沒回話 rc %s %s" % (r.returncode, (r.stderr or "")[-160:])}
    if got.get("duckdb") is None:
        return dict(got, lamp="GRAY", why="這個 Python 沒有 duckdb(VRN 走 pyarrow 備援;溢寫不適用)")
    tdir = env.get("VIA_DUCKDB_TEMP_DIR", "")
    ok_t = bool(tdir) and os.path.normcase(str(got.get("temp_directory", ""))).startswith(os.path.normcase(tdir))
    ok_m = ("VIA_DUCKDB_MEM" not in env) or not str(got.get("memory_limit", "")).startswith("?")
    lamp = "GREEN" if got.get("hook") == HOOK_TAG and ok_t and ok_m else "YELLOW"
    return dict(got, lamp=lamp, why="" if lamp == "GREEN" else "鉤沒生效(hook=%s · temp=%s)" % (got.get("hook"), got.get("temp_directory")))


def sweep_runs(base: Path, keep: int = KEEP_RUNS, max_age_h: float = RUN_MAX_AGE_H, now: float | None = None, apply: bool = True) -> list:
    """只清 VRN 自己的舊輪夾(有 .vrn_run 標記);行程還活著、還新的不碰;最新 keep 輪留著。"""
    now = now or time.time()
    runs = sorted((d for d in Path(base).glob("run_*") if (d / ".vrn_run").is_file()), key=lambda d: d.stat().st_mtime, reverse=True)
    gone = []
    for d in runs[keep:]:
        try:
            meta = json.loads((d / ".vrn_run").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            meta = {}
        if now - d.stat().st_mtime < max_age_h * 3600 or _alive(int(meta.get("pid") or 0)):
            continue
        if apply:
            shutil.rmtree(d, ignore_errors=True)
        gone.append(d.name)
    return gone


def _alive(pid: int) -> bool:
    if pid <= 0 or pid == os.getpid():
        return pid == os.getpid()
    try:
        if os.name == "nt":
            r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True, timeout=10)
            return str(pid) in (r.stdout or "")
        os.kill(pid, 0)
        return True
    except (OSError, subprocess.SubprocessError):
        return False


# ---------------------------------------------------------------- 備份
def output_dir(root: Path, env=None) -> Path | None:
    env = os.environ if env is None else env
    cfg = root / "VIA_Reports" / "vrn2" / "VRN2_Output_Config.json"
    try:
        v = json.loads(cfg.read_text(encoding="utf-8")).get("output_dir") if cfg.is_file() else None
    except (OSError, ValueError):
        v = None
    v = v or env.get("VRN2_OUTPUT_DIR")
    return Path(v) if v else None


_SKIP = ("backup", "stash", "selftest", "_repo_", "via_spill", ".tmp")


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def backup_db(out: Path | None, dest_base: Path, now=None, keep: int = KEEP_BACKUPS) -> dict:
    if out is None or not Path(out).is_dir():
        return {"lamp": "GRAY", "why": "沒有輸出夾(VRN2_Output_Config.json / VRN2_OUTPUT_DIR 都沒設)· 沒有庫可備"}
    out = Path(out)
    dbs = sorted(p for p in out.rglob("*") if p.is_file() and (p.suffix == ".duckdb" or p.name.endswith(".duckdb.wal"))
                 and not any(s in str(p.relative_to(out)).lower() for s in _SKIP))
    pq = sorted(p for p in out.rglob("*.parquet") if not any(s in str(p.relative_to(out)).lower() for s in _SKIP))
    size = sum(p.stat().st_size for p in dbs) // 2 ** 20
    if not dbs:
        return {"lamp": "GRAY", "why": f"輸出夾沒有 .duckdb(parquet {len(pq)} 支是只增分割檔,不需整檔備份)", "parquet": len(pq)}
    fr = free_mb(dest_base)
    if fr is not None and fr < 2 * size + 64:
        return {"lamp": "YELLOW", "why": f"備份夾空間不夠:要 {size} MB × 2 · 剩 {fr} MB → 這輪不備份", "size_mb": size}
    dest = Path(dest_base) / (now or datetime.now()).strftime("%Y%m%d_%H%M%S")
    rows, bad = [], []
    for p in dbs:
        rel = p.relative_to(out)
        t = dest / rel
        t.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, t)
        a, b = _sha(p), _sha(t)
        rows.append({"path": str(rel), "bytes": p.stat().st_size, "sha256": a})
        if a != b:
            bad.append(str(rel))
    man = {"tool": TAG, "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "source": str(out), "files": rows,
           "parquet": [{"path": str(p.relative_to(out)), "bytes": p.stat().st_size} for p in pq[:5000]], "parquet_n": len(pq)}
    (dest / "MANIFEST.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    olds = sorted((d for d in Path(dest_base).iterdir() if d.is_dir() and (d / "MANIFEST.json").is_file()), key=lambda d: d.name)
    for d in olds[:-keep]:
        shutil.rmtree(d, ignore_errors=True)
    if bad:
        return {"lamp": "RED", "why": "複本 sha256 對不上:" + " · ".join(bad[:3]), "dest": str(dest)}
    return {"lamp": "GREEN", "dest": str(dest), "files": len(rows), "size_mb": size, "parquet_n": len(pq), "kept": min(len(olds), keep)}


def latest_backup(dest_base: Path) -> dict:
    ds = sorted((d for d in Path(dest_base).glob("*") if (d / "MANIFEST.json").is_file()), key=lambda d: d.name) if Path(dest_base).is_dir() else []
    if not ds:
        return {"lamp": "GRAY", "line": f"還沒有備份({dest_base})· launch --run 起跑前自動備"}
    d = ds[-1]
    try:
        man = json.loads((d / "MANIFEST.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"lamp": "RED", "line": f"{d.name} MANIFEST 讀不懂"}
    miss = [f["path"] for f in man.get("files", []) if not (d / f["path"]).is_file() or (d / f["path"]).stat().st_size != f.get("bytes")]
    age = (time.time() - (d / "MANIFEST.json").stat().st_mtime) / 3600
    lamp = "RED" if miss else ("YELLOW" if age > STALE_H else "GREEN")
    return {"lamp": lamp, "line": f"{d.name} · 庫檔 {len(man.get('files', []))} · 大小對得上 {len(man.get('files', [])) - len(miss)}"
            f" · {age:.0f}h 前 · 留 {len(ds)} 輪" + (f" · 缺 {miss[:2]}" if miss else "") + (" · 過期" if age > STALE_H else "")}


# ---------------------------------------------------------------- launch --run
def _patch_env(extra: dict) -> list:
    """把前版 launch 用的 sm_child_env 換成「原本 + 本輪環境」;回 [(模組, 原函式)] 供還原。"""
    done = []
    for m in launch_modules():
        orig = vars(m)["sm_child_env"]

        def wrapped(_orig=orig):
            e = _orig()
            e.update(extra)
            return e
        wrapped.__wrapped__ = orig
        m.sm_child_env = wrapped
        done.append((m, orig))
    return done


def _receipt(root: Path, rec: dict) -> Path:
    d = root / "VIA_Reports" / "vrn" / "launch"
    d.mkdir(parents=True, exist_ok=True)
    p = d / "VRN_LAUNCH_RES_latest.json"
    p.write_text(json.dumps(rec, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return p


def launch_run(args: list, root: Path | None = None) -> int:
    root = root or via_root()
    t0 = time.time()
    rec = {"tool": TAG, "started": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    bk = backup_db(output_dir(root), backup_base())
    rec["backup"] = bk
    print(f"  [備份] {bk['lamp']} · " + (f"{bk.get('files')} 支庫檔 {bk.get('size_mb')} MB → {bk.get('dest')}(sha256 逐檔驗過 · 留 {KEEP_BACKUPS} 輪)"
                                         if bk["lamp"] == "GREEN" else bk.get("why", "")), flush=True)
    tp = prepare_temp()
    env = dict(os.environ, **tp["env_add"])
    pr = probe(env)
    rec.update(temp={k: v for k, v in tp.items() if k != "env_add"}, probe=pr)
    print(f"  [TEMP] {pr['lamp']} · DuckDB 溢寫 → {pr.get('temp_directory', tp['run'])} · 記憶體上限 {pr.get('memory_limit', '?')}"
          f"(可用 {tp['avail_mb']} MB × {MEM_FRAC} ÷ {LANES} 道 · 來源 {tp['mem_source']})· 執行緒 {tp['threads']} · temp 剩 {tp['free_mb']} MB"
          f" · 根 {tp['base_from']}" + (f" · {pr['why']}" if pr.get("why") else ""), flush=True)
    swept = sweep_runs(Path(tp["base"]))
    if swept:
        print(f"  [TEMP] 清掉 VRN 舊輪 {len(swept)} 個(> {RUN_MAX_AGE_H:.0f}h · 行程不在 · 留 {KEEP_RUNS} 輪)", flush=True)
    add = tp["env_add"] if pr["lamp"] in ("GREEN", "GRAY") else {k: v for k, v in tp["env_add"].items() if k in ("TMP", "TEMP", "TMPDIR")}
    patched = _patch_env(add)
    rc = 1
    try:
        rc = PRIOR.main(["launch", *args])
    finally:
        for m, orig in patched:
            m.sm_child_env = orig
        spill = sum(f.stat().st_size for f in Path(tp["run"], "duckdb").rglob("*") if f.is_file()) // 2 ** 20 if Path(tp["run"], "duckdb").is_dir() else 0
        for sub in ("duckdb", "tmp"):
            shutil.rmtree(Path(tp["run"]) / sub, ignore_errors=True)
        rec.update(rc=rc, secs=round(time.time() - t0, 1), spill_mb_left=spill, finished=datetime.now(timezone.utc).isoformat(timespec="seconds"))
        p = _receipt(root, rec)
        print(f"  [TEMP] 本輪溢寫夾已清(跑完時還留 {spill} MB)· 收據 {p.relative_to(root)}", flush=True)
    return rc


# ---------------------------------------------------------------- resources(只讀)
def _vrn_tails() -> list:
    fam = {}
    for p in HERE.glob("*.py"):
        m = re.match(r"(.+)_v(\d{4})\.py$", p.name)
        if m and (m.group(1) not in fam or int(m.group(2)) > _vnum(fam[m.group(1)])):
            fam[m.group(1)] = p
    return sorted(fam.values())


def omniroute_scan(files=None) -> dict:
    """語法樹掃:匯入 omniroute、或字串常數裡有它的本機埠 :20128 的現役尾版 → 紅(OmniRoute 不得進 VRN 執行路徑)。"""
    hit, bad = [], 0
    files = list(files) if files is not None else _vrn_tails()
    for p in files:
        try:
            t = ast.parse(Path(p).read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            bad += 1
            continue
        for n in ast.walk(t):
            names = [a.name for a in n.names] if isinstance(n, ast.Import) else [n.module or ""] if isinstance(n, ast.ImportFrom) else []
            s = n.value.lower() if isinstance(n, ast.Constant) and isinstance(n.value, str) else ""
            if any("omniroute" in x.lower() for x in names) or ":20128" in s:      # 匯入它 · 或打它的本機埠(說明文字提到名字不算)
                if Path(p).name != Path(__file__).name:
                    hit.append(Path(p).name)
                break
    return {"scanned": len(files), "unparsed": bad, "hits": sorted(set(hit))}


def resources(root: Path | None = None) -> dict:
    root = root or via_root()
    rows = {}
    base, why = temp_base()
    fr = free_mb(base)
    olds = [d for d in base.glob("run_*") if (d / ".vrn_run").is_file()] if base.is_dir() else []
    rows["TEMP"] = {"lamp": "GREEN" if fr and fr >= 2048 else ("YELLOW" if fr else "GRAY"),
                    "line": f"{base}(來源 {why} · 不在 OneDrive)· 剩 {fr} MB · 舊輪 {len(olds)}" + (" · 剩不到 2 GB" if fr and fr < 2048 else "")}
    av, src = mem_available_mb()
    b = budget_mb(av)
    rows["MEMORY"] = {"lamp": "GREEN" if av and av >= 2048 else ("YELLOW" if av else "GRAY"),
                      "line": f"可用 {av} MB(來源 {src})→ 每道 DuckDB 上限 {b} MB × {LANES} 道;超過就溢寫到 TEMP"}
    lb = latest_backup(backup_base())
    rows["BACKUP"] = lb
    rp = root / "VIA_Reports" / "vrn" / "launch" / "VRN_LAUNCH_RES_latest.json"
    try:
        lr = json.loads(rp.read_text(encoding="utf-8")) if rp.is_file() else None
    except (OSError, ValueError):
        lr = None
    if lr:
        age = (time.time() - rp.stat().st_mtime) / 3600
        pl = (lr.get("probe") or {}).get("lamp", "GRAY")
        rows["LAUNCH_HOOK"] = {"lamp": "YELLOW" if pl == "GREEN" and age > STALE_H else pl,
                               "line": f"上次 launch rc {lr.get('rc')} · 鉤 {pl} · 溢寫 {(lr.get('probe') or {}).get('temp_directory')} · 上限 {(lr.get('probe') or {}).get('memory_limit')} · {age:.0f}h 前"}
    else:
        rows["LAUNCH_HOOK"] = {"lamp": "GRAY", "line": "還沒有 v0283 的 launch 收據(跑一次 launch --run)"}
    gp = root / "VIA_Reports" / "graphify" / "VIA_Graphify_latest.json"
    try:
        g = json.loads(gp.read_text(encoding="utf-8")) if gp.is_file() else None
    except (OSError, ValueError):
        g = None
    if g is None:
        rows["GRAPHIFY"] = {"lamp": "GRAY", "line": "沒有 Graphify 收據(桌機跑 VIA_Graphify v0101;只解析程式碼 · 不出網 · 一系統一張圖;記憶體不夠它自己跳過)"}
    else:
        txt = json.dumps(g, ensure_ascii=False)
        age = (time.time() - gp.stat().st_mtime) / 3600
        has = '"VRN' in txt
        rows["GRAPHIFY"] = {"lamp": ("GREEN" if age <= 7 * 24 else "YELLOW") if has else "YELLOW",
                            "line": f"收據 {age:.0f}h 前 · " + ("有 VRN 的圖" if has else "收據裡沒有 VRN 的圖") + " · 圖只做導航,證據仍用骨架卡"}
    om = omniroute_scan()
    rows["OMNIROUTE"] = {"lamp": "RED" if om["hits"] else "GREEN",
                         "line": (f"VRN 尾版有 OmniRoute 參照:{om['hits'][:3]}(不得進執行路徑)" if om["hits"] else
                                  f"不在 VRN 執行路徑(語法樹掃現役尾版 {om['scanned']} 支 · 0 支參照);它是桌機 AI 閘道,只給 AI 工具用")}
    rows["AGENT_MEMORY"] = {"lamp": "GRAY", "line": "未導入:VCGC-REQ185 評估後決定不引入(成熟度低 · 無鎖版 · 要 pip);"
                                                    "AI 記憶用交接冊 + 每日教訓帳;要改需操作員裁定"}
    lamps = [r["lamp"] for r in rows.values()]
    unproven = [k for k, r in rows.items() if r["lamp"] == "GRAY" and k != "AGENT_MEMORY"]     # 沒證據 ≠ 綠(設計上不導入的 agentmemory 除外)
    worst = "RED" if "RED" in lamps else "YELLOW" if "YELLOW" in lamps or unproven else "GREEN"
    return {"lamp": worst, "rows": rows, "unproven": unproven, "counts": {k: lamps.count(k) for k in ("GREEN", "YELLOW", "RED", "GRAY")}}


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    PRIOR.TAG = TAG
    if a[:1] == ["resources"]:
        r = resources()
        if "--json" in a:
            print(json.dumps(r, ensure_ascii=False, indent=1))
        else:
            c = r["counts"]
            print(f"[{TAG}] resources {r['lamp']} · 綠 {c['GREEN']} 黃 {c['YELLOW']} 紅 {c['RED']} 灰 {c['GRAY']}"
                  + (f" · 還沒證據:{' · '.join(r['unproven'])}" if r["unproven"] else ""))
            for k, v in r["rows"].items():
                print(f"  [{v['lamp']:<6}] {k:<12} {v['line']}")
        return {"GREEN": 0, "YELLOW": 2, "GRAY": 2}.get(r["lamp"], 1)
    if a[:1] == ["launch"] and "--run" in a:
        return launch_run(a[1:])
    return PRIOR.main(a)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    rc0 = PRIOR.selftest()
    print(f"=== {TAG} · 薄尾自測(TEMP 鉤生效 · 備份 · resources;暫存夾 · 零網路)===")
    chk("⓪ 直接前版 %s 自測過" % PRIOR_PATH.name, rc0 == 0, f"rc {rc0}")
    keep_env = dict(os.environ)
    try:
        with tempfile.TemporaryDirectory() as td:
            t = Path(td)
            env0 = dict(os.environ, VIA_TEMP_ROOT=str(t / "tmproot"))
            tp = prepare_temp(env0, avail=6000)
            chk("① 本輪夾在 VIA_TEMP_ROOT\\VRN 底下 · 預算 = 6000 × 0.5 ÷ 3 = 1000 MB · 鉤檔寫在本輪夾",
                Path(tp["run"]).parent == t / "tmproot" / "VRN" and tp["budget_mb"] == 1000 and (Path(tp["hook_dir"]) / "sitecustomize.py").is_file(), tp)
            od = dict(os.environ, VIA_TEMP_ROOT=str(t / "OneDrive" / "x"), LOCALAPPDATA=str(t / "lad"))
            chk("② VIA_TEMP_ROOT 在 OneDrive → 不用,退到 LOCALAPPDATA\\VIA_TEMP\\VRN", temp_base(od)[0] == t / "lad" / "VIA_TEMP" / "VRN")
            try:
                import duckdb  # noqa: F401
                has_duck = True
            except ImportError:
                has_duck = False
            pr = probe(dict(env0, **tp["env_add"]))
            if has_duck:
                chk("③ 探針子行程:鉤生效(hook 標記 · temp_directory 在本輪夾 · memory_limit 有值)= 綠", pr["lamp"] == "GREEN", pr)
                pr2 = probe(dict(env0, **{k: v for k, v in tp["env_add"].items() if k != "PYTHONPATH"}))
                chk("④ 拿掉 PYTHONPATH(只有標記沒有鉤)→ 不算生效 = 黃", pr2["lamp"] == "YELLOW", pr2)
                (t / "existing").mkdir()
                (t / "existing" / "sitecustomize.py").write_text("import os\nos.environ['VRN_ST_CHAIN']='1'\n", encoding="utf-8")
                e3 = dict(env0, **tp["env_add"])
                e3["PYTHONPATH"] = e3["PYTHONPATH"] + os.pathsep + str(t / "existing")
                r3 = subprocess.run([sys.executable, "-c", "import os;print(os.environ.get('VRN_ST_CHAIN'))"], env=e3, capture_output=True, text=True, timeout=60)
                chk("⑤ 原有的 sitecustomize 照樣接力執行(不吃掉別人的)", (r3.stdout or "").strip() == "1", r3.stderr[-200:])
                e4 = dict(e3, VIA_DUCK_TEMP="0")
                r4 = probe(e4)
                chk("⑥ VIA_DUCK_TEMP=0 → 不掛(操作員可關)", r4.get("hook") is None, r4)
            else:
                chk("③ 本環境沒有 duckdb → 探針照實灰(不裝作綠)", pr["lamp"] == "GRAY", pr)
            out = t / "vrn_database"
            (out / "sub").mkdir(parents=True)
            (out / "vrn.duckdb").write_bytes(b"DUCK" * 1000)
            (out / "sub" / "x.duckdb.wal").write_bytes(b"W" * 10)
            (out / "p.parquet").write_bytes(b"P")
            (out / "backup").mkdir()
            (out / "backup" / "old.duckdb").write_bytes(b"O")
            bb = t / "bk"
            r1 = backup_db(out, bb, now=datetime(2026, 11, 22, 1, 0, 0))
            chk("⑦ 備份:兩支庫檔(含 .wal)複製且 sha256 對上 · 略過 backup 夾 · parquet 只記清單", r1["lamp"] == "GREEN" and r1["files"] == 2
                and (bb / "20261122_010000" / "vrn.duckdb").read_bytes() == b"DUCK" * 1000 and r1["parquet_n"] == 1, r1)
            for i in range(2, 6):
                backup_db(out, bb, now=datetime(2026, 11, 22, i, 0, 0))
            chk("⑧ 只留最近 3 輪", sorted(d.name for d in bb.iterdir()) == ["20261122_030000", "20261122_040000", "20261122_050000"], sorted(d.name for d in bb.iterdir()))
            chk("⑨ latest_backup 綠 · 檔被刪 → 紅並點名", latest_backup(bb)["lamp"] == "GREEN"
                and ((bb / "20261122_050000" / "vrn.duckdb").unlink() or latest_backup(bb)["lamp"] == "RED"))
            chk("⑩ 沒有輸出夾 → 灰(照實,不假裝備過)", backup_db(None, bb)["lamp"] == "GRAY" and backup_db(t / "nope", bb)["lamp"] == "GRAY")
            rb = t / "runs"
            for i, pid in enumerate((999999, 999998, 999997, 999996, 999995, 999994, 999993)):
                d = rb / f"run_2026112{i}"
                d.mkdir(parents=True)
                (d / ".vrn_run").write_text(json.dumps({"pid": pid}), encoding="utf-8")
                old = time.time() - (100 + i) * 3600
                os.utime(d, (old, old))
            (rb / "run_other").mkdir()
            gone = sweep_runs(rb)
            chk("⑪ 舊輪只清 VRN 自己標記過的、留最新 5 輪 · 沒標記的夾不碰", len(gone) == 2 and (rb / "run_other").is_dir()
                and len([d for d in rb.glob("run_2*")]) == 5, gone)
            bad = t / "bad.py"
            bad.write_text("import omniroute\nURL='http://127.0.0.1:20128/v1'\n", encoding="utf-8")
            good = t / "good.py"
            good.write_text("import duckdb\n", encoding="utf-8")
            chk("⑫ OmniRoute 掃描:匯入或打 20128 埠 → 抓到;乾淨的不抓", omniroute_scan([bad, good])["hits"] == ["bad.py"])
            chk("⑬ VRN 現役尾版目前 0 支參照 OmniRoute", omniroute_scan()["hits"] == [], omniroute_scan()["hits"])
            root = t / "via"
            (root / "VIA_Reports" / "vrn" / "launch").mkdir(parents=True)
            os.environ["VIA_TEMP_ROOT"] = str(t / "tmproot")
            os.environ["VIA_BACKUP_ROOT"] = str(bb)
            r = resources(root)
            chk("⑭ resources 七列都在 · agentmemory 灰(照 REQ185)· Graphify 沒收據 = 灰", set(r["rows"]) == {"TEMP", "MEMORY", "BACKUP", "LAUNCH_HOOK", "GRAPHIFY", "OMNIROUTE", "AGENT_MEMORY"}
                and r["rows"]["AGENT_MEMORY"]["lamp"] == "GRAY" and r["rows"]["GRAPHIFY"]["lamp"] == "GRAY", r)
            chk("⑭b 有格還沒證據(灰)→ 總燈不得綠(SKIP 不是綠)", r["lamp"] != "GREEN" and "GRAPHIFY" in r["unproven"] and "AGENT_MEMORY" not in r["unproven"], r["lamp"])
            fake = launch_modules()
            chk("⑮ 前版鏈裡跑 launch 的模組找得到(sm_child_env 換得到)", len(fake) >= 1, len(fake))
            if fake:
                m = fake[0]
                orig = m.sm_child_env
                pt = _patch_env({"VIA_DUCKDB_TEMP_DIR": "X"})
                got = m.sm_child_env().get("VIA_DUCKDB_TEMP_DIR")
                for mm, o in pt:
                    mm.sm_child_env = o
                chk("⑯ 換裝:前版 launch 的子行程環境帶本輪變數 · 跑完還原", got == "X" and m.sm_child_env is orig)
    finally:
        os.environ.clear()
        os.environ.update(keep_env)
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    peer = [k for k in ("VIA_FROM_VCGC", "VIA_FROM_VDFSM") if re.search(r"environ(?:\[[\"']%s[\"']\]\s*=|\.setdefault\([\"']%s)" % (k, k), body)]
    chk("⑰ 系統獨立:不設他系統的入口旗標(本檔是 VRN 自己的入口;VCGC 只支援不干涉)", not peer, peer)
    chk("⑱ 加速器橋在;不出網 · 不碰 TA-Lib · 不寫契約檔 / 資產冊", "[VIA:ACCEL-BRIDGE:v0100]" in src and "_via_net()." not in body
        and "talib" not in body.lower() and "VRN_NUMBER_REQUEST" not in body and "Asset_Register" not in body)
    pub = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    chk("⑲ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in pub), f"{len(pub)} 支")
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
