#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL230_ToolCoverageProbe v0105 — 薄尾:PS 尾版掃描不收 Python 虛擬環境夾(含 pyvenv.cfg 的夾)

工作站交接 WS_HANDOVER_20261002_080732(R50 監控):④ PS 加速器模組橋 RED 155/156,唯一缺的是
functional modules/WorkOps/engines/.venv_pm/Scripts/Activate.ps1 —— 這是 python -m venv 產的啟動檔(本機產物、git 不載、
不是倉內程式),第 3 次重複出錯(CGC_MDL058 帳)。v0102 / v0103 的 _ps_tails 只照夾名排除(CGC_MDL117 EXCLUDE_DIRS),
夾名千變(.venv · .venv_pm · venv312 …)排不完 → 改照內容認:夾裡有 pyvenv.cfg 就是虛擬環境,整夾不掃(全部版本一起換掉)。
其餘照 v0104(預設開頁 · 六面矩陣 · AST 目錄 · 只增帳本)。

用法:
  python CGC_MDL230_ToolCoverageProbe_v0105.py matrix [--no-open] [--ledger] [--json] [--baseline <json>] [--no-pwsh]
  python CGC_MDL230_ToolCoverageProbe_v0105.py --selftest
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
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "CGC_MDL230_ToolCoverageProbe"


def _vnum(path: Path) -> int:
    match = re.search(r"_v(\d+)$", path.stem)
    return int(match.group(1)) if match else -1


def _prior() -> Path:
    mine = _vnum(Path(__file__))
    older = [p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < mine]
    if not older:
        raise ImportError(f"{STEM}: no version below v{mine:04d}")
    return max(older, key=_vnum)


PRIOR = _prior()
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
    """本支往前的模組鏈(v0104 → v0103 → v0102 …):每支自己的全域都要換到新 _ps_tails。"""
    out, m = [], _PRIOR
    while m is not None and m not in out:
        out.append(m)
        m = getattr(m, "_PRIOR", None)
    return out


_BASE_PS_TAILS = next((m.__dict__["_ps_tails"] for m in _chain_modules() if "_ps_tails" in m.__dict__), None)


def venv_dirs(root: Path, exclude: set) -> set:
    """root 底下的 Python 虛擬環境夾名(夾裡有 pyvenv.cfg);照 exclude 先剪枝。"""
    names = set()
    for r, dirs, _files in os.walk(root):
        keep = []
        for d in dirs:
            if d in exclude:
                continue
            if (Path(r) / d / "pyvenv.cfg").is_file():
                names.add(d)
                continue
            keep.append(d)
        dirs[:] = keep
    return names


def _ps_tails(root: Path, exclude: set, fam_rx: str) -> tuple:
    return _BASE_PS_TAILS(root, set(exclude) | venv_dirs(Path(root), set(exclude)), fam_rx)


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
        (root / "Run-A-v0100.ps1").write_text("Write-Host a\n", encoding="utf-8")
        venv = root / "functional modules" / "WorkOps" / "engines" / ".venv_pm"
        (venv / "Scripts").mkdir(parents=True)
        (venv / "pyvenv.cfg").write_text("home = C:/Python312\n", encoding="utf-8")
        (venv / "Scripts" / "Activate.ps1").write_text("# venv\n", encoding="utf-8")
        plain = root / "functional modules" / "WorkOps" / "venv_named_but_code"
        plain.mkdir(parents=True)
        (plain / "Run-B-v0100.ps1").write_text("Write-Host b\n", encoding="utf-8")
        tails, _hist = _ps_tails(root, set(), r"^(?P<fam>.+)-v(?P<v>\d{4})(?P<s>[A-Z]?)\.ps1$")
        names = sorted(p.name for p in tails)
        chk("㊶ 有 pyvenv.cfg 的夾(.venv_pm)整夾不掃:Activate.ps1 不算 PS 尾版", "Activate.ps1" not in names, names)
        chk("㊷ 夾名像 venv 但沒有 pyvenv.cfg = 倉內程式照掃", "Run-B-v0100.ps1" in names and "Run-A-v0100.ps1" in names, names)
    chk("㊸ 前版每一支的 _ps_tails 都換成本版(matrix 走哪一支都一樣)",
        all(m.__dict__["_ps_tails"] is _ps_tails for m in _chain_modules() if "_ps_tails" in m.__dict__))
    ok = rc == 0 and all(results)
    print(f"  [{ENGINE_TAG} 虛擬環境夾不算 PS 尾版] 自測 {sum(results)}/{len(results)} {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    return _PRIOR.main(a)


if __name__ == "__main__":
    raise SystemExit(main())
