#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL226_StepMatrix v0102 — 薄尾:第一步實測的快取鍵含整條版本鏈(Codex #366 P2)

Codex 審查(PR #366 P2):v0101 的快取鍵只雜湊鎖上的 NLP 薄尾(v0105)——它真正執行的是 v0104 → v0103 本體;
本體被改、被換、被刪,鍵不變,第一步照拿舊的「六件全過」報綠,`--brief` 其實已經壞了。全景同理(v0116 薄尾 → v0115 本體)。
本尾版:鍵 = 鎖上那支**同 stem、版號 ≤ 它的每一支**(整條版本鏈)的位元組,加上本矩陣自己的版本鏈;
鏈上任何一支改了 / 少了 / 多了 = 重測。舊版照 L04 不改,正常情況鍵不動;一動就是有人碰了不該碰的東西,重測才是對的反應。
其餘照 v0101(thin tail;__getattr__ 轉接)。零網路 · 不安裝 · 不寫冊。
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
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "CGC_MDL226_StepMatrix"


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", path.stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


def _chain(p: Path) -> list:
    """同 stem、版號 ≤ 它的每一支(依版號排);不是版號檔就只有它自己。"""
    m = re.match(r"^(?P<stem>.+)_v(?P<num>\d{4})\.py$", p.name)
    if not m:
        return [p]
    return sorted((q for q in p.parent.glob(m.group("stem") + "_v[0-9][0-9][0-9][0-9].py")
                   if _vnum(q) <= int(m.group("num"))), key=_vnum)


_V0101_KEY = PRIOR._key


def _key(files: list) -> str:
    """整條版本鏈的鍵(鏈上任何一支改了 / 少了 / 多了,鍵就變)。"""
    seen: list = []
    for f in list(files) + [Path(__file__)]:
        for q in _chain(Path(f)):
            if q not in seen:
                seen.append(q)
    return _V0101_KEY(seen)


PRIOR._key = _key                     # 前一版的 token_tools() 算鍵時問這一支


def main() -> int:
    return PRIOR.main()


def selftest() -> int:
    rc = PRIOR.selftest()
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        a, b = d / "X_ENG001_Y_v0100.py", d / "X_ENG001_Y_v0101.py"
        a.write_text("x = 1\n", encoding="utf-8")
        b.write_text("from prior import *\n", encoding="utf-8")
        k1, k1b = _key([b]), _key([b])
        a.write_text("x = 2\n", encoding="utf-8")         # 本體被改
        k2 = _key([b])
        a.unlink()                                        # 本體被刪
        k3 = _key([b])
        (d / "X_ENG001_Y_v0102.py").write_text("y = 1\n", encoding="utf-8")   # 比鎖上那支新的版本不算進鍵
        k4 = _key([b])
    chk("⑪ v0102 快取鍵含整條版本鏈(Codex #366 P2):同一組位元鍵不變 · 本體被改 → 鍵變 · 本體被刪 → 鍵變 · "
        "比鎖上那支新的版本不影響鍵;前一版的 token_tools 算鍵時用的就是這一支",
        k1 == k1b and k2 != k1 and k3 != k2 and k4 == k3 and PRIOR._key is _key)
    ok = rc == 0 and all(results)
    print(f"  {Path(__file__).stem} selftest +{sum(results)}/{len(results)} {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
