#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC v0197 — 薄尾:掃描面只增一條具名排除「收容夾 /intake_」—— 收容副本不得冒充活樹尾版。

操作員 2026-11-13 裁定(選 a):「選 a 主控台出新版排除收容夾」。
實錄:claude/practical-pasteur 分支把上傳的主控台收容版放在 docs/handoff/ai/intake_20261110_vcgc_multimatrix/v0195/
(WorkbenchLocal v0104.ps1 寫死該路徑,.ps1 AI 不改 · L70;收容正本零觸碰 · L03)。本體 v0142 的 SCAN_EXCLUDE 只排 references/,
掃描面「全樹 − 具名排除」照檔名取最大版號 → 收容的 v0195 把 registry 的活樹主控台 v0192 擠掉:registry-sync 乾跑
「退役 378」幾乎全是主控台元件(把收容副本登成現役主控台)。本版只做一件:沿前版鏈找到自己定義 SCAN_EXCLUDE 的模組,
只增一條 ("/intake_", 因由) 並清它的 _TAIL_CACHE。條文照本體 ㉜ 的規矩:有因由 · 不准吃到下限(批699 九式)裡的檔。

版號說明(L25 多 AI 交會):v0193–v0196 已由並行分支 claude/optimistic-goodall-yhalc5 使用(不同內容),本版跳號取 v0197,
不與之同號。本分支 glob 前版 = v0192;兩支合併後 glob 前版 = 那條的 v0196,本版疊在其上,鏈不斷、排除照樣生效。
其餘動詞一字不改,照 v0192 → PRIOR 鏈。VIA_FROM_VCGC=YES 才放行(同前版)。零網路;不碰 TA-Lib;不代設同意閘。
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

import contextlib

import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL149_VeritasCentralGovernanceConsole"


def _vnum(p) -> int:
    m = re.search(r"_v(\d+)\.(?:py|html)$", str(p))
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_v0197", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)          # 本分支 v0192;合併後為 v0196
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)

INTAKE_EXCLUDE = ("/intake_",
                  "收容夾(docs/handoff/ai/intake_* 等原樣收容的上傳 / 他分支副本):收容正本零觸碰(L03),"
                  "同名高版號的收容副本不得冒充活樹尾版(2026-11-13 實錄:收容版主控台 v0195 擠掉 registry 的 v0192,"
                  "registry-sync 乾跑誤退役 378 元件)")


def __getattr__(name):
    return getattr(PRIOR, name)


def scan_owners() -> list:
    """自己定義 SCAN_EXCLUDE 的模組(本體 v0142;另掃已載入的同族模組,防鏈上換手)。"""
    out, seen, m = [], set(), PRIOR
    while m is not None and id(m) not in seen:
        seen.add(id(m))
        if "SCAN_EXCLUDE" in vars(m):
            out.append(m)
        m = vars(m).get("PRIOR")
    for mod in list(sys.modules.values()):
        f = str(getattr(mod, "__file__", "") or "")
        if _STEM in f and "SCAN_EXCLUDE" in vars(mod) and all(mod is not o for o in out):
            out.append(mod)
    return out


def install(on: bool = True) -> int:
    """只增一條排除(on)或拿掉本版這一條(off,只給自測對照用);每次都清尾版快取。回處理的模組數。"""
    n = 0
    for m in scan_owners():
        lst = vars(m)["SCAN_EXCLUDE"]
        has = any(f == INTAKE_EXCLUDE[0] for f, _ in lst)
        if on and not has:
            lst.append(INTAKE_EXCLUDE)
        elif not on and has:
            lst[:] = [x for x in lst if x[0] != INTAKE_EXCLUDE[0]]
        cache = vars(m).get("_TAIL_CACHE")
        if isinstance(cache, dict):
            cache.clear()
        n += 1
    return n


install(True)


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    rc = PRIOR.main(argv)
    if args[:1] == ["help"]:
        print("  [v0197] 掃描面排除收容夾 /intake_(收容副本不冒充活樹尾版;registry-sync · live_components · scan_face 同一份清單)")
    return rc


