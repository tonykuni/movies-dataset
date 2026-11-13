#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0266 — v0265 薄尾(v0265 一字不動):缺第三方套件的判讀認得「別名 + 這台真的沒裝」。

實錄(2026-11-13 容器 VRN_SystemManager v0265 test):VRN_ENG060_TextOmni · VRN_ENG393_DocClassVerify 判 FAIL。
  兩支都只卡 PyMuPDF(fitz):ENG060 印「[FAIL] pymupdf 道(ModuleNotFoundError)」· ENG393 印「主標題:PyMuPDF 不在」與
  「fitz_tables:ABSENT(No module named 'fitz')」,另有「自造首頁 PDF」一項因造 PDF 要 fitz 而失敗。容器沒裝 PyMuPDF,桌機主境有。
  v0265 的 sm_missing_lib 只認「每個 [FAIL] 行都寫 No module named」或「最後例外是 ModuleNotFoundError」→ 這兩種寫法認不出來 → 誤紅。
本版:v0265 規則先照跑;不中時再看「輸出點名了已知第三方套件(含別名 pymupdf / PyMuPDF → fitz)且有缺件字樣
  (ModuleNotFoundError · No module named · 不在 · 缺件 · ABSENT),而且這台用 importlib.util.find_spec 實查確實沒裝」
  → 判 ABSENT,原因寫「缺套件 X(這台沒裝 · 有裝的機器要複驗)」。自家模組(VRN_ / VDF_ / CGC_ …)缺仍算真壞;
  套件其實有裝 → 照實 FAIL(不漂白)。其餘(test / health / conform / 所有動詞)全照 v0265。
VRN-2 自己的入口(L120 / L123);零網路 · 不用 TA-Lib · 不寫同意閘 · 不裝套件。
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
# [VIA:NET-BRIDGE] 留名:本版不出網

import contextlib
import importlib.util
import io
import re
import sys
from pathlib import Path

VERSION = "v0266"
HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
_MISSING_V0265 = PRIOR.sm_missing_lib

#: 輸出裡的寫法 → 實際 import 名(第三方;自家模組不在此表)
LIB_ALIASES = {"pymupdf": "fitz", "fitz": "fitz", "yfinance": "yfinance", "pdfplumber": "pdfplumber", "pypdfium2": "pypdfium2",
               "pytesseract": "pytesseract", "paddleocr": "paddleocr", "easyocr": "easyocr", "camelot": "camelot",
               "tabula": "tabula", "openpyxl": "openpyxl", "python-docx": "docx", "akshare": "akshare", "duckdb": "duckdb"}
MISSING_WORDS = re.compile(r"ModuleNotFoundError|No module named|不在|缺件|ABSENT", re.I)


def __getattr__(name):
    return getattr(PRIOR, name)


def lib_installed(mod: str) -> bool:
    try:
        return importlib.util.find_spec(mod) is not None
    except (ImportError, ValueError):
        return False


def sm_missing_lib(text: str) -> str:
    got = _MISSING_V0265(text)
    if got:
        return got
    t = text or ""
    if not MISSING_WORDS.search(t):
        return ""
    if any(m.split(".")[0].startswith(PRIOR.SM_REPO_MOD_PREFIX) for m in re.findall(r"No module named '([\w.]+)'", t)):
        return ""                                       # 自家模組缺 = 真壞
    low = t.lower()
    named = {mod for alias, mod in LIB_ALIASES.items() if re.search(r"(?<![\w-])" + re.escape(alias.lower()) + r"(?![\w-])", low)}
    absent = sorted(m for m in named if not lib_installed(m))
    return ",".join(absent) + "(這台沒裝 · 有裝的機器要複驗)" if absent else ""


PRIOR.sm_missing_lib = sm_missing_lib       # v0265 sm_test_native 用模組全域名 → 換成本版
PRIOR.SM_VERSION = VERSION


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""), flush=True)

    print("=== %s %s · 薄尾自測(缺套件別名 + 實查;其餘照 v0265)===" % (_STEM, VERSION), flush=True)
    e060 = "  [PASS] 車道矩陣 10+5 完整\n  [FAIL] pymupdf 道(ModuleNotFoundError)\n  [計] 5/6 檢通過\n"
    e393 = "  [FAIL] 主標題:PyMuPDF 不在 → 測試跳過\n  [FAIL] 自造首頁 PDF\n  [OK] fitz_tables:ABSENT(No module named 'fitz')\n"
    fitz_here = lib_installed("fitz")
    chk("① 重現:v0265 認不出 ENG060 / ENG393 的寫法(回空)", _MISSING_V0265(e060) == "" and _MISSING_V0265(e393) == "")
    if fitz_here:
        chk("② 這台有 fitz → 照實 FAIL(不漂白)", sm_missing_lib(e060) == "" and sm_missing_lib(e393) == "")
    else:
        chk("② 這台沒 fitz → ENG060 判缺 fitz", sm_missing_lib(e060).startswith("fitz"), sm_missing_lib(e060))
        chk("③ 這台沒 fitz → ENG393 判缺 fitz(別名 PyMuPDF)", sm_missing_lib(e393).startswith("fitz"), sm_missing_lib(e393))
    chk("④ 套件其實有裝(json)→ 不算缺件,照實 FAIL", sm_missing_lib("[FAIL] openpyxl 不在\n") == "" if lib_installed("openpyxl") else True)
    chk("⑤ 自家模組缺 → 真壞(不判缺件)", sm_missing_lib("[FAIL] x\nNo module named 'VRN_ENG999_X'\npymupdf 不在\n") == "")
    chk("⑥ 沒有缺件字樣 → 不判缺件", sm_missing_lib("[FAIL] pymupdf 道 數字對不上\n") == "")
    chk("⑦ 換裝:v0265 的 sm_missing_lib 指本版 · 版號 v0266", PRIOR.sm_missing_lib is sm_missing_lib and PRIOR.SM_VERSION == VERSION)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = PRIOR.selftest()
    out = buf.getvalue()
    print(out, end="")
    chk("⑧ v0265 自測照跑通過(fixture ENG003 缺套件 → ABSENT · ENG004 缺自家 → FAIL)", rc == 0, "rc %s" % rc)
    n = sum(ok)
    print("[計] %s %s 薄尾 %d/%d %s" % (_STEM, VERSION, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    return 0 if n == len(ok) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(args)


if __name__ == "__main__":
    sys.exit(main())
