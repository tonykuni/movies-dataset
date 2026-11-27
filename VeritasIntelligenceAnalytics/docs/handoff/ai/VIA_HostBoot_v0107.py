#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VIA_HostBoot v0107 — 薄尾(v0100–v0106 一字不動):up 的三步同時跑(VCGC 啟動 · 備份 + Graphify · VDF 啟動)

操作員 2026-11-27:「one py with 加速器去啟動全部三步驟同行 · 一個 ps 啟動她」。
v0106 的 up 依序跑:① VCGC enter(約 11 分)→ ② 備份 + Graphify → ③ VDF start,前一步跑完才起下一步。
本版把 up 換成**三道同時起**(PS 照舊是那一支 Start-VIA-v0100.ps1,它找的是本家族尾版):
  ① 三支各自的入口子行程同時起(各寫自己的 log;三系統獨立,誰紅都不擋別人)。
     ② 備份的前置閘(Fail-Closed)照舊只管備份本身:閘紅 = 不備份、零寫入,VDF 照跑。
  ② 每 ≤30 秒一行心跳:每道 跑著 / 完成 · 已幾秒 · 最後一行輸出。
  ③ 開跑前量一次可用記憶體:低於 VIA_UP_MIN_GB(預設 4)→ 照實印黃、自動改逐步跑(Graphify 建圖吃記憶體;
     主機 11-25 實錄建 VDF 圖時可用記憶體掉到 0.8 GB)。--force-parallel 照樣同時跑;--serial 一律逐步(= v0106)。
  ④ Ctrl+C → 三道的子行程樹整棵收掉,rc 130;總燈 = 三道裡最差的(紅 1 · 黃 / 略過 2 · 全綠 0)。
  ⑤ 前版 v0106 自測 ⑤ 吃本機狀態(父行程帶 VIA_FROM_VCGC 就判錯);本版跑前版自測時先拿掉、跑完放回(前版一字不動)。
不 import 他系統(三支都用子行程叫各自的入口);零 TA-Lib;同意閘不在本檔設(VDF 開跑前自己檢查)。
用法:pwsh -NoProfile -File Start-VIA-v0100.ps1 [--serial] [--force-parallel] [--skip-backup] [VDF start 參數…] | --selftest
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

import importlib.util
import os
import re
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

FAMILY = "VIA_HostBoot"
VERSION = "v0107"
TAG = f"{FAMILY} {VERSION}"
HERE = Path(__file__).resolve()
MIN_GB_DEFAULT = 4.0


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
_PREV_RUN_UP = PRIOR.run_up


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def say(msg: str) -> None:
    print(msg, flush=True)


def heartbeat_sec() -> int:
    try:
        v = int(os.environ.get("VIA_HEARTBEAT_SEC", "30"))
    except ValueError:
        v = 30
    return max(1, min(v, 30))


def avail_gb():
    """可用記憶體(GB);量不到回 None(照實,不猜)。"""
    try:
        import psutil
        return psutil.virtual_memory().available / 1e9
    except Exception:  # noqa: BLE001
        pass
    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) * 1024 / 1e9
    except OSError:
        pass
    if os.name == "nt":
        try:
            import ctypes

            class MS(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong), ("ullTotalPhys", ctypes.c_ulonglong),
                            ("ullAvailPhys", ctypes.c_ulonglong), ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong), ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            st = MS()
            st.dwLength = ctypes.sizeof(MS)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st))
            return st.ullAvailPhys / 1e9
        except Exception:  # noqa: BLE001
            return None
    return None


def min_gb() -> float:
    try:
        return float(os.environ.get("VIA_UP_MIN_GB", str(MIN_GB_DEFAULT)))
    except ValueError:
        return MIN_GB_DEFAULT


