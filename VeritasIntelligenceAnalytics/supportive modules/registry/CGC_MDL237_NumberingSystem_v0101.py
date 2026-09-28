#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL237_NumberingSystem v0101 — ENV 類把工具鎖冊的四件工具也編進去(加速器 · 網路 · LAYOUT · NLP)

R26 Z277:v0100 的 env_items() 讀工具鎖冊時找 `lock["tools"]` / `lock["families"]`,但 VIA_ToolVersion_Lock 的頂層鍵就是
accelerator / network / layout / nlp(每家一個 {path, version, sha256, …})→ 四件工具的鎖一列都沒編成 ENV 號。
v0101 只換 env_items():先照 v0100 算;v0100 沒產出任何 `lock|…` 列時,改讀頂層每個帶 path / version 的家,
列格式與 v0100 同一支 item()(內容鍵 `lock|<家>`,只增不減)。其餘整支 v0100 原樣(thin tail;__getattr__ 轉接)。
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
STEM = "CGC_MDL237_NumberingSystem"


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", path.stem)
    return int(m.group(1)) if m else -1


PRIOR = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(STEM + "_prior_for_" + Path(__file__).stem, PRIOR)
_PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _PRIOR
_spec.loader.exec_module(_PRIOR)
ENGINE = Path(__file__).stem
_V0100_ENV = _PRIOR.env_items


def lock_rows(lock_path, lock: dict) -> list:
    """Top-level tool families of the lock book (accelerator / network / layout / nlp …) as ENV rows."""
    out = []
    for fam, row in sorted((lock or {}).items()):
        if not isinstance(row, dict) or not (row.get("path") or row.get("version")):
            continue
        out.append(_PRIOR.item("ENV", "lock|" + fam, fam, "工具鎖", _PRIOR._rel(lock_path), "via-vcgc tools activate " + fam,
                               _PRIOR.updated(_PRIOR._rel(lock_path)), "VCGC", str(row.get("version") or "—"), "GREEN",
                               Path(str(row.get("path") or "")).name))
    return out


def env_items(envs: dict) -> list:
    out = _V0100_ENV(envs)
    if any(str(r.get("key", "")).startswith("lock|") or "lock|" in str(r.get("content_key", "")) for r in out):
        return out
    lock = _PRIOR._newest(HERE, "VIA_ToolVersion_Lock_v*.json")
    return out + (lock_rows(lock, _PRIOR._json(lock)) if lock else [])


_PRIOR.env_items = env_items            # build() looks env_items up in v0100's globals at call time


def __getattr__(name: str):
    return getattr(_PRIOR, name)


def main(argv=None) -> int:
    if "--selftest" in (sys.argv[1:] if argv is None else argv):
        return selftest()
    return _PRIOR.main(argv)


def selftest() -> int:
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    lock = _PRIOR._newest(HERE, "VIA_ToolVersion_Lock_v*.json")
    rows = lock_rows(lock, _PRIOR._json(lock))
    fams = sorted(str(r.get("name")) for r in rows)
    chk("Z277 工具鎖冊四件工具都成 ENV 列(頂層鍵)", {"accelerator", "network", "layout", "nlp"} <= set(fams), ", ".join(fams))
    v = {str(r.get("name")): str(r.get("version") or r.get("ver") or "") for r in rows}
    chk("Z277 列帶鎖定版號", all(v.get(f) for f in ("accelerator", "network")) and v.get("accelerator", "").startswith("v"), str(v))
    fake = {"tools": {"x": {"version": "v1"}}}
    rows2 = lock_rows(lock, fake)
    chk("Z277 沒有頂層家時不發明列(舊格式交給 v0100)", rows2 == [])
    ok = all(results)
    print(f"  {ENGINE} selftest {sum(results)}/{len(results)} {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
