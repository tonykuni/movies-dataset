#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN-2 v0259: transposed tables — the third reader's touching number fragments are joined before the gate is asked again (thin tail over v0258).

Operator 2026-11-02 uploaded 華南投顧-6143-振曜-1141128.pdf (the last 「輸出冊缺項 · 年度數據」 of the closeout). Page 1 prints the annual table
「年度EPS預估」 with the years as rows (2022 · 2023 · 2024 · 2025(F) · 2026(F)) and 8 items as columns (營收 · 毛利率(%) · 營益率(%) · 業外收支率(%) ·
股本 · 稅前純益 · 稅前EPS · 稅後EPS) = 40 values. The second reader (pypdfium2) reads every row; the third-reader gate of v0236 (pdfplumber) rejected
the whole table 「每個年份一行對不上」: in the 2026(F) row Word left a stray space glyph from another font (Calibri, 2 pt lower) lying across the
digits of 「3.0」, so pdfplumber splits the word into 「3」 and 「.0」 although the glyphs touch. One split number → the row's number sequence differs
→ all 40 values rejected.

v0259 asks the same gate (v0236 _g3_trans · unchanged) again, only for rows the books rejected with 「轉置表第三讀法(pdfplumber)對不上」, on the
pdfplumber lines with touching number fragments joined: two words of one line whose boxes touch (gap ≤ 0.5 pt) are one word when the left one has a
digit, the joint is a decimal / thousands separator (「3」+「.0」 · 「1,」+「234」 · 「12.」+「5」) and the result is a number token. A table that now
passes goes back to the annual book (VERIFY notes it · ROW / SECTION as extracted); a table that still fails stays in the Rejected book with its reason.
The book gap 「年度數據」 is cleared for a report that now has annual rows. Nothing else changes: extraction, v0258's table repair, the other gates,
the other books and the U/I stay v0258 / v0257 / v0255 / v0243 code (reached through PRIOR).
"""
from __future__ import annotations

# ===== 1. Parameters =====
TAG = "v0259"
DISPLAY_NAME = "VRN-2 SystemManager"
PRIOR_NAME = "VRN_SystemManager_v0258.py"

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import re
import sys
import tempfile
import types

# [VIA:ACCEL-BRIDGE:v0111] The original manager executes its accelerator bridge.
_spec = importlib.util.spec_from_file_location("vrn_manager_prior_for_v0259", Path(__file__).with_name(PRIOR_NAME))
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
for _name, _value in list(vars(PRIOR).items()):
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = _value


def __getattr__(name):
    return getattr(PRIOR, name)


def _rebind(function):
    result = types.FunctionType(function.__code__, globals(), function.__name__, function.__defaults__, function.__closure__)
    result.__kwdefaults__, result.__doc__ = function.__kwdefaults__, function.__doc__
    return result


# ===== 2. Third reader: touching number fragments =====
_TJ_REASON = "轉置表第三讀法(pdfplumber)對不上"
_TJ_VERIFY = "年度列表(轉置 · pypdfium2 對欄) · pdfplumber 再驗(v0259 相連的數字碎片接回)"
_TJ_GAP = 0.5


def _tj_joinable(left: str, right: str) -> bool:
    """Left + right is one number split at its separator: 「3」+「.0」 · 「1,」+「234」 · 「12.」+「5」(the result must be a number token)."""
    if not re.search(r"\d", left) or not right:
        return False
    if not (re.match(r"^[.,]\d", right) or (re.search(r"[.,]$", left) and right[:1].isdigit())):
        return False
    return bool(_SV_TOK.match(left + right))


def _tj_line(tokens: list) -> list:
    """One pdfplumber line [(x0, x1, word)] (sorted by x) with touching number fragments joined."""
    out = []
    for a, b, t in sorted(tokens):
        if out:
            pa, pb, pt = out[-1]
            if a - pb <= _TJ_GAP and _tj_joinable(pt, t):
                out[-1] = (pa, max(pb, b), pt + t)
                continue
        out.append((a, b, t))
    return out


def _tj_page(pg):
    """_g3_page result → the same tuple with every line's touching number fragments joined (text strings unchanged) · None stays None."""
    if not pg:
        return pg
    return ([(top, _tj_line(tokens)) for top, tokens in pg[0]],) + tuple(pg[1:])


def _tj_bbox(res, filename: str, table: str):
    for r in res or []:
        if r.get("file") != filename:
            continue
        for pg in r.get("pages") or []:
            for z in pg.get("zones") or []:
                if z.get("id") == table and z.get("bbox"):
                    return z["bbox"]
    return None


