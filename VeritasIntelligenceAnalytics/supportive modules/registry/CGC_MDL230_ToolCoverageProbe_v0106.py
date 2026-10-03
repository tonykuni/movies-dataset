#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL230_ToolCoverageProbe v0106 — 薄尾:無版號舊 PS 檔有同族版號檔時算版史(不算尾版)

工具覆蓋矩陣 ④「PS 加速器模組橋(尾版)」RED 712/713,唯一缺的是 `Invoke-VIA-Step1-SyncAndLKGC.ps1`——它是無版號舊檔,
同夾已有帶橋與模板章的 `Invoke-VIA-Step1-SyncAndLKGC-v0101.ps1`。冊上律(ps_tail_why)「無版號 = 自己就是尾」只在
**沒有同族版號檔**時成立。本版只換 `_ps_tails`:先照 v0105(虛擬環境夾不掃),再把「同夾同名有 -vNNNN / _vNNNN 版」的
無版號檔移到版史。其餘(六面矩陣 · AST 目錄 · 只增帳本 · 預設開頁)照 v0105。
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
STEM = "CGC_MDL230_ToolCoverageProbe"


def _vnum(path: Path) -> int:
    match = re.search(r"_v(\d+)$", path.stem)
    return int(match.group(1)) if match else -1


PRIOR = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_v{_vnum(Path(__file__)):04d}", PRIOR)
_PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _PRIOR
_spec.loader.exec_module(_PRIOR)
for _name, _value in vars(_PRIOR).items():
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = _value
ENGINE_TAG = f"{STEM} v{_vnum(Path(__file__)):04d}"


def __getattr__(name: str):
    return getattr(_PRIOR, name)


def _chain_modules() -> list:
    out, m = [], _PRIOR
    while m is not None and m not in out:
        out.append(m)
        m = getattr(m, "_PRIOR", None)
    return out


_V0105_PS_TAILS = _PRIOR.__dict__["_ps_tails"]
_VERSIONED = re.compile(r"^(?P<fam>.+?)[-_]v\d{3,4}[A-Z]?\.ps1$")


def _ps_tails(root: Path, exclude: set, fam_rx: str) -> tuple:
    tails, history = _V0105_PS_TAILS(root, exclude, fam_rx)
    versioned = {}
    for p in tails:
        m = _VERSIONED.match(p.name)
        if m:
            versioned.setdefault(str(p.parent), set()).add(m.group("fam"))
    keep = []
    for p in tails:
        if not _VERSIONED.match(p.name) and p.stem in versioned.get(str(p.parent), set()):
            history += 1                                   # 無版號舊檔,同夾同名已有版號檔 → 版史
        else:
            keep.append(p)
    return keep, history


for _m in _chain_modules():
    if "_ps_tails" in _m.__dict__:
        _m._ps_tails = _ps_tails


def selftest() -> int:
    import tempfile
    rc = _PRIOR.selftest()
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        for n in ("Invoke-A.ps1", "Invoke-A-v0101.ps1", "Solo.ps1", "B-v0100.ps1", "B-v0102.ps1"):
            (root / n).write_text("Write-Host x\n", encoding="utf-8")
        tails, hist = _ps_tails(root, set(), r"^(?P<fam>.*?)[-_]v(?P<v>\d{3,4})(?P<s>[A-Z]?)\.ps1$")
        names = sorted(p.name for p in tails)
        chk("㊹ 無版號舊檔 + 同夾 -v0101 → 版史;單支無版號照算尾版;版號族照最大版號",
            names == ["B-v0102.ps1", "Invoke-A-v0101.ps1", "Solo.ps1"] and hist == 2, (names, hist))
    chk("㊺ 前版每一支的 _ps_tails 都換成本版", all(m.__dict__["_ps_tails"] is _ps_tails for m in _chain_modules() if "_ps_tails" in m.__dict__))
    ok = rc == 0 and all(results)
    print(f"  [{ENGINE_TAG} 無版號舊 PS 檔算版史] 自測 {sum(results)}/{len(results)} {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    return _PRIOR.main(a)


if __name__ == "__main__":
    raise SystemExit(main())
