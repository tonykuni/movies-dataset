#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Independent verifier v0114: v0113 + a second reading for annual FAIL by column alignment (v0113 kept byte-identical).

v0114: desktop 2026-10-30 17:06 (RoundAll v0107 · FIN evidence): the only annual FAIL left — 260914_daiwa_aspeed.pdf PBR (x) 26E 'n.a.' "value
not on the page / cannot locate the item row or the period header" — is the character-box reader again: the page's own text reads header
"Year to 31 Dec 26E 27E 28E" and row "PBR (x) n.a. 29.2 16.8", so 26E is 'n.a.', exactly the book value. When the core says FAIL, v0114 reads the
page a second way (PDFium whole-page text, then pdfplumber text lines — each reader on its own), takes the nearest header line above the item row
that holds the period, and aligns the row's values with the header's periods by order (only when the counts are equal). The source value at the
period equal to the book value → empty marker: NILVAL · number: PRESENT (note says which reader, header and row). Different value or no
alignment → FAIL stays, with what the source holds there (a corrupted / shifted value is still caught).

v0113: desktop 2026-10-29 19:13 (RoundAll v0102 · verifier v0111): annual data BADITEM 19 = MS-3665 ×7 / MS-8358 ×6 / MS-8210 ×4 / Daiwa aspeed ×2
("ModelWare net inc (NT $ mn)" ×8 · "Prior EPS (NT$)**" ×4 · "DPS" ×2), every one "value on the page" — the same character-box reader
(page_lines) that misread the MS key-data sidebars in v0112 is the only reader BADITEM asks. When it says "item not on this page", v0113 reads
the page a second way (PDFium whole-page text + pdfplumber text lines, text_lines) and keeps the earlier verdict only when the item is there:
the whole item (spaces / * † $ , . quotes / brackets ignored, as v0103) or, for items of two words or more, every word in order within three
consecutive lines (a label wrapped or split by the reader). A fabricated / renamed item is found by neither reading and stays BADITEM; its note
then carries the closest source line of the second reading, so the paste-back shows what the page really says. A value that is not on the page
(FAIL) also gets the item's source line of the second reading in its note (verdict unchanged).

v0112: desktop 2026-10-29 19:00 (RoundAll v0102): MS-6669 CURRENT_PRICE_REPORT 3510.00 FAIL "next to the target-price label" and MS-3661 3190.00 FAIL
"not in the first 4 pages", while the source lines are "Shr price, close (Oct 7, 2025) NT$3,510.00" / "... (Dec 3, 2025) NT$3,190.00" (RoundAll v0102
evidence, read with PDFium get_text_range) and the book values equal them. The character-box reader (page_lines) splits / pairs these sidebars
differently on the desktop's library versions (the same MS-3661 PDF passes in the container). When near_label() says no, v0112 reads the page a
second way (PDFium whole-page text + pdfplumber text lines) and accepts the value only when the label on the SAME line, nearest before the value,
is the field's own label (or "<n>% upside" / "NT$<n> price target" right after it). A value whose same-line label is the other price (a swap)
stays FAIL, so the swap / mutation checks keep working.

v0111: v0110 with the source-excerpt reader switched to VRN2_VerbatimVerifier_v0105 (v0110 kept byte-identical).

v0111: a hyphen at a line end matches however PDFium writes it (U+FFFE / U+0002 / "-" + line break, any next character) — the desktop's
only point FAIL (3014TT-20231005.pdf point 3, "…Type-" / "C PD …") came from that. Same structure as v0110 (the --shard children run this file).

v0110: exact source excerpts (verbatim v0104 · MISSING ≠ FAIL); v0105 financial checks intact.

