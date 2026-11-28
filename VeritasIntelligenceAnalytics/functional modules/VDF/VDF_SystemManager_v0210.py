#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF SystemManager v0210 — 薄尾(v0209 以前一字不動):hostrun 逾時要砍整棵行程樹(PR #777 Codex P2)

v0208 的 stream() 逾時只 kill() 管理器那一支;vv 步驟裡 v0197 one_engine() 用 subprocess.run() 開的引擎自測子行程
  沒被砍,還在跑(吃 CPU、可能鎖著庫),hostrun 卻已往下跑 outputs 與 check-db。
本版:
  ① stream():每一步開在自己的行程群組(POSIX start_new_session · Windows CREATE_NEW_PROCESS_GROUP);
     逾時(或結束後收不了屍)→ 整群砍掉(POSIX killpg SIGKILL · Windows taskkill /T /F),再收屍,回 124。
     換掉 v0208 模組裡的 stream,v0208 的 cmd_hostrun 照用。
  ② 修 v0209 的潛在無限重跑:v0209 hostrun 只要家族尾版比 v0209 新就開子行程跑尾版;直接跑本檔時尾版就是本檔,
     子行程又回到 v0209 → 又開本檔……。本版改成跟「實際被啟動的那一版」比:被啟動的就是最新 → 不重跑。
     判法不寫死本檔版號,以後的新版照樣成立。
其餘照 v0209。零網路(git fetch 除外)· 不碰 TA-Lib · 不設同意閘 · 不 import VCGC。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(VDF 全導入令;惰性載入=import 時零網路、零行為變更) =====
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT;網路只認 AegisNexus);缺席回 None(誠實)"""
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
import queue
import re
import signal
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

VERSION = "v0210"
STEM = "VDF_SystemManager"
TAG = f"VDF_SystemManager {VERSION}"
HERE = Path(__file__).resolve().parent


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)                 # v0209
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


V209 = PRIOR
V208 = V209.V208
V194 = V209.V194
_ORIG_STREAM = V208.stream
_ORIG_NEWEST = V209.newest_tail


def _popen_group_kwargs() -> dict:
    if os.name == "nt":
        return {"creationflags": getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x200)}
    return {"start_new_session": True}


def kill_tree(p: subprocess.Popen) -> None:
    """整棵砍:Windows taskkill /T /F(要在父行程還活著時從它往下找);POSIX 砍整個行程群組。最後收屍。"""
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True, timeout=30,
                           stdin=subprocess.DEVNULL)
        else:
            os.killpg(p.pid, signal.SIGKILL)
    except (OSError, subprocess.SubprocessError):
        pass
    try:
        p.kill()
    except OSError:
        pass
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        pass


def stream(cmd: list, timeout: float, out: list) -> int:
    """照 v0208:逐行照印並收下、期限另外看;差別:每步自成行程群組,逾時整棵砍掉,回 124。"""
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    for k in ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT"):
        env.pop(k, None)
    p = subprocess.Popen(cmd, cwd=tempfile.gettempdir(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                         encoding="utf-8", errors="replace", env=env, stdin=subprocess.DEVNULL, **_popen_group_kwargs())
    q: queue.Queue = queue.Queue()

    def reader():
        for ln in p.stdout:
            q.put(ln)
        q.put(None)

    threading.Thread(target=reader, daemon=True).start()
    deadline = time.time() + timeout
    while True:
        try:
            ln = q.get(timeout=0.5)
        except queue.Empty:
            ln = ""
        if ln is None:
            try:
                return p.wait(timeout=60)
            except subprocess.TimeoutExpired:
                kill_tree(p)
                return 124
        if ln:
            print(ln, end="", flush=True)
            out.append(ln.rstrip("\n"))
        if time.time() > deadline:
            kill_tree(p)
            out.append(f"[hostrun] 逾時 {timeout}s → 整棵行程樹砍掉")
            return 124


def launched_file() -> Path:
    """實際被啟動的那一版(__main__ 是本家族的某一版就用它;被別的程式匯入時用本檔)。"""
    m = sys.modules.get("__main__")
    f = Path(getattr(m, "__file__", "") or "")
    return f.resolve() if f.name.startswith(STEM + "_v") else Path(__file__).resolve()


def newest_tail(folder: Path = HERE) -> Path:
    """給 v0209 hostrun 用:尾版沒有比被啟動的那一版新 → 回 v0209 自己(不重跑);真的有更新的才回那一支。"""
    t = _ORIG_NEWEST(folder)
    return t if _vnum(t) > _vnum(launched_file()) else Path(V209.__file__)


V208.stream = stream
V209.newest_tail = newest_tail


def cmd_hostrun(args: list) -> int:
    return V209.cmd_hostrun(args)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:240]) if note and not cond else ""), flush=True)

    print(f"[計] {TAG} 自測開始(本版 4 項 + 前版 {PRIOR_PATH.name} 自測 · 暫存夾 · 零網路)", flush=True)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T1 加速器真的載到 · 第 3 行標記 · 網路橋在", VIA_ACCEL is not None and src.splitlines()[2] == "# [VIA:ACCEL-BRIDGE:v0111]"
        and VIA_NET_TOOL_PATH is not None)
    with tempfile.TemporaryDirectory(prefix="vdf_sm210_") as td:
        mark = Path(td) / "grandchild_survived.txt"
        grand = f"import time,pathlib;time.sleep(2.5);pathlib.Path({str(mark)!r}).write_text('x')"
        child = ("import subprocess,sys,time;subprocess.Popen([sys.executable,'-c'," + repr(grand) + "]);"
                 "print('child up',flush=True);time.sleep(30)")
        lines = []
        t0 = time.time()
        rc = stream([sys.executable, "-c", child], 0.8, lines)
        took = time.time() - t0
        time.sleep(3.5)
        survived = mark.exists()
    chk("T2 (Codex P2)逾時 → 回 124、整棵砍(孫行程 2.5 秒後要寫檔,砍完等 3.5 秒檔仍不在)",
        rc == 124 and not survived and took < 15 and any("child up" in x for x in lines), (rc, survived, round(took, 1), lines))
    lines2 = []
    rc2 = stream([sys.executable, "-c", "print('a');print('b');raise SystemExit(3)"], 30, lines2)
    chk("T3 一般結束照收輸出、照回 rc(不砍)", rc2 == 3 and lines2 == ["a", "b"], (rc2, lines2))
    t_self = newest_tail()
    entry = launched_file()
    chk("T4 (無限重跑)被啟動的就是最新 → v0209 不再開子行程;換掉的是 v0208 的 stream 與 v0209 的 newest_tail",
        (Path(t_self) == Path(V209.__file__) if _vnum(_ORIG_NEWEST(HERE)) <= _vnum(entry) else _vnum(t_self) > _vnum(entry))
        and V208.stream is stream and V209.newest_tail is newest_tail, (t_self, entry))
    V208.stream, V209.newest_tail = _ORIG_STREAM, _ORIG_NEWEST    # 跑前版自測時還原前版自己的函式
    try:
        rc = PRIOR.selftest() if callable(getattr(PRIOR, "selftest", None)) else 1
    finally:
        V208.stream, V209.newest_tail = stream, newest_tail
    chk("T5 前版 v0209 自測照過(含整條前版鏈)", rc == 0, rc)
    print(f"[計] {TAG} 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(a)


if __name__ == "__main__":
    raise SystemExit(main())
