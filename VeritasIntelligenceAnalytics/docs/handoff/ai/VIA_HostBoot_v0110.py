#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VIA_HostBoot v0110 — 薄尾(v0100–v0109 一字不動):監工暫停不卡死 · 三數照原定三道算(PR #773 Codex P1 · P2;VCGC-REQ284)

v0108 的兩個洞:
  P1 pause() 列舉子行程後,其中一支剛好退出 → suspend 它丟 NoSuchProcess → 整個 pause 回 False;
     但父行程已經被 suspend,呼叫端沒把這一道標成 paused,回升與收尾都不會 resume 它 → 整輪 up 永久等候。
     → 本版:逐支 suspend / resume,已退出的那支跳過;只要停成任一支就回 True(呼叫端會記住、之後恢復);一支都沒停成才回 False。
  P2 逐步跑(--serial / 記憶體不足)時備份紅 → v0106 的 runner 提前停,VDF 那一道連列都沒有;三數只照 rows 算 → 「應 2 · 已 2 · 略過 0」,VDF 被整道漏掉。
     → 本版:照原定計畫(up_steps 的三道)補齊沒跑到的道,記 SKIP「提前停止:前一步紅,這一道沒跑」;總燈若原本綠就降黃,紅照紅。
其餘照 v0109(網路橋 · 鎖冊網路工具實載)與 v0108(三道 · VCGC 叫管理器 launch · 降壓 · 監工 · 加速器 / 容器封頂)。
不 import 他系統;零 TA-Lib;同意閘不在本檔設。
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
    VIA_ACCEL = None  # graceful:載不到時總燈最好只到黃(v0108 ④)
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
except Exception:  # noqa: BLE001
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT 由擷取端自己檢查);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:NET-BRIDGE:END] =====
import importlib.util
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

FAMILY = "VIA_HostBoot"
VERSION = "v0110"
TAG = f"{FAMILY} {VERSION}"
HERE = Path(__file__).resolve()


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


