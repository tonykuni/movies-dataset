#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VCGC_CommandHub v0111 — 薄尾(v0100–v0110 一字不動):新短令 via-health(先期檢查 · 安裝 · 系統健康,一行常態用)

2026-11-24 操作員「上面若有先期檢查安裝檢視指令及系統健康的功能都優化放入 VCGC 當常態使用工具」:
  今天主機上這件事是靠一長串 PS 一行(HostBoot → FastRun --set env,…)跑的;本版把它收成 VCGC 的一個短令,
  PS 載入器照 `names --ps` 自動生函式,操作員只打 `via-health`。
via-health 做什麼(不另寫引擎,只呼叫 FastRun 尾版):
  env  → doctor(裝前 6 項)→ 安裝閘(CGC_MDL056,只裝 doctor 計畫列的)→ doctor(裝後 3 項)· 環境總管 envmgr 並行
  vrn  → VRN_SystemManager 尾版 version · health · verbs
  vdf  → VDF_SystemManager 尾版 version · health
  動態進度條 · 每步上限 · 全文寫 VIA_Reports/fastrun/<時間>/ · 加 --push 推收據到 intake 分支(只有雜湊與數字)。
  可加:--set env(只查環境)· --set env,vrn,vdf,fidelity · --lanes N · --timeout 秒 · --push。
FastRun 自己經 VCGC 過閘(VIA_FROM_VCGC 由它的子行程設,本中樞不設、不寫檔)。不 import 他系統。零 TA-Lib。
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
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VCGC_CommandHub"
TAG = "VCGC_CommandHub v0111"
FASTRUN_DIR = HERE / "docs" / "handoff" / "ai"
HEALTH_DEFAULT_SET = "env,vrn,vdf"


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


def __getattr__(name):
    return getattr(PRIOR, name)


def _owner(name: str):
    """前版鏈上自己定義 name 的那一版(換在真正被讀的那一層;R4 換錯層)。"""
    m, seen = PRIOR, set()
    while m is not None and id(m) not in seen:
        seen.add(id(m))
        if name in vars(m):
            return m
        m = vars(m).get("PRIOR") or vars(m).get("P0")
    return None


DISPATCH_OWNER = _owner("dispatch")          # v0102:dispatch() 查 CMD 後呼叫本模組的 main;CMD / COMMANDS 也在這
_PREV_MAIN = DISPATCH_OWNER.main             # = v0106 的 route


def fastrun_tail(root: Path = FASTRUN_DIR) -> Path | None:
    c = [p for p in root.glob("VIA_FastRun_v*.py") if _vnum(p) >= 0]
    return max(c, key=_vnum) if c else None


def health_argv(args: list, tail: Path) -> list:
    a = list(args)
    if not any(x == "--set" or x.startswith("--set=") for x in a):
        a = ["--set", HEALTH_DEFAULT_SET] + a
    return [sys.executable, str(tail), *a]


def cmd_health(args: list) -> int:
    t = fastrun_tail()
    if t is None:
        print("[via-health] 找不到 VIA_FastRun 尾版(%s)→ 先 git fetch / switch 到有它的分支" % FASTRUN_DIR)
        return 3
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    env.pop("VIA_FROM_VCGC", None)               # 交給 FastRun 自己經 VCGC 過閘(它外層畫進度條)
    argv = health_argv(args, t)
    print("[via-health] %s %s" % (t.name, " ".join(argv[2:])), flush=True)
    return subprocess.run(argv, cwd=str(HERE.parent), env=env).returncode


