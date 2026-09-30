#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC v0181 — 薄尾:`monitor` 動詞 · 任何 VCGC 動作收尾都在背景自動開全景監控(AUTO SYNC VCGC ↔ 子系統)

操作員(側線 2026-09-30):「上傳擋入 VCGC 起任何碰到 VCGC 就自動開啟他來監控 · 與 VCGC 高度 AUTO SYNC ·
  VCGC 與子系統高度 AUTO SYNC」「導入加速器」
本版:
  ① monitor [scan|watch|dashboard|lessons|sync|show …] → VCGC run VIA_Panorama 尾版(閘 · 事件 · 教訓照舊)。
     不叫 panorama:那是 v0103 起既有的「全景(PLAN 預覽)」動詞(盤點冊站 V-panorama),本版原樣轉交前版、不蓋。
  ② 自動監控:每個 VCGC 動作(成功或失敗)收尾都呼叫 VIA_Panorama 尾版 `autostart --from <動詞>`
     (VIA_ACCEL.run_fast · 20 秒上限;對方約 0.3 秒回):記一筆觸碰;背景監控沒在跑就起一支(單例),
     背景那支每輪全景(304 不重掃)+ 有觸碰就經本入口跑唯讀同步探針 sync-check · ssot panorama(VCGC → VDF → VRN → SUP)。
     提示只寫 stderr 一行,不污染 stdout(sync-check 等動詞印 JSON 給別支解析)。
     不觸發:VIA_PANORAMA_AUTO=0 · 背景監控自己呼叫(VIA_PANORAMA_ACTIVE=1,防遞迴)· 串測中(VIA_VCGC_TEST_ACTIVE=1)· CI=true · --selftest。
     --apply 一律不自動下(同意閘);監控只列待批准指令。
  ③ help 的目前生效入口 = 本版;多印 monitor 一行。其餘照 v0180。零網路。
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
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL149_VeritasCentralGovernanceConsole"
PRIOR_PATH = max(p for p in HERE.glob(_STEM + "_v*.py") if p.name < Path(__file__).name)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_v0181", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
PANORAMA_FAMILY = "VIA_Panorama"
AUTO_ENV = "VIA_PANORAMA_AUTO"
ACTIVE_ENV = "VIA_PANORAMA_ACTIVE"
TEST_ENV = "VIA_VCGC_TEST_ACTIVE"
PANO_LINE = ("monitor [scan|watch|dashboard|lessons|sync|show …]  VIA 全景(只讀)· 任何 VCGC 動作都會在背景自動開監控與"
             " AUTO SYNC(VIA_PANORAMA_AUTO=0 關)")


def __getattr__(name):
    return getattr(PRIOR, name)


def _chain() -> list:
    mods, m = [], PRIOR
    while m is not None and m not in mods:
        mods.append(m)
        m = vars(m).get("PRIOR")
    return mods


# ---------------------------------------------------------------- ③ help: current entry is this tail
_PREV_CATALOG = PRIOR.help_catalog
_PREV_SHOW = vars(PRIOR).get("_show_help_v0180")


def help_catalog():
    card = _PREV_CATALOG()
    card.update(entry=Path(__file__).name, previous=PRIOR_PATH.name, monitor=PANO_LINE)
    return card


def _show_help_v0181():
    if _PREV_SHOW is not None:
        _PREV_SHOW()
    print("  " + PANO_LINE)


_PATCHED: list = []


def _patch_help(on: bool = True) -> None:
    """v0180 把舊版的 help 接到它身上;本版接回自己(v0180 本身不動)。on=False 還原(跑前版自測時用)。"""
    if on:
        for _m in _chain()[1:]:
            if vars(_m).get("help_catalog") is _PREV_CATALOG:
                _m.help_catalog = help_catalog
                _PATCHED.append((_m, "help_catalog", _PREV_CATALOG))
            if _PREV_SHOW is not None and vars(_m).get("show_current_help") is _PREV_SHOW:
                _m.show_current_help = _show_help_v0181
                _PATCHED.append((_m, "show_current_help", _PREV_SHOW))
    else:
        for _m, attr, orig in _PATCHED:
            setattr(_m, attr, orig)
        _PATCHED.clear()


_patch_help(True)


# ---------------------------------------------------------------- ① monitor → VIA_Panorama 尾版 through run
def monitor(args: list) -> int:
    return PRIOR.main(["run", "--family", "core", PANORAMA_FAMILY] + list(args))


# ---------------------------------------------------------------- ② 任何 VCGC 動作收尾 → 背景自動開監控
def panorama_tail() -> Path | None:
    hits = sorted(HERE.glob(PANORAMA_FAMILY + "_v*.py"))
    return hits[-1] if hits else None


def auto_skip(args: list) -> str:
    if os.environ.get(AUTO_ENV) == "0":
        return f"{AUTO_ENV}=0"
    if os.environ.get(ACTIVE_ENV) == "1":
        return "監控自己呼叫(防遞迴)"
    if os.environ.get(TEST_ENV) == "1":
        return "串測中"
    if os.environ.get("CI", "").lower() == "true":
        return "CI"
    if args[:1] in (["--selftest"], ["selftest"]):
        return "自測"
    return ""


