#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL278_NumberGrant v0101 — 薄尾:④ 中央檢測對正則證明套件缺誠實容忍(修既存容器紅)。

v0100 ④ 的夾具含一條 REGEX 候選 IN-01(^[1-9][0-9]{3}$ · pos/neg 齊),預期 make_plan 給 READY → READY 共 3。
正則證明引擎要套件(re2 · polars · pandera · ahocorasick · duckdb);容器重建後這些不在(Default 無 setup script · AI 不裝套件),
IN-01 照設計停 REVIEW(REGEX_PROOF_ENGINE_ABSENT · 不拿 re 冒充)→ READY 2 · REVIEW 1,黃燈不變。這是誠實結果非退步。
v0101(薄尾 · v0100 不動):跑 v0100 自測;唯一紅是 ④ 且形狀符合「套件缺 → REGEX 停 REVIEW」(READY 2 + REVIEW + 套件確實缺)才容忍;
套件齊的桌機要求 v0100 全 9/9。其餘一字不動、不裝套件。
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
import io
import contextlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL278_NumberGrant"
TAG = "v" + Path(__file__).stem.rsplit("_v", 1)[-1]


def _vnum(p):
    import re
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0101", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["--selftest"]:
        return selftest()
    return PRIOR.main(argv)


def selftest() -> int:
    proof_absent = [m for m in ("re2", "polars", "pandera", "ahocorasick", "duckdb") if importlib.util.find_spec(m) is None]
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rc = PRIOR.selftest()
    except Exception as exc:  # noqa: BLE001
        print(buf.getvalue(), end="", flush=True)
        print(f"  [FAIL] 前版 v0100 自測擲例外 · {type(exc).__name__}: {exc}", flush=True)
        return 1
    out = buf.getvalue()
    fails = [ln for ln in out.splitlines() if "[FAIL]" in ln]
    # 唯一紅是 ④、形狀 = 套件缺 → REGEX 停 REVIEW(READY 2 · 有 REVIEW),且證明套件確實缺 → 容忍
    only4 = len(fails) == 1 and "④" in fails[0] and "'READY': 2" in fails[0] and "REVIEW" in fails[0]
    tolerated = rc != 0 and proof_absent and only4
    # 印出前版輸出(容忍時把末行 FAIL 判決濾掉,改印 v0101 判決)
    for ln in out.splitlines():
        if tolerated and ln.lstrip().startswith("[計]") and "FAIL" in ln:
            continue
        if tolerated and "[FAIL]" in ln and "④" in ln:
            ln = ln.replace("[FAIL]", "[容忍·套件缺]")
        print(ln, flush=True)
    print(f"=== {_STEM} {TAG} · 薄尾自測(④ 正則證明套件缺誠實容忍;proof_absent={proof_absent})===", flush=True)
    if rc == 0:
        print(f"  [計] {_STEM} {TAG} · 前版 v0100 全 9/9 · PASS", flush=True)
        return 0
    if tolerated:
        print("  [容忍] ④ 唯一紅:正則證明套件缺(%s)→ REGEX 候選 IN-01 照設計停 REVIEW · READY 2 而非 3 · 黃燈不變(桌機套件齊才要求 READY 3)" % ",".join(proof_absent), flush=True)
        print(f"  [計] {_STEM} {TAG} · 前版唯一紅為套件缺容忍 · PASS", flush=True)
        return 0
    print(f"  [計] {_STEM} {TAG} · 前版紅非套件缺(真問題)· FAIL · fails={len(fails)} · proof_absent={bool(proof_absent)}", flush=True)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