def _last_line(p: Path) -> str:
    try:
        with open(p, "rb") as fh:
            fh.seek(0, 2)
            size = fh.tell()
            fh.seek(max(0, size - 4096))
            tail = fh.read().decode("utf-8", "replace")
    except OSError:
        return ""
    lines = [x.strip() for x in re.split(r"[\r\n]+", tail) if x.strip() and "SyntaxWarning" not in x]
    return lines[-1][:120] if lines else ""


def _kill_tree(proc) -> None:
    if proc.poll() is not None:
        return
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True, timeout=30)
        else:
            os.killpg(proc.pid, signal.SIGKILL)
    except (OSError, subprocess.SubprocessError):
        proc.kill()
    try:
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        pass


def _lamp(rc) -> str:
    return "GREEN" if rc == 0 else ("YELLOW" if rc == 2 else "RED")


def run_parallel(via: Path, extra: list, skip_backup: bool = False, popen=None, py: str = None, logdir: Path = None,
                 every: int = None, log=say) -> tuple:
    """三步同時起;回 (總 rc, 各步列)。popen 可換(自測用)。"""
    popen = popen or subprocess.Popen
    every = every or heartbeat_sec()
    logdir = Path(logdir or tempfile.mkdtemp(prefix="via_up_lanes_"))
    logdir.mkdir(parents=True, exist_ok=True)
    rows, lanes = [], []
    if skip_backup:
        rows.append({"step": "② 備份 + Graphify(VCGC · VDF)", "rc": None, "secs": 0.0, "lamp": "SKIP", "note": "--skip-backup:略過(不算綠)"})
    for i, (name, cmd, add, _stop) in enumerate(PRIOR.up_steps(via, extra, skip_backup, py), 1):
        if not cmd:
            rows.append({"step": name, "rc": None, "secs": 0.0, "lamp": "RED", "note": "找不到尾版(先 git pull)"})
            log(f"[RED] {name}:找不到尾版")
            continue
        lp = logdir / f"lane{i}.log"
        fh = open(lp, "wb")
        kw = {"stdout": fh, "stderr": subprocess.STDOUT, "cwd": str(via.parent), "env": dict(os.environ, **add)}
        if os.name == "nt":
            kw["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            kw["start_new_session"] = True
        lanes.append({"name": name, "proc": popen(cmd, **kw), "fh": fh, "log": lp, "t0": time.monotonic(), "done": None})
        log(f"[起] {name} · log {lp}")
    t0 = time.monotonic()
    interrupted = False
    try:
        while any(L["done"] is None for L in lanes):
            deadline = time.monotonic() + every
            while time.monotonic() < deadline and any(L["done"] is None for L in lanes):
                for L in lanes:
                    if L["done"] is None and L["proc"].poll() is not None:
                        L["done"] = time.monotonic()
                        log(f"[完] {L['name']} · rc {L['proc'].returncode} · {L['done'] - L['t0']:.0f} 秒")
                time.sleep(0.2)
            if any(L["done"] is None for L in lanes):
                parts = ["%s %s %ds%s" % (L["name"][:1], "跑著" if L["done"] is None else "完成", int((L["done"] or time.monotonic()) - L["t0"]),
                                          (" · " + _last_line(L["log"])) if L["done"] is None else "") for L in lanes]
                log(f"[心跳] 已 {int(time.monotonic() - t0)} 秒 · " + " | ".join(parts))
    except KeyboardInterrupt:
        interrupted = True
        for L in lanes:
            _kill_tree(L["proc"])
        log("[Ctrl+C] 三道子行程樹已整棵收掉")
    finally:
        for L in lanes:
            try:
                L["fh"].close()
            except OSError:
                pass
    for L in lanes:
        rc = L["proc"].returncode
        if interrupted and L["done"] is None:
            rows.append({"step": L["name"], "rc": None, "secs": round(time.monotonic() - L["t0"], 1), "lamp": "RED", "note": "Ctrl+C 中斷:沒完成"})
            continue
        note = ""
        if rc not in (0, 2) and L["name"].startswith("②"):
            note = "前置閘紅只擋備份本身(零寫入);VDF 同時照跑"
        elif rc not in (0, 2):
            note = "系統獨立:不擋其他兩道 · 看 log"
        rows.append({"step": L["name"], "rc": rc, "secs": round((L["done"] or time.monotonic()) - L["t0"], 1), "lamp": _lamp(rc), "note": note,
                     "log": str(L["log"])})
    rows.sort(key=lambda r: r["step"])
    if interrupted:
        return 130, rows
    lamps = [r["lamp"] for r in rows]
    final = 1 if "RED" in lamps else (2 if ("YELLOW" in lamps or "SKIP" in lamps) else 0)
    for r in rows:
        if r["lamp"] == "RED" and r.get("log"):
            log(f"\n-- {r['step']} log 最後幾行({r['log']})--")
            try:
                tail = Path(r["log"]).read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                tail = []
            for x in [y for y in tail if y.strip() and "SyntaxWarning" not in y][-12:]:
                log("   " + x[:200])
    return final, rows


def run_up(via: Path, extra: list, skip_backup: bool = False, runner=None, py: str = None) -> tuple:
    """v0106 main 叫的就是這個名字(模組全域已換)。預設三步同時;--serial 或記憶體不足 → 照 v0106 逐步。"""
    a = list(extra)
    serial, force = "--serial" in a, "--force-parallel" in a
    a = [x for x in a if x not in ("--serial", "--force-parallel")]
    if runner is not None or serial:
        say("[up] 逐步跑(--serial)· 照 v0106")
        return _PREV_RUN_UP(via, a, skip_backup, runner, py)
    gb, need = avail_gb(), min_gb()
    if gb is not None and gb < need and not force:
        say(f"[黃] 可用記憶體 {gb:.1f} GB < {need:.1f} GB(VIA_UP_MIN_GB)→ 改逐步跑,免得三道同時把記憶體吃光;要硬跑加 --force-parallel")
        return _PREV_RUN_UP(via, a, skip_backup, runner, py)
    say(f"[up] 三步同時跑 · 可用記憶體 {'量不到' if gb is None else '%.1f GB' % gb} · 心跳每 {heartbeat_sec()} 秒 · Ctrl+C 收三道")
    return run_parallel(via, a, skip_backup, py=py)


def install() -> None:
    PRIOR.run_up = run_up          # v0106 的 main 查它模組全域的 run_up → 本版
    PRIOR.TAG = TAG                # 開頭橫幅寫實際跑的尾版


def _restore() -> None:
    PRIOR.run_up = _PREV_RUN_UP
    PRIOR.TAG = _PREV_TAG


_PREV_TAG = PRIOR.TAG
install()


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(a)


def selftest() -> int:
    import contextlib
    import io
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print(f"[計] {TAG} 自測開始(本版 7 項 · 前版 {PRIOR_PATH.name})", flush=True)
    with tempfile.TemporaryDirectory(prefix="hb107_") as d:
        d = Path(d)
        via = d / "repo" / "VeritasIntelligenceAnalytics"
        via.mkdir(parents=True)
        sleeps = {"①": 1.6, "②": 1.6, "③": 1.6}
        rcs = {"①": 2, "②": 1, "③": 0}
        fake_steps = [(n, [sys.executable, "-c", f"import time,sys; print('{n} 起'); time.sleep({sleeps[n[:1]]}); print('{n} 完'); sys.exit({rcs[n[:1]]})"], {}, n.startswith("②"))
                      for n in ("① VCGC 啟動", "② 備份 + Graphify(VCGC · VDF)", "③ VDF 啟動")]
        keep = PRIOR.up_steps
        lines = []
        try:
            PRIOR.up_steps = lambda via, extra, skip_backup=False, py=None: [s for s in fake_steps if not (skip_backup and s[0].startswith("②"))]
            t = time.monotonic()
            rc, rows = run_parallel(via, [], logdir=d / "logs", every=1, log=lambda *x: lines.append(" ".join(map(str, x))))
            wall = time.monotonic() - t
            rc2, rows2 = run_parallel(via, [], skip_backup=True, logdir=d / "logs2", every=1, log=lambda *x: None)
        finally:
            PRIOR.up_steps = keep
        st = {r["step"][:1]: r for r in rows}
        chk("① 三道同時跑:牆鐘 < 三道相加(1.6 秒 ×3 序跑要 4.8 秒)", wall < 4.0 and len(rows) == 3, round(wall, 2))
        chk("② 各道照自己的 rc 給燈:① 黃 · ② 紅 · ③ 綠;② 紅不擋 ③(VDF 照跑)",
            st["①"]["lamp"] == "YELLOW" and st["②"]["lamp"] == "RED" and st["③"]["lamp"] == "GREEN" and st["③"]["rc"] == 0
            and "VDF 同時照跑" in st["②"]["note"], rows)
        chk("③ 總燈 = 最差的一道(有紅 → rc 1);--skip-backup 那道記 SKIP(不算綠)→ rc 2",
            rc == 1 and rc2 == 2 and any(r["lamp"] == "SKIP" for r in rows2), (rc, rc2))
        chk("④ 每 ≤1 秒(測試間隔)一行心跳,寫每道跑著 / 完成與最後一行輸出", sum("[心跳]" in x for x in lines) >= 1
            and any("跑著" in x for x in lines if "[心跳]" in x), [x for x in lines if "[心跳]" in x][:2])
        called = []
        keep_prev = _PREV_RUN_UP
        try:
            globals()["_PREV_RUN_UP"] = lambda via, a, s, r, p: called.append(list(a)) or (0, [])
            keep_min = os.environ.get("VIA_UP_MIN_GB")
            os.environ["VIA_UP_MIN_GB"] = "100000"
            with contextlib.redirect_stdout(io.StringIO()):
                run_up(via, ["--start", "2026-11-01"])
                run_up(via, ["--serial"])
            os.environ.pop("VIA_UP_MIN_GB", None) if keep_min is None else os.environ.__setitem__("VIA_UP_MIN_GB", keep_min)
        finally:
            globals()["_PREV_RUN_UP"] = keep_prev
        chk("⑤ 可用記憶體不足 → 自動改逐步(照 v0106);--serial 一律逐步;旗標不傳給 VDF",
            avail_gb() is None or called == [["--start", "2026-11-01"], []], called)
        chk("⑥ v0106 的 main 叫到的是本版 run_up(模組全域已換)· 橫幅寫 v0107", PRIOR.run_up is run_up and PRIOR.TAG == TAG)
    src = HERE.read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("⑦ 檔面:第 3 行加速器標記 · 執行時真的載到 · 零 TA-Lib · 不設同意閘 · 不 import 他系統",
        src.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]" and VIA_ACCEL is not None
        and not re.search(r"^\s*(import|from)\s+talib", body, re.M)
        and not re.search(r"os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", body)
        and not re.search(r"^\s*(import|from)\s+(VDF_|VRN_|VQG_|VAP_|CGC_)", body, re.M), "VIA_ACCEL %s" % (VIA_ACCEL is not None))
    n = sum(ok)
    print(f"[計] {TAG} 本版 {n}/{len(ok)}", flush=True)
    _restore()
    parent_mark = os.environ.pop("VIA_FROM_VCGC", None)   # v0106 自測 ⑤ 吃本機狀態:父行程帶 VCGC 入口標記就判錯 → 先拿掉再跑
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            rc_prior = PRIOR.selftest()
    finally:
        if parent_mark is not None:
            os.environ["VIA_FROM_VCGC"] = parent_mark
        install()
    print(f"[前版] {PRIOR_PATH.name} 自測 rc={rc_prior}", flush=True)
    print(f"[計] {TAG} 自測 OK {n} · FAIL {len(ok) - n} · 前版 rc={rc_prior}", flush=True)
    return 0 if n == len(ok) and rc_prior == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
