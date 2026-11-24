#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VCGC_CommandHub v0106 — 薄尾(v0100–v0105 一字不動):短指令 via-bak / via-pano 與主控台選單接到 v0105 的新做法

PR #733 Codex 審查(P2):PS 載入器把短指令叫成 `x via-bak` / `x via-pano`,選單也走同一條路:
  v0102 的 dispatch() 查表後呼叫「v0102 模組裡的 main」;v0104 把那個 main 換成自己的,v0105 沒換
  → 短指令與選單都繞過 v0105 的 bak(ApplyRun G 道)/ pano(全景 + 工具箱 + 連線),--net 等新旗標落到舊的剖析器。
本版只做一件事:把 v0102 模組的 main(dispatch 真正讀的那一層)換成本版的路由:
  bak · pano · boot --all → v0105(照 v0105 的分工:bak --incremental 仍交前版的增量快照)
  其他                    → 換之前的那一個 main(v0104 的 _main_v0104),行為不變
不另改指令表、不改 PS(載入器照舊叫 `x <短令>`)。不 import 他系統。零 TA-Lib。
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
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VCGC_CommandHub"
TAG = "VCGC_CommandHub v0106"


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
    """前版鏈上自己定義 name 的那一版(換在 dispatch 真正讀的那一層;R4 換錯層)。"""
    m, seen = PRIOR, set()
    while m is not None and id(m) not in seen:
        seen.add(id(m))
        if name in vars(m):
            return m
        m = vars(m).get("PRIOR") or vars(m).get("P0")
    return None


DISPATCH_OWNER = _owner("dispatch")          # v0102:dispatch() 查 CMD 後呼叫本模組的 main
_PREV_MAIN = DISPATCH_OWNER.main if DISPATCH_OWNER is not None else None


def _to_hub(a: list) -> bool:
    return a[:1] in (["bak"], ["pano"]) or (a[:1] == ["boot"] and "--all" in a)


def route(argv: list | None = None) -> int:
    """dispatch / 選單 / 本版入口共用:bak · pano · boot --all 交 v0105,其他交換之前的 main。"""
    a = list(sys.argv[1:] if argv is None else argv)
    if _to_hub(a):
        keep = sys.argv
        sys.argv = [keep[0] if keep else "hub"] + a
        try:
            return PRIOR.main()                  # v0105 的 main 讀 sys.argv
        finally:
            sys.argv = keep
    return _PREV_MAIN(a)


if DISPATCH_OWNER is not None:
    DISPATCH_OWNER.main = route


def main(argv: list | None = None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return route(a)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("[計] %s 自測開始(本版 6 項 · 前版 %s)" % (TAG, PRIOR_PATH.name), flush=True)
    chk("T1 前版是 v0105;dispatch 在 v0102(換在 dispatch 讀的那一層)",
        PRIOR_PATH.name == "VCGC_CommandHub_v0105.py" and DISPATCH_OWNER is not None
        and Path(getattr(DISPATCH_OWNER, "__file__", "")).name == "VCGC_CommandHub_v0102.py",
        (PRIOR_PATH.name, getattr(DISPATCH_OWNER, "__file__", None)))
    chk("T2 v0102 模組的 main 已換成本版路由;換之前的那一個留著給其他動詞", DISPATCH_OWNER.main is route
        and callable(_PREV_MAIN) and _PREV_MAIN is not route, _PREV_MAIN)
    hub, prev = [], []
    keep = (PRIOR.cmd_bak, PRIOR.cmd_pano, PRIOR.cmd_boot, PRIOR.run, globals()["_PREV_MAIN"], sys.argv)
    try:
        PRIOR.cmd_bak = lambda note, net: (hub.append(("bak", note, net)), ([], 0))[1]
        PRIOR.cmd_pano = lambda apply, scope, net, since: (hub.append(("pano", apply, scope, net)), ([], 0))[1]
        PRIOR.cmd_boot = lambda all_, net, since: (hub.append(("boot", all_, net)), ([], 0))[1]
        PRIOR.run = lambda cmd, title, rows, rc: 0
        sys.argv = ["hub"]
        r = [main(["x", "via-bak", "--note", "n", "--net"]),          # PS 載入器的路:x <短令> → 整條前版鏈 → dispatch
             DISPATCH_OWNER.dispatch("via-pano", ["--apply", "--scope", "S"])]   # 選單的路:直接 dispatch
        chk("T3 x via-bak / x via-pano(PS 載入器與選單的路)→ v0105 的 bak / pano(--net 交新剖析器)",
            hub == [("bak", "n", True), ("pano", True, "S", False)] and r == [0, 0], (hub, r))
        hub.clear()
        globals()["_PREV_MAIN"] = lambda a: prev.append(list(a)) or 0
        route(["boot", "--all", "--net"])
        route(["doctor"])
        route(["boot"])
        chk("T4 boot --all → v0105;doctor / boot(不帶 --all)→ 換之前的 main,參數不變",
            hub == [("boot", True, True)] and prev == [["doctor"], ["boot"]], (hub, prev))
        chk("T5 呼叫後 sys.argv 還原", sys.argv == ["hub"], sys.argv)
    finally:
        PRIOR.cmd_bak, PRIOR.cmd_pano, PRIOR.cmd_boot, PRIOR.run, globals()["_PREV_MAIN"], sys.argv = keep
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T6 檔面:第 3 行加速器標記 · 零 TA-Lib · 本行程不寫同意閘 · 不 import 他系統",
        src.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]" and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", src) and not re.search(r"^\s*(import|from)\s+(VDF|VRN|VQG|VAP)", src, re.M))
    n = sum(ok)
    print("[計] %s 自測 %d/%d · %s" % (TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    print("[前版] %s 自測(原函式)" % PRIOR_PATH.name, flush=True)
    DISPATCH_OWNER.main = _PREV_MAIN               # 前版自測照它原本的鏈跑(前版自測慣例)
    try:
        rc_prior = PRIOR.selftest()
    finally:
        DISPATCH_OWNER.main = route
    print("[計] %s 自測 OK %d · FAIL %d · 前版 rc=%s" % (TAG, n, len(ok) - n, rc_prior), flush=True)
    return 0 if n == len(ok) and rc_prior == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