For SOURCE_VERBATIM books, complete PDFium source matches replace the old
synthetic-sentence coverage heuristic. OCR stays pending; mismatches stay FAIL.
"""
from __future__ import annotations
import importlib.util
from pathlib import Path
import re
import sys
import types


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# [VIA:ACCEL-BRIDGE:v0111] Every verifier shard applies the active locked tool.
BRIDGE = load("independent_v0114_execution", "VIA_ExecutionBridge_v0103.py")
BRIDGE.activate(Path(__file__).resolve().parents[2])
PRIOR = load("independent_v0114_financial_core", "VRN2_IndependentVerifier_v0105.py")
QUOTES = load("independent_v0114_source_reader", "VRN2_VerbatimVerifier_v0105.py")
for _name, _value in list(vars(PRIOR).items()):
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = _value
VERSION = "VRN2_IndependentVerifier_v0114"
_native_near_label = PRIOR.near_label
_AFTER_LABEL = {3: re.compile(r"^\s*%\s*(?:upside|downside|潛在漲幅|上漲空間|隱含漲幅|漲幅)", re.I), 1: re.compile(r"^\s*(?:price\s*target|target\s*price|目標價)", re.I)}
_TEXT_LINES = {}


def text_lines(pdf, pno):
    """v0112 second reading of a page: PDFium whole-page text (get_text_range) + pdfplumber text lines (not the character boxes of page_lines)."""
    key = (str(pdf), pno)
    if key not in _TEXT_LINES:
        out = []
        try:
            doc = pdfium.PdfDocument(str(pdf))
            if 1 <= pno <= len(doc):
                out += doc[pno - 1].get_textpage().get_text_range().replace("\r", "\n").split("\n")
            doc.close()
        except Exception:  # noqa: BLE001
            pass
        try:
            import pdfplumber
            with pdfplumber.open(str(pdf)) as d:
                if pno <= len(d.pages):
                    out += (d.pages[pno - 1].extract_text() or "").split("\n")
        except Exception:  # noqa: BLE001
            pass
        _TEXT_LINES[key] = [nfk(line) for line in out if line.strip()]
    return _TEXT_LINES[key]


def line_label(line, start, end):
    """Kind of the label that owns the number at line[start:end]: '<n>% upside' / '<n> price target' right after it, else the nearest label before it on the line (0 = none)."""
    for kind, rx in _AFTER_LABEL.items():
        if rx.match(line[end:]):
            return kind
    before = [(m.end(), 1 if m.group(1) else (2 if m.group(2) else 3)) for m in _LABRX.finditer(line) if m.end() <= start]
    return max(before)[1] if before else 0


def near_label(pdf, v, field, pages=(1, 2, 3, 4)):
    """v0112: v0111's character-box check first (its message "前 %d 頁 …" kept when both readings say no); if it says no, the same-line label in
    the second reading decides (never across lines)."""
    ok, why = _native_near_label(pdf, v, field, pages)
    if ok:
        return ok, why
    fv = _numv(re.sub(r"[^\d.,]", "", str(v)).strip(".,"))
    if fv is None:
        return ok, why
    want = _KIND[field]
    for pg in pages:
        for line in text_lines(pdf, pg):
            for st_, en_ in _num_cands(line, fv):
                if line_label(line, st_, en_) == want:
                    return True, "第 %d 頁 · 同列標籤(第二種讀法 · %s)" % (pg, line[max(0, st_ - 40):en_ + 12].strip()[-72:])
    return ok, why


PRIOR.near_label = near_label            # verify_basic / _swap_hint look near_label up in the v0105 core's globals
_native_verify_fin = PRIOR.verify_fin
_WORD = re.compile(r"[a-z]+|\d+|[㐀-鿿]+")


def _words(t):
    return _WORD.findall(nfk(t).lower())


def _in_order(words, text):
    at = 0
    for w in words:
        at = text.find(w, at)
        if at < 0:
            return False
        at += len(w)
    return True


def item_on_page(pdf, pno, item):
    """v0113 second reading for BADITEM: (True, source line) when the item is on the page — whole item (squash + v0103 _inm) or, for two words or
    more, every word in order within three consecutive lines; else (False, closest source line or "")."""
    lines = text_lines(pdf, pno)
    si = squash(item)
    if not si or not lines:
        return False, ""
    sq = [squash(line) for line in lines]
    for width in (1, 2, 3):                                      # one line first, then a label wrapped over two / three lines
        for i in range(len(lines) - width + 1):
            joined = "".join(sq[i:i + width])
            if si in joined or (_inm(si) and _inm(si) in _inm(joined)):
                return True, " / ".join(lines[i:i + width])[:120]
    words = _words(item)
    if len(words) >= 2 and sum(len(w) for w in words) >= 6:
        low = [nfk(line).lower() for line in lines]
        for width in (1, 2, 3):
            for i in range(len(lines) - width + 1):
                if _in_order(words, " ".join(low[i:i + width])):
                    return True, " / ".join(lines[i:i + width])[:120]
    best, score = "", 0
    for line in lines:
        got = sum(len(w) for w in set(words) if len(w) >= 2 and w in nfk(line).lower())
        if got > score:
            best, score = line, got
    return False, best[:120]


_PER = re.compile(r"^(?:fy)?(?:(?:19|20)\d{2}[aefp]?|\d{2}[aefp])$", re.I)
_VALTOK = re.compile(r"^(?:\(?-?[\d,]*\.?\d+\)?%?|n\.?a\.?|n/a|nm|n\.m\.|-+|–|—)$", re.I)
_NILS = {"n.a", "na", "n/a", "nm", "n.m", "-", "--", "---", "–", "—"}
_READERS = {}


def reader_lines(pdf, pno):
    """v0114: the page's lines per reader (PDFium whole-page text · pdfplumber text lines) — kept apart so a header and a row come from one reader."""
    key = (str(pdf), pno)
    if key not in _READERS:
        out = {}
        try:
            doc = pdfium.PdfDocument(str(pdf))
            if 1 <= pno <= len(doc):
                out["pdfium"] = [nfk(l) for l in doc[pno - 1].get_textpage().get_text_range().replace("\r", "\n").split("\n") if l.strip()]
            doc.close()
        except Exception:  # noqa: BLE001
            pass
        try:
            import pdfplumber
            with pdfplumber.open(str(pdf)) as d:
                if pno <= len(d.pages):
                    out["pdfplumber"] = [nfk(l) for l in (d.pages[pno - 1].extract_text() or "").split("\n") if l.strip()]
        except Exception:  # noqa: BLE001
            pass
        _READERS[key] = out
    return _READERS[key]


