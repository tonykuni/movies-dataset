#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VIA_HostBoot v0108 — 薄尾(v0100–v0107 一字不動):up 三道同時跑照 CLAUDE.md 補齊(VCGC-REQ284)

操作員 2026-11-28:「generate a PY activating vcgc and vdf systems with 3 processes run simultaneously with high speed.
Complying with Claude.md … Should be employment accelerator module.」
v0107 的 up 已經是三道同時(VCGC · 備份 + Graphify · VDF);本版只補 CLAUDE.md 要的五件,不另做一支:
  ① VCGC 那一道改叫 VCGC 自己的一鍵啟用:CGC_SystemManager 尾版 launch --lanes 3(VCGC-REQ282;內部 3 道 · token 閘 · 收據)。
     管理器尾版不在 → 照 v0106 叫主控台 enter(照實印出用的是哪一支)。
  ② 開跑前先降壓:gc 一次、量可用記憶體(低於門檻照 v0107 改逐步跑)。
  ③ 監工:跑的途中每 2 秒量一次可用記憶體;低於 VIA_UP_PAUSE_GB(預設 1.0)→ 暫停最新起的那一道(整棵子行程樹),
     回到 VIA_UP_RESUME_GB(預設 2.0)以上 → 恢復;至少留一道在跑。用 psutil;沒有 psutil 的 POSIX 用 SIGSTOP / SIGCONT;都沒有 → 只量不停(照實印)。
  ④ 加速器真的載到才可能綠:VIA_ACCEL is None → 總燈最好只到黃(只有標記、載不到 = 假加速)。
  ⑤ 容器跑的結果最多黃(AGENTS.md);主機照舊可綠。另印 應 / 已 / 略過 三數。
三支照舊各用子行程叫自己的入口(不 import 他系統);同意閘不在本檔設;零 TA-Lib。
用法(PS 照舊那一支,找本家族尾版):pwsh -NoProfile -File Start-VIA-v0101.ps1 [--serial] [--force-parallel] [--skip-backup] [VDF start 參數…]
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0111] SuperAccel 加速器橋(graceful;執行時載得到才算) =====
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
    VIA_ACCEL = None  # graceful:載不到時總燈最好只到黃(④)
# ===== [VIA:ACCEL-BRIDGE:END] =====
import gc
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
VERSION = "v0108"
TAG = f"{FAMILY} {VERSION}"
HERE = Path(__file__).resolve()
MANAGER = ("supportive modules/registry", "CGC_SystemManager")


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


