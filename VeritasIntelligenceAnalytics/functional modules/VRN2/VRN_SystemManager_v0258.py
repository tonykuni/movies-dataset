#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN-2 v0258: table repair before the books — label on its own half-line · two-level period header (thin tail over v0257).

Operator 2026-11-01 uploaded the originals of two reports the closeout listed as 「輸出冊缺項 · 年度數據」(human item H-275f449a).
Both DO print annual tables; the extraction engine read them, the books dropped them:

  · 欣銓(3264,B_買進)-CTBC260918.pdf page 5 (資產負債表 · 現金流量表 · 損益表 · 比率分析, 2022 – 2027F): every item name is printed
    ~3 pt lower than its numbers, so the engine stores two rows — ['', <n>, <n>, …] then [<item>, '', …]. The books skip a
    row without an item AND a row without values, so all four tables vanished without a trace (not even in the Rejected book).
    The right-hand table's item cell is split, too: ['', '營', '業收入淨額', '', …].
  · Daiwa-6278 20260521.pdf page 2 (TSMT financial summary): a year banner (2024 · 2025 · 2026) sits above the real column header
    (1Q24 … 1Q26 · 2024 · 2025 · 3M26). The engine cut the columns at the banner, so each cell holds 3–5 numbers (「一格多值 · 子欄位未拆」)
    and the annual 2024 / 2025 columns never reach the annual book.

v0258 repairs such zones (a copy — the extraction result and P1VIEW stay as they are) and then runs v0257's books unchanged:
  ① half-line pairing: a value-only row next to a label-only row is merged ONLY when the second reader (pypdfium2) prints that label and
    exactly that sequence of annual-column numbers on one line (unique on the page; ≥ 2 numbers). Label pieces in several cells are
    joined (CJK + CJK without a space, CJK + Latin with one).
  ② two-level period header: when the row under the header holds the real period labels (all period-like · ≥ 2 annual · unique ·
    some cell holding several), the table is re-gridded on that row: the second reader must find the sub-header line once, and each data
    row once (item + the same number sequence); every number goes to the nearest sub-header label (one-to-one · in order · within 0.4 of
    the narrowest column gap). A row the second reader cannot place is dropped from the table and written to the Rejected book with the reason.
