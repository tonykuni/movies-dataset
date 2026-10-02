#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC v0187 — 薄尾:`run` 解析引擎路徑一律轉絕對路徑 · stem 搜尋根加 FlowSystem 引擎夾

R51b(2026-10-02)實錄:`handoff test` 在 VIA 根下跑 `run "supportive modules/…/X_v0101.py"` 時,v0168 的 _tail
看到相對路徑在 cwd 下存在就原樣回傳相對路徑,run_engine 再以 cwd=引擎所在夾起子行程 → 路徑拼兩次、找不到檔(rc 2)。
另外 FlowSystem 引擎(FLOW_ENG0xx)不在 run 的 stem 根,只能給路徑。
本版:
  ① 給檔路徑:cwd 下或 VIA 下存在就回絕對路徑(子行程 cwd 換到引擎夾也不會拼錯)。
  ② stem 找不到時,再到 FlowSystem 引擎夾找(同 v0168 規則:有版號取最大版,沒有才取無版號檔)。
     → 操作員可直接 `via-vcgc run FLOW_ENG023_FlowTwActiveEtf --refresh`。
  修法:替換 v0168 模組上的 _tail(run_engine 讀的是那個模組的全域);其餘照 v0186(VIA_FROM_VCGC=YES 才放行,同前版)。
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
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
_STEM = "CGC_MDL149_VeritasCentralGovernanceConsole"
PRIOR_PATH = max(p for p in HERE.glob(_STEM + "_v*.py") if p.name < Path(__file__).name)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_v0187", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
EXTRA_ROOTS = ("supportive modules/VIA_FlowSystem/FlowSystem_v2/engines",)


def __getattr__(name):
    return getattr(PRIOR, name)


def _run_owner():
    """沿前版鏈找到自己定義 run_engine 的那個模組(v0168)。"""
    m = PRIOR
    while m is not None:
        if "run_engine" in vars(m):
            return m
        m = vars(m).get("PRIOR")
    return None


_OWNER = _run_owner()
_BASE_TAIL = vars(_OWNER)["_tail"] if _OWNER is not None else None


def _tail(stem: str, via: Path = VIA, roots=EXTRA_ROOTS):
    p = Path(stem)
    if p.suffix == ".py":
        for q in (p, via / p):
            if q.is_file():
                return q.resolve()
        return None
    hit = _BASE_TAIL(stem) if _BASE_TAIL is not None and via == VIA else None
    if hit is not None:
        return Path(hit).resolve()
    hits = []
    for r in roots:
        hits += [q for q in (via / r).glob(stem + "_v*.py") if PRIOR._vnum(q) >= 0]
        q = via / r / (stem + ".py")
        if q.is_file() and not hits:
            hits.append(q)
    return max(hits, key=PRIOR._vnum).resolve() if hits else None


if _OWNER is not None:
    vars(_OWNER)["_tail"] = _tail

# ---------------------------------------------------------------- help(同 v0186 的掛法:目前生效入口 = 本版)
RUN_LINE = "run [--family f] <stem 或檔路徑> [參數…]  檔路徑一律轉絕對路徑 · stem 也找 FlowSystem 引擎夾(FLOW_ENG0xx)"
_PREV_CATALOG = PRIOR.help_catalog
_PREV_SHOW = vars(PRIOR).get("_show_help_v0186")
_PATCHED: list = []


def help_catalog():
    card = _PREV_CATALOG()
    card.update(entry=Path(__file__).name, previous=PRIOR_PATH.name, run=RUN_LINE)
    return card


def _show_help_v0187():
    if _PREV_SHOW is not None:
        _PREV_SHOW()
    print("  " + RUN_LINE)


def _chain() -> list:
    mods, m = [], PRIOR
    while m is not None and m not in mods:
        mods.append(m)
        m = vars(m).get("PRIOR")
    return mods


def _patch_help(on: bool = True) -> None:
    if on:
        for _m in _chain():
            if vars(_m).get("help_catalog") is _PREV_CATALOG:
                _m.help_catalog = help_catalog
                _PATCHED.append((_m, "help_catalog", _PREV_CATALOG))
            if _PREV_SHOW is not None and vars(_m).get("show_current_help") is _PREV_SHOW:
                _m.show_current_help = _show_help_v0187
                _PATCHED.append((_m, "show_current_help", _PREV_SHOW))
    else:
        for _m, attr, orig in _PATCHED:
            setattr(_m, attr, orig)
        _PATCHED.clear()


_patch_help(True)


def main(argv=None):
    return PRIOR.main(argv)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print("=== VCGC v0187 · 薄尾自測(run 路徑解析)===")
    chk("① 找到 run_engine 的正主並換上新 _tail", _OWNER is not None and vars(_OWNER).get("_tail") is _tail,
        getattr(_OWNER, "__name__", None))
    with tempfile.TemporaryDirectory() as td:
        via = Path(td)
        eng = via / EXTRA_ROOTS[0]
        eng.mkdir(parents=True)
        (eng / "FLOW_X.py").write_text("", encoding="utf-8")
        chk("② stem 只有無版號檔 → 取它", _tail("FLOW_X", via) == (eng / "FLOW_X.py").resolve())
        (eng / "FLOW_X_v0101.py").write_text("", encoding="utf-8")
        (eng / "FLOW_X_v0102.py").write_text("", encoding="utf-8")
        chk("③ 有版號 → 取最大版", _tail("FLOW_X", via) == (eng / "FLOW_X_v0102.py").resolve())
        rel = EXTRA_ROOTS[0] + "/FLOW_X_v0101.py"
        here = os.getcwd()
        try:
            os.chdir(via)
            r = _tail(rel, via)
        finally:
            os.chdir(here)
        chk("④ 相對路徑在 cwd 下存在 → 回絕對路徑(R51b 拼兩次的根因)", r is not None and r.is_absolute() and r.is_file(), r)
        chk("⑤ 相對 VIA 的路徑(cwd 不在 VIA)→ 絕對路徑", _tail(rel, via) == (eng / "FLOW_X_v0101.py").resolve())
        chk("⑥ 不存在的檔 / stem → None", _tail("nope/NO_SUCH.py", via) is None and _tail("NO_SUCH_STEM", via) is None)
    real = _tail("CGC_MDL149_VeritasCentralGovernanceConsole")
    chk("⑦ 真樹:VCGC 自己的 stem 仍走 v0168 規則取尾版", real is not None and real.name == Path(__file__).name, real and real.name)
    flow = _tail("FLOW_ENG023_FlowTwActiveEtf")
    chk("⑧ 真樹:FLOW_ENG023 經 stem 找得到(FlowSystem 夾)", flow is not None and flow.parent.name == "engines", flow and flow.name)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑨ 加速器橋在;前版檔不動(本版只是薄尾)", "VIA:ACCEL-BRIDGE" in src and PRIOR_PATH.is_file())
    card = help_catalog()
    chk("⑩ help 目前生效入口 = 本版 · 前版 = v0186 · 多 run 說明", card.get("entry") == Path(__file__).name
        and card.get("previous") == PRIOR_PATH.name and "run" in card, (card.get("entry"), card.get("previous")))
    good = all(ok)
    print(f"  [計] VCGC v0187 薄尾 {sum(ok)}/{len(ok)} · {'PASS' if good else 'FAIL'}")
    if not good:
        return 1
    _patch_help(False)
    try:
        return PRIOR.selftest()
    finally:
        _patch_help(True)


if __name__ == "__main__":
    raise SystemExit(selftest() if sys.argv[1:] == ["--selftest"] else main())