def _pkey(t):
    return (re.sub(r"\D", "", t)[-2:], re.sub(r"[^aefp]", "", t.lower()))


def _same_value(a, b):
    na, nb = re.sub(r"[\s,]", "", str(a).lower()).rstrip("."), re.sub(r"[\s,]", "", str(b).lower()).rstrip(".")
    if na in _NILS or nb in _NILS:
        return na in _NILS and nb in _NILS
    def num(x):
        neg = x.startswith("(") and x.endswith(")")
        try:
            v = float(x.strip("()%"))
        except ValueError:
            return None
        return -v if neg else v
    va, vb = num(na), num(nb)
    return va is not None and vb is not None and abs(va - vb) < 1e-9


def column_value(pdf, pno, item, period):
    """v0114: (reader, header line, row line, value at the period) by column order — nearest header above the item row holding the period,
    equal counts only; None when no reader aligns."""
    words = [w for w in re.findall(r"[a-z]+|\d+|[㐀-鿿]+", nfk(item).lower()) if len(w) >= 2][:3]
    want = _pkey(period)
    if not words or not want[0]:
        return None
    for how, lines in reader_lines(pdf, pno).items():
        head = None
        for line in lines:
            toks = line.split()
            pers = [t for t in toks if _PER.match(t)]
            if len(pers) >= 2 and any(_pkey(t) == want for t in pers):
                head = (line, pers)
                continue
            low = line.lower()
            if head and all(w in low for w in words):
                vals = [t for t in toks if _VALTOK.match(t)]
                idx = next((i for i, t in enumerate(head[1]) if _pkey(t) == want), None)
                if idx is not None and len(vals) == len(head[1]):
                    return how, head[0], line, vals[idx]
    return None