Every repaired value then passes the same checks as before (second-reader column check · third-reader gate · one row one item · the
independent verifier in step 8). Zones that do not match these shapes are not touched; extraction, acceptance, the other books, the
verifiers and the U/I stay v0257 / v0255 / v0243 code (reached through PRIOR).
"""
from __future__ import annotations

# ===== 1. Parameters =====
TAG = "v0258"
DISPLAY_NAME = "VRN-2 SystemManager"
PRIOR_NAME = "VRN_SystemManager_v0257.py"

from collections import Counter
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import re
import sys
import tempfile
import types

# [VIA:ACCEL-BRIDGE:v0111] The original manager executes its accelerator bridge.
_spec = importlib.util.spec_from_file_location("vrn_manager_prior_for_v0258", Path(__file__).with_name(PRIOR_NAME))
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


# ===== 2. Zone repair =====
_ZR_PER = re.compile(_XV_PER.pattern + r"|^\d{1,2}M\d{2}[AEFP]?$|^[12]H\d{2}[AEFP]?$", re.I)   # + 3M26 · 9M25 · 1H26
_ZR_LAB = re.compile(r"[A-Za-z㐀-鿿]")
_ZR_REASON = "子表頭重排(v0258):第二讀取器對不到這一列(科目 + 同一串數值)· 不輸出"


def _zr_hdr(rows):
    """Same header rule as the books (v0229): the first of the top 4 rows with ≥ 2 annual period cells after the item cell."""
    return next(((i, rw) for i, rw in enumerate(rows[:4]) if sum(bool(_SK_ANNUAL.match((c or "").strip())) for c in rw[1:]) >= 2), None)


def _zr_num(cell) -> bool:
    text = (cell or "").strip()
    return bool(text) and all(_SV_TOK.match(t) for t in text.split())


def _zr_label(row):
    """Label-only row → its label (pieces in several cells joined) · otherwise None."""
    cells = [(c or "").strip() for c in row or []]
    filled = [c for c in cells if c]
    if not filled or any(_zr_num(c) for c in filled) or not all(_ZR_LAB.search(c) for c in filled):
        return None
    label = ""
    for piece in filled:
        latin_l, latin_r = bool(re.search(r"[A-Za-z0-9)%]$", label)), bool(re.match(r"[A-Za-z0-9(]", piece))
        cjk_l, cjk_r = bool(re.search(r"[㐀-鿿]$", label)), bool(re.match(r"[㐀-鿿]", piece))
        if label and ((cjk_l and latin_r) or (latin_l and cjk_r) or (latin_l and latin_r and len(label) > 1 and len(piece) > 1)):
            label += " "                                                   # 公告基本 · EPS(元) → 公告基本 EPS(元) · 營 · 業收入淨額 → 營業收入淨額 · E · BITDA → EBITDA
        label += piece
    return label


def _zr_vrow(row, ann) -> bool:
    """Value-only row: no item cell · every filled cell is numbers / nil marks · ≥ 2 annual columns filled."""
    if not row or (row[0] or "").strip():
        return False
    if any((c or "").strip() and not _zr_num(c) for c in row[1:]):
        return False
    return sum(1 for j in ann if j < len(row) and (row[j] or "").strip()) >= 2


def _zr_same_line(lines, label, values) -> bool:
    """Second reader: exactly one printed line holds the label and this exact number sequence (contiguous, in order)."""
    key, want = _xv_sq(label), [_xv_sq(v) for v in values]
    if not key or not want:
        return False
    hits = 0
    for _y, tokens in lines:
        if key not in _xv_sq("".join(t for _a, _b, t in tokens)):
            continue
        nums = [_xv_sq(t) for _a, _b, t in tokens if _SV_TOK.match(t)]
        if any(nums[i:i + len(want)] == want for i in range(len(nums) - len(want) + 1)):
            hits += 1
    return hits == 1


def _zr_pre_pair(rows) -> bool:
    hdr = _zr_hdr(rows)
    if not hdr:
        return False
    hi, hrow = hdr
    ann = [j for j, c in enumerate(hrow) if j and _SK_ANNUAL.match((c or "").strip())]
    body = rows[hi + 1:]
    return any(_zr_vrow(body[i], ann) and ((i + 1 < len(body) and _zr_label(body[i + 1])) or (i and _zr_label(body[i - 1])))
               for i in range(len(body)))


def _zr_pair(rows, lines):
    """① Half-line pairing → (new rows, pairs merged) or None (nothing confirmed by the second reader)."""
    hdr = _zr_hdr(rows)
    if not hdr or not lines:
        return None
    hi, hrow = hdr
    ann = [j for j, c in enumerate(hrow) if j and _SK_ANNUAL.match((c or "").strip())]
    out = [list(r) for r in rows[:hi + 1]]
    open_label = False                                                    # out[-1] is an original label-only row not merged yet
    merged, i = 0, hi + 1
    while i < len(rows):
        row = list(rows[i])
        values = [(row[j] or "").strip() for j in ann if j < len(row) and re.search(r"\d", row[j] or "")]   # annual numbers only (a nil mark / a
        if _zr_vrow(row, ann) and len(values) >= 2:                       # non-annual column such as 3Q17 can sit on another printed line)
            after = _zr_label(rows[i + 1]) if i + 1 < len(rows) else None
            if after and _zr_same_line(lines, after, values):
                out.append([after] + row[1:])
                merged, i, open_label = merged + 1, i + 2, False
                continue
            before = _zr_label(out[-1]) if open_label else None
            if before and _zr_same_line(lines, before, values):
                out[-1] = [before] + row[1:]
                merged, i, open_label = merged + 1, i + 1, False
                continue
        out.append(row)
        open_label = _zr_label(row) is not None
        i += 1
    return (out, merged) if merged else None


def _zr_pre_regrid(rows) -> bool:
    hdr = _zr_hdr(rows)
    if not hdr or hdr[0] + 1 >= len(rows):
        return False
    sub = rows[hdr[0] + 1]
    labels = [t for c in sub[1:] for t in (c or "").split()]
    return (len(labels) >= 3 and len(set(labels)) == len(labels) and all(_ZR_PER.match(t) for t in labels)
            and sum(bool(_SK_ANNUAL.match(t)) for t in labels) >= 2 and any(len((c or "").split()) >= 2 for c in sub[1:]))


def _zr_regrid(rows, lines):
    """② Two-level period header → (new rows, rows placed, [(row index, item, numbers)] not placed) or None (not this shape / not confirmed)."""
    if not lines or not _zr_pre_regrid(rows):
        return None
    hi, _hrow = _zr_hdr(rows)
    sub = rows[hi + 1]
    labels = [t for c in sub[1:] for t in (c or "").split()]
    found = [k for k, (_y, tokens) in enumerate(lines) if [t for _a, _b, t in tokens if _ZR_PER.match(t)] == labels]
    if len(found) != 1:
        return None
    sl = found[0]
    sx = [(a + b) / 2 for a, b, t in lines[sl][1] if _ZR_PER.match(t)]
    if any(sx[i + 1] <= sx[i] for i in range(len(sx) - 1)):
        return None
    tol = 0.4 * min(sx[i + 1] - sx[i] for i in range(len(sx) - 1))     # between two labels (middle 20 %) → not placed
    lo = sx[0] - 2 * tol
    out = [list(r) for r in rows[:hi]] + [[(sub[0] or "")] + labels]
    placed, annual, dropped = 0, 0, []
    for ri in range(hi + 2, len(rows)):
        row = rows[ri]
        item = ((row[0] if row else "") or "").strip()
        nums = [t for c in row[1:] for t in (c or "").split()]
        if not nums:
            out.append([(row[0] if row else "") or ""] + [""] * len(labels))   # section heading (Margins (%) · YoY (%))
            continue
        cells = None
        key = _xv_sq(item)[:14]
        if key and _ZR_LAB.search(item) and all(_SV_TOK.match(t) for t in nums):
            want = [_xv_sq(t) for t in nums]
            hits = []
            for k in range(sl + 1, len(lines)):
                tokens = lines[k][1]
                if key not in _xv_sq("".join(t for _a, _b, t in tokens)):
                    continue
                seq = [(a, b) for a, b, t in tokens if (a + b) / 2 >= lo and _SV_TOK.match(t)]
                if [_xv_sq(t) for a, b, t in tokens if (a + b) / 2 >= lo and _SV_TOK.match(t)] == want:
                    hits.append(seq)
            if len(hits) == 1:
                idx = [min(range(len(sx)), key=lambda n, c=(a + b) / 2: abs(sx[n] - c)) for a, b in hits[0]]
                if len(set(idx)) == len(idx) and idx == sorted(idx) and all(abs(sx[n] - (a + b) / 2) <= tol for n, (a, b) in zip(idx, hits[0])):
                    cells = [""] * len(labels)
                    for n, t in zip(idx, nums):
                        cells[n] = t
        if cells is None:
            dropped.append((ri, item, " ".join(nums)))
            continue
        out.append([row[0]] + cells)
        placed += 1
        annual += sum(1 for n, t in enumerate(cells) if t and _SK_ANNUAL.match(labels[n]))
    if not placed or not annual or len(dropped) > placed:
        return None
    return out, placed, dropped


def _zone_repair(res, st, v2):
    """Copy of the extraction result with ① / ② applied to stock reports' annual tables → (res, stats, examples, Rejected rows)."""
    stock = {s_.get("file"): s_ for s_ in st or [] if s_.get("stock", True)}
    cache, stat, examples, rejected, out = {}, Counter(), [], [], []
    for r in res or []:
        f = r.get("file")
        if f not in stock:
            out.append(r)
            continue
        pdf, copied = None, None
        for pi, pg in enumerate(r.get("pages") or []):
            for zi, z in enumerate(pg.get("zones") or []):
                rows = z.get("rows") or []
                if z.get("minor") != "TB" or not rows or not _zr_hdr(rows):
                    continue
                want_grid, want_pair = _zr_pre_regrid(rows), _zr_pre_pair(rows)
                if not (want_grid or want_pair):
                    continue
                pdf = pdf or _out_pdf(f, Path(v2))
                pno = int(pg.get("pno") or 1)
                lines = _xv_lines(pdf, pno, cache) if pdf.exists() else []
                new, notes = rows, []
                if want_grid:
                    grid = _zr_regrid(new, lines)
                    if grid:
                        new, placed, dropped = grid
                        stat["子表頭重排表"] += 1
                        stat["子表頭重排列"] += placed
                        stat["重排對不上"] += len(dropped)
                        notes.append("子表頭重排 %d 列%s" % (placed, " · 對不上 %d 列(剔除冊)" % len(dropped) if dropped else ""))
                        s_ = stock[f]
                        for _ri, item, nums in dropped:
                            rejected.append({"BOOK": "FinancialData", "FILENAME": f, "FIELD": "", "VALUE": nums, "REASON": _ZR_REASON,
                                             "REPORT_DATE": s_.get("date", ""), "TICKER": s_.get("ticker", ""), "BROKER": s_.get("broker", ""),
                                             "PAGE": pno, "TABLE": z.get("id"), "ITEM": item, "PERIOD": ""})
                if _zr_pre_pair(new):
                    paired = _zr_pair(new, lines)
                    if paired:
                        new, merged = paired
                        stat["半行配對列"] += merged
                        stat["半行配對表"] += 1
                        notes.append("科目半行配對 %d 列" % merged)
                if new is not rows:
                    if copied is None:
                        copied = copy.deepcopy(r)
                    zone = copied["pages"][pi]["zones"][zi]
                    zone["rows"] = new
                    zone["repair"] = "v0258 " + " · ".join(notes)
                    examples.append("%s %s %s" % (f[:24], z.get("id"), " · ".join(notes)))
        out.append(copied if copied is not None else r)
    return out, stat, examples, rejected


