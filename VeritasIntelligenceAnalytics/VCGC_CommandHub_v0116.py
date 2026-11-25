#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC_CommandHub v0116 — 薄尾(v0100–v0115 一字不動):via-graph / via-bak 子動詞長跑有心跳 · Ctrl+C 收整棵子行程樹

操作員 2026-11-25 主機實錄:via-graph / 安全同步跑了好幾分鐘畫面完全沒字 → 以為卡住按 Ctrl+C,
  留下一段 subprocess._communicate 的 KeyboardInterrupt 追蹤。CLAUDE.md「長跑要有心跳」:子行程每 30 秒內至少一行。
本版:v0115 的 cmd_graph(建圖 · git 讀倉 · 查詢)與 cmd_bak_sub(還原 / 卡 / 對倉)改用 hb_run 起子行程:
  ① 每 VIA_HEARTBEAT_SEC 秒(預設 30,上限 30)印一行:哪一步 · 已幾秒 · pid ·(有 psutil 時)系統可用記憶體;
  ② 子行程自己一個行程群組;按 Ctrl+C → 收掉整棵子行程樹,印「這一步沒完成 · 不寫快照」,rc 130(不留孤兒寫手);
  ③ timeout 到了一樣收整棵樹再丟 TimeoutExpired(git_state 已照 v0115 接住 → 快照標「讀不到倉」)。
其餘照 v0115(fail-closed · 快照 · 只增帳 · 離線)。換的是 v0115 模組全域 cmd_graph / cmd_bak_sub,v0115 的 route 叫到的就是本版。
不 import 他系統;零 TA-Lib;不設同意閘。
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

import importlib.util
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VCGC_CommandHub"
TAG = "VCGC_CommandHub v0116"


def _vnum(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
if PRIOR_PATH.stem in sys.modules:
    PRIOR = sys.modules[PRIOR_PATH.stem]
else:
    _spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem, PRIOR_PATH)
    PRIOR = importlib.util.module_from_spec(_spec)
    sys.modules[PRIOR_PATH.stem] = PRIOR
    _spec.loader.exec_module(PRIOR)
_PREV_GRAPH, _PREV_BAK = PRIOR.cmd_graph, PRIOR.cmd_bak_sub


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def heartbeat_sec() -> int:
    try:
        v = int(os.environ.get("VIA_HEARTBEAT_SEC", "30"))
    except ValueError:
        v = 30
    return max(1, min(v, 30))                          # 規定:30 秒內至少一行


def _label(argv: list) -> str:
    a = [str(x) for x in argv]
    if "graphify" in a and "run" in a and "--system" in a:
        return "建圖 " + a[a.index("--system") + 1]
    if a[:1] == ["git"]:
        return "讀倉(git " + " ".join(x for x in a[1:] if not x.startswith("/") and x != "-C")[:40] + ")"
    return Path(a[0]).name + (" " + a[1] if len(a) > 1 and not a[1].endswith(".py") else (" " + a[2] if len(a) > 2 else ""))


def _free_mem() -> str:
    try:
        import psutil
        return " · 可用記憶體 %.1f GB" % (psutil.virtual_memory().available / 1e9)
    except Exception:                                   # noqa: BLE001
        return ""


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


