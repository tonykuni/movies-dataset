#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL236_NumberedCatalog v0101 — 編號冊(VIA_Numbering_*)是產出,不當 regex / 參數來源(斷回饋迴圈)

v0100 的 regex 掃描走 registry 下每一本 *SSOT* 冊。R23 起 CGC_MDL237 把編號寫進 VIA_Numbering_SSOT_v0100.json(編入 SSOT),
那本冊的分類表裡有模組名如 CGC_MDL115_SSOTRegexDict——鍵名帶 Regex,v0100 就把它當成 regex 再編一次號:每跑一次
apply 就多長 11 列(回饋迴圈)。v0101:VIA_Numbering_* 仍算一本 SSOT 冊(SS 照列),但不進 regex / 參數掃描。
其餘照 v0100。只收 VCGC 呼叫。零網路。
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
STEM = "CGC_MDL236_NumberedCatalog"


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", path.stem)
    return int(m.group(1)) if m else -1


PRIOR = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(STEM + "_prior_for_" + Path(__file__).stem, PRIOR)
_PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _PRIOR
_spec.loader.exec_module(_PRIOR)
ENGINE = Path(__file__).stem
GENERATED = re.compile(r"^VIA_Numbering_")
_SSOT_BOOKS = _PRIOR.ssot_books
_REGEX_AND_PARAMS = _PRIOR.regex_and_params


def source_books() -> list:
    """SSOT books that are rule sources: every *SSOT* book except the numbering books this system writes itself."""
    return [p for p in _SSOT_BOOKS() if not GENERATED.match(p.name)]


def regex_and_params(ledger: dict) -> tuple:
    _PRIOR.ssot_books = source_books
    try:
        return _REGEX_AND_PARAMS(ledger)
    finally:
        _PRIOR.ssot_books = _SSOT_BOOKS


_PRIOR.regex_and_params = regex_and_params


def __getattr__(name: str):
    return getattr(_PRIOR, name)


def main(argv=None) -> int:
    return _PRIOR.main(argv)


def selftest() -> int:
    import tempfile
    rc = _PRIOR.selftest()
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    with tempfile.TemporaryDirectory() as td:
        a, b = Path(td) / "VIA_Numbering_SSOT_v0100.json", Path(td) / "VIA_Central_Params_SSOT_v0100.json"
        a.write_text('{"categories": {"FNC": {"CGC_MDL115_SSOTRegexDict_v0100": "FNC-C0001"}}}', encoding="utf-8")
        b.write_text('{"rules": {"rx": "\\\\d+"}}', encoding="utf-8")
        orig = _SSOT_BOOKS
        globals()["_SSOT_BOOKS"] = lambda: [a, b]
        try:
            kept = [p.name for p in source_books()]
            rx, _ = regex_and_params({"codes": {}, "next": {}})
        finally:
            globals()["_SSOT_BOOKS"] = orig
    chk("⑩ 編號冊不當 regex 來源(斷回饋迴圈);規則冊照掃", kept == ["VIA_Central_Params_SSOT_v0100.json"] and
        not [r for r in rx if "Numbering" in r["source"]], ", ".join(kept))
    chk("⑪ 編號冊仍算一本 SSOT 冊(SS 照列)", any(GENERATED.match(p.name) for p in _SSOT_BOOKS()) or
        not (HERE / "VIA_Numbering_SSOT_v0100.json").exists())
    ok = rc == 0 and all(results)
    print(f"  {ENGINE} selftest +{sum(results)}/{len(results)} {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