# ===== 3. Books =====
def _out_books_v0258(res, acc, st, v2):
    """v0258 = zone repair (copy) → v0257 books unchanged · rows the re-grid could not place → Rejected book (with the reason)."""
    try:
        res2, stat, examples, zrej = _zone_repair(res, st, v2)
    except Exception as error:  # noqa: BLE001  — a repair error never costs the books: v0257 runs on the original result
        res2, stat, examples, zrej = res, Counter(), [], []
        _say("[計] v0258 表格修補略過(%s: %s)· 輸出冊照 v0257" % (type(error).__name__, str(error)[:120]))
    basic, fin, summ, gaps, made = _PRIOR_OUT_V0257(res2, acc, st, v2)
    if zrej:
        od = Path(v2) / "output"
        rej = _XV_LAST.get("rej")
        if rej is None:
            try:
                rej = json.loads((od / "VRN2_Rejected_latest.json").read_text(encoding="utf-8"))
            except (OSError, ValueError):
                rej = []
        rej = list(rej) + zrej
        made = [m_ for m_ in made if not m_.startswith("Rejected(")] + [_write_book(od, "Rejected", rej)]
        _XV_LAST["rej"] = rej
    note = "v0258 表格修補:科目半行配對 %d 列(%d 表)· 子表頭重排 %d 表 %d 列 · 對不上 %d 列(剔除冊)" % (
        stat["半行配對列"], stat["半行配對表"], stat["子表頭重排表"], stat["子表頭重排列"], stat["重排對不上"])
    it = _XV_LAST.get("item")
    if it:
        _XV_LAST["item"] = (it[0], it[1], it[2] + " · " + note)
    if examples:
        _say("[計] %s · %s" % (note, " | ".join(examples[:4])))
    return basic, fin, summ, gaps, made