def hb_run(argv, env=None, cwd=None, capture_output=False, text=False, timeout=None, every=None, log=print):
    """subprocess.run 的替身(v0115 用到的參數):長跑每 every 秒印一行心跳;Ctrl+C / 逾時收整棵子行程樹。"""
    every = every or heartbeat_sec()
    kw = {"env": env, "cwd": cwd}
    if capture_output:
        kw.update(stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if text:
            kw.update(encoding="utf-8", errors="replace")
    if os.name == "nt":
        kw["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kw["start_new_session"] = True
    start = time.monotonic()
    proc = subprocess.Popen(list(argv), **kw)
    label = _label(argv)
    try:
        while True:
            try:
                out, err = proc.communicate(timeout=every)
                break
            except subprocess.TimeoutExpired:
                spent = int(time.monotonic() - start)
                if timeout is not None and spent >= timeout:
                    _kill_tree(proc)
                    raise subprocess.TimeoutExpired(argv, timeout)
                log("[via-graph] 心跳 · %s 還在跑 · 已 %d 秒 · pid %d%s(不用按 Ctrl+C)" % (label, spent, proc.pid, _free_mem()), flush=True)
    except KeyboardInterrupt:
        _kill_tree(proc)
        log("[via-graph] 收到 Ctrl+C · %s 的子行程(pid %d)已整棵收掉 · 這一步沒完成,不寫快照" % (label, proc.pid), flush=True)
        raise
    return subprocess.CompletedProcess(argv, proc.returncode, out, err)


def cmd_graph(args: list, run=None, out: Path = None) -> int:
    try:
        return _PREV_GRAPH(args, run=run or hb_run, out=out)
    except KeyboardInterrupt:
        return 130


def cmd_bak_sub(args: list, run=None) -> int:
    try:
        return _PREV_BAK(args, run=run or hb_run)
    except KeyboardInterrupt:
        return 130


def install() -> None:
    PRIOR.cmd_graph = cmd_graph                         # v0115 的 route / main 查模組全域 → 用本版
    PRIOR.cmd_bak_sub = cmd_bak_sub


def _restore() -> None:
    PRIOR.cmd_graph, PRIOR.cmd_bak_sub = _PREV_GRAPH, _PREV_BAK


install()


def main(argv: list | None = None) -> int:
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

    print("[計] %s 自測開始(本版 6 項 · 前版 %s)" % (TAG, PRIOR_PATH.name), flush=True)
    lines = []
    log = lambda *a, **k: lines.append(" ".join(str(x) for x in a))   # noqa: E731
    r = hb_run([sys.executable, "-c", "import time; time.sleep(2.6)"], every=1, log=log)
    beats = [x for x in lines if "心跳" in x]
    chk("① 長跑每秒(測試間隔)一行心跳 · 寫哪一步 · 已幾秒 · pid · 回傳碼照收", r.returncode == 0 and len(beats) >= 2
        and all("已 " in x and "pid" in x for x in beats), lines)
    r2 = hb_run([sys.executable, "-c", "import sys; print('\\u5b8c\\u6210'); sys.exit(3)"], capture_output=True, text=True, every=5, log=log)
    chk("② capture_output + text:stdout 照收(UTF-8)· 非 0 回傳碼原樣交回", r2.returncode == 3 and r2.stdout.strip() == "完成", (r2.returncode, r2.stdout))
    t0 = time.monotonic()
    timed_out = False
    try:
        hb_run([sys.executable, "-c", "import time; time.sleep(30)"], timeout=2, every=1, log=log)
    except subprocess.TimeoutExpired:
        timed_out = True
    chk("③ 逾時:收整棵子行程樹再丟 TimeoutExpired(不等子行程自己結束)", timed_out and time.monotonic() - t0 < 10, round(time.monotonic() - t0, 1))
    calls = []

    def boom(argv, **kw):
        calls.append(list(argv))
        raise KeyboardInterrupt
    with contextlib.redirect_stdout(io.StringIO()):
        rc_int = cmd_graph(["build", "--sys", "VCGC"], run=boom)
    chk("④ 建圖途中 Ctrl+C:via-graph 回 rc 130(不吐 Python 追蹤)", rc_int == 130, (rc_int, calls[:1]))
    chk("⑤ v0115 的 route / main 叫到的是本版(模組全域已換)· 心跳間隔上限 30 秒",
        PRIOR.cmd_graph is cmd_graph and PRIOR.cmd_bak_sub is cmd_bak_sub and heartbeat_sec() <= 30 and PRIOR_PATH.name < Path(__file__).name)
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("⑥ 檔面:加速器橋 · 零 TA-Lib · 不設同意閘 · 不 import 他系統",
        "[VIA:ACCEL-BRIDGE:v0100]" in src and not re.search(r"^\s*(import|from)\s+talib", body, re.M)
        and not re.search(r"os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", body) and not re.search(r"^\s*(import|from)\s+(VDF_|VRN_|VQG_|VAP_|CGC_)", body, re.M))
    n = sum(ok)
    print("[計] %s 自測 %d/%d · %s" % (TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    print("[前版] %s 自測(換回前版的 cmd_graph / cmd_bak_sub)" % PRIOR_PATH.name, flush=True)
    _restore()
    try:
        rc_prior = PRIOR.selftest()
    finally:
        install()
    print("[計] %s 自測 OK %d · FAIL %d · 前版 rc=%s" % (TAG, n, len(ok) - n, rc_prior), flush=True)
    return 0 if n == len(ok) and rc_prior == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
