#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL257_AiVerbLadder v0102 — 薄尾:自測③ 的「照實退路」判讀跟上匯流排標籤

實錄(2026-10-10,PR #518 交接收據 ai_verb_ladder 重跑):v0101 本版 3/4,③ 失敗於
('/usr/local/bin/python3', 'bus:base 退路(境未見)')。容器沒建家族境時,CGC_MDL157 匯流排照實回報
「bus:base 退路(境未見)」——這正是 ③ 要接受的「照實退路」,但 v0101 只認字首「退路」/「sys.executable」,
匯流排標籤加了 bus: 前綴就誤判。本版:③ 改認來源標籤含「退路」或以 sys.executable 起頭(家族境找到時照舊要求非目前解譯器)。
引擎行為(梯次 · family_run · 判讀)一字不改,全照 v0101;只收 VCGC 呼叫。零網路。
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
STEM = "CGC_MDL257_AiVerbLadder"


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_v{_vnum(Path(__file__)):04d}", _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)          # v0101:已把家族版 _run_selftest 裝進 v0100 模組全域


def __getattr__(name: str):
    return getattr(PRIOR, name)


def honest_fallback(py: str, src: str) -> bool:
    """③ 判讀:解得到家族境(非目前解譯器)= 過;沒有家族境時,來源標籤要照實寫出退路。"""
    return bool(py) and (py != sys.executable or "退路" in str(src) or str(src).startswith("sys.executable"))


def _tail_checks() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {note}" if note and not cond else ""))

    base = PRIOR.PRIOR
    chk("① v0101 家族版 _run_selftest 仍裝在 v0100 模組全域", base._run_selftest is PRIOR._run_selftest)
    chk("② 家族判定:VRN / VDF / VAP / core", PRIOR.family_of("functional modules/VRN/x.py") == "vrn"
        and PRIOR.family_of("functional modules/VAP/x.py") == "vap" and PRIOR.family_of("/tmp/x.py") == "core")
    py, src, _ = PRIOR.family_python("functional modules/VDF/engine/x.py")
    chk("③ VDF 引擎解得到家族境 python(或照實退路)", honest_fallback(py, src)
        and honest_fallback(sys.executable, "bus:base 退路(境未見)") and honest_fallback("/env/vdf/python", "bus:via_vdf")
        and not honest_fallback(sys.executable, "bus:via_vdf"), (py, src))
    s = Path(__file__).read_text(encoding="utf-8")
    chk("④ 加速器橋在 · 本檔沒有 subprocess 以 sys.executable 直派(AST)", "[VIA:ACCEL-BRIDGE:v0100]" in s and PRIOR._no_direct_sysexe(__file__))
    print(f"[計] CGC_MDL257_AiVerbLadder v0102 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


def main() -> None:
    if sys.argv[1:2] == ["--selftest"]:
        _, fails = PRIOR.PRIOR.selftest()
        rc_tail = _tail_checks()
        sys.exit(0 if fails == 0 and rc_tail == 0 else 1)
    PRIOR.main()


if __name__ == "__main__":
    main()