_PRIOR_OUT_V0257 = getattr(PRIOR._out_books, "__wrapped__", PRIOR._out_books)    # v0257's books (v0257 wraps them in the phase timer)
_out_books = _timed("輸出冊", _out_books_v0258)


def completion(*args, **kwargs):
    result = PRIOR.completion(*args, **kwargs)
    result["manager"] = f"{DISPLAY_NAME} {TAG}"
    return result


# ===== 4. Native flow with v0258 globals (books · completion · register) =====
_native_vrn2 = _rebind(PRIOR._native_vrn2)
_success_register = _rebind(PRIOR._success_register)
vrn2 = _rebind(PRIOR.vrn2)


# ===== 5. Self-test =====
def _fake_line(y, *tokens):
    """Second-reader line from (x0, text) pairs: width 6 pt per character."""
    return (y, [(x, x + 6 * len(t), t) for x, t in tokens])


def selftest():
    bad = []

    def chk(name, cond):
        print("[%s] %s" % ("PASS" if cond else "FAIL", name), flush=True)
        if not cond:
            bad.append(name)

    # ① / ③ two-level period header (Daiwa-6278 page 2 shape)
    rows = [["TSMT: financial summary"], ["", "2024", "2025", "2026"],
            ["(TWDm)", "1Q24 2Q24 3Q24 4Q24", "1Q25 2Q25 3Q25", "4Q25 1Q26 2024 2025 3M26"],
            ["Net sales", "1,001 1,002 1,003 1,004", "2,001 2,002 2,003", "3,001 3,002 4,100 4,200 3,002"],
            ["EPS (TWD)", "1.11 1.12 1.13 1.14", "1.21 1.22 1.23", "1.24 1.31 4.44 4.55 1.31"],
            ["YoY (%)", "", "", ""],
            ["Net sales", "1.1% -2.2% -3.3% -4.4%", "5.5% 6.6% 7.7%", "8.8% 9.9%"],
            ["Gross profit", "5,001 5,002", "", ""]]
    subx = [100 + 30 * n for n in range(12)]
    heads = ["1Q24", "2Q24", "3Q24", "4Q24", "1Q25", "2Q25", "3Q25", "4Q25", "1Q26", "2024", "2025", "3M26"]
    lines = [_fake_line(700, (140, "2024"), (250, "2025"), (340, "2026")),
             _fake_line(690, (40, "(TWDm)"), *[(x - 12, h) for x, h in zip(subx, heads)]),
             _fake_line(680, (40, "Net"), (62, "sales"), *[(x - 15, v) for x, v in zip(subx, rows[3][1].split() + rows[3][2].split() + rows[3][3].split())]),
             _fake_line(670, (40, "EPS"), (62, "(TWD)"), *[(x - 12, v) for x, v in zip(subx, "1.11 1.12 1.13 1.14 1.21 1.22 1.23 1.24 1.31 4.44 4.55 1.31".split())]),
             _fake_line(660, (40, "YoY"), (62, "(%)")),
             _fake_line(650, (40, "Net"), (62, "sales"), *[(x - 15, v) for x, v in zip(subx, "1.1% -2.2% -3.3% -4.4% 5.5% 6.6% 7.7% 8.8% 9.9%".split())]),
             _fake_line(640, (40, "Gross"), (72, "profit"), (subx[0] - 15, "5,001"), (subx[1], "5,002"))]
    grid = _zr_regrid(rows, lines)
    new, placed, dropped = grid if grid else ([], 0, [])
    head = new[1] if len(new) > 1 else []
    ns = next((r for r in new if r[0] == "Net sales"), [])
    eps = next((r for r in new if r[0] == "EPS (TWD)"), [])
    chk("① 兩層期間表頭(Daiwa-6278 第 2 頁)→ 依子表頭重排:2024 / 2025 年度欄 · EPS 年度欄 · 季度值留在季度欄",
        head[1:] == heads and ns[heads.index("2024") + 1] == "4,100" and ns[heads.index("2025") + 1] == "4,200" and ns[heads.index("4Q24") + 1] == "1,004"
        and eps[heads.index("2024") + 1] == "4.44" and eps[heads.index("2025") + 1] == "4.55" and placed == 3)
    yoy = [r for r in new if r[0] == "Net sales"][1:] if new else []
    chk("② 只有季度值的列(YoY 9 個)照第二讀取器的 x 進季度欄 · 年度欄空 · 段落標題列留著(SECTION 不變)",
        bool(yoy) and yoy[0][heads.index("1Q26") + 1] == "9.9%" and not yoy[0][heads.index("2024") + 1] and ["YoY (%)"] + [""] * 12 in new)
    chk("③ 第二讀取器那一列的數值不在子表頭欄位內(第二個數在 2Q24 與 3Q24 中間)→ 這列不放 · 移剔除冊理由",
        [(item, nums) for _ri, item, nums in dropped] == [("Gross profit", "5,001 5,002")] and not any(r[0] == "Gross profit" for r in new))
    lines_moved = [lines[0], lines[1], _fake_line(680, (40, "Net"), (62, "sales"), (subx[0] - 15, "999"))] + lines[3:]
    g2 = _zr_regrid(rows, lines_moved)
    chk("④ 第二讀取器找不到同一串數值的列 → 不猜(Net sales 移剔除 · EPS 照放)",
        bool(g2) and not any(r[0] == "Net sales" and r[heads.index("2024") + 1] for r in g2[0]) and any(d[1] == "Net sales" for d in g2[2]))
    quarterly = [["", "2025", "2026"], ["", "1Q25 2Q25 3Q25 4Q25", "1Q26 2Q26 3Q26 4Q26"], ["Revenue", "1 2 3 4", "5 6 7 8"]]
    old_new = [["", "2026F", "2027F"], ["", "Old New Diff", "Old New Diff"], ["Revenue", "1 2 3", "4 5 6"]]
    chk("⑤ 子表頭沒有年度欄(全季度)/ 不是期間(Old New Diff)/ 第二讀取器沒有那一行 → 不重排(交給 v0234 子欄拆分)",
        not _zr_pre_regrid(quarterly) and not _zr_pre_regrid(old_new) and _zr_regrid(rows, lines[2:]) is None and _zr_regrid(rows, []) is None)

    # ⑥ – ⑨ half-line pairing (欣銓 3264 page 5 shape)
    fl = [["資產負債表 2013"], ["", "2022", "2023", "2024", "2025"],
          ["", "10,100", "10,200", "10,300", "10,400"], ["資產總計", "", "", "", ""],
          ["", "2,100", "2,200", "2,300", "2,400"], ["流動資產", "", "", "", ""]]
    fr = [["損益表"], ["", "3Q17", "2023", "2024", "2025", "2026F", "2027F"],
          ["", "--", "11,000", "12,000", "13,000", "14,000", "15,000"], ["", "營", "業收入淨額", "", "", "", ""],
          ["", "--", "1,100", "1,200", "1,300", "1,400", "1,500"], ["", "E", "BITDA", "", "", "", ""],
          ["", "--", "3.01", "3.02", "3.03", "- -", "- -"], ["", "公告基本", "EPS(元)", "", "", "", ""],
          ["其他", "", "", "", "", "", ""]]
    page = [_fake_line(700, (37, "(百萬元)"), (141, "2022"), (176, "2023"), (210, "2024"), (245, "2025"), (281, "3Q17"), (386, "2023"), (422, "2024"), (457, "2025"), (492, "2026F"), (530, "2027F")),
            _fake_line(686, (37, "資產總計"), (144, "10,100"), (177, "10,200"), (212, "10,300"), (248, "10,400"), (302, "--"), (313, "營業收入淨額"), (389, "11,000"), (424, "12,000"), (460, "13,000"), (497, "14,000"), (537, "15,000")),
            _fake_line(670, (37, "流動資產"), (148, "2,100"), (181, "2,200"), (216, "2,300"), (252, "2,400"), (302, "--"), (313, "EBITDA"), (389, "1,100"), (424, "1,200"), (460, "1,300"), (497, "1,400"), (537, "1,500")),
            _fake_line(655, (302, "--")),
            _fake_line(652, (313, "公告基本"), (337, "EPS(元)"), (392, "3.01"), (426, "3.02"), (462, "3.03"), (500, "-"), (504, "-"), (540, "-"), (544, "-"))]
    p1 = _zr_pair(fl, page)
    p2 = _zr_pair(fr, page)
    chk("⑥ 科目印在數字下方 3pt(欣銓 P5 資產負債表)→ 第二讀取器同一列有「科目 + 這串數字」才併:資產總計 / 流動資產",
        bool(p1) and p1[1] == 2 and ["資產總計", "10,100", "10,200", "10,300", "10,400"] in p1[0] and ["流動資產", "2,100", "2,200", "2,300", "2,400"] in p1[0])
    chk("⑦ 右表科目被切成兩格(「營」「業收入淨額」·「E」「BITDA」·「公告基本」「EPS(元)」)→ 接回(中英之間一格空白)· 只比年度欄的數字(3Q17 的 -- 在別的印刷列也併)· 段落列不動",
        bool(p2) and p2[1] == 3 and ["公告基本 EPS(元)", "--", "3.01", "3.02", "3.03", "- -", "- -"] in p2[0] and ["營業收入淨額", "--", "11,000", "12,000", "13,000", "14,000", "15,000"] in p2[0]
        and ["EBITDA", "--", "1,100", "1,200", "1,300", "1,400", "1,500"] in p2[0] and ["其他", "", "", "", "", "", ""] in p2[0])
    rev = [fl[0], fl[1], fl[3], fl[2], fl[5], fl[4]]
    p3 = _zr_pair(rev, page)
    chk("⑧ 科目在數字上方(順序相反)也能併 · 只併第二讀取器確認的那一對",
        bool(p3) and p3[1] == 2 and ["資產總計", "10,100", "10,200", "10,300", "10,400"] in p3[0] and ["流動資產", "2,100", "2,200", "2,300", "2,400"] in p3[0])
    wrong = [fl[0], fl[1], fl[2], fl[5]]                                  # first value row next to 流動資產 only (流動資產 is printed with the second value row)
    heading = [fl[0], fl[1], ["營運指標", "", "", "", ""], fl[2]]          # section heading above a value row
    chk("⑨ 科目與數字不在同一印刷列(配錯 / 段落標題)→ 不併(原樣 · 跟以前一樣不輸出)· 沒有第二讀取器 → 不併",
        _zr_pair(wrong, page) is None and _zr_pair(heading, page) is None and _zr_pair(fl, []) is None and _zr_pair(fl, page[:1]) is None)

    # ⑩ zone repair on a result copy · ⑪ books wrapper
    res = [{"file": "a.pdf", "pages": [{"pno": 5, "zones": [{"id": "P5·FL·01·TB", "minor": "TB", "rows": fl}, {"id": "P5·F·02·TX", "minor": "TX", "records": [{"text": "x"}]}]}]},
           {"file": "b.pdf", "pages": [{"pno": 5, "zones": [{"id": "P5·FL·01·TB", "minor": "TB", "rows": fl}]}]}]
    st = [{"file": "a.pdf", "stock": True, "ticker": "3264", "date": "2026-09-18", "broker": "中信"}, {"file": "b.pdf", "stock": False}]
    before = json.dumps(res, ensure_ascii=False)
    saved_lines, saved_pdf = globals()["_xv_lines"], globals()["_out_pdf"]
    try:
        with tempfile.TemporaryDirectory() as td:
            pdf = Path(td) / "a.pdf"
            pdf.write_bytes(b"%PDF-1.4 fake")
            globals()["_out_pdf"] = lambda f, v2: Path(td) / f
            globals()["_xv_lines"] = lambda p, n, c: page if n == 5 else []
            res2, stat, ex, zrej = _zone_repair(res, st, Path(td))
            z = res2[0]["pages"][0]["zones"][0]
            chk("⑩ 只修個股報告的表(非個股原樣)· 修的是副本(擷取結果 / P1VIEW 不動)· 區塊註明 v0258",
                json.dumps(res, ensure_ascii=False) == before and res2[1] is res[1] and z["rows"][2][0] == "資產總計" and z["repair"].startswith("v0258 科目半行配對 2 列")
                and stat["半行配對列"] == 2 and res2[0]["pages"][0]["zones"][1] is not z and not zrej and ex)
            v2 = Path(td) / "v2"
            (v2 / "output").mkdir(parents=True)
            seen = {}
            saved_out, saved_last = globals()["_PRIOR_OUT_V0257"], dict(_XV_LAST)
            try:
                _XV_LAST.clear()
                _XV_LAST.update(rej=[{"BOOK": "FinancialData", "VALUE": "x", "REASON": "前版的剔除"}], item=("輸出值驗證", "YELLOW", "基本資料 欄 1"))
                globals()["_PRIOR_OUT_V0257"] = lambda r_, a_, s_, v_: (seen.__setitem__("res", r_), ([], [], [], [], ["FinancialData(0 列)", "Rejected(1 列)"]))[1]
                dres = [{"file": "a.pdf", "pages": [{"pno": 5, "zones": [{"id": "P2·F·01·TB", "minor": "TB", "rows": rows}]}]}]
                globals()["_xv_lines"] = lambda p, n, c: lines
                out = _out_books(dres, [], st, v2)
                rbook = json.loads((v2 / "output" / "VRN2_Rejected_latest.json").read_text(encoding="utf-8"))
                chk("⑪ 輸出冊:v0257 拿到修過的副本 · 重排對不上的列進剔除冊(前版的剔除不漏)· 輸出值驗證那一項註明 v0258 · 輸出冊階段照樣計時",
                    seen["res"][0]["pages"][0]["zones"][0]["rows"][1][1:] == heads and rbook[0]["REASON"] == "前版的剔除"
                    and [x["ITEM"] for x in rbook[1:]] == ["Gross profit"] and rbook[1]["REASON"] == _ZR_REASON and rbook[1]["TICKER"] == "3264"
                    and "v0258 表格修補" in _XV_LAST["item"][2] and "子表頭重排 1 表 3 列" in _XV_LAST["item"][2]
                    and any(p_["phase"] == "輸出冊" for p_ in PHASES) and sum(1 for m_ in out[4] if m_.startswith("Rejected(")) == 1)
                globals()["_xv_lines"] = lambda p, n, c: (_ for _ in ()).throw(RuntimeError("boom"))
                with contextlib.redirect_stdout(io.StringIO()) as said:
                    _out_books(dres, [], st, v2)
                chk("⑫ 修補出錯 → 輸出冊照 v0257(原始結果)· 印一行原因(不吞)",
                    seen["res"] is dres and "v0258 表格修補略過(RuntimeError" in said.getvalue())
            finally:
                globals()["_PRIOR_OUT_V0257"] = saved_out
                _XV_LAST.clear()
                _XV_LAST.update(saved_last)
    finally:
        globals()["_xv_lines"], globals()["_out_pdf"] = saved_lines, saved_pdf
    chk("⑬ 原生流程綁本版名稱空間(輸出冊 / 完成判定 / 成功登記 → v0258)· 前版程式碼不動",
        _native_vrn2.__globals__ is globals() and vrn2.__globals__ is globals() and _native_vrn2.__code__ is PRIOR._native_vrn2.__code__
        and _success_register.__globals__ is globals() and _out_books.__wrapped__ is _out_books_v0258 and completion.__module__ == __name__
        and _PRIOR_OUT_V0257.__name__ == "_out_books_v0257")
    why = ""
    try:
        with contextlib.redirect_stdout(io.StringIO()) as said:
            prior_rc = PRIOR.selftest()
        why = "" if prior_rc == 0 else said.getvalue().strip().splitlines()[-1][:160]
    except AssertionError as error:
        prior_rc, why = 1, str(error)[:160]
    chk("⑭ v0257 自測(一列一科目 · 冪等閘)照樣全過%s" % (" · " + why if why else ""), prior_rc == 0)
    print("[%s] v0258: table repair before the books — label half-line pairing and two-level period header re-grid, both confirmed by the second reader · unplaced rows to Rejected · %d checks · failed %d"
          % ("PASS" if not bad else "FAIL", 14, len(bad)), flush=True)
    return 0 if not bad else 1


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
