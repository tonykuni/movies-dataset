#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL183_CeleritasPolicyGate v0104 — 薄尾:supportive modules/intake 收容件 .ps1 = 凍結收容(INFO),不算基線外新缺

2026-10-05 main 收進 VIA_AzureFlow_QA_v0120(fac6c243)。它的 5 支 .ps1 跟 v0110 那份同名同職,
基線資料檔把 v0110 那份記在 ps1_debt.intake_20260928(「收容件(L03),不是債也不是新產出」)。
v0103 的 scan 只認基線上具名的那幾支,所以每收一版新收容就假紅一次(⑭ 實樹 · 新缺 5)。
收容件依 L03 凍結不改(CLAUDE.md:凍結來源不改),也就是永遠不會帶章 —— 算它紅等於要人去改凍結件。

本尾版只換一件事:基線外新缺裡路徑在 supportive modules/intake/ 下的,移到 ps.intake(INFO 照列,不消失)。
  · 其餘(活檔沒章 · 版史規則 · 已還債棘輪 · 唯讀本 · PS 稽核委派引擎)全照 v0103(L04 舊版一字不動)
  · 基線資料檔 VIA_CeleritasPolicy_Baseline_v0100.json 一個字都不改(批709:基線在資料檔,不在碼)
  · 負控:收容夾外同名檔、或只是路徑中含 intake 字樣的活檔,照紅
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
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL183_CeleritasPolicyGate"
PRIOR_PATH = [p for p in sorted(HERE.glob(_STEM + "_v*.py")) if p.name < Path(__file__).name][-1]
_spec = importlib.util.spec_from_file_location("cgc_mdl183_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V0101 = PRIOR.V0101
VERSION = "v" + Path(__file__).stem.rsplit("_v", 1)[-1]
PS_MARK = PRIOR.PS_MARK
_SCAN_V0103 = PRIOR.scan
INTAKE_PREFIX = "supportive modules/intake/"


def __getattr__(name):
    return getattr(PRIOR, name)


def is_intake(rel: str) -> bool:
    """路徑前綴就是 supportive modules/intake/(L03 收容正本);只是含 intake 字樣不算。"""
    return str(rel).replace("\\", "/").startswith(INTAKE_PREFIX)


def scan(root: Path | None = None) -> dict:
    """同 v0103 掃描;基線外新缺裡 supportive modules/intake/ 下的 .ps1 → ps.intake(INFO),其餘照紅。"""
    s = _SCAN_V0103(root)
    ps = s.get("ps")
    if not isinstance(ps, dict):
        return s
    nm = ps.get("new_missing") or []
    ps["intake"] = sorted(set(ps.get("intake") or []) | {r for r in nm if is_intake(r)})
    ps["new_missing"] = [r for r in nm if not is_intake(r)]
    ps["state"] = "GREEN" if not ps["new_missing"] else "RED"
    py = s.get("py") or {}
    s["state"] = "GREEN" if ps["state"] == "GREEN" and py.get("state") == "GREEN" else "RED"
    return s


def _install_v0104() -> None:
    V0101.scan = scan            # v0101 的 report 讀模組層 scan
    PRIOR.PRIOR.scan = scan      # v0102
    PRIOR.scan = scan            # v0103 的 selftest ⑬⑭⑯ 與 ⑮ 都改量本版(同一把尺)


_install_v0104()
report = V0101.report


def selftest() -> int:
    rc = PRIOR.selftest()        # v0101 八檢 + v0102 + v0103 加檢照跑(實樹 ⑭ 以本版規則量)
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' (' + note + ')') if note else ''}")

    print(f"=== {_STEM} {VERSION} 薄尾加檢(收容件 .ps1 = 凍結收容 INFO)===")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        qa = root / "supportive modules" / "intake" / "QA_v9999"
        qa.mkdir(parents=True)
        (qa / "Invoke-QA.ps1").write_text("Write-Host 1\n", encoding="utf-8")
        live = root / "x" / "intake_tools"
        live.mkdir(parents=True)
        (live / "Invoke-QA.ps1").write_text("Write-Host 2\n", encoding="utf-8")
        s = scan(root)
        ps = s.get("ps") or {}
        chk("⑰ 收容夾 .ps1 → ps.intake(INFO 照列);收容夾外同名 · 路徑只含 intake 字樣的活檔照紅(負控)",
            s.get("state") != "NODATA"
            and ps.get("intake") == ["supportive modules/intake/QA_v9999/Invoke-QA.ps1"]
            and ps.get("new_missing") == ["x/intake_tools/Invoke-QA.ps1"] and ps.get("state") == "RED",
            f"intake {ps.get('intake')} · 新缺 {ps.get('new_missing')}")
    real = scan()
    rps = real.get("ps") or {}
    chk("⑱ 實樹:基線外新缺 0;收容件照列不消失",
        not rps.get("new_missing") and isinstance(rps.get("intake"), list),
        f"新缺 {rps.get('new_missing')} · 收容 {len(rps.get('intake') or [])}")
    chk("⑲ report 與各層 scan 同一把尺", V0101.scan is scan and PRIOR.scan is scan and PRIOR.PRIOR.scan is scan)
    ok = rc == 0 and all(results)
    print(f"  [計] {_STEM} {VERSION} 本版 {sum(results)}/{len(results)} · 前版 {'PASS' if rc == 0 else 'FAIL'} · 合計 {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    print(f"=== Celeritas 產出契約閘 {VERSION}(薄尾 · 收容件 .ps1 = 凍結收容 INFO · 執法 L102)===")
    return report()


if __name__ == "__main__":
    raise SystemExit(main())
