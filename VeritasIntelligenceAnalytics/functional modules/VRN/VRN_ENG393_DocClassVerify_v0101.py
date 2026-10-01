#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VRN_ENG393_DocClassVerify v0101 — 薄尾:數字格剖析遇到「只有幣別前綴」的格子當掉(前版 v0100 本體照讀)

v0100→v0101(R36 操作員工作站實錄 2026-10-01 `via-vcgc run --family vrn VRN_ENG393_DocClassVerify verify --samples "C:\測試樣本報告"`):
  Traceback … build_cells → parse_num → `sign, s = s[0], s[1:]` → IndexError: string index out of range(第 2 次)。
  根因:Python 的 `"" in "+-"` 永遠為 True。格子整格就是冊上的前綴(`$` `NT$` `US$` …,表頭的幣別欄常見)時,
  剝掉前綴後 s 變空字串,第二次正負號檢查 `s[:1] in "+-"` 判真,再取 s[0] 就當掉 —— 一格就讓整批 verify 停掉。
  修法(只動取數這一格,其餘一字不動):正負號檢查改成「s 非空且首字是 + / -」;剝完前綴 / 字尾後是空字串 = 不是數字格(None, '')。
  前版 build_cells 在前版命名空間裡叫 parse_num → 換掉 PRIOR.parse_num 這一格即可(同 ENG080 v0111 的作法)。
VIA_FROM_VCGC:經 VCGC 跑(via-vcgc run --family vrn VRN_ENG393_DocClassVerify …取尾版);零網路;不用 TA-Lib;正本唯讀。
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
import unicodedata
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_ENG393_DocClassVerify"


def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum,
                  default=HERE / "VRN_ENG393_DocClassVerify_v0100.py")   # the prior this tail was cut from
_spec = importlib.util.spec_from_file_location("docclass_prior_for_" + Path(__file__).stem, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


ENGINE = Path(__file__).stem


def _signed(s: str) -> bool:
    return bool(s) and s[0] in "+-"


def parse_num(text, bk: dict | None = None) -> tuple:
    """Whole cell is one number → (Fraction, unit); otherwise (None, ''). A cell that is only a prefix / suffix is not a number."""
    spec = ((bk or PRIOR.book()).get("xcheck") or {}).get("numeric_cell") or {}
    s = unicodedata.normalize("NFKC", PRIOR.ZW_RX.sub("", str(text or ""))).strip()
    s = re.sub(r"\s+", "", s)
    if not s:
        return None, ""
    for ch in spec.get("minus_chars", "−–—－"):
        s = s.replace(ch, "-")
    neg = False
    if spec.get("neg_paren", True) and len(s) > 2 and s[0] in "(（" and s[-1] in ")）":
        neg, s = True, s[1:-1]
    sign = ""
    if _signed(s):
        sign, s = s[0], s[1:]
    for pre in sorted(spec.get("strip_prefix") or [], key=len, reverse=True):
        if s.upper().startswith(pre.upper()):
            s = s[len(pre):]
            break
    if not sign and _signed(s):
        sign, s = s[0], s[1:]
    unit = ""
    for suf in sorted(spec.get("strip_suffix") or [], key=len, reverse=True):
        if s.endswith(suf):
            unit, s = suf, s[:-len(suf)]
            break
    if not s:
        return None, ""
    rx = spec.get("rx") or r"^[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?$"
    if not re.fullmatch(rx, s):
        return None, ""
    try:
        v = Fraction(Decimal(s.replace(",", "")))
    except (InvalidOperation, ValueError):
        return None, ""
    if sign == "-":
        v = -v
    return (-v if neg else v), unit


PRIOR.parse_num = parse_num          # build_cells / 自核在前版命名空間裡叫它 → 換這一格即可


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    # 實錄重現:前版本體的 parse_num(不經本版換格)遇到只有前綴的格子會當掉
    spec2 = importlib.util.spec_from_file_location("docclass_raw_prior_" + ENGINE, _PRIOR_PATH)
    raw = importlib.util.module_from_spec(spec2)
    sys.modules[spec2.name] = raw
    spec2.loader.exec_module(raw)
    crashed = []
    for c in ("$", "NT$", "US$"):
        try:
            raw.parse_num(c)
        except IndexError:
            crashed.append(c)
    chk("實錄重現:前版遇到整格只有幣別前綴($ · NT$ · US$)→ IndexError", crashed == ["$", "NT$", "US$"], crashed)
    chk("本版:只有前綴 / 只有字尾 / 只有符號的格子 = 不是數字格,不當掉",
        all(parse_num(c) == (None, "") for c in ("$", "NT$", "US$", "%", "x", "倍", "-", "+", "(%)", "NT$%", "-$")),
        [(c, parse_num(c)) for c in ("$", "NT$", "US$", "%", "x", "倍", "-", "+", "(%)", "NT$%", "-$")])
    chk("數值照舊:NT$1,200 → 1200 · -3.5% → -3.5 % · (12.5) → -12.5 · +$5 → 5 · −2 倍 → -2 倍",
        parse_num("NT$1,200") == (1200, "") and parse_num("-3.5%") == (Fraction(-7, 2), "%") and parse_num("(12.5)") == (Fraction(-25, 2), "")
        and parse_num("+$5") == (5, "") and parse_num("−2倍") == (-2, "倍"))
    same = [c for c in ("1,234", "-0.1%", "(3.2)", "US$45.6", "27.9x", "n.a.", "Q1", "2Q25", "", "abc", "12.5pp")
            if raw.parse_num(c) != parse_num(c)]
    chk("其餘格子與前版結果完全相同(只修當掉那一條路)", not same, same)
    chk("前版 build_cells / 自核走本版的 parse_num", PRIOR.parse_num is parse_num)
    body = Path(__file__).read_text(encoding="utf-8")
    chk("帶加速器橋 · VIA_FROM_VCGC 標記 · 不匯入 TA-Lib", "[VIA:ACCEL-BRIDGE" in body and "VIA_FROM_VCGC" in body
        and not re.search(r"^\s*(import|from)\s+" + "ta" + r"lib\b", body, re.M))
    print("--- 前版 v0100 全套自測(在本版取數下重跑)---")
    prc = PRIOR.selftest()
    chk("前版自測在本版取數下仍全過", prc == 0)
    print(f"[VRN_ENG393 v0101 前綴格不當掉] 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return PRIOR.main()


if __name__ == "__main__":
    sys.exit(main())