def auto_monitor(args: list, launcher=None) -> str:
    """不擋、不拋、不寫 stdout;回一行狀態(也寫 stderr)。"""
    why = auto_skip(args)
    if why:
        return "skip:" + why
    tail = panorama_tail()
    if tail is None:
        return "skip:VIA_Panorama 不在"
    argv = [sys.executable, str(tail), "autostart", "--from", " ".join(args[:2]) or "(無動詞)"]
    try:
        if launcher is not None:
            rc, out = launcher(argv)
        elif VIA_ACCEL is not None and hasattr(VIA_ACCEL, "run_fast"):
            rc, out = VIA_ACCEL.run_fast(argv, timeout=20)
        else:
            p = subprocess.run(argv, capture_output=True, timeout=20, stdin=subprocess.DEVNULL)
            rc, out = p.returncode, (p.stdout + p.stderr).decode("utf-8", "replace")
    except Exception as e:  # 監控起不來不影響 VCGC 本身的結果
        rc, out = "ERR", f"{type(e).__name__}: {e}"
    line = next((ln for ln in str(out).splitlines() if ln.startswith("[監控]")), f"[監控] rc {rc} · {str(out).strip()[:120]}")
    print(line, file=sys.stderr)
    return line


# ---------------------------------------------------------------- main
def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        if args[:1] == ["monitor"]:
            if os.environ.get("VIA_FROM_VCGC") != "YES":
                print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
                return 2
            return monitor(args[1:])
        return PRIOR.main(args)
    finally:
        auto_monitor(args)


# ---------------------------------------------------------------- selftest
def selftest():
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    import contextlib
    import io
    keep = {k: os.environ.get(k) for k in ("VIA_FROM_VCGC", AUTO_ENV, ACTIVE_ENV, TEST_ENV, "CI")}
    seen, calls = [], []
    real_main, real_auto = PRIOR.main, globals()["auto_monitor"]
    PRIOR.main = lambda a: seen.append(list(a)) or 0
    globals()["auto_monitor"] = lambda a, launcher=None: calls.append(list(a)) or "stub"
    try:
        for k in keep:
            os.environ.pop(k, None)
        os.environ["VIA_FROM_VCGC"] = "YES"
        rc = main(["monitor", "lessons"])
        rc2 = main(["panorama"])  # 既有動詞:原樣轉交前版
        os.environ.pop("VIA_FROM_VCGC", None)
        denied = main(["monitor"])
    finally:
        PRIOR.main = real_main
        globals()["auto_monitor"] = real_auto
    chk("① monitor 走 run VIA_Panorama 尾版;不經 VCGC 拒跑;既有 panorama 動詞原樣轉交前版(不蓋)",
        rc == 0 and seen[0] == ["run", "--family", "core", PANORAMA_FAMILY, "lessons"] and seen[1] == ["panorama"] and denied == 2, seen)
    chk("② 每個 VCGC 動作收尾都觸發監控(含被拒的那次)", calls == [["monitor", "lessons"], ["panorama"], ["monitor"]] and rc2 == 0, calls)
    fired = []

    def fake(argv):
        fired.append(argv)
        return 0, "[監控] 已在背景起全景監控 pid 1 · 頁 x\n"
    err, outb = io.StringIO(), io.StringIO()
    with contextlib.redirect_stderr(err), contextlib.redirect_stdout(outb):
        line = auto_monitor(["sync-check"], launcher=fake)
    chk("② 觸發帶動詞 · 呼叫尾版 autostart · 提示只寫 stderr(stdout 乾淨,JSON 動詞不受影響)",
        fired and fired[0][2:] == ["autostart", "--from", "sync-check"] and line.startswith("[監控]") and outb.getvalue() == ""
        and "[監控]" in err.getvalue(), fired)
    skips = []
    for k, v in ((AUTO_ENV, "0"), (ACTIVE_ENV, "1"), (TEST_ENV, "1"), ("CI", "true")):
        os.environ[k] = v
        skips.append(auto_monitor(["status"], launcher=fake).startswith("skip:"))
        os.environ.pop(k, None)
    skips.append(auto_monitor(["--selftest"], launcher=fake).startswith("skip:"))
    chk("② 不觸發:AUTO=0 · 監控自己(防遞迴)· 串測中 · CI · 自測", all(skips) and len(fired) == 1, skips)

    def boom(argv):
        raise RuntimeError("x")
    with contextlib.redirect_stderr(io.StringIO()):
        safe = auto_monitor(["status"], launcher=boom)
    chk("② 監控起不來不拋、不影響 VCGC 結果", safe.startswith("[監控]"), safe)
    tail = panorama_tail()
    chk("② VIA_Panorama 尾版在且有 autostart", tail is not None and "def autostart" in tail.read_text(encoding="utf-8"), tail)
    card = help_catalog()
    chk("③ help 目前生效入口 = 本版 · 多一行 monitor", card.get("entry") == Path(__file__).name and "monitor" in card
        and card.get("previous") == PRIOR_PATH.name, card.get("entry"))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("加速器:ACCEL 橋 · NET 橋 · 觸發走 VIA_ACCEL.run_fast", "[VIA:ACCEL-BRIDGE" in src and "[VIA:NET-BRIDGE" in src
        and "VIA_ACCEL.run_fast(argv, timeout=20)" in src)
    for k, v in keep.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    print(f"  VCGC v0181 selftest {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    if not all(ok):
        return 1
    _patch_help(False)  # 前版自測核的是「help 接在 v0180」:暫時還原,跑完再接回本版
    try:
        return PRIOR.selftest()
    finally:
        _patch_help(True)


if __name__ == "__main__":
    if sys.argv[1:2] == ["--selftest"]:
        raise SystemExit(selftest())
    raise SystemExit(main())