_BELOW = [p for p in HERE.parent.glob(FAMILY + "_v[0-9][0-9][0-9][0-9].py") if 0 <= _vnum(p) < _vnum(HERE)]
PRIOR_PATH = max(_BELOW, key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{FAMILY}_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE106 = PRIOR.PRIOR                       # v0106:main · up_steps · run_up 的全域都在這一層
_PREV_UP_STEPS = BASE106.up_steps
_PREV_RUN_UP = PRIOR.run_up                 # v0107 的 run_up(三道 / 逐步的分流)
say = PRIOR.say


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def is_container() -> bool:
    return os.name != "nt"


def up_steps(via: Path, extra: list, skip_backup: bool = False, py: str = None) -> list:
    """① VCGC 改叫自己的一鍵啟用(管理器尾版 launch --lanes 3);管理器不在 → 照 v0106(主控台 enter)。其餘兩道照舊。"""
    steps = list(_PREV_UP_STEPS(via, extra, skip_backup, py))
    mgr = BASE106.tail_of(via, MANAGER)
    if mgr and steps and steps[0][0].startswith("①"):
        py = py or sys.executable
        steps[0] = ("① VCGC 啟動(管理器 launch)", [py, "-X", "utf8", str(mgr), "launch", "--lanes", "3"], {"VIA_FROM_VCGC": "YES"}, False)
    return steps


def _procs(pid: int):
    import psutil
    p = psutil.Process(pid)
    return [p] + p.children(recursive=True)


def pause(proc) -> bool:
    """暫停一道的整棵子行程樹;回有沒有停成。"""
    try:
        for x in _procs(proc.pid):
            x.suspend()
        return True
    except ImportError:
        if os.name != "nt":
            try:
                os.killpg(proc.pid, signal.SIGSTOP)
                return True
            except OSError:
                return False
        return False
    except Exception:  # noqa: BLE001  (psutil.NoSuchProcess 等:那一道已經結束)
        return False


def resume(proc) -> bool:
    try:
        for x in _procs(proc.pid):
            x.resume()
        return True
    except ImportError:
        if os.name != "nt":
            try:
                os.killpg(proc.pid, signal.SIGCONT)
                return True
            except OSError:
                return False
        return False
    except Exception:  # noqa: BLE001
        return False


def _gb_env(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except ValueError:
        return default


def run_parallel(via: Path, extra: list, skip_backup: bool = False, popen=None, py: str = None, logdir: Path = None,
                 every: int = None, log=say, steps: list = None, mem=None, tick: float = 2.0) -> tuple:
    """三道同時起 + 監工(記憶體低 → 暫停最新一道,回升 → 恢復,至少留一道);回 (總 rc, 各步列)。"""
    popen = popen or subprocess.Popen
    every = every or PRIOR.heartbeat_sec()
    mem = mem or PRIOR.avail_gb
    low, high = _gb_env("VIA_UP_PAUSE_GB", 1.0), _gb_env("VIA_UP_RESUME_GB", 2.0)
    logdir = Path(logdir or tempfile.mkdtemp(prefix="via_up_lanes_"))
    logdir.mkdir(parents=True, exist_ok=True)
    rows, lanes = [], []
    if skip_backup:
        rows.append({"step": "② 備份 + Graphify(VCGC · VDF)", "rc": None, "secs": 0.0, "lamp": "SKIP", "note": "--skip-backup:略過(不算綠)"})
    for i, (name, cmd, add, _stop) in enumerate(steps if steps is not None else up_steps(via, extra, skip_backup, py), 1):
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
        lanes.append({"name": name, "proc": popen(cmd, **kw), "fh": fh, "log": lp, "t0": time.monotonic(), "done": None, "paused": False})
        log(f"[起] {name} · log {lp}")
    t0, last_hb, last_mem = time.monotonic(), time.monotonic(), 0.0
    interrupted, paused_ever, no_pause_said = False, 0, False
    try:
        while any(L["done"] is None for L in lanes):
            for L in lanes:
                if L["done"] is None and L["proc"].poll() is not None:
                    L["done"] = time.monotonic()
                    log(f"[完] {L['name']} · rc {L['proc'].returncode} · {L['done'] - L['t0']:.0f} 秒")
            now = time.monotonic()
            if now - last_mem >= tick:
                last_mem = now
                gb = mem()
                live = [L for L in lanes if L["done"] is None]
                running = [L for L in live if not L["paused"]]
                if gb is not None and gb < low and len(running) > 1:
                    newest = max(running, key=lambda L: L["t0"])
                    if pause(newest["proc"]):
                        newest["paused"] = True
                        paused_ever += 1
                        log(f"[監工] 可用記憶體 {gb:.1f} GB < {low:g} GB → 暫停最新一道「{newest['name']}」(留 {len(running) - 1} 道在跑)")
                    elif not no_pause_said:
                        no_pause_said = True
                        log("[監工] 記憶體偏低但這台停不了子行程(沒有 psutil 也不是 POSIX)· 只量不停")
                elif gb is not None and gb >= high:
                    for L in sorted([L for L in live if L["paused"]], key=lambda L: L["t0"]):
                        if resume(L["proc"]):
                            L["paused"] = False
                            log(f"[監工] 可用記憶體 {gb:.1f} GB ≥ {high:g} GB → 恢復「{L['name']}」")
                            break
                elif gb is not None and not running and live:
                    first = min(live, key=lambda L: L["t0"])       # 保險:至少留一道在跑
                    if resume(first["proc"]):
                        first["paused"] = False
            if any(L["done"] is None for L in lanes) and now - last_hb >= every:
                last_hb = now
                gb = mem()
                parts = ["%s %s %ds%s" % (L["name"][:1], "暫停" if L["paused"] else ("跑著" if L["done"] is None else "完成"),
                                          int((L["done"] or now) - L["t0"]), (" · " + PRIOR._last_line(L["log"])) if L["done"] is None else "") for L in lanes]
                log(f"[心跳] 已 {int(now - t0)} 秒 · 記憶體 {'量不到' if gb is None else '%.1f GB' % gb} · " + " | ".join(parts))
            time.sleep(0.2)
    except KeyboardInterrupt:
        interrupted = True
        for L in lanes:
            if L["paused"]:
                resume(L["proc"])
            PRIOR._kill_tree(L["proc"])
        log("[Ctrl+C] 三道子行程樹已整棵收掉")
    finally:
        for L in lanes:
            if L["paused"] and L["proc"].poll() is None:
                resume(L["proc"])
            try:
                L["fh"].close()
            except OSError as e:
                log(f"[黃] 關不掉 log:{e}")
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
        rows.append({"step": L["name"], "rc": rc, "secs": round((L["done"] or time.monotonic()) - L["t0"], 1), "lamp": PRIOR._lamp(rc), "note": note,
                     "log": str(L["log"])})
    rows.sort(key=lambda r: r["step"])
    if interrupted:
        return 130, rows
    lamps = [r["lamp"] for r in rows]
    final = 1 if "RED" in lamps else (2 if ("YELLOW" in lamps or "SKIP" in lamps) else 0)
    if paused_ever:
        log(f"[監工] 途中暫停過 {paused_ever} 次(都已恢復)")
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


def cap(rc: int, rows: list, accel_ok: bool, container: bool) -> tuple:
    """④ 加速器載不到 · ⑤ 容器 → 總燈最好只到黃(紅照紅);各加一列寫原因。"""
    rows = list(rows)
    if not accel_ok:
        rows.append({"step": "⓪ 加速器", "rc": None, "secs": 0.0, "lamp": "YELLOW", "note": "VIA_ACCEL 沒載到:只有標記、載不到 = 假加速"})
    if container:
        rows.append({"step": "⓪ 執行地", "rc": None, "secs": 0.0, "lamp": "YELLOW", "note": "容器跑的結果最多黃;收尾要主機實跑"})
    if rc == 0 and (not accel_ok or container):
        rc = 2
    return rc, rows


def tally(rows: list) -> str:
    lanes = [r for r in rows if not r["step"].startswith("⓪")]
    ran = [r for r in lanes if r.get("rc") is not None]
    return f"應 {len(lanes)} · 已 {len(ran)} · 略過 {len(lanes) - len(ran)}"


def run_up(via: Path, extra: list, skip_backup: bool = False, runner=None, py: str = None) -> tuple:
    """v0106 main 查它模組全域的 run_up → 本版。先降壓,再照 v0107 分流(三道 / 逐步),最後套 ④ ⑤ 並印三數。"""
    gc.collect()
    rc, rows = _PREV_RUN_UP(via, extra, skip_backup, runner, py)
    rc, rows = cap(rc, rows, VIA_ACCEL is not None, is_container())
    say(f"[up] {tally(rows)} · 加速器 {'載到' if VIA_ACCEL is not None else '沒載到(黃)'} · {'容器(最多黃)' if is_container() else '主機'}")
    return rc, rows


def install() -> None:
    BASE106.up_steps = up_steps     # v0107 的 run_parallel / v0106 的逐步都查 v0106 模組全域的 up_steps
    PRIOR.run_parallel = run_parallel
    BASE106.run_up = run_up         # v0106 的 main 查它模組全域的 run_up
    BASE106.TAG = TAG


install()


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return BASE106.main(a)


def selftest() -> int:
    ok, bad = [], []

    def chk(name, cond, note=""):
        (ok if cond else bad).append(name)
        print(("  [OK] " if cond else "  [NG] ") + name + (f" · {note}" if note else ""), flush=True)

    src = HERE.read_text(encoding="utf-8")
    chk("① 加速器:第 3 行標記 · 執行時載得到(VIA_ACCEL is not None)", src.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]" and VIA_ACCEL is not None)
    chk("② 前版經 glob 載入(本檔之下最大的一版)", PRIOR_PATH == max(_BELOW, key=_vnum), PRIOR_PATH.name)
    chk("③ 掛鉤在定義那一層(v0106 的 up_steps · run_up · v0107 的 run_parallel)",
        vars(BASE106)["up_steps"] is up_steps and vars(BASE106)["run_up"] is run_up and vars(PRIOR)["run_parallel"] is run_parallel)
    body = "\n".join(src.splitlines()[40:])
    chk("④ 不 import 他系統 · 零 TA-Lib", not re.search(r"^\s*(import|from)\s+(VDF_|VRN_|VQG_|VAP_|CGC_|talib)", body, re.M))
    with tempfile.TemporaryDirectory() as td:
        via = Path(td) / "VeritasIntelligenceAnalytics"
        for rel in ("supportive modules/registry/CGC_MDL149_VeritasCentralGovernanceConsole_v0100.py", "docs/handoff/ai/VIA_DailyBackup_v0100.py",
                    "functional modules/VDF/VDF_MDL022_SafeParallelLaunch_v0100.py"):
            (via / rel).parent.mkdir(parents=True, exist_ok=True)
            (via / rel).write_text("x = 1\n", encoding="utf-8")
        s0 = up_steps(via, [], False, "py")
        chk("⑤ 管理器不在 → ① 照舊叫主控台 enter(照實)", s0[0][1][-1] == "enter" and "VeritasCentralGovernanceConsole" in s0[0][1][3])
        (via / "supportive modules/registry/CGC_SystemManager_v0100.py").write_text("x = 1\n", encoding="utf-8")
        s1 = up_steps(via, [], False, "py")
        chk("⑥ 管理器在 → ① 叫管理器 launch --lanes 3 · 帶 VIA_FROM_VCGC · 其餘兩道照舊",
            s1[0][1][-3:] == ["launch", "--lanes", "3"] and "CGC_SystemManager" in s1[0][1][3] and s1[0][2].get("VIA_FROM_VCGC") == "YES"
            and [x[0][:1] for x in s1] == ["①", "②", "③"], str(s1[0][1][-3:]))
        lane = [sys.executable, "-c", "import time,sys; time.sleep(float(sys.argv[1])); sys.exit(int(sys.argv[2]))"]
        steps = [("① A", lane + ["3.0", "0"], {}, False), ("② B", lane + ["3.0", "0"], {}, True), ("③ C", lane + ["3.0", "0"], {}, True)]
        lines = []
        seq = iter([0.5, 0.5, 0.5, 5.0, 5.0] + [5.0] * 200)
        t0 = time.monotonic()
        rc, rows = run_parallel(via, [], steps=steps, logdir=Path(td) / "logs", every=1, log=lines.append, mem=lambda: next(seq), tick=0.3)
        el = time.monotonic() - t0
        chk("⑦ 三道同時起(總時間 < 序跑的和 9 秒)· 全綠 rc 0", rc == 0 and el < 8.5 and [r["lamp"] for r in rows] == ["GREEN"] * 3, f"{el:.1f}s")
        paused = [x for x in lines if x.startswith("[監工]") and "暫停最新一道" in x]
        resumed = [x for x in lines if x.startswith("[監工]") and "恢復" in x]
        chk("⑧ 監工:記憶體低 → 暫停最新起的一道、至少留一道;回升 → 恢復",
            paused and resumed and all("「① A」" not in x for x in paused), f"暫停 {len(paused)} · 恢復 {len(resumed)}")
        steps_red = [("① A", lane + ["0.3", "1"], {}, False), ("② B", lane + ["0.3", "0"], {}, True), ("③ C", None, {}, True)]
        rc2, rows2 = run_parallel(via, [], steps=steps_red, logdir=Path(td) / "logs2", every=1, log=lines.append, mem=lambda: 9.0, tick=0.3)
        chk("⑨ 一道紅不擋別道 · 找不到尾版照實紅 · 總燈紅 rc 1", rc2 == 1 and len(rows2) == 3 and rows2[0]["lamp"] == "RED" and rows2[1]["lamp"] == "GREEN"
            and rows2[2]["note"].startswith("找不到"))
    g = [{"step": "① A", "rc": 0, "lamp": "GREEN"}, {"step": "② B", "rc": 0, "lamp": "GREEN"}]
    chk("⑩ 容器全綠 → 黃 rc 2(加一列寫原因);主機 + 加速器在 → 綠 rc 0;加速器沒載到 → 黃;紅照紅",
        cap(0, g, True, True)[0] == 2 and any(r["step"] == "⓪ 執行地" for r in cap(0, g, True, True)[1]) and cap(0, g, True, False)[0] == 0
        and cap(0, g, False, False)[0] == 2 and cap(1, g, True, True)[0] == 1)
    chk("⑪ 三數:應 = 已 + 略過(⓪ 列不算道)", tally(cap(2, g + [{"step": "③ C", "rc": None, "lamp": "RED"}], True, True)[1]) == "應 3 · 已 2 · 略過 1")
    env = dict(os.environ)
    env.pop("VIA_FROM_VCGC", None)
    pr = subprocess.run([sys.executable, str(PRIOR_PATH), "--selftest"], capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=900)
    chk("⑫ 直接前版自測(乾淨子行程)rc 0", pr.returncode == 0, (pr.stdout.strip().splitlines() or ["?"])[-1][:80])
    print(f"[計] {TAG} 自測 {len(ok)}/{len(ok) + len(bad)}" + (" · 不過:" + " · ".join(bad) if bad else " · PASS"), flush=True)
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
