#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""CGC_SystemManager v0120 — 薄尾:toolbox 中央控管群補「VCGC 四指令中樞」(VCGC_CommandHub,倉的 VIA 根)

2026-11-24 全景:#729 新進的 VCGC_CommandHub 是操作員每天打的四個短指令(via · via-pano · via-bak · via-ast)的 Python 本體,
但工具箱目錄沒有它 → 它有沒有編號、有沒有交接案、有沒有盤點站、會不會影響他系統,toolbox check 都看不到。
本版只把它加進中央控管群(資料夾 = VIA 根);核法照 v0119(程式七件事 + 逐函式獨立性)。其餘動詞全部照 v0119。
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
_STEM = "CGC_SystemManager"
TAG = "CGC_SystemManager v0120"


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
if "cgc_prior_for_v0120" in sys.modules:
    PRIOR = sys.modules["cgc_prior_for_v0120"]
else:
    _spec = importlib.util.spec_from_file_location("cgc_prior_for_v0120", PRIOR_PATH)
    PRIOR = importlib.util.module_from_spec(_spec)
    sys.modules["cgc_prior_for_v0120"] = PRIOR
    _spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


HUB = {"key": "hub", "name": "VCGC 四指令中樞(via · via-pano · via-bak · via-ast 的 Python 本體)", "stem": "VCGC_CommandHub", "dir": ".",
       "route": "via / via-pano / via-bak / via-ast(VIA_ProfileLoader 取尾版)"}
if not any(t.get("key") == "hub" for t in PRIOR.CENTRAL):
    PRIOR.CENTRAL.insert(0, HUB)


def main() -> int:
    return PRIOR.main()


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("[計] %s 自測開始(本版 3 項 · 前版 %s)" % (TAG, PRIOR_PATH.name), flush=True)
    cat = PRIOR.catalog()
    chk("T1 中央控管群有四指令中樞,而且只有一筆", sum(t["key"] == "hub" for t in cat) == 1 and [t for t in cat if t["key"] == "hub"][0]["group"] == "中央控管")
    row = [r for r in PRIOR.check()["rows"] if r["key"] == "hub"]
    chk("T2 真倉:找得到中樞尾版(VIA 根)並核了獨立性", row and row[0]["tail"] and "獨立性" in row[0]["items"], row)
    src = Path(__file__).read_text(encoding="utf-8")
    prior_rc = PRIOR.selftest()
    chk("T3 第 3 行加速器標記 · 前版 %s 自測照過" % PRIOR_PATH.name, src.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]" and prior_rc == 0, prior_rc)
    n = sum(ok)
    print("[計] %s 自測 %d/%d · %s" % (TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    return 0 if n == len(ok) else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
