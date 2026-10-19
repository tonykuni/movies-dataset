#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG045_OutputHub v0102 — 薄尾:自測改寫進**私有暫存夾**(多支同時自測不再互撞)

操作員令(2026-10-19):「繼續 跑完貼回結果 對於記憶體跟TEMP支援方式用最快最佳的方法 自動完成」。
容器全流程真跑(ActivateVDF v0107):引擎啟動 94/94 可啟動,自測 RED 2 —— 其中 ENG045 6/7。
查因:v0101 自測固定寫 VIA_Reports/vdfout_runs/selftest_out(共用夾;每次先把舊檔改名 .bak 再寫,已累積 150 支 .bak)。
  同一秒有兩支自測(全流程的引擎啟動 + 另一支同時跑的自測)→ 一支把另一支剛寫的檔改名 / DuckDB 檔被占 → parquet / duckdb 往返 FAIL。
  容器重現:四支同時跑,三輪各 2 支 FAIL(parquet 往返 / duckdb 表往返);單跑永遠 7/7。
本版:自測把前版的 EV 暫換成本次私有暫存夾(TMP / TEMP 底下 · 跑完刪)再跑前版七檢 → 共用夾一字不動、不再生 .bak、併跑不互撞。
  真跑(rows JSON → 全格式落地)完全照 v0101(輸出夾 · 帳都不變)。VDF 自己的模組:不匯入他系統程式;不碰 TA-Lib;同意閘不讀不寫。
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
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
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG045_OutputHub"
TAG = "v0102"


def _vnum_v0102(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0102(p) < _vnum_v0102(__file__)), key=_vnum_v0102)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


load_params, write_all, summary = PRIOR.load_params, PRIOR.write_all, PRIOR.summary
PARAMS, OUT_ROOT, EV = PRIOR.PARAMS, PRIOR.OUT_ROOT, PRIOR.EV


def prior_selftest_private() -> int:
    """前版七檢,但寫進本次私有暫存夾(共用的 vdfout_runs/selftest_out 一字不動);跑完刪夾。"""
    tmp = Path(tempfile.mkdtemp(prefix="vdf_eng045_selftest_"))
    keep = PRIOR.EV
    PRIOR.EV = tmp
    try:
        return PRIOR.selftest()
    finally:
        PRIOR.EV = keep
        shutil.rmtree(tmp, ignore_errors=True)


def _listing(d: Path) -> list:
    return sorted((p.name, p.stat().st_mtime_ns) for p in d.iterdir()) if d.is_dir() else []


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {_STEM} {TAG} · 薄尾自測(私有暫存夾 · 併跑不互撞)===")
    shared = PRIOR.EV / "selftest_out"
    before = _listing(shared)
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        rc_once = prior_selftest_private()
    chk("① 自測只寫本次私有暫存夾:前版七檢照過,共用的 vdfout_runs/selftest_out 一字不動(不再生 .bak)",
        rc_once in (0, 3) and _listing(shared) == before, {"rc": rc_once, "共用夾檔數": len(before)})
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    procs = [subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--selftest-private"], env=env,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
             for _ in range(4)]
    rcs = [p.wait(timeout=300) for p in procs]
    outs = [p.stdout.read() for p in procs]
    chk("② 四支同時自測全過(v0101 在容器四支併跑三輪各 2 支 FAIL:parquet / duckdb 往返互撞)",
        all(rc in (0, 3) for rc in rcs) and all("[FAIL]" not in o for o in outs), rcs)
    src = Path(__file__).read_text(encoding="utf-8")
    imports = re.findall(r"^\s*(?:import|from)\s+([A-Za-z_][\w.]*)", src, re.M)
    chk("③ 加速器橋 · 網路橋在;不匯入他系統程式;不碰 TA-Lib;同意閘不寫",
        "VIA:ACCEL-BRIDGE" in src and "def _via_net" in src
        and not [x for x in imports if x.startswith(("CGC_", "VRN_", "VCGC"))]
        and not re.search(r"^\s*(import|from)\s+" + "talib", src, re.M)
        and not re.search(r"\[[\"']VIA_(NET|SCRAPE)_" + r"CONSENT[\"']\]\s*=(?!=)", src))
    n = sum(ok)
    print(f"  [計] {_STEM} {TAG} 本版 {n}/{len(ok)} · {'PASS' if n == len(ok) else 'FAIL'}")
    if n != len(ok):
        return 1
    rc1 = prior_selftest_private()
    return rc1


def main() -> int:
    argv = sys.argv[1:]
    if "--selftest-private" in argv:
        return prior_selftest_private()
    if "--selftest" in argv:
        return selftest()
    return PRIOR.main()


if __name__ == "__main__":
    sys.exit(main())
