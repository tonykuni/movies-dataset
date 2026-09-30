#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC v0180 — 薄尾:`test` 走 VCGC 全功能串測尾版 · `enter` 啟動前先串測 · help 目前生效入口改回尾版

操作員(側線 2026-09-30 b):「VCGC 所有功能盤點 … 用一個 PS 檔案串聯測試啟動一切不遺漏 且 AI 進入系統也會跑這流程
後面生成的指令也會跑這個流程 任何更新留紀錄版本及時間」。實測(同批):
  · `test` 由 v0160 釘死 CGC_MDL224_TestAuto_v0100.py(硬寫 9 支自測)—— 新版不會被接到。
  · `enter`(AI / 操作員唯一入口)沒有測 VCGC 自己的功能,容器沒有 pwsh 時 go 回 ABSENT,等於沒跑任何串測。
  · `help` 印「[目前生效入口] …v0177」:v0177 把 help 目錄接到自己身上,v0178 / v0179 沒接回。
本版:
  ① test [--quick|--full|--only <站>|inventory|--json] → VCGC run CGC_MDL224_TestAuto 尾版(閘 · 事件 · 教訓照舊)。
  ② enter:工具版本卡過了、啟動全部(go)之前先跑 test --quick;--card 也跑(AI 進場用 --card)。
     串測中(VIA_VCGC_TEST_ACTIVE=1)不再串測,防遞迴。
  ③ help 的目前生效入口 = 本版;多印 test 一行。其餘照 v0179。零網路。
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
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
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL149_VeritasCentralGovernanceConsole"
PRIOR_PATH = max(p for p in HERE.glob(_STEM + "_v*.py") if p.name < Path(__file__).name)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_v0180", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
TEST_FAMILY = "CGC_MDL224_TestAuto"
ACTIVE = "VIA_VCGC_TEST_ACTIVE"
TEST_LINE = "test [--quick|--full|--only <站>|inventory]  VCGC 全功能串測(盤點冊驅動 · 沿用 · 版本時間紀錄;PS 操作台 ①g 與 enter 都跑)"


def __getattr__(name):
    return getattr(PRIOR, name)


def _chain() -> list:
    mods, m = [], PRIOR
    while m is not None and m not in mods:
        mods.append(m)
        m = vars(m).get("PRIOR")
    return mods


def _owner(name: str):
    """(function, module) of the first console version below this one that defines `name` itself."""
    for m in _chain():
        if name in vars(m) and callable(vars(m)[name]):
            return vars(m)[name], m
    return None, None


# ---------------------------------------------------------------- ③ help: current entry is this tail
_V0177_CATALOG, _v0177 = _owner("help_catalog")          # v0179's own (it calls down the chain; untouched)
_SHOW, _SHOW_MOD = None, None
for _m in _chain():
    if "_SHOW_HELP" in vars(_m) and "show_current_help" in vars(_m):     # v0177: its show wraps v0175's original
        _SHOW, _SHOW_MOD = vars(_m)["show_current_help"], _m
        break


def help_catalog():
    card = PRIOR.help_catalog()
    card.update(entry=Path(__file__).name, previous=PRIOR_PATH.name, test=TEST_LINE)
    return card


def show_current_help():
    if _SHOW is not None:
        _SHOW()
    print("  " + TEST_LINE)


if _SHOW_MOD is not None:                                 # only the modules below v0177: its own catalog stays the base
    _below = _chain()[_chain().index(_SHOW_MOD) + 1:]
    for _m in _below:
        if "help_catalog" in vars(_m):
            _m.help_catalog = help_catalog
        if "show_current_help" in vars(_m):
            _m.show_current_help = show_current_help


# ---------------------------------------------------------------- ① test → the newest CGC_MDL224 tail through run
def test(args: list) -> int:
    return PRIOR.main(["run", "--family", "core", TEST_FAMILY] + list(args))


# ---------------------------------------------------------------- ② enter runs the chain before starting everything
def enter_with_test(rest: list, enter_fn=None, run_test=None, go_verb=None) -> int:
    enter_fn = enter_fn or _owner("enter")[0]
    run_test = run_test or (lambda: test(["--quick"]))
    _go = go_verb or _owner("_verb")[0]
    done = {}

    def go_after_test(go_args):
        print("[進入 5/5 · 啟動全部 · 先串測] via-vcgc test --quick(盤點 · 快站 · 更新過的尾版自測 · 版本時間紀錄)")
        done["test"] = run_test()
        print(f"[進入 5/5 · 串測] rc {done['test']}({'綠' if done['test'] == 0 else '黃' if done['test'] == 2 else '紅'};PS 操作台 ①g 會再跑整輪,沒變的站沿用)")
        return _go(["go", *go_args])

    if "--card" in rest:
        rc = enter_fn(rest)
        if rc == 0:
            print("[進入 · --card · 串測] via-vcgc test --quick(AI 進場也走同一流程)")
            done["test"] = run_test()
    else:
        rc = enter_fn(rest, go=go_after_test)
    t = done.get("test")
    if t is not None:
        print(f"[進入 · 串測總結] test --quick rc {t} · 入口 rc {rc}")
        if rc == 0 and t == 1:
            return 1
    return rc