def verify_fin(rows, pdfdir, allrows=None):
    """v0113: v0105's verify_fin, then every BADITEM is read a second way (item_on_page); FAIL notes get the item's source line (verdict kept).
    v0114: a FAIL is aligned by column in the second reading — the source value at the period equals the book value → NILVAL (empty marker) /
    PRESENT (number); otherwise FAIL stays with what the source holds there."""
    res = _native_verify_fin(rows, pdfdir, allrows)
    for r in res:
        if r.get("_V") not in ("BADITEM", "FAIL"):
            continue
        pdf, pno = Path(pdfdir) / r["FILENAME"], int(r["PAGE"])
        found, line = item_on_page(pdf, pno, r.get("ITEM", ""))
        if r["_V"] == "FAIL":
            col = column_value(pdf, pno, r.get("ITEM", ""), r.get("PERIOD", ""))
            if col and _same_value(col[3], r.get("VALUE", "")):
                nil = re.sub(r"[\s,]", "", str(r.get("VALUE", "")).lower()).rstrip(".") in _NILS
                r["_V"] = "NILVAL" if nil else "PRESENT"
                r["_N"] = "第二種讀法依欄位對齊(%s):表頭「%s」· 科目列「%s」· %s 這一欄是 %r = 冊值%s · 原判:%s" % (
                    col[0], col[1][:90], col[2][:90], r.get("PERIOD"), col[3], "(空值記號 · 不算錯值)" if nil else "", r["_N"][:160])
            elif col:
                r["_N"] = "%s · 第二種讀法依欄位對齊(%s):%s 這一欄是 %r ≠ 冊值 %r(表頭「%s」· 科目列「%s」)" % (r["_N"], col[0], r.get("PERIOD"), col[3], r.get("VALUE"), col[1][:80], col[2][:80])
            elif found:
                r["_N"] = "%s · 第二種讀法的科目列「%s」" % (r["_N"], line)
            continue
        prefix = "科目 %r 本頁原文沒有 · " % (nfk(r["ITEM"]).strip(),)
        rest = r["_N"][len(prefix):] if r["_N"].startswith(prefix) else r["_N"]
        if found:
            r["_V"] = "PRESENT" if rest.startswith("值在該頁 · 驗證器對不到期間欄") else "ALIGNED"
            r["_N"] = "科目字在本頁(第二種讀法 · 「%s」)· %s" % (line, rest)
        else:
            r["_N"] = "%s · 第二種讀法也沒有這個科目%s" % (r["_N"], (" · 最像的列「%s」" % line) if line else "(本頁沒有相近的列)")
    return res


PRIOR.verify_fin = verify_fin            # run_files (rebound here) and the v0105 core both look verify_fin up by name
QUOTE_RESULT = None
QUOTE_DOCUMENTS = {}


def __getattr__(name):
    return getattr(PRIOR, name)


def rebind(function):
    result = types.FunctionType(function.__code__, globals(), function.__name__, function.__defaults__, function.__closure__)
    result.__kwdefaults__ = function.__kwdefaults__
    return result


def verify_summary(rows, pdfdir, basic=None, fin=None):
    result = PRIOR.verify_summary(rows, pdfdir, basic, fin)
    if QUOTE_RESULT is None:
        return result
    index = {(row.get("file"), row.get("point")): row for row in QUOTE_RESULT["rows"]}
    global_failure = any(row["state"] == "FAIL" and not row.get("point") for row in QUOTE_RESULT["rows"])
    for item in result:
        name = item["FILENAME"]
        if (QUOTE_DOCUMENTS.get(name) or {}).get("mode") != "SOURCE_VERBATIM":
            continue
        for point in range(1, 5):
            proof = index.get((name, point), {})
            state = proof.get("state")
            if global_failure:
                state = "FAIL"
            verdict = {"PASS": "PASS", "OCR_PENDING": "OCR", "MISSING": "MISSING"}.get(state, "FAIL")
            note = "完整原文與來源 PDF 雜湊相符 · p.%s · pypdfium2" % proof.get("page") if state == "PASS" else ("影像頁 · OCR 原文需核對原圖" if state == "OCR_PENDING" else ("原文不足 · 沒有可引用的句子 · 待核對" if state == "MISSING" else proof.get("reason", "原文來源證據未齊")))
            item["checks"][f"POINT_{point}"] = verdict + " · " + note
    return result


_run_files = rebind(PRIOR.run_files)


def run_files(od, pdfdir, files):
    global QUOTE_RESULT, QUOTE_DOCUMENTS
    source = Path(od) / "VRN2_SummarySource_latest.json"
    QUOTE_RESULT, QUOTE_DOCUMENTS = None, {}
    if source.is_file():
        document = json.loads(source.read_text(encoding="utf-8-sig"))
        QUOTE_DOCUMENTS = {row["file"]: row for row in document["documents"]}
        QUOTE_RESULT = QUOTES.verify(od, pdfdir)
    return _run_files(od, pdfdir, files)