def route(argv: list | None = None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["health"]:
        return cmd_health(a[1:])
    return _PREV_MAIN(a)


DISPATCH_OWNER.main = route
if "via-health" not in DISPATCH_OWNER.CMD:
    DISPATCH_OWNER.COMMANDS.append({
        "name": "via-health", "group": "環境", "title": "先期檢查 · 安裝 · 系統健康(常態用)", "target": ["health"],
        "plugin": "VIA_FastRun 尾版(doctor → 安裝閘 → doctor · envmgr · VRN / VDF health)",
        "help": "一行跑完:VCGC doctor 裝前 6 項 → 經安裝閘(CGC_MDL056)只裝 doctor 計畫列的 → 裝後重驗 3 項;"
                "環境總管 envmgr 與 VRN / VDF 的 version · health 並行。動態進度條 · 每步上限 · 全文在 VIA_Reports/fastrun/。"
                "--set 換組(env · vrn · vdf · nlp · fidelity)· --push 推收據(只有雜湊與數字)。",
        "examples": ["via-health", "via-health --push", "via-health --set env", "via-health --set env,vrn,vdf,fidelity --push"],
        "replaces": []})
    DISPATCH_OWNER.CMD["via-health"] = DISPATCH_OWNER.COMMANDS[-1]


def main(argv: list | None = None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    if a[:1] == ["health"]:
        return cmd_health(a[1:])
    return PRIOR.main(a)


def selftest() -> int:
    import contextlib
    import io
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("[計] %s 自測開始(本版 5 項 · 前版 %s)" % (TAG, PRIOR_PATH.name), flush=True)
    chk("T1 換在 dispatch 讀的那一層(v0102)· 前版是 v0110",
        Path(DISPATCH_OWNER.__file__).name == "VCGC_CommandHub_v0102.py" and DISPATCH_OWNER.main is route
        and PRIOR_PATH.name == "VCGC_CommandHub_v0110.py")
    c = DISPATCH_OWNER.CMD.get("via-health")
    names = [x["name"] for x in DISPATCH_OWNER.COMMANDS]
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        DISPATCH_OWNER.cmd_names(ps=True)
    chk("T2 指令冊有 via-health(一筆 · 欄位齊)· names --ps 印得出 → PS 載入器自動生函式",
        c and names.count("via-health") == 1 and all(c.get(k) for k in ("help", "examples", "plugin", "target"))
        and "via-health|via-health" in buf.getvalue().splitlines())
    t = fastrun_tail()
    a1 = health_argv([], Path("F.py"))
    a2 = health_argv(["--set", "env", "--push"], Path("F.py"))
    chk("T3 預設組 env,vrn,vdf · 自己給 --set 就照給的 · 其他參數原樣轉 · FastRun 尾版找得到",
        a1[2:] == ["--set", "env,vrn,vdf"] and a2[2:] == ["--set", "env", "--push"] and t is not None and _vnum(t) >= 103, (a1, a2, t))
    seen = []
    keep_run, keep_flag = subprocess.run, os.environ.get("VIA_FROM_VCGC")
    try:
        subprocess.run = lambda argv, cwd=None, env=None: (seen.append((argv, cwd, env)) or type("R", (), {"returncode": 0})())
        os.environ["VIA_FROM_VCGC"] = os.environ.get("VIA_FROM_VCGC", "YES")
        with contextlib.redirect_stdout(io.StringIO()):
            rcs = [main(["x", "via-health", "--push"]),               # PS 載入器的路:x <短令> → 整條前版鏈 → dispatch → route
                   DISPATCH_OWNER.dispatch("via-health", []),         # 選單的路:直接 dispatch
                   main(["health", "--set", "env"])]                  # 本版入口
    finally:
        subprocess.run = keep_run
        os.environ.pop("VIA_FROM_VCGC", None) if keep_flag is None else os.environ.__setitem__("VIA_FROM_VCGC", keep_flag)
    chk("T4 三條路(x 短令 · 選單 dispatch · 直接 health)都到 FastRun 尾版 · 子行程不帶 VIA_FROM_VCGC(交 FastRun 自己過閘)",
        rcs == [0, 0, 0] and len(seen) == 3 and all(Path(s[0][1]).name.startswith("VIA_FastRun_v") for s in seen)
        and seen[0][0][2:] == ["--set", "env,vrn,vdf", "--push"] and seen[2][0][2:] == ["--set", "env"]
        and all("VIA_FROM_VCGC" not in s[2] for s in seen), (rcs, [s[0][2:] for s in seen]))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T5 檔面:加速器橋 · 零 TA-Lib · 不寫同意閘 · 不 import 他系統",
        "[VIA:ACCEL-BRIDGE:v0100]" in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", src)
        and not re.search(r"^\s*(import|from)\s+(VDF_|VRN_|VQG_|VAP_)", src, re.M))
    n = sum(ok)
    print("[計] %s 自測 %d/%d · %s" % (TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    print("[前版] %s 自測(dispatch 讀的 main 還原成前版的)" % PRIOR_PATH.name, flush=True)
    DISPATCH_OWNER.main = _PREV_MAIN
    try:
        rc_prior = PRIOR.selftest()
    finally:
        DISPATCH_OWNER.main = route
    print("[計] %s 自測 OK %d · FAIL %d · 前版 rc=%s" % (TAG, n, len(ok) - n, rc_prior), flush=True)
    return 0 if n == len(ok) and rc_prior == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