# ---------------------------------------------------------------- main
def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] == ["test"]:
        if os.environ.get("VIA_FROM_VCGC") != "YES":
            print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
            return 2
        return test(args[1:])
    if args[:1] == ["enter"] and os.environ.get("VIA_FROM_VCGC") == "YES" and os.environ.get(ACTIVE) != "1":
        return enter_with_test(args[1:])
    return PRIOR.main(args)


# ---------------------------------------------------------------- selftest
def selftest():
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    seen = []
    real = PRIOR.main
    PRIOR.main = lambda a: seen.append(list(a)) or 0
    env = os.environ.get("VIA_FROM_VCGC")
    os.environ["VIA_FROM_VCGC"] = "YES"
    try:
        rc = main(["test", "--quick"])
        os.environ.pop("VIA_FROM_VCGC", None)
        denied = main(["test"])
    finally:
        PRIOR.main = real
        if env is None:
            os.environ.pop("VIA_FROM_VCGC", None)
        else:
            os.environ["VIA_FROM_VCGC"] = env
    chk("① test 走 run CGC_MDL224_TestAuto 尾版(不再釘 v0100);不經 VCGC 拒跑",
        rc == 0 and seen == [["run", "--family", "core", TEST_FAMILY, "--quick"]] and denied == 2, seen)
    order = []
    rc_full = enter_with_test([], enter_fn=lambda r, go=None: go(["-NoOpen"]),
                              run_test=lambda: order.append(("test",)) or 2,
                              go_verb=lambda a: order.append(("go", list(a))) or 0)
    chk("② enter:串測在啟動全部(go)之前、go 照舊帶參數;串測黃不擋啟動",
        order == [("test",), ("go", ["go", "-NoOpen"])] and rc_full == 0, order)
    order.clear()
    rc_card_red = enter_with_test(["--card"], enter_fn=lambda r, go=None: 0, run_test=lambda: order.append(("test",)) or 1,
                                  go_verb=lambda a: order.append(("go",)) or 0)
    order2 = []
    rc_card_bad = enter_with_test(["--card"], enter_fn=lambda r, go=None: 2, run_test=lambda: order2.append(("test",)) or 0,
                                  go_verb=lambda a: 0)
    chk("③ enter --card(AI 進場)也串測、不啟動;串測紅 → 入口回紅;入口卡沒過就不串測",
        order == [("test",)] and rc_card_red == 1 and rc_card_bad == 2 and order2 == [], (rc_card_red, rc_card_bad))
    os.environ[ACTIVE] = "1"
    os.environ["VIA_FROM_VCGC"] = "YES"
    hit = []
    real = PRIOR.main
    PRIOR.main = lambda a: hit.append(list(a)) or 0
    try:
        main(["enter", "--card", "--no-pull"])
    finally:
        PRIOR.main = real
        os.environ.pop(ACTIVE, None)
        if env is None:
            os.environ.pop("VIA_FROM_VCGC", None)
        else:
            os.environ["VIA_FROM_VCGC"] = env
    chk("④ 串測中(VIA_VCGC_TEST_ACTIVE=1)enter 直接走前版:不遞迴", hit == [["enter", "--card", "--no-pull"]], hit)
    low = [m for m in _chain() if "show_current_help" in vars(m) and "_SHOW_HELP" not in vars(m)]
    entries = {vars(m)["help_catalog"]().get("entry") for m in low if "help_catalog" in vars(m)}
    chk("⑤ help 目前生效入口 = 本版(v0177 以下各版的目錄與說明都接到本版)· 多一行 test",
        _SHOW is not None and entries == {Path(__file__).name} and help_catalog().get("test") == TEST_LINE, entries)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 加速器橋 · 網路橋在;不碰 TA-Lib", "VIA:ACCEL-BRIDGE" in src and "VIA:NET-BRIDGE" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M))
    print(f"[VCGC v0180] 本版 {sum(ok)}/{len(ok)}")
    if not all(ok):
        return 1
    return PRIOR.selftest()


if __name__ == "__main__":
    raise SystemExit(selftest() if sys.argv[1:] == ["--selftest"] else main())