run_parallel = rebind(PRIOR.run_parallel)
write_digest = rebind(PRIOR.write_digest)
ui_payload = rebind(PRIOR.ui_payload)
main = rebind(PRIOR.main)
def selftest():
    global QUOTE_RESULT, QUOTE_DOCUMENTS
    result = PRIOR.selftest()
    original = PRIOR.verify_summary
    saved = QUOTE_RESULT, QUOTE_DOCUMENTS
    try:
        PRIOR.verify_summary = lambda *args: [{"FILENAME": "a.pdf", "checks": {"POINT_1": "PASS"}}]
        QUOTE_DOCUMENTS = {"a.pdf": {"mode": "SOURCE_VERBATIM"}}
        QUOTE_RESULT = {"rows": [{"file": "a.pdf", "point": 1, "state": "FAIL", "reason": "tampered source"}]}
        assert verify_summary([], ".")[0]["checks"]["POINT_1"].startswith("FAIL")
        QUOTE_RESULT["rows"][0]["state"] = "OCR_PENDING"
        assert verify_summary([], ".")[0]["checks"]["POINT_1"].startswith("OCR")
        QUOTE_RESULT["rows"][0]["state"] = "MISSING"
        assert verify_summary([], ".")[0]["checks"]["POINT_1"].startswith("MISSING")
        assert ui_payload([], [], [], "fp", 0, 1, True, "test")["ver"] == VERSION
    finally:
        PRIOR.verify_summary = original
        QUOTE_RESULT, QUOTE_DOCUMENTS = saved
    print("[PASS] v0110: source mismatch remains FAIL; OCR remains pending; missing excerpt is MISSING; payload carries actual verifier version")
    assert QUOTES.VERSION == "v0105" and QUOTES.comparable("Type-\nC PD") == QUOTES.comparable("Type\ufffeC PD")
    print("[PASS] v0111: excerpt reader = VerbatimVerifier v0105 (line-end hyphen as U+FFFE / U+0002 / '-' + newline, any next character)")
    sidebar = ["Stock Rating Equal-weight", "Price target NT$3,500.00", "Shr price, close (Oct 7, 2025) NT$3,510.00", "Up/downside to price target (%) -0.3",
               "Our PT of NT$730 implies 18% upside", "We reiterate our OW rating with a NT$730 price target."]
    saved_lines, saved_native = dict(_TEXT_LINES), globals()["_native_near_label"]
    try:
        _TEXT_LINES[("sidebar.pdf", 1)] = [nfk(line) for line in sidebar]
        globals()["_native_near_label"] = lambda pdf, v, field, pages=(1, 2, 3, 4): (False, "前 4 頁有這個數 · 但旁邊是目標價標籤")   # the desktop's character-box miss
        got = {k: near_label("sidebar.pdf", v, k, (1,))[0] for k, v in (("CURRENT_PRICE_REPORT", "3510.00"), ("TARGET_PRICE", "3500.00"), ("UPSIDE_PCT", "-0.3"))}
        swapped = (near_label("sidebar.pdf", "3500.00", "CURRENT_PRICE_REPORT", (1,))[0], near_label("sidebar.pdf", "3510.00", "TARGET_PRICE", (1,))[0])
        prose = (near_label("sidebar.pdf", "18", "UPSIDE_PCT", (1,))[0], near_label("sidebar.pdf", "730.00", "TARGET_PRICE", (1,))[0], near_label("sidebar.pdf", "730", "CURRENT_PRICE_REPORT", (1,))[0])
        assert got == {"CURRENT_PRICE_REPORT": True, "TARGET_PRICE": True, "UPSIDE_PCT": True}, got
        assert swapped == (False, False), swapped
        assert prose == (True, True, False), prose
        assert "第二種讀法" in near_label("sidebar.pdf", "3510.00", "CURRENT_PRICE_REPORT", (1,))[1]
    finally:
        _TEXT_LINES.clear(); _TEXT_LINES.update(saved_lines)
        globals()["_native_near_label"] = saved_native
    assert PRIOR.near_label is near_label
    print("[PASS] v0112: price labels read a second way when the character-box reader says no — same-line label only (MS-6669 3510 / MS-3661 3190 sidebars PASS · swapped target / price stays FAIL · '18% upside' and 'NT$730 price target' prose)")
    page = ["Financial summary (NT$ mn)  12/24  12/25e  12/26e", "ModelWare net inc (NT$ mn)  4,396  9,045  10,120", "Prior EPS (NT$)**  1.10  2.30", "EPS (NT$)**  1.20  2.40",
            "Dividend", "DPS (NT$)  0.50  0.80", "Gross margin", "(%)  31.2  32.0", "Operating income 2,100 2,400"]
    key = str(Path("t") / "ms.pdf")
    native = globals()["_native_verify_fin"]
    saved_lines = dict(_TEXT_LINES)
    try:
        _TEXT_LINES[(key, 1)] = [nfk(line) for line in page]
        def fake(rows, pdfdir, allrows=None):        # the desktop's character-box miss: every row came back BADITEM
            out = []
            for x in rows:
                note = "值在該頁 · 驗證器對不到期間欄" if x.get("_KEEP") == "PRESENT" else "dx 1.0 · 欄寬 40 · 科目列"
                out.append(dict(x, _V="BADITEM", _N="科目 %r 本頁原文沒有 · %s" % (nfk(x["ITEM"]).strip(), note)))
            return out
        globals()["_native_verify_fin"] = fake
        rows = [{"FILENAME": "ms.pdf", "PAGE": 1, "ITEM": "ModelWare net inc (NT $ mn)", "PERIOD": "12/24", "VALUE": "4,396", "_KEEP": "PRESENT"},
                {"FILENAME": "ms.pdf", "PAGE": 1, "ITEM": "Prior EPS (NT$)**", "PERIOD": "12/25e", "VALUE": "2.30"},
                {"FILENAME": "ms.pdf", "PAGE": 1, "ITEM": "DPS", "PERIOD": "12/25e", "VALUE": "0.80"},
                {"FILENAME": "ms.pdf", "PAGE": 1, "ITEM": "Gross margin (%)", "PERIOD": "12/24", "VALUE": "31.2"},
                {"FILENAME": "ms.pdf", "PAGE": 1, "ITEM": "Fabricated reserve ratio", "PERIOD": "12/24", "VALUE": "4,396"},
                {"FILENAME": "ms.pdf", "PAGE": 1, "ITEM": "ModelWare capex (NT $ mn)", "PERIOD": "12/24", "VALUE": "4,396"},
                {"FILENAME": "ms.pdf", "PAGE": 1, "ITEM": "Net debt", "PERIOD": "12/24", "VALUE": "9,045"}]
        got = verify_fin(rows, "t")
        verdicts = [r["_V"] for r in got]
        assert verdicts == ["PRESENT", "ALIGNED", "ALIGNED", "ALIGNED", "BADITEM", "BADITEM", "BADITEM"], verdicts
        assert "第二種讀法" in got[0]["_N"] and got[0]["_N"].endswith("值在該頁 · 驗證器對不到期間欄"), got[0]["_N"]
        assert "Gross margin / (%)" in got[3]["_N"], got[3]["_N"]                                    # wrapped label (three-line window)
        assert "最像的列「ModelWare net inc (NT$ mn)" in got[5]["_N"] and "第二種讀法也沒有" in got[4]["_N"], (got[4]["_N"], got[5]["_N"])
        globals()["_native_verify_fin"] = lambda rows, pdfdir, allrows=None: [dict(x, _V="FAIL", _N="值不在該頁(驗證器讀法)") for x in rows]
        fail = verify_fin([{"FILENAME": "ms.pdf", "PAGE": 1, "ITEM": "DPS", "PERIOD": "12/26e", "VALUE": "n.a."}], "t")[0]
        assert fail["_V"] == "FAIL" and "第二種讀法的科目列「DPS (NT$)" in fail["_N"], fail
    finally:
        _TEXT_LINES.clear(); _TEXT_LINES.update(saved_lines)
        globals()["_native_verify_fin"] = native
    assert PRIOR.verify_fin is verify_fin and globals()["verify_fin"] is verify_fin
    saved_rd = dict(_READERS)
    native = globals()["_native_verify_fin"]
    try:
        key = str(Path("t") / "daiwa.pdf")
        _READERS[(key, 1)] = {"pdfium": ["Daiwa Capital Markets", "Year to 31 Dec 26E 27E 28E", "EPS (TWD) 102.3 120.4 141.0", "PBR (x) n.a. 29.2 16.8", "Tel +886 2 2345 6789"]}
        _TEXT_LINES[(key, 1)] = _READERS[(key, 1)]["pdfium"]
        globals()["_native_verify_fin"] = lambda rows, pdfdir, allrows=None: [dict(x, _V="FAIL", _N="空值記號 %r · 定不出科目列 · 值不在該頁(驗證器讀法)" % x["VALUE"]) for x in rows]
        rows = [{"FILENAME": "daiwa.pdf", "PAGE": 1, "ITEM": "PBR (x)", "PERIOD": "26E", "VALUE": "n.a."},
                {"FILENAME": "daiwa.pdf", "PAGE": 1, "ITEM": "PBR (x)", "PERIOD": "27E", "VALUE": "29.2"},
                {"FILENAME": "daiwa.pdf", "PAGE": 1, "ITEM": "PBR (x)", "PERIOD": "27E", "VALUE": "n.a."},
                {"FILENAME": "daiwa.pdf", "PAGE": 1, "ITEM": "PBR (x)", "PERIOD": "28E", "VALUE": "29.2"},
                {"FILENAME": "daiwa.pdf", "PAGE": 1, "ITEM": "EPS (TWD)", "PERIOD": "28E", "VALUE": "141.0"},
                {"FILENAME": "daiwa.pdf", "PAGE": 1, "ITEM": "ROE (%)", "PERIOD": "26E", "VALUE": "n.a."}]
        got = [r["_V"] for r in verify_fin(rows, "t")]
        assert got == ["NILVAL", "PRESENT", "FAIL", "FAIL", "PRESENT", "FAIL"], got
        notes = verify_fin(rows[:3], "t")
        assert "26E 這一欄是 'n.a.' = 冊值" in notes[0]["_N"] and "27E 這一欄是 '29.2' ≠ 冊值 'n.a.'" in notes[2]["_N"], (notes[0]["_N"], notes[2]["_N"])
        assert _same_value("(1,234.5)", "-1234.5") and not _same_value("n.a.", "0") and _same_value("NA", "n.a.") and not _same_value("29.2", "16.8")
    finally:
        _READERS.clear(); _READERS.update(saved_rd)
        _TEXT_LINES.clear(); _TEXT_LINES.update(saved_lines)
        globals()["_native_verify_fin"] = native
    print("[PASS] v0114: annual FAIL aligned by column in the second reading — Daiwa aspeed PBR 26E 'n.a.' = source → NILVAL · number equal → PRESENT · a value moved to another column / a marker where the source has a number / no item row → FAIL stays")
    print("[PASS] v0113: BADITEM read a second way — item on the page (whole · wrapped · words in order) keeps PRESENT / ALIGNED; fabricated / renamed item stays BADITEM with the closest source line; FAIL keeps FAIL with the item's source line")
    return result


if __name__ == "__main__":
    if sys.argv[1:2] == ["--shard"]:
        od, pdfdir, selection, target = sys.argv[2:6]
        vb, vf, vs = run_files(od, pdfdir, json.loads(Path(selection).read_text(encoding="utf-8")))
        Path(target).write_text(json.dumps({"basic": vb, "fin": vf, "summary": vs}, ensure_ascii=False), encoding="utf-8")
        raise SystemExit(0)
    if sys.argv[1:2] == ["--selftest"]:
        raise SystemExit(selftest())
    arguments = sys.argv[1:]
    ui = arguments[arguments.index("--ui") + 1] if "--ui" in arguments else None
    positional = [item for i, item in enumerate(arguments) if item != "--ui" and not (i > 0 and arguments[i-1] == "--ui")]
    raise SystemExit(main(*positional[:3], ui=ui))
