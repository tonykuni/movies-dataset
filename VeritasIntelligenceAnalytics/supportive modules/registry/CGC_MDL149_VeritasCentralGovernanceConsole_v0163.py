#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL149_VeritasCentralGovernanceConsole v0163 — VCGC 中央治理主控台(資料庫中央管控 dbm 路由)

v0162→v0163(側線 2026-09-28;操作員令「VIA_DBManager 放在中央管控系統 VCGC,由它統一處理輸出」;L20 所有庫的唯一接觸口):
  `dbm …` 交給 CGC_MDL228 VIADBManager 尾版(overview / reconcile / plan / export),其餘參數一律原樣給 v0162。
  與 v0162 同規矩:只收 VCGC 呼叫(VIA_FROM_VCGC=YES),否則 DENY。v0162 留作版史(L04)。
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
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE / "CGC_MDL149_VeritasCentralGovernanceConsole_v0162.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


prev = _load(PREVIOUS, "vcgc_v0162_for_v0163")


def __getattr__(name: str):
    return getattr(prev, name)


def def_dbmanager():
    """資料庫中央管控尾版(CGC_MDL228_VIADBManager_v*.py,取最新)。不在 = None(照實)。"""
    hits = sorted(HERE.glob("CGC_MDL228_VIADBManager_v*.py"))
    return _load(hits[-1], "vcgc_dbmanager_tail") if hits else None


def _is_dbm(args) -> bool:
    return bool(args) and args[0] == "dbm"


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if _is_dbm(args):
        if os.environ.get("VIA_FROM_VCGC") != "YES":
            print('{"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}')
            return 2
        dbm = def_dbmanager()
        if dbm is None:
            print('{"via": "vcgc", "state": "ABSENT", "why": "CGC_MDL228_VIADBManager 尾版不在"}')
            return 2
        return dbm.main(args[1:] or ["overview"])
    return prev.main(argv)


def selftest() -> int:
    routed = _is_dbm(["dbm", "overview"]) and not _is_dbm(["status"]) and not _is_dbm(["layout", "--selftest"]) and not _is_dbm([])
    dbm = def_dbmanager()
    tail_ok = dbm is not None and callable(getattr(dbm, "main", None)) and Path(dbm.__file__).name.startswith("CGC_MDL228_VIADBManager_v")
    print(f"  [{'OK' if routed else 'FAIL'}] dbm 走資料庫中央管控,其餘參數照舊給 v0162")
    print(f"  [{'OK' if tail_ok else 'FAIL'}] 資料庫中央管控尾版 {Path(dbm.__file__).name if dbm else '不在'}")
    if not (routed and tail_ok):
        return 1
    return prev.selftest()


if __name__ == "__main__":
    args = sys.argv[1:]
    raise SystemExit(selftest() if args == ["--selftest"] else main())