_BELOW = [p for p in HERE.parent.glob(FAMILY + "_v[0-9][0-9][0-9][0-9].py") if 0 <= _vnum(p) < _vnum(HERE)]
PRIOR_PATH = max(_BELOW, key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{FAMILY}_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V108 = PRIOR.PRIOR                    # 定義 pause / resume / run_up(三數)的那一層
BASE106 = PRIOR.BASE106
_ORIG_SERIAL = vars(V108)["_PREV_RUN_UP"]     # v0108 的 run_up 先叫它(= v0107 的分流)
say = PRIOR.say


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def _apply(proc, verb: str) -> bool:
    """對一道的整棵子行程樹逐支 suspend / resume;已退出的那支跳過。停(或恢復)成任一支就回 True。"""
    try:
        import psutil
    except ImportError:
        if os.name != "nt":
            try:
                os.killpg(proc.pid, signal.SIGSTOP if verb == "suspend" else signal.SIGCONT)
                return True
            except OSError:
                return False
        return False
    try:
        root = psutil.Process(proc.pid)
        procs = [root] + root.children(recursive=True)
    except psutil.Error:
        return False                       # 父行程已經不在:這一道已結束,不必停
    done = 0
    for x in procs:
        try:
            getattr(x, verb)()
            done += 1
        except psutil.NoSuchProcess:
            continue                       # 列舉之後剛好退出:跳過,不影響其他支
        except psutil.Error:
            continue
    return done > 0


def pause(proc) -> bool:
    return _apply(proc, "suspend")


def resume(proc) -> bool:
    return _apply(proc, "resume")


SKIP_NOTE = "提前停止:前一步紅,這一道沒跑"


def fill_planned(rc: int, rows: list, planned: list) -> tuple:
    """照原定計畫補齊沒有列的道(以 ①②③ 為鍵);補了且原本綠 → 黃。"""
    have = {r["step"][:1] for r in rows}
    rows = list(rows)
    added = []
    for name in planned:
        if name[:1] not in have:
            rows.append({"step": name, "rc": None, "secs": 0.0, "lamp": "SKIP", "note": SKIP_NOTE})
            added.append(name)
    rows.sort(key=lambda r: r["step"])
    if added and rc == 0:
        rc = 2
    if added:
        say("[up] 沒跑到的道:" + " · ".join(added) + "(" + SKIP_NOTE + ")")
    return rc, rows


def serial_or_parallel(via: Path, extra: list, skip_backup: bool = False, runner=None, py: str = None) -> tuple:
    """包 v0107 的分流:跑完照原定三道補齊沒列到的道,v0108 的三數才算得對。"""
    rc, rows = _ORIG_SERIAL(via, extra, skip_backup, runner, py)
    a = [x for x in extra if x not in ("--serial", "--force-parallel")]
    planned = [s[0] for s in BASE106.up_steps(via, a, skip_backup, py)]
    return fill_planned(rc, rows, planned)


def install() -> None:
    V108.pause = pause                  # v0108 的 run_parallel 查它模組全域的 pause / resume
    V108.resume = resume
    V108._PREV_RUN_UP = serial_or_parallel
    BASE106.TAG = TAG


install()


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return BASE106.main(a)


def selftest() -> int:
    import ast
    import tempfile
    ok, bad = [], []

    def chk(name, cond, note=""):
        (ok if cond else bad).append(name)
        print(("  [OK] " if cond else "  [NG] ") + name + (f" · {note}" if note else ""), flush=True)

    src = HERE.read_text(encoding="utf-8")
    imports = {a.name for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Import) for a in n.names}
    chk("① 加速器:第 3 行標記 · 語法樹匯入 · 執行時載得到 · 網路橋在且載得起來",
        src.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]" and "VIA_SuperAccel_Module" in imports and VIA_ACCEL is not None
        and "[VIA:NET-BRIDGE:v0100]" in src and _via_net() is not None)
    chk("② 前版經 glob 載入 · 掛鉤在定義那一層(v0108 的 pause · resume · _PREV_RUN_UP)",
        PRIOR_PATH == max(_BELOW, key=_vnum) and vars(V108)["pause"] is pause and vars(V108)["resume"] is resume
        and vars(V108)["_PREV_RUN_UP"] is serial_or_parallel, PRIOR_PATH.name)
    import psutil

    def wait_status(pid, cond, limit=2.0):
        t0 = time.monotonic()
        st = psutil.Process(pid).status()
        while not cond(st) and time.monotonic() - t0 < limit:
            time.sleep(0.05)
            st = psutil.Process(pid).status()
        return st

    parent = subprocess.Popen([sys.executable, "-c",
                               "import subprocess,sys,time;c=subprocess.Popen([sys.executable,'-c','import time;time.sleep(0.3)']);time.sleep(30)"],
                              start_new_session=(os.name != "nt"))
    time.sleep(0.15)
    try:
        real_children = psutil.Process(parent.pid).children(recursive=True)

        class Gone:
            def suspend(self):
                raise psutil.NoSuchProcess(999999)

            def resume(self):
                raise psutil.NoSuchProcess(999999)

        orig_children = psutil.Process.children
        psutil.Process.children = lambda self, recursive=False: list(real_children) + [Gone()]
        try:
            time.sleep(0.4)                          # 讓真的子行程退出:列舉時在,suspend 時已不在
            p_ok = pause(parent)
            status = wait_status(parent.pid, lambda s: s == psutil.STATUS_STOPPED)      # 訊號是非同步的:等它真的停
            r_ok = resume(parent)
            status2 = wait_status(parent.pid, lambda s: s != psutil.STATUS_STOPPED)
        finally:
            psutil.Process.children = orig_children
        chk("③ P1 反控:列舉後子行程退出 → pause 照樣回 True(父行程已停)· resume 回 True 且父行程恢復",
            p_ok is True and status == psutil.STATUS_STOPPED and r_ok is True and status2 != psutil.STATUS_STOPPED, f"{status} → {status2}")
    finally:
        parent.kill()
        parent.wait()
    dead = subprocess.Popen([sys.executable, "-c", "pass"])
    dead.wait()
    chk("④ 反控:整道已結束 → pause 回 False(不假裝停成)", pause(dead) is False)
    planned = ["① VCGC 啟動(管理器 launch)", "② 備份 + Graphify(VCGC · VDF)", "③ VDF 啟動"]
    serial_red = [{"step": planned[0], "rc": 2, "lamp": "YELLOW"}, {"step": planned[1], "rc": 1, "lamp": "RED"}]
    rc, rows = fill_planned(1, serial_red, planned)
    chk("⑤ P2:逐步跑備份紅提前停 → 補 ③ VDF 一列 SKIP · 三數 應 3 · 已 2 · 略過 1 · 紅照紅",
        rc == 1 and rows[-1]["step"] == planned[2] and rows[-1]["note"] == SKIP_NOTE and PRIOR.tally(rows) == "應 3 · 已 2 · 略過 1", PRIOR.tally(rows))
    rc2, rows2 = fill_planned(0, [{"step": planned[0], "rc": 0, "lamp": "GREEN"}], planned)
    chk("⑥ 補了沒跑到的道且原本綠 → 黃 rc 2", rc2 == 2 and len(rows2) == 3)
    rc3, rows3 = fill_planned(0, [{"step": p, "rc": 0, "lamp": "GREEN"} for p in planned], planned)
    chk("⑦ 三道都有列 → 不補 · 燈不變", rc3 == 0 and len(rows3) == 3)
    with tempfile.TemporaryDirectory() as td:
        via = Path(td) / "VeritasIntelligenceAnalytics"
        for rel in ("supportive modules/registry/CGC_MDL149_VeritasCentralGovernanceConsole_v0100.py", "docs/handoff/ai/VIA_DailyBackup_v0100.py",
                    "functional modules/VDF/VDF_MDL022_SafeParallelLaunch_v0100.py"):
            (via / rel).parent.mkdir(parents=True, exist_ok=True)
            (via / rel).write_text("x = 1\n", encoding="utf-8")
        calls = []

        def runner(cmd, env):
            calls.append(cmd)
            return 1 if "VIA_DailyBackup" in cmd[3] else 0
        rc4, rows4 = BASE106.run_up(via, ["--serial"], False, runner, sys.executable)
        names = [r["step"][:1] for r in rows4 if not r["step"].startswith("⓪")]
        chk("⑧ 端到端(--serial · 備份紅):VDF 沒起 · 三道都有列 · ③ 記 SKIP · 總燈紅",
            len(calls) == 2 and names == ["①", "②", "③"] and rc4 == 1
            and next(r for r in rows4 if r["step"].startswith("③"))["lamp"] == "SKIP", f"{names} rc {rc4}")
    env = dict(os.environ)
    env.pop("VIA_FROM_VCGC", None)
    pr = subprocess.run([sys.executable, str(PRIOR_PATH), "--selftest"], capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=1500)
    chk("⑨ 直接前版自測(乾淨子行程)rc 0", pr.returncode == 0, (pr.stdout.strip().splitlines() or ["?"])[-1][:80])
    print(f"[計] {TAG} 自測 {len(ok)}/{len(ok) + len(bad)}" + (" · 不過:" + " · ".join(bad) if bad else " · PASS"), flush=True)
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
