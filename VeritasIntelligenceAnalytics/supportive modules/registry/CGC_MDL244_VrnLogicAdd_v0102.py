#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL244_VrnLogicAdd v0102 — 薄尾:自測② 的「照實退路」判讀跟上匯流排標籤

實錄(2026-10-10,PR #518 交接收據 vrn_logic_add 重跑):v0101 本版 3/4,② 失敗於
{'python': '/usr/local/bin/python3', 'source': 'bus:base 退路(境未見)'}。容器沒建 VRN 家族境時,
CGC_MDL157 匯流排照實回報「bus:base 退路(境未見)」——這正是 ② 要接受的「照實退路」,但 v0101 只認
字首「退路」/「sys.executable」,匯流排標籤加了 bus: 前綴就誤判(與 CGC_MDL257 v0102 同一病)。
本版:② 改認來源標籤含「退路」或以 sys.executable 起頭(家族境找到時照舊要求非目前解譯器);
[計] 行不再帶家族境路徑(換機器就變字,交接標記不能釘機器路徑),路徑另起一行照印。
派送行為(家族路由 · check · main)一字不改,全照 v0101;前版以 glob 取(不釘版號)。只收 VCGC 呼叫。零網路。
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
STEM = "CGC_MDL244_VrnLogicAdd"


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_v{_vnum(Path(__file__)):04d}", _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)          # v0101:載入時已把 v0100 模組的 subprocess 換成家族路由版


def __getattr__(name: str):
    return getattr(PRIOR, name)


def honest_fallback(py: str, src: str) -> bool:
    """② 判讀:解得到家族境(非目前解譯器)= 過;沒有家族境時,來源標籤要照實寫出退路。"""
    return bool(py) and (py != sys.executable or "退路" in str(src) or str(src).startswith("sys.executable"))


def selftest() -> int:
    rc = PRIOR.PRIOR.selftest()          # v0100 自測(check 經 v0101 家族路由)
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {note}" if note and not cond else ""))

    chk("① 前版自測照過(check 經家族路由)", rc == 0)
    r = [x for x in PRIOR.ROUTED if x["engine"] == PRIOR.PRIOR.ENGINE.name]
    chk("② VRN 引擎自測改走家族境 python(不是目前解譯器,除非照實退路)",
        r and honest_fallback(r[-1]["python"], r[-1]["source"])
        and honest_fallback(sys.executable, "bus:base 退路(境未見)") and honest_fallback("/env/vrn/python", "bus:via_vrn_312")
        and not honest_fallback(sys.executable, "bus:via_vrn_312"), r[-1:] if r else "沒派")
    chk("③ 家族判定:VRN / VDF / VAP / core", PRIOR.family_of("functional modules/VRN/x.py") == "vrn"
        and PRIOR.family_of("functional modules/VDF/e/x.py") == "vdf"
        and PRIOR.family_of("supportive modules/registry/x.py") == "core")
    src = Path(__file__).read_text(encoding="utf-8")
    chk("④ 加速器橋在 · 本檔沒有 subprocess 以 sys.executable 直派(AST)",
        "[VIA:ACCEL-BRIDGE:v0100]" in src and PRIOR._no_direct_sysexe(__file__))
    passed = all(ok)
    print(f"  [境] VRN 家族境 {r[-1]['python'] if r else '-'} · 來源 {r[-1]['source'] if r else '-'}")
    print(f"[計] CGC_MDL244_VrnLogicAdd v0102 本版 {sum(ok)}/{len(ok)} · {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


def main() -> int:
    return PRIOR.main()


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