def _tj_recheck(res, fin: list, rej: list, v2):
    """Rows rejected by the transposed-table gate → asked again with joined fragments. → (rows back to the book, Rejected rows left, notes)."""
    have = {(x.get("FILENAME"), x.get("TABLE"), x.get("ITEM"), x.get("PERIOD")) for x in fin}
    groups, rest = {}, []
    for x in rej:
        if x.get("BOOK") == "FinancialData" and str(x.get("REASON", "")).startswith(_TJ_REASON):
            groups.setdefault((x.get("FILENAME"), x.get("PAGE"), x.get("TABLE")), []).append(x)
        else:
            rest.append(x)
    back, notes = [], []
    for (f, pno, table), xs in groups.items():
        why, bbox = "", _tj_bbox(res, f, table)
        pdf = _out_pdf(f, Path(v2))
        if not bbox or not pdf.exists():
            why = "沒有區塊位置 / 原 PDF"
        else:
            pg = _tj_page(_g3_page(pdf, int(pno or 1)))
            why = "閘不可用" if pg is None else _g3_trans([dict(x, VERIFY="") for x in xs], pg, bbox[0], bbox[2])
        if why or any((x.get("FILENAME"), x.get("TABLE"), x.get("ITEM"), x.get("PERIOD")) in have for x in xs):
            rest.extend(xs)                                               # still not confirmed (or already in the book) → stays with its reason
            continue
        for x in xs:
            row = {k: v for k, v in x.items() if k not in ("BOOK", "REASON", "FIELD")}
            row["VERIFY"] = _TJ_VERIFY
            back.append(row)
        notes.append("%s %s %d 值" % (str(f)[:24], table, len(xs)))
    return back, rest, notes


