#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only second-reader check of the four source excerpts and their PDF hash — v0105 = v0104 thin tail (v0104 kept byte-identical).

v0105: a hyphen at a line end is the same text however the reader writes it.
  Desktop 2026-10-29 (52 files): 3014TT-20231005.pdf point 3 FAIL "second reader did not reproduce the complete source excerpt" — the only FAIL,
  and the reason for closeout rc 1. The excerpt (pdfplumber) ends a line with "…聯陽Type-" and the next line starts "C PD 至少";
  PDFium writes that line-end hyphen as U+FFFE and drops the line break ("Type\\ufffeC"). v0104 only joined "-<newline>" before a lowercase
  letter and did not know U+FFFE, so "type-c" (excerpt) never matched "type\\ufffec" (PDF). Reproduced in the container with a generated PDF.
  v0105 comparable(): U+FFFE → "-<newline>" first, then any "-<newline>" (any next character) is dropped on both sides; U+0002 / U+00AD stay
  removed as in v0104. Hyphens inside a line are untouched, the stored excerpt is never changed (only the comparison form).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import tempfile

VERSION = "v0105"
PRIOR_NAME = "VRN2_VerbatimVerifier_v0104.py"
HERE = Path(__file__).resolve().parent
_LINE_END_HYPHEN = re.compile(r"-[ \t]*\r?\n\s*")


def _prior():
    for path in (HERE / PRIOR_NAME,):
        if path.is_file():
            spec = importlib.util.spec_from_file_location("vrn2_verbatim_prior_v0104", path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            return module
    raise FileNotFoundError("前版 %s 不在 %s" % (PRIOR_NAME, HERE))


PRIOR = _prior()
for _name in dir(PRIOR):
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = getattr(PRIOR, _name)
_native_comparable = PRIOR.comparable


def comparable(text):
    text = str(text).replace("\ufffe", "-\n").replace("\u2010", "-").replace("\u2011", "-")   # PDFium line-end hyphen · Unicode hyphens
    text = _LINE_END_HYPHEN.sub("", text)                                                     # "-" + line break is optional, any next character
    return _native_comparable(text)


PRIOR.comparable = comparable          # v0104 verify() looks comparable up in its own globals → this version
verify = PRIOR.verify


def _pdf_with_line_end_hyphen(path: Path) -> bool:
    """A real PDF whose line ends with a hyphen before an uppercase letter (needs PyMuPDF; skipped without it)."""
    try:
        import pymupdf as fitz  # noqa: WPS433
    except Exception:  # noqa: BLE001
        try:
            import fitz  # noqa: WPS433
        except Exception:  # noqa: BLE001
            return False
    doc = fitz.open()
    page = doc.new_page()
    for i, line in enumerate(("support NB ODM supply chain, we estimate 2024 ITE Type-", "C PD at least doubles, inter-", "national demand stays firm")):
        page.insert_text((72, 72 + 16 * i), line, fontsize=11)
    doc.save(str(path))
    return True


def selftest():
    bad = []

    def chk(label, cond):
        print(("[PASS] " if cond else "[FAIL] ") + label, flush=True)
        if not cond:
            bad.append(label)

    try:
        PRIOR.selftest()
        chk("① v0104 自測(缺摘錄 = MISSING · 沒證據的字 = FAIL)照過", True)
    except AssertionError as error:
        chk("① v0104 自測(缺摘錄 = MISSING · 沒證據的字 = FAIL)照過 · %s" % error, False)
    quote = "我們預估2024 年聯陽Type-\nC PD 至少"
    chk("② 行尾連字號:摘錄「Type-↵C」= PDFium「Type\\ufffeC」= 舊 PDFium「Type\\x02C」= 「Type-\\r\\nC」(下一字大寫也接)",
        comparable(quote) == comparable("我們預估2024 年聯陽Type\ufffeC PD 至少") == comparable("我們預估2024 年聯陽Type\x02C PD 至少") == comparable("我們預估2024 年聯陽Type-\r\nC PD 至少"))
    chk("③ v0104 的行為還在:小寫接合「inter-↵national」= 「international」· 行內連字號「Type-C」保留 · 項目符號 / 控制字元照舊去掉",
        comparable("inter-\nnational") == comparable("international") and comparable("Type-C PD") != comparable("TypeC PD") and comparable("\x00 先進封裝 • 測試\n產能") == comparable("先進封裝測試產能"))
    chk("④ v0104 的比對確實對不上這段(桌機 FAIL 的原因)· v0105 對得上",
        _native_comparable(quote) not in _native_comparable("我們預估2024 年聯陽Type\ufffeC PD 至少") and comparable(quote) in comparable("……我們預估2024 年聯陽Type\ufffeC PD 至少翻倍……"))
    with tempfile.TemporaryDirectory(prefix="vrn2-verbatim105-") as temporary:
        out, src = Path(temporary) / "out", Path(temporary) / "src"
        out.mkdir()
        src.mkdir()
        if _pdf_with_line_end_hyphen(src / "h.pdf"):
            excerpt = "we estimate 2024 ITE Type-\nC PD at least doubles, inter-\nnational demand"
            (out / "VRN2_Summary_latest.json").write_text(json.dumps([{"FILENAME": "h.pdf", "TITLE": "t", "POINT_1": excerpt, "POINT_2": "", "POINT_3": "", "POINT_4": ""}]), encoding="utf-8")
            points = [{"point": 1, "verbatim": True, "quote": excerpt, "quote_sha256": hashlib.sha256(excerpt.encode("utf-8")).hexdigest(), "page": 1}] + [{"point": i, "verbatim": False, "quote": "", "page": None} for i in (2, 3, 4)]
            (out / "VRN2_SummarySource_latest.json").write_text(json.dumps({"documents": [{"file": "h.pdf", "pdf_sha256": hashlib.sha256((src / "h.pdf").read_bytes()).hexdigest(), "points": points}]}), encoding="utf-8")
            PRIOR.comparable = _native_comparable
            old = PRIOR.verify(out, src)
            PRIOR.comparable = comparable
            new = verify(out, src)
            p_old = next(r for r in old["rows"] if r.get("point") == 1)
            p_new = next(r for r in new["rows"] if r.get("point") == 1)
            chk("⑤ 真 PDF(PyMuPDF 產生 · 行尾「Type-」下一行「C PD」):v0104 = FAIL(second reader …)· v0105 = PASS", p_old["state"] == "FAIL" and p_new["state"] == "PASS")
        else:
            print("[SKIP] ⑤ 沒有 PyMuPDF · 不產生真 PDF(② ~ ④ 已涵蓋比對式)", flush=True)
    print("[%s] VRN2_VerbatimVerifier %s --selftest · 5 項 · 不過 %d" % ("PASS" if not bad else "FAIL", VERSION, len(bad)), flush=True)
    return 0 if not bad else 1


def main(argv=None):
    if (sys.argv[1:] if argv is None else argv) == ["--selftest"]:
        return selftest()
    return PRIOR.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