def selftest() -> int:
    keep_file = PRIOR.__dict__.get("__file__")
    PRIOR.__dict__["__file__"] = str(Path(__file__).resolve())      # 前版鏈「尾版 = 自己」的檢查指向目前生效入口(本檔)
    try:
        prior_rc = PRIOR.selftest()
    finally:
        PRIOR.__dict__["__file__"] = keep_file
    print("=== VCGC v0197 · 薄尾自測(掃描面排除收容夾 /intake_)===")
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    chk("① 前版鏈自測過(v0192 → … ;合併後 v0196 → …)", prior_rc == 0, f"rc {prior_rc}")
    install(True)                                     # 前版自測途中另載的同族模組(例:TA-Lib 禁用檢查的副本)也補上本條(冪等)
    owners = scan_owners()
    entries = [sum(1 for f, _ in vars(m)["SCAN_EXCLUDE"] if f == INTAKE_EXCLUDE[0]) for m in owners]
    chk("② 找到定義 SCAN_EXCLUDE 的模組 · 本條各只出現一次 · 因由不空", owners and all(n == 1 for n in entries) and INTAKE_EXCLUDE[1].strip(),
        f"{len(owners)} 支 · {[getattr(m, '__name__', '?')[-24:] for m in owners]}")
    body = owners[0] if owners else None
    if body is not None:
        why = body._excuse("docs/handoff/ai/intake_20261110_vcgc_multimatrix/v0195/" + _STEM + "_v0195.py")
        live = body._excuse("supportive modules/registry/" + _STEM + "_v0197.py")
        chk("③ 收容夾路徑被本條吃掉、registry 的主控台不被吃", why == INTAKE_EXCLUDE[1] and live == "", (why[:20], live))
        without = [x for x in body.SCAN_EXCLUDE if x[0] != INTAKE_EXCLUDE[0]]
        old = body._tail_files(without).get(_STEM)
        new = body._tail_files().get(_STEM)
        rel_new = new.relative_to(body.VIA).as_posix() if new else ""
        chk("④ 真樹:主控台家族的尾版 = registry 那支(不是收容副本);沒有本條時會被收容版擠掉(若樹上有收容副本)",
            rel_new.startswith("supportive modules/registry/") and (old is None or "/intake_" in old.as_posix() or old == new),
            f"現 {rel_new} · 無本條時 {old.relative_to(body.VIA).as_posix() if old else '—'}")
        floor = set(body._floor_files())
        lost = sorted(floor - set(body._tail_files()))
        lost_before = sorted(floor - set(body._tail_files(without)))
        face = body.scan_face()
        chk("⑤ 照本體 ㉛ ㉜:本條**不新增**任何下限(批699 九式)缺口 · 每條排除都有因由 · 本條吃掉幾支照實印",
            lost == lost_before and not face["no_why"],
            f"本條新增缺口 {sorted(set(lost) - set(lost_before)) or '無'} · 既有缺口(非本條)"
            f" {lost_before or '無'} · 本條吃 {face['eaten'].get(INTAKE_EXCLUDE[0])} 支 · 治理 {face['families']} 家族")
    else:
        chk("③ 本體可用", False, "找不到定義 SCAN_EXCLUDE 的模組")
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 只有單獨 --selftest 跑中央自測:run X --selftest 照路由給 X",
        bool(re.search(r'^\s+sys\.exit\(selftest\(\) if sys\.argv\[1:\] == \["--selftest"\] else main\(\)\)', src, re.M)))
    chk("⑦ 加速器橋在 · 只收 VCGC(VIA_FROM_VCGC)· 本檔零網路 · 不碰 TA-Lib",
        "[VIA:ACCEL-BRIDGE" in src and "VIA_FROM_VCGC" in src
        and not re.search(r"^\s*(import|from)\s+(urllib|requests|http\.client|socket|talib)\b", src, re.M))
    print(f"  [計] VCGC v0197 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(selftest() if sys.argv[1:] == ["--selftest"] else main())    # 只有單獨 --selftest 跑中央自測;run X --selftest 照路由給 X(v0176 起的規矩)
