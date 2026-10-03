#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL124_BridgeSweeper v0110 — 薄尾:PS 版史判準照版號、不照檔名字典序

工具覆蓋矩陣(CGC_MDL230)與本器都把 `Invoke-VIA-Step1-SyncAndLKGC.ps1`(無版號舊檔)當 PS 尾版報缺 / 計畫注橋;
真正的尾版是同夾的 `Invoke-VIA-Step1-SyncAndLKGC-v0101.ps1`(橋與模板章都在)。病根:v0106 起 `_ps_history` 用
`sorted(檔名)[-1]` 當尾版,`.ps1` 的 `.`(0x2E)排在 `-v0101` 的 `-`(0x2D)後面 → 無版號舊檔贏了。照 `--apply` 會把橋寫進
舊 .ps1(違 L70:不改既有 .ps1)。本版只換 `_ps_history`:同族照版號比大小(無版號 = -1),其餘一字照 v0109。
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
STEM = "CGC_MDL124_BridgeSweeper"


def _vnum_v0110(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum_v0110(p) < _vnum_v0110(__file__)), key=_vnum_v0110)
_spec = importlib.util.spec_from_file_location(STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
for _n, _v in vars(PRIOR).items():
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = _v
_PS_VNUM_V0110 = re.compile(r"[-_]v(\d{4})(?=\.ps1$)")


def ps_version_v0110(name: str) -> int:
    m = _PS_VNUM_V0110.search(name)
    return int(m.group(1)) if m else -1


def _ps_history(rows: list) -> set:
    """同族非尾版 = 版史。族 = 檔名去 -vNNNN / _vNNNN;尾版 = 同族**版號最大**者(無版號 = -1);只在 HAS / MISSING 之間比。"""
    fams: dict = {}
    for r in rows:
        if r["state"] not in ("HAS", "MISSING"):
            continue
        fams.setdefault(PRIOR._PS_VER.sub("", r["file"]), []).append(r["file"])
    hist = set()
    for fs in fams.values():
        if len(fs) > 1:
            fs = sorted(fs, key=lambda f: (ps_version_v0110(f), f))
            hist.update(fs[:-1])
    return hist


PRIOR._ps_history = _ps_history


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return PRIOR.main()


def selftest() -> int:
    rc0 = PRIOR.selftest()
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print("=== CGC_MDL124_BridgeSweeper v0110 · 薄尾自測(PS 版史照版號)===")
    chk("① v0109 自測過", rc0 == 0, f"rc {rc0}")
    rows = [{"file": "Invoke-A.ps1", "state": "MISSING"}, {"file": "Invoke-A-v0101.ps1", "state": "HAS"},
            {"file": "B-v0100.ps1", "state": "HAS"}, {"file": "B-v0102.ps1", "state": "MISSING"}, {"file": "C.ps1", "state": "MISSING"}]
    chk("② 無版號舊檔 + 同族 -v0101 → 無版號是版史(不是尾版);B 照版號 v0102 是尾版;單支 C 自己是尾",
        _ps_history(rows) == {"Invoke-A.ps1", "B-v0100.ps1"}, sorted(_ps_history(rows)))
    real = [r for r in PRIOR.scan_ps(".") if "Invoke-VIA-Step1-SyncAndLKGC" in r["file"]]
    chk("③ 真樹:Invoke-VIA-Step1-SyncAndLKGC.ps1 判版史、-v0101 是尾版(不再計畫注橋進舊 .ps1)",
        len(real) == 2 and _ps_history(real) == {"Invoke-VIA-Step1-SyncAndLKGC.ps1"}, [r["file"] for r in real])
    chk("④ 前版全域已換成本版(run_ps 走的就是這一支)", PRIOR._ps_history is _ps_history)
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑤ 加速器橋在;不碰 TA-Lib", "[VIA:ACCEL-BRIDGE" in text and not re.search(r"^\s*(import|from)\s+talib", text, re.M))
    print(f"  [計] CGC_MDL124_BridgeSweeper v0110 本版 {sum(ok)}/{len(ok)} · v0109 {'PASS' if rc0 == 0 else 'FAIL'} · 合計 {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