# ===== 3. Books =====
def _out_books_v0259(res, acc, st, v2):
    """v0259 = v0258 books + transposed tables asked again with the third reader's touching number fragments joined."""
    basic, fin, summ, gaps, made = _PRIOR_OUT_V0258(res, acc, st, v2)
    od = Path(v2) / "output"
    rej = _XV_LAST.get("rej")
    if rej is None:
        try:
            rej = json.loads((od / "VRN2_Rejected_latest.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            rej = []
    try:
        back, rest, notes = _tj_recheck(res, fin, list(rej), v2)
    except Exception as error:  # noqa: BLE001  — a recheck error never costs the books: v0258's books stand as written
        back, rest, notes = [], rej, []
        _say("[計] v0259 轉置表再驗略過(%s: %s)· 輸出冊照 v0258" % (type(error).__name__, str(error)[:120]))
    if back:
        fin = list(fin) + back
        made = [m_ for m_ in made if not m_.startswith(("FinancialData(", "Rejected("))]
        made = [_write_book(od, "FinancialData", fin)] + made + [_write_book(od, "Rejected", rest)]
        _XV_LAST["rej"] = rest
        done = {x["FILENAME"] for x in back}
        kept = []
        for g in gaps or []:
            head, _sep, miss = str(g).partition(":")
            if any(str(f)[:28] == head for f in done):
                miss = "、".join(m_ for m_ in miss.split("、") if m_ != "年度數據")
                if not miss:
                    continue
                g = "%s:%s" % (head, miss)
            kept.append(g)
        gaps = kept
    note = "v0259 轉置表再驗(第三讀法相連的數字碎片接回):回主冊 %d 值%s" % (len(back), (" · " + " | ".join(notes[:3])) if notes else "")
    it = _XV_LAST.get("item")
    if it:
        _XV_LAST["item"] = (it[0], it[1], it[2] + " · " + note)
    if back:
        _say("[計] " + note)
    return basic, fin, summ, gaps, made


_PRIOR_OUT_V0258 = getattr(PRIOR._out_books, "__wrapped__", PRIOR._out_books)    # v0258's books (v0258 wraps them in the phase timer)
_out_books = _timed("輸出冊", _out_books_v0259)


def completion(*args, **kwargs):
    result = PRIOR.completion(*args, **kwargs)
    result["manager"] = f"{DISPLAY_NAME} {TAG}"
    return result


# ===== 4. Native flow with v0259 globals (books · completion · register) =====
_native_vrn2 = _rebind(PRIOR._native_vrn2)
_success_register = _rebind(PRIOR._success_register)
vrn2 = _rebind(PRIOR.vrn2)


# ===== 5. Self-test =====
def selftest():
    bad = []

    def chk(name, cond):
        print("[%s] %s" % ("PASS" if cond else "FAIL", name), flush=True)
        if not cond:
            bad.append(name)

    chk("① 相連的數字碎片接回:「3」+「.0」→ 3.0 · 「1,」+「234」→ 1,234 · 「12.」+「5」→ 12.5(盒子相連 · 間距 ≤ 0.5pt)",
        _tj_line([(101.0, 106.0, "3"), (105.9, 113.0, ".0"), (147.0, 160.0, "8.6")]) == [(101.0, 113.0, "3.0"), (147.0, 160.0, "8.6")]
        and _tj_line([(10, 20, "1,"), (20.3, 35, "234")])[0][2] == "1,234" and _tj_line([(10, 20, "12."), (20, 25, "5")])[0][2] == "12.5")
    chk("② 不接:中間有空隙(兩欄)· 不是小數 / 千分位(12 34 · 2026 (F))· 文字 · 接起來不是數字",
        len(_tj_line([(10, 20, "3"), (21, 30, ".0")])) == 2 and len(_tj_line([(10, 20, "12"), (20, 30, "34")])) == 2
        and len(_tj_line([(10, 20, "2026"), (20, 30, "(F)")])) == 2 and len(_tj_line([(10, 20, "EPS"), (20, 30, ".0")])) == 2
        and len(_tj_line([(10, 20, "3"), (20, 30, ".0.0")])) == 2)
    yrs = ["2022", "2023", "2024", "2025(F)", "2026(F)"]
    vals = [["11.1", "21.1", "5.1", "1.1"], ["12.2", "22.2", "6.2", "1.2"], ["13.3", "23.3", "7.3", "1.3"], ["14.4", "24.4", "8.4", "-0.4"], ["15.5", "25.5", "9.5", "3.0"]]
    cx = [290, 330, 365, 405]

    def line(y, yr, vs, split=False):
        tk = [(234.0, 260.0, yr)]
        for x, v in zip(cx, vs):
            if split and v == "3.0":
                tk += [(x - 4, x + 1, "3"), (x + 0.95, x + 7, ".0")]
            else:
                tk.append((x - 6, x + 6, v))
        return (y, tk)
    head = [(690.0, [(320.0, 335.0, "毛利率"), (355.0, 370.0, "營益率"), (390.0, 405.0, "業外收")]),
            (696.0, [(241.0, 255.0, "年度"), (285.0, 300.0, "營收")]),
            (703.0, [(326.0, 336.0, "(%)"), (362.0, 372.0, "(%)"), (389.0, 410.0, "支率(%)")])]
    plumber = (head + [line(719.7 + 18 * i, y, v, split=(i == 4)) for i, (y, v) in enumerate(zip(yrs, vals))], "rawtext", [])
    labels = ["營收", "毛利率(%)", "營益率(%)", "業外收支率(%)"]
    rows = [{"BOOK": "FinancialData", "FILENAME": "h.pdf", "PAGE": 1, "TABLE": "P1·M·05·TB", "ITEM": l_, "PERIOD": y, "VALUE": v, "ROW": i + 1, "SECTION": "",
             "REASON": _TJ_REASON + " · pdfplumber 每個年份一行對不上 / 欄名接不出", "REPORT_DATE": "2025-11-28", "TICKER": "6143", "BROKER": "華南"}
            for i, (y, vs) in enumerate(zip(yrs, vals)) for l_, v in zip(labels, vs)]
    other = {"BOOK": "FinancialData", "FILENAME": "h.pdf", "PAGE": 1, "TABLE": "P1·M·06·TB", "ITEM": "x", "PERIOD": "2024", "VALUE": "1", "REASON": "非數據列(表頭 / 子表頭 / 分隔線)"}
    res = [{"file": "h.pdf", "pages": [{"pno": 1, "zones": [{"id": "P1·M·05·TB", "bbox": [234.3, 680.0, 420.0, 816.0], "minor": "TB", "rows": []}]}]}]
    chk("③ 原樣(「3」「.0」分開)問 v0236 的轉置表閘 → 不過「每個年份一行對不上」(跟桌機一樣)· 接回後 → 過",
        _g3_trans(rows, plumber, 234.3, 420.0) != "" and _g3_trans(rows, _tj_page(plumber), 234.3, 420.0) == "")
    saved = {k: globals()[k] for k in ("_g3_page", "_out_pdf")}
    try:
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "h.pdf").write_bytes(b"%PDF-1.4 fake")
            globals()["_out_pdf"] = lambda f, v2: Path(td) / f
            globals()["_g3_page"] = lambda pdf, pno: plumber
            back, rest, notes = _tj_recheck(res, [], rows + [other], Path(td))
            chk("④ 剔除冊裡轉置表閘那 20 值 → 整張表再驗過 → 回主冊(VERIFY 註明 v0259 · 沒有 BOOK / REASON)· 別的理由的剔除列不動",
                len(back) == 20 and all(x["VERIFY"] == _TJ_VERIFY and "REASON" not in x and "BOOK" not in x for x in back) and rest == [other]
                and {(x["ITEM"], x["PERIOD"], x["VALUE"]) for x in back} >= {("業外收支率(%)", "2026(F)", "3.0"), ("營收", "2022", "11.1")} and notes)
            back2, rest2, _n2 = _tj_recheck(res, [dict(rows[0], VERIFY="x")], rows, Path(td))
            globals()["_g3_page"] = lambda pdf, pno: (plumber[0][:-1], "", [])        # 2026(F) line missing → still fails
            back3, rest3, _n3 = _tj_recheck(res, [], rows, Path(td))
            globals()["_g3_page"] = lambda pdf, pno: None
            back4, _r4, _n4 = _tj_recheck(res, [], rows, Path(td))
            chk("⑤ 主冊已有同鍵 → 不放回 · 第三讀法還是對不上 / 讀不到 → 留剔除冊(理由不變)",
                not back2 and len(rest2) == 20 and not back3 and rest3 == rows and not back4)
            globals()["_g3_page"] = lambda pdf, pno: plumber
            v2 = Path(td) / "v2"
            (v2 / "output").mkdir(parents=True)
            seen, saved_out, saved_last = {}, globals()["_PRIOR_OUT_V0258"], dict(_XV_LAST)
            try:
                _XV_LAST.clear()
                _XV_LAST.update(rej=rows + [other], item=("輸出值驗證", "YELLOW", "基本資料 欄 1"))
                globals()["_PRIOR_OUT_V0258"] = lambda r_, a_, s_, v_: ([], [], [], ["h.pdf:年度數據", "h.pdf:TITLE、年度數據", "x.pdf:年度數據"], ["FinancialData(0 列)", "Rejected(21 列)"])
                with contextlib.redirect_stdout(io.StringIO()):
                    out = _out_books(res, [], [], v2)
                book = json.loads((v2 / "output" / "VRN2_FinancialData_latest.json").read_text(encoding="utf-8"))
                rbook = json.loads((v2 / "output" / "VRN2_Rejected_latest.json").read_text(encoding="utf-8"))
                chk("⑥ 輸出冊:年度數據冊多 20 值 · 剔除冊只剩別的理由 · 缺項「h.pdf:年度數據」清掉(別的缺項 / 別的檔照留)· 輸出值驗證那一項註明 v0259 · 輸出冊階段照樣計時",
                    len(book) == 20 and rbook == [other] and out[3] == ["h.pdf:TITLE", "x.pdf:年度數據"] and "v0259 轉置表再驗" in _XV_LAST["item"][2]
                    and any(p_["phase"] == "輸出冊" for p_ in PHASES) and sum(1 for m_ in out[4] if m_.startswith("FinancialData(")) == 1)
                globals()["_tj_recheck"] = lambda *a: (_ for _ in ()).throw(RuntimeError("boom"))
                with contextlib.redirect_stdout(io.StringIO()) as said:
                    out2 = _out_books(res, [], [], v2)
                chk("⑦ 再驗出錯 → 輸出冊照 v0258(不少一筆)· 印一行原因(不吞)", out2[3] == ["h.pdf:年度數據", "h.pdf:TITLE、年度數據", "x.pdf:年度數據"] and "v0259 轉置表再驗略過(RuntimeError" in said.getvalue())
            finally:
                globals()["_PRIOR_OUT_V0258"] = saved_out
                globals()["_tj_recheck"] = _tj_recheck_saved
                _XV_LAST.clear()
                _XV_LAST.update(saved_last)
    finally:
        globals().update(saved)
    chk("⑧ 原生流程綁本版名稱空間(輸出冊 / 完成判定 / 成功登記 → v0259)· 前版程式碼不動",
        _native_vrn2.__globals__ is globals() and vrn2.__globals__ is globals() and _native_vrn2.__code__ is PRIOR._native_vrn2.__code__
        and _success_register.__globals__ is globals() and _out_books.__wrapped__ is _out_books_v0259 and completion.__module__ == __name__
        and _PRIOR_OUT_V0258.__name__ == "_out_books_v0258")
    why = ""
    try:
        with contextlib.redirect_stdout(io.StringIO()) as said:
            prior_rc = PRIOR.selftest()
        why = "" if prior_rc == 0 else said.getvalue().strip().splitlines()[-1][:160]
    except AssertionError as error:
        prior_rc, why = 1, str(error)[:160]
    chk("⑨ v0258 自測(表格修補 · 再跑 v0257 一列一科目 · 冪等閘)照樣全過%s" % (" · " + why if why else ""), prior_rc == 0)
    print("[%s] v0259: transposed tables asked again with the third reader's touching number fragments joined · still failing stays in Rejected · %d checks · failed %d"
          % ("PASS" if not bad else "FAIL", 9, len(bad)), flush=True)
    return 0 if not bad else 1


_tj_recheck_saved = _tj_recheck


def main(argv=None):
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments == ["--selftest"]:
        return selftest()
    if arguments[:1] == ["vrn2"]:
        code, lines = vrn2(arguments[1:])
        for line in lines:
            print(line, flush=True)
        return code
    return PRIOR.main(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
