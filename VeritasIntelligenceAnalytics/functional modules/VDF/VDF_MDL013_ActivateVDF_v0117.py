#!/usr/bin/env python3
r"""VDF_MDL013_ActivateVDF v0117 — 薄尾:記憶體准入閘(引擎子行程起跑前看可用記憶體)· 工作數扣保底 · 每支子行程峰值記憶體收據

操作員回報(2026-11-15 工作站實跑 v0115/v0116 · 16 GB · 起跑可用 5,529 MB):總覽「記憶體閘:最低可用 69 MB · 等待 0 次」;
engine_launch 102 支跑了 1,610 秒;操作員令:「先優化記憶體及 CPU 再執行以上動作」。
查到(容器實測 + 程式碼):
  · 前版記憶體閘只在「每一步起跑前」看一次;engine_launch 是一步(27 分鐘),步裡 VDF_SystemManager 並行 6 支引擎子行程
    (v0164 run_items 執行緒池)一路補新的,完全不看可用記憶體 → 可用掉到 69 MB(Windows 開始換頁,牆鐘被拖長、易逾時)。
  · 工作數與每支 DuckDB 預算只算 DuckDB 上限,沒算每支 Python 本身(容器實測 pandas + numpy + duckdb 109 MB · 加速器再 +36 MB);
    也沒有留保底:6 支 × 506 MB + 資料庫流程 1,351 MB 已超過起跑可用。
本版(v0100 … v0116 一字不動;只在本版的一輪裡生效,前版自測照舊):
  ① 記憶體准入閘:本輪鉤(sitecustomize)多一段,只在引擎流程的子行程(引擎載入探針 / --selftest / 它們的子行程)起跑「最前面」
     (載入加速器、numpy 之前,這時行程約 12 MB)看可用記憶體;低於保底就每 0.5 秒再看一次,最多等 VIA_VDF_MEM_ADMIT_MAX_S 秒
     (預設 45;等滿照樣起跑,不擋、不算失敗)。指揮行程(VDF_SystemManager_* · ActivateVDF)一律不等。執行緒池的格子被等待中的
     子行程佔著 → 記憶體緊時實際並行數自動變少,鬆了自動回滿。保底 = max(保留 1,024 MB, 總量 × 10%)(= 前版記憶體閘的「壓力」線;
     16 GB → 1,608 MB);VIA_VDF_MEM_FLOOR_MB 可改 · VIA_VDF_MEM_ADMIT=0 可關。
  ② 工作數扣保底 + 算進每支 Python 本身:可用 −max(保留, 保底)後 ÷ 700 MB 定工作數;每支 DuckDB 上限 = 該額度 × 0.9 ÷(工作數 + 其他流程)
     − 250 MB(Python 本身),最少 256 MB(DuckDB 照舊溢寫到本機 TEMP)。流程 DuckDB 預算同樣先扣保底。操作員自己設的值照用。
     工作站實例:可用 5,529 → 引擎 5 支(前版 6)· 每支 DuckDB 256 MB(前版 506)· 每條流程 DuckDB 1,176 MB(前版 1,351)。
  ③ 每支子行程一行記憶體收據(本輪 temp/mem_receipts.jsonl):起跑可用 · 准入等了幾秒 · 結束時峰值(Windows peak_wset · 其他 ru_maxrss)。
     收尾印「[記憶體] 子行程 N · 准入等過 k 支(共 s 秒)· 峰值 中位 / 九成 / 最大(哪一支)」並寫進總覽 JSON(mem_admit)與總覽頁一段。
     下一輪可照實測峰值再調 700 / 250 這兩個數。
VDF 自己的模組:不匯入他系統程式;同意閘不讀不寫;不碰 TA-Lib;不裝套件;不寫環境(只寫子行程 env)。
用法同前(ActivateVDF.py run …;本檔是尾版就用本版)· 自測 python VDF_MDL013_ActivateVDF_v0117.py --selftest(本版 + 前版鏈)。
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
PER_JOB_MB_V0117 = 700          # 一支引擎工作佔的額度(定工作數用)
PY_BASE_MB_V0117 = 250          # 每支 Python 本身(pandas + numpy + duckdb + 加速器;容器實測 109 + 36 MB,Windows 留餘裕)
ADMIT_MAX_S_V0117 = 45.0        # 准入閘最多等幾秒(等滿照樣起跑)
MEM_LOG_NAME_V0117 = "mem_receipts.jsonl"
SECTION_ID_V0117 = "vdf-mem-admit-v0117"


def _vnum_v0117(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0117(p) < _vnum_v0117(__file__)), key=_vnum_v0117)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
with warnings.catch_warnings():
    warnings.simplefilter("ignore", SyntaxWarning)
    warnings.simplefilter("ignore", DeprecationWarning)
    _spec.loader.exec_module(PRIOR)
V0100 = PRIOR.V0100


def __getattr__(name):
    return getattr(PRIOR, name)


def _owner_v0117(name: str):
    m, seen = PRIOR, []
    while isinstance(m, types.ModuleType) and m not in seen:
        if name in vars(m):
            return m
        seen.append(m)
        m = vars(m).get("PRIOR")
    return None


V0115 = _owner_v0117("HOOK_SRC_V0115")              # 本輪鉤 · 引擎工作數 · 工具環境 · 寫總覽 的那一版(v0115 模組全域)
_ORIG = {k: getattr(V0115, k) for k in ("engine_jobs", "tools_env", "HOOK_SRC_V0115", "_WRITE_ORIG")}
_PLAN_SLOTS_V0115 = V0100.plan_slots               # = v0115 plan_slots(v0115 匯入時已換在 v0100 全域)
_RUN17 = {"on": False, "floor": None}


# ---------------------------------------------------------------- ② 保底 · 工作數 · 預算
def floor_mb(total_mb, env=None) -> int:
    """保底 = max(保留, 總量 × 壓力比)(= 前版記憶體閘的壓力線);VIA_VDF_MEM_FLOOR_MB 可改。"""
    env = os.environ if env is None else env
    try:
        v = int(env.get("VIA_VDF_MEM_FLOOR_MB") or 0)
    except ValueError:
        v = 0
    if v > 0:
        return v
    return max(V0100.RESERVE_MB, int((total_mb or 0) * V0100.PRESSURE_FRACTION))


def plan_slots(cpu: dict, mem: dict, want: int = 3, per_flow_mb: int = V0100.PER_FLOW_MB, reserve_mb: int = V0100.RESERVE_MB) -> dict:
    o = _PLAN_SLOTS_V0115(cpu, mem, want, per_flow_mb, reserve_mb)
    if not _RUN17["on"]:
        return o
    avail, total = mem.get("avail_mb"), mem.get("total_mb")
    fl = floor_mb(total)
    o["floor_mb"] = fl
    if avail is not None:
        o["duckdb_mem_mb"] = max(256, int((avail - max(reserve_mb, fl)) * V0115.mem_fraction()) // o["slots"])
        o["mem_note"] = "記憶體扣保底:(可用 %s − 保底 %s MB)× %s ÷ %s 條 = 每條 %s MB" % (
            avail, max(reserve_mb, fl), V0115.mem_fraction(), o["slots"], o["duckdb_mem_mb"])
    return o


def engine_jobs(res: dict, env: dict | None = None) -> dict:
    env = os.environ if env is None else env
    cpu, mem, plan = res.get("cpu") or {}, res.get("mem") or {}, res.get("plan") or {}
    usable_cpu = cpu.get("usable") or os.cpu_count() or 1
    avail, total = mem.get("avail_mb"), mem.get("total_mb")
    fl = floor_mb(total, env)
    room = (avail - max(V0100.RESERVE_MB, fl)) if avail is not None else None
    jobs = max(1, min(usable_cpu - 1, (room // PER_JOB_MB_V0117) if room is not None else usable_cpu - 1))
    others = max(0, int(plan.get("slots") or 1) - 1)
    per = max(256, int((room if room is not None else 4096) * V0115.mem_fraction()) // (jobs + others) - PY_BASE_MB_V0117)
    out = {"VIA_VDF_LAUNCH_JOBS": str(jobs), "VIA_VDF_LAUNCH_MEM_MB": str(per), "VIA_VDF_LAUNCH_THREADS": "1",
           "VIA_VDF_MEM_FLOOR_MB": str(fl), "VIA_VDF_MEM_ADMIT_MAX_S": str(int(ADMIT_MAX_S_V0117))}
    got = {k: env.get(k) or v for k, v in out.items()}       # 操作員自己設了就照用
    _RUN17["floor"] = int(got["VIA_VDF_MEM_FLOOR_MB"])
    return got


def tools_env(res: dict, t: dict | None = None) -> dict:
    env = _ORIG["tools_env"](res, t)
    if res.get("temp_run"):
        env["VIA_VDF_MEM_LOG"] = str(Path(res["temp_run"]) / MEM_LOG_NAME_V0117)
    return env


# ---------------------------------------------------------------- ① 准入閘 + ③ 收據(寫進本輪鉤)
MEM_SNIPPET_V0117 = r'''

def _vdf_avail_mb():
    try:
        import psutil
        return psutil.virtual_memory().available // 1048576
    except Exception:  # noqa: BLE001 — 沒有 psutil 換下一個量法
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
                return int(ms.ullAvailPhys // 1048576)
        except Exception:  # noqa: BLE001
            return None
        return None
    try:
        with open("/proc/meminfo", encoding="ascii") as fh:
            for ln in fh:
                if ln.startswith("MemAvailable:"):
                    return int(ln.split()[1]) // 1024
    except Exception:  # noqa: BLE001
        return None
    return None


def _vdf_peak_mb():
    try:
        import psutil
        mi = psutil.Process().memory_info()
        pk = getattr(mi, "peak_wset", None)
        if pk:
            return int(pk // 1048576)
    except Exception:  # noqa: BLE001
        pass
    try:
        import resource
        r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return int(r // 1048576) if sys.platform == "darwin" else int(r // 1024)
    except Exception:  # noqa: BLE001
        return None


def _vdf_mem_admit():
    # v0117:引擎流程子行程起跑最前面看可用記憶體;低於保底就等(最多 VIA_VDF_MEM_ADMIT_MAX_S 秒,等滿照樣起跑);結束時記峰值。
    if getattr(sys, "_vdf_mem_tag", None):
        return
    sys._vdf_mem_tag = _TAG
    import time
    argv = [str(a) for a in (getattr(sys, "argv", None) or [""])]
    head = os.path.basename(argv[0]) if argv else ""
    boss = head.startswith(("VDF_SystemManager", "VDF_MDL013_ActivateVDF", "ActivateVDF"))
    rec = {"pid": os.getpid(), "argv": (" ".join(os.path.basename(a) if i == 0 else a for i, a in enumerate(argv[:3])))[-160:],
           "tag": _TAG, "boss": boss}
    try:
        floor = int(os.environ.get("VIA_VDF_MEM_FLOOR_MB") or 0)
    except ValueError:
        floor = 0
    try:
        max_s = float(os.environ.get("VIA_VDF_MEM_ADMIT_MAX_S") or 45)
    except ValueError:
        max_s = 45.0
    t0 = time.time()
    a = _vdf_avail_mb()
    rec["avail0"], rec["floor"] = a, floor
    if floor > 0 and not boss and os.environ.get("VIA_VDF_MEM_ADMIT", "1") != "0":
        while a is not None and a < floor and time.time() - t0 < max_s:
            time.sleep(0.5)
            a = _vdf_avail_mb()
    rec["wait_s"] = round(time.time() - t0, 2)
    rec["avail_go"] = a
    log = os.environ.get("VIA_VDF_MEM_LOG")
    if not log:
        return

    def _bye():
        rec["peak_mb"] = _vdf_peak_mb()
        rec["secs"] = round(time.time() - t0, 1)
        try:
            import json
            with open(log, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except Exception:  # noqa: BLE001 — 收據寫不進不連累本行程
            pass
    import atexit
    atexit.register(_bye)


try:
    _vdf_mem_admit()
except Exception:  # noqa: BLE001
    pass
'''


def hook_src_v0117(base: str | None = None) -> str:
    src = _ORIG["HOOK_SRC_V0115"] if base is None else base
    anchor = "\n\ndef _vdf_tools():"                # 准入閘放在載工具(加速器 → numpy)之前:等的時候行程最小
    if anchor not in src:
        raise RuntimeError("v0115 鉤原文對不上接點(_vdf_tools)")
    return src.replace(anchor, MEM_SNIPPET_V0117.rstrip("\n") + anchor, 1)


HOOK_SRC_V0117 = hook_src_v0117()


def _pct(xs: list, q: float):
    if not xs:
        return None
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(q * (len(xs) - 1))))]


def mem_summary(temp_run) -> dict:
    out = {"n": 0, "workers": 0, "waited": 0, "wait_secs": 0.0, "max_wait": 0.0, "peak_median": None, "peak_p90": None,
           "peak_max": None, "peak_who": None, "floor": _RUN17.get("floor"), "bad_lines": 0}
    if not temp_run:
        return out
    f = Path(temp_run) / MEM_LOG_NAME_V0117
    try:
        lines = f.read_text(encoding="utf-8").splitlines()
    except OSError:
        return out
    peaks = []
    for ln in lines:
        try:
            r = json.loads(ln)
        except ValueError:
            out["bad_lines"] += 1
            continue
        out["n"] += 1
        if not r.get("boss"):
            out["workers"] += 1
        w = float(r.get("wait_s") or 0)
        if w >= 0.5:
            out["waited"] += 1
            out["wait_secs"] = round(out["wait_secs"] + w, 1)
            out["max_wait"] = max(out["max_wait"], w)
        if out["floor"] is None and r.get("floor"):
            out["floor"] = r.get("floor")
        pk = r.get("peak_mb")
        if isinstance(pk, int) and not r.get("boss"):
            peaks.append(pk)
            if out["peak_max"] is None or pk > out["peak_max"]:
                out["peak_max"], out["peak_who"] = pk, r.get("argv")
    out["peak_median"], out["peak_p90"] = _pct(peaks, 0.5), _pct(peaks, 0.9)
    return out


def mem_line(s: dict) -> str:
    if not s.get("n"):
        return "[記憶體] 本輪沒有子行程記憶體收據(VIA_VDF_TOOLS=0 或鉤沒掛上)"
    return ("[記憶體] 子行程 %d(引擎工作 %d)· 保底 %s MB · 准入等過 %d 支(共 %.1f 秒 · 最長 %.1f 秒)· 峰值 中位 %s / 九成 %s / 最大 %s MB(%s)"
            % (s["n"], s["workers"], s.get("floor"), s["waited"], s["wait_secs"], s["max_wait"], s["peak_median"], s["peak_p90"],
               s["peak_max"], s.get("peak_who") or "—"))


def mem_section(s: dict) -> str:
    import html as _h
    return ('<section id="%s"><h2>記憶體准入閘(v0117)</h2><p>%s</p><p class="mut">引擎子行程起跑前看可用記憶體,低於保底就等'
            '(最多 VIA_VDF_MEM_ADMIT_MAX_S 秒,等滿照樣起跑);指揮行程不等。VIA_VDF_MEM_ADMIT=0 可關 · VIA_VDF_MEM_FLOOR_MB 可改。</p></section>'
            % (SECTION_ID_V0117, _h.escape(mem_line(s))))


def _write(c, u=None):
    if _RUN17["on"]:
        c["mem_admit"] = mem_summary(V0115._RUN15.get("temp_run"))
    r = _ORIG["_WRITE_ORIG"](c, u) if u is not None else _ORIG["_WRITE_ORIG"](c)
    try:
        hp = Path(((c.get("report") or {}).get("html")) or (r or {}).get("html") or "")
    except AttributeError:
        hp = Path("")
    if _RUN17["on"] and hp.suffix == ".html" and hp.is_file():
        t = hp.read_text(encoding="utf-8")
        if SECTION_ID_V0117 not in t and "</body>" in t:
            hp.write_text(t.replace("</body>", mem_section(c["mem_admit"]) + "</body>", 1), encoding="utf-8")
    return r


# ---------------------------------------------------------------- 換裝 / 還原(前版自測看它自己的狀態)
_V0114_G = PRIOR.operate_links.__globals__
_ACTIVATE_V0116 = PRIOR.activate


def _patch_v0117() -> None:
    V0100.plan_slots = plan_slots
    V0115.engine_jobs, V0115.tools_env, V0115.HOOK_SRC_V0115, V0115._WRITE_ORIG = engine_jobs, tools_env, HOOK_SRC_V0117, _write
    _V0114_G["activate"] = activate


def _unpatch_v0117() -> None:
    V0100.plan_slots = _PLAN_SLOTS_V0115
    for k, v in _ORIG.items():
        setattr(V0115, k, v)
    _V0114_G["activate"] = _ACTIVATE_V0116


def activate(opt, manager: Path | None = None, py: str | None = None, temp: Path | None = None) -> dict:
    """同 v0116 activate;本輪:引擎子行程記憶體准入閘 · 工作數扣保底 · 子行程峰值收據;收尾印一行。"""
    _RUN17.update(on=True, floor=None)
    tag_keep = V0115.TAG
    V0115.TAG = TAG                               # 總覽 / 終端標實際跑的版(v0115 activate 把它的 TAG 蓋到前版;v0116 沿用顯示成 v0115)
    try:
        card = _ACTIVATE_V0116(opt, manager, py, temp)
    finally:
        _RUN17["on"] = False
        V0115.TAG = tag_keep
    s = card.get("mem_admit") or mem_summary(V0115._RUN15.get("temp_run"))
    print("  " + mem_line(s), flush=True)
    card["mem_admit"] = s
    return card


_patch_v0117()


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--selftest"]:
        return selftest()
    PRIOR._patch_v0116()                          # v0116 main 會先換上它自己的 activate → 不走它的 main;兩版依序換好
    _patch_v0117()
    return V0115.main(argv)                       # v0115 main 不再換裝,直接叫 v0114 main(它叫模組全域 activate = 本版)


# ---------------------------------------------------------------- 自測(沙盒 · 零網路)
def selftest() -> int:
    import shutil
    import subprocess
    import tempfile
    import time
    p = f = 0

    def chk(name, cond, note=""):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s%s" % (name, (" · " + str(note)[:300]) if note else ""))

    print("=== %s · 薄尾自測(記憶體准入閘 · 工作數扣保底 · 子行程峰值收據)===" % TAG)
    ws = {"cpu": {"usable": 8}, "mem": {"avail_mb": 5529, "total_mb": 16080}, "plan": {"slots": 3}}
    old = _ORIG["engine_jobs"](ws, {})
    new = engine_jobs(ws, {})
    chk("① 工作站實例(可用 5,529 / 16,080 MB · 8 核 · 3 條):保底 1,608 · 引擎 %s 支(前版 %s)· 每支 DuckDB %s MB(前版 %s)"
        % (new["VIA_VDF_LAUNCH_JOBS"], old["VIA_VDF_LAUNCH_JOBS"], new["VIA_VDF_LAUNCH_MEM_MB"], old["VIA_VDF_LAUNCH_MEM_MB"]),
        new["VIA_VDF_MEM_FLOOR_MB"] == "1608" and new["VIA_VDF_LAUNCH_JOBS"] == "5" and new["VIA_VDF_LAUNCH_MEM_MB"] == "256"
        and int(new["VIA_VDF_LAUNCH_JOBS"]) <= int(old["VIA_VDF_LAUNCH_JOBS"]) and int(new["VIA_VDF_LAUNCH_MEM_MB"]) <= int(old["VIA_VDF_LAUNCH_MEM_MB"]), (new, old))
    big = engine_jobs({"cpu": {"usable": 8}, "mem": {"avail_mb": 14000, "total_mb": 16080}, "plan": {"slots": 3}}, {})
    low = engine_jobs({"cpu": {"usable": 8}, "mem": {"avail_mb": 1500, "total_mb": 16080}, "plan": {"slots": 3}}, {})
    chk("② 記憶體多 → 7 支(核 − 1 封頂)· 記憶體比保底還少 → 1 支(不會 0 或負數)· DuckDB 最少 256 MB",
        big["VIA_VDF_LAUNCH_JOBS"] == "7" and low["VIA_VDF_LAUNCH_JOBS"] == "1" and low["VIA_VDF_LAUNCH_MEM_MB"] == "256", (big, low))
    own = engine_jobs(ws, {"VIA_VDF_LAUNCH_JOBS": "2", "VIA_VDF_MEM_FLOOR_MB": "3000", "VIA_VDF_MEM_ADMIT_MAX_S": "10"})
    chk("③ 操作員自己設的照用(工作數 2 · 保底 3,000 · 最多等 10 秒)", own["VIA_VDF_LAUNCH_JOBS"] == "2" and own["VIA_VDF_MEM_FLOOR_MB"] == "3000"
        and own["VIA_VDF_MEM_ADMIT_MAX_S"] == "10", own)
    _RUN17["floor"] = None                          # 上面三測只量算式;不留給後面的彙整
    _RUN17["on"] = True
    try:
        ps = plan_slots({"usable": 8, "cores": 8}, {"avail_mb": 5529, "total_mb": 16080, "how": "test"})
    finally:
        _RUN17["on"] = False
    chk("④ 流程 DuckDB 預算先扣保底:每條 %s MB(前版 1,351)· 說明寫明" % ps.get("duckdb_mem_mb"),
        ps.get("duckdb_mem_mb") == 1176 and ps.get("floor_mb") == 1608 and "保底" in ps.get("mem_note", ""), ps)
    src = HOOK_SRC_V0117
    try:
        compile(src, "sitecustomize.py", "exec")
        compiled = True
    except SyntaxError as exc:
        compiled = exc
    chk("⑤ 本輪鉤:准入閘在載工具之前 · 標籤照舊 · 可編譯 · 前版鉤原文一字不少",
        compiled is True and src.index("_vdf_mem_admit()") < src.index("def _vdf_tools():") and '_TAG = "vdf-activate-v0115"' in src
        and src.replace(MEM_SNIPPET_V0117.rstrip("\n"), "") == _ORIG["HOOK_SRC_V0115"], compiled)
    tmp = Path(tempfile.mkdtemp(prefix="vdf_act0117_"))
    try:
        hook = tmp / "hook"
        hook.mkdir()
        (hook / "sitecustomize.py").write_text(src, encoding="utf-8")
        log = tmp / MEM_LOG_NAME_V0117
        base = {k: v for k, v in os.environ.items() if not k.startswith(("VIA_VDF_", "VIA_DUCK"))}
        base.update(PYTHONPATH=str(hook), VIA_VDF_MEM_LOG=str(log), VIA_VDF_TOOLS="0", VIA_DUCK_TEMP="0", PYTHONIOENCODING="utf-8")
        boss = tmp / "VDF_SystemManager_v9999.py"
        boss.write_text("print('boss')\n", encoding="utf-8")
        eng = tmp / "VDF_ENG999_Probe_v0100.py"
        eng.write_text("x = [0] * 4_000_000\nprint('eng')\n", encoding="utf-8")

        def run(script, **kw):
            t0 = time.time()
            r = subprocess.run([sys.executable, str(script), "--selftest"], env=dict(base, **kw), capture_output=True, text=True, timeout=60)
            return r.returncode, round(time.time() - t0, 2), r.stdout.strip()
        r1 = run(eng, VIA_VDF_MEM_FLOOR_MB=str(10 ** 9), VIA_VDF_MEM_ADMIT_MAX_S="1.2")
        r2 = run(eng, VIA_VDF_MEM_FLOOR_MB="1")
        r3 = run(boss, VIA_VDF_MEM_FLOOR_MB=str(10 ** 9), VIA_VDF_MEM_ADMIT_MAX_S="5")
        r4 = run(eng, VIA_VDF_MEM_FLOOR_MB=str(10 ** 9), VIA_VDF_MEM_ADMIT_MAX_S="5", VIA_VDF_MEM_ADMIT="0")
        rows = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines()] if log.is_file() else []
        chk("⑥ 可用低於保底:引擎子行程等到上限(%.1f 秒)才起跑 · 照樣跑完 rc 0(不擋、不算失敗)" % r1[1],
            r1[0] == 0 and r1[2] == "eng" and 1.0 <= r1[1] < 10, r1)
        chk("⑦ 可用高於保底 → 不等(%.2f 秒)· 指揮行程(VDF_SystemManager_*)保底再高也不等(%.2f 秒)· VIA_VDF_MEM_ADMIT=0 → 不等(%.2f 秒)" % (r2[1], r3[1], r4[1]),
            r2[0] == r3[0] == r4[0] == 0 and r3[2] == "boss" and max(r2[1], r3[1], r4[1]) < 4.5
            and len(rows) == 4 and rows[2]["boss"] and rows[2]["wait_s"] < 0.5 and rows[3]["wait_s"] < 0.5 and rows[1]["wait_s"] < 0.5, (r2, r3, r4, rows))
        chk("⑧ 每支子行程一行收據:起跑可用 · 保底 · 等了幾秒 · 峰值(引擎那支配了 32 MB 串列 → 峰值 > 20 MB)",
            len(rows) == 4 and rows[0]["wait_s"] >= 1.0 and all(isinstance(r.get("peak_mb"), int) for r in rows) and rows[0]["peak_mb"] > 20
            and rows[0]["avail0"] is not None and rows[0]["floor"] == 10 ** 9, rows[:1])
        (tmp / "run").mkdir()
        mlog = tmp / "run" / MEM_LOG_NAME_V0117
        mlog.write_text("\n".join(json.dumps(r) for r in [
            {"boss": True, "wait_s": 0, "peak_mb": 900, "argv": "VDF_SystemManager_v0180.py engine"},
            {"boss": False, "wait_s": 3.2, "peak_mb": 120, "argv": "-c a", "floor": 1608},
            {"boss": False, "wait_s": 0.1, "peak_mb": 480, "argv": "VDF_ENG051.py --selftest"},
            {"boss": False, "wait_s": 0.6, "peak_mb": 200, "argv": "-c b"}]) + "\n{壞行\n", encoding="utf-8")
        s = mem_summary(tmp / "run")
        chk("⑨ 收尾彙整:子行程 4(工作 3)· 等過 2 支 3.8 秒 · 峰值中位 200 / 最大 480(哪一支)· 指揮行程不算峰值 · 壞行照數不崩 · %s" % mem_line(s),
            s["n"] == 4 and s["workers"] == 3 and s["waited"] == 2 and s["wait_secs"] == 3.8 and s["peak_median"] == 200 and s["peak_max"] == 480
            and "ENG051" in s["peak_who"] and s["bad_lines"] == 1 and s["floor"] == 1608 and mem_line(s).startswith("[記憶體] 子行程 4"), s)
        chk("⑩ 沒有收據 → 照實說沒有(不冒充)", mem_line(mem_summary(tmp / "none")).startswith("[記憶體] 本輪沒有子行程記憶體收據"))
        envt = tools_env({"temp_run": str(tmp / "run")}, {"sup": str(tmp), "accelerator": {"path": None}, "network": {"path": None}})
        chk("⑪ 每條流程的子行程都帶收據路徑(本輪 temp)", envt.get("VIA_VDF_MEM_LOG") == str(tmp / "run" / MEM_LOG_NAME_V0117), envt)
        page = tmp / "ACTIVATE_VDF_latest.html"
        page.write_text("<html><body><p>x</p></body></html>", encoding="utf-8")
        seen = {}
        _ORIG_W = _ORIG["_WRITE_ORIG"]
        _ORIG["_WRITE_ORIG"] = lambda c, u=None: seen.setdefault("card", dict(c)) and {"html": str(page)}
        keep_run = dict(V0115._RUN15)
        try:
            V0115._RUN15["temp_run"] = str(tmp / "run")
            _RUN17["on"] = True
            _write({"report": {"html": str(page)}})
            _write({"report": {"html": str(page)}})
        finally:
            _RUN17["on"] = False
            _ORIG["_WRITE_ORIG"] = _ORIG_W
            V0115._RUN15.clear()
            V0115._RUN15.update(keep_run)
        t = page.read_text(encoding="utf-8")
        chk("⑫ 寫總覽:JSON 多 mem_admit · 總覽頁多一段(寫兩次也只一段)", (seen.get("card") or {}).get("mem_admit", {}).get("n") == 4
            and t.count(SECTION_ID_V0117) == 1 and t.index(SECTION_ID_V0117) < t.index("</body>"), t[-300:])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    chk("⑬ 換裝在位:v0100 plan_slots · v0115 engine_jobs / tools_env / 鉤原文 / 寫總覽 · main 叫的 activate 全是本版",
        V0100.plan_slots is plan_slots and V0115.engine_jobs is engine_jobs and V0115.tools_env is tools_env
        and V0115.HOOK_SRC_V0115 is HOOK_SRC_V0117 and V0115._WRITE_ORIG is _write and _V0114_G["activate"] is activate)
    PRIOR._patch_v0116()                          # 模擬 v0116 main 先換裝(工作站實錄:本版被它蓋掉)
    _patch_v0117()
    srcm = Path(__file__).read_text(encoding="utf-8").split("def main", 1)[1].split("def selftest", 1)[0]
    chk("⑬b 入口順序:v0116 換完再換本版 → main 叫的 activate 仍是本版 · main 不走 v0116 main(它會換回自己的)",
        _V0114_G["activate"] is activate and "V0115.main(argv)" in srcm and "PRIOR.main(argv)" not in srcm)
    me = Path(__file__).read_text(encoding="utf-8")
    body = me.split("def selftest", 1)[0]
    chk("⑭ VDF 獨立:不匯入他系統程式 · 兩座橋在 · 同意閘不讀不寫 · 不碰 TA-Lib", not re.search(r"^\s*(import|from)\s+(CGC_|VRN_|VCGC|talib)", me, re.M)
        and "VIA:ACCEL-BRIDGE" in me and "VIA:NET-BRIDGE" in me and "_CONSENT" not in body)
    if f:
        print("[計] %s 自測 %d/%d · FAIL" % (TAG, p, p + f))
        return 1
    print("[計] %s 本版 %d/%d · PASS" % (TAG, p, p + f))
    if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1":
        return 0
    _unpatch_v0117()
    try:
        rc1 = PRIOR.selftest()
    finally:
        _patch_v0117()
    print("[計] %s 前版鏈 rc %s · %s" % (TAG, rc1, "PASS" if rc1 == 0 else "FAIL"))
    return rc1 if rc1 in (0, 1, 2, 3) else 1


if __name__ == "__main__":
    raise SystemExit(main())
