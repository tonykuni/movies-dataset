#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VRN_ENG073_ReportStructuredDB v0139 — 薄尾:自測讀命令冊改沿 dot-source 鏈(R33 SDD 自測實錄)

R33 SDD 自測(CGC_MDL245 selftests,經 VCGC run)實錄 v0138:60/64。⓬ 批659「repair-price 動詞接得到 + 四面登錄在位」判紅,
因為它只讀命令冊 Register-VIA-Commands 尾版的字面;自 v0244 起尾版是薄尾(dot-source 往回接),via-repairprice 在 v0243 本體裡、
執行期確實在 —— 與全景 v0116 · 唯一接觸口 CGC_MDL157 v0106 同一類「看不見薄尾鏈」的假紅。
本尾版:自測期間「讀命令冊」改用 CGC_MDL157 v0106 起的鏈讀(命令冊鏈的唯一正主;L05 不另寫第二把尺),其餘每一檢照 v0138。
㉑㉒㉓ 金融機構 SSOT 三檢需要 pydantic(缺件 = 依批412 規矩一律紅,裝件是操作員的手),本尾版不動。
其餘整支照 v0138(__getattr__ 轉接;L04 舊版留作版史)。VRN 不直接對外:只帶加速器橋,不帶網路橋。
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
_STEM = "VRN_ENG073_ReportStructuredDB"


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", path.stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum,
                  default=HERE / "VRN_ENG073_ReportStructuredDB_v0138.py")   # the prior this tail was cut from
_spec = importlib.util.spec_from_file_location("eng073_prior_for_" + Path(__file__).stem, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


_BOOK_RX = re.compile(r"^Register-VIA-Commands-v\d{4}\.ps1$")


def _chain_reader():
    """The command-book chain reader of CGC_MDL157 (its owner since v0106); absent → None (then the tail text is read, as before)."""
    reg = HERE.parent.parent / "supportive modules" / "registry"
    hits = sorted(reg.glob("CGC_MDL157_VIAUniqueEntryControl_v*.py"), key=_vnum)
    for p in reversed(hits):
        try:
            spec = importlib.util.spec_from_file_location("uec_for_eng073", p)
            m = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = m
            spec.loader.exec_module(m)
            if hasattr(m, "command_book_chain"):
                return m.read
        except Exception:
            continue
    return None


def selftest() -> int:
    """v0138's selftest, with one change: a command book (Register-VIA-Commands-v*.ps1) reads as its dot-source chain."""
    reader = _chain_reader()
    orig = Path.read_text

    busy = []

    def book_aware(self, *a, **k):
        if reader is not None and not busy and _BOOK_RX.match(self.name):
            busy.append(1)                       # the chain reader reads each book itself: no re-entry
            try:
                return reader(self)
            finally:
                busy.pop()
        return orig(self, *a, **k)

    Path.read_text = book_aware
    try:
        rc = PRIOR.selftest()
    finally:
        Path.read_text = orig
    print(f"  [v0139] 命令冊照 dot-source 鏈讀(正主 CGC_MDL157 v0106 起的 read):{'有' if reader else '缺,照舊讀尾版'}")
    return rc


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return PRIOR.main()


if __name__ == "__main__":
    sys.exit(main())
