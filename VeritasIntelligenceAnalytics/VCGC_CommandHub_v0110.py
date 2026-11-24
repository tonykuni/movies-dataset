#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VCGC_CommandHub v0110 — 薄尾(v0100–v0109 一字不動):via-doctor 印總表時崩潰修正

2026-11-24 操作員「先檢查加速器跟網路工具的 libs env 是否都安裝 · 其他工具也是透過 VCGC 工具進行安裝」→ 跑 via-doctor:
  七支外掛都跑完、DOCTOR_latest 也寫了,印總表那一步 TypeError: print_matrix() got an unexpected keyword argument 'footer_note'。
  原因:v0105 把 v0100 的 print_detailed_summary_matrix(title, sections, footer_note=…) 換成自己的 print_matrix(title, rows, footer=…),
  參數名不同;v0101 的 _rows_print(doctor · install 計畫 · 其他總表)照 v0100 的寫法傳 footer_note → 崩潰。
本版:在 v0105 換的那一層裝一支相容外殼,footer_note / footer 兩種寫法都收,轉給 v0105 的四色矩陣;其他不動。不 import 他系統。零 TA-Lib。
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

import contextlib
import importlib.util
import io
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VCGC_CommandHub"
TAG = "VCGC_CommandHub v0110"


def _vnum(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
if PRIOR_PATH.stem in sys.modules:
    PRIOR = sys.modules[PRIOR_PATH.stem]
else:
    _spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem, PRIOR_PATH)
    PRIOR = importlib.util.module_from_spec(_spec)
    sys.modules[PRIOR_PATH.stem] = PRIOR
    _spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


def _owner(name: str):
    """前版鏈上自己定義 name 的那一版(換在真正被讀的那一層;R4 換錯層)。"""
    m, seen = PRIOR, set()
    while m is not None and id(m) not in seen:
        seen.add(id(m))
        if name in vars(m):
            return m
        m = vars(m).get("PRIOR") or vars(m).get("P0")
    return None


HUB = _owner("parse_g")                                   # v0105:四色 print_matrix 在這
MATRIX_OWNER = HUB._MATRIX_OWNER                          # v0105 換掉 print_detailed_summary_matrix 的那一層(v0100)
_MATRIX0 = MATRIX_OWNER.print_detailed_summary_matrix     # = v0105 的 print_matrix(title, rows, footer=…)


def print_matrix_compat(title: str, sections: list, footer_note: str = None, footer: str = None, **_ignored) -> None:
    """v0100 寫法(footer_note=)與 v0105 寫法(footer=)都收,轉給 v0105 的四色矩陣。"""
    note = footer if footer is not None else footer_note
    if note is None:
        return _MATRIX0(title, sections)
    return _MATRIX0(title, sections, footer=note)


MATRIX_OWNER.print_detailed_summary_matrix = print_matrix_compat


def main(argv: list | None = None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(a)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("[計] %s 自測開始(本版 4 項 · 前版 %s)" % (TAG, PRIOR_PATH.name), flush=True)
    chk("T1 換在 v0105 換掉的那一層(print_detailed_summary_matrix 的定義層)· 原本那支是 v0105 的 print_matrix",
        Path(HUB.__file__).name == "VCGC_CommandHub_v0105.py" and MATRIX_OWNER.print_detailed_summary_matrix is print_matrix_compat
        and _MATRIX0 is HUB.print_matrix and "print_detailed_summary_matrix" in vars(MATRIX_OWNER))
    rows = [{"category": "A", "metric": "m", "status": "黃燈", "detail": "d", "action": "做某事"}]
    errs = []
    for kw in ({"footer_note": "VCGC Hub v0101 | 註"}, {"footer": "v0105 寫法"}, {}):
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                MATRIX_OWNER.print_detailed_summary_matrix("自測總表", rows, **kw)
        except TypeError as e:
            errs.append("%s → %s" % (kw, e))
    chk("T2 footer_note=(v0100 / v0101 _rows_print 的寫法)· footer=(v0105)· 不帶,三種都不再 TypeError", not errs, errs)
    ran = []
    keep = HUB.print_matrix
    try:
        HUB.print_matrix = lambda title, rows, footer="x": ran.append(footer)
        globals()["_MATRIX0"] = HUB.print_matrix
        MATRIX_OWNER.print_detailed_summary_matrix("t", rows, footer_note="NOTE")
    finally:
        HUB.print_matrix = keep
        globals()["_MATRIX0"] = keep
    chk("T3 footer_note 的內容照實轉成 v0105 的 footer(不丟註腳)", ran == ["NOTE"], ran)
    rp = _owner("_rows_print")._rows_print
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rp("VCGC DOCTOR — 自測", [{"category": "PY", "metric": "rich", "lamp": "YELLOW", "detail": "缺", "action": "via-install rich"}])
        e = ""
    except TypeError as ex:
        e = str(ex)
    chk("T4 doctor 實際走的 v0101 _rows_print 不再崩潰(崩潰處重現)", not e and "自測" in buf.getvalue(), e)
    n = sum(ok)
    print("[計] %s 自測 %d/%d · %s" % (TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    print("[前版] %s 自測(原函式)" % PRIOR_PATH.name, flush=True)
    MATRIX_OWNER.print_detailed_summary_matrix = _MATRIX0   # 前版自測照它原本的鏈跑(v0105 T9 要看到它自己那支)
    try:
        rc_prior = PRIOR.selftest()
    finally:
        MATRIX_OWNER.print_detailed_summary_matrix = print_matrix_compat
    print("[計] %s 自測 OK %d · FAIL %d · 前版 rc=%s" % (TAG, n, len(ok) - n, rc_prior), flush=True)
    return 0 if n == len(ok) and rc_prior == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
