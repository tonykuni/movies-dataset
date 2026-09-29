#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GRP_ENG041_RotationMethodLab v0103 — 輪動方法論實測室(薄尾:接 SUP_MDL755 Polars 表格層守門 · 記憶體不足轉 temp)
操作員 2026-09-29「go on add polars to all necessary engines 記憶體不足可用temp替代用」。

v0102 → v0103(側線 2026-09-29 c;主線批號由併線的手指定 L25):
  量到的:價 · 成交 · 法人面板撈進 pandas(滾動 17 處)(必要引擎名冊 N1,SUP_MDL755 NECESSARY)。
  本尾版在本引擎行程裝 FRAME 守門(SUP_MDL755 VIAPolarsFrame;鎖冊 frame 優先,R20c):之後開的每條 DuckDB 連線 → 溢寫夾改到
  受管 temp(VIA_TEMP_ROOT 或系統 temp 下的 VIA_spill/,跑完即刪;當掉留下的由 sweep 清);檔案庫上限收到「當下可用記憶體 × 0.5」
  (下限 512 MiB;VIA_FRAME_MEM_FRACTION 可調),記憶體不足時 DuckDB 改寫 temp、不吃光 RAM;記憶體庫只換溢寫夾(表資料不能溢寫,
  收上限會 Out of Memory)。有 polars 的境,Polars 串流也寫同一夾(POLARS_TEMP_DIR)。
  pandas 端照前一版一字不動(`.df()` 零差異):容器實量把 `.df()` 改走 temp parquet 再讀回,峰值反而升(761 對 642 MB)、
  沒 ORDER BY 時列序還會變 —— 所以不走那條;記憶體不足時省下來的是 DuckDB 端(join / 排序 / 聚合溢寫到受管 temp)。
  其餘照 v0102 一字不動(thin tail;__getattr__ 轉接;CLI 原樣交 v0102 的 main())。零網路 · 不安裝。
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
# ===== [VIA:FRAME-BRIDGE:v0100] Polars 表格層橋(操作員 2026-09-29 記憶體不足可用temp替代用;graceful) =====
VIA_FRAME_PATH = None
try:
    import json as _fb_json
    from pathlib import Path as _fb_Path
    _fb_p = _fb_Path(__file__).resolve()
    while _fb_p.parent != _fb_p:
        _fb_sup = _fb_p / "supportive modules"
        if (_fb_sup / "registry").is_dir():
            _fb_locks = sorted((_fb_sup / "registry").glob("VIA_ToolVersion_Lock_v*.json"))
            _fb_rel = ((_fb_json.loads(_fb_locks[-1].read_text(encoding="utf-8")).get("frame") or {}).get("path")
                       if _fb_locks else None)
            _fb_hit = (_fb_p.parent / _fb_rel) if _fb_rel else None
            if _fb_hit is None or not _fb_hit.is_file():
                _fb_tails = sorted(_fb_sup.glob("SUP_MDL755_VIAPolarsFrame_v*.py"))
                _fb_hit = _fb_tails[-1] if _fb_tails else None
            VIA_FRAME_PATH = str(_fb_hit) if _fb_hit else None
            break
        _fb_p = _fb_p.parent
except Exception:
    VIA_FRAME_PATH = None


def _via_frame():
    """Polars 表格層惰性載入(鎖冊 frame 優先,缺則尾版);缺席回 None(誠實,引擎照舊跑)"""
    if VIA_FRAME_PATH is None:
        return None
    try:
        import importlib.util as _fb_ilu
        import sys as _fb_sys
        _fb_mod = _fb_sys.modules.get("VIA_FRAME")
        if _fb_mod is None or getattr(_fb_mod, "__file__", None) != VIA_FRAME_PATH:
            _fb_spec = _fb_ilu.spec_from_file_location("VIA_FRAME", VIA_FRAME_PATH)
            _fb_mod = _fb_ilu.module_from_spec(_fb_spec)
            _fb_spec.loader.exec_module(_fb_mod)
            _fb_sys.modules["VIA_FRAME"] = _fb_mod
        return _fb_mod
    except Exception:
        return None
# ===== [VIA:FRAME-BRIDGE:END] =====

import importlib.util
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "GRP_ENG041_RotationMethodLab"


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", path.stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


def guard() -> dict:
    """本引擎行程的 DuckDB 守門;FRAME 缺席 = 照前一版跑(誠實回 ABSENT,不擋)。"""
    fr = _via_frame()
    if fr is None:
        return {"state": "ABSENT", "why": "SUP_MDL755 VIAPolarsFrame 不在(橋解不到)"}
    return fr.install_duckdb_guard(_STEM)


def main() -> int:
    guard()
    return PRIOR.main()


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    print(f"=== {Path(__file__).stem} · 薄尾自測(FRAME 守門開著,再串 {PRIOR_PATH.stem} 全部檢)===")
    saved = os.environ.get("VIA_TEMP_ROOT")
    saved_guard = os.environ.pop("VIA_FRAME_GUARD", None)    # 量的是守門本身:操作員關掉的閥先放開,結束還原
    sandbox = tempfile.mkdtemp(prefix="via_frame_tail_")
    os.environ["VIA_TEMP_ROOT"] = sandbox
    fr = _via_frame()
    chk("① FRAME 橋:解到 SUP_MDL755 VIAPolarsFrame(鎖冊 frame 優先,缺則尾版)並載得進來",
        fr is not None and callable(getattr(fr, "install_duckdb_guard", None)), Path(VIA_FRAME_PATH or "-").name)
    rc = 1
    try:
        g = guard()
        import duckdb
        c = duckdb.connect(os.path.join(sandbox, "t.duckdb"))
        tdir = c.execute("SELECT current_setting('temp_directory')").fetchone()[0]
        c.close()
        chk("② 守門開:本行程新開的 DuckDB 連線 → 溢寫夾在受管 temp(VIA_TEMP_ROOT/VIA_spill)下;前一版全部檢在守門下照跑",
            g.get("state") == "ON" and tdir == g.get("spill") and Path(tdir).parent.name == "VIA_spill", tdir)
        rc = PRIOR.selftest()
    finally:
        if fr is not None:
            fr.uninstall_duckdb_guard()
        if saved is None:
            os.environ.pop("VIA_TEMP_ROOT", None)
        else:
            os.environ["VIA_TEMP_ROOT"] = saved
        if saved_guard is not None:
            os.environ["VIA_FRAME_GUARD"] = saved_guard
        spill = Path(sandbox, "VIA_spill")
        left = sorted(p.name for p in spill.glob("*")) if spill.is_dir() else []
        shutil.rmtree(sandbox, ignore_errors=True)
    chk("③ 收:守門卸下、溢寫夾刪乾淨(零足跡)", not left, ", ".join(left[:3]))
    print(f"  {Path(__file__).stem} 薄尾 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'} · 前一版 rc={rc}")
    return rc if all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv[1:] else main())
